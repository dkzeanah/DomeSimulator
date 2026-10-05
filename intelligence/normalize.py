"""Deterministic normalisation: redaction, path symbols, and action names.

Everything here is pure functions over strings and JSON-like values, so it is
cheap enough to run inside a hook and easy to test.

Three jobs:

1. **Redaction** (:func:`redact`).  Values under keys whose names look like
   secrets are replaced, recursively; secret-looking ``name=value`` pairs and
   ``Bearer`` headers inside strings are masked; ``.env`` contents are never
   kept.
2. **Symbolisation** (:func:`symbolize`).  The project root, Claude's
   scratchpad, temp dirs and the home directory become ``<PROJECT_ROOT>``,
   ``<CLAUDE_SCRATCHPAD>``, ``<TEMP>`` and ``<HOME>``; :func:`generalize`
   further replaces numbers, hashes, PIDs and quoted literals so one family of
   commands collapses to one pattern.
3. **Classification** (:func:`classify_tool`, :func:`classify_command`).  A tool
   call becomes one vocabulary name -- ``python.syntax_check``,
   ``render.stills``, ``git.commit`` -- by ordered rules, never by a model.
"""

from __future__ import annotations

import hashlib
import json
import os
import re
import shlex
from dataclasses import dataclass

from .database import PROJECT_ROOT

# ----------------------------------------------------------------------
# Redaction
# ----------------------------------------------------------------------

#: Key-name fragments whose values are secrets.
SECRET_KEY_PARTS = ("password", "passwd", "secret", "token", "api_key", "apikey",
                    "authorization", "bearer", "credential", "private_key")
REDACTED = "<REDACTED>"

# KEY=value / KEY: value / "key": "value" pairs inside free text.
_SECRET_PAIR = re.compile(
    r"(?i)\b([A-Za-z0-9_\-]*(?:password|passwd|secret|token|api_?key|authorization|"
    r"credential|private_key)[A-Za-z0-9_\-]*)(\s*[:=]\s*)(\"[^\"]*\"|'[^']*'|[^\s,;&|]+)")
_BEARER = re.compile(r"(?i)\b(bearer)\s+[A-Za-z0-9._~+/=\-]{8,}")
# Common provider key shapes (OpenAI/Anthropic sk-, GitHub ghp_, Stripe sk_/rk_, AWS AKIA).
_KEY_SHAPES = re.compile(
    r"\b(sk-[A-Za-z0-9_\-]{16,}|sk-ant-[A-Za-z0-9_\-]{16,}|gh[pousr]_[A-Za-z0-9]{20,}|"
    r"(?:sk|rk|pk)_(?:live|test)_[A-Za-z0-9]{12,}|AKIA[0-9A-Z]{16})\b")
# A .env file anywhere in a path or command.
_DOTENV = re.compile(r"(^|[\\/\s'\"])\.env(\.[A-Za-z0-9_]+)?($|[\s'\"])")


def is_secret_key(name: str) -> bool:
    """True when a key's name looks like it holds a secret."""
    lowered = str(name).lower()
    return any(part in lowered for part in SECRET_KEY_PARTS)


def redact_text(text: str) -> str:
    """Mask secret-looking pairs, bearer tokens and known key shapes in text."""
    if not text:
        return text
    # Bearer first: in "Authorization: Bearer <tok>" the pair rule would
    # otherwise take the word "Bearer" as the value and leave the token.
    text = _BEARER.sub(lambda m: f"{m.group(1)} {REDACTED}", text)
    text = _SECRET_PAIR.sub(lambda m: f"{m.group(1)}{m.group(2)}{REDACTED}", text)
    return _KEY_SHAPES.sub(REDACTED, text)


def redact(value, _depth: int = 0):
    """Recursively redact a JSON-like value. Never mutates its argument."""
    if _depth > 40:                      # pathological nesting: stop, keep a marker
        return "<DEPTH LIMIT>"
    if isinstance(value, dict):
        out = {}
        for key, item in value.items():
            out[key] = REDACTED if is_secret_key(key) and item not in (None, "", [], {}) \
                else redact(item, _depth + 1)
        return out
    if isinstance(value, list):
        return [redact(item, _depth + 1) for item in value]
    if isinstance(value, str):
        return redact_text(value)
    return value


def mentions_dotenv(text: str) -> bool:
    """True when a path or command refers to a .env file."""
    return bool(text) and bool(_DOTENV.search(text.replace("\\", "/")))


# ----------------------------------------------------------------------
# Size control
# ----------------------------------------------------------------------

@dataclass(frozen=True)
class Capped:
    """A text value cut to a limit, with what is needed to know it was cut."""
    text: str
    length: int
    sha256: str
    truncated: bool


def cap(text: str, limit: int) -> Capped:
    """Truncate ``text`` to ``limit`` characters, keeping length and hash."""
    text = "" if text is None else str(text)
    digest = hashlib.sha256(text.encode("utf-8", "replace")).hexdigest()
    if len(text) <= limit:
        return Capped(text, len(text), digest, False)
    keep = text[:limit]
    return Capped(keep + f"\n<TRUNCATED {len(text) - limit} chars>", len(text), digest, True)


def to_text(value) -> str:
    """A tool response (string, dict or list) as one string."""
    if value is None:
        return ""
    if isinstance(value, str):
        return value
    try:
        return json.dumps(value, ensure_ascii=False, default=str)
    except (TypeError, ValueError):
        return str(value)


# ----------------------------------------------------------------------
# Symbolisation
# ----------------------------------------------------------------------

def _variants(path: str) -> list[str]:
    """A path in the spellings it can appear in: \\ and / and Git Bash /c/..."""
    p = path.rstrip("\\/")
    fwd = p.replace("\\", "/")
    out = {p, fwd, p.replace("/", "\\")}
    if re.match(r"^[A-Za-z]:/", fwd):
        out.add("/" + fwd[0].lower() + fwd[2:])          # /c/Users/...
    return sorted(out, key=len, reverse=True)


_ROOT_VARIANTS = _variants(str(PROJECT_ROOT))
_HOME_VARIANTS = _variants(os.path.expanduser("~"))
# Claude's per-session scratchpad, in either slash style, with or without the tail.
_SCRATCHPAD = re.compile(
    r"(?i)(?:[A-Z]:)?[\\/][^\s'\"]*?[\\/]Temp[\\/]claude[\\/][^\\/\s'\"]+[\\/]"
    r"[0-9a-f\-]{36}[\\/]scratchpad|\$TEMP/claude/[^/\s'\"]+/[0-9a-f\-]{36}/scratchpad"
    r"|/tmp/claude[^\s'\"]*?/scratchpad")
_TEMP = re.compile(r"(?i)(?:[A-Z]:)?[\\/]Users[\\/][^\\/]+[\\/]AppData[\\/]Local[\\/]Temp|\$env:TEMP|\$TEMP")


def symbolize(text: str) -> str:
    """Replace machine-specific locations with stable symbols."""
    if not text:
        return text
    text = _SCRATCHPAD.sub("<CLAUDE_SCRATCHPAD>", text)
    for variant in _ROOT_VARIANTS:
        text = re.sub(re.escape(variant), "<PROJECT_ROOT>", text, flags=re.I)
    text = _TEMP.sub("<TEMP>", text)
    for variant in _HOME_VARIANTS:
        text = re.sub(re.escape(variant), "<HOME>", text, flags=re.I)
    return text


_HEX = re.compile(r"\b[0-9a-f]{12,64}\b", re.I)
_UUID = re.compile(r"\b[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}\b", re.I)
_NUMBER = re.compile(r"(?<![A-Za-z_])\d+(?:\.\d+)?(?![A-Za-z_])")
_QUOTED = re.compile(r"\"(?:[^\"\\]|\\.){24,}\"|'(?:[^'\\]|\\.){24,}'")
_PATHISH = re.compile(r"(?:<PROJECT_ROOT>|<CLAUDE_SCRATCHPAD>|<TEMP>|<HOME>)[^\s'\";|&)]*")


def generalize(command: str, limit: int = 160) -> str:
    """A command reduced to its family: symbols, then numbers, hashes,
    long quoted literals and concrete paths become placeholders."""
    text = symbolize(command or "")
    text = _QUOTED.sub("<STR>", text)
    text = _UUID.sub("<UUID>", text)
    text = _HEX.sub("<HASH>", text)
    text = _PATHISH.sub(lambda m: m.group(0).split("/")[0].split("\\")[0] + "/<PATH>"
                        if ("/" in m.group(0) or "\\" in m.group(0)) else m.group(0), text)
    text = _NUMBER.sub("<N>", text)
    text = re.sub(r"\s+", " ", text).strip()
    return text[:limit]


# ----------------------------------------------------------------------
# Classification
# ----------------------------------------------------------------------

@dataclass(frozen=True)
class Spec:
    """Static description of one vocabulary entry."""
    category: str
    purpose: str
    risk: str              # low | medium | high
    success_signal: str


#: The seed vocabulary. Names not listed here still classify (see SPEC_FOR);
#: this table only gives the common ones their descriptions.
SPECS: dict[str, Spec] = {
    "python.syntax_check": Spec("python", "compile a file without running it", "low", "exit 0, no output"),
    "python.run_module": Spec("python", "run a project module with -m", "medium", "exit 0"),
    "python.run_script": Spec("python", "run a Python script file", "medium", "exit 0"),
    "python.inline": Spec("python", "run a short python -c snippet", "medium", "exit 0, expected print"),
    "python.selftest": Spec("verify", "run a tool's built-in self-test", "low", "exit 0, 'ok'/'passed'"),
    "project.launch": Spec("project", "start a project application or launcher tool", "medium", "process starts"),
    "project.check": Spec("verify", "run a project validator suite", "low", "'passed' summary, exit 0"),
    "render.stills": Spec("render", "render still frames of a film for review", "medium", "PNGs written"),
    "render.video": Spec("render", "render a film or export a video", "high", "mp4 written, exit 0"),
    "render.queue": Spec("render", "operate the re-render queue", "medium", "exit 0"),
    "render.plates": Spec("render", "take book plates from films", "medium", "plates made, none failed"),
    "book.check": Spec("verify", "run the wedge book's checks", "low", "'N of N passed'"),
    "book.build": Spec("book", "build the book HTML/PDF", "medium", "pdf path printed"),
    "book.renumber": Spec("book", "renumber book chapters", "medium", "chapters moved"),
    "book.ledger": Spec("book", "regenerate the concept ledger", "low", "ledger written"),
    "book.run_module": Spec("book", "run a wedge_book module", "medium", "exit 0"),
    "presenter.run": Spec("project", "drive the presenter studio", "medium", "exit 0"),
    "media.inspect": Spec("media", "inspect media with ffprobe", "low", "stream info printed"),
    "media.transcode": Spec("media", "encode/convert media with ffmpeg", "medium", "output file written"),
    "media.extract_frame": Spec("media", "pull a frame out of a video", "low", "png written"),
    "git.status": Spec("git", "show working tree status", "low", "exit 0"),
    "git.diff": Spec("git", "show changes", "low", "exit 0"),
    "git.log": Spec("git", "show history", "low", "exit 0"),
    "git.add": Spec("git", "stage changes", "medium", "exit 0"),
    "git.commit": Spec("git", "record a commit", "high", "commit hash printed"),
    "git.push": Spec("git", "publish commits to a remote", "high", "remote updated"),
    "git.branch": Spec("git", "list or change branches", "medium", "exit 0"),
    "git.tag": Spec("git", "tag a commit", "medium", "exit 0"),
    "git.worktree": Spec("git", "manage worktrees", "medium", "exit 0"),
    "git.other": Spec("git", "other git command", "medium", "exit 0"),
    "npm.run": Spec("node", "run an npm script", "medium", "exit 0"),
    "dependency.install": Spec("dependency", "install packages", "high", "installed"),
    "process.inspect": Spec("process", "list or query running processes", "low", "process listed"),
    "process.start": Spec("process", "start a background process", "medium", "process id"),
    "process.kill": Spec("process", "stop a process", "high", "process gone"),
    "process.wait": Spec("process", "wait for a condition or a running job", "low", "condition met"),
    "filesystem.read": Spec("filesystem", "read a file", "low", "content returned"),
    "filesystem.search": Spec("filesystem", "search files by name or content", "low", "matches returned"),
    "filesystem.list": Spec("filesystem", "list a directory", "low", "entries returned"),
    "filesystem.edit": Spec("filesystem", "change part of a file", "medium", "edit applied"),
    "filesystem.write": Spec("filesystem", "write a whole file", "medium", "file written"),
    "filesystem.delete": Spec("filesystem", "delete files", "high", "file gone"),
    "filesystem.copy": Spec("filesystem", "copy or move files", "medium", "file present"),
    "filesystem.mkdir": Spec("filesystem", "create directories", "low", "directory present"),
    "filesystem.check": Spec("filesystem", "test whether paths exist / sizes", "low", "answer printed"),
    "web.search": Spec("web", "search the web", "low", "results returned"),
    "web.fetch": Spec("web", "fetch a web page", "low", "content returned"),
    "browser.navigate": Spec("browser", "open a page in the built-in browser", "low", "page loaded"),
    "browser.inspect": Spec("browser", "read or screenshot a browser page", "low", "content returned"),
    "browser.interact": Spec("browser", "click/type in a browser page", "medium", "page changed"),
    "agent.spawn": Spec("agent", "delegate to a subagent", "medium", "report returned"),
    "artifact.publish": Spec("artifact", "publish or read a claude.ai artifact", "medium", "url returned"),
    "skill.invoke": Spec("skill", "load a skill's instructions", "low", "instructions loaded"),
    "tool.load": Spec("tool", "load deferred tool schemas", "low", "schemas returned"),
    "user.ask": Spec("user", "ask the user a question", "low", "answer returned"),
    "user.send_file": Spec("user", "send a file to the user", "low", "delivered"),
    "shell.echo": Spec("shell", "print text", "low", "text printed"),
    "shell.other": Spec("shell", "unclassified shell command", "medium", "exit 0"),
    "mcp.call": Spec("mcp", "call an MCP server tool", "medium", "result returned"),
    "tool.other": Spec("tool", "unclassified tool call", "medium", "result returned"),
}


def spec_for(name: str) -> Spec:
    """The description for a vocabulary name; unknown names get a generic one."""
    if name in SPECS:
        return SPECS[name]
    family = name.split(".", 1)[0]
    return Spec(family, f"{name.replace('.', ' ')}", "medium", "exit 0")


# Commands that only set up the shell and say nothing about intent.
_PREAMBLE = re.compile(
    r"(?i)^(cd|set-location|pushd|popd|export|set|[A-Z_][A-Z0-9_]*=\S*$|"
    r"try\b|if\s*\(\$PSStyle|\$ErrorActionPreference)(\s|$)")
# A PowerShell assignment in front of a command: `$p = Start-Process ...`.
_ASSIGN = re.compile(r"^\$[A-Za-z_][\w:]*\s*=\s*")
# Wrappers whose payload is the real command.
_TIMEOUT = re.compile(r"^timeout\s+\d+[smh]?\s+")
_NESTED_SHELL = re.compile(r"(?i)^(?:powershell|pwsh|bash|sh|cmd)(?:\.exe)?\s+(?:-\w+\s+)*"
                           r"(?:-c|-command|/c)\s+(?P<body>.+)$", re.S)


def _split_chain(command: str) -> list[str]:
    """Split on ; && || | and newlines -- but never inside quotes, braces or
    parentheses, so `py -c "a; b"` and `{ $_.x; }` stay whole."""
    pieces, buf, quote, depth, i = [], [], None, 0, 0
    text = command or ""
    while i < len(text):
        ch = text[i]
        if quote:
            buf.append(ch)
            if ch == "\\" and quote == '"' and i + 1 < len(text):
                buf.append(text[i + 1])
                i += 2
                continue
            if ch == quote:
                quote = None
        elif ch in "'\"":
            quote = ch
            buf.append(ch)
        elif ch in "({":
            depth += 1
            buf.append(ch)
        elif ch in ")}":
            depth = max(0, depth - 1)
            buf.append(ch)
        elif depth == 0 and (ch in ";\n" or text.startswith(("&&", "||"), i) or ch == "|"):
            pieces.append("".join(buf))
            buf = []
            i += 2 if text.startswith(("&&", "||"), i) else 1
            continue
        else:
            buf.append(ch)
        i += 1
    pieces.append("".join(buf))
    return pieces

_PY_EXE = re.compile(r"(?i)^(?:\S*[\\/])?(py|python[\d.]*|pythonw?)(?:\.exe)?$")


def _tokens(segment: str) -> list[str]:
    """Split one command into words, tolerating unbalanced quotes."""
    try:
        return shlex.split(segment, posix=True)
    except ValueError:
        return segment.split()


def _segments(command: str, _depth: int = 0) -> list[str]:
    """The meaningful pieces of a chained command line: preamble dropped,
    assignments and wrappers (timeout, powershell -c "...") peeled off."""
    out = []
    for piece in _split_chain(command):
        piece = piece.strip()
        if not piece or _PREAMBLE.match(piece):
            continue
        piece = _ASSIGN.sub("", piece)                               # $x = cmd ...
        piece = re.sub(r"^(?:[A-Z_][A-Z0-9_]*=\S+\s+)+", "", piece)  # FOO=1 cmd ...
        piece = _TIMEOUT.sub("", piece)                              # timeout 600 cmd ...
        nested = _NESTED_SHELL.match(piece)
        if nested and _depth < 2:                                    # powershell -c "..."
            body = nested.group("body").strip()
            if len(body) > 1 and body[0] == body[-1] and body[0] in "'\"":
                body = body[1:-1]
            out.extend(_segments(body, _depth + 1))
            continue
        if piece and not piece.startswith(("\"", "'")):              # bare string literal: noise
            out.append(piece)
    return out


def classify_python(words: list[str], segment: str) -> str:
    """Name a python invocation from its arguments."""
    args = words[1:]
    while args and re.match(r"^-\d", args[0]):          # py -3.12
        args = args[1:]
    while args and args[0] in ("-u", "-B", "-X", "-W", "-O"):
        args = args[2:] if args[0] in ("-X", "-W") else args[1:]
    if "--selftest" in segment or "--self-test" in segment:
        return "python.selftest"
    if not args:
        return "python.run_script"
    if args[0] == "-m" and len(args) > 1:
        module, rest = args[1], args[2:]
        if module == "py_compile" or module == "compileall":
            return "python.syntax_check"
        if module == "pip":
            return "dependency.install" if "install" in rest else "python.run_module"
        if module == "rerender":
            if "stills" in rest:
                return "render.stills"
            if "render" in rest:
                return "render.video"
            return "render.queue"
        if module.startswith("wedge_book"):
            sub = module.split(".", 1)[1] if "." in module else ""
            if sub == "check":
                return "book.check"
            if sub == "build":
                return "book.build"
            if sub == "renumber":
                return "book.renumber"
            if sub == "ledger":
                return "book.ledger"
            if sub == "plates" and "--render" in rest:
                return "render.plates"
            return "book.run_module"
        if module.startswith("two_v_demo.release"):
            return "render.video"
        if module.startswith("intelligence"):
            return "intelligence.inspect"
        return "python.run_module"
    if args[0] == "-c":
        code = " ".join(args[1:])
        if "_selftest" in code or "validate_" in code:
            return "python.selftest"
        if "py_compile" in code or "ast.parse" in code:
            return "python.syntax_check"
        if "write_config" in code or "launcher" in code:
            return "project.launch"
        if "validate" in code or "selftest" in code:
            return "python.selftest"
        if "_run_masterclass" in code and "shots" in code:
            return "render.stills"
        return "python.inline"
    if args[0] == "-":
        return "python.inline"
    script = args[0].replace("\\", "/").rsplit("/", 1)[-1].lower()
    if script.startswith("presenter_studio"):
        if "--export" in args:
            return "render.video"
        if "--shots" in args:
            return "render.stills"
        return "presenter.run"
    if script in ("launcher.py", "assembly_line.py", "assembly_line_simple.py",
                  "two_v_masterclass.py", "local_voice_studio.py") or "launcher" in script:
        return "project.launch"
    if "render_plates" in script:
        return "render.plates"
    return "python.run_script"


#: Simple first-word rules for shells (both Bash and PowerShell).
_FIRST_WORD = {
    "ffprobe": "media.inspect",
    "get-process": "process.inspect", "tasklist": "process.inspect", "ps": "process.inspect",
    "get-ciminstance": "process.inspect", "get-wmiobject": "process.inspect",
    "stop-process": "process.kill", "taskkill": "process.kill", "kill": "process.kill",
    "start-process": "process.start",
    "start-sleep": "process.wait", "sleep": "process.wait", "until": "process.wait",
    "wait-process": "process.wait",
    "get-childitem": "filesystem.list", "ls": "filesystem.list", "dir": "filesystem.list",
    "gci": "filesystem.list",
    "get-content": "filesystem.read", "cat": "filesystem.read", "type": "filesystem.read",
    "head": "filesystem.read", "tail": "filesystem.read", "gc": "filesystem.read",
    "select-string": "filesystem.search", "grep": "filesystem.search", "rg": "filesystem.search",
    "find": "filesystem.search", "where.exe": "filesystem.search", "where": "filesystem.search",
    "remove-item": "filesystem.delete", "rm": "filesystem.delete", "del": "filesystem.delete",
    "copy-item": "filesystem.copy", "move-item": "filesystem.copy", "cp": "filesystem.copy",
    "mv": "filesystem.copy",
    "new-item": "filesystem.mkdir", "mkdir": "filesystem.mkdir",
    "test-path": "filesystem.check", "get-item": "filesystem.check", "stat": "filesystem.check",
    "echo": "shell.echo", "write-output": "shell.echo", "write-host": "shell.echo", "printf": "shell.echo",
    "set-content": "filesystem.write", "out-file": "filesystem.write",
    "awk": "filesystem.read", "wc": "filesystem.read", "less": "filesystem.read",
    "nvidia-smi": "process.inspect", "where-object": "process.inspect",
    "select-object": "shell.echo", "format-table": "shell.echo", "ft": "shell.echo",
}


def classify_segment(segment: str) -> str | None:
    """Name one command segment, or None if nothing matches."""
    words = _tokens(segment)
    if not words:
        return None
    first = words[0]
    low = first.lower().rsplit("/", 1)[-1].rsplit("\\", 1)[-1]
    if low in ("&", "."):                 # PowerShell call operator: & "C:\x.exe" ...
        words = words[1:]
        if not words:
            return None
        first = words[0]
        low = first.lower().rsplit("/", 1)[-1].rsplit("\\", 1)[-1]
    if _PY_EXE.match(first) or low.endswith("python.exe"):
        return classify_python(words, segment)
    if low == "git":
        sub = next((w for w in words[1:] if not w.startswith("-")), "")
        name = f"git.{sub}"
        return name if name in SPECS else "git.other"
    if low in ("ffmpeg", "ffmpeg.exe"):
        if "-frames:v" in segment and ".png" in segment.lower():
            return "media.extract_frame"
        return "media.transcode"
    if low in ("npm", "npx", "pnpm", "yarn"):
        if len(words) > 1 and words[1] in ("install", "i", "add", "ci"):
            return "dependency.install"
        return "npm.run"
    if low in ("pip", "pip3"):
        return "dependency.install" if "install" in words else "shell.other"
    if low in ("claude", "claude.exe"):  # a headless Claude Code run is a delegated agent
        return "agent.spawn"
    if low == "sed":                     # sed -i edits in place; plain sed only reads
        return "filesystem.edit" if any(w.startswith("-i") for w in words[1:]) else "filesystem.read"
    if low in _FIRST_WORD:
        return _FIRST_WORD[low]
    return None


def classify_command(command: str) -> str:
    """Name a shell command line by its most significant segment.

    The first segment that matches a rule wins, after dropping preamble such as
    ``cd`` and variable assignments; a line of pure plumbing is shell.other."""
    if re.match(r"^\s*(until|while)\b", command or ""):     # a polling loop is waiting
        return "process.wait"
    for segment in _segments(command):
        name = classify_segment(segment)
        if name and name not in ("shell.echo", "process.wait", "filesystem.check"):
            return name
    # Nothing significant: fall back to the first segment that matched at all.
    for segment in _segments(command):
        name = classify_segment(segment)
        if name:
            return name
    return "shell.other"


#: Tool name -> vocabulary name for Claude Code's non-shell tools.
_TOOL_MAP = {
    "Read": "filesystem.read", "NotebookRead": "filesystem.read",
    "Grep": "filesystem.search", "Glob": "filesystem.search",
    "Edit": "filesystem.edit", "MultiEdit": "filesystem.edit", "NotebookEdit": "filesystem.edit",
    "Write": "filesystem.write",
    "WebSearch": "web.search", "WebFetch": "web.fetch",
    "Agent": "agent.spawn", "Task": "agent.spawn",
    "Artifact": "artifact.publish", "ArtifactData": "artifact.publish",
    "Skill": "skill.invoke", "ToolSearch": "tool.load",
    "AskUserQuestion": "user.ask", "SendUserFile": "user.send_file",
    "Monitor": "process.wait", "TaskStop": "process.kill",
}


def classify_tool(tool_name: str, tool_input) -> str:
    """The vocabulary name for one tool call."""
    tool_input = tool_input if isinstance(tool_input, dict) else {}
    if tool_name in ("Bash", "PowerShell"):
        return classify_command(str(tool_input.get("command", "")))
    if tool_name in _TOOL_MAP:
        return _TOOL_MAP[tool_name]
    if tool_name.startswith("mcp__") and "Browser" in tool_name:
        tail = tool_name.rsplit("__", 1)[-1]
        if tail in ("navigate", "preview_start", "tabs_create"):
            return "browser.navigate"
        if tail in ("computer", "form_input", "browser_batch"):
            return "browser.interact"
        return "browser.inspect"
    if tool_name.startswith("mcp__"):
        return "mcp.call"
    return "tool.other"


def describe_input(tool_name: str, tool_input) -> str:
    """The one string that best represents a tool call's input, for patterns."""
    tool_input = tool_input if isinstance(tool_input, dict) else {}
    for key in ("command", "file_path", "pattern", "url", "query", "path", "skill", "description"):
        if tool_input.get(key):
            return str(tool_input[key])
    return tool_name


def touched_files(tool_name: str, tool_input) -> tuple[list[str], str]:
    """(paths, how) a tool call read/edited/searched, symbolised; how is
    'read' | 'edit' | 'search' | ''."""
    tool_input = tool_input if isinstance(tool_input, dict) else {}
    path = tool_input.get("file_path") or tool_input.get("notebook_path")

    def norm(p) -> str:                  # one spelling per file: symbols, forward slashes
        return symbolize(str(p)).replace("\\", "/")

    if tool_name in ("Read", "NotebookRead") and path:
        return [norm(path)], "read"
    if tool_name in ("Edit", "MultiEdit", "Write", "NotebookEdit") and path:
        return [norm(path)], "edit"
    if tool_name in ("Grep", "Glob"):
        return [norm(tool_input.get("path") or "<PROJECT_ROOT>")], "search"
    return [], ""
