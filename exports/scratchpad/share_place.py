"""Move the figure-placement helper into figure.py so lessons can share it."""

from pathlib import Path

NL = chr(10)


def sub(path: Path, old: str, new: str) -> None:
    s = path.read_text(encoding="utf-8")
    if old not in s:
        raise SystemExit(f"pattern not found in {path.name}: {old[:200]}")
    path.write_text(s.replace(old, new, 1), encoding="utf-8")


figure = Path(r"C:\Users\Don\Desktop\DomeSim\two_v_demo\figure.py")
sub(
    figure,
    "def draw_figure(",
    "def place_figure(" + NL
    + "    joints: Mapping[str, np.ndarray]," + NL
    + "    origin," + NL
    + "    yaw_deg: float = 0.0," + NL
    + ") -> dict[str, np.ndarray]:" + NL
    + '    """Move a posed figure to a spot on the floor, facing a direction.' + NL
    + NL
    + "    The pose functions all build a figure standing at the origin facing" + NL
    + "    +X, because a pose is about the body and not about where the body" + NL
    + "    is. This is what puts it somewhere." + NL
    + '    """' + NL
    + "    angle = math.radians(yaw_deg)" + NL
    + "    cos_a, sin_a = math.cos(angle), math.sin(angle)" + NL
    + "    origin = np.asarray(origin, dtype=np.float64)" + NL
    + "    placed: dict[str, np.ndarray] = {}" + NL
    + "    for name, point in joints.items():" + NL
    + "        x, y, z = float(point[0]), float(point[1]), float(point[2])" + NL
    + "        placed[name] = origin + np.array(" + NL
    + "            [x * cos_a - y * sin_a, x * sin_a + y * cos_a, z]" + NL
    + "        )" + NL
    + "    return placed" + NL
    + NL + NL
    + "def draw_figure(",
)

# The line lesson keeps its own short name, now backed by the shared one.
line = Path(r"C:\Users\Don\Desktop\DomeSim\two_v_demo\lesson_line.py")
sub(
    line,
    "def _place(joints, origin, yaw_deg: float = 0.0) -> dict:" + NL
    + '    """Move a figure' + chr(39) + "s joints to a spot on the floor, "
    + 'facing a direction."""' + NL
    + "    angle = math.radians(yaw_deg)" + NL
    + "    cos_a, sin_a = math.cos(angle), math.sin(angle)" + NL
    + "    origin = np.asarray(origin, dtype=np.float64)" + NL
    + "    placed = {}" + NL
    + "    for name, point in joints.items():" + NL
    + "        x, y, z = float(point[0]), float(point[1]), float(point[2])" + NL
    + "        placed[name] = origin + np.array(" + NL
    + "            [x * cos_a - y * sin_a, x * sin_a + y * cos_a, z]" + NL
    + "        )" + NL
    + "    return placed",
    "_place = place_figure",
)

s = line.read_text(encoding="utf-8")
if "place_figure" not in s.split("_place = place_figure")[0]:
    s = s.replace("from .figure import (", "from .figure import (" + NL
                  + "    place_figure,", 1)
    line.write_text(s, encoding="utf-8")

# And the added build sections use it directly.
extra = Path(r"C:\Users\Don\Desktop\DomeSim\two_v_demo\lesson_build_extra.py")
sub(
    extra,
    "from .figure import POSES, draw_figure, joint_positions",
    "from .figure import POSES, draw_figure, joint_positions, place_figure",
)
sub(
    extra,
    '    joints = joint_positions(POSES["kneel"], 1.75)' + NL
    + "    draw_figure(opaque, joints, np.array([0.0, 0.0, 0.0]), scale=0.95, yaw=150.0)",
    '    joints = place_figure(' + NL
    + '        joint_positions(POSES["kneel"], 1.75), (0.0, 0.0, 0.0), 150.0)' + NL
    + "    draw_figure(opaque, joints, scale=0.95)",
)
sub(
    extra,
    "    person_scale = view * 1.75 * 39.3701" + NL
    + '    joints = joint_positions(POSES["kneel"], 1.75)' + NL
    + "    draw_figure(opaque, joints, np.array([0.0, 0.0, 0.0])," + NL
    + "                scale=person_scale, yaw=200.0)",
    "    # The figure is drawn at the shelter's own scale, which is the whole" + NL
    + "    # point of the shot: the dome is small, not the person." + NL
    + "    person_scale = view * 39.3701" + NL
    + "    joints = place_figure(" + NL
    + '        joint_positions(POSES["kneel"], 1.75 * person_scale),' + NL
    + "        (0.0, 0.0, 0.0), 200.0)" + NL
    + "    draw_figure(opaque, joints, scale=person_scale)",
)

print("place_figure shared; both lessons updated")
