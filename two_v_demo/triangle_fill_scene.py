"""The pieces the triangle-fill film shows, built from :mod:`two_v_demo.triangle_fill`.

* a wedge end-on, and a **pair** whose second wedge slides along the first's slant from
  nested to bowtie -- shown three times life size so the shape reads;
* a dome triangle at **true size**, tilted like a panel, its frame of three wedges and its
  open middle filled with pairs **course by course from the top corner down**, at any
  overlap, the pairs placed exactly where :func:`triangle_fill.triangle_courses` puts them.

World metres, on the Cabin World's exhibit platform.
"""

from __future__ import annotations

import math

import numpy as np

from . import cabin_stage
from . import triangle_fill as tf
from .render_kit import TriangleBatch

IN = 0.0254
PC = np.array([cabin_stage.CENTRE[0], cabin_stage.CENTRE[1], cabin_stage.HEIGHT])
BIG = 3.0                                   # the pair close-up: three times life size (said on screen)
A_COL = (1.00, 0.80, 0.50, 1.0)             # wedge A: pale pine
B_COL = (0.78, 0.40, 0.22, 1.0)             # wedge B: red-brown, so the pair reads as two
END = (1.00, 0.93, 0.78, 1.0)               # end grain, bright: the section is the point
FRAME = (0.50, 0.34, 0.20, 1.0)
GAP = (0.35, 0.75, 1.0, 0.45)               # the air in a bowtie
TILT = math.radians(35.0)                   # the panel leans back like a dome panel


def _prism(b: TriangleBatch, ring_a, ring_b, colour, end=None) -> None:
    ring_a, ring_b = [np.asarray(q, float) for q in ring_a], [np.asarray(q, float) for q in ring_b]
    c = np.mean(ring_a + ring_b, axis=0)

    def face(pts, col):
        n = np.cross(pts[1] - pts[0], pts[2] - pts[0])
        if np.linalg.norm(n) < 1e-12:
            return
        if n @ (np.mean(pts, axis=0) - c) < 0:
            pts, n = pts[::-1], -n
        for k in range(1, len(pts) - 1):
            b.triangle(pts[0], pts[k], pts[k + 1], col, n)

    end = colour if end is None else end            # each wedge's end in its own colour, so a pair reads as two
    face(ring_a, end)
    face(ring_b, end)
    m = len(ring_a)
    for k in range(m):
        face([ring_a[k], ring_a[(k + 1) % m], ring_b[(k + 1) % m], ring_b[k]], colour)


def _section_to_world(origin, down, across, sec, scale):
    return [origin + down * (d * IN * scale) + across * (a * IN * scale) for d, a in sec]


# ----------------------------------------------------------------------
# The close-up: one wedge, one pair
# ----------------------------------------------------------------------

#: The close-up stands upright: down the triangle is down, through the panel is across (y),
#: and the wedges run along x, so the camera looks at their end grain.
CLOSE = PC + np.array([0.0, 0.0, 1.35])


def wedge_close(length_m: float = 0.9) -> TriangleBatch:
    b = TriangleBatch()
    p = tf.pair(1.0)
    down, across, along = np.array([0, 0, -1.0]), np.array([0, 1.0, 0]), np.array([1.0, 0, 0])
    sec = _section_to_world(CLOSE, down, across, p["a"], BIG)
    _prism(b, [q - along * length_m / 2 for q in sec], [q + along * length_m / 2 for q in sec], A_COL)
    return b


def pair_close(p: float, length_m: float = 0.9) -> tuple[TriangleBatch, TriangleBatch]:
    """The pair at overlap ``p``, end-on; and the air inside it (the bowtie's empty middle)."""
    b, air = TriangleBatch(), TriangleBatch()
    pr = tf.pair(p)
    down, across, along = np.array([0, 0, -1.0]), np.array([0, 1.0, 0]), np.array([1.0, 0, 0])
    for sec, col in ((pr["a"], A_COL), (pr["b"], B_COL)):
        w = _section_to_world(CLOSE, down, across, sec, BIG)
        _prism(b, [q - along * length_m / 2 for q in w], [q + along * length_m / 2 for q in w], col)
    if p < 0.999:                                   # the empty middle, as a pale block
        f = tf.wedge()["face_in"]
        h = pr["span_in"]
        box = [(0.0, -f / 2), (0.0, f / 2 + p * f / 2), (h, f / 2 + p * f / 2), (h, -f / 2)]
        w = _section_to_world(CLOSE + along * (length_m / 2 + 0.002), down, across, box, BIG)
        _prism(air, w, [q + along * 0.004 for q in w], GAP)
    return b, air


def close_points(p: float) -> dict:
    """Where to hang labels on the close-up."""
    pr = tf.pair(p)
    top = CLOSE + np.array([0.0, 0.0, 0.0])
    bottom = CLOSE + np.array([0.0, 0.0, -pr["span_in"] * IN * BIG])
    return {"top": top, "bottom": bottom, "side": CLOSE + np.array([0.0, 0.35, -pr["span_in"] * IN * BIG / 2])}


# ----------------------------------------------------------------------
# The triangle at true size
# ----------------------------------------------------------------------

def panel_frame(at=None):
    """The panel's axes: u across (world x), v down the slope from the top corner, n out of it."""
    at = PC if at is None else np.asarray(at, float)
    u = np.array([1.0, 0.0, 0.0])
    v = np.array([0.0, -math.cos(TILT), -math.sin(TILT)])
    n = np.cross(u, v)
    if n[2] < 0:
        n = -n
    return at, u, v, n


def _apex(at, base_in, side_in):
    o, u, v, n = panel_frame(at)
    height = math.sqrt(side_in ** 2 - (base_in / 2) ** 2) * IN
    # stand the triangle so its middle sits over ``at`` and its base is near the platform
    return o - v * height * 0.5 + np.array([0, 0, height * math.sin(TILT) * 0.5 + 0.12]), u, v, n, height


def triangle(base_in: float, side_in: float, p: float, show: float = 1.0, at=None,
             d_in: float = tf.LOG_IN) -> tuple[TriangleBatch, dict]:
    """The frame and ``show`` (0 to 1) of the courses, filled from the top down."""
    b = TriangleBatch()
    apex, u, v, n, height = _apex(at, base_in, side_in)
    corners = [apex, apex + v * height - u * base_in * IN / 2, apex + v * height + u * base_in * IN / 2]
    w = tf.wedge(d_in)
    f, h = w["face_in"] * IN, w["depth_in"] * IN
    # the frame: a wedge along each edge, face out, lying in the panel
    centre = np.mean(corners, axis=0)
    for k in range(3):
        a0, a1 = corners[k], corners[(k + 1) % 3]
        d = (a1 - a0) / np.linalg.norm(a1 - a0)
        inward = centre - (a0 + a1) / 2
        inward -= d * (inward @ d)
        inward /= np.linalg.norm(inward)
        ring = [np.zeros(3), inward * f, -n * h * 0.5]          # a wedge's section, roughly
        _prism(b, [a0 + q for q in ring], [a1 + q for q in ring], FRAME)
    courses = tf.triangle_courses(base_in, side_in, p, d_in)
    shown = int(math.ceil(len(courses) * max(0.0, min(1.0, show))))
    pr = tf.pair(p, d_in)
    open_h = tf.triangle_courses  # noqa: F841 (named for the reader: courses are already inset)
    for k, c in enumerate(courses[:shown]):
        top_v = c.v_in - pr["span_in"] / 2
        # the open triangle is inset; place courses relative to the inset top corner
        r = base_in * (height / IN) / (base_in + 2 * side_in)
        inset = w["face_in"] / 2
        top_offset = (height / IN) * (inset / r)              # the inset moves the top corner down this far
        origin = apex + v * ((top_offset + top_v) * IN)
        for sec, col in ((pr["a"], A_COL), (pr["b"], B_COL)):
            pts = [origin + v * (dn * IN) + n * (ac * IN) for dn, ac in sec]
            half = c.width_in * IN / 2
            _prism(b, [q - u * half for q in pts], [q + u * half for q in pts], col)
    info = {"courses": len(courses), "shown": shown, "wedges": 2 * shown,
            "feet": sum(cc.wedge_in for cc in courses[:shown]) / 12,
            "label": apex + v * height + n * 0.25, "apex": apex, "height_m": height}
    return b, info


def validate_triangle_fill_scene() -> None:
    tf.validate()
    for p in (0.0, 0.5, 1.0):
        b, air = pair_close(p)
        assert len(b.vertices) and np.all(np.isfinite(np.asarray(b.vertices, float)))
    base, side, _n = tf.dome_faces()[0]
    t, info = triangle(base, side, 1.0)
    assert info["shown"] == info["courses"] and len(t.vertices)
    t0, i0 = triangle(base, side, 1.0, show=0.0)
    assert i0["shown"] == 0
