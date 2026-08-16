"""Dome accessories and appliances: the things that make a shell a home.

Every emitter here follows the same contract as the star objects in
:mod:`presenter.world` -- ``emit(opaque, transparent, params, t, targets)``
-- so the scene composer can drop any of them onto a stage, animate their
parameters over a shot, and point the camera at them by name.

Positions are given the way you would describe them to a builder standing
inside the dome: a compass bearing (``az_deg``) and, where it matters, an
angle up from the horizon (``polar_deg``), against the dome's own radius.
That keeps an accessory glued to the shell when the dome is resized.
"""

from __future__ import annotations

import math

import numpy as np

from two_v_demo.geometry import normalize

from .world import Batch, TAU, _geo, _rotate_about, rnd

# Shared material colours, so a stove in one scene matches a stove in the
# next without every emitter inventing its own palette.
STEEL = (0.52, 0.56, 0.62, 1.0)
DARK_STEEL = (0.24, 0.26, 0.30, 1.0)
CHROME = (0.82, 0.84, 0.88, 1.0)
TIMBER = (0.64, 0.47, 0.28, 1.0)
WHITE_GOODS = (0.90, 0.91, 0.93, 1.0)
GLASS = (0.62, 0.82, 0.92, 0.30)
EMBER = (1.00, 0.48, 0.12, 1.0)
WATER = (0.22, 0.52, 0.78, 0.72)


def _tangent_basis(az_deg: float):
    """Outward / along-the-wall / up unit vectors at a compass bearing."""
    a = math.radians(az_deg)
    outward = np.array([math.cos(a), math.sin(a), 0.0])
    along = np.array([-math.sin(a), math.cos(a), 0.0])
    up = np.array([0.0, 0.0, 1.0])
    return outward, along, up


def _shell_frame(R: float, az_deg: float, polar_deg: float):
    """A point on the dome's surface plus a local frame there.

    ``polar_deg`` is measured from the apex, so 0 is straight overhead and
    90 is down at the base ring. Returns (point, outward, u, v)."""
    polar = math.radians(polar_deg)
    az = math.radians(az_deg)
    point = np.array([R * math.sin(polar) * math.cos(az),
                      R * math.sin(polar) * math.sin(az),
                      R * math.cos(polar)])
    outward = normalize(point)
    helper = np.array([0.0, 0.0, 1.0])
    if abs(float(np.dot(outward, helper))) > 0.92:
        helper = np.array([0.0, 1.0, 0.0])
    u = normalize(np.cross(outward, helper))
    v = normalize(np.cross(outward, u))
    return point, outward, u, v


def _face_polar(center) -> float:
    """Angle in degrees from the apex to a face centre."""
    n = normalize(np.asarray(center, dtype=np.float64))
    return math.degrees(math.acos(max(-1.0, min(1.0, float(n[2])))))


def _face_az(center) -> float:
    return math.degrees(math.atan2(float(center[1]), float(center[0])))


def _angle_gap(a: float, b: float) -> float:
    """Smallest absolute difference between two bearings, in degrees."""
    return abs((a - b + 180.0) % 360.0 - 180.0)


# ---------------------------------------------------------------------------
# Openings: door, windows, skylight
# ---------------------------------------------------------------------------

def emit_door(o: Batch, tr: Batch, p: dict, t: float, targets: dict) -> None:
    """A framed entry door standing in the dome's lower band.

    ``open`` swings the leaf on its hinge from shut (0) to wide (1), which
    is what you animate across a shot to walk the camera inside."""
    R = float(p.get("radius", 4.8))
    az = float(p.get("az_deg", 0.0))
    width = float(p.get("width", 0.92))
    height = float(p.get("height", 2.05))
    openness = max(0.0, min(1.0, float(p.get("open", 0.0))))
    leaf_color = tuple(p.get("leaf_color", TIMBER))
    outward, along, _up = _tangent_basis(az)
    # Stand the frame just inside the base ring so the jambs read against
    # the shell rather than floating outside it.
    base = outward * (R * float(p.get("inset", 0.985)))
    hinge = base - along * (width * 0.5)
    jamb = 0.09
    for side in (-1.0, 1.0):
        post = base + along * (width * 0.5 + jamb * 0.5) * side
        o.box((post[0], post[1], height * 0.5), (0.14, jamb, height),
              STEEL, yaw=math.radians(az))
    header = base + np.array([0.0, 0.0, height + 0.06])
    o.box((header[0], header[1], header[2]),
          (0.14, width + jamb * 2, 0.12), STEEL, yaw=math.radians(az))
    o.box((base[0], base[1], 0.02), (0.24, width + jamb * 2, 0.04),
          DARK_STEEL, yaw=math.radians(az))
    swing = openness * math.radians(95.0)
    leaf_dir = _rotate_about(along, np.zeros(3), np.array([0.0, 0.0, 1.0]),
                             swing)
    centre = hinge + leaf_dir * (width * 0.5)
    o.box((centre[0], centre[1], height * 0.5), (0.05, width, height - 0.05),
          leaf_color, yaw=math.radians(az) + swing)
    handle = hinge + leaf_dir * (width * 0.86)
    o.cylinder((handle[0], handle[1], height * 0.47),
               (handle[0] + outward[0] * 0.09,
                handle[1] + outward[1] * 0.09, height * 0.47),
               0.022, CHROME, sides=6)
    targets["door"] = (base + np.array([0.0, 0.0, height * 0.5]),
                       max(height * 0.9, R * 0.55))


def _glazed_faces(o: Batch, tr: Batch, R: float, keep, color,
                  frame_color, inset: float):
    """Glaze whichever real 2V dome faces pass the ``keep`` test.

    Glazing the dome's own triangles (rather than pasting a rectangle on
    the outside) is what makes a window read as part of the structure."""
    geo = _geo()
    verts = geo.vertices * R
    glazed = []
    for face in geo.hemisphere_faces:
        pts = [verts[k] for k in face]
        centre = sum(pts) / 3.0
        if not keep(centre):
            continue
        n = normalize(centre)
        pane = [centre + (pt - centre) * inset + n * 0.01 for pt in pts]
        tr.tri(pane[0], pane[1], pane[2], color, n)
        for i in range(3):
            j = (i + 1) % 3
            o.cylinder(pane[i], pane[j], 0.035, frame_color, sides=5,
                       caps=False)
        glazed.append(centre)
    return glazed


def emit_window_band(o: Batch, tr: Batch, p: dict, t: float,
                     targets: dict) -> None:
    """Glazed dome faces in a horizontal band -- the dome's windows.

    ``polar_deg`` picks how high the band sits (measured down from the
    apex) and ``spread_deg`` how tall it is; ``az_deg`` / ``arc_deg``
    limit it to one side of the dome instead of ringing it completely."""
    R = float(p.get("radius", 4.8))
    polar = float(p.get("polar_deg", 58.0))
    spread = float(p.get("spread_deg", 16.0))
    az = float(p.get("az_deg", 0.0))
    arc = float(p.get("arc_deg", 360.0))
    tint = float(p.get("tint", 0.30))
    color = (GLASS[0], GLASS[1], GLASS[2], max(0.04, min(0.9, tint)))

    def keep(centre):
        if abs(_face_polar(centre) - polar) > spread:
            return False
        return arc >= 359.0 or _angle_gap(_face_az(centre), az) <= arc * 0.5

    glazed = _glazed_faces(o, tr, R, keep, color, STEEL,
                           float(p.get("inset", 0.90)))
    if glazed:
        centre = sum(glazed) / len(glazed)
    else:
        centre = np.array([0.0, 0.0, R * 0.5])
    targets["windows"] = (centre, R * 0.85)


def emit_skylight(o: Batch, tr: Batch, p: dict, t: float,
                  targets: dict) -> None:
    """Glazing over the crown faces, with a raised curb around the ring."""
    R = float(p.get("radius", 4.8))
    reach = float(p.get("polar_deg", 30.0))
    tint = float(p.get("tint", 0.24))
    color = (0.70, 0.86, 0.95, max(0.04, min(0.9, tint)))
    _glazed_faces(o, tr, R, lambda c: _face_polar(c) <= reach, color,
                  CHROME, float(p.get("inset", 0.92)))
    if float(p.get("curb", 1.0)) > 0.5:
        curb_polar = math.radians(reach)
        ring_r = R * math.sin(curb_polar)
        ring_z = R * math.cos(curb_polar)
        segs = 28
        for i in range(segs):
            a0 = TAU * i / segs
            a1 = TAU * (i + 1) / segs
            o.cylinder((ring_r * math.cos(a0), ring_r * math.sin(a0), ring_z),
                       (ring_r * math.cos(a1), ring_r * math.sin(a1), ring_z),
                       0.05, CHROME, sides=6, caps=False)
    targets["skylight"] = (np.array([0.0, 0.0, R * 0.92]), R * 0.7)


# ---------------------------------------------------------------------------
# Heat, water, power
# ---------------------------------------------------------------------------

def emit_wood_stove(o: Batch, tr: Batch, p: dict, t: float,
                    targets: dict) -> None:
    """A wood stove on a hearth pad with a flue climbing to the crown.

    ``fire`` 0..1 lights the firebox: turn it up across a shot and the
    embers brighten and the flue heat shimmer picks up."""
    R = float(p.get("radius", 4.8))
    az = float(p.get("az_deg", 150.0))
    ring = R * float(p.get("ring_frac", 0.45))
    fire = max(0.0, min(1.0, float(p.get("fire", 0.6))))
    body_r = float(p.get("body_r", 0.30))
    body_h = float(p.get("body_h", 0.78))
    flue_h = float(p.get("flue_h", 3.2))
    a = math.radians(az)
    cx, cy = ring * math.cos(a), ring * math.sin(a)
    o.box((cx, cy, 0.03), (1.30, 1.30, 0.06), (0.30, 0.30, 0.33, 1.0),
          yaw=a)
    for k in range(4):                              # stubby legs
        ang = TAU * k / 4 + math.pi / 4
        lx, ly = cx + body_r * 0.7 * math.cos(ang), cy + body_r * 0.7 * math.sin(ang)
        o.cylinder((lx, ly, 0.06), (lx, ly, 0.20), 0.03, DARK_STEEL, sides=5)
    o.cylinder((cx, cy, 0.20), (cx, cy, 0.20 + body_h), body_r,
               (0.16, 0.16, 0.18, 1.0), sides=12)
    outward, _along, _up = _tangent_basis(az + 180.0)
    face = np.array([cx, cy, 0.20 + body_h * 0.45]) + outward * body_r
    o.cylinder(face - outward * 0.02, face + outward * 0.02, body_r * 0.55,
               (0.10, 0.10, 0.12, 1.0), sides=10)
    if fire > 0.02:
        glow = (EMBER[0], EMBER[1] * (0.4 + 0.6 * fire), 0.10,
                0.35 + 0.55 * fire)
        tr.disc((face[0] + outward[0] * 0.03, face[1] + outward[1] * 0.03,
                 face[2]), body_r * 0.45, glow, sides=12)
    o.cylinder((cx, cy, 0.20 + body_h), (cx, cy, flue_h), 0.075,
               DARK_STEEL, sides=8)
    if fire > 0.02:                                  # rising heat
        for i in range(int(14 * fire)):
            u = (t * 0.5 + rnd(i, 4.0)) % 1.0
            z = 0.20 + body_h + u * (flue_h - body_h)
            tr.marker((cx + 0.05 * math.sin(t * 2.0 + i), cy, z),
                      0.03 + 0.02 * u, (1.0, 0.6, 0.25, 0.5 * (1.0 - u)))
    targets["wood_stove"] = (np.array([cx, cy, 0.20 + body_h * 0.5]),
                             max(1.4, R * 0.5))


def emit_water_tank(o: Batch, tr: Batch, p: dict, t: float,
                    targets: dict) -> None:
    """A cistern with a visible fill line.

    ``level`` 0..1 is how full it is, so a shot can fill or drain it while
    the camera watches."""
    R = float(p.get("radius", 4.8))
    az = float(p.get("az_deg", 210.0))
    ring = R * float(p.get("ring_frac", 1.35))
    tank_r = float(p.get("tank_r", 0.62))
    tank_h = float(p.get("tank_h", 1.90))
    level = max(0.0, min(1.0, float(p.get("level", 0.62))))
    a = math.radians(az)
    cx, cy = ring * math.cos(a), ring * math.sin(a)
    o.cylinder((cx, cy, 0.0), (cx, cy, tank_h), tank_r,
               (0.30, 0.42, 0.48, 1.0), sides=14)
    for band in (0.28, 0.62, 0.90):                  # hoop ribs
        z = tank_h * band
        segs = 18
        for i in range(segs):
            a0 = TAU * i / segs
            a1 = TAU * (i + 1) / segs
            o.cylinder((cx + tank_r * 1.01 * math.cos(a0),
                        cy + tank_r * 1.01 * math.sin(a0), z),
                       (cx + tank_r * 1.01 * math.cos(a1),
                        cy + tank_r * 1.01 * math.sin(a1), z),
                       0.028, STEEL, sides=5, caps=False)
    if level > 0.01:
        tr.cylinder((cx, cy, 0.02), (cx, cy, tank_h * level),
                    tank_r * 0.96, WATER, sides=14)
    o.cylinder((cx, cy, tank_h), (cx, cy, tank_h + 0.18), 0.10, STEEL,
               sides=8)
    tap = np.array([cx + tank_r, cy, 0.35])
    o.cylinder(tap, tap + np.array([0.22, 0.0, 0.0]), 0.035, CHROME, sides=6)
    targets["water_tank"] = (np.array([cx, cy, tank_h * 0.5]),
                             max(tank_h * 0.85, 1.4))


def emit_battery_rack(o: Batch, tr: Batch, p: dict, t: float,
                      targets: dict) -> None:
    """Battery bank plus inverter cabinet -- the off-grid power wall.

    ``charge`` 0..1 lights the cells' state-of-charge indicators."""
    R = float(p.get("radius", 4.8))
    az = float(p.get("az_deg", 250.0))
    ring = R * float(p.get("ring_frac", 0.72))
    cells = int(p.get("cells", 6))
    charge = max(0.0, min(1.0, float(p.get("charge", 0.75))))
    a = math.radians(az)
    outward, along, _up = _tangent_basis(az)
    base = np.array([ring * math.cos(a), ring * math.sin(a), 0.0])
    rack_w = 1.45
    rack_h = 1.25
    o.box((base[0], base[1], rack_h * 0.5), (0.55, rack_w, 0.05),
          DARK_STEEL, yaw=a)
    o.box((base[0], base[1], 0.03), (0.60, rack_w, 0.06), DARK_STEEL, yaw=a)
    rows = 2
    per_row = max(1, cells // rows)
    lit = int(round(cells * charge))
    index = 0
    for row in range(rows):
        z = 0.22 + row * (rack_h * 0.52)
        for k in range(per_row):
            offset = (k - (per_row - 1) * 0.5) * (rack_w / max(1, per_row))
            centre = base + along * offset
            o.box((centre[0], centre[1], z + 0.16),
                  (0.42, rack_w / per_row * 0.86, 0.32),
                  (0.18, 0.20, 0.24, 1.0), yaw=a)
            led = centre + outward * 0.22
            color = ((0.20, 0.95, 0.45, 1.0) if index < lit
                     else (0.35, 0.12, 0.12, 1.0))
            o.marker((led[0], led[1], z + 0.16), 0.030, color)
            index += 1
    inv = base + along * (rack_w * 0.5 + 0.42)
    o.box((inv[0], inv[1], 0.75), (0.34, 0.62, 1.10), (0.80, 0.82, 0.86, 1.0),
          yaw=a)
    screen = inv + outward * 0.18
    o.marker((screen[0], screen[1], 1.05), 0.055, (0.20, 0.75, 1.00, 1.0))
    targets["battery_rack"] = (base + np.array([0.0, 0.0, rack_h * 0.5]),
                               max(rack_w * 1.1, R * 0.45))


def emit_mini_split(o: Batch, tr: Batch, p: dict, t: float,
                    targets: dict) -> None:
    """A ductless heat pump: indoor head on the shell, condenser outside.

    ``spin`` turns the condenser fan, and ``flow`` streams conditioned air
    off the indoor head so a shot can show it running."""
    R = float(p.get("radius", 4.8))
    az = float(p.get("az_deg", 40.0))
    head_polar = float(p.get("polar_deg", 55.0))
    spin = float(p.get("spin", 2.0))
    flow = max(0.0, min(1.0, float(p.get("flow", 0.6))))
    point, outward, u, v = _shell_frame(R, az, head_polar)
    inward = -outward
    head = point + inward * 0.16
    o.box((head[0], head[1], head[2]), (0.26, 0.92, 0.30), WHITE_GOODS,
          yaw=math.radians(az))
    vane = head + inward * 0.13
    o.box((vane[0], vane[1], vane[2] - 0.12), (0.06, 0.84, 0.05),
          (0.72, 0.75, 0.80, 1.0), yaw=math.radians(az))
    if flow > 0.02:
        for i in range(int(26 * flow)):
            k = (t * 0.55 + rnd(i, 2.0)) % 1.0
            drop = vane + inward * (0.25 + 2.6 * k) \
                + np.array([0.0, 0.0, -1.5 * k * k])
            side = (rnd(i, 3.0) - 0.5) * 0.9
            tr.marker((drop[0] + side * u[0], drop[1] + side * u[1], drop[2]),
                      0.05, (0.55, 0.85, 1.0, 0.55 * (1.0 - k)))
    out_r = R * float(p.get("ring_frac", 1.22))
    a = math.radians(az)
    cx, cy = out_r * math.cos(a), out_r * math.sin(a)
    o.box((cx, cy, 0.42), (0.36, 0.86, 0.72), (0.74, 0.76, 0.80, 1.0), yaw=a)
    fan_c = np.array([cx, cy, 0.46]) + np.array([math.cos(a), math.sin(a),
                                                 0.0]) * 0.19
    for blade in range(5):
        ang = spin * t * TAU + TAU * blade / 5
        along = np.array([-math.sin(a), math.cos(a), 0.0])
        tip = fan_c + along * (0.24 * math.cos(ang)) \
            + np.array([0.0, 0.0, 0.24 * math.sin(ang)])
        o.cylinder(fan_c, tip, 0.022, (0.88, 0.90, 0.93, 1.0), sides=4,
                   caps=False)
    o.cylinder((cx, cy, 0.05), (point[0], point[1], 0.05), 0.035,
               (0.30, 0.32, 0.36, 1.0), sides=6)
    targets["mini_split"] = (head, max(1.2, R * 0.55))
    targets["condenser"] = (np.array([cx, cy, 0.45]), 1.1)


# ---------------------------------------------------------------------------
# Decks, lofts, rainwater
# ---------------------------------------------------------------------------

def emit_loft(o: Batch, tr: Batch, p: dict, t: float, targets: dict) -> None:
    """A mezzanine floor with a guard rail and a ladder up to it.

    A dome's upper volume is only usable if you can stand on some of it,
    which is exactly what this half-deck is for."""
    R = float(p.get("radius", 4.8))
    deck_z = float(p.get("deck_z", 2.35))
    frac = max(0.15, min(0.95, float(p.get("span", 0.62))))
    arc = math.radians(float(p.get("arc_deg", 190.0)))
    az = math.radians(float(p.get("az_deg", 90.0)))
    deck_r = R * frac
    segs = 26
    deck_color = tuple(p.get("deck_color", TIMBER))
    for i in range(segs):
        a0 = az - arc * 0.5 + arc * i / segs
        a1 = az - arc * 0.5 + arc * (i + 1) / segs
        inner = np.array([0.0, 0.0, deck_z])
        p0 = (deck_r * math.cos(a0), deck_r * math.sin(a0), deck_z)
        p1 = (deck_r * math.cos(a1), deck_r * math.sin(a1), deck_z)
        o.tri(inner, p0, p1, deck_color, (0, 0, 1))
        o.quad((p0[0], p0[1], deck_z - 0.10), (p1[0], p1[1], deck_z - 0.10),
               p1, p0, (0.44, 0.33, 0.20, 1.0))
    rail_h = float(p.get("rail_h", 1.0))
    posts = 9
    for k in range(posts):
        a = az - arc * 0.5 + arc * k / max(1, posts - 1)
        px, py = deck_r * 0.97 * math.cos(a), deck_r * 0.97 * math.sin(a)
        o.cylinder((px, py, deck_z), (px, py, deck_z + rail_h), 0.035,
                   STEEL, sides=6)
    for i in range(segs):
        a0 = az - arc * 0.5 + arc * i / segs
        a1 = az - arc * 0.5 + arc * (i + 1) / segs
        o.cylinder((deck_r * 0.97 * math.cos(a0),
                    deck_r * 0.97 * math.sin(a0), deck_z + rail_h),
                   (deck_r * 0.97 * math.cos(a1),
                    deck_r * 0.97 * math.sin(a1), deck_z + rail_h),
                   0.03, STEEL, sides=5, caps=False)
    lad_a = az + math.pi
    lx, ly = deck_r * 0.55 * math.cos(lad_a), deck_r * 0.55 * math.sin(lad_a)
    side = np.array([-math.sin(lad_a), math.cos(lad_a), 0.0]) * 0.22
    for s in (-1, 1):
        foot = np.array([lx, ly, 0.0]) + side * s
        top = np.array([lx, ly, deck_z]) + side * s \
            + np.array([math.cos(lad_a), math.sin(lad_a), 0.0]) * 0.30
        o.cylinder(foot, top, 0.035, (0.70, 0.55, 0.34, 1.0), sides=6)
    rungs = max(2, int(deck_z / 0.28))
    for k in range(1, rungs):
        z = deck_z * k / rungs
        push = np.array([math.cos(lad_a), math.sin(lad_a), 0.0]) \
            * (0.30 * k / rungs)
        centre = np.array([lx, ly, z]) + push
        o.cylinder(centre - side, centre + side, 0.022,
                   (0.75, 0.60, 0.38, 1.0), sides=5)
    targets["loft"] = (np.array([deck_r * 0.4 * math.cos(az),
                                 deck_r * 0.4 * math.sin(az), deck_z]),
                       max(deck_r * 1.1, R * 0.8))


def emit_deck(o: Batch, tr: Batch, p: dict, t: float, targets: dict) -> None:
    """An exterior deck and steps outside the door."""
    R = float(p.get("radius", 4.8))
    az = float(p.get("az_deg", 0.0))
    width = float(p.get("width", 3.4))
    depth = float(p.get("depth", 2.2))
    deck_z = float(p.get("deck_z", 0.34))
    a = math.radians(az)
    outward, along, _up = _tangent_basis(az)
    centre = outward * (R + depth * 0.5)
    o.box((centre[0], centre[1], deck_z), (depth, width, 0.09), TIMBER,
          yaw=a)
    planks = 9
    for k in range(planks):                            # visible plank lines
        off = (k - (planks - 1) * 0.5) * (width / planks)
        line = centre + along * off
        o.box((line[0], line[1], deck_z + 0.05),
              (depth * 0.98, width / planks * 0.10, 0.012),
              (0.50, 0.36, 0.21, 1.0), yaw=a)
    for s in (-1.0, 1.0):
        for k in range(5):
            post = centre + along * (width * 0.5 * s) \
                + outward * ((k / 4.0 - 0.5) * depth * 0.9)
            o.cylinder((post[0], post[1], deck_z),
                       (post[0], post[1], deck_z + 0.95), 0.045, TIMBER,
                       sides=6)
        rail_a = centre + along * (width * 0.5 * s) - outward * depth * 0.45
        rail_b = centre + along * (width * 0.5 * s) + outward * depth * 0.45
        o.cylinder((rail_a[0], rail_a[1], deck_z + 0.95),
                   (rail_b[0], rail_b[1], deck_z + 0.95), 0.04, TIMBER,
                   sides=6)
    steps = int(p.get("steps", 3))
    for k in range(steps):
        z = deck_z * (steps - k) / (steps + 1)
        tread = centre + outward * (depth * 0.5 + 0.28 * (k + 1))
        o.box((tread[0], tread[1], z), (0.30, width * 0.45, 0.07),
              (0.56, 0.41, 0.24, 1.0), yaw=a)
    targets["deck"] = (np.array([centre[0], centre[1], deck_z + 0.4]),
                       max(width, depth) * 0.85)


def emit_rain_catch(o: Batch, tr: Batch, p: dict, t: float,
                    targets: dict) -> None:
    """A gutter ring at the dome's base, a downspout, and running water.

    A dome is a single continuous catchment: ``flow`` 0..1 drives how hard
    it is raining into the ring."""
    R = float(p.get("radius", 4.8))
    ring_r = R * float(p.get("ring_frac", 1.0))
    ring_z = float(p.get("ring_z", 0.16))
    flow = max(0.0, min(1.0, float(p.get("flow", 0.7))))
    spout_az = float(p.get("spout_az_deg", 300.0))
    segs = 40
    for i in range(segs):
        a0 = TAU * i / segs
        a1 = TAU * (i + 1) / segs
        o.cylinder((ring_r * math.cos(a0), ring_r * math.sin(a0), ring_z),
                   (ring_r * math.cos(a1), ring_r * math.sin(a1), ring_z),
                   0.09, (0.58, 0.60, 0.64, 1.0), sides=7, caps=False)
    for k in range(8):                                  # hangers
        a = TAU * k / 8
        o.cylinder((ring_r * math.cos(a), ring_r * math.sin(a), ring_z),
                   (ring_r * 0.94 * math.cos(a), ring_r * 0.94 * math.sin(a),
                    ring_z + 0.22), 0.022, STEEL, sides=5)
    sa = math.radians(spout_az)
    sx, sy = ring_r * math.cos(sa), ring_r * math.sin(sa)
    o.cylinder((sx, sy, ring_z), (sx, sy, 0.0), 0.075,
               (0.52, 0.55, 0.60, 1.0), sides=8)
    if flow > 0.02:
        for i in range(int(30 * flow)):
            u = (t * 1.4 + rnd(i, 5.0)) % 1.0
            tr.marker((sx + 0.03 * math.sin(t * 6.0 + i), sy,
                       ring_z * (1.0 - u)), 0.035,
                      (0.60, 0.82, 0.95, 0.75))
        for i in range(int(40 * flow)):                 # sheet flow on shell
            a = TAU * rnd(i, 6.0)
            u = (t * 0.9 + rnd(i, 7.0)) % 1.0
            polar = math.radians(20.0 + 68.0 * u)
            pt = np.array([R * math.sin(polar) * math.cos(a),
                           R * math.sin(polar) * math.sin(a),
                           R * math.cos(polar)])
            tr.marker(pt * 1.01, 0.028, (0.65, 0.85, 0.96, 0.5))
    targets["rain_catch"] = (np.array([0.0, 0.0, ring_z]), R * 1.25)


# ---------------------------------------------------------------------------
# Appliances and furniture
# ---------------------------------------------------------------------------

def emit_kitchen_run(o: Batch, tr: Batch, p: dict, t: float,
                     targets: dict) -> None:
    """A counter run with sink, range and refrigerator.

    ``reveal`` 0..1 brings the pieces in one at a time (counter, then the
    range, then the refrigerator), which is how a build shot shows a
    kitchen going in without a cut."""
    R = float(p.get("radius", 4.8))
    az = float(p.get("az_deg", -35.0))
    ring = R * float(p.get("ring_frac", 0.60))
    run = float(p.get("run", 2.80))
    reveal = max(0.0, min(1.0, float(p.get("reveal", 1.0))))
    a = math.radians(az)
    outward, along, _up = _tangent_basis(az)
    base = np.array([ring * math.cos(a), ring * math.sin(a), 0.0])
    counter_h = 0.92
    cab = tuple(p.get("cabinet_color", (0.62, 0.47, 0.32, 1.0)))
    if reveal > 0.02:
        o.box((base[0], base[1], counter_h * 0.5), (0.64, run, counter_h),
              cab, yaw=a)
        o.box((base[0], base[1], counter_h + 0.02), (0.70, run + 0.04, 0.05),
              (0.80, 0.81, 0.84, 1.0), yaw=a)
        sink = base - along * (run * 0.28)
        o.box((sink[0], sink[1], counter_h - 0.06), (0.44, 0.52, 0.16),
              (0.72, 0.74, 0.78, 1.0), yaw=a)
        neck = sink - outward * 0.22
        o.cylinder((neck[0], neck[1], counter_h + 0.05),
                   (neck[0], neck[1], counter_h + 0.34), 0.022, CHROME,
                   sides=6)
        o.cylinder((neck[0], neck[1], counter_h + 0.34),
                   (neck[0] + outward[0] * 0.16, neck[1] + outward[1] * 0.16,
                    counter_h + 0.32), 0.020, CHROME, sides=6)
    if reveal > 0.34:                                   # the range
        rng = base + along * (run * 0.26)
        o.box((rng[0], rng[1], counter_h * 0.5), (0.64, 0.76, counter_h),
              WHITE_GOODS, yaw=a)
        for k in range(4):
            ox = (-0.16 if k < 2 else 0.16)
            oy = (-0.18 if k % 2 == 0 else 0.18)
            burner = rng + outward * ox + along * oy
            o.disc((burner[0], burner[1], counter_h + 0.06), 0.09,
                   (0.16, 0.16, 0.18, 1.0), sides=12)
        door = rng - outward * 0.33
        o.box((door[0], door[1], counter_h * 0.42), (0.04, 0.66, 0.48),
              (0.30, 0.32, 0.36, 1.0), yaw=a)
        handle = rng - outward * 0.38
        o.cylinder((handle[0], handle[1], counter_h * 0.72),
                   (handle[0], handle[1], counter_h * 0.72), 0.02, CHROME,
                   sides=6)
        o.box((handle[0], handle[1], counter_h * 0.70), (0.05, 0.62, 0.04),
              CHROME, yaw=a)
    if reveal > 0.67:                                   # the refrigerator
        fridge = base + along * (run * 0.5 + 0.42)
        o.box((fridge[0], fridge[1], 0.90), (0.70, 0.78, 1.80),
              WHITE_GOODS, yaw=a)
        seam = fridge - outward * 0.355
        o.box((seam[0], seam[1], 1.22), (0.02, 0.76, 0.02),
              (0.62, 0.64, 0.68, 1.0), yaw=a)
        grip = fridge - outward * 0.38 + along * 0.30
        o.box((grip[0], grip[1], 1.05), (0.05, 0.05, 0.52), CHROME, yaw=a)
    targets["kitchen"] = (base + np.array([0.0, 0.0, counter_h]),
                          max(run * 0.9, R * 0.5))


def emit_furniture(o: Batch, tr: Batch, p: dict, t: float,
                   targets: dict) -> None:
    """A living set: table with chairs, and a sofa facing the middle."""
    R = float(p.get("radius", 4.8))
    az = float(p.get("az_deg", 60.0))
    ring = R * float(p.get("ring_frac", 0.42))
    chairs = int(p.get("chairs", 4))
    a = math.radians(az)
    outward, along, _up = _tangent_basis(az)
    centre = np.array([ring * math.cos(a), ring * math.sin(a), 0.0])
    table_r = float(p.get("table_r", 0.62))
    top_z = 0.74
    o.cylinder((centre[0], centre[1], top_z),
               (centre[0], centre[1], top_z + 0.05), table_r, TIMBER,
               sides=16)
    o.cylinder((centre[0], centre[1], 0.02), (centre[0], centre[1], top_z),
               0.08, (0.44, 0.33, 0.20, 1.0), sides=8)
    o.cylinder((centre[0], centre[1], 0.02), (centre[0], centre[1], 0.06),
               0.36, (0.44, 0.33, 0.20, 1.0), sides=12)
    for k in range(max(0, chairs)):
        ca = TAU * k / max(1, chairs)
        seat = centre + np.array([math.cos(ca), math.sin(ca), 0.0]) \
            * (table_r + 0.42)
        o.box((seat[0], seat[1], 0.44), (0.40, 0.40, 0.06),
              (0.58, 0.43, 0.28, 1.0), yaw=ca)
        back = seat + np.array([math.cos(ca), math.sin(ca), 0.0]) * 0.18
        o.box((back[0], back[1], 0.68), (0.05, 0.38, 0.44),
              (0.58, 0.43, 0.28, 1.0), yaw=ca)
        for lk in range(4):
            la = TAU * lk / 4 + math.pi / 4
            leg = seat + np.array([math.cos(ca + la), math.sin(ca + la),
                                   0.0]) * 0.16
            o.cylinder((leg[0], leg[1], 0.0), (leg[0], leg[1], 0.42), 0.022,
                       (0.44, 0.33, 0.20, 1.0), sides=5)
    sofa = centre - outward * (table_r + 1.30)
    fabric = tuple(p.get("sofa_color", (0.32, 0.38, 0.46, 1.0)))
    o.box((sofa[0], sofa[1], 0.22), (0.86, 1.90, 0.44), fabric, yaw=a)
    back = sofa - outward * 0.36
    o.box((back[0], back[1], 0.56), (0.16, 1.90, 0.72), fabric, yaw=a)
    for s in (-1.0, 1.0):
        arm = sofa + along * (0.95 * s)
        o.box((arm[0], arm[1], 0.38), (0.80, 0.18, 0.30), fabric, yaw=a)
    targets["furniture"] = (centre + np.array([0.0, 0.0, 0.5]),
                            max(table_r * 3.0, R * 0.55))


ACCESSORY_EMITTERS = {
    "door": emit_door,
    "window_band": emit_window_band,
    "skylight": emit_skylight,
    "wood_stove": emit_wood_stove,
    "water_tank": emit_water_tank,
    "battery_rack": emit_battery_rack,
    "mini_split": emit_mini_split,
    "loft": emit_loft,
    "deck": emit_deck,
    "rain_catch": emit_rain_catch,
    "kitchen_run": emit_kitchen_run,
    "furniture": emit_furniture,
}
