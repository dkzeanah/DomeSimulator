"""Every derivation the master presentation's math screens put on film.

The master lesson is the one video that walks through the whole project,
so this module is deliberately a *bridge*: it computes nothing new of its
own.  Every step list below is formatted from the same modules the
interactive tools run on -- ``geometry``, ``build_geometry``,
``hubless_geometry``, ``dome_advantage``, ``dome_costing``,
``dome_performance``, ``franken_economics``, ``energetics`` -- so a
figure cannot appear on a math screen without existing in the code that
the simulators themselves trust.

A *step list* is a tuple of strings.  The math overlay reveals them one
at a time as the chapter plays, and renders the **last line as the
conclusion band**, so every list here ends with the sentence the viewer
should leave with.

Derived versus borrowed: everything geometric, every count, every length
and every dollar total is derived.  The borrowed constants (drag
coefficients, climate, prices, published paint performance, the two
measured boards) are all declared in the source modules' own EXTERNAL
tables and repeated in :func:`master_report`.
"""

from __future__ import annotations

import math
from functools import lru_cache

from .build_geometry import error_budget, stock_plan, strut_details
from .dome_advantage import (
    FACT as ADV_FACT,
    advantages,
    box_envelope,
    dome_envelope,
)
from .dome_costing import FLOOR_SQFT, Startup, build_variants, radius_for_floor
from .dome_performance import (
    FACT as PERF_FACT,
    PonyWall,
    WaterCatch,
    assemblies,
    running_costs,
    sky_cooling,
)
from .franken_economics import flat_rate_table
from .geometry import PHI, build_demo_geometry, fit_measurements
from .hubless_geometry import (
    compound_setups,
    franken_hardware,
    hubless_summary,
)


# The two boards this project was originally asked about.  They are
# measurements of physical wood, so they are external by definition.
MEASURED_LONG_IN = 72.0
MEASURED_SHORT_IN = 63.5

EXTERNAL_CONSTANTS: tuple[tuple[str, float, str, str], ...] = (
    ("measured_long_in", MEASURED_LONG_IN, "in",
     "The long member of the audited dome, measured with a tape."),
    ("measured_short_in", MEASURED_SHORT_IN, "in",
     "The short member of the audited dome, measured with a tape."),
)


GEOMETRY = build_demo_geometry()
SUMMARY = hubless_summary()
FIT = fit_measurements(MEASURED_LONG_IN, MEASURED_SHORT_IN)

# The starter home every price and performance figure describes: the
# radius that gives a 314 sq ft circle of floor, same as the costing
# and kickstarter modules use.
HOME_RADIUS_IN = radius_for_floor(FLOOR_SQFT)


def _conclude(steps: list[str], conclusion: str) -> tuple[str, ...]:
    steps.append(conclusion)
    return tuple(steps)


# ----------------------------------------------------------------------
# Screen 1 -- everything on screen is counted, not claimed
# ----------------------------------------------------------------------

@lru_cache(maxsize=1)
def steps_counted() -> tuple[str, ...]:
    short = next(c for c in GEOMETRY.edge_classes if c.name == "SHORT")
    long = next(c for c in GEOMETRY.edge_classes if c.name == "LONG")
    struts = short.hemisphere_count + long.hemisphere_count
    panels = len(GEOMETRY.hemisphere_faces)
    hubs = len({int(v) for face in GEOMETRY.hemisphere_faces for v in face})
    steps = [
        "count the model, live, right now:",
        f"triangular panels          = {panels}",
        f"SHORT edges                = {short.hemisphere_count}",
        f"LONG edges                 = {long.hemisphere_count}",
        f"edges total = {short.hemisphere_count} + {long.hemisphere_count} "
        f"= {struts}",
        f"hubs (shared corners)      = {hubs}",
        "none of these were typed in -- they are counted",
        "off the same 3D model being drawn behind this panel",
    ]
    return _conclude(
        steps,
        f"{panels} panels, {struts} edges, {hubs} corners -- and every "
        "number in this film is made the same way")


# ----------------------------------------------------------------------
# Screen 2 -- the box comparison, derived
# ----------------------------------------------------------------------

@lru_cache(maxsize=1)
def steps_envelope() -> tuple[str, ...]:
    dome = dome_envelope()
    box = box_envelope()
    surface = advantages()[0]
    wind = advantages()[3]
    side = math.sqrt(box.footprint_sqft)
    steps = [
        f"same floor, both shapes: {box.footprint_sqft:.0f} sq ft",
        f"box: side = sqrt({box.footprint_sqft:.0f}) = {side:.1f} ft, "
        f"walls {ADV_FACT['wall_height_ft']:.0f} ft, "
        f"{ADV_FACT['gable_pitch']:.2f} pitch roof",
        f"box skin  = walls + roof + gables = {box.envelope_sqft:,.0f} sq ft",
        f"dome skin = 40 flat triangles     = {dome.envelope_sqft:,.0f} sq ft",
        f"difference = {box.envelope_sqft - dome.envelope_sqft:,.0f} sq ft "
        f"= {surface.percent_better:.0f}% less to build, seal, paint, heat",
        f"volume enclosed: dome {dome.volume_cuft:,.0f} cu ft "
        f"vs box {box.volume_cuft:,.0f} cu ft",
        f"wind drag (published): dome Cd {wind.dome:.2f} vs box "
        f"Cd {wind.other:.2f} = {wind.percent_better:.0f}% less load",
    ]
    return _conclude(
        steps,
        f"the dome buys the same floor with {surface.percent_better:.0f}% "
        "less outside -- and pays for that once, then every winter")


# ----------------------------------------------------------------------
# Screen 3 -- the two strut lengths, from phi to the tape measure
# ----------------------------------------------------------------------

@lru_cache(maxsize=1)
def steps_chords() -> tuple[str, ...]:
    raw_radius = math.sqrt(1.0 + PHI * PHI)
    # The midpoint radius is measured off the model rather than quoted
    # from a closed form, so the screen shows what the geometry contains.
    flat = GEOMETRY.flat_midpoints
    measured_mid = float(sum(
        math.sqrt(float(p[0]) ** 2 + float(p[1]) ** 2 + float(p[2]) ** 2)
        for p in flat) / len(flat))
    steps = [
        f"phi = (1 + sqrt 5) / 2 = {PHI:.6f}",
        f"12 corners at (0, +-1, +-phi): radius = sqrt(1 + phi^2) "
        f"= {raw_radius:.6f}",
        "divide by that radius -> icosahedron on a unit sphere",
        f"halve every edge: midpoints sit at {measured_mid:.6f}, "
        "inside the sphere",
        "push each midpoint back out to radius 1",
        f"measure every edge again -> only two lengths remain:",
        f"SHORT = {GEOMETRY.short_factor:.6f} x R    "
        f"LONG = {GEOMETRY.long_factor:.6f} x R",
        f"the audited boards: {MEASURED_LONG_IN:.0f} in / "
        f"{MEASURED_SHORT_IN:.1f} in -> best-fit "
        f"R = {FIT.best_fit_radius:.1f} in",
    ]
    return _conclude(
        steps,
        "two lengths of wood, thirty of one and thirty-five of the "
        "other, are the entire frame")


# ----------------------------------------------------------------------
# Screen 4 -- radius to cut list to lumber order
# ----------------------------------------------------------------------

@lru_cache(maxsize=1)
def steps_cutlist() -> tuple[str, ...]:
    short, long = strut_details()
    radius = FIT.best_fit_radius
    # The same worked example the construction lesson uses: 8 ft stock
    # and a 3/4 in connector deduction, both stated on screen.
    stock_in, deduction_in = 96.0, 0.75
    plan = stock_plan(radius, stock_in, deduction_in)
    steps = [
        f"pick the audited dome: R = {radius:.1f} in",
        f"SHORT = {GEOMETRY.short_factor:.6f} x R = "
        f"{GEOMETRY.short_factor * radius:.2f} in, "
        f"cut {short.dome_count} times",
        f"LONG  = {GEOMETRY.long_factor:.6f} x R = "
        f"{GEOMETRY.long_factor * radius:.2f} in, "
        f"cut {long.dome_count} times",
        f"hub-centre minus a measured {deduction_in:.2f} in connector "
        "deduction = the saw setting",
    ]
    for run in plan:
        steps.append(
            f"{run.strut_class}: {run.pieces_needed} pieces from "
            f"{run.sticks} sticks of {stock_in / 12:.0f} ft stock, "
            f"{run.offcut_per_stick:.1f} in offcut each")
    return _conclude(
        steps,
        "one radius scales the whole cut list; the lumber order "
        "falls straight out of it")


# ----------------------------------------------------------------------
# Screen 5 -- the hubless count: 120 sticks, no hubs anywhere
# ----------------------------------------------------------------------

@lru_cache(maxsize=1)
def steps_hubless() -> tuple[str, ...]:
    steps = [
        f"hubless: every triangle brings its own three boards",
        f"{SUMMARY.triangles} triangles x 3 = "
        f"{SUMMARY.triangles * 3} struts",
        f"interior seams: {SUMMARY.doubled_edges} -- each carries "
        "two boards, one from each neighbour",
        f"rim seams: {SUMMARY.rim_edges} -- each carries one",
        f"check: {SUMMARY.doubled_edges} x 2 + {SUMMARY.rim_edges} = "
        f"{SUMMARY.strut_check} = the strut count",
        f"hubs required = 0",
    ]
    return _conclude(
        steps,
        f"{SUMMARY.struts} sticks bolt to each other -- there is no "
        "hub to buy, weld, or wait for")


# ----------------------------------------------------------------------
# Screen 6 -- the jig and saw settings, measured off the model
# ----------------------------------------------------------------------

@lru_cache(maxsize=1)
def steps_jigs() -> tuple[str, ...]:
    equilateral = next(t for t in GEOMETRY.triangle_classes
                       if len(set(t.side_names)) == 1)
    isosceles = next(t for t in GEOMETRY.triangle_classes
                     if len(set(t.side_names)) > 1)
    setups = compound_setups()
    past = [s for s in setups if not s.within_saw_range]
    steps = [
        f"only two triangle shapes exist in the whole dome:",
        f"equilateral x{equilateral.hemisphere_count}: corners "
        + " / ".join(f"{a:.1f} deg" for a in equilateral.angles_deg),
        f"isosceles   x{isosceles.hemisphere_count}: corners "
        + " / ".join(f"{a:.1f} deg" for a in isosceles.angles_deg),
        "mitre (saw swing) = 90 - corner/2;  bevel (blade tilt)",
        "= (180 - fold to the neighbour)/2",
    ]
    for setup in setups:
        steps.append(
            f"setup: mitre {setup.mitre_deg:.2f} deg, bevel "
            f"{setup.bevel_deg:.2f} deg -- {setup.count} strut ends")
    if past:
        steps.append(
            f"{sum(s.count for s in past)} ends sit past a 50 deg saw: "
            f"swing to the complement ({past[0].complement_deg:.2f} deg) "
            "and quarter-turn the stick")
    return _conclude(
        steps,
        f"two jigs and {len(setups)} saw setups cut all "
        f"{SUMMARY.struts} struts -- that is the entire machine shop")


# ----------------------------------------------------------------------
# Screen 7 -- what an eighth of an inch does
# ----------------------------------------------------------------------

@lru_cache(maxsize=1)
def steps_error() -> tuple[str, ...]:
    budget = error_budget(0.125)
    steps = [
        f"the base ring is a regular {budget.base_sides}-sided polygon",
        f"circumradius = side / (2 sin(180/{budget.base_sides})) "
        f"= side / {2.0 * math.sin(math.pi / budget.base_sides):.6f}",
        f"so radius error = strut error x {budget.amplification:.6f}",
        f"that multiplier is exactly phi = {PHI:.6f}",
        f"an error of {budget.strut_error:.3f} in per base strut moves "
        f"the radius {budget.radius_error:.3f} in",
        f"the diameter {budget.diameter_error:.3f} in, and the apex "
        f"{budget.apex_error:.3f} in",
    ]
    return _conclude(
        steps,
        "the ring multiplies every strut error by the golden ratio -- "
        "which is why you check each ring before building the next")


# ----------------------------------------------------------------------
# Screen 8 -- the frankendome, counted and audited
# ----------------------------------------------------------------------

@lru_cache(maxsize=1)
def steps_franken() -> tuple[str, ...]:
    hardware = franken_hardware()
    steps = [
        f"{hardware.triangles} triangles x "
        f"{hardware.brackets_per_triangle} folded brackets = "
        f"{hardware.brackets} brackets",
        f"{hardware.brackets} brackets x "
        f"{hardware.screws_per_bracket} screws = {hardware.screws} screws",
        f"{hardware.unique_edges} seams x {hardware.bolts_per_edge} bolts "
        f"= {hardware.bolts} bolts, {hardware.washers} washers",
        f"built in {hardware.build_days} days = "
        f"{hardware.triangles_per_day:.0f} triangles and "
        f"{hardware.screws_per_day:.0f} screws a day",
        f"standing {hardware.stood_months} months = "
        f"{hardware.service_ratio:.0f}x its own build time",
        "no milled lumber, no bought hubs, no machine shop --",
        "the geometry carried whatever the chainsaw made",
    ]
    return _conclude(
        steps,
        f"ten days of work has stood {hardware.service_ratio:.0f} times "
        "longer than it took to build -- that is what the shape forgives")


# ----------------------------------------------------------------------
# Screen 9 -- the price ladder, receipts attached
# ----------------------------------------------------------------------

@lru_cache(maxsize=1)
def steps_price() -> tuple[str, ...]:
    builds = build_variants()
    steps = [
        f"one dome, {FLOOR_SQFT:.0f} sq ft of floor "
        f"({builds[0].diameter_ft:.0f} ft across), priced four ways,",
        "every part bought new at the till:",
    ]
    for build in builds:
        steps.append(
            f"{build.name}: ${build.total:,.0f}  "
            f"(${build.per_sqft:.0f}/sq ft)")
    cheapest, dearest = builds[0], builds[-1]
    return _conclude(
        steps,
        f"${cheapest.total:,.0f} to ${dearest.total:,.0f} for a finished "
        "shell -- the cheapest is under the price of a used car")


# ----------------------------------------------------------------------
# Screen 10 -- a year of heating and cooling, both shapes
# ----------------------------------------------------------------------

@lru_cache(maxsize=1)
def steps_energy() -> tuple[str, ...]:
    dome_run, box_run = running_costs()
    assembly = assemblies()[1]
    steps = [
        f"wall build-up: R-{assembly.r_value:.1f} "
        f"-> U = 1/R = {assembly.u_value:.4f}",
        f"heat loss rate = skin x U:",
        f"dome: {dome_run.envelope_sqft:,.0f} sq ft x "
        f"{assembly.u_value:.4f} = {dome_run.ua:,.0f} BTU/hr/F",
        f"box:  {box_run.envelope_sqft:,.0f} sq ft x "
        f"{assembly.u_value:.4f} = {box_run.ua:,.0f} BTU/hr/F",
        f"x {PERF_FACT['heating_degree_days']:.0f} heating degree days "
        f"and {PERF_FACT['cooling_degree_days']:.0f} cooling",
        f"dome: {dome_run.total_kwh:,.0f} kWh/yr = "
        f"${dome_run.annual_cost:,.0f} at "
        f"{PERF_FACT['power_price'] * 100:.0f} cents",
        f"box:  {box_run.total_kwh:,.0f} kWh/yr = "
        f"${box_run.annual_cost:,.0f}",
    ]
    saving = box_run.annual_cost - dome_run.annual_cost
    return _conclude(
        steps,
        f"${saving:,.0f} a year, every year, from the shape alone -- "
        "same insulation, same climate, same floor")


# ----------------------------------------------------------------------
# Screen 11 -- the brim as a water plant
# ----------------------------------------------------------------------

@lru_cache(maxsize=1)
def steps_water() -> tuple[str, ...]:
    water = WaterCatch(1.5)
    steps = [
        f"hat rim radius = {water.rim_radius_ft:.1f} ft; add an "
        f"{water.brim_ft * 12:.0f} in brim -> {water.catch_radius_ft:.1f} ft",
        f"catchment = pi x {water.catch_radius_ft:.1f}^2 = "
        f"{water.catchment_sqft:,.0f} sq ft of plan area",
        f"x {PERF_FACT['rainfall_in_year']:.0f} in of rain a year "
        f"x {PERF_FACT['gallons_per_sqft_inch']:.4f} gal per sq ft inch",
        f"x {PERF_FACT['runoff_coefficient']:.2f} runoff",
        f"= {water.gallons_year:,.0f} gallons a year, "
        f"{water.gallons_day:.0f} a day, into a tank by the door",
        "no pump, one downpipe -- the roof shape does the collecting",
    ]
    return _conclude(
        steps,
        f"{water.gallons_year:,.0f} gallons a year from a brim the "
        "rain was already running off")


# ----------------------------------------------------------------------
# Screen 12 -- dome labour is a flat rate
# ----------------------------------------------------------------------

@lru_cache(maxsize=1)
def steps_flatrate() -> tuple[str, ...]:
    table = flat_rate_table()
    small, large = table[0], table[-1]
    steps = [
        "scale the dome up and count what changes:",
        f"{small.diameter_ft:.0f} ft dome: "
        f"{small.floor_area_sqft:,.0f} sq ft of floor",
        f"{large.diameter_ft:.0f} ft dome: "
        f"{large.floor_area_sqft:,.0f} sq ft -- "
        f"{large.floor_area_sqft / small.floor_area_sqft:.1f}x the house",
        f"struts either way: {large.struts}",
        f"brackets either way: {large.brackets}",
        f"screws either way: {large.screws}",
        "floor area grows with radius squared;",
        "the parts list does not grow at all",
    ]
    return _conclude(
        steps,
        f"{large.floor_area_sqft / small.floor_area_sqft:.1f}x the house "
        "for the same list of operations -- that is what makes it a product")


# ----------------------------------------------------------------------
# Screen 13 -- what a build costs the people who build it
# ----------------------------------------------------------------------

@lru_cache(maxsize=1)
def steps_labour() -> tuple[str, ...]:
    from .energetics import build_energy

    energy = build_energy(serial=1, crew=2)
    by_motion: dict[str, float] = {}
    for element in energy.elements:
        for name, kcal in element.by_motion().items():
            by_motion[name] = by_motion.get(name, 0.0) + kcal
    fasten = by_motion.get("fasten", 0.0)
    steps = [
        f"simulate every part placement, all six motions, crew of "
        f"{energy.crew}:",
        f"time on task = {energy.hours_per_worker:.0f} hours each "
        f"= {energy.shifts:.1f} eight-hour shifts",
        f"food energy = {energy.kcal_per_worker:,.0f} kcal per worker",
        f"mechanical work actually raising things = "
        f"{energy.mechanical_kcal:,.0f} kcal "
        f"({energy.mechanical_fraction * 100:.2f}% of the fuel)",
        f"fastening alone = {fasten:,.0f} kcal "
        f"({fasten / energy.kcal_per_worker * 100:.0f}% of the fuel) -- "
        "and it lifts nothing",
        "so a factory should not chase the lifting;",
        "it should chase the screw gun",
    ]
    return _conclude(
        steps,
        f"lifting is {energy.mechanical_fraction * 100:.1f}% of the "
        "effort; fastening is where the shift actually goes")


# ----------------------------------------------------------------------
# The audit report and the proof
# ----------------------------------------------------------------------

ALL_SCREENS: tuple[tuple[str, object], ...] = (
    ("counted", steps_counted),
    ("envelope", steps_envelope),
    ("chords", steps_chords),
    ("cutlist", steps_cutlist),
    ("hubless", steps_hubless),
    ("jigs", steps_jigs),
    ("error", steps_error),
    ("franken", steps_franken),
    ("price", steps_price),
    ("energy", steps_energy),
    ("water", steps_water),
    ("flatrate", steps_flatrate),
    ("labour", steps_labour),
)


def master_report() -> str:
    """The audit: every math screen, line by line, plus provenance."""
    lines = [
        "THE MASTER PRESENTATION -- MATH SCREEN AUDIT",
        "",
        "Every line below is what the corresponding math screen shows,",
        "generated by the same call the renderer makes.  Figures marked",
        "external in the source modules are borrowed and sourced there;",
        "everything else is derived from the geometry.",
        "",
    ]
    for name, builder in ALL_SCREENS:
        lines.append(f"== {name.upper()} ==")
        lines.extend(f"  {line}" for line in builder())
        lines.append("")
    lines.append("External constants declared by this module:")
    for key, value, units, source in EXTERNAL_CONSTANTS:
        lines.append(f"  {key} = {value} {units}  ({source})")
    return "\n".join(lines)


def validate_master_facts() -> None:
    """Prove the bridge: the screens agree with the modules they cite."""
    # Every screen builds, every line is non-empty, every screen ends in
    # a conclusion that is a sentence rather than a fragment of algebra.
    for name, builder in ALL_SCREENS:
        steps = builder()
        assert len(steps) >= 4, (name, len(steps))
        assert all(line.strip() for line in steps), name
        assert len(steps[-1]) >= 30, (name, steps[-1])

    # The counted screen must agree with the geometry it claims to count.
    short = next(c for c in GEOMETRY.edge_classes if c.name == "SHORT")
    long = next(c for c in GEOMETRY.edge_classes if c.name == "LONG")
    assert short.hemisphere_count == 30 and long.hemisphere_count == 35
    assert len(GEOMETRY.hemisphere_faces) == 40
    assert f"{short.hemisphere_count}" in "".join(steps_counted())

    # The hubless check must actually balance.
    assert SUMMARY.strut_check == SUMMARY.struts == SUMMARY.triangles * 3

    # The error screen's multiplier really is phi.
    assert math.isclose(error_budget(0.125).amplification, PHI,
                        rel_tol=1e-9)

    # The energy screen's saving is the difference of the two runs it
    # displays, and the box genuinely costs more.
    dome_run, box_run = running_costs()
    assert box_run.annual_cost > dome_run.annual_cost

    # The price ladder is sorted the way the narration claims.
    builds = build_variants()
    assert builds[0].total < builds[-1].total

    # The flat-rate screen: parts identical, floor not.
    table = flat_rate_table()
    assert table[0].struts == table[-1].struts
    assert table[0].floor_area_sqft < table[-1].floor_area_sqft

    # The chord screen's factors match the geometry to full precision.
    assert f"{GEOMETRY.short_factor:.6f}" in "".join(steps_chords())
    assert f"{GEOMETRY.long_factor:.6f}" in "".join(steps_chords())
