"""Public launcher for the standalone ModernGL 2V teaching world.

This executable is intentionally separate from ``dome_creator.py`` and
``assembly_line.py``. Launch and configure it from the consolidated
launcher (``py -3.12 launcher.py``), which exposes every option
(fullscreen, self-test, report, stills, video export + narration,
voice tools, build-packet export, size) as GUI fields. Run directly
with no launcher ticket present and it opens the normal live
presentation, fullscreen.
"""

from two_v_demo.app import main


if __name__ == "__main__":
    raise SystemExit(main())
