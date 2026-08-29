"""The hexagonal dome masterclass: one hexagon, then many.

Act one builds the cage you can frame from a single strut length and a
single hexagon template -- and shows why it still needs twelve pentagons.
Act two raises the frequency for a bigger dome and follows exactly what
that costs: more strut lengths, more panel shapes, and panels that stop
lying flat.

Every number on screen comes from :mod:`two_v_demo.hex_geometry`.
"""

from __future__ import annotations

import math

import numpy as np

from .geometry import normalize
from .hex_geometry import (
    HexBuild,
    HexCage,
    descartes_deficit,
    euler_pentagon_proof,
    flat_vertex_angle_sum,
    goldberg,
    hex_report,
    hex_tiling,
    truncated_icosahedron,
    validate_hex_geometry,
)
from .lessons import Chapter, Lesson
from .render_kit import (
    AMBER,
    CYAN,
    GREEN,
    MUTED,
    PURPLE,
    RED,
    WHITE,
    TriangleBatch,
    WorldLabel,
    clamp,
    ease_in_out,
    smoothstep,
)


# The radius the lesson prices everything at: a 20 ft diameter dome.
LESSON_RADIUS_IN = 120.0
CONNECTOR_DEDUCTION_IN = 0.75

SOCCER = truncated_icosahedron()
GP2 = goldberg(2)
GP3 = goldberg(3)
GP4 = goldberg(4)

PANEL_COLORS = (CYAN, AMBER, GREEN, PURPLE, (0.95, 0.45, 0.75, 1.0))
STRUT_COLORS = (CYAN, AMBER, GREEN, PURPLE, (0.95, 0.45, 0.75, 1.0),
                (0.55, 0.80, 0.35, 1.0))


def _colour_for(names: tuple[str, ...], name: str, palette) -> tuple:
    return palette[names.index(name) % len(palette)]


# ----------------------------------------------------------------------
# Drawing helpers shared by the hex scenes
# ----------------------------------------------------------------------

def polygon_shell(
    batch: TriangleBatch,
    vertices: np.ndarray,
    faces,
    scale: float,
    offset: np.ndarray,
    colour,
    reveal: float = 1.0,
    lift: float = 0.0,
) -> None:
    """Fill each polygon by fanning it from its own centre."""
    face_list = list(faces)
    count = int(math.ceil(len(face_list) * clamp(reveal)))
    for face in face_list[:count]:
        points = [vertices[index] * scale for index in face]
        centre = sum(points) / len(points)
        outward = normalize(centre)
        points = [point + outward * lift + offset for point in points]
        middle = centre + outward * lift + offset
        for position in range(len(points)):
            a = points[position]
            b = points[(position + 1) % len(points)]
            batch.triangle(middle, a, b, colour, outward)


def cage_edges(cage: HexCage, subset=None) -> list[tuple[int, int]]:
    return list(cage.edges if subset is None else subset)


def draw_cage(
    app,
    opaque: TriangleBatch,
    cage: HexCage,
    scale: float,
    offset: np.ndarray,
    *,
    edges=None,
    radius: float = 0.055,
    by_class: bool = True,
    reveal: float = 1.0,
    node_radius: float = 0.085,
    plain=None,
) -> None:
    """Draw a cage's frame, colouring each strut by its measured length."""
    edge_list = cage_edges(cage, edges)
    names = tuple(item.name for item in cage.edge_classes)
    class_of = dict(zip(cage.edges, cage.edge_class_of))
    colours = None
    if by_class:
        colours = {
            edge: _colour_for(names, class_of[edge], STRUT_COLORS)
            for edge in edge_list
        }
    app.add_edges(
        opaque, cage.vertices, edge_list, scale, offset,
        plain or WHITE, radius, colours, reveal,
    )
    shown = int(math.ceil(len(edge_list) * clamp(reveal)))
    corners = sorted({index for edge in edge_list[:shown] for index in edge})
    app.add_nodes(
        opaque, cage.vertices, scale, offset, (0.80, 0.88, 0.94, 1.0),
        node_radius, corners,
    )


def draw_panels(
    app,
    transparent: TriangleBatch,
    cage: HexCage,
    scale: float,
    offset: np.ndarray,
    *,
    faces=None,
    alpha: float = 0.20,
    reveal: float = 1.0,
    lift: float = 0.0,
) -> None:
    """Fill panels, tinting every panel class its own colour."""
    names = tuple(item.name for item in cage.face_classes)
    indices = list(range(len(cage.faces)) if faces is None else faces)
    count = int(math.ceil(len(indices) * clamp(reveal)))
    for face_index in indices[:count]:
        colour = _colour_for(names, cage.face_class_of[face_index], PANEL_COLORS)
        tint = (colour[0], colour[1], colour[2], alpha)
        polygon_shell(
            transparent, cage.vertices, [cage.faces[face_index]],
            scale, offset, tint, 1.0, lift,
        )


def flat_panel_points(cage: HexCage, face_index: int) -> np.ndarray:
    """Lay one panel down flat, so its true shape can be seen and measured."""
    points = cage.vertices[list(cage.faces[face_index])]
    centre = points.mean(axis=0)
    centred = points - centre
    _, _, right = np.linalg.svd(centred, full_matrices=False)
    basis_x, basis_y = right[0], right[1]
    return np.array([
        [float(np.dot(point, basis_x)), float(np.dot(point, basis_y)), 0.0]
        for point in centred
    ])


def draw_flat_panel(
    app,
    opaque: TriangleBatch,
    transparent: TriangleBatch,
    cage: HexCage,
    face_index: int,
    centre: np.ndarray,
    scale: float,
    colour,
    *,
    strut_radius: float = 0.055,
    label: str | None = None,
) -> None:
    """Draw one panel as a flat template standing up in the frame."""
    flat = flat_panel_points(cage, face_index) * scale
    points = [
        centre + np.array([float(point[0]), 0.0, float(point[1])])
        for point in flat
    ]
    fill = (colour[0], colour[1], colour[2], 0.22)
    normal = np.array([0.0, -1.0, 0.0])
    middle = sum(points) / len(points)
    for position in range(len(points)):
        a = points[position]
        b = points[(position + 1) % len(points)]
        transparent.triangle(middle, a, b, fill, normal)
        opaque.cylinder(a, b, strut_radius, colour, 8)
    if label:
        app.world_labels.append(WorldLabel(
            middle, label,
            (int(colour[0] * 255), int(colour[1] * 255), int(colour[2] * 255)),
        ))


def bar_row(
    opaque: TriangleBatch,
    app,
    entries,
    origin: np.ndarray,
    spacing: float,
    height_scale: float,
) -> None:
    """A row of labelled bars -- the lesson's only chart form."""
    for index, (label, value, colour) in enumerate(entries):
        height = max(0.05, value * height_scale)
        x = origin[0] + index * spacing
        opaque.box((x, origin[1], origin[2] + height * 0.5),
                   (spacing * 0.44, 0.7, height), colour)
        app.world_labels.append(WorldLabel(
            np.array([x, origin[1], origin[2] + height + 0.45]), label,
            (int(colour[0] * 255), int(colour[1] * 255), int(colour[2] * 255)),
        ))


# ----------------------------------------------------------------------
# Act zero -- why hexagons, and why they will not curve
# ----------------------------------------------------------------------

def scene_hex_flat(app, opaque, transparent, p: float) -> None:
    centres, corners = hex_tiling(3, 1.35)
    reveal = smoothstep(min(1.0, p * 1.6))
    shown = int(math.ceil(len(centres) * reveal))
    for index in range(shown):
        ring = corners[index] + np.array([0.0, 0.0, 0.9])
        middle = centres[index] + np.array([0.0, 0.0, 0.9])
        tint = CYAN if index % 3 else AMBER
        for position in range(6):
            a, b = ring[position], ring[(position + 1) % 6]
            opaque.cylinder(a, b, 0.045, tint, 7)
            transparent.triangle(middle, a, b,
                                 (tint[0], tint[1], tint[2], 0.13),
                                 np.array([0.0, 0.0, 1.0]))
    app.world_labels.append(WorldLabel(
        np.array([0.0, 0.0, 2.6]),
        f"{shown} HEXAGONS, ONE SHAPE, PERFECTLY FLAT", (111, 235, 155),
    ))


def scene_hex_flat_angle(app, opaque, transparent, p: float) -> None:
    """Three hexagons round one corner, with the angle budget spelled out."""
    circumradius = 2.1
    step = circumradius * math.sqrt(3.0)
    axis_a = np.array([step, 0.0, 0.0])
    axis_b = np.array([step * 0.5, step * math.sqrt(3.0) * 0.5, 0.0])
    base = np.array([0.0, -1.4, 1.1])
    tints = (CYAN, AMBER, GREEN)
    corner_offsets = np.array([
        [circumradius * math.cos(math.radians(30.0 + 60.0 * k)),
         circumradius * math.sin(math.radians(30.0 + 60.0 * k)), 0.0]
        for k in range(6)
    ])
    shown = 1 + int(round(smoothstep(min(1.0, p * 1.7)) * 2.0))
    centres = (np.zeros(3), axis_a, axis_b)
    shared = base + axis_a * (1.0 / 3.0) + axis_b * (1.0 / 3.0)
    for index in range(min(3, shown)):
        middle = base + centres[index]
        ring = middle + corner_offsets
        tint = tints[index]
        for position in range(6):
            a, b = ring[position], ring[(position + 1) % 6]
            opaque.cylinder(a, b, 0.055, tint, 8)
            transparent.triangle(middle, a, b,
                                 (tint[0], tint[1], tint[2], 0.15),
                                 np.array([0.0, 0.0, 1.0]))
        app.world_labels.append(WorldLabel(
            middle, "120.000 deg",
            (int(tint[0] * 255), int(tint[1] * 255), int(tint[2] * 255)),
        ))
    opaque.sphere(shared, 0.20, RED, 6, 10)
    app.world_labels.append(WorldLabel(
        shared + np.array([0.0, 0.0, 1.5]),
        f"3 x 120 = {flat_vertex_angle_sum(6):.0f} deg\n0 deg left over",
        (255, 87, 94),
    ))


def scene_hex_deficit(app, opaque, transparent, p: float) -> None:
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
                   "FULL TURN OF PAPER\n360 deg -> stays flat", (61, 211, 255)),
        WorldLabel(right + np.array([0.0, 0.0, -0.9]),
                   f"WEDGE REMOVED\n{360.0 - math.degrees(missing):.1f} deg -> rises "
                   f"{height:.2f}", (111, 235, 155)),
        WorldLabel(np.array([0.0, 0.0, 4.4]),
                   "NOTHING STRETCHED. ONLY ANGLE WAS REMOVED.",
                   (255, 177, 62)),
    ])


# ----------------------------------------------------------------------
# Act one -- the single-hexagon cage
# ----------------------------------------------------------------------

def scene_hex_pentagon_swap(app, opaque, transparent, p: float) -> None:
    """One pentagon among hexagons, with both angle budgets side by side."""
    swap = smoothstep(clamp((p - 0.18) / 0.62))
    centre = np.array([0.0, 0.0, 1.2])
    for sides, offset, tint, label in (
        (6, np.array([-4.6, 0.0, 0.0]), CYAN, "HEXAGON"),
        (5, np.array([4.6, 0.0, 0.0]), AMBER, "PENTAGON"),
    ):
        middle = centre + offset
        radius = 2.5
        ring = [
            middle + np.array([
                radius * math.cos(math.tau * k / sides + math.pi / 2.0),
                radius * math.sin(math.tau * k / sides + math.pi / 2.0),
                0.0,
            ])
            for k in range(sides)
        ]
        for position in range(sides):
            a, b = ring[position], ring[(position + 1) % sides]
            opaque.cylinder(a, b, 0.06, tint, 8)
            transparent.triangle(middle, a, b,
                                 (tint[0], tint[1], tint[2], 0.16),
                                 np.array([0.0, 0.0, 1.0]))
        interior = 180.0 * (sides - 2) / sides
        app.world_labels.append(WorldLabel(
            middle,
            f"{label}\ncorner {interior:.1f} deg\n"
            f"3 corners = {flat_vertex_angle_sum(sides):.1f} deg",
            (int(tint[0] * 255), int(tint[1] * 255), int(tint[2] * 255)),
        ))
    gap = 360.0 - flat_vertex_angle_sum(5)
    lift = swap * 1.6
    opaque.arrow(np.array([4.6, 0.0, 1.2]), np.array([4.6, 0.0, 1.2 + lift + 0.5]),
                 0.05, GREEN)
    app.world_labels.append(WorldLabel(
        np.array([0.0, 0.0, 5.0]),
        f"THE PENTAGON LEAVES {gap:.0f} deg UNUSED -- THAT IS THE CURVE",
        (111, 235, 155),
    ))


def scene_hex_euler(app, opaque, transparent, p: float) -> None:
    """The count that never changes, drawn as four cages of different size."""
    models = ((SOCCER, "GP(1,1)"), (GP2, "GP(2,0)"), (GP3, "GP(3,0)"),
              (GP4, "GP(4,0)"))
    positions = np.linspace(-12.6, 6.2, len(models))
    reveal = smoothstep(min(1.0, p * 1.5))
    for index, ((cage, notation), x) in enumerate(zip(models, positions)):
        centre = np.array([float(x), 0.0, 3.0])
        scale = 2.05
        angle = p * math.tau * 0.10
        rotation = np.array([
            [math.cos(angle), -math.sin(angle), 0.0],
            [math.sin(angle), math.cos(angle), 0.0],
            [0.0, 0.0, 1.0],
        ])
        spun = cage.vertices @ rotation.T
        pentagons = [
            face for face_index, face in enumerate(cage.faces)
            if len(face) == 5
        ]
        app.add_edges(opaque, spun, cage.edges, scale, centre,
                      (0.33, 0.45, 0.56, 1.0), 0.030, None, reveal)
        polygon_shell(transparent, spun, pentagons, scale, centre,
                      (1.00, 0.67, 0.20, 0.55), reveal, 0.012)
        app.world_labels.append(WorldLabel(
            centre + np.array([0.0, 0.0, -2.85]),
            f"{notation}\n{cage.hexagons} hexagons\n{cage.pentagons} pentagons",
            (255, 177, 62) if index else (61, 211, 255),
        ))
    app.world_labels.append(WorldLabel(
        np.array([-3.2, 0.0, 6.4]),
        "HEXAGONS: AS MANY AS YOU LIKE.   PENTAGONS: ALWAYS TWELVE.",
        (111, 235, 155),
    ))


def scene_hex_soccer(app, opaque, transparent, p: float) -> None:
    scale = 5.0
    centre = np.zeros(3)
    app.add_latitude_sphere(transparent, scale, centre, False, 0.055)
    draw_panels(app, transparent, SOCCER, scale, centre, alpha=0.17, lift=0.004)
    draw_cage(app, opaque, SOCCER, scale, centre, radius=0.062,
              reveal=smoothstep(p * 1.4), node_radius=0.095)
    app.world_labels.append(WorldLabel(
        np.array([0.0, 0.0, 6.0]),
        f"{SOCCER.hexagons} HEXAGONS + {SOCCER.pentagons} PENTAGONS"
        f"   {len(SOCCER.edges)} STRUTS", (111, 235, 155),
    ))


def scene_hex_soccer_struts(app, opaque, transparent, p: float) -> None:
    """Ninety struts, and a rack proving they are all the same stick."""
    scale = 3.5
    centre = np.array([-2.0, 0.0, 4.3])
    draw_cage(app, opaque, SOCCER, scale, centre, radius=0.05,
              reveal=smoothstep(p * 1.5), node_radius=0.075)
    build = HexBuild(SOCCER, LESSON_RADIUS_IN, CONNECTOR_DEDUCTION_IN)
    name, count, centre_length, cut_length = build.strut_table()[0]
    reveal = int(count * smoothstep(clamp((p - 0.15) / 0.8)))
    length = 1.7
    for index in range(reveal):
        column, row = index % 20, index // 20
        x = -7.8 + column * 0.55
        y = 4.2 + row * 0.95
        opaque.cylinder(np.array([x, y, 0.20]),
                        np.array([x, y, 0.20 + length]), 0.05, CYAN, 6)
    app.world_labels.extend([
        WorldLabel(np.array([-2.6, 4.2, 2.45]),
                   f"{reveal:02d} / {count} STRUTS CUT -- ONE SAW SETTING",
                   (61, 211, 255)),
        WorldLabel(np.array([-2.6, 6.1, 2.45]),
                   f"centre to centre {centre_length:.3f} in\n"
                   f"cut {cut_length:.3f} in after hub deduction",
                   (169, 188, 203)),
    ])


def scene_hex_soccer_panels(app, opaque, transparent, p: float) -> None:
    """Both panel templates, laid flat and measured."""
    order = [item for item in SOCCER.face_classes]
    names = tuple(item.name for item in SOCCER.face_classes)
    positions = np.linspace(-1.2, 5.4, len(order))
    reveal = smoothstep(min(1.0, p * 1.6))
    for index, (item, x) in enumerate(zip(order, positions)):
        face_index = SOCCER.face_class_of.index(item.name)
        colour = _colour_for(names, item.name, PANEL_COLORS)
        if reveal < (index + 0.15) / max(1, len(order)):
            continue
        draw_flat_panel(
            app, opaque, transparent, SOCCER, face_index,
            np.array([float(x), 0.0, 2.7]), 4.4, colour,
            label=f"{item.name}   x{item.count}\n"
                  f"side {item.edge_factors[0] * LESSON_RADIUS_IN:.3f} in\n"
                  f"corner {item.corner_angles_deg[0]:.3f} deg\n"
                  f"{'flat, regular' if item.is_regular else 'irregular'}",
        )
    app.world_labels.append(WorldLabel(
        np.array([2.1, 0.0, 5.1]),
        "TWO TEMPLATES CUT THE WHOLE SKIN", (111, 235, 155),
    ))


def scene_hex_soccer_cut(app, opaque, transparent, p: float) -> None:
    """Where the cage meets the ground -- and how far from level it is."""
    scale = 5.0
    centre = np.zeros(3)
    lift = smoothstep(clamp((p - 0.12) / 0.7))
    dome = list(SOCCER.dome_faces)
    draw_panels(app, transparent, SOCCER, scale, centre, faces=dome, alpha=0.16)
    draw_cage(app, opaque, SOCCER, scale, centre,
              edges=SOCCER.dome_edges, radius=0.055, node_radius=0.08)
    rim = SOCCER.base_vertices
    for edge in SOCCER.boundary_edges:
        a, b = (SOCCER.vertices[index] * scale for index in edge)
        opaque.cylinder(a, b, 0.10, RED, 10)
    low = SOCCER.rim_low * scale
    for index in rim:
        point = SOCCER.vertices[index] * scale
        opaque.cylinder(np.array([point[0], point[1], low]),
                        point, 0.035, GREEN, 6)
        opaque.sphere(point, 0.11, RED, 5, 9)
    # The level course that has to make up the difference.
    for step in range(36):
        angle_a = math.tau * step / 36
        angle_b = math.tau * (step + 1) / 36
        radius = scale * 0.99
        a = np.array([radius * math.cos(angle_a), radius * math.sin(angle_a), low])
        b = np.array([radius * math.cos(angle_b), radius * math.sin(angle_b), low])
        opaque.cylinder(a, b, 0.05, GREEN, 6)
    build = HexBuild(SOCCER, LESSON_RADIUS_IN, CONNECTOR_DEDUCTION_IN)
    app.world_labels.extend([
        WorldLabel(np.array([0.0, 0.0, 6.2]),
                   f"RIM RISES AND FALLS {build.base_wobble:.1f} in"
                   f" ON A {LESSON_RADIUS_IN * 2 / 12:.0f} ft DOME",
                   (255, 87, 94)),
        WorldLabel(np.array([0.0, -7.4, low + 0.2]),
                   "LEVEL COURSE MAKES UP THE DIFFERENCE", (111, 235, 155)),
    ])


def scene_hex_soccer_build(app, opaque, transparent, p: float) -> None:
    """Raise the dome from the rim up, one course at a time."""
    scale = 5.0
    reveal = smoothstep(p)
    records = sorted(
        SOCCER.dome_edges,
        key=lambda edge: float(np.mean(SOCCER.vertices[list(edge), 2])),
    )
    count = int(math.ceil(len(records) * reveal))
    names = tuple(item.name for item in SOCCER.edge_classes)
    class_of = dict(zip(SOCCER.edges, SOCCER.edge_class_of))
    for edge in records[:count]:
        a, b = (SOCCER.vertices[index] * scale for index in edge)
        opaque.cylinder(a, b, 0.062, _colour_for(names, class_of[edge], STRUT_COLORS), 9)
    built = sorted({index for edge in records[:count] for index in edge})
    app.add_nodes(opaque, SOCCER.vertices, scale, np.zeros(3), WHITE, 0.088, built)
    face_records = sorted(
        SOCCER.dome_faces,
        key=lambda index: float(np.mean(SOCCER.vertices[list(SOCCER.faces[index]), 2])),
    )
    filled = max(0, int(len(face_records) * (reveal - 0.16) / 0.84))
    draw_panels(app, transparent, SOCCER, scale, np.zeros(3),
                faces=face_records[:filled], alpha=0.18, lift=0.004)
    app.world_labels.append(WorldLabel(
        np.array([0.0, 0.0, 6.1]),
        f"RIM TO CROWN   {count:02d} / {len(SOCCER.dome_edges)} STRUTS",
        (111, 235, 155),
    ))


# ----------------------------------------------------------------------
# Act two -- hexagons in different sizes
# ----------------------------------------------------------------------

def scene_hex_dual(app, opaque, transparent, p: float) -> None:
    """Watch a triangulated dome turn into a hexagon cage."""
    from .hex_geometry import geodesic_class_one

    scale = 5.0
    blend = ease_in_out(clamp((p - 0.14) / 0.68))
    geo_vertices, geo_faces = geodesic_class_one(2)
    app.add_latitude_sphere(transparent, scale, np.zeros(3), False, 0.05)
    if blend < 0.98:
        app.add_edges(
            opaque, geo_vertices,
            [(int(a), int(b)) for face in geo_faces
             for a, b in ((face[0], face[1]), (face[1], face[2]), (face[2], face[0]))
             if a < b],
            scale, np.zeros(3),
            (0.40, 0.47, 0.57, 1.0 - blend * 0.75), 0.038,
        )
    # Every triangle's centre is a hexagon corner; every triangle vertex
    # becomes a panel.  Grow the cage out of the centres.
    grown = GP2.vertices * (0.55 + 0.45 * blend)
    if blend > 0.02:
        app.add_nodes(opaque, GP2.vertices, scale, np.zeros(3), AMBER,
                      0.09 * blend + 0.02)
        draw_cage(app, opaque, GP2, scale * (0.55 + 0.45 * blend), np.zeros(3),
                  radius=0.05 * blend + 0.005, by_class=False,
                  plain=CYAN, node_radius=0.001)
    app.world_labels.append(WorldLabel(
        np.array([0.0, 0.0, 6.0]),
        f"EVERY TRIANGLE CORNER BECOMES ONE PANEL   {blend * 100:3.0f}%",
        (255, 177, 62),
    ))


def scene_hex_goldberg2(app, opaque, transparent, p: float) -> None:
    scale = 5.0
    app.add_latitude_sphere(transparent, scale, np.zeros(3), False, 0.05)
    draw_panels(app, transparent, GP2, scale, np.zeros(3), alpha=0.17, lift=0.004)
    draw_cage(app, opaque, GP2, scale, np.zeros(3), radius=0.055,
              reveal=smoothstep(p * 1.4), node_radius=0.08)
    build = HexBuild(GP2, LESSON_RADIUS_IN, CONNECTOR_DEDUCTION_IN)
    for index, (name, count, centre_length, _) in enumerate(build.strut_table()):
        app.world_labels.append(WorldLabel(
            np.array([-7.4, 0.0, 5.0 - index * 0.85]),
            f"{name}  x{count}  {centre_length:.3f} in",
            tuple(int(value * 255) for value in STRUT_COLORS[index][:3]),
        ))
    app.world_labels.append(WorldLabel(
        np.array([0.0, 0.0, 6.1]),
        f"{GP2.hexagons} HEXAGONS, {GP2.pentagons} PENTAGONS, "
        f"{GP2.strut_lengths} STRUT LENGTHS", (111, 235, 155),
    ))


def scene_hex_two_struts(app, opaque, transparent, p: float) -> None:
    """One GP(2,0) hexagon, flat, with its two different sides called out."""
    face_index = GP2.face_class_of.index("HEX")
    draw_flat_panel(app, opaque, transparent, GP2, face_index,
                    np.array([-1.1, 0.0, 3.0]), 5.4, CYAN)
    soccer_face = SOCCER.face_class_of.index("HEX")
    draw_flat_panel(app, opaque, transparent, SOCCER, soccer_face,
                    np.array([5.3, 0.0, 3.0]), 5.4, AMBER)
    hexagon = next(item for item in GP2.face_classes if item.sides == 6)
    regular = next(item for item in SOCCER.face_classes if item.sides == 6)
    app.world_labels.extend([
        WorldLabel(np.array([-1.1, 0.0, 0.4]),
                   f"GP(2,0) HEXAGON\nsides "
                   f"{min(hexagon.edge_factors) * LESSON_RADIUS_IN:.3f}"
                   f" and {max(hexagon.edge_factors) * LESSON_RADIUS_IN:.3f} in\n"
                   f"corners {min(hexagon.corner_angles_deg):.2f}"
                   f" to {max(hexagon.corner_angles_deg):.2f} deg",
                   (61, 211, 255)),
        WorldLabel(np.array([5.3, 0.0, 0.4]),
                   f"GP(1,1) HEXAGON\nevery side "
                   f"{regular.edge_factors[0] * LESSON_RADIUS_IN:.3f} in\n"
                   f"every corner {regular.corner_angles_deg[0]:.2f} deg",
                   (255, 177, 62)),
        WorldLabel(np.array([2.1, 0.0, 5.6]),
                   "RAISING THE FREQUENCY BREAKS THE REGULAR HEXAGON",
                   (255, 87, 94)),
    ])


def scene_hex_size_ladder(app, opaque, transparent, p: float) -> None:
    """The price list: what each frequency costs in shapes and lengths."""
    models = ((SOCCER, "GP(1,1)"), (GP2, "GP(2,0)"), (GP3, "GP(3,0)"),
              (GP4, "GP(4,0)"))
    reveal = smoothstep(min(1.0, p * 1.5))
    positions = np.linspace(-11.4, 5.4, len(models))
    for index, ((cage, notation), x) in enumerate(zip(models, positions)):
        if reveal < (index + 0.1) / len(models):
            continue
        struts = cage.strut_lengths
        shapes = cage.hex_shapes
        opaque.box((float(x) - 1.05, 0.0, 0.35 + struts * 0.34),
                   (1.5, 0.8, struts * 0.68), CYAN)
        opaque.box((float(x) + 1.05, 0.0, 0.35 + shapes * 0.34),
                   (1.5, 0.8, shapes * 0.68), AMBER)
        app.world_labels.extend([
            WorldLabel(np.array([float(x), 0.0, -0.55]),
                       f"{notation}\n{cage.hexagons + cage.pentagons} panels",
                       (169, 188, 203)),
            WorldLabel(np.array([float(x) - 1.05, 0.0, 0.5 + struts * 0.68 + 0.5]),
                       f"{struts} strut", (61, 211, 255)),
            WorldLabel(np.array([float(x) + 1.05, 0.0, 0.5 + shapes * 0.68 + 0.5]),
                       f"{shapes} hex shape", (255, 177, 62)),
        ])
    app.world_labels.append(WorldLabel(
        np.array([-3.0, 0.0, 6.4]),
        "BIGGER AND ROUNDER COSTS SHAPES, EVERY TIME", (111, 235, 155),
    ))


def scene_hex_warp(app, opaque, transparent, p: float) -> None:
    """A single hexagon lifted off its own best-fit plane."""
    face_index = max(
        range(len(GP4.faces)),
        key=lambda index: (
            len(GP4.faces[index]) == 6,
            next(item.planarity_error for item in GP4.face_classes
                 if item.name == GP4.face_class_of[index]),
        ),
    )
    face = GP4.faces[face_index]
    points = GP4.vertices[list(face)]
    centre = points.mean(axis=0)
    centred = points - centre
    _, _, right = np.linalg.svd(centred, full_matrices=False)
    normal = right[-1]
    exaggeration = 26.0 * ease_in_out(clamp((p - 0.12) / 0.7))
    scale = 13.0
    base = np.array([2.2, 0.0, 2.9])
    flat, warped = [], []
    for point in centred:
        offset = float(np.dot(point, normal))
        in_plane = point - normal * offset
        local_x = right[0]
        local_y = right[1]
        planar = np.array([
            float(np.dot(in_plane, local_x)) * scale,
            0.0,
            float(np.dot(in_plane, local_y)) * scale,
        ])
        flat.append(base + planar)
        warped.append(base + planar + np.array([0.0, offset * scale * exaggeration, 0.0]))
    for position in range(6):
        opaque.cylinder(flat[position], flat[(position + 1) % 6], 0.035, MUTED, 6)
        opaque.cylinder(warped[position], warped[(position + 1) % 6], 0.07, AMBER, 9)
        opaque.cylinder(flat[position], warped[position], 0.025, RED, 5)
    warp_class = next(
        item for item in GP4.face_classes
        if item.name == GP4.face_class_of[face_index]
    )
    build = HexBuild(GP4, LESSON_RADIUS_IN, CONNECTOR_DEDUCTION_IN)
    app.world_labels.extend([
        WorldLabel(base + np.array([0.0, 0.0, 2.3]),
                   f"OUT OF PLANE BY {warp_class.planarity_error * LESSON_RADIUS_IN:.4f} in"
                   f"   (SHOWN x{exaggeration:.0f})", (255, 87, 94)),
        WorldLabel(base + np.array([0.0, 0.0, -2.4]),
                   "SIX CORNERS ON A SPHERE DO NOT SHARE A PLANE",
                   (169, 188, 203)),
    ])


def scene_hex_warp_cost(app, opaque, transparent, p: float) -> None:
    """Warp, per cage, at the lesson's radius -- and what to do about it."""
    entries = []
    for cage, notation in ((SOCCER, "GP(1,1)"), (GP2, "GP(2,0)"),
                           (GP3, "GP(3,0)"), (GP4, "GP(4,0)")):
        warp = cage.worst_planarity * LESSON_RADIUS_IN
        flat = warp < 1e-9
        entries.append((
            f"{notation}\n{warp:.4f} in" + ("\nFLAT" if flat else ""),
            max(warp, 0.02), GREEN if flat else AMBER,
        ))
    bar_row(opaque, app, entries, np.array([-9.6, 0.0, 0.35]), 4.2, 8.0)
    app.world_labels.extend([
        WorldLabel(np.array([-3.2, 0.0, 5.6]),
                   f"WORST PANEL WARP AT R = {LESSON_RADIUS_IN:.0f} in",
                   (111, 235, 155)),
        WorldLabel(np.array([-3.2, 0.0, -1.5]),
                   "FLAT PANEL + WARPED FRAME = A GAP TO SEAL",
                   (169, 188, 203)),
    ])


def scene_hex_compare(app, opaque, transparent, p: float) -> None:
    """The two hex domes, at the same radius, side by side."""
    scale = 3.5
    reveal = smoothstep(min(1.0, p * 1.4))
    for cage, offset, tint in ((SOCCER, np.array([2.4, 0.0, 1.1]), CYAN),
                               (GP4, np.array([-7.6, 0.0, 1.1]), AMBER)):
        draw_panels(app, transparent, cage, scale, offset,
                    faces=cage.dome_faces, alpha=0.15)
        app.add_edges(opaque, cage.vertices, cage.dome_edges, scale, offset,
                      tint, 0.042, None, reveal)
        build = HexBuild(cage, LESSON_RADIUS_IN, CONNECTOR_DEDUCTION_IN)
        app.world_labels.append(WorldLabel(
            offset + np.array([0.0, 0.0, -2.15]),
            f"{cage.notation}\n{len(cage.dome_faces)} panels  "
            f"{len(cage.dome_edges)} struts\n"
            f"{cage.strut_lengths} strut length(s)  {cage.hex_shapes} hex shape(s)\n"
            f"rim wobble {build.base_wobble:.1f} in",
            (int(tint[0] * 255), int(tint[1] * 255), int(tint[2] * 255)),
        ))
    app.world_labels.append(WorldLabel(
        np.array([-3.0, 0.0, 6.0]),
        "SAME RADIUS, SAME SPHERE, DIFFERENT SHOP", (111, 235, 155),
    ))


def scene_hex_skin(app, opaque, transparent, p: float) -> None:
    """Three hexagons meeting at a hub -- where the water gets in."""
    scale = 5.0
    centre = np.zeros(3)
    app.add_latitude_sphere(transparent, scale, centre, True, 0.05)
    draw_panels(app, transparent, SOCCER, scale, centre,
                faces=SOCCER.dome_faces, alpha=0.15, lift=0.006)
    draw_cage(app, opaque, SOCCER, scale, centre,
              edges=SOCCER.dome_edges, radius=0.05, node_radius=0.07)
    # Follow one hub and lift the three panels that meet on it.
    hub = max(SOCCER.base_vertices, key=lambda index: SOCCER.vertices[index][2]) \
        if SOCCER.base_vertices else 0
    hub = int(np.argmax(SOCCER.vertices[:, 2]))
    lift = ease_in_out(clamp((p - 0.2) / 0.65)) * 0.9
    touching = [index for index, face in enumerate(SOCCER.faces) if hub in face]
    for face_index in touching:
        polygon_shell(transparent, SOCCER.vertices, [SOCCER.faces[face_index]],
                      scale, centre, (1.00, 0.67, 0.20, 0.35), 1.0, lift)
    point = SOCCER.vertices[hub] * scale
    opaque.sphere(point, 0.18, RED, 6, 10)
    app.world_labels.extend([
        WorldLabel(point + np.array([0.0, 0.0, 1.6 + lift]),
                   "THREE PANELS, ONE HUB, THREE SEAMS", (255, 87, 94)),
        WorldLabel(np.array([0.0, 0.0, -1.2]),
                   "SHINGLE FROM THE RIM UP SO EVERY LAP SHEDS DOWNHILL",
                   (169, 188, 203)),
    ])


def scene_hex_choose(app, opaque, transparent, p: float) -> None:
    """Panels against strut classes: the whole decision in one picture."""
    models = ((SOCCER, "GP(1,1)"), (GP2, "GP(2,0)"), (GP3, "GP(3,0)"),
              (GP4, "GP(4,0)"))
    reveal = smoothstep(min(1.0, p * 1.4))
    for index, (cage, notation) in enumerate(models):
        if reveal < (index + 0.1) / len(models):
            continue
        x = -10.6 + index * 5.0
        panels = len(cage.dome_faces)
        opaque.box((x, 1.4, 0.35 + panels * 0.036),
                   (1.5, 0.8, panels * 0.072), CYAN)
        opaque.box((x, -1.4, 0.35 + cage.strut_lengths * 0.42),
                   (1.5, 0.8, cage.strut_lengths * 0.84), AMBER)
        app.world_labels.extend([
            WorldLabel(np.array([x, 1.4, 0.5 + panels * 0.072 + 0.5]),
                       f"{panels} panels", (61, 211, 255)),
            WorldLabel(np.array([x, -1.4, 0.5 + cage.strut_lengths * 0.84 + 0.5]),
                       f"{cage.strut_lengths} lengths", (255, 177, 62)),
            WorldLabel(np.array([x, 0.0, -0.75]), notation, (169, 188, 203)),
        ])
    app.world_labels.append(WorldLabel(
        np.array([-3.1, 0.0, 6.2]),
        "MORE PANELS IS WORK YOU REPEAT. MORE LENGTHS IS WORK YOU GET WRONG.",
        (111, 235, 155),
    ))


def scene_hex_finale(app, opaque, transparent, p: float) -> None:
    scale = 5.0
    if p < 0.30:
        local = p / 0.30
        centres, corners = hex_tiling(2, 1.5)
        shown = int(math.ceil(len(centres) * smoothstep(local)))
        for index in range(shown):
            ring = corners[index] + np.array([0.0, 0.0, 1.1])
            for position in range(6):
                opaque.cylinder(ring[position], ring[(position + 1) % 6],
                                0.05, CYAN, 7)
    elif p < 0.64:
        local = (p - 0.30) / 0.34
        app.add_latitude_sphere(transparent, scale, np.zeros(3), False, 0.05)
        draw_panels(app, transparent, SOCCER, scale, np.zeros(3),
                    alpha=0.16, reveal=smoothstep(local), lift=0.004)
        draw_cage(app, opaque, SOCCER, scale, np.zeros(3), radius=0.058,
                  reveal=smoothstep(local * 1.3), node_radius=0.085)
    else:
        local = (p - 0.64) / 0.36
        app.add_latitude_sphere(transparent, scale, np.zeros(3), True, 0.05)
        draw_panels(app, transparent, SOCCER, scale, np.zeros(3),
                    faces=SOCCER.dome_faces, alpha=0.18,
                    reveal=smoothstep(local), lift=0.004)
        draw_cage(app, opaque, SOCCER, scale, np.zeros(3),
                  edges=SOCCER.dome_edges, radius=0.062, node_radius=0.088)
    app.world_labels.append(WorldLabel(
        np.array([0.0, 0.0, 6.2]),
        "FLAT SHEET  ->  TWELVE PENTAGONS  ->  A DOME THAT CLOSES",
        (111, 235, 155),
    ))


# ----------------------------------------------------------------------
# Live figures beside the fixed equations
# ----------------------------------------------------------------------

def hex_equations(app, stage: str) -> list[str]:
    build = HexBuild(SOCCER, LESSON_RADIUS_IN, CONNECTOR_DEDUCTION_IN)
    if stage == "hex_flat_angle":
        return [
            f"regular hexagon corner = {180.0 * 4 / 6:.3f} deg",
            f"three of them          = {flat_vertex_angle_sum(6):.3f} deg",
            "spare angle            = 0.000 deg",
        ]
    if stage == "hex_deficit":
        deficit = descartes_deficit(SOCCER)
        return [
            f"pentagon corner   = {180.0 * 3 / 5:.3f} deg",
            f"three of them     = {flat_vertex_angle_sum(5):.3f} deg",
            f"spare angle       = {360.0 - flat_vertex_angle_sum(5):.3f} deg",
            f"whole cage needs  = {deficit.total_deficit_deg:.3f} deg",
        ]
    if stage == "hex_euler":
        lines = []
        for cage in (SOCCER, GP2, GP3, GP4):
            lines.append(
                f"{cage.notation}: H {cage.hexagons:>3}  P {cage.pentagons}"
                f"  V-E+F = {cage.euler}"
            )
        return lines
    if stage in ("hex_soccer", "hex_soccer_struts"):
        name, count, centre_length, cut_length = build.strut_table()[0]
        return [
            f"struts        = {len(SOCCER.edges)} total, {count} in the dome",
            f"strut lengths = {SOCCER.strut_lengths}",
            f"centre length = {centre_length:.4f} in",
            f"cut length    = {cut_length:.4f} in",
        ]
    if stage == "hex_soccer_panels":
        return [
            f"{item.name}: x{item.count}  side "
            f"{item.edge_factors[0] * LESSON_RADIUS_IN:.4f} in  "
            f"area {item.area_factor * LESSON_RADIUS_IN**2:.1f} sq in"
            for item in SOCCER.face_classes
        ]
    if stage == "hex_soccer_cut":
        return [
            f"dome panels  = {len(SOCCER.dome_faces)}",
            f"rim corners  = {len(SOCCER.base_vertices)}",
            f"rim high     = {SOCCER.rim_high * LESSON_RADIUS_IN:+.3f} in",
            f"rim low      = {SOCCER.rim_low * LESSON_RADIUS_IN:+.3f} in",
            f"level-up     = {build.base_wobble:.3f} in",
        ]
    if stage in ("hex_goldberg2", "hex_two_struts"):
        gp2 = HexBuild(GP2, LESSON_RADIUS_IN, CONNECTOR_DEDUCTION_IN)
        return [
            f"{name}: x{count}  {centre:.4f} in"
            for name, count, centre, _ in gp2.strut_table()
        ] + [f"hexagon shapes = {GP2.hex_shapes}, regular = {GP2.all_hexagons_regular}"]
    if stage == "hex_size_ladder":
        return [
            f"{cage.notation}: {cage.strut_lengths} lengths, "
            f"{cage.hex_shapes} hex shapes, {len(cage.faces)} panels"
            for cage in (SOCCER, GP2, GP3, GP4)
        ]
    if stage in ("hex_warp", "hex_warp_cost"):
        return [
            f"{cage.notation}: worst warp "
            f"{cage.worst_planarity * LESSON_RADIUS_IN:.5f} in"
            for cage in (SOCCER, GP2, GP3, GP4)
        ]
    if stage in ("hex_compare", "hex_choose"):
        return [
            f"{cage.notation}: {len(cage.dome_faces)} panels, "
            f"{len(cage.dome_edges)} struts, {cage.strut_lengths} lengths"
            for cage in (SOCCER, GP2, GP3, GP4)
        ]
    if stage == "hex_dual":
        return [
            f"2V geodesic: 42 corners, 80 triangles",
            f"its dual   : {len(GP2.faces)} panels, {len(GP2.vertices)} corners",
            f"corners of degree 5 -> {GP2.pentagons} pentagons",
        ]
    return []


SCENES = {
    "hex_flat": scene_hex_flat,
    "hex_flat_angle": scene_hex_flat_angle,
    "hex_deficit": scene_hex_deficit,
    "hex_pentagon_swap": scene_hex_pentagon_swap,
    "hex_euler": scene_hex_euler,
    "hex_soccer": scene_hex_soccer,
    "hex_soccer_struts": scene_hex_soccer_struts,
    "hex_soccer_panels": scene_hex_soccer_panels,
    "hex_soccer_cut": scene_hex_soccer_cut,
    "hex_soccer_build": scene_hex_soccer_build,
    "hex_dual": scene_hex_dual,
    "hex_goldberg2": scene_hex_goldberg2,
    "hex_two_struts": scene_hex_two_struts,
    "hex_size_ladder": scene_hex_size_ladder,
    "hex_warp": scene_hex_warp,
    "hex_warp_cost": scene_hex_warp_cost,
    "hex_compare": scene_hex_compare,
    "hex_skin": scene_hex_skin,
    "hex_choose": scene_hex_choose,
    "hex_finale": scene_hex_finale,
}


CHAPTERS: tuple[Chapter, ...] = (
    Chapter(
        "honeycomb", "01", "The shape everything reaches for",
        "A hexagon encloses the most floor for the least edge that still tiles.",
        (
            "Bees use it, basalt cools into it, and a soap froth settles into it,",
            "because a hexagon walls off more area per foot of wall than a square or",
            "a triangle while still leaving no gap. That is why builders keep",
            "asking for a dome made of hexagons. This lesson answers that request",
            "honestly: what you can have, what you cannot, and exactly what the",
            "difference costs in the shop.",
        ),
        ("hexagon area = 2.598 x side^2", "perimeter per unit area: hexagon beats square"),
        13.0, (90.0, 64.0, 17.0), "hex_flat",
    ),
    Chapter(
        "flat_forever", "02", "A sheet of hexagons will not curve",
        "Three hexagon corners use up all three hundred and sixty degrees.",
        (
            "Stand at any corner of a hexagon tiling and three panels meet there.",
            "Each brings a hundred and twenty degrees, and three of those is exactly",
            "three hundred and sixty: a full turn, flat, with nothing left over.",
            "A surface can only bend where the angle around a corner adds up to",
            "less than a full turn. The regular hexagon has no slack to give, so a",
            "sheet of them stays a sheet no matter how many you add.",
        ),
        ("3 x 120 = 360 deg", "spare angle = 0 -> zero curvature"),
        16.0, (90.0, 56.0, 15.5), "hex_flat_angle",
    ),
    Chapter(
        "buy_curve", "03", "Curvature is bought with missing angle",
        "Cut a wedge out of a flat disc and it has to rise into a cone.",
        (
            "Take a paper disc, cut one wedge out, and pull the two cut edges",
            "together. The paper cannot lie flat any more; it lifts into a cone.",
            "Nothing was stretched. The only thing that changed is that there is",
            "less than a full turn of paper around the centre. That missing angle",
            "is the whole mechanism of curvature, and it is the only currency a",
            "dome has to spend.",
        ),
        ("missing angle -> curvature", "flat = 360 deg   domed < 360 deg"),
        15.0, (90.0, 20.0, 15.0), "hex_deficit",
    ),
    Chapter(
        "pentagon", "04", "The pentagon is where the angle comes from",
        "Swap one hexagon for a pentagon and thirty-six degrees go missing.",
        (
            "A regular pentagon corner is a hundred and eight degrees. Three of",
            "them come to three hundred and twenty-four, which leaves thirty-six",
            "degrees of slack at that corner. Fold the slack out and the surface",
            "pulls into a bowl. Every hexagon dome you have ever seen is doing this:",
            "hexagons carry the field, and pentagons do all of the curving.",
        ),
        ("pentagon corner = 108 deg", "3 x 108 = 324 deg", "spare = 36 deg per pentagon"),
        16.0, (90.0, 38.0, 16.0), "hex_pentagon_swap",
    ),
    Chapter(
        "twelve", "05", "Exactly twelve pentagons. Always.",
        "The hexagon count cancels out of the arithmetic. The pentagon count cannot.",
        (
            "Descartes proved that any closed convex cage is missing exactly seven",
            "hundred and twenty degrees in total, no matter its size. A hexagon",
            "corner contributes nothing to that budget, and each pentagon",
            "contributes sixty. Seven hundred and twenty divided by sixty is twelve.",
            "Run the same argument through Euler's formula and the hexagons cancel",
            "algebraically, leaving the same answer. Twenty hexagons or two thousand,",
            "the cage still closes on exactly twelve pentagons.",
        ),
        ("V - E + F = 2", "F = P + H,  E = (5P + 6H)/2,  V = (5P + 6H)/3",
         "-> P/6 = 2  ->  P = 12", "total deficit = 720 deg = 12 x 60"),
        20.0, (90.0, 20.0, 19.5), "hex_euler",
    ),
    Chapter(
        "one_hexagon", "06", "The single-hexagon dome",
        "Twenty identical hexagons, twelve identical pentagons, ninety identical struts.",
        (
            "This is the cage you want if one shape is the goal: the truncated",
            "icosahedron, the pattern on a football. Every hexagon is regular and",
            "identical to every other. Every pentagon is regular and identical to",
            "every other. And every one of its ninety struts is exactly the same",
            "length, so the whole frame comes off one saw setting. No other",
            "hexagonal cage on a sphere is this kind to a builder.",
        ),
        ("20 hexagons + 12 pentagons = 32 panels", "90 struts, 60 hubs",
         "V - E + F = 60 - 90 + 32 = 2"),
        18.0, (30.0, 26.0, 14.5), "hex_soccer",
    ),
    Chapter(
        "one_strut", "07", "One strut length, cut ninety times",
        "Set the stop block once and every member in the building is right.",
        (
            "Because all ninety struts share one length, the cut list is a single",
            "line. Set a stop block on the saw, cut ninety pieces, and check a",
            "sample against a master gauge rather than a tape. The number the",
            "geometry gives you is hub centre to hub centre, so subtract the",
            "connector allowance for your chosen hub before you cut. Measure that",
            "allowance on a real assembled joint. Do not take it from a catalogue.",
        ),
        ("centre length = chord factor x R", "cut length = centre length - deduction",
         "one length x 90 pieces"),
        18.0, (90.0, 20.0, 17.0), "hex_soccer_struts",
    ),
    Chapter(
        "two_templates", "08", "Two flat templates cut the whole skin",
        "One hexagon jig and one pentagon jig cover all thirty-two panels.",
        (
            "Both panel shapes are genuinely flat: their corners lie in a plane, so",
            "you can cut them from sheet goods with no tricks. Make one full-size",
            "hexagon template and one pentagon template out of a scrap sheet, and",
            "trace every panel from those two. Cut them slightly oversize, fit them",
            "to the raised frame, then trim. The frame is always slightly less",
            "perfect than the arithmetic, and the panel is where you absorb that.",
        ),
        ("hexagon: 6 equal sides, 6 equal corners",
         "pentagon: 5 equal sides, 5 equal corners", "both exactly planar"),
        18.0, (-90.0, 14.0, 12.0), "hex_soccer_panels",
    ),
    Chapter(
        "the_cut", "09", "Where do you cut it off?",
        "A hexagon cage has no level equator, so its rim comes out as a zigzag.",
        (
            "A triangulated dome can be built to have a flat ring of hubs at the",
            "equator. A hexagon cage cannot: no ring of its struts runs level, so",
            "wherever you stop, the bottom edge rises and falls. On a twenty foot",
            "dome that zigzag is over three feet deep. You have two honest options.",
            "Build a level stem wall and let the zigzag sit on top of it, or cut",
            "the bottom row of panels along a chalked level line and flash the cut.",
            "Either way, decide before you cut a single strut.",
        ),
        ("no strut runs level -> the rim steps",
         "rim spread = high corner - low corner",
         "stem wall makes up the difference"),
        21.0, (44.0, 18.0, 15.5), "hex_soccer_cut",
    ),
    Chapter(
        "raise_it", "10", "Raising it, rim to crown",
        "Build complete rings, check the diameter, then close the crown last.",
        (
            "Lay the rim out on the stem wall and bolt the first course of hubs",
            "down. Work upward one complete ring at a time, never up one side, so",
            "error spreads evenly instead of piling up in one place. Measure the",
            "diameter across each finished ring in three directions before you start",
            "the next one. Leave the crown panel until last; it is where every",
            "accumulated millimetre finally shows up, and it is far easier to trim",
            "one panel than to unbolt a ring.",
        ),
        ("ring by ring, never one side at a time",
         "check diameter in three directions per ring", "crown closes last"),
        20.0, (40.0, 24.0, 15.0), "hex_soccer_build",
    ),
    Chapter(
        "bigger", "11", "Now you want it bigger",
        "The single-hexagon cage comes in exactly one pattern. For more, subdivide.",
        (
            "The football cage is a fixed pattern. You can scale it, but you cannot",
            "make it finer, and past about eight metres across its panels get too",
            "big to handle and too flat to look round. To get a finer cage you",
            "subdivide the underlying triangulated sphere and take its dual. That",
            "is the family called Goldberg polyhedra, and it is where the second",
            "half of this lesson lives.",
        ),
        ("GP(1,1) = football, one pattern only",
         "finer cage -> subdivide, then dualise"),
        16.0, (30.0, 28.0, 15.5), "hex_goldberg2",
    ),
    Chapter(
        "dual", "12", "Every triangle corner becomes one panel",
        "The dual swaps corners for panels: five-way corners become the pentagons.",
        (
            "Take a two-frequency geodesic sphere. Mark the centre of every",
            "triangle, then join the centres around each corner. Corners where six",
            "triangles met become hexagons. The twelve corners where only five met",
            "become pentagons. That is the whole operation, and it explains the",
            "twelve directly: they are the twelve corners the icosahedron started",
            "with, and no amount of subdividing ever creates or destroys one.",
        ),
        ("dual: face centres -> new corners",
         "degree-6 corner -> hexagon", "degree-5 corner -> pentagon"),
        19.0, (26.0, 26.0, 14.5), "hex_dual",
    ),
    Chapter(
        "not_regular", "13", "The hexagons are not regular any more",
        "The first subdivision already splits one strut length into two.",
        (
            "Lay a Goldberg hexagon flat next to a football hexagon and the",
            "difference is immediate. Its sides are no longer all equal and its",
            "corners are no longer all a hundred and twenty degrees. It is still a",
            "perfectly good panel and it still tiles the cage, but it is a specific",
            "shape with a specific orientation, and now the strut list has two",
            "lines on it instead of one.",
        ),
        ("GP(2,0): 2 strut lengths",
         "hexagon sides no longer equal", "corners no longer all 120 deg"),
        18.0, (-90.0, 14.0, 13.0), "hex_two_struts",
    ),
    Chapter(
        "ladder", "14", "Every step up multiplies the shapes",
        "Two lengths, then four, then six: the shop work grows faster than the dome.",
        (
            "Go to three frequency and the cage has two distinct hexagon shapes and",
            "four strut lengths. Go to four and it is three shapes and six lengths.",
            "The dome gets rounder and its panels get easier to lift, but every",
            "extra length is another jig, another label, and another chance to",
            "reach for the wrong stick. This is the real trade, and it is worth",
            "making deliberately rather than discovering it halfway through cutting.",
        ),
        ("GP(2,0): 2 lengths, 1 hex shape", "GP(3,0): 4 lengths, 2 hex shapes",
         "GP(4,0): 6 lengths, 3 hex shapes"),
        19.0, (90.0, 18.0, 20.0), "hex_size_ladder",
    ),
    Chapter(
        "warp", "15", "And the panels stop being flat",
        "Six corners on a sphere do not share a plane. The football's do; nobody else's.",
        (
            "Here is the part almost nobody mentions. Three points always define a",
            "plane, so a triangular panel is flat for free. Six points on a sphere",
            "generally do not, so a subdivided hexagon panel is warped: its corners",
            "want to sit slightly out of any flat sheet you cut. The amount is",
            "small, but it is not zero, and it is the reason hexagon domes are",
            "usually skinned with a membrane or with slightly domed panels rather",
            "than with rigid flat sheets.",
        ),
        ("3 points define a plane -> triangles are free",
         "6 points on a sphere generally do not",
         "warp = corner distance from best-fit plane"),
        20.0, (-72.0, 22.0, 12.5), "hex_warp",
    ),
    Chapter(
        "warp_cost", "16", "What the warp actually costs",
        "Measured at a twenty foot dome, so you can decide with a number.",
        (
            "The football cage measures exactly zero: its panels are genuinely flat",
            "and always will be. Every subdivided cage measures more than zero. Put",
            "a flat sheet on a warped opening and you either gap it at two corners",
            "or you spring the sheet and let it take the twist. Both are workable if",
            "you plan for them. Neither is workable if you find out about it with",
            "the crane on site.",
        ),
        ("flat panel + warped opening = a gap to seal",
         "membrane, domed panel, or sprung sheet"),
        18.0, (90.0, 20.0, 19.0), "hex_warp_cost",
    ),
    Chapter(
        "seams", "17", "Three panels, one hub, three seams",
        "Every hub on a hexagon cage is a three-way seam pointed at the sky.",
        (
            "Because every corner is three-way, every hub is a junction of three",
            "panel edges, and on the upper half of the dome those seams point",
            "uphill. Water finds them. Shingle the skin from the rim upward so",
            "every lap sheds downhill, tape or flash each hub, and give yourself an",
            "eave that throws water clear of the wall rather than down it. A dome",
            "leaks at its seams long before it fails at its struts.",
        ),
        ("every corner is 3-way", "3 panel edges meet at each hub",
         "lap from the rim upward"),
        18.0, (44.0, 22.0, 13.5), "hex_skin",
    ),
    Chapter(
        "choose", "18", "Choosing between them",
        "Repeated work is cheap. Varied work is where the mistakes live.",
        (
            "If the dome is small enough that a two metre panel is liftable, take",
            "the football: one strut, two templates, flat panels, no warp. If you",
            "need a bigger or rounder shell, accept the subdivision, but then be",
            "rigorous about labelling, because a four-length dome punishes a",
            "mis-sorted stick far more than a one-length dome does. Colour code the",
            "ends. Do it at the saw, not at the scaffold.",
        ),
        ("small and simple -> GP(1,1)",
         "large and round -> subdivide, then label ruthlessly"),
        18.0, (90.0, 20.0, 20.0), "hex_choose",
    ),
    Chapter(
        "compare", "19", "The two domes, side by side",
        "Same radius, same sphere, completely different day in the shop.",
        (
            "Here they are at the same radius. One is sixteen panels, fifty-five",
            "struts, and a single length. The other is a far rounder shell that",
            "needs six lengths and three hexagon templates. Neither is better. They",
            "are answers to different questions, and the only mistake is choosing",
            "one without knowing which question you asked.",
        ),
        ("same R, same sphere", "different panel count, different cut list"),
        16.0, (90.0, 22.0, 18.0), "hex_compare",
    ),
    Chapter(
        "close", "20", "The whole transformation",
        "A flat sheet, twelve pentagons, and a shell that closes on itself.",
        (
            "Start with a sheet of hexagons that will never curve. Remove sixty",
            "degrees at twelve places and it closes into a sphere. Cut that sphere",
            "where you want a wall, stand it on something level, and skin it from",
            "the rim up. Every number in this lesson came from that one idea, and",
            "every one of them can be recomputed from the geometry rather than",
            "trusted from a table.",
        ),
        ("flat sheet -> 12 pentagons -> closed shell",
         "one radius scales the whole cut list"),
        17.0, (30.0, 32.0, 15.0), "hex_finale",
    ),
)


HEX_LESSON = Lesson(
    key="hex",
    brand="HEX / HEXAGONAL DOME MASTERCLASS",
    title="Hexagonal Dome Masterclass",
    chapters=CHAPTERS,
    scenes=SCENES,
    equations=hex_equations,
    selftest=validate_hex_geometry,
    report=lambda: hex_report(LESSON_RADIUS_IN, CONNECTOR_DEDUCTION_IN),
    snapshot_prefix="hex",
)
