"""The Panel Creator, Cell Wall & Seams and Masterclass Theatre spaces, as data a browser can use.

* **Panel Creator** is the Triangle Infill tool (infill/) as `two_v_demo.infill_dome` puts it on
  the whole dome: its 41 ways to fill a triangle (the owner's pairs and the tool's patterns, filling
  or covering), each panel type's pieces meshed by the tool's own mesher and cut to the opening's
  walls, each piece's numbers and saw recipe, and the forty seats the panels take on the dome. The
  meshes and the piece tables go to public/portal/infill/ (fetched one way at a time); the list of
  ways, their whole-dome figures and the seats are bundled.
* **Cell Wall & Seams** is `two_v_demo.cell_wall` and `two_v_demo.seam_climate`: the layer stack,
  the router's scenarios and interlocks, the seam controller's constants, modes and the owner's
  weathers, and the dome's seam bands. The browser re-runs the small exact parts -- the dew point,
  the controller's three questions, the wall's temperature profile, the interlocks -- and
  scripts/test_portal_spaces.mjs checks them against the Python.
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
        },
    }, 17)          # full precision: the browser re-runs these and is tested against the Python


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
    return {"decide": decide, "profiles": profiles, "checks": checks, "cold": cold}


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
