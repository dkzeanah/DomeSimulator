"""Build Domology: the manuscript and the code, composed into pages.

::

    py -3.12 -m domology.build              a draft: layout, reader and PDF
    py -3.12 -m domology.build --no-pdf     layout and reader only (fast)
    py -3.12 -m domology.build --png        also page images, for the reading video
    py -3.12 -m domology.build --publish    copy the results into deliverables/domology
    py -3.12 -m domology.build --final      a publishing build: refuses while any author
                                            request, placeholder or missing plate remains

A draft is written to ``domology/.cache/build`` and overwritten each time: that
folder is a workbench. ``--publish`` is what puts files under ``deliverables``,
and it never replaces one -- the interior becomes ``domology-interior-v2.pdf``
when a first one exists, as this repository does for every render.

Three back-matter chapters are written by this module rather than by hand: the
glossary (from the project's lexicon), *The Numbers Behind This Book* (every
live figure the prose quotes, its value and what computes it) and the plate
index (every illustration, the tool that drew it and the page it is on). The
book is laid out twice so that the index can quote the pages of the first pass.
"""

from __future__ import annotations

import argparse
import json
import os
import re
import shutil
import subprocess
import time
from datetime import date
from pathlib import Path

from . import config as C
from . import outline
from . import plates as P
from . import science
from .layout import BookInfo, Entry, Layout, PlateInfo, SheetInfo, compose_book
from .markup import (TOKEN, Block, Chapter, Resolver, Span, _assign_ids, parse_chapter,
                     parse_file, parse_header, parse_inline, reset_tokens, smarten)

BUILD = C.CACHE / "build"
META_FILE = C.MANUSCRIPT / "0-front" / "_meta.md"
"""Front-matter details only the author can give: dedication, epigraph, ISBN."""

PLACEHOLDER = re.compile(r"\[[A-Z]{2,}[A-Z ]*(?::[^\]]*)?\]")
"""A bracketed request like ``[AUTHOR NAME]`` or ``[ISBN]`` left in printed text."""

TOOL_NAMES = {
    "film": "Film engine",
    "scene": "Film engine, scene built for this book",
    "forge": "Dome Forge",
    "line": "Assembly Line",
    "chart": "Chart drawn from the code",
    "composite": "Dome Forge, two views",
}

GROUP_TITLES = {
    "dm": "Geometry, comparisons and the catalogue",
    "hist": "Dates from the project's history",
    "dmch": "Chapter numbers",
    "tree": "The tree",
    "member": "One member",
    "dome": "The dome two trees make",
    "frame": "The frame",
    "edges": "Edges and members",
    "seam": "The seams and the fold",
    "jig": "The jig",
    "work": "The work",
    "fuel": "Fuel",
    "saw": "The saw",
    "versus": "A wedge against a board",
    "board": "The two-by-four",
    "method_a": "Method A, worked",
    "route": "Routes from tree to frame",
    "roundtrip": "The round trip",
    "value": "What the fortnight keeps",
    "why": "Why build this way",
    "pine": "The twenty-dollar pine",
    "house": "Where a house's price goes",
    "stack": "The house, stacked",
    "trailer": "The manufactured home",
    "time": "How long a house takes",
    "wage": "Wages",
    "lumber": "The lumber peak",
    "shape": "What the shape saves",
}
GROUP_ORDER = ("dm", "hist", "tree", "member", "dome", "frame", "edges", "seam", "jig",
               "work", "fuel", "saw", "versus", "board", "method_a", "route", "roundtrip",
               "value", "why", "pine", "house", "stack", "trailer", "time", "wage",
               "lumber", "shape", "dmch")


# ----------------------------------------------------------------------
# Reading the manuscript
# ----------------------------------------------------------------------

def git_commit() -> str:
    try:
        result = subprocess.run(["git", "rev-parse", "--short", "HEAD"], cwd=C.ROOT,
                                capture_output=True, text=True, timeout=20)
        return result.stdout.strip() or "unknown"
    except (OSError, subprocess.SubprocessError):
        return "unknown"


def front_extra() -> dict:
    if META_FILE.exists():
        meta, _body, _lines = parse_header(META_FILE.read_text(encoding="utf-8"))
        return meta
    return {}


def read_chapters(resolver: Resolver) -> dict[str, Chapter]:
    """Every hand-written chapter in reading order; a missing file becomes its
    outline scaffold, so the book always builds whole."""
    chapters: dict[str, Chapter] = {}
    for section, plan, book in outline.all_chapters():
        if plan.id in outline.GENERATED:
            continue
        path = outline.manuscript_path(plan, book, section)
        if path.exists():
            chapter = parse_file(path, resolver)
        else:
            chapter = parse_chapter(outline.scaffold(section, plan, book), resolver, path,
                                    plan.id)
            chapter.status = "missing"
        if chapter.id != plan.id:
            # The plan's id wins, so a renamed header cannot orphan annotations.
            chapter.id = plan.id
            _assign_ids(chapter.blocks, plan.id)
        if "title" not in chapter.meta:
            chapter.title = smarten(plan.title)
        if "deck" not in chapter.meta:
            chapter.deck = smarten(plan.deck)
        if plan.opener and not chapter.meta.get("opener"):
            chapter.meta["opener"] = plan.opener
        chapter.meta.setdefault("section", section)
        chapters[plan.id] = chapter
    return chapters


def spans_of(obj):
    """Every span inside a block, list, table or note, depth first."""
    if isinstance(obj, Span):
        yield obj
        for inner in obj.note or ():
            yield from spans_of(inner)
    elif isinstance(obj, Block):
        yield from spans_of(obj.spans)
        yield from spans_of(obj.items)
        for child in obj.children:
            yield from spans_of(child)
    elif isinstance(obj, (list, tuple)):
        for item in obj:
            yield from spans_of(item)


def placed_plates(chapter: Chapter) -> list[str]:
    found = [chapter.meta["opener"]] if chapter.meta.get("opener") else []
    found += [block.ref for block in chapter.blocks if block.kind == "plate"]
    return found


def placed_sheets(chapter: Chapter) -> list[str]:
    return [block.ref for block in chapter.blocks if block.kind == "math"]


# ----------------------------------------------------------------------
# What the paginator asks for
# ----------------------------------------------------------------------

class Lookups:
    """The three callables the paginator is handed: plates, math sheets, tables."""

    def __init__(self, resolver: Resolver):
        self.resolver = resolver
        self.sheet_cache: dict[str, SheetInfo] = {}
        self.table_cache: dict[str, tuple | None] = {}

    def plate(self, plate_id: str) -> PlateInfo | None:
        plate = P.BY_ID.get(plate_id)
        if plate is None:
            return None
        path, aspect = P.aspect_of(plate)
        return PlateInfo(plate.id, smarten(plate.title),
                         parse_inline(plate.caption, self.resolver), plate.credit, path, aspect)

    def sheet(self, key: str) -> SheetInfo | None:
        if key not in science.SHEETS:
            return None
        if key not in self.sheet_cache:
            sheet = science.SHEETS[key]
            try:
                rows = tuple(sheet.rows())
            except Exception as error:  # a broken sheet prints as broken, never as blank
                rows = (f"this worksheet failed to compute: {type(error).__name__}: {error}",
                        "The code has to be fixed before this box can print.")
            self.sheet_cache[key] = SheetInfo(key, sheet.title, rows, sheet.source)
        return self.sheet_cache[key]

    def table(self, key: str) -> tuple | None:
        from . import tables
        if key not in self.table_cache:
            self.table_cache[key] = tables.rows(key)
        return self.table_cache[key]


# ----------------------------------------------------------------------
# The chapters the build writes itself
# ----------------------------------------------------------------------

def _chapter(cid: str, blocks: list[Block]) -> Chapter:
    plan = outline.by_id()[cid][1]
    _assign_ids(blocks, cid)
    return Chapter(cid, smarten(plan.title), smarten(plan.deck), "generated", blocks,
                   {"section": "back"})


def _para(*spans: Span) -> Block:
    return Block("para", list(spans))


def _cells(*texts: str) -> list:
    return [[Span(text)] for text in texts]


def glossary_chapter(chapters: dict[str, Chapter], resolver: Resolver) -> Chapter:
    from two_v_demo import lexicon
    text = " ".join(block.plain() for chapter in chapters.values()
                    for block in chapter.blocks).lower()
    chosen = []
    for term in lexicon.terms():
        names = {term.name.lower(), term.key.lower(), *(alias.lower() for alias in term.aliases)}
        if any(name and re.search(rf"(?<![a-z]){re.escape(name)}(?:s|es)?(?![a-z])", text)
               for name in names):
            chosen.append(term)
    chosen.sort(key=lambda term: term.name.lower())
    blocks = [_para(Span("Every word below is used somewhere in this book. The definitions "
                         "are the project's own, from the lexicon the films are checked "
                         "against, and any number in them is live, like the rest of the "
                         "book's.", "i"))]
    letter = ""
    for term in chosen:
        first = term.name[:1].upper()
        if first != letter:
            letter = first
            blocks.append(Block("h3", [Span(letter)]))
        blocks.append(_para(Span(smarten(term.name), "b"), Span(" — "),
                            *parse_inline(term.define, resolver)))
    if not chosen:
        blocks.append(_para(Span("The glossary fills itself as the chapters are written.")))
    return _chapter("glossary", blocks)


def token_usage(chapters: dict[str, Chapter]) -> dict[str, list[str]]:
    """Token -> the chapters that print it, in reading order, captions included."""
    used: dict[str, list[str]] = {}
    for cid, chapter in chapters.items():
        for span in spans_of(chapter.blocks):
            if span.token:
                used.setdefault(span.token, []).append(cid)
        for plate_id in placed_plates(chapter):
            plate = P.BY_ID.get(plate_id)
            if plate is not None:
                for match in TOKEN.finditer(plate.caption + json.dumps(plate.recipe)):
                    used.setdefault(match.group(1), []).append(cid)
    return used


def numbers_chapter(used: dict[str, list[str]], chapters: dict[str, Chapter],
                    resolver: Resolver) -> Chapter:
    numbers = outline.chapter_numbers()

    def where(cids: list[str]) -> str:
        seen: list[str] = []
        for cid in cids:
            label = str(numbers[cid]) if cid in numbers else chapters[cid].title
            if label not in seen:
                seen.append(label)
        return ", ".join(seen)

    groups: dict[str, list[str]] = {}
    for name in used:
        groups.setdefault(name.split(".")[0], []).append(name)
    blocks = [_para(Span(
        "Every figure this book quotes is a live value. The prose holds a reference to it, "
        "not the number: the value was computed by the project's code when this copy was "
        "built. This is the full list -- each figure's name in the code, the value it had "
        "at build time, what it measures, and the chapters that print it. Change the code "
        "and rebuild, and every page that quotes a figure changes with it. Nothing here "
        "was typed."))]
    order = {group: index for index, group in enumerate(GROUP_ORDER)}
    for group in sorted(groups, key=lambda g: (order.get(g, len(order)), g)):
        blocks.append(Block("h3", [Span(GROUP_TITLES.get(group, group.replace("_", " ")
                                                         .capitalize()))]))
        head = _cells("Figure", "Value", "What it is", "Chapters")
        rows = []
        for name in sorted(groups[group]):
            try:
                describe = resolver.describe(name)
            except Exception:
                describe = ""
            rows.append([[Span(name, "code")], [Span(resolver.value(name))],
                         [Span(smarten(describe))], [Span(where(used[name]))]])
        for start in range(0, len(rows), 24):
            blocks.append(Block("table", items=[head] + rows[start:start + 24]))
    if not groups:
        blocks.append(_para(Span("No chapter quotes a live figure yet.")))
    return _chapter("numbers", blocks)


def plate_order(chapters: dict[str, Chapter]) -> list[str]:
    order = ["frontispiece"] if "frontispiece" in P.BY_ID else []
    for _section, plan, _book in outline.all_chapters():
        chapter = chapters.get(plan.id)
        if chapter is None:
            continue
        for plate_id in placed_plates(chapter):
            if plate_id not in order:
                order.append(plate_id)
    return order


def plates_chapter(chapters: dict[str, Chapter], numbers: dict, folios: dict) -> Chapter:
    blocks = [_para(Span(
        "No illustration in this book is a stock picture or a generic view. Each is a "
        "scene from one of the project's tools, set up to show one idea -- a moment "
        "chosen, a layer hidden, a triangle lifted out, a label added -- and this list "
        "says which tool drew it and what was changed. The three book dividers reuse "
        "renders from the same tools as backgrounds."))]
    head = _cells("Plate", "Title, and what was changed", "Made with", "Page")
    rows = []
    for plate_id in plate_order(chapters):
        plate = P.BY_ID.get(plate_id)
        if plate is None:
            continue
        rows.append([[Span(numbers.get(plate_id, "–"))],
                     [Span(smarten(plate.title), "b"), Span(". "),
                      Span(smarten(plate.change), "i")],
                     [Span(TOOL_NAMES.get(plate.tool, plate.tool))],
                     [Span(folios.get(plate_id, "–"))]])
    for start in range(0, len(rows), 16):
        blocks.append(Block("table", items=[head] + rows[start:start + 16]))
    return _chapter("plates-index", blocks)


# ----------------------------------------------------------------------
# Composition
# ----------------------------------------------------------------------

def front_meta(resolver: Resolver) -> dict:
    extra = front_extra()
    today = date.today()
    year = extra.get("year", str(today.year))
    copyright_blocks = [
        [Span(f"Copyright © {year} {C.AUTHOR}. All rights reserved.")],
        [Span("No part of this book may be reproduced in any form without the author's "
              "permission, except for brief quotations in reviews.")],
        [Span(f"This copy was built on {today:%B} {today.day}, {today.year} from the DomeSim "
              f"repository at commit {git_commit()}. Every number in it was computed by the "
              "project's code at that moment; the appendix The Numbers Behind This Book "
              "lists each one, its value, and what computes it.")],
        [Span("The plates were rendered by the project's own tools: the DomeSim film engine, "
              "Dome Forge, the Dome Home Assembly Line and the Dome Creator.")],
        [Span("This book describes how one person designed and built a dome. It is not "
              "engineering, legal or financial advice. Check your local building code, have "
              "any structure people will live in reviewed by a qualified engineer, and use a "
              "chainsaw only with training and protective equipment.", "i")],
        [Span(f"ISBN {extra.get('isbn', '[ISBN]')}")],
    ]
    return {
        "frontispiece": "frontispiece",
        "books": [(book.number, book.name) for book in outline.BOOKS],
        "author": C.AUTHOR,
        "copyright": copyright_blocks,
        "dedication": parse_inline(extra.get("dedication", "[DEDICATION: a line of your own]"),
                                   resolver),
        "epigraph": parse_inline(extra.get(
            "epigraph", "Every house is an argument about what a person is worth."), resolver),
        "epigraph_source": extra.get("epigraph_source", "The Round House Creed"),
    }


def compose(chapters: dict[str, Chapter], meta: dict, lookups: Lookups) -> Layout:
    numbers = outline.chapter_numbers()
    front = [Entry(chapters[plan.id], None, None, "front") for plan in outline.FRONT]
    parts = []
    for book in outline.BOOKS:
        info = BookInfo(book.number, book.name, book.promise, book.plate,
                        tuple((numbers[plan.id], chapters[plan.id].title)
                              for plan in book.chapters))
        parts.append((info, [Entry(chapters[plan.id], numbers[plan.id], info)
                             for plan in book.chapters]))
    back = [Entry(chapters[plan.id], None, None, "back") for plan in outline.BACK]
    return compose_book(parts, back, front, meta, lookups.plate, lookups.sheet, lookups.table)


# ----------------------------------------------------------------------
# Checks
# ----------------------------------------------------------------------

def printed_text(chapters: dict[str, Chapter], meta: dict) -> str:
    parts = [span.text for chapter in chapters.values() for span in spans_of(chapter.blocks)]
    parts += [chapter.title + " " + chapter.deck for chapter in chapters.values()]
    for key in ("copyright", "dedication", "epigraph"):
        parts += [span.text for span in spans_of(meta.get(key, []))]
    parts.append(str(meta.get("author", "")))
    return " ".join(parts)


def audit(chapters: dict[str, Chapter], layout: Layout, meta: dict, final: bool) -> dict:
    plans = outline.by_id()
    problems = list(layout.problems)
    warnings: list[str] = []
    requests: dict[str, int] = {}
    words: dict[str, list[int]] = {}
    statuses: dict[str, str] = {}
    for cid, chapter in chapters.items():
        _section, plan, _book = plans[cid]
        statuses[cid] = chapter.status
        count = len(chapter.author_requests())
        if count:
            requests[cid] = count
        words[cid] = [chapter.words, plan.target]
        if cid in outline.GENERATED:
            continue
        placed = placed_plates(chapter)
        missing = [pid for pid in plan.plates if pid not in placed]
        extra = [pid for pid in placed if pid not in plan.plates]
        if missing:
            warnings.append(f"{cid}: the plan promises {', '.join(missing)}, "
                            "which the text does not place")
        if extra:
            warnings.append(f"{cid}: the text places {', '.join(extra)}, "
                            "which the plan does not list")
        sheets = placed_sheets(chapter)
        unplaced = [key for key in plan.sheets if key not in sheets]
        if unplaced:
            warnings.append(f"{cid}: the plan's worked math {', '.join(unplaced)} is not placed")
    placeholders = sorted(set(PLACEHOLDER.findall(printed_text(chapters, meta))))
    pages = len(layout.pages)
    gutter_needed = C.min_gutter_in(pages)
    kdp = {
        "pages": pages,
        "even": pages % 2 == 0,
        "in_range": C.KDP_PAGE_RANGE[0] <= pages <= C.KDP_PAGE_RANGE[1],
        "gutter_in": round(C.GRID.inside / C.PT_PER_IN, 3),
        "gutter_needed_in": gutter_needed,
        "outside_in": round(C.GRID.outside / C.PT_PER_IN, 3),
        "outside_needed_in": C.MIN_OUTER_IN_WITH_BLEED,
        "spine_in": round(pages * C.SPINE_IN_PER_PAGE[C.PAPER], 4),
        "spine_text": pages >= C.SPINE_TEXT_MIN_PAGES,
        "trim_in": [C.TRIM.width_in, C.TRIM.height_in],
        "bleed_in": C.TRIM.bleed_in,
    }
    if kdp["gutter_in"] + 1e-9 < gutter_needed:
        problems.append(f"the inside margin is {kdp['gutter_in']} in; KDP needs "
                        f"{gutter_needed} in for {pages} pages")
    if kdp["outside_in"] + 1e-9 < C.MIN_OUTER_IN_WITH_BLEED:
        problems.append("the outside margin is below KDP's minimum with bleed")
    if not kdp["in_range"]:
        problems.append(f"{pages} pages is outside KDP's {C.KDP_PAGE_RANGE} range")
    if not kdp["even"]:
        warnings.append("the page count is odd; KDP will add a blank page at the end")
    blocking = list(problems)
    if requests:
        blocking.append(f"{sum(requests.values())} author requests remain in "
                        f"{len(requests)} chapters")
    if placeholders:
        blocking.append("placeholders remain: " + ", ".join(placeholders))
    unwritten = [cid for cid, status in statuses.items() if status in ("missing", "outline")]
    if unwritten:
        blocking.append(f"{len(unwritten)} chapters are not written yet: "
                        + ", ".join(unwritten))
    return {
        "ok": not (blocking if final else problems),
        "final": final,
        "problems": problems,
        "blocking": blocking,
        "warnings": warnings,
        "requests": requests,
        "placeholders": placeholders,
        "statuses": statuses,
        "words": words,
        "total_words": sum(value[0] for value in words.values()),
        "kdp": kdp,
    }


# ----------------------------------------------------------------------
# Output
# ----------------------------------------------------------------------

def token_info(used: dict[str, list[str]], resolver: Resolver) -> dict:
    info = {}
    for name in sorted(used):
        try:
            describe = resolver.describe(name)
        except Exception:
            describe = ""
        group = name.split(".")[0]
        source = {"dm": "domology.science", "hist": "domology.science (git history)",
                  "dmch": "domology.outline"}.get(group, "two_v_demo.book_tokens")
        info[name] = [resolver.value(name), describe, source, sorted(set(used[name]),
                                                                 key=used[name].index)]
    return info


def relative_href(base: Path):
    def href(src: str) -> str:
        return os.path.relpath(Path(src).resolve(), base.resolve()).replace(os.sep, "/")
    return href


def file_href(src: str) -> str:
    return Path(src).resolve().as_uri()


def chapter_list(chapters: dict[str, Chapter], layout: Layout) -> list[dict]:
    numbers = outline.chapter_numbers()
    first_page = {line.chapter: line.page for line in layout.toc if line.chapter}
    rows = []
    for _section, plan, book in outline.all_chapters():
        chapter = chapters.get(plan.id)
        if chapter is None:
            continue
        rows.append({"id": plan.id, "title": chapter.title, "number": numbers.get(plan.id),
                     "book": book.number if book else None, "status": chapter.status,
                     "words": chapter.words, "target": plan.target,
                     "page": first_page.get(plan.id),
                     "path": str(chapter.path) if chapter.path else None,
                     "requests": len(chapter.author_requests())})
    return rows


def build(final: bool = False, pdf: bool = True, png: bool = False, dpi: float = 150.0,
          publish: bool = False, verbose: bool = True) -> dict:
    started = time.time()

    def say(text: str) -> None:
        if verbose:
            print(text, flush=True)

    reset_tokens()
    resolver = Resolver(extra=outline.chapter_tokens(), strict=final)
    lookups = Lookups(resolver)
    chapters = read_chapters(resolver)
    chapters["glossary"] = glossary_chapter(chapters, resolver)
    used = token_usage(chapters)
    chapters["numbers"] = numbers_chapter(used, chapters, resolver)
    chapters["plates-index"] = plates_chapter(chapters, {}, {})
    ordered = {plan.id: chapters[plan.id] for _s, plan, _b in outline.all_chapters()}
    meta = front_meta(resolver)
    say("composing ...")
    layout = compose(ordered, meta, lookups)
    ordered["plates-index"] = plates_chapter(ordered, layout.numbers or {}, layout.plates)
    layout = compose(ordered, meta, lookups)
    report = audit(ordered, layout, meta, final)
    report["seconds_layout"] = round(time.time() - started, 1)
    say(f"{len(layout.pages)} pages, {report['total_words']:,} words, "
        f"{len(report['problems'])} problems, {len(report['warnings'])} warnings")

    BUILD.mkdir(parents=True, exist_ok=True)
    tokens = token_info(used, resolver)
    data = layout.to_json()
    data.update({"chapters": chapter_list(ordered, layout), "tokens": tokens, "report": report,
                 "built": time.strftime("%Y-%m-%d %H:%M:%S")})
    (BUILD / "layout.json").write_text(json.dumps(data), encoding="utf-8")
    from . import pages as pages_out
    from . import reader
    reader_path = BUILD / "reader.html"
    reader_path.write_text(reader.reader_html(layout, relative_href(BUILD), tokens,
                                              ordered), encoding="utf-8")
    report["reader"] = str(reader_path)
    pdf_path = BUILD / "interior.pdf"
    if pdf:
        say("printing the PDF ...")
        html_path = BUILD / "print.html"
        html_path.write_text(pages_out.print_html(layout.pages, file_href), encoding="utf-8")
        pages_out.print_pdf(html_path, pdf_path)
        facts = pages_out.pdf_facts(pdf_path)
        report["pdf"] = {**facts, "path": str(pdf_path)}
        size = facts.get("size_pt")
        if size and (abs(size[0] - C.TRIM.canvas_w) > 0.5 or abs(size[1] - C.TRIM.canvas_h) > 0.5):
            report["problems"].append(f"the PDF's pages are {size[0]:.2f} x {size[1]:.2f} pt, "
                                      f"not {C.TRIM.canvas_w:.2f} x {C.TRIM.canvas_h:.2f}")
        if facts.get("pages") != len(layout.pages):
            report["problems"].append(f"the PDF has {facts.get('pages')} pages; the layout "
                                      f"has {len(layout.pages)}")
    if png:
        say("drawing page images ...")
        folder = BUILD / "pages"
        folder.mkdir(exist_ok=True)
        for page in layout.pages:
            pages_out.png_page(page, dpi).save(folder / f"page-{page.index + 1:04d}.png")
        report["png"] = str(folder)
    if publish:
        from two_v_demo.deliverables import next_version_path
        C.OUT.mkdir(parents=True, exist_ok=True)
        published = {}
        if pdf:
            target = next_version_path(C.OUT / "domology-interior.pdf")
            shutil.copyfile(pdf_path, target)
            published["interior"] = str(target)
        target = next_version_path(C.OUT / "domology-reader.html")
        target.write_text(reader.reader_html(layout, relative_href(C.OUT), tokens, ordered),
                          encoding="utf-8")
        published["reader"] = str(target)
        report["published"] = published
    report["ok"] = not (report["blocking"] if final else report["problems"])
    report["seconds"] = round(time.time() - started, 1)
    (BUILD / "report.json").write_text(json.dumps(report, indent=2), encoding="utf-8")
    if publish:
        target = next_version_path(C.OUT / "domology-build-report.json")
        target.write_text(json.dumps(report, indent=2), encoding="utf-8")
    return report


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__,
                                     formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--final", action="store_true")
    parser.add_argument("--no-pdf", action="store_true")
    parser.add_argument("--png", action="store_true")
    parser.add_argument("--dpi", type=float, default=150.0)
    parser.add_argument("--publish", action="store_true")
    args = parser.parse_args(argv)
    report = build(final=args.final, pdf=not args.no_pdf, png=args.png, dpi=args.dpi,
                   publish=args.publish)
    for label in ("problems", "blocking" if args.final else "", "warnings"):
        if label and report.get(label):
            print(f"{label.upper()}:")
            for line in report[label][:60]:
                print("  -", line)
    kdp = report["kdp"]
    print(f"{kdp['pages']} pages; spine {kdp['spine_in']} in; gutter {kdp['gutter_in']} in "
          f"(needs {kdp['gutter_needed_in']}); {report['total_words']:,} words; "
          f"{sum(report['requests'].values())} author requests; {report['seconds']} s")
    if report.get("published"):
        for key, value in report["published"].items():
            print(f"published {key}: {value}")
    return 0 if report["ok"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
