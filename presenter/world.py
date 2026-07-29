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


OBJECT_EMITTERS = {
    "dome": emit_dome,
    "plenum": emit_plenum,
    "blower": emit_blower,
    "airflow": emit_airflow,
}


# ---------------------------------------------------------------------------
# Frame assembly
# ---------------------------------------------------------------------------

def build_frame(env: EnvironmentSpec, objects: list, t: float,
                shot=None, progress: float = 0.0):
    """Compose one deterministic frame.

    ``objects`` is a list of (name, params) pairs; shot actions override
    parameters for the duration of the shot. Returns (opaque batch,
    transparent batch, focus-target dict)."""
    o, tr = Batch(), Batch()
    targets: dict = {}
    _emit_terrain(o, env)
    _emit_water(o, tr, env, t)
    _emit_flora(o, env)
    _emit_tsunami(tr, env, t)
    _emit_tornado(o, tr, env, t)
    _emit_weather(tr, env, t)
    for name, params in objects:
        emitter = OBJECT_EMITTERS.get(name)
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
