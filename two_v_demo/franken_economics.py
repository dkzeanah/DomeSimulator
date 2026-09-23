"""What a franken-dome actually costs, and why dome labour is a flat rate.

Two arguments live here, and they are the commercial case for the whole
project.

**Labour is flat.**  A 2V dome of any diameter has the same 40 triangles,
the same 120 struts, the same 120 brackets and the same 960 screws.  A
dome twice as wide is not twice the work: it is the *same* work on longer
sticks.  Every process count in :func:`flat_rate_table` is identical down
every column, and only the material grows.  That is a very unusual
property for a building, and it is the reason a dome factory optimises
differently from a stick-frame factory: there are few processes, they
repeat, and improving one improves every dome you will ever build.

**The prototype was nearly free.**  The timber was self-harvested, the
brackets were folded from scrap, and the only cash that changed hands was
for screws.  The real future cost is the fibreglass, which is computed
here from actual areas rather than guessed.

Everything that is a purchased-goods figure is in
:data:`EXTERNAL_PRICES`, named and sourced, because those are the numbers
that move with the market and with your supplier.
"""

from __future__ import annotations

import math
from dataclasses import dataclass
from functools import lru_cache

from .geometry import DomeMeasurements, build_demo_geometry
from .hubless_geometry import hubless_summary
from .strut_stock import tally


GEOMETRY = build_demo_geometry()
SUMMARY = hubless_summary()


# ----------------------------------------------------------------------
# Purchased goods -- the only numbers here that are not geometry
# ----------------------------------------------------------------------

@dataclass(frozen=True)
class Price:
    key: str
    value: float
    units: str
    note: str


EXTERNAL_PRICES: tuple[Price, ...] = (
    Price("screw_box_250", 12.0, "USD per 250",
          "Exterior structural screws, big-box shelf price."),
    Price("resin_gallon", 62.0, "USD per gallon",
          "Polyester laminating resin, boatbuilding grade, with catalyst."),
    Price("cloth_sqyd", 4.20, "USD per square yard",
          "6 oz fibreglass cloth, plain weave."),
    Price("csm_sqyd", 2.60, "USD per square yard",
          "1.5 oz chopped strand mat."),
    Price("resin_coverage_sqft_per_gal", 40.0, "sq ft per gallon per layer",
          "Laminating resin wet-out plus one coat, typical hand layup."),
    Price("layup_layers", 2.0, "layers",
          "One mat layer for bulk, one cloth layer for a fair surface."),
    Price("waste_factor", 1.15, "multiplier",
          "Cutting waste and overlap on a compound-curved surface."),
)

PRICE = {item.key: item.value for item in EXTERNAL_PRICES}

SQFT_PER_SQYD = 9.0


# ----------------------------------------------------------------------
# The flat-rate argument
# ----------------------------------------------------------------------

@dataclass(frozen=True)
class DomeSize:
    """One diameter, with its counts and its materials."""

    radius_in: float

    @property
    def measurements(self) -> DomeMeasurements:
        return DomeMeasurements(self.radius_in)

    @property
    def diameter_ft(self) -> float:
        return self.radius_in * 2.0 / 12.0

    @property
    def floor_area_sqft(self) -> float:
        return math.pi * self.radius_in ** 2 / 144.0

    @property
    def shell_area_sqft(self) -> float:
        """Hemisphere surface, which is what gets fibreglassed."""
        return 2.0 * math.pi * self.radius_in ** 2 / 144.0

    # --- the counts that do not move ---------------------------------
    @property
    def triangles(self) -> int:
        return SUMMARY.triangles

    @property
    def struts(self) -> int:
        return SUMMARY.struts

    @property
    def brackets(self) -> int:
        return SUMMARY.triangles * 3

    @property
    def screws(self) -> int:
        return self.brackets * 8

    @property
    def processes(self) -> int:
        """Distinct shop operations. The same nine at any size.

        Named, in order, in :data:`PROCESSES`; the count is the length of
        that tuple so the list and the number cannot drift apart.
        """
        return len(PROCESSES)

    @property
    def process_counts(self) -> tuple[ProcessCount, ...]:
        """Each of the nine with how many times it happens at this size."""
        return tuple(ProcessCount(step, step.repetitions(self))
                     for step in PROCESSES)

    # --- the one that does ------------------------------------------
    @property
    def strut_feet(self) -> float:
        """Total linear feet of stick, which is the only thing that grows."""
        geometry = GEOMETRY
        total = 0.0
        for item in geometry.edge_classes:
            total += item.hemisphere_count * item.factor * self.radius_in
        # A hubless frame doubles every shared edge.
        doubled = (SUMMARY.doubled_edges * 2 + SUMMARY.rim_edges) / \
            len(geometry.hemisphere_edges)
        return total * doubled / 12.0

    # --- and how long one stick gets, which is what you carry ---------
    #
    # These are *cut* lengths, not chords. A hubless pinwheel insets every
    # member from the vertex by an amount that depends on the member's
    # width, and the width does not change with the dome -- so the stick
    # you pick up is shorter than the edge it spans, and by a different
    # margin at every diameter. Scaling a chord factor gets this wrong in
    # the unsafe direction, which is why ``wedge_geometry`` solves it.
    @property
    def member_classes(self):
        from . import book_math as bm
        from . import wedge_geometry as wg
        return wg.member_classes(self.radius_in, bm.BOOK_TREE.member_width_in,
                                 SOLO["gasket_in"])

    @property
    def long_member_ft(self) -> float:
        """The longest stick you actually have to handle, in feet."""
        return max(item.length_in for item in self.member_classes) / 12.0

    @property
    def short_member_ft(self) -> float:
        return min(item.length_in for item in self.member_classes) / 12.0

    @property
    def member_feet(self) -> float:
        """Linear feet of *cut member* standing in the finished frame.

        Not the same as :attr:`strut_feet`, and the gap is the pinwheel
        again. ``strut_feet`` totals the edge network -- chord lengths, the
        stock you have to own. This totals what is left after every member
        is inset from its vertices, which is what ends up in the building.
        The difference is the vertex gaps, and because the inset is set by
        member width rather than by radius, the two do not keep a constant
        ratio: a small dome loses proportionally more of its stock to gaps.
        """
        return sum(item.count * item.length_in
                   for item in self.member_classes) / 12.0

    @property
    def within_solo_reach(self) -> bool:
        """True when one person can still handle the longest stick alone."""
        return self.long_member_ft <= SOLO["solo_long_member_ft"] + 1e-9


def flat_rate_table(
    diameters_ft: tuple[float, ...] = (10.0, 16.0, 20.0, 30.0),
) -> tuple[DomeSize, ...]:
    return tuple(DomeSize(feet * 12.0 / 2.0) for feet in diameters_ft)


# ----------------------------------------------------------------------
# The nine operations
# ----------------------------------------------------------------------
#
# ``DomeSize.processes`` used to be the literal 9 with the names in a
# docstring, which meant the book's list and the book's count could drift
# apart without anything complaining.  They are one object now: the count
# is the length of this tuple, and a chapter that names the nine reads
# them from here.
#
# Each process also knows how many times it *repeats* at a given size, and
# that turns out to be the sharper version of the flat-rate claim.  Seven
# of the nine repeat an identical number of times at every diameter -- not
# merely "still on the list", the same count.  The two that move are the
# two that touch raw material and area rather than joints: felling, which
# follows linear feet of stick, and glassing, which follows the shell.

@dataclass(frozen=True)
class Process:
    """One shop operation, with what it is counted in at any size."""

    key: str
    name: str
    tool: str
    unit: str
    flat: bool
    note: str

    def repetitions(self, size: "DomeSize") -> float:
        return _PROCESS_COUNTS[self.key](size)


@dataclass(frozen=True)
class ProcessCount:
    """A process paired with how often it happens at one diameter."""

    process: Process
    count: float

    @property
    def display(self) -> str:
        if self.process.unit == "sq ft":
            return f"{self.count:,.0f} sq ft"
        return f"{self.count:,.0f} {self.process.unit}"


def _trees_for(size: DomeSize) -> float:
    """Whole trees a diameter needs, at this book's trunk."""
    from . import book_math as bm
    plan = bm.BOOK_TREE
    per_tree = plan.usable_length_ft * plan.sectors
    return float(math.ceil(size.member_feet / per_tree))


_PROCESS_COUNTS = {
    "fell": _trees_for,
    "rip": lambda size: float(size.struts),
    "crosscut": lambda size: float(size.struts),
    "fold": lambda size: float(size.brackets),
    "drill": lambda size: float(size.screws),
    "screw": lambda size: float(size.screws),
    "raise": lambda size: float(size.triangles),
    "sheathe": lambda size: float(size.triangles),
    "glass": lambda size: size.shell_area_sqft,
}


PROCESSES: tuple[Process, ...] = (
    Process("fell", "Fell", "chainsaw", "trees", False,
            "Drop the tree, limb it, buck it to section length. The only "
            "process whose count follows the timber rather than the joints, "
            "and the only one with weather and a chain in it."),
    Process("rip", "Rip", "mill or bandsaw", "members", True,
            "Split each round section into wedges along its length. The "
            "longest of the nine by hours, and therefore the one worth "
            "improving first."),
    Process("crosscut", "Crosscut", "mitre saw and jig", "members", True,
            "Cut each member to its solved length, both ends, on the jig "
            "that holds the angle so you do not have to measure it."),
    Process("fold", "Fold", "bench brake", "brackets", True,
            "Bend flat stock to the connector angle. One setup, then "
            "repetition; the angle lives in the tool, not in the operator."),
    Process("drill", "Drill", "drill press", "holes", True,
            "Pilot the bracket legs. One hole per screw, which is why this "
            "count is the largest number on the list."),
    Process("screw", "Screw", "impact driver", "screws", True,
            "Drive the frame together. The count is fixed by the bracket "
            "pattern, so it does not care how big the dome is."),
    Process("raise", "Raise", "cable and winch", "panels", True,
            "Lift each assembled triangle into place and tie it to its "
            "neighbours. Panels go up, not members -- that is what keeps "
            "this a one-person job at the top of the band."),
    Process("sheathe", "Sheathe", "knife and stapler", "panels", True,
            "Close each triangle. Still counted in panels, still forty of "
            "them, whatever the panels measure."),
    Process("glass", "Glass", "roller and brush", "sq ft", False,
            "Lay up the shell. The second process that scales, and it "
            "scales as the square, because it is priced by area."),
)


PROCESS = {step.key: step for step in PROCESSES}


# ----------------------------------------------------------------------
# What one person can handle -- declared, then spent
# ----------------------------------------------------------------------
#
# The flat rate is real but it is not unbounded, and the bound is not a
# structural one.  It is a handling one, and it is a *choice*: the longest
# stick the builder is willing to carry, hold at both ends of, and set into
# a triangle without a second pair of hands.  That number cannot be derived
# from geometry, so it is declared here with the reason, the way prices are.
# Everything downstream of it -- which diameters stay inside the band -- is
# then computed from the 2V chord factors.

@dataclass(frozen=True)
class Declared:
    """A figure chosen rather than solved, carrying why it was chosen."""

    key: str
    value: float
    units: str
    note: str


SOLO_LIMITS: tuple[Declared, ...] = (
    Declared("solo_long_member_ft", 6.0, "feet",
             "Longest single member the builder will handle alone. Chosen, "
             "not derived: it is the most one person wants to carry, stand "
             "both ends of, and set without help. Assembled triangles go up "
             "on an overhead cable and winch slung in the trees, so the limit "
             "is on the stick in your hands, not on the lift."),
    Declared("gasket_in", 0.75, "inches",
             "Gasket allowance between mating members, as used by "
             "book_math.tree_first. Repeated here so the handling band and "
             "the book's own dome are solved on identical terms."),
)

SOLO = {item.key: item.value for item in SOLO_LIMITS}


@dataclass(frozen=True)
class SoloBand:
    """The band of diameters a declared member limit allows.

    The diameter is *solved*, not scaled. Member length grows with the
    radius but not proportionally, because the pinwheel overhang depends on
    the member's width and the width does not change with the dome -- so
    this defers to :func:`wedge_geometry.radius_for_member_length`, the same
    inverse :func:`book_math.tree_first` uses to size a dome to a log.
    """

    member_ft: float

    @property
    def radius_in(self) -> float:
        from . import book_math as bm
        from . import wedge_geometry as wg
        return wg.radius_for_member_length(
            self.member_ft * 12.0, bm.BOOK_TREE.member_width_in,
            SOLO["gasket_in"])

    @property
    def diameter_ft(self) -> float:
        """The dome whose longest cut member is the declared limit."""
        return self.radius_in * 2.0 / 12.0

    @property
    def radius_ft(self) -> float:
        return self.diameter_ft / 2.0

    @property
    def floor_area_sqft(self) -> float:
        return math.pi * self.radius_ft ** 2

    @property
    def short_member_ft(self) -> float:
        """The other stick at that diameter, for the cut list."""
        return DomeSize(self.radius_in).short_member_ft

    @property
    def sizes_inside(self) -> tuple[DomeSize, ...]:
        return tuple(s for s in flat_rate_table() if s.within_solo_reach)

    @property
    def sizes_outside(self) -> tuple[DomeSize, ...]:
        return tuple(s for s in flat_rate_table() if not s.within_solo_reach)


def solo_band(member_ft: float | None = None) -> SoloBand:
    """The diameters one person can frame alone, given a handling limit."""
    limit = SOLO["solo_long_member_ft"] if member_ft is None else member_ft
    return SoloBand(limit)


# ----------------------------------------------------------------------
# The fibreglass bill
# ----------------------------------------------------------------------

@dataclass(frozen=True)
class GlassJob:
    """Everything that has to be laminated, and what it takes."""

    shell_sqft: float
    floor_under_sqft: float
    tower_sqft: float

    @property
    def total_sqft(self) -> float:
        return self.shell_sqft + self.floor_under_sqft + self.tower_sqft

    @property
    def layers(self) -> float:
        return PRICE["layup_layers"]

    @property
    def waste(self) -> float:
        return PRICE["waste_factor"]

    @property
    def fabric_sqft(self) -> float:
        """Cloth and mat area, per layer, with waste."""
        return self.total_sqft * self.waste

    @property
    def cloth_sqyd(self) -> float:
        return self.fabric_sqft / SQFT_PER_SQYD

    @property
    def csm_sqyd(self) -> float:
        return self.fabric_sqft / SQFT_PER_SQYD

    @property
    def resin_gallons(self) -> float:
        return (self.total_sqft * self.layers * self.waste
                / PRICE["resin_coverage_sqft_per_gal"])

    @property
    def resin_cost(self) -> float:
        return self.resin_gallons * PRICE["resin_gallon"]

    @property
    def cloth_cost(self) -> float:
        return self.cloth_sqyd * PRICE["cloth_sqyd"]

    @property
    def csm_cost(self) -> float:
        return self.csm_sqyd * PRICE["csm_sqyd"]

    @property
    def total_cost(self) -> float:
        return self.resin_cost + self.cloth_cost + self.csm_cost


def _tower_area_sqft() -> float:
    """Outside of the assembly line's centre utility column.

    Read off ``al_build`` rather than assumed, so if the column changes
    shape the glass bill follows it.
    """
    # Deliberately not wrapped in a try: an import failure here used to
    # be swallowed and return zero, which quietly cached a wrong area and
    # printed "utility tower 0 sq ft" as though it were a measurement.
    # A number that reaches the screen must fail loudly or be right.
    # Seeded and type-pinned. al_build.random_spec stores the serial but
    # does not seed from it, so an unseeded call returns a different dome
    # every time -- sometimes a shed with no column stage at all, which is
    # how this measured zero once and then 119 sq ft the next run.
    from .energetics import home_spec

    import al_build as AL

    catalog, _ = AL.build_dome_catalog(home_spec(1))
    column = [e for e in catalog.elements if e.stage == "column"]
    if not column:
        raise ValueError("al_build produced no column stage to measure")

    # The column's pieces overlap -- the risers sit inside the base -- so
    # its height is the span from the lowest bottom to the highest top,
    # never the sum of the parts.
    bottoms = [float(e.centroid[2]) - max(e.dims[2], 0.0) / 2.0 for e in column]
    tops = [float(e.centroid[2]) + max(e.dims[2], 0.0) / 2.0 for e in column]
    height_m = max(tops) - min(bottoms)
    widths = [max(e.dims[0], e.dims[1]) for e in column if any(e.dims)]
    radius_m = (sum(widths) / len(widths) / 2.0) if widths else 0.2
    area_m2 = 2.0 * math.pi * radius_m * max(0.3, height_m)
    return area_m2 * 10.7639


@lru_cache(maxsize=8)
def glass_job(radius_in: float = 120.0) -> GlassJob:
    """The laminating job for one franken-dome at this radius."""
    size = DomeSize(radius_in)
    return GlassJob(
        shell_sqft=size.shell_area_sqft,
        floor_under_sqft=size.floor_area_sqft,
        tower_sqft=_tower_area_sqft(),
    )


# ----------------------------------------------------------------------
# The floor
# ----------------------------------------------------------------------

@dataclass(frozen=True)
class Floor:
    """A round deck matching the dome, sitting on blocks."""

    radius_in: float
    joist_spacing_in: float = 16.0
    block_ring_count: int = 3

    @property
    def area_sqft(self) -> float:
        return math.pi * self.radius_in ** 2 / 144.0

    @property
    def perimeter_ft(self) -> float:
        return 2.0 * math.pi * self.radius_in / 12.0

    @property
    def joists(self) -> int:
        """Parallel joists across a circle at this spacing."""
        return max(1, int(2.0 * self.radius_in / self.joist_spacing_in) - 1)

    @property
    def joist_feet(self) -> float:
        """Total joist length: each chord across the circle."""
        total = 0.0
        for index in range(self.joists):
            offset = (index + 1) * self.joist_spacing_in - self.radius_in
            half = math.sqrt(max(0.0, self.radius_in ** 2 - offset ** 2))
            total += 2.0 * half
        return total / 12.0

    @property
    def blocks(self) -> int:
        """Piers: a centre block plus rings under the joist crossings."""
        return 1 + sum(6 * (ring + 1) for ring in range(self.block_ring_count))


# ----------------------------------------------------------------------
# The whole build, priced
# ----------------------------------------------------------------------

@dataclass(frozen=True)
class BuildCost:
    radius_in: float

    @property
    def size(self) -> DomeSize:
        return DomeSize(self.radius_in)

    @property
    def floor(self) -> Floor:
        return Floor(self.radius_in)

    @property
    def glass(self) -> GlassJob:
        return glass_job(self.radius_in)

    @property
    def screw_cost(self) -> float:
        boxes = math.ceil(self.size.screws / 250.0)
        return boxes * PRICE["screw_box_250"]

    @property
    def timber_cost(self) -> float:
        """Self-harvested. The chainsaw ran on fuel; the wood was free."""
        return 0.0

    @property
    def bracket_cost(self) -> float:
        """Folded from scrap washing-machine casing."""
        return 0.0

    @property
    def total(self) -> float:
        return (self.screw_cost + self.timber_cost + self.bracket_cost
                + self.glass.total_cost)

    @property
    def cost_per_sqft(self) -> float:
        return self.total / max(1.0, self.size.floor_area_sqft)


def economics_report(radius_in: float = 120.0) -> str:
    """A portable audit of the commercial case."""
    lines = ["FRANKEN-DOME ECONOMICS - CALCULATION AUDIT", ""]
    lines.append("--- labour is a flat rate ---")
    lines.append(f"  {'diameter':<10}{'floor':>9}{'shell':>9}"
                 f"{'tri':>6}{'struts':>8}{'brackets':>10}{'screws':>8}"
                 f"{'proc':>6}{'stick ft':>10}")
    for size in flat_rate_table():
        lines.append(
            f"  {size.diameter_ft:>7.0f} ft{size.floor_area_sqft:>9.0f}"
            f"{size.shell_area_sqft:>9.0f}{size.triangles:>6}"
            f"{size.struts:>8}{size.brackets:>10}{size.screws:>8}"
            f"{size.processes:>6}{size.strut_feet:>10.0f}")
    lines.append("")
    lines.append("  every count is identical at every size; only material grows")
    lines.append("")

    band = solo_band()
    lines.append("--- and where one pair of hands runs out ---")
    for item in SOLO_LIMITS:
        lines.append(f"  DECLARED {item.key:<22} {item.value:>6.2f} "
                     f"{item.units:<8} {item.note}")
    lines.append(f"  a {band.member_ft:.0f} ft long member is a dome "
                 f"{band.diameter_ft:.1f} ft across "
                 f"({band.floor_area_sqft:.0f} sq ft of floor)")
    lines.append(f"  its other stick is {band.short_member_ft:.2f} ft")
    for size in flat_rate_table():
        verdict = "solo" if size.within_solo_reach else "needs help or frequency"
        lines.append(f"  {size.diameter_ft:>5.0f} ft dome   long member "
                     f"{size.long_member_ft:>5.2f} ft   {verdict}")
    lines.append("")

    cost = BuildCost(radius_in)
    size, floor, glass = cost.size, cost.floor, cost.glass
    lines.append(f"--- the prototype at {size.diameter_ft:.0f} ft across ---")
    lines.append(f"  floor deck            {floor.area_sqft:.0f} sq ft, "
                 f"{floor.joists} joists, {floor.joist_feet:.0f} ft of joist")
    lines.append(f"  sitting on            {floor.blocks} blocks")
    lines.append("")
    lines.append(f"  shell to glass        {glass.shell_sqft:.0f} sq ft")
    lines.append(f"  floor underside       {glass.floor_under_sqft:.0f} sq ft")
    lines.append(f"  utility tower         {glass.tower_sqft:.0f} sq ft")
    lines.append(f"  total area            {glass.total_sqft:.0f} sq ft")
    lines.append(f"  with {glass.waste:.2f}x waste     "
                 f"{glass.fabric_sqft:.0f} sq ft of fabric per layer")
    lines.append("")
    lines.append(f"  resin                 {glass.resin_gallons:.1f} gal"
                 f"   ${glass.resin_cost:,.0f}")
    lines.append(f"  6 oz cloth            {glass.cloth_sqyd:.0f} sq yd"
                 f"   ${glass.cloth_cost:,.0f}")
    lines.append(f"  1.5 oz mat            {glass.csm_sqyd:.0f} sq yd"
                 f"   ${glass.csm_cost:,.0f}")
    lines.append(f"  screws                {size.screws} "
                 f"           ${cost.screw_cost:,.0f}")
    lines.append(f"  timber (self-harvested)          $0")
    lines.append(f"  brackets (scrap, folded by hand) $0")
    lines.append("")
    lines.append(f"  TOTAL                            ${cost.total:,.0f}")
    lines.append(f"  per square foot of floor         "
                 f"${cost.cost_per_sqft:,.2f}")
    lines.append("")
    counts = tally()
    lines.append(f"  round logs consumed   {counts.logs_needed():.0f}")
    lines.append("")
    lines.append("purchased-goods prices this model takes on authority:")
    for item in EXTERNAL_PRICES:
        lines.append(f"  {item.key:<30} {item.value:>8.2f} {item.units:<28} "
                     f"{item.note}")
    return "\n".join(lines)


def validate_economics() -> None:
    """Prove the commercial case before it goes on screen."""
    sizes = flat_rate_table()
    assert len(sizes) >= 3

    # The whole argument: counts identical, material growing.
    first = sizes[0]
    for size in sizes:
        assert size.triangles == first.triangles == 40
        assert size.struts == first.struts == 120
        assert size.brackets == first.brackets == 120
        assert size.screws == first.screws == 960
        assert size.processes == first.processes
    for earlier, later in zip(sizes, sizes[1:]):
        assert later.diameter_ft > earlier.diameter_ft
        assert later.strut_feet > earlier.strut_feet
        assert later.floor_area_sqft > earlier.floor_area_sqft
        # Area grows with the square of diameter; sticks only linearly.
        ratio = later.diameter_ft / earlier.diameter_ft
        assert math.isclose(later.strut_feet / earlier.strut_feet, ratio,
                            rel_tol=1e-6), (earlier.strut_feet, later.strut_feet)
        assert math.isclose(later.floor_area_sqft / earlier.floor_area_sqft,
                            ratio ** 2, rel_tol=1e-6)

    # A hemisphere's shell is exactly twice its floor.
    for size in sizes:
        assert math.isclose(size.shell_area_sqft, size.floor_area_sqft * 2.0,
                            rel_tol=1e-9)

    # The handling band. The declared limit picks out a diameter through the
    # wedge solver, and the round trip has to close: solve for the diameter,
    # cut the members at it, and the longest one is the limit again.
    band = solo_band()
    assert band.member_ft == SOLO["solo_long_member_ft"] == 6.0
    round_trip = DomeSize(band.radius_in).long_member_ft
    assert math.isclose(round_trip, band.member_ft, rel_tol=1e-4), round_trip

    # The cut member is shorter than the chord it spans, because the pinwheel
    # insets it from the vertex -- and by a *different* fraction at every
    # diameter, which is exactly why this is solved rather than scaled. If
    # these two ever came out proportional, the solver would have been
    # replaced by a multiplication and the band would be wrong.
    fractions = []
    for size in sizes:
        chord = size.measurements.long_center_length / 12.0
        assert size.long_member_ft < chord, (size.diameter_ft, chord)
        assert size.long_member_ft > size.short_member_ft
        fractions.append(size.long_member_ft / chord)
        # A dome is inside the band exactly when it is no wider than the
        # diameter the limit picks out.  No third answer.
        assert size.within_solo_reach == (
            size.diameter_ft <= band.diameter_ft + 1e-6)
    assert max(fractions) - min(fractions) > 0.05, fractions

    # The band has to actually split the table, or the caveat is decoration.
    assert band.sizes_inside and band.sizes_outside
    assert len(band.sizes_inside) + len(band.sizes_outside) == len(sizes)

    # And the convergence worth knowing: the book's own two-tree dome is
    # sized by the same 6 ft stick, so the largest dome one person can frame
    # alone and the largest dome two trees will yield are the same dome.
    from . import book_math as bm
    assert math.isclose(bm.tree_first().radius_in, band.radius_in,
                        rel_tol=1e-6)

    # Cut stock versus edge network. The frame always holds less linear foot-
    # age than the chords it spans, because every member is inset, and the
    # book's own dome has to agree with book_math about how much.
    for size in sizes:
        assert 0.0 < size.member_feet < size.strut_feet, size.diameter_ft
    assert math.isclose(DomeSize(band.radius_in).member_feet,
                        bm.tree_first().timber_in_frame_ft, rel_tol=1e-9)
    # The edge network is exactly linear in diameter; cut members are not,
    # and the book says so rather than rounding the difference away.
    edge_ratio = sizes[-1].strut_feet / sizes[0].strut_feet
    cut_ratio = sizes[-1].member_feet / sizes[0].member_feet
    assert math.isclose(edge_ratio,
                        sizes[-1].diameter_ft / sizes[0].diameter_ft,
                        rel_tol=1e-6)
    assert cut_ratio > edge_ratio + 0.2, (cut_ratio, edge_ratio)

    # The nine operations. The count is the list, the list is ordered, and
    # seven of the nine repeat identically at every diameter -- which is the
    # flat rate stated at its sharpest.
    assert len(PROCESSES) == first.processes == 9
    assert len({step.key for step in PROCESSES}) == len(PROCESSES)
    flat_keys = {step.key for step in PROCESSES if step.flat}
    assert len(flat_keys) == 7, sorted(flat_keys)
    baseline = {item.process.key: item.count
                for item in first.process_counts}
    for size in sizes:
        counts = {item.process.key: item.count for item in size.process_counts}
        assert set(counts) == set(baseline)
        for step in PROCESSES:
            if step.flat:
                assert counts[step.key] == baseline[step.key], step.key
            assert counts[step.key] > 0, step.key
    # The two that move must actually move across the table, or the claim
    # that seven are flat is trivially true of all nine.
    for key in ("fell", "glass"):
        assert sizes[-1].process_counts[
            [s.key for s in PROCESSES].index(key)].count > baseline[key], key

    floor = Floor(120.0)
    assert floor.joists > 1
    assert 0 < floor.joist_feet < floor.joists * 2 * floor.radius_in / 12.0
    assert floor.blocks > 6

    glass = glass_job(120.0)
    # The tower is part of the job; a zero here means the column was not
    # measured, which is how it silently vanished from the bill once.
    assert glass.tower_sqft > 0.0, "utility tower measured as zero"
    # And it must be the same every run, or the bill is fiction.
    assert _tower_area_sqft() == _tower_area_sqft()
    assert glass.shell_sqft > glass.floor_under_sqft
    assert glass.total_sqft > glass.shell_sqft
    assert glass.resin_gallons > 0.0
    assert glass.fabric_sqft > glass.total_sqft  # waste is additive
    assert glass.total_cost > 0.0

    cost = BuildCost(120.0)
    # The headline: free wood, free brackets, and glass dominating.
    assert cost.timber_cost == 0.0 and cost.bracket_cost == 0.0
    assert cost.glass.total_cost > cost.screw_cost, "glass should dominate"
    assert cost.total > 0.0
    assert cost.cost_per_sqft > 0.0

    for item in EXTERNAL_PRICES:
        assert item.key and item.units and item.note
        assert item.value >= 0.0
