"""Materials and what they cost, for every kind of dome Dome Sketch draws.

Two tables, kept apart on purpose:

* **quantities** -- counted from the solved model: sheets of plate from the nesting, metres of
  weld from the shell's own seams, logs from the log plan, studs from the cut list. Nothing here
  is typed in.
* **prices** -- declared estimates, each with what it is, what it is per, and why that figure.
  They move with the market and with the yard, so the page lets the viewer replace them and the
  total follows.

A row's cost is its quantity in the price's own unit times the price. The total is labelled an
estimate wherever it is shown.

The prices come from the tables the repository already keeps, by reference rather than by copy:

* ``two_v_demo.dome_costing.PRICES`` -- the shelf quotes behind the 2V cost study (sheathing);
* ``infill.base.BASE_CONSTANTS`` -- what a log from your own trees costs (nothing, as an
  assumption);
* :data:`PRICE_ESTIMATES` -- the framed-panel dome's typical prices, which the PDF plan set's
  price sheet also reads (``plans.s_prices``), so the page and the PDF agree;
* :data:`METAL_PRICES` -- steel plate, wire and fittings for the all-steel domes.
"""

from __future__ import annotations

import math
from dataclasses import dataclass

import numpy as np

from . import model as M
from . import solids as S

IN = M.IN
FT = M.FT
LB = 0.45359237
FT2 = FT * FT
YD3 = (3 * FT) ** 3


@dataclass(frozen=True)
class Price:
    key: str
    label: str
    usd: float
    per: str
    kind: str          # estimate | assumption | quote
    why: str
    source: str


#: Typical US retail prices, October 2026: DECLARED ESTIMATES, not quotes. They exist so the
#: price sheet can multiply the counted quantities by something; replace them with your yard's.
#: key -> (what is priced, US dollars, per). The plan set's price sheet reads this table too.
PRICE_ESTIMATES = {
    "stud_2x3": ("2x3 stud, 8 ft", 4.25, "each"),
    "ply_half": ("1/2 in plywood, 4x8", 38.00, "sheet"),
    "polycarb": ("1/4 in polycarbonate", 45.00, "m²"),
    "board_2x6": ("2x6, 8 ft", 9.50, "each"),
    "pt_2x4": ("pressure-treated 2x4, 8 ft", 7.50, "each"),
    "board_2x4": ("2x4, 8 ft", 4.75, "each"),
    "ply_34": ("3/4 in plywood, 4x8", 55.00, "sheet"),
    "joist_2x8": ("2x8, 10 ft", 16.00, "each"),
    "deck_54x6": ("5/4x6 decking, 12 ft", 14.00, "each"),
    "screws_3in": ("75 mm screws", 12.00, "100"),
    "staples": ("staples", 8.00, "1000"),
    "tape": ("seam tape", 0.60, "m"),
    "shingles": ("shingles or cladding", 18.00, "m²"),
    "pier": ("precast pier block", 12.00, "each"),
}

#: The all-steel domes: plate, wire, fittings and finishes (key -> label, USD, per, why).
METAL_PRICES = {
    "plate_lb": ("Hot-rolled mild steel plate (A36), 4 x 8 ft sheets", 1.20, "lb",
                 "a small-shop price from a metal supplier, late 2026; plate is sold by the sheet and priced by weight"),
    "wire_lb": ("ER70S-6 MIG wire", 3.60, "lb", "an 11 lb spool at about $40"),
    "tube_ft": ("1-1/2 in square tube, 1/8 in wall", 4.00, "ft", "legs, cut from a 20 ft stick"),
    "pipe_ft": ("Flue pipe the size of the flue, for the collar", 6.00, "ft", "single-wall black pipe, cut for the collar"),
    "brick": ("Firebrick split, 4-1/2 x 9 x 1-1/4 in", 3.50, "each", "a fireplace or kiln supplier's split"),
    "gasket_ft": ("5/8 in rope gasket with its cement", 1.75, "ft", "sold by the foot with a tube of gasket cement"),
    "door_set": ("Two weld-on barrel hinges and a latch", 35.00, "set", "weld-on hinges and a cam latch"),
    "hearth_ft2": ("Hearth: stone or tile on cement board", 6.00, "ft²", "tile or slate over 1/2 in cement board"),
    "stove_paint_ft2": ("High-temperature stove paint, one coat", 0.80, "ft²", "a $12 can covers about 15 ft²"),
    "coupling": ("Weld-on threaded half coupling and a pipe stub", 12.00, "each", "one per opening in the shell"),
    "valve": ("Ball valve", 18.00, "each", "on the outlet and the drain"),
    "hatch_set": ("Hatch hinge, hasp, screen and gasket", 40.00, "set", "for the manway lid"),
    "concrete_yd3": ("Concrete, ready-mix, delivered", 165.00, "yd³", "bagged concrete costs about twice this"),
    "lining_ft2": ("Potable-water epoxy lining (NSF/ANSI 61), one coat", 1.50, "ft²", "a two-part tank lining"),
    "paint_ft2": ("Exterior metal primer and paint, one coat", 0.50, "ft²", "a gallon covers about 350 ft² at $45 a coat of primer and paint"),
}

#: The wedge method's own purchases (logs are the method's point: from your own trees, they cost nothing).
WOOD_PRICES = {
    "screw": ("Structural wood screw, 6 in", 0.75, "each", "a box of 50 at about $37"),
    "key_stock": ("Seam keys", 0.0, "each", "split from the logs' offcuts; set a price if you buy stock for them"),
}

#: Counts the geometry cannot give: how many screws a joint takes.
ASSUMED = {
    "screws_per_end": (2, "structural screws through each wedge or stick end at a panel corner"),
    "seam_screw_m": (12 * IN, "one structural screw each side of a seam, this far apart"),
    "waste": (0.10, "extra sheathing bought for cut-off and mistakes"),
}


def prices() -> dict[str, Price]:
    """Every price this module can use, with its source."""
    from infill.base import BASE_CONSTANTS
    from two_v_demo import dome_costing as DC

    out: dict[str, Price] = {}
    for k, (label, usd, per) in PRICE_ESTIMATES.items():
        out[k] = Price(k, label, usd, per, "estimate", "typical US retail, October 2026", "sketch_claude.costing (the plan set's price sheet)")
    for k, (label, usd, per, why) in METAL_PRICES.items():
        out[k] = Price(k, label, usd, per, "estimate", why, "sketch_claude.costing")
    for k, (label, usd, per, why) in WOOD_PRICES.items():
        out[k] = Price(k, label, usd, per, "assumption" if usd == 0 else "estimate", why, "sketch_claude.costing")
    osb = next(p for p in DC.PRICES if p.key == "osb_half_4x8")
    out["osb"] = Price("osb", "1/2 in OSB, 4 x 8 sheet", osb.value, "sheet", "estimate", osb.note, "two_v_demo.dome_costing.PRICES")
    for name, value, _u, kind, why in BASE_CONSTANTS:
        if name == "usd_log":
            out["log"] = Price("log", "Log, from your own trees", value, "each", kind, why, "infill.base.BASE_CONSTANTS")
    return out


# ----------------------------------------------------------------------
# A row of the materials table
# ----------------------------------------------------------------------

def _row(item: str, qty_text: str, counted: str, key: str | None, units: float, qty: float | None = None) -> dict:
    """``units`` is the quantity in the price's own unit (sheets, lb, ft, ft², each...)."""
    return {"item": item, "qty_text": qty_text, "from": counted, "price": key, "units": float(units),
            "qty": float(units if qty is None else qty)}


def _cost(rows: list[dict], table: dict[str, Price]) -> dict:
    used = []
    total = 0.0
    for r in rows:
        p = table.get(r["price"]) if r["price"] else None
        r["usd"] = round(r["units"] * p.usd / _div(p.per), 2) if p else None
        if r["usd"] is not None:
            total += r["usd"]
        if p and p.key not in used:
            used.append(p.key)
    price_rows = [{"key": k, "label": table[k].label, "usd": table[k].usd, "per": table[k].per, "kind": table[k].kind,
                   "why": table[k].why, "source": table[k].source} for k in used]
    return {"rows": rows, "prices": price_rows, "total": round(total, 2)}


def _sheet_kg(t: float, steel: float) -> float:
    return 4 * FT * 8 * FT * t * steel


def _wire_kg(weld_m: float, t: float, steel: float) -> float:
    """Weld metal for a full-penetration 60° V on plate of thickness t (area t²·tan 30°), at 90% deposition."""
    return weld_m * t * t * math.tan(math.radians(30)) * steel / 0.9


def _face_area(mesh: S.Mesh) -> float:
    """The largest flat face of a thin piece (a skin panel): its covering area."""
    v, t = mesh.verts, mesh.tris
    if not len(t):
        return 0.0
    cr = np.cross(v[t[:, 1]] - v[t[:, 0]], v[t[:, 2]] - v[t[:, 0]])
    a = np.linalg.norm(cr, axis=1) / 2
    n = np.round(cr / np.maximum(np.linalg.norm(cr, axis=1, keepdims=True), 1e-15), 3)
    best: dict[tuple, float] = {}
    for k, ai in zip(map(tuple, n), a):
        best[k] = best.get(k, 0.0) + float(ai)
    return max(best.values())


# ----------------------------------------------------------------------
# Per kind
# ----------------------------------------------------------------------

def panel_counts(t: dict, sp) -> dict:
    """The framed-panel dome's bought quantities that are not already in its tables. The plan
    set's materials sheet and this module both count from here."""
    D = M.D
    base_lengths = [b["length_m"] for b in t["base_sections"]]
    porch = (D("porch_w_m") * D("deck_front_m")) if sp.porch else 0.0
    return {
        "base_lengths": base_lengths,
        "base_boards": math.ceil(sum(base_lengths) / D("board_l_m") * (1 + D("waste"))),
        "plates": math.ceil(sum(base_lengths) / D("board_l_m") * (1 + D("waste"))),
        "deck_boards": math.ceil(t["deck_m2"] / D("deck_board_m") / D("deck_board_l_m") * (1 + D("waste"))),
        "porch_m2": porch,
        "porch_boards": math.ceil(porch / D("deck_board_m") / D("deck_board_l_m") * (1 + D("waste"))),
        "shingles_m2": t["skin_m2"] * (1 + D("waste")),
        "piers": t["base_edges"] // 3 + 1 + (4 if sp.porch else 0),
    }


def _panel(model: M.Model) -> list[dict]:
    from .kinds import m, m2, n
    t, sp = model.tables, model.spec
    c = panel_counts(t, sp)
    door = t["door"]
    D = M.D
    return [
        _row("2x3 studs, 8 ft (each ripped into two sticks)", n(t["boards"]), f"{t['stick_count']} sticks, {m(t['stick_m'])} of stick", "stud_2x3", t["boards"]),
        _row("1/2 in plywood, 4x8 sheets, for the skin", n(t["sheets"]), f"{m2(t['skin_m2'])} of panel, nested on sheets", "ply_half", t["sheets"]),
        _row("Window glazing, 1/4 in polycarbonate", m2(t["glass_m2"]), f"{t['windows']} windows, {t['skylights']} skylight panels", "polycarb", t["glass_m2"]),
        _row("2x6, 8 ft, base boards", n(c["base_boards"]), f"{len(c['base_lengths'])} sections, {m(sum(c['base_lengths']))}", "board_2x6", c["base_boards"]),
        _row("Pressure-treated 2x4, 8 ft, bottom plates", n(c["plates"]), m(sum(c["base_lengths"])), "pt_2x4", c["plates"]),
        _row("2x4, 8 ft, door posts and head", "3" if door else "0", (f"posts {m(door['H'])}, head {m(2 * door['X'])}" if door else ""), "board_2x4", 3 if door else 0),
        _row("3/4 in plywood, door cards", "1" if door else "0", "two cards from one sheet", "ply_34", 1 if door else 0),
        _row("2x8 joists and rim, deck framing", n(2 * t["base_edges"]), "one joist to each base corner, one rim board each side", "joist_2x8", 2 * t["base_edges"]),
        _row("5/4x6 decking, 12 ft", n(c["deck_boards"] + c["porch_boards"]), f"floor {m2(t['deck_m2'])}" + (f", porch {m2(c['porch_m2'])}" if c["porch_m2"] else ""),
             "deck_54x6", c["deck_boards"] + c["porch_boards"]),
        _row("75 mm (3 in) screws, panel corners", n(t["screws_corner"]), f"{t['corners']} corners x {int(D('screws_per_corner'))}", "screws_3in", t["screws_corner"]),
        _row("75 mm (3 in) screws, panel to panel", n(t["screws_seam"]), f"{m(t['seam_m'])} of seam, both sides every {m(D('seam_screw_m'))}", "screws_3in", t["screws_seam"]),
        _row("Staples", n(t["staples"]), f"every {m(D('staple_m'))} round each skinned panel", "staples", t["staples"]),
        _row("Seam tape", m(t["tape_m"]), f"{m(t['seam_m'])} of seam plus {D('waste') * 100:.0f}%", "tape", t["tape_m"]),
        _row("Shingles or cladding", m2(c["shingles_m2"]), "over the plywood skin", "shingles", c["shingles_m2"] if sp.skin == "cabin" else 0.0),
        _row("Piers", n(c["piers"]), "under every third corner, the centre and the porch", "pier", c["piers"]),
    ]


def _sheathing(model: M.Model, rows: list[dict]) -> None:
    from .kinds import m2, n
    skins = [p for p in model.pieces if p.tag == "skin" and len(p.mesh.tris)]
    if not skins:
        return
    area = sum(_face_area(p.mesh) for p in skins)
    sheets = math.ceil(area * (1 + ASSUMED["waste"][0]) / (4 * FT * 8 * FT))
    rows.append(_row("1/2 in OSB sheathing, 4 x 8 sheets", n(sheets), f"{len(skins)} panels, {m2(area)}, plus {ASSUMED['waste'][0] * 100:.0f}%", "osb", sheets))


def _wedge(model: M.Model) -> list[dict]:
    from .kinds import kg, m, n
    sp, t = model.spec, model.tables
    w = t["wedge"]
    members = [p for p in model.pieces if p.tag == "frame"]
    keys = [p for p in model.pieces if p.tag == "key"]
    green = _green(t)
    rows = [_row(f"Logs, {sp.log_m / IN:.0f} in across the small end", n(w["logs"]),
                 f"the log plan: {w['logs']} logs of {m(_log_len(t) or sp.log_len_m)}" + (f", {kg(green)} green" if green else ""),
                 "log", w["logs"])]
    if keys:
        L = sum(float(p.info.get("length_m", 0.0)) for p in keys)
        rows.append(_row("Seam keys", n(len(keys)), f"{len(keys)} keys, {m(L)} in all", "key_stock", len(keys)))
    ends = 2 * len(members) * ASSUMED["screws_per_end"][0]
    seam = sum(2 * (math.floor(float(p.info.get("length_m", 0.0)) / ASSUMED["seam_screw_m"][0]) + 1) for p in keys)
    rows.append(_row("Structural screws, 6 in", n(ends + seam), f"{ASSUMED['screws_per_end'][0]} through each of {2 * len(members)} wedge ends"
                     + (f", and {n(seam)} along the keyed seams" if seam else ""), "screw", ends + seam))
    _sheathing(model, rows)
    return rows


def _green(t: dict) -> float:
    for k, v in t.get("summary", []):
        if k == "Green wood" and v.startswith("{kg:"):
            return float(v[4:-1])
    return 0.0


def _log_len(t: dict) -> float:
    for c in t.get("cards", []):
        if c.get("kind") == "log":
            for k, v in c["rows"]:
                if k == "Length" and v.startswith("{m:"):
                    return float(v[3:-1])
    return 0.0


def _zome(model: M.Model) -> list[dict]:
    from .kinds import m, n
    z = model.tables["zome"]
    sticks = [p for p in model.pieces if p.tag == "frame"]
    rows = [_row(f"Log sections, {z['log_m'] / IN:.0f} in across", n(z["sections"]),
                 f"{z['sections']} sections of {m(z['section_m'])}, split into {z['wedges']} wedges", "log", z["sections"])]
    ends = 2 * len(sticks) * ASSUMED["screws_per_end"][0]
    rows.append(_row("Structural screws, 6 in", n(ends), f"{ASSUMED['screws_per_end'][0]} through each of {2 * len(sticks)} stick ends", "screw", ends))
    _sheathing(model, rows)
    return rows


def _steel_common(model: M.Model, info: dict, steel: float, rows: list[dict], floor_t: float | None = None) -> None:
    from .kinds import kg, m, n
    tp = info["plate_m"]
    tf = floor_t if floor_t is not None else tp
    sk, fk = _sheet_kg(tp, steel), _sheet_kg(tf, steel)
    if tf == tp:
        nsh = info["shell_sheets"] + info["floor_pieces"]
        rows.append(_row(f"{tp / IN:.4g} in plate, 4 x 8 ft sheets", n(nsh),
                         f"the shell nests on {info['shell_sheets']}, each floor piece takes one; {kg(sk)} a sheet", "plate_lb", nsh * sk / LB, nsh))
    else:
        rows.append(_row(f"{tp / IN:.4g} in plate, 4 x 8 ft sheets (shell)", n(info["shell_sheets"]), f"the shell's nesting; {kg(sk)} a sheet",
                         "plate_lb", info["shell_sheets"] * sk / LB, info["shell_sheets"]))
        rows.append(_row(f"{tf / IN:.4g} in plate, 4 x 8 ft sheets (floor)", n(info["floor_pieces"]), f"one sheet for each floor piece; {kg(fk)} a sheet",
                         "plate_lb", info["floor_pieces"] * fk / LB, info["floor_pieces"]))
    wire = _wire_kg(info["weld_m"], tp, steel)
    rows.append(_row("MIG wire", kg(wire), f"{m(info['weld_m'])} of seam, a full-penetration 60° V on {m(tp)} plate", "wire_lb", wire / LB, wire))


def _outside_m2(model: M.Model, tags=("shell", "door", "cap")) -> float:
    return sum(float(p.info.get("area_m2", 0.0)) for p in model.pieces if p.tag in tags and p.material == "steel_plate")


def _stove(model: M.Model) -> list[dict]:
    from .kinds import m, m2, n
    t, sp = model.tables, model.spec
    st = t["stove"]
    steel = 7850.0
    rows: list[dict] = []
    _steel_common(model, st, steel, rows)
    legs = [p for p in model.pieces if p.group == "legs"]
    leg_len = sum(float(p.info.get("length_m", 0.0)) for p in legs)
    rows.append(_row("Legs: 1-1/2 in square tube", m(leg_len), f"{len(legs)} legs of {m(sp.legs_m)}", "tube_ft", leg_len / FT, leg_len))
    collar = next((p for p in model.pieces if p.id == "collar"), None)
    if collar:
        h = float(collar.info.get("height_m", 0.0))
        rows.append(_row(f"Flue collar, {m(sp.flue_m)} pipe", m(h), "one collar welded over the cap's hole", "pipe_ft", h / FT, h))
    rows.append(_row("Firebrick splits", n(st["bricks"]), "laid across the floor plate inside", "brick", st["bricks"]))
    gk = st["door_perimeter_m"] * 1.1
    rows.append(_row("Rope gasket round the door", m(gk), f"the door's edge, {m(st['door_perimeter_m'])}, plus 10% for the joints", "gasket_ft", gk / FT, gk))
    rows.append(_row("Door hinges and latch", "1 set", f"{st['hinges']} hinges and a latch", "door_set", 1))
    hearth = next((p for p in model.pieces if p.group == "hearth"), None)
    if hearth:
        a = float(hearth.info.get("width_m", 0.0)) * float(hearth.info.get("depth_m", 0.0))
        rows.append(_row("Hearth pad", m2(a), f"{m(hearth.info['width_m'])} x {m(hearth.info['depth_m'])}, under the stove and out past the door",
                         "hearth_ft2", a / FT2, a))
    out = _outside_m2(model)
    rows.append(_row("High-temperature paint, one coat", m2(out), "the shell, door and cap, outside", "stove_paint_ft2", out / FT2, out))
    return rows


def _tank(model: M.Model) -> list[dict]:
    from .kinds import m, m2, n
    t = model.tables
    tk = t["tank"]
    steel = 7850.0
    rows: list[dict] = []
    _steel_common(model, tk, steel, rows, floor_t=tk["floor_m"])
    pipes = [p for p in model.pieces if p.group.startswith("pipe-")]
    rows.append(_row("Threaded half couplings with pipe stubs", n(len(pipes)), ", ".join(p.name.replace(" pipe", "").lower() for p in pipes), "coupling", len(pipes)))
    valves = [p for p in pipes if p.group in ("pipe-outlet", "pipe-drain")]
    rows.append(_row("Ball valves", n(len(valves)), "on the outlet and the drain", "valve", len(valves)))
    if any(p.group == "hatch" for p in model.pieces):
        rows.append(_row("Hatch hardware", "1 set", "hinge, hasp, insect screen and gasket for the manway lid", "hatch_set", 1))
    pad = next((p for p in model.pieces if p.group == "pad"), None)
    if pad:
        v = float(pad.info.get("area_m2", 0.0)) * float(pad.info.get("thickness_m", 0.0))
        rows.append(_row("Concrete pad", f"{v:.2f} m³ ({v / YD3:.2f} yd³)", f"{m2(pad.info['area_m2'])} at {m(pad.info['thickness_m'])}", "concrete_yd3", v / YD3, v))
    wet = _outside_m2(model, ("shell", "cap")) + _outside_m2(model, ("floor",))
    rows.append(_row("Potable-water lining, one coat", m2(wet), "inside the shell, cap and floor", "lining_ft2", wet / FT2, wet))
    out = _outside_m2(model, ("shell", "cap"))
    rows.append(_row("Exterior primer and paint, one coat", m2(out), "the shell and cap, outside", "paint_ft2", out / FT2, out))
    return rows


KINDS = {"panel": _panel, "wedge": _wedge, "zome": _zome, "stove": _stove, "tank": _tank}

NOT_INCLUDED = {
    "panel": "tools, deck fasteners, the door leaf's hardware, paint or oil, delivery, permits and your time",
    "wedge": "tools, chain and bar oil, the foundation, the floor, doors and windows, delivery, permits and your time",
    "zome": "tools, chain and bar oil, the foundation, the floor, doors and windows, delivery, permits and your time",
    "stove": "the stove pipe to your chimney and the chimney itself, shielding gas, grinding discs, an inspection, and your time",
    "tank": "the plumbing beyond the valves, shielding gas, grinding discs, a water test, delivery, and your time",
}


def materials(kind: str, model: M.Model) -> dict:
    """The materials table for one design: counted quantities, the declared prices they use, a total."""
    rows = KINDS[kind](model)
    out = _cost(rows, prices())
    out["kind"] = kind
    out["note"] = ("Quantities are counted from this design. Prices are declared estimates (typical US retail, late 2026), "
                   f"not quotes: replace them with your supplier's. Not included: {NOT_INCLUDED[kind]}.")
    out["assumed"] = [{"name": k, "value": v, "why": why} for k, (v, why) in ASSUMED.items()
                      if kind in ("wedge", "zome") or k == "waste"]
    return out


def _div(per: str) -> int:
    return 100 if per == "100" else 1000 if per == "1000" else 1


def reprice(table: dict, overrides: dict | None) -> dict:
    """The same quantities at the viewer's own prices (key -> USD), marked as theirs. The page does
    this sum itself as prices are typed; an export made from the page sends them here."""
    if not overrides:
        return table
    prices = []
    for p in table["prices"]:
        p = dict(p)
        try:
            v = float(overrides.get(p["key"], "nan"))
        except (TypeError, ValueError):
            v = math.nan
        if math.isfinite(v) and v >= 0:
            p.update(usd=v, kind="yours", why="your own price, typed in Dome Sketch")
        prices.append(p)
    by = {p["key"]: p for p in prices}
    rows, total = [], 0.0
    for r in table["rows"]:
        r = dict(r)
        p = by.get(r["price"])
        if p:
            r["usd"] = round(r["units"] * p["usd"] / _div(p["per"]), 2)
            total += r["usd"]
        rows.append(r)
    return {**table, "rows": rows, "prices": prices, "total": round(total, 2)}


def validate_costing(table: dict) -> None:
    """A materials table adds up: every row's cost is its units times its price, the total is their sum."""
    by = {p["key"]: p for p in table["prices"]}
    total = 0.0
    for r in table["rows"]:
        if r["price"] is None:
            continue
        p = by[r["price"]]
        assert abs(r["usd"] - round(r["units"] * p["usd"] / _div(p["per"]), 2)) < 0.006, r
        total += r["usd"]
    assert abs(total - table["total"]) < 0.01 * max(1, len(table["rows"])), (total, table["total"])
