---
section: back
title: The Software in This Book
status: draft
target: 2000
updated: 2026-09-17
---
# The Software in This Book

## What generated these numbers

Every figure in this book comes from one of the programs below, and each
program is included with the book. They are named here so a reader can
find the exact line behind any number printed in these pages.

**`geodesic_raw_wedge_dome_dihedral.py`** -- the live solver and 3-D world.
This is the heart of the project: it solves the raw-wedge dome, its seams,
its dihedral angles and its jig, and it is where the standing dome's own
mesh lives. The book's figures of the frame are this program's mesh, not a
sketch of it.

**`two_v_demo/book_math.py`** -- the book's arithmetic. The two sizing
methods, the tree model, the fortnight, the round trip and the declared
constants. Where a chapter works a number through by hand, this module is
the hand.

**`two_v_demo/wedge_geometry.py`** -- the tree and pinwheel arithmetic the
book and the films share: member classes, splits, yield, recovery.

**`two_v_demo/book_tokens.py`** -- the {{book.chapters}}-chapter book's
living figures. Every figure a sentence quotes -- a token in double braces
-- resolves here, from the modules above, at export time.

**`two_v_demo/book.py`** -- the outline: the parts, the chapters, the pages
and where each figure sits.

**`two_v_demo/book_plots.py` and `book_diagrams.py`** -- the charts and
tables, and the line drawings. Both draw from the same geometry, never from
a number typed beside the drawing.

**`two_v_demo/book_figures.py`** -- the renderers, and the rule that a
re-rendered figure gets a new name rather than replacing the old one.

**`two_v_demo/book_manuscript.py` and `book_export.py`** -- the manuscript
itself, and the readable forms: this HTML, the PDF and the Markdown source.

**`two_v_demo/book_app.py`** -- Book Studio, the desk the book is written
at, including the reader built into it.

Nothing in this list restates a figure another module already derives, and
nothing draws a dome that the solver has not solved. That is what "the
numbers are computed, not typed" means in practice: every one of them
traces to a function in one of these files.

## Reproducing every figure in this book

The whole book rebuilds from these commands, run from the project's folder
with Python 3.12:

```text
py -3.12 -c "from two_v_demo.book import validate_everything; validate_everything()"
```

checks the arithmetic, the outline, every token, every figure and the
manuscript machinery, and reports what passed. It is the gate the book
must pass before it is exported.

```text
py -3.12 launcher.py
```

opens the project's launcher. Its **Book: 2 Trees** tab carries the
actions: `read_html` and `read_pdf` build the book you are reading;
`export` writes the Markdown source; `audit` prints every number the book
states and the calculation behind it; `progress` shows what is written;
`render_figures` redraws every illustration. Each build writes a new,
versioned file -- nothing in this project is ever overwritten by a
rebuild, so the copy you have and the copy a build makes cannot be the
same file by accident.

The 3-D figures are rendered by the solver's own renderers; the two
film-still figures come from the project's films through the launcher's
Masterclass tab. The photographs that remain are the author's to take;
until then the book simply leaves their pages out.

## The launcher

Every tool in this project opens from one window, `launcher.py`:

```text
py -3.12 launcher.py
```

Its tabs are the project's own: the simulator, the lessons and their
films, the dome park, the presenter, and the book this page belongs to.
The book tab is the one to use for anything in this book: read it, build
it, check it, or sit down and change it -- the same files this book was
written in are the files you would write in, plain Markdown in
`book/manuscript/`, one file per chapter.

The launcher also runs the films' smoketests, and the book's, which is the
last line of this section and the one worth repeating: a copy of this book
exists only if every check passed.
