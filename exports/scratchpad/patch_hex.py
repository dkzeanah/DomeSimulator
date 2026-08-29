"""Re-scale and re-frame the hex lesson after looking at every still."""

from pathlib import Path

path = Path(r"C:\Users\Don\Desktop\DomeSim\two_v_demo\lesson_hex.py")
src = path.read_text(encoding="utf-8")


def sub(old: str, new: str) -> None:
    global src
    if old not in src:
        raise SystemExit("pattern not found:\n" + old[:300])
    src = src.replace(old, new, 1)


# --- 02: reach all three hexagons, and show the shared corner clearly ----
sub("""    shown = 1 + int(smoothstep(min(1.0, p * 1.5)) * 2.0 + 1e-6)""",
    """    shown = 1 + int(round(smoothstep(min(1.0, p * 1.7)) * 2.0))""")

# --- 03: a flat disc beside the same disc folded into a cone ------------
sub('''def scene_hex_deficit(app, opaque, transparent, p: float) -> None:
    """Cut a wedge out of a flat disc and watch it become a cone."""
    fold = ease_in_out(clamp((p - 0.10) / 0.72))
    missing = math.radians(60.0) * fold
    span = math.tau - missing
    apex = np.array([0.0, 0.0, 1.0])
    radius = 3.6
    # Rolling a disc into a cone keeps arc length, so the height follows.
    cone_radius = radius * span / math.tau
    height = math.sqrt(max(0.0, radius**2 - cone_radius**2))
    top = apex + np.array([0.0, 0.0, height])
    segments = 40
    for index in range(segments):
        angle_a = span * index / segments
        angle_b = span * (index + 1) / segments
        a = apex + np.array([cone_radius * math.cos(angle_a),
                             cone_radius * math.sin(angle_a), 0.0])
        b = apex + np.array([cone_radius * math.cos(angle_b),
                             cone_radius * math.sin(angle_b), 0.0])
        transparent.triangle(top, a, b, (0.15, 0.82, 1.00, 0.20),
                             normalize(np.cross(a - top, b - top)))
        opaque.cylinder(a, b, 0.035, CYAN, 6)
    for angle in (0.0, span):
        edge = apex + np.array([cone_radius * math.cos(angle),
                                cone_radius * math.sin(angle), 0.0])
        opaque.cylinder(top, edge, 0.055, AMBER, 8)
    app.world_labels.extend([
        WorldLabel(top + np.array([0.0, 0.0, 0.6]),
                   f"{math.degrees(missing):.1f} deg REMOVED", (255, 177, 62)),
        WorldLabel(apex + np.array([0.0, -radius - 0.9, 0.0]),
                   "TAKE ANGLE OUT -> THE SHEET DOMES", (111, 235, 155)),
    ])''',
    '''def scene_hex_deficit(app, opaque, transparent, p: float) -> None:
    """The same disc twice: left stays flat, right loses a wedge and rises."""
    radius = 2.9
    fold = ease_in_out(clamp((p - 0.10) / 0.72))
    missing = math.radians(90.0) * fold
    segments = 44

    def disc(centre, span, tint):
        # Rolling a disc into a cone preserves arc length, so the height
        # of the cone follows from the wedge that was taken out.
        cone_radius = radius * span / math.tau
        height = math.sqrt(max(0.0, radius**2 - cone_radius**2))
        top = centre + np.array([0.0, 0.0, height])
        for index in range(segments):
            angle_a = span * index / segments
            angle_b = span * (index + 1) / segments
            a = centre + np.array([cone_radius * math.cos(angle_a),
                                   cone_radius * math.sin(angle_a), 0.0])
            b = centre + np.array([cone_radius * math.cos(angle_b),
                                   cone_radius * math.sin(angle_b), 0.0])
            transparent.triangle(top, a, b, (tint[0], tint[1], tint[2], 0.22),
                                 normalize(np.cross(a - top, b - top)))
            opaque.cylinder(a, b, 0.045, tint, 7)
            opaque.cylinder(top, a, 0.018, (tint[0], tint[1], tint[2], 0.55), 5)
        for angle in (0.0, span):
            edge = centre + np.array([cone_radius * math.cos(angle),
                                      cone_radius * math.sin(angle), 0.0])
            opaque.cylinder(top, edge, 0.065, AMBER, 8)
        return top, height

    left = np.array([-3.6, 0.0, 0.8])
    right = np.array([3.6, 0.0, 0.8])
    disc(left, math.tau, CYAN)
    _, height = disc(right, math.tau - missing, GREEN)
    app.world_labels.extend([
        WorldLabel(left + np.array([0.0, 0.0, -0.9]),
                   "FULL TURN OF PAPER\\n360 deg -> stays flat", (61, 211, 255)),
        WorldLabel(right + np.array([0.0, 0.0, -0.9]),
                   f"WEDGE REMOVED\\n{360.0 - math.degrees(missing):.1f} deg -> rises "
                   f"{height:.2f}", (111, 235, 155)),
        WorldLabel(np.array([0.0, 0.0, 4.4]),
                   "NOTHING STRETCHED. ONLY ANGLE WAS REMOVED.",
                   (255, 177, 62)),
    ])''')

# --- 07: put the strut rack in front of the cage, not off to one side ---
sub('''    reveal = int(count * smoothstep(clamp((p - 0.15) / 0.8)))
    length = 1.9
    for index in range(reveal):
        column, row = index % 11, index // 11
        x = -9.8 + column * 0.30
        y = 4.6 - row * 0.62
        opaque.cylinder(np.array([x, y, 0.35]),
                        np.array([x, y, 0.35 + length]), 0.048, CYAN, 6)
    app.world_labels.extend([
        WorldLabel(np.array([-8.2, 4.6, 2.9]),
                   f"{reveal:02d} / {count} STRUTS CUT", (61, 211, 255)),
        WorldLabel(np.array([-8.2, -1.6, 0.9]),
                   f"every one {centre_length:.3f} in centre to centre\\n"
                   f"cut {cut_length:.3f} in after hub deduction",
                   (169, 188, 203)),
    ])''',
    '''    reveal = int(count * smoothstep(clamp((p - 0.15) / 0.8)))
    length = 1.7
    for index in range(reveal):
        column, row = index % 30, index // 30
        x = -6.9 + column * 0.475
        y = -6.4 - row * 0.85
        opaque.cylinder(np.array([x, y, 0.30]),
                        np.array([x, y, 0.30 + length]), 0.055, CYAN, 6)
    app.world_labels.extend([
        WorldLabel(np.array([0.0, -6.4, 2.6]),
                   f"{reveal:02d} / {count} STRUTS CUT -- ONE SAW SETTING",
                   (61, 211, 255)),
        WorldLabel(np.array([0.0, -8.1, 0.55]),
                   f"centre to centre {centre_length:.3f} in\\n"
                   f"cut {cut_length:.3f} in after hub deduction",
                   (169, 188, 203)),
    ])''')

# --- 08 / 13 / 15: the flat templates were drawn many times too large ---
sub('''    positions = np.linspace(-4.4, 4.4, len(order))''',
    '''    positions = np.linspace(-3.3, 3.3, len(order))''')
sub('''        draw_flat_panel(
            app, opaque, transparent, SOCCER, face_index,
            np.array([float(x), 0.0, 3.4]), 13.0, colour,''',
    '''        draw_flat_panel(
            app, opaque, transparent, SOCCER, face_index,
            np.array([float(x), 0.0, 2.7]), 4.4, colour,''')
sub('''    app.world_labels.append(WorldLabel(
        np.array([0.0, 0.0, 7.1]),
        "TWO TEMPLATES CUT THE WHOLE SKIN", (111, 235, 155),
    ))''',
    '''    app.world_labels.append(WorldLabel(
        np.array([0.0, 0.0, 5.1]),
        "TWO TEMPLATES CUT THE WHOLE SKIN", (111, 235, 155),
    ))''')

sub('''    draw_flat_panel(app, opaque, transparent, GP2, face_index,
                    np.array([-3.9, 0.0, 3.6]), 15.0, CYAN)
    soccer_face = SOCCER.face_class_of.index("HEX")
    draw_flat_panel(app, opaque, transparent, SOCCER, soccer_face,
                    np.array([4.1, 0.0, 3.6]), 15.0, AMBER)''',
    '''    draw_flat_panel(app, opaque, transparent, GP2, face_index,
                    np.array([-3.3, 0.0, 3.0]), 5.4, CYAN)
    soccer_face = SOCCER.face_class_of.index("HEX")
    draw_flat_panel(app, opaque, transparent, SOCCER, soccer_face,
                    np.array([3.3, 0.0, 3.0]), 5.4, AMBER)''')
sub('''        WorldLabel(np.array([-3.9, 0.0, 0.7]),''',
    '''        WorldLabel(np.array([-3.3, 0.0, 0.4]),''')
sub('''        WorldLabel(np.array([4.1, 0.0, 0.7]),''',
    '''        WorldLabel(np.array([3.3, 0.0, 0.4]),''')
sub('''        WorldLabel(np.array([0.0, 0.0, 7.0]),
                   "RAISING THE FREQUENCY BREAKS THE REGULAR HEXAGON",''',
    '''        WorldLabel(np.array([0.0, 0.0, 5.6]),
                   "RAISING THE FREQUENCY BREAKS THE REGULAR HEXAGON",''')

sub('''    exaggeration = 26.0 * ease_in_out(clamp((p - 0.12) / 0.7))
    scale = 34.0
    base = np.array([0.0, 0.0, 3.2])''',
    '''    exaggeration = 26.0 * ease_in_out(clamp((p - 0.12) / 0.7))
    scale = 13.0
    base = np.array([0.0, 0.0, 2.9])''')
sub('''        WorldLabel(base + np.array([0.0, 0.0, 3.0]),''',
    '''        WorldLabel(base + np.array([0.0, 0.0, 2.3]),''')
sub('''        WorldLabel(base + np.array([0.0, 0.0, -3.1]),''',
    '''        WorldLabel(base + np.array([0.0, 0.0, -2.4]),''')

# --- 09: keep the level-course caption out from behind the dome --------
sub('''        WorldLabel(np.array([0.0, 0.0, low - 0.9]),
                   "LEVEL COURSE MAKES UP THE DIFFERENCE", (111, 235, 155)),''',
    '''        WorldLabel(np.array([0.0, -7.4, low + 0.2]),
                   "LEVEL COURSE MAKES UP THE DIFFERENCE", (111, 235, 155)),''')

# --- 16: a flat cage still needs a visible bar, labelled as flat -------
sub('''    entries = []
    for cage, notation in ((SOCCER, "GP(1,1)"), (GP2, "GP(2,0)"),
                           (GP3, "GP(3,0)"), (GP4, "GP(4,0)")):
        warp = cage.worst_planarity * LESSON_RADIUS_IN
        entries.append((f"{notation}\\n{warp:.4f} in", warp, CYAN if warp < 1e-6 else AMBER))
    bar_row(opaque, app, entries, np.array([-6.0, 0.0, 0.35]), 4.0, 5.2)''',
    '''    entries = []
    for cage, notation in ((SOCCER, "GP(1,1)"), (GP2, "GP(2,0)"),
                           (GP3, "GP(3,0)"), (GP4, "GP(4,0)")):
        warp = cage.worst_planarity * LESSON_RADIUS_IN
        flat = warp < 1e-9
        entries.append((
            f"{notation}\\n{warp:.4f} in" + ("\\nFLAT" if flat else ""),
            max(warp, 0.02), GREEN if flat else AMBER,
        ))
    bar_row(opaque, app, entries, np.array([-6.0, 0.0, 0.35]), 4.0, 8.0)''')

# --- cameras, re-aimed after looking at every frame --------------------
CAMERAS = {
    '"hex_flat",': "(90.0, 64.0, 17.0)",
    '"hex_flat_angle",': "(90.0, 56.0, 15.5)",
    '"hex_deficit",': "(90.0, 20.0, 15.0)",
    '"hex_pentagon_swap",': "(90.0, 38.0, 16.0)",
    '"hex_euler",': "(90.0, 20.0, 21.0)",
    '"hex_soccer_struts",': "(90.0, 26.0, 17.5)",
    '"hex_soccer_panels",': "(-90.0, 14.0, 12.0)",
    '"hex_two_struts",': "(-90.0, 14.0, 13.0)",
    '"hex_size_ladder",': "(90.0, 18.0, 20.0)",
    '"hex_warp",': "(-72.0, 22.0, 12.5)",
    '"hex_warp_cost",': "(90.0, 20.0, 19.0)",
    '"hex_choose",': "(90.0, 20.0, 20.0)",
    '"hex_compare",': "(90.0, 22.0, 18.0)",
}
for stage, camera in CAMERAS.items():
    marker = ", " + stage
    index = src.index(marker)
    line_start = src.rindex("\n", 0, index) + 1
    line = src[line_start:index]
    # The chapter tuple line looks like:  13.0, (30.0, 46.0, 15.0)
    before, _, _ = line.partition(", (")
    src = src[:line_start] + before + ", " + camera + src[index:]

path.write_text(src, encoding="utf-8")
print("lesson_hex.py re-framed")
