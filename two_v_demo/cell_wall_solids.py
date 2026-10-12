"""Solid layers for the cell wall film: every layer one piece, cut away.

The first cut drew each layer as see-through tiles, and wherever they
overlapped they turned to mush. Here every layer is a continuous solid shell
with a drawn thickness, made by moving the solver's dome outward along its own
radius, so neighbouring cells meet at the seams the way one sheet would. A
quarter of the stack is cut away facing the camera; the cut faces show each
layer in section with its channels in it, and the flows run along those
sections, every layer at once. Fabric layers are quilts: forty puffed,
stitched patches, one per triangle.

Layers are drawn thicker than they are (:data:`DRAW_SCALE`, at least
:data:`MIN_DRAWN`), and the film says so; their real thicknesses are
:func:`cell_wall.thickness_mm`'s. Nothing drawn here is a figure.
"""

from __future__ import annotations

import math
from functools import lru_cache

import numpy as np

from . import cabin_world as cw
from . import cell_wall as cwall
from . import cell_wall_scene as cs
from . import channel_scene as sc
from .render_kit import TriangleBatch

DRAW_SCALE = 4.0
MIN_DRAWN = 0.034
INNER_SKIN = 0.012           # the board that closes the cavity on the room side, drawn

#: How a layer's channels look in section, and which way its contents run on
#: the two cut faces: (disc colour, disc radius as a share of the layer, spacing m,
#: flow colour, direction on the first cut, on the second, flow style).
SECTION = {
    "thermal": ((1.00, 0.55, 0.30, 1.0), 0.32, 0.045, (1.00, 0.45, 0.20, 1.0), 1, -1, "pulse"),
    "air_in": ((0.92, 1.00, 0.94, 1.0), 0.38, 0.11, (0.55, 1.00, 0.70, 1.0), 1, 1, "cone"),
    "fog": ((0.55, 0.55, 0.58, 1.0), 0.36, 0.14, (0.85, 0.85, 0.88, 1.0), -1, -1, "puff"),
    "bus": ((0.20, 0.25, 0.75, 1.0), 0.28, 0.10, (0.75, 0.80, 1.00, 1.0), -1, -1, "packet"),
    "water": ((0.10, 0.30, 0.65, 1.0), 0.30, 0.035, (0.35, 0.70, 1.00, 1.0), -1, -1, "drop"),
    "filter": ((0.88, 0.98, 0.90, 1.0), 0.22, 0.05, (0.55, 1.00, 0.70, 1.0), 1, 1, "cone"),
    "vacuum": ((0.30, 0.15, 0.40, 1.0), 0.20, 0.028, (0.85, 0.65, 1.00, 1.0), -1, -1, "dot"),
    "living": ((0.25, 0.55, 0.95, 1.0), 0.18, 0.20, (0.40, 0.75, 1.00, 1.0), -1, -1, "drop"),
}

FABRIC_PUFF = {"thermal": 0.006, "air_in": 0.018, "fog": 0.010, "bus": 0.004, "airbag": 0.014,
               "living": 0.012, "cap": 0.0}
"""How much each fabric layer's patches puff up, drawn (a quilt's loft)."""


def tone(rgba, k: float) -> tuple:
    return (min(1.0, rgba[0] * k), min(1.0, rgba[1] * k), min(1.0, rgba[2] * k), 1.0)


# ----------------------------------------------------------------------
# The dome, and points on a layer at a height above every face
# ----------------------------------------------------------------------

@lru_cache(maxsize=1)
def dome() -> dict:
    model, scale, shift = sc._world()
    topo = model.topology
    v = np.asarray(topo.vertices, dtype=float) * scale + np.asarray(shift, float)
    c = np.asarray(shift, float)
    faces, normals, ds = [], [], []
    owners: dict[tuple, list[int]] = {}
    for i, f in enumerate(topo.faces):
        ids = tuple(f.vertices)
        a, b, d = (v[k] for k in ids)
        n = np.cross(b - a, d - a)
        n /= np.linalg.norm(n)
        if np.dot(n, (a + b + d) / 3 - c) < 0:
            n = -n
        faces.append(ids)
        normals.append(n)
        ds.append(float(np.dot(n, a - c)))
        for j in range(3):
            owners.setdefault(tuple(sorted((ids[j], ids[(j + 1) % 3]))), []).append(i)
    rim = {k for k, o in owners.items() if len(o) == 1}
    links = [tuple(o) for o in owners.values() if len(o) == 2]
    return {"v": v, "c": c, "faces": faces, "normals": normals, "d": float(np.mean(ds)),
            "rim": rim, "links": links, "owners": owners}


def lift(p: np.ndarray, h: float) -> np.ndarray:
    """A point on the face planes, moved out to height ``h`` above them -- radially,
    so every face moves together and a layer stays one continuous sheet."""
    D = dome()
    return D["c"] + (p - D["c"]) * (1.0 + h / D["d"])


# ----------------------------------------------------------------------
# The stack's drawn heights
# ----------------------------------------------------------------------

def drawn(key: str) -> float:
    if key == "airbag":
        return MIN_DRAWN
    return max(MIN_DRAWN, cwall.thickness_mm(key) / 1000 * DRAW_SCALE)


def heights(explode: float, order=None, inflate: float = 0.0) -> dict[str, tuple[float, float]]:
    """(inner, outer) height of every layer above the face planes, from assembled
    (0) to exploded (1). ``order`` puts the weather side in another order (the
    owner's first drawing)."""
    e = max(0.0, min(1.0, explode))
    fs = cs.faces()
    top = float(np.mean([f.top for f in fs]))
    bottom = float(np.mean([f.bottom for f in fs]))
    gap = 0.004 + 0.15 * e
    out: dict[str, tuple[float, float]] = {}
    h = top + 0.003
    weather = order or cs.WEATHER
    for key in weather:
        t = drawn(key)
        if key == "airbag":
            t += cwall.C["airbag_m"] * max(0.0, min(1.0, inflate))
        out[key] = (h, h + t)
        h += t + gap
    h = bottom - 0.003 - INNER_SKIN
    out["skin"] = (h, h + INNER_SKIN)
    for key in cs.ROOM:                      # nearest the core first
        if order and key in order:
            continue
        t = drawn(key)
        h -= gap * 0.8 + t
        out[key] = (h, h + t)
    out["core"] = (bottom + 0.006, top - 0.006)
    return out


# ----------------------------------------------------------------------
# Solids, and cutting them
# ----------------------------------------------------------------------

def _prism(a, b, c, a2, b2, c2, rim_sides=(False, False, False)) -> list:
    """A triangular prism as tagged faces, each wound to face outward."""
    faces = [([a2, b2, c2], "top"), ([c, b, a], "bottom")]
    for k, (p, q, p2, q2) in enumerate(((a, b, a2, b2), (b, c, b2, c2), (c, a, c2, a2))):
        faces.append(([p, q, q2, p2], "rim" if rim_sides[k] else "side"))
    return faces


def _clip(faces: list, n: np.ndarray, off: float) -> tuple[list, list | None]:
    """Keep the part of a convex solid with n.x <= off. Returns its faces and the
    new face on the plane (None when nothing was cut)."""
    kept, cut = [], []
    for poly, tag in faces:
        out = []
        m = len(poly)
        for i in range(m):
            p, q = poly[i], poly[(i + 1) % m]
            dp, dq = float(np.dot(n, p)) - off, float(np.dot(n, q)) - off
            if dp <= 0:
                out.append(p)
            if dp * dq < 0:
                x = p + (q - p) * (dp / (dp - dq))
                out.append(x)
                cut.append(x)
        if len(out) >= 3:
            kept.append((out, tag))
    cap = _order(cut, n) if len(cut) >= 3 else None
    return kept, cap


def _order(points: list, n: np.ndarray) -> list | None:
    uniq: list[np.ndarray] = []
    for p in points:
        if not any(np.linalg.norm(p - q) < 1e-7 for q in uniq):
            uniq.append(p)
    if len(uniq) < 3:
        return None
    e1 = np.array([0.0, 0.0, 1.0]) - n * n[2]
    if np.linalg.norm(e1) < 1e-6:
        e1 = np.array([1.0, 0.0, 0.0])
    e1 /= np.linalg.norm(e1)
    e2 = np.cross(n, e1)
    mid = np.mean(uniq, axis=0)
    return sorted(uniq, key=lambda p: math.atan2(float(np.dot(p - mid, e2)), float(np.dot(p - mid, e1))))


class Cut:
    """A wedge taken out of the stack, centred on an azimuth round the dome's axis.

    :meth:`facing` makes the usual one: the wedge in front of the camera, both
    cut faces turned toward it, so every layer shows as a band on each side,
    nested inside the next, with the frame and the room within."""

    @classmethod
    def facing(cls, camera_azimuth_deg: float) -> "Cut":
        return cls(camera_azimuth_deg, 42.0)

    def __init__(self, azimuth_deg: float, half_deg: float = 48.0):
        D = dome()
        self.c = D["c"]
        t, a = math.radians(azimuth_deg), math.radians(half_deg)
        self.azimuth, self.half = azimuth_deg, half_deg
        self.n1 = np.array([-math.sin(t - a), math.cos(t - a), 0.0])     # into the wedge from plane 1
        self.n2 = np.array([math.sin(t + a), -math.cos(t + a), 0.0])     # into the wedge from plane 2

    def f1(self, p) -> float:
        return float(np.dot(self.n1, np.asarray(p) - self.c))

    def f2(self, p) -> float:
        return float(np.dot(self.n2, np.asarray(p) - self.c))

    def removed(self, p) -> bool:
        return self.f1(p) > 0 and self.f2(p) > 0

    def apply(self, faces: list) -> tuple[list, list]:
        """The solid with the wedge taken out: its faces, and its cut faces as
        (polygon, plane index, outward normal)."""
        pts = [p for poly, _t in faces for p in poly]
        v1 = [self.f1(p) for p in pts]
        v2 = [self.f2(p) for p in pts]
        if max(v1) <= 0 or (min(v1) >= 0 and max(v2) <= 0):
            return faces, []
        if min(v1) >= 0 and min(v2) >= 0:
            return [], []
        caps = []
        off1 = float(np.dot(self.n1, self.c))
        off2 = float(np.dot(self.n2, self.c))
        a_faces, cap_a = _clip(faces, self.n1, off1)
        if cap_a is not None and self.f2(np.mean(cap_a, axis=0)) > 0:
            caps.append((cap_a, 1, self.n1))
        rest, cap_r = _clip(faces, -self.n1, -off1)
        if cap_r is not None:
            rest = rest + [(cap_r, "inner")]
        b_faces, cap_b = _clip(rest, self.n2, off2)
        if cap_b is not None:
            caps.append((cap_b, 2, self.n2))
        return a_faces + [f for f in b_faces if f[1] != "inner"], caps


TWO_SIDED = [True]
"""Emit both windings. The per-frame opaque pass culls back faces, so geometry
drawn there needs both; static layers are drawn with culling off (the shader
lights a back face as a front one), so a static build sets this False and
halves its size."""


def _tri2(batch: TriangleBatch, a, b, c, colour) -> None:
    """Lit by its own geometric normal; both windings when the pass culls."""
    g = np.cross(b - a, c - a)
    s = float(np.linalg.norm(g))
    if s < 1e-12:
        return
    g = g / s
    batch.triangle(a, b, c, colour, g)
    if TWO_SIDED[0]:
        batch.triangle(a, c, b, colour, -g)


def _fan(batch: TriangleBatch, poly: list, colour, _normal=None) -> None:
    for i in range(1, len(poly) - 1):
        _tri2(batch, poly[0], poly[i], poly[i + 1], colour)


def disc_on(batch: TriangleBatch, centre, normal, radius: float, colour, segs: int = 10) -> None:
    n = np.asarray(normal, float)
    e1 = np.array([0.0, 0.0, 1.0]) - n * n[2]
    e1 = e1 / np.linalg.norm(e1) if np.linalg.norm(e1) > 1e-6 else np.array([1.0, 0.0, 0.0])
    e2 = np.cross(n, e1)
    ring = [centre + (e1 * math.cos(t) + e2 * math.sin(t)) * radius
            for t in np.linspace(0, math.tau, segs, endpoint=False)]
    for k in range(segs):
        _tri2(batch, centre, ring[k], ring[(k + 1) % segs], colour)


# ----------------------------------------------------------------------
# The stack, as solids
# ----------------------------------------------------------------------

def _corners(fi: int) -> tuple:
    D = dome()
    return tuple(D["v"][k] for k in D["faces"][fi])


def _rim_sides(fi: int) -> tuple:
    D = dome()
    ids = D["faces"][fi]
    return tuple(tuple(sorted((ids[j], ids[(j + 1) % 3]))) in D["rim"] for j in range(3))


def _cavity(fi: int) -> tuple:
    """The face's cavity: inside its three members."""
    a, b, c = _corners(fi)
    la, lb, lc = np.linalg.norm(b - c), np.linalg.norm(c - a), np.linalg.norm(a - b)
    inc = (la * a + lb * b + lc * c) / (la + lb + lc)
    area = 0.5 * np.linalg.norm(np.cross(b - a, c - a))
    r = 2 * area / (la + lb + lc)
    k = max(0.05, (r - cs.member_width()) / r)
    return tuple(inc + (p - inc) * k for p in (a, b, c))


def layer_solids(key: str, hin: float, hout: float, puff: float = 0.0, n_sub: int = 1,
                 lower_only: bool = False) -> list[tuple[int, list]]:
    """Every face's piece of one layer, as (face index, tagged faces)."""
    fs = cs.faces()
    out = []
    for fi in range(len(dome()["faces"])):
        if lower_only and not fs[fi].lower:
            continue
        a, b, c = _cavity(fi) if key == "core" else _corners(fi)
        rims = (False, False, False) if key == "core" else _rim_sides(fi)
        if n_sub <= 1 or puff <= 0:
            out.append((fi, _prism(lift(a, hin), lift(b, hin), lift(c, hin),
                                   lift(a, hout), lift(b, hout), lift(c, hout), rims)))
            continue
        # A quilted patch: the face split into n x n small prisms, the tops puffed.
        def pt(i, j):
            u, v = i / n_sub, j / n_sub
            return a + (b - a) * u + (c - a) * v, (u, v, 1 - u - v)
        for i in range(n_sub):
            for j in range(n_sub - i):
                for tri in (((i, j), (i + 1, j), (i, j + 1)),
                            ((i + 1, j), (i + 1, j + 1), (i, j + 1)) if i + j + 1 < n_sub else None):
                    if tri is None:
                        continue
                    base, tops, sides = [], [], []
                    for (ii, jj) in tri:
                        p, (u, v, w) = pt(ii, jj)
                        bump = 27.0 * max(u, 0) * max(v, 0) * max(w, 0)
                        base.append(lift(p, hin))
                        tops.append(lift(p, hout + puff * bump))
                    for k in range(3):
                        (i0, j0), (i1, j1) = tri[k], tri[(k + 1) % 3]
                        edge = None
                        if j0 == 0 and j1 == 0:
                            edge = 0
                        elif i0 + j0 == n_sub and i1 + j1 == n_sub:
                            edge = 1
                        elif i0 == 0 and i1 == 0:
                            edge = 2
                        sides.append(edge is not None and rims[edge])
                    out.append((fi, _prism(*base, *tops, tuple(sides))))
    return out


#: Face colour per tag, as a multiple of the layer's colour.
SHADE = {"top": 1.0, "bottom": 0.62, "rim": 0.78, "side": 0.78, "cap": 0.84}


def patch_tint(key: str, fi: int) -> float:
    """Quilt patches are not all one dye lot."""
    if key in FABRIC_PUFF:
        return 0.86 + 0.22 * ((fi * 37) % 11) / 10
    return 1.0


def draw_stack(batch: TriangleBatch, cut: Cut | None, explode: float, keys=None, order=None,
               inflate: float = 0.0, quilts: bool = True, sections: dict | None = None,
               channel_discs: bool = True, colours: dict | None = None) -> dict:
    """Every layer as a solid, the wedge cut out. Records each layer's section
    mid-line points (for flows) into ``sections`` keyed (layer, plane)."""
    hs = heights(explode, order, inflate)
    sections = {} if sections is None else sections
    for key, (hin, hout) in hs.items():
        if keys is not None and key not in keys:
            continue
        if key == "skin":
            col = (0.80, 0.78, 0.72, 1.0)
        elif key == "core":
            col = cs.FOAM
        else:
            col = (colours or {}).get(key) or cs.colour(key, 1.0)
        puff = FABRIC_PUFF.get(key, 0.0) if quilts else 0.0
        solids = layer_solids(key, hin, hout, puff, 3 if puff > 0 else 1, lower_only=key == "airbag")
        for fi, faces in solids:
            tint = patch_tint(key, fi) if quilts else 1.0
            if cut is not None:
                faces, caps = cut.apply(faces)
            else:
                caps = []
            normal = dome()["normals"][fi]
            for poly, tag in faces:
                if tag == "side":
                    continue
                _fan(batch, poly, tone(col, SHADE[tag] * tint), normal if tag != "bottom" else -normal)
            for poly, plane, n in caps:
                _fan(batch, poly, tone(col, SHADE["cap"]), n)
                mid = np.mean(poly, axis=0)
                sections.setdefault((key, plane), []).append(mid)
                if channel_discs and key in SECTION:
                    _channels(batch, key, poly, n, hout - hin)
    return sections


def _channels(batch: TriangleBatch, key: str, poly: list, n: np.ndarray, thick: float) -> None:
    """The layer's channels where the cut passes through them."""
    colour, share, pitch = SECTION[key][0], SECTION[key][1], SECTION[key][2]
    mid = np.mean(poly, axis=0)
    radial = mid - dome()["c"]
    radial = radial - n * np.dot(radial, n)
    radial /= np.linalg.norm(radial) + 1e-12
    along = np.cross(n, radial)
    s = [float(np.dot(p - mid, along)) for p in poly]
    lo, hi = min(s), max(s)
    r = min(thick * share, pitch * 0.42)
    if hi - lo < pitch * 0.6:
        disc_on(batch, mid + n * 0.0015, n, r, colour, 8)
        return
    count = max(1, int((hi - lo) / pitch))
    for k in range(count):
        t = lo + (k + 0.5) * (hi - lo) / count
        disc_on(batch, mid + along * t + n * 0.0015, n, r, colour, 8)


def section_line(sections: dict, key: str, plane: int) -> list[np.ndarray]:
    """A layer's section mid-line on one cut face, rim first, crown last."""
    pts = sections.get((key, plane), [])
    return sorted(pts, key=lambda p: float(p[2]))


def flow_along(batch: TriangleBatch, line: list, p: float, colour, direction: int, style: str,
               count: int = 9, size: float = 0.05, normal=None) -> None:
    """Contents moving along a layer's section: down (-1) or up (+1)."""
    if len(line) < 2:
        return
    pts = np.asarray(line)
    seg = np.linalg.norm(np.diff(pts, axis=0), axis=1)
    total = float(seg.sum())
    if total <= 0:
        return
    cum = np.concatenate([[0.0], np.cumsum(seg)])
    for k in range(count):
        s = ((k / count) + p * 0.55 * direction) % 1.0 * total
        i = int(min(len(seg) - 1, np.searchsorted(cum, s, side="right") - 1))
        t = (s - cum[i]) / max(seg[i], 1e-9)
        q = pts[i] + (pts[i + 1] - pts[i]) * t
        d = (pts[i + 1] - pts[i]) / max(seg[i], 1e-9) * direction
        if normal is not None:
            q = q + np.asarray(normal) * 0.004
        if style == "cone":
            batch.cone(q - d * size * 0.5, q + d * size * 0.5, size * 0.38, colour, 8)
        elif style == "drop":
            batch.sphere(q, size * 0.36, colour, 3, 6)
        elif style == "packet":
            batch.box(q, (size * 0.5, size * 0.5, size * 0.5), colour)
        elif style == "pulse":
            batch.sphere(q, size * (0.30 + 0.12 * math.sin((p * 6 + k) * math.pi)), colour, 3, 6)
        elif style == "puff":
            batch.sphere(q, size * 0.45, colour, 3, 6)
        else:
            batch.sphere(q, size * 0.22, colour, 3, 5)


def draw_flows(batch: TriangleBatch, sections: dict, p: float, keys=None, cut: Cut | None = None,
               reverse: dict | None = None) -> None:
    """Every layer's contents moving at once, along both cut faces."""
    for key, spec in SECTION.items():
        if keys is not None and key not in keys:
            continue
        _c, _s, _p, colour, d1, d2, style = spec
        for plane, d in ((1, d1), (2, d2)):
            if reverse and key in reverse:
                d = -d
            n = None
            if cut is not None:
                n = cut.n1 if plane == 1 else cut.n2
            flow_along(batch, section_line(sections, key, plane), p, colour, d, style,
                       count=10, size=0.085, normal=n)


# ----------------------------------------------------------------------
# Stitches: a quilt's seams, sewn
# ----------------------------------------------------------------------

def stitches(batch: TriangleBatch, key: str, h: float, cut: Cut | None, colour=(0.12, 0.10, 0.09, 1.0),
             dash: float = 0.05) -> None:
    """Running stitches round every patch, a little inside its edges."""
    for fi in range(len(dome()["faces"])):
        corners = cs.inset(cs.faces()[fi], 0.035, 0.0)
        pts = [lift(p - cs.faces()[fi].normal * 0.0, h) for p in corners]
        for k in range(3):
            a, b = pts[k], pts[(k + 1) % 3]
            length = float(np.linalg.norm(b - a))
            steps = int(length / dash)
            for s in range(0, steps, 2):
                p0 = a + (b - a) * (s / steps)
                p1 = a + (b - a) * (min(steps, s + 1) / steps)
                if cut is not None and (cut.removed(p0) or cut.removed(p1)):
                    continue
                batch.cylinder(p0, p1, 0.0035, colour, 4)


# ----------------------------------------------------------------------
# Cached stacks: a cut configuration built once, drawn from the GPU
# ----------------------------------------------------------------------

_SECTIONS: dict[str, dict] = {}


def _make_cut(azimuth: float | None) -> Cut | None:
    """``azimuth`` is the camera's: the cut faces it (see :meth:`Cut.facing`)."""
    return None if azimuth is None else Cut.facing(azimuth)


def stack_key(azimuth: float | None, explode: float, keys=None, order=None, inflate: float = 0.0,
              quilts: bool = True, colours: dict | None = None) -> str:
    parts = ["stack", "whole" if azimuth is None else f"{azimuth:.0f}", f"{explode:.2f}", f"{inflate:.2f}",
             "q" if quilts else "f", ",".join(keys) if keys else "all", ",".join(order) if order else "phys"]
    if colours:
        parts.append(",".join(sorted(colours)))
    return "cellwall:" + ":".join(parts)


def build_stack(azimuth: float | None, explode: float, keys=None, order=None, inflate: float = 0.0,
                quilts: bool = True, colours: dict | None = None) -> TriangleBatch:
    """The stack for one configuration, one-sided (for a static layer); its
    section lines are kept for :func:`sections_for`."""
    key = stack_key(azimuth, explode, keys, order, inflate, quilts, colours)
    batch = TriangleBatch()
    sections: dict = {}
    TWO_SIDED[0] = False
    try:
        draw_stack(batch, _make_cut(azimuth), explode, keys, order, inflate, quilts, sections, True, colours)
    finally:
        TWO_SIDED[0] = True
    _SECTIONS[key] = sections
    return batch


def sections_for(azimuth: float | None, explode: float, keys=None, order=None, inflate: float = 0.0,
                 quilts: bool = True, colours: dict | None = None) -> dict:
    key = stack_key(azimuth, explode, keys, order, inflate, quilts, colours)
    if key not in _SECTIONS:
        build_stack(azimuth, explode, keys, order, inflate, quilts, colours)
    return _SECTIONS[key]


def paint_stack(app, azimuth: float | None, explode: float, keys=None, order=None, inflate: float = 0.0,
                quilts: bool = True, colours: dict | None = None) -> dict:
    """Hand a cut stack to the renderer as a static layer; returns its sections."""
    key = stack_key(azimuth, explode, keys, order, inflate, quilts, colours)
    m = cw.landmarks()
    r = m.dome_r + 0.6 + 1.2 * explode
    subject = [m.dome_centre + [x * r, y * r, 0] for x, y in ((1, 0), (-1, 0), (0, 1), (0, -1))] + [
        m.apex + [0, 0, 0.5 + explode]]
    app.static_layer(key, lambda: build_stack(azimuth, explode, keys, order, inflate, quilts, colours),
                     subject)
    return sections_for(azimuth, explode, keys, order, inflate, quilts, colours)


# ----------------------------------------------------------------------
# The local-net: every gasket jumpered to its neighbours
# ----------------------------------------------------------------------

@lru_cache(maxsize=1)
def face_hops() -> dict[int, int]:
    """Hops from the nearest rim port to every face, on the world's own dome."""
    D = dome()
    rim_faces = sorted({o[0] for k, o in D["owners"].items() if len(o) == 1})
    return cwall._hops(len(D["faces"]), D["links"], rim_faces)


def _loop_point(fi: int, a: np.ndarray, b: np.ndarray, h: float) -> np.ndarray:
    """Where face ``fi``'s gasket passes the middle of its edge a-b."""
    f = cs.faces()[fi]
    mid = (a + b) / 2
    toward = f.incentre - mid
    toward -= f.normal * np.dot(toward, f.normal)
    toward /= np.linalg.norm(toward)
    return mid + toward * cs.loop_inset() + f.normal * h


def jumper_paths(outside: bool = False) -> list[tuple[int, int, list]]:
    """Each seam's jumper: from one gasket's port, across the seam -- down
    through the V (inside) or over the ridge (outside) -- to the other's."""
    D = dome()
    fs = cs.faces()
    out = []
    for (va, vb), owners in D["owners"].items():
        if len(owners) != 2:
            continue
        i, j = owners
        a, b = D["v"][va], D["v"][vb]
        hi = fs[i].top - 0.012
        p = _loop_point(i, a, b, hi)
        q = _loop_point(j, a, b, fs[j].top - 0.012)
        n = fs[i].normal + fs[j].normal
        n /= np.linalg.norm(n)
        mid = (a + b) / 2 + n * (fs[i].top + 0.05 if outside else (fs[i].top + fs[i].bottom) / 2)
        out.append((i, j, [p, mid, q]))
    return out


def rim_port_points() -> list[tuple[int, np.ndarray, np.ndarray]]:
    """Each rim edge's port: the gasket point by it, and the manifold below."""
    D = dome()
    fs = cs.faces()
    m = cw.landmarks()
    out = []
    for (va, vb), owners in D["owners"].items():
        if len(owners) != 1:
            continue
        fi = owners[0]
        a, b = D["v"][va], D["v"][vb]
        p = _loop_point(fi, a, b, fs[fi].top - 0.012)
        mid = (a + b) / 2
        outward = np.array([mid[0] - m.dome_centre[0], mid[1] - m.dome_centre[1], 0.0])
        outward /= np.linalg.norm(outward)
        out.append((fi, p, mid + outward * 0.30 + np.array([0.0, 0.0, 0.06])))
    return out


JUMPER = (0.96, 0.98, 1.00, 1.0)
PORT = (0.10, 0.10, 0.12, 1.0)


@lru_cache(maxsize=None)
def jumper_batch(outside: bool = True) -> TriangleBatch:
    """Every jumper and every rim port. On the dome the jumpers are drawn over
    the ridge (the outside seam) where the eye can find them; the bench shows
    the one through the V."""
    b = TriangleBatch()
    for _i, _j, path in jumper_paths(outside):
        for p, q in zip(path, path[1:]):
            b.cylinder(p, q, 0.017, JUMPER, 8)
        b.sphere(path[1], 0.022, JUMPER, 3, 8)
        for p in (path[0], path[-1]):
            b.sphere(p, 0.030, PORT, 3, 8)                    # the drilled port
    for _fi, p, man in rim_port_points():
        b.cylinder(p, man, 0.017, JUMPER, 8)
        b.sphere(p, 0.030, PORT, 3, 8)
        b.box(man, (0.11, 0.11, 0.08), (0.30, 0.32, 0.36, 1.0))
    return b


# ----------------------------------------------------------------------
# A quilt shell: forty patches, each a different shirt
# ----------------------------------------------------------------------

SHIRTS = ((0.86, 0.22, 0.24), (0.20, 0.42, 0.78), (0.95, 0.78, 0.20), (0.22, 0.62, 0.40),
          (0.55, 0.30, 0.66), (0.96, 0.52, 0.18), (0.18, 0.66, 0.72), (0.80, 0.80, 0.78),
          (0.30, 0.30, 0.34), (0.90, 0.45, 0.60))


def quilt_batch(h: float, puff: float = 0.035, n: int = 4, prints: bool = True) -> TriangleBatch:
    """A T-shirt quilt over the whole dome: every triangle its own shirt, with a
    print on it, puffed, stitched round its edges, and showing its thickness at
    the rim."""
    b = TriangleBatch()
    TWO_SIDED[0] = False
    try:
        for fi in range(len(dome()["faces"])):
            shirt = SHIRTS[(fi * 7) % len(SHIRTS)]
            body = (*shirt, 1.0)
            ink = (*(1.0 - 0.75 * np.asarray(shirt)), 1.0)
            a, bb, c = _corners(fi)
            f = cs.faces()[fi]
            grid = {}
            for i in range(n + 1):
                for j in range(n + 1 - i):
                    u, v = i / n, j / n
                    w = 1 - u - v
                    p = a + (bb - a) * u + (c - a) * v
                    grid[(i, j)] = (lift(p, h + puff * 27 * u * v * w), (u, v, w))
            for i in range(n):
                for j in range(n - i):
                    tris = [((i, j), (i + 1, j), (i, j + 1))]
                    if i + j + 1 < n:
                        tris.append(((i + 1, j), (i + 1, j + 1), (i, j + 1)))
                    for t in tris:
                        (p0, w0), (p1, w1), (p2, w2) = (grid[k] for k in t)
                        centre = np.mean([w0, w1, w2], axis=0)
                        # The print: a disc of ink in the middle of each shirt.
                        on_print = prints and np.linalg.norm(centre - np.array([1 / 3, 1 / 3, 1 / 3])) < 0.17
                        _tri2(b, p0, p1, p2, ink if on_print else tone(body, 0.92 + 0.08 * ((i + j) % 2)))
            # Stitches round the patch.
            corners = [lift(p, h + 0.004) for p in cs.inset(f, 0.03, 0.0)]
            for k in range(3):
                p0, p1 = corners[k], corners[(k + 1) % 3]
                steps = max(2, int(np.linalg.norm(p1 - p0) / 0.06))
                for s in range(0, steps, 2):
                    b.cylinder(p0 + (p1 - p0) * s / steps, p0 + (p1 - p0) * min(steps, s + 1) / steps,
                               0.004, (0.95, 0.93, 0.86, 1.0), 4)
            # Its edge at the rim, so the quilt shows its thickness there.
            for k, rim in enumerate(_rim_sides(fi)):
                if rim:
                    pa, pb = (a, bb, c)[k], (a, bb, c)[(k + 1) % 3]
                    _fan(b, [lift(pa, h - 0.02), lift(pb, h - 0.02), lift(pb, h), lift(pa, h)], tone(body, 0.7))
    finally:
        TWO_SIDED[0] = True
    return b


# ----------------------------------------------------------------------
# The sample table: every layer as a swatch, stacked and pulled apart
# ----------------------------------------------------------------------

TABLE = np.array([2.65, -4.55])
TABLE_TOP = 0.78
SWATCH = 0.36
SWATCH_ORDER = ("thermal", "air_in", "fog", "bus", "skin", "core", "osb", "water", "filter", "vacuum",
                "cage", "cap", "airbag", "living")


def swatch_levels() -> dict[str, tuple[float, float]]:
    """Each swatch's bottom and top height over the table: room side lowest."""
    out, z = {}, TABLE_TOP + 0.10
    for key in SWATCH_ORDER:
        if key == "skin":
            t = 0.012
        elif key == "core":
            t = 0.12
        elif key == "airbag":
            t = 0.08
        else:
            t = max(0.014, cwall.thickness_mm(key) / 1000 * 1.6)
        out[key] = (z, z + t)
        z += t + 0.055
    return out


def _slab(b, x0, y0, x1, y1, z0, z1, col) -> None:
    b.box(((x0 + x1) / 2, (y0 + y1) / 2, (z0 + z1) / 2), (x1 - x0, y1 - y0, z1 - z0), col)


@lru_cache(maxsize=1)
def swatch_batch() -> TriangleBatch:
    """The table and the stack of swatches, each showing how its channels are made."""
    b = TriangleBatch()
    tx, ty = TABLE
    half = SWATCH / 2
    # The table.
    _slab(b, tx - 0.55, ty - 0.38, tx + 0.55, ty + 0.38, TABLE_TOP - 0.04, TABLE_TOP, (0.55, 0.40, 0.25, 1.0))
    for dx in (-0.5, 0.5):
        for dy in (-0.33, 0.33):
            _slab(b, tx + dx - 0.03, ty + dy - 0.03, tx + dx + 0.03, ty + dy + 0.03, 0.0, TABLE_TOP - 0.04,
                  (0.40, 0.28, 0.16, 1.0))
    # A post the swatches hang from, so the stack reads as a sample, not a tower.
    b.cylinder((tx + half + 0.06, ty + half + 0.06, TABLE_TOP), (tx + half + 0.06, ty + half + 0.06, 2.25),
               0.012, (0.35, 0.35, 0.38, 1.0), 8)
    x0, x1, y0, y1 = tx - half, tx + half, ty - half, ty + half
    for key, (z0, z1) in swatch_levels().items():
        t = z1 - z0
        if key == "skin":
            _slab(b, x0, y0, x1, y1, z0, z1, (0.80, 0.78, 0.72, 1.0))
            continue
        col = cs.FOAM if key == "core" else cs.colour(key, 1.0)
        if key == "thermal":          # capillary mat: a thin fabric, tubes across it, two headers
            _slab(b, x0, y0, x1, y1, z0, z0 + t * 0.35, tone(col, 0.8))
            for k in range(9):
                y = y0 + 0.03 + k * (SWATCH - 0.06) / 8
                b.cylinder((x0 + 0.03, y, z0 + t * 0.6), (x1 - 0.03, y, z0 + t * 0.6), t * 0.3, col, 8)
            for x in (x0 + 0.03, x1 - 0.03):
                b.cylinder((x, y0 + 0.01, z0 + t * 0.6), (x, y1 - 0.01, z0 + t * 0.6), t * 0.55, tone(col, 0.9), 10)
        elif key == "air_in":         # textile duct: quilted air cells, perforated
            n = 4
            for i in range(n):
                for j in range(n):
                    cx = x0 + (i + 0.5) * SWATCH / n
                    cy = y0 + (j + 0.5) * SWATCH / n
                    _slab(b, cx - SWATCH / n * 0.47, cy - SWATCH / n * 0.47, cx + SWATCH / n * 0.47,
                          cy + SWATCH / n * 0.47, z0, z0 + t * 0.6, tone(col, 0.9))
                    b.sphere((cx, cy, z0 + t * 0.6), SWATCH / n * 0.42, tone(col, 1.0), 4, 10)
                    b.sphere((cx, cy, z0 + t * 0.6 + SWATCH / n * 0.40), 0.006, (0.15, 0.25, 0.18, 1.0), 2, 5)
        elif key == "fog":            # hose sleeves sewn to a strip
            _slab(b, x0, y0, x1, y1, z0, z0 + t * 0.3, tone(col, 0.8))
            for k in range(3):
                y = y0 + (k + 0.5) * SWATCH / 3
                b.cylinder((x0, y, z0 + t * 0.7), (x1, y, z0 + t * 0.7), t * 0.55, col, 12)
                b.cylinder((x0 - 0.002, y, z0 + t * 0.7), (x1 + 0.002, y, z0 + t * 0.7), t * 0.3,
                           (0.35, 0.35, 0.38, 1.0), 10)
        elif key == "bus":            # e-textile: thread traces and a node
            _slab(b, x0, y0, x1, y1, z0, z1, tone(col, 0.85))
            for k in range(5):
                y = y0 + 0.04 + k * 0.07
                b.cylinder((x0 + 0.02, y, z1 + 0.001), (x1 - 0.02, y, z1 + 0.001), 0.0025, (0.95, 0.85, 0.40, 1.0), 4)
            b.box(((x0 + x1) / 2, (y0 + y1) / 2, z1 + 0.008), (0.05, 0.035, 0.014), (0.10, 0.12, 0.30, 1.0))
        elif key == "core":           # the frame: foam, and a member with its C-channel and gasket
            _slab(b, x0 + 0.07, y0, x1, y1, z0, z1, col)
            b.box((x0 + 0.035, (y0 + y1) / 2, (z0 + z1) / 2), (0.07, SWATCH, t), (0.80, 0.58, 0.33, 1.0))
            b.box((x0 + 0.035, (y0 + y1) / 2, z1 + 0.001), (0.02, SWATCH, 0.004), DARK_SLOT)
            b.cylinder((x0 + 0.035, y0 - 0.005, z1 - 0.004), (x0 + 0.035, y1 + 0.005, z1 - 0.004), 0.008,
                       cs.LOOP, 10)
            # A port drilled from the gasket out through the member's side, and its jumper.
            b.cylinder((x0 + 0.035, ty, z1 - 0.004), (x0 - 0.06, ty, z0 + t * 0.5), 0.006, (0.9, 0.97, 1.0, 1.0), 8)
        elif key == "osb":
            _slab(b, x0, y0, x1, y1, z0, z1, col)
            rng = np.random.default_rng(3)
            for _ in range(40):
                px, py = rng.uniform(x0 + 0.02, x1 - 0.02), rng.uniform(y0 + 0.02, y1 - 0.02)
                b.box((px, py, z1 + 0.0008), (rng.uniform(0.02, 0.06), rng.uniform(0.008, 0.02), 0.001),
                      tone(col, rng.uniform(0.8, 1.2)))
        elif key == "water":          # twin-wall: two skins and the ribs between them
            for z in (z0, z1 - t * 0.12):
                _slab(b, x0, y0, x1, y1, z, z + t * 0.12, col)
            for k in range(13):
                y = y0 + k * SWATCH / 12
                _slab(b, x0, y - 0.002, x1, y + 0.002, z0, z1, tone(col, 0.85))
        elif key == "filter":         # pleated media
            n = 10
            for k in range(n):
                xa, xb = x0 + k * SWATCH / n, x0 + (k + 0.5) * SWATCH / n
                xc = x0 + (k + 1) * SWATCH / n
                for p, q in ((xa, xb), (xb, xc)):
                    zlow, zhigh = (z0, z1) if p == xa else (z1, z0)
                    _fan(b, [np.array([p, y0, zlow]), np.array([q, y0, zhigh]), np.array([q, y1, zhigh]),
                             np.array([p, y1, zlow])], tone(col, 0.95 if p == xa else 0.8))
        elif key == "vacuum":         # spacer fabric: two faces and the pile that holds them apart
            for z in (z0, z1 - 0.003):
                _slab(b, x0, y0, x1, y1, z, z + 0.003, col)
            for i in range(10):
                for j in range(10):
                    px, py = x0 + (i + 0.5) * SWATCH / 10, y0 + (j + 0.5) * SWATCH / 10
                    b.cylinder((px, py, z0), (px + 0.004, py, z1), 0.0016, tone(col, 0.7), 3)
        elif key == "cage":           # woven wire
            for k in range(13):
                s = k * SWATCH / 12
                b.cylinder((x0, y0 + s, (z0 + z1) / 2), (x1, y0 + s, (z0 + z1) / 2), 0.0018, STEEL_WIRE, 4)
                b.cylinder((x0 + s, y0, (z0 + z1) / 2), (x0 + s, y1, (z0 + z1) / 2), 0.0018, STEEL_WIRE, 4)
        elif key == "cap":
            _slab(b, x0 - 0.01, y0 - 0.01, x1 + 0.01, y1 + 0.01, z0, z1, col)
        elif key == "airbag":         # drop-stitch: two skins tied by threads, inflated
            _slab(b, x0 + 0.01, y0 + 0.01, x1 - 0.01, y1 - 0.01, z0, z1, col)
            for x in (x0 + 0.01, x1 - 0.01):
                b.cylinder((x, y0 + 0.01, (z0 + z1) / 2), (x, y1 - 0.01, (z0 + z1) / 2), t / 2, tone(col, 0.9), 12)
            for i in range(6):
                for j in range(6):
                    b.sphere((x0 + 0.04 + i * 0.056, y0 + 0.04 + j * 0.056, z1 + 0.001), 0.004,
                             tone(col, 0.6), 2, 5)
        elif key == "living":         # felt pockets, a drip line, and what grows in them
            _slab(b, x0, y0, x1, y1, z0, z1, (0.30, 0.45, 0.26, 1.0))
            b.cylinder((x0, ty, z1 + 0.004), (x1, ty, z1 + 0.004), 0.004, (0.15, 0.15, 0.17, 1.0), 6)
            rng = np.random.default_rng(8)
            for _ in range(26):
                px, py = rng.uniform(x0 + 0.02, x1 - 0.02), rng.uniform(y0 + 0.02, y1 - 0.02)
                tall = rng.uniform(0.03, 0.08)
                b.cone((px, py, z1), (px, py, z1 + tall), tall * 0.35, cs.LEAF if rng.random() < 0.6 else cs.LEAF_LIGHT, 6)
    return b


DARK_SLOT = (0.10, 0.08, 0.07, 1.0)
STEEL_WIRE = (0.82, 0.84, 0.88, 1.0)


def swatch_label_point(key: str) -> np.ndarray:
    z0, z1 = swatch_levels()[key]
    return np.array([TABLE[0] + SWATCH / 2 + 0.25, TABLE[1] - SWATCH / 2, (z0 + z1) / 2])


SWATCH_NAME = {"thermal": "HEAT", "air_in": "AIR", "fog": "FOG", "bus": "BUS", "core": "FRAME",
               "osb": "BOARD", "water": "WATER", "filter": "FILTER", "vacuum": "VACUUM", "cage": "CAGE",
               "cap": "CAP", "airbag": "BLADDER", "living": "PLANTS"}


def swatch_label(key: str) -> str:
    """'WATER: TWIN-WALL SHEET, 10 MM' -- what it does, what it is, how thick."""
    what = cwall.CONSTRUCTION[key][0].upper()
    return f"{SWATCH_NAME[key]}: {what}, {cwall.thickness_mm(key):.0f} MM"


def swatch_flows(batch: TriangleBatch, p: float) -> None:
    """What each swatch carries, moving: hot water in the mat's tubes, air up
    through the duct's cells, water in the flutes, vacuum through the pile."""
    tx, ty = TABLE
    half = SWATCH / 2
    lv = swatch_levels()
    z0, z1 = lv["thermal"]
    for k in range(9):
        y = ty - half + 0.03 + k * (SWATCH - 0.06) / 8
        x = tx - half + 0.03 + ((k * 0.13 + p * 0.8) % 1.0) * (SWATCH - 0.06)
        batch.sphere((x, y, z0 + (z1 - z0) * 0.6), (z1 - z0) * 0.32, (1.0, 0.85, 0.5, 1.0), 2, 6)
    z0, z1 = lv["water"]
    for k in range(12):
        y = ty - half + (k + 0.5) * SWATCH / 12
        x = tx + half - ((k * 0.21 + p * 0.7) % 1.0) * SWATCH
        batch.sphere((x, y, (z0 + z1) / 2), (z1 - z0) * 0.25, (0.85, 0.95, 1.0, 1.0), 2, 6)
    z0, z1 = lv["air_in"]
    for k in range(4):
        cx = tx - half + (k + 0.5) * SWATCH / 4
        zz = z1 + 0.02 + 0.05 * ((p * 1.2 + k * 0.25) % 1.0)
        batch.cone((cx, ty, zz), (cx, ty, zz + 0.03), 0.01, (0.55, 1.0, 0.7, 1.0), 8)


# ----------------------------------------------------------------------
# Fire: a front in the trees to the west, its heat, its embers, and steam
# ----------------------------------------------------------------------

FIRE_AZIMUTH = 90.0       # degrees: the fire comes up the open valley to the north (scene dressing)


@lru_cache(maxsize=1)
def _ground_xyz() -> np.ndarray:
    return np.asarray(cw.layer("ground").vertices, dtype=np.float32).reshape(-1, 10)[:, :3]


def ground_z(x: float, y: float) -> float:
    """The world's own ground height under a point: its nearest terrain vertex."""
    a = _ground_xyz()
    d = (a[:, 0] - x) ** 2 + (a[:, 1] - y) ** 2
    return float(a[int(np.argmin(d)), 2])


def fire_dir() -> np.ndarray:
    a = math.radians(FIRE_AZIMUTH)
    return np.array([math.cos(a), math.sin(a), 0.0])


def fire_side(f: cs.Face) -> bool:
    return float(np.dot(f.normal, fire_dir())) > 0.05


@lru_cache(maxsize=1)
def fire_bases() -> tuple:
    """Where the flames stand, on the ground of the valley, and how tall each is."""
    m = cw.landmarks()
    rng = np.random.default_rng(41)
    out = []
    for _ in range(52):
        a = math.radians(FIRE_AZIMUTH + rng.uniform(-42, 42))
        r = rng.uniform(9.5, 13.5)
        x, y = m.dome_centre[0] + r * math.cos(a), m.dome_centre[1] + r * math.sin(a)
        out.append((np.array([x, y, ground_z(x, y)]), rng.uniform(2.6, 5.6)))
    return tuple(out)


def fire_front(batch: TriangleBatch, p: float, intensity: float = 1.0) -> list[np.ndarray]:
    """Flames along an arc across the valley, flickering; returns their bases."""
    bases = []
    for k, (base, tall0) in enumerate(fire_bases()):
        bases.append(base)
        flick = 0.65 + 0.35 * math.sin(p * 40 + k * 1.7) * math.sin(p * 23 + k)
        tall = tall0 * intensity * (0.75 + 0.25 * flick)
        for layer, col in enumerate(((1.0, 0.25, 0.05, 1.0), (1.0, 0.55, 0.10, 1.0), (1.0, 0.85, 0.35, 1.0))):
            batch.cone(base + np.array([0, 0, 0.1 * layer]), base + np.array([0.15 * math.sin(p * 9 + k), 0,
                       tall * (1 - 0.25 * layer)]), (0.65 - 0.18 * layer) * intensity, col, 7)
    return bases


def radiant(batch: TriangleBatch, faces, p: float, colour=(1.0, 0.45, 0.12, 1.0)) -> None:
    """Heat arriving: arrows from the fire's side onto each face."""
    d = -fire_dir()
    for f in faces:
        end = f.centre + f.normal * (f.top + 0.6)
        t = (p * 1.4 + f.index * 0.17) % 1.0
        start = end - d * (2.6 - 1.8 * t) + np.array([0, 0, 0.3])
        batch.arrow(start, start + d * 0.55, 0.035, colour)


def steam(batch: TriangleBatch, faces, p: float, h: float = 0.30) -> None:
    """Water evaporating off the hot side: where the heat goes."""
    rng = np.random.default_rng(57)
    for f in faces:
        for k in range(3):
            t = (rng.random() + p * 0.9) % 1.0
            q = f.centre + f.normal * (f.top + h + 0.6 * t) + np.array([0, 0, 0.9 * t])
            batch.sphere(q, 0.10 + 0.18 * t, (0.97, 0.98, 1.00, 0.55 * (1 - t)), 4, 8)


def intakes(batch: TriangleBatch, closed: float) -> list[np.ndarray]:
    """A port at every rim corner, outside, under the cap's brim; a shutter
    slides across it as ``closed`` goes from 0 to 1."""
    m = cw.landmarks()
    out = []
    for q in cs.rim_corners():
        o = np.array([q[0] - m.dome_centre[0], q[1] - m.dome_centre[1], 0.0])
        o /= np.linalg.norm(o)
        side = np.array([-o[1], o[0], 0.0])
        port = q + o * 0.24 + np.array([0.0, 0.0, 0.55])
        batch.box(port, (0.22, 0.22, 0.14), (0.30, 0.30, 0.33, 1.0))
        shut = port + side * 0.22 * (1 - closed) + np.array([0, 0, -0.075])
        batch.box(shut, (0.24, 0.24, 0.02), (0.85, 0.20, 0.15, 1.0) if closed > 0.5 else (0.45, 0.45, 0.48, 1.0))
        out.append(port)
    return out


# ----------------------------------------------------------------------
# Uses per network, as bars round the pad
# ----------------------------------------------------------------------

def uses_bars(batch: TriangleBatch, grow: float = 1.0) -> list[tuple[str, np.ndarray, int]]:
    """One bar per network on the ground round the pad, as tall as its uses."""
    mu = cwall.multipliers()
    m = cw.landmarks()
    nets = sorted(mu["per"], key=lambda k: -mu["per"][k])
    hero = math.degrees(math.atan2(cw.HERO_EYE[1] - m.dome_centre[1], cw.HERO_EYE[0] - m.dome_centre[0]))
    out = []
    for k, key in enumerate(nets):
        a = math.radians(hero - 75 + 150 * k / max(1, len(nets) - 1))
        r = m.deck_r + 1.0
        x, y = m.dome_centre[0] + r * math.cos(a), m.dome_centre[1] + r * math.sin(a)
        base = np.array([x, y, ground_z(x, y)])
        h = 0.35 * mu["per"][key] * max(0.02, grow)
        col = cs.colour(key, 1.0) if key in cwall.LAYER else {"local_net": cs.LOOP, "global": cs.GLOW,
                                                               "rings": (0.95, 0.80, 0.35, 1.0)}[key]
        batch.box(base + np.array([0, 0, h / 2]), (0.28, 0.28, h), col)
        out.append((key, base + np.array([0, 0, h + 0.25]), mu["per"][key]))
    return out


def validate_cell_wall_solids() -> None:
    D = dome()
    assert len(D["faces"]) == 40 and len(D["rim"]) == 10 and len(D["links"]) == 55
    hs = heights(0.0)
    assert hs["osb"][0] > cs.faces()[0].top - 0.01 and hs["thermal"][1] < cs.faces()[0].bottom
    cut = Cut(-90.0)
    # A point straight toward the camera is cut away; one behind is kept.
    probe = D["c"] + np.array([0.0, -3.0, 0.5])
    assert cut.removed(probe) and not cut.removed(D["c"] + np.array([0.0, 3.0, 0.5]))
    # Cutting a prism that straddles a plane gives a cap on it.
    solids = layer_solids("water", *hs["water"])
    caps = 0
    for _fi, faces in solids:
        _kept, cs_ = cut.apply(faces)
        caps += len(cs_)
    assert caps > 0
    sec: dict = {}
    batch = TriangleBatch()
    draw_stack(batch, cut, 0.5, sections=sec)
    assert batch.vertices and section_line(sec, "water", 1) and section_line(sec, "water", 2)
    # The local-net on the world's dome matches the facts module's count.
    ln = cwall.local_net()
    assert len(jumper_paths()) == ln["jumpers"] and len(rim_port_points()) == ln["rim_ports"]
    assert max(face_hops().values()) == ln["max_hops_from_rim"], "world and reference agree on hops"
    assert swatch_batch().vertices and quilt_batch(0.4).vertices and jumper_batch().vertices
    assert set(SWATCH_NAME) == set(cwall.LAYER)
    # The cut faces the camera: straight at the camera is removed, behind is kept,
    # and both cut faces turn toward the line of sight.
    face = Cut.facing(-90.0)
    assert face.removed(D["c"] + np.array([0.0, -2.5, 0.5])) and not face.removed(D["c"] + np.array([0, 3.0, 0.5]))
    toward = np.array([0.0, -1.0, 0.0])
    assert float(np.dot(-face.n1, toward)) < 0 or float(np.dot(face.n1, toward)) > 0.5
    assert set(SWATCH_ORDER) == set(cwall.LAYER) | {"skin"}
    lv = swatch_levels()
    assert all(lv[a][1] < lv[b][0] for a, b in zip(SWATCH_ORDER, SWATCH_ORDER[1:])), "swatches never touch"
