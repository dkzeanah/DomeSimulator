"""The composer's local server: the page in the browser talks to this, on this PC only.

    py -3.12 -m books.composer             # opens http://127.0.0.1:8765 in the browser
    py -3.12 -m books.composer --no-browser --port 8765
    py -3.12 -m books.composer --selftest

It listens on 127.0.0.1 only, so nothing on the network can reach it. It reads and
writes the books' ``loom.json`` files (every save keeps the previous copy), lists the
pictures in ``assets/`` and the PDFs in the library, draws PDF pages to images for the
reader, keeps notes on any PDF page, and prints a book to a new numbered PDF.
"""

from __future__ import annotations

import argparse
import json
import mimetypes
import re
import sys
import threading
import webbrowser
from http import HTTPStatus
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import parse_qs, unquote, urlparse

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from books.composer import loom as L  # noqa: E402
from books.studio import routes as SR  # noqa: E402

STATIC = HERE / "static"
NOTES = ROOT / "books" / ".pdf-notes"


def _inside(path: Path, *roots: Path) -> bool:
    p = path.resolve()
    return any(p.is_relative_to(r.resolve()) for r in roots)


def shelf() -> dict:
    from books import shelf as S
    out = []
    for b in S.SHELF:
        latest = b.latest() if b.output else None
        out.append({"key": b.key, "title": b.title, "words": b.words, "engine": b.engine, "build": b.build,
                    "by": b.by, "status": b.status, "note": b.note,
                    "latest": latest.relative_to(ROOT).as_posix() if latest else None})
    looms = []
    for slug in L.looms():
        try:
            lm = L.load(slug)
            done = sum(1 for c in lm["cells"].values() if c.get("status") == "done")
            looms.append({"slug": slug, "title": lm["title"], "kind": lm.get("kind", ""),
                          "cells": len(lm["cells"]), "done": done})
        except (OSError, ValueError, KeyError):
            looms.append({"slug": slug, "title": slug, "kind": "?", "cells": 0, "done": 0})
    return {"books": out, "looms": looms,
            "templates": {k: v["label"] for k, v in L.TEMPLATES.items()}, "link_kinds": L.LINK_KINDS}


def assets() -> list[dict]:
    try:
        import assetlib
        rows = list(assetlib.load().values())
    except ImportError:
        rows = []
    return sorted(({"name": e["name"], "version": e["version"], "file": "assets/" + e["file"],
                    "category": e["category"], "note": e.get("note", ""), "origin": e.get("origin", "")}
                   for e in rows if e["category"] not in ("clips", "reference")
                   or e["file"].endswith(".pdf")), key=lambda e: (e["category"], e["name"], e["version"]))


def pdfs() -> list[dict]:
    import medialib
    out = []
    for item in medialib.items():
        for p in item.entries:
            if p.is_file() and p.suffix.lower() == ".pdf":
                out.append({"path": p.relative_to(ROOT).as_posix(), "item": item.slug, "day": item.day,
                            "name": p.name})
    for p in sorted((ROOT / "assets" / "reference").glob("*.pdf")):
        out.append({"path": p.relative_to(ROOT).as_posix(), "item": "reference", "day": "", "name": p.name})
    return sorted(out, key=lambda r: (r["day"], r["name"]), reverse=True)


def _pdf_path(rel: str) -> Path:
    p = (ROOT / rel).resolve()
    if p.suffix.lower() != ".pdf" or not p.is_file() or not _inside(p, ROOT / "deliverables", ROOT / "assets"):
        raise PermissionError("only PDFs in the library or in assets/ can be opened")
    return p


def _notes_file(rel: str) -> Path:
    return NOTES / (re.sub(r"[^A-Za-z0-9._-]+", "_", rel) + ".json")


class Handler(BaseHTTPRequestHandler):
    server_version = "Composer/1"

    def log_message(self, fmt, *args):          # quiet
        pass

    # -- plumbing ---------------------------------------------------------
    def _send(self, code: int, body: bytes, ctype: str) -> None:
        self.send_response(code)
        self.send_header("Content-Type", ctype)
        self.send_header("Content-Length", str(len(body)))
        self.send_header("Cache-Control", "no-store")
        self.end_headers()
        self.wfile.write(body)

    def _json(self, data, code: int = 200) -> None:
        self._send(code, json.dumps(data, ensure_ascii=False).encode("utf-8"), "application/json; charset=utf-8")

    def _err(self, code: int, msg: str) -> None:
        self._json({"error": msg}, code)

    def _body(self) -> dict:
        n = int(self.headers.get("Content-Length") or 0)
        return json.loads(self.rfile.read(n) or b"{}") if n else {}

    def _file(self, p: Path) -> None:
        ctype = mimetypes.guess_type(p.name)[0] or "application/octet-stream"
        self._send(200, p.read_bytes(), ctype)

    # -- routes -----------------------------------------------------------
    def do_GET(self):  # noqa: N802
        u = urlparse(self.path)
        q = {k: v[0] for k, v in parse_qs(u.query).items()}
        if SR.handles(u.path):                         # the Book Studio (books.studio)
            return SR.handle(self, "GET")
        try:
            if u.path in ("/", "/index.html"):
                return self._file(STATIC / "index.html")
            if u.path.startswith("/static/"):
                p = (STATIC / unquote(u.path[len("/static/"):])).resolve()
                if not _inside(p, STATIC) or not p.is_file():
                    return self._err(404, "not found")
                return self._file(p)
            if u.path.startswith("/file/"):
                p = (ROOT / unquote(u.path[len("/file/"):])).resolve()
                if not _inside(p, ROOT / "assets", ROOT / "books", ROOT / "deliverables") or not p.is_file():
                    return self._err(404, "not found")
                return self._file(p)
            if u.path == "/api/shelf":
                return self._json(shelf())
            if u.path == "/api/assets":
                return self._json(assets())
            if u.path == "/api/pdfs":
                return self._json(pdfs())
            m = re.fullmatch(r"/api/loom/([a-z0-9-]+)", u.path)
            if m:
                return self._json(L.load(m.group(1)))
            m = re.fullmatch(r"/api/loom/([a-z0-9-]+)/preview", u.path)
            if m:
                lm = L.load(m.group(1))
                page = L.render_html(lm, q.get("order", "by-level"))
                page = page.replace("file:///", "/file-abs/")
                return self._send(200, page.encode("utf-8"), "text/html; charset=utf-8")
            if u.path.startswith("/file-abs/"):
                p = Path(unquote(u.path[len("/file-abs/"):]))
                if not _inside(p, ROOT / "assets", ROOT / "books", ROOT / "deliverables") or not p.is_file():
                    return self._err(404, "not found")
                return self._file(p)
            if u.path == "/api/pdf/info":
                import pymupdf
                p = _pdf_path(q["path"])
                with pymupdf.open(p) as doc:
                    first = doc[0].rect if len(doc) else None
                    return self._json({"pages": len(doc), "w": first.width if first else 0,
                                       "h": first.height if first else 0, "title": doc.metadata.get("title", "")})
            if u.path == "/api/pdf/page":
                import pymupdf
                p = _pdf_path(q["path"])
                n = int(q.get("n", 1))
                dpi = max(36, min(int(q.get("dpi", 96)), 200))
                with pymupdf.open(p) as doc:
                    png = doc[n - 1].get_pixmap(dpi=dpi).tobytes("png")
                return self._send(200, png, "image/png")
            if u.path == "/api/pdf/text":
                import pymupdf
                p = _pdf_path(q["path"])
                with pymupdf.open(p) as doc:
                    return self._json({"text": doc[int(q.get("n", 1)) - 1].get_text()})
            if u.path == "/api/pdf/notes":
                f = _notes_file(q["path"])
                return self._json(json.loads(f.read_text(encoding="utf-8")) if f.is_file() else [])
            return self._err(404, "not found")
        except PermissionError as e:
            return self._err(403, str(e))
        except (KeyError, ValueError, FileNotFoundError) as e:
            return self._err(400, f"{type(e).__name__}: {e}")

    def do_POST(self):  # noqa: N802
        u = urlparse(self.path)
        if SR.handles(u.path):
            return SR.handle(self, "POST")
        try:
            data = self._body()
            if u.path == "/api/loom":                      # a new book
                title = data.get("title", "").strip() or "Untitled"
                kind = data.get("kind", "layered")
                slug = L.slugify(data.get("slug") or title)
                if L.path(slug).exists():
                    return self._err(409, f"a book called {slug} already exists")
                if data.get("import") == "master-edition":
                    lm = L.import_master_edition()
                    lm["title"] = title or lm["title"]
                else:
                    threads = [t.strip() for t in data.get("threads", "").split(",") if t.strip()]
                    lm = L.new(title, kind, threads or None, data.get("author", ""))
                L.save(slug, lm)
                return self._json({"slug": slug})
            m = re.fullmatch(r"/api/loom/([a-z0-9-]+)/export", u.path)
            if m:
                out = L.export_pdf(L.load(m.group(1)), data.get("order", "by-level"), m.group(1))
                return self._json({"path": out.relative_to(ROOT).as_posix()})
            if u.path == "/api/pdf/notes":
                rel = data["path"]
                _pdf_path(rel)
                f = _notes_file(rel)
                f.parent.mkdir(parents=True, exist_ok=True)
                f.write_text(json.dumps(data.get("notes", []), indent=1, ensure_ascii=False), encoding="utf-8")
                return self._json({"ok": True})
            if u.path == "/api/pdf/place":                 # a PDF page as a picture for a book
                import pymupdf
                p = _pdf_path(data["path"])
                n = int(data.get("n", 1))
                slug = data["slug"]
                out = L.folder(slug) / "pictures" / f"{p.stem}-page-{n}.png"
                out.parent.mkdir(parents=True, exist_ok=True)
                with pymupdf.open(p) as doc:
                    doc[n - 1].get_pixmap(dpi=150).save(out)
                return self._json({"asset": out.relative_to(ROOT).as_posix()})
            return self._err(404, "not found")
        except PermissionError as e:
            return self._err(403, str(e))
        except (KeyError, ValueError) as e:
            return self._err(400, f"{type(e).__name__}: {e}")

    def do_PUT(self):  # noqa: N802
        if SR.handles(urlparse(self.path).path):
            return SR.handle(self, "PUT")
        m = re.fullmatch(r"/api/loom/([a-z0-9-]+)", urlparse(self.path).path)
        if not m:
            return self._err(404, "not found")
        try:
            L.save(m.group(1), self._body())
            return self._json({"ok": True})
        except ValueError as e:
            return self._err(400, str(e))


def serve(port: int = 8765, browser: bool = True) -> ThreadingHTTPServer:
    """Listen on ``port``, or the next free one if another program has it."""
    for candidate in ([port] if port == 0 else range(port, port + 20)):
        try:
            httpd = ThreadingHTTPServer(("127.0.0.1", candidate), Handler)
            break
        except OSError:
            continue
    else:
        raise OSError(f"no free port from {port} to {port + 19}")
    port = httpd.server_address[1]
    url = f"http://127.0.0.1:{port}/"
    print(f"Book Composer: {url}  (close this window to stop)")
    if browser:
        threading.Timer(0.6, lambda: webbrowser.open(url)).start()
    return httpd


def selftest() -> None:
    import tempfile
    import urllib.request

    L.selftest()
    with tempfile.TemporaryDirectory() as scratch:
        saved = L.BOOKS
        L.BOOKS = Path(scratch)
        httpd = serve(0, browser=False)
        port = httpd.server_address[1]
        t = threading.Thread(target=httpd.serve_forever, daemon=True)
        t.start()
        base = f"http://127.0.0.1:{port}"

        def call(method, path, body=None):
            req = urllib.request.Request(base + path, method=method,
                                         data=json.dumps(body).encode() if body is not None else None,
                                         headers={"Content-Type": "application/json"})
            with urllib.request.urlopen(req) as r:
                return json.loads(r.read())
        try:
            assert "<html" in urllib.request.urlopen(base + "/").read().decode().lower()
            slug = call("POST", "/api/loom", {"title": "Pip and the Log", "kind": "children",
                                              "threads": "Pip, Moss"})["slug"]
            lm = call("GET", f"/api/loom/{slug}")
            lm["cells"]["read/pip"]["title"] = "Pip finds a log"
            call("PUT", f"/api/loom/{slug}", lm)
            assert call("GET", f"/api/loom/{slug}")["cells"]["read/pip"]["title"] == "Pip finds a log"
            assert list((L.BOOKS / slug / ".history").glob("loom-*.json")), "the old copy was not kept"
            preview = urllib.request.urlopen(base + f"/api/loom/{slug}/preview?order=by-thread").read().decode()
            assert "Pip finds a log" in preview
            try:
                urllib.request.urlopen(base + "/file/../../Windows/win.ini")
                raise AssertionError("escaped the project")
            except urllib.error.HTTPError as e:
                assert e.code == 404
            sh = call("GET", "/api/shelf")
            assert any(b["key"] == "master" for b in sh["books"])
        finally:
            httpd.shutdown()
            L.BOOKS = saved
    print("composer selftest: ok")


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(prog="books.composer")
    ap.add_argument("--port", type=int, default=8765)
    ap.add_argument("--no-browser", action="store_true")
    ap.add_argument("--selftest", action="store_true")
    a = ap.parse_args(argv)
    if a.selftest:
        selftest()
        return 0
    httpd = serve(a.port, not a.no_browser)
    try:
        httpd.serve_forever()
    except KeyboardInterrupt:
        pass
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
