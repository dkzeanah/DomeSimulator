"""*The 40 Hour Cabin: Master Edition* -- every rung of the idea, both books inside.

A reader's proof that puts the whole project in one place: six rungs of the
same twelve ideas, from a story read aloud to the frontier, woven into the
two books this project is writing (the Complete Edition and the
Amazon paperback), which are bound in whole as Volumes A and B.

    py -3.12 -m master_book.build            # the master edition PDF (never overwrites)
    py -3.12 -m master_book.build --draft X  # a proof to look at, outside deliverables/
    py -3.12 -m master_book.check --pdf      # every guard, and the newest built copy
    py -3.12 -m master_book.pitch            # the one-page grant summary
    py -3.12 -m master_book.pitch --proof X  # the same, printed for looking at

The manuscript is ``books/master-edition/manuscript/``: the letter and the guide in
``front/``, six rungs of twelve chapters in ``rung1/`` to ``rung6/``, and the
comparison, the checker's page and the colophon in ``back/``. The grid -- which
chapter sits where, and which chapters of the two volumes each card routes to
-- is :mod:`master_book.outline`.
"""
