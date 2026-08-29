"""Hubless framing, breathing shells, sheet shelters, and the franken-dome.

Four additions to the construction lesson, all measured off the same 2V
hemisphere the rest of it uses.

``hubless_struts`` / ``compound_setups``
    A hubless dome has no hubs at all: every one of its forty triangles is
    a complete, closed triangle, so the dome is 120 struts rather than 65.
    Each strut end is a *compound* cut -- a mitre and a bevel set at the
    same time -- and this module measures every one of them off the model
    rather than quoting a table.

``sheet_nesting``
    How large a forty-panel shelter can be cut from a single sheet, by
    pairing congruent triangles into parallelograms and strip-packing them.

``airflow_cases``
    The dome shell used as a distributed filter: a blower at the centre,
    air crossing the whole envelope instead of one extract point.

``franken_hardware``
    The bolt, bracket and screw count for a dome built from whatever stock
    is to hand, and what that trade actually buys.
"""

from __future__ import annotations

import math
from dataclasses import dataclass
from functools import lru_cache

import numpy as np

from .geometry import build_demo_geometry, normalize


# ----------------------------------------------------------------------
# Published or conventional values -- everything else here is computed
# ----------------------------------------------------------------------

TYPICAL_MITRE_SAW_MAX_DEG = 50.0
"""How far a common mitre saw swings from square.

Better saws reach 55 or 60 degrees; almost none reach past that. This is
the number that decides whether a hubless dome is a jig problem or a
weekend of frustration, so the lesson states it as a tool limit rather
than a geometric one.
"""

SAW_KERF_IN = 0.125
"""Material a blade removes per cut. A CNC laser is far finer; a bandsaw
or track saw is about this."""

SHEET_EDGE_MARGIN_IN = 0.5
"""Unusable strip around a sheet: clamp room, damaged edge, squaring cut."""


# ----------------------------------------------------------------------
# Hubless framing
# ----------------------------------------------------------------------

@dataclass(frozen=True)
class HublessStrut:
    """One of the 120 struts, with the two cuts its ends need."""

    face: tuple[int, int, int]
    edge: tuple[int, int]
    length_factor: float
    corner_a_deg: float
    corner_b_deg: float
    dihedral_deg: float | None
    """None on a rim strut, which has no neighbouring panel to fold to."""

    @property
    def is_rim(self) -> bool:
        return self.dihedral_deg is None

    @property
    def bevel_deg(self) -> float:
        """Blade tilt: half the fold to the neighbouring triangle.

        A rim strut has no neighbour, so it is cut square and is the only
        easy strut in the whole dome.
        """
        if self.dihedral_deg is None:
            return 0.0
        return (180.0 - self.dihedral_deg) * 0.5

    def mitre_deg(self, end: str) -> float:
        """Saw swing away from square, at one end.

        Two members meeting at an interior angle ``C`` are each cut at
        ``C / 2`` from their own axis, which is ``90 - C / 2`` away from
        square -- and square is what a saw scale is zeroed on.
        """
        corner = self.corner_a_deg if end == "a" else self.corner_b_deg
        return 90.0 - corner * 0.5


@dataclass(frozen=True)
class CompoundSetup:
    """One distinct (mitre, bevel) pair the shop has to set up."""

    mitre_deg: float
    bevel_deg: float
    count: int

    @property
    def within_saw_range(self) -> bool:
        return self.mitre_deg <= TYPICAL_MITRE_SAW_MAX_DEG

    @property
    def complement_deg(self) -> float:
        """The same cut, approached from the other reference face.

        When the mitre is past the saw's stop, the way through is to swing
        the saw to this instead and rotate the workpiece a quarter turn in
        the sled. The cut is identical; only the reference changes.
        """
        return 90.0 - self.mitre_deg


@lru_cache(maxsize=1)
def hubless_struts() -> tuple[HublessStrut, ...]:
    """Every strut of a hubless 2V hemisphere, measured off the model."""
    geometry = build_demo_geometry()
    faces = [tuple(int(value) for value in face) for face in geometry.hemisphere_faces]

    normal_of: dict[tuple[int, int, int], np.ndarray] = {}
    for face in faces:
        points = geometry.vertices[list(face)]
        normal = normalize(np.cross(points[1] - points[0], points[2] - points[0]))
        if float(np.dot(normal, points.mean(axis=0))) < 0.0:
            normal = -normal
        normal_of[face] = normal

    faces_at_edge: dict[tuple[int, int], list[tuple[int, int, int]]] = {}
    for face in faces:
        for position in range(3):
            a, b = face[position], face[(position + 1) % 3]
            faces_at_edge.setdefault((a, b) if a < b else (b, a), []).append(face)

    dihedral_of: dict[tuple[int, int], float] = {}
    for edge, sharing in faces_at_edge.items():
        if len(sharing) != 2:
            continue
        cosine = float(np.clip(
            float(np.dot(normal_of[sharing[0]], normal_of[sharing[1]])), -1.0, 1.0
        ))
        dihedral_of[edge] = 180.0 - math.degrees(math.acos(cosine))

    struts: list[HublessStrut] = []
    for face in faces:
        for position in range(3):
            a_index = face[position]
            b_index = face[(position + 1) % 3]
            o_index = face[(position + 2) % 3]
            a = geometry.vertices[a_index]
            b = geometry.vertices[b_index]
            o = geometry.vertices[o_index]
            corner_a = math.degrees(math.acos(float(np.clip(
                float(np.dot(normalize(b - a), normalize(o - a))), -1.0, 1.0))))
            corner_b = math.degrees(math.acos(float(np.clip(
                float(np.dot(normalize(a - b), normalize(o - b))), -1.0, 1.0))))
            key = (a_index, b_index) if a_index < b_index else (b_index, a_index)
            struts.append(HublessStrut(
                face=face,
                edge=key,
                length_factor=float(np.linalg.norm(b - a)),
                corner_a_deg=corner_a,
                corner_b_deg=corner_b,
                dihedral_deg=dihedral_of.get(key),
            ))
    return tuple(struts)


@lru_cache(maxsize=1)
def compound_setups() -> tuple[CompoundSetup, ...]:
    """The distinct compound-angle setups, and how many ends need each."""
    counts: dict[tuple[int, int], int] = {}
    for strut in hubless_struts():
        for end in ("a", "b"):
            key = (int(round(strut.mitre_deg(end) * 1e3)),
                   int(round(strut.bevel_deg * 1e3)))
            counts[key] = counts.get(key, 0) + 1
    return tuple(sorted(
        (CompoundSetup(mitre / 1e3, bevel / 1e3, count)
         for (mitre, bevel), count in counts.items()),
        key=lambda item: (-item.count, item.mitre_deg),
    ))


@dataclass(frozen=True)
class HublessSummary:
    """The whole hubless frame, counted."""

    triangles: int
    struts: int
    unique_edges: int
    doubled_edges: int
    rim_edges: int
    setups: int
    setups_past_saw: int

    @property
    def strut_check(self) -> int:
        """Two struts on every shared edge, one on every rim edge."""
        return self.doubled_edges * 2 + self.rim_edges


@lru_cache(maxsize=1)
def hubless_summary() -> HublessSummary:
    geometry = build_demo_geometry()
    struts = hubless_struts()
    rim = sum(1 for strut in struts if strut.is_rim)
    setups = compound_setups()
    return HublessSummary(
        triangles=len(geometry.hemisphere_faces),
        struts=len(struts),
        unique_edges=len(geometry.hemisphere_edges),
        doubled_edges=sum(1 for strut in struts if not strut.is_rim) // 2,
        rim_edges=rim,
        setups=len(setups),
        setups_past_saw=sum(1 for item in setups if not item.within_saw_range),
    )


# ----------------------------------------------------------------------
# Cutting forty panels from one sheet
# ----------------------------------------------------------------------

@dataclass(frozen=True)
class PanelClass:
    """One triangle shape on the dome half."""

    count: int
    sides: tuple[float, float, float]
    area_factor: float

    def pair_base(self) -> float:
        """Longest side, which two triangles are joined along to nest."""
        return max(self.sides)

    def pair_height(self, radius: float) -> float:
        """Height of that parallelogram: twice the area over the base."""
        base = self.pair_base() * radius
        return 2.0 * self.area_factor * radius * radius / base


@lru_cache(maxsize=1)
def panel_classes() -> tuple[PanelClass, ...]:
    geometry = build_demo_geometry()
    groups: dict[tuple[int, int, int], int] = {}
    for face in geometry.hemisphere_faces:
        points = geometry.vertices[[int(value) for value in face]]
        sides = tuple(sorted(
            float(np.linalg.norm(points[i] - points[(i + 1) % 3])) for i in range(3)
        ))
        key = tuple(int(round(value * 1e9)) for value in sides)
        groups[key] = groups.get(key, 0) + 1
    classes: list[PanelClass] = []
    for key, count in sorted(groups.items(), key=lambda kv: -kv[1]):
        sides = tuple(value / 1e9 for value in key)
        a, b, c = sides
        s = (a + b + c) * 0.5
        area = math.sqrt(max(0.0, s * (s - a) * (s - b) * (s - c)))
        classes.append(PanelClass(count, sides, area))
    return tuple(classes)


@dataclass(frozen=True)
class NestingPlan:
    """A sheet, a radius, and whether the panels actually fit on it."""

    sheet_width: float
    sheet_height: float
    radius: float
    rows_used: float
    fits: bool

    @property
    def usable_width(self) -> float:
        return self.sheet_width - 2.0 * SHEET_EDGE_MARGIN_IN

    @property
    def usable_height(self) -> float:
        return self.sheet_height - 2.0 * SHEET_EDGE_MARGIN_IN

    @property
    def diameter(self) -> float:
        return 2.0 * self.radius

    @property
    def headroom(self) -> float:
        """A hemisphere is exactly as tall as its radius."""
        return self.radius

    @property
    def floor_area_sqft(self) -> float:
        return math.pi * self.radius * self.radius / 144.0

    @property
    def can_stand_up(self) -> bool:
        """Under about 6 ft of headroom, nobody is standing up in this."""
        return self.headroom >= 72.0

    @property
    def can_sit_up(self) -> bool:
        """Seated adult height, floor to top of head, is about 36 in."""
        return self.headroom >= 36.0

    def with_riser(self, riser_height: float) -> float:
        """Headroom once the same shell sits on a straight wall.

        The shell is fixed by the sheet it came off, but nothing says it
        has to start at the ground. A riser costs a strip of wall and
        buys its own height in headroom, one inch for one inch, without
        touching a single panel.
        """
        return self.headroom + riser_height

    def riser_for(self, target_headroom: float) -> float:
        """How tall a riser this shell needs to reach a given headroom."""
        return max(0.0, target_headroom - self.headroom)

    @property
    def riser_wall_area_sqft(self) -> float:
        """Wall area added per inch of riser: the circumference, once."""
        return 2.0 * math.pi * self.radius / 144.0


def _rows_needed(radius: float, width: float) -> float:
    """Total strip height to nest every panel at this radius.

    Congruent triangles pair into parallelograms, and parallelograms strip
    -pack with no waste along a row: the shear of one is filled by the next.
    Only the ends of a row and the kerf between parts are lost.
    """
    total_height = 0.0
    for panel in panel_classes():
        pairs = math.ceil(panel.count / 2)
        base = panel.pair_base() * radius + SAW_KERF_IN
        height = panel.pair_height(radius) + SAW_KERF_IN
        per_row = max(1, int((width - panel.pair_base() * radius) // base))
        rows = math.ceil(pairs / per_row)
        total_height += rows * height
    return total_height


def sheet_nesting(
    sheet_width: float = 120.0,
    sheet_height: float = 60.0,
) -> NestingPlan:
    """Largest dome whose forty panels still come off one sheet.

    Solved by bisection on the radius rather than by an efficiency factor,
    so the answer responds to the real shapes and the real kerf.
    """
    low, high = 1.0, sheet_width
    usable_w = sheet_width - 2.0 * SHEET_EDGE_MARGIN_IN
    usable_h = sheet_height - 2.0 * SHEET_EDGE_MARGIN_IN
    for _ in range(80):
        middle = (low + high) * 0.5
        if _rows_needed(middle, usable_w) <= usable_h:
            low = middle
        else:
            high = middle
    return NestingPlan(
        sheet_width=sheet_width,
        sheet_height=sheet_height,
        radius=low,
        rows_used=_rows_needed(low, usable_w),
        fits=True,
    )


# ----------------------------------------------------------------------
# The shell as a filter
# ----------------------------------------------------------------------

M_PER_INCH = 0.0254
CFM_PER_M3H = 0.5885778
FPM_PER_MS = 196.8504


@dataclass(frozen=True)
class AirflowCase:
    """One ventilation rate, and what it means at the wall."""

    name: str
    air_changes_per_hour: float
    volume_m3: float
    shell_area_m2: float

    @property
    def m3_per_hour(self) -> float:
        return self.volume_m3 * self.air_changes_per_hour

    @property
    def cfm(self) -> float:
        return self.m3_per_hour * CFM_PER_M3H

    @property
    def face_velocity_ms(self) -> float:
        """How fast the air actually crosses the wall.

        This is the number that makes the idea interesting: the shell is
        enormous next to the volume, so the air creeps through it.
        """
        return self.m3_per_hour / 3600.0 / self.shell_area_m2

    @property
    def face_velocity_fpm(self) -> float:
        return self.face_velocity_ms * FPM_PER_MS

    @property
    def is_draught_free(self) -> bool:
        """Below about 40 ft/min, moving air is not felt as a draught."""
        return self.face_velocity_fpm < 40.0


@dataclass(frozen=True)
class AirflowModel:
    """A dome, treated as a plenum with a porous wall."""

    radius_in: float
    cases: tuple[AirflowCase, ...]

    @property
    def radius_m(self) -> float:
        return self.radius_in * M_PER_INCH

    @property
    def shell_area_m2(self) -> float:
        return 2.0 * math.pi * self.radius_m ** 2

    @property
    def volume_m3(self) -> float:
        return (2.0 / 3.0) * math.pi * self.radius_m ** 3

    @property
    def volume_cuft(self) -> float:
        return self.volume_m3 * 35.31467

    @property
    def area_to_volume(self) -> float:
        """Square metres of wall per cubic metre of room.

        A hemisphere gives ``3 / R``: the smaller the dome, the more wall
        there is per unit of air, and the gentler the flow through it.
        """
        return self.shell_area_m2 / self.volume_m3

    @property
    def base_tube_length_in(self) -> float:
        """Circumference of the ring main around the base."""
        return 2.0 * math.pi * self.radius_in


def airflow_model(radius_in: float = 60.0) -> AirflowModel:
    """Ventilation numbers for a dome of this radius."""
    radius_m = radius_in * M_PER_INCH
    shell = 2.0 * math.pi * radius_m ** 2
    volume = (2.0 / 3.0) * math.pi * radius_m ** 3
    cases = tuple(
        AirflowCase(name, ach, volume, shell)
        for name, ach in (
            ("general ventilation", 6.0),
            ("welding fume control", 20.0),
            ("full purge", 40.0),
        )
    )
    return AirflowModel(radius_in, cases)


# The honest part.  A breathing wall is a real, published building-science
# idea, but these are the things that decide whether it works.
AIRFLOW_CAVEATS: tuple[tuple[str, str], ...] = (
    ("Direction changes everything",
     "Pulling air inward through the shell warms it on the way in and "
     "recovers heat that would otherwise be lost. Pushing it outward "
     "purges fumes fastest, which is what a welder wants, but drives "
     "indoor moisture into the shell."),
    ("Moisture is the failure mode",
     "Warm wet air pushed outward through a cold wall reaches its dew "
     "point somewhere inside that wall. In a heating climate this is how "
     "you rot a shell from the inside without ever seeing it."),
    ("A sealed skin cannot breathe",
     "A monolithic fibreglass encapsulation is the opposite of a porous "
     "wall. You cannot have both by accident: the path has to be designed "
     "in, with a deliberate permeable band and a sealed remainder."),
    ("The filter has to be serviceable",
     "Anything that catches particulate eventually holds it. A filter you "
     "cannot reach is a filter you will not change."),
    ("This one is untested",
     "The geometry and the flow numbers here are computed. Whether a "
     "strut lattice makes a good distributed plenum at building scale is "
     "the creator's own idea and has not been measured."),
)


# ----------------------------------------------------------------------
# The franken-dome
# ----------------------------------------------------------------------

@dataclass(frozen=True)
class FrankenBuild:
    """A dome framed from whatever stock was to hand."""

    triangles: int
    brackets_per_triangle: int
    screws_per_bracket: int
    bolts_per_edge: int
    unique_edges: int
    shared_edges: int
    build_days: int
    stood_months: int

    @property
    def brackets(self) -> int:
        return self.triangles * self.brackets_per_triangle

    @property
    def screws(self) -> int:
        return self.brackets * self.screws_per_bracket

    @property
    def bolts(self) -> int:
        return self.unique_edges * self.bolts_per_edge

    @property
    def structural_bolts(self) -> int:
        """Bolts on edges that actually join two triangles together."""
        return self.shared_edges * self.bolts_per_edge

    @property
    def washers(self) -> int:
        return self.bolts * 2

    @property
    def fasteners(self) -> int:
        return self.screws + self.bolts

    @property
    def triangles_per_day(self) -> float:
        return self.triangles / self.build_days

    @property
    def screws_per_day(self) -> float:
        return self.screws / self.build_days

    @property
    def service_ratio(self) -> float:
        """How many times over the dome outlived its own build time."""
        return (self.stood_months * 30.0) / self.build_days


@lru_cache(maxsize=1)
def franken_hardware() -> FrankenBuild:
    """Hardware counts for the mixed-stock dome, from the real geometry."""
    summary = hubless_summary()
    return FrankenBuild(
        triangles=summary.triangles,
        brackets_per_triangle=3,
        screws_per_bracket=8,
        bolts_per_edge=2,
        unique_edges=summary.unique_edges,
        shared_edges=summary.doubled_edges,
        build_days=10,
        stood_months=6,
    )


# What the mixed-stock method actually trades.
FRANKEN_TRADE: tuple[tuple[str, str], ...] = (
    ("What you give up",
     "Struts of different sections meet at different effective "
     "centrelines, so no joint lands exactly where the geometry says. "
     "The frame settles into a shape near the sphere rather than on it."),
    ("Why it still stands",
     "A closed triangulated shell has enormous redundancy. Every "
     "triangle is individually rigid, and an error at one joint is taken "
     "up by the two hundred that surround it instead of accumulating."),
    ("What buys it back",
     "The sheathing. A monolithic skin bonded over a lumpy frame spans "
     "the slack and returns the shell action the geometry lost."),
    ("What it is good for",
     "Storage, a workshop, a shelter, anything where the covering "
     "matters more than the tolerance."),
    ("What it is not for",
     "Anything inspected, occupied full time, or carrying snow you have "
     "not calculated for."),
)


# ----------------------------------------------------------------------
# Reporting
# ----------------------------------------------------------------------

def hubless_report(radius: float = 120.0) -> str:
    """A portable audit of everything these four sections claim."""
    summary = hubless_summary()
    lines = ["HUBLESS / SHELTER / AIRFLOW / FRANKEN-DOME - CALCULATION AUDIT", ""]
    lines.append("--- hubless framing ---")
    lines.append(f"  triangles              {summary.triangles}")
    lines.append(f"  struts (3 per triangle){summary.struts:>4}")
    lines.append(f"  unique edges           {summary.unique_edges}")
    lines.append(f"  edges carrying 2 struts{summary.doubled_edges:>4}")
    lines.append(f"  rim edges carrying 1   {summary.rim_edges}")
    lines.append(f"  check 2x{summary.doubled_edges} + {summary.rim_edges} "
                 f"= {summary.strut_check}")
    lines.append(f"  distinct compound setups {summary.setups}"
                 f"   past a {TYPICAL_MITRE_SAW_MAX_DEG:.0f} deg saw: "
                 f"{summary.setups_past_saw}")
    for setup in compound_setups():
        flag = "" if setup.within_saw_range else "  <- past the saw's stop"
        lines.append(
            f"    mitre {setup.mitre_deg:7.3f}  bevel {setup.bevel_deg:6.3f}"
            f"  x{setup.count:<4}(or swing {setup.complement_deg:6.3f} "
            f"and turn the part){flag}"
        )
    lines.append("")

    lines.append("--- micro shelter, 40 panels from one sheet ---")
    for width, height in ((120.0, 60.0), (96.0, 48.0)):
        plan = sheet_nesting(width, height)
        lines.append(
            f"  {width:.0f} x {height:.0f} in sheet -> R {plan.radius:6.2f} in, "
            f"{plan.diameter:6.2f} in across, {plan.headroom:5.2f} in headroom, "
            f"{plan.floor_area_sqft:5.2f} sq ft"
        )
        lines.append(
            f"     stand up inside: {plan.can_stand_up}   "
            f"sit up inside: {plan.can_sit_up}   "
            f"nesting used {plan.rows_used:.1f} of "
            f"{plan.usable_height:.1f} in"
        )
        for target in (36.0, 60.0, 72.0):
            riser = plan.riser_for(target)
            lines.append(
                f"     {target:.0f} in headroom needs a {riser:5.2f} in riser"
                f"  (+{riser * plan.riser_wall_area_sqft:5.2f} sq ft of wall)"
            )
    lines.append("")

    lines.append("--- the shell as a filter ---")
    model = airflow_model(60.0)
    lines.append(f"  dome R {model.radius_in:.0f} in: shell "
                 f"{model.shell_area_m2:.2f} m2, volume {model.volume_m3:.2f} m3 "
                 f"({model.volume_cuft:.0f} cu ft)")
    lines.append(f"  wall per unit of air   {model.area_to_volume:.3f} m2/m3"
                 f"   base ring main {model.base_tube_length_in:.1f} in")
    for case in model.cases:
        lines.append(
            f"    {case.name:<22} {case.air_changes_per_hour:4.0f} ACH -> "
            f"{case.cfm:6.1f} CFM, through the wall at "
            f"{case.face_velocity_fpm:5.2f} ft/min"
            f"   felt as a draught: {not case.is_draught_free}"
        )
    for title, _ in AIRFLOW_CAVEATS:
        lines.append(f"    caveat: {title}")
    lines.append("")

    lines.append("--- the franken-dome ---")
    franken = franken_hardware()
    lines.append(f"  {franken.triangles} triangles x "
                 f"{franken.brackets_per_triangle} corners = "
                 f"{franken.brackets} brackets")
    lines.append(f"  x {franken.screws_per_bracket} screws = "
                 f"{franken.screws:,} screws")
    lines.append(f"  {franken.bolts_per_edge} bolts x {franken.unique_edges} "
                 f"edges = {franken.bolts} bolts, {franken.washers} washers")
    lines.append(f"  of those, {franken.structural_bolts} join two triangles")
    lines.append(f"  {franken.fasteners:,} fasteners total")
    lines.append(f"  {franken.build_days} days -> "
                 f"{franken.triangles_per_day:.1f} triangles and "
                 f"{franken.screws_per_day:.0f} screws a day")
    lines.append(f"  stood {franken.stood_months} months = "
                 f"{franken.service_ratio:.0f}x its own build time")
    return "\n".join(lines)


def validate_hubless() -> None:
    """Prove all four models before any of their numbers reach a screen."""
    summary = hubless_summary()
    # The headline claim: three struts per triangle, and every shared edge
    # carries two of them.
    assert summary.struts == summary.triangles * 3, summary
    assert summary.strut_check == summary.struts, summary
    assert summary.doubled_edges + summary.rim_edges == summary.unique_edges, summary
    assert summary.triangles == 40 and summary.struts == 120, summary

    struts = hubless_struts()
    assert len(struts) == 120
    # Every triangle closes: its three corners sum to 180 degrees.
    by_face: dict[tuple[int, int, int], list[float]] = {}
    for strut in struts:
        by_face.setdefault(strut.face, []).append(strut.corner_a_deg)
    for face, corners in by_face.items():
        assert abs(sum(corners) - 180.0) < 1e-6, (face, sum(corners))
    # Rim struts are the only square-cut ones.
    assert all(strut.bevel_deg == 0.0 for strut in struts if strut.is_rim)
    assert all(strut.bevel_deg > 0.0 for strut in struts if not strut.is_rim)

    setups = compound_setups()
    assert setups, "there must be at least one compound setup"
    assert sum(item.count for item in setups) == 2 * len(struts)
    # The point of the chapter: the mitres are past a common saw's stop.
    assert summary.setups_past_saw > 0, setups
    for setup in setups:
        assert 0.0 < setup.mitre_deg < 90.0, setup
        assert 0.0 <= setup.bevel_deg < 45.0, setup
        # The complement trick has to land somewhere a saw can reach.
        if not setup.within_saw_range:
            assert setup.complement_deg <= TYPICAL_MITRE_SAW_MAX_DEG, setup

    classes = panel_classes()
    assert sum(item.count for item in classes) == 40, classes

    plan = sheet_nesting(120.0, 60.0)
    assert plan.radius > 12.0, plan.radius
    # It has to fit on the sheet it was solved for, with the panels no
    # bigger than the sheet is wide.
    assert plan.rows_used <= plan.usable_height + 1e-6, plan
    assert max(item.pair_base() for item in classes) * plan.radius \
        <= plan.usable_width, plan
    # And the honest part: it is a crawl-in shelter, not a room.
    assert not plan.can_stand_up, plan.headroom
    # A riser buys headroom inch for inch without touching a panel.
    assert plan.with_riser(24.0) == plan.headroom + 24.0
    assert plan.riser_for(72.0) > 0.0
    assert plan.riser_for(1.0) == 0.0
    # A smaller sheet must give a smaller dome.
    assert sheet_nesting(96.0, 48.0).radius < plan.radius

    model = airflow_model(60.0)
    assert model.shell_area_m2 > 0.0 and model.volume_m3 > 0.0
    # A hemisphere's wall-to-air ratio is exactly 3 / R.
    assert abs(model.area_to_volume - 3.0 / model.radius_m) < 1e-9
    previous = 0.0
    for case in model.cases:
        assert case.cfm > previous, case
        previous = case.cfm
        # The whole point: crossing the wall this slowly is not a draught.
        assert case.is_draught_free, (case.name, case.face_velocity_fpm)
    assert len(AIRFLOW_CAVEATS) >= 5

    franken = franken_hardware()
    assert franken.brackets == 120, franken.brackets
    assert franken.screws == 960, franken.screws
    assert franken.bolts == 130, franken.bolts
    assert franken.structural_bolts == 110, franken.structural_bolts
    assert franken.triangles_per_day == 4.0, franken.triangles_per_day
    assert franken.service_ratio > 1.0, franken.service_ratio
    assert len(FRANKEN_TRADE) >= 5
