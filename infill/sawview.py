"""One cut, laid out on the saw: the geometry both the 3-D tool and the films draw.

A recipe step's animation (:mod:`infill.recipes`) carries the stick, the
keeper and the offcut as solids in the piece's own coordinates, and -- for a
mitre-saw cut -- the frame of the saw table. This turns them into *saw
coordinates*: x along the fence (your left to your right), y from the fence
toward you is negative (the piece lies at y < 0, its back against the fence at
y = 0), z up from the table. The blade's plane passes through the cut.

Then :func:`moment` says where everything is at a moment of the cut: the stick
slides in, the blade comes down through it, lifts, and the offcut falls away
to its side. The 3-D tool and the films call the same two functions, so the
cut the film shows is the cut the tool shows.
"""

from __future__ import annotations

import numpy as np

from . import solids as so

BLADE_R = 6.0            # in: a 12 in blade
SLIDE_IN = 25.0          # in: how far the stick slides in at the start
OFFCUT_AWAY = 14.0       # in: how far the offcut falls away along the fence


def _frame(an: dict) -> np.ndarray:
    if an["type"] == "mitre":
        return np.asarray(an["frame"], float)
    sol = an["stick"]
    along = sol.along if sol.along is not None else np.array([1.0, 0.0, 0.0])
    x = np.asarray(along, float) / np.linalg.norm(along)
    z = np.array([0.0, 0.0, 1.0])
    y = np.cross(z, x)
    return np.array([x, y, z])


def parts(an: dict) -> dict | None:
    """The cut in saw coordinates, or None for a step with no cut."""
    if not an or an.get("type") not in ("mitre", "freehand") or an.get("stick") is None:
        return None
    pl = an.get("plane")
    F = _frame(an)
    near = an.get("offcut") if an.get("offcut") is not None and an["offcut"].faces else an["stick"]
    c = near.vertices().mean(axis=0)
    X0 = c - (float(pl.n @ c) - pl.d) * pl.n if pl is not None else c

    def to_saw(v):
        return (F @ (np.asarray(v, float) - X0).T).T
    pts = to_saw(an["stick"].vertices())
    shift = np.array([0.0, -pts[:, 1].max(), -pts[:, 2].min()])
    moved = pts + shift

    def conv(sol):
        if sol is None or not sol.faces:
            return None
        return so.Solid([(to_saw(p) + shift, t) for p, t in sol.faces])
    whole = an.get("keeper") is None and an.get("offcut") is None
    out = {"type": an["type"], "whole": whole, "extent": (moved.min(axis=0), moved.max(axis=0)),
           "keeper": conv(an["stick"] if whole else an.get("keeper")), "offcut": conv(an.get("offcut")),
           "keeper_right": an.get("keeper_right", True), "mitre": an.get("mitre", 0.0),
           "bevel": an.get("bevel", 0.0), "bp": shift.copy()}
    for part in ("keeper", "offcut"):
        sol = an.get(part)
        at = None
        if sol is not None and sol.faces:
            v = to_saw(sol.vertices()) + shift
            beside = v[np.abs(v[:, 0] - shift[0]) < 14.0]      # the part of it beside the blade
            at = (beside if len(beside) else v).mean(axis=0)
        out[part + "_at"] = at
    ns = F @ pl.n if pl is not None else np.array([1.0, 0.0, 0.0])
    if ns[0] < 0:
        ns = -ns
    out["ns"] = ns
    return out


def bench(sc: dict) -> list[tuple[tuple, tuple, str]]:
    """The table and fence (mitre saw), or a bench under the piece (by hand):
    (centre, size, colour hex) boxes in saw coordinates."""
    if sc["type"] == "mitre":
        return [((0.0, -10.0, -0.75), (70.0, 22.0, 1.5), "#7d8a96"),
                ((0.0, 1.0, 2.5), (70.0, 2.0, 5.0), "#5b6670")]
    lo, hi = sc["extent"]
    return [(((lo[0] + hi[0]) / 2, (lo[1] + hi[1]) / 2, -0.75),
             (hi[0] - lo[0] + 12.0, hi[1] - lo[1] + 12.0, 1.5), "#4a5560")]


def _e(t: float, a: float, b: float) -> float:
    return min(1.0, max(0.0, (t - a) / (b - a)))


def moment(sc: dict, t: float) -> dict:
    """Where everything is at ``t`` (0..1) of the cut: offsets for the keeper
    and the offcut, and the blade's centre, axis and radius."""
    slide = (1 - _e(t, 0.0, 0.18)) ** 2 * -SLIDE_IN
    away = _e(t, 0.58, 0.85)
    sign = -1.0 if sc["keeper_right"] else 1.0
    offsets = {"keeper": np.array([slide, 0.0, 0.0]),
               "offcut": np.array([slide + sign * OFFCUT_AWAY * away, -4.0 * away, 0.0])}
    ns = sc["ns"]
    up = np.array([0.0, 0.0, 1.0]) - ns * ns[2]
    up = up / max(np.linalg.norm(up), 1e-6)
    top = 4.0 + BLADE_R
    h = top - (top + 1.5) * _e(t, 0.2, 0.55) + (top + 1.5) * _e(t, 0.62, 0.8)
    return {"offsets": offsets, "blade_centre": sc["bp"] + up * h, "blade_axis": ns, "blade_r": BLADE_R,
            "cutting": 0.2 <= t <= 0.62}
