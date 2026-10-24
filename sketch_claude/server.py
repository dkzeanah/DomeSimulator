"""The Dome Sketch app's local server: the page, the model as JSON, and the plan and render jobs.

    GET  /                       the app
    GET  /static/<file>          its script, styles and three.js
    GET  /api/defaults           the default spec, the presets and the declared inputs
    POST /api/model              {spec} -> every piece's geometry, and the tables
    POST /api/plans              {spec} -> start a plan-set PDF job
    POST /api/showcase           {spec} -> start a showcase-renders job
    GET  /api/jobs               the jobs and how they are going
    GET  /api/outputs            the plan sets and showcases made so far
    GET  /api/file?path=...      a file from deliverables/, to open in the browser

Bound to 127.0.0.1 only. Jobs run as separate processes (``py -m sketch_claude plans``) so a
long render never blocks the page, and every output is a new numbered folder.
"""

from __future__ import annotations

import base64
import json
import mimetypes
import subprocess
import sys
import threading
import time
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import parse_qs, urlparse

import numpy as np

from . import TAG
from . import model as M

HERE = Path(__file__).resolve().parent
STATIC = HERE / "static"
ROOT = HERE.parent
PORT = 8767
EPISODES = HERE / "episodes"


def _season_id(sid: str) -> str:
    import re as _re
    if not _re.fullmatch(r"season\d{2}", sid):
        raise ValueError("seasons are named like season01")
    return sid


def _episode_file(eid: str) -> Path:
    import re as _re
    if not _re.fullmatch(r"s\d{2}e\d{2}", eid):
        raise ValueError("episodes are named like s01e01")
    return EPISODES / f"{eid}.json"

PRESETS = {
    "reference": {"label": "16 ft reference (4.88 m)", "spec": {"frequency": 3, "cut": "5/8", "diameter_m": M.D("diameter_m")}},
    "4m": {"label": "4 m, 3V 5/8", "spec": {"frequency": 3, "cut": "5/8", "diameter_m": 4.0}},
    "15ft": {"label": "15 ft (4.57 m), 3V 5/8", "spec": {"frequency": 3, "cut": "5/8", "diameter_m": 15 * M.FT}},
    "5m": {"label": "5 m, 3V 5/8", "spec": {"frequency": 3, "cut": "5/8", "diameter_m": 5.0}},
    "6m": {"label": "6 m, 3V 5/8", "spec": {"frequency": 3, "cut": "5/8", "diameter_m": 6.0}},
    "2v": {"label": "2V hemisphere, 4 m", "spec": {"frequency": 2, "cut": "1/2", "diameter_m": 4.0}},
    "4v": {"label": "4V 5/8, 7 m", "spec": {"frequency": 4, "cut": "5/8", "diameter_m": 7.0}},
}


def _b64(a: np.ndarray, dtype) -> str:
    return base64.b64encode(np.ascontiguousarray(a, dtype=dtype).tobytes()).decode("ascii")


def _clean(v):
    """Make a table value JSON-safe (numpy numbers, tuples, nested dicts)."""
    if isinstance(v, dict):
        return {str(k): _clean(x) for k, x in v.items()}
    if isinstance(v, (list, tuple, set)):
        return [_clean(x) for x in v]
    if isinstance(v, (np.floating,)):
        return float(v)
    if isinstance(v, (np.integer,)):
        return int(v)
    if isinstance(v, np.bool_):
        return bool(v)
    if isinstance(v, np.ndarray):
        return v.tolist()
    if isinstance(v, float) and (v != v):
        return None
    return v


def scene(spec: M.Spec) -> dict:
    m = M.build(spec)
    mark = {pid: r["mark"] for r in m.tables["sticks"] for pid in r["ids"]}
    pieces = []
    for p in m.pieces:
        if not len(p.mesh.verts):
            continue
        info = {k: v for k, v in p.info.items() if k not in ("outline_yz",)}
        if p.id in mark:
            info["mark"] = mark[p.id]
        pieces.append({
            "id": p.id, "name": p.name, "tag": p.tag, "material": p.material, "group": p.group, "step": p.step,
            "explode": [float(x) for x in p.explode], "info": _clean(info),
            "v": _b64(p.mesh.verts, "<f4"), "t": _b64(p.mesh.tris, "<u4"), "e": _b64(p.mesh.edges, "<u4"),
        })
    t = m.tables
    keep = ("title", "frequency", "cut", "diameter_m", "height_m", "inside_height_m", "floor_m2", "base_edges", "tapered", "level",
            "taper_m", "panels", "whole", "partial", "windows", "skylights", "stick_count", "stick_m", "boards", "rings", "bevel_lo",
            "bevel_hi", "sheets", "skin_m2", "glass_m2", "seam_m", "screws_corner", "screws_seam", "staples", "tape_m", "deck_m2",
            "base_mitre", "warnings", "chords")
    tables = {k: _clean(t[k]) for k in keep}
    tables["classes"] = _clean([{k: c[k] for k in ("name", "kind", "letters", "sides_m", "angles", "bevels", "count", "built", "height_m", "area_m2")}
                                for c in t["classes"]])
    tables["sticks"] = _clean([{k: r[k] for k in ("mark", "cls", "side", "kind", "count", "long_m", "head_mitre", "head_bevel",
                                                  "tail_mitre", "rip_deg", "panels")} for r in t["sticks"]])
    tables["door"] = _clean({k: v for k, v in (t["door"] or {}).items() if k != "cards"}) if t["door"] else None
    tables["base_sections"] = _clean(t["base_sections"])
    return {"spec": spec.to_dict(), "pieces": pieces, "tables": tables, "materials": M.MATERIALS,
            "landmarks": _clean(m.landmarks), "max_step": max(p.step for p in m.pieces)}


# ----------------------------------------------------------------------
# Jobs
# ----------------------------------------------------------------------

JOBS: dict[str, dict] = {}


def start_job(kind: str, spec: M.Spec, extra: list[str] | None = None) -> dict:
    jid = f"{kind}-{int(time.time() * 1000)}"
    cmd = [sys.executable, "-m", "sketch_claude", kind, "--spec", json.dumps(spec.to_dict()), *(extra or [])]
    job = {"id": jid, "kind": kind, "state": "running", "log": "", "started": time.time(), "ended": None, "output": None,
           "title": spec.title}
    JOBS[jid] = job

    def run():
        try:
            p = subprocess.Popen(cmd, cwd=ROOT, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True,
                                 encoding="utf-8", errors="replace")
            for line in p.stdout:
                job["log"] = (job["log"] + line)[-12000:]
                if line.startswith("OUTPUT "):
                    job["output"] = line[7:].strip()
            code = p.wait()
            job["state"] = "done" if code == 0 else "failed"
        except OSError as e:
            job["log"] += f"\n{e}"
            job["state"] = "failed"
        job["ended"] = time.time()

    threading.Thread(target=run, daemon=True).start()
    return job


def outputs() -> list[dict]:
    import medialib
    out = []
    import medialib as _ml
    slugs = {o.slug for o in _ml.outputs() if o.slug.startswith(TAG)}
    for slug in sorted(slugs):
        for o in medialib.outputs(slug):
            folder = Path(o.folder) if hasattr(o, "folder") else None
            files = sorted(p for p in (folder.iterdir() if folder and folder.is_dir() else []) if p.suffix.lower() in (".pdf", ".png", ".jpg", ".md"))
            out.append({"slug": slug, "folder": folder.relative_to(ROOT).as_posix() if folder else "",
                        "files": [f.relative_to(ROOT).as_posix() for f in files]})
    return out


# ----------------------------------------------------------------------
# HTTP
# ----------------------------------------------------------------------

class Handler(BaseHTTPRequestHandler):
    server_version = "DomeSketch/1"

    def log_message(self, fmt, *args):     # quiet
        pass

    def _send(self, code: int, body: bytes, ctype: str):
        self.send_response(code)
        self.send_header("Content-Type", ctype)
        self.send_header("Content-Length", str(len(body)))
        self.send_header("Cache-Control", "no-store")
        self.end_headers()
        self.wfile.write(body)

    def _json(self, obj, code: int = 200):
        self._send(code, json.dumps(obj).encode("utf-8"), "application/json")

    def _err(self, code: int, msg: str):
        self._json({"error": msg}, code)

    def _body(self) -> dict:
        n = int(self.headers.get("Content-Length") or 0)
        return json.loads(self.rfile.read(n) or b"{}")

    def _file(self, f: Path):
        ctype = mimetypes.guess_type(f.name)[0] or "application/octet-stream"
        if f.suffix == ".js":
            ctype = "text/javascript"
        self._send(200, f.read_bytes(), ctype)

    def do_GET(self):
        u = urlparse(self.path)
        q = {k: v[0] for k, v in parse_qs(u.query).items()}
        try:
            if u.path in ("/", "/index.html"):
                return self._file(STATIC / "index.html")
            if u.path in ("/director", "/director/"):
                return self._file(STATIC / "director.html")
            if u.path in ("/season", "/season/"):
                return self._file(STATIC / "season.html")
            if u.path in ("/lesson", "/lesson/"):
                return self._file(STATIC / "lesson.html")
            if u.path.startswith("/api/lesson/"):
                from . import lesson_web as L
                return self._json(L.public_spec(u.path.rsplit("/", 1)[1]))
            if u.path.startswith("/api/season/"):
                from . import writers as WR
                parts = u.path.split("/")[3:]
                sid = _season_id(parts[0])
                if len(parts) == 1:
                    return self._file(EPISODES / f"{sid}.json")
                if parts[1] == "coverage":
                    return self._json(WR.coverage(sid))
            if u.path == "/api/series":
                return self._file(EPISODES / "series.json")
            if u.path == "/api/episodes":
                eps = []
                for f in sorted(EPISODES.glob("s[0-9][0-9]e[0-9][0-9].json")):
                    d = json.loads(f.read_text(encoding="utf-8"))
                    eps.append({"id": d["id"], "number": d.get("number", d["id"]), "title": d.get("title", ""), "status": d.get("status", "scripted")})
                return self._json(eps)
            if u.path.startswith("/api/episode/"):
                f = _episode_file(u.path.rsplit("/", 1)[1])
                return self._file(f) if f.is_file() else self._err(404, "no such episode")
            if u.path.startswith("/static/"):
                f = (STATIC / u.path[len("/static/"):]).resolve()
                if not f.is_relative_to(STATIC) or not f.is_file():
                    return self._err(404, "not found")
                return self._file(f)
            if u.path == "/api/defaults":
                return self._json({"spec": M.Spec().to_dict(), "presets": PRESETS, "tag": TAG,
                                   "cuts": [{"frequency": f, "cut": c} for f, c in M.CUTS],
                                   "declared": {k: {"value": d.value, "unit": d.unit, "why": d.why, "kind": d.kind} for k, d in M.DECLARED.items()}})
            if u.path == "/api/jobs":
                return self._json(sorted(JOBS.values(), key=lambda j: -j["started"]))
            if u.path == "/api/outputs":
                return self._json(outputs())
            if u.path == "/api/file":
                f = (ROOT / q.get("path", "")).resolve()
                if not f.is_relative_to((ROOT / "deliverables").resolve()) or not f.is_file():
                    return self._err(403, "only files in deliverables/")
                return self._file(f)
            return self._err(404, "not found")
        except Exception as e:      # the page shows the message
            return self._err(500, f"{type(e).__name__}: {e}")

    def do_PUT(self):
        u = urlparse(self.path)
        try:
            if u.path.startswith("/api/season/"):
                from . import writers as WR
                sid = _season_id(u.path.split("/")[3])
                d = self._body()
                if not isinstance(d.get("episodes"), list):
                    return self._err(400, "a season needs a list of episodes")
                return self._json({"ok": True, "kept": WR.save(sid, d)})
            if u.path.startswith("/api/episode/"):
                f = _episode_file(u.path.rsplit("/", 1)[1])
                d = self._body()
                if not isinstance(d.get("beats"), list):
                    return self._err(400, "an episode needs a list of beats")
                kept = None
                if f.exists():
                    import datetime as _dt
                    keep = EPISODES / ".versions"
                    keep.mkdir(exist_ok=True)
                    kept = keep / f"{f.stem}-{_dt.datetime.now().strftime('%Y%m%d-%H%M%S')}.json"
                    kept.write_bytes(f.read_bytes())
                f.write_text(json.dumps(d, indent=1, ensure_ascii=False), encoding="utf-8")
                return self._json({"ok": True, "kept": kept.relative_to(ROOT).as_posix() if kept else None})
            return self._err(404, "not found")
        except Exception as e:
            return self._err(400, f"{type(e).__name__}: {e}")

    def do_POST(self):
        u = urlparse(self.path)
        try:
            if u.path.startswith("/api/render/"):
                from . import episode_server as E
                q = {k: v[0] for k, v in parse_qs(u.query).items()}
                n = int(self.headers.get("Content-Length") or 0)
                raw = self.rfile.read(n)
                if u.path == "/api/render/start":
                    b = json.loads(raw or b"{}")
                    return self._json(E.render_start(b.get("slug", "take"), int(b.get("fps", 30)), bool(b.get("draft"))))
                if u.path == "/api/render/frame":
                    return self._json(E.render_frame(q["id"], raw, int(q["n"])))
                if u.path == "/api/render/finish":
                    k = int.from_bytes(raw[:4], "little")
                    meta = json.loads(raw[4:4 + k].decode("utf-8"))
                    return self._json(E.render_finish(meta["id"], raw[4 + k:], meta))
                if u.path == "/api/render/abort":
                    return self._json(E.render_abort(q.get("id", "")))
            if u.path in ("/api/lesson-finish", "/api/lesson-still"):
                from . import lesson_web as L
                q = {k: v[0] for k, v in parse_qs(u.query).items()}
                raw = self.rfile.read(int(self.headers.get("Content-Length") or 0))
                if u.path == "/api/lesson-still":
                    return self._json(L.save_still(q["lesson"], q.get("orient", "landscape"), int(q["n"]), raw))
                return self._json(L.finish(q["id"], json.loads(raw or b"{}")))
            if u.path == "/api/recording":
                from . import episode_server as E
                n = int(self.headers.get("Content-Length") or 0)
                raw = self.rfile.read(n)
                k = int.from_bytes(raw[:4], "little")
                meta = json.loads(raw[4:4 + k].decode("utf-8"))
                return self._json(E.save_recording(raw[4 + k:], meta))
            b = self._body()
            if u.path == "/api/voice":
                from . import episode_server as E
                f = E.voice(b["text"], b.get("voice", "en-US-GuyNeural"), b.get("rate", "+0%"), b.get("pitch", "+0Hz"))
                return self._send(200, f.read_bytes(), "audio/mpeg")
            if u.path == "/api/set":
                from . import episode_server as E
                return self._json(E.set_pieces(M.Spec.from_dict(b.get("spec") or {})))
            spec = M.Spec.from_dict(b.get("spec") or {})
            if u.path == "/api/model":
                return self._json(scene(spec))
            if u.path == "/api/plans":
                return self._json(start_job("plans", spec))
            if u.path == "/api/showcase":
                return self._json(start_job("showcase", spec))
            if u.path.startswith("/api/season/"):
                from . import writers as WR
                parts = u.path.split("/")[3:]
                sid, what, eid = _season_id(parts[0]), parts[1], str(b.get("episode", ""))
                _episode_file(eid)
                if what == "skeleton":
                    if (EPISODES / f"{eid}.json").exists() and not b.get("replace"):
                        return self._err(409, f"{eid} already has a script; pass replace to keep it as a version and start again")
                    ep = WR.skeleton(sid, eid)
                    return self._json({"ok": True, "kept": WR.save(eid, ep), "beats": len(ep["beats"])})
                if what == "draft":
                    ep = WR.draft(sid, eid)
                    kept = WR.save(eid, ep)
                    return self._json({"ok": True, "kept": kept, "beats": len(ep["beats"]), "notes": ep.get("draft_notes", [])})
                return self._err(404, "not found")
            if u.path == "/api/episode-render":
                extra = ["--episode", str(b.get("episode", "s01e01"))] + (["--draft"] if b.get("draft") else [])
                return self._json(start_job("episode", spec, extra))
            if u.path == "/api/episode":
                return self._json(start_job("episode", spec, ["--draft"] if b.get("draft") else []))
            return self._err(404, "not found")
        except Exception as e:
            print(f"[server] {u.path}: {type(e).__name__}: {e}", flush=True)
            return self._err(400, f"{type(e).__name__}: {e}")


def serve(port: int = PORT) -> ThreadingHTTPServer:
    return ThreadingHTTPServer(("127.0.0.1", port), Handler)
