"""The triangles to be filled or covered, solved from the max strut length.

The frame is the wedge dome's: three log sectors per triangle in a same-handed
pinwheel, each lying on one sawn face. :func:`two_v_demo.wedge_geometry.radius_for_member_length`
finds the dome whose longest member is the max strut length; its 40 panels
come in two shapes, and :func:`pinwheel_panels` gives every member's cut length.

A sector lying on a sawn face has its point toward the opening and its
other sawn face rising at the sector angle -- 45 degrees for an eighth of a
log -- leaning back over itself. So the opening is a tray: smallest at the
flat side, where the members' points are, and widening up the slope to the
open side, one panel-thickness higher. Every infill piece rests on, or mates
to, that slope.

Coordinates: inches; ``x, y`` in the panel's plane with the base edge along
``y = 0``; ``z`` up from the flat side (0) to the open side (``thickness``).
"""

from __future__ import annotations

import math
from dataclasses import dataclass, field
from functools import lru_cache

import numpy as np

from . import geom2d as g2
from .constants import C


@dataclass(frozen=True)
class Spec:
    """What the person enters."""

    max_strut_in: float = 72.0
    frame_log_in: float = 12.0
    """Diameter of the logs the frame members were split from."""
    splits: int = 8
    gasket_in: float = C["gasket_in"]

    @property
    def sector_deg(self) -> float:
        return 360.0 / self.splits

    @property
    def radius_in(self) -> float:
        """Pith to bark of a frame member."""
        return self.frame_log_in / 2.0

    @property
    def thickness_in(self) -> float:
        """How thick the frame stands, flat side to open side."""
        return self.radius_in * math.sin(math.radians(min(90.0, self.sector_deg)))

    @property
    def wall_deg(self) -> float:
        """The opening's walls, measured from the panel's plane."""
        return self.sector_deg


@dataclass
class PanelType:
    name: str
    label: str
    count: int
    tri: np.ndarray
    """The nominal triangle (mathematical vertices), 2-D, base along y = 0."""
    edge_class: tuple[str, str, str]
    edge_len: tuple[float, float, float]
    member_len: tuple[float, float, float]
    spec: Spec = field(repr=False)
    folds: tuple = (None, None, None)

    # -- the opening ---------------------------------------------------------
    def inset_at(self, z: float) -> float:
        """How far the opening's wall stands in from the nominal edge at
        height ``z``."""
        s = self.spec
        return s.gasket_in / 2 + s.radius_in - z / math.tan(math.radians(s.wall_deg))

    def opening(self, z: float = 0.0) -> np.ndarray:
        return g2.inset_triangle(self.tri, self.inset_at(z))

    def outline(self) -> np.ndarray:
        """The panel's own outside edge: the nominal triangle less half a gasket."""
        return g2.inset_triangle(self.tri, self.spec.gasket_in / 2)

    def edge(self, k: int) -> tuple[np.ndarray, np.ndarray]:
        return self.tri[k], self.tri[(k + 1) % 3]

    def inward(self, k: int) -> np.ndarray:
        a, b = self.edge(k)
        n = g2.perp(g2.unit(b - a))
        centre = self.tri.mean(axis=0)
        return n if float(np.dot(n, centre - a)) > 0 else -n

    def wall_plane(self, k: int) -> tuple[np.ndarray, float]:
        """Edge ``k``'s wall as ``n . X = d`` in (x, y, z), ``n`` pointing
        into the opening. The wall leans back over the frame member."""
        m = self.inward(k)
        a, _b = self.edge(k)
        cot = 1.0 / math.tan(math.radians(self.spec.wall_deg))
        n = np.array([m[0], m[1], cot])
        d = float(np.dot(m, a)) + self.spec.gasket_in / 2 + self.spec.radius_in
        length = float(np.linalg.norm(n))
        return n / length, d / length

    # -- the frame members, for drawing --------------------------------------
    def members(self) -> list[np.ndarray]:
        """Each frame member's footprint on the flat side, as a pinwheel."""
        return [poly for poly, _l, _d in g2.pinwheel(self.tri, self.spec.radius_in, self.spec.gasket_in / 2)]

    def fold_deg(self, k: int) -> float | None:
        """How sharply the dome folds at edge ``k``: the angle between this
        panel and the one across the seam (None on the rim)."""
        return self.folds[k]


def _flatten(corners3: np.ndarray, base: int) -> np.ndarray:
    """A face's three corners as a flat triangle, edge ``base`` along y = 0."""
    order = [base, (base + 1) % 3, (base + 2) % 3]
    a, b, c = (corners3[i] for i in order)
    ab = float(np.linalg.norm(b - a))
    ac = float(np.linalg.norm(c - a))
    bc = float(np.linalg.norm(c - b))
    x = (ab * ab + ac * ac - bc * bc) / (2 * ab)
    y = math.sqrt(max(0.0, ac * ac - x * x))
    return np.array([[0.0, 0.0], [ab, 0.0], [x, y]]), order


@lru_cache(maxsize=32)
def solve(spec: Spec) -> dict:
    """The dome for this max strut length, and its two panel types."""
    from two_v_demo import wedge_geometry as wg

    radius = wg.radius_for_member_length(spec.max_strut_in, spec.radius_in, spec.gasket_in)
    panels = wg.pinwheel_panels(radius, spec.radius_in, spec.gasket_in)
    groups: dict[tuple, list] = {}
    for p in panels:
        key = tuple(sorted(m.edge_class for m in p.members))
        groups.setdefault(key, []).append(p)
    # Which panels meet at each edge, for the fold across every seam.
    by_edge: dict[tuple, list] = {}
    for p in panels:
        for m in p.members:
            by_edge.setdefault(m.edge, []).append(p)

    def fold(p, m):
        other = [q for q in by_edge[m.edge] if q is not p]
        if not other:
            return None
        c = float(np.clip(np.dot(p.normal, other[0].normal), -1.0, 1.0))
        return math.degrees(math.acos(c))
    types = []
    for key, members in sorted(groups.items(), key=lambda kv: -len(kv[1])):
        # An interior panel if there is one, so every edge has a seam.
        p = next((q for q in members if all(len(by_edge[m.edge]) == 2 for m in q.members)), members[0])
        classes = [m.edge_class for m in p.members]
        # Put the odd edge out (or edge 0) along the base.
        base = next((i for i, c in enumerate(classes) if classes.count(c) == 1), 0)
        tri, order = _flatten(np.asarray(p.corners, float), base)
        cls = tuple(classes[i] for i in order)
        mem = tuple(float(p.members[i].length_in) for i in order)
        lens = tuple(float(p.members[i].edge_length_in) for i in order)
        name = "".join(c[0] for c in cls)
        label = {"LSS": "Long base, two short sides", "LLL": "Three long sides (equilateral)"}.get(
            name, name)
        folds = tuple(fold(p, p.members[i]) for i in order)
        types.append(PanelType(name=name, label=label, count=len(members), tri=tri,
                               edge_class=cls, edge_len=lens, member_len=mem, spec=spec, folds=folds))
    return {"radius_in": radius, "diameter_ft": 2 * radius / 12.0, "panels": len(panels),
            "types": types}


def validate_frame() -> None:
    s = Spec()
    d = solve(s)
    assert d["panels"] == 40 and sum(t.count for t in d["types"]) == 40
    assert len(d["types"]) == 2
    assert abs(max(max(t.member_len) for t in d["types"]) - s.max_strut_in) < 1e-3
    for t in d["types"]:
        lo, hi = t.opening(0.0), t.opening(s.thickness_in)
        assert g2.area(hi) > g2.area(lo) > 0, "the tray widens toward the open side"
        # The wall plane holds the opening's edge at both heights.
        for k in range(3):
            n, dd = t.wall_plane(k)
            for z, poly in ((0.0, lo), (s.thickness_in, hi)):
                # some vertex pair of the opening lies on the wall
                vals = [abs(float(np.dot(n, [v[0], v[1], z])) - dd) for v in poly]
                assert sorted(vals)[1] < 1e-6, (k, z, vals)
        assert all(f is not None and 10 < f < 30 for f in t.folds), t.folds
        # Drawn members match the solver's cut lengths.
        for k, m in enumerate(t.members()):
            length = float(np.linalg.norm(m[1] - m[0]))
            assert abs(length - t.member_len[k]) < 1e-6, (length, t.member_len[k])
