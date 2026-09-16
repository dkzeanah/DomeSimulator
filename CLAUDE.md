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
exists.

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
