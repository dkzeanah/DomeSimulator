"""The book's drawings: cross-sections to scale, from the same geometry as its
tables. Each returns an inline SVG; one unit is one inch of wood."""

from __future__ import annotations

import html
import math

from . import geometry as g
from . import tokens

S = 22.0          # drawing units per inch of wood
E = html.escape


def _pt(x: float, y: float, ox: float, oy: float) -> str:
    """Wood inches (y up) to drawing units (y down)."""
    return f"{ox + x * S:.1f},{oy - y * S:.1f}"


def _poly(points, ox, oy, cls) -> str:
    return f'<polygon class="{cls}" points="{" ".join(_pt(x, y, ox, oy) for x, y in points)}"/>'


def _text(x, y, ox, oy, s, cls="lab", anchor="middle") -> str:
    return (f'<text class="{cls}" x="{ox + x * S:.1f}" y="{oy - y * S:.1f}" '
            f'text-anchor="{anchor}">{E(s)}</text>')


def _svg(w_in: float, h_in: float, body: str, label: str) -> str:
    return (f'<svg class="fig" viewBox="0 0 {w_in * S:.0f} {h_in * S:.0f}" role="img" '
            f'aria-label="{E(label)}">{body}</svg>')


def _rot(points, deg, cx=0.0, cy=0.0):
    a = math.radians(deg)
    out = []
    for x, y in points:
        x0, y0 = x - cx, y - cy
        out.append((cx + x0 * math.cos(a) - y0 * math.sin(a), cy + x0 * math.sin(a) + y0 * math.cos(a)))
    return out


def triangle(w: g.Wedge, eff: bool = True):
    """The trimmed wedge with its point at the origin, opening along +x."""
    r = w.r_eff if eff else w.r
    t = math.radians(w.theta)
    return [(0.0, 0.0), (r, 0.0), (r * math.cos(t), r * math.sin(t))]


def slant_pair(w: g.Wedge):
    """Two wedges mated on a radial face, one turned end for end: the skewed board."""
    a, b, c = triangle(w)
    # the second is the first turned half a turn about the middle of the shared face a-b
    mx, my = (a[0] + b[0]) / 2, (a[1] + b[1]) / 2
    c2 = (2 * mx - c[0], 2 * my - c[1])
    return [a, c2, b, c], (a, b, c), (b, a, c2)


def upright_pair(w: g.Wedge):
    """The slant pair stood on its long side: (wedge one, wedge two, planed
    rectangle as x0, x1, height). The rectangle is the overlap of the bottom and
    top faces, square to them -- the largest board cut square to the long side --
    less the planing allowance on every face."""
    quad, t1, t2 = slant_pair(w)
    a, _b, c = t1
    ang = -math.degrees(math.atan2(c[1] - a[1], c[0] - a[0]))
    t1, t2 = _rot(t1, ang), _rot(t2, ang)
    pts = t1 + t2
    base = t1[0][1]
    if sum(y - base for _, y in pts) < 0:
        t1, t2 = [(x, 2 * base - y) for x, y in t1], [(x, 2 * base - y) for x, y in t2]
    pts = t1 + t2
    minx = min(x for x, _ in pts)
    t1 = [(x - minx, y - base) for x, y in t1]
    t2 = [(x - minx, y - base) for x, y in t2]
    pts = t1 + t2
    h = max(y for _, y in pts)
    bottom = [x for x, y in pts if abs(y) < 1e-6]
    top = [x for x, y in pts if abs(y - h) < 1e-6]
    x0, x1 = max(min(bottom), min(top)), min(max(bottom), max(top))
    k = g.D["plane_in"]
    return t1, t2, (x0 + k, x1 - k, k, h - k)


def fig_log() -> str:
    d = g.D["reference_log_in"]
    r = d / 2
    ox, oy = (r + 0.6) * S, (r + 0.6) * S
    body = [f'<circle class="bark" cx="{ox:.1f}" cy="{oy:.1f}" r="{r * S:.1f}"/>']
    w = g.Wedge(d, 8)
    body.append(_poly(triangle(w, eff=False), ox, oy, "pick"))
    for k in range(4):
        a = math.radians(45 * k)
        x, y = r * math.cos(a), r * math.sin(a)
        body.append(f'<line class="kerf" x1="{ox - x * S:.1f}" y1="{oy + y * S:.1f}" '
                    f'x2="{ox + x * S:.1f}" y2="{oy - y * S:.1f}" stroke-width="{g.D["kerf_in"] * S:.1f}"/>')
    body.append(f'<circle class="pith" cx="{ox:.1f}" cy="{oy:.1f}" r="3"/>')
    body.append(_text(r * 0.66, r * 0.2, ox, oy, f"{w.theta:.0f}°", "val"))
    return _svg(d + 1.2, d + 1.2, "".join(body), "A round log split eight ways through its centre")


def fig_slant() -> str:
    w = g.Wedge(g.D["reference_log_in"], 8)
    p = g.Pair(w, "slant")
    t1, t2, (x0, x1, y0, y1) = upright_pair(w)
    pts = t1 + t2
    width = max(x for x, _ in pts)
    h = max(y for _, y in pts)
    ox, oy = 1.4 * S, (h + 0.9) * S
    body = [_poly(t1, ox, oy, "wood"), _poly(t2, ox, oy, "wood2"),
            _poly([(x0, y0), (x1, y0), (x1, y1), (x0, y1)], ox, oy, "plane"),
            _text((x0 + x1) / 2, (y0 + y1) / 2 - 0.1, ox, oy, f"{x1 - x0:.2f} in square", "val")]
    # the corners
    acute = min(pts, key=lambda q: (q[1], q[0]))
    body.append(_text(acute[0] + 0.55, acute[1] + 0.25, ox, oy, f"{p.acute:.1f}°"))
    body.append(_text(width / 2, -0.55, ox, oy, f"{p.sides[0]:.2f} in", "lab"))
    return _svg(width + 2.8, h + 1.6, "".join(body),
                "Two wedges mated slant to slant make a skewed board that planes to a square")


def fig_back() -> str:
    q = g.Wedge(g.D["reference_log_in"], 4)
    e = g.Wedge(g.D["reference_log_in"], 8)
    body = []
    r = q.r_eff
    ox, oy = 0.8 * S, (r + 0.9) * S
    body.append(_poly([(0, 0), (r, 0), (0, r)], ox, oy, "wood"))
    body.append(_poly([(r, 0), (r, r), (0, r)], ox, oy, "wood2"))
    body.append(_text(r / 2, -0.5, ox, oy, f"{r:.2f} in", "val"))
    tri = triangle(e)
    bx, by = tri[1]
    cx, cy = tri[2]
    dx, dy = cx - bx, cy - by
    n2 = dx * dx + dy * dy
    ax, ay = tri[0]
    k = ((ax - bx) * dx + (ay - by) * dy) / n2
    fx, fy = bx + k * dx, by + k * dy
    mirror = (2 * fx - ax, 2 * fy - ay)
    rot = -e.theta / 2
    t1 = _rot(tri, rot)
    t2 = _rot([tri[1], mirror, tri[2]], rot)
    ox2 = ox + (r + 1.6) * S
    oy2 = oy - r * S / 2
    body.append(_poly(t1, ox2, oy2, "wood"))
    body.append(_poly(t2, ox2, oy2, "wood2"))
    width = r + 1.6 + 2 * e.depth + 1.4
    return _svg(width, r + 1.5, "".join(body), "Quarters back to back make a true square; eighths make a diamond")


def fig_tradeoff() -> str:
    ref = g.D["reference_log_in"]
    body = []
    x0 = 0.5
    tallest = max(max(y for _, y in sum(upright_pair(g.Wedge(ref, n))[:2], [])) for n in (6, 8, 12, 16))
    for n in (6, 8, 12, 16):
        w = g.Wedge(ref, n)
        t1, t2, (rx0, rx1, ry0, ry1) = upright_pair(w)
        wid = max(x for x, _ in t1 + t2)
        ox, oy = x0 * S, (tallest + 0.4) * S
        body.append(_poly(t1, ox, oy, "wood"))
        body.append(_poly(t2, ox, oy, "wood2"))
        body.append(_poly([(rx0, ry0), (rx1, ry0), (rx1, ry1), (rx0, ry1)], ox, oy, "plane"))
        body.append(_text(wid / 2, -0.55, ox, oy, f"{n} ways", "lab"))
        body.append(_text(wid / 2, -1.1, ox, oy, f"{rx1 - rx0:.2f} x {ry1 - ry0:.2f} in", "val"))
        x0 += wid + 0.9
    return _svg(x0, tallest + 1.9, "".join(body), "Pairs from finer splits are flatter and closer to boards")


def fig_shim() -> str:
    w = g.Wedge(g.D["reference_log_in"], 8)
    tri = triangle(w)
    # lay it on its back: rotate so the chord b-c is horizontal and the point is up
    b, c = tri[1], tri[2]
    ang = -math.degrees(math.atan2(c[1] - b[1], c[0] - b[0]))
    pts = _rot(tri, ang)
    if pts[0][1] < pts[1][1]:
        pts = [(x, -y) for x, y in pts]
    miny = min(y for _, y in pts)
    minx = min(x for x, _ in pts)
    pts = [(x - minx + 2.6, y - miny) for x, y in pts]
    point, b2, c2 = pts
    left = b2 if b2[0] < c2[0] else c2
    # the shim fills between the left radial face and a plumb line from the left corner
    shim = [left, (left[0], point[1]), point]
    ox, oy = 0.5 * S, (point[1] + 1.0) * S
    body = [_poly(pts, ox, oy, "wood"), _poly(shim, ox, oy, "shim"),
            f'<line class="plumb" x1="{ox + left[0] * S:.1f}" y1="{oy - (point[1] + 0.6) * S:.1f}" '
            f'x2="{ox + left[0] * S:.1f}" y2="{oy + 0.3 * S:.1f}"/>',
            _text(left[0] - 0.2, point[1] / 2, ox, oy, f"{w.shim_angle:.1f}° shim", "val", "end"),
            _text((point[0] + c2[0]) / 2 + 1.2, point[1] / 2, ox, oy, "face now plumb", "lab", "start")]
    width = max(x for x, _ in pts) + 2.5
    return _svg(width + 2.0, point[1] + 1.8, "".join(body),
                "A wedge on its back, with a thin wedge as a shim, presents a plumb face")


def fig_octagon() -> str:
    d = g.D["reference_log_in"]
    w = g.Wedge(d, 8)
    r = w.r_eff * 1.6
    ox = oy = (r + 1.0) * S
    body = []
    for k in range(8):
        tri = _rot([(0, 0), (r, 0), (r * math.cos(math.radians(45)), r * math.sin(math.radians(45)))], 45 * k)
        body.append(_poly(tri, ox, oy, "wood" if k % 2 else "wood2"))
    return _svg(2 * r + 2, 2 * r + 2, "".join(body), "Eight trimmed wedges make an octagon")


def fig_keyed_seam() -> str:
    w = g.Wedge(g.D["reference_log_in"], 8)
    tri = triangle(w)
    # two wedges side by side on their backs, their radial faces opening a V between them
    b, c = tri[1], tri[2]
    ang = -math.degrees(math.atan2(c[1] - b[1], c[0] - b[0]))
    t = _rot(tri, ang)
    if t[0][1] < t[1][1]:
        t = [(x, -y) for x, y in t]
    miny = min(y for _, y in t)
    minx = min(x for x, _ in t)
    t = [(x - minx, y - miny) for x, y in t]
    width = max(x for x, _ in t)
    gap = 0.25
    t2 = [(x + width + gap, y) for x, y in t]
    left_face_top = max(t, key=lambda p: p[1])
    right_top = max(t2, key=lambda p: p[1])
    key = [(width, 0.0), (width + gap, 0.0), (right_top[0], right_top[1] * 0.35),
           (left_face_top[0], left_face_top[1] * 0.35)]
    ox, oy = 0.6 * S, (left_face_top[1] + 0.9) * S
    body = [_poly(t, ox, oy, "wood"), _poly(t2, ox, oy, "wood2"),
            _poly([(left_face_top[0], left_face_top[1]), (width, 0), (width + gap, 0),
                   (right_top[0], right_top[1])], ox, oy, "seam"),
            _text(width + gap / 2, left_face_top[1] + 0.35, ox, oy, "the V between them is a channel", "val")]
    return _svg(2 * width + gap + 1.2, left_face_top[1] + 1.7, "".join(body),
                "Two wedges on their backs leave a V-shaped channel between them")


def fig_recovery() -> str:
    t = tokens.table()
    rows = [("Split, as it comes off the log", float(t["sq.split_pct"]), "ours"),
            ("Backs trimmed flat", float(t["sq.tri_pct"]), "ours"),
            (f"Paired, {t['sq.best_n']} ways, planed to boards", float(t["sq.best_kept"]), "ours"),
            ("Sawn into 2x4s (the simulator's mill)", float(t["sq.sawn_pct"]), "them"),
            ("Paired eighths, planed square", float(t["sq.squares_pct"]), "soft")]
    width, row_h = 340.0, 26.0
    out = [f'<svg class="fig" viewBox="0 0 {width:.0f} {row_h * len(rows) + 8:.0f}" role="img" '
           f'aria-label="How much of a {t["sq.log"]} inch log each way of working keeps">']
    for i, (label, pct, cls) in enumerate(rows):
        y = i * row_h + 4
        bw = (width - 60) * pct / 100
        out.append(f'<text class="lab" x="0" y="{y + 9:.1f}" text-anchor="start">{E(label)}</text>')
        out.append(f'<rect class="{cls}" x="0" y="{y + 12:.1f}" width="{bw:.1f}" height="9" rx="1.5"/>')
        out.append(f'<text class="val" x="{bw + 4:.1f}" y="{y + 20:.1f}" text-anchor="start">{pct:.0f}%</text>')
    out.append("</svg>")
    return "".join(out)


FIGURES = {
    "log": fig_log, "slant": fig_slant, "back": fig_back, "tradeoff": fig_tradeoff,
    "shim": fig_shim, "octagon": fig_octagon, "seam": fig_keyed_seam, "recovery": fig_recovery,
}

CSS = """
svg.fig { display: block; margin: .12in auto .04in; max-width: 100%; height: auto; max-height: 3.4in; }
svg.fig .bark { fill: var(--bark); stroke: var(--ink); stroke-width: 1; }
svg.fig .wood { fill: var(--wood-1); stroke: var(--ink); stroke-width: 1; }
svg.fig .wood2 { fill: var(--wood-2); stroke: var(--ink); stroke-width: 1; }
svg.fig .pick { fill: var(--wood-2); stroke: none; }
svg.fig .kerf { stroke: var(--paper); }
svg.fig .pith { fill: var(--ink); }
svg.fig .plane { fill: none; stroke: var(--accent); stroke-width: 1.6; stroke-dasharray: 5 3; }
svg.fig .shim { fill: var(--accent-soft); stroke: var(--ink); stroke-width: 1; }
svg.fig .seam { fill: var(--water); stroke: none; }
svg.fig .plumb { stroke: var(--ink); stroke-width: 1; stroke-dasharray: 2 2; }
svg.fig .lab { font: 10px "Segoe UI", system-ui, sans-serif; fill: var(--ink-2); }
svg.fig .val { font: 700 10px "Segoe UI", system-ui, sans-serif; fill: var(--ink); }
svg.fig rect.ours { fill: var(--accent); } svg.fig rect.them { fill: var(--muted); }
svg.fig rect.soft { fill: var(--accent-soft); }
"""
