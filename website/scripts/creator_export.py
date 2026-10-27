"""The Dome Creator, as tables a browser can use.

The Portal's Dome Creator space (website/src/world/creator.ts) is the desktop tool
(dome_creator.py, on dome_model.DomeModel) brought to the web. A browser cannot run the
Creator, so this exports what it computes from: its menus and dial ranges (read from the
tool, via two_v_demo.creator_facts), its material, panel, cladding-layer and Panel Lab
tables, the wedge-cut panels' stock (materials.wedge_panel), every strut shape's cross
section at every width the dial allows (the Creator's own function, evaluated), the
workshop fit-out (rooms, partitions, props, wiring and plumbing), the presets, and the
dome's geometry at unit radius for every frequency (struts scale with the radius, panel
areas with its square). The browser then does only the Creator's arithmetic --
DomeModel.stats() -- and scripts/test_creator.mjs checks it against stats() itself.

    py -3.12 scripts/creator_export.py --fixtures FILE   # write test cases with the Creator's answers
"""

from __future__ import annotations

import argparse
import json
import random
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(ROOT))

import dome_model  # noqa: E402
import materials  # noqa: E402
import presets  # noqa: E402
import workshop  # noqa: E402
from two_v_demo import creator_facts  # noqa: E402

HUBLESS = "Hubless Doubled"


def _r(x: float, n: int = 6) -> float:
    return round(float(x), n)


def dial_values(dial) -> list[float]:
    return [_r(dial.low + i * dial.step, 4) for i in range(dial.settings)]


def geometry(frequency: int, frame_style: str) -> dict:
    """The dome at radius 1: struts, hubs, bolts, panels, and the drawing."""
    cfg = dome_model.DomeConfig(frequency=frequency, radius=1.0, frame_style=frame_style,
                                foundation="Bare Ground")
    m = dome_model.DomeModel(cfg)
    centre = m.sphere_center
    geo = m.geo
    return {
        "frequency": frequency, "frameStyle": frame_style,
        "baseZ": _r(geo.base_z),
        "struts": [_r(length) for _p, _q, length in m.struts],
        "hubs": len(m.hubs), "bolts": len(m.bolt_points),
        "panelAreas": [_r(p.area) for p in m.panels],
        "panelKeys": [p.key for p in m.panels],
        # the drawing: unit-sphere nodes and the edges and faces between them (z up)
        "vertices": [[_r(c, 10) for c in v] for v in (m.world_verts - centre)],
        "edges": [[int(a), int(b)] for a, b in geo.edges],
        "faces": [[int(i) for i in f] for f in geo.faces],
    }


def web_config(cfg: "dome_model.DomeConfig") -> dict:
    """A DomeConfig in the browser's terms (creator.ts Config)."""
    d = cfg.to_dict()
    return {"frequency": d["frequency"], "radius": d["radius"], "frameStyle": d["frame_style"], "hubStyle": d["hub_style"],
            "strutShape": d["strut_shape"], "strutWidth": d["strut_width"], "frameMaterial": d["frame_material"],
            "panel": d["default_panel"], "foundation": d["foundation"], "foundationScale": d["foundation_scale"],
            "wedgeOrientation": d["wedge_orientation"], "layers": list(d["layers"]), "panelOverrides": dict(d["panel_overrides"]),
            "sections": list(d["sections"]), "partitions": d["partitions"],
            "props": [{"type": q["type"], "x": float(q.get("x", 0)), "y": float(q.get("y", 0)), "yaw": float(q.get("yaw", 0))} for q in d["props"]],
            "trunkStockLength": d["trunk_stock_length"], "trunkCircumference": d["trunk_circumference"],
            "frameColor": d["frame_color"], "panelColor": d["panel_color"], "recess": d["recess_pct"], "customPanels": {}}


def creator_config(c: dict) -> "dome_model.DomeConfig":
    """The browser's Config back into a DomeConfig (custom panels registered first)."""
    for name, definition in (c.get("customPanels") or {}).items():
        materials.register_custom_panel(name, definition)
    return dome_model.DomeConfig.from_dict({
        "frequency": c["frequency"], "radius": c["radius"], "frame_style": c["frameStyle"], "hub_style": c["hubStyle"],
        "strut_shape": c["strutShape"], "strut_width": c["strutWidth"], "frame_material": c["frameMaterial"],
        "default_panel": c["panel"], "foundation": c["foundation"], "foundation_scale": c["foundationScale"],
        "wedge_orientation": c.get("wedgeOrientation", "Inside"), "layers": c.get("layers", ["None"] * 3),
        "panel_overrides": c.get("panelOverrides", {}), "sections": c.get("sections", ["Unassigned"] * 10),
        "partitions": c.get("partitions", "Markings"), "props": c.get("props", []),
        "trunk_stock_length": c.get("trunkStockLength", 0.0), "trunk_circumference": c.get("trunkCircumference", 0.0)})


def _rgb(c) -> list[float]:
    return [_r(x, 4) for x in c]


def tables() -> dict:
    dials = {d.name: d for d in creator_facts.dials()}
    widths = dial_values(dials["Strut width"])
    defaults = dome_model.DomeConfig()
    return {
        "_generated_by": "website/scripts/creator_export.py from dome_model, materials and two_v_demo.creator_facts -- do not edit",
        "frequencies": [v for _label, v in creator_facts.axis("Frequency").values],
        "frameStyles": list(dome_model.FRAME_STYLES),
        "hubStyles": list(dome_model.HUB_STYLES),
        "dials": {name: {"low": d.low, "high": d.high, "step": d.step, "unit": d.unit, "values": dial_values(d)}
                  for name, d in dials.items() if name in ("Radius", "Strut width", "Foundation size")},
        "defaults": {"frequency": defaults.frequency, "radius": defaults.radius, "frameStyle": defaults.frame_style,
                     "hubStyle": defaults.hub_style, "strutShape": materials.STRUT_SHAPES[defaults.strut_shape].name,
                     "strutWidth": defaults.strut_width, "frameMaterial": materials.FRAME_MATERIALS[defaults.frame_material].name,
                     "panel": defaults.default_panel, "foundation": defaults.foundation, "foundationScale": defaults.foundation_scale},
        "strutShapes": [{"name": s.name, "kind": s.kind, "splits": s.splits if s.kind == "wedge" else 0,
                         "section": {f"{w:.4f}": float(s.cross_section_area(w)) for w in widths},
                         # the cross section at 6 cm, for drawing (u across, v radial)
                         "profile": [[_r(u / 0.06, 5), _r(v / 0.06, 5)] for u, v in s.profile(0.06)]}
                        for s in materials.STRUT_SHAPES],
        "wedgeOrientations": list(materials.WEDGE_ORIENTATIONS),
        "frameMaterials": [{"name": f.name, "density": f.density, "costPerKg": f.cost_per_kg,
                            "hubWeight": f.hub_weight, "hubCost": f.hub_cost} for f in materials.FRAME_MATERIALS],
        "panels": [{"name": p.name, "areaWeight": p.area_weight, "costPerM2": p.cost_per_m2,
                    "wattsPerM2": p.watts_per_m2, "isWindow": p.is_window, "rgb": _rgb(p.color), "alpha": p.alpha,
                    "colorable": p.colorable, "shape": p.shape} for p in materials.PANEL_TYPES],
        "layers": [{"name": l.name, "areaWeight": l.area_weight, "costPerM2": l.cost_per_m2, "thickness": l.thickness,
                    "rgb": _rgb(l.color), "alpha": l.alpha} for l in materials.LAYER_TYPES],
        "frameColors": [{"name": c.name, "rgb": _rgb(c.rgb)} for c in materials.FRAME_COLORS],
        "panelColors": [{"name": c.name, "rgb": _rgb(c.rgb)} for c in materials.PANEL_COLORS],
        # the Panel Lab: a base surface plus hardware, spread over a nominal panel (register_custom_panel)
        "panelLab": {"components": [{"name": c.name, "cost": c.cost, "weight": c.weight, "minutes": c.minutes,
                                     "screwsEach": c.screws_each} for c in materials.PANEL_COMPONENTS],
                     "screwCost": materials.SCREW_COST, "nominalPanelM2": 2.0},
        # wedge-cut panels: what one square metre takes (materials.wedge_panel)
        "wedgePanels": [{"name": f"Wedge Cut 1/{n}", **{k: (_r(v) if isinstance(v, float) else v)
                                                       for k, v in vars(materials.wedge_panel(n)).items()}}
                        for n in materials.WEDGE_PANEL_SPLITS],
        "fitout": {
            "rooms": [{"name": r.name, "rgb": _rgb(r.color), "blurb": r.hint} for r in workshop.ROOM_TYPES],
            "partitionModes": list(workshop.PARTITION_MODES), "partitionHeights": dict(workshop.PARTITION_HEIGHTS),
            "centerFraction": workshop.CENTER_FRACTION, "wedgeDegrees": workshop.WEDGE_DEGREES,
            "wallCostPerM2": workshop.WALL_COST_PER_M2, "wallWeightPerM2": workshop.WALL_WEIGHT_PER_M2,
            "doorway": 1.0, "wallRimGap": 0.20, "wallMin": 0.4,
            "props": [{"name": q.name, "category": q.category, "cost": q.cost, "weight": q.weight, "watts": q.watts,
                       "role": q.role, "radius": q.pick_radius, "height": q.pick_height} for q in workshop.PROP_TYPES],
            "waterFixtures": sorted(workshop.WATER_FIXTURES),
            "wireCostPerM": workshop.WIRE_COST_PER_M, "pexCostPerM": workshop.PEX_COST_PER_M,
            "drainCostPerM": workshop.DRAIN_COST_PER_M, "fixtureRoughCost": workshop.FIXTURE_ROUGH_COST,
            "wireSlack": 1.3, "pipeSlack": 1.25, "utility": [0.6, -0.75],
        },
        "trunkStock": {"step": 0.3048, "max": 12.192, "waste": 1.10, "shape": "Full Tree Trunk"},
        "presets": [{"name": name, "config": web_config(dome_model.DomeConfig.from_dict(data))} for name, data in presets.PRESETS],
        "foundations": [{"name": f.name, "costPerM2": f.cost_per_m2, "weightPerM2": f.weight_per_m2, "height": f.height}
                        for f in materials.FOUNDATION_TYPES],
        "constants": {"boltCost": dome_model.BOLT_COST, "boltWeight": dome_model.BOLT_WEIGHT,
                      "wedgesPerTree": dome_model.WEDGES_PER_TREE, "frameCostFactor": 1.15,
                      "hubReferenceWidth": 0.05, "hubScalePower": 1.5,
                      "bracketWeightFactor": 0.85, "bracketCostFactor": 1.25},
        # one per frequency: every frame style but Hubless Doubled is built on these edges, and
        # the browser shrinks each triangle for Hubless Doubled the way DomeModel.rebuild does
        "geometry": [geometry(f, "Hub & Strut") for f in [v for _l, v in creator_facts.axis("Frequency").values]],
        "hublessInset": 0.75, "hublessInsetCap": 0.4,
        "notes": {
            "Continuous Steel Arcs": "The Creator bills this frame for hub connectors its assembly never fits.",
            "Hex Cell": "The Creator prices this frame as hub-and-strut.",
            "Rebar Lattice": "The Creator bills this frame for hub connectors its assembly never fits.",
            "Concrete Formwork": "The Creator prices this frame as hub-and-strut.",
        },
    }


# ----------------------------------------------------------------------
# Test cases, with the Creator's own answers
# ----------------------------------------------------------------------

ANSWERS = ("height", "floor_area", "surface_area", "strut_count", "strut_total_len", "hub_count", "panel_count",
           "frame_weight", "frame_cost", "hub_weight", "hub_cost", "panel_weight", "panel_cost", "foundation_area",
           "foundation_weight", "foundation_cost", "structure_weight", "total_cost", "solar_watts", "bolt_count",
           "trees_required", "wall_cost", "wire_cost", "plumbing_cost", "prop_cost",
           "layer_weight", "layer_cost", "wall_count", "wall_area", "wall_weight", "wire_len", "pex_len", "drain_len",
           "prop_count", "prop_weight", "prop_watts", "trunk_stock_count", "assigned_sections", "hardware_screws",
           "wedge_splits", "wedge_log_diameter")


def fixtures(n: int = 240, seed: int = 11) -> list[dict]:
    t = tables()
    rnd = random.Random(seed)
    names = [l["name"] for l in t["layers"]]
    rooms = [r["name"] for r in t["fitout"]["rooms"]]
    props = [q["name"] for q in t["fitout"]["props"]]
    comps = [c["name"] for c in t["panelLab"]["components"]]
    out = []
    for i in range(n):
        c = {
            "frequency": rnd.choice(t["frequencies"]),
            "radius": rnd.choice(t["dials"]["Radius"]["values"]),
            "frameStyle": rnd.choice(t["frameStyles"]),
            "hubStyle": rnd.choice(t["hubStyles"]),
            "strutShape": rnd.choice(t["strutShapes"])["name"],
            "strutWidth": rnd.choice(t["dials"]["Strut width"]["values"]),
            "frameMaterial": rnd.choice(t["frameMaterials"])["name"],
            "panel": rnd.choice(t["panels"])["name"],
            "foundation": rnd.choice(t["foundations"])["name"],
            "foundationScale": rnd.choice(t["dials"]["Foundation size"]["values"]),
        }
        # the fit-out, layers, overrides and the rest, on most cases (the first 40 stay bare)
        geo = next(g for g in t["geometry"] if g["frequency"] == c["frequency"])
        custom = {}
        if i >= 40:
            fr = c["radius"]
            c.update({
                "wedgeOrientation": rnd.choice(t["wedgeOrientations"]),
                "layers": [rnd.choice(names) for _ in range(3)],
                "sections": [rnd.choice(rooms) for _ in range(10)],
                "partitions": rnd.choice(t["fitout"]["partitionModes"]),
                "props": [{"type": rnd.choice(props), "x": round(rnd.uniform(-0.8, 0.8) * fr, 2),
                           "y": round(rnd.uniform(-0.8, 0.8) * fr, 2), "yaw": float(rnd.randrange(0, 360, 15))}
                          for _ in range(rnd.randint(0, 9))],
                "trunkStockLength": rnd.choice([0.0, 2.4384, 3.6576, 6.096]),
            })
            if rnd.random() < 0.3:
                name = f"Custom Mk{i}"
                custom[name] = {"base": rnd.choice([p["name"] for p in t["panels"] if p["name"] != "Open"]),
                                "components": {rnd.choice(comps): rnd.randint(1, 6) for _ in range(rnd.randint(1, 3))}}
            pool = [p["name"] for p in t["panels"]] + list(custom)
            c["panelOverrides"] = {k: rnd.choice(pool) for k in rnd.sample(geo["panelKeys"], rnd.randint(0, min(12, len(geo["panelKeys"]))))}
            c["customPanels"] = custom
        if i == 0:
            c = dict(t["defaults"])
        cfg = creator_config(c)
        s = dome_model.DomeModel(cfg).stats()
        out.append({"config": c, "answers": {k: s[k] for k in ANSWERS},
                    "strutClasses": [[name, round(length, 2), count] for name, length, count in s["strut_classes"]],
                    "wedgePanels": [[r["name"], r["wedge_ft"], r["log_ft"]] for r in s["wedge_panel_rows"]]})
    return out


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--fixtures", type=Path)
    a = ap.parse_args()
    if a.fixtures:
        a.fixtures.write_text(json.dumps(fixtures(), indent=1), encoding="utf-8")
        print(f"wrote {a.fixtures}")
        return 0
    print(json.dumps(tables())[:400])
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
