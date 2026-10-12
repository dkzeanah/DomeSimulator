"""The two drawings: the triangle seen face-on (plan) and the pieces seen
end-on (section). Both draw through :mod:`infill.draw`, so the viewer, the
SVG sheet and the PNG checks are one drawing."""

from __future__ import annotations

import numpy as np

from . import geom2d as g2
from .draw import PALETTE as P
from .draw import Painter, View
from .patterns import LAYS, MATERIALS, Layout
from .section import POSES

POSE_NAME = {"FDR": "on its face, like the frame", "FUL": "flipped (face to the open side)",
             "FDL": "on its face, point back", "FUR": "flipped, point out",
             "PD": "standing on its point", "PU": "hanging point-up",
             "BD": "board at the flat side", "BU": "board at the open side", "BE": "board on edge",
             "sheet": "sheet", "film": "film", "metal": "metal",
             "full": "whole round", "wall": "round cut along the wall", "graded": "small round in a gap",
             "copy": "copied round, cut to fit the gaps"}


def _fill(pose: str, material: str) -> str:
    if material == "rounds":
        return P.get(pose, P["full"])
    if material in ("osb", "ply"):
        return P["sheet"]
    if material in ("film", "metal"):
        return P[material]
    return P.get(pose, P["FDR"])


def plan(painter: Painter, L: Layout, x: int, y: int, w: int, h: int, numbers: bool = True,
         highlight: int | None = None, from_side: str = "open") -> None:
    """``from_side``: look from the open side (pieces nearest it on top) or
    from the flat side."""
    panel = L.panel
    tri = panel.tri
    pad = panel.spec.radius_in * 0.6
    lo, hi = tri.min(axis=0) - pad, tri.max(axis=0) + pad
    v = View((lo[0], lo[1], hi[0], hi[1]), w, h, margin=30, ox=x, oy=y)
    cover = L.opts.mode == "cover"
    # The frame.
    for m in panel.members():
        painter.poly(v.px(m), fill="#d8c3a8" if cover else P["frame"], outline=P["bark"], width=1)
    painter.poly(v.px(tri), outline=P["muted"], width=1, dash=True)
    if not cover:
        painter.poly(v.px(panel.opening(0.0)), outline=P["ink"], width=1.2)
        painter.poly(v.px(panel.opening(panel.spec.thickness_in)), outline=P["muted"], width=1, dash=True)
    if L.extra and "layers" in L.extra:
        _plan_rounds(painter, L, v, numbers)
        _edge_labels(painter, L, v)
        return
    # The pieces.
    many = len(L.pieces) > 70
    reach = {}
    for p in L.placed:
        reach[id(p)] = (float(p.poly[:, 1].min()), float(p.poly[:, 1].max()))
    order = list(range(len(L.pieces)))
    heights = [_height(p, L) for p in L.pieces]
    if from_side == "open":
        order.sort(key=lambda i: heights[i][1])
    else:
        order.sort(key=lambda i: -heights[i][0])
    for i in order:
        p = L.pieces[i]
        if len(p.plan) < 3:
            continue
        fill = _fill(p.pose, p.material)
        if highlight is not None and i == highlight:
            fill = "#f4d03f"
        painter.poly(v.px(p.plan), fill=fill, outline=P["ink"] if not many else "#6b5a45",
                     width=0.6 if many else 1.0)
    if L.remainder is not None:
        painter.poly(v.px(L.remainder), fill=P["plug"], outline=P["ink"], width=1)
    # Numbers on the pieces.
    if numbers and len(L.pieces) <= 60:
        for i, p in enumerate(L.pieces):
            if len(p.plan) < 3 or g2.area(p.plan) < 4:
                continue
            c = p.plan.mean(axis=0)
            cx, cy = v.pt(*c)
            painter.text(cx, cy, str(i + 1), P["ink"], 10, "mm", bold=True)
    _edge_labels(painter, L, v)


def _edge_labels(painter: Painter, L: Layout, v: View) -> None:
    panel = L.panel
    # Edges: class and length, outside the frame; the reference edge marked.
    for k in range(3):
        a, b = panel.edge(k)
        mid = (a + b) / 2 - panel.inward(k) * (panel.spec.radius_in * 0.75)
        mx, my = v.pt(*mid)
        mark = "  ◄ runs laid from here" if (k == L.opts.edge and L.opts.arrangement in
                                              ("parallel", "louvers", "chevron", "strips")) else ""
        painter.text(mx, my, f"{panel.edge_class[k].lower()} edge {panel.edge_len[k]:.1f} in{mark}",
                     P["muted"], 10, "mm")


def _layer_clip(L: Layout, layer) -> np.ndarray:
    if L.opts.mode == "fill":
        return L.panel.opening((layer.z0 + layer.z1) / 2)
    return L.clip


def _plan_rounds(painter: Painter, L: Layout, v: View, numbers: bool) -> None:
    """One layer of rounds face-on: the gaps (cut to fit, or open), the
    copied rounds they are cut from (dashed), the layer below (faint), and
    the rounds themselves with their growth rings."""
    from .rounds import circle
    ls = L.extra["layers"]
    k = max(0, min(L.opts.layer - 1, len(ls) - 1))
    layer = ls[k]
    clip = _layer_clip(L, layer)
    painter.poly(v.px(clip), fill=P["cutfit"] if L.extra["cut"] else P["air"], outline=P["ink"], width=1)
    if k > 0:
        for r in ls[k - 1].rounds:
            painter.poly(v.px(g2.clip_convex(circle(r.c, r.r), clip)), outline="#a8957a", width=0.8, dash=True)
    for r in layer.copies:
        painter.poly(v.px(g2.clip_convex(r.poly, clip)), outline=P["cut"], width=0.9, dash=True)
    for r in layer.rounds:
        painter.poly(v.px(r.poly), fill=P[r.kind], outline=P["bark"], width=1.2)
        if r.kind != "wall":
            for f in (0.66, 0.33):
                painter.poly(v.px(circle(r.c, r.r * f, 32)), outline=P["ring"], width=0.6)
    x0, y0 = v.pt(L.panel.tri[:, 0].min(), L.panel.tri[:, 1].max())
    painter.text(x0, y0 - 22, f"Layer {k + 1} of {len(ls)}, {layer.z0:.2f}–{layer.z1:.2f} in up",
                 P["ink"], 11, "lt", bold=True)
    painter.text(x0, y0 - 6, f"pattern covers {100 * (1 - layer.gaps_in2 / layer.open_in2):.0f}%"
                 + (f", cut to fit {100 * (1 - layer.void_in2 / layer.open_in2):.1f}%" if L.extra["cut"] else ""),
                 P["muted"], 10, "lt")


def _section_rounds(painter: Painter, L: Layout, x: int, y: int, w: int, h: int) -> None:
    """End-on through the middle of the triangle: every layer, the rounds it
    cuts through, the cut-to-fit pieces between, the frame's walls."""
    ls = L.extra["layers"]
    T = L.T
    panel = L.panel
    R = panel.spec.radius_in
    ymid = float(panel.opening(0.0)[:, 1].mean())

    def span_at(z):
        poly = panel.opening(z) if L.opts.mode == "fill" else L.clip
        chord = g2.clip_convex(g2.strip((0.0, ymid), (1.0, 0.0), (0.0, 1.0), -1e-4, 1e-4), poly)
        return (float(chord[:, 0].min()), float(chord[:, 0].max())) if len(chord) else (0.0, 0.0)
    xl0, _ = span_at(0.0)
    xlT, _ = span_at(T)
    top = ls[-1].z1 if L.opts.mode == "fill" else T + ls[-1].z1
    v = View((xl0 - R, -0.6, xl0 + 30.0, top + 0.8), w, h, margin=22, ox=x, oy=y)
    base = 0.0 if L.opts.mode == "fill" else T
    for layer in ls:
        z0, z1 = base + layer.z0, base + layer.z1
        a, b = span_at(min((layer.z0 + layer.z1) / 2, T))
        b = min(b, xl0 + 30.0)
        painter.poly(v.px([(a, z0), (b, z0), (b, z1), (a, z1)]),
                     fill=P["cutfit"] if L.extra["cut"] else P["air"], outline=P["muted"], width=0.6)
        for r in layer.rounds:
            dy = abs(r.c[1] - ymid)
            if dy >= r.r:
                continue
            half = (r.r * r.r - dy * dy) ** 0.5
            xa, xb = max(a, r.c[0] - half), min(b, r.c[0] + half)
            if xb > xa:
                painter.poly(v.px([(xa, z0), (xb, z0), (xb, z1), (xa, z1)]), fill=P[r.kind],
                             outline=P["bark"], width=1)
    if L.opts.mode == "fill":
        painter.poly(v.px([(xl0 - R, 0.0), (xl0, 0.0), (xlT, T), (xl0 - R, T)]), fill=P["frame"],
                     outline=P["bark"], width=1.2)
    else:
        painter.poly(v.px([(xl0 - R, 0.0), (xl0 + 30, 0.0), (xl0 + 30, T), (xl0 - R, T)]), fill="#d8c3a8",
                     outline=P["bark"], width=1)
    fx, fy = v.pt(xl0 - R * 0.5, 0.4)
    painter.text(fx, fy, "frame", "#f7f3ea", 10, "mm", bold=True)
    sx, sy = v.pt(xl0 - R, -0.35)
    ex, _ = v.pt(xl0 - R + 1.0, -0.35)
    painter.line([(sx, sy), (ex, sy)], P["ink"], 2)
    painter.text(ex + 4, sy, "1 in  (cut through the middle of the triangle)", P["muted"], 9, "lm")


def _height(piece, L: Layout) -> tuple[float, float]:
    """How near the flat side and the open side a piece reaches, from its pose."""
    T = L.T
    if piece.pose in ("FUL", "FUR", "PU", "BU"):
        return (T * 0.5, T + L.z0)
    if piece.pose in ("FDR", "FDL", "PD", "BD"):
        return (L.z0, T * 0.5 + L.z0)
    return (L.z0, T + L.z0)


def section(painter: Painter, L: Layout, x: int, y: int, w: int, h: int) -> None:
    """End-on: the frame member at the left, the first pieces packed against it."""
    if L.extra and "layers" in L.extra:
        _section_rounds(painter, L, x, y, w, h)
        return
    T = L.T
    spec = L.panel.spec
    R = spec.radius_in
    kind = MATERIALS[L.opts.material][1]
    z_top = T + (max((float(p.poly[:, 1].max()) for p in L.placed), default=T) - T if L.opts.mode == "cover" else 0)
    z_top = max(z_top, T)
    span = R * 3.4
    v = View((-R * 1.05, -0.6, span, z_top + 0.9), w, h, margin=26, ox=x, oy=y)
    # The thickness of the frame, as air.
    painter.poly(v.px([(-R, 0), (span, 0), (span, T), (-R, T)]), fill=P["air"])
    painter.line(v.px([(-R, 0), (span, 0)]), P["muted"], 1)
    painter.line(v.px([(-R, T), (span, T)]), P["muted"], 1, dash=True)
    fx, fy = v.pt(span, 0)
    painter.text(fx - 4, fy + 10, "flat side", P["muted"], 10, "rm")
    fx, fy = v.pt(span, T)
    painter.text(fx - 4, fy - 10, "open side", P["muted"], 10, "rm")
    if L.wall is not None:
        painter.poly(v.px(L.wall), fill=P["frame"], outline=P["bark"], width=1.2)
        wx, wy = v.pt(-R * 0.55, T * 0.18)
        painter.text(wx, wy, "frame", "#f7f3ea", 10, "mm", bold=True)
    if kind in ("log", "board"):
        for p in L.placed:
            if p.x_lo > span:
                break
            painter.poly(v.px(p.poly), fill=_fill(p.pose, L.opts.material), outline=P["bark"], width=1)
        # Pitch dimension under the first repeat.
        m = L.metrics
        if m.get("pitch") and L.placed:
            per = m.get("per_period", 1) or 1
            if len(L.placed) > per:
                a = L.placed[0].x_lo
                b = a + m["pitch"]
                yy = -0.35
                painter.line(v.px([(a, yy), (b, yy)]), P["cut"], 1.4)
                for xx in (a, b):
                    painter.line(v.px([(xx, yy - 0.12), (xx, yy + 0.12)]), P["cut"], 1.4)
                tx, ty = v.pt((a + b) / 2, yy)
                painter.text(tx, ty + 9, f"repeat {m['pitch']:.2f} in", P["cut"], 10, "mt")
    elif kind in ("sheet", "film"):
        t = {"osb": 0.4375, "ply": 0.71875, "film": 0.05}[L.opts.material]
        if L.opts.mode == "fill":
            top = T if (L.opts.flush == "open" or kind == "film") else t
            base = top - t
            # The slab rests on the 45° wall: its edge is bevelled to match.
            x0b, x0t = -base, -top
            painter.poly(v.px([(x0b, base), (span, base), (span, top), (x0t, top)]),
                         fill=_fill("sheet", L.opts.material), outline=P["ink"], width=1)
            if kind == "film":
                painter.line(v.px([(x0t, top), (0.0, 0.0)]), P["vent"], 2.0)
        else:
            painter.poly(v.px([(-R, T), (span, T), (span, T + t), (-R, T + t)]),
                         fill=_fill("sheet", L.opts.material), outline=P["ink"], width=1)
    elif kind == "metal":
        xs = np.linspace(-R if L.opts.mode == "cover" else 0, span, 200)
        base = T if L.opts.mode == "cover" else T - 0.5
        zs = base + 0.25 + 0.25 * np.sin(xs * 2 * np.pi / 2.67)
        painter.line(v.px(np.c_[xs, zs]), P["ink"], 2)
    # A scale: 1 inch.
    sx, sy = v.pt(-R, -0.45)
    ex, _ = v.pt(-R + 1.0, -0.45)
    painter.line([(sx, sy), (ex, sy)], P["ink"], 2)
    painter.text(ex + 4, sy, "1 in", P["muted"], 9, "lm")


def legend(painter: Painter, L: Layout, x: int, y: int) -> int:
    seen = []
    for p in L.pieces:
        key = p.pose
        if key not in seen and key != "copy":
            seen.append(key)
    yy = y
    for key in seen:
        painter.rect(x, yy, x + 14, yy + 12, fill=_fill(key, L.opts.material), outline=P["ink"])
        painter.text(x + 20, yy + 6, POSE_NAME.get(key, key), P["ink"], 10, "lm")
        yy += 18
    if L.extra and "layers" in L.extra:
        key, text = ("cutfit", "gap, cut to fit from a copied round") if L.extra["cut"] else \
            ("air", "gap, left open")
        painter.rect(x, yy, x + 14, yy + 12, fill=P[key], outline=P["ink"])
        painter.text(x + 20, yy + 6, text, P["ink"], 10, "lm")
        yy += 18
        painter.line([(x, yy + 6), (x + 14, yy + 6)], P["cut"], 1.2, dash=True)
        painter.text(x + 20, yy + 6, "a copied round, laid over the gaps", P["ink"], 10, "lm")
        yy += 18
    if L.remainder is not None:
        painter.rect(x, yy, x + 14, yy + 12, fill=P["plug"], outline=P["ink"])
        painter.text(x + 20, yy + 6, "centre left over (plug or vent)", P["ink"], 10, "lm")
        yy += 18
    return yy


def sheet_png(L: Layout, path, w: int = 1600, h: int = 900) -> str:
    """Plan, section and legend on one image."""
    from .draw import PilPainter
    p = PilPainter(w, h)
    p.text(20, 20, L.title, P["ink"], 20, "lt", bold=True)
    lay = f" — {LAYS[L.opts.lay][1]}" if L.opts.lay else ""
    p.text(20, 50, f"{L.panel.label}, {L.opts.mode}{lay}"[:150], P["muted"], 13, "lt")
    plan(p, L, 10, 80, int(w * 0.55), h - 90)
    section(p, L, int(w * 0.56), 80, int(w * 0.43), int(h * 0.45))
    legend(p, L, int(w * 0.58), int(h * 0.58))
    p.img.save(str(path))
    return str(path)
