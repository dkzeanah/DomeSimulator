"""Book plates from existing model geometry, rendered with NumPy and Pillow.

No OpenGL window or added dependency is required. New renders use new directories.
"""
from __future__ import annotations

import math
from pathlib import Path
import textwrap
import uuid

import numpy as np
from PIL import Image, ImageDraw, ImageFont

from .storage import stamp

PAPER = (248, 246, 236)
INK = (34, 67, 53)


def font(size, serif=False):
    name = "georgia.ttf" if serif else "segoeui.ttf"
    path = Path("C:/Windows/Fonts") / name
    return ImageFont.truetype(str(path), size) if path.exists() else ImageFont.load_default()


def canvas(title, subtitle, width=1800, height=1400):
    im = Image.new("RGB", (width, height), PAPER)
    draw = ImageDraw.Draw(im)
    draw.text((90, 55), "2 TREES   /   PROJECT PLATES", fill=(115, 131, 114), font=font(22))
    draw.text((90, 104), title, fill=INK, font=font(49, True))
    for i, line in enumerate(textwrap.wrap(subtitle, 115)):
        draw.text((90, 179 + 33*i), line, fill=INK, font=font(25))
    draw.line((90, height - 105, width - 90, height - 105), fill=(195, 198, 176), width=2)
    draw.text((90, height - 78), "DomeSim geometry · illustrative model plate · dimensions and connection design remain separate", fill=(110, 120, 103), font=font(20))
    return im


def projection(points, azimuth=-55, elevation=25):
    az, el = math.radians(azimuth), math.radians(elevation)
    right = np.array([-math.sin(az), math.cos(az), 0.0])
    toward = np.array([math.cos(el)*math.cos(az), math.cos(el)*math.sin(az), math.sin(el)])
    up = np.cross(toward, right)
    return np.asarray(points) @ np.stack([right, -up, toward], axis=1)


def draw_mesh(im, meshes, box=(90, 290, 1710, 1260), azimuth=-55, elevation=25):
    triangles, colors = [], []
    for mesh in meshes:
        if not hasattr(mesh, "indices") or not len(mesh.indices):
            continue
        vertices = np.asarray(mesh.vertices, dtype=float)
        indices = np.asarray(mesh.indices, dtype=int).reshape(-1, 3)
        triangles.extend(vertices[indices, :3])
        colors.extend(vertices[indices, 6:9].mean(axis=1))
    triangles = np.asarray(triangles)
    if triangles.size == 0:
        raise ValueError("Simulator returned no triangles.")
    colors = np.asarray(colors)
    projected = projection(triangles.reshape(-1, 3), azimuth, elevation).reshape(-1, 3, 3)
    low = projected[:, :, :2].min(axis=(0, 1))
    high = projected[:, :, :2].max(axis=(0, 1))
    scale = min((box[2]-box[0]) / max(high[0]-low[0], 0.01), (box[3]-box[1]) / max(high[1]-low[1], 0.01)) * .92
    offset = np.array([(box[0]+box[2])/2, (box[1]+box[3])/2]) - (low+high)/2 * scale
    xy = projected[:, :, :2] * scale + offset
    normals = np.cross(triangles[:, 1] - triangles[:, 0], triangles[:, 2] - triangles[:, 0])
    normals /= np.maximum(np.linalg.norm(normals, axis=1)[:, None], 1e-9)
    light = np.array([-.4, -.6, .85]); light /= np.linalg.norm(light)
    shading = .60 + .40 * np.abs(normals @ light)
    draw = ImageDraw.Draw(im)
    for i in np.argsort(projected[:, :, 2].mean(axis=1)):
        color = tuple(int(v) for v in np.clip(colors[i] * shading[i] * 255, 0, 255))
        draw.polygon([tuple(p) for p in xy[i]], fill=color)


def draw_wire(im, vertices, faces, box=(100, 290, 1700, 1240), azimuth=-55, elevation=25):
    projected = projection(vertices, azimuth, elevation)
    used = sorted(set(v for face in faces for v in face))
    low, high = projected[used, :2].min(axis=0), projected[used, :2].max(axis=0)
    scale = min((box[2]-box[0]) / max(high[0]-low[0], .01), (box[3]-box[1]) / max(high[1]-low[1], .01)) * .9
    offset = np.array([(box[0]+box[2])/2, (box[1]+box[3])/2]) - (low+high)/2*scale
    xy = projected[:, :2] * scale + offset
    draw = ImageDraw.Draw(im)
    order = sorted(range(len(faces)), key=lambda i: np.mean(projected[list(faces[i]), 2]))
    for i in order:
        polygon = [tuple(xy[v]) for v in faces[i]]
        fill = (220, 230, 209) if i % 2 else (232, 227, 208)
        draw.polygon(polygon, fill=fill)
        draw.line(polygon + polygon[:1], fill=INK, width=5, joint="curve")


def render_all(folder):
    from two_v_demo.raw_wedge_bridge import simulator
    from two_v_demo.geometry import build_demo_geometry
    from two_v_demo.hex_geometry import truncated_icosahedron
    from two_v_demo.zome_geometry import polar_zonohedron
    sim = simulator()
    output = Path(folder) / (stamp() + "-" + uuid.uuid4().hex[:6])
    output.mkdir(parents=True, exist_ok=False)
    results = []
    def save(im, name, caption, source):
        target = output / (name + ".png")
        im.save(target, dpi=(240, 240))
        results.append((target, caption, source))
    for orientation in sim.WEDGE_ORIENTATION_ORDER:
        config = sim.DomeConfig(wedge_orientation=orientation, jig_enabled=False)
        model = sim.build_physical_model(config)
        mesh = sim.build_world_meshes(model)
        # Render the same meshes with a print palette instead of the simulator's
        # bright red/green diagnostic radial-face colors.
        mesh["wood"].vertices[:, 6:10] = (0.69, 0.47, 0.26, 1)
        mesh["rigid"].vertices[:, 6:10] = (0.38, 0.48, 0.37, 1)
        im = canvas(orientation.replace("_", " ").title(), "Forty independent pinwheel triangle frames; neighboring panels retain two members along each shared edge.")
        draw_mesh(im, [mesh[key] for key in ("wood", "rigid") if key in mesh])
        save(im, orientation, f"Raw-wedge dome: {orientation}; 120 members, 40 panels, 55 interior seams.",
             "Model render: geodesic_raw_wedge_dome_dihedral.py; A=72 in; trunk diameter=8 in; raw_trapezoid; " + orientation)
    model = sim.build_physical_model(sim.DomeConfig(jig_enabled=False))
    # Two true neighboring panels demonstrate the separate members at a seam.
    shared = next(edge for edge in model.topology.edges.values() if not edge.is_base)
    adjacent = [f.index for f in model.topology.faces if all(v in f.vertices for v in shared.key)]
    meshes = []
    palette = [(0.63, 0.35, 0.18, 1), (0.28, 0.49, 0.37, 1), (0.72, 0.57, 0.29, 1)]
    for face_index in adjacent:
        for member in model.members:
            if member.face_index != face_index:
                continue
            accumulator = sim.MeshAccumulator()
            sim.add_raw_sector_member(accumulator, model, member)
            mesh = accumulator.finish()
            mesh.vertices[:, 6:10] = palette[member.local_edge_index]
            meshes.append(mesh)
    normal = sum((model.topology.faces[i].normal for i in adjacent), np.zeros(3))
    normal /= np.linalg.norm(normal)
    azimuth = math.degrees(math.atan2(normal[1], normal[0]))
    elevation = math.degrees(math.asin(normal[2]))
    im = canvas("The pinwheel / two neighboring panels", "Each butt meets the side of the next member. Each triangle owns three members; a shared axis carries two.")
    draw_mesh(im, meshes, azimuth=azimuth, elevation=elevation)
    save(im, "pinwheel-pair", "Two adjacent independent pinwheel triangles: doubled members at the shared seam. Color distinguishes the three members in each panel.", "Actual simulator member meshes, default point_dome_in configuration; camera and display colors only.")
    g = build_demo_geometry()
    im = canvas("The geometric hemisphere", "40 faces · 26 vertices · 65 unique edges. These zero-thickness edges are reference geometry.")
    draw_wire(im, g.vertices, g.hemisphere_faces)
    save(im, "geodesic", "2V reference mesh; a mesh edge is not a stock cut length.", "Model render: two_v_demo/geometry.py")
    cage = truncated_icosahedron()
    im = canvas("Hexagons and pentagons", "A different project geometry, with its own panel and member counts.")
    draw_wire(im, cage.vertices, [cage.faces[i] for i in cage.dome_faces])
    save(im, "hex-dome", "Truncated-icosahedron dome selection from the hex geometry tool.", "Model render: two_v_demo/hex_geometry.py; truncated_icosahedron().dome_faces")
    zome = polar_zonohedron()
    im = canvas("The polar zome", "Rhombic panels generated by the zome tool; this form is not a spherical 2V dome.")
    draw_wire(im, zome.vertices, [zome.faces[i] for i in zome.dome_faces])
    save(im, "zome", "Polar zome from the project's six-generator, 54-degree default model.", "Model render: two_v_demo/zome_geometry.py; polar_zonohedron()")
    im = canvas("Two trees / a counted inventory", "The author's proposed section plan. Acceptance still depends on length, section, defects, and fabrication.")
    d = ImageDraw.Draw(im)
    for tree in range(2):
        x = 110 + tree * 850
        d.text((x, 305), f"TREE {tree + 1}", font=font(36, True), fill=INK)
        for row in range(8):
            y = 380 + row * 76
            d.text((x, y+12), f"S{row+1:02d}", font=font(24), fill=INK)
            for sector in range(8):
                px = x + 90 + sector * 68
                spare = row == 7 and sector >= 4
                d.rounded_rectangle((px, y, px+53, y+52), radius=7, fill=(200, 157, 93) if spare else (62, 104, 79))
                d.text((px+16, y+10), str(sector+1), fill=PAPER, font=font(23))
        d.text((x, 1030), "8 sections × 8 blanks = 64", font=font(31, True), fill=INK)
        d.text((x, 1082), "60 intended + 4 potential spares", font=font(24), fill=INK)
    d.text((110, 1170), "128 gross blanks − 8 rejected or reserved = 120 target members", font=font(33, True), fill=INK)
    save(im, "inventory", "Eight six-foot sections per tree yield 64 potential blanks, with four per tree above the 60-member allocation.", "Computed inventory diagram from the user's proposed plan; colored spare positions are bookkeeping, not a grading rule.")
    return results


if __name__ == "__main__":
    from .storage import DEFAULT_HOME
    for path, caption, _ in render_all(DEFAULT_HOME / "rendered"):
        print(path, caption)
