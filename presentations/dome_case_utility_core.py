"""Argument 9 of 10: the curved-wall answer (the utility core).

The single most common objection to a curved-wall house — where do the
straight-line things go — and this project's specific answer, plus the
rest of presentation.txt's "what must be solved" table: leaks, fire,
code and insurance unfamiliarity. Solved with details and paperwork,
not with the shape.
"""

from __future__ import annotations

from presenter.script import OverlayPanel, Presentation, Scene, Shot
from presentations._numbers import R

FIELD = "a calm open field in daylight"
WORLD = (("dome", {"radius": R, "skin_alpha": 0.10}),
        ("utility_column", {"radius": R, "reveal": 1.0}),
        ("hatch", {"radius": R, "az_deg": 35.0, "polar_deg": 60.0,
                  "open": 0.0}))


def build() -> Presentation:
    scenes = (
        Scene(
            "hook", "The objection that comes up first, every time",
            FIELD,
            world=WORLD,
            shots=(
                Shot("objection", 9.0, lens="wide", focus="dome",
                     yaw=-50, pitch=16, orbit=8,
                     caption="\"Where does the plumbing go in a "
                             "round room?\"",
                     panel=OverlayPanel(
                         title="THE OBJECTION",
                         bullets=("Cabinets, plumbing runs, and large "
                                  "windows all want straight lines and "
                                  "flat planes",
                                  "A dome has to earn the right to "
                                  "ignore that, not assume it away",
                                  "This is the objection that ends "
                                  "most curved-wall pitches before the "
                                  "numbers even come up"),
                         position="right"),
                     narration=(
                         "Before cost, before resilience, this is the "
                         "objection that actually stops most curved-"
                         "wall pitches: cabinets, plumbing runs, and "
                         "large windows all want straight lines and "
                         "flat planes. A dome has to earn the right to "
                         "ignore that, not assume it away.",
                     )),
            ),
        ),
        Scene(
            "the_core", "Concentrate the straight lines in one place",
            FIELD,
            world=WORLD,
            shots=(
                Shot("column", 9.5, lens="wide", focus="utility_column",
                     yaw=-45, pitch=16, orbit=8,
                     actions=(("utility_column", "reveal", 0.0, 1.0),),
                     caption="One straight core, floor to apex, "
                             "carrying water and power",
                     panel=OverlayPanel(
                         title="THIS PROJECT'S ANSWER",
                         bullets=("A utility column runs floor to "
                                  "apex, carrying water on one side "
                                  "and power on the other",
                                  "Kitchen and bath cabinetry mount "
                                  "against it, not against the curved "
                                  "shell",
                                  "Other designs use a rectangular "
                                  "utility core against one wall — "
                                  "different shape, same principle"),
                         position="left"),
                     narration=(
                         "The answer is not to fight the curve "
                         "everywhere. It's to concentrate the straight "
                         "lines into one place: a utility column "
                         "running floor to apex, carrying water on one "
                         "side and power on the other.",
                         "Kitchen and bath cabinetry mounts against "
                         "that column, not against the curved shell. "
                         "Other designs solve the same problem with a "
                         "rectangular utility core built against one "
                         "wall — different shape, identical principle.",
                     )),
                Shot("windows", 8.5, lens="portrait", focus="dome",
                     yaw=90, pitch=18, orbit=6,
                     caption="Standardized triangular openings, not "
                             "one-off curved glass",
                     panel=OverlayPanel(
                         title="THE SAME PRINCIPLE, FOR WINDOWS",
                         bullets=("Large custom windows are solved the "
                                  "same way — standardize the opening "
                                  "shape",
                                  "Triangular panels swap for glazed "
                                  "triangular panels, no one-off "
                                  "curved glass required"),
                         position="right"),
                     narration=(
                         "Large custom windows get the identical "
                         "treatment: standardize the opening instead "
                         "of custom-cutting curved glass. A glazed "
                         "triangular panel swaps in for a structural "
                         "one, using the same forty-panel geometry "
                         "already on the shell.",
                     )),
            ),
        ),
        Scene(
            "the_rest_of_the_list", "The rest of the list solves the "
                                   "same way",
            FIELD,
            world=WORLD,
            shots=(
                Shot("hatch_leaks", 9.0, lens="macro", focus="hatch",
                     yaw=-15, pitch=12, orbit=6,
                     actions=(("hatch", "open", 0.0, 1.0),),
                     caption="Leaks: gasketed joints and testing, not "
                             "an assumption about the shape",
                     panel=OverlayPanel(
                         title="LEAKS",
                         bullets=("Solved with a gasketed, tested "
                                  "detail at every penetration",
                                  "This hatch is exactly that detail: "
                                  "raised coaming, locking wheel, "
                                  "gasket",
                                  "Not an assumption that curved "
                                  "surfaces shed water better on "
                                  "their own"),
                         position="right"),
                     narration=(
                         "Leaks get solved the way this hatch solves "
                         "them: a raised coaming, a locking wheel, a "
                         "gasket, tested — not an assumption that a "
                         "curved surface sheds water better on its "
                         "own.",
                     )),
                Shot("fire_code", 9.0, lens="wide", focus="dome",
                     yaw=140, pitch=16, orbit=8,
                     caption="Fire, code, and insurance unfamiliarity: "
                             "paperwork and materials, not the shape",
                     panel=OverlayPanel(
                         title="FIRE, CODE, INSURANCE",
                         bullets=("Fire rating: noncombustible "
                                  "cladding, same as any code-"
                                  "compliant structure",
                                  "Code and appraisal unfamiliarity: "
                                  "pre-approved plans, engineer-"
                                  "stamped design",
                                  "Insurance: lenders and appraisers "
                                  "lined up before the first sale, "
                                  "not after"),
                         position="left"),
                     narration=(
                         "Fire rating comes from noncombustible "
                         "cladding, the same as any code compliant "
                         "building. Code and appraisal unfamiliarity "
                         "get solved with pre-approved plans and an "
                         "engineer-stamped design, arranged before the "
                         "first sale rather than argued about during "
                         "it.",
                     )),
            ),
        ),
        Scene(
            "close", "Every hard objection has a detail, not a hope",
            "a calm open field at dusk",
            world=WORLD,
            shots=(
                Shot("close_shot", 10.0, lens="ultrawide", perspective=6,
                     focus="dome", yaw=-90, pitch=22,
                     caption="One core, one hatch detail, one "
                             "paperwork checklist — that's the whole "
                             "answer",
                     panel=OverlayPanel(
                         title="WHAT MUST BE SOLVED — SOLVED",
                         bullets=("Curved cabinetry and plumbing → a "
                                  "utility core",
                                  "Custom windows → standardized "
                                  "triangular openings",
                                  "Leaks, fire, code, insurance → "
                                  "details and paperwork, arranged in "
                                  "advance",
                                  "Part of a ten-part case for 2V "
                                  "geodesic domes in the housing "
                                  "market"),
                         position="bottom"),
                     narration=(
                         "Every objection on this list gets a specific "
                         "detail, not a hope that the shape makes the "
                         "problem disappear. That discipline — a real "
                         "answer for every real objection — is what "
                         "makes the rest of this case worth believing.",
                         "This is one part of a ten part case for 2V "
                         "geodesic domes in the housing market.",
                     )),
            ),
        ),
    )
    return Presentation(
        title="The Curved-Wall Answer",
        author="DomeSim Presenter Studio",
        scenes=scenes,
    )
