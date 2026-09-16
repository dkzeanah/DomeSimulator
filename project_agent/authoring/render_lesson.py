"""Render any lesson module on its own, without registering it anywhere.

The normal path for a film is the three-file registration contract, so the
launcher and the deliverables table know about it. That is the right thing for
a film you intend to publish, and the wrong thing for one you are still
writing: you want to look at it before you commit to it existing.

This runner takes a module that defines a Lesson and plays it directly.

    # prove it, without drawing anything
    py -3.12 project_agent/authoring/render_lesson.py --module two_v_demo.lesson_mything --selftest

    # look at it: PNGs at chosen seconds
    py -3.12 project_agent/authoring/render_lesson.py --module two_v_demo.lesson_mything --stills 6,20,34

    # one still per chapter, at each chapter's midpoint
    py -3.12 project_agent/authoring/render_lesson.py --module two_v_demo.lesson_mything --chapter-stills

    # the whole film, narrated, as an MP4
    py -3.12 project_agent/authoring/render_lesson.py --module two_v_demo.lesson_mything --export exports/mything.mp4

A file that is not importable as a module works too:

    py -3.12 project_agent/authoring/render_lesson.py --file some/where/lesson_draft.py --stills 5

Notes
-----
* Inspect stills before a full export. Cost depends on duration, geometry,
  resolution, frame rate, and whether narration must be synthesized.
* Each still run gets a new folder, so earlier review images are preserved.
* Exports are append-only. Pointing --export at a file that exists writes
  the next version beside it (-v2, -v3) rather than overwriting the old cut.
* --silent skips narration entirely, which is the fast way to check motion
  and timing without waiting on speech synthesis.
"""

from __future__ import annotations

import argparse
import importlib
import importlib.util
import math
import sys
from datetime import datetime
from pathlib import Path
import uuid

REPO_ROOT = Path(__file__).resolve().parent.parent.parent
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))


def load_module(module_name: str = "", file_path: str = ""):
    """Import by dotted name, or load a loose file by path."""
    if module_name:
        return importlib.import_module(module_name)
    path = Path(file_path)
    if not path.is_file():
        raise SystemExit(f"no such file: {path}")
    spec = importlib.util.spec_from_file_location(path.stem, path)
    if spec is None or spec.loader is None:
        raise SystemExit(f"cannot load {path}")
    module = importlib.util.module_from_spec(spec)
    sys.modules[path.stem] = module
    spec.loader.exec_module(module)
    return module


def find_lesson(module):
    """The Lesson object in a module, whatever it is called.

    Looked up by type rather than by name so an authored file can call it
    MY_LESSON, LESSON, or anything else and still play.
    """
    from two_v_demo.lessons import Lesson

    # Aliases of one instance are harmless; distinct films are ambiguous.
    found = list({id(value): value for name, value in vars(module).items()
                  if isinstance(value, Lesson) and not name.startswith("_")}.values())
    if not found:
        raise SystemExit(
            f"{module.__name__} defines no Lesson. A lesson module must end "
            "with something like:  MY_LESSON = Lesson(key=..., chapters=..., "
            "scenes=...)")
    if len(found) > 1:
        names = ", ".join(sorted(lesson.key for lesson in found))
        raise SystemExit(f"Multiple public Lessons in {module.__name__}: {names}. "
                         "Keep exactly one public LESSON so an isolated export cannot select the wrong film.")
    return found[0]


def chapter_midpoints(lesson) -> list[str]:
    """One second-mark per chapter, at its midpoint on the silent timeline."""
    times: list[str] = []
    cursor = 0.0
    for chapter in lesson.chapters:
        times.append(f"{cursor + chapter.duration / 2.0:.1f}")
        cursor += chapter.duration
    return times


def parse_size(value: str) -> tuple[int, int]:
    try:
        width, height = (int(part) for part in value.lower().split("x", 1))
    except ValueError:
        raise SystemExit(f"--size wants WIDTHxHEIGHT, not {value!r}") from None
    if width < 64 or height < 64 or width % 2 or height % 2:
        raise SystemExit("--size needs even dimensions of at least 64 pixels for H.264 export")
    return width, height


def validate_timeline(lesson, times: list[str]) -> list[float]:
    """Reject broken content or wrapped screenshot times before creating GL."""
    for chapter in lesson.chapters:
        if not math.isfinite(chapter.duration) or chapter.duration <= 0.5:
            raise SystemExit("Chapter durations must be finite and exceed 0.5 seconds")
        if len(chapter.camera) != 3 or not all(math.isfinite(x) for x in chapter.camera) or chapter.camera[2] <= 0:
            raise SystemExit("Each camera needs finite yaw, pitch, and positive distance")
        if lesson.scenes and chapter.stage not in lesson.scenes:
            raise SystemExit(f"Chapter stage {chapter.stage!r} is missing from SCENES")
    total = sum(chapter.duration for chapter in lesson.chapters)
    seconds = []
    for value in times:
        try:
            second = float(value)
        except ValueError:
            raise SystemExit(f"still times are seconds: {value!r}") from None
        if not math.isfinite(second) or not 0 <= second < total:
            raise SystemExit(f"Still time {value} must be at least zero and below the silent duration {total:g}s")
        seconds.append(second)
    return seconds


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="Play one lesson module without registering it.")
    source = parser.add_mutually_exclusive_group(required=True)
    source.add_argument("--module", default="",
                        help="dotted module, e.g. two_v_demo.lesson_mything")
    source.add_argument("--file", default="",
                        help="path to a .py file that defines a Lesson")
    parser.add_argument("--selftest", action="store_true",
                        help="run the lesson's own proof and stop")
    parser.add_argument("--stills", default="",
                        help="comma-separated seconds, e.g. 6,20,34")
    parser.add_argument("--chapter-stills", action="store_true",
                        help="one still per chapter, at each midpoint")
    parser.add_argument("--export", default="",
                        help="render the whole film to this .mp4")
    parser.add_argument("--out-dir", default="",
                        help="where stills go (default: two_v_demo_output/<key>)")
    parser.add_argument("--size", default="1600x900")
    parser.add_argument("--fps", type=int, default=30)
    parser.add_argument("--silent", action="store_true",
                        help="export without narration (much faster)")
    parser.add_argument("--no-selftest", action="store_true",
                        help="skip the lesson proof before rendering")
    args = parser.parse_args(argv)
    if not 1 <= args.fps <= 120:
        parser.error("--fps must be between 1 and 120")
    width, height = parse_size(args.size)

    module = load_module(args.module, args.file)
    lesson = find_lesson(module)
    print(f"lesson: {lesson.key}  {lesson.title}  "
          f"({len(lesson.chapters)} chapters, style {lesson.style})")

    lesson.validate()
    validate_timeline(lesson, [])
    print("  lesson.validate() ok")
    if lesson.selftest is not None and not args.no_selftest:
        lesson.selftest()
        print(f"  {lesson.selftest.__name__}() ok")
    if args.selftest:
        return 0

    times = [t.strip() for t in args.stills.split(",") if t.strip()]
    if args.chapter_stills:
        times = chapter_midpoints(lesson)
    if not times and not args.export:
        print("nothing to do: pass --stills, --chapter-stills or --export")
        return 2

    # Imported here so --selftest costs no window and no GL context.
    from two_v_demo.app import MasterclassApp

    seconds = validate_timeline(lesson, times)
    app = MasterclassApp(size=(width, height), hidden=True, lesson=lesson)
    try:
        if times:
            out_dir = Path(args.out_dir) if args.out_dir else (
                REPO_ROOT / "two_v_demo_output" / lesson.key)
            out_dir = out_dir / (datetime.now().strftime("review-%Y%m%d-%H%M%S-") + uuid.uuid4().hex[:8])
            paths = app.render_shots(seconds, out_dir)
            print(f"{len(paths)} still(s) in {out_dir}")
        if args.export:
            target = Path(args.export)
            target.parent.mkdir(parents=True, exist_ok=True)
            app.export_video(target, fps=args.fps, narration=not args.silent)
    finally:
        app.pygame.quit()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
