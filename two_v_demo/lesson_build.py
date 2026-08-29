"""The 2V dome, built start to finish.

The original fourteen-chapter masterclass explains where a 2V dome's two
strut lengths come from.  This lesson keeps that derivation and then keeps
going: sizing, hub systems, end cuts, bevels, stock, jigs, setting out,
foundations, raising, checking, skinning, openings, and the mistakes that
actually happen.  Thirty chapters, all of them about the same building.

Stages that the original lesson already draws well are reused by name --
the renderer falls back to its own ``scene_*`` methods for any stage this
module does not define.  Every construction number comes from
:mod:`two_v_demo.build_geometry`.
"""

from __future__ import annotations

import math
from dataclasses import replace

import numpy as np

from .build_geometry import (
    build_report,
    dihedral_classes,
    dome_rings,
    error_budget,
    hub_types,
    stock_plan,
    strut_details,
    validate_build_geometry,
)
from .geometry import (
    PHI,
    DomeMeasurements,
    build_demo_geometry,
    fit_measurements,
    normalize,
    validate_geometry,
)
from .hubless_geometry import hubless_report, validate_hubless
from .lesson_build_extra import (
    EXTRA_CHAPTERS,
    EXTRA_SCENES,
    extra_equations,
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


GEOMETRY = build_demo_geometry()
FIT = fit_measurements(72.0, 63.5)
RADIUS_IN = FIT.best_fit_radius
DEDUCTION_IN = 0.75
STOCK_SHORT_IN = 96.0
STOCK_LONG_IN = 192.0
MEASUREMENTS = DomeMeasurements(RADIUS_IN, DEDUCTION_IN)

DOME_SCALE = 5.0
RING_COLORS = (CYAN, AMBER, GREEN, PURPLE, RED)


def _rgb(colour) -> tuple[int, int, int]:
    return (int(colour[0] * 255), int(colour[1] * 255), int(colour[2] * 255))


def _inches(value: float) -> str:
    feet, rest = divmod(value, 12.0)
    return f"{value:.2f} in ({int(feet)} ft {rest:.1f} in)"


# ----------------------------------------------------------------------
# Shared drawing
# ----------------------------------------------------------------------

def dome_frame(
    app,
    opaque: TriangleBatch,
    *,
    scale: float = DOME_SCALE,
    offset: np.ndarray | None = None,
    radius: float = 0.06,
    reveal: float = 1.0,
    edges=None,
    colours=None,
    nodes: bool = True,
) -> None:
    offset = np.zeros(3) if offset is None else offset
    edge_list = list(GEOMETRY.hemisphere_edges if edges is None else edges)
    app.add_edges(opaque, GEOMETRY.vertices, edge_list, scale, offset, WHITE,
                  radius, colours if colours is not None else app.dome_class_colors(),
                  reveal)
    if nodes:
        shown = int(math.ceil(len(edge_list) * clamp(reveal)))
        corners = sorted({index for edge in edge_list[:shown] for index in edge})
        app.add_nodes(opaque, GEOMETRY.vertices, scale, offset,
                      (0.80, 0.88, 0.94, 1.0), 0.10, corners)


def dome_skin(
    app,
    transparent: TriangleBatch,
    *,
    scale: float = DOME_SCALE,
    offset: np.ndarray | None = None,
    alpha: float = 0.13,
    reveal: float = 1.0,
    faces=None,
) -> None:
    offset = np.zeros(3) if offset is None else offset
    chosen = GEOMETRY.hemisphere_faces if faces is None else np.asarray(faces)
    app.add_face_shell(transparent, GEOMETRY.vertices, chosen, scale, offset,
                       (0.10, 0.42, 0.58, alpha), reveal)


def ring_of_hub() -> dict[int, int]:
    lookup: dict[int, int] = {}
    for ring in dome_rings():
        for hub in ring.hubs:
            lookup[hub] = ring.index
    return lookup


def person(opaque: TriangleBatch, base: np.ndarray, height: float, colour) -> None:
    """A six-foot figure, drawn to scale, so the dome has a size."""
    opaque.cylinder(base, base + np.array([0.0, 0.0, height * 0.55]),
                    height * 0.075, colour, 8)
    opaque.sphere(base + np.array([0.0, 0.0, height * 0.62]),
                  height * 0.085, colour, 5, 10)
    for side in (-1.0, 1.0):
        opaque.cylinder(base + np.array([side * height * 0.04, 0.0, 0.0]),
                        base + np.array([side * height * 0.055, 0.0, height * 0.30]),
                        height * 0.035, colour, 6)


def bar_row(app, opaque, entries, origin, spacing, height_scale) -> None:
    for index, (label, value, colour) in enumerate(entries):
        height = max(0.08, value * height_scale)
        x = origin[0] - index * spacing
        opaque.box((x, origin[1], origin[2] + height * 0.5),
                   (spacing * 0.45, 0.75, height), colour)
        app.world_labels.append(WorldLabel(
            np.array([x, origin[1], origin[2] + height + 0.5]), label, _rgb(colour)))


# ----------------------------------------------------------------------
# Act one -- what you are building
# ----------------------------------------------------------------------

def scene_build_finished(app, opaque, transparent, p: float) -> None:
    scale = DOME_SCALE
    dome_skin(app, transparent, alpha=0.15)
    dome_frame(app, opaque, reveal=smoothstep(p * 1.4))
    # One radius of the model is one radius of the building.
    person_height = 72.0 / RADIUS_IN * scale
    person(opaque, np.array([scale * 0.62, -scale * 0.55, 0.0]),
           person_height, GREEN)
    app.world_labels.extend([
        WorldLabel(np.array([0.0, 0.0, scale * 1.16]),
                   f"{_inches(MEASUREMENTS.diameter)} ACROSS", (61, 211, 255)),
        WorldLabel(np.array([scale * 0.62, -scale * 0.55, person_height * 0.95]),
                   "6 ft", (111, 235, 155)),
        WorldLabel(np.array([0.0, 0.0, -0.85]),
                   f"{MEASUREMENTS.floor_area / 144.0:.0f} sq ft floor   "
                   f"{MEASUREMENTS.enclosed_volume / 1728.0:.0f} cu ft inside",
                   (169, 188, 203)),
    ])


def scene_build_vocab(app, opaque, transparent, p: float) -> None:
    """Name every part once, on the real thing, before using the words."""
    scale = DOME_SCALE
    dome_frame(app, opaque, radius=0.05, nodes=True)
    highlight = smoothstep(min(1.0, p * 1.3))
    long_edge = next(edge for edge in GEOMETRY.hemisphere_edges
                     if app.edge_class[edge] == "LONG")
    short_edge = next(edge for edge in GEOMETRY.hemisphere_edges
                      if app.edge_class[edge] == "SHORT")
    for edge, label, colour in ((long_edge, "STRUT (LONG)", AMBER),
                                (short_edge, "STRUT (SHORT)", CYAN)):
        a, b = (GEOMETRY.vertices[index] * scale for index in edge)
        opaque.cylinder(a, b, 0.13, colour, 12)
        app.world_labels.append(WorldLabel((a + b) * 0.5, label, _rgb(colour)))
    hub = int(long_edge[0])
    point = GEOMETRY.vertices[hub] * scale
    opaque.sphere(point, 0.22 * highlight + 0.1, GREEN, 6, 10)
    app.world_labels.append(WorldLabel(point + np.array([0.0, 0.0, 0.75]),
                                       "HUB", (111, 235, 155)))
    face = GEOMETRY.hemisphere_faces[0]
    app.add_face_shell(transparent, GEOMETRY.vertices,
                       np.asarray([face]), scale, np.zeros(3),
                       (0.66, 0.48, 1.00, 0.34))
    centre = GEOMETRY.vertices[list(face)].mean(axis=0) * scale
    app.world_labels.append(WorldLabel(centre, "PANEL", (168, 122, 255)))


def scene_build_rings(app, opaque, transparent, p: float) -> None:
    """Colour the dome by the course it is raised in."""
    scale = DOME_SCALE
    lookup = ring_of_hub()
    colours = {}
    for edge in GEOMETRY.hemisphere_edges:
        top = max(edge, key=lambda index: GEOMETRY.vertices[index][2])
        colours[edge] = RING_COLORS[lookup.get(top, 0) % len(RING_COLORS)]
    dome_frame(app, opaque, colours=colours, radius=0.062,
               reveal=smoothstep(p * 1.35))
    for ring in dome_rings():
        colour = RING_COLORS[ring.index % len(RING_COLORS)]
        height = ring.height_factor * scale
        radius = max(0.18, ring.radius_factor * scale)
        for step in range(48):
            angle_a = math.tau * step / 48
            angle_b = math.tau * (step + 1) / 48
            a = np.array([radius * math.cos(angle_a), radius * math.sin(angle_a), height])
            b = np.array([radius * math.cos(angle_b), radius * math.sin(angle_b), height])
            opaque.cylinder(a, b, 0.022, (colour[0], colour[1], colour[2], 0.8), 5)
        # Fan the captions round the dome so they do not stack on screen.
        bearing = math.radians(196.0 + ring.index * 26.0)
        anchor = np.array([
            (radius + 1.9) * math.cos(bearing),
            (radius + 1.9) * math.sin(bearing),
            height,
        ])
        app.world_labels.append(WorldLabel(
            anchor,
            f"{ring.name.upper()}\n{ring.hub_count} hubs\n"
            f"height {ring.height(RADIUS_IN):.1f} in\n"
            f"across {ring.diameter(RADIUS_IN):.1f} in",
            _rgb(colour),
        ))


def scene_build_size(app, opaque, transparent, p: float) -> None:
    """What a radius buys: floor, headroom, volume, and skin to pay for."""
    reveal = smoothstep(min(1.0, p * 1.4))
    radii = (72.0, 96.0, RADIUS_IN, 144.0)
    for index, radius in enumerate(radii):
        if reveal < (index + 0.1) / len(radii):
            continue
        measure = DomeMeasurements(radius, DEDUCTION_IN)
        x = 3.6 - index * 4.6
        height = radius / 144.0 * 4.6
        opaque.box((x, 0.0, height * 0.5), (2.1, 2.1, height),
                   RING_COLORS[index % len(RING_COLORS)])
        app.world_labels.append(WorldLabel(
            np.array([x, 0.0, height + 0.85]),
            f"R {radius:.0f} in\n{measure.floor_area / 144.0:.0f} sq ft\n"
            f"{measure.enclosed_volume / 1728.0:.0f} cu ft\n"
            f"skin {measure.spherical_skin_area / 144.0:.0f} sq ft",
            _rgb(RING_COLORS[index % len(RING_COLORS)]),
        ))
    app.world_labels.append(WorldLabel(
        np.array([-2.9, 0.0, 6.4]),
        "FLOOR GROWS WITH R SQUARED. VOLUME WITH R CUBED.", (111, 235, 155),
    ))


# ----------------------------------------------------------------------
# Act two -- the shop
# ----------------------------------------------------------------------

def scene_build_deduction(app, opaque, transparent, p: float) -> None:
    """Hub centre to hub centre is not the length you cut."""
    explode = ease_in_out(clamp((p - 0.15) / 0.7))
    left = np.array([-3.6, 0.0, 2.9])
    right = np.array([3.6, 0.0, 2.9])
    hub_radius = 0.62
    opaque.sphere(left, hub_radius, MUTED, 6, 12)
    opaque.sphere(right, hub_radius, MUTED, 6, 12)
    gap = hub_radius * (0.35 + 0.65 * explode)
    start = left + np.array([gap, 0.0, 0.0])
    end = right - np.array([gap, 0.0, 0.0])
    opaque.cylinder(start, end, 0.20, CYAN, 12)
    app.add_dimension(opaque, left + np.array([0.0, 0.0, 1.7]),
                      right + np.array([0.0, 0.0, 1.7]), AMBER,
                      f"CENTRE TO CENTRE  {strut_details()[1].centre_length(RADIUS_IN):.3f} in")
    app.add_dimension(opaque, start + np.array([0.0, 0.0, -1.5]),
                      end + np.array([0.0, 0.0, -1.5]), CYAN,
                      f"CUT LENGTH  "
                      f"{strut_details()[1].cut_length(RADIUS_IN, DEDUCTION_IN):.3f} in")
    app.world_labels.append(WorldLabel(
        np.array([0.0, 0.0, 5.6]),
        f"DEDUCTION {DEDUCTION_IN:.3f} in IS BOTH ENDS TOGETHER\n"
        f"MEASURE IT ON A JOINT YOU HAVE ACTUALLY BUILT", (255, 87, 94),
    ))


def scene_build_endcut(app, opaque, transparent, p: float) -> None:
    """The end-cut angle, drawn as the angle between a chord and its tangent."""
    detail = strut_details()[1]
    theta = math.radians(detail.central_angle_deg)
    centre = np.array([0.0, 0.0, 2.5])
    radius = 2.9
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
                   f"central angle\n{detail.central_angle_deg:.4f} deg",
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


def scene_build_bevel(app, opaque, transparent, p: float) -> None:
    """Two panels folding along a strut, and the bevel that lets them meet."""
    folds = dihedral_classes()
    open_angle = ease_in_out(clamp((p - 0.12) / 0.72))
    for index, item in enumerate(folds):
        base = np.array([3.2 - index * 6.4, 0.0, 2.4])
        half = math.radians(180.0 - item.dihedral_deg) * 0.5 * open_angle
        spine_a = base + np.array([0.0, -2.3, 0.0])
        spine_b = base + np.array([0.0, 2.3, 0.0])
        colour = CYAN if item.strut_class == "SHORT" else AMBER
        opaque.cylinder(spine_a, spine_b, 0.10, colour, 10)
        for side in (-1.0, 1.0):
            direction = np.array([side * math.cos(half), 0.0, -math.sin(half)])
            far_a = spine_a + direction * 2.6
            far_b = spine_b + direction * 2.6
            normal = normalize(np.cross(spine_b - spine_a, direction))
            transparent.triangle(spine_a, spine_b, far_b,
                                 (colour[0], colour[1], colour[2], 0.20), normal)
            transparent.triangle(spine_a, far_b, far_a,
                                 (colour[0], colour[1], colour[2], 0.20), normal)
            opaque.cylinder(far_a, far_b, 0.05, colour, 8)
            opaque.cylinder(spine_a, far_a, 0.05, colour, 8)
            opaque.cylinder(spine_b, far_b, 0.05, colour, 8)
        app.world_labels.append(WorldLabel(
            base + np.array([0.0, 0.0, 1.7]),
            f"ALONG {item.strut_class}  x{item.count}\n"
            f"fold {item.dihedral_deg:.3f} deg\n"
            f"bevel each edge {item.bevel_deg:.3f} deg",
            _rgb(colour),
        ))
    app.world_labels.append(WorldLabel(
        np.array([0.0, 0.0, 6.0]),
        "TWO FOLD ANGLES IN THE WHOLE DOME", (111, 235, 155),
    ))


def scene_build_hubs(app, opaque, transparent, p: float) -> None:
    """Every hub type, marked on the dome it belongs to."""
    scale = DOME_SCALE
    dome_frame(app, opaque, radius=0.045, nodes=False,
               colours={edge: (0.36, 0.47, 0.57, 1.0)
                        for edge in GEOMETRY.hemisphere_edges})
    lookup = ring_of_hub()
    reveal = smoothstep(min(1.0, p * 1.4))
    by_ring: dict[str, tuple] = {}
    for hub in hub_types():
        by_ring[hub.ring_name] = hub
    for index, hub_index in enumerate(sorted(lookup)):
        if index / max(1, len(lookup)) > reveal:
            continue
        ring_index = lookup[hub_index]
        colour = RING_COLORS[ring_index % len(RING_COLORS)]
        opaque.sphere(GEOMETRY.vertices[hub_index] * scale, 0.20, colour, 5, 10)
    for order, hub in enumerate(hub_types()):
        colour = RING_COLORS[
            next(ring.index for ring in dome_rings() if ring.name == hub.ring_name)
            % len(RING_COLORS)
        ]
        app.world_labels.append(WorldLabel(
            np.array([-7.4, 0.0, 6.2 - order * 1.05]),
            f"{hub.name}  x{hub.count}  {hub.strut_count} struts  "
            f"{hub.class_summary}",
            _rgb(colour),
        ))


def scene_build_hubkit(app, opaque, transparent, p: float) -> None:
    """Three ways to make the joint, and what each one costs you."""
    reveal = smoothstep(min(1.0, p * 1.4))
    systems = (
        ("STEEL STAR PLATE", CYAN, "one plate per hub type\nbolts through flattened ends"),
        ("TIMBER, BEVELLED", AMBER, "no connector at all\nevery cut is compound"),
        ("PIPE AND HUB BALL", GREEN, "one ball, many angles\nlongest deduction"),
    )
    for index, (label, colour, note) in enumerate(systems):
        if reveal < (index + 0.1) / len(systems):
            continue
        centre = np.array([4.4 - index * 4.6, 0.0, 3.0])
        if index == 0:
            opaque.box((centre[0], centre[1], centre[2]), (1.5, 1.5, 0.16), colour)
        elif index == 1:
            opaque.box((centre[0], centre[1], centre[2]), (0.9, 0.9, 0.9), colour)
        else:
            opaque.sphere(centre, 0.62, colour, 6, 12)
        for arm in range(5):
            angle = math.tau * arm / 5
            direction = np.array([math.cos(angle) * 0.86, math.sin(angle) * 0.86, 0.5])
            opaque.cylinder(centre + direction * 0.55, centre + direction * 2.3,
                            0.10, MUTED, 8)
        app.world_labels.append(WorldLabel(
            centre + np.array([0.0, 0.0, -1.5]), f"{label}\n{note}", _rgb(colour)))
    app.world_labels.append(WorldLabel(
        np.array([-0.2, 0.0, 6.2]),
        "THE HUB SYSTEM SETS THE DEDUCTION. PICK IT FIRST.", (111, 235, 155),
    ))


def scene_build_stock(app, opaque, transparent, p: float) -> None:
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
            f"{stock:.0f} in stock, {run.strut_class}\n"
            f"{run.per_stick} per stick x {run.sticks} sticks\n"
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


def scene_build_jig(app, opaque, transparent, p: float) -> None:
    """A stop block, a master gauge, and a label on every piece."""
    bench = np.array([0.0, 0.0, 1.5])
    opaque.box((bench[0], bench[1], bench[2]), (11.0, 2.6, 0.35),
               (0.13, 0.19, 0.25, 1.0))
    fence_y = bench[1] + 1.0
    opaque.box((bench[0], fence_y, bench[2] + 0.55), (11.0, 0.30, 0.75), MUTED)
    piece_length = 6.4
    stop_x = -piece_length * 0.5
    opaque.box((stop_x - 0.25, fence_y - 0.6, bench[2] + 0.7),
               (0.45, 1.5, 1.05), RED)
    slide = ease_in_out(clamp((p - 0.12) / 0.7))
    opaque.box((stop_x + piece_length * 0.5, fence_y - 0.85,
                bench[2] + 0.45), (piece_length, 0.85, 0.42), CYAN)
    saw_x = stop_x + piece_length
    opaque.box((saw_x, fence_y - 0.85, bench[2] + 1.4 - slide * 0.85),
               (0.10, 1.6, 1.6), (0.72, 0.78, 0.84, 1.0))
    detail = strut_details()[0]
    app.world_labels.extend([
        WorldLabel(np.array([stop_x - 0.25, fence_y - 0.6, bench[2] + 1.9]),
                   "STOP BLOCK", (255, 87, 94)),
        WorldLabel(np.array([stop_x + piece_length * 0.5, fence_y - 0.85,
                             bench[2] + 1.25]),
                   f"{detail.name}  {detail.cut_length(RADIUS_IN, DEDUCTION_IN):.3f} in",
                   (61, 211, 255)),
        WorldLabel(np.array([saw_x, fence_y - 0.85, bench[2] + 3.3]),
                   "CUT EVERY PIECE OF ONE CLASS BEFORE MOVING THE STOP",
                   (111, 235, 155)),
        WorldLabel(np.array([0.0, bench[1] - 2.6, bench[2] + 0.2]),
                   "LABEL EACH PIECE AT THE SAW, NOT AT THE SCAFFOLD",
                   (169, 188, 203)),
    ])


# ----------------------------------------------------------------------
# Act three -- the site
# ----------------------------------------------------------------------

def scene_build_layout(app, opaque, transparent, p: float) -> None:
    """Setting out the base decagon, and the diagonal that proves it."""
    ring = dome_rings()[0]
    scale = DOME_SCALE
    reveal = smoothstep(min(1.0, p * 1.4))
    hubs = sorted(ring.hubs, key=lambda index: math.atan2(
        float(GEOMETRY.vertices[index][1]), float(GEOMETRY.vertices[index][0])))
    points = [GEOMETRY.vertices[index] * scale for index in hubs]
    shown = int(math.ceil(len(points) * reveal))
    for index in range(shown):
        a = points[index]
        b = points[(index + 1) % len(points)]
        opaque.cylinder(a, b, 0.085, AMBER, 9)
        opaque.cylinder(a, a + np.array([0.0, 0.0, 0.9]), 0.05, GREEN, 6)
        opaque.sphere(a + np.array([0.0, 0.0, 0.9]), 0.11, GREEN, 5, 9)
    if reveal > 0.85:
        for offset in (0, 1, 2):
            a = points[offset]
            b = points[(offset + 5) % len(points)]
            opaque.cylinder(a, b, 0.035, CYAN, 6)
        diagonal = float(np.linalg.norm(points[0] - points[5])) / scale * RADIUS_IN
        app.world_labels.append(WorldLabel(
            np.zeros(3), f"EVERY DIAGONAL {diagonal:.2f} in", (61, 211, 255)))
    side = ring.diameter(RADIUS_IN) * math.sin(math.pi / ring.hub_count)
    app.world_labels.extend([
        WorldLabel(np.array([0.0, 0.0, 4.4]),
                   f"{ring.hub_count}-SIDED BASE, SIDE {side:.3f} in",
                   (255, 177, 62)),
        WorldLabel(np.array([0.0, 0.0, -1.1]),
                   "SET OUT FROM THE CENTRE, NOT PEG TO PEG", (169, 188, 203)),
    ])


def scene_build_foundation(app, opaque, transparent, p: float) -> None:
    """Three ways to meet the ground, drawn at the same base ring."""
    reveal = smoothstep(min(1.0, p * 1.4))
    options = (
        ("PIER PER HUB", CYAN, "cheapest, needs a level survey"),
        ("RING BEAM", AMBER, "spreads load, easy to level"),
        ("SLAB", GREEN, "floor and foundation together"),
    )
    for index, (label, colour, note) in enumerate(options):
        if reveal < (index + 0.1) / len(options):
            continue
        x = 4.6 - index * 4.8
        if index == 0:
            for arm in range(5):
                angle = math.tau * arm / 5
                opaque.box((x + math.cos(angle) * 1.5, math.sin(angle) * 1.5, 0.55),
                           (0.55, 0.55, 1.1), colour)
        elif index == 1:
            for step in range(28):
                angle_a = math.tau * step / 28
                angle_b = math.tau * (step + 1) / 28
                a = np.array([x + 1.7 * math.cos(angle_a), 1.7 * math.sin(angle_a), 0.45])
                b = np.array([x + 1.7 * math.cos(angle_b), 1.7 * math.sin(angle_b), 0.45])
                opaque.cylinder(a, b, 0.24, colour, 7)
        else:
            opaque.cylinder(np.array([x, 0.0, 0.10]), np.array([x, 0.0, 0.48]),
                            1.95, colour, 30)
        app.world_labels.append(WorldLabel(
            np.array([x, 0.0, 2.1]), f"{label}\n{note}", _rgb(colour)))
    app.world_labels.append(WorldLabel(
        np.array([-0.1, 0.0, 5.4]),
        "WHATEVER YOU CHOOSE, IT HAS TO BE LEVEL TO A FEW MILLIMETRES",
        (111, 235, 155),
    ))


def scene_build_riser(app, opaque, transparent, p: float) -> None:
    """A riser wall: the cheapest headroom a dome will ever give you."""
    scale = DOME_SCALE
    rise = ease_in_out(clamp((p - 0.12) / 0.72)) * 2.2
    offset = np.array([0.0, 0.0, rise])
    dome_skin(app, transparent, offset=offset, alpha=0.13)
    dome_frame(app, opaque, offset=offset, radius=0.055)
    ring = dome_rings()[0]
    radius = ring.radius_factor * scale
    for step in range(40):
        angle_a = math.tau * step / 40
        angle_b = math.tau * (step + 1) / 40
        for level in (0.0, rise):
            a = np.array([radius * math.cos(angle_a), radius * math.sin(angle_a), level])
            b = np.array([radius * math.cos(angle_b), radius * math.sin(angle_b), level])
            opaque.cylinder(a, b, 0.05, AMBER, 6)
    for step in range(20):
        angle = math.tau * step / 20
        a = np.array([radius * math.cos(angle), radius * math.sin(angle), 0.0])
        opaque.cylinder(a, a + np.array([0.0, 0.0, rise]), 0.05, AMBER, 6)
    real_rise = rise / scale * RADIUS_IN
    app.world_labels.extend([
        WorldLabel(np.array([radius + 1.4, 0.0, rise * 0.5]),
                   f"RISER {real_rise:.1f} in", (255, 177, 62)),
        WorldLabel(np.array([0.0, 0.0, scale + rise + 1.0]),
                   f"USABLE HEIGHT AT THE WALL GOES UP BY THE WHOLE RISER",
                   (111, 235, 155)),
    ])


def scene_build_subassembly(app, opaque, transparent, p: float) -> None:
    """The two triangle families, built flat on the ground first."""
    reveal = smoothstep(min(1.0, p * 1.4))
    for index, triangle in enumerate(GEOMETRY.triangle_classes):
        if reveal < (index + 0.1) / len(GEOMETRY.triangle_classes):
            continue
        sides = [
            (name, next(item.factor for item in GEOMETRY.edge_classes
                        if item.name == name))
            for name in triangle.side_names
        ]
        scale = 7.6
        a = np.array([0.0, 0.0, 0.0])
        b = a + np.array([sides[0][1] * scale, 0.0, 0.0])
        # Place the third corner by intersecting the other two side lengths.
        length_a, length_b, length_c = (item[1] * scale for item in sides)
        x = (length_a**2 + length_c**2 - length_b**2) / (2.0 * length_a)
        y = math.sqrt(max(0.0, length_c**2 - x**2))
        c = a + np.array([x, 0.0, y])
        centre = (a + b + c) / 3.0
        base = np.array([3.4 - index * 7.4, 0.0, 1.4]) - centre
        points = [a + base, b + base, c + base]
        colour_of = {"SHORT": CYAN, "LONG": AMBER}
        for position in range(3):
            name = triangle.side_names[position]
            opaque.cylinder(points[position], points[(position + 1) % 3],
                            0.10, colour_of[name], 10)
        transparent.triangle(points[0], points[1], points[2],
                             (0.30, 0.55, 0.75, 0.16), np.array([0.0, -1.0, 0.0]))
        app.world_labels.append(WorldLabel(
            sum(points) / 3.0,
            f"{triangle.name}\nx{triangle.hemisphere_count} in the dome\n"
            f"corners {triangle.angles_deg[0]:.2f} / "
            f"{triangle.angles_deg[1]:.2f} / {triangle.angles_deg[2]:.2f} deg",
            (169, 188, 203),
        ))
    app.world_labels.append(WorldLabel(
        np.array([-0.2, 0.0, 5.6]),
        "BUILD BOTH FAMILIES FLAT, ON A JIG, BEFORE ANYTHING GOES UP",
        (111, 235, 155),
    ))


def scene_build_raise(app, opaque, transparent, p: float) -> None:
    """Raise it ring by ring, with the current course called out."""
    scale = DOME_SCALE
    reveal = smoothstep(p)
    lookup = ring_of_hub()
    records = sorted(
        GEOMETRY.hemisphere_edges,
        key=lambda edge: float(np.mean(GEOMETRY.vertices[list(edge), 2])),
    )
    count = int(math.ceil(len(records) * reveal))
    for edge in records[:count]:
        top = max(edge, key=lambda index: GEOMETRY.vertices[index][2])
        colour = RING_COLORS[lookup.get(top, 0) % len(RING_COLORS)]
        a, b = (GEOMETRY.vertices[index] * scale for index in edge)
        opaque.cylinder(a, b, 0.075, colour, 9)
    built = sorted({index for edge in records[:count] for index in edge})
    app.add_nodes(opaque, GEOMETRY.vertices, scale, np.zeros(3), WHITE, 0.10, built)
    faces = sorted(
        GEOMETRY.hemisphere_faces,
        key=lambda face: float(np.mean(GEOMETRY.vertices[face, 2])),
    )
    filled = max(0, int(len(faces) * (reveal - 0.16) / 0.84))
    if filled:
        dome_skin(app, transparent, faces=np.asarray(faces[:filled]), alpha=0.15)
    current = 0
    for ring in dome_rings():
        if any(lookup.get(max(edge, key=lambda i: GEOMETRY.vertices[i][2])) == ring.index
               for edge in records[max(0, count - 4):count]):
            current = ring.index
    app.world_labels.append(WorldLabel(
        np.array([0.0, 0.0, scale * 1.18]),
        f"{count:02d} / {len(records)} STRUTS   NOW ON THE "
        f"{dome_rings()[current].name.upper()}",
        _rgb(RING_COLORS[current % len(RING_COLORS)]),
    ))


def scene_build_apex(app, opaque, transparent, p: float) -> None:
    """Closing the crown, which is where all the error turns up."""
    scale = DOME_SCALE
    apex = int(np.argmax(GEOMETRY.vertices[:, 2]))
    without = [edge for edge in GEOMETRY.hemisphere_edges if apex not in edge]
    dome_skin(app, transparent, alpha=0.09)
    dome_frame(app, opaque, edges=without, radius=0.05)
    drop = (1.0 - ease_in_out(clamp((p - 0.15) / 0.7))) * 3.2
    tip = GEOMETRY.vertices[apex] * scale + np.array([0.0, 0.0, drop])
    for edge in GEOMETRY.hemisphere_edges:
        if apex not in edge:
            continue
        other = edge[0] if edge[1] == apex else edge[1]
        opaque.cylinder(GEOMETRY.vertices[other] * scale, tip, 0.10, GREEN, 10)
    opaque.sphere(tip, 0.20, GREEN, 6, 10)
    hub = next(item for item in hub_types() if item.ring_name == "apex")
    app.world_labels.extend([
        WorldLabel(tip + np.array([0.0, 0.0, 0.8]),
                   f"APEX HUB: {hub.strut_count} x SHORT", (111, 235, 155)),
        WorldLabel(np.array([0.0, 0.0, -1.0]),
                   "IF THE CROWN WILL NOT CLOSE, THE ERROR IS IN THE RING BELOW",
                   (255, 87, 94)),
    ])


# ----------------------------------------------------------------------
# Act four -- checking, skinning, and what goes wrong
# ----------------------------------------------------------------------

def scene_build_error(app, opaque, transparent, p: float) -> None:
    """One eighth of an inch per strut, multiplied by the golden ratio."""
    budget = error_budget(0.125)
    scale = DOME_SCALE
    ring = dome_rings()[0]
    radius = ring.radius_factor * scale
    grow = ease_in_out(clamp((p - 0.12) / 0.72))
    # Two decagons: the drawing, and the one the errors actually built.
    for label, factor, colour, thickness in (
        ("AS DRAWN", 1.0, CYAN, 0.06),
        ("AS BUILT", 1.0 + grow * 0.16, RED, 0.06),
    ):
        for step in range(ring.hub_count):
            angle_a = math.tau * step / ring.hub_count
            angle_b = math.tau * (step + 1) / ring.hub_count
            a = np.array([radius * factor * math.cos(angle_a),
                          radius * factor * math.sin(angle_a), 0.35])
            b = np.array([radius * factor * math.cos(angle_b),
                          radius * factor * math.sin(angle_b), 0.35])
            opaque.cylinder(a, b, thickness, colour, 8)
        app.world_labels.append(WorldLabel(
            np.array([0.0, -radius * factor - 0.9, 0.35]), label, _rgb(colour)))
    bar_row(app, opaque, (
        (f"strut error\n{budget.strut_error:.4f} in", budget.strut_error, CYAN),
        (f"radius error\n{budget.radius_error:.4f} in", budget.radius_error, AMBER),
        (f"diameter error\n{budget.diameter_error:.4f} in", budget.diameter_error, RED),
    ), np.array([-3.0, 4.6, 0.35]), 2.6, 7.0)
    app.world_labels.append(WorldLabel(
        np.array([0.0, 0.0, 5.4]),
        f"A {ring.hub_count}-SIDED RING AMPLIFIES BY "
        f"{budget.amplification:.6f} -- WHICH IS PHI", (111, 235, 155),
    ))


def scene_build_check(app, opaque, transparent, p: float) -> None:
    """The measurement loop: length, triangle, ring, radius, height."""
    scale = DOME_SCALE
    dome_frame(app, opaque, radius=0.045,
               colours={edge: (0.36, 0.47, 0.57, 1.0)
                        for edge in GEOMETRY.hemisphere_edges})
    stage = int(clamp(p * 1.02) * 5)
    checks = (
        ("1  MEMBER", "gauge, not tape"),
        ("2  TRIANGLE", "all three corners"),
        ("3  RING", "diameter three ways"),
        ("4  RADIUS", "centre to every hub"),
        ("5  HEIGHT", "apex above base plane"),
    )
    if stage == 0:
        edge = next(edge for edge in GEOMETRY.hemisphere_edges
                    if app.edge_class[edge] == "LONG")
        a, b = (GEOMETRY.vertices[index] * scale for index in edge)
        opaque.cylinder(a, b, 0.14, GREEN, 12)
    elif stage == 1:
        face = GEOMETRY.hemisphere_faces[6]
        points = [GEOMETRY.vertices[int(index)] * scale for index in face]
        for position in range(3):
            opaque.cylinder(points[position], points[(position + 1) % 3],
                            0.11, GREEN, 10)
    elif stage == 2:
        ring = dome_rings()[0]
        hubs = sorted(ring.hubs, key=lambda index: math.atan2(
            float(GEOMETRY.vertices[index][1]), float(GEOMETRY.vertices[index][0])))
        for offset in (0, 1, 2):
            a = GEOMETRY.vertices[hubs[offset]] * scale
            b = GEOMETRY.vertices[hubs[(offset + 5) % len(hubs)]] * scale
            opaque.cylinder(a, b, 0.045, GREEN, 6)
    elif stage == 3:
        for index in sorted(ring_of_hub()):
            opaque.cylinder(np.zeros(3), GEOMETRY.vertices[index] * scale,
                            0.022, GREEN, 5)
    else:
        app.add_dimension(opaque, np.array([0.0, 0.9, 0.0]),
                          np.array([0.0, 0.9, scale]), GREEN,
                          f"HEIGHT = R = {RADIUS_IN:.2f} in")
    label, note = checks[min(stage, 4)]
    app.world_labels.append(WorldLabel(
        np.array([0.0, 0.0, scale * 1.2]), f"{label}\n{note}", (111, 235, 155)))


def scene_build_skin(app, opaque, transparent, p: float) -> None:
    """Skin it from the rim upward so every lap sheds downhill."""
    scale = DOME_SCALE
    dome_frame(app, opaque, radius=0.045)
    faces = sorted(
        GEOMETRY.hemisphere_faces,
        key=lambda face: float(np.mean(GEOMETRY.vertices[face, 2])),
    )
    laid = int(math.ceil(len(faces) * smoothstep(p)))
    for face in faces[:laid]:
        corners = [GEOMETRY.vertices[int(index)] for index in face]
        outward = normalize(sum(corners))
        points = [corner * scale + outward * 0.09 for corner in corners]
        transparent.triangle(points[0], points[1], points[2],
                             (0.32, 0.91, 0.58, 0.30), outward)
    app.world_labels.extend([
        WorldLabel(np.array([0.0, 0.0, scale * 1.2]),
                   f"{laid:02d} / {len(faces)} PANELS, RIM UPWARD",
                   (111, 235, 155)),
        WorldLabel(np.array([0.0, 0.0, -1.0]),
                   "EVERY LAP OVER THE ONE BELOW IT", (169, 188, 203)),
    ])


def scene_build_openings(app, opaque, transparent, p: float) -> None:
    """A door in the base ring and a skylight near the crown."""
    scale = DOME_SCALE
    swing = ease_in_out(clamp((p - 0.18) / 0.66))
    ring = dome_rings()[0]
    hubs = sorted(ring.hubs, key=lambda index: math.atan2(
        float(GEOMETRY.vertices[index][1]), float(GEOMETRY.vertices[index][0])))
    door_faces = [
        index for index, face in enumerate(GEOMETRY.hemisphere_faces)
        if sum(1 for corner in face if int(corner) in hubs[:2]) >= 2
    ]
    apex = int(np.argmax(GEOMETRY.vertices[:, 2]))
    crown_faces = [
        index for index, face in enumerate(GEOMETRY.hemisphere_faces)
        if apex in [int(corner) for corner in face]
    ][:1]
    removed = set(door_faces) | set(crown_faces)
    keep = np.asarray([
        face for index, face in enumerate(GEOMETRY.hemisphere_faces)
        if index not in removed
    ])
    dome_skin(app, transparent, faces=keep, alpha=0.14)
    dome_frame(app, opaque, radius=0.052)
    for index in removed:
        face = GEOMETRY.hemisphere_faces[index]
        corners = [GEOMETRY.vertices[int(value)] for value in face]
        outward = normalize(sum(corners))
        points = [corner * scale + outward * (0.12 + swing * 1.5) for corner in corners]
        transparent.triangle(points[0], points[1], points[2],
                             (1.00, 0.67, 0.20, 0.34), outward)
        for position in range(3):
            opaque.cylinder(points[position], points[(position + 1) % 3],
                            0.05, AMBER, 8)
    app.world_labels.extend([
        WorldLabel(np.array([0.0, 0.0, scale * 1.2]),
                   "OPENINGS TAKE WHOLE PANELS", (255, 177, 62)),
        WorldLabel(np.array([0.0, 0.0, -1.05]),
                   "CUT A STRUT AND YOU HAVE TO REPLACE ITS LOAD PATH",
                   (255, 87, 94)),
    ])


def scene_build_failures(app, opaque, transparent, p: float) -> None:
    """The four mistakes that actually stop domes going up."""
    entries = (
        ("DEDUCTION GUESSED", "every strut wrong, equally", RED),
        ("BASE NOT LEVEL", "error walks around the ring", AMBER),
        ("BUILT UP ONE SIDE", "a ring is not stable until it closes", PURPLE),
        ("PARTS UNLABELLED", "8 in apart, and they look alike", CYAN),
    )
    reveal = smoothstep(min(1.0, p * 1.3))
    for index, (title, note, colour) in enumerate(entries):
        if reveal < (index + 0.1) / len(entries):
            continue
        x = 5.6 - index * 5.1
        opaque.box((x, 0.0, 1.75), (2.9, 0.35, 2.3),
                   (colour[0], colour[1], colour[2], 1.0))
        # A red cross in front of each board, not buried inside it.
        for first, second in (((-1.15, 0.75), (1.15, 2.75)),
                              ((-1.15, 2.75), (1.15, 0.75))):
            opaque.cylinder(np.array([x + first[0], 0.45, first[1]]),
                            np.array([x + second[0], 0.45, second[1]]),
                            0.10, RED, 8)
        app.world_labels.append(WorldLabel(
            np.array([x, 0.0, 3.7]), title + chr(10) + note, _rgb(colour)))
    app.world_labels.append(WorldLabel(
        np.array([-2.0, 0.0, 6.3]),
        "NONE OF THESE ARE GEOMETRY PROBLEMS", (111, 235, 155),
    ))


def scene_build_recap(app, opaque, transparent, p: float) -> None:
    scale = DOME_SCALE
    if p < 0.22:
        local = p / 0.22
        app.add_latitude_sphere(transparent, scale, np.zeros(3), False, 0.05)
        app.add_edges(opaque, GEOMETRY.ico_vertices, GEOMETRY.ico_edges,
                      scale, np.zeros(3), PURPLE, 0.08, None, smoothstep(local))
    elif p < 0.46:
        local = (p - 0.22) / 0.24
        moving = GEOMETRY.flat_midpoints.copy()
        amount = ease_in_out(local)
        moving[12:] = moving[12:] * (1 - amount) + GEOMETRY.vertices[12:] * amount
        app.add_latitude_sphere(transparent, scale, np.zeros(3), False, 0.05)
        app.add_edges(opaque, moving, GEOMETRY.edges, scale, np.zeros(3),
                      WHITE, 0.05, app.dome_class_colors(), smoothstep(local * 1.4))
    elif p < 0.72:
        local = (p - 0.46) / 0.26
        dome_frame(app, opaque, reveal=smoothstep(local))
        dome_skin(app, transparent, reveal=smoothstep(local), alpha=0.12)
    else:
        local = (p - 0.72) / 0.28
        dome_skin(app, transparent, alpha=0.16, reveal=smoothstep(local))
        dome_frame(app, opaque)
        person(opaque, np.array([scale * 0.62, -scale * 0.55, 0.0]),
               72.0 / RADIUS_IN * scale, GREEN)
    app.world_labels.append(WorldLabel(
        np.array([0.0, 0.0, scale * 1.24]),
        "PHI -> ICOSAHEDRON -> 2V -> TWO LENGTHS -> A BUILDING",
        (111, 235, 155),
    ))


# ----------------------------------------------------------------------
# Live figures
# ----------------------------------------------------------------------

def build_equations(app, stage: str) -> list[str]:
    added = extra_equations(app, stage)
    if added:
        return added
    short, long = strut_details()
    if stage == "build_finished":
        return [
            f"radius     = {RADIUS_IN:.4f} in",
            f"diameter   = {MEASUREMENTS.diameter:.4f} in",
            f"height     = {MEASUREMENTS.height:.4f} in",
            f"floor      = {MEASUREMENTS.floor_area / 144.0:.2f} sq ft",
            f"volume     = {MEASUREMENTS.enclosed_volume / 1728.0:.2f} cu ft",
        ]
    if stage == "build_vocab":
        return [
            f"struts  = {len(GEOMETRY.hemisphere_edges)} in 2 classes",
            f"hubs    = {sum(ring.hub_count for ring in dome_rings())}",
            f"panels  = {len(GEOMETRY.hemisphere_faces)} in 2 families",
        ]
    if stage == "build_rings":
        return [
            f"{ring.name:<12} {ring.hub_count:>2} hubs  h {ring.height(RADIUS_IN):7.2f}"
            f"  d {ring.diameter(RADIUS_IN):8.2f} in"
            for ring in dome_rings()
        ]
    if stage == "build_size":
        return [
            f"R {radius:5.0f} in -> floor "
            f"{DomeMeasurements(radius).floor_area / 144.0:6.1f} sq ft, "
            f"volume {DomeMeasurements(radius).enclosed_volume / 1728.0:7.1f} cu ft"
            for radius in (72.0, 96.0, RADIUS_IN, 144.0)
        ]
    if stage in ("build_deduction", "build_jig"):
        return [
            f"{item.name}: centre {item.centre_length(RADIUS_IN):.4f} in, "
            f"cut {item.cut_length(RADIUS_IN, DEDUCTION_IN):.4f} in"
            for item in strut_details()
        ] + [f"deduction = {DEDUCTION_IN:.4f} in across both ends"]
    if stage == "build_endcut":
        return [
            f"{item.name}: central {item.central_angle_deg:.4f} deg, "
            f"end cut {item.axial_angle_deg:.4f} deg"
            for item in strut_details()
        ] + ["chord = 2 R sin(central / 2)"]
    if stage == "build_bevel":
        return [
            f"along {item.strut_class}: fold {item.dihedral_deg:.4f} deg, "
            f"bevel {item.bevel_deg:.4f} deg  x{item.count}"
            for item in dihedral_classes()
        ]
    if stage in ("build_hubs", "build_hubkit"):
        return [
            f"{hub.name}: x{hub.count}  {hub.strut_count} struts  "
            f"{hub.class_summary}"
            for hub in hub_types()
        ]
    if stage == "build_stock":
        rows = []
        for stock in (STOCK_SHORT_IN, STOCK_LONG_IN):
            runs = stock_plan(RADIUS_IN, stock, DEDUCTION_IN)
            rows.append(
                f"{stock:.0f} in stock: "
                + ", ".join(
                    f"{run.strut_class} {run.per_stick}/stick x{run.sticks}"
                    for run in runs
                )
            )
        return rows
    if stage == "build_layout":
        ring = dome_rings()[0]
        side = ring.diameter(RADIUS_IN) * math.sin(math.pi / ring.hub_count)
        return [
            f"base hubs   = {ring.hub_count}",
            f"base side   = {side:.4f} in",
            f"base circle = {ring.diameter(RADIUS_IN):.4f} in across",
            f"side x phi  = {side * PHI:.4f} in = the radius of the ring",
        ]
    if stage == "build_subassembly":
        return [
            f"{item.name}: x{item.hemisphere_count}  corners "
            f"{item.angles_deg[0]:.3f} / {item.angles_deg[1]:.3f} / "
            f"{item.angles_deg[2]:.3f} deg"
            for item in GEOMETRY.triangle_classes
        ]
    if stage == "build_error":
        budget = error_budget(0.125)
        return [
            f"strut error    = {budget.strut_error:.4f} in each",
            f"radius error   = {budget.radius_error:.4f} in",
            f"diameter error = {budget.diameter_error:.4f} in",
            f"amplification  = {budget.amplification:.6f}",
            f"phi            = {PHI:.6f}",
        ]
    if stage in ("build_check", "build_apex"):
        return [
            f"expected height = R = {RADIUS_IN:.4f} in",
            f"base diagonal   = {2.0 * dome_rings()[0].radius_factor * RADIUS_IN:.4f} in",
            "check length -> triangle -> ring -> radius -> height",
        ]
    if stage in ("build_skin", "build_openings"):
        return [
            f"panels     = {len(GEOMETRY.hemisphere_faces)}",
            f"skin area  = {MEASUREMENTS.spherical_skin_area / 144.0:.2f} sq ft",
            f"flat panel = {MEASUREMENTS.planar_panel_area / 144.0:.2f} sq ft",
        ]
    if stage == "build_riser":
        return [
            f"dome height    = {MEASUREMENTS.height:.3f} in",
            "riser adds its own height at every point of the wall",
            f"floor area is unchanged at {MEASUREMENTS.floor_area / 144.0:.1f} sq ft",
        ]
    return []


SCENES = {
    "build_finished": scene_build_finished,
    "build_vocab": scene_build_vocab,
    "build_rings": scene_build_rings,
    "build_size": scene_build_size,
    "build_deduction": scene_build_deduction,
    "build_endcut": scene_build_endcut,
    "build_bevel": scene_build_bevel,
    "build_hubs": scene_build_hubs,
    "build_hubkit": scene_build_hubkit,
    "build_stock": scene_build_stock,
    "build_jig": scene_build_jig,
    "build_layout": scene_build_layout,
    "build_foundation": scene_build_foundation,
    "build_riser": scene_build_riser,
    "build_subassembly": scene_build_subassembly,
    "build_raise": scene_build_raise,
    "build_apex": scene_build_apex,
    "build_error": scene_build_error,
    "build_check": scene_build_check,
    "build_skin": scene_build_skin,
    "build_openings": scene_build_openings,
    "build_failures": scene_build_failures,
    "build_recap": scene_build_recap,
}
SCENES.update(EXTRA_SCENES)


CHAPTERS: tuple[Chapter, ...] = (
    Chapter(
        "brief", "01", "What we are actually building",
        "One dome, twenty feet across, from two boards you already own.",
        (
            "Before any mathematics, here is the finished thing, drawn to scale with a",
            "six foot person beside it. Twenty feet across, ten feet to the crown, about",
            "three hundred square feet of floor. Everything in the next half hour is in",
            "service of that object: where its two strut lengths come from, how to cut",
            "them, how to join them, how to stand them up, and how to know you got it",
            "right.",
        ),
        ("one radius scales the whole building", "height = radius"),
        17.0, (32.0, 22.0, 15.0), "build_finished",
    ),
    Chapter(
        "vocab", "02", "The five words we will keep using",
        "Hub, strut, panel, chord factor, frequency. Learn them on the real thing.",
        (
            "A hub is a joint. A strut is a straight member between two hubs. A panel is",
            "the triangle they enclose. A chord factor is a strut's length divided by the",
            "radius, which is what lets one drawing serve every size of dome. And",
            "frequency is how many times each edge of the parent shape was divided:",
            "two, in this case, which is where two V comes from.",
        ),
        ("chord factor = strut length / radius",
         "frequency = divisions per parent edge"),
        17.0, (36.0, 24.0, 13.5), "build_vocab",
    ),
    Chapter(
        "why_triangle", "03", "Why the whole thing is triangles",
        "A triangle cannot change shape without changing a side length.",
        (
            "Push the top corner of a square frame and it folds over into a diamond; no",
            "side got longer, the shape just moved. Do the same to a triangle and nothing",
            "happens, because moving any corner would have to stretch a side. That is the",
            "entire structural argument for a geodesic dome, and it is why the frame",
            "carries load along its members rather than bending them.",
        ),
        ("F = F_compression + F_tension",
         "geometry explains the form; an engineer sizes the members"),
        16.0, (35.0, 30.0, 15.0), "rigidity",
    ),
    Chapter(
        "parent", "04", "Where the shape starts: the icosahedron",
        "Twenty equal triangles are the closest a regular solid gets to a sphere.",
        (
            "Of the five regular solids, the icosahedron has the most faces and the most",
            "evenly spread corners, so it needs the least correction when you push it out",
            "to a sphere. That is the only reason it is chosen. It gives twenty",
            "equilateral launch pads and twelve corners, and every geodesic dome in",
            "common use starts here.",
        ),
        ("faces: 4, 6, 8, 12, 20", "2V means: halve every parent edge"),
        16.0, (32.0, 27.0, 18.0), "platonic",
    ),
    Chapter(
        "phi", "05", "Phi builds the twelve corners",
        "The golden ratio places the parent vertices. It is not the strut ratio.",
        (
            "The twelve corners of an icosahedron are three golden rectangles standing",
            "at right angles to each other. That is where the golden ratio genuinely",
            "lives in this shape. It is worth being precise about, because the ratio of",
            "the two finished strut lengths is not phi, and expecting it to be has sent",
            "a lot of people down the wrong path.",
        ),
        ("phi = (1 + sqrt 5) / 2", "corners: (0, +-1, +-phi) and its rotations"),
        17.0, (30.0, 22.0, 16.0), "coordinates",
    ),
    Chapter(
        "unit", "06", "Put it on a sphere of radius one",
        "One division turns coordinates into numbers you can scale to any size.",
        (
            "Divide every corner by its distance from the centre and the solid now sits",
            "on a sphere of radius exactly one. From here on, every length we measure is",
            "a multiple of the radius, so the same drawing serves a garden dome and a",
            "hangar. This is the single most useful move in the whole derivation.",
        ),
        ("v_hat = v / ||v||", "parent edge = 1.051462 R"),
        15.0, (27.0, 25.0, 14.0), "icosahedron",
    ),
    Chapter(
        "halve", "07", "Halve every edge",
        "Thirty parent edges give thirty midpoints, and they are all too close in.",
        (
            "Take the midpoint of every one of the thirty edges. That is just the average",
            "of the two ends, and it is easy. But those midpoints sit inside the sphere,",
            "not on it, because a straight line between two points on a curved surface",
            "always cuts the corner. Leave them there and you have a faceted lump, not a",
            "dome.",
        ),
        ("m = (a + b) / 2", "||m|| = 0.850651, short of 1"),
        16.0, (30.0, 24.0, 14.0), "midpoints",
    ),
    Chapter(
        "project", "08", "Push the midpoints out to the sphere",
        "This one move is what creates the second strut length.",
        (
            "Slide each midpoint straight out from the centre until it reaches the",
            "sphere. Nothing else changes. But by moving those thirty points outward,",
            "every triangle around them changes shape, and the edges that used to be",
            "equal split into two different lengths. That is the whole origin of the two",
            "cut lengths in your shopping list.",
        ),
        ("p = m / ||m||", "the move outward = 0.149349 R"),
        17.0, (29.0, 22.0, 14.0), "projection",
    ),
    Chapter(
        "classes", "09", "Two lengths, and nothing else",
        "One hundred and twenty edges collapse into exactly two numbers.",
        (
            "Measure every edge on the finished sphere and they fall into two groups and",
            "only two. The shorter one runs from an original corner to a projected",
            "midpoint. The longer one runs between two projected midpoints, and it comes",
            "out to exactly one over phi, which is the one place the golden ratio does",
            "show up in the answer.",
        ),
        ("SHORT = 0.546533 R", "LONG = 0.618034 R = 1 / phi",
         "ratio = 1.130826, not phi"),
        18.0, (31.0, 25.0, 14.0), "classes",
    ),
    Chapter(
        "sizing", "10", "Choosing your radius",
        "Floor grows with the square of the radius. Volume grows with the cube.",
        (
            "Now pick a size, and pick it for a reason. Doubling the radius gives four",
            "times the floor, eight times the volume, and four times the skin you have to",
            "buy and waterproof. Headroom at the wall is the thing people underestimate:",
            "at the very edge of a hemisphere there is none at all, which is what the",
            "riser wall later in this lesson is for.",
        ),
        ("floor = pi R^2", "skin = 2 pi R^2", "volume = 2/3 pi R^3"),
        18.0, (90.0, 20.0, 19.0), "build_size",
    ),
    Chapter(
        "rings", "11", "The dome is four rings and a crown",
        "Twenty-six hubs, in courses, at heights you can measure before you build.",
        (
            "Cut the sphere in half and the hubs sort themselves into level courses: ten",
            "on the ground, then two rings of five, then five more, then the single hub at",
            "the top. Twenty-six joints in total. Those ring heights and diameters are",
            "your check numbers during the raise, so write them on the drawing before you",
            "start.",
        ),
        ("26 hubs: 10 + 5 + 5 + 5 + 1",
         "every ring is a level circle you can measure"),
        19.0, (38.0, 22.0, 16.0), "build_rings",
    ),
    Chapter(
        "audit", "12", "Auditing the boards you already have",
        "Two measured members imply two radii. Fit them, do not average them.",
        (
            "You measured seventy-two inches and sixty-three and a half. Each of those",
            "implies a radius on its own, and they disagree slightly, because real",
            "members contain cutting and measuring error. The right move is a least",
            "squares fit that weights both, not picking whichever one you trust more.",
            "That fit is the radius the rest of this lesson uses.",
        ),
        ("R from LONG = 72 / 0.618034", "R from SHORT = 63.5 / 0.546533",
         "best fit minimises both residuals"),
        19.0, (28.0, 25.0, 16.0), "audit",
    ),
    Chapter(
        "hubkit", "13", "Choose the hub system before anything else",
        "The connector decides the deduction, and the deduction decides every cut.",
        (
            "A steel star plate, a bevelled timber joint, and a drilled hub ball all",
            "build the same geometry but they eat different amounts of strut. Choose the",
            "system now, build one joint for real, and measure how much shorter the",
            "members have to be. Everything downstream depends on that one measurement,",
            "and no catalogue number is a substitute for it.",
        ),
        ("hub system -> connector deduction -> every cut length",
         "build one real joint and measure it"),
        19.0, (90.0, 18.0, 17.5), "build_hubkit",
    ),
    Chapter(
        "deduction", "14", "Centre length is not cut length",
        "The geometry gives hub centres. The saw needs something shorter.",
        (
            "Every number in the derivation is hub centre to hub centre, because that is",
            "what the sphere is made of. The stick you cut has to be shorter by whatever",
            "the two connectors occupy. Note that the deduction is the total across both",
            "ends, not per end; halving it by mistake is one of the most common ways a",
            "dome ends up refusing to close.",
        ),
        ("cut length = centre length - deduction",
         "deduction is both ends together"),
        19.0, (-90.0, 16.0, 14.0), "build_deduction",
    ),
    Chapter(
        "endcut", "15", "The end-cut angle is half the central angle",
        "One line of arithmetic gives you the angle the strut leaves the surface at.",
        (
            "A strut is a chord across the sphere, so it dips below the surface between",
            "its ends. The angle it makes with the surface at each end is exactly half",
            "the central angle that chord subtends, and the central angle comes straight",
            "out of the chord factor. That is the angle to tip a hub plate to, or to cut",
            "a timber end back to, and there is one value per strut class.",
        ),
        ("chord = 2 R sin(theta / 2)", "end cut = theta / 2"),
        20.0, (-90.0, 14.0, 13.5), "build_endcut",
    ),
    Chapter(
        "bevel", "16", "The panel bevels",
        "Two panels fold along every interior strut, and there are only two fold angles.",
        (
            "Where two panels meet along a strut they are not in the same plane; they",
            "fold. If you are skinning with rigid sheets, the edge of each panel wants to",
            "be planed to half that fold so the two faces meet cleanly. There are exactly",
            "two fold angles in the whole dome, one along each strut class, which means",
            "two saw settings and no thinking at the bench.",
        ),
        ("bevel = (180 - fold) / 2", "two fold angles in the entire dome"),
        20.0, (90.0, 18.0, 16.5), "build_bevel",
    ),
    Chapter(
        "hubs", "17", "How many kinds of joint",
        "Five hub types, and they are not interchangeable.",
        (
            "Grouping the hubs by how many struts arrive and at what angles gives a small",
            "number of distinct types. Make a set for each type, keep them in separate",
            "labelled boxes, and check one against a drawing before you make the rest.",
            "The base hubs are the ones to make first, because they also have to take the",
            "anchor bolts.",
        ),
        ("hub type = strut count + splay angles",
         "make one, check it, then make the batch"),
        19.0, (40.0, 24.0, 15.5), "build_hubs",
    ),
    Chapter(
        "stock", "18", "Buying the stock",
        "Choose the stock length before the radius and the offcut nearly vanishes.",
        (
            "Here is a real cost that geometry lessons never mention. At this radius, a",
            "standard eight foot stick yields exactly one strut and throws the rest away.",
            "A sixteen foot stick yields several. The right time to notice that is while",
            "the radius is still adjustable, because a small change in radius can move",
            "you from one piece per stick to two.",
        ),
        ("pieces per stick = floor((stock + kerf) / (cut + kerf))",
         "kerf counts; include it"),
        20.0, (90.0, 14.0, 19.0), "build_stock",
    ),
    Chapter(
        "cutting", "19", "Cutting: a stop block and a master",
        "Cut every piece of one class before you move anything.",
        (
            "Set a stop block for the first class and cut all of them without touching",
            "the setting. Keep the very first good piece as a master gauge and compare",
            "the rest to it rather than re-measuring with a tape, because a tape",
            "introduces a new error every time you use it. Label each piece as it comes",
            "off the saw. Then, and only then, move the stop.",
        ),
        ("one setting per class", "compare to a master, not to a tape",
         "label at the saw"),
        19.0, (66.0, 20.0, 15.5), "build_jig",
    ),
    Chapter(
        "cutlist", "20", "The finished cut list",
        "Sixty-five members, two lengths, and a count you can hand to a shop.",
        (
            "This is the whole order: thirty of the shorter class and thirty-five of the",
            "longer, at the cut lengths we derived, plus the hub schedule. Add spares.",
            "Two or three of each class costs very little and saves an entire afternoon",
            "the first time a piece splits or a cut goes wrong.",
        ),
        ("30 SHORT + 35 LONG = 65 members", "add spares of both classes"),
        17.0, (31.0, 25.0, 15.0), "cutlist",
    ),
    Chapter(
        "subassembly", "21", "Build the triangles flat, first",
        "Two triangle families repeat all forty times. Jig them on the ground.",
        (
            "The dome contains only two kinds of triangle: thirty with two short sides",
            "and one long, and ten with three long sides. Lay one of each out on a flat",
            "floor, screw down blocks to make a jig, and assemble the rest inside the",
            "jig. Every panel then comes out identical, and the raise turns into",
            "bolting known-good pieces together rather than fitting each one.",
        ),
        ("30 x SHORT-SHORT-LONG", "10 x LONG-LONG-LONG",
         "jig them flat before anything goes up"),
        20.0, (90.0, 18.0, 17.0), "build_subassembly",
    ),
    Chapter(
        "layout", "22", "Setting out the base",
        "A ten-sided ring, set out from the centre, checked on the diagonals.",
        (
            "Drive a pin at the centre and swing the base radius to mark all ten hub",
            "positions. Do not step around the ring measuring side to side, because every",
            "small error then adds to the next one. When the ten are pegged, measure the",
            "long diagonals: on a regular ten-sided ring they are all identical, so any",
            "difference is telling you exactly where the setting out drifted.",
        ),
        ("set out from the centre, every time",
         "all five long diagonals are equal on a true ring"),
        20.0, (32.0, 52.0, 17.5), "build_layout",
    ),
    Chapter(
        "foundation", "23", "Meeting the ground",
        "Piers, a ring beam, or a slab. Whichever you choose has to be level.",
        (
            "A dome puts a concentrated outward-and-down load at each base hub, so the",
            "foundation either has to catch each one individually with a pier, or tie",
            "them all together with a ring beam or slab that resists the spread. The",
            "structural choice is yours and your engineer's. The one non-negotiable is",
            "that the ten bearing points end up on one level plane.",
        ),
        ("base hubs push down and outward",
         "pier, ring beam, or slab -- but level"),
        20.0, (90.0, 22.0, 17.0), "build_foundation",
    ),
    Chapter(
        "riser", "24", "The riser wall",
        "The cheapest usable space a dome will ever sell you.",
        (
            "A hemisphere has no headroom at its edge, which makes the outer ring of",
            "floor nearly useless. Stand the whole dome on a short vertical wall and every",
            "point of the shell rises by that amount, so the perimeter becomes furniture",
            "height or door height. It costs one ring of studs and it changes the plan",
            "completely. Decide on it before you set out, because it changes the",
            "foundation.",
        ),
        ("riser adds its height everywhere",
         "the floor area does not change; the usable area does"),
        20.0, (34.0, 20.0, 16.5), "build_riser",
    ),
    Chapter(
        "raise", "25", "Raising it, one complete ring at a time",
        "Never build up one side. The shell is not stable until a ring closes.",
        (
            "Bolt the base hubs down, then work upward in complete courses. A half-built",
            "ring is a row of unstable triangles and it will lean; a closed ring is a",
            "rigid hoop that holds its own shape. Prop each course until the one above it",
            "closes. Measure the diameter across each finished ring in three directions",
            "before you begin the next, and correct there rather than higher up.",
        ),
        ("complete rings, never one column",
         "prop until the ring above closes",
         "measure each ring three ways"),
        21.0, (40.0, 24.0, 15.0), "build_raise",
    ),
    Chapter(
        "apex", "26", "Closing the crown",
        "If the last hub will not fit, the error is in the ring below it.",
        (
            "The top hub is where every accumulated millimetre finally arrives, so it is",
            "the honest test of everything below. If the five struts will not reach it",
            "cleanly, resist the urge to force them. Go back down and measure the ring",
            "beneath: nearly always it is slightly out of round or slightly out of level,",
            "and correcting it there is far quicker than fighting the crown.",
        ),
        ("the crown reports the error, it does not cause it",
         "5 SHORT struts meet at the apex"),
        19.0, (36.0, 30.0, 14.5), "build_apex",
    ),
    Chapter(
        "error", "27", "What an eighth of an inch actually does",
        "A ten-sided ring amplifies a strut error by exactly the golden ratio.",
        (
            "Here is a number worth carrying around. If every base strut is one eighth of",
            "an inch long, the base radius is out by phi times that, and the diameter by",
            "twice again. The same golden ratio that placed the parent corners now",
            "governs how your mistakes grow. It is not a large factor, but it is a",
            "multiplier, and it explains why domes drift bigger rather than smaller.",
        ),
        ("regular n-gon: radius = side / (2 sin(pi/n))",
         "for n = 10 that divisor is 0.618034",
         "so radius error = phi x strut error"),
        21.0, (44.0, 32.0, 15.5), "build_error",
    ),
    Chapter(
        "check", "28", "The measurement loop",
        "Member, triangle, ring, radius, height. In that order, every time.",
        (
            "Check a member against the master gauge. Check a triangle on all three",
            "corners. Check a ring on its diameter, three ways. Check the radius from the",
            "centre pin to each hub. Check the apex height against the radius, because on",
            "a true hemisphere they are the same number. Each check catches what the",
            "previous one could hide, and doing them in order is what stops a small",
            "error becoming a structural one.",
        ),
        ("length -> triangle -> ring -> radius -> height",
         "expected dome height = R exactly"),
        21.0, (30.0, 24.0, 15.5), "build_check",
    ),
    Chapter(
        "skin", "29", "Skinning it, rim upward",
        "Forty panels, laid so every lap sheds downhill, sealed at every hub.",
        (
            "Start at the base and work up so each panel laps over the one below it,",
            "exactly like roof shingles. Every hub is a junction of several panel corners",
            "and those are the leak points, so flash or tape each one before the next",
            "course covers it. Give the base a real drip edge that throws water clear of",
            "the wall. A dome almost never fails structurally; it fails at its seams.",
        ),
        ("40 panels in the dome half", "lap upward, seal every hub",
         "a drip edge at the base is not optional"),
        20.0, (34.0, 24.0, 15.0), "build_skin",
    ),
    Chapter(
        "openings", "30", "Doors, windows, and what not to cut",
        "Take whole panels. Cutting a strut means replacing a load path.",
        (
            "The clean way to make an opening is to leave a panel out and frame the",
            "triangle. The frame is untouched and the shell keeps working. If you must",
            "make a bigger opening, head it with a member at least as strong as the ones",
            "you removed and get that detail checked, because a dome carries load through",
            "its net and a missing strut is a missing path, not just a missing stick.",
        ),
        ("whole panels are free openings",
         "a cut strut needs its load path replaced"),
        20.0, (48.0, 20.0, 15.0), "build_openings",
    ),
    Chapter(
        "failures", "31", "The four things that actually go wrong",
        "None of them are geometry. All of them are avoidable.",
        (
            "Domes rarely fail because the arithmetic was wrong. They fail because the",
            "connector deduction was guessed instead of measured, because the base was",
            "not level, because someone built up one side instead of in rings, or because",
            "two similar-looking members got mixed up. Each of those is a habit, not a",
            "calculation, and each is cheap to fix before you start and expensive after.",
        ),
        ("deduction guessed", "base not level", "built up one side",
         "parts unlabelled"),
        19.0, (90.0, 16.0, 19.0), "build_failures",
    ),
    Chapter(
        "recap", "32", "The whole thing, once more, quickly",
        "From the golden ratio to a building you can stand inside.",
        (
            "Phi places twelve corners. Normalising puts them on a unit sphere. Halving",
            "every edge and pushing the midpoints out gives two chord factors. One radius",
            "turns those into two cut lengths. A connector deduction turns those into saw",
            "settings. Jigs turn saw settings into identical triangles, rings turn",
            "triangles into a shell, and a skin turns a shell into a room. Every number",
            "came from the geometry, and every one of them can be recomputed instead of",
            "trusted.",
        ),
        ("phi -> icosahedron -> 2V -> SHORT + LONG -> R -> cut list -> building",),
        20.0, (30.0, 28.0, 15.0), "build_recap",
    ),
)

# The four added sections sit between the failure list and the recap, so
# the lesson still ends on the summary. The recap keeps its position and
# takes whatever number it now lands on.
CHAPTERS = (
    CHAPTERS[:-1]
    + EXTRA_CHAPTERS
    + (replace(CHAPTERS[-1], number=f"{len(CHAPTERS) + len(EXTRA_CHAPTERS):02d}"),)
)


def _selftest() -> None:
    validate_geometry()
    validate_build_geometry()
    validate_hubless()


BUILD_LESSON = Lesson(
    key="build",
    brand="2V / DOME CONSTRUCTION, START TO FINISH",
    title="2V Dome Construction Masterclass",
    chapters=CHAPTERS,
    scenes=SCENES,
    equations=build_equations,
    selftest=_selftest,
    report=lambda: build_report(RADIUS_IN, DEDUCTION_IN, STOCK_SHORT_IN)
    + chr(10) * 2 + hubless_report(RADIUS_IN),
    snapshot_prefix="build",
)
