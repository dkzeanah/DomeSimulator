"""Renumber the book's chapters into the order the outline lists them.

Chapter numbers live in four places that must agree: ``number=`` in
:mod:`wedge_book.outline`, the manuscript file name (``NN-title.md``), the
file's front matter and heading (``chapter: NN``, ``# NN. Title``), and every
plate's ``book_chapter`` in :mod:`wedge_book.plates`. Prose never types a
number -- it writes ``{{ch.ref}}`` -- so nothing else moves.

To add a chapter, define it in the outline with a temporary number of 900 or
more, put it where it belongs in its Part's ``chapters`` tuple, and run this.
Every chapter is then numbered by its place in the book.

    py -3.12 -m wedge_book.renumber           # show what would move
    py -3.12 -m wedge_book.renumber --apply   # move it
"""

from __future__ import annotations

import re
from pathlib import Path

from . import store

OUTLINE = store.ROOT / "wedge_book" / "outline.py"
PLATES = store.ROOT / "wedge_book" / "plates.py"
MANUSCRIPT = store.BOOK_DIR / "manuscript"
TEMPORARY = 900


def plan() -> dict[str, tuple[int, int]]:
    """ref -> (current number, number by position in the book)."""
    from . import outline

    return {c.key: (c.number, n) for n, c in enumerate(outline.BOOK.chapters, 1)}


def apply(moves: dict[str, tuple[int, int]]) -> list[str]:
    from two_v_demo.book import Chapter

    from . import outline

    done = []
    changed = {ref: (a, b) for ref, (a, b) in moves.items() if a != b}
    if not changed:
        return done
    old_to_new = {a: b for a, b in changed.values()}

    # The outline: one ``number=N, ref="REF"`` per chapter.
    text = OUTLINE.read_text(encoding="utf-8")
    for ref, (a, b) in changed.items():
        old = f'number={a}, ref="{ref}"'
        assert text.count(old) == 1, f"outline: expected one {old!r}"
        text = text.replace(old, f'number={b}, ref="{ref}"')
    OUTLINE.write_text(text, encoding="utf-8")

    # The manuscript: move every file first to a temporary name, then home,
    # so a chapter moving onto another's old number never collides.
    by_ref = {c.key: c for c in outline.BOOK.chapters}
    staged = []
    for ref, (a, b) in changed.items():
        chapter = by_ref[ref]
        old_path = MANUSCRIPT / f"{a:02d}-{chapter._title_slug('-')}.md"
        if not old_path.is_file():
            continue                      # a new chapter with no prose yet
        tmp = old_path.with_name(f"_renumber_{ref}.md")
        old_path.rename(tmp)
        staged.append((tmp, chapter, a, b))
    for tmp, chapter, a, b in staged:
        body = tmp.read_text(encoding="utf-8")
        body = re.sub(r"^chapter: \d+$", f"chapter: {b}", body, count=1, flags=re.M)
        body = re.sub(rf"^# {a}\. ", f"# {b}. ", body, count=1, flags=re.M)
        target = MANUSCRIPT / f"{b:02d}-{chapter._title_slug('-')}.md"
        assert not target.exists(), target
        target.write_text(body, encoding="utf-8")
        tmp.unlink()
        done.append(f"{a:>3} -> {b:<3} {target.name}")

    # The plates: each one's book_chapter, through the same map.
    plates_text = PLATES.read_text(encoding="utf-8")

    def move(match: re.Match) -> str:
        n = int(match.group(2))
        return f"{match.group(1)}{old_to_new.get(n, n)}"
    plates_text = re.sub(r'(Plate\("[^"]+", "[^"]+", "[^"]+", )(\d+)\b', move, plates_text)
    PLATES.write_text(plates_text, encoding="utf-8")
    return done


def main(argv: list[str] | None = None) -> int:
    import argparse

    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--apply", action="store_true")
    args = parser.parse_args(argv)
    moves = plan()
    changed = {r: m for r, m in moves.items() if m[0] != m[1]}
    for ref, (a, b) in changed.items():
        print(f"  {ref:<16} {a:>3} -> {b}")
    print(f"{len(changed)} chapters to renumber")
    if args.apply and changed:
        for line in apply(moves):
            print("  moved", line)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
