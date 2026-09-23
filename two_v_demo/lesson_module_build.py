"""Building one utility core, on camera, in the order you would build it.

A separate film from the campaign cut, and deliberately so. The campaign
argues that a dome is worth buying; this one assumes you are past that and
shows the work. It is the shop-floor document: what is on the bench, what
happens first, and where the two places are that you do not get a second
chance.

Everything on screen is :mod:`column_build`'s sequence and
:mod:`seed_model`'s component list. The film cannot show a step the process
sheet does not have, because the chapters are generated from it.
"""

from __future__ import annotations

import math

import numpy as np

import column_build
import seed_model
import seed_world

from . import creator_bridge as creator
from . import seed_bridge as seed
from .lessons import Chapter, Lesson
from .render_kit import WorldLabel, clamp, ease_in_out

BUYER = (0.42, 0.75, 1.00)
GREEN = (0.45, 0.92, 0.62)
HOST = (1.00, 0.76, 0.32)
MUTED = (0.74, 0.78, 0.84)
WARN = (1.00, 0.55, 0.45)


def _label(app, point, text, colour) -> None:
    app.world_labels.append(
        WorldLabel(np.asarray(point, dtype=np.float32), text, colour))


def _screen_left(app) -> np.ndarray:
    """The world direction that reads as leftward at this chapter's camera."""
    yaw = math.radians(float(getattr(app, "camera_yaw", 90.0)))
    return np.array([math.sin(yaw), -math.cos(yaw), 0.0])


def _shift(app) -> np.ndarray:
    """Where the core stands, given what the overlay is using.

    A math chapter spends the right of the frame on its worksheet. The core
    is a tall thin object rather than a wide one, so it slides less far than
    the campaign film's dome does -- a sixth of the camera distance rather
    than a fifth, or it walks off the left edge. Checked on stills at 0.17,
    which left it right of the free half's centre; 0.28 centres it.
    """
    chapters = getattr(app, "chapters", None)
    index = getattr(app, "chapter_index", None)
    if not chapters or index is None:
        return np.zeros(3)
    if (chapters[index].overlay or "") != "math":
        return np.zeros(3)
    distance = float(getattr(app, "camera_distance", 6.0))
    return _screen_left(app) * distance * 0.28


def _ground(app, shift) -> None:
    creator.draw(app, creator.environment(), offset=tuple(shift),
                 backdrop=True)


# ----------------------------------------------------------------------
# Scenes
# ----------------------------------------------------------------------

def _core(app, stage: str, partial: float) -> None:
    creator.draw(app, seed.core_stage(stage, partial),
                 offset=tuple(_shift(app)))


def scene_bench(app, opaque, transparent, p: float) -> None:
    """The empty bench and the tools that have to be on it."""
    _ground(app, _shift(app))
    _core(app, "chase", round(clamp(p * 1.4), 2))
    shift = _shift(app)
    tools = column_build.TOOLS
    shown = int(len(tools) * clamp((p - 0.15) / 0.65))
    for index in range(min(shown, 4)):
        _label(app, shift + np.array([0.0, 0.0, 2.7 - index * 0.42]),
               tools[index][0].upper(), MUTED)
    if p > 0.12:
        _label(app, shift + np.array([0.0, 0.0, 3.5]), "ON THE BENCH", BUYER)


def _stage_scene(stage: str):
    """One painter per stage, so a chapter can name its own."""

    def painter(app, opaque, transparent, p: float) -> None:
        _ground(app, _shift(app))
        _core(app, stage, round(ease_in_out(clamp(p / 0.85)), 2))
        steps = column_build.steps(stage)
        index = min(len(steps) - 1, int(clamp(p / 0.85) * len(steps)))
        step = steps[index]
        shift = _shift(app)
        if p > 0.10:
            _label(app, shift + np.array([0.0, 0.0, 3.5]),
                   f"STEP {step.number}", BUYER)
        if p > 0.22:
            _label(app, shift + np.array([0.0, 0.0, 3.05]),
                   f"{step.minutes:.0f} MIN", GREEN)
        if p > 0.80 and step.checkpoint:
            _label(app, shift + np.array([0.0, 0.0, 0.35]), "CHECK", WARN)

    return painter


def scene_stand(app, opaque, transparent, p: float) -> None:
    """The finished core, and where it goes."""
    shift = _shift(app)
    _ground(app, shift)
    _core(app, "close", 1.0)
    if p > 0.45:
        creator.draw(app, seed.pad(),
                     offset=tuple(shift + np.array([0.0, 0.0, -0.75])))
    if p > 0.20:
        _label(app, shift + np.array([0.0, 0.0, 3.6]), "ONE CORE", BUYER)
    if p > 0.60:
        _label(app, shift + np.array([0.0, 0.0, 3.15]),
               f"{column_build.practised_hours():.1f} H", GREEN)
    if p > 0.78:
        _label(app, shift + np.array([0.0, 0.0, 0.3]),
               "EVERY DOME. EVERY SIZE.", HOST)


SCENES: dict = {
    "mb_bench": scene_bench,
    "mb_stand": scene_stand,
}
for _key, _title in column_build.STAGES:
    SCENES[f"mb_{_key}"] = _stage_scene(_key)


# ----------------------------------------------------------------------
# Worksheets
# ----------------------------------------------------------------------

DOT = "  ·  "


def steps_tools() -> tuple[str, ...]:
    out = ["what has to be on the bench before you start.", ""]
    for tool, why in column_build.TOOLS:
        out.append(f"   {tool[:30]:<30}{DOT}{why[:30]}")
    out.extend(["",
                f"   practised {column_build.practised_hours():.1f} h"
                f"{DOT}first one "
                f"{column_build.first_build_hours():.1f} h"])
    return tuple(out)


def steps_for(stage: str):
    def builder() -> tuple[str, ...]:
        title = dict(column_build.STAGES)[stage]
        out = [title.lower() + ".", ""]
        for step in column_build.steps(stage):
            out.append(f"   {step.number}. {step.title[:44]}")
            out.append(f"      {step.minutes:.0f} min{DOT}"
                       f"{', '.join(step.tools)[:40] or 'no tool'}")
            if step.checkpoint:
                out.append(f"      check: {step.checkpoint[:44]}")
        out.append("")
        out.append(f"   stage total{DOT}"
                   f"{column_build.stage_minutes(stage):.0f} min")
        return tuple(out)

    return builder


def steps_materials() -> tuple[str, ...]:
    out = ["everything you buy for one core.", ""]
    for service, what, qty, unit in column_build.MATERIALS:
        out.append(f"   {service:<9}{DOT}{what[:34]:<34}{DOT}"
                   f"{qty:>5.0f} {unit}")
    out.extend(["",
                f"   parts{DOT}${seed_model.column_group().cost:,.0f}"
                f"{DOT}labour{DOT}${column_build.labour_usd():,.0f}"])
    return tuple(out)


# ----------------------------------------------------------------------
# Chapters
# ----------------------------------------------------------------------

def _math(slug, title, promise, narration, steps_, duration, camera, stage):
    return Chapter(slug, "00", title, promise, narration, tuple(steps_),
                   duration, camera, stage, overlay="math")


def _stage_camera(stage: str) -> tuple[float, float, float]:
    """One camera rule for the five stages, walking round as it builds.

    Yaw steps so the face being worked on is toward the lens: water is on
    the west face and power on the east, so the camera has to be on the
    right side of the core to see either of them being fitted.
    """
    yaw = {"chase": 52.0, "drain": 118.0, "water": 150.0,
           "power": 26.0, "close": 60.0}[stage]
    return (yaw, 13.0, 5.2)


STAGE_NARRATION = {
    "chase": (
        "The chase first, and on a bench, upside down.",
        "Four insulated sections, a base flange, and every hole you will "
        "ever need drilled and grommeted while the thing is in pieces at "
        "waist height. That is the whole reason this stage exists: a hole "
        "drilled now takes thirty seconds and a hole drilled later takes an "
        "hour and a hole saw inside a finished core.",
        "Dry-fit it, check it is plumb over the full run, then take it "
        "apart again. The chase is the one part where an eighth of an inch "
        "at the bottom is an inch at the apex, and the apex is where the "
        "seal cap has to seat."),
    "drain": (
        "Drain next, because it is the one you cannot re-route.",
        "A two-inch stack the full height with a trap at its foot. Dry-fit "
        "the whole run and mark every joint across the socket before you "
        "open the cement, because solvent cement gives you about five "
        "seconds and no second chance at alignment.",
        "Bottom to top so gravity is not pulling a fresh joint apart. Then "
        "the floor-port boot, which is the joint the host makes once and "
        "nobody touches again for the life of the pad."),
    "water": (
        "Then water -- and then you prove it, before any electrical part "
        "exists inside this thing.",
        "Manifold at chest height, isolating valve at knee height where "
        "somebody who has never seen the building will look for it, and "
        "both on the opposite face from where the panel is going. Four "
        "capped tails off the manifold, because a dome with no plumbing "
        "still ships with them -- the alternative is opening the chase "
        "later.",
        "Every crimp gets the go/no-go gauge. Every single one, including "
        "the ones you are sure about, because an uncrimped ring will pass a "
        "pressure test and fail in a year.",
        "And then the test. Eighty psi, thirty minutes, a gauge on it. This "
        "is the last moment a leak costs you nothing. After this the panel "
        "goes in, and a leak costs the panel."),
    "power": (
        "Power last, into a core you already know is dry.",
        "Load centre at chest height on the dry face, inlet at the base. "
        "Feeder to the main lugs, strain relief at both ends, and every lug "
        "torqued to the figure printed inside the panel door -- with a "
        "torque screwdriver, not by feel. A loose terminal is how a panel "
        "burns, and it is the failure nobody sees coming.",
        "Four breakers. Outlet ring, lighting, the window unit, and one "
        "spare that exists so the first module somebody snaps on does not "
        "need this door opened again. Label them in writing, on the door, "
        "now -- not from memory in a year."),
    "close": (
        "Close it, prove the cap, stand it up.",
        "Sleeve on the chase, cap on the sleeve, six catches set so the "
        "gasket compresses evenly all the way round. Then open and close it "
        "five times on the bench. If it is stiff down here it is impossible "
        "at the top of a dome in the rain, and that cap is the one thing "
        "between the building and the weather.",
        "Cover on captive fasteners so there is no bag of screws to lose. "
        "Then two people stand it up and it goes onto the pad's service "
        "port as one object -- and every joint you made in the last "
        "thirteen steps is still reachable with that cover off."),
}


def _build_chapters() -> tuple[Chapter, ...]:
    chapters = [
        Chapter(
            "open", "00", "Build one utility core",
            f"{column_build.practised_hours():.1f} hours practised. "
            f"{column_build.first_build_hours():.1f} for your first.",
            ("This is not the pitch. This is the work.",
             "A utility core is the one part of this dome that is identical "
             "in every dome we make -- every size, every fit-out, every "
             "shape -- because the interface it plugs into never changes. "
             "So it is the first thing worth learning to build, and the "
             "first thing worth building a jig for.",
             "Fourteen steps, five stages, about seven hours once you have "
             "done a few. Your first will take closer to seventeen, and "
             "anybody who tells you otherwise has not built one."),
            (), 26.0, (52.0, 13.0, 5.4), "mb_stand"),
        _math("tools", "What has to be on the bench",
              "Nine tools. Two of them are the ones people skip.",
              ("Before anything, the bench.",
               "Nine tools, and two of them are the ones people leave in the "
               "van. The go/no-go gauge for the crimps, because a bad crimp "
               "passes a pressure test. And the torque screwdriver for the "
               "panel, because a terminal that feels tight is not a "
               "terminal that is tight.",
               "Everything else on this list you probably own."),
              steps_tools(), 28.0, (44.0, 14.0, 5.0), "mb_bench"),
    ]
    for key, title in column_build.STAGES:
        chapters.append(_math(
            key, title,
            f"{len(column_build.steps(key))} steps, "
            f"{column_build.stage_minutes(key):.0f} minutes.",
            STAGE_NARRATION[key], steps_for(key)(),
            30.0 if key != "water" else 34.0,
            _stage_camera(key), f"mb_{key}"))
    chapters.append(_math(
        "materials", "Everything you buy for one",
        "Twenty-three lines. None of them exotic.",
        ("And the shopping list, which is the least exciting slide here and "
         "the one people actually screenshot.",
         "Twenty-three lines, and nothing on it is exotic. PEX and crimp "
         "rings, ABS and cement, a load centre and four breakers, four "
         "sections of insulated chase, and a cap. Every one of these is a "
         "thing you can buy this afternoon from somewhere that is already "
         "near you.",
         "Parts come to about fourteen hundred dollars. Labour at shop rate "
         "is two hundred more once you are practised. That is the object "
         "that turns a frame and a platform into a building with services "
         "in it."),
        steps_materials(), 30.0, (60.0, 14.0, 5.4), "mb_stand"))
    chapters.append(Chapter(
        "wrap", "00", "One core, every dome",
        "Build it once. It moves to the next dome when you outgrow this one.",
        ("Last thing, and it is the reason this film is separate from the "
         "others.",
         "This object is not consumed by the dome it goes into. It unbolts "
         "from four joints and a lift, and it goes into the next one. When "
         "somebody outgrows a stem cell and builds the size up, the core "
         "they built on a bench in a weekend goes with them.",
         "Which means the seven hours you just watched is not seven hours "
         "per dome. It is seven hours, once, for as long as you keep "
         "building."),
        (), 26.0, (70.0, 16.0, 6.0), "mb_stand"))
    return tuple(chapters)


CHAPTERS: tuple[Chapter, ...] = tuple(
    Chapter(**{**chapter.__dict__, "number": f"{index:02d}"})
    for index, chapter in enumerate(_build_chapters(), start=1))


ALL_SCREENS = (
    ("tools", steps_tools),
    ("materials", steps_materials),
) + tuple((key, steps_for(key)) for key, _t in column_build.STAGES)


def module_build_report() -> str:
    return column_build.report()


def validate_module_build() -> None:
    """The film cannot show a step the process sheet does not have."""
    column_build.validate_column_build()

    assert len(CHAPTERS) >= 8, len(CHAPTERS)
    slugs = [c.slug for c in CHAPTERS]
    assert len(set(slugs)) == len(slugs), slugs

    for chapter in CHAPTERS:
        assert chapter.stage in SCENES, (chapter.slug, chapter.stage)
        assert chapter.narration, chapter.slug
        assert chapter.duration > 0.0
        assert len(chapter.camera) == 3
        if chapter.overlay == "math":
            assert chapter.equations, chapter.slug

    # Every stage of the process sheet is a chapter, and in order.
    filmed = [c.slug for c in CHAPTERS if c.slug in dict(column_build.STAGES)]
    assert filmed == [k for k, _t in column_build.STAGES], filmed

    # Every scene is reachable.
    staged = {c.stage for c in CHAPTERS}
    assert staged == set(SCENES), set(SCENES) - staged

    # The two spoken hour figures have to be the model's.
    spoken = " ".join(" ".join(c.narration) + " " + c.promise
                      for c in CHAPTERS)
    assert "seven hours" in spoken.lower()
    assert "seventeen" in spoken.lower()
    assert abs(column_build.practised_hours() - 7.0) <= 1.0, (
        f"the voice says seven hours; the sheet says "
        f"{column_build.practised_hours():.1f}")
    assert abs(column_build.first_build_hours() - 17.0) <= 1.5, (
        f"the voice says seventeen; the sheet says "
        f"{column_build.first_build_hours():.1f}")

    # A build film that never mentions the two checkpoints is a tour.
    assert "go/no-go" in spoken.lower()
    assert "torque" in spoken.lower()

    total = sum(c.duration for c in CHAPTERS)
    assert 180.0 <= total <= 600.0, total


MODULE_BUILD_LESSON = Lesson(
    key="module_build",
    brand="THE STEM CELL DOME / SHOP FLOOR",
    title="Build one utility core",
    chapters=CHAPTERS,
    scenes=SCENES,
    selftest=validate_module_build,
    report=module_build_report,
    snapshot_prefix="modulebuild",
    style="teaching",
    voice_rate="+2%",
    label_layout="declutter",
    ground="off",
)


if __name__ == "__main__":
    validate_module_build()
    total = sum(c.duration for c in CHAPTERS)
    print(f"module build ok: {len(CHAPTERS)} chapters, {total / 60.0:.1f} min")
