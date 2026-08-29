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
        """Distinct operations: fell, rip, crosscut, fold, drill, screw,
        raise, sheathe, glass. The same nine at any size."""
        return 9

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


def flat_rate_table(
    diameters_ft: tuple[float, ...] = (10.0, 16.0, 20.0, 30.0),
) -> tuple[DomeSize, ...]:
    return tuple(DomeSize(feet * 12.0 / 2.0) for feet in diameters_ft)


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
