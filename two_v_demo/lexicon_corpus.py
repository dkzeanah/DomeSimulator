"""Every word this project says out loud or puts on a page, and where it came from.

The catalogue of terms and concepts in :mod:`two_v_demo.lexicon` is only honest if it
is built from what the films and the book actually say, rather than from what somebody
remembers them saying. This module gathers every script, outline and note in the
repository into one list of passages, each tagged with where it came from, so that
"how often do the films say *kerf*" is a count, and so a catalogue entry can point at
the chapter that explains it.

Nothing here is copied. Films are read from the lesson registry, the book from its
outline and manuscript, presentations by building them; a chapter rewritten tomorrow is
what the next report counts.

Sources
-------
``film``        every lesson in the registry: titles, headlines, narration, equations
``segment``     the reusable stingers, outros and calls to action, counted once
``presenter``   the presenter-engine presentations: narration, captions, panels
``book``        the *2 Trees* outline: parts, chapters, pages, beats, figure captions
``manuscript``  the *2 Trees* chapter drafts, prose only, number tokens resolved
``notes``       the author's raw notes and the collected pitch material
``codex``       the parallel Codex edition of the book
``listing``     published video descriptions
``trailer``     the launcher trailer's narration, when its manifest carries it

Identical text is stored once and remembers every place it appears. Six cuts of the
same montage share most of their chapters, and counting each copy would make the
montage look six times as talkative as it is.
"""

from __future__ import annotations

import importlib
import json
import re
from dataclasses import dataclass
from functools import lru_cache
from pathlib import Path


ROOT = Path(__file__).resolve().parent.parent

SOURCES: tuple[tuple[str, str], ...] = (
    ("film", "Films rendered by the masterclass engine"),
    ("segment", "Reusable stingers, outros and calls to action"),
    ("presenter", "Presenter-engine presentations"),
    ("book", "The 2 Trees outline"),
    ("manuscript", "The 2 Trees chapter drafts"),
    ("notes", "The author's raw notes and collected pitch material"),
    ("codex", "The Codex edition of the book"),
    ("listing", "Published video descriptions"),
    ("trailer", "The launcher trailer"),
)
SOURCE_NAMES = tuple(name for name, _ in SOURCES)

# Where a passage sits decides how it reaches an audience, which matters later: a term
# that is only ever shown and never said needs a caption, not a line of narration.
SPOKEN_FIELDS = frozenset({"narration", "headline_spoken", "line"})

NOTE_FILES: tuple[tuple[str, str], ...] = (
    ("discovering-the-wedge.txt", "The author's first account of the wedge method"),
    ("dome-spec-wedges.txt", "The raw-wedge dome specification"),
    ("presentation.txt", "Collected pitch material the presentations draw on"),
)


@dataclass(frozen=True)
class Place:
    """One spot in one work."""

    source: str
    work: str
    """Lesson key, presentation module, book chapter number or file stem."""
    locator: str
    """Chapter slug, scene/shot, page title -- whatever finds it inside the work."""
    heading: str = ""
    """The human-readable name of that spot, such as the chapter title."""

    def ref(self) -> str:
        return f"{self.source}:{self.work}/{self.locator}"


@dataclass(frozen=True)
class Passage:
    """One piece of text, and every place it appears."""

    field: str
    """What kind of text it is: ``title``, ``headline``, ``narration``, ``equation``,
    ``caption``, ``bullet``, ``stat``, ``beat``, ``purpose``, ``prose``, ``note``..."""
    text: str
    places: tuple[Place, ...]

    @property
    def spoken(self) -> bool:
        return self.field in SPOKEN_FIELDS

    @property
    def sources(self) -> frozenset[str]:
        return frozenset(place.source for place in self.places)


# ----------------------------------------------------------------------
# Text hygiene
# ----------------------------------------------------------------------

_FRONT_MATTER = re.compile(r"\A---\s*\n.*?\n---\s*\n", re.S)
_COMMENT = re.compile(r"<!--.*?-->", re.S)
_IMAGE = re.compile(r"!\[([^\]]*)\]\([^)]*\)")
_LINK = re.compile(r"\[([^\]]+)\]\([^)]*\)")
_CODE = re.compile(r"`([^`]*)`")
_EMPHASIS = re.compile(r"(\*\*|__|\*|_)(?=\S)(.+?)(?<=\S)\1")


def clean(text: str) -> str:
    """One line of plain prose: no markup, no doubled whitespace."""
    text = _CODE.sub(r"\1", text)
    text = _EMPHASIS.sub(r"\2", text)
    return " ".join(text.split())


def markdown_paragraphs(raw: str) -> tuple[list[str], list[str], list[str]]:
    """Split a Markdown file into (headings, paragraphs, image captions).

    Front matter and HTML comments are dropped: in this repository the comments are
    the outline's own instructions to the writer, which the ``book`` source already
    counts from the outline itself, and counting them twice would inflate every term
    the outline mentions.
    """
    raw = _FRONT_MATTER.sub("", raw.replace("\r\n", "\n"))
    raw = _COMMENT.sub("", raw)
    captions = [clean(alt) for alt in _IMAGE.findall(raw) if alt.strip()]
    raw = _IMAGE.sub("", raw)
    raw = _LINK.sub(r"\1", raw)
    headings: list[str] = []
    paragraphs: list[str] = []
    buffer: list[str] = []

    def flush() -> None:
        if buffer:
            paragraph = clean(" ".join(buffer))
            if paragraph:
                paragraphs.append(paragraph)
            buffer.clear()

    for line in raw.split("\n"):
        stripped = line.strip()
        if not stripped:
            flush()
            continue
        if stripped.startswith("#"):
            flush()
            heading = clean(stripped.lstrip("#").strip())
            if heading:
                headings.append(heading)
            continue
        if stripped in ("---", "***"):
            flush()
            continue
        # A list item is its own paragraph: it is a point, not part of a sentence.
        if re.match(r"^([-*+]|\d+[.)])\s+", stripped):
            flush()
            buffer.append(re.sub(r"^([-*+]|\d+[.)])\s+", "", stripped))
            flush()
            continue
        buffer.append(stripped)
    flush()
    return headings, paragraphs, captions


def plain_paragraphs(raw: str) -> list[str]:
    """Blank-line separated paragraphs of a plain text file."""
    blocks = re.split(r"\n\s*\n", raw.replace("\r\n", "\n"))
    return [clean(block) for block in blocks if clean(block)]


# ----------------------------------------------------------------------
# The readers, one per source
# ----------------------------------------------------------------------

Entry = tuple[Place, str, str]
"""(place, field, text) before identical passages are merged."""


def _segment_slugs() -> frozenset[str]:
    from .segments import SEGMENTS
    return frozenset(chapter.slug for segment in SEGMENTS.values()
                     for chapter in segment.chapters)


def _chapter_entries(source: str, work: str, chapter, headline_spoken: bool
                     ) -> list[Entry]:
    place = Place(source, work, chapter.slug, chapter.title)
    entries: list[Entry] = [(place, "title", chapter.title)]
    if chapter.promise.strip():
        entries.append((place, "headline_spoken" if headline_spoken else "headline",
                        chapter.promise))
    narration = " ".join(line.strip() for line in chapter.narration if line.strip())
    if narration:
        entries.append((place, "narration", narration))
    for equation in chapter.equations:
        if str(equation).strip():
            entries.append((place, "equation", str(equation)))
    return entries


def read_films() -> tuple[list[Entry], dict[str, str]]:
    """Every chapter of every film in the registry, segments excepted."""
    from .lesson_registry import LESSONS

    skip = _segment_slugs()
    entries: list[Entry] = []
    titles: dict[str, str] = {}
    for lesson in LESSONS.values():
        titles[lesson.key] = lesson.title
        spoken = lesson.style != "hype"
        for chapter in lesson.chapters:
            if chapter.slug in skip:
                continue
            entries.extend(_chapter_entries("film", lesson.key, chapter, spoken))
    return entries, titles


def read_segments() -> tuple[list[Entry], dict[str, str]]:
    from .segments import SEGMENTS

    entries: list[Entry] = []
    titles: dict[str, str] = {}
    for segment in SEGMENTS.values():
        titles[segment.key] = segment.title
        for chapter in segment.chapters:
            spoken = chapter.overlay != "hype"
            entries.extend(_chapter_entries("segment", segment.key, chapter, spoken))
    return entries, titles


def presentation_modules() -> tuple[str, ...]:
    folder = ROOT / "presentations"
    return tuple(sorted(
        path.stem for path in folder.glob("*.py")
        if not path.stem.startswith("_")))


def read_presentations() -> tuple[list[Entry], dict[str, str]]:
    """Build each presenter-engine presentation and read what it says and shows."""
    entries: list[Entry] = []
    titles: dict[str, str] = {}
    for name in presentation_modules():
        module = importlib.import_module(f"presentations.{name}")
        build = getattr(module, "build", None)
        if build is None:
            continue
        presentation = build()
        titles[name] = presentation.title
        for scene in presentation.scenes:
            if scene.title:
                entries.append((Place("presenter", name, scene.slug, scene.title),
                                "title", scene.title))
            for shot in scene.shots:
                place = Place("presenter", name, f"{scene.slug}/{shot.slug}",
                              scene.title or scene.slug)
                narration = " ".join(str(line).strip() for line in shot.narration
                                     if str(line).strip())
                if narration:
                    entries.append((place, "narration", narration))
                if shot.caption:
                    entries.append((place, "caption", shot.caption))
                panel = shot.panel
                if panel is None:
                    continue
                if panel.title:
                    entries.append((place, "title", panel.title))
                for bullet in panel.bullets:
                    entries.append((place, "bullet", str(bullet)))
                for equation in panel.equations:
                    entries.append((place, "equation", str(equation)))
                for stat in panel.stats:
                    label, value = (tuple(stat) + ("", ""))[:2]
                    entries.append((place, "stat", f"{label}: {value}"))
    return entries, titles


def read_book() -> tuple[list[Entry], dict[str, str]]:
    """The outline of *2 Trees*: every title, purpose, beat and caption."""
    from .book import BOOK
    from .book_tokens import resolve

    def tokens(text: str) -> str:
        return resolve(text, strict=False)

    entries: list[Entry] = []
    titles = {"2trees": BOOK.title}

    def page_entries(place: Place, pages) -> None:
        for page in pages:
            spot = Place(place.source, place.work, f"{place.locator}/{page.kind}",
                         place.heading)
            entries.append((spot, "title", tokens(page.title)))
            if page.purpose:
                entries.append((spot, "purpose", tokens(page.purpose)))
            for beat in page.beats:
                entries.append((spot, "beat", tokens(beat)))
            for figure in page.figures:
                entries.append((spot, "caption", tokens(figure.caption)))
                if figure.note:
                    entries.append((spot, "note", tokens(figure.note)))

    for matter in BOOK.front + BOOK.back:
        place = Place("book", "2trees", matter.key, matter.title)
        entries.append((place, "title", matter.title))
        page_entries(place, matter.pages)
    for part in BOOK.parts:
        place = Place("book", "2trees", f"part{part.number}", part.title)
        entries.append((place, "title", part.title))
        entries.append((place, "epigraph", tokens(part.epigraph)))
        entries.append((place, "purpose", tokens(part.promise)))
        for chapter in part.chapters:
            spot = Place("book", "2trees", f"ch{chapter.number:02d}", chapter.title)
            entries.append((spot, "title", tokens(chapter.title)))
            entries.append((spot, "headline", tokens(chapter.deck)))
            page_entries(spot, chapter.pages)
    return entries, titles


def read_manuscript() -> tuple[list[Entry], dict[str, str]]:
    """The prose actually written so far, with its number tokens filled in."""
    from .book import MANUSCRIPT_DIR
    from .book_tokens import resolve

    entries: list[Entry] = []
    titles: dict[str, str] = {}
    for path in sorted(MANUSCRIPT_DIR.rglob("*.md")):
        raw = resolve(path.read_text(encoding="utf-8", errors="replace"),
                      strict=False)
        headings, paragraphs, captions = markdown_paragraphs(raw)
        work = path.stem
        titles[work] = headings[0] if headings else work
        place = Place("manuscript", work, work, titles[work])
        for paragraph in paragraphs:
            entries.append((place, "prose", paragraph))
        for caption in captions:
            entries.append((place, "caption", caption))
    return entries, titles


def read_notes() -> tuple[list[Entry], dict[str, str]]:
    entries: list[Entry] = []
    titles: dict[str, str] = {}
    for name, title in NOTE_FILES:
        path = ROOT / name
        if not path.is_file():
            continue
        work = path.stem
        titles[work] = title
        for index, paragraph in enumerate(
                plain_paragraphs(path.read_text(encoding="utf-8", errors="replace"))):
            entries.append((Place("notes", work, f"p{index + 1:03d}", title),
                            "note", paragraph))
    return entries, titles


def read_codex() -> tuple[list[Entry], dict[str, str]]:
    entries: list[Entry] = []
    titles: dict[str, str] = {}
    folder = ROOT / "two_trees_codex" / "workspace" / "pages"
    for path in sorted(folder.glob("*.md")):
        headings, paragraphs, captions = markdown_paragraphs(
            path.read_text(encoding="utf-8", errors="replace"))
        work = path.stem
        titles[work] = headings[0] if headings else work
        place = Place("codex", work, work, titles[work])
        for heading in headings:
            entries.append((place, "title", heading))
        for paragraph in paragraphs:
            entries.append((place, "prose", paragraph))
        for caption in captions:
            entries.append((place, "caption", caption))
    return entries, titles


def read_listings() -> tuple[list[Entry], dict[str, str]]:
    """Video descriptions: only the part meant for the public, below the rule."""
    entries: list[Entry] = []
    titles: dict[str, str] = {}
    for path in sorted((ROOT / "deliverables" / "masterclass").glob("*-youtube.md")):
        raw = path.read_text(encoding="utf-8", errors="replace").replace("\r\n", "\n")
        public = raw.split("\n---\n", 1)[1] if "\n---\n" in raw else raw
        work = path.stem
        titles[work] = work.replace("-", " ")
        for index, paragraph in enumerate(plain_paragraphs(public)):
            entries.append((Place("listing", work, f"p{index + 1:03d}", titles[work]),
                            "listing", paragraph))
    return entries, titles


def _strings_under(value, keys: frozenset[str], found: list[str], key: str = "") -> None:
    if isinstance(value, dict):
        for name, inner in value.items():
            _strings_under(inner, keys, found, str(name).lower())
    elif isinstance(value, list):
        for inner in value:
            _strings_under(inner, keys, found, key)
    elif isinstance(value, str) and key in keys and value.strip():
        found.append(value)


def read_trailer() -> tuple[list[Entry], dict[str, str]]:
    """The launcher trailer's spoken lines, if its render manifest recorded them."""
    entries: list[Entry] = []
    titles: dict[str, str] = {}
    for path in sorted((ROOT / "deliverables" / "launcher_trailer").rglob(
            "video_manifest.json")):
        try:
            data = json.loads(path.read_text(encoding="utf-8", errors="replace"))
        except json.JSONDecodeError:
            continue
        work = path.parent.name
        titles[work] = clean(str(data.get("title") or "Launcher trailer"))
        scenes = data.get("scenes") if isinstance(data, dict) else None
        if isinstance(scenes, list) and scenes:
            # The manifest separates what is said from what is shown, so keep it
            # separated: a headline is type on screen, the narration is the voice.
            for scene in scenes:
                if not isinstance(scene, dict):
                    continue
                place = Place("trailer", work, f"scene{int(scene.get('id', 0)):02d}",
                              clean(str(scene.get("kicker") or "")) or titles[work])
                for key, field in (("kicker", "title"), ("headline", "headline"),
                                   ("narration", "line")):
                    value = clean(str(scene.get(key) or ""))
                    if value:
                        entries.append((place, field, value))
            continue
        found: list[str] = []
        _strings_under(data, frozenset({"narration", "text", "line", "caption"}),
                       found)
        for index, line in enumerate(dict.fromkeys(found)):
            entries.append((Place("trailer", work, f"line{index + 1:02d}",
                                  titles[work]), "line", clean(line)))
    return entries, titles


READERS = {
    "film": read_films,
    "segment": read_segments,
    "presenter": read_presentations,
    "book": read_book,
    "manuscript": read_manuscript,
    "notes": read_notes,
    "codex": read_codex,
    "listing": read_listings,
    "trailer": read_trailer,
}


# ----------------------------------------------------------------------
# The corpus
# ----------------------------------------------------------------------

@dataclass(frozen=True)
class Corpus:
    passages: tuple[Passage, ...]
    titles: dict
    """(source, work) -> the work's display title."""
    raw_entries: int
    """Entries read before identical text was merged."""

    def of(self, source: str) -> tuple[Passage, ...]:
        return tuple(p for p in self.passages if source in p.sources)

    def works(self, source: str | None = None) -> tuple[tuple[str, str], ...]:
        return tuple(key for key in self.titles
                     if source is None or key[0] == source)


def _normal(text: str) -> str:
    return " ".join(text.split())


@lru_cache(maxsize=1)
def corpus(sources: tuple[str, ...] = SOURCE_NAMES) -> Corpus:
    """Every passage from every source, identical text merged."""
    merged: dict[tuple[str, str], list[Place]] = {}
    order: list[tuple[str, str]] = []
    titles: dict[tuple[str, str], str] = {}
    raw = 0
    for source in sources:
        entries, work_titles = READERS[source]()
        for work, title in work_titles.items():
            titles[(source, work)] = title
        for place, field, text in entries:
            text = _normal(text)
            if not text:
                continue
            raw += 1
            key = (field, text)
            if key not in merged:
                merged[key] = []
                order.append(key)
            if place not in merged[key]:
                merged[key].append(place)
    passages = tuple(Passage(field, text, tuple(merged[(field, text)]))
                     for field, text in order)
    return Corpus(passages=passages, titles=titles, raw_entries=raw)


def word_count(text: str) -> int:
    return len(re.findall(r"[A-Za-z][A-Za-z'\-]*", text))


def corpus_summary(data: Corpus | None = None) -> str:
    data = data or corpus()
    lines = [f"{len(data.passages)} passages "
             f"({data.raw_entries} before identical text was merged)", ""]
    width = max(len(name) for name in SOURCE_NAMES)
    for name, description in SOURCES:
        passages = data.of(name)
        words = sum(word_count(p.text) for p in passages)
        works = len(data.works(name))
        lines.append(f"  {name:<{width}}  {works:>3} works  {len(passages):>5} passages"
                     f"  {words:>7,} words   {description}")
    total = sum(word_count(p.text) for p in data.passages)
    spoken = sum(word_count(p.text) for p in data.passages if p.spoken)
    lines += ["", f"  {total:,} words in all, {spoken:,} of them spoken aloud"]
    return "\n".join(lines)


def validate_corpus() -> None:
    """Every source must actually contribute, and provenance must survive merging."""
    data = corpus()
    assert data.passages, "the corpus is empty"
    for name in ("film", "segment", "presenter", "book", "notes"):
        assert data.of(name), f"source {name!r} contributed nothing"
    for passage in data.passages:
        assert passage.places, passage.text[:60]
        assert passage.text == _normal(passage.text)
    # Merging must not lose a place: every film chapter still finds its title.
    from .lesson_registry import LESSONS
    skip = _segment_slugs()
    titled = {(p.work, p.locator) for passage in data.of("film")
              for p in passage.places if passage.field == "title"}
    for lesson in LESSONS.values():
        for chapter in lesson.chapters:
            if chapter.slug in skip:
                continue
            assert (lesson.key, chapter.slug) in titled, (lesson.key, chapter.slug)
    print(f"lexicon_corpus OK: {len(data.passages)} passages from "
          f"{len(data.titles)} works")


if __name__ == "__main__":
    print(corpus_summary())
