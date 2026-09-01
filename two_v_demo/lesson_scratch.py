"""From scratch: every calculation behind a dome on a screen.

This lesson answers one question, end to end, for somebody who has
never written a line of code: **what does a computer actually work out,
starting from nothing, to put a geodesic dome in front of you?**

It runs in two halves.

*The shape.*  One irrational number places twelve points.  Normalizing
turns them into a unit-free recipe.  Counting proves the surface closed.
Halving every edge makes new points that are in the wrong place, and one
division puts them right -- which is the entire difference between a
faceted ball and a geodesic dome.  Measuring what came out gives two
strut lengths, and one multiplication turns those into lumber.

*The picture.*  A line with no thickness becomes a tube.  A triangle
learns which way it faces.  The model flattens into one list of numbers.
A camera is placed with two angles and a distance, the world is moved in
front of it, depth is loaded into a fourth coordinate, one divide makes
distant things small, a stretch turns that into pixels, a comparison
decides what hides what, and three dot products decide how bright it is.

Every figure quoted on a math screen comes from
:mod:`two_v_demo.scratch_facts`, which computes nothing of its own: the
geometry comes from ``geometry.py`` and the camera, projection and pixel
arithmetic come from the renderer's own functions.  The pictures obey
the same rule.  The clip-space chapter really multiplies the dome by the
real matrix and divides by w; the culling chapter really counts which
faces point away from the real eye; the lighting chapter draws the same
four vectors the math screen prints.
"""

from __future__ import annotations

import math
from dataclasses import replace

import numpy as np

from .geometry import build_demo_geometry, normalize
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
)
from .scratch_facts import (
    ALL_SCREENS,
    APEX_WORLD,
    FRAME_HEIGHT,
    FRAME_WIDTH,
    REFERENCE_CAMERA,
    SCALE,
    depth_value,
    dome_batch,
    eye_position,
    lighting_sample,
    reference_matrices,
    render_settings,
    scratch_report,
    steps_buffer,
    steps_chords,
    steps_counts,
    steps_depth,
    steps_euler,
    steps_eye,
    steps_frame,
    steps_light,
    steps_midpoint,
    steps_normal,
    steps_normalize,
    steps_phi,
    steps_pixel,
    steps_project,
    steps_projection,
    steps_scale,
    steps_tube,
    steps_view,
    validate_scratch_facts,
)
from .render_kit import project_point


GEOMETRY = build_demo_geometry()
SETTINGS = render_settings()

# The camera the culling chapter counts against.  A painter is handed
# the app, not the chapter, so the one camera both the picture and its
# label describe is stated here and used in the chapter below.
CULL_CAMERA = (34.0, 22.0, 17.0)

# The depth chapter's camera, for the same reason: the panels are placed
# along its own line of sight so that they really overlap on screen.
DEPTH_CAMERA = (34.0, 34.0, 22.0)


def _prose(lines: tuple[str, ...], per_paragraph: int = 2) -> tuple[str, ...]:
    """Reflow authored source lines into whole-sentence paragraphs.

    The teaching card prints one narration item per paragraph, so source
    hard-wrapped to fit an editor would appear on screen as a ragged
    column of fragments.  Joining the lines and re-splitting them at
    sentence ends lets the source stay readable at 79 columns and the
    card stay readable at 1080p.  The speech and the subtitles are built
    from the same text either way.
    """
    text = " ".join(line.strip() for line in lines if line.strip())
    sentences: list[str] = []
    current = ""
    for word in text.split():
        current = f"{current} {word}".strip()
        if word.endswith((".", "?", "!")):
            sentences.append(current)
            current = ""
    if current:
        sentences.append(current)
    return tuple(
        " ".join(sentences[index:index + per_paragraph])
        for index in range(0, len(sentences), per_paragraph)
    )


def _rgb(colour) -> tuple[int, int, int]:
    return tuple(int(round(channel * 255)) for channel in colour[:3])


def _fade(colour, alpha: float):
    return (colour[0], colour[1], colour[2], clamp(alpha) * colour[3])


def _math_shift(app, amount: float = 4.6) -> float:
    """How far to slide a wide picture toward screen left, or zero.

    The math overlay takes the right 42% of the frame, so a scene laid
    out as a row -- the vertex buffer, the frame, the filmstrip -- would
    run underneath it on its own math chapter.  Those painters ask this,
    and with the camera on +Y (screen left is +X) they move that way.
    The selftest's stand-in app has no chapters, so it gets zero.
    """
    chapters = getattr(app, "chapters", None)
    index = getattr(app, "chapter_index", None)
    if not chapters or index is None:
        return 0.0
    try:
        chapter = chapters[index]
    except (IndexError, TypeError, KeyError):
        return 0.0
    return amount if getattr(chapter, "overlay", None) == "math" else 0.0


def _label(app, point, text: str, colour) -> None:
    app.world_labels.append(
        WorldLabel(np.asarray(point, dtype=float), text, _rgb(colour)))


def _ico_edges(batch, centre, scale: float, colour, radius: float = 0.045,
               reveal: float = 1.0) -> None:
    """The parent icosahedron's thirty edges."""
    edges = GEOMETRY.ico_edges
    shown = max(0, min(len(edges), int(round(len(edges) * clamp(reveal)))))
    for edge in edges[:shown]:
        a = GEOMETRY.ico_vertices[edge[0]] * scale + centre
        b = GEOMETRY.ico_vertices[edge[1]] * scale + centre
        batch.cylinder(a, b, radius, colour, 6)


def _sphere_edges(batch, centre, scale: float, radius: float = 0.035,
                  reveal: float = 1.0, upper_only: bool = False) -> None:
    """The finished 2V sphere, coloured by strut class."""
    edges = [edge for edge in GEOMETRY.edges
             if not upper_only
             or (GEOMETRY.vertices[edge[0]][2] >= -1e-9
                 and GEOMETRY.vertices[edge[1]][2] >= -1e-9)]
    shown = max(0, min(len(edges), int(round(len(edges) * clamp(reveal)))))
    class_by_edge = dict(zip(GEOMETRY.edges, GEOMETRY.edge_class_by_edge))
    for edge in edges[:shown]:
        a = GEOMETRY.vertices[edge[0]] * scale + centre
        b = GEOMETRY.vertices[edge[1]] * scale + centre
        colour = CYAN if class_by_edge[edge] == "SHORT" else AMBER
        batch.cylinder(a, b, radius, colour, 6)


def _pedestal(batch, centre, radius: float, reveal: float) -> None:
    grow = ease_in_out(clamp(reveal))
    if grow <= 0.02:
        return
    batch.disc(np.asarray(centre, dtype=float), radius * grow,
               (0.10, 0.20, 0.30, 1.0), 28)


def _arc(batch, centre, radius: float, start_deg: float, end_deg: float,
         colour, sweep_from=None, thickness: float = 0.06) -> None:
    """An arc marking an angle in space.

    ``sweep_from`` is the horizontal direction the angle is measured
    from; leave it out and the arc lies flat on the ground, which is how
    a yaw angle reads.  Give it one and the arc stands up in the
    vertical plane through it, which is how a pitch angle reads.
    """
    centre = np.asarray(centre, dtype=float)
    steps = max(4, int(abs(end_deg - start_deg) / 4.0))
    previous = None
    for index in range(steps + 1):
        angle = math.radians(
            start_deg + (end_deg - start_deg) * index / steps)
        if sweep_from is None:
            point = centre + np.array([radius * math.cos(angle),
                                       radius * math.sin(angle), 0.0])
        else:
            direction = np.asarray(sweep_from, dtype=float)
            point = centre + radius * (
                direction * math.cos(angle)
                + np.array([0.0, 0.0, 1.0]) * math.sin(angle))
        if previous is not None:
            batch.cylinder(previous, point, thickness, colour, 5)
        previous = point


# ======================================================================
# The map of the whole calculation
# ======================================================================

_STATIONS = (
    ("1 ONE NUMBER", "phi: 12 points", CYAN),
    ("2 NORMALIZE", "divide by length", CYAN),
    ("3 SUBDIVIDE", "halve the edges", AMBER),
    ("4 PROJECT", "push to the sphere", AMBER),
    ("5 MESH", "tubes, triangles", GREEN),
    ("6 CAMERA", "three matrices", PURPLE),
    ("7 PIXELS", "divide, shade", RED),
)


def _station_icon(batch, index: int, centre, grow: float) -> None:
    size = 1.05 * grow
    if index == 0:
        for vertex in GEOMETRY.ico_vertices:
            batch.sphere(vertex * size + centre, 0.12, CYAN, 4, 6)
    elif index == 1:
        _ico_edges(batch, centre, size, CYAN, 0.05)
    elif index == 2:
        _ico_edges(batch, centre, size, MUTED, 0.04)
        for edge in GEOMETRY.ico_edges:
            midpoint = (GEOMETRY.ico_vertices[edge[0]]
                        + GEOMETRY.ico_vertices[edge[1]]) * 0.5
            batch.sphere(midpoint * size + centre, 0.10, AMBER, 4, 6)
    elif index == 3:
        _sphere_edges(batch, centre, size, 0.035)
    elif index == 4:
        a = centre + np.array([-0.9, 0.0, -0.6]) * grow
        b = centre + np.array([0.9, 0.0, -0.6]) * grow
        c = centre + np.array([0.0, 0.0, 0.9]) * grow
        batch.triangle(a, b, c, _fade(GREEN, 0.55))
        for start, end in ((a, b), (b, c), (c, a)):
            batch.cylinder(start, end, 0.09 * grow, GREEN, 8)
    elif index == 5:
        tip = centre + np.array([0.0, 0.0, 0.9]) * grow
        batch.cone(centre + np.array([0.0, 0.0, -0.2]) * grow, tip,
                   0.42 * grow, PURPLE, 10)
        for corner in ((-1, -1), (1, -1), (1, 1), (-1, 1)):
            far = centre + np.array([corner[0] * 0.85, corner[1] * 0.85,
                                     -1.1]) * grow
            batch.cylinder(tip, far, 0.035, _fade(PURPLE, 0.7), 5)
    else:
        for row in range(3):
            for column in range(5):
                batch.box(centre + np.array([
                    (2.0 - column) * 0.42, 0.0, (1.0 - row) * 0.42]) * grow,
                    np.array([0.34, 0.10, 0.34]) * grow,
                    _fade(RED, 0.45 + 0.16 * ((row + column) % 3)))


def scene_sc_pipeline(app, opaque, transparent, p: float) -> None:
    """Seven stations: the whole calculation, left to right.

    The camera sits on +Y, so +X is screen LEFT and station one takes
    the largest +X.
    """
    spacing = 5.05
    for index, (title, caption, colour) in enumerate(_STATIONS):
        x = (3 - index) * spacing - 2.6
        reveal = clamp(p * (len(_STATIONS) + 1.2) - index + 0.4)
        centre = np.array([x, 0.0, 0.06])
        _pedestal(opaque, centre, 1.55, reveal)
        if reveal <= 0.06:
            continue
        grow = ease_in_out(clamp(reveal))
        _station_icon(opaque, index, np.array([x, 0.0, 2.20]), grow)
        _label(app, np.array([x, 0.0, 4.9]), f"{title}\n{caption}", colour)
        if index < len(_STATIONS) - 1 and reveal > 0.75:
            opaque.arrow(np.array([x - 1.75, 0.0, 0.9]),
                         np.array([x - spacing + 1.75, 0.0, 0.9]),
                         0.045, MUTED)
    if p > 0.55:
        _label(app, np.array([-2.6, 0.0, 6.8]),
               "GEOMETRY  ->  MESH  ->  CAMERA  ->  PIXELS", WHITE)


# ======================================================================
# The shape
# ======================================================================

def scene_sc_euler(app, opaque, transparent, p: float) -> None:
    """Count the corners, then the edges, then the faces."""
    centre = np.array([0.0, 0.0, 3.2])
    scale = 3.2
    vertices = len(GEOMETRY.ico_vertices)
    faces = len(GEOMETRY.base_faces)
    edges = len(GEOMETRY.ico_edges)

    corner_phase = clamp(p * 3.2)
    edge_phase = clamp((p - 0.30) * 3.2)
    face_phase = clamp((p - 0.60) * 3.4)

    shown_corners = max(1, int(round(vertices * corner_phase)))
    for index, vertex in enumerate(GEOMETRY.ico_vertices):
        if index >= shown_corners:
            break
        opaque.sphere(vertex * scale + centre, 0.20, CYAN, 5, 8)
    _ico_edges(opaque, centre, scale, WHITE, 0.045, edge_phase)
    if face_phase > 0.02:
        shown_faces = int(round(faces * face_phase))
        for index, face in enumerate(GEOMETRY.base_faces):
            if index >= shown_faces:
                break
            a, b, c = (GEOMETRY.ico_vertices[int(corner)] * scale + centre
                       for corner in face)
            transparent.triangle(a, b, c, _fade(GREEN, 0.30))

    _label(app, centre + np.array([0.0, 0.0, scale + 1.3]),
           f"V  corners = {shown_corners}", CYAN)
    if edge_phase > 0.05:
        _label(app, centre + np.array([0.0, 0.0, -scale - 0.7]),
               f"E  edges = {int(round(edges * edge_phase))}", WHITE)
    if face_phase > 0.05:
        _label(app, centre + np.array([0.0, 0.0, -scale - 1.8]),
               f"F  faces = {int(round(faces * face_phase))}", GREEN)
    if p > 0.88:
        _label(app, centre + np.array([0.0, 0.0, -scale - 2.9]),
               f"V - E + F = {vertices} - {edges} + {faces} = "
               f"{vertices - edges + faces}", AMBER)


def scene_sc_hemisphere(app, opaque, transparent, p: float) -> None:
    """Cut the finished sphere in half and keep the top."""
    centre = np.array([0.0, 0.0, 3.4])
    scale = 3.4
    cut = ease_in_out(clamp(p * 1.6))

    class_by_edge = dict(zip(GEOMETRY.edges, GEOMETRY.edge_class_by_edge))
    for edge in GEOMETRY.edges:
        a = GEOMETRY.vertices[edge[0]]
        b = GEOMETRY.vertices[edge[1]]
        upper = a[2] >= -1e-9 and b[2] >= -1e-9
        start = a * scale + centre
        end = b * scale + centre
        if upper:
            colour = CYAN if class_by_edge[edge] == "SHORT" else AMBER
            opaque.cylinder(start, end, 0.05, colour, 6)
        else:
            faded = _fade(MUTED, 0.75 * (1.0 - cut))
            if faded[3] > 0.02:
                transparent.cylinder(start, end, 0.03, faded, 5)

    if cut > 0.05:
        transparent.disc(centre, scale * 1.02 * cut,
                         (0.16, 0.68, 0.95, 0.16), 48)
    short = next(item for item in GEOMETRY.edge_classes
                 if item.name == "SHORT")
    long = next(item for item in GEOMETRY.edge_classes if item.name == "LONG")
    _label(app, centre + np.array([0.0, 0.0, scale + 1.1]),
           f"KEEP z >= 0\n{len(GEOMETRY.hemisphere_faces)} panels  ·  "
           f"{short.hemisphere_count + long.hemisphere_count} struts",
           WHITE)
    if p > 0.45:
        _label(app, centre + np.array([scale + 2.2, 0.0, -0.2]),
               f"SHORT x {short.hemisphere_count}", CYAN)
        _label(app, centre + np.array([-scale - 2.2, 0.0, -0.2]),
               f"LONG x {long.hemisphere_count}", AMBER)
    if p > 0.70:
        _label(app, centre + np.array([0.0, 0.0, -scale - 1.1]),
               f"base ring: {len(GEOMETRY.base_ring)} corners at z = 0",
               GREEN)


# ======================================================================
# The mesh
# ======================================================================

def scene_sc_tube(app, opaque, transparent, p: float) -> None:
    """One strut, blown up: the ring, the frame, and the skin."""
    a = np.array([4.4, 0.0, 3.4])
    b = np.array([-6.8, 0.0, 3.4])
    axis = b - a
    direction = normalize(axis)
    trial = np.array([0.0, 0.0, 1.0])
    side = normalize(np.cross(direction, trial))
    up = normalize(np.cross(direction, side))
    radius = 1.25
    sides = 8

    # The bare strut first: two points and the line between them, which
    # is all the model actually holds.
    opaque.cylinder(a, b, 0.035, _fade(MUTED, 0.9), 5)
    opaque.sphere(a, 0.30, WHITE, 6, 10)
    opaque.sphere(b, 0.30, WHITE, 6, 10)
    _label(app, a + np.array([0.0, 0.0, 1.0]), "a", WHITE)
    _label(app, b + np.array([0.0, 0.0, 1.0]), "b", WHITE)

    if p > 0.10:
        # Lifted clear of the strut itself: drawn on the axis it is lost
        # among the ring lines that arrive later.
        lift = np.array([0.0, 0.0, 2.3])
        opaque.arrow(a + lift, a + lift + direction * 3.6, 0.085, CYAN)
        _label(app, a + lift + direction * 4.3,
               "d = (b - a) / |b - a|", CYAN)
    if p > 0.24:
        opaque.arrow(a, a + side * 2.7, 0.075, AMBER)
        _label(app, a + side * 3.3, "s = d x t", AMBER)
    if p > 0.34:
        opaque.arrow(a, a + up * 2.7, 0.075, GREEN)
        _label(app, a + up * 3.3, "u = d x s", GREEN)

    ring_phase = clamp((p - 0.42) * 3.2)
    if ring_phase > 0.02:
        shown = max(1, int(round(sides * ring_phase)))
        for index in range(shown):
            angle = math.tau * index / sides
            offset = radius * (side * math.cos(angle) + up * math.sin(angle))
            opaque.sphere(a + offset, 0.16, AMBER, 4, 7)
            opaque.sphere(b + offset, 0.16, AMBER, 4, 7)
            if index:
                previous = math.tau * (index - 1) / sides
                previous_offset = radius * (side * math.cos(previous)
                                            + up * math.sin(previous))
                opaque.cylinder(a + previous_offset, a + offset,
                                0.05, AMBER, 5)
            # The rings are stitched to each other only once both of
            # them exist, or the picture reads as a cage before it has
            # been explained as one.
            if p > 0.60:
                opaque.cylinder(a + offset, b + offset, 0.04,
                                _fade(MUTED, 0.9), 5)
        _label(app, (a + b) * 0.5 + np.array([0.0, 0.0, -radius - 1.2]),
               f"ring of {shown} points, repeated at each end", AMBER)

    skin = clamp((p - 0.66) * 3.0)
    if skin > 0.02:
        transparent.cylinder(a, b, radius, _fade(CYAN, 0.42 * skin), sides)
    if p > 0.80:
        per_cylinder = sides * 2 + 2 * (sides - 2)
        _label(app, (a + b) * 0.5 + np.array([0.0, 0.0, radius + 1.6]),
               f"{sides} sides  ->  {per_cylinder} triangles", WHITE)


def scene_sc_winding(app, opaque, transparent, p: float) -> None:
    """The same triangle wound both ways, and what each one does.

    Both copies sit the same distance from the camera and lie tilted
    back toward it, so the normal standing out of one and the normal
    driven down through the other are both plainly visible instead of
    pointing straight at the lens.
    """
    tilt = math.radians(66.0)
    across = np.array([1.0, 0.0, 0.0])
    plane_up = np.array([0.0, -math.sin(tilt), math.cos(tilt)])
    toward_camera = np.array([0.0, 1.0, 0.0])

    for sign, colour, name in ((1.0, CYAN, "COUNTER-CLOCKWISE"),
                               (-1.0, RED, "CLOCKWISE")):
        origin = np.array([4.6 * sign - 1.8, 0.0, 2.4])
        corners = [origin + across * -2.3 + plane_up * -1.6,
                   origin + across * 2.3 + plane_up * -1.6,
                   origin + plane_up * 2.7]
        normal = normalize(np.cross(corners[1] - corners[0],
                                    corners[2] - corners[0]))
        # Author the front-facing winding once, then reverse it for the
        # second copy, so the two really are the same triangle listed
        # two ways rather than two different triangles.
        if float(np.dot(normal, toward_camera)) < 0.0:
            corners = [corners[0], corners[2], corners[1]]
            normal = -normal
        if sign < 0:
            corners = [corners[0], corners[2], corners[1]]
            normal = -normal

        culled = sign < 0 and p > 0.72
        face_colour = _fade(colour, 0.14 if culled else 0.40)
        # The reversed copy is drawn in the transparent pass, where face
        # culling is off: otherwise the card would remove it and the
        # chapter would have nothing to point at.
        target = transparent if sign < 0 else opaque
        target.triangle(corners[0], corners[1], corners[2], face_colour)

        for index, corner in enumerate(corners):
            opaque.sphere(corner, 0.19, WHITE, 5, 8)
            _label(app, corner + plane_up * 0.75, "abc"[index], WHITE)
        order = clamp(p * 2.6)
        for index in range(3):
            if order < (index + 1) / 3.0:
                break
            start = corners[index]
            end = corners[(index + 1) % 3]
            direction = normalize(end - start)
            opaque.arrow(start + direction * 0.42, end - direction * 0.42,
                         0.055, colour)
        if p > 0.44:
            centroid = sum(corners) / 3.0
            arrow_colour = GREEN if sign > 0 else RED
            opaque.arrow(centroid, centroid + normal * 2.8, 0.07,
                         arrow_colour)
            _label(app, centroid + normal * 3.4,
                   "n = (b - a) x (c - a)" if sign > 0
                   else "n points into the ground", arrow_colour)
        caption = name
        if p > 0.72:
            caption += ("\nfacing you: kept and shaded" if sign > 0
                        else "\nfacing away: dropped")
        _label(app, origin + np.array([0.0, 0.0, 4.6]), caption, colour)

_FIELDS = (
    ("x", CYAN), ("y", CYAN), ("z", CYAN),
    ("nx", GREEN), ("ny", GREEN), ("nz", GREEN),
    ("r", AMBER), ("g", AMBER), ("b", AMBER), ("a", AMBER),
)


def scene_sc_buffer(app, opaque, transparent, p: float) -> None:
    """One vertex as ten numbers, and the whole dome as a wall of them."""
    shift = _math_shift(app)
    dome_batch(clamp(0.12 + p * 1.8),
               origin=np.array([5.6 + shift, 0.0, 0.0]),
               scale=2.6, into=opaque)
    _label(app, np.array([5.6 + shift, 0.0, 3.9]), "the picture", CYAN)

    shown = max(1, int(round(len(_FIELDS) * clamp(p * 2.0))))
    for index, (name, colour) in enumerate(_FIELDS):
        if index >= shown:
            break
        x = 2.0 - index * 0.92 + shift
        centre = np.array([x, 0.0, 4.4])
        opaque.box(centre, np.array([0.74, 0.74, 0.74]), _fade(colour, 0.85))
        _label(app, centre + np.array([0.0, 0.0, 0.78]), name, colour)
    if p > 0.30:
        _label(app, np.array([1.1 + shift, 0.0, 5.9]), "position", CYAN)
        _label(app, np.array([-1.7 + shift, 0.0, 5.9]), "normal", GREEN)
        _label(app, np.array([-5.0 + shift, 0.0, 5.9]), "colour", AMBER)
        _label(app, np.array([-1.7 + shift, 0.0, 3.2]),
               "one vertex = 10 numbers = 40 bytes", WHITE)

    wall = clamp((p - 0.45) * 2.4)
    if wall > 0.02:
        floats = len(dome_batch().vertices)
        rows, columns = 6, 26
        for row in range(rows):
            for column in range(columns):
                if (row * columns + column) / (rows * columns) > wall:
                    continue
                opaque.box(
                    np.array([2.4 - column * 0.30 + shift, 0.0,
                              2.05 - row * 0.30]),
                    np.array([0.22, 0.10, 0.22]),
                    _fade(PURPLE, 0.55 + 0.25 * ((row + column) % 2)))
        _label(app, np.array([-2.4 + shift, 0.0, 0.15]),
               f"{floats // 10:,} vertices  ·  "
               f"{floats * 4 / 1024:.0f} KB", PURPLE)


# ======================================================================
# The camera
# ======================================================================

def scene_sc_world(app, opaque, transparent, p: float) -> None:
    """The model, sitting at the origin of a world with three axes."""
    dome_batch(clamp(0.12 + p * 1.5), scale=4.0, into=opaque)
    length = 6.2 * ease_in_out(clamp(p * 1.7))
    if length > 0.4:
        for direction, colour, name in (
            (np.array([1.0, 0.0, 0.0]), RED, "+X"),
            (np.array([0.0, 1.0, 0.0]), GREEN, "+Y"),
            (np.array([0.0, 0.0, 1.0]), CYAN, "+Z  up"),
        ):
            opaque.arrow(np.zeros(3), direction * length, 0.055, colour)
            _label(app, direction * (length + 0.7), name, colour)
    if p > 0.40:
        for tick in range(1, 7):
            opaque.box(np.array([float(tick), 0.0, 0.02]),
                       np.array([0.06, 0.5, 0.04]), MUTED)
        _label(app, np.array([3.0, 1.4, 0.25]),
               "1 world unit per tick", MUTED)
    if p > 0.60:
        _label(app, np.array([0.0, 0.0, -1.2]),
               f"the dome is built at radius {SCALE:.0f}\n"
               "nothing here knows about a screen yet", WHITE)


def _camera_body(batch, eye, target, scale: float = 1.0) -> None:
    direction = normalize(np.asarray(target) - np.asarray(eye))
    batch.cone(eye - direction * 0.5 * scale, eye + direction * 0.9 * scale,
               0.42 * scale, PURPLE, 12)
    batch.box(eye - direction * 0.85 * scale,
              np.array([0.6, 0.6, 0.6]) * scale, _fade(PURPLE, 0.85))


def scene_sc_orbit(app, opaque, transparent, p: float) -> None:
    """Two angles and a distance, placing a real camera."""
    yaw, pitch, distance = REFERENCE_CAMERA
    target = np.asarray(SETTINGS.target, dtype=float)
    eye = np.asarray(eye_position(REFERENCE_CAMERA), dtype=float)
    ground = np.array([eye[0], eye[1], 0.0])

    dome_batch(1.0, scale=2.4, into=opaque)

    ring = ease_in_out(clamp(p * 1.5))
    if ring > 0.05:
        radius = distance * math.cos(math.radians(pitch))
        _arc(opaque, np.array([target[0], target[1], eye[2]]), radius,
             0.0, 360.0 * ring, _fade(PURPLE, 0.55), thickness=0.05)

    if p > 0.20:
        _camera_body(opaque, eye, target)
        _label(app, eye + np.array([0.0, 0.0, 1.3]),
               f"eye = ({eye[0]:.2f}, {eye[1]:.2f}, {eye[2]:.2f})", PURPLE)
    if p > 0.34:
        opaque.cylinder(target, eye, 0.045, _fade(WHITE, 0.75), 6)
        _label(app, (target + eye) * 0.5 + np.array([0.0, 0.0, 0.8]),
               f"distance = {distance:.1f}", WHITE)
    if p > 0.48:
        opaque.cylinder(np.zeros(3), np.array([distance * 0.55, 0.0, 0.0]),
                        0.04, _fade(AMBER, 0.8), 5)
        opaque.cylinder(np.zeros(3), ground * 0.62, 0.04,
                        _fade(AMBER, 0.8), 5)
        _arc(opaque, np.zeros(3), 3.4, 0.0, yaw, AMBER)
        _label(app, np.array([3.9 * math.cos(math.radians(yaw * 0.5)),
                              3.9 * math.sin(math.radians(yaw * 0.5)), 0.3]),
               f"yaw = {yaw:.0f} deg", AMBER)
    if p > 0.64:
        opaque.cylinder(ground, eye, 0.04, _fade(GREEN, 0.7), 5)
        _arc(opaque, np.zeros(3), 4.6, 0.0, pitch, GREEN,
             sweep_from=normalize(np.array([ground[0], ground[1], 0.0])))
        _label(app, ground * 0.42 + np.array([0.0, 0.0, 2.1]),
               f"pitch = {pitch:.0f} deg", GREEN)
    if p > 0.80:
        _label(app, target + np.array([0.0, 0.0, 4.4]),
               "target = (0, 0, 2.25)", CYAN)


def scene_sc_view(app, opaque, transparent, p: float) -> None:
    """The camera's own three directions, drawn where they belong."""
    target = np.asarray(SETTINGS.target, dtype=float)
    eye = np.asarray(eye_position(REFERENCE_CAMERA), dtype=float)
    forward = normalize(target - eye)
    right = normalize(np.cross(forward, np.array([0.0, 0.0, 1.0])))
    up = normalize(np.cross(right, forward))

    dome_batch(1.0, scale=2.4, into=opaque)
    _camera_body(opaque, eye, target)

    for index, (direction, colour, name) in enumerate((
        (forward, CYAN, "f  forward"),
        (right, AMBER, "r  right = f x up"),
        (up, GREEN, "u  up = r x f"),
    )):
        if p < 0.15 + index * 0.18:
            continue
        length = 4.6 if index == 0 else 3.0
        opaque.arrow(eye, eye + direction * length, 0.065, colour)
        _label(app, eye + direction * (length + 0.8), name, colour)
    if p > 0.74:
        _label(app, eye + np.array([0.0, 0.0, 2.0]),
               "the world gets multiplied by these three rows\n"
               "so that it arrives already facing the lens", WHITE)


def scene_sc_frustum(app, opaque, transparent, p: float) -> None:
    """What the lens can see: a box that widens with distance."""
    target = np.asarray(SETTINGS.target, dtype=float)
    eye = np.asarray(eye_position(REFERENCE_CAMERA), dtype=float)
    forward = normalize(target - eye)
    right = normalize(np.cross(forward, np.array([0.0, 0.0, 1.0])))
    up = normalize(np.cross(right, forward))

    aspect = FRAME_WIDTH / FRAME_HEIGHT
    half_vertical = math.radians(SETTINGS.fov_degrees) * 0.5
    half_horizontal = math.atan(math.tan(half_vertical) * aspect)

    dome_batch(1.0, scale=2.4, into=opaque)
    _camera_body(opaque, eye, target)

    reach = ease_in_out(clamp(p * 1.5))
    near_distance, far_distance = 3.0, 10.0 * reach
    if far_distance < 3.6:
        return

    def plane(distance: float):
        centre = eye + forward * distance
        half_up = math.tan(half_vertical) * distance
        half_right = math.tan(half_horizontal) * distance
        return [centre + right * sx * half_right + up * sy * half_up
                for sx, sy in ((-1, -1), (1, -1), (1, 1), (-1, 1))]

    near = plane(near_distance)
    far = plane(far_distance)
    for corners, colour, radius in ((near, CYAN, 0.05), (far, PURPLE, 0.04)):
        for index in range(4):
            opaque.cylinder(corners[index], corners[(index + 1) % 4],
                            radius, colour, 5)
    for index in range(4):
        opaque.cylinder(near[index], far[index], 0.03,
                        _fade(PURPLE, 0.55), 5)
    transparent.quad(*near, _fade(CYAN, 0.10))

    _label(app, eye + forward * near_distance + up * 1.2,
           f"near plane\nnothing closer is drawn", CYAN)
    if p > 0.55:
        _label(app, eye + forward * far_distance * 1.02 + up * 2.6,
               f"far plane\nthe real one is {SETTINGS.far:.0f} units out",
               PURPLE)
        _label(app, eye + forward * 5.0 - up * 5.2,
               f"half-angle {math.degrees(half_vertical):.1f} deg up and "
               f"down, {math.degrees(half_horizontal):.1f} deg left and "
               f"right\nboth planes are drawn closer than "
               f"{SETTINGS.near} and {SETTINGS.far:.0f} so they fit on "
               "screen", WHITE)


# ======================================================================
# Pixels
# ======================================================================

def scene_sc_clip(app, opaque, transparent, p: float) -> None:
    """The dome, actually divided by w, actually inside the cube.

    The wireframe on the right is not an impression of clip space: it
    is this lesson's own dome pushed through the real matrix and
    divided by its own w, which is why it leans.
    """
    dome_batch(1.0, origin=np.array([6.2, 0.0, 0.0]), scale=2.5, into=opaque)
    _label(app, np.array([6.2, 0.0, 4.0]), "WORLD SPACE", CYAN)

    cube_centre = np.array([-7.6, 0.0, 3.6])
    half = 3.1
    grow = ease_in_out(clamp(p * 1.6))
    if grow > 0.05:
        corners = [cube_centre + np.array([x, y, z]) * half * grow
                   for x in (-1, 1) for y in (-1, 1) for z in (-1, 1)]
        for a in range(8):
            for b in range(a + 1, 8):
                if int(np.count_nonzero(corners[a] - corners[b])) == 1:
                    opaque.cylinder(corners[a], corners[b], 0.035,
                                    _fade(WHITE, 0.55), 5)
        _label(app, cube_centre + np.array([0.0, 0.0, half + 1.2]),
               "CLIP SPACE, after dividing by w\n"
               "everything visible fits -1 .. +1", WHITE)

    inside = clamp((p - 0.35) * 2.2)
    if inside > 0.02:
        _projection, _view, mvp = reference_matrices()
        class_by_edge = dict(zip(GEOMETRY.edges, GEOMETRY.edge_class_by_edge))
        edges = [edge for edge in GEOMETRY.hemisphere_edges]
        shown = int(round(len(edges) * inside))

        def ndc(index: int):
            point = GEOMETRY.vertices[index] * SCALE
            clip = mvp @ np.array([point[0], point[1], point[2], 1.0],
                                  dtype=np.float32)
            if clip[3] <= 1e-6:
                return None
            divided = clip[:3] / clip[3]
            return cube_centre + np.array([
                -float(divided[0]), float(divided[2]), float(divided[1])
            ]) * half

        for edge in edges[:shown]:
            a, b = ndc(edge[0]), ndc(edge[1])
            if a is None or b is None:
                continue
            colour = CYAN if class_by_edge[edge] == "SHORT" else AMBER
            opaque.cylinder(a, b, 0.045, colour, 5)
    if p > 0.80:
        _label(app, cube_centre + np.array([0.0, 0.0, -half - 1.1]),
               "the lean is the perspective: near struts kept more\n"
               "of their size than far ones", AMBER)


def scene_sc_screen(app, opaque, transparent, p: float) -> None:
    """The frame itself, with one vertex landing on its real pixel."""
    width, height = 11.0, 6.19
    centre = np.array([_math_shift(app), 0.0, 4.0])
    grow = max(0.18, ease_in_out(clamp(p * 1.8)))
    half_w, half_h = width * 0.5 * grow, height * 0.5 * grow
    corners = [centre + np.array([sx * half_w, 0.0, sy * half_h])
               for sx, sy in ((1, 1), (-1, 1), (-1, -1), (1, -1))]
    transparent.quad(*corners, (0.05, 0.17, 0.28, 0.30))
    for index in range(4):
        opaque.cylinder(corners[index], corners[(index + 1) % 4],
                        0.05, WHITE, 5)

    if p > 0.28:
        for column in range(1, 8):
            x = half_w - column * (2 * half_w / 8)
            opaque.cylinder(centre + np.array([x, 0.0, -half_h]),
                            centre + np.array([x, 0.0, half_h]),
                            0.012, _fade(MUTED, 0.55), 4)
        for row in range(1, 5):
            z = half_h - row * (2 * half_h / 5)
            opaque.cylinder(centre + np.array([-half_w, 0.0, z]),
                            centre + np.array([half_w, 0.0, z]),
                            0.012, _fade(MUTED, 0.55), 4)
        _label(app, centre + np.array([half_w - 1.4, -0.1,
                                       half_h - 0.5]),
               f"{FRAME_WIDTH} x {FRAME_HEIGHT} pixels", WHITE)

    if p > 0.45:
        _projection, _view, mvp = reference_matrices()
        pixel = project_point(mvp, APEX_WORLD, FRAME_WIDTH, FRAME_HEIGHT)
        if pixel is not None:
            u = pixel[0] / FRAME_WIDTH
            v = pixel[1] / FRAME_HEIGHT
            spot = centre + np.array([half_w - u * 2 * half_w, -0.10,
                                      half_h - v * 2 * half_h])
            opaque.sphere(spot, 0.22, AMBER, 6, 10)
            opaque.cylinder(spot + np.array([0.0, 0.0, 0.0]),
                            centre + np.array([half_w, 0.0, spot[2]
                                               - centre[2]]),
                            0.02, _fade(AMBER, 0.7), 4)
            opaque.cylinder(spot,
                            centre + np.array([spot[0] - centre[0], 0.0,
                                               half_h]),
                            0.02, _fade(AMBER, 0.7), 4)
            _label(app, spot + np.array([0.0, 0.0, -0.9]),
                   f"the top of the dome\npx {pixel[0]:.0f}   "
                   f"py {pixel[1]:.0f}", AMBER)
    if p > 0.78:
        _label(app, centre + np.array([0.0, 0.0, -half_h - 1.0]),
               "0,0 is the top left corner, not the middle", MUTED)


def scene_sc_depth(app, opaque, transparent, p: float) -> None:
    """Three panels straight down the view axis, drawn nearest first.

    They are placed along the chapter camera's own forward direction and
    turned to face it, so they really do overlap on screen -- and the
    nearest really does win, though it was drawn before the others.
    """
    eye = np.asarray(eye_position(DEPTH_CAMERA), dtype=float)
    target = np.asarray(SETTINGS.target, dtype=float)
    forward = normalize(target - eye)
    right = normalize(np.cross(forward, np.array([0.0, 0.0, 1.0])))
    up = normalize(np.cross(right, forward))

    layout = ((11.0, -1, GREEN), (15.0, 0, AMBER), (19.0, 1, CYAN))
    # Placed along the camera's own line of sight, which means checking
    # they clear the ground: a panel that sinks under it is hidden by
    # the ground rather than by the panel in front of it.
    distances = sorted(item[0] for item in layout)
    rank = {distance: name for distance, name in
            zip(distances, ("nearest", "middle", "furthest"))}

    reveal = clamp(p * 2.2)
    for index, (distance, step, colour) in enumerate(layout):
        if index / len(layout) > reveal:
            continue
        # Sized and spaced in proportion to their distance, so all three
        # arrive the same size on screen and overlap by about half: the
        # only thing left to tell them apart is which one won.
        half = 0.130 * distance
        centre = (eye + forward * distance
                  + right * (0.200 * step + 0.115) * distance
                  + up * -0.045 * step * distance)
        assert centre[2] > 0.4, "a depth panel sank into the ground"
        corners = [centre + right * sx * half + up * sy * half
                   for sx, sy in ((1, 1), (-1, 1), (-1, -1), (1, -1))]
        opaque.quad(*corners, _fade(colour, 1.0), -forward)
        for edge in range(4):
            opaque.cylinder(corners[edge], corners[(edge + 1) % 4],
                            0.05, WHITE, 5)
        _label(app, centre - up * (half + 0.8),
               f"{rank[distance]}\n{distance:.2f} units from the lens\n"
               f"depth = {depth_value(distance):.6f}", colour)
    if p > 0.62:
        _label(app, eye + forward * 15.0 - up * 4.4 + right * 1.6,
               "drawn nearest first, and the two behind it were still\n"
               "rejected one pixel at a time. No sorting happened.", WHITE)

def scene_sc_cull(app, opaque, transparent, p: float) -> None:
    """Half of every closed surface points away from you."""
    eye = np.asarray(eye_position(CULL_CAMERA), dtype=float)
    count = 18
    radius = 5.4
    facing = 0
    for index in range(count):
        angle = math.tau * index / count
        outward = np.array([math.cos(angle), math.sin(angle), 0.0])
        centre = outward * radius + np.array([0.0, 0.0, 2.6])
        side = np.cross(outward, np.array([0.0, 0.0, 1.0]))
        corners = [centre - side * 1.05 - np.array([0.0, 0.0, 1.5]),
                   centre + side * 1.05 - np.array([0.0, 0.0, 1.5]),
                   centre + np.array([0.0, 0.0, 1.9])]
        # Wind each triangle so its front is its outward face; listed
        # the other way round the card would cull the ones this chapter
        # is about to call "kept".
        normal = normalize(np.cross(corners[1] - corners[0],
                                    corners[2] - corners[0]))
        if float(np.dot(normal, outward)) < 0.0:
            corners = [corners[0], corners[2], corners[1]]
        toward_eye = float(np.dot(outward, normalize(eye - centre)))
        if toward_eye > 0.0:
            facing += 1
            opaque.triangle(corners[0], corners[1], corners[2],
                            _fade(CYAN, 0.95))
            for edge in range(3):
                opaque.cylinder(corners[edge], corners[(edge + 1) % 3],
                                0.05, WHITE, 5)
        else:
            dropped = clamp((p - 0.40) * 2.5)
            alpha = 0.5 * (1.0 - dropped)
            if alpha > 0.02:
                transparent.triangle(corners[0], corners[1], corners[2],
                                     _fade(RED, alpha))
                transparent.triangle(corners[0], corners[2], corners[1],
                                     _fade(RED, alpha))
    _label(app, np.array([0.0, 0.0, 7.8]),
           f"{count} triangles in a ring, every one facing outward", WHITE)
    if p > 0.34:
        _label(app, np.array([0.0, 0.0, 6.6]),
               f"n . v > 0 for {facing}: kept and shaded", CYAN)
    if p > 0.52:
        _label(app, np.array([0.0, 0.0, -0.9]),
               f"n . v <= 0 for {count - facing}: dropped before a single\n"
               "pixel of them is ever coloured", RED)

def scene_sc_light(app, opaque, transparent, p: float) -> None:
    """The four directions the shading equation actually uses.

    Seen from the side, deliberately: the numbers on the math screen
    describe the panel as the film's own camera sees it, so watching
    from somewhere else is the only way to see the direction to that
    camera as an arrow rather than as a dot.
    """
    sample = lighting_sample()
    dome_batch(1.0, into=opaque)
    centre = np.asarray(sample.centre, dtype=float)
    corners = [np.asarray(corner, dtype=float) for corner in sample.corners]
    opaque.triangle(corners[0], corners[1], corners[2], _fade(WHITE, 0.55),
                    np.asarray(sample.normal, dtype=float))
    transparent.triangle(corners[0], corners[2], corners[1],
                         _fade(WHITE, 0.25))

    if p > 0.20:
        eye = np.asarray(eye_position(REFERENCE_CAMERA), dtype=float)
        distance = float(np.linalg.norm(eye - centre))
        # Drawn along the true direction but closer in, or it lands off
        # the edge of the frame; the label says how far out it really is.
        marker = centre + np.asarray(sample.view) * 5.4
        _camera_body(opaque, marker, centre, 0.9)
        _label(app, marker + np.array([0.0, 0.0, 1.4]),
               f"the film's own camera\n{distance:.1f} units out this way",
               PURPLE)
    if p > 0.30:
        sun = centre + np.asarray(sample.light) * 7.5
        opaque.sphere(sun, 0.55, AMBER, 6, 10)
        for spoke in range(8):
            angle = math.tau * spoke / 8.0
            offset = np.array([math.cos(angle) * 0.95,
                               math.sin(angle) * 0.95, 0.55])
            opaque.cylinder(sun, sun + offset, 0.05, AMBER, 4)
        _label(app, sun + np.array([0.0, 0.0, 1.3]), "the light", AMBER)

    arrows = (
        (sample.normal, WHITE, "n  the panel's own direction", 0.10, 3.4),
        (sample.light, AMBER,
         f"l  to the light\nn . l = {sample.diffuse:.4f}", 0.26, 5.6),
        (sample.view, CYAN, "v  to the eye", 0.44, 4.6),
        (sample.half, GREEN,
         f"h  halfway\n(n . h) ^ 42 = {sample.specular:.4f}", 0.62, 2.4),
    )
    for direction, colour, name, threshold, length in arrows:
        if p < threshold:
            continue
        opaque.arrow(centre, centre + np.asarray(direction) * length,
                     0.075, colour)
        _label(app, centre + np.asarray(direction) * (length + 0.9),
               name, colour)
    if p > 0.80:
        _label(app, np.array([0.0, 0.0, SCALE + 2.2]),
               f"one panel, one light, one eye\n"
               f"brightness out = {sample.lit:.4f}", WHITE)

def scene_sc_blend(app, opaque, transparent, p: float) -> None:
    """The skin goes on last, and does not write depth."""
    dome_batch(1.0, into=opaque)
    fade = clamp((p - 0.15) * 1.8)
    if fade > 0.02:
        shown = int(round(len(GEOMETRY.hemisphere_faces) * fade))
        for index, face in enumerate(GEOMETRY.hemisphere_faces):
            if index >= shown:
                break
            a, b, c = (GEOMETRY.vertices[int(corner)] * SCALE
                       for corner in face)
            transparent.triangle(a, b, c, (0.10, 0.42, 0.62, 0.34))
    _label(app, np.array([0.0, 0.0, SCALE + 1.7]),
           "opaque frame first, glazing second", WHITE)
    if p > 0.55:
        _label(app, np.array([0.0, 0.0, SCALE + 0.2]),
               "result = new colour x a + old colour x (1 - a)", CYAN)
    if p > 0.75:
        _label(app, np.array([0.0, 0.0, -0.6]),
               "depth writing is switched off for these panels, or the\n"
               "first one drawn would hide the ones behind it", AMBER)


def scene_sc_frame(app, opaque, transparent, p: float) -> None:
    """The loop: the whole calculation, thirty times a second."""
    count = 9
    spacing = 2.35
    shift = _math_shift(app)
    active = int(clamp(p) * (count - 1))
    for index in range(count):
        x = (count / 2.0 - index - 0.5) * spacing - 1.4 + shift
        current = index == active
        # A dark slate with the frame drawn on it, rather than a filled
        # panel: a filled one hides the very picture it is meant to hold.
        opaque.box(np.array([x, 0.0, 3.5]), np.array([2.05, 0.14, 1.55]),
                   _fade(MUTED, 0.30))
        if current:
            for corner in ((-1, -1), (1, -1), (1, 1), (-1, 1)):
                nxt = {(-1, -1): (1, -1), (1, -1): (1, 1),
                       (1, 1): (-1, 1), (-1, 1): (-1, -1)}[corner]
                opaque.cylinder(
                    np.array([x + corner[0] * 1.02, -0.1,
                              3.5 + corner[1] * 0.78]),
                    np.array([x + nxt[0] * 1.02, -0.1,
                              3.5 + nxt[1] * 0.78]), 0.055, CYAN, 5)
        dome_batch(1.0 if index <= active else 0.0,
                   origin=np.array([x, -0.35, 3.02]), scale=0.86,
                   hubs=False, into=opaque)
    _label(app, np.array([shift, 0.0, 5.4]),
           f"{count} frames of {30} -- a third of one second", WHITE)
    if p > 0.35:
        _label(app, np.array([shift, 0.0, 1.7]),
               "each one: clear, rebuild, upload, project, depth-test,\n"
               "shade, draw the panel, swap", CYAN)
    if p > 0.70:
        triangles = len(dome_batch().vertices) // 30
        _label(app, np.array([shift, 0.0, 0.5]),
               f"{triangles:,} triangles in 33.33 milliseconds", AMBER)


SCENES = {
    "sc_pipeline": scene_sc_pipeline,
    "sc_euler": scene_sc_euler,
    "sc_hemisphere": scene_sc_hemisphere,
    "sc_tube": scene_sc_tube,
    "sc_winding": scene_sc_winding,
    "sc_buffer": scene_sc_buffer,
    "sc_world": scene_sc_world,
    "sc_orbit": scene_sc_orbit,
    "sc_view": scene_sc_view,
    "sc_frustum": scene_sc_frustum,
    "sc_clip": scene_sc_clip,
    "sc_screen": scene_sc_screen,
    "sc_depth": scene_sc_depth,
    "sc_cull": scene_sc_cull,
    "sc_light": scene_sc_light,
    "sc_blend": scene_sc_blend,
    "sc_frame": scene_sc_frame,
}

# Stages drawn by the renderer's own built-in painters: the original 2V
# lesson's scenes, reused here where they already show exactly the right
# thing.  They need no entry in SCENES, but the selftest has to know
# they are real.
BUILTIN_STAGES = {
    "hero", "rigidity", "platonic", "coordinates", "icosahedron",
    "midpoints", "projection", "classes", "derivations", "cutlist",
    "finale",
}


# ======================================================================
# The chapters
# ======================================================================

def _math(slug: str, title: str, promise: str, narration: tuple[str, ...],
          steps: tuple[str, ...], duration: float,
          camera: tuple[float, float, float], stage: str) -> Chapter:
    """A math screen: picture on the left, derivation on the right."""
    return Chapter(slug, "00", title, promise, narration, steps,
                   duration, camera, stage, "math")


_AUTHORED: tuple[Chapter, ...] = (
    # ------------------------------------------------------------------
    # ACT 0 -- what we are about to compute
    # ------------------------------------------------------------------
    Chapter(
        "open", "00", "Nothing but arithmetic",
        "A dome on a screen is two calculations: a shape, and a picture.",
        (
            "Everything you are looking at started as arithmetic. There is no",
            "model file behind this dome, no artist, and no drawing. There is one",
            "number, a handful of formulas, and a list of instructions for turning",
            "the answers into coloured pixels.",
            "Over the next half hour we are going to do the whole job from",
            "nothing. First the shape: how a computer works out where the corners",
            "of a geodesic dome go, and how long each piece of timber has to be.",
            "Then the picture: how those corners become tubes and triangles, how a",
            "camera gets placed with two angles, and how a point in space turns",
            "into a particular pixel on your screen.",
            "Every number you see on a math screen in this film is worked out",
            "while the frame is being drawn, by the same code drawing it.",
        ),
        ("shape: 12 points -> 2 strut lengths",
         "picture: 3 matrices -> 1 divide -> pixels"),
        26.0, (30.0, 22.0, 15.5), "hero",
    ),
    Chapter(
        "pipeline", "00", "The seven stations",
        "Seven steps stand between one number and a lit pixel.",
        (
            "Here is the whole road, laid out. Station one: a single irrational",
            "number places twelve points in space. Station two: we divide each",
            "point by its own length, which puts them all on a sphere of radius",
            "one and turns the model into a recipe instead of a specific object.",
            "Station three: we halve every edge, which gives us more points, in",
            "slightly the wrong place. Station four: we push those points outward",
            "until they reach the sphere, and that single push is what makes the",
            "shape geodesic.",
            "Station five: the shape becomes a mesh, because a graphics card can",
            "only draw triangles. Station six: a camera is placed, and the whole",
            "world is moved in front of it. Station seven: a divide, a stretch,",
            "and a lighting sum turn all of that into the picture you are",
            "watching.",
            "Every station is a formula. We are going to do all seven.",
        ),
        ("geometry -> mesh -> camera -> pixels",),
        30.0, (90.0, 13.0, 37.0), "sc_pipeline",
    ),

    # ------------------------------------------------------------------
    # ACT I -- the shape
    # ------------------------------------------------------------------
    Chapter(
        "why_triangles", "00", "Why the shape is triangles at all",
        "A triangle cannot change shape without changing a side length.",
        (
            "Before any arithmetic, one decision. Why triangles?",
            "Push the top of a square frame and it leans over: the corners turn",
            "and the sides stay the same length. The shape has somewhere to go.",
            "Push the top of a triangle and nothing can move unless one of the",
            "three sides gets longer or shorter, which timber and steel are very",
            "unwilling to do.",
            "That is the whole reason a dome is made of triangles rather than",
            "panels. It is also, conveniently, the reason computer graphics is",
            "made of triangles: three points always lie in one flat plane, so a",
            "triangle can never be bent or twisted, and the maths for drawing one",
            "never has a special case.",
            "The same fact serves the builder and the renderer.",
        ),
        ("a triangle is fixed by its three side lengths",
         "three points always lie in one plane"),
        24.0, (35.0, 26.0, 15.0), "rigidity",
    ),
    Chapter(
        "why_ico", "00", "Why we start from the icosahedron",
        "Of the five perfectly regular solids, one starts closest to a ball.",
        (
            "We need a starting shape whose corners are spread as evenly as",
            "possible over a sphere, because every correction we make later is",
            "smaller when we start closer.",
            "There are exactly five solids where every face is the same regular",
            "polygon and every corner is identical: the tetrahedron with four",
            "faces, the cube with six, the octahedron with eight, the dodecahedron",
            "with twelve and the icosahedron with twenty. Five. That is not a",
            "shortlist, it is all of them that can exist.",
            "The icosahedron wins because twenty triangular faces already sit",
            "close to the surface of a ball, and because its faces are triangles",
            "to begin with, so subdividing them gives more triangles rather than",
            "some new shape we would have to think about.",
        ),
        ("faces: 4, 6, 8, 12, 20",
         "20 triangles start closest to a sphere"),
        26.0, (32.0, 25.0, 18.0), "platonic",
    ),
    Chapter(
        "coordinates", "00", "Twelve points from one number",
        "Three rectangles, one ratio, twelve perfectly spaced corners.",
        (
            "Here is where the arithmetic starts, and it starts with one number.",
            "Phi, written with the Greek letter that looks like a circle with a",
            "line through it, is one plus the square root of five, all divided by",
            "two. About one point six one eight.",
            "Take three rectangles, each one phi long and two units wide, and",
            "stand them at right angles to each other through a common centre.",
            "Their twelve corners are the twelve corners of an icosahedron. In",
            "coordinates that means every combination of zero, plus or minus one,",
            "and plus or minus phi, in each of three orders.",
            "That is the entire input to this project. One number, arranged.",
        ),
        ("phi = (1 + sqrt 5) / 2 = 1.618034",
         "(0, +/-1, +/-phi) and its two rotations"),
        26.0, (30.0, 22.0, 16.0), "coordinates",
    ),
    _math(
        "m_phi", "Where the twelve points come from",
        "One number, three families of coordinates, twelve even points.",
        (
            "Let us do that properly, on the math screen. Phi is defined as one",
            "plus the square root of five over two. Its defining property is that",
            "phi squared equals phi plus one, which is what makes it turn up",
            "whenever a shape has fivefold symmetry.",
            "Writing zero, plus or minus one and plus or minus phi in three",
            "rotating orders gives three families of four points each: twelve in",
            "total. The bars either side of v mean the length of v, which is the",
            "square root of x squared plus y squared plus z squared, straight out",
            "of Pythagoras in three dimensions.",
            "Measure the closest pair of those twelve points and you get exactly",
            "two. Measure any point's distance from the centre and you get the",
            "square root of one plus phi squared, the same for all twelve. Even",
            "spacing, and a common radius, for free.",
        ),
        steps_phi(), 52.0, (30.0, 22.0, 21.0), "coordinates",
    ),
    Chapter(
        "normalize", "00", "Putting them on a sphere of radius one",
        "Divide every point by its own length and the model becomes a recipe.",
        (
            "Those twelve points sit at a radius of one point nine oh two, which",
            "is a useless number to design with. So we normalize.",
            "Normalizing means dividing a point's coordinates by its own distance",
            "from the centre. The direction is untouched. Only the distance",
            "changes, and it becomes exactly one.",
            "Now every measurement on this model is a fraction of the radius",
            "rather than a length. That is the single most useful thing in this",
            "whole film, because it means we never have to redo the geometry. Pick",
            "a radius at the very end, multiply, and the same numbers give you a",
            "greenhouse or an aircraft hangar.",
        ),
        ("v_hat = v / |v|", "edge = 2 / sqrt(1 + phi^2) = 1.051462 R"),
        24.0, (27.0, 25.0, 14.5), "icosahedron",
    ),
    _math(
        "m_normalize", "The divide that makes it reusable",
        "Length one in, length one out; every distance becomes a multiplier.",
        (
            "On screen: the raw points, their awkward radius, and the divide that",
            "fixes it. V hat, spoken as v-hat, is the usual way to write a vector",
            "that has been scaled to length one.",
            "Check the result and every one of the twelve now sits at radius one,",
            "to the last decimal place a computer can hold. The edge that measured",
            "exactly two now measures one point zero five one four six two.",
            "That number is called a chord factor. It is not a length. It is what",
            "you multiply a radius by to get a length. Chord factor times radius",
            "in inches gives inches; times radius in metres gives metres. The",
            "geometry no longer knows or cares which.",
        ),
        steps_normalize(), 48.0, (27.0, 25.0, 19.5), "icosahedron",
    ),
    Chapter(
        "counting", "00", "Counting the surface",
        "Corners, edges and faces, and the check that catches every mistake.",
        (
            "Before going further we should check that what we have built is",
            "actually a closed surface and not a bag with a hole in it.",
            "Count the corners: twelve. Count the triangular faces: twenty. Each",
            "face has three sides, and every side is shared with exactly one",
            "neighbour, so the number of edges is twenty times three divided by",
            "two, which is thirty.",
            "Now add them up in a particular way: corners minus edges plus faces.",
            "For any closed surface without holes, that always comes to two. It is",
            "true of a cube, a pyramid, a football and this icosahedron. If it",
            "does not come to two, something in the model is broken, and it is far",
            "cheaper to find that out now than after cutting the timber.",
        ),
        ("V - E + F = 2", "E = F x 3 / 2 = 30"),
        26.0, (30.0, 24.0, 16.5), "sc_euler",
    ),
    _math(
        "m_euler", "Euler's check",
        "One addition proves the model closed.",
        (
            "Here is the count, run live against the model on the left. V for",
            "vertices, which is just a mathematician's word for corners. E for",
            "edges. F for faces.",
            "The reason edges equal faces times three over two is worth saying",
            "slowly: every triangle contributes three sides, but each side is",
            "shared between two triangles, so counting sides double-counts every",
            "edge. Divide by two and the double counting goes away.",
            "Twelve minus thirty plus twenty is two. And when we subdivide later",
            "and end up with forty-two corners, a hundred and twenty edges and",
            "eighty faces, the same sum still gives two. That is not a",
            "coincidence, it is a property of any closed surface, and it is the",
            "cheapest bug detector in geometry.",
        ),
        steps_euler(), 50.0, (30.0, 24.0, 21.0), "sc_euler",
    ),
    Chapter(
        "midpoints", "00", "Cutting every edge in half",
        "Thirty new points, all of them slightly too close to the centre.",
        (
            "Twenty triangles is not enough for a building. To get more, we",
            "subdivide: mark the midpoint of every edge, and use those midpoints",
            "to cut each triangle into four smaller ones.",
            "The midpoint of two points is the plainest formula in this film. Add",
            "the two sets of coordinates together and halve them. That is all an",
            "average is.",
            "But look at where the midpoint lands. The two ends of the edge are on",
            "the sphere. The straight line between them cuts through the inside of",
            "the sphere, so its middle is nearer the centre than the ends are.",
            "Measure it and you get zero point eight five zero, not one. Those",
            "points are in the wrong place, and fixing that is the next step.",
        ),
        ("m = (a + b) / 2", "|m| = 0.850651, not 1"),
        26.0, (30.0, 24.0, 14.5), "midpoints",
    ),
    _math(
        "m_midpoint", "How far in the midpoint falls",
        "The straight line cuts the corner; the sag is fifteen percent.",
        (
            "The numbers behind that. A and b both have length one, because we",
            "normalized them. Their average has length zero point eight five zero",
            "six five one.",
            "The difference, about zero point one four nine of the radius, is how",
            "far short of the surface the midpoint lands. That sounds small until",
            "you scale it: on the dome this project measures, with a radius just",
            "under ten feet, it is more than seventeen inches of sag.",
            "If you stop here you do get a valid shape. It is a subdivided",
            "icosahedron: twenty triangles turned into eighty, but still visibly",
            "faceted, with the original twenty flat faces staring back at you. It",
            "is not a dome, and its struts come in the wrong lengths.",
        ),
        steps_midpoint(), 48.0, (30.0, 24.0, 19.5), "midpoints",
    ),
    Chapter(
        "project", "00", "The push that makes it geodesic",
        "One divide moves thirty points onto the sphere and changes everything.",
        (
            "Here is the step the whole shape turns on, and it is the same divide",
            "we already used.",
            "Take a midpoint. Draw a ray from the centre of the sphere through it,",
            "and slide the point along that ray until it is exactly one radius",
            "from the centre. That is projection. In arithmetic it is p equals m",
            "divided by the length of m: same direction, new distance.",
            "Watch what it does. The point moves out, so the four small triangles",
            "in each original face are no longer flat and no longer identical. The",
            "surface stops being twenty flat plates and starts being a sphere.",
            "And the edges, which were all equal a moment ago, are now two",
            "different lengths.",
            "One divide. That is the difference between a faceted ball and a",
            "geodesic dome.",
        ),
        ("p = m / |m|", "the surface bulges; the edges split into two"),
        28.0, (29.0, 22.0, 14.5), "projection",
    ),
    _math(
        "m_project", "Projection, exactly",
        "Same direction, distance set to the radius.",
        (
            "Formally: p equals m over the length of m. Dividing a vector by its",
            "own length always gives length one, and never changes which way it",
            "points, which is exactly what we want. The point travels along its",
            "own ray and lands on the surface.",
            "Every one of the thirty midpoints moves out by the same fraction of",
            "the radius, because on this shape they all started at the same depth.",
            "But they move away from their neighbours by different amounts",
            "depending on where those neighbours are, and that is what splits one",
            "edge length into two.",
            "This is also why the word geodesic is used. A geodesic is the",
            "shortest path across a curved surface, and these struts are straight",
            "lines standing in for exactly those paths.",
        ),
        steps_project(), 50.0, (29.0, 22.0, 19.5), "projection",
    ),
    Chapter(
        "classes", "00", "Measuring what came out",
        "A hundred and twenty edges, and exactly two different lengths.",
        (
            "Now we simply measure. Every edge of the new surface, one at a time,",
            "and then sort the answers.",
            "A hundred and twenty edges come back with exactly two distinct",
            "lengths and nothing in between. Not approximately two: two, to the",
            "limit of what a computer can represent. The colours you are looking",
            "at are assigned by that measurement, not by a naming convention.",
            "The shorter one runs from an original corner to a projected midpoint.",
            "The longer one runs between two projected midpoints. Published dome",
            "tables call them A and B, but different tables disagree about which",
            "is which, so this project says SHORT and LONG and stays out of the",
            "argument.",
        ),
        ("SHORT = 0.546533 R", "LONG = 0.618034 R"),
        26.0, (31.0, 25.0, 14.5), "classes",
    ),
    _math(
        "m_chords", "Two lengths, four ways",
        "Coordinates, angles, the law of cosines and CAD all agree.",
        (
            "The two chord factors, and four independent ways of getting them.",
            "Route one is brute force: subtract one end's coordinates from the",
            "other's and take the length of what is left.",
            "Route two goes through the angle. The dot product of two unit vectors",
            "is the cosine of the angle between them, so the inverse cosine of u",
            "dot v gives the central angle: the angle subtended at the centre of",
            "the sphere. Feed that into chord equals two R sine of theta over two,",
            "which is the standard chord formula from any circle, and out comes",
            "the same number.",
            "They agree to about one part in ten thousand million million, which",
            "is floating point dust rather than disagreement.",
            "And look at the long one: zero point six one eight zero three four.",
            "That is one over phi, exactly. But the ratio between the two struts",
            "is one point one three, not phi. People expect the golden ratio to",
            "come out at the end because it went in at the start. It does not.",
        ),
        steps_chords(), 60.0, (31.0, 25.0, 19.5), "classes",
    ),
    Chapter(
        "cross_check", "00", "Never trust one calculation",
        "Four routes to the same number is not waste; it is the proof.",
        (
            "It is worth saying why we bothered doing that four different ways.",
            "A single calculation that agrees with itself proves nothing. Four",
            "calculations that share no working, and land on the same number,",
            "prove that the number is a property of the shape rather than an",
            "artefact of one method or one typo.",
            "This is the habit that separates a model you can build from a model",
            "that merely runs. Every figure in this repository is computed, and",
            "wherever there are two ways to compute it, both are checked against",
            "each other before anything reaches a screen.",
        ),
        ("c = |R u - R v|", "theta = acos(u . v)", "c = 2 R sin(theta / 2)"),
        22.0, (29.0, 24.0, 14.0), "derivations",
    ),
    Chapter(
        "hemisphere", "00", "Half a sphere is a building",
        "Keep every face above the equator and count what you have.",
        (
            "A sphere is not a house. Cut it at the equator and keep the top, and",
            "now it is one.",
            "The cut is trivial in code: keep every face whose three corners all",
            "sit at or above zero height. This particular arrangement of the",
            "icosahedron has a genuine ring of corners exactly at the equator, so",
            "the cut is clean, with no half-triangles to fudge.",
            "What survives is forty triangular panels, sixty-five struts, and",
            "twenty-six hubs where those struts meet. Thirty of the struts are the",
            "short one and thirty-five are the long one. Ten corners sit on the",
            "ground, and that ring is what your foundation follows.",
        ),
        ("keep faces with all z >= 0",
         "40 panels, 65 struts, 26 hubs"),
        26.0, (30.0, 23.0, 16.5), "sc_hemisphere",
    ),
    _math(
        "m_counts", "Counting the building",
        "Every part, counted off the model rather than looked up.",
        (
            "These are counts, made now, off the same model being drawn beside",
            "the panel. Forty panels. Thirty short struts, thirty-five long ones,",
            "sixty-five in total. Twenty-six hubs.",
            "The cross-check is the same shared-edge argument as before. Forty",
            "triangles have a hundred and twenty sides between them, but most of",
            "those sides are shared with a neighbouring triangle, and the ones",
            "around the open base are not shared at all. Work through it and a",
            "hundred and twenty side-slots close up into exactly sixty-five real",
            "struts.",
            "Two lengths and a count. That is the entire bill of materials for the",
            "frame of a building.",
        ),
        steps_counts(), 50.0, (30.0, 23.0, 21.0), "sc_hemisphere",
    ),
    Chapter(
        "scale", "00", "Choosing a size, at last",
        "One multiplication turns the recipe into a cut list.",
        (
            "Everything so far has been unit-free. Now we choose a size, and we do",
            "it exactly once.",
            "This project started from two real boards someone measured: seventy",
            "two inches and sixty three and a half. Divide each by its chord",
            "factor and each board implies a radius. The two answers differ",
            "slightly, because tape measures, saw kerfs and hub fittings are real",
            "things.",
            "Rather than pick a favourite, we use least squares: the radius that",
            "makes the total of the squared misses as small as possible. It lands",
            "between the two, missing each by about a tenth of an inch.",
            "Multiply the two chord factors by that radius and you have a cut",
            "list. Thirty pieces at one length, thirty-five at the other, and a",
            "note that those are hub centre to hub centre, not saw cuts.",
        ),
        ("R = length / chord factor",
         "cut length = centre length - connector deduction"),
        28.0, (31.0, 25.0, 15.0), "cutlist",
    ),
    _math(
        "m_scale", "From factors to lumber",
        "Two boards, one best-fit radius, sixty-five cuts.",
        (
            "The fit, in full. Each measured board on its own implies a radius,",
            "and the two disagree by about a third of an inch.",
            "Least squares is worth a sentence, because it sounds harder than it",
            "is. Each candidate radius predicts a length for each board. Subtract",
            "the prediction from the measurement and you get a residual: how wrong",
            "that guess was. Square the residuals so that overshoot and undershoot",
            "both count as error, add them up, and pick the radius where that",
            "total is smallest. There is a formula that jumps straight to the",
            "answer, and that is what the code uses.",
            "The result is a dome a shade under twenty feet across, with about",
            "three hundred square feet of floor, and two numbers on a cut list.",
            "Notice the last line. What comes out is the distance between hub",
            "centres. What your saw needs is that minus whatever your connector",
            "occupies at each end, and no geometry can tell you that. Your",
            "hardware does.",
        ),
        steps_scale(), 58.0, (31.0, 25.0, 20.0), "cutlist",
    ),

    # ------------------------------------------------------------------
    # ACT II -- from a shape to a mesh
    # ------------------------------------------------------------------
    Chapter(
        "tube", "00", "A line with no thickness",
        "Graphics cards draw triangles. Nothing else. Not even lines.",
        (
            "The shape is finished. Now we have to make it visible, and the first",
            "surprise is that we cannot simply draw it.",
            "A graphics card draws triangles. That is very nearly the whole of its",
            "vocabulary. Our struts are pairs of points with no thickness at all,",
            "so each one has to be given a body: a tube, built out of triangles,",
            "wrapped around the line where the strut goes.",
            "To build a ring around a line you need two directions square to that",
            "line. The cross product gives you them. Cross the strut direction",
            "with any other direction and you get something perpendicular to both;",
            "cross that with the strut again and you have a second perpendicular.",
            "Now you can walk in a circle around the axis using sine and cosine,",
            "the way you would around any circle.",
        ),
        ("d = (b - a) / |b - a|", "s = d x t,  u = d x s"),
        28.0, (88.0, 18.0, 17.5), "sc_tube",
    ),
    _math(
        "m_tube", "Building one strut",
        "Two cross products, eight points, twenty-eight triangles.",
        (
            "The arithmetic for one strut. D is the direction, found by",
            "subtracting the ends and normalizing, which by now should feel",
            "familiar.",
            "T is any convenient direction that is not parallel to d. The code",
            "picks straight up unless the strut is nearly vertical, in which case",
            "it picks sideways instead, because crossing two parallel directions",
            "gives you nothing at all.",
            "The ring formula is just a circle drawn in the plane defined by s and",
            "u. Two pi i over n walks all the way round in n even steps. Do it at",
            "both ends and join corresponding points, and the tube is a strip of",
            "quadrilaterals, each of which is two triangles.",
            "Eight sides gives sixteen triangles of tube, plus twelve more to cap",
            "the ends: twenty-eight triangles for one strut. Multiply by",
            "sixty-five and the frame alone is one thousand eight hundred and",
            "twenty triangles.",
        ),
        steps_tube(), 56.0, (88.0, 18.0, 23.0), "sc_tube",
    ),
    Chapter(
        "winding", "00", "Which way does a triangle face?",
        "The order you list the corners in decides which side is the front.",
        (
            "A triangle needs a front and a back. Without one it cannot be lit,",
            "because lighting depends on the angle between the surface and the",
            "light, and it cannot be hidden, because there would be no way to tell",
            "the inside of the dome from the outside.",
            "The direction a face points is called its normal, and it comes from a",
            "cross product of two of its edges. Cross products care about order,",
            "so listing the corners a, b, c gives a normal pointing one way, and",
            "listing them a, c, b gives one pointing the other.",
            "The convention here, and in almost all graphics, is",
            "counter-clockwise as seen from the front. Get it backwards on one",
            "triangle and it disappears. Get it backwards everywhere and your dome",
            "turns inside out.",
        ),
        ("n = (b - a) x (c - a)", "counter-clockwise = facing you"),
        26.0, (90.0, 34.0, 17.0), "sc_winding",
    ),
    _math(
        "m_normal", "The normal, the area and the winding",
        "One cross product, three answers.",
        (
            "The cross product of two edge vectors gives a third vector at right",
            "angles to both, so it sticks straight out of the surface. Dividing it",
            "by its own length makes it exactly one long, which the lighting maths",
            "will assume later.",
            "The length you divided by was not wasted, either: it is twice the",
            "area of the triangle. So one cross product tells you which way the",
            "face points and how big it is.",
            "The check on the last line is a dot product between the normal and",
            "the direction from the dome's centre out to the face. It comes to",
            "very nearly plus one, which means the normal points outward, which",
            "means the corners were listed the right way round.",
            "This is the sort of check worth automating. A dome with one triangle",
            "wound backwards has a hole in it that only appears from one angle.",
        ),
        steps_normal(), 54.0, (90.0, 34.0, 21.5), "sc_winding",
    ),
    Chapter(
        "buffer", "00", "The model becomes a list of numbers",
        "Points, edges and faces all flatten into one long array.",
        (
            "At this point the elegant structure goes away. Corners, edges, faces,",
            "the classes of strut: none of that survives the trip to the graphics",
            "card.",
            "What the card gets is one flat list of numbers. Ten per vertex: three",
            "for where it is, three for which way its surface faces, and four for",
            "colour, the fourth being opacity. Three vertices in a row make a",
            "triangle. That is the entire format.",
            "It is deliberately wasteful. Corners that are shared between",
            "triangles are written out again for each one, because that lets every",
            "face carry its own flat normal and its own colour. Memory is cheap",
            "and the alternative is a picture where every strut is smeared into",
            "its neighbour.",
        ),
        ("10 floats per vertex = 40 bytes",
         "3 vertices = 1 triangle"),
        26.0, (90.0, 19.0, 18.5), "sc_buffer",
    ),
    _math(
        "m_buffer", "Counting the actual upload",
        "The dome beside this panel, in floats, vertices and kilobytes.",
        (
            "This is not an estimate. The list on the right counts the batch of",
            "numbers that the dome on the left was drawn from, in the frame you",
            "are watching.",
            "A float is a single number as a computer stores it, four bytes each.",
            "Ten of them per vertex is forty bytes. Three vertices per triangle is",
            "a hundred and twenty bytes per triangle.",
            "Three thousand nine hundred triangles, eleven thousand seven hundred",
            "vertices, four hundred and fifty seven kilobytes. That is the whole",
            "dome as the graphics card understands it, and it is rebuilt and sent",
            "across thirty times a second, because the animation may have changed",
            "something.",
            "For comparison, that is smaller than a single photograph.",
        ),
        steps_buffer(), 52.0, (90.0, 19.0, 23.0), "sc_buffer",
    ),

    # ------------------------------------------------------------------
    # ACT III -- the camera
    # ------------------------------------------------------------------
    Chapter(
        "world", "00", "Where things are: world space",
        "One agreed origin, three axes, and everything measured from them.",
        (
            "Before we can photograph the dome we have to agree where everything",
            "is. That agreement is called world space, and it is nothing more",
            "than a chosen origin and three directions at right angles.",
            "In this project, X and Y run along the ground and Z points up, which",
            "is the convention surveyors and architects use. The dome is built",
            "around the origin, at a radius of five world units.",
            "World units are not metres or feet. They are whatever we decide, and",
            "the geometry only cares about ratios. What matters is that the",
            "camera, the light and the model all speak the same units, because",
            "everything from here on is subtraction between positions.",
        ),
        ("origin = (0, 0, 0)", "+Z is up; the dome has radius 5"),
        24.0, (36.0, 28.0, 19.0), "sc_world",
    ),
    Chapter(
        "orbit", "00", "Placing the camera with two angles",
        "Yaw, pitch and distance become one point in space.",
        (
            "A camera needs a position and something to look at. Rather than type",
            "coordinates, we use the way a person actually thinks about a camera:",
            "how far around it is, how high up it is, and how far back.",
            "Those are yaw, pitch and distance. Yaw is the angle around the",
            "vertical axis, pitch is the angle up from the ground, and distance is",
            "simply how far from the thing being looked at.",
            "Turning them into a position is straight trigonometry. Cosine of the",
            "pitch tells you how much of the distance is spread out along the",
            "ground, and sine of the pitch tells you how much of it went upward.",
            "Split the ground part between X and Y using the cosine and sine of",
            "the yaw, and you have your point.",
            "Every chapter of this film states its camera as those three numbers.",
        ),
        ("eye = target + d (cos p cos y, cos p sin y, sin p)",),
        28.0, (60.0, 27.0, 34.0), "sc_orbit",
    ),
    _math(
        "m_eye", "The camera position, computed",
        "Two angles and a distance become a point you can check.",
        (
            "Here are the real numbers for a real chapter of this film: yaw",
            "thirty-four degrees, pitch twenty-four, distance fifteen, aimed at a",
            "point two and a quarter units above the origin, which is roughly the",
            "middle of the dome.",
            "Cosine of twenty-four degrees is about zero point nine one, so",
            "ninety-one percent of the distance lies along the ground. Sine of",
            "twenty-four is about zero point four one, so the rest went up.",
            "Out comes an eye position of about eleven point four, seven point",
            "seven, eight point four. And the check on the last line matters:",
            "measure from that point back to the target and you get fifteen point",
            "zero zero, which is the distance we asked for. If trigonometry has",
            "gone in the right slots, that check passes automatically.",
        ),
        steps_eye(), 52.0, (60.0, 27.0, 38.0), "sc_orbit",
    ),
    Chapter(
        "view", "00", "Moving the world instead of the camera",
        "The card has no camera. So we move everything else.",
        (
            "Here is the idea that surprises people most. A graphics card does not",
            "have a camera. It draws whatever is sitting in front of a fixed eye",
            "at the origin, looking down one particular axis, always.",
            "So instead of moving the camera to a good spot, we move the entire",
            "world so that the good spot lands on the origin. That transformation",
            "is called the view matrix, and it is built from three directions.",
            "Forward is from the eye toward the target. Right is the cross product",
            "of forward with a rough idea of up, which is why it comes out",
            "perfectly horizontal. And true up is right crossed with forward",
            "again, which corrects for the tilt of the camera.",
            "Three directions at right angles, and one offset for where the eye",
            "was. That is the whole matrix.",
        ),
        ("f = normalize(target - eye)", "r = f x up,  u = r x f"),
        28.0, (60.0, 27.0, 34.0), "sc_view",
    ),
    _math(
        "m_view", "The view matrix, entry by entry",
        "Three directions in the rows, minus the eye in the last column.",
        (
            "The three directions, and the matrix they build.",
            "Look at the top three rows. Each one is one of our directions, and",
            "multiplying a point by that row is a dot product, which measures how",
            "far along that direction the point lies. So the multiplication",
            "answers three questions at once: how far right, how far up, and how",
            "far forward, from the camera's point of view.",
            "The last column is where the eye's own position gets subtracted. It",
            "is written as minus each row dotted with the eye, which packs a",
            "rotation and a slide into one multiplication instead of two.",
            "The line showing r dot f as a number with e minus seventeen in it is",
            "not a mistake. It says the two directions are perpendicular to within",
            "the accuracy a computer can represent, which is as perpendicular as",
            "anything gets in floating point.",
        ),
        steps_view(), 56.0, (60.0, 27.0, 38.0), "sc_view",
    ),
    Chapter(
        "frustum", "00", "What the lens can see",
        "A pyramid with its tip cut off, and everything outside is discarded.",
        (
            "The camera cannot see everything. It sees a wedge: everything inside",
            "a certain angle, further away than a near limit and closer than a far",
            "one. The shape of that wedge is a pyramid with its tip cut off, and",
            "it has the excellent name frustum.",
            "The angle is the field of view. This film uses forty-eight degrees",
            "measured vertically, which is a slightly long lens: calm, not",
            "dramatic. The horizontal angle is wider, because the frame is wider",
            "than it is tall, and that ratio is called the aspect.",
            "The near and far limits exist for a practical reason we will get to:",
            "they set the range of depths the card can tell apart. Anything",
            "outside the frustum is thrown away before it costs anything to draw.",
        ),
        ("fov = 48 deg vertical", "near = 0.08, far = 120"),
        28.0, (62.0, 24.0, 30.0), "sc_frustum",
    ),
    _math(
        "m_projection", "The projection matrix",
        "The matrix does not shrink anything. It arranges the divide.",
        (
            "This is the matrix people find hardest, so here it is in pieces.",
            "F, on the top two rows, is one over the tangent of half the field of",
            "view. A narrow lens gives a big f, which spreads the picture out; a",
            "wide lens gives a small f, which squeezes more in. The x row is",
            "divided by the aspect so that a wide frame does not stretch",
            "everything sideways.",
            "The third row remaps depth into the range the card wants, using the",
            "near and far limits.",
            "The fourth row is where the magic actually lives, and it does almost",
            "nothing: it copies the point's depth, negated, into a fourth slot",
            "called w. No division has happened yet. All the matrix has done is",
            "put each point's distance somewhere the next step can find it.",
        ),
        steps_projection(), 56.0, (62.0, 24.0, 34.0), "sc_frustum",
    ),

    # ------------------------------------------------------------------
    # ACT IV -- pixels
    # ------------------------------------------------------------------
    Chapter(
        "clip", "00", "The divide that makes distance work",
        "Divide by w and the whole world folds into a two-unit cube.",
        (
            "Now the divide. Every point's x, y and z get divided by that fourth",
            "number, w, which is the point's distance from the camera.",
            "Because it is a division by distance, things twice as far away end up",
            "half as big. That is perspective. Not a special effect, not a",
            "formula for foreshortening: a division that had to happen anyway to",
            "get the numbers into range.",
            "What comes out is called normalized device coordinates, and",
            "everything the camera can see now lies inside a cube running from",
            "minus one to plus one on every axis. The wireframe on the left is",
            "this project's own dome, put through the real matrix and really",
            "divided. That is why it leans: the near struts kept more of their",
            "size than the far ones did.",
        ),
        ("ndc = clip / w", "everything visible is inside -1 .. +1"),
        28.0, (90.0, 22.0, 26.0), "sc_clip",
    ),
    Chapter(
        "screen", "00", "Landing on a pixel",
        "One stretch turns the cube into the frame you are watching.",
        (
            "The last step of position is almost insultingly simple after that.",
            "The cube runs from minus one to plus one. The frame runs from zero to",
            "nineteen twenty across and zero to ten eighty down. So: add one,",
            "halve it, multiply by the width. Same for height.",
            "The only wrinkle is that screens count rows downward from the top",
            "left, while our cube counts upward, so the vertical one gets flipped.",
            "That is the one minus in the formula.",
            "Every label you have seen floating over a strut in this film was",
            "placed by exactly this calculation, running on the point in the",
            "middle of that strut.",
        ),
        ("px = (ndc_x * 0.5 + 0.5) * width",
         "py = (1 - (ndc_y * 0.5 + 0.5)) * height"),
        26.0, (90.0, 18.0, 19.0), "sc_screen",
    ),
    _math(
        "m_pixel", "One vertex, all the way",
        "World, camera, clip, cube, pixel -- with the numbers at each stop.",
        (
            "Let us follow one point the whole way and watch it change at every",
            "stop. The point is the very top of the dome, five units above the",
            "origin, which we can all agree on without any arithmetic.",
            "Written as four numbers with a one on the end. That one marks it as a",
            "position rather than a direction, so that the sliding part of the",
            "view matrix applies to it.",
            "After the view matrix it is expressed from the camera's point of",
            "view, and its third number is depth into the screen.",
            "After the projection matrix, look at w: it is that same depth,",
            "waiting.",
            "Divide, and every number lands inside the cube. Stretch, and it lands",
            "on a pixel: nine hundred and sixty across, three hundred and twenty",
            "down. Nine sixty is exactly half of nineteen twenty, which is the",
            "check: the apex sits directly above the centre of a dome the camera",
            "is aimed at, so it must land on the vertical centre line.",
        ),
        steps_pixel(), 62.0, (90.0, 18.0, 24.0), "sc_screen",
    ),
    Chapter(
        "depth", "00", "What hides what",
        "No sorting. Every pixel just remembers how far away it is.",
        (
            "Two things want the same pixel. Which one wins?",
            "The obvious answer is to sort everything back to front and paint in",
            "order. Real graphics cards do not do that, because sorting thousands",
            "of triangles every frame is expensive, and because two triangles can",
            "overlap in ways that have no correct order at all.",
            "Instead every pixel keeps a second number beside its colour: the",
            "depth of whatever is currently drawn there. When a new fragment",
            "arrives, one comparison decides it. Nearer, keep it. Further, throw",
            "it away. No sorting, no ordering, and it works no matter what order",
            "the triangles arrive in.",
            "The three panels here are drawn in the worst possible order, back to",
            "front reversed, and the picture still comes out right.",
        ),
        ("keep the fragment with the smaller depth",),
        26.0, DEPTH_CAMERA, "sc_depth",
    ),
    _math(
        "m_depth", "Why depth precision runs out",
        "The divide that made perspective also warps the depth scale.",
        (
            "There is a catch, and it explains a bug every 3D artist has seen.",
            "Depth gets stored between zero and one, but not evenly. The same",
            "divide by w that produced perspective also squashes the depth scale,",
            "so distances close to the camera get an enormous share of the",
            "available precision and far ones get almost none.",
            "Look at the table. Between the near limit and twice the near limit",
            "the depth value uses half of its entire range. By fifteen units out",
            "it is changing in the fifth decimal place.",
            "When two far-off surfaces round to the same stored depth, the card",
            "cannot tell which is in front, and they flicker against each other as",
            "the camera moves. That is z-fighting. The cure is almost always to",
            "push the near limit further out, because that is the setting that",
            "governs how the precision is shared.",
        ),
        steps_depth(), 56.0, DEPTH_CAMERA, "sc_depth",
    ),
    Chapter(
        "cull", "00", "Throwing away half of everything",
        "On a closed surface, half the triangles face away from you.",
        (
            "Here is a free saving. On any closed shape, roughly half the surface",
            "is pointing away from you at any moment. You cannot see it, because",
            "the near half is in the way.",
            "So before doing any work on a triangle, the card checks its winding",
            "on screen. If the corners come out clockwise after projection, the",
            "triangle is facing away and it is dropped immediately: no depth test,",
            "no lighting, no pixels.",
            "The red ghosts fading out here are the ones being dropped. This is",
            "why the corner order mattered several chapters ago, and it is also",
            "why a model with one triangle wound backwards shows a hole from one",
            "side and a floating panel from the other.",
        ),
        ("clockwise after projection = facing away",
         "dropped before any shading happens"),
        26.0, CULL_CAMERA, "sc_cull",
    ),

    # ------------------------------------------------------------------
    # ACT V -- light, glass and the loop
    # ------------------------------------------------------------------
    Chapter(
        "light", "00", "How bright is this surface?",
        "Three directions, three dot products, one number.",
        (
            "Everything so far decided where things are. Now, how bright.",
            "The whole of the shading in this film comes from three directions",
            "and the angles between them. Where the surface faces, which is the",
            "normal we computed with a cross product. Where the light is. And",
            "where the eye is.",
            "The dot product of two directions of length one gives the cosine of",
            "the angle between them: one when they point the same way, zero at",
            "right angles, negative when they face apart. So a single dot product",
            "of the normal with the light direction answers the question a",
            "painter answers by eye: is this surface turned toward the light or",
            "away from it?",
            "That is Lambert's law, and it is nearly the whole of what you read as",
            "shape.",
        ),
        ("diffuse = max(n . l, 0)", "h = (l + v) / |l + v|"),
        28.0, (-36.0, 26.0, 25.0), "sc_light",
    ),
    _math(
        "m_light", "The lighting equation this film runs",
        "Real vectors, real constants, one brightness out.",
        (
            "These are the actual vectors for one actual panel of the dome",
            "standing beside the panel, and the actual constants from the shader",
            "program that this film's frames are drawn with.",
            "Diffuse is the normal dotted with the light direction, clamped so",
            "that a surface facing away goes dark rather than negative.",
            "The highlight uses a trick worth knowing. Rather than work out where",
            "a mirror reflection would go, we take the direction exactly halfway",
            "between the light and the eye. If the surface faces that halfway",
            "direction, you are in the reflection. Raising that to the power of",
            "forty-two makes the falloff sharp, which is what makes it read as",
            "gloss rather than haze.",
            "The rim term brightens edges where the surface curves away from you,",
            "which is what separates the silhouette from the background.",
            "Add those three with the weights shown and you have the colour of one",
            "pixel. No shadows, no bounced light, no ray tracing anywhere in this",
            "film.",
        ),
        steps_light(), 62.0, (-36.0, 26.0, 27.0), "sc_light",
    ),
    Chapter(
        "blend", "00", "Glass, and why order comes back",
        "Transparency is the one place where drawing order matters again.",
        (
            "The depth test let us ignore drawing order. Transparency takes that",
            "back, because a see-through surface has to be mixed with whatever is",
            "behind it, which means whatever is behind it has to be there already.",
            "So the renderer works in two passes. Everything solid first, with the",
            "depth test doing its job. Then everything transparent, with depth",
            "writing switched off, so that a panel drawn early does not stop the",
            "panels behind it from being drawn at all.",
            "The mixing itself is one line: the new colour times its opacity, plus",
            "the old colour times one minus that opacity. Opacity is the fourth",
            "number in every vertex colour, the one we have been carrying since",
            "the buffer chapter without using.",
        ),
        ("out = new x a + old x (1 - a)",
         "opaque pass first, transparent pass second"),
        26.0, (30.0, 24.0, 16.5), "sc_blend",
    ),
    Chapter(
        "frame", "00", "And then it does it again",
        "Everything you have watched happens thirty times a second.",
        (
            "One more thing, and it is the one that makes all the rest matter.",
            "Everything in this film — building the tubes, uploading the numbers,",
            "placing the camera, three matrix multiplications per corner, a divide",
            "per corner, a depth comparison per pixel and a lighting sum per",
            "pixel — happens once for the picture you are looking at. And then",
            "it all happens again for the next one, thirty times a second.",
            "That budget, thirty-three milliseconds, is the reason for nearly",
            "every decision in this film. It is why lighting is dot products",
            "rather than ray tracing. It is why half the triangles are thrown away",
            "before shading. It is why depth is one comparison instead of a sort.",
        ),
        ("30 frames/s = 33.33 ms each",),
        26.0, (90.0, 19.0, 22.0), "sc_frame",
    ),
    _math(
        "m_frame", "The cost of one frame",
        "The whole calculation, counted and divided by the clock.",
        (
            "The budget, in numbers. Thirty-three point three three milliseconds",
            "per frame. Three thousand nine hundred triangles in the frame you are",
            "watching, which works out at about eight microseconds each if they",
            "were done one after another — and they are not, they are done",
            "thousands at a time.",
            "The bottom half is the part people underestimate. A full frame at",
            "this resolution is over two million pixels, and the lighting sum runs",
            "for every one of them that gets covered. Sixty-two million lighting",
            "calculations a second, at worst, for one dome on a dark background.",
            "And one last property worth stating. Every scene in this film is a",
            "pure function of which chapter it is and how far through that chapter",
            "we are. Nothing accumulates, nothing depends on what happened before.",
            "Which is why this same film renders identically on any machine, every",
            "time, and why the numbers you have watched being computed can be",
            "checked by anybody who runs it.",
        ),
        steps_frame(), 58.0, (90.0, 19.0, 26.0), "sc_frame",
    ),
    Chapter(
        "close", "00", "The whole chain, once more",
        "One number in; a lit, shaded, sorted picture out.",
        (
            "That is the entire calculation, from nothing.",
            "Phi placed twelve points. A division put them on a unit sphere.",
            "Halving every edge made thirty more points in the wrong place, and a",
            "second division put them right, which split the edges into two",
            "lengths: zero point five four six and zero point six one eight of the",
            "radius. Half the sphere, counted, is forty panels and sixty-five",
            "struts. One multiplication turned that into a cut list.",
            "Then: each strut became a tube of twenty-eight triangles. Each",
            "triangle got a normal from a cross product. All of it flattened into",
            "one list of numbers. Two angles placed a camera, three matrices moved",
            "the world in front of it, one divide made distance work, one stretch",
            "found the pixel, one comparison decided what hides what, and three",
            "dot products decided how bright it was.",
            "No step in that chain is beyond someone who can use a calculator. The",
            "cleverness is not in any one formula. It is in the fact that they",
            "compose — and that every single number can be checked.",
        ),
        ("phi -> icosahedron -> subdivide -> project -> 2 lengths",
         "mesh -> view -> projection -> divide -> pixel -> light"),
        30.0, (30.0, 28.0, 17.0), "finale",
    ),
)


CHAPTERS: tuple[Chapter, ...] = tuple(
    replace(chapter, number=f"{index + 1:02d}",
            narration=_prose(chapter.narration))
    for index, chapter in enumerate(_AUTHORED)
)


def validate_scratch() -> None:
    """Prove the lesson before a frame of it renders."""
    validate_scratch_facts()

    lesson = SCRATCH_LESSON
    lesson.validate()

    slugs = [chapter.slug for chapter in lesson.chapters]
    assert len(set(slugs)) == len(slugs), "duplicate slug in the lesson"

    for chapter in lesson.chapters:
        assert chapter.narration, chapter.slug
        painted = (chapter.stage in SCENES
                   or chapter.stage in BUILTIN_STAGES)
        assert painted, (chapter.slug, chapter.stage)
        if chapter.overlay == "math":
            # A math screen with nothing to derive is a broken promise.
            assert len(chapter.equations) >= 5, chapter.slug
            assert len(chapter.equations[-1]) >= 30, chapter.slug

    # Every screen the facts module offers is used exactly once, and no
    # chapter shows a derivation that module does not own.
    used = {chapter.equations for chapter in lesson.chapters
            if chapter.overlay == "math"}
    offered = {builder() for _name, builder in ALL_SCREENS}
    assert used == offered, (
        f"{len(offered - used)} unused screens, "
        f"{len(used - offered)} unknown screens")

    # The order the narration promises: shape before mesh, mesh before
    # camera, camera before pixels, light last.
    order = {slug: index for index, slug in enumerate(slugs)}
    assert order["coordinates"] < order["project"] < order["classes"]
    assert order["classes"] < order["scale"] < order["tube"]
    assert order["tube"] < order["buffer"] < order["orbit"]
    assert order["orbit"] < order["view"] < order["frustum"] < order["clip"]
    assert order["clip"] < order["screen"] < order["depth"] < order["light"]
    assert order["light"] < order["frame"] < order["close"]

    # Every painter must actually draw something, and label it, at every
    # phase of its chapter -- including the very first frame, where an
    # empty stage would read as a fault in the film.
    class _App:
        def __init__(self):
            self.world_labels = []

    for stage, painter in SCENES.items():
        for progress in (0.0, 0.25, 0.5, 0.75, 1.0):
            probe = _App()
            opaque, transparent = TriangleBatch(), TriangleBatch()
            painter(probe, opaque, transparent, progress)
            assert opaque.vertices or transparent.vertices, (stage, progress)
            for label in probe.world_labels:
                assert label.text.strip(), (stage, progress)

    # The clip-space picture must really be the divided dome: at least
    # one strut has to land inside the cube, or the chapter is drawing
    # an empty box while the narration describes a dome.
    probe = _App()
    opaque = TriangleBatch()
    scene_sc_clip(probe, opaque, TriangleBatch(), 1.0)
    assert len(opaque.vertices) > 30 * 200, "clip space looks empty"

    # The culling chapter's label has to match the picture: some faces
    # kept, some dropped, and the two adding up.
    probe = _App()
    scene_sc_cull(probe, TriangleBatch(), TriangleBatch(), 1.0)
    text = " ".join(label.text for label in probe.world_labels)
    assert "kept and shaded" in text and "dropped" in text, text


SCRATCH_LESSON = Lesson(
    key="scratch",
    brand="FROM SCRATCH / GEOMETRY TO PIXELS",
    title="From Scratch: Every Calculation Behind a Dome on Screen",
    chapters=CHAPTERS,
    scenes=SCENES,
    selftest=validate_scratch,
    report=scratch_report,
    snapshot_prefix="scratch",
    label_layout="declutter",
)
