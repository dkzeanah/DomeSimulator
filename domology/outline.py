"""Domology's structure: three books, twenty-nine chapters, in order, as data.

Each chapter says what it is for (``purpose``), how long it should run
(``target``, in words), which illustrations it carries (``plates``, ids from
:mod:`plates`) and which worked-math boxes it prints (``sheets``, keys of
:data:`science.SHEETS`). The build checks the manuscript against this: a plate
the plan promises but the prose never places is reported, and so is one the
prose places that the plan does not know.

The three books are three reading speeds, and a reader can take any one alone:

* **Book One, The Dome** -- why the shape works. Geometry and physics, argued
  with computed numbers; skippable by anyone who only wants to build.
* **Book Two, The Journey** -- how this project found its methods, tool by
  tool, from a walkable simulator to a dome cut from two trees. Its dates are
  read from the repository's history.
* **Book Three, The Build** -- do this, then this. Follow it and you get a
  dome.

Chapter numbers are continuous across the three books, and prose never types
one: it writes ``{{dmch.wedge}}``, so inserting a chapter cannot leave a
cross-reference pointing at the wrong place.
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from . import config


@dataclass(frozen=True)
class ChapterPlan:
    id: str
    title: str
    deck: str
    purpose: str
    target: int = 2000
    plates: tuple[str, ...] = ()
    sheets: tuple[str, ...] = ()
    opener: str | None = None


@dataclass(frozen=True)
class BookPlan:
    number: int
    key: str
    name: str
    promise: str
    plate: str
    chapters: tuple[ChapterPlan, ...]


FRONT: tuple[ChapterPlan, ...] = (
    ChapterPlan(
        "how-to-read", "Three Books in One",
        "How to read this book, and what every number in it promises.",
        "Explain the three books and the three reading speeds; the promise that every "
        "number is computed by the project's code; the margin notes; the plates made by "
        "the project's own tools; and the yellow author boxes in drafts.",
        900),
    ChapterPlan(
        "creed", "The Round House Creed",
        "The argument this whole project was built to make.",
        "The author's creed, in the author's words, exactly as the project published it.",
        450),
)


BOOKS: tuple[BookPlan, ...] = (
    BookPlan(1, "dome", "The Dome",
             "Why the geodesic dome encloses the most, with the least, from the fewest parts.",
             "divider-dome",
             (
                 ChapterPlan(
                     "enclose", "The Shape That Encloses the Most",
                     "Half a sphere is the cheapest wall there is, and the numbers say by how much.",
                     "Make the efficiency case from geometry first (sphere against cube, "
                     "hemisphere against a box house on the same floor), then from priced "
                     "quantities, and print where the saving stops: a finished home saves far "
                     "less than a bare shell because the fit-out is the same.",
                     2400, ("creator-lineup", "chart-skin", "chart-comparison"),
                     ("sphere_box", "efficiency", "comparisons"), opener="creator-lineup"),
                 ChapterPlan(
                     "triangle", "Triangles Do Not Rack",
                     "Why forty triangles hold what forty squares cannot.",
                     "Rigidity: a triangle's shape is fixed by its side lengths; a square's is "
                     "not. Load paths through a triangulated shell, members in compression and "
                     "tension, and why the joint -- not the stick -- is the question.",
                     1900, ("rigidity", "force-panel", "classes-colored"), (),
                     opener="rigidity"),
                 ChapterPlan(
                     "icosahedron", "Twelve Points and a Golden Ratio",
                     "Every geodesic dome begins as the most symmetrical solid there is.",
                     "The five Platonic solids; why the icosahedron; its twelve vertices from "
                     "phi; normalizing onto a sphere; Euler's count.",
                     2000, ("platonic", "ico-coordinates"), ("phi", "normalize", "euler"),
                     opener="platonic"),
                 ChapterPlan(
                     "subdivide", "Divide, Push, Repeat",
                     "How a flat solid becomes a sphere: split every edge and push the new points out.",
                     "Midpoint subdivision and projection; chord factors; what raising the "
                     "frequency buys and costs; why even frequencies cut at the equator.",
                     2100, ("midpoints", "projection", "chart-frequency"),
                     ("midpoint", "project", "chords", "frequency"), opener="projection"),
                 ChapterPlan(
                     "two-lengths", "Two Lengths, Forty Triangles",
                     "The 2V hemisphere: sixty-five edges, two lengths, two shapes, two jigs.",
                     "Count the 2V hemisphere; the reference dome from a 72-inch board; the two "
                     "triangle shapes and the two jigs that make all forty.",
                     2200, ("classes-dome", "forge-jig-shop", "cutlist"),
                     ("counts", "reference", "jigs"), opener="classes-dome"),
                 ChapterPlan(
                     "deficit", "The Missing Fifteen Degrees",
                     "Why flat triangles curve, and where the curve is hiding.",
                     "Angular deficit at five- and six-way hubs; Descartes' 720 degrees; why a "
                     "flat fan rises; cover patterns and their darts; twelve pentagons always.",
                     2000, ("forge-deficit", "forge-pattern", "hex-deficit"),
                     ("deficit", "pentagons"), opener="forge-deficit"),
                 ChapterPlan(
                     "joints", "Hubs, Hubless, and the Seam",
                     "Where a dome actually fails, and three honest ways to join one.",
                     "Hub-and-strut; hubless bolted triangles with doubled seams; the compound "
                     "cut and why it is hard; hourglass waist joints; what each asks of a shop.",
                     2200, ("hub-dome", "forge-hubless", "compound-cut", "forge-waist"),
                     ("hub_vs_hubless", "hubless"), opener="forge-hubless"),
                 ChapterPlan(
                     "weather", "Wind, Water, and Weight",
                     "What the shape does for you when the weather turns, and what it does not.",
                     "Wind around a round body; the leaky-dome problem turned into plumbing "
                     "(dished panels, micro-drains, seam veins, a collector and a cistern); "
                     "snow and the honest limits of what this project has tested.",
                     2000, ("kick-wind", "forge-water", "forge-rain"), (), opener="forge-water"),
                 ChapterPlan(
                     "family", "The Dome Family",
                     "Hex, zome, and higher frequencies: when a different dome is the better answer.",
                     "Goldberg hex cages, zomes with one strut length, the twelve preset designs "
                     "measured side by side, and how to choose.",
                     1900, ("hex-soccer", "zome-star", "creator-framing"),
                     ("catalogue", "size"), opener="hex-soccer"),
                 ChapterPlan(
                     "cost", "What a Dome Costs, and What It Saves",
                     "The honest arithmetic: where the shape saves money, and where it stops.",
                     "Cost per square foot across the catalogue; the dome against a box on one "
                     "rate card; where a house's money goes; what building it yourself changes.",
                     2200, ("creator-economics", "why-dome", "chart-house"),
                     ("catalogue_cost", "house_sources", "score"), opener="why-dome"),
             )),
    BookPlan(2, "journey", "The Journey",
             "How one person built a dome in software before building one in wood, and what "
             "each tool taught.",
             "divider-journey",
             (
                 ChapterPlan(
                     "simulator", "A Dome in Software First",
                     "A walkable world where a dome could be built, priced and argued with "
                     "before a single cut.",
                     "The project's first weeks, dated from its history: the Dome Creator, "
                     "presets, the live bill of materials, why a simulator came before a saw.",
                     1900, ("creator-homestead", "creator-trunk"), ("catalogue",),
                     opener="creator-homestead"),
                 ChapterPlan(
                     "factory", "The Factory Line",
                     "Fifteen stations, four products, and the question an investor asks.",
                     "The assembly line: station order, the factory case, labor limb by limb, "
                     "and what a line teaches a person building one dome alone.",
                     1900, ("line-frame", "line-services", "line-interior"), (),
                     opener="line-frame"),
                 ChapterPlan(
                     "teaching", "Teaching the Geometry to Myself",
                     "A film engine, a lesson from scratch, and the rule that every number on "
                     "screen is computed.",
                     "The masterclass engine and the from-scratch lesson; math screens; the "
                     "discipline of computed numbers and corrections on camera; this book as "
                     "the same machinery on paper.",
                     1800, ("scratch-pipeline", "math-screen"), ("scale",),
                     opener="scratch-pipeline"),
                 ChapterPlan(
                     "forge", "Dome Forge and the Water Dome",
                     "Layers, hubless triangles, a jig shop, and seams that drink the rain.",
                     "Dome Forge as a thinking tool: per-triangle make-up, mixed profiles, "
                     "pentagons and hourglasses, cover patterns and nesting.",
                     2000, ("forge-layers", "forge-panel", "forge-pentagon", "forge-nesting"),
                     (), opener="forge-layers"),
                 ChapterPlan(
                     "frankendome", "The Frankendome",
                     "Strut-agnostic, asymmetric, joined from the top down: it stood, and it taught.",
                     "The build before the wedge: any stick anywhere, V-brackets, the ten-piece "
                     "pentagon, slack and settling, and why nothing that does not repeat can "
                     "be jigged.",
                     2000, ("franken-bracket", "franken-triangle", "franken-slack"), (),
                     opener="franken-triangle"),
                 ChapterPlan(
                     "wedge", "The Cut That Changed It",
                     "One chainsaw, eight sectors, and most of the tree kept.",
                     "The radial wedge: recovery against square milling, the machines that drop "
                     "out, the fifteen middlemen, the four orientations.",
                     2300, ("wedge-split", "wedge-round", "wedge-orient", "wedge-chain"),
                     ("yield", "mills", "middlemen", "orientation"), opener="wedge-split"),
                 ChapterPlan(
                     "two-trees", "Two Trees and a Fortnight",
                     "Size the dome to the tree, then give it fourteen days.",
                     "Tree-first sizing, the harvest, the measured cutting rate, the fortnight "
                     "plan, and what the shell is worth -- with every figure labelled as "
                     "measured, published or the author's.",
                     2300, ("harvest-explode", "solved-dome", "pine-ladder"),
                     ("harvest_measured", "rate", "pine_sources"), opener="harvest-explode"),
                 ChapterPlan(
                     "corrections", "What I Got Wrong, and What Is Still Unproven",
                     "The claims that did not survive, and the tests still to run.",
                     "The mitre claim, the labor-rate comparison and the bending strength, "
                     "each named before it is fixed; then an honest list of what has not been "
                     "measured yet.",
                     1800, ("buttcut", "wedge-stick"), ("structure", "buttcut"),
                     opener="buttcut"),
             )),
    BookPlan(3, "build", "The Build",
             "A guide to building a wedge dome the way it was built here, from choosing a tree "
             "to closing the shell.",
             "divider-build",
             (
                 ChapterPlan(
                     "plan", "Plan: Size, Site, and the Two Methods",
                     "Decide the dome from the floor you want, or from the tree you have.",
                     "Method A (floor first) and Method B (tree first) worked in full; site, "
                     "permits and the limits of this book.",
                     2200, ("method-dome", "dome-top"), (), opener="method-dome"),
                 ChapterPlan(
                     "tools", "Tools, Stock, and Safety",
                     "One chainsaw, a flat board, and the few things you cannot skip.",
                     "The kit; the wedge against the board; fasteners and the gasket; the "
                     "safety rules that are not optional.",
                     1700, ("wedge-section", "tool-chain"), (), opener="wedge-section"),
                 ChapterPlan(
                     "harvest", "Harvest: Fell, Buck, Split",
                     "Turning two standing pines into a pile of struts.",
                     "Felling, bucking to length, splitting to sectors, fuel and time -- as "
                     "numbered steps with safety boxes.",
                     2200, ("harvest-fell", "harvest-buck", "harvest-pile"), (),
                     opener="harvest-fell"),
                 ChapterPlan(
                     "jig", "Build the Jig",
                     "Solve the geometry once, in plywood, so you never solve it again.",
                     "The pinwheel jig: layout, stops, locate first and cut second.",
                     1800, ("jig-panel", "jig-stages"), ("wedge_jig",), opener="jig-panel"),
                 ChapterPlan(
                     "panels", "Forty Panels",
                     "Butt cut, head overfit, flush cut: one panel, forty times.",
                     "The panel procedure in order, batching, and checking each panel.",
                     2100, ("pinwheel", "panel-drawing", "flush-cut"), ("buttcut",),
                     opener="pinwheel"),
                 ChapterPlan(
                     "seams", "Seams, Keys, and the Fold",
                     "Where two panels meet, and why the key holds the angle.",
                     "Gaskets, keys, the two fold angles, and assembling a seam.",
                     1800, ("gasket", "keystone", "fold"), ("dihedral",), opener="gasket"),
                 ChapterPlan(
                     "foundation", "The Footing and the Ring",
                     "A level ring is most of a dome's foundation.",
                     "Footings, the base ring, riser walls, and checking level.",
                     1700, ("foundation", "riser"), (), opener="foundation"),
                 ChapterPlan(
                     "raise", "Raise the Shell",
                     "Ring by ring from the ground up, stable at every step.",
                     "Assembly order, temporary support, the apex, and checks as you go.",
                     2000, ("raise", "apex", "assemble"), (), opener="raise"),
                 ChapterPlan(
                     "close", "Skin, Openings, and Water",
                     "Close the shell against the weather, and let the seams drink the rain.",
                     "Skinning, doors and windows, the water path, and inspection.",
                     2000, ("skin", "openings", "forge-veins"), (), opener="skin"),
                 ChapterPlan(
                     "inside", "Inside a Round Room",
                     "Light, power, heat and furniture in a room with no corners.",
                     "Living in the finished dome: layout, the service column, small power, "
                     "heating a sphere, and furnishing curved walls.",
                     1700, ("look-room", "line-interior-room"), (), opener="look-room"),
                 ChapterPlan(
                     "check", "Check, Correct, Record",
                     "Where the error goes, how to measure the finished dome, and what to write down.",
                     "Tolerances and where they accumulate, measuring the built dome, the "
                     "records worth keeping, and reporting back.",
                     1700, ("check", "error"), ("defects",), opener="check"),
             )),
)


BACK: tuple[ChapterPlan, ...] = (
    ChapterPlan("worksheets", "Worksheets",
                "Blank forms for the tree register, the member log and the time and money.",
                "Printable tables to fill in at the bench.", 300),
    ChapterPlan("glossary", "Glossary", "The words beside the cuts.",
                "Generated from the project's lexicon: every term the book uses.", 0),
    ChapterPlan("numbers", "The Numbers Behind This Book",
                "Every live figure the book quotes, its value, and what computes it.",
                "Generated: the proof that the book and the code agree.", 0),
    ChapterPlan("plates-index", "The Plates",
                "Every illustration, the tool that rendered it, and what was changed to make it.",
                "Generated from the plate catalogue.", 0),
    ChapterPlan("sources", "Sources, Assumptions, and Corrections",
                "What each figure rests on, and what has been corrected.",
                "The published sources, the author's own figures and the estimates, each "
                "labelled; and the corrections log.", 800),
    ChapterPlan("tools", "The Tools",
                "Every program that made this book, and how to run it yourself.",
                "A plain-language guide to the launcher and each tool.", 900),
    ChapterPlan("about", "About the Author", "", "The author's own words.", 250),
    ChapterPlan("next", "What Comes Next", "More domes, more films, more of the story.",
                "Teasers and callbacks: the films that go with each chapter, and what is "
                "being built next.", 450),
)

GENERATED = ("glossary", "numbers", "plates-index")
"""Back-matter chapters the build writes itself, from code."""


def all_chapters() -> list[tuple[str, ChapterPlan, BookPlan | None]]:
    """(section, plan, book) for every chapter in reading order."""
    rows = [("front", plan, None) for plan in FRONT]
    for book in BOOKS:
        rows += [("body", plan, book) for plan in book.chapters]
    rows += [("back", plan, None) for plan in BACK]
    return rows


def chapter_numbers() -> dict[str, int]:
    numbers = {}
    count = 0
    for book in BOOKS:
        for plan in book.chapters:
            count += 1
            numbers[plan.id] = count
    return numbers


def chapter_tokens() -> dict[str, str]:
    """``{{dmch.<id>}}`` -> the chapter's number, for cross-references."""
    return {f"dmch.{cid.replace('-', '_')}": str(number)
            for cid, number in chapter_numbers().items()}


def manuscript_path(plan: ChapterPlan, book: BookPlan | None, section: str) -> Path:
    if section == "front":
        return config.MANUSCRIPT / "0-front" / f"{plan.id}.md"
    if section == "back":
        return config.MANUSCRIPT / "4-back" / f"{plan.id}.md"
    number = chapter_numbers()[plan.id]
    return config.MANUSCRIPT / f"{book.number}-{book.key}" / f"{number:02d}-{plan.id}.md"


def by_id() -> dict[str, tuple[str, ChapterPlan, BookPlan | None]]:
    return {plan.id: (section, plan, book) for section, plan, book in all_chapters()}


def scaffold(section: str, plan: ChapterPlan, book: BookPlan | None) -> str:
    """A starting file for a chapter: its header and its brief, never prose."""
    lines = ["---", f"id: {plan.id}", f"title: {plan.title}"]
    if plan.deck:
        lines.append(f"deck: {plan.deck}")
    if plan.opener:
        lines.append(f"opener: {plan.opener}")
    lines += ["status: outline", f"target: {plan.target}", "---",
              f"<!-- Purpose: {plan.purpose} -->", ""]
    for plate in plan.plates:
        if plate != plan.opener:
            lines += [f"[[plate: {plate}]]", ""]
    for sheet in plan.sheets:
        lines += [f"[[math: {sheet}]]", ""]
    return "\n".join(lines)


def validate_outline() -> None:
    ids = [plan.id for _section, plan, _book in all_chapters()]
    assert len(ids) == len(set(ids)), "a chapter id is used twice"
    assert sum(len(book.chapters) for book in BOOKS) == len(chapter_numbers())
    from . import science
    for _section, plan, _book in all_chapters():
        for sheet in plan.sheets:
            assert sheet in science.SHEETS, (plan.id, sheet)
        if plan.opener:
            assert plan.opener in plan.plates, (plan.id, plan.opener)
