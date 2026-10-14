"""Core wedge-building arithmetic shared by books, concepts and films.

The nominal reference uses the live raw-wedge solver through seed_model.
Pair coverage is an explicit planning assumption, not a solved joint. The
opposed-point section experiment is separate from all-points-inward infill.
Neither its span nor its void fraction establishes weather or load performance.
"""

from __future__ import annotations

import math
from functools import lru_cache

import numpy as np

EXTERNAL_CONSTANTS = (
    ("usable_trunk_ft", 60.0, "ft", "assumption", "straight usable trunk at uniform reference diameter, not tree height"),
    ("frame_blank_in", 72.0, "in", "assumption", "one six-foot blank per frame member, before cuts and kerf"),
    ("opening_inset_fraction", 0.5, "wedge chord", "assumption", "planning inset only; actual tray openings come from infill.frame"),
)
D = {name: value for name, value, *_ in EXTERNAL_CONSTANTS}
OVERLAPS = (0.0, 0.25, 0.5, 0.75, 1.0)


def _positive(value: float, name: str) -> float:
    value = float(value)
    if not math.isfinite(value) or value <= 0:
        raise ValueError(f"{name} must be finite and positive")
    return value


def coverage_length(area_sqft: float, pair_pitch_in: float, pieces_per_pair: int = 2) -> float:
    """Wedge footage from CONTINUOUS measured/assumed face pitch, not section span."""
    area_sqft = float(area_sqft)
    if not math.isfinite(area_sqft) or area_sqft < 0:
        raise ValueError("area must be finite and nonnegative")
    pitch = _positive(pair_pitch_in, "continuous pair pitch")
    if not isinstance(pieces_per_pair, int) or pieces_per_pair < 1:
        raise ValueError("pieces_per_pair must be a positive integer")
    return pieces_per_pair * area_sqft * 12.0 / pitch


def pair_section(log_in: float, splits: int, engagement: float) -> dict:
    """Ideal CHORD triangles with opposed points, not curved raw sectors.

    The cell is an assumed periodic envelope of width w and depth h(2-p).
    Two unchanged triangles have area wh, so their solid fraction is 1/(2-p).
    This depth is not a face-coverage pitch and is never used in the takeoff.
    """
    log_in = _positive(log_in, "log diameter")
    if not isinstance(splits, int) or splits < 3:
        raise ValueError("splits must be an integer of at least three")
    p = float(engagement)
    if not math.isfinite(p) or not 0 <= p <= 1:
        raise ValueError("engagement must lie between zero and one")
    radius = log_in / 2.0
    half = math.pi / splits
    width = log_in * math.sin(half)
    height = radius * math.cos(half)
    return {"engagement": p, "chord_in": width, "height_in": height,
            "span_in": height * (2 - p), "contact_in": radius * p,
            "solid_fraction": 1 / (2 - p), "void_fraction": 1 - 1 / (2 - p),
            "wood_area_in2": width * height}


def _budget(faces, nominal_ft, finished_ft, member_count, log_in, splits,
            blank_in, trunk_ft, inset_fraction) -> dict:
    """faces holds (count, area in sq ft, perimeter in inches)."""
    log_in = _positive(log_in, "log diameter")
    blank_in = _positive(blank_in, "blank length")
    trunk_ft = _positive(trunk_ft, "usable trunk")
    section = pair_section(log_in, splits, 0)
    inset = float(inset_fraction) * section["chord_in"]
    if not math.isfinite(inset) or inset < 0:
        raise ValueError("opening inset must be finite and nonnegative")
    area = sum(count * a for count, a, _ in faces)
    opening = sum(count * a * max(0.0, 1 - inset / (2 * a * 144 / perimeter)) ** 2
                  for count, a, perimeter in faces)
    gross_frame = member_count * blank_in / 12
    frame_trunk = gross_frame / splits
    tree_rounds = math.floor(trunk_ft * 12 / blank_in + 1e-9)
    rows = []
    for overlap in OVERLAPS:
        pitch = (2 - overlap) * section["chord_in"]
        infill = coverage_length(opening, pitch)
        raw = frame_trunk + infill / splits
        rows.append({"overlap": overlap, "pair_pitch_in": pitch, "infill_ft": infill,
                     "infill_trunk_ft": infill / splits, "finished_total_ft": finished_ft + infill,
                     "nominal_total_ft": nominal_ft + infill, "raw_trunk_ft": raw,
                     "tree_equivalents": raw / trunk_ft, "whole_tree_equivalents": math.ceil(raw / trunk_ft)})
    return {"log_in": log_in, "splits": splits, "blank_in": blank_in, "trunk_ft": trunk_ft,
            "inset_fraction": inset_fraction, "inset_in": inset, "chord_in": section["chord_in"],
            "area_sqft": area, "opening_sqft": opening, "nominal_frame_ft": nominal_ft,
            "finished_frame_ft": finished_ft, "members": member_count,
            "gross_frame_ft": gross_frame, "frame_trunk_ft": frame_trunk,
            "rounds_per_tree": tree_rounds, "wedges_per_tree": tree_rounds * splits,
            "tree_wedge_ft": trunk_ft * splits, "rows": rows,
            "pair_sections": [pair_section(log_in, splits, p) for p in OVERLAPS]}


@lru_cache(maxsize=8)
def reference(long_chord_in: float = 72.0, log_in: float = 12.0) -> dict:
    """Nominal-chord example; physical member lengths come from the same solver."""
    import seed_model as seed
    geo = seed.seed_geometry(_positive(long_chord_in, "long chord"), _positive(log_in, "log diameter"))
    result = _budget([(f.count, f.area_sqft, f.perimeter_in) for f in geo.faces],
                     sum(f.count * f.perimeter_in for f in geo.faces) / 12,
                     geo.member_stock_ft, geo.member_count, log_in, seed.SEED_RADIAL_SPLITS,
                     D["frame_blank_in"], D["usable_trunk_ft"], D["opening_inset_fraction"])
    if max(m.stock_length_in for m in geo.members) > result["blank_in"] + 1e-6:
        raise ValueError("this reference requires longer frame blanks; use a stock cutting plan")
    result.update(long_in=geo.long_edge_in, short_in=geo.short_edge_in,
                  panel_count=sum(f.count for f in geo.faces), shared_edges=sum(r[1] for r in geo.geodesic_edges),
                  scale_basis="nominal long chord", faces=[{"name": f.name, "count": f.count, "area_sqft": f.area_sqft} for f in geo.faces])
    result["equilateral_panels"] = sum(f.count for f in geo.faces if math.isclose(f.perimeter_in, 3*geo.long_edge_in))
    result["isosceles_panels"] = result["panel_count"] - result["equilateral_panels"]
    return result


@lru_cache(maxsize=1)
def live() -> dict:
    """The infill tool's max-FINISHED-member case, explicitly a different scale."""
    from .frame import Spec, solve
    from .geom2d import area
    spec = Spec()
    types = solve(spec)["types"]
    result = _budget([(t.count, area(t.tri) / 144, sum(t.edge_len)) for t in types],
                     sum(t.count * sum(t.edge_len) for t in types) / 12,
                     sum(t.count * sum(t.member_len) for t in types) / 12,
                     sum(t.count * len(t.member_len) for t in types), spec.frame_log_in, spec.splits,
                     spec.max_strut_in, D["usable_trunk_ft"], D["opening_inset_fraction"])
    result.update(long_in=max(max(t.edge_len) for t in types), short_in=min(min(t.edge_len) for t in types),
                  panel_count=sum(t.count for t in types), scale_basis="maximum finished member",
                  solved_opening_sqft=sum(t.count * area(t.opening(0)) for t in types) / 144)
    return result


@lru_cache(maxsize=8)
def pentagon(side_in: float | None = None) -> dict:
    """Golden-ratio centreline identities, derived from the existing floor polygon."""
    from .base import BaseOptions, pentagon as floor_polygon
    side = _positive(BaseOptions().side_in if side_in is None else side_in, "pentagon side")
    points = floor_polygon(side)
    diagonal = float(np.linalg.norm(points[2] - points[0]))
    phi = diagonal / side
    long = diagonal - side
    short = diagonal - 2 * long
    def angle(a, b):
        return math.degrees(math.acos(float(np.clip(a @ b / np.linalg.norm(a) / np.linalg.norm(b), -1, 1))))
    interior = angle(points[4] - points[0], points[1] - points[0])
    diagonal_angle = angle(points[2] - points[0], points[1] - points[0])
    return {"side_in": side, "phi": phi, "diagonal_in": diagonal, "long_in": long, "short_in": short,
            "long_count": 2 * len(points), "short_count": len(points), "perimeter_count": len(points),
            "interior_deg": interior, "turn_deg": 180 - interior, "miter_deg": (180 - interior) / 2,
            "butt_deg": abs(interior - 90), "diagonal_deg": diagonal_angle,
            "diagonal_butt_deg": abs(90 - diagonal_angle),
            "interior_ft": len(points) * diagonal / 12,
            "all_ft": len(points) * (side + diagonal) / 12,
            "ideal_stock_logs": 3 * len(points), "spare_short_count": len(points)}


def assumptions() -> str:
    f = reference()
    return "\n".join([f"Reference long CHORD {f['long_in']:g} in; log {f['log_in']:g} in; {f['splits']} radial splits",
                      *(f"{n} = {v:g} {u} ({kind}): {why}" for n, v, u, kind, why in EXTERNAL_CONSTANTS),
                      "pair pitch = (2 - overlap) x outer chord: ASSUMED continuous one-face coverage",
                      "opposed-point span is a different axis/model; not all-points-inward seating",
                      "no allowance for kerf, taper, defects, seals, course offcuts or packing losses"])


def token_values() -> dict[str, str]:
    f, g = reference(), pentagon()
    values = {"wm." + key: f"{f[key]:,.2f}" for key in
              ("long_in", "short_in", "chord_in", "area_sqft", "opening_sqft", "nominal_frame_ft", "finished_frame_ft",
               "gross_frame_ft", "frame_trunk_ft", "trunk_ft", "tree_wedge_ft", "inset_in", "log_in", "blank_in")}
    values.update({"wm." + key: str(f[key]) for key in ("members", "panel_count", "equilateral_panels", "isosceles_panels", "shared_edges", "splits", "wedges_per_tree", "rounds_per_tree")})
    for label, row in (("least", f["rows"][0]), ("most", f["rows"][-1])):
        for key in ("infill_ft", "infill_trunk_ft", "raw_trunk_ft", "nominal_total_ft"):
            values[f"wm.{label}_{key}"] = f"{row[key]:,.1f}"
        values[f"wm.{label}_trees"] = str(row["whole_tree_equivalents"])
    values["wm.assumptions"] = assumptions()
    values["wm.pair_table"] = "\n".join([
        "| Assumed overlap | Continuous pair pitch in | Infill wedge ft | Infill trunk ft | Frame plus infill trunk ft | Whole tree equivalents |",
        "| --- | --- | --- | --- | --- | --- |",
        *(f"| {100*r['overlap']:.0f}% | {r['pair_pitch_in']:.2f} | {r['infill_ft']:,.1f} | {r['infill_trunk_ft']:,.1f} | {r['raw_trunk_ft']:,.1f} | {r['whole_tree_equivalents']} |" for r in f["rows"])])
    values["wm.section_table"] = "\n".join([
        "| Opposed-point engagement | Envelope depth in | Slant contact in | Assumed cell void |",
        "| --- | --- | --- | --- |",
        *(f"| {100*r['engagement']:.0f}% | {r['span_in']:.2f} | {r['contact_in']:.2f} | {100*r['void_fraction']:.1f}% |" for r in f["pair_sections"])])
    values["wm.section_height_in"] = f"{f['pair_sections'][0]['height_in']:.3f}"
    for key in ("phi", "side_in", "diagonal_in", "long_in", "short_in", "interior_ft", "all_ft", "interior_deg", "turn_deg", "miter_deg", "butt_deg", "diagonal_deg", "diagonal_butt_deg"):
        values["wm.pent_" + key] = f"{g[key]:,.3f}" if key == "phi" else f"{g[key]:,.2f}"
    values["wm.pent_logs"] = str(g["ideal_stock_logs"])
    values["wm.pent_spare"] = str(g["spare_short_count"])
    return values


def report() -> str:
    t = token_values()
    f = reference()
    return (assumptions() + "\n\nNOMINAL CHORD CASE (not finished cut lengths)\n"
            f"chords {f['long_in']:.2f} / {f['short_in']:.2f} in; {f['members']} panel-owned members\n"
            f"nominal edges {f['nominal_frame_ft']:.2f} ft; solver cut-stock {f['finished_frame_ft']:.2f} ft\n"
            f"gross frame blanks {f['gross_frame_ft']:.2f} ft; raw trunk reserve {f['frame_trunk_ft']:.2f} ft\n"
            f"gross area {f['area_sqft']:.2f} sq ft; assumed opening {f['opening_sqft']:.2f} sq ft\n\n"
            + t["wm.pair_table"] + "\n\nSEPARATE OPPOSED-POINT CHORD-TRIANGLE EXPERIMENT\n"
            + t["wm.section_table"]
            + "\n\nBounds require continuous projected coverage: neither bowtie span nor point contact proves it.\n")


def validate_methodology() -> None:
    from .base import pentagon as polygon
    p = pentagon()
    assert math.isclose(p["phi"], (1 + math.sqrt(5)) / 2, rel_tol=1e-12)
    assert math.isclose(p["long_in"] + p["short_in"], p["side_in"], abs_tol=1e-9)
    assert math.isclose(2*p["long_in"] + p["short_in"], p["diagonal_in"], abs_tol=1e-9)
    pts = polygon(p["side_in"])
    diagonal = (pts[0], pts[2])
    crossings = []
    from .base import _seg_cross
    for a, b in ((pts[1], pts[3]), (pts[1], pts[4])):
        hit = _seg_cross(*diagonal, a, b)
        assert hit is not None
        crossings.append(float(np.linalg.norm(hit-diagonal[0])))
    segments = np.diff([0.0, *sorted(crossings), p["diagonal_in"]])
    assert np.allclose(segments, [p["long_in"], p["short_in"], p["long_in"]])
    assert math.isclose(p["butt_deg"], 18) and math.isclose(p["diagonal_butt_deg"], 54)
    f = reference()
    assert f["members"] == 3*f["panel_count"] and f["shared_edges"] < f["members"]
    assert 0 < f["opening_sqft"] < f["area_sqft"]
    assert f["finished_frame_ft"] < f["nominal_frame_ft"] < f["gross_frame_ft"]
    rows = f["rows"]
    assert all(a["infill_ft"] < b["infill_ft"] for a,b in zip(rows,rows[1:]))
    assert math.isclose(rows[-1]["infill_ft"], 2*rows[0]["infill_ft"])
    assert math.isclose(rows[0]["raw_trunk_ft"]-rows[0]["infill_trunk_ft"], f["frame_trunk_ft"])
    assert rows[0]["raw_trunk_ft"] > rows[0]["nominal_total_ft"]/f["splits"]
    for row in rows:
        count = row["whole_tree_equivalents"]
        assert (count-1)*f["trunk_ft"] < row["raw_trunk_ft"] <= count*f["trunk_ft"]
    cells = f["pair_sections"]
    assert all(math.isclose(c["wood_area_in2"], cells[0]["wood_area_in2"]) for c in cells)
    assert cells[0]["void_fraction"] == .5 and cells[-1]["void_fraction"] == 0
    assert cells[0]["span_in"] > cells[-1]["span_in"]
    assert not math.isclose(cells[0]["span_in"], rows[0]["pair_pitch_in"])
    for bad in (-1, 1.1, float("nan")):
        try:
            pair_section(12, 8, bad)
        except ValueError:
            pass
        else:
            raise AssertionError("invalid overlap accepted")
    try:
        coverage_length(10, 0)
    except ValueError:
        pass
    else:
        raise AssertionError("zero pitch accepted")
    live_case = live()
    assert live_case["long_in"] > f["long_in"]
    assert 0 < live_case["solved_opening_sqft"] < live_case["area_sqft"]


if __name__ == "__main__":
    validate_methodology()
    print(report())
