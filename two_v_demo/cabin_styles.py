"""The 40-hour cabin, styled every way the Dome Creator can style it, priced.

The book's cabin is a 2V dome at the solver's sphere radius. The Dome Creator
can build that dome -- same frequency, same size -- and dress it in everything
on its menus. This module does that, one Creator rebuild per row, and reports
what each choice costs, weighs and takes in hours:

* **the price list** -- every catalogue entry the Creator prices, as declared in
  ``materials.py`` and ``workshop.py``;
* **one menu at a time** -- the bare cabin with each frame material, each panel,
  each cladding and each foundation in turn;
* **twelve styles** -- the cabin's frame dressed in the finishes of each of the
  Creator's twelve designs;
* **every skin on every frame** -- frame material x panel, and cladding x
  foundation, in full;
* **the fit-out, item by item** -- every piece of equipment priced, and each
  design's fit-out as a package.

The bare cabin is the Creator's Split-Log Homestead -- timber, hubless doubled,
quarter wedges, plywood panels -- rebuilt at the cabin's radius, with nothing
on its floor. The Creator frames in quarter wedges; the cabin is framed in
eighth-log wedges, so the Creator's frame line is the Creator's figure, and the
book prints it beside the wedge method's own (:func:`frame_note`).

Every price is a declared input of the Creator multiplied by a quantity its
model measured. The rows are cached on disk, keyed by the Creator's source.
"""

from __future__ import annotations

import hashlib
import json
from functools import lru_cache
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
CACHE = Path(__file__).resolve().parent / ".cache" / "cabin_styles.json"
SOURCES = ("materials.py", "workshop.py", "dome_model.py", "mesh_builder.py", "presets.py",
           "two_v_demo/cabin_styles.py", "two_v_demo/creator_facts.py")
BASE_DESIGN = "Split-Log Homestead"
SQFT = 10.7639104
FT = 3.280839895
LB = 2.20462262


def cabin_radius_m() -> float:
    """The book's dome: the solver's sphere radius."""
    from . import raw_wedge_bridge as rb
    return float(rb.model().topology.sphere_radius_in) * 0.0254


def base_config() -> dict:
    """The bare cabin: the Split-Log Homestead's shell at the cabin's size and
    frequency, with an empty floor."""
    from .creator_facts import _config
    cfg = json.loads(json.dumps(_config(BASE_DESIGN)))
    cfg.update(radius=round(cabin_radius_m(), 4), frequency=2, props=[], partitions="None",
               sections=["Unassigned"] * len(cfg.get("sections", [])) or cfg.get("sections", []))
    return cfg


NATURAL = {
    # What each material is made into, and how thick. The Creator weighs a
    # frame as solid struts of the chosen shape and width, so steel cut to the
    # cabin's 10 cm quarter wedges would be priced as solid steel wedges. Each
    # material instead takes the section and width of a Creator design built
    # in it; the three no design uses are given a tube, and say so.
    "Timber (SPF)": ("Quarter Wedge", None, "the cabin's own"),
    "Whole Tree Trunk": ("Full Tree Trunk", 0.2021, "the Whole Trunk Lodge's"),
    "Aluminum": ("Round Tube", 0.04, "the Grow Dome's"),
    "Structural Steel": ("Square Tube", 0.05, "the Woodland Square Mirror's"),
    "Rebar Steel": ("Rebar Rod", 0.024, "the Rebar Garden Dome's"),
    "Galvanized Steel": ("Round Tube", 0.04, "assumed: no design uses it"),
    "PVC Pipe": ("Round Tube", 0.04, "assumed: no design uses it"),
    "Bamboo": ("Round Tube", 0.05, "assumed: no design uses it"),
}


def with_material(cfg: dict, material: str) -> dict:
    cfg = json.loads(json.dumps(cfg))
    shape, width, _src = NATURAL.get(material, (cfg["strut_shape"], None, ""))
    cfg["frame_material"] = material
    cfg["strut_shape"] = shape
    if width is not None:
        cfg["strut_width"] = width
    return cfg


STYLE_KEYS = ("default_panel", "panel_color", "layers", "foundation", "frame_color")
"""What 'a style' carries over from a design: its skin, its colours and what it
stands on. The frame -- material, style, shape, frequency -- stays the cabin's."""


def _stats(cfg: dict) -> dict:
    from .creator_facts import _stats as stats
    return stats(cfg)


def _hours(cfg: dict, name: str) -> float:
    from .creator_bridge import build
    return float(build(cfg, name).hours)


def _row(label: str, cfg: dict, hours: bool = False) -> dict:
    s = _stats(cfg)
    out = {"label": label, "total": s["total_cost"], "frame": s["frame_cost"] + s["hub_cost"],
           "panels": s["panel_cost"], "cladding": s["layer_cost"], "foundation": s["foundation_cost"],
           "fitout": s["prop_cost"] + s["wall_cost"] + s["plumbing_cost"] + s["wire_cost"],
           "weight_kg": s["structure_weight"], "frame_kg": s["frame_weight"], "panel_kg": s["panel_weight"],
           "solar_w": s["solar_watts"]}
    if hours:
        out["hours"] = _hours(cfg, label)
    return out


def _key() -> str:
    h = hashlib.sha256()
    for name in SOURCES:
        h.update((ROOT / name).read_bytes())
    return h.hexdigest()


def _work() -> dict:
    import materials as m
    import workshop as w
    from . import creator_facts as cf
    from .creator_bridge import presets_all

    base = base_config()
    s0 = _stats(base)
    out: dict = {
        "radius_m": base["radius"], "diameter_ft": 2 * base["radius"] * FT,
        "floor_sqft": s0["floor_area"] * SQFT, "floor_m2": s0["floor_area"],
        "surface_m2": s0["surface_area"], "surface_sqft": s0["surface_area"] * SQFT,
        "struts": s0["strut_count"], "strut_m": s0["strut_total_len"], "panels": s0["panel_count"],
        "foundation_m2": s0["foundation_area"], "base": _row("Bare cabin", base, hours=True),
        "base_parts": {k: base[k] for k in ("frame_material", "frame_style", "strut_shape", "strut_width",
                                            "default_panel", "layers", "foundation")},
    }
    # -- the price list, as declared -------------------------------------
    out["price_list"] = {
        "frame": [{"name": f.name, "density": f.density, "per_kg": f.cost_per_kg, "hub": f.hub_cost}
                  for f in m.FRAME_MATERIALS],
        "panels": [{"name": p.name, "per_m2": p.cost_per_m2, "kg_m2": p.area_weight, "window": p.is_window,
                    "watts_m2": p.watts_per_m2} for p in m.PANEL_TYPES if p.name != "Open"],
        "layers": [{"name": l.name, "per_m2": l.cost_per_m2, "thick_mm": 1000 * l.thickness}
                   for l in m.LAYER_TYPES if l.name != "None"],
        "foundations": [{"name": f.name, "per_m2": f.cost_per_m2, "kg_m2": f.weight_per_m2}
                        for f in m.FOUNDATION_TYPES],
        "components": [{"name": c.name, "cost": c.cost, "minutes": c.minutes} for c in m.PANEL_COMPONENTS],
        "rates": {"screw": m.SCREW_COST, "wire_m": w.WIRE_COST_PER_M, "pex_m": w.PEX_COST_PER_M,
                  "drain_m": w.DRAIN_COST_PER_M, "fixture_rough": w.FIXTURE_ROUGH_COST},
        "props": [{"name": p.name, "category": p.category.title(), "cost": p.cost, "kg": p.weight,
                   "watts": p.watts} for p in w.PROP_TYPES],
        "rooms": [r.name for r in w.ROOM_TYPES if r.name != "Unassigned"],
    }
    # -- one menu at a time, on the bare cabin -----------------------------
    def sweep(field, values, set_value):
        rows = []
        for v in values:
            cfg = json.loads(json.dumps(base))
            set_value(cfg, v)
            rows.append(_row(v, cfg))
        return rows
    out["by_frame"] = []
    for f in m.FRAME_MATERIALS:
        row = _row(f.name, with_material(base, f.name))
        shape, width, src = NATURAL.get(f.name, (base["strut_shape"], None, ""))
        row.update(shape=shape, width_cm=100 * (width if width is not None else base["strut_width"]), source=src)
        out["by_frame"].append(row)
    out["by_panel"] = sweep("default_panel", [p.name for p in m.PANEL_TYPES if p.name != "Open"],
                            lambda c, v: c.__setitem__("default_panel", v))
    out["by_layer"] = sweep("layers", [l.name for l in m.LAYER_TYPES],
                            lambda c, v: c.__setitem__("layers", [v, "None", "None"]))
    out["by_foundation"] = sweep("foundation", [f.name for f in m.FOUNDATION_TYPES],
                                 lambda c, v: c.__setitem__("foundation", v))
    # -- the twelve styles on the cabin's frame ----------------------------
    styles = []
    for name, design in presets_all():
        cfg = json.loads(json.dumps(base))
        for k in STYLE_KEYS:
            if k in design:
                cfg[k] = json.loads(json.dumps(design[k]))
        row = _row(name, cfg, hours=True)
        row.update(panel_name=cfg["default_panel"], layer_names=[x for x in cfg["layers"] if x != "None"],
                   foundation_name=cfg["foundation"], design_total=cf._stats(design)["total_cost"])
        styles.append(row)
    out["styles"] = styles
    # -- every skin on every frame -----------------------------------------
    frames = [f.name for f in m.FRAME_MATERIALS]
    panels = [p.name for p in m.PANEL_TYPES if p.name != "Open"]
    grid = {}
    for fr in frames:
        for pa in panels:
            cfg = with_material(base, fr)
            cfg["default_panel"] = pa
            grid[f"{fr}|{pa}"] = _stats(cfg)["total_cost"]
    out["frame_panel"] = {"frames": frames, "panels": panels, "cost": grid,
                          "shapes": {fr: NATURAL.get(fr, (base["strut_shape"],))[0] for fr in frames}}
    layers = [l.name for l in m.LAYER_TYPES]
    founds = [f.name for f in m.FOUNDATION_TYPES]
    grid2 = {}
    for la in layers:
        for fo in founds:
            cfg = json.loads(json.dumps(base))
            cfg.update(layers=[la, "None", "None"], foundation=fo)
            grid2[f"{la}|{fo}"] = _stats(cfg)["total_cost"]
    out["layer_foundation"] = {"layers": layers, "foundations": founds, "cost": grid2}
    # -- fit-out packages: each design's equipment, priced -----------------
    by_name = w.PROP_TYPE_BY_NAME
    packages = []
    for name, design in presets_all():
        items = [p["type"] for p in design.get("props", []) if p.get("type") in by_name]
        if not items:
            continue
        packages.append({"name": name, "items": len(items),
                         "cost": sum(by_name[i].cost for i in items),
                         "kg": sum(by_name[i].weight for i in items),
                         "watts": sum(by_name[i].watts for i in items),
                         "list": sorted(set(items))})
    out["packages"] = packages
    # -- the counts the Creator's menus multiply to ------------------------
    out["counts"] = {"shells": cf.shell_permutations(), "distinct": cf.distinct_shells(),
                     "fitouts": cf.fitout_permutations(), "dials": cf.dial_permutations()}
    return out


@lru_cache(maxsize=1)
def facts() -> dict:
    key = _key()
    try:
        data = json.loads(CACHE.read_text(encoding="utf-8"))
        if data.get("key") == key:
            return data["facts"]
    except (OSError, ValueError):
        pass
    f = _work()
    text = json.dumps({"key": key, "facts": f}, indent=1,
                      default=lambda v: v.item() if hasattr(v, "item") else str(v))
    CACHE.parent.mkdir(parents=True, exist_ok=True)
    CACHE.write_text(text, encoding="utf-8")
    return json.loads(text)["facts"]


def style_config(name: str) -> dict:
    """The cabin dressed as one of the Creator's designs (for drawing)."""
    from .creator_bridge import presets_all
    cfg = base_config()
    for preset_name, design in presets_all():
        if preset_name == name:
            for k in STYLE_KEYS:
                if k in design:
                    cfg[k] = json.loads(json.dumps(design[k]))
            return cfg
    raise KeyError(name)


def validate_cabin_styles() -> None:
    f = facts()
    assert abs(f["radius_m"] - cabin_radius_m()) < 1e-3
    assert f["struts"] == 120 and f["panels"] == 40, (f["struts"], f["panels"])
    assert len(f["styles"]) == 12 and len(f["by_panel"]) == 15 and len(f["by_frame"]) == 8
    fp = f["frame_panel"]
    assert len(fp["cost"]) == len(fp["frames"]) * len(fp["panels"])
    # A sweep row and its matrix cell are the same build.
    base_frame = f["base_parts"]["frame_material"]
    for row in f["by_panel"]:
        assert abs(fp["cost"][f"{base_frame}|{row['label']}"] - row["total"]) < 0.01, row["label"]
    # Every row's lines add up to its total, within the hardware the lines leave out.
    for row in f["styles"]:
        parts = row["frame"] + row["panels"] + row["cladding"] + row["foundation"] + row["fitout"]
        assert parts <= row["total"] + 0.01, row
