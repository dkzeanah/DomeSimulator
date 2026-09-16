"""Public launcher for the dome scene composer.

Cycle a piece of furniture, turn it, drop it into a geodesic room, and
the dome refuses whatever does not fit under the shell where you put
it.  Launch and configure it from the consolidated launcher
(``py -3.12 launcher.py``), which exposes the room, the starting
layout, the window size and the headless still renderer as GUI fields.
Run directly with no launcher ticket present and it opens the store,
furnished, ready to edit.
"""

from two_v_demo.composer_app import main


if __name__ == "__main__":
    raise SystemExit(main())
