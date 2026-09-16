# Write one DomeSim film

You are writing ONE Python file: a *lesson module* for the DomeSim
repository. A lesson is a narrated 3-D film. The renderer already exists;
your file supplies the chapters, the copy, and the painting code.

## Hard rules. A file that breaks any of these is rejected.

1. **Every number on screen is computed, never typed.** Import a facts
   module and call it. If a figure genuinely cannot be derived -- a price, a
   labour rate -- assign it to a named constant with a comment saying where
   it came from, and keep those together in one block.
2. **Lay rows of things out along X.** The camera sits on +Y looking at the
   origin, so two objects separated along Y are separated in *depth*: the
   near one hides the far one and both look foreshortened. Separate along X,
   or stack along Z.
3. **A painter is a pure function of (app, opaque, transparent, progress).**
   Never read the clock, never use an unseeded random number. The same
   progress value must always draw the same frame, or the render is not
   reproducible.
4. **The lesson proves itself.** Write a validate function that asserts what
   the film claims, and pass it as `selftest=`. The renderer runs it before
   drawing anything.
5. **Import only** from: `two_v_demo.lessons`, `two_v_demo.render_kit`,
   `two_v_demo.visual_objects`, the facts modules listed below, plus `math`
   and `numpy`. No file reading, no network, no subprocess.
6. **Nothing straddles z=0.** The ground is at z=0; build upward.


## The drawing API

Two batches reach every painter. `opaque` for solid things,
`transparent` for anything with alpha below 1 (glass, ghosts,
shading). Both are the same type and take the same calls:

    opaque.cylinder(start, end, radius, colour, sides=8)
    opaque.sphere(centre, radius, colour, rings=5, segments=8)
    opaque.box(centre, size, colour)
    opaque.disc(centre, radius, colour, segments=48)
    opaque.cone(base, tip, radius, colour, sides=10)
    opaque.arrow(start, end, radius, colour)
    opaque.triangle(a, b, c, colour, normal=None)
    opaque.quad(a, b, c, d, colour, normal=None)

Points are `np.array([x, y, z])`. Colours are RGBA tuples,
0.0-1.0. Import the named ones from `two_v_demo.render_kit`:

    AMBER  AMBER_SOFT  BG  CYAN  CYAN_SOFT  GREEN  GROUND  MUTED  NAVY  PURPLE  RED  SURFACE  WHITE

Also from render_kit: `clamp(v)`, `smoothstep(v)`,
`ease_in_out(v)` for easing a reveal, and `WorldLabel`.

### Text pinned in the world

    app.world_labels.append(WorldLabel(
        np.array([x, y, z]), "TEXT", (red, green, blue)))

The colour here is 0-255 integers, not floats. Labels are drawn
as flat text at that point, always facing the viewer.

## Ready-made objects

Do not redraw what exists. Put one on the stage with:

    stage = visual_objects.stage_for(app, opaque, transparent,
                                     origin=(x, y, z))
    visual_objects.draw(stage, "person", height=1.8)

| key | what it is | knobs |
|---|---|---|
| wedge_member | Raw wedge member | length, depth, lift, roll_deg |
| timber_stick | Rough timber | length, radius, lift, seed, style |
| board_2x4 | Dressed two-by-four | length_ft, units_per_ft, on_edge, lift |
| section_disc | Bucked section, end-on | radius, pieces, spread, lift |
| wedge_shell | Pinwheel wedge dome | radius, reveal |
| solved_dome | The simulator's solved dome | radius, orientation, keys, alpha |
| hub_dome | 2V hub dome | radius, reveal, rough |
| person | Person | height, pose, walk, heading_deg |
| force_arrow | Compression or tension | length, kind, thickness, lift |
| dimension | Dimension line | length, lift |
| icon | Pinned pictogram | size, alpha, angle, lift |
| pine_tree | Pine tree, standing or felled | fell, limb, units_per_ft, icon |
| log_sections | Log, bucked and split | buck, explode, units_per_ft, icon |
| harvest | The harvest, tree to wedges | fell, limb, buck, explode, units_per_ft, icon |

Pictograms available to the `icon` object and to callouts:

    chainsaw, pine, log, slice, split, wedge, fuel, calendar, clock, dollar, dome, ruler, person, truck, factory, board, house, drop, bolt, check, cross, arrow, sun, flame

## Where numbers come from

Call one of these. Each is validated by its own module, which
is what makes it safe to put on screen:

| facts id | module.function | what it gives |
|---|---|---|
| al_build.assumptions | al_build.ASSUMPTIONS | The assembly line's editable assumption table (wages, workers, capex, pricing, QC) |
| al_build.comparisons | al_build.building_comparisons | Box-vs-dome comparisons (shed and home tiers) priced by identical rates |
| book.design_first | two_v_demo.book_math.design_first | Method A: the cut list and felling list from a chosen design |
| book.frame_counts | two_v_demo.book_math.frame_counts | Book's frame accounting: (120 members, 40 panels, 65 unique edges) and why 40 triangles need 120 members |
| book.report | two_v_demo.book_math.book_math_report | Plain-text calculation audit: declared constants, both methods, the fortnight, and the unflattering figures printed on purpose |
| book.round_trip | two_v_demo.book_math.round_trip | The proof that Methods A and B are one calculation held at opposite ends; prints the residual |
| book.tree_first | two_v_demo.book_math.tree_first | Method B: size the dome from the tree you have (BOOK_TREE) |
| costing.radius_for_floor | two_v_demo.dome_costing.radius_for_floor | Dome radius that delivers a given floor area |
| costing.report | two_v_demo.dome_costing.costing_report | Plain-text costing report for a floor area |
| costing.variants | two_v_demo.dome_costing.build_variants | Costed dome build variants (framing value, shell options) from the shared cost model |
| geometry.demo | two_v_demo.geometry.build_demo_geometry | The 2V demo geometry: chord factors, strut classes, triangle classes, area and angle audit for the reference dome |
| geometry.fit | two_v_demo.geometry.fit_measurements | Fit the two chord classes to supplied strut lengths and return the resulting radius, counts, and per-class lengths |
| geometry.report | two_v_demo.geometry.calculation_report | Plain-text calculation report for the 2V dome |
| hubless.report | two_v_demo.hubless_geometry.hubless_report | Plain-text hubless build report |
| hubless.summary | two_v_demo.hubless_geometry.hubless_summary | Hubless frame counts: 40 triangles, 120 members, 65 unique edges, seam and panel classes |
| pine.model | two_v_demo.pine_value_economics.pine | The pine value-ladder model: solid board feet, wedge vs sawn recovery, framing value, financed avoided payments, wage per hour |
| pine.sources | two_v_demo.pine_value_economics.source_lines | Every borrowed constant the pine model uses, with its provenance (author-measured vs published) |
| pine.tokens | two_v_demo.pine_value_economics.token_specs | The pine model's token specs (the live figures a film would quote) |
| wedge.build_plan | two_v_demo.wedge_geometry.build_plan | The full two-tree build plan: blanks, members needed, surplus, and the dome the stock sizes |
| wedge.radius_for_member | two_v_demo.wedge_geometry.radius_for_member_length | Invert the geometry: which dome radius a given member length sizes |
| wedge.report | two_v_demo.wedge_geometry.wedge_report | Plain-text wedge report (tree, sections, members, gaskets) |
| wedge.tree_yield | two_v_demo.wedge_geometry.tree_yield | What one log yields: solid board feet, wedge recovery, 2x4 recovery, and the honest comparison between them |

In a lesson module, import the function directly, e.g.
`from two_v_demo.geometry import build_demo_geometry`.

## The camera and the stage

`camera=(yaw_degrees, pitch_degrees, distance)` on every chapter. The camera
orbits a fixed target at (0, 0, 2.25).

* `yaw=90` puts the camera on +Y. X then runs across the screen: this is the
  yaw to use for any row or line-up.
* `yaw=40..55` gives a three-quarter view, good for a single object.
* `pitch` 12-22 for most shots; 30-40 to look down into something.
* `distance` about twice the widest thing on screen. A 5-unit dome frames
  well at 15-18.

World units are metres-ish: a person is 1.8 tall, a dome 5 across. Keep the
subject in the upper two-thirds of the frame -- the overlay uses the bottom.


## Chapter and Lesson

`Chapter(slug, number, title, promise, narration, equations, duration, camera, stage, overlay, callouts)`

* `slug` short id, `number` "01" upward, `title` on the card
* `promise` one sentence -- the headline, spoken as well in
  teaching style
* `narration` a tuple of complete sentences, one per entry
* `equations` a tuple of short lines for the live calculation
  panel; leave it `()` only if you want that panel empty
* `duration` seconds, the floor -- narration may run longer
* `stage` the SCENES key this chapter paints
* `overlay` optional: "math" turns the chapter into a
  worksheet with the picture on the left

`Lesson(key, brand, title, chapters, scenes, equations, selftest, report, snapshot_prefix, style, voice_rate, audio_bed, audio_bed_gain, camera_fn, label_layout, frame_fit, ground)`

* `style` "teaching" (cards) or "hype" (one big line)
* `label_layout="declutter"` stops world labels overlapping
* `ground="off"` if your subject brings its own floor
* `selftest` your validate function

## What to output

Exactly one Python file. No explanation before or after it, no markdown
fences around it -- just the file, starting with its docstring.

The docstring must state, on its own line, where the file is saved:

    SAVE THIS AS: two_v_demo/lesson_<key>.py

Use the same `<key>` everywhere: the file name, the `key=` field, the
`snapshot_prefix=`, and the prefix on every scene name. `<key>` is lowercase
letters, digits and underscores, starting with a letter.

The file must end with a module-level `Lesson(...)` assignment.

After the Lesson, add a comment block giving the two commands that run it:

    # HOW TO SEE IT
    #   py -3.12 project_agent/authoring/render_lesson.py --module two_v_demo.lesson_<key> --chapter-stills
    #   py -3.12 project_agent/authoring/render_lesson.py --module two_v_demo.lesson_<key> --export exports/<key>.mp4

## Checklist -- read your own file against this before answering

* every figure on screen traces to a facts call or a named, sourced constant
* every row is laid along X, not Y
* every chapter has: slug, number, title, promise, narration, equations,
  duration, camera, stage -- in that order
* every `stage` string appears as a key in the SCENES dict
* narration is one complete sentence per tuple entry
* chapter numbers are "01", "02", ... and are unique
* the validate function asserts something that could actually fail
* the file imports nothing outside the allowed list


## A complete worked example

This file renders today. Copy its shape.

```python
"""WORKED EXAMPLE -- a complete masterclass lesson in one file.

This is the pattern every film in this repository follows, reduced to the
smallest thing that is still real. It renders, it proves itself, and every
number it puts on screen is computed by code that also validates it.

WHERE A FILE LIKE THIS GOES
    two_v_demo/lesson_<key>.py        (key is lowercase letters and underscores)

HOW TO SEE IT, WITHOUT REGISTERING ANYTHING
    py -3.12 project_agent/authoring/render_lesson.py --module project_agent.authoring.example_lesson --selftest
    py -3.12 project_agent/authoring/render_lesson.py --module project_agent.authoring.example_lesson --stills 6,20,34
    py -3.12 project_agent/authoring/render_lesson.py --module project_agent.authoring.example_lesson --export exports/example.mp4

THE FOUR RULES THIS FILE OBEYS
    1. Numbers are computed, never typed. Every figure below comes from
       two_v_demo.geometry, which has its own validator.
    2. Rows are laid out along X. The camera sits on +Y, so two things
       separated along Y are separated in depth and the near one hides the far.
    3. A painter is a pure function of (stage, progress). No wall-clock time,
       and no random numbers without a fixed seed, or the render stops being
       reproducible.
    4. The lesson proves itself in validate_example(), which the renderer runs
       before it draws a single frame.
"""

from __future__ import annotations

import math

import numpy as np

from two_v_demo import visual_objects
from two_v_demo.geometry import (
    DomeMeasurements,
    build_demo_geometry,
    fit_measurements,
)
from two_v_demo.lessons import Chapter, Lesson
from two_v_demo.render_kit import (
    AMBER,
    CYAN,
    GREEN,
    MUTED,
    WHITE,
    WorldLabel,
    clamp,
    ease_in_out,
    smoothstep,
)

# ----------------------------------------------------------------------
# The numbers. Computed once at import, from the repository's own geometry.
# ----------------------------------------------------------------------

GEOMETRY = build_demo_geometry()
FIT = fit_measurements(72.0, 63.5)
MEASURE = DomeMeasurements(FIT.best_fit_radius)

RADIUS = 5.0
"""World radius the dome is drawn at.

The renderer works in these units, not in inches. The inches live in the
labels, where a viewer can read them."""

EDGE_CLASS = dict(zip(GEOMETRY.edges, GEOMETRY.edge_class_by_edge))
HEMISPHERE = tuple(GEOMETRY.hemisphere_edges)
LONG_COUNT = sum(1 for edge in HEMISPHERE if EDGE_CLASS[edge] == "LONG")
SHORT_COUNT = sum(1 for edge in HEMISPHERE if EDGE_CLASS[edge] == "SHORT")


def _rgb(colour) -> tuple[int, int, int]:
    return (int(colour[0] * 255), int(colour[1] * 255), int(colour[2] * 255))


def steps_struts() -> tuple[str, ...]:
    """The math screen, derived rather than asserted."""
    return (
        "two chord factors come out of the subdivision:",
        f"long   {GEOMETRY.long_factor:.6f} x radius",
        f"short  {GEOMETRY.short_factor:.6f} x radius",
        f"fit {MEASURE.long_cut_length:.1f} in and "
        f"{MEASURE.short_cut_length:.1f} in struts to those factors",
        f"and the radius they agree on is {FIT.best_fit_radius:.1f} in "
        f"({MEASURE.diameter / 12.0:.1f} ft across)",
        f"{LONG_COUNT} long and {SHORT_COUNT} short = "
        f"{LONG_COUNT + SHORT_COUNT} struts in the hemisphere",
        f"floor area {MEASURE.floor_area / 144.0:.0f} sq ft",
        "two lengths, one shape -- which is the whole reason this is "
        "buildable by one person with a chop saw",
    )


# ----------------------------------------------------------------------
# Painters. The signature is always (app, opaque, transparent, progress).
# ----------------------------------------------------------------------

def scene_shell(app, opaque, transparent, p: float) -> None:
    """Raise the hemisphere, one strut at a time, coloured by length class."""
    grown = ease_in_out(clamp(p * 1.3))
    shown = int(len(HEMISPHERE) * grown)
    for edge in HEMISPHERE[:shown]:
        start = GEOMETRY.vertices[edge[0]] * RADIUS
        end = GEOMETRY.vertices[edge[1]] * RADIUS
        colour = CYAN if EDGE_CLASS[edge] == "LONG" else AMBER
        opaque.cylinder(start, end, 0.075, colour, 8)

    # A person for scale, borrowed rather than drawn again.
    stage = visual_objects.stage_for(app, opaque, transparent,
                                     origin=(RADIUS + 1.6, 0.0, 0.0))
    visual_objects.draw(stage, "person", height=1.8, heading_deg=180.0)

    app.world_labels.append(WorldLabel(
        np.array([0.0, 0.0, RADIUS + 1.4]),
        f"{MEASURE.diameter / 12.0:.1f} FT ACROSS", _rgb(WHITE)))
    if p > 0.45:
        app.world_labels.append(WorldLabel(
            np.array([0.0, 0.0, RADIUS + 0.4]),
            f"{shown} of {len(HEMISPHERE)} struts", _rgb(MUTED)))


def scene_classes(app, opaque, transparent, p: float) -> None:
    """The two strut lengths, side by side, to scale with each other."""
    reveal = smoothstep(clamp(p * 1.4))
    rows = (
        ("LONG", MEASURE.long_cut_length, LONG_COUNT, CYAN, 2.9),
        ("SHORT", MEASURE.short_cut_length, SHORT_COUNT, AMBER, 1.3),
    )
    longest = max(row[1] for row in rows)
    for name, inches, count, colour, height in rows:
        length = RADIUS * 1.7 * (inches / longest) * reveal
        if length <= 0.01:
            continue
        # Each stick lies along X, and the two are stacked in Z. Laying them
        # along Y instead points them into the screen, where the camera sees a
        # foreshortened stub and the near one hides the far one. This is the
        # single most common way a first draft comes back looking wrong.
        opaque.cylinder(np.array([-length / 2.0, 0.0, height]),
                        np.array([length / 2.0, 0.0, height]),
                        0.16, colour, 10)
        app.world_labels.append(WorldLabel(
            np.array([length / 2.0 + 1.2, 0.0, height]),
            f"{name}  {inches:.1f} in", _rgb(colour)))
        if p > 0.5:
            app.world_labels.append(WorldLabel(
                np.array([-length / 2.0 - 1.2, 0.0, height]),
                f"x{count}", _rgb(MUTED)))
    if p > 0.7:
        app.world_labels.append(WorldLabel(
            np.array([0.0, 0.0, 4.3]),
            f"long / short = {GEOMETRY.ratio:.4f}", _rgb(GREEN)))


def scene_check(app, opaque, transparent, p: float) -> None:
    """A quiet stage for the math screen: the shell, still, at rest."""
    for edge in HEMISPHERE:
        start = GEOMETRY.vertices[edge[0]] * RADIUS
        end = GEOMETRY.vertices[edge[1]] * RADIUS
        colour = CYAN if EDGE_CLASS[edge] == "LONG" else AMBER
        opaque.cylinder(start, end, 0.055, colour, 6)
    drift = math.sin(p * math.pi) * 0.4
    app.world_labels.append(WorldLabel(
        np.array([0.0, 0.0, RADIUS + 1.0 + drift]),
        "EVERY FIGURE RECOMPUTED AT IMPORT", _rgb(MUTED)))


SCENES = {
    "example_shell": scene_shell,
    "example_classes": scene_classes,
    "example_check": scene_check,
}


# ----------------------------------------------------------------------
# Chapters. camera is (yaw degrees, pitch degrees, distance in world units).
# ----------------------------------------------------------------------

CHAPTERS: tuple[Chapter, ...] = (
    Chapter(
        "shell", "01", "Two lengths, one shape",
        "Sixty-five struts, and only two of them are different.",
        # One sentence per line. Each line is its own paragraph on the card,
        # so a sentence split across two lines reads as two broken fragments.
        ("A two-frequency dome is built from exactly two strut lengths.",
         "Every cyan stick is the long one and every amber stick the short "
         "one, and there is no third kind anywhere in it.",
         "That is what makes this shape buildable by one person with a chop "
         "saw and a stop block."),
        # Non-math chapters can still fill the live calculation panel. Leave
        # this empty and the panel renders as an empty box.
        (f"long strut   {MEASURE.long_cut_length:.1f} in",
         f"short strut  {MEASURE.short_cut_length:.1f} in",
         f"{LONG_COUNT} long + {SHORT_COUNT} short = "
         f"{LONG_COUNT + SHORT_COUNT} struts"),
        14.0, (46.0, 18.0, 17.0), "example_shell"),
    Chapter(
        "classes", "02", "The two sticks",
        "Cut these two lengths and you have the whole dome.",
        ("Here are the two lengths beside each other, drawn to the same scale "
         "as one another.",
         "The numbers beside them are not rounded for the caption: they are "
         "the cut lengths the geometry module computes from the radius the "
         "struts themselves imply.",
         "Cut those two, and the shape is decided."),
        (f"long / short = {GEOMETRY.ratio:.4f}",
         f"radius {FIT.best_fit_radius:.1f} in",
         f"{MEASURE.diameter / 12.0:.1f} ft across"),
        13.0, (90.0, 14.0, 14.0), "example_classes"),
    Chapter(
        "check", "03", "Where the numbers come from",
        "Nothing on screen was typed in.",
        ("Every figure in this lesson traces back to one function that also "
         "proves itself.",
         "The chord factors are subdivision geometry, the radius is fitted to "
         "the two measured struts, and the counts are the edges themselves, "
         "sorted by class and counted.",
         "Change the two strut lengths at the top of the file and every number "
         "you have seen moves with them."),
        steps_struts(), 18.0, (46.0, 20.0, 17.0), "example_check",
        overlay="math"),
)


# ----------------------------------------------------------------------
# The proof. Run before anything renders.
# ----------------------------------------------------------------------

def validate_example() -> None:
    """Prove the lesson draws something and states nothing it cannot back."""
    from two_v_demo.render_kit import TriangleBatch

    assert LONG_COUNT + SHORT_COUNT == len(HEMISPHERE), "a strut class was lost"
    assert LONG_COUNT > 0 and SHORT_COUNT > 0, "a class came out empty"
    assert MEASURE.long_cut_length > MEASURE.short_cut_length > 0.0
    assert 1.0 < GEOMETRY.ratio < 1.2, GEOMETRY.ratio   # long / short

    class _Probe:
        def __init__(self) -> None:
            self.world_labels: list = []
            self.world_icons: list = []

    for stage, painter in SCENES.items():
        for progress in (0.1, 0.5, 1.0):
            probe = _Probe()
            opaque, transparent = TriangleBatch(), TriangleBatch()
            painter(probe, opaque, transparent, progress)
            if progress > 0.2:
                assert opaque.vertices, (stage, progress)
            for label in probe.world_labels:
                assert label.text.strip(), (stage, progress)

    steps = steps_struts()
    assert len(steps) >= 5 and all(line.strip() for line in steps)


EXAMPLE_LESSON = Lesson(
    key="example",
    brand="AUTHORING / WORKED EXAMPLE",
    title="Two Lengths, One Shape",
    chapters=CHAPTERS,
    scenes=SCENES,
    selftest=validate_example,
    snapshot_prefix="example",
    style="teaching",
    label_layout="declutter",
)
```

## Your task

Replace this section with what the film should be about, then output nothing but the file.
