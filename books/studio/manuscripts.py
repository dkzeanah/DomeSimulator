"""The shelf's manuscript books in the Book Studio: their chapters, their builds, their newest PDF.

The books already written keep their own engines (books.shelf): their words are Markdown files in
a folder, and a command prints a new numbered PDF. The studio edits those files in place -- every
save keeps the previous copy in ``books/.studio-versions/`` -- and runs the book's own build in the
background, so the result is always the engine's, not a second typesetting of it.
"""

from __future__ import annotations

import datetime as dt
import re
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
    # the manuscript's own chapters first, then the book's working notes (prompts, ledgers)
    for p in sorted(folder.rglob("*.md"), key=lambda q: ("manuscript" not in q.relative_to(folder).parts, q.as_posix())):
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


# ----------------------------------------------------------------------
# Pictures in a chapter: what each image link shows, and swapping one
# ----------------------------------------------------------------------

IMAGE_LINK = re.compile(r"!\[(?P<alt>[^\]]*)\]\((?P<src>[^)\s]+)\)")


def _figure_dir(chapter: Path, src: str) -> Path:
    """The folder an image link's pictures live in (through the numbered library for old addresses)."""
    parts = Path(src.split("?")[0]).parts
    if "deliverables" in parts:                    # the engines read these from the project root
        d = ROOT.joinpath(*parts[parts.index("deliverables"):]).parent
    else:
        d = (chapter.parent / src).resolve().parent
    if "deliverables" in d.parts:
        import medialib
        d = medialib.locate(d)
    return d


def _resolve(chapter: Path, src: str) -> Path | None:
    """The picture an image link shows, the way the book engines find it: the newest version of
    that name in its folder (two_v_demo.book_export.latest_figure), or the file itself."""
    stem = Path(src.split("?")[0]).stem
    try:
        from two_v_demo.book_export import latest_figure
        got = latest_figure(stem, _figure_dir(chapter, src))
        if got:
            return got
    except Exception:
        pass
    p = (chapter.parent / src).resolve()
    return p if p.is_file() else None


def pictures(key: str, rel: str) -> list[dict]:
    p = _check(key, rel)
    out = []
    for i, m in enumerate(IMAGE_LINK.finditer(p.read_text(encoding="utf-8"))):
        f = _resolve(p, m.group("src"))
        out.append({"index": i, "alt": m.group("alt"), "src": m.group("src"), "name": Path(m.group("src")).stem,
                    "file": f.relative_to(ROOT).as_posix() if f and f.is_relative_to(ROOT) else None})
    return out


def swap_picture(key: str, rel: str, index: int, asset: str, alt: str | None = None) -> dict:
    """Show a library picture in place of the chapter's ``index``-th image. The picture is filed in
    the book's figures folder under its own name (a new file; nothing is overwritten) and the link
    is changed to point at it, so the book's own build finds it the way it finds every figure."""
    import shutil
    p = _check(key, rel)
    text = p.read_text(encoding="utf-8")
    links = list(IMAGE_LINK.finditer(text))
    if not 0 <= index < len(links):
        raise ValueError(f"the chapter has {len(links)} pictures")
    m = links[index]
    src_asset = (ROOT / asset).resolve()
    if not src_asset.is_relative_to((ROOT / "assets").resolve()) or not src_asset.is_file():
        raise PermissionError("pictures come from the asset library")
    if src_asset.suffix.lower() not in (".png", ".svg", ".jpg"):
        raise ValueError("the book's engine takes .png, .svg or .jpg")
    folder = _figure_dir(p, m.group("src"))
    folder.mkdir(parents=True, exist_ok=True)
    stem, n = src_asset.stem, 1
    target = folder / f"{stem}{src_asset.suffix.lower()}"
    # a different picture already filed under that name: take the next free name, never overwrite
    while target.exists() and target.read_bytes() != src_asset.read_bytes():
        n += 1
        target = folder / f"{stem}-alt{n}{src_asset.suffix.lower()}"
    if not target.exists():
        shutil.copyfile(src_asset, target)
    new_src = str(Path(m.group("src")).parent / target.name).replace("\\", "/")
    new_link = f"![{m.group('alt') if alt is None else alt}]({new_src})"
    out = write(key, rel, text[:m.start()] + new_link + text[m.end():])
    return {**out, "src": new_src, "filed": target.relative_to(ROOT).as_posix(), "was": m.group("src")}
