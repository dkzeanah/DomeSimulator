"""*2 Trees: Build Your (D)Home* -- the whole book, as a structure.

This module is the outline: every part, every chapter, every page, in order,
with what each one is for, roughly how long it runs, which figures sit on it,
and -- crucially -- which function in this repository each of its numbers has
to come from.

Why the outline is code
-----------------------
Because the numbers are.  A book that says the dome is twenty-one and a half
feet across, and a simulator that says something else, is a book with an
erratum in it.  Every figure the manuscript prints is written as a token --
``{{dome.diameter_ft}}`` -- and resolved at export time from
:mod:`book_math`, which in turn derives from :mod:`wedge_geometry` and the
solved dome in ``geodesic_raw_wedge_dome_dihedral.py``.  Change the geometry
and the next export of the book says the new number, in every chapter that
mentions it, without anybody going looking.

Three books in one
------------------
The reader wanted a story, a manual and an explanation, and those are three
different reading speeds.  Rather than blend them into mush, each chapter
declares which one it is (:attr:`Chapter.strand`), the part pages say what
strand is coming, and a reader who only wants the manual can follow the
``howto`` chapters straight through.

What lives where
----------------
* This module -- structure, purpose, targets, figure placement.
* :mod:`book_math` -- every derived number, and the declared constants.
* :mod:`book_figures` -- how each illustration is actually rendered.
* :mod:`book_app` -- the desk you write it at.
* ``book/`` -- the manuscript itself, one Markdown file per chapter.
"""

from __future__ import annotations

from dataclasses import dataclass, replace, field
from pathlib import Path


ROOT = Path(__file__).resolve().parent.parent
BOOK_DIR = ROOT / "book"
MANUSCRIPT_DIR = BOOK_DIR / "manuscript"
EXPORT_DIR = ROOT / "deliverables" / "book"

WORDS_PER_PAGE = 340
"""Words on a set page at this trim and type size. Used only to turn word
targets into a believable page count; nothing depends on it being exact."""

TITLE = "2 Trees: Build Your (D)Home"
SUBTITLE = ("One small chainsaw, 120 wedge struts, and a geodesic dome "
            "in a fortnight")


# ----------------------------------------------------------------------
# The pieces
# ----------------------------------------------------------------------

PAGE_KINDS = {
    "part": "A full-page divider opening a part. Title, epigraph, and one "
            "line saying what strand of the book is coming.",
    "opener": "A chapter opening page: title, deck, and the promise of the "
              "chapter in two or three sentences.",
    "text": "Ordinary running prose.",
    "spread": "Two facing pages designed together -- usually an argument on "
              "the left and its picture on the right.",
    "plate": "A full-page image with a caption and nothing else.",
    "table": "A page whose content is a table generated from code.",
    "worked": "A worked example: numbers carried all the way through, with "
              "every intermediate shown.",
    "steps": "A numbered procedure the reader follows at the saw or the "
             "bench.",
    "sidebar": "A boxed aside that can be skipped without losing the thread.",
    "safety": "A boxed warning. These are not decorative and are never "
              "folded into running text.",
    "errata": "A correction to something this project published earlier, "
              "named before it is fixed.",
}

STRANDS = {
    "story": "What happened, in order, to a person with a saw.",
    "howto": "Do this, then this. Follow it and you get a dome.",
    "explain": "Why any of it works. Skippable by anyone in a hurry.",
    "reference": "Tables and lists you come back to, not read through.",
}


@dataclass(frozen=True)
class Figure:
    """One illustration, and where its pixels come from.

    ``source`` names a renderer in :mod:`book_figures`; ``spec`` is that
    renderer's own argument dictionary. Nothing here draws anything -- this
    is the placement and the caption, so that the outline can be read and
    reordered without waiting on a render.
    """

    key: str
    caption: str
    source: str
    spec: dict = field(default_factory=dict)
    full_page: bool = False
    note: str = ""
    """Anything the artist or renderer needs to know that a caption cannot
    carry -- what must be legible, what must not be cropped."""


@dataclass(frozen=True)
class Page:
    """One page, or one designed spread, of the finished book."""

    kind: str
    title: str
    purpose: str
    """What this page is for. If it cannot be said in a sentence, the page is
    doing two jobs and should be two pages."""
    words: int = 0
    figures: tuple[Figure, ...] = ()
    beats: tuple[str, ...] = ()
    """The points this page makes, in order. The writing desk shows these as
    a checklist so a half-written page is visibly half-written."""

    @property
    def sheets(self) -> int:
        """Typeset pages this page is likely to occupy.

        An outline entry is a unit of intent, not a sheet of paper: a
        1,100-word ``text`` entry is three pages once it is set. Kinds that
        are inherently one page stay one page however much caption they
        carry; a spread is two by definition; everything else is estimated
        from its word target so the running total means something.
        """
        if self.kind == "spread":
            return 2
        if self.kind in ("part", "plate"):
            return 1
        estimated = -(-self.words // WORDS_PER_PAGE)  # ceiling division
        return max(1, estimated)


@dataclass(frozen=True)
class Chapter:
    """One chapter: its pages, its strand, and where its numbers live."""

    number: int
    title: str
    deck: str
    strand: str
    pages: tuple[Page, ...]
    derives: tuple[str, ...] = ()
    """Fully-qualified callables every number in this chapter must trace to.
    Empty means the chapter states no figures at all, which is checked."""
    corrects: str = ""
    """If this chapter fixes something already published, what."""
    ref: str = ""
    """A short, stable name for cross-referencing this chapter.

    Chapter *numbers* move every time one is inserted, so prose that says
    "see Chapter 18" is stale the moment the outline changes -- exactly the
    failure the number tokens exist to prevent, applied to structure instead
    of arithmetic. Prose writes ``{{ch.method_a}}`` and gets the current
    number. Defaults to the title, slugged, which is fine for a chapter
    nothing points at."""

    section: str = ""
    """The group inside its part, when the part is too big to read as one run.

    A part prints one divider. When a part carries fifty chapters, one divider
    at the front of it is not enough navigation, and the honest fix is a second
    level rather than a longer part title. Empty means the chapter sits directly
    under its part, which is what every chapter did before this existed -- so a
    book that sets no sections renders exactly as it always did."""

    @property
    def key(self) -> str:
        """The stable identity used by ``{{ch.…}}`` cross-references.

        Deliberately *not* what names the manuscript file: giving a chapter
        a short ref should never rename anybody's file.
        """
        return self.ref or self._title_slug("_")

    def _title_slug(self, joiner: str) -> str:
        keep = [c.lower() if c.isalnum() else joiner for c in self.title]
        slug = "".join(keep)
        while joiner * 2 in slug:
            slug = slug.replace(joiner * 2, joiner)
        return slug.strip(joiner)

    @property
    def slug(self) -> str:
        """The manuscript filename stem: number, then the title."""
        return f"{self.number:02d}-{self._title_slug('-')}"

    @property
    def words(self) -> int:
        return sum(page.words for page in self.pages)

    @property
    def sheets(self) -> int:
        return sum(page.sheets for page in self.pages)

    @property
    def figures(self) -> tuple[Figure, ...]:
        return tuple(fig for page in self.pages for fig in page.figures)

    def path(self, root: Path = MANUSCRIPT_DIR) -> Path:
        return root / f"{self.slug}.md"


@dataclass(frozen=True)
class Part:
    """A group of chapters behind one divider page."""

    number: int
    title: str
    epigraph: str
    promise: str
    """The line printed on the part page: what the reader is about to get."""
    chapters: tuple[Chapter, ...]

    @property
    def words(self) -> int:
        return sum(chapter.words for chapter in self.chapters)

    @property
    def sheets(self) -> int:
        # One for the part page itself.
        return 1 + sum(chapter.sheets for chapter in self.chapters)

    @property
    def strands(self) -> tuple[str, ...]:
        seen: list[str] = []
        for chapter in self.chapters:
            if chapter.strand not in seen:
                seen.append(chapter.strand)
        return tuple(seen)


@dataclass(frozen=True)
class Matter:
    """Front or back matter: pages that carry no chapter number."""

    key: str
    title: str
    pages: tuple[Page, ...]

    @property
    def words(self) -> int:
        return sum(page.words for page in self.pages)

    @property
    def sheets(self) -> int:
        return sum(page.sheets for page in self.pages)


@dataclass(frozen=True)
class Book:
    """The whole thing."""

    title: str
    subtitle: str
    front: tuple[Matter, ...]
    parts: tuple[Part, ...]
    back: tuple[Matter, ...]

    @property
    def chapters(self) -> tuple[Chapter, ...]:
        return tuple(ch for part in self.parts for ch in part.chapters)

    @property
    def words(self) -> int:
        return (sum(m.words for m in self.front)
                + sum(p.words for p in self.parts)
                + sum(m.words for m in self.back))

    @property
    def sheets(self) -> int:
        return (sum(m.sheets for m in self.front)
                + sum(p.sheets for p in self.parts)
                + sum(m.sheets for m in self.back))

    @property
    def figures(self) -> tuple[Figure, ...]:
        out: list[Figure] = []
        for matter in self.front:
            out += [f for page in matter.pages for f in page.figures]
        for chapter in self.chapters:
            out += list(chapter.figures)
        for matter in self.back:
            out += [f for page in matter.pages for f in page.figures]
        return tuple(out)

    def chapter(self, number: int) -> Chapter:
        for chapter in self.chapters:
            if chapter.number == number:
                return chapter
        raise ValueError(f"no chapter {number}; the book has "
                         f"{len(self.chapters)}")

    def by_ref(self, ref: str) -> Chapter:
        """Look a chapter up by its stable ref rather than its number.

        Anything that names a specific chapter -- a test, a tool, a default
        -- should use this. Numbers move when the outline does, and code
        that hard-codes one goes quietly wrong rather than failing, which is
        precisely what happened to this book's own GUI self-test the first
        time three chapters were inserted.
        """
        for chapter in self.chapters:
            if chapter.key == ref:
                return chapter
        raise ValueError(
            f"no chapter with ref {ref!r}; known refs include "
            f"{', '.join(sorted(c.key for c in self.chapters)[:8])}...")


# ----------------------------------------------------------------------
# Shorthand, so the outline below reads as an outline
# ----------------------------------------------------------------------

def _p(kind: str, title: str, purpose: str, words: int = 0,
       figures: tuple[Figure, ...] = (), beats: tuple[str, ...] = ()) -> Page:
    return Page(kind=kind, title=title, purpose=purpose, words=words,
                figures=figures, beats=beats)


def _f(key: str, caption: str, source: str, full_page: bool = False,
       note: str = "", **spec) -> Figure:
    return Figure(key=key, caption=caption, source=source, spec=spec,
                  full_page=full_page, note=note)


# Renderer shorthands. Each names a function in book_figures.
DOME = "raw_wedge_world"        # the simulator's own solved dome
JIG = "raw_wedge_jig"           # the fabrication jig, at a stage
PANEL = "panel_jig_svg"         # flat panel drawing, straight from the sim
SHOT = "lesson_still"           # a frame from one of the films
PLOT = "book_plot"              # a chart drawn from book_math
DIAG = "book_diagram"           # a labelled line drawing from geometry
PHOTO = "photo_slot"            # a photograph the author supplies


# ======================================================================
# FRONT MATTER
# ======================================================================

FRONT: tuple[Matter, ...] = (
    Matter("title", "Title pages", (
        _p("plate", "Half-title", "The title alone, on a field of bark.",
           figures=(_f("front-bark", "", PHOTO, full_page=True,
                       note="Close bark texture, shallow depth of field. "
                            "No dome visible yet."),)),
        _p("plate", "Frontispiece",
           "The finished frame against sky, so the reader knows on page two "
           "what the book is for.",
           figures=(_f("front-frame", "The frame, day fourteen.", DOME,
                       full_page=True, orientation="point_dome_in",
                       view="hero", parts=("wood",)),)),
        _p("text", "Title page", "Title, subtitle, author, imprint.",
           words=40),
        _p("text", "Copyright and colophon",
           "Rights, edition, and the fact that every number in the book was "
           "generated by the software listed in the back.", words=220),
    )),
    Matter("orientation", "How to read this", (
        _p("text", "What this book is",
           "Set expectations honestly in one page: a story, a manual and an "
           "explanation, bound together.", words=650,
           beats=(
               "Two trees, one small saw, 120 struts, fourteen days.",
               "It is a real build, not a proposal.",
               "Three strands, and how to read only the one you want.",
               "Every number here is computed; the code is in the back.",
           )),
        _p("spread", "The three strands",
           "Show the strands as three tracks through the contents, so a "
           "reader can pick one and go.", words=500,
           figures=(_f("strand-map", "Three ways through this book.", DIAG,
                       diagram="strand_map"),)),
        _p("safety", "Before you start a saw",
           "The warning page. Chainsaws, felling, and the fact that this "
           "book is not an engineer's stamp.", words=600,
           beats=(
               "A chainsaw is the most dangerous tool most people ever hold.",
               "Felling kills people who have done it a hundred times.",
               "Chaps, helmet, gloves, boots, and never alone.",
               "Nothing here is a structural sign-off. Check your code.",
               "Where the book states a load figure, it says who to ask.",
           )),
        _p("table", "Every number in this book, and where it comes from",
           "The declared-constants table, printed before anything uses it.",
           words=350,
           figures=(_f("constants-table",
                       "Declared inputs, separated from derived results.",
                       PLOT, plot="declared_constants"),)),
    )),
)


# ======================================================================
# PART I -- TWO TREES
# ======================================================================

PART_I = Part(
    number=1,
    title="Two Trees",
    epigraph="I cut a tree, I rip the trunk, it is usable wood. Fifteen "
             "middlemen, gone.",
    promise="The story strand. How the method was found, and what it "
            "replaced.",
    chapters=(
        Chapter(
            1, "The Tree That Was Already Down",
            "A windfall pine, a small saw, and a question nobody had asked "
            "out loud",
            "story",
            (
                _p("opener", "The Tree That Was Already Down",
                   "Open on the specific tree. Ground the whole book in one "
                   "object before any theory arrives.", words=400),
                _p("text", "Sixty feet of pine, and no way to use it",
                   "Establish the problem: a fallen tree is not lumber, and "
                   "the gap between them is where all the money is.",
                   words=1100,
                   beats=(
                       "Trunk measured: butt, top, usable straight length.",
                       "What a mill would charge to convert it.",
                       "What it costs to haul, and to wait.",
                       "The saw on the shelf cost less than the haul.",
                   )),
                _p("spread", "The tree, measured",
                   "Put the actual trunk on the page with its dimensions, "
                   "because every number later in the book descends from it.",
                   words=350,
                   figures=(_f("tree-measured",
                               "The book's tree: {{tree.butt_diameter_in}} "
                               "inches at the butt, "
                               "{{tree.top_diameter_in}} at the top, "
                               "{{tree.usable_length_ft}} feet of usable "
                               "trunk.", DIAG, diagram="tree_taper"),)),
                _p("text", "What I actually wanted",
                   "State the goal plainly: a round house, built alone, out "
                   "of what was on the ground.", words=800),
            ),
            derives=("book_math.BOOK_TREE",),
        ),
        Chapter(
            2, "Fifteen Middlemen",
            "Why a two-by-four costs what it costs, and how much of that is "
            "wood",
            "explain",
            (
                _p("opener", "Fifteen Middlemen",
                   "Frame the economic argument that motivates everything "
                   "after it.", words=350),
                _p("text", "From stump to rack",
                   "Walk the actual chain: fell, skid, haul, scale, saw, "
                   "edge, trim, dry, plane, grade, bundle, ship, stock, "
                   "shelve, sell.", words=1200),
                _p("spread", "The chain, and where the wood goes",
                   "Show recovery falling at each step of industrial "
                   "conversion against the single step here.", words=450,
                   figures=(_f("middlemen-chain",
                               "Every step between a standing tree and a "
                               "board on a rack.", DIAG,
                               diagram="middlemen_chain"),)),
                _p("text", "The price of a 2x4, taken apart",
                   "Use the declared shelf price and say honestly how little "
                   "of it is the tree.", words=900),
                _p("sidebar", "Nominal, dressed, and the missing third",
                   "A 2x4 is 1.5 by 3.5. This matters later, in the money "
                   "chapter, so it is established here.", words=400,
                   beats=(
                       "Nominal 2x4 is {{board.nominal_in2}} square inches.",
                       "Dressed 2x4 is {{board.dressed_in2}}.",
                       "The book compares against both, and says which.",
                   )),
            ),
            derives=("book_math.DECLARED",
                     "book_math.NOMINAL_TWO_BY_FOUR_IN2",
                     "book_math.DRESSED_TWO_BY_FOUR_IN2"),
        
            ref="middlemen",
        ),
        Chapter(
            3, "The Frankendome",
            "Forty triangles, no two struts alike, and the failure that "
            "taught the method",
            "story",
            (
                _p("opener", "The Frankendome",
                   "The build before this one. It worked, and it was awful, "
                   "and that is why the wedge exists.", words=400),
                _p("text", "Strut-agnostic, and what that cost",
                   "Explain the earlier idea: join forty triangles edge to "
                   "edge from the top down, any stick anywhere.", words=1000),
                _p("plate", "The frankendome standing",
                   "One full page of the lumpy frame, so the reader sees the "
                   "before.",
                   figures=(_f("franken-standing",
                               "The frankendome: it stood, and no two "
                               "members matched.", SHOT, full_page=True,
                               lesson="franken", second=42.0),)),
                _p("text", "The ten-piece pentagon",
                   "The one part of the frankendome that was genuinely "
                   "better, and carried forward.", words=750),
                _p("text", "Why I stopped",
                   "Name the real failure: nothing repeated, so nothing "
                   "could be jigged.", words=650),
            ),
            derives=("hubless_geometry.hubless_summary",),
        ),
        Chapter(
            4, "The V-Bracket Afternoon",
            "Trying to join shapes that have nothing in common",
            "story",
            (
                _p("opener", "The V-Bracket Afternoon",
                   "The middle step: brackets that could join anything to "
                   "anything.", words=350),
                _p("text", "A bracket that does not care",
                   "Why the V shape tolerates members of unlike section, and "
                   "why that tolerance was a warning sign.", words=950),
                _p("spread", "Four joints that nearly worked",
                   "Show the bracket attempts side by side with what each "
                   "one could not do.", words=400,
                   figures=(_f("bracket-attempts",
                               "Four joints, and the one thing each could "
                               "not do.", DIAG, diagram="bracket_attempts"),)),
                _p("text", "The question that ended it",
                   "If the bracket has to absorb every difference, what "
                   "would it take for there to be no difference?",
                   words=600),
            ),
        ),
        Chapter(
            5, "The Cut That Changed It",
            "Split the trunk like a cake, and the stick is already the right "
            "shape",
            "story",
            (
                _p("opener", "The Cut That Changed It",
                   "The discovery, told as it happened, without hindsight "
                   "tidying it.", words=400),
                _p("text", "Half, half, half again",
                   "Three passes, eight sectors, no squaring at all.",
                   words=900),
                _p("spread", "One trunk, eight sticks",
                   "The single most important picture in the book: the round "
                   "section becoming eight identical wedges.", words=350,
                   figures=(_f("trunk-eighths",
                               "Three cuts. Eight structural members. Nothing "
                               "squared, nothing planed.", DIAG,
                               diagram="trunk_eighths"),)),
                _p("text", "What became obvious immediately",
                   "Same section everywhere, so one jig; four orientations, "
                   "so four behaviours from one stick.", words=850),
                _p("text", "And what took another week",
                   "The honest part: the seam angles are not all the same, "
                   "and that took days to accept.", words=700),
            ),
            derives=("wedge_geometry.SECTORS_PER_LOG",
                     "wedge_geometry.sector_chord_in",
                     "wedge_geometry.sector_depth_in",
                     "book_math.panel_seam_count",
                     "book_math.BOOK_TREE.recovery"),
        
            ref="the_cut",
        ),
    ),
)


# ======================================================================
# PART II -- WHY A DOME LETS YOU DO THIS
# ======================================================================

PART_II = Part(
    number=2,
    title="Why a Dome Lets You Do This",
    epigraph="We can only use this method because of the dome's inherent "
             "structure.",
    promise="The explanation strand. Skip it if you only want the manual, "
            "but the method does not transfer to a square house and this is "
            "the chapter that says why.",
    chapters=(
        Chapter(
            6, "Triangles Do Not Care What Shape Your Stick Is",
            "Why a triangulated frame can accept a member no mill would sell",
            "explain",
            (
                _p("opener", "Triangles Do Not Care",
                   "The central permission: triangulation makes section "
                   "shape a detail.", words=400),
                _p("text", "Axial, not bending",
                   "A triangulated member is pushed or pulled along its "
                   "length; it is not asked to be flat.", words=1000),
                _p("spread", "The same load, two frames",
                   "Rectangular frame racking beside a triangulated one "
                   "standing.", words=400,
                   figures=(_f("racking-compare",
                               "A rectangle needs a sheet to stand. A "
                               "triangle does not.", DIAG,
                               diagram="racking_compare"),)),
                _p("text", "What the wedge is good at",
                   "Depth from pith to bark is where the stiffness is, and "
                   "the wedge has more of it than a 2x4.", words=800),
                _p("sidebar", "One eighth of a tree",
                   "Put the section area on the page against a 2x4's, both "
                   "ways.", words=350),
            ),
            derives=("book_math.BOOK_TREE.member_area_in2",
                     "wedge_geometry.bearing_area_in2"),
        
            ref="triangles",
        ),
        Chapter(
            7, "Not a Worse Two-by-Four",
            "The head-to-head nobody runs honestly, run honestly",
            "explain",
            (
                _p("opener", "Not a Worse Two-by-Four",
                   "Meet the objection head on: is a split log actually as "
                   "good as a board? Answer it with numbers, including the "
                   "one that says no.", words=450),
                _p("text", "The rectangle is not the tree's idea",
                   "Establish that dimensional lumber is a manufacturing "
                   "choice made for rectangular buildings, not a property "
                   "of wood.", words=800,
                   beats=(
                       "A tree is round; a 2x4 is what a mill does to it.",
                       "That process exists because houses are rectangles.",
                       "When the building is not a rectangle, the question "
                       "reopens.",
                   )),
                _p("text", "More wood, from a modest tree",
                   "The area comparison, on the small log rather than the "
                   "flattering one.", words=800,
                   beats=(
                       "An {{versus.diameter_in}}-inch log, split "
                       "{{tree.sectors}} ways: {{versus.wedge_area_in2}} "
                       "square inches a stick.",
                       "A dressed 2x4 is {{board.dressed_in2}}.",
                       "That is {{versus.area_gain_pct}} per cent more wood.",
                       "A bigger log widens the gap; this is the "
                       "conservative case.",
                   )),
                _p("spread", "The two sections, side by side",
                   "Draw both cross-sections at the same scale with their "
                   "properties called out.", words=400,
                   figures=(_f("section-compare",
                               "One eighth of an {{versus.diameter_in}}-inch "
                               "log against a dressed 2x4, at the same "
                               "scale.", DIAG,
                               diagram="section_compare"),)),
                _p("text", "And now the number that does not help",
                   "Area is not strength. Compute the bending comparison "
                   "and report it plainly.", words=900,
                   beats=(
                       "Bending depends on where the wood is, not just how "
                       "much.",
                       "A wedge puts a lot of its wood near the pith.",
                       "Stiffness comes out {{versus.stiffness_pct}} per "
                       "cent against a 2x4 on edge -- effectively equal.",
                       "Bending strength comes out "
                       "{{versus.strength_pct}} per cent. That is worse.",
                       "Against the same board laid flat it is "
                       "{{versus.flat_stiffness_ratio}} times stiffer.",
                   )),
                _p("table", "The comparison in full",
                   "Every column, flattering and not.", words=250,
                   figures=(_f("versus-table",
                               "{{versus.verdict}}", PLOT,
                               plot="wedge_versus_board"),)),
                _p("text", "Which is the right question",
                   "Reframe: in a triangulated frame members are loaded "
                   "along their length, and there area is what counts.",
                   words=850,
                   beats=(
                       "A rectangular building asks pieces to be beams.",
                       "A triangulated one asks them to be struts.",
                       "For a strut, cross-section area carries the load.",
                       "So the wedge's {{versus.area_gain_pct}} per cent is "
                       "the number that applies, and its bending deficit is "
                       "the one that mostly does not.",
                       "Mostly. Panels do see bending from wind and snow, "
                       "and that is where the deficit is real.",
                   )),
                _p("text", "What this chapter does not claim",
                   "Fence the argument honestly so nobody quotes it "
                   "wrongly.", words=650,
                   beats=(
                       "Not that a wedge beats a 2x4 as a floor joist.",
                       "Not that it beats one as a stud, a rafter or a "
                       "shelf.",
                       "Only that inside a frame designed around it, it is "
                       "a better use of the tree.",
                   )),
            ),
            derives=("book_math.wedge_versus_board",
                     "book_math.sector_section",
                     "book_math.board_section"),
            ref="versus_board",
        ),
        Chapter(
            8, "Forty Panels, One Hundred and Twenty Members",
            "The 2V hemisphere, counted",
            "explain",
            (
                _p("opener", "Forty Panels", "Introduce the frame itself.",
                   words=350),
                _p("text", "Where 2V comes from",
                   "Icosahedron, one subdivision, projected to a sphere, cut "
                   "at the equator.", words=1000),
                _p("plate", "The frame, exploded",
                   "Full page: forty panels pushed apart along their own "
                   "normals.",
                   figures=(_f("frame-exploded",
                               "Forty panels, {{frame.members}} members, "
                               "{{frame.seams}} seams between them.", DOME,
                               full_page=True, view="exploded",
                               explode_in=8.0, palette="simulator",
                               parts=("wood", "rigid")),)),
                _p("table", "What the frame contains",
                   "Counts, straight from the geometry, with the rim edges "
                   "separated from the seams.", words=300,
                   figures=(_f("frame-counts",
                               "Counted from the solved dome, not chosen.",
                               PLOT, plot="frame_counts"),)),
                _p("text", "Why hemispheres and not spheres",
                   "The rim is where the frame meets the ground and where "
                   "ten edges join nothing.", words=700),
            ),
            derives=("book_math.frame_counts", "book_math.panel_seam_count"),
        ),
        Chapter(
            9, "Two Lengths, Not Forty",
            "The whole reason a dome can be built by one person",
            "explain",
            (
                _p("opener", "Two Lengths", "The repeatability argument.",
                   words=300),
                _p("text", "Short and long",
                   "A 2V dome has two edge classes. Everything else follows "
                   "from that.", words=850),
                _p("table", "The member schedule",
                   "The four member classes with their counts and lengths, "
                   "generated.", words=250,
                   figures=(_f("member-classes",
                               "Every stick in the dome, in four lengths.",
                               PLOT, plot="member_classes"),)),
                _p("text", "Why the pinwheel splits two into four",
                   "The inset that avoids mitres makes each class into two "
                   "near-identical lengths, and that is a feature.",
                   words=800),
            ),
            derives=("wedge_geometry.member_classes",),
        ),
        Chapter(
            10, "Compression, Tension, and One Eighth of a Tree",
            "What a wedge strut can actually carry",
            "explain",
            (
                _p("opener", "One Eighth of a Tree",
                   "Move from geometry to force.", words=350),
                _p("text", "Along the grain, and across it",
                   "The two directions that matter, and which one the joints "
                   "load.", words=1000),
                _p("text", "The end-to-side bearing",
                   "The end of a sector is the sector: nothing is notched "
                   "away to make the joint.", words=800),
                _p("safety", "What this book will not tell you",
                   "State the limit clearly: allowable stresses are species, "
                   "grade and moisture dependent, and a book cannot grade "
                   "your tree.", words=450),
                _p("sidebar", "The number I will give you",
                   "Bearing area, which is geometry, versus allowable "
                   "pressure, which is not.", words=400),
            ),
            derives=("wedge_geometry.bearing_area_in2",
                     "book_math.DECLARED"),
        
            ref="forces",
        ),
        Chapter(
            11, "What a Dome Costs You",
            "The chapter that argues against the book",
            "explain",
            (
                _p("opener", "What a Dome Costs You",
                   "State up front that this chapter is here to talk the "
                   "reader out of it if it should.", words=400),
                _p("text", "Furniture does not fit a curve",
                   "Honest accounting of the round-room problem.",
                   words=800),
                _p("text", "Roofing a compound surface",
                   "Where domes leak, why, and what it costs to stop.",
                   words=900),
                _p("text", "Permits, appraisals and resale",
                   "The non-technical costs nobody puts in a dome book.",
                   words=750),
                _p("text", "When to build a rectangle",
                   "The genuine cases where this method is the wrong "
                   "answer.", words=600),
            ),
            derives=("dome_costing.costing_report",),
        
            ref="dome_costs",
        ),
    ),
)


# ======================================================================
# PART III -- THE WEDGE
# ======================================================================

PART_III = Part(
    number=3,
    title="The Wedge",
    epigraph="Same stick, four ways up.",
    promise="The paradigm itself: how a split trunk becomes a structural "
            "member, and the four things it can do.",
    chapters=(
        Chapter(
            12, "Split Like a Cake",
            "Three passes, eight sectors, and why eight",
            "howto",
            (
                _p("opener", "Split Like a Cake", "The cut, introduced.",
                   words=300),
                _p("steps", "The three passes",
                   "The actual procedure at the log, in order.", words=700,
                   beats=(
                       "Pass one: halve the section through the pith.",
                       "Pass two and three: quarter each half.",
                       "Passes four to seven: pith to bark, eighths.",
                       "Why the halving pass goes first, every time.",
                   )),
                _p("spread", "Three cuts, eight sticks",
                   "The cut sequence drawn on a real section.", words=350,
                   figures=(_f("split-sequence",
                               "The order of the passes. Halve, quarter, "
                               "eighth.", DIAG, diagram="split_sequence"),)),
                _p("text", "One log, two, four, eight",
                   "The production hierarchy, which is what makes the "
                   "afternoon repetitive enough to be fast.", words=650,
                   beats=(
                       "1 log becomes 2 halves becomes 4 quarters becomes "
                       "{{tree.sectors}} members.",
                       "Every major cut doubles the number of pieces.",
                       "You are never deciding where the next stick comes "
                       "from -- the geometry has already decided.",
                       "That is what a guide rail, a cradle or a splitting "
                       "fixture can be built around.",
                   )),
                _p("text", "Why eight and not six or twelve",
                   "Forty-five degrees is the number that makes the seam key "
                   "work, and a sixth is too fat to handle alone.",
                   words=900),
                _p("table", "What other split counts give you",
                   "Six, eight, ten, twelve, compared on section and width.",
                   words=250,
                   figures=(_f("split-counts",
                               "Sector width and depth against split count.",
                               PLOT, plot="split_counts"),)),
            ),
            derives=("wedge_geometry.SECTORS_PER_LOG",
                     "wedge_geometry.sector_area_in2",
                     "wedge_geometry.sector_chord_in"),
        
            ref="split",
        ),
        Chapter(
            13, "Eighty-Seven Percent",
            "The recovery arithmetic, with the kerf paid for",
            "explain",
            (
                _p("opener", "Eighty-Seven Percent",
                   "The headline claim, and immediately the caveats.",
                   words=400),
                _p("text", "What a mill loses, and to what",
                   "Slabs, edgings, trim, drying degrade, and the kerf.",
                   words=950),
                _p("text", "What the wedge loses",
                   "Only the kerf, and here is the kerf, counted.",
                   words=800),
                _p("spread", "Both conversions, same log",
                   "The round section packed with 2x4s beside the same "
                   "section split into eighths.", words=400,
                   figures=(_f("recovery-compare",
                               "The same log, converted twice. "
                               "{{tree.recovery_pct}} percent against "
                               "{{tree.sawn_recovery_pct}}.", DIAG,
                               diagram="recovery_compare"),)),
                _p("table", "Section by section",
                   "The whole trunk, one row per section, both ways.",
                   words=250,
                   figures=(_f("section-rows",
                               "Every bucked section, both conversions.",
                               PLOT, plot="section_rows"),)),
                _p("errata", "Where 88 became 87",
                   "The project brief said 88 percent for a bigger tree. "
                   "This book's tree gives {{tree.recovery_pct}}. Both are "
                   "printed and the difference explained.", words=500),
            ),
            derives=("book_math.BOOK_TREE.recovery",
                     "wedge_geometry.tree_yield",
                     "wedge_geometry.section_rows"),
            corrects="The 88% recovery figure in the project brief, which "
                     "was computed for a 15-inch butt rather than this "
                     "book's 12-inch tree.",
        
            ref="recovery",
        ),
        Chapter(
            14, "Four Ways Up",
            "One stick, four orientations, four different buildings",
            "explain",
            (
                _p("opener", "Four Ways Up",
                   "The orientation idea, which is the most original thing "
                   "in the method.", words=400),
                _p("text", "Rotating about its own axis",
                   "The wedge is not symmetric, so which way its point aims "
                   "changes the frame.", words=850),
                _p("plate", "All four, side by side",
                   "Full page: the same seam in all four orientations.",
                   figures=(_f("orientations-four",
                               "The same pair of sticks, four ways up.",
                               DIAG, full_page=True,
                               diagram="orientation_quad"),)),
                _p("text", "Point dome in",
                   "The default, and why: flat sawn faces where the key "
                   "wants them, bark out at the weather.", words=600,
                   beats=(
                       "Both points at the centre, curved bark at the sky.",
                       "The sawn faces land where the seam key wants them.",
                       "And the stick tells you which way it goes: bark is "
                       "out, pith is in. No mark, no label, no confusion at "
                       "the top of a ladder.",
                       "The curved face is not waste. It is depth, weather "
                       "surface, and an orientation cue at once.",
                   )),
                _p("text", "Point panel in",
                   "The two sticks either side of a seam aim apart.",
                   words=500),
                _p("text", "Point dome out",
                   "Bark inward, a ridged outside surface, and which face "
                   "receives the next stick.", words=500),
                _p("text", "Point panel out",
                   "The bark faces the middle of the panel and the joint "
                   "bears on a round surface.", words=550),
                _p("table", "Choosing one",
                   "What each orientation buys and costs.", words=300,
                   figures=(_f("orientation-table",
                               "Read straight from the simulator's own "
                               "seam readings.", PLOT,
                               plot="orientation_table"),)),
            ),
            derives=("raw_wedge_bridge.orientations",
                     "raw_wedge_bridge.seam_pair_reading"),
        
            ref="orientations",
        ),
        Chapter(
            15, "The Pinwheel",
            "Three sticks, one triangle, and not one mitre",
            "explain",
            (
                _p("opener", "The Pinwheel",
                   "The joint that makes the whole thing buildable alone.",
                   words=400),
                _p("text", "Why mitres were the enemy",
                   "A mitre is a compound angle cut on both ends of every "
                   "stick. Forty panels of that is not a fortnight.",
                   words=800),
                _p("text", "Each end lands on a side, not a point",
                   "The pinwheel, explained in the way that finally makes "
                   "it obvious.", words=900),
                _p("spread", "One panel, taken apart",
                   "Exploded pinwheel with the inset and the bearing shown.",
                   words=400,
                   figures=(_f("pinwheel-exploded",
                               "Three members, three end-to-side joints, no "
                               "mitre anywhere.", DIAG,
                               diagram="pinwheel_exploded"),)),
                _p("text", "What the inset costs",
                   "The honest price: the panel is slightly smaller than the "
                   "triangle it sits in, and every member length accounts "
                   "for it.", words=700),
                _p("errata", "The mitre claim, corrected",
                   "An earlier film in this project said no cut in the dome "
                   "is a mitre. The butt cut is a compound angle. It is "
                   "still made once, on one end, off the jig -- but it is "
                   "not nothing, and the film's own correction chapter is "
                   "the model for this one.", words=550),
            ),
            derives=("wedge_geometry.pinwheel_panels",
                     "wedge_geometry.member_classes"),
            corrects="The 'no mitres anywhere' claim, already corrected on "
                     "camera in lesson_wedge_why.",
        
            ref="pinwheel",
        ),
        Chapter(
            16, "The Seam and Its Key",
            "Where two panels meet, and the angle nobody wants to hear about",
            "explain",
            (
                _p("opener", "The Seam and Its Key",
                   "The least glamorous chapter, and the one that decides "
                   "whether the dome closes.", words=400),
                _p("text", "The fold angle is not constant",
                   "Say the unwelcome thing early: seams differ, and the "
                   "range is this.", words=800),
                _p("text", "Raw trapezoid, or shaved flat",
                   "The two honest answers, with what each costs.",
                   words=900),
                _p("spread", "One seam, both ways",
                   "The tapered key beside the parallel one.", words=400,
                   figures=(_f("seam-both-ways",
                               "Leave the split faces alone and taper the "
                               "key, or plane the faces and use one key "
                               "everywhere.", DIAG, diagram="seam_modes"),)),
                _p("table", "Every seam in the dome",
                   "Fold angles, sorted, with the extremes named.",
                   words=300,
                   figures=(_f("seam-schedule",
                               "All {{frame.seams}} seams and their fold "
                               "angles.", PLOT, plot="seam_schedule"),)),
                _p("text", "Hose, key or nothing",
                   "The third option, and when a compressible seam beats a "
                   "rigid one.", words=650),
            ),
            derives=("wedge_geometry.gasket_plan",
                     "raw_wedge_bridge.model"),
        
            ref="seams",
        ),
        Chapter(
            17, "Let the Connector Hold the Angle",
            "Keep the wood, machine the small part",
            "explain",
            (
                _p("opener", "Let the Connector Hold the Angle",
                   "State the division of labour that makes rough timber "
                   "buildable to a tolerance.", words=450),
                _p("text", "Three jobs, three different things doing them",
                   "The principle, plainly: the tree supplies bulk, the jig "
                   "supplies repeatability, the connector supplies "
                   "precision.", words=900,
                   beats=(
                       "Precision is expensive per cubic inch of material.",
                       "A member is large; a key is small.",
                       "So put the accuracy in the small part.",
                       "The tree supplies the structural mass.",
                       "The jig supplies the repeatability.",
                       "The connector supplies the precision.",
                   )),
                _p("spread", "Where the precision lives",
                   "Show the same joint with the accuracy in the member, "
                   "then with it in the key.", words=400,
                   figures=(_f("precision-location",
                               "Machine every member to fit, or machine one "
                               "key profile and repeat it.", DIAG,
                               diagram="precision_location"),)),
                _p("text", "The wedge starts close to useful",
                   "The sector face already sits at half the sector angle, "
                   "which is not far from what the seam wants.", words=850,
                   beats=(
                       "A split face sits {{seam.half_sector_deg}} degrees "
                       "off the member's centreline.",
                       "The seams fold by {{seam.fold_a_deg}} and "
                       "{{seam.fold_b_deg}} degrees.",
                       "So the raw face is already within a few degrees of "
                       "what a flat key wants.",
                       "It does not match. It starts close, which is "
                       "different and more useful than starting square.",
                   )),
                _p("worked", "What planing the faces actually costs",
                   "Compute the depth of cut for each seam class, over a "
                   "narrow mating land.", words=700,
                   figures=(_f("shaving-cost",
                               "The whole cost of the shaved-flat option: "
                               "under half an inch, on a "
                               "{{member.depth_in}}-inch-deep member.",
                               PLOT, plot="shaving_cost"),)),
                _p("text", "Or do not plane at all",
                   "The compliant option: a key that takes up the "
                   "difference by deforming.", words=800,
                   beats=(
                       "A rubber or foam spline fills a range, not a value.",
                       "It seals, isolates and takes tolerance at once.",
                       "It cannot carry the load a timber key can.",
                       "Which you choose depends on whether the seam is "
                       "structural or only weathertight.",
                   )),
                _p("text", "Why this is a manufacturing idea, not a dodge",
                   "Defend it: this is how repeatable production works "
                   "everywhere, not a way of avoiding accuracy.",
                   words=650),
            ),
            derives=("book_math.shaving_plan",
                     "book_math.panel_seam_count"),
            ref="connector",
        ),
        Chapter(
            18, "Why Every Panel Keeps Its Own Edge",
            "One hundred and twenty members for sixty-five edges, and what "
            "the difference buys",
            "explain",
            (
                _p("opener", "Every Panel Keeps Its Own Edge",
                   "Introduce the panelised frame and the wood it costs.",
                   words=400),
                _p("text", "The arithmetic that does not look right",
                   "Confront the number: forty triangles, three members "
                   "each, but only sixty-five edges.", words=800,
                   beats=(
                       "{{frame.panels}} panels x "
                       "{{frame.members_per_panel}} = {{frame.members}} "
                       "members.",
                       "But the shell has only {{frame.edges}} edges.",
                       "{{edges.duplicated}} members exist twice over.",
                       "That is {{edges.duplication_ratio}} times the "
                       "timber a shared-strut frame would use.",
                   )),
                _p("spread", "One seam, two members",
                   "Draw the seam sandwich: member, key, member.",
                   words=400,
                   figures=(_f("seam-sandwich",
                               "An interior seam holds two members and a "
                               "key, not one shared strut.", DIAG,
                               diagram="seam_sandwich"),)),
                _p("text", "What the extra wood buys",
                   "The case for spending it, item by item.", words=950,
                   beats=(
                       "A panel that owns its edges can be built flat.",
                       "It can be checked, skinned and sealed on the "
                       "ground.",
                       "It can be lifted as one finished thing.",
                       "It can be taken out later without disturbing its "
                       "neighbours.",
                       "The seam gains room for a gasket.",
                       "And the frame gains redundancy at every edge.",
                   )),
                _p("text", "The check that has to close",
                   "Count the members two ways and show them agreeing.",
                   words=600,
                   beats=(
                       "Panel by panel: {{frame.panels}} x "
                       "{{frame.members_per_panel}}.",
                       "Edge by edge: {{frame.seams}} shared x 2, plus "
                       "{{frame.rim_edges}} rim.",
                       "Both give {{frame.members}}.",
                       "If they ever disagree, the frame is not the frame "
                       "you think it is.",
                   )),
                _p("text", "When to share a strut instead",
                   "Honest note on the alternative and who it suits.",
                   words=650),
            ),
            derives=("book_math.edge_accounting",),
            ref="own_edge",
        ),
        Chapter(
            19, "Bends, Knots and Small Units",
            "Why six-foot pieces forgive what sixteen-foot boards do not",
            "explain",
            (
                _p("opener", "Small Units",
                   "The resilience argument, which is the quiet advantage.",
                   words=350),
                _p("text", "A bend costs you a section, not a tree",
                   "Cut either side of the bend and keep going.", words=800),
                _p("text", "Knots, and where they are allowed",
                   "A knot in the middle of a compression member is not the "
                   "same as a knot at a bearing face.", words=750),
                _p("spread", "One bent trunk, salvaged",
                   "The same crooked tree drawn as a mill would reject it "
                   "and as this method buckes it.", words=400,
                   figures=(_f("bent-trunk",
                               "A bend a mill would refuse, and the sections "
                               "either side of it.", DIAG,
                               diagram="bent_trunk"),)),
                _p("text", "Grade your own stock",
                   "A practical sorting procedure for a pile of wedges.",
                   words=700),
                _p("text", "Trees nobody else wants",
                   "The economic consequence of tolerating variation: what "
                   "counts as building material widens considerably.",
                   words=800,
                   beats=(
                       "Storm debris, clearing waste, low-value sawlogs.",
                       "A tree too bent or too short for a mill is "
                       "{{tree.sectors}} good sticks a section.",
                       "It is often already on the site.",
                       "Which removes the haul, the mill fee and the "
                       "markup, and replaces them with fuel and bar oil.",
                   )),
                _p("text", "And the journey it does not take",
                   "The supply chain, counted as handling rather than as "
                   "operations.", words=650,
                   beats=(
                       "Forest, logger, mill, kiln, distributor, retailer, "
                       "site.",
                       "Against: tree, cutting station, drying stack, jig.",
                       "Every removed stage is fuel, time, and a margin.",
                       "This is the same argument as Chapter "
                       "{{ch.middlemen}}, made about distance rather than "
                       "about wood.",
                   )),
            ),
            derives=("book_math.BOOK_TREE",),
        
            ref="small_units",
        ),
    ),
)


# ======================================================================
# PART IV -- THE TWO CALCULATIONS
# ======================================================================

PART_IV = Part(
    number=4,
    title="The Two Calculations",
    epigraph="Either you know the dome you want, or you know the tree you "
             "have. Never both.",
    promise="The manual's core. Two methods, run in opposite directions, "
            "and the proof that they close on the same dome.",
    chapters=(
        Chapter(
            20, "Which Way Round Are You Working?",
            "Choose your method before you touch anything",
            "howto",
            (
                _p("opener", "Which Way Round",
                   "The decision that determines every later number.",
                   words=350),
                _p("text", "Design first, or tree first",
                   "State the two, and the honest test for which one you are "
                   "actually in.", words=800),
                _p("spread", "The decision, drawn",
                   "A flow chart from what you know to which chapter to "
                   "read.", words=300,
                   figures=(_f("method-decision",
                               "Start from what you actually have.", DIAG,
                               diagram="method_decision"),)),
                _p("text", "The one thing both methods share",
                   "Both solve the same relationship between radius and "
                   "member length. Everything else is which end you hold.",
                   words=650),
            ),
            derives=("wedge_geometry.longest_member_in",
                     "wedge_geometry.radius_for_member_length"),
        
            ref="which_way",
        ),
        Chapter(
            21, "Method A: From the Dome You Want",
            "Radius in, cut list out",
            "howto",
            (
                _p("opener", "Method A", "The design-first path.",
                   words=300),
                _p("steps", "The procedure",
                   "Numbered, followable, with a worked number at every "
                   "step.", words=900,
                   beats=(
                       "Decide the floor area you want to stand on.",
                       "Convert floor to radius.",
                       "Measure your stock's sector width.",
                       "Read the four member classes off the layout.",
                       "Round the bucking length up to the next foot.",
                       "Count sections, then trunk feet, then trees.",
                   )),
                _p("worked", "Three hundred square feet",
                   "Carry one example all the way, showing every "
                   "intermediate.", words=850,
                   figures=(_f("method-a-worked",
                               "Three hundred square feet, from floor to "
                               "felling list.", PLOT,
                               plot="method_a_worked"),)),
                _p("text", "Where this method surprises people",
                   "Member length does not scale with the dome, because the "
                   "pinwheel inset does not.", words=700),
                _p("table", "Design-first lookup",
                   "A table of floor areas against radius, longest member "
                   "and trees, so the reader can skip the arithmetic.",
                   words=250,
                   figures=(_f("design-lookup",
                               "Floor area to trees, at this book's stock "
                               "section.", PLOT, plot="design_lookup"),)),
            ),
            derives=("book_math.design_first",
                     "book_math.design_first_for_floor"),
        
            ref="method_a",
        ),
        Chapter(
            22, "Method B: From the Tree You Have",
            "Section length in, dome out",
            "howto",
            (
                _p("opener", "Method B",
                   "The tree-first path, and the one the title refers to.",
                   words=300),
                _p("steps", "The procedure",
                   "Numbered, from a standing tree to a dome diameter.",
                   words=900,
                   beats=(
                       "Measure butt, top and usable straight length.",
                       "Pick a bucking length you can carry alone.",
                       "Count sections; multiply by eight.",
                       "Sector width comes from the mid diameter.",
                       "Solve the radius that makes the longest member fit.",
                       "Check the strut count against 120.",
                   )),
                _p("worked", "Two trees, one hundred and twenty struts",
                   "The book's own build, carried through completely.",
                   words=900,
                   figures=(_f("method-b-worked",
                               "{{tree.sections}} sections x "
                               "{{tree.sectors}} = {{tree.struts_per_tree}} "
                               "struts per tree. Two trees, "
                               "{{dome.struts_available}} struts, "
                               "{{frame.members}} needed.",
                               PLOT, plot="method_b_worked"),)),
                _p("text", "You do not get to choose the diameter",
                   "The uncomfortable consequence, stated plainly.",
                   words=650),
                _p("table", "Tree-first lookup",
                   "Section length against dome diameter and floor.",
                   words=250,
                   figures=(_f("tree-lookup",
                               "Bucking length to dome size.", PLOT,
                               plot="tree_lookup"),)),
            ),
            derives=("book_math.tree_first", "book_math.BOOK_TREE"),
        
            ref="method_b",
        ),
        Chapter(
            23, "The Round Trip",
            "Proving the two methods are one calculation",
            "explain",
            (
                _p("opener", "The Round Trip",
                   "Why this chapter exists: so neither method is a rule of "
                   "thumb.", words=350),
                _p("text", "Run it forwards, then backwards",
                   "Design a dome, read its longest member, size a dome to "
                   "that member, and compare.", words=700),
                _p("worked", "The residual",
                   "Print the actual error, which is "
                   "{{roundtrip.residual_in}} inches.", words=500,
                   figures=(_f("round-trip",
                               "Out and back. The gap is smaller than any "
                               "saw can cut.", PLOT, plot="round_trip"),)),
                _p("text", "What would break it",
                   "Change the gasket, the sector count or the stock width "
                   "between the two directions and it will not close.",
                   words=600),
            ),
            derives=("book_math.round_trip",),
        
            ref="round_trip",
        ),
        Chapter(
            24, "The Worked Build",
            "Every number for this book's dome, in one place",
            "reference",
            (
                _p("opener", "The Worked Build",
                   "One chapter a builder can work from without reading "
                   "anything else.", words=300),
                _p("table", "The tree",
                   "Taper, sections, struts, recovery.", words=200,
                   figures=(_f("worked-tree", "This book's tree.", PLOT,
                               plot="worked_tree"),)),
                _p("table", "The dome",
                   "Radius, diameter, height, floor.", words=200,
                   figures=(_f("worked-dome", "The dome that results.",
                               PLOT, plot="worked_dome"),)),
                _p("table", "The cut list",
                   "All {{frame.members}} members by class and length.",
                   words=200,
                   figures=(_f("worked-cutlist",
                               "The full cut list.", PLOT,
                               plot="worked_cutlist"),)),
                _p("table", "The seam schedule",
                   "Every seam and its key.", words=200,
                   figures=(_f("worked-seams", "The seam schedule.", PLOT,
                               plot="worked_seams"),)),
                _p("plate", "The dome this describes",
                   "Full page render of exactly the dome the tables specify.",
                   figures=(_f("worked-render",
                               "{{dome.diameter_ft}} feet across, "
                               "{{dome.floor_sqft}} square feet of floor.",
                               DOME, full_page=True, view="three_quarter",
                               parts=("wood", "rigid")),),),
            ),
            derives=("book_math.book_math_report", "book_math.tree_first"),
        
            ref="worked_build",
        ),
        Chapter(
            25, "When the Numbers Say No",
            "Reading a result that means do not build this",
            "howto",
            (
                _p("opener", "When the Numbers Say No",
                   "The chapter that gives permission to stop.", words=350),
                _p("text", "Not enough struts",
                   "What to do when two trees is one hundred and twelve, not "
                   "one hundred and twenty.", words=700),
                _p("text", "Too big to lift alone",
                   "A six-foot green wedge is heavy. Say how heavy.",
                   words=650),
                _p("text", "Stock too small in section",
                   "When the sector is too slender to bear, and what the "
                   "options are.", words=700),
                _p("text", "Three ways out",
                   "Shorter bucking, a third tree, or a smaller dome, with "
                   "the arithmetic for each.", words=750),
            ),
            derives=("book_math.tree_first", "book_math.design_first"),
        
            ref="numbers_say_no",
        ),
    ),
)


# ======================================================================
# PART V -- THE FORTNIGHT
# ======================================================================

PART_V = Part(
    number=5,
    title="The Fortnight",
    epigraph="Fourteen days, one saw, and no help that could not be "
             "summoned by phone.",
    promise="The story and the manual running together: what happened on "
            "each day, and what you should do on yours.",
    chapters=(
        Chapter(
            26, "Day Zero: The Saw",
            "A hundred and ninety-nine dollars and a sixteen-inch bar",
            "story",
            (
                _p("opener", "Day Zero", "The tool, honestly assessed.",
                   words=350),
                _p("text", "The smallest saw on the shelf",
                   "What {{saw.displacement_cc}} cc and a "
                   "{{saw.bar_in}}-inch bar can and cannot do.", words=900),
                _p("sidebar", "What I would have bought instead",
                   "The honest counterfactual: a bigger saw, and why it "
                   "would not have changed the method.", words=400),
                _p("steps", "Setting it up",
                   "Chain, tension, ripping considerations, bar oil, and the "
                   "file.", words=800),
                _p("safety", "Chaps, helmet, and never alone",
                   "The second safety page, placed where the saw actually "
                   "starts.", words=500),
            ),
            derives=("book_math.DECLARED",),
        ),
        Chapter(
            27, "Days One and Two: Felling",
            "Putting two trees on the ground where you want them",
            "howto",
            (
                _p("opener", "Felling", "The most dangerous two days.",
                   words=300),
                _p("safety", "Read this before the notch",
                   "Escape route, hinge, barber chair, and widow-makers.",
                   words=600),
                _p("steps", "The notch and the back cut",
                   "The procedure, with the hinge dimension called out.",
                   words=900),
                _p("spread", "The hinge, drawn",
                   "What the hinge does and what happens when it is wrong.",
                   words=350,
                   figures=(_f("felling-hinge",
                               "The hinge steers the tree. Everything else "
                               "is timing.", DIAG, diagram="felling_hinge"),)),
                _p("text", "Limbing without pinching",
                   "Working a downed trunk, tension and compression sides.",
                   words=750),
                _p("text", "What actually happened",
                   "The story half: the second tree did not go where it was "
                   "supposed to.", words=700),
            ),
        ),
        Chapter(
            28, "Days Three and Four: Bucking",
            "Cutting the trunk into the only length that matters",
            "howto",
            (
                _p("opener", "Bucking", "One measurement, repeated eight "
                   "times.", words=300),
                _p("steps", "Marking and cutting to length",
                   "How to mark {{tree.section_length_ft}}-foot sections on a "
                   "tapered trunk without a tape drifting.", words=800),
                _p("text", "Where to start, and why not at the butt",
                   "Choosing the start point around bends and butt flare.",
                   words=700),
                _p("spread", "Eight sections from one trunk",
                   "The whole trunk laid out with its sections and the "
                   "offcut.", words=350,
                   figures=(_f("bucking-plan",
                               "{{tree.usable_length_ft}} feet into "
                               "{{tree.sections}} sections of "
                               "{{tree.section_length_ft}}. Offcut: "
                               "{{tree.offcut_ft}} feet.", DIAG,
                               diagram="bucking_plan"),)),
                _p("text", "Moving six-foot green sections alone",
                   "The unglamorous logistics that decide whether this is a "
                   "one-person job.", words=750),
            ),
            derives=("book_math.BOOK_TREE",),
        ),
        Chapter(
            29, "Days Five to Eight: Ripping",
            "One hundred and twenty struts, thirty to an afternoon",
            "howto",
            (
                _p("opener", "Ripping", "The bulk of the labour, in four "
                   "days.", words=350),
                _p("steps", "The three passes, at the log",
                   "The full procedure with the saw actually in hand.",
                   words=1000),
                _p("text", "Holding a round section still",
                   "The cradle, the wedges, and why the first pass is the "
                   "hard one.", words=800),
                _p("text", "Reading the pith",
                   "Aiming a rip at the centre of a section that is not "
                   "round.", words=700),
                _p("spread", "The cutting rhythm",
                   "What thirty struts in six hours actually looks like as a "
                   "sequence.", words=400,
                   figures=(_f("ripping-rhythm",
                               "{{work.struts_per_hour}} struts an hour, "
                               "sustained.", PLOT, plot="ripping_rhythm"),)),
                _p("text", "Chain, file, and the cost of a dull cut",
                   "Sharpening cadence and what a dull chain does to the "
                   "kerf and to you.", words=700),
                _p("sidebar", "What this is worth an hour",
                   "The money, both ways, with the caveat attached.",
                   words=450),
            ),
            derives=("book_math.fortnight", "book_math.BOOK_TREE"),
        ),
        Chapter(
            30, "Day Nine: The Jig",
            "One flat bench that makes forty panels the same",
            "howto",
            (
                _p("opener", "The Jig", "The day that pays for itself.",
                   words=350),
                _p("text", "Why a jig and not a tape",
                   "Repeatability beats accuracy when there are forty of "
                   "something.", words=750),
                _p("steps", "Building it",
                   "The bench, the triangle, the rails, the fences, the cut "
                   "planes.", words=1000),
                _p("plate", "The jig, complete",
                   "Full page of the finished fixture.",
                   figures=(_f("jig-complete",
                               "The fixture with a panel on it, at the moment "
                               "the long heads are flush-cut.", JIG,
                               full_page=True, stage=10),),),
            ),
            derives=("raw_wedge_bridge.jig_stages",),
        
            ref="the_jig",
        ),
        Chapter(
            31, "Days Ten to Twelve: Forty Panels",
            "The same twelve motions, forty times",
            "howto",
            (
                _p("opener", "Forty Panels",
                   "The production days, and what makes them go wrong.",
                   words=350),
                _p("steps", "One panel, start to finish",
                   "The twelve jig steps as a followable procedure.",
                   words=1100),
                _p("text", "Sorting the pile",
                   "Which stick goes where, and the marking scheme that "
                   "survives being left in the rain.", words=700),
                _p("text", "The fourth panel is the first good one",
                   "Honest note on the learning curve.", words=550),
                _p("table", "Panel variants",
                   "Which panels are genuinely different, and how few there "
                   "are.", words=250,
                   figures=(_f("panel-variants",
                               "How many distinct panels the dome actually "
                               "contains.", PLOT, plot="panel_variants"),)),
            ),
            derives=("raw_wedge_bridge.jig_stages", "raw_wedge_bridge.model"),
        ),
        Chapter(
            32, "Days Thirteen and Fourteen: Raising",
            "Forty panels become one building",
            "howto",
            (
                _p("opener", "Raising", "The two days that look like the "
                   "photographs.", words=350),
                _p("steps", "Bottom ring first",
                   "The assembly order that lets one person do it.",
                   words=1000),
                _p("text", "Propping, and what holds it up before it is "
                   "closed", "The temporary structure nobody photographs.",
                   words=750),
                _p("text", "Closing the top",
                   "The last panel, and why it is the hardest.", words=650),
                _p("plate", "Standing",
                   "Full page. The frame complete.",
                   figures=(_f("standing-frame",
                               "Day fourteen. {{frame.members}} members, "
                               "two trees.", DOME, full_page=True,
                               view="hero", parts=("wood", "rigid")),),),
                _p("text", "What was not done",
                   "Honest inventory of what a standing frame is not: not a "
                   "shell, not a home, not finished.", words=600),
            ),
            derives=("book_math.frame_counts",),
        ),
    ),
)


# ======================================================================
# PART VI -- THE JIG AND THE CUTS
# ======================================================================

PART_VI = Part(
    number=6,
    title="The Jig and the Cuts",
    epigraph="Any error in stock length or butt angle leaves as offcut "
             "instead of building up around the triangle.",
    promise="Reference for the bench. Come back to this part while you are "
            "working, not while you are reading.",
    chapters=(
        Chapter(
            33, "One Bench, Forty Panels",
            "What the jig is and what each part of it does",
            "reference",
            (
                _p("opener", "One Bench", "The fixture, part by part.",
                   words=300),
                _p("table", "The twelve stages",
                   "Every stage of the jig, named, straight from the "
                   "simulator.", words=300,
                   figures=(_f("jig-stages",
                               "The twelve stages, in order.", PLOT,
                               plot="jig_stages"),)),
                _p("spread", "The jig, labelled",
                   "Every component called out.", words=400,
                   figures=(_f("jig-labelled",
                               "Bench, triangle, rails, fences, cut planes "
                               "-- the fixture before any wood is on it.",
                               JIG, stage=4, view="three_quarter"),)),
                _p("text", "Setting it out on a real floor",
                   "How to lay the triangle out full size with a string and "
                   "a pencil.", words=800),
                _p("text", "Locate from the sawn faces, never the bark",
                   "The datum question, which is what makes a jig work on "
                   "natural timber at all.", words=850,
                   beats=(
                       "Bark is irregular, and no two sticks share it.",
                       "The two sawn faces are flat, and every stick has "
                       "them at the same angle.",
                       "So the fixture locates on those, and only those.",
                       "The bark floats in an oversized clearance and is "
                       "never touched.",
                       "Precision where precision matters; tolerance where "
                       "the tree varies.",
                   )),
            ),
            derives=("raw_wedge_bridge.jig_stages",),
        
            ref="jig_reference",
        ),
        Chapter(
            34, "The Butt Cut",
            "The one compound angle, made before anything is assembled",
            "reference",
            (
                _p("opener", "The Butt Cut", "Name it honestly: this is a "
                   "compound cut.", words=350),
                _p("text", "The angle its neighbour presents",
                   "Where the butt angle comes from, geometrically.",
                   words=800),
                _p("table", "Butt cut setups",
                   "Every distinct setup, from the simulator's own setup "
                   "list.", words=300,
                   figures=(_f("butt-setups",
                               "How few distinct setups the whole dome "
                               "needs.", PLOT, plot="butt_setups"),)),
                _p("steps", "Making it",
                   "At the saw, with the allowance still attached.",
                   words=750),
            ),
            derives=("raw_wedge_bridge.model",),
        
            ref="butt_cut",
        ),
        Chapter(
            35, "The Head Overfit",
            "Deliberately cutting it too long",
            "reference",
            (
                _p("opener", "The Head Overfit",
                   "The idea that makes the whole method tolerant.",
                   words=400),
                _p("text", "Where error goes",
                   "The core argument: overshoot, pull tight, then cut in "
                   "place.", words=850),
                _p("sidebar", "Locate first, cut second",
                   "The maxim, and why it is the opposite of how most people "
                   "are taught to work with a tape.", words=450,
                   beats=(
                       "Dimensional lumber teaches: measure, then cut, then "
                       "fit.",
                       "Rough timber will not survive that order -- the "
                       "stick is not the shape the tape assumed.",
                       "So put the member in the jig first, long.",
                       "The fixture, not the tape, establishes the cut.",
                       "Locate first. Cut second.",
                   )),
                _p("spread", "Long, then flush",
                   "The same panel before and after the flush cut.",
                   words=350,
                   figures=(_f("head-overfit",
                               "{{jig.head_overfit_in}} inches of deliberate "
                               "overshoot, sawn off against the fence.",
                               JIG, stage=9),)),
                _p("text", "How much to leave",
                   "Sizing the overfit against your own stock variation.",
                   words=700),
                _p("table", "Offcut per dome",
                   "What the tolerance costs in wood.", words=250,
                   figures=(_f("offcut-total",
                               "The price of the tolerance, in board feet.",
                               PLOT, plot="offcut_total"),)),
            ),
            derives=("book_math.DECLARED", "raw_wedge_bridge.model"),
        
            ref="head_overfit",
        ),
        Chapter(
            36, "Flush-Cutting in Place",
            "The cut that makes the panel true",
            "reference",
            (
                _p("opener", "Flush-Cutting", "The final operation on the "
                   "jig.", words=300),
                _p("steps", "Against the fence",
                   "The procedure, with the saw held the way it has to be "
                   "held.", words=750),
                _p("text", "Why this cannot be done first",
                   "The order is not arbitrary and this says why.",
                   words=600),
            ),
            derives=("raw_wedge_bridge.jig_stages",),
        ),
        Chapter(
            37, "Panel Drawings",
            "One flat drawing per distinct panel, full size",
            "reference",
            (
                _p("opener", "Panel Drawings",
                   "How to use the drawings, and how to print them full "
                   "size.", words=400),
                _p("plate", "Panel drawing, type one",
                   "A full-page flat drawing, exported from the simulator.",
                   figures=(_f("panel-1",
                               "Panel type one, flat, full size.", PANEL,
                               full_page=True, panel_index=0),),),
                _p("plate", "Panel drawing, type two",
                   "The second distinct panel.",
                   figures=(_f("panel-2",
                               "Panel type two, flat, full size.", PANEL,
                               full_page=True, panel_index=1),),),
                _p("text", "Reading a panel drawing",
                   "What every line on the drawing is.", words=650),
            ),
            derives=("raw_wedge_bridge.model",),
        
            ref="panel_drawings",
        ),
        Chapter(
            38, "Where Error Goes",
            "A tolerance budget for a building made of split logs",
            "explain",
            (
                _p("opener", "Where Error Goes",
                   "The chapter that explains why the method survives "
                   "imprecision.", words=400),
                _p("text", "Four places error can land",
                   "Stock length, butt angle, seam gap, and the ring.",
                   words=900),
                _p("text", "Three of them are absorbed",
                   "Which errors the method eats and which it accumulates.",
                   words=800),
                _p("spread", "The tolerance budget",
                   "Where a sixteenth of an inch ends up.", words=400,
                   figures=(_f("tolerance-budget",
                               "Error, and where the method sends it.",
                               DIAG, diagram="tolerance_budget"),)),
                _p("text", "The one that accumulates",
                   "Name it: the bottom ring. Say how to check it as you "
                   "go.", words=700),
            ),
        
            ref="where_error_goes",
        ),
    ),
)


# ======================================================================
# PART VII -- FROM FRAME TO HOME
# ======================================================================

PART_VII = Part(
    number=7,
    title="From Frame to Home",
    epigraph="A standing frame is not a house. It is the fortnight's "
             "result, and the beginning of the year's work.",
    promise="What happens after day fourteen: shell, openings, weather, and "
            "living in a round room.",
    chapters=(
        Chapter(
            39, "The Footing and the Ring",
            "What the dome stands on",
            "howto",
            (
                _p("opener", "The Footing", "The part that is under "
                   "everything.", words=300),
                _p("text", "Ten points, or one ring",
                   "The two approaches, and why the ring is usually right "
                   "here.", words=850),
                _p("steps", "Setting out a circle accurately",
                   "String, stake, and the check that catches an out-of-round "
                   "ring before it matters.", words=800),
                _p("text", "Anchoring against uplift",
                   "A dome is a wing. Say so.", words=700),
                _p("safety", "This is where to ask somebody",
                   "Footings are load and soil. Point at the professional.",
                   words=350),
            ),
        ),
        Chapter(
            40, "Closing the Shell",
            "Forty triangles of something over forty triangles of nothing",
            "howto",
            (
                _p("opener", "Closing the Shell",
                   "The options, ranked by how much they cost and how well "
                   "they work.", words=400),
                _p("text", "Sheathing a triangle",
                   "Cutting sheet goods to a triangle without wasting half "
                   "of every sheet.", words=850),
                _p("text", "Nesting the cuts",
                   "The layout that gets two panels from one sheet.",
                   words=700,
                   ),
                _p("table", "Sheet count",
                   "How many sheets the shell takes, computed.", words=250,
                   figures=(_f("sheet-count",
                               "Shell area and sheets, from the solved "
                               "geometry.", PLOT, plot="sheet_count"),)),
                _p("text", "The alternatives",
                   "Fabric, shingle, living roof, and what each demands of "
                   "the frame.", words=800),
            ),
            derives=("dome_costing.shell_sqft",),
        ),
        Chapter(
            41, "Doors, Windows and the Rim",
            "Cutting holes in something that works by being closed",
            "howto",
            (
                _p("opener", "Doors and Windows",
                   "The chapter where a dome fights back.", words=400),
                _p("text", "A door at the rim",
                   "The easy case, and how to frame it.", words=800),
                _p("text", "A window in a panel",
                   "The harder case: keeping the triangle triangulated.",
                   words=850),
                _p("spread", "Three openings that work",
                   "Rim door, panel window, and the risers option.",
                   words=400,
                   figures=(_f("openings-three",
                               "Three ways to open a dome without "
                               "un-triangulating it.", DIAG,
                               diagram="openings"),)),
                _p("text", "Risers: cheating height at the rim",
                   "The vertical wall under the dome, and what it buys.",
                   words=700),
            ),
        
            ref="openings",
        ),
        Chapter(
            42, "Weather and Water",
            "Where it leaks, and where the water goes",
            "howto",
            (
                _p("opener", "Weather and Water",
                   "The honest chapter about domes and rain.", words=400),
                _p("text", "Every seam is a potential leak",
                   "{{frame.seams}} of them. Say the number.", words=750),
                _p("text", "Shedding, not sealing",
                   "The principle that actually works on a compound "
                   "surface.", words=800),
                _p("text", "Harvesting it instead",
                   "A dome is a very good rain collector, and this is the "
                   "one place the shape helps.", words=700),
                _p("text", "Condensation and the inside face",
                   "The problem people discover in month three.",
                   words=650),
            ),
            derives=("book_math.panel_seam_count",),
        ),
        Chapter(
            43, "Inside a Round Room",
            "Living with curves",
            "explain",
            (
                _p("opener", "Inside a Round Room",
                   "What it is actually like.", words=400),
                _p("text", "Where the usable floor really is",
                   "The honest number: floor area against floor you can "
                   "stand up on.", words=800,
                   ),
                _p("spread", "Standing height, mapped",
                   "A plan of the floor coloured by headroom.", words=350,
                   figures=(_f("headroom-map",
                               "{{dome.floor_sqft}} square feet of floor. "
                               "Rather less of it lets you stand up.",
                               PLOT, plot="headroom_map"),)),
                _p("text", "Furniture, storage and the wall that curves "
                   "away", "Practical solutions, including the ones that "
                   "are just compromises.", words=800),
                _p("text", "Acoustics, and the whispering problem",
                   "A hemisphere focuses sound at the centre. Deal with "
                   "it.", words=600),
            ),
            derives=("book_math.tree_first",),
        
            ref="round_room",
        ),
        Chapter(
            44, "Heat, Power and the Small Systems",
            "Making a shell into somewhere you can be in February",
            "howto",
            (
                _p("opener", "The Small Systems",
                   "What has to happen before it is a home.", words=350),
                _p("text", "Insulating between wedges",
                   "The cavity a wedge frame gives you, and what fits in "
                   "it.", words=850),
                _p("text", "Running services in a frame with no studs",
                   "Where the wires and pipes go.", words=750),
                _p("text", "Heating a round volume",
                   "Why it is easier than a rectangle, and the one way it "
                   "is not.", words=700),
                _p("text", "Off grid, or not",
                   "Honest treatment of the choice, without romance.",
                   words=700),
            ),
        ),
    ),
)


# ======================================================================
# PART VIII -- WHAT IT ACTUALLY COST
# ======================================================================

PART_VIII = Part(
    number=8,
    title="What It Actually Cost",
    epigraph="Several pages in this book exist specifically to state the "
             "number that does not help the argument.",
    promise="The accounting. Money, hours, breakage, and the claims this "
            "project got wrong.",
    chapters=(
        Chapter(
            45, "The Money, Both Ways",
            "What was spent, and what was avoided",
            "reference",
            (
                _p("opener", "The Money", "How this chapter counts, before "
                   "it counts.", words=400),
                _p("table", "What was actually spent",
                   "Saw, fuel, chain, fasteners, gaskets, sheeting.",
                   words=300,
                   figures=(_f("money-spent",
                               "Cash out, itemised.", PLOT,
                               plot="money_spent"),)),
                _p("text", "Substitution value is not income",
                   "The most important paragraph in the chapter.",
                   words=700),
                _p("table", "The strut, valued three ways",
                   "Nominal 2x4, dressed 2x4, and board feet.", words=300,
                   figures=(_f("strut-value",
                               "One strut, valued three ways. The numbers "
                               "disagree and the reasons are printed.",
                               PLOT, plot="strut_value"),)),
                _p("errata", "The fifty dollars an hour claim",
                   "The brief said fifty. Computed properly it is "
                   "{{work.rate_nominal_usd}} nominal, "
                   "{{work.rate_dressed_usd}} dressed. Name the error, then "
                   "show the arithmetic that produces the smaller number.",
                   words=650),
            ),
            derives=("book_math.fortnight", "book_math.BOOK_TREE"),
            corrects="The $50/hour figure in the project brief, which "
                     "doubled a volume ratio for safety rather than "
                     "computing the section.",
        
            ref="money",
        ),
        Chapter(
            46, "The Hours",
            "Where fourteen days actually went",
            "reference",
            (
                _p("opener", "The Hours", "Time, honestly logged.",
                   words=300),
                _p("table", "The fortnight, hour by hour",
                   "Each day, what was done, how long it took.", words=350,
                   figures=(_f("hours-log",
                               "Fourteen days, and where they went.", PLOT,
                               plot="hours_log"),)),
                _p("text", "What took longest and why",
                   "The surprises: not the ripping.", words=750),
                _p("text", "What a second build would take",
                   "The learning-curve estimate, marked clearly as an "
                   "estimate.", words=600),
            ),
            derives=("book_math.fortnight",),
        ),
        Chapter(
            47, "What Broke",
            "The failures, listed",
            "story",
            (
                _p("opener", "What Broke", "The chapter every build book "
                   "should have and most do not.", words=350),
                _p("text", "The stick that split along the pith",
                   "What happened, why, and how to spot it first.",
                   words=700),
                _p("text", "The seam that would not close",
                   "The fold-angle problem, encountered in the flesh.",
                   words=750),
                _p("text", "The panel I built backwards",
                   "Handedness, and the marking scheme that came from this.",
                   words=650),
                _p("text", "What I would call a near miss",
                   "The safety incident, reported rather than tidied away.",
                   words=600),
            ),
        
            ref="what_broke",
        ),
        Chapter(
            48, "Corrections",
            "Everything this project has published and had to fix",
            "reference",
            (
                _p("opener", "Corrections",
                   "State the policy: a correction is a chapter, never a "
                   "silent re-cut.", words=450),
                _p("errata", "The mitre claim",
                   "Named in full, with the film that corrected it.",
                   words=500),
                _p("errata", "The recovery percentage",
                   "88 for the brief's tree, {{tree.recovery_pct}} for this "
                   "one. Neither is wrong; they are different trees.",
                   words=450),
                _p("errata", "The hourly rate",
                   "Cross-referenced to chapter 42.", words=350),
                _p("errata", "Seams against edges",
                   "{{frame.edges}} edges, {{frame.seams}} seams. An early "
                   "draft of this book used the wrong one.", words=400),
                _p("text", "How to report one",
                   "Invite the reader to find the next error, and say where "
                   "to send it.", words=400),
            ),
            derives=("book_math.frame_counts", "book_math.panel_seam_count",
                     "book_math.BOOK_TREE.recovery"),
            corrects="Every published claim this project has had to revise.",
        
            ref="corrections",
        ),
    ),
)


# ======================================================================
# PART IX -- TAKE IT FURTHER
# ======================================================================

PART_IX = Part(
    number=9,
    title="Take It Further",
    epigraph="Smaller units, more room for error, and minimum impact when "
             "errors occur.",
    promise="Where the method goes next, and what it does not cover.",
    chapters=(
        Chapter(
            49, "Bigger, Smaller, Other Frequencies",
            "Changing the dome without changing the method",
            "explain",
            (
                _p("opener", "Other Frequencies",
                   "What 3V and 4V change, and what they do not.",
                   words=400),
                _p("text", "More panels, shorter sticks",
                   "The trade, stated as arithmetic.", words=800),
                _p("table", "Frequency comparison",
                   "2V, 3V, 4V on panel count, member classes and longest "
                   "member.", words=300,
                   figures=(_f("frequency-compare",
                               "What each frequency asks of the woodpile.",
                               PLOT, plot="frequency_compare"),)),
                _p("text", "Where the method stops working",
                   "Too small and the sector is too fat for the panel.",
                   words=700),
            ),
            derives=("wedge_geometry.member_classes",),
        
            ref="frequencies",
        ),
        Chapter(
            50, "Other Species, Other Sections",
            "Hardwood, hemlock, and a trunk that is not round",
            "howto",
            (
                _p("opener", "Other Species",
                   "What changes when the tree is not pine.", words=400),
                _p("text", "Density, splitting and the drying schedule",
                   "Practical differences, species by species.", words=900),
                _p("text", "A trunk that is oval",
                   "Splitting an out-of-round section into eight usable "
                   "members.", words=750),
                _p("text", "Green versus dry",
                   "Building with green wood, and what it does over the "
                   "first year.", words=800),
            ),
        ),
        Chapter(
            51, "Building With Other People",
            "What changes when there are three of you",
            "howto",
            (
                _p("opener", "Other People",
                   "The method was designed for one; here is what a crew "
                   "changes.", words=400),
                _p("text", "Parallel jigs",
                   "Two benches, and the sorting problem that follows.",
                   words=700),
                _p("text", "Teaching the twelve steps",
                   "How to hand the procedure to somebody in an afternoon.",
                   words=700),
                _p("text", "A build that is not yours",
                   "Helping somebody else, and the liability conversation.",
                   words=600),
            ),
        ),
        Chapter(
            52, "What I Would Do Differently",
            "The honest closing chapter",
            "story",
            (
                _p("opener", "What I Would Do Differently",
                   "Close the story strand where it started: one person, "
                   "one saw.", words=400),
                _p("text", "The five decisions I would change",
                   "Specific, named, with what each would have cost.",
                   words=1000),
                _p("text", "What I would keep exactly",
                   "The parts that were right the first time.", words=700),
                _p("text", "The next one",
                   "What the second dome is, and why.", words=700),
                _p("plate", "The dome, a year on",
                   "The closing image.",
                   figures=(_f("closing-image", "One year on.", PHOTO,
                               full_page=True),),),
            ),
        ),
    ),
)


# ======================================================================
# THE TWO PARTS OF THIS BOOK
# ======================================================================
#
# The nine parts above are the original book -- the build, told as it was
# found. This volume is larger than that: it puts the build inside a first
# part and follows it with the argument for why any of it scales.
#
# The nine are *absorbed*, never rewritten. `_absorb` renumbers their
# chapters continuously and hangs each one's old part title on it as its
# `section`, so a reader still gets "The Wedge" and "The Fortnight" as
# signposts instead of a fifty-two-chapter run with one divider at the front.
#
# Renumbering is safe to do here -- and only here -- because prose refers to
# chapters through `{{ch.…}}` keys, never through numbers.

_LEGACY_PARTS = (PART_I, PART_II, PART_III, PART_IV, PART_V,
                 PART_VI, PART_VII, PART_VIII, PART_IX)


def _absorb(parts, start: int) -> tuple[tuple[Chapter, ...], int]:
    """Renumber a run of chapters continuously, and say where the next one goes.

    Returns the chapters and the number after the last of them, so the next
    part can carry on counting without a second place to get it wrong. Each
    chapter keeps its old part title as its section.
    """
    out: list[Chapter] = []
    number = start
    for part in parts:
        for chapter in part.chapters:
            out.append(replace(chapter, number=number, section=part.title))
            number += 1
    return tuple(out), number


_BUILD_CHAPTERS, _NEXT_NUMBER = _absorb(_LEGACY_PARTS, 1)

PART_BUILD = Part(
    number=1,
    title="How to Build One",
    epigraph="A dome is a frame, a skin and a floor, and the frame is the "
             "only part of it that has to be got right.",
    promise="The method, in the order it is actually done: what a dome is, "
            "why the shape carries load, how a tree becomes forty panels, and "
            "the fortnight that turns those panels into a shell.",
    chapters=_BUILD_CHAPTERS,
)

PART_SCALE = Part(
    number=2,
    title="Why It Scales",
    epigraph="The parts list does not grow with the house. Everything "
             "downstream of that one fact is this part.",
    promise="The argument for the whole idea: why the same frame covers a "
            "shed and a hall, what that does to cost and labour, and what "
            "would have to be true for a network of domes to work.",
    chapters=(
        Chapter(
            _NEXT_NUMBER, "The List That Does Not Grow",
            "Triple the diameter and the parts count does not move: the same "
            "forty triangles and one hundred and twenty struts frame a ten "
            "foot dome or a thirty foot one",
            "explain",
            (
                _p("opener", "The List That Does Not Grow",
                   "What actually changes when a dome gets bigger, and what "
                   "stays exactly where it was.", words=260),
                _p("table", "The same list, four times",
                   "Four diameters from the same frame: every count identical, "
                   "and only the stick moves.", words=420),
                _p("spread", "One grows as the square, one as a line",
                   "Floor area goes as the square of the diameter; the stick "
                   "to frame it goes as the diameter. Work out what that does "
                   "to the stick per square foot.", words=430,
                   figures=(_f("flat-rate-curves",
                               "Three lines: the floor rises as the square, "
                               "the stick as a line, and the parts list does "
                               "not rise at all.", PLOT, plot="flat_rate"),)),
                _p("text", "What is flat and what quietly is not",
                   "Nine processes, one hundred and twenty brackets, nine "
                   "hundred and sixty screws, at every size. Then the two "
                   "things that are not flat -- the stick and the skin -- "
                   "said out loud.", words=380),
                _p("worked", "The limit is my arms, not the arithmetic",
                   "The ceiling on the flat rate is a declared handling "
                   "limit: the longest member one person will carry and set "
                   "alone. Work that limit through the chord factors and it "
                   "picks out a diameter, and that diameter splits the "
                   "table.", words=460,
                   figures=(_f("solo-band",
                               "Member length against diameter, with the "
                               "declared handling limit crossing it.",
                               PLOT, plot="solo_band"),)),
                _p("text", "Inside the band, nothing changes at all",
                   "Below the limit the flat rate is not approximate, it is "
                   "exact: same assembly pattern, same hardware numbers, same "
                   "operations, same strut preparation. Above it there are "
                   "two honest options, and raising the frequency is the one "
                   "move that genuinely lengthens the list.", words=380),
                _p("text", "Solve it once",
                   "Every count in the table is a count of things you figure "
                   "out exactly once. The second build is the same list with "
                   "the problems already solved, so it can only be better "
                   "timing than the first.", words=300),
                _p("text", "Why it is worth counting this way",
                   "The rate a builder is paid does not move with the size of "
                   "the job, so the price of floor area falls as the dome "
                   "grows.", words=300),
            ),
            derives=("two_v_demo.franken_economics.flat_rate_table",
                     "two_v_demo.franken_economics.solo_band",
                     "two_v_demo.franken_economics.SOLO_LIMITS",
                     "two_v_demo.franken_economics.SUMMARY"),
            ref="flat_rate",
        ),

        # ---------------------------------------------------------- labour
        Chapter(
            _NEXT_NUMBER + 1, "Nine Processes at Any Size",
            "The nine operations named one by one, and why a list this short "
            "is the thing worth improving: fix one process and every dome you "
            "ever build gets cheaper",
            "explain",
            (
                _p("opener", "Nine Processes at Any Size",
                   "The parts list is flat; so is the process list, and the "
                   "process list is the shorter of the two.", words=240),
                _p("steps", "The nine, in the order they happen",
                   "Fell, rip, crosscut, fold, drill, screw, raise, sheathe "
                   "and glass -- named from franken_economics.PROCESSES, "
                   "with what each one actually asks of you.", words=620,
                   figures=(_f("nine-process-counts",
                               "Every operation's repetition count across "
                               "four diameters: seven lines dead flat, two "
                               "climbing.", PLOT, plot="process_counts"),)),
                _p("table", "Seven of the nine do not move at all",
                   "Not merely still on the list -- the identical count. "
                   "The two that move are the two that touch raw material "
                   "and area rather than joints.", words=300,
                   figures=(_f("nine-process-table",
                               "Every operation against four diameters. "
                               "Seven rows are constant all the way across.",
                               PLOT, plot="process_table"),)),
                _p("text", "Why a short list compounds",
                   "A dome shop optimises differently from a stick-frame "
                   "shop: there are few operations, they repeat, and "
                   "improving one improves every dome that follows. A house "
                   "with a twenty-item framing list alone has nowhere to put "
                   "that effort -- and a short list concentrates mistakes as "
                   "well as improvements.", words=460),
                _p("worked", "What one process is worth, in hours",
                   "Take the ripping, the longest of the nine, and work out "
                   "what the declared improvement returns over one build and "
                   "over a run of them.", words=440,
                   figures=(_f("nine-rip-payback",
                               "What a proportional saving at one bench "
                               "returns as the run of domes lengthens, "
                               "measured in whole ripping stages.",
                               PLOT, plot="rip_payback"),)),
                _p("text", "The processes that are not on the list",
                   "Permits, inspections, delivery, waiting for a crew. They "
                   "are real, they are not flat, and they are not in the "
                   "nine because the nine is a shop count, not a project "
                   "count.", words=340),
            ),
            derives=("two_v_demo.franken_economics.DomeSize",
                     "two_v_demo.book_math.fortnight"),
            ref="nine_processes",
        ),
        Chapter(
            _NEXT_NUMBER + 2, "What an Hour at the Log Is Worth",
            "Splitting your own struts pays a rate; here is the rate, "
            "computed three ways, including the way that flatters it least",
            "explain",
            (
                _p("opener", "What an Hour at the Log Is Worth",
                   "Not what timber costs. What an hour of your own time "
                   "buys when you spend it on a log instead of at a till.",
                   words=240),
                _p("worked", "One strut, valued three ways",
                   "Against a nominal two-by-four, against a dressed one, "
                   "and by board foot -- with the disagreement between them "
                   "left in.", words=520,
                   figures=(_f("scale-strut-value",
                               "One strut, valued three ways, with the "
                               "estimate this project started from kept in "
                               "the table.", PLOT, plot="strut_value"),)),
                _p("text", "Why the dressed number is the honest one",
                   "A nominal two-by-four is not two inches by four. It is "
                   "smaller, so a strut replaces more of them, so the "
                   "honest comparison is the *higher* one -- which is "
                   "exactly the direction that deserves suspicion, and "
                   "gets it here.", words=400),
                _p("text", "The shelf price is a stack",
                   "What you pay at a yard is the timber plus the drying "
                   "plus the handling plus the margin plus the overheads. "
                   "Harvesting removes some of those layers and not the "
                   "others, and it is worth knowing which.", words=420),
                _p("sidebar", "This is not money anybody has been paid",
                   "Every rate in this chapter is a substitution value: what "
                   "you did not spend, not what you earned. It buys "
                   "groceries only if you were going to buy the timber.",
                   words=240),
            ),
            derives=("two_v_demo.book_math.fortnight",
                     "two_v_demo.book_math.BOOK_TREE",
                     "two_v_demo.franken_economics.EXTERNAL_PRICES"),
            ref="hour_at_log",
        ),
        Chapter(
            _NEXT_NUMBER + 3, "Where the Fuel Actually Goes",
            "A metabolic ledger of one build: every part lifted, carried and "
            "fastened, priced in calories -- and the discovery that most of "
            "the fuel raises nothing at all",
            "explain",
            (
                _p("opener", "Where the Fuel Actually Goes",
                   "Money is one ledger. Calories are another, and it is the "
                   "one that decides whether a build is finishable alone.",
                   words=260),
                _p("table", "One house, counted in parts and motions",
                   "Every element, its mass, the motions it takes and the "
                   "energy each motion costs.", words=440,
                   figures=(_f("fuel-station-ledger",
                               "Fifteen stations, ordered by what they cost "
                               "a body rather than by what they weigh.",
                               PLOT, plot="station_ledger"),)),
                _p("worked", "The fastening surprise",
                   "Fastening spends the great majority of the fuel while "
                   "raising nothing: the screw does not go up, the arm does. "
                   "Carry that through and it changes which part of the "
                   "build is worth designing out.", words=520,
                   figures=(_f("fuel-motion-split",
                               "Each motion's share of the clock beside its "
                               "share of the fuel. Only the gap between the "
                               "two is intensity.",
                               PLOT, plot="motion_split"),
                            _f("fuel-motion-efficiency",
                               "How much of each motion's fuel became "
                               "height, against the most muscle can convert.",
                               PLOT, plot="motion_efficiency"))),
                _p("text", "What this says about the hardware",
                   "If most of the energy is in fastening, then a joint that "
                   "needs fewer fasteners is worth more than a joint that is "
                   "faster per fastener. That is an argument for the key and "
                   "against more screws.", words=420),
                _p("sidebar", "What is measured and what is modelled",
                   "The masses are real and the motions are counted. The "
                   "calorie cost of a motion is a published model with named "
                   "constants, and the felling and bucking were never "
                   "metered at all.", words=280),
            ),
            derives=("two_v_demo.energetics.build_energy",
                     "two_v_demo.energetics.EXTERNAL_CONSTANTS"),
            ref="fuel_ledger",
        ),

        # ------------------------------------------------------ the shell
        Chapter(
            _NEXT_NUMBER + 4, "Less Skin for the Same Floor",
            "A dome wraps a given floor in noticeably less outside surface "
            "than a box does, and the wall you never build never costs "
            "anything to build, heat or repair",
            "explain",
            (
                _p("opener", "Less Skin for the Same Floor",
                   "The cheapest square foot of wall is the one that is not "
                   "in the drawing.", words=240),
                _p("spread", "The same floor, two envelopes",
                   "A dome and a box at the same floor area, with their "
                   "envelopes computed and set side by side.", words=460,
                   figures=(_f("skin-two-envelopes",
                               "The same floor drawn twice, to one scale, "
                               "with the headroom line across both.",
                               PLOT, plot="envelope_compare"),)),
                _p("text", "What the saved skin is worth four times over",
                   "Skin is bought once, insulated once, weatherproofed "
                   "repeatedly and heated every winter. A saving in area is "
                   "a saving in all four, which is why this number is worth "
                   "more than it first looks.", words=440,
                   figures=(_f("skin-claims",
                               "Four claims, and which of them are actually "
                               "separate findings.",
                               PLOT, plot="advantage_claims"),)),
                _p("text", "Where the box wins",
                   "Boxes stack, share walls, take standard sheet goods "
                   "without cutting, and fit rectangular furniture. Row "
                   "housing beats a dome on envelope per floor outright, and "
                   "pretending otherwise is not an argument.", words=420,
                   figures=(_f("skin-versus-size",
                               "The surface margin against floor area, "
                               "carried past the size where it dies.",
                               PLOT, plot="envelope_versus_size"),)),
            ),
            derives=("two_v_demo.dome_advantage.dome_envelope",
                     "two_v_demo.dome_advantage.box_envelope",
                     "two_v_demo.dome_advantage.envelope_saving",
                     "two_v_demo.dome_advantage.envelope_crossover_sqft",
                     "two_v_demo.dome_advantage.standing_sqft",
                     "two_v_demo.dome_advantage.EXTERNAL"),
            ref="less_skin",
        ),
        Chapter(
            _NEXT_NUMBER + 5, "The Cheapest Square Footage in the Building",
            "Standing the shell on a short straight wall buys floor, "
            "headroom and usable edge for the least money per square foot of "
            "anything in the build",
            "explain",
            (
                _p("opener", "The Cheapest Square Footage in the Building",
                   "The dome's weakness is its edge. A pony wall fixes the "
                   "edge with the cheapest wall there is.", words=260),
                _p("table", "The pony wall ladder",
                   "Wall height against floor gained, headroom gained and "
                   "cost, so the reader can pick a rung.", words=440),
                _p("text", "Why the edge is the expensive part of a dome",
                   "A sphere meets the floor at a tangent, so the last foot "
                   "of radius has almost no headroom in it. Lifting the "
                   "whole shell converts that dead ring into room.",
                   words=420),
                _p("worked", "Where the ladder stops paying",
                   "Keep climbing and the wall stops being cheap: it starts "
                   "carrying load, it starts needing its own framing, and at "
                   "some rung you have simply built a round box with a hat "
                   "on. Find that rung.", words=440),
            ),
            derives=("two_v_demo.dome_performance.pony_wall_ladder",
                     "two_v_demo.dome_performance.assemblies"),
            ref="pony_wall",
        ),
        Chapter(
            _NEXT_NUMBER + 6, "The Roof Is Already a Gutter",
            "An overhanging brim throws water clear of every joint and "
            "collects it in the same move, and the annual catch off a dome "
            "this size is not a trivial number",
            "explain",
            (
                _p("opener", "The Roof Is Already a Gutter",
                   "The overhang is not decoration. It is the detail that "
                   "keeps water out of the base joints.", words=240),
                _p("spread", "Where the water goes, with and without a brim",
                   "Rain running down a shell into the base joints, against "
                   "rain dripping clear into a tank.", words=440),
                _p("worked", "The annual catch",
                   "Rainfall times footprint times a collection efficiency, "
                   "carried through to gallons, with the efficiency declared "
                   "rather than assumed.", words=460),
                _p("text", "What the catch is actually good for",
                   "Not drinking, without treatment. Irrigation, flushing, "
                   "washing and a buffer against a dry well -- and a reason "
                   "the tank belongs under the pad rather than beside it.",
                   words=400),
            ),
            derives=("two_v_demo.dome_performance.WaterCatch",
                     "two_v_demo.dome_performance.hat_rim_radius_ft"),
            ref="brim_gutter",
        ),
        Chapter(
            _NEXT_NUMBER + 7, "A House That Gets Warmer Every Winter",
            "Build the skeleton once and add layers to it for as long as you "
            "own it: the shell ladder turns a shelter into a house in steps "
            "you can afford one at a time",
            "explain",
            (
                _p("opener", "A House That Gets Warmer Every Winter",
                   "Most houses are finished or unfinished. A dome shell can "
                   "be neither, permanently and on purpose.", words=260),
                _p("table", "The shell ladder, rung by rung",
                   "Each layer, what it costs, what it does to the envelope "
                   "and what it does to the running bill.", words=460),
                _p("text", "Why the bones are the thing to get right",
                   "Every layer in that ladder attaches to the frame. Get "
                   "the frame right and nothing later is blocked; get it "
                   "wrong and every rung inherits the error.", words=420),
                _p("worked", "The rung that pays back fastest",
                   "Rank the layers by what they return per dollar and per "
                   "weekend, and be honest that the fastest payback is "
                   "rarely the one people do first.", words=440),
            ),
            derives=("park_model.shell_ladder",
                     "two_v_demo.dome_performance.running_costs"),
            ref="shell_ladder",
        ),

        # --------------------------------------------------- the ground
        Chapter(
            _NEXT_NUMBER + 8, "One Hardware Set, Three Sizes",
            "The brackets, keys and fasteners that frame a small dome frame "
            "a large one unchanged, which is what makes a shared parts bin "
            "possible across a whole site",
            "explain",
            (
                _p("opener", "One Hardware Set, Three Sizes",
                   "The counts were flat in chapter one of this part. The "
                   "hardware itself is flat too, and that is a different and "
                   "more useful claim.", words=260),
                _p("table", "The same bin, three domes",
                   "Hardware by class across three dome sizes, with the "
                   "columns that do not move shown not moving.", words=440),
                _p("text", "What invariance buys a site",
                   "One order, one bin, one spare set, one training. A park "
                   "of mixed dome sizes can hold a single inventory, which "
                   "is the difference between a hobby and an operation.",
                   words=420),
                _p("text", "What does change, and it is the timber",
                   "The stick grows. So does the section, eventually. The "
                   "hardware does not, and the reason is that a bracket "
                   "holds an angle, and the angles are the same at every "
                   "diameter.", words=380),
            ),
            derives=("park_model.hardware_invariance",
                     "park_model.dome_catalogue"),
            ref="hardware_invariance",
        ),
        Chapter(
            _NEXT_NUMBER + 9, "Buy for the Next Two Steps",
            "The cheapest thing you can do on a site is oversize the parts "
            "that are hard to change later and undersize nothing else",
            "explain",
            (
                _p("opener", "Buy for the Next Two Steps",
                   "Not for the dome you are building. For the two after "
                   "it.", words=240),
                _p("text", "What is hard to change and what is not",
                   "Trenches, conduit, pad diameter and service capacity are "
                   "hard. Shell layers, interior walls and fixtures are "
                   "easy. Spend the planning on the first list.", words=440),
                _p("worked", "The cost of the upgrade you did not leave room "
                   "for",
                   "Price the same service upgrade two ways: laid in at "
                   "build time, and retrofitted under a finished pad.",
                   words=480),
                _p("text", "The growth path as a sequence, not a plan",
                   "A plan is a drawing of the end state. A path is the "
                   "order in which you get there without ever having to "
                   "undo a step, and only the second one survives contact "
                   "with money.", words=420),
            ),
            derives=("park_model.housing_options",
                     "park_model.crossover_months"),
            ref="growth_path",
        ),
        Chapter(
            _NEXT_NUMBER + 10, "The Ground Is What You Cannot Take With You",
            "Measured across the dome catalogue, the foundation is between a "
            "small fraction and most of what a dome costs -- and it is the "
            "only part you leave behind",
            "explain",
            (
                _p("opener", "The Ground Is What You Cannot Take With You",
                   "The frame is portable. The ground under it is not, and "
                   "the ground is where the surprise is.", words=260),
                _p("table", "Foundation share, across the catalogue",
                   "Every dome in the catalogue with its foundation as a "
                   "share of its total, small to large.", words=440),
                _p("text", "Why the share swings so far",
                   "A cheap shell on an expensive pad and an expensive shell "
                   "on a cheap pad are both real configurations, and the "
                   "spread between them is the single largest lever on this "
                   "page.", words=440),
                _p("worked", "The hinge, stated as a decision",
                   "If the foundation is most of the cost, the shell is not "
                   "the thing to optimise. Work out which side of that hinge "
                   "a given build sits on before choosing anything else.",
                   words=460),
            ),
            derives=("park_model.foundation_share", "park_model.on_pad"),
            ref="foundation_share",
        ),
        Chapter(
            _NEXT_NUMBER + 11, "A Pad, Not a Plot",
            "A serviced pad is the unit a dome site is actually built from: "
            "a deck, a set of services and a diameter, priced as one thing",
            "explain",
            (
                _p("opener", "A Pad, Not a Plot",
                   "Land is sold in acres. Domes sit on pads, and the pad is "
                   "the thing with a price.", words=260),
                _p("table", "What a pad is made of",
                   "Deck, services, drainage and anchorage, each with its "
                   "cost and its life.", words=460),
                _p("text", "Gravel, concrete or wood",
                   "Three decks, three prices, three failure modes. The "
                   "cheapest to build is not the cheapest to own, and the "
                   "difference is not small.", words=440),
                _p("worked", "The cheap pad, costed honestly",
                   "The least a pad can cost and still be a pad, with every "
                   "line that got left out named so the number cannot be "
                   "mistaken for a finished one.", words=460),
            ),
            derives=("park_model.Pad", "park_model.pad_sizes",
                     "park_model.cheap_pad_rows",
                     "park_model.cheap_pad_cost"),
            ref="the_pad",
        ),
        Chapter(
            _NEXT_NUMBER + 12,
            "Turning the House Toward the Sun, Until It Stops Being Worth It",
            "A rotating foundation is buildable and it does raise the solar "
            "yield -- and the honest arithmetic says it pays only under "
            "conditions that are worth stating before anybody pours a ring",
            "explain",
            (
                _p("opener", "Turning the House Toward the Sun",
                   "The off-the-wall one. A house on a ring, following the "
                   "sun, and the reason it is in this book is that the "
                   "arithmetic is interesting even where it loses.",
                   words=280),
                _p("text", "Why a dome can do this and a box cannot",
                   "A circular footprint has no preferred direction, so "
                   "rotating it changes nothing about how it meets its pad. "
                   "A rectangle on a turntable is a geometry problem at "
                   "every angle.", words=420),
                _p("worked", "What tracking actually returns",
                   "The yield from a fixed array against a tracked one, "
                   "carried through with the ring, the drive and the "
                   "maintenance priced in.", words=500),
                _p("text", "Where it stops paying, said plainly",
                   "The ring costs money per foot of circumference and the "
                   "gain is a percentage of a solar yield. Write both as "
                   "curves and they cross, and on most sites they cross in "
                   "the wrong place.", words=440),
                _p("sidebar", "Why it is still in the book",
                   "Because it is a real answer to a real question, because "
                   "the failure is instructive, and because the conditions "
                   "under which it wins are specific enough to recognise if "
                   "you ever have them.", words=260),
            ),
            derives=("park_model.solar_layouts",
                     "park_model.declared",
                     "two_v_demo.park_facts.steps_solar"),
            ref="rotation",
        ),
        Chapter(
            _NEXT_NUMBER + 13, "One Pad, Every Dome Size",
            "An iris of hinged blades closes a single oversized pad down to "
            "whatever dome is standing on it, so one pad serves the whole "
            "catalogue instead of one model",
            "explain",
            (
                _p("opener", "One Pad, Every Dome Size",
                   "Pads come in steps. Domes do not. The iris is the "
                   "adapter between them.", words=260),
                _p("spread", "How the blades swing",
                   "The pivot ring, the blade length and the swing angle "
                   "that closes the opening to a given diameter -- solved, "
                   "so the drawing and the caption are the same fact.",
                   words=460),
                _p("worked", "What the iris costs against what it saves",
                   "One iris against the alternative of pouring a pad per "
                   "dome size, over a site with a mixed catalogue.",
                   words=480),
                _p("text", "The case against it",
                   "It is a mechanism on a foundation, which is a thing that "
                   "can seize, fill with grit and need maintaining. A pad "
                   "that never moves never fails, and that is a real "
                   "argument.", words=400),
            ),
            derives=("park_model.iris_span", "park_model.iris_covers",
                     "park_model.iris_cost", "park_model.domes_that_fit"),
            ref="the_iris",
        ),
        Chapter(
            _NEXT_NUMBER + 14, "Why a Network Beats a Park",
            "A park is pads you rent. A network is pads that hold their "
            "value because a dome can leave one and arrive at another, and "
            "that difference is the whole resale argument",
            "explain",
            (
                _p("opener", "Why a Network Beats a Park",
                   "The question nobody building a single dome asks, and "
                   "everybody building the second one does: what is it worth "
                   "when you want out?", words=280),
                _p("text", "The line, and what runs along it",
                   "Power, water, waste and data reach a pad along a line, "
                   "and the cost of that line per pad falls as pads are "
                   "added to it. That is the only economy of scale on the "
                   "site.", words=440),
                _p("worked", "Host and tenant, both sides of the ledger",
                   "What the pad owner takes and what the dome owner pays, "
                   "with the crossover where renting stops beating owning.",
                   words=500),
                _p("text", "Resale, with the haircut left in",
                   "A dome that can only sit on one pad is worth what that "
                   "pad's owner says. A dome that can move is worth what the "
                   "network says, minus a recovery penalty that is computed "
                   "here rather than waved away.", words=460),
                _p("sidebar", "This is the least-built idea in the book",
                   "The frame is built. The pad is costed. The network is "
                   "arithmetic and one film, and it should be read as a "
                   "proposal rather than a report.", words=260),
            ),
            derives=("park_model.host_comparison",
                     "park_model.tenant_utilities",
                     "park_model.crossover_months"),
            ref="the_network",
        ),
        Chapter(
            _NEXT_NUMBER + 15, "What Would Have to Be True",
            "The closing audit: every claim in this part restated as a "
            "condition, with the ones that are not met yet marked as not met",
            "explain",
            (
                _p("opener", "What Would Have to Be True",
                   "A book that only argues one way is a sales document. "
                   "This is the chapter that argues the other way.",
                   words=280),
                _p("table", "Every claim, and what it rests on",
                   "Each claim in this part with its source, its status "
                   "-- measured, modelled or proposed -- and its caveat.",
                   words=520),
                _p("text", "The finished number nobody likes",
                   "The honest all-in figure for a finished dome, which is "
                   "several times the bare shell, and the reason the bare "
                   "shell keeps getting quoted instead.", words=460),
                _p("text", "The energy claim this book does not make",
                   "A dome is not automatically cheaper to heat. The "
                   "envelope helps and the airtightness is a build-quality "
                   "question, and this book has not metered a winter.",
                   words=420),
                _p("text", "What one person has actually done",
                   "The narrowest true version of the whole argument: what "
                   "was built, what was measured, what was modelled, and "
                   "what is still only a drawing.", words=440),
            ),
            derives=("two_v_demo.house_economics.price_total",
                     "two_v_demo.house_economics.construction_total",
                     "two_v_demo.dome_performance.ten_points",
                     "two_v_demo.lexicon_concepts.CONCEPTS"),
            ref="honest_limits",
        ),
    ),
)

PARTS: tuple[Part, ...] = (PART_BUILD, PART_SCALE)


# ======================================================================
# BACK MATTER
# ======================================================================

BACK: tuple[Matter, ...] = (
    Matter("tables", "The Master Tables", (
        _p("table", "Full cut list",
           "Every member, by class, length and count.", words=200,
           figures=(_f("back-cutlist", "The complete cut list.", PLOT,
                       plot="worked_cutlist"),)),
        _p("table", "Full seam schedule",
           "Every seam, its fold angle and its key.", words=200,
           figures=(_f("back-seams", "The complete seam schedule.", PLOT,
                       plot="worked_seams"),)),
        _p("table", "Butt cut setups",
           "Every distinct saw setup in the build.", words=200,
           figures=(_f("back-setups", "Every distinct setup.", PLOT,
                       plot="butt_setups"),)),
        _p("table", "Declared constants",
           "The inputs table, repeated for reference.", words=200,
           figures=(_f("back-constants", "Declared inputs.", PLOT,
                       plot="declared_constants"),)),
    )),
    Matter("glossary", "Glossary", (
        _p("text", "Glossary",
           "Every term the book uses that a reader may not have.",
           words=1400),
    )),
    Matter("software", "The Software in This Book", (
        _p("text", "What generated these numbers",
           "Name every module, what it computes, and how to run it.",
           words=900),
        _p("steps", "Reproducing every figure in this book",
           "The actual commands, so a reader can regenerate the lot.",
           words=600),
        _p("text", "The launcher",
           "How to open any of it without touching a command line.",
           words=500),
    )),
    Matter("index", "Index and Colophon", (
        _p("text", "Index", "Generated from the manuscript.", words=0),
        _p("text", "Colophon",
           "How the book was made, including the fact that its arithmetic "
           "is a test suite.", words=350),
    )),
)


BOOK = Book(title=TITLE, subtitle=SUBTITLE, front=FRONT, parts=PARTS,
            back=BACK)


# ----------------------------------------------------------------------
# Reading the outline
# ----------------------------------------------------------------------

def outline_text(book: Book = BOOK, detail: str = "chapters") -> str:
    """The outline as plain text.

    ``detail`` is ``parts``, ``chapters`` or ``pages``.
    """
    lines = [f"{book.title}", f"{book.subtitle}", ""]
    lines.append(f"{len(book.parts)} parts, {len(book.chapters)} chapters, "
                 f"{book.sheets} pages, {book.words:,} words targeted, "
                 f"{len(book.figures)} figures")
    lines.append("")

    if detail != "parts":
        lines.append("FRONT MATTER")
        for matter in book.front:
            lines.append(f"  {matter.title}  "
                         f"({matter.sheets}pp, {matter.words:,}w)")
            if detail == "pages":
                for page in matter.pages:
                    lines.append(f"      [{page.kind}] {page.title}")
        lines.append("")

    for part in book.parts:
        lines.append(f"PART {part.number} -- {part.title.upper()}  "
                     f"({part.sheets}pp, {part.words:,}w, "
                     f"{'/'.join(part.strands)})")
        lines.append(f"    “{part.epigraph}”")
        if detail == "parts":
            lines.append("")
            continue
        for chapter in part.chapters:
            lines.append(f"  {chapter.number:>2}. {chapter.title}  "
                         f"[{chapter.strand}] "
                         f"({chapter.sheets}pp, {chapter.words:,}w)")
            lines.append(f"      {chapter.deck}")
            if chapter.corrects:
                lines.append(f"      CORRECTS: {chapter.corrects}")
            if detail == "pages":
                for page in chapter.pages:
                    figs = "".join(f" [{f.key}]" for f in page.figures)
                    lines.append(f"        [{page.kind}] {page.title}"
                                 f"{figs}")
        lines.append("")

    if detail != "parts":
        lines.append("BACK MATTER")
        for matter in book.back:
            lines.append(f"  {matter.title}  "
                         f"({matter.sheets}pp, {matter.words:,}w)")
            if detail == "pages":
                for page in matter.pages:
                    lines.append(f"      [{page.kind}] {page.title}")
    return "\n".join(lines)


def figure_index(book: Book | None = None) -> dict[str, Figure]:
    """Every figure by key, for the renderer and the writing desk.

    Not cached: a ``Figure`` carries a spec dictionary, so the outline is
    not hashable, and rebuilding sixty entries costs nothing.
    """
    return {fig.key: fig for fig in (book or BOOK).figures}


def strand_chapters(strand: str, book: Book = BOOK) -> tuple[Chapter, ...]:
    """Every chapter on one strand, in order.

    A reader who wants only the manual reads the ``howto`` chapters straight
    through; the book says so on its own contents page, so it has to be true.
    """
    return tuple(ch for ch in book.chapters if ch.strand == strand)


# ----------------------------------------------------------------------
# The self-test
# ----------------------------------------------------------------------

def validate_book() -> None:
    """The outline has to be sound before anybody writes into it."""
    book = BOOK

    # Chapters are numbered 1..N with no gaps and no repeats: a book with
    # two chapter 19s is a book nobody can navigate.
    numbers = [ch.number for ch in book.chapters]
    assert numbers == list(range(1, len(numbers) + 1)), numbers

    # Slugs are unique, or two chapters share a manuscript file and one
    # silently overwrites the other.
    slugs = [ch.slug for ch in book.chapters]
    assert len(set(slugs)) == len(slugs), \
        [s for s in slugs if slugs.count(s) > 1]

    # Figure keys are unique across the whole book, since the renderer
    # writes one file per key.
    keys = [fig.key for fig in book.figures]
    assert len(set(keys)) == len(keys), \
        sorted({k for k in keys if keys.count(k) > 1})

    # Every page kind and strand is one this book knows how to set.
    for part in book.parts:
        for chapter in part.chapters:
            assert chapter.strand in STRANDS, (chapter.number, chapter.strand)
            assert chapter.pages, f"chapter {chapter.number} has no pages"
            assert chapter.deck.strip(), chapter.number
            for page in chapter.pages:
                assert page.kind in PAGE_KINDS, (chapter.number, page.kind)
                assert page.purpose.strip(), (chapter.number, page.title)
                # A page with no words and no figure is a page with nothing
                # on it.
                assert page.words or page.figures, \
                    (chapter.number, page.title)
    for matter in book.front + book.back:
        for page in matter.pages:
            assert page.kind in PAGE_KINDS, (matter.key, page.kind)

    # Every chapter opens with an opener, so the design is consistent.
    for chapter in book.chapters:
        assert chapter.pages[0].kind == "opener", \
            (chapter.number, chapter.pages[0].kind)

    # A chapter that names figures must say where its numbers come from,
    # or the manuscript can invent them. Story chapters may state none.
    for chapter in book.chapters:
        mentions = any("{{" in page.title or "{{" in fig.caption
                       for page in chapter.pages for fig in page.figures)
        if mentions:
            assert chapter.derives, \
                f"chapter {chapter.number} prints numbers but derives none"

    # Every renderer named by a figure is one book_figures implements.
    known = {DOME, JIG, PANEL, SHOT, PLOT, DIAG, PHOTO}
    for fig in book.figures:
        assert fig.source in known, (fig.key, fig.source)

    # Every strand is actually used, or the contents page promises a track
    # that does not exist.
    for strand in STRANDS:
        assert strand_chapters(strand), strand

    # Corrections are real: a chapter that claims to correct something says
    # what, and there is an errata page in it to do it on.
    for chapter in book.chapters:
        if chapter.corrects:
            assert any(page.kind == "errata" for page in chapter.pages), \
                chapter.number

    # The book is a book: enough pages to bind, not so many nobody finishes.
    #
    # These bounds are a tripwire, not a target. They exist so that the
    # outline growing -- which it does every time a chapter is inserted --
    # is something somebody notices and decides about, rather than something
    # that happens quietly over a month. The plan is currently around
    # 160,000 words, which is a long book: a complete build manual, a
    # reference and a narrative bound together. That is a deliberate choice
    # and the per-page targets in the outline are where to trim it.
    assert 300 <= book.sheets <= 800, book.sheets
    assert 60000 <= book.words <= 200000, book.words

    _check_derivations(book)

    counts = {strand: len(strand_chapters(strand)) for strand in STRANDS}
    print(f"book OK: {len(book.parts)} parts, {len(book.chapters)} chapters, "
          f"{book.sheets} pages, {book.words:,} words, "
          f"{len(book.figures)} figures; strands {counts}")


def _check_derivations(book: Book) -> None:
    """Every ``derives`` entry names something that actually exists.

    ``derives`` is the promise that a chapter's numbers come from code rather
    than from the author's memory, and an unchecked promise is a comment. A
    function that gets renamed, or a module that gets split, should break the
    outline loudly instead of leaving a chapter pointing at nothing.

    Two spellings are accepted because the outline has always used both: a
    bare module name is looked up inside ``two_v_demo`` first and then at the
    top level, so ``book_math.fortnight`` and ``park_model.on_pad`` both
    resolve without anybody having to remember which package a module lives
    in. Dotted attribute paths (``BOOK_TREE.recovery``) are walked.
    """
    import importlib

    def resolve(reference: str) -> bool:
        parts = reference.split(".")
        for split in range(len(parts) - 1, 0, -1):
            name = ".".join(parts[:split])
            for candidate in (name, f"{__package__}.{name}"):
                try:
                    module = importlib.import_module(candidate)
                except ImportError:
                    continue
                target = module
                for attribute in parts[split:]:
                    if not hasattr(target, attribute):
                        break
                    target = getattr(target, attribute)
                else:
                    return True
        return False

    broken = [(chapter.number, reference)
              for chapter in book.chapters
              for reference in chapter.derives
              if not resolve(reference)]
    assert not broken, f"chapters deriving from nothing: {broken}"

    _run_source_selftests(book)


def _run_source_selftests(book: Book) -> None:
    """Run the selftest of every module a chapter derives its numbers from.

    Naming a module in ``derives`` used to prove only that the name still
    existed. But a chapter's numbers are exactly as trustworthy as the
    module behind them, and most of those modules carry a ``validate_*``
    that pins the claims the book repeats -- that the surface margin has
    not drifted, that a round trip still closes, that a ratio a paragraph
    describes in words is still the ratio it describes.

    Those selftests were reachable only through the films that happened to
    call them, so a change could pass the book's own checks and leave a
    written chapter quietly wrong. Running them here closes that gap: the
    book cannot report itself sound while any arithmetic it cites is not.

    Costs about twelve seconds, nearly all of it the metabolic ledger
    walking its element list. That is a fair price for the guarantee.
    """
    import contextlib
    import importlib
    import io

    seen: dict[str, object] = {}
    for chapter in book.chapters:
        for reference in chapter.derives:
            parts = reference.split(".")
            for split in range(len(parts) - 1, 0, -1):
                name = ".".join(parts[:split])
                for candidate in (name, f"{__package__}.{name}"):
                    if candidate in seen:
                        break
                    try:
                        seen[candidate] = importlib.import_module(candidate)
                    except ImportError:
                        continue
                    break
                else:
                    continue
                break

    failures = []
    for name, module in sorted(seen.items()):
        for attribute in sorted(dir(module)):
            if not attribute.startswith("validate_"):
                continue
            check = getattr(module, attribute)
            if not callable(check):
                continue
            try:
                # Several of these announce themselves when they pass,
                # and the book's own summary already says book_math is
                # sound. Swallow the chatter; keep the failure.
                with contextlib.redirect_stdout(io.StringIO()):
                    check()
            except Exception as error:      # noqa: BLE001 - reported below
                # A bare `assert x` carries no message at all, so report
                # the line that failed as well. Without this the whole
                # report reads "validate_advantage: " and says nothing.
                import traceback
                frame = traceback.extract_tb(error.__traceback__)[-1]
                detail = str(error).strip() or type(error).__name__
                failures.append(
                    f"{name}.{attribute}: {detail}\n"
                    f"      {Path(frame.filename).name}:{frame.lineno}  "
                    f"{(frame.line or '').strip()}")
    assert not failures, \
        "source selftests the book depends on are failing:\n  " \
        + "\n  ".join(failures)


def validate_everything() -> None:
    """Run every self-test the book has, in dependency order.

    One command that says whether the book is sound: its arithmetic, its
    tokens, its outline, its figures and its manuscript machinery. Ordered so
    the cheapest and most fundamental fails first -- there is no point
    checking that a chapter quotes a token correctly if the arithmetic behind
    that token is broken.
    """
    from . import (book_export, book_figures, book_manuscript, book_math,
                   book_tokens)

    book_math.validate_book_math()
    validate_book()
    book_tokens.validate_tokens()
    book_figures.validate_figures()
    book_manuscript.validate_manuscript()
    book_export.validate_export()
    print("--- 2 Trees: every check passed")


if __name__ == "__main__":
    print(outline_text(detail="pages"))
    print()
    validate_everything()
