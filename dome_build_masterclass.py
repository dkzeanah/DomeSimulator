"""Public launcher for the start-to-finish 2V dome construction lesson.

Same renderer as ``two_v_masterclass.py``, different lesson: thirty-two
chapters covering sizing, hubs, cutting, setting out, raising, checking
and skinning. Launch and configure it from the consolidated launcher
(``py -3.12 launcher.py``), whose 2V Masterclass tab has a Lesson field.
"""

from two_v_demo.app import main


if __name__ == "__main__":
    raise SystemExit(main(default_lesson="build"))
