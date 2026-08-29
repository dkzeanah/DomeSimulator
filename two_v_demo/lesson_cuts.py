"""The compound cut, on both machines, step by step.

The hardest operation in a hubless dome is not a hard *idea* -- it is two
cuts on two different machines, each of which can only do the one the
other cannot, with a jig in between that has to be built before anything
worth keeping goes near a blade.

Everything drawn here is at one consistent scale: **one world unit is two
inches**, so a ten inch blade is five units across and a 2x4 is 1.75 by
0.75.  Keeping that honest is what lets the pictures answer questions
like "will the blade actually come through" instead of just illustrating.
"""

from __future__ import annotations

import math

import numpy as np

from .geometry import normalize
from .lessons import Chapter, Lesson
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
from .sawing import (
    BLADE_DIAMETER_IN,
    FAILURES,
    STEPS,
    STOCK_THICKNESS_IN,
    STOCK_WIDTH_IN,
    TABLE_SAW_MAX_TILT_DEG,
    TYPICAL_MITRE_SAW_MAX_DEG,
    BevelCheck,
    FiveCutCheck,
    blade_projection_in,
    cut_plans,
    sawing_report,
    sled_capacity_in,
    validate_sawing,
)


UNITS_PER_INCH = 0.5
"""One world unit is two inches. Every dimension below goes through here."""


def inch(value: float) -> float:
    return value * UNITS_PER_INCH


BLADE_R = inch(BLADE_DIAMETER_IN) * 0.5
STOCK_W = inch(STOCK_WIDTH_IN)
STOCK_T = inch(STOCK_THICKNESS_IN)

PLANS = cut_plans()
PLAN = PLANS[0]

STEEL = (0.78, 0.83, 0.90, 1.0)
DARK_STEEL = (0.28, 0.32, 0.38, 1.0)
TIMBER = (0.72, 0.55, 0.32, 1.0)
TIMBER_CUT = (0.86, 0.70, 0.44, 1.0)
JIG = (0.42, 0.34, 0.24, 1.0)

TABLE_Z = 1.30
"""Height of a saw table above the scene floor.

The renderer's ground slab occupies z -0.34 to -0.06, so anything
built straddling zero interpenetrates it and the depth buffer tears
both solids into stripes. Everything here sits on top of it."""


def _rgb(colour) -> tuple[int, int, int]:
    return (int(colour[0] * 255), int(colour[1] * 255), int(colour[2] * 255))


def _rotate_z(point: np.ndarray, degrees: float) -> np.ndarray:
    angle = math.radians(degrees)
    cos_a, sin_a = math.cos(angle), math.sin(angle)
    return np.array([
        point[0] * cos_a - point[1] * sin_a,
        point[0] * sin_a + point[1] * cos_a,
        point[2],
    ])


def _prism(batch, centre, size, colour, yaw_deg: float = 0.0) -> None:
    """A box that can be turned about Z, which the batch's box cannot."""
    half = np.asarray(size, dtype=np.float64) * 0.5
    corners = []
    for sx in (-1, 1):
        for sy in (-1, 1):
            for sz in (-1, 1):
                corners.append(_rotate_z(
                    np.array([half[0] * sx, half[1] * sy, half[2] * sz]),
                    yaw_deg) + np.asarray(centre, dtype=np.float64))
    faces = ((0, 1, 3, 2), (4, 6, 7, 5), (0, 4, 5, 1),
             (2, 3, 7, 6), (0, 2, 6, 4), (1, 5, 7, 3))
    for a, b, c, d in faces:
        pa, pb, pc, pd = (corners[i] for i in (a, b, c, d))
        normal = normalize(np.cross(pb - pa, pc - pa))
        batch.triangle(pa, pb, pc, colour, normal)
        batch.triangle(pa, pc, pd, colour, normal)


def _blade(batch, hub, axis, radius: float, thickness: float = 0.045,
           colour=STEEL, teeth: bool = True) -> None:
    """A saw blade: a thin disc with an arbor and a rim of teeth."""
    axis = normalize(np.asarray(axis, dtype=np.float64))
    hub = np.asarray(hub, dtype=np.float64)
    batch.cylinder(hub - axis * thickness, hub + axis * thickness,
                   radius, colour, 30)
    batch.cylinder(hub - axis * thickness * 3, hub + axis * thickness * 3,
                   radius * 0.16, DARK_STEEL, 12)
    if not teeth:
        return
    reference = np.array([0.0, 0.0, 1.0])
    if abs(float(np.dot(reference, axis))) > 0.9:
        reference = np.array([1.0, 0.0, 0.0])
    basis_x = normalize(reference - axis * float(np.dot(reference, axis)))
    basis_y = np.cross(axis, basis_x)
    for index in range(36):
        angle = math.tau * index / 36
        point = hub + (basis_x * math.cos(angle) + basis_y * math.sin(angle)) * radius
        batch.sphere(point, thickness * 1.6, (0.85, 0.88, 0.92, 1.0), 3, 6)


# ----------------------------------------------------------------------
# Scenes
# ----------------------------------------------------------------------

def scene_cut_two_angles(app, opaque, transparent, p: float) -> None:
    """One strut, and the two completely different angles on it."""
    length = 9.0
    centre = np.array([0.0, 0.0, 2.4])
    reveal = ease_in_out(clamp(p * 1.4))

    # The stick, on edge, the way it sits in the dome.
    _prism(opaque, centre, (length, STOCK_T, STOCK_W), TIMBER)

    # The rip bevel runs the whole length, on one edge only.
    bevel = math.radians(PLAN.bevel_deg) * reveal
    top = centre[2] + STOCK_W * 0.5
    for side in (-1.0, 1.0):
        x = side * length * 0.5
        opaque.cylinder(np.array([x, -STOCK_T * 0.5, top]),
                        np.array([x, STOCK_T * 0.5 - math.tan(bevel) * STOCK_W,
                                  top - STOCK_W]),
                        0.035, CYAN, 6)
    opaque.cylinder(np.array([-length * 0.5, STOCK_T * 0.5, top]),
                    np.array([length * 0.5, STOCK_T * 0.5, top]),
                    0.05, CYAN, 8)

    # The mitre is at the ends, and it is a different animal entirely.
    for side in (-1.0, 1.0):
        x = side * length * 0.5
        swing = math.radians(PLAN.mitre_deg) * reveal * side
        opaque.cylinder(
            np.array([x, -STOCK_T * 0.6, centre[2] - STOCK_W * 0.5]),
            np.array([x - math.tan(swing) * STOCK_W * 1.2, -STOCK_T * 0.6,
                      centre[2] + STOCK_W * 0.5]),
            0.05, AMBER, 8)

    app.world_labels.extend([
        WorldLabel(np.array([0.0, STOCK_T * 0.5, top + 1.5]),
                   f"RIP BEVEL {PLAN.bevel_deg:.3f} deg\n"
                   "runs the whole length  -  TABLE SAW", (61, 211, 255)),
        WorldLabel(np.array([length * 0.5 + 1.6, 0.0, centre[2] + 2.4]),
                   f"END MITRE {PLAN.mitre_deg:.3f} deg\n"
                   "only at the ends  -  MITRE SAW", (255, 177, 62)),
        WorldLabel(np.array([0.0, 0.0, -0.9]),
                   "the bevel joins this triangle to the NEXT one;  "
                   "the mitre joins it to its OWN two",
                   (169, 188, 203)),
    ])


def scene_cut_machines(app, opaque, transparent, p: float) -> None:
    """What each machine can and cannot do."""
    reveal = clamp(p * 1.4)
    for index, (label, detail, colour, can) in enumerate((
        ("TABLE SAW", "rips along the length", CYAN, True),
        ("TABLE SAW", "cannot crosscut at 62 deg", CYAN, False),
        ("MITRE SAW", "crosscuts the ends", AMBER, True),
        ("MITRE SAW", "cannot rip at all", AMBER, False),
    )):
        if index / 4 > reveal:
            continue
        x = -8.4 + index * 5.6
        opaque.box((x, 0.0, 2.0), (3.4, 0.6, 2.6),
                   colour if can else (0.30, 0.16, 0.18, 1.0))
        if not can:
            for sign in (-1.0, 1.0):
                opaque.cylinder(np.array([x - 1.4 * sign, -0.4, 0.8]),
                                np.array([x + 1.4 * sign, -0.4, 3.2]),
                                0.10, RED, 6)
        app.world_labels.append(WorldLabel(
            np.array([x, 0.0, 4.0]), f"{label}\n{detail}",
            _rgb(colour) if can else (255, 87, 94)))
    app.world_labels.append(WorldLabel(
        np.array([0.0, 0.0, -1.0]),
        "this is why it takes two machines, not one", (111, 235, 155)))


def _table_saw(opaque, transparent, tilt_deg: float, feed: float,
               show_work: bool = True, fence_y: float = 1.55):
    """A table saw seen from the operator's left, blade tilted away."""
    _prism(opaque, (0.0, 0.0, TABLE_Z - 0.25), (15.0, 10.5, 0.5), DARK_STEEL)
    _prism(opaque, (0.0, 0.0, (TABLE_Z - 0.5) * 0.5),
           (11.0, 8.0, TABLE_Z - 0.5), (0.18, 0.21, 0.26, 1.0))
    # The slot the blade comes through.
    _prism(opaque, (0.0, 0.0, TABLE_Z + 0.02), (BLADE_R * 2.2, 0.30, 0.06),
           (0.06, 0.08, 0.11, 1.0))
    # Blade, tilted about the feed axis, most of it under the table.
    tilt = math.radians(tilt_deg)
    axis = np.array([0.0, math.cos(tilt), -math.sin(tilt)])
    hub = np.array([0.0, 0.0, TABLE_Z - BLADE_R * 0.62])
    _blade(opaque, hub, axis, BLADE_R)
    # Rip fence.
    _prism(opaque, (0.0, fence_y, TABLE_Z + 0.9), (14.5, 0.5, 1.8),
           (0.55, 0.58, 0.64, 1.0))
    if not show_work:
        return
    # The stick, lying flat, riding the fence, part way through.
    length = 11.0
    x = -length * 0.5 - 3.0 + feed * (length + 6.0)
    _prism(opaque, (x, fence_y - 0.35 - STOCK_W * 0.5,
                   TABLE_Z + STOCK_T * 0.5),
           (length, STOCK_W, STOCK_T), TIMBER)


def scene_cut_rip(app, opaque, transparent, p: float) -> None:
    """The table saw, tilted, ripping the bevel down the whole length."""
    feed = clamp(p * 1.25)
    _table_saw(opaque, transparent, PLAN.bevel_deg, feed)
    projection = blade_projection_in(PLAN.bevel_deg)
    app.world_labels.extend([
        WorldLabel(np.array([-3.4, -1.4, TABLE_Z + BLADE_R * 1.25]),
                   f"BLADE TILT {PLAN.bevel_deg:.3f} deg", (61, 211, 255)),
        WorldLabel(np.array([5.6, -2.4, TABLE_Z + 4.4]),
                   f"height {projection:.4f} in\n"
                   f"(square would be {STOCK_THICKNESS_IN:g})", (255, 177, 62)),
        WorldLabel(np.array([-6.6, -2.4, TABLE_Z + 3.4]),
                   "ONE PASS, FULL LENGTH", (111, 235, 155)),
        WorldLabel(np.array([0.0, -4.6, TABLE_Z - 0.4]),
                   "marked edge against the fence, every stick, no exceptions",
                   (169, 188, 203)),
    ])


def scene_cut_bevel_check(app, opaque, transparent, p: float) -> None:
    """Two offcuts, put together, reading twice the error."""
    close = ease_in_out(clamp((p - 0.15) / 0.65))
    check = BevelCheck(PLAN.bevel_deg, 180.0 - 2.0 * PLAN.bevel_deg)
    half = math.radians(PLAN.bevel_deg) * close
    for side in (-1.0, 1.0):
        yaw = math.degrees(half) * side
        centre = np.array([side * 3.2 * (1.0 - close * 0.62), 0.0, 2.4])
        _prism(opaque, centre, (6.0, STOCK_W, STOCK_T), TIMBER_CUT, yaw)
    app.world_labels.extend([
        WorldLabel(np.array([0.0, 0.0, 4.6]),
                   f"THE PAIR MUST READ {check.paired_angle_deg:.3f} deg",
                   (61, 211, 255)),
        WorldLabel(np.array([0.0, 0.0, 0.7]),
                   f"which is exactly the dome's own fold along this strut",
                   (111, 235, 155)),
        WorldLabel(np.array([0.0, 0.0, -0.9]),
                   "an error in the tilt shows up here doubled, "
                   "so it stops being invisible", (169, 188, 203)),
    ])


def _mitre_saw(opaque, transparent, swing_deg: float, drop: float,
               show_work: bool = True):
    """A mitre saw. The table swings, so the WORK turns under a fixed blade."""
    _prism(opaque, (0.0, 0.0, TABLE_Z - 0.3), (13.0, 9.5, 0.6), DARK_STEEL)
    opaque.disc(np.array([0.0, 0.0, TABLE_Z + 0.02]), 3.8,
                (0.30, 0.34, 0.40, 1.0), 36)
    # Fence and workpiece both turn with the table.
    _prism(opaque, (0.0, 2.6, TABLE_Z + 1.1), (12.0, 0.55, 2.2),
           (0.52, 0.56, 0.62, 1.0), swing_deg)
    if show_work:
        _prism(opaque, (0.0, 1.55, TABLE_Z + 0.05 + STOCK_W * 0.5),
               (10.0, STOCK_T, STOCK_W), TIMBER, swing_deg)
    # Column, arm and head do not turn.
    _prism(opaque, (0.0, 4.6, TABLE_Z + 3.4), (1.5, 1.5, 7.2),
           (0.34, 0.38, 0.44, 1.0))
    hub_z = TABLE_Z + 6.4 - drop * 4.9
    hub = np.array([0.0, 0.9, hub_z])
    opaque.cylinder(np.array([0.0, 4.6, TABLE_Z + 6.6]), hub, 0.34,
                    (0.44, 0.48, 0.54, 1.0), 10)
    _blade(opaque, hub, np.array([1.0, 0.0, 0.0]), BLADE_R)
    _prism(opaque, (1.4, 0.9, hub_z), (2.2, 1.6, 1.6), (0.20, 0.46, 0.30, 1.0))
    opaque.cylinder(hub + np.array([1.2, -1.4, 0.9]),
                    hub + np.array([1.2, -2.6, 1.3]), 0.22,
                    (0.14, 0.16, 0.20, 1.0), 8)


def scene_cut_mitre_limit(app, opaque, transparent, p: float) -> None:
    """The saw swung as far as it goes, still short of what is needed."""
    swing = TYPICAL_MITRE_SAW_MAX_DEG * ease_in_out(clamp(p * 1.5))
    _mitre_saw(opaque, transparent, swing, 0.0)
    app.world_labels.extend([
        WorldLabel(np.array([0.0, 0.0, 8.6]),
                   f"SWUNG TO ITS STOP: {swing:.1f} deg", (111, 235, 155)),
        WorldLabel(np.array([-5.6, -2.6, 2.6]),
                   f"THE DOME WANTS {PLAN.mitre_deg:.3f} deg", (255, 87, 94)),
        WorldLabel(np.array([5.2, -2.6, 2.2]),
                   "the scale simply does not go there", (169, 188, 203)),
    ])


def scene_cut_complement(app, opaque, transparent, p: float) -> None:
    """The same cut, taken from the other reference face."""
    turn = ease_in_out(clamp((p - 0.2) / 0.6))
    centre = np.array([0.0, 0.0, 2.6])
    # The angle, drawn once, with both ways of naming it.
    length = 5.6
    axis = _rotate_z(np.array([length, 0.0, 0.0]), 0.0)
    opaque.cylinder(centre - axis, centre + axis, 0.06, MUTED, 8)
    cut = _rotate_z(np.array([0.0, 0.0, 1.0]), 0.0) * 3.6
    swung = np.array([
        3.6 * math.sin(math.radians(PLAN.mitre_deg)), 0.0,
        3.6 * math.cos(math.radians(PLAN.mitre_deg))])
    opaque.cylinder(centre, centre + cut, 0.05, MUTED, 8)
    opaque.cylinder(centre, centre + swung, 0.10,
                    RED if turn < 0.5 else CYAN, 10)
    app.world_labels.extend([
        WorldLabel(centre + cut + np.array([0.0, 0.0, 0.8]),
                   "SQUARE", (169, 188, 203)),
        WorldLabel(centre + swung * 1.25,
                   f"{PLAN.mitre_deg:.3f} deg from square\n"
                   "= past every saw's stop", (255, 87, 94)),
        WorldLabel(centre + axis * 1.2 + np.array([0.0, 0.0, 0.6]),
                   f"{PLAN.complement_deg:.3f} deg from the blade\n"
                   "= the same cut, and easy", (61, 211, 255)),
        WorldLabel(np.array([0.0, 0.0, -0.8]),
                   "one angle, two names. build the sled to the second one.",
                   (111, 235, 155)),
    ])


def _sled(opaque, transparent, travel: float, fence_deg: float,
          show_work: bool = True, show_lap: bool = True):
    """A crosscut sled on the table saw, with the work on the angled fence."""
    y = -4.2 + travel * 8.4
    _prism(opaque, (0.0, 0.0, TABLE_Z - 0.25), (15.0, 10.5, 0.5), DARK_STEEL)
    _prism(opaque, (0.0, 0.0, (TABLE_Z - 0.5) * 0.5),
           (11.0, 8.0, TABLE_Z - 0.5), (0.18, 0.21, 0.26, 1.0))
    _prism(opaque, (0.0, 0.0, TABLE_Z + 0.02), (BLADE_R * 2.2, 0.30, 0.06),
           (0.06, 0.08, 0.11, 1.0))
    _blade(opaque, np.array([0.0, 0.0, TABLE_Z - BLADE_R * 0.70]),
           np.array([0.0, 1.0, 0.0]), BLADE_R)
    # Sled base and its two rails.
    _prism(opaque, (0.0, y, TABLE_Z + 0.32), (11.5, 7.5, 0.28), JIG)
    for offset in (-3.9, 3.9):
        _prism(opaque, (0.0, y + offset, TABLE_Z + 0.80), (11.5, 0.7, 1.7),
               (0.34, 0.27, 0.19, 1.0))
    # The angled fence: this is the part that carries the whole job.
    _prism(opaque, (0.0, y - 0.6, TABLE_Z + 0.95), (11.0, 0.55, 1.0),
           (0.58, 0.42, 0.22, 1.0), fence_deg)
    if show_lap:
        # The relief lap: the blade must finish the cut flush, so the
        # fence is cut away exactly where the blade passes.
        _prism(opaque, (0.0, y - 0.6, TABLE_Z + 0.95), (1.1, 0.9, 1.05),
               (0.10, 0.12, 0.15, 1.0), fence_deg)
    if not show_work:
        return
    # The stick, butted to the stop, one end projecting over the lap.
    offset = _rotate_z(np.array([2.6, 0.0, 0.0]), fence_deg)
    _prism(opaque, (offset[0], y - 0.6 + offset[1] + 0.5,
                    TABLE_Z + 0.46 + STOCK_W * 0.5),
           (9.0, STOCK_T, STOCK_W), TIMBER, fence_deg)
    stop = _rotate_z(np.array([7.4, 0.0, 0.0]), fence_deg)
    _prism(opaque, (stop[0], y - 0.6 + stop[1] + 0.5, TABLE_Z + 0.9),
           (0.9, 1.4, 1.1), GREEN, fence_deg)


def scene_cut_sled_build(app, opaque, transparent, p: float) -> None:
    """The sled itself, before any work goes on it."""
    _sled(opaque, transparent, 0.18, PLAN.sled_fence_deg,
          show_work=False, show_lap=False)
    app.world_labels.extend([
        WorldLabel(np.array([0.0, -2.2, 2.6]),
                   f"FENCE AT {PLAN.sled_fence_deg:.3f} deg TO THE BLADE",
                   (61, 211, 255)),
        WorldLabel(np.array([-5.6, 2.4, 2.4]),
                   "runners in the mitre slots\nno slop, no story", (169, 188, 203)),
        WorldLabel(np.array([0.0, 0.0, -1.0]),
                   "build it and prove it before you cut a part you care about",
                   (111, 235, 155)),
    ])


def scene_cut_fivecut(app, opaque, transparent, p: float) -> None:
    """The five-cut method: make an invisible error measurable."""
    reveal = clamp(p * 1.3)
    checks = ((0.001, GREEN), (0.005, AMBER), (0.020, RED))
    for index, (difference, colour) in enumerate(checks):
        if index / len(checks) > reveal:
            continue
        check = FiveCutCheck(20.0, 2.0 + difference, 2.0)
        x = -6.0 + index * 6.0
        opaque.box((x, 0.0, 1.9), (3.4, 0.6, 2.6), colour)
        app.world_labels.append(WorldLabel(
            np.array([x, 0.0, 3.9]),
            f"{difference:.3f} in over 20 in\n"
            f"fence off {check.fence_error_deg:.4f} deg\n"
            f"{check.error_over_a_strut:.5f} in per strut", _rgb(colour)))
    app.world_labels.append(WorldLabel(
        np.array([0.0, 0.0, -0.9]),
        "four cuts multiply the error by four; the fifth strip shows it",
        (169, 188, 203)))


def scene_cut_lap(app, opaque, transparent, p: float) -> None:
    """Why the fence has to be cut away where the blade passes."""
    _sled(opaque, transparent, 0.30, PLAN.sled_fence_deg, show_lap=True)
    app.world_labels.extend([
        WorldLabel(np.array([0.0, -2.0, 2.9]),
                   "RELIEF LAP\nthe blade finishes the cut flush",
                   (255, 177, 62)),
        WorldLabel(np.array([4.4, -0.4, 2.4]),
                   "STOP BLOCK\nlength comes from here, not a tape",
                   (111, 235, 155)),
        WorldLabel(np.array([-5.4, 1.2, 2.4]),
                   "one end projects past the fence", (61, 211, 255)),
    ])


def scene_cut_first_end(app, opaque, transparent, p: float) -> None:
    """The cut itself, all the way through."""
    travel = ease_in_out(clamp(p * 1.2))
    _sled(opaque, transparent, travel, PLAN.sled_fence_deg)
    app.world_labels.extend([
        WorldLabel(np.array([0.0, -1.0, TABLE_Z + 4.6]),
                   f"ONE PASS  -  fence {PLAN.sled_fence_deg:.3f} deg,  "
                   f"travel {sled_capacity_in(PLAN.mitre_deg):.2f} in",
                   (61, 211, 255)),
        WorldLabel(np.array([-6.4, -3.4, TABLE_Z + 2.4]),
                   "bevelled edge down\nagainst the fence", (255, 177, 62)),
        WorldLabel(np.array([0.0, -4.8, TABLE_Z - 0.5]),
                   "let the blade stop before you lift the work",
                   (169, 188, 203)),
    ])


def scene_cut_turn(app, opaque, transparent, p: float) -> None:
    """Turn the strut end for end. Do not flip it face over face."""
    phase = clamp(p * 1.4)
    turning = phase < 0.5
    angle = 180.0 * ease_in_out(clamp(phase / 0.5)) if turning else 180.0
    centre = np.array([-4.4, 0.0, 2.6])
    _prism(opaque, centre, (7.0, STOCK_T, STOCK_W), TIMBER, angle)
    opaque.cylinder(centre + np.array([0.0, 0.0, STOCK_W * 0.5 + 0.1]),
                    centre + np.array([0.0, 0.0, STOCK_W * 0.5 + 0.9]),
                    0.05, CYAN, 6)
    # The wrong one, mirrored, next to it.
    wrong = np.array([4.4, 0.0, 2.6])
    _prism(opaque, wrong, (7.0, STOCK_T, STOCK_W), (0.42, 0.24, 0.24, 1.0))
    opaque.cylinder(wrong + np.array([0.0, 0.0, -STOCK_W * 0.5 - 0.1]),
                    wrong + np.array([0.0, 0.0, -STOCK_W * 0.5 - 0.9]),
                    0.05, RED, 6)
    for sign in (-1.0, 1.0):
        opaque.cylinder(wrong + np.array([-1.8 * sign, -0.5, -1.4]),
                        wrong + np.array([1.8 * sign, -0.5, 1.4]),
                        0.09, RED, 6)
    app.world_labels.extend([
        WorldLabel(centre + np.array([0.0, 0.0, 2.4]),
                   "TURN end for end\nbevel stays on the same side",
                   (61, 211, 255)),
        WorldLabel(wrong + np.array([0.0, 0.0, 2.4]),
                   "FLIP face over face\nmirrored part, will not close",
                   (255, 87, 94)),
    ])


def scene_cut_batch(app, opaque, transparent, p: float) -> None:
    """Cut every end that shares a setting before changing anything."""
    reveal = clamp(p * 1.25)
    for index, plan in enumerate(PLANS):
        if index / len(PLANS) > reveal:
            continue
        x = -9.0 + index * 3.6
        height = 0.6 + plan.ends / 60.0 * 3.4
        colour = (CYAN, AMBER, GREEN, PURPLE, RED, WHITE)[index % 6]
        opaque.box((x, 0.0, height * 0.5 + 0.2), (2.3, 0.9, height), colour)
        app.world_labels.append(WorldLabel(
            np.array([x, 0.0, height + 0.9]),
            f"{plan.name}\nmitre {plan.mitre_deg:.1f}\n"
            f"bevel {plan.bevel_deg:.1f}\nx{plan.ends} ends", _rgb(colour)))
    app.world_labels.append(WorldLabel(
        np.array([0.0, 0.0, -1.0]),
        f"{len(PLANS)} setting changes for "
        f"{sum(item.ends for item in PLANS)} ends, not one per part",
        (111, 235, 155)))


def scene_cut_dryfit(app, opaque, transparent, p: float) -> None:
    """Three struts on a flat floor. Either it closes or it does not."""
    close = ease_in_out(clamp(p * 1.3))
    radius = 4.6
    corners = [np.array([radius * math.cos(math.tau * i / 3 + math.pi / 2),
                         radius * math.sin(math.tau * i / 3 + math.pi / 2),
                         0.4]) for i in range(3)]
    for index in range(3):
        a = corners[index]
        b = corners[(index + 1) % 3]
        gap = (1.0 - close) * 0.9
        direction = normalize(b - a)
        _prism(opaque, tuple((a + b) * 0.5 + direction * 0.0),
               (float(np.linalg.norm(b - a)) - gap, STOCK_T, STOCK_W),
               TIMBER,
               math.degrees(math.atan2(direction[1], direction[0])))
    for corner in corners:
        opaque.sphere(corner, 0.16 + (1.0 - close) * 0.2,
                      GREEN if close > 0.92 else AMBER, 4, 9)
    app.world_labels.append(WorldLabel(
        np.array([0.0, 0.0, 3.4]),
        "IT CLOSES, OR THE SETTINGS ARE WRONG" if close > 0.92
        else "CLOSING...", (111, 235, 155) if close > 0.92 else (255, 177, 62)))
    app.world_labels.append(WorldLabel(
        np.array([0.0, 0.0, -1.2]),
        "three sticks lost, not two hundred and forty", (169, 188, 203)))


def scene_cut_failures(app, opaque, transparent, p: float) -> None:
    """The five ways this goes wrong."""
    reveal = clamp(p * 1.3)
    colours = (RED, AMBER, PURPLE, CYAN, GREEN)
    for index, (title, _) in enumerate(FAILURES):
        if index / len(FAILURES) > reveal:
            continue
        x = -8.8 + index * 4.4
        opaque.box((x, 0.0, 1.7), (2.6, 0.55, 2.6), colours[index % len(colours)])
        for sign in (-1.0, 1.0):
            opaque.cylinder(np.array([x - 1.1 * sign, -0.4, 0.6]),
                            np.array([x + 1.1 * sign, -0.4, 2.8]),
                            0.08, (0.75, 0.16, 0.18, 1.0), 6)
        app.world_labels.append(WorldLabel(
            np.array([x, 0.0, 3.7]), title.upper(),
            _rgb(colours[index % len(colours)])))


def scene_cut_recap(app, opaque, transparent, p: float) -> None:
    """The whole sequence, once, in order."""
    reveal = clamp(p * 1.2)
    order = (("RIP TO WIDTH", CYAN), ("MARK THE EDGE", AMBER),
             ("TILT AND RIP", GREEN), ("BUILD THE SLED", PURPLE),
             ("LAP AND STOP", RED), ("CUT, TURN, CUT", WHITE),
             ("DRY-FIT ONE", GREEN))
    for index, (label, colour) in enumerate(order):
        if index / len(order) > reveal:
            continue
        x = -10.2 + index * 3.4
        opaque.box((x, 0.0, 1.4), (2.5, 0.5, 1.6), colour)
        if index:
            opaque.arrow(np.array([x - 1.7, 0.0, 1.4]),
                         np.array([x - 1.3, 0.0, 1.4]), 0.05, MUTED)
        app.world_labels.append(WorldLabel(
            np.array([x, 0.0, 2.7]), label, _rgb(colour)))
    app.world_labels.append(WorldLabel(
        np.array([0.0, 0.0, -1.0]),
        "two machines, one jig, six settings, two hundred and forty ends",
        (111, 235, 155)))


SCENES = {
    "cut_two_angles": scene_cut_two_angles,
    "cut_machines": scene_cut_machines,
    "cut_rip": scene_cut_rip,
    "cut_bevel_check": scene_cut_bevel_check,
    "cut_mitre_limit": scene_cut_mitre_limit,
    "cut_complement": scene_cut_complement,
    "cut_sled_build": scene_cut_sled_build,
    "cut_fivecut": scene_cut_fivecut,
    "cut_lap": scene_cut_lap,
    "cut_first_end": scene_cut_first_end,
    "cut_turn": scene_cut_turn,
    "cut_batch": scene_cut_batch,
    "cut_dryfit": scene_cut_dryfit,
    "cut_failures": scene_cut_failures,
    "cut_recap": scene_cut_recap,
}


def cut_equations(app, stage: str) -> list[str]:
    """Live settings for the cutting lesson."""
    if stage in ("cut_two_angles", "cut_machines"):
        return [
            f"rip bevel  = {PLAN.bevel_deg:.3f} deg   (table saw tilt)",
            f"end mitre  = {PLAN.mitre_deg:.3f} deg   (from square)",
            f"sled fence = {PLAN.sled_fence_deg:.3f} deg   (from the blade)",
        ]
    if stage in ("cut_rip", "cut_bevel_check"):
        return [
            f"blade tilt   = {PLAN.bevel_deg:.3f} deg",
            f"blade height = {blade_projection_in(PLAN.bevel_deg):.4f} in",
            f"paired offcuts must read "
            f"{180.0 - 2.0 * PLAN.bevel_deg:.3f} deg",
            f"saw tilts to {TABLE_SAW_MAX_TILT_DEG:g} deg, so this is easy",
        ]
    if stage in ("cut_mitre_limit", "cut_complement"):
        return [
            f"needed  = {PLAN.mitre_deg:.3f} deg from square",
            f"saw stops at {TYPICAL_MITRE_SAW_MAX_DEG:g} deg",
            f"complement = {PLAN.complement_deg:.3f} deg from the blade",
            "same cut, different reference face",
        ]
    if stage in ("cut_sled_build", "cut_lap", "cut_first_end"):
        return [
            f"fence to blade = {PLAN.sled_fence_deg:.3f} deg",
            f"blade travel   = {sled_capacity_in(PLAN.mitre_deg):.3f} in",
            f"stock          = {STOCK_WIDTH_IN:g} x {STOCK_THICKNESS_IN:g} in",
        ]
    if stage == "cut_fivecut":
        return [
            f"{d:.3f} in over 20 in -> "
            f"{FiveCutCheck(20.0, 2.0 + d, 2.0).fence_error_deg:.4f} deg"
            for d in (0.001, 0.005, 0.020)
        ]
    if stage == "cut_batch":
        return [
            f"{plan.name}  mitre {plan.mitre_deg:6.3f}  "
            f"bevel {plan.bevel_deg:5.3f}  x{plan.ends}"
            for plan in PLANS
        ]
    return []


CHAPTERS: tuple[Chapter, ...] = (
    Chapter(
        "two_angles", "01", "Two angles, one stick",
        "Every strut carries two completely different angles, on two machines.",
        (
            "This is the hardest operation in the whole dome, and it is worth being",
            "precise about why. Every strut carries two angles that have nothing to do",
            "with each other. There is a bevel that runs the entire length of the stick,",
            "and there is a mitre at each end. The bevel decides how this triangle meets",
            "the triangle next door. The mitre decides how this strut meets the other two",
            "struts of its own triangle. Get one right and the other wrong and you have a",
            "part that looks perfect on the bench and fits absolutely nothing.",
        ),
        ("rip bevel: the whole length", "end mitre: only the ends",
         "different jobs, different machines"),
        24.0, (62.0, 22.0, 23.0), "cut_two_angles",
    ),
    Chapter(
        "machines", "02", "Why it takes two saws",
        "Each machine can only do the cut the other one cannot.",
        (
            "A table saw rips along the length of a board and cannot sensibly crosscut a",
            "long stick at sixty degrees. A mitre saw crosscuts ends and cannot rip at",
            "all. That is the entire reason this job needs two machines. It is not",
            "fussiness and it is not showing off. There is no single setup on either saw",
            "that produces a finished strut.",
        ),
        ("table saw: rips, cannot crosscut at 62 deg",
         "mitre saw: crosscuts, cannot rip"),
        18.0, (90.0, 15.0, 19.0), "cut_machines",
    ),
    Chapter(
        "width", "03", "One width, one session",
        "Every angle after this is measured from the edge of the board.",
        (
            "Before any angle at all: rip every stick to one width, in one session, with",
            "the fence untouched. Every angle downstream is measured from the edge of the",
            "board, so if the boards are not identical in width, nothing after this point",
            "can be right, and no amount of care at the mitre saw will rescue it. This is",
            "the least interesting step and the one that quietly decides the outcome.",
        ),
        ("uniform width = the master reference",
         "one session, fence untouched"),
        18.0, (256.0, 13.0, 24.0), "cut_rip",
    ),
    Chapter(
        "mark", "04", "Mark the mating edge",
        "Only one long edge gets the bevel. Mark it before anything moves.",
        (
            "Only one long edge of each strut gets bevelled: the one that will lie",
            "against the neighbouring triangle. Mark that edge on every stick in the pile",
            "before a single one goes near the blade. Bevelling the wrong edge is the",
            "most common way to manufacture a large quantity of mirror-image firewood,",
            "and it is completely invisible until you try to assemble.",
        ),
        ("one edge only", "mark the whole pile first"),
        17.0, (48.0, 24.0, 21.0), "cut_two_angles",
    ),
    Chapter(
        "tilt", "05", "Setting the blade tilt",
        "Do not trust the saw's own scale.",
        (
            "Now the table saw. Tilt the blade to the bevel for this strut class. Do not",
            "trust the scale cast into the saw; it is a starting point, not a",
            "measurement. And set the blade height after the tilt, never before, because",
            "a tilted blade has to travel further to cross the same thickness and a height",
            "set square will not come through.",
        ),
        ("set the tilt first, the height second",
         "a tilted blade needs more height"),
        18.0, (250.0, 11.0, 22.0), "cut_rip",
    ),
    Chapter(
        "prove_tilt", "06", "Proving the tilt",
        "Rip two offcuts, put them together, and read twice the error.",
        (
            "Here is how you know the tilt is right before you commit the pile. Rip two",
            "offcuts at the setting, then put the two cut faces together and measure the",
            "pair. If the tilt is correct the pair closes to exactly the fold the dome",
            "wants along that strut. And because the pair carries both errors, anything",
            "too small to see in a single piece is obvious in the double.",
        ),
        ("the pair reads the dome's own dihedral",
         "error shows up doubled"),
        19.0, (70.0, 20.0, 21.0), "cut_bevel_check",
    ),
    Chapter(
        "rip", "07", "The rip",
        "One pass, full length, marked edge against the fence.",
        (
            "Featherboard before the blade, push stick past it, marked edge against the",
            "fence for every stick without exception. One pass, the full length. This is",
            "the easy half of the job: the bevel the dome needs is nowhere near the",
            "forty-five degrees the saw can tilt to, so the machine is never the limit",
            "here. Consistency is.",
        ),
        ("one pass, full length", "the tilt is well inside the saw's range"),
        18.0, (264.0, 12.0, 24.0), "cut_rip",
    ),
    Chapter(
        "limit", "08", "The saw runs out of scale",
        "Swing it to its stop and it is still not enough.",
        (
            "Now the ends, and now the problem. Swing the mitre saw as far as it goes.",
            "A common saw stops at about fifty degrees from square. The mitres this dome",
            "wants start at fifty-five and a half and run past sixty-two. Not one of the",
            "settings this dome needs is on the scale. The saw is not badly made. The",
            "angle is simply outside what a mitre saw is built to do.",
        ),
        ("saw stops near 50 deg", "the dome wants 55.6 to 62.2 deg"),
        19.0, (56.0, 20.0, 34.0), "cut_mitre_limit",
    ),
    Chapter(
        "complement", "09", "One angle, two names",
        "Measure it from the blade instead of from square.",
        (
            "The way out is not a trick, it is a change of reference. An angle measured",
            "from square and its complement measured from the blade describe the same",
            "cut. Sixty-two degrees from square is twenty-seven point eight degrees from",
            "the blade. So stop trying to make the saw's table reach the number, and",
            "build a fence that holds the work at the complement instead.",
        ),
        ("62.215 from square = 27.785 from the blade",
         "same cut, different reference"),
        19.0, (72.0, 18.0, 18.0), "cut_complement",
    ),
    Chapter(
        "sled", "10", "The sled",
        "A crosscut sled with its fence built to the complement.",
        (
            "So the ends get cut on a crosscut sled on the table saw. Two runners in the",
            "mitre slots with no slop at all, a flat base, and a fence set to the",
            "complement angle referenced off the blade. Build the sled first. Prove it.",
            "Only then cut a part you care about. Every strut in the dome passes over",
            "this one fence, so every error built into it is an error repeated two",
            "hundred and forty times.",
        ),
        ("runners with no slop", "fence referenced off the blade",
         "one fence, 240 ends"),
        21.0, (78.0, 36.0, 36.0), "cut_sled_build",
    ),
    Chapter(
        "fivecut", "11", "Proving the fence",
        "The five-cut method makes an invisible error measurable.",
        (
            "You cannot check a fence this critical with a combination square. Use the",
            "five-cut method: cut a scrap four times, rotating it a quarter turn between",
            "cuts, then slice a fifth strip off and measure that strip at both ends. The",
            "four cuts multiply the fence error by four, so a difference of five",
            "thousandths across a twenty inch strip means the fence is out by less than",
            "four thousandths of a degree. That is a level of proof you simply cannot get",
            "by eye.",
        ),
        ("four cuts multiply the error by four",
         "0.005 in over 20 in = 0.0036 deg"),
        23.0, (90.0, 15.0, 19.0), "cut_fivecut",
    ),
    Chapter(
        "lap", "12", "The relief lap and the stop block",
        "The blade has to finish the cut flush, so the fence gets cut away.",
        (
            "Two details on the sled that decide whether it works. First, the strut sits",
            "against the fence with one end projecting past it, and the blade has to",
            "finish that cut flush, so the fence is cut away at the blade path. Cut that",
            "lap once, with the sled in the exact position it will always be used in.",
            "Second, length comes from a stop block clamped to the sled, never from a",
            "pencil line. Two hundred and forty ends measured individually will drift.",
            "Two hundred and forty ends against one block will not.",
        ),
        ("relief lap: cut once, in position",
         "stop block, never a tape measure"),
        23.0, (72.0, 34.0, 32.0), "cut_lap",
    ),
    Chapter(
        "first_end", "13", "The first end",
        "Bevelled edge down, butted to the stop, one pass all the way through.",
        (
            "Bevelled edge down and against the fence. Marked face up. Strut butted hard",
            "to the stop block, the end projecting over the lap. One pass, all the way",
            "through, and let the blade come to a stop before you lift the work. That is",
            "the compound cut: the sled is holding the mitre and the stick is already",
            "carrying its bevel, so both angles arrive on the same pass.",
        ),
        ("bevel down, marked face up", "butted to the stop, one pass"),
        20.0, (80.0, 32.0, 36.0), "cut_first_end",
    ),
    Chapter(
        "turn", "14", "Turn it, do not flip it",
        "The second end is not a mirror of the first.",
        (
            "Now the second end, and this is where a whole afternoon can go. The second",
            "end is not a mirror of the first. Rotate the strut end for end about its own",
            "long axis, the way the sled was built for, so the bevelled edge stays on the",
            "same side of the dome. If you flip it face over face instead, you mirror the",
            "part. It will look completely correct lying on the bench and it will refuse",
            "to close a triangle, and you will not find out until assembly.",
        ),
        ("turn end for end about the long axis",
         "flipping face over face mirrors the part"),
        22.0, (66.0, 20.0, 23.0), "cut_turn",
    ),
    Chapter(
        "batch", "15", "Batch by setting",
        "Six setting changes, not two hundred and forty.",
        (
            "Cut every end that shares a setting before you change anything. Changing a",
            "setting is where error enters the job, so change it as few times as the work",
            "allows. Six setups cover all two hundred and forty ends in the dome. Sorted",
            "by setting that is six careful changes. Sorted by triangle it is a change",
            "every couple of minutes for two days, and every one of them a chance to be",
            "slightly wrong.",
        ),
        ("6 setups cover 240 ends", "batch by setting, never by triangle"),
        20.0, (90.0, 16.0, 20.0), "cut_batch",
    ),
    Chapter(
        "dryfit", "16", "Dry-fit one triangle",
        "Three struts on a flat floor, no fasteners.",
        (
            "Before you cut the rest of the pile, dry-assemble one triangle. Three struts",
            "on a flat floor, no fasteners at all. If it closes with no gap at any corner",
            "and lies flat, your settings are right and you can cut with confidence. If",
            "it does not, you have lost three sticks instead of the whole pile, and you",
            "still have the setting in front of you to correct.",
        ),
        ("no gap at any corner, and it lies flat",
         "three sticks lost, not 240"),
        20.0, (46.0, 42.0, 21.0), "cut_dryfit",
    ),
    Chapter(
        "failures", "17", "The five ways it goes wrong",
        "Every one of them looks correct until assembly.",
        (
            "Five failures, and they share a nasty property: every one produces a part",
            "that looks right. Bevel on the wrong edge. Setting the sled to the mitre",
            "instead of its complement. Flipping instead of turning. A stop block that",
            "has walked under repeated impact. And a blade set to a height that was",
            "correct before you tilted it. Check the block against a reference stick",
            "every twenty cuts, and check the height after every tilt change.",
        ),
        ("all five produce parts that look correct",
         "check the stop every 20 cuts"),
        22.0, (90.0, 15.0, 20.0), "cut_failures",
    ),
    Chapter(
        "recap", "18", "The whole sequence",
        "Two machines, one jig, six settings, two hundred and forty ends.",
        (
            "Rip everything to one width. Mark the mating edge. Tilt, prove the tilt with",
            "a pair of offcuts, and rip the bevel full length. Build the sled to the",
            "complement and prove it with the five-cut method. Cut the relief lap and set",
            "the stop block. Then cut, turn, cut, batching by setting, and dry-fit one",
            "triangle before you trust the rest. Two machines, one jig, six settings, two",
            "hundred and forty ends. Do it in that order and the hardest part of the dome",
            "becomes the most repetitive part instead.",
        ),
        ("rip -> mark -> tilt -> rip -> sled -> lap -> cut -> turn -> dry-fit",),
        24.0, (90.0, 16.0, 22.0), "cut_recap",
    ),
)


CUTS_LESSON = Lesson(
    key="cuts",
    brand="HUBLESS / THE COMPOUND CUT",
    title="The Compound Cut, Both Machines",
    chapters=CHAPTERS,
    scenes=SCENES,
    equations=cut_equations,
    selftest=validate_sawing,
    report=sawing_report,
    snapshot_prefix="cuts",
)
