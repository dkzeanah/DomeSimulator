"""The arithmetic behind *2 Trees: Build Your (D)Home*.

Every number the book prints comes from here, and everything here comes from
geometry that already exists in this repository -- :mod:`wedge_geometry` for
the tree and the pinwheel, :mod:`raw_wedge_bridge` for the solved dome itself,
:mod:`hubless_geometry` for the strut count.  Nothing in this module restates a
figure another module already derives.

The book teaches two ways to size a wedge dome, and they run in opposite
directions:

**Design first** -- you know the dome you want.  Pick a radius, and the
pinwheel layout tells you how long each of the 120 members has to be, how much
trunk that eats, and what floor you end up standing on.

**Tree first** -- you know the tree you have.  Buck it into sections, split each
section into eight, and the length of a section decides the dome.  You do not
choose the diameter; you find out what it is.

Both are solved with the same function pair.  ``longest_member_in`` maps a
radius to a member length; ``radius_for_member_length`` inverts it.  The book
shows the two directions closing on the same dome, because that round trip is
the proof that neither method is a rule of thumb.

A note on two tree models
-------------------------
:mod:`wedge_geometry` carries a 60-foot trunk bucked into 12-foot sections,
each split into eight and then *crosscut in the middle* -- eighty six-foot
struts per tree.  The book's headline model buckes to six feet directly, so a
section is a strut and there is no crosscut: sixty-four struts from a
forty-eight-foot trunk.  Both are shown, side by side, in
:func:`reconcile_tree_models`.  They disagree because they are different cuts
of different trees, not because either is wrong, and the book says so on the
page rather than quietly picking the flattering one.
"""

from __future__ import annotations

import math
from dataclasses import dataclass
from functools import lru_cache

from . import wedge_geometry as wg
from .hubless_geometry import hubless_summary


# ----------------------------------------------------------------------
# Declared constants: things that cannot be derived from geometry.
#
# Everything below is an input to the book, not a result of it.  Each one
# carries the reason it is here and how sure we are of it, and the book puts
# this table on the page before it uses any of these numbers.
# ----------------------------------------------------------------------

@dataclass(frozen=True)
class Declared:
    """One number that had to be looked up, bought, or decided."""

    key: str
    value: float
    unit: str
    kind: str
    """One of ``measured``, ``priced``, ``decided``, ``estimated``."""
    reason: str


DECLARED: tuple[Declared, ...] = (
    Declared("saw_displacement_cc", 38.2, "cc", "measured",
             "Husqvarna 120 Mark II, the small consumer saw this build was "
             "done with. Check the plate on your own saw before quoting it."),
    Declared("saw_bar_in", 16.0, "in", "measured",
             "Bar length supplied with that saw. Sets the deepest single "
             "plunge, and so the largest trunk one pass can halve."),
    Declared("saw_price_usd", 199.0, "usd", "priced",
             "Shelf price of that saw at a big-box store, rounded. The book "
             "compares it against a bandsaw mill, not against nothing."),
    Declared("chain_kerf_in", 0.25, "in", "measured",
             "Cut width of a standard chain. Four kerf-diameters leave the "
             "log per section; this is what makes recovery 88% and not 100%."),
    Declared("two_by_four_price_usd", 8.88, "usd", "priced",
             "2x4x16 untreated pine, the material this method replaces."),
    Declared("build_days", 14.0, "days", "decided",
             "The fortnight the story covers: fell to standing frame."),
    Declared("cutting_afternoon_struts", 30.0, "struts", "measured",
             "Struts ripped in one six-hour afternoon once the method was "
             "settled. One observation, not an average."),
    Declared("cutting_afternoon_hours", 6.0, "hours", "measured",
             "Length of that afternoon."),
    Declared("gasket_thickness_in", 0.75, "in", "decided",
             "Key, spline or hose between neighbouring panels. A build "
             "choice: change it and every member length moves."),
    Declared("head_overfit_in", 6.0, "in", "decided",
             "Stock deliberately left long on the head end so error leaves as "
             "offcut instead of accumulating around the triangle."),
    Declared("butt_allowance_in", 8.0, "in", "decided",
             "Spare stock held past the butt cut while that cut is made."),
    Declared("saw_fuel_tank_l", 0.28, "L", "estimated",
             "Fuel tank of the saw. A retailer's listing for the 120 Mark III "
             "gives 0.28 L and an unverified listing for the Mark II gives "
             "0.30 L; neither manufacturer page checked prints it, and the "
             "project's own notes disagree about which Mark the saw is. Read it "
             "off your own saw before quoting a fuel figure."),
    Declared("saw_fuel_tank_high_l", 0.37, "L", "estimated",
             "The largest tank figure in circulation for this size of saw, kept "
             "so a fuel total is shown as a range rather than as a point that "
             "rests on one unverified listing."),
    Declared("brief_strut_value_usd", 10.0, "usd", "estimated",
             "What this project's own early brief put one strut at. It was "
             "reached by doubling a volume ratio for safety rather than by "
             "measuring a cross-section, so it is an estimate and a generous "
             "one. Kept, not deleted: the chapter that recomputes the figure "
             "has to be able to show what it is correcting. The hourly rate "
             "it implies is derived from it, never declared beside it."),
)

LITRES_PER_US_GALLON = 3.785411784
"""Exact: the US gallon is defined as 231 cubic inches, which is this many litres."""

DECLARED_BY_KEY = {item.key: item for item in DECLARED}


def declared(key: str) -> float:
    """One declared constant's value, by key, with a clear error if absent."""
    try:
        return DECLARED_BY_KEY[key].value
    except KeyError:
        raise ValueError(
            f"unknown declared constant {key!r}; the book will not invent one. "
            f"Known: {', '.join(sorted(DECLARED_BY_KEY))}") from None


# ----------------------------------------------------------------------
# The frame the book is about, straight from the solved dome
# ----------------------------------------------------------------------

@lru_cache(maxsize=1)
def frame_counts() -> tuple[int, int, int]:
    """(members, panels, unique edges) of the 2V hemisphere this book builds.

    Read off :mod:`hubless_geometry`, the same source the films use, so the
    book cannot drift away from them.

    The third figure is *edges*, not seams. Every panel boundary is an edge,
    but the ones around the open rim have nothing on the other side, so they
    are not joints. :func:`panel_seam_count` is the number of seams a builder
    actually has to close.
    """
    summary = hubless_summary()
    return summary.struts, summary.triangles, summary.unique_edges


@lru_cache(maxsize=1)
def panel_seam_count() -> int:
    """Seams between two panels, counted on the solved dome itself.

    The simulator solves each one -- it knows a seam's fold angle and its
    key -- so it is the authority on how many there are, and it is fewer than
    the edge count because the rim edges join nothing.
    """
    from .raw_wedge_bridge import model
    return len(model().seams)


@dataclass(frozen=True)
class EdgeAccounting:
    """Why 40 triangles need 120 members when there are only 65 edges.

    This frame is *panelised*: each triangle is built complete, on the
    ground, and keeps its own edge member. So an interior seam has two
    members in it -- one from each panel -- with the key between them,
    rather than one shared strut that both panels bolt to.

    That costs wood. It also buys the whole method: a panel that owns all
    three of its edges can be built flat on a jig, checked, skinned and
    lifted as a finished thing, and it can be taken out again later without
    disassembling its neighbours.
    """

    panels: int
    members_per_panel: int
    unique_edges: int
    shared_edges: int
    rim_edges: int

    @property
    def members(self) -> int:
        return self.panels * self.members_per_panel

    @property
    def members_from_edges(self) -> int:
        """The same count, reached from the edges instead of the panels."""
        return self.shared_edges * 2 + self.rim_edges

    @property
    def duplicated_members(self) -> int:
        """Members that exist only because edges are not shared."""
        return self.members - self.unique_edges

    @property
    def duplication_ratio(self) -> float:
        return self.members / self.unique_edges


@lru_cache(maxsize=1)
def edge_accounting() -> EdgeAccounting:
    """The panelisation arithmetic, and it has to close two ways."""
    members, panels, edges = frame_counts()
    shared = panel_seam_count()
    result = EdgeAccounting(
        panels=panels, members_per_panel=members // panels,
        unique_edges=edges, shared_edges=shared, rim_edges=edges - shared)
    if result.members_from_edges != result.members:
        raise AssertionError(
            "the frame does not add up: counting members panel by panel "
            f"gives {result.members}, counting them edge by edge gives "
            f"{result.members_from_edges}. One of the two is wrong and the "
            "book will not print either until it is known which.")
    return result


# A dressed 2x4 is not two inches by four. The book compares against both,
# because which one you mean changes the money chapter by a factor of 1.5.
NOMINAL_TWO_BY_FOUR_IN2 = 2.0 * 4.0
"""8.00 sq in. What ``2x4`` says, and what board-foot arithmetic assumes."""

DRESSED_TWO_BY_FOUR_IN2 = 1.5 * 3.5
"""5.25 sq in. What is actually on the rack, and what you would be buying."""


MEMBERS_IN_FRAME = frame_counts()[0]
"""120. The number in the book's subtitle, and it is counted, not chosen."""


# ----------------------------------------------------------------------
# The wedge against the board it replaces
#
# The case for radially split timber is usually made on area: an eighth of
# a round log holds more wood than a two-by-four.  That is true and it is
# computed below.  It is also not the whole story, because a section's
# resistance to bending depends on where its wood sits, not only on how
# much there is -- and a wedge puts a lot of its wood near the pith, where
# it does the least good.  Both numbers are computed here, and the book
# prints both.
# ----------------------------------------------------------------------

@dataclass(frozen=True)
class SectionProperties:
    """One cross-section, measured the way a structural section is measured.

    ``strong`` is bending about the axis that puts the section's depth to
    work; ``weak`` is the other one. For a wedge in a dome shell the strong
    direction is radial -- in and out of the shell -- because that is where
    pith-to-bark depth lies.
    """

    name: str
    area_in2: float
    strong_i_in4: float
    strong_s_in3: float
    weak_i_in4: float
    weak_s_in3: float
    depth_in: float
    width_in: float


def polygon_properties(points) -> tuple[float, float, float, float, float]:
    """(area, cx, cy, Ix, Iy) of a closed polygon, about its own centroid.

    Shoelace formulas rather than a lookup table, so a sector, a rectangle
    and any shape a reader wants to try all go through the same code and
    cannot disagree with each other by a factor somebody mistyped.
    """
    import numpy as np

    x = np.asarray([p[0] for p in points], dtype=np.float64)
    y = np.asarray([p[1] for p in points], dtype=np.float64)
    x1, y1 = np.roll(x, -1), np.roll(y, -1)
    cross = x * y1 - x1 * y
    area = cross.sum() / 2.0
    cx = ((x + x1) * cross).sum() / (6.0 * area)
    cy = ((y + y1) * cross).sum() / (6.0 * area)
    ix = ((y * y + y * y1 + y1 * y1) * cross).sum() / 12.0
    iy = ((x * x + x * x1 + x1 * x1) * cross).sum() / 12.0
    return abs(area), cx, cy, ix - area * cy * cy, iy - area * cx * cx


def _sector_polygon(diameter_in: float, sectors: int, steps: int = 2000):
    """One radial sector, with its bark face as a real arc, not a chord."""
    radius = diameter_in * 0.5
    half = math.pi / sectors
    points = [(0.0, 0.0)]
    for index in range(steps + 1):
        angle = -half + 2.0 * half * index / steps
        points.append((radius * math.cos(angle), radius * math.sin(angle)))
    return points


def sector_section(diameter_in: float,
                   sectors: int = wg.SECTORS_PER_LOG) -> SectionProperties:
    """Section properties of one split-log wedge."""
    points = _sector_polygon(diameter_in, sectors)
    area, cx, _cy, ix, iy = polygon_properties(points)
    # Extreme fibre distances from the centroidal axes.
    across = max(abs(p[1]) for p in points)
    along = max(abs(p[0] - cx) for p in points)
    return SectionProperties(
        name=f'{diameter_in:.0f}" log, 1/{sectors}',
        area_in2=area,
        # Radial bending -- in and out of the dome shell -- is the strong
        # direction, because that is the way the pith-to-bark depth runs.
        strong_i_in4=iy, strong_s_in3=iy / along,
        weak_i_in4=ix, weak_s_in3=ix / across,
        depth_in=diameter_in * 0.5,
        width_in=wg.sector_chord_in(diameter_in, sectors),
    )


def board_section(width_in: float, depth_in: float,
                  name: str = "") -> SectionProperties:
    """Section properties of a rectangular board, depth in the strong way."""
    strong_i = width_in * depth_in ** 3 / 12.0
    weak_i = depth_in * width_in ** 3 / 12.0
    return SectionProperties(
        name=name or f'{width_in:g} x {depth_in:g}',
        area_in2=width_in * depth_in,
        strong_i_in4=strong_i, strong_s_in3=strong_i / (depth_in * 0.5),
        weak_i_in4=weak_i, weak_s_in3=weak_i / (width_in * 0.5),
        depth_in=depth_in, width_in=width_in,
    )


DRESSED_BOARD = board_section(1.5, 3.5, "dressed 2x4, on edge")
NOMINAL_BOARD = board_section(2.0, 4.0, "nominal 2x4, on edge")


@dataclass(frozen=True)
class WedgeVersusBoard:
    """The head-to-head, with the flattering and unflattering both kept."""

    diameter_in: float
    sectors: int
    wedge: SectionProperties
    board: SectionProperties

    @property
    def area_ratio(self) -> float:
        """More wood, or less. Above 1.0 favours the wedge."""
        return self.wedge.area_in2 / self.board.area_in2

    @property
    def area_gain_pct(self) -> float:
        return (self.area_ratio - 1.0) * 100.0

    @property
    def stiffness_ratio(self) -> float:
        """Bending stiffness, strong axis both. This is the honest one."""
        return self.wedge.strong_i_in4 / self.board.strong_i_in4

    @property
    def strength_ratio(self) -> float:
        """Section modulus, strong axis both: bending strength."""
        return self.wedge.strong_s_in3 / self.board.strong_s_in3

    @property
    def flat_stiffness_ratio(self) -> float:
        """Against the same board laid flat, which is how a lot of cheap
        framing actually ends up loaded."""
        return self.wedge.strong_i_in4 / self.board.weak_i_in4

    @property
    def verdict(self) -> str:
        """One sentence a reader can quote without misleading anybody."""
        return (
            f"{self.area_gain_pct:+.0f}% wood, "
            f"{(self.stiffness_ratio - 1) * 100:+.0f}% bending stiffness, "
            f"{(self.strength_ratio - 1) * 100:+.0f}% bending strength")


def wedge_versus_board(diameter_in: float = 8.0,
                       sectors: int = wg.SECTORS_PER_LOG,
                       board: SectionProperties = DRESSED_BOARD
                       ) -> WedgeVersusBoard:
    """One wedge against one board, on area and on bending.

    The default is an eight-inch log, which is the modest case: a tree
    almost anybody can fell and move alone. Bigger logs favour the wedge
    more, so quoting the small one is the conservative choice.
    """
    return WedgeVersusBoard(diameter_in=diameter_in, sectors=sectors,
                            wedge=sector_section(diameter_in, sectors),
                            board=board)


# ----------------------------------------------------------------------
# How much wood a flat key costs you
# ----------------------------------------------------------------------

@dataclass(frozen=True)
class ShaveRow:
    """What one seam class costs if you plane its faces flat."""

    fold_angle_deg: float
    seams: int
    half_fold_deg: float
    raw_face_deg: float
    correction_deg: float
    land_in: float

    @property
    def depth_in(self) -> float:
        """Deepest cut across the mating land, at the bark edge."""
        return self.land_in * math.tan(math.radians(self.correction_deg))

    @property
    def as_fraction_of_depth(self) -> float:
        """That cut, against the whole pith-to-bark depth of the member."""
        return self.depth_in / BOOK_TREE.member_depth_in


def shaving_plan(land_in: float = 2.0,
                 sectors: int = wg.SECTORS_PER_LOG) -> tuple[ShaveRow, ...]:
    """What it costs to plane both seam faces flat, per seam class.

    The raw split face sits at half the sector angle from the member's own
    centreline. The face a flat key wants sits at half the seam's fold angle.
    The difference is what has to come off -- and over a narrow mating land
    it is a surprisingly small amount of wood, which is the argument for
    the shaved-flat option not being the betrayal it sounds like.
    """
    from .raw_wedge_bridge import model

    raw_face = 180.0 / sectors  # half of one sector's angle
    counts: dict[float, int] = {}
    for seam in model().seams:
        angle = round(float(seam.fold_angle_deg), 3)
        counts[angle] = counts.get(angle, 0) + 1
    return tuple(
        ShaveRow(fold_angle_deg=angle, seams=count,
                 half_fold_deg=angle * 0.5, raw_face_deg=raw_face,
                 correction_deg=raw_face - angle * 0.5, land_in=land_in)
        for angle, count in sorted(counts.items()))


# ----------------------------------------------------------------------
# How many operations each route actually takes
# ----------------------------------------------------------------------

MILL_ROUTE: tuple[tuple[str, str], ...] = (
    ("fell", "fell"),
    ("limb", "limb"),
    ("buck", "buck"),
    ("haul", "transport to the mill"),
    ("set up", "position on the mill"),
    ("slab", "remove the slabs"),
    ("rotate", "rotate the log"),
    ("cant", "square a cant"),
    ("resaw", "resaw repeatedly"),
    ("edge", "edge"),
    ("trim", "trim"),
    ("sort", "sort"),
    ("dry", "dry"),
    ("plane", "plane"),
)
"""Operations from a standing tree to a graded board. Fourteen.

Each entry is ``(short, full)``: the short form is what fits in a box on a
diagram, the full one is what the prose says. One list, so a drawing and a
paragraph cannot disagree about how many steps there are."""

WEDGE_ROUTE: tuple[tuple[str, str], ...] = (
    ("fell", "fell"),
    ("buck", "buck to structural length"),
    ("halve", "split through the centre"),
    ("quarter", "halves into quarters"),
    ("eighth", "quarters into eighths"),
    ("dry", "dry"),
    ("jig", "place in the jig"),
    ("cut", "cut the ends and the mating face"),
)
"""Operations from a standing tree to a member in the frame. Eight.

Note the two lists do not end in the same place, and the book says so: the
mill route stops at a graded board, which still has to be bought, carried
to site, cut to length and jointed. The wedge route above already includes
its joint cuts. Counted to the same finish line the gap is wider, not
narrower -- but this module will not quietly claim that; it prints both
lists and lets the difference in scope be visible.
"""


# ----------------------------------------------------------------------
# METHOD B, the one in the title: tree first
# ----------------------------------------------------------------------

@dataclass(frozen=True)
class TreeCutPlan:
    """A trunk bucked so that one section split eight ways *is* eight struts.

    The difference from :class:`wedge_geometry.LogModel` is the crosscut. That
    model buckes long and halves each wedge afterwards; this one buckes to
    finished length, so the only cuts are the fell, the bucking, and three rips
    per section. Fewer operations, and no chance of a crosscut landing where a
    knot has already spoiled the stick.
    """

    butt_diameter_in: float
    top_diameter_in: float
    usable_length_ft: float
    section_length_ft: float
    sectors: int = wg.SECTORS_PER_LOG
    kerf_in: float = 0.25

    # -- what the bucking gives ----------------------------------------
    @property
    def sections(self) -> int:
        return int(self.usable_length_ft // self.section_length_ft)

    @property
    def struts_per_section(self) -> int:
        return self.sectors

    @property
    def struts_per_tree(self) -> int:
        return self.sections * self.sectors

    @property
    def strut_length_ft(self) -> float:
        """A section is a strut: no crosscut, so these are the same thing."""
        return self.section_length_ft

    @property
    def offcut_ft(self) -> float:
        """Trunk left over because it did not fill a whole section."""
        return self.usable_length_ft - self.sections * self.section_length_ft

    # -- the log itself -------------------------------------------------
    def diameter_at(self, height_ft: float) -> float:
        fraction = height_ft / self.usable_length_ft
        return (self.butt_diameter_in
                + (self.top_diameter_in - self.butt_diameter_in) * fraction)

    @property
    def mid_diameter_in(self) -> float:
        return self.diameter_at(self.usable_length_ft * 0.5)

    @property
    def solid_bf(self) -> float:
        return wg.LogModel.frustum_bf(
            self.butt_diameter_in, self.top_diameter_in,
            self.usable_length_ft * 12.0)

    @property
    def kerf_bf(self) -> float:
        """Three rip passes per section cost four diameters of kerf.

        Two cuts cross the full diameter (the halving, then each quarter) and
        four run pith to bark for the eighths; four radius-length cuts are two
        diameters. That reasoning is
        :meth:`wedge_geometry.LogModel.kerf_bf_for`, applied section by
        section with this plan's own taper.
        """
        total = 0.0
        for index in range(self.sections):
            low = index * self.section_length_ft
            mid = self.diameter_at(low + self.section_length_ft * 0.5)
            total += (4.0 * mid * self.kerf_in * self.section_length_ft * 12.0
                      / wg.CUBIC_INCHES_PER_BOARD_FOOT)
        return total

    @property
    def wedge_bf(self) -> float:
        return self.solid_bf - self.kerf_bf

    @property
    def recovery(self) -> float:
        return self.wedge_bf / self.solid_bf

    @property
    def bf_per_strut(self) -> float:
        return self.wedge_bf / self.struts_per_tree

    # -- the member this tree produces ----------------------------------
    @property
    def member_width_in(self) -> float:
        """Bark-face width of a sector at the trunk's mid diameter."""
        return wg.sector_chord_in(self.mid_diameter_in, self.sectors)

    @property
    def member_depth_in(self) -> float:
        return wg.sector_depth_in(self.mid_diameter_in)

    @property
    def member_area_in2(self) -> float:
        return wg.sector_area_in2(self.mid_diameter_in, self.sectors)

    @property
    def equivalent_two_by_fours(self) -> float:
        """Cross-section of one strut, in units of a nominal 2x4 (8 sq in).

        The conservative reading, and the one that agrees with the board-foot
        arithmetic elsewhere in this repository.
        """
        return self.member_area_in2 / NOMINAL_TWO_BY_FOUR_IN2

    @property
    def equivalent_dressed_two_by_fours(self) -> float:
        """The same comparison against the board you would actually buy.

        A dressed 2x4 is 1.5 by 3.5 inches. Against that smaller section a
        strut replaces about half again as many boards -- which is the
        honest number if the question is *what would this have cost me at
        the store*, and the flattering one if the question is *how much wood
        is in it*. The book prints both and says which is which.
        """
        return self.member_area_in2 / DRESSED_TWO_BY_FOUR_IN2


BOOK_TREE = TreeCutPlan(
    butt_diameter_in=12.0,
    top_diameter_in=8.0,
    usable_length_ft=48.0,
    section_length_ft=6.0,
)
"""The tree the book is written around: eight six-foot sections, sixty-four
struts. Two of them is 128 struts for a frame that needs 120."""


@dataclass(frozen=True)
class TreeFirstResult:
    """What a stack of tree-cut struts turns into once it is a dome."""

    plan: TreeCutPlan
    trees: int
    struts_available: int
    struts_needed: int
    radius_in: float
    longest_member_in: float
    shortest_member_in: float
    member_classes: tuple[wg.MemberClass, ...]

    @property
    def spare_struts(self) -> int:
        return self.struts_available - self.struts_needed

    @property
    def spare_fraction(self) -> float:
        return self.spare_struts / self.struts_needed

    @property
    def enough(self) -> bool:
        return self.struts_available >= self.struts_needed

    @property
    def diameter_ft(self) -> float:
        return self.radius_in * 2.0 / 12.0

    @property
    def height_ft(self) -> float:
        return self.radius_in / 12.0

    @property
    def floor_sqft(self) -> float:
        return math.pi * (self.radius_in / 12.0) ** 2

    @property
    def timber_in_frame_ft(self) -> float:
        return sum(item.length_in * item.count
                   for item in self.member_classes) / 12.0

    @property
    def trees_strictly_needed(self) -> float:
        """Trees to cover the frame, as a fraction rather than a count."""
        return self.struts_needed / self.plan.struts_per_tree


@lru_cache(maxsize=8)
def tree_first(plan: TreeCutPlan = BOOK_TREE, trees: int = 2,
               gasket_in: float = 0.75) -> TreeFirstResult:
    """Size the dome to the tree, not the other way round.

    The section length is the longest member the frame may contain, so it goes
    straight into :func:`wedge_geometry.radius_for_member_length`. Everything
    after that is a consequence.
    """
    width = plan.member_width_in
    target_in = plan.strut_length_ft * 12.0
    radius = wg.radius_for_member_length(target_in, width, gasket_in)
    classes = wg.member_classes(radius, width, gasket_in)
    return TreeFirstResult(
        plan=plan,
        trees=trees,
        struts_available=trees * plan.struts_per_tree,
        struts_needed=MEMBERS_IN_FRAME,
        radius_in=radius,
        longest_member_in=max(item.length_in for item in classes),
        shortest_member_in=min(item.length_in for item in classes),
        member_classes=classes,
    )


# ----------------------------------------------------------------------
# METHOD A: design first
# ----------------------------------------------------------------------

@dataclass(frozen=True)
class DesignFirstResult:
    """What a chosen dome demands of the woodpile."""

    radius_in: float
    member_width_in: float
    member_classes: tuple[wg.MemberClass, ...]
    struts_needed: int
    plan: TreeCutPlan

    @property
    def longest_member_in(self) -> float:
        return max(item.length_in for item in self.member_classes)

    @property
    def shortest_member_in(self) -> float:
        return min(item.length_in for item in self.member_classes)

    @property
    def diameter_ft(self) -> float:
        return self.radius_in * 2.0 / 12.0

    @property
    def height_ft(self) -> float:
        return self.radius_in / 12.0

    @property
    def floor_sqft(self) -> float:
        return math.pi * (self.radius_in / 12.0) ** 2

    @property
    def bucking_length_ft(self) -> int:
        """The bucking length this dome asks for: the longest member, up.

        Bucking shorter than the longest member cannot be recovered by cutting
        more carefully, so this rounds up to the next whole foot.
        """
        return int(math.ceil(self.longest_member_in / 12.0))

    @property
    def sections_needed(self) -> float:
        """Whole sections to cover the frame, at eight struts each."""
        return self.struts_needed / self.plan.sectors

    @property
    def trunk_feet_needed(self) -> float:
        return self.sections_needed * self.bucking_length_ft

    @property
    def trees_needed(self) -> float:
        return self.trunk_feet_needed / self.plan.usable_length_ft

    @property
    def whole_trees_needed(self) -> int:
        return int(math.ceil(self.trees_needed))

    @property
    def timber_in_frame_ft(self) -> float:
        return sum(item.length_in * item.count
                   for item in self.member_classes) / 12.0


@lru_cache(maxsize=16)
def design_first(radius_in: float = 132.0,
                 plan: TreeCutPlan = BOOK_TREE,
                 gasket_in: float = 0.75) -> DesignFirstResult:
    """Start from the dome you want and find out what it costs in trunk."""
    width = plan.member_width_in
    classes = wg.member_classes(radius_in, width, gasket_in)
    return DesignFirstResult(
        radius_in=radius_in,
        member_width_in=width,
        member_classes=classes,
        struts_needed=MEMBERS_IN_FRAME,
        plan=plan,
    )


def design_first_for_floor(floor_sqft: float,
                           plan: TreeCutPlan = BOOK_TREE,
                           gasket_in: float = 0.75) -> DesignFirstResult:
    """Design first, entered the way people actually think: by floor area.

    Nobody wants a 132-inch radius. They want a room of a certain size, and the
    radius is what delivers it.
    """
    radius_in = math.sqrt(floor_sqft / math.pi) * 12.0
    return design_first(radius_in, plan, gasket_in)


# ----------------------------------------------------------------------
# The round trip: the two methods have to close
# ----------------------------------------------------------------------

@dataclass(frozen=True)
class RoundTrip:
    """One method's answer fed into the other, and the gap between them."""

    start_radius_in: float
    longest_member_in: float
    recovered_radius_in: float

    @property
    def radius_error_in(self) -> float:
        return abs(self.recovered_radius_in - self.start_radius_in)

    @property
    def closes(self) -> bool:
        """Within a thousandth of an inch, far finer than any saw."""
        return self.radius_error_in < 1e-3


def round_trip(radius_in: float = 132.0,
               plan: TreeCutPlan = BOOK_TREE,
               gasket_in: float = 0.75) -> RoundTrip:
    """Design a dome, read its longest member, then size a dome to it.

    If the two methods are the same arithmetic run in opposite directions this
    comes back where it started. The book prints the residual rather than
    asserting the claim.
    """
    width = plan.member_width_in
    longest = wg.longest_member_in(radius_in, width, gasket_in)
    recovered = wg.radius_for_member_length(longest, width, gasket_in)
    return RoundTrip(start_radius_in=radius_in,
                     longest_member_in=longest,
                     recovered_radius_in=recovered)


# ----------------------------------------------------------------------
# The two tree models, side by side
# ----------------------------------------------------------------------

@dataclass(frozen=True)
class TreeModelRow:
    """One way of bucking a trunk, and what it yields."""

    name: str
    usable_length_ft: float
    section_length_ft: float
    crosscut: bool
    strut_length_ft: float
    struts_per_tree: int
    solid_bf: float
    wedge_bf: float
    recovery: float
    bf_per_strut: float
    note: str

    @property
    def trees_for_frame(self) -> float:
        return MEMBERS_IN_FRAME / self.struts_per_tree


def reconcile_tree_models(plan: TreeCutPlan = BOOK_TREE
                          ) -> tuple[TreeModelRow, ...]:
    """The book's tree next to the films' tree, with neither hidden.

    These are different trees cut different ways. Printing both, difference
    visible, is the point: a reader with a taller trunk should get the taller
    trunk's answer, not the book's.
    """
    film = wg.tree_yield()
    log = film.log
    return (
        TreeModelRow(
            name="Book: buck to finished length",
            usable_length_ft=plan.usable_length_ft,
            section_length_ft=plan.section_length_ft,
            crosscut=False,
            strut_length_ft=plan.strut_length_ft,
            struts_per_tree=plan.struts_per_tree,
            solid_bf=plan.solid_bf,
            wedge_bf=plan.wedge_bf,
            recovery=plan.recovery,
            bf_per_strut=plan.bf_per_strut,
            note="A section is a strut. Three rips, no crosscut.",
        ),
        TreeModelRow(
            name="Films: buck long, halve the wedge",
            usable_length_ft=log.usable_length_ft,
            section_length_ft=log.section_length_ft,
            crosscut=True,
            strut_length_ft=log.strut_length_ft,
            struts_per_tree=log.struts_per_tree,
            solid_bf=film.solid_bf,
            wedge_bf=film.wedge_bf,
            recovery=film.wedge_recovery,
            bf_per_strut=film.bf_per_strut,
            note="A longer, fatter trunk handled in 12-foot lengths.",
        ),
    )


# ----------------------------------------------------------------------
# What the fortnight was worth
# ----------------------------------------------------------------------

@dataclass(frozen=True)
class Fortnight:
    """The two weeks, in struts, hours and dollars."""

    days: float
    struts_needed: int
    struts_per_afternoon: float
    hours_per_afternoon: float
    board_price_usd: float
    board_length_ft: float
    strut_length_ft: float

    @property
    def afternoons_of_ripping(self) -> float:
        return self.struts_needed / self.struts_per_afternoon

    @property
    def ripping_hours(self) -> float:
        return self.afternoons_of_ripping * self.hours_per_afternoon

    @property
    def struts_per_hour(self) -> float:
        return self.struts_per_afternoon / self.hours_per_afternoon

    @property
    def board_sections(self) -> float:
        """Strut-length pieces one purchased board would yield."""
        return self.board_length_ft / self.strut_length_ft

    @property
    def price_per_board_section_usd(self) -> float:
        return self.board_price_usd / self.board_sections

    def substitute_value_usd(self, equivalent_two_by_fours: float) -> float:
        """What one strut's worth of 2x4 would have cost at the store.

        The strut's cross-section is worth this many 2x4s, so its replacement
        cost is that many store pieces of the same length. A substitution
        value, not a market price for a log.
        """
        return self.price_per_board_section_usd * equivalent_two_by_fours

    def hourly_rate_usd(self, equivalent_two_by_fours: float) -> float:
        return (self.substitute_value_usd(equivalent_two_by_fours)
                * self.struts_per_hour)

    @property
    def minutes_per_strut(self) -> float:
        """How long one member spends at the rip, on average."""
        return 60.0 / self.struts_per_hour

    def improvement(self, fraction: float, builds: int = 1) -> "Improvement":
        """What shaving ``fraction`` off the ripping returns over ``builds``.

        The point of a nine-item process list is that effort spent on one
        item is not spent once.  This is that sentence as arithmetic: the
        saving expressed per strut, per build and across a run, and then
        measured in whole ripping stages so the payoff carries a unit a
        builder recognises rather than a percentage.
        """
        if not 0.0 < fraction < 1.0:
            raise ValueError(f"fraction must be a proper fraction: {fraction}")
        if builds < 1:
            raise ValueError(f"builds must be at least one: {builds}")
        return Improvement(self, fraction, builds)


@dataclass(frozen=True)
class Improvement:
    """A proportional speed-up at one process, spent over a run of domes."""

    work: Fortnight
    fraction: float
    builds: int

    @property
    def seconds_per_strut(self) -> float:
        """The saving at the scale you can actually aim at it."""
        return self.work.minutes_per_strut * self.fraction * 60.0

    @property
    def hours_per_build(self) -> float:
        return self.work.ripping_hours * self.fraction

    @property
    def hours_total(self) -> float:
        return self.hours_per_build * self.builds

    @property
    def afternoons_total(self) -> float:
        return self.hours_total / self.work.hours_per_afternoon

    @property
    def rip_stages(self) -> float:
        """The saving measured in whole ripping stages of one dome."""
        return self.hours_total / self.work.ripping_hours


def fortnight(plan: TreeCutPlan = BOOK_TREE) -> Fortnight:
    return Fortnight(
        days=declared("build_days"),
        struts_needed=MEMBERS_IN_FRAME,
        struts_per_afternoon=declared("cutting_afternoon_struts"),
        hours_per_afternoon=declared("cutting_afternoon_hours"),
        board_price_usd=declared("two_by_four_price_usd"),
        board_length_ft=16.0,
        strut_length_ft=plan.strut_length_ft,
    )


# ----------------------------------------------------------------------
# The fortnight, day by day, and what the saw drinks
# ----------------------------------------------------------------------

FORTNIGHT_PLAN: tuple[tuple[str, int, int, str], ...] = (
    ("saw", 0, 0, "day_zero_the_saw"),
    ("felling", 1, 2, "days_one_and_two_felling"),
    ("bucking", 3, 4, "days_three_and_four_bucking"),
    ("ripping", 5, 8, "days_five_to_eight_ripping"),
    ("jig", 9, 9, "the_jig"),
    ("panels", 10, 12, "days_ten_to_twelve_forty_panels"),
    ("raising", 13, 14, "days_thirteen_and_fourteen_raising"),
)
"""The book's fortnight as data: (phase, first day, last day, the chapter that
tells it). This is a plan, not a result, so :func:`validate_fortnight_plan` holds
it to what *is* derived -- it must end on the declared build length, and the
ripping block must be exactly the afternoons the measured cutting rate needs."""

HARVEST_PHASES = ("felling", "bucking", "ripping")
"""Tree standing to struts stacked: everything the chainsaw does."""


def phase_days(phase: str) -> int:
    """How many days the plan gives one phase."""
    for name, first, last, _ref in FORTNIGHT_PLAN:
        if name == phase:
            return last - first + 1
    raise ValueError(f"no phase {phase!r} in the fortnight; phases are "
                     f"{', '.join(row[0] for row in FORTNIGHT_PLAN)}")


def harvest_days() -> int:
    """Days from the first felling cut to the last strut ripped."""
    rows = [row for row in FORTNIGHT_PLAN if row[0] in HARVEST_PHASES]
    return max(row[2] for row in rows) - min(row[1] for row in rows) + 1


@dataclass(frozen=True)
class RippingFuel:
    """The fuel the ripping takes: measured burn, derived hours, declared tank.

    Only the ripping is counted, because only the ripping was timed with the fuel
    written down. Felling and bucking are not metered, and this figure says so
    rather than guessing them in.
    """

    tanks_per_hour: float
    hours: float
    tank_l: float
    tank_high_l: float

    @property
    def tanks(self) -> float:
        return self.tanks_per_hour * self.hours

    @property
    def litres(self) -> float:
        return self.tanks * self.tank_l

    @property
    def litres_high(self) -> float:
        return self.tanks * self.tank_high_l

    @property
    def gallons(self) -> float:
        return self.litres / LITRES_PER_US_GALLON

    @property
    def gallons_high(self) -> float:
        return self.litres_high / LITRES_PER_US_GALLON


@lru_cache(maxsize=1)
def ripping_fuel(plan: TreeCutPlan = BOOK_TREE) -> RippingFuel:
    # The burn rate is the why film's measurement, read from where that film reads
    # it, so the film and the book cannot quote two different saws.
    from .wedge_why_facts import cut_rate_model
    return RippingFuel(
        tanks_per_hour=cut_rate_model()["fuel_tanks_per_hour"],
        hours=fortnight(plan).ripping_hours,
        tank_l=declared("saw_fuel_tank_l"),
        tank_high_l=declared("saw_fuel_tank_high_l"),
    )


def validate_fortnight_plan() -> None:
    """The plan has to agree with the arithmetic it is a plan for."""
    from .book import BOOK

    days = [(first, last) for _name, first, last, _ref in FORTNIGHT_PLAN]
    assert days[0][0] == 0, "the fortnight starts on day zero"
    for (_, end), (start, _) in zip(days, days[1:]):
        assert start == end + 1, f"a gap or an overlap in the plan at day {start}"
    assert days[-1][1] == int(declared("build_days")), (
        "the plan does not end on the declared build length")
    afternoons = math.ceil(fortnight().afternoons_of_ripping - 1e-9)
    assert phase_days("ripping") == afternoons, (
        f"the plan gives {phase_days('ripping')} days to ripping, the measured "
        f"rate needs {afternoons}")
    for _name, _first, _last, ref in FORTNIGHT_PLAN:
        BOOK.by_ref(ref)  # raises if the chapter that tells it has gone
    fuel = ripping_fuel()
    assert fuel.litres < fuel.litres_high, "the fuel range is upside down"
    assert fuel.hours == fortnight().ripping_hours


# ----------------------------------------------------------------------
# The audit
# ----------------------------------------------------------------------

def book_math_report() -> str:
    """Plain-text audit of every figure the book puts on a page."""
    plan = BOOK_TREE
    tf = tree_first(plan)
    df = design_first(tf.radius_in, plan)
    trip = round_trip(tf.radius_in, plan)
    work = fortnight(plan)
    members, panels, edges = frame_counts()
    seams = panel_seam_count()

    lines = [
        "2 TREES -- CALCULATION AUDIT",
        "",
        "DECLARED CONSTANTS (inputs, not results)",
    ]
    for item in DECLARED:
        lines.append(f"  {item.key:<28} {item.value:>10.2f} {item.unit:<7}"
                     f" [{item.kind}]")
        lines.append(f"      {item.reason}")
    lines += [
        "",
        "THE FRAME (counted, not chosen)",
        f"  members                  {members}",
        f"  panels                   {panels}",
        f"  unique edges             {edges}",
        f"  panel-to-panel seams     {seams}",
        f"  rim edges (join nothing) {edges - seams}",
        "",
        "THE TREE (book model: buck to finished length)",
        f"  taper                    {plan.butt_diameter_in:.1f} in butt to "
        f"{plan.top_diameter_in:.1f} in top over "
        f"{plan.usable_length_ft:.0f} ft",
        f"  sections                 {plan.sections} x "
        f"{plan.section_length_ft:.0f} ft",
        f"  struts per section       {plan.struts_per_section}",
        f"  struts per tree          {plan.struts_per_tree}",
        f"  solid wood               {plan.solid_bf:.1f} bf",
        f"  kerf lost                {plan.kerf_bf:.1f} bf",
        f"  usable wood              {plan.wedge_bf:.1f} bf "
        f"({plan.recovery * 100:.1f}% recovery)",
        f"  wood per strut           {plan.bf_per_strut:.2f} bf",
        f"  member section           {plan.member_width_in:.2f} in wide x "
        f"{plan.member_depth_in:.2f} in deep = "
        f"{plan.member_area_in2:.2f} sq in",
        f"  worth this many 2x4s     {plan.equivalent_two_by_fours:.2f} "
        f"nominal (8.00 sq in)",
        f"                           "
        f"{plan.equivalent_dressed_two_by_fours:.2f} dressed "
        f"(5.25 sq in, what is on the rack)",
        "",
        "METHOD B -- TREE FIRST",
        f"  strut length available   {plan.strut_length_ft * 12:.1f} in",
        f"  dome radius that fits    {tf.radius_in:.3f} in",
        f"  diameter                 {tf.diameter_ft:.2f} ft",
        f"  height                   {tf.height_ft:.2f} ft",
        f"  floor                    {tf.floor_sqft:.1f} sq ft",
        f"  struts needed            {tf.struts_needed}",
        f"  struts from {tf.trees} trees        {tf.struts_available}"
        f"  (spare {tf.spare_struts})",
        f"  trees strictly needed    {tf.trees_strictly_needed:.2f}",
        f"  timber in the frame      {tf.timber_in_frame_ft:.1f} ft",
        "",
        "  member classes:",
    ]
    for item in tf.member_classes:
        lines.append(f"    {item.edge_class:<6} x{item.count:<4} "
                     f"{item.length_in:8.3f} in")
    lines += [
        "",
        "METHOD A -- DESIGN FIRST (entered at the same radius)",
        f"  radius chosen            {df.radius_in:.3f} in",
        f"  longest member           {df.longest_member_in:.3f} in",
        f"  shortest member          {df.shortest_member_in:.3f} in",
        f"  bucking length           {df.bucking_length_ft} ft",
        f"  sections needed          {df.sections_needed:.1f}",
        f"  trunk feet needed        {df.trunk_feet_needed:.1f} ft",
        f"  trees needed             {df.trees_needed:.2f} "
        f"(buy {df.whole_trees_needed})",
        "",
        "THE ROUND TRIP (the two methods must close)",
        f"  started at               {trip.start_radius_in:.6f} in",
        f"  longest member           {trip.longest_member_in:.6f} in",
        f"  came back to             {trip.recovered_radius_in:.6f} in",
        f"  residual                 {trip.radius_error_in:.2e} in "
        f"({'closes' if trip.closes else 'DOES NOT CLOSE'})",
        "",
        "THE TWO TREE MODELS, SIDE BY SIDE",
    ]
    for row in reconcile_tree_models(plan):
        lines += [
            f"  {row.name}",
            f"    {row.usable_length_ft:.0f} ft trunk in "
            f"{row.section_length_ft:.0f} ft sections, "
            f"crosscut: {'yes' if row.crosscut else 'no'}",
            f"    strut {row.strut_length_ft:.1f} ft, "
            f"{row.struts_per_tree} per tree, "
            f"{row.recovery * 100:.1f}% recovery, "
            f"{row.bf_per_strut:.2f} bf each",
            f"    trees for the frame: {row.trees_for_frame:.2f}",
            f"    {row.note}",
        ]
    lines += [
        "",
        "THE FORTNIGHT",
        f"  days                     {work.days:.0f}",
        f"  struts per hour          {work.struts_per_hour:.1f}",
        f"  hours of ripping         {work.ripping_hours:.1f}",
        f"  afternoons               {work.afternoons_of_ripping:.1f}",
        f"  store price per strut-length piece  "
        f"${work.price_per_board_section_usd:.2f}",
        f"  substitute value per strut, nominal "
        f"${work.substitute_value_usd(plan.equivalent_two_by_fours):.2f}",
        f"  substitute value per strut, dressed "
        f"${work.substitute_value_usd(plan.equivalent_dressed_two_by_fours):.2f}",
        f"  implied hourly rate, nominal        "
        f"${work.hourly_rate_usd(plan.equivalent_two_by_fours):.2f}",
        f"  implied hourly rate, dressed        "
        f"${work.hourly_rate_usd(plan.equivalent_dressed_two_by_fours):.2f}",
        "",
        "  The brief this project started from estimated $50 an hour. Both",
        "  figures above are lower, and the reason is worth printing: that",
        "  estimate valued a strut at $10 by doubling a 2.5x volume ratio",
        "  for safety, where this computes the ratio from the actual",
        "  cross-section of a sector at this trunk's mid diameter.",
        "",
        "  These are substitution values, computed from one measured",
        "  afternoon and a shelf price. They are not revenue, and nobody has",
        "  paid them. The book says so where it prints them.",
    ]
    return "\n".join(lines)


def validate_book_math() -> None:
    """Self-test: the book's arithmetic has to hold before it is printed."""
    plan = BOOK_TREE

    # The title has to be true: eight sections of eight is sixty-four, and
    # two trees has to actually cover a hundred and twenty members.
    assert plan.sections == 8, plan.sections
    assert plan.struts_per_section == 8, plan.struts_per_section
    assert plan.struts_per_tree == 64, plan.struts_per_tree
    assert plan.offcut_ft == 0.0, plan.offcut_ft

    result = tree_first(plan, trees=2)
    assert result.struts_needed == 120, result.struts_needed
    assert result.struts_available == 128, result.struts_available
    assert result.enough, "two trees must cover the frame"
    assert result.spare_struts == 8, result.spare_struts
    assert 1.0 < result.trees_strictly_needed < 2.0, \
        result.trees_strictly_needed

    # Recovery has to beat sawn lumber, and be a fraction, not a slogan.
    assert 0.80 < plan.recovery < 0.95, plan.recovery
    film = wg.tree_yield()
    assert plan.recovery > film.two_by_four_recovery, (
        plan.recovery, film.two_by_four_recovery)

    # The longest member the tree-first dome contains must be exactly the
    # stock length. If it were longer, the dome could not be built from it.
    stock_in = plan.strut_length_ft * 12.0
    assert abs(result.longest_member_in - stock_in) < 1e-6, \
        (result.longest_member_in, stock_in)

    # The two methods are one calculation run both ways.
    trip = round_trip(result.radius_in, plan)
    assert trip.closes, trip

    # Design first, entered by floor area, must land on the floor asked for.
    wanted = 300.0
    design = design_first_for_floor(wanted, plan)
    assert abs(design.floor_sqft - wanted) < 1e-6, design.floor_sqft
    assert design.whole_trees_needed >= 1, design.whole_trees_needed
    # A bigger dome cannot need less trunk than a smaller one.
    smaller = design_first_for_floor(wanted * 0.5, plan)
    assert smaller.longest_member_in < design.longest_member_in, \
        (smaller.longest_member_in, design.longest_member_in)

    # Member classes cover the whole frame exactly once.
    assert sum(item.count for item in result.member_classes) == 120, \
        [(i.edge_class, i.count) for i in result.member_classes]

    # Both tree models must be present, and disagree honestly.
    rows = reconcile_tree_models(plan)
    assert len(rows) == 2, rows
    assert rows[0].struts_per_tree != rows[1].struts_per_tree, rows

    # Seams are fewer than edges, because the rim joins nothing. If these
    # ever come out equal, something has closed the dome into a sphere.
    _members, _panels, edges = frame_counts()
    seams = panel_seam_count()
    assert 0 < seams < edges, (seams, edges)

    # A dressed board is smaller than a nominal one, so a strut replaces
    # more of them. Getting this backwards would flatter the book.
    assert (plan.equivalent_dressed_two_by_fours
            > plan.equivalent_two_by_fours), plan

    # The panelisation has to add up two independent ways, or the book is
    # describing a frame that cannot exist.
    edges = edge_accounting()
    assert edges.members == 120, edges
    assert edges.members_from_edges == edges.members, edges
    assert edges.duplicated_members == 55, edges.duplicated_members
    assert 1.5 < edges.duplication_ratio < 2.0, edges.duplication_ratio

    # The wedge-versus-board comparison must be honest in both directions:
    # more wood, and -- because a wedge puts much of it near the pith --
    # less bending strength than the same board stood on edge. If this ever
    # comes out flattering in every column, the comparison has broken.
    versus = wedge_versus_board(8.0)
    assert versus.area_ratio > 1.0, versus.area_ratio
    assert versus.strength_ratio < 1.0, versus.strength_ratio
    assert versus.flat_stiffness_ratio > 1.0, versus.flat_stiffness_ratio
    # Numerical section properties must agree with the closed forms.
    radius, alpha = 4.0, math.pi / wg.SECTORS_PER_LOG
    section = sector_section(8.0)
    assert abs(section.area_in2 - alpha * radius ** 2) < 1e-6, section
    weak_analytic = (radius ** 4 / 4.0) * (alpha - math.sin(alpha)
                                           * math.cos(alpha))
    assert abs(section.weak_i_in4 - weak_analytic) < 1e-4, \
        (section.weak_i_in4, weak_analytic)
    # A bigger log must favour the wedge more, or the "fell a bigger tree"
    # advice in the chapter is backwards.
    assert wedge_versus_board(12.0).area_ratio > versus.area_ratio

    # Shaving is a small cut, or the shaved-flat option is not the cheap
    # alternative the book says it is.
    rows = shaving_plan(2.0)
    assert rows, "no seam classes to shave"
    for row in rows:
        assert 0.0 < row.correction_deg < row.raw_face_deg, row
        assert 0.0 < row.depth_in < 1.0, row
        assert row.as_fraction_of_depth < 0.25, row
    assert sum(row.seams for row in rows) == panel_seam_count(), rows

    # The two processing routes are different lengths and honestly labelled.
    assert len(MILL_ROUTE) > len(WEDGE_ROUTE), (len(MILL_ROUTE),
                                                len(WEDGE_ROUTE))
    for route in (MILL_ROUTE, WEDGE_ROUTE):
        shorts = [short for short, _full in route]
        assert len(set(shorts)) == len(shorts), shorts
        for short, full in route:
            assert short and full, (short, full)
            assert len(short) <= 8, short

    # Every declared constant is reachable and labelled.
    for item in DECLARED:
        assert declared(item.key) == item.value
        assert item.kind in {"measured", "priced", "decided", "estimated"}, \
            item
        assert item.reason.strip(), item

    # The audit prints without raising, and mentions the residual.
    report = book_math_report()
    assert "ROUND TRIP" in report, report[:200]
    print("book_math OK: "
          f"{plan.struts_per_tree} struts/tree x 2 = "
          f"{result.struts_available} for a {result.struts_needed}-member "
          f"frame; {result.diameter_ft:.1f} ft dome, "
          f"{result.floor_sqft:.0f} sq ft floor; "
          f"round trip closes to {trip.radius_error_in:.1e} in")


if __name__ == "__main__":
    print(book_math_report())
    validate_book_math()
