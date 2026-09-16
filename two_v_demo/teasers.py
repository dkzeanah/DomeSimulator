"""Teasers: a short hype cut for every film.

A film here runs ten to thirty minutes, and almost nobody meets it first. They
meet a clip in a feed that has three seconds to earn the fourth. So every film
gets a teaser built out of itself:

* a **hook** -- the film's sharpest claim, with its number, in the first beat;
* three to five **beats** -- real chapters, each played at pace from the part of
  the chapter where something happens, with a steady push-in;
* a **call to action** -- where the full film is -- over the share scene the
  films already end on;
* **outreach** -- a question to answer, over the same contact card as every
  video's outro.

Nothing is re-drawn and no number is typed. Every beat borrows a chapter's own
painter and camera, and every figure in the words is a token computed by the
code the films use. A film with a hand-written spec in :data:`SPECS` gets its
hook and lines from there; every other film gets a spec built mechanically from
its chapters' own promises, which is honest if plainer.

A teaser is a lesson like any other -- ``teaser_<film>`` in the registry -- so it
exports in both shapes through the normal path, and a phone frame gets the
vertical layout and the fitted camera from :mod:`two_v_demo.frame`.

::

    py -3.12 -m two_v_demo.teasers --list
    py -3.12 -m two_v_demo.teasers --lesson why --stills
    py -3.12 -m two_v_demo.teasers --lesson why                # both shapes, narrated
    py -3.12 -m two_v_demo.teasers --all
"""

from __future__ import annotations

import argparse
import subprocess
import sys
from dataclasses import dataclass
from pathlib import Path

import numpy as np

from .lessons import Chapter, Lesson

PREFIX = "teaser_"
OUTPUT_DIR = Path("deliverables/teasers")
MAX_SECONDS = 58.0
"""Short-form platforms stop at sixty seconds; a teaser stays inside that."""
WINDOW = (0.35, 0.95)
"""The part of a chapter a beat plays: past the set-up, into the payoff."""
VOICE_RATE = "+8%"
BED = "beds/frankenbeat"


@dataclass(frozen=True)
class Beat:
    """One chapter of the film, played at teaser pace."""

    slug: str
    line: str = ""
    """What the voice says. Empty uses the chapter's own promise. May hold tokens."""
    words: str = ""
    """The headline on screen. Empty uses the line."""
    kicker: str = ""
    """The small label over the headline. Empty uses the chapter's title."""
    window: tuple[float, float] = WINDOW
    seconds: float = 3.4
    """The least it runs; the voice sets the real length."""


@dataclass(frozen=True)
class TeaserSpec:
    hook: Beat
    beats: tuple[Beat, ...]
    cta: str = ""
    """What the voice says over the share scene. Empty uses the film kind's call."""
    cta_words: str = ""
    outreach: str = ""
    """What the voice says over the contact card. Empty uses the film kind's ask."""
    outreach_words: str = ""


# The call and the ask depend on what kind of film it is: "every number, worked
# on screen" is true of a masterclass and nonsense after a micro-drama.
CALLS: dict[str, tuple[str, str, str, str]] = {
    "math": ("The full film works every number on screen. It is linked below.",
             "The whole film: every number, worked on screen.",
             "Where would you build one? Tell me, and send this to one person who "
             "should see it.",
             "Where would you build one?"),
    "pitch": ("The whole thing is linked below.",
              "Watch the whole thing.",
              "Send this to one person who can carry it further than I can.",
              "Send it to one person."),
    "story": ("The full episode is linked below.",
              "Watch the episode.",
              "Who should hold the key? Tell me what happens next.",
              "Who should hold the key?"),
    "series": ("The whole series is linked below.",
               "Watch the whole series.",
               "Who should hold the key? Tell me what happens next.",
               "Who should hold the key?"),
    "look": ("The whole lookbook is linked below.",
             "The whole lookbook.",
             "Which room would you live in? Tell me, and send this to someone who would.",
             "Which room would you live in?"),
}


def kind_of(key: str) -> str:
    """Which call a film ends its teaser on."""
    if key == "series":
        return "series"
    if key == "drama":
        return "story"
    if key == "look":
        return "look"
    if key.startswith("hype") or key in ("kick", "kick2"):
        return "pitch"
    return "math"


# ----------------------------------------------------------------------
# Hand-written hooks for the films that carry the argument
# ----------------------------------------------------------------------

SPECS: dict[str, TeaserSpec] = {
    "why": TeaserSpec(
        hook=Beat("round",
                  "Saw a log into two-by-fours and you keep {{tree.sawn_recovery_pct}} percent "
                  "of it. Split it, and you keep {{tree.recovery_pct}}.",
                  "Sawn: {{tree.sawn_recovery_pct}}% kept. Split: {{tree.recovery_pct}}%.",
                  "WHY WEDGES"),
        beats=(
            Beat("split", "One chainsaw. Each section splits {{tree.sectors}} ways, like a cake.",
                 "Split {{tree.sectors}} ways. No sawmill."),
            Beat("pinwheel", "{{frame.panels}} triangles, three sticks each, every end butted "
                             "to the next stick's side.",
                 "{{frame.panels}} panels. Three sticks each."),
            Beat("stick", "A wedge is weaker than a board in bending. So the shell never asks "
                          "it to bend.",
                 "Weaker than a board in bending. The shell never asks it to bend."),
            Beat("dome", "{{dome.trees}} trees, and the frame is done.",
                 "{{dome.trees}} trees. One dome."),
        )),
    "harvest": TeaserSpec(
        hook=Beat("tree", "{{dome.trees}} trees. {{work.days}} days. One dome frame.",
                  kicker="TWO TREES, ALL AT ONCE"),
        beats=(
            Beat("fell"),
            Beat("explode", "Buck it to length, split every section, and the pile is the frame.",
                 "Every section, split.", window=(0.30, 0.90)),
            Beat("worth", "Two weeks of one person keeps {{value.frame_saved}} dollars of "
                          "framing.",
                 "${{value.frame_saved}} kept, against buying the frame."),
        )),
    "all_domes": TeaserSpec(
        hook=Beat("open",
                  "Twelve finished designs, drawn by the tool that builds them.",
                  "Every dome the Creator makes. The tool's own renderer.",
                  "ALL DOMES"),
        beats=(
            Beat("build", "One dome, assembled in the order its own record says "
                          "to build it.",
                 "Foundation, frame, skin, wiring. Step by step."),
            Beat("panels", "Sixteen panel types on the same shell. The mirrors "
                           "reflect a tree line the shader works out per pixel.",
                 "Sixteen skins. Same shell."),
            Beat("fitout", "Roof off: benches, walls, conduit, pipe. All of it "
                           "in the bill of materials.",
                 "The dome is the cheap part of the dome."),
            Beat("random", "Eight drawn at random out of sixteen billion.",
                 "Eight of 16,554,295,296."),
        )),
    "pine_value": TeaserSpec(
        hook=Beat("question", "What is one pine tree worth? On the stump, about "
                              "{{pine.stump_usd}} dollars.",
                  "One pine, on the stump: ${{pine.stump_usd}}.", "THE TWENTY-DOLLAR PINE"),
        beats=(
            Beat("firewood", "Burned, about {{pine.firewood_usd}} dollars.",
                 "As firewood: ${{pine.firewood_usd}}."),
            Beat("lumber", "Sawn into lumber, about {{pine.mill_usd}}.",
                 "As sawn lumber: ${{pine.mill_usd}}."),
            Beat("use_value", "Split into a dome's frame, it stands in for {{pine.use_usd}} "
                              "dollars of framing.",
                 "As a dome's frame: ${{pine.use_usd}}."),
            Beat("ladder", "Same tree. Every rung."),
        )),
    "why_build": TeaserSpec(
        hook=Beat("question", "Why build the frame yourself? By my numbers, {{why.hours}} hours "
                              "of work stand in for {{why.framing_value}} dollars of framing.",
                  "{{why.hours}} hours. ${{why.framing_value}} of framing.",
                  "WHY BUILD THIS WAY"),
        beats=(Beat("chain"), Beat("tree"), Beat("jig"), Beat("why"))),
    "2v": TeaserSpec(
        hook=Beat("welcome", "A whole dome from two lengths of wood: {{dm.long_count}} long, "
                             "{{dm.short_count}} short.",
                  "Two lengths of wood. One dome.", "THE 2V MASTERCLASS"),
        beats=(Beat("triangles"), Beat("project"), Beat("classes"), Beat("cut_list"))),
    "world": TeaserSpec(
        hook=Beat("world_open", "{{dm.presets}} domes, one geometry engine, drawn at true "
                                "relative size.",
                  "{{dm.presets}} domes. One engine.", "EVERY DOME IN THE WORLD"),
        beats=(Beat("show_02"), Beat("show_03"), Beat("framing"), Beat("cladding"))),
    "scratch": TeaserSpec(
        hook=Beat("open", "Every dome in these films starts with one number: {{dm.phi}}.",
                  "It starts with one number: {{dm.phi}}.", "DOME FROM SCRATCH"),
        beats=(Beat("pipeline"), Beat("coordinates"), Beat("project"), Beat("frame"))),
}


# ----------------------------------------------------------------------
# A spec for every other film
# ----------------------------------------------------------------------

def _segment_slugs() -> set[str]:
    from .segments import SEGMENTS
    return {chapter.slug for segment in SEGMENTS.values() for chapter in segment.chapters}


def auto_spec(lesson: Lesson, beats: int = 4) -> TeaserSpec:
    """A plain teaser from the film's own chapters.

    The hook is the first chapter's promise; the beats are spread evenly through
    the rest of the film, preferring a chapter whose numbers arrive on screen,
    because that is where a film proves something. Math screens are passed over:
    a worksheet is the full film's job, not a clip's.
    """
    skip = _segment_slugs()
    candidates = [chapter for chapter in lesson.chapters
                  if chapter.slug not in skip and chapter.overlay != "math"
                  and chapter.promise.strip()]
    if not candidates:
        candidates = [chapter for chapter in lesson.chapters if chapter.slug not in skip] \
            or list(lesson.chapters)
    hook, rest = candidates[0], candidates[1:]
    count = min(beats, len(rest))
    picks = []
    for index in range(count):
        low = int(len(rest) * index / count)
        high = max(low + 1, int(len(rest) * (index + 1) / count))
        bucket = rest[low:high]
        numbered = [chapter for chapter in bucket if chapter.callouts]
        pool = numbered or bucket
        picks.append(pool[len(pool) // 2])
    return TeaserSpec(hook=Beat(hook.slug, kicker=lesson.brand),
                      beats=tuple(Beat(chapter.slug) for chapter in picks))


# ----------------------------------------------------------------------
# Building the teaser lesson
# ----------------------------------------------------------------------

def _resolve(text: str) -> str:
    from .callouts import resolve
    return resolve(text)


def _borrow(lesson: Lesson, chapter: Chapter, window: tuple[float, float]):
    """The chapter's own painter, playing only the window of it the beat wants."""
    painter = lesson.scenes.get(chapter.stage)
    start, end = window

    def paint(app, opaque, transparent, progress: float) -> None:
        local = start + (end - start) * progress
        if painter is not None:
            painter(app, opaque, transparent, local)
        else:
            getattr(app, f"scene_{chapter.stage}")(opaque, transparent, local)
    return paint


def _camera(sources: dict):
    """Each beat's own camera, pushing in: a teaser never stands still."""
    from .scratch_facts import render_settings
    orbit_fov = render_settings().fov_degrees

    def camera(app, chapter, progress, width, height):
        origin = sources.get(chapter.number)
        if origin is not None and origin[2].camera_fn is not None:
            base, (start, end), lesson = origin
            eye, target, fov = lesson.camera_fn(app, base, start + (end - start) * progress,
                                                width, height)
        else:
            eye, target = app.camera()
            fov = orbit_fov
        eye = np.asarray(eye, dtype=np.float32)
        target = np.asarray(target, dtype=np.float32)
        push = 1.06 - 0.10 * float(progress)
        return target + (eye - target) * push, target, fov
    return camera


def estimate_seconds(lesson: Lesson) -> float:
    """How long the narrated teaser will run, from the narrator's measured pace."""
    from .audio import SPEECH_DELAY, TAIL_PADDING
    from .callouts import characters_per_second
    pace = characters_per_second(lesson.voice_rate)
    return sum(max(chapter.duration,
                   SPEECH_DELAY + len(" ".join(chapter.narration)) / pace + TAIL_PADDING)
               for chapter in lesson.chapters)


def _build(source: Lesson, spec: TeaserSpec) -> Lesson:
    from .segments import CTA_SHARE, OUTRO, scene_seg_outro, scene_seg_share
    by_slug = {chapter.slug: chapter for chapter in source.chapters}
    chapters: list[Chapter] = []
    scenes: dict = {}
    sources: dict = {}
    for index, beat in enumerate((spec.hook,) + spec.beats):
        if beat.slug not in by_slug:
            raise ValueError(f"teaser for {source.key!r} borrows {beat.slug!r}, "
                             "which the film does not have")
        base = by_slug[beat.slug]
        line = _resolve(beat.line or base.promise)
        words = _resolve(beat.words) if beat.words else line
        kicker = _resolve(beat.kicker) if beat.kicker else base.title
        number = f"{index + 1:02d}"
        stage = f"tz{index:02d}"
        scenes[stage] = _borrow(source, base, beat.window)
        sources[number] = (base, beat.window, source)
        chapters.append(Chapter(base.slug, number, kicker, words, (line,), (), beat.seconds,
                                base.camera, stage, "hype"))
    count = len(chapters)
    call, call_words, ask, ask_words = CALLS[kind_of(source.key)]
    kicker = {"story": "THE FULL EPISODE", "series": "THE WHOLE SERIES",
              "look": "THE LOOKBOOK"}.get(kind_of(source.key), "THE FULL FILM")
    chapters.append(Chapter("teaser_cta", f"{count + 1:02d}", kicker,
                            _resolve(spec.cta_words or call_words),
                            (_resolve(spec.cta or call),), (), 4.0,
                            CTA_SHARE.chapters[0].camera, "tz_cta", "hype"))
    scenes["tz_cta"] = scene_seg_share
    chapters.append(Chapter("teaser_outreach", f"{count + 2:02d}", "YOUR TURN",
                            _resolve(spec.outreach_words or ask_words),
                            (_resolve(spec.outreach or ask),), (), 5.0,
                            OUTRO.chapters[0].camera, "tz_outreach", "hype"))
    scenes["tz_outreach"] = scene_seg_outro
    return Lesson(key=PREFIX + source.key, brand=source.brand,
                  title=f"{source.title}: the teaser", chapters=tuple(chapters),
                  scenes=scenes, snapshot_prefix=PREFIX + source.key, style="hype",
                  voice_rate=VOICE_RATE, audio_bed=BED, audio_bed_gain=0.12,
                  camera_fn=_camera(sources), label_layout="declutter")


def teaser_lesson(key: str) -> Lesson:
    """The teaser for one film, as a lesson the renderer can play."""
    from .lesson_registry import LESSONS
    if key not in LESSONS:
        raise ValueError(f"no film {key!r} to make a teaser of")
    source = LESSONS[key]
    spec = SPECS.get(key)
    if spec is not None:
        return _build(source, spec)
    spec = auto_spec(source)
    lesson = _build(source, spec)
    # A mechanical spec is trimmed to fit; a hand-written one has to fit as written.
    while estimate_seconds(lesson) > MAX_SECONDS and len(spec.beats) > 2:
        spec = TeaserSpec(spec.hook, spec.beats[:-1])
        lesson = _build(source, spec)
    return lesson


def teaser_keys() -> list[str]:
    """Every film a teaser is made for: all of them, teasers excepted."""
    from .lesson_registry import LESSONS
    return [key for key in LESSONS if not key.startswith(PREFIX)]


def plan_text(key: str) -> str:
    lesson = teaser_lesson(key)
    lines = [f"{key}: {lesson.title} -- about {estimate_seconds(lesson):.0f} s, "
             f"{'hand-written' if key in SPECS else 'from its chapters'}"]
    for chapter in lesson.chapters:
        lines.append(f"  {chapter.number} [{chapter.slug}] {chapter.title.upper()}: "
                     f"{chapter.promise}")
        if chapter.narration[0] != chapter.promise:
            lines.append(f"       voice: {chapter.narration[0]}")
    return "\n".join(lines)


def validate_teasers() -> None:
    from .lesson_registry import LESSONS
    for key in SPECS:
        assert key in LESSONS, f"a teaser spec names {key!r}, which is not a film"
    for key in teaser_keys():
        lesson = teaser_lesson(key)
        lesson.validate()
        slugs = [chapter.slug for chapter in lesson.chapters]
        assert slugs[-2:] == ["teaser_cta", "teaser_outreach"], (key, slugs[-2:])
        assert 4 <= len(slugs) <= 8, (key, len(slugs))
        seconds = estimate_seconds(lesson)
        assert seconds <= MAX_SECONDS, f"the {key} teaser runs about {seconds:.0f} s"
        for chapter in lesson.chapters:
            text = chapter.promise + " ".join(chapter.narration) + chapter.title
            assert "{{" not in text, (key, chapter.number, "an unresolved token")


# ----------------------------------------------------------------------
# Rendering
# ----------------------------------------------------------------------

def output_path(key: str) -> Path:
    from .deliverables import DELIVERABLE_BY_LESSON
    item = DELIVERABLE_BY_LESSON.get(key)
    stem = Path(item.filename).stem if item else key
    return OUTPUT_DIR / f"{stem}-teaser.mp4"


def export(key: str, orientation: str = "both", fps: int = 30) -> int:
    """Narrate and render one teaser, both shapes by default, via the normal export."""
    import launcher_common as lc
    target = output_path(key)
    target.parent.mkdir(parents=True, exist_ok=True)
    lc.write_config("two_v_masterclass", {
        "action": "export_video", "lesson": PREFIX + key, "export_video": str(target),
        "orientation": orientation, "fps": fps,
    })
    return subprocess.call([sys.executable, "two_v_masterclass.py"])


def _stills_worker(key: str, orientation: str, folder: Path) -> int:
    from .app import MasterclassApp
    from .frame import size_for
    from .lessons import chapter_start
    lesson = teaser_lesson(key)
    app = MasterclassApp(size=size_for(orientation), fullscreen=False, hidden=True,
                         lesson=lesson)
    durations = tuple(chapter.duration for chapter in lesson.chapters)
    times = [chapter_start(index, durations, lesson.chapters) + durations[index] * 0.6
             for index in range(len(lesson.chapters))]
    app.render_shots(times, folder / orientation)
    app.pygame.quit()
    return 0


def stills(key: str, folder: Path) -> int:
    """One still per teaser chapter in each shape, to look at before a render."""
    code = 0
    for orientation in ("portrait", "landscape"):
        code |= subprocess.call([sys.executable, "-m", "two_v_demo.teasers", "--lesson", key,
                                 "--stills-worker", orientation, "--out", str(folder)])
    return code


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__,
                                     formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--lesson", default="")
    parser.add_argument("--all", action="store_true")
    parser.add_argument("--list", action="store_true")
    parser.add_argument("--stills", action="store_true")
    parser.add_argument("--orientation", default="both",
                        choices=("both", "portrait", "landscape"))
    parser.add_argument("--fps", type=int, default=30)
    parser.add_argument("--stills-worker", default="")
    parser.add_argument("--out", default="")
    args = parser.parse_args(argv)
    keys = teaser_keys() if args.all or not args.lesson else [args.lesson]
    if args.stills_worker:
        return _stills_worker(args.lesson, args.stills_worker, Path(args.out))
    if args.list:
        print("\n\n".join(plan_text(key) for key in keys))
        return 0
    if args.stills:
        code = 0
        for key in keys:
            folder = Path(args.out or "two_v_demo_output") / f"{PREFIX}{key}"
            code |= stills(key, folder)
            print(f"stills: {folder}")
        return code
    if not args.lesson and not args.all:
        parser.error("name a film with --lesson, or pass --all")
    failures = []
    for key in keys:
        print(f"=== teaser: {key} ===")
        if export(key, args.orientation, args.fps) != 0:
            failures.append(key)
    if failures:
        print("failed:", ", ".join(failures))
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
