"""How much wedge timber a whole dome takes: the frame, and closing every triangle.

Core wedge-building methodology. The model is the one worked out with the owner in a
ChatGPT session (October 2026); this module reproduces it from the project's own
geometry -- the strut lengths, the triangle count and shapes and the face areas all come
from the dome solver (:mod:`geodesic_raw_wedge_dome_dihedral`), never typed -- and
:func:`validate` checks every figure that session stated against it. Where the solver
knows better, both numbers are kept and the difference is said.

The model, in four steps:

1. **The frame.** 120 wedge members (each panel owns its three edges), 60 long and 60
   short. Their nominal length is the frame's footage; the solver's cut lengths are
   shorter, because every member stops against its neighbour at the pinwheel.
2. **The faces.** 30 isosceles and 10 equilateral triangles. Their area, less a strip
   inside every edge where the frame's own wedge sits (half a wedge face wide), is the
   open area to close.
3. **The wedge.** A log of diameter d split eight ways gives wedges with a face (the
   chord) of ``d sin 22.5 deg`` and a depth of ``d/2 cos 22.5 deg``.
4. **Closing a triangle with pairs**, points facing inward. A pair covers between two
   faces (``p = 0``, the pair touching only at the points -- a bowtie) and one face
   (``p = 1``, fully nested along the slants): ``(2 - p) x face``. So one face of infill
   takes ``2 x area / ((2 - p) x face)`` of wedge, from the least (``p = 0``) to the
   most (``p = 1``).

Trees: every foot of trunk gives eight feet of wedge. A 60 ft pine of the stated
diameter gives 480 ft -- before taper, kerf, knots and fitting, which the model leaves
out and says so.

The cross-check: the Triangle Infill calculator (:mod:`infill`) cuts real pieces for one
panel; the area method is compared with its actual piece lengths for the same coverage.
"""

from __future__ import annotations

import math
from functools import lru_cache

WEDGES_PER_SECTION = 8
TREE_FT = 60.0
#: The diameters the session's table ran, inches -- a choice of what to show.
DIAMETERS = (8.0, 10.0, 12.0, 14.0, 16.0)
OVERLAPS = (0.0, 0.25, 0.5, 0.75, 1.0)

#: What the ChatGPT session stated, to be checked against the solver: (name, value, tolerance).
CHATGPT_STATED = (
    ("long_in", 72.0, 0.05), ("short_in", 63.66, 0.05), ("members", 120, 0),
    ("unique_edges", 65, 0), ("iso_faces", 30, 0), ("eq_faces", 10, 0),
    ("frame_nominal_ft", 678.3, 0.5), ("area_ft2", 549.66, 0.5),
    ("face_in_12", 4.592, 0.002), ("depth_in_12", 5.543, 0.002),
    ("open_area_ft2_12", 427.55, 0.5), ("infill_min_ft_12", 1117.2, 1.5), ("infill_max_ft_12", 2234.5, 2.5),
    ("total_min_ft_12", 1795.5, 2.0), ("total_max_ft_12", 2912.8, 3.0),
    ("trees_min_12", 4, 0), ("trees_max_12", 7, 0), ("frame_trunk_ft", 90.0, 0.01),
    ("pentagon_long_in", 148.33, 0.01), ("pentagon_short_in", 91.67, 0.01),
    ("butt_cut_off_square_deg", 18.0, 1e-9), ("diagonal_cut_off_square_deg", 54.0, 1e-9),
)


@lru_cache(maxsize=1)
def dome() -> dict:
    """The solver's dome: strut lengths, members, faces and their areas and inradii."""
    import numpy as np

    import geodesic_raw_wedge_dome_dihedral as d

    m = d.build_physical_model(d.DomeConfig())
    lengths = {}
    for e in m.topology.edges.values():
        a, b = m.topology.vertices[e.key[0]], m.topology.vertices[e.key[1]]
        lengths.setdefault(e.edge_type, []).append(float(np.linalg.norm(a - b)))
    long_in, short_in = max(np.mean(v) for v in lengths.values()), min(np.mean(v) for v in lengths.values())
    faces = []
    for f in m.topology.faces:
        p = m.topology.vertices[list(f.vertices)]
        sides = [float(np.linalg.norm(p[i] - p[(i + 1) % 3])) for i in range(3)]
        area = 0.5 * float(np.linalg.norm(np.cross(p[1] - p[0], p[2] - p[0])))
        faces.append({"area_in2": area, "inradius_in": area / (sum(sides) / 2),
                      "equilateral": max(sides) - min(sides) < 0.5})
    nominal = 0.0
    for mm in m.members:
        nominal += long_in if abs(float(mm.nominal_length_in) - long_in) < abs(float(mm.nominal_length_in) - short_in) \
            else short_in
    return {"long_in": long_in, "short_in": short_in, "members": len(m.members),
            "unique_edges": len(m.topology.edges), "faces": faces,
            "iso_faces": sum(1 for f in faces if not f["equilateral"]),
            "eq_faces": sum(1 for f in faces if f["equilateral"]),
            "frame_nominal_ft": nominal / 12.0,
            "frame_cut_ft": sum(float(mm.physical_stock_length_in) for mm in m.members) / 12.0,
            "area_ft2": sum(f["area_in2"] for f in faces) / 144.0,
            "solver_log_in": float(m.config.trunk_diameter_in),
            "longest_member_in": max(float(mm.physical_stock_length_in) for mm in m.members)}


def wedge(d_in: float) -> dict:
    return {"face_in": d_in * math.sin(math.pi / 8), "depth_in": d_in / 2 * math.cos(math.pi / 8),
            "slant_in": d_in / 2}


def open_area_ft2(d_in: float) -> float:
    """The faces' area less a strip half a wedge face wide inside every edge (the frame's own wedge)."""
    inset = wedge(d_in)["face_in"] / 2
    return sum(f["area_in2"] * max(0.0, 1 - inset / f["inradius_in"]) ** 2 for f in dome()["faces"]) / 144.0


def pair_cover_in(d_in: float, p: float) -> float:
    return (2 - p) * wedge(d_in)["face_in"]


def infill_ft(d_in: float, p: float) -> float:
    """One face of infill, closed with pairs at overlap ``p``: feet of wedge."""
    return 2 * open_area_ft2(d_in) * 12 / pair_cover_in(d_in, p)


def frame_trunk_ft() -> float:
    """Trunk for the frame: one wedge per member, a section as long as the longest strut."""
    sections = math.ceil(dome()["members"] / WEDGES_PER_SECTION)
    return sections * dome()["long_in"] / 12.0


def row(d_in: float, p: float) -> dict:
    inf = infill_ft(d_in, p)
    total = dome()["frame_nominal_ft"] + inf
    trunk = inf / WEDGES_PER_SECTION + frame_trunk_ft()
    return {"d_in": d_in, "p": p, "pair_cover_in": pair_cover_in(d_in, p), "infill_ft": inf,
            "total_ft": total, "trunk_ft": trunk, "trees": math.ceil(total / (TREE_FT * WEDGES_PER_SECTION))}


def pentagon() -> dict:
    phi = (1 + 5 ** 0.5) / 2
    side = 240.0
    diag = phi * side
    return {"pentagon_long_in": diag - side, "pentagon_short_in": diag - 2 * (diag - side),
            "butt_cut_off_square_deg": 108.0 - 90.0, "diagonal_cut_off_square_deg": 90.0 - 108.0 / 3}


def calculator_check() -> dict:
    """The Triangle Infill calculator's flip-flop fill of one panel, against the area method
    at the same coverage: how far the area method's estimate is from real pieces."""
    from infill import facts as inf
    lay = inf._layout("w8", "parallel", "flipflop", "fill")
    m = lay.metrics
    per_wedge = m["pitch"] / m["per_period"]
    area_method_in = m["open_area_in2"] / per_wedge
    return {"pieces": m["pieces"], "real_in": m["linear_in"], "area_method_in": area_method_in,
            "excess_pct": 100 * (area_method_in / m["linear_in"] - 1),
            "implied_overlap": 2 - m["pitch"] / wedge(12.0)["face_in"]}


@lru_cache(maxsize=1)
def facts() -> dict:
    dm = dome()
    lo, hi = row(12.0, 0.0), row(12.0, 1.0)
    out = {k: dm[k] for k in ("long_in", "short_in", "members", "unique_edges", "iso_faces", "eq_faces",
                              "frame_nominal_ft", "frame_cut_ft", "area_ft2", "solver_log_in", "longest_member_in")}
    out.update(face_in_12=wedge(12)["face_in"], depth_in_12=wedge(12)["depth_in"],
               open_area_ft2_12=open_area_ft2(12), infill_min_ft_12=lo["infill_ft"],
               infill_max_ft_12=hi["infill_ft"], total_min_ft_12=lo["total_ft"], total_max_ft_12=hi["total_ft"],
               trees_min_12=lo["trees"], trees_max_12=hi["trees"], trunk_min_ft_12=lo["trunk_ft"],
               trunk_max_ft_12=hi["trunk_ft"], frame_trunk_ft=frame_trunk_ft(),
               solver_lo=row(dm["solver_log_in"], 0.0), solver_hi=row(dm["solver_log_in"], 1.0),
               table=[row(d, p) for d in DIAMETERS for p in (0.0, 1.0)], overlaps=[row(12.0, p) for p in OVERLAPS],
               frame_saving_ft=dm["frame_nominal_ft"] - dm["frame_cut_ft"])
    out.update(pentagon())
    return out


def verification() -> list[tuple[str, float, float, bool]]:
    """Every figure the session stated: (name, stated, computed here, agrees)."""
    f = facts()
    return [(name, stated, float(f[name]), abs(float(f[name]) - stated) <= tol)
            for name, stated, tol in CHATGPT_STATED]


def steps_frame() -> list[str]:
    f = facts()
    return [f"{f['members']} wedge members: {f['members'] // 2} long ({f['long_in']:.2f} in) and "
            f"{f['members'] // 2} short ({f['short_in']:.2f} in); {f['unique_edges']} unique edges.",
            f"Nominal frame: {f['frame_nominal_ft']:.1f} ft of wedge. Cut to the solver's pinwheel lengths: "
            f"{f['frame_cut_ft']:.1f} ft ({f['frame_saving_ft']:.1f} ft less).",
            f"Trunk for the frame: {math.ceil(f['members'] / WEDGES_PER_SECTION)} sections of "
            f"{f['long_in'] / 12:.0f} ft, {f['frame_trunk_ft']:.0f} ft of log."]


def steps_infill() -> list[str]:
    f = facts()
    out = [f"{f['iso_faces']} isosceles + {f['eq_faces']} equilateral faces: {f['area_ft2']:.1f} sq ft.",
           f"A 12 in log split 8 ways: face {f['face_in_12']:.3f} in, depth {f['depth_in_12']:.3f} in.",
           f"Open after the frame's strip: {f['open_area_ft2_12']:.1f} sq ft.",
           "Pairs, points in: a pair covers (2 - overlap) x one face."]
    for r in f["overlaps"]:
        out.append(f"  overlap {r['p']:.0%}: {r['pair_cover_in']:.2f} in a pair -> {r['infill_ft']:,.0f} ft infill, "
                   f"{r['total_ft']:,.0f} ft with the frame, {r['trees']} trees of {TREE_FT:.0f} ft")
    return out


def validate() -> None:
    bad = [(n, s, c) for n, s, c, ok in verification() if not ok]
    assert not bad, f"the session's figures and the solver disagree: {bad}"
    f = facts()
    assert f["infill_min_ft_12"] < f["infill_max_ft_12"] and f["trees_min_12"] <= f["trees_max_12"]
    assert f["frame_cut_ft"] < f["frame_nominal_ft"], "the pinwheel cuts must shorten the frame"
    assert f["solver_lo"]["infill_ft"] > f["infill_min_ft_12"], "a smaller log must take more wedge"


if __name__ == "__main__":
    validate()
    for name, stated, got, ok in verification():
        print(f"{'ok ' if ok else 'BAD'} {name:30s} stated {stated:>10g}   computed {got:>12.3f}")
    print("\n".join(steps_frame() + steps_infill()))
    c = calculator_check()
    print(f"calculator: {c['pieces']} pieces, {c['real_in']:.0f} in real vs {c['area_method_in']:.0f} in by area "
          f"({c['excess_pct']:+.1f}%), implied overlap {c['implied_overlap']:.2f}")
