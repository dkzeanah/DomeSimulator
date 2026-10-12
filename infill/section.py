"""The pieces seen end-on, and how they nest.

Every log piece is a sector of a log: an eighth (45 degrees), or an eighth
bandsawn into two sixteenths (22.5) or four thirty-seconds (11.25). Its two
sawn faces lose half a kerf each -- a chainsaw kerf where the log was split
in eight, a bandsaw kerf where a wedge was sliced -- so the point comes out
blunted, which is real and is drawn. The curved face is bark.

A piece can lie six ways in the frame's thickness (the ``POSES``): on a sawn
face against the flat side or against the open side, point toward or away
from the frame wall, or standing on its point or on its bark. Laid down,
every new piece is slid toward the frame until it touches something
(:func:`pack`) -- so pitches, gaps and coverage are measured off the shapes,
not assumed. Boards and louvers are spaced, not packed (:func:`spaced`).

Section coordinates: ``x`` across the runs, away from the wall the runs
start at (the frame member's point is at ``x = 0`` on the flat side); ``z``
up through the panel, flat side 0, open side ``T``.
"""

from __future__ import annotations

import math
from dataclasses import dataclass

import numpy as np

from . import geom2d as g2
from .constants import C

ARC = 32


@dataclass(frozen=True)
class Stock:
    key: str
    label: str
    kind: str                 # "sector" | "board"
    radius: float = 0.0       # sector: pith to bark
    angle_deg: float = 0.0    # sector: included angle
    kerf_a: float = 0.0       # sector: half-kerf lost off each sawn face
    kerf_b: float = 0.0
    width: float = 0.0        # board
    thick: float = 0.0
    length: float = 0.0       # the longest piece the stock comes in
    per_log: int = 0          # sector: pieces one log section yields

    def local(self) -> np.ndarray:
        """The cross-section: a sector's point near the origin, its bisector
        up +y; a board from (−w/2, 0) to (w/2, t)."""
        if self.kind == "board":
            w, t = self.width, self.thick
            return np.array([[-w / 2, 0.0], [w / 2, 0.0], [w / 2, t], [-w / 2, t]])
        R, half = self.radius, math.radians(self.angle_deg / 2)
        d1 = np.array([-math.sin(half), math.cos(half)])
        d2 = np.array([math.sin(half), math.cos(half)])
        n1 = np.array([math.cos(half), math.sin(half)])
        n2 = np.array([-math.cos(half), math.sin(half)])
        k1, k2 = self.kerf_a, self.kerf_b
        # The blunted point: where the two kerf-offset faces meet.
        A = np.array([n1, n2])
        p0 = np.linalg.solve(A, np.array([k1, k2]))
        e1 = k1 * n1 + d1 * math.sqrt(max(0.0, R * R - k1 * k1))
        e2 = k2 * n2 + d2 * math.sqrt(max(0.0, R * R - k2 * k2))
        a1, a2 = math.atan2(e1[1], e1[0]), math.atan2(e2[1], e2[0])
        arc = [np.array([R * math.cos(a), R * math.sin(a)]) for a in np.linspace(a1, a2, ARC)]
        return np.array([p0, e1, *arc[1:-1], e2])

    @property
    def area(self) -> float:
        return g2.area(self.local())

    @property
    def face_width(self) -> float:
        """The usable width of a sawn face, point to bark."""
        if self.kind == "board":
            return self.width
        return float(np.linalg.norm(self.local()[1] - self.local()[0]))


def stocks(log_in: float, strut_in: float) -> dict[str, Stock]:
    """Every stock the calculator knows, for logs of this diameter."""
    R = log_in / 2
    kc, kb = C["chainsaw_kerf_in"] / 2, C["bandsaw_kerf_in"] / 2
    return {
        "w8": Stock("w8", "Wedge (1/8 of a log)", "sector", R, 45.0, kc, kc, length=strut_in, per_log=8),
        "s16": Stock("s16", "1/16 slice (a wedge bandsawn in two)", "sector", R, 22.5, kc, kb,
                     length=strut_in, per_log=16),
        # Four slices share the wedge's two chainsaw faces and three bandsaw cuts.
        "s32": Stock("s32", "1/32 slice (a wedge bandsawn in four)", "sector", R, 11.25,
                     (kc + 3 * kb) / 4, (kc + 3 * kb) / 4,
                     length=strut_in, per_log=32),
        "fence": Stock("fence", "Fence picket", "board", width=C["fence_w_in"], thick=C["fence_t_in"],
                       length=C["fence_l_in"]),
        "milled": Stock("milled", "Milled 1x6 board", "board", width=C["milled_w_in"],
                        thick=C["milled_t_in"], length=C["milled_l_in"]),
    }


# ----------------------------------------------------------------------
# Poses: how a piece lies in the frame's thickness
# ----------------------------------------------------------------------

POSES = {
    "FDR": "on a sawn face against the flat side, point toward the open run (like the frame)",
    "FUL": "flipped over: sawn face against the open side, point back toward the wall",
    "FDL": "on a sawn face against the flat side, point back toward the wall",
    "FUR": "flipped over: sawn face against the open side, point toward the open run",
    "PD": "standing on its point, bark toward the open side",
    "PU": "hanging point-up, bark toward the flat side",
    "BD": "board flat against the flat side",
    "BU": "board flat against the open side",
    "BE": "board on edge",
}


def _rot(poly: np.ndarray, deg: float) -> np.ndarray:
    a = math.radians(deg)
    R = np.array([[math.cos(a), -math.sin(a)], [math.sin(a), math.cos(a)]])
    return poly @ R.T


def posed(stock: Stock, pose: str, T: float) -> np.ndarray:
    """The piece's section in the frame's thickness, at an arbitrary x."""
    p = stock.local()
    if stock.kind == "board":
        if pose == "BE":
            p = _rot(p, 90.0)
        top = pose == "BU"
    else:
        phi = stock.angle_deg
        rotation = {"FDR": 90 - phi / 2, "FUL": -phi / 2 - 90, "FDL": phi / 2 - 90,
                    "FUR": 90 + phi / 2, "PD": 0.0, "PU": 180.0}[pose]
        p = _rot(p, rotation)
        top = pose in ("FUL", "FUR", "PU")
    if top:
        p = p + np.array([0.0, T - p[:, 1].max()])
    else:
        p = p - np.array([0.0, p[:, 1].min()])
    return fit(p, T)


def fit(p: np.ndarray, T: float) -> np.ndarray:
    """A piece taller than the frame is ripped flush with both faces."""
    if p[:, 1].max() > T + 1e-9:
        p = g2.clip_halfplane(p, (0.0, T), (0.0, -1.0))
    if p[:, 1].min() < -1e-9:
        p = g2.clip_halfplane(p, (0.0, 0.0), (0.0, 1.0))
    return p


def trim(stock: Stock, pose: str, T: float) -> float:
    """How much has to be ripped off a piece in this pose to sit flush."""
    raw = posed_raw(stock, pose, T)
    return max(0.0, float(raw[:, 1].max() - raw[:, 1].min()) - T)


def posed_raw(stock: Stock, pose: str, T: float) -> np.ndarray:
    p = stock.local()
    if stock.kind == "board":
        if pose == "BE":
            p = _rot(p, 90.0)
        return p - np.array([0.0, p[:, 1].min()])
    phi = stock.angle_deg
    rotation = {"FDR": 90 - phi / 2, "FUL": -phi / 2 - 90, "FDL": phi / 2 - 90,
                "FUR": 90 + phi / 2, "PD": 0.0, "PU": 180.0}[pose]
    p = _rot(p, rotation)
    return p - np.array([0.0, p[:, 1].min()])


def frame_section(radius: float, angle_deg: float) -> np.ndarray:
    """The frame member end-on: lying on a sawn face, point at x = 0."""
    s = Stock("frame", "frame", "sector", radius, angle_deg)
    p = posed_raw(s, "FDR", 0.0)
    bottom = p[np.abs(p[:, 1]) < 1e-9]
    return p - np.array([bottom[:, 0].max(), 0.0])


# ----------------------------------------------------------------------
# Packing
# ----------------------------------------------------------------------

def extents(poly: np.ndarray, zs: np.ndarray) -> tuple[np.ndarray, np.ndarray]:
    """For each height, the polygon's leftmost and rightmost x (nan where
    the height misses it)."""
    lo = np.full(len(zs), np.nan)
    hi = np.full(len(zs), np.nan)
    p = np.asarray(poly, float)
    for i in range(len(p)):
        a, b = p[i], p[(i + 1) % len(p)]
        z0, z1 = a[1], b[1]
        if abs(z1 - z0) < 1e-12:
            sel = np.abs(zs - z0) < 1e-9
            for x in (a[0], b[0]):
                lo[sel] = np.fmin(lo[sel], x)
                hi[sel] = np.fmax(hi[sel], x)
            continue
        zmin, zmax = min(z0, z1), max(z0, z1)
        sel = (zs >= zmin - 1e-12) & (zs <= zmax + 1e-12)
        if not np.any(sel):
            continue
        x = a[0] + (zs[sel] - z0) * (b[0] - a[0]) / (z1 - z0)
        lo[sel] = np.fmin(lo[sel], x)
        hi[sel] = np.fmax(hi[sel], x)
    return lo, hi


@dataclass
class Placed:
    stock: Stock
    pose: str
    poly: np.ndarray

    @property
    def x_lo(self) -> float:
        return float(self.poly[:, 0].min())

    @property
    def x_hi(self) -> float:
        return float(self.poly[:, 0].max())


def pack(T: float, wall: np.ndarray, sequence: list[tuple[Stock, str]], count: int,
         gap: float = 0.0, samples: int = 600) -> list[Placed]:
    """Lay ``count`` pieces, cycling through ``sequence``, each slid toward
    the wall until it touches the wall or a piece already down."""
    top = max(T, float(wall[:, 1].max()))
    for stock, pose in sequence:
        top = max(top, float(posed(stock, pose, T)[:, 1].max()))
    zs = np.linspace(0.0, top, samples)
    _lo, env = extents(wall, zs)
    out: list[Placed] = []
    for i in range(count):
        stock, pose = sequence[i % len(sequence)]
        p = posed(stock, pose, T)
        lo, hi = extents(p, zs)
        both = ~np.isnan(lo) & ~np.isnan(env)
        if np.any(both):
            shift = float(np.max(env[both] + gap - lo[both]))
        else:
            # Nothing at this piece's heights yet: start it at the wall's foot.
            shift = float(np.nanmax(env)) + gap - float(np.nanmin(lo))
        p = p + np.array([shift, 0.0])
        out.append(Placed(stock, pose, p))
        _l, h = extents(p, zs)
        env = np.where(np.isnan(env), h, np.where(np.isnan(h), env, np.fmax(env, h)))
    return out


def spaced(T: float, start: float, layout: list[tuple[Stock, str, float, float]]) -> list[Placed]:
    """Pieces at chosen places: (stock, pose, x of the piece's left edge,
    tilt in degrees about its own middle)."""
    out = []
    for stock, pose, x, tilt in layout:
        p = posed(stock, pose, T)
        if tilt:
            c = p.mean(axis=0)
            p = _rot(p - c, tilt) + c
            p = p - np.array([0.0, max(0.0, p[:, 1].min() - 0.0)]) if p[:, 1].min() > 0 else p
            if p[:, 1].min() < 0:
                p = p - np.array([0.0, p[:, 1].min()])
        p = p + np.array([start + x - p[:, 0].min(), 0.0])
        out.append(Placed(stock, pose, p))
    return out


# ----------------------------------------------------------------------
# What a section measures
# ----------------------------------------------------------------------

def measure(placed: list[Placed], T: float, period: int, x0: float = 0.0) -> dict:
    """Pitch of one repeat, how much of the thickness is wood, and what
    light and air can get through."""
    n = len(placed)
    reps = n // period
    if reps >= 3:
        starts = [placed[k * period].x_lo for k in range(reps)]
        pitch = float(np.mean(np.diff(starts[1:])))
        a0, a1 = starts[1], starts[-1]
        span = a1 - a0
        mid = placed[period: (reps - 1) * period]
    else:
        pitch = placed[-1].x_hi - placed[0].x_lo
        a0, a1, span, mid = placed[0].x_lo, placed[-1].x_hi, placed[-1].x_hi - placed[0].x_lo, placed
    span = max(span, 1e-9)
    solid = sum(g2.area(p.poly) for p in mid) / (span * T) if reps >= 3 else \
        sum(g2.area(p.poly) for p in placed) / (span * T)
    # Plan view: which x are covered by any piece seen straight on.
    xs = np.linspace(a0, a1, 2000)
    covered = np.zeros_like(xs, dtype=bool)
    for p in placed:
        covered |= (xs >= p.x_lo - 1e-9) & (xs <= p.x_hi + 1e-9)
    see_through = 1.0 - float(covered.mean())
    # Seam kinds: what touches what between neighbours.
    return {"pitch": pitch, "per_period": period, "solid": min(1.0, solid),
            "see_through": see_through, "pieces_per_ft": 12.0 * period / pitch if pitch > 0 else 0.0}


def min_gap(a: np.ndarray, b: np.ndarray) -> float:
    """Closest approach of two polygons (sampled along their edges)."""
    def dense(p):
        pts = []
        for i in range(len(p)):
            u, v = p[i], p[(i + 1) % len(p)]
            for t in np.linspace(0, 1, 12, endpoint=False):
                pts.append(u + (v - u) * t)
        return np.array(pts)
    A, B = dense(a), dense(b)
    d = np.sqrt(((A[:, None, :] - B[None, :, :]) ** 2).sum(axis=2))
    return float(d.min())


def validate_section() -> None:
    st = stocks(12.0, 72.0)
    w8 = st["w8"]
    # A blunted wedge still has nearly the whole sector's area.
    full = math.pi * 6 ** 2 / 8
    lost = (w8.kerf_a + w8.kerf_b) * w8.radius
    assert abs(w8.area - (full - lost)) < 0.05, (w8.area, full - lost)
    # Slices: the 1/16 halves add back to less than a wedge (one bandsaw kerf).
    assert st["s16"].area * 2 < full and st["s32"].area * 4 < st["s16"].area * 2
    T = 6.0 * math.sin(math.radians(45))
    wall = frame_section(6.0, 45.0)
    # The frame's slant mates exactly with a flipped wedge: no gap, no overlap.
    ideal = Stock("ideal", "ideal", "sector", 6.0, 45.0)
    placed = pack(T, wall, [(ideal, "FUL")], 1)
    zs = np.linspace(0.05, T - 0.05, 50)
    _lo, wall_hi = extents(wall, zs)
    lo, _hi = extents(placed[0].poly, zs)
    ok = ~np.isnan(lo) & ~np.isnan(wall_hi)
    assert ok.sum() > 40, "the wall and the first piece share their heights"
    assert np.allclose(lo[ok], wall_hi[ok], atol=1e-6), "the flipped wedge lies on the frame's slant"
    assert abs(float(wall[:, 1].max()) - T) < 1e-6 and abs(float(wall[:, 0].min()) + 6.0) < 1e-6
    # Alternating flips repeat with a steady pitch, and close up tight.
    seq = pack(T, wall, [(w8, "FUL"), (w8, "FDR")], 12)
    m = measure(seq, T, 2)
    assert m["pitch"] > 0 and 0.6 < m["solid"] < 1.0
    for p in seq:
        assert p.poly[:, 1].min() > -1e-6 and p.poly[:, 1].max() < T + 1e-6
