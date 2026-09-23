"""Everything that has to happen *after* a render, done once and the same way.

A finished film is not a deliverable on its own. What actually gets published
is a small folder: the landscape cut, the phone cut, a set of thumbnails cut
out of the video, and the copy that goes in the box underneath it. Until this
module, all of that was hand work done differently every time, which is how a
film ends up on a platform with a description that disagrees with the film.

So it is generated, from the same lesson the renderer played:

* **The description writes itself from the script.** Every chapter already has
  a title, a promise and its narration; the promise lines are the beats, and
  the chapter list is the timestamps. Nothing is re-typed, so the copy cannot
  drift from the cut.
* **Timestamps are real.** They come from the narration plan the exporter
  wrote -- the actual per-chapter seconds of the finished file -- not from the
  authored durations, which are only the silent timeline.
* **Thumbnails come out of the video**, one per chapter at its midpoint, so
  they are frames that exist rather than a separate render that might not
  match.
* **The plug-in segments are already in the cut.** ``compose_segments`` splices
  the call to action, the outro and the party stinger during the export; this
  module only records which ones went in, so the description can mention them.

Run it after an export::

    py -3.12 -m two_v_demo.release --lesson dome_park

or let the launcher's Render tab do it by ticking "build the release folder".
"""

from __future__ import annotations

import json
import subprocess
from dataclasses import dataclass
from pathlib import Path

from .audio import resolve_executable
from .deliverables import DELIVERABLE_BY_LESSON, OUTPUT_DIR
from .lesson_registry import get_lesson

RELEASE_DIR = Path("deliverables/releases")

HASHTAG_BANK: dict[str, tuple[str, ...]] = {
    "seed_pitch": (
        # The owner's own five come first, in their order.
        "#diy", "#construction", "#geodesicdome", "#realestate", "#tinyhome",
        "#stemcelldome", "#tinyhouse", "#kickstarter", "#modularhousing",
        "#affordablehousing", "#housingcrisis", "#offgrid", "#homestead",
        "#boatbuilding", "#fiberglass", "#timberframe", "#starterhome",
        "#prefab", "#passiveincome", "#landowner",
    ),
    "dome_park": (
        "#domepark", "#geodesicdome", "#tinyhome", "#offgrid", "#homestead",
        "#nomad", "#vanlife", "#rvlife", "#kickstarter", "#opensource",
        "#alternativehousing", "#housingcrisis", "#solar", "#diy",
        "#owneroccupied", "#modularhousing",
    ),
    "byod_snarky": (
        "#bringyourownhome", "#domepark", "#geodesicdome", "#tinyhome",
        "#starterhome", "#affordablehousing", "#housingcrisis", "#renting",
        "#landlord", "#diy", "#offgrid", "#modularhousing", "#kickstarter",
        "#shorts", "#reels", "#mascot",
    ),
    "byod_polished": (
        "#bringyourownhome", "#domepark", "#geodesicdome", "#tinyhome",
        "#starterhome", "#affordablehousing", "#offgrid", "#solar",
        "#modularhousing", "#openbuilding", "#kickstarter", "#housingcrisis",
        "#diy", "#domehome", "#alternativehousing", "#homestead",
    ),
    "byod_deepseek": (
        "#bringyourownhome", "#domepark", "#geodesicdome", "#tinyhome",
        "#starterhome", "#affordablehousing", "#offgrid", "#solar",
        "#modularhousing", "#openbuilding", "#kickstarter", "#housingcrisis",
        "#diy", "#domehome", "#alternativehousing", "#homestead",
    ),
    "_default": (
        "#geodesicdome", "#domebuilding", "#diy", "#woodworking",
        "#opensource", "#tinyhome", "#offgrid", "#homestead",
    ),
}
"""Per-film tags, because a generic set is worth nothing on any platform.

Kept here rather than in the lesson so that copy can be tuned without
touching a film's source, and so a film that has no entry still gets a
sensible default instead of nothing."""


# ----------------------------------------------------------------------
# Timings
# ----------------------------------------------------------------------

def _plan_path(video: Path) -> Path:
    return video.with_name(f"{video.stem}-narration-plan.json")


def chapter_marks(lesson, video: Path) -> list[tuple[float, str, str]]:
    """(start seconds, title, promise) for every chapter of the finished cut.

    Prefers the narration plan the exporter wrote, because narration stretches
    a chapter past its authored duration and a timestamp taken from the script
    would be wrong by minutes by the end of a film.
    """
    plan = _plan_path(video)
    starts: list[float] = []
    if plan.is_file():
        try:
            data = json.loads(plan.read_text(encoding="utf-8"))
            # The exporter records the stretched per-chapter length under
            # "chapter_durations". That is the only honest source for a
            # timestamp: narration pushes every chapter past its authored
            # duration, and the error compounds all the way down the list.
            # "chapter_durations" is the stretched, as-rendered length of
            # every entry on the finished timeline, segments included; it
            # sums to the file's duration. "chapter_starts", when present, is
            # the same information already accumulated.
            recorded = data.get("chapter_starts")
            spans = [float(v) for v in data.get("chapter_durations", [])]
            if recorded and len(recorded) == len(spans):
                starts = [float(v) for v in recorded]
            else:
                cursor = 0.0
                for span in spans:
                    starts.append(cursor)
                    cursor += span
        except (OSError, ValueError, TypeError, AttributeError):
            starts = []
    chapters = lesson.chapters
    if starts and len(starts) != len(chapters):
        # The exporter plays the *composed* lesson -- the film plus the call
        # to action, outro and stingers spliced in -- so its plan has more
        # entries than the lesson does. Rebuild the same composition and the
        # counts line up again, segment titles included.
        try:
            from .segments import compose
            composed = compose(lesson)
            if len(composed.chapters) == len(starts):
                chapters = composed.chapters
        except (ImportError, ValueError):
            pass
    if len(starts) != len(chapters):
        # No plan, or a plan that still does not match: fall back to the
        # authored timeline, which is only right for a silent cut.
        starts, cursor = [], 0.0
        chapters = lesson.chapters
        for chapter in chapters:
            starts.append(cursor)
            cursor += chapter.duration
    return [(starts[i], c.title, c.promise)
            for i, c in enumerate(chapters)]


def stamp(seconds: float) -> str:
    total = int(round(seconds))
    hours, rest = divmod(total, 3600)
    minutes, secs = divmod(rest, 60)
    return (f"{hours}:{minutes:02d}:{secs:02d}" if hours
            else f"{minutes}:{secs:02d}")


# ----------------------------------------------------------------------
# Copy
# ----------------------------------------------------------------------

def _beats(lesson, limit: int = 6) -> list[str]:
    """The promises, which are already one line each and already the point.

    Spread across the film rather than taken off the front. On a
    thirty-nine chapter cut the first six promises are the first fifteen
    per cent of it, so a reader deciding whether to watch saw the opening
    argument and never the ending -- which on the campaign film is the
    price, what the money buys and who it is for.

    The first is always kept, because it is the hook.
    """
    # The spliced call-to-action and outro are not beats of the film. Their
    # promises are generic by design ("Follow the experiments"), and an
    # inclusive spread lands on them every time, so a reader deciding
    # whether to watch got the outro as the last thing they read.
    from .teasers import _segment_slugs

    spliced = _segment_slugs()
    seen: list[str] = []
    for chapter in lesson.chapters:
        if chapter.slug in spliced:
            continue
        line = chapter.promise.strip()
        if line and line not in seen:
            seen.append(line)
    if len(seen) <= limit:
        return seen
    # Even steps through what is left, after the hook, and INCLUSIVE of the
    # last one -- a spread that stops four chapters short still misses the
    # ending, which is where a campaign film keeps its price.
    rest, picks = seen[1:], [seen[0]]
    span = len(rest) - 1
    steps = max(1, limit - 2)
    for index in range(limit - 1):
        picks.append(rest[min(span, int(round(index * span / steps)))])
    # A rounding collision would repeat a line; walk forward instead.
    out: list[str] = []
    for line in picks:
        if line in out:
            for candidate in rest:
                if candidate not in out:
                    line = candidate
                    break
        out.append(line)
    return out[:limit]


def hashtags(lesson_key: str) -> tuple[str, ...]:
    return HASHTAG_BANK.get(lesson_key, HASHTAG_BANK["_default"])


def youtube_description(lesson, video: Path) -> str:
    marks = chapter_marks(lesson, video)
    tags = hashtags(lesson.key)
    lines = [lesson.chapters[0].promise.strip(), ""]
    lines.append(lesson.chapters[0].narration[0].strip())
    lines.extend(["", "In this film:", ""])
    lines.extend(f"- {beat}" for beat in _beats(lesson))
    lines.extend([
        "",
        "Every figure on screen is computed by the model that drew the "
        "picture, and the numbers that argue against the idea are in here "
        "with the ones that argue for it.",
        "",
        "Chapters",
        "",
    ])
    lines.extend(f"{stamp(start)} {title}" for start, title, _ in marks)
    lines.extend(["", " ".join(tags)])
    return "\n".join(lines)


def short_description(lesson, limit: int = 2200) -> str:
    """Facebook: the opening, the beats, the tags. No timestamps."""
    tags = hashtags(lesson.key)
    lines = [lesson.chapters[0].promise.strip(), ""]
    lines.append(lesson.chapters[0].narration[0].strip())
    lines.extend(["", *[f"- {beat}" for beat in _beats(lesson, 4)], ""])
    lines.append(" ".join(tags))
    text = "\n".join(lines)
    return text[:limit].rstrip()


def caption(lesson, limit: int = 2200) -> str:
    """Instagram: one hook, a few lines, tags in a block at the end."""
    tags = hashtags(lesson.key)
    lines = [lesson.chapters[0].promise.strip(), ""]
    lines.extend(f"{beat}" for beat in _beats(lesson, 3))
    lines.extend(["", "Full film in bio.", "", " ".join(tags)])
    return "\n".join(lines)[:limit].rstrip()


POSTSCRIPTS: dict[str, tuple[str, ...]] = {
    "seed_pitch": (
        "A note on how this was made, because somebody always asks.",
        "",
        "These presentations are rendered out of code. I describe what I "
        "want explained, and the argument, the geometry and the figures are "
        "produced from the model that holds them -- no editing timeline, no "
        "compositing, no hand-set captions. Every number you just watched "
        "was read off that model while the frame was being drawn, which is "
        "also why the three chapters that argue against the pitch could not "
        "quietly be left out of it.",
        "",
        "It is not always perfect. It is an extremely reasonable trade for "
        "being able to say what I want rendered and have it come out, and it "
        "is an ongoing project in its own right.",
    ),
}
"""A closing note appended to a film's release copy.

Not part of the film -- this is what goes under the video on the platform,
where a reader has time for it and where the question actually gets asked.
Keyed by lesson, so a film without one is unaffected."""


def description_document(lesson, video: Path) -> str:
    """All three, in one file, so a person copies rather than writes."""
    parts = [
        f"# {lesson.title} -- release copy",
        "",
        f"Generated from `{lesson.key}` and `{video.name}`. Every line here "
        "comes out of the film's own script, so it cannot disagree with the "
        "cut.",
        "",
        "## YouTube",
        "",
        "```",
        youtube_description(lesson, video),
        "```",
        "",
        "## Facebook",
        "",
        "```",
        short_description(lesson),
        "```",
        "",
        "## Instagram",
        "",
        "```",
        caption(lesson),
        "```",
        "",
    ]
    postscript = POSTSCRIPTS.get(lesson.key)
    if postscript:
        parts += ["## Postscript, for any platform", "", "```"]
        parts += list(postscript)
        parts += ["```", ""]
    return "\n".join(parts)


# ----------------------------------------------------------------------
# Thumbnails
# ----------------------------------------------------------------------

def grab_thumbnails(video: Path, out_dir: Path, marks, ffmpeg: str = "",
                    width: int = 1280) -> list[Path]:
    """One frame per chapter, taken out of the finished file.

    Out of the video rather than re-rendered, so a thumbnail is guaranteed to
    be a frame somebody can actually scrub to.
    """
    exe = ffmpeg or resolve_executable("ffmpeg")
    out_dir.mkdir(parents=True, exist_ok=True)
    made: list[Path] = []
    for index, (start, title, _promise) in enumerate(marks, start=1):
        slug = "".join(c if c.isalnum() else "-" for c in title.lower())
        slug = "-".join(part for part in slug.split("-") if part)[:48]
        target = out_dir / f"{index:02d}-{slug}.jpg"
        # A second in, so the frame is the chapter rather than its first
        # frame, which is often mid-transition.
        at = max(0.0, start + 1.5)
        try:
            subprocess.run(
                [exe, "-y", "-loglevel", "error", "-ss", f"{at:.2f}",
                 "-i", str(video), "-frames:v", "1",
                 "-vf", f"scale={width}:-2", str(target)],
                check=True, capture_output=True)
        except (OSError, subprocess.CalledProcessError):
            continue
        if target.is_file():
            made.append(target)
    return made


# ----------------------------------------------------------------------
# The release folder
# ----------------------------------------------------------------------

@dataclass
class Release:
    lesson_key: str
    folder: Path
    video: Path
    portrait: Path | None
    thumbnails: list[Path]
    description: Path
    captions: Path | None

    def summary(self) -> str:
        lines = [f"release: {self.folder}",
                 f"  landscape   {self.video.name}"]
        lines.append(f"  portrait    "
                     f"{self.portrait.name if self.portrait else '(none)'}")
        lines.append(f"  thumbnails  {len(self.thumbnails)}")
        lines.append(f"  description {self.description.name}")
        if self.captions:
            lines.append(f"  captions    {self.captions.name}")
        return "\n".join(lines)


def latest_cut(lesson_key: str, root: Path = OUTPUT_DIR) -> Path:
    """The newest version of this film's deliverable, -v3 beating -v2."""
    item = DELIVERABLE_BY_LESSON.get(lesson_key)
    if item is None:
        raise ValueError(f"{lesson_key!r} has no deliverable entry")
    base = root / item.filename
    stem, suffix = base.stem, base.suffix
    found = sorted(root.glob(f"{stem}*{suffix}"),
                   key=lambda p: p.stat().st_mtime if p.is_file() else 0)
    found = [p for p in found if not p.name.startswith(".")]
    if not found:
        raise FileNotFoundError(f"no rendered cut for {lesson_key!r} in {root}")
    return found[-1]


def newest_version(path: Path) -> Path:
    """The file an append-only export actually wrote for this requested name.

    An export asked for ``film.mp4`` writes ``film-v3.mp4`` when two cuts
    already exist, and says so only on the console. The newest sibling that
    shares the requested stem is the one that just finished. Phone cuts and
    hidden temporaries are not candidates.
    """
    path = Path(path)
    if not path.parent.is_dir():
        return path
    found = [item for item in path.parent.glob(f"{path.stem}*{path.suffix}")
             if not item.name.startswith(".")
             and "-vertical" not in item.stem[len(path.stem):]]
    if not found:
        return path
    return max(found, key=lambda item: item.stat().st_mtime)


def build_release(lesson_key: str, video: Path | None = None,
                  root: Path = RELEASE_DIR, ffmpeg: str = "",
                  portrait: Path | None = None) -> Release:
    """Assemble the publishable folder for one film.

    ``portrait`` names the phone cut when the caller knows it -- the exporter
    does, and the versioned name it gets (``film-vertical-v2``) cannot be
    guessed from the landscape cut's (``film-v3``).
    """
    lesson = get_lesson(lesson_key)
    cut = video or latest_cut(lesson_key)
    folder = root / cut.stem
    folder.mkdir(parents=True, exist_ok=True)

    marks = chapter_marks(lesson, cut)
    thumbs = grab_thumbnails(cut, folder / "thumbnails", marks, ffmpeg)

    description = folder / "description.md"
    description.write_text(description_document(lesson, cut), encoding="utf-8")

    srt = cut.with_suffix(".srt")
    captions = folder / srt.name if srt.is_file() else None
    if captions:
        captions.write_bytes(srt.read_bytes())

    # The phone cut: named by the caller, or found beside the landscape one.
    if portrait is not None and not Path(portrait).is_file():
        portrait = None
    for candidate in (cut.with_name(f"{cut.stem}-portrait{cut.suffix}"),
                      cut.with_name(f"{cut.stem}-vertical{cut.suffix}")):
        if portrait is None and candidate.is_file():
            portrait = candidate

    (folder / "video.txt").write_text(
        f"landscape: {cut.resolve()}\n"
        + (f"portrait:  {portrait.resolve()}\n" if portrait else
           "portrait:  not exported -- re-run with orientation=both\n"),
        encoding="utf-8")
    return Release(lesson_key, folder, cut, portrait, thumbs, description,
                   captions)


def main(argv: list[str] | None = None) -> int:
    import argparse

    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--lesson", required=True)
    parser.add_argument("--video", default="",
                        help="a specific cut; default is the newest")
    parser.add_argument("--ffmpeg", default="")
    args = parser.parse_args(argv)
    release = build_release(args.lesson,
                            Path(args.video) if args.video else None,
                            ffmpeg=args.ffmpeg)
    print(release.summary())
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
