"""Scenes built for Domology from the film engine's own parts.

Most plates re-shoot a chapter of an existing film. A few ideas have no film
chapter that shows them cleanly, so they are built here from the same pieces
the films use -- the solved dome, the arrows, the labels -- with every number
on them read from a token, never typed.

Each function paints into the two triangle batches the engine hands a scene,
after (or instead of) a borrowed film scene, with the plate's recipe and the
token resolver.
"""

from __future__ import annotations

import math
import re

import numpy as np

from two_v_demo.render_kit import AMBER, CYAN, GREEN, RED, WHITE, WorldLabel
from two_v_demo.visual_objects import draw, rgb, stage_for

from .markup import TOKEN

WOOD = (0.80, 0.62, 0.40, 1.0)
HUB = (0.58, 0.63, 0.70, 1.0)


def resolve_text(text: str, resolver) -> str:
    return TOKEN.sub(lambda match: resolver.value(match.group(1)), text)


def _label(app, point, text: str, colour) -> None:
    app.world_labels.append(WorldLabel(np.asarray(point, dtype=float), text, rgb(colour)))


def force_panel(app, opaque, transparent, p, recipe, resolver) -> None:
    """One triangle under load: rafters in compression, the tie in tension."""
    a = np.array([-3.4, 0.0, 0.7])
    b = np.array([3.4, 0.0, 0.7])
    c = np.array([0.0, 0.0, 5.0])
    for start, end in ((a, c), (c, b), (a, b)):
        opaque.cylinder(start, end, 0.17, WOOD, 14)
    for point in (a, b, c):
        opaque.sphere(point, 0.28, HUB, 8, 12)
    opaque.arrow(c + np.array([0.0, 0.0, 2.4]), c + np.array([0.0, 0.0, 0.38]), 0.10, RED)
    for start, end in ((a, c), (b, c)):
        direction = (end - start) / np.linalg.norm(end - start)
        outward = np.cross(direction, np.array([0.0, 1.0, 0.0]))
        outward = outward if outward[2] > 0 else -outward
        offset = outward * 0.62
        middle = (start + end) * 0.5
        opaque.arrow(start + direction * 0.9 + offset, middle - direction * 0.4 + offset, 0.065, RED)
        opaque.arrow(end - direction * 0.9 + offset, middle + direction * 0.4 + offset, 0.065, RED)
    below = np.array([0.0, 0.0, -0.62])
    middle = (a + b) * 0.5
    opaque.arrow(middle + np.array([-0.6, 0.0, 0.0]) + below, a + np.array([0.9, 0.0, 0.0]) + below,
                 0.065, CYAN)
    opaque.arrow(middle + np.array([0.6, 0.0, 0.0]) + below, b - np.array([0.9, 0.0, 0.0]) + below,
                 0.065, CYAN)
    for support in (a, b):
        opaque.arrow(support + np.array([0.0, 0.0, -1.7]), support + np.array([0.0, 0.0, -0.32]),
                     0.075, GREEN)
    _label(app, c + np.array([0.0, 0.0, 2.9]), "LOAD", RED)
    _label(app, (a + c) * 0.5 + np.array([-1.7, 0.0, 0.6]), "COMPRESSION", RED)
    _label(app, (b + c) * 0.5 + np.array([1.7, 0.0, 0.6]), "COMPRESSION", RED)
    _label(app, middle + np.array([0.0, 0.0, -1.35]), "TENSION", CYAN)
    _label(app, a + np.array([0.0, 0.0, -2.2]), "SUPPORT", GREEN)
    _label(app, b + np.array([0.0, 0.0, -2.2]), "SUPPORT", GREEN)


def _floor_ring(opaque, radius: float, colour, lift: float = 0.04, segments: int = 72) -> None:
    for index in range(segments):
        t0 = math.tau * index / segments
        t1 = math.tau * (index + 1) / segments
        opaque.cylinder(np.array([radius * math.cos(t0), radius * math.sin(t0), lift]),
                        np.array([radius * math.cos(t1), radius * math.sin(t1), lift]),
                        0.035, colour, 6)


def dimensioned_dome(app, opaque, transparent, p, recipe, resolver) -> None:
    """The solved dome with its radius, its height and its floor marked."""
    radius = 4.0
    draw(stage_for(app, opaque, transparent), "solved_dome", radius=radius, orientation=0,
         keys=1.0, alpha=1.0)
    _floor_ring(opaque, radius, AMBER)
    # Radius, along the ground in front of the dome.
    start = np.array([0.0, -0.02, 0.06])
    end = np.array([radius * math.cos(-0.6), radius * math.sin(-0.6), 0.06])
    opaque.cylinder(start, end, 0.045, AMBER, 6)
    for point in (start, end):
        opaque.sphere(point, 0.09, AMBER, 6, 8)
    _label(app, (start + end) * 0.5 + np.array([0.3, -1.0, 0.0]),
           resolve_text("RADIUS {{method_a.radius_ft}} FT", resolver), AMBER)
    # Height, a vertical line just beside the shell.
    base = np.array([radius + 0.7, 0.0, 0.0])
    top = base + np.array([0.0, 0.0, radius])
    opaque.cylinder(base, top, 0.045, CYAN, 6)
    for point in (base, top):
        opaque.cylinder(point - np.array([0.25, 0.0, 0.0]), point + np.array([0.25, 0.0, 0.0]),
                        0.04, CYAN, 6)
    _label(app, top * 0.5 + base * 0.5 + np.array([1.5, 0.0, 0.0]), "HEIGHT = RADIUS", CYAN)
    _label(app, np.array([0.0, 0.0, radius + 1.1]),
           resolve_text("{{method_a.floor_sqft}} SQ FT OF FLOOR", resolver), WHITE)


def dome_plan(app, opaque, transparent, p, recipe, resolver) -> None:
    """The solved dome from above, with its floor circle."""
    radius = 4.0
    draw(stage_for(app, opaque, transparent), "solved_dome", radius=radius, orientation=0,
         keys=1.0, alpha=1.0)
    _floor_ring(opaque, radius, AMBER, 0.05)
    _floor_ring(opaque, radius * 1.18, (0.35, 0.42, 0.5, 1.0), 0.02, 96)
    _label(app, np.array([0.0, -radius - 1.1, 0.1]),
           resolve_text("FLOOR {{method_a.floor_sqft}} SQ FT", resolver), AMBER)


def hv_dome_centred(app, chapter, progress, width, height, yaw=-48.0, pitch=12.0,
                    radii=3.4, fov=44.0):
    """The harvest's solved dome centred for a full page, instead of slid aside
    to leave room for a worksheet as the films do."""
    from two_v_demo import lesson_harvest as lh
    radius = lh._dome_radius()
    target = np.asarray(lh.DOME_ORIGIN, dtype=float) + np.array([0.0, 0.0, radius * 0.5])
    return lh._orbit(target, yaw, pitch, radius * radii), target, fov


def hv_pile(app, chapter, progress, width, height, yaw=-112.0, pitch=24.0,
            distance=17.5, fov=46.0):
    """The harvest's log or wedge pile, centred, with nothing slid aside for a tally."""
    from two_v_demo import lesson_harvest as lh
    p = min(1.0, max(0.0, float(progress)))
    explode = lh._knobs("explode", p)["explode"] if chapter.slug == "explode" else 1.0
    target = np.asarray(lh._log_centre(explode), dtype=float)
    return lh._orbit(target, yaw, pitch, distance), target, fov


CAMERAS = {"hv_dome_centred": hv_dome_centred, "hv_pile": hv_pile}


EXTRAS = {
    "force_panel": force_panel,
    "dimensioned_dome": dimensioned_dome,
    "dome_plan": dome_plan,
}
