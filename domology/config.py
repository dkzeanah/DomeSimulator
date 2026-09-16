"""Every setting that shapes the printed book, in one place.

The page is a real KDP paperback: 8 x 10 inch trim, premium colour, printed
with bleed. KDP's published rules are here as data -- the inside margin a page
count needs, the paper thickness that sets the spine -- so the build can check
the interior against them instead of trusting that somebody remembered.

Units: inches where KDP states inches, points (1/72 inch) everywhere a page is
drawn. ``Trim`` and ``Grid`` convert.
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path


PKG = Path(__file__).resolve().parent
ROOT = PKG.parent
MANUSCRIPT = PKG / "manuscript"
CACHE = PKG / ".cache"
"""Scratch state the build may overwrite: layouts, measured plate sizes."""
HISTORY = PKG / "history"
"""Every saved version of a chapter from the editor, never deleted."""
ANNOTATIONS = PKG / "annotations.json"
"""Notes left in the editor for the next revision pass."""
OUT = ROOT / "deliverables" / "domology"
"""Finished things. Append-only, like every deliverable in this repository."""
PLATES = OUT / "plates"

PT_PER_IN = 72.0

TITLE = "Domology"
SUBTITLE = "The Geodesic Dome: the Science, the Journey, and the Build"
TAGLINE = "Three books in one"
AUTHOR = "[AUTHOR NAME]"
"""Left as a placeholder on purpose: the author sets it, the build does not
guess it. A final build refuses to run while it is still in brackets."""


# ----------------------------------------------------------------------
# KDP's rules
# ----------------------------------------------------------------------

KDP_PAGE_RANGE = (24, 828)
"""Premium-colour paperback page limits."""

SPINE_IN_PER_PAGE = {"white": 0.002252, "cream": 0.0025,
                     "premium_color": 0.002347}
"""Paper thickness per page, which is what the spine width is made of."""

PAPER = "premium_color"

GUTTER_IN = ((150, 0.375), (300, 0.5), (500, 0.625), (700, 0.75),
             (828, 0.875))
"""Minimum inside margin by page count: (up to this many pages, inches)."""

MIN_OUTER_IN_WITH_BLEED = 0.375
"""Minimum outside, top and bottom margin when the file has bleed."""

SPINE_TEXT_MIN_PAGES = 80
"""KDP prints spine text only on books of more than 79 pages."""


def min_gutter_in(pages: int) -> float:
    for limit, inches in GUTTER_IN:
        if pages <= limit:
            return inches
    raise ValueError(f"{pages} pages is more than KDP prints")


# ----------------------------------------------------------------------
# The page
# ----------------------------------------------------------------------

@dataclass(frozen=True)
class Trim:
    """The finished page, and the bleed printed past its outside edges."""

    width_in: float = 8.0
    height_in: float = 10.0
    bleed_in: float = 0.125

    @property
    def canvas_w(self) -> float:
        """Page width in the PDF: bleed on the outside edge only."""
        return (self.width_in + self.bleed_in) * PT_PER_IN

    @property
    def canvas_h(self) -> float:
        """Page height in the PDF: bleed at the top and the bottom."""
        return (self.height_in + 2.0 * self.bleed_in) * PT_PER_IN

    @property
    def width(self) -> float:
        return self.width_in * PT_PER_IN

    @property
    def height(self) -> float:
        return self.height_in * PT_PER_IN

    @property
    def bleed(self) -> float:
        return self.bleed_in * PT_PER_IN

    def x0(self, recto: bool) -> float:
        """Where the trimmed page starts on the canvas.

        A right-hand page has its spine on the left and its bleed on the
        right, so the trim starts at zero; a left-hand page is the mirror.
        """
        return 0.0 if recto else self.bleed

    @property
    def y0(self) -> float:
        return self.bleed


@dataclass(frozen=True)
class Grid:
    """Margins and the two columns: the reading column, and the outer column
    where side notes, and the provenance of the numbers, are printed."""

    inside_in: float = 0.75
    outside_in: float = 0.55
    top_in: float = 0.75
    bottom_in: float = 0.9
    side_in: float = 1.8
    gap_in: float = 0.24

    @property
    def inside(self) -> float:
        return self.inside_in * PT_PER_IN

    @property
    def outside(self) -> float:
        return self.outside_in * PT_PER_IN

    @property
    def top(self) -> float:
        return self.top_in * PT_PER_IN

    @property
    def bottom(self) -> float:
        return self.bottom_in * PT_PER_IN

    @property
    def side(self) -> float:
        return self.side_in * PT_PER_IN

    @property
    def gap(self) -> float:
        return self.gap_in * PT_PER_IN


@dataclass(frozen=True)
class Type:
    """Type sizes and line spacing, in points."""

    body: float = 10.4
    leading: float = 14.6
    small: float = 7.7
    small_leading: float = 10.2
    h2: float = 13.2
    h3: float = 10.8
    caption: float = 8.2
    caption_leading: float = 10.6
    mono: float = 7.3
    mono_leading: float = 10.0
    head: float = 6.9
    folio: float = 8.0
    chapter_number: float = 58.0
    chapter_title: float = 25.0
    deck: float = 12.6
    pull: float = 13.4


TRIM = Trim()
GRID = Grid()
TYPE = Type()


# ----------------------------------------------------------------------
# Colour
# ----------------------------------------------------------------------
# The two accent colours are the dome's two strut lengths as the simulator
# paints them: amber for the long strut, cyan for the short. On paper they
# are darkened so they survive premium-colour printing and still read in
# greyscale proofs.

INK = "#1c1b19"
MUTED = "#6c655a"
FAINT = "#b9b1a4"
RULE = "#cfc7ba"
LONG = "#b8751a"
"""Amber: the long strut. Chapter numbers, plate labels, conclusions."""
SHORT = "#17779a"
"""Cyan: the short strut. Rules, links, side-note markers."""
NIGHT = "#070b13"
"""The simulator's own background, for full-bleed plate pages."""
PAPER_WHITE = "#ffffff"
MATH_TINT = "#eaf4f7"
CONCLUSION_TINT = "#fbeed8"
SIDEBAR_TINT = "#f3efe7"
SAFETY_TINT = "#fbe7e2"
SAFETY = "#a3321f"
AUTHOR_TINT = "#fff3a8"
AUTHOR_EDGE = "#c9a400"
