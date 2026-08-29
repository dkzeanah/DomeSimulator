"""The franken-dome: 120 struts, no two alike, held by folded sheet metal.

An experiment rather than a recommendation, documented honestly.  The
frame is whatever the chainsaw produced that day -- round, quarter-sawn,
wedge, square, rectangular -- and the joints are V brackets folded out of
scrap washing-machine casing.  Nothing is precise, everything settles,
and the sheathing takes up what the tolerance never had.

What was actually used, and what was not
----------------------------------------
The dome in this lesson was **screwed**, not bolted: three folded
brackets per triangle, four screws into each strut.  The bolted version
is presented as the upgrade it is, and labelled as such, because
pretending the prototype had hardware it did not is exactly the kind of
thing the rest of this package exists to avoid.
"""

from __future__ import annotations

import math

import numpy as np

from .geometry import build_demo_geometry, normalize
from .hubless_geometry import FRANKEN_TRADE, franken_hardware, hubless_summary
from .franken_economics import economics_report, validate_economics
from .lesson_franken_extra import (
    EXTRA_CHAPTERS,
    EXTRA_SCENES,
    extra_equations,
)
from .lessons import Chapter, Lesson
from .strut_stock import stock_report, validate_stock
from .render_kit import (
    AMBER,
    CYAN,
    GREEN,
    MUTED,
    PURPLE,
    RED,
    WHITE,
    WorldLabel,
    clamp,
    ease_in_out,
    smoothstep,
)


GEOMETRY = build_demo_geometry()
SUMMARY = hubless_summary()
FRANKEN = franken_hardware()
SCALE = 5.2

TIMBER = (0.66, 0.48, 0.28, 1.0)
TIMBER_PALE = (0.78, 0.62, 0.38, 1.0)
BARK = (0.34, 0.26, 0.18, 1.0)
GALV = (0.72, 0.75, 0.80, 1.0)
GALV_DARK = (0.46, 0.50, 0.56, 1.0)
SCREW = (0.86, 0.80, 0.42, 1.0)


# ----------------------------------------------------------------------
# Mixed stock: five profiles, drawn as what they actually are
# ----------------------------------------------------------------------

# name, sides for the prism, radius multiplier, colour.  A three-sided
# prism really is a wedge; a four-sided one really is square stock.  Using
# the segment count to carry the profile keeps the picture honest.
PROFILES: tuple[tuple[str, int, float, tuple], ...] = (
    ("ROUND", 14, 1.00, TIMBER),
    ("QUARTER-SAWN", 4, 0.92, TIMBER_PALE),
    ("WEDGE", 3, 1.12, BARK),
    ("SQUARE", 4, 0.86, TIMBER),
    ("RECTANGULAR", 4, 1.05, TIMBER_PALE),
)


def _profile_for(index: int) -> tuple[str, int, float, tuple]:
    """Deterministic, so the same strut is the same stick in every shot."""
    return PROFILES[(index * 7 + index // 3) % len(PROFILES)]


def _strut(batch, a, b, index: int, radius: float = 0.11) -> None:
    """One stick, drawn with its own cross-section."""
    _, sides, multiplier, colour = _profile_for(index)
    batch.cylinder(np.asarray(a, dtype=np.float64),
                   np.asarray(b, dtype=np.float64),
                   radius * multiplier, colour, sides)


def _jitter(seed: int, settle: float) -> np.ndarray:
    """Where the joints actually land, before and after the frame settles.

    ``settle`` runs 0 to 1.  At 0 the frame is as it goes together, every
    joint sitting where a different centreline put it.  At 1 it has been
    pulled together and taken up its slack -- which is a real thing a
    loose frame does, not a rendering trick.
    """
    rng = np.random.default_rng(seed)
    raw = rng.normal(0.0, 1.0, GEOMETRY.vertices.shape) * 0.075
    return GEOMETRY.vertices + raw * (1.0 - settle * 0.72)


def _franken_frame(batch, settle: float, radius: float = 0.11,
                   scale: float = SCALE) -> np.ndarray:
    points = _jitter(7, settle)
    for index, edge in enumerate(GEOMETRY.hemisphere_edges):
        a, b = (points[i] * scale for i in edge)
        _strut(batch, a, b, index, radius)
    return points


def _rgb(colour) -> tuple[int, int, int]:
    return (int(colour[0] * 255), int(colour[1] * 255), int(colour[2] * 255))


# ----------------------------------------------------------------------
# The V bracket, in the three states it exists in
# ----------------------------------------------------------------------

def _bracket_flat(batch, centre, size=(3.6, 1.15), holes: int = 8,
                  colour=GALV) -> None:
    """The band as it leaves the shears: flat, drilled, not yet bent."""
    centre = np.asarray(centre, dtype=np.float64)
    length, width = size
    batch.box(tuple(centre), (length, width, 0.055), colour)
    for index in range(holes):
        row, column = divmod(index, holes // 2)
        x = centre[0] - length * 0.5 + length * (0.14 + 0.24 * column)
        y = centre[1] + (width * 0.24 if row else -width * 0.24)
        batch.cylinder(np.array([x, y, centre[2] - 0.06]),
                       np.array([x, y, centre[2] + 0.06]),
                       0.075, (0.06, 0.08, 0.11, 1.0), 8)


def _slab(batch, centre, along, across, up, colour) -> None:
    """An oriented rectangular slab: six faces, each wound outward.

    ``along``, ``across`` and ``up`` are half-extent vectors, so the slab
    can lie at any angle. ``batch.box`` is axis-aligned only, which is why
    the folded bracket needs this.

    The renderer culls by winding rather than by the normal handed to it,
    so each face is wound from its outward direction instead of trusting a
    fixed vertex order -- get that backwards and the face is lit correctly
    and still invisible.
    """
    centre = np.asarray(centre, dtype=np.float64)
    axes = [np.asarray(v, dtype=np.float64) for v in (along, across, up)]
    for index in range(3):
        axis = axes[index]
        other_a, other_b = axes[(index + 1) % 3], axes[(index + 2) % 3]
        for sign in (1.0, -1.0):
            face = centre + axis * sign
            outward = normalize(axis) * sign
            corners = [face - other_a - other_b, face + other_a - other_b,
                       face + other_a + other_b, face - other_a + other_b]
            turn = np.cross(corners[1] - corners[0], corners[2] - corners[0])
            if float(np.dot(turn, outward)) < 0.0:
                corners.reverse()
            batch.quad(corners[0], corners[1], corners[2], corners[3],
                       colour, outward)


HOLES_PER_LEG = 4
"""Four holes a side, eight a bracket, four screws into each strut."""

_HOLE_GRID = ((0.34, -0.26), (0.34, 0.26), (0.76, -0.26), (0.76, 0.26))
"""Where those four sit on a leg: along the leg, then across it."""


def _bracket_bent(batch, centre, fold_deg: float, size=(3.6, 1.15),
                  colour=GALV, screws: bool = False) -> None:
    """The band folded down the middle into a V.

    Each leg is a genuine flat rectangle with four holes through it. The
    first version drew a leg as a pair of four-sided cylinders -- a
    four-sided cylinder is a diamond prism, so the bracket rendered as a
    crumpled angular blob rather than as folded sheet metal, and it put
    six screws on a leg that only ever takes four.
    """
    centre = np.asarray(centre, dtype=np.float64)
    length, width = size
    half = length * 0.5
    thickness = 0.075

    # fold_deg is the angle *between* the legs, so each leg sits half of it
    # off the bisector -- and the bisector points straight up, because that
    # is where a dome corner puts it. Measuring from the X axis instead
    # aimed both legs the same way and produced a sideways wedge that never
    # touched the struts it was supposed to be holding.
    half_angle = math.radians(fold_deg * 0.5)
    for side in (-1.0, 1.0):
        direction = np.array([side * math.sin(half_angle), 0.0,
                              math.cos(half_angle)])
        # The plate's own normal: perpendicular to the leg, still in XZ, so
        # the two legs share a crease running along Y.
        face_normal = np.array([side * math.cos(half_angle), 0.0,
                                -math.sin(half_angle)])
        across = np.array([0.0, 1.0, 0.0])

        _slab(batch, centre + direction * half * 0.5,
              direction * half * 0.5, across * width * 0.5,
              face_normal * thickness * 0.5, colour)

        for reach, offset in _HOLE_GRID:
            seat = (centre + direction * half * reach
                    + across * width * offset)
            # A hole is a dark disc through the plate; a screw is a head
            # proud of it. Both sit exactly where the hole was drilled.
            batch.cylinder(seat - face_normal * thickness,
                           seat + face_normal * thickness,
                           0.085, (0.05, 0.06, 0.09, 1.0), 10)
            if screws:
                batch.sphere(seat + face_normal * thickness * 1.6,
                             0.10, SCREW, 3, 7)


def scene_fk_premise(app, opaque, transparent, p: float) -> None:
    """The finished thing, lumpy, standing."""
    settle = ease_in_out(clamp(p * 1.2))
    _franken_frame(opaque, settle, 0.12)
    app.world_labels.extend([
        WorldLabel(np.array([0.0, 0.0, SCALE + 1.6]),
                   f"{SUMMARY.struts} STRUTS, NO TWO ALIKE", (255, 177, 62)),
        WorldLabel(np.array([0.0, 0.0, -1.0]),
                   f"{FRANKEN.build_days} days, a chainsaw, and "
                   f"{FRANKEN.screws:,} screws", (169, 188, 203)),
    ])


def scene_fk_stock(app, opaque, transparent, p: float) -> None:
    """Five profiles, side by side, each drawn as what it is."""
    reveal = clamp(p * 1.35)
    span = 14.0
    step = span / (len(PROFILES) - 1)
    for index, (name, sides, multiplier, colour) in enumerate(PROFILES):
        if index / len(PROFILES) > reveal:
            continue
        x = -span * 0.5 + index * step
        base = np.array([x, 0.0, 0.7])
        top = np.array([x, 0.0, 5.1])
        opaque.cylinder(base, top, 0.46 * multiplier, colour, sides)
        app.world_labels.append(WorldLabel(
            np.array([x, 0.0, 5.9]), name, _rgb(colour)))
    app.world_labels.append(WorldLabel(
        np.array([0.0, 0.0, -0.6]),
        "every section has a different centreline, so no joint lands "
        "where the geometry says", (169, 188, 203)))


def scene_fk_bracket_flat(app, opaque, transparent, p: float) -> None:
    """Where a bracket comes from: a flat band with holes in it."""
    reveal = clamp(p * 1.4)
    # The donor: a washing machine panel.
    opaque.box((-6.4, 0.0, 2.6), (4.6, 0.35, 4.6), GALV_DARK)
    app.world_labels.append(WorldLabel(
        np.array([-6.4, 0.0, 5.6]),
        "WASHING MACHINE CASING\nfree, flat, and stronger than it looks",
        _rgb(GALV)))
    # Bands sheared from it, drilled.
    for index in range(3):
        if index / 3 > reveal:
            continue
        _bracket_flat(opaque, (2.2, 0.0, 1.4 + index * 1.6))
        if index == 1:
            app.world_labels.append(WorldLabel(
                np.array([2.2, 0.0, 1.4 + index * 1.6]),
                "8 HOLES", (134, 210, 255)))
    app.world_labels.append(WorldLabel(
        np.array([2.2, 0.0, 6.2]),
        "FLAT BAND, DRILLED  -  not yet a bracket", (61, 211, 255)))


def scene_fk_bracket_bend(app, opaque, transparent, p: float) -> None:
    """One fold down the middle turns a band into a joint."""
    fold = 180.0 - ease_in_out(clamp((p - 0.12) / 0.7)) * 108.0
    _bracket_bent(opaque, (0.0, 0.0, 2.4), fold, colour=GALV)
    app.world_labels.extend([
        WorldLabel(np.array([0.0, 0.0, 5.2]),
                   "ONE FOLD, DOWN THE MIDDLE", (61, 211, 255)),
        WorldLabel(np.array([0.0, 0.0, 0.4]),
                   f"the fold angle is whatever that corner turned out to be",
                   (169, 188, 203)),
    ])


def scene_fk_bracket_fitted(app, opaque, transparent, p: float) -> None:
    """The bracket in place: one V, two struts, four screws each."""
    reveal = clamp(p * 1.4)
    corner = np.array([0.0, 0.0, 1.4])
    for side, index in ((-1.0, 0), (1.0, 4)):
        direction = np.array([side * math.cos(math.radians(28.0)), 0.0,
                              math.sin(math.radians(28.0))])
        _strut(opaque, corner, corner + direction * 6.2, index, 0.42)
    _bracket_bent(opaque, tuple(corner + np.array([0.0, -0.55, 0.0])),
                  124.0, size=(5.0, 1.5), screws=reveal > 0.35)
    app.world_labels.extend([
        WorldLabel(corner + np.array([0.0, 0.0, 3.6]),
                   "4 SCREWS INTO EACH STRUT\n8 per bracket", (255, 177, 62)),
        WorldLabel(corner + np.array([-4.2, 0.0, 2.4]),
                   "STRUT A", (169, 188, 203)),
        WorldLabel(corner + np.array([4.2, 0.0, 2.4]),
                   "STRUT B", (169, 188, 203)),
        WorldLabel(np.array([0.0, 0.0, -1.0]),
                   f"{FRANKEN.brackets_per_triangle} brackets per triangle  x  "
                   f"{SUMMARY.triangles} triangles  =  {FRANKEN.brackets}",
                   (111, 235, 155)),
    ])


def scene_fk_triangle(app, opaque, transparent, p: float) -> None:
    """One triangle, three sticks, three brackets."""
    build = clamp(p * 1.3)
    radius = 4.6
    corners = [np.array([radius * math.cos(math.tau * i / 3 + math.pi / 2),
                         radius * math.sin(math.tau * i / 3 + math.pi / 2),
                         0.9]) for i in range(3)]
    for index in range(3):
        if index / 3 > build:
            continue
        _strut(opaque, corners[index], corners[(index + 1) % 3], index * 3, 0.20)
    for index, corner in enumerate(corners):
        if (index + 1) / 3 > build:
            continue
        _bracket_bent(opaque, tuple(corner), 118.0, size=(2.2, 0.9),
                      screws=build > 0.85)
    app.world_labels.append(WorldLabel(
        np.array([0.0, 0.0, 4.2]),
        "3 STICKS, 3 BRACKETS, 24 SCREWS", (61, 211, 255)))
    app.world_labels.append(WorldLabel(
        np.array([0.0, 0.0, -1.0]),
        f"repeat {SUMMARY.triangles} times", (169, 188, 203)))


def scene_fk_slack(app, opaque, transparent, p: float) -> None:
    """The slack, exaggerated by nothing: this is the jitter as built."""
    points = _franken_frame(opaque, 0.0, 0.12)
    ideal = GEOMETRY.vertices
    used = sorted({i for edge in GEOMETRY.hemisphere_edges for i in edge})
    worst = 0.0
    for index in used:
        actual = points[index] * SCALE
        target = ideal[index] * SCALE
        offset = float(np.linalg.norm(actual - target))
        worst = max(worst, offset)
        opaque.sphere(target, 0.055, (0.32, 0.91, 0.58, 1.0), 3, 7)
        if offset > 0.02:
            opaque.cylinder(target, actual, 0.028, RED, 5)
    app.world_labels.extend([
        WorldLabel(np.array([0.0, 0.0, SCALE + 1.8]),
                   "GREEN = WHERE THE GEOMETRY SAYS", (111, 235, 155)),
        WorldLabel(np.array([0.0, 0.0, SCALE + 0.9]),
                   "RED = WHERE THE STICK ACTUALLY PUT IT", (255, 87, 94)),
        WorldLabel(np.array([0.0, 0.0, -1.0]),
                   "not one joint lands on the sphere, and it does not matter yet",
                   (169, 188, 203)),
    ])


def scene_fk_settle(app, opaque, transparent, p: float) -> None:
    """Pull it together and the whole frame takes up its slack."""
    settle = ease_in_out(clamp((p - 0.08) / 0.78))
    _franken_frame(opaque, settle, 0.12)
    app.world_labels.extend([
        WorldLabel(np.array([0.0, 0.0, SCALE + 1.6]),
                   "SETTLING" if settle < 0.92 else "SETTLED",
                   (255, 177, 62) if settle < 0.92 else (111, 235, 155)),
        WorldLabel(np.array([0.0, 0.0, -1.0]),
                   "every triangle is rigid, so the error is shared out "
                   "instead of walking around a ring", (169, 188, 203)),
    ])


def scene_fk_skin(app, opaque, transparent, p: float) -> None:
    """The sheathing spans what the tolerance never had."""
    skin = ease_in_out(clamp((p - 0.35) / 0.58))
    points = _franken_frame(opaque, 0.55, 0.11)
    if skin > 0.01:
        for face in GEOMETRY.hemisphere_faces:
            corners = np.array([
                points[int(v)] * (1.0 - skin) + GEOMETRY.vertices[int(v)] * skin
                for v in face
            ]) * (SCALE * (1.0 + 0.05 * skin))
            normal = normalize(corners.mean(axis=0))
            transparent.triangle(corners[0], corners[1], corners[2],
                                 (0.55, 0.80, 0.88, 0.36 * skin), normal)
    app.world_labels.append(WorldLabel(
        np.array([0.0, 0.0, SCALE + 1.8]),
        "THE SKIN SPANS THE SLACK" if skin > 0.4 else "LUMPY FRAME",
        (111, 235, 155) if skin > 0.4 else (255, 177, 62)))


def scene_fk_trees(app, opaque, transparent, p: float) -> None:
    """Four trees taking the share the tolerance could not."""
    scale = 3.6
    points = _jitter(7, 0.55)
    for index, edge in enumerate(GEOMETRY.hemisphere_edges):
        a, b = (points[i] * scale for i in edge)
        _strut(opaque, a, b, index, 0.075)
    tension = ease_in_out(clamp((p - 0.18) / 0.64))
    apex = np.array([0.0, 0.0, scale])
    for index in range(4):
        angle = math.tau * index / 4 + math.pi * 0.25
        trunk = np.array([7.6 * math.cos(angle), 7.6 * math.sin(angle), 0.0])
        opaque.cylinder(trunk, trunk + np.array([0.0, 0.0, 8.6]), 0.32, BARK, 8)
        for level in range(3):
            transparent.sphere(trunk + np.array([0.0, 0.0, 5.2 + level * 1.3]),
                               1.6 - level * 0.3, (0.22, 0.45, 0.26, 0.42), 3, 7)
        if tension > 0.02:
            anchor = trunk + np.array([0.0, 0.0, 6.8])
            opaque.cylinder(anchor, apex * tension + anchor * (1.0 - tension),
                            0.026, GREEN, 6)
    app.world_labels.extend([
        WorldLabel(np.array([0.0, 0.0, scale + 2.6]),
                   "GUYED INTO FOUR TREES", (111, 235, 155)),
        WorldLabel(np.array([0.0, 0.0, -1.1]),
                   "the site carried what the frame did not", (169, 188, 203)),
    ])


def scene_fk_ledger(app, opaque, transparent, p: float) -> None:
    """What it actually took, in parts."""
    reveal = clamp(p * 1.3)
    rows = (
        (f"{FRANKEN.brackets} BRACKETS", FRANKEN.brackets, CYAN),
        (f"{FRANKEN.screws:,} SCREWS", FRANKEN.screws, AMBER),
        (f"{SUMMARY.struts} STRUTS", SUMMARY.struts, GREEN),
        (f"{SUMMARY.triangles} TRIANGLES", SUMMARY.triangles, PURPLE),
    )
    biggest = max(value for _, value, _ in rows)
    span = 12.0
    step = span / (len(rows) - 1)
    for index, (label, value, colour) in enumerate(rows):
        if index / len(rows) > reveal:
            continue
        x = -span * 0.5 + index * step
        height = 4.2 * (value / biggest) ** 0.55
        opaque.box((x, 0.0, height * 0.5 + 0.2), (1.9, 0.95, max(0.06, height)),
                   colour)
        app.world_labels.append(WorldLabel(
            np.array([x, 0.0, height + 0.9]), label, _rgb(colour)))
    app.world_labels.append(WorldLabel(
        np.array([0.0, 0.0, -1.0]),
        f"{FRANKEN.build_days} days  -  "
        f"{FRANKEN.triangles_per_day:.0f} triangles and "
        f"{FRANKEN.screws_per_day:.0f} screws a day", (111, 235, 155)))


def scene_fk_bolts(app, opaque, transparent, p: float) -> None:
    """The upgrade that was NOT used, labelled as the upgrade it is."""
    reveal = clamp(p * 1.3)
    corner = np.array([-4.4, 0.0, 1.8])
    for side, index in ((-1.0, 0), (1.0, 4)):
        direction = np.array([side * math.cos(math.radians(26.0)), 0.0,
                              math.sin(math.radians(26.0))])
        _strut(opaque, corner, corner + direction * 4.4, index, 0.38)
    _bracket_bent(opaque, tuple(corner + np.array([0.0, -0.5, 0.0])), 128.0,
                  size=(4.0, 1.3), screws=True)
    app.world_labels.append(WorldLabel(
        corner + np.array([0.0, 0.0, 3.4]),
        "WHAT WAS BUILT\nfolded bracket, 8 screws", (111, 235, 155)))

    other = np.array([4.4, 0.0, 1.8])
    for side, index in ((-1.0, 1), (1.0, 3)):
        direction = np.array([side * math.cos(math.radians(26.0)), 0.0,
                              math.sin(math.radians(26.0))])
        _strut(opaque, other, other + direction * 4.4, index, 0.38)
    if reveal > 0.3:
        for step in (-0.5, 0.5):
            point = other + np.array([step, 0.0, 0.35])
            opaque.cylinder(point + np.array([0.0, -0.75, 0.0]),
                            point + np.array([0.0, 0.75, 0.0]),
                            0.10, WHITE, 8)
            for end in (-0.75, 0.75):
                opaque.sphere(point + np.array([0.0, end, 0.0]), 0.19, MUTED, 4, 8)
    app.world_labels.append(WorldLabel(
        other + np.array([0.0, 0.0, 3.4]),
        "THE UPGRADE\n2 bolts, nuts and washers", (61, 211, 255)))
    app.world_labels.append(WorldLabel(
        np.array([0.0, 0.0, -1.2]),
        "the prototype was screwed, not bolted  -  bolts are what to do next",
        (169, 188, 203)))


def scene_fk_trade(app, opaque, transparent, p: float) -> None:
    """What the method gives up and what it buys."""
    reveal = clamp(p * 1.3)
    colours = (RED, GREEN, CYAN, AMBER, PURPLE)
    for index, (title, _) in enumerate(FRANKEN_TRADE):
        if index / len(FRANKEN_TRADE) > reveal:
            continue
        x = -9.0 + index * 4.5
        opaque.box((x, 0.0, 1.7), (2.7, 0.55, 2.6), colours[index % len(colours)])
        app.world_labels.append(WorldLabel(
            np.array([x, 0.0, 3.7]), title.upper(),
            _rgb(colours[index % len(colours)])))


SCENES = {
    "fk_premise": scene_fk_premise,
    "fk_stock": scene_fk_stock,
    "fk_bracket_flat": scene_fk_bracket_flat,
    "fk_bracket_bend": scene_fk_bracket_bend,
    "fk_bracket_fitted": scene_fk_bracket_fitted,
    "fk_triangle": scene_fk_triangle,
    "fk_slack": scene_fk_slack,
    "fk_settle": scene_fk_settle,
    "fk_skin": scene_fk_skin,
    "fk_trees": scene_fk_trees,
    "fk_ledger": scene_fk_ledger,
    "fk_bolts": scene_fk_bolts,
    "fk_trade": scene_fk_trade,
}
SCENES.update(EXTRA_SCENES)


def franken_equations(app, stage: str) -> list[str]:
    added = extra_equations(app, stage)
    if added:
        return added
    if stage in ("fk_premise", "fk_stock"):
        return [
            f"struts    = {SUMMARY.struts}, any section",
            f"triangles = {SUMMARY.triangles}",
            f"build     = {FRANKEN.build_days} days",
        ]
    if stage in ("fk_bracket_flat", "fk_bracket_bend", "fk_bracket_fitted"):
        return [
            f"brackets  = {SUMMARY.triangles} x "
            f"{FRANKEN.brackets_per_triangle} = {FRANKEN.brackets}",
            f"screws    = {FRANKEN.screws_per_bracket} per bracket "
            f"(4 into each strut)",
            f"total     = {FRANKEN.screws:,} screws",
        ]
    if stage == "fk_triangle":
        return [
            f"per triangle: 3 struts, "
            f"{FRANKEN.brackets_per_triangle} brackets, "
            f"{FRANKEN.brackets_per_triangle * FRANKEN.screws_per_bracket} screws",
            f"x {SUMMARY.triangles} triangles",
        ]
    if stage in ("fk_slack", "fk_settle", "fk_skin"):
        return [
            "no joint lands on the sphere",
            "every triangle is rigid on its own",
            "the skin returns the shell action",
        ]
    if stage == "fk_ledger":
        return [
            f"brackets {FRANKEN.brackets}   screws {FRANKEN.screws:,}",
            f"{FRANKEN.triangles_per_day:.0f} triangles/day, "
            f"{FRANKEN.screws_per_day:.0f} screws/day",
            f"stood {FRANKEN.stood_months} months = "
            f"{FRANKEN.service_ratio:.0f}x its build time",
        ]
    if stage == "fk_bolts":
        return [
            "built: folded brackets + screws",
            f"upgrade: {FRANKEN.bolts_per_edge} bolts per edge = "
            f"{FRANKEN.bolts} bolts",
            f"          + {FRANKEN.washers} washers",
        ]
    return []


CHAPTERS: tuple[Chapter, ...] = (
    Chapter(
        "premise", "01", "The franken-dome",
        "One hundred and twenty struts, and no two of them alike.",
        (
            "This is an experiment, not a recommendation, and it is documented here",
            "because nobody seems to have written it down. The question was simple: how",
            "fast does a dome go up if you stop caring what the struts are? Not cheaper",
            "struts. Not rougher struts. Struts with no specification at all, beyond",
            "being roughly the right length.",
        ),
        ("120 struts, no specification", "10 days, one chainsaw"),
        20.0, (34.0, 24.0, 17.0), "fk_premise",
    ),
    Chapter(
        "stock", "02", "Whatever the chainsaw made",
        "Round, quarter-sawn, wedge, square, rectangular. All in the same dome.",
        (
            "Round logs still in the bark. Quarter-sawn pieces off a milling jig. Wedges",
            "that were offcuts of something else. Square stock, rectangular stock,",
            "whatever came off the pile that day. They are not interchangeable in any",
            "engineering sense: every one of those sections has its centreline in a",
            "different place, so no two joints in the whole dome are the same joint.",
        ),
        ("five profiles, one frame", "every section, a different centreline"),
        20.0, (90.0, 16.0, 19.0), "fk_stock",
    ),
    Chapter(
        "bracket_flat", "03", "Where a bracket comes from",
        "A flat band of washing machine casing, drilled.",
        (
            "The joints are the interesting part. Every one is a bracket I made, and",
            "every bracket started as a flat band sheared out of a scrapped washing",
            "machine. That casing is galvanised sheet in a gauge that is genuinely",
            "structural at this size, it is free, it is already flat, and there is a",
            "great deal of it in the world. Shear a band, drill six or eight holes in",
            "it, and that is the whole component.",
        ),
        ("washing machine casing", "shear a band, drill 6 to 8 holes"),
        21.0, (86.0, 18.0, 18.0), "fk_bracket_flat",
    ),
    Chapter(
        "bracket_bend", "04", "One fold makes it a joint",
        "Bend it in half and it becomes a V.",
        (
            "Then one fold, straight down the middle, and the band becomes a V. That is",
            "the entire bracket. No welding, no castings, no bought connectors. And",
            "because you are bending it yourself, the fold angle is simply whatever that",
            "particular corner turned out to be, which on a frame like this is never the",
            "angle on the drawing. The bracket adapts to the joint instead of the joint",
            "having to match the bracket. That is the trick, and it is why the method",
            "tolerates such rough stock.",
        ),
        ("one fold, down the middle",
         "the bracket adapts to the joint, not the other way round"),
        23.0, (66.0, 20.0, 14.0), "fk_bracket_bend",
    ),
    Chapter(
        "bracket_fitted", "05", "Four screws into each strut",
        "Two struts, one V, eight screws.",
        (
            "In place it works like this. The V straddles the corner, one leg down each",
            "strut. Four screws through the leg into the first strut, four more into the",
            "second, so eight screws per bracket. Four in shear along a leg is a",
            "genuinely stiff connection, and it fails gradually and visibly rather than",
            "suddenly, which for a structure you are experimenting with is exactly the",
            "behaviour you want.",
        ),
        ("4 screws into each strut", "8 screws per bracket",
         "surprisingly stiff in shear"),
        22.0, (58.0, 18.0, 15.0), "fk_bracket_fitted",
    ),
    Chapter(
        "triangle", "06", "One triangle at a time",
        "Three sticks, three brackets, twenty-four screws.",
        (
            "The unit of work is one triangle: three sticks, three brackets, twenty-four",
            "screws. You build them flat on the ground, which means no ladder work and no",
            "holding anything overhead. Forty of those and the dome is a pile of finished",
            "triangles waiting to be stood up.",
        ),
        ("3 sticks + 3 brackets + 24 screws", "40 triangles, all built flat"),
        19.0, (44.0, 34.0, 15.0), "fk_triangle",
    ),
    Chapter(
        "slack", "07", "Nothing lands where it should",
        "Green is the geometry. Red is where the stick actually put it.",
        (
            "Here is the honest picture of what you get. The green points are where the",
            "geometry says every hub belongs. The red lines show where the sticks",
            "actually put them. Not one joint in the dome lands on the sphere. Some are",
            "out by a quarter of an inch, some by more, and every single one of those",
            "errors is a different error because every stick is a different stick.",
        ),
        ("green = the geometry", "red = the stick",
         "not one joint on the sphere"),
        21.0, (30.0, 26.0, 18.0), "fk_slack",
    ),
    Chapter(
        "settle", "08", "And then it settles",
        "Pull it together and the whole frame shares the error out.",
        (
            "Now watch what happens when you actually pull it together and stand it up.",
            "The frame settles. Every triangle is individually rigid, so a joint that",
            "wants to sit proud is held by the two around it, and the error gets shared",
            "out across the whole shell instead of accumulating around a ring the way it",
            "does in a precise dome. That redundancy is not a nice property here. It is",
            "the only reason the thing stands at all.",
        ),
        ("the error is shared, not accumulated",
         "redundancy is what makes it possible"),
        23.0, (52.0, 22.0, 17.0), "fk_settle",
    ),
    Chapter(
        "skin", "09", "The sheathing takes up the rest",
        "A monolithic skin spans slack the frame never lost.",
        (
            "What is left after settling is a lumpy brain of a frame that is near the",
            "sphere without being on it. The sheathing finishes the job. A skin bonded",
            "over the outside bridges every remaining gap and gives back the shell action",
            "the sloppiness cost. Once it is on, the structure behaves far more like the",
            "skin than like the frame, which is the whole reason the frame is allowed to",
            "be this bad.",
        ),
        ("the skin returns the shell action",
         "the structure becomes the skin, not the frame"),
        22.0, (38.0, 26.0, 17.0), "fk_skin",
    ),
    Chapter(
        "trees", "10", "Borrowing from the site",
        "Four trees did the work the tolerance did not.",
        (
            "It went up between four trees, and that was not an accident. Cable overhead",
            "tied back into the trunks meant the frame never had to be self-supporting",
            "while it was going together, and the trees kept taking a share afterwards.",
            "Covered in clear plastic, it stood through half a year of weather before I",
            "took it down deliberately. That is eighteen times its own build time, which",
            "is the only durability number I actually have.",
        ),
        ("guyed into four trees", "stood 6 months = 18x its build time"),
        22.0, (46.0, 20.0, 21.0), "fk_trees",
    ),
    Chapter(
        "ledger", "11", "The parts list",
        "One hundred and twenty brackets, nine hundred and sixty screws.",
        (
            "The whole ledger. One hundred and twenty brackets, folded by hand from",
            "scrap. Nine hundred and sixty screws. One hundred and twenty struts of no",
            "particular description. Ten days, which is four triangles and about a",
            "hundred screws a day. The timber was free and the brackets were free. The",
            "screws were the entire material cost of the structure.",
        ),
        ("120 brackets, 960 screws", "10 days, 4 triangles a day",
         "the screws were the whole material cost"),
        22.0, (90.0, 16.0, 18.0), "fk_ledger",
    ),
    Chapter(
        "bolts", "12", "What I did not do",
        "This one was screwed, not bolted. Bolts are the upgrade.",
        (
            "One correction, because it matters. This dome was screwed together. It was",
            "not bolted. If you build one to keep, put two bolts with nuts and washers",
            "through every edge as well, and that is a hundred and thirty bolts on top of",
            "the screws. It is the single best place to spend money on this structure,",
            "because bolts come out again. They get unbolted and reused on the next and",
            "better dome, so heavy hardware bought once never becomes obsolete. But it is",
            "not what held this one up, and saying otherwise would be inventing a",
            "structure I did not build.",
        ),
        ("built: brackets and screws", "upgrade: 130 bolts, 260 washers",
         "bolts come out again and get reused"),
        26.0, (74.0, 18.0, 16.0), "fk_bolts",
    ),
# The strut coding, the deck and the commercial case go in ahead of
# the closing trade-off chapter.
    Chapter(
        "trade", "13", "What it trades",
        "A little structure for a great deal of speed.",
        (
            "So what is the trade? You give up precision, and with it any claim to a",
            "calculated structure. You get back an enormous amount of speed, a material",
            "cost near zero, and a method that tolerates stock nobody else would use. For",
            "a storage building, a workshop, or a shelter, where the covering matters more",
            "than the tolerance, I think that is a completely valid way to build. For",
            "anything inspected, occupied full time, or carrying snow you have not",
            "calculated for, it is not. Both of those things are true at once.",
        ),
        ("give up: precision and calculation",
         "get back: speed and near-zero cost"),
        24.0, (90.0, 15.0, 20.0), "fk_trade",
    ),
)


from dataclasses import replace as _replace

CHAPTERS = tuple(
    _replace(chapter, number=f"{index + 1:02d}")
    for index, chapter in enumerate(
        CHAPTERS[:-1] + EXTRA_CHAPTERS + CHAPTERS[-1:])
)


FRANKEN_LESSON = Lesson(
    key="franken",
    brand="FRANKENDOME / MIXED STOCK",
    title="The Franken-Dome",
    chapters=CHAPTERS,
    scenes=SCENES,
    equations=franken_equations,
    selftest=lambda: (validate_stock(), validate_economics(), None)[-1],
    report=lambda: stock_report() + chr(10) * 2 + economics_report(),
    snapshot_prefix="franken",
    # New work, so labels declutter. The 13-chapter version that
    # shipped as frankendome-build.mp4 predates both this and the
    # eight added chapters, and is archival rather than reproducible.
    label_layout="declutter",
)
