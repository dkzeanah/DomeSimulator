"""What Amazon KDP requires of a paperback interior and its cover, as declared constants.

None of these can be derived: they are KDP's published rules (Kindle Direct Publishing help,
"Set Trim Size, Bleed, and Margins", "Paperback Page Count", "Create a Paperback Cover" and
"Paperback Submission Guidelines", as the project read them in October 2026). Each carries the
rule it states. KDP changes its tables now and then -- check them against the help pages before
an upload; the Proof Desk prints this table beside every certificate so the reader can.

wedge_book.kdp lays its own book out to the strictest of these; books.studio.proof checks any
finished PDF against them.
"""

from __future__ import annotations

SOURCE = "Amazon KDP help pages (trim, bleed and margins; page count; paperback cover; submission guidelines), as read October 2026"

#: KDP's paperback trim sizes, inches (width, height).
TRIM_SIZES: tuple[tuple[float, float], ...] = (
    (5.0, 8.0), (5.06, 7.81), (5.25, 8.0), (5.5, 8.5), (6.0, 9.0), (6.14, 9.21), (6.69, 9.61), (7.0, 10.0),
    (7.44, 9.69), (7.5, 9.25), (8.0, 10.0), (8.25, 6.0), (8.25, 8.25), (8.5, 8.5), (8.5, 11.0), (8.27, 11.69),
)

#: Bleed: what a full-bleed interior adds to the trim, inches -- the outside edge, and top plus bottom.
BLEED_WIDTH_IN = 0.125
BLEED_HEIGHT_IN = 0.25

#: The inside (gutter) margin by page count: (most pages, least inside margin in inches).
GUTTER_TABLE: tuple[tuple[int, float], ...] = ((150, 0.375), (300, 0.5), (500, 0.625), (700, 0.75), (828, 0.875))

#: The least outside, top and bottom margin, inches, without and with bleed.
OUTSIDE_MIN_IN = 0.25
OUTSIDE_MIN_BLEED_IN = 0.375

#: Page counts KDP prints, by interior (least, most) -- the regular trim sizes.
PAGE_RANGE = {"black-white": (24, 828), "black-cream": (24, 776), "standard-color": (72, 600), "premium-color": (24, 828)}

#: Spine width per page, inches, by paper (KDP's cover calculator uses these).
SPINE_PER_PAGE_IN = {"black-white": 0.002252, "black-cream": 0.0025, "standard-color": 0.002252, "premium-color": 0.002347}

#: KDP allows text on the spine only from this many pages up.
SPINE_TEXT_MIN_PAGES = 79

#: What the cover's full wrap adds round the trim: bleed on every edge, inches.
COVER_BLEED_IN = 0.125

#: Images KDP prints sharply: it warns below this resolution.
IMAGE_MIN_PPI = 300

#: Blank pages: KDP rejects more than this many in a row at the start or in the middle, and more than END at the end.
BLANK_RUN_MAX = 2
BLANK_END_MAX = 10

#: The largest interior file KDP takes, bytes.
FILE_MAX_BYTES = 650 * 1024 * 1024


def gutter_for(pages: int) -> float | None:
    """The least inside margin KDP asks of a book this long, inches (None past the table)."""
    for most, inside in GUTTER_TABLE:
        if pages <= most:
            return inside
    return None


def spine_in(pages: int, paper: str = "black-white") -> float:
    return pages * SPINE_PER_PAGE_IN[paper]


def cover_size_in(trim: tuple[float, float], pages: int, paper: str = "black-white") -> tuple[float, float]:
    """The full-wrap cover, inches: bleed, back, spine, front, bleed across; bleed, trim, bleed down."""
    w, h = trim
    return (COVER_BLEED_IN * 2 + w * 2 + spine_in(pages, paper), COVER_BLEED_IN * 2 + h)


def table() -> list[dict]:
    """The rules, for printing beside a certificate."""
    return [
        {"rule": "Trim sizes", "value": ", ".join(f"{w:g} x {h:g} in" for w, h in TRIM_SIZES)},
        {"rule": "Bleed adds", "value": f"{BLEED_WIDTH_IN} in to the width, {BLEED_HEIGHT_IN} in to the height"},
        {"rule": "Inside margin by page count", "value": "; ".join(f"up to {n}: {m} in" for n, m in GUTTER_TABLE)},
        {"rule": "Outside, top and bottom", "value": f"at least {OUTSIDE_MIN_IN} in ({OUTSIDE_MIN_BLEED_IN} in with bleed)"},
        {"rule": "Page counts", "value": "; ".join(f"{k}: {a}-{b}" for k, (a, b) in PAGE_RANGE.items())},
        {"rule": "Spine per page", "value": "; ".join(f"{k}: {v} in" for k, v in SPINE_PER_PAGE_IN.items())},
        {"rule": "Spine text", "value": f"{SPINE_TEXT_MIN_PAGES} pages or more"},
        {"rule": "Images", "value": f"{IMAGE_MIN_PPI} ppi or better"},
        {"rule": "Blank pages", "value": f"no more than {BLANK_RUN_MAX} in a row (start or middle), {BLANK_END_MAX} at the end"},
        {"rule": "File size", "value": f"up to {FILE_MAX_BYTES // (1024 * 1024)} MB"},
        {"rule": "Fonts", "value": "every font embedded"},
    ]
