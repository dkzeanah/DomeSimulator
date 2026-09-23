"""Render a long film in pieces and join them, because long renders die here.

The stem-cell campaign cut is twenty minutes and it has never finished in one
process. It has stopped at 513s and at 773s; the point moves when the workload
changes, which rules out a bad frame and points at something cumulative that
nobody has pinned down yet. Meanwhile the five-minute films render first time,
every time.

So: stop asking one process to draw twenty minutes. Give each process four or
five chapters, let it exit, and concatenate what comes out. Every piece is a
short render, and short renders work.

Three things make the joins invisible.

**One narration, sliced.** The speech is synthesised once, into one plan, and
every segment muxes the slice of that one track belonging to its chapters. No
segment ever asks the speech service for anything, so no two segments can
disagree about how long a word took.

**Frame-exact windows.** A segment's window is computed from the same chapter
durations the whole film uses, so segment two starts on the frame segment one
stopped on. No overlap to crossfade, no gap to hide.

**Stream copy at the join.** The pieces are concatenated without re-encoding,
so the finished file is bit-identical to what the segments rendered. Joining is
not a second generation of encoding.

What this does not do is explain why the long render fails. It routes around
it. That is worth saying plainly: this is a workaround with a clean seam, not
a diagnosis.
"""

from __future__ import annotations

import json
import math
import subprocess
import sys
from dataclasses import dataclass
from pathlib import Path

ROOT = Path(__file__).resolve().parent
MASTERCLASS = ROOT / "two_v_masterclass.py"


@dataclass(frozen=True)
class Segment:
    """One piece of the film: a chapter window and where its file goes."""

    index: int
    first: int      # 1-based, inclusive
    last: int       # 1-based, inclusive
    path: Path

    @property
    def window(self) -> str:
        return f"{self.first}-{self.last}"


def plan_segments(chapters: int, per: int, target: Path) -> list[Segment]:
    """Cut a chapter count into windows of at most ``per``."""
    if chapters < 1:
        raise ValueError("a film with no chapters cannot be segmented")
    per = max(1, per)
    segments, index, first = [], 1, 1
    while first <= chapters:
        last = min(chapters, first + per - 1)
        segments.append(Segment(
            index, first, last,
            target.with_name(f".{target.stem}-seg{index:02d}{target.suffix}")))
        first = last + 1
        index += 1
    return segments


def _ffmpeg() -> str:
    from two_v_demo.app import resolve_executable

    return resolve_executable("ffmpeg", None)


def concat(segments: list[Segment], target: Path) -> Path:
    """Join the pieces without re-encoding a single frame."""
    listing = target.with_suffix(".segments.txt")
    # Absolute paths, and written as ASCII without a BOM. ffmpeg resolves a
    # concat entry relative to the *listing file's* directory rather than the
    # working directory, so a relative path that reads correctly from the
    # shell resolves to nonsense from inside the list -- which is how the
    # first six-segment run rendered every piece and then failed to join
    # them.
    listing.write_text(
        "\n".join(f"file '{s.path.resolve().as_posix()}'" for s in segments)
        + "\n", encoding="ascii")
    subprocess.run(
        [_ffmpeg(), "-y", "-f", "concat", "-safe", "0", "-i", str(listing),
         "-c", "copy", "-movflags", "+faststart", str(target)],
        check=True, capture_output=True)
    listing.unlink(missing_ok=True)
    return target


def probe_seconds(path: Path) -> float:
    out = subprocess.run(
        ["ffprobe", "-v", "error", "-show_entries", "format=duration",
         "-of", "csv=p=0", str(path)],
        capture_output=True, text=True)
    try:
        return float(out.stdout.strip())
    except ValueError:
        return 0.0


def render(lesson: str, target: Path, plan: Path, per: int = 5,
           orientation: str = "landscape", keep: bool = False,
           compose: bool = True) -> dict:
    """Render ``lesson`` in windows of ``per`` chapters and join them.

    ``plan`` is an existing narration plan. It is required rather than
    optional: segments must share one, and synthesising per segment would
    both waste the speech service and risk two pieces disagreeing.
    """
    if not plan.is_file():
        raise FileNotFoundError(
            f"no narration plan at {plan}. Render the film once with "
            "narration (it may fail part way -- the plan is written before "
            "the first frame) and point this at the plan it left behind.")

    # The chapter count comes from the narration plan, not from the lesson.
    # A composed film is the lesson's chapters plus the spliced call-to-action
    # and outro, so the lesson says 28 where the film the plan was built for
    # is 30 -- and a window over the wrong count silently drops the end of
    # the film. The plan is what the render is being matched against, so the
    # plan is what decides.
    plan_data = json.loads(plan.read_text(encoding="utf-8"))
    chapters = len(plan_data.get("chapter_durations") or [])
    if chapters < 1:
        raise ValueError(f"{plan} has no chapter_durations")
    segments = plan_segments(chapters, per, target)
    made: list[Segment] = []
    for segment in segments:
        ticket = {
            "lesson": lesson,
            "action": "export_video",
            # Composition has to match the plan the segments are muxed
            # against. The plan was built for the composed film, so the
            # spliced call-to-action and outro are chapters in their own
            # right and get rendered by whichever window contains them --
            # once each, at the end, exactly as in a single-pass render.
            "compose_segments": compose,
            "export_video": str(segment.path),
            "orientation": orientation,
            "chapter_range": segment.window,
            "local_narration_plan": str(plan),
            "release": False,
            "teaser": False,
        }
        print(f"segment {segment.index}/{len(segments)}: "
              f"chapters {segment.window}")
        code = subprocess.call(
            [sys.executable, "-u", "-c",
             "import json,sys;from two_v_demo import app;"
             "raise SystemExit(app.main(config=json.loads(sys.argv[1])))",
             json.dumps(ticket)],
            cwd=str(ROOT))
        if code != 0 or not segment.path.is_file():
            return {"ok": False, "failed_at": segment.index,
                    "window": segment.window, "returncode": code,
                    "made": [str(s.path) for s in made]}
        made.append(segment)

    concat(made, target)
    seconds = probe_seconds(target)
    if not keep:
        for segment in made:
            segment.path.unlink(missing_ok=True)
    return {"ok": True, "segments": len(made), "path": str(target),
            "seconds": round(seconds, 2)}


def validate_segmented_render() -> None:
    """The windows have to tile the film exactly: no gap, no overlap."""
    target = Path("x.mp4")

    for chapters, per in ((28, 5), (30, 4), (9, 3), (1, 5), (7, 1)):
        segments = plan_segments(chapters, per, target)
        assert segments, (chapters, per)
        assert segments[0].first == 1, (chapters, per)
        assert segments[-1].last == chapters, (chapters, per)
        for before, after in zip(segments, segments[1:]):
            assert after.first == before.last + 1, (
                f"{chapters}/{per}: gap or overlap between "
                f"{before.window} and {after.window}")
        for segment in segments:
            assert segment.first <= segment.last
            assert segment.last - segment.first + 1 <= per
        # Every chapter appears exactly once.
        covered = [c for s in segments for c in range(s.first, s.last + 1)]
        assert covered == list(range(1, chapters + 1)), (chapters, per)
        # Segment files are hidden and distinct, so a half-done run does not
        # look like a set of finished cuts sitting in deliverables.
        names = [s.path.name for s in segments]
        assert len(set(names)) == len(names)
        assert all(n.startswith(".") for n in names)

    try:
        plan_segments(0, 5, target)
    except ValueError:
        pass
    else:
        raise AssertionError("a film with no chapters should not segment")

    # The ticket parser and this module have to agree about what a window is.
    from two_v_demo.app import _chapter_range
    segment = plan_segments(28, 5, target)[1]
    start, stop = _chapter_range({"chapter_range": segment.window})
    assert start == segment.first - 1, (start, segment.first)
    assert stop == segment.last, (stop, segment.last)


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--lesson", default="seed_pitch")
    parser.add_argument("--out", required=False)
    parser.add_argument("--plan", required=False)
    parser.add_argument("--per", type=int, default=5)
    parser.add_argument("--orientation", default="landscape")
    parser.add_argument("--keep", action="store_true",
                        help="leave the segment files on disk")
    parser.add_argument("--validate", action="store_true")
    args = parser.parse_args()

    if args.validate or not args.out:
        validate_segmented_render()
        print("segmented render ok")
        if not args.out:
            raise SystemExit(0)

    result = render(args.lesson, Path(args.out), Path(args.plan),
                    per=args.per, orientation=args.orientation,
                    keep=args.keep)
    print(json.dumps(result, indent=2))
    raise SystemExit(0 if result.get("ok") else 1)
