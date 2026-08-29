"""Public launcher for the Frankendome montage.

Same renderer as ``two_v_masterclass.py``, but this one is not a lesson:
it runs full-frame with a single line of type over it, at a quicker
speech rate, and it argues for the project rather than teaching the
geometry. Launch and configure it from the consolidated launcher
(``py -3.12 launcher.py``), whose Masterclass tab has a Lesson field. Run
directly with no launcher ticket present and it opens the montage,
fullscreen.
"""

from two_v_demo.app import main


if __name__ == "__main__":
    raise SystemExit(main(default_lesson="hype"))
