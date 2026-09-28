"""The seam channel, built as objects in the Cabin World.

A length of one real seam sits on sawhorses in front of the dome, full size:
two members from the reference 12 in log, end grain toward the camera, the
V between them, the hollow key in two halves, and the services packed
inside it -- the water line, the circuit, the Peltier pair, the drain --
with the bolts crossing near the ridge. Beside it, the same seam opened by
the spacer a 4 in duct needs. On the dome itself: every seam lit, the two
seams that carry the building's air, and a rosette at the vertices where
the channels meet.

Every size comes from :mod:`channel_facts`, which reads the solver. The
positions of the benches are scene dressing.
"""

from __future__ import annotations

import math
from functools import lru_cache

import numpy as np

from . import cabin_world as cw
from . import channel_facts as cf
from .render_kit import TriangleBatch

M = 0.0254                       # metres per inch
BENCH_A = np.array([1.20, -4.35])    # the fitted seam
BENCH_B = np.array([2.15, -4.35])    # the same seam opened by the duct spacer
SAWHORSE_TOP = 0.66
SPECIMEN_LEN = 0.90              # metres of seam on the bench

PINE_FACE = (0.80, 0.58, 0.33, 1.0)
PINE_SAWN = (0.93, 0.76, 0.50, 1.0)
KEY = (0.35, 0.80, 0.86, 0.34)
KEY_EDGE = (0.20, 0.55, 0.62, 1.0)
PEX = (0.85, 0.18, 0.16, 1.0)          # hot-water red PEX reads at a glance
NM = (0.95, 0.93, 0.86, 1.0)           # white NM sheath
LOWV = (0.12, 0.12, 0.13, 1.0)
DRAIN = (0.70, 0.86, 0.95, 1.0)
DUCT = (0.78, 0.79, 0.82, 1.0)
STEEL = (0.62, 0.64, 0.68, 1.0)
AIR = (0.45, 0.92, 0.62, 0.85)
WATER = (0.42, 0.75, 1.00, 0.9)
GLOW = (1.00, 0.74, 0.32, 1.0)
CYAN = (0.30, 0.85, 1.00, 1.0)


def tight() -> cf.SeamType:
    """The narrower of the two seam profiles: the one every figure must survive."""
    return min(cf.seam_types(), key=lambda t: t.gap_deg)


# ----------------------------------------------------------------------
# The seam frame: x across the seam, y outward (up), z along the seam
# ----------------------------------------------------------------------

class Frame:
    """Seam-section inches to world metres, for one bench."""

    def __init__(self, bench: np.ndarray, t: cf.SeamType):
        ridge_z = SAWHORSE_TOP + t.depth_in * math.cos(math.radians(t.gap_deg / 2)) * M
        self.origin = np.array([bench[0], bench[1] - SPECIMEN_LEN / 2, ridge_z])
        self.y0, self.y1 = 0.0, SPECIMEN_LEN

    def at(self, x_in: float, y_in: float, along_m: float) -> np.ndarray:
        return self.origin + np.array([x_in * M, along_m, y_in * M])

    @property
    def near(self) -> np.ndarray:
        """Centre of the end face the camera looks at, a little below the ridge."""
        return self.origin + np.array([0.0, 0.0, -0.07])


def _extrude(batch: TriangleBatch, frame: Frame, poly, colours, a0: float, a1: float,
             cap=None) -> None:
    """A prism along the seam from a 2-D polygon (inches). ``colours`` per edge."""
    n = len(poly)
    for i in range(n):
        p, q = poly[i], poly[(i + 1) % n]
        batch.quad(frame.at(*p, a0), frame.at(*q, a0), frame.at(*q, a1), frame.at(*p, a1),
                   colours[i % len(colours)])
    if cap is not None:
        for along, normal in ((a0, (0, -1.0, 0)), (a1, (0, 1.0, 0))):
            for i in range(1, n - 1):
                batch.triangle(frame.at(*poly[0], along), frame.at(*poly[i], along),
                               frame.at(*poly[i + 1], along), cap, np.array(normal))


def _members(batch: TriangleBatch, frame: Frame, t: cf.SeamType, spacer_in: float) -> None:
    """Two 45 degree sectors of the log, sawn faces forming the V, end grain showing."""
    from wedge_book import cover_scene as cs

    h = math.radians(t.gap_deg / 2)
    sector = math.radians(360.0 / cw.landmarks().splits)
    r = t.depth_in
    for side in (-1, 1):
        pith = (side * (r * math.sin(h) + spacer_in / 2), -r * math.cos(h))
        # The sawn face runs from the pith up to the ridge; the sector turns
        # away from the seam from there.
        toward_ridge = math.atan2(math.cos(h), -side * math.sin(h))
        t0, t1 = ((toward_ridge, toward_ridge + sector) if side < 0
                  else (toward_ridge - sector, toward_ridge))
        steps = 10
        arc = [(pith[0] + r * math.cos(t0 + (t1 - t0) * k / steps),
                pith[1] + r * math.sin(t0 + (t1 - t0) * k / steps)) for k in range(steps + 1)]
        poly = [pith] + arc
        colours = [PINE_SAWN] + [PINE_FACE] * (steps) + [PINE_SAWN]
        _extrude(batch, frame, poly, colours, frame.y0, frame.y1)
        for along, normal in ((frame.y0, (0, -1.0, 0)), (frame.y1, (0, 1.0, 0))):
            cs.end_grain(batch, frame.at(*pith, along), (M / M, 0.0, 0.0), (0.0, 0.0, 1.0),
                         normal, r * M, t0, t1, steps, phase=side * 1.3)


def _sawhorses(batch: TriangleBatch, bench: np.ndarray) -> None:
    wood, dark = (0.55, 0.40, 0.24, 1.0), (0.40, 0.28, 0.16, 1.0)
    for dy in (-SPECIMEN_LEN / 2 + 0.14, SPECIMEN_LEN / 2 - 0.14):
        c = np.array([bench[0], bench[1] + dy, SAWHORSE_TOP - 0.03])
        batch.box(c, (0.62, 0.07, 0.06), wood)
        for dx in (-0.25, 0.25):
            for ddy in (-0.05, 0.05):
                batch.box((c[0] + dx, c[1] + ddy, (SAWHORSE_TOP - 0.06) / 2),
                          (0.035, 0.035, SAWHORSE_TOP - 0.06), dark)


# ----------------------------------------------------------------------
# What goes inside
# ----------------------------------------------------------------------

def inner(t: cf.SeamType, spacer_in: float = 0.0):
    return cf.inset(cf.v_polygon(t, spacer_in, t.nose_in), cf.K["key_wall_in"])


def half_width(poly, y: float) -> float:
    """Half the channel's width at height ``y`` (the polygon is symmetric)."""
    right = sorted((p for p in poly if p[0] > 0), key=lambda p: p[1])
    (xb, yb), (xt, yt) = right[0], right[-1]
    if yt == yb:
        return xb
    k = min(1.0, max(0.0, (y - yb) / (yt - yb)))
    return xb + (xt - xb) * k


def pack(t: cf.SeamType, spacer_in: float, keys) -> list[tuple[cf.Service, float, float]]:
    """Stack the services up the middle of the channel, widest at the bottom.

    Returns (service, x, y) centres in inches. The bottom of the section is
    the room side, where the channel is widest; the ridge end is narrowest.
    """
    poly = inner(t, spacer_in)
    cursor = min(p[1] for p in poly) + 0.05
    placed = []
    for s in sorted((cf.SERVICE[k] for k in keys), key=lambda s: -s.width_in):
        height = s.width_in if s.shape == "round" else s.thick_in
        y = cursor + height / 2
        if s.width_in / 2 > half_width(poly, cursor + height) - 0.02:
            raise ValueError(f"{s.label} does not fit at {y:.2f} in")
        placed.append((s, 0.0, y))
        cursor += height + 0.06
    return placed


def _service(batch: TriangleBatch, frame: Frame, s: cf.Service, x: float, y: float,
             a0: float, a1: float) -> None:
    colour = {"pex_half": PEX, "pex_three_quarter": PEX, "nm_14_2": NM, "nm_12_2": NM,
              "peltier_pair": LOWV, "drain": DRAIN}.get(s.key, DUCT)
    if s.shape == "round":
        batch.cylinder(frame.at(x, y, a0), frame.at(x, y, a1), s.width_in / 2 * M, colour, 16)
    else:
        centre = (frame.at(x, y, a0) + frame.at(x, y, a1)) / 2
        batch.box(centre, (s.width_in * M, a1 - a0, s.thick_in * M), colour)


def key_shell(batch: TriangleBatch, frame: Frame, t: cf.SeamType, spacer_in: float,
              colour=KEY) -> None:
    """The hollow key: outer and inner surfaces, the two ends as rings."""
    outer = cf.v_polygon(t, spacer_in, t.nose_in)
    inside = inner(t, spacer_in)
    outer, inside = cf._ccw(outer), cf._ccw(inside)
    _extrude(batch, frame, outer, [colour], frame.y0 + 0.002, frame.y1 - 0.002)
    _extrude(batch, frame, inside, [colour], frame.y0 + 0.002, frame.y1 - 0.002)
    for along in (frame.y0 + 0.002, frame.y1 - 0.002):
        for i in range(len(outer)):
            j = (i + 1) % len(outer)
            batch.quad(frame.at(*outer[i], along), frame.at(*outer[j], along),
                       frame.at(*inside[j], along), frame.at(*inside[i], along), KEY_EDGE)
    # The split between the two half-keys, top and bottom, down the middle.
    top, bottom = max(p[1] for p in outer), min(p[1] for p in outer)
    for y in (top, bottom):
        a, b = frame.at(0.0, y, frame.y0), frame.at(0.0, y, frame.y1)
        batch.cylinder(a, b, 0.0012, KEY_EDGE, 6)


def half_keys(batch: TriangleBatch, frame: Frame, t: cf.SeamType, apart_m: float,
              colour=KEY) -> None:
    """The key split down its middle: each half belongs to one member's face."""
    outer = cf.v_polygon(t, 0.0, t.nose_in)
    inside = inner(t)
    for side in (-1, 1):
        def half(poly):
            pts = [p for p in poly if p[0] * side > 0]
            top = max(p[1] for p in poly)
            bottom = min(p[1] for p in poly)
            return [(0.0, top)] + sorted(pts, key=lambda p: -p[1]) + [(0.0, bottom)]
        shift = side * apart_m / M
        for poly in (half(outer), half(inside)):
            moved = [(x + shift, y) for x, y in poly]
            _extrude(batch, frame, moved, [colour], frame.y0 + 0.002, frame.y1 - 0.002)


def bolts(batch: TriangleBatch, frame: Frame, t: cf.SeamType, spacer_in: float) -> None:
    """Bolts cross the V near the ridge, where it is narrowest."""
    y = -(t.nose_in + 0.45)
    reach = half_width(cf.v_polygon(t, spacer_in, t.nose_in), y) + 1.2
    for along in (0.22, SPECIMEN_LEN - 0.22):
        batch.cylinder(frame.at(-reach, y, along), frame.at(reach, y, along), 0.25 / 2 * M, STEEL, 12)


@lru_cache(maxsize=None)
def _static(name: str) -> TriangleBatch:
    """The heavy, unchanging pieces, built once per process."""
    t = tight()
    batch = TriangleBatch()
    if name == "bench_a":
        frame = Frame(BENCH_A, t)
        _sawhorses(batch, BENCH_A)
        _members(batch, frame, t, 0.0)
    elif name == "bench_a_bundle":
        frame = Frame(BENCH_A, t)
        for s, x, y in pack(t, 0.0, cf.BUNDLE):
            _service(batch, frame, s, x, y, frame.y0 - 0.03, frame.y1 + 0.03)
    elif name == "bench_a_bolts":
        bolts(batch, Frame(BENCH_A, t), t, 0.0)
    elif name == "bench_b":
        sp = spacer_4()
        frame = Frame(BENCH_B, t)
        _sawhorses(batch, BENCH_B)
        _members(batch, frame, t, sp)
        # The ridge is now open by the spacer's width: an aluminium cap closes it.
        top = frame.at(0.0, 0.0, frame.y0)
        batch.box(top + np.array([0.0, SPECIMEN_LEN / 2, 0.006]),
                  ((sp + 1.5) * M, SPECIMEN_LEN, 0.004), STEEL)
    elif name == "bench_b_duct":
        sp = spacer_4()
        frame = Frame(BENCH_B, t)
        for s, x, y in pack(t, sp, ("duct_4",) + cf.BUNDLE):
            _service(batch, frame, s, x, y, frame.y0 - 0.03, frame.y1 + 0.03)
    elif name == "seams":
        for a, b in world_seams():
            batch.cylinder(a, b, 0.014, GLOW, 6)
    return batch


def spacer_4() -> float:
    """The spacer the tight profile gets when every panel moves out for a 4 in duct."""
    sp = cf.spacer_for(("duct_4",) + cf.BUNDLE)
    types = cf.seam_types()
    return sp.actual_in[types.index(tight())]


def paint_bench(app, which: str = "a", bundle: bool = True, bolted: bool = True) -> Frame:
    """The specimen, as cached layers; the see-through key is drawn per frame."""
    t = tight()
    if which == "a":
        app.static_layer("channel:bench_a", lambda: _static("bench_a"), bench_points(BENCH_A))
        if bundle:
            app.static_layer("channel:bench_a_bundle", lambda: _static("bench_a_bundle"))
        if bolted:
            app.static_layer("channel:bench_a_bolts", lambda: _static("bench_a_bolts"))
        return Frame(BENCH_A, t)
    app.static_layer("channel:bench_b", lambda: _static("bench_b"), bench_points(BENCH_B))
    app.static_layer("channel:bench_b_duct", lambda: _static("bench_b_duct"))
    return Frame(BENCH_B, t)


def bench_points(bench: np.ndarray) -> list[np.ndarray]:
    t = tight()
    frame = Frame(bench, t)
    w = (t.depth_in + 1.0) * M
    return [frame.origin + np.array([dx, dy, dz]) for dx in (-w, w)
            for dy in (0.0, SPECIMEN_LEN) for dz in (-0.16, 0.05)]


def peltier_and_gate(batch: TriangleBatch, frame: Frame, t: cf.SeamType) -> dict:
    """The cold plate on the key's room-side wall, fins below; the gate at the far end."""
    poly = inner(t)
    bottom = min(p[1] for p in poly)
    mid = SPECIMEN_LEN * 0.55
    plate = frame.at(0.0, bottom + 0.08, mid)
    batch.box(plate, (0.040, 0.040, 0.004), (0.80, 0.83, 0.88, 1.0))
    base = frame.at(0.0, bottom - cf.K["key_wall_in"] - 0.3, mid)
    for k in range(7):
        batch.box(base + np.array([-0.027 + k * 0.009, 0.0, -0.018]), (0.003, 0.050, 0.036),
                  (0.55, 0.57, 0.60, 1.0))
    # Three-way gate: a collar round the key near the far end, three ports.
    far = SPECIMEN_LEN - 0.10
    centre = frame.at(0.0, (bottom + max(p[1] for p in poly)) / 2, far)
    outer_w = 2 * half_width(cf.v_polygon(t, 0.0, t.nose_in), bottom) * M
    batch.box(centre, (outer_w + 0.03, 0.05, t.depth_in * M * 0.9), (0.95, 0.60, 0.15, 1.0))
    ports = {
        "along": centre + np.array([0.0, 0.07, 0.0]),
        "silica": centre + np.array([0.0, 0.0, -t.depth_in * M * 0.75]),
        "isolate": centre + np.array([outer_w / 2 + 0.07, 0.0, 0.0]),
    }
    batch.cylinder(centre, ports["silica"], 0.012, (0.95, 0.60, 0.15, 1.0), 10)
    batch.box(ports["silica"] + np.array([0.0, 0.0, -0.03]), (0.10, 0.06, 0.05), (0.90, 0.90, 0.85, 1.0))
    batch.cylinder(centre, ports["isolate"], 0.010, (0.95, 0.60, 0.15, 1.0), 10)
    return {"plate": plate, "fins": base, **ports}


def air_arrows(batch: TriangleBatch, frame: Frame, t: cf.SeamType, spacer_in: float,
               p: float, keys=cf.BUNDLE) -> None:
    """Air moving along the free space above the bundle."""
    poly = inner(t, spacer_in)
    top = max(q[1] for q in poly)
    packed = pack(t, spacer_in, keys)
    s, _x, y = packed[-1]
    over = y + (s.width_in if s.shape == "round" else s.thick_in) / 2
    y_air = (over + top) / 2
    for k in range(6):
        along = ((k / 6 + p * 0.8) % 1.0) * (SPECIMEN_LEN - 0.1) + 0.05
        a = frame.at(0.0, y_air, along)
        batch.cone(a, a + np.array([0.0, 0.05, 0.0]), 0.012, AIR, 10)


# ----------------------------------------------------------------------
# On the dome
# ----------------------------------------------------------------------

@lru_cache(maxsize=None)
def _world():
    from wedge_book import cover_scene as cs

    s = cs.sizes()
    model = cs.cover_model()
    scale = s.dome_r / model.topology.sphere_radius_in
    shift = np.array([0.0, 0.0, cs.DECK_TOP + 0.02])
    return model, scale, shift


def world_seams(lift_in: float = 0.5) -> list[tuple[np.ndarray, np.ndarray]]:
    """Every seam's outer ridge, in the world, ``lift_in`` proud of it."""
    model, scale, shift = _world()
    out = []
    for seam in model.seams:
        n = (seam.apex_start + seam.apex_end) / 2
        lift = n / np.linalg.norm(n) * lift_in
        out.append(((seam.apex_start + lift) * scale + shift, (seam.apex_end + lift) * scale + shift))
    return out


def air_seams(count: int = 2) -> list[tuple[np.ndarray, np.ndarray]]:
    """The seams nearest the hero camera, lowest end first."""
    # Lifted clear of the members' rounded faces, which stand above the ridge.
    seams = sorted(world_seams(6.0), key=lambda ab: (ab[0][1] + ab[1][1]) / 2)[:count]
    return [(a, b) if a[2] < b[2] else (b, a) for a, b in seams]


def vertices() -> list[dict]:
    """Every dome vertex in the world, with how many channels meet there."""
    model, scale, shift = _world()
    topo = model.topology
    faces_at: dict[int, int] = {}
    for f in topo.faces:
        for v in f.vertices:
            faces_at[v] = faces_at.get(v, 0) + 1
    rim = {v for e in topo.edges.values() if e.is_base for v in e.key}
    out = []
    for v, count in faces_at.items():
        nbrs = [e.key[1] if e.key[0] == v else e.key[0] for e in topo.edges.values()
                if v in e.key and not e.is_base]
        out.append({"index": v, "ways": count, "rim": v in rim,
                    "point": topo.vertices[v] * scale + shift,
                    "normal": topo.vertices[v] / np.linalg.norm(topo.vertices[v]),
                    "neighbours": [topo.vertices[n] * scale + shift for n in nbrs]})
    return out


def facing_vertex(ways: int) -> dict:
    """The interior vertex of this kind that faces the hero camera best."""
    hero = np.array(cw.HERO_EYE)
    cands = [v for v in vertices() if v["ways"] == ways and not v["rim"]]
    return min(cands, key=lambda v: np.linalg.norm(v["point"] - hero))


def rosette(batch: TriangleBatch, vertex: dict, radius: float, colour=CYAN) -> None:
    """A junction box inside a vertex, and the channel mouths it gathers."""
    n = vertex["normal"]
    centre = vertex["point"] - n * (cw.landmarks().trunk_r + 0.03)
    arms = []
    for q in vertex["neighbours"]:
        d = q - vertex["point"]
        d = d - n * np.dot(d, n)
        arms.append(d / np.linalg.norm(d))
    for d in arms:
        batch.cylinder(centre, centre + d * 0.40, 0.03, colour, 8)
    batch.sphere(centre, radius, colour, 5, 12)


def footprint_ring(batch: TriangleBatch, radius: float, colour, z: float, width: float = 0.05) -> None:
    steps = 96
    for k in range(steps):
        a, b = math.tau * k / steps, math.tau * (k + 1) / steps
        p = [np.array([r * math.cos(t), r * math.sin(t), z]) for r, t in
             ((radius - width, a), (radius + width, a), (radius + width, b), (radius - width, b))]
        batch.quad(*p, colour, np.array([0.0, 0.0, 1.0]))


def paint_seams(app) -> None:
    app.static_layer("channel:seams", lambda: _static("seams"))


def validate_channel_scene() -> None:
    cf.validate_channel()
    t = tight()
    placed = pack(t, 0.0, cf.BUNDLE)
    assert len(placed) == len(cf.BUNDLE)
    # Every service sits inside the key's inside.
    poly = inner(t)
    for s, _x, y in placed:
        h = s.width_in if s.shape == "round" else s.thick_in
        assert min(p[1] for p in poly) < y - h / 2 and y + h / 2 < max(p[1] for p in poly)
    pack(t, spacer_4(), ("duct_4",) + cf.BUNDLE)
    assert len(world_seams()) == sum(x.count for x in cf.seam_types())
    assert facing_vertex(5)["ways"] == 5 and facing_vertex(6)["ways"] == 6
