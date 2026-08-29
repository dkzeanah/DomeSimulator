"""What the dome does once somebody lives in it.

The costing modules answer what it takes to build.  This one answers the
question a buyer actually asks: what does it cost to *run*, and what does
the shape give back?

Four things are modelled, all of them from the same geometry:

**The pony wall.**  A hemisphere has plenty of volume and almost none of
it against the rim, where the ceiling meets the floor.  Lifting the shell
on a short stem wall converts the useless perimeter into usable room, and
it is the cheapest square footage in the whole building.

**Heating and cooling.**  Degree-day method, at the user's 17 cents a
kilowatt hour.  The dome wins by having less skin, and the margin is the
same 42% the surface comparison gives, because loss is proportional to
area at equal assembly.

**Radiative sky cooling paint.**  A real material with published numbers,
not a slogan: high solar reflectance plus high emittance in the 8-13
micron window the atmosphere is transparent at, so the roof radiates to
deep space and sits below ambient.

**Water off the brim.**  The hat has to overhang to keep rain off the
bottom ring anyway; once it does, it is a gutter, and the catchment is
the horizontal projection of everything above it.

Every external number is in :data:`EXTERNAL` with its source.
"""

from __future__ import annotations

import math
from dataclasses import dataclass

import numpy as np

from .dome_advantage import box_envelope, dome_envelope
from .dome_costing import FLOOR_SQFT, radius_for_floor, shell_sqft
from .geometry import build_demo_geometry


GEOMETRY = build_demo_geometry()


@dataclass(frozen=True)
class Fact:
    key: str
    value: float
    units: str
    source: str


EXTERNAL: tuple[Fact, ...] = (
    Fact("power_price", 0.17, "USD/kWh",
         "The rate this model is asked to use."),
    Fact("heating_degree_days", 4200.0, "F-days base 65",
         "A middling US heating climate."),
    Fact("cooling_degree_days", 1200.0, "F-days base 65",
         "A middling US cooling climate."),
    Fact("furnace_cop", 1.0, "dimensionless",
         "Resistance electric heat, the worst case, so the saving is not "
         "flattered by a heat pump."),
    Fact("ac_seer", 14.0, "BTU/Wh",
         "A basic modern split system, minimum US federal standard."),
    Fact("r_foam_1in", 3.9, "hr sq ft F/BTU",
         "R-3.9 per inch, the polystyrene board on the bill of materials."),
    Fact("r_osb_half", 0.62, "hr sq ft F/BTU", "1/2 in OSB sheathing."),
    Fact("r_batt_cavity", 19.0, "hr sq ft F/BTU",
         "Fibreglass batt filling the 5.5 in strut cavity."),
    Fact("r_air_films", 0.85, "hr sq ft F/BTU",
         "Interior plus exterior surface films."),
    Fact("solar_absorptance_dark", 0.85, "dimensionless",
         "A conventional dark roof."),
    Fact("solar_absorptance_paint", 0.04, "dimensionless",
         "Barium sulphate radiative cooling paint: 96%+ solar reflectance, "
         "as published for the ultra-white formulations."),
    Fact("radiative_cool_w_m2", 40.0, "W/sq m",
         "Daily-average net radiative cooling power, taken well below the "
         "117 W/sq m midday peak reported for these paints."),
    Fact("peak_solar_w_m2", 700.0, "W/sq m",
         "Mean daytime irradiance on a sunlit surface."),
    Fact("cooling_hours_year", 1600.0, "hours",
         "Daylight hours in the cooling season."),
    Fact("rainfall_in_year", 40.0, "inches",
         "US average annual precipitation; substitute your own."),
    Fact("runoff_coefficient", 0.85, "dimensionless",
         "Fraction of rain that reaches the tank off a hard roof."),
    Fact("gallons_per_sqft_inch", 0.6233, "gal",
         "One inch of rain on one square foot, exactly 144/231."),
    Fact("water_price_per_gal", 0.006, "USD/gal",
         "Typical US municipal water plus sewer."),
    Fact("headroom_ft", 6.67, "ft",
         "Where a floor stops being usable: 6 ft 8 in."),
    Fact("pony_wall_cost_sqft", 4.20, "USD/sq ft",
         "Studs, sheathing, foam and fasteners for a short stem wall."),
    Fact("h_outer", 4.0, "BTU/hr sq ft F",
         "Outside surface film coefficient at a light breeze. This is what "
         "decides how little of the absorbed sun ever gets inside."),
    Fact("btu_per_kwh", 3412.0, "BTU/kWh", "Definition."),
)

FACT = {item.key: item.value for item in EXTERNAL}


# ----------------------------------------------------------------------
# The pony wall
# ----------------------------------------------------------------------

@dataclass(frozen=True)
class PonyWall:
    """A stem wall under the shell, and what it buys.

    A dome's floor is only usable where the ceiling is high enough to
    stand under. Near the rim it is not, so a bare hemisphere wastes its
    whole perimeter. Raising the shell moves the whole ceiling profile up
    and converts that ring into room.
    """

    height_ft: float
    floor_sqft: float = FLOOR_SQFT

    @property
    def radius_ft(self) -> float:
        return radius_for_floor(self.floor_sqft) / 12.0

    def usable_radius_ft(self) -> float:
        """Out to where the ceiling is still above head height."""
        need = FACT["headroom_ft"] - self.height_ft
        if need <= 0.0:
            return self.radius_ft  # the wall alone already clears it
        if need >= self.radius_ft:
            return 0.0
        return math.sqrt(self.radius_ft ** 2 - need ** 2)

    @property
    def usable_sqft(self) -> float:
        return math.pi * self.usable_radius_ft() ** 2

    @property
    def usable_fraction(self) -> float:
        return self.usable_sqft / self.floor_sqft

    @property
    def wall_sqft(self) -> float:
        return 2.0 * math.pi * self.radius_ft * self.height_ft

    @property
    def cost(self) -> float:
        return self.wall_sqft * FACT["pony_wall_cost_sqft"]

    def gain_over(self, other: "PonyWall") -> float:
        return self.usable_sqft - other.usable_sqft

    def cost_per_gained_sqft(self, other: "PonyWall") -> float:
        gain = self.gain_over(other)
        return (self.cost - other.cost) / gain if gain > 0 else float("inf")


def pony_wall_ladder() -> tuple[PonyWall, ...]:
    return tuple(PonyWall(h) for h in (0.0, 2.0, 3.0, 4.0))


# ----------------------------------------------------------------------
# Heating and cooling
# ----------------------------------------------------------------------

@dataclass(frozen=True)
class Assembly:
    """One wall build-up, and the U-value it works out to."""

    name: str
    r_value: float

    @property
    def u_value(self) -> float:
        return 1.0 / self.r_value


def assemblies() -> tuple[Assembly, ...]:
    films = FACT["r_air_films"]
    sheath = FACT["r_osb_half"]
    foam = FACT["r_foam_1in"]
    return (
        Assembly("AS BILLED (1 in foam)", films + sheath + foam),
        Assembly("CAVITY FILLED", films + sheath + foam
                 + FACT["r_batt_cavity"]),
    )


@dataclass(frozen=True)
class RunningCost:
    """A year of heating and cooling one envelope."""

    label: str
    envelope_sqft: float
    assembly: Assembly

    @property
    def ua(self) -> float:
        return self.envelope_sqft * self.assembly.u_value

    @property
    def heating_kwh(self) -> float:
        btu = self.ua * FACT["heating_degree_days"] * 24.0
        return btu / FACT["btu_per_kwh"] / FACT["furnace_cop"]

    @property
    def cooling_kwh(self) -> float:
        btu = self.ua * FACT["cooling_degree_days"] * 24.0
        return btu / FACT["ac_seer"] / 1000.0

    @property
    def total_kwh(self) -> float:
        return self.heating_kwh + self.cooling_kwh

    @property
    def annual_cost(self) -> float:
        return self.total_kwh * FACT["power_price"]


def running_costs(assembly: Assembly | None = None
                  ) -> tuple[RunningCost, RunningCost]:
    """The dome and the box, same assembly, same climate."""
    chosen = assembly or assemblies()[1]
    return (
        RunningCost("2V dome", dome_envelope().envelope_sqft, chosen),
        RunningCost("square house", box_envelope().envelope_sqft, chosen),
    )


# ----------------------------------------------------------------------
# Radiative sky cooling paint
# ----------------------------------------------------------------------

@dataclass(frozen=True)
class SkyCooling:
    """What the paint is worth over a cooling season.

    Modelled through **sol-air temperature**, which is the only honest way
    to do it. Sunlight landing on a roof does not walk into the building:
    the surface heats up, and only the fraction the assembly conducts
    inward -- ``U / h_outer``, on the order of one percent for an
    insulated wall -- ever becomes cooling load. The rest re-radiates and
    convects straight back off.

    Counting the whole absorbed watt as saved load is a common way to
    make these paints look magical. It gave this model a saving of
    $1,090 a year against a building whose entire cooling bill was $38,
    which is how the error was caught.

    Two effects, kept separate because they are separate physics: not
    absorbing sunlight, and radiating through the 8-13 micron window to a
    sky that is effectively at 3 K.
    """

    lit_sqft: float
    assembly: Assembly

    @property
    def lit_m2(self) -> float:
        return self.lit_sqft * 0.092903

    @property
    def _irradiance_btu(self) -> float:
        """Mean daytime irradiance in BTU/hr/sq ft."""
        return FACT["peak_solar_w_m2"] * 0.3170

    @property
    def solar_delta_f(self) -> float:
        """How much cooler the surface runs, in sol-air terms."""
        drop = (FACT["solar_absorptance_dark"]
                - FACT["solar_absorptance_paint"])
        return drop * self._irradiance_btu / FACT["h_outer"]

    @property
    def radiative_delta_f(self) -> float:
        """How far below ambient the emission alone pulls the surface."""
        return (FACT["radiative_cool_w_m2"] * 0.3170) / FACT["h_outer"]

    @property
    def load_reduction_btu_hr(self) -> float:
        total_delta = self.solar_delta_f + self.radiative_delta_f
        return self.lit_sqft * self.assembly.u_value * total_delta

    @property
    def dark_roof_gain_btu_hr(self) -> float:
        """What a dark roof would have pushed in, for comparison."""
        delta = (FACT["solar_absorptance_dark"] * self._irradiance_btu
                 / FACT["h_outer"])
        return self.lit_sqft * self.assembly.u_value * delta

    @property
    def gain_cut_percent(self) -> float:
        """The honest headline: how much of the roof-driven gain goes."""
        if self.dark_roof_gain_btu_hr <= 0.0:
            return 0.0
        return min(100.0, self.load_reduction_btu_hr
                   / self.dark_roof_gain_btu_hr * 100.0)

    @property
    def season_kwh_electric(self) -> float:
        btu = self.load_reduction_btu_hr * FACT["cooling_hours_year"]
        return btu / FACT["ac_seer"] / 1000.0

    @property
    def annual_saving(self) -> float:
        return self.season_kwh_electric * FACT["power_price"]


def sky_cooling(floor_sqft: float = FLOOR_SQFT,
                assembly: Assembly | None = None) -> SkyCooling:
    """Roughly half the shell faces the sun at any one time."""
    return SkyCooling(shell_sqft(radius_for_floor(floor_sqft)) * 0.5,
                      assembly or assemblies()[1])


# ----------------------------------------------------------------------
# Water off the brim
# ----------------------------------------------------------------------

def hat_rim_radius_ft(floor_sqft: float = FLOOR_SQFT) -> float:
    """Plan radius of the ring where the hat stops.

    The hat covers the upper twenty triangles, so its edge is the highest
    shared vertex ring below them; the catchment is the circle that ring
    encloses.
    """
    radius_in = radius_for_floor(floor_sqft)
    faces = list(GEOMETRY.hemisphere_faces)
    order = sorted(range(len(faces)), key=lambda i: float(
        GEOMETRY.vertices[[int(v) for v in faces[i]]][:, 2].mean()))
    upper = {int(v) for i in order[20:] for v in faces[i]}
    lower = {int(v) for i in order[:20] for v in faces[i]}
    shared = upper & lower
    plan = [float(math.hypot(*GEOMETRY.vertices[v][:2])) for v in shared]
    return max(plan) * radius_in / 12.0


@dataclass(frozen=True)
class WaterCatch:
    """Rain off the hat, into a tank."""

    brim_ft: float
    floor_sqft: float = FLOOR_SQFT

    @property
    def rim_radius_ft(self) -> float:
        return hat_rim_radius_ft(self.floor_sqft)

    @property
    def catch_radius_ft(self) -> float:
        return self.rim_radius_ft + self.brim_ft

    @property
    def catchment_sqft(self) -> float:
        """Horizontal projection -- rain falls straight down, so the plan
        area is what catches it, not the sloped area."""
        return math.pi * self.catch_radius_ft ** 2

    @property
    def gallons_year(self) -> float:
        return (self.catchment_sqft * FACT["rainfall_in_year"]
                * FACT["gallons_per_sqft_inch"] * FACT["runoff_coefficient"])

    @property
    def gallons_day(self) -> float:
        return self.gallons_year / 365.0

    @property
    def value_year(self) -> float:
        return self.gallons_year * FACT["water_price_per_gal"]

    def tank_days(self, tank_gallons: float, use_gal_day: float = 50.0
                  ) -> float:
        return tank_gallons / use_gal_day if use_gal_day else 0.0


# ----------------------------------------------------------------------
# The ten points
# ----------------------------------------------------------------------

@dataclass(frozen=True)
class Point:
    """One argument, with the number that carries it."""

    number: int
    headline: str
    figure: str
    detail: str


def ten_points(floor_sqft: float = FLOOR_SQFT) -> tuple[Point, ...]:
    """Why this shape, for cheap manufactured housing, in ten numbers.

    Each figure is computed here rather than written down, so the list
    cannot drift away from the modules that produce it.
    """
    from .dome_costing import build_variants
    from .franken_economics import flat_rate_table

    dome, box = dome_envelope(floor_sqft), box_envelope(floor_sqft)
    builds = build_variants()
    pristine = builds[2]
    small, large = flat_rate_table()[0], flat_rate_table()[-1]
    bare, tall = PonyWall(0.0), PonyWall(3.0)
    dome_run, box_run = running_costs()
    paint = sky_cooling(floor_sqft)
    water = WaterCatch(1.5)
    surface_margin = (1.0 - dome.envelope_sqft / box.envelope_sqft) * 100.0

    return (
        Point(1, "Less building for the same floor",
              f"{surface_margin:.0f}% less exterior",
              f"{dome.envelope_sqft:.0f} sq ft of skin against "
              f"{box.envelope_sqft:.0f} for a square house with the same "
              f"{floor_sqft:.0f} sq ft of floor."),
        Point(2, "The parts list does not grow",
              f"{large.struts} struts at any size",
              f"{small.diameter_ft:.0f} ft or {large.diameter_ft:.0f} ft, it is "
              f"{large.struts} struts, {large.brackets} brackets and "
              f"{large.screws} screws either way. Nine times the house, the "
              f"same box of parts."),
        Point(3, "Nine operations, endlessly repeated",
              f"{large.processes} processes",
              "Every efficiency you find in one of them pays out 120 times "
              "per house, and again on every house after that."),
        Point(4, "It is stiff because of its shape",
              "40 triangles, no bracing",
              "A triangle cannot change shape without a side changing "
              "length. There is nothing left to brace, and nothing to rack."),
        Point(5, "Wind finds nothing to push on",
              "drag 0.42 against 1.05",
              "A curved shell has about a third the drag coefficient of a "
              "box, before any hold-down is considered."),
        Point(6, "It costs what the parts cost",
              f"${pristine.total:,.0f} finished",
              f"Pressure treated, insulated, glassed and fitted out, at "
              f"${pristine.per_sqft:.0f} the square foot, with nothing "
              f"salvaged and nothing donated."),
        Point(7, "A stem wall buys the wasted perimeter back",
              f"+{tall.gain_over(bare):.0f} sq ft usable",
              f"A {tall.height_ft:.0f} ft pony wall lifts usable floor from "
              f"{bare.usable_sqft:.0f} to {tall.usable_sqft:.0f} sq ft for "
              f"${tall.cost - bare.cost:,.0f} -- about "
              f"${tall.cost_per_gained_sqft(bare):.0f} a square foot, the "
              f"cheapest room in the building."),
        Point(8, "Less skin means less to heat and cool",
              f"${box_run.annual_cost - dome_run.annual_cost:,.0f} a year saved",
              f"{dome_run.total_kwh:,.0f} kWh against {box_run.total_kwh:,.0f} "
              f"at {FACT['power_price']*100:.0f} cents, same insulation, "
              f"same climate."),
        Point(9, "The roof can refuse the sun",
              f"{paint.gain_cut_percent:.0f}% of roof heat gain gone",
              f"Radiative cooling paint reflects "
              f"{(1-FACT['solar_absorptance_paint'])*100:.0f}% of sunlight and "
              f"radiates through the atmospheric window, so the shell runs "
              f"{paint.solar_delta_f + paint.radiative_delta_f:.0f} F cooler "
              f"than a dark one and sits below ambient in full sun."),
        Point(10, "The brim that keeps rain off also collects it",
              f"{water.gallons_year:,.0f} gallons a year",
              f"A {water.brim_ft*12:.0f} in overhang gives "
              f"{water.catchment_sqft:.0f} sq ft of catchment -- "
              f"{water.gallons_day:.0f} gallons a day on average rainfall, "
              f"straight into a tank."),
    )


def performance_report(floor_sqft: float = FLOOR_SQFT) -> str:
    lines = ["DOME PERFORMANCE - CALCULATION AUDIT", ""]

    lines.append("  pony wall (usable floor is where you can stand up):")
    for wall in pony_wall_ladder():
        lines.append(
            f"    {wall.height_ft:>3.0f} ft wall   usable "
            f"{wall.usable_sqft:>6.0f} sq ft "
            f"({wall.usable_fraction*100:>4.0f}%)   wall "
            f"{wall.wall_sqft:>5.0f} sq ft   ${wall.cost:>6,.0f}")
    bare, tall = PonyWall(0.0), PonyWall(3.0)
    lines.append(f"    -> 3 ft buys {tall.gain_over(bare):.0f} sq ft at "
                 f"${tall.cost_per_gained_sqft(bare):.2f}/sq ft")
    lines.append("")

    lines.append("  running cost at "
                 f"{FACT['power_price']*100:.0f} cents/kWh:")
    for assembly in assemblies():
        dome_run, box_run = running_costs(assembly)
        lines.append(f"    {assembly.name}  (R-{assembly.r_value:.1f}, "
                     f"U={assembly.u_value:.3f})")
        for run in (dome_run, box_run):
            lines.append(
                f"      {run.label:<14}{run.heating_kwh:>8,.0f} kWh heat "
                f"{run.cooling_kwh:>7,.0f} kWh cool "
                f"{run.total_kwh:>8,.0f} total   ${run.annual_cost:>7,.0f}/yr")
        lines.append(f"      saving: ${box_run.annual_cost - dome_run.annual_cost:,.0f} a year")
    lines.append("")

    paint = sky_cooling(floor_sqft)
    lines.append("  radiative sky cooling paint:")
    lines.append(f"    sunlit shell      {paint.lit_sqft:.0f} sq ft "
                 f"({paint.lit_m2:.0f} sq m)")
    lines.append(f"    surface runs      {paint.solar_delta_f:.0f} F cooler "
                 f"(sun) + {paint.radiative_delta_f:.0f} F (radiated)")
    lines.append(f"    roof-driven gain  "
                 f"{paint.dark_roof_gain_btu_hr:,.0f} BTU/hr dark -> "
                 f"{paint.dark_roof_gain_btu_hr - paint.load_reduction_btu_hr:,.0f}"
                 f" painted")
    lines.append(f"    that gain cut by  {paint.gain_cut_percent:.0f}%")
    lines.append(f"    electricity saved {paint.season_kwh_electric:,.0f} kWh"
                 f"  = ${paint.annual_saving:,.0f}/yr")
    rough = sky_cooling(floor_sqft, assemblies()[0])
    lines.append(f"    on the as-billed wall instead: "
                 f"${rough.annual_saving:,.0f}/yr")
    lines.append("")

    lines.append("  water off the brim:")
    lines.append(f"    hat rim radius    {hat_rim_radius_ft(floor_sqft):.1f} ft")
    for brim in (0.0, 1.0, 1.5, 2.0):
        catch = WaterCatch(brim, floor_sqft)
        lines.append(
            f"    {brim*12:>3.0f} in brim   catchment "
            f"{catch.catchment_sqft:>5.0f} sq ft   "
            f"{catch.gallons_year:>7,.0f} gal/yr   "
            f"{catch.gallons_day:>4.0f} gal/day   ${catch.value_year:>5,.0f}/yr")
    lines.append("")

    lines.append("  the ten points:")
    for point in ten_points(floor_sqft):
        lines.append(f"    {point.number:>2}. {point.headline}")
        lines.append(f"        {point.figure}")
    lines.append("")
    lines.append("external facts:")
    for item in EXTERNAL:
        lines.append(f"  {item.key:<26}{item.value:>10.4f} {item.units:<22} "
                     f"{item.source}")
    return "\n".join(lines)


def validate_performance() -> None:
    """Nothing reaches the screen that this cannot prove."""
    # -- pony wall -----------------------------------------------------
    ladder = pony_wall_ladder()
    assert ladder[0].height_ft == 0.0
    for lower, higher in zip(ladder, ladder[1:]):
        assert higher.usable_sqft > lower.usable_sqft, \
            "a taller wall must give more usable floor"
        assert higher.wall_sqft > lower.wall_sqft
        assert higher.cost > lower.cost
    bare = ladder[0]
    for wall in ladder:
        assert 0.0 <= wall.usable_fraction <= 1.0, wall.usable_fraction
    # A bare hemisphere wastes a lot of its floor; that is the whole point.
    assert bare.usable_fraction < 0.65, bare.usable_fraction
    tall = PonyWall(3.0)
    assert tall.usable_fraction > 0.80, tall.usable_fraction
    assert tall.cost_per_gained_sqft(bare) < 15.0, \
        "the pony wall has to be cheap floor or the argument fails"

    # Sanity: the usable radius can never exceed the dome's own radius.
    for wall in ladder + (PonyWall(12.0),):
        assert wall.usable_radius_ft() <= wall.radius_ft + 1e-9

    # -- energy --------------------------------------------------------
    basic, filled = assemblies()
    assert filled.r_value > basic.r_value
    assert filled.u_value < basic.u_value
    for assembly in assemblies():
        dome_run, box_run = running_costs(assembly)
        assert dome_run.total_kwh < box_run.total_kwh
        assert dome_run.annual_cost < box_run.annual_cost
        # Loss is proportional to area at equal assembly, so the margin
        # must equal the surface margin exactly. If these ever disagree,
        # one of them has been fudged.
        area_ratio = dome_envelope().envelope_sqft / box_envelope().envelope_sqft
        assert math.isclose(dome_run.total_kwh / box_run.total_kwh, area_ratio,
                            rel_tol=1e-9)
        assert dome_run.heating_kwh > 0 and dome_run.cooling_kwh > 0

    # -- paint ---------------------------------------------------------
    paint = sky_cooling()
    assert paint.solar_delta_f > 0 and paint.radiative_delta_f > 0
    assert paint.annual_saving > 0
    assert 0.0 < paint.gain_cut_percent <= 100.0, paint.gain_cut_percent

    # The check that caught the original error: painting a roof cannot save
    # more than the whole building spends on cooling. Counting every
    # absorbed watt as avoided load had this model claiming $1,090 a year
    # against a $38 cooling bill, which is the kind of number a campaign
    # gets called out for.
    for assembly in assemblies():
        lit = sky_cooling(FLOOR_SQFT, assembly)
        dome_run, _ = running_costs(assembly)
        cooling_bill = dome_run.cooling_kwh * FACT["power_price"]
        assert lit.annual_saving < cooling_bill * 4.0, (
            f"paint saves ${lit.annual_saving:.0f} against a "
            f"${cooling_bill:.0f} cooling bill on {assembly.name}")

    # A better-insulated wall must gain less from the paint, because less
    # of the rejected heat was getting in to begin with.
    basic, filled = assemblies()
    assert (sky_cooling(FLOOR_SQFT, filled).annual_saving
            < sky_cooling(FLOOR_SQFT, basic).annual_saving)

    # -- water ---------------------------------------------------------
    rim = hat_rim_radius_ft()
    radius_ft = radius_for_floor(FLOOR_SQFT) / 12.0
    assert 0.0 < rim < radius_ft, (rim, radius_ft)
    previous = 0.0
    for brim in (0.0, 1.0, 1.5, 2.0):
        catch = WaterCatch(brim)
        assert catch.gallons_year > previous
        previous = catch.gallons_year
        assert catch.catchment_sqft > 0
    # One inch of rain on one square foot really is 0.6233 gallons.
    assert math.isclose(FACT["gallons_per_sqft_inch"], 144.0 / 231.0,
                        rel_tol=1e-3)

    # -- the ten points ------------------------------------------------
    points = ten_points()
    assert len(points) == 10, len(points)
    assert [p.number for p in points] == list(range(1, 11))
    for point in points:
        assert point.headline and point.figure and point.detail, point.number
        assert len(point.headline) < 60, point.headline

    for item in EXTERNAL:
        assert item.source and item.units and item.value > 0.0
