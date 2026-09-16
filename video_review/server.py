"""Loopback-only review UI with byte-range media streaming and disk persistence."""
from __future__ import annotations

from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
import json
import mimetypes
from pathlib import Path
import re
import secrets
from urllib.parse import parse_qs, urlsplit

from .model import ReviewStore

STATIC = Path(__file__).parent / "static"


def make_server(root, port=0, library=None):
    store = ReviewStore(root, library)
    token = secrets.token_urlsafe(32)

    class Handler(BaseHTTPRequestHandler):
        def log_message(self, *_args):
            pass

        def send_bytes(self, data, kind="application/json", status=200, headers=None):
            self.send_response(status)
            self.send_header("Content-Type", kind)
            self.send_header("Content-Length", str(len(data)))
            self.send_header("Cache-Control", "no-store")
            self.send_header("X-Content-Type-Options", "nosniff")
            self.send_header("Referrer-Policy", "no-referrer")
            self.send_header("Content-Security-Policy", "default-src 'self'; script-src 'self'; style-src 'self'; media-src 'self'; img-src 'self' data:; object-src 'none'; frame-ancestors 'none'")
            for key, value in (headers or {}).items():
                self.send_header(key, value)
            self.end_headers()
            if self.command != "HEAD":
                self.wfile.write(data)

        def json(self, value, status=200):
            self.send_bytes(json.dumps(value, ensure_ascii=False, allow_nan=False).encode(), status=status)

        def valid_host(self):
            return self.headers.get("Host") in {f"127.0.0.1:{self.server.server_port}", f"localhost:{self.server.server_port}"}

        def do_HEAD(self):
            self.do_GET()

        def do_GET(self):
            try:
                if not self.valid_host():
                    self.json({"error": "Local requests only"}, 403)
                    return
                url = urlsplit(self.path)
                query = parse_qs(url.query)
                path = url.path
                if path in ("/", "/app.js", "/style.css"):
                    asset = STATIC / ("index.html" if path == "/" else path[1:])
                    kind = {"/": "text/html; charset=utf-8", "/app.js": "text/javascript; charset=utf-8", "/style.css": "text/css; charset=utf-8"}[path]
                    self.send_bytes(asset.read_bytes(), kind)
                elif path == "/api/bootstrap":
                    self.json({"token": token, "root": str(store.root), "reviews": store.listing(), "videos": store.videos()})
                elif path == "/api/review":
                    number = int(query["round"][0]) if "round" in query else None
                    self.json(store.state(query["id"][0], number))
                elif path == "/media":
                    self.media(store.media(query["id"][0], int(query["round"][0])))
                elif path == "/artifact":
                    filename = query["file"][0]
                    if filename not in {"revision.json", "script-before.md", "script-updated.md", "action-list.md", "next-build-prompt.md"}:
                        raise ValueError("Unknown artifact")
                    packet = store.packet_path(query["id"][0], int(query["round"][0]), int(query["packet"][0]))
                    self.send_bytes((packet.parent / filename).read_bytes(), "text/plain; charset=utf-8")
                else:
                    self.json({"error": "Not found"}, 404)
            except (ValueError, KeyError, OSError, TypeError) as exc:
                self.json({"error": str(exc)}, 400)
            except (BrokenPipeError, ConnectionResetError):
                pass

        def do_POST(self):
            try:
                origin = self.headers.get("Origin")
                if (not self.valid_host() or self.headers.get("X-Review-Token") != token
                        or (origin and origin != f"http://{self.headers.get('Host')}")):
                    self.json({"error": "Reload the local review page before saving"}, 403)
                    return
                length = int(self.headers.get("Content-Length", "0"))
                if not 0 < length <= 2000000:
                    raise ValueError("Request too large or empty")
                data = json.loads(self.rfile.read(length))
                path = urlsplit(self.path).path
                if path == "/api/create":
                    result = store.create(data)
                elif path == "/api/note":
                    result = store.save_note(data.get("project_id") or data["id"], data["round"],
                                             dict(data, id=data.get("note_id")))
                elif path == "/api/packet":
                    result = store.build_packet(data["id"], data["round"], data["revision"])
                elif path == "/api/advance":
                    result = store.advance(data["id"], data["round"], data)
                else:
                    self.json({"error": "Not found"}, 404)
                    return
                self.json(result)
            except (ValueError, KeyError, OSError, TypeError) as exc:
                self.json({"error": str(exc)}, 400)

        def media(self, path):
            size = path.stat().st_size
            start, end, status = 0, size - 1, 200
            value = self.headers.get("Range")
            if value:
                match = re.fullmatch(r"bytes=(\d*)-(\d*)", value)
                if not match or not any(match.groups()):
                    self.send_bytes(b"", status=416, headers={"Content-Range": f"bytes */{size}"})
                    return
                first, last = match.groups()
                if first:
                    start = int(first)
                    end = min(int(last), size - 1) if last else size - 1
                else:
                    start = max(0, size - int(last))
                if start >= size or start > end:
                    self.send_bytes(b"", status=416, headers={"Content-Range": f"bytes */{size}"})
                    return
                status = 206
            self.send_response(status)
            self.send_header("Content-Type", mimetypes.guess_type(path.name)[0] or "video/mp4")
            self.send_header("Accept-Ranges", "bytes")
            self.send_header("Content-Length", str(max(0, end - start + 1)))
            self.send_header("Cache-Control", "no-store")
            if status == 206:
                self.send_header("Content-Range", f"bytes {start}-{end}/{size}")
            self.end_headers()
            if self.command == "HEAD":
                return
            try:
                with path.open("rb") as stream:
                    stream.seek(start)
                    remaining = end - start + 1
                    while remaining > 0:
                        chunk = stream.read(min(256 * 1024, remaining))
                        if not chunk:
                            break
                        self.wfile.write(chunk)
                        remaining -= len(chunk)
            except (BrokenPipeError, ConnectionResetError):
                pass

    server = ThreadingHTTPServer(("127.0.0.1", port), Handler)
    server.daemon_threads = True
    server.review_store = store
    return server
