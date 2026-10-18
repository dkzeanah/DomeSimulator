"""The shelf's manuscript books in the Book Studio: their chapters, their builds, their newest PDF.

The books already written keep their own engines (books.shelf): their words are Markdown files in
a folder, and a command prints a new numbered PDF. The studio edits those files in place -- every
save keeps the previous copy in ``books/.studio-versions/`` -- and runs the book's own build in the
background, so the result is always the engine's, not a second typesetting of it.
"""

from __future__ import annotations

import datetime as dt
import shlex
import subprocess
import sys
import threading
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from books import shelf as S  # noqa: E402

VERSIONS = ROOT / "books" / ".studio-versions"
SKIP = {".versions", ".studio-versions", "__pycache__", "node_modules"}


def book(key: str) -> S.Book:
    if key not in S.BY_KEY:
        raise ValueError(f"no book {key!r} on the shelf")
    return S.BY_KEY[key]


def chapters(key: str) -> list[dict]:
    b = book(key)
    folder = ROOT / b.words
    if not folder.is_dir():
        return []
    out = []
    for p in sorted(folder.rglob("*.md")):
        if any(part in SKIP for part in p.parts):
            continue
        rel = p.relative_to(ROOT).as_posix()
        text = p.read_text(encoding="utf-8", errors="replace")
        first = _title(text, p.stem)
        out.append({"path": rel, "title": first[:120], "words": len(text.split()), "folder": p.parent.relative_to(folder).as_posix()})
    return out


def _title(text: str, fallback: str) -> str:
    """A chapter's title: its front matter's title, else its first heading, else its first line."""
    import re
    m = re.match(r"---\s*\n(.*?)\n---", text, re.S)
    if m:
        t = re.search(r"^title:\s*(.+)$", m.group(1), re.M)
        if t:
            return t.group(1).strip().strip("'\"")
        text = text[m.end():]
    h = re.search(r"^#{1,6}\s+(.+)$", text, re.M)
    if h:
        return h.group(1).strip()
    return next((ln.strip() for ln in text.splitlines() if ln.strip()), fallback)


def _check(key: str, rel: str) -> Path:
    b = book(key)
    p = (ROOT / rel).resolve()
    if not p.is_relative_to((ROOT / b.words).resolve()) or p.suffix != ".md":
        raise PermissionError(f"{rel} is not one of {b.title}'s Markdown files")
    return p


def read(key: str, rel: str) -> str:
    return _check(key, rel).read_text(encoding="utf-8")


def write(key: str, rel: str, text: str) -> dict:
    p = _check(key, rel)
    old = p.read_text(encoding="utf-8") if p.exists() else ""
    if old == text:
        return {"saved": False}
    keep = VERSIONS / rel
    keep.mkdir(parents=True, exist_ok=True)
    (keep / f"{dt.datetime.now().strftime('%Y%m%d-%H%M%S')}.md").write_text(old, encoding="utf-8")
    p.write_text(text, encoding="utf-8")
    return {"saved": True, "words": len(text.split())}


def replace(key: str, rel: str, find: str, repl: str) -> dict:
    text = read(key, rel)
    n = text.count(find)
    if not n:
        raise ValueError(f"{find[:60]!r} is not in {rel}")
    return {**write(key, rel, text.replace(find, repl)), "replaced": n}


# ----------------------------------------------------------------------
# Builds, in the background
# ----------------------------------------------------------------------

JOBS: dict[str, dict] = {}


def build(key: str) -> dict:
    b = book(key)
    job = JOBS.get(key)
    if job and job["state"] == "running":
        return job
    cmd = shlex.split(b.build.replace("py -3.12", f'"{sys.executable}"'), posix=False)
    cmd = [c.strip('"') for c in cmd]
    job = {"key": key, "command": b.build, "state": "running", "log": "", "started": time.time(), "ended": None, "code": None}
    JOBS[key] = job

    def run():
        try:
            p = subprocess.Popen(cmd, cwd=ROOT, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True, encoding="utf-8", errors="replace")
            for line in p.stdout:
                job["log"] = (job["log"] + line)[-20000:]
            job["code"] = p.wait()
            job["state"] = "done" if job["code"] == 0 else "failed"
        except OSError as e:
            job["log"] += f"\n{e}"
            job["state"] = "failed"
        job["ended"] = time.time()

    threading.Thread(target=run, daemon=True).start()
    return job


def latest_pdf(key: str) -> str | None:
    b = book(key)
    p = b.latest() if b.output else None
    return p.relative_to(ROOT).as_posix() if p else None
