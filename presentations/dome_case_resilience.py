"""Argument 7 of 10: what the shape earns you (structural resilience).

The hedged wind/seismic case, why it matters financially (insurance
premiums, not just survival), and an explicit list of the resilience
claims this project refuses to make — the discipline that makes the
smaller, real claim believable.
"""

from __future__ import annotations

from presenter.script import OverlayPanel, Presentation, Scene, Shot
from presentations._numbers import R

STORM = "storm clouds over the open field"
FIELD = "a calm open field in daylight"
WORLD = (("dome", {"radius": R, "skin_alpha": 0.16}),)


def build() -> Presentation:
    scenes = (
        Scene(
            "hook", "Resilience is a financial argument, not just a "
                   "survival one",
            STORM,
            world=WORLD,
            shots=(
                Shot("thesis", 9.0, lens="wide", perspective=4,
                     focus="dome", yaw=-60, pitch=26, orbit=10,
                     caption="U.S. GAO: insurance premiums run about "
                             "58% higher in high-wind-risk areas",
                     panel=OverlayPanel(
                         title="WHY THIS ARGUMENT MATTERS",
                         stats=(("U.S. GAO, 2026",
                                 "Insurance premiums ~58% higher in "
                                 "high-wind-risk areas"),),
                         bullets=("Resilience isn't just about "
                                  "surviving a storm",
                                  "It's about what an insurer and an "
                                  "appraiser charge before the storm "
                                  "ever arrives"),
                         position="right"),
                     narration=(
                         "Resilience is not only about surviving a "
                         "storm. The U.S. Government Accountability "
                         "Office finds insurance premiums run roughly "
                         "fifty eight percent higher in high wind risk "
                         "areas — a cost that shows up every year, "
                         "storm or no storm.",
                         "That is the financial version of this "
                         "argument, and it's the one that actually "
                         "matters to a buyer's monthly payment.",
                     )),
            ),
        ),
        Scene(
            "the_mechanics", "What the geometry actually does",
            STORM,
            world=WORLD,
            shots=(
                Shot("wind", 9.0, lens="wide", perspective=4,
                     focus="dome", yaw=40, pitch=24, orbit=8,
                     caption="No single flat face for wind to "
                             "concentrate on",
                     panel=OverlayPanel(
                         title="WIND",
                         bullets=("A curved, continuous shell has no "
                                  "single flat wall for pressure to "
                                  "concentrate on",
                                  "Wind moving around a dome sheds more "
                                  "evenly than around sharp corners",
                                  "A real aerodynamic property — not a "
                                  "claim about outcomes in any "
                                  "specific storm"),
                         position="left"),
                     narration=(
                         "A curved, continuous shell has no single "
                         "flat wall for wind pressure to concentrate "
                         "on the way it does against a box's corners. "
                         "Air sheds around the curve more evenly.",
                         "That is a real aerodynamic property of the "
                         "shape. It is not a claim about what happens "
                         "in any specific storm.",
                     )),
                Shot("seismic", 9.0, lens="wide", focus="dome",
                     yaw=-150, pitch=18, orbit=8,
                     caption="Load spreads through a triangulated "
                             "lattice, not into a handful of studs",
                     panel=OverlayPanel(
                         title="SEISMIC",
                         bullets=("Sixty five struts share load "
                                  "through many redundant paths",
                                  "A stud wall concentrates load into "
                                  "far fewer members",
                                  "More paths for load to travel is a "
                                  "structural property, not a survival "
                                  "guarantee"),
                         position="right"),
                     narration=(
                         "The same is true for lateral load moving "
                         "through the frame. Sixty five struts share "
                         "the work through many redundant paths, where "
                         "a conventional stud wall concentrates the "
                         "same load into far fewer members.",
                         "More paths for load to travel through is a "
                         "structural property. It is still not a "
                         "survival guarantee for any specific event.",
                     )),
            ),
        ),
        Scene(
            "the_myths", "What this project will not say about any of "
                        "it",
            FIELD,
            world=WORLD,
            shots=(
                Shot("claims", 10.5, lens="wide", focus="dome",
                     yaw=0, pitch=14, orbit=8,
                     caption="Four specific claims this project "
                             "refuses to make about resilience",
                     panel=OverlayPanel(
                         title="CLAIMS THIS PROJECT WILL NOT MAKE",
                         bullets=(
                             "“A dome is disaster-proof.”",
                             "“All wind pushes a dome downward.”",
                             "“A dome cannot be lifted.”",
                             "“The structure automatically qualifies "
                             "for insurance.”"),
                         position="bottom"),
                     narration=(
                         "A dome is not disaster proof. Not all wind "
                         "pushes a dome downward — under the wrong "
                         "conditions a roof shape can still generate "
                         "uplift. A dome can absolutely be lifted if "
                         "the engineering doesn't account for that.",
                         "And the structure does not automatically "
                         "qualify for insurance just because it's a "
                         "dome. Every one of those is a real claim "
                         "someone could make about this shape, and "
                         "every one of them is false.",
                     )),
                Shot("real_path", 9.0, lens="portrait", focus="dome",
                     yaw=-80, pitch=16, orbit=6,
                     caption="The real path to lower insurance: an "
                             "engineer-stamped design, not a hopeful "
                             "adjective",
                     panel=OverlayPanel(
                         title="WHAT ACTUALLY LOWERS THE PREMIUM",
                         bullets=("An engineer-stamped design for the "
                                  "actual hazard package at the site",
                                  "FEMA: code adoption measurably "
                                  "reduces disaster losses — sold as a "
                                  "tested code-above system, not an "
                                  "exception to code",
                                  "Insurers price engineering, not "
                                  "shape alone"),
                         position="right"),
                     narration=(
                         "FEMA's own research finds that code adoption "
                         "measurably reduces disaster losses — which "
                         "means the path to a lower premium runs "
                         "through an engineer-stamped design for the "
                         "actual hazard package at the site, sold as a "
                         "tested code-above system, not an exception "
                         "to code.",
                         "Insurers price engineering. They don't price "
                         "an adjective.",
                     )),
            ),
        ),
        Scene(
            "close", "The honest version of a strong argument",
            "the same open field at dusk",
            world=WORLD,
            shots=(
                Shot("close_shot", 9.5, lens="ultrawide", perspective=6,
                     focus="dome", yaw=-90, pitch=22,
                     caption="Genuinely different structural "
                             "properties — sold as exactly that, and "
                             "nothing more",
                     panel=OverlayPanel(
                         title="WHAT THE SHAPE ACTUALLY EARNS YOU",
                         bullets=("Real aerodynamic and load-path "
                                  "advantages, honestly described",
                                  "A real, GAO-documented cost for "
                                  "getting resilience wrong",
                                  "Part of a ten-part case for 2V "
                                  "geodesic domes in the housing "
                                  "market"),
                         position="bottom"),
                     narration=(
                         "The shape genuinely does earn structural "
                         "advantages — real load paths, real "
                         "aerodynamics. Sold as exactly that, with the "
                         "specific overclaims named and refused, this "
                         "is the version of the resilience argument "
                         "that survives contact with an underwriter.",
                         "This is one part of a ten part case for 2V "
                         "geodesic domes in the housing market.",
                     )),
            ),
        ),
    )
    return Presentation(
        title="What the Shape Earns You",
        author="DomeSim Presenter Studio",
        scenes=scenes,
    )
