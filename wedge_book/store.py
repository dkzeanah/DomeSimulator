"""Where The Wedge Method lives: one database, one folder tree, one JSON.

The book has three homes and they are deliberately different shapes.

* **The JSON project** (``wedge_method_book_app/*.wedgebook.json``) is what the
  Tkinter app opens and saves. It is the app's own format and this module does
  not change it; it reads it and writes it back.
* **The database** (``book_wedge/wedge_book.sqlite3``) is the queryable copy.
  It answers the questions a folder tree cannot: which sections are empty, how
  many words are in Part III, which figures a chapter still owes. It is
  committed, because a book's state is project history and not a build
  artefact.
* **The folder tree** (``book_wedge/``) is the writing surface. One folder per
  part, one folder per chapter, one Markdown file per section. It is what a
  person edits, what git diffs read sensibly, and what the PDF is built from.

All three hold the same text. :func:`sync` moves it between them and always in
a stated direction, because a two-way sync that guesses is a two-way sync that
eventually eats a paragraph.

The rule everywhere: **Markdown is the source of truth once a section has been
written into the tree.** The JSON and the database follow it. That way an hour
of editing in a text editor is never lost to an app that had the file open.
"""

from __future__ import annotations

import json
import re
import sqlite3
import unicodedata
from dataclasses import dataclass, field
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
PROJECT_JSON = ROOT / "wedge_method_book_app" / "the_wedge_method.wedgebook.json"
BOOK_DIR = ROOT / "book_wedge"
DB_PATH = BOOK_DIR / "wedge_book.sqlite3"

CREDIT = ("Generated with code @ "
          "https://github.com/dkzeanah/DomeSimulator")
"""The label every figure in this book carries.

Stated once here so a figure cannot be published without it and cannot drift
into a second wording.
"""


# ----------------------------------------------------------------------
# Naming
# ----------------------------------------------------------------------

def slug(text: str) -> str:
    """A folder or file name from a heading, stable across runs.

    Stable matters more than pretty: these names are what git tracks, so a
    slug that changes because a title gained a comma produces a delete and an
    add instead of an edit.
    """
    text = unicodedata.normalize("NFKD", text)
    text = text.encode("ascii", "ignore").decode("ascii")
    # Drop a leading "Part III - " or "12. " so the ordinal prefix this
    # module adds is the only ordinal in the name.
    text = re.sub(r"^\s*(part\s+[ivxlc]+\s*[-—:]\s*|\d+\.\s*)", "", text,
                  flags=re.IGNORECASE)
    text = re.sub(r"[^\w\s-]", "", text).strip().lower()
    text = re.sub(r"[\s_]+", "-", text)
    return re.sub(r"-{2,}", "-", text).strip("-") or "untitled"


def numbered(index: int, text: str) -> str:
    return f"{index:02d}-{slug(text)}"


# ----------------------------------------------------------------------
# The book in memory
# ----------------------------------------------------------------------

@dataclass
class Section:
    title: str
    body: str = ""
    notes: str = ""
    index: int = 0

    @property
    def words(self) -> int:
        return len(self.body.split())

    @property
    def written(self) -> bool:
        return bool(self.body.strip())


@dataclass
class Chapter:
    title: str
    body: str = ""
    notes: str = ""
    index: int = 0
    sections: list[Section] = field(default_factory=list)

    @property
    def words(self) -> int:
        return len(self.body.split()) + sum(s.words for s in self.sections)

    @property
    def written(self) -> int:
        return sum(1 for s in self.sections if s.written)


@dataclass
class Part:
    title: str
    body: str = ""
    notes: str = ""
    index: int = 0
    chapters: list[Chapter] = field(default_factory=list)

    @property
    def words(self) -> int:
        return len(self.body.split()) + sum(c.words for c in self.chapters)


@dataclass
class Book:
    metadata: dict
    parts: list[Part]
    voice: str = ""
    production: str = ""
    illustration_checklist: list = field(default_factory=list)
    chapter_illustration_plan: dict = field(default_factory=dict)
    front_matter: dict = field(default_factory=dict)

    # -- counts ------------------------------------------------------
    @property
    def sections(self) -> list[tuple[Part, Chapter, Section]]:
        return [(p, c, s) for p in self.parts for c in p.chapters
                for s in c.sections]

    @property
    def words(self) -> int:
        return sum(p.words for p in self.parts)

    @property
    def written(self) -> int:
        return sum(1 for _p, _c, s in self.sections if s.written)

    def progress(self) -> str:
        total = len(self.sections)
        return (f"{self.written} of {total} sections, "
                f"{self.words:,} words")


# ----------------------------------------------------------------------
# JSON in, JSON out
# ----------------------------------------------------------------------

def load_json(path: Path | None = None) -> Book:
    """The app's project file, as objects."""
    path = path or PROJECT_JSON
    raw = json.loads(path.read_text(encoding="utf-8"))
    parts = []
    for pi, praw in enumerate(raw.get("parts", []), start=1):
        chapters = []
        for ci, craw in enumerate(praw.get("chapters", []), start=1):
            sections = [
                Section(sraw.get("title", ""), sraw.get("body") or "",
                        sraw.get("notes") or "", si)
                for si, sraw in enumerate(craw.get("sections", []), start=1)
            ]
            chapters.append(Chapter(craw.get("title", ""),
                                    craw.get("body") or "",
                                    craw.get("notes") or "", ci, sections))
        parts.append(Part(praw.get("title", ""), praw.get("body") or "",
                          praw.get("notes") or "", pi, chapters))
    return Book(
        metadata=raw.get("metadata", {}),
        parts=parts,
        voice=raw.get("author_voice_instructions", ""),
        production=raw.get("production_elements", ""),
        illustration_checklist=raw.get("illustration_checklist", []),
        chapter_illustration_plan=raw.get("chapter_illustration_plan", {}),
        front_matter=raw.get("front_matter", {}),
    )


def save_json(book: Book, path: Path | None = None) -> Path:
    """Write the book back into the app's own format, in place.

    Round-trips every key the app knows about. Anything this module does not
    model is read from the file on disk and put back untouched, so saving here
    can never silently drop a field a future version of the app adds.
    """
    path = path or PROJECT_JSON
    raw = json.loads(path.read_text(encoding="utf-8"))
    raw["parts"] = [
        {
            "title": p.title, "body": p.body, "notes": p.notes,
            "chapters": [
                {
                    "title": c.title, "body": c.body, "notes": c.notes,
                    "sections": [
                        {"title": s.title, "body": s.body, "notes": s.notes}
                        for s in c.sections
                    ],
                }
                for c in p.chapters
            ],
        }
        for p in book.parts
    ]
    path.write_text(json.dumps(raw, indent=2, ensure_ascii=False),
                    encoding="utf-8")
    return path


# ----------------------------------------------------------------------
# The folder tree
# ----------------------------------------------------------------------

FRONT_MATTER_RE = re.compile(r"^---\n(.*?)\n---\n", re.DOTALL)


def _md(title: str, kind: str, body: str, notes: str, **extra) -> str:
    """One Markdown file: a small header, then the prose.

    The header is there so a file can be moved, renamed or opened on its own
    and still say what it is. It is deliberately not YAML with a parser
    behind it -- it is four lines a person can read and edit.
    """
    lines = ["---", f"title: {title}", f"kind: {kind}"]
    for key, value in extra.items():
        lines.append(f"{key}: {value}")
    lines.append("---")
    lines.append("")
    lines.append(f"# {title}")
    lines.append("")
    lines.append(body.strip() or "<!-- not written yet -->")
    if notes.strip():
        lines += ["", "<!-- NOTES", notes.strip(), "-->"]
    return "\n".join(lines) + "\n"


def _read_md(path: Path) -> tuple[str, str]:
    """The body and notes back out of one Markdown file."""
    text = path.read_text(encoding="utf-8")
    text = FRONT_MATTER_RE.sub("", text, count=1)
    notes = ""
    match = re.search(r"<!-- NOTES\n(.*?)\n-->\s*$", text, re.DOTALL)
    if match:
        notes = match.group(1).strip()
        text = text[: match.start()]
    # Drop the H1 the writer sees; the title lives in the outline.
    text = re.sub(r"^\s*#\s+.*?\n", "", text, count=1)
    body = text.strip()
    if body == "<!-- not written yet -->":
        body = ""
    return body, notes


def part_dir(part: Part) -> Path:
    return BOOK_DIR / numbered(part.index, part.title)


def chapter_dir(part: Part, chapter: Chapter) -> Path:
    return part_dir(part) / numbered(chapter.index, chapter.title)


def write_tree(book: Book, base: Path | None = None) -> int:
    """Fan the whole book out: part folders, chapter folders, section files.

    Returns how many files were written. Existing files are overwritten, so
    the caller is expected to have synced the other way first if the tree is
    the newer copy -- :func:`sync` does exactly that.
    """
    base = base or BOOK_DIR
    base.mkdir(parents=True, exist_ok=True)
    written = 0
    for part in book.parts:
        pdir = base / numbered(part.index, part.title)
        pdir.mkdir(parents=True, exist_ok=True)
        (pdir / "00-part.md").write_text(
            _md(part.title, "part", part.body, part.notes), encoding="utf-8")
        written += 1
        for chapter in part.chapters:
            cdir = pdir / numbered(chapter.index, chapter.title)
            cdir.mkdir(parents=True, exist_ok=True)
            (cdir / "00-chapter.md").write_text(
                _md(chapter.title, "chapter", chapter.body, chapter.notes,
                    figures=str(cdir / "figures")), encoding="utf-8")
            (cdir / "figures").mkdir(exist_ok=True)
            written += 1
            for section in chapter.sections:
                name = numbered(section.index, section.title) + ".md"
                (cdir / name).write_text(
                    _md(section.title, "section", section.body, section.notes),
                    encoding="utf-8")
                written += 1
    return written


def read_tree(book: Book, base: Path | None = None) -> int:
    """Pull edited Markdown back into ``book``. Returns how many changed.

    Matching is by position, not by filename, because a writer who renames a
    heading should not orphan their own text. The outline is the skeleton;
    the files hang off it in order.
    """
    base = base or BOOK_DIR
    if not base.is_dir():
        return 0
    changed = 0
    for part in book.parts:
        pdir = base / numbered(part.index, part.title)
        if not pdir.is_dir():
            continue
        path = pdir / "00-part.md"
        if path.is_file():
            body, notes = _read_md(path)
            if body != part.body or notes != part.notes:
                part.body, part.notes = body, notes
                changed += 1
        for chapter in part.chapters:
            cdir = pdir / numbered(chapter.index, chapter.title)
            if not cdir.is_dir():
                continue
            path = cdir / "00-chapter.md"
            if path.is_file():
                body, notes = _read_md(path)
                if body != chapter.body or notes != chapter.notes:
                    chapter.body, chapter.notes = body, notes
                    changed += 1
            for section in chapter.sections:
                path = cdir / (numbered(section.index, section.title) + ".md")
                if not path.is_file():
                    continue
                body, notes = _read_md(path)
                if body != section.body or notes != section.notes:
                    section.body, section.notes = body, notes
                    changed += 1
    return changed


# ----------------------------------------------------------------------
# The database
# ----------------------------------------------------------------------

SCHEMA = """
CREATE TABLE IF NOT EXISTS part (
    idx INTEGER PRIMARY KEY, title TEXT NOT NULL,
    body TEXT NOT NULL DEFAULT '', notes TEXT NOT NULL DEFAULT '');
CREATE TABLE IF NOT EXISTS chapter (
    part_idx INTEGER NOT NULL, idx INTEGER NOT NULL, title TEXT NOT NULL,
    body TEXT NOT NULL DEFAULT '', notes TEXT NOT NULL DEFAULT '',
    PRIMARY KEY (part_idx, idx));
CREATE TABLE IF NOT EXISTS section (
    part_idx INTEGER NOT NULL, chapter_idx INTEGER NOT NULL,
    idx INTEGER NOT NULL, title TEXT NOT NULL,
    body TEXT NOT NULL DEFAULT '', notes TEXT NOT NULL DEFAULT '',
    words INTEGER NOT NULL DEFAULT 0,
    PRIMARY KEY (part_idx, chapter_idx, idx));
CREATE TABLE IF NOT EXISTS figure (
    key TEXT PRIMARY KEY, chapter INTEGER, title TEXT NOT NULL,
    caption TEXT NOT NULL DEFAULT '', path TEXT NOT NULL DEFAULT '',
    recipe TEXT NOT NULL DEFAULT '', credit TEXT NOT NULL DEFAULT '',
    built INTEGER NOT NULL DEFAULT 0);
"""


def connect(path: Path | None = None) -> sqlite3.Connection:
    path = path or DB_PATH
    path.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(path)
    conn.executescript(SCHEMA)
    return conn


def write_db(book: Book, path: Path | None = None) -> int:
    """Replace the database's copy of the outline and prose."""
    conn = connect(path)
    try:
        with conn:
            conn.execute("DELETE FROM part")
            conn.execute("DELETE FROM chapter")
            conn.execute("DELETE FROM section")
            rows = 0
            for part in book.parts:
                conn.execute(
                    "INSERT INTO part (idx, title, body, notes) "
                    "VALUES (?, ?, ?, ?)",
                    (part.index, part.title, part.body, part.notes))
                rows += 1
                for chapter in part.chapters:
                    conn.execute(
                        "INSERT INTO chapter (part_idx, idx, title, body, "
                        "notes) VALUES (?, ?, ?, ?, ?)",
                        (part.index, chapter.index, chapter.title,
                         chapter.body, chapter.notes))
                    rows += 1
                    for section in chapter.sections:
                        conn.execute(
                            "INSERT INTO section (part_idx, chapter_idx, idx,"
                            " title, body, notes, words) "
                            "VALUES (?, ?, ?, ?, ?, ?, ?)",
                            (part.index, chapter.index, section.index,
                             section.title, section.body, section.notes,
                             section.words))
                        rows += 1
        return rows
    finally:
        conn.close()


def unwritten(path: Path | None = None) -> list[tuple[int, int, int, str]]:
    """Every section still empty, in book order. The writing queue."""
    conn = connect(path)
    try:
        return list(conn.execute(
            "SELECT part_idx, chapter_idx, idx, title FROM section "
            "WHERE TRIM(body) = '' ORDER BY part_idx, chapter_idx, idx"))
    finally:
        conn.close()


def word_counts(path: Path | None = None) -> list[tuple[str, int, int]]:
    """Per chapter: title, words, sections written. What the app shows."""
    conn = connect(path)
    try:
        return list(conn.execute(
            "SELECT c.title, COALESCE(SUM(s.words), 0), "
            "  COALESCE(SUM(CASE WHEN TRIM(s.body) <> '' THEN 1 ELSE 0 END), 0)"
            " FROM chapter c LEFT JOIN section s"
            "   ON s.part_idx = c.part_idx AND s.chapter_idx = c.idx"
            " GROUP BY c.part_idx, c.idx ORDER BY c.part_idx, c.idx"))
    finally:
        conn.close()


# ----------------------------------------------------------------------
# Sync
# ----------------------------------------------------------------------

def sync(direction: str = "tree-wins", path: Path | None = None) -> dict:
    """Move the book between its three homes, in a stated direction.

    ``tree-wins``  -- read the Markdown, then write the JSON and the database.
                     The default, because the tree is the writing surface.
    ``json-wins``  -- take the app's project file and fan it out again. Use
                     after the Tkinter app has been the thing doing the
                     editing.

    Never guesses. A sync that picks a winner per file by timestamp is how a
    morning's work goes missing.
    """
    if direction not in ("tree-wins", "json-wins"):
        raise ValueError("direction must be 'tree-wins' or 'json-wins'")
    book = load_json(path)
    pulled = 0
    if direction == "tree-wins":
        pulled = read_tree(book)
        if pulled:
            save_json(book, path)
    files = write_tree(book)
    rows = write_db(book)
    return {"direction": direction, "pulled_from_tree": pulled,
            "files_written": files, "db_rows": rows,
            "progress": book.progress()}


def validate_store() -> None:
    """Prove the three homes agree before anything writes a book into them."""
    import tempfile

    book = load_json()
    validate_reference_dome(book)
    validate_no_mitre_claim(book)
    validate_cut_not_scaled(book)
    validate_no_placeholders(book)
    assert book.parts, "no parts"
    assert len(book.sections) > 100, len(book.sections)
    assert book.metadata.get("title"), "the book has no title"

    # Slugs must be stable and collision-free inside a chapter, or two
    # sections share a file and one of them is lost.
    for part in book.parts:
        names = [numbered(c.index, c.title) for c in part.chapters]
        assert len(set(names)) == len(names), (part.title, names)
        for chapter in part.chapters:
            files = [numbered(s.index, s.title) for s in chapter.sections]
            assert len(set(files)) == len(files), (chapter.title, files)

    assert slug("Part III - Building the Dome") == "building-the-dome"
    assert slug("12. Doors and Windows") == "doors-and-windows"
    assert slug("Wide side / narrow side orientation") == \
        "wide-side-narrow-side-orientation"

    # A round trip through the tree must not change one character of prose.
    with tempfile.TemporaryDirectory() as folder:
        base = Path(folder)
        write_tree(book, base)
        before = [(s.title, s.body, s.notes) for _p, _c, s in book.sections]
        changed = read_tree(book, base)
        after = [(s.title, s.body, s.notes) for _p, _c, s in book.sections]
        assert changed == 0, f"{changed} sections changed on a round trip"
        assert before == after, "the tree round trip altered the prose"

        # And an edit in the tree has to come back. This used to pick an
        # unwritten section so the placeholder was there to overwrite, and
        # then the book was finished and there were none -- so the check
        # that Markdown wins started raising StopIteration instead of
        # testing anything. Any section will do; put it back afterwards.
        part, chapter, section = book.sections[0]
        target = (base / numbered(part.index, part.title)
                  / numbered(chapter.index, chapter.title)
                  / (numbered(section.index, section.title) + ".md"))
        assert target.is_file(), target
        original = section.body
        try:
            target.write_text(
                target.read_text(encoding="utf-8") + "\n\nEdited on disk.\n",
                encoding="utf-8")
            assert read_tree(book, base) >= 1
            assert "Edited on disk." in section.body, section.title
        finally:
            section.body = original

    # The database has to answer the questions the tree cannot.
    with tempfile.TemporaryDirectory() as folder:
        db = Path(folder) / "t.sqlite3"
        rows = write_db(book, db)
        assert rows == len(book.parts) + sum(
            len(p.chapters) for p in book.parts) + len(book.sections)
        queue = unwritten(db)
        assert len(queue) == len(book.sections) - book.written
        counts = word_counts(db)
        assert len(counts) == sum(len(p.chapters) for p in book.parts)
        assert any(words > 0 for _t, words, _n in counts)

    assert CREDIT.startswith("Generated with code @ https://github.com/")


if __name__ == "__main__":
    validate_store()
    book = load_json()
    print(f"The Wedge Method: {book.progress()}")
    for title, words, done in word_counts(DB_PATH) if DB_PATH.exists() else []:
        print(f"  {title[:44]:<44} {words:>6,} words  {done} written")

# ----------------------------------------------------------------------
# The two-domes trap
# ----------------------------------------------------------------------

def _other_dome_figures() -> dict[str, str]:
    """Figures that belong to the *other* dome in this repository.

    ``wedge_geometry.build_plan()`` sizes a dome from the log it is cut out
    of and lands at 22.0 feet. ``seed_world.geometry()`` sizes one from a
    six-foot member and lands at 19.416 feet -- and that is the one the
    campaign film prices, the one the figures are rendered from, and the one
    this book calls the reference build.

    Both are right about their own building, so nothing raises when a
    chapter reaches for the wrong one. Three sections of this book described
    a 22-foot dome with a 369-square-foot floor before anybody noticed, and
    369 is the pad platform rather than any dome's floor at all.

    So: the numbers that only make sense for the other dome are listed here
    by name, with what the reference build says instead.
    """
    import seed_model
    import seed_world
    import two_v_demo.wedge_geometry as wedge

    geometry = seed_world.geometry()
    plan = wedge.build_plan()
    seed = seed_model.seed_geometry()
    return {
        f"{plan.radius_in:.1f}":
            f"the log-sized dome's radius; this book's is "
            f"{geometry.radius_in:.4f} in",
        f"{2.0 * plan.radius_in / 12.0:.1f}-foot":
            f"the log-sized dome's diameter; this book's is "
            f"{2.0 * geometry.radius_in / 12.0:.3f} ft",
        "369 square feet of floor":
            f"the pad platform, not a floor; the dome's is "
            f"{seed.floor_decagon_sqft:.0f} sq ft",
    }


def validate_reference_dome(book: "Book | None" = None) -> None:
    """No section may quote the other dome's figures as this one's."""
    book = book or load_json()
    wrong = []
    for _part, chapter, section in book.sections:
        text = section.body or ""
        if not text:
            continue
        for figure, why in _other_dome_figures().items():
            if figure in text:
                wrong.append(f"{chapter.title} / {section.title}: "
                             f"{figure!r} is {why}")
    assert not wrong, "the book is describing the wrong dome:\n  " + \
        "\n  ".join(wrong)

#: How a list of offending sections is laid out in an assertion message.
NEWLINE_BULLET = "\n  "


#: Text that means "nobody has written this yet", however confident it looks.
#:
#: The book reported 152 of 152 sections written while chapter 1 still
#: carried the instruction to write one of them, because `written` means
#: "the body is not empty" and an instruction is not empty. Four pages in.
PLACEHOLDERS: tuple[str, ...] = (
    "Put the finished manuscript prose",
    "Do not include these bracketed instructions",
    "TODO",
    "FIXME",
    "Lorem ipsum",
    "[write ",
    "[TK]",
)


def validate_no_placeholders(book: "Book | None" = None) -> None:
    """No section may ship with its own instructions in it."""
    book = book or load_json()
    found = []
    for _part, chapter, section in book.sections:
        body = section.body or ""
        for mark in PLACEHOLDERS:
            if mark.lower() in body.lower():
                found.append(f"{chapter.title} / {section.title}: {mark!r}")
    assert not found, (
        f"{len(found)} sections still carry placeholder text:"
        + NEWLINE_BULLET + NEWLINE_BULLET.join(found))

    # And a section that is a sentence long is not written either, whatever
    # the count says. Twelve words is generous: the shortest real section in
    # this book is a stated refusal and it is longer than that.
    thin = [f"{c.title} / {s.title} ({len(s.body.split())} words)"
            for _p, c, s in book.sections
            if s.body and len(s.body.split()) < 12]
    assert not thin, (
        f"{len(thin)} sections are too short to be written:"
        + NEWLINE_BULLET + NEWLINE_BULLET.join(thin))


def validate_no_mitre_claim(book: "Book | None" = None) -> None:
    """The book may not repeat a claim the films already corrected.

    ``lesson_wedge_why`` has a chapter that names the mitre error and then
    corrects it, because a published film that says something wrong gets a
    chapter rather than a silent re-cut. The book then said the wrong thing
    again in two places and built two more chapters on top of it.

    What the solve gives: the butt IS a compound cut. The bevel is constant
    at half the sector angle, because it comes from how the log was split
    rather than from where the member sits, and the mitre takes three values
    across all 120 members. What the pinwheel removes is the shared vertex,
    not the mitre.
    """
    from two_v_demo import wedge_why_facts

    cut = wedge_why_facts.butt_cut_model()
    assert cut["bevel_is_constant"], "the bevel is no longer constant"
    assert cut["setting_count"] <= 4, cut["setting_count"]

    banned = (
        "No compound mitre",
        "No end of any member is mitred",
        "no member is mitred",
        "Every cut is a plain angle",
        "every cut is a plain angle",
        "no mitre anywhere",
    )
    # A correction has to be allowed to quote the thing it is correcting, or
    # this check forbids the very pattern the repository requires: name the
    # error, then fix it. So the test is per paragraph, and a paragraph that
    # retracts the claim in the same breath is doing the right thing.
    retracting = ("not true", "an earlier", "earlier version",
                  "earlier telling", "corrected", "correction",
                  "is wrong", "was wrong")
    book = book or load_json()
    wrong = []
    for _part, chapter, section in book.sections:
        for para in (section.body or "").split("\n\n"):
            lowered = para.lower()
            if any(mark in lowered for mark in retracting):
                continue
            for phrase in banned:
                if phrase in para:
                    wrong.append(
                        f"{chapter.title} / {section.title}: {phrase!r}")
    assert not wrong, (
        "the book is repeating the mitre claim the films corrected; the butt "
        f"is a compound cut of a {cut['bevel_deg']:.1f} degree bevel and one "
        f"of {cut['setting_count']:.0f} mitres:" + NEWLINE_BULLET
        + NEWLINE_BULLET.join(wrong))



def validate_cut_not_scaled(book: "Book | None" = None) -> None:
    """The strut table must subtract a bite, not scale the chord.

    The cut length is the chord minus what the pinwheel takes at each end,
    and that bite is set by the member's WIDTH. A member does not get wider
    because the dome does, so the bite is identical at every diameter --
    proven here rather than asserted, by solving the same pinwheel at two
    radii and comparing.

    The table got this wrong once. It used a fixed ratio, which is exactly
    right at the reference build and wrong at every other row, by more than
    eight inches at the small end. Every stick.
    """
    import seed_world
    import two_v_demo.wedge_geometry as wedge

    geometry = seed_world.geometry()
    width = geometry.member_width_in
    a_factor = geometry.long_edge_in / geometry.radius_in

    def bite(radius_in: float) -> float:
        panels = wedge.pinwheel_panels(radius_in, width)
        longest = max(m.length_in for p in panels for m in p.members)
        return radius_in * a_factor - longest

    small, large = bite(48.0), bite(180.0)
    assert abs(small - large) < 1e-6, (
        f"the bite is no longer constant with radius: {small} vs {large}; "
        f"the strut table's arithmetic depends on it being so")

    # And the published table has to carry the solver's own reference row.
    book = book or load_json()
    for _part, chapter, section in book.sections:
        if section.title != "Strut tables":
            continue
        text = section.body or ""
        for member in geometry.members:
            cut = f"{member.stock_length_in:.3f}"
            assert cut in text, (
                f"the strut table no longer prints the solved "
                f"{member.edge_type} cut of {cut} in")
        assert "MINUS" in text.upper() or "minus a constant" in text, (
            "the strut table must say the cut is the chord minus a bite")
        return
    raise AssertionError("the strut table has gone")
