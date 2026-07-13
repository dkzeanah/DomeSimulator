"""
Parametric geodesic dome model.

Builds class-I geodesic domes at any frequency, exposes struts / hubs /
panel slots, tracks per-panel overrides (the interchangeable recessed
panels), and computes a complete live bill of materials: lengths, areas,
weights, and costs for frame, panels, cladding layers, and foundation.
"""

from __future__ import annotations

import json
import math
import string
from dataclasses import dataclass, field
from pathlib import Path

import numpy as np

from materials import (
    FRAME_COLORS,
    FRAME_MATERIALS,
    FOUNDATION_TYPES,
    LAYER_TYPES,
    PANEL_COLORS,
    PANEL_TYPES,
    PANEL_TYPE_BY_NAME,
    STRUT_SHAPES,
    FoundationType,
    FrameMaterial,
    LayerType,
    PanelType,
    StrutShape,
)


def normalize(v: np.ndarray) -> np.ndarray:
    v = np.asarray(v, dtype=np.float64)
    n = float(np.linalg.norm(v))
    if n <= 1e-12:
        return v.copy()
    return v / n


def _icosahedron() -> tuple[np.ndarray, np.ndarray]:
    g = (1.0 + math.sqrt(5.0)) * 0.5
    verts = np.array([
        [-1, g, 0], [1, g, 0], [-1, -g, 0], [1, -g, 0],
        [0, -1, g], [0, 1, g], [0, -1, -g], [0, 1, -g],
        [g, 0, -1], [g, 0, 1], [-g, 0, -1], [-g, 0, 1],
    ], dtype=np.float64)
    verts = np.array([normalize(v) for v in verts])
    faces = np.array([
        [0, 11, 5], [0, 5, 1], [0, 1, 7], [0, 7, 10], [0, 10, 11],
        [1, 5, 9], [5, 11, 4], [11, 10, 2], [10, 7, 6], [7, 1, 8],
        [3, 9, 4], [3, 4, 2], [3, 2, 6], [3, 6, 8], [3, 8, 9],
        [4, 9, 5], [2, 4, 11], [6, 2, 10], [8, 6, 7], [9, 8, 1],
    ], dtype=np.int32)
    return verts, faces


def _rotate_vertex_up(verts: np.ndarray) -> np.ndarray:
    top = verts[np.argmax(verts[:, 2])]
    target = np.array([0.0, 0.0, 1.0])
    axis = np.cross(top, target)
    length = float(np.linalg.norm(axis))
    if length < 1e-9:
        return verts
    axis /= length
    angle = math.acos(float(np.clip(np.dot(top, target), -1.0, 1.0)))
    c, s = math.cos(angle), math.sin(angle)
    rotated = []
    for v in verts:
        rotated.append(
            v * c + np.cross(axis, v) * s + axis * np.dot(axis, v) * (1 - c)
        )
    return np.array(rotated)


@dataclass
class GeodesicData:
    """Unit-radius dome in 'dome frame': sphere center at origin."""
    verts: np.ndarray                      # (N, 3) unit sphere, base flattened
    faces: np.ndarray                      # (M, 3) vertex indices
    edges: list[tuple[int, int]]
    base_z: float                          # z of the flattened base plane
    base_ring: list[int]                   # indices of base-ring vertices


_GEO_CACHE: dict[int, GeodesicData] = {}


def build_geodesic(frequency: int) -> GeodesicData:
    """Subdivide an icosahedron, cut at the vertex ring nearest the equator,
    and flatten that ring onto a single plane (flat-base adaptation)."""
    if frequency in _GEO_CACHE:
        return _GEO_CACHE[frequency]

    base_verts, base_faces = _icosahedron()
    base_verts = _rotate_vertex_up(base_verts)

    lookup: dict[tuple, int] = {}
    verts: list[np.ndarray] = []
    faces: list[tuple[int, int, int]] = []

    def add_vert(p: np.ndarray) -> int:
        p = normalize(p)
        key = tuple(np.round(p, 6))
        idx = lookup.get(key)
        if idx is not None:
            return idx
        idx = len(verts)
        lookup[key] = idx
        verts.append(p)
        return idx

    f = frequency
    for ia, ib, ic in base_faces:
        a, b, c = base_verts[ia], base_verts[ib], base_verts[ic]
        grid: dict[tuple[int, int], int] = {}
        for i in range(f + 1):
            for j in range(f + 1 - i):
                point = a * (f - i - j) + b * i + c * j
                grid[(i, j)] = add_vert(point)
        for i in range(f):
            for j in range(f - i):
                faces.append((grid[(i, j)], grid[(i + 1, j)], grid[(i, j + 1)]))
                if i + j < f - 1:
                    faces.append((
                        grid[(i + 1, j)], grid[(i + 1, j + 1)], grid[(i, j + 1)]
                    ))

    varr = np.array(verts)

    # Cluster vertex z-values into latitude rings, pick the ring nearest the
    # equator (preferring the one just below for odd frequencies), and
    # flatten it into a plane so the dome sits cleanly on the ground.
    order = np.argsort(-varr[:, 2])
    clusters: list[list[int]] = []
    for idx in order:
        z = varr[idx, 2]
        if clusters and abs(varr[clusters[-1][-1], 2] - z) < 0.045:
            clusters[-1].append(int(idx))
        else:
            clusters.append([int(idx)])

    def cluster_rank(cluster: list[int]) -> tuple:
        mean = float(np.mean([varr[i, 2] for i in cluster]))
        return (round(abs(mean), 4), 0 if mean <= 1e-6 else 1)

    candidates = [c for c in clusters if len(c) >= 3]
    base_cluster = min(candidates, key=cluster_rank)
    base_z = float(np.mean([varr[i, 2] for i in base_cluster]))
    for i in base_cluster:
        varr[i, 2] = base_z

    base_set = set(base_cluster)
    kept_faces = [
        face for face in faces
        if all(varr[i, 2] >= base_z - 1e-5 for i in face)
    ]

    used = sorted({i for face in kept_faces for i in face})
    remap = {old: new for new, old in enumerate(used)}
    out_verts = varr[used]
    out_faces = np.array(
        [[remap[a], remap[b], remap[c]] for a, b, c in kept_faces],
        dtype=np.int32,
    )
    edge_set = {
        tuple(sorted((face[i], face[(i + 1) % 3])))
        for face in out_faces for i in range(3)
    }
    ring = [remap[i] for i in base_cluster if i in remap]

    data = GeodesicData(
        verts=out_verts,
        faces=out_faces,
        edges=sorted(edge_set),
        base_z=base_z,
        base_ring=ring,
    )
    _GEO_CACHE[frequency] = data
    return data


# ---------------------------------------------------------------------------
# Configuration
# ---------------------------------------------------------------------------

FRAME_STYLES = ["Hub & Strut", "Hubless Doubled"]
HUB_STYLES = ["Node Puck", "Metal Brackets"]

BOLT_COST = 1.6            # per through-bolt in hubless mode
BOLT_WEIGHT = 0.09
WEDGES_PER_TREE = 4        # split a log in half, then quarters


@dataclass
class DomeConfig:
    frequency: int = 3
    radius: float = 5.0
    strut_shape: int = 3          # index into STRUT_SHAPES (lumber)
    strut_width: float = 0.06     # m
    frame_style: str = "Hub & Strut"
    hub_style: str = "Node Puck"
    wedge_flip: bool = False      # quarter wedge: curve outward instead
    frame_material: int = 2       # index into FRAME_MATERIALS (timber)
    frame_color: int = 0          # index into FRAME_COLORS (material color)
    trunk_stock_length: float = 0.0       # m; 0 = not tracked
    trunk_circumference: float = 0.0      # m; display/BOM note
    default_panel: str = "Plywood"
    panel_color: int = 0          # index into PANEL_COLORS
    recess_pct: float = 0.50      # 0..1 of strut depth
    layers: list[str] = field(default_factory=lambda: ["None", "None", "None"])
    foundation: str = "Concrete Slab"
    foundation_scale: float = 1.15
    panel_overrides: dict[str, str] = field(default_factory=dict)
    sections: list[str] = field(
        default_factory=lambda: ["Unassigned"] * 10)
    partitions: str = "Markings"
    props: list[dict] = field(default_factory=list)
    inventory: list[str] = field(default_factory=list)

    def to_dict(self) -> dict:
        return {
            "frequency": self.frequency,
            "radius": self.radius,
            "strut_shape": STRUT_SHAPES[self.strut_shape].name,
            "strut_width": self.strut_width,
            "frame_material": FRAME_MATERIALS[self.frame_material].name,
            "frame_color": FRAME_COLORS[self.frame_color].name,
            "trunk_stock_length": self.trunk_stock_length,
            "trunk_circumference": self.trunk_circumference,
            "default_panel": self.default_panel,
            "panel_color": PANEL_COLORS[self.panel_color].name,
            "recess_pct": self.recess_pct,
            "layers": list(self.layers),
            "foundation": self.foundation,
            "foundation_scale": self.foundation_scale,
            "panel_overrides": dict(self.panel_overrides),
            "sections": list(self.sections),
            "partitions": self.partitions,
            "props": [dict(p) for p in self.props],
            "inventory": list(self.inventory),
            "frame_style": self.frame_style,
            "hub_style": self.hub_style,
            "wedge_flip": self.wedge_flip,
        }

    @staticmethod
    def from_dict(data: dict) -> "DomeConfig":
        cfg = DomeConfig()
        cfg.frequency = int(data.get("frequency", cfg.frequency))
        cfg.radius = float(data.get("radius", cfg.radius))
        cfg.strut_width = float(data.get("strut_width", cfg.strut_width))
        cfg.trunk_stock_length = float(
            data.get("trunk_stock_length", cfg.trunk_stock_length))
        cfg.trunk_circumference = float(
            data.get("trunk_circumference", cfg.trunk_circumference))
        cfg.recess_pct = float(data.get("recess_pct", cfg.recess_pct))
        cfg.foundation_scale = float(
            data.get("foundation_scale", cfg.foundation_scale)
        )

        def index_of(items, name, fallback):
            for i, item in enumerate(items):
                if item.name == name:
                    return i
            return fallback

        cfg.strut_shape = index_of(
            STRUT_SHAPES, data.get("strut_shape"), cfg.strut_shape)
        cfg.frame_material = index_of(
            FRAME_MATERIALS, data.get("frame_material"), cfg.frame_material)
        cfg.frame_color = index_of(
            FRAME_COLORS, data.get("frame_color"), cfg.frame_color)
        cfg.panel_color = index_of(
            PANEL_COLORS, data.get("panel_color"), cfg.panel_color)

        if data.get("default_panel") in PANEL_TYPE_BY_NAME:
            cfg.default_panel = data["default_panel"]
        layer_names = {l.name for l in LAYER_TYPES}
        cfg.layers = [
            name if name in layer_names else "None"
            for name in (list(data.get("layers", [])) + ["None"] * 3)[:3]
        ]
        foundation_names = {f.name for f in FOUNDATION_TYPES}
        if data.get("foundation") in foundation_names:
            cfg.foundation = data["foundation"]
        cfg.panel_overrides = {
            str(k): v for k, v in dict(data.get("panel_overrides", {})).items()
            if v in PANEL_TYPE_BY_NAME
        }

        import workshop
        room_names = set(workshop.ROOM_TYPE_BY_NAME)
        cfg.sections = [
            name if name in room_names else "Unassigned"
            for name in (list(data.get("sections", []))
                         + ["Unassigned"] * 10)[:10]
        ]
        if data.get("partitions") in workshop.PARTITION_MODES:
            cfg.partitions = data["partitions"]
        cfg.props = [
            {"type": p["type"], "x": float(p.get("x", 0.0)),
             "y": float(p.get("y", 0.0)), "yaw": float(p.get("yaw", 0.0)),
             "on": bool(p.get("on", True))}
            for p in list(data.get("props", []))
            if isinstance(p, dict)
            and p.get("type") in workshop.PROP_TYPE_BY_NAME
        ]
        cfg.inventory = [
            name for name in list(data.get("inventory", []))
            if name in workshop.PROP_TYPE_BY_NAME
        ][:28]
        if data.get("frame_style") in FRAME_STYLES:
            cfg.frame_style = data["frame_style"]
        if data.get("hub_style") in HUB_STYLES:
            cfg.hub_style = data["hub_style"]
        cfg.wedge_flip = bool(data.get("wedge_flip", False))
        return cfg


@dataclass
class PanelSlot:
    key: str
    face: tuple[int, int, int]
    world_verts: np.ndarray          # (3, 3)
    centroid: np.ndarray
    area: float
    panel_type: PanelType


class DomeModel:
    """Config + generated world-space geometry + stats."""

    def __init__(self, config: DomeConfig | None = None,
                 origin: tuple[float, float] = (0.0, 0.0)) -> None:
        self.config = config or DomeConfig()
        self.origin = np.array([origin[0], origin[1], 0.0])
        self.geo: GeodesicData | None = None
        self.world_verts = np.zeros((0, 3))
        self.sphere_center = np.zeros(3)
        self.panels: list[PanelSlot] = []
        self.struts: list[tuple[np.ndarray, np.ndarray, float]] = []
        self.hubs: list[tuple[np.ndarray, list[np.ndarray]]] = []
        self.bolt_points: list[np.ndarray] = []
        self.rebuild()

    # -- convenience accessors ------------------------------------------------

    @property
    def shape(self) -> StrutShape:
        return STRUT_SHAPES[self.config.strut_shape]

    @property
    def material(self) -> FrameMaterial:
        return FRAME_MATERIALS[self.config.frame_material]

    @property
    def foundation(self) -> FoundationType:
        for f in FOUNDATION_TYPES:
            if f.name == self.config.foundation:
                return f
        return FOUNDATION_TYPES[0]

    @property
    def active_layers(self) -> list[LayerType]:
        out = []
        for name in self.config.layers:
            layer = next((l for l in LAYER_TYPES if l.name == name), None)
            if layer and layer.name != "None":
                out.append(layer)
        return out

    @property
    def strut_depth(self) -> float:
        return self.shape.depth(self.config.strut_width)

    @property
    def floor_radius(self) -> float:
        base_z = self.geo.base_z if self.geo else 0.0
        return self.config.radius * math.sqrt(max(0.0, 1.0 - base_z ** 2))

    def section_at(self, x: float, y: float) -> int:
        import workshop
        return workshop.section_of(x - float(self.origin[0]),
                                   y - float(self.origin[1]),
                                   self.floor_radius)

    def light_positions(self) -> list[tuple[float, float, float]]:
        """World positions of powered lamp props (shader point lights)."""
        import workshop
        fh = self.foundation.height
        ox, oy = float(self.origin[0]), float(self.origin[1])
        out = []
        for entry in self.config.props:
            prop = workshop.PROP_TYPE_BY_NAME.get(entry.get("type"))
            if prop is not None and prop.light_z is not None \
                    and entry.get("on", True):
                out.append((ox + float(entry.get("x", 0.0)),
                            oy + float(entry.get("y", 0.0)),
                            fh + prop.light_z))
        return out[:16]

    def frame_color_rgb(self) -> tuple[float, float, float]:
        named = FRAME_COLORS[self.config.frame_color]
        if named.rgb[0] < 0:
            return self.material.color
        return named.rgb

    def panel_tint(self) -> tuple[float, float, float]:
        return PANEL_COLORS[self.config.panel_color].rgb

    # -- geometry -------------------------------------------------------------

    def rebuild(self) -> None:
        cfg = self.config
        self.geo = build_geodesic(cfg.frequency)
        radius = cfg.radius
        base_lift = self.foundation.height
        # World: dome base plane sits on top of the foundation, dome axis at
        # the origin. Sphere center is below/at the base plane.
        self.sphere_center = np.array(
            [float(self.origin[0]), float(self.origin[1]),
             base_lift - self.geo.base_z * radius]
        )
        self.world_verts = self.geo.verts * radius + self.sphere_center

        self.struts = []
        self.hubs = []
        self.bolt_points = []
        if cfg.frame_style == "Hubless Doubled":
            # Every triangle is its own complete 3-strut frame, shrunk
            # toward its centroid so neighbours run side by side along
            # the shared edge, bolted together — no hubs.
            inset = cfg.strut_width * 0.75
            for face in self.geo.faces:
                tri = self.world_verts[list(face)]
                centroid = tri.mean(axis=0)
                pulled = []
                for v in tri:
                    to_c = centroid - v
                    d = float(np.linalg.norm(to_c))
                    pulled.append(v + to_c * (min(inset, d * 0.4) / d))
                for i in range(3):
                    p0, p1 = pulled[i], pulled[(i + 1) % 3]
                    self.struts.append(
                        (p0, p1, float(np.linalg.norm(p1 - p0))))
            for a, b in self.geo.edges:
                pa, pb = self.world_verts[a], self.world_verts[b]
                for frac in (0.33, 0.67):
                    self.bolt_points.append(pa + (pb - pa) * frac)
        else:
            incident: dict[int, list[np.ndarray]] = {}
            for a, b in self.geo.edges:
                pa, pb = self.world_verts[a], self.world_verts[b]
                self.struts.append(
                    (pa, pb, float(np.linalg.norm(pb - pa))))
                incident.setdefault(a, []).append(normalize(pb - pa))
                incident.setdefault(b, []).append(normalize(pa - pb))
            self.hubs = [
                (self.world_verts[i], incident.get(i, []))
                for i in range(len(self.world_verts))
            ]

        self.panels = []
        for face in self.geo.faces:
            tri = self.world_verts[list(face)]
            centroid = tri.mean(axis=0)
            unit_c = normalize(
                self.geo.verts[list(face)].mean(axis=0)
            )
            key = f"{unit_c[0]:.3f},{unit_c[1]:.3f},{unit_c[2]:.3f}"
            area = 0.5 * float(np.linalg.norm(
                np.cross(tri[1] - tri[0], tri[2] - tri[0])
            ))
            type_name = cfg.panel_overrides.get(key, cfg.default_panel)
            panel_type = PANEL_TYPE_BY_NAME.get(
                type_name, PANEL_TYPE_BY_NAME[cfg.default_panel]
            )
            self.panels.append(PanelSlot(
                key=key,
                face=tuple(int(i) for i in face),
                world_verts=tri,
                centroid=centroid,
                area=area,
                panel_type=panel_type,
            ))

    # -- panel interchange ----------------------------------------------------

    def cycle_panel(self, key: str, step: int) -> str:
        import materials
        current = self.config.panel_overrides.get(key, self.config.default_panel)
        names = materials.panel_type_names()
        idx = ((names.index(current) if current in names else 0)
               + step) % len(names)
        self.config.panel_overrides[key] = names[idx]
        return names[idx]

    def set_panel(self, key: str, name: str) -> None:
        if name in PANEL_TYPE_BY_NAME:
            self.config.panel_overrides[key] = name

    def set_all_panels(self, name: str) -> None:
        if name in PANEL_TYPE_BY_NAME:
            self.config.default_panel = name
            self.config.panel_overrides.clear()

    def panel_at(self, key: str) -> PanelSlot | None:
        for p in self.panels:
            if p.key == key:
                return p
        return None

    # -- ray picking ----------------------------------------------------------

    def pick_panel(
        self,
        origin: np.ndarray,
        direction: np.ndarray,
        max_distance: float = 120.0,
    ) -> tuple[PanelSlot | None, float]:
        """Möller–Trumbore over all panel slots; returns nearest hit."""
        best: PanelSlot | None = None
        best_t = max_distance
        o = np.asarray(origin, dtype=np.float64)
        d = normalize(direction)
        for panel in self.panels:
            v0, v1, v2 = panel.world_verts
            e1 = v1 - v0
            e2 = v2 - v0
            pvec = np.cross(d, e2)
            det = float(np.dot(e1, pvec))
            if abs(det) < 1e-9:
                continue
            inv = 1.0 / det
            tvec = o - v0
            u = float(np.dot(tvec, pvec)) * inv
            if u < 0.0 or u > 1.0:
                continue
            qvec = np.cross(tvec, e1)
            v = float(np.dot(d, qvec)) * inv
            if v < 0.0 or u + v > 1.0:
                continue
            t = float(np.dot(e2, qvec)) * inv
            if 0.05 < t < best_t:
                best_t = t
                best = panel
        return best, best_t

    # -- stats / bill of materials --------------------------------------------

    def layer_covered_panels(self) -> list[PanelSlot]:
        """Cladding layers skip open slots and windows."""
        return [
            p for p in self.panels
            if p.panel_type.name != "Open" and not p.panel_type.is_window
        ]

    def stats(self) -> dict:
        cfg = self.config
        shape = self.shape
        mat = self.material

        # Struts grouped into length classes (A, B, C, ...).
        groups: dict[float, int] = {}
        total_len = 0.0
        for _, _, length in self.struts:
            key = round(length, 2)
            groups[key] = groups.get(key, 0) + 1
            total_len += length
        classes = [
            (string.ascii_uppercase[i % 26], length, count)
            for i, (length, count) in enumerate(
                sorted(groups.items(), key=lambda kv: -kv[0])
            )
        ]

        cs_area = shape.cross_section_area(cfg.strut_width)
        frame_weight = total_len * cs_area * mat.density
        frame_cost = frame_weight * mat.cost_per_kg * 1.15

        hub_count = len(self.hubs)
        hub_scale = (cfg.strut_width / 0.05) ** 1.5
        if cfg.hub_style == "Metal Brackets":
            hub_scale *= 0.85               # plates weigh less than pucks
            hub_cost_scale = hub_scale * 1.25
        else:
            hub_cost_scale = hub_scale
        hub_weight = hub_count * mat.hub_weight * hub_scale
        hub_cost = hub_count * mat.hub_cost * hub_cost_scale

        bolt_count = len(self.bolt_points)
        bolt_weight = bolt_count * BOLT_WEIGHT
        bolt_cost = bolt_count * BOLT_COST
        hub_weight += bolt_weight
        hub_cost += bolt_cost

        # Quarter wedges are harvested four to a log.
        trees_required = 0
        if shape.kind == "wedge":
            trees_required = math.ceil(len(self.struts) / WEDGES_PER_TREE)
        trunk_stock_count = 0
        trunk_longest = max(groups.keys(), default=0.0)
        trunk_too_short = False
        if cfg.trunk_stock_length > 0 and shape.name == "Full Tree Trunk":
            trunk_stock_count = math.ceil(
                total_len * 1.10 / cfg.trunk_stock_length)
            trunk_too_short = trunk_longest > cfg.trunk_stock_length

        # Panels grouped by type.
        panel_groups: dict[str, dict] = {}
        panel_weight = 0.0
        panel_cost = 0.0
        solar_watts = 0.0
        for p in self.panels:
            t = p.panel_type
            g = panel_groups.setdefault(
                t.name, {"count": 0, "area": 0.0, "weight": 0.0, "cost": 0.0}
            )
            g["count"] += 1
            g["area"] += p.area
            g["weight"] += p.area * t.area_weight
            g["cost"] += p.area * t.cost_per_m2
            panel_weight += p.area * t.area_weight
            panel_cost += p.area * t.cost_per_m2
            solar_watts += p.area * t.watts_per_m2

        covered_area = sum(p.area for p in self.layer_covered_panels())
        layer_rows = []
        layer_weight = 0.0
        layer_cost = 0.0
        for layer in self.active_layers:
            w = covered_area * layer.area_weight
            c = covered_area * layer.cost_per_m2
            layer_rows.append((layer.name, covered_area, w, c))
            layer_weight += w
            layer_cost += c

        foundation = self.foundation
        f_radius = cfg.radius * cfg.foundation_scale
        f_area = math.pi * f_radius ** 2 if foundation.height > 0 else 0.0
        if foundation.name == "Bare Ground":
            f_area = 0.0
        f_weight = f_area * foundation.weight_per_m2
        f_cost = f_area * foundation.cost_per_m2

        base_z = self.geo.base_z
        base_ring_radius = math.sqrt(max(0.0, 1.0 - base_z * base_z))
        floor_area = math.pi * (base_ring_radius * cfg.radius) ** 2
        surface_area = sum(p.area for p in self.panels)
        height = (1.0 - base_z) * cfg.radius

        # Workshop fit-out: props and partition walls.
        import workshop
        prop_groups: dict[str, dict] = {}
        prop_weight = prop_cost = prop_watts = 0.0
        for entry in cfg.props:
            prop = workshop.PROP_TYPE_BY_NAME.get(entry.get("type"))
            if prop is None:
                continue
            g = prop_groups.setdefault(
                prop.name, {"count": 0, "weight": 0.0, "cost": 0.0,
                            "watts": 0.0})
            g["count"] += 1
            g["weight"] += prop.weight
            g["cost"] += prop.cost
            g["watts"] += prop.watts
            prop_weight += prop.weight
            prop_cost += prop.cost
            prop_watts += prop.watts

        wall_segments = workshop.partition_segments(self)
        wall_area = sum(s["length"] * s["height"] for s in wall_segments)
        wall_weight = wall_area * workshop.WALL_WEIGHT_PER_M2
        wall_cost = wall_area * workshop.WALL_COST_PER_M2

        wire_runs = workshop.wiring_runs(self)
        wire_len = sum(r["length"] for r in wire_runs)
        wire_cost = wire_len * workshop.WIRE_COST_PER_M
        pipe_runs = workshop.plumbing_runs(self)
        pex_len = sum(r["length"] for r in pipe_runs) * 2.0   # hot + cold
        drain_len = sum(r["length"] for r in pipe_runs)
        plumbing_cost = (pex_len * workshop.PEX_COST_PER_M
                         + drain_len * workshop.DRAIN_COST_PER_M
                         + len(pipe_runs) * workshop.FIXTURE_ROUGH_COST)

        assigned_sections = sum(
            1 for name in cfg.sections if name != "Unassigned")

        # Custom-panel hardware rollup (brackets, screws, seals...).
        import materials
        hardware: dict[str, int] = {}
        hardware_screws = 0
        for p in self.panels:
            definition = materials.CUSTOM_PANEL_DEFS.get(p.panel_type.name)
            if not definition:
                continue
            for comp_name, qty in definition.get("components", {}).items():
                comp = materials.PANEL_COMPONENT_BY_NAME.get(comp_name)
                if comp is None or qty <= 0:
                    continue
                hardware[comp_name] = hardware.get(comp_name, 0) + qty
                hardware_screws += comp.screws_each * qty

        structure_weight = (frame_weight + hub_weight + panel_weight
                            + layer_weight + prop_weight + wall_weight)
        total_cost = (frame_cost + hub_cost + panel_cost + layer_cost
                      + f_cost + prop_cost + wall_cost
                      + wire_cost + plumbing_cost)

        return {
            "frequency": cfg.frequency,
            "radius": cfg.radius,
            "height": height,
            "floor_area": floor_area,
            "surface_area": surface_area,
            "strut_classes": classes,
            "strut_count": len(self.struts),
            "strut_total_len": total_len,
            "hub_count": hub_count,
            "panel_groups": panel_groups,
            "panel_count": len(self.panels),
            "frame_weight": frame_weight,
            "frame_cost": frame_cost,
            "hub_weight": hub_weight,
            "hub_cost": hub_cost,
            "panel_weight": panel_weight,
            "panel_cost": panel_cost,
            "layer_rows": layer_rows,
            "layer_weight": layer_weight,
            "layer_cost": layer_cost,
            "foundation_name": foundation.name,
            "foundation_area": f_area,
            "foundation_weight": f_weight,
            "foundation_cost": f_cost,
            "structure_weight": structure_weight,
            "total_cost": total_cost,
            "solar_watts": solar_watts,
            "prop_groups": prop_groups,
            "prop_count": len(cfg.props),
            "prop_weight": prop_weight,
            "prop_cost": prop_cost,
            "prop_watts": prop_watts,
            "wall_count": len(wall_segments),
            "wall_area": wall_area,
            "wall_weight": wall_weight,
            "wall_cost": wall_cost,
            "assigned_sections": assigned_sections,
            "frame_style": cfg.frame_style,
            "hub_style": cfg.hub_style,
            "bolt_count": bolt_count,
            "trees_required": trees_required,
            "trunk_stock_length": cfg.trunk_stock_length,
            "trunk_circumference": cfg.trunk_circumference,
            "trunk_stock_count": trunk_stock_count,
            "trunk_too_short": trunk_too_short,
            "trunk_longest": trunk_longest,
            "wire_runs": len(wire_runs),
            "wire_len": wire_len,
            "wire_cost": wire_cost,
            "pipe_fixtures": len(pipe_runs),
            "pex_len": pex_len,
            "drain_len": drain_len,
            "plumbing_cost": plumbing_cost,
            "hardware": hardware,
            "hardware_screws": hardware_screws,
        }

    def bom_text(self) -> str:
        s = self.stats()
        cfg = self.config
        lines: list[str] = []
        add = lines.append
        add("=" * 62)
        add("GEODESIC DOME — BILL OF MATERIALS")
        add("=" * 62)
        add(f"Frequency:        {cfg.frequency}V (flat-base class I)")
        add(f"Radius:           {cfg.radius:.2f} m")
        add(f"Height:           {s['height']:.2f} m")
        add(f"Floor area:       {s['floor_area']:.1f} m^2")
        add(f"Surface area:     {s['surface_area']:.1f} m^2")
        add("")
        add("-- FRAME " + "-" * 53)
        add(f"Material:         {self.material.name}")
        add(f"Strut profile:    {self.shape.name}, "
            f"{cfg.strut_width * 100:.1f} cm wide")
        add(f"Frame style:      {s['frame_style']}")
        add(f"Struts:           {s['strut_count']} pcs, "
            f"{s['strut_total_len']:.1f} m total")
        for label, length, count in s["strut_classes"]:
            add(f"   {label}: {count:3d} x {length:.2f} m")
        if s["trees_required"]:
            add(f"Trees to harvest: {s['trees_required']} logs "
                f"({WEDGES_PER_TREE} quarter-wedges each)")
        if s["trunk_stock_count"]:
            add(f"Tree trunks:      {s['trunk_stock_count']} x "
                f"{s['trunk_stock_length']:.2f} m stock "
                f"({s['trunk_stock_length'] * 3.28084:.1f} ft)")
            if s["trunk_circumference"]:
                add(f"Trunk size:       "
                    f"{s['trunk_circumference'] * 39.3701:.1f} in circ "
                    f"({cfg.strut_width * 39.3701:.1f} in dia)")
            if s["trunk_too_short"]:
                add(f"WARNING: longest strut is {s['trunk_longest']:.2f} m, "
                    "longer than the selected trunk stock.")
        if s["bolt_count"]:
            add(f"Edge bolts:       {s['bolt_count']} pcs (hubless joins)")
        else:
            add(f"Hubs:             {s['hub_count']} pcs "
                f"({s['hub_style']})")
        add(f"Frame weight:     {s['frame_weight']:.1f} kg "
            f"(+ hubs {s['hub_weight']:.1f} kg)")
        add(f"Frame cost:       ${s['frame_cost']:,.0f} "
            f"(+ hubs ${s['hub_cost']:,.0f})")
        add("")
        add("-- PANELS " + "-" * 52)
        for name, g in sorted(s["panel_groups"].items()):
            add(f"   {name:<18} {g['count']:3d} pcs  {g['area']:7.1f} m^2  "
                f"{g['weight']:8.1f} kg  ${g['cost']:,.0f}")
        if s["solar_watts"] > 0:
            add(f"   Solar capacity:  {s['solar_watts'] / 1000.0:.2f} kW")
        add("")
        add("-- CLADDING LAYERS " + "-" * 43)
        if s["layer_rows"]:
            for name, area, weight, cost in s["layer_rows"]:
                add(f"   {name:<18} {area:7.1f} m^2  {weight:8.1f} kg  "
                    f"${cost:,.0f}")
        else:
            add("   (none)")
        add("")
        add("-- FOUNDATION " + "-" * 48)
        add(f"   {s['foundation_name']:<18} {s['foundation_area']:7.1f} m^2  "
            f"{s['foundation_weight']:8.1f} kg  ${s['foundation_cost']:,.0f}")
        add("")
        add("-- WORKSHOP FIT-OUT " + "-" * 42)
        import workshop
        for i, name in enumerate(cfg.sections):
            if name != "Unassigned":
                add(f"   {workshop.section_label(i):<14} {name}")
        if s["wall_count"]:
            add(f"   Partition walls   {s['wall_count']} pcs  "
                f"{s['wall_area']:.1f} m^2  {s['wall_weight']:.0f} kg  "
                f"${s['wall_cost']:,.0f}")
        if s["prop_groups"]:
            for name, g in sorted(s["prop_groups"].items()):
                watts = f"  {g['watts']:.0f} W" if g["watts"] else ""
                add(f"   {name:<18} {g['count']:3d} pcs  "
                    f"{g['weight']:6.0f} kg  ${g['cost']:,.0f}{watts}")
            add(f"   Equipment power:  {s['prop_watts']:,.0f} W")
        if not s["prop_groups"] and not s["wall_count"]:
            add("   (empty)")
        add("")
        if s["wire_runs"]:
            add("-- ELECTRICAL ROUGH-IN " + "-" * 39)
            add(f"   Wire runs:        {s['wire_runs']} circuits, "
                f"{s['wire_len']:.1f} m conduit  ${s['wire_cost']:,.0f}")
        if s["pipe_fixtures"]:
            add("-- PLUMBING ROUGH-IN " + "-" * 41)
            add(f"   Fixtures:         {s['pipe_fixtures']}")
            add(f"   PEX supply:       {s['pex_len']:.1f} m "
                f"(hot + cold)")
            add(f"   Drain/waste:      {s['drain_len']:.1f} m")
            add(f"   Rough-in cost:    ${s['plumbing_cost']:,.0f}")
        if s["hardware"]:
            add("-- PANEL HARDWARE (custom panels) " + "-" * 28)
            for comp_name, qty in sorted(s["hardware"].items()):
                add(f"   {comp_name:<18} {qty} pcs")
            add(f"   Screws:           {s['hardware_screws']} pcs")
        if s["wire_runs"] or s["pipe_fixtures"] or s["hardware"]:
            add("")
        hours = getattr(self, "construction_hours", 0.0)
        if hours:
            add(f"ESTIMATED CONSTRUCTION: {hours:,.0f} labor-hours "
                f"(~{hours / 8.0:,.0f} days @ 8 h, 1 worker)")
        add("=" * 62)
        add(f"STRUCTURE WEIGHT (above foundation): "
            f"{s['structure_weight']:,.0f} kg")
        add(f"TOTAL ESTIMATED COST:                ${s['total_cost']:,.0f}")
        add("=" * 62)
        return "\n".join(lines)

    # -- persistence ----------------------------------------------------------

    def save(self, path: str | Path = "dome_design.json") -> Path:
        path = Path(path)
        path.write_text(
            json.dumps(self.config.to_dict(), indent=2), encoding="utf-8"
        )
        return path

    def load(self, path: str | Path = "dome_design.json") -> bool:
        path = Path(path)
        if not path.exists():
            return False
        self.config = DomeConfig.from_dict(
            json.loads(path.read_text(encoding="utf-8"))
        )
        self.rebuild()
        return True
