"""Every figure the film and the book state about filling the triangles and
framing the floor -- worked out here, once, by the same code the 3-D tool runs.

The film (:mod:`two_v_demo.lesson_every_piece`) and the book's chapter both
read :func:`facts`; neither types a number. Building every floor pattern takes
a little while, so the result is kept on disk, keyed by the source of every
module it depends on: change a line of the calculator and the facts are worked
out again.
"""

from __future__ import annotations

import hashlib
import json
import math
from dataclasses import replace
from functools import lru_cache
from pathlib import Path

HERE = Path(__file__).resolve().parent
CACHE = HERE / ".cache" / "facts.json"
SOURCES = ("frame.py", "section.py", "patterns.py", "rounds.py", "solids.py", "recipes.py", "constants.py",
           "base.py", "stock.py", "facts.py", "geom2d.py")

# The worked examples. Each is a choice of what to show, not a figure.
WEDGE = ("w8", "parallel", "flipflop", "fill")
EXAMPLE_PIECE = 5                    # "Run 5": the piece the saw chapters cut
PERMUTATIONS = (
    ("w8", "parallel", "flipflop", "fill"),
    ("w8", "chevron", "flipflop", "fill"),
    ("s16", "parallel", "standing", "fill"),
    ("w8", "rings", "flipflop", "fill"),
    ("milled", "parallel", "butted", "fill"),
    ("fence", "louvers", "", "fill"),
    ("rounds", "hex", "aligned", "fill"),
    ("osb", "sheet", "", "cover"),
    ("metal", "strips", "", "cover"),
    ("film", "sheet", "", "cover"),
)
BASE_MATERIALS = ("half", "round", "quarter", "6x6", "4x4")


def _key() -> str:
    h = hashlib.sha256()
    for name in SOURCES:
        h.update((HERE / name).read_bytes())
    return h.hexdigest()


def _opts(material, arrangement, lay, mode):
    from .patterns import Options, valid
    return valid(Options(material, arrangement, lay or "flipflop", mode, 0, 12.0, 45.0, "open", 1.5, 3.0,
                         "cut", 1))


def _layout(material, arrangement, lay, mode):
    from .frame import Spec, solve
    from .patterns import layout
    panel = solve(Spec())["types"][0]
    return layout(panel, _opts(material, arrangement, lay, mode))


def _work() -> dict:
    from . import base as bs
    from . import recipes as rc
    from . import rounds as rd
    from . import solids as so
    from .constants import CONSTANTS
    from .frame import Spec, solve
    from .patterns import ARRANGEMENTS, LAYS, MATERIALS

    spec = Spec()
    S = solve(spec)
    types = S["types"]
    panel = types[0]
    out: dict = {"dome_radius_in": S["radius_in"], "dome_diameter_ft": S["diameter_ft"],
                 "strut_in": spec.max_strut_in, "frame_log_in": spec.frame_log_in,
                 "thickness_in": spec.thickness_in, "wall_deg": spec.wall_deg,
                 "types": [{"label": t.label, "count": t.count, "edges": list(t.edge_len),
                            "classes": list(t.edge_class)} for t in types],
                 "folds": sorted({round(f, 3) for t in types for f in t.folds}),
                 "infill_constants": len(CONSTANTS), "infill_log_in": _opts(*WEDGE).infill_log_in}
    # The wedge fill and its worked piece.
    L = _layout(*WEDGE)
    R = rc.recipes(L)
    lens = [p.long for p in L.pieces]
    piece = L.pieces[EXAMPLE_PIECE - 1]
    r = R[EXAMPLE_PIECE - 1]
    corners = {n: hi - lo for n, lo, hi in so.corners(piece.solid)}
    cuts = [s.anim for s in r.steps if s.anim and s.anim.get("type") in ("mitre", "freehand")]
    cut_rows = []
    for an in cuts:
        off = an.get("offcut")
        lo_hi = so.length(off) if off is not None and off.faces else (0.0, 0.0)
        cut_rows.append({"type": an["type"], "mitre": abs(an.get("mitre", 0.0)), "bevel": an.get("bevel", 0.0),
                         "keeper_right": an.get("keeper_right"), "off_long": lo_hi[0], "off_short": lo_hi[1]})
    out["wedge"] = {"title": L.title, "pieces": len(L.pieces), "longest": max(lens), "shortest": min(lens),
                    "piece": EXAMPLE_PIECE, "name": piece.group,
                    "point": corners.get("the point", 0.0),
                    "corners": sorted(corners.values(), reverse=True), "cuts": cut_rows,
                    "steps": [s.title for s in r.steps]}
    # Covering with a sheet: the bevels.
    Lc = _layout("osb", "sheet", "", "cover")
    out["sheet"] = {"pieces": len(Lc.pieces), "bevels": [e.bevel for e in Lc.pieces[0].ends]}
    # The permutations.
    perms = []
    for mat, arr, lay, mode in PERMUTATIONS:
        Lp = _layout(mat, arr, lay, mode)
        perms.append({"material": MATERIALS[mat][0], "key": mat, "arrangement": ARRANGEMENTS[arr],
                      "arr": arr, "lay": LAYS[lay][0] if lay in LAYS and arr != "louvers" else "",
                      "lay_key": lay, "mode": mode, "pieces": len(Lp.pieces)})
    out["perms"] = perms
    # Log rounds.
    Lr = _layout("rounds", "hex", "aligned", "fill")
    kinds: dict = {}
    for p in Lr.pieces:
        kinds[p.pose] = kinds.get(p.pose, 0) + 1
    frags = sum(getattr(p, "note", "").count("gap") for p in Lr.pieces)
    out["rounds"] = {"pieces": len(Lr.pieces), "kinds": kinds, "thick_in": Lr.opts.round_t_in,
                     "layers": len({p.group for p in Lr.pieces}), "copy_note": frags}
    # The floor base.
    o = bs.BaseOptions(dome_radius_in=S["radius_in"])
    b = bs.build(o)
    c = b.checks
    frame = [m for m in b.members if m.role == "frame"][0]
    marks = {n: hi - lo for n, lo, hi in frame.marks}
    ang = math.degrees(math.acos(min(1.0, abs(float(frame.planes[0][0].n[:2] @ frame.along)))))
    roles: dict = {}
    for m in b.members:
        roles[m.role] = roles.get(m.role, 0) + 1
    centre_pier = max(b.piers, key=lambda p: p.load_lb) if b.piers else None
    joist = next(m for m in b.members if m.role == "joist")
    jr = next(rr for rr in b.recipes if rr.number == joist.number)
    jsaw = [s.anim for s in jr.steps if s.anim and s.anim.get("type") == "mitre"]
    out["base"] = {
        "side_ft": o.side_in / 12, "log_in": o.log_in, "inner_r_ft": c["inner_r_in"] / 12,
        "corner_r_ft": c["corner_r_in"] / 12, "apothem_ft": bs.apothem(o.side_in) / 12,
        "area_ft2": c["area_ft2"], "dome_need_ft": c["dome_need_in"] / 12,
        "margin_ft": (c["inner_r_in"] - c["dome_need_in"]) / 12, "fits": bool(c["dome_fits"]),
        "frame_top_in": marks.get("along the top", 0.0),
        "frame_back_in": max(v for n, v in marks.items() if "widest" in n), "corner_deg": ang,
        "members": len(b.members), "roles": roles, "piers": len(b.piers), "extra_piers": c["extra_piers"],
        "worst": c["worst_ratio"], "deck_gap_in": c["deck_clear_in"], "deck_allow_in": c["deck_allow_in"],
        "total_lb": c["total_lb"], "pier_sum_lb": c["pier_sum_lb"], "pier_max_lb": c["pier_max_lb"],
        "pad_max_in": c["pad_max_in"], "big_pads": c["big_pads"], "hangers": b.stock["hangers"],
        "logs": b.stock["logs_total"], "usd": b.stock["usd"], "lines": b.stock["lines"],
        "joist": {"name": joist.name, "length_in": joist.s_hi - joist.s_lo, "mat": joist.mat,
                  "bevel": jsaw[0]["bevel"] if jsaw else 0.0, "mitre": abs(jsaw[0]["mitre"]) if jsaw else 0.0,
                  "end1": bs._end_words(joist, 0), "end2": bs._end_words(joist, 1)},
        "centre_pier_lb": centre_pier.load_lb if centre_pier else 0.0,
        "fb_psi": bs.K["fb_psi"], "live_psf": bs.K["live_psf"], "dead_psf": bs.K["dead_psf"],
        "declared": len(bs.BASE_CONSTANTS), "overhang_in": bs.K["dome_overhang_in"],
        "saw_height_in": bs.K["saw_height_in"], "joist_depth_in": bs.MATERIALS[o.sec_mat][3],
        "joist_name": bs.MATERIALS[o.sec_mat][0], "soil_psf": bs.K["soil_psf"], "pad_min_in": bs.K["pad_min_in"],
        "spacing_in": o.spacing_in, "deck_name": bs.DECKS[o.deck][0], "bevel_max": rc.BEVEL_MAX,
        "declared_kinds": {k: sum(1 for *_x, kk, _w in bs.BASE_CONSTANTS if kk == k)
                           for k in ("standard", "estimate", "assumption", "nominal")},
    }

    def row(bb):
        cc = bb.checks
        return {"key": bb.opts.pattern, "name": bs.PATTERNS[bb.opts.pattern][0], "members": len(bb.members),
                "piers": len(bb.piers), "worst": cc.get("worst_ratio", 0.0), "extra": cc.get("extra_piers", 0),
                "deck_gap_in": cc["deck_clear_in"], "deck_ok": bool(cc["deck_ok"]),
                "logs": bb.stock["logs_total"], "usd": bb.stock["usd"], "pier_max_lb": cc.get("pier_max_lb", 0.0),
                "pad_max_in": cc.get("pad_max_in", 0.0), "prim": bb.opts.prim_mat, "support": bb.opts.support}
    out["patterns"] = [row(bs.build(replace(o, pattern=k), with_recipes=False)) for k in bs.PATTERNS]
    gravel = replace(o, support="gravel", deck="fill")
    out["gravel"] = [row(bs.build(replace(gravel, pattern=k), with_recipes=False)) for k in bs.PATTERNS]
    out["materials"] = [dict(row(bs.build(replace(o, prim_mat=m), with_recipes=False)),
                             material=bs.MATERIALS[m][0]) for m in BASE_MATERIALS]
    star = bs.build(replace(o, pattern="star"), with_recipes=False)
    out["base"]["star_members"] = sum(1 for m in star.members if m.role == "primary")
    out["base"]["star_pieces"] = sorted({round(m.length, 1) for m in star.members if m.role == "primary"})
    out["base"]["rings"] = sum(1 for m in bs.build(replace(gravel, pattern="rings"), with_recipes=False).members
                               if m.role == "primary") // 5
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
    CACHE.parent.mkdir(parents=True, exist_ok=True)
    text = json.dumps({"key": key, "facts": f}, indent=1, default=lambda v: v.item() if hasattr(v, "item") else str(v))
    CACHE.write_text(text, encoding="utf-8")
    return json.loads(text)["facts"]


def by(rows: list, key: str) -> dict:
    return next(r for r in rows if r["key"] == key)
