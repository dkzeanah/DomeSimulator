"""``sq.*``: every figure *'Square' on Demand* prints, computed.

The book quotes three kinds of number:

* its own geometry -- wedges, pairs, squares, shims, pitches, the trade-off
  between splitting finer and losing more to the saw -- from
  :mod:`square_book.geometry`;
* the project's measured and modelled facts (the splitting rate, the zome) --
  everything else resolves through the Master Edition's tokens, which hand on to
  the Complete Edition's, so this book cannot disagree with them;
* the published veteran figures the pitch quotes, from :mod:`master_book.pitch`.

An unknown token stops the build.
"""

from __future__ import annotations

import math
import re
from functools import lru_cache

from . import geometry as g

TOKEN = re.compile(r"\{\{([a-z_]+\.[a-z_0-9]+)\}\}")


def _f(v: float, d: int = 2) -> str:
    return f"{v:,.{d}f}"


def _pct(v: float) -> str:
    return f"{100 * v:.0f}"


def _cols(rows: list[tuple], widths: tuple[int, ...]) -> str:
    """Aligned plain text, the way the print edition turns tables into tables:
    at least two spaces between every column."""
    out = []
    for row in rows:
        cells = []
        for cell, w in zip(row, widths):
            cells.append(f"{str(cell):<{w}}")
        out.append("  ".join(cells).rstrip())
    return "\n".join(out)


def zome_rows() -> list[dict]:
    """The Complete Edition's zome, row by row, and the split that would make
    its gap blocks: a wedge's point is 360/n degrees, the gap's V is the fold."""
    from two_v_demo import panel_method as pm

    rows = []
    for r in pm.facts()["zome_rows"]:
        exact = 360.0 / r.fold_deg
        near = round(exact)
        halving = min((2, 4, 8, 16, 32), key=lambda n: abs(360.0 / n - r.fold_deg))
        rows.append({"row": r.row, "fold": r.fold_deg, "bevel": r.block_bevel_deg,
                     "gap_in": r.gap_m / 0.0254, "exact": exact, "near": near,
                     "near_err": 360.0 / near - r.fold_deg, "halving": halving,
                     "halving_err": 360.0 / halving - r.fold_deg})
    return rows


@lru_cache(maxsize=1)
def table() -> dict[str, str]:
    from master_book import pitch

    t: dict[str, str] = {}
    ref = g.D["reference_log_in"]
    w8, w4, w12, w16 = (g.Wedge(ref, n) for n in (8, 4, 12, 16))
    slant = g.Pair(w8, "slant")
    back8 = g.Pair(w8, "back")
    quarter = g.Pair(w4, "back")
    rec = g.Recovery(ref)
    trade = {row["n"]: row for row in g.table_tradeoff(ref)}
    best_n = max(trade, key=lambda n: trade[n]["pairs_kept"])

    t.update({
        "sq.log": _f(ref, 0), "sq.r": _f(w8.r, 1), "sq.theta": _f(w8.theta, 1), "sq.beta": _f(w8.beta, 1),
        "sq.chord": _f(w8.chord), "sq.depth": _f(w8.depth), "sq.kerf": _f(g.D["kerf_in"]),
        "sq.plane": "1/16", "sq.tri_area": _f(w8.triangle_area, 1), "sq.sector_area": _f(w8.sector_area, 1),
        "sq.back_loss": _f(w8.back_loss, 1), "sq.back_loss_pct": _pct(w8.back_loss / w8.sector_area),
        "sq.round_area": _f(math.pi * (ref / 2) ** 2, 1),
        # the skewed pair
        "sq.acute": _f(slant.acute, 1), "sq.obtuse": _f(slant.obtuse, 1),
        "sq.pair_long": _f(slant.sides[0]), "sq.pair_short": _f(slant.sides[1]),
        "sq.pair_thick": _f(slant.thickness), "sq.pair_area": _f(slant.area, 1),
        "sq.square": _f(slant.planed[0]), "sq.square_kept_pair": _pct(slant.kept_of_pair),
        "sq.square_kept": _pct(slant.kept_of_log), "sq.square_2x4": str(slant.fits(3.5, 1.5)),
        "sq.square_4x4": str(slant.fits(3.5, 3.5)), "sq.cos45": _f(math.cos(math.radians(45)), 3),
        # back to back
        "sq.diamond_w": _f(back8.planed[0]), "sq.diamond_t": _f(back8.planed[1]),
        "sq.diamond_kept": _pct(back8.kept_of_log),
        "sq.quarter_square": _f(quarter.planed[0]), "sq.quarter_kept": _pct(quarter.kept_of_log),
        "sq.quarter_r": _f(w4.r_eff),
        # finer splits
        "sq.n12_w": _f(trade[12]["member"][0]), "sq.n12_t": _f(trade[12]["member"][1]),
        "sq.n12_kept": _pct(trade[12]["pairs_kept"]), "sq.n12_kerf": _pct(trade[12]["kerf_lost"]),
        "sq.n16_w": _f(trade[16]["member"][0]), "sq.n16_t": _f(trade[16]["member"][1]),
        "sq.n16_kept": _pct(trade[16]["pairs_kept"]), "sq.n16_kerf": _pct(trade[16]["kerf_lost"]),
        "sq.n8_kerf": _pct(trade[8]["kerf_lost"]), "sq.n24_kept": _pct(trade[24]["pairs_kept"]),
        "sq.n24_kerf": _pct(trade[24]["kerf_lost"]),
        "sq.best_n": str(best_n), "sq.best_kept": _pct(trade[best_n]["pairs_kept"]),
        "sq.cos30": _f(math.cos(math.radians(30)), 3),
        # against the mill, the reference log
        "sq.split_pct": _pct(rec.split), "sq.tri_pct": _pct(rec.triangles), "sq.squares_pct": _pct(rec.squares),
        "sq.sawn_pct": _pct(rec.sawn), "sq.sawn_count": str(rec.two_by_fours),
        # shims and pitch
        "sq.shim_deg": _f(w8.shim_angle, 1), "sq.shim_split": str(w8.shim_split),
        "sq.shim_thick": _f(w8.shim_thick), "sq.pitch8": _f(w8.pitch_in_12, 1),
        "sq.pitch6": _f(g.Wedge(ref, 6).pitch_in_12, 1), "sq.pitch12": _f(w12.pitch_in_12, 1),
        "sq.pitch16": _f(w16.pitch_in_12, 1), "sq.pitch4": _f(w4.pitch_in_12, 0),
        "sq.oct_interior": _f(180 - w8.theta, 0),
    })

    # tables
    rows = [("log, in", "wedge back, in", "pith to back, in", "pair planes to, in square",
             "dressed 2x4s in it", "dressed 4x4s in it")]
    for r in g.table_wedges():
        rows.append((_f(r["d"], 0), _f(r["chord"]), _f(r["depth"]), _f(r["square"]),
                     r["two_by_fours"], r["four_by_four"]))
    t["sq.t_wedges"] = _cols(rows, (8, 15, 17, 26, 19, 18))

    rows = [("log, in", "split, kept %", "backs trimmed %", "paired square %", "sawn 2x4s %", "2x4s a section")]
    for r in g.table_recovery():
        rows.append((_f(r["d"], 0), _pct(r["split"]), _pct(r["triangles"]), _pct(r["squares"]),
                     _pct(r["sawn"]), r["two_by_fours"]))
    t["sq.t_recovery"] = _cols(rows, (8, 14, 16, 16, 12, 14))

    rows = [("split", "point, deg", "pair", "member, in", "members", "kept %", "kerf %", "skew pitch, in 12")]
    for n, r in sorted(trade.items()):
        mw, mt = r["member"]
        rows.append((f"{n} ways", _f(r["theta"], 1), "back to back" if r["way"] == "back" else "slant",
                     f"{mw:.2f} x {mt:.2f}", r["members"], _pct(r["pairs_kept"]), _pct(r["kerf_lost"]),
                     _f(r["pitch"], 1)))
    t["sq.t_tradeoff"] = _cols(rows, (8, 11, 13, 13, 8, 7, 7, 17))

    rows = [("declared", "value", "kind", "why")]
    for d in g.DECLARED:
        value = "1/16 in" if d.key == "plane_in" else f"{d.value:g} {d.unit}"
        rows.append((d.key, value, d.kind, d.why))
    t["sq.t_declared"] = _cols(rows, (17, 9, 14, 40))

    z = zome_rows()
    rows = [("row", "fold, deg", "gap at depth, in", "split for the block", "nearest", "off by, deg",
             "by halving", "off by, deg")]
    for r in z:
        rows.append((r["row"], _f(r["fold"], 1), _f(r["gap_in"]), _f(r["exact"], 1), f"{r['near']} ways",
                     _f(r["near_err"], 1), f"{r['halving']} ways", _f(r["halving_err"], 1)))
    t["sq.t_zome"] = _cols(rows, (4, 10, 17, 20, 8, 11, 11, 11))
    t["sq.zome_fold_lo"] = _f(min(r["fold"] for r in z), 1)
    t["sq.zome_fold_hi"] = _f(max(r["fold"] for r in z), 1)
    t["sq.zome_n_lo"] = str(min(r["near"] for r in z))
    t["sq.zome_n_hi"] = str(max(r["near"] for r in z))

    # veterans: published, quoted from the pitch's own table
    t["sq.vets_pit"] = f"{pitch.VETERANS['pit'][0]:,}"
    t["sq.vets_out"] = f"{pitch.VETERANS['unsheltered'][0]:,}"
    t["sq.vets_when"] = pitch.VETERANS_COUNTED
    t["sq.village"] = str(pitch.VETERANS["village"][0])
    t["sq.programs"] = ", ".join(pitch.VETERAN_PROGRAMS)
    return t


def resolve(text: str, strict: bool = True) -> str:
    """``sq.*`` here; everything else through the Master Edition's tokens."""
    from master_book import tokens as mb

    own = table()

    def swap(m: re.Match) -> str:
        name = m.group(1)
        if not name.startswith("sq."):
            return m.group(0)
        if name not in own:
            if strict:
                raise KeyError(f"no token {name!r}")
            return m.group(0)
        return own[name]

    text = TOKEN.sub(swap, text)
    if TOKEN.search(text):
        text = mb.resolve(text, strict=strict)
    return text


if __name__ == "__main__":
    g.validate()
    for k, v in table().items():
        print(f"{{{{{k}}}}}", v if "\n" not in v else "\n" + v)
