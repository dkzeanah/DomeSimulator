"""Public launcher for the assembly-line energy lesson.

Same renderer as ``two_v_masterclass.py``, different lesson. This one
follows a two-person crew through every motion needed to build one dome
and puts a number on what each motion costs them. Launch and configure it
from the consolidated launcher (``py -3.12 launcher.py``), whose
Masterclass tab has a Lesson field. Run directly with no launcher ticket
present and it opens the assembly-line lesson, fullscreen.
"""

from two_v_demo.app import main


if __name__ == "__main__":
    raise SystemExit(main(default_lesson="line"))
