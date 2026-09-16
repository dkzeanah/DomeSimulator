"""The tool layer: typed, schema-described wrappers over the repo's real
programmatic APIs.

Design rules:

* Every tool is a plain function plus a JSON schema (function-calling
  shape) plus a human description.  The LLM's only freedom is *which
  tools to call in which order*.
* Writes are allowlisted to authoring paths; engine source is never
  written by the agent.
* Spawned tool processes redirect their output to a log file (no pipes),
  so runs work in constrained environments and the log is always in the
  run manifest.
* Every tool returns a JSON-able dict ``{ok, ...}`` — observable,
  recordable, auditable.
"""

from __future__ import annotations

import contextlib
import dataclasses
import importlib
import io
import json
import os
import re
import subprocess
import sys
import time
from pathlib import Path
from typing import Any

from . import config, ledger
from .facts import FACT_SPECS

# ---------------------------------------------------------------------------
# Small shared helpers
# ---------------------------------------------------------------------------


def _with_properties(obj: Any, data: dict) -> dict:
    """Merge @property values (computed figures) into a field dict."""
    for name in dir(type(obj)):
        if isinstance(getattr(type(obj), name, None), property):
            try:
                data[name] = _to_jsonable(getattr(obj, name))
            except Exception:  # noqa: BLE001
                pass
    return data


def _to_jsonable(obj: Any) -> Any:
    if obj is None or isinstance(obj, (str, int, float, bool)):
        return obj
    if dataclasses.is_dataclass(obj):
        return _with_properties(obj, {k: _to_jsonable(v)
                                      for k, v in dataclasses.asdict(obj).items()})
    if isinstance(obj, dict):
        return {str(k): _to_jsonable(v) for k, v in obj.items()}
    if isinstance(obj, (list, tuple, set)):
        return [_to_jsonable(v) for v in obj]
    if hasattr(obj, "__dict__"):
        # A plain result object (e.g. a report class): its fields, plus any
        # @property computed values that evaluate cleanly.
        data = {k: _to_jsonable(v) for k, v in vars(obj).items()}
        return _with_properties(obj, data)
    return str(obj)


def _spawn(script: str, tool: str, cfg: dict,
           timeout: int = config.TIMEOUT_STILLS, label: str = "") -> dict:
    """Write a launch ticket and spawn the repo tool; stdout/stderr go to a log
    file inside the run directory (never a pipe).

    The ticket is written under a lock.  A tool is configured by writing
    ``.launcher_configs/<tool>.json`` and then spawning it, and the tool
    consumes and deletes that file at startup — so two of these in flight for
    the same tool (an agent run during a render, or two agent runs) race, and
    the loser's job silently runs with the winner's configuration.

    A timeout is reported, never raised: the caller needs a result dict and a
    log path, not a traceback from inside a helper.
    """
    import launcher_common  # repo root on sys.path

    run_dir = config.RUNS_DIR / "_last"
    run_dir.mkdir(parents=True, exist_ok=True)
    stamp = time.strftime("%H%M%S")
    log_path = run_dir / f"spawn_{label or tool}_{stamp}.log"
    started = time.monotonic()
    timed_out = False
    returncode = -1
    try:
        with config.ticket_lock(tool):
            launcher_common.write_config(tool, cfg)
            try:
                with log_path.open("w", encoding="utf-8") as logf:
                    proc = subprocess.run(
                        [config.agent_python(), str(script)],
                        cwd=str(config.REPO_ROOT),
                        env={**os.environ, "PYTHONUNBUFFERED": "1"},
                        stdout=logf, stderr=subprocess.STDOUT,
                        timeout=timeout,
                    )
                returncode = proc.returncode
            except subprocess.TimeoutExpired:
                timed_out = True
    except config.TicketBusy as exc:
        return {"ok": False, "returncode": -1, "elapsed_s": 0.0,
                "log": str(log_path), "tail": str(exc), "error": str(exc),
                "busy": True}
    except OSError as exc:
        return {"ok": False, "returncode": -1, "elapsed_s": 0.0,
                "log": str(log_path), "tail": f"could not start {script}: {exc}",
                "error": f"{type(exc).__name__}: {exc}"}

    elapsed = time.monotonic() - started
    tail = ""
    if log_path.is_file():
        tail = "\n".join(
            log_path.read_text(encoding="utf-8", errors="replace")
            .splitlines()[-30:])
    result = {
        "ok": (not timed_out) and returncode == 0,
        "returncode": returncode,
        "elapsed_s": round(elapsed, 1),
        "log": str(log_path),
        "tail": tail,
    }
    if timed_out:
        result["timeout"] = True
        result["error"] = (f"{script} did not finish within {timeout}s; the "
                           f"log is at {log_path}")
    return result


def _run_dir(tag: str) -> Path:
    directory = config.RUNS_DIR / tag
    directory.mkdir(parents=True, exist_ok=True)
    return directory


# ---------------------------------------------------------------------------
# Tools
# ---------------------------------------------------------------------------


def _t_sync_knowledge(args: dict) -> dict:
    from . import spec
    data = spec.sync_knowledge(write=True)
    return {"ok": True, "summary": spec.kb_summary(data), "path": str(config.KB_PATH)}


def _t_list_items(args: dict) -> dict:
    kind = str(args.get("kind", "facts"))
    from . import spec
    kb = spec.load_kb()
    section = kb["sections"]
    if kind == "facts":
        rows = {fid: f["description"] for fid, f in section["facts"]["data"].items()}
        text = "\n".join(f"  {k}: {v}" for k, v in rows.items())
        return {"ok": True, "text": text or "no facts registered"}
    if kind == "lessons":
        data = section["lessons"]["data"]
        text = "\n".join(
            f"  {k:<13} {v['chapters']:>3} chapters  {v['style']:<9} "
            f"prefix={v['snapshot_prefix']}  {v['title']}"
            for k, v in sorted(data.items()) if not k.startswith("_"))
        return {"ok": True, "text": text}
    if kind == "presets":
        data = section["presets"]["data"]
        text = "\n".join(f"  {k:<16} {v['label']}" for k, v in sorted(data.items()))
        return {"ok": True, "text": text}
    if kind == "deliverables":
        data = section["deliverables"]["data"]
        text = "\n".join(
            f"  {'built' if (v.get('built') if isinstance(v, dict) else False) else '     '} "
            f" {k}" for k, v in sorted(data.items()) if not k.startswith("_"))
        return {"ok": True, "text": text}
    if kind == "tokens":
        data = section["book_tokens"]["data"]
        text = "\n".join(f"  {k} = {v['value']}  ({v['describe']})"
                         for k, v in sorted(data.items()))
        return {"ok": True, "text": text[:4000]}
    if kind == "targets":
        return {"ok": True, "text": ", ".join(section["focus_targets"]["data"]["names"])}
    if kind == "ledger":
        return {"ok": True, "text": ledger.ledger_text()}
    return {"ok": False, "error": f"unknown list kind {kind!r} "
            "(facts|lessons|presets|deliverables|tokens|targets|ledger)"}


def _t_query_facts(args: dict) -> dict:
    fact_id = str(args.get("id", ""))
    spec = FACT_SPECS.get(fact_id)
    if spec is None:
        return {"ok": False, "error": f"unknown fact id {fact_id!r}; "
                f"choose from {', '.join(sorted(FACT_SPECS))}"}
    params = args.get("params") or {}
    if not isinstance(params, dict):
        return {"ok": False, "error": "params must be an object"}
    unknown = set(params) - set(spec.params)
    if unknown:
        return {"ok": False, "error": f"params not allowed for {fact_id}: "
                f"{sorted(unknown)}; allowed: {sorted(spec.params)}"}
    converted = {}
    for key, value in params.items():
        try:
            converted[key] = spec.params[key](value)
        except (TypeError, ValueError) as exc:
            return {"ok": False, "error": f"bad value for {key}: {exc}"}
    if getattr(spec, "kind", "call") == "value" and converted:
        return {"ok": False, "error": f"{fact_id} is a table, not a function; "
                                      "it takes no parameters"}
    try:
        module = importlib.import_module(spec.module)
        attribute = getattr(module, spec.func)
        if getattr(spec, "kind", "call") == "value":
            result = attribute
        else:
            if not callable(attribute):
                return {"ok": False, "fact": fact_id,
                        "error": f"{spec.module}.{spec.func} is not callable; "
                                 "the facts entry should declare kind='value'"}
            result = attribute(**converted)
    except Exception as exc:  # noqa: BLE001
        return {"ok": False, "error": f"{type(exc).__name__}: {exc}",
                "fact": fact_id}
    return {
        "ok": True,
        "fact": fact_id,
        "module": spec.module,
        "result": _to_jsonable(result),
        "note": spec.note,
    }


def _t_selftest(args: dict) -> dict:
    target = str(args.get("tool", "masterclass"))
    lesson_key = str(args.get("lesson", "") or "2v")
    if target == "book":
        try:
            from two_v_demo.book import validate_everything
            validate_everything()
            return {"ok": True, "tool": target,
                    "message": "validate_everything() passed (math, outline, "
                               "tokens, figures, manuscript, export)"}
        except Exception as exc:  # noqa: BLE001
            return {"ok": False, "tool": target,
                    "error": f"{type(exc).__name__}: {exc}"}
    table = {
        "masterclass": ("two_v_masterclass.py", "two_v_masterclass",
                        {"action": "selftest", "lesson": lesson_key}),
        "presenter": ("presenter_studio.py", "presenter", {"action": "selftest"}),
        "dome_forge": ("dome_forge.py", "dome_forge", {"action": "selftest"}),
    }
    if target not in table:
        return {"ok": False, "error": f"unknown selftest target {target!r}"}
    script, tool, cfg = table[target]
    result = _spawn(script, tool, cfg, timeout=600, label=f"selftest_{target}")
    result["tool"] = target
    return result


def _t_render_stills(args: dict) -> dict:
    backend = str(args.get("backend", "masterclass"))
    times = [str(t) for t in args.get("times", [])]
    if not times:
        return {"ok": False, "error": "times is required (list of seconds)"}
    size = str(args.get("size", "1600x900"))
    run_tag = f"stills_{backend}_{time.strftime('%H%M%S')}"
    shot_dir = _run_dir(run_tag) / "stills"
    shot_dir.mkdir(parents=True, exist_ok=True)

    if backend == "masterclass":
        lesson_key = str(args.get("lesson", "2v"))
        try:
            # Import the lesson module directly (never the cached registry).
            import importlib
            module = importlib.import_module(f"two_v_demo.lesson_{lesson_key}")
            prefix = getattr(
                module, f"{lesson_key.upper()}_LESSON").snapshot_prefix
        except Exception as exc:  # noqa: BLE001
            return {"ok": False, "error": f"cannot resolve lesson {lesson_key!r}: {exc}"}
        cfg = {"action": "shots", "lesson": lesson_key,
               "shots": ",".join(times), "no_narration": True, "size": size}
        result = _spawn("two_v_masterclass.py", "two_v_masterclass", cfg,
                        timeout=1200, label=run_tag)
        expected = [config.REPO_ROOT / "two_v_demo_output" / lesson_key /
                    f"{prefix}_{float(t):07.2f}s.png" for t in times]
    elif backend == "presenter":
        demo = args.get("demo") or args.get("script")
        if not demo:
            return {"ok": False, "error": "demo (or script path) is required"}
        cfg = {"action": "shots", "shots": ",".join(times), "size": size}
        if str(demo).endswith((".json", ".py")):
            # A script path goes straight through; demo-name forgiveness
            # only applies to built-in demo keys.
            cfg["script"] = str(demo)
        else:
            from presenter_studio import DEMOS
            key = str(demo)
            if key not in DEMOS:
                candidates = [key, key.removeprefix("dome_"), f"dome_{key}"]
                key = next((c for c in candidates if c in DEMOS), "")
                module_file = (config.REPO_ROOT / "presentations" /
                               f"{str(demo)}.py")
                if not key and module_file.is_file():
                    key = ""
                    cfg["script"] = str(module_file.relative_to(config.REPO_ROOT))
                elif not key:
                    return {"ok": False,
                            "error": f"unknown presenter demo {demo!r}; "
                                     f"choose from {', '.join(sorted(DEMOS))}"}
                else:
                    demo = key
            if "script" not in cfg:
                cfg["demo"] = str(demo)
        result = _spawn("presenter_studio.py", "presenter", cfg,
                        timeout=1200, label=run_tag)
        expected = [config.REPO_ROOT / "deliverables" / "presenter" /
                    f"shot_{float(t):07.1f}s.png" for t in times]
    elif backend == "dome_forge":
        # In-process capture: the repo's own shots CLI replaces the app's
        # stack after construction without re-initialising the selection
        # attributes its UI expects, so we build the app the supported
        # way and then fly the camera ourselves (same views as cli._shots).
        from dome_forge.app import DomeForgeApp
        from dome_forge.layers import LayerStack, default_stack
        width, height = (1600, 900)
        try:
            width, height = (int(v) for v in size.lower().split("x", 1))
        except ValueError:
            pass
        app = DomeForgeApp(size=(width, height), hidden=True)
        stack = default_stack()
        stack.selected_faces = set()
        stack.explode = 0.0
        app.stack = stack
        views = [
            ("exterior", 38.0, 22.0, 15.0, False, 0.0),
            ("cutaway", 200.0, 10.0, 7.0, True, 1.3),
            ("top", 90.0, 78.0, 16.0, False, 2.1),
            ("ground", 300.0, -4.0, 12.0, False, 3.4),
        ]
        written = []
        try:
            for name, yaw, pitch, distance, cut, when in views:
                app.yaw, app.pitch, app.distance = yaw, pitch, distance
                app.stack.settings.cut_enabled = cut
                app.clock_t = when
                written.append(app.capture(shot_dir / f"{name}.png"))
        finally:
            app.pygame.quit()
        expected = [shot_dir / name for name in
                    ("exterior.png", "cutaway.png", "top.png", "ground.png")]
        result = {"ok": all(p.is_file() for p in expected), "returncode": 0,
                  "log": "", "tail": "", "elapsed_s": 0.0}
        paths = [str(p) for p in written if p.is_file()]
        missing = [str(p) for p in expected if not p.is_file()]
        return {"ok": bool(paths) and not missing, "backend": backend,
                "paths": paths, "missing": missing, "log": "",
                "tail": "", "elapsed_s": 0.0}
    elif backend == "assembly_line":
        cfg = {"action": "shots", "shots": ",".join(times),
               "shot_speed": float(args.get("shot_speed", 6)),
               "shot_dir": str(shot_dir),
               "seed": int(args.get("seed", 42))}
        result = _spawn("assembly_line.py", "assembly_line", cfg,
                        timeout=900, label=run_tag)
        expected = [shot_dir / f"shot_{float(t):07.1f}s.png" for t in times]
    else:
        return {"ok": False, "error": f"unknown backend {backend!r} "
                "(masterclass|presenter|dome_forge|assembly_line)"}

    paths = [p for p in expected if p.is_file()]
    missing = [str(p) for p in expected if not p.is_file()]
    return {
        "ok": bool(result["ok"]) and not missing,
        "backend": backend,
        "paths": [str(p) for p in paths],
        "missing": missing,
        "log": result["log"],
        "tail": result["tail"],
        "elapsed_s": result["elapsed_s"],
    }


def _t_export_video(args: dict) -> dict:
    out = str(args.get("out", ""))
    if not out:
        return {"ok": False, "error": "out (output mp4 path) is required"}
    fps = int(args.get("fps", 30))
    size = str(args.get("size", "1920x1080"))
    if args.get("demo") or args.get("script"):
        demo = args.get("demo") or args.get("script")
        cfg = {"action": "export", "export": out, "fps": fps, "size": size,
               "no_narration": bool(args.get("no_narration", False)),
               "overlay": str(args.get("overlay", "full"))}
        if str(demo).endswith((".json", ".py")):
            cfg["script"] = demo
        else:
            cfg["demo"] = demo
        result = _spawn("presenter_studio.py", "presenter", cfg,
                        timeout=3600, label="export")
    else:
        lesson_key = str(args.get("lesson", "2v"))
        cfg = {"action": "export_video", "lesson": lesson_key,
               "export_video": out, "fps": fps, "size": size,
               "no_narration": bool(args.get("no_narration", False)),
               "compose_segments": bool(args.get("compose_segments", False))}
        # Voice settings travel only when asked for. Sent blindly, they
        # override the lesson's own declared pacing, and chapter durations are
        # measured off the speech — so a stray rate moves every boundary in
        # the film and the result no longer matches the published cut.
        if args.get("voice"):
            cfg["voice"] = str(args["voice"])
        if args.get("voice_rate"):
            cfg["voice_rate"] = str(args["voice_rate"])
        orientation = str(args.get("orientation") or "").lower()
        if orientation in ("landscape", "portrait", "both"):
            cfg["orientation"] = orientation
        result = _spawn("two_v_masterclass.py", "two_v_masterclass", cfg,
                        timeout=config.TIMEOUT_EXPORT, label="export")
    out_path = config.REPO_ROOT / out
    companions = [str(p) for p in (
        out_path.with_suffix(".srt"),
        Path(str(out_path) + "-narration.m4a"),
        Path(str(out_path) + "-narration.md")) if p.is_file()]
    return {
        "ok": result["ok"] and out_path.is_file(),
        "video": str(out_path),
        "companions": companions,
        "log": result["log"], "tail": result["tail"],
        "elapsed_s": result["elapsed_s"],
    }


def _t_export_book(args: dict) -> dict:
    action = str(args.get("action", "audit"))
    allowed = {"read_html", "read_pdf", "export", "render_figures", "audit",
               "progress", "outline"}
    if action not in allowed:
        return {"ok": False, "error": f"action must be one of {sorted(allowed)}"}
    strict = bool(args.get("strict", True))
    try:
        from two_v_demo.book_app import run_headless
        code = run_headless(action, Path("book/manuscript"),
                            Path("deliverables/book"), strict=strict)
        return {"ok": code == 0, "action": action, "returncode": code,
                "out_dir": "deliverables/book"}
    except Exception as exc:  # noqa: BLE001
        return {"ok": False, "error": f"{type(exc).__name__}: {exc}"}


def _t_verify_render(args: dict) -> dict:
    path = Path(str(args.get("path", "")))
    if not str(path) or not path.is_file():
        return {"ok": False, "error": f"no such file: {path}"}
    try:
        from verify_renders import check
        buffer = io.StringIO()
        with contextlib.redirect_stdout(buffer):
            ok = check(path)
        return {"ok": ok, "path": str(path), "report": buffer.getvalue()}
    except Exception as exc:  # noqa: BLE001
        return {"ok": False, "error": f"{type(exc).__name__}: {exc}"}


_WRITE_ALLOWLIST = (
    ("project_agent", None),
    ("exports", None),
    ("presentations", None),
    ("book", "manuscript"),
)


def _t_write_file(args: dict) -> dict:
    raw = str(args.get("path", "")).strip()
    if not raw:
        return {"ok": False, "error": "path is required"}
    if "content" not in args:
        return {"ok": False, "error": "content is required (may be empty)"}
    content = str(args.get("content") or "")
    try:
        resolved = config.repo_path(raw)
    except config.PathOutsideRepo as exc:
        return {"ok": False, "error": f"write denied: {exc}"}
    rel = Path(config.relative_to_repo(resolved))
    parts = rel.parts
    allowed = False
    for prefix, sub in _WRITE_ALLOWLIST:
        if parts[:1] == (prefix,) and (sub is None or parts[1:2] == (sub,)):
            allowed = True
            break
    if not allowed and parts[:1] == ("two_v_demo",):
        name = parts[-1]
        if name.startswith("lesson_") or name.endswith("_facts.py"):
            allowed = True
    if not allowed:
        return {"ok": False,
                "error": f"write denied for {rel}: allowlist is project_agent/, "
                         "exports/, presentations/, book/manuscript/, and "
                         "two_v_demo/lesson_*.py or two_v_demo/*_facts.py"}
    resolved.parent.mkdir(parents=True, exist_ok=True)
    resolved.write_text(content, encoding="utf-8")
    return {"ok": True, "written": str(resolved), "chars": len(content)}


def _t_read_file(args: dict) -> dict:
    raw = str(args.get("path", "")).strip()
    if not raw:
        return {"ok": False, "error": "path is required"}
    try:
        # Confined to the repository: an absolute path used to escape it
        # entirely, because REPO_ROOT / "/anywhere/else" is "/anywhere/else".
        resolved = config.repo_path(raw)
    except config.PathOutsideRepo as exc:
        return {"ok": False, "error": f"read denied: {exc}"}
    if not resolved.is_file():
        return {"ok": False, "error": f"no such file: {raw}"}
    text = resolved.read_text(encoding="utf-8", errors="replace")
    try:
        limit = max(1, int(args.get("limit", 6000)))
    except (TypeError, ValueError):
        limit = 6000
    return {"ok": True, "path": config.relative_to_repo(resolved),
            "content": text[:limit],
            "truncated": len(text) > limit, "chars": len(text)}


def _t_declare_constant(args: dict) -> dict:
    name = str(args.get("name", "")).strip()
    value = str(args.get("value", "")).strip()
    unit = str(args.get("unit", "")).strip()
    source = str(args.get("source", "")).strip()
    kind = str(args.get("kind", "declared"))
    if not name or not value:
        return {"ok": False, "error": "name and value are required"}
    if kind not in ("declared", "estimated"):
        return {"ok": False, "error": "kind must be declared or estimated"}
    item = ledger.add_item(
        question=f"constant {name}",
        kind=kind, proposal=f"use {value} {unit}".strip(),
        source=source, note="declared by user/agent")
    item = ledger.resolve(item.id, f"{value} {unit}".strip(), source=source)
    return {"ok": True, "item": item.to_dict()}


def _t_resolve(args: dict) -> dict:
    item_id = str(args.get("id", "")).strip()
    answer = str(args.get("answer", "")).strip()
    source = str(args.get("source", "")).strip()
    if not item_id or not answer:
        return {"ok": False, "error": "id and answer are required"}
    item = ledger.resolve(item_id, answer, source=source)
    if item is None:
        return {"ok": False, "error": f"no ledger item {item_id!r}"}
    return {"ok": True, "item": item.to_dict()}


def _t_drop_claim(args: dict) -> dict:
    item_id = str(args.get("id", "")).strip()
    item = ledger.drop(item_id, note=str(args.get("note", "dropped: cannot be sourced")))
    if item is None:
        return {"ok": False, "error": f"no ledger item {item_id!r}"}
    return {"ok": True, "item": item.to_dict()}


def _t_scan_claims(args: dict) -> dict:
    text = str(args.get("text", ""))
    path = args.get("path")
    if not text and path:
        resolved = (config.REPO_ROOT / str(path)).resolve()
        if not resolved.is_file():
            return {"ok": False, "error": f"no such file: {path}"}
        text = resolved.read_text(encoding="utf-8", errors="replace")
    if not text:
        return {"ok": False, "error": "text or path is required"}
    items = ledger.scan_claims(text)
    return {"ok": True, "filed": len(items),
            "items": [i.to_dict() for i in items],
            "hint": "resolve each with resolve(id=..., answer=..., source=...), "
                    "or declare_constant(name=..., value=..., unit=..., source=...)"}


def _t_constants_module(args: dict) -> dict:
    out = Path(str(args.get("out", f"project_agent/runs/_last/resolved_constants.py")))
    resolved = (config.REPO_ROOT / out).resolve()
    try:
        written = ledger.constants_module(resolved)
        return {"ok": True, "written": str(written)}
    except ValueError as exc:
        return {"ok": False, "error": str(exc)}


def _t_view(args: dict) -> dict:
    path = Path(str(args.get("path", config.RUNS_DIR)))
    resolved = path if path.is_absolute() else config.REPO_ROOT / path
    if not resolved.exists():
        return {"ok": False, "error": f"no such path: {resolved}"}
    if os.name == "nt":
        os.startfile(str(resolved))  # noqa: S606
        opened = str(resolved)
    else:
        opened = ""
    return {"ok": True, "opened": opened, "path": str(resolved),
            "note": "opened in the OS file browser (Windows)" if opened
            else "open the path manually"}


def _t_run_recipe(args: dict) -> dict:
    from . import recipes
    recipe = str(args.get("recipe", ""))
    params = args.get("params") or {}
    if not isinstance(params, dict):
        return {"ok": False, "error": "params must be an object"}
    return recipes.run_recipe(recipe, params)


def _t_help(args: dict) -> dict:  # noqa: ARG001
    from . import recipes
    lines = []
    for name, entry in TOOLS.items():
        description = str(entry.get("description", "")).strip()
        first = description.splitlines()[0] if description else ""
        lines.append(f"  {name:<18} {first}")
    text = "\n".join(lines)
    text += "\n\nrecipes (run with run_recipe):\n" + recipes.recipes_text()
    return {"ok": True, "text": text}


# ---------------------------------------------------------------------------
# Registry + JSON schemas (OpenAI function-calling shape)
# ---------------------------------------------------------------------------


def _schema(name: str, description: str, properties: dict,
            required: list[str]) -> dict:
    return {
        "type": "function",
        "function": {
            "name": name,
            "description": description,
            "parameters": {
                "type": "object",
                "properties": properties,
                "required": required,
            },
        },
    }


def _prop(prop_type: str, description: str, enum: list[str] | None = None,
          items: dict | None = None) -> dict:
    schema: dict = {"type": prop_type, "description": description}
    if enum:
        schema["enum"] = enum
    if items:
        schema["items"] = items
    return schema


TOOLS: dict[str, dict] = {
    "sync_knowledge": {
        "call": _t_sync_knowledge,
        "description": ("Rebuild the project knowledge base from the repo's own "
                        "menu/dump functions and return a compact summary."),
        "schema": _schema("sync_knowledge",
                          "Rebuild the project knowledge base from the repo.",
                          {}, []),
    },
    "list_items": {
        "call": _t_list_items,
        "description": ("List a part of the knowledge base: facts (derive-and-"
                        "simulate index), lessons, presets, deliverables, book "
                        "tokens, focus targets, or the resolution ledger."),
        "schema": _schema("list_items",
                          "List one kind of project knowledge.",
                          {"kind": _prop("string", "Which catalogue.",
                                         enum=["facts", "lessons", "presets",
                                               "deliverables", "tokens",
                                               "targets", "ledger"])},
                          ["kind"]),
    },
    "query_facts": {
        "call": _t_query_facts,
        "description": ("Compute a figure by calling a real, validated facts "
                        "module (geometry, trees/wedges, costing, the book's "
                        "arithmetic, pine value, factory economics). List with "
                        "list_items(kind='facts')."),
        "schema": _schema("query_facts",
                          "Derive a number from a validated facts module.",
                          {"id": _prop("string", "Facts entry id, e.g. "
                                       "'wedge.tree_yield' or 'pine.model'."),
                           "params": _prop("object", "Optional keyword "
                                           "arguments the entry allows.")},
                          ["id"]),
    },
    "selftest": {
        "call": _t_selftest,
        "description": ("Run a tool's proof suite: masterclass lessons "
                        "(validates the lesson's facts), presenter, dome forge, "
                        "or the whole book stack."),
        "schema": _schema("selftest",
                          "Run a proof suite before anything reaches a frame.",
                          {"tool": _prop("string", "Which suite.",
                                         enum=["masterclass", "presenter",
                                               "dome_forge", "book"]),
                           "lesson": _prop("string", "Lesson key for the "
                                           "masterclass suite, e.g. '2v'.")},
                          ["tool"]),
    },
    "render_stills": {
        "call": _t_render_stills,
        "description": ("Render one or more still PNGs headlessly from a world "
                        "(masterclass lesson timeline, presenter demo, dome "
                        "forge named views, assembly line timeline) and return "
                        "the file paths for review."),
        "schema": _schema("render_stills",
                          "Render still images from a world for visual review.",
                          {"backend": _prop("string", "Which world.",
                                            enum=["masterclass", "presenter",
                                                  "dome_forge", "assembly_line"]),
                           "times": _prop("array", "Seconds on the timeline, "
                                          "e.g. ['45','90'].",
                                          items={"type": "string"}),
                           "lesson": _prop("string", "Lesson key (masterclass)."),
                           "demo": _prop("string", "Built-in demo name "
                                         "(presenter), e.g. 'dome_accessibility'."),
                           "size": _prop("string", "Size WxH, default 1600x900."),
                           "shot_speed": _prop("number", "Assembly line sim "
                                               "speed, default 6."),
                           "seed": _prop("number", "Assembly line run seed, "
                                         "default 42.")},
                          ["backend", "times"]),
    },
    "export_video": {
        "call": _t_export_video,
        "description": ("Export a narrated MP4 (masterclass lesson or presenter "
                        "demo) with its .srt, narration track, and script. "
                        "Output is append-only; verify afterwards with "
                        "verify_render."),
        "schema": _schema("export_video",
                          "Export a narrated MP4 plus companions.",
                          {"out": _prop("string", "Output path, e.g. "
                                        "exports/my-film.mp4."),
                           "lesson": _prop("string", "Lesson key (masterclass)."),
                           "demo": _prop("string", "Demo name (presenter)."),
                           "fps": _prop("number", "Frames per second, default 30."),
                           "size": _prop("string", "Size WxH."),
                           "no_narration": _prop("boolean", "Silent export."),
                           "voice": _prop("string", "edge-tts voice."),
                           "voice_rate": _prop("string", "e.g. '-3%'."),
                           "overlay": _prop("string", "Presenter overlay level.",
                                            enum=["full", "no_captions",
                                                  "titles_only", "clean"]),
                           "compose_segments": _prop("boolean", "Splice branded "
                                                     "segments (lessons)."),
                           "orientation": _prop("string", "Which shapes to "
                                                "render: landscape, portrait, "
                                                "or both (the phone cut reuses "
                                                "the same narration).",
                                                enum=["landscape", "portrait",
                                                      "both"])},
                          ["out"]),
    },
    "export_book": {
        "call": _t_export_book,
        "description": ("Run a Book Studio action headlessly: read_html, "
                        "read_pdf, export markdown, render_figures, audit, "
                        "progress, or outline."),
        "schema": _schema("export_book",
                          "Produce a readable book form.",
                          {"action": _prop("string", "Which book action.",
                                           enum=["read_html", "read_pdf",
                                                 "export", "render_figures",
                                                 "audit", "progress",
                                                 "outline"]),
                           "strict": _prop("boolean", "Refuse on misspelt "
                                           "tokens (default true).")},
                          ["action"]),
    },
    "verify_render": {
        "call": _t_verify_render,
        "description": ("Check a rendered MP4 is whole by frame count and "
                        "audio/video drift, not merely plausible."),
        "schema": _schema("verify_render",
                          "Verify a render by frame count.",
                          {"path": _prop("string", "Path to the MP4.")},
                          ["path"]),
    },
    "read_file": {
        "call": _t_read_file,
        "description": "Read a repository file (anywhere under the repo).",
        "schema": _schema("read_file", "Read a repo file.",
                          {"path": _prop("string", "Path relative to the repo "
                                         "root.")}, ["path"]),
    },
    "write_file": {
        "call": _t_write_file,
        "description": ("Write an authoring file. Allowlist: project_agent/, "
                        "exports/, presentations/, book/manuscript/, "
                        "two_v_demo/lesson_*.py, two_v_demo/*_facts.py."),
        "schema": _schema("write_file", "Write an authoring file.",
                          {"path": _prop("string", "Relative path."),
                           "content": _prop("string", "Full file content.")},
                          ["path", "content"]),
    },
    "declare_constant": {
        "call": _t_declare_constant,
        "description": ("Record a borrowed figure as a named constant with "
                        "unit and source in the resolution ledger (the repo's "
                        "EXTERNAL_CONSTANTS pattern)."),
        "schema": _schema("declare_constant",
                          "Declare an external constant with provenance.",
                          {"name": _prop("string", "Constant name."),
                           "value": _prop("string", "Value."),
                           "unit": _prop("string", "Unit."),
                           "source": _prop("string", "Where it comes from."),
                           "kind": _prop("string", "declared or estimated.",
                                         enum=["declared", "estimated"])},
                          ["name", "value"]),
    },
    "resolve": {
        "call": _t_resolve,
        "description": ("Close a ledger gap: answer one pending item with a "
                        "value and an optional source."),
        "schema": _schema("resolve",
                          "Resolve a pending ledger item.",
                          {"id": _prop("string", "Ledger item id, e.g. led-0003."),
                           "answer": _prop("string", "The resolved value."),
                           "source": _prop("string", "Optional source.")},
                          ["id", "answer"]),
    },
    "drop_claim": {
        "call": _t_drop_claim,
        "description": "Mark an unsourceable ledger item as dropped, with a note.",
        "schema": _schema("drop_claim", "Drop an unsourceable claim.",
                          {"id": _prop("string", "Ledger item id."),
                           "note": _prop("string", "Why it was dropped.")},
                          ["id"]),
    },
    "scan_claims": {
        "call": _t_scan_claims,
        "description": ("Scan pasted text for numeric claims and file each one "
                        "into the resolution ledger classified as computed / "
                        "declared / estimated / review — the gap-finding pass."),
        "schema": _schema("scan_claims",
                          "Find and classify numeric claims in text.",
                          {"text": _prop("string", "The text to scan."),
                           "path": _prop("string", "Or a file path to scan.")},
                          []),
    },
    "constants_module": {
        "call": _t_constants_module,
        "description": ("Emit a paste-ready Python constants module from all "
                        "resolved declared ledger items."),
        "schema": _schema("constants_module",
                          "Generate a constants module from the ledger.",
                          {"out": _prop("string", "Output path, e.g. "
                                        "exports/resolved_constants.py.")},
                          []),
    },
    "view": {
        "call": _t_view,
        "description": ("Open a folder in the OS file browser so rendered "
                        "stills can be looked at (the look-at-every-still "
                        "gate)."),
        "schema": _schema("view", "Open a folder for visual review.",
                          {"path": _prop("string", "Folder path.")}, []),
    },
    "run_recipe": {
        "call": _t_run_recipe,
        "description": ("Execute a production recipe end-to-end with gates: "
                        "claims (text -> classified claims + ledger), stills "
                        "(render + review), book (selftest -> figures -> "
                        "HTML/PDF), presenter (stage/validate a Presentation "
                        "-> stills -> export), film (teaching film: claims -> "
                        "scaffold -> constants -> narration -> register -> "
                        "selftest -> stills -> export -> verify)."),
        "schema": _schema("run_recipe",
                          "Run a gated media-production recipe.",
                          {"recipe": _prop("string", "Which recipe.",
                                           enum=["claims", "stills", "book",
                                                 "presenter", "film"]),
                           "params": _prop("object", "Recipe parameters "
                                           "(key, title, source, times, "
                                           "demo, prompt, export, size, fps, "
                                           "declare, figures, pdf, "
                                           "no_narration, ...).")},
                          ["recipe"]),
    },
    "help": {
        "call": _t_help,
        "description": "List every tool and recipe and what it does.",
        "schema": _schema("help", "List tools.", {}, []),
    },
}


def dispatch(name: str, args: dict) -> dict:
    """Execute one tool call. Returns the tool's result dict."""
    spec = TOOLS.get(name)
    if spec is None:
        return {"ok": False, "error": f"unknown tool {name!r}"}
    try:
        return spec["call"](args or {})
    except Exception as exc:  # noqa: BLE001
        return {"ok": False, "error": f"{type(exc).__name__}: {exc}"}


def tool_schemas() -> list[dict]:
    return [spec["schema"] for spec in TOOLS.values()]
