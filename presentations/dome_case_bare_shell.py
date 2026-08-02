"""Argument 2 of 10: the bare-shell number (the shed tier).

The cleanest possible test: strip away finishes, kitchens, and mechanical
systems entirely, price two bare shells built from identical materials at
identical rates, matched on enclosed volume. Numbers come straight from
``al_build.building_comparisons()`` via ``presentations._numbers`` — the
same function the interactive assembly-line comparison area uses.
"""

from __future__ import annotations

from presenter.script import OverlayPanel, Presentation, Scene, Shot
from presentations._numbers import (
    SHED, SHED_BOX_H, SHED_BOX_L, SHED_BOX_W, SHED_CLAD_PCT,
    SHED_DOME_R_M, SHED_FRAME_PCT, SHED_SAVE_PCT,
)

FIELD = "a calm open field in daylight"
WORLD = (("comparison_pair",
         {"box_w": SHED_BOX_W, "box_l": SHED_BOX_L, "box_h": SHED_BOX_H,
          "dome_r": SHED_DOME_R_M, "gap": 3.0}),)


def build() -> Presentation:
    scenes = (
        Scene(
            "hook", "The cleanest possible test",
            FIELD,
            world=WORLD,
            shots=(
                Shot("frame", 9.0, lens="wide", focus="compare_pair",
                     yaw=-30, pitch=15, orbit=8,
                     caption="Strip away every finish. What's left is "
                             "just the shape.",
                     panel=OverlayPanel(
                         title="WHY A BARE SHELL",
                         bullets=("No kitchens, no fixtures, no "
                                  "mechanicals to blur the comparison",
                                  "A shed sells storage space, so match "
                                  "the two on enclosed volume",
                                  "Same lumber rate, same skin rate, "
                                  "same labor rate for both"),
                         position="right"),
                     narration=(
                         "Before any argument about kitchens or "
                         "mechanicals, here is the cleanest possible "
                         "test: two bare shells, no finishes at all, "
                         "priced from identical materials at identical "
                         "rates.",
                         "A shed sells storage space, so the two "
                         "buildings are matched on one thing only: "
                         "enclosed volume. The only variable left is the "
                         "shape.",
                     )),
                Shot("both", 8.0, lens="ultrawide", focus="compare_pair",
                     yaw=10, pitch=18, orbit=10,
                     caption=f"Same {SHED['box']['vol_ft3']:,.0f} cubic "
                             f"feet enclosed, two different shapes",
                     panel=OverlayPanel(
                         title="THE SETUP",
                         stats=(("Enclosed volume, both",
                                 f"{SHED['box']['vol_ft3']:,.0f} ft³"),
                                ("Box footprint",
                                 "24 × 16 ft, 10 ft wall"),
                                ("Dome radius",
                                 f"{SHED['dome']['r_ft']:.1f} ft")),
                         position="left"),
                     narration=(
                         "Twenty four by sixteen feet, ten foot walls, "
                         "on the left. A dome sized to enclose that "
                         "exact same volume, on the right. Same "
                         "materials. Same crew rate. Different geometry.",
                     )),
            ),
        ),
        Scene(
            "the_numbers", "What the identical materials actually cost",
            FIELD,
            world=WORLD,
            shots=(
                Shot("build_cost", 9.5, lens="wide", focus="compare_pair",
                     yaw=-50, pitch=16, orbit=8,
                     caption=f"{SHED_SAVE_PCT:.0f}% less to build, same "
                             f"materials, same labor rate",
                     panel=OverlayPanel(
                         title="THE BUILD COST",
                         stats=(("Box shell",
                                 f"${SHED['box']['build']:,.0f}"),
                                ("Dome shell",
                                 f"${SHED['dome']['build']:,.0f}")),
                         bullets=(f"{SHED_SAVE_PCT:.0f}% cheaper, and "
                                  "nothing about the rates changed — "
                                  "only the shape did",),
                         position="right"),
                     narration=(
                         f"The box costs "
                         f"${SHED['box']['build']:,.0f}. The dome costs "
                         f"${SHED['dome']['build']:,.0f}. That is "
                         f"{SHED_SAVE_PCT:.0f} percent less, and not one "
                         "material rate changed between the two "
                         "numbers — only the geometry did.",
                     )),
                Shot("framing", 9.0, lens="portrait", focus="compare_dome",
                     yaw=60, pitch=18, orbit=6,
                     caption=f"{SHED_FRAME_PCT:.0f}% less framing lumber "
                             f"to enclose the same space",
                     panel=OverlayPanel(
                         title="WHERE THE SAVINGS COME FROM: FRAMING",
                         stats=(("Box framing",
                                 f"{SHED['box']['framing_lf']:,.0f} ft"),
                                ("Dome framing",
                                 f"{SHED['dome']['framing_lf']:,.0f} ft")),
                         position="left"),
                     narration=(
                         f"Framing tells the same story from the "
                         f"lumber side: {SHED_FRAME_PCT:.0f} percent "
                         f"less linear footage of frame to enclose the "
                         f"identical volume. Fewer members, less labor "
                         f"cutting and setting them.",
                     )),
                Shot("cladding", 9.0, lens="portrait", focus="compare_dome",
                     yaw=-100, pitch=16, orbit=6,
                     caption=f"{SHED_CLAD_PCT:.0f}% less exterior skin "
                             f"for the same enclosed volume",
                     panel=OverlayPanel(
                         title="WHERE THE SAVINGS COME FROM: SKIN",
                         stats=(("Box skin area",
                                 f"{SHED['box']['cladding_sf']:,.0f} "
                                 f"ft²"),
                                ("Dome skin area",
                                 f"{SHED['dome']['cladding_sf']:,.0f} "
                                 f"ft²")),
                         position="right"),
                     narration=(
                         f"And the skin: {SHED_CLAD_PCT:.0f} percent "
                         "less exterior sheet metal to wrap the same "
                         "enclosed volume. Less material bought, less "
                         "material installed.",
                     )),
            ),
        ),
        Scene(
            "why_it_works", "The reason is a sphere, not a sales pitch",
            FIELD,
            world=WORLD,
            shots=(
                Shot("geometry", 9.5, lens="wide", focus="compare_dome",
                     yaw=140, pitch=20, orbit=8,
                     caption="A sphere encloses more volume per square "
                             "foot of skin than a box does — that's "
                             "just geometry",
                     panel=OverlayPanel(
                         title="THE ACTUAL REASON",
                         bullets=("A box's corners and flat faces waste "
                                  "surface area relative to the volume "
                                  "inside",
                                  "A sphere is the shape that minimizes "
                                  "surface area for a given volume",
                                  "Less surface area needing framing "
                                  "and skin is a mathematical fact, not "
                                  "a sales pitch"),
                         position="left"),
                     narration=(
                         "There is no trick here. A sphere is the shape "
                         "that minimizes surface area for a given "
                         "enclosed volume — a mathematical fact, not a "
                         "sales pitch. A box's flat faces and sharp "
                         "corners simply need more material to wrap the "
                         "same amount of space.",
                         "A 2V dome is an approximation of that sphere, "
                         "close enough to inherit most of the "
                         "advantage.",
                     )),
                Shot("caveat_close", 9.0, lens="wide", focus="compare_pair",
                     yaw=0, pitch=14, orbit=6,
                     caption="This is the bare-shell number — the "
                             "finished-home number is smaller, and "
                             "that's the honest one too",
                     panel=OverlayPanel(
                         title="ONE HONEST CAVEAT",
                         bullets=("This test strips out kitchens, "
                                  "baths, and mechanicals on purpose",
                                  "Add those back for a finished home "
                                  "and the price gap shrinks a lot",
                                  "That's a different argument in this "
                                  "same ten-part series — watch it "
                                  "before you quote this number for a "
                                  "finished house"),
                         position="right"),
                     narration=(
                         "One honest caveat before the close: this "
                         "number is for a bare shell on purpose. Add "
                         "back a kitchen, a bathroom, and mechanical "
                         "systems for a finished home, and this "
                         "percentage shrinks a lot — that's a separate "
                         "argument in this same series, and it's worth "
                         "watching before you quote this number for a "
                         "finished house.",
                         "For storage, a workshop, or anything that "
                         "sells bare enclosed volume, though, this "
                         "number is the real one.",
                     )),
            ),
        ),
    )
    return Presentation(
        title="The Bare-Shell Number",
        author="DomeSim Presenter Studio",
        scenes=scenes,
    )
