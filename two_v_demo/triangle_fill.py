"""Filling a dome triangle with pairs of wedges: laid, course by course, not estimated.

The owner's method. Wedges go into the triangle in **pairs**, running across it, the two
**points facing each other** down the triangle. Slide one along the other's slant and the
pair changes shape without changing its wood:

* **nested** (overlap ``p = 1``): the slants lie together along their whole length and the
  pair is a solid parallelogram. Down the triangle it spans one wedge **depth**.
* **bowtie** (``p = 0``): the pair touches only at the two points, tip to tip. It spans two
  depths, and the middle of the pair is empty.

Between them the pair spans ``(2 - p) x depth`` downward, and is ``1/(2 - p)`` wood.

Here every pair is placed: the courses run from the triangle's top corner down to its
base at that pitch, each wedge as long as the triangle is wide where it lies, inside a
strip where the frame's own wedges sit. The dome's triangles are the solver's. So the
footage is counted, wedge by wedge -- not an area divided by a width.

This corrects the first count (:mod:`two_v_demo.wedge_coverage_facts`, from the owner's
ChatGPT session): that one divided the open area by ``(2 - p) x`` the wedge's **face**
width. With the points facing each other down the triangle, the pair's downward reach is
set by the wedge's **depth**, which for an eighth of a log is longer than its face. Laid
pair by pair -- with the short pairs near each top corner and the closing pair at each
base -- the first count lands a few percent high when nested and runs low as a bowtie.

Coordinates in a triangle: ``u`` across (along the base), ``v`` down from the top corner.
"""

from __future__ import annotations

import math
from dataclasses import dataclass
from functools import lru_cache

SPLITS = 8
TREE_FT = 60.0
#: The log the method's worked example uses: a choice of what to show.
LOG_IN = 12.0


def wedge(d_in: float = LOG_IN) -> dict:
    """An eighth of a log: its face (the chord), its depth (face to point), its slant."""
    half = math.pi / SPLITS
    return {"face_in": d_in * math.sin(half), "depth_in": d_in / 2 * math.cos(half), "slant_in": d_in / 2,
            "area_in2": 0.5 * d_in * math.sin(half) * d_in / 2 * math.cos(half)}


def pair(p: float, d_in: float = LOG_IN) -> dict:
    """Where the second wedge sits for overlap ``p``, in the pair's cross-section.

    ``down`` runs down the triangle, ``across`` through the panel. Wedge A has its face at
    down = 0 and its point at down = depth; wedge B's face is at ``down = (2 - p) depth``,
    its point at ``(1 - p) depth``, shifted ``p x face/2`` through the panel -- which is
    exactly a slide along A's slant."""
    w = wedge(d_in)
    h, f = w["depth_in"], w["face_in"]
    span = (2 - p) * h
    a = [(0.0, -f / 2), (0.0, f / 2), (h, 0.0)]
    shift = p * f / 2
    b = [(span, shift - f / 2), (span, shift + f / 2), (span - h, shift)]
    return {"a": a, "b": b, "span_in": span, "thick_in": f + shift, "solid": 1 / (2 - p),
            "contact_in": p * w["slant_in"], "p": p}


@dataclass
class Course:
    v_in: float          # down from the top corner, to the pair's middle
    width_in: float      # the triangle's width there
    wedges: int = 2

    @property
    def wedge_in(self) -> float:
        return self.wedges * self.width_in


def triangle_courses(base_in: float, side_in: float, p: float, d_in: float = LOG_IN,
                     inset_in: float | None = None) -> list[Course]:
    """Every pair in one isosceles triangle (base, two equal sides), top corner down.

    ``inset_in`` is the strip inside every edge where the frame's own wedges sit: by
    default half a wedge face, the same allowance the first count used."""
    w = wedge(d_in)
    inset = w["face_in"] / 2 if inset_in is None else inset_in
    height = math.sqrt(side_in ** 2 - (base_in / 2) ** 2)
    r = base_in * height / (base_in + 2 * side_in)            # inradius
    k = max(0.0, 1 - inset / r)                                # the open triangle, scaled about the incentre
    H, B = height * k, base_in * k
    pitch = (2 - p) * w["depth_in"]
    out, v = [], 0.0
    while v + pitch <= H + 1e-9 or not out:
        mid = v + pitch / 2
        if mid > H:
            break
        out.append(Course(mid, B * mid / H))
        v += pitch
    # the strip left at the base when the pitch does not divide the height: one more pair,
    # nested to fit -- a real panel closes it, so it is counted
    if H - v > 1e-6 and out:
        out.append(Course(H - (H - v) / 2, B * (H - (H - v) / 2) / H))
    return out


def triangle(base_in: float, side_in: float, p: float, d_in: float = LOG_IN) -> dict:
    cs = triangle_courses(base_in, side_in, p, d_in)
    return {"courses": len(cs), "wedges": sum(c.wedges for c in cs), "wedge_ft": sum(c.wedge_in for c in cs) / 12,
            "longest_in": max(c.width_in for c in cs), "shortest_in": min(c.width_in for c in cs)}


@lru_cache(maxsize=1)
def dome_faces() -> list[tuple[float, float, int]]:
    """The solver's triangle types: (base, equal side, how many)."""
    from two_v_demo import wedge_coverage_facts as wc
    d = wc.dome()
    long_in, short_in = d["long_in"], d["short_in"]
    return [(long_in, short_in, d["iso_faces"]), (long_in, long_in, d["eq_faces"])]


def dome(p: float, d_in: float = LOG_IN) -> dict:
    """The whole dome's infill at overlap ``p``, laid triangle by triangle."""
    from two_v_demo import wedge_coverage_facts as wc
    ft = wedges = 0
    for base, side, n in dome_faces():
        t = triangle(base, side, p, d_in)
        ft += n * t["wedge_ft"]
        wedges += n * t["wedges"]
    frame = wc.dome()["frame_nominal_ft"]
    total = frame + ft
    per_tree = TREE_FT * SPLITS
    return {"p": p, "infill_ft": ft, "infill_wedges": wedges, "total_ft": total,
            "trees": total / per_tree, "whole_trees": math.ceil(total / per_tree),
            "pair_span_in": pair(p, d_in)["span_in"], "solid": pair(p, d_in)["solid"]}


@lru_cache(maxsize=1)
def facts() -> dict:
    from two_v_demo import wedge_coverage_facts as wc
    w = wedge(LOG_IN)
    nested, bowtie = dome(1.0), dome(0.0)
    base, side, _n = dome_faces()[0]
    first = wc.facts()
    return {"log_in": LOG_IN, "face_in": w["face_in"], "depth_in": w["depth_in"], "slant_in": w["slant_in"],
            "depth_over_face": w["depth_in"] / w["face_in"],
            "nested": nested, "bowtie": bowtie, "half": dome(0.5),
            "iso_nested": triangle(base, side, 1.0), "iso_bowtie": triangle(base, side, 0.0),
            "iso_base_in": base, "iso_side_in": side,
            "first_min_ft": first["infill_min_ft_12"], "first_max_ft": first["infill_max_ft_12"],
            "first_over_pct": 100 * (first["infill_max_ft_12"] / nested["infill_ft"] - 1)}


def validate() -> None:
    f = facts()
    a, b = pair(1.0), pair(0.0)
    assert abs(a["span_in"] - f["depth_in"]) < 1e-9 and abs(b["span_in"] - 2 * f["depth_in"]) < 1e-9
    # nested: B's point lands on A's face corner and the slants coincide -- a parallelogram
    assert abs(a["b"][2][0] - 0.0) < 1e-9 and abs(a["b"][2][1] - f["face_in"] / 2) < 1e-9
    # bowtie: the two points touch
    assert b["a"][2] == (f["depth_in"], 0.0) and abs(b["b"][2][0] - f["depth_in"]) < 1e-9 and b["b"][2][1] == 0
    assert f["bowtie"]["infill_ft"] < f["half"]["infill_ft"] < f["nested"]["infill_ft"]
    assert f["iso_bowtie"]["courses"] < f["iso_nested"]["courses"]
    assert f["depth_over_face"] > 1, "an eighth of a log is deeper than its face is wide"
    assert f["first_max_ft"] > f["nested"]["infill_ft"], "the first count used the face, and ran high"


if __name__ == "__main__":
    validate()
    f = facts()
    print(f"12 in log: face {f['face_in']:.2f} in, depth {f['depth_in']:.2f} in")
    for name in ("nested", "half", "bowtie"):
        r = f[name]
        print(f"{name:7s} pair spans {r['pair_span_in']:.2f} in, {r['solid']:.0%} wood: infill {r['infill_wedges']} "
              f"wedges, {r['infill_ft']:,.0f} ft; with the frame {r['total_ft']:,.0f} ft = {r['trees']:.1f} trees")
    print(f"one isosceles triangle: nested {f['iso_nested']}; bowtie {f['iso_bowtie']}")
    print(f"first count {f['first_min_ft']:,.0f}-{f['first_max_ft']:,.0f} ft: {f['first_over_pct']:.0f}% over at nested")
