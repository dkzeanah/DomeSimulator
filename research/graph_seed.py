"""The seed of the knowledge graph: every idea this codebase is built on.

One node per concept a viewer, a builder or a searcher would type into a
search box, grouped into the project's territories, each with:

* a plain-language ``summary`` of what it means *in this project*;
* ``seeds`` -- search phrases to cycle through on YouTube and Google, which
  are also what the research engine (:mod:`research.engine`) scores;
* ``files`` -- where the codebase handles it, checked to exist;
* edges to the nodes it depends on or leads to.

This file is the source of truth for the seed. The published graph page
keeps its own edits in its database; ``py -3.12 -m research.graph_seed``
writes ``research/knowledge-graph.json`` for seeding it and for the engine.
"""

from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
OUT = Path(__file__).resolve().parent / "knowledge-graph.json"

CATEGORIES = {
    "geometry": ("Geodesic geometry", "The mathematics of the shell: frequencies, chords, angles."),
    "wedge": ("Wedge method", "Hubless 2V framing from split-log wedges -- the book's core."),
    "timber": ("Timber & harvest", "From standing tree to member: felling, ripping, yield, wood."),
    "envelope": ("Skin & comfort", "Panels, layers, insulation, moisture, cooling."),
    "systems": ("Services & systems", "The utility column, power, water, air, modules."),
    "site": ("Site & network", "Pads, foundations, dome parks, hosts and tenants, permits."),
    "modular": ("Modular housing", "Stem cell, fit-outs, ADUs, kit homes, the housing market."),
    "economics": ("Cost & campaign", "Prices, labour, margins, Kickstarter, deferment."),
    "structure": ("Structure & safety", "Loads, engineering, the mast, floating domes."),
    "media": ("Media & storytelling", "Films, the render engine, the book, how it is told."),
}

# (id, label, category, summary, seeds, files)
NODES: list[tuple[str, str, str, str, tuple[str, ...], tuple[str, ...]]] = [
    # ---- geometry ---------------------------------------------------------
    ("geodesic-dome", "Geodesic dome", "geometry",
     "A sphere approximated by flat triangles, so every piece is short, straight and loaded along its length.",
     ("geodesic dome", "how geodesic domes work", "geodesic dome explained", "buckminster fuller dome"),
     ("two_v_demo/geometry.py", "geodesic_raw_wedge_dome_dihedral.py")),
    ("2v-frequency", "2V frequency", "geometry",
     "Each icosahedron face split in two: two strut lengths, two triangle shapes, 40 triangles in a hemisphere.",
     ("2v geodesic dome", "2v dome calculator", "2 frequency dome strut lengths", "2v vs 3v dome"),
     ("seed_model.py", "two_v_masterclass.py")),
    ("icosahedron", "Icosahedron", "geometry",
     "The 20-faced solid every geodesic dome is subdivided from; its 12 corners become the five-way junctions.",
     ("icosahedron geodesic", "why domes use the icosahedron", "icosahedron subdivision"),
     ("two_v_demo/geometry.py",)),
    ("chord-factors", "Chord factors & strut lengths", "geometry",
     "Multipliers that turn a dome radius into member lengths; the book derives them rather than copying tables.",
     ("geodesic dome chord factors", "dome strut length formula", "geodesic dome cut list"),
     ("two_v_demo/wedge_geometry.py", "seed_model.py")),
    ("dihedral-angle", "Dihedral angle & fold", "geometry",
     "The bend between neighbouring faces: 18 deg across long seams, 22.5 across short ones in the reference 2V.",
     ("geodesic dome dihedral angle", "dome panel angles", "geodesic dome compound angles"),
     ("geodesic_raw_wedge_dome_dihedral.py", "campaign_schematics.py")),
    ("frequency-families", "3V, 4V and beyond", "geometry",
     "Higher frequencies: rounder, more parts, more lengths -- the trade the book declines for a first building.",
     ("3v geodesic dome", "4v dome", "dome frequency explained", "which dome frequency is best"),
     ("two_v_demo/lesson_hex.py",)),
    ("zome", "Zome", "geometry",
     "A dome swept from spirals instead of subdivided from a sphere; a different family, compared honestly.",
     ("zome house", "zome structure", "zome vs geodesic dome", "zome building"),
     ("zome_masterclass.py", "two_v_demo/lesson_zome.py")),
    ("hex-dome", "Hex dome & twelve pentagons", "geometry",
     "Why every dome of this family has exactly twelve five-way points, however it is tiled.",
     ("hexagon dome", "goldberg polyhedron", "why 12 pentagons", "hexagon geodesic dome"),
     ("hex_masterclass.py", "two_v_demo/lesson_hex.py")),

    # ---- wedge method ----------------------------------------------------
    ("wedge-member", "Split-log wedge member", "wedge",
     "Every member is one-eighth of a round log: triangular section, rounded face out, 45 deg point in.",
     ("split log dome", "log wedge construction", "wedge timber frame", "radial sawn timber"),
     ("geodesic_raw_wedge_dome_dihedral.py", "two_v_demo/wedge_geometry.py", "wedge_book/figures.py")),
    ("hubless", "Hubless geodesic dome", "wedge",
     "No connectors: members meet members. Removes the part most dome builders buy, machine or get wrong.",
     ("hubless geodesic dome", "geodesic dome without hubs", "dome connectors alternative", "no hub dome"),
     ("hubless_cut_masterclass.py", "two_v_demo/hubless_geometry.py")),
    ("pinwheel-joint", "Pinwheel corner joint", "wedge",
     "Each member's end butts into the side of the next; three chase round the triangle; the vertex stays empty.",
     ("pinwheel joint", "pinwheel geodesic dome", "reciprocal frame joint", "dome corner joint wood"),
     ("geodesic_raw_wedge_dome_dihedral.py", "book_wedge/manuscript/12-nothing-meets-at-the-corner.md")),
    ("panelized-dome", "Panel-first framing", "wedge",
     "Each triangle is its own frame, built flat on a bench and lifted as a finished object.",
     ("panelized geodesic dome", "prefab dome panels", "dome triangle panels build"),
     ("jig_focus_world.py", "book_wedge/manuscript/14-one-flat-board-forty-identical-panels.md")),
    ("seam-key", "Seam and key", "wedge",
     "Two members back to back at every seam; a key -- a slimmer wedge -- fills the V they leave.",
     ("geodesic dome seams", "dome panel joints", "timber spline joint"),
     ("two_v_demo/lesson_seam.py", "wedge_book/graphics.py")),
    ("seam-channel", "The seam channel", "wedge",
     "Left open, the V is a duct and a conduit that reaches every junction: air, cable, water.",
     ("dome ventilation", "service chase in walls", "hidden wiring timber frame"),
     ("seed_model.py", "book_wedge/manuscript/18-the-seam-does-four-jobs.md")),
    ("compound-cut", "Compound butt cut", "wedge",
     "Bevel constant at half the sector angle; three saw settings for 120 members.",
     ("compound miter cut", "geodesic dome cuts", "compound angle saw setup"),
     ("geodesic_raw_wedge_dome_dihedral.py",)),
    ("assembly-jig", "Assembly jig", "wedge",
     "The bench that makes forty identical panels: one set-up, many repeats.",
     ("geodesic dome jig", "panel assembly jig", "repeatable woodworking jig"),
     ("jig_focus_world.py", "workshop.py")),
    ("wedge-orientation", "Point in, face out", "wedge",
     "Four ways a wedge could sit; the book's is point toward the centre, rounded face to the weather.",
     ("wedge orientation", "log orientation timber frame"),
     ("wedge_book/figures.py",)),

    # ---- timber ----------------------------------------------------------
    ("chainsaw-ripping", "Ripping logs with a chainsaw", "timber",
     "The splitting process of the book's clock: one session at the log, 30 wedges.",
     ("chainsaw ripping logs", "chainsaw milling", "rip cut log chainsaw", "alaskan mill"),
     ("wedge_book/systems.py", "book_wedge/manuscript/09-stop-squaring-start-splitting.md")),
    ("log-yield", "Log yield: split vs sawn", "timber",
     "Split into wedges a log keeps 1.95x the wood of milling it into boards.",
     ("lumber yield from a log", "how much lumber in a tree", "board feet in a log"),
     ("seed_model.py", "two_v_demo/lesson_harvest.py")),
    ("trees-per-dome", "Trees per dome", "timber",
     "The frame against a mitred dome: 92 percent of the trees -- a small win, stated as small.",
     ("how many trees to build a house", "timber for a cabin", "build a cabin from your own trees"),
     ("seed_model.py", "two_v_demo/lesson_pine_value.py")),
    ("green-wood", "Green wood & drying", "timber",
     "Building with fresh-cut timber: weight, movement, checking, and why the frame forgives it.",
     ("green wood construction", "building with green logs", "wood shrinkage drying"),
     ("seed_model.py",)),
    ("timber-framing", "Timber framing", "timber",
     "The craft tradition the method sits beside: heavy members, wooden joinery, no stud walls.",
     ("timber framing", "timber frame cabin build", "traditional timber frame joinery"),
     ("book_wedge/manuscript/03-build-it-so-you-can-change-your-mind.md",)),
    ("pine-value", "What a pine is worth", "timber",
     "Standing, firewood, sawn, split, structure: the value ladder of one tree.",
     ("value of a pine tree", "timber value per tree", "stumpage price"),
     ("two_v_demo/lesson_pine_value.py",)),
    ("owner-builder", "Owner-builder", "timber",
     "One person, a chainsaw, forty hours of effort spread over months.",
     ("build your own cabin", "one man cabin build", "off grid cabin alone"),
     ("wedge_book/systems.py", "book_wedge/manuscript/front/title.md")),

    # ---- envelope --------------------------------------------------------
    ("dome-panels", "Pop-in panels", "envelope",
     "Forty identical openings; the panel set decides what the building is.",
     ("dome panels", "geodesic dome windows", "dome skylight panel"),
     ("seed_model.py", "fitout_wet.py")),
    ("shower-cap", "The shower-cap shell", "envelope",
     "One watertight outer cap over breathable layers -- a hat stack, not a sealed box.",
     ("dome cover", "geodesic dome waterproofing", "dome roof leak"),
     ("soft_shell.py", "book_wedge/manuscript/19-a-dome-is-a-head-and-it-wears-hats.md")),
    ("quilt-insulation", "Quilted insulation", "envelope",
     "Layers of recycled clothing, sewn at a kitchen table; about 132 t-shirts a layer.",
     ("recycled textile insulation", "diy insulation", "yurt insulation"),
     ("quilt_network.py", "soft_shell.py")),
    ("moisture", "Moisture & dew point", "envelope",
     "Why two waterproof layers rot a wall, and why the breather sits under the cap.",
     ("dome condensation problem", "dew point in walls", "vapor barrier mistakes"),
     ("soft_shell.py", "book_wedge/manuscript/02-water-is-the-silent-killer.md")),
    ("hull-laminate", "Boat-hull shell", "envelope",
     "Marine composites priced by weight: the rigid alternative, and why it caps the building.",
     ("fiberglass dome", "epoxy fiberglass shell", "boat building techniques house"),
     ("hull_laminate.py",)),
    ("radiative-cooling", "Radiative cooling coat", "envelope",
     "A barium-sulphate coat that runs 48 F cooler than dark; compounds with the dome's small envelope.",
     ("radiative cooling paint", "cool roof paint", "barium sulfate paint"),
     ("two_v_demo/dome_performance.py", "seed_model.py")),
    ("surface-to-volume", "Less envelope per floor", "envelope",
     "A dome encloses a floor with 41.5 percent less skin than a box.",
     ("dome energy efficiency", "surface area to volume house", "are domes more efficient"),
     ("two_v_demo/dome_advantage.py",)),

    # ---- systems ---------------------------------------------------------
    ("utility-column", "Utility column", "systems",
     "Every service comes up the middle and out through one sealed hole at the apex.",
     ("dome plumbing", "utility core house", "service core design"),
     ("column_build.py", "seed_model.py", "two_v_demo/lesson_module_build.py")),
    ("seal-cap", "Apex seal cap", "systems",
     "The one penetration in the weather surface, gasketed, opened in ten minutes.",
     ("dome roof vent", "dome apex", "roof penetration flashing"),
     ("seed_world.py",)),
    ("utility-panel", "Utility panel (polyp)", "systems",
     "Noisy, hot or weather-facing equipment outside the footprint, fed from the cap.",
     ("outdoor utility cabinet", "off grid power shed"),
     ("seed_model.py",)),
    ("off-grid-power", "Off-grid solar", "systems",
     "800 W and a 10 kWh bank against the dome's own 4.59 kWh a day.",
     ("off grid solar cabin", "tiny house solar setup", "10kwh battery off grid"),
     ("seed_model.py", "electrical.py")),
    ("rainwater", "Rain & water from the seams", "systems",
     "The seams as gutters into the pad's tank -- an experiment, reported as one.",
     ("rainwater harvesting cabin", "off grid water system", "rain catchment roof"),
     ("seed_model.py", "book_wedge/manuscript/18-the-seam-does-four-jobs.md")),
    ("modules", "Snap-in modules", "systems",
     "Shower, sink, cooktop, fridge, camera ring: modules that plug into five mounting places.",
     ("modular bathroom pod", "tiny house kitchen module"),
     ("seed_model.py", "fitout_wet.py")),

    # ---- site ------------------------------------------------------------
    ("pad", "The pad", "site",
     "A serviced platform built once by a host; the dome lands on it with four connections and a lift.",
     ("dome platform", "cabin foundation on piers", "diy deck foundation"),
     ("pad_deck.py", "park_world.py")),
    ("foundation-types", "Foundation types", "site",
     "Gravel, piers, epoxy deck, concrete ring, slab -- priced side by side.",
     ("cheapest cabin foundation", "pier vs slab foundation", "yurt platform"),
     ("pad_deck.py",)),
    ("dome-park", "Dome Park", "site",
     "An RV park for domes: hosts build pads, owners bring buildings. Foundations are 8-63 percent of a dome.",
     ("rv park for tiny homes", "tiny home community", "land lease tiny house"),
     ("dome_park.py", "park_model.py", "two_v_demo/lesson_dome_park.py")),
    ("dome-network", "The dome network", "site",
     "Hosts, owners, quilters, builders and people with trees, found through the website.",
     ("tiny house community", "land sharing tiny homes"),
     ("web/server/src/routes/network.js", "book_wedge/manuscript/22-why-a-network-beats-a-park.md")),
    ("permits-codes", "Permits & codes", "site",
     "Local, and the book says so: ask the building department before the first tree falls.",
     ("dome building permit", "geodesic dome building code", "tiny house legal"),
     ("book_wedge/manuscript/front/title.md",)),

    # ---- modular ---------------------------------------------------------
    ("stem-cell", "The stem cell dome", "modular",
     "A frame that has not decided what it is yet; the panels and modules decide.",
     ("modular dome home", "stem cell architecture", "adaptable house design"),
     ("seed_model.py", "seed_world.py", "two_v_demo/lesson_seed_pitch.py")),
    ("fit-outs", "Fifteen buildings from one frame", "modular",
     "Home, food stand, sauna, gym, studio, garage, bunker, treehouse, jacuzzi -- same frame.",
     ("dome sauna", "dome studio backyard", "dome greenhouse", "backyard dome office"),
     ("seed_model.py", "book_wedge/manuscript/30-fifteen-buildings-from-one-body.md")),
    ("adu", "Backyard ADU", "modular",
     "Most buyers already have a house: the dome as the second building.",
     ("backyard adu", "accessory dwelling unit cost", "backyard office build"),
     ("seed_model.py",)),
    ("kit-home", "Kit homes & prefab", "modular",
     "Where the dome sits against kits, prefab and shed-to-house conversions.",
     ("dome home kit", "prefab cabin kit", "cheapest kit home"),
     ("kickstarter.py",)),
    ("tiny-house", "Tiny houses", "modular",
     "The audience next door: small, owner-built, off-grid curious.",
     ("tiny house build", "tiny house on a budget", "tiny house tour"),
     ()),
    ("housing-affordability", "Housing affordability", "modular",
     "The author's aim: change the housing market for the better.",
     ("housing crisis solutions", "cheap way to build a house", "affordable housing ideas"),
     ("wedge_book/print_edition.py",)),
    ("code-a-home", "Coding a home", "modular",
     "Modular, reusable, decoupled, extensible: a house built like good software.",
     ("open source house", "open source architecture", "parametric house design"),
     ("wedge_book/print_edition.py", "two_v_demo/creator_bridge.py")),

    # ---- economics -------------------------------------------------------
    ("dome-cost", "What a dome costs", "economics",
     "Built cost, margin named as profit, per square foot -- all computed.",
     ("how much does a geodesic dome cost", "dome home cost", "cost to build a dome"),
     ("kickstarter.py", "seed_model.py", "two_v_demo/dome_costing.py")),
    ("labour-hours", "The 40-hour clock", "economics",
     "37.5 hours for the frame, 67 for the whole standard building, both on page one.",
     ("how long to build a dome", "build a cabin in a week", "40 hour cabin"),
     ("wedge_book/systems.py", "book_wedge/manuscript/front/title.md")),
    ("deferment", "Build now, finish later", "economics",
     "The deferment ladder: live in the shelter while the building grows.",
     ("build a house in stages", "pay as you go house build", "debt free house"),
     ("seed_model.py",)),
    ("kickstarter", "Kickstarter campaign", "economics",
     "Tiers, a goal that is the sum of its list, and the risks said out loud.",
     ("kickstarter housing project", "crowdfunding a house", "kickstarter tiny house"),
     ("kickstarter.py", "campaign.py", "campaign_prompts.py")),
    ("free-book", "The free book", "economics",
     "Email-gated PDF on the site; KDP paperback alongside.",
     ("free dome plans", "geodesic dome plans pdf", "dome building book"),
     ("web/server/src/routes/leads.js", "wedge_book/print_edition.py")),

    # ---- structure -------------------------------------------------------
    ("engineering", "Loads & the engineer", "structure",
     "Snow, wind, ground: an engineer's numbers, never the book's.",
     ("geodesic dome snow load", "dome wind resistance", "are domes strong"),
     ("book_wedge/manuscript/front/title.md",)),
    ("triangles-rigid", "Why triangles", "structure",
     "A triangle cannot change shape without changing a side: the whole structural argument.",
     ("why triangles are strong", "triangulation structure", "why domes are strong"),
     ("book_wedge/manuscript/04-why-it-is-triangles.md",)),
    ("floating-dome", "The floating dome", "structure",
     "Hung from three trees by a mast: a design possibility, priced not rated.",
     ("treehouse dome", "suspended treehouse", "hanging tent tree"),
     ("seed_model.py", "book_wedge/manuscript/31-hang-it-between-two-trees.md")),
    ("error-tolerance", "A frame that forgives error", "structure",
     "Error lands in the seam's key, not in the neighbours: why a lumpy frame still stands.",
     ("woodworking mistakes fix", "tolerance in construction"),
     ("book_wedge/manuscript/01-your-skull-is-not-symmetrical-either.md",)),

    # ---- media -----------------------------------------------------------
    ("film-engine", "The film engine", "media",
     "Programmatic films: every number on screen computed, every camera move code.",
     ("programmatic video", "python 3d animation", "explainer video engine"),
     ("two_v_demo/app.py", "two_v_demo/lesson_registry.py")),
    ("simulator", "The wedge simulator", "media",
     "The raw-wedge solver's 3-D world: the source of the book's figures and the cover.",
     ("3d dome simulator", "geodesic dome software", "dome design software free"),
     ("geodesic_raw_wedge_dome_dihedral.py", "two_v_demo/raw_wedge_bridge.py")),
    ("lumen", "Lumen the mascot", "media",
     "A low-poly jellyfish with its own voice who carries the jokes and the warmth.",
     ("mascot explainer video", "animated mascot youtube"),
     ("two_v_demo/mascot.py",)),
    ("the-book", "Geodesic Dome Wedge Method", "media",
     "The 40 Hour Cabin: 176 pages, every figure computed, KDP-ready.",
     ("geodesic dome book", "how to build a dome book", "cabin building book"),
     ("wedge_book/print_edition.py", "wedge_book/cover_scene.py")),
    ("cinematic-reveal", "Cinematic reveal shots", "media",
     "Hook-first footage: the build from nothing, the orbit at golden hour, the macro of a seam.",
     ("cinematic build video", "time lapse cabin build", "cinematic woodworking"),
     ("wedge_book/cover_scene.py", "two_v_demo/drama_camera.py")),
    ("frankendome", "The Frankendome", "media",
     "The first dome, lumpy and patched: the origin story the films keep.",
     ("first dome build fail", "diy dome mistakes"),
     ("frankendome_masterclass.py", "two_v_demo/lesson_franken.py")),
]

# (source, target, relation)
EDGES: list[tuple[str, str, str]] = [
    ("geodesic-dome", "2v-frequency", "chooses"), ("icosahedron", "geodesic-dome", "subdivides into"),
    ("2v-frequency", "chord-factors", "sets"), ("2v-frequency", "dihedral-angle", "sets"),
    ("geodesic-dome", "frequency-families", "compared with"), ("geodesic-dome", "zome", "compared with"),
    ("geodesic-dome", "hex-dome", "same family"), ("icosahedron", "hex-dome", "twelve pentagons"),
    ("2v-frequency", "wedge-member", "framed with"), ("wedge-member", "hubless", "enables"),
    ("hubless", "pinwheel-joint", "by way of"), ("pinwheel-joint", "panelized-dome", "makes"),
    ("panelized-dome", "seam-key", "leaves"), ("seam-key", "seam-channel", "opens as"),
    ("dihedral-angle", "seam-key", "sizes"), ("wedge-member", "compound-cut", "needs"),
    ("panelized-dome", "assembly-jig", "built on"), ("wedge-member", "wedge-orientation", "placed by"),
    ("chainsaw-ripping", "wedge-member", "produces"), ("log-yield", "wedge-member", "argues for"),
    ("log-yield", "trees-per-dome", "feeds"), ("pine-value", "log-yield", "explains"),
    ("green-wood", "wedge-member", "material of"), ("timber-framing", "wedge-member", "tradition of"),
    ("owner-builder", "chainsaw-ripping", "does"), ("owner-builder", "labour-hours", "measured by"),
    ("panelized-dome", "dome-panels", "closed by"), ("dome-panels", "shower-cap", "under"),
    ("shower-cap", "quilt-insulation", "covers"), ("shower-cap", "moisture", "answers"),
    ("shower-cap", "hull-laminate", "compared with"), ("radiative-cooling", "shower-cap", "coats"),
    ("surface-to-volume", "geodesic-dome", "property of"),
    ("seam-channel", "rainwater", "carries"), ("seam-channel", "utility-column", "feeds"),
    ("utility-column", "seal-cap", "ends in"), ("seal-cap", "utility-panel", "feeds"),
    ("utility-column", "modules", "hosts"), ("utility-panel", "off-grid-power", "houses"),
    ("rainwater", "pad", "stored in"),
    ("pad", "utility-column", "services"), ("pad", "foundation-types", "built as"),
    ("pad", "dome-park", "unit of"), ("dome-park", "dome-network", "grows into"),
    ("pad", "permits-codes", "subject to"), ("quilt-insulation", "dome-network", "made by"),
    ("stem-cell", "fit-outs", "becomes"), ("dome-panels", "stem-cell", "defines"),
    ("stem-cell", "adu", "sold as"), ("stem-cell", "kit-home", "compared with"),
    ("stem-cell", "tiny-house", "neighbour of"), ("code-a-home", "stem-cell", "philosophy of"),
    ("stem-cell", "housing-affordability", "aims at"), ("modules", "fit-outs", "make"),
    ("stem-cell", "dome-cost", "priced in"), ("dome-cost", "kickstarter", "funds"),
    ("labour-hours", "dome-cost", "part of"), ("deferment", "dome-cost", "spreads"),
    ("dome-park", "dome-cost", "halves foundation"), ("free-book", "kickstarter", "audience for"),
    ("triangles-rigid", "geodesic-dome", "why"), ("error-tolerance", "seam-key", "absorbed by"),
    ("engineering", "floating-dome", "rates"), ("utility-column", "floating-dome", "holds the mast"),
    ("engineering", "permits-codes", "required by"),
    ("simulator", "pinwheel-joint", "solves"), ("simulator", "the-book", "illustrates"),
    ("film-engine", "simulator", "draws"), ("lumen", "film-engine", "stars in"),
    ("the-book", "free-book", "given as"), ("cinematic-reveal", "film-engine", "shot with"),
    ("frankendome", "error-tolerance", "proves"), ("the-book", "labour-hours", "titled by"),
]


def build() -> dict:
    ids = [n[0] for n in NODES]
    assert len(ids) == len(set(ids)), "duplicate node id"
    missing_files = [(n[0], f) for n in NODES for f in n[5] if not (ROOT / f).exists()]
    assert not missing_files, f"graph names files that do not exist: {missing_files}"
    for a, b, _ in EDGES:
        assert a in ids and b in ids, f"edge to an unknown node: {a} -> {b}"
    assert all(n[2] in CATEGORIES for n in NODES)
    return {
        "categories": [{"id": k, "label": v[0], "blurb": v[1]} for k, v in CATEGORIES.items()],
        "nodes": [{"id": i, "label": l, "category": c, "summary": s, "seeds": list(seeds),
                   "files": list(files), "order": k, "status": "seed", "notes": ""}
                  for k, (i, l, c, s, seeds, files) in enumerate(NODES)],
        "edges": [{"id": f"{a}__{b}", "source": a, "target": b, "relation": r} for a, b, r in EDGES],
    }


def main() -> int:
    graph = build()
    OUT.write_text(json.dumps(graph, indent=1), encoding="utf-8")
    print(f"{OUT.relative_to(ROOT)}: {len(graph['nodes'])} keywords, {len(graph['edges'])} links, "
          f"{sum(len(n['seeds']) for n in graph['nodes'])} search phrases")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
