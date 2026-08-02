"""Argument 5 of 10: beating the manufactured home (the real benchmark).

Not a comparison to stick-built custom construction — a comparison to
the existing manufactured-home industry this project's own model treats
as its actual competitor. Numbers come from al_build.benchmark() /
throughput() / break_even() via presentations._numbers.
"""

from __future__ import annotations

from presenter.script import OverlayPanel, Presentation, Scene, Shot
from presentations._numbers import (
    BENCH_DAYS_PCT, BENCH_LABOR_PCT, BENCH_PRICE_PCT, HERO_BENCH,
    HERO_BREAK_EVEN, HERO_LABOR_HOURS, HERO_THROUGHPUT, R,
)

FIELD = "a calm open field in daylight"


def build() -> Presentation:
    scenes = (
        Scene(
            "hook", "The competitor that actually matters",
            FIELD,
            world=(("dome", {"radius": R, "skin_alpha": 0.14}),),
            shots=(
                Shot("thesis", 9.0, lens="wide", focus="dome",
                     yaw=-45, pitch=16, orbit=8,
                     caption="Not a comparison to a custom house — a "
                             "comparison to the existing manufactured "
                             "home industry",
                     panel=OverlayPanel(
                         title="WHY THIS BENCHMARK",
                         bullets=("Manufactured homes already have a "
                                  "market, buyers, and lenders",
                                  "If a dome can't beat that industry's "
                                  "own numbers, the pitch is weaker "
                                  "than it sounds",
                                  "This project sets its own benchmark "
                                  "and checks against it, in the open"),
                         position="right"),
                     narration=(
                         "Comparing a dome to a bespoke stick-built "
                         "custom house is an easy win and not a very "
                         "useful one. The competitor that actually "
                         "matters is the manufactured home industry — "
                         "it already has a market, buyers, and lenders "
                         "who understand it.",
                         "This project sets its own benchmark for that "
                         "industry, states the assumption plainly, and "
                         "checks a representative dome against it — in "
                         "the open, not behind a marketing number.",
                     )),
            ),
        ),
        Scene(
            "the_matchup", "The three numbers that matter to a buyer",
            FIELD,
            world=(("dome", {"radius": R, "skin_alpha": 0.12}),),
            shots=(
                Shot("price", 9.0, lens="wide", focus="dome",
                     yaw=60, pitch=16, orbit=8,
                     caption=f"{BENCH_PRICE_PCT:.0f}% lower price",
                     panel=OverlayPanel(
                         title="PRICE",
                         stats=(("Conventional manufactured home",
                                 f"${HERO_BENCH['conventional']['price']:,.0f}"),
                                ("This simulator's representative dome",
                                 f"${HERO_BENCH['dome']['price']:,.0f}")),
                         position="right"),
                     narration=(
                         f"Price first: "
                         f"${HERO_BENCH['conventional']['price']:,.0f} "
                         f"for the benchmark, "
                         f"${HERO_BENCH['dome']['price']:,.0f} for the "
                         f"representative dome — "
                         f"{BENCH_PRICE_PCT:.0f} percent lower.",
                     )),
                Shot("labor", 9.0, lens="wide", focus="dome",
                     yaw=-130, pitch=18, orbit=8,
                     caption=f"{BENCH_LABOR_PCT:.0f}% fewer labor hours",
                     panel=OverlayPanel(
                         title="LABOR",
                         stats=(("Conventional manufactured home",
                                 f"{HERO_BENCH['conventional']['labor_hours']:.0f}"
                                 f" labor hrs"),
                                ("This simulator's representative dome",
                                 f"{HERO_LABOR_HOURS:.0f} labor hrs")),
                         position="left"),
                     narration=(
                         f"Labor second: "
                         f"{HERO_BENCH['conventional']['labor_hours']:.0f}"
                         f" hours for the benchmark against "
                         f"{HERO_LABOR_HOURS:.0f} for the dome — "
                         f"{BENCH_LABOR_PCT:.0f} percent fewer hours "
                         "of paid work to build one.",
                     )),
                Shot("days", 9.0, lens="portrait", focus="dome",
                     yaw=10, pitch=20, orbit=6,
                     caption=f"{BENCH_DAYS_PCT:.0f}% fewer build days",
                     panel=OverlayPanel(
                         title="TIME",
                         stats=(("Conventional manufactured home",
                                 f"{HERO_BENCH['conventional']['build_days']:.0f}"
                                 f" build days"),
                                ("This simulator's representative dome",
                                 f"{HERO_BENCH['dome']['build_days']:.0f}"
                                 f" build days")),
                         position="right"),
                     narration=(
                         f"And time: "
                         f"{HERO_BENCH['conventional']['build_days']:.0f} "
                         f"days for the benchmark, "
                         f"{HERO_BENCH['dome']['build_days']:.0f} for "
                         f"the dome — {BENCH_DAYS_PCT:.0f} percent "
                         "fewer days between a signed contract and a "
                         "finished shell.",
                     )),
            ),
        ),
        Scene(
            "the_factory", "How one factory hits these numbers",
            FIELD,
            world=(("dome", {"radius": R, "skin_alpha": 0.10}),),
            shots=(
                Shot("throughput", 9.5, lens="wide", focus="dome",
                     yaw=-70, pitch=16, orbit=10,
                     caption=f"About "
                             f"{HERO_THROUGHPUT['pipelined_per_year']:.0f} "
                             f"domes a year from one pipelined line",
                     panel=OverlayPanel(
                         title="THE FACTORY MATH",
                         stats=(("Bottleneck station",
                                 HERO_THROUGHPUT["bottleneck"]["key"]),
                                ("Units per year, pipelined",
                                 f"≈ "
                                 f"{HERO_THROUGHPUT['pipelined_per_year']:.0f}"),
                                ("Line capex",
                                 f"${HERO_BREAK_EVEN['capex']:,.0f}")),
                         position="left"),
                     narration=(
                         "These aren't wishful numbers — they come "
                         "from a station-by-station model of one "
                         "production line, framing as the bottleneck, "
                         f"turning out roughly "
                         f"{HERO_THROUGHPUT['pipelined_per_year']:.0f} "
                         "domes a year.",
                     )),
                Shot("breakeven", 9.0, lens="portrait", focus="dome",
                     yaw=150, pitch=18, orbit=6,
                     caption=f"Break-even in about "
                             f"{HERO_BREAK_EVEN['units_to_recover_capex']:.0f} "
                             f"units",
                     panel=OverlayPanel(
                         title="THE BREAK-EVEN",
                         stats=(("Units to cover annual fixed cost",
                                 f"≈ "
                                 f"{HERO_BREAK_EVEN['units_to_cover_annual_fixed']:.0f}"),
                                ("Units to recover the full line capex",
                                 f"≈ "
                                 f"{HERO_BREAK_EVEN['units_to_recover_capex']:.0f}")),
                         position="right"),
                     narration=(
                         "At that rate, the line covers its own annual "
                         "fixed overhead in a few weeks of production "
                         "and recovers its full capital cost in about "
                         f"{HERO_BREAK_EVEN['units_to_recover_capex']:.0f} "
                         "units — the kind of number that gets a "
                         "factory built in the first place.",
                     )),
            ),
        ),
        Scene(
            "close", "Assumptions you can check, not a number to trust "
                    "blind",
            "a calm open field at dusk",
            world=(("dome", {"radius": R, "skin_alpha": 0.14}),),
            shots=(
                Shot("close_shot", 10.5, lens="ultrawide", perspective=6,
                     focus="dome", yaw=-90, pitch=22,
                     caption="Every input is stated — disagree with one "
                             "and the arithmetic still shows its work",
                     panel=OverlayPanel(
                         title="STATED, NOT HIDDEN",
                         bullets=("Wage rates, station timings, and the "
                                  "benchmark price are this project's "
                                  "own assumptions",
                                  "Change any one of them and the "
                                  "percentages move — the model is not "
                                  "hiding that",
                                  "Part of a ten-part case for 2V "
                                  "geodesic domes in the housing "
                                  "market"),
                         position="bottom"),
                     narration=(
                         "Every number behind this comparison — wage "
                         "rates, station timings, the benchmark price "
                         "itself — is a stated assumption in this "
                         "project's own code, not a hidden constant. "
                         "Change one and the percentages move, openly.",
                         "That is the actual claim: not that this beats "
                         "a manufactured home by magic, but that it "
                         "beats this project's own honestly stated "
                         "assumptions about one. This is one part of a "
                         "ten part case for 2V geodesic domes in the "
                         "housing market.",
                     )),
            ),
        ),
    )
    return Presentation(
        title="Beating the Manufactured Home",
        author="DomeSim Presenter Studio",
        scenes=scenes,
    )
