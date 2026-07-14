"""
Mesh assembly for the dome creator.

Vertex layout (11 floats): position(3) normal(3) rgba(4) mat_id(1).
Opaque and transparent triangles are kept in separate index lists so the
renderer can draw glass / sheeting in a blended second pass.
"""

from __future__ import annotations

import math
from dataclasses import dataclass, field

import numpy as np

from dome_model import DomeModel, normalize
import materials
from materials import (
    MAT_GRASS,
    MAT_PLAIN,
)
import workshop

VERTEX_FLOATS = 11


@dataclass
class Mesh:
    vertices: np.ndarray          # (N, 11) float32
    opaque: np.ndarray            # uint32 index array
    transparent: np.ndarray      # uint32 index array


class MeshBuilder:
    def __init__(self) -> None:
        self.vertices: list[list[float]] = []
        self.opaque: list[int] = []
        self.transparent: list[int] = []

    # -- low level -------------------------------------------------------

    def _indices(self, alpha: float) -> list[int]:
        return self.transparent if alpha < 0.999 else self.opaque

    def add_vertex(
        self,
        p,
        n,
        color: tuple[float, float, float],
        alpha: float,
        mat_id: int,
    ) -> int:
        self.vertices.append([
            float(p[0]), float(p[1]), float(p[2]),
            float(n[0]), float(n[1]), float(n[2]),
            color[0], color[1], color[2], alpha,
            float(mat_id),
        ])
        return len(self.vertices) - 1

    def triangle(self, p0, p1, p2, color, alpha=1.0, mat_id=MAT_PLAIN,
                 normal=None) -> None:
        p0 = np.asarray(p0, dtype=np.float64)
        p1 = np.asarray(p1, dtype=np.float64)
        p2 = np.asarray(p2, dtype=np.float64)
        if normal is None:
            normal = normalize(np.cross(p1 - p0, p2 - p0))
        base = self.add_vertex(p0, normal, color, alpha, mat_id)
        self.add_vertex(p1, normal, color, alpha, mat_id)
        self.add_vertex(p2, normal, color, alpha, mat_id)
        self._indices(alpha).extend([base, base + 1, base + 2])

    def quad(self, p0, p1, p2, p3, normal, color, alpha=1.0,
             mat_id=MAT_PLAIN) -> None:
        base = self.add_vertex(p0, normal, color, alpha, mat_id)
        self.add_vertex(p1, normal, color, alpha, mat_id)
        self.add_vertex(p2, normal, color, alpha, mat_id)
        self.add_vertex(p3, normal, color, alpha, mat_id)
        self._indices(alpha).extend([
            base, base + 1, base + 2, base, base + 2, base + 3,
        ])

    # -- primitives ------------------------------------------------------

    def prism(
        self,
        start,
        end,
        profile: list[tuple[float, float]],
        u_axis,
        v_axis,
        color,
        alpha=1.0,
        mat_id=MAT_PLAIN,
        cap_ends=True,
        smooth=False,
    ) -> None:
        """Sweep a 2D CCW profile from start to end.

        u_axis / v_axis are the world-space directions of the profile's
        local x / y axes (both perpendicular to the sweep axis).
        """
        start = np.asarray(start, dtype=np.float64)
        end = np.asarray(end, dtype=np.float64)
        axis = end - start
        length = float(np.linalg.norm(axis))
        if length < 1e-7:
            return
        axis_dir = axis / length
        u_axis = np.asarray(u_axis, dtype=np.float64)
        v_axis = np.asarray(v_axis, dtype=np.float64)

        n = len(profile)
        ring0 = [start + u_axis * u + v_axis * v for u, v in profile]
        ring1 = [end + u_axis * u + v_axis * v for u, v in profile]

        for i in range(n):
            j = (i + 1) % n
            if smooth:
                n0 = normalize(u_axis * profile[i][0] + v_axis * profile[i][1])
                n1 = normalize(u_axis * profile[j][0] + v_axis * profile[j][1])
            else:
                du = profile[j][0] - profile[i][0]
                dv = profile[j][1] - profile[i][1]
                flat = normalize(u_axis * dv - v_axis * du)
                n0 = n1 = flat
            base = self.add_vertex(ring0[i], n0, color, alpha, mat_id)
            self.add_vertex(ring0[j], n1, color, alpha, mat_id)
            self.add_vertex(ring1[j], n1, color, alpha, mat_id)
            self.add_vertex(ring1[i], n0, color, alpha, mat_id)
            self._indices(alpha).extend([
                base, base + 1, base + 2, base, base + 2, base + 3,
            ])

        if not cap_ends:
            return
        for center, ring, cap_normal in (
            (start, ring0, -axis_dir),
            (end, ring1, axis_dir),
        ):
            c = self.add_vertex(center, cap_normal, color, alpha, mat_id)
            first = len(self.vertices)
            for p in ring:
                self.add_vertex(p, cap_normal, color, alpha, mat_id)
            for i in range(n):
                j = (i + 1) % n
                self._indices(alpha).extend([c, first + i, first + j])

    def cylinder(self, start, end, radius, sides, color, alpha=1.0,
                 mat_id=MAT_PLAIN, cap_ends=True) -> None:
        start = np.asarray(start, dtype=np.float64)
        end = np.asarray(end, dtype=np.float64)
        axis_dir = normalize(end - start)
        helper = np.array([0.0, 0.0, 1.0])
        if abs(float(np.dot(axis_dir, helper))) > 0.92:
            helper = np.array([0.0, 1.0, 0.0])
        u_axis = normalize(np.cross(axis_dir, helper))
        v_axis = normalize(np.cross(axis_dir, u_axis))
        profile = [
            (radius * math.cos(2 * math.pi * i / sides),
             radius * math.sin(2 * math.pi * i / sides))
            for i in range(sides)
        ]
        self.prism(start, end, profile, u_axis, v_axis, color, alpha,
                   mat_id, cap_ends, smooth=sides >= 8)

    def disc(self, center, radius, sides, color, alpha=1.0,
             mat_id=MAT_PLAIN, z_normal=1.0) -> None:
        center = np.asarray(center, dtype=np.float64)
        normal = np.array([0.0, 0.0, float(np.sign(z_normal))])
        c = self.add_vertex(center, normal, color, alpha, mat_id)
        first = len(self.vertices)
        for i in range(sides):
            a = 2 * math.pi * i / sides
            p = center + np.array([radius * math.cos(a),
                                   radius * math.sin(a), 0.0])
            self.add_vertex(p, normal, color, alpha, mat_id)
        for i in range(sides):
            j = (i + 1) % sides
            if z_normal >= 0:
                self._indices(alpha).extend([c, first + i, first + j])
            else:
                self._indices(alpha).extend([c, first + j, first + i])

    def cone(self, base, tip, radius, sides, color, alpha=1.0,
             mat_id=MAT_PLAIN) -> None:
        base = np.asarray(base, dtype=np.float64)
        tip = np.asarray(tip, dtype=np.float64)
        axis = normalize(tip - base)
        helper = np.array([0.0, 0.0, 1.0])
        if abs(float(np.dot(axis, helper))) > 0.92:
            helper = np.array([0.0, 1.0, 0.0])
        u = normalize(np.cross(axis, helper))
        v = normalize(np.cross(axis, u))
        ring = [base + u * (radius * math.cos(2 * math.pi * i / sides))
                + v * (radius * math.sin(2 * math.pi * i / sides))
                for i in range(sides)]
        for i in range(sides):
            j = (i + 1) % sides
            self.triangle(ring[i], ring[j], tip, color, alpha, mat_id)

    def sphere(self, center, radius, color, alpha=1.0,
               mat_id=MAT_PLAIN, rings=6, sides=10) -> None:
        center = np.asarray(center, dtype=np.float64)
        for row in range(rings):
            p0 = -math.pi * 0.5 + math.pi * row / rings
            p1 = -math.pi * 0.5 + math.pi * (row + 1) / rings
            for col in range(sides):
                a0 = 2 * math.pi * col / sides
                a1 = 2 * math.pi * (col + 1) / sides
                def point(pitch, azimuth):
                    return center + radius * np.array([
                        math.cos(pitch) * math.cos(azimuth),
                        math.cos(pitch) * math.sin(azimuth),
                        math.sin(pitch),
                    ])
                q0, q1 = point(p0, a0), point(p0, a1)
                q2, q3 = point(p1, a1), point(p1, a0)
                self.triangle(q0, q1, q2, color, alpha, mat_id,
                              normal=normalize((q0 + q1 + q2) / 3 - center))
                self.triangle(q0, q2, q3, color, alpha, mat_id,
                              normal=normalize((q0 + q2 + q3) / 3 - center))

    # -- output ----------------------------------------------------------

    def build(self) -> Mesh:
        vertices = (
            np.asarray(self.vertices, dtype=np.float32)
            if self.vertices else np.zeros((0, VERTEX_FLOATS), np.float32)
        )
        return Mesh(
            vertices=vertices,
            opaque=np.asarray(self.opaque, dtype=np.uint32),
            transparent=np.asarray(self.transparent, dtype=np.uint32),
        )


# ---------------------------------------------------------------------------
# Scene assembly
# ---------------------------------------------------------------------------

def build_environment() -> Mesh:
    """Static build field, reference grid, and wooded perimeter."""
    b = MeshBuilder()

    b.disc((0.0, 0.0, -0.02), 220.0, 64, (0.30, 0.36, 0.26),
           mat_id=MAT_GRASS)

    extent = 60.0
    spacing = 3.0
    count = int(extent / spacing)
    for i in range(-count, count + 1):
        coord = i * spacing
        major = i % 5 == 0
        color = (0.40, 0.45, 0.36) if major else (0.34, 0.39, 0.31)
        radius = 0.035 if major else 0.02
        b.cylinder((-extent, coord, 0.0), (extent, coord, 0.0),
                   radius, 5, color, cap_ends=False)
        b.cylinder((coord, -extent, 0.0), (coord, extent, 0.0),
                   radius, 5, color, cap_ends=False)

    tree_sites = [
        (-34, -26, 1.0), (-25, -34, 0.9), (-15, -39, 1.1),
        (2, -42, 1.0), (18, -38, 0.85), (31, -31, 1.15),
        (40, -17, 0.95), (43, 1, 1.05), (39, 19, 0.9),
        (30, 34, 1.2), (13, 40, 0.95), (-4, 43, 1.1),
        (-20, 39, 0.9), (-34, 31, 1.05), (-42, 17, 1.15),
        (-44, -2, 0.9), (-41, -17, 1.0), (24, -23, 0.72),
        (-27, 20, 0.78), (27, 19, 0.75), (-20, -24, 0.70),
    ]
    for index, (x, y, scale) in enumerate(tree_sites):
        trunk_h = 5.5 * scale + (index % 3) * 0.7
        trunk_r = 0.30 * scale
        b.cylinder((x, y, 0.0), (x, y, trunk_h), trunk_r, 10,
                   (0.34, 0.22, 0.12), mat_id=materials.MAT_WOOD)
        if index % 3 == 0:
            # Broadleaf crowns make mirror panels reflect varied silhouettes.
            for dx, dy, dz, size in ((0, 0, 0.8, 2.5),
                                     (1.3, 0.2, 0.3, 1.8),
                                     (-1.0, 0.7, 0.2, 1.7)):
                b.sphere((x + dx * scale, y + dy * scale,
                          trunk_h + dz * scale), size * scale,
                         (0.18, 0.36 + 0.03 * (index % 2), 0.16),
                         mat_id=MAT_GRASS)
        else:
            for level in range(3):
                z0 = trunk_h - 1.0 + level * 1.25 * scale
                b.cone((x, y, z0), (x, y, z0 + 3.2 * scale),
                       (2.5 - level * 0.45) * scale, 12,
                       (0.12, 0.31 + level * 0.025, 0.15),
                       mat_id=MAT_GRASS)

    return b.build()


def console_placement(model: DomeModel) -> dict:
    """The monitoring system: apex PTZ camera plus a wall-mounted
    monitor hung high on the north wall, above the doorway, angled
    down toward the middle of the floor."""
    cfg = model.config
    r = cfg.radius
    fh = model.foundation.height
    up = np.array([0.0, 0.0, 1.0])
    cz = float(model.sphere_center[2])
    apex_z = cz + r

    ox, oy = float(model.origin[0]), float(model.origin[1])
    zs = min(fh + 2.75, apex_z - 0.7)
    zs = max(zs, fh + 1.55)
    horiz = math.sqrt(max(r * r - (zs - cz) ** 2, 0.09))
    d = max(horiz - 0.34, 0.8)
    screen_center = np.array([ox, oy + d, zs])

    # Angle the screen down toward the center of the floor.
    target = np.array([ox, oy, fh + 1.0])
    n_t = normalize(target - screen_center)
    right = normalize(np.cross(up, n_t))
    up_s = normalize(np.cross(n_t, right))

    hw, hh = 0.60, 0.34                        # generous 16:9 monitor
    front = screen_center + n_t * 0.02
    corners = np.array([
        front - right * hw - up_s * hh,        # bottom-left
        front + right * hw - up_s * hh,        # bottom-right
        front + right * hw + up_s * hh,        # top-right
        front - right * hw + up_s * hh,        # top-left
    ])

    door_h = min(2.05, zs - fh - 0.55)
    door_y = math.sqrt(
        max(r * r - (fh + door_h - cz) ** 2, 0.05)) - 0.18

    return {
        "screen_center": screen_center,
        "screen_corners": corners,
        "right": right,
        "up_s": up_s,
        "normal": n_t,
        "half_w": hw,
        "half_h": hh,
        "ptz_eye": np.array([ox, oy, apex_z - 0.62]),
        "apex_z": apex_z,
        "door_y": door_y,
        "door_h": door_h,
        "origin": (ox, oy),
    }


def build_dome_mesh(model: DomeModel, events: list | None = None,
                    include_console: bool = True) -> Mesh:
    """Full dome assembly, emitted in real construction order (inspired
    by trailer-home manufacturing: site → chassis/foundation → frame →
    sheathing → rough MEP → interior fit-out → commissioning).

    When `events` is given, a checkpoint is appended after each work
    step: {label, hours (real-world estimate), opaque/transparent index
    counts, pos (worker station)}. Rendering only up to a checkpoint's
    counts shows the dome partially built.
    """
    b = MeshBuilder()
    cfg = model.config
    shape = model.shape
    frame_color = model.frame_color_rgb()
    hub_color = tuple(c * 0.45 for c in frame_color)
    tint = model.panel_tint()
    center = model.sphere_center
    radius = cfg.radius
    width = cfg.strut_width
    depth = model.strut_depth
    fh = model.foundation.height
    ox, oy = float(model.origin[0]), float(model.origin[1])
    up_axis = np.array([0.0, 0.0, 1.0])
    east = np.array([1.0, 0.0, 0.0])
    north = np.array([0.0, 1.0, 0.0])

    def mark(label: str, hours: float, pos) -> None:
        if events is not None:
            events.append({
                "label": label,
                "hours": max(hours, 0.02),
                "opaque": len(b.opaque),
                "transparent": len(b.transparent),
                "pos": (float(pos[0]), float(pos[1]), float(pos[2])),
            })

    def floor_pos(p) -> tuple:
        """Worker station: below/near a point, pulled toward center."""
        v = np.array([float(p[0]) - ox, float(p[1]) - oy])
        d = float(np.linalg.norm(v))
        if d > 1e-6:
            v = v / d * max(d - 1.0, 0.5)
        return (ox + v[0], oy + v[1], fh)

    # ---- 1. site prep and foundation (the "chassis") ----
    foundation = model.foundation
    f_area = math.pi * (radius * cfg.foundation_scale) ** 2
    if foundation.name != "Bare Ground":
        f_radius = radius * cfg.foundation_scale
        h = foundation.height
        b.disc((ox, oy, h), f_radius, 48, foundation.top_color,
               mat_id=foundation.mat_id)
        if foundation.name == "Treehouse Platform":
            # A central living trunk, perimeter posts, braces, and access ladder.
            b.cylinder((ox, oy, 0.0), (ox, oy, h + 0.45), 0.72, 14,
                       (0.32, 0.21, 0.12), mat_id=materials.MAT_WOOD)
            for k in range(6):
                a = 2 * math.pi * k / 6
                px = ox + math.cos(a) * f_radius * 0.72
                py = oy + math.sin(a) * f_radius * 0.72
                b.cylinder((px, py, 0.0), (px, py, h), 0.16, 8,
                           (0.40, 0.27, 0.15), mat_id=materials.MAT_WOOD)
                b.cylinder((px, py, h * 0.45), (ox, oy, h - 0.15),
                           0.10, 7, (0.38, 0.25, 0.14),
                           mat_id=materials.MAT_WOOD)
            ladder_y = oy - f_radius * 0.82
            for sx in (-0.28, 0.28):
                b.cylinder((ox + sx, ladder_y, 0.0),
                           (ox + sx, ladder_y, h), 0.055, 7,
                           (0.48, 0.32, 0.18), mat_id=materials.MAT_WOOD)
            for rung in range(max(2, int(h / 0.35))):
                rz = 0.25 + rung * 0.35
                b.cylinder((ox - 0.28, ladder_y, rz),
                           (ox + 0.28, ladder_y, rz), 0.035, 7,
                           (0.52, 0.35, 0.19), mat_id=materials.MAT_WOOD)
        elif h > 0.015:
            b.cylinder((ox, oy, 0.0), (ox, oy, h), f_radius, 48,
                       foundation.side_color, mat_id=MAT_PLAIN,
                       cap_ends=False)
        mark(f"Site prep & {foundation.name.lower()}",
             max(6.0, f_area * 0.12), (ox, oy + radius * 0.5, fh))

    # ---- 2. floor layout markings ----
    workshop.build_sections(b, model)
    mark("Floor layout & section markings", 1.5, (ox, oy, fh))

    # ---- 3. frame: struts from the base ring upward ----
    profile = shape.profile(width, flip=getattr(cfg, "wedge_flip", False))
    smooth = shape.kind == "circle"
    hubless = cfg.frame_style == "Hubless Doubled"
    strut_hours = 0.08 if hubless else 0.12
    if shape.kind == "wedge":
        strut_hours += 0.04           # sizing split logs takes longer
    arc_style = cfg.frame_style in {"Continuous Steel Arcs", "Rebar Lattice"}
    if arc_style:
        meridians = 12 if cfg.frame_style == "Continuous Steel Arcs" else 22
        ring_count = 3 if cfg.frame_style == "Continuous Steel Arcs" else 7
        segments = 18
        base_angle = math.asin(max(-0.99, min(0.99, (fh - center[2]) / radius)))
        rod_radius = max(width * 0.5, 0.012)
        for k in range(meridians):
            az = 2 * math.pi * k / meridians
            points = []
            for step in range(segments + 1):
                theta = base_angle + (math.pi * 0.5 - base_angle) * step / segments
                rr = radius * math.cos(theta)
                points.append(np.array([
                    ox + math.cos(az) * rr,
                    oy + math.sin(az) * rr,
                    center[2] + radius * math.sin(theta),
                ]))
            for p0, p1 in zip(points, points[1:]):
                b.cylinder(p0, p1, rod_radius, shape.sides, frame_color,
                           cap_ends=False)
        for ring in range(1, ring_count + 1):
            theta = base_angle + (math.pi * 0.5 - base_angle) * ring / (ring_count + 1)
            rr = radius * math.cos(theta)
            z = center[2] + radius * math.sin(theta)
            ring_points = [np.array([
                ox + math.cos(2 * math.pi * k / meridians) * rr,
                oy + math.sin(2 * math.pi * k / meridians) * rr, z])
                for k in range(meridians)]
            for k in range(meridians):
                b.cylinder(ring_points[k], ring_points[(k + 1) % meridians],
                           rod_radius, shape.sides, frame_color,
                           cap_ends=False)
        mark(f"Raise {cfg.frame_style.lower()}",
             meridians * 0.35 + ring_count * 1.2, (ox, oy - radius, fh))
        ordered_struts = []
    else:
        ordered_struts = sorted(
            model.struts, key=lambda s: float((s[0][2] + s[1][2]) * 0.5))
    n_struts = len(ordered_struts)
    for i, (p0, p1, _length) in enumerate(ordered_struts):
        mid = (p0 + p1) * 0.5
        radial = normalize(mid - center)
        axis_dir = normalize(p1 - p0)
        u_axis = normalize(np.cross(axis_dir, radial))
        if np.linalg.norm(u_axis) < 1e-6:
            u_axis = np.array([1.0, 0.0, 0.0])
        v_axis = normalize(np.cross(u_axis, axis_dir))
        if float(np.dot(v_axis, radial)) < 0.0:
            v_axis = -v_axis
        b.prism(p0, p1, profile, u_axis, v_axis, frame_color,
                mat_id=MAT_PLAIN, cap_ends=True, smooth=smooth)
        mark(f"Install strut {i + 1}/{n_struts}", strut_hours,
             floor_pos(mid))

    # ---- 4. joins: hubs / bracket plates / hubless edge bolts ----
    bracket_steel = (0.62, 0.65, 0.69)
    hub_list = ([] if arc_style else
                sorted(model.hubs, key=lambda hb: float(hb[0][2])))
    hub_hours = 0.20 if cfg.hub_style == "Metal Brackets" else 0.15
    for hi, (p, directions) in enumerate(hub_list):
        radial = normalize(p - center)
        if cfg.hub_style == "Metal Brackets":
            plate_len = width * 3.4
            plate_w = width * 0.95
            b.cylinder(p + radial * depth * 0.40,
                       p + radial * depth * 0.58,
                       max(width * 0.7, 0.025), 8, bracket_steel,
                       cap_ends=True)
            for direction in directions:
                along = normalize(
                    direction - radial * float(np.dot(direction, radial)))
                side = normalize(np.cross(radial, along))
                start = p + radial * depth * 0.52
                b.prism(start, start + along * plate_len,
                        [(-plate_w * 0.5, -0.006), (plate_w * 0.5, -0.006),
                         (plate_w * 0.5, 0.006), (-plate_w * 0.5, 0.006)],
                        side, radial, bracket_steel, cap_ends=True)
        else:
            b.cylinder(p - radial * depth * 0.52,
                       p + radial * depth * 0.58,
                       max(width * 0.95, 0.03), 8, hub_color,
                       cap_ends=True)
        mark(f"Fasten hub {hi + 1}/{len(hub_list)}", hub_hours,
             floor_pos(p))

    if model.bolt_points:
        bolt_color = (0.20, 0.22, 0.25)
        for p in model.bolt_points:
            radial = normalize(p - center)
            b.cylinder(p - radial * depth * 0.9, p + radial * depth * 0.9,
                       0.013, 6, bolt_color, cap_ends=True)
        mark(f"Through-bolt {len(model.bolt_points)} edge joins",
             len(model.bolt_points) * 0.03, (ox, oy, fh))

    # ---- 5. doorway framing ----
    place = console_placement(model)
    door_y = place["door_y"]
    door_h = place["door_h"]
    wood = (0.42, 0.28, 0.16)
    for sx in (-0.55, 0.55):
        b.prism(np.array([ox + sx, oy + door_y, fh]),
                np.array([ox + sx, oy + door_y, fh + door_h]),
                [(-0.06, -0.05), (0.06, -0.05), (0.06, 0.05), (-0.06, 0.05)],
                east, north, wood, cap_ends=True)
    b.prism(np.array([ox - 0.64, oy + door_y, fh + door_h + 0.06]),
            np.array([ox + 0.64, oy + door_y, fh + door_h + 0.06]),
            [(-0.05, -0.08), (0.05, -0.08), (0.05, 0.08), (-0.05, 0.08)],
            north, up_axis, wood, cap_ends=True)
    mark("Frame the entrance", 2.0, (ox, oy + door_y - 1.0, fh))

    # ---- 6. sheathing: panels bottom-up ----
    recess = depth * min(max(cfg.recess_pct, 0.05), 0.95)
    pull = width * 0.62
    fitted = [p for p in model.panels if p.panel_type.name != "Open"]
    fitted.sort(key=lambda p: float(p.centroid[2]))
    for pi, panel in enumerate(fitted):
        ptype = panel.panel_type
        outward = normalize(panel.centroid - center)
        pts = []
        for v in panel.world_verts:
            to_c = panel.centroid - v
            dist = float(np.linalg.norm(to_c))
            q = v + to_c * (min(pull, dist * 0.45) / max(dist, 1e-9))
            pts.append(q - outward * recess)
        if ptype.colorable:
            color = tuple(
                min(1.0, ptype.color[i] * tint[i]) for i in range(3))
        else:
            color = ptype.color
        if ptype.shape == "triangle":
            b.triangle(pts[0], pts[1], pts[2], color, ptype.alpha,
                       ptype.mat_id, normal=outward)
        else:
            sides = 6 if ptype.shape == "hexagon" else 4
            tangent = normalize(np.cross(
                outward, np.array([0.0, 0.0, 1.0])))
            if float(np.linalg.norm(tangent)) < 1e-5:
                tangent = np.array([1.0, 0.0, 0.0])
            bitangent = normalize(np.cross(outward, tangent))
            visual_area = panel.area * 0.72
            if sides == 6:
                tile_radius = math.sqrt(visual_area / (1.5 * math.sqrt(3.0)))
                phase = math.pi / 6
            else:
                tile_radius = math.sqrt(visual_area / 2.0)
                phase = math.pi / 4
            tile_center = np.mean(pts, axis=0)
            polygon = [tile_center + tangent * (
                math.cos(phase + 2 * math.pi * k / sides) * tile_radius)
                + bitangent * (
                math.sin(phase + 2 * math.pi * k / sides) * tile_radius)
                for k in range(sides)]
            for k in range(sides):
                b.triangle(tile_center, polygon[k], polygon[(k + 1) % sides],
                           color, ptype.alpha, ptype.mat_id, normal=outward)
            seam = (0.16, 0.18, 0.18) if ptype.mat_id == materials.MAT_MIRROR \
                else tuple(max(0.05, c * 0.55) for c in color)
            for k in range(sides):
                b.cylinder(polygon[k] + outward * 0.006,
                           polygon[(k + 1) % sides] + outward * 0.006,
                           max(0.008, width * 0.10), 5, seam,
                           cap_ends=False)

        # Custom panels show their bracket hardware along the edges.
        hours = 0.7 if ptype.is_window else 0.4
        definition = materials.CUSTOM_PANEL_DEFS.get(ptype.name)
        if definition:
            _c, _w, _s, minutes = materials.custom_panel_extras(definition)
            hours += minutes / 60.0
            brackets = sum(
                qty for comp, qty in
                definition.get("components", {}).items()
                if "Bracket" in comp or "Gusset" in comp)
            for k in range(min(int(brackets), 6)):
                e = k % 3
                m0 = np.asarray(pts[e])
                m1 = np.asarray(pts[(e + 1) % 3])
                frac = 0.5 if k < 3 else 0.3
                mp = m0 + (m1 - m0) * frac
                edge_dir = normalize(m1 - m0)
                b.prism(mp - edge_dir * 0.07 + outward * 0.008,
                        mp + edge_dir * 0.07 + outward * 0.008,
                        [(-0.025, -0.008), (0.025, -0.008),
                         (0.0, 0.018)],
                        normalize(np.cross(outward, edge_dir)), outward,
                        (0.55, 0.58, 0.62), cap_ends=True)
        mark(f"Fit {ptype.name.lower()} {pi + 1}/{len(fitted)}", hours,
             floor_pos(panel.centroid))

    # ---- 7. cladding layers ----
    covered = model.layer_covered_panels()
    covered_area = sum(p.area for p in covered)
    offset = depth * 0.55 + 0.01
    for layer in model.active_layers:
        offset += layer.thickness * 0.5
        for panel in covered:
            pts = []
            for v in panel.world_verts:
                rel = v - center
                dist = float(np.linalg.norm(rel))
                pts.append(center + rel * ((dist + offset) / dist))
            outward = normalize(panel.centroid - center)
            b.triangle(pts[0], pts[1], pts[2], layer.color, layer.alpha,
                       layer.mat_id, normal=outward)
        offset += layer.thickness * 0.5 + 0.008
        mark(f"Apply {layer.name.lower()} layer",
             max(1.0, covered_area * 0.05), (ox, oy - radius - 1.0, 0.0))

    # ---- 8. rough electrical: conduit runs to outlets ----
    wire_runs = workshop.wiring_runs(model)
    for run in wire_runs:
        sx, sy = run["from"]
        tx, ty = run["to"]
        start = np.array([ox + sx, oy + sy, fh + 0.025])
        end = np.array([ox + tx, oy + ty, fh + 0.025])
        if float(np.linalg.norm(end - start)) > 0.05:
            direction = normalize(end - start)
            perp = normalize(np.cross(up_axis, direction))
            b.prism(start, end,
                    [(-0.016, -0.016), (0.016, -0.016),
                     (0.016, 0.016), (-0.016, 0.016)],
                    perp, up_axis, (0.25, 0.26, 0.29), cap_ends=True)
        mark(f"Wire {run['target'].lower()} "
             f"({run['length']:.0f} m run)",
             0.5 + run["length"] * 0.05,
             (ox + tx, oy + ty - 0.8, fh))

    # ---- 9. rough plumbing: supply + drain to each fixture ----
    pipe_runs = workshop.plumbing_runs(model)
    for run in pipe_runs:
        sx, sy = run["from"]
        tx, ty = run["to"]
        direction = normalize(np.array([tx - sx, ty - sy, 0.0]))
        perp = normalize(np.cross(up_axis, direction))
        for side, color in ((-0.06, (0.75, 0.20, 0.18)),   # hot PEX
                            (0.0, (0.20, 0.35, 0.75)),      # cold PEX
                            (0.06, (0.45, 0.46, 0.48))):    # drain
            start = np.array([ox + sx, oy + sy, fh + 0.015]) + perp * side
            end = np.array([ox + tx, oy + ty, fh + 0.015]) + perp * side
            b.prism(start, end,
                    [(-0.012, -0.012), (0.012, -0.012),
                     (0.012, 0.012), (-0.012, 0.012)],
                    perp, up_axis, color, cap_ends=True)
        mark(f"Plumb {run['fixture'].lower()} "
             f"({run['length']:.0f} m runs)",
             2.0 + run["length"] * 0.1, (ox + tx, oy + ty - 0.8, fh))

    # ---- 10. interior partitions ----
    seg_count_before = len(b.opaque)
    workshop.build_partitions(b, model)
    segs = workshop.partition_segments(model)
    if segs and len(b.opaque) > seg_count_before:
        mark(f"Frame {len(segs)} partition walls", len(segs) * 1.5,
             (ox, oy, fh))

    # ---- 11. equipment & furnishing ----
    prop_hours = {"battery": 1.5, "controller": 2.0, "meter": 0.75,
                  "outlet": 0.5}
    for entry in model.config.props:
        prop = workshop.PROP_TYPE_BY_NAME.get(entry.get("type"))
        if prop is None:
            continue
        workshop.build_prop(b, model, entry)
        hours = prop_hours.get(prop.role, 0.3)
        mark(f"Install {prop.name.lower()}", hours,
             (ox + float(entry["x"]), oy + float(entry["y"]) - 0.9, fh))

    # ---- 12. monitoring system: monitor, computer, PTZ camera ----
    if include_console:
        bezel_color = (0.09, 0.09, 0.10)
        sc = place["screen_center"]
        hw, hh = place["half_w"], place["half_h"]
        n_t, right_s, up_s = (place["normal"], place["right"],
                              place["up_s"])
        b.prism(sc - n_t * 0.36, sc - n_t * 0.02,
                [(-0.05, -0.05), (0.05, -0.05), (0.05, 0.05),
                 (-0.05, 0.05)],
                right_s, up_s, (0.30, 0.31, 0.34), cap_ends=True)
        b.prism(sc - n_t * 0.07, sc + n_t * 0.012,
                [(-hw - 0.05, -hh - 0.05), (hw + 0.05, -hh - 0.05),
                 (hw + 0.05, hh + 0.05), (-hw - 0.05, hh + 0.05)],
                right_s, up_s, bezel_color, cap_ends=True)
        cb = sc - up_s * (hh + 0.17)
        b.prism(cb - n_t * 0.10, cb + n_t * 0.02,
                [(-0.28, -0.09), (0.28, -0.09), (0.28, 0.09),
                 (-0.28, 0.09)],
                right_s, up_s, (0.16, 0.17, 0.19), cap_ends=True)
        b.prism(cb + n_t * 0.02, cb + n_t * 0.028,
                [(0.16, -0.03), (0.22, -0.03), (0.22, 0.03),
                 (0.16, 0.03)],
                right_s, up_s, (0.3, 0.9, 0.4), mat_id=12, cap_ends=True)

        apex = np.array([ox, oy, place["apex_z"]])
        b.cylinder(apex - up_axis * 0.02, apex - up_axis * 0.30, 0.035, 8,
                   (0.30, 0.31, 0.33), cap_ends=True)
        b.cylinder(apex - up_axis * 0.30, apex - up_axis * 0.48, 0.095,
                   10, (0.10, 0.10, 0.11), cap_ends=True)
        b.cylinder(apex - up_axis * 0.48, apex - up_axis * 0.53, 0.045,
                   10, (0.05, 0.08, 0.14), cap_ends=True)
        mark("Install monitoring system", 1.5,
             (ox, oy + door_y - 1.2, fh))

    # ---- 13. commissioning (no geometry, pure labor) ----
    mark("Test, inspect & commission", 2.0, (ox, oy, fh))

    return b.build()


def build_avatar_mesh() -> Mesh:
    """Simple third-person player figure, built at the origin facing +Y."""
    b = MeshBuilder()
    body = (0.22, 0.32, 0.52)
    skin = (0.85, 0.68, 0.52)
    b.cylinder((0, 0, 0.05), (0, 0, 0.95), 0.17, 10, body, cap_ends=True)
    b.cylinder((0, 0, 0.95), (0, 0, 1.49), 0.14, 10,
               (0.28, 0.38, 0.58), cap_ends=True)
    b.cylinder((0, 0, 1.51), (0, 0, 1.83), 0.11, 10, skin, cap_ends=True)
    # Nose marker so the facing direction reads clearly.
    b.cylinder((0, 0.10, 1.67), (0, 0.16, 1.67), 0.025, 6, skin,
               cap_ends=True)
    return b.build()


def build_worker_mesh() -> Mesh:
    """Construction worker: safety vest and hard hat."""
    b = MeshBuilder()
    b.cylinder((0, 0, 0.05), (0, 0, 0.95), 0.17, 10,
               (0.30, 0.30, 0.34), cap_ends=True)          # work pants
    b.cylinder((0, 0, 0.95), (0, 0, 1.49), 0.15, 10,
               (0.95, 0.45, 0.08), cap_ends=True)          # hi-vis vest
    b.cylinder((0, 0, 1.51), (0, 0, 1.76), 0.11, 10,
               (0.85, 0.68, 0.52), cap_ends=True)
    b.cylinder((0, 0, 1.76), (0, 0, 1.86), 0.13, 10,
               (0.95, 0.85, 0.10), cap_ends=True)          # hard hat
    return b.build()


def build_prop_mesh(name: str) -> Mesh:
    """A single prop at the origin (for the placement ghost preview)."""
    b = MeshBuilder()
    prop = workshop.PROP_TYPE_BY_NAME[name]
    prop.build(b, workshop.Transform(0.0, 0.0, 0.0, 0.0))
    return b.build()
