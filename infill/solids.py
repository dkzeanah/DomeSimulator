"""Every piece as a real solid, and the measurements a person cuts to.

A strip piece is its cross-section run along its length and cut by planes --
the 45° walls of the opening (or the panel's edges, covering), a chevron's
centre line, a ring member's square ends. Building it that way gives, exactly:

* the solid itself (faces tagged: which sawn face, the bark, which cut),
* the length of every long edge after both ends are cut -- the point line,
  each bark corner -- which is what you mark,
* the planes of the cuts, one saw cut per plane, which :mod:`infill.recipes`
  turns into a saw setting.

Section edges carry names from the stock (``sawn 1``, ``bark``, ``sawn 2``
for a sector; ``face 1``, ``edge 1`` ... for a board) through every rotation
and rip, so a face of the finished piece can be named in words.
"""

from __future__ import annotations

import math
from dataclasses import dataclass, field

import numpy as np

from . import geom2d as g2
from . import section as sec

BIG = 400.0   # half-length of an uncut run before its planes trim it


# ----------------------------------------------------------------------
# Sections with named edges
# ----------------------------------------------------------------------

def tagged_local(stock: sec.Stock) -> tuple[np.ndarray, list[str]]:
    p = stock.local()
    if stock.kind == "board":
        return p, ["face 1", "edge 1", "face 2", "edge 2"]
    n = len(p)
    tags = ["sawn 1"] + ["bark"] * (n - 2) + ["sawn 2"]
    return p, tags


def clip_tagged(poly: np.ndarray, tags: list[str], point, normal, tag: str):
    """Keep (x - point).normal >= 0; edges keep their names, the new edge
    along the clip line is called ``tag``."""
    point, normal = np.asarray(point, float), np.asarray(normal, float)
    out_p, out_t = [], []
    n = len(poly)
    for i in range(n):
        a, b = poly[i], poly[(i + 1) % n]
        da, db = float(np.dot(a - point, normal)), float(np.dot(b - point, normal))
        if da >= 0:
            out_p.append(a)
            out_t.append(tags[i] if db >= 0 else tags[i])
        if (da >= 0) != (db >= 0):
            t = da / (da - db)
            x = a + (b - a) * t
            out_p.append(x)
            # Entering the kept side: the edge from here is the original edge;
            # leaving it: the edge from here runs along the clip line.
            out_t.append(tags[i] if da < 0 else tag)
    # Fix the names: an edge that starts at a point we kept but whose far end
    # was cut runs to the crossing point -- still the original edge.
    return np.array(out_p), out_t


def tagged_section(stock: sec.Stock, pose: str, T: float, tilt: float = 0.0):
    """The stock's section in its pose, ripped flush, tilted -- with names."""
    p, tags = tagged_local(stock)
    if stock.kind == "board":
        if pose == "BE":
            p = sec._rot(p, 90.0)
        top = pose == "BU"
    else:
        phi = stock.angle_deg
        rotation = {"FDR": 90 - phi / 2, "FUL": -phi / 2 - 90, "FDL": phi / 2 - 90,
                    "FUR": 90 + phi / 2, "PD": 0.0, "PU": 180.0}[pose]
        p = sec._rot(p, rotation)
        top = pose in ("FUL", "FUR", "PU")
    if top:
        p = p + np.array([0.0, T - p[:, 1].max()])
    else:
        p = p - np.array([0.0, p[:, 1].min()])
    if tilt:
        c = p.mean(axis=0)
        p = sec._rot(p - c, tilt) + c
        p = p - np.array([0.0, p[:, 1].min()])
    if p[:, 1].max() > T + 1e-9:
        p, tags = clip_tagged(p, tags, (0.0, T), (0.0, -1.0), "ripped flush (open side)")
    if p[:, 1].min() < -1e-9:
        p, tags = clip_tagged(p, tags, (0.0, 0.0), (0.0, 1.0), "ripped flush (flat side)")
    return p, tags


def match(placed_poly: np.ndarray, poly: np.ndarray) -> np.ndarray:
    """Slide a named section onto where the packer put the piece."""
    d = placed_poly.min(axis=0) - poly.min(axis=0)
    out = poly + d
    return out


# ----------------------------------------------------------------------
# Convex solids
# ----------------------------------------------------------------------

@dataclass(eq=False)
class Plane:
    n: np.ndarray       # unit; the piece is where n . X >= d
    d: float
    tag: str


@dataclass
class Solid:
    faces: list[tuple[np.ndarray, str]]
    planes: list[Plane] = field(default_factory=list)
    origin: np.ndarray | None = None      # 3-D frame of a strip piece
    along: np.ndarray | None = None
    across: np.ndarray | None = None
    section: np.ndarray | None = None
    tags: list[str] | None = None

    def vertices(self) -> np.ndarray:
        return np.concatenate([f for f, _t in self.faces]) if self.faces else np.zeros((0, 3))

    def point(self, x: float, z: float, s: float) -> np.ndarray:
        return self.origin + self.across * x + np.array([0.0, 0.0, 1.0]) * z + self.along * s


def _clip_face(poly: np.ndarray, pl: Plane):
    out, cut = [], []
    n = len(poly)
    for i in range(n):
        a, b = poly[i], poly[(i + 1) % n]
        da, db = float(pl.n @ a) - pl.d, float(pl.n @ b) - pl.d
        if da >= -1e-9:
            out.append(a)
        if (da >= -1e-9) != (db >= -1e-9):
            t = da / (da - db)
            x = a + (b - a) * t
            out.append(x)
            cut.append(x)
    return (np.array(out) if len(out) >= 3 else None), cut


def clip(solid: Solid, pl: Plane) -> Solid:
    faces, cap = [], []
    for poly, tag in solid.faces:
        kept, cut = _clip_face(poly, pl)
        if kept is not None and g2_area3(kept) > 1e-9:
            faces.append((kept, tag))
        cap.extend(cut)
    if len(cap) >= 3:
        pts = np.unique(np.round(np.array(cap), 9), axis=0)
        if len(pts) >= 3:
            c = pts.mean(axis=0)
            u = pts[0] - c
            u /= max(np.linalg.norm(u), 1e-12)
            v = np.cross(-pl.n, u)
            ang = np.arctan2((pts - c) @ v, (pts - c) @ u)
            ring = pts[np.argsort(ang)]
            if g2_area3(ring) > 1e-9:
                faces.append((ring, pl.tag))
    used = any(t == pl.tag for _p, t in faces)
    planes = solid.planes + ([pl] if used else [])
    return Solid(faces, planes, solid.origin, solid.along, solid.across, solid.section, solid.tags)


def g2_area3(poly: np.ndarray) -> float:
    if len(poly) < 3:
        return 0.0
    p = np.asarray(poly, float)
    q = np.roll(p, -1, axis=0)
    s = np.array([(p[:, 1] * q[:, 2] - p[:, 2] * q[:, 1]).sum(),
                  (p[:, 2] * q[:, 0] - p[:, 0] * q[:, 2]).sum(),
                  (p[:, 0] * q[:, 1] - p[:, 1] * q[:, 0]).sum()])
    return 0.5 * float(np.linalg.norm(s))


def prism(section: np.ndarray, tags: list[str], origin2, along2, across2, z0: float) -> Solid:
    o = np.array([origin2[0], origin2[1], z0])
    a = np.array([along2[0], along2[1], 0.0])
    c = np.array([across2[0], across2[1], 0.0])
    up = np.array([0.0, 0.0, 1.0])

    def P(x, z, s):
        return o + c * x + up * z + a * s
    faces = []
    n = len(section)
    for i in range(n):
        p, q = section[i], section[(i + 1) % n]
        faces.append((np.array([P(p[0], p[1], -BIG), P(q[0], q[1], -BIG), P(q[0], q[1], BIG),
                                P(p[0], p[1], BIG)]), tags[i]))
    faces.append((np.array([P(x, z, -BIG) for x, z in section[::-1]]), "raw end"))
    faces.append((np.array([P(x, z, BIG) for x, z in section]), "raw end"))
    return Solid(faces, [], o, a, c, section, tags)


def slab(plan: np.ndarray, z_lo: float, z_hi: float, side_tag: str = "edge") -> Solid:
    p = g2.ccw(plan)
    faces = [(np.array([[x, y, z_lo] for x, y in p[::-1]]), "bottom"),
             (np.array([[x, y, z_hi] for x, y in p]), "top")]
    for i in range(len(p)):
        a, b = p[i], p[(i + 1) % len(p)]
        faces.append((np.array([[a[0], a[1], z_lo], [b[0], b[1], z_lo], [b[0], b[1], z_hi],
                                [a[0], a[1], z_hi]]), side_tag))
    return Solid(faces)


# ----------------------------------------------------------------------
# Measurements
# ----------------------------------------------------------------------

def corners(solid: Solid) -> list[tuple[str, float, float]]:
    """Each long edge of a strip piece -- where two named faces meet -- and
    the stretch of it left between the cuts: (name, s_from, s_to)."""
    out = []
    sect, tags = solid.section, solid.tags
    n = len(sect)
    for i in range(n):
        before, after = tags[i - 1], tags[i]
        if before == after:
            continue
        name = corner_name(before, after)
        x, z = sect[i]
        lo, hi = -BIG, BIG
        P0 = solid.point(x, z, 0.0)
        ok = True
        for pl in solid.planes:
            na = float(pl.n @ solid.along)
            val = float(pl.n @ P0) - pl.d
            if abs(na) < 1e-9:
                if val < -1e-6:
                    ok = False
                continue
            t = -val / na
            if na > 0:
                lo = max(lo, t)
            else:
                hi = min(hi, t)
        if ok and hi > lo:
            out.append((name, lo, hi))
    return out


def corner_name(a: str, b: str) -> str:
    pair = {a, b}
    if pair == {"sawn 1", "sawn 2"}:
        return "the point"
    if "bark" in pair:
        other = (pair - {"bark"}).pop()
        return f"the bark corner of {other}"
    if all(t.startswith(("face", "edge")) for t in pair):
        return "corner " + "/".join(sorted(pair))
    return " / ".join(sorted(pair))


def length(solid: Solid) -> tuple[float, float]:
    cs = corners(solid)
    if not cs:
        return 0.0, 0.0
    ls = [hi - lo for _n, lo, hi in cs]
    return max(ls), min(ls)


def validate_solids() -> None:
    st = sec.stocks(12.0, 72.0)
    T = 6.0 * math.sin(math.radians(45))
    p, tags = tagged_section(st["w8"], "FUL", T)
    assert len(p) == len(tags) and tags.count("bark") > 5
    s = prism(p, tags, (0.0, 0.0), (1.0, 0.0), (0.0, 1.0), 0.0)
    # Square ends 50 in apart: every corner is 50 in.
    s = clip(s, Plane(np.array([1.0, 0, 0]), -25.0, "end 1"))
    s = clip(s, Plane(np.array([-1.0, 0, 0]), -25.0, "end 2"))
    for _n, lo, hi in corners(s):
        assert abs((hi - lo) - 50.0) < 1e-6
    assert len(s.planes) == 2
    # A 45° plane across the end makes the corners differ by their heights.
    s2 = prism(p, tags, (0.0, 0.0), (1.0, 0.0), (0.0, 1.0), 0.0)
    n = np.array([1.0, 0.0, 1.0]) / math.sqrt(2)
    s2 = clip(s2, Plane(n, -10.0, "wall"))
    s2 = clip(s2, Plane(np.array([-1.0, 0, 0]), -25.0, "end 2"))
    cs = corners(s2)
    zs = {nm: None for nm, *_ in cs}
    assert max(hi - lo for _n, lo, hi in cs) - min(hi - lo for _n, lo, hi in cs) > 1.0


# ----------------------------------------------------------------------
# Pieces of a layout as solids
# ----------------------------------------------------------------------

def bounds(panel, opts) -> list[Plane]:
    """The planes every piece of this triangle is trimmed to: the 45° walls
    of the opening (filling), or the panel's edges bevelled to half each
    seam's fold so neighbouring coverings meet (covering)."""
    from .constants import C
    out = []
    T = panel.spec.thickness_in
    for k in range(3):
        if opts.mode == "fill":
            n, d = panel.wall_plane(k)
            out.append(Plane(np.asarray(n, float), float(d), f"wall {k}"))
        else:
            m = panel.inward(k)
            a, _b = panel.edge(k)
            d0 = float(m @ a) + panel.spec.gasket_in / 2 - C["cover_overhang_in"]
            tb = math.tan(math.radians((panel.folds[k] or 0.0) / 2))
            n = np.array([m[0], m[1], tb])
            d = d0 + tb * T
            L = float(np.linalg.norm(n))
            out.append(Plane(n / L, d / L, f"edge {k}"))
    return out


def build(piece, panel, opts) -> Solid | None:
    sp = piece.spec
    if sp is None:
        return None
    if sp["type"] == "strip":
        sect = np.asarray(sp["section"], float)
        T = float(sect[:, 1].max())
        tp, tags = tagged_section(piece.stock, piece.pose, T, sp.get("tilt", 0.0))
        tp = match(sect, tp)
        if len(tp) != len(sect) or np.abs(tp - sect).max() > 1e-6:
            tp, tags = sect, ["side"] * len(sect)
        s = prism(tp, tags, sp["origin"], sp["along"], sp["across"], sp["z0"])
        if "s_range" in sp:
            lo, hi = sp["s_range"]
            o = s.origin
            s = clip(s, Plane(s.along, float(s.along @ o) + lo, "end (square)"))
            s = clip(s, Plane(-s.along, -(float(s.along @ o) + hi), "end (square)"))
        else:
            for pl in bounds(panel, opts):
                s = clip(s, pl)
            extra = sp.get("extra")
            if extra is not None:
                e = g2.ccw(np.asarray(extra, float))
                for i in range(len(e)):
                    a, b = e[i], e[(i + 1) % len(e)]
                    d = g2.unit(b - a)
                    inward = np.array([-d[1], d[0]])
                    n = np.array([inward[0], inward[1], 0.0])
                    s = clip(s, Plane(n, float(inward @ a), "centre line"))
        return s
    if sp["type"] == "slab":
        s = slab(np.asarray(sp["plan"], float), *sp["z"])
        if sp.get("bounds"):
            for pl in bounds(panel, opts):
                s = clip(s, pl)
        if sp.get("half"):
            apex, nx = sp["half"]
            s = clip(s, Plane(np.array([nx, 0.0, 0.0]), float(nx * apex[0]), "centre line"))
        return s
    if sp["type"] == "extrude":
        faces = []
        z0, z1 = sp["z"]
        for poly in sp["polys"]:
            p = g2.ccw(np.asarray(poly, float))
            faces.append((np.array([[x, y, z0] for x, y in p[::-1]]), "bottom (traced)"))
            faces.append((np.array([[x, y, z1] for x, y in p]), "top (traced)"))
            for i in range(len(p)):
                a, b = p[i], p[(i + 1) % len(p)]
                faces.append((np.array([[a[0], a[1], z0], [b[0], b[1], z0], [b[0], b[1], z1],
                                        [a[0], a[1], z1]]), "traced edge"))
        return Solid(faces)
    return None


def attach(pieces, panel, opts) -> None:
    """Build every piece's solid; strip pieces take their lengths from it."""
    for p in pieces:
        try:
            p.solid = build(p, panel, opts)
        except Exception:  # noqa: BLE001 -- a drawing problem must not stop the layout
            p.solid = None
        if p.solid is not None and p.spec and p.spec["type"] == "strip" and p.solid.tags:
            longest, shortest = length(p.solid)
            if longest > 0:
                p.long, p.short = longest, shortest
