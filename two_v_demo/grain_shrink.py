"""Which way the rings run: why store lumber warps as it dries and a wedge stays true.

A wedge strut shrinks. Every piece of wood does. What the film this module feeds
(:mod:`two_v_demo.lesson_rings`) shows is that a wedge shrinks *the same way every
time and keeps its shape*, and a store-bought board shrinks in a way decided by
where in the log the saw happened to cut it -- which nobody at the store knows.

**The one rule.** Wood shrinks about one and a half times as much *round* the
growth rings (tangential) as *across* them (radial), and hardly at all along the
grain (:data:`two_v_demo.wood_care.CONSTANTS`). A piece that does not enclose the
pith, drying with nothing holding it, therefore moves every point at radius *r*
and angle *theta* about the pith to::

    r'     = r (1 - e_R)
    theta' = theta_0 + (theta - theta_0) (1 - e_T) / (1 - e_R)

radial strain ``e_R`` along every radius, tangential strain ``e_T`` along every
ring, and no stress anywhere (:func:`free_shrink`). That one map is the whole
film, and four consequences fall straight out of it:

* a face cut **along a radius** stays straight, because radii map to radii --
  the wedge's two sawn faces;
* a face cut **along a ring** stays a ring, because circles about the pith map
  to circles -- the wedge's bark face;
* **any other straight face bends** -- every face of a board, but at most one:
  the cup of a flatsawn board, the diamond of a square with diagonal rings;
* a piece that **encloses the pith cannot follow the map at all**: the full
  circle comes up short by ``360 (1 - k)`` degrees and the wood tears along a
  radius -- the check in a boxed heart, and in every log end.

So the shape a board takes depends on where its pith was, and a store board
does not tell you. A wedge's pith is always at its point.

The boards are the ones a mill saws from the same log the wedges come from
(:func:`two_v_demo.wedge_geometry.lumber_yield`), and the wedge is the exact,
kerfed section (:func:`two_v_demo.wedge_geometry.split_section`). The handbook
shrinkage, fibre saturation and target moisture are
:mod:`two_v_demo.wood_care`'s and :mod:`two_v_demo.seam_climate`'s; the sector's
angle change is :func:`two_v_demo.wood_care.sector_after_drying`'s, so this film
and the seam chapters state the same figure from the same function.

**What it does not model**, and the film says so: real logs (a wandering pith,
reaction wood, knots), and movement *along* the length -- the youngest wood at a
wedge's point shrinks more along the grain than the rest, so a wedge can bow
toward its point, the same way in every member, by an amount not measured here.

    py -3.12 -m two_v_demo.grain_shrink
"""

from __future__ import annotations

import math
from dataclasses import dataclass
from functools import lru_cache

import numpy as np

from . import seam_climate as scl
from . import wedge_geometry as wg
from . import wood_care as wc

TAU = 2.0 * math.pi

CONSTANTS: tuple[tuple[str, float, str, str, str], ...] = (
    ("sdry_mc", 0.19, "kg/kg", "standard",
     "S-DRY on a grade stamp: surfaced at 19% moisture or less (American Softwood "
     "Lumber Standard, PS 20). The mill planes it straight there; the rest of the drying "
     "happens after you buy it"),
    ("stud_t_in", 1.5, "in", "standard", "a dressed 2x4 is 1.5 in thick (PS 20 dry dressed size)"),
    ("stud_w_in", 3.5, "in", "standard", "and 3.5 in wide"),
    ("joist_w_in", 9.25, "in", "standard", "a dressed 2x10 is 9.25 in wide"),
    ("post_in", 3.5, "in", "standard", "a dressed 4x4 post is 3.5 in square"),
    ("shrink_long_lo", 0.001, "-", "standard",
     "along the grain, green to oven-dry, normal wood: 0.1 to 0.2% (USDA Wood Handbook, ch. 4)"),
    ("shrink_long_hi", 0.002, "-", "standard", "the top of that range"),
    ("flat_below_deg", 30.0, "deg", "standard",
     "rings under 30 degrees to the wide face, measured at the board's centre: flatsawn"),
    ("quarter_above_deg", 60.0, "deg", "standard",
     "rings over 60 degrees to the wide face: quartersawn; between the two: rift"),
)
"""Handbook and grading values, each with its source."""

DISPLAY: tuple[tuple[str, float, str, str, str], ...] = (
    ("drawn_x", 5.0, "x", "display",
     "the movement is drawn five times life size so it can be seen; every number "
     "on screen is the true one"),
)
"""How the picture is drawn. Not a property of wood."""

C = {name: value for name, value, _u, _k, _w in CONSTANTS + DISPLAY}


def _kerf(label: str) -> float:
    return next(k for k, name in wg.KERFS_IN if name == label)


MILL_KERF = "bandsaw mill"
WEDGE_KERF = "ripping chainsaw"


# ----------------------------------------------------------------------
# The rule
# ----------------------------------------------------------------------

def moisture_strain(mc_from: float, mc_to: float) -> tuple[float, float]:
    """(radial, tangential) shrinkage strain between two moistures, from the handbook values."""
    f = wc.shrinkage_fraction(mc_to) - wc.shrinkage_fraction(mc_from)
    return wc.C["shrink_radial"] * f, wc.C["shrink_tangential"] * f


def ring_closure(er: float, et: float) -> float:
    """How much every angle about the pith is multiplied by: (1 - e_T) / (1 - e_R)."""
    return (1.0 - et) / (1.0 - er)


def wrap(a):
    """An angle, or an array of them, into (-pi, pi]."""
    return -((-np.asarray(a, dtype=float) + math.pi) % TAU - math.pi)


def unwrapped(xy: np.ndarray, theta0: float) -> np.ndarray:
    """Each point's angle about the pith, continuous about ``theta0`` (within pi of it)."""
    return theta0 + wrap(np.arctan2(xy[:, 1], xy[:, 0]) - theta0)


def free_shrink(xy: np.ndarray, er: float, et: float, theta0: float, ang: np.ndarray | None = None) -> np.ndarray:
    """THE map: every point about the pith (the origin), dried with nothing holding it.

    ``ang`` is each point's unwrapped angle; for a piece that does not enclose the pith it
    is :func:`unwrapped`. A piece that does is given a slit and its angles explicitly
    (:func:`disc_mesh`, :func:`rect_mesh`), and the gap opens at the slit."""
    xy = np.asarray(xy, dtype=float)
    r = np.hypot(xy[:, 0], xy[:, 1])
    a = unwrapped(xy, theta0) if ang is None else np.asarray(ang, dtype=float)
    a2 = theta0 + (a - theta0) * ring_closure(er, et)
    r2 = r * (1.0 - er)
    return np.stack([r2 * np.cos(a2), r2 * np.sin(a2)], axis=1)


def check_angle_deg(er: float, et: float) -> float:
    """What a full ring comes up short by, when it cannot follow the map: the check's V."""
    return 360.0 * (1.0 - ring_closure(er, et))


# ----------------------------------------------------------------------
# Measuring a dried piece
# ----------------------------------------------------------------------

def _line(p0, p1, n: int = 81) -> np.ndarray:
    t = np.linspace(0.0, 1.0, n)[:, None]
    return np.asarray(p0, float) * (1 - t) + np.asarray(p1, float) * t


def face_bow(p0, p1, er: float, et: float, theta0: float) -> float:
    """How far a straight face, dried, departs from straight: the largest gap between the
    dried face and the line joining its dried ends. Signed: positive when the middle has moved
    toward the pith (the face is hollow as seen from outside the piece, away from the pith)."""
    pts = _line(p0, p1)
    q = free_shrink(pts, er, et, theta0)
    a, b = q[0], q[-1]
    u = (b - a) / np.linalg.norm(b - a)
    n = np.array([-u[1], u[0]])
    d = (q - a) @ n
    i = int(np.argmax(np.abs(d)))
    mid = q[len(q) // 2]
    toward = -mid / (np.linalg.norm(mid) or 1.0)          # from the face toward the pith
    sign = 1.0 if (n @ toward) * d[i] > 0 else -1.0
    return sign * abs(float(d[i]))


def corner_angle_deg(c, a, b, er: float, et: float, theta0: float, step: float = 1e-3) -> float:
    """The dried angle at corner ``c`` between its edges toward ``a`` and toward ``b``."""
    c, a, b = (np.asarray(v, float) for v in (c, a, b))
    pts = np.array([c, c + (a - c) * step, c + (b - c) * step])
    q = free_shrink(pts, er, et, theta0)
    u, v = q[1] - q[0], q[2] - q[0]
    return math.degrees(math.acos(float(u @ v / (np.linalg.norm(u) * np.linalg.norm(v)))))


@dataclass(frozen=True)
class Board:
    """One rectangle sawn from the log: lower-left corner, size, about the pith at the origin."""

    x0: float
    y0: float
    w: float
    t: float

    @property
    def centre(self) -> np.ndarray:
        return np.array([self.x0 + self.w / 2, self.y0 + self.t / 2])

    @property
    def corners(self) -> tuple[np.ndarray, ...]:
        x0, y0, x1, y1 = self.x0, self.y0, self.x0 + self.w, self.y0 + self.t
        return tuple(np.array(p, float) for p in ((x0, y0), (x1, y0), (x1, y1), (x0, y1)))

    @property
    def holds_pith(self) -> bool:
        return self.x0 < 0 < self.x0 + self.w and self.y0 < 0 < self.y0 + self.t

    @property
    def ring_angle_deg(self) -> float:
        """Angle between the rings and the wide face, at the board's centre. The ring's tangent
        is square to the radius, so it is the radius's angle from the thickness direction."""
        cx, cy = self.centre
        return math.degrees(math.atan2(abs(cx), abs(cy)))

    @property
    def kind(self) -> str:
        if self.holds_pith:
            return "boxed heart"
        a = self.ring_angle_deg
        return "flatsawn" if a < C["flat_below_deg"] else "quartersawn" if a > C["quarter_above_deg"] else "rift"


@dataclass(frozen=True)
class Movement:
    """What drying does to one board, at true size."""

    board: Board
    kind: str
    ring_angle_deg: float
    width_loss_in: float
    thick_loss_in: float
    cup_in: float                  # the wide face that bends most: + hollow away from the pith
    diamond_deg: float             # the corner that moves furthest from square
    check_deg: float               # the V a boxed heart must open (0 if it holds no pith)
    check_gap_in: float            # the check's width at the face it opens on

    @property
    def width_loss_pct(self) -> float:
        return 100.0 * self.width_loss_in / self.board.w

    @property
    def thick_loss_pct(self) -> float:
        return 100.0 * self.thick_loss_in / self.board.t


def board_movement(b: Board, er: float, et: float) -> Movement:
    c = b.centre
    theta0 = math.atan2(c[1], c[0])
    if b.holds_pith:
        # A boxed heart cannot follow the map: it checks. The check runs from the pith to the top
        # face (rect_mesh cuts its slit there); its two lips are the same green point given angles
        # a full turn apart, and the map parts them by the V. Across the pith, both the width and
        # the thickness are two radii end to end, so each loses e_R.
        top = np.array([[0.0, b.y0 + b.t]] * 2)
        theta0 = 1.5 * math.pi
        q = free_shrink(top, er, et, theta0, ang=np.array([theta0 - math.pi, theta0 + math.pi]))
        return Movement(b, b.kind, b.ring_angle_deg, b.w * er, b.t * er, 0.0, 0.0,
                        check_angle_deg(er, et), float(np.linalg.norm(q[0] - q[1])))
    p = b.corners
    q = free_shrink(np.array(p), er, et, theta0)
    mids_g = [(p[0] + p[3]) / 2, (p[1] + p[2]) / 2, (p[0] + p[1]) / 2, (p[3] + p[2]) / 2]
    mids_d = free_shrink(np.array(mids_g), er, et, theta0)
    width = float(np.linalg.norm(mids_d[1] - mids_d[0]))
    thick = float(np.linalg.norm(mids_d[3] - mids_d[2]))
    cups = [face_bow(p[0], p[1], er, et, theta0), face_bow(p[3], p[2], er, et, theta0)]
    cup = max(cups, key=abs)
    a = [corner_angle_deg(p[i], p[(i + 1) % 4], p[(i - 1) % 4], er, et, theta0) for i in range(4)]
    del q
    # A diamond is opposite corners opening together while the other two close: the rectangle
    # leaning into a parallelogram. (Corners on one face opening together is the cup's taper.)
    diamond = abs(a[0] + a[2] - a[1] - a[3]) / 4.0
    return Movement(b, b.kind, b.ring_angle_deg, b.w - width, b.t - thick, cup, diamond, 0.0, 0.0)


# ----------------------------------------------------------------------
# The log, the store boards, the wedges
# ----------------------------------------------------------------------

def log_diameter_in() -> float:
    """The seed dome's log, the same one wood_care dries the wedges from."""
    return wc.sector_after_drying().log_in


def splits() -> int:
    import seed_model
    return int(seed_model.SEED_RADIAL_SPLITS)


@lru_cache(maxsize=4)
def stud_boards(diameter_in: float | None = None) -> tuple[Board, ...]:
    """The log sawn for studs, the way a mill saws it (wedge_geometry.lumber_yield)."""
    d = diameter_in or log_diameter_in()
    y = wg.lumber_yield(d, C["stud_t_in"], C["stud_w_in"], _kerf(MILL_KERF))
    return tuple(Board(x, yy, C["stud_w_in"], C["stud_t_in"]) for x, yy in y.pieces)


def green_to_target() -> tuple[float, float]:
    """Green (above fibre saturation) down to the frame's working moisture."""
    return moisture_strain(wc.C["fibre_saturation"], scl.C["mc_target"])


def after_purchase() -> tuple[float, float]:
    """What is still to come after the mill planes it straight at S-DRY: 19% to working moisture."""
    return moisture_strain(C["sdry_mc"], scl.C["mc_target"])


@dataclass(frozen=True)
class WedgeMovement:
    bisector_deg: float
    angle_green_deg: float
    angle_dry_deg: float
    close_deg: float
    depth_green_in: float
    depth_dry_in: float
    face_bow_in: float             # the sawn faces: offset half a kerf from a radius, so not quite zero
    bark_roundness_in: float       # spread of the dried bark face's radius about the pith


@lru_cache(maxsize=1)
def wedge_section():
    return wg.split_section(log_diameter_in(), splits(), _kerf(WEDGE_KERF))


def wedge_corners(bisector_deg: float) -> tuple[np.ndarray, np.ndarray, np.ndarray]:
    """A kerfed wedge's point, and where each sawn face meets the bark: the clockwise face's
    end, then the counter-clockwise one's. About the pith, inches."""
    s = wedge_section()
    r = s.diameter_in / 2
    half = math.pi / splits()
    phi = math.radians(bisector_deg)
    point = s.point_setback_in * np.array([math.cos(phi), math.sin(phi)])
    ends = []
    for side in (-1.0, 1.0):
        u = np.array([math.cos(phi + side * half), math.sin(phi + side * half)])
        b = point @ u
        t = -b + math.sqrt(b * b - (point @ point - r * r))
        ends.append(point + t * u)
    return point, ends[0], ends[1]


def wedge_movement(bisector_deg: float, er: float, et: float) -> WedgeMovement:
    """One kerfed wedge, its point toward the pith, dried by the map."""
    s = wedge_section()
    r = s.diameter_in / 2
    phi = math.radians(bisector_deg)
    point, *ends = wedge_corners(bisector_deg)
    qp, qa, qb = free_shrink(np.array([point, ends[0], ends[1]]), er, et, phi)
    u, v = qa - qp, qb - qp
    ang_dry = math.degrees(math.acos(float(u @ v / (np.linalg.norm(u) * np.linalg.norm(v)))))
    bows = [face_bow(point, e, er, et, phi) for e in ends]
    edge = math.atan2(ends[1][1], ends[1][0]) - phi
    arc = np.array([[r * math.cos(phi + a), r * math.sin(phi + a)] for a in np.linspace(-edge, edge, 61)])
    radii = np.hypot(*free_shrink(arc, er, et, phi).T)
    bark = r * np.array([math.cos(phi), math.sin(phi)])
    dp = free_shrink(np.array([point, bark]), er, et, phi)
    return WedgeMovement(bisector_deg, 360.0 / splits(), ang_dry, 360.0 / splits() - ang_dry,
                         r - s.point_setback_in, float(np.linalg.norm(dp[1] - dp[0])),
                         max(bows, key=abs), float(radii.max() - radii.min()))


def all_wedges(er: float, et: float) -> tuple[WedgeMovement, ...]:
    n = splits()
    return tuple(wedge_movement(90.0 + i * 360.0 / n, er, et) for i in range(n))


# ----------------------------------------------------------------------
# Everything the film says, computed once
# ----------------------------------------------------------------------

@dataclass(frozen=True)
class Facts:
    er: float                      # green to working moisture
    et: float
    er_after: float                # S-DRY to working moisture: after the store
    et_after: float
    k: float
    check_deg: float
    log_in: float
    boards: tuple[Movement, ...]   # every stud in the log, green to working moisture
    after: tuple[Movement, ...]    # the same studs, S-DRY to working moisture
    wedges: tuple[WedgeMovement, ...]
    sector: object                 # wood_care.Drying: the sector's own figures
    cup_board: int                 # index of the flatsawn board that cups most
    calm_board: int                # the flatsawn board nearest the bark
    diamond_board: int
    heart_board: int
    quarter_board: int
    joist: Movement                # a 2x10 from the same log, the flatsawn one nearest the heart
    post_heart: bool               # does a 4x4 sawn from this log hold the pith?

    def counts(self) -> dict[str, int]:
        out: dict[str, int] = {}
        for m in self.boards:
            out[m.kind] = out.get(m.kind, 0) + 1
        return out

    @property
    def share_still_to_come(self) -> float:
        """Of the green-to-working shrinkage, the share left when the board is sold."""
        return self.et_after / self.et


@lru_cache(maxsize=1)
def facts() -> Facts:
    er, et = green_to_target()
    er2, et2 = after_purchase()
    boards = stud_boards()
    moves = tuple(board_movement(b, er, et) for b in boards)
    after = tuple(board_movement(b, er2, et2) for b in boards)
    flat = [i for i, m in enumerate(moves) if m.kind == "flatsawn"]
    cup = max(flat, key=lambda i: abs(moves[i].cup_in))
    calm = max(flat, key=lambda i: boards[i].centre[1] ** 2 + boards[i].centre[0] ** 2)
    diamond = max((i for i, m in enumerate(moves) if m.kind != "boxed heart"), key=lambda i: moves[i].diamond_deg)
    heart = next(i for i, m in enumerate(moves) if m.kind == "boxed heart")
    quarter = max((i for i, m in enumerate(moves) if m.kind == "quartersawn"), key=lambda i: moves[i].ring_angle_deg)
    y = wg.lumber_yield(log_diameter_in(), C["stud_t_in"], C["joist_w_in"], _kerf(MILL_KERF))
    joists = [board_movement(Board(x, yy, C["joist_w_in"], C["stud_t_in"]), er, et) for x, yy in y.pieces]
    joist = max((m for m in joists if m.kind == "flatsawn"), key=lambda m: abs(m.cup_in))
    posts = wg.lumber_yield(log_diameter_in(), C["post_in"], C["post_in"], _kerf(MILL_KERF))
    post_heart = any(Board(x, yy, C["post_in"], C["post_in"]).holds_pith for x, yy in posts.pieces)
    return Facts(er, et, er2, et2, ring_closure(er, et), check_angle_deg(er, et), log_diameter_in(),
                 moves, after, all_wedges(er, et), wc.sector_after_drying(), cup, calm, diamond, heart, quarter,
                 joist, post_heart)


def seam_fold_deg() -> float:
    """The fold at the tighter seam: the dome's, so drying does not change it (channel_facts)."""
    from . import channel_facts as cf
    return min(cf.seam_types(), key=lambda t: t.gap_deg).fold_deg


def spread(values) -> float:
    v = list(values)
    return max(v) - min(v)


# ----------------------------------------------------------------------
# The pictures: meshes for the web stage (sketch_claude/static/lessonstage.js, build_section)
# ----------------------------------------------------------------------

@dataclass
class Mesh:
    xy: np.ndarray                 # (N, 2) green, inches about the pith
    tri: np.ndarray                # (M, 3)
    ang: np.ndarray                # (N,) unwrapped angle about the pith
    theta0: float


def rect_mesh(b: Board, step: float = 0.125, slit: bool = False) -> Mesh:
    """A board as a grid. With ``slit`` (a boxed heart), the column through the pith is cut
    from the pith to the top face, so the dried halves can part there."""
    nx = max(2, int(math.ceil(b.w / step)) + 1)
    ny = max(2, int(math.ceil(b.t / step)) + 1)
    xs = np.linspace(b.x0, b.x0 + b.w, nx)
    ys = np.linspace(b.y0, b.y0 + b.t, ny)
    if slit:
        xs = np.unique(np.append(xs, 0.0))
        ys = np.unique(np.append(ys, 0.0))
    ip = int(np.argmin(np.abs(xs))) if slit else -1
    jp = int(np.argmin(np.abs(ys))) if slit else -1
    pts, idx, angs = [], {}, []
    c = b.centre
    theta0 = 1.5 * math.pi if slit else math.atan2(c[1], c[0])

    def add(x, y, a=None):
        pts.append((x, y))
        angs.append(a)
        return len(pts) - 1

    for i, x in enumerate(xs):
        for j, y in enumerate(ys):
            if slit and i == ip and j > jp:
                idx[(i, j, 0)] = add(x, y, theta0 - math.pi)    # the left lip of the slit
                idx[(i, j, 1)] = add(x, y, theta0 + math.pi)    # the right lip
            else:
                idx[(i, j, 0)] = add(x, y)
    tris = []
    for i in range(len(xs) - 1):
        for j in range(len(ys) - 1):
            def v(ii, jj, right=(i == ip)):
                if slit and ii == ip and jj > jp:
                    return idx[(ii, jj, 1 if right else 0)]
                return idx[(ii, jj, 0)]
            a, bb, cc, d = v(i, j), v(i + 1, j), v(i + 1, j + 1), v(i, j + 1)
            tris += [(a, bb, cc), (a, cc, d)]
    xy = np.array(pts, float)
    auto = unwrapped(xy, theta0)
    ang = np.array([auto[n] if a is None else a for n, a in enumerate(angs)])
    return Mesh(xy, np.array(tris, int), ang, theta0)


def sector_mesh(bisector_deg: float, nr: int = 28, ns: int = 14) -> Mesh:
    """The exact kerfed wedge: a fan from its point to the bark, its two faces half a kerf off
    the radii either side of the bisector."""
    s = wedge_section()
    r = s.diameter_in / 2
    half = math.pi / splits()
    phi = math.radians(bisector_deg)
    h = s.point_setback_in * math.sin(half)                  # each face's offset from its radius
    p0 = s.point_setback_in * np.array([math.cos(phi), math.sin(phi)])
    pts, angs = [tuple(p0)], [phi]
    for i in range(1, nr + 1):
        rho = s.point_setback_in + (r - s.point_setback_in) * i / nr
        beta = half - math.asin(min(1.0, h / rho))
        for j in range(ns + 1):
            a = phi + beta * (2 * j / ns - 1)
            pts.append((rho * math.cos(a), rho * math.sin(a)))
            angs.append(a)
    tris = []
    for j in range(ns):
        tris.append((0, 1 + j, 2 + j))
    for i in range(1, nr):
        a0, a1 = 1 + (i - 1) * (ns + 1), 1 + i * (ns + 1)
        for j in range(ns):
            tris += [(a0 + j, a1 + j, a1 + j + 1), (a0 + j, a1 + j + 1, a0 + j + 1)]
    return Mesh(np.array(pts, float), np.array(tris, int), np.array(angs, float), phi)


def disc_mesh(radius_in: float, slit_deg: float = 90.0, nr: int = 30, nt: int = 120) -> Mesh:
    """The log end, slit along one radius so that, dried, the ring can come up short there."""
    cut = math.radians(slit_deg)
    theta0 = cut + math.pi
    pts, angs = [(0.0, 0.0)], [theta0]
    for i in range(1, nr + 1):
        rho = radius_in * i / nr
        for j in range(nt + 1):
            a = theta0 - math.pi + TAU * j / nt
            pts.append((rho * math.cos(a), rho * math.sin(a)))
            angs.append(a)
    tris = [(0, 1 + j, 2 + j) for j in range(nt)]
    for i in range(1, nr):
        a0, a1 = 1 + (i - 1) * (nt + 1), 1 + i * (nt + 1)
        for j in range(nt):
            tris += [(a0 + j, a1 + j, a1 + j + 1), (a0 + j, a1 + j + 1, a0 + j + 1)]
    return Mesh(np.array(pts, float), np.array(tris, int), np.array(angs, float), theta0)


def boundary_loop(tri: np.ndarray) -> list[int]:
    """The mesh's outline, in order: the edges only one triangle uses, chained."""
    count: dict[tuple[int, int], int] = {}
    for a, b, c in tri:
        for e in ((a, b), (b, c), (c, a)):
            k = (min(e), max(e))
            count[k] = count.get(k, 0) + 1
    nxt: dict[int, list[int]] = {}
    for (a, b), n in count.items():
        if n == 1:
            nxt.setdefault(a, []).append(b)
            nxt.setdefault(b, []).append(a)
    start = min(nxt)
    loop, prev, cur = [start], None, start
    while True:
        options = [v for v in nxt[cur] if v != prev]
        if not options:
            break
        prev, cur = cur, options[0]
        if cur == start:
            break
        loop.append(cur)
        if len(loop) > len(nxt) + 1:
            break
    return loop


def _r(a, nd: int = 4) -> list:
    return [round(float(x), nd) for x in np.asarray(a).ravel()]


def _place(xy: np.ndarray, at=(0.0, 0.0), flip: bool = False, anchor=None) -> np.ndarray:
    """Move a piece in the picture (rigidly): about ``anchor`` (default its own green centre),
    turned over if ``flip``, to ``at``. Inches."""
    xy = np.asarray(xy, float)
    a = np.asarray(anchor, float) if anchor is not None else None
    out = xy - (a if a is not None else 0.0)
    if flip:
        out = out * np.array([1.0, -1.0])
    return out + np.asarray(at, float)


def piece(mesh: Mesh, *, drawn_x: float | None = None, at=None, flip: bool = False,
          bark: float = 0.0, tone: str = "store", label: str = "", appear=(0.0, 0.04),
          explode=(0.0, 0.0), dim: bool = False, recentre: bool = True, dry: bool = True,
          anchor=None, pin=None, ghost: bool = False) -> dict:
    """One piece for the stage: green and drawn-dry positions (inches, already placed), its
    triangles, its outline, and each point's green radius (for the rings). ``pin`` is a green
    point (about the pith) that the dried piece keeps where it was -- a seam's ridge, say."""
    x = C["drawn_x"] if drawn_x is None else drawn_x
    er, et = green_to_target()
    g = mesh.xy
    d = free_shrink(g, er * x, et * x, mesh.theta0, mesh.ang) if dry else g.copy()
    if pin is not None and dry:
        p = np.asarray(pin, float)[None, :]
        d = d + p[0] - free_shrink(p, er * x, et * x, mesh.theta0)[0]
    elif recentre and dry:
        d = d - d.mean(axis=0) + g.mean(axis=0)           # dried where it lay: a rigid shift only
    if anchor is None:
        anchor = g.mean(axis=0) if at is not None else np.zeros(2)
    place = at if at is not None else (0.0, 0.0)
    gp, dp = _place(g, place, flip, anchor), _place(d, place, flip, anchor)
    return {"g": _r(gp), "d": _r(dp), "tri": [int(v) for v in mesh.tri.ravel()],
            "loop": [int(v) for v in boundary_loop(mesh.tri)], "r0": _r(np.hypot(g[:, 0], g[:, 1]), 3),
            "bark": round(float(bark), 3), "tone": tone, "label": label, "appear": list(appear),
            "explode": _r(explode, 3), "dim": dim, "ghost": ghost}


def ink(points: np.ndarray, *, mesh_theta0: float, ang=None, at=None, anchor=None, flip=False,
        color: str = "#fff2c8", width: float = 0.06, appear=(0.0, 0.05), drawn_x: float | None = None,
        shift=None) -> dict:
    """A line drawn on the end face, moved by the same map as the wood under it."""
    x = C["drawn_x"] if drawn_x is None else drawn_x
    er, et = green_to_target()
    g = np.asarray(points, float)
    d = free_shrink(g, er * x, et * x, mesh_theta0, ang)
    if shift is not None:
        d = d + shift
    anchor = np.zeros(2) if anchor is None else anchor
    place = (0.0, 0.0) if at is None else at
    return {"g": _r(_place(g, place, flip, anchor)), "d": _r(_place(d, place, flip, anchor)),
            "color": color, "width": width, "appear": list(appear)}


def _dry_shift(mesh: Mesh, x: float | None = None) -> np.ndarray:
    """The rigid shift :func:`piece` applies, so ink drawn on a piece stays on it."""
    x = C["drawn_x"] if x is None else x
    er, et = green_to_target()
    d = free_shrink(mesh.xy, er * x, et * x, mesh.theta0, mesh.ang)
    return mesh.xy.mean(axis=0) - d.mean(axis=0)


def _fmt(v: float, nd: int = 3) -> str:
    return f"{v:.{nd}f}"


def _pct(v: float, nd: int = 1) -> str:
    return f"{100 * v:.{nd}f}%"


DRY = (0.42, 0.78)     # when, in a chapter's progress, the wood dries on screen


def _ring_ink(r_in: float, theta0: float, a0: float, a1: float, n: int = 90, **kw) -> dict:
    a = np.linspace(a0, a1, n)
    pts = np.stack([r_in * np.cos(a), r_in * np.sin(a)], axis=1)
    return ink(pts, mesh_theta0=theta0, ang=a, **kw)


def scenes() -> dict:
    """Every chapter's picture, declared: what is on the end face, when it appears, when it
    dries, and the true figures written beside it."""
    F = facts()
    R = F.log_in / 2
    boards = stud_boards()
    out: dict[str, dict] = {}
    wedge_up = 90.0                                  # a wedge drawn point-down, bark up

    def wedge_piece(bis=wedge_up, at=None, label="", appear=(0.0, 0.04), explode=(0, 0), dim=False, ghost=False):
        """A wedge placed by its point (``at`` is where the point goes)."""
        point = wedge_corners(bis)[0]
        return piece(sector_mesh(bis), at=at, bark=R, tone="wedge", label=label, appear=appear,
                     explode=explode, dim=dim, ghost=ghost, anchor=point if at is not None else None)

    def board_piece(i, at=None, label="", appear=(0.0, 0.04), flip=False, explode=(0, 0), dim=False, ghost=False,
                    bark_up=False):
        """A stud placed by its centre. ``bark_up`` turns a board from below the pith over, so its
        heart side is down (the way a cup is usually drawn); a mirror image, so the same board."""
        b = boards[i]
        flip = flip or (bark_up and b.centre[1] < 0)
        return piece(rect_mesh(b, slit=b.holds_pith), at=at, flip=flip, label=label, appear=appear,
                     explode=explode, dim=dim, recentre=not b.holds_pith, ghost=ghost,
                     anchor=b.centre if at is not None else None)

    def tag(text, at, color="#fff7e8", size=0.24, appear=(0.0, 0.05)):
        return {"text": text, "at": _r(at, 3), "color": color, "size": size, "appear": list(appear)}

    cup, calm = F.boards[F.cup_board], F.boards[F.calm_board]
    w0 = F.wedges[0]

    # 1. the hook: a flatsawn stud and a wedge, the same log, drying side by side
    out["hook"] = {
        "U": 0.42, "dry": [0.18, 0.62], "dir": [0.16, -1.0, 0.22],
        "pieces": [board_piece(F.cup_board, at=(-4.4, 0.5), label="store 2x4", ghost=True, bark_up=True),
                   wedge_piece(at=(3.6, -0.25), label="wedge", ghost=True)],
        "labels": [tag("a store 2x4", (-4.4, -1.3), appear=(0.05, 0.12)),
                   tag("a wedge", (3.6, -1.3), appear=(0.05, 0.12)),
                   tag(f"cups {_fmt(abs(cup.cup_in))} in", (-4.4, 2.4), "#ff8a6a", appear=(0.66, 0.74)),
                   tag("sawn faces stay flat", (3.6, 6.2), "#9fe0a0", appear=(0.66, 0.74))],
        "lines": [],
    }

    # 2. the three directions, on the log end
    disc = disc_mesh(R)
    arrows = [
        {"from": _r((R * 0.62, 0.0), 3), "to": _r((R * 0.62, R * 0.38), 3), "color": "#ffb04a",
         "label": f"round the rings  {_pct(wc.C['shrink_tangential'])}", "appear": [0.25, 0.32]},
        {"from": _r((R * 0.30, -R * 0.30), 3), "to": _r((R * 0.62, -R * 0.62), 3), "color": "#5ec8f2",
         "label": f"across the rings  {_pct(wc.C['shrink_radial'])}", "appear": [0.45, 0.52]},
        {"from": _r((-R * 0.45, R * 0.15), 3), "out": 2.2, "color": "#c9c1b2",
         "label": "along the grain: almost none", "appear": [0.65, 0.72]},
    ]
    out["numbers"] = {"U": 0.36, "dry": None, "dir": [0.30, -1.0, 0.24],
                      "pieces": [piece(disc, bark=R, tone="log", dry=False, recentre=False)],
                      "arrows": arrows, "labels": [], "lines": []}

    # 3. the rule: radii stay straight, rings stay round, other lines bend, the circle cannot close
    disc = disc_mesh(R, slit_deg=90.0)
    lines = []
    for a in (-30.0, 30.0, 150.0, 210.0, 270.0):
        rad = math.radians(a)
        pts = _line((0.0, 0.0), (R * 0.96 * math.cos(rad), R * 0.96 * math.sin(rad)), 40)
        lines.append(ink(pts, mesh_theta0=disc.theta0, color="#9fe0a0", appear=(0.12, 0.2)))
    for rr in (R * 0.45, R * 0.8):
        lines.append(_ring_ink(rr, disc.theta0, disc.theta0 - math.pi + 0.002, disc.theta0 + math.pi - 0.002, 160,
                               color="#5ec8f2", appear=(0.2, 0.28)))
    for y in (-R * 0.55,):
        half = math.sqrt(R * R - y * y) * 0.92
        lines.append(ink(_line((-half, y), (half, y), 60), mesh_theta0=disc.theta0, color="#ff8a6a", width=0.08,
                         appear=(0.28, 0.36)))
    lines.append(ink(_line((R * 0.25, -R * 0.15), (R * 0.25, R * 0.75), 60), mesh_theta0=disc.theta0,
                     color="#ff8a6a", width=0.08, appear=(0.28, 0.36)))
    out["rule"] = {"U": 0.36, "dry": list(DRY), "dir": [0.10, -1.0, 0.16],
                   "pieces": [piece(disc, bark=R, tone="log", recentre=False)], "lines": lines,
                   "labels": [tag("a radius stays straight", (-R * 1.05, -R * 0.75), "#9fe0a0", appear=(0.80, 0.86)),
                              tag("a ring stays round", (-R * 1.05, R * 0.55), "#5ec8f2", appear=(0.84, 0.90)),
                              tag("any other line bends", (R * 1.05, -R * 0.9), "#ff8a6a", appear=(0.88, 0.94)),
                              tag(f"the ring comes up {F.check_deg:.1f} deg short", (0.0, R * 1.22), "#ffd27a",
                                  appear=(0.74, 0.80))]}

    # 4. sawing: the log, then fifteen studs, pulled apart, then dried
    ghost = piece(disc_mesh(R), bark=R, tone="log", dry=False, recentre=False, appear=(0.0, 0.03))
    ghost["vanish"] = [0.30, 0.38]
    studs = []
    for i, b in enumerate(boards):
        c = b.centre
        studs.append(board_piece(i, appear=(0.28, 0.34), explode=tuple(c * 0.18)))
    lab = []
    kinds = F.counts()
    colour = {"flatsawn": "#ff8a6a", "rift": "#ffd27a", "quartersawn": "#5ec8f2", "boxed heart": "#ff5a5a"}
    for i, b in enumerate(boards):
        lab.append(tag({"flatsawn": "F", "rift": "R", "quartersawn": "Q", "boxed heart": "H"}[F.boards[i].kind],
                       b.centre * 1.18 + np.array([0.0, 0.0]), colour[F.boards[i].kind], 0.22, (0.5, 0.56)))
    out["sawing"] = {"U": 0.34, "dry": [0.78, 0.97], "explodeAt": [0.38, 0.5], "dir": [0.10, -1.0, 0.16],
                     "pieces": [ghost] + studs, "labels": lab, "lines": []}

    # 5. the cup: two flatsawn studs, nearer and farther from the heart
    pa = board_piece(F.cup_board, at=(0.0, 2.6), ghost=True, bark_up=True)
    pb = board_piece(F.calm_board, at=(0.0, -1.2), ghost=True, bark_up=True)
    out["cup"] = {"U": 0.6, "dry": list(DRY), "dir": [0.08, -1.0, 0.14],
                  "pieces": [pa, pb], "lines": [],
                  "labels": [tag(f"{_fmt(_dist(boards[F.cup_board]))} in from the heart: cups {_fmt(abs(cup.cup_in))} in",
                                 (0.0, 4.6), "#ff8a6a", appear=(0.8, 0.86)),
                             tag(f"{_fmt(_dist(boards[F.calm_board]))} in from the heart: cups {_fmt(abs(calm.cup_in))} in",
                                 (0.0, -2.9), "#ffd27a", appear=(0.84, 0.9))]}

    # 6. the diamond: the stud whose corners leave square the most, beside the quartersawn one
    dm, qm = F.boards[F.diamond_board], F.boards[F.quarter_board]
    out["diamond"] = {"U": 0.75, "dry": list(DRY), "dir": [0.06, -1.0, 0.12],
                      "pieces": [board_piece(F.diamond_board, at=(-2.4, 0.6), ghost=True),
                                 board_piece(F.quarter_board, at=(2.4, 0.6), ghost=True)],
                      "lines": [],
                      "labels": [tag(f"rings at {dm.ring_angle_deg:.0f} deg: corners {dm.diamond_deg:.2f} deg off square",
                                     (-2.4, 2.9), "#ffd27a", appear=(0.8, 0.86)),
                                 tag(f"rings at {qm.ring_angle_deg:.0f} deg: corners {qm.diamond_deg:.2f} deg off",
                                     (2.4, -1.7), "#5ec8f2", appear=(0.84, 0.9))]}

    # 7. the boxed heart: the stud that holds the pith checks
    hm = F.boards[F.heart_board]
    hb = boards[F.heart_board]
    out["check"] = {"U": 0.75, "dry": list(DRY), "dir": [0.08, -1.0, 0.14],
                    "pieces": [board_piece(F.heart_board, at=(0.0, 0.4), ghost=True)],
                    "lines": [],
                    "labels": [tag(f"opens {hm.check_deg:.1f} deg: {_fmt(hm.check_gap_in)} in at the face",
                                   (0.0, 2.3), "#ff5a5a", appear=(0.8, 0.86)),
                               tag("pith inside", (0.0, -1.4), "#ffd27a", appear=(0.12, 0.2))]}

    # 8. the pile: every stud, turned this way and that, as they come on the cart
    pile = []
    cols = 4
    order = sorted(range(len(boards)), key=lambda i: (i * 7) % len(boards))
    for n, i in enumerate(order):
        row, col = divmod(n, cols)
        at = ((col - (cols - 1) / 2) * 4.3, (1.5 - row) * 2.6)
        pile.append(board_piece(i, at=at, flip=bool((n * 3) % 2), appear=(0.02 + 0.015 * n, 0.06 + 0.015 * n)))
    out["pile"] = {"U": 0.36, "dry": [0.36, 0.72], "dir": [0.12, -1.0, 0.24],
                   "pieces": pile, "lines": [],
                   "labels": [tag(f"width lost: {min(m.width_loss_pct for m in F.boards):.1f} to "
                                  f"{max(m.width_loss_pct for m in F.boards):.1f}%", (0.0, 6.0), "#ffd27a",
                                  appear=(0.76, 0.82))]}

    # 9. the wedge: faces on the radii, bark on a ring
    wm = sector_mesh(wedge_up)
    s = wedge_section()
    half = math.pi / splits()
    sh = _dry_shift(wm)
    wl = []
    for j in (0.25, 0.5, 0.75):
        rr = s.point_setback_in + (R - s.point_setback_in) * j
        beta = half - math.asin(min(1.0, s.point_setback_in * math.sin(half) / rr))
        a = np.linspace(math.radians(wedge_up) - beta, math.radians(wedge_up) + beta, 30)
        wl.append(ink(np.stack([rr * np.cos(a), rr * np.sin(a)], 1), mesh_theta0=wm.theta0, ang=a,
                      color="#5ec8f2", width=0.05, appear=(0.2, 0.28), shift=sh))
    out["wedge"] = {"U": 0.7, "dry": list(DRY), "dir": [0.10, -1.0, 0.16], "lift": 0.4,
                    "pieces": [piece(wm, bark=R, tone="wedge", ghost=True)], "lines": wl,
                    "labels": [tag(f"{w0.angle_green_deg:.0f} deg closes {F.sector.close_deg:.2f} deg", (0.0, R + 0.9),
                                   "#ffd27a", appear=(0.8, 0.86)),
                               tag(f"sawn faces bend {abs(w0.face_bow_in):.4f} in", (-3.0, 2.0), "#9fe0a0", appear=(0.84, 0.9)),
                               tag("bark face stays round", (3.0, 2.0), "#5ec8f2", appear=(0.88, 0.94))]}

    # 10. eight wedges, one answer: the whole log split, and dried
    ws = []
    for i in range(splits()):
        bis = 90.0 + i * 360.0 / splits()
        c = np.array([math.cos(math.radians(bis)), math.sin(math.radians(bis))])
        ws.append(piece(sector_mesh(bis), bark=R, tone="wedge", explode=tuple(c * 1.6), appear=(0.0, 0.03)))
    out["eight"] = {"U": 0.34, "dry": [0.42, 0.74], "explodeAt": [0.12, 0.3], "dir": [0.10, -1.0, 0.18],
                    "pieces": ws, "lines": [],
                    "labels": [tag(f"all {splits()} close {F.sector.close_deg:.2f} deg", (0.0, R + 2.6), "#9fe0a0",
                                   appear=(0.78, 0.84))]}

    # 11. dry first, key last: two members at a seam, the V between their sawn faces, a key in it.
    # Each wedge leans out by half the fold so its facing face meets the other's at the ridge
    # (the V is wood_care's: the sector angle less the fold), and the ridge is held as they dry.
    v = F.sector.gap_green_deg
    lean = 180.0 / splits() - v / 2
    ridge_at = np.array([0.0, R])
    pair, faces = [], []
    for side, bis in ((-1, 90.0 + lean), (1, 90.0 - lean)):
        point, e_cw, e_ccw = wedge_corners(bis)
        ridge = e_cw if side < 0 else e_ccw                 # the face that looks into the seam
        pair.append(piece(sector_mesh(bis), bark=R, tone="wedge", at=ridge_at, anchor=ridge, pin=ridge, ghost=True))
        faces.append(point - ridge)
    reach = 0.9
    key = np.array([ridge_at, ridge_at + faces[0] * reach, ridge_at + faces[1] * reach])
    keyp = piece(Mesh(key, np.array([[0, 1, 2]]), np.zeros(3), 0.0), tone="key", dry=False,
                 appear=(0.14, 0.2))
    keyp["back"] = 0.01               # just behind the wood, so the faces are seen to swing in over it
    pair.append(keyp)
    out["keys"] = {"U": 0.6, "dry": list(DRY), "dir": [0.10, -1.0, 0.18],
                   "pieces": pair, "lines": [],
                   "labels": [tag(f"V {v:.2f} deg, cut green", (0.0, R + 0.8), "#c9c1b2", appear=(0.18, 0.24)),
                              tag("key", (0.0, R - 2.6), "#e8e0cf", 0.2, appear=(0.2, 0.26)),
                              tag(f"closes to {F.sector.gap_dry_deg:.2f} deg dry", (0.0, R + 1.6), "#ffd27a",
                                  appear=(0.8, 0.86)),
                              tag(f"each face swings in {F.sector.face_tilt_in:.3f} in: the key is too wide",
                                  (0.0, R - 6.4), "#ff8a6a", appear=(0.84, 0.9))]}

    # 12. what it still does: the wedge and the stud, both dried, side by side
    out["limits"] = {"U": 0.42, "dry": [0.1, 0.4], "dir": [0.16, -1.0, 0.22],
                     "pieces": [board_piece(F.cup_board, at=(-4.4, 0.5), ghost=True, bark_up=True),
                                wedge_piece(at=(3.6, -0.25), ghost=True)],
                     "labels": [tag(f"depth {_fmt(w0.depth_green_in, 2)} -> {_fmt(w0.depth_dry_in, 2)} in", (3.6, -1.4),
                                    "#ffd27a", appear=(0.3, 0.38)),
                                tag("it still shrinks", (3.6, 6.4), "#ffd27a", appear=(0.4, 0.48))],
                     "lines": []}
    return out


def _dist(b: Board) -> float:
    """How far a board's nearest face is from the pith."""
    return float(min(abs(b.y0), abs(b.y0 + b.t)) if (b.y0 > 0 or b.y0 + b.t < 0) else 0.0)


# ----------------------------------------------------------------------
# The sheets: every figure the film puts on screen
# ----------------------------------------------------------------------

def equations() -> dict[str, list[str]]:
    """Every chapter's sheet: five lines at most, short enough for the phone cut."""
    F = facts()
    w = F.wedges[0]
    cup, calm = F.boards[F.cup_board], F.boards[F.calm_board]
    dm, qm, hm = F.boards[F.diamond_board], F.boards[F.quarter_board], F.boards[F.heart_board]
    kinds = F.counts()
    after_worst = max(abs(m.cup_in) for m in F.after)
    fsp, mc = wc.C["fibre_saturation"], scl.C["mc_target"]
    fold = seam_fold_deg()
    pc = lambda v: f"{v * 100:.0f}"
    widths = [m.width_loss_pct for m in F.boards]
    return {
        "hook": [f"same log, green to {pc(mc)}% moisture",
                 f"store 2x4: cups {_fmt(abs(cup.cup_in))} in",
                 f"wedge: sawn faces bend {abs(w.face_bow_in):.4f} in",
                 "both shrink; one changes shape"],
        "numbers": [f"round the rings {_pct(wc.C['shrink_tangential'])}   across {_pct(wc.C['shrink_radial'])}",
                    f"along the grain {_pct(C['shrink_long_lo'])} to {_pct(C['shrink_long_hi'])}",
                    f"none above {pc(fsp)}%; stamped S-DRY at {pc(C['sdry_mc'])}%",
                    f"dried to {pc(mc)}%: ({pc(fsp)} - {pc(mc)}) / {pc(fsp)} = {wc.shrinkage_fraction(mc):.2f} of it",
                    f"e_T = {_pct(F.et, 2)}   e_R = {_pct(F.er, 2)}   (drawn {C['drawn_x']:g}x)"],
        "rule": ["r' = r (1 - e_R)",
                 "theta' = theta (1 - e_T) / (1 - e_R)",
                 f"k = {1 - F.et:.4f} / {1 - F.er:.4f} = {F.k:.5f}",
                 f"full ring: 360 (1 - k) = {F.check_deg:.2f} deg short"],
        "sawing": [f"{F.log_in:.0f} in log, {_kerf(MILL_KERF):.3f} in mill kerf",
                   f"{len(F.boards)} studs, {C['stud_t_in']:g} x {C['stud_w_in']:g} in",
                   f"flatsawn {kinds.get('flatsawn', 0)}   quartersawn {kinds.get('quartersawn', 0)}",
                   f"rift {kinds.get('rift', 0)}   boxed heart {kinds.get('boxed heart', 0)}",
                   "one grade stamp for all of them"],
        "cup": [f"{_fmt(_dist(cup.board))} in from the heart: cup {_fmt(abs(cup.cup_in))} in",
                f"{_fmt(_dist(calm.board))} in from the heart: cup {_fmt(abs(calm.cup_in))} in",
                f"width lost: {cup.width_loss_pct:.1f}% and {calm.width_loss_pct:.1f}%",
                f"a 2x10 from the same spot: {_fmt(abs(F.joist.cup_in))} in",
                "edges curl away from the heart"],
        "diamond": [f"rings at {dm.ring_angle_deg:.0f} deg: {dm.diamond_deg:.2f} deg off square",
                    f"rings at {qm.ring_angle_deg:.0f} deg: {qm.diamond_deg:.2f} deg off square",
                    f"width lost at {qm.ring_angle_deg:.0f} deg: {qm.width_loss_pct:.1f}%  (across)",
                    f"flatsawn: {cup.width_loss_pct:.1f}%  (round the rings)"],
        "check": [f"k = {F.k:.5f}: every ring must shorten",
                  "a closed ring cannot; it tears on a radius",
                  f"V = 360 (1 - k) = {hm.check_deg:.2f} deg",
                  f"{_fmt(_dist(hm.board) or hm.board.t / 2)} in out, at the face: {_fmt(hm.check_gap_in)} in"]
                 + ([f"a 4x4 from this log holds the pith too"] if F.post_heart else []),
        "pile": [f"{len(F.boards)} studs, green to {pc(mc)}%",
                 f"width lost: {min(widths):.1f} to {max(widths):.1f}%",
                 f"cup 0 to {max(abs(m.cup_in) for m in F.boards):.3f} in; lean 0 to {max(m.diamond_deg for m in F.boards):.2f} deg",
                 f"sold at S-DRY {pc(C['sdry_mc'])}%: {F.share_still_to_come * 100:.0f}% still to come",
                 f"after you buy it: up to {after_worst:.3f} in more cup"],
        "wedge": [f"{w.angle_green_deg:.0f} -> {F.sector.sector_dry_deg:.2f} deg: closes {F.sector.close_deg:.2f}",
                  f"sawn faces bend {abs(w.face_bow_in):.4f} in",
                  f"  (half a {_kerf(WEDGE_KERF):.3f} in kerf off the radius)",
                  f"bark face stays round: {w.bark_roundness_in:.5f} in",
                  f"depth {w.depth_green_in:.2f} -> {w.depth_dry_in:.2f} in"],
        "eight": [f"{splits()} wedges, one map",
                  f"each closes {min(x.close_deg for x in F.wedges):.2f} deg",
                  f"spread across the {splits()}: {spread(x.close_deg for x in F.wedges):.6f} deg",
                  f"spread across {len(F.boards)} studs: {spread(widths):.2f} points",
                  "  of width, before cup and checks"],
        "keys": [f"V = sector - fold = {w.angle_green_deg:.0f} - {fold:.2f} = {F.sector.gap_green_deg:.2f}",
                 f"dry: {F.sector.sector_dry_deg:.2f} - {fold:.2f} = {F.sector.gap_dry_deg:.2f} deg",
                 f"each face swings in {F.sector.face_tilt_in:.3f} in, room side",
                 "a key cut green is too wide there",
                 "so: dry the frame, then make the keys"],
        "limits": [f"still shrinks {_pct(F.et)} round, {_pct(F.er)} across",
                   f"{F.sector.thick_in:.2f} in thick: dries {F.sector.times_slower_than_board:.1f}x slower than a 2x",
                   "modelled: a round log, centred rings",
                   "not modelled: knots, reaction wood",
                   "not measured: bow along the length"],
    }


SHEET_TITLES = {
    "numbers": "DECLARED: HANDBOOK VALUES",
    "keys": "A CORRECTION, THEN THE RULE",
    "limits": "WHAT IT STILL DOES",
}


def web_stage() -> dict:
    """The stage data the browser draws the film from."""
    sc = scenes()
    note = f"movement drawn {C['drawn_x']:g}x life size; every number true size"
    return {"sections": sc, "drawnX": C["drawn_x"],
            "notes": {k: note for k, v in sc.items() if v.get("dry")}}


# ----------------------------------------------------------------------
# Report and checks
# ----------------------------------------------------------------------

def report() -> str:
    F = facts()
    out = ["WHICH WAY THE RINGS RUN", "",
           f"green to {scl.C['mc_target'] * 100:.0f}%: e_R {F.er * 100:.2f}%, e_T {F.et * 100:.2f}%, k {F.k:.5f}, "
           f"a closed ring short by {F.check_deg:.2f} deg",
           f"after S-DRY: e_R {F.er_after * 100:.2f}%, e_T {F.et_after * 100:.2f}%  "
           f"({F.share_still_to_come * 100:.0f}% still to come)", "",
           f"{len(F.boards)} studs from the {F.log_in:.0f} in log:"]
    for i, m in enumerate(F.boards):
        b = m.board
        out.append(f"  {i:2d} at ({b.centre[0]:+6.2f},{b.centre[1]:+6.2f})  {m.kind:<12} rings {m.ring_angle_deg:5.1f} deg  "
                   f"width -{m.width_loss_pct:4.2f}%  thick -{m.thick_loss_pct:4.2f}%  cup {m.cup_in:+.4f} in  "
                   f"corners {m.diamond_deg:.3f} deg" + (f"  CHECK {m.check_deg:.2f} deg / {m.check_gap_in:.3f} in" if m.check_deg else ""))
    w = F.wedges[0]
    out += ["", f"wedge: {w.angle_green_deg:.1f} -> {w.angle_dry_deg:.3f} deg (wood_care: {F.sector.close_deg:.4f} close); "
                f"faces bend {w.face_bow_in:+.5f} in; bark round to {w.bark_roundness_in:.6f} in; "
                f"depth {w.depth_green_in:.3f} -> {w.depth_dry_in:.3f} in",
            f"eight wedges: close spread {spread(x.close_deg for x in F.wedges):.2e} deg"]
    return "\n".join(out)


def validate_grain_shrink() -> None:
    F = facts()
    er, et = F.er, F.et
    # The map is right: radial and tangential strain where they belong.
    p = np.array([[3.0, 0.0], [3.0001, 0.0], [3.0, 0.0001]])
    q = free_shrink(p, er, et, 0.0)
    assert abs(np.linalg.norm(q[1] - q[0]) / 1e-4 - (1 - er)) < 1e-6
    assert abs(np.linalg.norm(q[2] - q[0]) / 1e-4 - (1 - et)) < 1e-4
    # Radii stay straight, rings stay round, other lines bend.
    assert abs(face_bow((0.5, 0.5), (4.0, 4.0), er, et, math.pi / 4)) < 1e-9
    assert abs(face_bow((-2.0, 3.0), (2.0, 3.0), er, et, math.pi / 2)) > 1e-3
    # The wedge's sector closes by exactly wood_care's figure: one number, one function.
    k = ring_closure(er, et)
    assert abs(360.0 / splits() * (1 - k) - F.sector.close_deg) < 1e-9
    # ... and the kerfed wedge, whose faces sit half a kerf off the radii, nearly so.
    w = F.wedges[0]
    assert abs(w.close_deg - F.sector.close_deg) < 0.01, (w.close_deg, F.sector.close_deg)
    assert abs(w.face_bow_in) < 0.005 and w.bark_roundness_in < 1e-9
    # The seam's V is the sector less the fold, so it closes as the sector does (wood_care, corrected).
    assert F.sector.gap_dry_deg < F.sector.gap_green_deg
    assert abs(F.sector.gap_dry_deg - (F.sector.sector_dry_deg - seam_fold_deg())) < 1e-9
    k_scene = scenes()["keys"]["pieces"]
    for pc in k_scene[:2]:                        # the drawn wedges swing in over the key, not away
        g, d = np.array(pc["g"]).reshape(-1, 2), np.array(pc["d"]).reshape(-1, 2)
        low = int(np.argmin(g[:, 1]))             # each wedge's point, at the room side
        assert abs(d[low, 0]) < abs(g[low, 0]), "the V should close as the wedges dry"
    # Every wedge moves the same; the studs do not.
    assert spread(x.close_deg for x in F.wedges) < 1e-9
    assert spread(abs(x.face_bow_in) for x in F.wedges) < 1e-12
    assert spread(m.width_loss_pct for m in F.boards) > 0.5
    # The log gives every kind of board, and one of them holds the pith.
    kinds = F.counts()
    assert kinds.get("flatsawn", 0) >= 2 and kinds.get("quartersawn", 0) >= 2 and kinds.get("boxed heart", 0) == 1
    # Flatsawn loses more width than quartersawn (round the rings, against across them).
    assert F.boards[F.cup_board].width_loss_pct > F.boards[F.quarter_board].width_loss_pct
    # The board nearer the heart cups more, and its edges go away from the heart.
    assert abs(F.boards[F.cup_board].cup_in) > abs(F.boards[F.calm_board].cup_in) > 0
    # The check: a closed ring comes up short, and the boxed heart's V is that.
    assert 0 < F.check_deg < 20 and F.boards[F.heart_board].check_gap_in > 0
    # Drying after the store is real, and less than drying from green.
    assert 0 < F.share_still_to_come < 1 and F.after[F.cup_board].cup_in != 0
    # Meshes: the outline closes, the slit opens.
    for m in (rect_mesh(stud_boards()[F.heart_board], slit=True), sector_mesh(90.0), disc_mesh(3.0)):
        loop = boundary_loop(m.tri)
        assert len(loop) > 8 and len(set(loop)) == len(loop)
    d = disc_mesh(3.0)
    dd = free_shrink(d.xy, er, et, d.theta0, d.ang)
    rim = 1 + (30 - 1) * 121
    assert np.linalg.norm(dd[rim] - dd[rim + 120]) > 0.1 * 3.0 * math.radians(F.check_deg) * (1 - er)
    sc = scenes()
    assert set(sc) == set(equations()), (set(sc) ^ set(equations()))


if __name__ == "__main__":
    validate_grain_shrink()
    print(report())
