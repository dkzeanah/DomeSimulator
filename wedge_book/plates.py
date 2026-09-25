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
    Plate("plate-stop-squaring", "wedge", "split", 9,
          plan="Log divided into wedge members",
          why="the round log being split, which the solver starts after"),
    Plate("plate-round-log-corners", "why", "round", 9,
          plan="Conventional rectangular strut versus wedge strut",
          why="the square section a sawmill cuts out of a round log, and "
              "what it throws away"),
    Plate("plate-tree-is-the-product", "why_build", "tree", 9,
          plan="Log divided into wedge members",
          why="the whole tree, before anything is taken out of it"),

    # -- 3. Geometry ---------------------------------------------------
    Plate("plate-frequency", "world", "math_frequency", 26,
          plan="Frequency and truncation comparison silhouettes",
          why="2V against 3V and 4V, which this solver does not build"),
    Plate("plate-frequency-cost", "world", "ladder", 26,
          plan="Frequency and truncation comparison silhouettes",
          why="what each frequency costs, counted"),

    # -- 4. Materials --------------------------------------------------
    Plate("plate-two-trees", "harvest", "tree", 9,
          plan="Grain/defect examples for member selection",
          why="the standing timber a frame comes out of"),
    Plate("plate-eight-materials", "all_domes", "materials", 24,
          plan="Nominal versus actual lumber cross-section",
          why="eight frame materials priced against each other -- steel, "
              "aluminium, timber, whole trunk, PVC, bamboo"),
    Plate("plate-eight-sections", "all_domes", "shapes", 24,
          plan="Conventional rectangular strut versus wedge strut",
          why="eight strut cross sections side by side, including the "
              "rectangular stick this method is an argument against"),
    Plate("plate-recovery", "pine_value", "recovery", 9,
          plan="Log divided into wedge members",
          why="how much of a log survives splitting against sawing"),

    # -- 5. Turning timber into wedges ---------------------------------
    Plate("plate-blade-tilt", "cuts", "tilt", 14,
          plan="Dimensional-lumber wedge-cutting layouts",
          why="the saw being set, which is the operation the book is "
              "describing"),
    Plate("plate-two-machines", "cuts", "machines", 14,
          plan="Saw/jig sequence for repetitive wedge production",
          why="why the cut takes two machines"),

    # -- 7. Connections ------------------------------------------------
    Plate("plate-gasket", "wedge", "gasket", 12,
          plan="Exploded fastener/plate alternatives",
          why="the gasket doing the shaving, which is the alternative to a "
              "machined key"),
    Plate("plate-six-joints", "all_domes", "styles", 12,
          plan="Exploded fastener/plate alternatives",
          why="six ways to join the same sticks, which is the whole "
              "alternatives question in one frame"),

    # -- 8 and 12. The ground -------------------------------------------
    Plate("plate-meeting-the-ground", "build", "foundation", 19,
          plan="Slab/ring/pier/raised-floor comparison sections",
          why="four foundations in section, which nothing here renders"),
    Plate("plate-seven-foundations", "all_domes", "foundations", 19,
          plan="Slab/ring/pier/raised-floor comparison sections",
          why="seven foundations priced against each other"),
    Plate("plate-the-pad", "seed_pitch", "deck", 32,
          plan="Prepared dome pad",
          why="the platform built one course at a time"),
    Plate("plate-pad-is-not-yours", "seed_pitch", "pad", 20,
          plan="Prepared dome pad",
          why="the pad as a thing somebody else owns"),

    # -- 9. Assembly ----------------------------------------------------
    Plate("plate-one-dome-step-by-step", "all_domes", "build", 13,
          plan="Temporary bracing and raising sequence",
          why="a dome going up in phases, which the wedge solver cannot "
              "show part-built"),
    Plate("plate-station", "line", "station", 13,
          why="one station of an assembly line, because forty identical "
              "panels is a production question"),

    # -- 10. Openings ---------------------------------------------------
    Plate("plate-openings", "build", "openings", 15,
          plan="Door opening",
          why="doors and windows, and what not to cut"),
    Plate("plate-openings-zome", "zome", "openings", 15,
          plan="Window-frame integration diagram",
          why="the same problem on a different geometry, which is how to "
              "tell a rule from a habit"),

    # -- 11. Panels and shells ------------------------------------------
    Plate("plate-sixteen-panels", "all_domes", "panels", 24,
          plan="Removable panel",
          why="sixteen panel types -- ply, glass, acrylic, twinwall, SIP, "
              "shingle, metal, solar, canvas, mirror, precast"),
    Plate("plate-nine-claddings", "all_domes", "layers", 24,
          plan="Insulated panel",
          why="nine cladding layers over the same shell"),
    Plate("plate-shower-cap", "seed_pitch", "cap", 2,
          plan="Panel-to-wedge weather-seal detail",
          why="one watertight layer over everything else, which is the "
              "shell strategy this book recommends"),
    Plate("plate-quilt", "seed_pitch", "quilt", 18,
          plan="Insulated panel",
          why="the insulation as a removable quilted layer"),
    Plate("plate-four-skins", "seed_pitch", "shell_cost", 17,
          why="four ways to skin the same frame, priced"),
    Plate("plate-sheet-problem", "seed_pitch", "sheet", 17,
          why="what a four-foot sheet does to a dome sized from its member"),

    # -- 13. Utilities ---------------------------------------------------
    Plate("plate-core-socket", "seed_pitch", "core", 32,
          plan="Utility column",
          why="the utility column, which lives in seed_world and not in the "
              "wedge solver"),
    Plate("plate-build-a-core", "module_build", "chase", 28,
          plan="Utility column",
          why="a core being built on a bench, service by service"),
    Plate("plate-core-cap", "module_build", "close", 28,
          plan="Gasketed service cap",
          why="the cap proved and the core stood up"),
    Plate("plate-shared-services", "byod", "shared", 28,
          plan="Floor utility interface",
          why="what a site shares and what each dome brings"),
    Plate("plate-polyps", "seed_pitch", "polyps", 27,
          why="services that hang off the outside instead of going through "
              "the wall"),

    # -- 14. Environmental control ----------------------------------------
    Plate("plate-layering", "seed_pitch", "layering", 18,
          plan="Insulation/ventilation/condensation path section",
          why="the envelope gaining a layer a winter"),
    Plate("plate-furnished", "look", "furnished", 32,
          plan="Completed dome cutaway",
          why="the finished inside, which is the nearest thing to a cutaway "
              "any tool here makes"),

    # -- 15 to 18. Variations, configurations, modules, platform ----------
    Plate("plate-hex", "hex", "one_hexagon", 23,
          why="a hexagonal dome: the same argument, different tiling"),
    Plate("plate-zome", "zome", "sweep", 22,
          why="a zome, where every panel is a flat parallelogram"),
    Plate("plate-twelve-domes", "all_domes", "open", 32,
          plan="Frequency and truncation comparison silhouettes",
          why="twelve finished buildings from one tool"),
    Plate("plate-swap-everything", "hype6", "swap", 3,
          plan="Removable panel",
          why="panels swapped without touching the frame"),
    Plate("plate-core-moves", "seed_pitch", "modular", 28,
          plan="Prefabricated triangle module",
          why="the core lifted out and carried to the next dome"),
    Plate("plate-mast-and-floor", "seed_pitch", "mast", 30,
          why="a mast through the column and a floor clamped to it"),
    Plate("plate-floating", "seed_pitch", "floating", 30,
          why="the dome hung between two trees, priced and not rated"),
    Plate("plate-catalogue", "seed_pitch", "catalogue", 29,
          why="the other buildings a homestead wants"),

    # -- 19 and 20. Reference --------------------------------------------
    Plate("plate-price-line-by-line", "seed_pitch", "price", 31,
          plan="Material-yield worksheet example",
          why="the whole invoice, line by line"),
    Plate("plate-yield", "why", "yield", 11,
          plan="Material-yield worksheet example",
          why="how much of the tree survives, measured"),
    Plate("plate-factors-to-lumber", "scratch", "m_scale", 11,
          plan="Cut-list worksheet example",
          why="chord factors turning into a cut list"),
    Plate("plate-against-itself", "seed_pitch", "against", 31,
          why="the three things the model says against its own argument"),
# -- the geometry, derived on screen --------------------------------
    Plate("plate-why-triangles", "scratch", "why_triangles", 4,
          why="why the shape is triangles at all, before any dome"),
    Plate("plate-icosahedron", "scratch", "why_ico", 4,
          why="the solid the whole thing starts from, and why that one"),
    Plate("plate-phi", "scratch", "m_phi", 5,
          plan="Center/radius/base-polygon layout diagram",
          why="twelve points placed by one irrational number -- the golden "
              "ratio's actual job in this method"),
    Plate("plate-project", "scratch", "project", 8,
          why="the push that turns a subdivided icosahedron into a sphere"),
    Plate("plate-chords-four-ways", "scratch", "m_chords", 6,
          why="the two chord factors derived four independent ways and "
              "cross-checked against each other"),
    Plate("plate-hemisphere", "scratch", "hemisphere", 7,
          why="where a sphere gets cut to become a building"),
    Plate("plate-counting", "scratch", "m_counts", 7,
          why="every part of the building counted from the topology"),
    Plate("plate-cross-check", "scratch", "cross_check", 6,
          why="two ways of computing the same number, and the residual "
              "between them"),

    # -- other shapes ----------------------------------------------------
    Plate("plate-zome-what", "zome", "what", 22,
          why="a zome is not a piece of a sphere, and the difference is "
              "the whole of why its panels are flat"),
    Plate("plate-zome-golden", "zome", "golden", 22,
          why="the famous one-panel zome, where the golden ratio is the "
              "design rather than a coincidence"),
    Plate("plate-zome-versus", "zome", "versus", 22,
          why="zome against geodesic dome, counted"),
    Plate("plate-hex-twelve", "hex", "twelve", 23,
          why="exactly twelve pentagons, always -- the fact that decides "
              "every hexagonal dome"),
    Plate("plate-hex-compare", "hex", "compare", 23,
          why="the hexagonal and geodesic domes side by side"),
    Plate("plate-hex-warp", "hex", "warp", 23,
          why="where hexagonal panels stop being flat, and what it costs"),

    # -- the catalogue ---------------------------------------------------
    Plate("plate-framing", "world", "framing", 25,
          why="hubs or no hubs, which is the trade this method is an "
              "answer to"),
    Plate("plate-efficiency", "world", "efficiency", 25,
          why="envelope per square foot of floor, measured across the "
              "whole catalogue"),
    Plate("plate-economics", "world", "math_economics", 26,
          why="every design in the catalogue, priced against each other"),
    Plate("plate-colours", "all_domes", "colours", 26,
          why="sixteen finishes over the same shell"),
    Plate("plate-floor-divisions", "all_domes", "floor", 26,
          why="four ways to divide a round floor, which is the question "
              "everybody asks second"),
    Plate("plate-fitout", "all_domes", "fitout", 26,
          why="the part nobody films: what goes inside"),

    # -- the stem cell ---------------------------------------------------
    Plate("plate-stem-cell", "seed_pitch", "stemcell", 27,
          why="why the product line is called a stem cell: one body, many "
              "things it can become"),
    Plate("plate-slices", "seed_pitch", "slices", 27,
          why="the roof comes apart too"),
    Plate("plate-core-cost", "seed_pitch", "core_cost", 28,
          why="what buying the core once is worth -- the argument for "
              "sinking the cost into hardware that transfers"),
    Plate("plate-system", "seed_pitch", "system", 28,
          why="why this only works as a system rather than as one "
              "building"),
    Plate("plate-seeds-priced", "seed_pitch", "seeds", 29,
          why="the whole catalogue of structures, priced"),
    Plate("plate-ladder", "seed_pitch", "ladder", 29,
          why="how far down the price ladder goes, and what each rung "
              "gives up"),
    Plate("plate-line", "line", "overview", 29,
          why="one building, fifteen stations: the manufacturing view of "
              "the same nine processes"),
    # -- the park, which is the network argument drawn -------------------
    Plate("plate-park-open", "dome_park", "open", 21,
          why="an RV park for houses, which is the comparison everybody "
              "reaches for first"),
    Plate("plate-two-owners", "dome_park", "legend", 20,
          why="two people, and what each of them owns -- the split the "
              "whole arrangement rests on"),
    Plate("plate-line-never-moves", "dome_park", "two_sides", 20,
          why="the line between host and tenant, and why nothing "
              "straddles it"),
    Plate("plate-four-ways-roof", "dome_park", "stay", 21,
          why="four ways to have a roof for a year, priced against each "
              "other"),
    Plate("plate-crossover", "dome_park", "crossover", 21,
          why="how long you have to stay before owning beats renting"),
    Plate("plate-host-exposure", "dome_park", "exposure", 21,
          why="the host's side against the obvious alternative, including "
              "the number that does not flatter the pad"),
    Plate("plate-why-network", "dome_park", "network", 21,
          why="why one pad is a transaction and many pads are a network"),
    Plate("plate-hardware-set", "dome_park", "hardware", 28,
          why="one hardware set, any size of house -- the transfer "
              "argument as the park film states it"),
    Plate("plate-what-does-not-move", "dome_park", "math_hardware", 28,
          why="what does not move when the house does, counted"),
    Plate("plate-ground-worth", "dome_park", "foundation", 19,
          why="the part of a house you never take with you, priced across "
              "the catalogue"),
    Plate("plate-layers-worth", "dome_park", "math_layers", 18,
          why="what each quilted layer is actually worth"),
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
    wanted: dict[str, list[Plate]] = {}
    for plate in plates:
        wanted.setdefault(plate.lesson, []).append(plate)

    made, missing, failed = [], [], []
    for key, group in wanted.items():
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
            # No scrubber, no play button, no PAUSED. A printed page has
            # none of those and the film's layout is unchanged without them.
            "plate": True,
        }
        print(f"{key}: {len(times)} plates")
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
