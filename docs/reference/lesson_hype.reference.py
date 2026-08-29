"""REFERENCE COPY -- do not edit, do not import.

Copied from two_v_demo/lesson_hype.py so an author (human or model) can read the
real thing without touching it. The live file is the source of
truth; this one is a snapshot for imitation.
"""

"""FRANKENDOME -- the montage.

Not a teaching lesson.  This one runs full-frame with a single line of
type over it, at a faster clip than the masterclasses, and it exists to
say what the project is for rather than how the geometry works.

The pictures reuse the same 2V hemisphere everything else in this package
is built on, because the argument is that one skeleton carries fifty years
of different panels -- and showing that with the actual geometry is worth
more than showing it with a stock shape.
"""

from __future__ import annotations

import math
from dataclasses import replace

import numpy as np

from .figure import POSES, draw_figure, joint_positions, place_figure
from .geometry import build_demo_geometry, normalize
from .lessons import Chapter, Lesson
from .segments import compose
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
SCALE = 5.2
PALETTE = (CYAN, AMBER, GREEN, PURPLE, RED, (0.35, 0.85, 0.92, 1.0))


def _rgb(colour) -> tuple[int, int, int]:
    return (int(colour[0] * 255), int(colour[1] * 255), int(colour[2] * 255))


def _frame(batch, scale: float = SCALE, colour=CYAN, radius: float = 0.075,
           reveal: float = 1.0) -> None:
    """The skeleton itself: the thing that is supposed to outlive everything."""
    edges = list(GEOMETRY.hemisphere_edges)
    count = int(math.ceil(len(edges) * clamp(reveal)))
    for edge in edges[:count]:
        a, b = (GEOMETRY.vertices[i] * scale for i in edge)
        batch.cylinder(a, b, radius, colour, 8)


def _panels(batch, scale: float = SCALE, colour_of=None, alpha: float = 0.30,
            subset=None) -> None:
    faces = list(GEOMETRY.hemisphere_faces)
    for index, face in enumerate(faces):
        if subset is not None and index not in subset:
            continue
        corners = GEOMETRY.vertices[[int(v) for v in face]] * scale
        colour = colour_of(index) if colour_of else CYAN
        normal = normalize(corners.mean(axis=0))
        batch.triangle(corners[0], corners[1], corners[2],
                       (colour[0], colour[1], colour[2], alpha), normal)


def _cards(app, batch, rows, p: float, height: float = 2.4,
           span: float = 13.0, z: float = 1.6) -> None:
    """A row of labelled blocks: the montage's workhorse."""
    reveal = clamp(p * 1.4)
    if not rows:
        return
    step = span / max(1, len(rows) - 1) if len(rows) > 1 else 0.0
    for index, (label, colour) in enumerate(rows):
        if index / len(rows) > reveal:
            continue
        x = -span * 0.5 + index * step if len(rows) > 1 else 0.0
        batch.box((x, 0.0, z), (max(1.2, span / len(rows) * 0.72), 0.55, height),
                  colour)
        app.world_labels.append(WorldLabel(
            np.array([x, 0.0, z + height * 0.5 + 0.6]), label, _rgb(colour)))


# ----------------------------------------------------------------------
# Scenes
# ----------------------------------------------------------------------

def scene_hype_bones(app, opaque, transparent, p: float) -> None:
    """The skeleton, snapping into being."""
    reveal = smoothstep(clamp(p * 1.9))
    _frame(opaque, SCALE, CYAN, 0.085, reveal)
    pulse = 0.5 + 0.5 * math.sin(p * math.tau * 2.0)
    _panels(transparent, SCALE, lambda i: CYAN, 0.05 + 0.07 * pulse)
    app.world_labels.append(WorldLabel(
        np.array([0.0, 0.0, SCALE + 1.4]), "BUILD THE BONES ONCE", (61, 211, 255)))


def scene_hype_platform(app, opaque, transparent, p: float) -> None:
    """The bones hold still while the panels keep changing."""
    _frame(opaque, SCALE, WHITE, 0.075)
    churn = p * 3.0

    def colour_of(index: int):
        return PALETTE[(index + int(churn * 6) + index * 3) % len(PALETTE)]

    _panels(transparent, SCALE, colour_of, 0.42)
    app.world_labels.append(WorldLabel(
        np.array([0.0, 0.0, SCALE + 1.4]),
        "THE SKELETON NEVER CHANGES", (240, 247, 252)))


def scene_hype_swap(app, opaque, transparent, p: float) -> None:
    """One panel leaves, a different one arrives."""
    _frame(opaque, SCALE, MUTED, 0.06)
    faces = list(GEOMETRY.hemisphere_faces)
    swapping = {3, 11, 19, 27, 33}
    _panels(transparent, SCALE, lambda i: CYAN, 0.22,
            subset=set(range(len(faces))) - swapping)
    lift = ease_in_out(clamp(p * 1.5))
    for order, index in enumerate(sorted(swapping)):
        corners = GEOMETRY.vertices[[int(v) for v in faces[index]]] * SCALE
        out = normalize(corners.mean(axis=0)) * (3.4 * lift)
        phase = (lift + order * 0.17) % 1.0
        colour = PALETTE[order % len(PALETTE)]
        moved = corners + out * (1.0 if order % 2 else -0.42)
        normal = normalize(moved.mean(axis=0))
        transparent.triangle(moved[0], moved[1], moved[2],
                             (colour[0], colour[1], colour[2], 0.70), normal)
        for i in range(3):
            opaque.cylinder(moved[i], moved[(i + 1) % 3], 0.05, colour, 6)
    app.world_labels.append(WorldLabel(
        np.array([0.0, 0.0, SCALE + 2.0]), "SWAP. ADD. UPGRADE.", (255, 177, 62)))


def scene_hype_absurd(app, opaque, transparent, p: float) -> None:
    """A panel for whatever gets invented later."""
    _frame(opaque, SCALE, MUTED, 0.055)
    _panels(transparent, SCALE, lambda i: CYAN, 0.14)
    face = GEOMETRY.hemisphere_faces[18]
    corners = GEOMETRY.vertices[[int(v) for v in face]] * SCALE
    out = normalize(corners.mean(axis=0))
    moved = corners + out * 2.2
    normal = normalize(moved.mean(axis=0))
    transparent.triangle(moved[0], moved[1], moved[2], (0.66, 0.48, 1.00, 0.75),
                         normal)
    hub = moved.mean(axis=0)
    for arm in range(6):
        angle = math.tau * arm / 6 + p * math.tau * 0.6
        elbow = hub + out * 0.9 + np.array([
            1.15 * math.cos(angle), 1.15 * math.sin(angle), 0.35])
        tip = elbow + np.array([
            0.85 * math.cos(angle + 1.1), 0.85 * math.sin(angle + 1.1), 0.75])
        opaque.cylinder(hub, elbow, 0.075, PURPLE, 7)
        opaque.cylinder(elbow, tip, 0.055, AMBER, 7)
        opaque.sphere(elbow, 0.11, WHITE, 4, 8)
    app.world_labels.append(WorldLabel(
        hub + out * 1.6 + np.array([0.0, 0.0, 2.0]),
        "THERE SHOULD BE A PANEL FOR THAT", (166, 128, 255)))


def scene_hype_archetypes(app, opaque, transparent, p: float) -> None:
    """Everyone the dome supposedly belongs to."""
    _cards(app, opaque, (
        ("HIPPIES", GREEN), ("BOND VILLAINS", RED),
        ("MATHEMATICIANS", CYAN), ("POLYCARBONATE OWNERS", AMBER),
    ), p, 2.6, 13.6, 1.7)
    _frame(transparent, 2.6, MUTED, 0.05)


def scene_hype_chassis(app, opaque, transparent, p: float) -> None:
    """Keep the chassis, upgrade the components."""
    opaque.box((0.0, 0.0, 2.6), (5.0, 2.2, 5.2), (0.20, 0.25, 0.33, 1.0))
    slide = ease_in_out(clamp(p * 1.4))
    for index in range(4):
        z = 0.9 + index * 1.15
        x = -3.4 - slide * 3.0 if index % 2 else 3.4 + slide * 3.0
        opaque.box((x, 0.0, z), (3.0, 1.5, 0.62), PALETTE[index % len(PALETTE)])
    app.world_labels.extend([
        WorldLabel(np.array([0.0, 0.0, 6.2]), "KEEP THE CHASSIS", (240, 247, 252)),
        WorldLabel(np.array([0.0, 0.0, -0.5]),
                   "UPGRADE THE COMPONENTS", (255, 177, 62)),
    ])


def scene_hype_badges(app, opaque, transparent, p: float) -> None:
    """The stack of things one person happens to be."""
    rows = (
        ("NAVY VETERAN", CYAN), ("PROGRAMMER", GREEN),
        ("AVIONICS TECH", AMBER), ("FABRICATOR", PURPLE),
        ("ENGINEERING STUDENT", RED),
    )
    reveal = clamp(p * 1.4)
    for index, (label, colour) in enumerate(rows):
        if index / len(rows) > reveal:
            continue
        z = 0.7 + index * 1.28
        width = 9.0 - index * 0.5
        opaque.box((0.0, 0.0, z), (width, 0.62, 1.0), colour)
        app.world_labels.append(WorldLabel(
            np.array([0.0, 0.0, z]), label, _rgb(colour)))


def scene_hype_teardown(app, opaque, transparent, p: float) -> None:
    """Everything comes apart, because everything can."""
    burst = ease_in_out(clamp(p * 1.3))
    for index, face in enumerate(GEOMETRY.hemisphere_faces):
        corners = GEOMETRY.vertices[[int(v) for v in face]] * SCALE
        out = normalize(corners.mean(axis=0)) * (burst * 4.6)
        spin = burst * math.tau * 0.4 * (1 if index % 2 else -1)
        rotation = np.array([
            [math.cos(spin), -math.sin(spin), 0.0],
            [math.sin(spin), math.cos(spin), 0.0],
            [0.0, 0.0, 1.0],
        ])
        moved = (corners - corners.mean(axis=0)) @ rotation.T + corners.mean(axis=0) + out
        colour = PALETTE[index % len(PALETTE)]
        for i in range(3):
            opaque.cylinder(moved[i], moved[(i + 1) % 3], 0.05, colour, 6)
    app.world_labels.append(WorldLabel(
        np.array([0.0, 0.0, SCALE + 3.2]), "TAKE IT APART", (255, 177, 62)))


def scene_hype_organs(app, opaque, transparent, p: float) -> None:
    """A heap of salvage, still full of working parts."""
    rng = np.random.default_rng(11)
    glow = 0.5 + 0.5 * math.sin(p * math.tau * 1.6)
    for index in range(34):
        x = float(rng.uniform(-6.4, 6.4))
        y = float(rng.uniform(-2.0, 2.0))
        z = float(rng.uniform(0.25, 2.6))
        kind = index % 4
        colour = PALETTE[index % len(PALETTE)]
        if kind == 0:
            opaque.cylinder(np.array([x, y, z]), np.array([x + 1.1, y, z]),
                            0.24, colour, 9)
        elif kind == 1:
            opaque.box((x, y, z), (0.85, 0.7, 0.7), colour)
        elif kind == 2:
            opaque.sphere(np.array([x, y, z]), 0.34, colour, 4, 9)
        else:
            opaque.cylinder(np.array([x, y, z]), np.array([x, y, z + 1.0]),
                            0.13, colour, 7)
    transparent.sphere(np.array([0.0, 0.0, 1.6]), 5.0 + glow * 0.5,
                       (0.32, 0.91, 0.58, 0.05 + 0.05 * glow), 5, 12)
    app.world_labels.append(WorldLabel(
        np.array([0.0, 0.0, 5.4]), "THE ORGANS ARE STILL GOOD", (111, 235, 155)))


def scene_hype_failure(app, opaque, transparent, p: float) -> None:
    """Cheap material makes failure affordable."""
    stage = int(clamp(p * 0.999) * 4)
    labels = ("DRILLED IT WRONG", "CUT IT SHORT", "WIRED IT BACKWARDS",
              "YOU HAVE CONDUCTED SCIENCE")
    colours = (RED, AMBER, PURPLE, GREEN)
    for index in range(4):
        x = -6.9 + index * 4.6
        colour = colours[index]
        done = index <= stage
        opaque.box((x, 0.0, 1.9), (3.1, 0.6, 3.1),
                   colour if done else (0.16, 0.20, 0.26, 1.0))
        if done and index < 3:
            for sign in (-1.0, 1.0):
                opaque.cylinder(np.array([x - 1.2 * sign, -0.4, 0.8]),
                                np.array([x + 1.2 * sign, -0.4, 3.0]),
                                0.10, (0.75, 0.16, 0.18, 1.0), 6)
        if done:
            app.world_labels.append(WorldLabel(
                np.array([x, 0.0, 3.9]), labels[index], _rgb(colour)))


def scene_hype_title(app, opaque, transparent, p: float) -> None:
    """A hard title card, built out of the dome itself."""
    burst = smoothstep(clamp(p * 1.6))
    _frame(opaque, SCALE * (0.55 + 0.45 * burst), AMBER, 0.11, burst)
    for index in range(24):
        angle = math.tau * index / 24 + p * 0.8
        reach = 6.6 + burst * 3.2
        a = np.array([reach * math.cos(angle), reach * math.sin(angle), 0.15])
        b = a + np.array([0.0, 0.0, 0.35 + burst * 1.5])
        opaque.cylinder(a, b, 0.07, RED, 6)


def scene_hype_phases(app, opaque, transparent, p: float) -> None:
    """Three phases, ascending, obviously."""
    reveal = clamp(p * 1.35)
    rows = (("PHASE ONE  BUILD FRAMES", CYAN),
            ("PHASE TWO  SPREAD THEM", AMBER),
            ("PHASE THREE  SELL UPGRADES", GREEN))
    for index, (label, colour) in enumerate(rows):
        if index / len(rows) > reveal:
            continue
        height = 2.0 + index * 1.9
        x = -5.2 + index * 5.2
        opaque.box((x, 0.0, height * 0.5), (3.6, 1.1, height), colour)
        app.world_labels.append(WorldLabel(
            np.array([x, 0.0, height + 0.8]), label, _rgb(colour)))


def scene_hype_catalog(app, opaque, transparent, p: float) -> None:
    """The tribute schedule."""
    _cards(app, opaque, (
        ("ARCTIC INSULATION", CYAN), ("GREENHOUSE PANEL", GREEN),
        ("SOLAR SHELL", AMBER), ("LUXURY WINDOW", PURPLE),
    ), p, 3.0, 13.8, 2.0)


def scene_hype_fortress(app, opaque, transparent, p: float) -> None:
    """One big dome, and a great many small ones."""
    _frame(opaque, 3.4, AMBER, 0.09)
    _panels(transparent, 3.4, lambda i: AMBER, 0.20)
    grow = ease_in_out(clamp(p * 1.2))
    rng = np.random.default_rng(5)
    for index in range(26):
        angle = math.tau * index / 26
        distance = 8.0 + (index % 4) * 2.6
        centre = np.array([distance * math.cos(angle), distance * math.sin(angle), 0.0])
        size = 0.75 * grow
        for edge in list(GEOMETRY.hemisphere_edges)[::4]:
            a, b = (GEOMETRY.vertices[i] * size + centre for i in edge)
            opaque.cylinder(a, b, 0.028, CYAN, 5)
    app.world_labels.append(WorldLabel(
        np.array([0.0, 0.0, 5.4]), "RULE THE HOBOCLASS", (255, 177, 62)))


def scene_hype_powertools(app, opaque, transparent, p: float) -> None:
    """The fatal flaw in the plan."""
    _frame(transparent, 3.0, MUTED, 0.045)
    stature = 4.4
    for offset, pose, yaw in ((-5.4, "fasten", 0.0), (0.0, "carry", 180.0),
                              (5.4, "reach_out", 20.0)):
        joints = place_figure(
            joint_positions(POSES[pose], stature), (offset, 3.2, 0.0), yaw)
        draw_figure(opaque, joints, scale=stature / 1.75)
    app.world_labels.append(WorldLabel(
        np.array([0.0, 3.2, stature + 1.3]),
        "THE HOBOCLASS OWNS POWER TOOLS", (111, 235, 155)))


def scene_hype_bolted(app, opaque, transparent, p: float) -> None:
    """A dome with whatever was lying around attached to it."""
    _frame(opaque, SCALE, AMBER, 0.07)
    _panels(transparent, SCALE, lambda i: AMBER, 0.12)
    attach = ease_in_out(clamp(p * 1.3))
    junk = (("RV WINDOW", CYAN, 6), ("HALF A SOLAR PANEL", GREEN, 14),
            ("CHICKEN COOP DOOR", PURPLE, 22),
            ("HIGHWAY MYSTERY OBJECT", RED, 30))
    for order, (label, colour, face_index) in enumerate(junk):
        if order / len(junk) > attach:
            continue
        face = GEOMETRY.hemisphere_faces[face_index % len(GEOMETRY.hemisphere_faces)]
        corners = GEOMETRY.vertices[[int(v) for v in face]] * SCALE
        centre = corners.mean(axis=0)
        out = normalize(centre)
        opaque.box(tuple(centre + out * 0.45),
                   (1.5 + order * 0.2, 1.2, 0.35), colour)
        app.world_labels.append(WorldLabel(
            centre + out * 1.9, label, _rgb(colour)))


def scene_hype_becomes(app, opaque, transparent, p: float) -> None:
    """One frame, many buildings."""
    names = ("A HOUSE", "A WORKSHOP", "A GREENHOUSE", "A CABIN",
             "A SHELTER", "A POWER STATION", "A RESEARCH LAB")
    index = int(clamp(p * 0.999) * len(names))
    colour = PALETTE[index % len(PALETTE)]
    _frame(opaque, SCALE, colour, 0.085)
    _panels(transparent, SCALE, lambda i: colour, 0.26)
    app.world_labels.append(WorldLabel(
        np.array([0.0, 0.0, SCALE + 1.5]), names[index], _rgb(colour)))


def scene_hype_tools(app, opaque, transparent, p: float) -> None:
    """The entire required tool list."""
    _cards(app, opaque, (
        ("A CIRCULAR SAW", CYAN), ("A DRILL", AMBER),
        ("RECLAIMED LUMBER", GREEN), ("QUESTIONABLE CONFIDENCE", PURPLE),
    ), p, 2.4, 13.6, 1.6)


def scene_hype_forwho(app, opaque, transparent, p: float) -> None:
    """Who it is actually for."""
    names = ("NORMAL PEOPLE", "DIY BUILDERS", "HOMESTEADERS", "PROGRAMMERS",
             "FABRICATORS", "TINKERERS", "PEOPLE LEARNING AS THEY GO")
    reveal = clamp(p * 1.3)
    for index, label in enumerate(names):
        if index / len(names) > reveal:
            continue
        row, column = divmod(index, 4)
        x = -7.2 + column * 4.8
        z = 4.0 - row * 2.1
        colour = PALETTE[index % len(PALETTE)]
        opaque.box((x, 0.0, z), (4.0, 0.5, 1.2), colour)
        app.world_labels.append(WorldLabel(
            np.array([x, 0.0, z]), label, _rgb(colour)))


def scene_hype_socials(app, opaque, transparent, p: float) -> None:
    """Where the experiments live."""
    _frame(opaque, 3.2, CYAN, 0.07, smoothstep(clamp(p * 1.8)))
    # Above the dome, in one clean band: these are the only words in the
    # whole montage a viewer might want to write down.
    reveal = clamp(p * 1.5)
    handles = (("@DonovanZeanah", CYAN), ("facebook.com/zeanah", PURPLE),
               ("@shortcircuiter", AMBER), ("zeanahlab.com", GREEN))
    for index, (label, colour) in enumerate(handles):
        if index / len(handles) > reveal:
            continue
        x = -7.8 + index * 5.2
        opaque.box((x, 0.0, 6.4), (4.3, 0.45, 0.95), colour)
        app.world_labels.append(WorldLabel(
            np.array([x, 0.0, 6.4]), label, _rgb(colour)))


# ----------------------------------------------------------------------
# The call to action
# ----------------------------------------------------------------------

def scene_hype_asymmetry(app, opaque, transparent, p: float) -> None:
    """What is on each side of this, drawn to scale."""
    grow = ease_in_out(clamp(p * 1.2))
    # Their side: a stack that keeps going past the top of the frame.
    for index in range(18):
        height = 0.42
        z = 0.3 + index * height * 1.06
        if index / 18 > grow:
            break
        opaque.box((-5.6, 0.0, z), (4.4, 2.0, height), (0.24, 0.30, 0.38, 1.0))
    # My side: one prototype and a chainsaw.
    _frame(opaque, 1.55, AMBER, 0.05, grow)
    opaque.box((5.4, 0.0, 0.42), (2.3, 0.55, 0.42), (0.62, 0.16, 0.14, 1.0))
    opaque.cylinder(np.array([4.5, 0.0, 0.42]), np.array([6.9, 0.0, 0.42]),
                    0.10, MUTED, 8)
    app.world_labels.extend([
        WorldLabel(np.array([-5.6, 0.0, 9.2]),
                   "INSTITUTIONAL CAPITAL", (169, 188, 203)),
        WorldLabel(np.array([5.4, 0.0, 3.0]),
                   "ONE PROTOTYPE\nAND A CHEAP CHAINSAW", (255, 177, 62)),
        WorldLabel(np.array([0.0, 0.0, -1.2]),
                   "this is the actual balance of forces", (111, 235, 155)),
    ])


def scene_hype_friend(app, opaque, transparent, p: float) -> None:
    """One person, one dome. The quietest shot in the film."""
    _frame(opaque, 3.4, CYAN, 0.06, smoothstep(clamp(p * 1.6)))
    _panels(transparent, 3.4, lambda i: CYAN, 0.10)
    stature = 3.9
    joints = place_figure(
        joint_positions(POSES["stand"], stature), (5.6, 0.0, 0.0), 200.0)
    draw_figure(opaque, joints, scale=stature / 1.75)
    app.world_labels.append(WorldLabel(
        np.array([5.6, 0.0, stature + 0.9]),
        "SOMEBODY YOU KNOW", (169, 188, 203)))


def scene_hype_share(app, opaque, transparent, p: float) -> None:
    """One dome becomes many, outward, fast."""
    spread = ease_in_out(clamp(p * 1.25))
    _frame(opaque, 2.2, AMBER, 0.07)
    for index in range(20):
        angle = math.tau * index / 20
        distance = 4.0 + spread * (7.0 + (index % 3) * 2.4)
        centre = np.array([distance * math.cos(angle),
                           distance * math.sin(angle), 0.0])
        size = 0.95 * spread
        for edge in list(GEOMETRY.hemisphere_edges)[::5]:
            a, b = (GEOMETRY.vertices[i] * size + centre for i in edge)
            opaque.cylinder(a, b, 0.03, CYAN, 5)
        if spread > 0.25:
            opaque.arrow(np.array([2.6 * math.cos(angle), 2.6 * math.sin(angle), 0.9]),
                         centre + np.array([0.0, 0.0, 0.9]), 0.028, GREEN)
    app.world_labels.append(WorldLabel(
        np.array([0.0, 0.0, 4.6]), "SEND IT TO ONE PERSON", (111, 235, 155)))


def scene_hype_audiences(app, opaque, transparent, p: float) -> None:
    """Anyone with reach. The list is deliberately unfussy."""
    names = ("HOMESTEADERS", "BUILDERS", "DEVELOPERS", "MAKERS",
             "CREATORS", "ANYONE WITH AN AUDIENCE")
    reveal = clamp(p * 1.3)
    for index, label in enumerate(names):
        if index / len(names) > reveal:
            continue
        row, column = divmod(index, 3)
        x = -6.2 + column * 6.2
        z = 4.2 - row * 2.3
        colour = PALETTE[index % len(PALETTE)]
        opaque.box((x, 0.0, z), (5.2, 0.5, 1.3), colour)
        app.world_labels.append(WorldLabel(
            np.array([x, 0.0, z]), label, _rgb(colour)))
    app.world_labels.append(WorldLabel(
        np.array([0.0, 0.0, -0.9]),
        "I genuinely do not care what your audience is about",
        (169, 188, 203)))


def scene_hype_needs(app, opaque, transparent, p: float) -> None:
    """What the money actually turns into."""
    reveal = clamp(p * 1.3)
    kit = (("A CNC ROUTER", CYAN), ("A LASER CUTTER", RED),
           ("CAMERAS", AMBER), ("POWER AND SPACE", GREEN))
    span = 13.2
    step = span / (len(kit) - 1)
    for index, (label, colour) in enumerate(kit):
        if index / len(kit) > reveal:
            continue
        x = -span * 0.5 + index * step
        opaque.box((x, 0.0, 2.0), (2.9, 1.4, 2.4), colour)
        if label == "A LASER CUTTER":
            opaque.cylinder(np.array([x, 0.0, 3.2]), np.array([x, 0.0, 6.4]),
                            0.07, RED, 6)
        app.world_labels.append(WorldLabel(
            np.array([x, 0.0, 3.8]), label, _rgb(colour)))
    app.world_labels.append(WorldLabel(
        np.array([0.0, 0.0, -0.9]),
        "not a salary. tooling. it turns straight back into parts.",
        (111, 235, 155)))


def scene_hype_number(app, opaque, transparent, p: float) -> None:
    """The ask, against what the internet moves without blinking."""
    grow = ease_in_out(clamp(p * 1.2))
    opaque.box((-4.6, 0.0, 0.55 * grow + 0.1), (3.4, 1.6, max(0.05, 1.1 * grow)),
               AMBER)
    for index in range(16):
        if index / 16 > grow:
            break
        opaque.box((4.6, 0.0, 0.3 + index * 0.46), (3.4, 1.6, 0.42),
                   (0.24, 0.30, 0.38, 1.0))
    app.world_labels.extend([
        WorldLabel(np.array([-4.6, 0.0, 2.6]), "WHAT I NEED", (255, 177, 62)),
        WorldLabel(np.array([4.6, 0.0, 8.4]),
                   "WHAT THE INTERNET MOVES\nWITHOUT THINKING ABOUT IT",
                   (169, 188, 203)),
        WorldLabel(np.array([0.0, 0.0, -1.1]),
                   "I am not going to beg for it and I am not going to dance for it",
                   (111, 235, 155)),
    ])


def scene_hype_hr(app, opaque, transparent, p: float) -> None:
    """The strategy, stated with total transparency."""
    slide = ease_in_out(clamp((p - 0.15) / 0.7))
    # A projection that was going up and then very much was not.
    points = []
    for index in range(14):
        t = index / 13.0
        x = -7.0 + t * 14.0
        z = 1.2 + t * 3.4 if t < 0.55 else 1.2 + 0.55 * 3.4 - (t - 0.55) * 7.0 * slide
        points.append(np.array([x, 0.0, max(0.2, z)]))
    for index in range(len(points) - 1):
        colour = GREEN if index < 7 else RED
        opaque.cylinder(points[index], points[index + 1], 0.10, colour, 8)
    app.world_labels.extend([
        WorldLabel(np.array([-4.6, 0.0, 4.4]),
                   "PROJECTED RENTAL YIELD", (111, 235, 155)),
        WorldLabel(np.array([5.2, 0.0, 2.2]),
                   "SEVENTH HOLIDAY OF THE YEAR,\nSUDDENLY REGRETTED",
                   (255, 87, 94)),
        WorldLabel(np.array([0.0, 0.0, -1.1]),
                   "a completely transparent and only slightly relatable strategy",
                   (169, 188, 203)),
    ])


def scene_hype_teslabot(app, opaque, transparent, p: float) -> None:
    """A request, addressed upward, with a dome for context."""
    _frame(opaque, 3.0, CYAN, 0.06, smoothstep(clamp(p * 1.7)))
    stature = 4.0
    # The applicant.
    joints = place_figure(
        joint_positions(POSES["reach_high"], stature), (-4.6, 0.0, 0.0), 210.0)
    draw_figure(opaque, joints, scale=stature / 1.75)
    # The requested colleague: same skeleton, rendered in metal, with a
    # second pair of arms because that is the entire point of asking.
    arrive = ease_in_out(clamp((p - 0.25) / 0.65))
    if arrive > 0.02:
        bot = place_figure(
            joint_positions(POSES["carry"], stature * 1.05),
            (5.0, 0.0, 0.0), 200.0)
        draw_figure(opaque, bot, scale=stature / 1.75,
                    skin=(0.62, 0.68, 0.76, 1.0),
                    hi_vis=(0.44, 0.50, 0.60, 1.0),
                    trousers=(0.28, 0.32, 0.40, 1.0),
                    helmet=(0.35, 0.85, 0.95, 1.0))
        shoulder = bot["chest"]
        for side in (-1.0, 1.0):
            elbow = shoulder + np.array([side * 1.15 * arrive, 0.0, -0.35])
            wrist = elbow + np.array([side * 0.95 * arrive, 0.0, 0.55])
            opaque.cylinder(shoulder, elbow, 0.11, (0.55, 0.60, 0.70, 1.0), 8)
            opaque.cylinder(elbow, wrist, 0.085, (0.55, 0.60, 0.70, 1.0), 8)
            opaque.sphere(elbow, 0.13, CYAN, 4, 8)
        app.world_labels.append(WorldLabel(
            np.array([5.0, 0.0, stature + 1.1]),
            "ONE (1) TESLABOT", (61, 211, 255)))
    app.world_labels.extend([
        WorldLabel(np.array([-4.6, 0.0, stature + 1.4]),
                   "ME, LYING ABOUT ENJOYING WIRING", (255, 177, 62)),
        WorldLabel(np.array([0.0, 0.0, -1.1]),
                   "for humanity, and related considerations",
                   (169, 188, 203)),
    ])


def scene_hype_psyche(app, opaque, transparent, p: float) -> None:
    """The actual list of likes, stated without further decoration."""
    grow = ease_in_out(clamp(p * 1.25))
    rows = (("CASH MONEY", AMBER), ("RESOURCES", GREEN),
            ("POWER", RED), ("INFLUENCE", PURPLE))
    span = 12.6
    step = span / (len(rows) - 1)
    for index, (label, colour) in enumerate(rows):
        x = -span * 0.5 + index * step
        height = (2.6 + index * 1.15) * grow
        opaque.box((x, 0.0, height * 0.5 + 0.15), (2.4, 1.2, max(0.06, height)),
                   colour)
        app.world_labels.append(WorldLabel(
            np.array([x, 0.0, height + 0.85]), label, _rgb(colour)))
    _frame(transparent, 1.5, MUTED, 0.04)
    app.world_labels.append(WorldLabel(
        np.array([0.0, 0.0, -1.2]),
        "method: ruling hobos. forcibly. sue me.", (169, 188, 203)))


SCENES = {
    "hype_bones": scene_hype_bones,
    "hype_platform": scene_hype_platform,
    "hype_swap": scene_hype_swap,
    "hype_absurd": scene_hype_absurd,
    "hype_archetypes": scene_hype_archetypes,
    "hype_chassis": scene_hype_chassis,
    "hype_badges": scene_hype_badges,
    "hype_teardown": scene_hype_teardown,
    "hype_organs": scene_hype_organs,
    "hype_failure": scene_hype_failure,
    "hype_title": scene_hype_title,
    "hype_phases": scene_hype_phases,
    "hype_catalog": scene_hype_catalog,
    "hype_fortress": scene_hype_fortress,
    "hype_powertools": scene_hype_powertools,
    "hype_bolted": scene_hype_bolted,
    "hype_becomes": scene_hype_becomes,
    "hype_tools": scene_hype_tools,
    "hype_forwho": scene_hype_forwho,
    "hype_asymmetry": scene_hype_asymmetry,
    "hype_friend": scene_hype_friend,
    "hype_share": scene_hype_share,
    "hype_audiences": scene_hype_audiences,
    "hype_needs": scene_hype_needs,
    "hype_number": scene_hype_number,
    "hype_hr": scene_hype_hr,
    "hype_teslabot": scene_hype_teslabot,
    "hype_psyche": scene_hype_psyche,
    "hype_socials": scene_hype_socials,
}


CHAPTERS: tuple[Chapter, ...] = (
    Chapter(
        "platform", "01", "The question",
        "What if a house was not a finished product?",
        (
            "What if a house was not really a finished product? What if it was a",
            "platform?",
        ),
        (), 4.0, (30.0, 22.0, 15.0), "hype_bones",
    ),
    Chapter(
        "bones", "02", "Build once",
        "Build the skeleton once. Keep the bones.",
        (
            "Build the geodesic skeleton once. Keep the bones.",
        ),
        (), 4.0, (52.0, 30.0, 13.5), "hype_bones",
    ),
    Chapter(
        "mutate", "03", "Then everything else",
        "Then replace, repair, upgrade, mutate, Frankenstein.",
        (
            "Then replace, repair, upgrade, mutate, Frankenstein, and occasionally bolt",
            "questionable things onto everything else for the next fifty years.",
        ),
        (), 4.0, (74.0, 20.0, 15.5), "hype_platform",
    ),
    Chapter(
        "swap", "04", "Every answer is yes",
        "New insulation? Swap it. Solar panels? Add them.",
        (
            "New insulation? Swap it. Solar panels? Add them. Greenhouse wall? Sure.",
            "Workshop extension? Absolutely.",
        ),
        (), 4.0, (18.0, 26.0, 17.0), "hype_swap",
    ),
    Chapter(
        "absurd", "05", "And whatever comes next",
        "There should be a panel for that.",
        (
            "Technology invented in twenty forty-seven by a child with six robotic arms?",
            "There should be a panel for that.",
        ),
        (), 4.0, (44.0, 18.0, 16.0), "hype_absurd",
    ),
    Chapter(
        "archetypes", "06", "Not just for them",
        "Not just a weird round house for hippies and Bond villains.",
        (
            "That is what fascinates me about geodesic construction. The dome is not just",
            "a weird round house for hippies, Bond villains, mathematicians, and people",
            "who own suspicious amounts of polycarbonate.",
        ),
        (), 4.0, (90.0, 14.0, 16.5), "hype_archetypes",
    ),
    Chapter(
        "chassis", "07", "A different paradigm",
        "Keep the chassis. Upgrade the components.",
        (
            "It could be an entirely different building paradigm. Think PC building.",
            "Keep the chassis. Upgrade the components. And apparently I have decided",
            "this is now my problem to investigate.",
        ),
        (), 4.0, (88.0, 12.0, 16.0), "hype_chassis",
    ),
    Chapter(
        "whoami", "08", "Who is behind this",
        "For anyone wondering who is behind all these triangles.",
        (
            "For anyone wondering who is behind this increasingly unreasonable quantity",
            "of triangles: I am a Navy veteran, programmer, agentic engineer, and a",
            "trade-school and F.A.A. accredited avionics bench technician. I am now using",
            "my G.I. Bill to pursue aerospace engineering.",
        ),
        (), 4.0, (90.0, 16.0, 15.0), "hype_badges",
    ),
    Chapter(
        "combination", "09", "A stable combination",
        "A perfectly stable combination.",
        (
            "Programmer, plus electronics technician, plus fabricator, plus engineering",
            "student, plus scavenger, plus Alabama hobo-redneck, plus aspiring science",
            "madman. A perfectly stable combination.",
        ),
        (), 4.0, (90.0, 20.0, 14.0), "hype_badges",
    ),
    Chapter(
        "teardown", "10", "The list of likes",
        "I like taking things apart.",
        (
            "I like programming things. I like wiring things. I like woodworking and",
            "metalworking. I like taking things apart.",
        ),
        (), 4.0, (36.0, 24.0, 19.0), "hype_teardown",
    ),
    Chapter(
        "organs", "11", "The organs are still good",
        "Excellent. The organs are still good.",
        (
            "I like finding machinery somebody threw away and immediately thinking:",
            "excellent, the organs are still good.",
        ),
        (), 4.0, (86.0, 18.0, 15.0), "hype_organs",
    ),
    Chapter(
        "supervillain", "12", "Give me the scrap",
        "I become the world's poorest supervillain.",
        (
            "Give me discarded motors, bearings, sheet metal, wiring harnesses, switches,",
            "sensors, lumber, gears and random military surplus hardware, and I become",
            "the world's poorest supervillain.",
        ),
        (), 4.0, (100.0, 22.0, 16.0), "hype_organs",
    ),
    Chapter(
        "affordable", "13", "Why salvage",
        "When the material is already garbage, failure becomes affordable.",
        (
            "That mentality is a huge part of Frankendome. When the material is cheap,",
            "salvaged, or already considered garbage, failure becomes affordable.",
        ),
        (), 4.0, (90.0, 14.0, 17.0), "hype_failure",
    ),
    Chapter(
        "mistakes", "14", "The catalogue of errors",
        "Drill the wrong hole? I do it often.",
        (
            "Drill the wrong hole? I do it often. Cut something too short? Again?",
            "Excellent. Wire it incorrectly? Educational.",
        ),
        (), 4.0, (90.0, 14.0, 17.0), "hype_failure",
    ),
    Chapter(
        "science", "15", "Congratulations",
        "Congratulations. You have conducted science.",
        (
            "Discover your revolutionary invention is actually a terrible idea?",
            "Congratulations. You have conducted science. Nobody has to hold a funeral",
            "for the four hundred dollar precision component you just murdered.",
        ),
        (), 4.0, (90.0, 14.0, 17.0), "hype_failure",
    ),
    Chapter(
        "trapped", "16", "You stop seeing junk",
        "Components temporarily trapped inside the wrong machine.",
        (
            "This is why I love prototyping from reclaimed materials. Eventually you stop",
            "seeing junk. You see components temporarily trapped inside the wrong",
            "machine. As a kid I loved Operation Junkyard. In hindsight, I was clearly",
            "receiving vocational training.",
        ),
        (), 4.0, (70.0, 20.0, 16.0), "hype_organs",
    ),
    Chapter(
        "empire", "17", "The business plan",
        "THE EVIL DOME EMPIRE",
        (
            "Which naturally brings us to my completely reasonable long-term business",
            "plan. The Evil Dome Empire.",
        ),
        (), 4.0, (26.0, 24.0, 18.0), "hype_title",
    ),
    Chapter(
        "phases", "18", "Three phases",
        "Spread them across civilization like structurally efficient triangles.",
        (
            "Phase one: build geodesic frames. Phase two: spread them across",
            "civilization like a plague of structurally efficient triangles. Phase three:",
            "become filthy rich selling upgrades.",
        ),
        (), 4.0, (90.0, 16.0, 16.0), "hype_phases",
    ),
    Chapter(
        "tribute", "19", "The tribute schedule",
        "Your tribute has been accepted.",
        (
            "Need the Imperial Arctic Insulation Package? That will cost you. Fancy",
            "greenhouse panels? Money, please. Solar integrated exterior shell? Straight",
            "into the treasury. Luxury window module? Your tribute has been accepted.",
        ),
        (), 4.0, (90.0, 15.0, 16.5), "hype_catalog",
    ),
    Chapter(
        "printer", "20", "The model",
        "Printers and ink cartridges, except the printer is your house.",
        (
            "My business model will basically be printers and ink cartridges, except the",
            "printer is your house.",
        ),
        (), 4.0, (88.0, 12.0, 16.0), "hype_chassis",
    ),
    Chapter(
        "fortress", "21", "The fortress",
        "Rule benevolently, but firmly, over the Hoboclass.",
        (
            "Eventually I shall sit inside an enormous spherical fortress overlooking",
            "thousands of domes, and rule benevolently, but firmly, over the Hoboclass.",
        ),
        (), 4.0, (40.0, 26.0, 26.0), "hype_fortress",
    ),
    Chapter(
        "weakness", "22", "One catastrophic weakness",
        "The Hoboclass owns power tools.",
        (
            "Unfortunately, my flawless evil genius strategy has one catastrophic",
            "weakness. The Hoboclass owns power tools.",
        ),
        (), 4.0, (86.0, 14.0, 17.0), "hype_powertools",
    ),
    Chapter(
        "module", "23", "Twelve seconds",
        "Brother, that is plywood, insulation and sheet metal.",
        (
            "I will unveil a magnificent four thousand dollar Imperial Replacement Wall",
            "Module, and somebody will stare at it for twelve seconds and say: brother,",
            "that is plywood, insulation and sheet metal.",
        ),
        (), 4.0, (90.0, 15.0, 16.5), "hype_catalog",
    ),
    Chapter(
        "threehours", "24", "Three hours later",
        "A chicken coop door and something they found beside the highway.",
        (
            "Three hours later their dome has a salvaged R.V. window, half a solar panel,",
            "two Harbor Freight brackets, a door from a chicken coop, and something they",
            "found beside the highway attached to it.",
        ),
        (), 4.0, (58.0, 20.0, 18.0), "hype_bolted",
    ),
    Chapter(
        "destroyed", "25", "The result",
        "My monopoly: destroyed. My customer: self-sufficient.",
        (
            "My monopoly: destroyed. My empire: humiliated. My customer: now completely",
            "self-sufficient. And standing proudly before me will be the natural predator",
            "of proprietary modular architecture.",
        ),
        (), 4.0, (110.0, 22.0, 18.0), "hype_bolted",
    ),
    Chapter(
        "frankendome", "26", "The predator",
        "FRANKENDOME",
        (
            "Frankendome.",
        ),
        (), 4.0, (14.0, 26.0, 18.0), "hype_title",
    ),
    Chapter(
        "serious", "27", "Now the serious part",
        "Everything up to here was a joke. This part is not.",
        (
            "Alright. Everything up to this point was a bit. This part is not, so I am",
            "going to drop the voice and just say it.",
        ),
        (), 4.0, (40.0, 22.0, 16.0), "hype_bones",
    ),
    Chapter(
        "asymmetry", "28", "The actual balance of forces",
        "They have trillions. I have a prototype and a cheap chainsaw.",
        (
            "Institutional capital is buying single family housing at a scale that is",
            "genuinely difficult to picture. They have trillions of dollars and entire",
            "departments. I have the leftover remains of one prototype and the cheapest",
            "chainsaw in the store. I am not pretending that is a fair fight. I am",
            "telling you that is the actual balance of forces, and I am doing it anyway.",
        ),
        (), 4.0, (90.0, 18.0, 22.0), "hype_asymmetry",
    ),
    Chapter(
        "friend", "29", "You already know somebody",
        "You know somebody who is never going to afford a house.",
        (
            "And here is the thing I actually want you to sit with. You know somebody who",
            "is never going to afford a house. Not because they are lazy and not because",
            "they did anything wrong. Because the arithmetic stopped working. You know",
            "exactly who they are. You thought of them just now.",
        ),
        (), 4.0, (44.0, 16.0, 17.0), "hype_friend",
    ),
    Chapter(
        "share", "30", "So do the one thing",
        "Send this to one person who can carry it further than I can.",
        (
            "So here is the ask, and it is small. Send this to one person who can carry it",
            "further than I can. That is it. That is the whole request. One share from",
            "somebody with reach does more for this than a month of me in a field with a",
            "chainsaw.",
        ),
        (), 4.0, (36.0, 26.0, 22.0), "hype_share",
    ),
    Chapter(
        "audiences", "31", "I do not care what your audience is",
        "Homesteaders, builders, developers, makers. Anyone with reach.",
        (
            "Homesteading channels. Construction channels. Developers. Makers. Preppers.",
            "Crowdfunding people. Creators of every description, and I do mean every",
            "description, because reach is reach and I am not in a position to be picky.",
            "If you have an audience and you think this is worth looking at, that is",
            "already more infrastructure than I have.",
        ),
        (), 4.0, (90.0, 16.0, 20.0), "hype_audiences",
    ),
    Chapter(
        "needs", "32", "What it turns into",
        "A CNC. A laser cutter. Cameras. Power.",
        (
            "And if it reaches somebody who wants to put weight behind it, here is what it",
            "turns into. A C.N.C. router. A laser cutter. Frickin' laser beams, said in the",
            "correct voice. Cameras, so the documentation stops being the bottleneck.",
            "Power and space to run all of it. None of that is a salary. Every bit of it",
            "turns straight back into parts and into footage of parts.",
        ),
        (), 4.0, (90.0, 16.0, 20.0), "hype_needs",
    ),
    Chapter(
        "number", "33", "The number",
        "Fifty thousand. The internet moves that on a slow afternoon.",
        (
            "The number is fifty thousand dollars. I am aware of how that sounds. I am",
            "also aware that the internet has collectively moved far larger sums than that",
            "for causes with considerably less to show for themselves, on a slow",
            "afternoon, without anybody thinking especially hard about it. I am not going",
            "to beg for it and I am not going to dance for it. I am going to keep building",
            "either way. It would simply happen faster with tooling.",
        ),
        (), 4.0, (90.0, 18.0, 20.0), "hype_number",
    ),
    Chapter(
        "hr", "34", "The strategy, stated plainly",
        "I want a rental portfolio's projections to take a very bad turn.",
        (
            "And I will be completely transparent about the endgame. Somewhere there is a",
            "man on his seventh holiday of the year, watching the projected yield on a",
            "portfolio of rental houses, and I would like that line to do something",
            "sudden and downward on account of this. That is the strategy. It is entirely",
            "transparent and only slightly relatable, and I have made my peace with it.",
        ),
        (), 4.0, (90.0, 16.0, 20.0), "hype_hr",
    ),
    Chapter(
        "thepoint", "35", "And honestly",
        "That is the point.",
        (
            "And honestly? That is the point. I do not just want to build domes. I want",
            "to document the geometry, fabrication, structural concepts, energy systems,",
            "modular panels, failures, experiments, software, electronics and weird",
            "prototypes well enough that somebody else can take the idea and run",
            "somewhere I never would have thought to go.",
        ),
        (), 4.0, (66.0, 22.0, 16.0), "hype_platform",
    ),
    Chapter(
        "becomes", "36", "What it could become",
        "A house. A workshop. A greenhouse. A shelter.",
        (
            "A dome could become a house. A workshop. A greenhouse. A cabin. A disaster",
            "shelter. An off-grid power station. A tiny home. A modular research lab. A",
            "timber frame monster made from trees you milled yourself, because apparently",
            "buying lumber normally was not entertaining enough.",
        ),
        (), 4.0, (34.0, 24.0, 16.0), "hype_becomes",
    ),
    Chapter(
        "shop", "37", "What you actually need",
        "You should not need a hundred thousand dollar shop.",
        (
            "And you should not need a hundred thousand dollar shop to experiment. Maybe",
            "you have a circular saw. A drill. Some reclaimed lumber. YouTube.",
            "Questionable confidence.",
        ),
        (), 4.0, (90.0, 14.0, 16.5), "hype_tools",
    ),
    Chapter(
        "instrument", "38", "The most important instrument",
        "I wonder if this will work.",
        (
            "And the most important engineering instrument ever created: I wonder if this",
            "will work.",
        ),
        (), 4.0, (90.0, 16.0, 15.0), "hype_tools",
    ),
    Chapter(
        "forwho", "39", "Who it is for",
        "People whose workshop looks like a tornado hit Lowe's.",
        (
            "That is who I want this project to be for. Normal people. D.I.Y. builders.",
            "Homesteaders. Programmers. Fabricators. Tinkerers. People learning as they",
            "go. People whose workshop looks like a tornado hit Lowe's. People who look",
            "at a pile of scrap and accidentally start designing infrastructure.",
        ),
        (), 4.0, (90.0, 16.0, 17.5), "hype_forwho",
    ),
    Chapter(
        "howcheap", "40", "The question to answer",
        "How cheap, modular, repairable and adaptable can this get?",
        (
            "I want to find out how cheap, modular, repairable, scalable and adaptable",
            "geodesic construction can actually become.",
        ),
        (), 4.0, (50.0, 22.0, 16.0), "hype_becomes",
    ),
    Chapter(
        "woods", "41", "If nobody is interested",
        "We will build weird triangular houses in the woods until somebody notices.",
        (
            "If conventional construction has no interest in any of this, that is okay.",
            "We will build weird triangular houses in the woods until somebody notices.",
        ),
        (), 4.0, (30.0, 24.0, 26.0), "hype_fortress",
    ),
    Chapter(
        "mission", "42", "The mission",
        "Accidentally teach the Hoboclass to manufacture everything themselves.",
        (
            "The mission remains simple. Spread geodesic domes throughout civilization",
            "like a highly efficient modular plague. Establish the Evil Dome Empire. Rule",
            "the Hoboclass. Accidentally teach the Hoboclass how to manufacture all my",
            "products themselves. Destroy my own recurring revenue model. Continue",
            "anyway.",
        ),
        (), 4.0, (90.0, 16.0, 16.0), "hype_phases",
    ),
    Chapter(
        "wins", "43", "Because in the end",
        "FRANKENDOME ALWAYS WINS.",
        (
            "Because in the end: Frankendome always wins.",
        ),
        (), 4.0, (8.0, 28.0, 18.0), "hype_title",
    ),
    Chapter(
        "follow", "44", "Follow the experiments",
        "Follow the experiments.",
        (
            "Follow the experiments. Instagram, Donovan Zeanah. Facebook dot com slash",
            "zeanah. TikTok, short circuiter. And zeanah lab dot com.",
        ),
        (), 4.0, (90.0, 18.0, 16.0), "hype_socials",
    ),
)


HYPE_LESSON = Lesson(
    key="hype",
    brand="FRANKENDOME",
    title="Frankendome",
    chapters=CHAPTERS,
    scenes=SCENES,
    snapshot_prefix="hype",
    style="hype",
    # A montage wants to move: a little quicker than the masterclasses,
    # which sit at -3% so the geometry has room to land.
    voice_rate="+7%",
)


# ----------------------------------------------------------------------
# Version two: the same film with the asides spliced in
# ----------------------------------------------------------------------

# The "list of likes" beat, opened out into five. The asides are verbatim
# and are meant to be delivered flat, which is why they get their own
# beats rather than being crammed into one breath.
LIKES_RUN: tuple[Chapter, ...] = (
    Chapter(
        "likes", "00", "The list of likes",
        "I like programming things. I like wiring things.",
        (
            "Like I said. A definitive and unquestionable stable combination of",
            "qualities. I like programming things. I like wiring things.",
        ),
        (), 4.0, (36.0, 24.0, 19.0), "hype_teardown",
    ),
    Chapter(
        "teslabot", "00", "Correction",
        "No I don't. I lied.",
        (
            "No I don't, I lied. But alas, there I am, doing it. That's why you all",
            "should share this video, so Elon Musk sees it. Tell him the homie needs a",
            "Teslabot, ASAP Rocky. For humanity and shit. No lie, no cap.",
        ),
        (), 4.0, (48.0, 18.0, 20.0), "hype_teslabot",
    ),
    Chapter(
        "whippersnapper", "00", "And then, crucially",
        "Then aggressively accuse him of being a whippersnapper.",
        (
            "Then aggressively accuse him of being a whippersnapper, followed",
            "immediately by asking him not to be one. For comedic effect, and for true",
            "cementation. Hypnotisation.",
        ),
        (), 4.0, (62.0, 20.0, 18.0), "hype_teslabot",
    ),
    Chapter(
        "wood", "00", "Back to the list",
        "I like woodworking and metalworking.",
        (
            "I like woodworking and metalworking.",
        ),
        (), 4.0, (30.0, 22.0, 18.0), "hype_teardown",
    ),
    Chapter(
        "psyche", "00", "Psyche",
        "Cash money. Resources, power, and influence.",
        (
            "Psyche. Cash money. Resources, power, and influence. That is what I like.",
            "How will I get it? Forcibly ruling hobos. Sue me. Tricking them into having",
            "a good time. Jesus Christ, the darkness here. You cannot fathom it. I",
            "promise, don't try.",
        ),
        (), 4.0, (90.0, 16.0, 20.0), "hype_psyche",
    ),
    Chapter(
        "apart", "00", "And the real one",
        "I like taking things apart.",
        (
            "I like taking things apart.",
        ),
        (), 4.0, (40.0, 26.0, 20.0), "hype_teardown",
    ),
)


def _splice(chapters: tuple[Chapter, ...], slug: str,
            replacement: tuple[Chapter, ...]) -> tuple[Chapter, ...]:
    """Swap one beat for a run of beats, then renumber the whole film."""
    out: list[Chapter] = []
    for chapter in chapters:
        if chapter.slug == slug:
            out.extend(replacement)
        else:
            out.append(chapter)
    return tuple(
        replace(chapter, number=f"{index + 1:02d}")
        for index, chapter in enumerate(out)
    )


CHAPTERS_V2 = _splice(CHAPTERS, "teardown", LIKES_RUN)


HYPE_V2_LESSON = Lesson(
    key="hype2",
    brand="FRANKENDOME",
    title="Frankendome, Version Two",
    chapters=CHAPTERS_V2,
    scenes=SCENES,
    snapshot_prefix="hype2",
    style="hype",
    voice_rate="+7%",
)


# ----------------------------------------------------------------------
# Version three: v2, plus the reason, and with the labels decluttered
# ----------------------------------------------------------------------

def scene_hype_mother(app, opaque, transparent, p: float) -> None:
    """One parent, one child, one shelter. Nothing else in frame."""
    _frame(opaque, 3.2, CYAN, 0.065, smoothstep(clamp(p * 1.5)))
    _panels(transparent, 3.2, lambda i: CYAN, 0.12)
    adult = 3.8
    child = 2.3
    for stature, offset, yaw in ((adult, -5.6, 205.0), (child, -3.9, 205.0)):
        joints = place_figure(
            joint_positions(POSES["stand"], stature), (offset, 0.6, 0.0), yaw)
        draw_figure(opaque, joints, scale=stature / 1.75)
    app.world_labels.append(WorldLabel(
        np.array([-4.7, 0.6, adult + 1.2]),
        "THE POINT OF ALL OF IT", (111, 235, 155)))


def scene_hype_igloo(app, opaque, transparent, p: float) -> None:
    """The proof that shipped several thousand years ago."""
    build = ease_in_out(clamp(p * 1.2))
    scale = 4.2
    # A compression dome laid up in courses, the way one actually goes up.
    courses = 9
    for course in range(courses):
        if course / courses > build:
            break
        height = math.sin(math.pi * 0.5 * course / courses)
        radius = scale * math.cos(math.pi * 0.5 * course / courses)
        z = scale * height
        blocks = max(6, int(26 * radius / scale))
        for index in range(blocks):
            angle = math.tau * index / blocks + course * 0.24
            centre = np.array([radius * math.cos(angle),
                               radius * math.sin(angle), z])
            opaque.box(tuple(centre),
                       (max(0.45, 6.4 * radius / scale / blocks * 2.6), 0.9, 0.52),
                       (0.80, 0.86, 0.93, 1.0))
    app.world_labels.extend([
        WorldLabel(np.array([0.0, 0.0, scale + 1.5]),
                   "A COMPRESSION DOME", (61, 211, 255)),
        WorldLabel(np.array([0.0, 0.0, -1.1]),
                   "built in the harshest terrain on earth, "
                   "out of the only material there was", (169, 188, 203)),
    ])


SCENES_V3 = dict(SCENES)
SCENES_V3["hype_mother"] = scene_hype_mother
SCENES_V3["hype_igloo"] = scene_hype_igloo


# The audiences beat, opened out. Everything from "and most importantly,
# women" onward is the reason the project exists, so it gets the room.
AUDIENCE_RUN: tuple[Chapter, ...] = (
    Chapter(
        "audiences", "00", "I do not care what your audience is",
        "Homesteaders, builders, developers, makers. Anyone with reach.",
        (
            "Homesteading channels. Construction channels. Developers. Makers.",
            "Preppers. Crowdfunding people. Anyone with reach. And most importantly,",
            "women.",
        ),
        (), 4.0, (90.0, 16.0, 20.0), "hype_audiences",
    ),
    Chapter(
        "whichones", "00", "Which women",
        "I don't care which ones.",
        (
            "I don't care which ones. Sinners, saints, OnlyFans models. Hey, this",
            "structure would make a great livestreaming studio for cheap. Just saying.",
        ),
        (), 4.0, (60.0, 20.0, 18.0), "hype_audiences",
    ),
    Chapter(
        "whywomen", "00", "Why women specifically",
        "Why do I say women specifically?",
        (
            "Why do I say women specifically? Look. My mother is an angel and a saint.",
            "But growing up with a single parent was hard. We had a trailer that needed",
            "to be repossessed. She had to file bankruptcy.",
        ),
        (), 4.0, (44.0, 18.0, 18.0), "hype_mother",
    ),
    Chapter(
        "howihandled", "00", "How I handled it",
        "I avoided talking to girls, because I could not afford to.",
        (
            "How did I handle that? As a teenager, I avoided talking to girls, because",
            "I knew I could not in good conscience afford to wine and dine a date.",
        ),
        (), 4.0, (52.0, 16.0, 17.0), "hype_mother",
    ),
    Chapter(
        "lunches", "00", "The part nobody says out loud",
        "I did not take the reduced school lunches.",
        (
            "We were so poor that I did not take the reduced school lunches, on account",
            "of how absolutely death-blowingly embarrassing that would have been.",
            "Getting it is not embarrassing. Getting it and needing it, is. And a lot of",
            "people need it.",
        ),
        (), 4.0, (90.0, 14.0, 18.0), "hype_friend",
    ),
    Chapter(
        "fuller", "00", "And then I heard Fuller",
        "He wanted housing cheap enough that a mother could raise her child.",
        (
            "Buckminster Fuller, who gave us the geodesic dome and a great deal else,",
            "said once that his goal was housing affordable enough that a mother was not",
            "so daily and endlessly burdened by it that she could not focus on the thing",
            "that actually matters, which is raising her child. That is not a direct",
            "quote. It is what I took from him.",
        ),
        (), 4.0, (34.0, 24.0, 17.0), "hype_platform",
    ),
    Chapter(
        "hooked", "00", "That was it",
        "I was hooked, determined, and completely sold.",
        (
            "And when I heard that, I knew immediately this was the exact thing I had",
            "been preparing to make my lifelong mission. Hooked, determined, confident,",
            "sold, without needing any further proof. This is it. That is what I thought",
            "then and it is what I think now. It is enormously larger than me, for all",
            "of the right reasons, and it makes profound sense, on mathematics.",
        ),
        (), 4.0, (58.0, 22.0, 18.0), "hype_bones",
    ),
    Chapter(
        "igloo", "00", "The proof already exists",
        "The Inuit had it right the whole time.",
        (
            "And if you want proof that the shape works, it already shipped. The Inuit",
            "built compression domes out of the only material available to them, and",
            "lived in the harshest terrain on the planet. What further proof do you",
            "need? Ask me, because I will try to give it to you.",
        ),
        (), 4.0, (40.0, 22.0, 19.0), "hype_igloo",
    ),
)


CHAPTERS_V3 = _splice(CHAPTERS_V2, "audiences", AUDIENCE_RUN)
# "Psyche" is read by the speech engine as "psych-ee". Spelled the way it
# sounds, it lands the way it is meant to.
CHAPTERS_V3 = tuple(
    replace(chapter, narration=tuple(
        line.replace("Psyche.", "Sike.") for line in chapter.narration))
    if chapter.slug == "psyche" else chapter
    for chapter in CHAPTERS_V3
)


HYPE_V3_LESSON = Lesson(
    key="hype3",
    brand="FRANKENDOME",
    title="Frankendome, Version Three",
    chapters=CHAPTERS_V3,
    scenes=SCENES_V3,
    snapshot_prefix="hype3",
    style="hype",
    voice_rate="+7%",
    # v1 and v2 keep the raw label placement they were rendered with.
    label_layout="declutter",
)


# ----------------------------------------------------------------------
# Version four: v3, plus the brand segments and two corrections
# ----------------------------------------------------------------------

# 1. The endgame, stated in full this time.
CHAPTERS_V4 = tuple(
    replace(chapter, narration=(
        "And I will be completely transparent about the endgame. Somewhere there",
        "is a man on his seventh holiday of the year, watching the projected yield",
        "on a portfolio of rental houses, and I would like that line to do",
        "something sudden and downward on account of this. And I would like his",
        "girlfriend to leave him over it. That is the strategy. It is entirely",
        "transparent and only slightly relatable, and I have made my peace with it.",
    ))
    if chapter.slug == "hr" else chapter
    for chapter in CHAPTERS_V3
)

# 2. "Sike" came out drawn to almost twice the length of "bike", which is
#    not the sound. "Psych" measures closest to it and carries the hard
#    final K, so it is spelled the way the dictionary spells it.
CHAPTERS_V4 = tuple(
    replace(chapter, narration=tuple(
        line.replace("Sike.", "Psych.") for line in chapter.narration))
    if chapter.slug == "psyche" else chapter
    for chapter in CHAPTERS_V4
)

# 3. The hand-written contact beat is dropped in favour of the modular
#    outro segment, which carries the corrected handles and is shared with
#    every other video.
CHAPTERS_V4 = tuple(
    chapter for chapter in CHAPTERS_V4 if chapter.slug != "follow"
)

CHAPTERS_V4 = tuple(
    replace(chapter, number=f"{index + 1:02d}")
    for index, chapter in enumerate(CHAPTERS_V4)
)


_HYPE_V4_BASE = Lesson(
    key="hype4",
    brand="FRANKENDOME",
    title="Frankendome, Version Four",
    chapters=CHAPTERS_V4,
    scenes=SCENES_V3,
    snapshot_prefix="hype4",
    style="hype",
    voice_rate="+7%",
    label_layout="declutter",
)

# The party sting lands before the outro; the montage keeps its own long
# call to action rather than taking the short generic one.
HYPE_V4_LESSON = compose(
    _HYPE_V4_BASE,
    include=("party",),
    exclude=("cta_share",),
)


# ----------------------------------------------------------------------
# Version five: v4, but sober
# ----------------------------------------------------------------------

# The endgame beat reverts to the shorter form -- the projection cratering
# and nothing further.
CHAPTERS_V5 = tuple(
    replace(chapter, narration=(
        "And I will be completely transparent about the endgame. Somewhere there",
        "is a man on his seventh holiday of the year, watching the projected yield",
        "on a portfolio of rental houses, and I would like that line to do",
        "something sudden and downward on account of this. That is the strategy.",
        "It is entirely transparent and only slightly relatable, and I have made",
        "my peace with it.",
    ))
    if chapter.slug == "hr" else chapter
    for chapter in CHAPTERS_V4
)


_HYPE_V5_BASE = Lesson(
    key="hype5",
    brand="FRANKENDOME",
    title="Frankendome, Version Five",
    chapters=CHAPTERS_V5,
    scenes=SCENES_V3,
    snapshot_prefix="hype5",
    style="hype",
    voice_rate="+7%",
    label_layout="declutter",
)

# The plain frankendome stands in for the party sting: same bones, no
# celebration.
HYPE_V5_LESSON = compose(
    _HYPE_V5_BASE,
    include=("franken_plain",),
    exclude=("cta_share",),
)
