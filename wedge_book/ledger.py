"""The concept ledger: every lesson in every film, and where the book holds it.

The book's job is to be the written embodiment of everything the films teach,
with the films' pictures placed where each idea is explained. This module is
the account of how far it has got. It reads every film in the registry, turns
each chapter into a **concept**, folds re-cuts and compilations into the film
they copy, places every concept in a Part of the book (in the book's own
order), and reads the manuscript to say whether the concept is

* **embodied** -- its picture is printed in the book, or the section that
  writes it up carries a ``<!-- concept: film/slug -->`` marker;
* **mentioned** -- the book uses its key words, but no section is about it;
* **missing** -- neither.

Filling the book a Part at a time is then mechanical: open the Part in
``book_wedge/ledger.md``, write each missing concept up in the chapter it
belongs to, put the marker in, add its plate to :mod:`wedge_book.plates`, and
re-run this. Nothing here is typed twice: titles, promises and narration are
the films' own, read live from the registry.

PLACEMENT

Each film has a home Part. Films that range over several subjects are marked
``mixed`` and their chapters are placed by :data:`RULES` (first match wins),
falling back to the home. :data:`OVERRIDES` settles anything the rules get
wrong, by ``(film, chapter slug)``. Every placement records how it was made,
so a wrong one is easy to find and a one-line fix.

    py -3.12 -m wedge_book.ledger              # write ledger.md / ledger.json, print the summary
    py -3.12 -m wedge_book.ledger --part 6     # what is left to write in one Part
"""

from __future__ import annotations

import json
import re
from dataclasses import asdict, dataclass, field
from pathlib import Path

from . import outline, plates, store

LEDGER_MD = store.BOOK_DIR / "ledger.md"
LEDGER_JSON = store.BOOK_DIR / "ledger.json"
MARKER = re.compile(r"<!--\s*concept:\s*([a-z0-9_]+)/([a-z0-9_]+)\s*-->")


# ----------------------------------------------------------------------
# The Parts, in book order. ``existing`` names the outline Part when there is
# one; a Part with none is proposed, and becomes real when it is written.
# ----------------------------------------------------------------------

@dataclass(frozen=True)
class PartPlan:
    key: str
    title: str
    existing: str = ""          # the outline Part's title, if it exists
    note: str = ""


PARTS: tuple[PartPlan, ...] = (
    PartPlan("right", "What Actually Has to Be Right", "What Actually Has to Be Right"),
    PartPlan("geometry", "The Geometry, From Scratch", "The Geometry, From Scratch"),
    PartPlan("stick", "The Stick", "The Stick", "the tree, the log, the split, the member, its finish"),
    PartPlan("panel", "The Panel", "The Panel", "the joint, the jig, the cuts, the work itself"),
    PartPlan("skin", "The Skin", "The Skin", "raising, the cap, the layers"),
    PartPlan("seam", "The Seam at Work", "The Seam at Work", "the channel, air, water, metal"),
    PartPlan("floor", "The Floor and the Ground", "The Floor and the Ground"),
    PartPlan("economics", "What It Costs and What It Is Worth", "",
             "proposed: the tree's value, labour, debt, the chain of middlemen"),
    PartPlan("network", "The Network", "The Network"),
    PartPlan("shapes", "Other Shapes", "Other Shapes"),
    PartPlan("catalogue", "The Catalogue", "The Catalogue"),
    PartPlan("living", "Living in a Round Room", "",
             "proposed: interiors, furnishing, the people in the room"),
    PartPlan("stemcell", "The Stem Cell", "The Stem Cell"),
    PartPlan("variations", "Variations", "Variations", "salvage domes, the floating dome"),
    PartPlan("tools", "The Tools", "The Tools", "the software, and the arithmetic of drawing it"),
    PartPlan("stories", "Appendix: The Stories", "",
             "proposed: the dramatised films, as stories rather than lessons"),
)
PART = {p.key: p for p in PARTS}


# ----------------------------------------------------------------------
# The films, in priority order: when two films teach the same chapter, the
# earlier one here is the one the concept is filed under.
# ----------------------------------------------------------------------

@dataclass(frozen=True)
class FilmPlan:
    key: str
    role: str          # teach | variant | fiction | scaffold
    home: str          # the Part its chapters go to by default
    mixed: bool = False
    variant_of: str = ""
    note: str = ""


FILMS: tuple[FilmPlan, ...] = (
    FilmPlan("cabin_wedge_explained", "teach", "stick", True),
    FilmPlan("wedge", "teach", "stick", True),
    FilmPlan("why", "teach", "stick", True),
    FilmPlan("harvest", "teach", "stick", True),
    FilmPlan("cabin_linseed_oil", "teach", "stick"),
    FilmPlan("2v", "teach", "geometry", True),
    FilmPlan("scratch", "teach", "geometry", True),
    FilmPlan("cuts", "teach", "panel"),
    FilmPlan("build", "teach", "panel", True),
    FilmPlan("line", "teach", "panel"),
    FilmPlan("seam", "teach", "seam"),
    FilmPlan("cabin_seam_climate", "teach", "seam"),
    FilmPlan("why_build", "teach", "economics"),
    FilmPlan("pine_value", "teach", "economics"),
    FilmPlan("dome_park", "teach", "network", True),
    FilmPlan("byod", "teach", "network", True),
    FilmPlan("hex", "teach", "shapes"),
    FilmPlan("zome", "teach", "shapes"),
    FilmPlan("world", "teach", "catalogue"),
    FilmPlan("world_chatgpt", "teach", "catalogue", True),
    FilmPlan("all_domes", "teach", "catalogue"),
    FilmPlan("look", "teach", "living"),
    FilmPlan("seed_pitch", "teach", "stemcell", True),
    FilmPlan("module_build", "teach", "stemcell"),
    FilmPlan("pitch_hero", "teach", "stemcell"),
    FilmPlan("kick", "teach", "stemcell"),
    FilmPlan("kick2", "teach", "stemcell"),
    FilmPlan("franken", "teach", "variations"),
    FilmPlan("hype", "teach", "variations", True),
    FilmPlan("master", "teach", "right", True,
             note="a compilation: most of it folds into the films it was cut from"),
    # Re-cuts: their chapters fold into the film they re-cut.
    FilmPlan("hype2", "variant", "variations", variant_of="hype"),
    FilmPlan("hype3", "variant", "variations", variant_of="hype"),
    FilmPlan("hype4", "variant", "variations", variant_of="hype"),
    FilmPlan("hype5", "variant", "variations", variant_of="hype"),
    FilmPlan("hype6", "variant", "variations", variant_of="hype"),
    FilmPlan("byod_deepseek", "variant", "network", variant_of="byod"),
    FilmPlan("byod_polished", "variant", "network", variant_of="byod"),
    FilmPlan("byod_snarky", "variant", "network", variant_of="byod"),
    FilmPlan("drama", "fiction", "stories"),
    FilmPlan("series", "fiction", "stories"),
    FilmPlan("pvtwo", "scaffold", "economics",
             note="an unfinished scaffold: its own screen says to replace its classes"),
    FilmPlan("cabin_pilot", "scaffold", "tools", note="the two-chapter Cabin World pilot"),
)
FILM = {f.key: f for f in FILMS}

#: For mixed films: the first rule whose pattern matches a chapter's title and
#: promise decides its Part. Ordered most specific first.
RULES: tuple[tuple[str, str], ...] = (
    ("seam", r"\bseams?\b|channel|\bkeys?\b|\bdew\b|humid|desiccant|peltier|gutter|\bducts?\b|spacer|rosette|condens"),
    ("tools", r"pixel|upload|\blens\b|shader|render|\bforge\b|rasteri|depth buffer|\bengine\b|view matrix|\bcamera\b|on screen|\bscreen\b"),
    ("network", r"\bhosts?\b|tenant|\bpark\b|\brent|supporter|\brv\b"),
    ("economics", r"\bcosts?\b|price|dollar|\$|\bdebt\b|interest|labou?r|\bwages?\b|economic|commodity|dealer|factory|mortgage|money|board feet"),
    ("floor", r"foundation|footing|\bpad\b|\bdeck\b|\bfloors?\b"),
    ("panel", r"\bpanels?\b|\bjig\b|pinwheel|\bbutt\b|\bfence\b|\bsled\b|mitre|miter|bevel|\btilt\b|assembly|motion|\bdoors?\b|window|opening|\bhubs?\b"),
    ("skin", r"\bskin\b|\bcap\b|insulat|\blayers?\b|\bhats?\b|membrane|cladding|sheath|\braise|raising|storm|weather|\broof"),
    ("geometry", r"icosa|\bphi\b|golden|\bchords?\b|sphere|frequenc|subdivi|midpoint|triangle|hemisphere|vert(ex|ices)|geodesic|projection|transformation|\bshell\b"),
    ("stick", r"\blogs?\b|\btrees?\b|split|wedge|\brip|\bfell|\bbuck|kerf|grain|timber|board|\bstick|member|section|\bsaw"),
)

#: Hand placements, by (film, chapter slug) -> Part key, for what the rules get wrong.
OVERRIDES: dict[tuple[str, str], str] = {}


def _overrides_by_title() -> dict[tuple[str, str], str]:
    """Hand placements written by chapter title, resolved to slugs at load.

    Titles are what a person reads in ledger.md, so they are what a person
    writes here; the slug is looked up so a renamed chapter fails loudly."""
    return {
        ("why", "This is the actual solved shell"): "geometry",
        ("why", "Why the lumpy one stays up"): "right",
        ("build", "Why the lumpy one stays up"): "right",
        ("wedge", "Squaring the circle"): "stick",
        ("wedge", "Why the network carries the load"): "right",
        ("wedge", "The pinwheel, measured"): "panel",
        ("why", "The pinwheel, measured"): "panel",
        ("cabin_wedge_explained", "How much room"): "seam",
        ("cabin_wedge_explained", "Two lengths, flat panels"): "panel",
        ("cabin_wedge_explained", "No hubs"): "panel",
        ("build", "Build the triangles flat, first"): "panel",
        ("build", "Choosing your radius"): "geometry",
        # From Scratch's second half is how the picture is drawn, not the dome.
        **{("scratch", t): "tools" for t in (
            "A line with no thickness", "Building one strut", "Which way does a triangle face?",
            "The normal, the area and the winding", "The model becomes a list of numbers",
            "Where things are: world space", "The projection matrix",
            "The divide that makes distance work", "Why depth precision runs out",
            "Throwing away half of everything", "How bright is this surface?",
            "The lighting equation this film runs", "Glass, and why order comes back",
            "And then it does it again", "The whole chain, once more")},
        ("hype", "Who is behind this"): "right",
        ("hype", "Three phases"): "network",
        ("byod", "How much shell can carry solar?"): "skin",
        ("seed_pitch", "The shell is a boat hull"): "skin",
        ("seed_pitch", "The core moves to the next dome"): "stemcell",
        ("build", "The wall as the filter"): "skin",
        ("master", "Every saw setting, measured off the model"): "panel",
        ("why", "Forty frames, not one lattice"): "panel",
        # Part 3 review: joints and panels belong to The Panel...
        **{("wedge", t): "panel" for t in (
            "Forty independent frames", "The corner nothing touches", "Neighbours do not share",
            "Forty frames, lifted whole")},
        **{("why", t): "panel" for t in (
            "The V bracket that made it possible", "What holds the wedge dome together",
            "Neighbours never share a stick", "The cut I said did not exist",
            "How many settings it really takes", "The angle nobody wants to cut",
            "The cut that is never measured", "What the fixture is enforcing",
            "A dome from whatever the woodlot gives")},
        ("build", "Borrowing strength from the site"): "panel",
        # ...the channel to The Seam...
        **{("cabin_wedge_explained", t): "seam" for t in (
            "The sizes we assumed", "Or start with a bigger log", "Two rules")},
        ("seed_pitch", "The gap nobody wanted"): "seam",
        # ...and money, the chain and the house to What It Costs.
        **{("harvest", t): "economics" for t in (
            "What the house numbers rest on", "Where a house's time goes",
            "What the fortnight is worth", "Every part of the house",
            "Where the saving comes from", "What this does not show")},
        **{("why", t): "economics" for t in (
            "Machines that stop being necessary", "Counting the machines out",
            "Fifteen sets of hands", "The part nobody counts", "The same frame, bought")},
        # Part 4 review: the hubbed build is the alternative method...
        **{("build", t): "variations" for t in (
            "The five words we will keep using", "Two lengths, and nothing else",
            "Choose the hub system before anything else", "Centre length is not cut length",
            "The end-cut angle is half the central angle", "The panel bevels",
            "How many kinds of joint", "Buying the stock", "Cutting: a stop block and a master",
            "Build the triangles flat, first", "The four things that actually go wrong",
            "The franken-dome", "Borrowing strength from the site")},
        ("2v", "Panels, hubs, and build sequence"): "variations",
        ("hype", "Three hours later"): "variations",
        # ...raising and skinning are The Skin, the tube is The Seam...
        **{("build", t): "skin" for t in (
            "The dome is four rings and a crown", "Setting out the base", "The riser wall",
            "Closing the crown", "Skinning it, rim upward", "Forty panels from one sheet")},
        ("seed_pitch", "What actually closes a triangle"): "skin",
        ("byod", "The size sets a limit"): "skin",
        **{("build", t): "seam" for t in (
            "The tube around the bottom", "Run it either way", "What would actually decide it")},
        # ...and swapping parts is Part 1's argument.
        ("hype", "Every answer is yes"): "right",
        ("hype", "And whatever comes next"): "right",
        ("byod", "Buy for the next two steps"): "stemcell",
        ("seed_pitch", "The member we want to make instead"): "variations",
    }


# ----------------------------------------------------------------------
# The ledger itself
# ----------------------------------------------------------------------

@dataclass
class Concept:
    film: str
    slug: str
    title: str
    promise: str
    part: str
    placed_by: str                 # home | rule | override | variant | fiction
    status: str = "missing"        # embodied | mentioned | missing | held
    book_chapter: int = 0          # where it is embodied, when it is
    plate: str = ""                # the picture that carries it, or the one to make
    plate_exists: bool = False
    also_in: list[str] = field(default_factory=list)   # duplicates folded into it

    @property
    def id(self) -> str:
        return f"{self.film}/{self.slug}"


def _norm(text: str) -> str:
    return re.sub(r"[^a-z0-9]+", " ", text.lower()).strip()


STOP = set("the a an of and to in is it its for on with one two what why how that "
           "this you your are be not as at by from or no every all into their them "
           "was were has have had will can than then so but if out up".split())


def _book_text() -> tuple[dict[int, str], set[str], dict[str, int]]:
    """Each chapter's text, the plate keys printed anywhere, and concept markers."""
    texts, printed, markers = {}, set(), {}
    link = re.compile(r"\]\(([a-z0-9\-]+)\.png\)")
    for chapter in outline.BOOK.chapters:
        path = chapter.path(outline.MANUSCRIPT_DIR)
        if not path.is_file():
            continue
        text = path.read_text(encoding="utf-8")
        texts[chapter.number] = text.lower()
        printed |= set(link.findall(text))
        for film, slug in MARKER.findall(text):
            markers.setdefault(f"{film}/{slug}", chapter.number)
    return texts, printed, markers


def _place(film: FilmPlan, chapter) -> tuple[str, str]:
    if (film.key, chapter.slug) in OVERRIDES:
        return OVERRIDES[(film.key, chapter.slug)], "override"
    if film.role == "fiction":
        return "stories", "fiction"
    if film.mixed:
        text = f"{chapter.title} {chapter.promise}".lower()
        for part, pattern in RULES:
            if re.search(pattern, text):
                return part, "rule"
    return film.home, "home"


def _resolve_overrides(lessons) -> None:
    for (film, title), part in _overrides_by_title().items():
        lesson = lessons.get(film)
        if lesson is None:
            continue
        slug = next((c.slug for c in lesson.chapters if c.title == title), None)
        if slug is not None:
            OVERRIDES[(film, slug)] = part


def build() -> list[Concept]:
    from two_v_demo.lesson_registry import LESSONS

    _resolve_overrides(LESSONS)
    texts, printed, markers = _book_text()
    whole = " ".join(texts.values())
    plate_by = {(p.lesson, p.chapter): p for p in plates.PLATES}
    concepts: list[Concept] = []
    seen: dict[str, Concept] = {}          # normalised title+promise -> concept

    for film in FILMS:
        lesson = LESSONS.get(film.key)
        if lesson is None:
            continue
        for chapter in lesson.chapters:
            if chapter.stage.startswith("seg_"):
                continue
            ident = f"{film.key}/{chapter.slug}"
            sig = _norm(f"{chapter.title} | {chapter.promise}")
            if film.role == "variant":
                target = seen.get(sig)
                if target is not None:
                    target.also_in.append(ident)
                    continue
            elif film.role == "teach" and sig in seen and seen[sig].film != film.key:
                seen[sig].also_in.append(ident)
                continue
            part, how = _place(film, chapter)
            if film.role == "variant":
                how = "variant"
            c = Concept(film.key, chapter.slug, chapter.title, chapter.promise, part, how)
            plate = plate_by.get((film.key, chapter.slug))
            if plate is not None:
                c.plate, c.plate_exists = plate.key, plate.path.is_file()
            else:
                c.plate = f"plate-{film.key.replace('_', '-')}-{chapter.slug.replace('_', '-')}"
            if film.role == "scaffold":
                c.status = "held"
            elif ident in markers:
                c.status, c.book_chapter = "embodied", markers[ident]
            elif plate is not None and plate.key in printed:
                c.status, c.book_chapter = "embodied", plate.book_chapter
            else:
                words = {w for w in re.findall(r"[a-z][a-z'-]{3,}", sig) if w not in STOP}
                if len(words) >= 2 and sum(1 for w in words if w in whole) / len(words) >= 0.8:
                    c.status = "mentioned"
            seen.setdefault(sig, c)
            concepts.append(c)

    order = {p.key: i for i, p in enumerate(PARTS)}
    rank = {f.key: i for i, f in enumerate(FILMS)}
    film_order = {(c.film, c.slug): n for n, c in enumerate(concepts)}
    concepts.sort(key=lambda c: (order[c.part], rank[c.film], film_order[(c.film, c.slug)]))
    return concepts


# ----------------------------------------------------------------------
# Reports
# ----------------------------------------------------------------------

MARK = {"embodied": "[x]", "mentioned": "[~]", "missing": "[ ]", "held": "[-]"}


def summary(concepts: list[Concept]) -> list[tuple[PartPlan, dict]]:
    rows = []
    for part in PARTS:
        mine = [c for c in concepts if c.part == part.key]
        counts = {s: sum(1 for c in mine if c.status == s) for s in MARK}
        counts["total"] = len(mine)
        rows.append((part, counts))
    return rows


def markdown(concepts: list[Concept]) -> str:
    from two_v_demo.lesson_registry import LESSONS

    rows = summary(concepts)
    teach = [c for c in concepts if c.status != "held"]
    done = sum(1 for c in teach if c.status == "embodied")
    out = ["# The concept ledger", "",
           "Every lesson in every film, placed in the book's order. Generated by "
           "`py -3.12 -m wedge_book.ledger` from the film registry and the manuscript; "
           "do not edit by hand -- change `wedge_book/ledger.py` (placements) or the "
           "manuscript (markers) and regenerate.", "",
           f"**{done} of {len(teach)} concepts embodied** "
           f"({100 * done / max(1, len(teach)):.0f}%), "
           f"{sum(1 for c in teach if c.status == 'mentioned')} mentioned, "
           f"{sum(1 for c in teach if c.status == 'missing')} missing. "
           f"{sum(len(c.also_in) for c in concepts)} duplicate chapters folded in.", "",
           "`[x]` embodied -- a section is about it, or its picture is printed  ",
           "`[~]` mentioned -- the book uses its words; no section is about it yet  ",
           "`[ ]` missing  ",
           "`[-]` held -- the film is unfinished", "",
           "To mark a concept embodied, write it up and put "
           "`<!-- concept: film/slug -->` in the section that does.", "",
           "| # | Part | concepts | embodied | mentioned | missing |", "|---|---|---|---|---|---|"]
    for n, (part, k) in enumerate(rows, 1):
        flag = "" if part.existing else " *(proposed)*"
        out.append(f"| {n} | {part.title}{flag} | {k['total']} | {k['embodied']} | "
                   f"{k['mentioned']} | {k['missing']} |")
    for n, (part, k) in enumerate(rows, 1):
        out += ["", f"## {n}. {part.title}" + ("" if part.existing else " *(proposed)*"), ""]
        if part.note:
            out += [f"*{part.note}*", ""]
        film = None
        for c in (c for c in concepts if c.part == part.key):
            if c.film != film:
                film = c.film
                title = LESSONS[film].title if film in LESSONS else film
                out += ["", f"**{title}** (`{film}`)", ""]
            where = f" -- ch {c.book_chapter}" if c.book_chapter else ""
            pic = f" -- `{c.plate}`" + ("" if c.plate_exists else " (to render)")
            dup = f" -- also in {', '.join(c.also_in[:3])}" + ("..." if len(c.also_in) > 3 else "") if c.also_in else ""
            how = "" if c.placed_by in ("home", "fiction") else f" -- placed by {c.placed_by}"
            out.append(f"- {MARK[c.status]} **{c.title}** -- {c.promise} `{c.id}`{where}{pic}{how}{dup}")
    return "\n".join(out) + "\n"


def write(concepts: list[Concept] | None = None) -> tuple[Path, Path]:
    concepts = concepts if concepts is not None else build()
    LEDGER_MD.write_text(markdown(concepts), encoding="utf-8")
    LEDGER_JSON.write_text(json.dumps([{**asdict(c), "id": c.id} for c in concepts], indent=1),
                           encoding="utf-8")
    return LEDGER_MD, LEDGER_JSON


def validate_ledger() -> None:
    """Every film chapter is accounted for, exactly once, in a real Part."""
    from two_v_demo.lesson_registry import LESSONS

    # Every film in the registry is in the plan (re-staged copies and teasers
    # are renderings of a film already listed, not films of their own).
    films = {k for k in LESSONS
             if not k.startswith(("teaser_", "concept_"))
             and not (k.startswith("cabin_") and k[6:] in LESSONS)}
    unplanned = sorted(films - set(FILM))
    assert not unplanned, f"films with no place in the ledger: {unplanned}"
    for f in FILMS:
        assert f.home in PART, (f.key, f.home)
        assert f.role in ("teach", "variant", "fiction", "scaffold"), f.key
        if f.role == "variant":
            assert FILM.get(f.variant_of, FilmPlan("", "", "")).role == "teach", f.key
    for part, _pattern in RULES:
        assert part in PART, part
    for value in OVERRIDES.values():
        assert value in PART, value
    # The outline's Parts are all in the plan, in the same order.
    planned = [p.existing for p in PARTS if p.existing]
    actual = [p.title for p in outline.BOOK.parts]
    assert planned == actual, f"the ledger's Parts are out of step with the outline: {actual}"

    concepts = build()
    ids = [c.id for c in concepts]
    assert len(ids) == len(set(ids)), "a concept is listed twice"
    folded = {d for c in concepts for d in c.also_in}
    accounted = set(ids) | folded
    for key in FILM:
        lesson = LESSONS.get(key)
        if lesson is None:
            continue
        for ch in lesson.chapters:
            if ch.stage.startswith("seg_"):
                continue
            assert f"{key}/{ch.slug}" in accounted, f"{key}/{ch.slug} is in no concept"
    # A concept the book says it embodies points at a chapter the book has.
    numbers = {c.number for c in outline.BOOK.chapters}
    for c in concepts:
        if c.status == "embodied":
            assert c.book_chapter in numbers, c.id


def main(argv: list[str] | None = None) -> int:
    import argparse

    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--part", type=int, default=0, help="list what is left in one Part")
    args = parser.parse_args(argv)
    validate_ledger()
    concepts = build()
    md, js = write(concepts)
    if args.part:
        part = PARTS[args.part - 1]
        todo = [c for c in concepts if c.part == part.key and c.status in ("missing", "mentioned")]
        print(f"Part {args.part}, {part.title}: {len(todo)} to write")
        for c in todo:
            print(f"  {MARK[c.status]} {c.id:<44} {c.title}")
        return 0
    for n, (part, k) in enumerate(summary(concepts), 1):
        print(f"{n:>2}. {part.title[:40]:<40}{'' if part.existing else ' (proposed)':<11}"
              f"{k['total']:>4} concepts  {k['embodied']:>3} embodied  "
              f"{k['mentioned']:>3} mentioned  {k['missing']:>3} missing")
    teach = [c for c in concepts if c.status != "held"]
    print(f"\n{sum(c.status == 'embodied' for c in teach)} of {len(teach)} embodied; "
          f"{sum(len(c.also_in) for c in concepts)} duplicate chapters folded in")
    print(f"wrote {md.relative_to(store.ROOT)} and {js.relative_to(store.ROOT)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
