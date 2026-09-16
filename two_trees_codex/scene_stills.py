"""Capture real lesson frames for the Codex book without modifying the lessons.

The public function runs the existing video renderer in a separate, hidden
process. This keeps its pygame/OpenGL context away from the Tk book editor and
leaves the shared lesson objects, camera functions, and source files untouched.
Each request creates a new directory with a PNG, recipe, provenance, and logs.
"""
from __future__ import annotations

import argparse
from dataclasses import asdict, replace
from datetime import datetime, timezone
import hashlib
import json
import math
import os
from pathlib import Path
import re
import shutil
import subprocess
import sys
import uuid


ROOT = Path(__file__).resolve().parents[1]
SCHEMA = "two-trees-scene-still/v1"
OVERLAYS = ("original", "clean", "teaching", "math")
DEPENDENCIES = ("numpy", "pygame", "moderngl")


class SceneRenderError(RuntimeError):
    """A scene could not be captured; the message locates the render logs."""


def _json_write(path: Path, value: object) -> None:
    # All files belong to a newly-created job directory. Exclusive writes also
    # protect a completed artifact if a worker is inadvertently run a second time.
    with path.open("x", encoding="utf-8") as stream:
        json.dump(value, stream, ensure_ascii=False, indent=2, allow_nan=False)
        stream.write("\n")


def _sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _digest(value: object) -> str:
    return hashlib.sha256(json.dumps(value, ensure_ascii=False, sort_keys=True,
                                    allow_nan=False).encode("utf-8")).hexdigest()


def _validated_request(scene: dict, progress: float | None, width: int,
                       height: int, overlay: str) -> dict:
    if not isinstance(scene, dict):
        raise ValueError("Select a scene from the book's scene catalog first.")
    for field in ("lesson_key", "chapter_slug"):
        if not isinstance(scene.get(field), str) or not scene[field].strip():
            raise ValueError(f"Scene requires a nonempty {field}.")
    if overlay not in OVERLAYS:
        raise ValueError(f"Overlay must be one of: {', '.join(OVERLAYS)}.")
    selected = scene.get("progress", 0.85) if progress is None else progress
    selected = 0.85 if selected is None else selected
    try:
        selected = float(selected)
    except (ValueError, TypeError):
        raise ValueError("Scene progress must be a finite number from 0 to 1.") from None
    if not math.isfinite(selected) or not 0 <= selected <= 1:
        raise ValueError("Scene progress must be a finite number from 0 to 1.")
    for field, value in (("width", width), ("height", height)):
        if isinstance(value, bool) or not isinstance(value, int) or not 256 <= value <= 4096:
            raise ValueError(f"Scene {field} must be an integer from 256 to 4096 pixels.")
    # Keep only plain catalog metadata in the cross-process document.
    selected_scene = {key: scene[key] for key in (
        "id", "lesson_key", "chapter_slug", "title", "stage", "duration",
        "camera", "caption", "source_hash", "source_file") if key in scene}
    request = {"schema": SCHEMA, "scene": selected_scene, "progress": selected,
               "width": width, "height": height, "overlay": overlay}
    try:
        json.dumps(request, allow_nan=False)
    except (TypeError, ValueError) as exc:
        raise ValueError(f"Scene metadata must contain finite JSON values: {exc}") from exc
    return request


def _process_options() -> dict:
    return {"creationflags": subprocess.CREATE_NO_WINDOW} if os.name == "nt" else {}


def _select_python() -> str:
    """Prefer this interpreter; permit an explicit renderer runtime override."""
    configured = os.environ.get("TWO_TREES_SCENE_PYTHON")
    candidates = [configured] if configured else [
        sys.executable,
        str(Path(os.environ.get("LOCALAPPDATA", "")) / "Python" /
            "pythoncore-3.12-64" / "python.exe") if os.name == "nt" else None,
        shutil.which("python"),
    ]
    failures = []
    probe = ("import importlib.util,json; print(json.dumps([n for n in "
             f"{DEPENDENCIES!r} if importlib.util.find_spec(n) is None]))")
    for candidate in dict.fromkeys(candidate for candidate in candidates if candidate):
        try:
            result = subprocess.run([candidate, "-c", probe], capture_output=True,
                                    text=True, encoding="utf-8", errors="replace",
                                    timeout=20, **_process_options())
            missing = json.loads(result.stdout.strip()) if result.returncode == 0 else None
            if missing == []:
                return candidate
            failures.append(f"{candidate}: missing {', '.join(missing)}" if missing
                            else f"{candidate}: {result.stderr.strip()[-500:]}")
        except (OSError, subprocess.TimeoutExpired, json.JSONDecodeError) as exc:
            failures.append(f"{candidate}: {exc}")
    raise SceneRenderError(
        "No Python runtime with the video renderer dependencies was found. "
        "Use the same Python as the existing video launcher, or install its "
        "dependencies with: python -m pip install numpy pygame moderngl. "
        "TWO_TREES_SCENE_PYTHON can specify that python.exe.\n" + "\n".join(failures))


def render_scene_still(scene: dict, output_dir: Path, progress: float | None = None,
                       width: int = 1600, height: int = 1000,
                       overlay: str = "original") -> dict:
    """Render a deterministic lesson snapshot in a new, versioned directory.

    ``progress`` is normalized chapter time, including the engine's own camera
    motion and timed labels. ``original`` retains all original presentation;
    ``clean`` omits every 2D overlay; teaching/math reuse the engine's overlays.
    Source calculations are illustrative source defaults, not the book's field
    records. No narration is synthesized and no source files are written.
    """
    request = _validated_request(scene, progress, width, height, overlay)
    executable = _select_python()
    scene_slug = re.sub(r"[^a-zA-Z0-9_-]+", "-",
                        str(scene.get("id") or f"{scene['lesson_key']}-{scene['chapter_slug']}"))[:90]
    stamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%S%fZ")
    job = Path(output_dir).resolve() / f"scene-{scene_slug}-{stamp}-{uuid.uuid4().hex[:8]}"
    job.mkdir(parents=True, exist_ok=False)
    request_path = job / "request.json"
    _json_write(request_path, request)
    env = os.environ.copy()
    env.update({"PYTHONUTF8": "1", "PYTHONIOENCODING": "utf-8",
                "PYTHONDONTWRITEBYTECODE": "1", "PYGAME_HIDE_SUPPORT_PROMPT": "1",
                "SDL_AUDIODRIVER": "dummy"})
    command = [executable, "-B", "-m", "two_trees_codex.scene_stills",
               "--worker", str(request_path)]
    stdout_path, stderr_path = job / "stdout.log", job / "stderr.log"
    try:
        with stdout_path.open("x", encoding="utf-8") as stdout, \
                stderr_path.open("x", encoding="utf-8") as stderr:
            result = subprocess.run(command, cwd=str(ROOT), env=env, stdout=stdout,
                                    stderr=stderr, timeout=180, **_process_options())
    except (OSError, subprocess.TimeoutExpired) as exc:
        raise SceneRenderError(f"Scene render could not finish: {exc}\nLogs: {job}") from exc
    result_path = job / "result.json"
    if result.returncode != 0 or not result_path.exists():
        diagnostic = stderr_path.read_text(encoding="utf-8", errors="replace")[-3500:]
        raise SceneRenderError(
            f"Scene renderer failed (exit {result.returncode}). Logs: {job}\n"
            "The existing renderer needs a working desktop OpenGL 3.3 driver; "
            "a dummy SDL video driver cannot render this scene.\n" + diagnostic)
    value = json.loads(result_path.read_text(encoding="utf-8"))
    if not Path(value["path"]).is_file() or not Path(value["provenance_path"]).is_file():
        raise SceneRenderError(f"Renderer returned incomplete output. Logs: {job}")
    return value


def _source_files() -> dict[str, str]:
    """Fingerprint imported repository code, including each painter's helpers."""
    sources = {}
    for module in list(sys.modules.values()):
        filename = getattr(module, "__file__", None)
        if not filename:
            continue
        source = Path(filename).resolve()
        if source.suffix != ".py" or not source.is_relative_to(ROOT) or not source.is_file():
            continue
        sources[source.relative_to(ROOT).as_posix()] = _sha256(source)
    return dict(sorted(sources.items()))


def _worker(request_path: Path) -> dict:
    # Import scene code only inside this worker: the book's editor needs neither
    # an OpenGL context nor the source registry's import side effects.
    from two_v_demo.app import MasterclassApp
    from two_v_demo.lesson_registry import get_lesson

    request = json.loads(request_path.read_text(encoding="utf-8"))
    scene = request["scene"]
    request = _validated_request(scene, request["progress"], request["width"],
                                 request["height"], request["overlay"])
    original_lesson = get_lesson(scene["lesson_key"])
    matches = [(index, chapter) for index, chapter in enumerate(original_lesson.chapters)
               if chapter.slug == scene["chapter_slug"]]
    if len(matches) != 1:
        raise ValueError(f"Scene {scene['chapter_slug']!r} is missing or ambiguous in "
                         f"lesson {original_lesson.key!r}. Refresh the scene catalog.")
    index, original_chapter = matches[0]
    if scene.get("stage") and scene["stage"] != original_chapter.stage:
        raise ValueError("The scene stage changed after cataloging. Refresh the scene catalog.")
    sources_before = _source_files()
    overlay = request["overlay"]
    chapter = original_chapter
    if overlay in ("teaching", "math"):
        chapter = replace(chapter, overlay=overlay)
    chapters = list(original_lesson.chapters)
    chapters[index] = chapter
    lesson = replace(original_lesson, chapters=tuple(chapters))

    class BookStillApp(MasterclassApp):
        def draw_ui(self, width, height):
            if overlay == "clean":
                self.ui_buttons.clear()
                return self.pygame.Surface((width, height), self.pygame.SRCALPHA)
            return super().draw_ui(width, height)

    app = None
    job = request_path.parent.resolve()
    try:
        app = BookStillApp(size=(request["width"], request["height"]),
                           hidden=True, lesson=lesson)
        app.output_dir = job
        app.set_chapter(index)
        app.playing = False
        # Video exports use this flag for the orbit camera's 7-degree movement.
        # render_shots() pauses it; retaining it makes a snapshot follow video.
        app.exporting = True
        app.chapter_progress = request["progress"]
        app.timeline += app.chapter_progress * app.chapter_durations[index]
        actual_size = app.pygame.display.get_window_size()
        if actual_size != (request["width"], request["height"]):
            raise RuntimeError(f"OpenGL created {actual_size}, requested "
                               f"{request['width']} x {request['height']}. Choose a smaller still.")
        app.render(present=False)
        path = job / "still.png"
        if path.exists():
            raise FileExistsError(f"Refusing to overwrite an existing still: {path}")
        app.save_screenshot(path)
        eye, target = app.camera()
        fov = 48.0
        camera_fn = lesson.camera_fn
        if camera_fn is not None:
            eye, target, fov = camera_fn(app, chapter, app.chapter_progress, *actual_size)
        recipe = {"lesson_key": lesson.key, "chapter_slug": chapter.slug,
                  "stage": chapter.stage, "progress": app.chapter_progress,
                  "camera": list(chapter.camera), "width": actual_size[0],
                  "height": actual_size[1], "overlay": overlay}
        from two_v_demo.callouts import schedule
        placed = schedule(chapter, app.chapter_durations[index],
                          speak_promise=app.speak_promise, rate=lesson.voice_rate)
        # Preserve the schedule, including inactive rows, so a book author can
        # choose a new progress that lands the desired explanatory number.
        callouts = [{"text": item.text, "unit": item.unit, "note": item.note,
                     "start_seconds": item.start, "end_seconds": item.end,
                     "active": item.start < app.chapter_progress * chapter.duration < item.end}
                    for item in placed]
        sources = _source_files()
        changed = [name for name, digest in sources_before.items()
                   if sources.get(name) != digest]
        if changed:
            raise RuntimeError("Source changed while rendering; refresh the catalog and retry: "
                               + ", ".join(changed))
        actual_overlay = "clean" if overlay == "clean" else chapter.overlay or lesson.style
        provenance = {
            "schema": SCHEMA,
            "created_utc": datetime.now(timezone.utc).isoformat(),
            "engine": "two_v_demo.app.MasterclassApp",
            "engine_mode": "hidden OpenGL; same scene painters, camera and overlays as video export",
            "recipe": recipe,
            "source_lesson_title": original_lesson.title,
            "source_chapter": asdict(original_chapter),
            "source_assumptions": "Source lesson model defaults. These figures are not "
                                  "verified field results and may differ from the manuscript's scenario.",
            "timing_basis": "Authored lesson durations; no audio synthesized or cached speech retiming loaded.",
            "chapter_duration_seconds": chapter.duration,
            "chapter_time_seconds": chapter.duration * app.chapter_progress,
            "lesson_time_seconds": app.timeline,
            "effective_overlay": actual_overlay,
            "world_labels_included": overlay != "clean",
            "callouts_included": overlay != "clean",
            "world_labels": [label.text for label in app.world_labels],
            "world_icon_count": len(app.world_icons),
            "callouts": callouts,
            "resolved_camera": {"eye": [float(v) for v in eye],
                                "target": [float(v) for v in target], "fov": float(fov),
                                "function": (f"{camera_fn.__module__}.{camera_fn.__qualname__}"
                                             if camera_fn else "MasterclassApp.camera")},
            "source_files_sha256": sources,
            "source_digest": _digest(sources),
            "recipe_digest": _digest(recipe),
            "image_sha256": _sha256(path),
            "runtime": {"python": sys.version, "executable": sys.executable,
                        "pygame": app.pygame.version.ver,
                        "moderngl": app.moderngl.__version__,
                        "opengl_vendor": app.ctx.info.get("GL_VENDOR"),
                        "opengl_renderer": app.ctx.info.get("GL_RENDERER"),
                        "opengl_version": app.ctx.info.get("GL_VERSION")},
        }
        provenance_path = job / "provenance.json"
        _json_write(provenance_path, provenance)
        caption = scene.get("caption") or (
            f"{chapter.title} — scene study from {original_lesson.title}, "
            f"{app.chapter_progress:.0%} through the scene. "
            "Figures show the source model's assumptions, not a field record.")
        provenance_text = (
            f"Rendered from {original_lesson.title} / {chapter.slug} at "
            f"{app.chapter_progress:.0%}, using the original video scene and camera "
            f"({overlay} overlay). Source model assumptions, not verified field results. "
            "Timing uses authored chapter durations; source hashes and the complete "
            "snapshot recipe are saved with this image.")
        result = {"path": str(path), "caption": caption,
                  "scene_id": scene.get("id", f"{lesson.key}:{chapter.slug}"),
                  "recipe": recipe, "provenance": provenance_text,
                  "render_metadata": provenance,
                  "provenance_path": str(provenance_path),
                  "stdout_path": str(job / "stdout.log"),
                  "stderr_path": str(job / "stderr.log")}
        _json_write(job / "result.json", result)
        print(f"Saved scene still: {path}")
        return result
    finally:
        if app is not None:
            app.pygame.quit()


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--worker", type=Path)
    parser.add_argument("--lesson", default="harvest")
    parser.add_argument("--chapter", default="tree")
    parser.add_argument("--progress", type=float, default=0.85)
    parser.add_argument("--overlay", choices=OVERLAYS, default="original")
    parser.add_argument("--width", type=int, default=1600)
    parser.add_argument("--height", type=int, default=1000)
    parser.add_argument("--output", type=Path, default=Path(__file__).parent / "workspace" / "scene_stills")
    args = parser.parse_args()
    if args.worker:
        _worker(args.worker)
    else:
        result = render_scene_still(
            {"lesson_key": args.lesson, "chapter_slug": args.chapter}, args.output,
            args.progress, args.width, args.height, args.overlay)
        print(json.dumps({key: result[key] for key in ("path", "caption", "recipe", "provenance_path")},
                         ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
