"""Public launcher for the compound-cut lesson.

Same renderer as ``two_v_masterclass.py``, different lesson. This one
covers the single hardest operation in a hubless dome in full: both
machines, the jig between them, and every saw setting measured off the
model rather than quoted. Launch and configure it from the consolidated
launcher (``py -3.12 launcher.py``), whose Masterclass tab has a Lesson
field. Run directly with no launcher ticket present and it opens the
cutting lesson, fullscreen.
"""

from two_v_demo.app import main


if __name__ == "__main__":
    raise SystemExit(main(default_lesson="cuts"))
