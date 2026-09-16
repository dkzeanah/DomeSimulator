"""The tree, and everything a chainsaw makes of it, as visual objects.

A standing pine, felled with a real face notch and back cut, pivoting over its hinge
and settling on the ground; limbed; bucked into sections; and every section split
into eight wedges at once, pushed apart into an exploded view. Each stage is a knob
from 0 to 1, so a chapter animates the whole harvest by moving four numbers.

The tree is the book's tree. Its usable length, butt and top diameters, bucking
length, section count and split count all come from :data:`book_math.BOOK_TREE`,
so the object on screen is the object the numbers on screen describe. A wedge in the
exploded view is drawn by :func:`lesson_wedge._wedge_prism`, the same prism every
wedge film uses, so the wedges here cannot look different from the wedges there.

Only the parts no calculation needs are drawing choices -- how tall the crown is, how
deep the notch is cut, how far apart the pieces fly -- and those are gathered in
:data:`DRAWING` with the reason each is what it is. None of them is ever printed.
"""

from __future__ import annotations

import math
from typing import Mapping

import numpy as np

from . import book_math as bm
from .geometry import normalize
from .lesson_wedge import BARK, WOOD, WOOD_DARK, _face, _wedge_prism
from .render_kit import TriangleBatch, clamp, ease_in_out, smoothstep
from .timber import _noise
from .visual_objects import Knob, Stage, VisualObject, register


PLAN = bm.BOOK_TREE

DRAWING: dict[str, tuple[float, str]] = {
    "stump_ft": (1.0, "Height of the felling cut. A stump about knee-low is what "
                      "a felling guide asks for; it is never quoted."),
    "tip_ft": (70.0, "Overall height of the drawn pine. The author's notes put the "
                     "trees he cuts at sixty to eighty feet."),
    "crown_base_ft": (40.0, "Lowest live whorl. Forest-grown pines self-prune "
                            "their lower branches; the usable trunk sits below."),
    "crown_radius_ft": (7.0, "Half the crown's width, for the silhouette only."),
    "notch_depth": (0.30, "Fraction of the diameter the face notch removes. The "
                          "usual guidance is a quarter to a third."),
    "gap_ft": (2.2, "Widest gap between flying sections in the exploded view."),
    "push": (1.9, "How far each wedge flies out, in trunk radii. Far enough that "
                  "the eight read as eight from across the stage."),
}


def _d(key: str) -> float:
    return DRAWING[key][0]


PINE = (0.21, 0.47, 0.26, 1.0)
PINE_DARK = (0.14, 0.35, 0.19, 1.0)
END_GRAIN = (0.80, 0.64, 0.42, 1.0)
RING_TONE = (0.66, 0.50, 0.30, 1.0)
KERF_DARK = (0.12, 0.08, 0.05, 1.0)
SAWDUST = (0.78, 0.67, 0.46, 1.0)
DUST = (0.62, 0.55, 0.44, 0.35)


# ----------------------------------------------------------------------
# The tree's shape, in feet, standing at the origin
# ----------------------------------------------------------------------

def usable_top_ft(plan=PLAN) -> float:
    return _d("stump_ft") + plan.usable_length_ft


def trunk_radius_ft(height_ft: float, plan=PLAN) -> float:
    """Radius of the stem at a height: the plan's taper, a flare, a thin tip."""
    stump = _d("stump_ft")
    butt = plan.butt_diameter_in / 24.0
    top = plan.top_diameter_in / 24.0
    if height_ft <= stump:
        flare = 1.0 - height_ft / stump
        return butt * (1.0 + 0.28 * flare * flare)
    if height_ft <= usable_top_ft(plan):
        return plan.diameter_at(height_ft - stump) / 24.0
    span = max(1e-6, _d("tip_ft") - usable_top_ft(plan))
    fraction = clamp((height_ft - usable_top_ft(plan)) / span)
    return top + (0.04 - top) * fraction


def _ring(height: float, sides: int, notch_depth_ft: float = 0.0,
          notch_top: float = 0.0, notch_base: float = 0.0,
          plan=PLAN) -> np.ndarray:
    """One ring of trunk surface, flattened on +X where the notch has been cut."""
    radius = trunk_radius_ft(height, plan)
    points = []
    for index in range(sides):
        angle = math.tau * index / sides
        x, y = radius * math.cos(angle), radius * math.sin(angle)
        if notch_depth_ft > 0.0 and notch_base <= height <= notch_top:
            # Deepest at the notch floor, nothing at its top: the sloping face.
            span = max(1e-6, notch_top - notch_base)
            cut = notch_depth_ft * (1.0 - (height - notch_base) / span)
            x = min(x, radius - cut)
        points.append((x, y, height))
    return np.asarray(points, dtype=np.float64)


def _skin(batch: TriangleBatch, rings: list[np.ndarray], seed: int) -> None:
    """Quads between consecutive rings, wound to face outward."""
    for level in range(len(rings) - 1):
        low, high = rings[level], rings[level + 1]
        sides = len(low)
        for index in range(sides):
            nxt = (index + 1) % sides
            corners = (low[index], low[nxt], high[nxt], high[index])
            centre = sum(corners) / 4.0
            outward = np.array([centre[0], centre[1], 0.0])
            if float(np.linalg.norm(outward)) < 1e-9:
                continue
            shade = 0.82 + 0.34 * _noise(seed + level * 31, index)
            colour = (BARK[0] * shade, BARK[1] * shade, BARK[2] * shade, 1.0)
            _face(batch, corners, colour, outward)


def _cap(batch: TriangleBatch, ring: np.ndarray, normal, colour) -> None:
    """Close a ring with a fan, facing ``normal``, with rings drawn on the grain."""
    centre = ring.mean(axis=0)
    normal = np.asarray(normal, dtype=np.float64)
    sides = len(ring)
    for index in range(sides):
        a, b = ring[index], ring[(index + 1) % sides]
        wound = (centre, a, b) if float(np.dot(np.cross(a - centre, b - centre),
                                               normal)) > 0 else (centre, b, a)
        batch.triangle(*wound, colour, normalize(normal))
    # Growth rings: two smaller fans a hair proud of the face, darker then lighter.
    for fraction, tone, lift in ((0.66, RING_TONE, 0.004), (0.33, END_GRAIN, 0.008)):
        inner = centre + (ring - centre) * fraction + normal * lift
        for index in range(sides):
            a, b = inner[index], inner[(index + 1) % sides]
            wound = (centre + normal * lift, a, b) if float(np.dot(
                np.cross(a - centre, b - centre), normal)) > 0 else \
                (centre + normal * lift, b, a)
            batch.triangle(*wound, tone, normalize(normal))


def _crown(batch: TriangleBatch, alpha: float, plan=PLAN) -> None:
    """Whorls of foliage: overlapping cones, widest at the bottom, a spire on top."""
    base = _d("crown_base_ft")
    tip = _d("tip_ft")
    tiers = 9
    for tier in range(tiers):
        share = tier / tiers
        height = base + (tip - base) * share
        spread = _d("crown_radius_ft") * (1.0 - share) ** 0.85 + 0.6
        rise = (tip - base) / tiers * 2.1
        jitter = (_noise(4301, tier) - 0.5) * 0.5
        colour = PINE if tier % 2 == 0 else PINE_DARK
        colour = (colour[0], colour[1], colour[2], alpha)
        batch.cone(np.array([jitter, -jitter * 0.6, height - rise * 0.25]),
                   np.array([0.0, 0.0, height + rise]),
                   spread * (0.92 + 0.16 * _noise(4302, tier)), colour, 11)
    # Dead lower branches, stubbed off below the live crown, as forest pines are.
    stub = (BARK[0], BARK[1], BARK[2], alpha)
    for index in range(7):
        height = base * (0.62 + 0.36 * _noise(4400, index))
        angle = math.tau * _noise(4401, index)
        radius = trunk_radius_ft(height, plan)
        root = np.array([radius * math.cos(angle), radius * math.sin(angle), height])
        reach = 1.2 + 1.8 * _noise(4402, index)
        end = root + np.array([math.cos(angle), math.sin(angle), 0.35]) * reach
        batch.cylinder(root, end, 0.06, stub, 5)


# ----------------------------------------------------------------------
# Felling: the notch, the back cut, the fall and the settle
# ----------------------------------------------------------------------

FELL_PHASES = {
    "notch": (0.00, 0.22),
    "back_cut": (0.24, 0.42),
    "fall": (0.42, 0.90),
    "settle": (0.90, 1.00),
}


def _phase(value: float, name: str) -> float:
    start, end = FELL_PHASES[name]
    return clamp((value - start) / (end - start))


def fall_angle_deg(fell: float) -> float:
    """How far over the tree is: slow to start, fast at the end, a small rebound.

    A tree leaves vertical almost reluctantly and hits the ground at speed; the ease
    here is the shape of that, not a solution of the pendulum.
    """
    u = _phase(fell, "fall")
    angle = 90.0 * (1.0 - math.cos(u * math.pi * 0.5)) ** 1.15
    settle = _phase(fell, "settle")
    if settle > 0.0:
        angle = 90.0 - 2.5 * math.sin(math.pi * settle) * (1.0 - settle)
    return angle


def hinge_x_ft(fell: float, plan=PLAN) -> float:
    """Where the hinge sits: the inner edge of the face notch."""
    radius = trunk_radius_ft(_d("stump_ft"), plan)
    depth = _d("notch_depth") * 2.0 * radius * _phase(fell, "notch")
    return radius - depth


def _rotate_y(batch: TriangleBatch, pivot, angle_deg: float, drop: float) -> None:
    """Turn a batch about the Y axis through ``pivot``, then lower it by ``drop``."""
    if not batch.vertices:
        return
    data = np.asarray(batch.vertices, dtype=np.float64).reshape(-1, 10)
    angle = math.radians(angle_deg)
    c, s = math.cos(angle), math.sin(angle)
    rotation = np.array([[c, 0.0, s], [0.0, 1.0, 0.0], [-s, 0.0, c]])
    pivot = np.asarray(pivot, dtype=np.float64)
    data[:, 0:3] = (data[:, 0:3] - pivot) @ rotation.T + pivot
    data[:, 2] -= drop
    data[:, 3:6] = data[:, 3:6] @ rotation.T
    batch.vertices[:] = data.ravel().tolist()


def _scale(batch: TriangleBatch, factor: float) -> TriangleBatch:
    if batch.vertices and factor != 1.0:
        data = np.asarray(batch.vertices, dtype=np.float64).reshape(-1, 10)
        data[:, 0:3] *= factor
        batch.vertices[:] = data.ravel().tolist()
    return batch


def _sawdust(batch: TriangleBatch, origin, direction, progress: float, seed: int,
             count: int = 16, reach: float = 2.2) -> None:
    """Chips thrown from a cut, each on its own arc. A pure function of progress."""
    if progress <= 0.0 or progress >= 1.0:
        return
    origin = np.asarray(origin, dtype=np.float64)
    direction = normalize(np.asarray(direction, dtype=np.float64))
    side = normalize(np.cross(direction, np.array([0.0, 0.0, 1.0])))
    for index in range(count):
        birth = _noise(seed, index) * 0.8
        age = (progress - birth) / 0.2
        if not 0.0 < age < 1.0:
            continue
        speed = reach * (0.6 + 0.6 * _noise(seed + 1, index))
        spread = (_noise(seed + 2, index) - 0.5) * 1.4
        velocity = direction * speed + side * spread + np.array([0.0, 0.0, 0.9])
        point = origin + velocity * age + np.array([0.0, 0.0, -1.6 * age * age])
        if point[2] <= 0.02:
            continue
        batch.sphere(point, 0.05, SAWDUST, 3, 5)


def _tree(opaque: TriangleBatch, transparent: TriangleBatch, stage: Stage,
          fell: float, limb: float, units: float, show_icon: bool,
          plan=PLAN) -> dict:
    """The standing or falling tree and its stump, in drawing units."""
    stump = _d("stump_ft")
    radius = trunk_radius_ft(stump, plan)
    notch_depth = _d("notch_depth") * 2.0 * radius * _phase(fell, "notch")
    notch_top = stump + 0.9 * radius
    sides = 16

    # The stump never moves.
    static, moving = TriangleBatch(), TriangleBatch()
    low_rings = [_ring(h, sides, plan=plan) for h in (0.0, stump * 0.5, stump)]
    _skin(static, low_rings, 9100)
    _cap(static, low_rings[-1], (0.0, 0.0, 1.0), END_GRAIN)

    # Everything above the cut goes over together.
    heights = [stump, stump + 0.001]
    heights += list(np.linspace(stump + 0.06, notch_top, 6))
    heights += list(np.arange(notch_top + 1.5, usable_top_ft(plan), 2.0))
    heights += [usable_top_ft(plan)]
    heights += list(np.arange(usable_top_ft(plan) + 2.5, _d("tip_ft"), 3.0))
    heights += [_d("tip_ft")]
    rings = [_ring(h, sides, notch_depth, notch_top, stump, plan) for h in heights]
    _skin(moving, rings, 9200)
    _cap(moving, rings[0], (0.0, 0.0, -1.0), END_GRAIN)

    crown_alpha = 1.0 - smoothstep(limb)
    if crown_alpha > 0.01:
        if crown_alpha >= 0.999:
            _crown(moving, 1.0, plan)
        else:
            crown = TriangleBatch()
            _crown(crown, crown_alpha, plan)
            pivot = np.array([hinge_x_ft(fell, plan), 0.0, stump])
            angle = fall_angle_deg(fell)
            drop = _drop(fell, plan)
            _rotate_y(crown, pivot, angle, drop)
            transparent.vertices.extend(_scale(crown, units).vertices)

    # The back cut: a dark kerf around the far side, growing through the phase.
    back = _phase(fell, "back_cut")
    back_height = stump + 0.12 * radius
    if 0.0 < back and fell < FELL_PHASES["fall"][0] + 0.05:
        arc = int(round(back * 8)) + 1
        for index in range(-arc, arc):
            a0 = math.pi + index * math.pi / 16.0
            a1 = a0 + math.pi / 16.0
            r = trunk_radius_ft(back_height, plan) * 1.012
            p0 = np.array([r * math.cos(a0), r * math.sin(a0), back_height])
            p1 = np.array([r * math.cos(a1), r * math.sin(a1), back_height])
            static.cylinder(p0, p1, 0.035, KERF_DARK, 4)

    pivot = np.array([hinge_x_ft(fell, plan), 0.0, stump])
    angle = fall_angle_deg(fell)
    drop = _drop(fell, plan)
    _rotate_y(moving, pivot, angle, drop)

    _sawdust(static, (radius + 0.2, 0.0, stump + 0.3 * radius), (1.0, 0.3, 0.0),
             _phase(fell, "notch"), 9301)
    _sawdust(static, (-radius - 0.2, 0.0, back_height), (-1.0, -0.4, 0.0),
             back, 9302)

    # Dust where the crown lands.
    settle = _phase(fell, "settle")
    tip_reach = _d("tip_ft") - stump
    impact = np.array([pivot[0] + tip_reach * 0.8, 0.0, 0.4])
    if settle > 0.0:
        for index in range(9):
            offset = np.array([(_noise(9400, index) - 0.5) * 9.0,
                               (_noise(9401, index) - 0.5) * 6.0, 0.0])
            size = 1.2 + settle * (2.5 + 2.0 * _noise(9402, index))
            fade = DUST[3] * (1.0 - settle)
            transparent.sphere(impact * units + offset * units,
                               size * units, (DUST[0], DUST[1], DUST[2], fade), 4, 8)

    opaque.vertices.extend(_scale(static, units).vertices)
    opaque.vertices.extend(_scale(moving, units).vertices)

    # The chainsaw, at the cut it is making. It shakes while it cuts and fades
    # out as the tree commits to the fall.
    notch = _phase(fell, "notch")
    icon_alpha = 0.0
    icon_side = 1.0
    if 0.0 < notch < 1.0 or (0.0 < back < 1.0) or \
            FELL_PHASES["back_cut"][1] <= fell < FELL_PHASES["fall"][0] + 0.12:
        rise = smoothstep(clamp(fell / 0.04))
        leave = 1.0 - smoothstep(clamp((fell - FELL_PHASES["fall"][0]) / 0.12))
        icon_alpha = rise * leave
        icon_side = 1.0 if fell < FELL_PHASES["back_cut"][0] else -1.0
    icon_point = np.array([icon_side * (radius + 1.4), 0.0, stump + 0.6 * radius])
    if show_icon and icon_alpha > 0.01:
        shake = 5.0 * math.sin(fell * 420.0) + 3.0 * math.sin(fell * 1030.0)
        # Aimed at the trunk, so the bar points into the cut from either side.
        trunk = np.array([0.0, 0.0, stump + 0.6 * radius])
        stage.icon(icon_point * units, "chainsaw", 104.0, None, icon_alpha, shake,
                   toward=trunk * units)

    height_now = stump + 0.45 * (_d("tip_ft") - stump)
    centre = _rotated_point(np.array([0.0, 0.0, height_now]), pivot, angle, drop)
    top_now = _rotated_point(np.array([0.0, 0.0, _d("tip_ft")]), pivot, angle, drop)
    return {
        "fell_point": np.array([radius, 0.0, stump]) * units,
        "saw": icon_point * units,
        "centre_of_mass": centre * units,
        "crown_top": top_now * units,
        "impact": impact * units,
    }


def _drop(fell: float, plan=PLAN) -> float:
    """How far the fallen trunk sinks from the hinge to lie on the ground."""
    stump = _d("stump_ft")
    lying_axis = stump + hinge_x_ft(1.0, plan)
    rest = trunk_radius_ft(stump + 0.5, plan)
    return (lying_axis - rest) * smoothstep(_phase(fell, "settle"))


def _rotated_point(point, pivot, angle_deg: float, drop: float) -> np.ndarray:
    angle = math.radians(angle_deg)
    c, s = math.cos(angle), math.sin(angle)
    rel = np.asarray(point, dtype=np.float64) - pivot
    x = rel[0] * c + rel[2] * s
    z = -rel[0] * s + rel[2] * c
    return np.array([x + pivot[0], rel[1] + pivot[1], z + pivot[2] - drop])


# ----------------------------------------------------------------------
# The fallen log: bucked into sections, every section split at once
# ----------------------------------------------------------------------

def log_layout(plan=PLAN) -> tuple[float, float]:
    """(where the butt end lies, the height of the log's axis) once it is down."""
    stump = _d("stump_ft")
    x_start = hinge_x_ft(1.0, plan)
    axis = trunk_radius_ft(stump + 0.5, plan)
    return x_start, axis


def _section_tube(batch: TriangleBatch, x0: float, x1: float, radius: float,
                  axis_z: float, seed: int) -> None:
    sides = 16
    rings = []
    for x in (x0, x1):
        rings.append(np.asarray([(x, radius * math.cos(math.tau * i / sides),
                                  axis_z + radius * math.sin(math.tau * i / sides))
                                 for i in range(sides)]))
    for index in range(sides):
        nxt = (index + 1) % sides
        corners = (rings[0][index], rings[0][nxt], rings[1][nxt], rings[1][index])
        centre = sum(corners) / 4.0
        shade = 0.82 + 0.34 * _noise(seed, index)
        _face(batch, corners, (BARK[0] * shade, BARK[1] * shade, BARK[2] * shade,
                               1.0), np.array([0.0, centre[1], centre[2] - axis_z]))
    _cap(batch, rings[0], (-1.0, 0.0, 0.0), END_GRAIN)
    _cap(batch, rings[1], (1.0, 0.0, 0.0), END_GRAIN)


def _log(opaque: TriangleBatch, stage: Stage, buck: float, explode: float,
         units: float, show_icon: bool, plan=PLAN) -> dict:
    """The usable trunk on the ground, cut to length and split, in drawing units."""
    x_start, rest_axis = log_layout(plan)
    length = plan.section_length_ft
    count = plan.sections
    sectors = plan.sectors
    cuts = max(1, count - 1)
    scratch = TriangleBatch()
    anchors: dict[str, np.ndarray] = {}

    # Sections part a kerf's width as each cut is made, then fly apart.
    cut_window = 0.8 / cuts
    for index in range(count):
        e = clamp((explode - 0.035 * index) / max(0.2, 1.0 - 0.035 * (count - 1)))
        e = ease_in_out(e)
        gap = _d("gap_ft") * e
        made = sum(1 for c in range(min(index, cuts))
                   if buck >= (c + 1) * cut_window)
        x0 = x_start + index * length + made * 0.12 + index * gap
        x1 = x0 + length - 0.06
        mid_height = _d("stump_ft") + (index + 0.5) * length
        radius = trunk_radius_ft(mid_height, plan)
        lift = e * _d("push") * radius * 1.1
        axis = rest_axis + lift
        centre = np.array([(x0 + x1) * 0.5, 0.0, axis])
        anchors[f"section_{index + 1}"] = centre * units
        if e <= 0.002:
            _section_tube(scratch, x0, x1, radius, axis, 9500 + index)
            continue
        push = e * _d("push") * radius
        for sector in range(sectors):
            angle = math.tau * (sector + 0.5) / sectors
            out = np.array([0.0, math.cos(angle), math.sin(angle)])
            start = np.array([x0, 0.0, axis]) + out * push
            end = np.array([x1, 0.0, axis]) + out * push
            _wedge_prism(scratch, start, end, out, radius * 0.985, segments=6,
                         angle_deg=360.0 / sectors)

    # Kerf marks and chips at each cut while it is being made, and the saw there.
    for cut in range(cuts):
        begin = cut * cut_window
        progress = clamp((buck - begin) / cut_window)
        x_cut = x_start + (cut + 1) * length
        radius = trunk_radius_ft(_d("stump_ft") + (cut + 1) * length, plan)
        top = np.array([x_cut, 0.0, rest_axis + radius + 1.0])
        if 0.0 < progress < 1.0 and explode <= 0.0:
            scratch.cylinder(np.array([x_cut - 0.04, 0.0, rest_axis]),
                             np.array([x_cut + 0.04, 0.0, rest_axis]),
                             radius * 1.01 * min(1.0, 0.3 + progress), KERF_DARK, 14)
            _sawdust(scratch, np.array([x_cut, -radius, rest_axis]),
                     (0.0, -1.0, 0.2), progress, 9600 + cut, 10, 1.6)
            if show_icon:
                fade = smoothstep(clamp(progress * 4.0)) * \
                    (1.0 - smoothstep(clamp((progress - 0.75) * 4.0)))
                shake = 5.0 * math.sin(progress * 240.0)
                stage.icon(top * units, "chainsaw", 88.0, None, fade, -90.0 + shake)

    opaque.vertices.extend(_scale(scratch, units).vertices)
    span_end = x_start + count * length
    anchors.update({
        "log_start": np.array([x_start, 0.0, rest_axis]) * units,
        "log_end": np.array([span_end, 0.0, rest_axis]) * units,
        "log_mid": np.array([(x_start + span_end) * 0.5, 0.0,
                             rest_axis + explode * _d("push")]) * units,
    })
    return anchors


# ----------------------------------------------------------------------
# Registration
# ----------------------------------------------------------------------

_UNITS = Knob("units_per_ft", "Drawing scale", 0.25, 0.01, 2.0, "units/ft",
              "Scene units per real foot. At the default a 70-foot pine is 17.5 "
              "units tall, which fits the stage.")
_ICON = Knob("icon", "Show the chainsaw", 1.0, 0.0, 1.0, "",
             "1 pins the chainsaw pictogram to every cut while it is being made.")


def _draw_pine(stage: Stage, k: Mapping) -> dict:
    opaque, transparent = TriangleBatch(), TriangleBatch()
    anchors = _tree(opaque, transparent, stage, k["fell"], k["limb"],
                    k["units_per_ft"], k["icon"] >= 0.5)
    stage.splice(opaque)
    stage.splice(transparent, transparent=True)
    return anchors


def _draw_log(stage: Stage, k: Mapping) -> dict:
    opaque = TriangleBatch()
    anchors = _log(opaque, stage, k["buck"], k["explode"], k["units_per_ft"],
                   k["icon"] >= 0.5)
    stage.splice(opaque)
    return anchors


def _draw_harvest(stage: Stage, k: Mapping) -> dict:
    """The whole harvest: tree until it is down and limbed, then the log."""
    opaque, transparent = TriangleBatch(), TriangleBatch()
    units = k["units_per_ft"]
    on_log = k["buck"] > 0.0 or k["explode"] > 0.0
    if on_log:
        anchors = _tree(opaque, transparent, stage, 1.0, 1.0, units, False)
        # Keep only the stump: the log is drawn by the sections from here on.
        opaque.vertices.clear()
        stump_rings = [_ring(h, 16) for h in (0.0, _d("stump_ft") * 0.5,
                                             _d("stump_ft"))]
        stump = TriangleBatch()
        _skin(stump, stump_rings, 9100)
        _cap(stump, stump_rings[-1], (0.0, 0.0, 1.0), END_GRAIN)
        opaque.vertices.extend(_scale(stump, units).vertices)
        anchors.update(_log(opaque, stage, k["buck"], k["explode"], units,
                            k["icon"] >= 0.5))
    else:
        anchors = _tree(opaque, transparent, stage, k["fell"], k["limb"], units,
                        k["icon"] >= 0.5)
        anchors.update({name: point for name, point in
                        _log(TriangleBatch(), Stage(TriangleBatch(),
                                                    TriangleBatch()),
                             0.0, 0.0, units, False).items()
                        if name.startswith("log_")})
    stage.splice(opaque)
    stage.splice(transparent, transparent=True)
    return anchors


_FELL = Knob("fell", "Felling", 0.0, 0.0, 1.0, "",
             "0 standing. Then the face notch, the back cut, the fall over the "
             "hinge, and at 1 the trunk lying on the ground.", animate=True)
_LIMB = Knob("limb", "Limbing", 0.0, 0.0, 1.0, "",
             "Fades the crown and the top away, leaving the usable trunk.",
             animate=True)
_BUCK = Knob("buck", "Bucking", 0.0, 0.0, 1.0, "",
             "Each cut to length is made in turn, from the butt to the top.",
             animate=True)
_EXPLODE = Knob("explode", "Exploded view", 0.0, 0.0, 1.0, "",
                "Every section splits into eight at once and the pieces fly apart.",
                animate=True)

register(VisualObject(
    "pine_tree", "Pine tree, standing or felled", "wood",
    "The book's pine: its usable trunk, taper and crown, felled with a face notch "
    "and a back cut, the chainsaw pictogram at the fell line, falling over the "
    "hinge and settling on the ground.",
    (_FELL, _LIMB, _UNITS, _ICON), _draw_pine, "new", 18.0,
    ("tree", "pine", "trunk", "crown", "stump", "bark", "felling", "notch",
     "hinge", "chainsaw")))

register(VisualObject(
    "log_sections", "Log, bucked and split", "wood",
    "The usable trunk on the ground, cut into the plan's sections and every "
    "section split into the plan's sectors, pushed apart into an exploded view.",
    (_BUCK, _EXPLODE, _UNITS, _ICON), _draw_log, "new", 7.0,
    ("log", "section", "slice", "bucking", "splitting", "wedge", "sector", "kerf",
     "sawdust")))

register(VisualObject(
    "harvest", "The harvest, tree to wedges", "processes",
    "The whole sequence as one object: fell, limb, buck and explode. Drive the "
    "four knobs in order across a chapter.",
    (_FELL, _LIMB, _BUCK, _EXPLODE, _UNITS, _ICON), _draw_harvest, "new", 12.0,
    ("harvest", "felling", "limbing", "bucking", "splitting", "ripping")))


def validate_forest() -> None:
    """The drawn tree must be the planned tree, and every stage must draw."""
    stump = _d("stump_ft")
    plan = PLAN
    # The taper the drawing uses is the taper the arithmetic uses.
    for fraction in (0.0, 0.25, 0.5, 1.0):
        height = stump + plan.usable_length_ft * fraction
        drawn = trunk_radius_ft(height) * 24.0
        planned = plan.diameter_at(plan.usable_length_ft * fraction)
        assert abs(drawn - planned) < 1e-9, (fraction, drawn, planned)
    # A fallen, bucked log is exactly the plan's sections, end to end.
    anchors = _log(TriangleBatch(), Stage(TriangleBatch(), TriangleBatch()),
                   0.0, 0.0, 1.0, False)
    span = anchors["log_end"][0] - anchors["log_start"][0]
    assert abs(span - plan.sections * plan.section_length_ft) < 1e-9, span
    assert len([name for name in anchors if name.startswith("section_")]) \
        == plan.sections
    # The fall is monotone until the settle, and ends lying down.
    angles = [fall_angle_deg(v) for v in np.linspace(0.0, 0.9, 40)]
    assert all(b >= a - 1e-9 for a, b in zip(angles, angles[1:])), angles
    assert abs(fall_angle_deg(1.0) - 90.0) < 1e-6
    assert fall_angle_deg(0.0) == 0.0
    # An exploded log is made of wedges: sections x sectors of them.
    probe = TriangleBatch()
    _log(probe, Stage(TriangleBatch(), TriangleBatch()), 1.0, 1.0, 1.0, False)
    whole = TriangleBatch()
    _log(whole, Stage(TriangleBatch(), TriangleBatch()), 1.0, 0.0, 1.0, False)
    assert len(probe.vertices) > len(whole.vertices), "splitting drew nothing new"
    # The saw appears while cutting and is gone once the tree is down.
    for fell, expect in ((0.1, True), (0.3, True), (0.95, False)):
        stage = Stage(TriangleBatch(), TriangleBatch())
        _tree(TriangleBatch(), TriangleBatch(), stage, fell, 0.0, 1.0, True)
        assert bool(stage.icons) == expect, (fell, stage.icons)
