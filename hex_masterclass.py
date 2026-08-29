"""Public launcher for the standalone hexagonal-dome teaching world.

Same renderer as ``two_v_masterclass.py``, different lesson. Launch and
configure it from the consolidated launcher (``py -3.12 launcher.py``),
whose 2V Masterclass tab has a Lesson field. Run directly with no
launcher ticket present and it opens the hex lesson, fullscreen.
"""

from two_v_demo.app import main


if __name__ == "__main__":
    raise SystemExit(main(default_lesson="hex"))
