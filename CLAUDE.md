# Working agreements for this repository

Claude Code reads this file automatically at the start of every session in this
directory, so anything written here applies without being repeated. Add rules by editing
this file; there is no GUI step and nothing to enable.

## Never overwrite a deliverable

**Rendered output is append-only.** A video, a fabrication package or an export that
already exists on disk is a thing that took hours to make and may already have been sent
somewhere. Re-rendering after a fix produces a **new file with an incremented name**
(`-v2`, `-v3`, …), never a replacement.

`two_v_demo.deliverables.next_version_path` implements this and
`MasterclassApp.export_video` calls it, so the rule holds even when somebody forgets it.
Do not add a "force" flag to defeat it; if an old cut is genuinely worthless, deleting it
is a separate, deliberate act.

The same applies to anything under `deliverables/`. Do not reuse a filename that already
exists; a rebuilt folder (a release) goes beside the first as `-v2`.

## One library, one way to make a film, one place for pictures

* **Everything made goes in `deliverables/`, one numbered folder per output** --
  `deliverables/<NNNN>-<concept>[-vN]/`, numbered in the order it was made, holding every
  file of that iteration: the cut, its phone cut, captions, voice, and `release/`
  (`medialib.py`; `deliverables/INDEX.md` and `index.html` list them all, with dates).
  A re-render is a new numbered folder (`-v2`), never a file added to the old one. Old
  paths like `deliverables/book/x.pdf` are *addresses* that `next_version_path` and
  `medialib.route` send to the right iteration. To read an output, use
  `medialib.latest(slug, ".pdf")` or `medialib.locate(old_path)`, never a glob of a
  folder. `deliverables/_moves/` records where every old file went.
* **Every film is made with `py -3.12 -m film make <lesson>`** (`show` first to see what
  it will do; `--voice mine --pace 1.5` for the owner's voice; `stills`, `teaser`). It
  claims the next numbered folder first and renders into it. Do not write a new staged
  script per film.
* **The 3-D world is `py -3.12 -m world3d`**: the foundation, the dome and the zome, their
  jigs and skins, built by their own solvers; edits are an operation log replayed on top.
  Add new structures there, not in another single-purpose window.
* **zeanahlab.com is `website/`** (Vite + React + TS + Tailwind on Cloudflare Pages, Pages
  Functions, D1, R2; `website/SETUP.md` is the runbook). It ports `web/`'s list, sample gate,
  accounts, shop and network, adds pads with their numbers, backers, founder plaques,
  salvage and each member's own life account (the book *Snowball*'s `snowball.py`, per
  member). Its numbers come only from `npm run facts` (`scripts/export_facts.py`, which reads
  `web/export_facts.py` and `seed_model`). The owner's strategy brief is in
  `website/private/`, which is gitignored and must never be committed.
* **Images and clips live in `assets/`, named for what they show** (`assetlib.py`,
  `assets/catalogue.json`). Never name a file after the tool that made it; the catalogue's
  `origin` field records that (publishers ask). Find one by name:
  `assetlib.image("wedge-method-cover", 4)`.

## Reuse what this repository already builds

This project has accumulated a lot of working machinery, and the failure mode is
re-implementing a worse version of it in a new file rather than importing the real one.
Before drawing, computing or animating anything, check whether it already exists:

* `geodesic_raw_wedge_dome_dihedral.py` — the live raw-wedge solver and 3-D world. Its
  solved geometry reaches the films through `two_v_demo/raw_wedge_bridge.py`, including
  `world_batches()`, which converts the simulator's own meshes into lesson geometry.
  **A film that talks about the wedge dome should show the simulator's dome, not a
  sketch of one.**
* `two_v_demo/segments.py` — reusable stingers and outros (`party`, `franken_plain`,
  `outro`, `whoami`, the CTAs). Splice these in rather than re-authoring them.
* `two_v_demo/lesson_*.py` — every published film's scene painters are importable.
* `two_v_demo/wedge_geometry.py`, `hubless_geometry.py`, `dome_costing.py` — the
  arithmetic. Films must derive from these, never restate their numbers by hand.
* `infill/methodology.py` — the core wedge-building stock ledger: the pentagon's
  complementary centreline lengths, nominal edges versus physical cuts versus
  uncut blanks, paired one-face infill and usable-trunk equivalents. Books and
  concepts use its `wm.*` tokens; films read the same functions. Read
  `docs/wedge-building-methodology.md` before extending this method. Pair span
  is not continuous coverage; opposed points, alternating points and two points
  both inward are different layouts. Keep the area/overlap model labelled as
  an assumption until the installed coverage is measured.

If two films state the same figure, they must be reading it from the same function.

## Numbers on screen are computed, not typed

Every figure a film shows must trace back to code that derives it. Where something
genuinely cannot be derived — a price, a labour rate — declare it in an explicit
constants table with a reason, and put that table on screen before using it. Keep
measured values and estimates in separate tables and say which is which.

When a conclusion is unflattering, show it. Several screens in this repository exist
specifically to state the number that does not help the argument.

## Corrections belong on camera

If a published film says something wrong, the fix is a chapter that names the error and
then corrects it, not a silent re-cut. `lesson_wedge_why.py` does this for the mitre
claim; follow that pattern.

## Before rendering

Run the lesson's selftest and look at a still from each new or changed chapter. A render
is roughly ninety minutes; a wrong camera angle found afterwards costs all of it.

## Every render is a release

One render produces a set, not a file. Any film exported by an LLM — new or re-cut —
must end with all of these, and the standard exporter now does it by default:

* the **landscape cut**, and a **phone cut** beside it (`orientation=both`, which is
  the default for `export_video` tickets; a lesson with `frame_fit="off"` stays
  landscape-only, because it opted out of re-framing);
* a **release folder** in `deliverables/releases/<cut-name>/` holding one thumbnail
  per chapter cut out of the finished video, the captions, and `description.md` with
  YouTube, Facebook and Instagram copy and hashtags.

`two_v_demo.release.build_release` builds the folder from the film's own script and the
exporter's narration plan, so the copy and the chapter timestamps match the cut. The
exporter calls it automatically when a render finishes. A film rendered some other way
— its own script, a staged pipeline — must call it by hand before the work is reported
done:

    py -3.12 -m two_v_demo.release --lesson <key> --video <path-to-cut.mp4>

Hashtags live in `release.HASHTAG_BANK`. A new film gets its own entry there.

The plug-in segments (call to action, outro, frankendome party) are spliced during the
export when a preset sets `compose_segments`; new films turn that on unless the lesson
already carries its own outro.

## The Cabin World is the baseline scene

New films are set in `two_v_demo/cabin_world.py`: the hilltop at sunset, the solver's
dome on its pad, the builder, the log, the stump and chainsaw, the member stack. Aim
cameras at `cabin_world.landmarks()` by name, never at copied coordinates.
`two_v_demo/lesson_cabin_pilot.py` is the worked example of a narrated film in it;
`wedge_book/cold_open.py` of a short one. Music for them is synthesised by
`two_v_demo/score.py`, never sampled.

Every earlier film is queued to be re-made in it (`rerender/`, the launcher's
**Re-render Queue**). Work that queue only through `py -3.12 -m rerender`: claim before
starting, note as you go, stop at `review`. The user alone marks a film `done`, and an
original is never edited to make a re-render.
