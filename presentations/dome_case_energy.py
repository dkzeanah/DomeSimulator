"""Argument 6 of 10: the off-grid case (energy and solar).

A genuine geometric advantage (more enclosed volume per square foot of
skin), a real modeled solar system, and a hard stop before the
oversold version of this argument ("every dome uses 30-50% less
energy"). Numbers come from al_build.product_value() via
presentations._numbers.
"""

from __future__ import annotations

import al_build as ab
from presenter.script import OverlayPanel, Presentation, Scene, Shot
from presentations._numbers import HERO_VALUE, R

FIELD = "a calm open field in daylight"
WORLD = (("dome", {"radius": R, "skin_alpha": 0.14}),
        ("solar_band", {"radius": R, "coverage": 1.0}))


def build() -> Presentation:
    scenes = (
        Scene(
            "hook", "Why off-grid matters to this pitch",
            FIELD,
            world=WORLD,
            shots=(
                Shot("thesis", 9.0, lens="wide", focus="dome",
                     yaw=-50, pitch=16, orbit=8,
                     caption="A dome that runs on its own power is a "
                             "different sale in a rural or disaster "
                             "market",
                     panel=OverlayPanel(
                         title="WHY THIS ARGUMENT MATTERS",
                         bullets=("Off-grid capability opens rural, "
                                  "remote, and disaster-response "
                                  "markets a grid-tied product can't "
                                  "reach",
                                  "The geometry has one real, provable "
                                  "advantage here",
                                  "The rest has to be hedged, and this "
                                  "presentation hedges it"),
                         position="right"),
                     narration=(
                         "Off-grid capability changes what market a "
                         "housing product can sell into. A rural site, "
                         "a disaster response deployment, a remote "
                         "off-grid residence — none of those care about "
                         "a grid connection they don't have.",
                         "The shape has exactly one real, provable "
                         "advantage in this argument. Everything past "
                         "that has to be hedged carefully, and this "
                         "presentation hedges it.",
                     )),
            ),
        ),
        Scene(
            "the_geometry", "The one real geometric fact",
            FIELD,
            world=WORLD,
            shots=(
                Shot("surface_volume", 9.5, lens="wide", focus="dome",
                     yaw=90, pitch=18, orbit=8,
                     caption="More enclosed volume per square foot of "
                             "skin — real, and just geometry",
                     panel=OverlayPanel(
                         title="THE PROVABLE PART",
                         bullets=("A sphere minimizes surface area for "
                                  "a given enclosed volume",
                                  "Less exterior skin means less area "
                                  "for heat to cross",
                                  "This part is a mathematical fact, "
                                  "not a performance promise"),
                         position="left"),
                     narration=(
                         "A sphere encloses more volume per square "
                         "foot of skin than a box does — the same fact "
                         "that drives the cost comparisons elsewhere "
                         "in this series. Less exterior skin area means "
                         "less area for heat to cross, in either "
                         "direction.",
                         "That much is geometry, not a promise about "
                         "how the finished building actually performs.",
                     )),
                Shot("r_value", 8.5, lens="macro", focus="apex",
                     yaw=-20, pitch=30, orbit=6,
                     caption=f"This project's own insulation model: "
                             f"R-{HERO_VALUE['r_value']:.0f} effective, "
                             f"one representative build",
                     panel=OverlayPanel(
                         title="ONE MODELED BUILD",
                         stats=(("Effective R-value",
                                 f"R-{HERO_VALUE['r_value']:.0f}"),),
                         bullets=("Computed from this dome's own "
                                  "insulation element count",
                                  "One representative build, not a "
                                  "universal claim"),
                         position="right"),
                     narration=(
                         "This project's own insulation model, for one "
                         "representative build, lands at roughly an "
                         f"R-{HERO_VALUE['r_value']:.0f} effective "
                         "value — computed from the actual insulation "
                         "elements this dome's catalog includes, not "
                         "assumed.",
                     )),
            ),
        ),
        Scene(
            "the_system", "What's actually modeled on the roof",
            FIELD,
            world=WORLD,
            shots=(
                Shot("array", 9.0, lens="wide", focus="solar",
                     yaw=-140, pitch=22, orbit=8,
                     caption="Panels placed only on faces the "
                             "geometry says face the sun",
                     panel=OverlayPanel(
                         title="THE MODELED SOLAR ARRAY",
                         stats=(("Panels placed",
                                 f"{HERO_VALUE['solar_panels']:.0f}"),
                                ("Array size",
                                 f"{HERO_VALUE['solar_kw']:.1f} kW"),
                                ("Daily generation",
                                 f"{HERO_VALUE['daily_generation_kwh']:.0f}"
                                 f" kWh")),
                         position="right"),
                     narration=(
                         f"{HERO_VALUE['solar_panels']:.0f} panels, "
                         f"placed only on the faces this dome's own "
                         f"geometry says face the sun, model out to a "
                         f"{HERO_VALUE['solar_kw']:.1f} kilowatt array "
                         f"generating roughly "
                         f"{HERO_VALUE['daily_generation_kwh']:.0f} "
                         "kilowatt hours on a representative day.",
                     )),
                Shot("surplus", 8.5, lens="portrait", focus="solar",
                     yaw=40, pitch=16, orbit=6,
                     caption=f"{HERO_VALUE['net_daily_kwh']:.0f} kWh "
                             f"modeled daily surplus over a "
                             f"{ab.ASSUMPTIONS['daily_load_kwh']:.0f} "
                             f"kWh/day load",
                     panel=OverlayPanel(
                         title="THE MODELED SURPLUS",
                         stats=(("Modeled daily load",
                                 f"{ab.ASSUMPTIONS['daily_load_kwh']:.0f}"
                                 f" kWh"),
                                ("Modeled daily surplus",
                                 f"{HERO_VALUE['net_daily_kwh']:.0f} "
                                 f"kWh"),
                                ("Battery capacity modeled",
                                 f"{HERO_VALUE['battery_kwh']:.0f} "
                                 f"kWh")),
                         position="left"),
                     narration=(
                         f"Against a modeled "
                         f"{ab.ASSUMPTIONS['daily_load_kwh']:.0f} "
                         "kilowatt hour daily load, that leaves a "
                         f"modeled surplus of about "
                         f"{HERO_VALUE['net_daily_kwh']:.0f} kilowatt "
                         "hours a day, banked against a battery sized "
                         f"for {HERO_VALUE['battery_kwh']:.0f} kilowatt "
                         "hours. Low operating demand, computed rather "
                         "than asserted.",
                     )),
            ),
        ),
        Scene(
            "the_hedge", "The claim that doesn't survive contact with "
                        "reality",
            "a calm open field at dusk",
            world=WORLD,
            shots=(
                Shot("myth", 9.5, lens="wide", focus="dome",
                     yaw=0, pitch=14, orbit=8,
                     caption="\"Every dome uses 30-50% less energy\" "
                             "is a claim this project will not make",
                     panel=OverlayPanel(
                         title="WHAT THE EVIDENCE DOESN'T SAY",
                         stats=(("One published simulation study "
                                 "(2024)",
                                 "52% lower cooling load — a geodesic "
                                 "tourist-accommodation model"),),
                         bullets=("One study, one building, one "
                                  "climate — not a universal law",
                                  "HVAC design, climate, and "
                                  "airtightness still decide the real "
                                  "number, every time",
                                  "This project's real numbers are "
                                  "hedged on purpose"),
                         position="right"),
                     narration=(
                         "A 2024 simulation study of geodesic tourist "
                         "accommodations found fifty two percent lower "
                         "cooling energy. That is one study, one "
                         "building, one climate — not a universal law "
                         "about domes.",
                         "Anyone who tells you every dome uses thirty "
                         "to fifty percent less energy, regardless of "
                         "climate or how it's built, is overselling "
                         "the shape. HVAC design, climate, and "
                         "airtightness still decide the real number, "
                         "every time.",
                     )),
                Shot("close_shot", 9.0, lens="ultrawide", perspective=6,
                     focus="dome", yaw=-90, pitch=22,
                     caption="Real geometry, real modeled numbers, one "
                             "claim deliberately left out",
                     panel=OverlayPanel(
                         title="THE HONEST OFF-GRID CASE",
                         bullets=("Less skin per volume: geometric fact",
                                  "Solar surplus: computed by this "
                                  "project's own model",
                                  "Universal energy savings: a claim "
                                  "this project refuses to make"),
                         position="bottom"),
                     narration=(
                         "Real geometry, real modeled solar numbers, "
                         "and one claim deliberately left off the "
                         "list. That is the honest version of the "
                         "off-grid case — part of a ten part argument "
                         "for 2V geodesic domes in the housing market.",
                     )),
            ),
        ),
    )
    return Presentation(
        title="The Off-Grid Case",
        author="DomeSim Presenter Studio",
        scenes=scenes,
    )
