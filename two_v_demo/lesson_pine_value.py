"""The $20 Pine: one tree, valued at every rung it can climb.

The author's essay argues that a tree has no single value, only a ladder of them --
standing, burned, sawn, split, built, financed -- and that the rung it reaches depends
on how much of it is kept, and on how much of the chain between the stump and the wall
its owner does. Every figure is a token from :mod:`two_v_demo.pine_value_economics`,
which takes the tree from :data:`wedge_geometry.DEFAULT_LOG` and the two upper rungs
from :mod:`two_v_demo.why_build_economics`, so this film, *Why Build This Way* and the
harvest film cannot disagree about a figure they share.

The author's own figures -- a mill's recovery, splitting's, a sawing rate, a cord
price -- are on a screen before any is used, beside the simulator's checks on them,
and the film closes on the cautions: the mill figure is generous to the mill, the
sawing rate may be high, and the top two rungs are not cash.

The pictures are the essay's pine; a cord with the tree's share of it lit; the
simulator's round section, split against sawn (from :mod:`lesson_wedge_why`); bars for
the gain and for the lumber price; the shell's trees against a mill's; the solved dome;
the ladder itself; the harvest's wedge pile; and *Why Build This Way*'s long chain
against the short one.
"""

from __future__ import annotations

import math
from collections import namedtuple
from pathlib import Path

import numpy as np

from . import house_economics as he
from . import lesson_harvest as lh
from . import lesson_why_build as wbl
from . import pine_value_economics as pv
from . import visuals_forest as vf
from . import wedge_geometry as wg
from . import why_build_economics as wb
from .book_tokens import resolve as _resolve
from .callouts import Callout, Tally
from .lesson_wedge_why import scene_ww_round
from .lessons import Chapter, Lesson
from .render_kit import (AMBER, CYAN, GREEN, MUTED, PURPLE, RED, WHITE, TriangleBatch,
                         WorldLabel, clamp, ease_in_out, smoothstep)
from .visual_objects import rgb, stage_for


def _t(text: str) -> str:
    return _resolve(text, strict=True)


PLINTH = (0.10, 0.15, 0.20, 1.0)
WOOD_LIT = (0.88, 0.67, 0.40, 1.0)
WOOD_DIM = (0.33, 0.29, 0.25, 1.0)
GHOST_RED = (RED[0], RED[1], RED[2], 0.30)
GHOST_GREEN = (GREEN[0], GREEN[1], GREEN[2], 0.30)

TREE_UPF = 0.12
"""Scene units per foot for the row of pines: the seventy-foot tree is 8.4 units."""
SPLIT_X = (-5.0, -2.9)
SAWN_X = (0.6, 2.7, 4.8)
BAR_HEIGHT = 5.0
"""The tallest bar, in scene units; the others are drawn to the same linear scale."""
BAR_X = (-1.7, 1.7)
CORD_UPF = 0.85
"""Scene units per foot for the cord."""
PIECE_FT = 0.5
"""Diameter of one drawn stick of firewood. The picture shows the stack's size; the
solid wood in it is the published figure on the labels, not what this packing gives."""
STEP_WIDTH, STEP_BASE, STEP_RISE = 1.9, 0.55, 0.72
DIM_X = 2.6
"""Where the usable-stem dimension line stands, clear of the crown."""


def _slug(app) -> str:
    chapters = getattr(app, "chapters", None)
    index = getattr(app, "chapter_index", None)
    if not chapters or index is None:
        return ""
    return chapters[index].slug


def _arrivals(app) -> tuple[float, ...]:
    """When each callout on the current chapter arrives, as chapter progress.

    Timed by the same schedule the callouts use -- the voice's own sentence timings
    when a render has them -- so a picture that changes on a figure changes as that
    figure lands on screen.
    """
    from .callouts import schedule, speech_timings
    chapters = getattr(app, "chapters", None)
    index = getattr(app, "chapter_index", None)
    if not chapters or index is None:
        return ()
    chapter = chapters[index]
    durations = getattr(app, "chapter_durations", None)
    seconds = durations[index] if durations else chapter.duration
    speech = getattr(app, "speech_durations", None)
    clips = getattr(app, "speech_clips", None)
    timings = speech_timings(clips[index]) if clips else ()
    placed = schedule(chapter, seconds, speech[index] if speech else None,
                      getattr(app, "speak_promise", False), timings,
                      getattr(getattr(app, "lesson", None), "voice_rate", None))
    return tuple(item.start / max(1e-6, seconds) for item in placed)


def _at(arrivals: tuple[float, ...], index: int, fallback: float) -> float:
    return arrivals[index] if index < len(arrivals) else fallback


def _label(app, point, text: str, colour) -> None:
    app.world_labels.append(WorldLabel(np.asarray(point, dtype=float), text,
                                       rgb(colour)))


def _pine(app, opaque, transparent, origin=(0.0, 0.0, 0.0), scale: float = 1.0,
          units: float = lh.UPF) -> None:
    """The essay's pine, standing: the forest object's tree drawn to
    :func:`pine_value_economics.essay_plan`, not the book's smaller one."""
    stage = stage_for(app, opaque, transparent, origin=origin, scale=scale)
    solid, clear = TriangleBatch(), TriangleBatch()
    vf._tree(solid, clear, stage, 0.0, 0.0, units, False, plan=pv.essay_plan())
    stage.splice(solid)
    stage.splice(clear, transparent=True)


LABELS = {
    "stem": _t("{{pine.length_ft}} FT OF USABLE STEM"),
    "butt": _t("{{pine.butt_in}} IN AT THE BUTT"),
    "top": _t("{{pine.top_in}} IN AT THE TOP"),
    "cord": _t("ONE CORD: {{pine.cord_ft3}} CU FT STACKED"),
    "share": _t("THIS PINE: {{pine.cords}} CORD"),
    "stem_bf": _t("{{pine.solid_bf}} BD FT IN THE STEM"),
    "split_name": _t("SPLIT, {{pine.wedge_pct}}%"),
    "sawn_name": _t("SAWN, {{pine.mill_pct}}%"),
    "split_kept": _t("{{pine.wedge_bf}} BD FT"),
    "sawn_kept": _t("{{pine.mill_bf}} BD FT"),
    "split_lost": _t("{{pine.wedge_lost_bf}} LEFT BEHIND"),
    "sawn_lost": _t("{{pine.mill_lost_bf}} LEFT BEHIND"),
    "price": _t("AT ${{pine.usd_per_bf}} A BOARD FOOT"),
    "split_usd": _t("${{pine.wedge_usd}}"),
    "sawn_usd": _t("${{pine.mill_usd}}"),
    "gain_usd": _t("+${{pine.value_gain}}"),
    "split_wood": _t("SPLIT, {{pine.wedge_bf}} BD FT"),
    "sawn_wood": _t("SAWN, {{pine.mill_bf}} BD FT"),
    "trees_split": _t("SPLIT: {{pine.shell_trees}} TREES"),
    "trees_sawn": _t("SAWN: {{pine.trees_equiv}} TREES"),
    "trees_bf": _t("{{pine.shell_bf}} BD FT"),
    "trees_same": _t("THE SAME {{pine.shell_bf}} BD FT"),
}

RUNGS = (
    ("pine", "STANDING", "{{pine.stump_usd}}", MUTED),
    ("flame", "FIREWOOD", "{{pine.firewood_usd}}", RED),
    ("board", "SAWN LUMBER", "{{pine.mill_usd}}", AMBER),
    ("split", "SPLIT STOCK", "{{pine.wedge_usd}}", GREEN),
    ("dome", "STRUCTURE", "{{pine.use_usd}}", CYAN),
    ("calendar", "FINANCED", "{{pine.financed_usd}}", PURPLE),
)
"""The ladder, bottom to top: pictogram, name, value token, colour."""


# ----------------------------------------------------------------------
# Scenes
# ----------------------------------------------------------------------

def scene_pv_pine(app, opaque, transparent, p: float) -> None:
    """The essay's pine, standing; in the stem chapter, its usable stem measured."""
    _pine(app, opaque, transparent)
    if _slug(app) != "stem":
        return
    bottom = vf._d("stump_ft") * lh.UPF
    top = vf.usable_top_ft(pv.essay_plan()) * lh.UPF
    grow = ease_in_out(clamp((p - 0.04) / 0.30))
    if grow <= 0.0:
        return
    reach = bottom + (top - bottom) * grow
    opaque.cylinder(np.array([DIM_X, 0.0, bottom]), np.array([DIM_X, 0.0, reach]),
                    0.05, AMBER, 6)
    for z in (bottom, reach):
        opaque.cylinder(np.array([DIM_X - 0.3, 0.0, z]),
                        np.array([DIM_X + 0.3, 0.0, z]), 0.05, AMBER, 6)
    if grow > 0.95:
        # Above the line, not beside it: beside it runs under the column on the right.
        _label(app, (DIM_X - 0.8, 0.0, top + 1.1), LABELS["stem"], AMBER)
        _label(app, (DIM_X + 2.0, 0.0, bottom + 0.2), LABELS["butt"], WHITE)
        _label(app, (-2.6, 0.0, top), LABELS["top"], WHITE)


def scene_pv_cord(app, opaque, transparent, p: float) -> None:
    """A cord drawn to its published size, stacked, with this tree's share of it lit."""
    t = pv.pine()
    arrivals = _arrivals(app)
    lit_at, fire_at = _at(arrivals, 2, 0.5), _at(arrivals, 4, 0.7)
    length, depth, height = (d * CORD_UPF for d in pv.CORD_FT)
    x0, y0, y1 = -length * 0.5, -depth * 0.5, depth * 0.5
    corners = [np.array([x, y, z]) for x in (x0, -x0) for y in (y0, y1)
               for z in (0.0, height)]
    for a in range(8):
        for b in range(a + 1, 8):
            if int(np.sum(np.abs(corners[a] - corners[b]) > 1e-9)) == 1:
                opaque.cylinder(corners[a], corners[b], 0.03, MUTED, 6)
    columns = int(round(pv.CORD_FT[0] / PIECE_FT))
    rows = int(round(pv.CORD_FT[2] / PIECE_FT))
    total = columns * rows
    step = PIECE_FT * CORD_UPF
    stacked = ease_in_out(clamp((p - 0.03) / 0.34)) * total
    share = t.cords * total
    light = smoothstep(clamp((p - lit_at + 0.02) / 0.05))
    for column in range(columns):
        for row in range(rows):
            index = column * rows + row
            if index >= stacked:
                continue
            x = x0 + (column + 0.5) * step
            z = (row + 0.5) * step
            colour = WOOD_LIT if index < share and light > 0.5 else WOOD_DIM
            opaque.cylinder(np.array([x, y0, z]), np.array([x, y1, z]),
                            step * 0.47, colour, 10)
            _front_disc(opaque, np.array([x, y0 - 0.004, z]), step * 0.47, colour)
    if stacked >= total * 0.98:
        _label(app, (length * 0.18, 0.0, height + 0.75), LABELS["cord"], MUTED)
    lit_centre = x0 + (share / rows) * step * 0.5
    if light > 0.5:
        _label(app, (lit_centre, y0, -0.55), LABELS["share"], AMBER)
    fire = smoothstep(clamp((p - fire_at + 0.02) / 0.05))
    if fire > 0.0:
        stage = stage_for(app, opaque, transparent)
        stage.icon(np.array([lit_centre, 0.0, height + 1.0]), "flame", 84.0, None,
                   fire, 0.0)


def _front_disc(batch, centre, radius: float, colour, sides: int = 14) -> None:
    """A whole disc facing the camera on -Y.

    Laid over the front of each stick of firewood, because the render kit's cylinder
    caps its ends with a fan that leaves two slices of every cap open.
    """
    normal = np.array([0.0, -1.0, 0.0])
    ring = [centre + radius * np.array([math.cos(a), 0.0, math.sin(a)])
            for a in (math.tau * index / sides for index in range(sides))]
    for index in range(sides):
        batch.triangle(centre, ring[index], ring[(index + 1) % sides], colour, normal)


def _bar(batch, x: float, low: float, high: float, colour) -> None:
    if high - low > 1e-4:
        batch.box((x, 0.0, (low + high) * 0.5), (1.7, 1.4, high - low), colour)


def scene_pv_bars(app, opaque, transparent, p: float) -> None:
    """Two bars to one linear scale: the wood each way kept (gain), or its price (lumber)."""
    t = pv.pine()
    opaque.box((0.0, 0.0, -0.05), (7.2, 2.4, 0.1), PLINTH)
    grow = ease_in_out(clamp((p - 0.03) / 0.25))
    split_x, sawn_x = BAR_X
    if _slug(app) == "lumber":
        unit = BAR_HEIGHT / t.wedge_usd
        split_top, sawn_top = t.wedge_usd * unit * grow, t.mill_usd * unit * grow
        _bar(opaque, split_x, 0.0, split_top, GREEN)
        _bar(opaque, sawn_x, 0.0, sawn_top, AMBER)
        arrivals = _arrivals(app)
        gap = smoothstep(clamp((p - _at(arrivals, 4, 0.6) + 0.02) / 0.05))
        if gap > 0.0:
            _bar(transparent, sawn_x, sawn_top, sawn_top + (split_top - sawn_top) * gap,
                 GHOST_GREEN)
        if grow > 0.9:
            _label(app, (split_x, 0.0, split_top * 0.5), LABELS["split_usd"], WHITE)
            _label(app, (sawn_x, 0.0, sawn_top * 0.5), LABELS["sawn_usd"], WHITE)
            _label(app, (split_x, 0.0, -0.55), LABELS["split_wood"], GREEN)
            _label(app, (sawn_x, 0.0, -0.55), LABELS["sawn_wood"], AMBER)
            _label(app, (0.0, 0.0, BAR_HEIGHT + 0.7), LABELS["price"], MUTED)
        if gap > 0.9:
            _label(app, (sawn_x, 0.0, (sawn_top + split_top) * 0.5), LABELS["gain_usd"],
                   GREEN)
        return
    whole = BAR_HEIGHT * grow
    for x, share, colour, name, kept_label, lost_label in (
            (split_x, t.wedge, GREEN, "split_name", "split_kept", "split_lost"),
            (sawn_x, t.mill, AMBER, "sawn_name", "sawn_kept", "sawn_lost")):
        kept = whole * share
        _bar(opaque, x, 0.0, kept, colour)
        _bar(transparent, x, kept, whole, GHOST_RED)
        if grow > 0.9:
            _label(app, (x, 0.0, kept * 0.5), LABELS[kept_label], WHITE)
            _label(app, (x, 0.0, (kept + whole) * 0.5), LABELS[lost_label], RED)
            _label(app, (x, 0.0, -0.55), LABELS[name], colour)
    if grow > 0.9:
        _label(app, (0.0, 0.0, BAR_HEIGHT + 0.7), LABELS["stem_bf"], MUTED)


def scene_pv_trees(app, opaque, transparent, p: float) -> None:
    """The shell's trees, split, against the trees a mill would need for the same wood."""
    height = vf._d("tip_ft") * TREE_UPF
    for x in SPLIT_X:
        _pine(app, opaque, transparent, origin=(x, 0.0, 0.0), units=TREE_UPF)
    split_centre = sum(SPLIT_X) / len(SPLIT_X)
    _label(app, (split_centre, 0.0, height + 0.9), LABELS["trees_split"], GREEN)
    _label(app, (split_centre, 0.0, -0.7), LABELS["trees_bf"], WHITE)
    arrivals = _arrivals(app)
    rise = ease_in_out(clamp((p - _at(arrivals, 3, 0.55) + 0.02) / 0.08))
    if rise <= 0.0:
        return
    for x in SAWN_X:
        _pine(app, opaque, transparent, origin=(x, 0.0, 0.0), scale=rise,
              units=TREE_UPF)
    if rise > 0.9:
        sawn_centre = sum(SAWN_X) / len(SAWN_X)
        _label(app, (sawn_centre, 0.0, height + 0.9), LABELS["trees_sawn"], AMBER)
        _label(app, (sawn_centre, 0.0, -0.7), LABELS["trees_same"], WHITE)


def scene_pv_ladder(app, opaque, transparent, p: float) -> None:
    """The ladder: one step per rung, rising left to right, each with its pictogram.

    The steps rise evenly because the ladder is an order, not a chart; the values are
    on the steps and on the column beside them. In the ladder chapter each step rises
    as its figure lands; after that the whole ladder stands.
    """
    stage = stage_for(app, opaque, transparent)
    count = len(RUNGS)
    opaque.box((0.0, 0.0, -0.05), (count * STEP_WIDTH + 0.6, 2.4, 0.1), PLINTH)
    climbing = _slug(app) == "ladder"
    arrivals = _arrivals(app) if climbing else ()
    for index, (icon, name, token, colour) in enumerate(RUNGS):
        x = (index - (count - 1) * 0.5) * STEP_WIDTH
        full = STEP_BASE + STEP_RISE * index
        grow = 1.0
        if climbing:
            start = _at(arrivals, index, 0.08 + 0.12 * index)
            grow = ease_in_out(clamp((p - start + 0.03) / 0.05))
        if grow <= 0.0:
            continue
        top = full * grow
        opaque.box((x, 0.0, top * 0.5), (STEP_WIDTH * 0.9, 1.6, top), colour)
        if grow > 0.6:
            shown = clamp((grow - 0.6) / 0.4)
            stage.icon(np.array([x, 0.0, top + 0.75]), icon, 58.0, None, shown, 0.0)
            _label(app, (x, 0.0, top + 1.75), f"{name}\n${_t(token)}", colour)


SCENES = {
    "pv_pine": scene_pv_pine,
    "pv_cord": scene_pv_cord,
    "pv_bars": scene_pv_bars,
    "pv_trees": scene_pv_trees,
    "pv_ladder": scene_pv_ladder,
    "ww_round": scene_ww_round,
    "hv_dome": lh.scene_hv_dome,
    "hv_harvest": lh.scene_hv_harvest,
    "wb_chain": wbl.scene_wb_chain,
}


# ----------------------------------------------------------------------
# Camera
# ----------------------------------------------------------------------

_As = namedtuple("_As", "slug stage overlay")

# Each fixed stage: (target, yaw, pitch, distance, field of view, and how far to slide
# sideways for a worksheet, for a tally, and for neither). The picture's middle is
# aimed at the middle of the space the headline, the worksheet and the column leave;
# with neither, the pine moves right, clear of the card on the left.
_FRAMES = {
    "pv_pine": ((0.0, 0.0, 4.4), -90.0, 6.0, 36.0, 44.0, 11.4, 2.0, -3.5),
    "pv_cord": ((0.0, 0.0, 1.0), -112.0, 18.0, 13.0, 44.0, 0.0, 3.2, 0.0),
    "pv_bars": ((0.0, 0.0, 0.8), -90.0, 10.0, 14.0, 44.0, 0.0, 2.8, 0.0),
    "pv_trees": ((-0.1, 0.0, 1.5), -90.0, 6.0, 23.0, 44.0, 0.0, 4.5, 0.0),
    "pv_ladder": ((0.0, 0.0, 1.1), -90.0, 10.0, 17.0, 44.0, 0.0, 4.9, 0.0),
    # The round section's discs face +Y, so this one camera stands on +Y.
    "ww_round": ((0.0, 0.0, 0.8), 90.0, 6.0, 24.0, 44.0, 0.0, 6.3, 0.0),
}


def _dome_camera(p: float, overlay: str | None):
    """The harvest's walk round the dome, aimed lower so the dome clears the headline
    and slid further so it clears the column."""
    radius = lh._dome_radius()
    target = lh.DOME_ORIGIN + np.array([0.0, 0.0, radius * 0.25])
    eye = lh._orbit(target, -62.0 + 48.0 * ease_in_out(p), 20.0, radius * 4.4)
    eye, target = lh._slide(eye, target, radius * (1.27 if overlay == "math" else 0.85))
    return eye, target, 42.0


def pine_camera(app, chapter, progress: float, width: int, height: int):
    """(eye, target, field of view): borrowed cameras for borrowed scenes, and a
    fixed stage for each of this film's own."""
    p = clamp(progress)
    stage = chapter.stage
    tally = any(isinstance(entry, Tally) for entry in chapter.callouts)
    if stage == "hv_dome":
        return _dome_camera(p, chapter.overlay)
    if stage == "hv_harvest":
        eye, target, fov = lh.harvest_camera(
            app, _As("cost", "hv_harvest", chapter.overlay), p, width, height)
        eye, target = lh._slide(eye, target, 3.0 if tally else 0.0)
        return eye, target, fov
    if stage == "wb_chain":
        return wbl.why_camera(app, _As(chapter.slug, "wb_chain", chapter.overlay),
                              p, width, height)
    target, yaw, pitch, distance, fov, for_math, for_tally, for_none = _FRAMES[stage]
    target = np.array(target, dtype=np.float64)
    eye = lh._orbit(target, yaw + 8.0 * (p - 0.5), pitch, distance)
    amount = for_math if chapter.overlay == "math" else (for_tally if tally else
                                                         for_none)
    eye, target = lh._slide(eye, target, amount)
    return eye, target, fov


# ----------------------------------------------------------------------
# Chapters
# ----------------------------------------------------------------------

def _c(slug: str, title: str, promise: str, narration: str, duration: float,
       stage: str, overlay: str | None = None,
       equations: tuple[str, ...] = (), callouts: tuple = ()) -> Chapter:
    spoken = _t(narration)
    from .audio import SPEECH_DELAY, TAIL_PADDING
    from .callouts import characters_per_second
    estimated = SPEECH_DELAY + len(spoken) / characters_per_second() + TAIL_PADDING
    return Chapter(slug, "00", title, _t(promise), (spoken,), equations,
                   max(duration, round(estimated, 1)), (0.0, 20.0, 20.0), stage,
                   overlay, callouts)


_AUTHORED: tuple[Chapter, ...] = (
    _c("question", "What is a pine worth",
       "Not one price. A ladder of them.",
       "What is a pine tree worth? Ask a timber buyer, a firewood dealer, a sawmill "
       "and a builder, and each gives a different answer, because a tree has no "
       "single value. It has a ladder of them, and the rung it reaches depends on "
       "what somebody does to it, and on how much of it they keep. Take one "
       "representative pine, the log the wedge film is built on: "
       "{{pine.length_ft}} feet of usable stem, "
       "{{pine.butt_in}} inches across at the butt and {{pine.top_in}} at the top. "
       "Let us climb its ladder, one rung at a time.",
       22.0, "pv_pine",
       callouts=(
           Callout("{{pine.length_ft}} ft", unit="of usable stem",
                   note="{{pine.butt_in}} in at the butt, {{pine.top_in}} in at the top",
                   icon="pine", cue="{{pine.length_ft}} feet of usable stem",
                   slot="left", hold=None),
       )),
    _c("sources", "What the ladder rests on",
       "Measured, published and mine, kept apart.",
       "Every rung rests on a figure, so here they all are before any of them is "
       "used. The tree is my representative pine, the wedge film's own log. Some "
       "figures are "
       "published: a sawmill's price for common pine, what standing pine sells for, "
       "and the size of a cord. Some are mine: a mill keeps {{pine.mill_pct}} "
       "percent of the stem as the lumber it wants, splitting keeps "
       "{{pine.wedge_pct}}, and the sawing rate and the cord price are mine too. The "
       "simulator checks both recoveries. Sawn into two by fours, this log keeps "
       "only {{pine.sawn_model_pct}} percent; split, it keeps {{pine.kerf_only_pct}} "
       "before any trimming. So the mill gets the benefit of the doubt, and the "
       "wedge gets no more than the model allows.",
       30.0, "pv_pine", overlay="math", equations=pv.source_lines()),
    _c("stem", "The stem, in board feet",
       "{{pine.solid_bf}} board feet, and about ${{pine.stump_usd}} standing.",
       "The usable stem is a long, tapering cone: {{pine.solid_ft3}} cubic feet of "
       "solid wood. A cubic foot holds {{pine.bf_per_ft3}} board feet, so that is "
       "{{pine.solid_bf}} board feet, the most that any method could ever get out of "
       "it. Green, it weighs about {{pine.stump_tons}} tons, and at the published "
       "stumpage of ${{pine.stumpage}} a ton, it sells standing for about "
       "{{pine.stump_usd}} dollars. That is the twenty-dollar pine. Every rung above "
       "this one is something somebody does to it.",
       26.0, "pv_pine",
       callouts=(
           Tally((
               Callout("{{pine.solid_ft3}} cu ft", unit="of solid wood",
                       cue="{{pine.solid_ft3}} cubic feet"),
               Callout("{{pine.bf_per_ft3}}", unit="board feet a cu ft", op="×",
                       cue="holds {{pine.bf_per_ft3}} board feet"),
               Callout("{{pine.solid_bf}} bd ft", unit="in the stem", op="=",
                       tone="total", cue="that is {{pine.solid_bf}} board feet"),
               Callout("${{pine.stump_usd}}", unit="standing, on the stump", op="·",
                       tone="total", cue="sells standing for about"),
           ), title="the stem", slot="right", icon="pine"),
       )),
    _c("firewood", "Burned, it is heat",
       "Burned, it is worth its heat: ${{pine.firewood_usd}}.",
       "The first rung up is fire. This stem is {{pine.solid_ft3}} cubic feet of "
       "solid wood. A cord is {{pine.cord_height_ft}} feet high, "
       "{{pine.cord_depth_ft}} deep and {{pine.cord_length_ft}} long, "
       "{{pine.cord_ft3}} cubic feet stacked, but air fills the gaps, and only about "
       "{{pine.cord_solid_ft3}} of those cubic feet are wood. So the stem makes "
       "{{pine.cords}} of a cord. At {{pine.cord_usd}} dollars a cord picked up, that "
       "is {{pine.firewood_usd}} dollars, or about {{pine.firewood_delivered_usd}} "
       "delivered. That values the tree for its heat. Every rung above this one "
       "values it for its shape.",
       28.0, "pv_cord",
       callouts=(
           Tally((
               Callout("{{pine.solid_ft3}} cu ft", unit="in the stem",
                       cue="This stem is {{pine.solid_ft3}}"),
               Callout("{{pine.cord_solid_ft3}} cu ft", unit="of wood in a cord",
                       op="÷", cue="only about {{pine.cord_solid_ft3}}"),
               Callout("{{pine.cords}}", unit="of a cord", op="=",
                       cue="makes {{pine.cords}} of a cord"),
               Callout("${{pine.cord_usd}}", unit="a cord, picked up", op="×",
                       cue="At {{pine.cord_usd}} dollars a cord"),
               Callout("${{pine.firewood_usd}}", unit="as firewood", op="=",
                       tone="total", cue="is {{pine.firewood_usd}} dollars"),
               Callout("${{pine.firewood_delivered_usd}}", unit="delivered", op="·",
                       tone="note",
                       cue="about {{pine.firewood_delivered_usd}} delivered"),
           ), title="as firewood", slot="right", icon="flame"),
       )),
    _c("recovery", "Split, not sawn",
       "A mill wants rectangles. A wedge takes the log as it is.",
       "Now shape. A sawmill has to turn a round log into rectangles, and everything "
       "outside them leaves as slabs, edgings and sawdust. The picture is the "
       "simulator's, packing this log with two by fours, and it keeps only "
       "{{pine.sawn_model_pct}} percent. A good mill cutting mixed sizes does better, "
       "so I give it {{pine.mill_pct}} percent. Splitting follows the round log "
       "instead of fighting it. From the same stem it keeps {{pine.wedge_pct}} "
       "percent, {{pine.wedge_bf}} board feet, where the mill keeps "
       "{{pine.mill_bf}}. That is {{pine.extra_bf}} more board feet of usable wood "
       "from one tree, because the corners of a log are not bad wood. They are only "
       "not rectangular.",
       32.0, "ww_round",
       callouts=(
           Tally((
               Callout("{{pine.solid_bf}} bd ft", unit="in the stem",
                       cue="From the same stem"),
               Callout("{{pine.wedge_share}}", unit="kept by splitting", op="×",
                       cue="it keeps {{pine.wedge_pct}} percent"),
               Callout("{{pine.wedge_bf}} bd ft", unit="split", op="=",
                       cue="{{pine.wedge_bf}} board feet"),
               Callout("{{pine.mill_bf}} bd ft", unit="sawn, at {{pine.mill_pct}}%",
                       op="−", cue="where the mill keeps"),
               Callout("{{pine.extra_bf}} bd ft", unit="more, from one tree", op="=",
                       tone="total", cue="That is {{pine.extra_bf}} more"),
           ), title="the same stem, two ways", slot="right", icon="split"),
       )),
    _c("gain", "Almost half as much again",
       "{{pine.gain_pct}}% more wood, {{pine.waste_cut_pct}}% less thrown away.",
       "Put the two recoveries side by side. {{pine.wedge_pct}} percent over "
       "{{pine.mill_pct}} is {{pine.gain_ratio}}, so splitting gets "
       "{{pine.gain_pct}} percent more usable wood out of the same tree. Now look at "
       "what is left behind. The mill leaves {{pine.mill_waste_pct}} percent of the "
       "stem, {{pine.mill_lost_bf}} board feet of it. Splitting leaves "
       "{{pine.wedge_waste_pct}} percent, {{pine.wedge_lost_bf}}. That is "
       "{{pine.waste_cut_pct}} percent less of the tree thrown away, from the same "
       "tree, with the same saw.",
       26.0, "pv_bars",
       callouts=(
           Tally((
               Callout("{{pine.wedge_pct}}%", unit="kept by splitting",
                       cue="{{pine.wedge_pct}} percent over"),
               Callout("{{pine.mill_pct}}%", unit="kept by a mill", op="÷",
                       cue="over {{pine.mill_pct}} is"),
               Callout("{{pine.gain_ratio}}", unit="times the wood", op="=",
                       tone="total", cue="is {{pine.gain_ratio}}"),
               Callout("+{{pine.gain_pct}}%", unit="more usable wood", op="·",
                       tone="note", cue="{{pine.gain_pct}} percent more"),
               Callout("{{pine.waste_cut_pct}}%", unit="less left behind", op="·",
                       tone="total", cue="That is {{pine.waste_cut_pct}} percent less"),
           ), title="the gain", slot="right", icon="split"),
       )),
    _c("three_trees", "The same wood from fewer trees",
       "{{pine.shell_trees}} trees split give as much wood as {{pine.trees_equiv}} "
       "sawn.",
       "A {{why.sqft}} square foot shell needs {{pine.shell_trees}} of these trees "
       "felled. Each one, split, gives {{pine.wedge_bf}} board feet, so the pair "
       "gives {{pine.shell_bf}}. A mill keeping {{pine.mill_pct}} percent gets "
       "{{pine.mill_bf}} from a tree, so to match the pair it would need "
       "{{pine.trees_equiv}} trees. Put the other way round, the mill's way needs "
       "almost half as many trees again, and a tree not cut is a tree still "
       "standing, or a tree left for the next building.",
       26.0, "pv_trees",
       callouts=(
           Tally((
               Callout("{{pine.wedge_bf}} bd ft", unit="split, one tree",
                       cue="gives {{pine.wedge_bf}} board feet"),
               Callout("{{pine.shell_trees}}", unit="trees", op="×",
                       cue="so the pair gives"),
               Callout("{{pine.shell_bf}} bd ft", unit="from the pair", op="=",
                       tone="total", cue="the pair gives {{pine.shell_bf}}"),
               Callout("{{pine.mill_bf}} bd ft", unit="sawn, one tree", op="÷",
                       cue="gets {{pine.mill_bf}} from a tree"),
               Callout("{{pine.trees_equiv}}", unit="trees, sawn", op="=",
                       tone="total", cue="need {{pine.trees_equiv}} trees"),
           ), title="the pair's wood", slot="right", icon="pine"),
       )),
    _c("lumber", "Priced as lumber",
       "Priced as wood, splitting is worth ${{pine.value_gain}} more a tree.",
       "Now put a price on the wood. The split yield, {{pine.wedge_bf}} board feet, "
       "at one sawmill's list price for common pine of ${{pine.usd_per_bf}} a board "
       "foot, is worth {{pine.wedge_usd}} dollars. The sawn yield, {{pine.mill_bf}} "
       "board feet, is worth {{pine.mill_usd}}. That is {{pine.value_gain}} dollars "
       "more from one tree, and {{pine.value_gain_shell}} from the shell's "
       "{{pine.shell_trees}}. And "
       "the sawn path still has to pay for the sawing: at my rate of "
       "${{pine.milling_usd_per_bf}} a board foot, about {{pine.milling_usd}} dollars "
       "for this tree.",
       28.0, "pv_bars",
       callouts=(
           Tally((
               Callout("{{pine.wedge_bf}} bd ft", unit="split",
                       cue="The split yield"),
               Callout("${{pine.usd_per_bf}}", unit="a board foot", op="×",
                       cue="list price for common pine"),
               Callout("${{pine.wedge_usd}}", unit="as split stock", op="=",
                       cue="is worth {{pine.wedge_usd}} dollars"),
               Callout("${{pine.mill_usd}}", unit="as sawn lumber", op="−",
                       cue="is worth {{pine.mill_usd}}"),
               Callout("${{pine.value_gain}}", unit="more, one tree", op="=",
                       tone="total", cue="That is {{pine.value_gain}} dollars more"),
               Callout("${{pine.value_gain_shell}}", unit="more from the pair", op="·",
                       tone="total", cue="and {{pine.value_gain_shell}} from"),
               Callout("${{pine.milling_usd}}", unit="to have it sawn", op="·",
                       tone="warn", cue="about {{pine.milling_usd}} dollars"),
           ), title="as lumber", slot="right", icon="board"),
       )),
    _c("use_value", "Built, it replaces framing",
       "Not what the wood would sell for. What it does.",
       "The next rung is not a price for wood at all. In the dome, these trees "
       "become a shell of {{why.sqft}} square feet. At {{why.usd_per_sqft}} dollars "
       "a square foot, with framing {{why.framing_pct}} percent of it, the framing "
       "that shell replaces is worth {{why.framing_value}} dollars, the figure the "
       "last film built. The frame uses {{pine.trunk_ft}} feet of trunk, "
       "{{pine.trees_consumed}} trees' worth, but {{pine.shell_trees}} are felled, "
       "so I divide by {{pine.shell_trees}}: each tree's share is {{pine.use_usd}} "
       "dollars. That is use value: not what the wood would fetch, but what you no "
       "longer have to buy, because the wood is doing the job.",
       28.0, "hv_dome",
       callouts=(
           Tally((
               Callout("{{why.sqft}} sq ft", unit="of shell", op="·", tone="note",
                       cue="a shell of {{why.sqft}} square feet"),
               Callout("${{why.framing_value}}", unit="of framing, one shell",
                       cue="is worth {{why.framing_value}} dollars"),
               Callout("{{pine.shell_trees}}", unit="trees felled", op="÷",
                       cue="so I divide by"),
               Callout("${{pine.use_usd}}", unit="one tree's share", op="=",
                       tone="total", cue="is {{pine.use_usd}} dollars"),
           ), title="as structure", slot="right", icon="dome"),
       )),
    _c("financed", "Carried on a mortgage",
       "What the same framing costs when it is borrowed.",
       "Most framing is not paid for in cash. It rides on a mortgage. On a "
       "{{why.mortgage_years}} year loan at {{why.mortgage_pct}} percent, "
       "{{why.framing_value}} dollars of framing becomes {{why.financed}} dollars of "
       "payments, and this tree's half of that is {{pine.financed_usd}}. Read this "
       "rung carefully. It is nominal dollars, paid a month at a time for "
       "{{why.mortgage_years}} years, not money in your hand today. But it is money "
       "a household never has to send to a lender, because a tree did the job "
       "instead.",
       28.0, "hv_dome",
       callouts=(
           Tally((
               Callout("{{why.mortgage_pct}}%", unit="for {{why.mortgage_years}} years",
                       op="·", tone="note", cue="at {{why.mortgage_pct}} percent"),
               Callout("${{why.financed}}", unit="of payments, one shell",
                       cue="becomes {{why.financed}} dollars"),
               Callout("{{pine.shell_trees}}", unit="trees felled", op="÷",
                       cue="this tree's half"),
               Callout("${{pine.financed_usd}}", unit="one tree, nominal", op="=",
                       tone="total", cue="of that is {{pine.financed_usd}}"),
           ), title="as financed framing", slot="right", icon="calendar"),
       )),
    _c("ladder", "The ladder",
       "One tree, every rung.",
       "Now put the rungs together. Standing, about {{pine.stump_usd}} dollars. "
       "Burned, {{pine.firewood_usd}}. Sawn into lumber, {{pine.mill_usd}}. Split "
       "into wedge stock, {{pine.wedge_usd}}. Built into structure, "
       "{{pine.use_usd}}. And as the mortgage payments that structure avoids, "
       "{{pine.financed_usd}}, nominal, over {{why.mortgage_years}} years. It is the "
       "same tree on every rung. What changes is how much of it is kept, and how far "
       "along the chain it travels before anyone has to pay for the next step.",
       30.0, "pv_ladder",
       callouts=(
           Tally((
               Callout("${{pine.stump_usd}}", unit="standing",
                       cue="Standing, about"),
               Callout("${{pine.firewood_usd}}", unit="burned", op="·",
                       cue="Burned, {{pine.firewood_usd}}"),
               Callout("${{pine.mill_usd}}", unit="sawn lumber", op="·",
                       cue="Sawn into lumber"),
               Callout("${{pine.wedge_usd}}", unit="split wedge stock", op="·",
                       cue="Split into wedge stock"),
               Callout("${{pine.use_usd}}", unit="the structure it replaces", op="·",
                       tone="total", cue="Built into structure"),
               Callout("${{pine.financed_usd}}", unit="financed, nominal", op="·",
                       tone="note", cue="And as the mortgage payments"),
           ), title="one pine", slot="right", icon="pine", check=False),
       )),
    _c("ratios", "The wood did not get better",
       "It got used.",
       "Compare the structure rung with the ones below it. {{pine.use_usd}} dollars "
       "is {{pine.fire_ratio}} times what the tree brings as firewood, "
       "{{pine.mill_ratio}} times its sawn lumber, and {{pine.wedge_ratio}} times "
       "its split stock. The wood did not get better between those rungs. The same "
       "fibres, from the same tree, stopped being sold as a commodity and started "
       "doing a job. The biggest step on this ladder is not from the woods to the "
       "mill. It is from material to function.",
       26.0, "pv_ladder",
       callouts=(
           Tally((
               Callout("{{pine.fire_ratio}}×", unit="the firewood",
                       cue="{{pine.fire_ratio}} times what"),
               Callout("{{pine.mill_ratio}}×", unit="the sawn lumber", op="·",
                       cue="{{pine.mill_ratio}} times its sawn"),
               Callout("{{pine.wedge_ratio}}×", unit="the split stock", op="·",
                       cue="{{pine.wedge_ratio}} times its split"),
           ), title="structure, against", slot="right", icon="dome", check=False),
       )),
    _c("formula", "What the tree is worth to me",
       "What it replaces, less what it costs me to make it do so.",
       "So here is the valuation that matters to a builder. A tree is worth to me "
       "what it can replace, less the cash it costs to process, less what my own "
       "hours could have earned instead. This tree replaces {{pine.use_usd}} dollars "
       "of framing. Its share of the work is {{pine.hours}} hours, and at "
       "{{why.wage}} dollars an hour take-home, that is {{pine.labor_usd}} dollars "
       "of my time. Its share of the cash is half the shell's {{why.cash}}, "
       "{{pine.cash_usd}} dollars. That leaves {{pine.net_usd}} dollars. A pine that "
       "sells for {{pine.stump_usd}} dollars standing is worth {{pine.net_usd}} to "
       "the person who builds with it, after paying for their own time. With the "
       "fortnight's actual receipts of {{value.frame_cash}} dollars, it is "
       "{{pine.net_measured_usd}}.",
       34.0, "hv_harvest",
       callouts=(
           Tally((
               Callout("${{pine.use_usd}}", unit="what it replaces",
                       cue="This tree replaces"),
               Callout("${{pine.labor_usd}}",
                       unit="{{pine.hours}} hours at ${{why.wage}}", op="−",
                       cue="that is {{pine.labor_usd}} dollars of my time"),
               Callout("${{pine.cash_usd}}", unit="cash, half the shell's", op="−",
                       cue="half the shell's {{why.cash}}"),
               Callout("${{pine.net_usd}}", unit="the tree, to me", op="=",
                       tone="total", cue="That leaves {{pine.net_usd}} dollars"),
               Callout("${{pine.net_measured_usd}}", unit="with real receipts",
                       op="·", tone="note", cue="it is {{pine.net_measured_usd}}"),
           ), title="value to me", slot="right", icon="check"),
       )),
    _c("upstream", "The household as the whole chain",
       "Logger, mill, yard, framer and lender, kept at home.",
       "This is vertical integration, at the scale of one household. A commercial "
       "house pays every hand between the stump and the wall: the logger, the "
       "hauler, the mill, the kiln, the yard, the framer, and very often the lender. "
       "Each one takes a margin, and every margin is inside the price. This method "
       "does not make those businesses unnecessary for everyone. It lets one owner "
       "do the few steps a chainsaw and a jig can do, and keep what those steps "
       "would have cost. That is where the rungs above the wood come from.",
       28.0, "wb_chain"),
    _c("honest", "What the ladder does not say",
       "The generous figures, and the ones against me.",
       "Three cautions, because a ladder like this is easy to oversell. First, my "
       "mill figure is generous to the mill: the simulator's own packing of this log "
       "keeps {{pine.sawn_model_pct}} percent, and I used {{pine.mill_pct}}. Second, "
       "my sawing rate may be high. A survey of portable sawmill owners in "
       "{{pine.survey_year}} found them charging ${{pine.survey_milling_low}} to "
       "${{pine.survey_milling_high}} a board foot. Prices have risen since, but the "
       "sawn path may cost less than I said. Third, the top two rungs are not cash. "
       "The {{pine.use_usd}} dollars counts only if you would otherwise have bought "
       "the frame, and the financed rung is nominal payments, spread over "
       "{{why.mortgage_years}} years.",
       36.0, "ww_round",
       callouts=(
           Tally((
               Callout("{{pine.sawn_model_pct}}%", unit="sawn, simulated",
                       tone="note", cue="packing of this log keeps"),
               Callout("${{pine.survey_milling_low}}–{{pine.survey_milling_high}}",
                       unit="to saw, surveyed", op="·", tone="warn",
                       cue="found them charging"),
               Callout("${{pine.use_usd}}", unit="not cash", op="·", tone="note",
                       cue="counts only if"),
               Callout("${{pine.financed_usd}}", unit="nominal", op="·",
                       tone="note", cue="the financed rung is nominal"),
           ), title="the cautions", slot="right", icon="cross", check=False),
       )),
    _c("closing", "Thousands of dollars of structure",
       "The difference is what you do with it.",
       "So a twenty-dollar pine is not a twenty-dollar pine. On the stump it brings "
       "about {{pine.stump_usd}} dollars. Burned, {{pine.firewood_usd}}. Sawn, "
       "{{pine.mill_usd}}. Split, {{pine.wedge_usd}}. Built into a shell, it replaces "
       "{{pine.use_usd}} dollars of framing, and {{pine.financed_usd}} of payments on "
       "a loan. The tree is the same on every rung. What moves it up the ladder is "
       "how much of it you keep, and how many of the steps between the tree and the "
       "wall you are willing to take yourself.",
       30.0, "pv_ladder"),
)

CHAPTERS: tuple[Chapter, ...] = tuple(
    Chapter(c.slug, f"{index + 1:02d}", c.title, c.promise, c.narration,
            c.equations, c.duration, c.camera, c.stage, c.overlay, c.callouts)
    for index, c in enumerate(_AUTHORED))

MONEY_CHAPTERS = ("stem", "firewood", "lumber", "use_value", "financed", "ladder",
                  "ratios", "formula", "honest", "closing")
"""Every chapter that quotes a price or a value: all after the screen that says which
figures are measured, which published and which the author's."""


# ----------------------------------------------------------------------
# The written version
# ----------------------------------------------------------------------

REUSED_SOURCES = ("stumpage_pine_usd_per_ton", "green_pine_lb_per_ft3", "shell_hours",
                  "why_usd_per_sqft", "why_framing_share", "why_mortgage_rate",
                  "why_mortgage_years", "why_after_tax_wage", "why_direct_cash")
"""The figures this film borrows from the house and why-build tables."""


def pine_document() -> str:
    """The script as a document: every chapter's words, then what is on screen,
    generated from the chapters themselves, with the sources at the end."""
    from .callouts import resolve
    lines = [f"# {PINE_VALUE_LESSON.title}", "",
             "*Every figure below is computed from `two_v_demo/pine_value_economics.py`, "
             "which borrows the tree from `wedge_geometry.DEFAULT_LOG` and the framing "
             "figures from `why_build_economics.py`; the author's own figures are "
             "listed at the end and labelled as the author's.*", ""]
    for chapter in PINE_VALUE_LESSON.chapters:
        lines += [f"## {chapter.title}", "", f"**{chapter.promise}**", "",
                  *chapter.narration, ""]
        shown = []
        for entry in chapter.callouts:
            rows = entry.rows if isinstance(entry, Tally) else (entry,)
            if isinstance(entry, Tally) and entry.title:
                shown += ["", f"*{entry.title}*", ""]
            for row in rows:
                text = f"{row.op} {resolve(row.text)} {resolve(row.unit)}".strip()
                note = resolve(row.note)
                shown.append(f"- {text}" + (f" ({note})" if note else ""))
        shown += [f"- {line}" for line in chapter.equations]
        if shown:
            lines += ["On screen:", "", *shown, ""]
    lines += ["## What the figures rest on", "",
              "| Figure | Value | Kind | Why it is believed |", "|---|---|---|---|"]
    borrowed = tuple(s for s in he.SOURCES + wb.SOURCES if s.key in REUSED_SOURCES)
    for source in pv.SOURCES + borrowed:
        why = source.note + (f" Source: {source.cite}" if source.cite else "")
        figure = f"{source.value:g}" if source.units == "year" else f"{source.value:,g}"
        lines.append(f"| `{source.key}` | {figure} {source.units} | "
                     f"{source.kind} | {why} |")
    lines.append("")
    return "\n".join(lines)


def write_pine_document(path: str | Path) -> Path:
    """Write the script document, refusing to replace one that exists."""
    from .deliverables import next_version_path
    target = next_version_path(Path(path))
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(pine_document(), encoding="utf-8")
    return target


# ----------------------------------------------------------------------
# Proof
# ----------------------------------------------------------------------

def validate_pine_value_lesson() -> None:
    import re

    from .callouts import check_tally
    from .render_kit import TriangleBatch

    pv.validate_pine_value()
    wb.validate_why_build()
    he.validate_house_economics()
    PINE_VALUE_LESSON.validate()

    # The drawn pine must be the valued pine, not the book's smaller tree.
    log, plan = wg.DEFAULT_LOG, pv.essay_plan()
    assert (plan.butt_diameter_in, plan.top_diameter_in, plan.usable_length_ft) == \
        (log.butt_diameter_in, log.top_diameter_in, log.usable_length_ft), plan
    for chapter in PINE_VALUE_LESSON.chapters:
        for text in (chapter.promise, *chapter.narration):
            assert "{{" not in text, (chapter.slug, text)
    order = [chapter.slug for chapter in PINE_VALUE_LESSON.chapters]
    for slug in MONEY_CHAPTERS:
        assert order.index("sources") < order.index(slug), slug
    assert order.index("honest") < order.index("closing")
    for chapter in PINE_VALUE_LESSON.chapters:
        for entry in chapter.callouts:
            if isinstance(entry, Tally) and entry.check:
                assert not check_tally(entry), (chapter.slug, check_tally(entry))
    ladder = next(c for c in PINE_VALUE_LESSON.chapters if c.slug == "ladder")
    assert len(ladder.callouts[0].rows) == len(RUNGS), "a rung without its row"

    class _Probe:
        def __init__(self, index):
            self.world_labels, self.world_icons = [], []
            self.chapters, self.chapter_index = PINE_VALUE_LESSON.chapters, index

    for index, chapter in enumerate(PINE_VALUE_LESSON.chapters):
        painter = SCENES[chapter.stage]
        for p in (0.0, 0.3, 0.6, 1.0):
            probe = _Probe(index)
            opaque, transparent = TriangleBatch(), TriangleBatch()
            painter(probe, opaque, transparent, p)
            assert opaque.vertices or transparent.vertices, (chapter.slug, p)
            eye, target, fov = pine_camera(probe, chapter, p, 1920, 1080)
            assert np.all(np.isfinite(eye)) and np.all(np.isfinite(target))
            assert float(np.linalg.norm(eye - target)) > 1.0, (chapter.slug, p)
    for chapter in _AUTHORED:
        assert not re.search(r"\d", chapter.title), chapter.title
    assert "{{" not in pine_document()


PINE_VALUE_LESSON = Lesson(
    key="pine_value",
    brand="TWO TREES",
    title="The $20 Pine",
    chapters=CHAPTERS,
    scenes=SCENES,
    selftest=validate_pine_value_lesson,
    snapshot_prefix="pine_value",
    style="hype",
    camera_fn=pine_camera,
    label_layout="declutter",
)
