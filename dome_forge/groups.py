"""Pentagons and hourglasses: the sub-assemblies a 2V dome really breaks into.

Nobody builds a dome one triangle at a time in their head. They think in
the groups the shape naturally falls into, and this module finds both of
them straight from the geometry rather than from a table someone typed:

* A **pentagon** is the five isosceles triangles that ring a five-way
  vertex, meeting at the apex between their two short sides. There are
  six of them on a hemisphere.
* An **hourglass** is two equilateral triangles that meet at exactly one
  vertex -- point to point, waist in the middle. There are ten, and they
  sit in the gaps between the pentagons. Because an equilateral has
  three corners, one triangle belongs to more than one hourglass; a
  joint is a property of the *waist*, not of the triangles.

The waist is the interesting part of an hourglass, because two mitered
points touching tip to tip is not a joint on its own -- it has to be
made into one. The joint library below covers the ways builders
actually do that.
"""

from __future__ import annotations

import math
from collections import defaultdict
from dataclasses import dataclass
from functools import lru_cache

import numpy as np

from presenter.world import Batch
from two_v_demo.geometry import build_demo_geometry, normalize


@dataclass(frozen=True)
class Pentagon:
    index: int
    vertex: int
    faces: tuple[int, ...]


@dataclass(frozen=True)
class Hourglass:
    index: int
    waist: int
    faces: tuple[int, int]


@lru_cache(maxsize=1)
def _topology():
    geo = build_demo_geometry()
    faces = geo.hemisphere_faces
    class_by_edge = {tuple(sorted(edge)): name
                     for edge, name in zip(geo.edges, geo.edge_class_by_edge)}

    def edge_names(face):
        return [class_by_edge[tuple(sorted((int(face[i]),
                                            int(face[(i + 1) % 3]))))]
                for i in range(3)]

    equilateral = {i for i, face in enumerate(faces)
                   if edge_names(face).count("LONG") == 3}
    at_vertex: dict[int, list[int]] = defaultdict(list)
    for index, face in enumerate(faces):
        for vertex in face:
            at_vertex[int(vertex)].append(index)

    pentagons = []
    for vertex, face_list in sorted(at_vertex.items()):
        if len(face_list) == 5 and not (set(face_list) & equilateral):
            pentagons.append(Pentagon(len(pentagons), vertex,
                                      tuple(sorted(face_list))))

    hourglasses = []
    for vertex, face_list in sorted(at_vertex.items()):
        pair = sorted(i for i in face_list if i in equilateral)
        if len(pair) != 2:
            continue
        # Two triangles that share more than a single vertex are edge
        # neighbours, not an hourglass.
        shared = set(faces[pair[0]].tolist()) & set(faces[pair[1]].tolist())
        if len(shared) == 1:
            hourglasses.append(Hourglass(len(hourglasses), vertex,
                                         (pair[0], pair[1])))
    return tuple(pentagons), tuple(hourglasses), equilateral


def pentagons() -> tuple[Pentagon, ...]:
    return _topology()[0]


def hourglasses() -> tuple[Hourglass, ...]:
    return _topology()[1]


def equilateral_faces() -> set[int]:
    return _topology()[2]


# ---------------------------------------------------------------------------
# How the two points are actually joined
# ---------------------------------------------------------------------------

@dataclass(frozen=True)
class WaistJoint:
    key: str
    label: str
    blurb: str


WAIST_JOINTS: tuple[WaistJoint, ...] = (
    WaistJoint("none", "Bare tips",
               "The two points simply touch. Fine while you are dry-"
               "fitting, but it carries nothing -- pick one of the "
               "others before it holds weight."),
    WaistJoint("banding", "Metal banding",
               "Steel strap wrapped around both tips and tensioned. "
               "Fast, cheap, needs no precise machining, and pulls the "
               "two points together rather than relying on fasteners in "
               "end grain."),
    WaistJoint("wood_brace", "Square wooden braces",
               "Square blocks bridging the two sides that form each "
               "point, then bolted through to the block opposite. The "
               "load goes into the sides of the triangles instead of "
               "into their fragile tips."),
    WaistJoint("monolithic", "Monolithic waist",
               "Both points are one continuous piece -- cut, cast, or "
               "laminated as a single part. Strongest and stiffest, and "
               "the least forgiving if a dimension is off."),
    WaistJoint("steel_plate", "Steel gusset plate",
               "A flat plate laid over the waist and bolted into both "
               "triangles. Easy to fabricate and easy to inspect."),
    WaistJoint("bolted_lap", "Bolted lap",
               "The tips are cut back to half thickness and overlapped "
               "so they finish flush, then bolted through the lap."),
)

JOINT_BY_KEY = {joint.key: joint for joint in WAIST_JOINTS}
JOINT_KEYS = tuple(joint.key for joint in WAIST_JOINTS)


@dataclass(frozen=True)
class PentagonPreset:
    key: str
    label: str
    fills: tuple[str, ...]
    strut: str | None = None


# Ready-made pentagons. The five fills are applied in the order the
# triangles come back from the geometry, so a pattern like "one door, rest
# solid" always lands the same way round.
PENTAGON_PRESETS: tuple[PentagonPreset, ...] = (
    PentagonPreset("glazed", "All glazed",
                   ("polycarbonate",) * 5),
    PentagonPreset("glass_cap", "Glass cap", ("glass",) * 5),
    PentagonPreset("solar_cap", "Solar cap", ("solar",) * 5),
    PentagonPreset("solid", "Solid shell", ("wood_sheet",) * 5),
    PentagonPreset("planked", "Planked", ("wood_planks",) * 5),
    PentagonPreset("shingled", "Shingled", ("shingles",) * 5),
    PentagonPreset("skylight", "Skylight + solid",
                   ("glass", "wood_sheet", "wood_sheet", "wood_sheet",
                    "wood_sheet")),
    PentagonPreset("vented", "Vent pair",
                   ("vent", "polycarbonate", "vent", "polycarbonate",
                    "polycarbonate")),
    PentagonPreset("alternating", "Alternating glass and solid",
                   ("glass", "wood_sheet", "glass", "wood_sheet", "glass")),
    PentagonPreset("entry", "Entry pentagon",
                   ("door", "wood_sheet", "wood_sheet", "polycarbonate",
                    "polycarbonate")),
    PentagonPreset("mirror_cluster", "Mirror cluster", ("mirror",) * 5),
    PentagonPreset("collector", "Fresnel collector",
                   ("fresnel", "mirror", "mirror", "mirror", "mirror")),
    PentagonPreset("aircon", "Plant pentagon",
                   ("ac_unit", "vent", "metal_sheet", "metal_sheet",
                    "metal_sheet")),
    PentagonPreset("insulated", "Insulated", ("sip",) * 5),
    PentagonPreset("splitlog_solid", "Split-log solid",
                   ("wood_planks",) * 5, strut="log_half"),
    PentagonPreset("light_frame", "Light 2x2 frame",
                   ("fabric",) * 5, strut="lumber_2x2"),
)

PRESET_BY_KEY = {preset.key: preset for preset in PENTAGON_PRESETS}


def _waist_frame(ctx, hourglass: Hourglass):
    """A local frame at the waist: outward, along the hourglass, across it."""
    waist = ctx.points[hourglass.waist]
    outward = normalize(waist)
    a = ctx.points[ctx.faces[hourglass.faces[0]]].mean(axis=0)
    b = ctx.points[ctx.faces[hourglass.faces[1]]].mean(axis=0)
    axis = b - a
    axis = axis - outward * float(np.dot(axis, outward))
    axis = normalize(axis)
    across = normalize(np.cross(outward, axis))
    return waist, outward, axis, across


def emit_waist(batch: Batch, ctx, hourglass: Hourglass, joint_key: str,
               tint_of, *, size: float = 1.0, alpha: float = 1.0) -> None:
    """Draw whatever holds the two points together."""
    if joint_key == "none":
        return
    waist, outward, axis, across = _waist_frame(ctx, hourglass)
    steel = tint_of("steel", alpha)
    timber = tint_of("timber", alpha)
    reach = 0.30 * size
    depth = 0.10 * size

    if joint_key == "banding":
        # Straps encircling the joined tips, one either side of the waist.
        for side in (-1.0, 1.0):
            centre = waist + axis * (reach * 0.45 * side)
            steps = 18
            ring = []
            for i in range(steps + 1):
                angle = math.tau * i / steps
                ring.append(centre
                            + outward * (math.cos(angle) * depth * 0.9)
                            + across * (math.sin(angle) * depth * 1.5))
            for i in range(steps):
                batch.cylinder(ring[i], ring[i + 1], 0.012 * size, steel,
                               sides=4)

    elif joint_key == "wood_brace":
        # Square blocks across the sides that form each point, bolted to
        # the block facing them.
        for side in (-1.0, 1.0):
            centre = (waist + axis * (reach * 0.62 * side)
                      - outward * depth * 0.45)
            batch.box(centre, (0.16 * size, 0.30 * size, 0.16 * size),
                      timber)
        for offset in (-0.55, 0.55):
            start = waist + across * (0.11 * size) + axis * (reach * offset)
            end = waist - across * (0.11 * size) + axis * (reach * offset)
            batch.cylinder(start, end, 0.012 * size, steel, sides=6)

    elif joint_key == "monolithic":
        # One continuous piece through the waist: a lens spanning both
        # tips, with no seam in the middle at all.
        top = waist + outward * (depth * 0.30)
        bottom = waist - outward * (depth * 0.75)
        for side in (-1.0, 1.0):
            tip = waist + axis * (reach * 1.15 * side)
            left = waist + across * (0.17 * size)
            right = waist - across * (0.17 * size)
            batch.tri(tip, left, top, timber)
            batch.tri(tip, top, right, timber)
            batch.tri(tip, right, bottom, timber)
            batch.tri(tip, bottom, left, timber)

    elif joint_key == "steel_plate":
        lift = outward * (depth * 0.18)
        corners = [
            waist + axis * (reach * 1.05) + lift,
            waist + across * (0.19 * size) + lift,
            waist - axis * (reach * 1.05) + lift,
            waist - across * (0.19 * size) + lift,
        ]
        thickness = outward * (0.012 * size)
        for face_pts, normal in ((corners, outward),
                                 ([p - thickness for p in corners], -outward)):
            batch.tri(face_pts[0], face_pts[1], face_pts[2], steel, normal)
            batch.tri(face_pts[0], face_pts[2], face_pts[3], steel, normal)
        for i in range(4):
            j = (i + 1) % 4
            batch.quad(corners[i], corners[i] - thickness,
                       corners[j] - thickness, corners[j], steel)
        for side in (-1.0, 1.0):
            at = waist + axis * (reach * 0.6 * side) + lift
            batch.cylinder(at + outward * 0.02 * size,
                           at - outward * 0.05 * size,
                           0.014 * size, tint_of("charcoal", alpha), sides=6)

    elif joint_key == "bolted_lap":
        # Each tip halved in thickness and overlapped, so the pair
        # finishes at the full thickness of one piece.
        for index, side in enumerate((-1.0, 1.0)):
            shift = outward * (depth * 0.22 * (1 if index == 0 else -1))
            centre = waist + axis * (reach * 0.42 * side) + shift
            batch.box(centre, (0.34 * size, 0.26 * size, 0.07 * size), timber)
        batch.cylinder(waist + outward * (depth * 0.6),
                       waist - outward * (depth * 0.6),
                       0.016 * size, steel, sides=6)


def group_centre(ctx, faces) -> np.ndarray:
    points = [ctx.points[ctx.faces[i]].mean(axis=0) for i in faces]
    return np.mean(points, axis=0)
