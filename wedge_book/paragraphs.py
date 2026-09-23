"""Join one-sentence paragraphs back into paragraphs.

Chapters 1 and 2 arrived written at one sentence per paragraph -- 99 and 97
percent of their blocks, against 33 to 55 percent everywhere else in the
book. On a printed page that reads as a list of assertions rather than
prose, and it is the single most recognisable tell that a machine wrote it.
It is also the first thing a reader and a KDP sample page see.

This joins them. It does not rewrite, reorder, summarise or add a word: the
only thing that changes is where the blank lines are. Run it twice and the
second run does nothing.

WHAT IS LEFT ALONE

* the shouted headings this book uses inside sections, in capitals
* bullets and dashes
* indented blocks, which are the builder's tables and would be destroyed
* anything already two sentences or longer, which was written as a paragraph
* a short line ending in a colon, which is introducing the thing below it
* the last sentence of a run, when it is short and lands like a beat --
  because that is a real device in this book's voice and joining it into
  the paragraph above throws the punch away
"""

from __future__ import annotations

import re

from . import store

SHOUT = re.compile(r"^[A-Z0-9][A-Z0-9 ,.'\-/()&]{3,}$")
SENTENCE_END = re.compile(r"[.!?][\"')\]]?(?:\s|$)")

#: Sentences per joined paragraph. Four is a paragraph; six is a wall.
TARGET = 3
MAX_WORDS = 95

#: A trailing sentence shorter than this is left standing alone, because a
#: short line after a paragraph is a beat and this book uses it deliberately.
BEAT_WORDS = 11


def sentences(text: str) -> int:
    return len(SENTENCE_END.findall(text.strip()))


def words(text: str) -> int:
    return len(text.split())


def joinable(block: str) -> bool:
    """Is this a plain prose block that may be merged with its neighbours?"""
    stripped = block.strip()
    if not stripped:
        return False
    if block.startswith(("    ", "\t")):
        return False
    if stripped.startswith(("* ", "- ", "> ", "#")):
        return False
    if "\n" in stripped and any(
            ln.lstrip().startswith(("* ", "- ")) for ln in stripped.split("\n")):
        return False
    if SHOUT.match(stripped):
        return False
    if stripped.endswith(":"):
        return False
    # A display formula stands on its own line. Joining one into the prose
    # around it does not lose a word, so the "not one word changed" check
    # passes -- and then the PDF exporter, which recognises a formula only
    # when it is a block by itself, prints the LaTeX source in the middle of
    # a sentence. That happened on 24 pages.
    if "$$" in stripped:
        return False
    if sentences(stripped) > 1:
        return False
    return True


def join(text: str, target: int = TARGET) -> str:
    """Rebuild a section's blocks with prose gathered into paragraphs."""
    blocks = re.split(r"\n\s*\n", text.strip())
    out: list[str] = []
    run: list[str] = []

    def flush() -> None:
        if not run:
            return
        # A short final sentence is a beat. Leave it on its own line.
        tail = None
        if len(run) > 1 and words(run[-1]) <= BEAT_WORDS:
            tail = run.pop()
        while run:
            take: list[str] = []
            while run and len(take) < target:
                candidate = " ".join(take + [run[0]])
                if take and words(candidate) > MAX_WORDS:
                    break
                take.append(run.pop(0))
            out.append(" ".join(take))
        if tail is not None:
            out.append(tail)

    for block in blocks:
        if joinable(block):
            run.append(" ".join(block.split()))
            continue
        flush()
        run = []
        out.append(block.rstrip())
    flush()
    return "\n\n".join(out).strip()


def one_sentence_fraction(text: str) -> float:
    """How much of a section is one-sentence paragraphs, ignoring furniture."""
    single = total = 0
    for block in re.split(r"\n\s*\n", (text or "").strip()):
        stripped = block.strip()
        if (not stripped or SHOUT.match(stripped)
                or stripped.startswith(("* ", "- ", "    "))):
            continue
        total += 1
        if sentences(stripped) <= 1:
            single += 1
    return single / total if total else 0.0


def rewrite(chapters: tuple[str, ...] = ("1.", "2."),
            book: store.Book | None = None, save: bool = True) -> dict:
    """Join the prose of the named chapters and report what moved."""
    book = book or store.load_json()
    report: dict[str, tuple[float, float, int, int]] = {}
    for part in book.parts:
        for chapter in part.chapters:
            if not chapter.title.startswith(chapters):
                continue
            before_blocks = after_blocks = 0
            before_frac = after_frac = 0.0
            n = 0
            for section in chapter.sections:
                if not section.body:
                    continue
                before = section.body
                before_frac += one_sentence_fraction(before)
                before_blocks += len(re.split(r"\n\s*\n", before.strip()))
                section.body = join(before)
                after_frac += one_sentence_fraction(section.body)
                after_blocks += len(re.split(r"\n\s*\n",
                                             section.body.strip()))
                n += 1
                # Not one word may change. Only the blank lines may.
                assert before.split() == section.body.split(), (
                    f"{chapter.title} / {section.title}: joining altered "
                    f"the words")
            if n:
                report[chapter.title] = (before_frac / n, after_frac / n,
                                         before_blocks, after_blocks)
    if save:
        store.save_json(book)
    return report


def validate_paragraphs(book: store.Book | None = None) -> None:
    """No chapter may go back to one sentence per paragraph.

    The threshold is deliberately loose. Short paragraphs are a real part of
    this book's voice and several chapters sit near half; what is being
    caught is the 97-to-99 percent case, which is not a voice but an
    artefact.
    """
    book = book or store.load_json()
    bad = []
    for part in book.parts:
        for chapter in part.chapters:
            fractions = [one_sentence_fraction(s.body)
                         for s in chapter.sections if s.body]
            if not fractions:
                continue
            mean = sum(fractions) / len(fractions)
            if mean > 0.80:
                bad.append(f"{chapter.title}: {mean * 100:.0f}%")
    assert not bad, (
        "these chapters are written at one sentence per paragraph, which "
        "reads as a list of assertions rather than prose:\n  "
        + "\n  ".join(bad))


def main(argv: list[str] | None = None) -> int:
    import argparse

    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--chapters", default="1.,2.",
                        help="comma-separated chapter number prefixes")
    parser.add_argument("--dry-run", action="store_true")
    args = parser.parse_args(argv)

    chapters = tuple(c.strip() for c in args.chapters.split(",") if c.strip())
    report = rewrite(chapters, save=not args.dry_run)
    for title, (before, after, blocks_before, blocks_after) in report.items():
        print(f"  {title}")
        print(f"      one-sentence paragraphs  "
              f"{before * 100:5.1f}%  ->  {after * 100:5.1f}%")
        print(f"      blocks                   "
              f"{blocks_before:5d}   ->  {blocks_after:5d}")
    if args.dry_run:
        print("  (dry run, nothing written)")
    else:
        print(" ", store.sync("json-wins")["progress"])
    return 0


if __name__ == "__main__":
    raise SystemExit(main())


DISPLAY_IN_PROSE = re.compile(r"\$\$.+?\$\$", re.S)


def unwrap_display(text: str) -> str:
    """Put display formulas back on their own lines.

    Repairs sections where an earlier run of :func:`join` merged a ``$$``
    block into the prose around it. Splits on the formula and keeps the
    words either side, in order.
    """
    out: list[str] = []
    for block in re.split(r"\n\s*\n", text.strip()):
        if "$$" not in block or block.startswith(("    ", "\t")):
            out.append(block.rstrip())
            continue
        cursor = 0
        for match in DISPLAY_IN_PROSE.finditer(block):
            before = block[cursor:match.start()].strip()
            if before:
                out.append(" ".join(before.split()))
            out.append(" ".join(match.group(0).split()))
            cursor = match.end()
        tail = block[cursor:].strip()
        if tail:
            out.append(" ".join(tail.split()))
    return "\n\n".join(out).strip()


def repair_display(book: store.Book | None = None, save: bool = True) -> int:
    """Split every paragraph that has a display formula buried in it."""
    book = book or store.load_json()
    fixed = 0
    for _part, chapter, section in book.sections:
        if not section.body or "$$" not in section.body:
            continue
        before = section.body
        after = unwrap_display(before)
        if after != before:
            assert before.split() == after.split(), (
                f"{chapter.title} / {section.title}: repair lost words")
            section.body = after
            fixed += 1
    if save and fixed:
        store.save_json(book)
    return fixed


def validate_display_alone(book: store.Book | None = None) -> None:
    """No display formula may share a block with prose.

    The PDF exporter recognises a formula only when its block contains
    nothing else. One buried in a sentence is printed as its own LaTeX
    source, which is how 24 pages of this book once carried an
    inverse-cosine formula, backslashes and braces and all, in the middle
    of a line of prose.
    """
    book = book or store.load_json()
    bad = []
    for _part, chapter, section in book.sections:
        for block in re.split(r"\n\s*\n", (section.body or "").strip()):
            if "$$" not in block:
                continue
            if not re.fullmatch(r"\s*\$\$.+?\$\$\s*", block, re.S):
                bad.append(f"{chapter.title} / {section.title}")
                break
    assert not bad, (
        "these sections have a display formula buried in a paragraph; the "
        "exporter will print its LaTeX source:\n  " + "\n  ".join(bad))
