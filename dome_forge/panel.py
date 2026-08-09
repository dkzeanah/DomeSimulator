"""Assemble one triangular panel: three struts plus a fill.

The three edges are treated independently on purpose. A real build often
mixes sections -- a split log on the long edge, a 2x2 on the short ones --
and mixing them changes the geometry, not just the colour: struts of
different widths push their inner faces in by different amounts, so the
opening in the middle is no longer a neatly scaled-down triangle. The
inner outline here is therefore built by intersecting each edge's own
offset line with its neighbour's, which is correct whether the three
widths match or not.

Everything is computed in the panel's own flat plane and lifted back into
3D at the end, so the same code serves a face of the dome and a single
panel sitting on a bench in the Panel Creator.
"""

from __future__ import annotations

import math

import numpy as np

from presenter.world import Batch

from .catalog import (FILL_BY_KEY, PROFILE_BY_KEY, PanelFill, Section,
                      StrutProfile, oriented_profile)


# ---------------------------------------------------------------------------
# Flat-plane helpers
# ---------------------------------------------------------------------------

def plane_basis(a, b, c):
    """An orthonormal frame for the plane through three points."""
    a = np.asarray(a, dtype=np.float64)
    b = np.asarray(b, dtype=np.float64)
    c = np.asarray(c, dtype=np.float64)
    normal = np.cross(b - a, c - a)
    length = float(np.linalg.norm(normal))
    normal = normal / length if length > 1e-12 else np.array([0.0, 0.0, 1.0])
    if float(np.dot(normal, (a + b + c) / 3.0)) < 0.0:
        normal = -normal
    e1 = b - a
    e1 = e1 / max(1e-12, float(np.linalg.norm(e1)))
    e2 = np.cross(normal, e1)
    return a, e1, e2, normal


def to_2d(point, origin, e1, e2):
    delta = np.asarray(point, dtype=np.float64) - origin
    return np.array([float(np.dot(delta, e1)), float(np.dot(delta, e2))])


def to_3d(point2d, origin, e1, e2, lift: float = 0.0, normal=None):
    out = origin + e1 * float(point2d[0]) + e2 * float(point2d[1])
    if lift and normal is not None:
        out = out + normal * lift
    return out


def _inward_normal(p0, p1, centroid):
    direction = p1 - p0
    length = float(np.linalg.norm(direction))
    if length < 1e-12:
        return np.array([0.0, 0.0])
    direction = direction / length
    perp = np.array([-direction[1], direction[0]])
    if float(np.dot(perp, centroid - p0)) < 0.0:
        perp = -perp
    return perp


def _line_intersect(p0, d0, p1, d1):
    """Where two lines cross, or None when they are effectively parallel."""
    denominator = d0[0] * d1[1] - d0[1] * d1[0]
    if abs(denominator) < 1e-12:
        return None
    diff = p1 - p0
    t = (diff[0] * d1[1] - diff[1] * d1[0]) / denominator
    return p0 + d0 * t


def inner_outline(points2d: np.ndarray, widths) -> np.ndarray:
    """The opening left in the middle once each edge has taken its own
    strut width off. Corner k is where edge k-1's inner face meets edge
    k's -- which is why mismatched widths still close up correctly."""
    centroid = points2d.mean(axis=0)
    count = len(points2d)
    lines = []
    for i in range(count):
        p0 = points2d[i]
        p1 = points2d[(i + 1) % count]
        normal = _inward_normal(p0, p1, centroid)
        offset = p0 + normal * widths[i]
        direction = p1 - p0
        lines.append((offset, direction / max(1e-12, np.linalg.norm(direction))))
    corners = []
    for i in range(count):
        previous = lines[(i - 1) % count]
        current = lines[i]
        hit = _line_intersect(previous[0], previous[1], current[0], current[1])
        corners.append(hit if hit is not None else points2d[i])
    return np.array(corners)


def _clip_halfplane(polygon, point, normal):
    """Sutherland-Hodgman clip: keep whatever lies on the normal's side."""
    if len(polygon) == 0:
        return polygon
    out = []
    count = len(polygon)
    for i in range(count):
        current = polygon[i]
        previous = polygon[(i - 1) % count]
        cur_in = float(np.dot(current - point, normal)) >= 0.0
        prev_in = float(np.dot(previous - point, normal)) >= 0.0
        if cur_in != prev_in:
            edge = current - previous
            denominator = float(np.dot(edge, normal))
            if abs(denominator) > 1e-12:
                t = float(np.dot(point - previous, normal)) / denominator
                out.append(previous + edge * t)
        if cur_in:
            out.append(current)
    return np.array(out) if out else np.zeros((0, 2))


def _band(polygon, axis, low, high):
    """The slice of a polygon between two parallel lines."""
    clipped = _clip_halfplane(polygon, axis * low, axis)
    if len(clipped) < 3:
        return None
    clipped = _clip_halfplane(clipped, axis * high, -axis)
    return clipped if len(clipped) >= 3 else None


# ---------------------------------------------------------------------------
# Emitting geometry
# ---------------------------------------------------------------------------

def _fan(batch: Batch, points3d, color, normal=None) -> None:
    for i in range(1, len(points3d) - 1):
        batch.tri(points3d[0], points3d[i], points3d[i + 1], color, normal)


def _plate(batch: Batch, polygon2d, origin, e1, e2, normal,
           lift: float, thickness: float, color) -> None:
    """A flat polygon given real depth, so it reads as a solid part."""
    if len(polygon2d) < 3:
        return
    top = [to_3d(p, origin, e1, e2, lift, normal) for p in polygon2d]
    if thickness <= 1e-6:
        _fan(batch, top, color, normal)
        _fan(batch, list(reversed(top)), color, -normal)
        return
    bottom = [p - normal * thickness for p in top]
    _fan(batch, top, color, normal)
    _fan(batch, list(reversed(bottom)), color, -normal)
    side = tuple(c * 0.8 for c in color[:3]) + (color[3],)
    for i in range(len(top)):
        j = (i + 1) % len(top)
        batch.quad(top[i], bottom[i], bottom[j], top[j], side)


def emit_strut(batch: Batch, section: Section, width: float, outer_a, outer_b,
               inner_a, inner_b, normal, color) -> None:
    """Sweep one cross-section along one edge.

    Each point of the section is carried between the two end miter lines,
    so the ends come out correctly mitered for any shape -- a rectangle, a
    half-round belly, or a hollow tube -- and for any roll of it.
    """
    width = max(1e-6, width)
    xs = [p[0] for p in section]
    base_x = min(xs)
    starts, ends = [], []
    for x, y in section:
        u = (x - base_x) / width
        starts.append(outer_a + (inner_a - outer_a) * u + normal * y)
        ends.append(outer_b + (inner_b - outer_b) * u + normal * y)
    count = len(section)
    for i in range(count):
        j = (i + 1) % count
        batch.quad(starts[i], ends[i], ends[j], starts[j], color)
        batch.quad(starts[j], ends[j], ends[i], starts[i], color)
    cap = tuple(c * 0.72 for c in color[:3]) + (color[3],)
    _fan(batch, starts, cap)
    _fan(batch, list(reversed(ends)), cap)


def emit_fill(batch: Batch, fill: PanelFill, polygon2d, origin, e1, e2,
              normal, tint_of, alpha_scale: float = 1.0) -> None:
    """Whatever spans the opening, drawn in the style the fill asks for."""
    if fill.style == "none" or len(polygon2d) < 3:
        return
    color = tint_of(fill.tint, fill.alpha * alpha_scale)
    lift = -0.004
    span = polygon2d.max(axis=0) - polygon2d.min(axis=0)
    reach = float(max(span[0], span[1]))

    if fill.style in ("plain", "cells", "rings", "mesh"):
        _plate(batch, polygon2d, origin, e1, e2, normal, lift,
               fill.thickness, color)

    if fill.style == "cells":
        # The cell grid that makes a solar module read as one.
        line = tint_of("steel", min(1.0, fill.alpha * alpha_scale))
        axis = np.array([1.0, 0.0])
        step = max(0.05, reach / 6.0)
        start = float(polygon2d[:, 0].min())
        k = 1
        while start + step * k < float(polygon2d[:, 0].max()):
            cut = start + step * k
            strip = _band(polygon2d, axis, cut - 0.004, cut + 0.004)
            if strip is not None:
                _plate(batch, strip, origin, e1, e2, normal,
                       lift - fill.thickness - 0.002, 0.0, line)
            k += 1

    elif fill.style == "rings":
        # Concentric steps -- what makes a Fresnel lens flat.
        centre = polygon2d.mean(axis=0)
        rings = 7
        for r in range(1, rings + 1):
            radius = reach * 0.5 * r / rings
            circle = np.array([
                centre + np.array([math.cos(a), math.sin(a)]) * radius
                for a in np.linspace(0.0, math.tau, 40, endpoint=False)
            ])
            clipped = circle
            for i in range(len(polygon2d)):
                p0 = polygon2d[i]
                p1 = polygon2d[(i + 1) % len(polygon2d)]
                inward = _inward_normal(p0, p1, centre)
                clipped = _clip_halfplane(clipped, p0 + inward * 0.01, inward)
                if len(clipped) < 3:
                    break
            if len(clipped) >= 3:
                _plate(batch, clipped, origin, e1, e2, normal,
                       lift + 0.002 + 0.001 * r, 0.0,
                       tint_of(fill.tint, fill.alpha * alpha_scale * 0.5))

    elif fill.style == "mesh":
        line = tint_of("charcoal", 0.9 * alpha_scale)
        for axis in (np.array([1.0, 0.0]), np.array([0.0, 1.0])):
            lo = float((polygon2d @ axis).min())
            hi = float((polygon2d @ axis).max())
            step = max(0.04, (hi - lo) / 9.0)
            position = lo + step
            while position < hi:
                strip = _band(polygon2d, axis, position - 0.003, position + 0.003)
                if strip is not None:
                    _plate(batch, strip, origin, e1, e2, normal,
                           lift - 0.002, 0.0, line)
                position += step

    elif fill.style == "planks":
        # Several flat boards making up a sheet, with a shadow gap.
        axis = np.array([0.0, 1.0])
        lo = float((polygon2d @ axis).min())
        hi = float((polygon2d @ axis).max())
        board = max(0.09, (hi - lo) / 7.0)
        position = lo
        index = 0
        while position < hi:
            strip = _band(polygon2d, axis, position + 0.006, position + board)
            if strip is not None:
                shade = 1.0 - 0.07 * (index % 3)
                _plate(batch, strip, origin, e1, e2, normal, lift,
                       fill.thickness,
                       tuple(c * shade for c in color[:3]) + (color[3],))
            position += board
            index += 1

    elif fill.style == "shingles":
        # Overlapping courses, each standing slightly proud of the one
        # below so water is always shed outward.
        axis = np.array([0.0, 1.0])
        lo = float((polygon2d @ axis).min())
        hi = float((polygon2d @ axis).max())
        course = max(0.07, (hi - lo) / 8.0)
        position = lo
        index = 0
        while position < hi:
            strip = _band(polygon2d, axis, position, position + course * 1.5)
            if strip is not None:
                shade = 1.0 - 0.09 * (index % 2)
                _plate(batch, strip, origin, e1, e2, normal,
                       lift + 0.004 + index * 0.0015, fill.thickness,
                       tuple(c * shade for c in color[:3]) + (color[3],))
            position += course
            index += 1

    elif fill.style == "louvers":
        # Angled slats: the gap between them is the airflow.
        axis = np.array([0.0, 1.0])
        lo = float((polygon2d @ axis).min())
        hi = float((polygon2d @ axis).max())
        slat = max(0.07, (hi - lo) / 7.0)
        position = lo
        index = 0
        while position < hi:
            strip = _band(polygon2d, axis, position + 0.012, position + slat * 0.8)
            if strip is not None:
                tilt = -0.022 if index % 2 == 0 else -0.030
                _plate(batch, strip, origin, e1, e2, normal, lift + tilt,
                       0.008, color)
            position += slat
            index += 1

    elif fill.style == "box":
        # A unit that fills the opening and stands proud of it.
        _plate(batch, polygon2d, origin, e1, e2, normal, lift,
               fill.thickness, color)
        shrunk = inner_outline(polygon2d, [reach * 0.14] * len(polygon2d))
        if len(shrunk) >= 3:
            _plate(batch, shrunk, origin, e1, e2, normal,
                   lift + 0.02, 0.01,
                   tint_of("charcoal", min(1.0, alpha_scale)))


def build_panel(op: Batch, tr: Batch, corners, strut_keys, fill_key,
                tint_of, *, seam: float = 0.004, alpha: float = 1.0,
                strut_tint: str | None = None, highlight: bool = False):
    """One complete panel: three struts (possibly all different) and a fill.

    ``corners`` are the triangle's three 3D points; ``strut_keys`` is one
    profile key per edge, edge i running from corner i to corner i+1.
    Returns the inner opening in 2D plus the plane frame, so callers can
    reuse them.
    """
    origin, e1, e2, normal = plane_basis(*corners)
    points2d = np.array([to_2d(p, origin, e1, e2) for p in corners])
    centroid = points2d.mean(axis=0)
    if seam > 0.0:
        points2d = inner_outline(points2d, [seam] * 3)

    resolved = [oriented_profile(spec) for spec in strut_keys]
    widths = [item[2] for item in resolved]
    inner2d = inner_outline(points2d, widths)

    target = tr if alpha < 0.999 else op
    for i, (profile, section, width, _depth) in enumerate(resolved):
        j = (i + 1) % 3
        colour_name = strut_tint or profile.tint
        color = tint_of(colour_name, alpha)
        if highlight:
            color = tint_of("amber", alpha)
        emit_strut(
            target, section, width,
            to_3d(points2d[i], origin, e1, e2),
            to_3d(points2d[j], origin, e1, e2),
            to_3d(inner2d[i], origin, e1, e2),
            to_3d(inner2d[j], origin, e1, e2),
            normal, color,
        )

    fill = FILL_BY_KEY.get(fill_key, FILL_BY_KEY["open"])
    if fill.style != "none":
        emit_fill(tr if fill.alpha < 0.999 else op, fill, inner2d,
                  origin, e1, e2, normal, tint_of, alpha)
    return inner2d, (origin, e1, e2, normal)
