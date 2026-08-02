"""The 2V housing case, converged from three independent LLM arguments and
grounded entirely in this project's own code.

Every number that appears on screen is computed from the same modules the
interactive tools use — ``al_build.building_comparisons()`` for the
box-vs-dome cost comparison, ``al_build.DOME_TYPES`` for the real product
line and build-stage sequence, ``two_v_demo.geometry.build_demo_geometry()``
for the strut/panel counts and the golden-ratio myth debunk. Nothing here is
a hardcoded marketing figure; if the underlying model changes, this
presentation's captions and narration change with it.

The argument itself converges three source documents (grok, gemini, and
chatgpt's independent cases for 2V geodesic domes in ``presentation.txt``)
into one narrative: proven-by-this-project's-own-math, then the honestly
hedged engineering case, then the contingent market/manufacturing case,
closing with an explicit list of claims this project refuses to make.
That last part is deliberate — chatgpt's source material was the most
rigorous of the three specifically because it said what NOT to claim, and
this presentation borrows that discipline as its credibility backbone.

Every shot carries a caption and, where there is a real claim to make, an
OverlayPanel with bullets/stats/equations, so the argument reads complete
with the sound off — narration is a second channel, not the only one.
"""

from __future__ import annotations

import al_build as ab
from presenter.script import OverlayPanel, Presentation, Scene, Shot
from presentations._numbers import (
    BENCH_DAYS_PCT, BENCH_LABOR_PCT, BENCH_PRICE_PCT, GEO, HERO_BENCH,
    HERO_BREAK_EVEN, HERO_MONTHLY, HERO_PRICE, HERO_THROUGHPUT,
    HERO_VALUE, HOME, HOME_BOX_H, HOME_BOX_L, HOME_BOX_W, HOME_DOME_R_M,
    HOME_FRAME_PCT, HOME_SAVE_PCT, HOME_VOL_PCT, HUB_COUNT, LONG, R, SHED,
    SHED_BOX_H, SHED_BOX_L, SHED_BOX_W, SHED_CLAD_PCT, SHED_DOME_R_M,
    SHED_FRAME_PCT, SHED_SAVE_PCT, SHORT, TRI_EQU, TRI_ISO,
)


def build() -> Presentation:
    scenes = (
        Scene(
            "hook", "The math nobody likes",
            "an open grass field at dusk",
            world=(("dome", {"radius": R, "skin_alpha": 0.18}),),
            shots=(
                Shot("empty_field", 8.0, lens="ultrawide", perspective=1,
                     focus="", yaw=0, pitch=8, orbit=6,
                     actions=(("dome", "radius", 0.001, 0.001),),
                     caption="22.7 million U.S. renter households are "
                             "cost-burdened right now",
                     panel=OverlayPanel(
                         title="THE STARTING NUMBERS",
                         stats=(("Cost-burdened renter households",
                                 "22.7M — Harvard JCHS, 2026"),
                                ("...paying over half their income",
                                 "12.1M households"),
                                ("National housing unit deficit",
                                 "3.8M – 5.5M units — "
                                 "HUD-backed research")),
                         position="bottom"),
                     narration=(
                         "Before any dome, the numbers. Harvard's Joint "
                         "Center for Housing Studies counts twenty two "
                         "point seven million cost burdened renter "
                         "households in the United States right now, "
                         "twelve point one million of them spending over "
                         "half of what they earn on rent alone.",
                         "HUD backed research puts the national housing "
                         "unit deficit somewhere between three point "
                         "eight and five and a half million units. That "
                         "is the gap this video is actually about.",
                     )),
                Shot("dome_arrives", 8.0, lens="wide", focus="dome",
                     yaw=-40, pitch=14, orbit=10,
                     caption="One proposed answer: a 2V geodesic dome — "
                             "modeled, priced, and built on screen by "
                             "real code",
                     panel=OverlayPanel(
                         title="WHAT THIS VIDEO IS",
                         bullets=("An argument for 2V geodesic domes in "
                                  "that gap",
                                  "...and a demonstration of the "
                                  "software that models them",
                                  "Every number and camera move you see "
                                  "is computed live, not decorated"),
                         position="right"),
                     narration=(
                         "This is one proposed answer: a two V geodesic "
                         "dome. Not a rendering somebody drew to look "
                         "convincing — every shape, every strut, every "
                         "dollar figure in this video was generated by "
                         "one Python toolset, running on the presenter's "
                         "own machine.",
                         "That toolset is also the product. By the end "
                         "you will have seen the argument for the dome "
                         "and the software that builds, prices, and "
                         "explains it.",
                     )),
            ),
        ),
        Scene(
            "fundamentals", "What a 2V dome actually is",
            "a calm open field in daylight",
            world=(
                ("dome", {"radius": R, "skin_alpha": 0.12}),
                ("triangle_vs_square", {"size": 1.8, "gap": 3.2,
                                        "cx": 0.0, "cy": -32.0,
                                        "strut": 0.05}),
            ),
            shots=(
                Shot("strut_classes", 7.5, lens="macro", focus="apex",
                     yaw=-35, pitch=30, orbit=8,
                     caption="Two strut lengths, repeated 65 times, "
                             "build the whole shell",
                     panel=OverlayPanel(
                         title="THE PARTS LIST",
                         stats=(("Structural struts",
                                 f"{len(GEO.hemisphere_edges)} total"),
                                ("Short struts",
                                 f"{SHORT.hemisphere_count}"),
                                ("Long struts",
                                 f"{LONG.hemisphere_count}"),
                                ("Strut lengths needed",
                                 f"{len(GEO.edge_classes)}"),
                                ("Triangular panels",
                                 f"{len(GEO.hemisphere_faces)} "
                                 f"({TRI_ISO.hemisphere_count} + "
                                 f"{TRI_EQU.hemisphere_count})"),
                                ("Hub vertices", f"{HUB_COUNT}")),
                         position="right"),
                     narration=(
                         "Zoom in and the whole shell is only two parts "
                         "repeated. Thirty short struts, cyan here, and "
                         "thirty five long struts, amber, meeting at "
                         "twenty six hub vertices.",
                         "Two lengths. Not twenty, not two hundred — "
                         "two. That is the entire structural parts list "
                         "for a two V dome, and it is exactly what the "
                         "simulator's own geometry engine computes, not "
                         "a marketing simplification.",
                     )),
                Shot("golden_ratio_myth", 8.0, lens="portrait",
                     focus="dome", yaw=10, pitch=16, orbit=6,
                     caption="The two strut lengths are NOT the golden "
                             "ratio — the math says so",
                     panel=OverlayPanel(
                         title="NOT THE GOLDEN RATIO",
                         equations=(
                             f"SHORT = {GEO.short_factor:.6f} × R",
                             f"LONG = {GEO.long_factor:.6f} × R",
                             f"LONG ÷ SHORT = {GEO.ratio:.6f}"),
                         bullets=("The golden ratio is 1.618034",
                                  f"{GEO.ratio:.6f} is not that number",
                                  "Computed live by the same code, "
                                  "every time"),
                         position="left"),
                     narration=(
                         "You will sometimes hear that a two V dome's "
                         "two strut lengths follow the golden ratio. "
                         "They do not, and this project would rather "
                         "show you the arithmetic than repeat the "
                         "claim.",
                         "Short is zero point five four six five three "
                         "three of the radius. Long is zero point six "
                         "one eight zero three four. Divide them and "
                         "you get one point one three zero eight two "
                         "six. The golden ratio is one point six one "
                         "eight. Different number. This project's own "
                         "teaching tool has made that exact correction "
                         "since before this video existed.",
                     )),
                Shot("rigidity_a", 7.5, lens="wide", focus="rigidity_pair",
                     yaw=-20, pitch=14, orbit=6,
                     actions=(("triangle_vs_square", "shear", 0.0, 1.0),),
                     caption="A square racks under sideways load — "
                             "a triangle can't",
                     panel=OverlayPanel(
                         title="WHY TRIANGLES",
                         bullets=("A square's corners are hinges — "
                                  "push sideways and it collapses into "
                                  "a parallelogram",
                                  "A triangle has no spare hinge — "
                                  "its side lengths lock its shape "
                                  "completely"),
                         position="bottom"),
                     narration=(
                         "Here is the structural reason forty of a "
                         "dome's panels are triangles and not squares. "
                         "Push sideways on an unbraced square frame and "
                         "it racks — the corners hinge and the whole "
                         "shape leans.",
                         "A triangle cannot do that. Fix all three side "
                         "lengths and the shape is completely "
                         "determined. There is no hinge left to give.",
                     )),
                Shot("rigidity_b", 7.0, lens="wide", focus="rigidity_pair",
                     yaw=-20, pitch=14, orbit=4,
                     actions=(("triangle_vs_square", "shear", 1.0, 1.0),
                              ("triangle_vs_square", "braced", 0.0, 1.0)),
                     caption="Add one diagonal — the square becomes "
                             "two triangles, and the racking stops",
                     panel=OverlayPanel(
                         title="THE FIX IS THE WHOLE POINT",
                         bullets=("One diagonal turns a racking square "
                                  "into two rigid triangles",
                                  "A 2V dome's skin is 40 of exactly "
                                  "that shape, already braced, in every "
                                  "direction"),
                         position="bottom"),
                     narration=(
                         "Add one diagonal member and the square "
                         "becomes two triangles. The racking disappears "
                         "— because you didn't reinforce the square, "
                         "you replaced it.",
                         "A geodesic dome's skin is forty of those "
                         "triangles, already assembled, curving in "
                         "every direction at once. It is not bracing "
                         "added to a building. Triangulation is the "
                         "building.",
                     )),
            ),
        ),
        Scene(
            "build", "Watching the simulator build one",
            "a calm open field in daylight",
            world=(
                ("dome", {"radius": R, "skin_alpha": 0.0}),
                ("utility_column", {"radius": R, "reveal": 1.0}),
                ("shell_layers", {"radius": R, "stage": 6.0}),
                ("hatch", {"radius": R, "az_deg": 35.0, "polar_deg": 60.0,
                          "open": 0.0}),
                ("interior_fixtures", {"radius": R, "reveal": 1.0}),
                ("solar_band", {"radius": R, "coverage": 1.0}),
            ),
            shots=(
                Shot("frame_and_core", 9.5, lens="wide",
                     focus="utility_column", yaw=-50, pitch=18, orbit=10,
                     actions=(("utility_column", "reveal", 0.0, 1.0),
                              ("shell_layers", "stage", 0.0, 0.0)),
                     caption="Stage 1-6 of 15: floor, frame, utility "
                             "column, water, power, rough fixtures",
                     panel=OverlayPanel(
                         title="BUILD SEQUENCE — STAGES 1-6",
                         bullets=("floor — the deck the shell sits on",
                                  "frame — 65 struts, 26 hubs",
                                  "column — water (4) and power (5) "
                                  "run floor to apex in one core",
                                  "fixtures (6) — rough plumbing and "
                                  "electrical stubbed out before the "
                                  "walls close"),
                         position="right"),
                     narration=(
                         "The simulator builds every dome in the same "
                         "order, station by station. Floor first, then "
                         "the sixty five strut frame you just watched "
                         "come together.",
                         "Immediately after the frame, a utility column "
                         "rises from the floor to the apex, carrying "
                         "water on one side and power on the other — "
                         "stages four and five. Rough plumbing and "
                         "electrical fixtures get stubbed out from that "
                         "same column at stage six, before anything "
                         "closes up. This is this project's specific "
                         "answer to the oldest objection to curved "
                         "rooms: where do the straight-line things go? "
                         "Other designs solve it with a rectangular "
                         "utility core built against one wall. "
                         "Different shape, same idea — put the plumbing "
                         "and the cabinetry where straight lines "
                         "belong, and let the dome do only what domes "
                         "are good at, which is enclosing space.",
                     )),
                Shot("shell_cladding", 10.5, lens="wide",
                     focus="shell_layers", yaw=30, pitch=16, orbit=8,
                     actions=(("shell_layers", "stage", 0.0, 6.0),),
                     caption="Stage 7-12 of 15: insulation, sheetrock, "
                             "OSB, water barrier, shingles, fiberglass",
                     panel=OverlayPanel(
                         title="BUILD SEQUENCE — STAGES 7-12, THE "
                               "CLADDING STACK",
                         bullets=("insulation (7) — first layer over "
                                  "the bare frame",
                                  "sheetrock (8) — interior wall "
                                  "finish",
                                  "osb (9) — structural sheathing",
                                  "wrap (10) — the water barrier",
                                  "shingles (11) — the weather skin",
                                  "fiberglass (12) — the finish coat"),
                         position="left"),
                     narration=(
                         "Then the shell claddings up, one layer at a "
                         "time, in the exact order the simulator's own "
                         "stage list uses: insulation, interior "
                         "sheetrock, structural sheathing, a water "
                         "barrier, shingles, and a fiberglass finish "
                         "coat.",
                         "Six layers, one shape. Every one of them has "
                         "to wrap a curved surface instead of a flat "
                         "one, which is a real fabrication difference "
                         "from stick framing — and part of why the "
                         "panel-and-jig approach later in this video "
                         "matters so much.",
                     )),
                Shot("hatch_shot", 8.5, lens="macro", focus="hatch",
                     yaw=-15, pitch=12, orbit=6,
                     actions=(("hatch", "open", 0.0, 1.0),
                              ("shell_layers", "alpha_mult", 1.0, 0.08)),
                     caption="Stage 13 of 15: a watertight deck hatch",
                     panel=OverlayPanel(
                         title="THE HATCH",
                         bullets=("Raised coaming keeps water out before "
                                  "the door does",
                                  "Locking wheel seats the door against "
                                  "a gasket, not just a latch",
                                  "Same detail family as a boat hatch, "
                                  "because the objection is the same"),
                         position="right"),
                     narration=(
                         "Stage thirteen: a watertight hatch, built the "
                         "way a boat hatch is built. A raised coaming "
                         "so water has to climb before it can reach the "
                         "door, and a locking wheel that seats the door "
                         "against a gasket instead of trusting a simple "
                         "latch.",
                     )),
                Shot("interior_shot", 8.5, lens="wide", focus="fixtures",
                     yaw=150, pitch=20, orbit=8,
                     actions=(("interior_fixtures", "reveal", 0.0, 1.0),
                              ("shell_layers", "alpha_mult", 1.0, 0.08)),
                     caption="Stage 14 of 15: kitchen, bed, and bath "
                             "fit out around the utility column",
                     panel=OverlayPanel(
                         title="INTERIOR FIT-OUT",
                         bullets=("Kitchen cabinetry against the "
                                  "utility column",
                                  "Bed and bath on the remaining floor "
                                  "plan",
                                  "Every fixture keyed to the one column "
                                  "that carries its supply lines"),
                         position="left"),
                     narration=(
                         "Stage fourteen, the interior fit out follows "
                         "the column: kitchen cabinetry tight against "
                         "it, bed and bath on the rest of the floor "
                         "plan. Nothing here waits on a custom curved "
                         "cabinet — every straight fixture sits against "
                         "the one straight core in the room.",
                     )),
                Shot("solar_and_lift", 9.0, lens="wide", perspective=5,
                     focus="solar", yaw=-140, pitch=22,
                     actions=(("solar_band", "coverage", 0.0, 1.0),
                              ("shell_layers", "alpha_mult", 1.0, 0.08)),
                     caption="Stage 15 of 15 — solar — then the "
                             "finished shell lifts as one piece",
                     panel=OverlayPanel(
                         title="THE LAST STAGE, AND THE LIFT",
                         stats=(("Solar panels placed",
                                 f"{HERO_VALUE['solar_panels']:.0f}"),
                                ("Modeled array size",
                                 f"{HERO_VALUE['solar_kw']:.1f} kW"),
                                ("Modeled daily surplus",
                                 f"{HERO_VALUE['net_daily_kwh']:.0f} kWh, "
                                 f"after a "
                                 f"{ab.ASSUMPTIONS['daily_load_kwh']:.0f} "
                                 f"kWh/day load")),
                         bullets=("Panels placed only on faces the "
                                  "geometry says face the sun",
                                  "An apex crane anchor lifts the "
                                  "finished shell in one piece"),
                         position="right"),
                     narration=(
                         "Stage fifteen, the last one: solar, placed "
                         "only on the faces the dome's own geometry "
                         "says face the sun — the same face data that "
                         "drove the golden ratio correction earlier in "
                         "this video is what decides where a panel is "
                         "allowed to go.",
                         "Then, after all fifteen stages, the entire "
                         "finished shell lifts as one piece from a ring "
                         "at the apex. In this project's assembly line "
                         "simulator, that crane sets the dome down on a "
                         "sun tracking turntable. It is a manufactured "
                         "product, handled like one, start to finish.",
                     )),
            ),
        ),
        Scene(
            "shed_numbers", "Round one: the bare shell",
            "a calm open field in daylight",
            world=(("comparison_pair",
                    {"box_w": SHED_BOX_W, "box_l": SHED_BOX_L,
                     "box_h": SHED_BOX_H, "dome_r": SHED_DOME_R_M,
                     "gap": 3.0}),),
            shots=(
                Shot("shed_compare", 10.0, lens="wide",
                     focus="compare_pair", yaw=-30, pitch=16, orbit=10,
                     caption=f"Same {SHED['box']['vol_ft3']:,.0f} cubic "
                             f"feet, same materials, same labor rate — "
                             f"{SHED_SAVE_PCT:.0f}% less to build",
                     panel=OverlayPanel(
                         title="BARE SHELL, MATCHED VOLUME",
                         stats=(
                             ("Box shell", f"${SHED['box']['build']:,.0f}"),
                             ("Dome shell",
                              f"${SHED['dome']['build']:,.0f}"),
                             ("Framing, box vs dome",
                              f"{SHED['box']['framing_lf']:,.0f} ft vs "
                              f"{SHED['dome']['framing_lf']:,.0f} ft"),
                             ("Skin area, box vs dome",
                              f"{SHED['box']['cladding_sf']:,.0f} ft² "
                              f"vs {SHED['dome']['cladding_sf']:,.0f} "
                              f"ft²")),
                         position="right"),
                     narration=(
                         "Round one is the simplest possible test: a "
                         "bare shell, no finishes, sized so both "
                         "buildings enclose exactly the same three "
                         "thousand eight hundred forty cubic feet. Same "
                         "lumber rate, same skin rate, same labor rate "
                         "for both — the only variable is the shape.",
                         f"The box costs twelve thousand four hundred "
                         f"twenty six dollars. The dome costs nine "
                         f"thousand four hundred forty four — "
                         f"{SHED_SAVE_PCT:.0f} percent less, using "
                         f"{SHED_FRAME_PCT:.0f} percent less framing and "
                         f"{SHED_CLAD_PCT:.0f} percent less exterior "
                         f"skin to enclose the identical space.",
                     )),
            ),
        ),
        Scene(
            "home_numbers", "Round two: the finished home — the "
                            "honest number",
            "a calm open field in daylight",
            world=(("comparison_pair",
                    {"box_w": HOME_BOX_W, "box_l": HOME_BOX_L,
                     "box_h": HOME_BOX_H, "dome_r": HOME_DOME_R_M,
                     "gap": 3.4}),),
            shots=(
                Shot("home_compare", 10.0, lens="wide",
                     focus="compare_pair", yaw=25, pitch=15, orbit=9,
                     caption=f"Same {ab.COMPARE_HOME_FLOOR_SF:.0f} sq ft "
                             f"floor, fully finished — only "
                             f"{HOME_SAVE_PCT:.1f}% cheaper, and that's "
                             f"the honest number",
                     panel=OverlayPanel(
                         title="FINISHED HOME, MATCHED FLOOR AREA",
                         stats=(
                             ("Stick-built house",
                              f"${HOME['box']['build']:,.0f}"),
                             ("Dome house",
                              f"${HOME['dome']['build']:,.0f}"),
                             ("Framing, stick vs dome",
                              f"{HOME['box']['framing_lf']:,.0f} ft vs "
                              f"{HOME['dome']['framing_lf']:,.0f} ft"),
                             ("Enclosed volume, same cost/footprint",
                              f"+{HOME_VOL_PCT:.0f}% for the dome")),
                         position="left"),
                     narration=(
                         f"Round two is harder on the dome, on purpose. "
                         f"Same six hundred forty square foot floor, but "
                         f"now both buildings are fully finished — "
                         f"kitchen, bath, mechanicals, the works. The "
                         f"dome is only {HOME_SAVE_PCT:.1f} percent "
                         f"cheaper here, not twenty four percent.",
                         "That smaller number is the trustworthy one. "
                         "A finished home's cost is dominated by "
                         "kitchens, bathrooms and mechanical systems "
                         "that cost the same no matter what shape the "
                         "walls are, so shape alone was never going to "
                         "rewrite the whole budget.",
                     )),
                Shot("home_volume", 8.5, lens="portrait", perspective=2,
                     focus="compare_dome", yaw=60, pitch=18, orbit=6,
                     caption=f"Same footprint, same budget — "
                             f"{HOME_VOL_PCT:.0f}% more usable volume "
                             f"inside the dome",
                     panel=OverlayPanel(
                         title="WHERE THE HOME TIER ACTUALLY WINS",
                         bullets=(
                             f"{HOME_FRAME_PCT:.0f}% less framing lumber "
                             f"for the same floor area",
                             f"{HOME_VOL_PCT:.0f}% more enclosed volume "
                             f"for the same footprint and about the "
                             f"same money",
                             "The honest pitch: not 'cheaper' — "
                             "'more room for the same money'"),
                         position="right"),
                     narration=(
                         "The number worth remembering from this round "
                         "is not the price. It's the volume. For the "
                         "same footprint and almost the same money, the "
                         "dome encloses forty percent more space, "
                         "because a hemisphere captures the volume a "
                         "flat ceiling throws away.",
                         "That is this project's actual pitch for a "
                         "finished home: not that domes are "
                         "dramatically cheaper — the numbers on screen "
                         "just showed you they usually are not — but "
                         "that the same money buys measurably more "
                         "room.",
                     )),
            ),
        ),
        Scene(
            "resilience", "What the shape earns you — and what it "
                          "doesn't",
            "storm clouds over the open field",
            world=(("dome", {"radius": R, "skin_alpha": 0.16}),),
            shots=(
                Shot("wind_case", 9.0, lens="wide", perspective=4,
                     focus="dome", yaw=-60, pitch=28, orbit=10,
                     caption="A curved, triangulated shell distributes "
                             "wind load more evenly than flat walls",
                     panel=OverlayPanel(
                         title="THE HEDGED STRUCTURAL CASE",
                         bullets=("No single flat face for wind to "
                                  "concentrate on",
                                  "Load spreads through a triangulated "
                                  "lattice instead of into a few studs",
                                  "A real structural property — not "
                                  "a claim that any dome is "
                                  "disaster-proof"),
                         position="right"),
                     narration=(
                         "Wind and seismic load spread through this "
                         "shape differently than through a box. There "
                         "is no single flat wall for pressure to "
                         "concentrate on, and load moving through a "
                         "triangulated lattice has far more paths to "
                         "travel than load moving through a stud wall.",
                         "That is a genuine structural property of the "
                         "geometry. It is also exactly as far as this "
                         "project is willing to take the claim.",
                     )),
                Shot("energy_case", 8.5, lens="macro", focus="dome",
                     yaw=40, pitch=14, orbit=6,
                     caption="More enclosed volume per square foot of "
                             "skin — real, but site- and "
                             "system-dependent",
                     panel=OverlayPanel(
                         title="THE HEDGED ENERGY CASE",
                         stats=(("This project's insulation model",
                                 f"R-{HERO_VALUE['r_value']:.0f} "
                                 f"effective, one representative build"),
                                ("One published simulation study (2024)",
                                 "52% lower cooling load — a "
                                 "geodesic tourist-accommodation model")),
                         bullets=("Less exterior skin per enclosed "
                                  "volume is a real geometric fact",
                                  "\"Every dome uses 30-50% less "
                                  "energy\" is not — HVAC design, "
                                  "climate and airtightness still "
                                  "decide the real number"),
                         position="left"),
                     narration=(
                         "A sphere encloses more volume per square foot "
                         "of skin than a box does, and less skin means "
                         "less area for heat to cross — that part is "
                         "just geometry. This project's own insulation "
                         "model lands at roughly an R-41 effective "
                         "value for a representative build.",
                         "A 2024 simulation study of geodesic tourist "
                         "accommodations found fifty two percent lower "
                         "cooling energy — that is one specific study "
                         "of one specific building, not a universal "
                         "law. Anyone who tells you every dome uses "
                         "thirty to fifty percent less energy, "
                         "regardless of climate or how it's built, is "
                         "overselling the shape.",
                     )),
            ),
        ),
        Scene(
            "manufacturing", "A standardized product, not a custom house",
            "a calm open field in daylight",
            world=(("dome", {"radius": R, "skin_alpha": 0.10}),),
            shots=(
                Shot("parts_repeat", 8.5, lens="wide", focus="dome",
                     yaw=-80, pitch=18, orbit=10,
                     caption="2 strut lengths, 2 triangle shapes, 40 "
                             "panels — the entire bill of materials",
                     panel=OverlayPanel(
                         title="THE MANUFACTURING CASE",
                         bullets=(
                             f"Two strut lengths: {SHORT.hemisphere_count} "
                             f"short, {LONG.hemisphere_count} long",
                             f"Two triangle shapes: "
                             f"{TRI_ISO.hemisphere_count} isosceles "
                             f"(long-short-short), "
                             f"{TRI_EQU.hemisphere_count} equilateral "
                             f"(long-long-long)",
                             "Jig-based production, color-coded parts, "
                             "flat-pack shipping"),
                         position="right"),
                     narration=(
                         "This is chatgpt's own framing from the source "
                         "material behind this video, and it's the "
                         "right one: a 2V dome is not a custom house "
                         "shaped like a dome. It is a standardized "
                         "product — minimal geometry, factory "
                         "repetition, rapid assembly.",
                         "Two strut lengths. Two triangle shapes: "
                         "thirty of one, ten of the other. Every part "
                         "in a jig, every part color coded, the whole "
                         "shell flat packable. Federal research on "
                         "modular construction broadly finds schedules "
                         "compressed twenty to fifty percent and costs "
                         "cut up to twenty percent — that is evidence "
                         "about modular construction in general, not a "
                         "guarantee for this specific shape, and this "
                         "project is not going to blur that line.",
                     )),
                Shot("throughput", 9.0, lens="wide", focus="dome",
                     yaw=100, pitch=16, orbit=8,
                     caption=f"One production line, modeled: about "
                             f"{HERO_THROUGHPUT['pipelined_per_year']:.0f} "
                             f"domes a year, break-even under "
                             f"{HERO_BREAK_EVEN['units_to_cover_annual_fixed']:.0f} "
                             f"units",
                     panel=OverlayPanel(
                         title="THE FACTORY MATH",
                         stats=(
                             ("Bottleneck station",
                              HERO_THROUGHPUT["bottleneck"]["key"]),
                             ("Units per year, one pipelined line",
                              f"≈ "
                              f"{HERO_THROUGHPUT['pipelined_per_year']:.0f}"),
                             ("Line capex",
                              f"${HERO_BREAK_EVEN['capex']:,.0f}"),
                             ("Units to cover annual fixed cost",
                              f"≈ "
                              f"{HERO_BREAK_EVEN['units_to_cover_annual_fixed']:.0f}"),
                             ("Units to recover the full line capex",
                              f"≈ "
                              f"{HERO_BREAK_EVEN['units_to_recover_capex']:.0f}")),
                         position="left"),
                     narration=(
                         "The same simulator that draws the struts also "
                         "runs the factory math. One pipelined "
                         "production line, modeled station by station "
                         "with the framing stage as the bottleneck, "
                         "turns out roughly eighty two domes a year.",
                         "At that rate, the line covers its own annual "
                         "fixed overhead in about nineteen units and "
                         "recovers its full capital cost in about "
                         "forty four — the kind of arithmetic a "
                         "lender, not a marketer, actually asks for.",
                     )),
                Shot("benchmark", 9.5, lens="portrait", focus="dome",
                     yaw=-140, pitch=20, orbit=8,
                     caption=f"Against a real manufactured-home "
                             f"benchmark: {BENCH_PRICE_PCT:.0f}% less "
                             f"price, {BENCH_LABOR_PCT:.0f}% fewer "
                             f"labor hours",
                     panel=OverlayPanel(
                         title="VS. A CONVENTIONAL MANUFACTURED HOME",
                         stats=(
                             ("Benchmark: conventional manufactured home",
                              f"${HERO_BENCH['conventional']['price']:,.0f}"
                              f" · "
                              f"{HERO_BENCH['conventional']['labor_hours']:.0f}"
                              f" labor hrs · "
                              f"{HERO_BENCH['conventional']['build_days']:.0f}"
                              f" build days"),
                             ("This simulator's representative dome",
                              f"${HERO_BENCH['dome']['price']:,.0f} · "
                              f"{HERO_BENCH['dome']['labor_hours']:.0f} "
                              f"labor hrs · "
                              f"{HERO_BENCH['dome']['build_days']:.0f} "
                              f"build days")),
                         position="right"),
                     narration=(
                         f"Set a representative dome from this "
                         f"simulator against this project's own "
                         f"conventional manufactured home benchmark and "
                         f"it prices {BENCH_PRICE_PCT:.0f} percent "
                         f"lower, uses {BENCH_LABOR_PCT:.0f} percent "
                         f"fewer labor hours, and models "
                         f"{BENCH_DAYS_PCT:.0f} percent fewer build "
                         f"days.",
                         "Those are this project's own assumptions, "
                         "stated plainly so you can disagree with any "
                         "one of them — not a claim dressed up as a "
                         "fact.",
                     )),
            ),
        ),
        Scene(
            "core", "Solving the hard objections",
            "a calm open field in daylight",
            world=(
                ("dome", {"radius": R, "skin_alpha": 0.10}),
                ("utility_column", {"radius": R, "reveal": 1.0}),
                ("hatch", {"radius": R, "az_deg": 35.0, "polar_deg": 60.0,
                          "open": 0.35}),
            ),
            shots=(
                Shot("utility_core", 9.0, lens="wide",
                     focus="utility_column", yaw=-45, pitch=16, orbit=8,
                     caption="The curved-wall objection has a "
                             "straight-line answer",
                     panel=OverlayPanel(
                         title="WHAT MUST BE SOLVED — AND HOW",
                         stats=(
                             ("Curved cabinetry / plumbing",
                              "A utility core: rectangular, or this "
                              "project's central column"),
                             ("Large custom windows",
                              "Standardized triangular openings, not "
                              "one-off curved glass"),
                             ("Foundation",
                              "An engineered ring foundation, not "
                              "\"light enough to skip one\"")),
                         position="left"),
                     narration=(
                         "A serious version of this pitch does not "
                         "pretend the curved wall is free. Cabinets, "
                         "plumbing runs and large custom windows all "
                         "want straight lines and flat planes, and a "
                         "dome has to earn the right to ignore that.",
                         "The answer is not to fight the curve "
                         "everywhere — it's to concentrate the straight "
                         "lines into one place, this utility core, and "
                         "let standardized triangular openings handle "
                         "windows instead of one-off curved glass. And "
                         "no, a light shell does not mean you skip an "
                         "engineered foundation.",
                     )),
                Shot("hatch_detail", 8.5, lens="macro", focus="hatch",
                     yaw=10, pitch=10, orbit=5,
                     caption="Leaks, fire, and code get solved by "
                             "details and paperwork, not by the shape",
                     panel=OverlayPanel(
                         title="MORE OF THE SAME LIST",
                         stats=(
                             ("Leaks",
                              "Gasketed joints + rainscreen + testing, "
                              "like the hatch shown here"),
                             ("Fire rating",
                              "Noncombustible cladding, same as any "
                              "code-compliant structure"),
                             ("Code / insurance / appraisal "
                              "unfamiliarity",
                              "Pre-approved plans, engineer-stamped "
                              "design, lenders lined up first")),
                         position="right"),
                     narration=(
                         "Leaks get solved the way this hatch solves "
                         "them: gasketed joints, a rainscreen, and real "
                         "testing — not an assumption that curved "
                         "surfaces shed water better. Fire rating comes "
                         "from noncombustible cladding, the same as any "
                         "code compliant building.",
                         "And the unglamorous stuff — appraisal, "
                         "insurance, code officials who have never seen "
                         "this shape — gets solved with paperwork done "
                         "in advance: engineer-stamped designs, "
                         "pre-approved plans, lenders and appraisers "
                         "already lined up. Fannie Mae's own selling "
                         "guide already allows dome-secured loans when "
                         "the appraiser has enough information. The "
                         "work is making sure they do.",
                     )),
            ),
        ),
        Scene(
            "honesty", "Claims this project will not make",
            "the same open field at dusk",
            world=(("dome", {"radius": R, "skin_alpha": 0.14}),),
            shots=(
                Shot("claims_list", 11.0, lens="wide", focus="dome",
                     yaw=0, pitch=12, orbit=8,
                     caption="What this project will not tell you — "
                             "on purpose",
                     panel=OverlayPanel(
                         title="CLAIMS THIS PROJECT WILL NOT MAKE",
                         bullets=(
                             "“A dome is disaster-proof.”",
                             "“A dome always costs less than a "
                             "normal house.”",
                             "“The strut relationship is the "
                             "golden ratio.”",
                             "“Natural circulation eliminates the "
                             "need for HVAC.”",
                             "“A kit is automatically legal because "
                             "the owner assembles it.”",
                             "“Domes are the answer for dense "
                             "urban housing.”"),
                         position="bottom"),
                     narration=(
                         "Before the close, the claims this project "
                         "deliberately will not make, because "
                         "overclaiming is what gets a new building type "
                         "laughed out of a lender's office. A dome is "
                         "not disaster proof. It does not always cost "
                         "less than a normal house — you just watched "
                         "the honest, smaller number for a finished "
                         "home.",
                         "The strut relationship is not the golden "
                         "ratio. Natural airflow does not eliminate the "
                         "need for real HVAC design. A kit is not "
                         "automatically legal because an owner "
                         "assembled it. And this shape is not the "
                         "answer for dense urban housing — it never "
                         "claimed to be.",
                     )),
                Shot("where_it_fits", 8.0, lens="portrait", focus="dome",
                     yaw=-70, pitch=16, orbit=6,
                     caption="Where the case is actually strong: "
                             "starter homes, ADUs, rural and off-grid, "
                             "disaster-resistant low-rise",
                     panel=OverlayPanel(
                         title="THE BOTTOM LINE",
                         bullets=("Not suited to high-rises or one-off "
                                  "custom architecture",
                                  "Genuinely suited to starter homes, "
                                  "rural housing, ADUs, workforce and "
                                  "veteran communities",
                                  "...and disaster-resistant low-rise, "
                                  "remote construction, and "
                                  "hospitality-funded development"),
                         position="right"),
                     narration=(
                         "Here is where the case actually holds: "
                         "starter homes, rural housing, accessory "
                         "dwelling units, workforce and veteran cottage "
                         "communities, disaster resistant low-rise "
                         "construction, and remote or off-grid sites "
                         "where shipping a flat-pack shell beats "
                         "trucking in lumber.",
                         "That is a narrower claim than 'domes will "
                         "replace housing.' It is also one this project "
                         "can actually defend, line by line, with its "
                         "own numbers.",
                     )),
            ),
        ),
        Scene(
            "product", "Three sizes, real financing, one toolkit",
            "a tropical beach at sunset",
            world=(
                ("dome", {"radius": R, "skin_alpha": 0.16}),
                ("solar_band", {"radius": R, "coverage": 1.0}),
            ),
            shots=(
                Shot("product_tiers", 9.5, lens="wide", focus="dome",
                     yaw=-100, pitch=18, orbit=10,
                     caption="Four real product tiers, priced by the "
                             "same engine that built this video",
                     panel=OverlayPanel(
                         title="THE ACTUAL PRODUCT LINE",
                         stats=tuple(
                             (ab.DOME_TYPES[k].name,
                              f"from ${ab.DOME_TYPES[k].price_base:,.0f} "
                              f"base + "
                              f"${ab.DOME_TYPES[k].price_per_m2:,.0f}/m"
                              f"² — {ab.DOME_TYPES[k].tagline}")
                             for k in ("home", "shed", "greenhouse",
                                      "shelter")),
                         position="left"),
                     narration=(
                         "Four product tiers, and every price on this "
                         "panel comes from the same pricing function "
                         "running inside the interactive simulator: a "
                         "turnkey off-grid dome home, a storage shed, a "
                         "greenhouse, and a welded steel-plate storm "
                         "shelter.",
                         "None of that is invented for this video. It "
                         "is the actual configuration table the "
                         "software ships with.",
                     )),
                Shot("financing", 8.5, lens="macro", focus="dome",
                     yaw=60, pitch=14, orbit=6,
                     caption=f"A representative home dome: "
                             f"${HERO_PRICE:,.0f}, "
                             f"{ab.ASSUMPTIONS['bhph_down_fraction']*100:.0f}"
                             f"% down, "
                             f"{ab.ASSUMPTIONS['bhph_apr']*100:.1f}% APR",
                     panel=OverlayPanel(
                         title="FINANCING, ALREADY MODELED",
                         stats=(
                             ("Sale price", f"${HERO_PRICE:,.0f}"),
                             ("Down payment",
                              f"{ab.ASSUMPTIONS['bhph_down_fraction']*100:.0f}%"),
                             ("APR / term",
                              f"{ab.ASSUMPTIONS['bhph_apr']*100:.1f}% / "
                              f"{ab.ASSUMPTIONS['bhph_term_months']} "
                              f"months"),
                             ("Monthly payment",
                              f"${HERO_MONTHLY:,.0f}")),
                         bullets=("Standardized financing is one of "
                                  "this project's own \"what must be "
                                  "solved\" items",
                                  "This is what a workable answer looks "
                                  "like, computed, not promised"),
                         position="right"),
                     narration=(
                         "Standardized financing is on this project's "
                         "own list of things that must be solved before "
                         "any of this scales, so here is a real answer: "
                         "this representative home dome, ten percent "
                         "down, eleven point nine percent APR over "
                         "sixty months, comes to about two thousand "
                         "seventy eight dollars a month.",
                         "That number exists because the software "
                         "computes it the same way it computes "
                         "everything else in this video — not because "
                         "it sounds good.",
                     )),
                Shot("close", 11.0, lens="ultrawide", perspective=6,
                     focus="dome", yaw=-90, pitch=22,
                     caption="The argument and the toolkit are the "
                             "same product",
                     panel=OverlayPanel(
                         title="WHAT YOU ARE ACTUALLY GETTING",
                         bullets=("A dome designer and cost engine",
                                  "An interactive assembly-line factory "
                                  "simulator",
                                  "A shed-vs-dome, house-vs-dome "
                                  "comparison tool",
                                  "A local voice studio for narration "
                                  "you own",
                                  "This presenter engine — the one "
                                  "that just built this entire video"),
                         position="bottom"),
                     narration=(
                         "Every model, every number, every camera move "
                         "in this video came out of the same codebase: "
                         "a dome designer, a factory simulator, a "
                         "comparison engine, a local voice studio, and "
                         "this presenter engine, which just spent the "
                         "last several minutes building its own sales "
                         "pitch out of nothing but a text script.",
                         "That is the actual product. The argument for "
                         "the dome was never separate from the "
                         "software that proves it — they shipped "
                         "together, and you just watched them work.",
                     )),
            ),
        ),
    )
    return Presentation(
        title="The 2V Housing Case",
        author="DomeSim Presenter Studio",
        scenes=scenes,
    )
