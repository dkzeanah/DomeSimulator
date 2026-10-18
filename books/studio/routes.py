"""The Book Studio's routes, served by the composer's local server (books.composer.server) on this PC only.

    /studio                        the studio's page
    /api/studio/books              every book: layout books, books that can be imported, manuscript books
    /api/studio/layout/<slug>      a layout book (GET), saved (PUT); POST /api/studio/layout makes or imports one
    /api/studio/layout/<slug>/export   print to a new numbered PDF in the library
    /api/studio/fill               fill {{tokens}} in a piece of text, as the printed book will
    /api/studio/library            the pictures; POST .../svg files a pasted SVG, .../upload a picture
    /api/studio/illustrate         DeepSeek draws one; /api/studio/claude-prompt writes the request for Claude
    /api/studio/agent              one instruction to the DeepSeek agent
    /api/studio/chapters|chapter   a manuscript book's chapters, one chapter (GET, PUT), a replacement (POST)
    /api/studio/build              run a manuscript book's own build (POST), and how it is going (GET)
"""

from __future__ import annotations

import base64
import re
from pathlib import Path
from urllib.parse import parse_qs, urlparse

from books.studio import agent as AG
from books.studio import doc as D
from books.studio import library as lib
from books.studio import manuscripts as MS

HERE = Path(__file__).resolve().parent
STATIC = HERE / "static"


def handles(path: str) -> bool:
    return path == "/studio" or path.startswith("/studio/") or path.startswith("/api/studio/")


def _books() -> dict:
    from books import shelf as S
    lays = []
    for slug in D.layouts():
        try:
            d = D.load(slug)
            lays.append({"slug": slug, "title": d["title"], "pages": len(d["pages"]), "w": d["page"]["w"], "h": d["page"]["h"]})
        except (OSError, ValueError):
            lays.append({"slug": slug, "title": slug, "pages": 0, "broken": True})
    have = {x["slug"] for x in lays}
    importable = [{"slug": s, "title": s.replace("-", " ").title()} for s in D.IMPORTERS if s not in have]
    manuscripts = [{"key": b.key, "title": b.title, "by": b.by, "status": b.status, "engine": b.engine, "build": b.build,
                    "latest": MS.latest_pdf(b.key), "chapters": len(MS.chapters(b.key))} for b in S.SHELF]
    return {"layouts": lays, "importable": importable, "manuscripts": manuscripts}


def handle(h, method: str):
    """``h`` is the composer's request handler (its _json, _err, _body, _file, _send)."""
    u = urlparse(h.path)
    q = {k: v[0] for k, v in parse_qs(u.query).items()}
    p = u.path
    try:
        if method == "GET" and p in ("/studio", "/studio/"):
            return h._file(STATIC / "studio.html")
        if method == "GET" and p.startswith("/studio/static/"):
            f = (STATIC / p[len("/studio/static/"):]).resolve()
            if not f.is_relative_to(STATIC) or not f.is_file():
                return h._err(404, "not found")
            return h._file(f)
        if p == "/api/studio/books" and method == "GET":
            return h._json(_books())

        m = re.fullmatch(r"/api/studio/layout/([a-z0-9-]+)", p)
        if m and method == "GET":
            return h._json(D.load(m.group(1)))
        if m and method == "PUT":
            D.save(m.group(1), h._body())
            return h._json({"ok": True})
        if p == "/api/studio/layout" and method == "POST":
            b = h._body()
            if b.get("import"):
                slug = b["import"]
                if slug not in D.IMPORTERS:
                    return h._err(400, f"no importer for {slug}")
                if D.path(slug).exists():
                    return h._err(409, f"{slug} already has a layout")
                D.save(slug, D.IMPORTERS[slug]())
                return h._json({"slug": slug})
            title = (b.get("title") or "").strip() or "Untitled"
            slug = re.sub(r"[^a-z0-9]+", "-", (b.get("slug") or title).lower()).strip("-") or "untitled"
            if D.path(slug).exists():
                return h._err(409, f"a book called {slug} already exists")
            D.save(slug, D.new(title, float(b.get("w", 8.5)), float(b.get("h", 11)), int(b.get("pages", 1))))
            return h._json({"slug": slug})
        m = re.fullmatch(r"/api/studio/layout/([a-z0-9-]+)/export", p)
        if m and method == "POST":
            body = h._body()
            out = D.export_pdf(m.group(1), D.validate(body["doc"]) if body.get("doc") else None)
            return h._json({"path": out.relative_to(D.ROOT).as_posix()})
        if p == "/api/studio/fill" and method == "POST":
            return h._json({"text": D.fill_tokens(h._body().get("text", ""))})

        if p == "/api/studio/library" and method == "GET":
            return h._json(lib.entries(q.get("text", "")))
        if p == "/api/studio/library/svg" and method == "POST":
            b = h._body()
            return h._json(lib.add_svg(b["name"], b["svg"], b.get("origin", "owner"), b.get("prompt"), b.get("note", "")))
        if p == "/api/studio/library/upload" and method == "POST":
            b = h._body()
            ext = "." + b.get("ext", "png").lower().lstrip(".")
            if ext not in lib.PICTURE:
                return h._err(400, "pictures only: svg, png, jpg, webp")
            data = base64.b64decode(b["data"])
            if ext == ".svg":
                return h._json(lib.add_svg(b["name"], data.decode("utf-8"), b.get("origin", "owner"), b.get("prompt")))
            return h._json(lib.add(b["name"], data, ext, b.get("origin", "owner"), b.get("prompt")))
        if p == "/api/studio/illustrate" and method == "POST":
            b = h._body()
            svg = lib.deepseek_svg(b["description"], float(b.get("w", 1)), float(b.get("h", 1)))
            return h._json(lib.add_svg(b["name"], svg, "deepseek", b["description"], "Drawn by DeepSeek in the Book Studio."))
        if p == "/api/studio/claude-prompt" and method == "POST":
            b = h._body()
            return h._json({"prompt": lib.claude_prompt(b["name"], b["description"], float(b.get("w", 1)), float(b.get("h", 1)), b.get("book", ""))})

        if p == "/api/studio/agent" and method == "POST":
            b = h._body()
            res = AG.run(b["instruction"], layout=b.get("doc"), book_key=b.get("book"), page=b.get("page"),
                         selected=b.get("selected"), history=b.get("history"))
            return h._json(res)

        if p == "/api/studio/chapters" and method == "GET":
            return h._json({"chapters": MS.chapters(q["book"]), "latest": MS.latest_pdf(q["book"])})
        if p == "/api/studio/chapter" and method == "GET":
            return h._json({"text": MS.read(q["book"], q["path"])})
        if p == "/api/studio/chapter" and method == "PUT":
            b = h._body()
            return h._json(MS.write(b["book"], b["path"], b["text"]))
        if p == "/api/studio/chapter/replace" and method == "POST":
            b = h._body()
            return h._json(MS.replace(b["book"], b["path"], b["find"], b["replace"]))
        if p == "/api/studio/build" and method == "POST":
            return h._json(MS.build(h._body()["book"]))
        if p == "/api/studio/build" and method == "GET":
            job = MS.JOBS.get(q["book"])
            return h._json(job or {"state": "idle"})
        return h._err(404, "not found")
    except PermissionError as e:
        return h._err(403, str(e))
    except (KeyError, ValueError, FileNotFoundError, RuntimeError) as e:
        return h._err(400, f"{type(e).__name__}: {e}")
    except OSError as e:
        return h._err(502, f"{type(e).__name__}: {e}")
