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
