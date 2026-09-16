"""The Twenty Dollar Pine, Part Two.

Scenes and copy.  Every figure comes from :mod:`two_v_demo.pvtwo_facts`,
which computes and proves them.

Layout note: this renderer's cameras sit on +Y, so two things separated
along Y are separated in *depth* and the nearer one hides the further
one.  Lay rows out along **X**.
"""

from __future__ import annotations

import math

import numpy as np

from .pvtwo_facts import (
    EXTERNAL_CONSTANTS,
    pvtwo_items,
    pvtwo_report,
    pvtwo_summary,
    validate_pvtwo,
)
from .lessons import Chapter, Lesson
from .render_kit import (
    AMBER,
    CYAN,
    GREEN,
    MUTED,
    PURPLE,
    RED,
    WHITE,
    WorldLabel,
    clamp,
    ease_in_out,
    smoothstep,
)


ITEMS = pvtwo_items()
SUMMARY = pvtwo_summary()
PALETTE = (CYAN, AMBER, GREEN, PURPLE, RED)


def _rgb(colour) -> tuple[int, int, int]:
    return (int(colour[0] * 255), int(colour[1] * 255), int(colour[2] * 255))


def scene_pvtwo_overview(app, opaque, transparent, p: float) -> None:
    """Open on the whole subject, assembling."""
    reveal = smoothstep(clamp(p * 1.5))
    for index, item in enumerate(ITEMS):
        if index / len(ITEMS) > reveal:
            continue
        angle = math.tau * index / len(ITEMS)
        centre = np.array([4.0 * math.cos(angle), 4.0 * math.sin(angle), 1.6])
        colour = PALETTE[index % len(PALETTE)]
        opaque.sphere(centre, 0.5 + item.size, colour, 5, 12)
        opaque.cylinder(np.array([0.0, 0.0, 1.6]), centre, 0.05, MUTED, 6)
    app.world_labels.append(WorldLabel(
        np.array([0.0, 0.0, 5.0]),
        f"{SUMMARY['parts']} PARTS IN {SUMMARY['classes']} CLASSES",
        (61, 211, 255)))


def scene_pvtwo_classes(app, opaque, transparent, p: float) -> None:
    """A labelled bar per class -- the montage's workhorse shape."""
    reveal = clamp(p * 1.35)
    largest = max(item.total for item in ITEMS) or 1.0
    span = 12.0
    step = span / max(1, len(ITEMS) - 1)
    for index, item in enumerate(ITEMS):
        if index / len(ITEMS) > reveal:
            continue
        x = -span * 0.5 + index * step
        height = 4.0 * (item.total / largest)
        colour = PALETTE[index % len(PALETTE)]
        opaque.box((x, 0.0, height * 0.5 + 0.2), (2.0, 0.9, max(0.05, height)),
                   colour)
        app.world_labels.append(WorldLabel(
            np.array([x, 0.0, height + 0.9]),
            f"{item.name}\nx{item.count}", _rgb(colour)))
    app.world_labels.append(WorldLabel(
        np.array([0.0, 0.0, -0.9]),
        "replace these with the real classes", (169, 188, 203)))


def scene_pvtwo_recap(app, opaque, transparent, p: float) -> None:
    """Close by restating the shape of the answer."""
    spin = p * math.tau * 0.35
    for index, item in enumerate(ITEMS):
        angle = math.tau * index / len(ITEMS) + spin
        centre = np.array([3.4 * math.cos(angle), 3.4 * math.sin(angle),
                           1.4 + item.size])
        opaque.box(tuple(centre), (1.2, 1.2, 0.5),
                   PALETTE[index % len(PALETTE)])
    app.world_labels.append(WorldLabel(
        np.array([0.0, 0.0, 4.8]),
        "EVERY NUMBER HERE WAS COMPUTED", (111, 235, 155)))


SCENES = {
    "pvtwo_overview": scene_pvtwo_overview,
    "pvtwo_classes": scene_pvtwo_classes,
    "pvtwo_recap": scene_pvtwo_recap,
}


def pvtwo_equations(app, stage: str) -> list[str]:
    """Live figures. The renderer appends these to a chapter's fixed lines,
    so do not restate anything already written there."""
    if stage == "pvtwo_overview":
        return [f"total = {SUMMARY['total']:.4f}"]
    if stage == "pvtwo_classes":
        return [
            f"{item.name:<10} {item.size:7.4f} x{item.count:<4} "
            f"= {item.total:8.4f}"
            for item in ITEMS
        ]
    return []


CHAPTERS: tuple[Chapter, ...] = (
    Chapter(
        "overview", "01", "What we are looking at",
        "Two suitable southern pines, roughly 15-inch diameter with about 60 feet of useful stem.",
        (
            "In Q4 2025 Alabama pine sawtimber stumpage was roughly $17-$21 per",
            "ton; the current Q2 2026 South-wide average is $23.34/ton.",
            "Lower-grade pine pulpwood was only about $6/ton.",
        ),
        (f"parts = {SUMMARY['parts']}", f"classes = {SUMMARY['classes']}"),
        12.0, (34.0, 24.0, 16.0), "pvtwo_overview",
    ),
    Chapter(
        "classes", "02", "The classes",
        "A local Tuscaloosa-area firewood seller currently lists $275/cord pickup and $300/cord delivered.",
        (
            "Alabama Extension defines a cord as 128 cubic feet of stacked wood,",
            "about 90 cubic feet of solid wood, and a 15-inch pine is about",
            "0.35-0.45 cord.",
            "Radial processing gives 1 log to 2 to 4 to 8 sectors; 8 times 60",
            "feet of usable stem is 480 linear feet, cut into six-foot members",
            "that is 80 structural blanks per tree.",
        ),
        ("grouped by measurement, not by name",),
        14.0, (90.0, 16.0, 18.0), "pvtwo_classes",
    ),
    Chapter(
        "recap", "03", "The whole thing, once more",
        "Two trees offer about 160 blanks against the approximately 120-member dome frame.",
        (
            "Under the dome model those same two trees supply the wedge stock for",
            "the 300-square-foot structural shell, whose commercial framing",
            "replacement value is modeled at about $4,800.",
            "If that avoided framing would have been financed at 6.5% over 30",
            "years, the nominal payment avoidance is roughly $10,900.",
        ),
        ("computed -> proved -> drawn",),
        12.0, (30.0, 26.0, 16.0), "pvtwo_recap",
    ),
)


PVTWO_LESSON = Lesson(
    key="pvtwo",
    brand="THE TWENTY DOLLAR PINE, PART TWO",
    title="The Twenty Dollar Pine, Part Two",
    chapters=CHAPTERS,
    scenes=SCENES,
    equations=pvtwo_equations,
    selftest=validate_pvtwo,
    report=pvtwo_report,
    snapshot_prefix="pvtwo",
)
