"""Convex solids from half-spaces, and the few curved shapes a furnished room needs.

Every stick, base board, card and post in the dome is a convex solid bounded by planes: a
stick is its outer face, inner face, bevelled edge, square inside edge, compound head cut
and square tail cut. Building it as the intersection of those six half-spaces, rather than
placing eight corners by hand, means the corners are wherever the planes put them -- which
is where a saw puts them.

A half-space is ``(n, c)``: the points ``x`` with ``n . x <= c``.
"""

from __future__ import annotations

import itertools
import math
from dataclasses import dataclass, field

import numpy as np

EPS = 1e-7


def unit(v) -> np.ndarray:
    v = np.asarray(v, dtype=float)
    n = float(np.linalg.norm(v))
    return v / n if n > 0 else v


def plane_through(point, normal) -> tuple[np.ndarray, float]:
    n = unit(normal)
    return n, float(n @ np.asarray(point, dtype=float))


@dataclass
class Mesh:
    """Triangles to shade and edges to ink: a SketchUp "group"."""

    verts: np.ndarray                    # (n, 3) float
    tris: np.ndarray                     # (m, 3) int
    edges: np.ndarray                    # (k, 2) int, the lines drawn in ink
    polys: list = field(default_factory=list)   # the faces as polygons (vertex index lists)

    def moved(self, offset) -> "Mesh":
        return Mesh(self.verts + np.asarray(offset, dtype=float), self.tris, self.edges, self.polys)

    def transformed(self, rot: np.ndarray, offset=(0, 0, 0)) -> "Mesh":
        return Mesh(self.verts @ np.asarray(rot).T + np.asarray(offset, dtype=float), self.tris, self.edges, self.polys)

    @property
    def centre(self) -> np.ndarray:
        return self.verts.mean(axis=0)


def merge(meshes: list[Mesh]) -> Mesh:
    vs, ts, es, ps = [], [], [], []
    k = 0
    for m in meshes:
        vs.append(m.verts)
        ts.append(m.tris + k)
        es.append(m.edges + k)
        ps.extend([[i + k for i in p] for p in m.polys])
        k += len(m.verts)
    return Mesh(np.vstack(vs), np.vstack(ts).astype(int), np.vstack(es).astype(int) if es else np.zeros((0, 2), int), ps)


def _poly_mesh(points: list[np.ndarray], faces: list[list[int]], ink: list[list[int]] | None = None) -> Mesh:
    verts = np.array(points, dtype=float)
    tris, edges = [], set()
    for f in faces:
        for i in range(1, len(f) - 1):
            tris.append((f[0], f[i], f[i + 1]))
    for f in (faces if ink is None else ink):
        for i in range(len(f)):
            a, b = f[i], f[(i + 1) % len(f)]
            edges.add((min(a, b), max(a, b)))
    return Mesh(verts, np.array(tris, dtype=int).reshape(-1, 3), np.array(sorted(edges), dtype=int).reshape(-1, 2), [list(f) for f in faces])


def corners(halfspaces: list[tuple[np.ndarray, float]]) -> np.ndarray:
    """The corners of a bounded convex solid: every triple of planes that meets inside all the rest."""
    pts: list[np.ndarray] = []
    H = [(np.asarray(n, float), float(c)) for n, c in halfspaces]
    for (n1, c1), (n2, c2), (n3, c3) in itertools.combinations(H, 3):
        A = np.array([n1, n2, n3])
        if abs(np.linalg.det(A)) < 1e-10:
            continue
        x = np.linalg.solve(A, np.array([c1, c2, c3]))
        if all(n @ x <= c + 1e-7 for n, c in H):
            if not any(np.linalg.norm(x - p) < 1e-7 for p in pts):
                pts.append(x)
    return np.array(pts)


def solid(halfspaces: list[tuple[np.ndarray, float]]) -> Mesh:
    """The convex solid inside every half-space, as a mesh (empty if they enclose nothing)."""
    pts = corners(halfspaces)
    if len(pts) < 4:
        return Mesh(np.zeros((0, 3)), np.zeros((0, 3), int), np.zeros((0, 2), int))
    centre = pts.mean(axis=0)
    faces = []
    for n, c in halfspaces:
        n = np.asarray(n, float)
        on = [i for i, p in enumerate(pts) if abs(n @ p - c) < 1e-6]
        if len(on) < 3:
            continue
        fc = pts[on].mean(axis=0)
        u = unit(pts[on[0]] - fc)
        v = np.cross(unit(n), u)
        on.sort(key=lambda i: math.atan2(float((pts[i] - fc) @ v), float((pts[i] - fc) @ u)))
        faces.append(on)
    if not faces:
        return Mesh(np.zeros((0, 3)), np.zeros((0, 3), int), np.zeros((0, 2), int))
    del centre
    return _poly_mesh(list(pts), faces)


def volume(m: Mesh) -> float:
    v = m.verts
    return abs(sum(float(np.dot(v[a], np.cross(v[b], v[c]))) for a, b, c in m.tris)) / 6.0


# ----------------------------------------------------------------------
# Boxes, prisms and round things
# ----------------------------------------------------------------------

def box(centre, size, yaw_deg: float = 0.0) -> Mesh:
    """An axis box turned about the vertical by ``yaw_deg``."""
    sx, sy, sz = (s / 2 for s in size)
    a = math.radians(yaw_deg)
    ux, uy, uz = np.array([math.cos(a), math.sin(a), 0]), np.array([-math.sin(a), math.cos(a), 0]), np.array([0, 0, 1.0])
    c = np.asarray(centre, float)
    H = []
    for u, s in ((ux, sx), (uy, sy), (uz, sz)):
        H.append((u, float(u @ c + s)))
        H.append((-u, float(-u @ c + s)))
    return solid(H)


def prism(polygon, normal, thickness: float) -> Mesh:
    """A flat polygon (3-D points, any winding) pushed ``thickness`` along ``normal``."""
    P = [np.asarray(p, float) for p in polygon]
    n = unit(normal)
    if np.dot(np.cross(P[1] - P[0], P[2] - P[0]), n) < 0:
        P = P[::-1]
    k = len(P)
    pts = P + [p + n * thickness for p in P]
    faces = [list(range(k))[::-1], list(range(k, 2 * k))]
    for i in range(k):
        j = (i + 1) % k
        faces.append([i, j, k + j, k + i])
    return _poly_mesh(pts, faces)


def cylinder(p0, p1, r: float, seg: int = 20, r1: float | None = None) -> Mesh:
    """A round rod (or cone with ``r1``). Its sides are smooth: only the rims are inked."""
    p0, p1 = np.asarray(p0, float), np.asarray(p1, float)
    ax = unit(p1 - p0)
    a = unit(np.cross(ax, [0, 0, 1.0] if abs(ax[2]) < 0.9 else [1.0, 0, 0]))
    b = np.cross(ax, a)
    r1 = r if r1 is None else r1
    ring = [math.tau * i / seg for i in range(seg)]
    bottom = [p0 + r * (math.cos(t) * a + math.sin(t) * b) for t in ring]
    top = [p1 + r1 * (math.cos(t) * a + math.sin(t) * b) for t in ring]
    pts = bottom + top
    faces = [list(range(seg))[::-1], list(range(seg, 2 * seg))]
    for i in range(seg):
        j = (i + 1) % seg
        faces.append([i, j, seg + j, seg + i])
    return _poly_mesh(pts, faces, ink=faces[:2])


def sphere_mesh(centre, r: float, seg: int = 16) -> Mesh:
    c = np.asarray(centre, float)
    pts, faces = [], []
    rings = seg // 2
    for i in range(rings + 1):
        ph = math.pi * i / rings
        for j in range(seg):
            th = math.tau * j / seg
            pts.append(c + r * np.array([math.sin(ph) * math.cos(th), math.sin(ph) * math.sin(th), math.cos(ph)]))
    for i in range(rings):
        for j in range(seg):
            a, b = i * seg + j, i * seg + (j + 1) % seg
            faces.append([a, b, b + seg, a + seg])
    m = _poly_mesh(pts, faces, ink=[])
    return m


# ----------------------------------------------------------------------
# Flat convex polygons, clipped the way a saw clips them
# ----------------------------------------------------------------------

def clip(poly: list[np.ndarray], sides: list, n, c: float, new_side) -> tuple[list[np.ndarray], list]:
    """Sutherland-Hodgman: keep the part of a convex polygon with ``n . x <= c``.

    ``sides[i]`` describes the edge from ``poly[i]`` to ``poly[i+1]``; an edge made by the
    cut gets ``new_side``.
    """
    n = np.asarray(n, float)
    out_p, out_s = [], []
    k = len(poly)
    for i in range(k):
        P, Q, s = poly[i], poly[(i + 1) % k], sides[i]
        dp, dq = float(n @ P - c), float(n @ Q - c)
        inP, inQ = dp <= EPS, dq <= EPS
        if inP:
            out_p.append(P)
            out_s.append(s if inQ else s)
            if not inQ:
                t = dp / (dp - dq)
                out_p.append(P + t * (Q - P))
                out_s.append(new_side)
        elif inQ:
            t = dp / (dp - dq)
            out_p.append(P + t * (Q - P))
            out_s.append(s)
    # merge vertices that landed on top of each other
    pp, ss = [], []
    for p, s in zip(out_p, out_s):
        if pp and np.linalg.norm(p - pp[-1]) < 1e-9:
            ss[-1] = s
            continue
        pp.append(p)
        ss.append(s)
    if len(pp) > 1 and np.linalg.norm(pp[0] - pp[-1]) < 1e-9:
        pp.pop()
        ss.pop()
    return pp, ss


def poly_area(poly: list[np.ndarray]) -> float:
    if len(poly) < 3:
        return 0.0
    s = np.zeros(3)
    for i in range(len(poly)):
        s += np.cross(poly[i], poly[(i + 1) % len(poly)])
    return float(np.linalg.norm(s)) / 2


def poly_thickness(poly: list[np.ndarray]) -> float:
    """The narrowest the polygon gets: its smallest width over all its side directions."""
    if len(poly) < 3:
        return 0.0
    best = math.inf
    for i in range(len(poly)):
        a, b = poly[i], poly[(i + 1) % len(poly)]
        e = unit(b - a)
        w = max(float(np.linalg.norm(np.cross(p - a, e))) for p in poly)
        best = min(best, w)
    return best
