# Instructions for coding agents in this repository

Every agent working here — Codex, Claude, or anything else — follows the working
agreements in **[CLAUDE.md](CLAUDE.md)**. They are not Claude-specific; that file is
simply the one Claude Code loads automatically. Read it before changing anything.

The short version, for the rules agents break most:

* **Never overwrite a rendered deliverable.** Re-renders get a new versioned name
  (`two_v_demo.deliverables.next_version_path`).
* **Reuse the repository's machinery.** Dome geometry, costing and the Dome Creator's
  meshes already exist; import them, do not redraw them.
* **Numbers on screen are computed**, or declared in a constants table that is shown
  on screen before it is used.
* **Run the lesson's selftest and look at stills before a full render.**
* **Every render is a release**: landscape cut, phone cut, and a release folder with
  thumbnails and platform copy. See "Every render is a release" in CLAUDE.md.
* **Registering a film means three files**: `two_v_demo/lesson_registry.py`,
  `two_v_demo/deliverables.py` and `render_presets.py`. The validators refuse a
  deliverable with no preset, and the launcher's smoketest runs them:

      LAUNCHER_SMOKETEST=1 py -3.12 launcher.py

  (An environment variable, not a flag. `launcher.py --smoketest` just opens the
  launcher.)
