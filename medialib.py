"""One library for everything the project makes: films, books, PDFs, stills, packs.

    py -3.12 -m medialib                 # rebuild the index (deliverables/INDEX.md + index.html)
    py -3.12 -m medialib find wedge      # every output whose name contains "wedge"
    py -3.12 -m medialib latest the-40-hour-cabin-the-case --ext .pdf
    py -3.12 -m medialib migrate         # dry run: what would move into the numbered layout
    py -3.12 -m medialib migrate --go    # move it, writing a manifest of every move
    py -3.12 -m medialib selftest

Every output is one folder, numbered in the order it was made and named for the
concept it is -- one folder per *iteration*, with all of that iteration's media
inside it::

    deliverables/
        0412-the-staple-house/
            the-staple-house.mp4  the-staple-house-vertical.mp4  the-staple-house.srt ...
            the-staple-house-myvoice-x1.5/      (the voice it was narrated with)
            release/                            (thumbnails, description.md, captions)
        0450-the-staple-house-v2/
            the-staple-house-v2.mp4  the-staple-house-v2-vertical.mp4 ...
            release/
        INDEX.md   index.html   _moves/

The number is the output's place in the order things were made; it is never
reused. ``-v2``, ``-v3`` say which iteration of the concept a folder is. A file's
*concept* (its slug) is its name with the version (``-v3``) and the companion
suffixes (``-vertical``, ``-narration``, ``-review``, ``-p1``...) taken off.

The old folders (``deliverables/book``, ``deliverables/masterclass``, ``exports``...)
and the dated layout that followed them are *addresses* now, not places: code may
still ask for ``deliverables/book/x.pdf``, and :func:`route` (through
:func:`two_v_demo.deliverables.next_version_path`) answers with the next iteration's
folder. Nothing in here overwrites anything.
"""

from __future__ import annotations

import argparse
import datetime as dt
import html
import json
import os
import re
import shutil
from dataclasses import dataclass, field
from pathlib import Path

ROOT = Path(__file__).resolve().parent
LIBRARY = ROOT / "deliverables"
MOVES = LIBRARY / "_moves"
OUTPUT = re.compile(r"^(\d{4,})-(.+?)(?:-v(\d+))?$")
DAY = re.compile(r"^\d{4}-\d{2}-\d{2}$")
LEGACY = (LIBRARY, ROOT / "exports")
LEGACY_SKIP = {"scratchpad", "_moves", "tasks"}
LIBRARY_FILES = {"INDEX.md", "index.html", "README.md"}
PROJECTS = {"byod", "byod-deepseek", "byod-styled", "launcher_trailer", "tree-value-video", "rap_demo"}
GENERIC = {"plates", "all", "final", "output", "build", "audio", "video", "stills", "frames", "out", "shots"}
_STAMP = re.compile(r"_\d{8}_\d{6}")

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
_PRIORITY = ("video", "book", "document", "slides", "page", "image", "audio", "archive", "text",
             "captions", "data", "code")


# ----------------------------------------------------------------------
# Names
# ----------------------------------------------------------------------

def _split_ext(name: str) -> tuple[str, str]:
    suffix = Path(name).suffix
    if suffix and len(suffix) <= 6 and (suffix.lower() in KINDS or suffix[1:].isalpha()):
        return name[: -len(suffix)], suffix
    return name, ""


def slug_of(name: str) -> str:
    """The concept a file or folder name belongs to."""
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


def is_main(name: str) -> bool:
    """The output's own file (``film.mp4``, ``film-v3.mp4``), not a companion of it."""
    stem, _ = _split_ext(Path(name).name)
    return bool(re.fullmatch(rf"{re.escape(slug_of(name))}(-v\d+)?", stem))


def kind_of(path: Path) -> str:
    if path.is_dir():
        if path.name.startswith("release"):
            return "release"
        return "voice" if "-voice" in path.name or "-myvoice" in path.name else "folder"
    return KINDS.get(path.suffix.lower(), "other")


def folder_name(seq: int, slug: str, version: int) -> str:
    return f"{seq:04d}-{slug}" + (f"-v{version}" if version > 1 else "")


def parse_folder(name: str) -> tuple[int, str, int] | None:
    m = OUTPUT.match(name)
    if not m or DAY.match(name):
        return None
    return int(m.group(1)), m.group(2), int(m.group(3) or 1)


def versioned(name: str, version: int) -> str:
    """``name`` as it is called in iteration ``version``: ``film-vertical.mp4`` -> ``film-v2-vertical.mp4``."""
    if version <= 1 or version_of(name) == version:
        return name
    slug = slug_of(name)
    stem, ext = _split_ext(name)
    rest = stem[len(slug):] if stem.startswith(slug) else ""
    rest = _VERSION.sub("", rest)
    return f"{slug}-v{version}{rest}{ext}"


# ----------------------------------------------------------------------
# Where things are
# ----------------------------------------------------------------------

@dataclass
class Output:
    seq: int
    slug: str
    version: int
    folder: Path

    @property
    def entries(self) -> list[Path]:
        return sorted(self.folder.iterdir()) if self.folder.is_dir() else []

    @property
    def made(self) -> dt.date:
        stamps = [p.stat().st_mtime for p in self.entries if p.is_file()] or [self.folder.stat().st_mtime]
        return dt.date.fromtimestamp(min(stamps))

    @property
    def kind(self) -> str:
        kinds = {kind_of(p) for p in self.entries}
        if "folder" in kinds:
            kinds |= {kind_of(f) for e in self.entries if e.is_dir() for f in e.rglob("*") if f.is_file()}
        for k in _PRIORITY:
            if k in kinds:
                return k
        return "folder" if kinds else "empty"

    @property
    def size(self) -> int:
        return sum(f.stat().st_size for f in self.folder.rglob("*") if f.is_file())


def outputs(slug: str | None = None) -> list[Output]:
    if not LIBRARY.is_dir():
        return []
    out = []
    for p in LIBRARY.iterdir():
        if p.is_dir():
            parsed = parse_folder(p.name)
            if parsed and (slug is None or parsed[1] == slug):
                out.append(Output(parsed[0], parsed[1], parsed[2], p))
    return sorted(out, key=lambda o: (o.seq, o.version))


def items() -> list[Output]:          # the name the rest of the project used for these
    return outputs()


def next_seq() -> int:
    return max((o.seq for o in outputs()), default=0) + 1


def iteration(slug: str, version: int) -> Path | None:
    for o in outputs(slug):
        if o.version == version:
            return o.folder
    return None


def item_dir(slug: str) -> Path | None:
    """The newest iteration's folder of a concept."""
    found = outputs(slug)
    return max(found, key=lambda o: (o.version, o.seq)).folder if found else None


def newest_version(slug: str) -> int:
    return max((o.version for o in outputs(slug)), default=0)


def today() -> str:
    return dt.date.today().isoformat()


def is_library_path(path: str | Path) -> bool:
    try:
        rel = _abs(path).relative_to(LIBRARY.resolve())
    except ValueError:
        return False
    return bool(rel.parts) and parse_folder(rel.parts[0]) is not None


def _abs(path: str | Path) -> Path:
    p = Path(path)
    return (p if p.is_absolute() else ROOT / p).resolve()


def free(path: Path) -> Path:
    """``path`` if nothing has that name, else the next version above the highest one beside it."""
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


def new_output(slug: str) -> tuple[Path, int]:
    """A new, empty folder for the next iteration of ``slug``: (folder, version)."""
    version = newest_version(slug) + 1
    folder = LIBRARY / folder_name(next_seq(), slug, version)
    folder.mkdir(parents=True, exist_ok=False)
    return folder, version


def new_path(name: str | Path) -> Path:
    """Where a new file called ``name`` goes.

    The output's own file (``film.mp4``) starts a new iteration: a new numbered folder,
    and the file named for its version (``film-v3.mp4``). A companion (``film-vertical.mp4``)
    joins the newest iteration of its concept, named for that version; with none yet, it
    starts one. The returned path never exists already."""
    name = Path(name).name
    slug = slug_of(name)
    if is_main(name) or newest_version(slug) == 0:
        folder, version = new_output(slug)
    else:
        version = newest_version(slug)
        folder = iteration(slug, version)
    return free(folder / versioned(name, version))


def new_folder(name: str) -> Path:
    """A new iteration that is itself a folder of files (a fabrication kit, a set of
    stills): the numbered folder is returned, created and empty."""
    folder, _version = new_output(slug_of(name))
    return folder


def release_dir(video: Path) -> Path:
    """The release folder of a cut, inside its iteration's folder."""
    return Path(video).parent / "release"


def new_release_path(name: str) -> Path:
    slug = slug_of(name)
    folder = iteration(slug, version_of(name)) or item_dir(slug) or new_output(slug)[0]
    return free(folder / "release")


# ----------------------------------------------------------------------
# The old addresses
# ----------------------------------------------------------------------

def _legacy_rel(path: str | Path) -> tuple[str, ...] | None:
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
        return rel.parts
    return None


def is_legacy_path(path: str | Path) -> bool:
    return _legacy_rel(path) is not None


def _is_voice(name: str) -> bool:
    return "-voice" in name or "-myvoice" in name


def _is_project(kind: str) -> bool:
    return kind in PROJECTS or bool(_STAMP.search(kind))


def address(path: str | Path) -> tuple[str, str] | None:
    """For a path at an old address: (the concept, the file's name). Kind folders, dated
    folders and the old item folders all reduce to the file's own name and its concept."""
    parts = _legacy_rel(path)
    if parts is None:
        return None
    if parts and DAY.match(parts[0]):            # the dated layout: day/item/...
        parts = parts[1:]
        if len(parts) >= 2:
            return slug_of(parts[0]), parts[-1]
    if not parts:
        return None
    if len(parts) == 1:
        return slug_of(parts[0]), parts[0]
    kind = parts[0]
    if _is_voice(kind):
        return slug_of(kind), parts[-1]
    if _is_project(kind):
        return slug_of(kind), parts[-1]
    if kind == "releases":
        return slug_of(parts[1]), parts[-1]
    if len(parts) == 2:
        return slug_of(parts[1]), parts[1]
    sub = parts[1]
    return (slug_of(f"{kind}-{sub}") if sub in GENERIC else slug_of(sub)), parts[-1]


def locate(path: str | Path) -> Path:
    """Where an old-style path lives now: the file of that name in its concept's iteration
    (the version its name carries, else the newest). If it does not exist yet, where the
    next one of its kind would go -- so ``.parent`` is the folder to look in."""
    found = address(path)
    if found is None:
        return Path(path)
    slug, name = found
    v = version_of(name)
    folder = iteration(slug, v) if v > 1 else None
    folder = folder or item_dir(slug)
    if folder is None:
        return LIBRARY / folder_name(next_seq(), slug, 1) / name
    candidate = folder / versioned(name, parse_folder(folder.name)[2])
    return candidate if candidate.exists() or not (folder / name).exists() else folder / name


def route(path: str | Path) -> Path:
    """The library's answer for a path an exporter asked for. An old-style path becomes a
    new file in the right iteration (folders created); a path with no file extension is
    taken to be an output that is a folder, and gets its own new numbered folder. Any
    other path comes back unchanged."""
    found = address(path)
    if found is None:
        return Path(path)
    slug, name = found
    if Path(str(path)).parent.name == "releases":
        return new_release_path(name)
    if not _split_ext(name)[1]:
        return new_folder(name)
    if slug_of(name) != slug:          # a file of a project or a generic folder: it joins that concept
        folder = item_dir(slug) or new_output(slug)[0]
        return free(folder / name)
    return new_path(name)


def latest(slug: str, ext: str | None = None, *, exact: bool = True) -> Path | None:
    """The newest iteration's own file of ``slug`` (``ext`` picks which)."""
    best = None
    for o in outputs(slug):
        for p in o.entries:
            if p.is_dir() or (ext and p.suffix.lower() != ext.lower()):
                continue
            if exact and not re.fullmatch(rf"{re.escape(slug)}(-v\d+)?", _split_ext(p.name)[0]):
                continue
            key = (o.version, version_of(p.name), p.stat().st_mtime)
            if best is None or key > best[0]:
                best = (key, p)
    return best[1] if best else None


def files(slug: str) -> list[Path]:
    return [p for o in outputs(slug) for p in o.entries]


def legacy_glob(pattern: str) -> list[Path]:
    return sorted(p for o in outputs() for p in o.folder.glob(pattern))


def days() -> list[Path]:
    """Gone with the dated layout; kept so old callers get nothing rather than an error."""
    return []


def find(text: str) -> list[Output]:
    text = text.lower()
    return [o for o in outputs() if text in o.slug.lower()]


# ----------------------------------------------------------------------
# The index
# ----------------------------------------------------------------------

def _mb(n: int) -> str:
    return f"{n / 1e6:,.1f} MB" if n < 1e9 else f"{n / 1e9:,.2f} GB"


def _main_file(o: Output) -> Path | None:
    for ext in (".mp4", ".pdf", ".png", ".html", ".md", ".zip", ".jpg", ".mp3", ".csv"):
        for p in o.entries:
            if p.is_file() and p.suffix.lower() == ext and is_main(p.name):
                return p
    plain = [p for p in o.entries if p.is_file()]
    return plain[0] if plain else None


def write_index() -> tuple[Path, Path]:
    """deliverables/INDEX.md and index.html: every output, newest first, with its number,
    its concept, its iteration, the day it was made and its size."""
    all_out = sorted(outputs(), key=lambda o: o.seq, reverse=True)
    total = sum(o.size for o in all_out)
    concepts = len({o.slug for o in all_out})
    md = ["# The library\n",
          f"{len(all_out)} outputs of {concepts} concepts, {_mb(total)}. One folder per output, numbered in "
          "the order it was made, every file of it inside. Rebuilt by `py -3.12 -m medialib`.\n",
          "| # | output | iteration | made | kind | size |", "|---|---|---|---|---|---|"]
    rows = []
    for o in all_out:
        main = _main_file(o)
        rel = (main or o.folder).relative_to(LIBRARY).as_posix()
        md.append(f"| {o.seq:04d} | [{o.slug}]({rel}) | v{o.version} | {o.made.isoformat()} | {o.kind} | {_mb(o.size)} |")
        rows.append(f"<tr><td class=n>{o.seq:04d}</td><td><a href='{html.escape(rel)}'>{html.escape(o.slug)}</a></td>"
                    f"<td>v{o.version}</td><td>{o.made.isoformat()}</td><td class=k>{o.kind}</td>"
                    f"<td class=n>{_mb(o.size)}</td></tr>")
    md_path = LIBRARY / "INDEX.md"
    md_path.write_text("\n".join(md) + "\n", encoding="utf-8")
    page = f"""<!doctype html><html><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>The library</title><style>
:root {{ --bg:#fbf8f3; --ink:#1d1d1b; --mut:#6b665e; --acc:#b0601e; --line:#e4ddd2; }}
@media (prefers-color-scheme: dark) {{ :root {{ --bg:#17161a; --ink:#ece8e1; --mut:#a49e95; --acc:#e09a5a; --line:#2c2a30; }} }}
body {{ background:var(--bg); color:var(--ink); font:15px/1.45 "Segoe UI",sans-serif; max-width:1100px; margin:0 auto; padding:24px 16px; }}
table {{ width:100%; border-collapse:collapse; }} td,th {{ border-bottom:1px solid var(--line); padding:5px 8px 5px 0; text-align:left; }}
td.k {{ color:var(--mut); }} td.n {{ font-variant-numeric:tabular-nums; color:var(--mut); white-space:nowrap; }}
a {{ color:var(--acc); text-decoration:none; word-break:break-word; }} p {{ color:var(--mut); }}
input {{ width:100%; box-sizing:border-box; padding:8px; font:inherit; margin:10px 0; background:transparent; color:var(--ink); border:1px solid var(--line); }}
.wrap {{ overflow-x:auto; }}
</style></head><body><h1>The library</h1><p>{len(all_out)} outputs of {concepts} concepts, {_mb(total)}. Newest first.</p>
<input id=q placeholder="Filter by name, kind or date"><div class=wrap><table><tr><th>#</th><th>output</th><th>iteration</th>
<th>made</th><th>kind</th><th>size</th></tr>{''.join(rows)}</table></div>
<script>q.oninput=()=>{{const t=q.value.toLowerCase();document.querySelectorAll('tr').forEach((r,i)=>{{if(i)r.style.display=r.textContent.toLowerCase().includes(t)?'':'none'}})}}</script>
</body></html>"""
    html_path = LIBRARY / "index.html"
    html_path.write_text(page, encoding="utf-8")
    return md_path, html_path


# ----------------------------------------------------------------------
# Moving everything into the numbered layout
# ----------------------------------------------------------------------

@dataclass
class Move:
    src: Path
    dst: Path


def _mtime(p: Path) -> float:
    if p.is_file():
        return p.stat().st_mtime
    stamps = [f.stat().st_mtime for f in p.rglob("*") if f.is_file()]
    return min(stamps) if stamps else p.stat().st_mtime


def _release_version(folder: Path) -> int:
    """Which iteration a release folder belongs to: the cut its video.txt names."""
    txt = folder / "video.txt"
    if txt.is_file():
        for line in txt.read_text(encoding="utf-8", errors="ignore").splitlines():
            if line.startswith("landscape:"):
                return version_of(Path(line.split(":", 1)[1].strip()).name)
    return version_of(folder.name)


def _units_dated() -> list[tuple[str, int, Path, str]]:
    """(concept, iteration, entry, name inside the new folder) for the dated layout."""
    out = []
    for day in sorted(p for p in LIBRARY.iterdir() if p.is_dir() and DAY.match(p.name)):
        for item in sorted(p for p in day.iterdir() if p.is_dir()):
            slug = item.name
            for e in sorted(item.iterdir()):
                if e.name == "releases" and e.is_dir():
                    for r in sorted(e.iterdir()):
                        out.append((slug, _release_version(r), r, "release"))
                elif slug_of(e.name) == slug:
                    out.append((slug, version_of(e.name), e, e.name))
                else:                                # a project's own folders and files
                    out.append((slug, 1, e, e.name))
    return out


def plan_migration() -> list[Move]:
    groups: dict[tuple[str, int], list[tuple[Path, str]]] = {}
    for slug, v, entry, name in _units_dated():
        groups.setdefault((slug, v), []).append((entry, name))
    order = sorted(groups, key=lambda k: min(_mtime(e) for e, _ in groups[k]))
    seq = next_seq()
    moves: list[Move] = []
    for slug, v in order:
        folder = LIBRARY / folder_name(seq, slug, v)
        seq += 1
        taken: set[Path] = set()
        for entry, name in groups[(slug, v)]:
            dst = folder / name
            k = 2
            while dst in taken or dst.exists():          # two releases of one cut: release, release-v2
                dst = folder / f"{name}-v{k}"
                k += 1
            taken.add(dst)
            moves.append(Move(entry, dst))
    return moves


def _rel(p: Path) -> Path:
    return Path(p).relative_to(LIBRARY.parent)


def migrate(go: bool = False) -> Path | None:
    moves = plan_migration()
    folders = {m.dst.parent for m in moves}
    print(f"{len(moves)} pieces into {len(folders)} numbered outputs")
    if not go:
        for m in moves[:12]:
            print(f"  {_rel(m.src)}  ->  {_rel(m.dst)}")
        print("dry run; add --go to move")
        return None
    MOVES.mkdir(parents=True, exist_ok=True)
    manifest = free(MOVES / f"{today()}-numbered.tsv")
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
    for day in [p for p in LIBRARY.iterdir() if p.is_dir() and DAY.match(p.name)]:
        for d in sorted((p for p in day.rglob("*") if p.is_dir()), key=lambda p: -len(p.parts)) + [day]:
            try:
                d.rmdir()
            except OSError:
                pass
    write_index()
    print(f"moved; manifest {_rel(manifest)}")
    return manifest


def moved(old: str | Path) -> Path | None:
    """Where a file went, following every manifest in order (an old address may have moved twice)."""
    old = Path(old)
    key = (_rel(old) if old.is_absolute() else old).as_posix()
    for manifest in sorted(MOVES.glob("*.tsv")):
        for line in manifest.read_text(encoding="utf-8").splitlines()[1:]:
            src, _, dst = line.partition("\t")
            if src == key or key.startswith(src + "/"):
                key = dst + key[len(src):]
    path = LIBRARY.parent / key
    return path if path.exists() else None


# ----------------------------------------------------------------------

def selftest() -> None:
    assert slug_of("film-vertical-v2.mp4") == "film" and version_of("film-vertical-v2.mp4") == 2
    assert is_main("film-v3.mp4") and not is_main("film-v3-vertical.mp4")
    assert versioned("film-vertical.mp4", 2) == "film-v2-vertical.mp4"
    assert versioned("film-v2.srt", 2) == "film-v2.srt"
    assert parse_folder("0412-the-staple-house-v2") == (412, "the-staple-house", 2)
    assert parse_folder("2026-10-14") is None
    import tempfile
    global LIBRARY, LEGACY, MOVES
    saved = LIBRARY, LEGACY, MOVES
    with tempfile.TemporaryDirectory() as scratch:
        LIBRARY = Path(scratch) / "deliverables"
        MOVES = LIBRARY / "_moves"
        LEGACY = (LIBRARY,)
        LIBRARY.mkdir()
        try:
            a = route(LIBRARY / "masterclass" / "film.mp4")
            assert a.parent.name == "0001-film" and a.name == "film.mp4", a
            a.write_bytes(b"1")
            v = route(LIBRARY / "masterclass" / "film-vertical.mp4")
            assert v.parent == a.parent and v.name == "film-vertical.mp4", v
            v.write_bytes(b"1")
            b = route(LIBRARY / "masterclass" / "film.mp4")          # a re-render: a new iteration
            assert b.parent.name == "0002-film-v2" and b.name == "film-v2.mp4", b
            b.write_bytes(b"2")
            bv = route(LIBRARY / "masterclass" / "film-vertical.mp4")
            assert bv.parent == b.parent and bv.name == "film-v2-vertical.mp4", bv
            assert latest("film", ".mp4") == b and locate(LIBRARY / "masterclass" / "film.mp4").parent == b.parent
            assert locate(LIBRARY / "masterclass" / "film.mp4").parent.name == "0002-film-v2"
            kit = route(LIBRARY / "zome" / "wedge-zome-wedge")
            assert kit.is_dir() and kit.name == "0003-wedge-zome-wedge"
            assert release_dir(b) == b.parent / "release"
            f1 = route(LIBRARY / "presenter" / "frames" / "frame_1.png")
            f2 = route(LIBRARY / "presenter" / "frames" / "frame_2.png")
            assert f1.parent == f2.parent and f1.parent.name.endswith("presenter-frames"), (f1, f2)
            # the dated layout, moved in
            day = LIBRARY / "2026-01-02" / "guide"
            (day / "releases" / "guide").mkdir(parents=True)
            (day / "guide.pdf").write_bytes(b"g")
            (day / "guide-v2.pdf").write_bytes(b"g2")
            (day / "releases" / "guide" / "video.txt").write_text("landscape: x/guide-v2.pdf\n")
            migrate(go=True)
            got = {o.folder.name: [p.name for p in o.entries] for o in outputs("guide")}
            assert any(n.endswith("-guide") and "guide.pdf" in f for n, f in got.items()), got
            assert any(n.endswith("-guide-v2") and "release" in f for n, f in got.items()), got
            assert not (LIBRARY / "2026-01-02").exists()
            write_index()
        finally:
            LIBRARY, LEGACY, MOVES = saved
    print("medialib selftest: ok")


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(prog="medialib", description="The numbered media library.")
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
        for o in find(a.text):
            print(f"{o.seq:04d}  v{o.version:<3d} {o.kind:9s} {o.folder.relative_to(ROOT)}")
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
