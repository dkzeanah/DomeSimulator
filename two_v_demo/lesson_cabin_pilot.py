"""Cabin World pilot: the smallest complete film set in the baseline scene.

Two chapters, and every piece a re-render needs, each used once: the world
through :func:`cabin_world.paint`, the sunset through ``Lesson.backdrop``,
the low sun through ``Lesson.light``, cameras from :mod:`two_v_demo.shots`
aimed at :func:`cabin_world.landmarks`, a chapter's own geometry on top of
the world (a marker in the unfinished crown), labels, and figures computed
by the modules that own them. Copy this file to start a re-render.

    py -3.12 -m rerender prompt cabin_pilot     # there is no such item; see rerender/README.md
"""

from __future__ import annotations

import numpy as np

from . import cabin_world as cw
from . import shots
from .lessons import Chapter, Lesson
from .render_kit import CYAN_SOFT, WorldLabel, smoothstep


def _figures() -> dict:
    """Every number the pilot states, from where it is computed."""
    from wedge_book import systems

    m = cw.landmarks()
    clock = systems.build_clock()
    return {"splits": m.splits, "members": int(clock["members"]),
            "missing": len(cw.missing_faces())}


F = _figures()


def scene_grain(app, opaque, transparent, p: float) -> None:
    cw.paint(app)
    m = cw.landmarks()
    app.world_labels.append(WorldLabel(
        m.log_end + np.array([0.0, 0.0, m.trunk_r * 1.9]),
        f"{F['splits']} WEDGES FROM ONE LOG", (255, 214, 150)))


def scene_dome(app, opaque, transparent, p: float) -> None:
    cw.paint(app)
    m = cw.landmarks()
    # This chapter's own geometry on top of the world: a glow in the gap.
    pulse = 0.6 + 0.4 * smoothstep(min(1.0, p * 2.0))
    transparent.sphere(m.gap, 0.55 * pulse, CYAN_SOFT, 6, 14)
    app.world_labels.append(WorldLabel(
        m.apex + np.array([0.0, 0.0, 0.9]), f"{F['members']} MEMBERS", (111, 235, 155)))


SCENES = {"cabin_grain": scene_grain, "cabin_dome": scene_dome}


def _moves():
    m = cw.landmarks()
    back = -m.log_axis
    grain = shots.push_in(m.log_end, m.log_end + back * 2.4 + [0.3, 0, 0.9],
                          m.log_end + back * 1.1 + [0.1, 0, 0.35], fov_start=44, fov_end=36)
    dome = shots.orbit(m.dome_centre + [0, 0, m.dome_r * 0.45], radius=m.dome_r * 3.6,
                       height=m.dome_r * 0.9, start_deg=-100, sweep_deg=35, fov=48)
    return {"cabin_grain": grain, "cabin_dome": dome}


MOVES = _moves()


def camera(app, chapter, progress: float, width: int, height: int):
    eye, target, fov = MOVES[chapter.stage](progress)
    return eye, target, fov


CHAPTERS = (
    Chapter(
        "grain", "01", "One log",
        "Every member starts here.",
        (f"Every member of this dome starts as one of {F['splits']} wedges, "
         "ripped from a log with a chainsaw, straight through its heart.",),
        (f"wedges per log = {F['splits']}",),
        8.0, (0.0, 0.0, 0.0), "cabin_grain"),
    Chapter(
        "dome", "02", "One dome",
        "The last triangles go up.",
        (f"{F['members']} of those members make the frame, and {F['missing']} "
         "crown triangles are still to go up.",),
        (f"members = {F['members']}",),
        8.0, (0.0, 0.0, 0.0), "cabin_dome"),
)


def validate_cabin_pilot() -> None:
    cw.validate_cabin_world()
    for ch in CHAPTERS:
        eye, target, fov = MOVES[ch.stage](0.5)
        assert np.all(np.isfinite(eye)) and 20 < fov < 70
        assert np.linalg.norm(np.asarray(eye) - np.asarray(target)) > 0.3


CABIN_PILOT_LESSON = Lesson(
    key="cabin_pilot", brand="DOMESIM", title="Cabin World Pilot",
    chapters=CHAPTERS, scenes=SCENES, selftest=validate_cabin_pilot,
    snapshot_prefix="cabin_pilot", camera_fn=camera, ground="off",
    backdrop=cw.backdrop, light=cw.LIGHT, label_layout="declutter",
)
