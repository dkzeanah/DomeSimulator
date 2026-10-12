"""Small plane geometry the infill calculator needs, with no dependencies
beyond numpy: convex clipping, line-polygon chords, polygon areas."""

from __future__ import annotations

import math

import numpy as np


def area(poly) -> float:
    p = np.asarray(poly, dtype=float)
    if len(p) < 3:
        return 0.0
    x, y = p[:, 0], p[:, 1]
    return 0.5 * abs(float(np.dot(x, np.roll(y, -1)) - np.dot(y, np.roll(x, -1))))


def ccw(poly) -> np.ndarray:
    """The polygon wound counter-clockwise."""
    p = np.asarray(poly, dtype=float)
    x, y = p[:, 0], p[:, 1]
    signed = 0.5 * (float(np.dot(x, np.roll(y, -1)) - np.dot(y, np.roll(x, -1))))
    return p if signed >= 0 else p[::-1]


def clip_halfplane(poly, point, normal) -> np.ndarray:
    """Keep the part of ``poly`` where (x - point) . normal >= 0."""
    p = [np.asarray(v, dtype=float) for v in poly]
    if not p:
        return np.zeros((0, 2))
    point, normal = np.asarray(point, float), np.asarray(normal, float)
    out = []
    for i in range(len(p)):
        a, b = p[i], p[(i + 1) % len(p)]
        da, db = float(np.dot(a - point, normal)), float(np.dot(b - point, normal))
        if da >= 0:
            out.append(a)
        if (da >= 0) != (db >= 0):
            t = da / (da - db)
            out.append(a + (b - a) * t)
    return np.array(out) if out else np.zeros((0, 2))


def clip_convex(poly, clipper) -> np.ndarray:
    """``poly`` clipped to the inside of the convex polygon ``clipper``."""
    c = ccw(clipper)
    out = np.asarray(poly, dtype=float)
    for i in range(len(c)):
        a, b = c[i], c[(i + 1) % len(c)]
        edge = b - a
        inward = np.array([-edge[1], edge[0]])
        out = clip_halfplane(out, a, inward)
        if len(out) == 0:
            break
    return out


def strip(origin, along, across, lo: float, hi: float, reach: float = 1e4) -> np.ndarray:
    """A long rectangle: every point origin + s*along + t*across with
    lo <= t <= hi."""
    o, a, n = (np.asarray(v, dtype=float) for v in (origin, along, across))
    return np.array([o + n * lo - a * reach, o + n * lo + a * reach,
                     o + n * hi + a * reach, o + n * hi - a * reach])


def inset_triangle(tri, distance: float) -> np.ndarray:
    """Every edge of a triangle moved in by ``distance``: the same triangle,
    scaled about its incentre."""
    t = np.asarray(tri, dtype=float)
    a = np.linalg.norm(t[1] - t[2])
    b = np.linalg.norm(t[2] - t[0])
    c = np.linalg.norm(t[0] - t[1])
    s = a + b + c
    if s < 1e-12:
        return t.copy()
    centre = (a * t[0] + b * t[1] + c * t[2]) / s
    r = 2 * area(t) / s
    if r < 1e-12:
        return t.copy()
    k = max(0.0, (r - distance) / r)
    return centre + (t - centre) * k


def inradius(tri) -> float:
    t = np.asarray(tri, dtype=float)
    s = sum(np.linalg.norm(t[i] - t[(i + 1) % 3]) for i in range(3))
    return 2 * area(t) / s if s > 1e-12 else 0.0


def extent_along(poly, axis) -> tuple[float, float]:
    d = np.asarray(poly, float) @ np.asarray(axis, float)
    return float(d.min()), float(d.max())


def unit(v) -> np.ndarray:
    v = np.asarray(v, dtype=float)
    n = np.linalg.norm(v)
    return v / n if n > 1e-12 else v


def perp(v) -> np.ndarray:
    return np.array([-v[1], v[0]])


def angle_deg(a, b) -> float:
    a, b = unit(a), unit(b)
    return math.degrees(math.acos(max(-1.0, min(1.0, float(np.dot(a, b))))))


def pinwheel(tri, width: float, gap: float = 0.0) -> list[tuple[np.ndarray, float, np.ndarray]]:
    """Three members of ``width`` round a triangle in a same-handed
    pinwheel, the way the frame is built: each runs from the far side of the
    member behind to the near side of the member ahead. Each band lies
    ``gap`` in from its edge. Returns (outline, length, direction) each."""
    t = np.asarray(tri, dtype=float)
    centre = t.mean(axis=0)
    lines = []
    for k in range(3):
        a, b = t[k], t[(k + 1) % 3]
        d = unit(b - a)
        m = perp(d)
        if float(np.dot(m, centre - a)) < 0:
            m = -m
        lines.append((a + m * gap, d, m))

    def hit(point, direction, q, e):
        den = direction[0] * e[1] - direction[1] * e[0]
        off = q - point
        return float((off[0] * e[1] - off[1] * e[0]) / den)
    out = []
    for k in range(3):
        prev, nxt = (k + 2) % 3, (k + 1) % 3
        p, d, m = lines[k]
        mid = p + m * width / 2
        t_tail = hit(mid, d, lines[prev][0], lines[prev][1])
        t_head = hit(mid, d, lines[nxt][0] + lines[nxt][2] * width, lines[nxt][1])
        lo, hi = min(t_tail, t_head), max(t_tail, t_head)
        inner = p + m * width
        poly = np.array([p + d * lo, p + d * hi, inner + d * hi, inner + d * lo])
        out.append((poly, hi - lo, d))
    return out


def hull(points) -> np.ndarray:
    """Convex hull, counter-clockwise (monotone chain)."""
    pts = sorted({(round(float(x), 9), round(float(y), 9)) for x, y in np.asarray(points, float)})
    if len(pts) < 3:
        return np.array(pts)

    def cross(o, a, b):
        return (a[0] - o[0]) * (b[1] - o[1]) - (a[1] - o[1]) * (b[0] - o[0])
    lower, upper = [], []
    for p in pts:
        while len(lower) >= 2 and cross(lower[-2], lower[-1], p) <= 0:
            lower.pop()
        lower.append(p)
    for p in reversed(pts):
        while len(upper) >= 2 and cross(upper[-2], upper[-1], p) <= 0:
            upper.pop()
        upper.append(p)
    return np.array(lower[:-1] + upper[:-1])
