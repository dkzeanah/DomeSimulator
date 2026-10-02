"""The cover, rendered from the model instead of painted by a generator.

Image generators draw "a geodesic dome" -- single struts meeting at hubs --
and this book exists to say that is not how this one is built. So the cover
is a render. The dome in it is the raw-wedge simulator's own solved frame,
through :func:`two_v_demo.raw_wedge_bridge.world_batches`: the 120 wedge
members with their compound butt cuts, the pinwheel corners, the doubled
seams and their keys, exactly as the book's figures show them.

Around it, the scene of the painted cover is rebuilt from simple geometry,
sized from the same model wherever the model has an opinion:

* the deck is the pad from :mod:`pad_deck`, at its computed diameter;
* the log is the book's 12 in trunk, split into its eight wedges;
* the member being lifted, and the stack beside the log, are wedges of the
  same 45 degree sector at the solver's member lengths;
* the builder is :mod:`two_v_demo.figure`'s worker in the ``reach_high`` pose.

Two crown triangles are left out, because the picture is of a building going
up. Everything is rendered twice -- over black, then over white -- which
gives an exact matte, and composited over a painted sunset (sky, sun, hills,
lake) that no mesh needs to carry. Lettering is set afterwards by
:mod:`wedge_book.cover_type`.

    py -3.12 -m wedge_book.cover_scene --preview    # quarter size, quick
    py -3.12 -m wedge_book.cover_scene              # full size
"""

from __future__ import annotations

import argparse
import math
from dataclasses import dataclass
from pathlib import Path

import numpy as np
from PIL import Image, ImageFilter

import pad_deck
import seed_model
from two_v_demo import figure, raw_wedge_bridge
from two_v_demo.render_kit import (SCENE_FRAGMENT_SHADER, SCENE_VERTEX_SHADER,
                                   TriangleBatch, look_at, perspective)

from . import outline, print_edition

OUT_DIR = outline.ROOT / "book_wedge" / "cover"
IN = 0.0254  # metres per inch

# The front cover with bleed, at 300 DPI.
BLEED_IN = 0.125
FULL_W = round((print_edition.TRIM_IN[0] + BLEED_IN) * 300)
FULL_H = round((print_edition.TRIM_IN[1] + 2 * BLEED_IN) * 300)


# ----------------------------------------------------------------------
# Sizes, from the model
# ----------------------------------------------------------------------

@dataclass(frozen=True)
class Sizes:
    dome_r: float        # sphere radius of the frame, m
    deck_r: float        # circumradius of the ten-sided pad, m
    trunk_r: float       # the log, m
    splits: int
    long_member: float   # stock length of a long member, m
    short_member: float


def sizes() -> Sizes:
    model = cover_model()
    geo = seed_model.seed_geometry()
    stock = {m.edge_type: m.stock_length_in for m in geo.members}
    across_ft = pad_deck.pad_diameter_ft()
    return Sizes(
        dome_r=model.topology.sphere_radius_in * IN,
        deck_r=across_ft * 0.3048 / 2 / math.cos(math.pi / 10),
        trunk_r=COVER_TRUNK_IN * IN / 2,
        splits=int(seed_model.SEED_RADIAL_SPLITS),
        long_member=stock["A"] * IN,
        short_member=stock["B"] * IN,
    )


#: The cover's log, in inches. ARTISTIC, not the book's number: the reference
#: build is seed_model.SEED_TRUNK_DIAMETER_IN (12 in). At cover size a 12 in
#: frame reads spindly, so the cover is rendered from a larger log -- every
#: wedge, seam and pinwheel is still the solver's own geometry, solved for
#: this log, just heavier. Nothing on the cover states a size.
COVER_TRUNK_IN = 15.0

DECK_TOP = 0.62  # the pad stands on piers; its top, m above the grass

# Timber, in the palette of fresh-split pine in low sun.
PINE_FACE = (0.80, 0.58, 0.33, 1.0)     # the rounded outer face
PINE_SAWN = (0.93, 0.76, 0.50, 1.0)     # a sawn side, paler
PINE_KEY = (0.86, 0.64, 0.38, 1.0)
PINE_END = (0.95, 0.80, 0.56, 1.0)      # end grain
BARK = (0.30, 0.20, 0.13, 1.0)
BARK_DARK = (0.20, 0.13, 0.09, 1.0)
DECK = (0.66, 0.47, 0.28, 1.0)
DECK_EDGE = (0.50, 0.34, 0.20, 1.0)
CONCRETE = (0.62, 0.61, 0.58, 1.0)
HEARTWOOD = (0.84, 0.58, 0.34, 1.0)     # the darker core of the end grain

RING_SPACING_M = 0.0048
"""Scene dressing, not a figure: the gap between growth rings drawn on end
grain, about five to the inch, a fast-grown pine. It is never shown as a
number and nothing is computed from it."""


# ----------------------------------------------------------------------
# The dome: the simulator's own frame, in pine, crown unfinished
# ----------------------------------------------------------------------

def _classify(colour: np.ndarray) -> np.ndarray:
    """The simulator's diagnostic colours, mapped back to what they mean.

    Its outer faces are dark brown, the two sawn sides green and red, the
    keys gold. A printed cover wants pine, but still wants those surfaces to
    read apart, so each keeps its own shade of pine.
    """
    r, g, b = colour[:, 0], colour[:, 1], colour[:, 2]
    out = np.tile(np.array(PINE_FACE, dtype=np.float32), (len(colour), 1))
    green = g > r * 1.15
    red = (r > 0.45) & (g < 0.35) & (b < 0.35)
    gold = (r > 0.55) & (g > 0.42) & (b < 0.32) & ~green
    out[green | red] = PINE_SAWN
    out[gold] = PINE_KEY
    return out


def cover_model():
    """The solver's dome, solved for the cover's log (see COVER_TRUNK_IN)."""
    return raw_wedge_bridge.model("point_dome_in", trunk_diameter_in=COVER_TRUNK_IN)


def dome_triangles(s: Sizes) -> np.ndarray:
    """The solved meshes as (n, 3, 10) triangles in scene units -- the same
    conversion :func:`raw_wedge_bridge.world_batches` does, for this model."""
    sim = raw_wedge_bridge.simulator()
    model = cover_model()
    meshes = sim.build_world_meshes(model)
    scale = s.dome_r / model.topology.sphere_radius_in
    parts = []
    for name in ("wood", "rigid"):
        data = meshes.get(name)
        if data is None or not hasattr(data, "indices") or len(data.indices) == 0:
            continue
        vertices = np.asarray(data.vertices, dtype=np.float64)
        indices = np.asarray(data.indices, dtype=np.int64)
        v = vertices[indices]
        v[:, 0:3] = v[:, 0:3] * scale + np.array([0.0, 0.0, DECK_TOP + 0.02])
        parts.append(v[:, 0:10])
    return np.concatenate(parts).astype(np.float32).reshape(-1, 3, 10)


def dome_batch(s: Sizes, missing_faces: tuple[int, ...]) -> tuple[TriangleBatch, dict]:
    sim = raw_wedge_bridge.simulator()
    model = cover_model()
    tri = dome_triangles(s)
    centres = tri[:, :, 0:3].mean(axis=1) - np.array([0.0, 0.0, DECK_TOP + 0.02])
    faces = model.topology.faces
    face_dirs = np.array([f.center / np.linalg.norm(f.center) for f in faces])
    dirs = centres / np.maximum(np.linalg.norm(centres, axis=1, keepdims=True), 1e-9)
    owner = np.argmax(dirs @ face_dirs.T, axis=1)
    keep = ~np.isin(owner, missing_faces)
    tri = tri[keep]
    # Pine, by surface, with a little variation member to member.
    flat = tri.reshape(-1, 10)
    colours = _classify(flat[:, 6:10])
    rng = np.random.default_rng(12)
    member_shade = rng.uniform(0.92, 1.06, size=len(faces))[owner[keep]]
    colours[:, 0:3] *= np.repeat(member_shade, 3)[:, None]
    flat[:, 6:10] = np.clip(colours, 0, 1)
    batch = TriangleBatch()
    batch.vertices = flat.reshape(-1).tolist()
    info = {"triangles": len(tri), "removed": int((~keep).sum()),
            "faces": len(faces), "sim": sim}
    return batch, info


def crown_gap_faces(n: int = 2, azimuth_deg: float = -60.0) -> tuple[int, ...]:
    """The ``n`` crown triangles nearest a direction: the ones not yet up."""
    model = cover_model()
    faces = model.topology.faces
    top = max(float(f.center[2]) for f in faces)
    crown = [f for f in faces if f.center[2] > top * 0.93]
    target = math.radians(azimuth_deg)

    def off(f):
        a = math.atan2(f.center[1], f.center[0])
        return abs((a - target + math.pi) % math.tau - math.pi)
    return tuple(f.index for f in sorted(crown, key=off)[:n])


# ----------------------------------------------------------------------
# The rest of the scene
# ----------------------------------------------------------------------

def _grain_colour(fraction: float, late: bool) -> tuple:
    """Heartwood in the middle, sapwood outside, each ring's latewood darker."""
    k = min(1.0, max(0.0, (fraction - 0.42) / 0.28))
    k = k * k * (3 - 2 * k)
    rgb = [h + (e - h) * k for h, e in zip(HEARTWOOD[:3], PINE_END[:3])]
    if late:
        rgb = [c * 0.80 for c in rgb]
    return (*rgb, 1.0)


def end_grain(batch: TriangleBatch, pith, u, v, normal, radius: float,
              t0: float, t1: float, steps: int, phase: float = 0.0) -> None:
    """The sawn end of a log or a wedge: growth rings about the pith.

    The rings are circles about the tree's heart, so a wedge ripped through
    the heart shows arcs of the same rings its neighbours do. A slow wobble
    keeps them from looking turned on a lathe; it vanishes at the pith and at
    the bark so the face still meets the sides exactly.
    """
    pith, u, v, normal = (np.asarray(x, float) for x in (pith, u, v, normal))
    rings = max(3, int(radius / RING_SPACING_M))
    step = radius / rings

    def point(r: float, t: float):
        f = r / radius
        r = r * (1 + 0.06 * math.sin(3 * t + phase) * f * (1 - f))
        return pith + u * (r * math.cos(t)) + v * (r * math.sin(t))
    bands = []
    for k in range(rings):
        r0 = k * step
        bands.append((r0, r0 + step * 0.70, False))
        bands.append((r0 + step * 0.70, r0 + step, True))
    for a, b, late in bands:
        colour = _grain_colour((a + b) / 2 / radius, late)
        for j in range(steps):
            ta = t0 + (t1 - t0) * j / steps
            tb = t0 + (t1 - t0) * (j + 1) / steps
            if a <= 1e-9:
                batch.triangle(pith, point(b, ta), point(b, tb), colour, normal)
            else:
                batch.quad(point(a, ta), point(a, tb), point(b, tb), point(b, ta),
                           colour, normal)


def ring_disc(batch: TriangleBatch, centre, radius: float, steps: int = 40) -> None:
    """A cut stump's top: the whole ring pattern, facing up."""
    end_grain(batch, centre, (1.0, 0.0, 0.0), (0.0, 1.0, 0.0), (0.0, 0.0, 1.0),
              radius, 0.0, math.tau, steps, phase=0.7)


def chainsaw(batch: TriangleBatch, base) -> None:
    """A chainsaw lying on its side: powerhead, handles, bar and chain.

    Built so it reads as a saw at a glance -- the silhouette is the long bar
    with its chain and nose, the wrap-around front handle and the rear
    handle loop. The bar points along +x and sits on the saw's right (-y),
    the side a camera south of the dome looks at.
    """
    b = np.asarray(base, float)
    orange, dark = (0.93, 0.42, 0.10, 1.0), (0.13, 0.13, 0.14, 1.0)
    grey, steel = (0.40, 0.41, 0.43, 1.0), (0.76, 0.77, 0.80, 1.0)
    chain, tooth = (0.20, 0.20, 0.22, 1.0), (0.58, 0.58, 0.61, 1.0)
    red, white = (0.78, 0.10, 0.08, 1.0), (0.95, 0.95, 0.92, 1.0)

    def box(c, size, colour):
        batch.box(b + np.asarray(c, float), size, colour)

    def tube(points, radius, colour):
        for p, q in zip(points, points[1:]):
            batch.cylinder(b + np.asarray(p, float), b + np.asarray(q, float), radius, colour, 10)
            batch.sphere(b + np.asarray(q, float), radius, colour, 3, 8)
    # The powerhead: a stepped housing, the air filter cover, cooling fins.
    box((0.0, 0.0, 0.075), (0.34, 0.20, 0.15), orange)
    box((-0.02, 0.0, 0.170), (0.28, 0.17, 0.05), orange)
    box((-0.08, 0.0, 0.205), (0.15, 0.15, 0.028), dark)
    for k in range(5):
        box((0.045 + k * 0.022, 0.0, 0.205), (0.010, 0.15, 0.035), grey)
    box((-0.02, -0.1005, 0.125), (0.22, 0.002, 0.018), white)       # stripe
    box((0.19, 0.03, 0.045), (0.035, 0.11, 0.06), grey)             # muffler
    for x, z, r in ((-0.11, 0.055, 0.022), (0.02, 0.04, 0.017)):     # fuel, oil caps
        batch.cylinder(b + [x, -0.100, z], b + [x, -0.114, z], r, dark, 14)
    # Starter on the far side.
    box((-0.02, 0.105, 0.09), (0.18, 0.018, 0.13), grey)
    box((-0.02, 0.122, 0.16), (0.08, 0.02, 0.022), dark)
    # Rear handle: a closed loop behind the body, the trigger under the grip.
    tube([(-0.17, 0.0, 0.025), (-0.37, 0.0, 0.025), (-0.37, 0.0, 0.15),
          (-0.15, 0.0, 0.195)], 0.017, orange)
    batch.cylinder(b + [-0.33, 0.0, 0.16], b + [-0.19, 0.0, 0.188], 0.021, dark, 12)
    box((-0.25, 0.0, 0.150), (0.05, 0.018, 0.03), red)
    # Front handle wrapping over the top of the powerhead, and the brake.
    tube([(0.07, 0.115, 0.03), (0.07, 0.13, 0.20), (0.07, 0.07, 0.285),
          (0.07, -0.05, 0.29), (0.05, -0.12, 0.23), (0.03, -0.125, 0.12)], 0.016, dark)
    box((0.15, 0.0, 0.245), (0.014, 0.17, 0.11), dark)
    # Clutch cover, then the bar and chain on the saw's right.
    box((0.13, -0.106, 0.07), (0.13, 0.03, 0.10), dark)
    bar_y, bar_z, start, length = -0.087, 0.07, 0.10, 0.50
    end = start + length
    box((start + length / 2, bar_y, bar_z), (length, 0.013, 0.070), steel)
    batch.cylinder(b + [end, bar_y - 0.0065, bar_z], b + [end, bar_y + 0.0065, bar_z],
                   0.035, steel, 20)
    batch.cylinder(b + [end, bar_y - 0.0055, bar_z], b + [end, bar_y + 0.0055, bar_z],
                   0.042, chain, 20)
    for sign in (1, -1):
        z = bar_z + sign * 0.038
        box((start + length / 2, bar_y, z), (length, 0.011, 0.010), chain)
        for k in range(int(length / 0.03)):
            box((start + 0.015 + k * 0.03, bar_y, z + sign * 0.007),
                (0.012, 0.012, 0.007), tooth)


def wedge_prism(batch: TriangleBatch, start, end, radius: float, splits: int,
                roll: float, face=PINE_FACE, sawn=PINE_SAWN, end_c=PINE_END,
                bark: bool = False, arc_steps: int = 5, centred: bool = True,
                grain: bool = True) -> None:
    """One member: a sector of a log, point to one side, rounded face to the other."""
    start, end = np.asarray(start, float), np.asarray(end, float)
    axis = end - start
    length = np.linalg.norm(axis)
    d = axis / length
    up = np.array([0.0, 0.0, 1.0]) if abs(d[2]) < 0.9 else np.array([1.0, 0.0, 0.0])
    u = np.cross(d, up); u /= np.linalg.norm(u)
    v = np.cross(d, u)
    half = math.pi / splits
    # The section, in the (u, v) plane: the point at the origin, the arc out.
    ring = [np.zeros(2)]
    for k in range(arc_steps + 1):
        t = -half + 2 * half * k / arc_steps + roll
        ring.append(np.array([math.cos(t), math.sin(t)]) * radius)
    # A loose member turns about its own middle; a wedge still in its log
    # keeps its point on the log's axis.
    centroid = np.mean(ring, axis=0) if centred else np.zeros(2)
    pts = [(p - centroid) for p in ring]

    def at(p, base):
        return base + u * p[0] + v * p[1]
    arc_colour = BARK if bark else face
    n = len(pts)
    for i in range(n):
        a, b = pts[i], pts[(i + 1) % n]
        colour = arc_colour if 0 < i < n - 1 else sawn
        batch.quad(at(a, start), at(b, start), at(b, end), at(a, end), colour)
    for base, normal in ((start, -d), (end, d)):
        if grain:
            end_grain(batch, at(pts[0], base), u, v, normal, radius,
                      -half + roll, half + roll, max(arc_steps, 6),
                      phase=roll * 1.7)
            continue
        for i in range(1, n - 1):
            batch.triangle(at(pts[0], base), at(pts[i], base), at(pts[i + 1], base), end_c)


def deck_batch(s: Sizes) -> TriangleBatch:
    batch = TriangleBatch()
    r = s.deck_r
    corners = [np.array([r * math.cos(math.tau * k / 10 + math.pi / 10),
                         r * math.sin(math.tau * k / 10 + math.pi / 10)]) for k in range(10)]
    # Boards: strips along x, clipped to the decagon.
    width, gap = 0.14, 0.008
    apothem = r * math.cos(math.pi / 10)
    y = -apothem
    rng = np.random.default_rng(3)
    while y < apothem - width:
        yc = y + width / 2
        xs = []
        for k in range(10):
            p, q = corners[k], corners[(k + 1) % 10]
            if (p[1] - yc) * (q[1] - yc) <= 0 and p[1] != q[1]:
                t = (yc - p[1]) / (q[1] - p[1])
                xs.append(p[0] + t * (q[0] - p[0]))
        if len(xs) >= 2:
            x0, x1 = min(xs), max(xs)
            shade = rng.uniform(0.90, 1.08)
            colour = tuple(min(1.0, c * shade) for c in DECK[:3]) + (1.0,)
            batch.box(((x0 + x1) / 2, yc, DECK_TOP - 0.02), (x1 - x0, width - gap, 0.04), colour)
        y += width
    # Fascia round the rim, joists under, piers on the grass.
    for k in range(10):
        p, q = corners[k], corners[(k + 1) % 10]
        mid, span = (p + q) / 2, np.linalg.norm(q - p)
        ang = math.atan2(q[1] - p[1], q[0] - p[0])
        c, sn = math.cos(ang), math.sin(ang)
        for i in range(8):
            t = (i + 0.5) / 8 - 0.5
            cx, cy = mid[0] + c * t * span, mid[1] + sn * t * span
            batch.box((cx, cy, DECK_TOP - 0.11), (span / 8 * 1.01, 0.05, 0.16), DECK_EDGE) if abs(c) > 0.7 \
                else batch.box((cx, cy, DECK_TOP - 0.11), (0.05, span / 8 * 1.01, 0.16), DECK_EDGE)
    ring = [0.0, r * 0.55, r * 0.92]
    for radius in ring:
        count = 1 if radius == 0 else (6 if radius < r * 0.7 else 12)
        for k in range(count):
            a = math.tau * k / count + 0.2
            x, y = radius * math.cos(a), radius * math.sin(a)
            batch.box((x, y, 0.14), (0.34, 0.34, 0.28), CONCRETE)
            batch.box((x, y, (0.28 + DECK_TOP - 0.19) / 2), (0.12, 0.12, DECK_TOP - 0.19 - 0.28), DECK_EDGE)
    return batch


def ground_batch(seed: int = 5) -> TriangleBatch:
    """A hilltop: grass that falls away at the edges, so the painted valley shows."""
    batch = TriangleBatch()
    rng = np.random.default_rng(seed)
    rings, spokes, radius = 70, 260, 30.0
    def z_at(rr):
        return -0.018 * rr * rr if rr > 9 else 0.0
    grid = []
    for i in range(rings + 1):
        rr = radius * (i / rings) ** 1.4
        row = []
        for j in range(spokes):
            a = math.tau * j / spokes
            jitter = rng.normal(0, 0.03)
            row.append(np.array([rr * math.cos(a), rr * math.sin(a), z_at(rr) + jitter * (rr > 1)]))
        grid.append(row)
    for i in range(rings):
        for j in range(spokes):
            a, b = grid[i][j], grid[i][(j + 1) % spokes]
            c, d = grid[i + 1][(j + 1) % spokes], grid[i + 1][j]
            ang = math.tau * j / spokes
            rr = radius * (i / rings) ** 1.4
            tone = 0.5 + 0.28 * math.sin(rr * 1.7 + ang * 5) * math.cos(rr * 0.9 - ang * 3)
            tone = min(1.0, max(0.0, tone + rng.normal(0, 0.10)))
            green = np.array([0.40, 0.46, 0.17]) * (1 - tone) + np.array([0.74, 0.64, 0.28]) * tone
            green *= rng.uniform(0.94, 1.05)
            col = (float(green[0]), float(green[1]), float(green[2]), 1.0)
            if np.linalg.norm(c - a) > 1e-6:
                batch.quad(a, b, c, d, col, np.array([0, 0, 1.0]))
    return batch


def pine(batch: TriangleBatch, x: float, y: float, height: float, rng) -> None:
    ground = -0.018 * (x * x + y * y) if (x * x + y * y) > 81 else 0.0
    trunk_r = height * 0.018
    batch.cylinder((x, y, ground - 0.3), (x, y, ground + height * 0.85), trunk_r,
                   (0.30, 0.19, 0.12, 1.0), 7)
    tiers = int(rng.integers(6, 9))
    for k in range(tiers):
        t = k / tiers
        base = ground + height * (0.25 + 0.70 * t)
        radius = height * (0.22 * (1 - t) + 0.04)
        tip = base + height * 0.20
        shade = rng.uniform(0.75, 1.15)
        colour = (0.12 * shade, 0.24 * shade, 0.12 * shade, 1.0)
        sides = 9
        for i in range(sides):
            a0, a1 = math.tau * i / sides, math.tau * (i + 1) / sides
            p0 = np.array([x + radius * math.cos(a0), y + radius * math.sin(a0), base])
            p1 = np.array([x + radius * math.cos(a1), y + radius * math.sin(a1), base])
            batch.triangle(np.array([x, y, tip]), p0, p1, colour)


def forest(seed: int = 9, sites: list | None = None) -> TriangleBatch:
    """Pines round the clearing, tall and close at the sides, as in the painting.

    ``sites``, if given, receives each pine's (x, y, height) -- what a camera
    needs to keep out of, and to see past."""
    batch = TriangleBatch()
    rng = np.random.default_rng(seed)
    placed = 0
    while placed < 70:
        x, y = rng.uniform(-28, 28), rng.uniform(-14, 26)
        # The camera looks up +y from about y = -12: keep a corridor clear
        # in front of it, and the valley behind the dome mostly open.
        if abs(x) < 7.5 + max(0.0, y) * 0.35:
            continue
        if math.hypot(x, y) < 9:
            continue
        height = rng.uniform(10, 18)
        pine(batch, x, y, height, rng)
        if sites is not None:
            sites.append((x, y, height))
        placed += 1
    return batch


def props(s: Sizes, camera_side: np.ndarray) -> TriangleBatch:
    """The log, its wedges, the stump and saw, the stack, the chips."""
    batch = TriangleBatch()
    rng = np.random.default_rng(21)
    R = s.trunk_r
    # The log: lying across the foreground left, its split end toward the camera.
    log_start = np.array([-0.55, -6.35, R])
    log_dir = np.array([-0.18, 1.0, 0.0]); log_dir /= np.linalg.norm(log_dir)
    log_end = log_start + log_dir * 1.35
    # The unsplit length of trunk, in bark.
    body = TriangleBatch()
    body.cylinder(log_start + log_dir * 0.45, log_end, R, BARK, 18)
    batch.vertices.extend(body.vertices)
    # The split end: eight sectors, opened slightly.
    for k in range(s.splits):
        if k == 5:
            continue
        roll = math.tau * k / s.splits
        # Sector offset outward a touch, where the rip cuts opened the splits --
        # in the same (u, v) frame wedge_prism builds its section in.
        u = np.cross(log_dir, [0, 0, 1.0]); u /= np.linalg.norm(u)
        v = np.cross(log_dir, u)
        shift = (u * math.cos(roll) + v * math.sin(roll)) * 0.010
        wedge_prism(batch, log_start + shift, log_start + log_dir * 0.47 + shift,
                    R, s.splits, roll, bark=True, centred=False, arc_steps=8)
    # The wedge that has come out, lying in front of the log.
    out_start = log_start + np.array([0.28, -0.12, -R + 0.05])
    wedge_prism(batch, out_start, out_start + np.array([0.42, 0.55, 0.0]),
                R, s.splits, math.pi / 2, bark=True)
    # The stump and the chainsaw on it.
    stump = np.array([-1.55, -4.55, 0.0])
    batch.cylinder(stump, stump + [0, 0, 0.42], 0.30, BARK, 16)
    ring_disc(batch, stump + [0, 0, 0.421], 0.29)
    chainsaw(batch, stump + np.array([-0.06, 0.02, 0.422]))
    # The stack of members: triangular ends toward the camera, alternating.
    stack_base = np.array([1.45, -6.55, 0.0])
    stack_dir = np.array([0.95, 1.0, 0.0]); stack_dir /= np.linalg.norm(stack_dir)
    side = np.cross(stack_dir, [0, 0, 1.0]); side /= np.linalg.norm(side)
    chord = 2 * R * math.sin(math.pi / s.splits)
    for layer in range(3):
        count = 4 - (layer % 2)
        for i in range(count):
            offset = side * ((i - (count - 1) / 2) * chord * 1.02) + np.array([0, 0, R * 0.55 + layer * R * 0.95])
            roll = math.pi / 2 if (i + layer) % 2 == 0 else -math.pi / 2
            length = s.long_member if (i + layer) % 3 else s.short_member
            a = stack_base + offset
            wedge_prism(batch, a, a + stack_dir * length, R, s.splits, roll)
    # Chips and curls, scattered from the log toward the deck.
    for _ in range(260):
        t = rng.uniform()
        centre = log_start * (1 - t) + np.array([0.2, -4.2, 0.0]) * t
        p = centre + np.array([rng.normal(0, 0.30 + t * 0.5), rng.normal(0, 0.25 + t * 0.4), 0.0])
        size = rng.uniform(0.015, 0.05)
        shade = rng.uniform(0.85, 1.1)
        batch.box((p[0], p[1], 0.012), (size, size * 0.45, 0.012),
                  (min(1, 0.95 * shade), min(1, 0.80 * shade), min(1, 0.58 * shade), 1.0))
    return batch


def builder(s: Sizes, gap_dir: np.ndarray) -> TriangleBatch:
    """The worker from the films, reaching up with a member for the gap."""
    batch = TriangleBatch()
    joints = figure.joint_positions(figure.POSES["reach_high"], 1.80)
    stand = np.array(gap_dir[:2]) * s.dome_r * 0.42
    yaw = math.degrees(math.atan2(gap_dir[1], gap_dir[0]))
    placed = figure.place_figure(joints, (stand[0], stand[1], DECK_TOP), yaw)
    figure.draw_figure(batch, placed, skin=(0.84, 0.62, 0.46, 1.0),
                       hi_vis=(0.60, 0.13, 0.10, 1.0), trousers=(0.20, 0.27, 0.42, 1.0),
                       helmet=(0.33, 0.30, 0.22, 1.0))
    grip = figure.grip_point(placed)
    # The member rises from his hands toward the unfinished crown.
    towards = np.array([gap_dir[0] * s.dome_r * 0.62, gap_dir[1] * s.dome_r * 0.62,
                        DECK_TOP + s.dome_r * 0.93])
    d = towards - grip; d /= np.linalg.norm(d)
    start = grip - d * s.long_member * 0.35
    wedge_prism(batch, start, start + d * s.long_member, s.trunk_r, s.splits, math.pi / 2)
    return batch


# ----------------------------------------------------------------------
# Render
# ----------------------------------------------------------------------

@dataclass
class Camera:
    eye: tuple = (0.50, -10.4, 1.55)
    target: tuple = (0.10, -1.0, 1.62)
    fov: float = 51.0


LIGHT = (0.55, 0.70, -0.45)   # sun low on the left, a little behind the camera


def render_rgba(batches: list[TriangleBatch], width: int, height: int, cam: Camera,
                samples: int = 8) -> np.ndarray:
    """Render twice -- over black and over white -- and return RGBA with an exact matte."""
    import moderngl

    ctx = moderngl.create_standalone_context()
    program = ctx.program(vertex_shader=SCENE_VERTEX_SHADER, fragment_shader=SCENE_FRAGMENT_SHADER)
    data = np.concatenate([np.asarray(b.vertices, dtype="f4") for b in batches if b.vertices])
    vbo = ctx.buffer(data.tobytes())
    vao = ctx.vertex_array(program, [(vbo, "3f 3f 4f", "in_position", "in_normal", "in_color")])
    ms = ctx.framebuffer(color_attachments=[ctx.renderbuffer((width, height), samples=samples)],
                         depth_attachment=ctx.depth_renderbuffer((width, height), samples=samples))
    out = ctx.framebuffer(color_attachments=[ctx.texture((width, height), 4)])
    eye, target = np.array(cam.eye, float), np.array(cam.target, float)
    mvp = perspective(cam.fov, width / height, 0.1, 400.0) @ look_at(eye, target)
    program["u_mvp"].write(np.ascontiguousarray(mvp.T).astype("f4").tobytes())
    program["u_camera"].value = tuple(float(v) for v in eye)
    program["u_light"].value = LIGHT
    shots = []
    for clear in (0.0, 1.0):
        ms.use()
        ctx.enable(moderngl.DEPTH_TEST)
        ctx.clear(clear, clear, clear, 1.0)
        vao.render()
        ctx.copy_framebuffer(out, ms)
        raw = np.frombuffer(out.read(components=4), dtype=np.uint8).reshape(height, width, 4)
        shots.append(np.flipud(raw[:, :, :3]).astype(np.float32) / 255.0)
    ctx.release()
    black, white = shots
    alpha = np.clip(1.0 - (white - black).mean(axis=2), 0.0, 1.0)
    colour = np.where(alpha[..., None] > 1e-3, black / np.maximum(alpha[..., None], 1e-3), 0.0)
    return np.dstack([np.clip(colour, 0, 1), alpha])


def horizon_row(cam: Camera, width: int, height: int) -> float:
    eye, target = np.array(cam.eye, float), np.array(cam.target, float)
    forward = target - eye
    level = np.array([forward[0], forward[1], 0.0]); level /= np.linalg.norm(level)
    far = eye + level * 1000.0
    mvp = perspective(cam.fov, width / height, 0.1, 4000.0) @ look_at(eye, target)
    clip = mvp @ np.array([*far, 1.0])
    ndc_y = clip[1] / clip[3]
    return (1 - (ndc_y * 0.5 + 0.5)) * height


def backdrop(width: int, height: int, horizon: float, seed: int = 2) -> np.ndarray:
    """The sunset, painted: sky, sun, hills in haze, and a lake."""
    rng = np.random.default_rng(seed)
    y = np.arange(height, dtype=np.float32)[:, None] / height
    x = np.arange(width, dtype=np.float32)[None, :] / width
    h = horizon / height
    top, mid, low, glow = (np.array(c, np.float32) for c in (
        (0.20, 0.38, 0.66), (0.62, 0.66, 0.78), (1.00, 0.70, 0.40), (1.00, 0.86, 0.58)))
    t = np.clip(y / max(h, 1e-3), 0, 1)[..., None]
    sky = np.where(t < 0.55, top + (mid - top) * (t / 0.55),
                   np.where(t < 0.85, mid + (low - mid) * ((t - 0.55) / 0.30),
                            low + (glow - low) * ((t - 0.85) / 0.15)))
    sky = np.broadcast_to(sky, (height, width, 3)).copy()
    # The sun, low on the left, and its glow.
    sx, sy = 0.14, h - 0.035
    d = np.sqrt(((x - sx) * width / height) ** 2 + (y - sy) ** 2)
    sky += (np.exp(-(d / 0.018) ** 2) * 1.2)[..., None] * np.array([1.0, 0.95, 0.80])
    sky += (np.exp(-(d / 0.20) ** 2) * 0.55)[..., None] * np.array([1.0, 0.72, 0.38])
    # Streaks of cloud.
    for k in range(9):
        cy = h * rng.uniform(0.30, 0.82)
        thick = rng.uniform(0.004, 0.012)
        cx, span = rng.uniform(0.1, 0.9), rng.uniform(0.15, 0.45)
        band = (np.exp(-((y - cy) / thick) ** 2) * np.exp(-((x - cx) / span) ** 2)
                * (0.6 + 0.4 * np.sin(x * rng.uniform(20, 40) + rng.uniform(0, 6))))
        sky += (band * 0.16)[..., None] * np.array([1.0, 0.66, 0.56])
    img = sky
    # Hills: four ridges, farthest palest.
    ridge_cols = [(0.62, 0.52, 0.62), (0.48, 0.42, 0.55), (0.33, 0.32, 0.42), (0.22, 0.25, 0.28)]
    xs = np.arange(width) / width
    for k, col in enumerate(ridge_cols):
        base = h - 0.004 + 0.012 * k
        amp = 0.018 + 0.012 * k
        ridge = np.full(width, base, dtype=np.float64)
        for octave in range(6):
            f = (2 + k) * 2 ** octave
            ridge -= (amp * 0.45 ** octave * np.sin(xs * f * math.pi + rng.uniform(0, 6))
                      * (0.7 + 0.3 * np.sin(xs * f * 0.37 + rng.uniform(0, 6))))
        mask = y >= ridge[None, :]
        img = np.where(mask[..., None], np.array(col, np.float32), img)
        if k == 1:
            # The lake, between the second and third ridges, with the sun on it.
            lake_top = ridge + 0.006
            lake = (y >= lake_top[None, :]) & (y < lake_top[None, :] + 0.03) & (x < 0.62)
            water = np.array([0.95, 0.72, 0.48], np.float32)
            shimmer = np.exp(-((x - sx) / 0.05) ** 2)[..., None] * 0.3
            img = np.where(lake[..., None], water * 0.85 + shimmer, img)
    return np.clip(img, 0, 1)


def grade(img: np.ndarray) -> np.ndarray:
    """Golden hour: warm the mids, lift the lows a little, and a soft vignette."""
    h, w, _ = img.shape
    img = img * np.array([1.06, 1.0, 0.90])
    img = img ** 0.94
    y, x = np.mgrid[0:h, 0:w]
    r = np.sqrt(((x - w / 2) / (w / 2)) ** 2 + ((y - h * 0.45) / (h / 2)) ** 2)
    img *= (1 - 0.22 * np.clip(r - 0.55, 0, 1))[..., None]
    return np.clip(img, 0, 1)


def render(width: int, height: int, cam: Camera | None = None) -> tuple[Image.Image, dict]:
    cam = cam or Camera()
    s = sizes()
    eye = np.array(cam.eye)
    # The crown gap faces the camera's right, where the builder reaches.
    toward_camera = math.degrees(math.atan2(eye[1], eye[0]))
    gap_faces = crown_gap_faces(2, toward_camera + 40)
    dome, info = dome_batch(s, gap_faces)
    model = cover_model()
    gap_centre = np.mean([model.topology.faces[i].center for i in gap_faces], axis=0)
    gap_dir = np.array([gap_centre[0], gap_centre[1], 0.0]); gap_dir /= np.linalg.norm(gap_dir)
    batches = [ground_batch(), deck_batch(s), dome, builder(s, gap_dir),
               props(s, eye), forest()]
    rgba = render_rgba(batches, width, height, cam)
    sky = backdrop(width, height, horizon_row(cam, width, height))
    alpha = rgba[..., 3:4]
    img = rgba[..., :3] * alpha + sky * (1 - alpha)
    img = grade(img)
    out = Image.fromarray((img * 255).astype(np.uint8))
    return out, {"sizes": s, "gap_faces": gap_faces, **{k: v for k, v in info.items() if k != "sim"}}


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--preview", action="store_true")
    parser.add_argument("--out", default="")
    args = parser.parse_args(argv)
    w, h = (FULL_W // 4, FULL_H // 4) if args.preview else (FULL_W, FULL_H)
    image, info = render(w, h)
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    path = Path(args.out) if args.out else OUT_DIR / ("scene-preview.png" if args.preview else "scene.png")
    image.save(path)
    print(path, image.size, info["gap_faces"], f"{info['triangles']} dome triangles, "
          f"{info['removed']} left out for the unfinished crown")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
