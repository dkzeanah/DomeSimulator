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
#: which pages (0-based) and what each shows -- chosen by looking at the sample
PAGES = [
    (0, "The cover"),
    (1, "What the book is, in its own numbers"),
    (4, "Chapter 1: Your Skull Is Not Symmetrical Either"),
    (8, "Chapter 2: Water Is the Silent Killer"),
    (14, "Chapter 13: Stop Squaring. Start Splitting."),
    (18, "The whole book: every part and chapter"),
]


def main() -> int:
    pdf = medialib.latest("the-40-hour-cabin-sample", ".pdf")
    if pdf is None:
        print("no sample PDF in the library")
        return 1
    OUT.mkdir(parents=True, exist_ok=True)
    doc = pymupdf.open(pdf)
    index = []
    for i, caption in PAGES:
        if i >= doc.page_count:
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
