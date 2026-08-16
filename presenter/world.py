"""Parametric, animatable world objects and environment composition.

Everything is a pure function of (params, absolute time t), so the same
frame renders identically in live preview and export. Geometry goes into
CPU triangle batches (position, normal, rgba) that the engine uploads
each frame.
"""

from __future__ import annotations

import math

import numpy as np

from two_v_demo.geometry import build_demo_geometry, normalize
from .prompt import EnvironmentSpec

TAU = math.tau


def rnd(i: float, salt: float = 0.0) -> float:
    """Deterministic pseudo-random in [0, 1)."""
    return (math.sin(i * 127.1 + salt * 311.7) * 43758.5453) % 1.0


def _rotate_about(point, pivot, axis, angle):
    """Rotate ``point`` by ``angle`` radians around the line through
    ``pivot`` parallel to ``axis`` (Rodrigues' rotation formula)."""
    axis = normalize(np.asarray(axis, dtype=np.float64))
    p = np.asarray(point, dtype=np.float64) - np.asarray(pivot, dtype=np.float64)
    ca, sa = math.cos(angle), math.sin(angle)
    rotated = (p * ca + np.cross(axis, p) * sa
               + axis * np.dot(axis, p) * (1.0 - ca))
    return np.asarray(pivot, dtype=np.float64) + rotated


class Batch:
    __slots__ = ("v",)

    def __init__(self) -> None:
        self.v: list[float] = []

    # -- primitives ------------------------------------------------------

    def tri(self, a, b, c, color, normal=None) -> None:
        if normal is None:
            u = np.subtract(b, a)
            w = np.subtract(c, a)
            n = np.cross(u, w)
            ln = float(np.linalg.norm(n))
            normal = n / ln if ln > 1e-12 else (0.0, 0.0, 1.0)
        r, g, bl, al = color
        nx, ny, nz = float(normal[0]), float(normal[1]), float(normal[2])
        for p in (a, b, c):
            self.v.extend((float(p[0]), float(p[1]), float(p[2]),
                           nx, ny, nz, r, g, bl, al))

    def quad(self, a, b, c, d, color, normal=None) -> None:
        self.tri(a, b, c, color, normal)
        self.tri(a, c, d, color, normal)

    def cylinder(self, start, end, radius, color, sides=8,
                 radius2=None, caps=True) -> None:
        start = np.asarray(start, dtype=np.float64)
        end = np.asarray(end, dtype=np.float64)
        axis = end - start
        length = float(np.linalg.norm(axis))
        if length < 1e-9:
            return
        axis /= length
        helper = np.array([0.0, 0.0, 1.0])
        if abs(float(np.dot(axis, helper))) > 0.92:
            helper = np.array([0.0, 1.0, 0.0])
        u = normalize(np.cross(axis, helper))
        w = normalize(np.cross(axis, u))
        r2 = radius if radius2 is None else radius2
        ring0 = []
        ring1 = []
        for i in range(sides):
            angle = TAU * i / sides
            d = u * math.cos(angle) + w * math.sin(angle)
            ring0.append((start + d * radius, d))
            ring1.append((end + d * r2, d))
        for i in range(sides):
            j = (i + 1) % sides
            p0, n0 = ring0[i]
            p1, n1 = ring0[j]
            p2, n2 = ring1[j]
            p3, n3 = ring1[i]
            self.tri(p0, p1, p2, color, n0)
            self.tri(p0, p2, p3, color, n3)
        if caps:
            for center, ring, sign in ((start, ring0, -1), (end, ring1, 1)):
                cap_n = axis * sign
                for i in range(sides):
                    j = (i + 1) % sides
                    if sign > 0:
                        self.tri(center, ring[i][0], ring[j][0], color, cap_n)
                    else:
                        self.tri(center, ring[j][0], ring[i][0], color, cap_n)

    def cone(self, base, tip, radius, color, sides=10) -> None:
        self.cylinder(base, tip, radius, color, sides=sides, radius2=0.001,
                      caps=True)

    def box(self, center, size, color, yaw=0.0) -> None:
        cx, cy, cz = center
        hx, hy, hz = size[0] * 0.5, size[1] * 0.5, size[2] * 0.5
        ca, sa = math.cos(yaw), math.sin(yaw)

        def pt(x, y, z):
            return (cx + x * ca - y * sa, cy + x * sa + y * ca, cz + z)

        def nv(x, y, z):
            return (x * ca - y * sa, x * sa + y * ca, z)
        self.quad(pt(-hx, -hy, hz), pt(hx, -hy, hz), pt(hx, hy, hz),
                  pt(-hx, hy, hz), color, nv(0, 0, 1))
        self.quad(pt(-hx, hy, -hz), pt(hx, hy, -hz), pt(hx, -hy, -hz),
                  pt(-hx, -hy, -hz), color, nv(0, 0, -1))
        self.quad(pt(hx, -hy, -hz), pt(hx, hy, -hz), pt(hx, hy, hz),
                  pt(hx, -hy, hz), color, nv(1, 0, 0))
        self.quad(pt(-hx, hy, -hz), pt(-hx, -hy, -hz), pt(-hx, -hy, hz),
                  pt(-hx, hy, hz), color, nv(-1, 0, 0))
        self.quad(pt(hx, hy, -hz), pt(-hx, hy, -hz), pt(-hx, hy, hz),
                  pt(hx, hy, hz), color, nv(0, 1, 0))
        self.quad(pt(-hx, -hy, -hz), pt(hx, -hy, -hz), pt(hx, -hy, hz),
                  pt(-hx, -hy, hz), color, nv(0, -1, 0))

    def disc(self, center, radius, color, sides=24, z_normal=1.0) -> None:
        cx, cy, cz = center
        n = (0.0, 0.0, 1.0 if z_normal >= 0 else -1.0)
        for i in range(sides):
            a0 = TAU * i / sides
            a1 = TAU * (i + 1) / sides
            p0 = (cx + radius * math.cos(a0), cy + radius * math.sin(a0), cz)
            p1 = (cx + radius * math.cos(a1), cy + radius * math.sin(a1), cz)
            if z_normal >= 0:
                self.tri(center, p0, p1, color, n)
            else:
                self.tri(center, p1, p0, color, n)

    def blob(self, center, radius, color, squash=1.0, seed=0.0) -> None:
        """Low-poly rock: perturbed octahedron subdivided once."""
        c = np.asarray(center, dtype=np.float64)
        pts = [np.array(p) for p in
               ((1, 0, 0), (-1, 0, 0), (0, 1, 0), (0, -1, 0),
                (0, 0, 1), (0, 0, -1))]
        faces = ((0, 2, 4), (2, 1, 4), (1, 3, 4), (3, 0, 4),
                 (2, 0, 5), (1, 2, 5), (3, 1, 5), (0, 3, 5))
        for fi, (a, b, d) in enumerate(faces):
            def wob(p, k):
                s = 0.75 + 0.5 * rnd(fi * 3.1 + k, seed)
                q = normalize(p) * radius * s
                return c + np.array([q[0], q[1], q[2] * 0.55 * squash])
            self.tri(wob(pts[a], 0), wob(pts[b], 1), wob(pts[d], 2), color)

    def marker(self, center, size, color) -> None:
        """Small octahedron glow-dot (used for particles)."""
        cx, cy, cz = center
        s = size
        top = (cx, cy, cz + s)
        bot = (cx, cy, cz - s)
        ring = ((cx + s, cy, cz), (cx, cy + s, cz), (cx - s, cy, cz),
                (cx, cy - s, cz))
        for i in range(4):
            j = (i + 1) % 4
            self.tri(top, ring[i], ring[j], color)
            self.tri(bot, ring[j], ring[i], color)


# ---------------------------------------------------------------------------
# Skies / palettes
# ---------------------------------------------------------------------------

SKIES = {
    "day":   {"clear": (0.55, 0.71, 0.86), "fog": (0.62, 0.74, 0.85),
              "light": (-0.45, -0.55, -0.72), "fogd": 0.006},
    "dusk":  {"clear": (0.32, 0.24, 0.36), "fog": (0.55, 0.36, 0.34),
              "light": (-0.75, -0.30, -0.42), "fogd": 0.010},
    "storm": {"clear": (0.16, 0.19, 0.24), "fog": (0.24, 0.27, 0.32),
              "light": (-0.35, -0.45, -0.80), "fogd": 0.016},
    "night": {"clear": (0.03, 0.05, 0.10), "fog": (0.05, 0.08, 0.14),
              "light": (-0.25, -0.35, -0.88), "fogd": 0.012},
}

TERRAIN_COLORS = {
    "grass": (0.24, 0.36, 0.20, 1.0),
    "sand":  (0.72, 0.62, 0.42, 1.0),
    "snow":  (0.88, 0.90, 0.94, 1.0),
    "rock":  (0.42, 0.41, 0.40, 1.0),
}


# ---------------------------------------------------------------------------
# Environment emitters
# ---------------------------------------------------------------------------

def _emit_terrain(o: Batch, env: EnvironmentSpec) -> None:
    base = TERRAIN_COLORS.get(env.terrain, TERRAIN_COLORS["grass"])
    rings = 7
    r_out = 90.0
    for k in range(rings):
        r0 = r_out * k / rings
        r1 = r_out * (k + 1) / rings
        shade = 1.0 - 0.05 * (k % 2)
        color = (base[0] * shade, base[1] * shade, base[2] * shade, 1.0)
        sides = 40
        for i in range(sides):
            a0 = TAU * i / sides
            a1 = TAU * (i + 1) / sides
            p00 = (r0 * math.cos(a0), r0 * math.sin(a0), -0.02)
            p01 = (r0 * math.cos(a1), r0 * math.sin(a1), -0.02)
            p11 = (r1 * math.cos(a1), r1 * math.sin(a1), -0.02)
            p10 = (r1 * math.cos(a0), r1 * math.sin(a0), -0.02)
            o.quad(p00, p01, p11, p10, color, (0, 0, 1))


def _emit_water(o: Batch, tr: Batch, env: EnvironmentSpec, t: float) -> None:
    if env.water == "none":
        return
    if env.water == "lake":
        center = np.array([16.0, -14.0, 0.0])
        radius = 12.0
    else:                                  # ocean: broad field to one side
        center = np.array([34.0, 0.0, 0.0])
        radius = 42.0
    if env.shoreline:
        ring = Batch.disc
        sand = (0.80, 0.71, 0.50, 1.0)
        o.disc((center[0], center[1], 0.005), radius + 3.0, sand, sides=36)
    blue = (0.14, 0.34, 0.48, 0.88)
    sides = 36
    rings = 6
    for k in range(rings):
        r0 = radius * k / rings
        r1 = radius * (k + 1) / rings
        for i in range(sides):
            a0 = TAU * i / sides
            a1 = TAU * (i + 1) / sides

            def wp(r, a):
                x = center[0] + r * math.cos(a)
                y = center[1] + r * math.sin(a)
                z = 0.05 + 0.06 * math.sin(a * 3.0 + t * 1.4 + r * 0.35)
                return (x, y, z)
            tr.quad(wp(r0, a0), wp(r0, a1), wp(r1, a1), wp(r1, a0), blue,
                    (0, 0, 1))


def _emit_tsunami(tr: Batch, env: EnvironmentSpec, t: float) -> None:
    if not env.tsunami:
        return
    # a looping wall of water sweeping in from the ocean side
    cycle = 14.0
    u = (t % cycle) / cycle
    dist = 70.0 - 52.0 * u
    height = 3.0 + 7.0 * u
    color = (0.16, 0.38, 0.50, 0.82)
    foam = (0.92, 0.96, 0.98, 0.9)
    arc = math.radians(70.0)
    segs = 26
    for i in range(segs):
        f0 = -arc / 2 + arc * i / segs
        f1 = -arc / 2 + arc * (i + 1) / segs

        def base(a):
            return (dist * math.cos(a), dist * math.sin(a), 0.0)

        def crest(a):
            lean = 4.0 * u
            return (dist * math.cos(a) - lean, dist * math.sin(a), height)
        tr.quad(base(f0), base(f1), crest(f1), crest(f0), color)
        c0, c1 = crest(f0), crest(f1)
        tr.quad(c0, c1, (c1[0] - 1.2, c1[1], c1[2] + 0.5),
                (c0[0] - 1.2, c0[1], c0[2] + 0.5), foam)


def _emit_tornado(o: Batch, tr: Batch, env: EnvironmentSpec,
                  t: float) -> None:
    if not env.tornado:
        return
    cx, cy = -34.0, 22.0
    height = 26.0
    layers = 14
    color = (0.35, 0.34, 0.38, 0.55)
    for k in range(layers):
        z0 = height * k / layers
        z1 = height * (k + 1) / layers
        r0 = 1.2 + 7.5 * (k / layers) ** 1.6
        r1 = 1.2 + 7.5 * ((k + 1) / layers) ** 1.6
        off0 = 1.6 * math.sin(t * 1.1 + k * 0.7)
        off1 = 1.6 * math.sin(t * 1.1 + (k + 1) * 0.7)
        sides = 14
        spin = t * 2.6 + k * 0.5
        for i in range(sides):
            a0 = TAU * i / sides + spin
            a1 = TAU * (i + 1) / sides + spin
            p00 = (cx + off0 + r0 * math.cos(a0), cy + r0 * math.sin(a0), z0)
            p01 = (cx + off0 + r0 * math.cos(a1), cy + r0 * math.sin(a1), z0)
            p11 = (cx + off1 + r1 * math.cos(a1), cy + r1 * math.sin(a1), z1)
            p10 = (cx + off1 + r1 * math.cos(a0), cy + r1 * math.sin(a0), z1)
            tr.quad(p00, p01, p11, p10, color)
    for i in range(26):                     # orbiting debris
        u = rnd(i, 3.3)
        z = 1.0 + 20.0 * rnd(i, 7.1)
        r = 2.5 + 8.0 * rnd(i, 1.9)
        a = TAU * u + t * (1.8 + rnd(i, 5.5))
        p = (cx + 1.6 * math.sin(t * 1.1 + z * 0.5) + r * math.cos(a),
             cy + r * math.sin(a), z)
        o.marker(p, 0.16 + 0.2 * rnd(i, 9.7), (0.28, 0.24, 0.20, 1.0))


def _emit_weather(tr: Batch, env: EnvironmentSpec, t: float) -> None:
    if env.weather == "snow":
        for i in range(230):
            u = rnd(i, 1.0)
            fall = ((t * (0.6 + 0.5 * rnd(i, 2.0)) * 1.6) + u * 12.0) % 12.0
            z = 12.0 - fall
            r = 26.0 * math.sqrt(rnd(i, 3.0))
            a = TAU * rnd(i, 4.0) + 0.3 * math.sin(t + i)
            p = (r * math.cos(a) + 0.8 * math.sin(t * 0.8 + i),
                 r * math.sin(a), z)
            tr.marker(p, 0.055, (0.96, 0.97, 1.0, 0.9))
    elif env.weather in ("rain", "storm"):
        for i in range(180):
            u = rnd(i, 6.0)
            fall = (t * 16.0 + u * 14.0) % 14.0
            z = 14.0 - fall
            r = 26.0 * math.sqrt(rnd(i, 7.0))
            a = TAU * rnd(i, 8.0)
            x, y = r * math.cos(a), r * math.sin(a)
            tr.quad((x, y, z), (x + 0.03, y, z), (x + 0.03, y, z - 0.7),
                    (x, y, z - 0.7), (0.55, 0.65, 0.80, 0.55))


def _emit_flora(o: Batch, env: EnvironmentSpec) -> None:
    def palm(x, y, seed):
        h = 4.5 + 2.0 * rnd(seed, 1.0)
        lean_a = TAU * rnd(seed, 2.0)
        segs = 5
        base = np.array([x, y, 0.0])
        tip = base.copy()
        for k in range(segs):
            nxt = tip + np.array([
                math.cos(lean_a) * 0.22 * k, math.sin(lean_a) * 0.22 * k,
                h / segs])
            o.cylinder(tip, nxt, 0.16 - 0.02 * k, (0.45, 0.34, 0.22, 1.0),
                       sides=6)
            tip = nxt
        for f in range(6):
            a = TAU * f / 6 + rnd(seed, 3.0)
            end = tip + np.array([math.cos(a) * 2.2, math.sin(a) * 2.2, -0.9])
            mid = tip + np.array([math.cos(a) * 1.1, math.sin(a) * 1.1, 0.35])
            side = np.array([-math.sin(a), math.cos(a), 0.0]) * 0.30
            o.tri(tip + side, tip - side, mid, (0.16, 0.42, 0.20, 1.0))
            o.tri(mid + side * 0.7, mid - side * 0.7, end,
                  (0.14, 0.38, 0.18, 1.0))

    def cactus(x, y, seed):
        h = 2.0 + 1.6 * rnd(seed, 1.0)
        green = (0.23, 0.42, 0.24, 1.0)
        o.cylinder((x, y, 0), (x, y, h), 0.22, green, sides=7)
        for s in (-1, 1):
            if rnd(seed, 2.0 + s) > 0.35:
                zj = h * (0.35 + 0.2 * rnd(seed, 3.0 + s))
                o.cylinder((x, y, zj), (x + 0.55 * s, y, zj), 0.13, green,
                           sides=6)
                o.cylinder((x + 0.55 * s, y, zj),
                           (x + 0.55 * s, y, zj + 0.8), 0.13, green, sides=6)

    def pine(x, y, seed):
        h = 3.5 + 2.5 * rnd(seed, 1.0)
        o.cylinder((x, y, 0), (x, y, h * 0.4), 0.14, (0.34, 0.24, 0.15, 1.0),
                   sides=6)
        for k in range(3):
            z0 = h * (0.25 + 0.22 * k)
            o.cone((x, y, z0), (x, y, z0 + h * 0.42),
                   (1.5 - 0.35 * k) * (0.7 + 0.4 * rnd(seed, 2.0)),
                   (0.12, 0.30, 0.16, 1.0), sides=9)

    def place(count, fn, salt):
        for i in range(count):
            a = TAU * rnd(i, salt)
            r = 16.0 + 46.0 * rnd(i, salt + 1.0)
            x, y = r * math.cos(a), r * math.sin(a)
            if x > 20.0 and abs(y) < 30.0:      # keep the waterline clear
                x = -x
            fn(x, y, i * 1.7 + salt)

    place(env.palms, palm, 11.0)
    place(env.cacti, cactus, 23.0)
    place(env.pines, pine, 37.0)
    for i in range(env.rocks):
        a = TAU * rnd(i, 51.0)
        r = 14.0 + 40.0 * rnd(i, 52.0)
        o.blob((r * math.cos(a), r * math.sin(a), 0.2),
               0.7 + 1.5 * rnd(i, 53.0), (0.45, 0.43, 0.41, 1.0),
               squash=0.9, seed=i * 0.7)


# ---------------------------------------------------------------------------
# The star objects: 2V dome, perimeter plenum, blower, airflow
# ---------------------------------------------------------------------------

CYAN = (0.15, 0.82, 1.00, 1.0)
AMBER = (1.00, 0.67, 0.20, 1.0)
GREEN = (0.32, 0.91, 0.58, 1.0)

_GEO = None


def _geo():
    global _GEO
    if _GEO is None:
        _GEO = build_demo_geometry()
    return _GEO


def emit_dome(o: Batch, tr: Batch, p: dict, t: float, targets: dict) -> None:
    geo = _geo()
    R = float(p.get("radius", 4.8))
    strut_r = float(p.get("strut", 0.055))
    skin_alpha = float(p.get("skin_alpha", 0.16))
    short_c = tuple(p.get("short_color", (0.15, 0.82, 1.0, 1.0)))
    long_c = tuple(p.get("long_color", (1.0, 0.67, 0.2, 1.0)))
    verts = geo.vertices * R
    for (i, j), cls in zip(geo.edges, geo.edge_class_by_edge):
        a, b = verts[i], verts[j]
        if a[2] < -1e-6 or b[2] < -1e-6:
            continue
        color = long_c if cls == "LONG" else short_c
        o.cylinder(a, b, strut_r, color, sides=6, caps=False)
    for i in set(k for e in geo.hemisphere_edges for k in e):
        v = verts[i]
        if v[2] > -1e-6:
            n = normalize(v)
            o.cylinder(v - n * 0.05, v + n * 0.06, strut_r * 1.9,
                       (0.75, 0.78, 0.84, 1.0), sides=6)
    if skin_alpha > 0.01:
        skin = (0.55, 0.75, 0.85, skin_alpha)
        for face in geo.hemisphere_faces:
            pts = [verts[k] * 0.985 for k in face]
            tr.tri(pts[0], pts[1], pts[2], skin)
    targets["dome"] = (np.array([0.0, 0.0, R * 0.45]), R * 1.15)
    targets["apex"] = (np.array([0.0, 0.0, R]), R * 0.35)


def _plenum_frame(p: dict):
    R = float(p.get("radius", 4.8))
    ring_r = R * float(p.get("ring_frac", 0.96))
    tube_r = float(p.get("tube", 0.30))
    z = tube_r + 0.02
    ports = int(p.get("ports", 10))
    blower_az = math.radians(float(p.get("blower_az", -30.0)))
    hose_az = math.radians(float(p.get("hose_az", 150.0)))
    return R, ring_r, tube_r, z, ports, blower_az, hose_az


def emit_plenum(o: Batch, tr: Batch, p: dict, t: float,
                targets: dict) -> None:
    R, ring_r, tube_r, z, ports, blower_az, hose_az = _plenum_frame(p)
    steel = (0.52, 0.56, 0.62, 1.0)
    segs = 44
    for i in range(segs):
        a0 = TAU * i / segs
        a1 = TAU * (i + 1) / segs
        p0 = (ring_r * math.cos(a0), ring_r * math.sin(a0), z)
        p1 = (ring_r * math.cos(a1), ring_r * math.sin(a1), z)
        o.cylinder(p0, p1, tube_r, steel, sides=8, caps=False)
    grille_open = float(p.get("grille_open", 1.0))
    first = None
    for g in range(ports):
        a = TAU * g / ports + math.radians(8.0)
        gx = (ring_r - tube_r - 0.01) * math.cos(a)
        gy = (ring_r - tube_r - 0.01) * math.sin(a)
        inward = (-math.cos(a), -math.sin(a), 0.0)
        o.box((gx + inward[0] * 0.03, gy + inward[1] * 0.03, z),
              (0.06, 0.34, 0.26), (0.30, 0.33, 0.38, 1.0), yaw=a)
        for s in range(3):                      # louver slats that open
            lz = z - 0.08 + s * 0.08
            tilt = 0.10 * grille_open
            o.box((gx + inward[0] * 0.05, gy + inward[1] * 0.05,
                   lz + tilt * 0.3),
                  (0.02, 0.30, 0.05), (0.75, 0.78, 0.84, 1.0), yaw=a)
        if first is None:
            first = np.array([gx, gy, z])
    targets["plenum"] = (np.array([ring_r * 0.7, 0.0, z]), ring_r * 1.25)
    if first is not None:
        targets["grille"] = (first, 0.9)


def emit_blower(o: Batch, tr: Batch, p: dict, t: float,
                targets: dict) -> None:
    R, ring_r, tube_r, z, ports, blower_az, hose_az = _plenum_frame(p)
    bx = (ring_r + 0.55) * math.cos(blower_az)
    by = (ring_r + 0.55) * math.sin(blower_az)
    out = (math.cos(blower_az), math.sin(blower_az), 0.0)
    yaw = blower_az
    body = (0.85, 0.45, 0.10, 1.0)
    dark = (0.22, 0.23, 0.26, 1.0)
    o.box((bx, by, z + 0.05), (0.55, 0.42, 0.44), body, yaw=yaw)
    o.cylinder((bx - out[0] * 0.5, by - out[1] * 0.5, z),
               (bx - out[0] * 0.9, by - out[1] * 0.9, z), 0.12, dark,
               sides=8)
    nozzle = (bx + out[0] * 0.55, by + out[1] * 0.55, z + 0.02)
    o.cylinder((bx + out[0] * 0.2, by + out[1] * 0.2, z + 0.02), nozzle,
               0.16, dark, sides=8, radius2=0.11)
    spin = float(p.get("spin", 0.0)) * t * TAU
    for blade in range(5):
        a = spin + TAU * blade / 5
        tip = (bx + 0.20 * math.cos(a) * (-out[1])
               + 0.0, by + 0.20 * math.cos(a) * out[0], z + 0.05
               + 0.20 * math.sin(a))
        o.cylinder((bx, by, z + 0.05), tip, 0.035,
                   (0.9, 0.92, 0.95, 1.0), sides=4, caps=False)
    # vacuum-mode canister beside the blower
    if float(p.get("vacuum", 0.0)) > 0.5:
        cx = bx + out[0] * 0.2 - out[1] * 0.9
        cy = by + out[1] * 0.2 + out[0] * 0.9
        o.cylinder((cx, cy, 0.0), (cx, cy, 0.9), 0.34,
                   (0.55, 0.58, 0.64, 1.0), sides=10)
        targets["canister"] = (np.array([cx, cy, 0.5]), 1.1)
    targets["blower"] = (np.array([bx, by, z + 0.1]), 1.0)
    # hose inlet on the far side (for the vacuum story)
    hx = (ring_r - tube_r - 0.02) * math.cos(hose_az)
    hy = (ring_r - tube_r - 0.02) * math.sin(hose_az)
    o.cylinder((hx, hy, z), (hx - math.cos(hose_az) * 0.5,
               hy - math.sin(hose_az) * 0.5, z * 0.8), 0.09,
               (0.35, 0.38, 0.44, 1.0), sides=7)
    targets["hose"] = (np.array([hx, hy, z]), 2.2)


def emit_airflow(o: Batch, tr: Batch, p: dict, t: float,
                 targets: dict) -> None:
    """Animated air particles: the mechanical heart of the story.

    mode 0 (exhaust): room air sinks to the perimeter grilles, races
    around the plenum tube to the blower port, and jets outside —
    the whole envelope held at negative pressure by one leaf blower.
    mode 1 (vacuum): the same loop reversed into a suction utility —
    debris near the hose inlet is pulled through the tube into the
    canister beside the blower.
    """
    intensity = float(p.get("intensity", 1.0))
    if intensity <= 0.01:
        return
    mode = float(p.get("mode", 0.0))
    R, ring_r, tube_r, z, ports, blower_az, hose_az = _plenum_frame(p)
    count = int(90 * min(1.0, intensity))
    speed = 0.10 + 0.06 * intensity

    def tube_point(az):
        return np.array([ring_r * math.cos(az), ring_r * math.sin(az), z])

    for i in range(count):
        u = (t * speed * (0.75 + 0.5 * rnd(i, 1.0)) + rnd(i, 2.0)) % 1.0
        if mode < 0.5:
            # --- exhaust: interior -> grille -> tube arc -> outside jet
            g = int(rnd(i, 3.0) * ports)
            g_az = TAU * g / ports + math.radians(8.0)
            start = np.array([
                (0.25 + 0.55 * rnd(i, 4.0)) * ring_r
                * math.cos(TAU * rnd(i, 5.0)),
                (0.25 + 0.55 * rnd(i, 4.0)) * ring_r
                * math.sin(TAU * rnd(i, 5.0)),
                0.5 + 2.4 * rnd(i, 6.0)])
            grille = tube_point(g_az) * 0.985
            if u < 0.42:
                k = u / 0.42
                k = k * k * (3 - 2 * k)
                pos = start + (grille - start) * k
                pos[0] += 0.25 * math.sin(t * 2.0 + i)
                pos[1] += 0.25 * math.cos(t * 1.7 + i * 1.3)
                color = (0.65, 0.85, 1.0, 0.85)
            elif u < 0.80:
                k = (u - 0.42) / 0.38
                delta = (blower_az - g_az) % TAU
                if delta > math.pi:
                    delta -= TAU
                az = g_az + delta * k
                pos = tube_point(az)
                color = CYAN
            else:
                k = (u - 0.80) / 0.20
                nozzle = tube_point(blower_az) * 1.12
                outward = np.array([math.cos(blower_az),
                                    math.sin(blower_az), 0.0])
                spread = np.array([-math.sin(blower_az),
                                   math.cos(blower_az), 0.0])
                pos = (nozzle + outward * (0.4 + 3.2 * k)
                       + spread * 0.5 * (rnd(i, 8.0) - 0.5) * k
                       + np.array([0, 0, 0.3 * k + 0.2 * k * rnd(i, 9.0)]))
                color = (1.0, 0.72, 0.25, 1.0 - 0.7 * k)
            size = 0.11 + 0.05 * math.sin(u * math.pi)
        else:
            # --- vacuum: debris -> hose -> tube arc -> canister
            hose = tube_point(hose_az) * 0.99
            start = hose + np.array([
                -math.cos(hose_az), -math.sin(hose_az), 0.0]) \
                * (0.6 + 1.6 * rnd(i, 4.0))
            start[0] += 0.8 * (rnd(i, 5.0) - 0.5)
            start[1] += 0.8 * (rnd(i, 6.0) - 0.5)
            start[2] = 0.05 + 0.3 * rnd(i, 7.0)
            if u < 0.35:
                k = (u / 0.35) ** 1.5
                pos = start + (hose - start) * k
                color = (0.62, 0.60, 0.55, 0.9)
            elif u < 0.85:
                k = (u - 0.35) / 0.50
                delta = (blower_az - hose_az) % TAU
                if delta > math.pi:
                    delta -= TAU
                az = hose_az + delta * k
                pos = tube_point(az)
                color = GREEN
            else:
                k = (u - 0.85) / 0.15
                can = tube_point(blower_az) * 1.05
                can = can + np.array([-math.sin(blower_az),
                                      math.cos(blower_az), 0.0]) * 0.9
                a = TAU * 2.0 * k + i
                pos = np.array([
                    can[0] + 0.2 * (1 - k) * math.cos(a),
                    can[1] + 0.2 * (1 - k) * math.sin(a),
                    0.9 - 0.7 * k])
                color = (0.45, 0.75, 0.50, 1.0 - 0.5 * k)
            size = 0.12
        tr.marker(pos, size * (1.5 + intensity) / 2.5, color)
    targets.setdefault("airflow", (np.array([0.0, 0.0, z]), ring_r))


# ---------------------------------------------------------------------------
# Build-process, comparison, and teaching-diagram objects
# ---------------------------------------------------------------------------

def _hemi_shell(batch: Batch, center, radius, color, rings=8, sides=20) -> None:
    """Low-poly hemisphere surface, apex at +Z, rim on the ``center`` plane."""
    cx, cy, cz = center

    def pt(ring, seg):
        theta = (math.pi / 2.0) * (ring / rings)
        phi = TAU * seg / sides
        x = radius * math.sin(theta) * math.cos(phi)
        y = radius * math.sin(theta) * math.sin(phi)
        z = radius * math.cos(theta)
        return (cx + x, cy + y, cz + z)

    for ring in range(rings):
        for seg in range(sides):
            a = pt(ring, seg)
            b = pt(ring + 1, seg)
            c = pt(ring + 1, seg + 1)
            d = pt(ring, seg + 1)
            batch.quad(a, b, c, d, color)


def emit_utility_column(o: Batch, tr: Batch, p: dict, t: float,
                        targets: dict) -> None:
    """Floor-to-apex utility column (water + power) with an apex
    crane-anchor ring for the turntable transfer."""
    R = float(p.get("radius", 4.8))
    height = R * max(0.0, min(1.0, float(p.get("reveal", 1.0))))
    col_r = float(p.get("col_r", 0.22))
    cx = float(p.get("cx", 0.0))
    cy = float(p.get("cy", 0.0))
    if height > 0.02:
        base = (cx, cy, 0.0)
        top = (cx, cy, height)
        steel = (0.58, 0.60, 0.64, 1.0)
        o.cylinder(base, top, col_r, steel, sides=10)
        water = (0.20, 0.45, 0.85, 1.0)
        power = (0.95, 0.75, 0.15, 1.0)
        off = col_r * 1.55
        o.cylinder((cx + off, cy, 0.0), (cx + off, cy, height),
                   col_r * 0.32, water, sides=6)
        o.cylinder((cx - off * 0.5, cy + off * 0.87, 0.0),
                   (cx - off * 0.5, cy + off * 0.87, height),
                   col_r * 0.32, power, sides=6)
    if height > 0.02 and float(p.get("anchor", 1.0)) > 0.5:
        ring_r = float(p.get("anchor_ring_r", col_r * 2.4))
        segs = 16
        chrome = (0.80, 0.82, 0.86, 1.0)
        for i in range(segs):
            a0 = TAU * i / segs
            a1 = TAU * (i + 1) / segs
            p0 = (cx + ring_r * math.cos(a0), cy + ring_r * math.sin(a0),
                  height + 0.06)
            p1 = (cx + ring_r * math.cos(a1), cy + ring_r * math.sin(a1),
                  height + 0.06)
            o.cylinder(p0, p1, 0.045, chrome, sides=6, caps=False)
        for k in range(4):
            a = TAU * k / 4
            hook_base = (cx + ring_r * math.cos(a), cy + ring_r * math.sin(a),
                         height + 0.06)
            hook_top = (cx + ring_r * math.cos(a), cy + ring_r * math.sin(a),
                        height + 0.30)
            o.cylinder(hook_base, hook_top, 0.03, (0.85, 0.87, 0.90, 1.0),
                       sides=5)
    # Floor the radius at a fraction of R, not just the column's own
    # height, so the camera doesn't snap in closer than any co-present
    # full-dome-scale object (e.g. a fully clad shell_layers shroud) and
    # end up pressed up against the inside of it.
    targets["utility_column"] = (np.array([cx, cy, height * 0.5]),
                                  max(1.2, height * 0.6, R * 0.9))
    targets["crane_anchor"] = (np.array([cx, cy, height + 0.15]), 1.0)


_SHELL_LAYERS = (
    ("insulation", (0.92, 0.85, 0.55, 0.55), 0.05),
    ("sheetrock", (0.88, 0.86, 0.80, 0.85), 0.02),
    ("osb", (0.72, 0.55, 0.32, 0.90), 0.03),
    ("wrap", (0.85, 0.87, 0.90, 0.55), 0.02),
    ("shingles", (0.25, 0.24, 0.26, 0.95), 0.04),
    ("fiberglass", (0.95, 0.97, 0.99, 0.35), 0.02),
)


def clad_radius(R: float, explode: float = 0.35) -> float:
    """Outer radius of the fully-clad shell for a bare-frame radius ``R``
    (mirrors :func:`emit_shell_layers`'s own accumulation). Useful for
    positioning anything that should sit on the FINISHED exterior surface
    — a roof-mounted panel, an exterior hatch trim — rather than at the
    bare-frame radius where the cladding would otherwise bury it."""
    return R * 1.02 + sum(explode + thick for _n, _c, thick
                          in _SHELL_LAYERS)


def emit_shell_layers(o: Batch, tr: Batch, p: dict, t: float,
                      targets: dict) -> None:
    """Concentric insulation/sheetrock/OSB/wrap/shingle/fiberglass reveal,
    driven by a continuous ``stage`` (0 = bare frame, len(_SHELL_LAYERS) =
    finished). ``alpha_mult`` (default 1.0) scales every layer's alpha —
    animate it toward 0 for a cutaway shot that needs to see past a
    fully-clad shell to something the shell would otherwise occlude (a
    hatch or interior fixture sitting at the bare-frame radius, well
    inside the clad shell's outer radius)."""
    R = float(p.get("radius", 4.8))
    stage = float(p.get("stage", len(_SHELL_LAYERS)))
    explode = float(p.get("explode", 0.35))
    alpha_mult = float(p.get("alpha_mult", 1.0))
    cx = float(p.get("cx", 0.0))
    cy = float(p.get("cy", 0.0))
    # Register the focus target up front, sized to the fully-clad shell, so
    # the camera has a stable frame for the whole shot even before stage 1
    # reveals anything (progress == 0 at the very start of a build shot).
    r_final = clad_radius(R, explode)
    targets["shell_layers"] = (np.array([cx, cy, r_final * 0.4]),
                               r_final * 0.5)
    if alpha_mult <= 0.005:
        return
    r = R * 1.02
    for idx, (_name, color, thick) in enumerate(_SHELL_LAYERS):
        reveal = max(0.0, min(1.0, stage - idx))
        r += explode
        if reveal > 0.001:
            alpha = color[3] * reveal * alpha_mult
            if alpha > 0.004:
                c = (color[0], color[1], color[2], alpha)
                _hemi_shell(tr, (cx, cy, 0.0), r, c, rings=7, sides=22)
        r += thick


def emit_hatch(o: Batch, tr: Batch, p: dict, t: float, targets: dict) -> None:
    """Watertight deck hatch: raised coaming, hinged door, locking wheel."""
    R = float(p.get("radius", 4.8))
    polar = math.radians(float(p.get("polar_deg", 62.0)))
    az = math.radians(float(p.get("az_deg", 0.0)))
    hatch_r = float(p.get("hatch_r", 0.5))
    openness = max(0.0, min(1.0, float(p.get("open", 0.0))))
    center = np.array([R * math.sin(polar) * math.cos(az),
                        R * math.sin(polar) * math.sin(az),
                        R * math.cos(polar)])
    outward = normalize(center)
    helper = np.array([0.0, 0.0, 1.0])
    if abs(float(np.dot(outward, helper))) > 0.92:
        helper = np.array([0.0, 1.0, 0.0])
    u = normalize(np.cross(outward, helper))
    v = normalize(np.cross(outward, u))
    steel = (0.42, 0.44, 0.48, 1.0)
    coam_h = 0.12
    rings = 14
    for i in range(rings):
        a0 = TAU * i / rings
        a1 = TAU * (i + 1) / rings

        def ring_pt(a, h):
            return center + outward * h + u * hatch_r * math.cos(a) \
                + v * hatch_r * math.sin(a)
        o.quad(ring_pt(a0, 0.0), ring_pt(a1, 0.0), ring_pt(a1, coam_h),
               ring_pt(a0, coam_h), steel)
    hinge_pivot = center + outward * coam_h + u * hatch_r
    swing = openness * math.radians(95.0)
    door_r = hatch_r * 0.94
    door_color = (0.58, 0.60, 0.64, 1.0)
    segs = 16
    door_center = _rotate_about(center + outward * coam_h, hinge_pivot, v,
                                swing)
    for i in range(segs):
        a0 = TAU * i / segs
        a1 = TAU * (i + 1) / segs
        r0 = (center + outward * coam_h + u * door_r * math.cos(a0)
              + v * door_r * math.sin(a0))
        r1 = (center + outward * coam_h + u * door_r * math.cos(a1)
              + v * door_r * math.sin(a1))
        r0 = _rotate_about(r0, hinge_pivot, v, swing)
        r1 = _rotate_about(r1, hinge_pivot, v, swing)
        o.tri(door_center, r0, r1, door_color)
    rot_outward = _rotate_about(outward, np.zeros(3), v, swing)
    rot_u = _rotate_about(u, np.zeros(3), v, swing)
    wheel_center = door_center + rot_outward * 0.05
    o.cylinder(wheel_center - rot_outward * 0.02,
               wheel_center + rot_outward * 0.02, 0.07,
               (0.85, 0.15, 0.12, 1.0), sides=8)
    for k in range(4):
        a = TAU * k / 4
        tip = (wheel_center + rot_u * math.cos(a) * 0.20
               + v * math.sin(a) * 0.20)
        o.cylinder(wheel_center, tip, 0.025, (0.90, 0.90, 0.92, 1.0), sides=5)
    # As with the utility column: floor at a fraction of R so the camera
    # doesn't end up closer than a co-present full-dome-scale object.
    targets["hatch"] = (center, max(hatch_r * 2.2, R * 1.35))


def emit_interior_fixtures(o: Batch, tr: Batch, p: dict, t: float,
                           targets: dict) -> None:
    """Kitchen / bed / bath blocks around the utility column, staged by
    a single ``reveal`` 0..1 (kitchen, then +bed, then +bath)."""
    R = float(p.get("radius", 4.8))
    reveal = float(p.get("reveal", 1.0))
    ring_r = R * 0.55
    # Register the focus target up front so the camera has somewhere to
    # look even before anything is revealed (progress == 0 at shot start).
    # Floored at a fraction of R for the same reason as the utility
    # column and hatch: don't snap in closer than a co-present
    # full-dome-scale object (e.g. a fully clad shell_layers shroud).
    targets["fixtures"] = (np.array([0.0, 0.0, 0.5]),
                           max(ring_r * 1.3, R * 1.4))
    if reveal <= 0.01:
        return
    cab = (0.68, 0.52, 0.34, 1.0)
    counter = (0.82, 0.83, 0.85, 1.0)
    frame = (0.90, 0.90, 0.92, 1.0)
    linens = (0.85, 0.87, 0.92, 1.0)
    tile = (0.75, 0.85, 0.86, 1.0)
    az = math.radians(float(p.get("kitchen_az", -35.0)))
    kx, ky = ring_r * math.cos(az), ring_r * math.sin(az)
    o.box((kx, ky, 0.45), (2.2, 0.65, 0.9), cab, yaw=az)
    o.box((kx, ky, 0.93), (2.2, 0.65, 0.04), counter, yaw=az)
    if reveal > 0.33:
        az = math.radians(float(p.get("bed_az", 130.0)))
        bx, by = ring_r * math.cos(az), ring_r * math.sin(az)
        o.box((bx, by, 0.24), (1.5, 2.0, 0.48), frame, yaw=az)
        o.box((bx, by, 0.55), (1.5, 2.0, 0.16), linens, yaw=az)
    if reveal > 0.66:
        az = math.radians(float(p.get("bath_az", 220.0)))
        wx, wy = ring_r * math.cos(az), ring_r * math.sin(az)
        o.box((wx, wy, 0.22), (0.8, 0.8, 0.44), tile, yaw=az)
        o.cylinder((wx, wy, 0.44), (wx, wy, 0.50), 0.34,
                   (0.92, 0.94, 0.96, 1.0), sides=10)


def emit_solar_band(o: Batch, tr: Batch, p: dict, t: float,
                    targets: dict) -> None:
    """PV panels on the real dome faces that face within ``tolerance_deg``
    of ``south_az_deg``, using the actual 2V face geometry."""
    R = float(p.get("radius", 4.8))
    south_az = math.radians(float(p.get("south_az_deg", -90.0)))
    south_dir = np.array([math.cos(south_az), math.sin(south_az), 0.0])
    tolerance = math.radians(float(p.get("tolerance_deg", 55.0)))
    min_polar = math.radians(float(p.get("min_polar_deg", 18.0)))
    coverage = max(0.0, min(1.0, float(p.get("coverage", 1.0))))
    geo = _geo()
    verts = geo.vertices * R
    panel = (0.08, 0.10, 0.16, 1.0)
    frame_c = (0.35, 0.36, 0.40, 1.0)
    qualifying = []
    for face in geo.hemisphere_faces:
        pts = [verts[k] for k in face]
        center = sum(pts) / 3.0
        n = normalize(center)
        polar = math.acos(max(-1.0, min(1.0, n[2])))
        if polar < min_polar or abs(n[0]) + abs(n[1]) <= 1e-6:
            continue
        horiz = normalize(np.array([n[0], n[1], 0.0]))
        ang = math.acos(max(-1.0, min(1.0, float(np.dot(horiz, south_dir)))))
        if ang <= tolerance:
            qualifying.append((pts, center, n))
    kept = qualifying[:max(1, int(round(len(qualifying) * coverage)))] \
        if qualifying else []
    for pts, center, n in kept:
        shrink = 0.86
        panel_pts = [center + (pt - center) * shrink + n * 0.015
                     for pt in pts]
        o.tri(panel_pts[0], panel_pts[1], panel_pts[2], panel, n)
        for i in range(3):
            j = (i + 1) % 3
            o.quad(panel_pts[i], panel_pts[j], panel_pts[j] - n * 0.02,
                   panel_pts[i] - n * 0.02, frame_c, n)
    targets["solar"] = (np.array([0.0, -R * 0.5, R * 0.55]), R * 0.9)


def emit_comparison_pair(o: Batch, tr: Batch, p: dict, t: float,
                         targets: dict) -> None:
    """Box vs dome, side by side, both scaled from real dimensions the
    caller supplies (see al_build.building_comparisons())."""
    box_w = float(p.get("box_w", 4.0))
    box_l = float(p.get("box_l", 4.0))
    box_h = float(p.get("box_h", 3.0))
    dome_r = float(p.get("dome_r", 2.6))
    gap = float(p.get("gap", 2.5))
    cx = float(p.get("cx", 0.0))
    cy = float(p.get("cy", 0.0))
    box_color = tuple(p.get("box_color", (0.62, 0.42, 0.28, 1.0)))
    dome_color = tuple(p.get("dome_color", (0.30, 0.62, 0.78, 1.0)))
    roof_color = tuple(p.get("roof_color", (0.30, 0.30, 0.32, 1.0)))
    box_x = cx - gap * 0.5 - box_w * 0.5
    dome_x = cx + gap * 0.5 + dome_r
    o.box((box_x, cy, box_h * 0.5), (box_w, box_l, box_h), box_color)
    o.box((box_x, cy, box_h + 0.03), (box_w * 1.02, box_l * 1.02, 0.06),
          roof_color)
    _hemi_shell(o, (dome_x, cy, 0.0), dome_r, dome_color, rings=8, sides=22)
    ground = (0.22, 0.24, 0.20, 1.0)
    o.disc((box_x, cy, -0.01), max(box_w, box_l) * 0.72, ground, sides=28)
    o.disc((dome_x, cy, -0.01), dome_r * 1.08, ground, sides=28)
    targets["compare_box"] = (np.array([box_x, cy, box_h * 0.5]),
                               max(box_w, box_l, box_h))
    targets["compare_dome"] = (np.array([dome_x, cy, dome_r * 0.45]),
                                dome_r * 1.3)
    targets["compare_pair"] = (np.array([cx, cy, dome_r * 0.4]),
                                (gap + box_w + dome_r * 2) * 0.62)


def emit_triangle_vs_square(o: Batch, tr: Batch, p: dict, t: float,
                            targets: dict) -> None:
    """Rigidity diagram: an unbraced square racks under ``shear`` while a
    triangle (or a diagonally ``braced`` square) holds its shape."""
    size = float(p.get("size", 2.4))
    braced = float(p.get("braced", 0.0)) > 0.5
    shear = 0.0 if braced else max(0.0, min(1.0, float(p.get("shear", 0.0))))
    gap = float(p.get("gap", 3.2))
    cx = float(p.get("cx", 0.0))
    cy = float(p.get("cy", 0.0))
    strut_r = float(p.get("strut", 0.05))
    base_z = float(p.get("base_z", 0.02))
    rigid = (0.30, 0.62, 0.78, 1.0)
    racking = (0.90, 0.30, 0.22, 1.0)

    sq_x = cx - gap * 0.5
    lean = shear * size * 0.42
    sq = [
        (sq_x - size * 0.5, cy, base_z),
        (sq_x + size * 0.5, cy, base_z),
        (sq_x + size * 0.5 + lean, cy, base_z + size),
        (sq_x - size * 0.5 + lean, cy, base_z + size),
    ]
    sq_color = rigid if (braced or shear <= 0.05) else racking
    for i in range(4):
        j = (i + 1) % 4
        o.cylinder(sq[i], sq[j], strut_r, sq_color, sides=6)
    if braced:
        o.cylinder(sq[0], sq[2], strut_r * 0.85, rigid, sides=6)

    tri_x = cx + gap * 0.5
    tri = [
        (tri_x - size * 0.5, cy, base_z),
        (tri_x + size * 0.5, cy, base_z),
        (tri_x, cy, base_z + size * 0.87),
    ]
    for i in range(3):
        j = (i + 1) % 3
        o.cylinder(tri[i], tri[j], strut_r, rigid, sides=6)

    targets["rigidity_square"] = (np.array([sq_x, cy, base_z + size * 0.5]),
                                   size)
    targets["rigidity_triangle"] = (np.array([tri_x, cy, base_z + size * 0.5]),
                                     size)
    targets["rigidity_pair"] = (np.array([cx, cy, base_z + size * 0.5]),
                                 (gap + size * 2) * 0.6)


OBJECT_EMITTERS = {
    "dome": emit_dome,
    "plenum": emit_plenum,
    "blower": emit_blower,
    "airflow": emit_airflow,
    "utility_column": emit_utility_column,
    "shell_layers": emit_shell_layers,
    "hatch": emit_hatch,
    "interior_fixtures": emit_interior_fixtures,
    "solar_band": emit_solar_band,
    "comparison_pair": emit_comparison_pair,
    "triangle_vs_square": emit_triangle_vs_square,
}

_ALL_EMITTERS: dict | None = None

# What else is on the stage this frame. The Dome Forge layers below are
# allowed to read their siblings (drains sit at the low point of whatever
# the panel layer is doing), which in the builder comes from the layer
# stack; here it comes from the scene's own object list.
_FRAME_OBJECTS: list = []


def _forge_stack(layers, radius: float):
    """A Dome Forge layer stack standing in for the builder's document.

    The bridged emitters expect the builder's stack: its sibling layers,
    its per-triangle assignments and its design library. A real (default)
    stack is used rather than a stub so anything they read is the same
    thing the builder would have handed them."""
    from dome_forge.layers import LayerStack
    stack = LayerStack(layers=list(layers))
    stack.settings.radius = float(radius)
    return stack


def _forge_context(radius: float):
    from dome_forge.build import DomeContext
    key = round(float(radius), 6)
    ctx = _FORGE_CONTEXTS.get(key)
    if ctx is None:
        ctx = DomeContext(key)
        _FORGE_CONTEXTS[key] = ctx
    return ctx


_FORGE_CONTEXTS: dict = {}


def _batch_span(batch: Batch, start: int):
    """Centre and radius of whatever was appended to ``batch`` since
    ``start`` -- so a bridged layer's focus framing is measured off the
    geometry it really emitted, not guessed."""
    if len(batch.v) <= start:
        return None
    pts = np.asarray(batch.v[start:], dtype=np.float64).reshape(-1, 10)[:, :3]
    return pts


def _forge_emitter(kind: str):
    """Wrap one Dome Forge layer emitter in the stage-object contract."""

    def emit(o: Batch, tr: Batch, p: dict, t: float, targets: dict) -> None:
        from dome_forge import build as forge_build
        from dome_forge.layers import Layer
        radius = float(p.get("radius", 4.8))
        params = {k: v for k, v in p.items() if k != "radius"}
        layer = Layer(kind=kind, params=params)
        ctx = _forge_context(radius)
        siblings = []
        for name, other in _FRAME_OBJECTS:
            if isinstance(name, str) and name.startswith("forge:"):
                other_kind = name.split(":", 1)[1]
                try:
                    siblings.append(Layer(
                        kind=other_kind,
                        params={k: v for k, v in dict(other).items()
                                if k != "radius"}))
                except KeyError:
                    continue
        if not any(s.kind == kind for s in siblings):
            siblings.append(layer)
        previous = forge_build._ACTIVE_STACK["stack"]
        forge_build._ACTIVE_STACK["stack"] = _forge_stack(siblings, radius)
        start_o, start_tr = len(o.v), len(tr.v)
        try:
            forge_build.EMITTERS[kind](o, tr, layer, ctx, t)
        finally:
            forge_build._ACTIVE_STACK["stack"] = previous
        chunks = [c for c in (_batch_span(o, start_o), _batch_span(tr, start_tr))
                  if c is not None]
        if chunks:
            pts = np.concatenate(chunks, axis=0)
            centre = pts.mean(axis=0)
            reach = float(np.max(np.linalg.norm(pts - centre, axis=1)))
        else:
            centre, reach = np.array([0.0, 0.0, radius * 0.45]), radius
        targets[f"forge_{kind}"] = (centre, max(0.5, reach))

    return emit


def all_emitters() -> dict:
    """Every object that can be placed on a stage.

    Three sources, resolved on first use so the modules can refer to each
    other freely whichever one is imported first: the star objects above,
    the accessory and appliance catalogue, and every layer the Dome Forge
    builder draws -- bridged in under a ``forge:`` prefix so a movie can
    use the real modelled panels, veins and cistern rather than a second
    copy of them."""
    global _ALL_EMITTERS
    if _ALL_EMITTERS is None:
        from .accessories import ACCESSORY_EMITTERS
        from dome_forge.build import EMITTERS as FORGE_EMITTERS
        merged = dict(OBJECT_EMITTERS)
        merged.update(ACCESSORY_EMITTERS)
        for kind in FORGE_EMITTERS:
            merged[f"forge:{kind}"] = _forge_emitter(kind)
        _ALL_EMITTERS = merged
    return _ALL_EMITTERS


# ---------------------------------------------------------------------------
# Frame assembly
# ---------------------------------------------------------------------------

def build_frame(env: EnvironmentSpec, objects: list, t: float,
                shot=None, progress: float = 0.0):
    """Compose one deterministic frame.

    ``objects`` is a list of (name, params) pairs; shot actions override
    parameters for the duration of the shot. Returns (opaque batch,
    transparent batch, focus-target dict)."""
    global _FRAME_OBJECTS
    o, tr = Batch(), Batch()
    targets: dict = {}
    _FRAME_OBJECTS = list(objects)
    _emit_terrain(o, env)
    _emit_water(o, tr, env, t)
    _emit_flora(o, env)
    _emit_tsunami(tr, env, t)
    _emit_tornado(o, tr, env, t)
    _emit_weather(tr, env, t)
    emitters = all_emitters()
    for name, params in objects:
        emitter = emitters.get(name)
        if emitter is None:
            continue
        p = dict(params)
        if shot is not None:
            for action in shot.actions:
                if action[0] == name:
                    p[action[1]] = shot.action_value(
                        name, action[1], progress,
                        float(p.get(action[1], 0.0)))
        emitter(o, tr, p, t, targets)
    targets.setdefault("origin", (np.zeros(3), 6.0))
    return o, tr, targets
