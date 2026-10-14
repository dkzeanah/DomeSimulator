"""A piece: one solid you can select, cut, delete, move or copy.

Every piece in the world -- a dome member, a zome stick, a log of the foundation,
a strut you drew yourself, a jig's table -- is the same thing: an
:class:`infill.solids.Solid` (planar polygon faces), a colour, a layer and a
name. That one representation is what lets the world treat three structures
built by three solvers as one model, and it is why cutting is exact: a cut is
:func:`infill.solids.clip` by a plane, twice, and the cut face is capped.

Units are inches, z up.
"""

from __future__ import annotations

import math
from dataclasses import dataclass, field

import numpy as np

from infill import solids as so


@dataclass
class Piece:
    pid: str
    layer: str
    name: str
    solid: so.Solid
    colour: tuple
    kind: str = "member"          # member | strut | skin | jig | ground | person
    meta: dict = field(default_factory=dict)

    # -- measuring -------------------------------------------------------
    def points(self) -> np.ndarray:
        return self.solid.vertices()

    def axis(self) -> tuple[np.ndarray, np.ndarray]:
        """The piece's long axis, end to end: the two extreme points along its principal direction."""
        if "a" in self.meta and "b" in self.meta:
            return np.asarray(self.meta["a"], float), np.asarray(self.meta["b"], float)
        p = self.points()
        c = p.mean(axis=0)
        _u, _s, vt = np.linalg.svd(p - c, full_matrices=False)
        d = vt[0]
        t = (p - c) @ d
        return c + d * t.min(), c + d * t.max()

    def extents(self) -> tuple[float, float, float]:
        """Length along the axis, then the two widths across it (inches)."""
        p = self.points()
        c = p.mean(axis=0)
        _u, _s, vt = np.linalg.svd(p - c, full_matrices=False)
        span = [(float(((p - c) @ vt[k]).max() - ((p - c) @ vt[k]).min())) for k in range(3)]
        return span[0], span[1], span[2]

    def volume(self) -> float:
        """Cubic inches, by the divergence theorem over its faces (fan-triangulated)."""
        v = 0.0
        for poly, _t in self.solid.faces:
            for k in range(1, len(poly) - 1):
                v += float(np.dot(poly[0], np.cross(poly[k], poly[k + 1]))) / 6.0
        return abs(v)


# ----------------------------------------------------------------------
# Making solids
# ----------------------------------------------------------------------

def from_rings(tails, heads, tag: str = "side") -> so.Solid:
    """A prism between two matching end polygons (a zome stick, a strut)."""
    tails = [np.asarray(t, float) for t in tails]
    heads = [np.asarray(h, float) for h in heads]
    n = len(tails)
    faces = [(np.array(tails[::-1]), "end-a"), (np.array(heads), "end-b")]
    for k in range(n):
        faces.append((np.array([tails[k], tails[(k + 1) % n], heads[(k + 1) % n], heads[k]]), tag))
    return _outward(so.Solid(faces))


def from_mesh(vertices: np.ndarray, indices: np.ndarray) -> so.Solid:
    """A closed triangle mesh (the dome's members, its jig) as a solid of triangles."""
    pos = np.asarray(vertices, float)[:, :3]
    tri = np.asarray(indices, int).reshape(-1, 3)
    faces = [(pos[t].copy(), "face") for t in tri
             if np.linalg.norm(np.cross(pos[t[1]] - pos[t[0]], pos[t[2]] - pos[t[0]])) > 1e-10]
    return so.Solid(faces)


def _outward(solid: so.Solid) -> so.Solid:
    c = solid.vertices().mean(axis=0)
    faces = []
    for poly, tag in solid.faces:
        n = np.cross(poly[1] - poly[0], poly[2] - poly[0])
        faces.append((poly[::-1].copy() if n @ (poly.mean(axis=0) - c) < 0 else poly, tag))
    return so.Solid(faces, solid.planes)


SECTIONS = ("wedge", "square", "half")


def section(kind: str, log_in: float = 12.0) -> np.ndarray:
    """A cross-section in its own (across, up) plane, centred on its centroid.

    wedge  -- an eighth of the log: two radial faces at 45 degrees and the trimmed back
    square -- two slant-paired eighths planed square: R/sqrt(2) on a side
    half   -- a half trunk on edge: the flat face, the round back
    """
    r = log_in / 2
    if kind == "wedge":
        th = math.radians(22.5)
        pts = [(0.0, 0.0)] + [(r * math.sin(a), r * math.cos(a))
                               for a in np.linspace(-th, th, 7)]
    elif kind == "square":
        h = r / math.sqrt(2) / 2
        pts = [(-h, -h), (h, -h), (h, h), (-h, h)]
    elif kind == "half":
        pts = [(0.0, -r)] + [(r * math.cos(a), r * math.sin(a))
                             for a in np.linspace(-math.pi / 2, math.pi / 2, 11)][1:-1] + [(0.0, r)]
    else:
        raise ValueError(f"section must be one of {SECTIONS}")
    pts = np.array(pts, float)
    return pts - pts.mean(axis=0)


def strut(a, b, kind: str = "wedge", log_in: float = 12.0) -> so.Solid:
    """A straight member of section ``kind`` from point ``a`` to point ``b``."""
    a, b = np.asarray(a, float), np.asarray(b, float)
    d = b - a
    L = float(np.linalg.norm(d))
    if L < 1e-6:
        raise ValueError("a strut needs two different points")
    d /= L
    up = np.array([0.0, 0.0, 1.0])
    across = np.cross(d, up)
    if np.linalg.norm(across) < 1e-6:
        across = np.array([1.0, 0.0, 0.0])
    across /= np.linalg.norm(across)
    upv = np.cross(across, d)
    sec = section(kind, log_in)
    ring = [x * across + y * upv for x, y in sec]
    return from_rings([a + q for q in ring], [b + q for q in ring])


def moved(solid: so.Solid, delta) -> so.Solid:
    delta = np.asarray(delta, float)
    return so.Solid([(p + delta, t) for p, t in solid.faces], solid.planes)


def cut(piece: Piece, point, normal) -> tuple[Piece, Piece] | None:
    """Saw ``piece`` through ``point`` square to ``normal``: two pieces, each capped."""
    n = np.asarray(normal, float)
    n /= np.linalg.norm(n)
    d = float(n @ np.asarray(point, float))
    a = so.clip(piece.solid, so.Plane(n, d, "saw"))
    b = so.clip(piece.solid, so.Plane(-n, -d, "saw"))
    if not a.faces or not b.faces:
        return None
    out = []
    for suffix, sol in (("a", a), ("b", b)):
        meta = {k: v for k, v in piece.meta.items() if k not in ("a", "b")}
        out.append(Piece(f"{piece.pid}.{suffix}", piece.layer, f"{piece.name} ({suffix})", sol, piece.colour,
                         piece.kind, meta))
    return out[0], out[1]


# ----------------------------------------------------------------------
# Drawing and picking
# ----------------------------------------------------------------------

def triangles(piece: Piece) -> np.ndarray:
    """(n, 3, 3) fan triangles of every face."""
    out = []
    for poly, _t in piece.solid.faces:
        for k in range(1, len(poly) - 1):
            out.append((poly[0], poly[k], poly[k + 1]))
    return np.array(out, float).reshape(-1, 3, 3)


def ray_hit(tris: np.ndarray, origin, direction) -> float | None:
    """Nearest positive distance along the ray to any of the triangles (Moller-Trumbore)."""
    if len(tris) == 0:
        return None
    o, d = np.asarray(origin, float), np.asarray(direction, float)
    v0, v1, v2 = tris[:, 0], tris[:, 1], tris[:, 2]
    e1, e2 = v1 - v0, v2 - v0
    p = np.cross(d, e2)
    det = np.einsum("ij,ij->i", e1, p)
    ok = np.abs(det) > 1e-12
    inv = np.where(ok, 1.0 / np.where(ok, det, 1.0), 0.0)
    s = o - v0
    u = np.einsum("ij,ij->i", s, p) * inv
    q = np.cross(s, e1)
    v = (q @ d) * inv
    t = np.einsum("ij,ij->i", e2, q) * inv
    hit = ok & (u >= 0) & (v >= 0) & (u + v <= 1) & (t > 1e-6)
    return float(t[hit].min()) if hit.any() else None


def snap(point, step: float, nodes: np.ndarray | None = None, reach: float = 4.0) -> np.ndarray:
    """A node within ``reach`` wins; otherwise the nearest grid point in x and y (z kept)."""
    p = np.asarray(point, float)
    if nodes is not None and len(nodes):
        dist = np.linalg.norm(nodes - p, axis=1)
        k = int(np.argmin(dist))
        if dist[k] <= reach:
            return nodes[k].copy()
    if step > 0:
        return np.array([round(p[0] / step) * step, round(p[1] / step) * step, p[2]])
    return p


def validate_pieces() -> None:
    s = strut((0, 0, 0), (100, 0, 0), "square")
    p = Piece("t", "test", "test", s, (1, 1, 1, 1), "strut", {"a": [0, 0, 0], "b": [100, 0, 0]})
    L, w1, w2 = p.extents()
    side = 6.0 / math.sqrt(2)
    # (a square has no preferred cross direction, so its widths are checked through its volume)
    assert abs(L - 100) < 1e-6, (L, w1, w2)
    assert abs(p.volume() - 100 * side * side) < 1e-6
    a, b = cut(p, (40, 0, 0), (1, 0, 0))
    assert abs(a.extents()[0] + b.extents()[0] - 100) < 1e-6
    assert abs(a.volume() + b.volume() - p.volume()) < 1e-6, "a cut loses no wood but the kerf we do not model"
    t = ray_hit(triangles(p), (50, -50, 0), (0, 1, 0))
    assert t is not None and abs(t - (50 - side / 2)) < 1e-6
    w = Piece("w", "t", "w", strut((0, 0, 0), (0, 0, 50), "wedge"), (1, 1, 1, 1))
    assert w.volume() > 0 and abs(w.extents()[0] - 50) < 1e-6
    assert np.allclose(snap((7.4, 13.1, 2.0), 6.0), (6.0, 12.0, 2.0))
    assert np.allclose(snap((7.4, 13.1, 2.0), 6.0, np.array([[8.0, 13.0, 2.0]])), (8.0, 13.0, 2.0))
