"""Render the pose vocabulary so it can be judged by eye, not by numbers."""

import sys

sys.path.insert(0, r"C:\Users\Don\Desktop\DomeSim")

from pathlib import Path

import numpy as np

from two_v_demo.app import MasterclassApp
from two_v_demo.figure import (
    POSES,
    draw_figure,
    joint_positions,
    walk_pose,
)
from two_v_demo.lessons import Chapter, Lesson
from two_v_demo.render_kit import WorldLabel

ROW_A = ("stand", "squat_deep", "squat_mid", "carry", "stoop")
ROW_B = ("reach_high", "kneel", "fasten", "fasten_high", "team_carry")

# The figure bends in its own sagittal plane, which is the X-Z plane when
# it faces +X.  The camera sits on +Y, so leaving the figure unturned is
# what puts that plane square to the lens; turning it 90 degrees would
# show the front view, where a squat and a stand look nearly identical.
SHOW = 2.4


def _place(joints, base, scale):
    """Scale a posed figure about the point it stands on."""
    origin = np.array([base[0], base[1], 0.0])
    return {key: origin + (point - origin) * scale
            for key, point in joints.items()}


def _row(app, opaque, names, label_fmt):
    for index, name in enumerate(names):
        x = 4.6 - index * 2.3
        pose = POSES[name] if isinstance(name, str) else name
        joints = joint_positions(pose, 1.75, (x, 0.0, 0.0), 0.0)
        draw_figure(opaque, _place(joints, (x, 0.0), SHOW), scale=SHOW)
        app.world_labels.append(WorldLabel(
            np.array([x, 0.0, -0.55]), label_fmt(name), (169, 188, 203)))


def scene_poses(app, opaque, transparent, p: float) -> None:
    _row(app, opaque, ROW_A, lambda n: n)


def scene_poses_b(app, opaque, transparent, p: float) -> None:
    _row(app, opaque, ROW_B, lambda n: n)


def scene_walk(app, opaque, transparent, p: float) -> None:
    for index in range(5):
        phase = index / 5.0
        x = 4.6 - index * 2.3
        joints = joint_positions(walk_pose(phase), 1.75, (x, 0.0, 0.0), 0.0)
        draw_figure(opaque, _place(joints, (x, 0.0), SHOW), scale=SHOW)
        app.world_labels.append(WorldLabel(
            np.array([x, 0.0, -0.55]), f"phase {phase:.2f}", (169, 188, 203)))


LESSON = Lesson(
    key="probe", brand="FIGURE PROBE", title="Figure probe",
    chapters=(
        Chapter("poses", "01", "Pose vocabulary", "Every named pose.",
                ("Checking the figure by eye.",), (), 10.0,
                (90.0, 8.0, 13.0), "poses"),
        Chapter("posesb", "02", "Pose vocabulary, part two", "The rest.",
                ("Checking the figure by eye.",), (), 10.0,
                (90.0, 8.0, 13.0), "posesb"),
        Chapter("walk", "03", "Walk cycle", "One full stride.",
                ("Checking the walk cycle by eye.",), (), 10.0,
                (90.0, 8.0, 13.0), "walk"),
    ),
    scenes={"poses": scene_poses, "posesb": scene_poses_b,
            "walk": scene_walk},
    snapshot_prefix="figure",
)

app = MasterclassApp(size=(1600, 900), hidden=True, lesson=LESSON)
out = Path(sys.argv[1])
app.render_shots([5.0, 15.0, 25.0], out)
app.pygame.quit()
print("done")
