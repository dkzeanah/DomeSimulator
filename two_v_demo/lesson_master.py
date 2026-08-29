"""The master presentation: every tool, every build, every number shown
being made.

This is the one film that walks the whole project end to end: the
toolchain tour (Dome Creator, Dome Forge, the Jig Shop, the Assembly
Line, the video engine itself), the case against the box, the complete
2V geometry and construction masterclass, the hubless method and the
compound cut, raising the frame -- cables in the trees included -- the
frankendome and why it exists, the starter home priced to the dollar,
and the factory case.  It is assembled from the lessons that already
exist plus a run of new chapters, so every borrowed chapter keeps the
painter, the camera and the proof it always had.

The new thing it introduces is the **math screen**: chapters whose
``overlay`` is ``"math"`` keep their picture live on the left while a
worksheet panel on the right reveals the derivation one line at a time
and lands on a conclusion band.  Every line on every math screen comes
from :mod:`two_v_demo.master_facts`, which computes nothing itself -- it
formats the same modules the interactive tools run on.
"""

from __future__ import annotations

import math
from dataclasses import replace

import numpy as np

from .figure import draw_figure, joint_positions, place_figure, walk_pose, POSES
from .geometry import build_demo_geometry, normalize
from .hubless_geometry import compound_setups, hubless_summary
from .lesson_build import BUILD_LESSON
from .lesson_cuts import CUTS_LESSON
from .lesson_franken import FRANKEN_LESSON
from .lesson_hype import CHAPTERS_V6 as HYPE_CHAPTERS, SCENES_V6 as HYPE_SCENES
from .lesson_kickstarter_v2 import (
    CHAPTERS as KICK2_CHAPTERS,
    SCENES as KICK2_SCENES,
)
from .lesson_line import LINE_LESSON
from .lessons import Chapter, Lesson
from .master_facts import (
    ALL_SCREENS,
    master_report,
    steps_chords,
    steps_counted,
    steps_cutlist,
    steps_energy,
    steps_envelope,
    steps_error,
    steps_flatrate,
    steps_franken,
    steps_hubless,
    steps_jigs,
    steps_labour,
    steps_price,
    steps_water,
    validate_master_facts,
)
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
from .segments import PARTY, compose
from .timber import CHAINSAW, draw_timber


GEOMETRY = build_demo_geometry()
SUMMARY = hubless_summary()
SCALE = 5.0


def _rgb(colour) -> tuple[int, int, int]:
    return tuple(int(round(channel * 255)) for channel in colour[:3])


def _mini_dome(batch, centre, size: float, colour=CYAN, radius: float = 0.030,
               phase: float = 1.0) -> None:
    """A small wireframe hemisphere, for the exhibit pedestals."""
    centre = np.asarray(centre, dtype=float)
    edges = list(GEOMETRY.hemisphere_edges)
    shown = max(0, int(len(edges) * clamp(phase)))
    for edge in edges[:shown]:
        a, b = (GEOMETRY.vertices[i] * size + centre for i in edge)
        batch.cylinder(a, b, radius, colour, 5)


def _pedestal(batch, x: float, reveal: float) -> None:
    grow = ease_in_out(clamp(reveal))
    if grow <= 0.02:
        return
    batch.disc(np.array([x, 0.0, 0.05]), 2.6 * grow,
               (0.10, 0.20, 0.30, 1.0), 26)


# ----------------------------------------------------------------------
# The toolchain, as five exhibits in a row
# ----------------------------------------------------------------------

def scene_ms_toolchain(app, opaque, transparent, p: float) -> None:
    """Five pedestals, one per tool, revealed left to right.

    The camera sits on +Y, so +X is screen LEFT: the first exhibit is
    placed at the largest +X and the row reads left to right on film.
    """
    exhibits = (
        ("DOME CREATOR\nwalkable site, live BOM", CYAN),
        ("DOME FORGE\nlayers, panels, jig shop", GREEN),
        ("ASSEMBLY LINE\n15 stations, real economics", AMBER),
        ("MASTERCLASS ENGINE\nthis film, computed", PURPLE),
        ("PRESENTER STUDIO\nscript to screen", RED),
    )
    spacing = 6.4
    for index, (label, colour) in enumerate(exhibits):
        # +X is screen left, so exhibit 0 takes the largest +X.  The
        # first exhibit opens already half-revealed so the chapter never
        # cuts in on an empty stage.
        x = (2.0 - index) * spacing
        reveal = clamp(p * (len(exhibits) + 0.8) - index + 0.5)
        _pedestal(opaque, x, reveal)
        if reveal <= 0.05:
            continue
        grow = ease_in_out(clamp(reveal))
        if index == 0:
            _mini_dome(opaque, (x + 0.7, 0.6, 0.1), 1.7 * grow, CYAN)
            _mini_dome(opaque, (x - 1.3, -0.9, 0.1), 1.0 * grow, MUTED)
        elif index == 1:
            _mini_dome(opaque, (x, 0.0, 0.1), 1.7 * grow, GREEN)
            for face in list(GEOMETRY.hemisphere_faces)[::4]:
                corners = (GEOMETRY.vertices[[int(v) for v in face]]
                           * 1.7 * grow * 1.12 + np.array([x, 0.0, 0.35]))
                transparent.triangle(
                    corners[0], corners[1], corners[2],
                    (0.35, 0.85, 0.60, 0.22),
                    normalize(corners.mean(axis=0) - np.array([x, 0.0, 0.0])))
        elif index == 2:
            for sign in (-1.0, 1.0):
                opaque.box((x, sign * 0.9, 0.22 * grow),
                           (5.2 * grow, 0.16, 0.12), (0.42, 0.46, 0.52, 1.0))
            for portal in range(3):
                gx = x + (portal - 1) * 1.9 * grow
                for sign in (-1.0, 1.0):
                    opaque.cylinder(np.array([gx, sign * 1.5, 0.0]),
                                    np.array([gx, sign * 1.5, 2.5 * grow]),
                                    0.07, AMBER, 5)
                opaque.box((gx, 0.0, 2.5 * grow), (0.16, 3.2, 0.16), AMBER)
            opaque.box((x, 0.0, 0.42 * grow), (1.7, 1.3, 0.3),
                       (0.30, 0.34, 0.40, 1.0))
            _mini_dome(opaque, (x, 0.0, 0.60 * grow), 1.0 * grow, WHITE,
                       0.024)
        elif index == 3:
            opaque.box((x, 0.0, 2.0 * grow), (3.0 * grow, 0.10, 1.9 * grow),
                       (0.07, 0.13, 0.22, 1.0))
            _mini_dome(opaque, (x + 0.03, -0.15, 1.35 * grow), 0.85 * grow,
                       PURPLE, 0.022, phase=p)
            opaque.box((x, -0.12, 1.12 * grow),
                       (2.5 * grow * clamp(p), 0.06, 0.07), AMBER)
        else:
            for leg in range(3):
                angle = math.tau * leg / 3.0 + 0.5
                foot = np.array([x + 0.9 * math.cos(angle),
                                 0.9 * math.sin(angle), 0.0])
                opaque.cylinder(foot, np.array([x, 0.0, 1.8 * grow]),
                                0.05, (0.40, 0.44, 0.50, 1.0), 5)
            opaque.box((x, 0.0, 2.0 * grow), (0.9, 0.6, 0.55), RED)
            opaque.cone(np.array([x, -0.35, 2.0 * grow]),
                        np.array([x, -1.05, 1.7 * grow]), 0.26,
                        (0.24, 0.26, 0.30, 1.0), 10)
            _mini_dome(opaque, (x, -3.4, 0.05), 0.8 * grow, MUTED, 0.02)
        if reveal > 0.45:
            app.world_labels.append(WorldLabel(
                np.array([x, 0.0, 4.3]), label, _rgb(colour)))
    app.world_labels.append(WorldLabel(
        np.array([0.0, 0.0, -1.7]),
        "one codebase -- every tool computes from the same geometry",
        (169, 188, 203)))


# ----------------------------------------------------------------------
# Dome Creator: the walkable site
# ----------------------------------------------------------------------

def scene_ms_creator(app, opaque, transparent, p: float) -> None:
    """The site: two domes, a walking avatar, and the apex camera."""
    main = np.array([3.2, 0.0, 0.0])
    second = np.array([-7.6, -2.4, 0.0])

    build = clamp(p * 1.6)
    edges = list(GEOMETRY.hemisphere_edges)
    for index, edge in enumerate(edges):
        a, b = (GEOMETRY.vertices[i] * 4.6 + main for i in edge)
        draw_timber(opaque, a, b, 0.075, index, CHAINSAW, sides=6)
    shown = int(len(edges) * build)
    for edge in edges[:shown]:
        a, b = (GEOMETRY.vertices[i] * 2.3 + second for i in edge)
        opaque.cylinder(a, b, 0.045, MUTED, 5)

    # The avatar, walking the site toward the main dome.
    walk = clamp(p * 1.15)
    start = np.array([-3.4, 4.6, 0.0])
    goal = np.array([1.4, 3.2, 0.0])
    spot = start + (goal - start) * ease_in_out(walk)
    pose = walk_pose((p * 6.0) % 1.0) if walk < 0.97 else POSES["stand"]
    # The dome is drawn at scale 4.6 for a 10 ft radius, so one foot is
    # 0.46 scene units and the six-foot reference avatar stands 2.76.
    joints = place_figure(
        joint_positions(pose, 2.76), spot,
        math.degrees(math.atan2((goal - start)[1], (goal - start)[0])))
    draw_figure(opaque, joints)
    # The click-to-walk beacon at the destination.
    pulse = 0.5 + 0.5 * math.sin(p * math.tau * 3.0)
    opaque.cone(np.array([goal[0], goal[1], 1.3 + 0.3 * pulse]),
                np.array([goal[0], goal[1], 0.35]), 0.28,
                (1.0, 0.85, 0.25, 1.0), 8)

    # The apex PTZ camera and its sweeping view cone.
    apex = main + np.array([0.0, 0.0, 4.6])
    opaque.cylinder(apex, apex + np.array([0.0, 0.0, 0.55]), 0.06,
                    (0.40, 0.44, 0.50, 1.0), 6)
    opaque.box(apex + np.array([0.0, 0.0, 0.75]), (0.5, 0.5, 0.4),
               (0.16, 0.18, 0.24, 1.0))
    sweep = math.sin(p * math.tau) * 1.8
    foot = main + np.array([sweep, 1.2, 0.0])
    # Wide end on the floor, point at the lens: the camera's field of view.
    transparent.cone(foot, apex + np.array([0.0, 0.0, 0.55]), 1.5,
                     (0.35, 0.80, 1.00, 0.14), 12)

    short = next(c for c in GEOMETRY.edge_classes if c.name == "SHORT")
    long = next(c for c in GEOMETRY.edge_classes if c.name == "LONG")
    app.world_labels.extend([
        WorldLabel(main + np.array([0.0, 0.0, 6.6]),
                   "CLICK ANYWHERE -- THE AVATAR WALKS THERE",
                   (61, 211, 255)),
        WorldLabel(np.array([-7.6, -2.4, 3.6]),
                   f"LIVE BOM\n{short.hemisphere_count + long.hemisphere_count}"
                   f" struts / {len(GEOMETRY.hemisphere_faces)} panels",
                   (111, 235, 155)),
        WorldLabel(main + np.array([0.0, 0.0, 5.6]),
                   "apex PTZ camera + vision", (255, 177, 62)),
        WorldLabel(np.array([0.0, 0.0, -1.8]),
                   "swap any panel, stack cladding, pick a foundation -- "
                   "the bill of materials follows live", (169, 188, 203)),
    ])


# ----------------------------------------------------------------------
# Dome Forge: the layer stack, assembling itself
# ----------------------------------------------------------------------

def scene_ms_forge(app, opaque, transparent, p: float) -> None:
    """The water-harvesting stack going together, layer by layer."""
    layers = 6.0
    # The frame opens already rising, so the first frame is not empty.
    frame_r = clamp(p * layers + 0.2)
    panels_r = clamp(p * layers - 1.0)
    veins_r = clamp(p * layers - 2.0)
    ring_r = clamp(p * layers - 3.0)
    tank_r = clamp(p * layers - 4.0)
    rain_r = clamp(p * layers - 5.0)

    edges = list(GEOMETRY.hemisphere_edges)
    shown = int(len(edges) * ease_in_out(frame_r))
    for index, edge in enumerate(edges[:shown]):
        a, b = (GEOMETRY.vertices[i] * SCALE for i in edge)
        draw_timber(opaque, a, b, 0.08, index, CHAINSAW, sides=6)

    if panels_r > 0.0:
        faces = list(GEOMETRY.hemisphere_faces)
        count = int(len(faces) * ease_in_out(panels_r))
        for face in faces[:count]:
            corners = GEOMETRY.vertices[[int(v) for v in face]] * SCALE * 1.03
            transparent.triangle(
                corners[0], corners[1], corners[2],
                (0.45, 0.75, 0.92, 0.26), normalize(corners.mean(axis=0)))

    if veins_r > 0.0:
        count = int(len(edges) * ease_in_out(veins_r))
        for edge in edges[:count]:
            a, b = (GEOMETRY.vertices[i] * SCALE * 0.93 for i in edge)
            opaque.cylinder(a, b, 0.032, GREEN, 5)

    if ring_r > 0.0:
        segments = 36
        grow = ease_in_out(ring_r)
        for index in range(int(segments * grow)):
            a0 = math.tau * index / segments
            a1 = math.tau * (index + 1) / segments
            radius = SCALE * 1.04
            opaque.cylinder(
                np.array([radius * math.cos(a0), radius * math.sin(a0), 0.28]),
                np.array([radius * math.cos(a1), radius * math.sin(a1), 0.28]),
                0.075, (0.55, 0.58, 0.64, 1.0), 6)

    if tank_r > 0.0:
        grow = ease_in_out(tank_r)
        pipe_top = np.array([SCALE * 1.04, 0.0, 0.28])
        tank_x = SCALE * 1.04 + 2.1
        opaque.cylinder(pipe_top, np.array([tank_x, 0.0, 1.6]), 0.09,
                        (0.62, 0.66, 0.72, 1.0), 6)
        opaque.cylinder(np.array([tank_x, 0.0, 1.6]),
                        np.array([tank_x, 0.0, 0.1]), 0.09,
                        (0.62, 0.66, 0.72, 1.0), 6)
        opaque.cylinder(np.array([tank_x, 0.0, 0.0]),
                        np.array([tank_x, 0.0, 2.2 * grow]), 1.0,
                        (0.24, 0.28, 0.34, 1.0), 14)
        if rain_r > 0.05:
            opaque.cylinder(np.array([tank_x, 0.0, 0.04]),
                            np.array([tank_x, 0.0,
                                      0.04 + 2.0 * grow * rain_r]),
                            0.9, (0.22, 0.55, 0.85, 1.0), 14)

    if rain_r > 0.0:
        for index in range(26):
            angle = math.tau * index / 26.0
            radius = SCALE * (0.35 + 0.55 * ((index * 7) % 10) / 10.0)
            fall = ((rain_r * 2.2 + index * 0.17) % 1.0)
            z = SCALE + 3.0 - fall * 4.2
            opaque.box((radius * math.cos(angle), radius * math.sin(angle), z),
                       (0.06, 0.06, 0.4), (0.45, 0.72, 0.95, 0.85))

    stages = (
        (frame_r, "1  TRIANGLE FRAME", _rgb(WHITE)),
        (panels_r, "2  DISHED PANELS + MICRO-DRAINS", (134, 210, 255)),
        (veins_r, "3  SEAM VEINS -- every leak lands in a channel",
         (111, 235, 155)),
        (ring_r, "4  COLLECTOR RING", (200, 205, 214)),
        (tank_r, "5  DOWNPIPE + CISTERN", (255, 177, 62)),
        (rain_r, "6  RAIN -> TANK", (96, 190, 255)),
    )
    z = SCALE + 3.6
    for reveal, label, colour in stages:
        if reveal > 0.15:
            app.world_labels.append(WorldLabel(
                np.array([-SCALE - 3.4, 0.0, z]), label, colour))
            z -= 1.05
    app.world_labels.append(WorldLabel(
        np.array([0.0, 0.0, -1.8]),
        "every layer hides, fades, reorders -- and the leaky-dome "
        "complaint becomes plumbing", (169, 188, 203)))


# ----------------------------------------------------------------------
# The Jig Shop: two tables build every triangle in the dome
# ----------------------------------------------------------------------

def _triangle_points(angles_deg, side: float):
    """Corner points of a triangle laid flat, longest side on the x axis."""
    a, b, c = (math.radians(v) for v in angles_deg)
    # Law of sines gives the other sides from the base and its angles.
    base = side
    left = base * math.sin(b) / math.sin(c) if math.sin(c) else base
    apex = np.array([left * math.cos(a), left * math.sin(a)])
    return (np.array([0.0, 0.0]), np.array([base, 0.0]), apex)


def _jig_table(app, opaque, centre_x: float, angles_deg, count: int,
               label: str, colour, reveal: float) -> None:
    if reveal <= 0.02:
        return
    grow = ease_in_out(clamp(reveal))
    top_z = 1.45
    opaque.box((centre_x, 0.0, top_z), (5.2, 4.0, 0.16),
               (0.32, 0.26, 0.20, 1.0))
    for sx in (-1.0, 1.0):
        for sy in (-1.0, 1.0):
            opaque.cylinder(
                np.array([centre_x + sx * 2.3, sy * 1.7, 0.0]),
                np.array([centre_x + sx * 2.3, sy * 1.7, top_z]),
                0.09, (0.22, 0.18, 0.14, 1.0), 6)

    points = _triangle_points(angles_deg, 3.6)
    centroid = sum(points) / 3.0
    corners = [np.array([centre_x + (pt - centroid)[0],
                         (pt - centroid)[1], top_z + 0.16])
               for pt in points]
    boards = int(3 * grow) + (1 if grow > 0.05 else 0)
    for index in range(min(3, boards)):
        a = corners[index]
        b = corners[(index + 1) % 3]
        draw_timber(opaque, a, b, 0.11, int(centre_x * 10) + index,
                    CHAINSAW, sides=4)
        # The fence outside each board, and a corner stop past each tip.
        direction = (b - a) / (np.linalg.norm(b - a) or 1.0)
        outward = np.array([direction[1], -direction[0], 0.0])
        if float(np.dot(outward, (a + b) * 0.5
                        - np.array([centre_x, 0.0, top_z]))) < 0.0:
            outward = -outward
        # The fence is a rail along the board's own direction -- a box
        # would be axis-aligned and lie across the table on the two
        # slanted edges.
        offset = outward * 0.34
        fence_a = a + offset + direction * 0.35
        fence_b = b + offset - direction * 0.35
        opaque.cylinder(fence_a, fence_b, 0.10, (0.55, 0.58, 0.64, 1.0), 4)
    if grow > 0.75:
        for corner in corners:
            opaque.box((float(corner[0]), float(corner[1]), top_z + 0.16),
                       (0.24, 0.24, 0.28), AMBER)

    if grow > 0.4:
        app.world_labels.append(WorldLabel(
            np.array([centre_x, 0.0, top_z + 2.6]),
            label, _rgb(colour)))
        app.world_labels.append(WorldLabel(
            np.array([centre_x, 0.0, top_z + 1.7]),
            "corners " + " / ".join(f"{a:.1f}°" for a in angles_deg)
            + f"   x{count}", (200, 214, 226)))


def scene_ms_jigshop(app, opaque, transparent, p: float) -> None:
    """Two jigs on two tables: the whole dome's fabrication tooling."""
    equilateral = next(t for t in GEOMETRY.triangle_classes
                       if len(set(t.side_names)) == 1)
    isosceles = next(t for t in GEOMETRY.triangle_classes
                     if len(set(t.side_names)) > 1)
    # +X is screen left at this camera, so the equilateral goes to +X.
    _jig_table(app, opaque, 4.3, equilateral.angles_deg,
               equilateral.hemisphere_count,
               "JIG ONE -- EQUILATERAL", CYAN, clamp(p * 2.4 + 0.25))
    _jig_table(app, opaque, -4.3, isosceles.angles_deg,
               isosceles.hemisphere_count,
               "JIG TWO -- ISOSCELES", AMBER, clamp(p * 2.4 - 0.55))
    setups = compound_setups()
    if p > 0.62:
        app.world_labels.append(WorldLabel(
            np.array([0.0, 0.0, -1.4]),
            f"{len(setups)} saw setups cut all {SUMMARY.struts} struts -- "
            "load, cut, drop in the jig, screw, repeat",
            (169, 188, 203)))


# ----------------------------------------------------------------------
# The teaching-video engine: every frame is computed
# ----------------------------------------------------------------------

def scene_ms_engine(app, opaque, transparent, p: float) -> None:
    """A film strip whose frames are the dome at successive moments."""
    frames = 5
    for index in range(frames):
        # +X is screen left: the first frame takes the largest +X, and
        # opens already part-grown so the stage is never empty.
        x = (2.0 - index) * 5.6
        reveal = clamp(p * (frames + 1.0) - index + 0.4)
        if reveal <= 0.02:
            continue
        grow = ease_in_out(reveal)
        opaque.box((x, 0.0, 2.6), (4.6 * grow, 0.10, 3.4 * grow),
                   (0.06, 0.12, 0.21, 1.0))
        for hole in range(4):
            hx = x - 2.0 + hole * 1.33
            opaque.box((hx, -0.10, 4.55 * grow), (0.5, 0.06, 0.3),
                       (0.02, 0.05, 0.09, 1.0))
        # The dome sits centred in its frame, big enough to read as the
        # subject of the film rather than a scribble along the sill.
        _mini_dome(opaque, (x, -0.25, 1.55), 1.85 * grow, CYAN, 0.034,
                   phase=(index + 1) / frames)
    bar = clamp(p * 1.1)
    opaque.box((0.0, 0.0, 0.35), (26.0, 0.2, 0.16), (0.15, 0.25, 0.35, 1.0))
    if bar > 0.01:
        # Fill from +X, which this camera renders as screen left.
        opaque.box((13.0 - 13.0 * bar, 0.0, 0.35),
                   (26.0 * bar, 0.22, 0.20), AMBER)
    app.world_labels.extend([
        WorldLabel(np.array([0.0, 0.0, 6.4]),
                   "EVERY FRAME IS A PURE FUNCTION OF TIME",
                   (240, 247, 252)),
        WorldLabel(np.array([0.0, 0.0, -1.6]),
                   "the narration is measured first and the film is cut to "
                   "fit it -- same input, same film, forever",
                   (169, 188, 203)),
    ])


# ----------------------------------------------------------------------
# Assembling the script
# ----------------------------------------------------------------------

def _chapters_by_slug(chapters) -> dict[str, Chapter]:
    return {chapter.slug: chapter for chapter in chapters}


_BUILD = _chapters_by_slug(BUILD_LESSON.chapters)
_CUTS = _chapters_by_slug(CUTS_LESSON.chapters)
_FRANKEN = _chapters_by_slug(FRANKEN_LESSON.chapters)
_LINE = _chapters_by_slug(LINE_LESSON.chapters)
_KICK2 = _chapters_by_slug(KICK2_CHAPTERS)
_HYPE = _chapters_by_slug(HYPE_CHAPTERS)


def _borrow(source: dict[str, Chapter], slug: str, prefix: str,
            overlay: str | None = None) -> Chapter:
    chapter = source[slug]
    return replace(chapter, slug=f"{prefix}_{slug}", overlay=overlay)


def _teach(source: dict[str, Chapter], slug: str, prefix: str) -> Chapter:
    """A borrowed teaching chapter keeps its cards inside the montage."""
    return _borrow(source, slug, prefix, overlay="teaching")


def _camera_of(source: dict[str, Chapter], slug: str,
               zoom: float = 1.30) -> tuple[float, float, float]:
    """The source chapter's framing, pulled back to clear the worksheet."""
    yaw, pitch, distance = source[slug].camera
    return (yaw, pitch, distance * zoom)


def _math(slug: str, title: str, promise: str, narration: tuple[str, ...],
          steps: tuple[str, ...], duration: float,
          camera: tuple[float, float, float], stage: str) -> Chapter:
    return Chapter(slug, "00", title, promise, narration, steps,
                   duration, camera, stage, "math")


CHAPTERS: tuple[Chapter, ...] = (
    # ------------------------------------------------------------------
    # ACT I -- the open, and the toolchain
    # ------------------------------------------------------------------
    Chapter(
        "ms_open", "00", "The whole argument, start to finish",
        "A starter home you can count.",
        (
            "This is the master presentation. Everything this project knows, in one",
            "film. The software tools and their worlds. The geometry, derived from",
            "nothing. The jigs, the compound cuts, the frames, the raising. The",
            "frankendome and the reason it exists. And a starter home, priced to the",
            "dollar, against the square house it wants to replace.",
            "One rule holds the whole way through: every number you are about to",
            "see is computed, on camera, by the same code that draws these pictures.",
            "When you see the math screen, you are watching the numbers being made.",
        ),
        (), 16.0, (34.0, 20.0, 17.0), "kick_title",
    ),
    Chapter(
        "ms_tools", "00", "One codebase, five worlds",
        "Every tool computes from the same geometry.",
        (
            "The project is one codebase wearing five faces. A dome creator you",
            "walk around in. A dome forge that builds one dome out of layers, like",
            "a paint program builds an image. A factory simulation that prices every",
            "screw. A teaching-video engine, which is what is rendering this very",
            "film. And a presenter studio that turns a script into a movie.",
            "They all read the same geometry module, so a strut length in one tool",
            "cannot disagree with the same strut in another.",
        ),
        (), 15.0, (90.0, 18.0, 26.0), "ms_toolchain",
    ),
    Chapter(
        "ms_creator", "00", "The Dome Creator",
        "A build-a-home world with a live bill of materials.",
        (
            "The Dome Creator is a walkable site. Click the ground and the avatar",
            "walks there. Click a panel and you can swap it: glass, shingle, solar,",
            "plastic sheeting, anything. Change the frequency, the radius, the frame",
            "material, the foundation. Every choice updates a live bill of",
            "materials: strut cut lists, panel weights, costs, even how many trees",
            "you would have to harvest. A camera hangs from every apex, watching the",
            "floor, counting what it sees. It is a sales floor, a design desk and a",
            "planning meeting in one window.",
        ),
        (), 16.0, (90.0, 16.0, 25.0), "ms_creator",
    ),
    Chapter(
        "ms_forge", "00", "The Dome Forge",
        "One dome, made of layers you can peel apart.",
        (
            "The Dome Forge is a single dome, taken apart like layers in a paint",
            "program. Frame, panels, drains, veins, ring, pipe, tank, rain --",
            "every part is its own layer you can hide, fade, reorder or tune.",
            "The default stack answers the oldest dome complaint there is. Domes",
            "leak, people say. So the panels dish inward and drain to one point",
            "each. A vein runs along the inside of every seam, standing off from",
            "the skin, so anything that gets past a joint lands in a channel",
            "instead of your floor. The veins run downhill to a collector ring,",
            "down a pipe, into a cistern. The leak becomes the water supply.",
        ),
        (), 17.0, (58.0, 18.0, 24.0), "ms_forge",
    ),
    Chapter(
        "ms_jigshop", "00", "The Jig Shop",
        "Two tables build all forty triangles.",
        (
            "Inside the forge is a jig shop, and it is the whole factory in",
            "miniature. A 2V dome has forty triangles but only two shapes: ten",
            "equilateral, thirty isosceles. So you build two jigs. A base plate, a",
            "scribed triangle, fences along each board, stops at each corner.",
            "Load three boards, screw the corners, lift out a finished panel.",
            "We will come back here with the exact angles once you have seen where",
            "they come from.",
        ),
        (), 14.0, (90.0, 34.0, 22.0), "ms_jigshop",
    ),
    Chapter(
        "ms_line", "00", "The Assembly Line",
        "Fifteen stations, and every dollar accounted for.",
        (
            "The assembly line is a factory simulation in the real",
            "trailer-plant order. A carriage rolls the home down the rails through",
            "fifteen stations: floor, frame, utility column, water, power,",
            "fixtures, insulation, sheetrock, sheathing, membrane, shingle scales,",
            "fiberglass, the sealed hatch, the fit-out, the solar band. Every",
            "element carries a real material cost and a real install time, and a",
            "simulated crew walks every part from the stockpile at a human stride,",
            "so the labor hours are earned, not assumed. Panels show profit and",
            "loss, the bottleneck station, break-even. It is an investor tool that",
            "happens to look like a video game.",
        ),
        (), 17.0, _camera_of(_LINE, "overview", 1.0), "line_overview",
    ),
    Chapter(
        "ms_engine", "00", "The engine rendering this film",
        "Programmatic video: correct because it is computed.",
        (
            "And the film you are watching right now is the fifth tool. Every",
            "frame is a pure function of time. Every scene is drawn by code, and",
            "every figure on screen is calculated by a module that also proves",
            "itself before a single frame renders. Generative video cannot be",
            "asked to be correct. This can. That promise is about to matter,",
            "because of what comes next.",
        ),
        (), 13.0, (90.0, 14.0, 30.0), "ms_engine",
    ),
    _math(
        "ms_math_counted", "Nothing here is typed in",
        "Watch the model count itself.",
        (
            "Here is the first math screen, and the rule it stands for.",
            "The panel on the right is counting the dome behind it, live.",
            "Forty panels. Sixty-five edges in two lengths. Twenty-six corners.",
            "Nobody wrote those numbers into a caption; the code that draws the",
            "dome is the code that counts it. Every claim in this film -- every",
            "angle, every dollar, every gallon -- reaches the screen the same",
            "way. If we cannot compute it, we name where it came from.",
        ),
        steps_counted(), 22.0, (31.0, 25.0, 19.0), "classes",
    ),

    # ------------------------------------------------------------------
    # ACT II -- the case against the box
    # ------------------------------------------------------------------
    _borrow(_KICK2, "problem", "k"),
    _borrow(_KICK2, "versus", "k"),
    _math(
        "ms_math_envelope", "The box comparison, derived",
        "Same floor. Less building. It is arithmetic.",
        (
            "Let us do that comparison properly, on the math screen.",
            "Same floor area for both shapes. The box needs walls, a roof and",
            "gables. The dome needs forty flat triangles. Add them up and the",
            "dome wants about forty percent less outside for the same inside --",
            "and the skin is the part you build, seal, paint and heat.",
            "The wind figures are the one borrowed pair on this screen: published",
            "drag coefficients, named as such. Everything else is geometry.",
        ),
        steps_envelope(), 24.0, _camera_of(_KICK2, "versus"), "kick_versus",
    ),
    _borrow(_KICK2, "triangle", "k"),
    _borrow(_KICK2, "wind", "k"),

    # ------------------------------------------------------------------
    # ACT III -- the geometry, from phi to two lengths
    # ------------------------------------------------------------------
    _teach(_BUILD, "brief", "b"),
    _teach(_BUILD, "vocab", "b"),
    _teach(_BUILD, "parent", "b"),
    _teach(_BUILD, "phi", "b"),
    _teach(_BUILD, "unit", "b"),
    _teach(_BUILD, "halve", "b"),
    _teach(_BUILD, "project", "b"),
    _teach(_BUILD, "classes", "b"),
    _math(
        "ms_math_chords", "Two lengths, derived from nothing",
        "From the golden ratio to a tape measure.",
        (
            "Now watch the whole derivation land in eight lines.",
            "Phi places twelve corners. One division puts them on a unit sphere.",
            "Halving every edge and pushing the midpoints back out changes the",
            "distances -- and when you measure every edge again, only two",
            "numbers remain. Multiply by any radius you like and those two",
            "numbers become two boards. The pair this project was originally",
            "asked about fits a ten-foot-radius dome almost exactly.",
        ),
        steps_chords(), 24.0, (29.0, 22.0, 19.0), "projection",
    ),

    # ------------------------------------------------------------------
    # ACT IV -- radius, parts, cut list
    # ------------------------------------------------------------------
    _teach(_BUILD, "sizing", "b"),
    _teach(_BUILD, "rings", "b"),
    _teach(_BUILD, "audit", "b"),
    _teach(_BUILD, "hubkit", "b"),
    _teach(_BUILD, "deduction", "b"),
    _teach(_BUILD, "endcut", "b"),
    _teach(_BUILD, "bevel", "b"),
    _teach(_BUILD, "hubs", "b"),
    _teach(_BUILD, "stock", "b"),
    _teach(_BUILD, "cutting", "b"),
    _teach(_BUILD, "cutlist", "b"),
    _math(
        "ms_math_cutlist", "The cut list makes itself",
        "One radius in, a lumber order out.",
        (
            "Here is the same chain as arithmetic. Pick the radius. The two",
            "factors turn it into two cut lengths. Subtract the connector",
            "deduction you measured -- measured, never guessed. Then the stock",
            "plan falls out: how many eight-foot sticks, how many pieces from",
            "each, and exactly how much offcut every stick leaves behind.",
            "Change the radius and every line on this screen recomputes. That",
            "is what it means for a house to have a parts list instead of a",
            "price opinion.",
        ),
        steps_cutlist(), 24.0, (31.0, 25.0, 20.0), "cutlist",
    ),

    # ------------------------------------------------------------------
    # ACT V -- hubless, and the compound cut
    # ------------------------------------------------------------------
    _teach(_BUILD, "hubless_intro", "b"),
    _teach(_BUILD, "hubless_edge", "b"),
    _math(
        "ms_math_hubless", "One hundred and twenty sticks, checked",
        "No hubs. The count proves itself.",
        (
            "The hubless method sounds wasteful until you count it honestly.",
            "Every triangle brings its own three boards, so every interior seam",
            "carries two boards side by side, and the rim seams carry one.",
            "Run the check and it balances exactly. What you bought with the",
            "extra wood is the removal of every hub: no welded stars, no",
            "brackets to order, no single part that the whole build waits on.",
        ),
        steps_hubless(), 22.0, _camera_of(_BUILD, "hubless_edge"),
        "build_hubless_edge",
    ),
    _teach(_BUILD, "hubless_cut", "b"),
    _teach(_BUILD, "hubless_saw", "b"),
    _teach(_CUTS, "two_angles", "c"),
    _teach(_CUTS, "machines", "c"),
    _teach(_CUTS, "tilt", "c"),
    _teach(_CUTS, "prove_tilt", "c"),
    _teach(_CUTS, "limit", "c"),
    _teach(_CUTS, "complement", "c"),
    _teach(_CUTS, "sled", "c"),
    _teach(_CUTS, "fivecut", "c"),
    _teach(_CUTS, "lap", "c"),
    _teach(_CUTS, "first_end", "c"),
    _teach(_CUTS, "turn", "c"),
    _teach(_CUTS, "batch", "c"),
    _teach(_CUTS, "dryfit", "c"),
    _math(
        "ms_math_jigs", "Every saw setting, measured off the model",
        "Two jigs. Six settings. Forty triangles.",
        (
            "Back to the jig shop, now with the numbers earned.",
            "Two triangle shapes, so two jigs. Every mitre is ninety degrees",
            "minus half the corner it closes. Every bevel is half the fold to",
            "the neighbouring panel. Count the distinct pairs and the whole",
            "dome needs six saw setups -- and the ends that sit past a fifty",
            "degree saw are reached by swinging to the complement and turning",
            "the stick a quarter turn. These figures are not from a chart.",
            "They are re-measured off the assembled 3D model every time the",
            "self-test runs, and the build stops if they ever disagree.",
        ),
        steps_jigs(), 26.0, (90.0, 34.0, 24.0), "ms_jigshop",
    ),

    # ------------------------------------------------------------------
    # ACT VI -- assembly and raising
    # ------------------------------------------------------------------
    _teach(_BUILD, "subassembly", "b"),
    _teach(_BUILD, "layout", "b"),
    _teach(_BUILD, "foundation", "b"),
    _teach(_BUILD, "riser", "b"),
    _teach(_BUILD, "raise", "b"),
    _teach(_BUILD, "apex", "b"),
    _math(
        "ms_math_error", "What an eighth of an inch becomes",
        "The base ring multiplies your mistakes by phi.",
        (
            "Before the skin goes on, one number worth respecting.",
            "The ten-sided base ring is a regular polygon, and its radius is",
            "the strut length divided by a fixed constant -- and for ten sides",
            "that constant happens to be one over the golden ratio. So every",
            "error in a base strut reaches the foundation multiplied by phi.",
            "That is not a superstition, it is trigonometry, and it is why the",
            "measurement loop checks every ring before the next one goes up.",
        ),
        steps_error(), 22.0, _camera_of(_BUILD, "error"), "build_error",
    ),
    _teach(_BUILD, "check", "b"),
    _teach(_BUILD, "skin", "b"),
    _teach(_BUILD, "openings", "b"),
    _teach(_BUILD, "failures", "b"),
    _teach(_BUILD, "franken_trees", "b"),

    # ------------------------------------------------------------------
    # ACT VII -- the frankendome
    # ------------------------------------------------------------------
    Chapter(
        "ms_franken_why", "00", "Why I built the ugly one",
        "The beautiful math needed an ugly test.",
        (
            "Everything you have seen so far assumes care. Milled lumber,",
            "measured deductions, jigs proved with a five-cut test. The",
            "frankendome is the opposite experiment, and I built it on purpose.",
            "Take whatever the chainsaw made. Skip the compound cuts. Fold flat",
            "steel into brackets instead of mitering seams. Let nothing land",
            "where it should, and then see what the geometry forgives.",
            "A normal hubless build replaces the hub with precision. The",
            "frankendome replaces it with tolerance -- and that difference is",
            "the entire experiment. If triangulation only works for careful",
            "people with good stock, it is a luxury. If it works for salvage",
            "and a folded bracket, it is a housing method.",
        ),
        (), 18.0, (34.0, 20.0, 18.0), "fk_premise",
    ),
    _teach(_FRANKEN, "stock", "f"),
    _teach(_FRANKEN, "bracket_flat", "f"),
    _teach(_FRANKEN, "bracket_bend", "f"),
    _teach(_FRANKEN, "bracket_fitted", "f"),
    _teach(_FRANKEN, "slack", "f"),
    _teach(_FRANKEN, "settle", "f"),
    _teach(_FRANKEN, "skin", "f"),
    _teach(_FRANKEN, "hubless", "f"),
    _teach(_FRANKEN, "doubling", "f"),
    _teach(_FRANKEN, "cost", "f"),
    _teach(_FRANKEN, "trade", "f"),
    _math(
        "ms_math_franken", "The frankendome, audited",
        "Ten days of work, six months of weather.",
        (
            "And here is the ugly one on the math screen, counted like",
            "everything else. Forty triangles, three folded brackets each,",
            "eight screws a bracket, two bolts a seam. Ten days of work.",
            "It has now stood through half a year of weather -- eighteen times",
            "longer than it took to build, and counting. The point is not that",
            "sloppy is good. The point is that the shape carries what the",
            "craftsmanship cannot, and that is exactly the margin a first-time",
            "builder needs.",
        ),
        steps_franken(), 22.0, _camera_of(_FRANKEN, "ledger"), "fk_ledger",
    ),
    _borrow(_HYPE, "platform", "h"),
    _borrow(_HYPE, "bones", "h"),
    _borrow(_HYPE, "mutate", "h"),
    _borrow(_HYPE, "swap", "h"),
    _borrow(_HYPE, "organs", "h"),
    _borrow(_HYPE, "skins", "h"),
    _borrow(_HYPE, "lines", "h"),
) + PARTY.chapters + (

    # ------------------------------------------------------------------
    # ACT VIII -- the starter home, priced
    # ------------------------------------------------------------------
    _borrow(_KICK2, "pony", "k"),
    _borrow(_KICK2, "flatrate", "k"),
    _math(
        "ms_math_flatrate", "The flat rate, proved",
        "Nine times the house. The same parts list.",
        (
            "This is the number that turns a weekend project into a product,",
            "so let us prove it rather than repeat it. Scale the dome from ten",
            "feet to thirty and count again. The floor grows nine times over,",
            "because area grows with the radius squared. The struts, the",
            "brackets and the screws do not change at all. The sticks get",
            "longer; the list of operations stays exactly the same length.",
            "Labor is priced by operations. That is why dome labor is a flat",
            "rate, and why the bigger house is the better deal.",
        ),
        steps_flatrate(), 24.0, _camera_of(_KICK2, "flatrate"),
        "kick_flatrate",
    ),
    _borrow(_KICK2, "brim", "k"),
    _borrow(_KICK2, "water", "k"),
    _math(
        "ms_math_water", "The water plant, derived",
        "Seven thousand gallons off a hat brim.",
        (
            "The rain figure sounds invented, so here is where it comes from.",
            "The hat rim plus an eighteen inch brim sweeps a circle, and rain",
            "falls straight down, so the flat area of that circle is the",
            "catchment. Multiply by an average year of rain, by the gallons in",
            "an inch of water on a square foot, and by an honest runoff",
            "factor. The climate numbers are borrowed and named; substitute",
            "your own rainfall and the screen recomputes. The shape of the",
            "roof was already doing the collecting -- the tank just agrees to",
            "accept it.",
        ),
        steps_water(), 24.0, _camera_of(_KICK2, "water"), "kick_water",
    ),
    _borrow(_KICK2, "hat", "k"),
    _borrow(_KICK2, "bom", "k"),
    _math(
        "ms_math_price", "The price guide, receipts attached",
        "Four ways to build it, priced at the till.",
        (
            "Here is the price guide, and the rules it was priced under.",
            "Nothing salvaged, nothing donated, nothing found. Every board,",
            "every ounce of resin, every screw at retail. Four versions of the",
            "same twenty-foot starter home: the bare cheapest, a budget build,",
            "the pristine version with the laminated hat, and the fully",
            "glassed one. The cheapest is under the price of a used car, and",
            "the dearest finished shell is still under ten thousand dollars.",
            "Every line traces to a priced part in the costing module, and the",
            "audit report that ships with this film prints the lot.",
        ),
        steps_price(), 24.0, _camera_of(_KICK2, "bom"), "kick_bom",
    ),
    _borrow(_KICK2, "energy", "k"),
    _math(
        "ms_math_energy", "A year of comfort, derived",
        "The skin you did not build never sends a bill.",
        (
            "The running cost is the same arithmetic a heat-loss engineer",
            "does, so watch it happen. Take each building's skin area, times",
            "the wall's U value -- same insulation in both. Times the degree",
            "days of a middling American climate, heating and cooling both.",
            "Convert to kilowatt hours, price at seventeen cents. The dome",
            "wins by exactly its missing skin, every single year, forever.",
            "The climate and the power price are borrowed constants, named on",
            "screen; the geometry is not.",
        ),
        steps_energy(), 24.0, _camera_of(_KICK2, "energy"), "kick_energy",
    ),
    _borrow(_KICK2, "paint", "k"),

    # ------------------------------------------------------------------
    # ACT IX -- the factory case
    # ------------------------------------------------------------------
    _teach(_LINE, "why", "l"),
    _teach(_LINE, "cycle", "l"),
    _teach(_LINE, "fasten", "l"),
    _math(
        "ms_math_labour", "What a build costs the builders",
        "Attack the screw gun, not the lifting.",
        (
            "One more derivation, because it changes what a dome factory",
            "should even be. Simulate every part placement in the build --",
            "every walk, lift, carry, position, fastening and rest -- with the",
            "body model used in ergonomics research. The lifting everyone",
            "worries about turns out to be a fraction of one percent of the",
            "fuel. Fastening, which raises nothing at all, is ninety percent",
            "of it. So the factory's job is not a crane. It is jigs, batching",
            "and better fastening -- which is exactly what the jig shop and",
            "the line you saw are for.",
        ),
        steps_labour(), 24.0, _camera_of(_LINE, "efficiency"),
        "line_efficiency",
    ),
    _borrow(_KICK2, "factory", "k"),

    # ------------------------------------------------------------------
    # ACT X -- the close
    # ------------------------------------------------------------------
    _borrow(_KICK2, "points", "k"),
    Chapter(
        "ms_close", "00", "Build one. Then build the next one faster.",
        "The geometry does not check your credit.",
        (
            "So that is the whole argument. A shape that spends less on skin",
            "and gives it back every winter. Two lengths of wood, two jigs, six",
            "saw settings. A build method that forgave a chainsaw, so it will",
            "forgive you. A price list with receipts, an energy bill you can",
            "derive, and a factory whose economics are simulated down to the",
            "footsteps. Every number in this film came out of code you can run,",
            "and the parts that are borrowed are named out loud.",
            "A sphere encloses the most room with the least material whether",
            "you are a developer or a widow. The geometry does not check your",
            "credit. Build one. Then build the next one faster.",
        ),
        (), 16.0, (90.0, 18.0, 26.0), "ms_toolchain",
    ),
)


CHAPTERS = tuple(
    replace(chapter, number=f"{index + 1:02d}")
    for index, chapter in enumerate(CHAPTERS)
)


SCENES = {}
SCENES.update(BUILD_LESSON.scenes)
SCENES.update(CUTS_LESSON.scenes)
SCENES.update(FRANKEN_LESSON.scenes)
SCENES.update(LINE_LESSON.scenes)
SCENES.update(HYPE_SCENES)
SCENES.update(KICK2_SCENES)
SCENES.update(PARTY.scenes)
SCENES.update({
    "ms_toolchain": scene_ms_toolchain,
    "ms_creator": scene_ms_creator,
    "ms_forge": scene_ms_forge,
    "ms_jigshop": scene_ms_jigshop,
    "ms_engine": scene_ms_engine,
})

# Stages the renderer draws with its own built-in painters: no entry in
# SCENES is needed, but the selftest still has to know they are real.
# These are the original fourteen-chapter lesson's stages, which live as
# ``scene_*`` methods on the app itself.
BUILTIN_STAGES = {
    "hero", "rigidity", "platonic", "coordinates", "icosahedron",
    "midpoints", "projection", "classes", "derivations", "audit",
    "cutlist", "assembly", "verification", "finale",
}


def master_equations(app, stage: str) -> list[str]:
    """Delegate live figures to whichever source lesson owns the stage."""
    for lesson in (BUILD_LESSON, FRANKEN_LESSON, CUTS_LESSON, LINE_LESSON):
        if lesson.equations is None:
            continue
        try:
            lines = lesson.equations(app, stage)
        except Exception:
            continue
        if lines:
            return list(lines)
    return []


def master_full_report() -> str:
    from .dome_advantage import advantage_report
    from .dome_costing import costing_report
    from .dome_performance import performance_report

    rule = "\n\n" + "=" * 68 + "\n\n"
    return rule.join((
        master_report(),
        advantage_report(),
        costing_report(),
        performance_report(),
    ))


def validate_master() -> None:
    """Prove the composition and every new painter before a frame renders."""
    from .render_kit import TriangleBatch

    validate_master_facts()

    lesson = MASTER_LESSON
    slugs = [chapter.slug for chapter in lesson.chapters]
    assert len(set(slugs)) == len(slugs), "duplicate slug in the master"

    for chapter in lesson.chapters:
        assert chapter.narration, chapter.slug
        painted = (chapter.stage in lesson.scenes
                   or chapter.stage in BUILTIN_STAGES)
        assert painted, (chapter.slug, chapter.stage)
        if chapter.overlay == "math":
            # A math screen with nothing to derive is a broken promise:
            # it needs steps plus a conclusion long enough to be a
            # sentence.
            assert len(chapter.equations) >= 5, chapter.slug
            assert len(chapter.equations[-1]) >= 30, chapter.slug

    # Every math screen the facts module offers is used exactly once.
    used = {chapter.equations for chapter in lesson.chapters
            if chapter.overlay == "math"}
    offered = {builder() for _, builder in ALL_SCREENS}
    assert used == offered, (
        f"{len(offered - used)} unused screens, "
        f"{len(used - offered)} unknown screens")

    # The acts arrive in the order the narration promises: tools before
    # geometry, geometry before the frankendome, frankendome before the
    # price guide, and the close last before the appended segments.
    order = {slug: index for index, slug in enumerate(slugs)}
    assert order["ms_tools"] < order["b_parent"] < order["b_hubless_intro"]
    assert order["b_hubless_intro"] < order["ms_franken_why"]
    assert order["ms_franken_why"] < order["k_bom"] < order["ms_close"]

    # Each new painter must actually draw and label at every phase.
    class _App:
        def __init__(self):
            self.world_labels = []

    for stage in ("ms_toolchain", "ms_creator", "ms_forge", "ms_jigshop",
                  "ms_engine"):
        painter = SCENES[stage]
        for progress in (0.0, 0.35, 0.7, 1.0):
            probe = _App()
            opaque, transparent = TriangleBatch(), TriangleBatch()
            painter(probe, opaque, transparent, progress)
            assert opaque.vertices or transparent.vertices, (stage, progress)
            for label in probe.world_labels:
                assert label.text.strip(), (stage, progress)

    # The jig tables must show the same angles the jigs are cut to.
    probe = _App()
    SCENES["ms_jigshop"](probe, TriangleBatch(), TriangleBatch(), 1.0)
    text = " ".join(label.text for label in probe.world_labels)
    assert "60.0" in text and "68.9" in text, text


_MASTER_BASE = Lesson(
    key="master",
    brand="DOMESIM / THE WHOLE ARGUMENT",
    title="The Dome Simulator Master Presentation",
    chapters=CHAPTERS,
    scenes=SCENES,
    equations=master_equations,
    selftest=validate_master,
    report=master_full_report,
    snapshot_prefix="master",
    style="hype",
    voice_rate="+4%",
    label_layout="declutter",
)

MASTER_LESSON = compose(_MASTER_BASE, include=("whoami",))
