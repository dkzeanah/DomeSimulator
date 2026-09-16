"""Every illustration in Domology, as a recipe.

A plate is not a screenshot. It is a scene from one of the project's own tools,
with something changed so that one idea shows: a moment chosen, a layer hidden,
a triangle lifted out, a label added. Each recipe says which tool draws it,
what was changed and why, and what caption the book prints under it -- and a
caption's numbers are live tokens, like the prose's.

Nothing is drawn here. :mod:`render_plates` draws, each tool in its own
process, and writes every render into ``deliverables/domology/plates`` beside a
record of exactly how it was made. Renders are append-only: a re-render writes
``-v2``, and the book always uses the newest.

Tools
-----
``film``   a chapter of one of the project's films, shot again at print size in
           the film engine's clean "plate" style (the picture and its labels;
           no headline, cards or callouts), sometimes with geometry added
``scene``  a scene built for this book from the engine's visual objects
``forge``  Dome Forge in a hidden window, with its layers set for the picture
``line``   the Dome Home Assembly Line, stopped at one station
``chart``  a chart drawn from the same code the numbers come from
``composite`` two renders side by side
"""

from __future__ import annotations

import json
import re
from dataclasses import dataclass, field
from functools import lru_cache
from pathlib import Path

from . import config

LANDSCAPE = (2400, 1500)
"""Print size for a text-width plate: 2400 px across 6.7 in is 358 dpi."""
PORTRAIT = (2440, 3080)
"""A full page with bleed, 8.125 x 10.25 in, at 300 dpi."""


@dataclass(frozen=True)
class Plate:
    id: str
    title: str
    caption: str
    concept: str
    change: str
    tool: str
    recipe: dict = field(default_factory=dict)
    size: tuple = LANDSCAPE

    @property
    def credit(self) -> str:
        r = self.recipe
        if self.tool == "film":
            from two_v_demo.lesson_registry import LESSONS
            lesson = LESSONS.get(r["lesson"])
            name = lesson.title if lesson else r["lesson"]
            return (f"Rendered by the DomeSim film engine from “{name}”, chapter "
                    f"“{r['chapter']}”, {round(r.get('progress', 0.6) * 100)}% "
                    f"through. {self.change}")
        if self.tool == "scene":
            return f"Built for this book from the film engine's visual objects. {self.change}"
        if self.tool == "forge":
            return f"Rendered by Dome Forge with its interface hidden. {self.change}"
        if self.tool == "line":
            return f"Rendered by the Dome Home Assembly Line. {self.change}"
        if self.tool == "chart":
            return f"Drawn when the book is built. {self.change}"
        if self.tool == "composite":
            return f"Two renders side by side. {self.change}"
        return self.change


def film(id, title, caption, concept, change, lesson, chapter, progress, size=LANDSCAPE,
         **options) -> Plate:
    recipe = {"lesson": lesson, "chapter": chapter, "progress": progress, **options}
    return Plate(id, title, caption, concept, change, "film", recipe, size)


def scene(id, title, caption, concept, change, name, camera, **options) -> Plate:
    return Plate(id, title, caption, concept, change, "scene",
                 {"scene": name, "camera": camera, **options})


def forge(id, title, caption, concept, change, **recipe) -> Plate:
    return Plate(id, title, caption, concept, change, "forge", recipe)


def line(id, title, caption, concept, change, **recipe) -> Plate:
    return Plate(id, title, caption, concept, change, "line", recipe)


def chart(id, title, caption, concept, change, name, **options) -> Plate:
    return Plate(id, title, caption, concept, change, "chart", {"chart": name, **options})


WATER_ONLY = ("ground", "veins", "vein_water", "collector_ring", "downpipe", "cistern")


PLATES: tuple[Plate, ...] = (
    # ------------------------------------------------------------------ Book One
    film("creator-lineup", "Twelve domes, one geometry engine",
         "All {{dm.presets}} designs in the Dome Creator, each rebuilt from the simulator's "
         "own model and stood side by side at true relative scale.",
         "One geometry makes buildings from a garden shed to a hangar.",
         "The lineup is frozen after the last design has risen, with its names kept.",
         "world", "world_open", 0.9),
    chart("chart-skin", "Less skin for the same floor",
          "On the same {{dm.box_floor}} square feet of floor, a box house needs "
          "{{dm.box_skin}} square feet of walls and roof and a 2V hemisphere of flat panels "
          "{{dm.panel_skin}}: {{dm.skin_saving_pct}} percent less envelope. A sphere wraps a "
          "volume in {{dm.sphere_saving_pct}} percent less skin than a cube.",
          "Envelope per unit of floor is where a dome's efficiency lives.",
          "From domology.science, using al_build's comparison house.", "skin"),
    chart("chart-comparison", "Where the saving stops",
          "One rate card, two shapes. As a bare shell the dome costs {{dm.shed_cut_pct}} "
          "percent less than the box; finished, only {{dm.home_cut_pct}} percent less, "
          "because the kitchen, bath and wiring cost the same in either shape.",
          "The shape saves on the shell, not on what goes inside it.",
          "From al_build.building_comparisons, with the fit-out drawn as its own band.",
          "comparison"),
    film("rigidity", "A triangle does not lean",
         "Three sides fix a triangle's three angles; four sides fix nothing about a "
         "square's. At the moment of greatest shear the square has leaned and the "
         "triangle has not moved.",
         "Triangulation makes a frame rigid without heavy joints.",
         "Stopped at the instant the square leans furthest.",
         "2v", "triangles", 0.25),
    scene("force-panel", "Compression and tension in one triangle",
          "Load a triangle at its apex and the two sloping members push back in "
          "compression while the tie across the bottom pulls in tension. Every member of "
          "a triangulated shell works along its length.",
          "Members carry load along their axes, not across them.",
          "Built for the book: three members, their forces, and the supports.",
          "force_panel", {"eye": [0.0, -15.5, 3.9], "target": [0.0, 0.0, 3.2], "fov": 40.0}),
    film("classes-colored", "Forty triangles, two shapes",
         "The 2V dome's struts sorted by length: {{dm.long_count}} long and "
         "{{dm.short_count}} short in a hubbed hemisphere, in two triangle shapes.",
         "A 2V dome has only two strut lengths and two triangle shapes.",
         "The classes scene once every strut has taken its class colour.",
         "2v", "classes", 0.92),
    film("platonic", "The five Platonic solids",
         "The five solids whose faces are all the same regular polygon. The icosahedron, "
         "with {{dm.ico_faces}} equilateral triangles, is the most sphere-like of them.",
         "The icosahedron is where every geodesic dome begins.",
         "Stopped once every edge has drawn, with the icosahedron highlighted.",
         "2v", "platonic", 0.8, camera={"zoom": 1.25}),
    film("ico-coordinates", "Twelve corners from one number",
         "Every corner of the icosahedron sits at a combination of 0, ±1 and ±φ, "
         "where φ = {{dm.phi}}. One vertex is marked.",
         "Phi places the icosahedron's twelve vertices exactly.",
         "The coordinates scene with its axes and one vertex labelled.",
         "2v", "phi", 0.92),
    film("midpoints", "Split every edge",
         "Mark the middle of every edge and each triangle becomes four: the "
         "icosahedron's {{dm.ico_faces}} faces become {{dm.sphere_faces}}.",
         "Subdivision multiplies the faces while keeping them triangles.",
         "Stopped after the midpoints appear, before they are pushed out.",
         "2v", "subdivide", 0.85),
    film("projection", "Push the new points out",
         "Move each new point out to the sphere. The flat faces bend into a dome and "
         "the edges fall into exactly two lengths.",
         "Projection turns a subdivided solid into a geodesic sphere.",
         "Near the end of the projection, with the points on the sphere.",
         "2v", "project", 0.9),
    chart("chart-frequency", "What frequency costs",
          "Built at one radius: {{dm.f1_struts}}, {{dm.f2_struts}}, {{dm.f3_struts}} and "
          "{{dm.f4_struts}} struts for 1V to 4V, in {{dm.f1_classes}}, {{dm.f2_classes}}, "
          "{{dm.f3_classes}} and {{dm.f4_classes}} lengths. Even frequencies cut exactly at "
          "the equator.",
          "Higher frequency buys smoothness and costs part variety.",
          "From world_facts.frequency_ladder, which builds each dome with the simulator.",
          "frequency"),
    film("classes-dome", "Two lengths of board",
         "The 2V hemisphere and the two boards it is cut from. Whatever the size, the "
         "long strut is {{dm.ratio}} times the short one.",
         "A whole dome is two cut lengths.",
         "The masterclass opening, once the dome has drawn, beside its two boards.",
         "2v", "welcome", 0.92),
    Plate("forge-jig-shop", "Two jigs make every triangle",
          "The two jigs that make all {{dm.hemi_faces}} triangles: {{dm.equi_count}} "
          "equilateral on the left, {{dm.iso_count}} isosceles on the right, each loaded "
          "with its three boards.",
          "Two shapes means two jigs, and a repeatable shop.",
          "Dome Forge's jig shop, both jigs loaded and seen from directly above so "
          "their true shapes compare, each named.",
          "composite",
          {"parts": [
              {"tool": "forge", "mode": "jigs", "jig": 0, "stage": "loaded",
               "yaw": -90.0, "pitch": 86.0, "distance": 6.8},
              {"tool": "forge", "mode": "jigs", "jig": 1, "stage": "loaded",
               "yaw": -90.0, "pitch": 86.0, "distance": 6.8},
          ],
           "labels": ["JIG A · EQUILATERAL · {{dm.equi_count}} PANELS",
                      "JIG B · ISOSCELES · {{dm.iso_count}} PANELS"]}),
    film("cutlist", "The whole cut list",
         "Every member of the hemisphere is one of two lengths, cut {{dm.long_count}} "
         "and {{dm.short_count}} times.",
         "The cut list of a 2V dome is two lines long.",
         "The masterclass cut-list scene at full reveal.",
         "2v", "cut_list", 0.92),
    forge("forge-deficit", "Why a flat fan rises",
          "At a five-way hub the flat corners fall {{dm.deficit5}} degrees short of a full "
          "turn, so closing the fan lifts its centre into the curve.",
          "Angular deficit is what curves a dome.",
          "The jig shop's last stage, which assembles a fan around one hub.",
          mode="jigs", jig=1, stage="deficit", yaw=64.0, pitch=60.0, distance=7.0),
    chart("forge-pattern", "A pentagon, laid flat",
          "Five triangles around a point, developed flat at the reference dome's size, "
          "with the {{dm.deficit5}}-degree dart that closes to make the curve. The dashed "
          "line is the cut with seam allowance; dotted lines are folds.",
          "A doubly curved cover is cut from flat stock by closing darts.",
          "From Dome Forge's cover-pattern geometry, dome_forge.patterns.", "pattern"),
    film("hex-deficit", "Curvature is bought with missing angle",
         "A sheet of hexagons stays flat, because three hexagon corners fill a full turn. "
         "A closed cage of polygons is always short by {{dm.descartes}} degrees in total.",
         "Descartes' theorem: every closed cage is short the same total angle.",
         "The hex masterclass's deficit scene.", "hex", "buy_curve", 0.8),
    film("hub-dome", "A dome on hubs",
         "{{dm.hemi_edges}} struts meet at {{dm.hemi_hubs}} hubs; each hub gathers up to six "
         "members at compound angles.",
         "Hub-and-strut puts all the geometry into the connectors.",
         "The construction masterclass's hub scene near its end.", "build", "hubs", 0.85),
    forge("forge-hubless", "Forty separate triangles",
          "The hubless frame: {{dm.hemi_faces}} triangles, each bringing its own three "
          "members, bolted to their neighbours. Here every triangle is lifted straight "
          "out from the centre so each can be seen whole.",
          "A hubless dome is a set of panels, not a set of sticks.",
          "Only the panel assemblies shown, fills off; every face selected and popped out.",
          mode="dome", only=("ground", "assemblies"),
          layers={"assemblies": {"show_fills": False, "highlight": False}},
          select="all", explode=1.4, yaw=38.0, pitch=24.0, distance=14.5),
    film("compound-cut", "Two angles at once",
         "A hubless strut's end needs a mitre and a bevel together: {{dm.hubless_setups}} "
         "distinct setups in all, {{dm.hubless_past_saw}} past a typical saw's stop.",
         "The compound cut is the hardest operation in a hubless dome.",
         "The compound-cut film's opening scene, moved in so its labels separate.",
         "cuts", "two_angles", 0.7, camera={"zoom": 0.75}),
    forge("forge-waist", "An hourglass and its waist",
          "Two equilateral triangles meeting at a single point, joined by wooden braces "
          "that carry the load into their sides rather than their end-grain tips.",
          "Where triangles meet point to point, the joint belongs to the waist.",
          "The group editor on the first hourglass, moved in close on its braced waist.",
          mode="groups", group=("hourglass", 0), joint="wood_brace", distance=3.0),
    film("kick-wind", "Wind around a round body",
         "Wind parts around a curved shell instead of piling against a flat wall.",
         "A round body has no broad face for wind to push on.",
         "The campaign film's wind scene.", "kick2", "wind", 0.7),
    forge("forge-water", "The water dome in section",
          "Dished panels shed rain to micro-drains; seam veins carry anything that gets "
          "past a seam down to a collector ring, a downpipe and a cistern.",
          "A dome's seams can be plumbing instead of leaks.",
          "The default water stack with the cutaway open and the flow mid-run.",
          mode="dome", cut=(150.0, 140.0), clock=1.4, yaw=205.0, pitch=22.0,
          distance=10.5),
    forge("forge-rain", "In the rain",
          "The same dome from outside, each panel dished to its own low point.",
          "Every panel sheds its own water.",
          "Rain and panel runoff on, from low on the ground.",
          mode="dome", clock=2.2, layers={"rain": {"visible": True}},
          yaw=32.0, pitch=6.0, distance=12.5),
    film("hex-soccer", "A soccer-ball dome",
         "The truncated icosahedron as a dome: pentagons and hexagons in place of "
         "triangles, and always {{dm.pentagons}} pentagons.",
         "Hex domes trade triangles for flat polygons.",
         "The hex masterclass's soccer-ball scene.", "hex", "one_hexagon", 0.8),
    film("zome-star", "A zome",
         "A zome: {{dm.zome_faces}} flat four-sided panels spiralling up to a single point.",
         "Zomes use flat rhombi and spiral symmetry.",
         "The zome masterclass's opening zome, fully drawn.", "zome", "what", 0.85),
    film("creator-framing", "Three ways to frame",
         "Hub and strut, hubless doubled triangles, and continuous arcs, compared on "
         "real designs from the catalogue.",
         "Framing systems trade hardware for wood and skill.",
         "The world film's framing scene.", "world", "framing", 0.8),
    film("creator-economics", "The same shape, clad twelve ways",
         "Across the catalogue a square foot costs from {{dm.cheapest_sqft}} to "
         "{{dm.dearest_sqft}} dollars: the cladding decides the price, not the shape.",
         "Materials, not geometry, set a dome's cost per foot.",
         "The world film's cladding scene.", "world", "cladding", 0.8),
    film("why-dome", "The shell being priced",
         "The simulator's solved wedge dome: the shell whose framing the cost chapters "
         "price.",
         "The priced object is the real solved geometry.",
         "Why Build This Way's dome scene.", "why_build", "question", 0.6),
    chart("chart-house", "Where a new house's price goes",
          "A new house's price from the builders' survey, first by who is paid, then by "
          "what the money buys.",
          "Most of a house's price is not its frame.",
          "From house_economics, NAHB's 2024 cost survey.", "house"),
    # ------------------------------------------------------------------ Book Two
    film("creator-homestead", "The Split-Log Homestead",
         "Half-round logs on the long seams, quarter-round on the short: a preset built "
         "from split wood, rebuilt by the simulator.",
         "Split logs can frame a dome directly.",
         "The world film's Split-Log Homestead chapter.", "world", "show_02", 0.8),
    film("creator-trunk", "The Whole Trunk Lodge",
         "Whole trunks as struts: a dome sized to the trees that frame it.",
         "The tree can set the size of the building.",
         "The world film's Whole Trunk Lodge chapter.", "world", "show_03", 0.8),
    line("line-frame", "The shell on the line",
         "The frame raised on the transfer carriage at the framing station, before "
         "anything hides it.",
         "A line builds the shell first, while it is open.",
         "The line stopped as the framing station finishes.",
         stage="frame", fraction=0.97, cutaway=False, yaw=-150.0, pitch=24.0, distance=14.0),
    line("line-services", "Services before skin",
         "Water and power routed through the floor to one central column while the "
         "shell is still open.",
         "Services go in while the frame is still open.",
         "The line at the power station, seen from above.",
         stage="power", fraction=0.99, cutaway=False, yaw=-30.0, pitch=50.0, distance=12.5),
    line("line-interior", "Fit-out through a cutaway",
         "Kitchen, bath and bedroom fitted at the interior station, seen through a roof "
         "cutaway.",
         "A round room fits a full home.",
         "The interior station with the cutaway forced open.",
         stage="interior", fraction=0.98, cutaway=True, yaw=-30.0, pitch=50.0, distance=12.5),
    film("scratch-pipeline", "From geometry to a pixel",
         "The whole chain the from-scratch film derives on camera: points, edges, "
         "triangles, the camera, the screen.",
         "The films compute every picture from first principles.",
         "The from-scratch film's pipeline scene, moved in so each stage reads.",
         "scratch", "pipeline", 0.9, camera={"zoom": 0.7}),
    film("math-screen", "A worksheet on screen",
         "A film's math screen: the picture stays live while every figure is derived "
         "beside it. This book prints the same worksheets.",
         "Every number on screen is computed, and shown being computed.",
         "Why Build This Way's sources chapter with its worksheet kept.",
         "why_build", "sources", 0.97, keep_overlay=True),
    forge("forge-layers", "Every layer at once",
          "The water dome with its panels made translucent, so the veins, collector "
          "ring, downpipe and cistern show through them.",
          "A dome is a stack of layers, each with one job.",
          "The panel assemblies at a third opacity, with the cutaway open.",
          mode="dome", cut=(160.0, 90.0), clock=1.0,
          layers={"assemblies": {"opacity": 0.33}},
          yaw=210.0, pitch=22.0, distance=12.0),
    forge("forge-panel", "Three kinds of stock in one frame",
          "Dome Forge's split-log stack: half-round logs on the long seams, quarter-round "
          "on the short, and a lighter 2x2 on the equilateral caps, with the fills turned "
          "off so the frame shows.",
          "A frame can mix its stock: each seam gets the stick it needs.",
          "The split-log stack, fills off, moved in close so the different stock reads.",
          mode="dome", stack="splitlog", only=("ground", "assemblies"),
          layers={"assemblies": {"show_fills": False, "highlight": False}},
          yaw=38.0, pitch=30.0, distance=7.0),
    forge("forge-pentagon", "A pentagon group",
          "Five isosceles triangles around a five-way hub, edited as one group.",
          "People design domes in pentagons and hourglasses, not triangles.",
          "The group editor with the first pentagon selected.",
          mode="groups", group=("pentagon", 0), yaw=30.0, pitch=34.0, distance=7.0),
    chart("forge-nesting", "Covers nested on the sheet",
          "Pentagon covers split three-plus-two so each piece fits the sheet, packed by "
          "Dome Forge's own nesting routine.",
          "Flat patterns nest onto real sheet sizes.",
          "From dome_forge.patterns.auto_nest.", "nesting"),
    film("franken-bracket", "A V-bracket between unlike members",
         "The connector that let any stick meet any other.",
         "A strut-agnostic frame needs an agnostic connector.",
         "The Frankendome film's fitted bracket.", "franken", "bracket_fitted", 0.8),
    film("franken-triangle", "Three different sticks, one rigid shape",
         "A Frankendome triangle made from three unlike members.",
         "A triangle is rigid whatever its sticks are.",
         "The Frankendome film's triangle scene.", "franken", "triangle", 0.8),
    film("franken-slack", "Slack and settling",
         "When every member is a little different, every joint takes up a little error "
         "and the frame settles.",
         "Irregular parts spread error through every joint.",
         "The Frankendome film's slack scene.", "franken", "slack", 0.6),
    film("wedge-split", "Split, not sawn",
         "One section of trunk split radially into {{tree.sectors}} sectors of "
         "{{tree.sector_angle_deg}} degrees each.",
         "A radial split uses the log's round shape instead of fighting it.",
         "The wedge film's split scene.", "wedge", "split", 0.8),
    film("wedge-round", "The same round, two ways",
         "Split, this log keeps {{pine.kerf_only_pct}} percent before trimming; packed with "
         "two-by-fours it keeps {{pine.sawn_model_pct}}.",
         "The corners of a log are only waste to a rectangle.",
         "The wedge argument's round-section scene, moved in so its labels separate.",
         "why", "round", 0.9, camera={"zoom": 0.85}),
    film("wedge-orient", "Four ways to turn a wedge",
         "The same wedge turned four ways in a panel makes four different buildings.",
         "Orientation is a design decision.",
         "The wedge film's orientation scene.", "wedge", "orient", 0.8),
    film("wedge-chain", "The machines that drop out",
         "Tree to frame, with the machines the wedge path never needs faded out.",
         "One chainsaw replaces a sawmill's chain.",
         "The wedge argument's processing-chain scene, moved in.", "why", "chain", 0.9,
         camera={"zoom": 0.7}),
    film("harvest-explode", "A section opened into its wedges",
         "One section of the bucked trunk, opened into the {{tree.sectors}} wedges a "
         "radial split makes.",
         "Each bucked section becomes a set of wedges.",
         "The harvest film's close look at one opened section.",
         "harvest", "why", 0.5),
    film("solved-dome", "The shell those wedges make",
         "The raw-wedge simulator's solved dome, keys and all.",
         "The design is solved before a tree is cut.",
         "The harvest film's dome scene.", "harvest", "worth", 0.5),
    film("pine-ladder", "One pine, every rung",
         "Standing, burned, sawn, split, built and financed: one tree's values side by side.",
         "What a tree is worth depends on what you do with it.",
         "The $20 Pine's closing ladder.", "pine_value", "closing", 0.9),
    film("buttcut", "The one compound cut",
         "The butt end of each member: the one compound cut the wedge method keeps, made "
         "once, off the jig.",
         "The wedge method still needs one compound cut.",
         "The wedge argument's butt-cut scene.", "why", "buttcut", 0.8),
    film("wedge-stick", "A wedge against a board, in bending",
         "One wedge and one dressed two-by-four in bending: the comparison that did not "
         "flatter the wedge, printed.",
         "A single wedge is a weaker beam; a triangulated frame does not ask it to be one.",
         "The wedge argument's stick scene.", "why", "stick", 0.85),
    # ------------------------------------------------------------------ Book Three
    scene("method-dome", "A dome from the floor you want",
          "A {{method_a.floor_sqft}} square foot dome: radius {{method_a.radius_ft}} feet, "
          "longest member {{method_a.longest_in}} inches.",
          "Method A: choose the floor, and the members follow.",
          "The solved dome with its radius, height and floor marked.",
          "dimensioned_dome", {"eye": [9.5, -12.5, 5.6], "target": [0.0, 0.0, 2.1],
                               "fov": 42.0}),
    scene("dome-top", "The floor it covers",
          "The same dome from above: the floor circle and the ring of hubs it stands on.",
          "A dome's footprint is a circle, and its foundation is a ring.",
          "The solved dome from overhead with the floor circle drawn.",
          "dome_plan", {"eye": [0.0, -2.2, 17.5], "target": [0.0, 0.0, 0.0], "fov": 40.0}),
    film("wedge-section", "A wedge and a board, end-on",
         "Drawn at the same real size.",
         "A wedge carries more wood than the board it replaces.",
         "Why Build This Way's cross-section, moved in.", "why_build", "tree", 0.9,
         camera={"zoom": 0.72}),
    film("tool-chain", "A long chain and a short one",
         "Income, tax, store, contractor, loan, shelter; or tree, wedge, jig, shell.",
         "The method shortens the chain between an hour and a house.",
         "Why Build This Way's chain scene, fully revealed.", "why_build", "chain", 0.97),
    film("harvest-fell", "The hinge steers the tree",
         "The face notch and the back cut, and the hinge between them.",
         "A felled tree goes where its hinge sends it.",
         "The harvest film's felling scene at the back cut.", "harvest", "fell", 0.42),
    film("harvest-buck", "Bucking to length",
         "The stem cut into sections as long as the longest member.",
         "Bucking to finished length removes a crosscut.",
         "The harvest film as the bucking cuts are made, re-aimed along the stem.",
         "harvest", "explode", 0.26,
         camera={"fn": "hv_pile", "yaw": -160.0, "pitch": 22.0, "distance": 13.0}),
    film("harvest-pile", "Two trees, split",
         "The harvest as a pile of wedges.",
         "The pile is the whole frame.",
         "The harvest film's pile, seen along the row from its near end.",
         "harvest", "cost", 0.5,
         camera={"fn": "hv_pile", "yaw": -160.0, "pitch": 22.0, "distance": 13.0}),
    film("jig-panel", "Locate first, cut second",
         "Members held in their true relationship before the excess is trimmed.",
         "The jig solves the geometry once.",
         "Why Build This Way's jig scene as the members arrive.", "why_build", "jig", 0.5),
    film("jig-stages", "The fabrication bench",
         "One flat jig that turns sticks into panels.",
         "A flat bench is the whole factory.",
         "The wedge argument's bench scene.", "why", "bench", 0.8),
    film("pinwheel", "The pinwheel panel",
         "Each member's end butts the side of the next, around the triangle.",
         "End to side, never end to end.",
         "The wedge film's pinwheel scene.", "wedge", "pinwheel", 0.85),
    film("panel-corner", "One corner, close up",
         "A pinwheel corner: one member's end against another's side.",
         "The corner is a physical object, not a point.",
         "The wedge film's corner scene.", "wedge", "corner", 0.8),
    chart("panel-drawing", "The two panels, drawn to build",
          "Both panel shapes at the book's build size, flattened: each stick's length, "
          "where its head stops against the next stick's side, and the corner left open. "
          "The ends are square because this drawing models a flat band; a real log "
          "sector needs the compound butt cut described in the text.",
          "Two drawings are the whole shop-drawing set for a pinwheel dome.",
          "From two_v_demo.wedge_geometry.pinwheel_panels at the build plan's radius.",
          "panel_drawing"),
    film("flush-cut", "Flush cutting in place",
         "The overlong head trimmed against the panel after the jig has located it.",
         "Leave it long, then cut it true.",
         "The wedge argument's flush-cut scene.", "why", "flush", 0.85),
    film("gasket", "The seam and its gasket",
         "Where two panels meet, with the gasket between them.",
         "Each panel keeps its own edge.",
         "The wedge film's gasket scene.", "wedge", "gasket", 0.85),
    film("keystone", "The key in the seam",
         "A shaped key holds the fold angle between two panels.",
         "The connector holds the angle, not the stick.",
         "The wedge argument's keystone scene.", "why", "keystone", 0.8),
    film("fold", "Two fold angles",
         "The dome's panels fold at only {{seam.distinct_angles}} angles: "
         "{{seam.fold_a_deg}} and {{seam.fold_b_deg}} degrees.",
         "A whole dome folds at two angles.",
         "The wedge argument's fold scene.", "why", "fold", 0.8),
    film("foundation", "A level ring",
         "Footings and a level ring: most of a dome's foundation.",
         "A dome needs a level ring, not a slab.",
         "The construction masterclass's foundation scene.", "build", "foundation", 0.85),
    film("riser", "A riser wall",
         "A short wall under the dome gains headroom at the edge.",
         "A riser trades a little wall for a lot of usable floor.",
         "The construction masterclass's riser scene.", "build", "riser", 0.85),
    film("raise", "Ring by ring",
         "Raising the shell from the ground up.",
         "Stable at every step.",
         "The construction masterclass's raising scene.", "build", "raise", 0.6),
    film("apex", "The top",
         "The last pieces at the apex.",
         "The apex closes the shell.",
         "The construction masterclass's apex scene.", "build", "apex", 0.85),
    film("assemble", "Forty panels into a shell",
         "The pinwheel panels assembled into the dome.",
         "The shell is forty repeats of one job.",
         "The wedge film's assembly scene.", "wedge", "assemble", 0.7),
    film("skin", "Skinning the shell",
         "Closing the triangles against the weather.",
         "Skin follows the triangles.",
         "The construction masterclass's skin scene.", "build", "skin", 0.7),
    film("openings", "An opening in a triangulated shell",
         "Framing a door or window without breaking the triangles.",
         "Openings are framed around triangles, not cut through them.",
         "The construction masterclass's openings scene.", "build", "openings", 0.8),
    forge("forge-veins", "The seam veins alone",
          "A channel beneath every seam, standing off the skin, draining to the "
          "collector ring.",
          "The drainage network follows the seams.",
          "Only the veins, the water in them, the collector, downpipe and cistern.",
          mode="dome", only=WATER_ONLY, clock=1.6, yaw=35.0, pitch=30.0, distance=11.0),
    film("look-room", "A furnished round room",
         "A dome furnished as a home.",
         "A round room lives like any other.",
         "The lookbook's furnished dome.", "look", "furnished", 0.6),
    line("line-interior-room", "The room around the column",
         "The interior station seen closer and from the side: the service column at the "
         "centre of the room.",
         "One column carries water and power to the whole round room.",
         "The interior station from a lower, closer angle.",
         stage="interior", fraction=0.99, cutaway=True, yaw=-10.0, pitch=40.0, distance=9.0),
    film("check", "Checking the shell",
         "Checking the finished shell against the drawing.",
         "Measure the built dome, not just the parts.",
         "The construction masterclass's check scene.", "build", "check", 0.8),
    film("error", "Where error goes",
         "Small errors at every joint add up around a ring.",
         "Error accumulates around closed loops.",
         "The construction masterclass's error scene.", "build", "error", 0.8),
    # ------------------------------------------------------------------ Full pages
    film("frontispiece", "The shell",
         "The raw-wedge simulator's solved dome.",
         "The book's subject, as the simulator solved it.",
         "Why Build This Way's dome, centred and rendered as a full page.",
         "why_build", "why", 0.5, size=PORTRAIT,
         camera={"fn": "hv_dome_centred", "pitch": 14.0, "radii": 3.7}),
    film("divider-dome", "Book One",
         "The dome, from the masterclass.", "The subject of Book One.",
         "The masterclass opening, rendered as a full page.",
         "2v", "welcome", 0.95, size=PORTRAIT),
    film("divider-journey", "Book Two",
         "Twelve designs from the Dome Creator.", "The tools of Book Two.",
         "The world lineup, rendered as a full page.",
         "world", "world_open", 0.9, size=PORTRAIT),
    film("divider-build", "Book Three",
         "Forty panels going up into a shell.", "The work of Book Three.",
         "The wedge film's assembly, rendered as a full page.",
         "wedge", "assemble", 0.7, size=PORTRAIT),
)

BY_ID: dict[str, Plate] = {plate.id: plate for plate in PLATES}


# ----------------------------------------------------------------------
# Finding the newest render
# ----------------------------------------------------------------------

def latest_render(plate_id: str, directory: Path | None = None) -> Path | None:
    """The newest rendered version of a plate, or None if it was never drawn."""
    directory = directory or config.PLATES
    if not directory.is_dir():
        return None
    candidates = []
    exact = directory / f"{plate_id}.png"
    if exact.exists():
        candidates.append((1, exact))
    for path in directory.glob(f"{plate_id}-v*.png"):
        match = re.fullmatch(rf"{re.escape(plate_id)}-v(\d+)", path.stem)
        if match:
            candidates.append((int(match.group(1)), path))
    return max(candidates)[1] if candidates else None


@lru_cache(maxsize=512)
def _image_size(path: str, mtime: float) -> tuple[int, int]:
    from PIL import Image
    with Image.open(path) as image:
        return image.size


def aspect_of(plate: Plate) -> tuple[Path | None, float]:
    path = latest_render(plate.id)
    if path is None:
        width, height = plate.size
        return None, width / height
    width, height = _image_size(str(path), path.stat().st_mtime)
    return path, width / height


def manifest_of(path: Path) -> dict:
    record = path.with_suffix(".json")
    if record.exists():
        return json.loads(record.read_text(encoding="utf-8"))
    return {}


def validate_plates() -> None:
    from . import outline
    ids = [plate.id for plate in PLATES]
    assert len(ids) == len(set(ids)), "a plate id is used twice"
    for plate in PLATES:
        assert plate.concept.strip() and plate.change.strip(), plate.id
        assert plate.tool in ("film", "scene", "forge", "line", "chart", "composite"), plate.id
        for field_name in ("caption", "concept", "title"):
            text = getattr(plate, field_name)
            for label in ("1V", "2V", "3V", "4V"):
                text = text.replace(label, "")
            assert not re.search(r"(?<![{\w])\d{2,}(?![\w}])", text), \
                (plate.id, f"the {field_name} types a number; use a token")
    for _section, plan, book in outline.all_chapters():
        for plate_id in plan.plates:
            assert plate_id in BY_ID, (plan.id, plate_id)
    for book in outline.BOOKS:
        assert book.plate in BY_ID, book.plate
    from two_v_demo.lesson_registry import LESSONS
    for plate in PLATES:
        if plate.tool == "film":
            lesson = LESSONS.get(plate.recipe["lesson"])
            assert lesson is not None, (plate.id, plate.recipe["lesson"])
            slugs = {chapter.slug for chapter in lesson.chapters}
            assert plate.recipe["chapter"] in slugs, (plate.id, plate.recipe["chapter"])
