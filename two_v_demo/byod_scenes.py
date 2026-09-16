"""Additional deterministic pictures for Bring Your Own Dome.

Iris and rotating services are concept illustrations, not fabrication plans.
The wedge chassis is the existing simulator's solved point-out geometry.
"""
from __future__ import annotations

import math
from functools import lru_cache

import numpy as np
import park_model as pm
import park_world
from . import creator_bridge as creator, park_bridge as park, raw_wedge_bridge as wedge
from . import lesson_dome_park as old
from . import byod_facts as facts
from .render_kit import AMBER, CYAN, GREEN, WHITE, MUTED, clamp, ease_in_out


def label(app, point, text, color=WHITE):
    old._label(app, np.asarray(point), text, color)


def ring(batch, radius, height, color, origin=(0., 0., 0.), thickness=.04):
    origin = np.asarray(origin)
    for i in range(72):
        a, b = math.tau * i / 72, math.tau * (i + 1) / 72
        batch.cylinder(origin + (radius * math.cos(a), radius * math.sin(a), height),
                       origin + (radius * math.cos(b), radius * math.sin(b), height),
                       thickness, color, 6)


def iris_radius(p):
    lo, hi = pm.iris_span()
    # Hold each end briefly: visible settled states are easier to compare.
    opened = ease_in_out(clamp((p - .15) / .65))
    return (lo + (hi - lo) * opened) / pm.FT_PER_M / 2


def scene_iris(app, opaque, transparent, p):
    creator.draw(app, park.field())
    maximum = pm.iris_span()[1] / pm.FT_PER_M / 2
    outer = maximum + .75
    radius = iris_radius(p)
    opaque.disc((0, 0, .15), outer + .2, (.29, .24, .18, 1), 72)
    ring(opaque, outer, .35, MUTED, thickness=.12)
    ring(opaque, maximum + .30, .40, AMBER, thickness=.065)
    n = 12
    for i in range(n):
        a = math.tau * i / n
        radial = np.array([math.cos(a), math.sin(a), 0.])
        tangent = np.array([-math.sin(a), math.cos(a), 0.])
        start = radial * (maximum + .45) + (0, 0, .48)
        end = radial * radius + (0, 0, .48)
        opaque.cylinder(radial * (pm.iris_span()[0] / pm.FT_PER_M / 2 - .1) + (0, 0, .3),
                        start, .045, MUTED, 6)
        # Overlapping tapered leaves follow the radial shoes. A diagonal
        # drive link makes the displacement legible from the high camera.
        corners = (start - tangent * .38, start + tangent * .55,
                   end + tangent * .60, end - tangent * .12)
        tint = (.52 + .035 * (i % 3), .39, .20, 1)
        opaque.triangle(corners[0], corners[1], corners[2], tint)
        opaque.triangle(corners[0], corners[2], corners[3], tint)
        opaque.cylinder(start + tangent * .25 + (0, 0, .1), end + (0, 0, .1),
                        .055, CYAN, 6)
        opaque.sphere(end + (0, 0, .11), .13, CYAN, 4, 8)
        opaque.cylinder(end - tangent * .24, end + tangent * .24, .15, AMBER, 4)
    ring(opaque, radius, .75, CYAN, thickness=.065)
    opaque.arrow((-radius, 0, 1.1), (radius, 0, 1.1), .035, CYAN)
    label(app, (0, 0, 2.0), f"{radius * 2 * pm.FT_PER_M:.1f} FT ACCEPTOR DIAMETER", CYAN)
    label(app, (0, -outer, 1.1), "SLIDING LEAVES + LOCKING SHOES", AMBER)
    label(app, (0, outer, .9), "IRIS CONCEPT / FLOOR STAYS PUT", MUTED)


def scene_title(app, opaque, transparent, p):
    old.scene_site(app, opaque, transparent, .26)
    app.world_labels.clear()


@lru_cache(maxsize=4)
def compact_dome(solar=False):
    config = dict(creator.presets_all()[0][1])
    config.update(radius=pm.SOLAR_RADIUS_FT / pm.FT_PER_M,
                  foundation="Bare Ground", props=[], partitions="None",
                  layers=["None"] * 3)
    if solar:
        config.update(old._clad_config(pm.solar_layouts()[0]))
    return creator.build(config, "BYOD compact shell")


def scene_rotation(app, opaque, transparent, p):
    creator.draw(app, park.field())
    spec = pm.Pad(diameter_ft=24, deck="concrete", rotating=True)
    angle = -65 + 165 * ease_in_out(clamp((p - .15) / .7))
    creator.draw(app, park.pad(spec, occupied=True, heading=angle))
    build = compact_dome(True)
    creator.draw(app, build, offset=(0, 0, park.dome_lift(spec)), yaw=angle)
    a = math.radians(angle)
    direction = np.array([math.cos(a), math.sin(a), 0.])
    opaque.arrow(direction * 3.3 + (0, 0, 1.9), direction * 5.2 + (0, 0, 1.9), .065, CYAN)
    opaque.sphere((6.0, -2.0, 6.3), .5, AMBER, 6, 12)
    label(app, (6.0, -2.0, 7.3), "SUN", AMBER)
    label(app, (-4.8, -1, 1), "PRIVATE CORNER", CYAN)
    label(app, (4.8, 3, 1), "STREET / VIEW", WHITE)
    label(app, (0, 0, 6), "OPTIONAL DELUXE FOUNDATION", AMBER)


def _wall(batch, a, b, color):
    a, b = np.asarray(a), np.asarray(b)
    for height in (.65, 1.0, 1.35):
        batch.cylinder(a + (0, 0, height), b + (0, 0, height), .17, color, 4)


def scene_rooms(app, opaque, transparent, p):
    creator.draw(app, park.field())
    spec = pm.Pad(diameter_ft=36, deck="wood")
    creator.draw(app, park.pad(spec, stage=4))
    # Fixed utility column; the room divider moves independently of it.
    opaque.cylinder((0, 0, .5), (0, 0, 2.3), .34, AMBER, 16)
    angle = .75 - 1.5 * ease_in_out(clamp((p - .2) / .5))
    outer = np.array([4.7 * math.cos(angle), 4.7 * math.sin(angle), 0])
    _wall(opaque, (.6, 0, 0), outer, CYAN)
    _wall(opaque, (-.6, 0, 0), (-4.7, 0, 0), (.65, .71, .75, 1))
    opaque.box((-2.3, 2, .85), (2.1, 2.9, .55), CYAN)
    opaque.box((-2.3, 2.9, 1.2), (1.8, .6, .2), WHITE)
    office = np.array([2.6, 2.5, 0])
    # Desk folds away when the bedroom grows.
    desk = max(.08, 1 - ease_in_out(clamp((p - .45) / .25)))
    opaque.box(office + (0, 0, 1.05), (1.7 * desk, .8, .12), AMBER)
    ring(opaque, 1.05, .55, AMBER, thickness=.045)
    label(app, (0, 0, 3.1), "UTILITY CORE / SAME PLACE", AMBER)
    label(app, (-2.7, 2.5, 1.9), "BEDROOM", CYAN)
    label(app, (2.5, -2, 1.8), "OFFICE + BEDROOM" if p < .5 else "MORE BEDROOM / OFFICE RETIRED", WHITE)


def scene_channels(app, opaque, transparent, p):
    radius = 5.
    wedge.world_batches(opaque, "point_dome_out", scene_radius=radius, parts=("wood",))
    model = wedge.model("point_dome_out")
    scale = radius / model.topology.sphere_radius_in
    # Separate supply/conduit traces rise from the known central service spot.
    # Drains remain at the floor; the picture does not imply uphill gravity flow.
    for i, color in enumerate((CYAN, AMBER)):
        x = (i - .5) * .20
        opaque.cylinder((x, 0, .15), (x, 0, radius + .08), .06, color, 8)
    for i, seam in enumerate(model.seams):
        if i / len(model.seams) > .15 + .85 * clamp(p * 1.6):
            continue
        a = np.asarray(seam.start) * scale
        b = np.asarray(seam.end) * scale
        opaque.cylinder(a, b, .035, CYAN, 5)
        t = (p * 3 + i * .09) % 1
        opaque.sphere(a + (b - a) * t, .085, AMBER, 3, 6)
    label(app, (0, 0, 6.6), "CENTER UP / OUT / AROUND THE SHELL", CYAN)
    label(app, (0, 0, -.8), "ACCESSIBLE CHANNELS / DRAIN AT FLOOR", MUTED)


def scene_growth(app, opaque, transparent, p):
    stage = min(2, int(p * 3))
    size = pm.DOME_CLASSES[stage]
    radius = 3.0 * size.longest_member_ft / pm.DOME_CLASSES[0].longest_member_ft
    wedge.world_batches(opaque, "point_dome_out", scene_radius=radius, parts=("wood", "rigid"))
    count = len(wedge.model("point_dome_out").members)
    label(app, (0, 0, radius + 1.3), f"{size.longest_member_ft:.0f} FT LONG MEMBER / ~{size.floor_sqft:,.0f} SQ FT", CYAN)
    label(app, (0, 0, -.9), f"{count} WEDGE MEMBERS / QUALIFIED HARDWARE KEPT", AMBER)
    # Collection rack: future, longer members appear beside the current dome.
    for i in range(8):
        if i / 8 > p:
            continue
        opaque.cylinder((7 + (i % 4) * .18, -2, .3 + (i // 4) * .18),
                        (7 + (i % 4) * .18, 2, .3 + (i // 4) * .18),
                        .075, (.62, .39, .18, 1), 3)


def scene_layers(app, opaque, transparent, p):
    # Reuse the real shell but replace the old price/payback labels entirely.
    old.scene_layers(app, opaque, transparent, p)
    app.world_labels.clear()
    shift = old._shift(app)
    count = min(7, int(p * 8))
    step = pm.shell_ladder(old.HOME)[count]
    # An exploded material stack beside the dome makes the removable layers
    # visible even when the Creator's three cladding slots are already filled.
    for i in range(count + 1):
        opaque.box(shift + (-5.1, 0, .8 + i * .30), (2.0, 2.4, .16),
                   CYAN if i == count else (.68, .54 + .03 * (i % 3), .34, 1))
    label(app, shift + (0, 0, 9), f"{count} ADDED LAYERS / MODEL R-{step.r_value:.1f}", CYAN)
    label(app, shift + (-5.1, 0, 4.2), "REMOVABLE WEATHER SHELL", WHITE)


def scene_solar(app, opaque, transparent, p):
    # Capacity only: do not borrow the old universal tracking-yield assumption.
    shift = old._shift(app)
    creator.draw(app, park.field(), offset=tuple(shift))
    for i, layout in enumerate(pm.solar_layouts()):
        x = (1 - i) * 8.
        build = creator.build(old._clad_config(layout), "BYOD " + layout.name)
        creator.draw(app, build, offset=tuple(shift + (x, 0, .35)), yaw=-20 + p * 40)
        label(app, shift + (x, 0, build.apex + 1.6), layout.name.upper(), CYAN)
        label(app, shift + (x, 0, build.apex + .5), f"{layout.watts / 1000:.1f} kW / {layout.area_sqft:,.0f} SQ FT", WHITE)


def scene_starter(app, opaque, transparent, p):
    shift = old._shift(app)
    creator.draw(app, park.field(), offset=tuple(shift))
    radius = facts.starter_diameter() / pm.FT_PER_M / 2
    # Block-supported deck: no misleading slab, motor or individual pedestal.
    for x in (-radius * .6, 0, radius * .6):
        for y in (-radius * .6, radius * .6):
            opaque.box(shift + (x, y, .3), (.55, .55, .5), MUTED)
    opaque.disc(shift + (0, 0, .6), radius, (.53, .36, .20, 1), 64)
    ring(opaque, radius, .70, AMBER, origin=shift, thickness=.10)
    opaque.cylinder(shift + (0, 0, .6), shift + (0, 0, 1.4), .20, AMBER, 12)
    label(app, shift + (0, 0, 2.6), "FIXED RIM / SHARED SERVICE SPUR", AMBER)


def scene_departure(app, opaque, transparent, p):
    old.scene_move(app, opaque, transparent, p)
    app.world_labels[:] = [x for x in app.world_labels if "no lease" not in x.text]
    label(app, old._shift(app) + (0, 0, 12), "DISASSEMBLE / TRANSPORT / REASSEMBLE", WHITE)


def scene_rewards(app, opaque, transparent, p):
    # Three physical categories; tier promises stay in the spoken script.
    for i, (name, color) in enumerate((("FOUNDER + KEEPSAKES", CYAN), ("SIGNED BOOK", AMBER), ("DESIGN SESSIONS", GREEN))):
        x = (1 - i) * 6
        opaque.box((x, 0, .4), (4.6, 3.8, .5), (.12, .17, .22, 1))
        if i == 0:
            wedge.world_batches(opaque, "point_dome_out", scene_radius=1.2, origin=(x, 0, .7))
        elif i == 1:
            opaque.box((x, 0, 1.7), (1.7, .35, 2.4), color)
            opaque.box((x, -.03, 1.7), (1.5, .37, 2.1), WHITE)
        else:
            opaque.box((x, 0, 1.5), (3.1, .25, 2), color)
            opaque.box((x, .17, 1.5), (2.8, .1, 1.7), (.06, .12, .18, 1))
        label(app, (x, 0, 3.9), name, color)


SCENES = {
    "byod_title": scene_title, "byod_iris": scene_iris,
    "byod_rotation": scene_rotation, "byod_rooms": scene_rooms,
    "byod_channels": scene_channels, "byod_growth": scene_growth,
    "byod_layers": scene_layers, "byod_solar": scene_solar,
    "byod_starter": scene_starter, "byod_departure": scene_departure,
    "byod_rewards": scene_rewards,
}
