"""Argument 10 of 10: where this actually wins (honest market fit).

The closing argument in the series: not "domes will replace housing,"
but a specific, defensible list of where a 2V dome is genuinely the
right tool — and an equally specific list of where it isn't. Closes the
whole ten-part case.
"""

from __future__ import annotations

from presenter.script import OverlayPanel, Presentation, Scene, Shot
from presentations._numbers import R

FIELD = "a calm open field in daylight"


def build() -> Presentation:
    scenes = (
        Scene(
            "hook", "Not the answer for dense urban housing — and "
                   "that's fine",
            FIELD,
            world=(("dome", {"radius": R, "skin_alpha": 0.14}),),
            shots=(
                Shot("not_everything", 9.0, lens="wide", focus="dome",
                     yaw=-40, pitch=16, orbit=8,
                     caption="\"Domes are the answer for dense urban "
                             "housing\" is a claim this project will "
                             "not make",
                     panel=OverlayPanel(
                         title="THE CLAIM THIS SERIES REFUSES",
                         bullets=("A 2V dome is not suited to "
                                  "high-rises or dense urban parcels",
                                  "Nine arguments in this series were "
                                  "about what the shape does well",
                                  "This one is about the discipline of "
                                  "saying where it doesn't apply"),
                         position="right"),
                     narration=(
                         "Nine arguments in this series were about "
                         "what this shape does well. This last one is "
                         "about the discipline of saying, just as "
                         "specifically, where it doesn't apply. Domes "
                         "are not the answer for dense urban housing, "
                         "and this project isn't going to pretend "
                         "otherwise.",
                     )),
            ),
        ),
        Scene(
            "where_it_fits", "Where the case actually holds",
            FIELD,
            world=(("dome", {"radius": R, "skin_alpha": 0.14}),),
            shots=(
                Shot("genuine_fit", 10.0, lens="wide", focus="dome",
                     yaw=60, pitch=16, orbit=8,
                     caption="Starter homes, ADUs, rural and off-grid, "
                             "disaster-resistant low-rise",
                     panel=OverlayPanel(
                         title="GENUINELY SUITED TO",
                         bullets=("Starter homes and workforce housing",
                                  "Accessory dwelling units",
                                  "Rural housing and off-grid "
                                  "residences",
                                  "Disaster-resistant low-rise "
                                  "construction",
                                  "Remote sites where a flat-pack shell "
                                  "beats trucking in lumber",
                                  "Workforce and veteran cottage "
                                  "communities, hospitality-funded "
                                  "development"),
                         position="left"),
                     narration=(
                         "Starter homes. Accessory dwelling units. "
                         "Rural housing, off-grid residences, "
                         "disaster-resistant low-rise construction, "
                         "remote sites where shipping a flat-pack "
                         "shell beats trucking in lumber. Workforce "
                         "and veteran cottage communities. Hospitality-"
                         "funded development that needs units built "
                         "fast and cheap.",
                         "Every one of those is a market where the "
                         "nine other arguments in this series actually "
                         "apply without much friction.",
                     )),
                Shot("not_suited", 9.0, lens="portrait", focus="dome",
                     yaw=-120, pitch=18, orbit=6,
                     caption="Not suited to high-rises or one-off "
                             "custom architecture",
                     panel=OverlayPanel(
                         title="NOT SUITED TO",
                         bullets=("High-rise or dense urban parcels — "
                                  "the geometry doesn't stack",
                                  "One-off custom architecture — the "
                                  "whole case rests on standardization",
                                  "Anywhere the buyer wants a shape a "
                                  "factory jig can't repeat"),
                         position="right"),
                     narration=(
                         "And not suited to high-rise or dense urban "
                         "parcels — the geometry doesn't stack the way "
                         "a building on a shared party wall needs to. "
                         "Not suited to one-off custom architecture "
                         "either, because the entire case in this "
                         "series rests on standardization. Ask for a "
                         "shape a factory jig can't repeat, and you've "
                         "asked for the one thing this product isn't.",
                     )),
            ),
        ),
        Scene(
            "the_sizes", "Three sizes, not one dome scaled up forever",
            FIELD,
            world=(("dome", {"radius": 3.05, "skin_alpha": 0.16}),),
            shots=(
                Shot("grow", 10.0, lens="wide", focus="",
                     yaw=-70, pitch=18, orbit=8,
                     actions=(("dome", "radius", 3.05, 5.49),),
                     caption="D20 studio to D36 family size — three "
                             "products, not one dome stretched thin",
                     panel=OverlayPanel(
                         title="THE ACTUAL PRODUCT SIZES",
                         stats=(("D20", "20 ft — studio, ADU, office, "
                                 "emergency shelter"),
                                ("D30", "30 ft — one-bedroom starter"),
                                ("D36", "36 ft — two-bedroom family")),
                         position="left"),
                     narration=(
                         "The product line comes in three sizes: a "
                         "twenty foot studio and ADU size, a thirty "
                         "foot one-bedroom starter size, and a thirty "
                         "six foot two-bedroom family size.",
                     )),
                Shot("dont_overscale", 9.0, lens="portrait",
                     focus="dome", yaw=100, pitch=16, orbit=6,
                     caption="Bigger family homes connect shells "
                             "together — they don't just scale one "
                             "dome up",
                     panel=OverlayPanel(
                         title="WHY IT STOPS AT D36",
                         bullets=("Buckling risk and panel handling "
                                  "both get worse as diameter grows",
                                  "A larger family home should connect "
                                  "multiple shells, not just inflate "
                                  "one bigger dome",
                                  "The standardization argument breaks "
                                  "if every size needs a new panel "
                                  "jig"),
                         position="right"),
                     narration=(
                         "It stops there on purpose. Buckling risk and "
                         "panel handling both get worse as diameter "
                         "grows, and a bigger dome needs its own jigs "
                         "— which breaks the standardization argument "
                         "this whole series is built on.",
                         "A larger family home connects multiple "
                         "shells together instead of inflating one "
                         "dome past where the geometry stays honest.",
                     )),
            ),
        ),
        Scene(
            "close", "Ten arguments, one honest bottom line",
            "a tropical beach at sunset",
            world=(("dome", {"radius": R, "skin_alpha": 0.16}),),
            shots=(
                Shot("close_shot", 12.0, lens="ultrawide", perspective=6,
                     focus="dome", yaw=-90, pitch=22,
                     caption="A narrower claim than 'domes will "
                             "replace housing' — and one this project "
                             "can actually defend",
                     panel=OverlayPanel(
                         title="THE BOTTOM LINE, TEN ARGUMENTS IN",
                         bullets=("Manufacturing, cost, rigidity, "
                                  "resilience, energy, financing, and "
                                  "the curved-wall objection — nine "
                                  "real, hedged arguments",
                                  "This tenth argument draws the "
                                  "actual boundary around where they "
                                  "apply",
                                  "Every number in all ten came from "
                                  "the same software, computed the "
                                  "same way, every time"),
                         position="bottom"),
                     narration=(
                         "Nine arguments about manufacturing, cost, "
                         "rigidity, resilience, energy, the curved-"
                         "wall objection, and financing. One tenth "
                         "argument drawing the actual boundary around "
                         "where all of it applies. That is a narrower "
                         "claim than 'domes will replace housing' — "
                         "and it's one this project can defend, line "
                         "by line, with its own numbers.",
                         "Every figure across all ten of these "
                         "presentations came from the same software, "
                         "computed the same way, every time. That "
                         "consistency is the actual argument.",
                     )),
            ),
        ),
    )
    return Presentation(
        title="Where This Actually Wins",
        author="DomeSim Presenter Studio",
        scenes=scenes,
    )
