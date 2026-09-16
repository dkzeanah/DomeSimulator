"""Public launcher for Book Studio.

The desk where *2 Trees: Build Your (D)Home* gets written: the outline, the
editor, the live numbers, the figures and the export, in one window.

Launch and configure it from the consolidated launcher (``py -3.12
launcher.py``), whose Book tab exposes the manuscript folder and which
chapter to open. Run directly with no launcher ticket present and it opens at
chapter one with the project's own ``book/manuscript/`` folder.
"""

from two_v_demo.book_app import main


if __name__ == "__main__":
    raise SystemExit(main())
