"""Exhibits the promo needs that no earlier film built: the pentagon foundation and its star.

The pentagon is :mod:`infill.base`'s own -- five 20 ft half trunks and the star inside --
built as solids by the floor solver and drawn here as a scale model on the Cabin World's
exhibit platform. Everything else the promo shows is borrowed from the films that built
it (:mod:`two_v_demo.staple_scene`, :mod:`two_v_demo.wedge_beyond_scene`).
"""

from __future__ import annotations

import numpy as np

from . import cabin_stage
from .render_kit import TriangleBatch

PC = np.array([cabin_stage.CENTRE[0], cabin_stage.CENTRE[1], cabin_stage.HEIGHT])
IN = 0.0254
#: The model's scale: the 20 ft pentagon fits the platform. A choice of how to show it.
FIT = 0.30
LOG = (0.66, 0.47, 0.30, 1.0)
LONG = (1.0, 0.70, 0.30, 1.0)       # the star's long pieces
SHORT = (0.45, 0.62, 0.80, 1.0)     # its short pieces
PIER = (0.55, 0.50, 0.44, 1.0)


def pentagon(show_star: float = 1.0) -> TriangleBatch:
    """The foundation, ``show_star`` of its star pieces drawn (0 to 1: the star builds in)."""
    from world3d import structures as ws
    B = ws.foundation_model()
    star = [p for p in B.pieces if p.kind == "primary"]
    n_star = int(round(len(star) * show_star))
    shown = [p for p in B.pieces if p.kind in ("frame", "pier")] + star[:n_star]
    long_len = max(round(p.ref.length, 1) for p in star) if star else 0
    b = TriangleBatch()
    for p in shown:
        if p.solid is None:
            continue
        if p.kind == "frame":
            colour = LOG
        elif p.kind == "pier":
            colour = PIER
        else:
            colour = LONG if round(p.ref.length, 1) == long_len else SHORT
        for poly, _t in p.solid.faces:
            pts = [PC + np.array([q[0], q[1], q[2]]) * IN * FIT for q in poly]
            n = np.cross(pts[1] - pts[0], pts[2] - pts[0])
            if np.linalg.norm(n) < 1e-12:
                continue
            for k in range(1, len(pts) - 1):
                b.triangle(pts[0], pts[k], pts[k + 1], colour, n)
    return b


def validate_promo_scene() -> None:
    full, none = pentagon(1.0), pentagon(0.0)
    assert len(full.vertices) > len(none.vertices) > 0
    assert np.all(np.isfinite(np.asarray(full.vertices, float)))
