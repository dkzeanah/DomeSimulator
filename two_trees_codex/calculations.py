"""Book-specific inventory arithmetic; physical geometry stays in the simulator."""
from __future__ import annotations

from collections import Counter
from functools import lru_cache
import math


def number(value, label, minimum=0, positive=False):
    value = float(value)
    if not math.isfinite(value) or value < minimum or (positive and value == 0):
        raise ValueError(f"{label} must be finite and {'greater than' if positive else 'at least'} {minimum}.")
    return value


@lru_cache(maxsize=1)
def geometry():
    from two_v_demo.geometry import build_demo_geometry
    return build_demo_geometry()


def radius_first(radius_ft):
    radius = number(radius_ft, "Radius", positive=True)
    g = geometry()
    return dict(radius_ft=radius, diameter_ft=2 * radius,
                circle_area_sqft=math.pi * radius**2,
                base_polygon_area_sqft=5 * radius**2 * math.sin(math.pi / 5),
                long_edge_in=12 * radius * g.long_factor,
                short_edge_in=12 * radius * g.short_factor,
                long_factor=g.long_factor, short_factor=g.short_factor)


def tree_first(section_ft=6, sections=8, trees=2, rejected_per_tree=4,
               trim_total_in=0, bucking_kerf_in=0.25):
    length = number(section_ft, "Section length", positive=True)
    counts = []
    for value, name, positive in [(sections, "Sections per tree", True),
                                  (trees, "Trees", True),
                                  (rejected_per_tree, "Rejected blanks per tree", False)]:
        value = number(value, name, positive=positive)
        if not value.is_integer():
            raise ValueError(f"{name} must be a whole number.")
        counts.append(int(value))
    sections, trees, rejected = counts
    if rejected > sections * 8:
        raise ValueError("Rejected blanks cannot exceed the blanks available per tree.")
    trim = number(trim_total_in, "Total end trim")
    kerf = number(bucking_kerf_in, "Bucking kerf")
    usable = length * 12 - trim
    if usable <= 0:
        raise ValueError("End trim consumes the entire section.")
    result = radius_first(usable / geometry().long_factor / 12)
    gross = sections * 8 * trees
    accepted = (sections * 8 - rejected) * trees
    result.update(gross_blanks=gross, accepted_blanks=accepted,
                  surplus=accepted - 120, gross_spares=gross - 120,
                  usable_stock_in=usable, sections_per_tree=sections, trees=trees,
                  rejected_per_tree=rejected, section_ft=length,
                  net_section_total_ft=sections * length,
                  minimum_trunk_ft=sections * length + (sections - 1) * kerf / 12,
                  note="Nominal-only estimate: validate actual joint stock lengths separately.")
    return result


def physical_schedule(radius_ft, trunk_diameter_in=8, orientation="point_dome_in",
                      extra_stock_in=0):
    from two_v_demo.raw_wedge_bridge import simulator
    sim = simulator()
    radius = radius_first(radius_ft)
    diameter = number(trunk_diameter_in, "Trunk diameter", positive=True)
    extra = number(extra_stock_in, "Additional fabrication stock")
    cfg = sim.DomeConfig(long_edge_in=radius["long_edge_in"],
                         trunk_diameter_in=diameter, wedge_orientation=orientation,
                         jig_enabled=False)
    model = sim.build_physical_model(cfg)
    rows = [dict(member_id=m.member_id, panel=m.face_index,
                 edge_type=m.edge_type, nominal_in=m.nominal_length_in,
                 finished_stock_in=m.physical_stock_length_in,
                 blank_required_in=m.physical_stock_length_in + extra)
            for m in model.members]
    return dict(**radius, members=len(rows), panels=len(model.topology.faces),
                unique_edges=len(model.topology.edges), seams=len(model.seams),
                edge_counts=dict(Counter(m.edge_type for m in model.members)),
                max_finished_stock_in=max(r["finished_stock_in"] for r in rows),
                max_blank_required_in=max(r["blank_required_in"] for r in rows),
                trunk_diameter_in=diameter, orientation=orientation,
                extra_stock_in=extra, schedule=rows)


def fit_physical_stock(usable_stock_in, trunk_diameter_in=8,
                       orientation="point_dome_in", extra_stock_in=0):
    """Invert the actual solver, checking every member, for a fixed cross-section.

    The simulator's member extents are affine in nominal radius for fixed joint
    settings. Derive each line from two solves; a third solve verifies the bound.
    Refuse the result if that assumption ever stops holding in a future solver.
    """
    stock = number(usable_stock_in, "Usable stock", positive=True)
    a = physical_schedule(10, trunk_diameter_in, orientation, extra_stock_in)
    b = physical_schedule(20, trunk_diameter_in, orientation, extra_stock_in)
    limits = []
    for x, y in zip(a["schedule"], b["schedule"]):
        if x["member_id"] != y["member_id"]:
            raise ValueError("The simulator changed member ordering; inverse solve needs review.")
        slope = (y["blank_required_in"] - x["blank_required_in"]) / 10
        if slope <= 0:
            raise ValueError("Non-increasing stock requirement; inverse solve needs review.")
        limits.append(10 + (stock - x["blank_required_in"]) / slope)
    radius = min(limits)
    if radius <= 0:
        raise ValueError("Stock is too short for the selected joint and allowances.")
    result = physical_schedule(radius, trunk_diameter_in, orientation, extra_stock_in)
    if abs(result["max_blank_required_in"] - stock) > 0.001:
        raise ValueError("Physical inverse did not close within 0.001 in; do not use this result.")
    return result


def report(result):
    lines = []
    for key, value in result.items():
        if key == "schedule":
            continue
        lines.append(f"{key.replace('_', ' ')}: {value:.5f}" if isinstance(value, float)
                     else f"{key.replace('_', ' ')}: {value}")
    lines.append("\nGeometry and stock planning only. Connection/load design is a separate task.")
    return "\n".join(lines)
