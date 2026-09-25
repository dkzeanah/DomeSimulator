"""The seam module, the column, the pad and the bench -- all of it, priced.

The dome in this book has {{dome.seam_ft}} feet of seam channel running
through its structure, and Chapter on connections argues that the channel
exists whether or not anybody uses it: it is the space two sawn faces leave.

This module is what happens when you decide to use it for everything at once.

WHAT THE SEAM MODULE IS

A fitted liner running the length of a seam, carrying four things:

* **a rain intake slot** along the outer ridge, and a gutter under it with
  suction points, so the seam is the building's guttering rather than
  something bolted to it;
* **a vent plenum** with perforations that wash air along the wood faces, so
  the timber is being dried by the same channel that carries the water;
* **a three-way gate** that routes the air either along the faces, or through
  a desiccant cartridge, or isolates the water path from the air path;
* **a removable silica cartridge**, and -- the part that makes this more than
  plumbing -- **thermoelectric condensing plates** on the cold side of the
  channel, so moisture in the air is dropped as liquid into the same gutter
  the rain uses.

THE AIR BARRIER

The fan is sized to hold the interior slightly above outside pressure, so the
net flow at every seam is *outward*. A gap in an inward-leaking building
admits weather; the same gap in an outward-flowing one does not, because the
air is going the wrong way for water to ride in on.

That is a real strategy and it is not free: it runs continuously, it costs a
fan and its power, and it only works while the fan runs.

WHAT THIS MODULE WILL NOT DO

It will not pretend the thermoelectric plates are a water supply. They are
dehumidifiers that happen to yield liquid, they are poor per watt against a
compressor, and :func:`water_comparison` prints the number that says so: one
inch of rain on this roof is worth more than the plates make in a year.

Prices are declared here with a reason on each, and the whole of it is an
*upgrade* on the standard article rather than a change to it -- the dome's
own price in :mod:`seed_model` is untouched by anything in this file.
"""

from __future__ import annotations

import math
from dataclasses import dataclass

GAL_PER_CUFT = 7.480519480519481
LITRES_PER_GAL = 3.785411784


# ----------------------------------------------------------------------
# Declared inputs
# ----------------------------------------------------------------------

EXTERNAL_CONSTANTS: tuple[tuple[str, float, str, str], ...] = (
    # -- the seam module ---------------------------------------------
    ("seam_cap_usd_per_ft", 3.40, "USD/ft",
     "assumption: the extruded outer cap with the rain intake slot, in "
     "anodised aluminium, bought by the foot"),
    ("seam_liner_usd_per_ft", 2.60, "USD/ft",
     "assumption: the perforated vented liner that sits inside the cap and "
     "washes air along the two wood faces"),
    ("seam_gutter_usd_per_ft", 2.10, "USD/ft",
     "assumption: the water channel under the intake slot, with its suction "
     "inlets punched at intervals"),
    ("seam_module_segments", 1.0, "segments per seam",
     "how many service segments one seam is divided into, which sets how "
     "many gates and cartridges there are. One. A seam on this dome is "
     "about five and a half feet long, so dividing it further puts a gate "
     "every seventeen inches -- which priced the module above the dome it "
     "is fitted to"),
    ("seam_gate_usd", 46.0, "USD each",
     "assumption: one three-way actuated gate -- two damper flaps and a "
     "small linear actuator -- that routes air along the faces, through the "
     "desiccant, or isolates the water path"),
    ("silica_cartridge_usd", 22.0, "USD each",
     "assumption: one removable silica gel drawer, refillable, sized to a "
     "seam segment"),
    ("seam_service_cover_usd", 9.0, "USD each",
     "assumption: the access panel over each segment, which is what makes "
     "the cartridge a consumable rather than a rebuild"),
    ("seam_drain_usd_per_ft", 1.15, "USD/ft",
     "assumption: the drain line from the gutter down to the tank"),

    # -- moving the air ----------------------------------------------
    ("ram_fan_usd", 185.0, "USD each",
     "assumption: one EC in-line fan with a speed controller, rated for "
     "continuous duty, which is what a pressure barrier requires"),
    ("ram_fans", 2.0, "fans",
     "the owner's stated arrangement: one drawing and one pushing, so the "
     "direction of the barrier can be reversed"),
    ("barrier_pressure_pa", 4.0, "Pa",
     "assumption: how far above outside the interior is held. A few pascals "
     "is enough to reverse flow at a small gap and is below what anybody "
     "feels on a door"),
    ("air_changes_per_hour", 0.55, "1/h",
     "assumption: the ventilation rate the fan is sized for, which is a "
     "dwelling rate rather than a workshop one"),

    # -- condensing ---------------------------------------------------
    ("peltier_module_usd", 14.0, "USD each",
     "assumption: one thermoelectric module with its cold plate, hot-side "
     "heatsink and thermal paste"),
    ("peltier_modules", 6.0, "modules",
     "the owner's stated arrangement: modules at the seams that see the most "
     "moisture, rather than one big unit in a cupboard"),
    ("peltier_watts_each", 60.0, "W",
     "assumption: what one module draws at the voltage it is run at, which "
     "is below its rating because efficiency collapses at full drive"),
    ("peltier_litres_per_kwh", 0.35, "L/kWh",
     "assumption: what a thermoelectric condenser actually yields in humid "
     "air. A compressor dehumidifier does three to four times this, and "
     "that difference is the honest case against the idea"),
    ("peltier_run_hours", 6.0, "hours/day",
     "assumption: run on daylight surplus rather than on the battery, "
     "because this is the one load that can wait"),

    # -- the water bench ----------------------------------------------
    ("water_filter_usd", 210.0, "USD",
     "assumption: a three-stage cartridge filter -- sediment, carbon and a "
     "0.5 micron block -- on the rise from the tank"),
    ("water_uv_usd", 165.0, "USD",
     "assumption: an inline UV lamp, which is what makes roof water "
     "drinkable rather than merely clear"),
    ("water_meter_usd", 78.0, "USD",
     "assumption: a pulse-output meter on the incoming rise, so consumption "
     "is a number rather than an impression"),
    ("water_pump_usd", 145.0, "USD",
     "assumption: a 12 V on-demand pump with an accumulator, sized for two "
     "fixtures"),
    ("first_flush_usd", 68.0, "USD",
     "assumption: the diverter that throws away the first gallons off a dry "
     "roof, which is the difference between roof water and drinking water"),

    # -- metering and control ------------------------------------------
    ("energy_meter_usd", 62.0, "USD",
     "assumption: a DIN-rail DC energy meter with a shunt, reading the "
     "array, the bank and the load separately"),
    ("charge_controller_usd", 195.0, "USD",
     "assumption: an MPPT controller sized above the array, because an "
     "undersized controller clips the best hour of the day"),

    # -- hardware -------------------------------------------------------
    ("bolt_usd_each", 0.92, "USD each",
     "assumption: one A2 stainless cup-head bolt, nut and two washers, at "
     "the size the wedge faces take"),
    ("bolts_per_seam", 8.0, "bolts",
     "the design's edge-to-edge fixing: four pairs along each seam, into "
     "the threaded inserts rather than into end grain"),
    ("insert_usd_each", 0.74, "USD each",
     "assumption: one threaded insert set into a sawn wedge face"),
    ("v_bracket_usd_each", 5.80, "USD each",
     "assumption: one flat V bracket, folded from 3 mm stainless on a bench "
     "brake, four holes per flap"),
    ("v_bracket_flap_fraction", 0.5, "fraction of member length",
     "the owner's stated rule: each flap may run out to half the member's "
     "length, so the screws are spread along the stick rather than "
     "clustered at its end"),
    # -- the clock ----------------------------------------------------
    ("split_wedges_per_session", 30.0, "wedges",
     "the owner's own measured rate: what one four-hour session at the log "
     "with a meagre chainsaw actually produces"),
    ("split_session_hours", 4.0, "hours",
     "the length of that session, measured rather than planned"),
    ("minutes_per_member_erected", 15.0, "minutes",
     "the owner's own figure for one member all the way through: split, "
     "cut, drilled, joined and standing in the shell. It averages the fast "
     "work and the slow work rather than timing one operation"),
    ("error_redundancy_fraction", 0.25, "fraction",
     "what is added for getting it wrong. Not contingency on price -- time, "
     "for the stick that splits off the radius, the panel that goes down in "
     "the wrong order, and the hour spent looking for the drill"),
    ("working_week_hours", 40.0, "hours",
     "the week this book is named after, which is a target rather than a "
     "result"),
)

CONSTANTS: dict[str, float] = {name: value
                               for name, value, _u, _w in EXTERNAL_CONSTANTS}


def declared(name: str) -> float:
    if name in CONSTANTS:
        return CONSTANTS[name]
    import seed_model

    return seed_model.declared(name)


# ----------------------------------------------------------------------
# One line of a bill
# ----------------------------------------------------------------------

@dataclass(frozen=True)
class Line:
    label: str
    quantity: float
    unit: str
    unit_cost: float
    source: str

    @property
    def cost(self) -> float:
        return self.quantity * self.unit_cost


@dataclass(frozen=True)
class Bill:
    key: str
    label: str
    why: str
    lines: tuple[Line, ...]

    @property
    def cost(self) -> float:
        return sum(line.cost for line in self.lines)

    def table(self) -> str:
        width = max(len(line.label) for line in self.lines) + 2
        out = []
        for line in self.lines:
            out.append(
                f"  {line.label:<{width}}"
                f"{line.quantity:>9,.1f} {line.unit:<12}"
                f"{'$' + format(line.unit_cost, ',.2f'):>11}"
                f"{'$' + format(line.cost, ',.0f'):>10}")
        out.append(f"  {'':<{width}}{'':>9} {'':<12}{'':>11}"
                   f"{'-' * 9:>10}")
        out.append(f"  {self.label:<{width}}{'':>9} {'':<12}{'':>11}"
                   f"{'$' + format(self.cost, ',.0f'):>10}")
        return "\n".join(out)


def _geometry():
    import seed_world

    return seed_world.geometry()


# ----------------------------------------------------------------------
# The seam module
# ----------------------------------------------------------------------

def seam_module() -> Bill:
    """The liner, the gutter, the gates, the cartridges and the plates."""
    geometry = _geometry()
    feet = geometry.seam_length_in / 12.0
    seams = float(geometry.seam_count)
    segments = seams * declared("seam_module_segments")

    return Bill("seam", "Seam module, whole dome",
                "the channel two sawn faces leave, fitted out as gutter, "
                "vent and dehumidifier at once",
                (
        Line("outer cap with intake slot", feet, "ft",
             declared("seam_cap_usd_per_ft"), "seam_cap_usd_per_ft"),
        Line("vented liner, perforated", feet, "ft",
             declared("seam_liner_usd_per_ft"), "seam_liner_usd_per_ft"),
        Line("water gutter with suction inlets", feet, "ft",
             declared("seam_gutter_usd_per_ft"), "seam_gutter_usd_per_ft"),
        Line("drain line to the tank", feet, "ft",
             declared("seam_drain_usd_per_ft"), "seam_drain_usd_per_ft"),
        Line("three-way gate, one per segment", segments, "each",
             declared("seam_gate_usd"), "seam_gate_usd"),
        Line("silica cartridge drawer", segments, "each",
             declared("silica_cartridge_usd"), "silica_cartridge_usd"),
        Line("service cover", segments, "each",
             declared("seam_service_cover_usd"), "seam_service_cover_usd"),
        Line("thermoelectric condensing plate", declared("peltier_modules"),
             "each", declared("peltier_module_usd"), "peltier_module_usd"),
        Line("ram fan, continuous duty", declared("ram_fans"), "each",
             declared("ram_fan_usd"), "ram_fan_usd"),
    ))


def column_bill() -> Bill:
    """Everything in the utility column, including the steel."""
    import seed_model

    geometry = _geometry()
    rise = seed_model.mast_rise_ft(seed_model.seed_geometry())
    spokes = float(geometry.base_sides)

    return Bill("column", "Utility column, complete",
                "the one object that touches the ground, the wall and the "
                "sky -- with the steel that makes the floor and the lift",
                (
        Line("column housing, insulated chase", rise, "ft",
             declared("mast_wood_clad_usd_per_ft"),
             "mast_wood_clad_usd_per_ft"),
        Line("steel core, service port to apex", rise, "ft",
             declared("mast_steel_core_usd_per_ft"),
             "mast_steel_core_usd_per_ft"),
        Line("base flange onto the service port", 1.0, "each",
             declared("mast_base_flange_usd"), "mast_base_flange_usd"),
        Line("apex sleeve and gasketed seal cap", 1.0, "each",
             declared("mast_apex_ring_usd"), "mast_apex_ring_usd"),
        Line("apex lifting ring", 1.0, "each",
             declared("lift_ring_usd"), "lift_ring_usd"),
        Line("floor hub that clamps the mast", 1.0, "each",
             declared("floor_hub_usd"), "floor_hub_usd"),
        Line("radial steel floor spokes", spokes, "each",
             declared("floor_spokes_usd_each"), "floor_spokes_usd_each"),
        Line("sub-panel, breakers and outlets", 1.0, "each",
             declared("column_electrical_usd")
             if "column_electrical_usd" in CONSTANTS else 310.0,
             "seed_model column group"),
        Line("water manifold and rise", 1.0, "each", 240.0,
             "seed_model column group"),
        Line("drain stack and floor-port tie", 1.0, "each", 165.0,
             "seed_model column group"),
    ))


def power_bill() -> Bill:
    """Array, controller, bank, metering."""
    watts = declared("solar_panel_watts")
    kwh = declared("battery_kwh")
    return Bill("power", "Power bench",
                "what makes the dome work off a pad's pedestal or off "
                "nothing at all",
                (
        Line("solar array", watts, "W",
             declared("solar_usd_per_watt_diy"), "solar_usd_per_watt_diy"),
        Line("MPPT charge controller", 1.0, "each",
             declared("charge_controller_usd"), "charge_controller_usd"),
        Line("battery bank, LiFePO4", kwh, "kWh",
             declared("battery_usd_per_kwh"), "battery_usd_per_kwh"),
        Line("DC energy meter and shunt", 1.0, "each",
             declared("energy_meter_usd"), "energy_meter_usd"),
    ))


def water_bill() -> Bill:
    """Tank, filtration, sterilisation, pump and metering."""
    gallons = declared("water_tank_gal")
    feet = _geometry().seam_length_in / 12.0
    return Bill("water", "Water bench",
                f"what turns {feet:,.0f} feet of seam gutter into something "
                "you can drink",
                (
        Line("under-floor tank", gallons, "gal",
             declared("water_tank_usd_per_gal"), "water_tank_usd_per_gal"),
        Line("first-flush diverter", 1.0, "each",
             declared("first_flush_usd"), "first_flush_usd"),
        Line("three-stage filter", 1.0, "each",
             declared("water_filter_usd"), "water_filter_usd"),
        Line("inline UV lamp", 1.0, "each",
             declared("water_uv_usd"), "water_uv_usd"),
        Line("on-demand pump and accumulator", 1.0, "each",
             declared("water_pump_usd"), "water_pump_usd"),
        Line("pulse-output water meter", 1.0, "each",
             declared("water_meter_usd"), "water_meter_usd"),
    ))


def hardware_bill() -> Bill:
    """Stainless, edge to edge, plus the V brackets."""
    geometry = _geometry()
    seams = float(geometry.seam_count)
    bolts = seams * declared("bolts_per_seam")
    inserts = bolts * 2.0
    return Bill("hardware", "Joining hardware, stainless",
                "edge to edge, into inserts rather than into end grain",
                (
        Line("A2 stainless bolt, nut, two washers", bolts, "sets",
             declared("bolt_usd_each"), "bolt_usd_each"),
        Line("threaded insert in a sawn face", inserts, "each",
             declared("insert_usd_each"), "insert_usd_each"),
        Line("flat V bracket, four holes a flap",
             float(geometry.member_count), "each",
             declared("v_bracket_usd_each"), "v_bracket_usd_each"),
    ))


def pad_bill() -> Bill:
    """The platform's own materials, taken off rather than rated."""
    import pad_deck
    import seed_model

    deck = pad_deck.deck(seed_model.declared_deck())
    return Bill("pad", f"Pad materials ({deck.label.lower()})",
                "the host's bill, counted board by board",
                tuple(Line(line.label, line.quantity, line.unit,
                           line.unit_cost, line.source)
                      for line in deck.lines))


def bills() -> tuple[Bill, ...]:
    return (seam_module(), column_bill(), power_bill(), water_bill(),
            hardware_bill(), pad_bill())


# ----------------------------------------------------------------------
# Does any of it work?
# ----------------------------------------------------------------------

def air_barrier() -> dict:
    """What the fan has to move to keep the seams flowing outward."""
    geometry = _geometry()
    radius_ft = geometry.radius_in / 12.0
    volume_cuft = (2.0 / 3.0) * math.pi * radius_ft ** 3
    ach = declared("air_changes_per_hour")
    cfm = volume_cuft * ach / 60.0
    feet = geometry.seam_length_in / 12.0
    return {
        "volume_cuft": volume_cuft,
        "ach": ach,
        "cfm": cfm,
        "pressure_pa": declared("barrier_pressure_pa"),
        "seam_ft": feet,
        "cfm_per_seam_ft": cfm / feet,
        "fans": declared("ram_fans"),
    }


def water_comparison() -> dict:
    """Rain against thermoelectric condensing, on this roof."""
    geometry = _geometry()
    roof_sqft = geometry.panel_sqft
    # An inch of rain on the roof's plan area. The shell is faceted, so its
    # own area over-counts what the sky actually delivers; the honest figure
    # is the circle the dome stands in.
    plan_sqft = geometry.floor_circle_sqft
    gallons_per_inch = plan_sqft / 12.0 * GAL_PER_CUFT

    modules = declared("peltier_modules")
    watts = modules * declared("peltier_watts_each")
    hours = declared("peltier_run_hours")
    kwh_per_day = watts * hours / 1000.0
    litres_per_day = kwh_per_day * declared("peltier_litres_per_kwh")
    gallons_per_day = litres_per_day / LITRES_PER_GAL

    return {
        "roof_sqft": roof_sqft,
        "plan_sqft": plan_sqft,
        "gallons_per_inch": gallons_per_inch,
        "peltier_watts": watts,
        "peltier_kwh_per_day": kwh_per_day,
        "peltier_litres_per_day": litres_per_day,
        "peltier_gallons_per_day": gallons_per_day,
        "peltier_gallons_per_year": gallons_per_day * 365.0,
        "rain_inches_equal_to_a_year": (gallons_per_day * 365.0
                                        / gallons_per_inch),
        "kwh_per_litre": (kwh_per_day / litres_per_day
                          if litres_per_day else float("inf")),
    }


def v_bracket() -> dict:
    """The connector, sized from the member it joins."""
    geometry = _geometry()
    member = next(m for m in geometry.members if m.edge_type == "A")
    flap = member.stock_length_in * declared("v_bracket_flap_fraction")
    return {
        "flap_in": flap,
        "holes_per_flap": 4,
        "holes_total": 8,
        "spacing_in": flap / 4.0,
        "member_in": member.stock_length_in,
        "count": geometry.member_count,
        "usd_each": declared("v_bracket_usd_each"),
    }


def build_clock() -> dict:
    """The forty-hour week this book is named after, worked out.

    Every figure here is the owner's own measured rate rather than an
    estimate from a process model: what a session at the log produces, and
    what one member costs from tree to standing. The arithmetic is the only
    part this module does.
    """
    geometry = _geometry()
    members = float(geometry.member_count)

    per_session = declared("split_wedges_per_session")
    session = declared("split_session_hours")
    split_hours = members / per_session * session

    minutes = declared("minutes_per_member_erected")
    straight_hours = members * minutes / 60.0

    redundancy = declared("error_redundancy_fraction")
    with_error = straight_hours * (1.0 + redundancy)
    week = declared("working_week_hours")

    return {
        "members": members,
        "wedges_per_session": per_session,
        "session_hours": session,
        "split_hours": split_hours,
        "minutes_per_member": minutes,
        "straight_hours": straight_hours,
        "redundancy": redundancy,
        "with_error": with_error,
        "week": week,
        "spare": week - with_error,
        "split_share": split_hours / straight_hours,
    }


def total() -> float:
    return sum(bill.cost for bill in bills())


def report() -> str:
    out = ["EVERY SYSTEM, PRICED", ""]
    for bill in bills():
        out.append(bill.label.upper())
        out.append(f"  {bill.why}")
        out.append("")
        out.append(bill.table())
        out.append("")
    out.append(f"  {'ALL SYSTEMS':<40}"
               f"{'$' + format(total(), ',.0f'):>12}")
    out += ["", "THE AIR BARRIER", ""]
    air = air_barrier()
    out.append(f"  interior volume       {air['volume_cuft']:>9,.0f} cu ft")
    out.append(f"  at {air['ach']:.2f} air changes an hour"
               f"  {air['cfm']:>6,.0f} cu ft a minute")
    out.append(f"  held above outside by {air['pressure_pa']:>9,.1f} Pa")
    out.append(f"  spread over           {air['seam_ft']:>9,.0f} ft of seam")
    out += ["", "WATER: RAIN AGAINST CONDENSING", ""]
    water = water_comparison()
    out.append(f"  one inch of rain      "
               f"{water['gallons_per_inch']:>9,.0f} gal")
    out.append(f"  the plates, a day     "
               f"{water['peltier_gallons_per_day']:>9,.2f} gal "
               f"({water['peltier_watts']:.0f} W)")
    out.append(f"  the plates, a year    "
               f"{water['peltier_gallons_per_year']:>9,.0f} gal")
    out.append(f"  which is the same as  "
               f"{water['rain_inches_equal_to_a_year']:>9,.1f} inches of rain")
    out.append(f"  energy per litre      "
               f"{water['kwh_per_litre']:>9,.2f} kWh")
    return "\n".join(out)


def validate_systems() -> None:
    """Every line is real, and the honest comparison is still honest."""
    for name, value, unit, why in EXTERNAL_CONSTANTS:
        assert value > 0.0, name
        assert unit, name
        assert len(why) > 40, f"{name} has no reason attached"

    every = bills()
    assert len(every) == 6, len(every)
    keys = [bill.key for bill in every]
    assert len(set(keys)) == len(keys), keys

    for bill in every:
        assert bill.lines, bill.key
        assert bill.why, bill.key
        # A stray format placeholder printed itself on the page once.
        assert "{" not in bill.why and "}" not in bill.why, (
            f"{bill.key}: an unfilled placeholder in the description")
        assert bill.cost > 0.0, bill.key
        for line in bill.lines:
            assert line.quantity > 0.0, (bill.key, line.label)
            assert line.unit_cost > 0.0, (bill.key, line.label)
            assert line.source, (bill.key, line.label)
        rendered = bill.table()
        assert bill.label in rendered

    # The seam module is a whole-dome number and it is not small. The
    # ceiling is the dome's own price: a fit-out that costs more than the
    # building is a different proposition and would need saying so on the
    # page rather than passing quietly.
    import seed_model

    seam = next(b for b in every if b.key == "seam")
    dome = seed_model.quote().price
    assert 2000.0 < seam.cost < dome, (
        f"the seam module is ${seam.cost:,.0f} against a dome at "
        f"${dome:,.0f}; at that ratio the chapter has to argue for it "
        "rather than offer it")

    air = air_barrier()
    assert air["cfm"] > 5.0, air
    # A barrier that needs a gale is not a barrier anybody will run.
    assert air["pressure_pa"] < 25.0, air

    water = water_comparison()
    # The claim this module refuses to make. If condensing ever beat rain on
    # this roof the chapter would have to be rewritten rather than quietly
    # keep its conclusion.
    assert water["gallons_per_inch"] > water["peltier_gallons_per_year"], (
        f"the plates now make {water['peltier_gallons_per_year']:,.0f} gal a "
        f"year against {water['gallons_per_inch']:,.0f} for an inch of rain; "
        "the chapter's conclusion no longer follows from the model")
    assert water["kwh_per_litre"] > 1.0, (
        "thermoelectric condensing has become cheap per litre; check the "
        "assumption before printing it")

    clock = build_clock()
    assert clock["members"] == 120, clock
    # The arithmetic the title rests on. If any of the three measured rates
    # moves far enough that the week stops being a week, the book is called
    # the wrong thing and this should say so rather than round quietly.
    assert abs(clock["split_hours"] - 16.0) < 0.5, clock["split_hours"]
    assert abs(clock["straight_hours"] - 30.0) < 0.5, clock
    assert clock["with_error"] <= clock["week"], (
        f"the build comes to {clock['with_error']:,.1f} hours against a "
        f"{clock['week']:,.0f} hour week; the title no longer holds")
    assert clock["with_error"] > clock["week"] * 0.8, (
        "the build now fits the week with room to spare, which means the "
        "redundancy is doing nothing and should be re-measured")
    assert 0.4 < clock["split_share"] < 0.7, clock["split_share"]

    bracket = v_bracket()
    assert bracket["holes_per_flap"] == 4, bracket
    assert bracket["flap_in"] > 10.0, bracket
    assert bracket["flap_in"] <= bracket["member_in"] * 0.5 + 1e-9, bracket
    assert bracket["count"] == 120, bracket

    rendered = report()
    assert "ALL SYSTEMS" in rendered
    assert "RAIN AGAINST CONDENSING" in rendered


def main(argv: list[str] | None = None) -> int:
    import argparse

    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--check", action="store_true")
    args = parser.parse_args(argv)

    validate_systems()
    if args.check:
        print("systems ok")
        return 0
    print(report())
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
