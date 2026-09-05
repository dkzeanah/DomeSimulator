"""Films as a library of beats rather than one indivisible render.

A twenty-nine minute film takes ninety minutes to render, so changing one camera angle
costs ninety minutes and destroys the only copy of what was there before. That is the
wrong unit of work. A **beat** is one chapter, or a small group of chapters that explain
one idea together, rendered to its own file with its own narration.

Two things fall out of that.

*Iteration gets cheap.* Fixing the jig chapter re-renders thirty seconds, not
twenty-nine minutes, and the rest of the film is untouched on disk.

*Composition becomes yours.* The beats are ordinary MP4s in ``beats/``, so they can be
reordered, dropped, replaced with something shot on a phone, or cut together in any
editor. :mod:`two_v_demo.beat_studio_app` is the one in this repository, but nothing
depends on it.

Section files are **concatenations of their beats**, not separate renders, and the whole
film is a concatenation of the sections. So a fix costs one beat render plus a few
seconds of stream copying, and every level stays consistent by construction.

Beat videos live in ``beats/`` and never in ``deliverables/``. Deliverables are finished
things that have been published; beats are working material.
"""

from __future__ import annotations

import json
import subprocess
from dataclasses import dataclass, replace
from pathlib import Path

from .lessons import Lesson


BEATS_DIR = Path(__file__).resolve().parent.parent / "beats"


@dataclass(frozen=True)
class Section:
    """One idea, and the chapters that build it."""

    key: str
    title: str
    slugs: tuple[str, ...]
    note: str = ""


@dataclass(frozen=True)
class Beat:
    """One renderable unit: a chapter, or a few that only make sense together."""

    key: str
    title: str
    section: str
    slugs: tuple[str, ...]
    order: int

    def path(self, root: Path = BEATS_DIR, lesson_key: str = "why") -> Path:
        return root / lesson_key / self.section / f"{self.order:02d}-{self.key}.mp4"


# ----------------------------------------------------------------------
# How the wedge film divides up
# ----------------------------------------------------------------------
# Grouping is by idea, not by running order convenience: a narrative chapter and the
# math screen that proves it are one beat, because showing either without the other
# misrepresents the argument.

WHY_SECTIONS: tuple[Section, ...] = (
    Section("01-origin", "Where the method came from",
            ("open", "franken", "franken_party", "bracket", "joinery"),
            "The frankendome, its V bracket, and why the wedge build joins differently."),
    Section("02-tree", "The tree and the stick",
            ("square", "round", "yield", "split", "member", "sector",
             "short", "defects"),
            "What a mill is for, what splitting keeps, and what a defect costs."),
    Section("03-frame", "The frame and its joint",
            ("realdome", "panels", "pinwheel", "joint", "buttcut",
             "buttcut_math", "duplicate"),
            "Forty independent frames, the pinwheel, and the compound butt cut."),
    Section("04-money", "What it costs and what it saves",
            ("assumptions", "chain", "mills", "middlemen", "middlemen_math",
             "sessions", "rate", "worth", "value", "store", "overhead"),
            "Measured cutting sessions, the price stack, and the overheads nobody counts."),
    Section("05-strength", "Whether the stick is strong enough",
            ("stick", "structure"),
            "The crossover diameter, stated as a limit rather than a boast."),
    Section("06-orientation", "Four rotations, four buildings",
            ("turn", "keystone", "channel", "features", "orientation"),
            "The keystone panel, the seam duct, and what turning the wedge is worth."),
    Section("07-variation", "A dome from mixed logs",
            ("mixed", "mixed_math"),
            "Ten to fifteen inch trunks, and what actually moves."),
    Section("08-seam", "The key in every seam",
            ("fold", "dihedral"),
            "Where the dihedral variation goes."),
    Section("09-jig", "The fixture",
            ("bench", "flush", "jig"),
            "One flat board, and the cut that is never measured."),
    Section("10-close", "The building at the end",
            ("dome", "sizing", "close", "summary", "cta_share", "outro"),
            "What two trees make, and the argument on one page."),
)

# Chapters that only make sense as a pair: a claim and the screen that proves it.
# Everything else is its own beat.
PAIRED: tuple[tuple[str, ...], ...] = (
    ("franken", "franken_party"),
    ("buttcut", "buttcut_math"),
    ("middlemen", "middlemen_math"),
    ("sessions", "rate"),
    ("worth", "value"),
    ("store", "overhead"),
    ("stick", "structure"),
    ("mixed", "mixed_math"),
    ("fold", "dihedral"),
    ("dome", "sizing"),
    ("close", "summary"),
)


# Films with a hand-written plan. Everything else gets a mechanical one, which is
# worse but honest: see auto_sections.
PLANS: dict[str, tuple[Section, ...]] = {"why": WHY_SECTIONS}

AUTO_SECTION_SIZE = 6


def auto_sections(lesson: Lesson, size: int = AUTO_SECTION_SIZE) -> tuple[Section, ...]:
    """A mechanical plan for a film nobody has sectioned by hand.

    Consecutive chapters are chunked into groups, and each chunk is named after the
    chapter that opens it. This is not as good as grouping by idea -- it will
    occasionally split a claim from the screen that proves it -- but it means any film
    can be rendered as beats today, and a hand-written plan can replace it later
    without changing anything else.
    """
    chapters = list(lesson.chapters)
    sections: list[Section] = []
    for index in range(0, len(chapters), size):
        chunk = chapters[index:index + size]
        number = index // size + 1
        sections.append(Section(
            key=f"{number:02d}-{chunk[0].slug}",
            title=chunk[0].title,
            slugs=tuple(c.slug for c in chunk),
            note="Auto-grouped: no hand-written plan for this film yet.",
        ))
    return tuple(sections)


def plan_for(lesson: Lesson) -> tuple[Section, ...]:
    """The hand-written plan for this film, or a mechanical one."""
    return PLANS.get(lesson.key) or auto_sections(lesson)


def _pair_for(slug: str) -> tuple[str, ...] | None:
    for group in PAIRED:
        if slug in group:
            return group
    return None


def beat_plan(lesson: Lesson,
              sections: tuple[Section, ...] | None = None) -> tuple[Beat, ...]:
    """Split a lesson into beats, in running order.

    Only chapters the lesson actually has are included, so a plan built against an
    uncomposed lesson simply omits the segment beats rather than failing.
    """
    sections = sections or plan_for(lesson)
    present = {chapter.slug for chapter in lesson.chapters}
    order_of = {chapter.slug: index
                for index, chapter in enumerate(lesson.chapters)}

    beats: list[Beat] = []
    seen: set[str] = set()
    counter = 0
    for section in sections:
        for slug in section.slugs:
            if slug not in present or slug in seen:
                continue
            group = _pair_for(slug)
            if group is not None:
                slugs = tuple(s for s in group if s in present)
            else:
                slugs = (slug,)
            seen.update(slugs)
            counter += 1
            title = next(c.title for c in lesson.chapters if c.slug == slugs[0])
            beats.append(Beat(
                key=slugs[0],
                title=title,
                section=section.key,
                slugs=slugs,
                order=counter,
            ))

    unplaced = sorted(present - seen, key=lambda s: order_of[s])
    if unplaced:
        raise ValueError(
            f"chapters missing from the beat plan: {unplaced}. Every chapter has to "
            "belong to a section, or a beat render would silently drop it.")
    return tuple(beats)


def sub_lesson(lesson: Lesson, slugs: tuple[str, ...]) -> Lesson:
    """The same lesson cut down to a few chapters, renumbered from one.

    Narration, subtitles and the timeline are all built from ``lesson.chapters``, so a
    sub-lesson renders as a self-contained little film with its own voice track.
    """
    wanted = [c for c in lesson.chapters if c.slug in set(slugs)]
    if not wanted:
        raise ValueError(f"no chapters matched {slugs}")
    ordered = tuple(
        replace(chapter, number=f"{index + 1:02d}")
        for index, chapter in enumerate(wanted)
    )
    return replace(lesson, chapters=ordered)


# ----------------------------------------------------------------------
# Joining
# ----------------------------------------------------------------------

def concat(parts: list[Path], target: Path, ffmpeg: str | None = None) -> Path:
    """Join finished beat videos without re-encoding them.

    Stream copy, so a section costs seconds rather than minutes and the picture is bit
    for bit what the beat render produced. Every part must share codec and geometry,
    which they do because one renderer made all of them.
    """
    # A bare "ffmpeg" on PATH here is a shim that rejects standard flags, so the
    # resolver the renderer already uses picks the real one.
    from .audio import resolve_executable
    ffmpeg = resolve_executable("ffmpeg", ffmpeg)

    existing = [p for p in parts if p.is_file()]
    if not existing:
        raise FileNotFoundError(f"nothing to join into {target.name}")
    target.parent.mkdir(parents=True, exist_ok=True)
    listing = target.with_suffix(".concat.txt")
    listing.write_text(
        "".join(f"file '{p.resolve().as_posix()}'\n" for p in existing),
        encoding="utf-8")
    subprocess.run(
        [ffmpeg, "-y", "-loglevel", "error",
         "-f", "concat", "-safe", "0", "-i", str(listing),
         "-c", "copy", str(target)],
        check=True)
    listing.unlink(missing_ok=True)
    return target


def library(root: Path = BEATS_DIR, lesson_key: str = "why") -> list[dict]:
    """Every rendered beat on disk, newest metadata first.

    The studio reads this on startup so the media library populates itself; nothing has
    to be imported by hand.
    """
    base = root / lesson_key
    items: list[dict] = []
    if not base.is_dir():
        return items
    for path in sorted(base.rglob("*.mp4")):
        if path.parent.name == "sections" or path.parent == base:
            kind = "section" if path.parent.name == "sections" else "film"
        else:
            kind = "beat"
        items.append({
            "path": str(path),
            "name": path.stem,
            "section": path.parent.name,
            "kind": kind,
            "bytes": path.stat().st_size,
        })
    return items


def write_manifest(lesson: Lesson, root: Path = BEATS_DIR,
                   lesson_key: str = "why") -> Path:
    """Record what the beats are, so the studio can label them properly."""
    plan = beat_plan(lesson)
    sections = {s.key: s for s in plan_for(lesson)}
    data = {
        "lesson": lesson_key,
        "title": lesson.title,
        "sections": [
            {"key": s.key, "title": s.title, "note": s.note}
            for s in plan_for(lesson)
        ],
        "beats": [
            {
                "key": b.key, "title": b.title, "section": b.section,
                "section_title": sections[b.section].title,
                "slugs": list(b.slugs), "order": b.order,
                "file": b.path(root, lesson_key).name,
            }
            for b in plan
        ],
    }
    base = root / lesson_key
    base.mkdir(parents=True, exist_ok=True)
    path = base / "manifest.json"
    path.write_text(json.dumps(data, indent=2), encoding="utf-8")
    return path


# Films whose framing is vertical: rendering these at 1920x1080 throws away the
# composition they were written for.
VERTICAL: frozenset[str] = frozenset({"drama", "series"})
VERTICAL_SIZE = "1080x1920"
LANDSCAPE_SIZE = "1920x1080"


def size_for(lesson_key: str) -> str:
    return VERTICAL_SIZE if lesson_key in VERTICAL else LANDSCAPE_SIZE


def validate_beats() -> None:
    """Every chapter belongs to exactly one section, and pairs stay together."""
    seen: set[str] = set()
    for section in WHY_SECTIONS:
        for slug in section.slugs:
            assert slug not in seen, f"{slug} is in two sections"
            seen.add(slug)
    for group in PAIRED:
        homes = {
            section.key
            for section in WHY_SECTIONS
            for slug in group if slug in section.slugs
        }
        assert len(homes) <= 1, f"paired chapters {group} straddle sections {homes}"
