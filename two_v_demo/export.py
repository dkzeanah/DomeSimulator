"""Fabrication and cross-check exports from the validated 2V model."""

from __future__ import annotations

import csv
import json
import math
from pathlib import Path

from .geometry import DomeMeasurements, build_demo_geometry, fit_measurements


def _write_csv(path: Path, rows: list[list[object]]) -> None:
    with path.open("w", newline="", encoding="utf-8") as handle:
        csv.writer(handle).writerows(rows)


def _field_guide(radius: float, connector_deduction: float) -> str:
    geometry = build_demo_geometry()
    dimensions = DomeMeasurements(radius, connector_deduction)
    return f"""# 2V Hemisphere Field Guide

Generated from the same geometry used by the ModernGL masterclass.

## Design basis

- Dome type: class-I, 2-frequency, true hemisphere
- Radius: {radius:.6f} in ({radius / 12.0:.6f} ft)
- Diameter: {dimensions.diameter:.6f} in ({dimensions.diameter / 12.0:.6f} ft)
- Height above a level base: {dimensions.height:.6f} in
- Base ring: 10 hub centers
- Unique frame members: 65
- Faces: 40
- Connector deduction: {connector_deduction:.6f} in total per member

All theoretical geometry is hub-center to hub-center. The connector deduction
is the **total** shortening across both ends of one member. Confirm it with a
full-scale joint mockup before cutting a production batch.

## Exact member schedule

| Class | Count | Chord factor | Center length | Stock cut length |
|---|---:|---:|---:|---:|
| SHORT | 30 | {geometry.short_factor:.9f} R | {dimensions.short_center_length:.6f} in | {dimensions.short_cut_length:.6f} in |
| LONG | 35 | {geometry.long_factor:.9f} R | {dimensions.long_center_length:.6f} in | {dimensions.long_cut_length:.6f} in |

Calculator letters are not standardized. This packet uses SHORT and LONG.

## Ways to reproduce the calculation

1. **Scale-factor method.** Multiply the chosen radius by `0.546533057825`
   for SHORT and `0.618033988750` for LONG.
2. **Cartesian-coordinate method.** Construct the phi-coordinate icosahedron,
   normalize its vertices, average each edge's endpoints, normalize each
   midpoint, and measure Euclidean endpoint distances.
3. **Dot-product method.** For unit endpoints `u` and `v`, calculate
   `theta = ACOS(DOT(u,v))`.
4. **Chord method.** Convert that central angle with
   `chord = 2 * radius * SIN(theta / 2)`.
5. **Law-of-cosines method.** With two radii and included angle theta,
   `chord^2 = R^2 + R^2 - 2 R^2 COS(theta)`.
6. **Measurement-fit method.** Divide each measured member by its factor, or
   minimize both residuals with
   `R = SUM(factor * measured) / SUM(factor^2)`.
7. **Spreadsheet method.** Put radius in `B1`; SHORT is
   `=B1*0.546533057825`; LONG is `=B1*0.618033988750`. Keep connector
   deduction in its own cell and subtract it only in the stock-cut column.
8. **CAD method.** Import `2v_geometry.obj` with document units set to inches,
   or import `2v_hub_coordinates.csv` and connect the edge pairs in
   `2v_edges.csv`.
9. **Compass/string check.** Lay out each panel family at full scale using
   two radii and intersection arcs. Diagonal equality is a fast shop-floor
   check, not a replacement for calibrated member gauges.

## Panel families

- 30 SHORT-SHORT-LONG triangles
- 10 LONG-LONG-LONG equilateral triangles

Use `2v_panels.csv` for side lengths, planar areas, and included angles. Panel
skin dimensions need real joint gaps, frame width, sheathing overlap, and
weather detailing; the chord triangle is only the structural centerline.

## Fabrication sequence

1. Choose a hub/joint system and make one full-size mockup.
2. Measure its total centerline-to-stock deduction; regenerate this packet.
3. Make hard SHORT and LONG gauges. Cut one of each and verify.
4. Batch-cut and permanently mark 30 SHORT and 35 LONG members.
5. Dry-fit one SHORT-SHORT-LONG and one LONG-LONG-LONG triangle.
6. Lay out and level the ten base hub centers from the coordinate file.
7. Assemble upward by altitude ring, checking level and opposing diagonals.
8. Correct accumulated error before closing the apex.
9. Recheck radius, diameter, height, fasteners, and foundation anchorage.
10. Add panels/weather layers only from a joint-specific envelope design.

PVC, timber, tube, and hubless frames share the centerline geometry but do not
share end cuts, bolt offsets, drilling patterns, or structural capacity.

## Verification targets

- Floor area: {dimensions.floor_area:.3f} in^2
- Spherical skin area: {dimensions.spherical_skin_area:.3f} in^2
- Planar chord-panel area: {dimensions.planar_panel_area:.3f} in^2
- Hemisphere volume: {dimensions.enclosed_volume:.3f} in^3
- Expected height: {dimensions.height:.6f} in

For an occupied, public, snow-loaded, or wind-loaded structure, have the
members, hubs, fasteners, openings, foundation, and local code compliance
reviewed by a qualified engineer. This packet defines geometry, not capacity.
"""


def export_build_packet(
    directory: Path,
    radius: float | None = None,
    connector_deduction: float = 0.0,
) -> tuple[Path, ...]:
    """Export spreadsheet-, CAD-, and shop-friendly files.

    ``radius`` and ``connector_deduction`` are inches. If radius is omitted,
    the least-squares fit of the supplied 72 in / 63.5 in members is used.
    """
    geometry = build_demo_geometry()
    if radius is None:
        radius = fit_measurements(72.0, 63.5).best_fit_radius
    if radius <= 0:
        raise ValueError("radius must be positive")
    dimensions = DomeMeasurements(radius, connector_deduction)
    if dimensions.short_cut_length <= 0:
        raise ValueError("connector deduction must be shorter than a SHORT member")
    directory.mkdir(parents=True, exist_ok=True)

    cut_path = directory / "2v_cut_list.csv"
    _write_csv(cut_path, [
        ["class", "count", "factor_R", "center_length_in",
         "total_connector_deduction_in", "stock_cut_length_in"],
        ["SHORT", 30, f"{geometry.short_factor:.12f}",
         f"{dimensions.short_center_length:.6f}", f"{connector_deduction:.6f}",
         f"{dimensions.short_cut_length:.6f}"],
        ["LONG", 35, f"{geometry.long_factor:.12f}",
         f"{dimensions.long_center_length:.6f}", f"{connector_deduction:.6f}",
         f"{dimensions.long_cut_length:.6f}"],
    ])

    panel_path = directory / "2v_panels.csv"
    panel_rows: list[list[object]] = [[
        "family", "count", "side_1_in", "side_2_in", "side_3_in",
        "angle_opposite_side_1_deg", "angle_opposite_side_2_deg",
        "angle_opposite_side_3_deg", "planar_area_sq_in",
    ]]
    length_by_name = {
        "SHORT": dimensions.short_center_length,
        "LONG": dimensions.long_center_length,
    }
    for triangle in geometry.triangle_classes:
        side_lengths = [length_by_name[name] for name in triangle.side_names]
        panel_rows.append([
            triangle.name,
            triangle.hemisphere_count,
            *(f"{value:.6f}" for value in side_lengths),
            *(f"{value:.6f}" for value in triangle.angles_deg),
            f"{triangle.planar_area_factor * radius**2:.6f}",
        ])
    _write_csv(panel_path, panel_rows)

    used_indices = sorted(
        {int(index) for face in geometry.hemisphere_faces for index in face}
    )
    remap = {old: new + 1 for new, old in enumerate(used_indices)}
    hub_path = directory / "2v_hub_coordinates.csv"
    hub_rows: list[list[object]] = [["hub_id", "x_in", "y_in", "z_in", "ring"]]
    z_values = sorted({
        round(float(geometry.vertices[index, 2]), 8) for index in used_indices
    })
    z_ring = {value: ring for ring, value in enumerate(z_values)}
    for old_index in used_indices:
        x, y, z = geometry.vertices[old_index] * radius
        hub_rows.append([
            remap[old_index], f"{x:.6f}", f"{y:.6f}", f"{z:.6f}",
            z_ring[round(float(geometry.vertices[old_index, 2]), 8)],
        ])
    _write_csv(hub_path, hub_rows)

    edge_path = directory / "2v_edges.csv"
    edge_rows: list[list[object]] = [[
        "edge_id", "hub_1", "hub_2", "class", "center_length_in"
    ]]
    for edge_id, edge in enumerate(geometry.hemisphere_edges, 1):
        class_name = geometry.edge_class_by_edge[geometry.edges.index(edge)]
        length = length_by_name[class_name]
        edge_rows.append([
            edge_id, remap[edge[0]], remap[edge[1]], class_name, f"{length:.6f}"
        ])
    _write_csv(edge_path, edge_rows)

    workbook_path = directory / "2v_calculation_workbook.csv"
    fit = fit_measurements(72.0, 63.5)
    _write_csv(workbook_path, [
        ["quantity", "equation_or_method", "value", "unit"],
        ["golden ratio", "(1+SQRT(5))/2", f"{(1 + math.sqrt(5)) / 2:.12f}", ""],
        ["SHORT factor", "coordinate/dot/chord cross-check",
         f"{geometry.short_factor:.12f}", "R"],
        ["LONG factor", "1/phi", f"{geometry.long_factor:.12f}", "R"],
        ["theoretical ratio", "LONG/SHORT", f"{geometry.ratio:.12f}", ""],
        ["chosen radius", "input or least-squares measurement fit",
         f"{radius:.6f}", "in"],
        ["radius from measured LONG", "72/LONG_factor",
         f"{fit.radius_from_long:.6f}", "in"],
        ["radius from measured SHORT", "63.5/SHORT_factor",
         f"{fit.radius_from_short:.6f}", "in"],
        ["least-squares radius", "SUM(factor*length)/SUM(factor^2)",
         f"{fit.best_fit_radius:.6f}", "in"],
        ["diameter", "2*R", f"{dimensions.diameter:.6f}", "in"],
        ["height", "R", f"{dimensions.height:.6f}", "in"],
        ["floor area", "PI()*R^2", f"{dimensions.floor_area:.6f}", "sq in"],
        ["spherical skin area", "2*PI()*R^2",
         f"{dimensions.spherical_skin_area:.6f}", "sq in"],
        ["hemisphere volume", "2/3*PI()*R^3",
         f"{dimensions.enclosed_volume:.6f}", "cu in"],
    ])

    obj_path = directory / "2v_geometry.obj"
    obj_lines = [
        "# 2V geodesic hemisphere",
        "# Coordinate unit: inch (set the importing CAD document to inches)",
        f"# radius: {radius:.6f} in",
    ]
    for old_index in used_indices:
        x, y, z = geometry.vertices[old_index] * radius
        obj_lines.append(f"v {x:.9f} {y:.9f} {z:.9f}")
    obj_lines.append("g panels")
    for face in geometry.hemisphere_faces:
        obj_lines.append("f " + " ".join(str(remap[int(index)]) for index in face))
    obj_lines.append("g frame_edges")
    for edge in geometry.hemisphere_edges:
        obj_lines.append(f"l {remap[edge[0]]} {remap[edge[1]]}")
    obj_path.write_text("\n".join(obj_lines) + "\n", encoding="utf-8")

    manifest_path = directory / "2v_build_packet.json"
    manifest = {
        "type": "class-I 2V geodesic hemisphere",
        "units": "inches",
        "radius": radius,
        "diameter": dimensions.diameter,
        "height": dimensions.height,
        "connector_deduction_total_per_member": connector_deduction,
        "counts": {
            "hubs": len(used_indices),
            "base_hubs": len(geometry.base_ring),
            "struts": len(geometry.hemisphere_edges),
            "short_struts": 30,
            "long_struts": 35,
            "panels": len(geometry.hemisphere_faces),
        },
        "factors": {
            "short": geometry.short_factor,
            "long": geometry.long_factor,
            "long_over_short": geometry.ratio,
        },
        "files": [
            cut_path.name, panel_path.name, hub_path.name, edge_path.name,
            workbook_path.name, obj_path.name, "2v_field_guide.md",
        ],
    }
    manifest_path.write_text(json.dumps(manifest, indent=2) + "\n", encoding="utf-8")

    guide_path = directory / "2v_field_guide.md"
    guide_path.write_text(_field_guide(radius, connector_deduction), encoding="utf-8")
    return (
        cut_path, panel_path, hub_path, edge_path,
        workbook_path, obj_path, manifest_path, guide_path,
    )

