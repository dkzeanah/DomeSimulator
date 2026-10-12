"""From pieces to things to split, saw or buy: for one triangle, or for the
whole dome (every triangle of both types, offcuts shared between them).

Strip stock is planned with first-fit-decreasing on the longest piece the
stock comes in (the max strut length, for log pieces), a crosscut kerf
between pieces. Log pieces then go back up the chain: slices to wedges,
wedges to log sections (eight to a section, each a strut length long).
"""

from __future__ import annotations

import math
from dataclasses import dataclass

from .constants import C
from .patterns import MATERIALS, Layout

CROSSCUT_KERF = 0.125
"""Lost between two pieces cut from one stick (a chop-saw blade)."""


def first_fit(lengths: list[float], stock: float, kerf: float = CROSSCUT_KERF) -> list[list[float]]:
    bins: list[list[float]] = []
    room: list[float] = []
    for L in sorted(lengths, reverse=True):
        need = L + kerf
        for i, r in enumerate(room):
            if r >= need - 1e-9:
                bins[i].append(L)
                room[i] -= need
                break
        else:
            bins.append([L])
            room.append(stock - need)
    return bins


@dataclass
class Plan:
    scope: str
    lines: list[tuple[str, str]]
    """(what, how many / how much) rows for the totals table."""
    cost: float
    kg: float
    warnings: list[str]


def plan(layouts: list[tuple[Layout, int]], scope: str) -> Plan:
    """``layouts``: each panel type's layout and how many triangles use it."""
    if not layouts:
        return Plan(scope, [], 0.0, 0.0, [])
    first = layouts[0][0]
    mat = first.opts.material
    kind = MATERIALS[mat][1]
    spec = first.panel.spec
    lines: list[tuple[str, str]] = []
    warnings: list[str] = []
    cost = 0.0
    kg = sum(L.metrics.get("kg", 0.0) * n for L, n in layouts)
    triangles = sum(n for _L, n in layouts)
    pieces = sum(len(L.pieces) * n for L, n in layouts)
    lines.append(("Triangles", f"{triangles}"))
    lines.append(("Pieces", f"{pieces:,}"))

    if kind in ("log", "board"):
        by_stock: dict[str, list[float]] = {}
        stock_len: dict[str, float] = {}
        labels: dict[str, str] = {}
        for L, n in layouts:
            for p in L.pieces:
                key = p.stock.key
                by_stock.setdefault(key, []).extend([p.long] * n)
                stock_len[key] = p.stock.length
                labels[key] = p.stock.label
        wedge_total = 0
        for key, lens in list(by_stock.items()):
            longest = max(lens)
            if longest > stock_len[key]:
                warnings.append(f"{labels[key]}: the longest piece ({longest:.1f} in) is longer than the "
                                f"stock ({stock_len[key]:.0f} in) -- splice it or choose a shorter run")
            sticks = first_fit([min(x, stock_len[key]) for x in lens], stock_len[key])
            used = sum(lens)
            waste = 1 - used / (len(sticks) * stock_len[key])
            lines.append((f"{labels[key]}: pieces", f"{len(lens):,}  ({used / 12:,.0f} ft of run)"))
            lines.append((f"{labels[key]}: sticks {stock_len[key] / 12:.0f} ft", f"{len(sticks):,}  "
                          f"({100 * waste:.0f}% offcut)"))
            if kind == "board":
                price = C["fence_usd"] if key == "fence" else C["milled_usd"]
                cost += len(sticks) * price
            else:
                per_wedge = {"w8": 1, "s16": 2, "s32": 4}[key]
                wedges = math.ceil(len(sticks) / per_wedge)
                lines.append(("   = wedges to slice" if per_wedge > 1 else "   = wedges", f"{wedges:,}"))
                wedge_total += wedges
        if kind == "log":
            wedges = wedge_total
            sections = math.ceil(wedges / 8)
            lines.append(("Log sections to split", f"{sections:,}  ({spec.max_strut_in / 12:.0f} ft long, "
                          f"{first.opts.infill_log_in:.0f} in across)"))
    elif kind == "round":
        by_d: dict[float, int] = {}
        for L, n in layouts:
            for d, k in L.extra["summary"]["by_diameter"].items():
                by_d[d] = by_d.get(d, 0) + k * n
        t = first.opts.round_t_in
        for d, k in sorted(by_d.items(), reverse=True):
            trunk = k * (t + C["chainsaw_kerf_in"])
            lines.append((f"Rounds Ø{d:g} in, {t:g} in thick", f"{k:,}  ({trunk / 12:,.1f} ft of trunk)"))
        frags = sum(L.extra["summary"]["frags"] * n for L, n in layouts)
        if frags:
            lines.append(("Cut-to-fit gap pieces", f"{frags:,}"))
    elif kind == "sheet":
        per = max(1, first.nest["per_sheet"]) if first.nest else 1
        parts = sum(L.nest["pieces_per_panel"] * n for L, n in layouts)
        sheets = 0
        for L, n in layouts:
            sheets += math.ceil(L.nest["pieces_per_panel"] * n / max(1, L.nest["per_sheet"]))
        lines.append(("Cut pieces", f"{parts:,}"))
        lines.append(("4 x 8 sheets", f"{sheets:,}  ({per} pieces to a sheet, best case)"))
        cost += sheets * (C["osb_usd"] if mat == "osb" else C["ply_usd"])
    elif kind == "film":
        roll_in = sum(L.nest["roll_in_per_piece"] * n for L, n in layouts)
        ft2 = roll_in * C["film_roll_w_in"] / 144.0
        lines.append(("Roll used", f"{roll_in / 12:,.1f} ft of a {C['film_roll_w_in'] / 12:.0f} ft wide roll "
                      f"({ft2:,.0f} sq ft)"))
        cost += ft2 * C["film_usd_ft2"]
    elif kind == "metal":
        lens = []
        for L, n in layouts:
            lens += [p.long for p in L.pieces] * n
        sheets = first_fit(lens, C["metal_l_in"])
        lines.append(("Corrugated panels 26 in x 8 ft", f"{len(sheets):,}"))
        cost += len(sheets) * C["metal_usd"]
        if max(lens) > C["metal_l_in"]:
            warnings.append("a strip is longer than an 8 ft panel: lap two panels end to end")
    lines.append(("Weight added", f"{kg:,.1f} kg  ({kg * 2.2046:,.0f} lb)"))
    if cost:
        lines.append(("Bought materials (estimate)", f"${cost:,.0f}"))
    elif kind in ("log", "round"):
        lines.append(("Bought materials", "none: your own logs"))
    return Plan(scope, lines, cost, kg, warnings)
