"""Recipes: ordered, gated plans that produce media.

A recipe is the specialization: the exact sequence of tool calls and
template fills the repo's own docs prescribe, with gates that stop the
run when a proof fails.  Every run writes a manifest; long runs are
resumable because each stage skips work whose output already exists.

Recipe catalogue:

* ``claims``  — text in, classified claims + resolution ledger out.
* ``stills``  — render + open stills from any world (the review gate).
* ``book``    — audit → figures (optional) → readable HTML/PDF.
* ``presenter`` — validate/stage a Presentation, stills, optional export.
* ``film``    — the teaching-film loop: claims → scaffold → constants →
                narration → register → selftest → stills → export → verify.
"""

from __future__ import annotations

import json
import re
import time
import traceback
from dataclasses import dataclass, field
from pathlib import Path

from . import config, ledger, templates, tools
from .config import ensure_dirs

_SENTENCE = re.compile(r"(?<=[.!?])\s+")


class RecipeAbort(Exception):
    """A gate failed: stop the recipe with a clear reason."""

    def __init__(self, label: str, reason: str) -> None:
        super().__init__(f"{label}: {reason}")
        self.label = label
        self.reason = reason


@dataclass
class RecipeContext:
    run_id: str
    params: dict
    steps: list[dict] = field(default_factory=list)
    outputs: list[str] = field(default_factory=list)

    @property
    def run_dir(self) -> Path:
        directory = config.RUNS_DIR / self.run_id
        directory.mkdir(parents=True, exist_ok=True)
        return directory

    def step(self, label: str, tool: str, args: dict,
             gate=None, required: bool = True) -> dict:
        print(f"\n[{len(self.steps) + 1}] {label}")
        result = tools.dispatch(tool, args)
        record = {"label": label, "tool": tool, "args": args,
                  "ok": result.get("ok"), "result": result}
        self.steps.append(record)
        self.outputs.extend(p for p in result.get("paths", []) if p)
        if result.get("error"):
            print(f"    ERROR: {result['error']}")
        if gate is not None:
            verdict = gate(result, self)
            if isinstance(verdict, tuple):
                ok, reason = verdict
            else:
                ok, reason = verdict, ""
            if not ok:
                if required:
                    raise RecipeAbort(label, reason or "gate failed")
                print(f"    [gate] {reason or 'failed'} (non-blocking)")
        return result

    def finish(self, status: str, note: str = "") -> Path:
        manifest = {
            "run_id": self.run_id, "status": status, "note": note,
            "params": self.params, "steps": self.steps,
            "outputs": self.outputs,
        }
        path = self.run_dir / "manifest.json"
        path.write_text(json.dumps(manifest, indent=2, default=str),
                        encoding="utf-8")
        return path


# ---------------------------------------------------------------------------
# Gates (shared)
# ---------------------------------------------------------------------------


def _gate_stills(result: dict, ctx: RecipeContext):
    paths = result.get("paths", [])
    return bool(paths), (f"{len(result.get('missing', []))} still(s) missing"
                         if not paths else "")


def _gate_ok(result: dict, ctx: RecipeContext):
    return bool(result.get("ok")), result.get("error", "") or "step failed"


def _gate_verified(result: dict, ctx: RecipeContext):
    return bool(result.get("ok")), "render verification failed"


# ---------------------------------------------------------------------------
# RECIPE claims
# ---------------------------------------------------------------------------


def recipe_claims(params: dict) -> dict:
    source = params.get("source") or params.get("text") or ""
    text = params.get("text", "")
    run_id = time.strftime("%Y%m%d-%H%M%S") + "-claims"
    ctx = RecipeContext(run_id, params)
    print(f"== recipe claims (run {run_id}) ==")
    if source and not text:
        path = Path(source)
        if not path.is_file():
            return {"ok": False, "error": f"no such file: {source}"}
        text = path.read_text(encoding="utf-8", errors="replace")
    if not text:
        return {"ok": False, "error": "claims needs source=<file> or text=..."}
    result = ctx.step("scan claims", "scan_claims", {"text": text},
                      gate=_gate_ok)
    pending = ledger.items(status="pending")
    if pending:
        print(f"\n{len(pending)} gap(s) now in the ledger. Resolve them "
              f"with: resolve led-XXXX = value | source")
    manifest = ctx.finish("done", f"{result.get('filed', 0)} claims filed")
    return {"ok": True, "filed": result.get("filed", 0),
            "manifest": str(manifest)}


# ---------------------------------------------------------------------------
# RECIPE stills
# ---------------------------------------------------------------------------


WORLDS = ("masterclass", "presenter", "dome_forge", "assembly_line")


def _seconds(values) -> list[str]:
    """Normalise a times argument to a list of second strings."""
    if isinstance(values, str):
        values = [v.strip() for v in values.split(",") if v.strip()]
    return [str(v).strip() for v in (values or []) if str(v).strip()]


def recipe_stills(params: dict) -> dict:
    backend = str(params.get("backend", "masterclass"))
    # Checked before any process is spawned: a typo here otherwise costs a
    # tool launch and shows up as an empty stills folder.
    if backend not in WORLDS:
        return {"ok": False, "error": f"unknown world {backend!r}; choose from "
                f"{', '.join(WORLDS)}"}
    times = _seconds(params.get("times", ["30", "90"]))
    if not times:
        return {"ok": False, "error": "times is required, e.g. times=30,90"}
    bad = [t for t in times if not re.fullmatch(r"\d+(?:\.\d+)?", t)]
    if bad:
        return {"ok": False, "error": f"times must be seconds: {bad}"}
    params = dict(params, times=times)
    run_id = time.strftime("%Y%m%d-%H%M%S") + f"-stills-{backend}"
    ctx = RecipeContext(run_id, params)
    print(f"== recipe stills (run {run_id}) ==")
    args = {"backend": backend, "times": times,
            "size": params.get("size", "1600x900")}
    if params.get("lesson"):
        args["lesson"] = params["lesson"]
    if params.get("demo"):
        args["demo"] = params["demo"]
    result = ctx.step(f"render {backend} stills", "render_stills", args,
                      gate=_gate_stills)
    ctx.step("open for review", "view",
             {"path": str(ctx.run_dir)}, gate=_gate_ok)
    manifest = ctx.finish("done")
    return {"ok": True, "paths": result.get("paths", []),
            "manifest": str(manifest)}


# ---------------------------------------------------------------------------
# RECIPE book
# ---------------------------------------------------------------------------


def recipe_book(params: dict) -> dict:
    run_id = time.strftime("%Y%m%d-%H%M%S") + "-book"
    ctx = RecipeContext(run_id, params)
    print(f"== recipe book (run {run_id}) ==")
    try:
        ctx.step("gate: full book selftest", "selftest", {"tool": "book"},
                 gate=_gate_ok)
        if params.get("figures"):
            ctx.step("render figures", "export_book",
                     {"action": "render_figures"}, gate=_gate_ok)
        ctx.step("build readable HTML", "export_book",
                 {"action": "read_html", "strict": True}, gate=_gate_ok)
        if params.get("pdf"):
            ctx.step("build PDF", "export_book",
                     {"action": "read_pdf", "strict": True}, gate=_gate_ok)
    except RecipeAbort as abort:
        manifest = ctx.finish("stopped", str(abort))
        return {"ok": False, "error": str(abort), "manifest": str(manifest)}
    ctx.step("open deliverables", "view",
             {"path": "deliverables/book"}, gate=_gate_ok)
    manifest = ctx.finish("done")
    return {"ok": True, "manifest": str(manifest)}


# ---------------------------------------------------------------------------
# RECIPE presenter
# ---------------------------------------------------------------------------


def _stage_prompt_brief(prompt: str, environment: str, out_json: Path) -> dict:
    """Mirror presenter_studio.load_presentation's prompt path: parse a
    brief into a skeleton Presentation and staple the default dome stage."""
    from dataclasses import replace
    from presenter.prompt import parse_brief
    pres = parse_brief(prompt, environment or "")
    default_world = (("dome", {"radius": 4.8}),
                     ("plenum", {"radius": 4.8}),
                     ("blower", {"radius": 4.8, "spin": 3.0}),
                     ("airflow", {"radius": 4.8, "intensity": 0.7}))
    pres = replace(pres, scenes=tuple(
        replace(scene, world=default_world) for scene in pres.scenes))
    pres.validate()
    out_json.parent.mkdir(parents=True, exist_ok=True)
    pres.to_json(out_json)
    return {"ok": True, "json": str(out_json),
            "scenes": len(pres.scenes),
            "note": "skeleton Presentation staged with the default dome world"}


def recipe_presenter(params: dict) -> dict:
    run_id = time.strftime("%Y%m%d-%H%M%S") + "-presenter"
    ctx = RecipeContext(run_id, params)
    print(f"== recipe presenter (run {run_id}) ==")
    demo = params.get("demo") or ""
    prompt = params.get("prompt") or ""
    script = params.get("script") or ""
    times = params.get("times", ["4", "20"])
    source = demo or script
    try:
        if prompt and not source:
            staged = _stage_prompt_brief(
                prompt, params.get("environment", ""),
                ctx.run_dir / "brief.json")
            source = str(staged["json"])
            print(f"    staged {staged['scenes']} scene(s) -> {staged['json']}")
        if not source:
            raise RecipeAbort("presenter", "need demo=..., script=..., or "
                                          "prompt=... (a brief is parsed and "
                                          "staged automatically)")
        args: dict = {"backend": "presenter", "times": times,
                      "size": params.get("size", "1600x900")}
        if script or str(source).endswith((".json", ".py")):
            args["script"] = str(source)
        else:
            args["demo"] = str(demo or source)
        ctx.step("render stills", "render_stills", args, gate=_gate_stills)
        if params.get("export"):
            export_args = {"out": params["export"],
                           "fps": int(params.get("fps", 30)),
                           "size": params.get("size", "1920x1080"),
                           "no_narration": bool(params.get("no_narration", False)),
                           "overlay": params.get("overlay", "full")}
            if script or str(source).endswith((".json", ".py")):
                export_args["script"] = str(source)
            else:
                export_args["demo"] = str(demo or source)
            export = ctx.step("export video", "export_video", export_args,
                              gate=_gate_ok)
            ctx.step("verify render", "verify_render",
                     {"path": export.get("video", "")}, gate=_gate_verified)
        ctx.step("open for review", "view",
                 {"path": str(ctx.run_dir)}, gate=_gate_ok)
    except RecipeAbort as abort:
        manifest = ctx.finish("stopped", str(abort))
        return {"ok": False, "error": str(abort), "manifest": str(manifest)}
    manifest = ctx.finish("done")
    return {"ok": True, "manifest": str(manifest)}


# ---------------------------------------------------------------------------
# RECIPE film  (the teaching-film loop)
# ---------------------------------------------------------------------------


def _lesson_by_key(key: str):
    """Load a lesson by importing its module directly — the registry may
    have been imported (and cached) before a registration edit in this
    process, so always go to the source module."""
    import importlib
    module = importlib.import_module(f"two_v_demo.lesson_{key}")
    lesson = getattr(module, f"{key.upper()}_LESSON")
    if lesson is None:
        raise ValueError(f"unknown lesson {key!r}")
    return lesson


def _chapter_times(key: str) -> list[str]:
    """One still time per chapter, at each chapter's midpoint (floor
    durations — the no-narration timeline)."""
    lesson = _lesson_by_key(key)
    starts: list[float] = []
    cursor = 0.0
    for chapter in lesson.chapters:
        starts.append(cursor + chapter.duration / 2.0)
        cursor += chapter.duration
    return [f"{t:.1f}" for t in starts]


def _read_source(params: dict) -> str:
    source = params.get("source", "")
    if not source:
        return params.get("text", "")
    path = Path(source)
    if not path.is_file():
        raise RecipeAbort("film", f"no such source file: {source}")
    return path.read_text(encoding="utf-8", errors="replace")


def recipe_film(params: dict) -> dict:
    key = str(params.get("key", "")).lower()
    title = str(params.get("title", ""))
    if not re.fullmatch(r"[a-z][a-z0-9_]{1,15}", key):
        return {"ok": False, "error": f"key must match [a-z][a-z0-9_]{{1,15}}: {key!r}"}
    if not title:
        title = f"{key.replace('_', ' ').title()} Masterclass"
    run_id = time.strftime("%Y%m%d-%H%M%S") + f"-film-{key}"
    ctx = RecipeContext(run_id, params)
    print(f"== recipe film (run {run_id}) key={key} ==")
    facts_path = config.REPO_ROOT / "two_v_demo" / f"{key}_facts.py"
    lesson_path = config.REPO_ROOT / "two_v_demo" / f"lesson_{key}.py"

    try:
        # 0. Declared constants from params (name=value unit|source).
        for declaration in params.get("declare", []) or []:
            name, _, rest = str(declaration).partition("=")
            value, _, source = rest.partition("|")
            value, _, unit = value.strip().partition(" ")
            tools.dispatch("declare_constant",
                           {"name": name.strip(), "value": value.strip(),
                            "unit": unit.strip(), "source": source.strip()})

        source_text = _read_source(params)
        if source_text:
            result = ctx.step("claim sweep", "scan_claims", {"text": source_text},
                              gate=_gate_ok)

        # 1. Scaffold (skips if the files already exist — resumable).
        if facts_path.is_file() or lesson_path.is_file():
            print("\n[scaffold] files exist — skipping (resume)")
            scaffold = {"ok": True, "resumed": True}
        else:
            scaffold = templates.run_process(
                ["scaffold_lesson.py", key, title], f"scaffold_{key}",
                timeout=300)
            ctx.steps.append({"label": "scaffold lesson", "tool": "scaffold",
                              "args": {"key": key, "title": title},
                              "ok": scaffold["ok"], "result": scaffold})
            if not scaffold["ok"]:
                raise RecipeAbort("film", f"scaffold failed: {scaffold['tail']}")

        # 2. Constants injection (mechanical, from resolved declared items).
        items = ledger.items(kind="declared", status="resolved")
        if items:
            result = templates.inject_constants(facts_path, items)
            ctx.steps.append({"label": "inject constants", "tool": "template",
                              "args": {"file": str(facts_path)},
                              "ok": result["ok"], "result": result})
            if not result["ok"]:
                raise RecipeAbort("film", result["error"])
            print(f"    injected {result.get('injected', 0)} constant(s): "
                  f"{result.get('names', [])}")

        # 3. Narration (mechanical, from source sentences — never clobbers).
        if source_text:
            sentences = [s.strip() for s in _SENTENCE.split(source_text)
                         if len(s.strip()) >= 12]
            result = templates.replace_narration(lesson_path, sentences)
            ctx.steps.append({"label": "fill narration", "tool": "template",
                              "args": {"file": str(lesson_path)},
                              "ok": result["ok"], "result": result})
            print(f"    narrated {result.get('replaced', 0)} chapter(s) "
                  f"({result.get('skipped', 0)} already authored)")

        # 4. Compile gates before touching the registry.
        for path in (facts_path, lesson_path):
            compiled = templates.validate_python(path)
            if not compiled["ok"]:
                raise RecipeAbort("film", f"{path.name} does not compile: "
                                          f"{compiled.get('error', '')}")

        # 5. Register: the three-file contract with backups + validators.
        #    First repair any pre-existing drift (registered lessons with
        #    no deliverable/preset entries), which the repo's own
        #    validate_deliverables treats as a failure.
        repair = templates.repair_registration()
        ctx.steps.append({"label": "repair registration drift",
                          "tool": "template", "args": {}, "ok": repair["ok"],
                          "result": repair})
        print(f"    repair: {repair.get('note', repair)}")
        if not repair["ok"]:
            raise RecipeAbort("film", repair.get("error", "repair failed"))
        filename = f"{key}-masterclass.mp4"
        summary = f"Generated by the project agent film recipe: {title}."
        registration = templates.register_lesson(key, filename, summary)
        ctx.steps.append({"label": "register lesson", "tool": "template",
                          "args": {"key": key, "filename": filename},
                          "ok": registration["ok"], "result": registration})
        print(f"    registration: {registration.get('note', registration)}")
        if not registration["ok"]:
            raise RecipeAbort("film", registration.get("error", "registration failed"))

        # 6. Proof gate: the full lesson selftest.
        ctx.step("selftest", "selftest",
                 {"tool": "masterclass", "lesson": key}, gate=_gate_ok)

        # 7. Stills gate: one per chapter, then look.
        times = _chapter_times(key)
        stills = ctx.step("stills (one per chapter)", "render_stills",
                          {"backend": "masterclass", "lesson": key,
                           "times": times, "size": params.get("size", "1600x900")},
                          gate=_gate_stills)
        ctx.step("open for review", "view",
                 {"path": str(config.REPO_ROOT / "two_v_demo_output" / key)},
                 gate=_gate_ok)

        # 8. Optional export + frame-count verification.  The repo's
        #    verify_render checks audio/video drift, which only applies to
        #    narrated renders; silent exports are checked by existence +
        #    the exporter's own success.
        if params.get("export"):
            export_args = {
                "lesson": key, "out": params["export"],
                "fps": int(params.get("fps", 30)),
                "size": params.get("size", "1920x1080"),
                "no_narration": bool(params.get("no_narration", False)),
                # Both of these are what a published film is actually made
                # with; without them a recipe export is a different cut from
                # the one the launcher preset produces.
                "compose_segments": bool(params.get("compose_segments", False)),
            }
            for passthrough in ("voice", "voice_rate", "voice_pitch",
                                "voice_volume", "orientation"):
                if params.get(passthrough):
                    export_args[passthrough] = params[passthrough]
            export = ctx.step("export video", "export_video", export_args,
                              gate=_gate_ok)
            if not params.get("no_narration"):
                ctx.step("verify render", "verify_render",
                         {"path": export.get("video", "")},
                         gate=_gate_verified)
            else:
                print("    [note] silent render: frame-count gate skipped "
                      "(verify_render checks audio drift)")
    except RecipeAbort as abort:
        manifest = ctx.finish("stopped", str(abort))
        return {"ok": False, "error": str(abort), "manifest": str(manifest)}

    manifest = ctx.finish("done")
    print(f"\nfilm recipe done: {manifest}")
    print("next steps: look at the stills (opened), review the ledger, then "
          "re-run with export=exports/<name>.mp4 when the copy is final.")
    return {"ok": True, "key": key, "manifest": str(manifest)}


# ---------------------------------------------------------------------------
# Registry + runner
# ---------------------------------------------------------------------------


RECIPES: dict[str, dict] = {
    "claims": {"label": "text -> classified claims + resolution ledger",
               "run": recipe_claims},
    "stills": {"label": "render + review stills from any world",
               "run": recipe_stills},
    "book": {"label": "book selftest -> figures -> readable HTML/PDF",
             "run": recipe_book},
    "presenter": {"label": "validate/stage a Presentation -> stills -> export",
                  "run": recipe_presenter},
    "film": {"label": "teaching film: claims -> scaffold -> register -> "
                      "selftest -> stills -> export -> verify",
             "run": recipe_film},
}


def run_recipe(recipe: str, params: dict | None = None) -> dict:
    """Run one recipe. Never raises: a caller gets a result dict either way.

    A recipe spawns renders and edits files, so it can fail in ways nobody
    predicted. When that happens it still owes the run a manifest and the
    reason — a traceback printed into a chat session is not a result, and
    leaves nothing to look at afterwards.
    """
    ensure_dirs()
    spec = RECIPES.get(recipe)
    if spec is None:
        return {"ok": False, "error": f"unknown recipe {recipe!r}; "
                f"choose from {', '.join(sorted(RECIPES))}"}
    try:
        return spec["run"](params or {})
    except RecipeAbort as abort:
        return {"ok": False, "error": str(abort)}
    except KeyboardInterrupt:
        return {"ok": False, "error": "interrupted before the recipe finished"}
    except Exception as exc:                              # noqa: BLE001
        run_id = time.strftime("%Y%m%d-%H%M%S") + f"-{recipe}-crash"
        context = RecipeContext(run_id, params or {})
        context.steps.append({"label": "unhandled error", "tool": recipe,
                              "args": params or {}, "ok": False,
                              "result": {"traceback":
                                         traceback.format_exc(limit=6)}})
        manifest = context.finish("crashed", f"{type(exc).__name__}: {exc}")
        return {"ok": False, "error": f"{type(exc).__name__}: {exc}",
                "manifest": str(manifest)}


def recipes_text() -> str:
    return "\n".join(f"  {key:<12} {spec['label']}"
                     for key, spec in RECIPES.items())
