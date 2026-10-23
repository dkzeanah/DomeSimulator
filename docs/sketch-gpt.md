# sketch-gpt

The cinematic director extends this studio with first-person/drone scouting,
automated shots, camera-path recording, a multi-track timeline and an original
family-comedy pilot. See [director controls](sketch-gpt-director.md) and
[Nearly Level series](nearly-level-series.md).

Open **sketch-gpt** under **Design & build** in `launcher.py`. The drawing studio
shares the existing world3d document, solver pieces and editing operations. Its
saved project is separate: `world3d/saved/sketch-gpt.json`.

Drag to orbit, select a piece for dimensions, choose a material palette or a
construction view, and switch between orbit, plan and front views. Delete,
copy, translate, cut at a member's midpoint, undo, save/load, and add a square strut by its endpoints. Units
are inches. The three palettes, furniture and selectively glazed triangular
skins are architectural studies, not specified construction assemblies.

The export button creates a new numbered `deliverables/*-sketch-gpt[-vN]`
release containing an illustrated PDF, landscape and portrait PNGs, editable OBJ
models, saved world, member identity map, baseline solver CSVs, per-panel solver
SVGs, thumbnails, platform copy, model status and SHA-256 manifest. The guide
contains the assembly sequence, all twelve real jig stages and every panel's
nominal triangle, physical stock lengths and directed member mates.

The frame, foundation, deck, skins and jig come from `world3d.structures` and
`geodesic_raw_wedge_dome_dihedral`. No alternate dome solver is introduced.
Technical references are fit-to-page, not full-size cutting templates. CSV
cut-plane descriptors use the solver's local face/fence references.

The current studio uses the default solver configuration. It is a focused
drawing/editing front end, not a full general CAD replacement. Moving or cutting
pieces does not recompute the underlying geodesic topology: exported views and
OBJ reflect edits, while fabrication sheets retain the baseline and are flagged
in `model-status.json`. Do not fabricate an edited model from stale schedules.

Doorway reinforcement, egress, structural connections, temporary bracing,
envelope performance, site design, services and approvals require project-specific
design. There were no external reference PDFs attached during initial development.

Developer checks:

```powershell
py -3.12 -m world3d.sketch_gpt --selftest
$env:LAUNCHER_SMOKETEST='1'
py -3.12 launcher.py
Remove-Item Env:LAUNCHER_SMOKETEST
```

Batch export: `py -3.12 -m world3d.sketch_gpt --export`.

For standalone implementations, pair `sketch-gpt-standalone-spec.md` with either
`sketch-gpt-rust-prompt.md` or `sketch-gpt-cpp-prompt.md`. Those prompts describe
the broader production target, including capabilities beyond this first studio.
