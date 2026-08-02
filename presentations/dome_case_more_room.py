"""Argument 3 of 10: more room, same money (the home tier).

The harder, fully-finished test — and the honest reframe once the price
gap turns out small. Numbers come straight from
``al_build.building_comparisons()`` via ``presentations._numbers``.
"""

from __future__ import annotations

import al_build as ab
from presenter.script import OverlayPanel, Presentation, Scene, Shot
from presentations._numbers import (
    HOME, HOME_BOX_H, HOME_BOX_L, HOME_BOX_W, HOME_DOME_R_M,
    HOME_FRAME_PCT, HOME_SAVE_PCT, HOME_VOL_PCT,
)

FIELD = "a calm open field in daylight"
WORLD = (("comparison_pair",
         {"box_w": HOME_BOX_W, "box_l": HOME_BOX_L, "box_h": HOME_BOX_H,
          "dome_r": HOME_DOME_R_M, "gap": 3.4}),)


def build() -> Presentation:
    scenes = (
        Scene(
            "hook", "A harder test, on purpose",
            FIELD,
            world=WORLD,
            shots=(
                Shot("setup", 9.0, lens="wide", focus="compare_pair",
                     yaw=-30, pitch=16, orbit=8,
                     caption=f"Same {ab.COMPARE_HOME_FLOOR_SF:.0f} sq "
                             f"ft floor, both fully finished this time",
                     panel=OverlayPanel(
                         title="THE HARDER TEST",
                         bullets=("Kitchen, bath, and mechanicals in "
                                  "both buildings this time",
                                  "Matched on floor area, because a "
                                  "house sells living space",
                                  "This is deliberately the test that "
                                  "makes the shape's job hardest"),
                         position="right"),
                     narration=(
                         "The bare-shell test was the easy win. This "
                         "one is deliberately harder: both buildings "
                         "fully finished, kitchen, bath, mechanicals, "
                         "matched on six hundred forty square feet of "
                         "floor because a house sells living space, "
                         "not enclosed volume.",
                         "If the dome's advantage is going to survive "
                         "anywhere, it has to survive here, where a lot "
                         "of the cost has nothing to do with the shape "
                         "of the walls.",
                     )),
            ),
        ),
        Scene(
            "the_honest_number", "The smaller number is the trustworthy one",
            FIELD,
            world=WORLD,
            shots=(
                Shot("price", 9.5, lens="wide", focus="compare_pair",
                     yaw=25, pitch=15, orbit=8,
                     caption=f"Only {HOME_SAVE_PCT:.1f}% cheaper — not "
                             f"the 24% you'd expect from round one",
                     panel=OverlayPanel(
                         title="THE HONEST PRICE",
                         stats=(("Stick-built house",
                                 f"${HOME['box']['build']:,.0f}"),
                                ("Dome house",
                                 f"${HOME['dome']['build']:,.0f}")),
                         position="left"),
                     narration=(
                         f"Stick built house: "
                         f"${HOME['box']['build']:,.0f}. Dome house: "
                         f"${HOME['dome']['build']:,.0f}. Only "
                         f"{HOME_SAVE_PCT:.1f} percent cheaper — a "
                         "fraction of the bare-shell savings.",
                         "That smaller number is the one worth trusting "
                         "precisely because it's smaller. A number that "
                         "stayed at twenty four percent after adding a "
                         "kitchen and bath would be the one to "
                         "distrust.",
                     )),
                Shot("why_smaller", 9.0, lens="portrait", focus="compare_pair",
                     yaw=-60, pitch=18, orbit=6,
                     caption="Kitchens, baths, and mechanicals cost the "
                             "same no matter what shape the walls are",
                     panel=OverlayPanel(
                         title="WHY IT SHRINKS",
                         bullets=("A finished home's cost is dominated "
                                  "by fit-out, not framing",
                                  "Cabinets, plumbing fixtures, "
                                  "HVAC — identical cost in a box or a "
                                  "dome",
                                  "Shape only affects the shell, and "
                                  "the shell is a shrinking share of "
                                  "the total"),
                         position="right"),
                     narration=(
                         "A finished home's price is dominated by "
                         "fit-out, not framing. A kitchen costs the "
                         "same whether it sits against a straight wall "
                         "or a curved one. Shape only moves the needle "
                         "on the shell, and the shell is a shrinking "
                         "share of the total once the fit-out goes in.",
                     )),
            ),
        ),
        Scene(
            "the_real_win", "The number worth remembering",
            FIELD,
            world=WORLD,
            shots=(
                Shot("framing", 8.5, lens="portrait", focus="compare_dome",
                     yaw=100, pitch=16, orbit=6,
                     caption=f"{HOME_FRAME_PCT:.0f}% less framing "
                             f"lumber for the identical floor area",
                     panel=OverlayPanel(
                         title="STILL TRUE: LESS FRAMING",
                         stats=(("Stick framing",
                                 f"{HOME['box']['framing_lf']:,.0f} ft"),
                                ("Dome framing",
                                 f"{HOME['dome']['framing_lf']:,.0f} "
                                 f"ft")),
                         position="left"),
                     narration=(
                         f"The framing number didn't shrink nearly as "
                         f"much: {HOME_FRAME_PCT:.0f} percent less "
                         "lumber for the identical floor area. Less "
                         "material, less labor cutting and setting it, "
                         "even after the price gap narrowed.",
                     )),
                Shot("volume", 9.5, lens="wide", focus="compare_dome",
                     yaw=-160, pitch=20, orbit=8,
                     caption=f"Same footprint, about the same money — "
                             f"{HOME_VOL_PCT:.0f}% more enclosed volume",
                     panel=OverlayPanel(
                         title="WHERE THE HOME TIER ACTUALLY WINS",
                         stats=(("Enclosed volume, same footprint",
                                 f"+{HOME_VOL_PCT:.0f}% for the "
                                 f"dome"),),
                         bullets=("A hemisphere captures the volume a "
                                  "flat ceiling throws away",
                                  "For the same footprint and almost "
                                  "the same money"),
                         position="right"),
                     narration=(
                         "Here is the number worth remembering instead "
                         "of price. For the same footprint and almost "
                         f"the same money, the dome encloses "
                         f"{HOME_VOL_PCT:.0f} percent more volume, "
                         "because a hemisphere captures the space a "
                         "flat ceiling simply throws away.",
                     )),
            ),
        ),
        Scene(
            "close", "The honest pitch",
            "a calm open field at dusk",
            world=WORLD,
            shots=(
                Shot("reframe", 10.0, lens="ultrawide", perspective=6,
                     focus="compare_pair", yaw=-90, pitch=22,
                     caption="Not 'cheaper' — 'more room for the same "
                             "money'",
                     panel=OverlayPanel(
                         title="THE ACTUAL PITCH FOR A FINISHED HOME",
                         bullets=("Not that domes are dramatically "
                                  "cheaper — they usually are not, "
                                  "finished",
                                  "That the same money buys measurably "
                                  "more livable space",
                                  "A pitch this project can defend with "
                                  "its own numbers, both directions"),
                         position="bottom"),
                     narration=(
                         "So here is the actual pitch for a finished "
                         "home, stated the honest way: not that domes "
                         "are dramatically cheaper, because the numbers "
                         "just showed you they usually are not.",
                         "It's that the same money buys measurably more "
                         "room. That is a pitch this project can defend "
                         "with its own numbers in both directions, "
                         "which is worth more than a bigger number it "
                         "couldn't.",
                     )),
            ),
        ),
    )
    return Presentation(
        title="More Room, Same Money",
        author="DomeSim Presenter Studio",
        scenes=scenes,
    )
