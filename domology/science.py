"""Book One's figures: the dome measured, and every worked-math box, named.

Nothing here restates a number another module already derives. The
icosahedron and the two strut classes come from ``two_v_demo.geometry``; the
jig angles from ``dome_forge.jigs``; the hubless counts from
``two_v_demo.hubless_geometry``; the frequency ladder and the twelve preset
domes from ``two_v_demo.world_facts``, which builds them with the simulator's
own model; the dome-against-box costs from ``al_build``; the pentagon proof
from ``two_v_demo.hex_geometry``; the milestones of the journey from this
repository's own history.

What this module adds are the few sums Book One makes that no film needed --
a sphere against a cube, a hemisphere against a house-shaped box, the missing
angle at each kind of vertex -- and one registry, :data:`SHEETS`, naming every
worked-math box the book prints and the function whose output it prints.

Every value is exported as a ``{{dm.*}}`` or ``{{hist.*}}`` token through
:func:`token_specs`, which ``two_v_demo.book_tokens`` loads with the rest.
"""

from __future__ import annotations

import math
import re
import subprocess
from dataclasses import dataclass
from datetime import date
from functools import lru_cache
from typing import Callable

from . import config

REFERENCE_LONG_IN = 72.0
"""The reference dome's long strut, in inches. Declared, not derived: it is
the size Dome Forge's jig shop and cover patterns were set up at, and the
72-inch board the 2V masterclass holds up beside its dome."""


# ----------------------------------------------------------------------
# The 2V hemisphere, counted
# ----------------------------------------------------------------------

@lru_cache(maxsize=1)
def two_v() -> dict:
    """Every count and angle of the 2V hemisphere, from the real geometry."""
    from two_v_demo.geometry import PHI, build_demo_geometry
    g = build_demo_geometry()
    classes = {c.name: c for c in g.edge_classes}
    short, long_ = classes["SHORT"], classes["LONG"]
    triangles = {t.side_names: t for t in g.triangle_classes}
    equilateral = next(t for sides, t in triangles.items() if len(set(sides)) == 1)
    isosceles = next(t for sides, t in triangles.items() if len(set(sides)) == 2)
    iso_angles = sorted(isosceles.angles_deg)
    hubs = {index for edge in g.hemisphere_edges for index in edge}
    return {
        "phi": PHI,
        "ico_vertices": len(g.raw_vertices),
        "ico_faces": len(g.base_faces),
        "ico_edges": len(g.ico_edges),
        "sphere_vertices": len(g.vertices),
        "sphere_faces": len(g.faces),
        "sphere_edges": len(g.edges),
        "hemi_faces": len(g.hemisphere_faces),
        "hemi_edges": len(g.hemisphere_edges),
        "hemi_hubs": len(hubs),
        "base_ring": len(g.base_ring),
        "short_factor": short.factor,
        "long_factor": long_.factor,
        "ratio": g.ratio,
        "short_count": short.hemisphere_count,
        "long_count": long_.hemisphere_count,
        "short_arc": short.central_angle_deg,
        "long_arc": long_.central_angle_deg,
        "equi_count": equilateral.hemisphere_count,
        "iso_count": isosceles.hemisphere_count,
        "iso_base": iso_angles[0],
        "iso_apex": iso_angles[-1],
        "equi_area": equilateral.planar_area_factor,
        "iso_area": isosceles.planar_area_factor,
    }


@lru_cache(maxsize=1)
def jigs() -> dict:
    """The two jigs' angles, straight from Dome Forge's verified cut list."""
    from dome_forge.jigs import jig_specs, vertex_report
    specs = {spec.key: spec for spec in jig_specs()}
    iso = specs["isosceles"]
    equi = specs["equilateral"]
    bevel = {}
    for spec in specs.values():
        for board in spec.boards:
            bevel.setdefault(board.edge_class, board.bevel)
    iso_miters = sorted(set(round(m, 6) for m in iso.miters))
    deficits = {row["triangles"]: row for row in vertex_report()
                if row["triangles"] in (5, 6)}
    return {
        "equi_needed": equi.triangles_needed,
        "iso_needed": iso.triangles_needed,
        "miter_equi": equi.miters[0],
        "miter_iso_low": iso_miters[0],
        "miter_iso_high": iso_miters[-1],
        "bevel_long": bevel["LONG"],
        "bevel_short": bevel["SHORT"],
        "deficit5": deficits[5]["deficit"],
        "deficit6": deficits[6]["deficit"],
        "vertices5": deficits[5]["count"],
        "vertices6": deficits[6]["count"],
    }


@lru_cache(maxsize=1)
def reference() -> dict:
    """The reference dome: the one with a 72-inch long strut."""
    from two_v_demo.geometry import DomeMeasurements
    t = two_v()
    radius_in = REFERENCE_LONG_IN / t["long_factor"]
    dome = DomeMeasurements(radius_in)
    sq = 144.0
    return {
        "long_in": REFERENCE_LONG_IN,
        "short_in": dome.short_center_length,
        "radius_in": radius_in,
        "radius_ft": radius_in / 12.0,
        "diameter_ft": dome.diameter / 12.0,
        "floor_sqft": dome.floor_area / sq,
        "skin_sqft": dome.spherical_skin_area / sq,
        "panel_sqft": dome.planar_panel_area / sq,
        "volume_ft3": dome.enclosed_volume / 1728.0,
    }


# ----------------------------------------------------------------------
# Why the shape is efficient
# ----------------------------------------------------------------------

@lru_cache(maxsize=1)
def efficiency() -> dict:
    """A sphere against a cube, and a hemisphere against a house-shaped box.

    The box is the one ``al_build``'s building comparison uses -- its floor,
    its 1.3-to-1 plan and its wall height -- so the pure-geometry answer here
    and the priced answer there describe the same two buildings.
    """
    import al_build
    t = two_v()
    sphere_to_cube = (36.0 * math.pi) ** (1.0 / 3.0) / 6.0
    floor = al_build.COMPARE_HOME_FLOOR_SF
    wall = al_build.COMPARE_HOME_WALL_FT
    width = math.sqrt(floor / 1.3)
    length = floor / width
    box_skin = 2.0 * wall * (width + length) + width * length
    radius = math.sqrt(floor / math.pi)
    curved = 2.0 * math.pi * radius ** 2
    panels = (t["equi_area"] * t["equi_count"] + t["iso_area"] * t["iso_count"]) \
        * radius ** 2
    return {
        "sphere_to_cube": sphere_to_cube,
        "sphere_saving": 1.0 - sphere_to_cube,
        "floor": floor,
        "wall": wall,
        "box_width": width,
        "box_length": length,
        "box_skin": box_skin,
        "box_per_floor": box_skin / floor,
        "dome_radius_ft": radius,
        "curved_skin": curved,
        "curved_per_floor": curved / floor,
        "panel_skin": panels,
        "panel_per_floor": panels / floor,
        "skin_saving": 1.0 - panels / box_skin,
    }


@lru_cache(maxsize=1)
def comparisons() -> dict:
    """``al_build``'s priced comparison: the same rates, two shapes."""
    import al_build
    return al_build.building_comparisons()


@lru_cache(maxsize=1)
def ladder() -> tuple:
    from two_v_demo.world_facts import frequency_ladder
    return frequency_ladder()


@lru_cache(maxsize=1)
def catalogue() -> dict:
    from two_v_demo.world_facts import dome_types
    types = dome_types()
    by_skin = sorted(types, key=lambda d: d.skin_per_floor)
    by_cost = sorted(types, key=lambda d: d.cost_per_sqft)
    return {"count": len(types), "best": by_skin[0], "worst": by_skin[-1],
            "cheapest": by_cost[0], "dearest": by_cost[-1],
            "smallest": min(types, key=lambda d: d.floor_sqft),
            "largest": max(types, key=lambda d: d.floor_sqft)}


@lru_cache(maxsize=1)
def hubless() -> object:
    from two_v_demo.hubless_geometry import hubless_summary
    return hubless_summary()


@lru_cache(maxsize=1)
def zome() -> object:
    from two_v_demo.zome_geometry import golden_zonohedron
    return golden_zonohedron()


# ----------------------------------------------------------------------
# The journey, from the repository's own history
# ----------------------------------------------------------------------

MILESTONES: tuple[tuple[str, str], ...] = (
    ("start", r"^Initial DomeSimulator"),
    ("assembly_line", r"assembly line simulation"),
    ("investor", r"investor decision tool"),
    ("presenter", r"presenter engine"),
    ("launcher", r"Consolidate every standalone tool"),
    ("forge", r"^Add Dome Forge"),
    ("hubless", r"hubless bolted triangles"),
    ("patterns", r"cover-pattern mode"),
    ("creed", r"Round House Creed"),
    ("master", r"master presentation"),
    ("scratch", r"from-scratch lesson"),
    ("wedge", r"radial-wedge build"),
    ("measured", r"argue the method in measured numbers"),
    ("mitre", r"Correct the mitre claim"),
)
"""Commit subjects that mark a turn in the project. The dates are read from
git, so the story's timeline cannot drift from what actually happened."""


@lru_cache(maxsize=1)
def history() -> dict:
    result = subprocess.run(
        ["git", "log", "--reverse", "--format=%ad|%s", "--date=short"],
        cwd=config.ROOT, capture_output=True, text=True, check=True)
    commits = [line.split("|", 1) for line in result.stdout.splitlines() if "|" in line]
    dates = {}
    for key, pattern in MILESTONES:
        for day, subject in commits:
            if re.search(pattern, subject, re.I):
                dates[key] = date.fromisoformat(day)
                break
    first = date.fromisoformat(commits[0][0])
    last = date.fromisoformat(commits[-1][0])
    return {"dates": dates, "commits": len(commits), "first": first, "last": last}


def _day(value: date) -> str:
    return f"{value.strftime('%B')} {value.day}, {value.year}"


# ----------------------------------------------------------------------
# Worked-math sheets
# ----------------------------------------------------------------------

def _conclude(rows: list[str], conclusion: str) -> tuple[str, ...]:
    rows.append(conclusion)
    return tuple(rows)


def sheet_reference() -> tuple[str, ...]:
    t, r = two_v(), reference()
    return _conclude([
        f"declared: long strut A = {r['long_in']:.0f} in (the tools' reference board)",
        f"radius R = A / {t['long_factor']:.6f} = {r['radius_in']:.2f} in "
        f"= {r['radius_ft']:.2f} ft",
        f"short strut B = {t['short_factor']:.6f} x R = {r['short_in']:.2f} in",
        f"diameter = 2R = {r['diameter_ft']:.2f} ft; height = R",
        f"floor = pi R^2 = {r['floor_sqft']:.0f} sq ft",
        f"curved skin = 2 pi R^2 = {r['skin_sqft']:.0f} sq ft; "
        f"flat panels {r['panel_sqft']:.0f} sq ft",
        f"volume = (2/3) pi R^3 = {r['volume_ft3']:,.0f} cu ft",
    ], f"two boards, {r['long_in']:.0f} in and {r['short_in']:.2f} in, "
       f"enclose {r['floor_sqft']:.0f} sq ft")


def sheet_sphere_box() -> tuple[str, ...]:
    e = efficiency()
    return _conclude([
        "equal volume, sphere against cube:",
        f"  area ratio = (36 pi)^(1/3) / 6 = {e['sphere_to_cube']:.4f}",
        f"  the sphere needs {e['sphere_saving'] * 100:.1f}% less skin",
        f"equal floor, {e['floor']:.0f} sq ft, a hemisphere against a box house:",
        f"  box {e['box_width']:.1f} x {e['box_length']:.1f} ft, walls "
        f"{e['wall']:.0f} ft, flat roof",
        f"  box skin = walls + roof = {e['box_skin']:,.0f} sq ft "
        f"({e['box_per_floor']:.2f} per sq ft of floor)",
        f"  hemisphere radius {e['dome_radius_ft']:.1f} ft: curved skin "
        f"{e['curved_skin']:,.0f} sq ft ({e['curved_per_floor']:.2f})",
        f"  its 2V flat panels: {e['panel_skin']:,.0f} sq ft "
        f"({e['panel_per_floor']:.2f})",
    ], f"same floor, {e['skin_saving'] * 100:.0f}% less envelope to build, "
       "insulate and seal")


def sheet_comparisons() -> tuple[str, ...]:
    c = comparisons()
    shed, home = c["shed"], c["home"]
    rows = ["one rate card, two shapes (al_build's comparison):",
            f"storage shed, matched on volume ({shed['box']['vol_ft3']:,.0f} cu ft):"]
    for key in ("box", "dome"):
        d = shed[key]
        rows.append(f"  {d['name']:<5} framing {d['framing_lf']:>6,.0f} ft  skin "
                    f"{d['cladding_sf']:>6,.0f} sq ft  build ${d['build']:>8,.0f}")
    rows.append(f"home, finished, matched on floor ({home['box']['floor_sf']:,.0f} sq ft):")
    for key in ("box", "dome"):
        d = home[key]
        rows.append(f"  {d['name']:<5} envelope {d['cladding_sf']:>6,.0f} sq ft  "
                    f"build ${d['build']:>9,.0f}  (${d['per_sf']:,.0f}/sq ft)")
    shed_cut = 1.0 - shed["dome"]["build"] / shed["box"]["build"]
    home_cut = 1.0 - home["dome"]["build"] / home["box"]["build"]
    return _conclude(rows, f"the dome costs {shed_cut * 100:.0f}% less as a bare "
                           f"shell and {home_cut * 100:.0f}% less finished -- the "
                           "fit-out is the same either way, which is why the "
                           "gap narrows")


def sheet_deficit() -> tuple[str, ...]:
    j = jigs()
    t = two_v()
    return _conclude([
        f"a flat equilateral corner is 60 deg; six fill 360 deg exactly (flat)",
        f"at a 5-way hub the flat corners sum to {360 - j['deficit5']:.2f} deg: "
        f"short by {j['deficit5']:.2f}",
        f"at a 6-way hub they sum to {360 - j['deficit6']:.2f} deg: "
        f"short by {j['deficit6']:.2f}",
        f"this hemisphere: {j['vertices5']} five-way hubs, {j['vertices6']} six-way",
        "Descartes: a closed convex cage is short exactly 720 deg in total",
        f"the icosahedron's {t['ico_vertices']} corners x 60 deg = 720 deg",
    ], "the missing angle is not a flaw to hide -- it is the curve")


def sheet_jigs() -> tuple[str, ...]:
    j, t = jigs(), two_v()
    return _conclude([
        f"{t['hemi_faces']} triangles, two shapes:",
        f"  jig A, equilateral: {j['equi_needed']} needed, corners 60 deg, "
        f"saw miter {j['miter_equi']:.3f} deg",
        f"  jig B, isosceles: {j['iso_needed']} needed, corners "
        f"{t['iso_base']:.3f} / {t['iso_base']:.3f} / {t['iso_apex']:.3f} deg",
        f"    saw miters {j['miter_iso_high']:.3f} and {j['miter_iso_low']:.3f} deg",
        f"  edge bevel: {j['bevel_long']:.4f} deg on LONG, "
        f"{j['bevel_short']:.4f} deg on SHORT",
        "every angle re-measured off the assembled 3-D faces before the "
        "shop drawing is trusted",
    ], f"two jigs make all {t['hemi_faces']} triangles")


def sheet_hubless() -> tuple[str, ...]:
    h = hubless()
    return _conclude([
        f"{h.triangles} triangles, each bringing its own three members:",
        f"  {h.triangles} x 3 = {h.struts} members",
        f"  {h.unique_edges} edges: {h.doubled_edges} shared seams (two members "
        f"each) + {h.rim_edges} rim edges (one)",
        f"  check: {h.doubled_edges} x 2 + {h.rim_edges} = {h.strut_check}",
        f"  {h.setups} distinct compound saw setups; {h.setups_past_saw} past a "
        "typical saw's stop",
    ], "no hubs to buy: the joint is the seam between two panels")


def sheet_pentagons() -> tuple[str, ...]:
    from two_v_demo.hex_geometry import euler_pentagon_proof
    rows = list(euler_pentagon_proof(20).lines)
    rows.append(f"try any number of hexagons: "
                f"{', '.join(str(euler_pentagon_proof(h).pentagons) for h in (0, 20, 110))}")
    return _conclude(rows, "a closed cage of pentagons and hexagons always has "
                           "exactly twelve pentagons")


@dataclass(frozen=True)
class Sheet:
    key: str
    title: str
    source: str
    rows: Callable[[], tuple[str, ...]]


def _call(module: str, name: str) -> Callable[[], tuple[str, ...]]:
    def run() -> tuple[str, ...]:
        import importlib
        return tuple(getattr(importlib.import_module(module), name)())
    return run


def _local(function: Callable[[], tuple[str, ...]]) -> Callable[[], tuple[str, ...]]:
    return function


_FILM = [
    ("phi", "Twelve points from one ratio", "two_v_demo.scratch_facts", "steps_phi"),
    ("normalize", "Onto the sphere", "two_v_demo.scratch_facts", "steps_normalize"),
    ("euler", "Euler's count", "two_v_demo.scratch_facts", "steps_euler"),
    ("midpoint", "Split every edge", "two_v_demo.scratch_facts", "steps_midpoint"),
    ("project", "Push the midpoints out", "two_v_demo.scratch_facts", "steps_project"),
    ("chords", "Two lengths fall out", "two_v_demo.scratch_facts", "steps_chords"),
    ("counts", "Counting the half sphere", "two_v_demo.scratch_facts", "steps_counts"),
    ("scale", "From factors to inches", "two_v_demo.scratch_facts", "steps_scale"),
    ("frequency", "What frequency costs", "two_v_demo.world_facts", "steps_frequency"),
    ("hub_vs_hubless", "Hubs or no hubs", "two_v_demo.world_facts", "steps_hub_vs_hubless"),
    ("catalogue_cost", "Twelve designs, priced", "two_v_demo.world_facts", "steps_economics"),
    ("efficiency", "Skin per square foot of floor", "two_v_demo.world_facts",
     "steps_efficiency"),
    ("size", "Size is a number you type", "two_v_demo.world_facts", "steps_scale"),
    ("catalogue", "Twelve designs, counted", "two_v_demo.world_facts", "steps_catalogue"),
    ("yield", "What a tree keeps", "two_v_demo.wedge_why_facts", "steps_yield"),
    ("mills", "The machines you never buy", "two_v_demo.wedge_why_facts", "steps_mills"),
    ("middlemen", "Fifteen hands between the tree and the rack",
     "two_v_demo.wedge_why_facts", "steps_middlemen"),
    ("wedge_value", "What one wedge is worth", "two_v_demo.wedge_why_facts", "steps_value"),
    ("structure", "Strong enough?", "two_v_demo.wedge_why_facts", "steps_structure"),
    ("orientation", "Four ways round", "two_v_demo.wedge_why_facts", "steps_orientation"),
    ("dihedral", "Two fold angles", "two_v_demo.wedge_why_facts", "steps_dihedral"),
    ("wedge_jig", "One jig, forty panels", "two_v_demo.wedge_why_facts", "steps_jig"),
    ("buttcut", "The one compound cut", "two_v_demo.wedge_why_facts", "steps_buttcut"),
    ("defects", "Bends, knots and small units", "two_v_demo.wedge_why_facts",
     "steps_defects"),
    ("rate", "Two timed sessions", "two_v_demo.wedge_why_facts", "steps_rate"),
    ("house_sources", "What the house figures rest on", "two_v_demo.house_economics",
     "source_lines"),
    ("why_sources", "The author's figures, beside the published ones",
     "two_v_demo.why_build_economics", "source_lines"),
    ("score", "One shell on one sheet", "two_v_demo.why_build_economics", "score_lines"),
    ("pine_sources", "What the pine's ladder rests on",
     "two_v_demo.pine_value_economics", "source_lines"),
    ("harvest_measured", "What was measured, and what was not",
     "two_v_demo.lesson_harvest", "assumption_lines"),
]

SHEETS: dict[str, Sheet] = {
    key: Sheet(key, title, f"{module}.{name}", _call(module, name))
    for key, title, module, name in _FILM
}
SHEETS.update({
    "reference": Sheet("reference", "The reference dome", "domology.science.sheet_reference",
                       sheet_reference),
    "sphere_box": Sheet("sphere_box", "Sphere against box",
                        "domology.science.sheet_sphere_box", sheet_sphere_box),
    "comparisons": Sheet("comparisons", "The same rate card, two shapes",
                         "al_build.building_comparisons", sheet_comparisons),
    "deficit": Sheet("deficit", "The missing angle", "dome_forge.jigs.vertex_report",
                     sheet_deficit),
    "jigs": Sheet("jigs", "Two jigs build the dome", "dome_forge.jigs.jig_specs",
                  sheet_jigs),
    "hubless": Sheet("hubless", "A hubless frame, counted",
                     "two_v_demo.hubless_geometry.hubless_summary", sheet_hubless),
    "pentagons": Sheet("pentagons", "Always twelve pentagons",
                       "two_v_demo.hex_geometry.euler_pentagon_proof", sheet_pentagons),
})


@lru_cache(maxsize=None)
def sheet_rows(key: str) -> tuple[str, ...]:
    return SHEETS[key].rows()


# ----------------------------------------------------------------------
# Tokens
# ----------------------------------------------------------------------

def token_specs() -> list[tuple[str, str, Callable[[], str]]]:
    """(name, description, compute) for every ``{{dm.*}}`` and ``{{hist.*}}``."""
    from two_v_demo.book_tokens import _n, _pct

    t, j, r, e = two_v, jigs, reference, efficiency

    specs = [
        ("dm.phi", "the golden ratio, phi", lambda: f"{t()['phi']:.6f}"),
        ("dm.ico_vertices", "corners of an icosahedron", lambda: str(t()["ico_vertices"])),
        ("dm.ico_faces", "faces of an icosahedron", lambda: str(t()["ico_faces"])),
        ("dm.ico_edges", "edges of an icosahedron", lambda: str(t()["ico_edges"])),
        ("dm.euler", "V - E + F for the icosahedron",
         lambda: str(t()["ico_vertices"] - t()["ico_edges"] + t()["ico_faces"])),
        ("dm.sphere_vertices", "hubs of the full 2V sphere", lambda: str(t()["sphere_vertices"])),
        ("dm.sphere_faces", "triangles of the full 2V sphere", lambda: str(t()["sphere_faces"])),
        ("dm.sphere_edges", "struts of the full 2V sphere", lambda: str(t()["sphere_edges"])),
        ("dm.hemi_faces", "triangles in the 2V hemisphere", lambda: str(t()["hemi_faces"])),
        ("dm.hemi_edges", "struts in a hubbed 2V hemisphere", lambda: str(t()["hemi_edges"])),
        ("dm.hemi_hubs", "hubs in the 2V hemisphere", lambda: str(t()["hemi_hubs"])),
        ("dm.base_ring", "hubs on the ground ring", lambda: str(t()["base_ring"])),
        ("dm.short_factor", "short chord factor (B / R)", lambda: f"{t()['short_factor']:.4f}"),
        ("dm.long_factor", "long chord factor (A / R)", lambda: f"{t()['long_factor']:.4f}"),
        ("dm.ratio", "long strut over short strut", lambda: f"{t()['ratio']:.4f}"),
        ("dm.short_count", "short struts in a hubbed hemisphere", lambda: str(t()["short_count"])),
        ("dm.long_count", "long struts in a hubbed hemisphere", lambda: str(t()["long_count"])),
        ("dm.short_arc", "arc a short strut spans, degrees", lambda: f"{t()['short_arc']:.2f}"),
        ("dm.long_arc", "arc a long strut spans, degrees", lambda: f"{t()['long_arc']:.2f}"),
        ("dm.equi_count", "equilateral triangles in the hemisphere", lambda: str(t()["equi_count"])),
        ("dm.iso_count", "isosceles triangles in the hemisphere", lambda: str(t()["iso_count"])),
        ("dm.iso_base", "isosceles base angle, degrees", lambda: f"{t()['iso_base']:.2f}"),
        ("dm.iso_apex", "isosceles apex angle, degrees", lambda: f"{t()['iso_apex']:.2f}"),
        ("dm.miter_equi", "saw miter for jig A, degrees", lambda: f"{j()['miter_equi']:.1f}"),
        ("dm.miter_iso_low", "smaller saw miter for jig B", lambda: f"{j()['miter_iso_low']:.2f}"),
        ("dm.miter_iso_high", "larger saw miter for jig B", lambda: f"{j()['miter_iso_high']:.2f}"),
        ("dm.bevel_long", "edge bevel on a long board, degrees", lambda: f"{j()['bevel_long']:.2f}"),
        ("dm.bevel_short", "edge bevel on a short board, degrees", lambda: f"{j()['bevel_short']:.2f}"),
        ("dm.deficit5", "angle missing at a 5-way hub, degrees", lambda: f"{j()['deficit5']:.2f}"),
        ("dm.deficit6", "angle missing at a 6-way hub, degrees", lambda: f"{j()['deficit6']:.2f}"),
        ("dm.vertices5", "five-way hubs in the hemisphere", lambda: str(j()["vertices5"])),
        ("dm.vertices6", "six-way hubs in the hemisphere", lambda: str(j()["vertices6"])),
        ("dm.descartes", "total missing angle of any closed cage", lambda: "720"),
        ("dm.ref_long_in", "the reference dome's long strut, inches", lambda: _n(r()["long_in"], 0)),
        ("dm.ref_short_in", "its short strut, inches", lambda: f"{r()['short_in']:.2f}"),
        ("dm.ref_radius_in", "its radius, inches", lambda: f"{r()['radius_in']:.1f}"),
        ("dm.ref_radius_ft", "its radius, feet", lambda: f"{r()['radius_ft']:.2f}"),
        ("dm.ref_diameter_ft", "its diameter, feet", lambda: f"{r()['diameter_ft']:.1f}"),
        ("dm.ref_floor_sqft", "its floor, square feet", lambda: _n(r()["floor_sqft"], 0)),
        ("dm.ref_skin_sqft", "its curved skin, square feet", lambda: _n(r()["skin_sqft"], 0)),
        ("dm.ref_panel_sqft", "its flat panels, square feet", lambda: _n(r()["panel_sqft"], 0)),
        ("dm.ref_volume_ft3", "its volume, cubic feet", lambda: _n(r()["volume_ft3"], 0)),
        ("dm.sphere_saving_pct", "less skin a sphere needs than a cube of the same volume",
         lambda: f"{e()['sphere_saving'] * 100:.1f}"),
        ("dm.box_floor", "the comparison house's floor, square feet", lambda: _n(e()["floor"], 0)),
        ("dm.box_wall_ft", "its wall height, feet", lambda: _n(e()["wall"], 0)),
        ("dm.box_skin", "the box house's walls and roof, square feet", lambda: _n(e()["box_skin"], 0)),
        ("dm.box_per_floor", "box skin per square foot of floor", lambda: f"{e()['box_per_floor']:.2f}"),
        ("dm.curved_per_floor", "hemisphere skin per square foot of floor",
         lambda: f"{e()['curved_per_floor']:.2f}"),
        ("dm.panel_skin", "2V panels over the same floor, square feet", lambda: _n(e()["panel_skin"], 0)),
        ("dm.panel_per_floor", "2V panel area per square foot of floor",
         lambda: f"{e()['panel_per_floor']:.2f}"),
        ("dm.skin_saving_pct", "less envelope than the box house, same floor",
         lambda: _pct(e()["skin_saving"], 0)),
        ("dm.presets", "designs in the Dome Creator catalogue", lambda: str(catalogue()["count"])),
        ("dm.best_skin_name", "the catalogue's most skin-efficient design",
         lambda: catalogue()["best"].name),
        ("dm.best_skin", "its skin per floor", lambda: f"{catalogue()['best'].skin_per_floor:.2f}"),
        ("dm.worst_skin_name", "the least skin-efficient design", lambda: catalogue()["worst"].name),
        ("dm.worst_skin", "its skin per floor", lambda: f"{catalogue()['worst'].skin_per_floor:.2f}"),
        ("dm.cheapest_sqft", "lowest cost per square foot in the catalogue",
         lambda: _n(catalogue()["cheapest"].cost_per_sqft, 0)),
        ("dm.dearest_sqft", "highest cost per square foot in the catalogue",
         lambda: _n(catalogue()["dearest"].cost_per_sqft, 0)),
        ("dm.hubless_struts", "members in a hubless hemisphere", lambda: str(hubless().struts)),
        ("dm.hubless_doubled", "shared seams in the hubless frame", lambda: str(hubless().doubled_edges)),
        ("dm.hubless_rim", "rim edges", lambda: str(hubless().rim_edges)),
        ("dm.hubless_setups", "distinct compound saw setups", lambda: str(hubless().setups)),
        ("dm.hubless_past_saw", "setups past a typical saw's stop", lambda: str(hubless().setups_past_saw)),
        ("dm.pentagons", "pentagons in any closed pentagon-hexagon cage", lambda: "12"),
        ("dm.zome_generators", "generators of the golden zonohedron", lambda: str(zome().generator_count)),
        ("dm.zome_faces", "rhombic faces of the golden zonohedron", lambda: str(len(zome().faces))),
        ("dm.zome_shapes", "distinct panel shapes in it", lambda: str(zome().panel_shapes)),
    ]

    def shed(key, part):
        return lambda: comparisons()["shed"][key][part]

    def home(key, part):
        return lambda: comparisons()["home"][key][part]

    c = comparisons
    specs += [
        ("dm.shed_volume", "the volume both sheds enclose, cubic feet",
         lambda: _n(c()["shed"]["box"]["vol_ft3"], 0)),
        ("dm.shed_box_skin", "the box shed's skin, square feet", lambda: _n(shed("box", "cladding_sf")(), 0)),
        ("dm.shed_dome_skin", "the dome shed's skin, square feet", lambda: _n(shed("dome", "cladding_sf")(), 0)),
        ("dm.shed_box_frame", "the box shed's framing, feet", lambda: _n(shed("box", "framing_lf")(), 0)),
        ("dm.shed_dome_frame", "the dome shed's framing, feet", lambda: _n(shed("dome", "framing_lf")(), 0)),
        ("dm.shed_box_cost", "the box shed, built", lambda: _n(shed("box", "build")(), 0)),
        ("dm.shed_dome_cost", "the dome shed, built", lambda: _n(shed("dome", "build")(), 0)),
        ("dm.shed_cut_pct", "the dome shed's saving",
         lambda: _pct(1.0 - shed("dome", "build")() / shed("box", "build")(), 0)),
        ("dm.home_floor", "the finished homes' floor, square feet", lambda: _n(home("box", "floor_sf")(), 0)),
        ("dm.home_box_skin", "the box home's envelope, square feet", lambda: _n(home("box", "cladding_sf")(), 0)),
        ("dm.home_dome_skin", "the dome home's envelope, square feet", lambda: _n(home("dome", "cladding_sf")(), 0)),
        ("dm.home_box_cost", "the box home, finished", lambda: _n(home("box", "build")(), 0)),
        ("dm.home_dome_cost", "the dome home, finished", lambda: _n(home("dome", "build")(), 0)),
        ("dm.home_cut_pct", "the finished dome's saving",
         lambda: _pct(1.0 - home("dome", "build")() / home("box", "build")(), 0)),
    ]

    for position in range(4):
        def step(i=position):
            return ladder()[i]
        f = position + 1
        specs += [
            (f"dm.f{f}_struts", f"struts in a {f}V dome", lambda s=step: str(s().struts)),
            (f"dm.f{f}_classes", f"strut lengths in a {f}V dome", lambda s=step: str(s().strut_classes)),
            (f"dm.f{f}_panels", f"panels in a {f}V dome", lambda s=step: str(s().panels)),
            (f"dm.f{f}_hubs", f"hubs in a {f}V dome", lambda s=step: str(s().hubs)),
        ]

    h = history
    for key, _pattern in MILESTONES:
        specs.append((f"hist.{key}", f"the day the history records: {key.replace('_', ' ')}",
                      lambda k=key: _day(h()["dates"][k])))
    specs += [
        ("hist.commits", "commits in the project's history", lambda: str(h()["commits"])),
        ("hist.first", "the first commit", lambda: _day(h()["first"])),
        ("hist.last", "the latest commit", lambda: _day(h()["last"])),
        ("hist.days", "days from the first commit to the latest",
         lambda: str((h()["last"] - h()["first"]).days)),
        ("hist.days_to_wedge", "days from the first commit to the wedge build",
         lambda: str((h()["dates"]["wedge"] - h()["first"]).days)),
        ("hist.days_to_forge", "days from the first commit to Dome Forge",
         lambda: str((h()["dates"]["forge"] - h()["first"]).days)),
    ]
    return specs


def validate_science() -> None:
    t = two_v()
    assert (t["ico_vertices"], t["ico_faces"], t["ico_edges"]) == (12, 20, 30)
    assert t["ico_vertices"] - t["ico_edges"] + t["ico_faces"] == 2
    assert (t["hemi_faces"], t["hemi_edges"], t["hemi_hubs"]) == (40, 65, 26)
    assert t["short_count"] + t["long_count"] == t["hemi_edges"]
    assert t["equi_count"] + t["iso_count"] == t["hemi_faces"]
    j = jigs()
    assert 0 < j["deficit5"] < j["deficit6"] < 30
    r = reference()
    assert abs(r["short_in"] - REFERENCE_LONG_IN / t["ratio"]) < 1e-9
    e = efficiency()
    assert 0.0 < e["sphere_saving"] < 0.25 and e["skin_saving"] > 0
    for key, sheet in SHEETS.items():
        rows = sheet_rows(key)
        assert len(rows) >= 2 and all(isinstance(row, str) for row in rows), key
    specs = token_specs()
    names = [name for name, _d, _c in specs]
    assert len(names) == len(set(names)), "a token is defined twice"
    for name, describe, compute in specs:
        assert describe and compute() not in ("", None), name
