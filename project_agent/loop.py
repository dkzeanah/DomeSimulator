"""The agent loop: planners, execution, and the run manifest.

Two planners implement the same interface:

* :class:`RulePlanner` — a deterministic command parser.  It proves the
  whole chain (chat text -> plan -> tools -> stills -> review) with no
  API key at all, and doubles as the reference behavior for the LLM.
* :class:`LlmPlanner` — an OpenAI-compatible function-calling client
  (works with OpenAI, or any compatible endpoint: Ollama, LM Studio,
  vLLM, DeepSeek, Groq, ...).  Configure with ``PROJECT_AGENT_API_KEY``
  / ``PROJECT_AGENT_API_BASE`` / ``PROJECT_AGENT_MODEL``.

Every run writes a manifest — brief, tool calls, outputs, gates — so a
produce run is an auditable file, not a memory.
"""

from __future__ import annotations

import json
import re
import time
import urllib.request
from dataclasses import dataclass, field
from pathlib import Path

from . import config, ledger, tools
from .config import ensure_dirs

SYSTEM_PROMPT = """You are the DomeSim Project Agent: a hyper-specialized
assistant that produces media (stills, narrated films, books) for the
DomeSim repository by operating its programmatic tools. You do not guess
numbers, you do not run shell commands, and you never write engine code.

House rules (from the repository):
- Every on-screen number is computed by code that proves it (use
  query_facts), or declared as an external constant with a unit and
  source (use declare_constant). Never type a figure into a caption.
- Unknown figures become ledger items (scan_claims, resolve), never
  silent guesses. Unsourceable claims are dropped and recorded.
- Render stills before exporting video and look at every one (view).
- Verify every render by frame count (verify_render).
- Rendered output is append-only; never overwrite an existing file.
- Lay rows along X, keep the left third clear in teaching style.

Knowledge base summary:
{kb_summary}

Pending ledger items:
{ledger_pending}

Answer conversationally but act through tools. When the user asks for
media, plan the minimal tool sequence and execute it. Report what was
decided, what remains unresolved, and the files produced."""


@dataclass
class ToolCall:
    name: str
    args: dict
    result: dict = field(default_factory=dict)


def _system_message() -> dict:
    from . import spec
    kb = spec.load_kb()
    summary = spec.kb_summary(kb)
    pending = ledger.ledger_text(only="pending")
    return {"role": "system", "content":
            SYSTEM_PROMPT.format(kb_summary=summary, ledger_pending=pending)}


# ---------------------------------------------------------------------------
# RulePlanner: deterministic parsing — no API key needed
# ---------------------------------------------------------------------------


BOOLEAN_FLAGS = frozenset({
    "no_narration", "figures", "pdf", "strict", "resume", "silent", "quiet",
})
"""Recipe parameters that are switches, not values.

Named explicitly because guessing is ambiguous: ``--no_narration
declare=cord=275`` is a switch followed by a parameter, while ``--declare
cord=275`` is a parameter followed by its value, and the two are
indistinguishable without knowing which names take a value. The first version
guessed, and quietly swallowed the declaration as the switch's value."""


def parse_produce_args(tokens: list[str]) -> dict:
    """Parse recipe parameters from chat/CLI tokens.

    Supports ``--key value`` and ``key=value`` forms; ``times`` splits on
    commas, ``declare`` accumulates; a switch from :data:`BOOLEAN_FLAGS`
    becomes ``"1"``; a bare token ending in .txt/.md/.py/.json becomes
    ``source``.
    """
    params: dict = {}

    def set_param(key: str, value: str) -> None:
        if key == "times":
            params[key] = [s.strip() for s in value.split(",") if s.strip()]
        elif key == "declare":
            params.setdefault("declare", []).append(value)
        else:
            params[key] = value

    index = 0
    while index < len(tokens):
        token = tokens[index]
        if token.startswith("--"):
            token = token[2:]
        if "=" in token:
            key, value = token.split("=", 1)
            set_param(key, value)
            index += 1
        elif tokens[index].startswith("--"):
            following = tokens[index + 1] if index + 1 < len(tokens) else ""
            takes_value = (token not in BOOLEAN_FLAGS and following
                           and not following.startswith("--"))
            if takes_value:
                set_param(token, following)
                index += 2
            else:
                set_param(token, "1")  # a switch
                index += 1
        else:
            if token.lower().endswith((".txt", ".md", ".py", ".json")):
                params.setdefault("source", token)
            elif not params.get("title"):
                params["title"] = token
            index += 1
    return params


def _parse_tool_calls(text: str) -> list[ToolCall]:
    """Best-effort command parsing. Returns [] when nothing matches."""
    t = text.strip()
    if not t:
        return []

    def one(name: str, args: dict) -> list[ToolCall]:
        return [ToolCall(name=name, args=args)]

    low = t.lower()

    if low in ("sync", "sync knowledge", "sync_knowledge"):
        return one("sync_knowledge", {})
    if low in ("help", "?", "tools"):
        return one("help", {})
    if low in ("ledger",):
        return one("list_items", {"kind": "ledger"})

    match = re.match(r"^list\s+(\w+)$", low)
    if match:
        return one("list_items", {"kind": match.group(1)})

    match = re.match(r"^facts?\s+([\w.]+)(?:\s+(.*))?$", low)
    if match:
        args: dict = {"id": match.group(1)}
        params: dict = {}
        for token in re.findall(r"(\w+)\s*=\s*([\w.]+)", match.group(2) or ""):
            params[token[0]] = token[1]
        if params:
            args["params"] = params
        return one("query_facts", args)

    match = re.match(r"^selftest\s+(\w+)(?:\s+lesson=(\w+))?$", low)
    if match:
        args = {"tool": match.group(1)}
        if match.group(2):
            args["lesson"] = match.group(2)
        return one("selftest", args)

    match = re.match(r"^stills?\s+(\w+)\s+at\s+([\d\s,]+)"
                     r"(?:\s+lesson=(\w+))?(?:\s+demo=([\w]+))?"
                     r"(?:\s+size=(\d+x\d+))?$", low)
    if match:
        args = {
            "backend": match.group(1),
            "times": [s.strip() for s in match.group(2).split(",") if s.strip()],
        }
        if match.group(3):
            args["lesson"] = match.group(3)
        if match.group(4):
            args["demo"] = match.group(4)
        if match.group(5):
            args["size"] = match.group(5)
        return one("render_stills", args)

    match = re.match(r"^verify\s+(.+)$", low)
    if match:
        return one("verify_render", {"path": match.group(1).strip()})

    match = re.match(r"^read\s+(.+)$", low)
    if match:
        return one("read_file", {"path": match.group(1).strip()})

    match = re.match(r"^book\s+(\w+)$", low)
    if match:
        return one("export_book", {"action": match.group(1)})

    match = re.match(r"^view\s*(.*)$", low)
    if match:
        args = {} if not match.group(1).strip() else {"path": match.group(1).strip()}
        return one("view", args)

    match = re.match(r"^declare\s+(\w+)\s*=\s*(.+?)\s*(?:\|\s*(.*))?$", t)
    if match:
        name = match.group(1)
        value_unit = match.group(2).strip()
        parts = value_unit.split(None, 1)
        args = {"name": name, "value": parts[0],
                "unit": parts[1] if len(parts) > 1 else ""}
        if match.group(3):
            args["source"] = match.group(3).strip()
        return one("declare_constant", args)

    match = re.match(r"^resolve\s+(led-\d+)\s*=\s*(.+?)\s*(?:\|\s*(.*))?$", t)
    if match:
        args = {"id": match.group(1), "answer": match.group(2).strip()}
        if match.group(3):
            args["source"] = match.group(3).strip()
        return one("resolve", args)

    match = re.match(r"^drop\s+(led-\d+)(?:\s+(.*))?$", low)
    if match:
        args = {"id": match.group(1)}
        if match.group(2):
            args["note"] = match.group(2).strip()
        return one("drop_claim", args)

    match = re.match(r"^claims?\s+(?:file=)?(.+\.txt)$", low)
    if match:
        return one("scan_claims", {"path": match.group(1).strip()})

    match = re.match(r"^constants(?:\s+(.+))?$", low)
    if match:
        args = {}
        if match.group(1):
            args["out"] = match.group(1).strip()
        return one("constants_module", args)

    match = re.match(r"^produce\s+(\w+)(?:\s+(.*))?$", low)
    if match:
        tokens = [m[0] or m[1] for m in
                  re.findall(r'"([^"]*)"|(\S+)', match.group(2) or "")]
        params = parse_produce_args(tokens)
        return one("run_recipe", {"recipe": match.group(1), "params": params})

    # A couple of natural-language fallbacks for the demo path.
    match = re.search(r"stills?\b.*\b(lesson|film)?\s*(\w+)\b.*\b(\d+)\b.*\b(\d+)\b",
                      low)
    if match and re.search(r"\bstill|shot|frame|screenshot\b", low):
        return one("render_stills", {
            "backend": "masterclass",
            "lesson": match.group(2) if match.group(2) != "the" else "2v",
            "times": [match.group(3), match.group(4)],
        })
    return []


class RulePlanner:
    """Deterministic planner over the command grammar."""

    name = "rule"
    max_steps = 1
    last_text = ""

    def plan(self, messages: list[dict]) -> list[ToolCall]:
        text = messages[-1]["content"] if messages else ""
        return _parse_tool_calls(text)

    def final_answer(self) -> str:
        return ("(rule planner) — command not recognized. Try: list facts, "
                "facts wedge.tree_yield, stills masterclass at 30,90 "
                "lesson=2v, selftest masterclass lesson=2v, declare name = "
                "value unit | source, resolve led-0001 = answer, claims "
                "file=path.txt, book read_html, verify path.mp4, view, help, "
                "or produce <film|presenter|book|stills|claims> key=... "
                "title=... source=... export=... "
                "Or configure PROJECT_AGENT_API_KEY for free-text planning.")


# ---------------------------------------------------------------------------
# LlmPlanner: OpenAI-compatible function calling (stdlib only)
# ---------------------------------------------------------------------------


class PlannerError(RuntimeError):
    """The planner could not produce a plan (network, endpoint, or reply)."""


class LlmPlanner:
    """Function-calling client against any OpenAI-compatible endpoint.

    Endpoints vary: a local Ollama or LM Studio returns different error shapes
    from OpenAI, and any of them can be down. Every failure here is raised as a
    :class:`PlannerError` with the endpoint's own words, so the REPL prints a
    usable message instead of a stack trace.
    """

    name = "llm"

    def __init__(self) -> None:
        self.base = config.llm_api_base()
        self.model = config.llm_model()
        self.key = config.llm_api_key()
        self.timeout = config.llm_timeout()
        self.max_steps = 8
        self.last_text = ""

    def _post(self, payload: dict) -> dict:
        request = urllib.request.Request(
            f"{self.base}/chat/completions",
            data=json.dumps(payload).encode("utf-8"),
            headers={"Content-Type": "application/json",
                     "Authorization": f"Bearer {self.key}"},
        )
        try:
            with urllib.request.urlopen(request, timeout=self.timeout) as response:
                body = response.read().decode("utf-8", errors="replace")
        except urllib.error.HTTPError as exc:
            detail = exc.read().decode("utf-8", errors="replace")[:400]
            raise PlannerError(
                f"{self.base} returned HTTP {exc.code}: {detail or exc.reason}"
            ) from None
        except urllib.error.URLError as exc:
            raise PlannerError(
                f"cannot reach {self.base}: {exc.reason}. Check "
                "PROJECT_AGENT_API_BASE, or unset PROJECT_AGENT_API_KEY to use "
                "the rule planner.") from None
        except TimeoutError:
            raise PlannerError(
                f"{self.base} did not answer within {self.timeout}s") from None
        try:
            data = json.loads(body)
        except json.JSONDecodeError:
            raise PlannerError(
                f"{self.base} returned something that is not JSON: "
                f"{body[:200]}") from None
        if isinstance(data, dict) and data.get("error"):
            error = data["error"]
            message = (error.get("message") if isinstance(error, dict)
                       else str(error))
            raise PlannerError(f"{self.base} reported: {message}")
        return data

    def plan(self, messages: list[dict]) -> list[ToolCall]:
        response = self._post({
            "model": self.model,
            "messages": messages,
            "tools": tools.tool_schemas(),
        })
        choices = response.get("choices") or []
        if not choices:
            raise PlannerError(
                f"{self.model} returned no choices: {str(response)[:200]}")
        message = choices[0].get("message") or {}
        # Kept so the caller can show what the model said. A reply with no tool
        # calls used to be discarded, which looked exactly like a hang.
        self.last_text = str(message.get("content") or "").strip()
        calls: list[ToolCall] = []
        for call in message.get("tool_calls") or []:
            function = call.get("function") or {}
            name = function.get("name")
            if not name:
                continue
            try:
                args = json.loads(function.get("arguments") or "{}")
            except json.JSONDecodeError:
                args = {}
            if not isinstance(args, dict):
                args = {}
            calls.append(ToolCall(name=name, args=args))
        return calls

    def final_answer(self) -> str:
        return self.last_text or "done"


# ---------------------------------------------------------------------------
# The run loop
# ---------------------------------------------------------------------------


def execute(calls: list[ToolCall]) -> list[ToolCall]:
    for call in calls:
        print(f"  -> {call.name} {json.dumps(call.args, default=str)[:160]}")
        call.result = tools.dispatch(call.name, call.args)
        status = "ok" if call.result.get("ok") else "FAIL"
        detail = ""
        for key in ("paths", "written", "error", "summary", "returncode",
                    "message", "tail", "elapsed_s"):
            if call.result.get(key):
                detail = f"  {key}: {str(call.result[key])[:300]}"
                break
        print(f"     [{status}] {detail}")
    return calls


def run_chat(user_text: str, run_id: str, planner=None) -> dict:
    """One chat turn: plan -> execute -> manifest. Returns the manifest."""
    ensure_dirs()
    planner = planner or (LlmPlanner() if config.llm_configured() else RulePlanner())
    if planner.name == "llm":
        messages: list[dict] = [_system_message(), {"role": "user",
                                                    "content": user_text}]
    else:
        messages = [{"role": "user", "content": user_text}]

    all_calls: list[ToolCall] = []
    errors: list[str] = []
    for _ in range(getattr(planner, "max_steps", 1)):
        try:
            calls = planner.plan(messages)
        except PlannerError as exc:
            # A planner that cannot reach its endpoint ends the turn with a
            # message; it must never take the REPL down with it.
            print(f"  planner: {exc}")
            errors.append(str(exc))
            break
        said = getattr(planner, "last_text", "")
        if said:
            print(f"  {said}")
        if not calls:
            break
        execute(calls)
        all_calls.extend(calls)
        if planner.name == "rule":
            break
        # Append assistant + tool results and continue the LLM loop.
        assistant = {"role": "assistant", "content": None, "tool_calls": [
            {"id": f"call_{i}", "type": "function",
             "function": {"name": call.name,
                          "arguments": json.dumps(call.args, default=str)}}
            for i, call in enumerate(calls)]}
        messages.append(assistant)
        for i, call in enumerate(calls):
            messages.append({"role": "tool", "tool_call_id": f"call_{i}",
                             "content": json.dumps(call.result, default=str)})
    run_dir = config.RUNS_DIR / run_id
    run_dir.mkdir(parents=True, exist_ok=True)
    manifest = {
        "run_id": run_id,
        "planner": planner.name,
        "brief": user_text,
        "said": getattr(planner, "last_text", ""),
        "errors": errors,
        "tool_calls": [
            {"name": call.name, "args": call.args, "ok": call.result.get("ok"),
             "result": call.result}
            for call in all_calls
        ],
        "gates": {
            "stills_reviewed": any(c.name == "view" for c in all_calls),
            "selftest_run": any(c.name == "selftest" and c.result.get("ok")
                                for c in all_calls),
            "render_verified": any(c.name == "verify_render" and c.result.get("ok")
                                   for c in all_calls),
        },
    }
    (run_dir / "manifest.json").write_text(
        json.dumps(manifest, indent=2, default=str), encoding="utf-8")
    manifest["manifest_path"] = str(run_dir / "manifest.json")

    if planner.name == "rule" and not all_calls and not errors:
        print(planner.final_answer())
    return manifest
