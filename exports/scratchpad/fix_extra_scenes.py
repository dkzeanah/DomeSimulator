"""Fix the five faults the first still pass found in the added chapters."""

import re
from pathlib import Path

NL = chr(10)
p = Path(r"C:\Users\Don\Desktop\DomeSim\two_v_demo\lesson_build_extra.py")
s = p.read_text(encoding="utf-8")


def sub(old: str, new: str) -> None:
    global s
    if old not in s:
        raise SystemExit("pattern not found: " + old[:240])
    s = s.replace(old, new, 1)


# --- 1. The equation card was printing each figure twice ---------------
# The renderer concatenates a chapter's fixed equations with these, so
# anything restated here appears on screen twice.  These now carry only
# what the fixed lines do not.
start = s.index("def extra_equations(")
end = len(s)
s = s[:start] + '''def extra_equations(app, stage: str) -> list[str]:
    """Live figures for the added chapters.

    The renderer appends these to the chapter's own fixed equations, so
    anything already stated there is deliberately absent here.
    """
    if stage == "build_hubless_intro":
        return [
            f"panels    = {SUMMARY.triangles} in 2 shapes",
            f"joints    = {SUMMARY.struts * 2} strut ends to cut",
        ]
    if stage == "build_hubless_edge":
        return [
            f"bolts at 2 per edge = {FRANKEN.bolts}",
            f"of those structural  = {FRANKEN.structural_bolts}",
        ]
    if stage in ("build_hubless_cut", "build_hubless_saw"):
        return [
            f"mitre {item.mitre_deg:6.3f}  bevel {item.bevel_deg:5.3f}"
            f"  x{item.count}"
            for item in SETUPS
        ]
    if stage in ("build_air_origin", "build_air_direction"):
        return [
            f"shell    = {AIR.shell_area_m2:.2f} m2",
            f"volume   = {AIR.volume_m3:.2f} m3 = {AIR.volume_cuft:.0f} cu ft",
            f"ring main = {AIR.base_tube_length_in:.0f} in around",
        ]
    if stage in ("build_air_wall", "build_air_caveats"):
        return [
            f"wall per m3 of air = {AIR.area_to_volume:.3f} m2",
        ] + [
            f"{case.air_changes_per_hour:.0f} ACH -> "
            f"{case.face_velocity_fpm:5.2f} ft/min through the wall"
            for case in AIR.cases
        ]
    if stage in ("build_shelter_nest", "build_shelter_size"):
        return [
            f"radius    = {SHELTER.radius:.2f} in",
            f"floor     = {SHELTER.floor_area_sqft:.2f} sq ft",
            f"riser for 6 ft = {SHELTER.riser_for(72.0):.1f} in",
        ]
    if stage in ("build_franken_stock", "build_franken_lumpy"):
        return [
            f"build time = {FRANKEN.build_days} days",
            f"rate       = {FRANKEN.triangles_per_day:.1f} triangles/day",
        ]
    if stage in ("build_franken_ledger", "build_franken_trees"):
        return [
            f"fasteners = {FRANKEN.fasteners:,} in total",
            f"stood     = {FRANKEN.service_ratio:.0f}x its build time",
        ]
    return []
'''

# --- 2. The protractor was small, skewed and its labels collided -------
old_saw = s[s.index("def scene_build_hubless_saw("):s.index("def scene_build_air_origin(")]
new_saw = '''def scene_build_hubless_saw(app, opaque, transparent, p: float) -> None:
    """A protractor showing the mitres sitting past the saw's own stop."""
    centre = np.array([0.0, 0.0, 0.4])
    radius = 6.2
    reveal = clamp(p * 1.5)

    def point_at(degrees: float, scale: float = 1.0) -> np.ndarray:
        angle = math.radians(degrees)
        return centre + np.array([
            radius * scale * math.cos(angle), 0.0, radius * scale * math.sin(angle)
        ])

    # A filled band for the range a common saw can reach, and another for
    # the range it cannot: two areas read faster than two sets of lines.
    for low, high, colour in (
        (0.0, TYPICAL_MITRE_SAW_MAX_DEG, (0.12, 0.50, 0.34, 0.55)),
        (TYPICAL_MITRE_SAW_MAX_DEG, 90.0, (0.45, 0.12, 0.14, 0.55)),
    ):
        steps = max(2, int(high - low))
        for index in range(steps):
            a = low + (high - low) * index / steps
            b = low + (high - low) * (index + 1) / steps
            inner_a, inner_b = point_at(a, 0.30), point_at(b, 0.30)
            outer_a, outer_b = point_at(a, 0.92), point_at(b, 0.92)
            normal = np.array([0.0, -1.0, 0.0])
            transparent.triangle(inner_a, outer_a, outer_b, colour, normal)
            transparent.triangle(inner_a, outer_b, inner_b, colour, normal)

    # Scale ticks every ten degrees.
    for degree in range(0, 91, 10):
        opaque.cylinder(point_at(degree, 0.92), point_at(degree, 1.0),
                        0.035, MUTED, 6)
    opaque.cylinder(centre, point_at(0.0), 0.045, MUTED, 6)
    opaque.cylinder(centre, point_at(90.0), 0.045, MUTED, 6)
    opaque.cylinder(centre, point_at(TYPICAL_MITRE_SAW_MAX_DEG), 0.085, GREEN, 8)

    # Where this dome's mitres actually land, labelled at staggered radii
    # so neighbouring readings cannot sit on top of each other.
    wanted = sorted({round(item.mitre_deg, 3) for item in SETUPS})
    for index, degree in enumerate(wanted):
        if reveal * 90.0 < degree:
            continue
        opaque.cylinder(centre, point_at(degree), 0.062, RED, 8)
        app.world_labels.append(WorldLabel(
            point_at(degree, 1.12 + index * 0.13), f"{degree:.1f} deg",
            (255, 87, 94)))
        complement = 90.0 - degree
        opaque.cylinder(centre, point_at(complement, 0.62), 0.045, CYAN, 8)
        app.world_labels.append(WorldLabel(
            point_at(complement, 0.50 - index * 0.11), f"{complement:.1f}",
            (61, 211, 255)))

    app.world_labels.extend([
        WorldLabel(point_at(TYPICAL_MITRE_SAW_MAX_DEG, 1.30),
                   f"A COMMON SAW STOPS AT {TYPICAL_MITRE_SAW_MAX_DEG:.0f} deg",
                   (111, 235, 155)),
        WorldLabel(point_at(72.0, 1.30),
                   "EVERY MITRE THIS DOME NEEDS", (255, 87, 94)),
        WorldLabel(point_at(20.0, 0.88),
                   "CUT THE COMPLEMENT INSTEAD", (61, 211, 255)),
        WorldLabel(centre + np.array([0.0, 0.0, -1.4]),
                   "same joint, reachable setting, part turned a quarter turn",
                   (169, 188, 203)),
    ])


'''
s = s.replace(old_saw, new_saw, 1)

# --- 3. The welder was drawn far too small for the dome ----------------
sub(
    '    joints = place_figure(' + NL
    + '        joint_positions(POSES["kneel"], 1.75), (0.0, 0.0, 0.0), 150.0)' + NL
    + "    draw_figure(opaque, joints, scale=0.95)",
    "    # The dome is drawn at 3.4 units for a 60 in radius, so a person is" + NL
    + "    # 68.9 in at the same scale. Getting this wrong is the difference" + NL
    + "    # between a workshop and a doll's house." + NL
    + "    person = 3.4 * (68.9 / AIR.radius_in)" + NL
    + "    joints = place_figure(" + NL
    + '        joint_positions(POSES["kneel"], person), (0.0, 0.0, 0.0), 150.0)' + NL
    + "    draw_figure(opaque, joints, scale=person / 1.75)",
)
# A denser plume, so the label has something to point at.
sub(
    "    for index in range(16):" + NL
    + "        t = (index / 16.0 + rise) % 1.0" + NL
    + "        height = 0.9 + t * 2.4" + NL
    + "        spread = 0.20 + t * 0.95",
    "    for index in range(34):" + NL
    + "        t = (index / 34.0 + rise) % 1.0" + NL
    + "        height = 1.6 + t * 2.2" + NL
    + "        spread = 0.24 + t * 1.05",
)
sub(
    "        transparent.sphere(point, 0.20 + t * 0.16," + NL
    + "                           (0.62, 0.66, 0.70, 0.24 * (1.0 - t)), 3, 7)",
    "        transparent.sphere(point, 0.26 + t * 0.22," + NL
    + "                           (0.68, 0.72, 0.76, 0.30 * (1.0 - t)), 3, 7)",
)

# --- 4. The nesting sheet z-fought, and every panel pointed the same way
old_nest = s[s.index("def scene_build_shelter_nest("):s.index("def scene_build_shelter_size(")]
new_nest = '''def scene_build_shelter_nest(app, opaque, transparent, p: float) -> None:
    """Forty panels laid out on one sheet, to scale."""
    sheet_w, sheet_h = SHELTER_SHEET
    view = 13.0 / sheet_w
    opaque.box((0.0, 0.0, 0.0), (sheet_w * view, sheet_h * view, 0.12),
               (0.20, 0.24, 0.30, 1.0))
    reveal = clamp(p * 1.25)
    radius = SHELTER.radius
    placed = 0
    total = sum(item.count for item in panel_classes())
    y_cursor = sheet_h * 0.5 - 0.5
    for panel_index, panel in enumerate(panel_classes()):
        base = panel.pair_base() * radius
        height = panel.pair_height(radius)
        per_row = max(1, int((sheet_w - 1.0 - base) // (base + 0.125)))
        pairs = math.ceil(panel.count / 2)
        colour = CYAN if panel_index == 0 else AMBER
        for pair in range(pairs):
            row, column = divmod(pair, per_row)
            x0 = -sheet_w * 0.5 + 0.5 + column * (base + 0.125)
            y0 = y_cursor - row * (height + 0.125)
            # A parallelogram is two triangles, and the second one points
            # the other way. That alternation is the whole reason paired
            # triangles strip-pack with no waste between them.
            for flip in (0, 1):
                if placed >= total * reveal:
                    break
                if flip:
                    corners = np.array([
                        [x0 + base, y0, 0.0],
                        [x0 + base + base * 0.35, y0 - height, 0.0],
                        [x0 + base * 0.35, y0 - height, 0.0],
                    ])
                else:
                    corners = np.array([
                        [x0, y0, 0.0],
                        [x0 + base, y0, 0.0],
                        [x0 + base * 0.35, y0 - height, 0.0],
                    ])
                corners[:, 0] *= view
                corners[:, 1] *= view
                # Clear of the sheet's own top face, or the two z-fight.
                corners[:, 2] = 0.22
                normal = np.array([0.0, 0.0, 1.0])
                transparent.triangle(corners[0], corners[1], corners[2],
                                     (colour[0], colour[1], colour[2], 0.55), normal)
                for i in range(3):
                    opaque.cylinder(corners[i], corners[(i + 1) % 3], 0.028,
                                    colour, 6)
                placed += 1
        rows_used = math.ceil(pairs / per_row)
        y_cursor -= rows_used * (height + 0.125)
    app.world_labels.extend([
        WorldLabel(np.array([0.0, sheet_h * view * 0.5 + 1.1, 0.5]),
                   f"ONE {sheet_w / 12:.0f} ft x {sheet_h / 12:.0f} ft SHEET",
                   (169, 188, 203)),
        WorldLabel(np.array([0.0, -sheet_h * view * 0.5 - 1.1, 0.5]),
                   f"ALL {SUMMARY.triangles} PANELS, PAIRED INTO PARALLELOGRAMS",
                   (111, 235, 155)),
    ])


'''
s = s.replace(old_nest, new_nest, 1)

# --- 5. The shelter shot cropped the person and fenced the riser -------
old_size = s[s.index("def scene_build_shelter_size("):s.index("def scene_build_franken_stock(")]
new_size = '''def scene_build_shelter_size(app, opaque, transparent, p: float) -> None:
    """What that sheet actually buys, with a person beside it for scale."""
    view = 4.4 / SHELTER.radius
    scale = SHELTER.radius * view
    for face in GEOMETRY.hemisphere_faces:
        corners = GEOMETRY.vertices[[int(v) for v in face]] * scale
        normal = normalize(corners.mean(axis=0))
        transparent.triangle(corners[0], corners[1], corners[2],
                             (0.15, 0.55, 0.75, 0.16), normal)
    for edge in GEOMETRY.hemisphere_edges:
        a, b = (GEOMETRY.vertices[i] * scale for i in edge)
        opaque.cylinder(a, b, 0.045, CYAN, 6)

    # The person stands beside the shell rather than inside it, because
    # the point of the shot is that they do not fit inside it.
    stature_units = 68.9 * view
    joints = place_figure(
        joint_positions(POSES["stand"], stature_units),
        (0.0, scale * 2.3, 0.0), 250.0)
    draw_figure(opaque, joints, scale=stature_units / 1.75)
    app.world_labels.append(WorldLabel(
        np.array([0.0, scale * 2.3, stature_units + 0.7]),
        "5 ft 8 in, standing", (169, 188, 203)))

    riser = SHELTER.riser_for(72.0) * view * ease_in_out(clamp((p - 0.45) / 0.5))
    if riser > 0.02:
        segments = 44
        for index in range(segments):
            angle_a = math.tau * index / segments
            angle_b = math.tau * (index + 1) / segments
            a = np.array([scale * math.cos(angle_a), scale * math.sin(angle_a), 0.0])
            b = np.array([scale * math.cos(angle_b), scale * math.sin(angle_b), 0.0])
            top_a = a + np.array([0.0, 0.0, riser])
            top_b = b + np.array([0.0, 0.0, riser])
            normal = normalize(np.array([a[0], a[1], 0.0]))
            # A solid band, not a row of posts: it is a wall.
            transparent.triangle(a, b, top_b, (0.32, 0.91, 0.58, 0.30), normal)
            transparent.triangle(a, top_b, top_a, (0.32, 0.91, 0.58, 0.30), normal)
            opaque.cylinder(top_a, top_b, 0.05, GREEN, 6)
            opaque.cylinder(a, b, 0.05, GREEN, 6)
        app.world_labels.append(WorldLabel(
            np.array([-scale * 1.25, 0.0, riser * 0.5]),
            f"RISER {SHELTER.riser_for(72.0):.0f} in\\nbuys standing room",
            (111, 235, 155)))

    app.world_labels.extend([
        WorldLabel(np.array([0.0, 0.0, scale + riser + 1.2]),
                   f"{SHELTER.diameter:.0f} in ACROSS, "
                   f"{SHELTER.headroom:.0f} in TALL", (61, 211, 255)),
        WorldLabel(np.array([0.0, -scale - 1.2, 0.4]),
                   f"{SHELTER.floor_area_sqft:.1f} sq ft", (169, 188, 203)),
    ])


'''
s = s.replace(old_size, new_size, 1)

p.write_text(s, encoding="utf-8")
print("five fixes applied to lesson_build_extra.py")
