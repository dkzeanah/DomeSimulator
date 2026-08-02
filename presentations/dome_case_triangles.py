"""Argument 4 of 10: why triangles don't rack (structural rigidity).

The geometric reason 40 of a 2V dome's panels are triangles and not
squares or hexagons, built entirely from first-principles mechanics —
no material assumptions, no cost model, just why the shape holds itself
up. Closes by tying it back to the dome's own real geometry.
"""

from __future__ import annotations

from presenter.script import OverlayPanel, Presentation, Scene, Shot
from presentations._numbers import GEO, LONG, R, SHORT, TRI_EQU, TRI_ISO

FIELD = "a calm open field in daylight"
DIAGRAM = ("triangle_vs_square", {"size": 2.2, "gap": 3.6, "cx": 0.0,
                                  "cy": 0.0, "strut": 0.06})


def build() -> Presentation:
    scenes = (
        Scene(
            "hook", "Why triangles, and not squares or hexagons",
            FIELD,
            world=(DIAGRAM,),
            shots=(
                Shot("question", 9.0, lens="wide", focus="rigidity_pair",
                     yaw=-25, pitch=14, orbit=8,
                     caption="Every geodesic dome panel is a triangle. "
                             "That's not an aesthetic choice.",
                     panel=OverlayPanel(
                         title="THE QUESTION",
                         bullets=("Squares tile a wall. Hexagons tile a "
                                  "honeycomb. Why does a dome insist on "
                                  "triangles?",
                                  "The answer is mechanical, not "
                                  "decorative",
                                  "It comes down to one property: what "
                                  "happens when you push a shape "
                                  "sideways"),
                         position="right"),
                     narration=(
                         "Squares tile a wall just fine. Hexagons tile "
                         "a honeycomb. So why does every geodesic dome "
                         "insist on triangles for its skin? Not for "
                         "looks — the answer is entirely mechanical.",
                         "It comes down to one property: what happens "
                         "when you push a shape sideways, not down.",
                     )),
            ),
        ),
        Scene(
            "the_problem", "A square has a hinge it doesn't know about",
            FIELD,
            world=(DIAGRAM,),
            shots=(
                Shot("racks", 9.0, lens="wide", focus="rigidity_pair",
                     yaw=-15, pitch=13, orbit=6,
                     actions=(("triangle_vs_square", "shear", 0.0, 1.0),),
                     caption="Four hinged corners means four degrees of "
                             "freedom the frame doesn't want",
                     panel=OverlayPanel(
                         title="THE PROBLEM WITH FOUR CORNERS",
                         bullets=("A square's four corners can each "
                                  "rotate independently",
                                  "Push sideways and the whole frame "
                                  "leans into a parallelogram",
                                  "The side lengths never changed — "
                                  "only the angles did"),
                         position="left"),
                     narration=(
                         "A square built from four rigid members and "
                         "four pinned corners is not actually rigid. "
                         "Push sideways and it leans into a "
                         "parallelogram — every side length stays "
                         "exactly the same, only the corner angles "
                         "change.",
                         "That's the hinge a square doesn't know it "
                         "has. Four corners, four independent angles, "
                         "and nothing in the geometry stops any of "
                         "them from moving.",
                     )),
                Shot("why_math", 8.5, lens="portrait",
                     focus="rigidity_square",
                     yaw=10, pitch=10, orbit=5,
                     caption="Four sides fix four lengths — but a "
                             "quadrilateral needs five numbers to pin "
                             "its shape down",
                     panel=OverlayPanel(
                         title="THE COUNTING ARGUMENT",
                         equations=("4 side lengths fix 4 numbers",
                                    "A quadrilateral's shape needs 5",
                                    "1 missing constraint = 1 degree "
                                    "of freedom left over"),
                         position="right"),
                     narration=(
                         "Here's the count that explains it. Four side "
                         "lengths pin down four numbers. But a "
                         "quadrilateral's shape needs five numbers "
                         "fully specified before it's locked. One "
                         "constraint short means one degree of freedom "
                         "left over — and that's exactly the racking "
                         "motion.",
                     )),
            ),
        ),
        Scene(
            "the_fix", "One diagonal changes the count",
            FIELD,
            world=(DIAGRAM,),
            shots=(
                Shot("brace", 9.0, lens="wide", focus="rigidity_pair",
                     yaw=-15, pitch=13, orbit=4,
                     actions=(("triangle_vs_square", "shear", 1.0, 1.0),
                              ("triangle_vs_square", "braced", 0.0, 1.0)),
                     caption="Add the fifth length — the racking has "
                             "nowhere left to go",
                     panel=OverlayPanel(
                         title="THE FIX",
                         bullets=("One diagonal adds exactly the fifth "
                                  "length the count was missing",
                                  "The square becomes two triangles "
                                  "sharing an edge",
                                  "Zero degrees of freedom left — the "
                                  "shape is fully determined"),
                         position="right"),
                     narration=(
                         "Add one diagonal member and the count "
                         "balances: five lengths for five numbers. The "
                         "square is now two triangles sharing an edge, "
                         "and there is no leftover freedom for the "
                         "shape to rack into.",
                         "That diagonal didn't reinforce the square. It "
                         "replaced it with something structurally "
                         "different.",
                     )),
                Shot("triangle_locked", 8.0, lens="macro",
                     focus="rigidity_triangle", yaw=20, pitch=12, orbit=5,
                     caption="A triangle starts fully determined — "
                             "three lengths, three numbers, exactly",
                     panel=OverlayPanel(
                         title="WHY A TRIANGLE NEVER NEEDED THE FIX",
                         equations=("3 side lengths fix 3 numbers",
                                    "A triangle's shape needs exactly 3",
                                    "0 degrees of freedom — it was "
                                    "never able to rack"),
                         position="left"),
                     narration=(
                         "A triangle never had the problem in the "
                         "first place. Three side lengths, three "
                         "numbers needed, an exact match. There was "
                         "never a spare degree of freedom for it to "
                         "move into.",
                     )),
            ),
        ),
        Scene(
            "the_dome", "Forty of them, curving in every direction",
            FIELD,
            world=(("dome", {"radius": R, "skin_alpha": 0.18}),),
            shots=(
                Shot("real_shell", 9.5, lens="wide", focus="dome",
                     yaw=-60, pitch=18, orbit=10,
                     caption="A 2V dome's skin is 40 triangles — "
                             "already braced, in every direction",
                     panel=OverlayPanel(
                         title="THE REAL GEOMETRY",
                         stats=(("Triangular panels",
                                 f"{len(GEO.hemisphere_faces)} "
                                 f"({TRI_ISO.hemisphere_count} + "
                                 f"{TRI_EQU.hemisphere_count})"),
                                ("Struts",
                                 f"{len(GEO.hemisphere_edges)} "
                                 f"({SHORT.hemisphere_count} short, "
                                 f"{LONG.hemisphere_count} long)")),
                         bullets=("Not bracing added to a spherical "
                                  "building",
                                  "Triangulation is the building"),
                         position="right"),
                     narration=(
                         "A two V dome's skin is forty of those "
                         "triangles, in two sizes, curving in every "
                         "direction at once. It isn't bracing bolted "
                         "onto a spherical building after the fact.",
                         "Triangulation is the building. Every panel "
                         "already has its fifth length, so there is "
                         "nowhere in the whole shell for a racking "
                         "motion to hide.",
                     )),
                Shot("close_shot", 8.5, lens="portrait", focus="apex",
                     yaw=30, pitch=26, orbit=6,
                     caption="One mechanical fact, forty times, in a "
                             "curved shell",
                     panel=OverlayPanel(
                         title="THE ARGUMENT, IN ONE LINE",
                         bullets=("A triangle can't rack — a fact of "
                                  "counting, not material",
                                  "A dome is nothing but triangles",
                                  "Part of a ten-part case for 2V "
                                  "geodesic domes in the housing "
                                  "market"),
                         position="left"),
                     narration=(
                         "One mechanical fact — a triangle can't rack "
                         "— applied forty times, curved into a shell. "
                         "That is the entire structural argument, and "
                         "it doesn't depend on what the struts are "
                         "made of.",
                         "This is one part of a ten part case for 2V "
                         "geodesic domes in the housing market.",
                     )),
            ),
        ),
    )
    return Presentation(
        title="Why Triangles Don't Rack",
        author="DomeSim Presenter Studio",
        scenes=scenes,
    )
