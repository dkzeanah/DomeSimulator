"""The whole project on one written page: what DomeSim and The 40 Hour Cabin are, so far.

    py -3.12 -m master_book.summary        # a new numbered .md and one-page .pdf in deliverables/pitch/

Prose, not a pitch: what the method is, what the software does, what has been
written and filmed, what is proved and what is not. Every figure is counted
or computed when it is built -- the code is counted on disk, the films from the
deliverables registry, the books from their outlines, the dome and the zome from
their solvers -- so the page is true on the day it is printed.
"""

from __future__ import annotations

import tempfile
from datetime import date
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "deliverables" / "pitch"
STEM = "domesim-project-summary"
BODY_PT = 9.6
SKIP = ("venv", "F5-TTS", "node_modules", ".claude", "worktrees", "__pycache__", "site-packages",
        "exports", "two_v_demo_output")


def counts() -> dict:
    from two_v_demo import book as volume_b
    from two_v_demo.deliverables import DELIVERABLES
    from two_v_demo.lesson_registry import LESSONS
    from wedge_book import outline as volume_a
    from wedge_zome import fabrication as zf

    from . import outline, pitch, tokens

    files = [p for p in ROOT.rglob("*.py") if not any(any(s in part for s in SKIP) for part in p.parts)]
    lines = sum(len(p.read_text(encoding="utf-8", errors="ignore").splitlines()) for p in files)
    t = tokens.tokens()

    from square_book import tokens as sq

    def tok(name):
        return sq.resolve("{{" + name + "}}")

    z = zf.facts("wedge")
    a = pitch.ask()
    import pymupdf

    from . import check
    master = check.latest()                      # the newest numbered copy, not the last by name
    master_pages = len(pymupdf.open(master)) if master else 0
    import medialib
    square = [p for p in [medialib.latest("square-on-demand", ".pdf")] if p]
    square_pages = len(pymupdf.open(square[-1])) if square else 0
    return {
        "date": date.today().strftime("%d %B %Y").lstrip("0"),
        "py_files": len(files), "py_lines": lines,
        "lessons": len(LESSONS), "films_registered": len(DELIVERABLES), "films": t["mb.films"].value(),
        "mp4": len(list((ROOT / "deliverables").rglob("*.mp4"))),
        "pdfs": len(list((ROOT / "deliverables").rglob("*.pdf"))),
        "vol_a": len(volume_a.BOOK.chapters), "vol_a_parts": len(volume_a.BOOK.parts),
        "vol_b": len(volume_b.BOOK.chapters), "cells": len(outline.CELLS), "rungs": len(outline.RUNGS),
        "threads": len(outline.THREADS), "master_pages": master_pages, "square_pages": square_pages,
        "dia": tok("dome.diameter_ft"), "floor": tok("dome.floor_sqft"), "members": tok("dome.members"),
        "panels": tok("dome.panels"), "clock": tok("clock.total"), "split_pct": tok("sq.split_pct"),
        "sawn_pct": tok("sq.sawn_pct"), "squares_pct": tok("sq.squares_pct"), "square_in": tok("sq.square"),
        "price": tok("money.price"), "per_sqft": tok("money.per_sqft"), "site": tok("why.site_usd_per_sqft"),
        "seeds": tok("seed.count"), "core": tok("core.cost"), "labour": tok("money.labour_hours"),
        "split_session": tok("hr.split_session"), "session": tok("hr.session"),
        "strut_lo": tok("web.strut_lo"), "strut_hi": tok("web.strut_hi"),
        "zome_panels": z["panels"], "zome_sections": z["stock"]["sections"], "zome_bevel": z["half"],
        "dome_sections": tok("parts.sections"), "ask": f"{a['total']:,.0f}",
        "vets": f"{pitch.VETERANS['pit'][0]:,}", "when": pitch.VETERANS_COUNTED,
    }


TEXT = """# DomeSim and The 40 Hour Cabin: the project so far

*Written {date}. Every figure on this page is counted or computed by the project's own code that day.*

**What it is.** One person's open-source project to make a small, owned home cheap enough that the
house stops eating the household. It has two halves that keep each other honest: a *method* for
framing round buildings from logs split lengthwise with one chainsaw, and the *software* that
solves, prices, films and writes about that method, so that no number anywhere is typed by hand.
It is built by {author}, a U.S. Navy veteran, in the open at github.com/dkzeanah/DomeSimulator.

**The method.** A two-frequency geodesic dome, {dia} ft across with {floor} sq ft of floor, framed
from {members} wedges split from logs and assembled as {panels} flat panels on one jig, joined in
pinwheels so nothing meets at a corner; {clock} hours to frame by the project's clock, about
{labour} for the whole building. Splitting keeps {split_pct}% of a log against {sawn_pct}% sawn
into two-by-fours. The product built on it is the *stem cell*: one standard body with a utility
core (${core}), snap-in panels, seams that double as channels for rain, wire and air, and a
silicone-soaked cotton skin, listing at ${price} (${per_sqft} a sq ft against ${site} for a new
site-built house), in {seeds} fit-outs. It stands on a serviced pad: own the building, rent the
ground. The same wedges now frame a zome too: {zome_panels} panels, every cut one {zome_bevel:.1f}° bevel,
{zome_sections} log sections against the dome's {dome_sections}.

**The software.** {py_files} Python files, about {py_lines:,} lines. At its centre is the raw-wedge
solver and its 3-D world, which cuts and joins every member; around it, the Dome Creator, the
Triangle Infill calculator, the new Wedge Zome world (with rulers, a six-foot person and a
click-to-measure readout), cost models for the stem cell, the campaign and a park of pads, the
seam-climate controller, the cell wall, the sky-web build, a CNC shop, a book engine whose
manuscripts carry live number tokens, a film pipeline that renders narrated lessons in a shared
3-D "Cabin World" in the owner's own synthesised voice and resumes after a crash, a website
(zeanahlab.com) that sells the book and runs a dome network, and a recorder that logs how the work
gets done.

**What has been written.** *The 40 Hour Cabin: Complete Edition* ({vol_a} chapters in {vol_a_parts}
parts, sold on the site with the code); *The 40 Hour Cabin: 2V Geodesic Dome Wedge Method*, the Amazon
paperback ({vol_b} chapters); the *Master Edition*, a {master_pages}-page reader's proof that tells
the whole idea in {rungs} rungs from a bedtime story to published experiments, across {threads}
threads, with both books bound in; *'Square' on Demand* ({square_pages} pages), on two wedges
paired into a {square_in} in square only where a square is needed; a title page for *Zome Zoomer*;
and *Domology*, a three-in-one book in progress.

**What has been filmed.** {films_registered} films registered and {films} rendered; {mp4} video
files in deliverables, counting phone cuts and teasers, and {pdfs} PDFs. The newest, *Beyond the
Dome*, takes the method past the dome: square on demand, shims, roof pitches, octagons, joints and
the zome.

**The ask, and who it is for.** A grant one-pager and a sheet of efficiency charts ask for
${ask}, the sum of costed lines: prove it, then make it repeatable. It is built by a veteran for
veterans -- {vets} were homeless on one night in {when} (HUD) -- to sit beside the programs that
already house them.

**What is proved, and what is not.** Measured: the splitting rate ({split_session} wedges per
{session}-hour session), strut weights ({strut_lo}-{strut_hi} kg) and a full-size prototype frame.
Modelled: cost, energy, rain, recovery. Not yet: an engineer's rating, an instrumented year of
weather, the moulded shell and its tooling. And the numbers that argue back stay on the page --
paired squares keep only {squares_pct}% of a log, less than the mill.
"""


CSS = f"""
@page {{ size: 8.5in 11in; margin: .45in .5in .45in; }}
html, body {{ background: #fff; margin: 0; }}
body {{ font: {BODY_PT}pt/1.42 Georgia, "Times New Roman", serif; color: #1d1d1b; }}
h1 {{ font: 800 19pt/1.1 "Segoe UI", sans-serif; margin: 0 0 .04in; color: #1d1d1b; }}
h1 + p em {{ color: #666; font-size: 7.6pt; }}
main {{ columns: 2; column-gap: .3in; }}
h1, h1 + p {{ column-span: all; }}
p {{ margin: 0 0 .09in; text-align: left; }}
strong {{ font-family: "Segoe UI", sans-serif; color: #b0601e; }}
"""


def build() -> tuple[Path, Path]:
    import pymupdf

    from two_v_demo import book_export
    from two_v_demo.deliverables import next_version_path
    from wedge_book import print_edition as pe

    from . import outline

    c = counts()
    md = TEXT.format(author=outline.AUTHOR, **c)
    html = book_export._markdown_to_html(md)
    page = (f'<!doctype html><html><head><meta charset="utf-8"><title>DomeSim: the project so far</title>'
            f"<style>{CSS}</style></head><body><main>{html}</main></body></html>")
    with tempfile.TemporaryDirectory() as scratch:
        proof = Path(scratch) / "summary.pdf"
        book_export._pdf_via_chrome(page, proof, book_export._chrome_path())
        doc = pymupdf.open(proof)
        try:
            if len(doc) != 1:
                raise RuntimeError(f"the summary runs to {len(doc)} pages; it must be one")
            shrunk = pe.scale_problem(doc, BODY_PT)
            if shrunk:
                raise RuntimeError(shrunk)
            OUT.mkdir(parents=True, exist_ok=True)
            pdf = next_version_path(OUT / f"{STEM}.pdf")
            mdp = pdf.with_suffix(".md")
            if mdp.exists():
                raise FileExistsError(mdp.name)
            doc.set_metadata({"title": "DomeSim and The 40 Hour Cabin: the project so far", "author": outline.AUTHOR})
            doc.save(pdf, garbage=3, deflate=True)
            mdp.write_text(md, encoding="utf-8")
        finally:
            doc.close()
    return mdp, pdf


if __name__ == "__main__":
    for p in build():
        print(f"wrote {p}")
