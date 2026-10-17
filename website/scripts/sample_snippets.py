"""Cut the funnel's teaser images out of the real sample PDF.

The /start page shows pages of the free sample -- the actual pages, from the newest edition
in the library (medialib.latest), so the teaser can never promise something the PDF does not
contain. Re-run after a new edition of the sample is published.

    py -3.12 scripts/sample_snippets.py
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

SITE = Path(__file__).resolve().parent.parent
ROOT = SITE.parent
sys.path.insert(0, str(ROOT))

import medialib  # noqa: E402
import pymupdf  # noqa: E402

OUT = SITE / "public" / "img" / "sample"
#: which pages, and what each shows -- each found by the words it opens with, so a new
#: edition of the sample (which can grow or shrink) still gives the right pages. None is
#: the cover, which is a picture.
PAGES = [
    (None, "The cover"),
    ("Free sample", "What the book is, in its own numbers"),
    ("Your Skull Is Not Symmetrical Either", "Chapter 1: Your Skull Is Not Symmetrical Either"),
    ("Water Is the Silent Killer", "Chapter 2: Water Is the Silent Killer"),
    ("Stop Squaring. Start Splitting.", "Chapter 13: Stop Squaring. Start Splitting."),
    ("A home you can account for", "A home you can account for: one number, the whole dome"),
]


def _squash(text: str) -> str:
    return "".join(ch for ch in text.lower() if ch.isalnum())


def find_page(doc, opening: str | None) -> int | None:
    """The first page whose first lines carry ``opening`` (letter-spacing ignored)."""
    if opening is None:
        return 0
    want = _squash(opening)
    for i, page in enumerate(doc):
        head = _squash(" ".join(page.get_text().strip().splitlines()[:4]))
        if want in head:
            return i
    return None


def main() -> int:
    pdf = medialib.latest("the-40-hour-cabin-sample", ".pdf")
    if pdf is None:
        print("no sample PDF in the library")
        return 1
    OUT.mkdir(parents=True, exist_ok=True)
    doc = pymupdf.open(pdf)
    index = []
    for opening, caption in PAGES:
        i = find_page(doc, opening)
        if i is None:
            print(f"  not in {pdf.name}: {caption}")
            continue
        pix = doc[i].get_pixmap(dpi=110)
        name = f"sample-page-{i + 1:02d}.jpg"
        pix.pil_save(OUT / name, quality=82)
        index.append({"src": f"/img/sample/{name}", "page": i + 1, "caption": caption})
    (SITE / "src" / "generated" / "sample-pages.json").write_text(
        json.dumps({"_generated_by": "scripts/sample_snippets.py from " + pdf.name, "pages": index}, indent=2) + "\n",
        encoding="utf-8")
    print(f"{len(index)} pages from {pdf.name}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
