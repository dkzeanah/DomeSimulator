"""Write the stem cell's figures for the web app, from the model.

The site shows the dome's size, price, reward tiers and fit-outs. None of
those are typed into the React code: this script asks :mod:`seed_model` and
:mod:`kickstarter` (through :func:`campaign_prompts.facts`, the same reader the
image prompts use) and writes ``server/src/generated/facts.json``, which the
API serves at ``/api/facts``. Change the model, run this, and the site agrees.

    py -3.12 export_facts.py            # regenerate
    py -3.12 export_facts.py --check    # fail if the committed file is stale
"""

from __future__ import annotations

import argparse
import json
import sys
from dataclasses import asdict
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent))

import campaign_prompts  # noqa: E402
import kickstarter  # noqa: E402
import seed_model  # noqa: E402

OUT = HERE / "server" / "src" / "generated" / "facts.json"


def build() -> dict:
    f = campaign_prompts.facts()
    return {
        "_generated_by": "web/export_facts.py from seed_model and kickstarter -- do not edit",
        "dome": {
            "acrossFt": round(f.across_ft, 2),
            "tallFt": round(f.tall_ft, 2),
            "floorSqft": round(f.floor_sqft, 1),
            "bays": f.bays,
            "members": f.members,
            "vertices": f.vertices,
            "baseSides": f.base_sides,
        },
        "price": {
            "stemCell": round(f.price),
            "costToBuild": round(f.built),
            "profit": round(f.margin),
            "marginOnCost": kickstarter.MARGIN,
            "perSqft": round(f.per_sqft, 2),
        },
        "wood": {
            "wedgeVsMilled": round(f.wedge_vs_milled, 2),
            "treesVsMitred": round(f.trees_vs_mitred, 3),
        },
        "quilt": {"shirtsPerLayer": f.shirts_per_layer},
        "goal": {
            "total": round(f.goal),
            "lines": [asdict(line) for line in kickstarter.goal_lines()],
        },
        "tiers": [
            {"key": t.key, "label": t.label, "pledge": t.pledge, "why": t.why}
            for t in kickstarter.tiers()
        ],
        "fitouts": [
            {"key": x.key, "label": x.label, "shape": x.shape, "blurb": x.blurb}
            for x in seed_model.fitouts()
        ],
        "panels": [
            {"key": p.key, "label": p.label, "usd": p.usd, "note": p.note}
            for p in seed_model.PANELS
        ],
        "sources": {
            "dome": "seed_model.seed_geometry()",
            "price": "kickstarter.cost_stack()",
            "wood": "seed_model.harvest(), seed_model.trees_against_mitred()",
            "quilt": "kickstarter.quilt_economics()",
            "goal": "kickstarter.goal_lines()",
            "tiers": "kickstarter.tiers()",
            "fitouts": "seed_model.fitouts()",
            "panels": "seed_model.PANELS",
        },
    }


BOOK_DIR = HERE.parent / "deliverables" / "book"


def _newest_pdf(stem: str) -> Path | None:
    """The highest -vN of a book, the same rule the server's latestVersion uses."""
    import re

    best, best_v = None, -1
    for path in BOOK_DIR.glob(f"{stem}*.pdf"):
        m = re.fullmatch(rf"{re.escape(stem)}(?:-v(\d+))?\.pdf", path.name)
        if m and (v := int(m.group(1) or 1)) > best_v:
            best, best_v = path, v
    return best


def _pages(path: Path | None) -> int | None:
    if not path:
        return None
    import pymupdf

    with pymupdf.open(path) as doc:
        return doc.page_count


def _contents(book) -> list[dict]:
    return [{"number": p.number, "title": p.title,
             "chapters": [{"number": c.number, "title": c.title} for c in p.chapters]}
            for p in book.parts]


def books() -> dict:
    """What the sales pages say about each book: contents, size and the
    headline figures, every one read from the book's own token resolver --
    the same values the books print."""
    from two_v_demo import book as digital_book, book_tokens as digital_tokens
    from wedge_book import outline as paper_outline, paper, teaser, tokens as paper_tokens

    def d(name: str) -> str:
        return digital_tokens.resolve("{{" + name + "}}")

    def w(name: str) -> str:
        return paper_tokens.resolve("{{" + name + "}}")

    digital = digital_book.BOOK
    paper_book = paper_outline.BOOK
    return {
        "digital": {
            "title": digital_book.TITLE,
            "subtitle": digital_book.SUBTITLE,
            "parts": _contents(digital),
            "chapters": sum(len(p.chapters) for p in digital.parts),
            "figures": sum(len(c.figures) for p in digital.parts for c in p.chapters),
            "pages": _pages(_newest_pdf("2-trees")),
            "numbers": {
                "trees": d("dome.trees"), "diameterFt": d("dome.diameter_ft"),
                "floorSqft": d("dome.floor_sqft"), "members": d("frame.members"),
                "panels": d("frame.panels"), "frameHours": d("hr.total"),
                "days": d("work.days"), "sawUsd": d("saw.price_usd"),
                "strutsPerTree": d("tree.struts_per_tree"),
            },
        },
        "paperback": {
            "title": paper_outline.TITLE,
            "subtitle": paper_outline.SUBTITLE,
            "author": paper_outline.AUTHOR,
            "parts": _contents(paper_book),
            "chapters": sum(len(p.chapters) for p in paper_book.parts),
            "figures": len(paper.used_keys()),
            "pages": _pages(_newest_pdf(paper_outline.STEM)),
            "numbers": {
                "members": w("dome.members"), "panels": w("dome.panels"),
                "floorSqft": w("dome.floor_sqft"), "diameterFt": w("dome.diameter_ft"),
                "frameHours": w("hr.total"), "labourHours": w("money.labour_hours"),
                "frameUsd": w("money.frame"), "shellUsd": w("money.cost"),
                "perSqftUsd": w("money.per_sqft"),
                "unchangedPct": w("stack.unchanged_pct"),
            },
        },
        "sample": {
            "pages": _pages(teaser.latest()),
            "front": list(teaser.FRONT),
            "chapters": [{"number": c.number, "title": c.title} for c in teaser.SAMPLE],
            "ofChapters": sum(len(p.chapters) for p in paper_book.parts),
        },
        "sources": {
            "digital": "two_v_demo.book.BOOK and two_v_demo.book_tokens",
            "paperback": "wedge_book.outline.BOOK, wedge_book.tokens, wedge_book.paper.used_keys()",
            "sample": "wedge_book.teaser",
            "pages": "page count of the newest -vN PDF in deliverables/book",
        },
    }


def render() -> str:
    data = build()
    data["books"] = books()
    return json.dumps(data, indent=2) + "\n"


MARK = HERE / "client" / "public" / "mark.svg"


def mark_svg() -> str:
    """The site's logo: the dome from directly above, drawn from the mesh.

    Short struts (the spokes of the six stars) in amber, long ones in tan --
    the same colour key the campaign images use.
    """
    from two_v_demo.geometry import build_demo_geometry

    geo = build_demo_geometry()
    v = geo.vertices
    edges = [tuple(map(int, e)) for e in geo.hemisphere_edges]
    lengths = {e: float(((v[e[0]] - v[e[1]]) ** 2).sum() ** 0.5) for e in edges}
    short = min(lengths.values())
    size, pad = 64.0, 5.0
    scale = (size / 2 - pad)

    def xy(i: int) -> str:
        return f"{size / 2 + v[i][0] * scale:.2f} {size / 2 - v[i][1] * scale:.2f}"

    lines = []
    for e in sorted(edges, key=lambda e: abs(lengths[e] - short) < 1e-6):
        colour = "#FFB13E" if abs(lengths[e] - short) < 1e-6 else "#D9B98C"
        lines.append(f'<path d="M{xy(e[0])} L{xy(e[1])}" stroke="{colour}"/>')
    return (
        f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {size:.0f} {size:.0f}">'
        f'<circle cx="32" cy="32" r="32" fill="#0B1522"/>'
        f'<g stroke-width="2.2" stroke-linecap="round" fill="none">{"".join(lines)}</g>'
        "</svg>\n"
    )


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--check", action="store_true")
    args = parser.parse_args(argv)
    outputs = {OUT: render(), MARK: mark_svg()}
    if args.check:
        stale = [p for p, text in outputs.items()
                 if not p.exists() or p.read_text(encoding="utf-8") != text]
        for p in stale:
            print(f"{p.relative_to(HERE)} is stale: run py -3.12 export_facts.py", file=sys.stderr)
        if stale:
            return 1
        print("facts.json and mark.svg match the model")
        return 0
    for path, text in outputs.items():
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(text, encoding="utf-8")
        print(path.relative_to(HERE))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
