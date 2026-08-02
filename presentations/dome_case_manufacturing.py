"""Argument 1 of 10: the standardized-product / manufacturing case.

Built around chatgpt's own framing from ``presentation.txt`` — the
strongest defensible case for a 2V dome is not "a house shaped like a
dome," it's a standardized manufactured product: minimal geometry,
factory repetition, rapid assembly, low operating demand, resilience
engineering, and standardized financing. Every number is pulled from
``presentations._numbers`` — the same modules the interactive tools use.
"""

from __future__ import annotations

import al_build as ab
from presenter.script import OverlayPanel, Presentation, Scene, Shot
from presentations._numbers import (
    BENCH_DAYS_PCT, BENCH_LABOR_PCT, BENCH_PRICE_PCT, GEO, HERO_BENCH,
    HERO_BREAK_EVEN, HERO_LABOR_HOURS, HERO_MONTHLY, HERO_PRICE,
    HERO_THROUGHPUT, HERO_VALUE, HUB_COUNT, LONG, R, SHORT, TRI_EQU,
    TRI_ISO,
)

FIELD = "a calm open field in daylight"


def build() -> Presentation:
    scenes = (
        Scene(
            "hook", "Not a custom house shaped like a dome",
            FIELD,
            world=(("dome", {"radius": R, "skin_alpha": 0.14}),),
            shots=(
                Shot("thesis", 9.0, lens="wide", focus="dome",
                     yaw=-50, pitch=16, orbit=10,
                     caption="The strongest case for a 2V dome is not "
                             "architecture — it's manufacturing",
                     panel=OverlayPanel(
                         title="THE CORE DISTINCTION",
                         bullets=("A custom house shaped like a dome is "
                                  "a hard sell, one at a time",
                                  "A standardized product, built the same "
                                  "way every time, is a different pitch "
                                  "entirely",
                                  "This project's simulator treats it as "
                                  "the second one"),
                         position="right"),
                     narration=(
                         "Set aside the aesthetics for a moment. The "
                         "strongest version of this pitch is not "
                         "architectural — it's industrial. A custom "
                         "house that happens to be shaped like a dome is "
                         "a hard, expensive sell, one at a time, from "
                         "scratch.",
                         "A standardized product, engineered once and "
                         "built the same way every time, is a completely "
                         "different pitch. This project's own simulator "
                         "treats a 2V dome as the second thing, not the "
                         "first.",
                     )),
                Shot("payload", 8.5, lens="macro", focus="apex",
                     yaw=-30, pitch=28, orbit=8,
                     caption="Minimal geometry, factory repetition, "
                             "rapid assembly, low operating demand, "
                             "resilience engineering, standardized "
                             "financing",
                     panel=OverlayPanel(
                         title="THE SIX-PART DEFINITION",
                         bullets=("Minimal geometry — two strut lengths, "
                                  "two triangle shapes",
                                  "Factory repetition — the same jig, "
                                  "every unit",
                                  "Rapid assembly, low operating demand, "
                                  "resilience engineering",
                                  "Standardized financing — priced and "
                                  "underwritten the same way every time"),
                         position="left"),
                     narration=(
                         "Six things have to be true at once for that "
                         "pitch to work: minimal geometry, factory "
                         "repetition, rapid assembly, low operating "
                         "demand, resilience engineering, and "
                         "standardized financing.",
                         "The next few minutes check this project's own "
                         "numbers against every one of those six, one at "
                         "a time.",
                     )),
            ),
        ),
        Scene(
            "six_parts", "Checking the six, one pair at a time",
            FIELD,
            world=(("dome", {"radius": R, "skin_alpha": 0.12}),
                  ("solar_band", {"radius": R, "coverage": 1.0})),
            shots=(
                Shot("geometry_repetition", 9.0, lens="wide", focus="dome",
                     yaw=-90, pitch=18, orbit=10,
                     caption="Minimal geometry + factory repetition: 2 "
                             "strut lengths, 2 triangle shapes, one jig",
                     panel=OverlayPanel(
                         title="1 & 2 — GEOMETRY, REPETITION",
                         stats=(("Structural struts",
                                 f"{len(GEO.hemisphere_edges)} total "
                                 f"({SHORT.hemisphere_count} short, "
                                 f"{LONG.hemisphere_count} long)"),
                                ("Triangle shapes",
                                 f"2 ({TRI_ISO.hemisphere_count} + "
                                 f"{TRI_EQU.hemisphere_count})"),
                                ("Hub vertices", f"{HUB_COUNT}")),
                         bullets=("Every panel and strut comes off the "
                                  "same two jigs",
                                  "Color-coded parts, flat-pack "
                                  "shipping"),
                         position="right"),
                     narration=(
                         "Minimal geometry and factory repetition are "
                         "really the same fact seen twice. Sixty five "
                         "struts, two lengths. Forty panels, two "
                         "shapes. Every one of them comes off the same "
                         "two jigs, color coded, flat packable.",
                         "That is not a simplification for the camera. "
                         "It is the actual geometry this project's "
                         "simulator computes, every time, for every "
                         "dome it builds.",
                     )),
                Shot("assembly_demand", 9.0, lens="wide", focus="dome",
                     yaw=60, pitch=16, orbit=8,
                     caption="Rapid assembly + low operating demand: "
                             "single-flow build time and a solar surplus",
                     panel=OverlayPanel(
                         title="3 & 4 — ASSEMBLY, OPERATING DEMAND",
                         stats=(("Total labor, one dome, all stations",
                                 f"{HERO_LABOR_HOURS:.0f} labor hours"),
                                ("Modeled solar array",
                                 f"{HERO_VALUE['solar_kw']:.1f} kW, "
                                 f"{HERO_VALUE['solar_panels']:.0f} "
                                 f"panels"),
                                ("Modeled daily surplus",
                                 f"{HERO_VALUE['net_daily_kwh']:.0f} kWh "
                                 f"over a "
                                 f"{ab.ASSUMPTIONS['daily_load_kwh']:.0f} "
                                 f"kWh/day load")),
                         position="left"),
                     narration=(
                         "Rapid assembly and low operating demand are "
                         "the other pair. This project's own station "
                         "timings add up to about "
                         f"{HERO_LABOR_HOURS:.0f} "
                         "labor hours to move one dome through every "
                         "station, start to finish.",
                         "And once it's standing, the modeled solar "
                         "array generates more than the modeled daily "
                         "load uses — low operating demand isn't a "
                         "slogan here, it's a subtracted number.",
                     )),
                Shot("resilience_financing", 9.0, lens="portrait",
                     focus="dome", yaw=140, pitch=18, orbit=6,
                     caption="Resilience engineering + standardized "
                             "financing: hedged, and computed",
                     panel=OverlayPanel(
                         title="5 & 6 — RESILIENCE, FINANCING",
                         stats=(("Structural claim",
                                 "Triangulated shell distributes load — "
                                 "not \"disaster-proof\""),
                                ("Financing, modeled",
                                 f"${HERO_PRICE:,.0f} · "
                                 f"{ab.ASSUMPTIONS['bhph_apr']*100:.1f}% "
                                 f"APR · ${HERO_MONTHLY:,.0f}/mo")),
                         position="right"),
                     narration=(
                         "Resilience engineering is real but modest: a "
                         "triangulated shell spreads load through more "
                         "paths than a stud wall does. That is as far "
                         "as this project will take the claim — not "
                         "disaster proof, just structurally different.",
                         "Standardized financing means the same math "
                         "every time: this representative dome, at "
                         "eleven point nine percent APR, comes to a "
                         "computed monthly payment, not a promised one.",
                     )),
            ),
        ),
        Scene(
            "factory_math", "The arithmetic a lender actually asks for",
            FIELD,
            world=(("dome", {"radius": R, "skin_alpha": 0.10}),),
            shots=(
                Shot("throughput", 9.0, lens="wide", focus="dome",
                     yaw=-70, pitch=16, orbit=10,
                     caption=f"One pipelined line: about "
                             f"{HERO_THROUGHPUT['pipelined_per_year']:.0f} "
                             f"domes a year",
                     panel=OverlayPanel(
                         title="ONE PRODUCTION LINE, MODELED",
                         stats=(("Bottleneck station",
                                 HERO_THROUGHPUT["bottleneck"]["key"]),
                                ("Units per year, pipelined",
                                 f"≈ "
                                 f"{HERO_THROUGHPUT['pipelined_per_year']:.0f}"),
                                ("Line capex",
                                 f"${HERO_BREAK_EVEN['capex']:,.0f}"),
                                ("Units to break even",
                                 f"≈ "
                                 f"{HERO_BREAK_EVEN['units_to_recover_capex']:.0f}")),
                         position="left"),
                     narration=(
                         "The same simulator that draws the struts runs "
                         "the factory math too. One pipelined line, "
                         "framing as the bottleneck station, turns out "
                         f"roughly "
                         f"{HERO_THROUGHPUT['pipelined_per_year']:.0f} "
                         "domes a year.",
                         "Against a two point four million dollar line "
                         "cost, that line recovers its own capital in "
                         f"about "
                         f"{HERO_BREAK_EVEN['units_to_recover_capex']:.0f} "
                         "units — arithmetic a lender checks, not a "
                         "pitch deck adjective.",
                     )),
                Shot("benchmark", 9.5, lens="portrait", focus="dome",
                     yaw=-150, pitch=20, orbit=8,
                     caption=f"Vs. a conventional manufactured home: "
                             f"{BENCH_PRICE_PCT:.0f}% less price, "
                             f"{BENCH_DAYS_PCT:.0f}% fewer build days",
                     panel=OverlayPanel(
                         title="VS. A CONVENTIONAL MANUFACTURED HOME",
                         stats=(
                             ("Benchmark",
                              f"${HERO_BENCH['conventional']['price']:,.0f}"
                              f" · "
                              f"{HERO_BENCH['conventional']['build_days']:.0f}"
                              f" build days"),
                             ("This simulator's representative dome",
                              f"${HERO_BENCH['dome']['price']:,.0f} · "
                              f"{HERO_BENCH['dome']['build_days']:.0f} "
                              f"build days")),
                         bullets=(f"{BENCH_LABOR_PCT:.0f}% fewer labor "
                                  "hours too",
                                  "This project's own assumptions, "
                                  "stated plainly enough to disagree "
                                  "with"),
                         position="right"),
                     narration=(
                         f"Set against this project's own conventional "
                         f"manufactured home benchmark, the representative "
                         f"dome prices {BENCH_PRICE_PCT:.0f} percent "
                         f"lower and models "
                         f"{BENCH_DAYS_PCT:.0f} percent fewer build "
                         f"days.",
                         "Those are stated assumptions, not a claim "
                         "dressed up as a fact — check them, disagree "
                         "with one, the arithmetic still shows its "
                         "work.",
                     )),
            ),
        ),
        Scene(
            "close", "Real evidence, honestly scoped",
            "a calm open field at dusk",
            world=(("dome", {"radius": R, "skin_alpha": 0.14}),),
            shots=(
                Shot("hedge", 9.0, lens="wide", focus="dome",
                     yaw=0, pitch=14, orbit=8,
                     caption="Federal modular-construction data, not a "
                             "dome-specific guarantee",
                     panel=OverlayPanel(
                         title="WHAT THE EVIDENCE ACTUALLY SAYS",
                         bullets=("DOE: modular construction broadly "
                                  "compresses schedules 20-50% and cuts "
                                  "costs up to 20%",
                                  "That is evidence about modular "
                                  "construction in general",
                                  "Not a guarantee for this specific "
                                  "shape — this project won't blur "
                                  "that line"),
                         position="left"),
                     narration=(
                         "One caveat, stated on purpose. Federal "
                         "research finds modular construction broadly "
                         "compresses schedules twenty to fifty percent "
                         "and cuts costs up to twenty percent.",
                         "That is real evidence about modular "
                         "construction as a category. It is not a "
                         "guarantee specific to this shape, and this "
                         "project is not going to blur that line to "
                         "make the pitch sound stronger than it is.",
                     )),
                Shot("close_shot", 10.0, lens="ultrawide", perspective=6,
                     focus="dome", yaw=-90, pitch=22,
                     caption="Six requirements, checked against real "
                             "numbers, out loud",
                     panel=OverlayPanel(
                         title="THE CASE, IN ONE LINE",
                         bullets=("Not a custom house — a standardized "
                                  "product",
                                  "Six requirements, six real numbers, "
                                  "computed by the same simulator",
                                  "Part of a ten-part case for 2V "
                                  "geodesic domes in the housing market"),
                         position="bottom"),
                     narration=(
                         "Minimal geometry, factory repetition, rapid "
                         "assembly, low operating demand, resilience "
                         "engineering, standardized financing — six "
                         "requirements, checked one at a time against "
                         "numbers this project's own software computes.",
                         "This is one part of a ten part case for 2V "
                         "geodesic domes in the housing market. The "
                         "manufacturing case is the one that holds up "
                         "best under its own weight.",
                     )),
            ),
        ),
    )
    return Presentation(
        title="The Standardized Product",
        author="DomeSim Presenter Studio",
        scenes=scenes,
    )
