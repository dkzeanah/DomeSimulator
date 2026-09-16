"""The manuscript of *2 Trees*: files on disk, and what state they are in.

The outline in :mod:`book` says what the book *should* contain.  This module
is about what has actually been written: one Markdown file per chapter under
``book/manuscript/``, each with a small front-matter block recording its
status, plus the machinery to scaffold missing files, count what is done, and
export the lot with every live number filled in.

Why Markdown files and not a database
-------------------------------------
Because a manuscript outlives the software that made it.  Plain files in a
folder can be opened in any editor, put under version control, diffed, mailed
and recovered.  The writing desk in :mod:`book_app` is a convenience over
these files, never a container for them: close it and the book is still there.

Scaffolding
-----------
:func:`scaffold` writes a starting file for any chapter that has none.  It
never touches a file that exists -- a chapter with words in it is a
deliverable, and this repository does not overwrite those.  The scaffold
carries the chapter's own page plan as headings and its beats as comments, so
an author opens a file that already knows what it is for.
"""

from __future__ import annotations

import re
from dataclasses import dataclass
from datetime import date
from pathlib import Path

from . import book_tokens
from .book import (BOOK, EXPORT_DIR, MANUSCRIPT_DIR, Book, Chapter, Matter,
                   Page)


STATUSES = ("outline", "drafting", "draft", "revised", "final")
"""What state a chapter is in. ``outline`` means the scaffold is untouched."""

FRONT_MATTER = re.compile(r"\A---\n(.*?)\n---\n", re.S)


# ----------------------------------------------------------------------
# One chapter's file
# ----------------------------------------------------------------------

@dataclass(frozen=True)
class ChapterFile:
    """A chapter's manuscript file, and what is in it."""

    chapter: Chapter
    path: Path
    exists: bool
    status: str
    updated: str
    body: str

    @property
    def words(self) -> int:
        """Words actually written, not counting headings or comments."""
        return count_words(self.body)

    @property
    def target(self) -> int:
        return self.chapter.words

    @property
    def progress(self) -> float:
        return self.words / self.target if self.target else 0.0

    @property
    def unknown_tokens(self) -> tuple[str, ...]:
        return book_tokens.unknown_tokens(self.body)

    @property
    def used_tokens(self) -> tuple[str, ...]:
        return book_tokens.used_tokens(self.body)

    @property
    def is_started(self) -> bool:
        return self.exists and self.status != "outline"


def count_words(text: str) -> int:
    """Words of prose, ignoring headings, comments and token braces.

    Counting the scaffold's own headings would make an untouched chapter look
    a fifth written, which is the sort of encouraging lie that stops being
    funny in month three.
    """
    kept: list[str] = []
    in_comment = False
    for line in text.splitlines():
        stripped = line.strip()
        # HTML comments span lines, and the scaffold's whole page plan lives
        # inside one. Testing only whether a line *starts* with "<!--" counts
        # every continuation line as prose, which made an untouched scaffold
        # report several hundred words written.
        if in_comment:
            if "-->" in stripped:
                in_comment = False
            continue
        if stripped.startswith("<!--"):
            if "-->" not in stripped:
                in_comment = True
            continue
        if not stripped:
            continue
        if stripped.startswith(("#", ">", "-->", "|", "---")):
            continue
        if stripped.startswith("![") or stripped.startswith("<!--"):
            continue
        if stripped.startswith(("*", "-", "+")) and len(stripped) < 3:
            continue
        kept.append(stripped)
    prose = " ".join(kept)
    prose = book_tokens.TOKEN_PATTERN.sub("0", prose)
    return len([word for word in prose.split() if any(c.isalnum()
                                                      for c in word)])


def parse_front_matter(text: str) -> tuple[dict[str, str], str]:
    """Split a manuscript file into its metadata and its prose."""
    match = FRONT_MATTER.match(text)
    if not match:
        return {}, text
    meta: dict[str, str] = {}
    for line in match.group(1).splitlines():
        if ":" in line:
            name, _, value = line.partition(":")
            meta[name.strip()] = value.strip()
    return meta, text[match.end():]


def read_chapter(chapter: Chapter, root: Path = MANUSCRIPT_DIR
                 ) -> ChapterFile:
    """Load one chapter's file, or report that it has none."""
    path = chapter.path(root)
    if not path.is_file():
        return ChapterFile(chapter=chapter, path=path, exists=False,
                           status="outline", updated="", body="")
    text = path.read_text(encoding="utf-8")
    meta, body = parse_front_matter(text)
    status = meta.get("status", "outline")
    if status not in STATUSES:
        status = "outline"
    return ChapterFile(chapter=chapter, path=path, exists=True,
                       status=status, updated=meta.get("updated", ""),
                       body=body)


def write_chapter(chapter: Chapter, body: str, status: str = "drafting",
                  root: Path = MANUSCRIPT_DIR) -> Path:
    """Save one chapter, stamping its status and the date.

    This is the one place in the book pipeline that overwrites a file, and it
    is meant to: it is the editor's save. Everything downstream of it --
    figures, exports -- versions instead.
    """
    if status not in STATUSES:
        raise ValueError(f"unknown status {status!r}; "
                         f"choose from {', '.join(STATUSES)}")
    path = chapter.path(root)
    path.parent.mkdir(parents=True, exist_ok=True)
    header = (f"---\n"
              f"chapter: {chapter.number}\n"
              f"title: {chapter.title}\n"
              f"strand: {chapter.strand}\n"
              f"status: {status}\n"
              f"target: {chapter.words}\n"
              f"updated: {date.today().isoformat()}\n"
              f"---\n")
    path.write_text(header + body.lstrip("\n"), encoding="utf-8")
    return path


# ----------------------------------------------------------------------
# Scaffolding
# ----------------------------------------------------------------------

def scaffold_body(chapter: Chapter) -> str:
    """A starting file that already knows what the chapter is for."""
    lines = [f"# {chapter.number}. {chapter.title}", "",
             f"*{chapter.deck}*", ""]
    if chapter.corrects:
        lines += [f"> **This chapter corrects something.** {chapter.corrects}",
                  ""]
    if chapter.derives:
        lines += ["<!-- Every number in this chapter must come from:",
                  *[f"     - {name}" for name in chapter.derives],
                  "     Quote them as live tokens in double braces, never as",
                  "     typed digits. The Numbers panel lists every one. -->",
                  ""]

    for page in chapter.pages:
        lines += [f"## {page.title}", "",
                  f"<!-- [{page.kind}] {page.purpose}"]
        if page.words:
            lines.append(f"     target: about {page.words} words")
        if page.beats:
            lines.append("     make these points, in order:")
            lines += [f"       {index}. {beat}"
                      for index, beat in enumerate(page.beats, start=1)]
        for figure in page.figures:
            lines.append(f"     figure [{figure.key}] ({figure.source}): "
                         f"{figure.caption or '(caption to write)'}")
        lines += ["-->", ""]
        for figure in page.figures:
            lines += [f"![{figure.caption}](../../deliverables/book/figures/"
                      f"{figure.key}.png)", ""]
        lines += ["", ""]
    return "\n".join(lines)


def sync_filenames(root: Path = MANUSCRIPT_DIR, book: Book = BOOK,
                   on_line=None) -> tuple[tuple[Path, Path], ...]:
    """Rename chapter files whose number changed when the outline moved.

    A manuscript filename carries its chapter number so a folder listing
    reads in order. That is worth having, and the price is that inserting a
    chapter leaves every later file misnamed. This renames them, reports
    every move, and refuses to overwrite: if the target already exists it is
    left alone and named in the return, because two chapters fighting over
    one filename is a thing a person should look at.

    Matching is by the title, not the number, so a file only moves when its
    chapter genuinely moved.
    """
    if not root.is_dir():
        return ()
    existing = {path.name: path for path in root.glob("*.md")}
    moved: list[tuple[Path, Path]] = []
    for chapter in book.chapters:
        want = chapter.path(root)
        if want.exists():
            continue
        tail = chapter._title_slug("-")
        matches = [path for name, path in existing.items()
                   if name.endswith(f"-{tail}.md")]
        if len(matches) != 1:
            continue
        source = matches[0]
        if want.exists():
            if on_line:
                on_line(f"    SKIP {source.name}: {want.name} already there")
            continue
        source.rename(want)
        moved.append((source, want))
        if on_line:
            on_line(f"    {source.name} -> {want.name}")
    return tuple(moved)


def scaffold(root: Path = MANUSCRIPT_DIR, book: Book = BOOK,
             on_line=None) -> tuple[Path, ...]:
    """Create a starting file for every chapter that has none.

    Never touches an existing file. A chapter someone has written into is a
    deliverable, and this repository's rule about those is that they do not
    get replaced by a machine.
    """
    root.mkdir(parents=True, exist_ok=True)
    written: list[Path] = []
    for chapter in book.chapters:
        path = chapter.path(root)
        if path.exists():
            if on_line:
                on_line(f"    kept  {path.name}")
            continue
        write_chapter(chapter, scaffold_body(chapter), status="outline",
                      root=root)
        written.append(path)
        if on_line:
            on_line(f"    wrote {path.name}")
    return tuple(written)


# ----------------------------------------------------------------------
# Where the book is up to
# ----------------------------------------------------------------------

@dataclass(frozen=True)
class Progress:
    """How much of the book exists."""

    files: tuple[ChapterFile, ...]

    @property
    def words(self) -> int:
        return sum(item.words for item in self.files)

    @property
    def target(self) -> int:
        return sum(item.target for item in self.files)

    @property
    def fraction(self) -> float:
        return self.words / self.target if self.target else 0.0

    @property
    def started(self) -> int:
        return sum(1 for item in self.files if item.is_started)

    @property
    def by_status(self) -> dict[str, int]:
        counts = {status: 0 for status in STATUSES}
        for item in self.files:
            counts[item.status] = counts.get(item.status, 0) + 1
        return counts

    @property
    def broken_tokens(self) -> tuple[tuple[int, str], ...]:
        """Every bad token in the manuscript, with its chapter number."""
        out: list[tuple[int, str]] = []
        for item in self.files:
            for name in item.unknown_tokens:
                out.append((item.chapter.number, name))
        return tuple(out)


def progress(root: Path = MANUSCRIPT_DIR, book: Book = BOOK) -> Progress:
    return Progress(tuple(read_chapter(chapter, root)
                          for chapter in book.chapters))


def progress_report(root: Path = MANUSCRIPT_DIR) -> str:
    state = progress(root)
    lines = [f"{BOOK.title}",
             f"{state.words:,} of {state.target:,} words "
             f"({state.fraction * 100:.1f}%), "
             f"{state.started} of {len(state.files)} chapters started",
             ""]
    for status in STATUSES:
        lines.append(f"  {status:<10} {state.by_status.get(status, 0)}")
    lines.append("")
    for item in state.files:
        bar = "#" * int(item.progress * 20)
        lines.append(f"  {item.chapter.number:>2}. "
                     f"{item.chapter.title[:38]:<38} "
                     f"{item.words:>6,}/{item.target:<6,} "
                     f"{item.status:<9} {bar}")
    if state.broken_tokens:
        lines += ["", "BROKEN TOKENS -- these would print as [?name]:"]
        for number, name in state.broken_tokens:
            lines.append(f"  ch {number}: {{{{{name}}}}}")
    return "\n".join(lines)


# ----------------------------------------------------------------------
# Export
# ----------------------------------------------------------------------

def matter_path(matter: Matter, where: str,
                root: Path = MANUSCRIPT_DIR) -> Path:
    """Where a front- or back-matter section's own file lives.

    Front and back matter is written the same way chapters are -- a file you
    can open in any editor -- rather than being generated from the outline
    every time. The outline still says what each section is *for*; this is
    where the actual words go.
    """
    return root / where / f"{matter.key}.md"


def read_matter(matter: Matter, where: str,
                root: Path = MANUSCRIPT_DIR) -> str:
    """One matter section's prose, or empty if nobody has written it."""
    path = matter_path(matter, where, root)
    if not path.is_file():
        return ""
    _meta, body = parse_front_matter(path.read_text(encoding="utf-8"))
    return body.strip()


def _matter_markdown(matter: Matter, where: str = "front",
                     root: Path = MANUSCRIPT_DIR) -> str:
    """A matter section: its own prose if written, its plan if not."""
    written = read_matter(matter, where, root)
    if written:
        return written
    lines = [f"# {matter.title}", ""]
    for page in matter.pages:
        lines += [f"## {page.title}", "", f"*{page.purpose}*", ""]
        for figure in page.figures:
            lines += [f"![{figure.caption}](figures/{figure.key}.png)", ""]
        if page.beats:
            lines += [f"{index}. {beat}"
                      for index, beat in enumerate(page.beats, start=1)]
            lines.append("")
        lines.append("**(not written yet)**")
        lines.append("")
    return "\n".join(lines)


def export_markdown(root: Path = MANUSCRIPT_DIR,
                    out_dir: Path = EXPORT_DIR,
                    book: Book = BOOK,
                    strict: bool = True,
                    include_unwritten: bool = True) -> Path:
    """One Markdown file containing the whole book, numbers resolved.

    Never overwrites: a previous export may already be with a reader, so a
    second export writes ``-v2``. Same rule as every other deliverable here.
    """
    from .deliverables import next_version_path

    parts: list[str] = [
        f"# {book.title}", "", f"*{book.subtitle}*", "",
        f"Exported {date.today().isoformat()}. Every figure in this file was "
        f"computed at export time from the geometry in this repository.",
        "", "---", ""]

    for matter in book.front:
        parts += [_matter_markdown(matter, "front", root), "", "---", ""]

    for part in book.parts:
        parts += [f"# Part {part.number}: {part.title}", "",
                  f"> {part.epigraph}", "", f"*{part.promise}*", "",
                  "---", ""]
        for chapter in part.chapters:
            item = read_chapter(chapter, root)
            if not item.exists and not include_unwritten:
                continue
            if item.body.strip():
                parts += [item.body.strip(), ""]
            else:
                parts += [f"## {chapter.number}. {chapter.title}", "",
                          f"*{chapter.deck}*", "",
                          "**(not written yet)**", ""]
            parts += ["---", ""]

    for matter in book.back:
        parts += [_matter_markdown(matter, "back", root), "", "---", ""]

    text = "\n".join(parts)
    text = book_tokens.resolve(text, strict=strict)

    out_dir.mkdir(parents=True, exist_ok=True)
    path = out_dir / "2-trees.md"
    if path.exists():
        path = next_version_path(path)
    path.write_text(text, encoding="utf-8")
    return path


def export_outline(out_dir: Path = EXPORT_DIR, book: Book = BOOK) -> Path:
    """The outline as a standalone document, for planning rather than
    reading."""
    from .book import outline_text
    from .deliverables import next_version_path

    out_dir.mkdir(parents=True, exist_ok=True)
    path = out_dir / "2-trees-outline.txt"
    if path.exists():
        path = next_version_path(path)
    path.write_text(outline_text(book, detail="pages"), encoding="utf-8")
    return path


# ----------------------------------------------------------------------
# The self-test
# ----------------------------------------------------------------------

def validate_manuscript() -> None:
    """The manuscript machinery works on a scratch copy, not on the book."""
    import tempfile

    with tempfile.TemporaryDirectory() as temporary:
        root = Path(temporary) / "manuscript"

        # Scaffolding creates one file per chapter, and every scaffold
        # parses back as the chapter it came from.
        written = scaffold(root)
        assert len(written) == len(BOOK.chapters), \
            (len(written), len(BOOK.chapters))
        for chapter in BOOK.chapters:
            item = read_chapter(chapter, root)
            assert item.exists, chapter.number
            assert item.status == "outline", (chapter.number, item.status)
            # A scaffold has structure but no prose: it must not count as
            # progress or the whole book looks a fifth done on day one.
            assert item.words < 200, (chapter.number, item.words)
            assert f"## {chapter.pages[0].title}" in item.body, chapter.number

        # Running it twice must not touch anything.
        again = scaffold(root)
        assert again == (), again

        # Writing prose is counted; the scaffold's headings are not.
        chapter = BOOK.chapter(1)
        prose = "word " * 500
        write_chapter(chapter, f"# heading\n\n{prose}", status="draft",
                      root=root)
        item = read_chapter(chapter, root)
        assert item.status == "draft", item.status
        assert 490 <= item.words <= 510, item.words
        assert item.updated, "a save must stamp a date"

        # Tokens in the prose resolve, and a bad one is reported rather
        # than silently printed.
        write_chapter(chapter, "The frame has {{frame.members}} members "
                               "and {{frame.nonsense}} of these.",
                      status="drafting", root=root)
        item = read_chapter(chapter, root)
        assert item.unknown_tokens == ("frame.nonsense",), \
            item.unknown_tokens
        assert "frame.members" in item.used_tokens, item.used_tokens

        state = progress(root)
        assert state.broken_tokens == ((1, "frame.nonsense"),), \
            state.broken_tokens
        assert state.started >= 1, state.started

        # A strict export refuses to print the broken token.
        out = Path(temporary) / "out"
        try:
            export_markdown(root, out, strict=True)
        except ValueError as exc:
            assert "frame.nonsense" in str(exc), exc
        else:  # pragma: no cover - the guard is the point
            raise AssertionError("strict export accepted a broken token")

        # Fixed, it exports, and the numbers are really substituted.
        write_chapter(chapter, "The frame has {{frame.members}} members.",
                      status="draft", root=root)
        path = export_markdown(root, out, strict=True)
        text = path.read_text(encoding="utf-8")
        assert "{{" not in text, "an export still contains raw tokens"
        assert "120 members" in text, text[:400]

        # A second export versions rather than replacing the first.
        second = export_markdown(root, out, strict=True)
        assert second != path, (path, second)
        assert path.exists(), "the first export was destroyed"

        outline = export_outline(out)
        assert outline.exists() and outline.stat().st_size > 2000, outline

    print(f"book_manuscript OK: scaffolds {len(BOOK.chapters)} chapters, "
          f"counts prose only, refuses broken tokens, versions exports")


if __name__ == "__main__":
    print(progress_report())
    print()
    validate_manuscript()
