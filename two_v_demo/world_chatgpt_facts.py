"""Production economics for ten Dome Creator builds in the ChatGPT cut.

The geometry, quantities, and bill-of-materials costs come from the shipped
Dome Creator presets through :mod:`two_v_demo.world_facts`.  Labor comes from
the construction-event ledger emitted by :func:`mesh_builder.build_dome_mesh`,
the same event stream the walkable Creator uses for its construction playback.

The modeled consumer price is deliberately labelled as a model, not a quote.
It adds the Assembly Line's burdened wage and activity-based overhead to the
Creator bill of materials, then applies the gross-margin percentage computed
by the closest existing Assembly Line product family.  No independent market
price is asserted.
"""

from __future__ import annotations

from dataclasses import dataclass
from functools import lru_cache

import al_build as assembly
from mesh_builder import build_dome_mesh

from .world_facts import DomeType, by_name, dome_geometry


SELECTED_NAMES: tuple[str, ...] = (
    "Timber Workshop",
    "Glass Studio Loft",
    "Split-Log Homestead",
    "Whole Trunk Lodge - 20 ft",
    "Grow Dome",
    "Hex Cell Pavilion",
    "Continuous Steel Arc Hangar",
    "Rebar Garden Dome",
    "Concrete Monocoque Form",
    "Treehouse Canopy Dome",
)


# This is a categorical bridge, not a claimed market fact.  It chooses the
# closest product line already priced by assembly_line/al_build so that the
# retail-margin rule comes from existing code rather than a new percentage.
ASSEMBLY_FAMILY_BY_NAME: dict[str, str] = {
    "Timber Workshop": "shed",
    "Glass Studio Loft": "home",
    "Split-Log Homestead": "home",
    "Whole Trunk Lodge - 20 ft": "home",
    "Grow Dome": "greenhouse",
    "Hex Cell Pavilion": "shed",
    "Continuous Steel Arc Hangar": "shed",
    "Rebar Garden Dome": "greenhouse",
    "Concrete Monocoque Form": "shelter",
    "Treehouse Canopy Dome": "home",
}


EXTERNAL_CONSTANTS: tuple[tuple[str, float, str, str], ...] = (
    (
        "burdened_wage_per_hour",
        assembly.ASSUMPTIONS["burdened_wage_per_hour"],
        "USD per labor-hour",
        "al_build.ASSUMPTIONS; the Assembly Line's declared loaded wage.",
    ),
    (
        "overhead_per_labor_hour",
        assembly.ASSUMPTIONS["overhead_per_labor_hour"],
        "USD per labor-hour",
        "al_build.ASSUMPTIONS; activity-based factory overhead.",
    ),
)


@dataclass(frozen=True)
class ProductionEconomics:
    """One Creator preset carried through the assembly-line cost model."""

    name: str
    family: str
    frame_material: float
    enclosure_material: float
    foundation_material: float
    fitout_material: float
    material_total: float
    site_hours: float
    frame_hours: float
    enclosure_hours: float
    systems_hours: float
    labor_hours: float
    labor_cost: float
    overhead: float
    factory_cost: float
    family_margin_fraction: float
    consumer_price: float

    @property
    def material_breakdown(self) -> tuple[tuple[str, float], ...]:
        return (
            ("frame + connectors", self.frame_material),
            ("panels + shell", self.enclosure_material),
            ("foundation", self.foundation_material),
            ("fit-out + systems", self.fitout_material),
        )

    @property
    def labor_breakdown(self) -> tuple[tuple[str, float], ...]:
        return (
            ("site + floor", self.site_hours),
            ("frame", self.frame_hours),
            ("enclosure", self.enclosure_hours),
            ("systems + finish", self.systems_hours),
        )


def selected_domes() -> tuple[DomeType, ...]:
    catalogue = by_name()
    return tuple(catalogue[name] for name in SELECTED_NAMES)


def _labor_bucket(label: str) -> str:
    text = label.lower()
    if text.startswith("site prep") or text.startswith("floor layout"):
        return "site"
    if (
        text.startswith("install strut")
        or text.startswith("fasten hub")
        or text.startswith("frame the entrance")
        or text.startswith("raise ")
        or text.startswith("through-bolt")
    ):
        return "frame"
    if text.startswith("fit ") or text.startswith("apply "):
        return "enclosure"
    return "systems"


@lru_cache(maxsize=4)
def family_margin_fraction(family: str) -> float:
    """Gross margin already produced by a representative line product."""
    representative = {
        "home": assembly.DomeSpec(
            dtype="home", radius=4.0, frequency=3, layout="1-Bedroom"
        ),
        "shed": assembly.DomeSpec(
            dtype="shed", radius=3.5, frequency=3, layout="Studio"
        ),
        "greenhouse": assembly.DomeSpec(
            dtype="greenhouse", radius=3.8, frequency=3, layout="Studio"
        ),
        "shelter": assembly.DomeSpec(
            dtype="shelter", radius=2.0, frequency=2, layout="Studio"
        ),
    }[family]
    catalog, _ = assembly.build_dome_catalog(representative)
    economics = assembly.unit_economics(catalog, representative)
    return economics["margin_pct"] / 100.0


@lru_cache(maxsize=16)
def production_economics(name: str) -> ProductionEconomics:
    dome = by_name()[name]
    stats = dome.stats

    frame_material = float(stats["frame_cost"] + stats["hub_cost"])
    enclosure_material = float(stats["panel_cost"] + stats["layer_cost"])
    foundation_material = float(stats["foundation_cost"])
    fitout_material = float(
        stats["prop_cost"]
        + stats["wall_cost"]
        + stats["wire_cost"]
        + stats["plumbing_cost"]
    )
    material_total = (
        frame_material
        + enclosure_material
        + foundation_material
        + fitout_material
    )

    events: list[dict] = []
    build_dome_mesh(dome_geometry(dome), events, include_console=False)
    hours = {"site": 0.0, "frame": 0.0, "enclosure": 0.0, "systems": 0.0}
    for event in events:
        hours[_labor_bucket(str(event["label"]))] += float(event["hours"])
    labor_hours = sum(hours.values())

    wage = assembly.ASSUMPTIONS["burdened_wage_per_hour"]
    overhead_rate = assembly.ASSUMPTIONS["overhead_per_labor_hour"]
    labor_cost = labor_hours * wage
    overhead = labor_hours * overhead_rate
    factory_cost = material_total + labor_cost + overhead

    family = ASSEMBLY_FAMILY_BY_NAME[name]
    margin_fraction = family_margin_fraction(family)
    consumer_price = factory_cost / (1.0 - margin_fraction)

    return ProductionEconomics(
        name=name,
        family=family,
        frame_material=frame_material,
        enclosure_material=enclosure_material,
        foundation_material=foundation_material,
        fitout_material=fitout_material,
        material_total=material_total,
        site_hours=hours["site"],
        frame_hours=hours["frame"],
        enclosure_hours=hours["enclosure"],
        systems_hours=hours["systems"],
        labor_hours=labor_hours,
        labor_cost=labor_cost,
        overhead=overhead,
        factory_cost=factory_cost,
        family_margin_fraction=margin_fraction,
        consumer_price=consumer_price,
    )


def production_rows() -> tuple[ProductionEconomics, ...]:
    return tuple(production_economics(name) for name in SELECTED_NAMES)


@lru_cache(maxsize=1)
def steps_production() -> tuple[str, ...]:
    rows = production_rows()
    lines = [
        "Creator BOM  +  Creator build events  +  Assembly Line economics:",
    ]
    for row in rows:
        lines.append(
            f"{row.name[:25]:<25}  BOM ${row.material_total:>8,.0f}  "
            f"{row.labor_hours:>5.0f} h  direct-sale ${row.consumer_price:>9,.0f}"
        )
    cheapest = min(rows, key=lambda item: item.consumer_price)
    fastest = min(rows, key=lambda item: item.labor_hours)
    lines.extend(
        [
            f"lowest modeled direct-sale price: {cheapest.name} at "
            f"${cheapest.consumer_price:,.0f}",
            f"least labor: {fastest.name} at {fastest.labor_hours:.0f} hours",
            "these are code-model outputs, not bids: site, permits, freight, "
            "tax and local engineering are outside the model",
        ]
    )
    return tuple(lines)


def world_chatgpt_report() -> str:
    count = len(SELECTED_NAMES)
    lines = [
        f"{count} DOME BUILDS -- CREATOR / FORGE / ASSEMBLY LINE MASTER CUT",
        "",
        "The material column is the Dome Creator BOM. Labor is the sum of",
        "the Creator's own construction events. Direct-sale price adds the",
        "Assembly Line wage and overhead, then preserves the modeled gross",
        "margin of the closest existing Assembly Line product family.",
        "It is a planning model, not a contractor quote.",
        "",
        "EXTERNAL INPUTS",
    ]
    for name, value, unit, source in EXTERNAL_CONSTANTS:
        lines.append(f"  {name}: {value:g} {unit} -- {source}")
    lines.append("")
    for dome, row in zip(selected_domes(), production_rows()):
        lines.extend(
            [
                f"== {dome.name} ==",
                f"  geometry       {dome.frequency}V, {dome.floor_sqft:,.0f} "
                f"sq ft, {dome.struts} struts, {dome.panels} panels",
                f"  assembly map   {row.family} family, "
                f"{row.family_margin_fraction * 100:.1f}% modeled margin",
                f"  materials      frame ${row.frame_material:,.0f}; "
                f"shell ${row.enclosure_material:,.0f}; foundation "
                f"${row.foundation_material:,.0f}; fit-out "
                f"${row.fitout_material:,.0f}; total "
                f"${row.material_total:,.0f}",
                f"  labor          site {row.site_hours:.1f} h; frame "
                f"{row.frame_hours:.1f} h; enclosure "
                f"{row.enclosure_hours:.1f} h; systems/finish "
                f"{row.systems_hours:.1f} h; total {row.labor_hours:.1f} h",
                f"  conversion     labor ${row.labor_cost:,.0f}; overhead "
                f"${row.overhead:,.0f}; factory cost "
                f"${row.factory_cost:,.0f}",
                f"  consumer model ${row.consumer_price:,.0f}",
                "",
            ]
        )
    lines.append("PRODUCTION SCREEN")
    lines.extend(f"  {line}" for line in steps_production())
    return "\n".join(lines)


def validate_world_chatgpt_facts() -> None:
    domes = selected_domes()
    rows = production_rows()
    assert len(domes) == 10
    assert len({dome.name for dome in domes}) == 10
    assert len(rows) == len(domes)
    assert set(ASSEMBLY_FAMILY_BY_NAME) == set(SELECTED_NAMES)

    for dome, row in zip(domes, rows):
        assert dome.name == row.name
        assert abs(row.material_total - dome.total_cost) < 0.01, dome.name
        assert abs(sum(value for _name, value in row.material_breakdown)
                   - row.material_total) < 0.01, dome.name
        assert abs(sum(value for _name, value in row.labor_breakdown)
                   - row.labor_hours) < 1e-9, dome.name
        assert row.labor_hours > 0.0, dome.name
        assert row.factory_cost > row.material_total, dome.name
        assert row.consumer_price > row.factory_cost, dome.name
        assert 0.10 < row.family_margin_fraction < 0.60, dome.name

    steps = steps_production()
    assert len(steps) == len(rows) + 4
    assert all(line.strip() for line in steps)
