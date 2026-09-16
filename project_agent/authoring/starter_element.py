"""SAVE THIS AS: two_v_demo/lesson_my_element.py

An eight-second example: assemble a triangular frame from three members.
Lengths and the displayed perimeter come from the actual endpoints below.
The 4-unit side is a chosen illustration dimension, not a building claim.

HOW TO USE (PowerShell, from the DomeSim project folder)
    py -3.12 project_agent/authoring/render_lesson.py --module two_v_demo.lesson_my_element --selftest
    py -3.12 project_agent/authoring/render_lesson.py --module two_v_demo.lesson_my_element --chapter-stills
    py -3.12 project_agent/authoring/render_lesson.py --module two_v_demo.lesson_my_element --export exports/manual/my_element-silent.mp4 --silent --size 960x540 --fps 24
    py -3.12 project_agent/authoring/render_lesson.py --module two_v_demo.lesson_my_element --export exports/manual/my_element.mp4 --size 1920x1080 --fps 30

This module supplies content to the existing renderer; do not run it directly.
Only this Lesson is rendered. No registry edit, intro, outro, or other film is
added by the standalone runner. Narrated duration can exceed eight seconds.
"""
from __future__ import annotations

import math
from types import SimpleNamespace
import numpy as np
from two_v_demo.lessons import Chapter, Lesson
from two_v_demo.render_kit import AMBER, CYAN, TriangleBatch, WorldLabel, clamp

# Change these illustration inputs, then recompute all measurements from them.
SIDE = 4.0
BASE_Z = 0.5
POINTS = np.array([
    [-SIDE / 2, 0.0, BASE_Z],
    [SIDE / 2, 0.0, BASE_Z],
    [0.0, 0.0, BASE_Z + math.sqrt(3) * SIDE / 2],
])
EDGES = ((0, 1), (1, 2), (2, 0))
LENGTHS = tuple(float(np.linalg.norm(POINTS[b] - POINTS[a])) for a, b in EDGES)
PERIMETER = sum(LENGTHS)


def scene_my_element(app, opaque, transparent, p):
    """Rebuild the exact picture from chapter progress, including rewinds."""
    for index, (a, b) in enumerate(EDGES):
        reveal = clamp(p * len(EDGES) - index)
        if reveal > 0:
            end = POINTS[a] + (POINTS[b] - POINTS[a]) * reveal
            opaque.cylinder(POINTS[a], end, 0.08, AMBER, sides=8)
    for point in POINTS:
        opaque.sphere(point, 0.12, CYAN, rings=4, segments=8)
    app.world_labels.append(WorldLabel(
        np.array([0.0, 0.0, POINTS[2, 2] + 0.65]),
        f"{len(EDGES)} MEMBERS / {PERIMETER:.1f} WORLD UNITS", (230, 242, 250)))


SCENES = {"my_element_assembly": scene_my_element}
CHAPTERS = (Chapter(
    slug="assembly", number="01", title="Triangle assembly",
    promise="The members meet to form a triangle.",
    narration=("Watch the members join to form a triangular frame.",),
    equations=(f"perimeter = {PERIMETER:.1f} world units",),
    duration=8.0, camera=(90.0, 18.0, 11.0), stage="my_element_assembly",
),)


def validate_my_element():
    assert SIDE > 0 and BASE_Z > 0
    assert all(math.isclose(length, SIDE) for length in LENGTHS)
    assert math.isclose(PERIMETER, len(EDGES) * SIDE)
    assert {chapter.stage for chapter in CHAPTERS} <= set(SCENES)
    # Check real geometry and prove that seeking backwards cannot change it.
    def frame(p):
        probe = SimpleNamespace(world_labels=[])
        solid, glass = TriangleBatch(), TriangleBatch()
        scene_my_element(probe, solid, glass, p)
        assert solid.vertices and np.isfinite(solid.vertices).all()
        return solid.vertices
    before = frame(0.25)
    frame(1.0)
    assert before == frame(0.25)


LESSON = Lesson(
    key="my_element", brand="MANUAL AUTHORING", title="Triangle Assembly",
    chapters=CHAPTERS, scenes=SCENES, selftest=validate_my_element,
    snapshot_prefix="my_element", style="hype", label_layout="declutter",
)

# WHAT TO CHANGE
# Edit scene_my_element for geometry, CHAPTERS for words/timing/camera.
# Add a painter and a Chapter with its matching stage for a second shot.
# Re-run --selftest, inspect --chapter-stills, then render --silent first.
# style="plate" removes headline/cards; world labels still appear.
# Remove world_labels appends too when you want a clean picture for editing.
# A silent MP4 has no narration; add your saved Presentation Voice WAV in an editor.
