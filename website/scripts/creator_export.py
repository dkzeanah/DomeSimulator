"""The Dome Creator, as tables a browser can use.

The Portal's Dome Creator space (website/src/world/creator.ts) is the desktop tool
(dome_creator.py, on dome_model.DomeModel) brought to the web. A browser cannot run the
Creator, so this exports what it computes from: its menus and dial ranges (read from the
tool, via two_v_demo.creator_facts), its material tables, every strut shape's cross
section at every width the dial allows (the Creator's own function, evaluated), and the
dome's geometry at unit radius for every frequency and both kinds of frame (struts scale
with the radius, panel areas with its square). The browser then does only the Creator's
arithmetic -- DomeModel.stats() for a dome without fit-out -- and scripts/test_creator.mjs
checks that arithmetic against stats() itself.

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
        # the drawing: unit-sphere nodes and the edges and faces between them (z up)
        "vertices": [[_r(c, 10) for c in v] for v in (m.world_verts - centre)],
        "edges": [[int(a), int(b)] for a, b in geo.edges],
        "faces": [[int(i) for i in f] for f in geo.faces],
    }


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
        "strutShapes": [{"name": s.name, "kind": s.kind,
                         "section": {f"{w:.4f}": float(s.cross_section_area(w)) for w in widths}}
                        for s in materials.STRUT_SHAPES],
        "frameMaterials": [{"name": f.name, "density": f.density, "costPerKg": f.cost_per_kg,
                            "hubWeight": f.hub_weight, "hubCost": f.hub_cost} for f in materials.FRAME_MATERIALS],
        "panels": [{"name": p.name, "areaWeight": p.area_weight, "costPerM2": p.cost_per_m2,
                    "wattsPerM2": p.watts_per_m2} for p in materials.PANEL_TYPES],
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
           "trees_required", "wall_cost", "wire_cost", "plumbing_cost", "prop_cost")


def fixtures(n: int = 160, seed: int = 11) -> list[dict]:
    t = tables()
    rnd = random.Random(seed)
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
        if i == 0:
            c = dict(t["defaults"])
        cfg = dome_model.DomeConfig.from_dict({
            "frequency": c["frequency"], "radius": c["radius"], "frame_style": c["frameStyle"], "hub_style": c["hubStyle"],
            "strut_shape": c["strutShape"], "strut_width": c["strutWidth"], "frame_material": c["frameMaterial"],
            "default_panel": c["panel"], "foundation": c["foundation"], "foundation_scale": c["foundationScale"]})
        s = dome_model.DomeModel(cfg).stats()
        out.append({"config": c, "answers": {k: s[k] for k in ANSWERS},
                    "strutClasses": [[name, round(length, 2), count] for name, length, count in s["strut_classes"]]})
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
