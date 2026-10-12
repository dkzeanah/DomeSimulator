"""The floor base: a pentagon of half trunks, and the structure inside it.

The outside is the owner's five 20 ft half trunks standing on edge, round
back out, flat face in, mitred at the corners -- the pentagon whose curved
backs measure the full 20 ft. Inside it goes one of several patterns, each
built from whichever materials are chosen for its two roles:

* **primary** members -- the star, the spokes, the beams, or the rings --
  which land on piers (or on a gravel bed) at their joints;
* **secondary** members -- joists -- which fill each space between the
  primaries and hang off their faces.

Materials: raw trunks, half trunks (on edge, or flat side up), quarter
trunks, 4x4, 6x6 and 2x6 to 2x12 on edge. Every joint is solved: where
members meet at a point they share it (mitred against each other, the
mitre running through the corner where their faces cross); where a member
lands on the side of a heavier one it is cut to that member's face. Every
piece becomes a solid, gets a number, a length along each edge you mark, the
angle of every end cut, the stock it comes out of, and a recipe.

Then the floor is loaded. Every square foot goes to the member nearest it
(that is what the decking spans to); joists hand their load to whatever
they hang on; every span is checked for bending and for sag, and on piers a
span that fails gets more piers until it passes. The largest gap the
decking has to bridge is measured too. Nothing here is a sizing table: the
numbers come from the shapes, and every figure that cannot be derived --
loads, wood strength, prices -- is in :data:`BASE_CONSTANTS` with a reason.

Coordinates: inches; the pentagon is centred on the origin with one corner
pointing +y; z is up from the ground, the floor's top flush at ``top``.
"""

from __future__ import annotations

import math
from dataclasses import dataclass, field, replace

import numpy as np

from . import recipes as rc
from . import solids as so
from .constants import C as IC

# name, value, unit, kind, why  -- shown on screen before anything is checked or priced
BASE_CONSTANTS: tuple[tuple[str, float, str, str, str], ...] = (
    ("live_psf", 40.0, "lb/ft2", "standard", "floor live load for a dwelling (IRC table R301.5)"),
    ("dead_psf", 10.0, "lb/ft2", "estimate", "decking, framing and fittings spread over the floor"),
    ("fb_psi", 875.0, "psi", "assumption", "allowable bending stress: No. 2 green softwood order of magnitude. "
                                            "Your logs are ungraded, so this is a guess, not a rating"),
    ("e_psi", 1.2e6, "psi", "estimate", "stiffness (modulus of elasticity) of green softwood"),
    ("deflect_ratio", 360.0, "L/x", "standard", "a floor may sag no more than span/360 under live load"),
    ("soil_psf", 1500.0, "lb/ft2", "standard", "presumptive bearing of ordinary soil (IRC table R401.4.1); "
                                               "each pier's gravel pad is sized from its load with it"),
    ("pad_min_in", 16.0, "in", "assumption", "smallest gravel pad under a stump pier, square"),
    ("pier_dia_in", 12.0, "in", "assumption", "stump piers cut from a 12 in log"),
    ("clearance_in", 6.0, "in", "assumption", "air under the lowest member when the floor is on piers"),
    ("dome_overhang_in", 6.0, "in", "assumption", "how far the dome's frame and skin stand past its sphere radius "
                                                  "at the base (the simulator's 8 in-trunk dome shows 3.8 in)"),
    ("node_tol_in", 0.5, "in", "assumption", "member ends closer than this are one joint"),
    ("min_piece_in", 12.0, "in", "assumption", "joists shorter than this are left out; block the gap instead"),
    ("lumber_max_in", 192.0, "in", "nominal", "the longest common lumber: 16 ft"),
    ("lumber_kerf_in", 0.125, "in", "nominal", "a mitre-saw blade"),
    ("saw_height_in", 6.0, "in", "nominal", "tallest piece a 12 in sliding mitre saw cuts standing on edge"),
    ("saw_depth_in", 12.0, "in", "nominal", "widest crosscut of a 12 in sliding mitre saw"),
    ("trim_in", 1.0, "in", "assumption", "the first cut on a log takes this much past its raw end"),
    ("deck_2x6_span_in", 24.0, "in", "standard", "2x6 deck boards laid across their supports"),
    ("deck_54_span_in", 16.0, "in", "standard", "5/4 x 6 deck boards laid across their supports"),
    ("deck_ply_span_in", 24.0, "in", "standard", "23/32 in tongue-and-groove plywood or OSB subfloor"),
    ("deck_puncheon_span_in", 48.0, "in", "assumption", "half logs flat side up, 10 in or more across"),
    ("deck_waste", 0.10, "", "assumption", "decking cut-off and waste"),
    ("usd_4x4_ft", 1.60, "$/ft", "estimate", "ground-contact treated 4x4"),
    ("usd_6x6_ft", 4.50, "$/ft", "estimate", "ground-contact treated 6x6"),
    ("usd_2x6_ft", 1.25, "$/ft", "estimate", "ground-contact treated 2x6"),
    ("usd_2x8_ft", 1.70, "$/ft", "estimate", "ground-contact treated 2x8"),
    ("usd_2x10_ft", 2.30, "$/ft", "estimate", "ground-contact treated 2x10"),
    ("usd_2x12_ft", 3.10, "$/ft", "estimate", "ground-contact treated 2x12"),
    ("usd_deck_ft", 1.10, "$/ft", "estimate", "2x6 or 5/4 x 6 deck board"),
    ("usd_log", 0.0, "$", "assumption", "a 20 ft log from your own trees; set a price if you buy them"),
    ("usd_hanger", 2.50, "$", "estimate", "one galvanised joist hanger with its nails"),
    ("usd_pier_pad", 6.0, "$", "estimate", "gravel for one pier pad"),
    ("usd_gravel_yd3", 40.0, "$/yd3", "estimate", "a cubic yard of crushed gravel, delivered"),
)
K = {name: value for name, value, _u, _k, _w in BASE_CONSTANTS}


def constants_table() -> list[str]:
    return [f"{n} = {v:g} {u} ({k}): {w}" for n, v, u, k, w in BASE_CONSTANTS]


# ----------------------------------------------------------------------
# Materials and their sections
# ----------------------------------------------------------------------

# key: (name, kind, width, depth) -- trunk sizes come from the log diameter
MATERIALS: dict[str, tuple[str, str, float, float]] = {
    "half": ("Half trunk on edge (round back out)", "half", 0, 0),
    "halfup": ("Half trunk, flat side up", "halfup", 0, 0),
    "quarter": ("Quarter trunk (sawn faces up and in)", "quarter", 0, 0),
    "round": ("Raw trunk (whole log)", "round", 0, 0),
    "4x4": ("4x4", "lumber", 3.5, 3.5),
    "6x6": ("6x6", "lumber", 5.5, 5.5),
    "2x6": ("2x6 on edge", "lumber", 1.5, 5.5),
    "2x8": ("2x8 on edge", "lumber", 1.5, 7.25),
    "2x10": ("2x10 on edge", "lumber", 1.5, 9.25),
    "2x12": ("2x12 on edge", "lumber", 1.5, 11.25),
}
TRUNK_KINDS = ("half", "halfup", "quarter", "round")
LUMBER_LENGTHS = (96.0, 120.0, 144.0, 168.0, 192.0)


def is_trunk(mat: str) -> bool:
    return MATERIALS[mat][1] in TRUNK_KINDS


def _arc(cx, cz, r, a0, a1, n=12):
    return [(cx + r * math.cos(math.radians(a)), cz + r * math.sin(math.radians(a)))
            for a in np.linspace(a0, a1, n + 1)]


@dataclass
class Section:
    poly: np.ndarray          # (x across -- + is the member's left -- , z up from its top at 0)
    tags: list[str]           # one per edge, i -> i+1
    y_lo: float
    y_hi: float
    depth: float
    area: float = 0.0
    inertia: float = 0.0      # in^4, bending under a vertical load
    modulus: float = 0.0      # in^3

    @property
    def width(self) -> float:
        return self.y_hi - self.y_lo


def section(mat: str, log_in: float, flat_left: bool = True, crown_line: bool = False) -> Section:
    """The member's cross-section. Half and quarter trunks put their flat face
    on the ``flat_left`` side. ``crown_line`` puts the round back's outermost
    line on the member's plan line (the frame: its 20 ft is measured there).
    The outline is coarse enough to cut quickly; its strength comes from a
    fine one."""
    s = _section(mat, log_in, flat_left, crown_line, 1)
    fine = _section(mat, log_in, flat_left, crown_line, 6)
    _properties(fine)
    s.area, s.inertia, s.modulus = fine.area, fine.inertia, fine.modulus
    return s


def _section(mat: str, log_in: float, flat_left: bool, crown_line: bool, fine: int) -> Section:
    _name, kind, w, h = MATERIALS[mat]
    r = log_in / 2.0
    f = 1.0 if flat_left else -1.0
    if kind == "lumber":
        pts = [(-w / 2, -h), (w / 2, -h), (w / 2, 0.0), (-w / 2, 0.0)]
        tags = ["face bottom", "face side L", "face top", "face side R"]
    elif kind == "round":
        pts = _arc(0.0, -r, r, 90, 450, 24 * fine)[:-1]
        tags = ["bark"] * len(pts)
    elif kind == "half":
        cx = f * (r if crown_line else r / 2)
        arc = _arc(cx, -r, r, 90, 270, 12 * fine) if f > 0 else _arc(cx, -r, r, 90, -90, 12 * fine)
        pts = arc
        tags = ["bark"] * (len(arc) - 1) + ["sawn flat"]
    elif kind == "halfup":
        arc = _arc(0.0, 0.0, r, 180, 360, 12 * fine)
        pts = arc
        tags = ["bark"] * (len(arc) - 1) + ["sawn top"]
    elif kind == "quarter":
        cx = f * r / 2
        arc = _arc(cx, 0.0, r, 180, 270, 6 * fine) if f > 0 else _arc(cx, 0.0, r, 0, -90, 6 * fine)
        pts = [(cx, 0.0)] + arc
        tags = ["sawn top"] + ["bark"] * (len(arc) - 1) + ["sawn side"]
    else:
        raise ValueError(mat)
    p = np.asarray(pts, float)
    return Section(p, tags, float(p[:, 0].min()), float(p[:, 0].max()), float(-p[:, 1].min()))


def _properties(s: Section) -> None:
    x, z = s.poly[:, 0], s.poly[:, 1]
    x1, z1 = np.roll(x, -1), np.roll(z, -1)
    cr = x * z1 - x1 * z
    a = 0.5 * cr.sum()
    cz = ((z + z1) * cr).sum() / (6 * a)
    izz = ((z * z + z * z1 + z1 * z1) * cr).sum() / 12.0
    i_c = abs(izz) - abs(a) * cz * cz
    s.area = abs(a)
    s.inertia = i_c
    s.modulus = i_c / max(abs(z.max() - cz), abs(z.min() - cz))


# ----------------------------------------------------------------------
# Options
# ----------------------------------------------------------------------

PATTERNS: dict[str, tuple[str, str]] = {
    "star_joists": ("Star + joists", "A five-point star corner to corner, every space between filled with "
                                     "joists. The star braces the pentagon across; the joists carry the deck."),
    "star": ("Star alone", "The star and nothing else: fewest pieces, longest deck spans."),
    "wheel": ("Wheel: 5 spokes + rings", "Five spokes from the centre to the corners; rings of joists "
                                         "between the spokes, parallel to the walls."),
    "sunburst": ("Sunburst: 10 spokes + rings", "Spokes to every corner and to the middle of every wall; "
                                                "rings between them. Shorter ring spans than the wheel."),
    "fan": ("Fan: 5 spokes + joists square to the walls", "Five spokes to the corners; joists run from "
                                                           "each wall straight in to the spokes."),
    "beams": ("Beams + joists", "Beams across the pentagon parallel to one wall; joists square to them. "
                                "The conventional deck frame."),
    "rings": ("Nested rings", "Pentagon inside pentagon, each ring's back pressed against the flat face of "
                              "the one outside it -- every corner the same 36 degree cut. Built on a gravel bed."),
}
SUPPORTS = {"piers": "On stump piers at every joint (floor clear of the ground)",
            "gravel": "On a levelled gravel bed (every member bears along its length)"}
DECKS: dict[str, tuple[str, str]] = {
    "2x6": ("2x6 deck boards", "deck_2x6_span_in"),
    "54": ("5/4 x 6 deck boards", "deck_54_span_in"),
    "ply": ("3/4 in plywood / OSB subfloor", "deck_ply_span_in"),
    "puncheon": ("Half logs flat side up (puncheon)", "deck_puncheon_span_in"),
    "fill": ("Earth, gravel or cob packed between", ""),
}


@dataclass(frozen=True)
class BaseOptions:
    pattern: str = "star_joists"
    frame_mat: str = "half"
    prim_mat: str = "half"
    sec_mat: str = "2x8"
    log_in: float = 12.0
    side_in: float = 240.0          # the frame's curved backs
    trunk_len_in: float = 240.0
    spacing_in: float = 24.0        # joists / rings, on centre
    beam_spacing_in: float = 72.0
    star_levels: int = 1
    support: str = "piers"
    deck: str = "2x6"
    dome_radius_in: float = 0.0     # the dome to be housed (sphere radius), 0 = not checked


def valid(o: BaseOptions) -> BaseOptions:
    deck = o.deck
    if deck == "fill" and o.support != "gravel":
        deck = "2x6"
    return replace(o, deck=deck, star_levels=max(1, min(3, int(o.star_levels))),
                   spacing_in=max(12.0, o.spacing_in), beam_spacing_in=max(24.0, o.beam_spacing_in),
                   log_in=max(4.0, o.log_in))


# ----------------------------------------------------------------------
# Plan geometry
# ----------------------------------------------------------------------

def _left(d) -> np.ndarray:
    return np.array([-d[1], d[0]])


def _unit(v) -> np.ndarray:
    v = np.asarray(v, float)
    n = float(np.linalg.norm(v))
    return v / n if n > 1e-12 else v * 0.0


def _cross(a, b) -> float:
    return float(a[0] * b[1] - a[1] * b[0])


def pentagon(side_in: float) -> np.ndarray:
    R = side_in / (2 * math.sin(math.radians(36)))
    return np.array([[R * math.cos(math.radians(90 + 72 * i)), R * math.sin(math.radians(90 + 72 * i))]
                     for i in range(5)])


def apothem(side_in: float) -> float:
    return side_in / (2 * math.tan(math.radians(36)))


def _seg_cross(a, b, c, d):
    """Where segment ab crosses segment cd (strictly inside both), or None."""
    r, s = b - a, d - c
    den = _cross(r, s)
    if abs(den) < 1e-12:
        return None
    t = _cross(c - a, s) / den
    u = _cross(c - a, r) / den
    if 1e-6 < t < 1 - 1e-6 and 1e-6 < u < 1 - 1e-6:
        return a + r * t
    return None


def split_all(segs: list[tuple[np.ndarray, np.ndarray]]) -> list[tuple[np.ndarray, np.ndarray]]:
    """Cut every segment where another crosses it."""
    out = []
    for i, (a, b) in enumerate(segs):
        cuts = [0.0, 1.0]
        d = b - a
        L2 = float(d @ d)
        for j, (c, e) in enumerate(segs):
            if i == j:
                continue
            p = _seg_cross(a, b, c, e)
            if p is not None:
                cuts.append(float((p - a) @ d) / L2)
            for q in (c, e):     # another segment ending on this one
                t = float((q - a) @ d) / L2
                if 1e-6 < t < 1 - 1e-6 and np.linalg.norm(a + d * t - q) < 1e-6:
                    cuts.append(t)
        cuts = sorted(set(round(c, 9) for c in cuts))
        for t0, t1 in zip(cuts, cuts[1:]):
            if t1 - t0 > 1e-6:
                out.append((a + d * t0, a + d * t1))
    return out


def _clip_line(poly: np.ndarray, p0: np.ndarray, d: np.ndarray):
    """The chord of a convex CCW polygon along the line p0 + t d."""
    lo, hi = -1e9, 1e9
    for i in range(len(poly)):
        a, b = poly[i], poly[(i + 1) % len(poly)]
        nn = _left(b - a)
        num = float(nn @ (p0 - a))
        den = float(nn @ d)
        if abs(den) < 1e-12:
            if num < -1e-9:
                return None
            continue
        t = -num / den
        if den > 0:
            lo = max(lo, t)
        else:
            hi = min(hi, t)
    if hi - lo < 1e-6:
        return None
    return p0 + d * lo, p0 + d * hi


def faces(segs: list[tuple[np.ndarray, np.ndarray]], tol: float = 0.05) -> list[np.ndarray]:
    """The bounded cells of a set of segments (a planar graph), each CCW."""
    pts: list[np.ndarray] = []

    def vid(p):
        for i, q in enumerate(pts):
            if np.linalg.norm(q - p) < tol:
                return i
        pts.append(np.asarray(p, float))
        return len(pts) - 1
    edges = set()
    for a, b in split_all(segs):
        i, j = vid(a), vid(b)
        if i != j:
            edges.add((i, j))
            edges.add((j, i))
    nbr: dict[int, list[int]] = {}
    for i, j in edges:
        nbr.setdefault(i, []).append(j)
    for i in nbr:
        nbr[i].sort(key=lambda j: math.atan2(*(pts[j] - pts[i])[::-1]))
    seen, out = set(), []
    for e in edges:
        if e in seen:
            continue
        cyc, cur = [], e
        while cur not in seen:
            seen.add(cur)
            u, v = cur
            cyc.append(u)
            ring = nbr[v]
            k = ring.index(u)
            cur = (v, ring[k - 1])          # the next edge clockwise from the way back
            if len(cyc) > 400:
                break
        poly = np.array([pts[i] for i in cyc])
        x, y = poly[:, 0], poly[:, 1]
        signed = 0.5 * float(np.dot(x, np.roll(y, -1)) - np.dot(y, np.roll(x, -1)))
        out.append((signed, poly))
    if not out:
        return []
    biggest = max(out, key=lambda t: abs(t[0]))
    sign = 1.0 if biggest[0] < 0 else -1.0
    return [p for s, p in out if s * sign > 1e-6 and p is not biggest[1]]


# ----------------------------------------------------------------------
# Members
# ----------------------------------------------------------------------

@dataclass(eq=False)
class Member:
    role: str                # frame / primary / joist
    rank: int                # 0 frame, 1 primary, 2 joist
    mat: str
    a: np.ndarray
    b: np.ndarray
    name: str = ""
    label: str = ""          # a name the pattern gives it (rings: "Ring 3, side 2")
    flat_left: bool = True
    crown_line: bool = False
    sect: Section | None = None
    planes: list = field(default_factory=lambda: [[], []])     # end a, end b
    meets: list = field(default_factory=lambda: [[], []])      # (other member, how) at each end
    receivers: list = field(default_factory=lambda: [[], []])  # members this end hangs on
    node: list = field(default_factory=lambda: [None, None])
    solid: so.Solid | None = None
    number: int = 0
    marks: list = field(default_factory=list)                  # (name, s_lo, s_hi)
    s_lo: float = 0.0
    s_hi: float = 0.0
    stock: str = ""
    stock_order: str = ""
    load_lb: float = 0.0
    live_lb: float = 0.0
    spans: list = field(default_factory=list)                  # (span in, ok, ratio)
    extra_piers: int = 0

    @property
    def along(self) -> np.ndarray:
        return _unit(self.b - self.a)

    @property
    def left(self) -> np.ndarray:
        return _left(self.along)

    @property
    def length(self) -> float:
        return float(np.linalg.norm(self.b - self.a))

    def end_point(self, e: int) -> np.ndarray:
        return self.a if e == 0 else self.b

    def u(self, e: int) -> np.ndarray:
        """Pointing from end ``e`` into the member."""
        return self.along if e == 0 else -self.along


@dataclass
class Node:
    p: np.ndarray
    ends: list                      # (member, end)
    through: list                   # members passing through
    pier: bool = False
    pier_xy: np.ndarray | None = None
    pier_top: float = 0.0
    load_lb: float = 0.0
    number: int = 0


@dataclass
class Pier:
    xy: np.ndarray
    top: float
    load_lb: float
    where: str
    number: int = 0
    solid: so.Solid | None = None
    stock: str = ""


@dataclass
class BasePiece:
    group: str
    material: str
    solid: so.Solid
    color: tuple
    kind: str
    ref: object
    pose: str = ""


@dataclass
class Base:
    opts: BaseOptions
    crown: np.ndarray
    members: list[Member]
    nodes: list[Node]
    piers: list[Pier]
    top: float
    cells: list[np.ndarray]
    checks: dict
    stock: dict
    pieces: list[BasePiece] = field(default_factory=list)
    recipes: list = field(default_factory=list)
    prep: object = None
    title: str = ""


def _pattern_lines(o: BaseOptions, crown: np.ndarray, frame_inner: float) -> tuple[list, str | None, object]:
    """The primary members' centre lines, and how to fill the cells between."""
    c = np.zeros(2)
    mids = [(crown[i] + crown[(i + 1) % 5]) / 2 for i in range(5)]
    lines: list = []
    fill, fixed = None, None
    if o.pattern in ("star", "star_joists"):
        poly = crown
        for _lvl in range(o.star_levels):
            diag = [(poly[i], poly[(i + 2) % 5]) for i in range(5)]
            pieces = split_all(diag)
            lines += pieces
            inner = []
            for i in range(5):
                p = _seg_cross(*diag[i], *diag[(i + 1) % 5])
                if p is not None:
                    inner.append(p)
            if len(inner) < 5:
                break
            inner = np.array(sorted(inner, key=lambda p: math.atan2(p[1], p[0])))
            poly = inner
        fill = "min_extent" if o.pattern == "star_joists" else None
    elif o.pattern == "wheel":
        lines = [(c, crown[i]) for i in range(5)]
        fill = "parallel_frame"
    elif o.pattern == "sunburst":
        lines = [(c, crown[i]) for i in range(5)] + [(c, mids[i]) for i in range(5)]
        fill = "parallel_frame"
    elif o.pattern == "fan":
        lines = [(c, crown[i]) for i in range(5)]
        fill = "perp_frame"
    elif o.pattern == "beams":
        a0 = apothem(o.side_in)
        top_y = float(crown[:, 1].max())
        y = -a0 + o.beam_spacing_in
        while y < top_y - o.beam_spacing_in * 0.5:
            ch = _clip_line(crown, np.array([0.0, y]), np.array([1.0, 0.0]))
            if ch is not None:
                lines.append(ch)
            y += o.beam_spacing_in
        fill, fixed = "fixed", np.array([0.0, 1.0])
    return lines, fill, fixed


def _fill_cell(cell: np.ndarray, rule: str, spacing: float, frame_lines, fixed=None) -> list:
    poly = cell
    edges = [(poly[i], poly[(i + 1) % len(poly)]) for i in range(len(poly))]

    def on_frame(a, b):
        for p, q in frame_lines:
            d = _unit(q - p)
            n = _left(d)
            if abs(float(n @ (a - p))) < 0.5 and abs(float(n @ (b - p))) < 0.5:
                return True
        return False
    frame_edges = [(a, b) for a, b in edges if on_frame(a, b)]
    if rule == "fixed" and fixed is not None:
        d = _unit(fixed)
    elif rule in ("parallel_frame", "perp_frame") and frame_edges:
        a, b = max(frame_edges, key=lambda e: np.linalg.norm(e[1] - e[0]))
        d = _unit(b - a)
        if rule == "perp_frame":
            d = _left(d)
    else:
        best = None
        for a, b in edges:
            dd = _unit(b - a)
            ext = float((poly @ dd).max() - (poly @ dd).min())
            if best is None or ext < best[0]:
                best = (ext, dd)
        d = best[1]
    n = _left(d)
    m = poly @ n
    m0, m1 = float(m.min()), float(m.max())
    count = int(math.ceil((m1 - m0) / spacing)) - 1
    out = []
    if count <= 0:
        return out
    start = m0 + ((m1 - m0) - spacing * (count - 1)) / 2
    for k in range(count):
        off = start + spacing * k
        ch = _clip_line(poly, n * off, d)
        if ch is not None and np.linalg.norm(ch[1] - ch[0]) >= K["min_piece_in"]:
            out.append(ch)
    return out


def _max_len(o: BaseOptions, mat: str) -> float:
    return o.trunk_len_in if is_trunk(mat) else K["lumber_max_in"]


def _split_long(m: Member, o: BaseOptions) -> list[Member]:
    limit = _max_len(o, m.mat)
    if m.role == "frame" or m.length <= limit - 8.0:
        return [m]
    n = int(math.ceil(m.length / (limit - 8.0)))
    out = []
    for k in range(n):
        a = m.a + (m.b - m.a) * (k / n)
        b = m.a + (m.b - m.a) * ((k + 1) / n)
        out.append(Member(m.role, m.rank, m.mat, a, b, flat_left=m.flat_left, crown_line=m.crown_line,
                          label=f"{m.label}, part {k + 1} of {n}" if m.label else ""))
    return out


def layout_members(o: BaseOptions) -> tuple[np.ndarray, list[Member], list[np.ndarray]]:
    crown = pentagon(o.side_in)
    members: list[Member] = []
    for i in range(5):
        members.append(Member("frame", 0, o.frame_mat, crown[i], crown[(i + 1) % 5], crown_line=True,
                              flat_left=True))
    frame_lines = [(m.a, m.b) for m in members]
    centre = np.zeros(2)
    cells: list[np.ndarray] = []
    if o.pattern == "rings":
        fs = section(o.frame_mat, o.log_in, True, True)
        ps = section(o.prim_mat, o.log_in, True, False)
        A = apothem(o.side_in) - fs.y_hi + ps.y_lo          # touching the frame's flat face
        k = 0
        while True:
            Rv = A / math.cos(math.radians(36))
            verts = np.array([[Rv * math.cos(math.radians(90 + 72 * i)), Rv * math.sin(math.radians(90 + 72 * i))]
                              for i in range(5)])
            inner_side = 2 * (A - ps.y_hi) * math.tan(math.radians(36))
            if inner_side < K["min_piece_in"] or A - ps.y_hi <= 0:
                break
            for i in range(5):
                members.append(Member("primary", 1, o.prim_mat, verts[i], verts[(i + 1) % 5], flat_left=True,
                                      label=f"Ring {k + 1}, side {i + 1}"))
            A = A - ps.y_hi + ps.y_lo
            k += 1
        return crown, members, cells
    frame_inner = 0.0
    lines, fill, fixed = _pattern_lines(o, crown, frame_inner)
    lines = split_all(lines)
    for a, b in lines:
        mid = (a + b) / 2
        d = _unit(b - a)
        flat_left = float(_left(d) @ (centre - mid)) >= 0     # flat face toward the middle
        members.append(Member("primary", 1, o.prim_mat, np.asarray(a, float), np.asarray(b, float),
                              flat_left=flat_left))
    if fill:
        cells = faces(frame_lines + [(m.a, m.b) for m in members if m.rank == 1])
        for cell in cells:
            for a, b in _fill_cell(cell, fill, o.spacing_in, frame_lines, fixed):
                members.append(Member("joist", 2, o.sec_mat, a, b, flat_left=True))
    return crown, members, cells


# ----------------------------------------------------------------------
# Joints
# ----------------------------------------------------------------------

def _face_plane(k: Member, toward_u: np.ndarray) -> so.Plane:
    """The face of member ``k`` on the side that ``toward_u`` points to."""
    s = _cross(k.along, toward_u)
    left = k.left
    if s >= 0:
        n2, d = left, float(left @ k.a) + k.sect.y_hi
    else:
        n2, d = -left, float(-left @ k.a) - k.sect.y_lo
    return so.Plane(np.array([n2[0], n2[1], 0.0]), d, "end cut")


def _junction_plane(m: Member, em: int, k: Member, ek: int, N: np.ndarray) -> so.Plane:
    um, uk = m.u(em), k.u(ek)
    side_m = _cross(m.along, uk) > 0
    side_k = _cross(k.along, um) > 0
    om = m.left * (m.sect.y_hi if side_m else m.sect.y_lo)
    ok = k.left * (k.sect.y_hi if side_k else k.sect.y_lo)
    den = _cross(um, uk)
    n2 = None
    if abs(den) > 1e-9:
        pm, pk = N + om, N + ok
        t = _cross(pk - pm, uk) / den
        P = pm + um * t
        v = P - N
        if np.linalg.norm(v) > 1e-6:
            n2 = _unit(_left(v))
    if n2 is None:
        n2 = _unit(um - uk)
    if float(n2 @ um) < 0:
        n2 = -n2
    return so.Plane(np.array([n2[0], n2[1], 0.0]), float(n2 @ N), "end cut")


def _angle(v) -> float:
    return math.atan2(v[1], v[0]) % (2 * math.pi)


def resolve(members: list[Member], o: BaseOptions) -> list[Node]:
    tol = K["node_tol_in"]
    ends = [(m, e) for m in members for e in (0, 1)]
    nodes: list[Node] = []
    for m, e in ends:
        p = m.end_point(e)
        for nd in nodes:
            if np.linalg.norm(nd.p - p) < tol:
                nd.ends.append((m, e))
                break
        else:
            nodes.append(Node(np.asarray(p, float), [(m, e)], []))
    for nd in nodes:
        enders = {id(m) for m, _e in nd.ends}
        for m in members:
            if id(m) in enders:
                continue
            d = m.b - m.a
            t = float((nd.p - m.a) @ d) / float(d @ d)
            if 0 < t < 1 and np.linalg.norm(m.a + d * t - nd.p) < tol:
                nd.through.append(m)
        for m, e in nd.ends:
            m.node[e] = nd
    for nd in nodes:
        for m, e in nd.ends:
            rays = []
            for k, ek in nd.ends:
                if k.rank <= m.rank:
                    rays.append((_angle(k.u(ek)), k, ek, "end"))
            for k in nd.through:
                if k.rank <= m.rank:
                    rays.append((_angle(k.along), k, None, "thru"))
                    rays.append((_angle(-k.along), k, None, "thru"))
            rays.sort(key=lambda r: r[0])
            me = next(i for i, r in enumerate(rays) if r[1] is m and r[3] == "end")
            planes, meets, recv = [], [], []
            n = len(rays)
            if n > 1:
                for step in (1, -1):
                    r = rays[(me + step) % n]
                    gap = (r[0] - rays[me][0]) * step % (2 * math.pi)
                    if gap >= math.radians(179.5) or gap < 1e-9:
                        continue
                    k = r[1]
                    if r[3] == "thru" or k.rank < m.rank:
                        pl = _face_plane(k, m.u(e))
                        how = "face"
                        if all(k is not q for q in recv):
                            recv.append(k)
                    else:
                        pl = _junction_plane(m, e, k, r[2], nd.p)
                        how = "mitre"
                    if not any(abs(float(pl.n @ q.n) - 1) < 1e-6 and abs(pl.d - q.d) < 1e-6 for q in planes):
                        planes.append(pl)
                        meets.append((k, how))
            if not planes:
                u = m.u(e)
                planes.append(so.Plane(np.array([u[0], u[1], 0.0]), float(u @ nd.p), "end cut"))
                meets.append((None, "square"))
            m.planes[e] = planes
            m.meets[e] = meets
            m.receivers[e] = recv
    return nodes


def build_solid(m: Member, top: float) -> so.Solid | None:
    s = so.prism(m.sect.poly, m.sect.tags, m.a, m.along, m.left, top)
    for pl in m.planes[0] + m.planes[1]:
        s = so.clip(s, pl)
        if not s.faces:
            return None
    return s


def _mark_lines(m: Member) -> list[tuple[str, float, float]]:
    """Where to measure: the top's left and right edges (or the top line of a
    round), and the round back's widest line, each as (x, z) in the section."""
    p = m.sect.poly
    topz = p[:, 1].max()
    top = p[p[:, 1] > topz - 1e-6]
    out = []
    left, right = top[:, 0].max(), top[:, 0].min()
    if left - right < 1e-6:
        out.append(("along the top", left, topz))
    else:
        out.append(("along the top, left edge", left, topz))
        out.append(("along the top, right edge", right, topz))
    i_max, i_min = int(p[:, 0].argmax()), int(p[:, 0].argmin())
    if p[i_max, 0] > left + 0.3:
        out.append(("along the widest point of the left side", p[i_max, 0], p[i_max, 1]))
    if p[i_min, 0] < right - 0.3:
        out.append(("along the widest point of the right side", p[i_min, 0], p[i_min, 1]))
    return out


def _s_range(m: Member, x: float, z: float, top: float, planes) -> tuple[float, float]:
    P0 = np.array([m.a[0], m.a[1], top]) + np.array([m.left[0], m.left[1], 0.0]) * x + np.array([0, 0, z])
    al = np.array([m.along[0], m.along[1], 0.0])
    lo, hi = -1e9, 1e9
    for pl in planes:
        na = float(pl.n @ al)
        val = float(pl.n @ P0) - pl.d
        if abs(na) < 1e-12:
            continue
        t = -val / na
        if na > 0:
            lo = max(lo, t)
        else:
            hi = min(hi, t)
    return lo, hi


# ----------------------------------------------------------------------
# Loads, spans and piers
# ----------------------------------------------------------------------

def _grid(crown: np.ndarray, step: float = 4.0) -> np.ndarray:
    lo, hi = crown.min(axis=0), crown.max(axis=0)
    xs = np.arange(lo[0] + step / 2, hi[0], step)
    ys = np.arange(lo[1] + step / 2, hi[1], step)
    X, Y = np.meshgrid(xs, ys)
    P = np.c_[X.ravel(), Y.ravel()]
    inside = np.ones(len(P), bool)
    for i in range(5):
        a, b = crown[i], crown[(i + 1) % 5]
        inside &= (P - a) @ _left(b - a) >= 0
    return P[inside]


def _seg_dist(P: np.ndarray, a: np.ndarray, b: np.ndarray) -> tuple[np.ndarray, np.ndarray]:
    d = b - a
    L2 = float(d @ d)
    t = np.clip((P - a) @ d / L2, 0.0, 1.0)
    Q = a + np.outer(t, d)
    return np.linalg.norm(P - Q, axis=1), t


def loads(base_members: list[Member], nodes: list[Node], crown: np.ndarray, o: BaseOptions) -> dict:
    step = 4.0
    P = _grid(crown, step)
    cell = step * step / 144.0                       # ft2 per grid point
    q, q_live = K["live_psf"] + K["dead_psf"], K["live_psf"]
    D = np.stack([_seg_dist(P, m.a, m.b)[0] for m in base_members])
    near = D.argmin(axis=0)
    face = D.min(axis=0) - np.array([base_members[i].sect.width / 2 for i in near])
    clear = 2.0 * float(max(face.max(), 0.0))
    for i, m in enumerate(base_members):
        n = int((near == i).sum())
        m.load_lb = n * cell * q
        m.live_lb = n * cell * q_live
    total = len(P) * cell * q
    out = {"total_lb": total, "area_ft2": len(P) * cell, "deck_clear_in": clear}
    if o.support == "gravel":
        for m in base_members:
            m.spans = []
        out["piers"] = []
        return out
    # Piers: every joint where a frame or primary member ends, and every splice.
    for nd in nodes:
        low = [m for m, _e in nd.ends if m.rank <= 1]
        splice = len(nd.ends) == 2 and abs(float(nd.ends[0][0].u(nd.ends[0][1]) @
                                                 nd.ends[1][0].u(nd.ends[1][1])) + 1) < 1e-6
        hung = all(m.receivers[e] for m, e in nd.ends)
        nd.pier = bool(low) or splice or not hung
    piers: list[Pier] = []
    pier_of: dict[int, Pier] = {}
    top = o_top(base_members, o)
    for nd in nodes:
        if not nd.pier:
            continue
        offs = []
        deep = 0.0
        for m, e in nd.ends:
            offs.append(nd.p + m.u(e) * (m.sect.width / 2) + m.left * ((m.sect.y_hi + m.sect.y_lo) / 2) - nd.p)
            deep = max(deep, m.sect.depth)
        for m in nd.through:
            offs.append(m.left * ((m.sect.y_hi + m.sect.y_lo) / 2))
            deep = max(deep, m.sect.depth)
        xy = nd.p + (np.mean(offs, axis=0) if offs else 0.0)
        pr = Pier(xy, top - deep, 0.0, "joint")
        piers.append(pr)
        pier_of[id(nd)] = pr
    fb, E, ratio = K["fb_psi"], K["e_psi"], K["deflect_ratio"]
    for m in sorted(base_members, key=lambda m: -m.rank):
        L = m.length
        w = m.load_lb / L if L > 0 else 0.0
        wl = m.live_lb / L if L > 0 else 0.0
        sup = []                                       # (s, pier or member)
        for e, s in ((0, 0.0), (1, L)):
            nd = m.node[e]
            if nd is not None and nd.pier:
                sup.append((s, pier_of[id(nd)]))
            elif m.receivers[e]:
                sup.append((s, m.receivers[e][0]))
            else:
                sup.append((s, None))
        for nd in nodes:
            if nd.pier and any(t is m for t in nd.through):
                sup.append((float((nd.p - m.a) @ m.along), pier_of[id(nd)]))
        sup.sort(key=lambda t: t[0])
        S, I = m.sect.modulus, m.sect.inertia
        s_allow = min(math.sqrt(8 * fb * S / w) if w > 0 else 1e9,
                      (384 * E * I / (5 * ratio * wl)) ** (1 / 3) if wl > 0 else 1e9)
        spans, final = [], [sup[0]]
        for (s0, t0), (s1, t1) in zip(sup, sup[1:]):
            sp = s1 - s0
            n = max(1, int(math.ceil(sp / s_allow - 1e-9)))
            if n > 1:
                for k in range(1, n):
                    s = s0 + sp * k / n
                    xy = m.a + m.along * s + m.left * ((m.sect.y_hi + m.sect.y_lo) / 2)
                    pr = Pier(xy, top - m.sect.depth, 0.0, f"under {m.name or m.role} (span)")
                    piers.append(pr)
                    final.append((s, pr))
                m.extra_piers += n - 1
            final.append((s1, t1))
            spans += [(sp / n, sp / n / s_allow)] * n
        m.spans = [(sp, r <= 1.0 + 1e-9, r) for sp, r in spans]
        for (s0, t0), (s1, t1) in zip(final, final[1:]):
            half = w * (s1 - s0) / 2
            for t in (t0, t1):
                if isinstance(t, Pier):
                    t.load_lb += half
                elif isinstance(t, Member):
                    t.load_lb += half
                    t.live_lb += half * (q_live / q)
                else:
                    pass
    out["piers"] = piers
    return out


def pad_in(load_lb: float) -> float:
    """The square gravel pad a pier needs, to the next 2 in."""
    need = math.sqrt(max(load_lb, 0.0) / K["soil_psf"]) * 12.0
    return max(K["pad_min_in"], 2.0 * math.ceil(need / 2.0 - 1e-9))


def o_top(members: list[Member], o: BaseOptions) -> float:
    deep = max(m.sect.depth for m in members)
    return deep + (K["clearance_in"] if o.support == "piers" else 0.0)


# ----------------------------------------------------------------------
# Stock
# ----------------------------------------------------------------------

def _ffd(items: list[tuple[float, object]], cap: float, kerf: float) -> list[list[tuple[float, object]]]:
    bins: list[list] = []
    room: list[float] = []
    for L, ref in sorted(items, key=lambda t: -t[0]):
        for i in range(len(bins)):
            if room[i] >= L + (kerf if bins[i] else 0.0) - 1e-9:
                room[i] -= L + (kerf if bins[i] else 0.0)
                bins[i].append((L, ref))
                break
        else:
            bins.append([(L, ref)])
            room.append(cap - L)
    return bins


def stock_plan(b_members: list[Member], piers: list[Pier], o: BaseOptions, deck_area_ft2: float,
               open_area_ft2: float, top: float) -> dict:
    out = {"logs": 0, "lines": [], "usd": 0.0, "lumber": {}, "frame": [], "hangers": 0}
    kerf_c = IC["chainsaw_kerf_in"]
    trunk = o.trunk_len_in
    by_kind: dict[str, list] = {}
    for m in b_members:
        need = m.s_hi - m.s_lo
        if m.role == "frame":
            out["frame"].append(m)
            m.stock = f"your half trunk {len(out['frame'])} (in hand)"
            m.stock_order = "the whole trunk"
            continue
        kind = MATERIALS[m.mat][1]
        allow = K["trim_in"] if is_trunk(m.mat) else 0.5
        by_kind.setdefault(m.mat if not is_trunk(m.mat) else kind, []).append((need + allow, m))
    log_sticks = {"round": 0, "half": 0, "halfup": 0, "quarter": 0}
    for key, items in by_kind.items():
        if key in TRUNK_KINDS:
            bins = _ffd(items, trunk, kerf_c)
            per = {"round": 1, "half": 2, "halfup": 2, "quarter": 4}[key]
            log_sticks[key] = len(bins)
            label = {"round": "Log", "half": "Half trunk", "halfup": "Half trunk", "quarter": "Quarter trunk"}[key]
            for i, bn in enumerate(bins):
                sid = f"{label} {key[0].upper()}{i + 1} ({trunk / 12:g} ft"
                sid += ", whole)" if per == 1 else f", one of {per} from a split log)"
                for j, (L, m) in enumerate(bn):
                    m.stock = sid
                    m.stock_order = f"cut {j + 1} of {len(bn)} on it"
            logs = int(math.ceil(len(bins) / per))
            out["lines"].append((f"{MATERIALS[items[0][1].mat][0]}: {len(bins)} sticks of {trunk / 12:g} ft",
                                 f"{logs} log(s) of {o.log_in:g} in x {trunk / 12:g} ft", logs * K["usd_log"]))
            out["logs"] += logs
        else:
            bins = _ffd(items, K["lumber_max_in"], K["lumber_kerf_in"])
            counts: dict[float, int] = {}
            for i, bn in enumerate(bins):
                used = sum(L for L, _m in bn) + K["lumber_kerf_in"] * (len(bn) - 1)
                Ls = next(x for x in LUMBER_LENGTHS if x >= used - 1e-9)
                counts[Ls] = counts.get(Ls, 0) + 1
                for j, (L, m) in enumerate(bn):
                    m.stock = f"{key} #{i + 1} ({Ls / 12:g} ft)"
                    m.stock_order = f"cut {j + 1} of {len(bn)} on it"
            ft = sum(Ls / 12 * n for Ls, n in counts.items())
            usd = ft * K[f"usd_{key}_ft"]
            desc = ", ".join(f"{n} x {Ls / 12:g} ft" for Ls, n in sorted(counts.items(), reverse=True))
            out["lines"].append((f"{key}: {desc}", f"{ft:.0f} ft", usd))
            out["lumber"][key] = ft
            out["usd"] += usd
    if piers:
        bins = _ffd([(p.top + K["trim_in"], p) for p in piers], trunk, kerf_c)
        for i, bn in enumerate(bins):
            for j, (L, p) in enumerate(bn):
                p.stock = f"pier log {i + 1} ({K['pier_dia_in']:g} in x {trunk / 12:g} ft), round {j + 1} of {len(bn)}"
        out["lines"].append((f"Stump piers: {len(piers)} rounds", f"{len(bins)} log(s) of {K['pier_dia_in']:g} in "
                             f"x {trunk / 12:g} ft", len(bins) * K["usd_log"] + len(piers) * K["usd_pier_pad"]))
        out["usd"] += len(piers) * K["usd_pier_pad"]
        out["logs"] += len(bins)
    hangers = sum(1 for m in b_members for e in (0, 1)
                  if m.rank == 2 and m.receivers[e] and not (m.node[e] is not None and m.node[e].pier))
    if hangers and o.support == "piers":
        out["hangers"] = hangers
        out["lines"].append(("Joist hangers (or notch and spike into logs)", f"{hangers}", hangers * K["usd_hanger"]))
        out["usd"] += hangers * K["usd_hanger"]
    # Decking.
    deck = o.deck
    if deck in ("2x6", "54"):
        lf = deck_area_ft2 * 12 / (5.5 + 0.25) * (1 + K["deck_waste"])
        n16 = int(math.ceil(lf / 16))
        out["lines"].append((f"{DECKS[deck][0]}: {deck_area_ft2:.0f} ft2", f"{n16} x 16 ft ({lf:.0f} ft)",
                             lf * K["usd_deck_ft"]))
        out["usd"] += lf * K["usd_deck_ft"]
    elif deck == "ply":
        sheets = int(math.ceil(deck_area_ft2 / 32 * (1 + K["deck_waste"]) + 0.999))
        out["lines"].append((f"{DECKS[deck][0]}: {deck_area_ft2:.0f} ft2", f"{sheets} sheets 4x8",
                             sheets * IC["ply_usd"]))
        out["usd"] += sheets * IC["ply_usd"]
    elif deck == "puncheon":
        lf = deck_area_ft2 * 12 / o.log_in * (1 + K["deck_waste"])
        halves = int(math.ceil(lf * 12 / o.trunk_len_in))
        logs = int(math.ceil(halves / 2))
        out["lines"].append((f"{DECKS[deck][0]}: {deck_area_ft2:.0f} ft2", f"{halves} halves = {logs} log(s)",
                             logs * K["usd_log"]))
        out["logs"] += logs
    elif deck == "fill":
        yd3 = open_area_ft2 * (top / 12) / 27
        out["lines"].append(("Gravel / earth packed between the members", f"{yd3:.1f} yd3",
                             yd3 * K["usd_gravel_yd3"]))
        out["usd"] += yd3 * K["usd_gravel_yd3"]
    if o.support == "gravel":
        yd3 = deck_area_ft2 * (4 / 12) / 27
        out["lines"].append(("Levelled gravel bed, 4 in deep", f"{yd3:.1f} yd3", yd3 * K["usd_gravel_yd3"]))
        out["usd"] += yd3 * K["usd_gravel_yd3"]
    out["logs_total"] = out["logs"]
    return out


# ----------------------------------------------------------------------
# The build
# ----------------------------------------------------------------------

def ftin(x: float) -> str:
    """Inches as feet and inches to the nearest 1/16."""
    sixteenths = int(round(x * 16))
    ft, rem = divmod(sixteenths, 12 * 16)
    inch, frac = divmod(rem, 16)
    s = f"{ft}' " if ft else ""
    s += f"{inch}"
    if frac:
        g = math.gcd(frac, 16)
        s += f" {frac // g}/{16 // g}"
    return s + '"'


ROLE_NAMES = {"frame": "Frame side", "primary": "Primary", "joist": "Joist"}


def _primary_word(o: BaseOptions) -> str:
    return {"star": "Star", "star_joists": "Star", "wheel": "Spoke", "sunburst": "Spoke", "fan": "Spoke",
            "beams": "Beam", "rings": "Ring"}[o.pattern]


def build(o: BaseOptions, with_recipes: bool = True) -> Base:
    o = valid(o)
    crown, members, cells = layout_members(o)
    split: list[Member] = []
    for m in members:
        split.extend(_split_long(m, o))
    members = split
    for m in members:
        m.sect = section(m.mat, o.log_in, m.flat_left, m.crown_line)
    nodes = resolve(members, o)
    top = o_top(members, o)
    kept = []
    for m in members:
        m.solid = build_solid(m, top)
        if m.solid is None:
            continue
        planes = m.planes[0] + m.planes[1]
        m.marks = []
        for name, x, z in _mark_lines(m):
            lo, hi = _s_range(m, x, z, top, planes)
            m.marks.append((name, lo, hi))
        sv = (m.solid.vertices()[:, :2] - m.a) @ m.along
        m.s_lo, m.s_hi = float(sv.min()), float(sv.max())
        kept.append(m)
    members = kept
    word = _primary_word(o)
    counters: dict[str, int] = {}
    for i, m in enumerate(members):
        m.number = i + 1
        base = {"frame": "Frame side", "primary": word, "joist": "Joist"}[m.role]
        counters[base] = counters.get(base, 0) + 1
        m.name = m.label or f"{base} {counters[base]}"
    ld = loads(members, nodes, crown, o)
    piers = ld.get("piers", [])
    for j, p in enumerate(piers):
        p.number = len(members) + j + 1
        circ = np.array([[p.xy[0] + K["pier_dia_in"] / 2 * math.cos(t), p.xy[1] + K["pier_dia_in"] / 2 * math.sin(t)]
                         for t in np.linspace(0, 2 * math.pi, 20, endpoint=False)])
        p.solid = so.slab(circ, 0.0, max(p.top, 0.5), "bark")
    plan_area = sum(m.sect.width * m.length for m in members) / 144.0
    st = stock_plan(members, piers, o, ld["area_ft2"], max(0.0, ld["area_ft2"] - plan_area), top)
    checks = _checks(members, piers, ld, o, crown)
    b = Base(o, crown, members, nodes, piers, top, cells, checks, st)
    b.title = f"Floor base: {PATTERNS[o.pattern][0]}"
    b.pieces = _pieces(b)
    if with_recipes:
        b.recipes = [member_recipe(m, b) for m in members] + [pier_recipe(p, b) for p in piers]
        b.prep = summary_card(b)
    return b


def _checks(members, piers, ld, o, crown) -> dict:
    out = {"area_ft2": ld["area_ft2"], "total_lb": ld["total_lb"], "deck_clear_in": ld["deck_clear_in"]}
    a0 = apothem(o.side_in)
    fs = section(o.frame_mat, o.log_in, True, True)
    out["inner_r_in"] = a0 - fs.y_hi
    out["corner_r_in"] = o.side_in / (2 * math.sin(math.radians(36)))
    need = o.dome_radius_in + K["dome_overhang_in"] if o.dome_radius_in > 0 else 0.0
    out["dome_need_in"] = need
    out["dome_fits"] = need <= out["inner_r_in"] if need else None
    deck_key = DECKS[o.deck][1]
    out["deck_allow_in"] = K[deck_key] if deck_key else None
    out["deck_ok"] = (o.deck == "fill") or (ld["deck_clear_in"] <= K[deck_key] + 1e-6)
    if o.support == "piers":
        spans = [(m, sp, r) for m in members for sp, _ok, r in m.spans]
        out["worst_ratio"] = max((r for _m, _s, r in spans), default=0.0)
        out["extra_piers"] = sum(m.extra_piers for m in members)
        out["piers"] = len(piers)
        out["pier_max_lb"] = max((p.load_lb for p in piers), default=0.0)
        out["pad_max_in"] = pad_in(out["pier_max_lb"])
        out["big_pads"] = sum(1 for p in piers if pad_in(p.load_lb) > K["pad_min_in"])
        out["pier_sum_lb"] = sum(p.load_lb for p in piers)
    return out


COLORS = {"half": (0.55, 0.38, 0.24, 1), "halfup": (0.6, 0.43, 0.27, 1), "quarter": (0.66, 0.48, 0.3, 1),
          "round": (0.45, 0.31, 0.2, 1), "lumber": (0.86, 0.72, 0.5, 1), "pier": (0.5, 0.42, 0.34, 1),
          "frame": (0.42, 0.27, 0.16, 1)}


def _pieces(b: Base) -> list[BasePiece]:
    out = []
    for m in b.members:
        kind = MATERIALS[m.mat][1]
        col = COLORS["frame"] if m.role == "frame" else COLORS.get(kind, COLORS["lumber"])
        if m.role == "joist" and kind != "lumber":
            col = tuple(min(1, c * 1.15) for c in col[:3]) + (1,)
        out.append(BasePiece(m.name, m.mat, m.solid, col, m.role, m))
    for p in b.piers:
        out.append(BasePiece(f"Pier {p.number - len(b.members)}", "pier", p.solid, COLORS["pier"], "pier", p))
    return out


# ----------------------------------------------------------------------
# Words
# ----------------------------------------------------------------------

def _end_words(m: Member, e: int) -> str:
    pls = m.planes[e]
    angs = [math.degrees(math.acos(min(1.0, abs(float(pl.n[:2] @ m.along))))) for pl in pls]
    if len(pls) == 1:
        return "square" if angs[0] < 0.05 else f"{angs[0]:.1f}° off square"
    return "a point: " + " and ".join(f"{a:.1f}°" for a in angs) + " off square"


def _meet_words(m: Member, e: int) -> str:
    bits = []
    for k, how in m.meets[e]:
        if k is None:
            bits.append("nothing (square end)")
        elif how == "face":
            face = "round back" if (MATERIALS[k.mat][1] in ("half", "round", "quarter")
                                    and _face_is_round(k, m.u(e))) else "face"
            bits.append(f"the {face} of #{k.number} ({k.name})")
        else:
            bits.append(f"#{k.number} ({k.name}), mitred")
    return ", ".join(bits)


def _face_is_round(k: Member, toward_u) -> bool:
    s = _cross(k.along, toward_u)
    side_tags = k.sect.tags
    p = k.sect.poly
    x = p[:, 0].max() if s >= 0 else p[:, 0].min()
    idx = [i for i in range(len(p)) if abs(p[i, 0] - x) < 1e-6]
    return all(side_tags[i] == "bark" and side_tags[i - 1] == "bark" for i in idx)


def _fix_words(m: Member, e: int, b: Base) -> str:
    nd = m.node[e]
    if b.opts.support == "piers" and nd is not None and nd.pier:
        return "It lands on the pier under this joint: pin it down with a 12 in spike or a rebar pin."
    recv = m.receivers[e]
    if recv:
        k = recv[0]
        if MATERIALS[k.mat][1] == "lumber" and MATERIALS[m.mat][1] == "lumber":
            return f"Hang it on #{k.number} with a joist hanger (or three 3-1/2 in structural screws, toed)."
        return (f"Let it 1 in into #{k.number} (a notch the shape of its end) and spike it: two 10 in spikes "
                f"or timber screws.")
    return "Butt it tight and toe-screw it."


def _setup_fits(m: Member, s: rc.Setup) -> bool:
    pts = np.array([m.solid.point(x, z, 0.0) for x, z in m.sect.poly]) if m.solid is not None else None
    if pts is None:
        return False
    h = float((pts @ s.frame[2]).max() - (pts @ s.frame[2]).min())
    d = float((pts @ s.frame[1]).max() - (pts @ s.frame[1]).min())
    return h <= K["saw_height_in"] + 1e-6 and d <= K["saw_depth_in"] + 1e-6


FACE_WORDS = {"face bottom": "its bottom", "face top": "its top", "face side L": "its left side",
              "face side R": "its right side"}


def _fence_face(m: Member, s: rc.Setup) -> str:
    best, val = "", -2.0
    for tag in FACE_WORDS:
        n = rc._face_normal(m.solid, tag)
        if n is not None and float(n @ s.frame[1]) > val:
            best, val = tag, float(n @ s.frame[1])
    return FACE_WORDS.get(best, "its back")


def member_recipe(m: Member, b: Base) -> rc.Recipe:
    o = b.opts
    name, kind = MATERIALS[m.mat][0], MATERIALS[m.mat][1]
    need = m.s_hi - m.s_lo
    trunk = is_trunk(m.mat)
    margin = K["trim_in"] if trunk else rc.END_MARGIN
    stock_len = _max_len(o, m.mat) if m.role != "frame" else o.side_in
    dims = [("Material", name + (f", from a {o.log_in:g} in log" if trunk else "")),
            ("Cut from", f"{m.stock} -- {m.stock_order}" if m.stock else "-"),
            ("Length overall", f"{need:.2f} in ({ftin(need)})")]
    for label, lo, hi in m.marks:
        dims.append((f"Length {label}", f"{hi - lo:.2f} in ({ftin(hi - lo)})"))
    dims.append(("End 1", f"{_end_words(m, 0)}; meets {_meet_words(m, 0)}"))
    dims.append(("End 2", f"{_end_words(m, 1)}; meets {_meet_words(m, 1)}"))
    if m.spans:
        worst = max(m.spans, key=lambda t: t[2])
        dims.append(("Longest span", f"{worst[0]:.1f} in, {worst[2] * 100:.0f}% of what it can carry"
                     + (f" (after {m.extra_piers} extra pier{'s' if m.extra_piers != 1 else ''})"
                        if m.extra_piers else "")))
    pack = b.top - m.sect.depth - (K["clearance_in"] if o.support == "piers" else 0.0)
    if pack > 0.05:
        dims.append(("Top flush", f"its bottom sits {pack:.2f} in higher than the deepest members' -- pack it "
                                  f"up that much wherever it rests on a pier or the bed"))
    steps: list[rc.Step] = []
    how_lay = ("as it will sit in the floor, top up, chocked on blocks so it cannot roll" if trunk else
               "on edge on blocks, top up")
    take = (f"Take {m.stock}" if m.stock else f"Take a {name.lower()}") + \
        f" ({m.stock_order}). Write {m.number} on it in chalk." if m.role != "frame" else \
        f"Take {m.stock}. Write {m.number} on it. Its round back measures the full {o.side_in / 12:g} ft."
    steps.append(rc.Step("stock", "Take the stock", take))
    # The stick as it comes, for the cut animations.
    s0 = m.s_lo - margin
    stick = so.prism(m.sect.poly, m.sect.tags, m.a, m.along, m.left, b.top)
    al3 = np.array([m.along[0], m.along[1], 0.0])
    a3 = np.array([m.a[0], m.a[1], b.top])
    stick = so.clip(stick, so.Plane(al3, float(al3 @ a3) + s0, "raw end"))
    stick = so.clip(stick, so.Plane(-al3, -(float(al3 @ a3) + s0 + max(stock_len, need + 2 * margin)), "raw end"))
    current = stick
    k = 0
    for e, label in ((0, "end 1"), (1, "end 2")):
        for pl in m.planes[e]:
            k += 1
            keeper = so.clip(current, pl)
            offcut = so.clip(current, so.Plane(-pl.n, -pl.d, "cut"))
            ang = math.degrees(math.acos(min(1.0, abs(float(pl.n[:2] @ m.along)))))
            marks = []
            for mname, x, z in _mark_lines(m):
                lo, hi = _s_range(m, x, z, b.top, [pl])
                s = lo if e == 0 else hi
                ref = (s - s0) if e == 0 else (s - m.s_lo + 0.0)
                marks.append((mname, s, ref))
            if e == 0:
                where = ("Trim the raw end: " + "; ".join(f"{max(0.0, r):.2f} in from the raw end {n}"
                                                         for n, _s, r in marks))
            else:
                first = {n: s for n, s, _r in [(n, lo, 0) for n, lo, _hi in m.marks]}
                where = ("Measure from the end 1 cut: " +
                         "; ".join(f"{s - first.get(n, m.s_lo):.2f} in ({ftin(s - first.get(n, m.s_lo))}) {n}"
                                   for n, s, _r in marks))
            side = "square" if ang < 0.05 else f"{ang:.1f}° off square"
            sets = [s for s in rc.setups(m.solid, pl) if s.feasible] if kind == "lumber" else []
            sets = [s for s in sets if _setup_fits(m, s)]
            sets.sort(key=lambda s: (abs(s.bevel) > 0.05, abs(s.mitre)))
            if sets:
                st = sets[0]
                text = (f"Lay it on the saw with {FACE_WORDS.get(st.table_tag, 'a flat face')} on the table and "
                        f"{_fence_face(m, st)} against the fence, the keeper to the "
                        f"{'RIGHT' if st.keeper_right else 'LEFT'} of the blade (left and right as you stand at "
                        f"end 1 looking toward end 2, for its sides). Mitre {rc.mitre_words(st.mitre)}. "
                        f"Bevel {rc.bevel_words(st.bevel)}. {where}. The cut is {side} in plan, plumb when the "
                        f"piece stands in the floor.")
                anim = {"type": "mitre", "frame": st.frame, "plane": pl, "stick": current, "keeper": keeper,
                        "offcut": offcut, "mitre": st.mitre, "bevel": st.bevel, "keeper_right": st.keeper_right}
                steps.append(rc.Step("saw", f"Cut {k} ({label}) on the mitre saw", text, anim))
            else:
                tool = "chainsaw" if trunk else "circular saw (both sides if it is deeper than the blade)"
                text = (f"Set it {how_lay}. {where}. Join the marks across the "
                        f"top with a straightedge -- the line runs {side}. Square the line down both sides with a "
                        f"level so the cut is plumb, and cut to the lines with the {tool}.")
                anim = {"type": "freehand", "plane": pl, "stick": current, "keeper": keeper, "offcut": offcut}
                steps.append(rc.Step("mark", f"Cut {k} ({label}), marked and cut by hand", text, anim))
            current = keeper
    finished = "; ".join(f"{hi - lo:.2f} in {n}" for n, lo, hi in m.marks)
    steps.append(rc.Step("check", "Check it", f"Finished: {finished}. Measure each against the list."))
    place = (f"It runs from {_meet_words(m, 0)} to {_meet_words(m, 1)}. End 1: {_fix_words(m, 0, b)} "
             f"End 2: {_fix_words(m, 1, b)}")
    if kind == "half":
        place += " Flat face " + ("toward the middle" if m.role != "frame" else "in, round back out") + "."
    if any(_face_is_round(k, m.u(e)) for e in (0, 1) for k, how in m.meets[e] if k is not None and how == "face"):
        place += (" Where an end meets a round back, scribe the curve onto the end and chisel or chainsaw it "
                  "to fit -- the cut list gives the length to the crown.")
    steps.append(rc.Step("place", "Put it in", place, {"type": "place", "solid": m.solid}))
    summary = f"{MATERIALS[m.mat][0].split(' (')[0]}, {need:.1f} in"
    return rc.Recipe(m.number, m.name, summary, dims, steps, None)


def pier_recipe(p: Pier, b: Base) -> rc.Recipe:
    h = p.top
    dims = [("Material", f"a round of a {K['pier_dia_in']:g} in log"),
            ("Cut from", p.stock or "-"),
            ("Height", f"{h:.2f} in ({ftin(h)}) above the pad"),
            ("Load on it", f"{p.load_lb:.0f} lb"),
            ("Gravel pad", f"{pad_in(p.load_lb):.0f} in square ({K['soil_psf']:.0f} lb/ft2 soil)")]
    steps = [rc.Step("stock", "Cut the round",
                     f"From {p.stock or 'a pier log'}, cut a round {h + K['trim_in']:.2f} in long, both ends "
                     f"square. Write P{p.number - len(b.members)} on it."),
             rc.Step("pad", "Dig the pad",
                     f"Dig a {pad_in(p.load_lb):.0f} in square hole to firm ground under the mark, fill it with "
                     "crushed gravel in 2 in lifts and tamp each one. Level the top."),
             rc.Step("set", "Set it",
                     f"Stand the round on the pad, plumb, and trim its top to {h:.2f} in above the pad so the "
                     f"members over it sit flush. It carries {p.load_lb:.0f} lb.",
                     {"type": "place", "solid": p.solid})]
    return rc.Recipe(p.number, f"Pier {p.number - len(b.members)}", f"stump pier, {h:.1f} in", dims, steps, None)


def summary_card(b: Base) -> rc.Recipe:
    o, c, st = b.opts, b.checks, b.stock
    steps = []
    fit = ""
    if c["dome_fits"] is not None:
        fit = (f" The dome needs {c['dome_need_in'] / 12:.2f} ft of radius ({o.dome_radius_in / 12:.2f} ft sphere "
               f"+ {K['dome_overhang_in']:g} in for its frame): "
               + ("it fits, with " if c["dome_fits"] else "it does NOT fit: short by ")
               + f"{abs(c['inner_r_in'] - c['dome_need_in']) / 12:.2f} ft at the narrowest.")
    steps.append(rc.Step("info", "The pentagon",
                         f"{o.side_in / 12:g} ft sides along the round backs. Largest circle inside the flat faces: "
                         f"{c['inner_r_in'] / 12:.2f} ft radius ({2 * c['inner_r_in'] / 12:.2f} ft across). "
                         f"Corner to centre {c['corner_r_in'] / 12:.2f} ft. Floor {c['area_ft2']:.0f} ft2." + fit))
    if o.support == "piers":
        verdict = ("Every span passes" if c["worst_ratio"] <= 1.0 + 1e-9 else "Some spans fail")
        steps.append(rc.Step("info", "Strength",
                             f"{verdict}: the worst span works at {c['worst_ratio'] * 100:.0f}% of what it can "
                             f"carry ({K['live_psf']:g} + {K['dead_psf']:g} lb/ft2, sag under span/"
                             f"{K['deflect_ratio']:g}). {c['extra_piers']} pier(s) were added mid-span to get "
                             f"there; {c['piers']} piers in all. Heaviest pier {c['pier_max_lb']:.0f} lb, on a "
                             f"{c['pad_max_in']:.0f} in pad; {c['big_pads']} pier(s) need a pad bigger than "
                             f"{K['pad_min_in']:g} in. The piers carry {c['pier_sum_lb']:.0f} lb of the "
                             f"{c['total_lb']:.0f} lb floor load."))
    else:
        steps.append(rc.Step("info", "Strength",
                             f"Every member bears on the gravel along its length, so nothing spans: the bed "
                             f"carries the {c['total_lb']:.0f} lb floor load. Level the bed to each member's "
                             f"depth and compact it."))
    if o.deck == "fill":
        steps.append(rc.Step("info", "Decking", "No decking: earth, gravel or cob is packed between the members "
                                                "and tamped to their tops."))
    else:
        ok = c["deck_ok"]
        steps.append(rc.Step("info", "Decking",
                             f"{DECKS[o.deck][0]}: the widest gap it has to bridge is {c['deck_clear_in']:.1f} in; "
                             f"it may span {c['deck_allow_in']:g} in. " +
                             ("It passes." if ok else "It does NOT pass: add joists, close the spacing, or "
                                                      "choose a stiffer deck.")))
    lines = [f"- {a}: {bq}" + (f" (${usd:,.0f})" if usd else "") for a, bq, usd in st["lines"]]
    steps.append(rc.Step("info", "Buy and cut",
                         f"Frame: your five {o.side_in / 12:g} ft half trunks.\n" + "\n".join(lines) +
                         f"\nLogs to fell or buy: {st['logs_total']}. Bought materials about ${st['usd']:,.0f}."))
    steps.append(rc.Step("info", "Declared numbers (not derived)",
                         "\n" + "\n".join("- " + t for t in constants_table())))
    return rc.Recipe(0, "The whole base", "", [], steps, None)


def compare(o: BaseOptions) -> list[str]:
    """Every pattern with these materials, side by side."""
    rows = []
    for key, (name, _why) in PATTERNS.items():
        b = build(replace(o, pattern=key), with_recipes=False)
        c, st = b.checks, b.stock
        pieces = len(b.members)
        strength = "gravel bed" if o.support == "gravel" else \
            f"worst span {c['worst_ratio'] * 100:.0f}%, {c['extra_piers']} extra piers, {c['piers']} piers"
        deck = "fill" if b.opts.deck == "fill" else f"deck gap {c['deck_clear_in']:.0f} in " + \
            ("ok" if c["deck_ok"] else "TOO WIDE")
        rows.append(f"{name}: {pieces} members; {strength}; {deck}; logs {st['logs_total']}; "
                    f"bought ${st['usd']:,.0f}")
    return rows


def validate_base() -> None:
    for key in PATTERNS:
        for support in ("piers", "gravel"):
            o = BaseOptions(pattern=key, support=support, deck="fill" if support == "gravel" else "2x6",
                            prim_mat="half" if key != "beams" else "6x6")
            b = build(o)
            assert b.members, key
            assert len(b.recipes) == len(b.members) + len(b.piers), key
            for m in b.members:
                assert m.solid is not None and m.s_hi - m.s_lo > 1.0, (key, m.name)
                assert np.isfinite(m.solid.vertices()).all()
            if support == "piers":
                c = b.checks
                assert abs(c["pier_sum_lb"] - c["total_lb"]) < 0.02 * c["total_lb"], \
                    (key, c["pier_sum_lb"], c["total_lb"])
                assert c["worst_ratio"] <= 1.0 + 1e-6, (key, c["worst_ratio"])
    # The frame: five pieces whose round backs are the full side, mitred 36 degrees.
    b = build(BaseOptions(pattern="star"))
    frame = [m for m in b.members if m.role == "frame"]
    assert len(frame) == 5
    for m in frame:
        back = [hi - lo for n, lo, hi in m.marks if "widest" in n]
        assert back and abs(back[0] - 240.0) < 0.05, back
        assert all(abs(math.degrees(math.acos(abs(float(pl.n[:2] @ m.along)))) - 36.0) < 0.05
                   for e in (0, 1) for pl in m.planes[e]), "frame corners are 36 degrees off square"
    # A half trunk on edge: I = pi r^4 / 8.
    s = section("half", 12.0)
    assert abs(s.inertia - math.pi * 6 ** 4 / 8) / (math.pi * 6 ** 4 / 8) < 0.02, s.inertia


# ----------------------------------------------------------------------
# Files
# ----------------------------------------------------------------------

def _free(path):
    from .export import free_path
    return free_path(path)


def _stem(b: Base) -> str:
    o = b.opts
    return f"base-{o.pattern}-{o.frame_mat}-{o.prim_mat}-{o.sec_mat}-{o.support}"


def write_cut_list(b: Base, out_dir):
    """Every member and pier: its stock, its lengths, its end cuts."""
    import csv
    path = _free(out_dir / f"{_stem(b)}-cut-list.csv")
    with open(path, "w", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        w.writerow([b.title])
        w.writerow(["#", "piece", "material", "cut from", "order", "overall (in)", "overall (ft-in)",
                    "lengths to mark", "end 1", "end 2", "longest span"])
        for m in b.members:
            marks = "; ".join(f"{hi - lo:.2f} in {n}" for n, lo, hi in m.marks)
            span = ""
            if m.spans:
                sp, _ok, r = max(m.spans, key=lambda t: t[2])
                span = f"{sp:.1f} in at {r * 100:.0f}%"
            w.writerow([m.number, m.name, MATERIALS[m.mat][0], m.stock, m.stock_order, f"{m.s_hi - m.s_lo:.2f}",
                        ftin(m.s_hi - m.s_lo), marks, f"{_end_words(m, 0)} -> {_meet_words(m, 0)}",
                        f"{_end_words(m, 1)} -> {_meet_words(m, 1)}", span])
        for p in b.piers:
            w.writerow([p.number, f"Pier {p.number - len(b.members)}", f"{K['pier_dia_in']:g} in log round",
                        p.stock, "", f"{p.top:.2f}", ftin(p.top), f"pad {pad_in(p.load_lb):.0f} in square",
                        "", "", f"{p.load_lb:.0f} lb"])
        w.writerow([])
        w.writerow(["Buy"])
        for a, q, usd in b.stock["lines"]:
            w.writerow([a, q, f"${usd:,.0f}" if usd else ""])
    return path


def write_compare(o: BaseOptions, rows: list[str], out_dir):
    path = _free(out_dir / f"base-compare-{o.frame_mat}-{o.prim_mat}-{o.sec_mat}-{o.support}.txt")
    head = [f"Every floor-base pattern with: frame {MATERIALS[o.frame_mat][0]}, primaries "
            f"{MATERIALS[o.prim_mat][0]}, joists {MATERIALS[o.sec_mat][0]}, {SUPPORTS[o.support]}, "
            f"deck {DECKS[o.deck][0]}, {o.log_in:g} in logs, {o.side_in / 12:g} ft sides.", ""]
    path.write_text("\n".join(head + rows + ["", "Declared numbers:"] + constants_table()), encoding="utf-8")
    return path


def write_plan_svg(b: Base, out_dir):
    """The floor from above: every member's outline and number, every pier."""
    from .geom2d import hull
    path = _free(out_dir / f"{_stem(b)}-plan.svg")
    lo, hi = b.crown.min(axis=0) - 30, b.crown.max(axis=0) + 30
    W = 1400
    sc = W / float(hi[0] - lo[0])
    H = int((hi[1] - lo[1]) * sc) + 140

    def X(p):
        return (p[0] - lo[0]) * sc, (hi[1] - p[1]) * sc + 110
    parts = [f'<svg xmlns="http://www.w3.org/2000/svg" width="{W}" height="{H}" viewBox="0 0 {W} {H}" '
             f'font-family="Segoe UI, Arial, sans-serif">',
             f'<rect width="{W}" height="{H}" fill="#fbf7ef"/>',
             f'<text x="20" y="34" font-size="22" font-weight="bold">{b.title}</text>',
             f'<text x="20" y="62" font-size="14">{len(b.members)} members, {len(b.piers)} piers. '
             f'{b.opts.side_in / 12:g} ft sides along the round backs; numbers match the cut list.</text>']
    fills = {"frame": "#8a5a36", "primary": "#b98a5a", "joist": "#e2c58f"}
    for m in b.members:
        h = hull(m.solid.vertices()[:, :2])
        pts = " ".join(f"{x:.1f},{y:.1f}" for x, y in (X(p) for p in h))
        parts.append(f'<polygon points="{pts}" fill="{fills.get(m.role, "#ccc")}" stroke="#3b2a1c" '
                     f'stroke-width="1"/>')
    for p in b.piers:
        x, y = X(p.xy)
        parts.append(f'<circle cx="{x:.1f}" cy="{y:.1f}" r="{K["pier_dia_in"] / 2 * sc:.1f}" fill="none" '
                     f'stroke="#4a6a8a" stroke-width="1.5" stroke-dasharray="3 2"/>')
    for m in b.members:
        x, y = X((m.a + m.b) / 2)
        parts.append(f'<circle cx="{x:.1f}" cy="{y:.1f}" r="9" fill="#fff" stroke="#3b2a1c"/>'
                     f'<text x="{x:.1f}" y="{y + 4:.1f}" font-size="10" text-anchor="middle">{m.number}</text>')
    parts.append("</svg>")
    path.write_text("\n".join(parts), encoding="utf-8")
    return path
