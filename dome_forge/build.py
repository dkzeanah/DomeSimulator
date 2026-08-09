"""Turn a layer stack into triangles.

Every dimension traces back to :func:`two_v_demo.geometry.build_demo_geometry`
-- the same 2V geometry the rest of this project teaches from -- scaled by
the dome radius. Nothing about the dome's shape, edge count, or face count
is written down twice.

Emitters are pure functions of (layer params, dome context, time), so the
same inputs always produce the same frame. That keeps a live preview and an
offscreen screenshot identical.
"""

from __future__ import annotations

import math

import numpy as np

from presenter.world import Batch
from two_v_demo.geometry import build_demo_geometry, normalize

TAU = math.tau


# Named colours, so a layer's "tint" choice means the same thing everywhere.
TINTS: dict[str, tuple[float, float, float]] = {
    "steel": (0.62, 0.68, 0.74),
    "aluminium": (0.78, 0.82, 0.86),
    "timber": (0.72, 0.52, 0.32),
    "glass": (0.55, 0.80, 0.92),
    "copper": (0.85, 0.52, 0.28),
    "water": (0.26, 0.62, 0.95),
    "amber": (1.00, 0.67, 0.20),
    "moss": (0.36, 0.62, 0.34),
    "charcoal": (0.20, 0.23, 0.26),
    "white": (0.93, 0.95, 0.97),
}


def tint(name: str, alpha: float = 1.0) -> tuple[float, float, float, float]:
    r, g, b = TINTS.get(name, TINTS["steel"])
    return (r, g, b, alpha)


def _shade(color, factor: float):
    """Lighten (>1) or darken (<1) a colour, keeping its alpha."""
    r, g, b, a = color
    return (min(1.0, r * factor), min(1.0, g * factor), min(1.0, b * factor), a)


def _slerp(a: np.ndarray, b: np.ndarray, t: float) -> np.ndarray:
    """Interpolate along the great circle between two unit vectors, so
    struts and veins follow the sphere instead of cutting straight across
    it."""
    dot = float(np.clip(np.dot(a, b), -1.0, 1.0))
    theta = math.acos(dot)
    if theta < 1e-9:
        return a.copy()
    sin_theta = math.sin(theta)
    return (math.sin((1.0 - t) * theta) / sin_theta) * a + (
        math.sin(t * theta) / sin_theta
    ) * b


class DomeContext:
    """Everything the emitters need to know about this particular dome."""

    def __init__(self, radius: float, cut_enabled: bool = False,
                 cut_start: float = 0.0, cut_sweep: float = 0.0) -> None:
        geo = build_demo_geometry()
        self.geo = geo
        self.radius = float(radius)
        self.unit = np.asarray(geo.vertices, dtype=np.float64)
        self.points = self.unit * self.radius
        self.faces = np.asarray(geo.hemisphere_faces, dtype=int)
        self.edges = tuple(geo.hemisphere_edges)
        self.base_ring = tuple(geo.base_ring)
        self.edge_class = {}
        for edge, name in zip(geo.edges, geo.edge_class_by_edge):
            self.edge_class[tuple(sorted(edge))] = name
        self.cut_enabled = bool(cut_enabled)
        self.cut_start = float(cut_start) % 360.0
        self.cut_sweep = float(cut_sweep)
        # The base ring's radius is a property of the geometry, not a guess.
        ring = self.points[list(self.base_ring)]
        self.base_radius = float(np.mean(np.hypot(ring[:, 0], ring[:, 1])))

    # -- cutaway ---------------------------------------------------------

    def hidden(self, point) -> bool:
        """True when a point falls inside the removed wedge, so the inside
        of the dome can be inspected without deleting any layer."""
        if not self.cut_enabled or self.cut_sweep <= 0.0:
            return False
        angle = math.degrees(math.atan2(float(point[1]), float(point[0]))) % 360.0
        delta = (angle - self.cut_start) % 360.0
        return delta < self.cut_sweep

    # -- helpers ---------------------------------------------------------

    def edge_name(self, a: int, b: int) -> str:
        return self.edge_class.get(tuple(sorted((a, b))), "LONG")

    def arc(self, a: int, b: int, radius: float, samples: int) -> list[np.ndarray]:
        ua, ub = self.unit[a], self.unit[b]
        return [_slerp(ua, ub, i / samples) * radius for i in range(samples + 1)]

    def face_centroid_unit(self, face) -> np.ndarray:
        return normalize(self.unit[face].sum(axis=0))


def rnd(i: float, salt: float = 0.0) -> float:
    """Deterministic pseudo-random in [0, 1) -- same seed, same dome, every
    run, so screenshots are reproducible."""
    return (math.sin(i * 127.1 + salt * 311.7) * 43758.5453) % 1.0


# ---------------------------------------------------------------------------
# Emitters. Each takes (opaque, translucent, layer, ctx, t) and adds
# triangles. `alpha` already folds in the layer's opacity slider.
# ---------------------------------------------------------------------------


def emit_ground(op: Batch, tr: Batch, layer, ctx: DomeContext, t: float) -> None:
    alpha = layer.opacity
    color = tint(layer.get("tint"), alpha)
    extent = ctx.radius * float(layer.get("extent"))
    target = tr if alpha < 0.999 else op
    target.disc((0.0, 0.0, -0.01), extent, color, sides=64)
    ring = _shade(color, 1.25)
    for i in range(48):
        a0 = TAU * i / 48
        a1 = TAU * (i + 1) / 48
        r0 = ctx.base_radius
        target.quad(
            (r0 * math.cos(a0), r0 * math.sin(a0), 0.0),
            (r0 * math.cos(a1), r0 * math.sin(a1), 0.0),
            (r0 * 1.03 * math.cos(a1), r0 * 1.03 * math.sin(a1), 0.0),
            (r0 * 1.03 * math.cos(a0), r0 * 1.03 * math.sin(a0), 0.0),
            ring, (0.0, 0.0, 1.0),
        )


def emit_frame(op: Batch, tr: Batch, layer, ctx: DomeContext, t: float) -> None:
    alpha = layer.opacity
    base = tint(layer.get("tint"), alpha)
    thickness = float(layer.get("thickness"))
    sides = int(layer.get("sides"))
    split = bool(layer.get("split_classes"))
    target = tr if alpha < 0.999 else op
    for a, b in ctx.edges:
        pa, pb = ctx.points[a], ctx.points[b]
        if ctx.hidden((pa + pb) * 0.5):
            continue
        color = base
        if split:
            color = _shade(base, 1.14 if ctx.edge_name(a, b) == "LONG" else 0.78)
        target.cylinder(pa, pb, thickness, color, sides=sides)


def face_frame(ctx: DomeContext, face, width: float, seam: float):
    """The three boards of one hubless triangle, in that triangle's own
    plane.

    Each board's outer long edge lies on the seam line between two sphere
    vertices, and the board runs ``width`` inward from there. Cutting all
    three that way automatically produces the mitered corners: each corner
    lands on the bisector of that triangle's interior angle. Because the
    neighbouring triangle does exactly the same on its side, every seam in
    the finished dome carries two boards -- which is what makes the whole
    thing hubless.

    Returns (boards, normal), where each board is the outer quad
    (p_a, p_b, p_b_inner, p_a_inner).
    """
    a, b, c = (ctx.points[i].astype(np.float64) for i in face)
    normal = normalize(np.cross(b - a, c - a))
    if float(np.dot(normal, (a + b + c) / 3.0)) < 0.0:
        normal = -normal

    def inset_corner(corner, first, second, offset):
        """Slide a corner along its own angle bisector until it sits
        ``offset`` in from both of its edges."""
        u1 = normalize(first - corner)
        u2 = normalize(second - corner)
        bisector = normalize(u1 + u2)
        half = math.acos(float(np.clip(np.dot(u1, u2), -1.0, 1.0))) * 0.5
        return corner + bisector * (offset / max(1e-6, math.sin(half)))

    # `seam` pulls the outer edge in slightly so the two boards meeting at
    # a seam stay visually distinct; at seam=0 they touch exactly.
    outer = [inset_corner(p, q, r, seam)
             for p, q, r in ((a, b, c), (b, c, a), (c, a, b))]
    inner = [inset_corner(p, q, r, seam + width)
             for p, q, r in ((a, b, c), (b, c, a), (c, a, b))]
    boards = []
    for i in range(3):
        j = (i + 1) % 3
        boards.append((outer[i], outer[j], inner[j], inner[i]))
    return boards, normal


def _solid_quad(batch: Batch, quad, normal, thickness: float, color) -> None:
    """Extrude a flat quad inward along ``normal`` into a closed board."""
    top = [np.asarray(p, dtype=np.float64) for p in quad]
    bottom = [p - normal * thickness for p in top]
    batch.quad(top[0], top[1], top[2], top[3], color, normal)
    batch.quad(bottom[3], bottom[2], bottom[1], bottom[0], color, -normal)
    side = _shade(color, 0.82)
    for i in range(4):
        j = (i + 1) % 4
        batch.quad(top[i], bottom[i], bottom[j], top[j], side)


def emit_triangle_frames(op: Batch, tr: Batch, layer, ctx: DomeContext,
                         t: float) -> None:
    """40 individual bolted triangles, no hubs anywhere."""
    alpha = layer.opacity
    base = tint(layer.get("tint"), alpha)
    width = float(layer.get("width"))
    thickness = float(layer.get("thickness"))
    seam = float(layer.get("seam"))
    split = bool(layer.get("split_classes"))
    show_bolts = bool(layer.get("bolts"))
    bolt_count = max(1, int(layer.get("bolt_count")))
    bolt_size = float(layer.get("bolt_size"))
    target = tr if alpha < 0.999 else op
    bolt_color = tint("steel", alpha)

    for face in ctx.faces:
        if ctx.hidden(ctx.points[face].mean(axis=0)):
            continue
        names = [ctx.edge_name(int(face[i]), int(face[(i + 1) % 3]))
                 for i in range(3)]
        color = base
        if split:
            # All-LONG is one of the 10 equilaterals; the rest are the 30
            # isosceles triangles. Those are exactly the two jig shapes.
            color = _shade(base, 1.16 if names.count("LONG") == 3 else 0.84)
        boards, normal = face_frame(ctx, face, width, seam)
        for board in boards:
            _solid_quad(target, board, normal, thickness, color)

        if show_bolts:
            for i, board in enumerate(boards):
                # Bolts run through the pair of boards that meet at this
                # seam, so they sit on the seam line itself.
                p0, p1 = board[0], board[1]
                for k in range(bolt_count):
                    f = (k + 1) / (bolt_count + 1)
                    at = p0 + (p1 - p0) * f
                    head = at - normal * (thickness * 0.5)
                    target.cylinder(
                        head + normal * bolt_size * 1.2,
                        head - normal * bolt_size * 1.2,
                        bolt_size * 0.5, bolt_color, sides=6,
                    )


def emit_assemblies(op: Batch, tr: Batch, layer, ctx: DomeContext,
                    t: float) -> None:
    """Every triangle drawn from its own assignment: its own three struts
    and its own fill."""
    from .panel import build_panel

    stack = _ACTIVE_STACK["stack"]
    if stack is None:
        return
    assignments = stack.assignments
    alpha = layer.opacity
    seam = float(layer.get("seam"))
    show_fills = bool(layer.get("show_fills"))
    highlight_on = bool(layer.get("highlight"))
    selected = getattr(stack, "selected_face", -1)
    # A whole group can be lit at once (the group editors do this), which
    # is what makes a pentagon or hourglass readable on a busy dome.
    lit = set(getattr(stack, "highlight_faces", ()) or ())

    for index, face in enumerate(ctx.faces):
        if ctx.hidden(ctx.points[face].mean(axis=0)):
            continue
        classes = [ctx.edge_name(int(face[i]), int(face[(i + 1) % 3]))
                   for i in range(3)]
        struts = assignments.strut_triple(index, classes)
        fill = assignments.fill_for(index) if show_fills else "open"
        build_panel(
            op, tr, [ctx.points[i] for i in face], struts, fill, tint,
            seam=seam, alpha=alpha,
            highlight=highlight_on and (index == selected or index in lit),
        )


def emit_waist_joints(op: Batch, tr: Batch, layer, ctx: DomeContext,
                      t: float) -> None:
    from .groups import emit_waist, hourglasses

    stack = _ACTIVE_STACK["stack"]
    if stack is None:
        return
    alpha = layer.opacity
    size = float(layer.get("size"))
    target = tr if alpha < 0.999 else op
    for hourglass in hourglasses():
        if ctx.hidden(ctx.points[hourglass.waist]):
            continue
        emit_waist(target, ctx, hourglass,
                   stack.assignments.joint_for(hourglass.index),
                   tint, size=size, alpha=alpha)


def emit_hubs(op: Batch, tr: Batch, layer, ctx: DomeContext, t: float) -> None:
    alpha = layer.opacity
    color = tint(layer.get("tint"), alpha)
    size = float(layer.get("size"))
    target = tr if alpha < 0.999 else op
    seen = sorted({int(i) for face in ctx.faces for i in face})
    for index in seen:
        point = ctx.points[index]
        if ctx.hidden(point):
            continue
        target.blob(point, size, color, seed=float(index))


def _panel_grid(ctx: DomeContext, face, inset: float, dish: float,
                lift: float, resolution: int):
    """Barycentric grid over one triangular face, pulled in from the struts
    and optionally dished inward like a golf-ball dimple.

    Returns a dict of (i, j) -> 3D point, where i+j <= resolution.
    """
    a, b, c = (ctx.unit[i] for i in face)
    radius = ctx.radius + lift
    # Convert the metric inset into a barycentric shrink toward the centroid.
    edge_len = float(np.linalg.norm(ctx.points[face[0]] - ctx.points[face[1]]))
    shrink = 0.0 if edge_len <= 1e-9 else min(0.45, inset / edge_len)
    grid: dict[tuple[int, int], np.ndarray] = {}
    for i in range(resolution + 1):
        for j in range(resolution + 1 - i):
            k = resolution - i - j
            u, v, w = i / resolution, j / resolution, k / resolution
            # pull toward centroid by `shrink`
            u = u + (1 / 3 - u) * shrink
            v = v + (1 / 3 - v) * shrink
            w = w + (1 / 3 - w) * shrink
            direction = normalize(u * a + v * b + w * c)
            # 27uvw peaks at exactly 1.0 at the centroid and is 0 on every
            # edge, so the dish blends smoothly into the seam line.
            bowl = 27.0 * u * v * w
            grid[(i, j)] = direction * (radius * (1.0 - dish * bowl))
    return grid


def emit_panels(op: Batch, tr: Batch, layer, ctx: DomeContext, t: float) -> None:
    alpha = layer.opacity
    color = tint(layer.get("tint"), alpha)
    inset = float(layer.get("inset"))
    dish = float(layer.get("dish"))
    lift = float(layer.get("lift"))
    resolution = max(1, int(layer.get("resolution")))
    target = tr if (alpha < 0.999 or layer.spec.translucent) else op
    for face in ctx.faces:
        if ctx.hidden(ctx.points[face].mean(axis=0)):
            continue
        grid = _panel_grid(ctx, face, inset, dish, lift, resolution)
        for i in range(resolution):
            for j in range(resolution - i):
                p00 = grid[(i, j)]
                p10 = grid[(i + 1, j)]
                p01 = grid[(i, j + 1)]
                target.tri(p00, p10, p01, color)
                if i + j < resolution - 1:
                    p11 = grid[(i + 1, j + 1)]
                    target.tri(p10, p11, p01, color)


def emit_micro_drains(op: Batch, tr: Batch, layer, ctx: DomeContext, t: float) -> None:
    alpha = layer.opacity
    color = tint(layer.get("tint"), alpha)
    bore = float(layer.get("bore"))
    spout = float(layer.get("spout"))
    target = tr if alpha < 0.999 else op
    panel = _find(ctx, "panels")
    dish = float(panel.get("dish")) if panel else 0.0
    lift = float(panel.get("lift")) if panel else 0.0
    for face in ctx.faces:
        centre = ctx.face_centroid_unit(face)
        low = centre * ((ctx.radius + lift) * (1.0 - dish))
        if ctx.hidden(low):
            continue
        target.cylinder(low, low - centre * spout, bore, color, sides=9)
        target.disc(low - centre * spout, bore * 1.25, _shade(color, 0.6), sides=9)


def _vein_frames(ctx: DomeContext, a: int, b: int, radius: float, samples: int):
    """Sample points along a seam plus a local frame at each, so a channel
    can be swept along the dome's actual curvature."""
    points = ctx.arc(a, b, radius, samples)
    frames = []
    for index, point in enumerate(points):
        radial = normalize(point)
        if index == 0:
            tangent = points[1] - points[0]
        elif index == len(points) - 1:
            tangent = points[-1] - points[-2]
        else:
            tangent = points[index + 1] - points[index - 1]
        tangent = normalize(tangent)
        side = normalize(np.cross(tangent, radial))
        frames.append((point, radial, side))
    return frames


def emit_veins(op: Batch, tr: Batch, layer, ctx: DomeContext, t: float) -> None:
    """The headline layer: an open channel running along the inside of every
    seam, standing off from the outer skin by a deliberate gap."""
    alpha = layer.opacity
    color = tint(layer.get("tint"), alpha)
    gap = float(layer.get("gap"))
    bore = float(layer.get("bore"))
    wrap = float(layer.get("wrap"))
    segments = max(3, int(layer.get("segments")))
    samples = max(2, int(layer.get("samples")))
    target = tr if alpha < 0.999 else op
    # The channel's spine sits a clear `gap` inside the skin, plus its own
    # radius, so `gap` really is empty inspectable space.
    spine_radius = ctx.radius - gap - bore
    span = TAU * wrap
    for a, b in ctx.edges:
        frames = _vein_frames(ctx, a, b, spine_radius, samples)
        if ctx.hidden(frames[len(frames) // 2][0]):
            continue
        rings = []
        for point, radial, side in frames:
            ring = []
            for s in range(segments + 1):
                # Sweep centred on -radial, so the channel's mouth opens
                # outward toward the seam it is catching water from.
                angle = -span * 0.5 + span * s / segments
                offset = (math.cos(angle) * -radial + math.sin(angle) * side)
                ring.append(point + offset * bore)
            rings.append(ring)
        for i in range(len(rings) - 1):
            for s in range(segments):
                p00, p01 = rings[i][s], rings[i][s + 1]
                p10, p11 = rings[i + 1][s], rings[i + 1][s + 1]
                # Emitted both ways round: a gutter is genuinely open, so it
                # has to read correctly from inside and outside the dome.
                target.quad(p00, p10, p11, p01, color)
                target.quad(p01, p11, p10, p00, color)


def _downhill(ctx: DomeContext, a: int, b: int) -> tuple[int, int]:
    """Order a seam's endpoints so water runs from the higher one to the
    lower one."""
    return (a, b) if ctx.points[a][2] >= ctx.points[b][2] else (b, a)


def emit_vein_water(op: Batch, tr: Batch, layer, ctx: DomeContext, t: float) -> None:
    alpha = layer.opacity
    color = tint(layer.get("tint"), alpha)
    speed = float(layer.get("speed"))
    density = max(1, int(layer.get("density")))
    size = float(layer.get("size"))
    vein = _find(ctx, "veins")
    gap = float(vein.get("gap")) if vein else 0.16
    bore = float(vein.get("bore")) if vein else 0.075
    spine_radius = ctx.radius - gap - bore
    for index, (ea, eb) in enumerate(ctx.edges):
        high, low = _downhill(ctx, ea, eb)
        ua, ub = ctx.unit[high], ctx.unit[low]
        for d in range(density):
            phase = (t * speed + rnd(index * 7.0 + d * 3.0)) % 1.0
            point = _slerp(ua, ub, phase) * spine_radius
            if ctx.hidden(point):
                continue
            # Ride in the bottom of the channel rather than on its spine.
            point = point - normalize(point) * bore * 0.35
            tr.blob(point, size, color, seed=float(index * 13 + d))


def emit_panel_runoff(op: Batch, tr: Batch, layer, ctx: DomeContext, t: float) -> None:
    alpha = layer.opacity
    color = tint(layer.get("tint"), alpha)
    speed = float(layer.get("speed"))
    density = max(1, int(layer.get("density")))
    size = float(layer.get("size"))
    panel = _find(ctx, "panels")
    dish = float(panel.get("dish")) if panel else 0.0
    lift = float(panel.get("lift")) if panel else 0.0
    radius = ctx.radius + lift
    for index, face in enumerate(ctx.faces):
        centre = ctx.face_centroid_unit(face)
        corners = [ctx.unit[i] for i in face]
        for d in range(density):
            phase = (t * speed + rnd(index * 5.0 + d * 11.0)) % 1.0
            start = corners[d % 3]
            # Slide from a corner to the dish's low point, then vanish into
            # the drain and restart -- that is the whole runoff story.
            direction = normalize(start * (1.0 - phase) + centre * phase)
            bowl = 27.0 * (1 / 3) * (1 / 3) * (1 / 3)  # depth at the centroid
            depth = dish * bowl * phase
            point = direction * (radius * (1.0 - depth))
            if ctx.hidden(point):
                continue
            tr.blob(point, size * (1.0 - 0.35 * phase), color,
                    seed=float(index * 17 + d))


def emit_shell(op: Batch, tr: Batch, layer, ctx: DomeContext, t: float) -> None:
    """A continuous dome surface at an arbitrary depth -- liner, barrier, or
    insulation, depending on where you put it and how thick you make it."""
    alpha = layer.opacity
    color = tint(layer.get("tint"), alpha)
    offset = float(layer.get("offset"))
    thickness = float(layer.get("thickness"))
    rings = max(3, int(layer.get("rings")))
    target = tr if (alpha < 0.999 or layer.spec.translucent) else op
    radii = [ctx.radius + offset]
    if thickness > 1e-6:
        radii.append(ctx.radius + offset - thickness)
    for radius in radii:
        if radius <= 0.05:
            continue
        segments = rings * 3
        for i in range(rings):
            for j in range(segments):
                t0, t1 = i / rings, (i + 1) / rings
                a0 = TAU * j / segments
                a1 = TAU * (j + 1) / segments

                def pt(tt, aa, r=radius):
                    polar = (math.pi * 0.5) * tt
                    z = math.sin(polar)
                    ring_r = math.cos(polar)
                    return (r * ring_r * math.cos(aa),
                            r * ring_r * math.sin(aa),
                            r * z)

                p00, p01 = pt(t0, a0), pt(t0, a1)
                p10, p11 = pt(t1, a0), pt(t1, a1)
                if ctx.hidden(p00):
                    continue
                target.quad(p00, p01, p11, p10, color)
                target.quad(p10, p11, p01, p00, color)


def emit_collector_ring(op: Batch, tr: Batch, layer, ctx: DomeContext, t: float) -> None:
    alpha = layer.opacity
    color = tint(layer.get("tint"), alpha)
    bore = float(layer.get("bore"))
    drop = float(layer.get("drop"))
    inset = float(layer.get("inset"))
    target = tr if alpha < 0.999 else op
    radius = ctx.base_radius - inset
    steps = 72
    for i in range(steps):
        a0 = TAU * i / steps
        a1 = TAU * (i + 1) / steps
        p0 = (radius * math.cos(a0), radius * math.sin(a0), drop)
        p1 = (radius * math.cos(a1), radius * math.sin(a1), drop)
        if ctx.hidden(p0):
            continue
        target.cylinder(p0, p1, bore, color, sides=7)


def emit_downpipe(op: Batch, tr: Batch, layer, ctx: DomeContext, t: float) -> None:
    alpha = layer.opacity
    color = tint(layer.get("tint"), alpha)
    bore = float(layer.get("bore"))
    azimuth = math.radians(float(layer.get("azimuth")))
    target = tr if alpha < 0.999 else op
    ring = _find(ctx, "collector_ring")
    drop = float(ring.get("drop")) if ring else 0.14
    inset = float(ring.get("inset")) if ring else 0.10
    tank = _find(ctx, "cistern")
    sink = float(tank.get("sink")) if tank else 0.25
    depth = float(tank.get("depth")) if tank else 1.5
    radius = ctx.base_radius - inset
    top = np.array([radius * math.cos(azimuth), radius * math.sin(azimuth), drop])
    knee = np.array([top[0], top[1], -sink - depth * 0.35])
    target.cylinder(top, knee, bore, color, sides=10)
    target.cylinder(knee, np.array([0.0, 0.0, knee[2]]), bore, color, sides=10)


def emit_cistern(op: Batch, tr: Batch, layer, ctx: DomeContext, t: float) -> None:
    alpha = layer.opacity
    color = tint(layer.get("tint"), alpha)
    radius = float(layer.get("radius"))
    depth = float(layer.get("depth"))
    sink = float(layer.get("sink"))
    fill = float(layer.get("fill"))
    top = -sink
    bottom = top - depth
    tr.cylinder((0.0, 0.0, top), (0.0, 0.0, bottom), radius, color, sides=28)
    tr.disc((0.0, 0.0, bottom), radius, _shade(color, 0.7), sides=28, z_normal=-1.0)
    if fill > 0.001:
        level = bottom + depth * fill
        water = tint("water", min(1.0, alpha + 0.35))
        tr.cylinder((0.0, 0.0, bottom + 0.01), (0.0, 0.0, level),
                    radius * 0.97, water, sides=28)
        tr.disc((0.0, 0.0, level), radius * 0.97, _shade(water, 1.2), sides=28)


def emit_rain(op: Batch, tr: Batch, layer, ctx: DomeContext, t: float) -> None:
    alpha = layer.opacity
    color = tint(layer.get("tint"), alpha)
    count = max(1, int(layer.get("count")))
    speed = float(layer.get("speed"))
    spread = float(layer.get("spread")) * ctx.radius
    length = float(layer.get("length"))
    ceiling = ctx.radius * 1.9
    for i in range(count):
        x = (rnd(i, 1.0) * 2.0 - 1.0) * spread
        y = (rnd(i, 2.0) * 2.0 - 1.0) * spread
        fall = (t * speed + rnd(i, 3.0) * 4.0) % 4.0
        z = ceiling - fall * (ceiling / 4.0)
        # Stop a drop once it reaches the shell it would have hit.
        surface = math.hypot(x, y)
        if surface < ctx.radius:
            limit = math.sqrt(max(0.0, ctx.radius ** 2 - surface ** 2))
            if z < limit:
                continue
        elif z < 0.0:
            continue
        tr.cylinder((x, y, z), (x, y, z + length), 0.012, color, sides=4)


EMITTERS = {
    "ground": emit_ground,
    "frame": emit_frame,
    "triangle_frames": emit_triangle_frames,
    "assemblies": emit_assemblies,
    "waist_joints": emit_waist_joints,
    "hubs": emit_hubs,
    "panels": emit_panels,
    "micro_drains": emit_micro_drains,
    "veins": emit_veins,
    "vein_water": emit_vein_water,
    "panel_runoff": emit_panel_runoff,
    "shell": emit_shell,
    "collector_ring": emit_collector_ring,
    "downpipe": emit_downpipe,
    "cistern": emit_cistern,
    "rain": emit_rain,
}


# Emitters that need to agree with a sibling layer (drains sit at the low
# point of whatever the panel layer is doing) read it through here.
_ACTIVE_STACK = {"stack": None}


def _find(ctx: DomeContext, kind: str):
    stack = _ACTIVE_STACK["stack"]
    if stack is None:
        return None
    for layer in stack.layers:
        if layer.kind == kind:
            return layer
    return None


def build_scene(stack, t: float) -> tuple[Batch, Batch]:
    """Build the whole dome for one moment in time.

    Returns (opaque, translucent) batches; the caller draws opaque first
    with depth writes on, then translucent with them off.
    """
    settings = stack.settings
    ctx = DomeContext(
        settings.radius, settings.cut_enabled,
        settings.cut_start, settings.cut_sweep,
    )
    _ACTIVE_STACK["stack"] = stack
    opaque, translucent = Batch(), Batch()
    try:
        for layer in stack.layers:
            if not layer.visible or layer.opacity <= 0.004:
                continue
            emitter = EMITTERS.get(layer.kind)
            if emitter is None:
                continue
            emitter(opaque, translucent, layer, ctx, t)
    finally:
        _ACTIVE_STACK["stack"] = None
    return opaque, translucent


def pick_face(stack, origin, direction) -> int:
    """Which triangle a ray hits first, or -1.

    Uses the Moller-Trumbore test against the dome's own faces, so what
    you click is exactly the face the geometry is built from -- no
    separate pickable proxy that could drift out of step.
    """
    ctx = DomeContext(
        stack.settings.radius, stack.settings.cut_enabled,
        stack.settings.cut_start, stack.settings.cut_sweep,
    )
    origin = np.asarray(origin, dtype=np.float64)
    direction = np.asarray(direction, dtype=np.float64)
    best_index, best_t = -1, float("inf")
    for index, face in enumerate(ctx.faces):
        a, b, c = (ctx.points[i] for i in face)
        if ctx.hidden((a + b + c) / 3.0):
            continue
        edge1, edge2 = b - a, c - a
        pvec = np.cross(direction, edge2)
        det = float(np.dot(edge1, pvec))
        if abs(det) < 1e-12:
            continue
        inv = 1.0 / det
        tvec = origin - a
        u = float(np.dot(tvec, pvec)) * inv
        if u < 0.0 or u > 1.0:
            continue
        qvec = np.cross(tvec, edge1)
        v = float(np.dot(direction, qvec)) * inv
        if v < 0.0 or u + v > 1.0:
            continue
        distance = float(np.dot(edge2, qvec)) * inv
        if 1e-6 < distance < best_t:
            best_t, best_index = distance, index
    return best_index


def face_edge_classes(stack, face_index: int) -> list[str]:
    ctx = DomeContext(stack.settings.radius)
    face = ctx.faces[face_index]
    return [ctx.edge_name(int(face[i]), int(face[(i + 1) % 3]))
            for i in range(3)]


def scene_stats(stack) -> dict:
    """Live counts for the readout, computed from the geometry rather than
    written down anywhere."""
    ctx = DomeContext(stack.settings.radius)
    geo = ctx.geo
    short = next(e for e in geo.edge_classes if e.name == "SHORT")
    long_ = next(e for e in geo.edge_classes if e.name == "LONG")
    return {
        "radius": ctx.radius,
        "base_radius": ctx.base_radius,
        "struts": len(ctx.edges),
        "short_struts": short.hemisphere_count,
        "long_struts": long_.hemisphere_count,
        "panels": len(ctx.faces),
        "hubs": len({int(i) for face in ctx.faces for i in face}),
        "short_len": short.factor * ctx.radius,
        "long_len": long_.factor * ctx.radius,
        "footprint": math.pi * ctx.base_radius ** 2,
        "layers": len(stack.layers),
        "visible": sum(1 for layer in stack.layers if layer.visible),
    }
