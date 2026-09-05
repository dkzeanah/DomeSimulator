"""Public launcher for Beat Studio.

Sequence rendered beats into a cut without re-rendering anything. The library populates
itself from ``beats/`` when the window opens, so there is no import step: render beats
from the Masterclass tab, then open this and arrange them.

Launch and configure it from the consolidated launcher (``py -3.12 launcher.py``), which
exposes the lesson and the beat folder as GUI fields. Run directly with no launcher
ticket present and it opens the wedge film's beat library.
"""

from two_v_demo.beat_studio_app import main


if __name__ == "__main__":
    raise SystemExit(main())
