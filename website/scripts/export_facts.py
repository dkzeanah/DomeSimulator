"""Write zeanahlab.com's numbers from the project's own models.

The site never types a figure. This script asks the same functions the films and books
read -- web/export_facts.build() (seed_model + kickstarter: the stem cell, its price, the
goal and the tiers), the book catalogue in web/books.config.json, and the stem cell's own
panel count for the founder plaques -- and writes src/generated/facts.json, which the
React pages import and the API reads.

    py -3.12 scripts/export_facts.py            # regenerate
    py -3.12 scripts/export_facts.py --check    # fail if the committed file is stale
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
SITE = HERE.parent
ROOT = SITE.parent
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "web"))

import export_facts as web_facts  # noqa: E402  (web/export_facts.py: the existing reader)
import seed_model  # noqa: E402

OUT = SITE / "src" / "generated" / "facts.json"


def build() -> dict:
    facts = web_facts.build()
    geo = seed_model.seed_geometry()
    catalogue = json.loads((ROOT / "web" / "books.config.json").read_text(encoding="utf-8"))
    site = json.loads((ROOT / "web" / "site.config.json").read_text(encoding="utf-8"))
    books = [{k: b[k] for k in ("slug", "title", "subtitle", "author", "blurb", "offer", "priceCents",
                                "currency", "includes", "kind", "bookingNote", "codebaseUrl", "amazonUrl", "file")
              if k in b}
             for b in catalogue["books"] if b.get("offer") != "none"]
    facts.update({
        "_generated_by": "website/scripts/export_facts.py from web/export_facts.build(), seed_model and "
                         "web/books.config.json -- do not edit",
        "plaques": {"slots": sum(f.count for f in geo.faces),
                    "source": "seed_model.seed_geometry().faces -- one plaque per panel of the stem cell"},
        "books": books,
        # contents, page counts and headline figures of each book, from the books' own
        # token resolvers -- the same values the books print (web/export_facts.books())
        "bookFacts": web_facts.books(),
        "site": {k: site[k] for k in ("name", "url", "tagline", "kickstarterUrl", "youtubeChannelUrl", "links")
                 if k in site},
    })
    facts["sources"]["plaques"] = facts["plaques"]["source"]
    facts["sources"]["books"] = "web/books.config.json"
    return facts


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--check", action="store_true")
    a = ap.parse_args()
    text = json.dumps(build(), indent=2, ensure_ascii=False) + "\n"
    if a.check:
        if not OUT.exists() or OUT.read_text(encoding="utf-8") != text:
            print(f"{OUT} is stale: run py -3.12 scripts/export_facts.py")
            return 1
        print("facts.json is current")
        return 0
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(text, encoding="utf-8")
    print(f"wrote {OUT.relative_to(ROOT)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
