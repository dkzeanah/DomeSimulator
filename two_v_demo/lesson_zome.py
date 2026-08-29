"""The zome masterclass: building with parallelograms, up to a point.

A zome is a zonohedron.  Everything the lesson teaches -- the single strut
length, the flat panels, the level rings, the point at the top -- follows
from one idea: the shape is *swept* along a small star of directions.

Every number on screen comes from :mod:`two_v_demo.zome_geometry`.
"""

from __future__ import annotations

import math

import numpy as np

from .geometry import PHI, normalize
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
from .zome_geometry import (
    Zome,
    ZomeBuild,
    golden_zonohedron,
    polar_generators,
    polar_zonohedron,
    validate_zome_geometry,
    zome_report,
    zonohedron_faces,
)


# The zome the lesson prices: six directions, four-foot struts.
LESSON_COUNT = 6
LESSON_PITCH = 54.0
LESSON_STRUT_IN = 48.0
CONNECTOR_DEDUCTION_IN = 1.5

ZOME = polar_zonohedron(LESSON_COUNT, LESSON_PITCH)
ZOME5 = polar_zonohedron(5, LESSON_PITCH)
ZOME7 = polar_zonohedron(7, LESSON_PITCH)
TALL = polar_zonohedron(LESSON_COUNT, 34.0)
WIDE = polar_zonohedron(LESSON_COUNT, 70.0)
GOLDEN = golden_zonohedron()

PANEL_COLORS = (CYAN, AMBER, GREEN, PURPLE, (0.95, 0.45, 0.75, 1.0))
# Every model in this lesson is drawn at unit strut length, so one world
# unit is one strut and nothing needs re-scaling between scenes.
GROUND_LIFT = 3.75


def _panel_colour(zome: Zome, face_index: int):
    names = tuple(item.name for item in zome.rhombus_classes)
    return PANEL_COLORS[names.index(zome.rhombus_class_of[face_index]) % len(PANEL_COLORS)]


def _to_rgb(colour) -> tuple[int, int, int]:
    return (int(colour[0] * 255), int(colour[1] * 255), int(colour[2] * 255))


# ----------------------------------------------------------------------
# Drawing helpers
# ----------------------------------------------------------------------

def zonotope(generators: np.ndarray):
    """Vertices, edges and faces of the solid swept by *generators*.

    Handles the two degenerate starts the sweep animation needs: one
    direction is a stick, two directions are a single parallelogram.
    """
    count = len(generators)
    if count == 1:
        points = np.array([-generators[0], generators[0]])
        return points, ((0, 1),), ()
    if count == 2:
        a, b = generators[0], generators[1]
        points = np.array([-a - b, a - b, a + b, -a + b])
        return points, ((0, 1), (1, 2), (2, 3), (3, 0)), ((0, 1, 2, 3),)
    vertices, faces, edges = zonohedron_faces(generators)
    return vertices, edges, faces


def draw_solid(
    app,
    opaque: TriangleBatch,
    transparent: TriangleBatch,
    vertices: np.ndarray,
    edges,
    faces,
    offset: np.ndarray,
    colour,
    *,
    scale: float = 1.0,
    alpha: float = 0.18,
    strut_radius: float = 0.055,
    node_radius: float = 0.075,
    reveal: float = 1.0,
    panel_colour=None,
) -> None:
    """Draw one zonohedron: filled panels, then the frame over the top."""
    edge_list = list(edges)
    face_list = list(faces)
    shown_faces = int(math.ceil(len(face_list) * clamp(reveal)))
    for index, face in enumerate(face_list[:shown_faces]):
        points = [vertices[corner] * scale + offset for corner in face]
        middle = sum(points) / len(points)
        tint = panel_colour(index) if panel_colour else colour
        fill = (tint[0], tint[1], tint[2], alpha)
        outward = normalize(middle - offset)
        for position in range(len(points)):
            transparent.triangle(middle, points[position],
                                 points[(position + 1) % len(points)],
                                 fill, outward)
    shown_edges = int(math.ceil(len(edge_list) * clamp(reveal)))
    for a, b in edge_list[:shown_edges]:
        opaque.cylinder(vertices[a] * scale + offset,
                        vertices[b] * scale + offset,
                        strut_radius, colour, 8)
    if node_radius > 0.0:
        corners = sorted({index for edge in edge_list[:shown_edges] for index in edge})
        for index in corners:
            opaque.sphere(vertices[index] * scale + offset, node_radius,
                          (0.80, 0.88, 0.94, 1.0), 4, 8)


def draw_zome(
    app,
    opaque: TriangleBatch,
    transparent: TriangleBatch,
    zome: Zome,
    offset: np.ndarray,
    *,
    faces=None,
    edges=None,
    scale: float = 1.0,
    alpha: float = 0.18,
    reveal: float = 1.0,
    strut_radius: float = 0.055,
    node_radius: float = 0.075,
    frame_colour=None,
    by_panel_class: bool = True,
) -> None:
    face_indices = list(range(len(zome.faces)) if faces is None else faces)
    chosen_faces = [zome.faces[index] for index in face_indices]
    if edges is None:
        kept: set[tuple[int, int]] = set()
        for face in chosen_faces:
            for position in range(4):
                a, b = face[position], face[(position + 1) % 4]
                kept.add((a, b) if a < b else (b, a))
        edges = tuple(sorted(kept))
    draw_solid(
        app, opaque, transparent, zome.vertices, edges, chosen_faces, offset,
        frame_colour or CYAN, scale=scale, alpha=alpha,
        strut_radius=strut_radius, node_radius=node_radius, reveal=reveal,
        panel_colour=(
            (lambda index: _panel_colour(zome, face_indices[index]))
            if by_panel_class else None
        ),
    )


def draw_flat_rhombus(
    app,
    opaque: TriangleBatch,
    transparent: TriangleBatch,
    zome: Zome,
    face_index: int,
    centre: np.ndarray,
    scale: float,
    colour,
    label: str | None = None,
    facing: float = -1.0,
) -> None:
    """Stand one panel up as a full-size template, in its true shape."""
    points = zome.vertices[list(zome.faces[face_index])]
    middle = points.mean(axis=0)
    centred = points - middle
    _, _, right = np.linalg.svd(centred, full_matrices=False)
    laid = [
        centre + np.array([
            float(np.dot(point, right[0])) * scale,
            0.0,
            float(np.dot(point, right[1])) * scale,
        ])
        for point in centred
    ]
    normal = np.array([0.0, facing, 0.0])
    fill = (colour[0], colour[1], colour[2], 0.22)
    for position in range(4):
        a, b = laid[position], laid[(position + 1) % 4]
        transparent.triangle(centre, a, b, fill, normal)
        opaque.cylinder(a, b, 0.055, colour, 8)
    # Both diagonals, because that is how a rhombus gets set out on a bench.
    opaque.cylinder(laid[0], laid[2], 0.022, MUTED, 5)
    opaque.cylinder(laid[1], laid[3], 0.022, MUTED, 5)
    if label:
        app.world_labels.append(WorldLabel(centre, label, _to_rgb(colour)))


def draw_star(
    app,
    opaque: TriangleBatch,
    generators: np.ndarray,
    origin: np.ndarray,
    colour,
    *,
    reveal: float = 1.0,
    radius: float = 0.04,
    label_them: bool = False,
) -> None:
    shown = int(math.ceil(len(generators) * clamp(reveal)))
    for index in range(shown):
        tip = origin + generators[index]
        opaque.arrow(origin, tip, radius, colour)
        if label_them:
            app.world_labels.append(WorldLabel(tip, f"g{index + 1}", _to_rgb(colour)))


def ground_offset(zome: Zome, x: float = 0.0, y: float = 0.0) -> np.ndarray:
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
        opaque.cylinder(a, b, thickness, colour, 5)


# ----------------------------------------------------------------------
# Act one -- the one idea
# ----------------------------------------------------------------------

def scene_zome_hero(app, opaque, transparent, p: float) -> None:
    draw_zome(app, opaque, transparent, ZOME, ground_offset(ZOME),
              reveal=smoothstep(p * 1.4), strut_radius=0.062, alpha=0.17)
    build = ZomeBuild(ZOME, LESSON_STRUT_IN, CONNECTOR_DEDUCTION_IN)
    apex = ZOME.vertices[ZOME.apex_index] + ground_offset(ZOME)
    app.world_labels.extend([
        WorldLabel(apex + np.array([-1.7, 0.0, -0.35]), "ONE POINT", (111, 235, 155)),
        WorldLabel(np.array([0.0, 0.0, -0.9]),
                   f"{len(ZOME.faces)} PARALLELOGRAMS   {len(ZOME.edges)} STRUTS"
                   f"   {len(ZOME.strut_lengths)} LENGTH", (61, 211, 255)),
    ])


def scene_zome_sweep(app, opaque, transparent, p: float) -> None:
    """Point, stick, panel, solid: the sweep that makes a zome, in four steps."""
    generators = polar_generators(LESSON_COUNT, LESSON_PITCH)
    stages = 4
    local = clamp(p * 1.08) * stages
    step = min(stages - 1, int(local))
    fraction = ease_in_out(clamp(local - step))
    used = step + 1
    base_vertices, base_edges, base_faces = zonotope(generators[:used])
    travel = generators[used] * fraction if used < len(generators) else np.zeros(3)
    origin = np.array([-3.0, 0.0, 2.9])

    zoom = 1.75
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
    draw_star(app, opaque, generators[:used] * zoom, origin, GREEN, radius=0.03)
    captions = (
        "ONE DIRECTION -> A STICK",
        "TWO DIRECTIONS -> A PARALLELOGRAM",
        "THREE DIRECTIONS -> A SOLID",
        "SIX DIRECTIONS -> A ZOME",
    )
    app.world_labels.append(WorldLabel(
        origin + np.array([0.0, 0.0, 4.6]), captions[step], (111, 235, 155),
    ))


def scene_zome_parallelogram(app, opaque, transparent, p: float) -> None:
    """Two directions define a plane, so the panel they sweep is always flat."""
    origin = np.array([-2.4, 0.0, 2.4])
    a = np.array([2.3, 0.0, 0.0])
    b = np.array([0.75, 0.0, 2.05])
    grow = ease_in_out(clamp((p - 0.08) / 0.7))
    corners = [origin, origin + a, origin + a + b * grow, origin + b * grow]
    normal = np.array([0.0, -1.0, 0.0])
    middle = sum(corners) / 4.0
    for position in range(4):
        transparent.triangle(middle, corners[position], corners[(position + 1) % 4],
                             (0.15, 0.82, 1.00, 0.20), normal)
    for position in range(4):
        opaque.cylinder(corners[position], corners[(position + 1) % 4], 0.06, CYAN, 8)
    opaque.arrow(origin, origin + a, 0.035, AMBER)
    opaque.arrow(origin, origin + b * max(grow, 0.02), 0.035, GREEN)
    app.world_labels.extend([
        WorldLabel(origin + a * 0.5 + np.array([0.0, 0.0, -0.5]),
                   "direction a", (255, 177, 62)),
        WorldLabel(origin + b * grow * 0.5 + np.array([-0.8, 0.0, 0.0]),
                   "direction b", (111, 235, 155)),
        WorldLabel(middle, "OPPOSITE SIDES EQUAL AND PARALLEL\n"
                           "FOUR CORNERS IN ONE PLANE, ALWAYS", (61, 211, 255)),
    ])


def scene_zome_rhombus(app, opaque, transparent, p: float) -> None:
    """Equal directions turn every parallelogram into a rhombus."""
    for index, (label, ratio, tint, x) in enumerate((
        ("UNEQUAL DIRECTIONS\nparallelogram\n4 sides, 2 lengths", 0.55, AMBER, 2.6),
        ("EQUAL DIRECTIONS\nrhombus\n4 sides, 1 length", 1.0, CYAN, -3.1),
    )):
        origin = np.array([x, 0.0, 1.5])
        a = np.array([2.0, 0.0, 0.0])
        b = np.array([2.0 * ratio * math.cos(math.radians(62.0)), 0.0,
                      2.0 * ratio * math.sin(math.radians(62.0))])
        corners = [origin, origin + a, origin + a + b, origin + b]
        middle = sum(corners) / 4.0
        normal = np.array([0.0, -1.0, 0.0])
        for position in range(4):
            transparent.triangle(middle, corners[position],
                                 corners[(position + 1) % 4],
                                 (tint[0], tint[1], tint[2], 0.18), normal)
            opaque.cylinder(corners[position], corners[(position + 1) % 4],
                            0.06, tint, 8)
        app.world_labels.append(WorldLabel(middle, label, _to_rgb(tint)))
    app.world_labels.append(WorldLabel(
        np.array([-0.3, 0.0, 5.1]),
        "ONE STRUT LENGTH IS A CHOICE YOU MAKE AT THE STAR", (111, 235, 155),
    ))


def scene_zome_star(app, opaque, transparent, p: float) -> None:
    """The star of directions, and the pitch angle that sets the shape."""
    generators = polar_generators(LESSON_COUNT, LESSON_PITCH)
    origin = np.array([-2.2, 0.0, 1.1])
    draw_star(app, opaque, generators, origin, CYAN,
              reveal=smoothstep(p * 1.5), radius=0.042, label_them=True)
    opaque.arrow(origin, origin + np.array([0.0, 0.0, 2.4]), 0.028, MUTED)
    # The cone the directions ride on.
    pitch = math.radians(LESSON_PITCH)
    for step in range(48):
        angle_a = math.tau * step / 48
        angle_b = math.tau * (step + 1) / 48
        ring_a = origin + np.array([math.sin(pitch) * math.cos(angle_a),
                                    math.sin(pitch) * math.sin(angle_a),
                                    math.cos(pitch)])
        ring_b = origin + np.array([math.sin(pitch) * math.cos(angle_b),
                                    math.sin(pitch) * math.sin(angle_b),
                                    math.cos(pitch)])
        opaque.cylinder(ring_a, ring_b, 0.016, (0.42, 0.52, 0.62, 1.0), 5)
    app.world_labels.extend([
        WorldLabel(origin + np.array([0.0, 0.0, 2.7]), "axis", (145, 165, 182)),
        WorldLabel(origin + np.array([0.0, 0.0, -0.85]),
                   f"{LESSON_COUNT} EQUAL DIRECTIONS, EVENLY SPACED\n"
                   f"pitch {LESSON_PITCH:.1f} deg from the axis", (61, 211, 255)),
    ])


def scene_zome_counts(app, opaque, transparent, p: float) -> None:
    """Every part count is a formula in the number of directions."""
    reveal = smoothstep(min(1.0, p * 1.4))
    for index, (zome, notation) in enumerate(
        ((ZOME5, "5 directions"), (ZOME, "6 directions"), (ZOME7, "7 directions"))
    ):
        if reveal < (index + 0.1) / 3.0:
            continue
        x = 4.2 - index * 6.0
        offset = ground_offset(zome, x)
        draw_zome(app, opaque, transparent, zome, offset, scale=0.62,
                  alpha=0.14, strut_radius=0.035, node_radius=0.045)
        count = zome.generator_count
        app.world_labels.append(WorldLabel(
            np.array([x, 0.0, -1.0]),
            f"{notation}\n{len(zome.faces)} panels = n(n-1)\n"
            f"{len(zome.edges)} struts = 2n(n-1)\n"
            f"{len(zome.vertices)} hubs = n(n-1)+2",
            (61, 211, 255),
        ))
    app.world_labels.append(WorldLabel(
        np.array([-1.8, 0.0, 6.2]),
        "NOTHING HERE IS LOOKED UP -- IT ALL FALLS OUT OF n",
        (111, 235, 155),
    ))


def scene_zome_apex(app, opaque, transparent, p: float) -> None:
    """The point at the top, and the angle that is missing there."""
    offset = ground_offset(ZOME)
    lift = ease_in_out(clamp((p - 0.18) / 0.66)) * 1.2
    others = [index for index in range(len(ZOME.faces)) if index not in ZOME.apex_faces]
    draw_zome(app, opaque, transparent, ZOME, offset, faces=others,
              alpha=0.08, strut_radius=0.04, node_radius=0.05,
              frame_colour=(0.34, 0.45, 0.55, 1.0), by_panel_class=False)
    apex = ZOME.vertices[ZOME.apex_index]
    for face_index in ZOME.apex_faces:
        face = ZOME.faces[face_index]
        points = [ZOME.vertices[corner] + offset for corner in face]
        direction = normalize(
            sum(points) / 4.0 - (apex + offset) + np.array([0.0, 0.0, 0.001])
        )
        points = [point + direction * lift for point in points]
        middle = sum(points) / 4.0
        for position in range(4):
            transparent.triangle(middle, points[position], points[(position + 1) % 4],
                                 (1.00, 0.67, 0.20, 0.30), normalize(middle - offset))
            opaque.cylinder(points[position], points[(position + 1) % 4],
                            0.05, AMBER, 8)
    opaque.sphere(apex + offset, 0.16, RED, 6, 10)
    app.world_labels.extend([
        WorldLabel(apex + offset + np.array([0.0, 0.0, 1.0 + lift]),
                   f"{len(ZOME.apex_faces)} PANELS, ONE POINT", (255, 87, 94)),
        WorldLabel(np.array([0.0, 0.0, 0.6]),
                   f"corners used {ZOME.apex_angle_sum:.3f} deg\n"
                   f"missing {360.0 - ZOME.apex_angle_sum:.3f} deg -> it closes",
                   (111, 235, 155)),
    ])


def scene_zome_rings(app, opaque, transparent, p: float) -> None:
    """Every hub in a ring is at exactly the same height."""
    offset = ground_offset(ZOME)
    draw_zome(app, opaque, transparent, ZOME, offset, alpha=0.09,
              strut_radius=0.042, node_radius=0.06,
              frame_colour=(0.38, 0.50, 0.60, 1.0), by_panel_class=False)
    shown = int(math.ceil(len(ZOME.level_rings) * smoothstep(min(1.0, p * 1.5))))
    for index, level in enumerate(ZOME.level_rings[:shown]):
        members = [
            corner for corner in range(len(ZOME.vertices))
            if abs(float(ZOME.vertices[corner][2]) - level) <= 1e-9
        ]
        tint = CYAN if index % 2 else AMBER
        radius = max(0.30, max(
            float(np.linalg.norm(ZOME.vertices[corner][:2])) for corner in members
        ))
        level_ring(opaque, offset, radius, level + offset[2],
                   (tint[0], tint[1], tint[2], 0.85))
        for corner in members:
            opaque.sphere(ZOME.vertices[corner] + offset, 0.10, tint, 5, 9)
    build = ZomeBuild(ZOME, LESSON_STRUT_IN, CONNECTOR_DEDUCTION_IN)
    spacing = (ZOME.level_rings[1] - ZOME.level_rings[0]) * build.scale
    app.world_labels.append(WorldLabel(
        np.array([0.0, 0.0, -0.95]),
        f"{len(ZOME.level_rings)} LEVEL RINGS, EVERY STEP {spacing:.3f} in",
        (111, 235, 155),
    ))


def scene_zome_shapes(app, opaque, transparent, p: float) -> None:
    """Every panel template the zome needs, laid flat and dimensioned."""
    build = ZomeBuild(ZOME, LESSON_STRUT_IN, CONNECTOR_DEDUCTION_IN)
    classes = ZOME.rhombus_classes
    reveal = smoothstep(min(1.0, p * 1.5))
    positions = np.linspace(-2.6, 6.6, len(classes))
    for index, item in enumerate(classes):
        if reveal < (index + 0.1) / len(classes):
            continue
        face_index = ZOME.rhombus_class_of.index(item.name)
        colour = PANEL_COLORS[index % len(PANEL_COLORS)]
        draw_flat_rhombus(
            app, opaque, transparent, ZOME, face_index,
            np.array([float(positions[index]), 0.0, 3.0]), 1.25, colour,
            f"{item.name}   x{item.count}\n"
            f"acute {item.acute_deg:.3f} deg\n"
            f"diagonals {item.short_diagonal * build.scale:.2f}"
            f" x {item.long_diagonal * build.scale:.2f} in",
            facing=1.0,
        )
    app.world_labels.append(WorldLabel(
        np.array([2.0, 0.0, 5.9]),
        f"{len(classes)} TEMPLATES FOR ALL {len(ZOME.faces)} PANELS",
        (111, 235, 155),
    ))


def scene_zome_pitch(app, opaque, transparent, p: float) -> None:
    """Same struts, same count -- pitch alone decides tall or wide."""
    reveal = smoothstep(min(1.0, p * 1.4))
    for index, (zome, label) in enumerate(
        ((TALL, "pitch 34 deg"), (ZOME, "pitch 54 deg"), (WIDE, "pitch 70 deg"))
    ):
        if reveal < (index + 0.1) / 3.0:
            continue
        x = 4.6 - index * 6.2
        offset = ground_offset(zome, x)
        draw_zome(app, opaque, transparent, zome, offset, scale=0.60,
                  alpha=0.13, strut_radius=0.034, node_radius=0.042)
        build = ZomeBuild(zome, LESSON_STRUT_IN, CONNECTOR_DEDUCTION_IN)
        app.world_labels.append(WorldLabel(
            np.array([x, 0.0, -1.05]),
            f"{label}\nheight {build.full_height:.1f} in\n"
            f"widest {build.widest_diameter:.1f} in\n"
            f"still {len(zome.strut_lengths)} strut length",
            (61, 211, 255),
        ))
    app.world_labels.append(WorldLabel(
        np.array([-1.6, 0.0, 6.2]),
        "ONE KNOB, AND IT COSTS NOTHING IN THE SHOP", (111, 235, 155),
    ))


def scene_zome_hubs(app, opaque, transparent, p: float) -> None:
    """Colour every hub by how many struts arrive at it."""
    offset = ground_offset(ZOME)
    draw_zome(app, opaque, transparent, ZOME, offset, alpha=0.09,
              strut_radius=0.045, node_radius=0.0,
              frame_colour=(0.40, 0.52, 0.62, 1.0), by_panel_class=False)
    incident: dict[int, int] = {index: 0 for index in range(len(ZOME.vertices))}
    for a, b in ZOME.edges:
        incident[a] += 1
        incident[b] += 1
    reveal = smoothstep(min(1.0, p * 1.5))
    hub_names = {}
    for hub in ZOME.hub_classes:
        hub_names.setdefault(hub.strut_count, hub)
    for index in range(len(ZOME.vertices)):
        if index / len(ZOME.vertices) > reveal:
            continue
        degree = incident[index]
        colour = {3: CYAN, 4: AMBER, 5: GREEN}.get(degree, RED)
        opaque.sphere(ZOME.vertices[index] + offset, 0.055 + degree * 0.022,
                      colour, 5, 10)
    for order, hub in enumerate(ZOME.hub_classes):
        colour = {3: CYAN, 4: AMBER, 5: GREEN}.get(hub.strut_count, RED)
        app.world_labels.append(WorldLabel(
            np.array([-4.4, 0.0, 5.4 - order * 0.95]),
            f"{hub.name}  x{hub.hub_count}  {hub.strut_count} struts  "
            f"deficit {hub.deficit_deg:.2f} deg",
            _to_rgb(colour),
        ))


def scene_zome_floor(app, opaque, transparent, p: float) -> None:
    """The floor line: no horizontal struts, but one repeated cut."""
    offset = roof_offset(ZOME)
    draw_zome(app, opaque, transparent, ZOME, offset, faces=ZOME.dome_faces,
              alpha=0.15, strut_radius=0.052, node_radius=0.07)
    rim = ZOME.rim_vertices
    for edge in ZOME.boundary_edges:
        a, b = (ZOME.vertices[index] + offset for index in edge)
        opaque.cylinder(a, b, 0.09, RED, 10)
    cut_height = (ZOME.rim_levels[0] + ZOME.rim_levels[-1]) * 0.5
    cut = ZOME.level_cut(cut_height)
    radius = max(float(np.linalg.norm(ZOME.vertices[index][:2])) for index in rim) + 0.5
    level_ring(opaque, offset, radius, cut_height + offset[2], GREEN,
               segments=52, thickness=0.05)
    app.world_labels.extend([
        WorldLabel(np.array([0.0, 0.0, cut_height + offset[2] + 3.4]),
                   f"RIM STEPS BETWEEN {len(ZOME.rim_levels)} HEIGHTS",
                   (255, 87, 94)),
        WorldLabel(np.array([0.0, 0.0, cut_height + offset[2] - 0.75]),
                   f"LEVEL LINE CROSSES {cut.strut_count} STRUTS, "
                   f"{cut.distinct_cuts} CUT SETTING", (111, 235, 155)),
    ])


def scene_zome_cutlist(app, opaque, transparent, p: float) -> None:
    """The rack: one length, cut once, for the whole roof."""
    build = ZomeBuild(ZOME, LESSON_STRUT_IN, CONNECTOR_DEDUCTION_IN)
    offset = roof_offset(ZOME, -2.6)
    draw_zome(app, opaque, transparent, ZOME, offset, faces=ZOME.dome_faces,
              alpha=0.15, strut_radius=0.05, node_radius=0.065)
    name, count, centre_length, cut_length = build.strut_table()[0]
    reveal = int(count * smoothstep(clamp((p - 0.12) / 0.82)))
    for index in range(reveal):
        column, row = index % 10, index // 10
        x = -7.6 + column * 0.66
        y = 7.2 + row * 1.0
        opaque.cylinder(np.array([x, y, 0.20]), np.array([x, y, 1.95]),
                        0.05, CYAN, 6)
    app.world_labels.extend([
        WorldLabel(np.array([-4.4, 7.2, 2.55]),
                   f"{reveal:02d} / {count} STRUTS", (61, 211, 255)),
        WorldLabel(np.array([-4.4, 9.2, 2.55]),
                   f"centre {centre_length:.3f} in   "
                   f"cut {cut_length:.3f} in", (169, 188, 203)),
    ])


def scene_zome_golden(app, opaque, transparent, p: float) -> None:
    """Thirty identical golden rhombi: the one-panel zome."""
    offset = ground_offset(GOLDEN)
    draw_zome(app, opaque, transparent, GOLDEN, offset,
              reveal=smoothstep(p * 1.4), alpha=0.17, strut_radius=0.058)
    item = GOLDEN.rhombus_classes[0]
    draw_flat_rhombus(app, opaque, transparent, GOLDEN, 0,
                      np.array([-6.2, 0.0, 3.6]), 1.35, AMBER,
                      f"ONE PANEL SHAPE\nx{item.count}\n"
                      f"acute {item.acute_deg:.4f} deg\n"
                      f"diagonals {item.long_diagonal / item.short_diagonal:.6f} : 1")
    app.world_labels.append(WorldLabel(
        np.array([0.0, 0.0, -0.95]),
        f"DIAGONAL RATIO = PHI = {PHI:.6f}", (111, 235, 155),
    ))


def scene_zome_golden_cost(app, opaque, transparent, p: float) -> None:
    """Where the golden zome charges you: the hub rings are uneven."""
    for index, (zome, label, x) in enumerate((
        (ZOME, "POLAR ZOME", 3.6), (GOLDEN, "GOLDEN ZOME", -3.6)
    )):
        offset = ground_offset(zome, x)
        draw_zome(app, opaque, transparent, zome, offset, scale=0.66,
                  alpha=0.10, strut_radius=0.032, node_radius=0.05,
                  frame_colour=(0.40, 0.52, 0.62, 1.0), by_panel_class=False)
        steps = [
            zome.level_rings[k + 1] - zome.level_rings[k]
            for k in range(len(zome.level_rings) - 1)
        ]
        for level in zome.level_rings:
            height = level * 0.66 + offset[2]
            radius = max(0.3, max(
                float(np.linalg.norm(zome.vertices[corner][:2])) * 0.66
                for corner in range(len(zome.vertices))
                if abs(float(zome.vertices[corner][2]) - level) <= 1e-9
            ))
            tint = CYAN if index else AMBER
            level_ring(opaque, offset, radius, height, tint,
                       segments=40, thickness=0.02)
        even = max(steps) - min(steps) <= 1e-9
        gaps = [
            zome.level_cut((zome.level_rings[k] + zome.level_rings[k + 1]) * 0.5)
            for k in range(len(zome.level_rings) - 1)
        ]
        awkward = sum(1 for gap in gaps if not gap.one_repeated_cut)
        app.world_labels.append(WorldLabel(
            np.array([x, 0.0, -1.05]),
            f"{label}\nrings evenly spaced: {'yes' if even else 'no'}\n"
            f"bands needing 2 cuts: {awkward} of {len(gaps)}",
            (61, 211, 255) if index else (255, 177, 62),
        ))
    app.world_labels.append(WorldLabel(
        np.array([0.0, 0.0, 6.0]),
        "ONE PANEL SHAPE, PAID FOR AT THE FLOOR", (111, 235, 155),
    ))


def scene_zome_raise(app, opaque, transparent, p: float) -> None:
    """Build it in tiers, because that is how the geometry hands it to you."""
    offset = roof_offset(ZOME)
    reveal = smoothstep(p)
    ordered = sorted(
        ZOME.dome_faces,
        key=lambda index: float(np.mean(ZOME.vertices[list(ZOME.faces[index]), 2])),
    )
    count = int(math.ceil(len(ordered) * reveal))
    draw_zome(app, opaque, transparent, ZOME, offset, faces=ordered[:count],
              alpha=0.17, strut_radius=0.055, node_radius=0.075)
    app.world_labels.append(WorldLabel(
        np.array([0.0, 0.0, ZOME.dome_height + offset[2] + 0.85]),
        f"TIER BY TIER   {count:02d} / {len(ordered)} PANELS", (111, 235, 155),
    ))


def scene_zome_openings(app, opaque, transparent, p: float) -> None:
    """A door and a window taken out of the rhombus wall."""
    offset = roof_offset(ZOME)
    # Take the openings out of the wall the camera is looking at, lowest
    # panel first, so a door reads as a door rather than as a skylight.
    bearing = np.array([math.cos(math.radians(56.0)), math.sin(math.radians(56.0))])

    def facing(index: int) -> float:
        centre = ZOME.vertices[list(ZOME.faces[index])].mean(axis=0)[:2]
        return float(np.dot(normalize(np.append(centre, 0.0))[:2], bearing))

    front = [index for index in ZOME.dome_faces if facing(index) > 0.55]
    removed = sorted(
        front or list(ZOME.dome_faces),
        key=lambda index: float(np.mean(ZOME.vertices[list(ZOME.faces[index]), 2])),
    )[:2]
    kept = [index for index in ZOME.dome_faces if index not in removed]
    draw_zome(app, opaque, transparent, ZOME, offset, faces=kept,
              alpha=0.16, strut_radius=0.052, node_radius=0.07)
    swing = ease_in_out(clamp((p - 0.18) / 0.64))
    for face_index in removed:
        face = ZOME.faces[face_index]
        points = [ZOME.vertices[corner] + offset for corner in face]
        hinge = points[0]
        opened = [
            hinge + (point - hinge) * 1.0 + np.array([0.0, -swing * 1.6, 0.0])
            for point in points
        ]
        middle = sum(opened) / 4.0
        for position in range(4):
            transparent.triangle(middle, opened[position], opened[(position + 1) % 4],
                                 (0.32, 0.91, 0.58, 0.28), np.array([0.0, -1.0, 0.0]))
            opaque.cylinder(opened[position], opened[(position + 1) % 4],
                            0.05, GREEN, 8)
    app.world_labels.append(WorldLabel(
        np.array([0.0, 0.0, ZOME.dome_height + offset[2] + 0.85]),
        "A WHOLE PANEL IS THE OPENING -- NO STRUT IS CUT", (111, 235, 155),
    ))


def scene_zome_versus(app, opaque, transparent, p: float) -> None:
    """The zome beside the triangulated dome it is usually confused with."""
    from .geometry import build_demo_geometry

    geometry = build_demo_geometry()
    reveal = smoothstep(min(1.0, p * 1.4))
    dome_scale = 3.4
    dome_offset = np.array([3.8, 0.0, 0.1])
    app.add_edges(opaque, geometry.vertices, geometry.hemisphere_edges,
                  dome_scale, dome_offset, AMBER, 0.045, None, reveal)
    app.add_nodes(opaque, geometry.vertices, dome_scale, dome_offset,
                  (0.80, 0.88, 0.94, 1.0), 0.06,
                  sorted({i for edge in geometry.hemisphere_edges for i in edge}))
    offset = ground_offset(ZOME, -4.4)
    draw_zome(app, opaque, transparent, ZOME, offset, faces=ZOME.dome_faces,
              scale=0.72, alpha=0.14, strut_radius=0.042, node_radius=0.055,
              reveal=reveal)
    app.world_labels.extend([
        WorldLabel(np.array([3.8, 0.0, -1.0]),
                   "2V GEODESIC DOME\ntriangles, 2 strut lengths\n"
                   "flat panels, level base ring", (255, 177, 62)),
        WorldLabel(np.array([-4.4, 0.0, -1.0]),
                   f"POLAR ZOME\nrhombi, {len(ZOME.strut_lengths)} strut length\n"
                   f"flat panels, level hub rings", (61, 211, 255)),
        WorldLabel(np.array([-0.3, 0.0, 6.2]),
                   "BOTH CLOSE. THEY CLOSE FOR DIFFERENT REASONS.",
                   (111, 235, 155)),
    ])


def scene_zome_finale(app, opaque, transparent, p: float) -> None:
    generators = polar_generators(LESSON_COUNT, LESSON_PITCH)
    offset = ground_offset(ZOME)
    if p < 0.26:
        local = p / 0.26
        draw_star(app, opaque, generators, np.array([0.0, 0.0, 2.6]), CYAN,
                  reveal=smoothstep(local), radius=0.045)
    elif p < 0.62:
        local = (p - 0.26) / 0.36
        draw_zome(app, opaque, transparent, ZOME, offset,
                  reveal=smoothstep(local), alpha=0.16, strut_radius=0.055)
    else:
        local = (p - 0.62) / 0.38
        draw_zome(app, opaque, transparent, ZOME, offset,
                  faces=ZOME.dome_faces, alpha=0.19, strut_radius=0.06,
                  reveal=smoothstep(local))
    app.world_labels.append(WorldLabel(
        np.array([0.0, 0.0, 8.0]),
        "A STAR OF DIRECTIONS  ->  A ROOM WITH A POINT ON IT",
        (111, 235, 155),
    ))


# ----------------------------------------------------------------------
# Live figures
# ----------------------------------------------------------------------

def zome_equations(app, stage: str) -> list[str]:
    build = ZomeBuild(ZOME, LESSON_STRUT_IN, CONNECTOR_DEDUCTION_IN)
    count = ZOME.generator_count
    if stage in ("zome_hero", "zome_finale"):
        return [
            f"directions n   = {count}",
            f"panels         = {len(ZOME.faces)}",
            f"struts         = {len(ZOME.edges)}  in {len(ZOME.strut_lengths)} length",
            f"hubs           = {len(ZOME.vertices)}",
            f"panel shapes   = {ZOME.panel_shapes}",
        ]
    if stage == "zome_counts":
        return [
            f"n = {zome.generator_count}: F {len(zome.faces)}  E {len(zome.edges)}"
            f"  V {len(zome.vertices)}  V-E+F = {zome.euler}"
            for zome in (ZOME5, ZOME, ZOME7)
        ]
    if stage == "zome_apex":
        return [
            f"panels at the point = {len(ZOME.apex_faces)}",
            f"corner angles used  = {ZOME.apex_angle_sum:.4f} deg",
            f"angle missing       = {360.0 - ZOME.apex_angle_sum:.4f} deg",
        ]
    if stage == "zome_rings":
        step = (ZOME.level_rings[1] - ZOME.level_rings[0]) * build.scale
        return [
            f"hub rings      = {len(ZOME.level_rings)}",
            f"ring spacing   = {step:.4f} in, every step",
            f"total height   = {build.full_height:.3f} in",
        ]
    if stage == "zome_shapes":
        return [
            f"{item.name}: x{item.count}  acute {item.acute_deg:.3f} deg  "
            f"diag {item.short_diagonal * build.scale:.2f} x "
            f"{item.long_diagonal * build.scale:.2f} in"
            for item in ZOME.rhombus_classes
        ]
    if stage == "zome_pitch":
        return [
            f"pitch {zome.pitch_deg:.0f} deg: height "
            f"{ZomeBuild(zome, LESSON_STRUT_IN).full_height:7.2f} in, "
            f"widest {ZomeBuild(zome, LESSON_STRUT_IN).widest_diameter:7.2f} in"
            for zome in (TALL, ZOME, WIDE)
        ]
    if stage == "zome_hubs":
        return [
            f"{hub.name}: x{hub.hub_count}  {hub.strut_count} struts  "
            f"corners {hub.angle_sum_deg:.3f} deg"
            for hub in ZOME.hub_classes
        ]
    if stage == "zome_floor":
        cut = ZOME.level_cut((ZOME.rim_levels[0] + ZOME.rim_levels[-1]) * 0.5)
        return [
            f"rim heights   = {len(ZOME.rim_levels)}",
            f"rim step      = {ZOME.rim_wobble * build.scale:.3f} in",
            f"struts cut    = {cut.strut_count}",
            f"cut settings  = {cut.distinct_cuts}",
            f"floor area    = {build.floor_area / 144.0:.2f} sq ft",
        ]
    if stage == "zome_cutlist":
        rows = [
            f"{name}: x{amount}  centre {centre:.3f} in  cut {cut:.3f} in"
            for name, amount, centre, cut in build.strut_table()
        ]
        rows.append(f"roof height = {build.height:.3f} in")
        rows.append(f"floor radius = {build.floor_radius:.3f} in")
        return rows
    if stage in ("zome_golden", "zome_golden_cost"):
        item = GOLDEN.rhombus_classes[0]
        return [
            f"panels        = {len(GOLDEN.faces)}, all one shape",
            f"struts        = {len(GOLDEN.edges)} in {len(GOLDEN.strut_lengths)} length",
            f"acute corner  = {item.acute_deg:.6f} deg",
            f"diagonal ratio= {item.diagonal_ratio:.9f}",
            f"phi           = {PHI:.9f}",
        ]
    if stage == "zome_versus":
        from .geometry import build_demo_geometry

        geometry = build_demo_geometry()
        return [
            f"2V dome: {len(geometry.hemisphere_faces)} triangles, "
            f"{len(geometry.hemisphere_edges)} struts, 2 lengths",
            f"zome   : {len(ZOME.dome_faces)} rhombi, "
            f"{len(ZOME.dome_edges)} struts, {len(ZOME.strut_lengths)} length",
            f"zome panel shapes = {ZOME.panel_shapes}",
        ]
    return []


SCENES = {
    "zome_hero": scene_zome_hero,
    "zome_sweep": scene_zome_sweep,
    "zome_parallelogram": scene_zome_parallelogram,
    "zome_rhombus": scene_zome_rhombus,
    "zome_star": scene_zome_star,
    "zome_counts": scene_zome_counts,
    "zome_apex": scene_zome_apex,
    "zome_rings": scene_zome_rings,
    "zome_shapes": scene_zome_shapes,
    "zome_pitch": scene_zome_pitch,
    "zome_hubs": scene_zome_hubs,
    "zome_floor": scene_zome_floor,
    "zome_cutlist": scene_zome_cutlist,
    "zome_golden": scene_zome_golden,
    "zome_golden_cost": scene_zome_golden_cost,
    "zome_raise": scene_zome_raise,
    "zome_openings": scene_zome_openings,
    "zome_versus": scene_zome_versus,
    "zome_finale": scene_zome_finale,
}


CHAPTERS: tuple[Chapter, ...] = (
    Chapter(
        "what", "01", "A zome is not a piece of a sphere",
        "It is a shape you sweep, and that changes everything about building it.",
        (
            "A geodesic dome starts with a sphere and chops it into triangles. A zome",
            "starts somewhere else entirely: you pick a handful of directions and sweep",
            "the shape out along them, one after another. What you get is a room built",
            "entirely from parallelograms, with a true point at the top, and it can be",
            "framed from a single length of stick.",
        ),
        ("zome = zonohedron = a swept solid", "every face a parallelogram",
         "one strut length, one point on top"),
        16.0, (34.0, 24.0, 15.5), "zome_hero",
    ),
    Chapter(
        "sweep", "02", "The sweep, in four steps",
        "A point becomes a stick, a stick becomes a panel, a panel becomes a room.",
        (
            "Take a point and drag it along the first direction: you have drawn a stick.",
            "Drag that stick along the second direction and it sweeps out a panel. Drag",
            "the panel along a third and you have a solid. Keep going for as many",
            "directions as you chose, and the surface of the result is your building.",
            "Every step of that is something you can do with your hands, and it is the",
            "only construction rule in this lesson.",
        ),
        ("sweep along g1, then g2, then g3, ...",
         "the result is called a zonohedron"),
        19.0, (90.0, 22.0, 15.0), "zome_sweep",
    ),
    Chapter(
        "flat", "03", "Every panel is flat, guaranteed",
        "Two directions define a plane, so the panel they sweep cannot be warped.",
        (
            "This is the zome's quiet advantage over a hexagon dome. Each panel comes",
            "from exactly two directions, and two directions define a plane, so all four",
            "corners of that panel lie in one flat sheet. Not approximately. Exactly, and",
            "at every size. You can cut a zome's panels from rigid sheet goods and they",
            "will lie down without springing, complaining, or leaving a gap at one corner.",
        ),
        ("two directions -> one plane",
         "opposite sides equal and parallel", "planar by construction, at any size"),
        19.0, (-90.0, 16.0, 13.0), "zome_parallelogram",
    ),
    Chapter(
        "rhombus", "04", "Make the directions equal and you get one strut",
        "A parallelogram with equal sides is a rhombus, and a rhombus needs one length.",
        (
            "Nothing so far forced the directions to be the same length. If they differ,",
            "the panels are general parallelograms and your cut list has several lines on",
            "it. Make every direction the same length and every side of every panel is",
            "that length, so the entire frame comes off one saw setting. This is a",
            "decision you make once, at the very start, and it pays for itself all the",
            "way through the build.",
        ),
        ("equal directions -> rhombic faces",
         "every strut the same length"),
        19.0, (-90.0, 16.0, 13.5), "zome_rhombus",
    ),
    Chapter(
        "star", "05", "The star of directions",
        "Space them evenly around a cone and the whole building falls out of two numbers.",
        (
            "For the classic pointed zome, arrange the directions evenly around a vertical",
            "axis, all leaning in at the same angle. That angle is the pitch, and it is",
            "your only shape control. How many directions you use sets how many sides the",
            "building has. Two numbers, a count and an angle, and everything else in this",
            "lesson is derived from them.",
        ),
        ("n directions, evenly spaced",
         "pitch = lean from the axis", "two numbers set the whole building"),
        18.0, (34.0, 26.0, 13.0), "zome_star",
    ),
    Chapter(
        "counts", "06", "Counting the parts before you buy anything",
        "Panels, struts and hubs are all simple formulas in the number of directions.",
        (
            "Each pair of directions makes exactly two panels, one on each side of the",
            "building, so the panel count is n times n minus one. Each panel has four",
            "edges and every edge is shared, so the strut count is twice that. Add the two",
            "points and you have the hub count. Check it against Euler's formula and it",
            "comes out to two every time, which is how you know you have not miscounted.",
        ),
        ("panels = n(n-1)", "struts = 2n(n-1)", "hubs = n(n-1)+2", "V - E + F = 2"),
        20.0, (90.0, 18.0, 18.0), "zome_counts",
    ),
    Chapter(
        "apex", "07", "The top comes to a point",
        "One vertex is reached by travelling along every direction, so the roof closes there.",
        (
            "Walk along all of the directions in turn and you arrive at one particular",
            "corner: the far end of the whole sweep. Only one corner can be reached that",
            "way, so the roof closes on a single point, with one panel arriving from each",
            "direction. Add up the panel corners that meet there and they come to less",
            "than a full turn. That shortfall is exactly why it closes into a peak instead",
            "of lying flat.",
        ),
        ("apex = sum of every direction", "n panels meet there",
         "corner angles < 360 deg -> a peak"),
        20.0, (36.0, 30.0, 15.0), "zome_apex",
    ),
    Chapter(
        "rings", "08", "The hubs land on level rings",
        "Every corner at a given height is at exactly that height. No tape needed.",
        (
            "Here is the property that makes a zome pleasant to build. A corner's height",
            "is just the number of directions you travelled to reach it, times the rise of",
            "one direction. Every corner reached in the same number of steps is therefore",
            "at exactly the same height, so the hubs sit on perfectly level rings, evenly",
            "spaced. A hexagon dome has nothing like this, and it is why a zome wall meets",
            "a floor and a lintel so easily.",
        ),
        ("corner height = steps x rise per direction",
         "n+1 level rings, evenly spaced", "no ring is approximate"),
        21.0, (38.0, 24.0, 15.5), "zome_rings",
    ),
    Chapter(
        "shapes", "09", "How many panel templates",
        "Directions one apart, two apart, and so on -- and the far pairs repeat.",
        (
            "A panel's shape depends only on how far apart its two directions sit around",
            "the star. Neighbouring directions give a long thin rhombus; opposite ones",
            "give a fat near-square. Because a pair separated by three steps one way is",
            "separated the other way by the same amount, the shapes pair up, and a zome",
            "with n directions needs only about half that many templates. Cut one jig per",
            "shape and trace the rest.",
        ),
        ("shape depends only on separation",
         "separation s and n-s are the same shape",
         "templates = round up of (n-1)/2"),
        21.0, (-90.0, 16.0, 13.0), "zome_shapes",
    ),
    Chapter(
        "pitch", "10", "Pitch is the free design knob",
        "Tall spire or low saucer, same struts, same count, same cut list.",
        (
            "Lean the directions in steeply and the zome climbs into a spire. Open them",
            "out and it settles into a wide saucer. Nothing about the strut length or the",
            "part count changes; only the panel angles do. That means you can shape the",
            "building to the site, the snow load, or the headroom you want without adding",
            "a single line to the cut list. Very few structural systems give you a free",
            "knob like this.",
        ),
        ("pitch changes shape, not part count",
         "still one strut length at every pitch"),
        20.0, (90.0, 18.0, 19.0), "zome_pitch",
    ),
    Chapter(
        "hubs", "11", "The joints are where a zome gets particular",
        "One strut length, but several different hubs, and they are not interchangeable.",
        (
            "The saving on struts is real, but it is paid back at the joints. The corners",
            "come in a handful of types: some take three struts, some four, and the two",
            "points take one from every direction. Each type has its own splay angles, so",
            "a hub that works at mid-height will not sit right near the top. Make a full",
            "set of angle jigs before you fabricate any of them, and stamp each hub with",
            "its type as it comes off the bench.",
        ),
        ("hub types vary; strut length does not",
         "each type has its own splay angles",
         "stamp the type on the hub at the bench"),
        21.0, (40.0, 26.0, 15.0), "zome_hubs",
    ),
    Chapter(
        "floor", "12", "Meeting the floor",
        "A zonohedron has no horizontal strut, but its floor line is one repeated cut.",
        (
            "Not one strut in a zome runs level, so a level floor line always crosses",
            "struts in mid span. On a polar zome that turns out not to matter: because",
            "every hub in a ring is at the same height, the level line meets every strut",
            "it crosses at exactly the same place along its length. One angle, one length,",
            "repeated all the way round. Mark one, check it, then use it as the master.",
        ),
        ("no horizontal struts anywhere",
         "level line crosses every strut identically",
         "one cut setting for the whole bottom row"),
        21.0, (44.0, 20.0, 15.5), "zome_floor",
    ),
    Chapter(
        "cutlist", "13", "The whole cut list",
        "One stick length, a handful of panel templates, and a hub schedule.",
        (
            "This is what the shop actually receives. A single strut length, cut as many",
            "times as there are struts in the roof, less the connector allowance you",
            "measured on a real joint. A template for each panel shape. And a hub schedule",
            "listing how many of each type. Everything on this list came from the two",
            "numbers you chose in chapter five, so if you change your mind about pitch,",
            "the list regenerates rather than needing to be re-derived.",
        ),
        ("cut length = centre length - deduction",
         "one length x every strut in the roof"),
        20.0, (90.0, 20.0, 17.0), "zome_cutlist",
    ),
    Chapter(
        "golden", "14", "The famous one-panel zome",
        "Thirty identical golden rhombi, and their diagonals land exactly on phi.",
        (
            "There is one zome where every single panel is the same shape: build the star",
            "from the six five-fold axes of an icosahedron and you get the rhombic",
            "triacontahedron. Thirty faces, all identical, all rhombi, and the ratio of",
            "each panel's diagonals is the golden ratio, exactly. One strut length and one",
            "template for the entire surface. It is the most economical shell in this",
            "whole series of lessons.",
        ),
        ("6 icosahedral axes -> 30 identical faces",
         "diagonal ratio = phi", "one strut, one template"),
        20.0, (34.0, 26.0, 15.0), "zome_golden",
    ),
    Chapter(
        "golden_cost", "15", "What the golden zome charges you",
        "Its hub rings are not evenly spaced, so the floor line stops being simple.",
        (
            "The catch shows up the moment you try to stand it on something. Its rings of",
            "hubs are not evenly spaced, so a level line through the middle of the",
            "building meets struts at two different points along their length, and the",
            "bottom row needs two cut settings instead of one. That is a real cost, and it",
            "is the exact mirror image of the polar zome's trade: one pays at the panel",
            "bench, the other at the floor.",
        ),
        ("golden zome: uneven ring spacing",
         "level cut needs two settings",
         "polar zome pays at the panels instead"),
        21.0, (90.0, 20.0, 18.0), "zome_golden_cost",
    ),
    Chapter(
        "raise", "16", "Raising it, tier by tier",
        "The geometry hands you the build sequence: one complete ring at a time.",
        (
            "Set out the bottom ring on a level base and bolt it down. Then add complete",
            "tiers, never a single column of panels up one side, because a zome is a",
            "shell and it is not stable until each ring closes. Prop the tier you are",
            "working on until the ring above it goes in. Check the diameter of each",
            "completed ring in three directions before starting the next, and leave the",
            "apex panels for last.",
        ),
        ("complete rings, never one column",
         "prop each tier until the ring closes", "apex panels last"),
        20.0, (40.0, 26.0, 16.0), "zome_raise",
    ),
    Chapter(
        "openings", "17", "Doors and windows",
        "Take out a whole panel and no strut needs cutting.",
        (
            "Because the frame is a net of complete rhombi, the natural opening is one",
            "whole panel. Leave the panel out, frame the rhombus, and hang a door or a",
            "fixed light in it: the structure is untouched. If you need something square,",
            "build a small dormer forward out of the rhombus rather than cutting struts",
            "out of the shell, and keep the shell's own net intact behind it.",
        ),
        ("one panel out = one opening",
         "the frame is never cut", "square openings dormer forward"),
        19.0, (56.0, 18.0, 15.0), "zome_openings",
    ),
    Chapter(
        "versus", "18", "Zome against geodesic dome",
        "Both close. They close for completely different reasons.",
        (
            "A geodesic dome closes because triangles hold their shape and its corners",
            "are missing a little angle each. A zome closes because a swept solid has to",
            "come back on itself. The dome gives you a shallower shell and famously stiff",
            "triangulation; the zome gives you fewer strut lengths, guaranteed flat",
            "panels, level hub rings, and vertical-ish walls that furniture can actually",
            "stand against. Pick by what your building has to do, not by which is rounder.",
        ),
        ("dome: triangles, 2 lengths, stiff shell",
         "zome: rhombi, 1 length, usable walls"),
        21.0, (90.0, 20.0, 17.5), "zome_versus",
    ),
    Chapter(
        "close", "19", "The whole transformation",
        "A star of directions, swept out, and closed on a point.",
        (
            "Pick a count and a pitch. Sweep the shape along that star of directions.",
            "Every panel arrives flat, every strut arrives the same length, the hubs land",
            "on level rings, and the roof closes on a single point. Cut the building off",
            "at whichever ring gives you the room you want, and the bottom row is one",
            "repeated cut. That is the entire method, and every number in this lesson was",
            "recomputed from it rather than read off a table.",
        ),
        ("count + pitch -> the whole building",
         "swept, flat, level, and closed"),
        18.0, (32.0, 30.0, 16.0), "zome_finale",
    ),
)


ZOME_LESSON = Lesson(
    key="zome",
    brand="ZOME / ZONOHEDRON MASTERCLASS",
    title="Zome Construction Masterclass",
    chapters=CHAPTERS,
    scenes=SCENES,
    equations=zome_equations,
    selftest=validate_zome_geometry,
    report=lambda: zome_report(LESSON_STRUT_IN, CONNECTOR_DEDUCTION_IN),
    snapshot_prefix="zome",
)
