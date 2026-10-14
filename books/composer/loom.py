"""A book as a loom: threads (perspectives) woven through levels (depths).

Every book the composer makes is one ``loom.json`` in ``books/<slug>/``::

    threads   the perspectives, or subjects, that run through the whole book
              (the tree, the split ... ; or for a children's book, the characters)
    levels    the depths, in order, each one unlocked by the last: by default
              Story -> Theory -> Working template -> Steps -> Family activity.
              A level has a *gate*: what a reader can do before going on, and
              the key that proves it (an answer, a count, a stamp) -- the same
              gate in print (a page to jump to) and on screen (a lock).
    cells     where a thread meets a level: a title, a deck line, the text
              (Markdown, numbers as ``{{tokens}}``), placed pictures (frames)
              and notes. One cell is one spread of the printed book.
    links     the relations between cells -- builds-on, explains, practice-for,
              contrasts, see-also -- which the graph draws and the printed
              book turns into "see also" lines.
    paths     reading routes: an ordered walk through cells for one reader
              ("Twelve bedtimes", "Check the maths").
    notes     annotations on any cell, page or link.

The same loom prints in different weaves: down each level (``by-level``: all the
stories, then all the theory ...), up each thread (``by-thread``: the tree from
story to activity, then the split ...), or along any path. That is how one body
of material is told several ways as the understanding of it grows: write a new
level or a new thread and every weave picks it up.

The Master Edition (``master_book``) is the worked example: :func:`import_master_edition`
turns its six rungs, twelve threads, seventy-two cells and nine paths into a loom.
"""

from __future__ import annotations

import copy
import datetime as dt
import html
import json
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
BOOKS = ROOT / "books"
SCHEMA = 1

LINK_KINDS = ("builds-on", "explains", "practice-for", "contrasts", "see-also")
STATUSES = ("empty", "draft", "review", "done")

# What a new book of each kind starts with. Levels are the ladder a reader climbs.
TEMPLATES: dict[str, dict] = {
    "layered": {
        "label": "Layered book (story to theory to template to steps to family)",
        "page": {"size": "8.5in 11in", "margin": "0.6in", "body_pt": 11},
        "levels": [
            ("story", "Story", "Wonder", "Tell it as a story anyone can follow, read aloud."),
            ("theory", "Theory", "Understand", "Why it works: the idea, the shapes, the numbers."),
            ("template", "Working template", "Model", "A template to copy: a model, a drawing, a jig."),
            ("steps", "Instructional steps", "Build", "Do it for real, one numbered step at a time."),
            ("family", "Family activity", "Share", "Something a family does together with it."),
        ],
    },
    "children": {
        "label": "Children's picture book",
        "page": {"size": "8in 8in", "margin": "0.5in", "body_pt": 18},
        "levels": [
            ("read", "Read aloud", "Listen", "The story, a page at a time, read to a child."),
            ("find", "Look and find", "Notice", "Things to point at and count in each picture."),
            ("make", "Make it", "Play", "Something to make with paper, straws or blocks."),
        ],
    },
    "coloring": {
        "label": "Coloring book",
        "page": {"size": "8.5in 11in", "margin": "0.5in", "body_pt": 14},
        "levels": [
            ("color", "Color it", "Color", "A full-page drawing to color, and one line to read."),
            ("count", "Count it", "Count", "Count the triangles, the logs, the pieces."),
            ("build", "Build it", "Build", "A cut-out model of what you colored."),
        ],
    },
    "construction-kit": {
        "label": "Construction kit manual",
        "page": {"size": "8.5in 11in", "margin": "0.6in", "body_pt": 11},
        "levels": [
            ("parts", "Parts", "Check", "Every part in the box, counted and labelled."),
            ("cut", "Cut", "Cut", "The cuts, with the saw setting for each."),
            ("assemble", "Assemble", "Assemble", "Put it together, in order."),
            ("check", "Check", "Prove", "How to know it is right before going on."),
        ],
    },
}


def now() -> str:
    return dt.datetime.now().isoformat(timespec="seconds")


def slugify(text: str) -> str:
    return re.sub(r"[^a-z0-9]+", "-", text.lower()).strip("-") or "untitled"


def cell_key(level: str, thread: str) -> str:
    return f"{level}/{thread}"


# ---------------------------------------------------------------------------
# Making and keeping a loom


def new(title: str, kind: str = "layered", threads: list[str] | None = None, author: str = "") -> dict:
    t = TEMPLATES[kind]
    threads = threads or ["Thread one", "Thread two", "Thread three"]
    loom = {
        "schema": SCHEMA, "title": title, "subtitle": "", "author": author, "kind": kind,
        "created": now(), "page": dict(t["page"]),
        "threads": [{"key": slugify(n), "name": n, "idea": "", "color": PALETTE[i % len(PALETTE)]}
                    for i, n in enumerate(threads)],
        "levels": [{"key": k, "name": n, "verb": v, "promise": p, "who": "", "time": "", "need": "",
                    "gate": {"title": f"Ready for the next level?", "done_when": "", "key": ""}}
                   for k, n, v, p in t["levels"]],
        "cells": {}, "links": [], "paths": [], "notes": [],
    }
    for lv in loom["levels"]:
        for th in loom["threads"]:
            loom["cells"][cell_key(lv["key"], th["key"])] = blank_cell()
    return loom


PALETTE = ("#b0601e", "#2f5d7c", "#5b7f3a", "#8a4f9e", "#c2410c", "#0f766e", "#a16207", "#be185d",
           "#4d7c0f", "#1d4ed8", "#9f1239", "#475569")


def blank_cell() -> dict:
    return {"title": "", "deck": "", "body": "", "frames": [], "status": "empty", "source": ""}


def folder(slug: str) -> Path:
    return BOOKS / slug


def path(slug: str) -> Path:
    return folder(slug) / "loom.json"


def looms() -> list[str]:
    return sorted(p.parent.name for p in BOOKS.glob("*/loom.json"))


def load(slug: str) -> dict:
    return json.loads(path(slug).read_text(encoding="utf-8"))


def save(slug: str, loom: dict) -> Path:
    """Write the loom; the copy it replaces is kept in ``.history/`` (nothing is lost)."""
    problems = validate(loom)
    if problems:
        raise ValueError("; ".join(problems[:5]))
    p = path(slug)
    p.parent.mkdir(parents=True, exist_ok=True)
    if p.is_file():
        hist = p.parent / ".history"
        hist.mkdir(exist_ok=True)
        stamp = dt.datetime.fromtimestamp(p.stat().st_mtime).strftime("%Y%m%d-%H%M%S")
        keep = hist / f"loom-{stamp}.json"
        if not keep.exists():
            keep.write_bytes(p.read_bytes())
    loom = dict(loom, saved=now())
    p.write_text(json.dumps(loom, indent=1, ensure_ascii=False) + "\n", encoding="utf-8")
    return p


def validate(loom: dict) -> list[str]:
    out = []
    if loom.get("schema") != SCHEMA:
        out.append("unknown schema")
    tk = [t["key"] for t in loom.get("threads", [])]
    lk = [lv["key"] for lv in loom.get("levels", [])]
    if len(set(tk)) != len(tk):
        out.append("two threads share a key")
    if len(set(lk)) != len(lk):
        out.append("two levels share a key")
    cells = loom.get("cells", {})
    for key in cells:
        lv, _, th = key.partition("/")
        if lv not in lk or th not in tk:
            out.append(f"cell {key} has no level or thread")
    for link in loom.get("links", []):
        if link.get("from") not in cells or link.get("to") not in cells:
            out.append(f"link {link.get('from')} -> {link.get('to')} names a missing cell")
        if link.get("kind") not in LINK_KINDS:
            out.append(f"link kind {link.get('kind')!r} is not one of {', '.join(LINK_KINDS)}")
    for pth in loom.get("paths", []):
        for stop in pth.get("stops", []):
            if stop not in cells:
                out.append(f"path {pth.get('key')} stops at a missing cell {stop}")
    return out


# ---------------------------------------------------------------------------
# Weaves: the orders a loom can be read in


def weave(loom: dict, order: str = "by-level") -> list[str]:
    """Cell keys in reading order. ``by-level``, ``by-thread``, or a path's key."""
    lv = [x["key"] for x in loom["levels"]]
    th = [x["key"] for x in loom["threads"]]
    cells = loom["cells"]
    if order == "by-level":
        return [cell_key(a, b) for a in lv for b in th if cell_key(a, b) in cells]
    if order == "by-thread":
        return [cell_key(a, b) for b in th for a in lv if cell_key(a, b) in cells]
    for p in loom.get("paths", []):
        if p["key"] == order:
            return [s for s in p["stops"] if s in cells]
    raise KeyError(f"no weave or path called {order!r}")


def neighbours(loom: dict, key: str) -> dict:
    """The way down (previous level, same thread), the way up, and the links out."""
    lv = [x["key"] for x in loom["levels"]]
    level, _, thread = key.partition("/")
    i = lv.index(level)
    down = cell_key(lv[i - 1], thread) if i > 0 else None
    up = cell_key(lv[i + 1], thread) if i + 1 < len(lv) else None
    links = [l for l in loom.get("links", []) if l["from"] == key]
    return {"down": down if down in loom["cells"] else None,
            "up": up if up in loom["cells"] else None, "links": links}


# ---------------------------------------------------------------------------
# Printing


def _tokens(text: str) -> str:
    if "{{" not in text:
        return text
    try:
        from square_book import tokens as sq
        return sq.resolve(text)
    except Exception:          # noqa: BLE001 -- a token the engines do not know prints as written
        return text


def _md(text: str) -> str:
    """Markdown to HTML with the books' own ``:::box`` asides (the shared converter)."""
    import markdown

    from two_v_demo.book_export import _boxes
    return markdown.markdown(_boxes(_tokens(text)), extensions=["tables", "sane_lists", "smarty"],
                             output_format="html5")


def _asset_src(name: str) -> str:
    """An asset by catalogue name (``wedge-method-cover``, ``name@3``) or by path."""
    p = Path(name)
    if not p.is_absolute():
        try:
            import assetlib
            base, _, ver = name.partition("@")
            p = assetlib.image(base, int(ver) if ver else None)
        except (KeyError, ImportError, ValueError):
            p = ROOT / name
    return p.resolve().as_uri() if p.is_file() else ""


def _frame_html(f: dict, kind: str) -> str:
    style = (f"left:{f.get('x', 0)}%;top:{f.get('y', 0)}%;width:{f.get('w', 30)}%;"
             f"height:{f.get('h', 30)}%;")
    if f.get("type") == "text":
        return f'<div class="frame text" style="{style}">{_md(f.get("text", ""))}</div>'
    src = _asset_src(f.get("asset", ""))
    if not src:
        return f'<div class="frame missing" style="{style}">missing picture: {html.escape(f.get("asset", ""))}</div>'
    line = " lineart" if f.get("lineart") or kind == "coloring" else ""
    cap = f'<figcaption>{html.escape(f["caption"])}</figcaption>' if f.get("caption") else ""
    return f'<figure class="frame{line}" style="{style}"><img src="{src}">{cap}</figure>'


def render_html(loom: dict, order: str = "by-level") -> str:
    """The whole book as one paged HTML document, in the weave asked for."""
    E = html.escape
    lv = {x["key"]: x for x in loom["levels"]}
    th = {x["key"]: x for x in loom["threads"]}
    keys = weave(loom, order)
    anchor = {k: "c-" + k.replace("/", "-") for k in keys}
    page = loom.get("page", {})
    parts = [f"<section class='title'><h1>{E(loom['title'])}</h1><p class='sub'>{E(loom.get('subtitle', ''))}</p>"
             f"<p class='by'>{E(loom.get('author', ''))}</p></section>"]
    # How to read this book: the grid, every cell a link.
    grid = ["<table class='grid'><tr><th></th>" + "".join(f"<th style='color:{t['color']}'>{E(t['name'])}</th>"
                                                       for t in loom["threads"]) + "</tr>"]
    for level in loom["levels"]:
        row = [f"<th>{E(level['name'])}</th>"]
        for t in loom["threads"]:
            k = cell_key(level["key"], t["key"])
            c = loom["cells"].get(k)
            if c and k in anchor:
                row.append(f"<td><a href='#{anchor[k]}'>{E(c.get('title') or '·')}</a></td>")
            elif c:
                row.append(f"<td class='off'>{E(c.get('title') or '')}</td>")   # not in this weave
            else:
                row.append("<td></td>")
        grid.append("<tr>" + "".join(row) + "</tr>")
    grid.append("</table>")
    ways = {"by-level": "down each level", "by-thread": "up each thread"}
    parts.append(f"<section class='how'><h2>How to read this book</h2><p>This printing goes "
                 f"{E(ways.get(order, 'along the path ' + order))}. Every square below is a chapter: "
                 f"across is a perspective, down is a level. Climb a column to follow one idea from story "
                 f"to activity; read a row to have the whole thing at one depth.</p>{''.join(grid)}</section>")
    last_level = None
    for k in keys:
        level_key, _, thread_key = k.partition("/")
        level, thread, c = lv[level_key], th[thread_key], loom["cells"][k]
        if order == "by-level" and level_key != last_level:
            if last_level is not None:
                parts.append(_gate_html(lv[last_level], level))
            parts.append(f"<section class='level'><p class='n'>Level {list(lv).index(level_key) + 1}</p>"
                         f"<h2>{E(level['name'])}</h2><p>{E(level.get('promise', ''))}</p>"
                         + (f"<p class='meta'>For: {E(level['who'])}</p>" if level.get("who") else "")
                         + "</section>")
            last_level = level_key
        nb = neighbours(loom, k)
        nav = []
        if nb["down"] and nb["down"] in anchor:
            nav.append(f"<a href='#{anchor[nb['down']]}'>&darr; {E(loom['cells'][nb['down']].get('title', ''))}</a>")
        if nb["up"] and nb["up"] in anchor:
            nav.append(f"<a href='#{anchor[nb['up']]}'>&uarr; {E(loom['cells'][nb['up']].get('title', ''))}</a>")
        for link in nb["links"]:
            if link["to"] in anchor:
                nav.append(f"<a href='#{anchor[link['to']]}'>{E(link['kind'])}: "
                           f"{E(loom['cells'][link['to']].get('title', ''))}</a>")
        frames = "".join(_frame_html(f, loom.get("kind", "")) for f in c.get("frames", []))
        parts.append(
            f"<section class='cell' id='{anchor[k]}'>"
            f"<p class='chips'><span style='background:{thread['color']}'>{E(thread['name'])}</span>"
            f"<span class='lv'>{E(level['name'])}</span></p>"
            f"<h3>{E(c.get('title') or thread['name'])}</h3>"
            + (f"<p class='deck'>{E(c['deck'])}</p>" if c.get("deck") else "")
            + (f"<div class='stage'>{frames}</div>" if frames else "")
            + f"<div class='body'>{_md(c.get('body', ''))}</div>"
            + (f"<nav>{' &middot; '.join(nav)}</nav>" if nav else "") + "</section>")
    css = _css(page, loom.get("kind", "layered"))
    return (f"<!doctype html><html><head><meta charset='utf-8'><title>{E(loom['title'])}</title>"
            f"<style>{css}</style></head><body>{''.join(parts)}</body></html>")


def _gate_html(done: dict, nxt: dict) -> str:
    g = done.get("gate", {})
    E = html.escape
    if not (g.get("done_when") or g.get("title")):
        return ""
    key = (f"<p class='key'>Your key: <span class='blank'></span> &nbsp; (the answer opens "
           f"{E(nxt['name'])})</p>") if g.get("key") else "<p class='key'>Stamp or sign here: <span class='blank'></span></p>"
    return (f"<section class='gate'><p class='n'>Before {E(nxt['name'])}</p><h2>{E(g.get('title') or 'Ready?')}</h2>"
            f"<p>{E(g.get('done_when', ''))}</p>{key}</section>")


def _css(page: dict, kind: str) -> str:
    body = page.get("body_pt", 11)
    big = kind in ("children", "coloring")
    return f"""
@page {{ size: {page.get('size', '8.5in 11in')}; margin: {page.get('margin', '0.6in')}; }}
html, body {{ margin: 0; background: #fff; color: #1d1d1b; }}
body {{ font: {body}pt/1.45 Georgia, serif; }}
h1 {{ font: 800 {34 if big else 30}pt/1.1 "Segoe UI", sans-serif; margin: 2in 0 .2in; }}
h2 {{ font: 800 20pt "Segoe UI", sans-serif; margin: 0 0 .15in; }}
h3 {{ font: 800 {22 if big else 17}pt/1.2 "Segoe UI", sans-serif; margin: .05in 0 .08in; }}
.sub {{ font: italic 15pt Georgia, serif; }} .by {{ font: 600 13pt "Segoe UI", sans-serif; margin-top: .4in; }}
section {{ break-after: page; }}
.title, .level, .gate {{ text-align: {'center' if big else 'left'}; }}
.level {{ padding-top: 2.5in; }} .level .n, .gate .n {{ font: 700 11pt "Segoe UI"; letter-spacing: .1em; text-transform: uppercase; color: #b0601e; }}
.gate {{ padding-top: 2.5in; }} .gate .key {{ margin-top: .4in; font: 600 12pt "Segoe UI"; }}
.blank {{ display: inline-block; width: 2in; border-bottom: 1.5px solid #333; }}
.chips span {{ display: inline-block; font: 700 8pt "Segoe UI"; color: #fff; padding: 2px 8px; border-radius: 9px; margin-right: 6px; }}
.chips .lv {{ background: #444; }}
.deck {{ font: italic 12pt Georgia; color: #444; margin: 0 0 .12in; }}
.stage {{ position: relative; width: 100%; height: {'7.2in' if big else '4.2in'}; margin: .05in 0 .15in; }}
.frame {{ position: absolute; margin: 0; overflow: hidden; }}
.frame img {{ width: 100%; height: 100%; object-fit: contain; }}
.frame.lineart img {{ filter: grayscale(1) contrast(4) brightness(1.4); }}
.frame figcaption {{ font: 8pt "Segoe UI"; color: #555; }}
.frame.text {{ font-size: {body}pt; }} .frame.missing {{ border: 1px dashed #c00; color: #c00; font: 8pt sans-serif; }}
nav {{ margin-top: .2in; padding-top: .06in; border-top: 1px solid #ddd; font: 9pt "Segoe UI"; }}
nav a, .grid a {{ color: #2f5d7c; text-decoration: none; }}
.grid {{ border-collapse: collapse; width: 100%; font: 8pt/1.25 "Segoe UI"; }}
.grid th, .grid td {{ border: .5px solid #ddd; padding: 3px; vertical-align: top; }}
.body img {{ max-width: 100%; }}
.grid td.off {{ color: #999; }}
aside.box {{ border: 1px solid #d8d2c8; border-left: 4px solid #b0601e; background: #faf6f0; padding: .08in .14in;
  margin: .12in 0; break-inside: avoid; }}
aside.box .box-label {{ font: 800 8.5pt "Segoe UI", sans-serif; text-transform: uppercase; letter-spacing: .06em;
  color: #b0601e; margin-bottom: .04in; }}
aside.box-against {{ border-left-color: #9f1239; }} aside.box-correction {{ border-left-color: #c2410c; }}
"""


def export_pdf(loom: dict, order: str = "by-level", slug: str | None = None) -> Path:
    """Print the loom in a weave to a new numbered PDF in the library."""
    import tempfile

    import medialib
    from two_v_demo import book_export

    name = f"{slug or slugify(loom['title'])}-{order}.pdf"
    out = medialib.new_path(name)
    with tempfile.TemporaryDirectory() as scratch:
        tmp = Path(scratch) / "book.pdf"
        book_export._pdf_via_chrome(render_html(loom, order), tmp, book_export._chrome_path())
        out.write_bytes(tmp.read_bytes())
    medialib.write_index()
    return out


# ---------------------------------------------------------------------------
# Bringing existing books in


def import_master_edition() -> dict:
    """The Master Edition's rungs, threads, cells and paths as a loom: the worked example."""
    from master_book import outline as o

    loom = {
        "schema": SCHEMA, "title": o.TITLE, "subtitle": o.SUBTITLE, "author": o.AUTHOR, "kind": "layered",
        "created": now(), "page": dict(TEMPLATES["layered"]["page"]),
        "threads": [{"key": t.key, "name": t.name, "idea": t.idea, "color": PALETTE[i % len(PALETTE)]}
                    for i, t in enumerate(o.THREADS)],
        "levels": [], "cells": {}, "links": [], "paths": [], "notes": [],
        "source": "master_book.outline (imported; the engine's own build still prints the Master Edition)",
    }
    for r in o.RUNGS:
        gate = r.milestones[-1] if r.milestones else None
        loom["levels"].append({
            "key": r.key, "name": r.title, "verb": r.verb, "promise": r.promise, "who": r.who,
            "time": r.time, "need": r.need,
            "gate": {"title": gate.title if gate else "Ready?", "done_when": gate.done_when if gate else r.ready,
                     "key": ""},
            "milestones": [{"key": m.key, "title": m.title, "who": m.who, "time": m.time, "need": m.need,
                            "done_when": m.done_when} for m in r.milestones]})
    rung_key = {r.number: r.key for r in o.RUNGS}
    for c in o.CELLS:
        body = c.path.read_text(encoding="utf-8") if c.path.is_file() else ""
        loom["cells"][cell_key(rung_key[c.rung], c.thread)] = {
            "title": c.title, "deck": c.deck, "body": body, "frames": [],
            "status": "done" if body.strip() else "empty",
            "source": c.path.relative_to(ROOT).as_posix() if c.path.is_file() else "",
            "refs": {"complete_edition": list(c.vol_a), "paperback": list(c.vol_b)}}
    # Each thread builds on itself, level to level.
    order = [r.key for r in o.RUNGS]
    for t in o.THREADS:
        for a, b in zip(order, order[1:]):
            loom["links"].append({"from": cell_key(b, t.key), "to": cell_key(a, t.key), "kind": "builds-on",
                                  "note": ""})
    for p in o.PATHS:
        stops = []
        for s in p.stops:
            m = re.fullmatch(r"r(\d)-(\w+)", s)
            if m:
                stops.append(cell_key(rung_key[int(m.group(1))], m.group(2)))
        loom["paths"].append({"key": p.key, "title": p.title, "who": p.who, "stops": stops,
                              "outside_stops": [s for s in p.stops if not re.fullmatch(r"r\d-\w+", s)]})
    return loom


def import_folder(title: str, manuscript: Path, kind: str = "layered") -> dict:
    """A plain folder of Markdown chapters, each one a cell on the first level, one thread each --
    a start from which to weave the other levels in."""
    files = sorted(Path(manuscript).glob("*.md"))
    loom = new(title, kind, threads=[f.stem.split("-", 1)[-1].replace("-", " ").title() for f in files] or None)
    first = loom["levels"][0]["key"]
    for f, t in zip(files, loom["threads"]):
        text = f.read_text(encoding="utf-8")
        head = next((l.lstrip("# ").strip() for l in text.splitlines() if l.startswith("#")), t["name"])
        loom["cells"][cell_key(first, t["key"])].update(title=head, body=text, status="draft",
                                                         source=f.resolve().relative_to(ROOT).as_posix()
                                                         if f.resolve().is_relative_to(ROOT) else str(f))
    return loom


def selftest() -> None:
    lm = new("Test", "children", ["Pip", "Moss"])
    assert len(lm["cells"]) == 6 and not validate(lm)
    k = cell_key("read", "pip")
    lm["cells"][k].update(title="Pip finds a log", body="Pip sees **8** wedges.")
    lm["links"].append({"from": cell_key("find", "pip"), "to": k, "kind": "practice-for", "note": ""})
    lm["paths"].append({"key": "pip", "title": "Pip's way", "who": "", "stops": [k, cell_key("make", "pip")]})
    assert not validate(lm)
    assert weave(lm, "by-thread")[:3] == ["read/pip", "find/pip", "make/pip"]
    assert weave(lm, "by-level")[:2] == ["read/pip", "read/moss"]
    assert weave(lm, "pip") == [k, "make/pip"]
    assert neighbours(lm, "find/pip")["down"] == k
    page = render_html(lm, "by-thread")
    assert "Pip finds a log" in page and "<strong>8</strong>" in page
    bad = copy.deepcopy(lm)
    bad["links"].append({"from": "x/y", "to": k, "kind": "nope"})
    assert len(validate(bad)) == 2
    me = import_master_edition()
    assert len(me["levels"]) == 6 and len(me["threads"]) == 12 and len(me["cells"]) == 72, \
        (len(me["levels"]), len(me["threads"]), len(me["cells"]))
    assert not validate(me), validate(me)[:3]
    assert weave(me, "bedtime")[0].endswith("/tree")
    printed = render_html(me, "bedtime")
    assert ":::box" not in printed and "class=\"box box-" in printed, "the books' boxes must print as boxes"
    print("loom selftest: ok")


if __name__ == "__main__":
    selftest()
