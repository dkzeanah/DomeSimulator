"""Four additions to the construction lesson.

Hubless framing and its compound cuts, the shell used as a filter, the
one-sheet micro shelter, and the mixed-stock franken-dome.  Kept in their
own module so the main construction lesson stays readable; the scenes and
chapters here are merged into it by :mod:`two_v_demo.lesson_build`.

Every figure comes from :mod:`two_v_demo.hubless_geometry`, which measures
all of it off the same 2V hemisphere the rest of the lesson uses.
"""

from __future__ import annotations

import math

import numpy as np

from .figure import POSES, draw_figure, joint_positions, place_figure
from .geometry import build_demo_geometry, normalize
from .hubless_geometry import (
    AIRFLOW_CAVEATS,
    TYPICAL_MITRE_SAW_MAX_DEG,
    airflow_model,
    compound_setups,
    franken_hardware,
    hubless_summary,
    panel_classes,
    sheet_nesting,
)
from .lessons import Chapter
from .render_kit import (
    AMBER,
    CYAN,
    GREEN,
    MUTED,
    PURPLE,
    RED,
    WHITE,
    WorldLabel,
    clamp,
    ease_in_out,
    smoothstep,
)


GEOMETRY = build_demo_geometry()
SUMMARY = hubless_summary()
SETUPS = compound_setups()
FRANKEN = franken_hardware()
SHELTER = sheet_nesting(120.0, 60.0)
AIR = airflow_model(60.0)

DOME_SCALE = 5.0
SHELTER_SHEET = (120.0, 60.0)


def _rgb(colour) -> tuple[int, int, int]:
    return (int(colour[0] * 255), int(colour[1] * 255), int(colour[2] * 255))


def _triangle_struts(
    batch,
    corners: np.ndarray,
    colour,
    radius: float = 0.075,
    inset: float = 0.10,
) -> None:
    """Draw a triangle as three separate struts, not three shared edges.

    The inset is the whole point of the picture: pulling each strut back
    from the corner shows that this triangle owns its own three members
    and shares none of them.
    """
    centre = corners.mean(axis=0)
    for index in range(3):
        a = corners[index]
        b = corners[(index + 1) % 3]
        direction = normalize(b - a)
        start = a + direction * inset * float(np.linalg.norm(b - a))
        end = b - direction * inset * float(np.linalg.norm(b - a))
        batch.cylinder(start, end, radius, colour, 8)


def scene_build_hubless_intro(app, opaque, transparent, p: float) -> None:
    """Forty complete triangles, drifting apart to show they are separate."""
    spread = ease_in_out(clamp((p - 0.10) / 0.75)) * 2.1
    for face in GEOMETRY.hemisphere_faces:
        corners = GEOMETRY.vertices[[int(v) for v in face]] * DOME_SCALE
        centre = corners.mean(axis=0)
        offset = normalize(centre) * spread
        _triangle_struts(opaque, corners + offset, CYAN, 0.062)
    app.world_labels.extend([
        WorldLabel(np.array([0.0, 0.0, 7.4]),
                   f"{SUMMARY.triangles} COMPLETE TRIANGLES", (61, 211, 255)),
        WorldLabel(np.array([0.0, 0.0, 6.5]),
                   f"{SUMMARY.triangles} x 3 = {SUMMARY.struts} STRUTS, "
                   f"NOT {SUMMARY.unique_edges}", (111, 235, 155)),
    ])


def scene_build_hubless_edge(app, opaque, transparent, p: float) -> None:
    """One shared edge carrying two struts, and one rim edge carrying one."""
    fold = ease_in_out(clamp((p - 0.15) / 0.70))
    # Left: a shared edge. Two triangles, each with its own strut, bolted.
    spine_a = np.array([-4.6, -2.6, 2.2])
    spine_b = np.array([-4.6, 2.6, 2.2])
    gap = 0.17
    for side, colour in ((-1.0, CYAN), (1.0, AMBER)):
        offset = np.array([0.0, 0.0, 0.0]) + np.array([side * gap, 0.0, 0.0])
        opaque.cylinder(spine_a + offset, spine_b + offset, 0.13, colour, 10)
        half = math.radians(22.0) * fold
        direction = np.array([side * math.cos(half), 0.0, -math.sin(half)])
        far_a = spine_a + offset + direction * 2.8
        far_b = spine_b + offset + direction * 2.8
        opaque.cylinder(spine_a + offset, far_a, 0.075, colour, 8)
        opaque.cylinder(spine_b + offset, far_b, 0.075, colour, 8)
        opaque.cylinder(far_a, far_b, 0.075, colour, 8)
        normal = normalize(np.cross(spine_b - spine_a, direction))
        transparent.triangle(spine_a + offset, spine_b + offset, far_b,
                             (colour[0], colour[1], colour[2], 0.14), normal)
        transparent.triangle(spine_a + offset, far_b, far_a,
                             (colour[0], colour[1], colour[2], 0.14), normal)
    # The bolts through both struts.
    for t in (0.28, 0.72):
        point = spine_a + (spine_b - spine_a) * t
        opaque.cylinder(point + np.array([-0.42, 0.0, 0.0]),
                        point + np.array([0.42, 0.0, 0.0]), 0.045, WHITE, 8)
        for end in (-0.42, 0.42):
            opaque.sphere(point + np.array([end, 0.0, 0.0]), 0.10, MUTED, 4, 8)

    # Right: a rim edge, one strut only.
    rim_a = np.array([4.6, -2.6, 2.2])
    rim_b = np.array([4.6, 2.6, 2.2])
    opaque.cylinder(rim_a, rim_b, 0.13, GREEN, 10)
    direction = np.array([-math.cos(math.radians(22.0) * fold), 0.0,
                          -math.sin(math.radians(22.0) * fold)])
    far_a = rim_a + direction * 2.8
    far_b = rim_b + direction * 2.8
    opaque.cylinder(rim_a, far_a, 0.075, GREEN, 8)
    opaque.cylinder(rim_b, far_b, 0.075, GREEN, 8)
    opaque.cylinder(far_a, far_b, 0.075, GREEN, 8)

    app.world_labels.extend([
        WorldLabel(np.array([-4.6, 0.0, 5.4]),
                   f"SHARED EDGE  x{SUMMARY.doubled_edges}\n"
                   "two struts, bolted face to face", (61, 211, 255)),
        WorldLabel(np.array([4.6, 0.0, 5.4]),
                   f"RIM EDGE  x{SUMMARY.rim_edges}\none strut, cut square",
                   (111, 235, 155)),
        WorldLabel(np.array([0.0, 0.0, 7.0]),
                   f"2 x {SUMMARY.doubled_edges} + {SUMMARY.rim_edges} "
                   f"= {SUMMARY.strut_check}", (255, 177, 62)),
    ])


def scene_build_hubless_cut(app, opaque, transparent, p: float) -> None:
    """One strut end, with the mitre swing and the blade tilt separated."""
    setup = SETUPS[0]
    reveal = ease_in_out(clamp(p * 1.4))
    centre = np.array([0.0, 0.0, 2.6])
    length = 5.4
    axis = np.array([1.0, 0.0, 0.0])
    start = centre - axis * length * 0.5
    end = centre + axis * length * 0.5

    # The blank, then the two angles applied to its end.
    opaque.box(tuple(centre), (length, 0.85, 0.42), (0.31, 0.37, 0.45, 1.0))

    # Mitre: swing in the plane of the triangle, drawn on the flat.
    mitre = math.radians(setup.mitre_deg) * reveal
    tip = end + np.array([0.0, math.tan(mitre) * 0.62, 0.0])
    opaque.cylinder(end + np.array([0.0, -0.62, 0.0]),
                    end + np.array([0.0, 0.62, 0.0]), 0.03, MUTED, 6)
    opaque.cylinder(end + np.array([-0.9, -0.62, 0.0]), tip, 0.05, CYAN, 8)
    # Bevel: tilt out of that plane.
    bevel = math.radians(setup.bevel_deg) * reveal
    opaque.cylinder(end + np.array([0.0, 0.0, -0.55]),
                    end + np.array([0.0, 0.0, 0.55]), 0.03, MUTED, 6)
    opaque.cylinder(end + np.array([-0.9, 0.0, -0.55]),
                    end + np.array([0.0, 0.0, math.tan(bevel) * 0.9 - 0.55]),
                    0.05, AMBER, 8)

    app.world_labels.extend([
        WorldLabel(end + np.array([0.4, 1.5, 0.0]),
                   f"MITRE  {setup.mitre_deg:.3f} deg\nthe saw swings",
                   (61, 211, 255)),
        WorldLabel(end + np.array([0.4, -0.6, 1.5]),
                   f"BEVEL  {setup.bevel_deg:.3f} deg\nthe blade tilts",
                   (255, 177, 62)),
        WorldLabel(start + np.array([-0.6, 0.0, 1.1]),
                   "ONE CUT, BOTH AT ONCE", (111, 235, 155)),
        WorldLabel(np.array([0.0, 0.0, -0.5]),
                   f"{SUMMARY.setups} DISTINCT SETUPS FOR ALL "
                   f"{SUMMARY.struts * 2} ENDS", (169, 188, 203)),
    ])


def scene_build_hubless_saw(app, opaque, transparent, p: float) -> None:
    """A protractor showing the mitres sitting past the saw's own stop."""
    centre = np.array([2.4, 0.0, -0.6])
    radius = 6.0
    reveal = clamp(p * 1.5)

    def point_at(degrees: float, scale: float = 1.0) -> np.ndarray:
        # Negative X so the quadrant opens toward screen right, into the
        # empty half of the frame rather than under the teaching card.
        angle = math.radians(degrees)
        return centre + np.array([
            -radius * scale * math.cos(angle), 0.0, radius * scale * math.sin(angle)
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
        WorldLabel(point_at(78.0, 1.42),
                   "EVERY MITRE THIS DOME NEEDS", (255, 87, 94)),
        WorldLabel(point_at(20.0, 0.88),
                   "CUT THE COMPLEMENT INSTEAD", (61, 211, 255)),
        WorldLabel(centre + np.array([0.0, 0.0, -1.4]),
                   "same joint, reachable setting, part turned a quarter turn",
                   (169, 188, 203)),
    ])


def scene_build_air_origin(app, opaque, transparent, p: float) -> None:
    """Where the idea came from: a welder, a closed shop, and no exit."""
    scale = 3.4
    for edge in GEOMETRY.hemisphere_edges:
        a, b = (GEOMETRY.vertices[i] * scale for i in edge)
        opaque.cylinder(a, b, 0.035, (0.30, 0.36, 0.44, 1.0), 6)
    # The ring main around the base.
    ring_radius = scale * 1.02
    segments = 48
    for index in range(segments):
        angle_a = math.tau * index / segments
        angle_b = math.tau * (index + 1) / segments
        a = np.array([ring_radius * math.cos(angle_a),
                      ring_radius * math.sin(angle_a), 0.16])
        b = np.array([ring_radius * math.cos(angle_b),
                      ring_radius * math.sin(angle_b), 0.16])
        opaque.cylinder(a, b, 0.11, CYAN, 8)
    # The blower on the ring.
    opaque.box((ring_radius + 0.35, 0.0, 0.42), (0.9, 0.75, 0.75), AMBER)

    # A welder at the middle, and what they are breathing.
    # The dome is drawn at 3.4 units for a 60 in radius, so a person is
    # 68.9 in at the same scale. Getting this wrong is the difference
    # between a workshop and a doll's house.
    person = 3.4 * (68.9 / AIR.radius_in)
    joints = place_figure(
        joint_positions(POSES["kneel"], person), (0.0, 0.0, 0.0), 150.0)
    draw_figure(opaque, joints, scale=person / 1.75)
    rise = ease_in_out(clamp(p * 1.2))
    for index in range(34):
        t = (index / 34.0 + rise) % 1.0
        height = 1.6 + t * 2.2
        spread = 0.24 + t * 1.05
        angle = index * 2.399
        point = np.array([spread * math.cos(angle), spread * math.sin(angle), height])
        transparent.sphere(point, 0.26 + t * 0.22,
                           (0.68, 0.72, 0.76, 0.30 * (1.0 - t)), 3, 7)

    app.world_labels.extend([
        WorldLabel(np.array([0.0, 0.0, 4.6]),
                   "FUMES GO UP AND STAY UP", (169, 188, 203)),
        WorldLabel(np.array([ring_radius + 0.35, 0.0, 1.3]),
                   "BLOWER ON A BASE RING MAIN", (255, 177, 62)),
        WorldLabel(np.array([0.0, -ring_radius - 0.6, 0.5]),
                   f"RING MAIN {AIR.base_tube_length_in:.0f} in AROUND",
                   (61, 211, 255)),
    ])


def scene_build_air_direction(app, opaque, transparent, p: float) -> None:
    """The same tube, run both ways: purge outward, or draw inward."""
    swap = 0.5 + 0.5 * math.sin(p * math.tau - math.pi * 0.5)
    outward = swap > 0.5
    scale = 3.1
    for offset, label, blowing in ((-5.0, "PUSH: PURGE", True),
                                   (5.0, "PULL: RECOVER", False)):
        base = np.array([offset, 0.0, 0.0])
        for edge in GEOMETRY.hemisphere_edges:
            a, b = (GEOMETRY.vertices[i] * scale + base for i in edge)
            opaque.cylinder(a, b, 0.032, (0.28, 0.34, 0.42, 1.0), 6)
        phase = ease_in_out(clamp(p * 1.3))
        colour = AMBER if blowing else CYAN
        for index in range(14):
            angle = index * 2.399
            elevation = 0.16 + (index % 5) * 0.19
            direction = np.array([
                math.cos(angle) * math.cos(elevation * math.pi * 0.5),
                math.sin(angle) * math.cos(elevation * math.pi * 0.5),
                math.sin(elevation * math.pi * 0.5),
            ])
            travel = ((index / 14.0) + phase) % 1.0
            near = base + direction * scale * (0.25 + travel * 0.70)
            far = base + direction * scale * (0.42 + travel * 0.78)
            if blowing:
                opaque.arrow(near, far, 0.032, colour)
            else:
                opaque.arrow(far, near, 0.032, colour)
        app.world_labels.append(WorldLabel(
            base + np.array([0.0, 0.0, 4.5]), label, _rgb(colour)))
        app.world_labels.append(WorldLabel(
            base + np.array([0.0, 0.0, -0.7]),
            "fumes out fastest\nmoisture pushed into the shell" if blowing
            else "incoming air warmed by the shell\nheat recovered on the way in",
            (169, 188, 203)))
    app.world_labels.append(WorldLabel(
        np.array([0.0, 0.0, 6.2]),
        "ONE TUBE, ONE SWITCH, TWO COMPLETELY DIFFERENT BUILDINGS",
        (111, 235, 155)))


def scene_build_air_wall(app, opaque, transparent, p: float) -> None:
    """How slowly the air actually crosses the wall."""
    reveal = smoothstep(clamp(p * 1.3))
    cases = AIR.cases
    fastest = max(case.face_velocity_fpm for case in cases)
    width, gap = 1.05, 1.5
    span = (len(cases) - 1) * (width + gap)
    for index, case in enumerate(cases):
        x = -span * 0.5 + index * (width + gap)
        height = 4.2 * (case.face_velocity_fpm / fastest) * reveal
        opaque.box((x, 0.0, height * 0.5 + 0.1), (width, 0.95, max(0.02, height)),
                   CYAN)
        app.world_labels.extend([
            WorldLabel(np.array([x, 0.0, height + 0.75]),
                       f"{case.face_velocity_fpm:.2f} ft/min", (61, 211, 255)),
            WorldLabel(np.array([x, 0.0, -0.6]),
                       f"{case.air_changes_per_hour:.0f} ACH\n{case.cfm:.0f} CFM",
                       (169, 188, 203)),
        ])
    # A draught you could feel, for comparison.
    draught = 4.2 * (40.0 / fastest)
    app.world_labels.append(WorldLabel(
        np.array([0.0, 0.0, 5.8]),
        "A DRAUGHT YOU CAN FEEL STARTS NEAR 40 ft/min", (255, 177, 62)))
    app.world_labels.append(WorldLabel(
        np.array([0.0, 0.0, 5.0]),
        f"{AIR.shell_area_m2:.1f} m2 OF WALL FOR {AIR.volume_m3:.1f} m3 OF AIR",
        (111, 235, 155)))


def scene_build_air_caveats(app, opaque, transparent, p: float) -> None:
    """The five things that decide whether a breathing wall works."""
    reveal = clamp(p * 1.35)
    span = 13.0
    step = span / max(1, len(AIRFLOW_CAVEATS) - 1)
    colours = (CYAN, AMBER, RED, PURPLE, GREEN)
    for index, (title, _) in enumerate(AIRFLOW_CAVEATS):
        if index / len(AIRFLOW_CAVEATS) > reveal:
            continue
        x = -span * 0.5 + index * step
        colour = colours[index % len(colours)]
        opaque.box((x, 0.0, 1.5), (2.05, 0.5, 2.5), colour)
        app.world_labels.append(WorldLabel(
            np.array([x, 0.0, 3.3]), title.upper(), _rgb(colour)))
    app.world_labels.append(WorldLabel(
        np.array([0.0, 0.0, 5.4]),
        "COMPUTED: THE FLOW.  UNTESTED: THE WALL.", (255, 87, 94)))


def scene_build_shelter_nest(app, opaque, transparent, p: float) -> None:
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


def scene_build_shelter_size(app, opaque, transparent, p: float) -> None:
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
    # Negative X puts the figure in the open half of the frame; positive
    # X hides it behind the teaching card at this chapter's camera.
    beside = np.array([-scale * 2.15, 0.0, 0.0])
    joints = place_figure(
        joint_positions(POSES["stand"], stature_units), beside, 250.0)
    draw_figure(opaque, joints, scale=stature_units / 1.75)
    app.world_labels.append(WorldLabel(
        beside + np.array([0.0, 0.0, stature_units + 0.8]),
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
            f"RISER {SHELTER.riser_for(72.0):.0f} in\nbuys standing room",
            (111, 235, 155)))

    app.world_labels.extend([
        WorldLabel(np.array([0.0, 0.0, scale + riser + 1.2]),
                   f"{SHELTER.diameter:.0f} in ACROSS, "
                   f"{SHELTER.headroom:.0f} in TALL", (61, 211, 255)),
        WorldLabel(np.array([0.0, -scale - 1.2, 0.4]),
                   f"{SHELTER.floor_area_sqft:.1f} sq ft", (169, 188, 203)),
    ])


def scene_build_franken_stock(app, opaque, transparent, p: float) -> None:
    """Five different sticks, all doing the same job."""
    reveal = clamp(p * 1.4)
    profiles = (
        ("ROUND", CYAN), ("QUARTER-CUT", AMBER), ("WEDGE", GREEN),
        ("SQUARE", PURPLE), ("RECTANGULAR", RED),
    )
    span = 13.6
    step = span / (len(profiles) - 1)
    for index, (name, colour) in enumerate(profiles):
        if index / len(profiles) > reveal:
            continue
        x = -span * 0.5 + index * step
        base = np.array([x, 0.0, 0.6])
        top = np.array([x, 0.0, 4.6])
        if name == "ROUND":
            opaque.cylinder(base, top, 0.34, colour, 14)
        elif name == "SQUARE":
            opaque.box(tuple((base + top) * 0.5), (0.62, 0.62, 4.0), colour)
        elif name == "RECTANGULAR":
            opaque.box(tuple((base + top) * 0.5), (0.86, 0.42, 4.0), colour)
        elif name == "QUARTER-CUT":
            opaque.cylinder(base, top, 0.34, colour, 6)
        else:
            opaque.cylinder(base, top, 0.36, colour, 3)
        app.world_labels.append(WorldLabel(
            np.array([x, 0.0, 5.3]), name, _rgb(colour)))
    app.world_labels.append(WorldLabel(
        np.array([0.0, 0.0, 6.5]),
        f"{SUMMARY.struts} STRUTS, WHATEVER THEY HAPPEN TO BE",
        (111, 235, 155)))
    app.world_labels.append(WorldLabel(
        np.array([0.0, 0.0, -0.4]),
        "every section has a different centreline, so no joint lands on the sphere",
        (169, 188, 203)))


def scene_build_franken_lumpy(app, opaque, transparent, p: float) -> None:
    """A deliberately imprecise frame, then the skin that forgives it."""
    rng = np.random.default_rng(7)
    jitter = rng.normal(0.0, 1.0, GEOMETRY.vertices.shape) * 0.055
    lumpy = GEOMETRY.vertices + jitter
    skin = ease_in_out(clamp((p - 0.42) / 0.52))
    for edge in GEOMETRY.hemisphere_edges:
        a, b = (lumpy[i] * DOME_SCALE for i in edge)
        opaque.cylinder(a, b, 0.075, AMBER, 8)
    used = sorted({i for edge in GEOMETRY.hemisphere_edges for i in edge})
    for index in used:
        opaque.sphere(lumpy[index] * DOME_SCALE, 0.11, MUTED, 4, 8)
    if skin > 0.01:
        for face in GEOMETRY.hemisphere_faces:
            corners = np.array([
                (lumpy[int(v)] * (1.0 - skin) + GEOMETRY.vertices[int(v)] * skin)
                for v in face
            ]) * (DOME_SCALE * (1.0 + 0.045 * skin))
            normal = normalize(corners.mean(axis=0))
            transparent.triangle(corners[0], corners[1], corners[2],
                                 (0.55, 0.80, 0.88, 0.34 * skin), normal)
    app.world_labels.extend([
        WorldLabel(np.array([0.0, 0.0, 7.2]),
                   "LUMPY FRAME" if skin < 0.4 else "THE SKIN SPANS THE SLACK",
                   (255, 177, 62) if skin < 0.4 else (111, 235, 155)),
        WorldLabel(np.array([0.0, 0.0, -0.8]),
                   "every triangle is still rigid; the error has nowhere to accumulate",
                   (169, 188, 203)),
    ])


def scene_build_franken_ledger(app, opaque, transparent, p: float) -> None:
    """What it cost in hardware, and what it bought in time."""
    reveal = clamp(p * 1.35)
    rows = (
        (f"{FRANKEN.brackets} BRACKETS", FRANKEN.brackets, CYAN),
        (f"{FRANKEN.screws:,} SCREWS", FRANKEN.screws, AMBER),
        (f"{FRANKEN.bolts} BOLTS", FRANKEN.bolts, GREEN),
        (f"{FRANKEN.washers} WASHERS", FRANKEN.washers, PURPLE),
    )
    biggest = max(value for _, value, _ in rows)
    span = 11.4
    step = span / (len(rows) - 1)
    for index, (label, value, colour) in enumerate(rows):
        if index / len(rows) > reveal:
            continue
        x = -span * 0.5 + index * step
        height = 4.0 * (value / biggest)
        opaque.box((x, 0.0, height * 0.5 + 0.15), (1.5, 0.95, max(0.05, height)),
                   colour)
        app.world_labels.append(WorldLabel(
            np.array([x, 0.0, height + 0.8]), label, _rgb(colour)))
    app.world_labels.extend([
        WorldLabel(np.array([0.0, 0.0, 6.0]),
                   f"{FRANKEN.fasteners:,} FASTENERS, "
                   f"{FRANKEN.build_days} DAYS", (111, 235, 155)),
        WorldLabel(np.array([0.0, 0.0, -0.9]),
                   f"stood {FRANKEN.stood_months} months: "
                   f"{FRANKEN.service_ratio:.0f}x its own build time",
                   (169, 188, 203)),
    ])


def scene_build_franken_trees(app, opaque, transparent, p: float) -> None:
    """Four trees, some cable, and a dome borrowing their strength."""
    scale = 3.6
    for edge in GEOMETRY.hemisphere_edges:
        a, b = (GEOMETRY.vertices[i] * scale for i in edge)
        opaque.cylinder(a, b, 0.055, AMBER, 6)
    tension = ease_in_out(clamp((p - 0.20) / 0.62))
    apex = np.array([0.0, 0.0, scale])
    for index in range(4):
        angle = math.tau * index / 4 + math.pi * 0.25
        trunk = np.array([7.4 * math.cos(angle), 7.4 * math.sin(angle), 0.0])
        opaque.cylinder(trunk, trunk + np.array([0.0, 0.0, 8.4]), 0.30,
                        (0.34, 0.27, 0.20, 1.0), 8)
        for level in range(3):
            height = 5.0 + level * 1.3
            transparent.sphere(trunk + np.array([0.0, 0.0, height]),
                               1.5 - level * 0.28, (0.22, 0.45, 0.26, 0.42), 3, 7)
        if tension > 0.02:
            anchor = trunk + np.array([0.0, 0.0, 6.6])
            opaque.cylinder(anchor, apex * tension + anchor * (1.0 - tension),
                            0.028, GREEN, 6)
    if tension > 0.5:
        transparent.sphere(apex, 0.30, (0.32, 0.91, 0.58, 0.55), 4, 9)
    app.world_labels.extend([
        WorldLabel(np.array([0.0, 0.0, scale + 2.4]),
                   "GUYED INTO FOUR TREES", (111, 235, 155)),
        WorldLabel(np.array([0.0, 0.0, -1.0]),
                   "the site carried what the frame did not",
                   (169, 188, 203)),
    ])


EXTRA_SCENES = {
    "build_hubless_intro": scene_build_hubless_intro,
    "build_hubless_edge": scene_build_hubless_edge,
    "build_hubless_cut": scene_build_hubless_cut,
    "build_hubless_saw": scene_build_hubless_saw,
    "build_air_origin": scene_build_air_origin,
    "build_air_direction": scene_build_air_direction,
    "build_air_wall": scene_build_air_wall,
    "build_air_caveats": scene_build_air_caveats,
    "build_shelter_nest": scene_build_shelter_nest,
    "build_shelter_size": scene_build_shelter_size,
    "build_franken_stock": scene_build_franken_stock,
    "build_franken_lumpy": scene_build_franken_lumpy,
    "build_franken_ledger": scene_build_franken_ledger,
    "build_franken_trees": scene_build_franken_trees,
}


def extra_equations(app, stage: str) -> list[str]:
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


EXTRA_CHAPTERS: tuple[Chapter, ...] = (
    Chapter(
        "hubless_intro", "32", "The dome with no hubs in it",
        "Forty complete triangles, and not one connector between them.",
        (
            "Everything so far assumed a hub: a plate or a bracket that several struts",
            "arrive at. There is another way to build the same sphere that has no hubs at",
            "all. You make each of the forty triangles as a finished, closed triangle, and",
            "then you bolt the triangles to each other edge to edge. Nothing meets at a",
            "point any more. Every joint is now a lap between two flat sides.",
        ),
        ("40 triangles x 3 struts = 120", "hubbed: 65 struts + 26 hubs",
         "hubless: 120 struts + 0 hubs"),
        21.0, (34.0, 26.0, 17.5), "build_hubless_intro",
    ),
    Chapter(
        "hubless_edge", "33", "Why it takes 120 struts, not 65",
        "Every shared edge now carries two struts instead of one.",
        (
            "A hubbed dome has sixty-five struts because each edge is one member serving",
            "the panels on both sides of it. A hubless dome gives each triangle its own",
            "three members, so an edge between two triangles ends up with two struts lying",
            "face to face, bolted through. Fifty-five edges are shared like that. Ten more",
            "sit on the rim with nothing on the other side. Two times fifty-five, plus ten,",
            "is one hundred and twenty, and that is the whole frame.",
        ),
        ("55 shared x 2 struts = 110", "10 rim x 1 strut = 10", "total = 120"),
        23.0, (92.0, 15.0, 17.0), "build_hubless_edge",
    ),
    Chapter(
        "hubless_cut", "34", "The compound cut",
        "Two angles at once, on the same pass, on every single end.",
        (
            "Here is the part that stops people. Each strut end needs the saw swung to a",
            "mitre, so the strut meets its neighbour in the plane of its own triangle, and",
            "the blade tilted to a bevel, so the face lies flat against the triangle next",
            "door. Those two settings are not applied one after the other. They happen on",
            "the same cut, which is what compound means, and getting one right while the",
            "other is wrong gives you a part that looks correct and fits nothing.",
        ),
        ("mitre: the saw swings", "bevel: the blade tilts",
         "one pass, both at once"),
        24.0, (66.0, 18.0, 13.0), "build_hubless_cut",
    ),
    Chapter(
        "hubless_saw", "35", "Every angle you need is past the stop",
        "The geometry is easy. The tool is the problem.",
        (
            "Now the sting. The mitres this dome asks for run from about fifty-six degrees",
            "to about sixty-two degrees away from square, and a common mitre saw stops at",
            "fifty. Not one of the settings this dome needs is on the scale. The way",
            "through is that a mitre and its complement are the same cut approached from",
            "the other face: swing the saw to the complement instead, which lands between",
            "twenty-seven and thirty-four degrees, and rotate the workpiece a quarter turn",
            "in a sled. Same joint, reachable setting. Build the sled first, before you cut",
            "anything you care about.",
        ),
        ("needed: 55.6 to 62.2 deg from square", "common saw stops at 50 deg",
         "complement: 27.8 to 34.4 deg, and turn the part"),
        26.0, (90.0, 8.0, 15.0), "build_hubless_saw",
    ),
    Chapter(
        "air_origin", "36", "The tube around the bottom",
        "This one started with a badly ventilated workshop.",
        (
            "A dome has an unhelpful habit: warm air and anything it carries rises to the",
            "apex and stays there. Weld inside one and you are standing in a chimney with",
            "no flue. The fix that came out of that is a tube running right around the",
            "base, with a blower on it, so the whole perimeter becomes one duct instead of",
            "the building having a single extract point somewhere on one wall.",
        ),
        ("ring main = one duct all the way round",
         "no single extract point", "the shape is the ductwork"),
        22.0, (40.0, 22.0, 15.5), "build_air_origin",
    ),
    Chapter(
        "air_direction", "37", "Run it either way",
        "The same tube and the same fan make two different buildings.",
        (
            "Push air in at the ring and it leaves through the shell, carrying fumes out",
            "through the whole surface at once instead of dragging them past your face to",
            "one vent. Reverse it and you draw outside air inward through the shell, which",
            "warms it against the structure on the way in and recovers heat you would",
            "otherwise throw away. That second mode has a real name in building science:",
            "dynamic insulation, or a breathing wall. Same hardware. One switch.",
        ),
        ("push: purge fumes through the whole surface",
         "pull: incoming air warmed by the shell",
         "one tube, one switch"),
        24.0, (88.0, 16.0, 20.0), "build_air_direction",
    ),
    Chapter(
        "air_wall", "38", "The wall as the filter",
        "The shell is so large that the air barely crawls through it.",
        (
            "Here is why the idea is interesting rather than merely odd. A ten foot dome",
            "holds about two hundred and sixty cubic feet of air behind about fifteen",
            "square metres of wall. Even purging hard, at forty air changes an hour, the",
            "air crosses that wall at about one foot per minute. A draught you can feel",
            "starts somewhere near forty. So the entire envelope becomes a filter face and",
            "nobody inside feels a thing, because the flow is spread over the whole",
            "building instead of rushing past one grille.",
        ),
        ("6 ACH -> 26 CFM", "20 ACH -> 87 CFM", "40 ACH -> 175 CFM",
         "through the wall at about 1 ft/min"),
        26.0, (90.0, 14.0, 15.0), "build_air_wall",
    ),
    Chapter(
        "air_caveats", "39", "What would actually decide it",
        "The flow numbers are computed. The wall is not proven.",
        (
            "Being straight about this: the geometry and the airflow above are calculated,",
            "and the idea that a strut lattice makes a good distributed plenum at building",
            "scale is untested. Five things decide it. Direction, because pushing warm wet",
            "air outward through a cold wall condenses it inside that wall and rots the",
            "shell where you cannot see it. A sealed fibreglass skin cannot breathe at all,",
            "so the permeable band has to be designed in rather than hoped for. And a",
            "filter you cannot reach is a filter you will never change.",
        ),
        ("computed: the flow", "untested: the wall",
         "moisture is the failure mode"),
        26.0, (90.0, 15.0, 17.0), "build_air_caveats",
    ),
    Chapter(
        "shelter_nest", "40", "Forty panels from one sheet",
        "The whole shell, nested onto a single ten by five foot sheet.",
        (
            "Different build entirely. Forget struts: cut the forty triangles as solid",
            "panels and join them edge to edge. The question is how big a dome you can get",
            "off one sheet. Congruent triangles pair into parallelograms, and",
            "parallelograms strip-pack with no waste along a row, because the slope of one",
            "is filled by the next. Solving that packing against a ten by five sheet, with",
            "a real kerf and a real edge margin, gives a radius of about thirty-one inches.",
        ),
        ("30 identical + 10 identical panels",
         "paired into parallelograms, strip-packed",
         "one 10 ft x 5 ft sheet"),
        24.0, (90.0, 62.0, 15.0), "build_shelter_nest",
    ),
    Chapter(
        "shelter_size", "41", "The sub-two-thousand-dollar storm shelter",
        "Sixty-two inches across, thirty-one inches tall. It is not cozy.",
        (
            "That sheet buys a shell about five feet across with thirty-one inches of",
            "headroom and twenty-one square feet of floor. You do not stand up in it. You",
            "do not really sit up in it either. I have been inside it, so nobody needs to",
            "tell me it is not cozy. It is a hole you can afford, above ground, that a",
            "laser can cut in an afternoon. And if you want it habitable rather than",
            "survivable, the riser wall from earlier fixes it for almost nothing: five",
            "inches of riser gets you sitting upright, and forty-one inches gets you",
            "standing, without recutting a single panel. If you have seen a shelter cheaper",
            "than this that a person can actually get into, message the channel. I would",
            "genuinely like to study it.",
        ),
        ("62 in across, 31 in headroom, 21 sq ft",
         "5 in riser -> sit upright", "41 in riser -> stand up"),
        30.0, (52.0, 13.0, 22.0), "build_shelter_size",
    ),
    Chapter(
        "franken_stock", "42", "The franken-dome",
        "One hundred and twenty struts, and no two of them alike.",
        (
            "Last one, and it is an experiment rather than a recommendation. I wanted to",
            "know how fast a dome goes up if you stop caring what the struts are. Round",
            "logs, quarter-cut pieces, wedges, square stock, rectangular offcuts, whatever",
            "the chainsaw produced that day. Every section has a different effective",
            "centreline, so not one joint lands where the geometry says it should.",
        ),
        ("120 struts, any section", "no two centrelines alike",
         "nothing lands on the sphere"),
        22.0, (30.0, 20.0, 17.0), "build_franken_stock",
    ),
    Chapter(
        "franken_lumpy", "43", "Why the lumpy one stays up",
        "The errors have nowhere to accumulate, and the skin covers the rest.",
        (
            "It should not work and it does, for two reasons. A closed triangulated shell",
            "is enormously redundant: every triangle is rigid by itself, so an error at one",
            "joint is absorbed by the two hundred around it instead of walking around a",
            "ring the way it does in a precise dome. What you get is a lumpy brain of a",
            "frame that is near the sphere without being on it. Then the sheathing does the",
            "rest. A monolithic skin bonded over the outside spans the slack and gives back",
            "the shell action the sloppiness cost you.",
        ),
        ("every triangle rigid on its own",
         "error absorbed, not accumulated",
         "the skin returns the shell action"),
        26.0, (36.0, 24.0, 17.0), "build_franken_lumpy",
    ),
    Chapter(
        "franken_trees", "44", "Borrowing strength from the site",
        "Four trees did the work the tolerance did not.",
        (
            "It went up between four trees, and that was not an accident. Cable overhead,",
            "tied back into the trunks, meant the frame never had to be self-supporting",
            "while it was going together, and the trees kept taking a share afterwards.",
            "Covered in clear plastic, it stood through half a year of weather with no",
            "complaints before I took it down on purpose. That is eighteen times its own",
            "build time, which is the only durability number I actually have.",
        ),
        ("guyed into four trees", "clear plastic cover",
         "stood 6 months = 18x its build time"),
        24.0, (44.0, 20.0, 20.0), "build_franken_trees",
    ),
    Chapter(
        "franken_ledger", "45", "What it cost, and the crown I award myself",
        "A chainsaw, a tarp, and rather a lot of screws.",
        (
            "The ledger. One hundred and twenty brackets, eight screws in each, which is",
            "nine hundred and sixty screws. Two bolts through every edge, so a hundred and",
            "thirty bolts and two hundred and sixty washers. Ten days, four triangles a",
            "day. The timber was free and the tarp was nearly free; the hardware was the",
            "real cost, and that is the part worth spending on, because heavy bolts get",
            "unbolted and reused on the next and better dome. That is investment that never",
            "goes obsolete. As far as I can tell nobody has put this particular method on",
            "the internet before, which by my own reckoning and absolutely nobody else's",
            "crowns me sovereign of a hobo commune that does not exist, somewhere pleasant",
            "with relaxed local statutes. The crown is imaginary. The building was not.",
        ),
        ("120 brackets x 8 = 960 screws", "130 bolts, 260 washers",
         "10 days, 4 triangles a day",
         "the hardware outlives the dome"),
        32.0, (90.0, 18.0, 16.0), "build_franken_ledger",
    ),
)
