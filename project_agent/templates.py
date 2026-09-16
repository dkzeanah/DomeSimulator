"""Editing the repository safely: scaffolding fills and lesson registration.

Everything here follows three rules:

1. **Never clobber authored content.**  Template fills replace *exact
   placeholder text* that the scaffolder generated; if the placeholder is gone,
   the file has been authored by hand and the step is skipped with a report
   instead of a blind overwrite.
2. **Never leave the repo half-edited.**  Registration is the documented
   three-part contract (``lesson_registry.py`` + ``deliverables.py`` +
   ``render_presets.py`` — the repo's own validators insist a lesson appears in
   all three).  Every file is backed up first, each edit is anchored on exact
   text, and the whole registration is validated by running the repo's own
   validators in a subprocess; any failure rolls all three files back.
3. **Fail before touching anything.**  :func:`preflight` checks that every
   anchor this module needs still exists.  The first version anchored the
   registry's tuple on a regex that assumed one lesson name per line; the day a
   line held two, registration failed *after* the other two files had already
   been written.

Backups live in ``project_agent/backups/`` with a manifest, not beside the
files they copy: agent litter in the repository root is how you end up with
``render_presets.py.agent-bak-pristine`` sitting in a diff months later.
"""

from __future__ import annotations

import json
import os
import re
import subprocess
import textwrap
import time
from pathlib import Path

from . import config

# The three files registration touches, and the anchor each edit needs.
REGISTRY_PATH = config.REPO_ROOT / "two_v_demo" / "lesson_registry.py"
DELIVERABLES_PATH = config.REPO_ROOT / "two_v_demo" / "deliverables.py"
PRESETS_PATH = config.REPO_ROOT / "render_presets.py"

REGISTRY_IMPORT_ANCHOR = "from .lessons import TWO_V_LESSON, Lesson"
REGISTRY_DICT_ANCHOR = "LESSONS: dict[str, Lesson] = {"
DELIVERABLES_ANCHOR = "\n)\n\n\nDELIVERABLE_BY_LESSON"
PRESETS_ANCHOR = "\n)\n\n\nPRESET_BY_KEY"


# ---------------------------------------------------------------------------
# Generic safe subprocess (output to a log file, never a pipe)
# ---------------------------------------------------------------------------


def run_process(args: list[str], label: str,
                timeout: int = config.TIMEOUT_QUICK) -> dict:
    """Run a python program with stdout/stderr to a log file.

    A timeout is reported, never raised: a recipe that calls this needs to end
    with a manifest and a reason, not a traceback from inside a helper.
    """
    log_dir = config.RUNS_DIR / "_last"
    log_dir.mkdir(parents=True, exist_ok=True)
    log_path = log_dir / f"{label}_{time.strftime('%H%M%S')}.log"
    timed_out = False
    returncode = -1
    try:
        with log_path.open("w", encoding="utf-8") as logf:
            proc = subprocess.run(
                [config.agent_python(), *args],
                cwd=str(config.REPO_ROOT),
                env={**os.environ, "PYTHONUNBUFFERED": "1"},
                stdout=logf, stderr=subprocess.STDOUT, timeout=timeout,
            )
        returncode = proc.returncode
    except subprocess.TimeoutExpired:
        timed_out = True
    except OSError as exc:
        return {"ok": False, "returncode": -1, "log": str(log_path),
                "tail": f"could not start {args[:2]}: {exc}",
                "error": f"{type(exc).__name__}: {exc}"}
    tail = ""
    if log_path.is_file():
        tail = "\n".join(
            log_path.read_text(encoding="utf-8", errors="replace")
            .splitlines()[-25:])
    result = {"ok": (not timed_out) and returncode == 0,
              "returncode": returncode, "log": str(log_path), "tail": tail}
    if timed_out:
        result["timeout"] = True
        result["error"] = f"timed out after {timeout}s"
    return result


def validate_python(path: Path) -> dict:
    """py_compile one file.  Returns {ok, error}."""
    result = run_process(["-m", "py_compile", str(path)],
                         f"compile_{path.stem}", timeout=120)
    if not result["ok"]:
        result["error"] = result.get("error") or result["tail"]
    return result


def validate_registration(key: str) -> dict:
    """Run the repo's own validators against the registered lesson — the same
    checks the launcher smoke test and the selftests enforce."""
    probe = (
        "import sys; sys.path.insert(0, '.'); "
        f"from two_v_demo.lesson_registry import get_lesson; get_lesson({key!r}); "
        "from two_v_demo.deliverables import validate_deliverables; "
        "validate_deliverables(); "
        "from render_presets import validate_render_presets; "
        "validate_render_presets(); print('registration ok')"
    )
    return run_process(["-c", probe], f"validate_register_{key}",
                       timeout=config.TIMEOUT_QUICK)


# ---------------------------------------------------------------------------
# Backups
# ---------------------------------------------------------------------------


def _backup(path: Path) -> Path:
    """Copy ``path`` into the agent's own backup folder and record it."""
    config.ensure_dirs()
    stamp = time.strftime("%Y%m%d-%H%M%S")
    backup = config.BACKUPS_DIR / f"{path.name}.{stamp}.bak"
    counter = 2
    while backup.exists():
        backup = config.BACKUPS_DIR / f"{path.name}.{stamp}-{counter}.bak"
        counter += 1
    backup.write_text(path.read_text(encoding="utf-8"), encoding="utf-8")
    manifest = config.BACKUPS_DIR / "manifest.jsonl"
    with manifest.open("a", encoding="utf-8") as handle:
        handle.write(json.dumps({
            "when": stamp,
            "original": config.relative_to_repo(path),
            "backup": backup.name,
        }) + "\n")
    return backup


def _restore(path: Path, backup: Path) -> None:
    path.write_text(backup.read_text(encoding="utf-8"), encoding="utf-8")


def _write_if_changed(path: Path, text: str) -> bool:
    """Write only when the content actually differs."""
    if path.is_file() and path.read_text(encoding="utf-8") == text:
        return False
    path.write_text(text, encoding="utf-8")
    return True


# ---------------------------------------------------------------------------
# Preflight: do the anchors this module needs still exist?
# ---------------------------------------------------------------------------


def preflight() -> dict:
    """Check every anchor registration depends on, before any file is written.

    Returns ``{ok, checks: [{name, ok, detail}]}``.  Run by the agent's
    selftest, so drift in the engine files is a failing check with a clear
    message rather than a half-finished registration.
    """
    checks: list[dict] = []

    def check(name: str, ok: bool, detail: str = "") -> None:
        checks.append({"name": name, "ok": bool(ok), "detail": detail})

    for path in (REGISTRY_PATH, DELIVERABLES_PATH, PRESETS_PATH):
        check(f"{path.name} exists", path.is_file(), str(path))

    if REGISTRY_PATH.is_file():
        text = REGISTRY_PATH.read_text(encoding="utf-8")
        check("registry import anchor", REGISTRY_IMPORT_ANCHOR in text,
              REGISTRY_IMPORT_ANCHOR)
        span = _registry_tuple_span(text)
        check("registry lesson tuple found", span is not None,
              "the LESSONS dict comprehension's tuple of lesson objects")
    if DELIVERABLES_PATH.is_file():
        text = DELIVERABLES_PATH.read_text(encoding="utf-8")
        check("deliverables tuple anchor", DELIVERABLES_ANCHOR in text,
              DELIVERABLES_ANCHOR.strip())
    if PRESETS_PATH.is_file():
        text = PRESETS_PATH.read_text(encoding="utf-8")
        check("presets tuple anchor", PRESETS_ANCHOR in text,
              PRESETS_ANCHOR.strip())
        check("presets _video helper", "def _video(" in text, "_video(...)")

    return {"ok": all(c["ok"] for c in checks), "checks": checks}


# ---------------------------------------------------------------------------
# 1. Constants injection into a scaffolded facts module
# ---------------------------------------------------------------------------

_CONSTANTS_BLOCK = re.compile(
    r"EXTERNAL_CONSTANTS(?:\s*:\s*tuple\[[^\]]*\])?\s*=\s*\(\n.*?\n\)",
    re.DOTALL)


def inject_constants(facts_path: Path, items: list) -> dict:
    """Replace the scaffolder's example-constant block with resolved declared
    ledger items.  Leaves the file untouched if nothing is resolved."""
    from . import ledger

    resolved = [i for i in items if isinstance(i, ledger.LedgerItem)
                and i.kind == "declared" and i.status == "resolved" and i.answer]
    if not facts_path.is_file():
        return {"ok": False, "error": f"no such facts module: {facts_path}"}
    text = facts_path.read_text(encoding="utf-8")
    if not resolved:
        return {"ok": True, "injected": 0,
                "note": "no resolved declared constants; placeholder left in place"}

    lines = ["EXTERNAL_CONSTANTS: tuple[tuple[str, object, str, str], ...] = ("]
    emitted: set[str] = set()
    for item in reversed(resolved):          # last resolution wins on a clash
        name = ledger.constant_name(item)
        if name in emitted:
            continue
        emitted.add(name)
        value, unit = ledger.split_value(item.answer)
        source = item.source or "resolution ledger"
        lines.append(f"    ({name!r}, {value!r}, {unit!r},")
        lines.append(f"     {source!r}),")
    lines.append(")")
    block = "\n".join(lines)

    if _CONSTANTS_BLOCK.search(text):
        text = _CONSTANTS_BLOCK.sub(lambda _m: block, text, count=1)
    elif "EXTERNAL_CONSTANTS" not in text:
        text = text.rstrip("\n") + "\n\n\n" + block + "\n"
    else:
        return {"ok": False,
                "error": "a constants block is present but not in the scaffold "
                         "shape (authored by hand?) — leaving the file untouched"}
    _write_if_changed(facts_path, text)
    return {"ok": True, "injected": len(emitted), "names": sorted(emitted)}


# ---------------------------------------------------------------------------
# 2. Narration replacement in a scaffolded lesson module
# ---------------------------------------------------------------------------

_PLACEHOLDER_CHAPTERS = (
    ("        \"One sentence that says what this lesson proves.\",",
     '        (\n            "Replace this narration with what is actually spoken. Keep it to prose a",\n            "person would say out loud; the numbers live on the card, not in the mouth.",\n        ),',
     '"What we are looking at"'),
    ("        \"What the parts sort into, and how many of each.\",",
     '        (\n            "One bar per class, measured rather than asserted. Say why the grouping is",\n            "the grouping, and what it costs the person building this.",\n        ),',
     '"The classes"'),
    ("        \"Every figure came from the model and can be recomputed.\",",
     '        (\n            "Close by saying what changed for the viewer. Every number in this lesson",\n            "came from a function that also proves itself, which is the only reason it",\n            "is worth putting on screen at all.",\n        ),',
     '"The whole thing, once more"'),
)


def _wrap_lines(sentence: str, width: int) -> list[str]:
    """One safe, quoted-ready string per wrapped line (no embedded newlines —
    each chunk becomes its own Python string literal)."""
    sentence = sentence.replace("\\", "").replace('"', "'")
    sentence = " ".join(sentence.split())
    return textwrap.wrap(sentence, width=width) or [""]


def replace_narration(lesson_path: Path, sentences: list[str]) -> dict:
    """Fill the scaffolder's three placeholder chapters with real copy.

    Teaching style speaks both the promise (headline) and the narration, so the
    fill gives each chapter *distinct* source sentences: the promise takes one,
    the narration takes the next two.  Chapters whose placeholder is already
    gone are left alone — authored content is never clobbered.
    """
    if not lesson_path.is_file():
        return {"ok": False, "error": f"no such lesson module: {lesson_path}"}
    usable = [s for s in sentences if len(s.strip()) >= 12]
    text = lesson_path.read_text(encoding="utf-8")
    if not usable:
        return {"ok": True, "replaced": 0, "note": "no source sentences given"}
    replaced = 0
    skipped = 0
    for index, (promise_ph, narration_ph, _title) in enumerate(_PLACEHOLDER_CHAPTERS):
        start = index * 3
        promise_sentence = usable[start] if start < len(usable) else ""
        narration_group = usable[start + 1:start + 3]
        if not promise_sentence and not narration_group:
            break
        if narration_ph not in text and promise_ph not in text:
            skipped += 1
            continue
        if narration_ph in text and narration_group:
            lines = ["        ("]
            for sentence in narration_group:
                for line in _wrap_lines(sentence, width=68):
                    lines.append(f'            "{line}",')
            lines.append("        ),")
            text = text.replace(narration_ph, "\n".join(lines), 1)
        if promise_ph in text and promise_sentence:
            clean = " ".join(promise_sentence.replace('"', "'").split())
            text = text.replace(promise_ph, f'        "{clean}",', 1)
        replaced += 1
    changed = _write_if_changed(lesson_path, text)
    return {"ok": True, "replaced": replaced, "skipped": skipped,
            "changed": changed,
            "note": f"{replaced} chapter(s) filled, {skipped} already authored"}


# ---------------------------------------------------------------------------
# 3. Lesson registration: the documented three-file contract
# ---------------------------------------------------------------------------


def _insert_import(registry_text: str, key: str, key_upper: str) -> str:
    if f"from .lesson_{key} import {key_upper}_LESSON" in registry_text:
        return registry_text                              # already there
    if REGISTRY_IMPORT_ANCHOR not in registry_text:
        raise ValueError("registry import anchor not found: "
                         f"{REGISTRY_IMPORT_ANCHOR!r}")
    return registry_text.replace(
        REGISTRY_IMPORT_ANCHOR,
        f"from .lesson_{key} import {key_upper}_LESSON\n{REGISTRY_IMPORT_ANCHOR}",
        1)


def _registry_tuple_span(registry_text: str) -> tuple[int, int] | None:
    """Character span of the lesson tuple inside the LESSONS dict.

    Found structurally — the opening ``(`` after the dict anchor, then its
    matching ``)`` — rather than by matching a line shape.  The tuple is
    hand-formatted and holds anywhere from one to several names per line, so
    any line-shaped pattern is a latent failure waiting for the next edit.
    """
    start = registry_text.find(REGISTRY_DICT_ANCHOR)
    if start < 0:
        return None
    open_paren = registry_text.find("(", start)
    if open_paren < 0:
        return None
    depth = 0
    for index in range(open_paren, len(registry_text)):
        char = registry_text[index]
        if char == "(":
            depth += 1
        elif char == ")":
            depth -= 1
            if depth == 0:
                return (open_paren, index)
    return None


def _insert_registry_entry(registry_text: str, key_upper: str) -> str:
    name = f"{key_upper}_LESSON"
    span = _registry_tuple_span(registry_text)
    if span is None:
        raise ValueError("registry lesson tuple not found (the LESSONS dict "
                         "comprehension changed shape)")
    open_paren, close_paren = span
    body = registry_text[open_paren + 1:close_paren]
    if re.search(rf"(?<![A-Z0-9_]){re.escape(name)}(?![A-Z0-9_])", body):
        return registry_text                              # already there
    indent = "                   "
    match = re.search(r"\n(\s+)\S", body)
    if match:
        indent = match.group(1)
    new_body = body.rstrip()
    new_body = f"{new_body},\n{indent}{name}"
    return registry_text[:open_paren + 1] + new_body + registry_text[close_paren:]


def _insert_deliverable(deliverables_text: str, key: str, filename: str,
                        summary: str) -> str:
    if f'Deliverable("{key}"' in deliverables_text:
        return deliverables_text                          # already there
    if DELIVERABLES_ANCHOR not in deliverables_text:
        raise ValueError("deliverables tuple anchor not found")
    entry = (
        f'    Deliverable("{key}", "{filename}",\n'
        f'                "{summary}",\n'
        "                compose=True),\n"
    )
    return deliverables_text.replace(
        DELIVERABLES_ANCHOR, f"\n{entry})\n\n\nDELIVERABLE_BY_LESSON", 1)


def _insert_preset(presets_text: str, key: str, filename: str,
                   summary: str) -> str:
    if f'_video("{key}"' in presets_text:
        return presets_text                               # already there
    if PRESETS_ANCHOR not in presets_text:
        raise ValueError("presets tuple anchor not found")
    entry = (
        f'    _video("{key}", "{key}", "{filename}",\n'
        f'           "{summary}"),\n'
    )
    return presets_text.replace(PRESETS_ANCHOR, f"\n{entry})\n\n\nPRESET_BY_KEY", 1)


def _quote_safe(text: str) -> str:
    """A summary that cannot break the string literal it is inserted into."""
    return " ".join(str(text).replace("\\", "").replace('"', "'").split())


def missing_deliverable_lessons() -> list[str]:
    """Lessons in the registry with no deliverables.py entry (the repo's own
    validate_deliverables treats every one of these as a failure)."""
    import importlib

    import two_v_demo.deliverables as deliverables
    import two_v_demo.lesson_registry as registry
    importlib.reload(deliverables)
    listed = {item.lesson for item in deliverables.DELIVERABLES}
    return sorted(set(registry.LESSONS) - listed - {"2v"})


def _repair_names() -> dict[str, str]:
    """Known filenames for lessons that were rendered but never registered."""
    return {
        "harvest": "two-trees-all-at-once.mp4",
        "pine_value": "the-20-dollar-pine.mp4",
        "why_build": "why-build-this-way.mp4",
    }


def _apply_registration(edits: list[tuple[Path, str]], validate,
                        label: str) -> dict:
    """Write a set of file edits, validate, and roll every one back on failure."""
    backups: list[tuple[Path, Path]] = []
    try:
        for path, content in edits:
            backups.append((path, _backup(path)))
            path.write_text(content, encoding="utf-8")
    except OSError as exc:
        for path, backup in reversed(backups):
            _restore(path, backup)
        return {"ok": False, "changed": False, "rolled_back": bool(backups),
                "error": f"could not write {label}: {exc}"}

    validation = validate()
    if not validation["ok"]:
        for path, backup in reversed(backups):
            _restore(path, backup)
        return {"ok": False, "changed": False, "rolled_back": True,
                "error": validation.get("error") or
                         f"validators failed after {label}",
                "tail": validation.get("tail", "")}
    return {"ok": True, "changed": True,
            "backups": [str(b) for _, b in backups]}


def repair_registration() -> dict:
    """Bring deliverables.py + render_presets.py back into line with the
    registry: every registered lesson gets a deliverable entry and a render
    preset, with backups and full re-validation.  Idempotent."""
    ready = preflight()
    if not ready["ok"]:
        broken = [c["name"] for c in ready["checks"] if not c["ok"]]
        return {"ok": False, "changed": False,
                "error": f"preflight failed: {', '.join(broken)}"}
    try:
        missing = missing_deliverable_lessons()
    except Exception as exc:                              # noqa: BLE001
        return {"ok": False, "changed": False,
                "error": f"cannot read the registry: {type(exc).__name__}: {exc}"}
    if not missing:
        return {"ok": True, "changed": False,
                "note": "deliverables and presets already cover the registry"}

    names = _repair_names()
    deliverables_text = DELIVERABLES_PATH.read_text(encoding="utf-8")
    presets_text = PRESETS_PATH.read_text(encoding="utf-8")
    try:
        for key in missing:
            filename = names.get(key, f"{key}-masterclass.mp4")
            summary = _quote_safe(
                f"Registered by the project agent repair step: the {key} "
                "lesson was in the registry without a deliverable entry.")
            deliverables_text = _insert_deliverable(
                deliverables_text, key, filename, summary)
            presets_text = _insert_preset(presets_text, key, filename, summary)
    except ValueError as exc:
        return {"ok": False, "changed": False, "error": str(exc)}

    def validate() -> dict:
        return run_process(
            ["-c", "import sys; sys.path.insert(0, '.'); "
                   "from two_v_demo.deliverables import validate_deliverables; "
                   "validate_deliverables(); "
                   "from render_presets import validate_render_presets; "
                   "validate_render_presets(); print('repair ok')"],
            "validate_repair", timeout=config.TIMEOUT_QUICK)

    result = _apply_registration(
        [(DELIVERABLES_PATH, deliverables_text), (PRESETS_PATH, presets_text)],
        validate, "repair")
    if result["ok"]:
        result["repaired"] = missing
        result["note"] = f"added deliverable + preset entries for {missing}"
    return result


def register_lesson(key: str, filename: str, summary: str) -> dict:
    """The documented registration contract, atomically: add the lesson to
    ``lesson_registry.py``, ``deliverables.py`` and ``render_presets.py`` with
    backups + the repo's own validators; roll back on any failure."""
    if not re.fullmatch(r"[a-z][a-z0-9_]{1,31}", key):
        return {"ok": False, "changed": False,
                "error": f"lesson key must match [a-z][a-z0-9_]: {key!r}"}
    ready = preflight()
    if not ready["ok"]:
        broken = [c["name"] for c in ready["checks"] if not c["ok"]]
        return {"ok": False, "changed": False,
                "error": f"preflight failed: {', '.join(broken)}"}

    key_upper = key.upper()
    summary = _quote_safe(summary)
    registry_text = REGISTRY_PATH.read_text(encoding="utf-8")
    deliverables_text = DELIVERABLES_PATH.read_text(encoding="utf-8")
    presets_text = PRESETS_PATH.read_text(encoding="utf-8")

    already = (f"from .lesson_{key} import {key_upper}_LESSON" in registry_text
               and re.search(rf"(?<![A-Z0-9_]){key_upper}_LESSON(?![A-Z0-9_])",
                             registry_text[slice(*(_registry_tuple_span(registry_text)
                                                   or (0, 0)))])
               and f'Deliverable("{key}"' in deliverables_text
               and f'_video("{key}"' in presets_text)
    if already:
        return {"ok": True, "changed": False, "note": "already registered"}

    try:
        new_registry = _insert_import(registry_text, key, key_upper)
        new_registry = _insert_registry_entry(new_registry, key_upper)
        new_deliverables = _insert_deliverable(
            deliverables_text, key, filename, summary)
        new_presets = _insert_preset(presets_text, key, filename, summary)
    except ValueError as exc:
        # Nothing has been written yet: the edits are computed first on
        # purpose, so a bad anchor cannot leave one file changed and two not.
        return {"ok": False, "changed": False, "error": str(exc)}

    result = _apply_registration(
        [(REGISTRY_PATH, new_registry),
         (DELIVERABLES_PATH, new_deliverables),
         (PRESETS_PATH, new_presets)],
        lambda: validate_registration(key), "registration")
    if result["ok"]:
        result["note"] = ("registered in lesson_registry.py, deliverables.py "
                          "and render_presets.py (the repo's validators pass)")
    return result
