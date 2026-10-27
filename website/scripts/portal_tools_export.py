"""The 3D Wedge Method and 3D Zome tools, as data a browser can use.

The Portal's two wedge spaces (website/src/world/wedge.ts, zome.ts) are the desktop tools
brought to the web, and a browser can run neither. So this exports what they compute from.

* **The wedge method** is `geodesic_raw_wedge_dome_dihedral.py`, the raw-wedge simulator,
  through `two_v_demo.raw_wedge_bridge`. Its solve is 400 lines of plane-cutting a browser
  does not need to repeat. So the simulator solves the dome itself, and this writes:
  * for each of its four wedge orientations, its own solved meshes, member by member
    (public/portal/wedge/<orientation>.bin), so the space shows the simulator's dome rather
    than a sketch of one;
  * the same for each alternating build (``orientation_pattern``: panels pointing in and out,
    so the sawn faces at a seam cancel), with `alternating_build.plan`'s reading of it --
    which way every panel points, the bands and the walk round each, every seam's pair, gap,
    fold and the degrees a matched seam costs against an in/out one;
  * the cut and seam tables over a grid of long edges and trunk diameters, for all of them.
* **The zome** is `wedge_zome.geometry`, which is small, exact plane geometry. The browser
  re-solves it (zome.ts) from the zonohedron and the wedge's cross-section, which come from
  here, and scripts/test_portal_tools.mjs checks that solve against
  `wedge_zome.fabrication.facts` itself.

    py -3.12 scripts/portal_tools_export.py --fixtures FILE   # zome test cases with the tool's answers
"""

from __future__ import annotations

import argparse
import json
import math
import random
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(ROOT))

import numpy as np  # noqa: E402

from two_v_demo import raw_wedge_bridge  # noqa: E402

WEDGE_MESH_DIR = ROOT / "website" / "public" / "portal" / "wedge"

# The zome app's own dial ranges (wedge_zome/app.py: log 6-24 in by 0.5, side 18-72 in by 1)
ZOME_LOGS = [6.0 + 0.5 * i for i in range(37)]
ZOME_SIDE = (18.0, 72.0, 1.0)

# The wedge method's grid: long edges and trunk diameters the cut tables are solved for
WEDGE_LONG = [48.0, 60.0, 72.0, 84.0, 96.0]
WEDGE_TRUNK = [6.0, 8.0, 10.0, 12.0, 14.0]

# The alternating builds the solver offers (orientation_pattern, pattern_ground_in), by the key
# the browser uses; "auto" is the solver's own choice of which ground panels point in.
PATTERNS = [
    ("alt_ground", "alternate_ground", "auto", "Alternating: the ground ring"),
    ("alt_ground_aaa", "alternate_ground", "AAA", "Alternating: the ground ring, AAA panels in"),
    ("alt_lower", "alternate_lower", "auto", "Alternating: the whole lower ring"),
    ("least_angle", "least_angle", "auto", "Alternating: every panel solved"),
]


# ----------------------------------------------------------------------
# The zome
# ----------------------------------------------------------------------

def zome_tables() -> dict:
    from square_book import geometry as sg
    from wedge_zome import geometry as zg

    z, ref_side = zg._zome()
    rim_h = float(z.rim_height)
    unit = (np.asarray(z.vertices, dtype=float) - np.array([0.0, 0.0, rim_h])) / float(z.strut_length)
    faces = [list(map(int, f)) for f in z.faces if min(unit[k][2] for k in f) >= -1e-6]
    logs = []
    for d in ZOME_LOGS:
        w = sg.Wedge(d, int(zg.D["splits"]))
        logs.append({"log": d, "theta": w.theta, "chordEff": w.chord_eff, "rEff": w.r_eff,
                     "square": sg.best_pair(w).planed[0],
                     "postSquare": sg.Pair(sg.Wedge(d, 4), "back").planed[0]})
    return {
        "_generated_by": "website/scripts/portal_tools_export.py from wedge_zome.geometry -- do not edit",
        "vertices": unit.tolist(), "faces": faces,
        "declared": [{"key": d.key, "value": d.value, "unit": d.unit, "kind": d.kind, "why": d.why} for d in zg.DECLARED],
        "kerf": sg.D["kerf_in"], "splits": int(zg.D["splits"]), "section": zg.D["section_in"],
        "logs": logs, "side": {"low": ZOME_SIDE[0], "high": ZOME_SIDE[1], "step": ZOME_SIDE[2], "reference": ref_side},
        "defaults": {"method": "wedge", "log": zg.D["log_in"], "side": round(ref_side, 2), "hand": "ccw", "orient": "back"},
    }


def _zome_answers(method: str, log: float, side: float, hand: str, orient: str) -> dict:
    from wedge_zome import fabrication as fab
    from wedge_zome import geometry as zg

    m = zg.build(method, log, side, hand, orient)
    f = fab.facts(method, m)
    keep = ("panels", "seams", "gap_lo", "gap_hi", "fold_lo", "fold_hi", "posts", "post_h", "rim_corners",
            "stick_w", "stick_h", "theta", "side", "height_ft", "rim_ft", "post_square")
    return {
        **{k: f[k] for k in keep},
        "stock": f["stock"], "other_stock": f["other_stock"],
        "rows": f["rows"],
        "types": [{"name": t["name"], "row": t["row"], "count": t["count"], "outer": t["outer"], "lengths": t["lengths"],
                   "tail": list(t["tail"]), "head": list(t["head"]), "longest": t["longest"]} for t in f["types"]],
        "blocks": f["blocks"],
    }


def zome_fixtures(n: int = 60, seed: int = 7) -> list[dict]:
    t = zome_tables()
    rnd = random.Random(seed)
    sides = [t["side"]["low"] + i * t["side"]["step"] for i in range(int((t["side"]["high"] - t["side"]["low"]) / t["side"]["step"]) + 1)]
    out = []
    for i in range(n):
        c = {"method": rnd.choice(["wedge", "square"]), "log": rnd.choice(ZOME_LOGS), "side": rnd.choice(sides),
             "hand": rnd.choice(["ccw", "cw"]), "orient": rnd.choice(["back", "point"])}
        if i == 0:
            c = dict(t["defaults"])
        out.append({"config": c, "answers": _zome_answers(c["method"], c["log"], c["side"], c["hand"], c["orient"])})
    return out


# ----------------------------------------------------------------------
# The wedge method
# ----------------------------------------------------------------------

def _mean(xs):
    xs = list(xs)
    return sum(xs) / len(xs)


def wedge_summary(model) -> dict:
    """What the space's tables show for one solved dome: the simulator's own fields."""
    sim = raw_wedge_bridge.simulator()
    cfg = model.config
    area = sim._sector_area_in2(model)
    out = {"members": len(model.members), "seams": len(model.seams), "joints": len(model.joints),
           "nodes": len(model.topology.vertices), "panels": len(model.topology.faces),
           "sphereRadius": model.topology.sphere_radius_in, "shortEdge": model.topology.short_edge_in,
           "longEdge": model.topology.long_edge_in, "sectorArea": area, "families": []}
    for t in ("A", "B"):
        ms = [m for m in model.members if m.edge_type == t]
        ss = [s for s in model.seams if s.edge_type == t]
        out["families"].append({
            "type": t, "count": len(ms), "nominal": _mean(m.nominal_length_in for m in ms),
            "blankMin": min(m.physical_stock_length_in for m in ms), "blankMax": max(m.physical_stock_length_in for m in ms),
            "axisMean": _mean(m.physical_axis_length_in for m in ms),
            "buttSetback": _mean(m.butt_setback_in for m in ms),
            "receivingSetback": _mean(m.receiving_axis_setback_in for m in ms),
            "seams": len(ss),
            "fold": _mean(s.fold_angle_deg for s in ss) if ss else None,
            "gap": _mean(s.raw_gap_angle_deg for s in ss) if ss else None,
            "keyBase": _mean(s.spacer_base_width_in for s in ss) if ss else None,
        })
    vol_in3 = sum(m.volume_equivalent_length_in for m in model.members) * area
    out["stockIn"] = sum(m.physical_stock_length_in for m in model.members)
    out["volumeFt3"] = vol_in3 / 1728.0
    out["dryLb"] = out["volumeFt3"] * cfg.dry_wood_density_lb_ft3
    out["greenLb"] = out["volumeFt3"] * cfg.green_wood_density_lb_ft3
    out["headOffcutIn"] = len(model.members) * cfg.head_overfit_in
    out["logsAtSplits"] = math.ceil(len(model.members) / cfg.radial_splits)
    return out


def _palette(rgba: np.ndarray, palette: list) -> np.ndarray:
    keys = [tuple(round(float(x), 3) for x in c[:3]) for c in rgba]
    for k in keys:
        if k not in palette:
            palette.append(k)
    where = {k: i for i, k in enumerate(palette)}
    return np.array([where[k] for k in keys], dtype=np.uint8)


def pack(parts: list[tuple[dict, object]], name: str) -> tuple[bytes, dict]:
    """Meshes quantised for the web, one file. Layout: int16 x,y,z per vertex (inches =
    q * scale, z up), a uint8 colour index per vertex padded to 2 bytes, then uint16
    triangle indices. Each part's header says where its vertices and indices lie."""
    verts, cols, idx, header = [], [], [], []
    palette: list = []
    base = ibase = 0
    for head, md in parts:
        v = np.asarray(md.vertices, dtype=np.float64).reshape(-1, 10)
        ix = np.asarray(md.indices, dtype=np.int64)
        header.append({**head, "v": [base, len(v)], "i": [ibase, len(ix)]})
        if not len(v):
            continue
        verts.append(v[:, 0:3])
        cols.append(_palette(v[:, 6:10], palette))
        idx.append(ix + base)
        base += len(v)
        ibase += len(ix)
    if base > 65535:
        raise ValueError(f"{name}: {base} vertices will not index in uint16")
    pos = np.concatenate(verts)
    scale = float(np.abs(pos).max()) / 32767.0
    q = np.round(pos / scale).astype("<i2")
    col = np.concatenate(cols)
    tri = np.concatenate(idx).astype("<u2")
    blob = q.tobytes() + col.tobytes() + (b"\0" if len(col) % 2 else b"") + tri.tobytes()
    return blob, {"file": f"/portal/wedge/{name}.bin", "vertices": base, "indices": int(len(tri)), "scale": scale,
                  "palette": [list(c) for c in palette], "parts": header, "bytes": len(blob)}


def wedge_mesh_file(orientation: str, model=None) -> tuple[bytes, dict]:
    """The simulator's own solved dome, member by member: each member, its head offcut
    (the stock flush-cut away on the jig) and each seam key."""
    sim = raw_wedge_bridge.simulator()
    model = model if model is not None else raw_wedge_bridge.model(orientation)

    def one(fn, *args):
        acc = sim.MeshAccumulator()
        fn(acc, model, *args)
        return acc.finish()

    parts = [({"kind": "member", "id": m.member_id, "face": m.face_index, "type": m.edge_type,
               "nominal": m.nominal_length_in, "blank": m.physical_stock_length_in, "axis": m.physical_axis_length_in,
               "butt": m.butt_setback_in, "receiving": m.receiving_axis_setback_in,
               "receives": m.receives_member_id, "buttInto": m.butt_into_member_id}, one(sim.add_raw_sector_member, m))
             for m in model.members]
    parts += [({"kind": "offcut", "id": m.member_id, "face": m.face_index}, one(sim.add_head_overfit, m)) for m in model.members]
    parts += [({"kind": "key", "id": s.seam_id, "type": s.edge_type, "faces": [s.face_a, s.face_b],
                "fold": s.fold_angle_deg, "gap": s.raw_gap_angle_deg, "keyBase": s.spacer_base_width_in}, one(sim.add_rigid_spacer, s))
              for s in model.seams]
    blob, head = pack(parts, orientation)
    head["faceNormals"] = [[float(x) for x in f.normal] for f in model.topology.faces]
    head["faceCentres"] = [[float(x) for x in f.center] for f in model.topology.faces]
    return blob, head


def pattern_plan(plan) -> dict:
    """alternating_build.plan's reading of one mixed dome, for the browser."""
    word = {"point_dome_in": "in", "point_dome_out": "out"}
    return {
        "ground": plan.ground_in,
        "panels": [{"type": q.face_type, "band": q.band, "walk": q.walk, "points": word[q.orientation],
                    "height": q.height_in} for q in plan.panels],
        "seams": [{"id": q.seam_id, "type": q.edge_type, "a": q.a, "b": q.b, "pair": q.pair, "gap": q.gap_deg,
                   "fold": q.fold_deg, "alt": q.alt_gap_deg, "extra": q.extra_deg, "key": q.key_width_in, "band": q.band}
                  for q in plan.seams],
        "bands": [{"band": b, "panels": ring, "summary": plan.band_summary(b)} for b, ring in sorted(plan.bands.items())],
        "rings": plan.vertex_rings,
        "matched": len(plan.matched()), "extraDeg": plan.total_extra_deg(), "pairs": dict(plan.counts()),
    }


JIG_PANEL = 5          # the panel the simulator's own jig walk-through and the film use


def jig_file() -> tuple[bytes, dict]:
    """The simulator's jig, stage by stage, for one panel of the default dome."""
    sim = raw_wedge_bridge.simulator()
    model = raw_wedge_bridge.model()
    parts, lines = [], []
    for st in range(len(sim.JIG_STAGES)):
        got = sim.build_fabrication_jig(model, JIG_PANEL, st)
        for kind in ("jig_fixture", "jig_wood", "jig_hangoff", "jig_head_overfit"):
            parts.append(({"stage": st, "kind": kind}, got[kind]))
        lv = np.asarray(got["jig_lines"].vertices, dtype=np.float64)
        lv = lv.reshape(-1, lv.shape[-1] if lv.ndim > 1 else 7) if len(lv) else lv
        lines.append([[round(float(x), 3) for x in r[:3]] + [round(float(x), 3) for x in r[3:6]] for r in lv])
    blob, head = pack(parts, "jig")
    head["lines"] = lines
    head["panel"] = JIG_PANEL
    return blob, head


def _trim(x):
    """Seven significant figures: the tables are read by eye and the meshes are int16 anyway."""
    if isinstance(x, float):
        return float(f"{x:.7g}")
    if isinstance(x, dict):
        return {k: _trim(v) for k, v in x.items()}
    if isinstance(x, (list, tuple)):
        return [_trim(v) for v in x]
    return x


def wedge_tables() -> tuple[dict, dict[Path, bytes]]:
    """The tables, and the mesh files to write beside them (public/portal/wedge/)."""
    sim = raw_wedge_bridge.simulator()
    orients = list(raw_wedge_bridge.orientations())
    defaults = sim.DomeConfig()
    grid = {}
    for o in orients:
        for L in WEDGE_LONG:
            for d in WEDGE_TRUNK:
                grid[f"{o}|{L:g}|{d:g}"] = wedge_summary(raw_wedge_bridge.model(o, "raw_trapezoid", L, d))
    from alternating_build import plan as alt
    for key, pattern, ground, _label in PATTERNS:
        for L in WEDGE_LONG:
            for d in WEDGE_TRUNK:
                pl = alt.plan(pattern, ground, L, d)
                grid[f"{key}|{L:g}|{d:g}"] = {**wedge_summary(pl.model), "matched": len(pl.matched()),
                                              "extraDeg": pl.total_extra_deg(), "pairs": dict(pl.counts())}
    meshes, files = {}, {}
    for o in orients:
        blob, head = wedge_mesh_file(o)
        meshes[o] = head
        files[WEDGE_MESH_DIR / f"{o}.bin"] = blob
    patterns = []
    for key, pattern, ground, label in PATTERNS:
        pl = alt.plan(pattern, ground)
        blob, head = wedge_mesh_file(key, pl.model)
        meshes[key] = head
        files[WEDGE_MESH_DIR / f"{key}.bin"] = blob
        patterns.append({"key": key, "pattern": pattern, "label": label, "blurb": alt.PATTERNS[pattern], **pattern_plan(pl)})
    # what the matched (in/in) seam costs on each edge type, uniform builds for comparison
    uniform_gaps = {o: {t: next(f["gap"] for f in grid[f"{o}|{defaults.long_edge_in:g}|{defaults.trunk_diameter_in:g}"]["families"] if f["type"] == t)
                        for t in ("A", "B")} for o in orients}
    blob, jig = jig_file()
    files[WEDGE_MESH_DIR / "jig.bin"] = blob
    labels = {"point_dome_in": "Point to the dome's centre", "point_panel_in": "Point into its own panel",
              "point_dome_out": "Point to the sky", "point_panel_out": "Point across the seam"}
    return {
        "_generated_by": "website/scripts/portal_tools_export.py from geodesic_raw_wedge_dome_dihedral.py -- do not edit",
        "orientations": [{"key": o, "label": labels.get(o, o), "reading": sim.SEAM_PAIR_READING[o],
                          "receiver": sim.pinwheel_receiver_surface_label(sim.DomeConfig(wedge_orientation=o))}
                         for o in orients],
        "jigStages": [{"slug": s, "title": t, "see": see, "does": does} for s, t, see, does in sim.JIG_STAGES],
        "longEdges": WEDGE_LONG, "trunks": WEDGE_TRUNK,
        "defaults": {"orientation": defaults.wedge_orientation, "longEdge": defaults.long_edge_in,
                     "trunk": defaults.trunk_diameter_in},
        "declared": {"splits": defaults.radial_splits, "headOverfit": defaults.head_overfit_in,
                     "dryDensity": defaults.dry_wood_density_lb_ft3, "greenDensity": defaults.green_wood_density_lb_ft3,
                     "keyNose": defaults.trapezoid_nose_depth_in},
        "grid": _trim(grid), "meshes": _trim(meshes), "jig": _trim(jig),
        "patterns": _trim(patterns), "uniformGaps": _trim(uniform_gaps),
    }, files


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--fixtures", type=Path)
    a = ap.parse_args()
    if a.fixtures:
        a.fixtures.write_text(json.dumps(zome_fixtures()), encoding="utf-8")
        print(f"wrote {a.fixtures}")
        return 0
    print(json.dumps(zome_tables())[:300])
    w, _files = wedge_tables()
    print({o: (h["vertices"], h["indices"], h["bytes"]) for o, h in w["meshes"].items()})
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
