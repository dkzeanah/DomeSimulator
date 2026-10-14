"""One library for everything the project makes: films, books, PDFs, stills, packs.

    py -3.12 -m medialib                 # rebuild the index (deliverables/INDEX.md + index.html)
    py -3.12 -m medialib find wedge      # every item whose name contains "wedge"
    py -3.12 -m medialib latest the-40-hour-cabin-the-case --ext .pdf
    py -3.12 -m medialib migrate         # dry run: what would move in from the old folders
    py -3.12 -m medialib migrate --go    # move it, writing a manifest of every move
    py -3.12 -m medialib selftest

The layout is by date, one folder per *item*, every version of the item squashed
into that one folder::

    deliverables/
        2026-10-14/
            beyond-the-dome-building-with-wedges/
                beyond-the-dome-building-with-wedges.mp4
                beyond-the-dome-building-with-wedges-v2.mp4
                beyond-the-dome-building-with-wedges-v2-vertical.mp4
                beyond-the-dome-building-with-wedges-v2.srt  ...
                releases/beyond-the-dome-building-with-wedges-v2/   (thumbnails, description.md)
        INDEX.md      index.html      _moves/

An item is named by its *slug*: the file name with its version (``-v3``) and its
companion suffixes (``-vertical``, ``-narration``, ``-review``, ``-p1``...) taken off,
so a cut, its phone cut, its captions and every later version live together. The
item's date folder is the day it was first made; a version made a month later
still goes into the same folder (that is the squashing -- nothing is deleted), and
the index lists it under the day it was made as well.

The old kind folders (``deliverables/book``, ``deliverables/masterclass``,
``exports``...) are now *addresses*, not places. Code may still ask for
``deliverables/book/x.pdf``; :func:`address` says which item that is and where in
the item's folder it belongs, and both the one-time move (:func:`migrate`) and every
new write (:func:`route`, through :func:`two_v_demo.deliverables.next_version_path`)
use that one rule.

Nothing in here overwrites anything: a new file always gets a name that does not
exist yet, climbing above the highest version ever made (the rule in CLAUDE.md).
"""

from __future__ import annotations

import argparse
import datetime as dt
import html
import os
import re
import shutil
from dataclasses import dataclass, field
from pathlib import Path

ROOT = Path(__file__).resolve().parent
LIBRARY = ROOT / "deliverables"
MOVES = LIBRARY / "_moves"
DAY = re.compile(r"^\d{4}-\d{2}-\d{2}$")
# Folders that used to hold output, by kind. Everything in them belongs in the library.
LEGACY = (LIBRARY, ROOT / "exports")
LEGACY_SKIP = {"scratchpad", "_moves", "tasks"}  # exports/scratchpad and tasks are working files, not output
LIBRARY_FILES = {"INDEX.md", "index.html", "README.md"}
# Old kind folders that are one piece of work each (a project with its own scripts,
# sources and outputs): they move whole, as one item.
PROJECTS = {"byod", "byod-deepseek", "byod-styled", "launcher_trailer", "tree-value-video", "rap_demo"}
# Sub-folders whose name says nothing by itself: the item is named after its kind too.
GENERIC = {"plates", "all", "final", "output", "build", "audio", "video", "stills", "frames", "out", "shots"}
_STAMP = re.compile(r"_\d{8}_\d{6}")

# Companion suffixes, taken off the end of a name (repeatedly) to find its item.
_TAILS = re.compile(
    r"(-narration-plan|-narration|-review|-youtube|-vertical|-landscape|-portrait|-silent"
    r"|-captions|-thumb(?:nail)?s?|-p\d{1,3}|-v\d+|-myvoice(?:-x[\d.]+)?|-voice-.+|-voice)$")
_VERSION = re.compile(r"-v(\d+)(?=$|-)")

KINDS = {
    ".mp4": "video", ".mkv": "video", ".mov": "video", ".webm": "video",
    ".m4a": "audio", ".wav": "audio", ".mp3": "audio",
    ".pdf": "document", ".md": "text", ".txt": "text", ".html": "page", ".srt": "captions",
    ".png": "image", ".jpg": "image", ".jpeg": "image", ".webp": "image", ".svg": "image", ".gif": "image",
    ".json": "data", ".csv": "data", ".tsv": "data", ".zip": "archive", ".docx": "document",
    ".pptx": "slides", ".epub": "book", ".py": "code",
}
# The kind an item is listed under: the most telling kind among its files.
_PRIORITY = ("video", "book", "document", "slides", "page", "image", "audio", "archive", "text",
             "captions", "data", "code")


def _split_ext(name: str) -> tuple[str, str]:
    suffix = Path(name).suffix
    if suffix and len(suffix) <= 6 and (suffix.lower() in KINDS or suffix[1:].isalpha()):
        return name[: -len(suffix)], suffix
    return name, ""


def slug_of(name: str) -> str:
    """The item a file or folder name belongs to."""
    stem, _ = _split_ext(name)
    while True:
        cut = _TAILS.sub("", stem)
        if cut == stem or not cut:
            break
        stem = cut
    return stem


def version_of(name: str) -> int:
    found = _VERSION.findall(_split_ext(name)[0])
    return int(found[-1]) if found else 1


def kind_of(path: Path) -> str:
    if path.is_dir():
        if path.parent.name == "releases":
            return "release"
        if path.name == "releases":
            return "releases"
        return "voice" if "-voice" in path.name or "-myvoice-" in path.name else "folder"
    return KINDS.get(path.suffix.lower(), "other")


# ---------------------------------------------------------------------------
# Where things are


def days() -> list[Path]:
    if not LIBRARY.is_dir():
        return []
    return sorted(p for p in LIBRARY.iterdir() if p.is_dir() and DAY.match(p.name))


def item_dir(slug: str) -> Path | None:
    """The folder that holds ``slug``, wherever (whichever day) it was first made."""
    for day in days():
        if (day / slug).is_dir():
            return day / slug
    return None


def today() -> str:
    return dt.date.today().isoformat()


def is_library_path(path: str | Path) -> bool:
    try:
        rel = _abs(path).relative_to(LIBRARY.resolve())
    except ValueError:
        return False
    return bool(rel.parts) and bool(DAY.match(rel.parts[0]))


def _abs(path: str | Path) -> Path:
    p = Path(path)
    return (p if p.is_absolute() else ROOT / p).resolve()


def _legacy_rel(path: str | Path) -> tuple[Path, ...] | None:
    """The parts of ``path`` below the old output root it is in, or None."""
    p = _abs(path)
    if is_library_path(p):
        return None
    for root in LEGACY:
        try:
            rel = p.relative_to(root.resolve())
        except ValueError:
            continue
        if not rel.parts or rel.parts[0] in LEGACY_SKIP or rel.parts[0] in LIBRARY_FILES:
            return None
        if root == LIBRARY and DAY.match(rel.parts[0]):
            return None
        return rel.parts
    return None


def is_legacy_path(path: str | Path) -> bool:
    """A path under one of the old output folders (``deliverables/book``, ``exports``...)."""
    return _legacy_rel(path) is not None


def _is_voice(name: str) -> bool:
    return "-voice" in name or "-myvoice-" in name


def _is_project(kind: str) -> bool:
    return kind in PROJECTS or bool(_STAMP.search(kind))


def address(path: str | Path) -> tuple[str, Path] | None:
    """For a path in an old output folder: (the item it belongs to, where it goes inside
    that item's folder). None for any other path.

    ``deliverables/book/x-v2.pdf``                  -> (x, x-v2.pdf)
    ``deliverables/releases/film-v2/description.md``-> (film, releases/film-v2/description.md)
    ``deliverables/zome/wedge-zome-wedge-v2/a.svg`` -> (wedge-zome-wedge, wedge-zome-wedge-v2/a.svg)
    ``deliverables/domology/plates/p01.png``        -> (domology-plates, p01.png)
    ``deliverables/byod/final/cut.mp4``             -> (byod, final/cut.mp4)       a project, kept whole
    ``deliverables/the-seam-does-four-jobs.mp4``    -> (the-seam-does-four-jobs, the-seam-does-four-jobs.mp4)
    """
    parts = _legacy_rel(path)
    if parts is None:
        return None
    if len(parts) == 1:
        return slug_of(parts[0]), Path(parts[0])
    kind = parts[0]
    if _is_voice(kind):                       # a voice cache left loose: it stays whole, beside its cut
        return slug_of(kind), Path(*parts)
    if _is_project(kind):
        return slug_of(kind), Path(*parts[1:])
    if kind == "releases":
        return slug_of(parts[1]), Path("releases", *parts[1:])
    if len(parts) == 2:
        return slug_of(parts[1]), Path(parts[1])
    sub = parts[1]
    if sub in GENERIC:
        return slug_of(f"{kind}-{sub}"), Path(*parts[2:])
    return slug_of(sub), Path(*parts[1:])


def _folder_for(slug: str, day: str | None = None) -> Path:
    return item_dir(slug) or LIBRARY / (day or today()) / slug


def new_path(name: str | Path, *, day: str | None = None) -> Path:
    """Where a new file called ``name`` goes: its item's folder, under a version that has
    never existed. ``foo.pdf`` -> ``.../foo.pdf``, then ``foo-v2.pdf``, ``foo-v3.pdf``.
    The parent folder is created; companion files are written beside the returned path."""
    name = Path(name).name
    folder = _folder_for(slug_of(name), day)
    folder.mkdir(parents=True, exist_ok=True)
    return free(folder / name)


def new_folder(name: str, *, day: str | None = None) -> Path:
    """A new, empty, versioned folder for an output that is a folder (a fabrication
    package, a set of stills): ``name``, then ``name-v2``..."""
    parent = _folder_for(slug_of(name), day)
    parent.mkdir(parents=True, exist_ok=True)
    target = free(parent / name)
    target.mkdir(parents=True)
    return target


def free(path: Path) -> Path:
    """``path`` if nothing has that name, else the next version above the highest one there."""
    if not path.exists():
        return path
    stem, suffix = _split_ext(path.name)
    match = re.match(r"^(.*)-v(\d+)$", stem)
    base = match.group(1) if match else stem
    version = 2
    for sibling in path.parent.glob(f"{base}-v*"):
        sib, sib_suffix = _split_ext(sibling.name)
        found = re.match(rf"^{re.escape(base)}-v(\d+)$", sib)
        if found and sib_suffix == suffix:
            version = max(version, int(found.group(1)) + 1)
    while True:
        candidate = path.with_name(f"{base}-v{version}{suffix}")
        if not candidate.exists():
            return candidate
        version += 1


def locate(path: str | Path) -> Path:
    """Where an old-style path (``deliverables/masterclass/film.mp4``) lives now. If the
    item has never been made, where it would go (so ``.parent`` is still the right folder
    to look in). Paths outside the old folders come back unchanged."""
    found = address(path)
    if found is None:
        return Path(path)
    slug, inner = found
    return _folder_for(slug) / inner


def route(path: str | Path) -> Path:
    """The library's answer for a path an exporter asked for: an old-style path is sent
    to its item's folder under a name that has never existed (parents created);
    anything else is returned as it is, for the caller's own versioning."""
    target = locate(path)
    if target == Path(path):
        return target
    target.parent.mkdir(parents=True, exist_ok=True)
    return free(target)


def release_dir(video: Path) -> Path:
    """The release folder of a cut, inside the cut's item folder."""
    return Path(video).parent / "releases" / Path(video).stem


def files(slug: str) -> list[Path]:
    folder = item_dir(slug)
    return sorted(folder.iterdir()) if folder else []


def latest(slug: str, ext: str | None = None, *, exact: bool = True) -> Path | None:
    """The newest version of an item's main file (``ext`` picks which: ``.pdf``, ``.mp4``).
    With ``exact``, only files named the slug plus a version (so ``latest("x", ".pdf")`` is
    never ``x-pack.pdf`` or ``x-vertical.mp4``)."""
    best = None
    for p in files(slug):
        if p.is_dir() or (ext and p.suffix.lower() != ext.lower()):
            continue
        if exact and not re.fullmatch(rf"{re.escape(slug)}(-v\d+)?", _split_ext(p.name)[0]):
            continue
        key = (version_of(p.name), p.stat().st_mtime)
        if best is None or key > best[0]:
            best = (key, p)
    return best[1] if best else None


def legacy_glob(pattern: str) -> list[Path]:
    """Files anywhere in the library matching a name pattern (``*-youtube.md``): what a glob
    over one of the old kind folders becomes, now that the kind is not a folder."""
    out = []
    for day in days():
        out.extend(day.glob(f"*/{pattern}"))
    return sorted(out)


# ---------------------------------------------------------------------------
# The index


@dataclass
class Item:
    slug: str
    folder: Path
    entries: list[Path] = field(default_factory=list)

    @property
    def day(self) -> str:
        return self.folder.parent.name

    @property
    def kind(self) -> str:
        kinds = {kind_of(p) for p in self.entries}
        if "folder" in kinds and len(self.entries) <= 3:
            inner = {kind_of(f) for e in self.entries if e.is_dir() for f in e.rglob("*") if f.is_file()}
            kinds |= inner
        for k in _PRIORITY:
            if k in kinds:
                return k
        return "folder" if kinds else "empty"

    @property
    def versions(self) -> int:
        return max((version_of(p.name) for p in self.entries if kind_of(p) not in ("voice", "releases")),
                   default=1)

    @property
    def updated(self) -> dt.date:
        stamps = [p.stat().st_mtime for p in self.entries]
        return dt.date.fromtimestamp(max(stamps) if stamps else self.folder.stat().st_mtime)

    @property
    def size(self) -> int:
        return sum(_size(p) for p in self.entries)


def _size(p: Path) -> int:
    if p.is_file():
        return p.stat().st_size
    return sum(f.stat().st_size for f in p.rglob("*") if f.is_file())


def items() -> list[Item]:
    out = []
    for day in days():
        for folder in sorted(p for p in day.iterdir() if p.is_dir()):
            out.append(Item(folder.name, folder, sorted(folder.iterdir())))
    return out


def find(text: str) -> list[Item]:
    text = text.lower()
    return [i for i in items() if text in i.slug.lower()]


def _mb(n: int) -> str:
    return f"{n / 1e6:,.1f} MB" if n < 1e9 else f"{n / 1e9:,.2f} GB"


def _main_file(item: Item) -> Path | None:
    for ext in (".mp4", ".pdf", ".png", ".html", ".md", ".zip", ".jpg", ".mp3"):
        found = latest(item.slug, ext)
        if found:
            return found
    plain = [p for p in item.entries if p.is_file()]
    return plain[-1] if plain else None


def write_index() -> tuple[Path, Path]:
    """deliverables/INDEX.md and index.html: every item, newest day first, under the day it
    was first made, and again under the last day a version was added."""
    all_items = items()
    by_day: dict[str, list[Item]] = {}
    later: dict[str, list[Item]] = {}
    for it in all_items:
        by_day.setdefault(it.day, []).append(it)
        if it.updated.isoformat() != it.day:
            later.setdefault(it.updated.isoformat(), []).append(it)
    total = sum(it.size for it in all_items)
    md = ["# The library\n",
          f"Everything the project has made: {len(all_items)} items over {len(by_day)} days, {_mb(total)}. "
          "One folder per item, every version of it inside, filed under the day it was first made. "
          "Rebuilt by `py -3.12 -m medialib`.\n"]
    rows = []
    for day in sorted(set(by_day) | set(later), reverse=True):
        md.append(f"\n## {day}\n")
        rows.append(f"<h2>{day}</h2><table>")
        for it in by_day.get(day, []):
            main = _main_file(it)
            rel = (main or it.folder).relative_to(LIBRARY).as_posix()
            v = f", {it.versions} versions" if it.versions > 1 else ""
            md.append(f"- **{it.slug}** ({it.kind}{v}, {_mb(it.size)}) -- [{Path(rel).name}]({rel})")
            rows.append(f"<tr><td class=k>{it.kind}</td><td><a href='{html.escape(rel)}'>{html.escape(it.slug)}</a>"
                        f"</td><td class=n>{it.versions if it.versions > 1 else ''}</td>"
                        f"<td class=n>{_mb(it.size)}</td></tr>")
        for it in later.get(day, []):
            rel = it.folder.relative_to(LIBRARY).as_posix()
            md.append(f"- *new version:* **{it.slug}** -- {it.versions} versions, filed under [{it.day}]({rel})")
            rows.append(f"<tr class=u><td class=k>new version</td><td><a href='{html.escape(rel)}'>"
                        f"{html.escape(it.slug)}</a> (filed under {it.day})</td>"
                        f"<td class=n>{it.versions}</td><td></td></tr>")
        rows.append("</table>")
    md_path = LIBRARY / "INDEX.md"
    md_path.write_text("\n".join(md) + "\n", encoding="utf-8")
    page = f"""<!doctype html><html><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>The library</title><style>
:root {{ --bg:#fbf8f3; --ink:#1d1d1b; --mut:#6b665e; --acc:#b0601e; --line:#e4ddd2; }}
@media (prefers-color-scheme: dark) {{ :root {{ --bg:#17161a; --ink:#ece8e1; --mut:#a49e95; --acc:#e09a5a; --line:#2c2a30; }} }}
body {{ background:var(--bg); color:var(--ink); font:15px/1.45 "Segoe UI",sans-serif; max-width:980px; margin:0 auto; padding:24px 16px; }}
h1 {{ margin:0 0 4px; }} p {{ color:var(--mut); }} h2 {{ margin:26px 0 6px; font-size:17px; }}
table {{ width:100%; border-collapse:collapse; }} td {{ border-bottom:1px solid var(--line); padding:5px 8px 5px 0; }}
td.k {{ color:var(--mut); width:90px; }} td.n {{ text-align:right; color:var(--mut); white-space:nowrap; }}
a {{ color:var(--acc); text-decoration:none; word-break:break-word; }} tr.u td {{ color:var(--mut); font-style:italic; }}
input {{ width:100%; box-sizing:border-box; padding:8px; font:inherit; margin:10px 0; background:transparent; color:var(--ink); border:1px solid var(--line); }}
</style></head><body><h1>The library</h1><p>{len(all_items)} items over {len(by_day)} days, {_mb(total)}. Newest first;
every version of an item is in its one folder.</p><input id=q placeholder="Filter by name or kind">{''.join(rows)}
<script>q.oninput=()=>{{const t=q.value.toLowerCase();document.querySelectorAll('tr').forEach(r=>r.style.display=r.textContent.toLowerCase().includes(t)?'':'none')}}</script>
</body></html>"""
    html_path = LIBRARY / "index.html"
    html_path.write_text(page, encoding="utf-8")
    return md_path, html_path


# ---------------------------------------------------------------------------
# Moving the old folders in


@dataclass
class Move:
    src: Path
    dst: Path


def _units(root: Path, depth: int = 0):
    """The pieces an old output folder moves in: whole files, whole item folders, whole
    project folders -- never a folder broken apart that :func:`address` would keep whole."""
    for p in sorted(root.iterdir()):
        if p.name in LEGACY_SKIP or p.name in LIBRARY_FILES or p.name == "__pycache__":
            continue
        if root in LEGACY and p.is_dir() and DAY.match(p.name):
            continue
        if p.is_file():
            yield p
        elif depth == 0 and _is_voice(p.name):
            yield p
        elif depth == 0 and _is_project(p.name):
            for inner in sorted(p.iterdir()):
                yield inner
        elif depth == 0 and p.name == "releases":
            yield from sorted(p.iterdir())
        elif depth == 0:
            yield from _units(p, 1)
        elif depth == 1 and p.name in GENERIC:
            yield from sorted(p.iterdir())
        else:
            yield p


def _rel(p: Path) -> Path:
    """A path relative to the project (the library's parent), as the manifests record it."""
    return Path(p).relative_to(LIBRARY.parent)


def _mtime(p: Path) -> float:
    if p.is_file():
        return p.stat().st_mtime
    stamps = [f.stat().st_mtime for f in p.rglob("*") if f.is_file()]
    return min(stamps) if stamps else p.stat().st_mtime


def plan_migration() -> list[Move]:
    groups: dict[str, list[tuple[Path, Path]]] = {}
    for root in LEGACY:
        if root.is_dir():
            for unit in _units(root):
                found = address(unit)
                if found:
                    groups.setdefault(found[0], []).append((unit, found[1]))
    moves: list[Move] = []
    taken: set[Path] = set()
    for slug, units in sorted(groups.items()):
        folder = item_dir(slug)
        if folder is None:
            first = min(_mtime(u) for u, _ in units)
            folder = LIBRARY / dt.date.fromtimestamp(first).isoformat() / slug
        for unit, inner in units:
            dst = folder / inner
            if dst.exists() or dst in taken:
                dst = _kept_both(dst, taken)
            taken.add(dst)
            moves.append(Move(unit, dst))
    return moves


def _kept_both(dst: Path, taken: set[Path]) -> Path:
    """Two old folders held different things under one name: keep both, never merge."""
    stem, suffix = _split_ext(dst.name)
    k = 2
    while True:
        cand = dst.with_name(f"{stem}-copy{k}{suffix}")
        if not cand.exists() and cand not in taken:
            return cand
        k += 1


def loose_outputs() -> list[Path]:
    """Films left in the project folder itself, with their captions, scripts and voice
    caches (``2v-masterclass*``, ``testo*``): output, so they belong in the library."""
    films = {slug_of(p.name) for p in LIBRARY.parent.glob("*.mp4")
             if not p.name.startswith(".") and not re.search(r"[ (]", p.name)}
    # Only names the asset library does not claim (it takes the generated clips).
    try:
        import assetlib
        films -= {slug_of(old) for old, *_ in assetlib.LOOSE}
    except ImportError:
        pass
    out = []
    for p in sorted(LIBRARY.parent.iterdir()):
        if p.name.startswith(".") or p.suffix == ".py":
            continue
        if slug_of(p.name) in films and (p.is_file() or _is_voice(p.name)):
            out.append(p)
    return out


def migrate(go: bool = False) -> Path | None:
    moves = plan_migration()
    for p in loose_outputs():
        slug = slug_of(p.name)
        folder = item_dir(slug) or next((m.dst.parent for m in moves if m.dst.parent.name == slug), None) \
            or LIBRARY / dt.date.fromtimestamp(_mtime(p)).isoformat() / slug
        moves.append(Move(p, folder / p.name))
    by_root: dict[str, int] = {}
    for m in moves:
        top = _rel(m.src).parts
        key = "/".join(top[:2]) if len(top) > 2 else top[0]
        by_root[key] = by_root.get(key, 0) + 1
    print(f"{len(moves)} pieces into {len({m.dst.relative_to(LIBRARY).parts[1] for m in moves})} items "
          f"over {len({m.dst.relative_to(LIBRARY).parts[0] for m in moves})} days")
    for k, v in sorted(by_root.items(), key=lambda kv: -kv[1]):
        print(f"  {v:5d}  from {k}")
    for m in moves:
        if m.src.name != m.dst.name and m.dst.name.count("-copy"):
            print(f"  kept both: {_rel(m.src)} -> {_rel(m.dst)}")
    if not go:
        print("dry run; add --go to move")
        return None
    MOVES.mkdir(parents=True, exist_ok=True)
    manifest = free(MOVES / f"{today()}-migration.tsv")
    with manifest.open("w", encoding="utf-8") as log:
        log.write("from\tto\n")
        for m in moves:
            m.dst.parent.mkdir(parents=True, exist_ok=True)
            if m.src.is_file():
                os.replace(m.src, m.dst)
            else:
                shutil.move(str(m.src), str(m.dst))
            log.write(f"{_rel(m.src).as_posix()}\t{_rel(m.dst).as_posix()}\n")
            log.flush()
    prune_empty()
    write_index()
    print(f"moved; manifest {_rel(manifest)}")
    return manifest


def prune_empty() -> None:
    """Remove the old kind folders once they are empty (only empty ones; never a file)."""
    for root in LEGACY:
        if not root.is_dir():
            continue
        for d in sorted((p for p in root.rglob("*") if p.is_dir()), key=lambda p: -len(p.parts)):
            if is_library_path(d) or any(s in d.relative_to(root).parts for s in LEGACY_SKIP):
                continue
            if d.name == "__pycache__":
                shutil.rmtree(d, ignore_errors=True)
                continue
            try:
                d.rmdir()
            except OSError:
                pass


def moved(old: str | Path) -> Path | None:
    """Where a file from an old folder went, by the migration manifests."""
    old = Path(old)
    key = (_rel(old) if old.is_absolute() else old).as_posix()
    for manifest in sorted(MOVES.glob("*.tsv")):
        for line in manifest.read_text(encoding="utf-8").splitlines()[1:]:
            src, _, dst = line.partition("\t")
            if src == key:
                return LIBRARY.parent / dst
    return None


# ---------------------------------------------------------------------------


def selftest() -> None:
    assert slug_of("beyond-the-dome-building-with-wedges-v2-vertical.mp4") == "beyond-the-dome-building-with-wedges"
    assert slug_of("film-vertical-v2.mp4") == "film"
    assert slug_of("cabin_cell_wall-teaser-v2-narration-plan.json") == "cabin_cell_wall-teaser"
    assert slug_of("all-domes-every-permutation-voice-en-US-AndrewMultilingualNeural-0-0Hz-0-7a9e03d82a") \
        == "all-domes-every-permutation"
    assert slug_of("dome_case_energy-voice") == "dome_case_energy"
    assert slug_of("shot_00004.0s.png") == "shot_00004.0s"
    assert slug_of("the-40-hour-cabin-the-case-v2-p1.png") == "the-40-hour-cabin-the-case"
    assert slug_of("2-trees-outline-v10.txt") == "2-trees-outline"
    assert slug_of("beyond-the-dome-building-with-wedges-myvoice-x1.5") == "beyond-the-dome-building-with-wedges"
    assert slug_of("wedge-zome-wedge-v3") == "wedge-zome-wedge"
    assert slug_of("cabin_wedge_explained-teaser-myvoice") == "cabin_wedge_explained-teaser"
    assert version_of("stem-cell-hero-cut-v3.mp4") == 3 and version_of("x.mp4") == 1
    assert version_of("cabin_cell_wall-teaser-v2-narration.md") == 2
    import tempfile
    global LIBRARY, LEGACY, MOVES
    saved = LIBRARY, LEGACY, MOVES
    with tempfile.TemporaryDirectory() as scratch:
        LIBRARY = Path(scratch) / "deliverables"
        MOVES = LIBRARY / "_moves"
        LEGACY = (LIBRARY,)
        try:
            a = new_path("film.mp4", day="2026-01-02")
            a.write_bytes(b"1")
            b = new_path("film.mp4", day="2026-03-04")          # squashed into the first day's folder
            assert b == LIBRARY / "2026-01-02" / "film" / "film-v2.mp4", b
            b.write_bytes(b"2")
            gone = LIBRARY / "2026-01-02" / "film" / "film-v7.mp4"
            gone.write_bytes(b"7")
            gone.unlink()
            assert new_path("film.mp4").name == "film-v3.mp4"
            assert latest("film", ".mp4") == b
            assert new_folder("kit").is_dir() and new_folder("kit").name == "kit-v2"
            # old addresses
            assert address(LIBRARY / "book" / "guide-v2.pdf") == ("guide", Path("guide-v2.pdf"))
            assert address(LIBRARY / "releases" / "film-v2" / "d.md") == ("film", Path("releases/film-v2/d.md"))
            assert address(LIBRARY / "zome" / "kit-v2" / "a.svg") == ("kit", Path("kit-v2/a.svg"))
            assert address(LIBRARY / "domology" / "plates" / "p01.png") == ("domology-plates", Path("p01.png"))
            assert address(LIBRARY / "byod" / "final" / "cut.mp4") == ("byod", Path("final/cut.mp4"))
            assert address(LIBRARY / "2026-01-02" / "film" / "film.mp4") is None
            assert address(LIBRARY / "film-voice-en-x" / "c1.mp3") == ("film", Path("film-voice-en-x/c1.mp3"))
            assert route(LIBRARY / "masterclass" / "film.mp4").name == "film-v3.mp4"
            assert locate(LIBRARY / "masterclass" / "film-v2.mp4") == b
            # a migration
            old = LIBRARY / "book"
            old.mkdir()
            (old / "guide.pdf").write_bytes(b"g")
            (old / "guide-v2.pdf").write_bytes(b"g2")
            (LIBRARY / "releases" / "film-v2").mkdir(parents=True)
            (LIBRARY / "releases" / "film-v2" / "description.md").write_text("d")
            (LIBRARY / "byod" / "final").mkdir(parents=True)
            (LIBRARY / "byod" / "final" / "cut.mp4").write_bytes(b"c")
            (LIBRARY / "byod" / "notes.md").write_text("n")
            plan = {m.src.name: m.dst for m in plan_migration()}
            assert plan["guide-v2.pdf"].parent == plan["guide.pdf"].parent
            assert plan["film-v2"] == LIBRARY / "2026-01-02" / "film" / "releases" / "film-v2"
            assert plan["final"].parent == plan["notes.md"].parent and plan["final"].parent.name == "byod"
            migrate(go=True)
            assert not old.exists() and not (LIBRARY / "releases").exists()
            assert latest("guide", ".pdf").name == "guide-v2.pdf"
            assert moved(old / "guide.pdf") is not None
            write_index()
        finally:
            LIBRARY, LEGACY, MOVES = saved
    print("medialib selftest: ok")


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(prog="medialib", description="The dated media library.")
    sub = ap.add_subparsers(dest="cmd")
    sub.add_parser("index")
    f = sub.add_parser("find")
    f.add_argument("text")
    la = sub.add_parser("latest")
    la.add_argument("slug")
    la.add_argument("--ext")
    m = sub.add_parser("migrate")
    m.add_argument("--go", action="store_true")
    sub.add_parser("selftest")
    a = ap.parse_args(argv)
    if a.cmd == "find":
        for it in find(a.text):
            print(f"{it.day}  {it.kind:9s} v{it.versions:<3d} {it.folder.relative_to(ROOT)}")
    elif a.cmd == "latest":
        p = latest(a.slug, a.ext)
        print(p or "none")
        return 0 if p else 1
    elif a.cmd == "migrate":
        migrate(a.go)
    elif a.cmd == "selftest":
        selftest()
    else:
        for p in write_index():
            print(f"wrote {p.relative_to(ROOT)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
