# 2 Trees: Build Your (D)Home

*One small chainsaw, 120 wedge struts, and a geodesic dome in a fortnight.*

This folder is the book. Everything below explains how it is put together and
how to work on it, in plain terms — you do not need to read any code to write
this book.

## Read it

From the DomeSim launcher, go to the **Book: 2 Trees** tab.

```bash
py -3.12 launcher.py
```

| I want to… | Action | What you get |
|---|---|---|
| **Just read it** | `read_html` | One web page with the whole book and every picture inside it. Opens in any browser. **Ctrl+P → Save as PDF** there gives the best-looking paper version there is. |
| **A PDF right now** | `read_pdf` | A typeset PDF, built directly. Uses Chrome if this machine has one, else a built-in typesetter; the log says which. |
| **Read while writing** | `studio` → **Read** tab | The book in the window, a chapter at a time, numbers filled in and figures in place. No export step. |
| **Edit somewhere else** | `export` | The Markdown source. |

Nothing is ever overwritten: a second build writes `-v2`.

The Read tab, the HTML and the PDF are all built from one function
(`book_export.book_html`), so what you read on screen and what you send
somebody cannot be different books.

## The reader's copy is clean

The exports (`read_html`, `read_pdf`, `export`) are what a reader gets, and
they never show the writing desk. Chapters and back-matter sections that
have no prose yet are simply **omitted** rather than marked, figures that
have not been rendered (or photographs not yet taken) are simply **absent**
rather than replaced by a placeholder card, and the manuscript's page-plan
comments never reach the file. There is no "(not written yet)" anywhere in
an exported book — the Write tab and the `progress` action are where the
state of the writing lives.

The front matter carries the book's title page, copyright and the
engineer's note: the book documents methods and prototypes, it is not a
substitute for site-specific structural engineering, and anything intended
for permanent occupancy should be reviewed by a qualified engineer and the
local authority. The back matter carries the master tables, the glossary,
the software section and the colophon.

The KDP layout mapping — how the publisher's structure guidance was
adapted onto this book — is `docs/kdp-layout-mapping.md`.

## Write it

Open the **Book: 2 Trees** tab with the `studio` action. Six tabs: Outline,
Write, Read, Numbers, Figures, Build.

## What is where

| | |
|---|---|
| `book/manuscript/` | The writing. One plain Markdown file per chapter. |
| `book/manuscript/front/`, `back/` | Front and back matter, same format. |
| `deliverables/book/figures/` | Every rendered illustration. |
| `deliverables/book/2-trees.md` | Exported books. Versioned, never replaced. |

The manuscript is ordinary text files in a folder. You can open them in any
editor, put them under version control, and email them. Book Studio is a
convenience over those files, never a container for them.

## The rule that shapes everything

**No number is ever typed into this book.**

Where a sentence needs a figure it writes a token:

```markdown
Two trees give {{dome.struts_available}} struts for a frame that needs
{{frame.members}}.
```

At export time each token is filled in from the same code that solves the
geometry and draws the 3-D models. Change the tree, the split count or the
dome, and every sentence that quotes it updates itself.

Chapter cross-references work the same way. Prose writes `{{ch.method_a}}`,
not "Chapter 21", because inserting one chapter otherwise leaves every later
pointer silently aimed at the wrong place. `sync_filenames()` renames the
manuscript files when numbers move, and `BOOK.by_ref()` is how code should
name a chapter.

This is not fussiness. A number typed into a paragraph is correct on the day
it is typed and silently wrong from the first time anything changes, and
there is no way to find those afterwards — nothing fails, the book just
becomes untrue in places nobody remembers.

The **Numbers** tab in Book Studio lists all 920 tokens with their current
values and a button to drop one into the text. A misspelt token stops the
export rather than printing a blank.

## The three strands

Each chapter declares which of three books it belongs to, and the contents
page promises a reader can follow one track:

* **story** (7 chapters) — what happened, in order, to somebody with a saw.
* **howto** (18) — do this, then this. A complete set of instructions alone.
* **explain** (37) — why any of it works. Skippable.
* **reference** (9) — tables you come back to at the bench.

## The two calculations

The calculations sit in Part 1 as a section, and they teach sizing in both
directions:

* **Method A, design first** (Ch. 21) — pick a floor area, get a cut list and
  a felling list.
* **Method B, tree first** (Ch. 22) — measure a trunk, buck it, and find out
  what dome it makes. This is the one the title refers to.
* **The round trip** (Ch. 23) — proof they are one calculation held at
  opposite ends. It prints the residual rather than asserting it.

## The three parts

The book is assembled as three parts:

* **Part 1 — How to Build One** (Ch. 1–52): the story, the method, the
  fortnight and the bench, absorbed unchanged from the original 52-chapter
  book, its old parts kept as sections.
* **Part 2 — Why It Scales** (Ch. 53–68): the flat parts list, the nine
  processes, the hour at the log, the fuel ledger, the envelope, the pad and
  its economics, the iris, the network, and the closing audit of what would
  have to be true.
* **Part 3 — Variations and Future Systems** (Ch. 69–71): the manufactured
  version of the method — the shower-cap soft shell and its $50 blanket
  quilts, the mast and the floor, and the floating dome. The figures are
  rendered from the solved model (`hat-stack`, `mast-floor`,
  `floating-dome`), and the numbers read live from `soft_shell.py` and
  `seed_model.py`, the same modules the stem-cell campaign quotes.

Parts 2 and 3 are drafted; Part 1's prose is still mostly scaffolds. A
fourth part, *Who This Is For* (the biography), is parked by request and
drops in at the front when it is written; nothing depends on it.

## Where the numbers come from

| module | what it holds |
|---|---|
| `two_v_demo/book_math.py` | Both methods, the tree model, the declared constants, the audit. |
| `two_v_demo/book_tokens.py` | The 920 live figures and cross-references the manuscript may quote. |
| `two_v_demo/book.py` | The outline: parts, chapters, pages, figure placement. |
| `two_v_demo/book_figures.py` | The renderers, and the append-only save rule. |
| `two_v_demo/book_plots.py` | Every table and chart. |
| `two_v_demo/book_diagrams.py` | Every explanatory line drawing. |
| `two_v_demo/book_manuscript.py` | Files, scaffolding, progress, export. |
| `two_v_demo/book_app.py` | Book Studio, including the reader. |
| `two_v_demo/book_export.py` | The readable forms: HTML, PDF, and the shared HTML the reader uses. |

Nothing in these restates a figure another module already derives. The tree
and pinwheel arithmetic comes from `wedge_geometry`; the solved dome, its
seams and its jig come straight from `geodesic_raw_wedge_dome_dihedral.py`
through `raw_wedge_bridge`. The 3-D figures are the simulator's own meshes,
not sketches of them.

## Illustrations

80 figures, drawn by nine renderers:

* **raw_wedge_world** — the solved dome, in a named view. Real geometry.
* **raw_wedge_jig** — the fabrication jig at one of its twelve stages.
* **panel_jig_svg** — flat, full-size panel drawings. Stays vector, because
  you print these and lay a stick on them.
* **book_plot** — tables and charts from `book_math`.
* **book_diagram** — explanatory drawings, from the same geometry.
* **lesson_still** — a real frame of one of the films. Needs PyOpenGL to
  render a new frame; without it, the renderer takes the already-rendered
  frame of the same lesson and second out of the stills archive
  (`two_v_demo_output/`), and only if neither exists does it tell you which
  launcher action produces the frame.
* **photo_slot** — a placeholder card describing the photograph still to be
  taken, laid out at the right size so a proof reads end to end.

The book's plates of the dome itself are film stills, not re-drawings: the
frontispiece, the worked build's plate and the raising plate are frames of
the decluttered wedge film (the frontispiece is the film's orientation
chapter at 425 s; the raising plate is the assemble chapter at 842.5 s; the
worked build's plate is the closing shot at 973 s). They are 1920×1080 film
frames copied into the figure slot, so the book and the film cannot
disagree about what the dome looks like.

The remaining dome renders default to a `timber` palette. The simulator
paints a wedge's two sawn faces red and green because that is how you read a
stick's orientation while flying around it; on paper that reads as a painted
climbing frame, so print figures re-map those to shades of sawn pine. The
geometry is untouched — only the colour. Chapter 13's plate keeps the loud
version, because there the colour *is* the lesson.

**Nothing is ever overwritten.** Re-rendering a figure that exists writes
`-v2`; so does exporting a book. Same rule as every other deliverable here.

## Corrections are chapters

Following the repository's practice, a published claim that turns out wrong
gets a chapter that names it, not a silent edit:

* **Ch. 12** — the 88% recovery figure was computed for a 15-inch butt; this
  book's smaller tree gives a lower one. Both are printed, with the reason.
  (This file is documentation, not manuscript, so it does not carry live
  tokens — the chapter itself does.)
* **Ch. 14** — "no mitres anywhere" was wrong. The butt cut is a compound
  angle. It is still made once, on one end, off the jig.
* **Ch. 42** — the $50/hour estimate. Computed from the actual section it is
  $20.43 against nominal 2x4s, $31.14 against dressed ones.
* **Ch. 48** — all of the above in one place, plus how to report the next one.

Chapter 7, *Not a Worse Two-by-Four*, is the same discipline applied to the
central claim: a wedge from an 8-inch log holds 20% more wood than a dressed
2x4, is within 1% of it in bending stiffness, and is **33% weaker** in bending
strength. All three are printed, in a table, near the front. The argument is
that a triangulated frame loads its members along their length, where area is
what counts — not that the wedge wins every column.

## Check it before you send it

```bash
py -3.12 -c "from two_v_demo.book import validate_everything; validate_everything()"
```

Or the **selftest** action on the launcher's Book tab. It runs the
arithmetic, the outline, every token, every figure and the manuscript
machinery, and says what passed.
