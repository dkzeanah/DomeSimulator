"""The sky web, drawn in the Cabin World.

Four anchor trees round the pad, the X of wire rope between them, the spiral
woven onto it, the winch and its line, the hook at the centre, and the
solver's own dome taken apart into its forty panels -- each one the
simulator's member meshes for that face (as :func:`wedge_book.cover_scene.dome_batch`
assigns them), moved as a rigid body: stacked flat on the deck, hoisted flat in
its harness, swung out and turned into place, hung on three pigtails. The
arithmetic is :mod:`two_v_demo.sky_web`'s; heights here are that module's.

Ropes are drawn thicker than they are, or a half-inch rope would be thinner
than a pixel at the distances the film is shot from: :data:`ROPE_DRAWN`.
"""

from __future__ import annotations

import math
from functools import lru_cache

import numpy as np

from wedge_book import cover_scene as cvs

from . import sky_web as sw
from .render_kit import TriangleBatch

BASE = cvs.DECK_TOP + 0.02
"""The world dome's rim (its sphere's centre), metres above the grass."""

ROPE_DRAWN = 5.0
"""Ropes and cords are drawn this many times their real thickness."""

WIRE = (0.62, 0.64, 0.66, 1.0)
WIRE_DARK = (0.40, 0.42, 0.44, 1.0)
SPIRAL = (0.82, 0.80, 0.72, 1.0)
CORD = (1.00, 0.52, 0.16, 1.0)
HARNESS = (1.00, 0.86, 0.20, 1.0)
GUY = (0.55, 0.56, 0.50, 1.0)
STEEL = (0.30, 0.32, 0.35, 1.0)
WINCH = (0.85, 0.22, 0.14, 1.0)
STRAP = (0.20, 0.45, 0.85, 1.0)
CANOPY = (0.12, 0.24, 0.12, 1.0)
BARK = (0.30, 0.19, 0.12, 1.0)

TREE_H = 18.0
STACKS = 7
STACK_R = 2.55


def ground(x: float, y: float) -> float:
    r2 = x * x + y * y
    return -0.018 * r2 if r2 > 81 else 0.0


# ----------------------------------------------------------------------
# The panels
# ----------------------------------------------------------------------

@lru_cache(maxsize=1)
def panels() -> list[dict]:
    """The solver's dome as forty rigid panels, in world metres, standing on the pad."""
    s = cvs.sizes()
    model = cvs.cover_model()
    batch, _info = cvs.dome_batch(s, ())
    tri = np.asarray(batch.vertices, dtype=np.float64).reshape(-1, 3, 10)
    topo = model.topology
    scale = s.dome_r / topo.sphere_radius_in
    v = np.asarray(topo.vertices, dtype=float) * scale + np.array([0.0, 0.0, BASE])
    centres = tri[:, :, 0:3].mean(axis=1) - np.array([0.0, 0.0, BASE])
    face_dirs = np.array([f.center / np.linalg.norm(f.center) for f in topo.faces])
    dirs = centres / np.maximum(np.linalg.norm(centres, axis=1, keepdims=True), 1e-9)
    owner = np.argmax(dirs @ face_dirs.T, axis=1)
    out = []
    for i, f in enumerate(topo.faces):
        corners = np.array([v[k] for k in f.vertices])
        lengths = np.array([np.linalg.norm(corners[(k + 1) % 3] - corners[k]) for k in range(3)])
        mids = np.array([(corners[k] + corners[(k + 1) % 3]) / 2 for k in range(3)])
        balance = (mids * lengths[:, None]).sum(axis=0) / lengths.sum()
        n = np.cross(corners[1] - corners[0], corners[2] - corners[0])
        n /= np.linalg.norm(n)
        if np.dot(n, balance - np.array([0.0, 0.0, BASE])) < 0:
            n = -n
        mesh = tri[owner == i].copy()
        # The panel's thickness along its own normal, for stacking it flat.
        d = (mesh[:, :, 0:3].reshape(-1, 3) - balance) @ n
        out.append({"corners": corners, "balance": balance, "normal": n, "mesh": mesh,
                    "below": float(-d.min()), "thick": float(d.max() - d.min())})
    return out


def rotation(axis, angle: float) -> np.ndarray:
    axis = np.asarray(axis, dtype=float)
    norm = np.linalg.norm(axis)
    if norm < 1e-12 or abs(angle) < 1e-12:
        return np.eye(3)
    k = axis / norm
    K = np.array([[0, -k[2], k[1]], [k[2], 0, -k[0]], [-k[1], k[0], 0]])
    return np.eye(3) + math.sin(angle) * K + (1 - math.cos(angle)) * K @ K


def to_flat(i: int, s: float = 1.0) -> np.ndarray:
    """The rotation that lays panel ``i`` flat, outer face up -- ``s`` of the way."""
    n = panels()[i]["normal"]
    angle = math.acos(float(np.clip(n[2], -1.0, 1.0)))
    return rotation(np.cross(n, [0.0, 0.0, 1.0]), angle * s)


def lift_z(level: int = 1) -> float:
    """How far the standing dome is raised to hang from web ``level``."""
    h = sw.hang(sw.C["anchor1_m"] if level == 1 else sw.C["anchor2_m"])
    return h["rim_m"] - BASE


def hung_balance(i: int, level: int = 1, gap: float = 0.0) -> np.ndarray:
    p = panels()[i]
    return p["balance"] + np.array([0.0, 0.0, lift_z(level)]) + p["normal"] * gap


def place(i: int, R: np.ndarray, at: np.ndarray) -> np.ndarray:
    """Panel ``i``'s mesh turned by ``R`` about its balance point, which goes to ``at``."""
    p = panels()[i]
    m = p["mesh"].copy()
    pos = m[:, :, 0:3].reshape(-1, 3)
    m[:, :, 0:3] = ((pos - p["balance"]) @ R.T + at).reshape(m.shape[0], 3, 3)
    m[:, :, 3:6] = (m[:, :, 3:6].reshape(-1, 3) @ R.T).reshape(m.shape[0], 3, 3)
    return m


def corners_at(i: int, R: np.ndarray, at: np.ndarray) -> np.ndarray:
    p = panels()[i]
    return (p["corners"] - p["balance"]) @ R.T + at


def emit(batch: TriangleBatch, mesh: np.ndarray) -> None:
    """Both windings, so the culled opaque batch shows every side."""
    flip = mesh[:, ::-1, :].copy()
    flip[:, :, 3:6] *= -1
    batch.vertices.extend(np.concatenate([mesh, flip]).reshape(-1).astype(np.float32).tolist())


# ----------------------------------------------------------------------
# Trees, ropes, the web
# ----------------------------------------------------------------------

def trees() -> list[np.ndarray]:
    return [np.array([x, y, ground(x, y)]) for x, y in sw.tree_xy()]


def tie(k: int, level: int = 1) -> np.ndarray:
    """Where web ``level``'s rope is tied on tree ``k``: on the trunk's inner face."""
    t = trees()[k]
    inward = -np.array([t[0], t[1], 0.0]) / math.hypot(t[0], t[1])
    r = sw.C["tree_dbh_m"] / 2 * 0.8
    z = sw.C["anchor1_m"] if level == 1 else sw.C["anchor2_m"]
    return np.array([t[0], t[1], z]) + inward * r


_PENDING: dict | None = None
"""While :func:`batched` is open, ropes are collected here and drawn together."""


def tube(batch: TriangleBatch, points, radius: float, colour, sides: int = 6) -> None:
    """A rope along ``points``: every segment a ring-to-ring sleeve (the same
    winding as :meth:`TriangleBatch.cylinder`), run a radius past both ends so
    the joints close without spheres. Ropes are drawn every frame while they
    grow, so this is vectorised, and inside :func:`batched` many ropes share
    one call."""
    pts = np.asarray([np.asarray(p, dtype=float) for p in points], dtype=float)
    if len(pts) < 2:
        return
    if _PENDING is not None and batch is _PENDING["target"]:
        key = (float(radius), tuple(float(c) for c in colour), int(sides))
        _PENDING["ropes"].setdefault(key, []).append((pts[:-1], pts[1:]))
        return
    _sleeves(batch, pts[:-1], pts[1:], radius, colour, sides)


class batched:
    """Collect every rope drawn into ``target`` inside the block and draw each
    kind at once on the way out. Ropes for any other batch -- a cached layer
    being built -- are drawn straight away, since that batch is uploaded the
    moment its builder returns."""

    def __init__(self, target: TriangleBatch):
        self.target = target

    def __enter__(self):
        global _PENDING
        self.outer = _PENDING
        _PENDING = {"target": self.target, "ropes": {}}
        return self

    def __exit__(self, *exc):
        global _PENDING
        pending, _PENDING = _PENDING, self.outer
        for (radius, colour, sides), parts in pending["ropes"].items():
            _sleeves(self.target, np.concatenate([a for a, _b in parts]),
                     np.concatenate([b for _a, b in parts]), radius, colour, sides)
        return False


def _sleeves(batch: TriangleBatch, a, b, radius: float, colour, sides: int) -> None:
    d = b - a
    length = np.linalg.norm(d, axis=1)
    keep = length > 1e-6
    if not np.any(keep):
        return
    a, b, d, length = a[keep], b[keep], d[keep], length[keep]
    u = d / length[:, None]
    a = a - u * radius
    b = b + u * radius
    trial = np.where(np.abs(u[:, 2:3]) > 0.88, [[0.0, 1.0, 0.0]], [[0.0, 0.0, 1.0]])
    t = np.cross(u, trial)
    t /= np.linalg.norm(t, axis=1, keepdims=True)
    bt = np.cross(u, t)
    ang = np.arange(sides) * (math.tau / sides)
    n = (t[:, None, :] * np.cos(ang)[None, :, None] + bt[:, None, :] * np.sin(ang)[None, :, None])
    n1 = np.roll(n, -1, axis=1)
    ra, rb = a[:, None, :] + n * radius, b[:, None, :] + n * radius
    ra1, rb1 = a[:, None, :] + n1 * radius, b[:, None, :] + n1 * radius
    pos = np.stack([ra, rb, rb1, ra, rb1, ra1], axis=2)          # (seg, side, 6, 3)
    nor = np.stack([n, n, n1, n, n1, n1], axis=2)
    col = np.broadcast_to(np.asarray(colour, dtype=float), pos.shape[:3] + (4,))
    data = np.concatenate([pos, nor, col], axis=3).reshape(-1)
    batch.vertices.extend(data.astype(np.float32).tolist())


def rope_r(inches: float) -> float:
    return inches * 0.0254 / 2 * ROPE_DRAWN


def catenary(a, b, sag: float, n: int = 24, upto: float = 1.0) -> list[np.ndarray]:
    a, b = np.asarray(a, float), np.asarray(b, float)
    out = []
    for k in range(n + 1):
        u = upto * k / n
        p = a + (b - a) * u
        p[2] -= 4 * sag * u * (1 - u)
        out.append(p)
    return out


def sag_m(taut: bool = False) -> float:
    return (sw.C["sag_ratio_taut"] if taut else sw.C["sag_ratio"]) * sw.span_m()


def x_ropes(level: int = 1, upto: float = 1.0) -> list[list[np.ndarray]]:
    """The two ropes of the X: tree 0 to tree 2, tree 1 to tree 3."""
    return [catenary(tie(0, level), tie(2, level), sag_m(), 32, upto),
            catenary(tie(1, level), tie(3, level), sag_m(), 32, upto)]


def web_z(x: float, y: float, level: int = 1) -> float:
    return sw.web_z(math.hypot(x, y), sw.C["anchor1_m"] if level == 1 else sw.C["anchor2_m"])


def spiral_points(level: int = 1, upto: float = 1.0, per_turn: int = 48) -> list[np.ndarray]:
    sp = sw.spiral()
    turns = sp["turns"] * upto
    b = sw.C["spiral_pitch_m"] / math.tau
    out = []
    steps = max(2, int(turns * per_turn))
    for k in range(steps + 1):
        th = math.tau * turns * k / steps
        r = b * th
        x, y = r * math.cos(th + math.pi / 4), r * math.sin(th + math.pi / 4)
        out.append(np.array([x, y, web_z(x, y, level) + rope_r(0.5) * 1.5]))
    return out


def next_trees() -> list[np.ndarray]:
    return [np.array([x, y, ground(x, y)]) for x, y in sw.next_tree_xy()]


def guy_line(k: int, level: int = 1) -> tuple[np.ndarray, np.ndarray]:
    """From the tie, back and down to the base of the next tree out."""
    t = tie(k, level)
    n = next_trees()[k]
    toward = np.array([t[0] - n[0], t[1] - n[1], 0.0])
    toward /= np.linalg.norm(toward)
    out = -toward
    g = n + toward * (sw.C["tree_dbh_m"] / 2 + 0.04) + np.array([0.0, 0.0, 0.35])
    return t + out * 0.25, g


def _pine(b: TriangleBatch, t: np.ndarray, rng, height: float = TREE_H, clear: float = 13.0) -> None:
    """A tall pine, limbed up to ``clear`` metres."""
    r0 = sw.C["tree_dbh_m"] / 2
    segs = 8
    for s in range(segs):
        z0 = t[2] - 0.3 + (height * 0.92 + 0.3) * s / segs
        z1 = t[2] - 0.3 + (height * 0.92 + 0.3) * (s + 1) / segs
        r = r0 * (1 - 0.72 * (s + 0.5) / segs)
        b.cylinder((t[0], t[1], z0), (t[0], t[1], z1), r, BARK, 9)
    for _k in range(14):
        z = t[2] + rng.uniform(2.5, clear - 0.5)
        a = rng.uniform(0, math.tau)
        d = np.array([math.cos(a), math.sin(a), 0.25])
        p0 = np.array([t[0], t[1], z])
        b.cylinder(p0, p0 + d * rng.uniform(0.25, 0.45), 0.035, BARK, 5)
    tiers = 7
    for k in range(tiers):
        f = k / tiers
        base = t[2] + clear + (height - clear) * 0.86 * f
        radius = 2.3 * (1 - f) + 0.35
        tip = base + 1.8
        shade = rng.uniform(0.8, 1.15)
        col = (CANOPY[0] * shade, CANOPY[1] * shade, CANOPY[2] * shade, 1.0)
        sides = 11
        for i in range(sides):
            a0, a1 = math.tau * i / sides, math.tau * (i + 1) / sides
            p0 = np.array([t[0] + radius * math.cos(a0), t[1] + radius * math.sin(a0), base])
            p1 = np.array([t[0] + radius * math.cos(a1), t[1] + radius * math.sin(a1), base])
            b.triangle(np.array([t[0], t[1], tip]), p0, p1, col)
            b.triangle(np.array([t[0], t[1], tip]), p1, p0, col)
            b.triangle(np.array([t[0], t[1], base - 0.2]), p1, p0, (col[0] * 1.6, col[1] * 1.5, col[2] * 1.3, 1))


def tree_batch() -> TriangleBatch:
    """The four anchor pines, limbed up past the ties, and the next tree out
    beyond each, whose base takes its guy."""
    b = TriangleBatch()
    rng = np.random.default_rng(31)
    for t in trees():
        _pine(b, t, rng)
    for t in next_trees():
        _pine(b, t, rng, TREE_H - 2.0, 9.0)
    return b


def straps(b: TriangleBatch, level: int) -> None:
    """A tree-saver strap round the trunk under each tie."""
    r0 = sw.C["tree_dbh_m"] / 2
    for k, t in enumerate(trees()):
        z = (sw.C["anchor1_m"] if level == 1 else sw.C["anchor2_m"])
        r = r0 * (1 - 0.72 * z / (TREE_H * 0.92)) + 0.02
        b.cylinder((t[0], t[1], z - 0.07), (t[0], t[1], z + 0.07), r, STRAP, 12)


def web_batch(level: int = 1, guys: bool = True, x: float = 1.0, spiral: float = 1.0) -> TriangleBatch:
    b = TriangleBatch()
    straps(b, level)
    for rope in x_ropes(level, x):
        tube(b, rope, rope_r(0.5), WIRE)
    if spiral > 0:
        tube(b, spiral_points(level, spiral), rope_r(0.375), SPIRAL, 5)
        # Seizings where the spiral crosses the X.
        if spiral >= 1.0:
            sp = sw.spiral()
            for k in range(1, int(sp["turns"]) + 1):
                r = k * sw.C["spiral_pitch_m"]
                for q in range(4):
                    a = math.pi / 4 + q * math.pi / 2
                    x0, y0 = r * math.cos(a), r * math.sin(a)
                    b.sphere(np.array([x0, y0, web_z(x0, y0, level) + 0.02]), rope_r(0.5) * 1.6,
                             CORD, 2, 6)
    if guys:
        for k in range(4):
            a, g = guy_line(k, level)
            tube(b, catenary(a, g, 0.08, 10), rope_r(0.625), GUY, 5)
            n = next_trees()[k]
            b.cylinder((n[0], n[1], g[2] - 0.07), (n[0], n[1], g[2] + 0.07),
                       sw.C["tree_dbh_m"] / 2 + 0.02, STRAP, 12)
    return b


# ----------------------------------------------------------------------
# Winch, block, hook
# ----------------------------------------------------------------------

def pulley_at(level: int = 1) -> np.ndarray:
    return np.array([0.0, 0.0, web_z(0.0, 0.0, level) - 0.18])


def hook_top(level: int = 1) -> float:
    return web_z(0.0, 0.0, level) - sw.C["hook_drop_m"]


def winch_at() -> np.ndarray:
    t = trees()[0]
    inward = -np.array([t[0], t[1], 0.0]) / math.hypot(t[0], t[1])
    return np.array([t[0], t[1], 1.0]) + inward * (sw.C["tree_dbh_m"] / 2 + 0.16)


def rig_batch(level: int = 1) -> TriangleBatch:
    """The winch on tree 0, its block at the tie, and the centre pulley."""
    b = TriangleBatch()
    w = winch_at()
    t = tie(0, level)
    # A 12 V winch: drum across, motor on one end, gearbox on the other,
    # and its battery on the ground with two heavy leads.
    across = np.array([-0.7071, 0.7071, 0.0])
    b.cylinder(w - across * 0.14, w + across * 0.14, 0.085, STEEL, 14)
    b.cylinder(w + across * 0.14, w + across * 0.36, 0.075, WINCH, 14)
    b.box(w - across * 0.20, np.array([0.13, 0.13, 0.18]), WINCH)
    bat = np.array([w[0] + 0.55, w[1] + 0.15, 0.13])
    b.box(bat, np.array([0.33, 0.18, 0.24]), (0.12, 0.12, 0.14, 1.0))
    b.box(bat + [0.0, 0.0, 0.13], np.array([0.30, 0.15, 0.02]), (0.9, 0.75, 0.1, 1.0))
    for side, col in ((-0.08, (0.85, 0.1, 0.1, 1.0)), (0.08, (0.05, 0.05, 0.05, 1.0))):
        tube(b, [bat + [side, 0.0, 0.14], bat + [side, 0.0, 0.35], w + across * 0.30 + [0, 0, 0.06]],
             0.012, col, 5)
    blk = t + np.array([0.0, 0.0, -0.25])
    b.sphere(blk, 0.10, STEEL, 3, 10)
    b.sphere(pulley_at(level), 0.12, STEEL, 3, 10)
    return b


def hoist_line(b: TriangleBatch, hook: np.ndarray, level: int = 1) -> None:
    """Winch up the trunk to the block, along to the centre pulley, down to the hook."""
    w = winch_at()
    blk = tie(0, level) + np.array([0.0, 0.0, -0.25])
    pul = pulley_at(level)
    tube(b, [w + [0, 0, 0.1], blk, pul + [0, 0, 0.05], hook], rope_r(0.3125), WIRE_DARK, 5)
    b.cone(hook + [0, 0, 0.12], hook - [0, 0, 0.12], 0.07, STEEL, 8)


def hook_rest(level: int = 1) -> np.ndarray:
    return np.array([0.0, 0.0, hook_top(level)])


# ----------------------------------------------------------------------
# One panel's trip: stack, hoist, swing, pigtails, slip
# ----------------------------------------------------------------------

@lru_cache(maxsize=1)
def stack_pose() -> dict:
    """Where each panel waits, flat on the deck, before its turn."""
    order = sw.hang_order()
    pose = {}
    heights = [cvs.DECK_TOP] * STACKS
    # The last to go up are at the bottom.
    for k, i in enumerate(reversed(order)):
        s = k % STACKS
        a = math.tau * s / STACKS - math.pi / 2 + math.pi / STACKS
        p = panels()[i]
        centre = np.array([STACK_R * math.cos(a), STACK_R * math.sin(a), 0.0])
        R = to_flat(i)
        # Turn it about the vertical so a corner points out from the pad's centre.
        corners = (p["corners"] - p["balance"]) @ R.T
        out = centre / np.linalg.norm(centre)
        far = corners[np.argmax(corners @ out)]
        spin = math.atan2(out[1], out[0]) - math.atan2(far[1], far[0])
        R = rotation([0, 0, 1], spin) @ R
        z = heights[s] + p["below"]
        heights[s] += p["thick"] + 0.01
        pose[i] = (R, centre + np.array([0.0, 0.0, z]))
    return pose


def eye_final(i: int, level: int = 1, gap: float = 0.0) -> np.ndarray:
    return hung_balance(i, level, gap) + panels()[i]["normal"] * sw.C["bridle_h_m"]


def trip(i: int, q: float, level: int = 1, gap: float = 0.0) -> dict:
    """Panel ``i``, ``q`` of the way through its trip: its rotation, its balance
    point, the hook, and how far the pigtails and the harness have got."""
    q = float(np.clip(q, 0.0, 1.0))
    R0, P0 = stack_pose()[i]
    bh = sw.C["bridle_h_m"]
    deck = np.array([0.0, 0.0, cvs.DECK_TOP + panels()[i]["below"] + 0.02])
    Rf = to_flat(i)
    top = hook_top(level)
    final_eye = eye_final(i, level, gap)
    reach_eye = final_eye.copy()
    reach_eye[2] = min(reach_eye[2], top)
    haul = final_eye[2] - reach_eye[2]
    e = lambda a, b: ease(np.clip((q - a) / (b - a), 0, 1))
    pig, harness = 0.0, 1.0
    if q < 0.10:
        u = e(0.0, 0.10)
        R = Rf if u > 0.5 else R0
        P = P0 + (deck - P0) * u
        eye = P + np.array([0, 0, bh])
    elif q < 0.40:
        u = e(0.10, 0.40)
        R = Rf
        lo = deck + np.array([0, 0, bh])
        hi = np.array([0.0, 0.0, max(reach_eye[2], lo[2])])
        hi[2] = min(hi[2], top)
        eye = lo + (hi - lo) * u
        P = eye - np.array([0, 0, bh])
    elif q < 0.66:
        u = e(0.40, 0.66)
        start = np.array([0.0, 0.0, min(top, reach_eye[2])])
        eye = start + (reach_eye - start) * u
        R = to_flat(i, 1.0 - u)
        P = eye - R @ (panels()[i]["normal"] * bh)
    else:
        # Pigtails over the web, the harness slipped, and -- near the crown,
        # where the hook ran out of height -- the last bit hauled on the pigtails.
        R = np.eye(3)
        pig = e(0.66, 0.80)
        harness = 1.0 - e(0.80, 0.90)
        up = e(0.88, 1.0) * haul
        eye = reach_eye + np.array([0, 0, up])
        P = eye - panels()[i]["normal"] * bh
    hook = eye if harness >= 1.0 else reach_eye + (hook_rest(level) - reach_eye) * (1 - harness)
    return {"R": R, "P": P, "eye": eye, "hook": hook, "pig": pig, "harness": harness, "haul": haul}


def ease(u: float) -> float:
    u = float(np.clip(u, 0.0, 1.0))
    return u * u * (3 - 2 * u)


def pigtails(b: TriangleBatch, corners: np.ndarray, grow: float = 1.0, level: int = 1) -> None:
    """Three cords, thrown up over the web and tied back to the corner."""
    if grow <= 0:
        return
    for c in corners:
        top = np.array([c[0], c[1], web_z(c[0], c[1], level) + 0.05])
        over = top + np.array([c[0], c[1], 0.0]) / max(1e-6, math.hypot(c[0], c[1])) * 0.10
        tail = over + np.array([0.0, 0.0, -0.45])
        path = [c, c + (top - c) * 0.5 + np.array([0.15, 0.0, 0.0]) * (1 - grow), top, over, tail]
        n = len(path) - 1
        reach = grow * n
        pts = [path[0]]
        for k in range(n):
            if reach <= k:
                break
            f = min(1.0, reach - k)
            pts.append(path[k] + (path[k + 1] - path[k]) * f)
        tube(b, pts, rope_r(0.25), CORD, 4)


def harness_legs(b: TriangleBatch, eye: np.ndarray, corners: np.ndarray, show: float = 1.0) -> None:
    if show <= 0:
        return
    for c in corners:
        end = eye + (c - eye) * show
        tube(b, [eye, end], rope_r(0.25), HARNESS, 4)
    b.sphere(eye, 0.05, STEEL, 2, 8)


def draw_trip(b: TriangleBatch, i: int, q: float, level: int = 1, gap: float = 0.0) -> dict:
    s = trip(i, q, level, gap)
    emit(b, place(i, s["R"], s["P"]))
    corners = corners_at(i, s["R"], s["P"])
    if q > 0.10:
        harness_legs(b, s["hook"] if s["harness"] < 1 else s["eye"], corners, max(0.0, s["harness"]))
    pigtails(b, corners, s["pig"], level)
    hoist_line(b, s["hook"], level)
    return s


def hung_batch(i: int, level: int = 1, gap: float = 0.0) -> TriangleBatch:
    """Panel ``i`` at rest on its pigtails: the cached form."""
    b = TriangleBatch()
    at = hung_balance(i, level, gap)
    emit(b, place(i, np.eye(3), at))
    pigtails(b, corners_at(i, np.eye(3), at), 1.0, level)
    return b


def stacked_batch(i: int) -> TriangleBatch:
    b = TriangleBatch()
    R, P = stack_pose()[i]
    emit(b, place(i, R, P))
    return b


def dome_pose(b: TriangleBatch, R: np.ndarray, centre_from: np.ndarray, centre_to: np.ndarray,
              gap: float = 0.0, cords=None) -> None:
    """The whole dome, joined (or floating ``gap`` apart), turned and moved as
    one -- every panel in a single array operation, since it runs per frame."""
    mesh, owner, balance, normal = _stacked_panels()
    at = (balance + normal * gap - centre_from) @ R.T + centre_to          # (40, 3)
    shift = at - balance @ R.T
    m = mesh.copy()
    m[:, :, 0:3] = m[:, :, 0:3] @ R.T + shift[owner][:, None, :]
    m[:, :, 3:6] = m[:, :, 3:6] @ R.T
    emit(b, m)
    if cords is not None:
        with batched(b):
            for i in range(len(at)):
                cords(b, corners_at(i, R, at[i]))


@lru_cache(maxsize=1)
def _stacked_panels():
    ps = panels()
    mesh = np.concatenate([p["mesh"] for p in ps])
    owner = np.concatenate([np.full(len(p["mesh"]), i) for i, p in enumerate(ps)])
    return (mesh, owner, np.array([p["balance"] for p in ps]), np.array([p["normal"] for p in ps]))


# ----------------------------------------------------------------------
# Joined: lashings, the cords to the apex, the skin
# ----------------------------------------------------------------------

@lru_cache(maxsize=None)
def joints(level: int = 1) -> np.ndarray:
    """The dome's joints where it hangs from web ``level``."""
    s = cvs.sizes()
    topo = cvs.cover_model().topology
    scale = s.dome_r / topo.sphere_radius_in
    return np.asarray(topo.vertices, dtype=float) * scale + np.array([0.0, 0.0, BASE + lift_z(level)])


def seam_pairs() -> list[tuple[int, int]]:
    owners: dict[tuple, int] = {}
    for f in cvs.cover_model().topology.faces:
        ids = tuple(f.vertices)
        for k in range(3):
            key = tuple(sorted((ids[k], ids[(k + 1) % 3])))
            owners[key] = owners.get(key, 0) + 1
    return [k for k, n in owners.items() if n == 2]


def lashings_batch(level: int = 1) -> TriangleBatch:
    """Every seam lashed in three places: coils of cord round the two struts."""
    b = TriangleBatch()
    v = joints(level)
    centre = np.array([0.0, 0.0, BASE + lift_z(level)])
    per = int(sw.C["lash_per_seam"])
    for a, c in seam_pairs():
        p, q = v[a], v[c]
        axis = (q - p) / np.linalg.norm(q - p)
        out = (p + q) / 2 - centre
        out -= axis * np.dot(out, axis)
        out /= np.linalg.norm(out)
        side = np.cross(axis, out)
        for k in range(per):
            m = p + (q - p) * (k + 1) / (per + 1) + out * 0.06
            pts = [m + axis * (t - 0.5) * 0.10 + (out * math.cos(t * 50) + side * math.sin(t * 50)) * 0.11
                   for t in np.linspace(0, 1, 60)]
            tube(b, pts, 0.010, CORD, 4)
    return b


def apex_rig(b: TriangleBatch, level: int = 1, grow: float = 1.0) -> dict:
    """Cords from the joints straight through the air to one free ring under
    the cap, and one line from the ring out through the cap to the hook."""
    v = joints(level)
    apex = v[np.argmax(v[:, 2])]
    ring = apex - np.array([0.0, 0.0, sw.C["master_drop_m"]])
    used = 0
    for p in v:
        d = ring - p
        horiz = math.hypot(d[0], d[1])
        if horiz < 1e-6:
            continue
        if math.degrees(math.atan2(d[2], horiz)) < sw.C["cord_min_deg"]:
            continue
        tube(b, [p, p + d * grow], rope_r(0.375), CORD, 4)
        used += 1
    b.sphere(ring, 0.09, STEEL, 3, 10)
    tube(b, [ring, apex, pulley_at(level)], rope_r(0.5), WIRE_DARK, 6)
    return {"ring": ring, "apex": apex, "cords": used}


def skin_batch(level: int = 1, grow: float = 1.0, colour=(0.90, 0.86, 0.74, 1.0)) -> TriangleBatch:
    """The silicone-soaked cotton over the frame, laid from the crown down."""
    b = TriangleBatch()
    topo = cvs.cover_model().topology
    v = joints(level)
    centre = np.array([0.0, 0.0, BASE + lift_z(level)])
    top = v[:, 2].max()
    bottom = v[:, 2].min()
    cut = top - (top - bottom) * grow - 1e-6
    for f in topo.faces:
        tri = np.array([v[i] for i in f.vertices])
        if tri.mean(axis=0)[2] < cut:
            continue
        out = [centre + (p - centre) * (1 + 0.11 / np.linalg.norm(p - centre)) for p in tri]
        b.triangle(out[0], out[1], out[2], colour)
        b.triangle(out[0], out[2], out[1], colour)
    return b


def validate_sky_web_scene() -> None:
    sw.validate_sky_web()
    ps = panels()
    assert len(ps) == 40 and sum(len(p["mesh"]) for p in ps) > 1000
    assert all(len(p["mesh"]) > 0 for p in ps)
    # The flat rotation lays the normal on +z.
    for i in (0, 17, 39):
        assert np.allclose(to_flat(i) @ ps[i]["normal"], [0, 0, 1], atol=1e-9)
    # Every hung panel sits below the web and above the deck.
    for i in range(40):
        c = corners_at(i, np.eye(3), hung_balance(i))
        assert c[:, 2].min() > cvs.DECK_TOP + 1.0
        for x, y, z in c:
            assert z < web_z(x, y) - 0.3
        s = trip(i, 1.0)
        assert np.allclose(s["P"], hung_balance(i), atol=1e-6), i
        assert trip(i, 0.0)["P"][2] >= cvs.DECK_TOP
    # Stacks stay on the deck.
    for i, (R, P) in stack_pose().items():
        c = corners_at(i, R, P)
        assert np.hypot(c[:, 0], c[:, 1]).max() < cvs.sizes().deck_r + 0.4, i
    # The hook never climbs past its top.
    for i in sw.hang_order():
        for q in np.linspace(0, 1, 21):
            assert trip(i, q)["hook"][2] <= hook_top() + 1e-6
    for k in range(4):
        assert abs(tie(k)[2] - sw.C["anchor1_m"]) < 1e-9
        a, g = guy_line(k)
        assert g[2] < a[2] and np.hypot(*(g[:2] - next_trees()[k][:2])) < 0.5
    assert len(seam_pairs()) == 55
    b = TriangleBatch()
    rig = apex_rig(b)
    assert rig["cords"] == sw.apex_lift()["cords"] - 1, "one cord a joint; the apex hangs on the line itself"
