# What This Book Declares

Every number in this book is computed from the geometry of a split log, except
these. They are declared, each with its kind and its reason, so you can change
any of them and rebuild.

    {{sq.t_declared}}

The project's measured and modelled figures -- the splitting rate, the fuel,
the zome, the dome's members -- come from the same software as the other books
in the project, and are the same numbers they print.

## How this copy was made

This copy was built in one step by the project's own software: the geometry in
`square_book/geometry.py`, the drawings in `square_book/figures.py`, drawn to
scale from the same numbers as the tables, and the chapters in
`books/square-on-demand/manuscript/`. To build another from the current manuscript:

    py -3.12 -m square_book.build

It never overwrites an earlier copy: each build is a new, numbered file.
