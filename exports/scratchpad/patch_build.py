"""Rebuild the two construction scenes that did not read, and spread labels."""

from pathlib import Path

path = Path(r"C:\Users\Don\Desktop\DomeSim\two_v_demo\lesson_build.py")
src = path.read_text(encoding="utf-8")


def cut(start: str, end: str) -> str:
    """Return the text between two markers, exclusive of *end*."""
    a = src.index(start)
    b = src.index(end)
    return src[a:b]


def swap(start: str, end: str, new: str) -> None:
    global src
    a = src.index(start)
    b = src.index(end)
    src = src[:a] + new + src[b:]


# ----------------------------------------------------------------------
# Chapter 15: draw the whole teaching circle, centred, face-on
# ----------------------------------------------------------------------
swap(
    "def scene_build_endcut(",
    "def scene_build_bevel(",
    '''def scene_build_endcut(app, opaque, transparent, p: float) -> None:
    """The end-cut angle, drawn as the angle between a chord and its tangent."""
    detail = strut_details()[1]
    theta = math.radians(detail.central_angle_deg)
    centre = np.array([0.0, 0.0, 3.1])
    radius = 3.5
    unit_x = np.array([1.0, 0.0, 0.0])
    unit_z = np.array([0.0, 0.0, 1.0])

    def on_circle(angle: float) -> np.ndarray:
        return centre + radius * (unit_x * math.cos(angle) + unit_z * math.sin(angle))

    # The sphere's great circle, faint, so the chord has something to cut.
    for step in range(96):
        opaque.cylinder(on_circle(math.tau * step / 96),
                        on_circle(math.tau * (step + 1) / 96),
                        0.022, (0.30, 0.40, 0.50, 1.0), 5)

    high = math.pi * 0.5 + theta * 0.5
    low = math.pi * 0.5 - theta * 0.5
    a, b = on_circle(high), on_circle(low)
    opaque.cylinder(centre, a, 0.035, MUTED, 6)
    opaque.cylinder(centre, b, 0.035, MUTED, 6)
    opaque.cylinder(a, b, 0.12, CYAN, 12)
    opaque.sphere(centre, 0.13, WHITE, 5, 9)
    opaque.sphere(a, 0.12, CYAN, 5, 9)
    opaque.sphere(b, 0.12, CYAN, 5, 9)

    # The central angle, arced at the centre.
    for step in range(20):
        first = low + (high - low) * step / 20
        second = low + (high - low) * (step + 1) / 20
        opaque.cylinder(
            centre + 1.15 * (unit_x * math.cos(first) + unit_z * math.sin(first)),
            centre + 1.15 * (unit_x * math.cos(second) + unit_z * math.sin(second)),
            0.030, PURPLE, 6,
        )

    # The tangent at b, and the angle the chord leaves it at.
    tangent = normalize(unit_x * -math.sin(low) + unit_z * math.cos(low))
    opaque.cylinder(b - tangent * 2.5, b + tangent * 2.5, 0.045, GREEN, 8)
    chord = normalize(a - b)
    reveal = ease_in_out(clamp((p - 0.12) / 0.7))
    for step in range(18):
        def between(value: float) -> np.ndarray:
            mix = normalize(tangent * (1.0 - value) + chord * value)
            return b + mix * 1.1

        first = (step / 18) * reveal
        second = ((step + 1) / 18) * reveal
        opaque.cylinder(between(first), between(second), 0.030, AMBER, 6)

    app.world_labels.extend([
        WorldLabel(centre + unit_z * 1.55,
                   f"central angle\\n{detail.central_angle_deg:.4f} deg",
                   (168, 122, 255)),
        WorldLabel((a + b) * 0.5 + unit_z * 0.55,
                   f"{detail.name} chord", (61, 211, 255)),
        WorldLabel(b + tangent * 2.9,
                   "tangent: the surface here", (111, 235, 155)),
        WorldLabel(b + normalize(tangent + chord) * 2.0,
                   f"END CUT {detail.axial_angle_deg:.4f} deg", (255, 177, 62)),
        WorldLabel(centre - unit_z * 1.9,
                   "end cut = half the central angle, every time",
                   (169, 188, 203)),
    ])


''',
)

# ----------------------------------------------------------------------
# Chapter 18: lay both classes into both stock lengths, properly
# ----------------------------------------------------------------------
swap(
    "def scene_build_stock(",
    "def scene_build_jig(",
    '''def scene_build_stock(app, opaque, transparent, p: float) -> None:
    """Nesting: both strut classes, laid into two different stock lengths."""
    reveal = smoothstep(min(1.0, p * 1.25))
    bar_width = 12.0
    colour_of = {"SHORT": CYAN, "LONG": AMBER}
    row = 0
    rows = []
    for stock in (STOCK_LONG_IN, STOCK_SHORT_IN):
        for run in stock_plan(RADIUS_IN, stock, DEDUCTION_IN):
            rows.append((stock, run))
    for index, (stock, run) in enumerate(rows):
        height = 5.4 - index * 1.45
        left = -bar_width * 0.5
        opaque.box((0.0, 0.0, height), (bar_width, 0.9, 0.22),
                   (0.11, 0.16, 0.21, 1.0))
        piece = run.cut_length / stock * bar_width
        kerf = 0.125 / stock * bar_width
        if (index + 1) / len(rows) > reveal + 0.05:
            continue
        for slot in range(run.per_stick):
            start = left + slot * (piece + kerf)
            opaque.box((start + piece * 0.5, 0.0, height + 0.30),
                       (piece * 0.97, 0.8, 0.36), colour_of[run.strut_class])
        used = run.per_stick * (piece + kerf) - kerf
        waste = bar_width - used
        if waste > 0.05:
            opaque.box((left + used + waste * 0.5, 0.0, height + 0.30),
                       (waste * 0.97, 0.8, 0.36), (0.42, 0.14, 0.16, 1.0))
        app.world_labels.append(WorldLabel(
            np.array([-bar_width * 0.5 - 3.3, 0.0, height + 0.3]),
            f"{stock:.0f} in stock, {run.strut_class}\\n"
            f"{run.per_stick} per stick x {run.sticks} sticks\\n"
            f"offcut {run.offcut_per_stick:.1f} in each",
            _rgb(colour_of[run.strut_class]),
        ))
    total_short = sum(
        run.sticks for run in stock_plan(RADIUS_IN, STOCK_SHORT_IN, DEDUCTION_IN)
    )
    total_long = sum(
        run.sticks for run in stock_plan(RADIUS_IN, STOCK_LONG_IN, DEDUCTION_IN)
    )
    app.world_labels.append(WorldLabel(
        np.array([0.0, 0.0, -0.55]),
        f"{STOCK_LONG_IN:.0f} in stock: {total_long} sticks     "
        f"{STOCK_SHORT_IN:.0f} in stock: {total_short} sticks",
        (111, 235, 155),
    ))


''',
)

# ----------------------------------------------------------------------
# Chapter 11: spread the ring captions round the dome instead of stacking
# ----------------------------------------------------------------------
old = '''        app.world_labels.append(WorldLabel(
            np.array([-radius - 1.5, 0.0, height]),
            f"{ring.name.upper()}\\n{ring.hub_count} hubs\\n"
            f"height {ring.height(RADIUS_IN):.1f} in\\n"
            f"across {ring.diameter(RADIUS_IN):.1f} in",
            _rgb(colour),
        ))'''
new = '''        # Fan the captions round the dome so they do not stack on screen.
        bearing = math.radians(196.0 + ring.index * 26.0)
        anchor = np.array([
            (radius + 1.9) * math.cos(bearing),
            (radius + 1.9) * math.sin(bearing),
            height,
        ])
        app.world_labels.append(WorldLabel(
            anchor,
            f"{ring.name.upper()}\\n{ring.hub_count} hubs\\n"
            f"height {ring.height(RADIUS_IN):.1f} in\\n"
            f"across {ring.diameter(RADIUS_IN):.1f} in",
            _rgb(colour),
        ))'''
assert old in src
src = src.replace(old, new, 1)

# Chapter 17's hub legend was fine but sat over the model at this yaw.
old = '''        app.world_labels.append(WorldLabel(
            np.array([-6.6, 0.0, 5.6 - order * 1.05]),'''
new = '''        app.world_labels.append(WorldLabel(
            np.array([-7.4, 0.0, 6.2 - order * 1.05]),'''
assert old in src
src = src.replace(old, new, 1)

path.write_text(src, encoding="utf-8")
print("lesson_build.py scenes rebuilt")
