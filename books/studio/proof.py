"""The Proof Desk: a manuscript book's finished PDF, page by page, to read, mark up, fix and certify.

What it reads is the file Amazon will read: the newest numbered PDF in the library (or any earlier
one), never a second typesetting of it. For every page it gives

* the page drawn (pymupdf), cached by file and size;
* its text, its measured content box and margins -- inside and outside by which side of the spread
  the page falls on -- and the pictures on it with their effective resolution;
* the manuscript chapter the page's words come from, found by searching the book's own Markdown,
  so a fix goes into the source and the book's own build prints the next copy;

and for the whole file a KDP preflight (books.studio.kdp_rules, with wedge_book.kdp's own file
checks), notes pinned to pages (``books/<book>/proof/annotations.json``, carried onto later builds
by their words), the pages that changed between two builds, and a certificate when it passes:
the file's SHA-256, every check, every note and the rules it was held to
(``books/<book>/proof/certificates/``). A certificate never touches the library.
"""

from __future__ import annotations

import datetime as dt
import functools
import hashlib
import json
import re
import tempfile
import threading
import unicodedata
from pathlib import Path

from books.studio import kdp_rules as K
from books.studio import manuscripts as MS

ROOT = MS.ROOT
CACHE = Path(tempfile.gettempdir()) / "zl-proof-cache"
_LOCK = threading.Lock()
PT = 72.0


# ----------------------------------------------------------------------
# Books and their builds
# ----------------------------------------------------------------------

def books() -> list[dict]:
    from books import shelf as S
    return [{"key": b.key, "title": b.title, "by": b.by, "status": b.status, "build": b.build, "builds": len(builds(b.key))}
            for b in S.SHELF if b.output]


@functools.lru_cache(maxsize=32)
def _outputs(output: str, stamp: int) -> list:
    import medialib
    return medialib.outputs(output)


def builds(key: str) -> list[dict]:
    """Every numbered copy of the book that has a PDF, newest first."""
    b = MS.book(key)
    folder = ROOT / "deliverables"
    stamp = int(folder.stat().st_mtime) if folder.is_dir() else 0
    out = []
    for o in reversed(_outputs(b.output, stamp)):
        pdfs = [p for p in o.entries if p.suffix.lower() == ".pdf"]
        if not pdfs:
            continue
        p = max(pdfs, key=lambda q: q.stat().st_size)
        out.append({"build": o.folder.name, "version": o.version, "pdf": p.relative_to(ROOT).as_posix(), "bytes": p.stat().st_size,
                    "made": dt.datetime.fromtimestamp(p.stat().st_mtime).strftime("%Y-%m-%d %H:%M")})
    return out


def pdf_path(key: str, build: str) -> Path:
    for x in builds(key):
        if x["build"] == build:
            return ROOT / x["pdf"]
    raise ValueError(f"{build!r} is not a printed copy of {key}")


@functools.lru_cache(maxsize=6)
def _doc(path: str, stamp: float):
    import pymupdf
    return pymupdf.open(path)


def doc(key: str, build: str):
    p = pdf_path(key, build)
    return _doc(str(p), p.stat().st_mtime)


def sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


# ----------------------------------------------------------------------
# A page
# ----------------------------------------------------------------------

def page_png(key: str, build: str, n: int, scale: float) -> bytes:
    """Page n (from 1) drawn at `scale` (1 = 72 dpi), cached by the file and the size."""
    p = pdf_path(key, build)
    scale = max(0.1, min(4.0, round(scale, 2)))
    CACHE.mkdir(parents=True, exist_ok=True)
    f = CACHE / f"{hashlib.sha1(f'{p}|{p.stat().st_mtime}'.encode()).hexdigest()[:16]}-{n}-{scale}.png"
    if f.is_file():
        return f.read_bytes()
    import pymupdf
    with _LOCK:
        d = doc(key, build)
        pix = d[n - 1].get_pixmap(matrix=pymupdf.Matrix(scale, scale), alpha=False)
        data = pix.tobytes("png")
    f.write_bytes(data)
    return data


def _is_recto(n: int) -> bool:
    """Page 1 is a right-hand page: odd pages are rectos, their inside edge on the left."""
    return n % 2 == 1


def measure(page, n: int) -> dict:
    """What is printed on a page and how far it stands from each trimmed edge."""
    W, H = page.rect.width, page.rect.height
    boxes = []
    for kind, r in page.get_bboxlog():
        if r[2] - r[0] <= 0.01 and r[3] - r[1] <= 0.01:
            continue
        # a full-page white background is not content
        if kind.startswith("fill") and r[0] <= 0.5 and r[1] <= 0.5 and r[2] >= W - 0.5 and r[3] >= H - 0.5:
            continue
        boxes.append((kind, [max(0, r[0]), max(0, r[1]), min(W, r[2]), min(H, r[3])]))
    images = []
    for info in page.get_image_info(xrefs=True):
        bx = info["bbox"]
        w_in, h_in = (bx[2] - bx[0]) / PT, (bx[3] - bx[1]) / PT
        ppi = min(info["width"] / w_in, info["height"] / h_in) if w_in > 0 and h_in > 0 else 0
        # a picture drawn past the page's edge is cut by it: the rest of it is on the page before or after
        cut = bx[0] < -1 or bx[1] < -1 or bx[2] > W + 1 or bx[3] > H + 1
        images.append({"bbox": [round(v, 1) for v in bx], "px": [info["width"], info["height"]], "ppi": round(ppi), "cut": cut})
    if not boxes:
        return {"w": W, "h": H, "blank": True, "box": None, "margins": None, "images": images, "inside": "left" if _is_recto(n) else "right"}
    x0 = min(b[1][0] for b in boxes); y0 = min(b[1][1] for b in boxes)
    x1 = max(b[1][2] for b in boxes); y1 = max(b[1][3] for b in boxes)
    left, right, top, bottom = x0 / PT, (W - x1) / PT, y0 / PT, (H - y1) / PT
    recto = _is_recto(n)
    return {"w": W, "h": H, "blank": False, "box": [round(x0, 1), round(y0, 1), round(x1, 1), round(y1, 1)],
            "margins": {"inside": round(left if recto else right, 3), "outside": round(right if recto else left, 3),
                        "top": round(top, 3), "bottom": round(bottom, 3)},
            "images": images, "inside": "left" if recto else "right"}


def page(key: str, build: str, n: int) -> dict:
    with _LOCK:
        d = doc(key, build)
        if not 1 <= n <= d.page_count:
            raise ValueError(f"no page {n}: the book has {d.page_count}")
        pg = d[n - 1]
        text = pg.get_text()
        m = measure(pg, n)
        words = pg.get_text("words")
    return {"n": n, "pages": d.page_count, "text": text, **m,
            "words": [[round(w[0], 1), round(w[1], 1), round(w[2], 1), round(w[3], 1), w[4]] for w in words[:4000]]}


def search(key: str, build: str, query: str, limit: int = 60) -> list[dict]:
    """The pages a phrase appears on, with where."""
    q = query.strip()
    if len(q) < 2:
        return []
    out = []
    with _LOCK:
        d = doc(key, build)
        for i in range(d.page_count):
            hits = d[i].search_for(q, quads=False)
            if hits:
                out.append({"n": i + 1, "hits": [[round(r.x0, 1), round(r.y0, 1), round(r.x1, 1), round(r.y1, 1)] for r in hits[:8]]})
                if len(out) >= limit:
                    break
    return out


# ----------------------------------------------------------------------
# Where a page's words come from
# ----------------------------------------------------------------------

def _norm(s: str) -> str:
    s = unicodedata.normalize("NFKC", s)
    s = re.sub(r"[*_`#>\[\]()|~]", " ", s)
    s = s.replace("’", "'").replace("‘", "'").replace("“", '"').replace("”", '"').replace("—", "-").replace("–", "-")
    return re.sub(r"\s+", " ", s).strip().lower()


@functools.lru_cache(maxsize=8)
def _sources(key: str, stamp: float) -> list[tuple[str, str, str]]:
    out = []
    for c in MS.chapters(key):
        text = MS.read(key, c["path"])
        out.append((c["path"], text, _norm(text)))
    return out


def sources(key: str) -> list[tuple[str, str, str]]:
    folder = ROOT / MS.book(key).words
    stamp = max((p.stat().st_mtime for p in folder.rglob("*.md")), default=0)
    return _sources(key, stamp)


def source_for(key: str, text: str) -> dict | None:
    """The chapter a page's words come from: its longer lines, looked for in every chapter."""
    lines = [_norm(ln) for ln in text.splitlines()]
    probes = sorted({ln[:70] for ln in lines if len(ln) >= 40}, key=len, reverse=True)[:12]
    if not probes:
        probes = [ln for ln in lines if len(ln) >= 16][:6]
    best, best_hits, first = None, 0, None
    for path, raw, norm in sources(key):
        hits = [p for p in probes if p in norm]
        if len(hits) > best_hits:
            best, best_hits, first = (path, raw, norm), len(hits), hits[0]
    if not best:
        return None
    path, raw, norm = best
    # the line in the file the first matched words begin on
    at = norm.find(first)
    words_before = len(norm[:at].split())
    line = 1
    count = 0
    for i, ln in enumerate(raw.splitlines(), start=1):
        count += len(_norm(ln).split())
        if count >= words_before:
            line = i
            break
    return {"path": path, "line": line, "matched": best_hits, "of": len(probes)}


# ----------------------------------------------------------------------
# Notes on pages
# ----------------------------------------------------------------------

KINDS = ("fix", "question", "ok", "note")


def _notes_file(key: str) -> Path:
    return ROOT / MS.book(key).words / "proof" / "annotations.json"


def notes(key: str) -> list[dict]:
    f = _notes_file(key)
    try:
        return json.loads(f.read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return []


def _save_notes(key: str, items: list[dict]) -> None:
    f = _notes_file(key)
    f.parent.mkdir(parents=True, exist_ok=True)
    tmp = f.with_suffix(".tmp")
    tmp.write_text(json.dumps(items, ensure_ascii=False, indent=1), encoding="utf-8")
    tmp.replace(f)


def add_note(key: str, build: str, n: int, text: str, kind: str = "fix", rect: list | None = None, author: str = "owner") -> dict:
    if kind not in KINDS:
        raise ValueError(f"a note is one of {', '.join(KINDS)}")
    if not text.strip():
        raise ValueError("a note needs words")
    pg = page(key, build, n)
    # the words under the note (or the page's first line): how it is found again in a later build
    anchor = ""
    if rect:
        under = [w[4] for w in pg["words"] if w[0] >= rect[0] - 2 and w[2] <= rect[2] + 2 and w[1] >= rect[1] - 2 and w[3] <= rect[3] + 2]
        anchor = " ".join(under)[:160]
    if not anchor:
        anchor = next((ln.strip() for ln in pg["text"].splitlines() if len(ln.strip()) > 20), "")[:160]
    with _LOCK:
        items = notes(key)
        item = {"id": hashlib.sha1(f"{build}{n}{text}{dt.datetime.now().isoformat()}".encode()).hexdigest()[:10], "build": build, "page": n,
                "rect": [round(v, 1) for v in rect] if rect else None, "kind": kind, "text": text.strip(), "status": "open", "author": author,
                "anchor": anchor, "created": dt.datetime.now().strftime("%Y-%m-%d %H:%M"), "replies": []}
        items.append(item)
        _save_notes(key, items)
    return item


def update_note(key: str, note_id: str, **fields) -> dict:
    with _LOCK:
        items = notes(key)
        item = next((x for x in items if x["id"] == note_id), None)
        if not item:
            raise ValueError(f"no note {note_id}")
        for k in ("text", "kind", "status"):
            if k in fields and fields[k] is not None:
                if k == "kind" and fields[k] not in KINDS:
                    raise ValueError(f"a note is one of {', '.join(KINDS)}")
                if k == "status" and fields[k] not in ("open", "resolved"):
                    raise ValueError("a note is open or resolved")
                item[k] = fields[k]
        if fields.get("status") == "resolved":
            item["resolved"] = dt.datetime.now().strftime("%Y-%m-%d %H:%M")
        if fields.get("reply"):
            item["replies"].append({"by": fields.get("author", "owner"), "text": fields["reply"], "at": dt.datetime.now().strftime("%Y-%m-%d %H:%M")})
        _save_notes(key, items)
    return item


def delete_note(key: str, note_id: str) -> None:
    with _LOCK:
        _save_notes(key, [x for x in notes(key) if x["id"] != note_id])


def notes_for(key: str, build: str) -> list[dict]:
    """This build's notes, and the open notes from earlier builds found again in it by their words."""
    out = []
    order = [b["build"] for b in builds(key)]
    for x in notes(key):
        if x["build"] == build:
            out.append({**x, "here": x["page"], "carried": False})
        elif x["status"] == "open" and x["build"] in order and order.index(x["build"]) > order.index(build) and x.get("anchor"):
            hit = search(key, build, x["anchor"][:60], limit=1)
            out.append({**x, "here": hit[0]["n"] if hit else None, "carried": True,
                        "rect_here": hit[0]["hits"][0] if hit and x.get("rect") else None})
    return out


def report(key: str, build: str) -> str:
    b = MS.book(key)
    lines = [f"# Proof notes: {b.title}", "", f"Build {build}, {dt.date.today().isoformat()}", ""]
    for x in sorted(notes_for(key, build), key=lambda y: (y["here"] or 9999, y["created"])):
        where = f"page {x['here']}" if x["here"] else "not found in this build"
        carried = f" (from {x['build']})" if x["carried"] else ""
        lines.append(f"- [{x['status']}] **{x['kind']}**, {where}{carried}: {x['text']}")
        for r in x.get("replies", []):
            lines.append(f"  - {r['by']}, {r['at']}: {r['text']}")
    return "\n".join(lines) + "\n"


# ----------------------------------------------------------------------
# The KDP preflight
# ----------------------------------------------------------------------

LEFTOVERS = {"an unfilled {{token}}": r"\{\{|\}\}", "a TODO or FIXME": r"\b(TODO|FIXME|XXX)\b",
             "placeholder text": r"(?i)lorem ipsum",
             # a value that failed to compute; "None of them" is English, "= None" and "None in" are not
             "a printed NaN, undefined or None value": r"(?<![A-Za-z])(NaN|nan|undefined)(?![A-Za-z])|[=:]\s*None\b|\bNone\s+(in|ft|mm|cm|%|\$|°)"}


def _check(key: str, title: str, status: str, detail: str, pages: list[int] | None = None) -> dict:
    return {"key": key, "title": title, "status": status, "detail": detail, "pages": (pages or [])[:200], "count": len(pages or [])}


@functools.lru_cache(maxsize=8)
def _preflight(path: str, stamp: float, paper: str) -> dict:
    from wedge_book import kdp as WK
    p = Path(path)
    out: list[dict] = []
    import pymupdf
    d = pymupdf.open(path)
    n = d.page_count
    if d.is_encrypted:
        out.append(_check("open", "The file opens", "fail", "the PDF is encrypted; KDP needs an unlocked file"))
    sizes = sorted({(round(pg.rect.width / PT, 3), round(pg.rect.height / PT, 3)) for pg in d})
    out.append(_check("one-size", "Every page the same size", "pass" if len(sizes) == 1 else "fail",
                      ", ".join(f"{w:g} x {h:g} in" for w, h in sizes)))
    w, h = sizes[0]
    trim, bleed = None, False
    for tw, th in K.TRIM_SIZES:
        if abs(w - tw) < 0.01 and abs(h - th) < 0.01:
            trim = (tw, th)
        elif abs(w - tw - K.BLEED_WIDTH_IN) < 0.01 and abs(h - th - K.BLEED_HEIGHT_IN) < 0.01:
            trim, bleed = (tw, th), True
    out.append(_check("trim", "A KDP trim size", "pass" if trim else "fail",
                      f"{trim[0]:g} x {trim[1]:g} in{' with bleed' if bleed else ', no bleed'}" if trim else f"{w:g} x {h:g} in is not one of KDP's sizes"))
    lo, hi = K.PAGE_RANGE[paper]
    out.append(_check("pages", "Page count", "pass" if lo <= n <= hi else "fail", f"{n} pages; {paper.replace('-', ' ')} takes {lo} to {hi}"))
    info = WK.inspect(p)
    out.append(_check("fonts", "Every font embedded", "pass" if info["embedded"] and not info["not_embedded"] else "fail",
                      f"embedded: {', '.join(x.split('+')[-1] for x in info['embedded'])}" + (f"; NOT embedded: {', '.join(info['not_embedded'])}" if info["not_embedded"] else "")))
    # margins, measured off every page against the table for this page count
    need_in = K.gutter_for(n)
    need_out = K.OUTSIDE_MIN_BLEED_IN if bleed else K.OUTSIDE_MIN_IN
    tight_in, tight_out, blank, low_ppi, cut = [], [], [], [], []
    worst = {"inside": 9.0, "outside": 9.0, "top": 9.0, "bottom": 9.0}
    for i, pg in enumerate(d, start=1):
        m = measure(pg, i)
        if m["blank"]:
            blank.append(i)
            continue
        mg = m["margins"]
        for k2 in worst:
            worst[k2] = min(worst[k2], mg[k2])
        if need_in is not None and mg["inside"] < need_in - 0.005:
            tight_in.append(i)
        if min(mg["outside"], mg["top"], mg["bottom"]) < need_out - 0.005 and not bleed:
            tight_out.append(i)
        if any(0 < im["ppi"] < K.IMAGE_MIN_PPI for im in m["images"]):
            low_ppi.append(i)
        if any(im["cut"] for im in m["images"]):
            cut.append(i)
    out.append(_check("gutter", "Inside margin (gutter)", "fail" if tight_in or need_in is None else "pass",
                      (f"KDP asks {need_in} in for {n} pages; the tightest page has {worst['inside']:.3f} in" if need_in else f"{n} pages is past KDP's gutter table")
                      + (f"; {len(tight_in)} pages are tighter" if tight_in else ""), tight_in))
    out.append(_check("outside", "Outside, top and bottom margins", "fail" if tight_out else "pass",
                      f"KDP asks {need_out} in; the tightest: outside {worst['outside']:.3f}, top {worst['top']:.3f}, bottom {worst['bottom']:.3f} in"
                      + (f"; {len(tight_out)} pages are tighter" if tight_out else ""), tight_out))
    out.append(_check("images", "Picture resolution", "warn" if low_ppi else "pass",
                      f"{len(low_ppi)} pages have a picture under {K.IMAGE_MIN_PPI} ppi" if low_ppi else f"every picture {K.IMAGE_MIN_PPI} ppi or better", low_ppi))
    out.append(_check("cut", "No picture cut by a page edge", "fail" if cut else "pass",
                      f"{len(cut)} pages carry part of a picture that runs off the page (the layout broke a figure across pages)" if cut else "every picture whole on its page", cut))
    runs, run = [], []
    for i in range(1, n + 1):
        if i in blank:
            run.append(i)
        else:
            if run:
                runs.append(run)
            run = []
    end_run = run
    long_mid = [p2 for r in runs if len(r) > K.BLANK_RUN_MAX for p2 in r]
    bad_end = len(end_run) > K.BLANK_END_MAX
    out.append(_check("blank", "Blank pages", "fail" if long_mid or bad_end else "pass",
                      f"{len(blank)} blank pages; longest run inside the book {max((len(r) for r in runs), default=0)}, at the end {len(end_run)}", long_mid or end_run if bad_end else long_mid))
    out.append(_check("size", "File size", "pass" if info["bytes"] <= K.FILE_MAX_BYTES else "fail", f"{info['bytes'] / 1e6:.1f} MB"))
    rendered = WK.check_rendered(p)
    pages_bad = sorted({x for v in rendered.values() for x in v})
    out.append(_check("unrendered", "No unrendered source on a page", "fail" if rendered else "pass",
                      "; ".join(f"{k2}: {len(v)} pages" for k2, v in rendered.items()) if rendered else "no raw math, tags or Markdown found", pages_bad))
    left: dict[str, list[int]] = {}
    for i, pg in enumerate(d, start=1):
        text = pg.get_text()
        for name, pat in LEFTOVERS.items():
            if re.search(pat, text):
                left.setdefault(name, []).append(i)
    out.append(_check("leftovers", "No leftover placeholders", "warn" if left else "pass",
                      "; ".join(f"{k2}: {len(v)} pages" for k2, v in left.items()) if left else "no tokens, TODOs or placeholders", sorted({x for v in left.values() for x in v})))
    meta = d.metadata or {}
    out.append(_check("meta", "Title and author in the file", "pass" if meta.get("title") and meta.get("author") else "warn",
                      f"{meta.get('title') or '(no title)'} by {meta.get('author') or '(no author)'}"))
    d.close()
    return {"pages": n, "trim": trim, "bleed": bleed, "paper": paper, "bytes": info["bytes"], "checks": out,
            "spine_in": K.spine_in(n, paper), "spine_text": n >= K.SPINE_TEXT_MIN_PAGES,
            "cover_in": K.cover_size_in(trim, n, paper) if trim else None, "need_gutter_in": need_in, "need_outside_in": need_out, "worst": worst}


def preflight(key: str, build: str, paper: str = "black-white") -> dict:
    if paper not in K.PAGE_RANGE:
        raise ValueError(f"paper is one of {', '.join(K.PAGE_RANGE)}")
    p = pdf_path(key, build)
    res = dict(_preflight(str(p), p.stat().st_mtime, paper))
    ns = notes_for(key, build)
    open_fix = [x for x in ns if x["status"] == "open" and x["kind"] == "fix"]
    open_q = [x for x in ns if x["status"] == "open" and x["kind"] == "question"]
    res["checks"] = res["checks"] + [_check("notes", "Proof notes settled", "fail" if open_fix else "warn" if open_q else "pass",
                                            f"{len(open_fix)} fixes and {len(open_q)} questions open of {len(ns)} notes",
                                            sorted({x['here'] for x in open_fix + open_q if x['here']}))]
    res["fails"] = sum(1 for c in res["checks"] if c["status"] == "fail")
    res["warns"] = sum(1 for c in res["checks"] if c["status"] == "warn")
    return res


# ----------------------------------------------------------------------
# Certificates
# ----------------------------------------------------------------------

def _certs_dir(key: str) -> Path:
    return ROOT / MS.book(key).words / "proof" / "certificates"


def certificates(key: str) -> list[dict]:
    d = _certs_dir(key)
    out = []
    for f in sorted(d.glob("*.json"), reverse=True) if d.is_dir() else []:
        try:
            out.append(json.loads(f.read_text(encoding="utf-8")))
        except ValueError:
            continue
    return out


def certify(key: str, build: str, paper: str, statement: str, by: str = "the owner", allow_warnings: bool = False) -> dict:
    pf = preflight(key, build, paper)
    if pf["fails"]:
        raise ValueError(f"{pf['fails']} checks fail; fix them before certifying")
    if pf["warns"] and not allow_warnings:
        raise ValueError(f"{pf['warns']} checks warn; accept them to certify")
    p = pdf_path(key, build)
    b = MS.book(key)
    cert = {
        "book": b.title, "key": key, "build": build, "file": p.relative_to(ROOT).as_posix(), "sha256": sha256(p), "bytes": p.stat().st_size,
        "pages": pf["pages"], "trim_in": pf["trim"], "bleed": pf["bleed"], "paper": paper, "spine_in": round(pf["spine_in"], 4),
        "spine_text_allowed": pf["spine_text"], "cover_in": [round(x, 4) for x in pf["cover_in"]] if pf["cover_in"] else None,
        "checks": pf["checks"], "warnings_accepted": [c["title"] for c in pf["checks"] if c["status"] == "warn"],
        "notes": {"total": len(notes_for(key, build)), "open": sum(1 for x in notes_for(key, build) if x["status"] == "open")},
        "statement": statement.strip(), "by": by, "at": dt.datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "rules": {"source": K.SOURCE, "table": K.table()},
    }
    d = _certs_dir(key)
    d.mkdir(parents=True, exist_ok=True)
    f = d / f"{dt.datetime.now().strftime('%Y%m%d-%H%M%S')}-{build}-{cert['sha256'][:8]}.json"
    f.write_text(json.dumps(cert, ensure_ascii=False, indent=1), encoding="utf-8")
    cert["saved"] = f.relative_to(ROOT).as_posix()
    return cert


def verify(key: str, cert_sha: str, build: str) -> bool:
    """Is the file still the one that was certified (byte for byte)?"""
    return sha256(pdf_path(key, build)) == cert_sha


# ----------------------------------------------------------------------
# Two builds compared
# ----------------------------------------------------------------------

def changed(key: str, a: str, b: str) -> dict:
    """The pages of build b whose words or pictures differ from build a's page of the same number."""
    def sig(build: str) -> list[str]:
        with _LOCK:
            d = doc(key, build)
            return [hashlib.sha1((pg.get_text() + str(len(pg.get_image_info()))).encode()).hexdigest() for pg in d]
    sa, sb = sig(a), sig(b)
    diff = [i + 1 for i in range(len(sb)) if i >= len(sa) or sa[i] != sb[i]]
    return {"a": a, "b": b, "pages_a": len(sa), "pages_b": len(sb), "changed": diff}


# ----------------------------------------------------------------------
# Routes (under the Book Studio's, on this PC only)
# ----------------------------------------------------------------------

def handles(path: str) -> bool:
    return path in ("/studio/proof", "/studio/proof/") or path.startswith("/api/studio/proof/")


def handle(h, method: str):
    from urllib.parse import parse_qs, urlparse
    u = urlparse(h.path)
    q = {k: v[0] for k, v in parse_qs(u.query).items()}
    p = u.path[len("/api/studio/proof/"):] if u.path.startswith("/api/studio/proof/") else ""
    try:
        if method == "GET":
            if u.path in ("/studio/proof", "/studio/proof/"):
                return h._file(Path(__file__).resolve().parent / "static" / "proof.html")
            if p == "books":
                return h._json(books())
            if p == "builds":
                return h._json({"builds": builds(q["book"]), "certificates": certificates(q["book"]), "job": MS.JOBS.get(q["book"])})
            if p == "page.png":
                return h._send(200, page_png(q["book"], q["build"], int(q["n"]), float(q.get("scale", 1))), "image/png")
            if p == "page":
                pg = page(q["book"], q["build"], int(q["n"]))
                return h._json({**pg, "source": source_for(q["book"], pg["text"])})
            if p == "search":
                return h._json(search(q["book"], q["build"], q.get("q", "")))
            if p == "notes":
                return h._json(notes_for(q["book"], q["build"]))
            if p == "report":
                return h._send(200, report(q["book"], q["build"]).encode("utf-8"), "text/markdown; charset=utf-8")
            if p == "preflight":
                return h._json(preflight(q["book"], q["build"], q.get("paper", "black-white")))
            if p == "rules":
                return h._json({"source": K.SOURCE, "table": K.table()})
            if p == "changed":
                return h._json(changed(q["book"], q["a"], q["b"]))
            if p == "chapter":
                return h._json({"path": q["path"], "text": MS.read(q["book"], q["path"])})
            if p == "chapters":
                return h._json({"chapters": MS.chapters(q["book"]), "build": MS.book(q["book"]).build})
            if p == "verify":
                return h._json({"same": verify(q["book"], q["sha"], q["build"])})
        data = h._body()
        if method == "POST":
            if p == "notes":
                return h._json(add_note(data["book"], data["build"], int(data["page"]), data.get("text", ""), data.get("kind", "fix"), data.get("rect")))
            m = re.fullmatch(r"notes/([0-9a-f]+)", p)
            if m:
                return h._json(update_note(data["book"], m.group(1), **{k: data.get(k) for k in ("text", "kind", "status", "reply")}))
            m = re.fullmatch(r"notes/([0-9a-f]+)/delete", p)
            if m:
                delete_note(data["book"], m.group(1))
                return h._json({"ok": True})
            if p == "chapter":
                return h._json(MS.write(data["book"], data["path"], data["text"]))
            if p == "replace":
                return h._json(MS.replace(data["book"], data["path"], data["find"], data["replace"]))
            if p == "rebuild":
                return h._json(MS.build(data["book"]))
            if p == "certify":
                return h._json(certify(data["book"], data["build"], data.get("paper", "black-white"), data.get("statement", ""),
                                       data.get("by", "the owner"), bool(data.get("acceptWarnings"))))
            if p == "agent":
                from books.studio import proof_agent as PA
                return h._json(PA.run(data["book"], data["build"], int(data.get("page") or 1), data.get("message", ""), data.get("history") or []))
        return h._err(404, "not found")
    except (KeyError, ValueError, PermissionError, FileNotFoundError) as e:
        return h._err(400, f"{type(e).__name__}: {e}")
    except Exception as e:                        # the page shows the message
        return h._err(500, f"{type(e).__name__}: {e}")
