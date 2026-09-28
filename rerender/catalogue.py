"""Every film this repository has rendered, read out of the code that made it.

Nothing here is typed by hand except the two small tables that say which
films belong together (:data:`FAMILIES`) and how a film whose subject is not
the wedge dome should sit in the Cabin World (:data:`FIT`). Titles,
chapters, narration, equations, callouts, where the originals are on disk,
which modules the numbers come from -- all of it is read from the lesson,
presentation or slideshow that produced the film, so the catalogue cannot
drift from the films.

Reading every lesson means importing all of them, which is slow, so
:func:`refresh` writes the result to ``rerender/catalogue.json`` and
everything else reads that. Refresh after adding or changing a film.
"""

from __future__ import annotations

import ast
import json
import os
import re
import runpy
import sys
from dataclasses import asdict, dataclass, field  # noqa: F401  (asdict re-exported)
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

CATALOGUE = ROOT / "rerender" / "catalogue.json"

# Where rendered films live. Scanned one level deep, never recursively --
# deliverables/ holds voice caches with thousands of files.
VIDEO_DIRS = ("deliverables/masterclass", "deliverables", "deliverables/teasers",
              "deliverables/presenter", "exports", "exports/*", "deliverables/byod/final/*",
              "deliverables/byod-deepseek", "deliverables/byod-styled/*")
RELEASES = "deliverables/releases"

# Modules that draw or narrate rather than compute: not a source of numbers.
INFRASTRUCTURE = {
    "render_kit", "lessons", "callouts", "icons", "mascot", "frame", "app", "audio",
    "beats", "segments", "soundboard", "narration", "lexicon", "overlay_ui",
    "portrait_ui", "drama_camera", "drama_director", "drama_face", "drama_rig",
    "drama_stage", "figure", "glam_body", "glam_cast", "glam_figure", "glam_hair",
    "glam_wardrobe", "style_profiles", "shots", "deliverables", "release", "teasers",
    "creator_bridge", "park_bridge", "script", "__future__",
}

WEDGE_MODULES = {"two_v_demo/wedge_geometry.py", "two_v_demo/wedge_facts.py",
                 "two_v_demo/raw_wedge_bridge.py", "two_v_demo/wedge_why_facts.py"}
"""A film that reads any of these is about the wedge dome, and fits the world best."""

FAMILIES: dict[str, tuple[str, str | None, str]] = {
    # key: (family, superseded_by, why)
    "hype": ("Frankendome montage", "hype6", "version one of six"),
    "hype2": ("Frankendome montage", "hype6", "version two of six"),
    "hype3": ("Frankendome montage", "hype6", "version three of six"),
    "hype4": ("Frankendome montage", "hype6", "version four of six"),
    "hype5": ("Frankendome montage", "hype6", "version five of six"),
    "hype6": ("Frankendome montage", None, "the newest montage"),
    "franken": ("Frankendome montage", None, "the build lesson the montages cut from"),
    "kick": ("Campaign film", "kick2", "the campaign film, first version"),
    "kick2": ("Campaign film", None, "the campaign film, current"),
    "byod": ("Bring Your Own Dome", None, "the original script"),
    "byod_deepseek": ("Bring Your Own Dome", "byod", "another model's attempt at the same film"),
    "byod_snarky": ("Bring Your Own Dome", "byod", "a style variant of the same script"),
    "byod_polished": ("Bring Your Own Dome", "byod", "a style variant of the same script"),
    "drama": ("The Vance Network", "series", "episode one; the series contains it"),
    "series": ("The Vance Network", None, "the complete mini-series"),
    "seed_pitch": ("Stem cell dome", None, "the campaign"),
    "pitch_hero": ("Stem cell dome", None, "the short hero cut"),
    "module_build": ("Stem cell dome", None, "building one utility core"),
    "pine_value": ("The $20 pine", None, "part one"),
    "pvtwo": ("The $20 pine", None, "part two"),
    "world": ("Every dome", None, "the survey"),
    "world_chatgpt": ("Every dome", None, "another model's accountable cut"),
}

FIT: dict[str, str] = {
    # How a film whose subject is not the 2V wedge dome sits in the Cabin World.
    "hex": "The subject is a hexagonal dome, not the wedge dome. Keep the hilltop, pad and "
           "sunset; hide the wedge dome (hide={'dome', 'builder'}) and stand the hex dome on "
           "the pad, drawn by the original lesson's own geometry.",
    "zome": "The subject is a zome. Hide the wedge dome and stand the zome on the pad, from "
            "the original lesson's geometry; the wedge dome may appear once for comparison.",
    "all_domes": "Every dome type in turn. Use the pad as the turntable: hide the wedge dome "
                 "while another stands there, bring it back for the wedge chapters.",
    "world": "A survey of many domes. Stage each one on the pad in turn; the Cabin World is "
             "the constant the viewer returns to.",
    "world_chatgpt": "As 'world': each build on the pad in turn.",
    "drama": "A drama with characters. Set the scenes in the Cabin World (the deck, the "
             "stump, the log pile) instead of the original stage; keep the cast rigs.",
    "series": "As 'drama': the whole mini-series set on the hilltop.",
    "line": "The assembly line is a process; show it happening in the Cabin World -- the log, "
            "the rip, the stack, the lift -- with the builder figure doing the work.",
    "scratch": "How the pixels are made: the Cabin World itself is the example to take "
               "apart (mesh, normals, the matte, the painted sky).",
    "master": "Very long. Split it into several re-renders by part if one render is "
              "impractical; record the split in the queue notes.",
    "tree_value": "A slideshow about what one tree is worth. Make it a lesson: every slide "
                  "becomes a chapter, the log and stump in the Cabin World carry it.",
    "launcher_trailer": "A trailer for the software. Show the tools' output in the Cabin "
                        "World rather than screenshots where it can.",
}


@dataclass
class Chapter:
    number: str
    title: str
    promise: str = ""
    narration: str = ""
    equations: list = field(default_factory=list)
    bullets: list = field(default_factory=list)


@dataclass
class Item:
    key: str
    kind: str                 # lesson | presentation | slideshow
    title: str
    source: str               # the file that made the original
    originals: list           # rendered files on disk, relative to the repository
    releases: list
    note: str = ""
    family: str = ""
    superseded_by: str = ""
    family_note: str = ""
    fit: str = ""
    voice_rate: str = ""
    audio_bed: str = ""
    style: str = ""
    chapters: list = field(default_factory=list)
    number_modules: list = field(default_factory=list)
    graph_nodes: list = field(default_factory=list)
    target_key: str = ""
    target_module: str = ""
    target_file: str = ""

    @property
    def default_priority(self) -> str:
        """Superseded cuts wait; films built on the wedge dome's own modules go
        first, because the Cabin World *is* the wedge dome. The user re-ranks."""
        if self.superseded_by:
            return "low"
        return "high" if WEDGE_MODULES & set(self.number_modules) else "normal"


def _rel(path: Path) -> str:
    return path.resolve().relative_to(ROOT).as_posix()


def slug(text: str) -> str:
    text = re.sub(r"[^a-z0-9]+", "-", text.lower()).strip("-")
    return text or "film"


def _videos() -> list[Path]:
    found = []
    for folder in VIDEO_DIRS:
        dirs = [p for p in ROOT.glob(folder) if p.is_dir()] if "*" in folder else (
            [ROOT / folder] if (ROOT / folder).is_dir() else [])
        for d in dirs:
            for entry in os.scandir(d):
                if entry.is_file() and entry.name.endswith(".mp4") and not entry.name.startswith("."):
                    found.append(Path(entry.path))
    return found


def _owner_map(stems: dict[str, list[str]], videos: list[Path]) -> dict[str, list[str]]:
    """Give each video to the item whose stem it matches most specifically."""
    owned: dict[str, list[str]] = {k: [] for k in stems}
    for video in videos:
        best, best_len = None, -1
        for key, candidates in stems.items():
            for stem in candidates:
                pattern = rf"^{re.escape(stem)}(-v\d+)?(-teaser)?(-vertical|-phone)?(-v\d+)?\.mp4$"
                if re.match(pattern, video.name) and len(stem) > best_len:
                    best, best_len = key, len(stem)
        if best:
            owned[best].append(_rel(video))
    return {k: sorted(v) for k, v in owned.items()}


def _releases(stems: list[str]) -> list[str]:
    base = ROOT / RELEASES
    if not base.is_dir():
        return []
    out = []
    for entry in os.scandir(base):
        if entry.is_dir() and any(re.match(rf"^{re.escape(s)}(-v\d+)?$", entry.name) for s in stems):
            out.append(_rel(Path(entry.path)))
    return sorted(out)


def number_modules(source: Path) -> list[str]:
    """Repository modules the film imports that compute rather than draw."""
    try:
        tree = ast.parse(source.read_text(encoding="utf-8"))
    except (OSError, SyntaxError):
        return []
    names = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.ImportFrom):
            base = node.module or ""
            if node.level:   # relative: inside the same package
                package = source.parent.name
                base = f"{package}.{base}" if base else package
                for alias in node.names:
                    names.add(f"{base}.{alias.name}" if not node.module else base)
            else:
                names.add(base)
                for alias in node.names:
                    names.add(f"{base}.{alias.name}")
        elif isinstance(node, ast.Import):
            names.update(alias.name for alias in node.names)
    out = set()
    for name in names:
        parts = name.split(".")
        leaf = parts[-1]
        if leaf in INFRASTRUCTURE or leaf.startswith("lesson_"):
            continue
        path = ROOT.joinpath(*parts).with_suffix(".py")
        if path.is_file() and path.resolve() != source.resolve():
            out.add(_rel(path))
    return sorted(out)


def _graph_nodes(files: set[str]) -> list[list[str]]:
    path = ROOT / "research" / "knowledge-graph.json"
    if not path.is_file():
        return []
    graph = json.loads(path.read_text(encoding="utf-8"))
    hits = []
    for node in graph.get("nodes", []):
        if files & set(node.get("files", [])):
            hits.append([node["id"], node["label"], node.get("summary", "")])
    return hits


def _callout_bullets(callouts) -> list[str]:
    out = []
    for c in callouts or ():
        rows = getattr(c, "rows", None)
        if rows is not None:
            title = getattr(c, "title", "")
            if title:
                out.append(title)
            out.extend(_callout_bullets(rows))
            continue
        text = " ".join(str(x) for x in (getattr(c, "text", ""), getattr(c, "unit", "")) if x)
        note = getattr(c, "note", "")
        if text:
            out.append(f"{text} -- {note}" if note else text)
    return out


def _lesson_owners() -> dict[str, Path]:
    """Which module defines each lesson: the one whose top level assigns it."""
    import importlib

    from two_v_demo.lessons import Lesson

    owners: dict[str, Path] = {}
    modules = sorted((ROOT / "two_v_demo").glob("lesson_*.py")) + [ROOT / "two_v_demo" / "lessons.py"]
    for path in modules:
        if path.stem == "lesson_registry":
            continue
        module = importlib.import_module(f"two_v_demo.{path.stem}")
        tree = ast.parse(path.read_text(encoding="utf-8"))
        assigned = set()
        for node in tree.body:
            targets = node.targets if isinstance(node, ast.Assign) else (
                [node.target] if isinstance(node, ast.AnnAssign) else [])
            assigned.update(t.id for t in targets if isinstance(t, ast.Name))
        for name in assigned:
            value = getattr(module, name, None)
            if isinstance(value, Lesson):
                owners.setdefault(value.key, path)
    return owners


def _target(key: str, stem: str) -> tuple[str, str, str]:
    safe = re.sub(r"[^a-z0-9_]", "_", key.lower())
    return (f"cabin_{safe}", f"two_v_demo/lesson_cabin_{safe}.py",
            f"deliverables/masterclass/cabin-{stem}.mp4")


def lesson_items(videos: list[Path]) -> list[Item]:
    from two_v_demo.deliverables import DELIVERABLES
    from two_v_demo.lesson_registry import LESSONS

    owners = _lesson_owners()
    by_lesson = {d.lesson: d for d in DELIVERABLES}
    # Re-renders are lessons too (cabin_*); they are the output, not the queue.
    order = [d.lesson for d in DELIVERABLES if not d.lesson.startswith("cabin_")] + [
        k for k in LESSONS if k not in by_lesson and not k.startswith("cabin_")]
    stems = {}
    for key in order:
        lesson = LESSONS[key]
        d = by_lesson.get(key)
        candidates = {slug(lesson.title), key}
        if d:
            candidates.add(Path(d.filename).stem)
        stems[key] = sorted(candidates)
    owned = _owner_map(stems, videos)
    items = []
    for key in order:
        lesson = LESSONS[key]
        d = by_lesson.get(key)
        source = owners.get(key)
        stem = Path(d.filename).stem if d else slug(lesson.title)
        chapters = [Chapter(
            number=str(ch.number), title=ch.title, promise=ch.promise,
            narration=" ".join(ch.narration), equations=list(ch.equations),
            bullets=_callout_bullets(ch.callouts)) for ch in lesson.chapters]
        numbers = number_modules(source) if source else []
        family, superseded, why = FAMILIES.get(key, ("", None, ""))
        tkey, tmod, tfile = _target(key, stem)
        items.append(Item(
            key=key, kind="lesson", title=lesson.title,
            source=_rel(source) if source else "", originals=owned[key],
            releases=_releases(stems[key]), note=d.note if d else "",
            family=family, superseded_by=superseded or "", family_note=why,
            fit=FIT.get(key, ""), voice_rate=lesson.voice_rate or "",
            audio_bed=lesson.audio_bed or "", style=lesson.style, chapters=chapters,
            number_modules=numbers,
            graph_nodes=_graph_nodes({*(numbers), _rel(source) if source else ""}),
            target_key=tkey, target_module=tmod, target_file=tfile))
    return items


def presentation_items(videos: list[Path]) -> list[Item]:
    import importlib

    items = []
    for path in sorted((ROOT / "presentations").glob("*.py")):
        if path.stem.startswith("_"):
            continue
        rendered = [v for v in videos if v.parent.name == "presenter" and v.stem == path.stem]
        if not rendered:
            continue
        module = importlib.import_module(f"presentations.{path.stem}")
        deck = module.build()
        chapters = []
        for index, scene in enumerate(deck.scenes, start=1):
            bullets, narration, captions = [], [], []
            for shot in scene.shots:
                if shot.caption:
                    captions.append(shot.caption)
                if shot.panel is not None:
                    if getattr(shot.panel, "title", ""):
                        bullets.append(shot.panel.title)
                    bullets.extend(getattr(shot.panel, "bullets", ()) or ())
                narration.extend(shot.narration)
            chapters.append(Chapter(number=str(index), title=scene.title or scene.slug,
                                    promise=" / ".join(captions), narration=" ".join(narration),
                                    bullets=bullets))
        numbers = number_modules(path)
        key = f"presenter_{path.stem}"
        tkey, tmod, tfile = _target(key, path.stem.replace("_", "-"))
        doc = (module.__doc__ or "").strip().splitlines()
        items.append(Item(
            key=key, kind="presentation", title=deck.title or path.stem,
            source=_rel(path), originals=[_rel(v) for v in rendered], releases=[],
            note=doc[0] if doc else "", family="The dome case (presenter)",
            chapters=chapters, number_modules=numbers,
            graph_nodes=_graph_nodes({*numbers, _rel(path)}),
            target_key=tkey, target_module=tmod, target_file=tfile))
    return items


def slideshow_items() -> list[Item]:
    items = []
    tree = ROOT / "deliverables" / "tree-value-video"
    content = tree / "build" / "content.py"
    if content.is_file():
        import contextlib
        import io

        with contextlib.redirect_stdout(io.StringIO()):   # it prints a summary
            scenes = runpy.run_path(str(content)).get("scenes", [])
        chapters = []
        for index, s in enumerate(scenes, start=1):
            body = [" | ".join(str(c) for c in b) if isinstance(b, (list, tuple)) else str(b)
                    for b in s.get("body", [])]
            if s.get("note"):
                body.append(f"note: {s['note']}")
            if s.get("source"):
                body.append(f"source: {s['source']}")
            chapters.append(Chapter(number=str(index), title=s["title"].replace("\n", " "),
                                    narration=s.get("narration", ""), bullets=body))
        tkey, tmod, tfile = _target("tree_value", "the-many-values-of-one-tree")
        items.append(Item(
            key="tree_value", kind="slideshow", title="The many values of one tree",
            source=_rel(content),
            originals=[_rel(p) for p in (tree / "output").glob("*.mp4")], releases=[],
            note="A narrated slideshow built outside the masterclass renderer "
                 "(build/assemble.py, build.mjs).",
            family="The $20 pine", fit=FIT["tree_value"], chapters=chapters,
            target_key=tkey, target_module=tmod, target_file=tfile))
    trailer = ROOT / "deliverables" / "launcher_trailer"
    manifests = sorted(trailer.glob("render_*/video_manifest.json"))
    if manifests:
        manifest = json.loads(manifests[-1].read_text(encoding="utf-8"))
        scenes = manifest.get("scenes", manifest if isinstance(manifest, list) else [])
        chapters = []
        for index, s in enumerate(scenes, start=1):
            if not isinstance(s, dict):
                continue
            title = (s.get("headline") or s.get("title") or s.get("heading")
                     or f"scene {index}").replace("\n", " ")
            if s.get("kicker"):
                title = f"{s['kicker'].title()}: {title}"
            words = s.get("narration") or s.get("caption") or s.get("text") or ""
            chapters.append(Chapter(number=str(index), title=str(title), narration=str(words),
                                    bullets=[str(x) for x in s.get("bullets", [])]))
        tkey, tmod, tfile = _target("launcher_trailer", "dome-simulator-trailer")
        items.append(Item(
            key="launcher_trailer", kind="slideshow", title="Dome Simulator trailer",
            source=_rel(trailer / "build_launcher_trailer.py"),
            originals=[_rel(p) for p in manifests[-1].parent.glob("*.mp4")], releases=[],
            note="A silent montage with burned-in titles over the project's renders.",
            fit=FIT["launcher_trailer"], chapters=chapters,
            target_key=tkey, target_module=tmod, target_file=tfile))
    return items


def build() -> list[Item]:
    videos = _videos()
    return lesson_items(videos) + presentation_items(videos) + slideshow_items()


def refresh() -> list[Item]:
    items = build()
    CATALOGUE.write_text(json.dumps([asdict(i) for i in items], indent=1, ensure_ascii=False),
                         encoding="utf-8")
    return items


def load() -> list[Item]:
    """The catalogue as last refreshed; refreshed now if it has never been built."""
    if not CATALOGUE.is_file():
        return refresh()
    raw = json.loads(CATALOGUE.read_text(encoding="utf-8"))
    items = []
    for entry in raw:
        entry["chapters"] = [Chapter(**c) for c in entry["chapters"]]
        items.append(Item(**entry))
    return items


def by_key(items: list[Item] | None = None) -> dict[str, Item]:
    return {i.key: i for i in (items or load())}
