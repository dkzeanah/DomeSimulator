"""The workshop: a panel's jig, its rails and clamps, and the two saws, as model pieces.

The step sheets show each stage of the method on the bench. The panel on the jig is the
model's own panel, laid flat: :func:`flat` is the rigid move that puts a panel's outer face
on the jig (face down, as it is built) with its base along +x, so the sticks drawn on the
jig are the same solids that go into the dome.
"""

from __future__ import annotations

import math

import numpy as np

from . import solids as S
from .model import D, Model, Panel, Piece, stick_planes
from .solids import Mesh, unit

BENCH_Z = 0.86          # the jig's top: a bench at a comfortable height


def base_side(p: Panel) -> int:
    """The side a panel class is drawn standing on: its odd side (the base of an isosceles panel)."""
    lt = [s.letter for s in p.sides]
    counts = {x: lt.count(x) for x in lt}
    odd = [i for i, x in enumerate(lt) if counts[x] == 1]
    if len(odd) == 1:
        return odd[0]
    L = [float(np.linalg.norm(p.poly[(k + 1) % len(p.poly)] - p.poly[k])) for k in range(len(p.poly))]
    return max(range(len(L)), key=lambda i: L[i])


def flat(p: Panel, k0: int | None = None):
    """(rotation, origin): jig coordinates = rotation @ (world - origin).

    The base side runs along +x from the origin, the panel lies at +y, the outer face sits on
    the jig at z = 0 and the inner face is up. Seen from above you look at the panel's inside,
    as the builder does."""
    k0 = base_side(p) if k0 is None else k0
    n = len(p.poly)
    a, b = p.poly[k0], p.poly[(k0 + 1) % n]
    e = unit(b - a)
    u = unit(np.cross(p.normal, b - a))
    R = np.array([-e, u, -p.normal])
    return R, b


def laid(mesh: Mesh, R, origin, lift=(0, 0, BENCH_Z)) -> Mesh:
    return Mesh((mesh.verts - origin) @ R.T + np.asarray(lift, float), mesh.tris, mesh.edges, mesh.polys)


def panel_on_jig(model: Model, p: Panel, sticks: str = "all", skin: bool = False, at=(0, 0)) -> list[Piece]:
    """The panel's sticks on the bench: ``sticks`` is "none", "first", "all" or a count."""
    R, o = flat(p)
    lift = (at[0], at[1], BENCH_Z)
    w, d = model.spec.stick_w_m, model.spec.stick_d_m
    k0 = base_side(p)
    order = [(k0 + i) % len(p.poly) for i in range(len(p.poly))]
    n = {"none": 0, "first": 1, "all": len(order)}.get(sticks, sticks if isinstance(sticks, int) else len(order))
    out = []
    for k in order[:n]:
        mesh = S.solid(list(stick_planes(p, k, w, d).values()))
        out.append(Piece(f"jig-{p.id}-s{k}", f"Stick {k + 1}", "frame", "pine", laid(mesh, R, o, lift), {"k": k}))
    if skin:
        poly = [(q - o) @ R.T + np.asarray(lift) - [0, 0, 0.0001] for q in p.poly]
        m = S.prism(poly, (0, 0, -1), D("skin_t_m"))
        out.append(Piece(f"jig-{p.id}-skin", "Skin", "skin", "ply", m, {}))
    return out


def jig(model: Model, p: Panel, rails: bool = True, at=(0, 0), arcs: bool = True) -> list[Piece]:
    """The plywood jig: the outline scribed with a trammel, and rails inside each stick."""
    R, o = flat(p)
    lift = np.array([at[0], at[1], BENCH_Z])
    pts = [(q - o) @ R.T + lift for q in p.poly]
    xs, ys = [q[0] for q in pts], [q[1] for q in pts]
    m = 0.08
    sheet = S.box(((min(xs) + max(xs)) / 2, (min(ys) + max(ys)) / 2, BENCH_Z - 0.0095),
                  (max(xs) - min(xs) + 2 * m, max(ys) - min(ys) + 2 * m, 0.019))
    out = [Piece(f"jig-{p.id}-ply", "Jig plywood", "jig", "jig", sheet, {})]
    # the scribed outline and the two trammel arcs that found the apex
    ink_v, ink_e = [], []
    def seg(a, b):
        ink_v.extend([a + [0, 0, 0.0004], b + [0, 0, 0.0004]])
        ink_e.append((len(ink_v) - 2, len(ink_v) - 1))
    for i in range(len(pts)):
        seg(pts[i], pts[(i + 1) % len(pts)])
    if arcs and len(pts) == 3:
        k0 = base_side(p)
        base_a, base_b = pts[0], pts[1]                     # origin end, then along +x
        apex = pts[2]
        for c in (base_a, base_b):
            r = float(np.linalg.norm(apex[:2] - c[:2]))
            t0 = math.atan2(apex[1] - c[1], apex[0] - c[0])
            prev = None
            for j in range(13):
                t = t0 + math.radians(-9 + 1.5 * j)
                q = c + np.array([r * math.cos(t), r * math.sin(t), 0])
                if prev is not None:
                    seg(prev, q)
                prev = q
    out.append(Piece(f"jig-{p.id}-ink", "Scribed outline", "jig", "steel",
                     Mesh(np.array(ink_v), np.zeros((0, 3), int), np.array(ink_e), []), {}))
    if rails:
        w = model.spec.stick_w_m
        for i in range(len(pts)):
            a, b = pts[i], pts[(i + 1) % len(pts)]
            e = unit(b - a)
            nrm = np.array([-e[1], e[0], 0])               # inward on the jig
            # the outline on the jig is mirrored (we look at the inside), so pick the side the centre is on
            cen = np.mean(pts, axis=0)
            if (cen - a) @ nrm < 0:
                nrm = -nrm
            L = float(np.linalg.norm(b - a))
            mid = (a + b) / 2 + nrm * (w + 0.019 + 0.002)
            rail = S.box(mid + [0, 0, 0.019], (L * 0.55, 0.038, 0.038), math.degrees(math.atan2(e[1], e[0])))
            out.append(Piece(f"jig-{p.id}-rail{i}", "Rail", "jig", "rail", rail, {}))
    return out


def bench(at=(0, 0), size=(1.6, 1.2)) -> list[Piece]:
    x, y = at
    sx, sy = size
    out = [Piece("bench-top", "Bench", "shop", "joist", S.box((x, y, BENCH_Z - 0.019 - 0.02), (sx, sy, 0.04)), {})]
    for dx in (-1, 1):
        for dy in (-1, 1):
            out.append(Piece(f"bench-leg{dx}{dy}", "Bench leg", "shop", "joist",
                             S.box((x + dx * (sx / 2 - 0.08), y + dy * (sy / 2 - 0.08), (BENCH_Z - 0.06) / 2), (0.07, 0.07, BENCH_Z - 0.06)), {}))
    out.append(Piece("floor", "Shop floor", "site", "concrete", S.box((x, y, -0.01), (sx + 3, sy + 3, 0.02)), {}))
    return out


def clamp(at, yaw: float, jaw: float = 0.08) -> list[Piece]:
    """A quick-grip bar clamp, its jaws ``jaw`` apart across the stick."""
    a = math.radians(yaw)
    ux = np.array([math.cos(a), math.sin(a), 0])
    p = np.asarray(at, float)
    up = np.array([0, 0, 1.0])
    parts = [S.box(p + up * 0.09, (0.018, 0.018, 0.22), yaw),
             S.box(p + up * 0.2 + ux * 0.03, (0.07, 0.03, 0.03), yaw),
             S.box(p - up * 0.015 + ux * 0.03, (0.07, 0.03, 0.03), yaw),
             S.box(p + up * 0.13 - ux * 0.05, (0.05, 0.035, 0.12), yaw)]
    return [Piece(f"clamp-{i}-{p[0]:.2f}-{p[1]:.2f}", "Clamp", "shop", "clamp" if i else "steel", m, {}) for i, m in enumerate(parts)]


def table_saw(bevel_deg: float, board_len: float = 1.1, w: float = 0.0635, t: float = 0.0381) -> list[Piece]:
    """A table saw ripping a 2x3 in half on its bevel: the blade tilted ``bevel_deg`` from square."""
    top_z = 0.86
    out = [Piece("ts-top", "Saw table", "shop", "tool", S.box((0, 0, top_z - 0.015), (0.8, 0.7, 0.03)), {}),
           Piece("ts-cab", "Saw cabinet", "shop", "tool", S.box((0, 0, (top_z - 0.03) / 2), (0.5, 0.5, top_z - 0.03)), {}),
           Piece("ts-wing", "Fence rail", "shop", "steel", S.box((0, -0.36, top_z - 0.03), (1.2, 0.04, 0.05)), {})]
    # blade: a disc in the x-z plane (cutting along x), turned about x by the bevel
    a = math.radians(bevel_deg)
    axis = np.array([0, math.cos(a), math.sin(a)])
    c = np.array([0.0, 0.0, top_z - 0.07])
    blade = S.cylinder(c - axis * 0.0015, c + axis * 0.0015, 0.127, 40)
    out.append(Piece("ts-blade", "Blade", "shop", "blade", blade, {"bevel": bevel_deg}))
    # the board: lying flat, its centreline over the blade; half of it already through
    fed = 0.35
    for side in (-1, 1):
        # each half: a quadrilateral cross-section split by the tilted cut through the centre
        y0 = 0.0
        tilt = math.tan(a) * t
        if side < 0:
            sec = [(-w / 2, 0), (y0 - tilt / 2, 0), (y0 + tilt / 2, t), (-w / 2, t)]
        else:
            sec = [(y0 + 0.0016 - tilt / 2, 0), (w / 2, 0), (w / 2, t), (y0 + 0.0016 + tilt / 2, t)]
        poly = [np.array([-board_len / 2 + fed, y, top_z + z]) for y, z in sec]
        m = S.prism(poly, (-1, 0, 0), fed)
        out.append(Piece(f"ts-half{side}", "Ripped half", "frame", "pine", m, {}))
    whole = S.box((-board_len / 2 + fed + (board_len - fed) / 2, 0, top_z + t / 2), (board_len - fed, w, t))
    out.append(Piece("ts-board", "2x3 board", "frame", "pine", whole, {}))
    fence = S.box((0, w / 2 + 0.03, top_z + 0.04), (0.75, 0.05, 0.08))
    out.append(Piece("ts-fence", "Fence", "shop", "tool2", fence, {}))
    return out


def miter_saw(mitre_deg: float, bevel_deg: float, stick_len: float, w: float, d: float) -> list[Piece]:
    """A compound mitre saw set to ``mitre_deg`` and ``bevel_deg``, a stick against its fence."""
    top_z = 0.86
    out = [Piece("ms-base", "Saw base", "shop", "tool", S.box((0, 0, top_z - 0.04), (0.6, 0.45, 0.08)), {}),
           Piece("ms-table", "Turntable", "shop", "steel", S.cylinder((0, -0.02, top_z - 0.005), (0, -0.02, top_z), 0.18, 40), {}),
           Piece("ms-fence-l", "Fence", "shop", "steel", S.box((-0.2, 0.12, top_z + 0.045), (0.3, 0.02, 0.09)), {}),
           Piece("ms-fence-r", "Fence", "shop", "steel", S.box((0.2, 0.12, top_z + 0.045), (0.3, 0.02, 0.09)), {}),
           Piece("ms-bench", "Saw stand", "stand", "joist", S.box((0, 0, top_z - 0.1), (1.6, 0.5, 0.04)), {}),
           Piece("ms-leg1", "Stand leg", "stand", "steel", S.box((-0.6, 0, (top_z - 0.12) / 2), (0.05, 0.4, top_z - 0.12)), {}),
           Piece("ms-leg2", "Stand leg", "stand", "steel", S.box((0.6, 0, (top_z - 0.12) / 2), (0.05, 0.4, top_z - 0.12)), {})]
    # blade plane: vertical through the turntable centre, turned by the mitre, tilted by the bevel
    m, b = math.radians(mitre_deg), math.radians(bevel_deg)
    nrm = np.array([math.cos(m) * math.cos(b), math.sin(m) * math.cos(b), math.sin(b)])
    nrm = np.array([math.cos(m), math.sin(m), 0]) * math.cos(b) + np.array([0, 0, 1.0]) * math.sin(b)
    c = np.array([0, -0.02, top_z + 0.12])
    blade = S.cylinder(c - nrm * 0.0015, c + nrm * 0.0015, 0.13, 40)
    out.append(Piece("ms-blade", "Blade", "shop", "blade", blade, {}))
    guard = S.cylinder(c - nrm * 0.03 + [0, 0, 0.02], c + nrm * 0.03 + [0, 0, 0.02], 0.1, 30)
    out.append(Piece("ms-guard", "Guard", "shop", "tool2", guard, {}))
    arm_a = np.array([0, 0.2, top_z + 0.02])
    out.append(Piece("ms-arm", "Arm", "shop", "tool", S.cylinder(arm_a, c + [0, 0.0, 0.08], 0.03, 14), {}))
    out.append(Piece("ms-motor", "Motor", "shop", "tool2", S.cylinder(c + nrm * 0.04 + [0, 0, 0.04], c + nrm * 0.16 + [0, 0, 0.06], 0.05, 20), {}))
    # the stick, square inside edge against the fence, outer face down, its end at the blade
    y_face = 0.11
    st = S.box((-stick_len / 2 - 0.01, y_face - w / 2, top_z + d / 2), (stick_len, w, d))
    out.append(Piece("ms-stick", "Stick", "frame", "pine", st, {}))
    return out
