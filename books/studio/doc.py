"""A book as pages of frames: the Book Studio's layout document.

Every layout book is one ``layout.json`` in ``books/<slug>/``::

    page     the trim (inches), the margin guides, the bleed and the paper colour
    styles   named text styles: font, size (pt), leading, colour, alignment, weight
    pages    in order; each a list of frames, back to front:
               text   its words (paragraphs split by a blank line, **bold**, *italic*, and
                      numbers as {{tokens}} the book's own token table fills), and a style
               image  an asset (``assets/...``) and how it fits its frame: cover or contain
               shape  a filled, stroked rectangle or ellipse

Frames are placed in inches from the page's top-left corner. Everything the studio's page does
and everything the DeepSeek agent does goes through :data:`OPS`, so the two can never make a
document the other cannot read. Every save keeps the previous copy in ``.versions/``, and a book
prints to a new numbered PDF in the library (it never overwrites one).
"""

from __future__ import annotations

import copy
import datetime as dt
import html
import json
import re
import uuid
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
BOOKS = ROOT / "books"
SCHEMA = 1
KINDS = ("text", "image", "shape")
FITS = ("cover", "contain", "fill")
ALIGNS = ("left", "center", "right", "justify")

DEFAULT_STYLES = {
    "body": {"font": "Georgia", "size": 12, "leading": 1.4, "colour": "#2c1e14", "align": "left", "weight": 400, "italic": False},
    "title": {"font": "Rockwell Extra Bold", "size": 36, "leading": 1.1, "colour": "#964818", "align": "center", "weight": 800, "italic": False},
    "heading": {"font": "Rockwell", "size": 20, "leading": 1.2, "colour": "#964818", "align": "left", "weight": 700, "italic": False},
    "caption": {"font": "Georgia", "size": 9, "leading": 1.3, "colour": "#6e5c48", "align": "left", "weight": 400, "italic": True},
    "folio": {"font": "Georgia", "size": 9, "leading": 1, "colour": "#8c7860", "align": "center", "weight": 400, "italic": False},
}


def path(slug: str) -> Path:
    if not re.fullmatch(r"[a-z0-9][a-z0-9-]*", slug):
        raise ValueError(f"not a book slug: {slug!r}")
    return BOOKS / slug / "layout.json"


def layouts() -> list[str]:
    return sorted(p.parent.name for p in BOOKS.glob("*/layout.json"))


def new_id(prefix: str) -> str:
    return f"{prefix}{uuid.uuid4().hex[:8]}"


def new(title: str, w: float = 8.5, h: float = 11.0, pages: int = 1) -> dict:
    doc = {"schema": SCHEMA, "title": title, "page": {"w": w, "h": h, "margin": 0.6, "bleed": 0.125, "paper": "#ffffff"},
           "styles": copy.deepcopy(DEFAULT_STYLES), "pages": []}
    for _ in range(pages):
        doc["pages"].append({"id": new_id("p"), "name": "", "frames": []})
    return doc


def validate(doc: dict) -> dict:
    """The shape every reader of the format relies on; raises ValueError on anything else."""
    if doc.get("schema") != SCHEMA:
        raise ValueError("not a version-1 layout")
    pg = doc.get("page") or {}
    for k in ("w", "h"):
        if not isinstance(pg.get(k), (int, float)) or not 1 <= pg[k] <= 40:
            raise ValueError(f"page.{k} must be 1 to 40 inches")
    ids = set()
    for p in doc.get("pages", []):
        if p.get("id") in ids:
            raise ValueError(f"two pages called {p.get('id')}")
        ids.add(p["id"])
        for f in p.get("frames", []):
            if f.get("kind") not in KINDS:
                raise ValueError(f"frame {f.get('id')}: kind must be one of {KINDS}")
            for k in ("x", "y", "w", "h"):
                if not isinstance(f.get(k), (int, float)):
                    raise ValueError(f"frame {f.get('id')}: {k} must be a number")
            if f["kind"] == "text" and f.get("style") not in doc["styles"]:
                raise ValueError(f"frame {f['id']}: no style {f.get('style')!r}")
    return doc


def load(slug: str) -> dict:
    return validate(json.loads(path(slug).read_text(encoding="utf-8")))


def save(slug: str, doc: dict) -> Path:
    validate(doc)
    p = path(slug)
    p.parent.mkdir(parents=True, exist_ok=True)
    if p.exists():
        keep = p.parent / ".versions"
        keep.mkdir(exist_ok=True)
        stamp = dt.datetime.now().strftime("%Y%m%d-%H%M%S")
        (keep / f"layout-{stamp}.json").write_bytes(p.read_bytes())
    p.write_text(json.dumps(doc, indent=1, ensure_ascii=False) + "\n", encoding="utf-8")
    return p


# ----------------------------------------------------------------------
# Operations: the only ways a document changes
# ----------------------------------------------------------------------

def _page(doc: dict, page: str | int) -> dict:
    pages = doc["pages"]
    if isinstance(page, int) or (isinstance(page, str) and page.isdigit()):
        i = int(page) - 1                         # pages are numbered from 1 for people
        if not 0 <= i < len(pages):
            raise ValueError(f"no page {page}: the book has {len(pages)}")
        return pages[i]
    for p in pages:
        if p["id"] == page:
            return p
    raise ValueError(f"no page {page!r}")


def _frame(doc: dict, frame: str) -> tuple[dict, dict]:
    for p in doc["pages"]:
        for f in p["frames"]:
            if f["id"] == frame:
                return p, f
    raise ValueError(f"no frame {frame!r}")


FRAME_FIELDS = {"x", "y", "w", "h", "rot", "text", "style", "src", "fit", "fill", "stroke", "strokeW", "opacity", "shape", "locked", "name", "radius", "focus"}


def op_add_page(doc, after: int | None = None, name: str = "", copy_of: str | int | None = None):
    pg = {"id": new_id("p"), "name": name, "frames": []}
    if copy_of is not None:
        src = _page(doc, copy_of)
        pg["frames"] = [{**copy.deepcopy(f), "id": new_id("f")} for f in src["frames"]]
        pg["name"] = name or (src.get("name", "") + " (copy)").strip()
    at = len(doc["pages"]) if after is None else max(0, min(len(doc["pages"]), int(after)))
    doc["pages"].insert(at, pg)
    return {"page": pg["id"], "number": at + 1}


def op_delete_page(doc, page):
    p = _page(doc, page)
    doc["pages"].remove(p)
    return {"deleted": p["id"]}


def op_move_page(doc, page, to: int):
    p = _page(doc, page)
    doc["pages"].remove(p)
    doc["pages"].insert(max(0, min(len(doc["pages"]), int(to) - 1)), p)
    return {"page": p["id"], "number": doc["pages"].index(p) + 1}


def op_rename_page(doc, page, name: str):
    _page(doc, page)["name"] = str(name)
    return {}


def op_add_frame(doc, page, kind: str, x: float, y: float, w: float, h: float, **fields):
    if kind not in KINDS:
        raise ValueError(f"kind must be one of {KINDS}")
    f = {"id": new_id("f"), "kind": kind, "x": float(x), "y": float(y), "w": float(w), "h": float(h), "rot": 0}
    if kind == "text":
        f.update(text="", style="body")
    elif kind == "image":
        f.update(src="", fit="cover")
    else:
        f.update(shape="rect", fill="#e8dcc0", stroke="", strokeW=0)
    for k, v in fields.items():
        if k in FRAME_FIELDS:
            f[k] = v
    if kind == "text" and f["style"] not in doc["styles"]:
        raise ValueError(f"no style {f['style']!r}")
    _page(doc, page)["frames"].append(f)
    return {"frame": f["id"]}


def op_update_frame(doc, frame, **fields):
    _p, f = _frame(doc, frame)
    for k, v in fields.items():
        if k not in FRAME_FIELDS:
            raise ValueError(f"a frame has no {k!r}")
        if k == "style" and v not in doc["styles"]:
            raise ValueError(f"no style {v!r}")
        if k in ("x", "y", "w", "h", "rot", "opacity", "strokeW", "radius"):
            v = float(v)
        f[k] = v
    return {}


def op_delete_frame(doc, frame):
    p, f = _frame(doc, frame)
    p["frames"].remove(f)
    return {}


def op_arrange(doc, frame, to: str):
    """Bring a frame to the front, send it to the back, or one step either way."""
    p, f = _frame(doc, frame)
    fs = p["frames"]
    i = fs.index(f)
    fs.pop(i)
    j = {"front": len(fs), "back": 0, "forward": min(len(fs), i + 1), "backward": max(0, i - 1)}[to]
    fs.insert(j, f)
    return {}


def op_set_style(doc, name: str, **fields):
    st = doc["styles"].setdefault(name, copy.deepcopy(DEFAULT_STYLES["body"]))
    for k, v in fields.items():
        if k not in DEFAULT_STYLES["body"]:
            raise ValueError(f"a style has no {k!r}")
        st[k] = v
    return {}


def op_set_page_size(doc, w: float | None = None, h: float | None = None, margin: float | None = None, paper: str | None = None):
    pg = doc["page"]
    for k, v in (("w", w), ("h", h), ("margin", margin), ("paper", paper)):
        if v is not None:
            pg[k] = float(v) if k != "paper" else str(v)
    return {}


def op_find_replace(doc, find: str, replace: str, regex: bool = False):
    if not find:
        raise ValueError("nothing to find")
    n = 0
    pat = re.compile(find if regex else re.escape(find))
    for p in doc["pages"]:
        for f in p["frames"]:
            if f["kind"] == "text" and f.get("text"):
                f["text"], k = pat.subn(replace, f["text"])
                n += k
    return {"replaced": n}


def op_set_title(doc, title: str):
    doc["title"] = str(title)
    return {}


OPS = {
    "add_page": op_add_page, "delete_page": op_delete_page, "move_page": op_move_page, "rename_page": op_rename_page,
    "add_frame": op_add_frame, "update_frame": op_update_frame, "delete_frame": op_delete_frame, "arrange": op_arrange,
    "set_style": op_set_style, "set_page_size": op_set_page_size, "find_replace": op_find_replace, "set_title": op_set_title,
}


def apply(doc: dict, op: str, args: dict) -> dict:
    """Run one operation on a document (in place) and check what it left."""
    if op not in OPS:
        raise ValueError(f"no operation {op!r}")
    result = OPS[op](doc, **(args or {}))
    validate(doc)
    return result


def outline(doc: dict) -> str:
    """The document in a few lines per page, for the agent to read."""
    pg = doc["page"]
    out = [f"{doc['title']}: {len(doc['pages'])} pages, {pg['w']} x {pg['h']} in, margin {pg.get('margin', 0)} in",
           "styles: " + ", ".join(f"{k} ({v['font']} {v['size']}pt)" for k, v in doc["styles"].items())]
    for i, p in enumerate(doc["pages"], 1):
        out.append(f"page {i} [{p['id']}] {p.get('name', '')}")
        for f in p["frames"]:
            box = f"at {f['x']:.2f},{f['y']:.2f} size {f['w']:.2f}x{f['h']:.2f}"
            if f["kind"] == "text":
                t = f.get("text", "").replace("\n", " / ")
                out.append(f"  text [{f['id']}] {box} style={f['style']}: {t[:160]}{'...' if len(t) > 160 else ''}")
            elif f["kind"] == "image":
                out.append(f"  image [{f['id']}] {box} src={f.get('src') or '(empty)'} fit={f.get('fit')}")
            else:
                out.append(f"  shape [{f['id']}] {box} {f.get('shape')} fill={f.get('fill')}")
    return "\n".join(out)


# ----------------------------------------------------------------------
# Rendering: one HTML page per book page, for the studio and the printer
# ----------------------------------------------------------------------

def _tokens():
    try:
        from wedge_book import tokens
        return tokens
    except Exception:          # the studio still opens without the book's token table
        return None


def fill_tokens(text: str) -> str:
    t = _tokens()
    return t.resolve(text, strict=False) if t and "{{" in text else text


def _inline(s: str) -> str:
    s = html.escape(s)
    s = re.sub(r"\*\*(.+?)\*\*", r"<b>\1</b>", s)
    s = re.sub(r"\*(.+?)\*", r"<i>\1</i>", s)
    return s


def text_html(text: str) -> str:
    paras = re.split(r"\n\s*\n", fill_tokens(text or "").strip())
    return "".join(f"<p>{'<br>'.join(_inline(line) for line in p.splitlines())}</p>" for p in paras if p.strip())


def font_stack(font: str) -> str:
    """A style's font, or a comma-separated list of fallbacks, as CSS."""
    return ",".join(f"'{f.strip()}'" for f in str(font).split(",") if f.strip()) + ",serif"


def style_css(st: dict) -> str:
    return (f"font-family:{font_stack(st['font'])};font-size:{st['size']}pt;line-height:{st['leading']};color:{st['colour']};"
            f"text-align:{st['align']};font-weight:{st['weight']};font-style:{'italic' if st.get('italic') else 'normal'}")


def frame_html(doc: dict, f: dict, src_url) -> str:
    box = (f"left:{f['x']}in;top:{f['y']}in;width:{f['w']}in;height:{f['h']}in;"
           f"transform:rotate({f.get('rot', 0)}deg);opacity:{f.get('opacity', 1)}")
    if f["kind"] == "text":
        return f'<div class="fr text" style="{box};{style_css(doc["styles"][f["style"]])}">{text_html(f.get("text", ""))}</div>'
    if f["kind"] == "image":
        if not f.get("src"):
            return f'<div class="fr image empty" style="{box}"></div>'
        fit = {"cover": "cover", "contain": "contain", "fill": "fill"}.get(f.get("fit", "cover"), "cover")
        pos = f.get("focus") or "50% 50%"
        return f'<div class="fr image" style="{box}"><img src="{html.escape(src_url(f["src"]))}" style="object-fit:{fit};object-position:{pos}"></div>'
    radius = "50%" if f.get("shape") == "ellipse" else f"{f.get('radius', 0)}in"
    stroke = f"border:{f.get('strokeW', 0)}pt solid {f.get('stroke') or 'transparent'};" if f.get("strokeW") else ""
    return f'<div class="fr shape" style="{box};background:{f.get("fill") or "transparent"};border-radius:{radius};{stroke}"></div>'


def page_css(doc: dict) -> str:
    pg = doc["page"]
    return f"""
@page {{ size: {pg['w']}in {pg['h']}in; margin: 0 }}
* {{ box-sizing: border-box }}
html, body {{ margin: 0; padding: 0 }}
.page {{ position: relative; width: {pg['w']}in; height: {pg['h']}in; overflow: hidden; background: {pg.get('paper', '#fff')};
         page-break-after: always; break-after: page }}
.fr {{ position: absolute; transform-origin: center }}
.fr.text p {{ margin: 0 0 0.6em }}
.fr.text p:last-child {{ margin-bottom: 0 }}
.fr.image img {{ width: 100%; height: 100%; display: block }}
"""


def render_html(doc: dict, src_url=lambda s: "/file/" + s, pages: list[int] | None = None) -> str:
    chosen = [p for i, p in enumerate(doc["pages"], 1) if pages is None or i in pages]
    body = "".join(f'<section class="page">{"".join(frame_html(doc, f, src_url) for f in p["frames"])}</section>' for p in chosen)
    return (f'<!doctype html><html><head><meta charset="utf-8"><title>{html.escape(doc["title"])}</title>'
            f"<style>{page_css(doc)}</style></head><body>{body}</body></html>")


def export_pdf(slug: str, doc: dict | None = None) -> Path:
    """Print the book through a real browser to a new numbered PDF in the library."""
    from two_v_demo import book_export
    from two_v_demo.deliverables import next_version_path

    doc = doc or load(slug)
    chrome = book_export._chrome_path()
    if not chrome:
        raise RuntimeError("no headless Chrome or Edge on this machine to print with")
    page = render_html(doc, src_url=lambda s: (ROOT / s).resolve().as_uri())
    out = next_version_path(ROOT / "deliverables" / "book" / f"{slug}-layout.pdf")
    out.parent.mkdir(parents=True, exist_ok=True)
    book_export._pdf_via_chrome(page, out, chrome)
    return out


# ----------------------------------------------------------------------
# Importers
# ----------------------------------------------------------------------

def import_kids_book() -> dict:
    """My Own Home, My Own Dome as a layout: the same pages kids_book.build prints, as frames."""
    import assetlib
    from kids_book import build as kb
    from wedge_book import outline as wo

    title, verses = kb.stanzas()
    side = kb.TRIM_IN
    m = side * kb.MARGIN / kb.PAGE
    pic_h = side * kb.PICTURE_H / kb.PAGE
    doc = new(title, side, side, 0)
    doc["page"].update(margin=round(m, 3), paper="#faf4e6")
    doc["styles"].update({
        "verse": {"font": "Bookman Old Style", "size": 20, "leading": 1.42, "colour": "#2c1e14", "align": "left", "weight": 400, "italic": False},
        "title": {"font": "Rockwell Extra Bold, Rockwell", "size": 40, "leading": 1.05, "colour": "#fff4de", "align": "center", "weight": 800, "italic": False},
        "title-dark": {"font": "Rockwell Extra Bold, Rockwell", "size": 34, "leading": 1.1, "colour": "#964818", "align": "center", "weight": 800, "italic": False},
        "byline": {"font": "Bookman Old Style", "size": 14, "leading": 1.3, "colour": "#2c1e14", "align": "center", "weight": 400, "italic": False},
        "cover-byline": {"font": "Bookman Old Style", "size": 13, "leading": 1.3, "colour": "#ffecc8", "align": "center", "weight": 700, "italic": False},
        "small": {"font": "Bookman Old Style", "size": 9, "leading": 1.5, "colour": "#6e5c48", "align": "center", "weight": 400, "italic": False},
        "end": {"font": "Bookman Old Style", "size": 13, "leading": 1.45, "colour": "#2c1e14", "align": "left", "weight": 400, "italic": False},
    })
    doc["styles"]["folio"]["font"] = "Bookman Old Style"
    pic = lambda k: assetlib.image(kb.NAMES[k]).relative_to(ROOT).as_posix()

    def page(name, frames):
        p = {"id": new_id("p"), "name": name, "frames": []}
        doc["pages"].append(p)
        for f in frames:
            kind = f.pop("kind")
            op_add_frame(doc, p["id"], kind, **f)
        return p

    head, tail = title.split(",", 1) if "," in title else (title, "")
    page("Cover", [
        dict(kind="image", x=0, y=0, w=side, h=side, src=pic("cover"), fit="cover", name="cover picture"),
        dict(kind="shape", x=0, y=0, w=side, h=side * 0.36, fill="rgba(18,12,8,0.45)", name="title shade"),
        dict(kind="text", x=0.4, y=0.5, w=side - 0.8, h=1.9, text=f"{head},\n{tail.strip()}", style="title", name="title"),
        dict(kind="shape", x=0, y=side * 0.905, w=side, h=side * 0.095, fill="rgba(18,12,8,0.6)", name="byline band"),
        dict(kind="text", x=0.4, y=side * 0.925, w=side - 0.8, h=0.4, text=f"A rhyming picture book  ·  {wo.AUTHOR}", style="cover-byline", name="byline"),
    ])
    page("Title page", [
        dict(kind="text", x=m, y=side * 0.30, w=side - 2 * m, h=1.2, text=title, style="title-dark"),
        dict(kind="text", x=m, y=side * 0.45, w=side - 2 * m, h=0.9, text=f"written by\n\n**{wo.AUTHOR}**", style="byline"),
        dict(kind="text", x=m, y=side * 0.78, w=side - 2 * m, h=1.1, style="small",
             text=f"Every picture is drawn in the same world as the grown-ups' book,\n{wo.TITLE}: the same dome, the same log, the same saw.\n"
                  f"Copyright © 2026 {wo.AUTHOR}.  zeanahlab.com/kids"),
    ])
    for i, verse in enumerate(verses, 1):
        page(f"Spread {i}", [
            dict(kind="image", x=0, y=0, w=side, h=pic_h, src=pic(str(i)), fit="cover", name="picture"),
            dict(kind="shape", x=0, y=pic_h - 0.01, w=side, h=0.03, fill="#784e2e", name="rule"),
            dict(kind="text", x=m, y=pic_h + 0.2, w=side - 2 * m, h=side - pic_h - 0.75, text=kb._typeset(verse), style="verse", name="verse"),
            dict(kind="text", x=0, y=side - 0.45, w=side, h=0.3, text=str(i), style="folio", name="folio"),
        ])
    page("For the grown-ups", [
        dict(kind="text", x=m, y=m, w=side - 2 * m, h=0.8, text=kb.NUMBERS_HEAD, style="heading"),
        dict(kind="text", x=m, y=m + 0.95, w=side - 2 * m, h=side - 2 * m - 0.95, text="\n\n".join(kb._typeset(p) for p in kb.numbers_text()), style="end"),
    ])
    doc["styles"]["heading"].update(font="Rockwell Extra Bold, Rockwell", size=24)
    doc["source"] = {"imported_from": "kids_book.build", "verse": kb.VERSE.relative_to(ROOT).as_posix(),
                     "note": "The verse and pictures were the kids_book engine's; edits here are the layout's own."}
    return validate(doc)


IMPORTERS = {"my-own-home-my-own-dome": import_kids_book}
