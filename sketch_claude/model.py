"""The dome as a buildable model: every stick, board, card and fitting, with its numbers.

``build(Spec())`` returns a :class:`Model` -- a list of :class:`Piece` (each a solid with a
name, a tag, a material and the figures a builder needs to cut it) plus the tables the plan
set prints. The sphere, the cut, the panel classes and the stick bevels come from
``two_v_demo.panel_method``; this module adds what a plan set needs on top of that solution:

* each panel's three sticks as solids: outer face, inner face, the bevelled edge on the
  plane halfway between the two panels, the square inside edge, the square tail that butts
  the next stick (the *initial* mitre) and the compound head that runs to the corner (the
  *final* mitre). Their saw settings are read off those planes, and the self-test checks
  them against panel_method's own bevel and pinwheel figures;
* base sections under every base edge, tapered where the 5/8 base zig-zags;
* a framed door: the panels it passes through are clipped into partial panels along the
  door's planes, with plywood door cards between the posts and the dome's skin;
* the deck, the skin, windows, a skylight, a stove pipe, a furnished room and a person
  for scale.

Units are metres and degrees throughout; the sheets convert.
"""

from __future__ import annotations

import math
from dataclasses import asdict, dataclass, field, fields, replace
from functools import lru_cache

import numpy as np

from two_v_demo import panel_method as pm
from two_v_demo.geometry import MM_PER_INCH

from . import solids as S
from .solids import Mesh, unit

IN = MM_PER_INCH / 1000.0          # one inch in metres
FT = 12 * IN


# ----------------------------------------------------------------------
# Declared inputs: everything the geometry cannot supply, with its reason
# ----------------------------------------------------------------------

@dataclass(frozen=True)
class Declared:
    value: float
    unit: str
    why: str
    kind: str = "choice"          # "choice" (a decision) | "estimate" (a builder's allowance)


_REF = pm.reference()

DECLARED: dict[str, Declared] = {
    "diameter_m": Declared(_REF.diameter_m, "m", "base corner to base corner: the repository's reference 3V panel dome "
                                                  "(panel_method.CONSTANTS base_ft, 16 ft)"),
    "stick_w_m": Declared((pm.CONSTANTS["stock_d_in"].value - pm.CONSTANTS["kerf_in"].value) / 2 * IN, "m",
                          "a stick's width flat on the jig: half a 2x3's 2-1/2 in, less the kerf. The rip that halves "
                          "the 2x3 is the bevel itself, so it runs through the board's thickness, not across it"),
    "stick_d_m": Declared(pm.CONSTANTS["stock_w_in"].value * IN, "m",
                          "a stick's depth through the wall: the 2x3's 1-1/2 in thickness, which the bevelled rip face spans"),
    "kerf_m": Declared(pm.CONSTANTS["kerf_in"].value * IN, "m", "a common table-saw blade (panel_method)"),
    "base_h_m": Declared(pm.CONSTANTS["base_board_in"].value * IN, "m", "base board height under the lowest base corner: a 2x6 on edge (panel_method)"),
    "base_t_m": Declared(1.5 * IN, "m", "base board thickness: 2x lumber"),
    "plate_w_m": Declared(3.5 * IN, "m", "bottom plate width: a pressure-treated 2x4 laid flat"),
    "plate_t_m": Declared(1.5 * IN, "m", "bottom plate thickness"),
    "riser_m": Declared(0.0, "m", "pony wall under the base sections: none on the reference dome"),
    "door_w_m": Declared(0.80, "m", "clear door opening: a 32 in leaf's opening, the narrowest an accessible door allows"),
    "door_h_m": Declared(1.93, "m", "clear door opening height: 6 ft 4 in, a standard leaf"),
    "door_h_min_m": Declared(1.80, "m", "the lowest clear opening accepted when the head is moved to a panel corner: "
                                         "small domes commonly take a 6 ft door"),
    "door_gap_m": Declared(0.010, "m", "gap round the leaf for hinges and swelling"),
    "post_w_m": Declared(1.5 * IN, "m", "door post across the opening: a 2x4's thickness"),
    "post_d_m": Declared(3.5 * IN, "m", "door post through the wall: a 2x4's width"),
    "head_h_m": Declared(3.5 * IN, "m", "door head depth: a 2x4 on edge"),
    "card_t_m": Declared(0.75 * IN, "m", "door cards: 3/4 in plywood fins between the posts and the skin"),
    "leaf_t_m": Declared(1.5 * IN, "m", "door leaf frame thickness: 2x stock"),
    "skin_t_m": Declared(0.5 * IN, "m", "panel skin: 1/2 in plywood under shingles (cabin), or twin-wall polycarbonate (clear)"),
    "glass_t_m": Declared(0.25 * IN, "m", "window glazing: 1/4 in polycarbonate"),
    "sheet_w_m": Declared(4 * FT, "m", "a sheet of plywood: 4 ft"),
    "sheet_l_m": Declared(8 * FT, "m", "a sheet of plywood: 8 ft"),
    "board_l_m": Declared(8 * FT, "m", "2x3 stock length: 8 ft studs, each ripped into two sticks"),
    "trim_m": Declared(0.025, "m", "extra length cut on every stick before its final mitre", "estimate"),
    "deck_h_m": Declared(0.45, "m", "deck top above the ground: piers and joists under it"),
    "deck_front_m": Declared(2.4, "m", "the porch in front of the door"),
    "porch_w_m": Declared(3.2, "m", "porch width across the door: room for two chairs either side of the path"),
    "deck_board_m": Declared(0.14, "m", "decking pitch: a 5/4x6 board (5-1/2 in) and its gap"),
    "deck_board_l_m": Declared(12 * FT, "m", "decking stock length: 12 ft"),
    "joist_w_m": Declared(1.5 * IN, "m", "deck joist thickness: 2x8"),
    "joist_d_m": Declared(7.25 * IN, "m", "deck joist depth: 2x8"),
    "screws_per_corner": Declared(2, "screws", "75 mm screws through each panel corner joint", "estimate"),
    "seam_screw_m": Declared(0.20, "m", "panel-to-panel screw spacing along a seam", "estimate"),
    "staple_m": Declared(0.05, "m", "staple spacing round a skinned section", "estimate"),
    "waste": Declared(0.10, "fraction", "allowance on sheet goods and tape for offcuts and mistakes", "estimate"),
    "person_m": Declared(1.75, "m", "the figure standing beside the dome for scale"),
}


def D(name: str) -> float:
    return DECLARED[name].value


# ----------------------------------------------------------------------
# What a model is built from
# ----------------------------------------------------------------------

CUTS = {
    # (frequency, name) -> target fraction of the sphere's diameter kept above the base
    (2, "1/2"): 0.5, (3, "5/8"): 5 / 8, (3, "1/2"): 0.5, (4, "1/2"): 0.5, (4, "5/8"): 5 / 8,
}


@dataclass(frozen=True)
class Spec:
    frequency: int = 3
    cut: str = "5/8"
    diameter_m: float = D("diameter_m")
    stick_w_m: float = D("stick_w_m")
    stick_d_m: float = D("stick_d_m")
    riser_m: float = D("riser_m")
    door: bool = True
    door_w_m: float = D("door_w_m")
    door_h_m: float = D("door_h_m")
    windows: int = 5
    skylight: bool = True
    skin: str = "cabin"            # cabin | clear | none
    furnish: bool = True
    porch: bool = True
    stove: bool = True
    people: bool = True

    @classmethod
    def from_dict(cls, d: dict) -> "Spec":
        names = {f.name: f for f in fields(cls)}
        kw = {}
        for k, v in (d or {}).items():
            if k not in names:
                continue
            t = names[k].type
            if t in ("bool", bool):
                kw[k] = v if isinstance(v, bool) else str(v).lower() in ("1", "true", "yes", "on")
            elif t in ("int", int):
                kw[k] = int(float(v))
            elif t in ("float", float):
                kw[k] = float(v)
            else:
                kw[k] = str(v)
        s = cls(**kw)
        if (s.frequency, s.cut) not in CUTS:
            s = replace(s, cut=next(c for f, c in CUTS if f == s.frequency))
        return s

    def to_dict(self) -> dict:
        return asdict(self)

    @property
    def title(self) -> str:
        return f"{self.frequency}V {self.cut} panel dome, {self.diameter_m:.2f} m"


# ----------------------------------------------------------------------
# A piece of the model
# ----------------------------------------------------------------------

@dataclass
class Piece:
    id: str
    name: str
    tag: str                       # frame | skin | glass | base | deck | door | furniture | person | site
    material: str
    mesh: Mesh
    info: dict = field(default_factory=dict)
    step: int = 0                  # assembly stage it goes on in
    group: str = ""                # what it belongs to (a panel's id, a section's id)
    explode: tuple = (0.0, 0.0, 0.0)   # direction it moves in an exploded view


MATERIALS: dict[str, dict] = {
    # colour (linear-ish sRGB hex), opacity, roughness hint, emissive
    "pine":      {"color": "#dcb57e", "label": "Pine panel sticks (2x3 ripped)"},
    "pine_dark": {"color": "#c99a5e", "label": "Pine, partial-panel and centre struts"},
    "plate":     {"color": "#8f9a63", "label": "Pressure-treated plate"},
    "base":      {"color": "#c7a06a", "label": "Base board"},
    "ply":       {"color": "#d8bf8e", "label": "Plywood"},
    "card":      {"color": "#cfae78", "label": "Door card (3/4 in plywood)"},
    "shingle":   {"color": "#6f5747", "label": "Shingle skin"},
    "shingle2":  {"color": "#7c6352", "label": "Shingle skin"},
    "shingle3":  {"color": "#665040", "label": "Shingle skin"},
    "poly":      {"color": "#cfe8ef", "opacity": 0.35, "label": "Clear polycarbonate"},
    "glass":     {"color": "#a9d7ea", "opacity": 0.28, "label": "Window glazing"},
    "trim":      {"color": "#e9e4d8", "label": "Painted trim"},
    "door":      {"color": "#8c5a3a", "label": "Door leaf"},
    "deck":      {"color": "#a8774f", "label": "Deck boards"},
    "joist":     {"color": "#8f6b45", "label": "Deck framing"},
    "concrete":  {"color": "#b9b5ad", "label": "Pier"},
    "steel":     {"color": "#3b3d40", "label": "Steel"},
    "hearth":    {"color": "#8a817a", "label": "Hearth stone"},
    "fabric":    {"color": "#d9cdb8", "label": "Linen"},
    "fabric2":   {"color": "#5e7d74", "label": "Wool"},
    "rug":       {"color": "#b9634a", "label": "Rug"},
    "leaf":      {"color": "#5f8a4c", "label": "Plant"},
    "pot":       {"color": "#b8735a", "label": "Pot"},
    "lamp":      {"color": "#ffd59a", "emissive": 1.0, "label": "Lamp"},
    "skin_tone": {"color": "#c99a7a", "label": "Person"},
    "denim":     {"color": "#4a5f7d", "label": "Person"},
    "shirt":     {"color": "#c8553d", "label": "Person"},
    "hair":      {"color": "#3a2a20", "label": "Person"},
    "ground":    {"color": "#9fb07a", "label": "Ground"},
    "gravel":    {"color": "#c9c1b2", "label": "Gravel"},
    "jig":       {"color": "#e8dcc0", "label": "Jig plywood"},
    "rail":      {"color": "#c69c64", "label": "Jig rail"},
    "clamp":     {"color": "#3d5a99", "label": "Clamp"},
    "tool":      {"color": "#5a5f66", "label": "Saw"},
    "tool2":     {"color": "#d4a72c", "label": "Saw"},
    "blade":     {"color": "#c6c9cc", "label": "Blade"},
}


@dataclass
class Model:
    spec: Spec
    pieces: list[Piece]
    tables: dict
    landmarks: dict

    def by_tag(self, *tags: str) -> list[Piece]:
        return [p for p in self.pieces if p.tag in tags]

    def bounds(self, tags=None) -> tuple[np.ndarray, np.ndarray]:
        ps = [p for p in self.pieces if (tags is None or p.tag in tags) and len(p.mesh.verts)]
        v = np.vstack([p.mesh.verts for p in ps])
        return v.min(axis=0), v.max(axis=0)


# ----------------------------------------------------------------------
# The sphere, the cut, the turn that puts a level base edge at the door
# ----------------------------------------------------------------------

def choose_cut(frequency: int, name: str) -> pm.Truncation:
    target = CUTS[(frequency, name)]
    sphere = pm.three_v_sphere(frequency)
    best = None
    for level in sphere.levels[1:-1]:
        t = pm.truncate(sphere, level)
        if not t.base:
            continue
        uses: dict[int, int] = {}
        for e in t.base:
            uses[e.a] = uses.get(e.a, 0) + 1
            uses[e.b] = uses.get(e.b, 0) + 1
        if any(n != 2 for n in uses.values()):
            continue
        score = abs(t.height_fraction - target)
        if best is None or score < best[0] - 1e-9:
            best = (score, t)
    return best[1]


def _rot_z(deg: float) -> np.ndarray:
    a = math.radians(deg)
    return np.array([[math.cos(a), -math.sin(a), 0], [math.sin(a), math.cos(a), 0], [0, 0, 1.0]])


# ----------------------------------------------------------------------
# A panel: a flat convex polygon whose every side knows the plane its stick's edge lies on
# ----------------------------------------------------------------------

@dataclass
class Side:
    kind: str                      # "seam" (another panel), "base" (a base board), "cut" (door card / head)
    plane: tuple                   # (n, c): the stick's edge face, n pointing out of the panel
    letter: str = ""
    other: int = -1                # neighbouring face index for a seam


@dataclass
class Panel:
    id: str
    face: int                      # sphere face it is made from
    kind: str                      # pentagon | hexagon
    cls: str                       # its panel class key, or "partial"
    poly: list                     # outer-face corners, counter-clockwise from outside
    sides: list                    # Side per edge poly[i] -> poly[i+1]
    normal: np.ndarray
    partial: bool = False
    window: bool = False
    skylight: bool = False
    pipe: bool = False
    level: int = 0                 # ring, counted from the base


def _inward(poly, normal, i) -> np.ndarray:
    a, b = poly[i], poly[(i + 1) % len(poly)]
    return unit(np.cross(normal, b - a))


def stick_planes(p: Panel, k: int, w: float, d: float) -> dict:
    """The six half-spaces of stick ``k`` (the stick along side k) in the pinwheel."""
    n = len(p.poly)
    N = p.normal
    a, b = p.poly[k], p.poly[(k + 1) % n]
    u = _inward(p.poly, N, k)
    u_next = _inward(p.poly, N, (k + 1) % n)
    edge = p.sides[k].plane
    head = p.sides[(k - 1) % n].plane
    c_out = float(N @ a)
    return {
        "outer": (N, c_out),
        "inner": (-N, -(c_out - d)),
        "edge": edge,
        "side": (u, float(u @ a + w)),
        "head": head,
        "tail": (-u_next, -float(u_next @ b + w)),
    }


def saw_setting(normal, along, across, through) -> tuple[float, float]:
    """(mitre, bevel) off square for an end cut whose plane has ``normal``, on a stick lying
    face down on the saw table: ``along`` its length, ``across`` its width, ``through`` its depth."""
    n = unit(normal)
    x, y, z = abs(float(n @ along)), abs(float(n @ across)), abs(float(n @ through))
    bevel = math.degrees(math.asin(min(1.0, z)))
    mitre = math.degrees(math.atan2(y, x))
    return mitre, bevel


def stick_figures(p: Panel, k: int, w: float, d: float, mesh: Mesh) -> dict:
    n = len(p.poly)
    N = p.normal
    a, b = p.poly[k], p.poly[(k + 1) % n]
    e = unit(b - a)
    u = _inward(p.poly, N, k)
    pl = stick_planes(p, k, w, d)
    head_m, head_b = saw_setting(pl["head"][0], e, u, N)
    tail_m, tail_b = saw_setting(pl["tail"][0], e, u, N)
    m = unit(pl["edge"][0])
    rip = math.degrees(math.acos(min(1.0, abs(float(m @ u)))))
    proj = mesh.verts @ e
    # along the outline (the outer face's outer edge): from the corner to the tail's long point
    tail_t = (float(u_next_dot(p, k, w)))
    return {
        "side": p.sides[k].letter or p.sides[k].kind,
        "kind": p.sides[k].kind,
        "long_m": float(proj.max() - proj.min()),
        "outline_m": tail_t,
        "rip_deg": rip,
        "head_mitre": head_m, "head_bevel": head_b,
        "tail_mitre": tail_m, "tail_bevel": tail_b,
    }


def u_next_dot(p: Panel, k: int, w: float) -> float:
    """Length of stick ``k`` along the outline: corner ``k`` to where its tail meets the next stick's inside face."""
    n = len(p.poly)
    a, b = p.poly[k], p.poly[(k + 1) % n]
    e = b - a
    u_next = _inward(p.poly, p.normal, (k + 1) % n)
    # a + t e on the plane u_next . x = u_next . b + w
    t = (float(u_next @ b) + w - float(u_next @ a)) / float(u_next @ e)
    return t * float(np.linalg.norm(e))


# ----------------------------------------------------------------------
# Building it
# ----------------------------------------------------------------------

@lru_cache(maxsize=16)
def _build_cached(spec: Spec) -> Model:
    return _build(spec)


def build(spec: Spec | None = None) -> Model:
    return _build_cached(spec or Spec())


def _build(spec: Spec) -> Model:
    cut = choose_cut(spec.frequency, spec.cut)
    sphere = cut.sphere
    R = (spec.diameter_m / 2) / cut.base_radius
    w, d = spec.stick_w_m, spec.stick_d_m
    pdome = pm.PanelDome(R, w, d, cut)

    # Turn the dome so a level base edge (or the first edge) faces -y, the door side.
    level_edges = [e for e in cut.base if not e.tapered] or list(cut.base)
    door_edge = level_edges[0]
    mid = (sphere.vertices[door_edge.a] + sphere.vertices[door_edge.b]) / 2
    turn = -90.0 - math.degrees(math.atan2(mid[1], mid[0]))
    rot = _rot_z(turn)
    base_top = D("plate_t_m") + D("base_h_m") + spec.riser_m
    lift = base_top - cut.cut_level * R
    V = (sphere.vertices @ rot.T) * R + np.array([0, 0, lift])
    centre = np.array([0, 0, lift])

    kept = list(cut.faces)
    kept_set = set(kept)
    edge_faces: dict[tuple[int, int], list[int]] = {}
    for i in kept:
        t = sphere.faces[i]
        for k in range(3):
            edge_faces.setdefault(tuple(sorted((int(t[k]), int(t[(k + 1) % 3])))), []).append(i)

    def face_normal(i):
        p0, p1, p2 = (V[k] for k in sphere.faces[i])
        return unit(np.cross(p1 - p0, p2 - p0))

    normals = {i: face_normal(i) for i in kept}
    base_set = {tuple(sorted((e.a, e.b))) for e in cut.base}

    # panel classes, by panel_method's own grouping (kind + sorted letters)
    classes = pdome.panel_classes()
    cls_of_key = {(pc.kind, tuple(sorted(pc.letters))): pc for pc in classes}
    cls_names = {pc.key: n for n, pc in zip("ABCDEFGHIJKLMNOP", classes)}

    def letter(a, b):
        return sphere.chord_letter(a, b)

    # -- each face as a polygon with its sides' edge planes --
    panels: list[Panel] = []
    face_panel: dict[int, Panel] = {}
    levels = sorted({round(float(np.mean(V[sphere.faces[i]][:, 2])), 4) for i in kept})
    for i in kept:
        t = [int(x) for x in sphere.faces[i]]
        N = normals[i]
        poly = [V[k].copy() for k in t]
        sides = []
        for k in range(3):
            a, b = t[k], t[(k + 1) % 3]
            key = tuple(sorted((a, b)))
            pa, pb = V[a], V[b]
            e = unit(pb - pa)
            u = unit(np.cross(N, pb - pa))
            if key in base_set:
                h = u.copy()
                h[2] = 0
                h = unit(h)
                m = unit(np.cross(e, h))
                if m @ u > 0:
                    m = -m
                sides.append(Side("base", (m, float(m @ pa)), letter(a, b)))
            else:
                other = next(j for j in edge_faces[key] if j != i)
                s = N + normals[other]
                m = unit(np.cross(e, s))
                if m @ u > 0:
                    m = -m
                sides.append(Side("seam", (m, float(m @ pa)), letter(a, b), other))
        letters = tuple(sorted(letter(t[k], t[(k + 1) % 3]) for k in range(3)))
        kind = "pentagon" if sphere.is_pentagon_face(i) else "hexagon"
        pc = cls_of_key[(kind, letters)]
        cz = round(float(np.mean([p[2] for p in poly])), 4)
        p = Panel(f"F{i:03d}", i, kind, cls_names[pc.key], poly, sides, N, level=levels.index(cz))
        panels.append(p)
        face_panel[i] = p

    # -- the door: clip the panels it passes through --
    door = None
    warnings: list[str] = []
    if spec.door:
        door, panels, warnings = _cut_door(spec, panels, V, cut, base_top, w)

    # -- windows, skylight, stove pipe --
    whole = [p for p in panels if not p.partial]
    zmax = max(float(np.max(V[:, 2])), 0)
    if spec.skylight:
        apex = int(np.argmax(V[:, 2]))
        for p in whole:
            if apex in sphere.faces[p.face]:
                p.skylight = True
    if spec.windows:
        candidates = [p for p in whole if not p.skylight and p.kind == "hexagon"]
        # a ring at eye height: the panels whose centres sit nearest 1.4 m above the floor
        def eye(p):
            return abs(float(np.mean([q[2] for q in p.poly])) - (base_top + 1.25))
        ring_level = min(candidates, key=eye).level
        ring = [p for p in candidates if p.level == ring_level]
        ring.sort(key=lambda p: _az(p))
        # skip the door's side: the window ring starts a fifth of a turn round from the door
        ring = [p for p in ring if abs(_angle_diff(_az(p), -90.0)) > 40.0]
        n = min(spec.windows, len(ring))
        if n:
            step = len(ring) / n
            for k in range(n):
                ring[int(k * step + step / 2) % len(ring)].window = True
    if spec.stove:
        stove_xy = np.array([0.0, 0.42 * spec.diameter_m / 2 * 1.0 + 0.0])
        hit = _vertical_hit(panels, stove_xy)
        if hit is not None:
            hit.pipe = True

    # -- pieces --
    pieces: list[Piece] = []
    ring_count = max(p.level for p in panels) + 1
    for p in panels:
        sticks = []
        for k in range(len(p.poly)):
            mesh = S.solid(list(stick_planes(p, k, w, d).values()))
            if not len(mesh.verts):
                warnings.append(f"{p.id} side {k}: no stick fits")
                continue
            fig = stick_figures(p, k, w, d, mesh)
            fig.update(panel=p.id, cls=p.cls, k=k)
            mat = "pine_dark" if p.partial or p.sides[k].kind == "cut" else "pine"
            pieces.append(Piece(f"{p.id}-s{k}", f"Stick {p.cls}{k + 1}" if not p.partial else f"Partial {p.id} stick {k + 1}",
                                "frame", mat, mesh, fig, step=2 + p.level, group=p.id, explode=tuple(p.normal)))
            sticks.append(fig)
        p_info = {"panel": p.id, "cls": p.cls, "kind": p.kind, "partial": p.partial, "level": p.level,
                  "sides_m": [float(np.linalg.norm(p.poly[(k + 1) % len(p.poly)] - p.poly[k])) for k in range(len(p.poly))],
                  "area_m2": S.poly_area(p.poly)}
        # skin: a thin slab just outside the outer face
        if spec.skin != "none" or p.window or p.skylight:
            if p.window or p.skylight:
                mat, tag, t = "glass", "glass", D("glass_t_m")
            elif spec.skin == "clear":
                mat, tag, t = "poly", "glass", D("skin_t_m") / 2
            else:
                mat, tag, t = ("shingle", "shingle2", "shingle3")[p.face % 3], "skin", D("skin_t_m")
            slab = S.prism([q + p.normal * 0.0015 for q in p.poly], p.normal, t)
            if tag == "skin":
                slab = _courses(slab, [q + p.normal * (0.0016 + t) for q in p.poly], p.normal)
            pieces.append(Piece(f"{p.id}-skin", ("Window " if p.window else "Skylight " if p.skylight else "Skin ") + p.id,
                                tag, mat, slab, p_info, step=2 + ring_count + 1, group=p.id, explode=tuple(p.normal * 1.6)))
            if p.window or p.skylight:
                pieces.append(_window_trim(p, t))
    # base sections
    pieces += _base_sections(spec, cut, V, door)
    # door parts
    if door:
        pieces += door["pieces"]
    # deck, porch, piers
    floor_poly = [V[v] for v in _base_loop(cut)]
    pieces += _deck(spec, floor_poly, door)
    if spec.stove:
        pieces += _stove(spec, panels, base_top)
    if spec.furnish:
        pieces += _furniture(spec, floor_poly, door)
    if spec.people:
        pieces += _person(np.array([-1.15, -spec.diameter_m / 2 - 0.9, 0.0]), 160.0)
    pieces += _site(spec)

    model = Model(spec, pieces, {}, {})
    model.landmarks = {
        "centre": centre.tolist(), "apex": [0.0, 0.0, float(V[:, 2].max())],
        "door": [0.0, float(door["y_post"]) if door else -spec.diameter_m / 2, D("door_h_m") / 2],
        "floor": [0.0, 0.0, 0.0], "R": R,
    }
    model.tables = _tables(spec, pdome, panels, pieces, door, cut, V, warnings, ring_count, base_top)
    model.panels = panels
    model.pdome = pdome
    return model



def _courses(slab: Mesh, poly, normal, spacing: float = 0.125) -> Mesh:
    """Shingle courses inked across a skin panel: level lines up its slope, ``spacing`` apart."""
    up = np.array([0, 0, 1.0])
    g = up - (up @ normal) * normal
    if np.linalg.norm(g) < 0.2:
        return slab
    g = unit(g)
    vals = [float(g @ q) for q in poly]
    verts, edges = list(slab.verts), list(map(tuple, slab.edges))
    s0 = math.floor(min(vals) / spacing) * spacing + spacing
    k = len(poly)
    while s0 < max(vals) - 1e-6:
        hits = []
        for i in range(k):
            a, b = poly[i], poly[(i + 1) % k]
            da, db = float(g @ a) - s0, float(g @ b) - s0
            if da * db < 0:
                hits.append(a + (b - a) * (da / (da - db)))
        if len(hits) == 2:
            verts += hits
            edges.append((len(verts) - 2, len(verts) - 1))
        s0 += spacing
    return Mesh(np.array(verts), slab.tris, np.array(edges, dtype=int), slab.polys)


def _az(p: Panel) -> float:
    c = np.mean(p.poly, axis=0)
    return math.degrees(math.atan2(c[1], c[0]))


def _angle_diff(a: float, b: float) -> float:
    return (a - b + 180) % 360 - 180


def _vertical_hit(panels, xy) -> Panel | None:
    """The whole panel a vertical line through ``xy`` leaves the dome by."""
    best = None
    for p in panels:
        if p.partial or p.skylight or p.window:
            continue
        P = [np.asarray(q) for q in p.poly]
        inside = True
        for i in range(len(P)):
            a, b = P[i][:2], P[(i + 1) % len(P)][:2]
            cr = (b[0] - a[0]) * (xy[1] - a[1]) - (b[1] - a[1]) * (xy[0] - a[0])
            if cr < 0:
                inside = False
                break
        if inside and (best is None or np.mean([q[2] for q in P]) > np.mean([q[2] for q in best.poly])):
            best = p
    return best


def _base_loop(cut: pm.Truncation) -> list[int]:
    nxt: dict[int, list[int]] = {}
    for e in cut.base:
        nxt.setdefault(e.a, []).append(e.b)
        nxt.setdefault(e.b, []).append(e.a)
    start = cut.base[0].a
    loop, prev, cur = [start], None, start
    while True:
        a, b = nxt[cur]
        n = b if a == prev else a
        if n == start:
            break
        loop.append(n)
        prev, cur = cur, n
    return loop


# ----------------------------------------------------------------------
# The door
# ----------------------------------------------------------------------

def _cut_door(spec: Spec, panels: list[Panel], V, cut, base_top, w):
    """Clip the panels in front of the door into partial panels, and frame the opening.

    Seen from the front (the door faces -y), the opening is the strip ``|x| < X`` below
    ``z = Z``, where ``X`` is the outside face of the door cards and ``Z`` the top of the
    head. Each panel that strip passes through keeps up to three convex pieces: left of
    it, right of it, above it. Their new edges are square struts that bear on the cards
    and the head. The posts stand inside the cards, as far forward as the skin allows.
    """
    warnings: list[str] = []
    min_thick = 2.5 * w
    pw_, ct_, hh_ = D("post_w_m"), D("card_t_m"), D("head_h_m")
    X0 = spec.door_w_m / 2 + pw_ + ct_
    Z0 = spec.door_h_m + hh_
    front_v = [q for p in panels for q in p.poly if q[1] < 0]
    # A card plane that clips the corner off a panel leaves a sliver too thin to frame. The
    # door is fitted to the dome instead: the cards move out (and the head up) to the nearest
    # panel corners until no sliver is left, never in, so the opening only gets bigger.
    xs = [X0] + sorted({round(abs(float(q[0])), 9) for q in front_v if X0 < abs(q[0]) < X0 + 0.30})
    Zmin = D("door_h_min_m") + hh_

    def crossings(X):
        """Heights where a panel edge crosses a card plane: a head there leaves no stub of a side."""
        zs = set()
        for p in panels:
            P = p.poly
            for i in range(len(P)):
                a, b = P[i], P[(i + 1) % len(P)]
                for xp in (X, -X):
                    if (a[0] - xp) * (b[0] - xp) < 0 and a[1] < 0:
                        z = a[2] + (b[2] - a[2]) * (xp - a[0]) / (b[0] - a[0])
                        if Zmin <= z < Z0 + 0.35:
                            zs.add(round(float(z), 9))
        return zs

    best = None
    short = 3 * w
    for X in xs:
        zs = [Z0] + sorted({round(float(q[2]), 9) for q in front_v if Zmin <= q[2] < Z0 + 0.35} | crossings(X),
                           key=lambda z: abs(z - Z0))
        for Z in zs:
            out, slivers = _door_clip(panels, X, Z, min_thick)
            stubs = sum(1 for p in out if p.partial for k in range(len(p.poly))
                        if np.linalg.norm(p.poly[(k + 1) % len(p.poly)] - p.poly[k]) < short)
            score = (len(slivers), stubs, (X - X0) + abs(Z - Z0))
            if best is None or score < best[0]:
                best = (score, X, Z, out, slivers)
        if best[0][0] == 0 and best[0][1] == 0:
            break
    _, X, Z, out, slivers = best
    # A seam that now borders the opening (its neighbour was inside the door) lies on a card's
    # plane or the head's: it becomes a door side, bearing on the card or the head.
    for p in out:
        for k, sd in enumerate(p.sides):
            if sd.kind != "seam":
                continue
            a, b = p.poly[k], p.poly[(k + 1) % len(p.poly)]
            if a[1] >= 0 or b[1] >= 0:
                continue
            plane = None
            for sx in (-1, 1):
                if abs(a[0] - sx * X) < 1e-6 and abs(b[0] - sx * X) < 1e-6 and max(a[2], b[2]) <= Z + 1e-6:
                    plane = (np.array([float(-sx), 0, 0]) * (1 if np.mean([q[0] for q in p.poly]) * sx < 0 else -1), None)
            if abs(a[2] - Z) < 1e-6 and abs(b[2] - Z) < 1e-6 and max(abs(a[0]), abs(b[0])) <= X + 1e-6:
                plane = (np.array([0, 0, -1.0]), None)
            if plane is None:
                continue
            n = plane[0]
            if float(n @ (np.mean(p.poly, axis=0) - a)) > 0:
                n = -n
            p.sides[k] = _square_if_steep(Side("cut", (n, float(n @ a)), "cut"), p.normal, p.poly[0])
            p.partial = p.partial or False
    warnings += slivers
    W = 2 * (X - pw_ - ct_)
    H = Z - hh_
    if abs(X - X0) > 1e-9 or abs(Z - Z0) > 1e-9:
        warnings.append(f"door fitted to the panel corners: clear opening {W * 1000:.0f} x {H * 1000:.0f} mm "
                        f"(asked for {spec.door_w_m * 1000:.0f} x {spec.door_h_m * 1000:.0f})")

    # The surface the cards meet: every outer face the planes x = +-X pass through.
    def trace(xp: float, zlo: float, zhi: float) -> list[tuple[float, float]]:
        segs = []
        for p in panels:
            P = p.poly
            for i in range(len(P)):
                a, b = P[i], P[(i + 1) % len(P)]
                if (a[0] - xp) * (b[0] - xp) < 0:
                    t = (xp - a[0]) / (b[0] - a[0])
                    q = a + t * (b - a)
                    if q[1] < 0:
                        segs.append((float(q[2]), float(q[1])))
        segs.sort()
        return [(z, y) for z, y in segs if zlo - 1e-9 <= z <= zhi + 1e-9]

    # below the lowest panel corner the skin is the base board's outer face
    loop = _base_loop(cut)
    base_pts = [V[v] for v in loop]

    def base_y(xp: float) -> float:
        best = None
        for i in range(len(base_pts)):
            a, b = base_pts[i], base_pts[(i + 1) % len(base_pts)]
            if (a[0] - xp) * (b[0] - xp) <= 0 and a[0] != b[0]:
                t = (xp - a[0]) / (b[0] - a[0])
                q = a + t * (b - a)
                if q[1] < 0:
                    best = (float(q[1]), float(q[2]))
        return best

    pieces: list[Piece] = []
    sides_info = {}
    y_post = -1e9
    traces = {}
    for sgn in (-1, 1):
        xp = sgn * X
        yb, zb = base_y(xp)
        tr = [(0.0, yb), (zb, yb)] + [(z, y) for z, y in trace(xp, zb, Z) if z > zb + 1e-6]
        # the skin at the top of the head, by interpolation
        tr = [(z, y) for z, y in tr if z <= Z]
        above = sorted(trace(xp, Z, Z + 2.0))
        if above:
            z0, y0 = tr[-1]
            z1, y1 = above[0]
            yz = y0 + (y1 - y0) * (Z - z0) / (z1 - z0) if z1 > z0 else y0
            tr.append((Z, yz))
        traces[sgn] = tr
        y_post = max(y_post, max(y for _, y in tr))
    pd, pw = D("post_d_m"), D("post_w_m")
    for sgn in (-1, 1):
        tr = traces[sgn]
        x_out = sgn * X
        x_in = sgn * (X - D("card_t_m"))
        # the card: from the skin back to the post's back face
        back = y_post + pd
        poly2d = [(y, z) for z, y in tr] + [(back, Z), (back, 0.0)]
        card_poly = [np.array([x_in, y, z]) for y, z in poly2d]
        card = S.prism(card_poly, (sgn, 0, 0), D("card_t_m"))
        info = {"outline_yz": poly2d, "x": x_in, "depth_bottom_m": back - tr[0][1], "depth_top_m": back - tr[-1][1],
                "height_m": Z}
        pieces.append(Piece(f"door-card-{'LR'[sgn > 0]}", f"Door card ({'left' if sgn < 0 else 'right'})", "door", "card",
                            card, info, step=2, group="door", explode=(sgn * 0.8, -0.4, 0)))
        sides_info[sgn] = info
        # the post, inside the card
        x0, x1 = sorted((sgn * W / 2, sgn * (W / 2 + pw)))
        post = S.box(((x0 + x1) / 2, y_post + pd / 2, H / 2), (x1 - x0, pd, H))
        pieces.append(Piece(f"door-post-{'LR'[sgn > 0]}", f"Door post ({'left' if sgn < 0 else 'right'})", "door", "pine",
                            post, {"length_m": H, "section": "2x4"}, step=2, group="door", explode=(sgn * 0.6, -0.6, 0)))
    # the head: from post to post across the top, its front following the skin
    y_head_front = min(traces[-1][-1][1], traces[1][-1][1])
    head = S.box((0, (y_head_front + y_post + pd) / 2, H + D("head_h_m") / 2),
                 (2 * X, (y_post + pd) - y_head_front, D("head_h_m")))
    pieces.append(Piece("door-head", "Door head", "door", "pine", head,
                        {"length_m": 2 * X, "depth_m": (y_post + pd) - y_head_front, "section": "2x4 on edge, ripped to the skin"},
                        step=2, group="door", explode=(0, -0.6, 0.5)))
    # the leaf
    g = D("door_gap_m")
    leaf_w, leaf_h = W - 2 * g, H - 2 * g
    pieces += _door_leaf(np.array([-W / 2 + g, y_post, g]), leaf_w, leaf_h)
    door = {"X": X, "Z": Z, "W": W, "H": H, "y_post": y_post, "pieces": pieces, "cards": sides_info,
            "leaf_w": leaf_w, "leaf_h": leaf_h}
    return door, out, warnings




#: A partial panel's cut stick is bevelled to lie flat on its card or the head up to this
#: angle; past it the bevel would eat most of the stick, so the stick is cut square and the
#: head (or card) gets a bevelled cap to meet it instead.
MAX_CUT_BEVEL = 15.0


def _square_if_steep(sd: "Side", normal, on_panel) -> "Side":
    if sd.kind != "cut":
        return sd
    n, c = np.asarray(sd.plane[0], float), float(sd.plane[1])
    # the stick's rip bevel against this plane is the plane's tilt off the panel's normal
    tilt = math.degrees(math.asin(min(1.0, abs(float(n @ normal)))))
    if tilt <= MAX_CUT_BEVEL:
        return sd
    # square instead: the plane through the same line that contains the panel's normal
    k = float(n @ normal)
    m = n - k * normal
    L = float(np.linalg.norm(m))
    c_panel = float(normal @ on_panel)
    return Side("cut", (m / L, (c - k * c_panel) / L), "square")


def _door_clip(panels, X, Z, min_thick):
    out, slivers = [], []
    for p in panels:
        if np.mean([q[1] for q in p.poly]) >= 0:
            out.append(p)
            continue
        probe, ps = list(p.poly), list(p.sides)
        for n, c in (((1, 0, 0), X), ((-1, 0, 0), X), ((0, 0, 1), Z)):
            probe, ps = S.clip(probe, ps, n, c, None)
            if len(probe) < 3:
                break
        if len(probe) < 3 or S.poly_area(probe) < 1e-6:
            out.append(p)
            continue
        cuts = [
            ("L", [((1, 0, 0), -X)]),
            ("R", [((-1, 0, 0), -X)]),
            ("T", [((1, 0, 0), X), ((-1, 0, 0), X), ((0, 0, -1), -Z)]),
        ]
        for tag, hs in cuts:
            poly, sides = list(p.poly), list(p.sides)
            for n, c in hs:
                n = np.array(n, float)
                poly, sides = S.clip(poly, sides, n, c, Side("cut", (n, c), "cut"))
                if len(poly) < 3:
                    break
            sides = [_square_if_steep(sd, p.normal, p.poly[0]) for sd in sides]
            if len(poly) < 3 or S.poly_area(poly) < 1e-5:
                continue
            th = S.poly_thickness(poly)
            if th < min_thick:
                slivers.append(f"{p.id}{tag}: a {th * 1000:.0f} mm sliver is left beside the door; the card covers it instead of a frame")
                continue
            out.append(Panel(f"{p.id}{tag}", p.face, p.kind, "partial", poly, sides, p.normal, partial=True, level=p.level))
    return out, slivers


def _door_leaf(origin, wd, ht) -> list[Piece]:
    """A ledged and framed leaf with a glazed upper half, hinged on its left (-x) side."""
    t = D("leaf_t_m")
    st = 0.09
    o = np.asarray(origin, float)
    parts = []
    def bx(name, x0, z0, x1, z1, mat="door", y0=0.0, y1=t):
        m = S.box((o[0] + (x0 + x1) / 2, o[1] + (y0 + y1) / 2, o[2] + (z0 + z1) / 2), (x1 - x0, y1 - y0, z1 - z0))
        parts.append(Piece(f"door-leaf-{name}", f"Door leaf {name}", "door", mat, m, {}, step=20, group="door-leaf",
                           explode=(0, -1.2, 0)))
    bx("hinge-stile", 0, 0, st, ht)
    bx("latch-stile", wd - st, 0, wd, ht)
    bx("bottom-rail", st, 0, wd - st, 0.18)
    bx("lock-rail", st, ht * 0.48, wd - st, ht * 0.48 + st)
    bx("top-rail", st, ht - st, wd - st, ht)
    bx("panel", st, 0.18, wd - st, ht * 0.48, y0=t * 0.35, y1=t * 0.65)
    bx("lite", st, ht * 0.48 + st, wd - st, ht - st, mat="glass", y0=t * 0.45, y1=t * 0.55)
    m = S.cylinder(o + [wd - 0.07, -0.02, ht * 0.45], o + [wd - 0.07, -0.08, ht * 0.45], 0.012, 10)
    parts.append(Piece("door-leaf-handle", "Door handle", "door", "steel", m, {}, step=20, group="door-leaf", explode=(0, -1.2, 0)))
    for z in (0.2, ht - 0.25):
        m = S.box(o + [0.0, -0.004, z], (0.02, 0.012, 0.1))
        parts.append(Piece(f"door-hinge-{z:.1f}", "Hinge", "door", "steel", m, {}, step=20, group="door-leaf", explode=(0, -1.2, 0)))
    return parts


# ----------------------------------------------------------------------
# Base sections, deck, porch
# ----------------------------------------------------------------------

def _base_sections(spec: Spec, cut, V, door) -> list[Piece]:
    loop = _base_loop(cut)
    pts = [V[v] for v in loop]
    n = len(pts)
    # wind the loop counter-clockwise seen from above
    area = sum(pts[i][0] * pts[(i + 1) % n][1] - pts[(i + 1) % n][0] * pts[i][1] for i in range(n))
    if area < 0:
        pts = pts[::-1]
    out = []
    bt, pt_, pw = D("base_t_m"), D("plate_t_m"), D("plate_w_m")
    up = np.array([0, 0, 1.0])
    for i in range(n):
        a, b = pts[i], pts[(i + 1) % n]
        prev, nxt = pts[i - 1], pts[(i + 2) % n]
        e = b - a
        eh = unit(np.array([e[0], e[1], 0]))
        inward = np.cross(up, eh)                     # left of a counter-clockwise loop: inside
        outer = (-inward, float(-inward @ a))         # outside face through the base line
        inner_board = (inward, float(inward @ a + bt))
        inner_plate = (inward, float(inward @ a + pw))
        # ends: vertical planes bisecting the corners
        def bis(p, q, r):
            d1 = unit(np.array([*(q - p)[:2], 0]))
            d2 = unit(np.array([*(r - q)[:2], 0]))
            nrm = unit(d1 + d2)
            return nrm
        n_b = bis(a, b, nxt)       # at b
        n_a = bis(prev, a, b)      # at a
        end_b = (n_b, float(n_b @ b))
        end_a = (-n_a, float(-n_a @ a))
        top_n = unit(np.cross(e, inward))
        if top_n[2] < 0:
            top_n = -top_n
        top = (top_n, float(top_n @ a))
        extra = []
        if door:
            # a base board that runs into the door opening stops at the card's face
            X = door["X"]
            mid = (a + b) / 2
            if mid[1] < 0 and (min(a[0], b[0]) < X and max(a[0], b[0]) > -X):
                if mid[0] > 0:
                    extra = [((-1.0, 0, 0), -X)]
                else:
                    extra = [((1.0, 0, 0), -X)]
                if abs(mid[0]) < X:
                    continue
        rise = abs(a[2] - b[2])
        name = f"B{i + 1:02d}"
        board = S.solid([outer, inner_board, end_a, end_b, top, ((0, 0, -1.0), -pt_)] + extra)
        plate = S.solid([outer, inner_plate, end_a, end_b, ((0, 0, 1.0), pt_), ((0, 0, -1.0), 0.0)] + extra)
        info = {"tapered": rise > 1e-6, "low_m": min(a[2], b[2]) - pt_, "high_m": max(a[2], b[2]) - pt_,
                "length_m": float(np.linalg.norm((b - a)[:2])), "rise_m": rise,
                "end_mitre": math.degrees(math.acos(min(1, abs(float(n_b @ eh))))) if True else 0}
        mx = (a + b) / 2
        ex = tuple(unit(np.array([mx[0], mx[1], 0])) * 0.8)
        if len(board.verts):
            out.append(Piece(f"{name}-board", f"Base section {name}", "base", "base", board, info, step=1, group=name, explode=ex))
        if len(plate.verts):
            out.append(Piece(f"{name}-plate", f"Bottom plate {name}", "base", "plate", plate, info, step=1, group=name, explode=ex))
    return out


def _deck(spec: Spec, floor_poly, door) -> list[Piece]:
    """A deck the shape of the base, one joist to each base corner, on piers; a porch at the door."""
    out = []
    pts = [np.array([p[0], p[1], 0.0]) for p in floor_poly]
    n = len(pts)
    area = sum(pts[i][0] * pts[(i + 1) % n][1] - pts[(i + 1) % n][0] * pts[i][1] for i in range(n))
    if area < 0:
        pts = pts[::-1]
    grow = 0.06
    rim = [p + unit(np.array([p[0], p[1], 0])) * grow for p in pts]
    top_t = 1.0 * IN
    jd, jw = D("joist_d_m"), D("joist_w_m")
    deck_h = D("deck_h_m")
    floor = S.prism([p - [0, 0, top_t] for p in rim], (0, 0, 1), top_t)
    out.append(Piece("deck-floor", "Floor decking", "deck", "deck", floor, {"area_m2": S.poly_area(rim)}, step=0, group="deck"))
    # rim boards and joists
    for i in range(n):
        a, b = rim[i], rim[(i + 1) % n]
        m = S.box(((a + b) / 2 - [0, 0, top_t + jd / 2]), (float(np.linalg.norm(b - a)), jw, jd),
                  math.degrees(math.atan2(*(b - a)[1::-1])))
        out.append(Piece(f"deck-rim-{i}", "Deck rim board", "deck", "joist", m, {}, step=0, group="deck", explode=(0, 0, -0.6)))
        j = S.box((a / 2 - [0, 0, top_t + jd / 2]), (float(np.linalg.norm(a[:2])), jw, jd * 0.98),
                  math.degrees(math.atan2(a[1], a[0])))
        out.append(Piece(f"deck-joist-{i}", "Deck joist", "deck", "joist", j, {}, step=0, group="deck", explode=(0, 0, -0.6)))
    # piers under the corners and the middle
    for i, p in enumerate(rim[::3] + [np.zeros(3)]):
        q = p * 0.92
        m = S.cylinder(q - [0, 0, deck_h], q - [0, 0, top_t + jd], 0.13, 16)
        out.append(Piece(f"pier-{i}", "Pier", "deck", "concrete", m, {}, step=0, group="deck", explode=(0, 0, -1.0)))
    if spec.porch and door:
        depth = D("deck_front_m")
        y0 = min(p[1] for p in rim) + 0.2
        width = D("porch_w_m")
        porch = S.box((0, y0 - depth / 2, -top_t / 2), (width, depth, top_t))
        out.append(Piece("porch", "Porch", "deck", "deck", porch, {}, step=0, group="porch"))
        for i in range(int(width / D("deck_board_m"))):
            x = -width / 2 + D("deck_board_m") * (i + 0.5)
            line = S.box((x, y0 - depth / 2, 0.0005), (0.004, depth, 0.001))
            out.append(Piece(f"porch-gap-{i}", "Deck gap", "deck", "joist", line, {}, step=0, group="porch"))
        for k, (dx, dz) in enumerate(((0.0, -0.15), (0.28, -0.3))):
            st = S.box((0, y0 - depth - 0.14 - dx, dz - 0.02), (1.4, 0.3, 0.04))
            out.append(Piece(f"porch-step-{k}", "Step", "deck", "deck", st, {}, step=0, group="porch"))
        for sx in (-1, 1):
            for yy in (y0 - 0.15, y0 - depth + 0.1):
                m = S.cylinder((sx * (width / 2 - 0.1), yy, -deck_h), (sx * (width / 2 - 0.1), yy, -top_t), 0.1, 14)
                out.append(Piece(f"porch-pier-{sx}-{yy:.1f}", "Pier", "deck", "concrete", m, {}, step=0, group="porch"))
    # deck board lines on the floor
    r = max(np.linalg.norm(p[:2]) for p in rim)
    for i in range(int(2 * r / D("deck_board_m"))):
        y = -r + D("deck_board_m") * (i + 0.5)
        xs = []
        for k in range(n):
            a, b = rim[k], rim[(k + 1) % n]
            if (a[1] - y) * (b[1] - y) < 0:
                t = (y - a[1]) / (b[1] - a[1])
                xs.append(a[0] + t * (b[0] - a[0]))
        if len(xs) >= 2:
            x0, x1 = min(xs), max(xs)
            m = S.box(((x0 + x1) / 2, y, 0.0005), (x1 - x0, 0.004, 0.001))
            out.append(Piece(f"deck-gap-{i}", "Deck gap", "deck", "joist", m, {}, step=0, group="deck"))
    return out


def _window_trim(p: Panel, t: float) -> Piece:
    """A painted frame round a window's glazing: the opening sash."""
    c = np.mean(p.poly, axis=0)
    inner = [c + (q - c) * 0.80 for q in p.poly]
    parts = []
    k = len(p.poly)
    for i in range(k):
        quad = [p.poly[i], p.poly[(i + 1) % k], inner[(i + 1) % k], inner[i]]
        parts.append(S.prism([q + p.normal * (0.0015 + t) for q in quad], p.normal, 0.02))
    return Piece(f"{p.id}-trim", f"Window frame {p.id}", "glass" if False else "skin", "trim", S.merge(parts), {},
                 step=99, group=p.id, explode=tuple(p.normal * 1.6))


def _stove(spec, panels, base_top) -> list[Piece]:
    hit = next((p for p in panels if p.pipe), None)
    y = 0.42 * spec.diameter_m / 2
    out = []
    out.append(Piece("hearth", "Hearth", "furniture", "hearth", S.box((0, y, 0.025), (0.9, 0.8, 0.05)), {}, step=30, group="stove"))
    out.append(Piece("stove", "Wood stove", "furniture", "steel", S.box((0, y, 0.05 + 0.33), (0.45, 0.4, 0.66)), {}, step=30, group="stove"))
    out.append(Piece("stove-glass", "Stove window", "furniture", "lamp", S.box((0, y - 0.201, 0.38), (0.26, 0.004, 0.18)), {}, step=30, group="stove"))
    top = 0.05 + 0.66
    if hit is not None:
        c = np.mean(hit.poly, axis=0)
        n = hit.normal
        # where the vertical line meets the panel's plane
        z_hit = float((n @ c - n[0] * 0 - n[1] * y) / n[2])
        end = z_hit + 0.6
    else:
        end = top + 2.0
    out.append(Piece("stove-pipe", "Stove pipe", "furniture", "steel", S.cylinder((0, y, top), (0, y, end), 0.075, 18), {"pipe_panel": hit.id if hit else None}, step=30, group="stove"))
    out.append(Piece("stove-cap", "Rain cap", "furniture", "steel", S.cylinder((0, y, end), (0, y, end + 0.12), 0.16, 18, r1=0.02), {}, step=30, group="stove"))
    return out


def _furniture(spec, floor_poly, door) -> list[Piece]:
    """A one-room cabin: bed, sofa, table, kitchen, shelves, rug, plants and a pendant light."""
    r = spec.diameter_m / 2
    k = r / 2.44                    # laid out for the reference dome; scaled to any other
    out = []
    def add(name, mesh, mat, group="room"):
        out.append(Piece(f"room-{len(out)}", name, "furniture", mat, mesh, {}, step=30, group=group))
    # bed against the back-left wall
    bx, by, yaw = -1.05 * k, 0.75 * k, 35
    add("Bed frame", S.box((bx, by, 0.17), (1.55, 2.05, 0.34), yaw), "pine")
    add("Mattress", S.box((bx, by, 0.42), (1.5, 2.0, 0.18), yaw), "fabric")
    a = math.radians(yaw)
    fwd = np.array([-math.sin(a), math.cos(a), 0])
    add("Quilt", S.box(np.array([bx, by, 0.52]) - fwd * 0.25, (1.54, 1.3, 0.04), yaw), "fabric2")
    for s in (-0.4, 0.4):
        side = np.array([math.cos(a), math.sin(a), 0])
        add("Pillow", S.box(np.array([bx, by, 0.56]) + fwd * 0.75 + side * s, (0.6, 0.35, 0.12), yaw), "fabric")
    # sofa on the right
    sx, sy, syaw = 1.25 * k, 0.45 * k, 100
    add("Sofa", S.box((sx, sy, 0.22), (1.9, 0.85, 0.44), syaw), "fabric2")
    a = math.radians(syaw)
    back = np.array([math.sin(a), -math.cos(a), 0]) * -1
    add("Sofa back", S.box(np.array([sx, sy, 0.6]) + back * 0.33, (1.9, 0.2, 0.4), syaw), "fabric2")
    # round table and two stools by the door
    tx, ty = 0.95 * k, -0.85 * k
    add("Table", S.cylinder((tx, ty, 0.72), (tx, ty, 0.75), 0.42, 28), "pine")
    add("Table leg", S.cylinder((tx, ty, 0.0), (tx, ty, 0.72), 0.04, 12), "steel")
    for ang in (30, 210):
        q = np.array([tx, ty, 0]) + 0.6 * np.array([math.cos(math.radians(ang)), math.sin(math.radians(ang)), 0])
        add("Stool", S.cylinder(q + [0, 0, 0.44], q + [0, 0, 0.48], 0.18, 20), "pine")
        add("Stool leg", S.cylinder(q, q + [0, 0, 0.44], 0.025, 10), "steel")
    # kitchen counter on the left of the door
    kx, ky, kyaw = -1.45 * k, -0.55 * k, 75
    add("Counter", S.box((kx, ky, 0.45), (1.6, 0.6, 0.9), kyaw), "trim")
    add("Worktop", S.box((kx, ky, 0.92), (1.65, 0.65, 0.04), kyaw), "pine")
    add("Sink", S.box((kx, ky, 0.93), (0.45, 0.35, 0.03), kyaw), "steel")
    # shelves behind the sofa
    add("Shelf", S.box((1.55 * k, 1.1 * k, 1.2), (0.9, 0.28, 0.03), 125), "pine")
    add("Shelf", S.box((1.55 * k, 1.1 * k, 1.55), (0.9, 0.28, 0.03), 125), "pine")
    for i in range(5):
        add("Books", S.box((1.55 * k - 0.25 + i * 0.1, 1.1 * k + 0.1 - i * 0.05, 1.33), (0.06, 0.2, 0.22), 125), ("rug", "fabric2", "trim", "leaf", "door")[i])
    # rug
    add("Rug", S.cylinder((0.1, -0.05, 0.002), (0.1, -0.05, 0.012), 1.05 * k, 40), "rug")
    # plants
    for (x, y, h) in ((-0.55 * k, -1.45 * k, 0.9), (1.75 * k, -0.2 * k, 1.2)):
        add("Pot", S.cylinder((x, y, 0), (x, y, 0.32), 0.16, 18, r1=0.2), "pot")
        add("Plant", S.sphere_mesh((x, y, 0.32 + h * 0.4), h * 0.32, 12), "leaf")
    # pendant light from the apex
    add("Pendant cord", S.cylinder((0.0, -0.05, 2.0), (0.0, -0.05, 3.2), 0.004, 6), "steel")
    add("Pendant", S.cylinder((0.0, -0.05, 1.82), (0.0, -0.05, 2.0), 0.2, 24, r1=0.03), "lamp")
    return out


def _person(at, yaw: float) -> list[Piece]:
    """A plain standing figure, 1.75 m tall, facing ``yaw`` degrees, for scale."""
    h = D("person_m")
    k = h / 1.75
    p = np.asarray(at, float)
    a = math.radians(yaw)
    side = np.array([math.cos(a), math.sin(a), 0])
    fwd = np.array([-math.sin(a), math.cos(a), 0])
    out = []
    def add(name, mesh, mat):
        out.append(Piece(f"person-{len(out)}", name, "person", mat, mesh, {}, step=40, group="person"))
    up = np.array([0, 0, 1.0])
    for sgn in (-1, 1):
        hip = p + side * 0.095 * k * sgn + up * 0.88 * k
        foot = p + side * 0.11 * k * sgn + up * 0.06 * k
        add("Leg", S.cylinder(foot, hip, 0.058 * k, 12, r1=0.075 * k), "denim")
        add("Shoe", S.box(p + side * 0.11 * k * sgn + fwd * 0.04 * k + up * 0.035 * k, (0.1 * k, 0.26 * k, 0.07 * k), yaw), "steel")
        sh = p + side * 0.215 * k * sgn + up * 1.40 * k
        el = p + side * 0.25 * k * sgn + up * 1.13 * k + fwd * 0.02 * k
        wr = p + side * 0.24 * k * sgn + up * 0.88 * k + fwd * 0.07 * k
        add("Upper arm", S.cylinder(sh, el, 0.048 * k, 10, r1=0.042 * k), "shirt")
        add("Forearm", S.cylinder(el, wr, 0.04 * k, 10, r1=0.034 * k), "skin_tone")
        add("Hand", S.sphere_mesh(wr - up * 0.05 * k, 0.045 * k, 10), "skin_tone")
    add("Hips", S.cylinder(p + up * 0.84 * k, p + up * 0.98 * k, 0.16 * k, 16, r1=0.155 * k), "denim")
    add("Torso", S.cylinder(p + up * 0.97 * k, p + up * 1.44 * k, 0.15 * k, 16, r1=0.19 * k), "shirt")
    add("Shoulders", S.sphere_mesh(p + up * 1.40 * k, 0.17 * k, 14), "shirt")
    add("Neck", S.cylinder(p + up * 1.44 * k, p + up * 1.53 * k, 0.05 * k, 10), "skin_tone")
    add("Head", S.sphere_mesh(p + up * 1.64 * k, 0.105 * k, 16), "skin_tone")
    add("Hair", S.sphere_mesh(p + up * 1.675 * k - fwd * 0.012 * k, 0.102 * k, 16), "hair")
    return out


def _site(spec) -> list[Piece]:
    r = spec.diameter_m / 2
    g = S.cylinder((0, 0, -D("deck_h_m") - 0.02), (0, 0, -D("deck_h_m")), r + 7.0, 48)
    gr = S.cylinder((0, 0, -D("deck_h_m") - 0.012), (0, 0, -D("deck_h_m") + 0.004), r + 0.9, 40)
    return [Piece("ground", "Ground", "site", "ground", g, {}, step=0, group="site"),
            Piece("gravel", "Gravel ring", "site", "gravel", gr, {}, step=0, group="site")]


# ----------------------------------------------------------------------
# The tables the plan set prints
# ----------------------------------------------------------------------

def section_groups(pdome: pm.PanelDome) -> list[tuple[str, list[int]]]:
    """Which faces go together into each pentagon and hexagon pre-assembly section.

    Same greedy order as ``panel_method.PanelDome.sections`` (pentagons first, then hexagons
    whose faces are still free); the self-test checks the counts agree."""
    sphere = pdome.sphere
    kept = set(pdome.cut.faces)
    around: dict[int, list[int]] = {}
    for i in kept:
        for v in sphere.faces[i]:
            around.setdefault(int(v), []).append(i)
    used: set[int] = set()
    out = []
    for v, fs in sorted(around.items(), key=lambda kv: sphere.valence[kv[0]]):
        need = int(sphere.valence[v])
        if len(fs) == need and not used.intersection(fs):
            out.append(("pentagon" if need == 5 else "hexagon", sorted(fs)))
            used.update(fs)
    return out


def _stick_rows(pieces: list[Piece]) -> list[dict]:
    """Every distinct stick: same length, same cuts, same bevel -> one row of the cut list."""
    rows: dict[tuple, dict] = {}
    for p in pieces:
        if p.tag != "frame":
            continue
        f = p.info
        key = (f["cls"] if f["cls"] != "partial" else f["panel"], round(f["long_m"], 4), round(f["head_mitre"], 1),
               round(f["head_bevel"], 1), round(f["tail_mitre"], 1), round(f["rip_deg"], 1), f["kind"])
        r = rows.setdefault(key, {**{k: f[k] for k in ("cls", "side", "kind", "long_m", "outline_m", "rip_deg", "head_mitre",
                                                          "head_bevel", "tail_mitre", "tail_bevel")}, "count": 0, "panels": set(), "sample": p.id, "ids": []})
        r["count"] += 1
        r["ids"].append(p.id)
        r["panels"].add(f["panel"])
    out = sorted(rows.values(), key=lambda r: (r["cls"] == "partial" or len(r["cls"]) > 2, r["cls"], -r["long_m"]))
    for i, r in enumerate(out, 1):
        r["mark"] = f"S{i}"
        r["panels"] = sorted(r["panels"])
    return out


def _boards_needed(lengths: list[float], board: float, kerf: float) -> int:
    """First-fit decreasing: how many boards the sticks come out of (each board ripped into two sticks)."""
    bins: list[float] = []
    for L in sorted(lengths, reverse=True):
        for i, used in enumerate(bins):
            if used + L + kerf <= board:
                bins[i] += L + kerf
                break
        else:
            bins.append(L + kerf)
    return math.ceil(len(bins) / 2)


def nest_triangles(tris: list[tuple[str, float, float, float]], sheet_w: float, sheet_l: float, gap: float):
    """Lay panel outlines (name, base, left, right) on sheets: rows along the sheet's length,
    alternately point-up and point-down, each slid as close to the last as it will go.

    Returns a list of sheets, each a list of (name, [(x, y) x3]) in sheet metres."""
    sheets: list[list] = []
    rows: list[dict] = []           # open rows: {"sheet", "y", "h", "x", "last"}

    def shape(base, left, right, flip):
        x, y = pm.trammel_apex(base, left, right)
        pts = [(0.0, 0.0), (base, 0.0), (x, y)]
        if flip:
            pts = [(base - px, y - py) for px, py in pts]
        return pts

    def overlap(P, Q) -> bool:
        for poly in (P, Q):
            for i in range(3):
                a, b = poly[i], poly[(i + 1) % 3]
                nx, ny = b[1] - a[1], a[0] - b[0]
                pa = [nx * p[0] + ny * p[1] for p in P]
                qa = [nx * p[0] + ny * p[1] for p in Q]
                if max(pa) <= min(qa) + 1e-9 or max(qa) <= min(pa) + 1e-9:
                    return False
        return True

    def offset(pts, gap):
        cx = sum(p[0] for p in pts) / 3
        cy = sum(p[1] for p in pts) / 3
        out = []
        for p in pts:
            d = math.hypot(p[0] - cx, p[1] - cy)
            k = (d + gap * 2) / d
            out.append((cx + (p[0] - cx) * k, cy + (p[1] - cy) * k))
        return out

    for name, base, left, right in tris:
        h = pm.trammel_apex(base, left, right)[1]
        placed = False
        for row in rows:
            if abs(row["h"] - h) > 1e-6:
                continue
            flip = not row["flip"]
            pts = shape(base, left, right, flip)
            # slide from the last triangle's left edge until it clears it
            last = offset(row["last"], gap / 2)
            lo, hi = row["last_x"], row["last_x"] + 2 * base
            for _ in range(24):
                mid = (lo + hi) / 2
                if overlap(offset([(px + mid, py) for px, py in pts], gap / 2), last):
                    lo = mid
                else:
                    hi = mid
            x = hi
            cand = [(px + x, py) for px, py in pts]
            if max(p[0] for p in cand) > sheet_l:
                continue
            sheets[row["sheet"]].append((name, [(px, py + row["y"]) for px, py in cand]))
            row.update(last=cand, last_x=x, flip=flip)
            placed = True
            break
        if placed:
            continue
        # a new row: on the newest sheet if it has room, else a new sheet
        y = 0.0
        if sheets:
            used = [r for r in rows if r["sheet"] == len(sheets) - 1]
            y = max((r["y"] + r["h"] + gap for r in used), default=0.0)
        if not sheets or y + h > sheet_w:
            sheets.append([])
            y = 0.0
        pts = shape(base, left, right, False)
        rows.append({"sheet": len(sheets) - 1, "y": y, "h": h, "flip": False, "last": pts, "last_x": 0.0})
        sheets[-1].append((name, [(px, py + y) for px, py in pts]))
    return sheets


def _tables(spec, pdome, panels, pieces, door, cut, V, warnings, ring_count, base_top) -> dict:
    classes = pdome.panel_classes()
    names = {pc.key: n for n, pc in zip("ABCDEFGHIJKLMNOP", classes)}
    whole = [p for p in panels if not p.partial]
    partial = [p for p in panels if p.partial]
    sticks = _stick_rows(pieces)
    frame = [p for p in pieces if p.tag == "frame"]
    trim = D("trim_m")
    boards = _boards_needed([p.info["long_m"] + trim for p in frame], D("board_l_m"), D("kerf_m"))
    seam_m = 0.0
    seen = set()
    for p in whole + partial:
        for k, s in enumerate(p.sides):
            if s.kind == "seam":
                key = tuple(sorted((p.face, s.other)))
                L = float(np.linalg.norm(p.poly[(k + 1) % len(p.poly)] - p.poly[k]))
                if key not in seen:
                    seen.add(key)
                    seam_m += L
    skin_panels = [p for p in panels if not (p.window or p.skylight)]
    nest = nest_triangles(
        [(p.cls, *sorted_sides(p)) for p in skin_panels if not p.partial], D("sheet_w_m"), D("sheet_l_m"), D("kerf_m") * 2)
    partial_area = sum(S.poly_area(p.poly) for p in partial)
    partial_sheets = math.ceil(partial_area * (1 + D("waste")) / (D("sheet_w_m") * D("sheet_l_m")))
    corners = sum(len(p.poly) for p in panels)
    perim = sum(sum(float(np.linalg.norm(p.poly[(k + 1) % len(p.poly)] - p.poly[k])) for k in range(len(p.poly))) for p in panels)
    base = [p for p in pieces if p.tag == "base" and p.id.endswith("board")]
    base_m = sum(p.info["length_m"] for p in base)
    deck_area = next((p.info["area_m2"] for p in pieces if p.id == "deck-floor"), 0.0)
    groups = section_groups(pdome)
    lo, hi = pdome.bevel_spread()
    t = {
        "title": spec.title,
        "frequency": spec.frequency, "cut": spec.cut,
        "R": pdome.radius_m, "diameter_m": spec.diameter_m, "height_m": float(V[:, 2].max()),
        "inside_height_m": float(V[:, 2].max()) - spec.stick_d_m,
        "floor_m2": pdome.floor_area_m2, "base_edges": len(cut.base), "tapered": cut.tapered_count, "level": cut.level_count,
        "taper_m": pdome.max_taper_m, "base_top_m": base_top,
        "chords": {L: pdome.chord_m(L) for L in "ABCDEFGH"[:len(cut.sphere.chord_classes)]},
        "classes": [{"name": names[pc.key], "key": pc.key, "kind": pc.kind, "letters": pc.letters, "sides_m": pc.sides,
                     "angles": pc.angles, "bevels": pc.bevels, "count": pc.count,
                     "built": sum(1 for p in whole if p.cls == names[pc.key]),
                     "height_m": pc.height, "area_m2": pc.area, "trammel": pm.trammel_apex(*pc.sides)} for pc in classes],
        "panels": len(cut.faces), "whole": len(whole), "partial": len(partial),
        "partials": [{"id": p.id, "sides_m": [float(np.linalg.norm(p.poly[(k + 1) % len(p.poly)] - p.poly[k])) for k in range(len(p.poly))],
                      "kinds": [s.kind for s in p.sides], "area_m2": S.poly_area(p.poly), "poly": [q.tolist() for q in p.poly],
                      "normal": p.normal.tolist()} for p in partial],
        "windows": sum(p.window for p in panels), "skylights": sum(p.skylight for p in panels),
        "sticks": sticks, "stick_count": len(frame), "stick_m": sum(p.info["long_m"] for p in frame),
        "boards": boards, "rings": ring_count,
        "bevel_lo": lo, "bevel_hi": hi, "folds": pdome.edge_folds(),
        "sections": [(k, len(fs)) for k, fs in groups], "section_groups": groups,
        "sections_counts": pdome.sections(),
        "seam_m": seam_m, "corners": corners,
        "screws_corner": corners * int(D("screws_per_corner")),
        "screws_seam": math.ceil(seam_m / D("seam_screw_m")) * 2,
        "staples": math.ceil(perim / D("staple_m")),
        "tape_m": seam_m * (1 + D("waste")),
        "sheets": len(nest) + partial_sheets, "nest": nest, "partial_sheets": partial_sheets,
        "skin_m2": sum(S.poly_area(p.poly) for p in skin_panels),
        "glass_m2": sum(S.poly_area(p.poly) for p in panels if p.window or p.skylight),
        "base_sections": [{"id": p.group, **{k: p.info[k] for k in ("tapered", "low_m", "high_m", "length_m", "rise_m", "end_mitre")}}
                          for p in base],
        "base_m": base_m, "deck_m2": deck_area,
        "base_mitre": 180.0 / len(cut.base),
        "door": None if not door else {k: door[k] for k in ("X", "Z", "W", "H", "y_post", "leaf_w", "leaf_h")} | {"cards": door["cards"]},
        "warnings": warnings,
    }
    return t


def sorted_sides(p: Panel) -> tuple[float, float, float]:
    """A whole panel's (base, left, right) as its class draws it: the odd side as the base."""
    L = [float(np.linalg.norm(p.poly[(k + 1) % 3] - p.poly[k])) for k in range(3)]
    lt = [s.letter for s in p.sides]
    counts = {x: lt.count(x) for x in lt}
    odd = [i for i, x in enumerate(lt) if counts[x] == 1]
    k0 = odd[0] if len(odd) == 1 else max(range(3), key=lambda i: L[i])
    return L[k0], L[(k0 + 1) % 3], L[(k0 + 2) % 3]


# ----------------------------------------------------------------------
# Self-test: the solids agree with panel_method's own figures
# ----------------------------------------------------------------------

def validate(spec: Spec | None = None) -> list[str]:
    m = build(spec or Spec())
    t = m.tables
    pd = m.pdome
    checks = []
    assert sum(c["count"] for c in t["classes"]) == t["panels"]
    assert t["sections_counts"][0] == sum(1 for k, _ in t["sections"] if k == "pentagon")
    assert t["sections_counts"][1] == sum(1 for k, _ in t["sections"] if k == "hexagon")
    checks.append(f"sections {t['sections_counts']} agree with panel_method")
    by_cls = {c["name"]: c for c in t["classes"]}
    n = 0
    for p in m.pieces:
        if p.tag != "frame" or p.info["cls"] == "partial":
            continue
        f = p.info
        panel = next(q for q in m.panels if q.id == f["panel"])
        k = f["k"]
        # the tail is the initial mitre: square bevel, 90 - corner angle off square
        nn = len(panel.poly)
        e1 = unit(panel.poly[(k + 1) % nn] - panel.poly[k])
        e2 = unit(panel.poly[(k + 2) % nn] - panel.poly[(k + 1) % nn])
        phi = math.degrees(math.acos(float(np.clip(-e1 @ e2, -1, 1))))
        assert abs(f["tail_bevel"]) < 1e-6, f
        assert abs(f["tail_mitre"] - (90 - phi)) < 1e-6, (f, phi)
        # the length along the outline is panel_method's pinwheel figure
        side = float(np.linalg.norm(panel.poly[(k + 1) % nn] - panel.poly[k]))
        assert abs(f["outline_m"] - (side - m.spec.stick_w_m / math.sin(math.radians(phi)))) < 1e-6
        # the rip bevel on a seam is half the fold between the two panels
        other = next((q for q in m.panels if q.face == panel.sides[k].other), None) if f["kind"] == "seam" else None
        if other is not None:
            fold = math.degrees(math.acos(float(np.clip(panel.normal @ other.normal, -1, 1))))
            assert abs(f["rip_deg"] - fold / 2) < 1e-6
            lo, hi = pd.edge_folds()[panel.sides[k].letter]
            assert lo / 2 - 1e-6 <= f["rip_deg"] <= hi / 2 + 1e-6
        n += 1
    checks.append(f"{n} whole-panel sticks: tail mitres, outline lengths and rip bevels agree with panel_method")
    for c in t["classes"]:
        assert abs(sum(c["angles"]) - 180) < 1e-9
    vol = sum(S.volume(p.mesh) for p in m.pieces if p.tag == "frame")
    expect = t["stick_m"] * m.spec.stick_w_m * m.spec.stick_d_m
    assert 0.6 * expect < vol < 1.2 * expect, (vol, expect)
    checks.append(f"stick timber {vol * 1000:.1f} L, against {expect * 1000:.1f} L from length x section")
    return checks


if __name__ == "__main__":
    for line in validate():
        print(line)
    m = build()
    t = m.tables
    print(t["title"], len(m.pieces), "pieces;", t["whole"], "whole +", t["partial"], "partial panels;", t["stick_count"], "sticks;",
          len(t["sticks"]), "distinct;", t["boards"], "boards;", t["sheets"], "sheets")
    for w in t["warnings"]:
        print("warning:", w)
