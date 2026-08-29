"""Put the crew on the same scale as everything else in the frame.

``figure.joint_positions`` works in real metres, but every other lesson in
this renderer builds its world about five units across and the camera
looks at a fixed point 2.25 units up.  A 1.75 m figure therefore came out
small and sat below the centre of frame.  Drawing it at FIGURE_SCALE puts
a person's mid-height at the camera's target and makes them the size of
the bars they are standing next to.

Also flips left-to-right reading order: with the camera on the +Y axis,
increasing X runs towards screen *left*, so sequences were coming out
backwards.
"""

import re
from pathlib import Path

p = Path(r"C:\Users\Don\Desktop\DomeSim\two_v_demo\lesson_line.py")
s = p.read_text(encoding="utf-8")


def sub(old: str, new: str, count: int = 1) -> None:
    global s
    if old not in s:
        raise SystemExit("pattern not found: " + old[:200])
    s = s.replace(old, new, count)


# 1. One scale constant, applied wherever a body is drawn.
sub(
    "LOAD_MAX_LENGTH = 1.7",
    "# The renderer's world is about five units across and its camera looks\n"
    "# at a point 2.25 units up.  Drawing a 1.75 m person at this scale puts\n"
    "# their chest on that point and makes them the size of the charts they\n"
    "# stand beside.  Every figure-relative height in this module is in the\n"
    "# same scaled units.\n"
    "FIGURE_SCALE = 2.2\n"
    "\n"
    "LOAD_MAX_LENGTH = 1.7",
)

sub(
    '''    joints = _place(joint_positions(pose, STATURE_M), origin, yaw)
    draw_figure(batch, joints, highlight=highlight)
    if load is not None:
        draw_load(batch, joints, load, load_colour)
    return joints''',
    '''    joints = _place(
        joint_positions(pose, STATURE_M * FIGURE_SCALE), origin, yaw)
    draw_figure(batch, joints, highlight=highlight, scale=FIGURE_SCALE)
    if load is not None:
        draw_load(batch, joints,
                  tuple(value * FIGURE_SCALE for value in load), load_colour)
    return joints''',
)

# 2. Sequences and bar rows must read left to right on screen.
sub(
    "        x = origin[0] - span * 0.5 + index * (width + gap) + width * 0.5",
    "        # +X points to screen left from this lesson's camera, so the\n"
    "        # first row has to take the largest X to read first.\n"
    "        x = origin[0] + span * 0.5 - index * (width + gap) - width * 0.5",
)
sub(
    "        x = -span * 0.5 + index * spacing\n"
    "        pose = _pose_for(motion, 0.65)",
    "        x = span * 0.5 - index * spacing\n"
    "        pose = _pose_for(motion, 0.65)",
)

# 3. The lift's limb readout sat on top of the live-calculation card.
sub(
    '''            np.array([-2.3, 0.0, 2.2 - index * 0.42]),''',
    '''            np.array([3.1, 0.0, 4.3 - index * 0.62]),''',
)

# 4. Figure-relative label heights, now in scaled units.
for old_z, new_z, marker in (
    ("0.0, 2.9]),\n                   f\"MECHANICAL WORK", "0.0, 5.2]),\n                   f\"MECHANICAL WORK", "lift"),
    ("np.array([0.0, 0.0, 2.9]),\n        f\"{BODY_MASS_KG:.0f} kg", "np.array([0.0, 0.0, 4.6]),\n        f\"{BODY_MASS_KG:.0f} kg", "skeleton"),
):
    if old_z in s:
        s = s.replace(old_z, new_z, 1)

s = s.replace("WorldLabel(np.array([x, 0.0, 2.35]),", "WorldLabel(np.array([x, 0.0, 4.5]),", 1)
s = s.replace("WorldLabel(np.array([0.0, 0.0, 2.6]),\n                   f\"{motion.distance:.1f} m EACH WAY\"",
              "WorldLabel(np.array([0.0, 0.0, 4.6]),\n                   f\"{motion.distance:.1f} m EACH WAY\"", 1)
s = s.replace("WorldLabel(np.array([x, 0.0, 2.05]),\n                   f\"{cost.watts:.0f} W\"",
              "WorldLabel(np.array([x, 0.0, 3.9]),\n                   f\"{cost.watts:.0f} W\"", 1)
s = s.replace("WorldLabel(np.array([-2.0, 0.0, 2.6]),", "WorldLabel(np.array([-2.0, 0.0, 4.6]),", 1)
s = s.replace("WorldLabel(np.array([-2.0, 0.0, 2.4]),", "WorldLabel(np.array([-2.0, 0.0, 4.4]),", 1)
s = s.replace("WorldLabel(np.array([2.0, 0.0, 2.9]),", "WorldLabel(np.array([2.0, 0.0, 5.0]),", 1)
s = s.replace("WorldLabel(np.array([0.0, 0.0, 3.6]),\n                   f\"+{", "WorldLabel(np.array([0.0, 0.0, 5.8]),\n                   f\"+{", 1)
s = s.replace("WorldLabel(np.array([-0.6, 0.0, 2.6]),", "WorldLabel(np.array([-0.6, 0.0, 4.8]),", 1)
s = s.replace("WorldLabel(np.array([1.4, 0.4, 2.1]),", "WorldLabel(np.array([1.4, 0.4, 3.6]),", 1)
s = s.replace("WorldLabel(np.array([-2.4, -1.6, 1.0]),", "WorldLabel(np.array([-2.4, -1.6, 1.6]),", 1)
s = s.replace("WorldLabel(np.array([1.9, 0.0, 2.9]),", "WorldLabel(np.array([1.9, 0.0, 5.0]),", 1)
s = s.replace("WorldLabel(np.array([0.0, 0.0, 3.1]),\n                   f\"TWO-PERSON",
              "WorldLabel(np.array([0.0, 0.0, 5.4]),\n                   f\"TWO-PERSON", 1)
s = s.replace("WorldLabel(np.array([0.0, 0.0, 3.6]),\n                   f\"W = m g h",
              "WorldLabel(np.array([0.0, 0.0, 5.6]),\n                   f\"W = m g h", 1)

# 5. Cameras have to back off by the same factor for figure-led scenes.
DISTANCES = {
    "line_station": 17.0, "line_cycle": 23.0, "line_walk": 18.0,
    "line_lift": 11.5, "line_carry": 20.0, "line_position": 15.0,
    "line_fasten": 15.0, "line_allowance": 14.0, "line_skeleton": 10.5,
    "line_selflift": 14.0, "line_limbs": 14.0, "line_team": 15.0,
    "line_overhead": 16.0, "line_work": 13.5, "line_shift": 14.0,
    "line_food": 18.0,
}
for stage, distance in DISTANCES.items():
    pattern = re.compile(
        r"\((-?[\d.]+), (-?[\d.]+), -?[\d.]+\), \"" + re.escape(stage) + r"\","
    )
    s, count = pattern.subn(
        lambda m: f'({m.group(1)}, {m.group(2)}, {distance}), "{stage}",', s, count=1)
    if count != 1:
        raise SystemExit(f"camera for {stage} not found")

p.write_text(s, encoding="utf-8")
print("figure scale, reading order, labels and cameras updated")
