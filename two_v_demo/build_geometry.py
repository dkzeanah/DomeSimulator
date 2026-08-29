"""Everything a 2V dome needs that is about *building* it, not about spheres.

:mod:`two_v_demo.geometry` answers "what shape is it".  This module answers
"what do I cut, at what angle, in what order, and what happens when I get
it slightly wrong".  Nothing here is a rule of thumb: every angle is
measured off the same 2V mesh the rest of the package draws.
"""

from __future__ import annotations

import math
from dataclasses import dataclass
from functools import lru_cache

import numpy as np

from .geometry import (
    PHI,
    DomeMeasurements,
    build_demo_geometry,
    fit_measurements,
    normalize,
)


# ----------------------------------------------------------------------
# Rings: the courses the dome is actually raised in
# ----------------------------------------------------------------------

@dataclass(frozen=True)
class Ring:
    """One level of hubs, from the ground up."""

    index: int
    name: str
    height_factor: float
    radius_factor: float
    hub_count: int
    hubs: tuple[int, ...]

    def height(self, radius: float) -> float:
        return self.height_factor * radius

    def diameter(self, radius: float) -> float:
        return 2.0 * self.radius_factor * radius


@lru_cache(maxsize=1)
def dome_rings() -> tuple[Ring, ...]:
    """Group the hemisphere's hubs into level rings, base first."""
    geometry = build_demo_geometry()
    used = sorted({index for edge in geometry.hemisphere_edges for index in edge})
    levels: list[float] = []
    for index in used:
        height = float(geometry.vertices[index][2])
        if not any(abs(height - value) <= 1e-9 for value in levels):
            levels.append(height)
    levels.sort()
    names = ("base ring", "second ring", "third ring", "fourth ring", "apex")
    rings: list[Ring] = []
    for order, level in enumerate(levels):
        members = tuple(
            index for index in used
            if abs(float(geometry.vertices[index][2]) - level) <= 1e-9
        )
        radius = max(
            float(np.linalg.norm(geometry.vertices[index][:2])) for index in members
        )
        name = names[order] if order < len(names) - 1 else "apex"
        if order == len(levels) - 1:
            name = "apex"
        rings.append(Ring(order, name, level, radius, len(members), members))
    return tuple(rings)


# ----------------------------------------------------------------------
# Strut end cuts and panel bevels
# ----------------------------------------------------------------------

@dataclass(frozen=True)
class StrutDetail:
    """One strut class, described the way a shop needs it."""

    name: str
    factor: float
    dome_count: int
    central_angle_deg: float

    @property
    def axial_angle_deg(self) -> float:
        """Angle between the strut and the surface at its own end.

        A chord that subtends a central angle ``theta`` leaves the sphere's
        tangent plane at exactly ``theta / 2``.  This is the angle a hub
        plate has to tip, or a timber strut end has to be cut back to, so
        that the member points along the surface instead of into it.
        """
        return self.central_angle_deg * 0.5

    def centre_length(self, radius: float) -> float:
        return self.factor * radius

    def cut_length(self, radius: float, deduction: float) -> float:
        return self.factor * radius - deduction


@lru_cache(maxsize=1)
def strut_details() -> tuple[StrutDetail, ...]:
    geometry = build_demo_geometry()
    return tuple(
        StrutDetail(
            name=item.name,
            factor=item.factor,
            dome_count=item.hemisphere_count,
            central_angle_deg=item.central_angle_deg,
        )
        for item in geometry.edge_classes
    )


@dataclass(frozen=True)
class DihedralClass:
    """One measured fold angle between two neighbouring panels."""

    strut_class: str
    count: int
    dihedral_deg: float

    @property
    def bevel_deg(self) -> float:
        """Half the fold, which is what each panel edge is planed to."""
        return (180.0 - self.dihedral_deg) * 0.5


@lru_cache(maxsize=1)
def dihedral_classes() -> tuple[DihedralClass, ...]:
    """Fold angle along every interior strut of the dome half."""
    geometry = build_demo_geometry()
    faces_at_edge: dict[tuple[int, int], list[np.ndarray]] = {}
    for face in geometry.hemisphere_faces:
        corners = [int(value) for value in face]
        points = geometry.vertices[corners]
        normal = normalize(np.cross(points[1] - points[0], points[2] - points[0]))
        if float(np.dot(normal, points.mean(axis=0))) < 0.0:
            normal = -normal
        for position in range(3):
            a, b = corners[position], corners[(position + 1) % 3]
            faces_at_edge.setdefault((a, b) if a < b else (b, a), []).append(normal)

    class_of = dict(zip(geometry.edges, geometry.edge_class_by_edge))
    groups: dict[tuple[str, int], int] = {}
    for edge, normals in faces_at_edge.items():
        if len(normals) != 2:
            continue  # A rim strut has only one panel on it.
        cosine = float(np.clip(float(np.dot(normals[0], normals[1])), -1.0, 1.0))
        fold = 180.0 - math.degrees(math.acos(cosine))
        key = (class_of[edge], int(round(fold * 1e6)))
        groups[key] = groups.get(key, 0) + 1
    return tuple(
        DihedralClass(name, count, angle / 1e6)
        for (name, angle), count in sorted(groups.items())
    )


# ----------------------------------------------------------------------
# Hubs
# ----------------------------------------------------------------------

@dataclass(frozen=True)
class HubType:
    """One kind of joint: how many struts, of which classes, at what splay."""

    name: str
    count: int
    strut_count: int
    strut_classes: tuple[str, ...]
    splay_deg: tuple[float, ...]
    ring_name: str

    @property
    def class_summary(self) -> str:
        short = sum(1 for name in self.strut_classes if name == "SHORT")
        long = len(self.strut_classes) - short
        return f"{short} SHORT + {long} LONG"


@lru_cache(maxsize=1)
def hub_types() -> tuple[HubType, ...]:
    """Every distinct joint in the dome half, measured and counted."""
    geometry = build_demo_geometry()
    class_of = dict(zip(geometry.edges, geometry.edge_class_by_edge))
    incident: dict[int, list[tuple[int, str]]] = {}
    for edge in geometry.hemisphere_edges:
        for near, far in ((edge[0], edge[1]), (edge[1], edge[0])):
            incident.setdefault(near, []).append((far, class_of[edge]))

    ring_of: dict[int, str] = {}
    for ring in dome_rings():
        for hub in ring.hubs:
            ring_of[hub] = ring.name

    groups: dict[tuple, list[int]] = {}
    for hub, arms in incident.items():
        classes = tuple(sorted(name for _, name in arms))
        directions = [
            normalize(geometry.vertices[far] - geometry.vertices[hub])
            for far, _ in arms
        ]
        splay: list[float] = []
        for first in range(len(directions)):
            for second in range(first + 1, len(directions)):
                cosine = float(np.clip(
                    float(np.dot(directions[first], directions[second])), -1.0, 1.0
                ))
                splay.append(round(math.degrees(math.acos(cosine)), 6))
        key = (len(arms), classes, tuple(sorted(splay)), ring_of.get(hub, "?"))
        groups.setdefault(key, []).append(hub)

    types: list[HubType] = []
    for order, (key, members) in enumerate(
        sorted(groups.items(), key=lambda item: (item[0][3], -item[0][0]))
    ):
        types.append(HubType(
            name=f"H{order + 1}",
            count=len(members),
            strut_count=key[0],
            strut_classes=key[1],
            splay_deg=key[2],
            ring_name=key[3],
        ))
    return tuple(types)


# ----------------------------------------------------------------------
# Buying and cutting the stock
# ----------------------------------------------------------------------

@dataclass(frozen=True)
class StockRun:
    """How one strut class comes out of a given stock length."""

    strut_class: str
    pieces_needed: int
    cut_length: float
    per_stick: int
    sticks: int
    offcut_per_stick: float

    @property
    def waste(self) -> float:
        return self.sticks * self.offcut_per_stick


def stock_plan(
    radius: float,
    stock_length: float,
    deduction: float = 0.0,
    kerf: float = 0.125,
) -> tuple[StockRun, ...]:
    """Work out sticks and offcut for each strut class, kerf included."""
    runs: list[StockRun] = []
    for detail in strut_details():
        cut = detail.cut_length(radius, deduction)
        if cut <= 0.0:
            raise ValueError("connector deduction is longer than the strut")
        per_stick = int(math.floor((stock_length + kerf) / (cut + kerf)))
        if per_stick < 1:
            raise ValueError(
                f"{detail.name} at {cut:.3f} does not fit {stock_length:.3f} stock"
            )
        sticks = int(math.ceil(detail.dome_count / per_stick))
        used = per_stick * cut + (per_stick - 1) * kerf
        runs.append(StockRun(
            strut_class=detail.name,
            pieces_needed=detail.dome_count,
            cut_length=cut,
            per_stick=per_stick,
            sticks=sticks,
            offcut_per_stick=stock_length - used,
        ))
    return tuple(runs)


# ----------------------------------------------------------------------
# What a small mistake actually does
# ----------------------------------------------------------------------

@dataclass(frozen=True)
class ErrorBudget:
    """How a per-strut error shows up at the scale of the building."""

    strut_error: float
    base_sides: int
    radius_error: float
    diameter_error: float
    apex_error: float

    @property
    def amplification(self) -> float:
        """Radius error per unit of strut error on the base ring."""
        return self.radius_error / self.strut_error if self.strut_error else 0.0


def error_budget(strut_error: float = 0.125) -> ErrorBudget:
    """A regular polygon's circumradius is its side over ``2 sin(pi/n)``.

    For the ten-sided base ring of a 2V dome that divisor is ``0.618034``,
    so the base radius moves by **phi times** whatever error is in each
    base strut.  An eighth of an inch per strut is a fifth of an inch on
    the radius, and a two-fifths of an inch on the diameter.
    """
    ring = dome_rings()[0]
    sides = ring.hub_count
    divisor = 2.0 * math.sin(math.pi / sides)
    radius_error = strut_error / divisor
    return ErrorBudget(
        strut_error=strut_error,
        base_sides=sides,
        radius_error=radius_error,
        diameter_error=2.0 * radius_error,
        # The apex sits one radius above the base plane, so a radius that
        # is out by this much carries the whole dome up or down with it.
        apex_error=radius_error,
    )


# ----------------------------------------------------------------------
# Reporting and proof
# ----------------------------------------------------------------------

def build_report(
    radius: float | None = None,
    deduction: float = 0.75,
    stock_length: float = 96.0,
) -> str:
    if radius is None:
        radius = fit_measurements(72.0, 63.5).best_fit_radius
    measurements = DomeMeasurements(radius, deduction)
    lines = [
        "2V DOME CONSTRUCTION - BUILD AUDIT",
        "",
        f"radius                {radius:.4f} in"
        f"   diameter {measurements.diameter:.4f} in",
        f"height                {measurements.height:.4f} in",
        f"floor area            {measurements.floor_area / 144.0:.3f} sq ft",
        f"skin area             {measurements.spherical_skin_area / 144.0:.3f} sq ft",
        f"enclosed volume       {measurements.enclosed_volume / 1728.0:.3f} cu ft",
        "",
        "RINGS (ground up)",
    ]
    for ring in dome_rings():
        lines.append(
            f"  {ring.index}: {ring.name:<12} {ring.hub_count:>2} hubs"
            f"   height {ring.height(radius):8.4f} in"
            f"   diameter {ring.diameter(radius):9.4f} in"
        )
    lines.extend(["", "STRUTS"])
    for detail in strut_details():
        lines.append(
            f"  {detail.name:<6} x{detail.dome_count:<3}"
            f"  factor {detail.factor:.9f}"
            f"  centre {detail.centre_length(radius):9.4f}"
            f"  cut {detail.cut_length(radius, deduction):9.4f}"
            f"  end cut {detail.axial_angle_deg:7.4f} deg"
        )
    lines.extend(["", "PANEL FOLDS"])
    for item in dihedral_classes():
        lines.append(
            f"  along {item.strut_class:<6} x{item.count:<3}"
            f"  dihedral {item.dihedral_deg:8.4f} deg"
            f"  bevel {item.bevel_deg:7.4f} deg"
        )
    lines.extend(["", "HUBS"])
    for hub in hub_types():
        lines.append(
            f"  {hub.name:<4} x{hub.count:<3} {hub.strut_count} struts"
            f"  ({hub.class_summary})  on the {hub.ring_name}"
        )
        lines.append(
            f"        splay {', '.join(f'{value:.3f}' for value in hub.splay_deg)}"
        )
    lines.extend(["", f"STOCK PLAN from {stock_length:.1f} in lengths"])
    for run in stock_plan(radius, stock_length, deduction):
        lines.append(
            f"  {run.strut_class:<6} {run.pieces_needed:>3} pieces @"
            f" {run.cut_length:8.4f}   {run.per_stick} per stick"
            f"   {run.sticks} sticks   offcut {run.offcut_per_stick:6.3f} each"
        )
    budget = error_budget(0.125)
    lines.extend([
        "",
        "ERROR BUDGET",
        f"  {budget.strut_error:.4f} in per base strut"
        f" -> radius {budget.radius_error:+.4f} in"
        f" -> diameter {budget.diameter_error:+.4f} in",
        f"  amplification {budget.amplification:.6f}  (= phi = {PHI:.6f})",
    ])
    return "\n".join(lines)


def validate_build_geometry() -> None:
    """Prove the construction numbers before any of them reach a screen."""
    geometry = build_demo_geometry()
    rings = dome_rings()
    # A 2V hemisphere in the five-fold-up frame: 10 + 10 + 5 + 1.
    assert sum(ring.hub_count for ring in rings) == 26, [r.hub_count for r in rings]
    assert rings[0].hub_count == 10, rings[0].hub_count
    assert rings[-1].hub_count == 1 and rings[-1].name == "apex"
    assert abs(rings[0].height_factor) < 1e-9, rings[0].height_factor
    assert abs(rings[-1].height_factor - 1.0) < 1e-9, rings[-1].height_factor
    for lower, upper in zip(rings, rings[1:]):
        assert upper.height_factor > lower.height_factor

    # The end cut is half the central angle, so it must reproduce the
    # chord it came from: chord = 2 R sin(theta / 2).
    for detail in strut_details():
        chord = 2.0 * math.sin(math.radians(detail.axial_angle_deg))
        assert abs(chord - detail.factor) < 1e-9, (detail.name, chord, detail.factor)
    assert sum(item.dome_count for item in strut_details()) == 65

    folds = dihedral_classes()
    assert folds, "the dome half has interior struts"
    for item in folds:
        assert 90.0 < item.dihedral_deg < 180.0, item
        assert 0.0 < item.bevel_deg < 45.0, item

    hubs = hub_types()
    assert sum(hub.count for hub in hubs) == 26, sum(hub.count for hub in hubs)
    assert sum(hub.count * hub.strut_count for hub in hubs) == 2 * 65
    apex = [hub for hub in hubs if hub.ring_name == "apex"]
    assert len(apex) == 1 and apex[0].count == 1 and apex[0].strut_count == 5

    radius = fit_measurements(72.0, 63.5).best_fit_radius
    runs = stock_plan(radius, 192.0, 0.75)
    for run in runs:
        assert run.per_stick >= 1 and run.sticks >= 1
        assert run.sticks * run.per_stick >= run.pieces_needed
        assert 0.0 <= run.offcut_per_stick < run.cut_length + 0.125

    budget = error_budget(0.125)
    # The ten-sided base ring amplifies by exactly the golden ratio.
    assert abs(budget.amplification - PHI) < 1e-9, budget.amplification
