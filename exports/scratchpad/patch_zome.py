"""Framing pass on the zome lesson, plus one real bug in the ring drawing."""

from pathlib import Path

path = Path(r"C:\Users\Don\Desktop\DomeSim\two_v_demo\lesson_zome.py")
src = path.read_text(encoding="utf-8")


def sub(old: str, new: str) -> None:
    global src
    if old not in src:
        raise SystemExit("pattern not found:\n" + old[:300])
    src = src.replace(old, new, 1)


# A roof-only view has to stand on its rim, not on the buried bottom point.
sub('''def ground_offset(zome: Zome, x: float = 0.0, y: float = 0.0) -> np.ndarray:
    """Stand a zome on the grid instead of letting it sink through it."""
    return np.array([x, y, -float(zome.vertices[:, 2].min()) + 0.15])''',
    '''def ground_offset(zome: Zome, x: float = 0.0, y: float = 0.0) -> np.ndarray:
    """Stand a zome on the grid instead of letting it sink through it."""
    return np.array([x, y, -float(zome.vertices[:, 2].min()) + 0.15])


def roof_offset(zome: Zome, x: float = 0.0, y: float = 0.0,
                scale: float = 1.0) -> np.ndarray:
    """Stand only the roof half on the grid, resting on its own rim."""
    return np.array([x, y, -zome.rim_height * scale + 0.15])


def level_ring(
    opaque: TriangleBatch,
    centre: np.ndarray,
    radius: float,
    height: float,
    colour,
    *,
    segments: int = 48,
    thickness: float = 0.022,
) -> None:
    """A horizontal circle drawn around a model's own axis, not the origin."""
    for step in range(segments):
        angle_a = math.tau * step / segments
        angle_b = math.tau * (step + 1) / segments
        a = np.array([centre[0] + radius * math.cos(angle_a),
                      centre[1] + radius * math.sin(angle_a), height])
        b = np.array([centre[0] + radius * math.cos(angle_b),
                      centre[1] + radius * math.sin(angle_b), height])
        opaque.cylinder(a, b, thickness, colour, 5)''')

# 01 -- keep the apex caption out of the header bar
sub('''    app.world_labels.extend([
        WorldLabel(apex + np.array([0.0, 0.0, 0.75]), "ONE POINT", (111, 235, 155)),''',
    '''    app.world_labels.extend([
        WorldLabel(apex + np.array([-1.7, 0.0, -0.35]), "ONE POINT", (111, 235, 155)),''')

# 02 -- the sweep was small and floating
sub("    origin = np.array([-2.6, 0.0, GROUND_LIFT])",
    "    origin = np.array([-3.0, 0.0, 2.9])")
sub('''    draw_solid(app, opaque, transparent, base_vertices, base_edges, base_faces,
               origin, CYAN, alpha=0.16, strut_radius=0.055, node_radius=0.07)
    if used < len(generators) and fraction > 0.01:
        draw_solid(app, opaque, transparent, base_vertices, base_edges, base_faces,
                   origin + travel, AMBER, alpha=0.10, strut_radius=0.04,
                   node_radius=0.05)
        for index in range(len(base_vertices)):
            opaque.cylinder(base_vertices[index] + origin,
                            base_vertices[index] + origin + travel,
                            0.022, (0.55, 0.68, 0.78, 1.0), 5)
    draw_star(app, opaque, generators[:used], origin + np.array([0.0, 0.0, 0.0]),
              GREEN, radius=0.026)''',
    '''    zoom = 1.75
    draw_solid(app, opaque, transparent, base_vertices, base_edges, base_faces,
               origin, CYAN, scale=zoom, alpha=0.16, strut_radius=0.06,
               node_radius=0.08)
    if used < len(generators) and fraction > 0.01:
        draw_solid(app, opaque, transparent, base_vertices, base_edges, base_faces,
                   origin + travel * zoom, AMBER, scale=zoom, alpha=0.10,
                   strut_radius=0.042, node_radius=0.055)
        for index in range(len(base_vertices)):
            start = base_vertices[index] * zoom + origin
            opaque.cylinder(start, start + travel * zoom, 0.024,
                            (0.55, 0.68, 0.78, 1.0), 5)
    draw_star(app, opaque, generators[:used] * zoom, origin, GREEN, radius=0.03)''')
sub('''    app.world_labels.append(WorldLabel(
        origin + np.array([0.0, 0.0, 4.3]), captions[step], (111, 235, 155),
    ))''',
    '''    app.world_labels.append(WorldLabel(
        origin + np.array([0.0, 0.0, 4.6]), captions[step], (111, 235, 155),
    ))''')

# 08 -- rings drawn around the model's own axis
sub('''        radius = max(0.30, max(
            float(np.linalg.norm(ZOME.vertices[corner][:2])) for corner in members
        ))
        height = level + offset[2]
        for step in range(48):
            angle_a = math.tau * step / 48
            angle_b = math.tau * (step + 1) / 48
            a = np.array([radius * math.cos(angle_a), radius * math.sin(angle_a), height])
            b = np.array([radius * math.cos(angle_b), radius * math.sin(angle_b), height])
            opaque.cylinder(a, b, 0.022, (tint[0], tint[1], tint[2], 0.85), 5)''',
    '''        radius = max(0.30, max(
            float(np.linalg.norm(ZOME.vertices[corner][:2])) for corner in members
        ))
        level_ring(opaque, offset, radius, level + offset[2],
                   (tint[0], tint[1], tint[2], 0.85))''')

# 09 -- the three templates were overlapping
sub("    positions = np.linspace(-1.6, 4.4, len(classes))",
    "    positions = np.linspace(-2.6, 6.6, len(classes))")
sub('''            np.array([float(positions[index]), 0.0, 3.0]), 1.5, colour,''',
    '''            np.array([float(positions[index]), 0.0, 3.0]), 1.25, colour,''')
sub('''    app.world_labels.append(WorldLabel(
        np.array([1.4, 0.0, 5.6]),''',
    '''    app.world_labels.append(WorldLabel(
        np.array([2.0, 0.0, 5.9]),''')

# 12 -- the floor scene should also stand on its rim
sub('''def scene_zome_floor(app, opaque, transparent, p: float) -> None:
    """The floor line: no horizontal struts, but one repeated cut."""
    offset = ground_offset(ZOME)''',
    '''def scene_zome_floor(app, opaque, transparent, p: float) -> None:
    """The floor line: no horizontal struts, but one repeated cut."""
    offset = roof_offset(ZOME)''')
sub('''    radius = max(float(np.linalg.norm(ZOME.vertices[index][:2])) for index in rim) + 0.5
    for step in range(52):
        angle_a = math.tau * step / 52
        angle_b = math.tau * (step + 1) / 52
        a = np.array([radius * math.cos(angle_a), radius * math.sin(angle_a),
                      cut_height + offset[2]])
        b = np.array([radius * math.cos(angle_b), radius * math.sin(angle_b),
                      cut_height + offset[2]])
        opaque.cylinder(a, b, 0.05, GREEN, 6)''',
    '''    radius = max(float(np.linalg.norm(ZOME.vertices[index][:2])) for index in rim) + 0.5
    level_ring(opaque, offset, radius, cut_height + offset[2], GREEN,
               segments=52, thickness=0.05)''')

# 13 -- a bigger roof, standing on its rim, with the rack clear of the panels
sub('''    offset = ground_offset(ZOME, -2.2)
    draw_zome(app, opaque, transparent, ZOME, offset, faces=ZOME.dome_faces,
              scale=0.68, alpha=0.14, strut_radius=0.04, node_radius=0.05)''',
    '''    offset = roof_offset(ZOME, -2.6, 0.0, 1.0) + np.array([0.0, 0.0, 1.9])
    draw_zome(app, opaque, transparent, ZOME, offset, faces=ZOME.dome_faces,
              alpha=0.15, strut_radius=0.05, node_radius=0.065)''')
sub('''    for index in range(reveal):
        column, row = index % 15, index // 15
        x = -7.6 + column * 0.62
        y = 4.4 + row * 0.95
        opaque.cylinder(np.array([x, y, 0.20]), np.array([x, y, 1.95]),
                        0.05, CYAN, 6)
    app.world_labels.extend([
        WorldLabel(np.array([-3.2, 4.4, 2.5]),
                   f"{reveal:02d} / {count} STRUTS", (61, 211, 255)),
        WorldLabel(np.array([-3.2, 6.3, 2.5]),
                   f"centre {centre_length:.3f} in\\n"
                   f"cut {cut_length:.3f} in", (169, 188, 203)),
    ])''',
    '''    for index in range(reveal):
        column, row = index % 15, index // 15
        x = -7.4 + column * 0.66
        y = 4.6 + row * 1.0
        opaque.cylinder(np.array([x, y, 0.20]), np.array([x, y, 1.95]),
                        0.05, CYAN, 6)
    app.world_labels.extend([
        WorldLabel(np.array([-2.6, 4.6, 2.55]),
                   f"{reveal:02d} / {count} STRUTS", (61, 211, 255)),
        WorldLabel(np.array([-2.6, 6.6, 2.55]),
                   f"centre {centre_length:.3f} in   "
                   f"cut {cut_length:.3f} in", (169, 188, 203)),
    ])''')

# 14 -- the template was sitting on the model
sub('''    draw_flat_rhombus(app, opaque, transparent, GOLDEN, 0,
                      np.array([-5.6, 0.0, 3.4]), 1.6, AMBER,''',
    '''    draw_flat_rhombus(app, opaque, transparent, GOLDEN, 0,
                      np.array([-6.2, 0.0, 3.6]), 1.35, AMBER,''')

# 15 -- the same ring bug, and the two models were sharing one stack of rings
sub('''        for k, level in enumerate(zome.level_rings):
            height = level * 0.66 + offset[2]
            radius = max(0.3, max(
                float(np.linalg.norm(zome.vertices[corner][:2])) * 0.66
                for corner in range(len(zome.vertices))
                if abs(float(zome.vertices[corner][2]) - level) <= 1e-9
            ))
            tint = CYAN if index else AMBER
            for step in range(40):
                angle_a = math.tau * step / 40
                angle_b = math.tau * (step + 1) / 40
                a = np.array([radius * math.cos(angle_a), radius * math.sin(angle_a), height])
                b = np.array([radius * math.cos(angle_b), radius * math.sin(angle_b), height])
                opaque.cylinder(a, b, 0.02, tint, 5)''',
    '''        for level in zome.level_rings:
            height = level * 0.66 + offset[2]
            radius = max(0.3, max(
                float(np.linalg.norm(zome.vertices[corner][:2])) * 0.66
                for corner in range(len(zome.vertices))
                if abs(float(zome.vertices[corner][2]) - level) <= 1e-9
            ))
            tint = CYAN if index else AMBER
            level_ring(opaque, offset, radius, height, tint,
                       segments=40, thickness=0.02)''')

path.write_text(src, encoding="utf-8")
print("lesson_zome.py framing pass applied")
