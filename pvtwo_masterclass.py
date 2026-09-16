"""Public launcher for the The Twenty Dollar Pine, Part Two lesson.

Same renderer as ``two_v_masterclass.py``, different lesson. Launch and
configure it from the consolidated launcher (``py -3.12 launcher.py``),
whose Masterclass tab has a Lesson field. Run directly with no launcher
ticket present and it opens this lesson, fullscreen.
"""

from two_v_demo.app import main


if __name__ == "__main__":
    raise SystemExit(main(default_lesson="pvtwo"))
