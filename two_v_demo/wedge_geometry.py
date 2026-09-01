"""Radial log sectors as structural members, and the panels they build.

This module models a different way of getting from a standing tree to a
2V hemisphere.  Instead of milling a round trunk into rectangles and
throwing the curved outside away, each log section is split
half-quarter-eighth into eight 45-degree sectors, and each sector *is*
the structural member: curved bark face outward, pith line inward.

Three things are computed here, and nothing else in the package computes
them:

**The tree.**  A tapered trunk, its solid volume, what the radial splits
cost in saw kerf, what is left in the wedges, and -- for comparison -- how
many true two-by-fours can actually be grid-packed out of the same
sections.  That last figure is computed rather than assumed, and it does
not agree with the optimistic estimate the brief works from; both are
reported, because the conclusion survives either one.

**The panel.**  Forty independent triangular frames.  Within each frame
the three members run as a same-handed pinwheel: every member's end
butts into the *side* of the next one, and its other end runs on past the
mathematical vertex so the previous member can butt into its side.  The
triangle's corners are therefore reference points, not wood endpoints,
and no member is mitred, coped or shaved -- both ends are square
crosscuts.

**The joint between panels.**  Neighbouring panels do not share a stick.
Each carries its own member along the shared edge, and the two meet
through a separate spline, key or rubber-hose gasket, so the pair is
separated by the gasket thickness and the wood is never cut to suit its
neighbour.

Conventions: lengths are inches unless a name says ``_ft``; ``bf`` is
board feet, and one board foot is 144 cubic inches.  Angles are degrees
on the way out and radians inside.
"""

from __future__ import annotations

import math
from dataclasses import dataclass
from functools import lru_cache

import numpy as np

from .geometry import build_demo_geometry, normalize
from .hubless_geometry import hubless_summary


CUBIC_INCHES_PER_BOARD_FOOT = 144.0
SECTORS_PER_LOG = 8
"""Half, then quarter, then eighth: three passes, eight sectors."""

SECTOR_ANGLE_DEG = 360.0 / SECTORS_PER_LOG

# ----------------------------------------------------------------------
# The tree.  Every figure below is measured off a real trunk, so these
# are inputs to the model rather than results of it.
# ----------------------------------------------------------------------

EXTERNAL_CONSTANTS: tuple[tuple[str, float, str, str], ...] = (
    ("butt_diameter_in", 15.0, "in",
     "Trunk diameter at the bottom of the usable length, from the brief."),
    ("top_diameter_in", 5.5, "in",
     "Trunk diameter where the usable length ends, from the brief."),
    ("usable_length_ft", 60.0, "ft",
     "Usable straight trunk on the example pine, from the brief."),
    ("section_length_ft", 12.0, "ft",
     "Bucking length: two six-foot struts per section."),
    ("kerf_in", 0.25, "in",
     "Ripping kerf of a large chainsaw, from the brief."),
    ("brief_two_by_fours_per_tree", 32.0, "pieces",
     "The brief's optimistic estimate of true 2x4x12s per tree. This "
     "module packs the same sections and gets fewer; both are shown."),
    ("gasket_thickness_in", 0.75, "in",
     "Spline / key / hose gasket between neighbouring panels. A build "
     "choice, not a derived value."),
    ("bearing_pressure_psi", 425.0, "psi",
     "Allowable compression perpendicular to grain for softwood species "
     "in this class -- used only to size the end-to-side bearing, and "
     "no substitute for a designer's number."),
)


@dataclass(frozen=True)
class LogModel:
    """One tapered trunk, and the arithmetic that follows from it."""

    butt_diameter_in: float = 15.0
    top_diameter_in: float = 5.5
    usable_length_ft: float = 60.0
    section_length_ft: float = 12.0
    kerf_in: float = 0.25

    @property
    def sections(self) -> int:
        return int(self.usable_length_ft // self.section_length_ft)

    def diameter_at(self, height_ft: float) -> float:
        """Trunk diameter that far up, taper taken as linear."""
        fraction = height_ft / self.usable_length_ft
        return (self.butt_diameter_in
                + (self.top_diameter_in - self.butt_diameter_in) * fraction)

    @staticmethod
    def frustum_bf(diameter_a: float, diameter_b: float,
                   length_in: float) -> float:
        """Solid wood in a tapered round length, in board feet."""
        radius_a, radius_b = diameter_a * 0.5, diameter_b * 0.5
        volume = (math.pi * length_in / 3.0
                  * (radius_a**2 + radius_a * radius_b + radius_b**2))
        return volume / CUBIC_INCHES_PER_BOARD_FOOT

    @property
    def solid_bf(self) -> float:
        return self.frustum_bf(self.butt_diameter_in, self.top_diameter_in,
                               self.usable_length_ft * 12.0)

    def kerf_bf_for(self, mid_diameter: float) -> float:
        """What the three splitting passes remove from one section.

        Two cuts cross the full diameter (half, then the quarters), and
        four more run from pith to bark to make the eighths.  Four
        radius-length cuts are two diameters of kerf, so the section
        loses four diameters of kerf in total.
        """
        return (4.0 * mid_diameter * self.kerf_in
                * self.section_length_ft * 12.0
                / CUBIC_INCHES_PER_BOARD_FOOT)

    @property
    def wedges_per_tree(self) -> int:
        return self.sections * SECTORS_PER_LOG

    @property
    def struts_per_tree(self) -> int:
        """Each section-length wedge is crosscut once at the middle."""
        return self.wedges_per_tree * 2

    @property
    def strut_length_ft(self) -> float:
        return self.section_length_ft / 2.0


DEFAULT_LOG = LogModel()


@dataclass(frozen=True)
class SectionRow:
    """One bucked log section, and what it gives up either way."""

    index: int
    butt_diameter_in: float
    top_diameter_in: float
    solid_bf: float
    kerf_bf: float
    sector_area_in2: float
    two_by_four_count: int
    two_by_four_rows: tuple[int, ...]

    @property
    def wedge_bf(self) -> float:
        return self.solid_bf - self.kerf_bf


def sector_area_in2(diameter_in: float,
                    sectors: int = SECTORS_PER_LOG) -> float:
    """Cross-sectional area of one radial sector of a round log."""
    radius = diameter_in * 0.5
    return math.pi * radius * radius / sectors


def sector_chord_in(diameter_in: float,
                    sectors: int = SECTORS_PER_LOG) -> float:
    """Width of a sector across its bark face -- the member's width."""
    radius = diameter_in * 0.5
    return 2.0 * radius * math.sin(math.pi / sectors)


def sector_depth_in(diameter_in: float) -> float:
    """Pith to bark: the member's depth, which is where its stiffness is."""
    return diameter_in * 0.5


def two_by_four_packing(diameter_in: float,
                        width_in: float = 4.0,
                        thickness_in: float = 2.0) -> tuple[int, ...]:
    """How many true 2x4s grid-pack into a round section, row by row.

    Sawn the way a mill actually saws: parallel rows across the log,
    each row as many pieces as its narrowest chord allows.  A section is
    sized on its small end, because a piece has to be full width along
    its whole length.
    """
    radius = diameter_in * 0.5
    rows: list[int] = []
    bottom = -radius
    while bottom + thickness_in <= radius + 1e-9:
        top = bottom + thickness_in
        # The row is limited by whichever of its two edges is nearer the
        # bark: that is where the circle pinches in.
        worst = max(abs(bottom), abs(top))
        half_chord = math.sqrt(max(0.0, radius * radius - worst * worst))
        rows.append(int((2.0 * half_chord) // width_in))
        bottom = top
    return tuple(rows)


@lru_cache(maxsize=4)
def section_rows(log: LogModel = DEFAULT_LOG) -> tuple[SectionRow, ...]:
    """Every bucked section of one trunk, both ways of cutting it."""
    rows: list[SectionRow] = []
    for index in range(log.sections):
        low = index * log.section_length_ft
        high = low + log.section_length_ft
        butt = log.diameter_at(low)
        top = log.diameter_at(high)
        packing = two_by_four_packing(top)
        rows.append(SectionRow(
            index=index,
            butt_diameter_in=butt,
            top_diameter_in=top,
            solid_bf=log.frustum_bf(butt, top, log.section_length_ft * 12.0),
            kerf_bf=log.kerf_bf_for((butt + top) * 0.5),
            sector_area_in2=sector_area_in2((butt + top) * 0.5),
            two_by_four_count=sum(packing),
            two_by_four_rows=packing,
        ))
    return tuple(rows)


@dataclass(frozen=True)
class TreeYield:
    """One trunk, converted both ways."""

    log: LogModel
    solid_bf: float
    kerf_bf: float
    wedge_bf: float
    wedge_count: int
    strut_count: int
    bf_per_strut: float
    two_by_four_count: int
    two_by_four_bf: float
    two_by_four_struts: int
    brief_two_by_four_count: int
    brief_two_by_four_bf: float

    @property
    def wedge_recovery(self) -> float:
        return self.wedge_bf / self.solid_bf

    @property
    def two_by_four_recovery(self) -> float:
        return self.two_by_four_bf / self.solid_bf

    @property
    def gain_over_computed(self) -> float:
        return self.wedge_bf / self.two_by_four_bf

    @property
    def gain_over_brief(self) -> float:
        """The same comparison against the brief's kinder estimate."""
        return self.wedge_bf / self.brief_two_by_four_bf


@lru_cache(maxsize=4)
def tree_yield(log: LogModel = DEFAULT_LOG) -> TreeYield:
    rows = section_rows(log)
    solid = sum(row.solid_bf for row in rows)
    kerf = sum(row.kerf_bf for row in rows)
    count = sum(row.two_by_four_count for row in rows)
    brief = int(next(value for key, value, _u, _s in EXTERNAL_CONSTANTS
                     if key == "brief_two_by_fours_per_tree"))
    # A true 2x4x12 is 2 x 4 x 144 cubic inches, which is 8 board feet.
    bf_each = 2.0 * 4.0 * log.section_length_ft * 12.0 \
        / CUBIC_INCHES_PER_BOARD_FOOT
    return TreeYield(
        log=log,
        solid_bf=solid,
        kerf_bf=kerf,
        wedge_bf=solid - kerf,
        wedge_count=log.wedges_per_tree,
        strut_count=log.struts_per_tree,
        bf_per_strut=(solid - kerf) / log.struts_per_tree,
        two_by_four_count=count,
        two_by_four_bf=count * bf_each,
        two_by_four_struts=count * 2,
        brief_two_by_four_count=brief,
        brief_two_by_four_bf=brief * bf_each,
    )


# ----------------------------------------------------------------------
# The panel: three members, one pinwheel, no mitres
# ----------------------------------------------------------------------

@dataclass(frozen=True)
class PinwheelMember:
    """One stick in one panel.

    ``tail`` is the end that runs past the mathematical vertex and
    receives the previous member; ``head`` is the end cut square against
    the side of the next member.  Both are square crosscuts.
    """

    face: tuple[int, int, int]
    position: int
    edge: tuple[int, int]
    edge_class: str
    edge_length_in: float
    length_in: float
    tail: np.ndarray
    head: np.ndarray
    inward: np.ndarray
    """Unit vector, in the panel's plane, from the edge toward the middle."""
    normal: np.ndarray
    """Panel normal, pointing out of the dome: the bark faces this way."""
    bearing_length_in: float
    """How far the tail runs through the receiving member's band.

    The tail is cut on the far face of the member behind, so it crosses
    that member's whole width: this is the length of the contact patch
    the end-to-side joint bears on, and it is the reason the joint needs
    no notch."""
    tail_vertex_gap_in: float
    head_vertex_gap_in: float
    """How far each square-cut end stops short of the mathematical
    vertex.  Both are positive: no wood reaches a corner, which is what
    makes the corners references rather than endpoints."""

    @property
    def inset_in(self) -> float:
        """How much shorter the stick is than its reference edge."""
        return self.edge_length_in - self.length_in


@dataclass(frozen=True)
class Panel:
    """One of the forty independent triangular frames."""

    face: tuple[int, int, int]
    corners: np.ndarray
    normal: np.ndarray
    members: tuple[PinwheelMember, ...]

    @property
    def perimeter_in(self) -> float:
        return sum(member.edge_length_in for member in self.members)

    @property
    def timber_in(self) -> float:
        return sum(member.length_in for member in self.members)


def _panel_basis(corners: np.ndarray) -> tuple[np.ndarray, np.ndarray,
                                               np.ndarray]:
    """An in-plane frame for one face, plus its outward normal."""
    normal = normalize(np.cross(corners[1] - corners[0],
                                corners[2] - corners[0]))
    if float(np.dot(normal, corners.mean(axis=0))) < 0.0:
        normal = -normal
    axis_u = normalize(corners[1] - corners[0])
    axis_v = normalize(np.cross(normal, axis_u))
    return axis_u, axis_v, normal


def _line_intersection(point_a: np.ndarray, direction_a: np.ndarray,
                       point_b: np.ndarray, direction_b: np.ndarray) -> float:
    """Parameter along line A where it crosses line B, in 2D."""
    denominator = (direction_a[0] * direction_b[1]
                   - direction_a[1] * direction_b[0])
    if abs(denominator) < 1e-12:
        raise ValueError("pinwheel members are parallel; check the panel")
    offset = point_b - point_a
    return float((offset[0] * direction_b[1]
                  - offset[1] * direction_b[0]) / denominator)


@lru_cache(maxsize=8)
def pinwheel_panels(radius_in: float = 116.362,
                    member_width_in: float = 4.8,
                    gasket_in: float = 0.75) -> tuple[Panel, ...]:
    """Lay out all forty panels, each as a same-handed pinwheel.

    The panel outline is the face triangle inset by half the gasket, so
    that two neighbours plus the gasket between them come back to the
    true geometry.  Inside that outline each member sits with its bark
    face on its own edge line, runs past one mathematical vertex to the
    far side of the previous member, and is cut square at the other end
    against the side of the next one.
    """
    geometry = build_demo_geometry()
    class_by_edge = dict(zip(geometry.edges, geometry.edge_class_by_edge))
    panels: list[Panel] = []
    for face in geometry.hemisphere_faces:
        indices = tuple(int(value) for value in face)
        corners = geometry.vertices[list(indices)] * radius_in
        axis_u, axis_v, normal = _panel_basis(corners)
        origin = corners[0]

        def flatten(point: np.ndarray) -> np.ndarray:
            offset = point - origin
            return np.array([float(np.dot(offset, axis_u)),
                             float(np.dot(offset, axis_v))])

        def lift(point: np.ndarray) -> np.ndarray:
            return origin + axis_u * point[0] + axis_v * point[1]

        flat = [flatten(corner) for corner in corners]
        centre = sum(flat) / 3.0

        # Edge lines, inset by half a gasket so the wood never touches
        # its neighbour's wood.
        edge_point: list[np.ndarray] = []
        edge_dir: list[np.ndarray] = []
        inward: list[np.ndarray] = []
        for position in range(3):
            start, end = flat[position], flat[(position + 1) % 3]
            direction = (end - start) / float(np.linalg.norm(end - start))
            towards = centre - start
            side = np.array([-direction[1], direction[0]])
            if float(np.dot(side, towards)) < 0.0:
                side = -side
            edge_point.append(start + side * (gasket_in * 0.5))
            edge_dir.append(direction)
            inward.append(side)

        members: list[PinwheelMember] = []
        for position in range(3):
            previous = (position + 2) % 3
            following = (position + 1) % 3
            # The member's own line: bark face on the edge, so the
            # centreline sits half a width in.
            line_point = edge_point[position] \
                + inward[position] * (member_width_in * 0.5)
            # Tail: out to the far face of the member behind, which is
            # that member's own edge line.
            tail_t = _line_intersection(
                line_point, edge_dir[position],
                edge_point[previous], edge_dir[previous])
            # Head: cut square on the near face of the member ahead.
            head_t = _line_intersection(
                line_point, edge_dir[position],
                edge_point[following] + inward[following] * member_width_in,
                edge_dir[following])
            # The tail also crosses the near face of the member behind;
            # the distance between those two crossings is the bearing.
            near_t = _line_intersection(
                line_point, edge_dir[position],
                edge_point[previous] + inward[previous] * member_width_in,
                edge_dir[previous])
            bearing = abs(near_t - tail_t)
            low, high = min(tail_t, head_t), max(tail_t, head_t)
            tail = line_point + edge_dir[position] * low
            head = line_point + edge_dir[position] * high
            a_index = indices[position]
            b_index = indices[(position + 1) % 3]
            key = (a_index, b_index) if a_index < b_index else (b_index,
                                                                a_index)
            members.append(PinwheelMember(
                face=indices,
                position=position,
                edge=key,
                edge_class=class_by_edge[key],
                edge_length_in=float(np.linalg.norm(
                    corners[(position + 1) % 3] - corners[position])),
                length_in=float(abs(head_t - tail_t)),
                tail=lift(tail),
                head=lift(head),
                bearing_length_in=bearing,
                tail_vertex_gap_in=float(np.linalg.norm(
                    lift(tail) - corners[position])),
                head_vertex_gap_in=float(np.linalg.norm(
                    lift(head) - corners[(position + 1) % 3])),
                inward=(axis_u * inward[position][0]
                        + axis_v * inward[position][1]),
                normal=normal,
            ))
        panels.append(Panel(face=indices, corners=corners, normal=normal,
                            members=tuple(members)))
    return tuple(panels)


@dataclass(frozen=True)
class MemberClass:
    """One length of stick, and how many the frame needs."""

    edge_class: str
    count: int
    length_in: float
    edge_length_in: float
    inset_in: float
    bearing_length_in: float
    vertex_gap_in: float


def member_classes(radius_in: float, member_width_in: float,
                   gasket_in: float = 0.75) -> tuple[MemberClass, ...]:
    """The distinct stick lengths, counted over all forty panels."""
    buckets: dict[tuple[str, int], list[PinwheelMember]] = {}
    for panel in pinwheel_panels(radius_in, member_width_in, gasket_in):
        for member in panel.members:
            key = (member.edge_class, int(round(member.length_in * 1e3)))
            buckets.setdefault(key, []).append(member)
    classes = [
        MemberClass(
            edge_class=name,
            count=len(members),
            length_in=members[0].length_in,
            edge_length_in=members[0].edge_length_in,
            inset_in=members[0].inset_in,
            bearing_length_in=members[0].bearing_length_in,
            vertex_gap_in=min(members[0].tail_vertex_gap_in,
                              members[0].head_vertex_gap_in),
        )
        for (name, _length), members in buckets.items()
    ]
    return tuple(sorted(classes, key=lambda item: item.length_in))


def longest_member_in(radius_in: float, member_width_in: float,
                      gasket_in: float = 0.75) -> float:
    return max(item.length_in
               for item in member_classes(radius_in, member_width_in,
                                          gasket_in))


@lru_cache(maxsize=8)
def radius_for_member_length(target_in: float = 72.0,
                             member_width_in: float = 4.8,
                             gasket_in: float = 0.75) -> float:
    """The dome radius whose longest pinwheel member is ``target_in``.

    Member length grows with the radius but not proportionally -- the
    pinwheel overhang depends on the member's width, which does not
    change with the dome -- so this is solved rather than scaled.
    """
    low, high = 12.0, 600.0
    for _ in range(80):
        middle = (low + high) * 0.5
        if longest_member_in(middle, member_width_in, gasket_in) < target_in:
            low = middle
        else:
            high = middle
    return (low + high) * 0.5


# ----------------------------------------------------------------------
# The joint between panels
# ----------------------------------------------------------------------

@dataclass(frozen=True)
class GasketPlan:
    """Every seam in the shell, and the angles it has to close."""

    interior_seams: int
    rim_seams: int
    interior_length_in: float
    rim_length_in: float
    min_dihedral_deg: float
    max_dihedral_deg: float
    thickness_in: float

    @property
    def total_length_ft(self) -> float:
        return (self.interior_length_in + self.rim_length_in) / 12.0


@lru_cache(maxsize=8)
def gasket_plan(radius_in: float = 116.362,
                thickness_in: float = 0.75) -> GasketPlan:
    """One gasket per seam, sized off the model's own dihedral angles."""
    from .hubless_geometry import hubless_struts

    geometry = build_demo_geometry()
    interior = 0.0
    rim = 0.0
    interior_count = 0
    rim_count = 0
    dihedrals: list[float] = []
    seen: set[tuple[int, int]] = set()
    for strut in hubless_struts():
        if strut.edge in seen:
            continue
        seen.add(strut.edge)
        length = float(np.linalg.norm(
            geometry.vertices[strut.edge[0]] - geometry.vertices[strut.edge[1]]
        )) * radius_in
        if strut.dihedral_deg is None:
            rim += length
            rim_count += 1
        else:
            interior += length
            interior_count += 1
            dihedrals.append(strut.dihedral_deg)
    return GasketPlan(
        interior_seams=interior_count,
        rim_seams=rim_count,
        interior_length_in=interior,
        rim_length_in=rim,
        min_dihedral_deg=min(dihedrals),
        max_dihedral_deg=max(dihedrals),
        thickness_in=thickness_in,
    )


@dataclass(frozen=True)
class BuildPlan:
    """The whole shell, from two trees to a floor area."""

    log: LogModel
    trees: int
    design_diameter_in: float
    member_width_in: float
    member_depth_in: float
    member_area_in2: float
    radius_in: float
    longest_member_in: float
    shortest_member_in: float
    members_needed: int
    members_available: int
    timber_in_frame_ft: float
    gasket: GasketPlan

    @property
    def spare_members(self) -> int:
        return self.members_available - self.members_needed

    @property
    def diameter_ft(self) -> float:
        return self.radius_in * 2.0 / 12.0

    @property
    def floor_sqft(self) -> float:
        return math.pi * (self.radius_in / 12.0) ** 2

    @property
    def height_ft(self) -> float:
        return self.radius_in / 12.0

    @property
    def equivalent_two_by_fours(self) -> float:
        """How many 2x4s the same cross-section is worth."""
        return self.member_area_in2 / 8.0


@lru_cache(maxsize=4)
def build_plan(trees: int = 2, design_diameter_in: float = 12.5,
               log: LogModel = DEFAULT_LOG,
               gasket_in: float = 0.75) -> BuildPlan:
    """Size the dome to the stock two trees actually produce.

    ``design_diameter_in`` is the trunk diameter the layout is drawn
    for; it sets the member's width, which sets the pinwheel overhang.
    The strut length comes from the bucking, so the dome's size is a
    result rather than a choice.
    """
    width = sector_chord_in(design_diameter_in)
    radius = radius_for_member_length(log.strut_length_ft * 12.0, width,
                                      gasket_in)
    classes = member_classes(radius, width, gasket_in)
    summary = hubless_summary()
    return BuildPlan(
        log=log,
        trees=trees,
        design_diameter_in=design_diameter_in,
        member_width_in=width,
        member_depth_in=sector_depth_in(design_diameter_in),
        member_area_in2=sector_area_in2(design_diameter_in),
        radius_in=radius,
        longest_member_in=max(item.length_in for item in classes),
        shortest_member_in=min(item.length_in for item in classes),
        members_needed=summary.struts,
        members_available=trees * log.struts_per_tree,
        timber_in_frame_ft=sum(item.length_in * item.count
                               for item in classes) / 12.0,
        gasket=gasket_plan(radius, gasket_in),
    )


def bearing_area_in2(member_width_in: float, member_depth_in: float) -> float:
    """Contact area where one member's square end meets the next one's side.

    The end of a sector is the sector itself, so the bearing patch is
    the member's own cross-section -- which is the whole point of the
    end-to-side joint: nothing is notched away to make it.
    """
    return sector_area_in2(member_depth_in * 2.0)


# ----------------------------------------------------------------------
# The audit and the proof
# ----------------------------------------------------------------------

def wedge_report() -> str:
    """A plain-text audit of every figure this lesson puts on screen."""
    log = DEFAULT_LOG
    yields = tree_yield(log)
    plan = build_plan()
    lines = [
        "RADIAL WEDGE CONSTRUCTION -- CALCULATION AUDIT",
        "",
        "THE TREE",
        f"  taper                    {log.butt_diameter_in:.1f} in butt to "
        f"{log.top_diameter_in:.1f} in top over {log.usable_length_ft:.0f} ft",
        f"  sections                 {log.sections} x "
        f"{log.section_length_ft:.0f} ft",
        f"  solid wood               {yields.solid_bf:.1f} bf",
        f"  ripping kerf             {yields.kerf_bf:.1f} bf",
        f"  left in the wedges       {yields.wedge_bf:.1f} bf "
        f"({yields.wedge_recovery * 100:.1f}%)",
        f"  wedges per tree          {yields.wedge_count} at "
        f"{log.section_length_ft:.0f} ft",
        f"  struts per tree          {yields.strut_count} at "
        f"{log.strut_length_ft:.0f} ft",
        f"  board feet per strut     {yields.bf_per_strut:.2f}",
        "",
        "THE SAME TREE AS RECTANGLES",
        f"  computed 2x4x12 per tree {yields.two_by_four_count} "
        f"({yields.two_by_four_bf:.0f} bf, "
        f"{yields.two_by_four_recovery * 100:.1f}%)",
        f"  brief's estimate         {yields.brief_two_by_four_count} "
        f"({yields.brief_two_by_four_bf:.0f} bf)",
        f"  wedge gain vs computed   x{yields.gain_over_computed:.2f}",
        f"  wedge gain vs the brief  x{yields.gain_over_brief:.2f}",
    ]
    for row in section_rows(log):
        lines.append(
            f"  section {row.index + 1}: {row.butt_diameter_in:.1f} -> "
            f"{row.top_diameter_in:.1f} in, {row.solid_bf:.1f} bf, "
            f"kerf {row.kerf_bf:.1f} bf, 2x4 rows "
            f"{'+'.join(str(value) for value in row.two_by_four_rows)} = "
            f"{row.two_by_four_count}"
        )
    lines.extend([
        "",
        "THE MEMBER",
        f"  design trunk diameter    {plan.design_diameter_in:.1f} in",
        f"  sector angle             {SECTOR_ANGLE_DEG:.0f} deg",
        f"  bark-face width          {plan.member_width_in:.2f} in",
        f"  pith-to-bark depth       {plan.member_depth_in:.2f} in",
        f"  cross-section            {plan.member_area_in2:.2f} sq in "
        f"= {plan.equivalent_two_by_fours:.2f} x a true 2x4",
        "",
        "THE PANEL",
        f"  panels                   {len(pinwheel_panels(plan.radius_in, plan.member_width_in))}",
        f"  members                  {plan.members_needed} "
        "(three per panel, none shared)",
    ])
    for item in member_classes(plan.radius_in, plan.member_width_in):
        lines.append(
            f"  {item.edge_class:<5} x{item.count:<3} stick "
            f"{item.length_in:7.3f} in on a {item.edge_length_in:7.3f} in "
            f"reference edge, both ends square; bearing "
            f"{item.bearing_length_in:.3f} in, nearest corner "
            f"{item.vertex_gap_in:.3f} in away"
        )
    gasket = plan.gasket
    lines.extend([
        "",
        "THE SHELL",
        f"  dome radius              {plan.radius_in:.2f} in "
        f"({plan.diameter_ft:.2f} ft across)",
        f"  floor area               {plan.floor_sqft:.1f} sq ft",
        f"  timber in the frame      {plan.timber_in_frame_ft:.1f} ft",
        f"  seams between panels     {gasket.interior_seams} interior, "
        f"{gasket.rim_seams} at the rim",
        f"  gasket length            {gasket.total_length_ft:.1f} ft at "
        f"{gasket.thickness_in:.2f} in thick",
        f"  dihedral range           {gasket.min_dihedral_deg:.2f} to "
        f"{gasket.max_dihedral_deg:.2f} deg",
        f"  members needed/available {plan.members_needed} / "
        f"{plan.members_available} from {plan.trees} trees "
        f"({plan.spare_members} spare)",
        "",
        "External constants declared by this module:",
    ])
    for key, value, units, source in EXTERNAL_CONSTANTS:
        lines.append(f"  {key} = {value} {units}  ({source})")
    return "\n".join(lines)


def validate_wedge_geometry() -> None:
    """Prove the model before a frame of the lesson renders."""
    log = DEFAULT_LOG
    assert log.sections == 5, log.sections
    assert log.struts_per_tree == 80, log.struts_per_tree

    # The trunk's solid volume, and what the splits leave behind.
    yields = tree_yield(log)
    assert 400.0 < yields.solid_bf < 480.0, yields.solid_bf
    assert 0.0 < yields.kerf_bf < yields.solid_bf * 0.2, yields.kerf_bf
    assert yields.wedge_recovery > 0.85, yields.wedge_recovery
    # Packing rectangles into a round log must do worse than keeping the
    # round log, or the whole argument is backwards.
    assert yields.two_by_four_bf < yields.wedge_bf, yields
    assert yields.gain_over_brief > 1.2, yields.gain_over_brief
    assert yields.two_by_four_count < yields.brief_two_by_four_count, yields

    # A sector at nine inches of diameter is a two-by-four's worth of
    # wood, which is the claim the member chapter is built on.
    assert abs(sector_area_in2(9.0) - 8.0) < 0.1, sector_area_in2(9.0)

    plan = build_plan()
    panels = pinwheel_panels(plan.radius_in, plan.member_width_in)
    assert len(panels) == 40, len(panels)
    assert sum(len(panel.members) for panel in panels) == 120

    # Laying every bark face on its own reference edge insets all three
    # members, so each stick is shorter than its edge -- and no corner
    # is touched by wood, which is the claim the panel chapter makes.
    for panel in panels:
        assert panel.timber_in < panel.perimeter_in, panel.face
        for member in panel.members:
            assert 0.0 < member.inset_in < member.edge_length_in * 0.3, member
            assert member.bearing_length_in > 0.0, member
            assert member.tail_vertex_gap_in > 0.0, member
            assert member.head_vertex_gap_in > 0.0, member
            # Bark outward: the panel normal points away from the centre.
            assert float(np.dot(member.normal,
                                panel.corners.mean(axis=0))) > 0.0
            # The pinwheel is same-handed: every member is offset toward
            # the middle of its own panel.
            middle = panel.corners.mean(axis=0)
            midpoint = (member.tail + member.head) * 0.5
            assert float(np.dot(member.inward, middle - midpoint)) > 0.0

    # The dome is sized by the bucking, so the longest stick is the
    # strut length the tree gave us.
    assert abs(plan.longest_member_in - log.strut_length_ft * 12.0) < 0.05

    # Two trees have to cover the frame with something left over.
    assert plan.members_available > plan.members_needed
    assert plan.spare_members >= 30, plan.spare_members

    # The seam count has to agree with the hubless frame the panels are
    # built on: 55 interior seams and 10 at the rim.
    summary = hubless_summary()
    assert plan.gasket.interior_seams == summary.doubled_edges
    assert plan.gasket.rim_seams == summary.rim_edges
    assert summary.struts == plan.members_needed == 120
