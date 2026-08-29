"""What a pristine 2V dome costs at shelf prices, and how cheap it goes.

The franken-dome answered "what if the wood is free".  This answers the
other question: buy everything, build it properly, and what is the floor
price of a 314 square foot dome home?

Every quantity here is computed off the geometry.  Every *price* is a
shelf quote and lives in :data:`PRICES`, because those move with the
market and with your store.

Two findings worth knowing before reading the numbers:

**The bottom ring is exactly half the shell.**  Sorting the forty
triangles by height and taking the lower twenty gives 50.0% of the area,
to three decimals.  That is not a coincidence of this radius -- it is a
property of the 2V hemisphere -- and it is what makes the "cowboy hat"
option exactly a half-price laminate rather than roughly one.

**Resin, not timber, is the cost.**  At boat-epoxy prices the laminate
is more than the entire frame, floor, sheathing and insulation combined.
Every route to a cheaper dome runs through the resin line.
"""

from __future__ import annotations

import math
from dataclasses import dataclass
from functools import lru_cache

import numpy as np

from .geometry import build_demo_geometry
from .hubless_geometry import hubless_summary


GEOMETRY = build_demo_geometry()
SUMMARY = hubless_summary()

FLOOR_SQFT = 314.0
"""The build being priced: a 20 ft diameter dome, 314 sq ft of floor."""


# ----------------------------------------------------------------------
# Shelf prices -- the only numbers here that are not computed
# ----------------------------------------------------------------------

@dataclass(frozen=True)
class Price:
    key: str
    value: float
    units: str
    note: str


PRICES: tuple[Price, ...] = (
    Price("board_2x6x12", 12.0, "USD each",
          "2x6x12 SPF, Lowes shelf price. Yields two struts."),
    Price("board_2x6x12_pt", 15.0, "USD each",
          "2x6x12 pressure treated. Yields two struts."),
    Price("board_2x4x20_pt", 22.0, "USD each", "2x4x20 pressure treated pine."),
    Price("board_2x6x20", 24.0, "USD each", "2x6x20 SPF."),
    Price("board_2x6x20_pt", 32.0, "USD each", "2x6x20 pressure treated."),
    Price("osb_half_4x8", 15.0, "USD per sheet", "1/2 in OSB, 4x8, 32 sq ft."),
    Price("foam_1in_4x8", 17.0, "USD per sheet",
          "R-3.9 1 in faced polystyrene board, 4x8."),
    Price("epoxy_gallon", 160.0, "USD per gallon",
          "5:1 boat epoxy with hardener."),
    Price("cloth_sqyd", 4.20, "USD per square yard", "6 oz fibreglass cloth."),
    Price("fixtures", 2000.0, "USD",
          "Kitchen, bath, electrical and the hatch, at the low end."),
    Price("hardware", 250.0, "USD",
          "Screws, bolts, brackets and fasteners throughout."),
    Price("resin_oz_wetout", 1.4, "oz per sq ft",
          "Boatbuilding rule of thumb: wetting out one layer of 6 oz cloth."),
    Price("resin_oz_full", 3.0, "oz per sq ft",
          "The same rule with multiple coats, fillets and sealing bare "
          "plywood -- which is the number that actually gets used."),
)

PRICE = {item.key: item.value for item in PRICES}

OZ_PER_GALLON = 128.0
SQFT_PER_OSB = 32.0
SQFT_PER_SQYD = 9.0
BOARD_LENGTH_FT = 12.0
STRUTS_PER_BOARD = 2
FLOOR_SHEET_WASTE = 1.18
"""Cutting a circle out of rectangles throws away about this much."""

FLOOR_LINEAR_FT = 720.0
"""Framing and decking for a 314 sq ft round floor, as measured on the
prototype: about 18 x 40 linear feet."""


# ----------------------------------------------------------------------
# Areas, computed
# ----------------------------------------------------------------------

@lru_cache(maxsize=1)
def face_areas() -> tuple[float, ...]:
    """Every triangle's area at unit radius, sorted low to high."""
    rows = []
    for face in GEOMETRY.hemisphere_faces:
        points = GEOMETRY.vertices[[int(v) for v in face]]
        sides = [float(np.linalg.norm(points[i] - points[(i + 1) % 3]))
                 for i in range(3)]
        half = sum(sides) / 2.0
        area = math.sqrt(max(0.0, half * (half - sides[0]) * (half - sides[1])
                             * (half - sides[2])))
        rows.append((float(points[:, 2].mean()), area))
    rows.sort()
    return tuple(area for _, area in rows)


def shell_sqft(radius_in: float) -> float:
    """Flat panel area of the whole shell, not the sphere it approximates."""
    return sum(face_areas()) * radius_in ** 2 / 144.0


def upper_shell_sqft(radius_in: float) -> float:
    """The top twenty triangles: the 'cowboy hat'.

    Exactly half the shell, because the 2V hemisphere splits into two
    equal-area rings of twenty. Verified in :func:`validate_costing`.
    """
    return sum(face_areas()[20:]) * radius_in ** 2 / 144.0


def radius_for_floor(floor_sqft: float = FLOOR_SQFT) -> float:
    """Radius in inches that gives this floor area."""
    return math.sqrt(floor_sqft * 144.0 / math.pi)


# ----------------------------------------------------------------------
# One costed build
# ----------------------------------------------------------------------

@dataclass(frozen=True)
class Build:
    """One way of building the same dome."""

    name: str
    pressure_treated: bool
    cowboy_hat: bool
    """Laminate only the upper twenty triangles."""
    resin_rate: str = "full"
    """``full`` (3 oz/sq ft) or ``wetout`` (1.4)."""
    insulated: bool = True
    floor_sqft: float = FLOOR_SQFT

    # -- geometry -----------------------------------------------------
    @property
    def radius_in(self) -> float:
        return radius_for_floor(self.floor_sqft)

    @property
    def diameter_ft(self) -> float:
        return self.radius_in * 2.0 / 12.0

    @property
    def shell_sqft(self) -> float:
        return shell_sqft(self.radius_in)

    @property
    def glass_sqft(self) -> float:
        """What actually gets laminated."""
        if self.cowboy_hat:
            return upper_shell_sqft(self.radius_in)
        return self.shell_sqft + self.floor_sqft

    # -- lumber -------------------------------------------------------
    @property
    def board_price(self) -> float:
        return PRICE["board_2x6x12_pt" if self.pressure_treated
                     else "board_2x6x12"]

    @property
    def strut_boards(self) -> int:
        """One 12 ft board yields two struts; the dome needs 120."""
        return math.ceil(SUMMARY.struts / STRUTS_PER_BOARD)

    @property
    def floor_boards(self) -> int:
        return math.ceil(FLOOR_LINEAR_FT / BOARD_LENGTH_FT)

    @property
    def lumber_cost(self) -> float:
        return (self.strut_boards + self.floor_boards) * self.board_price

    # -- sheathing and insulation -------------------------------------
    @property
    def panel_box_in(self) -> tuple[float, float]:
        """Bounding box of the largest triangle, base by height."""
        biggest = (0.0, 0.0)
        for face in GEOMETRY.hemisphere_faces:
            points = GEOMETRY.vertices[[int(v) for v in face]] * self.radius_in
            sides = [float(np.linalg.norm(points[i] - points[(i + 1) % 3]))
                     for i in range(3)]
            base = max(sides)
            half = sum(sides) / 2.0
            area = math.sqrt(max(0.0, half * (half - sides[0])
                                 * (half - sides[1]) * (half - sides[2])))
            height = 2.0 * area / base
            if base * height > biggest[0] * biggest[1]:
                biggest = (base, height)
        return biggest

    @property
    def panel_fits_sheet(self) -> bool:
        """Can one triangle be cut whole from a 4x8 sheet?

        At 20 ft the answer is no -- the panel is 74 x 64 inches and the
        sheet is 48 x 96 -- which is why the sheet count below is one per
        triangle rather than an area division.
        """
        base, height = self.panel_box_in
        return ((base <= 96.0 and height <= 48.0)
                or (base <= 48.0 and height <= 96.0))

    @property
    def shell_panels(self) -> int:
        """Sheets for the shell.

        Dividing area by sheet area gives 18 sheets and is a fantasy: it
        assumes triangles tile a rectangle with no offcut. They do not.
        Whole panels do not fit a sheet at this size, so each triangle is
        seamed from two pieces cut from one sheet -- and the laminate is
        what makes the seam disappear. One sheet per triangle.
        """
        if self.panel_fits_sheet:
            # Two per sheet when they do fit, which is the small shelter.
            return math.ceil(len(GEOMETRY.hemisphere_faces) / 2)
        return len(GEOMETRY.hemisphere_faces)

    @property
    def floor_panels(self) -> int:
        """Decking for a round floor, with the offcut from the circle."""
        return math.ceil(self.floor_sqft / SQFT_PER_OSB * FLOOR_SHEET_WASTE)

    @property
    def sheathing_panels(self) -> int:
        return self.shell_panels + self.floor_panels

    @property
    def sheathing_cost(self) -> float:
        return self.sheathing_panels * PRICE["osb_half_4x8"]

    @property
    def insulation_cost(self) -> float:
        if not self.insulated:
            return 0.0
        return self.sheathing_panels * PRICE["foam_1in_4x8"]

    # -- laminate -----------------------------------------------------
    @property
    def resin_oz_per_sqft(self) -> float:
        return PRICE["resin_oz_full" if self.resin_rate == "full"
                     else "resin_oz_wetout"]

    @property
    def resin_gallons(self) -> float:
        return self.glass_sqft * self.resin_oz_per_sqft / OZ_PER_GALLON

    @property
    def resin_cost(self) -> float:
        return self.resin_gallons * PRICE["epoxy_gallon"]

    @property
    def cloth_sqyd(self) -> float:
        return self.glass_sqft / SQFT_PER_SQYD

    @property
    def cloth_cost(self) -> float:
        return self.cloth_sqyd * PRICE["cloth_sqyd"]

    @property
    def glass_cost(self) -> float:
        return self.resin_cost + self.cloth_cost

    # -- totals -------------------------------------------------------
    @property
    def fixtures_cost(self) -> float:
        return PRICE["fixtures"]

    @property
    def hardware_cost(self) -> float:
        return PRICE["hardware"]

    @property
    def shell_total(self) -> float:
        """Everything but the fit-out: a weathertight empty dome."""
        return (self.lumber_cost + self.sheathing_cost + self.insulation_cost
                + self.glass_cost + self.hardware_cost)

    @property
    def total(self) -> float:
        return self.shell_total + self.fixtures_cost

    @property
    def per_sqft(self) -> float:
        return self.total / self.floor_sqft

    def lines(self) -> tuple[tuple[str, float], ...]:
        return (
            (f"lumber ({self.strut_boards + self.floor_boards} boards @ "
             f"${self.board_price:.0f})", self.lumber_cost),
            (f"sheathing ({self.sheathing_panels} OSB)", self.sheathing_cost),
            (f"insulation ({self.sheathing_panels} foam)",
             self.insulation_cost),
            (f"epoxy ({self.resin_gallons:.1f} gal @ "
             f"${PRICE['epoxy_gallon']:.0f})", self.resin_cost),
            (f"cloth ({self.cloth_sqyd:.0f} sq yd)", self.cloth_cost),
            ("hardware", self.hardware_cost),
            ("fixtures", self.fixtures_cost),
        )


def build_variants() -> tuple[Build, ...]:
    return (
        Build("CHEAPEST", pressure_treated=False, cowboy_hat=True,
              resin_rate="wetout", insulated=False),
        Build("BUDGET", pressure_treated=False, cowboy_hat=True,
              resin_rate="full"),
        Build("PRISTINE, HAT", pressure_treated=True, cowboy_hat=True,
              resin_rate="full"),
        Build("PRISTINE, FULL", pressure_treated=True, cowboy_hat=False,
              resin_rate="full"),
    )


# ----------------------------------------------------------------------
# Starting a factory
# ----------------------------------------------------------------------

@dataclass(frozen=True)
class Startup:
    """What a hundred thousand dollars actually buys."""

    capital: float = 100_000.0

    EQUIPMENT: tuple[tuple[str, float], ...] = (
        ("Flatbed truck, used", 18_000.0),
        ("Trailer", 6_000.0),
        ("Crane lift / telehandler, used", 28_000.0),
        ("Sawmill, portable band", 9_000.0),
        ("Table saw, mitre saw, sleds and jigs", 3_500.0),
        ("Compressor, guns, hand tools", 3_000.0),
        ("Laminating kit, extraction, PPE", 4_500.0),
        ("Shop rent and power, six months", 9_000.0),
        ("Insurance, licence, permits", 5_000.0),
    )

    @property
    def equipment_total(self) -> float:
        return sum(value for _, value in self.EQUIPMENT)

    @property
    def working_capital(self) -> float:
        return self.capital - self.equipment_total

    def units_fundable(self, build: Build) -> float:
        """How many domes the leftover cash can put materials into."""
        return self.working_capital / build.total


def costing_report(floor_sqft: float = FLOOR_SQFT) -> str:
    """A portable audit of the build cost and the startup case."""
    lines = ["PRISTINE DOME COSTING - CALCULATION AUDIT", ""]
    sample = build_variants()[0]
    lines.append(f"  floor            {floor_sqft:.0f} sq ft "
                 f"({sample.diameter_ft:.1f} ft across)")
    lines.append(f"  shell panels     {sample.shell_sqft:.0f} sq ft")
    lines.append(f"  upper 20 only    {upper_shell_sqft(sample.radius_in):.0f}"
                 f" sq ft   (exactly half: the 2V hemisphere splits evenly)")
    base, height = sample.panel_box_in
    lines.append(f"  largest panel    {base:.1f} x {height:.1f} in"
                 f"   -> 4x8 sheet (48x96): "
                 f"{'fits' if sample.panel_fits_sheet else 'DOES NOT FIT'}")
    lines.append(f"  sheets           {sample.shell_panels} shell "
                 f"(1 per triangle, seamed) + {sample.floor_panels} floor")
    lines.append(f"  struts           {SUMMARY.struts} from "
                 f"{sample.strut_boards} boards at 2 per 12 ft board")
    lines.append(f"  floor framing    {FLOOR_LINEAR_FT:.0f} linear ft = "
                 f"{sample.floor_boards} boards")
    lines.append("")

    for build in build_variants():
        lines.append(f"--- {build.name} ---")
        for label, value in build.lines():
            lines.append(f"    {label:<44} ${value:>9,.0f}")
        lines.append(f"    {'SHELL ONLY':<44} ${build.shell_total:>9,.0f}")
        lines.append(f"    {'TOTAL WITH FIXTURES':<44} ${build.total:>9,.0f}")
        lines.append(f"    {'per sq ft':<44} ${build.per_sqft:>9,.2f}")
        lines.append("")

    startup = Startup()
    lines.append("--- starting a factory on $100,000 ---")
    for label, value in startup.EQUIPMENT:
        lines.append(f"    {label:<44} ${value:>9,.0f}")
    lines.append(f"    {'EQUIPMENT TOTAL':<44} ${startup.equipment_total:>9,.0f}")
    lines.append(f"    {'WORKING CAPITAL LEFT':<44} "
                 f"${startup.working_capital:>9,.0f}")
    budget = build_variants()[1]
    lines.append(f"    materials for {startup.units_fundable(budget):.1f} "
                 f"domes at the BUDGET price")
    lines.append("")
    lines.append("shelf prices this model takes on authority:")
    for item in PRICES:
        lines.append(f"  {item.key:<22} {item.value:>9.2f} {item.units:<22} "
                     f"{item.note}")
    return "\n".join(lines)


def validate_costing() -> None:
    """Prove the costing before any of it goes on screen."""
    areas = face_areas()
    assert len(areas) == 40, len(areas)

    # The claim the cowboy hat rests on: the lower twenty triangles are
    # exactly half the shell. This is a property of the 2V hemisphere,
    # not an accident of one radius.
    lower = sum(areas[:20])
    upper = sum(areas[20:])
    assert math.isclose(lower, upper, rel_tol=1e-9), (lower, upper)
    for radius in (60.0, 120.0, 180.0):
        assert math.isclose(upper_shell_sqft(radius), shell_sqft(radius) / 2.0,
                            rel_tol=1e-9)

    assert math.isclose(radius_for_floor(314.0) * 2 / 12.0, 20.0, rel_tol=0.02)

    builds = build_variants()
    assert len(builds) >= 4
    for build in builds:
        assert build.strut_boards * 2 >= SUMMARY.struts
        assert build.sheathing_panels > 0
        assert build.resin_gallons > 0.0
        assert build.total > build.shell_total  # fixtures are extra
        assert build.per_sqft > 0.0

    cheapest, budget, hat, full = builds
    # Each step up must cost more than the one below it.
    assert cheapest.total < budget.total < hat.total < full.total, \
        [b.total for b in builds]
    # The hat really does halve the laminate.
    assert math.isclose(hat.glass_sqft, hat.shell_sqft / 2.0, rel_tol=1e-9)
    assert full.glass_sqft > hat.glass_sqft * 2.0  # full adds the floor too
    # Pressure treating only moves the lumber line.
    assert hat.lumber_cost > budget.lumber_cost
    assert hat.glass_cost == budget.glass_cost
    # The headline: at boat-epoxy prices the laminate beats the structure.
    assert full.glass_cost > (full.lumber_cost + full.sheathing_cost
                              + full.insulation_cost), "resin should dominate"
    # And the target the whole exercise is aimed at.
    assert budget.total < 15_000.0, budget.total

    startup = Startup()
    assert startup.equipment_total < startup.capital
    assert startup.working_capital > 0.0
    assert startup.units_fundable(budget) >= 1.0

    for item in PRICES:
        assert item.key and item.units and item.note and item.value > 0.0

    # franken_economics uses 2*pi*R^2 -- the *smooth* hemisphere. This
    # module sums the flat triangles, which is what actually gets sheathed
    # and laminated. The faceted surface is smaller; assert the gap is the
    # size it should be so neither number can drift unnoticed.
    reference = build_variants()[0]
    smooth = 2.0 * math.pi * reference.radius_in ** 2 / 144.0
    faceted = reference.shell_sqft
    assert faceted < smooth, (faceted, smooth)
    assert 0.90 < faceted / smooth < 0.95, faceted / smooth

    # The nesting claim: at 20 ft a panel genuinely does not fit a sheet.
    assert not reference.panel_fits_sheet
    naive = math.ceil(reference.shell_sqft / SQFT_PER_OSB)
    assert reference.shell_panels > naive, (reference.shell_panels, naive)
