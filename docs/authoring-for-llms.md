# Writing a lesson for this engine — instructions for a model

You are being asked to produce Python source that this repository renders
into a narrated teaching video. This document is the contract. Follow it
and your output drops in and runs; deviate and it will be rejected by a
selftest before a frame is drawn.

Read `docs/reference/*.reference.py` for real, working examples. Those
are read-only snapshots of the live files — imitate them, do not import
them.

---

## 0. The one rule that matters most

**Every number that appears on screen must be computed by code that also
proves it.** Never type a figure into a caption. If a value cannot be
derived, it is an *external constant*: give it a name, a unit, a source,
and print it in the report so a viewer can see which figures are derived
and which are borrowed.

This is not style. A lesson that asserts numbers is worthless, because
nobody can check it. A lesson that computes them can be re-derived by
anyone, forever.

---

## 1. What you deliver

Exactly two files, plus two small edits.

```
two_v_demo/<key>_facts.py     the maths, and the proofs
two_v_demo/lesson_<key>.py    the pictures and the words
```

Then the caller adds your lesson to `two_v_demo/lesson_registry.py` and
`two_v_demo/deliverables.py`.

`<key>` is short, lower case, letters and digits and underscores only.

You can skip the boilerplate entirely:

```bash
py -3.12 scaffold_lesson.py <key> "Display Title"
```

That writes both files already working, already self-proving. Then
replace the placeholder facts with real ones.

---

## 2. The facts module

```python
"""One line saying what this computes.

State plainly which numbers are derived and which are borrowed.
"""

from __future__ import annotations

import math
from dataclasses import dataclass
from functools import lru_cache


# Anything taken on authority. Keep this list short and honest.
EXTERNAL_CONSTANTS: tuple[tuple[str, float, str, str], ...] = (
    ("name", 0.0, "units", "Where it comes from, and why it is needed."),
)


@dataclass(frozen=True)
class Thing:
    """One measured item."""
    name: str
    size: float


@lru_cache(maxsize=1)
def things() -> tuple[Thing, ...]:
    """Compute them. This is the real work."""
    ...


def <key>_report() -> str:
    """A portable, plain-text audit of every claim the lesson makes."""
    ...


def validate_<key>() -> None:
    """Prove the model. Assertions, not prints.

    Assert the properties that would make the lesson WRONG if broken,
    not the ones that are trivially true. Good: 'the twelve pentagons
    are always exactly twelve', 'raising costs more than lowering',
    'the counts do not change with size'. Bad: 'the list is not empty'.
    """
    ...
```

**Determinism is mandatory.** Seed every random generator. If you call
something in the wider repository that uses `random`, pass it an
explicitly seeded `random.Random(n)` — `al_build.random_spec` looks like
it seeds from its `serial` argument and does not, which silently made a
figure change between runs until it was caught.

---

## 3. The lesson module

### 3a. A scene painter

```python
def scene_<key>_thing(app, opaque, transparent, p: float) -> None:
    """One sentence on what this picture shows."""
```

* `p` runs 0 to 1 across the chapter. **Every frame must be a pure
  function of `p`.** Never accumulate state between frames.
* `opaque` and `transparent` are `TriangleBatch`es. Draw solid things
  into the first, anything with alpha into the second.
* Put text in the world with
  `app.world_labels.append(WorldLabel(point_3d, "TEXT", (r, g, b)))`.

Available on a batch — see `render_kit.reference.py`:

| Call | Makes |
|---|---|
| `cylinder(a, b, r, colour, segments)` | a rod; `segments=3` wedge, `4` square, `14+` round |
| `box(centre, size, colour)` | an axis-aligned block |
| `sphere(centre, r, colour, rings, sides)` | a ball |
| `triangle(a, b, c, colour, normal)` | one face |
| `cone(base, tip, r, colour, segments)` | a taper |
| `arrow(from, to, r, colour)` | rod plus cone |
| `disc(centre, r, colour, segments)` | a flat circle — **colour before segments** |

Higher-level helpers you should reuse rather than reinvent:

| Module | Gives you |
|---|---|
| `figure` | an articulated person: `POSES`, `walk_pose`, `joint_positions`, `place_figure`, `draw_figure`, `draw_load` |
| `timber` | wood that looks like wood: `draw_timber`, `draw_glue`, `draw_patch`, `draw_cardboard`, `draw_led_run` |
| `render_kit` | colours, `clamp`, `smoothstep`, `ease_in_out` |

### 3b. A chapter

```python
Chapter(
    "slug",            # unique within the lesson
    "01",              # number; renumbered on composition, so any value
    "Chapter Title",   # the kicker
    "One line promise, shown large.",
    (                  # narration: what is SPOKEN. prose, not numbers.
        "Write it the way a person talks. Keep figures on the card,",
        "not in the mouth.",
    ),
    ("fixed = 1.0",),  # equations: fixed lines on the card
    12.0,              # duration FLOOR in seconds; speech stretches it
    (34.0, 24.0, 16.0),# camera: yaw°, pitch°, distance
    "scene_stage_key", # which painter draws it
    None,              # optional overlay override: "hype", "teaching"
                       # or "math"
)
```

A chapter with `overlay="math"` is a **math screen**: the picture stays
live on the left and the chapter's `equations` are revealed one per
beat on a worksheet panel, in their authored order. Write them as a
derivation — inputs, then operations, then results — and make the
**last line the conclusion**: it is rendered in its own band, large, at
80% progress. A math screen ignores the live-equation merge, so the
tuple must be complete on its own; generate it from a facts function
(see `master_facts.py`) so every line is computed, and give the chapter
a duration floor of 20 seconds or more so the reveal can breathe.

### 3c. The lesson

```python
<KEY>_LESSON = Lesson(
    key="<key>",
    brand="ON-SCREEN BRAND LINE",
    title="Display Title",
    chapters=CHAPTERS,
    scenes=SCENES,                 # {stage_name: painter}
    equations=<key>_equations,     # optional live figures
    selftest=validate_<key>,
    report=<key>_report,
    snapshot_prefix="<key>",
    style="teaching",              # or "hype" for a full-frame montage
    label_layout="declutter",      # new work; "raw" reproduces old renders
    voice_rate=None,               # e.g. "+7%" for a montage
)
```

---

## 4. Camera, and the traps that cost the most time

`camera` is `(yaw°, pitch°, distance)`, looking at `(0, 0, 2.25)`.

* **At yaw 90 the camera sits on +Y.** So **+X renders to screen LEFT**,
  and two objects separated along **Y are separated in DEPTH**, not
  across the frame. Lay rows out along **X**. A two-person crew laid out
  along Y appeared as one person; a saw fence at +Y hid the blade it was
  meant to frame.
* **Scale distance to the subject**, roughly 2× its size. A dome of
  radius 5 wants ~15; a saw 18 units across wants ~25–38.
* **Keep the left third clear** in `teaching` style — the card lives
  there.
* **Never build a solid straddling `z = 0`.** The ground slab occupies
  −0.34 to −0.06 and the depth buffer will tear both into stripes.
* **A row only reads as a row from a side-on camera.** At an oblique yaw
  it foreshortens into a diagonal.

---

## 5. Narration, and how timing actually works

The audio is made first and the video is cut to fit it.

* `duration` is a **floor**. Measured speech stretches it.
* Narration is a tuple of source lines; they are joined into prose
  before synthesis, so line breaks are for your readability only.
* `promise` is spoken **as well as** shown in `teaching` style. In a
  `hype` montage it is on-screen type only — so do not write a promise
  that merely restates the first narration line, or the voice says
  everything twice.
* Captions are re-split on sentence boundaries and timed by length.
  Short punchy sentences get their own cue, which is good for jokes.

---

## 6. Reusable segments

`segments.py` holds branded pieces that repeat across videos: the contact
outro, calls to action, the credentials stack, the party sting. A lesson
does not place them; each segment declares its own placement, and
`compose()` splices and renumbers.

Do not hand-write a contact card or a call to action into a new lesson.
Use the segment, so the handles are maintained in one place.

---

## 7. What "done" means

In order. Do not skip step 4.

1. `Action = selftest, Lesson = <key>` — runs your proofs *and* writes
   the companion files.
2. Render a still per chapter.
3. **Look at every one.** This catches what nothing else can: objects
   behind the teaching card, labels stacked on labels, a figure at
   doll-house scale, a saw not touching the wood. Every one of those
   happened here and none was caught by a test.
4. Export, then verify by **frame count**, not duration:
   `nb_frames ≈ duration × fps`, and picture length ≈ audio length. A
   truncated render still reports a plausible duration — that is exactly
   how a 21-second video with 15 minutes of audio once passed review.
5. Add it to `deliverables.py`.

---

## 8. Output format for a model

Emit **complete files**, not diffs and not fragments. For each file:

    === FILE: two_v_demo/<key>_facts.py ===
    <entire file>

    === FILE: two_v_demo/lesson_<key>.py ===
    <entire file>

Rules:

* No placeholder comments like `# ... rest of implementation`. Every
  function must be complete and runnable.
* No imports of anything not in the standard library, `numpy`, or this
  package.
* No text on screen that is not either computed or explicitly listed as
  an external constant.
* British or American spelling, consistently, matching the file you are
  extending.
* Comments explain **why**, never what. `# blade tilt` on a line setting
  blade tilt is noise; `# height is set after tilt because a tilted
  blade travels further` is not.

---

## 9. A worked example to imitate

`docs/reference/lesson_hype.reference.py` is the Frankendome montage —
the largest lesson in the repository, with four versions built by
splicing and renumbering. It shows:

* full-frame `hype` styling with one line of type
* variant lessons derived from one another with `dataclasses.replace`
* segment composition for the outro and the sting
* per-chapter overlay overrides for a four-second sting inside a lesson

`docs/reference/timber.reference.py` shows deterministic procedural
texture: how to make 120 sticks all look different while guaranteeing
each one looks the *same* in every frame — get that wrong and the
material boils under motion.

`docs/reference/segments.reference.py` shows the packaging pattern.

`docs/video-engine.md` is the architecture, with diagrams.
