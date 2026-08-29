"""Public launcher for the franken-dome build lesson.

Same renderer as ``two_v_masterclass.py``, different lesson: the
mixed-stock dome, its folded sheet-metal brackets, and the slack it
settles out. Launch and configure it from the consolidated launcher
(``py -3.12 launcher.py``), whose Masterclass tab has a Lesson field. Run
directly with no launcher ticket present and it opens the franken-dome
lesson, fullscreen.
"""

from two_v_demo.app import main


if __name__ == "__main__":
    raise SystemExit(main(default_lesson="franken"))
