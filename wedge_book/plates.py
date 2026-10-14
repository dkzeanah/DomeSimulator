"""The book's other pictures: frames taken out of this project's films.

:mod:`wedge_book.figures` operates one tool -- the raw-wedge solver -- and it
is the right tool for anything about the frame. It is the wrong tool, or no
tool at all, for two thirds of what a book about building a dome has to show.
It has no doorway. It has no foundation. It does not know the utility column
exists, it builds 2V hemispheres and nothing else, and it has never seen a
sheet of plywood.

All of that exists here. This repository has thirty-seven published films and
between them they draw the openings, the pad, the column and its seal cap, the
quilted layers, the frequencies, eight cross sections, eight frame materials,
sixteen panel types, nine claddings and seven foundations -- each one already
solved, already costed, already narrated.

So a plate is **a frame of a film**, taken at a named chapter of a named
lesson. Three things follow from that and all three are the point:

* **the geometry is the films' geometry.** ``all_domes`` draws the Dome
  Creator's real meshes; ``seed_pitch`` draws seed_world's column and cap;
  ``build`` draws the construction lesson's openings. None of it is redrawn
  for the book;
* **the caption is the film's own words.** A chapter carries a title, a
  promise and its narration, and the plate's caption is made of those rather
  than written beside the picture. A film that is corrected corrects the book;
* **the breadth comes free.** The chapter of ``all_domes`` that shows eight
  cross sections is one plate, and it shows eight cross sections.

WHAT A PLATE COSTS

A film frame is a film frame: it carries the film's chrome -- its title cards,
its callouts, its mascot. That is a real difference from the solver figures,
which are the bare world. The book says which is which, because a reader who
sees both should know that one is a photograph of a tool and the other is a
still from a video.
"""

from __future__ import annotations

import json
import shutil
import subprocess
import sys
from dataclasses import dataclass, field
from pathlib import Path

from . import store

ROOT = store.ROOT
FIGURE_DIR = store.BOOK_DIR / "figures"
SHOT_DIR = ROOT / "two_v_demo_output"

#: The films need Python 3.12; one of their modules uses a quoted f-string
#: expression that 3.11 cannot parse. Stated here rather than discovered at
#: render time, an hour in.
PYTHON = "py"
PYTHON_ARGS = ("-3.12",)


@dataclass(frozen=True)
class Plate:
    """One frame of one film, and where it goes in the book."""

    key: str
    lesson: str
    chapter: str
    book_chapter: int
    plan: str = ""
    #: How far through the film's chapter to take the frame. Two thirds by
    #: default, because a chapter's first second is usually its title card
    #: arriving and its last is the next one starting.
    at: float = 0.66
    #: Written only when the film's own title or promise is wrong for a book.
    title: str = ""
    caption: str = ""
    #: What this plate is showing that the solver cannot.
    why: str = ""
    #: True for a frontispiece: the world with no text on it at all.
    bare: bool = False

    @property
    def path(self) -> Path:
        return FIGURE_DIR / f"{self.key}.png"

    def full_caption(self, lesson=None) -> str:
        """The film's own words, unless this plate overrides them."""
        text = self.caption
        if not text and lesson is not None:
            chapter = find_chapter(lesson, self.chapter)
            bits = [chapter.promise.rstrip(".")]
            if chapter.narration:
                first = chapter.narration[0].strip().rstrip(".")
                if first and first.lower() not in bits[0].lower():
                    bits.append(first)
            text = ". ".join(bits)
        return (f"{text.rstrip('.')}. From "
                f"{lesson.title if lesson is not None else self.lesson}, "
                f"a film in this project. {store.CREDIT}")


# ----------------------------------------------------------------------
# Reading the films
# ----------------------------------------------------------------------

def lessons() -> dict:
    from two_v_demo.lesson_registry import LESSONS

    return LESSONS


def find_chapter(lesson, slug: str):
    for chapter in lesson.chapters:
        if chapter.slug == slug:
            return chapter
    raise KeyError(
        f"{lesson.key} has no chapter {slug!r}; it has "
        f"{[c.slug for c in lesson.chapters][:8]}...")


def shot_time(lesson, slug: str, at: float) -> float:
    """When in the film to take the frame, from the film's own durations."""
    elapsed = 0.0
    for chapter in lesson.chapters:
        if chapter.slug == slug:
            return elapsed + chapter.duration * min(max(at, 0.02), 0.96)
        elapsed += chapter.duration
    raise KeyError(slug)


# ----------------------------------------------------------------------
# The catalogue
# ----------------------------------------------------------------------

PLATES: tuple[Plate, ...] = (
    # -- 1. Why build a dome ------------------------------------------
    Plate("plate-why-hour", "why_build", "question", 1,
          why="the economic case, which no geometry tool can draw"),
    Plate("plate-the-room", "look", "room", 1,
          plan="Simple triangle-to-curved-shell explanation diagram",
          why="what the inside of one is actually like, furnished"),

    # -- 2. The wedge method ------------------------------------------
    Plate("plate-stop-squaring", "wedge", "split", 13,
          plan="Log divided into wedge members",
          why="the round log being split, which the solver starts after"),
    Plate("plate-round-log-corners", "why", "round", 13,
          plan="Conventional rectangular strut versus wedge strut",
          why="the square section a sawmill cuts out of a round log, and "
              "what it throws away"),
    Plate("plate-tree-is-the-product", "why_build", "tree", 13,
          plan="Log divided into wedge members",
          why="the whole tree, before anything is taken out of it"),

    # -- 3. Geometry ---------------------------------------------------
    Plate("plate-frequency", "world", "math_frequency", 63,
          plan="Frequency and truncation comparison silhouettes",
          why="2V against 3V and 4V, which this solver does not build"),
    Plate("plate-frequency-cost", "world", "ladder", 63,
          plan="Frequency and truncation comparison silhouettes",
          why="what each frequency costs, counted"),

    # -- 4. Materials --------------------------------------------------
    Plate("plate-two-trees", "harvest", "tree", 13,
          plan="Grain/defect examples for member selection",
          why="the standing timber a frame comes out of"),
    Plate("plate-eight-materials", "all_domes", "materials", 61,
          plan="Nominal versus actual lumber cross-section",
          why="eight frame materials priced against each other -- steel, "
              "aluminium, timber, whole trunk, PVC, bamboo"),
    Plate("plate-eight-sections", "all_domes", "shapes", 61,
          plan="Conventional rectangular strut versus wedge strut",
          why="eight strut cross sections side by side, including the "
              "rectangular stick this method is an argument against"),
    Plate("plate-recovery", "pine_value", "recovery", 13,
          plan="Log divided into wedge members",
          why="how much of a log survives splitting against sawing"),

    # -- 5. Turning timber into wedges ---------------------------------
    Plate("plate-blade-tilt", "cuts", "tilt", 24,
          plan="Dimensional-lumber wedge-cutting layouts",
          why="the saw being set, which is the operation the book is "
              "describing"),
    Plate("plate-two-machines", "cuts", "machines", 24,
          plan="Saw/jig sequence for repetitive wedge production",
          why="why the cut takes two machines"),

    # -- 7. Connections ------------------------------------------------
    Plate("plate-gasket", "wedge", "gasket", 20,
          plan="Exploded fastener/plate alternatives",
          why="the gasket doing the shaving, which is the alternative to a "
              "machined key"),
    Plate("plate-six-joints", "all_domes", "styles", 20,
          plan="Exploded fastener/plate alternatives",
          why="six ways to join the same sticks, which is the whole "
              "alternatives question in one frame"),

    # -- 8 and 12. The ground -------------------------------------------
    Plate("plate-meeting-the-ground", "build", "foundation", 39,
          plan="Slab/ring/pier/raised-floor comparison sections",
          why="four foundations in section, which nothing here renders"),
    Plate("plate-seven-foundations", "all_domes", "foundations", 39,
          plan="Slab/ring/pier/raised-floor comparison sections",
          why="seven foundations priced against each other"),
    Plate("plate-the-pad", "seed_pitch", "deck", 85,
          plan="Prepared dome pad",
          why="the platform built one course at a time"),
    Plate("plate-pad-is-not-yours", "seed_pitch", "pad", 42,
          plan="Prepared dome pad",
          why="the pad as a thing somebody else owns"),

    # -- 9. Assembly ----------------------------------------------------
    Plate("plate-one-dome-step-by-step", "all_domes", "build", 22,
          plan="Temporary bracing and raising sequence",
          why="a dome going up in phases, which the wedge solver cannot "
              "show part-built"),
    Plate("plate-station", "line", "station", 22,
          why="one station of an assembly line, because forty identical "
              "panels is a production question"),

    # -- 10. Openings ---------------------------------------------------
    Plate("plate-openings", "build", "openings", 26,
          plan="Door opening",
          why="doors and windows, and what not to cut"),
    Plate("plate-openings-zome", "zome", "openings", 26,
          plan="Window-frame integration diagram",
          why="the same problem on a different geometry, which is how to "
              "tell a rule from a habit"),

    # -- 11. Panels and shells ------------------------------------------
    Plate("plate-sixteen-panels", "all_domes", "panels", 61,
          plan="Removable panel",
          why="sixteen panel types -- ply, glass, acrylic, twinwall, SIP, "
              "shingle, metal, solar, canvas, mirror, precast"),
    Plate("plate-nine-claddings", "all_domes", "layers", 61,
          plan="Insulated panel",
          why="nine cladding layers over the same shell"),
    Plate("plate-shower-cap", "seed_pitch", "cap", 2,
          plan="Panel-to-wedge weather-seal detail",
          why="one watertight layer over everything else, which is the "
              "shell strategy this book recommends"),
    Plate("plate-quilt", "seed_pitch", "quilt", 31,
          plan="Insulated panel",
          why="the insulation as a removable quilted layer"),
    Plate("plate-four-skins", "seed_pitch", "shell_cost", 29,
          why="four ways to skin the same frame, priced"),
    Plate("plate-sheet-problem", "seed_pitch", "sheet", 29,
          why="what a four-foot sheet does to a dome sized from its member"),

    # -- 13. Utilities ---------------------------------------------------
    Plate("plate-core-socket", "seed_pitch", "core", 85,
          plan="Utility column",
          why="the utility column, which lives in seed_world and not in the "
              "wedge solver"),
    Plate("plate-build-a-core", "module_build", "chase", 67,
          plan="Utility column",
          why="a core being built on a bench, service by service"),
    Plate("plate-core-cap", "module_build", "close", 67,
          plan="Gasketed service cap",
          why="the cap proved and the core stood up"),
    Plate("plate-shared-services", "byod", "shared", 67,
          plan="Floor utility interface",
          why="what a site shares and what each dome brings"),
    Plate("plate-polyps", "seed_pitch", "polyps", 66,
          why="services that hang off the outside instead of going through "
              "the wall"),

    # -- 14. Environmental control ----------------------------------------
    Plate("plate-layering", "seed_pitch", "layering", 31,
          plan="Insulation/ventilation/condensation path section",
          why="the envelope gaining a layer a winter"),
    Plate("plate-furnished", "look", "furnished", 85,
          plan="Completed dome cutaway",
          why="the finished inside, which is the nearest thing to a cutaway "
              "any tool here makes"),

    # -- 15 to 18. Variations, configurations, modules, platform ----------
    Plate("plate-hex", "hex", "one_hexagon", 58,
          why="a hexagonal dome: the same argument, different tiling"),
    Plate("plate-zome", "zome", "sweep", 55,
          why="a zome, where every panel is a flat parallelogram"),
    Plate("plate-twelve-domes", "all_domes", "open", 85,
          plan="Frequency and truncation comparison silhouettes",
          why="twelve finished buildings from one tool"),
    Plate("plate-swap-everything", "hype6", "swap", 3,
          plan="Removable panel",
          why="panels swapped without touching the frame"),
    Plate("plate-core-moves", "seed_pitch", "modular", 67,
          plan="Prefabricated triangle module",
          why="the core lifted out and carried to the next dome"),
    Plate("plate-mast-and-floor", "seed_pitch", "mast", 76,
          why="a mast through the column and a floor clamped to it"),
    Plate("plate-floating", "seed_pitch", "floating", 76,
          why="the dome hung between two trees, priced and not rated"),
    Plate("plate-catalogue", "seed_pitch", "catalogue", 69,
          why="the other buildings a homestead wants"),

    # -- 19 and 20. Reference --------------------------------------------
    Plate("plate-price-line-by-line", "seed_pitch", "price", 83,
          plan="Material-yield worksheet example",
          why="the whole invoice, line by line"),
    Plate("plate-yield", "why", "yield", 16,
          plan="Material-yield worksheet example",
          why="how much of the tree survives, measured"),
    Plate("plate-factors-to-lumber", "scratch", "m_scale", 16,
          plan="Cut-list worksheet example",
          why="chord factors turning into a cut list"),
    Plate("plate-against-itself", "seed_pitch", "against", 83,
          why="the three things the model says against its own argument"),
# -- the geometry, derived on screen --------------------------------
    Plate("plate-why-triangles", "scratch", "why_triangles", 6,
          why="why the shape is triangles at all, before any dome"),
    Plate("plate-icosahedron", "scratch", "why_ico", 6,
          why="the solid the whole thing starts from, and why that one"),
    Plate("plate-phi", "scratch", "m_phi", 7,
          plan="Center/radius/base-polygon layout diagram",
          why="twelve points placed by one irrational number -- the golden "
              "ratio's actual job in this method"),
    Plate("plate-project", "scratch", "project", 11,
          why="the push that turns a subdivided icosahedron into a sphere"),
    Plate("plate-chords-four-ways", "scratch", "m_chords", 9,
          why="the two chord factors derived four independent ways and "
              "cross-checked against each other"),
    Plate("plate-hemisphere", "scratch", "hemisphere", 10,
          why="where a sphere gets cut to become a building"),
    Plate("plate-counting", "scratch", "m_counts", 10,
          why="every part of the building counted from the topology"),
    Plate("plate-cross-check", "scratch", "cross_check", 9,
          why="two ways of computing the same number, and the residual "
              "between them"),

    # -- other shapes ----------------------------------------------------
    Plate("plate-zome-what", "zome", "what", 55,
          why="a zome is not a piece of a sphere, and the difference is "
              "the whole of why its panels are flat"),
    Plate("plate-zome-golden", "zome", "golden", 55,
          why="the famous one-panel zome, where the golden ratio is the "
              "design rather than a coincidence"),
    Plate("plate-zome-versus", "zome", "versus", 55,
          why="zome against geodesic dome, counted"),
    Plate("plate-hex-twelve", "hex", "twelve", 58,
          why="exactly twelve pentagons, always -- the fact that decides "
              "every hexagonal dome"),
    Plate("plate-hex-compare", "hex", "compare", 58,
          why="the hexagonal and geodesic domes side by side"),
    Plate("plate-hex-warp", "hex", "warp", 58,
          why="where hexagonal panels stop being flat, and what it costs"),

    # -- the catalogue ---------------------------------------------------
    Plate("plate-framing", "world", "framing", 62,
          why="hubs or no hubs, which is the trade this method is an "
              "answer to"),
    Plate("plate-efficiency", "world", "efficiency", 62,
          why="envelope per square foot of floor, measured across the "
              "whole catalogue"),
    Plate("plate-economics", "world", "math_economics", 63,
          why="every design in the catalogue, priced against each other"),
    Plate("plate-colours", "all_domes", "colours", 63,
          why="sixteen finishes over the same shell"),
    Plate("plate-floor-divisions", "all_domes", "floor", 63,
          why="four ways to divide a round floor, which is the question "
              "everybody asks second"),
    Plate("plate-fitout", "all_domes", "fitout", 63,
          why="the part nobody films: what goes inside"),

    # -- the stem cell ---------------------------------------------------
    Plate("plate-stem-cell", "seed_pitch", "stemcell", 66,
          why="why the product line is called a stem cell: one body, many "
              "things it can become"),
    Plate("plate-slices", "seed_pitch", "slices", 66,
          why="the roof comes apart too"),
    Plate("plate-core-cost", "seed_pitch", "core_cost", 67,
          why="what buying the core once is worth -- the argument for "
              "sinking the cost into hardware that transfers"),
    Plate("plate-system", "seed_pitch", "system", 67,
          why="why this only works as a system rather than as one "
              "building"),
    Plate("plate-seeds-priced", "seed_pitch", "seeds", 69,
          why="the whole catalogue of structures, priced"),
    Plate("plate-ladder", "seed_pitch", "ladder", 69,
          why="how far down the price ladder goes, and what each rung "
              "gives up"),
    Plate("plate-line", "line", "overview", 69,
          why="one building, fifteen stations: the manufacturing view of "
              "the same nine processes"),
    # -- the park, which is the network argument drawn -------------------
    Plate("plate-park-open", "dome_park", "open", 49,
          why="an RV park for houses, which is the comparison everybody "
              "reaches for first"),
    Plate("plate-two-owners", "dome_park", "legend", 42,
          why="two people, and what each of them owns -- the split the "
              "whole arrangement rests on"),
    Plate("plate-line-never-moves", "dome_park", "two_sides", 42,
          why="the line between host and tenant, and why nothing "
              "straddles it"),
    Plate("plate-four-ways-roof", "dome_park", "stay", 49,
          why="four ways to have a roof for a year, priced against each "
              "other"),
    Plate("plate-crossover", "dome_park", "crossover", 49,
          why="how long you have to stay before owning beats renting"),
    Plate("plate-host-exposure", "dome_park", "exposure", 49,
          why="the host's side against the obvious alternative, including "
              "the number that does not flatter the pad"),
    Plate("plate-why-network", "dome_park", "network", 49,
          why="why one pad is a transaction and many pads are a network"),
    Plate("plate-hardware-set", "dome_park", "hardware", 67,
          why="one hardware set, any size of house -- the transfer "
              "argument as the park film states it"),
    Plate("plate-what-does-not-move", "dome_park", "math_hardware", 67,
          why="what does not move when the house does, counted"),
    Plate("plate-ground-worth", "dome_park", "foundation", 39,
          why="the part of a house you never take with you, priced across "
              "the catalogue"),
    Plate("plate-layers-worth", "dome_park", "math_layers", 31,
          why="what each quilted layer is actually worth"),
    # -- the frontispiece -------------------------------------------------
    Plate("plate-cabin", "world", "show_02", 1, at=0.55,
          title="Split-Log Homestead",
          why="the frontispiece: a split-log timber dome standing in "
              "woodland, which is the building this book is about"),
    Plate("plate-lodge", "world", "show_03", 1, at=0.55,
          title="Whole Trunk Lodge",
          why="the same method at twenty feet, in whole trunks"),
    Plate("plate-frame-on-land", "seed_pitch", "frame", 1, at=0.62,
          bare=True, title="The frame is already on your land",
          why="the wedge timber frame standing in its own woodland, which "
              "is what this book is a picture of"),
    Plate("plate-frame-cost", "seed_pitch", "frame_cost", 1, at=0.5,
          title="What the frame costs",
          why="the same frame with its price on it, outdoors"),

    # -- the wood, and the seam at work (films: The Wedge Dome, Explained;
    #    Which Way the Seam Breathes) --------------------------------------
    Plate("plate-the-vee", "cabin_wedge_explained", "vee", 17,
          why="the real-size seam section on the bench: the V that drying "
              "opens, which the solver draws only as a diagram"),
    Plate("plate-bark-face", "cabin_wedge_explained", "member", 18,
          why="the member stack in the Cabin World, round face out, which is "
              "the one face a finish goes on"),
    Plate("plate-bundle-fits", "cabin_wedge_explained", "bundle", 32,
          why="the four services packed to scale inside the printed key, "
              "which no solver view contains"),
    Plate("plate-no-duct", "cabin_wedge_explained", "ducts", 32,
          why="a three-inch duct drawn on the seam's end face: the number "
              "that does not help, as a picture"),
    Plate("plate-spacer", "cabin_wedge_explained", "spacer", 32,
          why="the same seam as built and opened by the duct spacer, side by "
              "side on two benches"),
    Plate("plate-half-keys", "cabin_wedge_explained", "print", 32,
          why="the key split into the two printed halves each member carries"),
    Plate("plate-rosettes", "cabin_wedge_explained", "hubs", 32,
          why="service rosettes inside a five-way and a six-way vertex of the "
              "solver's own dome"),
    Plate("plate-sky-floating", "cabin_sky_web", "floating", 77,
          why="the solver's forty panels hung apart on their pigtails, seen "
              "from underneath: the state the method is built to reach"),
    Plate("plate-sky-guys", "cabin_sky_web", "guys", 77,
          why="the X and its four guys to the bases of the next trees out, "
              "with the tree margins on them"),
    Plate("plate-sky-pigtails", "cabin_sky_web", "pigtails", 77, at=0.55,
          why="one panel at its place with three cords thrown over the spiral "
              "and the harness still on"),
    Plate("plate-sky-treepost", "cabin_sky_web", "treepost", 77,
          why="a milled 6x6 standing beside the living trunk it would be sawn "
              "from, with both buckling loads on them"),
    Plate("plate-sky-apex", "cabin_sky_web", "apex", 77,
          why="the cords from every joint to one free ring under the cap, the "
              "way a single central lift really spreads the weight"),
    Plate("plate-sky-skin", "cabin_sky_web", "skin", 77, at=0.8,
          why="the silicone-cotton skin going over the hung, joined frame"),
    Plate("plate-sky-corners", "cabin_sky_web", "corners", 77,
          why="the joined dome tilted on one raised corner under the second web"),
    Plate("plate-sty-bare", "cabin_styles", "bare", 78, at=0.7,
          why="the book's own dome rebuilt in the Dome Creator at its own size, bare"),
    Plate("plate-sty-timber-workshop", "cabin_styles", "s_timber_workshop", 79, at=0.7,
          why="the cabin's frame dressed in the Timber Workshop's skin and foundation, in the Creator's own shader"),
    Plate("plate-sty-glass-studio-loft", "cabin_styles", "s_glass_studio_loft", 79, at=0.7,
          why="the cabin's frame dressed in the Glass Studio Loft's skin and foundation, in the Creator's own shader"),
    Plate("plate-sty-split-log-homestead", "cabin_styles", "s_split_log_homestead", 79, at=0.7,
          why="the cabin's frame dressed in the Split-Log Homestead's skin and foundation, in the Creator's own shader"),
    Plate("plate-sty-whole-trunk-lodge--20-ft", "cabin_styles", "s_whole_trunk_lodge___20_f", 79, at=0.7,
          why="the cabin's frame dressed in the Whole Trunk Lodge - 20 ft's skin and foundation, in the Creator's own shader"),
    Plate("plate-sty-grow-dome", "cabin_styles", "s_grow_dome", 79, at=0.7,
          why="the cabin's frame dressed in the Grow Dome's skin and foundation, in the Creator's own shader"),
    Plate("plate-sty-hex-cell-pavilion", "cabin_styles", "s_hex_cell_pavilion", 79, at=0.7,
          why="the cabin's frame dressed in the Hex Cell Pavilion's skin and foundation, in the Creator's own shader"),
    Plate("plate-sty-continuous-steel-arc-hangar", "cabin_styles", "s_continuous_steel_arc_han", 79, at=0.7,
          why="the cabin's frame dressed in the Continuous Steel Arc Hangar's skin and foundation, in the Creator's own shader"),
    Plate("plate-sty-rebar-garden-dome", "cabin_styles", "s_rebar_garden_dome", 79, at=0.7,
          why="the cabin's frame dressed in the Rebar Garden Dome's skin and foundation, in the Creator's own shader"),
    Plate("plate-sty-concrete-monocoque-form", "cabin_styles", "s_concrete_monocoque_form", 79, at=0.7,
          why="the cabin's frame dressed in the Concrete Monocoque Form's skin and foundation, in the Creator's own shader"),
    Plate("plate-sty-woodland-hex-mirror", "cabin_styles", "s_woodland_hex_mirror", 79, at=0.7,
          why="the cabin's frame dressed in the Woodland Hex Mirror's skin and foundation, in the Creator's own shader"),
    Plate("plate-sty-woodland-square-mirror", "cabin_styles", "s_woodland_square_mirror", 79, at=0.7,
          why="the cabin's frame dressed in the Woodland Square Mirror's skin and foundation, in the Creator's own shader"),
    Plate("plate-sty-treehouse-canopy-dome", "cabin_styles", "s_treehouse_canopy_dome", 79, at=0.7,
          why="the cabin's frame dressed in the Treehouse Canopy Dome's skin and foundation, in the Creator's own shader"),
    Plate("plate-ep-numbered", "cabin_every_piece", "numbered", 87,
          why="the triangle calculator's seventeen wedges in their frame, each "
              "with its number, on the exhibit platform"),
    Plate("plate-ep-saw", "cabin_every_piece", "saw1", 87, at=0.42,
          why="the worked wedge on the mitre saw as the tool sets it up: face "
              "down, corner to the fence, mitre and bevel, the blade in the cut"),
    Plate("plate-ep-offcut", "cabin_every_piece", "saw2", 87, at=0.88,
          why="the second cut done and its offcut fallen away, long enough to keep"),
    Plate("plate-ep-perms", "cabin_every_piece", "perms", 87, at=0.15,
          why="the same triangle filled another of the ten ways"),
    Plate("plate-ep-under", "cabin_every_piece", "under", 87, at=0.9,
          why="the filled panel tipped up to show its underside"),
    Plate("plate-ep-frame", "cabin_every_piece", "frame5", 87, at=0.85,
          why="the five half trunks of the floor's frame round the dome's "
              "centre, with the circle inside them and the circle the dome needs"),
    Plate("plate-ep-corner", "cabin_every_piece", "corner", 87, at=0.35,
          why="a frame trunk's corner marked for its 36 degree chainsaw cut"),
    Plate("plate-ep-star", "cabin_every_piece", "star", 87, at=0.92,
          why="the star alone, with the deck gap it leaves"),
    Plate("plate-ep-joists", "cabin_every_piece", "joists", 87, at=0.95,
          why="the star with every space between its points joisted"),
    Plate("plate-ep-gravel", "cabin_every_piece", "gravel", 87,
          why="the nested rings laid on a gravel bed, no piers"),
    Plate("plate-ep-dome", "cabin_every_piece", "dome", 87, at=0.8,
          why="the dome standing on the star-and-joists floor"),
    Plate("plate-dew-point", "cabin_seam_climate", "dewpoint", 33,
          why="the two airs' dew points over the dome, the chapter's single "
              "rule stated as numbers on the building"),
    Plate("plate-levels", "cabin_seam_climate", "levels", 34,
          why="every seam of the solver's dome coloured by the band it runs "
              "in, which is where the four levels come from"),
    Plate("plate-dead-level", "cabin_seam_climate", "pentagon", 34,
          why="the dead-level pentagon ring and the belt's five low corners, "
              "the drainage argument in one frame"),
    Plate("plate-packed-seam", "cabin_seam_climate", "packed", 36,
          why="a seam section filled with beads, with the pressure it would "
              "take to push the dome's air through it"),
    Plate("plate-two-drawers", "cabin_seam_climate", "drawer", 36,
          why="the drawer, the bypass and the gate at the end of a seam, the "
              "arrangement the chapter recommends"),
    Plate("plate-stove-exchanger", "cabin_seam_climate", "stove", 36,
          why="a stove inside the dome with a sealed exchanger on its flue: "
              "heat to clean air, smoke kept apart"),
    Plate("plate-two-skins", "cabin_seam_climate", "radial", 37,
          why="the seam's two skins with a Peltier plate on each, which is "
              "the owner's arrangement drawn to scale"),
    Plate("plate-heat-pump", "cabin_seam_climate", "pump", 37,
          why="the plates reversing with the season, heat arrows showing "
              "where the heat is thrown"),
    Plate("plate-frost", "cabin_seam_climate", "owner", 37,
          why="a plate driven far under the dew point, frosted, the answer "
              "to the owner's question as a picture"),
    # -- Part 1, filled from the concept ledger --------------------------
    Plate("plate-network-load", "wedge", "triangles", 1,
          why="the triangulated network with the load path drawn, which is the "
              "argument for an odd-shaped member"),
    Plate("plate-lumpy-one", "build", "franken_lumpy", 1,
          why="the salvage frame that stood, with the reasons on screen: error "
              "absorbed, and the skin returning the shell action"),
    Plate("plate-whole-argument", "master", "ms_open", 4,
          why="the master presentation's opening frame: the whole argument the "
              "book proves, in one picture"),
    Plate("plate-model-counts-itself", "master", "ms_math_counted", 4,
          why="the math screen counting panels, edges and corners off the model "
              "drawn behind it"),
    Plate("plate-cut-list", "cabin_wedge_explained", "counts", 4,
          why="the Cabin World dome with its two member lengths and counts, the "
              "same figures as the book's own cut list"),
    Plate("plate-flat-rate", "master", "ms_math_flatrate", 4,
          why="the flat-rate proof: two dome sizes, one parts list, counted on "
              "screen"),
    Plate("plate-four-lines", "master", "h_lines", 4,
          why="the four product lines drawn from one skeleton"),
    Plate("plate-ugly-one", "master", "ms_franken_why", 5,
          why="the frankendome: salvage, folded brackets and a frame that stood, "
              "which no solver view can show"),
    Plate("plate-build-the-next", "master", "ms_close", 5,
          why="the master presentation's closing frame, the argument closed"),
    # -- Part 8, filled from the concept ledger --------------------------
    Plate("plate-pine-ladder", "pine_value", "ladder", 43,
          why="one tree's value on every rung, stump to financed framing"),
    Plate("plate-stud-hands", "why", "middlemen", 44,
          why="every hand a stud passes through between the stump and the rack"),
    Plate("plate-interest", "why_build", "interest", 45,
          why="a mortgage's interest drawn as the square feet it would buy"),
    Plate("plate-house-money", "harvest", "house_money", 46,
          why="a new house's price split by the builders' own survey"),
    Plate("plate-invoice", "seed_pitch", "invoice", 47,
          why="the stem-cell dome's invoice, line by line, with the margin shown"),
    # -- Part 7, filled from the concept ledger --------------------------
    Plate("plate-pad-build", "dome_park", "pad_build", 42,
          why="a pad built in courses: ground, deck, the acceptor rim, the "
              "services up the middle"),
    Plate("plate-iris", "byod", "iris", 42,
          why="the iris rim opening and closing to take more than one dome size"),
    # -- Part 5, filled from the concept ledger --------------------------
    Plate("plate-rings", "build", "rings", 28,
          why="the corners sorted into level courses, the check heights for the "
              "raise"),
    Plate("plate-riser", "build", "riser", 28,
          why="the same dome stood on a riser wall, with the headroom it buys"),
    Plate("plate-boat-hull", "seed_pitch", "shell", 29,
          why="the composite boat-hull shell over the stem-cell frame"),
    Plate("plate-air-wall", "build", "air_wall", 31,
          why="air pushed through the whole shell at a speed nobody feels"),
    Plate("plate-solar-shell", "byod", "solar", 31,
          why="the same dome with cells on one side, the top half, and the whole "
              "shell"),
    # -- Part 4, filled from the concept ledger --------------------------
    Plate("plate-forty-frames", "wedge", "panels", 21,
          why="the forty independent triangular frames, each finished before "
              "it meets a neighbour"),
    Plate("plate-keystone", "why", "keystone", 21,
          why="the tapered opening that stops a panel falling through: the "
              "frame as a chassis"),
    Plate("plate-six-motions", "line", "cycle", 23,
          why="one worker's six motions for one part, each with its cost"),
    Plate("plate-trunk-work", "line", "limbs", 23,
          why="the lifting work split by limb group, the trunk doing most"),
    Plate("plate-compound-cut", "build", "hubless_cut", 25,
          why="a rectangular strut's end with its mitre and bevel shown on "
              "the same pass"),
    Plate("plate-the-sled", "cuts", "sled", 25,
          why="the crosscut sled fenced to the complement, which reaches the "
              "angles no mitre saw does"),
    Plate("plate-five-cut", "cuts", "fivecut", 25,
          why="the five-cut test making a fence error a caliper can read"),
    # -- Part 3, filled from the concept ledger --------------------------
    Plate("plate-one-log", "cabin_wedge_explained", "grain", 12,
          why="the split log's end grain in the Cabin World: the whole frame "
              "before it is cut"),
    Plate("plate-fell-line", "harvest", "fell", 12,
          why="the notch, the back cut and the hinge, drawn on the falling tree"),
    Plate("plate-two-trees-dome", "wedge", "m_dome", 12,
          why="the dome the two worked trees size, solved backwards from the "
              "longest member"),
    Plate("plate-saw-sessions", "why", "sessions", 14,
          why="the two timed saw sessions and the fuel, the measured half of "
              "the argument"),
    Plate("plate-counting-cuts", "wedge", "m_actions", 14,
          why="cuts per member counted both ways, splitting against milling"),
    Plate("plate-thin-coat", "cabin_linseed_oil", "apply", 19,
          why="a thin coat being wiped dry on a sample, in the Cabin World "
              "workshop"),
    Plate("plate-oil-seam", "cabin_linseed_oil", "seam", 19,
          why="the real seam specimen, showing which surfaces a finish must "
              "stay off"),
    # -- Part 2, filled from the concept ledger --------------------------
    Plate("plate-unit-sphere", "2v", "normalize", 8,
          why="the icosahedron after the one division that puts it on a unit "
              "sphere, with the chord factor on screen"),
    Plate("plate-halve", "2v", "subdivide", 8,
          why="the thirty parent edges with their midpoints marked, before "
              "anything moves"),
    Plate("plate-midpoint-sag", "scratch", "midpoints", 8,
          why="a midpoint sitting inside the sphere, the sag the projection "
              "has to fix"),
    Plate("plate-push-out", "2v", "project", 8,
          why="the midpoints pushed out along their own rays to the sphere"),
    Plate("plate-two-classes", "2v", "classes", 8,
          why="every edge measured and grouped: exactly two lengths"),
    Plate("plate-solved-shell", "why", "realdome", 10,
          why="the raw-wedge solver's own output, members and keys, which is "
              "what every later number is measured off"),
    Plate("plate-what-moves", "why", "mixed_math", 10,
          why="the same shell solved for a thin log and a fat one, with what "
              "changes and what does not"),
    Plate("plate-ring-error", "build", "error", 11,
          why="the ten-sided base ring and the factor that multiplies a strut "
              "error"),
    Plate("plate-measure-loop", "build", "check", 11,
          why="the measurement loop in order, member to height"),
    Plate("plate-whole-transformation", "2v", "finale", 11,
          why="the derivation in one frame, golden ratio to cut list"),
    Plate("plate-plate-first", "cabin_seam_climate", "order", 37,
          why="air moving over the plate before the wood, with the dew point "
              "it leaves at"),
    # -- Part 10: the framed-panel method, from cabin_panel_method --------
    Plate("plate-zome-model", "cabin_panel_method", "zome", 57,
          why="a nine-sided zome model framed with no bevel, four same sticks a panel"),
    Plate("plate-zome-joint", "cabin_panel_method", "zome_joint", 57,
          why="one zome panel full size: a pinwheel of four sticks, both ends parallel"),
    Plate("plate-panel-two", "cabin_panel_method", "two", 59,
          why="the wedge dome and a 3V panel dome side by side on one hill"),
    Plate("plate-panel-sphere", "cabin_panel_method", "sphere", 59,
          why="the 3V dome's sticks coloured by chord, the five-way points marked"),
    Plate("plate-panel-cut", "cabin_panel_method", "cut", 59,
          why="the 5/8 cut, with the part of the sphere it leaves out ghosted"),
    Plate("plate-panel-base", "cabin_panel_method", "base", 59,
          why="the zig-zag base: tapered sections in amber, level ones in blue"),
    Plate("plate-panel-panels", "cabin_panel_method", "panels", 59,
          why="the two panel outlines drawn full size on the jig sheet"),
    Plate("plate-panel-deck", "cabin_panel_method", "deck", 59, at=0.9,
          why="the radial deck: posts, five girders, a joist to every base corner, the rim"),
    Plate("plate-panel-jig", "cabin_panel_method", "jig", 60, at=0.95,
          why="two trammel arcs crossing at the hexagon panel's apex"),
    Plate("plate-panel-pinwheel", "cabin_panel_method", "pinwheel", 60,
          why="a hexagon panel's three sticks pinwheeled on the jig, each coloured"),
    Plate("plate-panel-bevel", "cabin_panel_method", "bevel", 60,
          why="every stick tinted by how far one shop bevel is from exact"),
    Plate("plate-panel-skin", "cabin_panel_method", "skin", 60,
          why="whole pentagons and hexagons skinned in one sheet each"),
    Plate("plate-panel-window", "cabin_panel_method", "window", 60, at=0.9,
          why="a window: a spare frame hinged at its top, held open by a strut"),
    # -- Part 9: the network, from dome_park, byod, seed_pitch and hype -------
    Plate("plate-pad-detail", "dome_park", "pad_detail", 50,
          why="everything the host owns drawn on one pad: deck, rim, pipes, pedestal"),
    Plate("plate-reserved-spot", "byod", "center", 50,
          why="the services coming up inside the footprint, never across the doorway"),
    Plate("plate-ground-share", "dome_park", "math_foundation", 50,
          why="each shipped design's foundation as a share of its build, measured"),
    Plate("plate-target-pad", "byod", "target", 51,
          why="the ten-thousand-dollar pad tested at three rents, payback on net"),
    Plate("plate-host-bills", "byod", "operating", 51,
          why="a pad host's yearly bill against a furnished short let's, same base costs"),
    Plate("plate-rooms-change", "byod", "rooms", 52,
          why="nonstructural partitions moved round a fixed service core as a family changes"),
    Plate("plate-semi-nomadic", "dome_park", "move", 52,
          why="a dome lifted off one pad and set down on another, services reconnected"),
    Plate("plate-pad-turns", "byod", "rotation", 53,
          why="the rotating foundation turning a one-sided array toward the sun"),
    Plate("plate-tracking-worth", "dome_park", "math_solar", 53,
          why="fixed against tracking for three claddings, with the surplus a tenant cannot use"),
    Plate("plate-bathhouse", "dome_park", "shared", 53,
          why="a site's shared bathhouse, so a dome on it can carry no plumbing at all"),
    Plate("plate-storage-dome", "byod", "storage", 53,
          why="the same kit of parts as a climate-controlled storage building"),
    Plate("plate-my-story", "byod", "my_story", 54,
          why="the author's own reason for the system, in the Cabin World"),
    Plate("plate-three-things", "seed_pitch", "three", 54,
          why="quilters, pad hosts and dome owners, each needing the other two"),
    Plate("plate-first-site", "byod", "ask", 54,
          why="what the first site's money builds, costed with the same pad model"),
    Plate("plate-three-phases", "hype", "phases", 54,
          why="the three-phase plan, stated with the Frankendome film's straight face"),
    # -- Part 10: the hexagon cage and the zome, built --------------------------
    Plate("plate-hex-cut", "hex", "the_cut", 58,
          why="the hexagon cage's rim stepping up and down where no strut runs level"),
    Plate("plate-hex-dual", "hex", "dual", 58,
          why="triangle centres joined round each corner: six-way corners become hexagons"),
    Plate("plate-hex-seams", "hex", "seams", 58,
          why="three panel edges meeting at every hub, pointed at the sky"),
    Plate("plate-zome-counts", "zome", "counts", 56,
          why="panels, struts and hubs counted from the number of directions, Euler checked"),
    Plate("plate-zome-rings", "zome", "rings", 56,
          why="every hub on a level ring, the rings evenly spaced"),
    Plate("plate-zome-pitch", "zome", "pitch", 56,
          why="the same struts and count leaned steep and shallow: spire against saucer"),
    Plate("plate-zome-floor", "zome", "floor", 56,
          why="a level floor line crossing every bottom strut at the same point"),
    # -- Part 11: the twelve designs, and what every choice costs ---------------
    Plate("plate-glass-loft", "world", "show_01", 64,
          why="the four-frequency glazed loft, the expensive beautiful end of the catalogue"),
    Plate("plate-grow-dome", "world", "show_04", 64,
          why="the workshop's skeleton in aluminium and polycarbonate: a greenhouse"),
    Plate("plate-hex-pavilion", "world", "show_05", 64,
          why="a hexagonal cell frame in structural steel, fitted as a presentation space"),
    Plate("plate-arc-hangar", "world", "show_06", 64,
          why="continuous curved steel ribs in place of short straight struts"),
    Plate("plate-rebar-garden", "world", "show_07", 64,
          why="a dense meridian-and-ring lattice bent from rebar, the cheapest building"),
    Plate("plate-concrete-form", "world", "show_08", 64,
          why="the frame as formwork for a poured concrete shell, with shoring and mixer"),
    Plate("plate-hex-mirror", "world", "show_09", 64,
          why="hexagonal mirror tiles reflecting the procedural sky and the trunks around"),
    Plate("plate-canopy-dome", "world", "show_11", 64,
          why="a two-frequency dome up in the canopy on a braced timber platform"),
    Plate("plate-menu-price", "all_domes", "math_price", 65,
          why="one design priced one menu at a time: which choice actually costs money"),
    Plate("plate-dice-domes", "all_domes", "random", 65,
          why="eight configurations drawn at random from the menus, built and priced"),
    Plate("plate-permutations", "all_domes", "math_permutations", 65,
          why="the menus multiplied into sixteen billion shells, and the film that would take"),
    Plate("plate-production-ledger", "world_chatgpt", "cg_costs_math", 65,
          why="ten builds carried from bill of materials through hours to a planning price"),
    # -- Part 12: the core built, the shape argued, the article priced ----------
    Plate("plate-core-bench", "module_build", "tools", 68,
          why="the nine tools on the bench before a core is started, gauge and torque driver included"),
    Plate("plate-core-water", "module_build", "water", 68,
          why="the manifold, the valve and the pressure test, before anything electrical exists"),
    Plate("plate-core-shopping", "module_build", "materials", 68,
          why="the twenty-three lines a core is bought from, none of them exotic"),
    Plate("plate-less-skin", "kick", "versus", 70,
          why="a box house and a dome on the same floor, with their skins measured"),
    Plate("plate-wind", "kick", "wind", 70,
          why="the wind meeting a box and a dome, with the two drag coefficients"),
    Plate("plate-the-hat", "kick", "hat", 70,
          why="the top twenty triangles laminated like a hat: exactly half the shell"),
    Plate("plate-first-one", "kick", "proof", 70,
          why="the first dome already standing, framed from four trees in ten days"),
    Plate("plate-pony-wall", "kick2", "pony", 70,
          why="the shell lifted on a stem wall, and the usable floor that buys back"),
    Plate("plate-run-cost", "kick2", "energy", 70,
          why="a year of heating and cooling, dome against box, on the same floor"),
    Plate("plate-sky-paint", "kick2", "paint", 70,
          why="a radiative-cooling roof running below air temperature in full sun"),
    Plate("plate-the-invoice", "pitch_hero", "price", 71,
          why="the standard article's price, with what it costs to build and the margin stated"),
    Plate("plate-thousand-shirts", "pitch_hero", "quilt", 71,
          why="the quilted insulation, each layer tagged with the name of who sewed it"),
    Plate("plate-off-grid", "seed_pitch", "solar", 71,
          why="the array and the bank sized against the dome's own measured draw"),
    Plate("plate-the-goal", "seed_pitch", "goal", 71,
          why="the campaign goal as the sum of a list, line by line"),
    # -- Part 13: hubs, the Frankendome, the empire, and why ---------------------
    Plate("plate-hub-kit", "build", "hubkit", 72,
          why="three hub systems building the same geometry and eating different strut"),
    Plate("plate-flat-triangles", "build", "subassembly", 72,
          why="the two triangle families jigged flat on the ground before anything goes up"),
    Plate("plate-four-failures", "build", "failures", 72,
          why="the four habits that make domes fail, none of them geometry"),
    Plate("plate-washing-machine", "franken", "bracket_bend", 73,
          why="a band of washing-machine casing folded once into a V bracket"),
    Plate("plate-slack", "franken", "slack", 73,
          why="green where the geometry puts each hub, red where the stick actually put it"),
    Plate("plate-woodpile", "franken", "stockpile", 73,
          why="every strut coloured by the section it was cut to, round to salvaged steel"),
    Plate("plate-franken-bill", "franken", "cost", 73,
          why="the Frankendome's whole bill: free timber, free brackets, screws and glass"),
    Plate("plate-moulded-member", "seed_pitch", "next", 73,
          why="the member with its hardware moulded in, which does not exist yet"),
    Plate("plate-evil-empire", "hype", "empire", 74,
          why="the Evil Dome Empire, introduced with the straight face it deserves"),
    Plate("plate-three-hours-later", "hype", "threehours", 74,
          why="a dome three hours after the Hoboclass got at it with salvage and power tools"),
    Plate("plate-balance-of-forces", "hype", "asymmetry", 74,
          why="the serious part: institutional capital against one prototype and a chainsaw"),
    Plate("plate-fuller", "hype3", "fuller", 75,
          why="the Fuller idea that turned an interest into a mission"),
    # -- Part 14: from one number to a lit pixel ---------------------------------
    Plate("plate-strut-tube", "scratch", "m_tube", 84,
          why="one strut given a body: two cross products, a ring of eight, twenty-eight triangles"),
    Plate("plate-the-divide", "scratch", "clip", 84,
          why="the solver's dome put through the real matrices and divided, leaning with distance"),
    Plate("plate-one-vertex", "scratch", "m_pixel", 84,
          why="the apex followed from world space to the pixel it lands on"),
    Plate("plate-what-hides-what", "scratch", "depth", 84,
          why="three panels drawn in the worst order and still right, by a depth test"),
    Plate("plate-three-dot-products", "scratch", "m_light", 84,
          why="the film's own lighting sum on one panel: diffuse, highlight and rim"),
)


def by_chapter(chapter: int) -> list[Plate]:
    return [p for p in PLATES if p.book_chapter == chapter]


def coverage() -> dict:
    """Which illustration-plan entries the plates satisfy."""
    have: dict[str, list[str]] = {}
    for plate in PLATES:
        if plate.plan:
            have.setdefault(plate.plan, []).append(plate.key)
    return have


# ----------------------------------------------------------------------
# Making them
# ----------------------------------------------------------------------

def render(plates: tuple[Plate, ...] | None = None,
           timeout: int = 5400) -> dict:
    """Take every plate's frame, one subprocess per film.

    One process per film rather than one per plate: building a lesson's world
    is most of the cost and a film with eight plates in it should pay for that
    once. The films are rendered by their own app, in its own Python, through
    the ticket it already has for this -- nothing here reaches into a
    renderer.
    """
    plates = plates if plates is not None else PLATES
    registry = lessons()
    # Grouped by film AND by whether the frame is bare, because bare is a
    # property of the whole render rather than of one shot: a frontispiece
    # and an ordinary plate from the same film need two runs.
    wanted: dict[tuple[str, bool], list[Plate]] = {}
    for plate in plates:
        wanted.setdefault((plate.lesson, plate.bare), []).append(plate)

    made, missing, failed = [], [], []
    for (key, bare), group in wanted.items():
        lesson = registry.get(key)
        if lesson is None:
            failed.append(f"no lesson {key!r}")
            continue
        times = {}
        for plate in group:
            try:
                times[plate] = shot_time(lesson, plate.chapter, plate.at)
            except KeyError as exc:
                failed.append(str(exc))
        if not times:
            continue
        ticket = {
            "lesson": key,
            "action": "shots",
            "shots": ",".join(f"{t:.2f}" for t in times.values()),
            "bare": bare,
            # No scrubber, no play button, no PAUSED. A printed page has
            # none of those and the film's layout is unchanged without them.
            "plate": True,
        }
        print(f"{key}: {len(times)} plates{' (bare)' if bare else ''}")
        result = subprocess.run(
            [PYTHON, *PYTHON_ARGS, "-c",
             "import json,sys;from two_v_demo import app;"
             "raise SystemExit(app.main(config=json.loads(sys.argv[1])))",
             json.dumps(ticket)],
            cwd=str(ROOT), capture_output=True, text=True, timeout=timeout)
        if result.returncode != 0:
            failed.append(f"{key}: {result.stderr[-400:]}")
            continue
        for plate, when in times.items():
            source = (SHOT_DIR / key
                      / f"{lesson.snapshot_prefix}_{when:07.2f}s.png")
            if not source.is_file():
                missing.append(f"{plate.key}: no frame at {when:.2f}s")
                continue
            plate.path.parent.mkdir(parents=True, exist_ok=True)
            shutil.copyfile(source, plate.path)
            made.append(plate.key)
    return {"asked": len(plates), "made": len(made),
            "missing": missing, "failed": failed}


def record(plates: tuple[Plate, ...] | None = None,
           db: Path | None = None) -> int:
    """Put the plates in the book's figure table beside the solver figures."""
    plates = plates if plates is not None else PLATES
    registry = lessons()
    conn = store.connect(db)
    try:
        with conn:
            for plate in plates:
                lesson = registry.get(plate.lesson)
                conn.execute(
                    "INSERT OR REPLACE INTO figure (key, chapter, title, "
                    "caption, path, recipe, credit, built) "
                    "VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
                    (plate.key, plate.book_chapter,
                     plate.title or (find_chapter(lesson, plate.chapter).title
                                     if lesson else plate.key),
                     plate.full_caption(lesson), str(plate.path),
                     json.dumps({"lesson": plate.lesson,
                                 "chapter": plate.chapter, "at": plate.at}),
                     store.CREDIT, int(plate.path.is_file())))
        return len(plates)
    finally:
        conn.close()


def validate_plates() -> None:
    """Every plate names a real chapter of a real film, and says why."""
    registry = lessons()
    keys = [p.key for p in PLATES]
    assert len(set(keys)) == len(keys), "two plates share a key"
    assert len(PLATES) >= 40, len(PLATES)

    seen: set[tuple[str, str]] = set()
    for plate in PLATES:
        lesson = registry.get(plate.lesson)
        assert lesson is not None, f"{plate.key}: no lesson {plate.lesson!r}"
        chapter = find_chapter(lesson, plate.chapter)
        assert 0.0 < plate.at < 1.0, plate.key
        assert plate.book_chapter >= 1, plate.key
        # A plate exists because the solver cannot make it. If it does not say
        # what it is for, it is a screenshot somebody liked.
        assert len(plate.why) > 20, f"{plate.key} does not say why it is here"
        # The same frame twice is one picture printed twice.
        mark = (plate.lesson, plate.chapter)
        assert mark not in seen, f"{plate.key} repeats {mark}"
        seen.add(mark)
        # The caption has to come out as something a reader can read.
        caption = plate.full_caption(lesson)
        assert len(caption) > 60, plate.key
        assert store.CREDIT in caption, plate.key
        # And the frame has to be inside the film.
        when = shot_time(lesson, plate.chapter, plate.at)
        total = sum(c.duration for c in lesson.chapters)
        assert 0.0 < when < total, (plate.key, when, total)
        assert chapter.duration > 1.0, (plate.key, chapter.duration)

    # The plates exist to fill the holes the solver leaves. Check they do.
    from . import figures

    solver_gaps = set(figures.coverage()["unmet"])
    filled = set(coverage())
    remaining = sorted(solver_gaps - filled)
    # Not every gap has to be filled by a plate -- some are worksheets and
    # blank pages -- but the ones a film draws should be.
    for name in remaining:
        assert name in figures.NOT_IN_THE_SOLVER, name
    assert len(filled & solver_gaps) >= 10, (
        f"the plates only fill {len(filled & solver_gaps)} of the "
        f"{len(solver_gaps)} illustrations the solver cannot make; the films "
        "draw more than that")

    # Every plate names a chapter the book actually has...
    from . import outline

    numbers = {chapter.number for chapter in outline.BOOK.chapters}
    stray = sorted({p.book_chapter for p in PLATES} - numbers)
    assert not stray, (
        f"plates are placed in chapters the book does not have: {stray}; "
        f"it has 1..{max(numbers)}")

    # ...and the chapter it names is the chapter whose prose prints it.
    #
    # This field drifted through two renumberings without anybody noticing,
    # because nothing read it: what reaches a page is the image link in the
    # manuscript. So something reads it now.
    import re as _re

    link = _re.compile(r"\]\(([a-z0-9\-]+)\.png\)")
    printed: dict[str, int] = {}
    for chapter in outline.BOOK.chapters:
        path = chapter.path(outline.MANUSCRIPT_DIR)
        if not path.is_file():
            continue
        for key in link.findall(path.read_text(encoding="utf-8")):
            printed.setdefault(key, chapter.number)

    misfiled = [
        f"{plate.key}: filed under {plate.book_chapter}, printed in "
        f"{printed[plate.key]}"
        for plate in PLATES
        if plate.key in printed and printed[plate.key] != plate.book_chapter]
    assert not misfiled, (
        f"{len(misfiled)} plates name a chapter they do not appear in:"
        + store.NEWLINE_BULLET + store.NEWLINE_BULLET.join(misfiled[:10]))

    # And how much rendered material the book is sitting on unused. Not an
    # error -- a plate may be rendered ahead of the chapter that will want
    # it -- but a large pile of them means the book has lost track of what
    # it has, which is how it ended up with no chapter about doorways while
    # holding two pictures of one.
    unused = sorted({p.key for p in PLATES} - set(printed))
    assert len(unused) <= 12, (
        f"{len(unused)} plates are rendered and never printed; either use "
        f"them or drop them: {unused[:12]}")


def main(argv: list[str] | None = None) -> int:
    import argparse

    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--render", action="store_true")
    parser.add_argument("--only", default="", help="one lesson key")
    args = parser.parse_args(argv)

    validate_plates()
    plates = tuple(p for p in PLATES
                   if not args.only or p.lesson == args.only)
    films = sorted({p.lesson for p in plates})
    print(f"{len(plates)} plates from {len(films)} films: {', '.join(films)}")
    have = sum(1 for p in plates if p.path.is_file())
    print(f"  {have} taken, {len(plates) - have} to take")
    for name, keys in sorted(coverage().items()):
        print(f"  {name[:52]:<52} {', '.join(keys)[:40]}")

    if args.render:
        result = render(plates)
        print(json.dumps(result, indent=2))
        record()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
