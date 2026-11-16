"""Every kind of dome Dome Sketch draws, behind one shape.

A kind is a solver that returns a :class:`model.Model`: pieces (solids with a tag, a material,
a group and the build step they go up on) and tables. Besides its own tables, every kind fills
the five the page reads for any dome:

* ``summary``  -- [label, text] rows for the side panel;
* ``cards``    -- the visual cut list: one card per cut family, with a 2-D drawing to scale;
* ``sheets``   -- plate or panel nesting, sheet by sheet;
* ``steps``    -- the build, step by step: what to do, with what, how to check it, and which
                  pieces it adds (``mode: add``) or is about (``mode: prep``);
* ``declared`` -- every input the geometry cannot supply, with its reason.

Numbers inside text are unit tokens -- ``{m:1.2345}``, ``{m2:..}``, ``{L:..}`` (litres),
``{kg:..}``, ``{kPa:..}``, ``{deg:..}`` -- so the page shows them in metres, feet and inches,
or inches, whichever the viewer picked. A figure is never typed into prose: it is formatted
from the value the solver returned.

The kinds:

========  ===========================================  ==============================
kind      what                                          solver
========  ===========================================  ==============================
wedge     the raw-wedge dome (the flagship)             wedge_builder.design + the
                                                        dihedral raw-wedge solver
zome      the wedge-framed zome                         wedge_zome.geometry
panel     framed-panel 2V/3V/4V domes                   sketch_claude.model
stove     an all-steel geodesic wood stove              sketch_claude.metal
tank      an all-steel geodesic water tank              sketch_claude.metal
========  ===========================================  ==============================
"""

from __future__ import annotations

import base64
import math
from dataclasses import asdict, fields
from typing import Callable

import numpy as np

from two_v_demo import panel_method as pm

from . import model as M
from . import solids as S

IN = M.IN
FT = M.FT


# ----------------------------------------------------------------------
# Unit tokens: numbers in text, formatted by the page in the viewer's units
# ----------------------------------------------------------------------

def _tok(kind: str, v: float) -> str:
    return "{%s:%.6g}" % (kind, float(v))


def m(v: float) -> str:
    """A length in metres."""
    return _tok("m", v)


def m2(v: float) -> str:
    """An area in square metres."""
    return _tok("m2", v)


def litres(v: float) -> str:
    """A volume in litres."""
    return _tok("L", v)


def kg(v: float) -> str:
    return _tok("kg", v)


def kpa(v: float) -> str:
    return _tok("kPa", v)


def mpa(v: float) -> str:
    return _tok("MPa", v)


def deg(v: float) -> str:
    return _tok("deg", v)


def n(v: float) -> str:
    """A count, with thousands separators."""
    return f"{int(round(v)):,}"


# ----------------------------------------------------------------------
# Specs: plain frozen dataclasses, filled from the page's JSON
# ----------------------------------------------------------------------

def from_dict(cls, d: dict):
    """A spec dataclass from a JSON dict: unknown keys dropped, each value coerced to its field's type."""
    names = {f.name: f for f in fields(cls)}
    kw = {}
    for k, v in (d or {}).items():
        if k not in names or v is None:
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
    return cls(**kw)


def to_dict(spec) -> dict:
    return asdict(spec)


# ----------------------------------------------------------------------
# The build book: steps that add pieces, and steps about them
# ----------------------------------------------------------------------

class Book:
    """The build in order. ``add`` puts pieces up (and numbers their ``step``); ``prep`` is a
    step about pieces already counted (cutting, bevelling, welding out), shown on the
    finished model with those pieces lit."""

    def __init__(self):
        self.steps: list[dict] = []
        self.k = 0

    def prep(self, title: str, text: str, focus=(), tools=(), check: str = "", phase: str = "Prepare") -> None:
        self.steps.append({"mode": "prep", "title": title, "text": text, "tools": list(tools), "check": check,
                           "focus": [p.id if hasattr(p, "id") else p for p in focus], "show": self.k - 1, "phase": phase})

    def add(self, title: str, text: str, pieces, tools=(), check: str = "", phase: str = "Build") -> int:
        pieces = list(pieces)
        if not pieces:
            return self.k - 1
        for p in pieces:
            p.step = self.k
        self.steps.append({"mode": "add", "title": title, "text": text, "tools": list(tools), "check": check,
                           "focus": [p.id for p in pieces], "show": self.k, "phase": phase})
        self.k += 1
        return self.k - 1


def context(pieces) -> None:
    """Pieces that are not built (ground, a room, a person): always shown, never a step."""
    for p in pieces:
        p.step = -1


# ----------------------------------------------------------------------
# Cut cards: a 2-D drawing to scale, and the rows a builder reads
# ----------------------------------------------------------------------

def flat(points3d, normal=None, longest_on_x: bool = True) -> list[list[float]]:
    """A flat polygon's corners in its own plane, the longest edge on the x axis, the rest above it."""
    P = [np.asarray(p, float) for p in points3d]
    k = len(P)
    if normal is None:
        normal = np.cross(P[1] - P[0], P[2] - P[0])
    nrm = S.unit(normal)
    i0 = 0
    if longest_on_x:
        i0 = max(range(k), key=lambda i: float(np.linalg.norm(P[(i + 1) % k] - P[i])))
    a, b = P[i0], P[(i0 + 1) % k]
    u = S.unit(b - a)
    v = np.cross(nrm, u)
    pts = [[float((q - a) @ u), float((q - a) @ v)] for q in P[i0:] + P[:i0]]
    if sum(p[1] for p in pts) < 0:
        pts = [[x, -y] for x, y in pts]
    return pts


def corner_angles(pts) -> list[float]:
    k = len(pts)
    out = []
    for i in range(k):
        p, a, b = np.array(pts[i]), np.array(pts[i - 1]), np.array(pts[(i + 1) % k])
        u, v = a - p, b - p
        c = float(np.dot(u, v) / (np.linalg.norm(u) * np.linalg.norm(v)))
        out.append(math.degrees(math.acos(max(-1.0, min(1.0, c)))))
    return out


def drawing(poly, dims: bool = True, angles: bool = True, notes=(), holes=(), inner=None, lines=()) -> dict:
    """A card's picture: the outline (metres, any frame), a dimension on every edge, the angle
    at every corner, free notes at points and round holes."""
    poly = [[float(x), float(y)] for x, y in poly]
    k = len(poly)
    d = {"poly": poly, "dims": [], "angles": [], "notes": [dict(n) for n in notes], "holes": [dict(h) for h in holes]}
    if inner:
        d["inner"] = [[float(x), float(y)] for x, y in inner]
    if lines:
        d["lines"] = [[[float(a[0]), float(a[1])], [float(b[0]), float(b[1])]] for a, b in lines]
    if dims:
        for i in range(k):
            a, b = poly[i], poly[(i + 1) % k]
            L = math.hypot(b[0] - a[0], b[1] - a[1])
            if L > 1e-6:
                d["dims"].append({"a": a, "b": b, "m": L})
    if angles and k >= 3:
        for p, ang in zip(poly, corner_angles(poly)):
            d["angles"].append({"at": p, "deg": ang})
    return d


def card(mark: str, title: str, count: int, rows, draw: dict | None = None, ids=(), group: str = "", kind: str = "") -> dict:
    return {"mark": mark, "title": title, "count": int(count), "rows": [[str(a), str(b)] for a, b in rows],
            "draw": draw, "ids": list(ids), "group": group, "kind": kind}


def declared_rows(table: dict) -> list[dict]:
    """A DECLARED dict as the page's rows: name, value (as a unit token where it has one), kind, why."""
    out = []
    unit_tok = {"m": m, "m2": m2, "kg/m3": lambda v: f"{v:g} kg/m³", "MPa": mpa, "kPa": kpa, "deg": deg,
                "m/s2": lambda v: f"{v:g} m/s²", "": lambda v: f"{v:g}"}
    for name, dcl in table.items():
        f = unit_tok.get(dcl.unit)
        out.append({"name": name, "value": f(dcl.value) if f else f"{dcl.value:g} {dcl.unit}".strip(),
                    "kind": dcl.kind, "why": dcl.why})
    return out


# ----------------------------------------------------------------------
# Meshes: triangle soups welded, with only the creases inked
# ----------------------------------------------------------------------

def feature_edges(verts: np.ndarray, tris: np.ndarray, crease_deg: float = 25.0) -> np.ndarray:
    """The edges worth drawing: open edges and creases sharper than ``crease_deg``."""
    if not len(tris):
        return np.zeros((0, 2), int)
    tv = verts[tris]
    nrm = np.cross(tv[:, 1] - tv[:, 0], tv[:, 2] - tv[:, 0])
    ln = np.linalg.norm(nrm, axis=1, keepdims=True)
    nrm = np.divide(nrm, ln, out=np.zeros_like(nrm), where=ln > 1e-15)
    seen: dict[tuple[int, int], list[int]] = {}
    for f, (a, b, c) in enumerate(tris):
        for x, y in ((a, b), (b, c), (c, a)):
            seen.setdefault((min(x, y), max(x, y)), []).append(f)
    cos = math.cos(math.radians(crease_deg))
    out = []
    for e, fs in seen.items():
        if len(fs) == 1 or (len(fs) == 2 and float(nrm[fs[0]] @ nrm[fs[1]]) < cos) or len(fs) > 2:
            out.append(e)
    return np.array(out, dtype=int).reshape(-1, 2)


def weld(verts: np.ndarray, tris: np.ndarray, tol: float = 1e-6) -> tuple[np.ndarray, np.ndarray]:
    """Merge coincident vertices (a flat-shaded soup has one per corner of every triangle)."""
    key = np.round(verts / tol).astype(np.int64)
    _, first, inverse = np.unique(key, axis=0, return_index=True, return_inverse=True)
    inverse = inverse.reshape(-1)
    new_tris = inverse[tris]
    keep = (new_tris[:, 0] != new_tris[:, 1]) & (new_tris[:, 1] != new_tris[:, 2]) & (new_tris[:, 0] != new_tris[:, 2])
    return verts[first], new_tris[keep]


def soup_mesh(verts: np.ndarray, tris: np.ndarray, scale: float = 1.0, crease_deg: float = 25.0) -> S.Mesh:
    v, t = weld(np.asarray(verts, float) * scale, np.asarray(tris, int).reshape(-1, 3), tol=1e-6)
    return S.Mesh(v, t, feature_edges(v, t, crease_deg))


def rings_mesh(a_ring, b_ring) -> S.Mesh:
    """A stick between two cross-section rings (its tail and its head)."""
    A = [np.asarray(p, float) for p in a_ring]
    B = [np.asarray(p, float) for p in b_ring]
    k = len(A)
    pts = A + B
    faces = [list(range(k))[::-1], list(range(k, 2 * k))]
    for i in range(k):
        j = (i + 1) % k
        faces.append([i, j, k + j, k + i])
    return S._poly_mesh(pts, faces)


def ring_rank(values, places: int = 4) -> list[int]:
    """Each value's rank among the distinct rounded values, lowest first (rings by height)."""
    levels = sorted({round(float(v), places) for v in values})
    return [levels.index(round(float(v), places)) for v in values]


# ----------------------------------------------------------------------
# The registry
# ----------------------------------------------------------------------

def _kinds() -> dict[str, dict]:
    from . import metal, wedge_kind
    return {
        "wedge": {"label": "Wedge dome", "spec": wedge_kind.WedgeSpec, "build": wedge_kind.build_wedge, "form": wedge_kind.WEDGE_FORM},
        "zome": {"label": "Wedge zome", "spec": wedge_kind.ZomeSpec, "build": wedge_kind.build_zome, "form": wedge_kind.ZOME_FORM},
        "panel": {"label": "Framed-panel dome", "spec": M.Spec, "build": build_panel, "form": PANEL_FORM},
        "stove": {"label": "Steel dome wood stove", "spec": metal.StoveSpec, "build": metal.build_stove, "form": metal.STOVE_FORM},
        "tank": {"label": "Steel dome water tank", "spec": metal.TankSpec, "build": metal.build_tank, "form": metal.TANK_FORM},
    }


def kind_of(d: dict | None) -> str:
    k = str((d or {}).get("kind") or "panel")
    return k if k in _kinds() else "panel"


def spec_from(d: dict | None):
    k = kind_of(d)
    if k == "panel":
        return M.Spec.from_dict({kk: v for kk, v in (d or {}).items() if kk != "kind"})
    return from_dict(_kinds()[k]["spec"], d or {})


def spec_dict(spec) -> dict:
    out = asdict(spec)
    out.setdefault("kind", "panel")
    return out


def build(d: dict | None) -> M.Model:
    k = kind_of(d)
    return _kinds()[k]["build"](spec_from(d))


# ----------------------------------------------------------------------
# The page's JSON
# ----------------------------------------------------------------------

def b64(a: np.ndarray, dtype) -> str:
    return base64.b64encode(np.ascontiguousarray(a, dtype=dtype).tobytes()).decode("ascii")


def clean(v):
    """Make a table value JSON-safe (numpy numbers, tuples, sets, nested dicts)."""
    if isinstance(v, dict):
        return {str(k): clean(x) for k, x in v.items()}
    if isinstance(v, (list, tuple, set)):
        return [clean(x) for x in v]
    if isinstance(v, np.ndarray):
        return clean(v.tolist())
    if isinstance(v, np.floating):
        return float(v)
    if isinstance(v, np.integer):
        return int(v)
    if isinstance(v, np.bool_):
        return bool(v)
    if isinstance(v, float) and not math.isfinite(v):
        return None
    return v


def pieces_json(model: M.Model, mark: dict | None = None) -> list[dict]:
    mark = mark or {}
    out = []
    for p in model.pieces:
        if not len(p.mesh.verts):
            continue
        info = {k: v for k, v in p.info.items() if k not in ("outline_yz",)}
        if p.id in mark:
            info["mark"] = mark[p.id]
        out.append({
            "id": p.id, "name": p.name, "tag": p.tag, "material": p.material, "group": p.group, "step": p.step,
            "explode": [float(x) for x in p.explode], "info": clean(info),
            "v": b64(p.mesh.verts, "<f4"), "t": b64(p.mesh.tris, "<u4"), "e": b64(p.mesh.edges, "<u4"),
        })
    return out


PANEL_KEEP = ("title", "frequency", "cut", "diameter_m", "height_m", "inside_height_m", "floor_m2", "base_edges", "tapered", "level",
              "taper_m", "panels", "whole", "partial", "windows", "skylights", "stick_count", "stick_m", "boards", "rings", "bevel_lo",
              "bevel_hi", "sheets", "skin_m2", "glass_m2", "seam_m", "screws_corner", "screws_seam", "staples", "tape_m", "deck_m2",
              "base_mitre", "warnings", "chords")
GENERIC = ("kind", "summary", "cards", "sheets", "steps", "declared", "tags", "scenes", "door")


def scene(d: dict | None) -> dict:
    """Everything the page draws and lists for one design."""
    spec = spec_from(d)
    k = kind_of(d)
    model = _kinds()[k]["build"](spec)
    t = model.tables
    if k == "panel":
        mark = {pid: r["mark"] for r in t["sticks"] for pid in r["ids"]}
        tables = {kk: clean(t[kk]) for kk in PANEL_KEEP}
        tables["classes"] = clean([{kk: c[kk] for kk in ("name", "kind", "letters", "sides_m", "angles", "bevels", "count", "built", "height_m", "area_m2")}
                                   for c in t["classes"]])
        tables["sticks"] = clean([{kk: r[kk] for kk in ("mark", "cls", "side", "kind", "count", "long_m", "head_mitre", "head_bevel",
                                                          "tail_mitre", "rip_deg", "panels")} for r in t["sticks"]])
        tables["door"] = clean({kk: v for kk, v in (t["door"] or {}).items() if kk != "cards"}) if t["door"] else None
        tables["base_sections"] = clean(t["base_sections"])
        tables.update({kk: clean(v) for kk, v in panel_extras(model).items()})
    else:
        mark = {}
        tables = clean(t)
    from . import costing
    tables["materials"] = clean(costing.materials(k, model))
    tables["kind"] = k
    steps = [p.step for p in model.pieces if len(p.mesh.verts)]
    return {"spec": spec_dict(spec) | {"kind": k}, "pieces": pieces_json(model, mark), "tables": tables,
            "materials": M.MATERIALS, "landmarks": clean(model.landmarks), "max_step": max(steps) if steps else 0}


# ----------------------------------------------------------------------
# Forms and presets
# ----------------------------------------------------------------------

def _cut_options(cuts) -> list[list[str]]:
    return [[f"{f}|{c}", f"{f}V {c}"] for f, c in cuts]


PANEL_FORM = [
    {"key": "fc", "label": "Geodesic", "type": "cut", "options": _cut_options(M.CUTS)},
    {"key": "diameter_m", "label": "Diameter", "type": "len", "min": 2, "max": 12, "step": 0.05},
    {"key": "stick_w_m", "label": "Stick width", "type": "len", "min": 0.015, "max": 0.12, "step": 0.001},
    {"key": "stick_d_m", "label": "Stick depth", "type": "len", "min": 0.015, "max": 0.2, "step": 0.001},
    {"key": "riser_m", "label": "Pony wall", "type": "len", "min": 0, "max": 1.5, "step": 0.05},
    {"key": "skin", "label": "Skin", "type": "select", "options": [["cabin", "Cabin: plywood and shingles"], ["clear", "Greenhouse: clear"], ["none", "None: frame only"]]},
    {"key": "windows", "label": "Windows", "type": "int", "min": 0, "max": 12, "step": 1},
    {"key": "door", "label": "Door", "type": "check"}, {"key": "skylight", "label": "Skylight", "type": "check"},
    {"key": "stove", "label": "Stove", "type": "check"}, {"key": "porch", "label": "Porch", "type": "check"},
    {"key": "furnish", "label": "Furnished", "type": "check"}, {"key": "people", "label": "Person", "type": "check"},
    {"key": "door_w_m", "label": "Door width", "type": "len", "min": 0.6, "max": 1.4, "step": 0.01},
    {"key": "door_h_m", "label": "Door height", "type": "len", "min": 1.6, "max": 2.4, "step": 0.01},
]


def presets() -> list[dict]:
    """Grouped; the flagship first, and the one the page opens on."""
    from . import metal, wedge_kind
    W = wedge_kind.WedgeSpec()
    out = [
        {"key": "wedge", "group": "The wedge method", "label": "The Wedge Dome (flagship)", "spec": spec_dict(W)},
        {"key": "wedge-alt", "group": "The wedge method", "label": "Alternating Wedge Dome (in / out panels)",
         "spec": spec_dict(W) | {"pattern": "alternate_ground"}},
        {"key": "wedge-big", "group": "The wedge method", "label": "Wedge Dome, 26 ft from 16 in logs",
         "spec": spec_dict(W) | {"diameter_m": 26 * FT, "log_m": 16 * IN}},
        {"key": "zome", "group": "The wedge method", "label": "The Wedge Zome", "spec": spec_dict(wedge_kind.ZomeSpec())},
        {"key": "reference", "group": "Framed-panel domes", "label": "16 ft reference (4.88 m), 3V 5/8",
         "spec": {"kind": "panel", "frequency": 3, "cut": "5/8", "diameter_m": M.D("diameter_m")}},
        {"key": "2v", "group": "Framed-panel domes", "label": "2V hemisphere, 4 m", "spec": {"kind": "panel", "frequency": 2, "cut": "1/2", "diameter_m": 4.0}},
        {"key": "4m", "group": "Framed-panel domes", "label": "4 m, 3V 5/8", "spec": {"kind": "panel", "frequency": 3, "cut": "5/8", "diameter_m": 4.0}},
        {"key": "5m", "group": "Framed-panel domes", "label": "5 m, 3V 5/8", "spec": {"kind": "panel", "frequency": 3, "cut": "5/8", "diameter_m": 5.0}},
        {"key": "6m", "group": "Framed-panel domes", "label": "6 m, 3V 5/8", "spec": {"kind": "panel", "frequency": 3, "cut": "5/8", "diameter_m": 6.0}},
        {"key": "4v", "group": "Framed-panel domes", "label": "4V 5/8, 7 m", "spec": {"kind": "panel", "frequency": 4, "cut": "5/8", "diameter_m": 7.0}},
        {"key": "stove", "group": "All-steel domes", "label": "Dome Wood Stove (18 in largest member)", "spec": spec_dict(metal.StoveSpec())},
        {"key": "stove-1v", "group": "All-steel domes", "label": "Compact stove: 1V, 18 in plates", "spec": spec_dict(metal.StoveSpec()) | {"frequency": 1, "cut": "3/4"}},
        {"key": "tank", "group": "All-steel domes", "label": "Dome Water Tank, 8 ft", "spec": spec_dict(metal.TankSpec())},
        {"key": "tank-12", "group": "All-steel domes", "label": "Dome Water Tank, 12 ft 3V 5/8",
         "spec": spec_dict(metal.TankSpec()) | {"frequency": 3, "cut": "5/8", "diameter_m": 12 * FT}},
    ]
    return out


def defaults() -> dict:
    ks = _kinds()
    return {"kinds": {k: {"label": v["label"], "form": v["form"]} for k, v in ks.items()},
            "presets": presets(), "default": "wedge"}


# ----------------------------------------------------------------------
# The framed-panel dome's cards and steps (its own tables stay as they were)
# ----------------------------------------------------------------------

def build_panel(spec: M.Spec) -> M.Model:
    return M.build(spec)


def panel_extras(model: M.Model) -> dict:
    t, spec = model.tables, model.spec
    frame = [p for p in model.pieces if p.tag == "frame"]
    summary = [
        ["Across the base", m(t["diameter_m"])], ["Deck to top", m(t["height_m"])],
        ["Floor", m2(t["floor_m2"])],
        ["Panels", f"{t['whole']} whole + {t['partial']} partial"], ["Sticks", f"{t['stick_count']} in {len(t['sticks'])} cuts"],
        ["2x3 studs", n(t["boards"])], ["Plywood sheets", n(t["sheets"])],
        ["Base sections", f"{t['tapered']} tapered, {t['level']} level"],
        ["Rip bevels", f"{deg(t['bevel_lo'])} to {deg(t['bevel_hi'])}"],
    ]
    if t["door"]:
        summary.append(["Door opening", f"{m(t['door']['W'])} x {m(t['door']['H'])}"])

    cards = []
    for r in t["sticks"]:
        try:
            outer, inner, _p = M.stick_outline(model, r["sample"])
        except Exception:                      # a stick the outline cannot be read from: draw its length
            outer, inner = [(0, 0), (r["long_m"], 0), (r["long_m"], spec.stick_w_m), (0, spec.stick_w_m)], None
        mn = min(x for x, _ in outer)
        outer = [(x - mn, y) for x, y in outer]
        inner = [(x - mn, y) for x, y in inner] if inner else None
        d = drawing(outer, angles=False, inner=inner,
                    notes=[{"at": [0.0, spec.stick_w_m * 1.9], "text": f"tail {deg(r['tail_mitre'])}"},
                           {"at": [r["long_m"] * 0.78, spec.stick_w_m * 1.9], "text": f"head {deg(r['head_mitre'])} / {deg(r['head_bevel'])}"}])
        d["dims"] = [{"a": [0.0, 0.0], "b": [r["long_m"], 0.0], "m": r["long_m"]}]
        cards.append(card(r["mark"], f"Stick {r['mark']}", r["count"], [
            ["Panel class", "partial" if r["cls"] == "partial" else r["cls"]], ["Side", f"{r['side']} ({r['kind']})"],
            ["Long point to long point", m(r["long_m"])], ["Head (compound)", f"{deg(r['head_mitre'])} mitre, {deg(r['head_bevel'])} bevel"],
            ["Tail", f"{deg(r['tail_mitre'])} mitre, square"], ["Rip bevel", deg(r["rip_deg"])],
        ], d, r["ids"], group=f"Rip at {r['rip_deg']:.1f}°", kind="stick"))
    for c in t["classes"]:
        a, b, cc = c["sides_m"]
        x, y = pm.trammel_apex(a, b, cc)
        ids = [p.id for p in model.pieces if p.tag in ("skin", "glass") and p.info.get("cls") == c["name"]]
        cards.append(card(f"Panel {c['name']}", f"Panel {c['name']} skin", c["count"], [
            ["Sides", " / ".join(m(s) for s in c["sides_m"])], ["Area", m2(c["area_m2"])], ["Kind", c["kind"]],
        ], drawing([(0, 0), (a, 0), (x, y)]), ids, group="Skin panels", kind="panel"))
    for sec in t["base_sections"]:
        L, lo, hi = sec["length_m"], sec["low_m"], sec["high_m"]
        ids = [p.id for p in model.pieces if p.tag == "base" and p.group == sec["id"]]
        cards.append(card(sec["id"], f"Base section {sec['id']}", 1, [
            ["Length", m(L)], ["Low end", m(lo)], ["High end", m(hi)], ["End mitres", deg(sec["end_mitre"])],
        ], drawing([(0, 0), (L, 0), (L, hi), (0, lo)], angles=False), ids, group="Base sections", kind="board"))

    sheets = [{"w": M.D("sheet_l_m"), "h": M.D("sheet_w_m"), "parts": [{"mark": nm, "pts": [list(p) for p in pts]} for nm, pts in sh]}
              for sh in t["nest"]]

    book = Book()
    ripped = max(t["sticks"], key=lambda r: r["count"])
    book.prep("Finish, then rip on the bevel",
              f"Oil or stain the 2x3s while they are whole. Then rip every one in half with the blade tilted to the rip bevel: "
              f"the cut leaves two sticks {m(spec.stick_w_m)} wide with the bevel already on one edge. Bevels on this dome run "
              f"{deg(t['bevel_lo'])} to {deg(t['bevel_hi'])}; rip each bevel as one batch and label it.",
              frame, ["Table saw", "Digital angle gauge", "Push stick"],
              f"Cut a scrap first and check the bevel with the gauge: {deg(ripped['rip_deg'])} for the most common stick.")
    book.prep("Cut the tails square, the heads compound",
              f"Cut every stick to its mark on the cut list ({len(t['sticks'])} different sticks, {t['stick_count']} in all). "
              "The tail gets a plain mitre; the head gets the compound cut (mitre and bevel) that runs into the corner.",
              frame, ["Mitre saw", "Stop block", "Pencil"], "Lay three sticks of one panel on the bench: their long points meet.")
    book.prep("Build each panel on the jig",
              "Screw a jig to a sheet of plywood for each panel class, lay the three sticks in it and screw the corners. "
              "The skin goes on later, on the dome.", frame, ["Jig", "Drill", "Screws"],
              "Measure each finished panel's sides against the panel cards.")
    names = {0: "Deck, piers and floor", 1: "Base sections", 2: "Door frame", 20: "Hang the door", 30: "Stove and furnishings", 99: "Windows and skylight"}
    rings = t["rings"]
    groups: dict[int, list] = {}
    for p in model.pieces:
        if p.tag in ("site", "person") or not len(p.mesh.verts):
            continue
        groups.setdefault(p.step, []).append(p)
    for k in sorted(groups):
        ps = groups[k]
        tags = {p.tag for p in ps}
        if k in names and not (k == 2 and "frame" in tags):
            title = names[k]
        elif "frame" in tags and "door" in tags:
            title = "Door frame and the first ring of panels"
        elif "frame" in tags:
            title = f"Ring {k - 1} of {rings} panels"
        elif "skin" in tags:
            title = "Skin the dome"
        else:
            title = ", ".join(sorted(tags)).capitalize()
        text = {
            "Deck, piers and floor": f"Set the piers, frame the deck and lay the floor ({m2(t['deck_m2'])}).",
            "Base sections": f"Stand the {t['base_edges']} base sections round the deck edge, mitred {deg(t['base_mitre'])} at each end.",
            "Skin the dome": f"Sheath the panels ({m2(t['skin_m2'])} of skin), tape every seam ({m(t['tape_m'])} of tape) and staple the covering.",
        }.get(title, f"Lift the panels of this ring onto the ones below and screw each seam. Check that every new corner meets its neighbours flush.")
        # the panel model is cached and its stage numbers are the scenes' own: point at them, never renumber
        book.steps.append({"mode": "add", "title": title, "text": text, "tools": [], "check": "",
                           "focus": [p.id for p in ps], "show": k, "phase": "Build"})
    return {"summary": summary, "cards": cards, "sheets": sheets, "steps": book.steps,
            "declared": declared_rows(M.DECLARED),
            "tags": [["frame", "Frame"], ["skin", "Skin"], ["glass", "Glazing"], ["base", "Base sections"], ["door", "Door"],
                     ["deck", "Deck"], ["furniture", "Furniture"], ["person", "Person"], ["site", "Ground"]]}


# ----------------------------------------------------------------------
# The checks: every kind, every preset
# ----------------------------------------------------------------------

def validate_kinds(verbose: bool = True) -> list[str]:
    """Every preset builds; the figures the page leans on are the solvers' own.

    * the stove's largest member is exactly the 18 in asked for;
    * the tank's capacity is the volume of the water it draws;
    * the wedge dome's cut list is Wedge Builder's families, count for count;
    * a steel plate's weld bevel is half the fold to its neighbour;
    * every piece that is built goes up in exactly one build step, and every step's pieces exist.
    """
    from . import costing, exports, metal, wedge_kind
    from wedge_builder import design as W

    out = []

    def ok(msg):
        out.append(msg)
        if verbose:
            print("ok:", msg)

    for pr in presets():
        sc = scene(pr["spec"])
        t = sc["tables"]
        ids = {q["id"] for q in sc["pieces"]}
        adds = [st for st in t["steps"] if st["mode"] == "add"]
        shows = [st["show"] for st in adds]
        assert len(shows) == len(set(shows)), f"{pr['key']}: two steps add at the same stage"
        built = [q for q in sc["pieces"] if q["step"] >= 0 and q["tag"] not in ("site", "person")]
        for q in built:
            assert q["step"] in shows, f"{pr['key']}: {q['id']} goes up in no step"
        for st in t["steps"]:
            missing = [f for f in st["focus"] if f not in ids]
            assert not missing, f"{pr['key']}: step {st['title']!r} names missing pieces {missing[:3]}"
        if t["kind"] != "panel":
            counted = [f for st in adds for f in st["focus"]]
            assert len(counted) == len(set(counted)), f"{pr['key']}: a piece goes up twice"
            assert set(counted) == {q["id"] for q in built}, f"{pr['key']}: the steps and the pieces disagree"
        assert t["cards"], f"{pr['key']}: no cut list"
        assert t["summary"], f"{pr['key']}: no summary"
        costing.validate_costing(t["materials"])
        notes = exports.validate_exports(sc)
        ok(f"{pr['key']}: {len(sc['pieces'])} pieces, {len(t['cards'])} cut cards, {len(t['steps'])} steps, each built piece in one step; "
           f"materials ${t['materials']['total']:,.0f} (estimate); exports read back: {notes[0]}; {notes[-2]}")

    st = metal.build_stove(metal.StoveSpec())
    longest = st.tables["stove"]["longest_m"]
    assert abs(longest - 18 * IN) < 1e-9, longest
    ok(f"stove: the largest member is {longest / IN:.4f} in, as asked")
    tk = metal.build_tank(metal.TankSpec())
    cap, mesh_l = tk.tables["tank"]["capacity_l"], tk.tables["tank"]["water_mesh_l"]
    assert abs(cap - mesh_l) < 1e-6 * cap, (cap, mesh_l)
    ok(f"tank: capacity {cap:.1f} L = the water's own volume {mesh_l:.1f} L")

    sh = metal.build_shell(2, "1/2", None, 18 * IN, None, 0.25 * IN, 0.0, 4 * IN, IN)
    by_face = {p.face: p for p in sh.plates}
    checked = 0
    for (a, b), fs in sh.edge_faces.items():
        if len(fs) != 2 or fs[0] not in by_face or fs[1] not in by_face:
            continue
        fold = pm.fold_deg(sh.trunc.sphere, fs[0], fs[1])
        p = by_face[fs[0]]
        for i in range(len(p.poly)):
            q0, q1 = p.poly[i], p.poly[(i + 1) % len(p.poly)]
            if {tuple(np.round(q0, 9)), tuple(np.round(q1, 9))} == {tuple(np.round(sh.V[a], 9)), tuple(np.round(sh.V[b], 9))}:
                assert abs(p.bevels[i] - fold / 2) < 1e-6, (p.bevels[i], fold)
                checked += 1
    assert checked > 20, checked
    ok(f"steel plates: every one of {checked} shared edges is bevelled half its fold")

    spec = wedge_kind.WedgeSpec()
    d = wedge_kind._design(spec)
    cards = {c["mark"]: c["count"] for c in wedge_kind.build_wedge(spec).tables["cards"]}
    for f in d.families:
        assert cards.get(f.name) == f.count, (f.name, cards.get(f.name), f.count)
    assert sum(f.count for f in d.families) == len(d.model.members)
    ok(f"wedge dome: the cut list is Wedge Builder's {len(d.families)} families, {len(d.model.members)} wedges")

    # a clipped bottom-ring plate is nested inside its chord triangle and cut as the plate it is
    sh_parts = [q for s_ in metal.build_stove(metal.StoveSpec()).tables["sheets"] for q in s_["parts"]]
    clipped = [q for q in sh_parts if len(q["pts"]) == 4]
    for q in clipped:
        tri = q["chord"]
        for x, y in q["pts"]:
            l = np.linalg.lstsq(np.array([[tri[0][0] - tri[2][0], tri[1][0] - tri[2][0]], [tri[0][1] - tri[2][1], tri[1][1] - tri[2][1]]]),
                                np.array([x - tri[2][0], y - tri[2][1]]), rcond=None)[0]
            assert min(l[0], l[1], 1 - l[0] - l[1]) > -1e-9, "a clipped plate pokes out of its nested triangle"
    assert clipped, "the stove's bottom ring has no clipped plates to check"
    ok(f"steel nesting: {len(clipped)} clipped plates cut as four-sided pieces inside their nested triangles")

    assert plans_prices() is costing.PRICE_ESTIMATES
    ok("the plan set's price sheet and the page's materials table read one price table")
    return out


def plans_prices():
    """The price table the PDF plan set multiplies by (plans.py needs reportlab, so read it from the source)."""
    import ast
    from pathlib import Path
    src = (Path(__file__).with_name("plans.py")).read_text(encoding="utf-8")
    tree = ast.parse(src)
    for node in tree.body:
        if isinstance(node, ast.Assign) and any(getattr(t_, "id", "") == "PRICE_ESTIMATES" for t_ in node.targets):
            assert ast.unparse(node.value) == "CO.PRICE_ESTIMATES", "plans.py keeps its own price table again"
            from . import costing
            return costing.PRICE_ESTIMATES
    raise AssertionError("plans.py has no PRICE_ESTIMATES")

