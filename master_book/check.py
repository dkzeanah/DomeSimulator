"""Every guard on the Master Edition, in one process.

    py -3.12 -m master_book.check            # the manuscript and its structure
    py -3.12 -m master_book.check --pdf      # and the newest built copy

What it holds the book to:

* the grid is whole -- six rungs, twelve threads, every cell written -- and
  every route points at a chapter that exists in its volume;
* the three reads are really there: on rungs one to three every chapter has
  its doing and its why, rung one its wonder question, rung two its test,
  rung three its worksheet and its warning; every route card asks its checker
  a question;
* every token resolves and no figure is typed into a worksheet where a token
  exists for it; every picture named is rendered;
* the splitting method stays the chainsaw rip -- this project's books once
  grew a froe from somebody's drafting, and it is not coming back;
* and, with ``--pdf``, that the finished copy is a letter-size book whose every
  printed page reference was filled in.
"""

from __future__ import annotations

import re
from pathlib import Path

from . import build, outline, tokens


def check_manuscript() -> list[str]:
    problems: list[str] = []
    texts = build.resolved_texts(strict=True)
    for key, text in texts.items():
        if "{{" in text:
            problems.append(f"{key}: an unresolved token")
        if re.search(r"\bfroe\b", text, re.I):
            problems.append(f"{key}: names a froe; the split is a chainsaw rip")
    for c in outline.CELLS:
        text = texts[c.anchor]
        boxes = re.findall(r"^:::box ([a-z-]+)", text, re.M)
        if outline.RUNG[c.rung].written:
            for need in ("do", "why"):
                if need not in boxes:
                    problems.append(f"{c.anchor}: no '{need}' box -- the three reads need it")
            extra = {1: "wonder", 2: "done", 3: "watch"}[c.rung]
            if extra not in boxes:
                problems.append(f"{c.anchor}: no '{extra}' box")
            words = len(re.sub(r":::.*?:::", " ", text, flags=re.S).split())
            if words < 80:
                problems.append(f"{c.anchor}: only {words} words of story")
        else:
            if "check" not in boxes:
                problems.append(f"{c.anchor}: a route card with no question for checkers")
        if c.figure:
            try:
                build.figure_path(c.figure.partition("|")[0])
            except FileNotFoundError as exc:
                problems.append(f"{c.anchor}: {exc}")
        # Worksheets quote the dome's own factors, never a typed one -- read
        # from the manuscript as written, before the tokens are filled.
        raw = c.path.read_text(encoding="utf-8")
        if re.search(r"÷ 0\.\d|× 8\b", raw):
            problems.append(f"{c.anchor}: a typed factor where a token exists")
    # A token that opens a line and is followed by a full stop becomes "5." --
    # and Markdown reads that as the next number of a list, splitting a sentence.
    for key, path in build.manuscript_files().items():
        for n, line in enumerate(path.read_text(encoding="utf-8").splitlines(), 1):
            if re.match(r"\s*\{\{[a-z_]+\.[a-z_0-9]+\}\}[.)](\s|$)", line):
                problems.append(f"{key}, line {n}: a token opens the line before a full stop; "
                                "Markdown may read it as a list number -- rewrap the line")
    return problems


def check_pdf(path: Path | None = None) -> list[str]:
    import pymupdf

    path = path or latest()
    if path is None:
        return ["no Master Edition has been built yet"]
    problems: list[str] = []
    doc = pymupdf.open(path)
    sizes = {(round(p.rect.width / 72, 2), round(p.rect.height / 72, 2)) for p in doc}
    if sizes != {(8.5, 11.0)}:
        problems.append(f"page sizes {sizes}")
    if doc.metadata.get("author") != outline.AUTHOR:
        problems.append("author missing from the metadata")
    # The read-aloud rung is only read aloud if its type is the size it was set
    # in; one table wider than the page once shrank this whole book to 79%.
    from wedge_book import print_edition as pe

    shrunk = pe.scale_problem(doc)
    if shrunk:
        problems.append(shrunk)
    toc = doc.get_toc()
    if len(toc) < len(outline.CELLS):
        problems.append(f"only {len(toc)} bookmarks")
    # Every page number this edition printed was filled in: no placeholder is
    # left on any page the edition writes itself -- the front, the rungs, the
    # volume openers and the back. Only the volumes' own chapters are skipped.
    bodies: list[range] = []
    for i, (lvl, title, n) in enumerate(toc):
        if lvl == 1 and title.startswith("Volume "):
            later = toc[i + 1:]
            first_part = next((m for l2, _, m in later if l2 == 2), n + 1)
            following = next((m for l2, _, m in later if l2 == 1), len(doc) + 1)
            bodies.append(range(first_part, following))
    for number in range(1, len(doc) + 1):
        if any(number in body for body in bodies):
            continue
        if re.search(r"(?<![\d,.])000(?![\d,])", doc[number - 1].get_text()):
            problems.append(f"page {number} still prints a placeholder page number")
    # A chapter's thread links close the chapter; alone on a page they are a
    # page of paper spent on four lines.
    starts = {title: n for _, title, n in toc}
    first_rung = next((n for _, title, n in toc if title.startswith("Rung 1")), 1)
    first_vol = next((n for lvl, title, n in toc if lvl == 1 and title.startswith("Volume ")), len(doc))
    for number in range(first_rung, first_vol):
        text = re.sub(r"^\s*\d+\s*", "", doc[number - 1].get_text()).strip()
        if text.startswith("THREAD ") and len(text) < 400:
            problems.append(f"page {number} holds nothing but a chapter's thread links")
    # A rung's chapter list is never cut in two: the page after an opener does
    # not begin part-way down the list.
    for lvl, title, n in toc:
        if lvl == 1 and title.startswith("Rung ") and n < len(doc):
            text = re.sub(r"^\s*\d+\s*", "", doc[n].get_text()).strip()
            if re.match(r"\d{2}\s", text):
                problems.append(f"{title}: its chapter list runs on to page {n + 1}")
    # The feedback sheet is torn out, so it is one page. The glossary after it
    # opens on a right-hand page, so a blank page between them is padding, not
    # a second sheet.
    feedback, after = starts.get(build.NAMED["feedback"]), starts.get(build.NAMED["glossary"])
    if feedback and after:
        spill = [n for n in range(feedback + 1, after)
                 if re.sub(r"^\s*\d+\s*", "", doc[n - 1].get_text()).strip()]
        if spill:
            problems.append(f"the feedback sheet runs on to page {spill[0]}; it should tear out as one")
    first = re.sub(r"\s", "", doc[0].get_text()).lower()
    if "masteredition" not in first:
        problems.append("the title page does not say Master Edition")
    doc.close()
    return problems


def latest() -> Path | None:
    import medialib
    folder = medialib.locate(outline.EXPORT_DIR / f"{outline.STEM}.pdf").parent
    found = sorted(folder.glob(f"{outline.STEM}*.pdf"), key=lambda p: p.stat().st_mtime)
    found = [p for p in found if re.fullmatch(rf"{re.escape(outline.STEM)}(-v\d+)?\.pdf", p.name)]
    return found[-1] if found else None


def main(argv: list[str] | None = None) -> int:
    import argparse

    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--pdf", action="store_true", help="also check the newest built copy")
    args = parser.parse_args(argv)
    outline.validate_outline()
    tokens.validate_tokens()
    problems = check_manuscript()
    if args.pdf:
        problems += check_pdf()
    for problem in problems:
        print(f"  PROBLEM: {problem}")
    if not problems:
        print(f"ok: {len(outline.CELLS)} chapters and cards, the three reads, tokens, figures"
              + (", and the built PDF" if args.pdf else ""))
    return 1 if problems else 0


if __name__ == "__main__":
    raise SystemExit(main())
