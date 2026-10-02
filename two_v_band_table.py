"""Band-level tables for the 2V geodesic dome built on a six-foot member.

The dome this describes is the standard 2-frequency icosahedron hemisphere
with a six-foot longest member: the exact dome ``seed_model`` prices, the
Raw Wedge Dome tool draws, and the films teach.  Every number below is
computed from that solver -- ``geodesic_raw_wedge_dome_dihedral``, imported
through :mod:`two_v_demo.raw_wedge_bridge` the same way ``seed_model`` does
it.  Nothing here is restated by hand.

What the tables answer, in the words the request used:

* the height of every level (floor, the two rings of the first band of
  triangles, the band just outside the cap / pentagon band, the apex);
* the "amount inward" of every ring -- its radius, diameter and
  circumference, and how far each ring has stepped in from the one below;
* the slope between consecutive levels;
* the variant truncations of the same 2V sphere (every flat, hub-level cut).

Run::

    py -3.12 two_v_band_table.py

which prints the report and also writes ``two_v_band_table.md`` beside this
file.  The module's :func:`band_report` returns the same text, so any film
or book page can show a row of this table by reading it from here instead of
typing it.
"""

from __future__ import annotations

import math
from collections import defaultdict
from dataclasses import dataclass

import numpy as np

from two_v_demo import raw_wedge_bridge

LONG_EDGE_IN = 72.0
"""The six-foot longest member.  The one dimension every other figure here
follows from, exactly as in ``seed_model.SEED_LONG_EDGE_IN``."""

EPS = 1e-6

# Zip Tie Domes' published 2V calculator at a six-foot "A" strut, captured
# in seed_model.PUBLISHED_2V_AT_6FT -- the independent cross-check.
PUBLISHED = {
    "dome height, ft": 9.7083,
    "dome diameter, ft": 19.4165,
    "A strut, ft": 6.0,
    "B strut, ft": 5.3059,
    "base perimeter, ft": 60.0,
    "A strut count": 35.0,
    "B strut count": 30.0,
    "panel count": 40.0,
}


@dataclass(frozen=True)
class Ring:
    """One level of hubs, from the ground up."""

    name: str
    height_in: float
    radius_in: float
    hubs: tuple[int, ...]
    valence: int


@dataclass(frozen=True)
class Variant:
    """One flat hub-level truncation of the full 2V sphere."""

    name: str
    hub_count: int
    base_hub_count: int
    a_count: int
    b_count: int
    height_in: float
    base_radius_in: float
    base_chord_perimeter_in: float | None  # None when base hubs are not strut-linked


def _solve():
    sim = raw_wedge_bridge.simulator()
    return sim.build_2v_hemisphere(float(LONG_EDGE_IN))


def _ft_in(total_inches: float) -> str:
    """118.5 -> 9' 10-1/2\", rounded to the nearest 1/16\"."""
    sixteenths = int(round(total_inches * 16.0))
    whole_in, frac16 = divmod(sixteenths, 16)
    whole_ft, whole_in = divmod(whole_in, 12)
    if frac16 == 0:
        return f"{whole_ft}' {whole_in}\""
    num, den = frac16, 16
    while num % 2 == 0:
        num //= 2
        den //= 2
    return f"{whole_ft}' {whole_in}-{num}/{den}\""


def rings(topo) -> tuple[Ring, ...]:
    """The hemisphere's hubs grouped by height, floor first."""
    heights = sorted({round(float(topo.vertices[i][2]), 9)
                      for i in range(len(topo.vertices))})
    assert len(heights) == 5, heights

    valence: dict[int, int] = defaultdict(int)
    for (a, b) in topo.edges:
        valence[a] += 1
        valence[b] += 1

    names = ("base ring (floor)",
             "level 1 · pentagon ring",
             "level 1 · hexagon ring",
             "level 2 · pentagon band",
             "apex (cap)")
    out = []
    for level, height in enumerate(heights):
        hubs = tuple(i for i in range(len(topo.vertices))
                     if abs(float(topo.vertices[i][2]) - height) < EPS)
        radius = max(float(np.linalg.norm(topo.vertices[i][:2])) for i in hubs)
        out.append(Ring(names[level], height, radius, hubs,
                        max(valence[i] for i in hubs)))
    assert [len(r.hubs) for r in out] == [10, 5, 5, 5, 1], \
        [len(r.hubs) for r in out]
    return tuple(out)


def band_faces(topo, the_rings: tuple[Ring, ...]) -> dict[str, list]:
    """Split the 40 panels into the cap, the second band, and the first band.

    A panel belongs to the highest band any of its corners reaches: the cap
    touches the apex, the second band touches the level-2 ring, the first
    band touches the floor.  The three bands have 5, 15 and 20 panels.
    """
    apex = the_rings[-1].hubs[0]
    level2 = set(the_rings[-2].hubs)
    floor = set(the_rings[0].hubs)
    bands = {"cap": [], "second band": [], "first band": []}
    for face in topo.faces:
        verts = set(face.vertices)
        if apex in verts:
            bands["cap"].append(face)
        elif verts & level2:
            bands["second band"].append(face)
        else:
            assert verts & floor, verts
            bands["first band"].append(face)
    assert [len(bands[k]) for k in ("cap", "second band", "first band")] \
        == [5, 15, 20]
    return bands


def band_struts(topo, bands: dict[str, list]) -> dict[str, dict[str, int]]:
    """A/B strut counts per band, each shared edge credited to the lowest
    band that uses it so nothing is counted twice."""
    claimed: set[tuple[int, int]] = set()
    result: dict[str, dict[str, int]] = {}
    for band in ("first band", "second band", "cap"):
        counts: dict[str, int] = {"A": 0, "B": 0}
        for face in bands[band]:
            for i, j in ((face.vertices[0], face.vertices[1]),
                         (face.vertices[1], face.vertices[2]),
                         (face.vertices[2], face.vertices[0])):
                key = (i, j) if i < j else (j, i)
                if key in claimed:
                    continue
                claimed.add(key)
                counts[topo.edges[key].edge_type] += 1
        result[band] = counts
    assert (result["first band"]["A"] + result["second band"]["A"]
            + result["cap"]["A"]) == 35
    assert (result["first band"]["B"] + result["second band"]["B"]
            + result["cap"]["B"]) == 30
    return result


def full_sphere(topo):
    """The complete 2V icosphere, mirrored across the equator from the
    hemisphere the solver returns (the icosphere is symmetric about z=0)."""
    verts = list(topo.vertices)
    mirror: dict[int, int] = {}
    for i, v in enumerate(topo.vertices):
        if v[2] > EPS:
            mirror[i] = len(verts)
            verts.append(np.array([v[0], v[1], -v[2]]))
    edge_types: dict[tuple[int, int], str] = {}
    for key, edge in topo.edges.items():
        edge_types[key] = edge.edge_type
        if not edge.is_base:
            a, b = key
            if a in mirror and b in mirror:
                edge_types[(mirror[a], mirror[b])] = edge.edge_type
            elif a in mirror:
                edge_types[(mirror[a], b)] = edge.edge_type
            else:
                edge_types[(a, mirror[b])] = edge.edge_type
    assert len(edge_types) == 120, len(edge_types)
    assert len(verts) == 42, len(verts)
    return verts, edge_types


def variants(topo, the_rings: tuple[Ring, ...]) -> tuple[Variant, ...]:
    """Every flat, hub-level cut of the full 2V sphere, apex-up.

    Cuts pass exactly through a ring of hubs -- the heights are read from
    the solved mesh itself, so hubs lying on the cut are never lost to a
    rounding error.  Listed from the smallest (the cap) to the full sphere.
    """
    verts, edge_types = full_sphere(topo)
    apex_z = max(float(v[2]) for v in verts)
    ring2, hex1, pent1 = (the_rings[3].height_in, the_rings[2].height_in,
                          the_rings[1].height_in)

    def make(name: str, cut: float) -> Variant:
        kept = {i for i, v in enumerate(verts) if float(v[2]) >= cut - EPS}
        a = b = 0
        for (i, j), kind in edge_types.items():
            if i in kept and j in kept:
                if kind == "A":
                    a += 1
                else:
                    b += 1
        base = [i for i in kept if abs(float(verts[i][2]) - cut) < EPS]
        base_radius = 0.0
        if base:
            base_radius = max(float(np.linalg.norm(verts[i][:2]))
                              for i in base)
        perimeter = None
        if len(base) >= 2:
            linked = {frozenset(key) for key in edge_types
                      if key[0] in base and key[1] in base}
            if len(linked) == len(base):
                perimeter = sum(
                    float(np.linalg.norm(verts[i] - verts[j]))
                    for i, j in (tuple(s) for s in linked))
        return Variant(name, len(kept), len(base), a, b,
                       apex_z - cut, base_radius, perimeter)

    return (
        make("cap (cut through the pentagon band)", ring2),
        make("cut through the level-1 hexagon ring", hex1),
        make("cut through the level-1 pentagon ring", pent1),
        make("hemisphere (cut through the equator) — the seed dome", 0.0),
        make("cut through the lower pentagon ring", -pent1),
        make("cut through the lower hexagon ring", -hex1),
        make("full 2V sphere", -apex_z),
    )


def strut_angles(topo) -> dict[tuple[str, float], int]:
    """Count the shared struts by type and by angle from horizontal.

    Angles are bucketed at a tenth of a degree; the buckets that actually
    occur are the report's 'where each strut lives' column.
    """
    buckets: dict[tuple[str, float], int] = defaultdict(int)
    for (a, b), edge in topo.edges.items():
        vector = topo.vertices[b] - topo.vertices[a]
        angle = math.degrees(math.atan2(abs(float(vector[2])),
                                        float(np.linalg.norm(vector[:2]))))
        buckets[(edge.edge_type, round(angle * 10.0) / 10.0)] += 1
    return dict(sorted(buckets.items()))


def _triangle_kind(face, topo) -> str:
    kinds = [topo.edges[(min(face.vertices[i], face.vertices[j]),
                         max(face.vertices[i], face.vertices[j]))].edge_type
             for i, j in ((0, 1), (1, 2), (2, 0))]
    return "AAA" if kinds.count("A") == 3 else "BAB"


def _angle_phrase(angles: dict[tuple[str, float], int], kind: str) -> str:
    values = [f"{angle:.1f}° ({count})"
              for (edge_kind, angle), count in angles.items()
              if edge_kind == kind]
    return ", ".join(values)


def band_report() -> str:
    topo = _solve()
    the_rings = rings(topo)
    bands = band_faces(topo, the_rings)
    struts_by_band = band_struts(topo, bands)
    variants_ = variants(topo, the_rings)
    angles = strut_angles(topo)

    radius_in = float(topo.sphere_radius_in)
    long_in = float(topo.long_edge_in)
    short_in = float(topo.short_edge_in)
    height_in = radius_in
    base_chord_in = sum(float(e.length) for e in topo.edges.values()
                        if e.is_base)
    aaa = sum(1 for f in topo.faces if _triangle_kind(f, topo) == "AAA")
    bab = len(topo.faces) - aaa
    floor_diameter = 2.0 * radius_in

    lines: list[str] = []
    add = lines.append

    add("# 2V Geodesic Dome on a Six-Foot Member — Every Level, Ring and Slope")
    add("")
    add(f"Longest member (A strut): **{_ft_in(long_in)}**  ·  "
        f"second member (B strut): **{_ft_in(short_in)}**  ·  "
        f"sphere radius: **{radius_in:.3f} in** ({radius_in / 12.0:.4f} ft)")
    add(f"Dome height **{_ft_in(height_in)}** ({height_in / 12.0:.4f} ft)  ·  "
        f"floor diameter **{_ft_in(floor_diameter)}** "
        f"({floor_diameter / 12.0:.4f} ft)")
    add(f"Hubs: **26**  ·  shared struts: **65** (35 A + 30 B)  ·  "
        f"panels: **40** ({aaa} AAA + {bab} BAB)  ·  base: a 10-sided ring "
        f"of **{_ft_in(base_chord_in)}** of chord")
    add("")
    add("> Cross-checked figure for figure against Zip Tie Domes' published 2V")
    add("> calculator run at a six-foot A strut (the same check")
    add("> ``seed_model.validate_seed_model`` runs).  A = LONG, B = SHORT,")
    add("> per the package convention in ``two_v_demo/geometry.py``.")
    add("")

    # ---- 1. The levels -------------------------------------------------
    add("## 1 · The levels, floor to apex")
    add("")
    add("| level | hubs | hub kind | height | height (ft) | × radius | "
        "× A strut | % of dome height |")
    add("|---|---|---|---|---|---|---|---|")
    for ring in the_rings:
        kind = {5: "5-way pentagon", 6: "6-way hexagon",
                4: "4-way base"}[ring.valence]
        add(f"| {ring.name} | {len(ring.hubs)} | {kind} | "
            f"**{_ft_in(ring.height_in)}** | {ring.height_in / 12.0:.3f} | "
            f"{ring.height_in / radius_in:.5f} | "
            f"{ring.height_in / long_in:.4f} | "
            f"{ring.height_in / height_in * 100.0:.1f}% |")
    add("")
    add("The first band of triangles runs from the floor up to *two* rings at")
    add("two different heights: its 5 pentagon corners sit lower (")
    add(f"{_ft_in(the_rings[1].height_in)}) and its 5 hexagon corners sit higher")
    add(f"({_ft_in(the_rings[2].height_in)}) — a gap of "
        f"{_ft_in(the_rings[2].height_in - the_rings[1].height_in)}.  "
        "The level-2 band")
    add("is the pentagon band just outside the cap, and the cap itself is")
    add("the apex sitting on it.")
    add("")

    # ---- 2. The amount inward ------------------------------------------
    add("## 2 · The amount inward — radius, diameter, circumference of every ring")
    add("")
    add("| ring | hubs | ring radius | ring diameter | circle through the hubs | "
        "share of floor circle | inward step from below |")
    add("|---|---|---|---|---|---|")
    floor_r = the_rings[0].radius_in
    for order, ring in enumerate(the_rings):
        circum = 2.0 * math.pi * ring.radius_in
        step = the_rings[order - 1].radius_in - ring.radius_in if order else 0.0
        step_txt = f"**{_ft_in(step)}**" if order else "—"
        add(f"| {ring.name} | {len(ring.hubs)} | **{_ft_in(ring.radius_in)}** "
            f"({ring.radius_in / 12.0:.3f} ft) | {_ft_in(2.0 * ring.radius_in)} | "
            f"**{_ft_in(circum)}** ({circum / 12.0:.2f} ft) | "
            f"{ring.radius_in / floor_r * 100.0:.1f}% | {step_txt} |")
    add("")
    add("The base ring's hubs are joined by ten A struts, so the built floor is")
    add(f"a decagon of **{_ft_in(base_chord_in)}** of chord inside a "
        f"{_ft_in(2.0 * math.pi * floor_r)} circle.  The pentagon band under "
        "the apex is likewise")
    add("closed by five A struts, so its circle of "
        f"{_ft_in(2.0 * math.pi * the_rings[3].radius_in)} carries "
        f"{_ft_in(5.0 * long_in)} of actual chord.  The two level-1 rings are "
        "not strut-linked:")
    add("each hub there ties to the rings above and below, not sideways.")
    add("")

    # ---- 3. The slope ----------------------------------------------------
    add("## 3 · The slope between levels")
    add("")
    add("Meridian slope: the rise of a level against how far its circle has")
    add("stepped inward from the level below (the cone the dome surface")
    add("traces between two rings).")
    add("")
    add("| rise | inward (run) | rise : run | slope from horizontal | what it is |")
    add("|---|---|---|---|---|")
    slopes = (
        (the_rings[0], the_rings[1], "first band, up to the pentagon ring"),
        (the_rings[0], the_rings[2], "first band, up to the hexagon ring"),
        (the_rings[1], the_rings[3], "second band, pentagon ring to pentagon band"),
        (the_rings[2], the_rings[3], "second band, hexagon ring to pentagon band"),
        (the_rings[3], the_rings[4], "the cap, pentagon band to apex"),
    )
    for low, high, what in slopes:
        rise = high.height_in - low.height_in
        run = low.radius_in - high.radius_in
        angle = math.degrees(math.atan2(rise, run))
        add(f"| {_ft_in(rise)} | {_ft_in(run)} | {rise / run:.3f} | "
            f"**{angle:.1f}°** | {what} |")
    add("")
    add("Reading down the table: the walls go up nearly vertical, the shoulder")
    add("leans to roughly 45°, and the cap flattens to about 16° at the apex.")
    add("")

    # ---- 4. Struts --------------------------------------------------------
    add("## 4 · The two struts, and where each one lives")
    add("")
    add("| strut | length | chord factor | count | panel mix |")
    add("|---|---|---|---|---|")
    add(f"| A (long) | **{_ft_in(long_in)}** ({long_in / 12.0:.4f} ft) | "
        f"{long_in / radius_in:.5f} | 35 | AAA panels: {aaa} of 40 |")
    add(f"| B (short) | **{_ft_in(short_in)}** ({short_in / 12.0:.4f} ft) | "
        f"{short_in / radius_in:.5f} | 30 | BAB panels only: {bab} of 40 |")
    add("")
    add("Struts by band (each shared strut credited to its lowest band):")
    add("")
    add("| band | panels | A struts | B struts |")
    add("|---|---|---|---|")
    for band in ("first band", "second band", "cap"):
        add(f"| {band} | {len(bands[band])} | {struts_by_band[band]['A']} | "
            f"{struts_by_band[band]['B']} |")
    add("")
    add("Where the struts lean, measured edge by edge off the mesh (each")
    add("strut's own angle from horizontal — a strut also runs sideways")
    add("around the dome, so this differs from the meridian slopes above):")
    add("")
    add("| strut | angle from horizontal | count |")
    add("|---|---|---|")
    for (kind, angle), count in angles.items():
        add(f"| {kind} | {angle:.1f}° | {count} |")
    add("")
    add(f"A struts appear at {_angle_phrase(angles, 'A')}; B struts at "
        f"{_angle_phrase(angles, 'B')}.  The flat A struts are the base ring "
        "and the pentagon band's")
    add("ring; the steepest A struts climb the first band; the steepest B")
    add("struts climb from the floor to the pentagon corners, and the")
    add("gentlest B struts close the cap to the apex.")
    add("")

    # ---- 5. Variants ------------------------------------------------------
    add("## 5 · The variant ways to cut this same 2V sphere")
    add("")
    add("Every flat, hub-level truncation of the full 42-hub icosphere, from")
    add("the cap up.  A cut is only listed where it passes exactly through a")
    add("ring of hubs, so each base is flat with no strut trimmed.")
    add("")
    add("| variant | hubs | struts (A/B) | height | height ÷ floor diameter | "
        "base | base circle through the hubs |")
    add("|---|---|---|---|---|---|---|")
    fractions = []
    for var in variants_:
        fractions.append(var.height_in / floor_diameter)
        if var.base_hub_count <= 1:
            base_txt = "—"
            circle_txt = "—"
        elif var.base_chord_perimeter_in is not None:
            base_txt = (f"{var.base_hub_count} hubs, "
                        f"{_ft_in(var.base_chord_perimeter_in)} of chord")
            circle_txt = _ft_in(2.0 * math.pi * var.base_radius_in)
        else:
            base_txt = f"{var.base_hub_count} hubs (not strut-linked)"
            circle_txt = _ft_in(2.0 * math.pi * var.base_radius_in)
        add(f"| {var.name} | {var.hub_count} | {var.a_count} / {var.b_count} | "
            f"**{_ft_in(var.height_in)}** ({var.height_in / 12.0:.3f} ft) | "
            f"{var.height_in / floor_diameter:.4f} | {base_txt} | "
            f"{circle_txt} |")
    add("")
    fraction_phrase = ", ".join(f"{value:.3f}" for value in fractions)
    add("The classic dome-catalogue names (3/8, 4/9, 5/8) are nominal labels,")
    add("not exact fractions: none of them lands on a hub ring of the 2V")
    add("icosphere, so a builder who wants a flat, uncut base uses one of the")
    add(f"ring cuts above, which sit at {fraction_phrase} of the floor")
    add("diameter.")
    add("")

    # ---- 6. Same dome, four ways -------------------------------------------
    add("## 6 · The same heights, four ways of saying them")
    add("")
    add("| level | feet & inches | decimal feet | inches | × radius | "
        "× 6-ft strut | polar angle from vertical |")
    add("|---|---|---|---|---|---|---|")
    for ring in the_rings:
        polar = math.degrees(math.acos(
            max(-1.0, min(1.0, ring.height_in / radius_in))))
        add(f"| {ring.name} | **{_ft_in(ring.height_in)}** | "
            f"{ring.height_in / 12.0:.4f} | {ring.height_in:.2f} | "
            f"{ring.height_in / radius_in:.5f} | "
            f"{ring.height_in / long_in:.4f} | {polar:.2f}° |")
    add("")

    add("## Cross-check against the published calculator")
    add("")
    add("| figure | published (Zip Tie, 6-ft A) | this model | ok |")
    add("|---|---|---|---|")
    checks = {
        "dome height, ft": height_in / 12.0,
        "dome diameter, ft": floor_diameter / 12.0,
        "A strut, ft": long_in / 12.0,
        "B strut, ft": short_in / 12.0,
        "base perimeter, ft": base_chord_in / 12.0,
        "A strut count": float(sum(1 for e in topo.edges.values()
                                   if e.edge_type == "A")),
        "B strut count": float(sum(1 for e in topo.edges.values()
                                   if e.edge_type == "B")),
        "panel count": float(len(topo.faces)),
    }
    for label, published in PUBLISHED.items():
        mine = checks[label]
        tolerance = 0.5 if label.endswith("count") else 0.001
        ok = abs(mine - published) <= tolerance
        add(f"| {label} | {published:,.4f} | {mine:,.4f} | "
            f"{'yes' if ok else 'NO'} |")
    add("")
    return "\n".join(lines)


def main() -> None:
    report = band_report()
    print(report)
    out = __file__.rsplit(".", 1)[0] + ".md"
    with open(out, "w", encoding="utf-8") as handle:
        handle.write(report + "\n")
    print(f"\n[wrote {out}]")


if __name__ == "__main__":
    main()
