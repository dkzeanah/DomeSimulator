"""The Panel Creator, Cell Wall & Seams and Masterclass Theatre spaces, as data a browser can use.

* **Panel Creator** is the Triangle Infill tool (infill/) as `two_v_demo.infill_dome` puts it on
  the whole dome: its 41 ways to fill a triangle (the owner's pairs and the tool's patterns, filling
  or covering), each panel type's pieces meshed by the tool's own mesher and cut to the opening's
  walls, each piece's numbers and saw recipe, and the forty seats the panels take on the dome. The
  meshes and the piece tables go to public/portal/infill/ (fetched one way at a time); the list of
  ways, their whole-dome figures and the seats are bundled.
* **Cell Wall & Seams** is `two_v_demo.cell_wall` and `two_v_demo.seam_climate`: the layer stack,
  the router's scenarios and interlocks, the seam controller's constants, modes and the owner's
  weathers, the dome's seam bands, every function's own computed check (foam, glue, vacuum,
  rain, fire, filter, heat, cool, cage, fog, flotation, living surface, the local net, the bus,
  the extras), and the reference dome itself -- its nodes, triangles and seams, each seam's band,
  the rim ports and belt low points, the lower triangles and every triangle's hops from the rim
  -- so the stage draws the skin on the solver's dome. The browser re-runs the small exact parts -- the dew point,
  the controller's three questions, the wall's temperature profile, the interlocks -- and
  scripts/test_portal_spaces.mjs checks them against the Python.
* **Dome Assembly Line** is `al_build`: each product line's dome built element by element at its
  stations (every element's mesh, material cost, labor and weight), and the editable assumptions
  its unit economics, throughput and break-even are worked from. The browser re-runs those sums
  (crew and wage change them) and scripts/test_portal_spaces.mjs checks them against `al_build`.
  For the factory floor (`assembly_line.py`, the desktop demo): a run of production specs drawn
  by `al_build.random_spec` from a fixed seed -- each its own catalog, mesh and elements, with the
  floor point a worker carries each element to -- and the demo's pacing, phases, disruptions and
  cost-sensitivity factors.
* **Foundation & Pads** is `world3d.structures` (the pentagon of half trunks, its star, its piers,
  its deck and its layout on the ground, as the solver builds them) and `pad_deck` (the platform a
  seed dome stands on, priced board by board from the lumber receipt, five ways, over a range of
  sizes).
* **Masterclass Theatre** is every lesson the masterclass renderer can play
  (`two_v_demo.lesson_registry`), chapter by chapter: titles, promises, narration and the
  equations each film's own code computes.

    py -3.12 scripts/portal_spaces_export.py --fixtures FILE   # test cases with the Python's answers
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

INFILL_DIR = ROOT / "website" / "public" / "portal" / "infill"


def _trim(x, sig: int = 7):
    if isinstance(x, float):
        return float(f"{x:.{sig}g}") if math.isfinite(x) else None
    if isinstance(x, dict):
        return {str(k): _trim(v, sig) for k, v in x.items()}
    if isinstance(x, (list, tuple)):
        return [_trim(v, sig) for v in x]
    if isinstance(x, (np.floating,)):
        return _trim(float(x), sig)
    if isinstance(x, (np.integer,)):
        return int(x)
    if isinstance(x, np.ndarray):
        return _trim(x.tolist(), sig)
    return x


def _palette(rgb: np.ndarray, palette: list) -> np.ndarray:
    keys = [tuple(round(float(x), 3) for x in c[:3]) for c in rgb]
    for k in keys:
        if k not in palette:
            palette.append(k)
    where = {k: i for i, k in enumerate(palette)}
    return np.array([where[k] for k in keys], dtype=np.uint8)


def pack_rows(chunks: list[np.ndarray], name: str, folder: str) -> tuple[bytes, dict, list[list[int]]]:
    """Triangle rows (x y z, normal, rgba; three per triangle) quantised for the web: int16 x,y,z
    per vertex, then a uint8 colour index per vertex. Returns the file, its header and where each
    chunk's vertices lie."""
    palette: list = []
    pos, col, ranges, base = [], [], [], 0
    for rows in chunks:
        rows = np.asarray(rows, dtype=np.float64).reshape(-1, 10)
        ranges.append([base, len(rows)])
        if len(rows):
            pos.append(rows[:, 0:3])
            col.append(_palette(rows[:, 6:9], palette))
        base += len(rows)
    p = np.concatenate(pos) if pos else np.zeros((0, 3))
    scale = float(np.abs(p).max()) / 32767.0 if len(p) else 1.0
    blob = np.round(p / scale).astype("<i2").tobytes() + (np.concatenate(col).tobytes() if col else b"")
    return blob, {"file": f"/portal/{folder}/{name}.bin", "vertices": base, "scale": scale,
                  "palette": [list(c) for c in palette]}, ranges


# ----------------------------------------------------------------------
# Panel Creator
# ----------------------------------------------------------------------

def _recipe(r) -> dict:
    return {"number": r.number, "name": r.name, "summary": r.summary, "dims": [list(d) for d in r.dims],
            "steps": [{"kind": s.kind, "title": s.title, "text": s.text} for s in r.steps]}


def infill_variant(v) -> tuple[bytes, dict, dict]:
    """One way to fill: both panel types' pieces, meshed, numbered, with their cuts."""
    from infill import recipes as rc
    from infill import solids as so
    from two_v_demo import infill_dome as idm

    chunks, kinds = [], []
    for kind in range(len(idm.types())):
        table: dict = {"kind": kind, "pieces": [], "recipes": [], "metrics": {}, "steps": [], "fitting": []}
        if v.family == "pairs":
            for i, (s, col, q) in enumerate(idm.pair_solids(kind, v.p)):
                chunks.append(idm._solid_rows(s, col))
                long, short = so.length(s)
                table["pieces"].append({"n": i + 1, "name": f"pair {i // 2 + 1}, wedge {'AB'[i % 2]}",
                                        "group": f"pair {i // 2 + 1}", "pose": "pair", "long": long, "short": short,
                                        "cuts": "cut to the opening's walls, planed flush with both faces",
                                        "note": f"overlap {q:.2f} (1 nested, 0 bowtie)"})
        else:
            L = idm.pattern_layout(kind, v.arrangement, v.lay, v.mode)
            for i, piece in enumerate(L.pieces):
                c = idm._piece_colour(piece)
                shade = 1.0 if i % 2 == 0 else 0.86
                chunks.append(idm._solid_rows(piece.solid, (c[0] * shade, c[1] * shade, c[2] * shade, c[3])))
                table["pieces"].append({"n": i + 1, "name": piece.group, "group": piece.group, "pose": piece.pose,
                                        "long": float(piece.long), "short": float(piece.short),
                                        "cuts": piece.cut_text, "note": piece.note})
            table["recipes"] = [_recipe(r) for r in rc.recipes(L)]
            prep = rc.prep_card(L)
            table["prep"] = _recipe(prep) if prep else None
            table["metrics"] = {k: val for k, val in L.metrics.items() if isinstance(val, (int, float, str))}
            table["steps"], table["fitting"] = list(L.steps), list(L.fitting)
        kinds.append(table)
    blob, head, ranges = pack_rows(chunks, v.key, "infill")
    k = 0
    for table in kinds:
        for piece in table["pieces"]:
            piece["v"] = ranges[k]
            k += 1
    return blob, head, {"key": v.key, "title": v.title, "kinds": _trim(kinds)}


def panel_creator() -> tuple[dict, dict[Path, bytes]]:
    from infill.frame import solve
    from two_v_demo import infill_dome as idm

    files: dict[Path, bytes] = {}
    blob, frames, ranges = pack_rows([idm.frame_rows(k) for k in range(len(idm.types()))], "frames", "infill")
    frames["kinds"] = ranges
    files[INFILL_DIR / "frames.bin"] = blob
    ways = []
    for v in idm.variants():
        blob, head, table = infill_variant(v)
        files[INFILL_DIR / f"{v.key}.bin"] = blob
        files[INFILL_DIR / f"{v.key}.json"] = (json.dumps(table, separators=(",", ":"), ensure_ascii=False) + "\n").encode("utf-8")
        f = idm.facts(v.key)
        ways.append({"key": v.key, "title": v.title, "family": v.family, "arrangement": v.arrangement,
                     "lay": v.lay, "mode": v.mode, "mesh": head, "table": f"/portal/infill/{v.key}.json",
                     "pieces": f["pieces"], "feet": f["feet"], "solid": f["solid"], "leftSqft": f["left_sqft"],
                     "planedOff": idm.planed_off(v.p) if v.family == "pairs" and v.p != "dial" else None})
    s = idm.spec()
    sol = solve(s)
    types = [{"name": t.name, "label": t.label, "count": t.count, "edgeClass": list(t.edge_class),
              "edgeLen": list(t.edge_len), "memberLen": list(t.member_len), "tri": t.tri.tolist()} for t in idm.types()]
    return _trim({
        "_generated_by": "website/scripts/portal_spaces_export.py from infill/ and two_v_demo.infill_dome -- do not edit",
        "ways": ways, "frames": frames, "types": types, "counts": idm.counts(),
        "seats": [{"kind": st.kind, "origin": st.origin.tolist(), "basis": st.basis.tolist()} for st in idm.seats()],
        "radiusIn": idm.radius_in(),
        "spec": {"longestIn": s.max_strut_in, "frameLogIn": s.frame_log_in, "splits": s.splits,
                 "thicknessIn": s.thickness_in, "wallDeg": s.wall_deg},
        "dome": {"panels": len(idm.seats()), "radiusIn": float(sol["radius_in"])},
    }), files


# ----------------------------------------------------------------------
# Cell Wall & Seams
# ----------------------------------------------------------------------

def _constants(rows) -> list[dict]:
    return [{"key": k, "value": v, "unit": u, "kind": kind, "why": why} for k, v, u, kind, why in rows]


def cell_wall() -> dict:
    from two_v_demo import cell_wall as cw
    from two_v_demo import seam_climate as scl

    r = scl.rings()
    n = cw.networks()
    profile_inputs = {"room_c": cw.C["room_c"], "winter_out_c": cw.C["winter_out_c"],
                      "film_in_rsi": cw.C["film_in_rsi"], "film_out_rsi": cw.C["film_out_rsi"], "core_rsi": cw.core_rsi()}
    return _trim({
        "_generated_by": "website/scripts/portal_spaces_export.py from two_v_demo.cell_wall and two_v_demo.seam_climate -- do not edit",
        "climate": {
            "constants": _constants(scl.CONSTANTS),
            "modes": [{"key": k, "path": path, "why": why} for k, (path, why) in scl.MODES.items()],
            "activeModes": list(scl.ACTIVE_MODES),
            "scenarios": [{"key": sc.key, "label": sc.label, "want": list(sc.want), "why": sc.why,
                           "sensors": {"t_in": sc.sensors.t_in, "rh_in": sc.sensors.rh_in, "t_out": sc.sensors.t_out,
                                       "rh_out": sc.sensors.rh_out, "t_seam": sc.sensors.t_seam, "rh_seam": sc.sensors.rh_seam,
                                       "wood_mc": sc.sensors.wood_mc, "rain": sc.sensors.rain, "harvest": sc.sensors.harvest,
                                       "cooling": sc.sensors.cooling}} for sc in scl.SCENARIOS],
            "bands": [{"key": b.key, "label": b.label, "seams": b.seams, "lengthFt": b.length_ft, "slopeDeg": b.slope_deg,
                       "drains": b.drains} for b in r["bands"]],
            "beltLowPoints": r["belt_low_points"], "rimPorts": r["rim_ports"], "apexFt": r["apex_height_ft"],
            "meridianFt": r["meridian_ft"], "stackPa": scl.stack_pa(),
        },
        "wall": {
            "constants": _constants(cw.CONSTANTS),
            "layers": [{"key": l.key, "label": l.label, "side": l.side, "medium": l.medium, "modes": list(l.modes),
                        "kind": l.kind, "rsi": l.rsi, "colour": list(l.colour), "job": l.job,
                        "thicknessMm": cw.thickness_mm(l.key), "construction": list(cw.CONSTRUCTION[l.key])}
                       for l in cw.LAYERS],
            "ownerStack": list(cw.OWNER_STACK),
            "profileInputs": profile_inputs,
            "routes": [list(x) for x in cw.ROUTES],
            "scenarios": [{"key": k, "label": label, "modes": modes} for k, label, modes in cw.SCENARIOS],
            "skin": cw.skin(), "complexity": cw.complexity(),
            "heatSplit": {"room": cw.heat_split("room"), "osb": cw.heat_split("osb")},
            "networks": {"triangles": n.triangles, "seams": n.seams},
            # every function's own check, with the layer it belongs to
            "checks": [{"key": key, "title": title, "layer": layer, "figures": _plain(getattr(cw, key)())}
                       for key, title, layer in CELL_CHECKS],
        },
        "dome": _cell_dome(),
    }, 17)          # full precision: the browser re-runs these and is tested against the Python


# The cell wall's checks, each with the layer it belongs to ("" for the whole wall)
CELL_CHECKS = (
    ("groove", "The groove in each strut", "core"), ("seam_room", "What fits in a seam", "core"),
    ("foam", "Foam in the cavity", "core"), ("glue", "Glue: flood and bead", "core"),
    ("vacuum", "Vacuum: the clamp", "vacuum"), ("rain", "Rain to the tank", "water"),
    ("fire", "Fire water: the sprinkler", "water"), ("fire_evap", "Fire water: evaporating it", "water"),
    ("air_filter", "The intake filter", "filter"), ("vent_dry", "Drying a wet cavity by vent", "air_in"),
    ("heating", "Heating", "thermal"), ("cooling", "Cooling", "thermal"),
    ("cage", "The Faraday cage", "cage"), ("fog", "Fog out, smoke in", "fog"),
    ("flotation", "Flotation", "airbag"), ("living", "The living surface", "living"),
    ("local_net", "The local net: cell to cell", "bus"), ("bus", "The CAN bus", "bus"),
    ("extras", "And the rest", ""), ("multipliers", "What one wall does", ""),
)


def _plain(x):
    """A check's figures as JSON: dicts and lists through, numpy numbers to floats."""
    if isinstance(x, dict):
        return {str(k): _plain(v) for k, v in x.items()}
    if isinstance(x, (list, tuple)):
        return [_plain(v) for v in x]
    if isinstance(x, (bool, str)) or x is None:
        return x
    try:
        return float(x)
    except (TypeError, ValueError):
        return str(x)


def _cell_dome() -> dict:
    """The reference dome the cell wall is reckoned on (channel_facts.reference_model): inches, z up."""
    from two_v_demo import cell_wall as cw
    from two_v_demo import channel_facts as cf
    from two_v_demo import seam_climate as scl
    model = cf.reference_model()
    topo = model.topology
    band_of = {}
    for key, seams in scl.classify(model).items():
        for q in seams:
            band_of[q.seam_id] = key
    r = topo.sphere_radius_in
    levels = sorted({round(float(v[2]) / r, 3) for v in topo.vertices})
    level = lambda v: round(float(v[2]) / r, 3)
    hops = cw.local_net()["hops"]
    return {
        "radiusIn": float(r),
        "vertices": [[float(c) for c in v] for v in topo.vertices],
        "faces": [{"v": [int(i) for i in f.vertices], "type": f.face_type, "hops": int(hops.get(f.index, hops.get(str(f.index), -1)))}
                  for f in topo.faces],
        "seams": [{"id": q.seam_id, "v": [int(q.edge_key[0]), int(q.edge_key[1])], "type": q.edge_type, "band": band_of.get(q.seam_id, ""),
                   "faces": [int(q.face_a), int(q.face_b)]} for q in model.seams],
        "rimPorts": [i for i, v in enumerate(topo.vertices) if level(v) == levels[0]],
        "lowPoints": [i for i, v in enumerate(topo.vertices) if level(v) == levels[1]],
        "lowerFaces": [int(i) for i in cw.lower_faces()],
    }


# ----------------------------------------------------------------------
# Dome Assembly Line
# ----------------------------------------------------------------------

AL_DIR = ROOT / "website" / "public" / "portal" / "assembly"


def _al_spec(dtype: str, layout: str | None = None):
    import al_build as A
    t = A.DOME_TYPES[dtype]
    return A.DomeSpec(serial=1, name=t.name, dtype=dtype, radius=round(sum(t.radius_range) / 2, 2),
                      frequency=t.freq_choices[0], layout=layout or ("1-Bedroom" if dtype == "home" else "Studio"))


def _al_line(dtype: str, layout: str | None = None) -> tuple[bytes, dict]:
    """One product line's dome, element by element: its mesh, and what each element costs. A home
    is built differently for each layout (its interior), so each layout is its own catalog."""
    spec = _al_spec(dtype, layout)
    return _al_line_from(spec, f"{dtype}-{spec.layout.lower()}")


def _al_line_from(spec, name: str) -> tuple[bytes, dict]:
    import al_build as A
    dtype = spec.dtype
    cat, _info = A.build_dome_catalog(spec)
    verts = np.asarray(cat.b.vertices, dtype=np.float64).reshape(-1, 11)
    opaque = np.asarray(cat.b.opaque, dtype=np.int64)
    trans = np.asarray(cat.b.transparent, dtype=np.int64)
    if len(verts) > 65535:
        raise ValueError(f"{dtype}: {len(verts)} vertices will not index in uint16")
    palette: list = []
    col = _palette(verts[:, 6:9], palette)
    scale = float(np.abs(verts[:, 0:3]).max()) / 32767.0
    q = np.round(verts[:, 0:3] / scale).astype("<i2")
    alpha = np.round(verts[:, 9] * 255).astype(np.uint8)
    blob = q.tobytes() + col.tobytes() + alpha.tobytes()
    blob += b"\0" * (len(blob) % 2)
    blob += opaque.astype("<u2").tobytes() + trans.astype("<u2").tobytes()
    elements = [{"stage": e.stage, "category": e.category, "label": e.label, "cost": e.material_cost,
                 "labor": e.labor_min, "weight": e.weight, "o": [e.o0, e.o1], "t": [e.t0, e.t1],
                 "at": [float(x) for x in e.centroid], "fp": [float(e.floor_point[0]), float(e.floor_point[1])]} for e in cat.elements]
    t = spec.type
    return blob, {
        "key": dtype, "name": t.name, "tagline": t.tagline, "stages": [st.key for st in spec.stages],
        "radius": spec.radius, "frequency": spec.frequency, "layout": spec.layout, "floorArea": spec.floor_area,
        "priceBase": t.price_base, "pricePerM2": t.price_per_m2, "elements": elements,
        "mesh": {"file": f"/portal/assembly/{name}.bin", "vertices": int(len(verts)), "opaque": int(len(opaque)),
                 "transparent": int(len(trans)), "scale": scale, "palette": [list(c) for c in palette]},
    }


AL_RUNS = 12          # production specs exported for the factory floor
AL_SEED = 2026        # the seed they are drawn with, so the run is the same every export


def _al_run(spec, n: int) -> tuple[bytes, dict, dict]:
    """One production spec as the factory builds it: mesh blob, head (in lines.json) and its elements."""
    import al_build as A
    blob, head = _al_line_from(spec, f"run-{n}")
    head.update({"serial": spec.serial, "model": spec.name, "cladding": spec.cladding, "claddingRgb": list(spec.cladding_color),
                 "accent": list(spec.accent), "floorR": spec.floor_radius, "price": spec.sale_price, "monthly": spec.monthly_payment,
                 "elementsFile": f"/portal/assembly/run-{n}.json"})
    elements = head.pop("elements")
    return blob, head, {"elements": elements}


def _factory() -> dict:
    """The desktop demo's pacing (assembly_line.py), read from it where it is code."""
    import assembly_line as AL
    phases = [{"kind": ph.kind, "station": ph.station, "dur": ph.dur} for ph in AL.build_phases()]
    return {
        "placeAnimPerLaborMin": AL.PLACE_ANIM_PER_LABOR_MIN, "walkSpeed": AL.ANIM_WALK_SPEED, "travelSecs": AL.TRAVEL_SECS,
        "phases": phases,
        # assembly_line.App.inject: what each disruption does to the line
        "disruptions": [{"key": "supply", "label": "Supply delay", "stall": 6.0, "note": "the station starved for 6 minute-equivalents"},
                        {"key": "breakdown", "label": "Machine breakdown", "stall": 8.0, "note": "maintenance responding"},
                        {"key": "absence", "label": "Worker absence", "crew": -1, "note": "the station's crew one short"}],
        # assembly_line.App._econ_with_sensitivity: which costs each factor moves, and cycle_sensitivity's steps
        "sensitivity": {"lumber": ["frame", "floor", "hub"], "resin": ["fiberglass", "shingle", "wrap"], "wage": [],
                        "levels": [1.0, 1.2, 0.85]},
    }


def assembly_line() -> tuple[dict, dict[Path, bytes]]:
    import random
    import al_build as A
    files, lines = {}, []
    for dtype in A.DOME_TYPE_LIST:
        for layout in (A.LAYOUTS if dtype == "home" else [None]):
            blob, head = _al_line(dtype, layout)
            files[AL_DIR / f"{dtype}-{head['layout'].lower()}.bin"] = blob
            lines.append(head)
    rng = random.Random(AL_SEED)
    runs = []
    for n in range(1, AL_RUNS + 1):
        blob, head, els = _al_run(A.random_spec(n, rng), n)
        files[AL_DIR / f"run-{n}.bin"] = blob
        files[AL_DIR / f"run-{n}.json"] = json.dumps(_trim(els, 17), separators=(",", ":")).encode("utf-8")
        runs.append(head)
    return _trim({
        "_generated_by": "website/scripts/portal_spaces_export.py from al_build -- do not edit",
        "factory": _factory(), "runs": runs,
        "assumptions": A.ASSUMPTIONS,
        "stages": [{"key": st.key, "title": st.title, "desc": st.desc, "colour": list(st.colour if hasattr(st, "colour") else st.color)}
                   for st in A._STAGE_LIST],
        "categoryLabel": A.CATEGORY_LABEL, "layouts": A.LAYOUTS,
        "lines": lines,
    }, 17), files


def _al_fixtures(rnd) -> list[dict]:
    """The line's sums with the assumptions moved about, and the Python's answers."""
    import al_build as A
    out = []
    keep = dict(A.ASSUMPTIONS)
    try:
        for i in range(40):
            dtype = A.DOME_TYPE_LIST[i % 4]
            over = {} if i < 4 else {"burdened_wage_per_hour": round(rnd.uniform(20, 80), 2),
                                     "overhead_per_labor_hour": round(rnd.uniform(5, 30), 2),
                                     "workers_per_station": rnd.randint(1, 6),
                                     "fixed_overhead_per_month": round(rnd.uniform(40_000, 150_000), 0),
                                     "line_capex": round(rnd.uniform(1e6, 5e6), 0),
                                     "bhph_apr": round(rnd.uniform(0.0, 0.2), 3)}
            A.ASSUMPTIONS.clear(); A.ASSUMPTIONS.update(keep); A.ASSUMPTIONS.update(over)
            spec = _al_spec(dtype, A.LAYOUTS[i % 3] if dtype == "home" else None)
            cat, _ = A.build_dome_catalog(spec)
            econ = A.unit_economics(cat, spec)
            tp = A.throughput(cat)
            out.append({"dtype": dtype, "layout": spec.layout, "over": over, "price": spec.sale_price,
                        "monthly": spec.monthly_payment, "econ": econ,
                        "throughput": {k: v for k, v in tp.items() if k not in ("rows", "bottleneck")},
                        "bottleneck": tp["bottleneck"]["key"], "rows": tp["rows"],
                        "breakEven": A.break_even(econ["margin"], econ["overhead"]),
                        "breakEvenDefault": A.break_even(econ["margin"]),
                        "value": A.product_value(cat, spec),
                        "scale": A.scale_scenarios(tp["single_flow_per_year"], econ["margin"], econ["price"])})
    finally:
        A.ASSUMPTIONS.clear(); A.ASSUMPTIONS.update(keep)
    return out


# ----------------------------------------------------------------------
# Foundation & Pads
# ----------------------------------------------------------------------

FOUNDATION_DIR = ROOT / "website" / "public" / "portal" / "foundation"


def foundation() -> tuple[dict, dict[Path, bytes]]:
    import pad_deck as pd
    from infill.app3d import solid_tris
    from world3d import structures as st

    sets = {"foundation": st.foundation(), "deck": st.foundation_deck(), "jig": st.foundation_jig()}
    chunks, heads = [], []
    for layer, pieces in sets.items():
        for p in pieces:
            rows = solid_tris(p.solid, (*p.colour[:3], 1.0) if len(p.colour) >= 3 else (0.8, 0.6, 0.4, 1.0))
            chunks.append(rows)
            heads.append({"id": p.pid, "layer": layer, "name": p.name, "kind": p.kind,
                          "meta": {k: v for k, v in p.meta.items() if k in ("group", "material", "centreline_in", "cut_in", "number")}})
    blob, mesh, ranges = pack_rows(chunks, "pieces", "foundation")
    for h, r in zip(heads, ranges):
        h["v"] = r
    # the jig is laid out to one side of the foundation in the 3-D world: say where, so it can be drawn in place
    across = pd.pad_diameter_ft()
    sizes = sorted({across} | {float(x) for x in range(12, 50, 2)})      # the seed dome's own size among them, exactly
    decks = {}
    for kind in pd.KINDS:
        decks[kind] = [{"across": a, **_deck(pd.deck(kind, a))} for a in sizes]
    return _trim({
        "_generated_by": "website/scripts/portal_spaces_export.py from world3d.structures and pad_deck -- do not edit",
        "pieces": heads, "mesh": mesh, "facts": st.foundation_facts(), "jigAt": [float(x) for x in st.FOUNDATION_JIG_AT],
        "pad": {"across": across, "sizes": sizes, "kinds": list(pd.KINDS), "decks": decks,
                "sequence": {k: [{"number": x.number, "label": x.label, "detail": x.detail, "cumulative": x.cumulative_usd}
                                 for x in pd.build_sequence(k)] for k in pd.KINDS},
                "board": {"usd": pd.board_usd(), "perFoot": pd.usd_per_linear_ft()}},
    }, 17), {FOUNDATION_DIR / "pieces.bin": blob}


def _deck(d) -> dict:
    return {"key": d.key, "label": d.label, "cost": d.cost, "area": d.area_sqft, "perSqft": d.usd_per_sqft,
            "boards": d.boards, "walkable": d.walkable, "note": d.note,
            "lines": [{"label": l.label, "quantity": l.quantity, "unit": l.unit, "unitCost": l.unit_cost, "cost": l.cost, "source": l.source}
                      for l in d.lines]}


# ----------------------------------------------------------------------
# Masterclass Theatre
# ----------------------------------------------------------------------

def masterclass() -> dict:
    """Every lesson the renderer can play, but not the Cabin World re-stagings of them (the
    same chapters again) or the ingested concepts (cards, not lessons)."""
    from two_v_demo import lesson_registry as lr

    out = []
    for key, lesson in lr.LESSONS.items():
        if key.startswith("cabin_") and key[6:] in lr.LESSONS:
            continue
        chapters = []
        for c in lesson.chapters:
            chapters.append({"slug": c.slug, "number": c.number, "title": c.title, "promise": c.promise,
                             "narration": list(c.narration), "equations": [str(e) for e in c.equations],
                             "duration": c.duration, "mood": getattr(c, "mood", "neutral")})
        if not chapters:
            continue
        out.append({"key": key, "brand": lesson.brand, "title": lesson.title, "style": lesson.style,
                    "minutes": sum(c["duration"] for c in chapters) / 60.0, "chapters": chapters})
    return _trim({"_generated_by": "website/scripts/portal_spaces_export.py from two_v_demo.lesson_registry -- do not edit",
                  "lessons": out, "default": lr.DEFAULT_LESSON_KEY})


# ----------------------------------------------------------------------
# Test cases, with the Python's answers
# ----------------------------------------------------------------------

def fixtures(n: int = 300, seed: int = 5) -> dict:
    from two_v_demo import cell_wall as cw
    from two_v_demo import seam_climate as scl

    rnd = random.Random(seed)
    decide = []
    for i in range(n):
        s = scl.Sensors(round(rnd.uniform(5, 30), 1), round(rnd.uniform(0.2, 0.95), 2), round(rnd.uniform(-15, 40), 1),
                        round(rnd.uniform(0.1, 1.0), 2), round(rnd.uniform(-5, 50), 1), round(rnd.uniform(0.2, 0.98), 2),
                        round(rnd.uniform(0.08, 0.26), 3), rnd.random() < 0.15, rnd.random() < 0.3, rnd.random() < 0.2)
        d = scl.decide(s)
        decide.append({"sensors": s.__dict__, "mode": d.mode, "dp": [d.dp_in, d.dp_out, d.dp_seam], "reasons": list(d.reasons)})
    for sc in scl.SCENARIOS:
        d = scl.decide(sc.sensors)
        decide.append({"sensors": sc.sensors.__dict__, "mode": d.mode, "dp": [d.dp_in, d.dp_out, d.dp_seam], "reasons": list(d.reasons)})
    keys = [l.key for l in cw.LAYERS]
    profiles = [{"stack": None, "t_out": None, "rows": cw.profile()},
                {"stack": list(cw.OWNER_STACK) + ["core"], "t_out": -20.0, "rows": cw.profile(tuple(cw.OWNER_STACK) + ("core",), -20.0)}]
    for _ in range(20):
        st = keys[:]
        rnd.shuffle(st)
        t = round(rnd.uniform(-30, 10), 1)
        profiles.append({"stack": st, "t_out": t, "rows": cw.profile(tuple(st), t)})
    checks = []
    for k, _label, modes in cw.SCENARIOS:
        checks.append({"modes": modes, "t_out": None, "broken": cw.check_scenario(modes)})
    for _ in range(200):
        modes = {l.key: rnd.choice(l.modes) for l in cw.LAYERS if rnd.random() < 0.6}
        t = rnd.choice([None, -5.0, 5.0])
        checks.append({"modes": modes, "t_out": t, "broken": cw.check_scenario(modes, t)})
    cold = [dict(cold=scl.cold_channel(t, rh), t=t, rh=rh) for t, rh in ((21.0, 0.55), (18.0, 0.7), (25.0, 0.4))]
    return {"decide": decide, "profiles": profiles, "checks": checks, "cold": cold, "assembly": _al_fixtures(rnd)}


# ----------------------------------------------------------------------
# Main
# ----------------------------------------------------------------------

def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--fixtures", type=Path)
    a = ap.parse_args()
    if a.fixtures:
        a.fixtures.write_text(json.dumps(fixtures()), encoding="utf-8")
        print(f"wrote {a.fixtures}")
        return 0
    t, files = panel_creator()
    print(len(t["ways"]), sum(len(b) for b in files.values()))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
