"""My Own Home, My Own Dome: the picture book.

The verse is ``books/my-own-home-my-own-dome/verse.md``. Every picture is rendered in
the Cabin World (:mod:`two_v_demo.cabin_world`) -- the solver's own dome, log, saw and
stack -- with the story's extras (a town of boxes, Pip, her friend) added as geometry,
then given one storybook finish so all the pages belong together.

    py -3.12 -m kids_book                 # build the PDF into a new numbered folder
    py -3.12 -m kids_book --pictures 1 9  # render just these pictures, to look at
"""
