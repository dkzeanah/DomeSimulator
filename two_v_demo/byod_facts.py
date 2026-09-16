"""Inputs and computed worksheets for the September 2026 BYOD revision.

This cut removes the spoken assumptions lecture, not the audit trail. Prices
remain scenarios. The $10k pad and $5k starter are the author's targets.
"""
from __future__ import annotations

import math
from functools import lru_cache

import park_model as pm
from .park_facts import HOME, home_pad, loaded_pad, usd

EXTERNAL_CONSTANTS = (
    ("pad_target", 10000.0, "USD", "Author's all-in serviced-pad target, not a quote"),
    ("starter_target", 5000.0, "USD", "Author's basic dome target; services supplied by site"),
    ("rent_low", 500.0, "USD/month", "Author's proposed low rent scenario"),
    ("rent_middle", 1000.0, "USD/month", "Midpoint of the author's rent range"),
    ("rent_high", 1500.0, "USD/month", "Author's proposed high rent scenario"),
    ("upgrade_steps", 2.0, "steps", "Author's hardware design brief; requires load qualification"),
    ("life_target", 10.0, "years", "Author's infrastructure service-life goal; not a warranty"),
)


def declared(name):
    return next(value for key, value, _unit, _source in EXTERNAL_CONSTANTS if key == name)


def starter_diameter():
    return math.ceil(pm.DOME_CLASSES[0].diameter_ft / pm.PAD_STEP_FT) * pm.PAD_STEP_FT


@lru_cache(maxsize=1)
def starter_pad_rows():
    # Use the starter footprint, not the old 40 ft default. Include the
    # trunk/site allowance that cheap_pad_rows does not account for.
    diameter = starter_diameter()
    return pm.cheap_pad_rows(diameter) + (
        ("site access + trunk service allowance", pm.declared("site_infrastructure_usd_per_pad")),
    )


def starter_pad_cost():
    return sum(value for _label, value in starter_pad_rows())


def steps_starter():
    diameter = starter_diameter()
    return (
        "STARTER SCENARIO / declared unit prices",
        f"{diameter:.0f} ft pad = {pm.pad_area_sqft(diameter):,.0f} sq ft",
        *(f"{label}: {usd(value)}" for label, value in starter_pad_rows()),
        f"TOTAL: {usd(starter_pad_cost())}",
        f"Author's all-in target: {usd(declared('pad_target'))}",
        "Fixed rim; shared services; no iris or rotation.",
        "Site allowance must cover the actual local works.",
        "Start with a working floor and services; add features later.",
    )


def steps_deluxe():
    pad = loaded_pad()
    iris = pm.iris_cost(pad.diameter_ft)
    return (
        "DELUXE SCENARIO / declared unit prices",
        f"Same model's {pad.diameter_ft:.0f} ft concrete pad:",
        *(f"{label}: {usd(value)}" for label, value in pad.cost_rows()),
        f"Add adjustable iris: {usd(iris)}",
        f"TOTAL WITH IRIS: {usd(pad.build_cost + iris)}",
        "A larger pad with rotation, column and solar.",
        "Optional future build; outside the first-site campaign scope.",
    )


def payback_rows():
    occupancy = pm.declared("occupancy_fraction")
    costs = home_pad().yearly_costs
    capital = declared("pad_target")
    rows = []
    for name in ("rent_low", "rent_middle", "rent_high"):
        rent = declared(name)
        net = rent * 12 * occupancy - costs
        rows.append((rent, net, capital / net * 12))
    return tuple(rows)


def steps_target():
    return (
        f"WHAT IF the complete pad costs {usd(declared('pad_target'))}?",
        "Power, water and drain included in that TARGET.",
        f"Leased {pm.declared('occupancy_fraction') * 100:.0f}% of the year",
        f"Management + tax + insurance: {usd(home_pad().yearly_costs)}/year",
        "Utility resale profit assumed zero here.",
        *(f"{usd(rent)}/mo -> {usd(net)}/yr net -> {months:.1f} months"
          for rent, net, months in payback_rows()),
        "Before financing, income tax and additional maintenance.",
        "One-year payback is a scenario, not a promise.",
    )


def steps_layers():
    ladder = pm.shell_ladder(HOME)
    return (
        "REMOVABLE SHELL / upgrade the insulation over time",
        f"Model assumption: +R-{pm.declared('quilt_r_per_layer'):.1f} per quilted layer",
        *(f"{step.layers} added layers -> R-{step.r_value:.1f}" for step in ladder),
        "Actual assemblies need tested moisture and fire performance.",
        "The outer shell supplies the weather and wind barrier.",
        "Insulation improves when you add suitable layers; age alone adds none.",
    )


def steps_solar():
    layouts = pm.solar_layouts()
    return (
        f"SAME DOME: {pm.SOLAR_RADIUS_FT * 2:.0f} ft across",
        "Panel areas are measured from the model's faces.",
        f"Assumed panel density: {pm.declared('panel_watts_per_sqft'):.1f} W/sq ft",
        *(f"{row.name}: {row.area_sqft:,.0f} sq ft -> {row.watts / 1000:.1f} kW"
          for row in layouts),
        "No panels = zero installed solar capacity.",
        f"Selected layouts: {min(x.watts for x in layouts) / 1000:.1f}"
        f" to {max(x.watts for x in layouts) / 1000:.1f} kW nameplate.",
        "Face area sets capacity, not guaranteed energy yield.",
        "Sun angle, shade, climate and losses set actual kWh.",
        "The useful limit is the available shell area.",
    )


def steps_growth():
    return (
        "HARDWARE DESIGN BRIEF / size for two upgrades",
        *(f"{row.longest_member_ft:.0f} ft longest member -> ~{row.floor_sqft:,.0f} sq ft"
          for row in pm.DOME_CLASSES),
        "These are the author's target sizes, not a load rating.",
        "Keep qualified connectors; collect longer replacement members.",
        "Larger frames also need more skin, insulation and pad area.",
        "Beyond the rated span, change hardware or frequency.",
        "One purchase should support a planned range of future homes.",
    )


def report():
    rows = ["BRING YOUR OWN DOME / revision audit", "", "Author's targets:"]
    rows.extend(f"{k}: {v:g} {u} -- {s}" for k, v, u, s in EXTERNAL_CONSTANTS)
    rows += ["", "Existing model inputs:"]
    rows.extend(f"{k}: {v:g} {u} -- {s}" for k, v, u, s in pm.EXTERNAL_CONSTANTS)
    for fn in (steps_starter, steps_deluxe, steps_target, steps_growth, steps_layers, steps_solar):
        rows.extend(("", *fn()))
    return "\n".join(rows) + "\n"


def validate():
    assert math.isclose(starter_pad_cost(), sum(x[1] for x in starter_pad_rows()))
    assert any("trunk" in label for label, _ in starter_pad_rows())
    assert starter_pad_cost() < loaded_pad().build_cost + pm.iris_cost(loaded_pad().diameter_ft)
    paybacks = [months for _, _, months in payback_rows()]
    assert paybacks[0] > paybacks[1] > paybacks[2] > 0
    assert paybacks[0] > 12 > paybacks[-1]
    layouts = pm.solar_layouts()
    assert max(row.watts for row in layouts) > min(row.watts for row in layouts) > 0
    for row in layouts:
        assert math.isclose(row.watts, row.area_sqft * pm.declared("panel_watts_per_sqft"))
    ladder = pm.shell_ladder(HOME)
    assert all(b.r_value > a.r_value for a, b in zip(ladder, ladder[1:]))
