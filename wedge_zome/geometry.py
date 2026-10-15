"""A zome framed the wedge way: the geometry, solved in three dimensions.

The zome is the Complete Edition's -- :func:`two_v_demo.panel_method.reference_zome`'s
nine-fold polar zonohedron at 54 degrees, panel side 0.9 m -- with the same
panels (every face above the rim) so this tool, the book and the film cannot
disagree about it. What changes is the stick.

Each rhombus panel is framed flat on a jig from four sticks in a **pinwheel**:
each stick runs along one edge, reaches the corner ahead of it, and its tail
butts the side of the stick behind it. Two ways to make the sticks:

``wedge`` -- the method's own. Each stick is a wedge split from a log (by
default the books' 12 in reference log, eight ways), its trimmed **back laid
flat on the outside** of the panel and its point toward the inside of the
building. A wedge's side faces lean half its point angle away from square, so
two panels meeting at a fold have that much clearance each: the backs close
tight along every **outside** seam, and the inside opens into a V of
(point angle - fold). Every fold of this zome is less than an eighth's point,
so nothing collides, nothing needs a block, and the inside V is a channel.

``square`` -- the non-bevelled method of the Complete Edition, with square
sticks planed from two wedges paired slant to slant (*'Square' on Demand*).
Square-edged panels meet on their inside edges and open a V outside, which is
filled with a **wedge block** -- split from a log 360/fold ways.

Everything is in inches. The cut planes, lengths and saw settings are solved
from the planes themselves, not assumed from the 2-D outline.
"""

from __future__ import annotations

import math
from dataclasses import dataclass, field
from functools import lru_cache

import numpy as np

IN_PER_M = 1 / 0.0254


def unit(v) -> np.ndarray:
    v = np.asarray(v, dtype=float)
    n = float(np.linalg.norm(v))
    return v / n if n > 1e-12 else v


@dataclass(frozen=True)
class Declared:
    key: str
    value: float
    unit: str
    kind: str
    why: str


#: What the wedge zome declares. The zome's own size and pitch come from the
#: panel method's declared table, so the book's zome and this one are one zome.
DECLARED: tuple[Declared, ...] = (
    Declared("log_in", 12.0, "in", "the project's", "the reference trunk the dome books are split from"),
    Declared("splits", 8.0, "ways", "the project's", "eighths: the dome's own wedges, so one pile frames either"),
    Declared("section_in", 72.0, "in", "the project's",
             "the length logs are bucked to for the dome: the longest stick one person sets alone"),
    Declared("sill_in", 3.5, "in", "estimate", "a sill ring the rim's lowest corners sit on"),
)
D = {d.key: d.value for d in DECLARED}


@dataclass(frozen=True)
class Plane:
    point: np.ndarray
    normal: np.ndarray

    def hit(self, origin: np.ndarray, direction: np.ndarray) -> float:
        denom = float(self.normal @ direction)
        return float(self.normal @ (self.point - origin)) / denom


@dataclass
class Stick:
    panel: int
    side: int
    row: int
    method: str
    origin: np.ndarray          # the outside corner of the edge the stick runs along (tail end)
    d: np.ndarray               # along the stick, tail to head
    v: np.ndarray               # in the panel's plane, pointing into the panel
    n: np.ndarray               # the panel's outward normal
    section: tuple              # (v, n) points of the cross-section, in order
    tail: Plane = None
    head: Plane = None
    ends: tuple = ()            # (tail points, head points), one per section point
    role: str = ""
    edge: tuple = ()            # the two zome vertices of the edge it runs along, tail first

    def point(self, s: tuple[float, float], t: float) -> np.ndarray:
        return self.origin + self.v * s[0] + self.n * s[1] + self.d * t

    def solve(self) -> None:
        tails, heads = [], []
        for s in self.section:
            base = self.point(s, 0.0)
            tails.append(base + self.d * self.tail.hit(base, self.d))
            heads.append(base + self.d * self.head.hit(base, self.d))
        self.ends = (tails, heads)

    def lengths(self) -> list[float]:
        tails, heads = self.ends
        return [float(np.linalg.norm(h - t)) for t, h in zip(tails, heads)]

    def cut(self, plane: Plane) -> tuple[float, float]:
        """(mitre, bevel) for an end, the stick lying back-down on the saw table
        with the edge the stick runs along against the fence. Mitre is the swing
        of the blade on the table, bevel its tilt, both from a square cut."""
        p = unit(plane.normal)
        if p @ self.d < 0:
            p = -p
        mitre = math.degrees(math.atan2(float(p @ self.v), float(p @ self.d)))
        bevel = math.degrees(math.asin(max(-1.0, min(1.0, float(p @ self.n)))))
        return mitre, bevel


@dataclass
class Panel:
    index: int
    row: int
    corners: list               # outside corners, in order, inches
    normal: np.ndarray
    acute: float
    sticks: list = field(default_factory=list)


@dataclass
class Seam:
    a: int
    b: int
    panels: tuple
    row_pair: tuple
    fold: float                 # how far one panel turns from the other, degrees
    gap: float                  # the V the method leaves at this seam, degrees
    gap_side: str               # 'inside' (wedge method) or 'outside' (square method)
    length: float


@dataclass
class ZomeModel:
    method: str
    vertices: np.ndarray        # inches, rim at z = 0
    panels: list
    seams: list
    rows: list                  # row numbers, top first
    wedge: object               # square_book.geometry.Wedge
    stick_w: float              # across the stick in the panel's plane
    stick_h: float              # through the panel
    rim: list                   # rim vertex indices, in order round the ring
    posts: list                 # (vertex, height) for rim corners above the sill
    scale: float
    log_in: float = 12.0
    side_in: float = 0.0
    hand: str = "ccw"
    orient: str = "back"

    def sticks(self) -> list:
        return [s for p in self.panels for s in p.sticks]


def _zome():
    from two_v_demo import panel_method as pm
    from two_v_demo.zome_geometry import polar_zonohedron

    count = int(pm.CONSTANTS["zome_n"].value)
    pitch = pm.CONSTANTS["zome_pitch_deg"].value
    side_in = pm.CONSTANTS["zome_side_m"].value * IN_PER_M
    return polar_zonohedron(count, pitch), side_in


def _section(method: str, wedge, orient: str = "back") -> tuple[tuple, float, float]:
    """The stick's cross-section in (into the panel, outward) coordinates.

    ``orient`` is the wedge's way round: ``back`` (its flat back on the outside,
    the method's) or ``point`` (its point on the outside -- shown only so the
    reason for ``back`` can be seen: the seams then open outside)."""
    if method == "wedge":
        c = wedge.chord_eff
        h = wedge.r_eff * math.cos(math.radians(wedge.theta / 2))
        if orient == "point":
            return ((0.0, -h), (c, -h), (c / 2, 0.0)), c, h
        return ((0.0, 0.0), (c, 0.0), (c / 2, -h)), c, h
    from square_book import geometry as sg
    s = sg.best_pair(wedge).planed[0]
    # square sticks: the panel's plane is their inside face; they stand outward
    return ((0.0, 0.0), (s, 0.0), (s, s), (0.0, s)), s, s


@lru_cache(maxsize=32)
def build(method: str = "wedge", log_in: float | None = None, side_in: float | None = None,
          hand: str = "ccw", orient: str = "back") -> ZomeModel:
    """The zome framed one way. ``log_in`` and ``side_in`` default to the
    declared log and the Complete Edition's panel side; ``hand`` turns the
    pinwheel the other way round (``cw``); ``orient`` sets the wedge's way round."""
    from square_book import geometry as sg

    z, ref_side = _zome()
    side_in = side_in or ref_side
    log_in = log_in or D["log_in"]
    scale = side_in / z.strut_length
    verts = np.asarray(z.vertices, dtype=float) * scale
    rim_h = z.rim_height * scale
    verts = verts - np.array([0.0, 0.0, rim_h])
    faces = [tuple(f) for f in z.faces if min(verts[k][2] for k in f) >= -1e-6]
    centre = verts.mean(axis=0)
    wedge = sg.Wedge(log_in, int(D["splits"]))
    section, w, h = _section(method, wedge, orient)

    # rows, top first, by the height of each panel's centre
    cz = [round(float(np.mean([verts[k][2] for k in f])), 4) for f in faces]
    levels = sorted(set(cz), reverse=True)
    panels: list[Panel] = []
    for i, f in enumerate(faces):
        pts = [verts[k] for k in f]
        nrm = unit(np.cross(pts[1] - pts[0], pts[2] - pts[0]))
        if nrm @ (np.mean(pts, axis=0) - centre) < 0:
            f = f[::-1]
            pts = pts[::-1]
            nrm = -nrm
        u, vv = pts[1] - pts[0], pts[3] - pts[0]
        ang = math.degrees(math.acos(float(np.clip(unit(u) @ unit(vv), -1, 1))))
        panels.append(Panel(i, levels.index(cz[i]) + 1, list(f), nrm, min(ang, 180 - ang)))

    for p in panels:
        ids = list(p.corners) if hand == "ccw" else list(p.corners)[::-1]   # cw: the pinwheel turned round
        pts = [verts[k] for k in ids]
        # counter-clockwise seen from outside, so 'into the panel' is n x d
        for k in range(4):
            a, b = pts[k], pts[(k + 1) % 4]
            d = unit(b - a)
            v = unit(np.cross(p.normal, d))
            if v @ (np.mean(pts, axis=0) - a) < 0:
                v = -v
            p.sticks.append(Stick(p.index, k, p.row, method, a, d, v, p.normal, section,
                                  edge=(ids[k], ids[(k + 1) % 4])))
        for k, s in enumerate(p.sticks):
            nxt, prv = p.sticks[(k + 1) % 4], p.sticks[(k - 1) % 4]
            if method == "wedge":
                # head: flush with the next stick's outer side face (it runs on the next edge)
                o, a_ = nxt.point(section[0], 0), nxt.point(section[2], 0)
                s.head = Plane(o, unit(np.cross(nxt.d, a_ - o)))
                # tail: against the previous stick's inner side face
                i_, a2 = prv.point(section[1], 0), prv.point(section[2], 0)
                s.tail = Plane(i_, unit(np.cross(prv.d, a2 - i_)))
            else:
                # square sticks: head flush with the next edge, tail on the previous stick's inner face
                s.head = Plane(nxt.origin, nxt.v)
                s.tail = Plane(prv.point(section[1], 0), prv.v)
            s.solve()
            s.role = "head at the corner, tail on the stick behind"

    seams = _seams(panels, verts, method, wedge, orient)
    rim, posts = _rim(z, verts, faces)
    return ZomeModel(method, verts, panels, seams, sorted({p.row for p in panels}), wedge, w, h,
                     rim, posts, scale, log_in, side_in, hand, orient)


def stick_on(panel, a: int, b: int):
    """The stick of a panel that runs along the edge between vertices a and b."""
    return next(s for s in panel.sticks if set(s.edge) == {a, b})


def _seams(panels, verts, method, wedge, orient="back") -> list:
    owners: dict[tuple[int, int], list] = {}
    for p in panels:
        for k in range(4):
            a, b = p.corners[k], p.corners[(k + 1) % 4]
            owners.setdefault(tuple(sorted((a, b))), []).append((p, k))
    seams = []
    for (a, b), own in owners.items():
        if len(own) != 2:
            continue
        (pa, ka), (pb, kb) = own
        fold = math.degrees(math.acos(float(np.clip(pa.normal @ pb.normal, -1, 1))))
        if method == "wedge":
            sa, sb = stick_on(pa, a, b), stick_on(pb, a, b)
            # the two outer side faces that face each other across the seam
            def face_normal(s):
                o, ap = s.point(s.section[0], 0), s.point(s.section[2], 0)
                return unit(np.cross(s.d, ap - o))
            na, nb = face_normal(sa), face_normal(sb)
            gap = math.degrees(math.acos(float(np.clip(abs(na @ nb), -1, 1))))
            side = "inside" if orient == "back" else "outside"
        else:
            gap, side = fold, "outside"
        seams.append(Seam(a, b, (pa.index, pb.index), tuple(sorted((pa.row, pb.row))), fold, gap, side,
                          float(np.linalg.norm(verts[a] - verts[b]))))
    return seams


def _rim(z, verts, faces) -> tuple[list, list]:
    counts: dict[tuple[int, int], int] = {}
    for f in faces:
        for k in range(4):
            key = tuple(sorted((f[k], f[(k + 1) % 4])))
            counts[key] = counts.get(key, 0) + 1
    rim = sorted({i for e, c in counts.items() if c == 1 for i in e},
                 key=lambda i: math.atan2(float(verts[i][1]), float(verts[i][0])))
    low = min(float(verts[i][2]) for i in rim)
    posts = [(i, float(verts[i][2]) - low) for i in rim if float(verts[i][2]) - low > 1e-6]
    return rim, posts


# ----------------------------------------------------------------------
# What the shop needs
# ----------------------------------------------------------------------

def stick_types(model: ZomeModel) -> list[dict]:
    """Every distinct stick, by row: its lengths and both end cuts, and how many."""
    groups: dict[tuple, dict] = {}
    for s in model.sticks():
        lens = s.lengths()
        tm, tb = s.cut(s.tail)
        hm, hb = s.cut(s.head)
        key = (s.row, round(lens[0], 2), round(tm, 1), round(tb, 1), round(hm, 1), round(hb, 1))
        g = groups.setdefault(key, {"row": s.row, "count": 0, "outer": lens[0], "lengths": lens,
                                    "tail": (tm, tb), "head": (hm, hb), "longest": max(lens)})
        g["count"] += 1
    out = sorted(groups.values(), key=lambda g: (g["row"], -g["count"]))
    letters = "ABCDEFGHIJKLMNOP"
    per_row: dict[int, int] = {}
    for g in out:
        k = per_row.get(g["row"], 0)
        g["name"] = f"R{g['row']}{letters[k]}"
        per_row[g["row"]] = k + 1
    return out


def rows(model: ZomeModel) -> list[dict]:
    out = []
    for r in model.rows:
        ps = [p for p in model.panels if p.row == r]
        ss = [s for s in model.seams if r in s.row_pair]
        out.append({"row": r, "panels": len(ps), "acute": ps[0].acute,
                     "fold_max": max(s.fold for s in ss), "gap_min": min(s.gap for s in ss),
                     "gap_max": max(s.gap for s in ss)})
    return out


def blocks(model: ZomeModel) -> list[dict]:
    """Square method only: the wedge block each seam's outside V needs, and the
    split that makes it -- a wedge's point is 360/n, the V is the fold."""
    out: dict[float, dict] = {}
    for s in model.seams:
        key = round(s.fold, 1)
        g = out.setdefault(key, {"fold": s.fold, "count": 0, "length": s.length,
                                 "split_exact": 360.0 / s.fold, "split": round(360.0 / s.fold)})
        g["count"] += 1
    for g in out.values():
        g["split_error"] = 360.0 / g["split"] - g["fold"]
    return sorted(out.values(), key=lambda g: g["fold"])


def stock(model: ZomeModel) -> dict:
    """Wedges and log sections the frame takes, cut from the dome's own section length."""
    from square_book import geometry as sg

    types = stick_types(model)
    kerf = sg.D["kerf_in"]
    # every stick is cut from a wedge of the dome's section length; the longest sets the count
    sticks = sum(g["count"] for g in types)
    longest = max(g["longest"] for g in types)
    each = int((D["section_in"] + kerf) // (longest + kerf))
    wedges = math.ceil(sticks / each)
    if model.method == "square":
        wedges *= 2                      # two wedges paired for every square stick
    sections = math.ceil(wedges / int(D["splits"]))
    return {"sticks": sticks, "sticks_per_wedge": each, "wedges": wedges, "sections": sections,
            "longest": longest}


def validate(model: ZomeModel | None = None) -> None:
    for method in ("wedge", "square"):
        m = model if (model and model.method == method) else build(method)
        assert len(m.panels) == 36, len(m.panels)
        assert len(m.rows) == 4
        for p in m.panels:
            pts = [m.vertices[k] for k in p.corners]
            # flat: the fourth corner lies in the plane of the first three
            assert abs(float((pts[3] - pts[0]) @ p.normal)) < 1e-6
            # rhombus
            sides = [np.linalg.norm(pts[(k + 1) % 4] - pts[k]) for k in range(4)]
            assert max(sides) - min(sides) < 1e-6
            for s in p.sticks:
                lens = s.lengths()
                assert all(0 < L < sides[0] + 1e-6 for L in lens), lens
        for sm in m.seams:
            assert sm.gap > 0
            if method == "wedge":
                # the clearance each side is half the point; the V left is the point less the fold
                assert abs(sm.gap - (m.wedge.theta - sm.fold)) < 0.05, (sm.gap, m.wedge.theta, sm.fold)
        if method == "wedge":
            # the outside closes: each stick's outer back edge lies on its panel's edge
            for p in m.panels:
                pts = [m.vertices[k] for k in p.corners]
                for k, s in enumerate(p.sticks):
                    tails, heads = s.ends
                    assert np.linalg.norm(heads[0] - pts[(k + 1) % 4]) < 1e-6
    # the book's rows agree with this model's
    from two_v_demo import panel_method as pm
    ref = pm.reference_zome()
    mine = rows(build("square"))
    for a, b in zip(ref, mine):
        assert abs(a.acute_deg - b["acute"]) < 0.05 and abs(a.fold_deg - b["fold_max"]) < 0.05, (a, b)


if __name__ == "__main__":
    validate()
    for method in ("wedge", "square"):
        m = build(method)
        print(method, len(m.panels), "panels", len(m.seams), "seams", "posts", len(m.posts))
        for r in rows(m):
            print("  ", {k: round(v, 2) if isinstance(v, float) else v for k, v in r.items()})
        for g in stick_types(m):
            print("  ", g["name"], g["count"], [round(x, 2) for x in g["lengths"]],
                  "tail", [round(x, 1) for x in g["tail"]], "head", [round(x, 1) for x in g["head"]])
        print("  ", stock(m))
    for b in blocks(build("square")):
        print({k: round(v, 2) if isinstance(v, float) else v for k, v in b.items()})
