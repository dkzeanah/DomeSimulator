"""Stop figures hiding behind each other and behind the charts.

The camera for this lesson sits on the +Y axis, so anything separated
along Y is separated in *depth* rather than across the frame, and the
nearer object simply covers the further one.  Every crew pair and every
figure-plus-chart arrangement has to be laid out along X instead.
"""

from pathlib import Path

p = Path(r"C:\Users\Don\Desktop\DomeSim\two_v_demo\lesson_line.py")
s = p.read_text(encoding="utf-8")


def sub(old: str, new: str) -> None:
    global s
    if old not in s:
        raise SystemExit("pattern not found: " + old[:220])
    s = s.replace(old, new, 1)


# --- chapter 03: the station -------------------------------------------
sub(
    '''    _floor(opaque, (0.0, 0.0, 0.0), (7.0, 6.0))
    _stockpile(opaque, (-2.4, -1.6, 0.0))
    _dome_hull(transparent, np.array([1.4, 0.4, 0.0]), 1.6, 0.55)
    index, motion, local = _motion_at(p)
    pose = _pose_for(motion, local)
    _worker(opaque, np.array([-0.6, -1.5, 0.0]), pose,
            load=_load_dims(DEMO_ELEMENT.dims) if motion.load_kg > 0 else None)
    _worker(opaque, np.array([-0.6, 1.5, 0.0]), POSES["reach_out"], yaw=-25.0)
    app.world_labels.extend([
        WorldLabel(np.array([-2.4, -1.6, 1.6]), "STOCKPILE", (169, 188, 203)),
        WorldLabel(np.array([1.4, 0.4, 3.6]), "THE DOME", (61, 211, 255)),
        WorldLabel(np.array([-0.6, 0.0, 4.8]),
                   f"CREW OF {CREW}", (111, 235, 155)),
    ])''',
    '''    _floor(opaque, (0.0, 0.0, 0.0), (14.0, 6.0))
    _stockpile(opaque, (5.2, 0.0, 0.0))
    _dome_hull(transparent, np.array([-4.4, 0.0, 0.0]), 2.6, 0.55)
    index, motion, local = _motion_at(p)
    pose = _pose_for(motion, local)
    # Both workers along X: separating them in Y would only stack them in
    # depth from this lesson's camera.
    _worker(opaque, np.array([1.5, 0.0, 0.0]), pose,
            load=_load_dims(DEMO_ELEMENT.dims) if motion.load_kg > 0 else None)
    _worker(opaque, np.array([-1.4, 0.0, 0.0]), POSES["reach_out"], yaw=180.0)
    app.world_labels.extend([
        WorldLabel(np.array([5.2, 0.0, 2.2]), "STOCKPILE", (169, 188, 203)),
        WorldLabel(np.array([-4.4, 0.0, 3.4]), "THE DOME", (61, 211, 255)),
        WorldLabel(np.array([0.0, 0.0, 5.4]),
                   f"CREW OF {CREW}", (111, 235, 155)),
    ])''',
)

# --- chapter 08: carrying, with the bars beside the walker --------------
sub(
    '''    _floor(opaque, (0.0, -2.6, 0.0), (12.0, 2.6))
    travel = ease_in_out(clamp(p * 1.15))
    x = -3.8 + travel * 7.6
    _worker(opaque, np.array([x, -2.6, 0.0]),
            _pose_for(DEMO_MOTIONS[2], p * 3.0), load=_load_dims(DEMO_ELEMENT.dims))''',
    '''    _floor(opaque, (6.4, 0.0, 0.0), (7.0, 3.0))
    travel = ease_in_out(clamp(p * 1.15))
    x = 4.2 + travel * 4.4
    _worker(opaque, np.array([x, 0.0, 0.0]),
            _pose_for(DEMO_MOTIONS[2], p * 3.0), load=_load_dims(DEMO_ELEMENT.dims))''',
)
sub(
    '''    ), origin=(0.0, 1.6, 0.0), height=3.6, reveal=smoothstep(p * 1.3),
        width=0.62, gap=0.5)
    app.world_labels.append(WorldLabel(
        np.array([0.0, 1.6, 4.6]),
        "PANDOLF: THE LOAD TERM IS QUADRATIC", (111, 235, 155)))''',
    '''    ), origin=(-2.6, 0.0, 0.0), height=3.6, reveal=smoothstep(p * 1.3),
        width=0.72, gap=0.62)
    app.world_labels.append(WorldLabel(
        np.array([-2.6, 0.0, 5.2]),
        "PANDOLF: THE LOAD TERM IS QUADRATIC", (111, 235, 155)))''',
)

# --- chapters 01 and 24: the whole line ---------------------------------
# Fifteen pads at 1.72 apart ran past the edge of frame, and putting the
# crew on the pad the dome occupies buried both.
sub(
    "    spacing = 1.72",
    "    spacing = 1.46",
)
sub(
    '''    for side in (-1, 1):
        _worker(opaque, np.array([positions[index] + 1.05, side * 0.95, 0.12]),
                POSES["fasten"] if side < 0 else POSES["reach_out"],
                yaw=180.0 if side > 0 else 0.0)
    app.world_labels.extend([
        WorldLabel(np.array([0.0, 0.0, 4.3]),''',
    '''    for offset, pose in ((-1.5, POSES["fasten"]), (1.5, POSES["reach_out"])):
        _worker(opaque, np.array([positions[index] + offset, 1.9, 0.12]),
                pose, yaw=180.0 if offset > 0 else 0.0)
    app.world_labels.extend([
        WorldLabel(np.array([0.0, 0.0, 5.6]),''',
)
sub(
    '''        WorldLabel(np.array([0.0, 0.0, 3.5]),
                   f"{SPEC.name}  -  {SPEC.radius:.2f} m radius, {SPEC.frequency}V",
                   (169, 188, 203)),''',
    '''        WorldLabel(np.array([0.0, 0.0, 4.6]),
                   f"{SPEC.name}  -  {SPEC.radius:.2f} m radius, {SPEC.frequency}V",
                   (169, 188, 203)),''',
)
sub(
    '''    for side in (-1, 1):
        _worker(opaque, np.array([positions[index] + 1.05, side * 0.95, 0.12]),
                POSES["reach_out"], yaw=180.0 if side > 0 else 0.0)
    app.world_labels.extend([
        WorldLabel(np.array([0.0, 0.0, 4.4]),
                   f"{len(CATALOG.elements)} PARTS   "
                   f"{ENERGY.hours_per_worker:.0f} h   "
                   f"{ENERGY.kcal_crew:,.0f} kcal", (61, 211, 255)),
        WorldLabel(np.array([0.0, 0.0, 3.6]),''',
    '''    for offset in (-1.5, 1.5):
        _worker(opaque, np.array([positions[index] + offset, 1.9, 0.12]),
                POSES["reach_out"], yaw=180.0 if offset > 0 else 0.0)
    app.world_labels.extend([
        WorldLabel(np.array([0.0, 0.0, 5.8]),
                   f"{len(CATALOG.elements)} PARTS   "
                   f"{ENERGY.hours_per_worker:.0f} h   "
                   f"{ENERGY.kcal_crew:,.0f} kcal", (61, 211, 255)),
        WorldLabel(np.array([0.0, 0.0, 4.7]),''',
)

p.write_text(s, encoding="utf-8")
print("station, carry and line-overview layouts fixed")
