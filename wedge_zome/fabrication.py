"""The wedge zome's fabrication package: what to cut, how, and in what order.

    py -3.12 -m wedge_zome.fabrication            # a new numbered package in deliverables/zome/
    py -3.12 -m wedge_zome.fabrication --method square

Everything in it is read from :mod:`wedge_zome.geometry`: the stick types and
their saw settings, the panel jigs drawn to scale, the seam channels, the rim
posts, the stock the frame takes, and -- for the square method -- the wedge
blocks and the end-grain templates that split them.
"""

from __future__ import annotations

import csv
import html
import json
import math
from pathlib import Path

import numpy as np

from . import geometry as g

ROOT = Path(__file__).resolve().parents[1]
OUT_DIR = ROOT / "deliverables" / "zome"
E = html.escape


def facts(method: str = "wedge", model=None) -> dict:
    """Every figure the how-to, the app's HUD and the film quote, in one place."""
    from square_book import geometry as sg

    m = model or g.build(method)
    other = g.build("square" if m.method == "wedge" else "wedge", m.log_in, m.side_in, m.hand)
    method = m.method
    types = g.stick_types(m)
    rows = g.rows(m)
    stock = g.stock(m)
    gaps = [s.gap for s in m.seams]
    from two_v_demo import panel_method as pm
    zrows = pm.reference_zome()
    w = m.wedge
    return {
        "method": method, "panels": len(m.panels), "rows": rows, "types": types, "stock": stock,
        "other_stock": g.stock(other), "seams": len(m.seams), "gap_lo": min(gaps), "gap_hi": max(gaps),
        "fold_lo": min(s.fold for s in m.seams), "fold_hi": max(s.fold for s in m.seams),
        "posts": len(m.posts), "post_h": max(h for _, h in m.posts) if m.posts else 0.0,
        "rim_corners": len(m.rim), "stick_w": m.stick_w, "stick_h": m.stick_h,
        "theta": w.theta, "half": w.theta / 2, "log": m.log_in, "splits": int(g.D["splits"]),
        "section": g.D["section_in"], "side": float(np.linalg.norm(m.vertices[m.panels[0].corners[1]]
                                                                      - m.vertices[m.panels[0].corners[0]])),
        "height_ft": float(m.vertices[:, 2].max()) / 12.0,
        "rim_ft": 2 * float(np.max(np.linalg.norm(m.vertices[:, :2], axis=1))) / 12.0,
        "blocks": g.blocks(g.build("square", m.log_in, m.side_in, m.hand)),
        "post_square": sg.Pair(sg.Wedge(m.log_in, 4), "back").planed[0],
        "dome_sections": None,
        "zome_rows_book": len(zrows),
    }


def _md_table(header: list[str], rows: list[list]) -> str:
    out = ["| " + " | ".join(header) + " |", "|" + "---|" * len(header)]
    out += ["| " + " | ".join(str(c) for c in r) + " |" for r in rows]
    return "\n".join(out)


def how_to(method: str = "wedge", model=None) -> str:
    f = facts(method, model)
    method = f["method"]
    s = f["stock"]
    types = f["types"]
    lines = [f"# The Wedge Zome: How to Cut and Build It", ""]
    lines += [
        f"A nine-sided zome of {f['panels']} rhombus panels in {len(f['rows'])} rows, "
        f"{f['rim_ft']:.1f} ft across and {f['height_ft']:.1f} ft tall, every panel side "
        f"{f['side']:.2f} in. It is the Complete Edition's zome, framed with wedges split "
        f"{f['splits']} ways from a {f['log']:.0f} in log -- the same wedges that frame the dome.", ""]
    if method == "wedge":
        lines += [
            "## The idea in one paragraph", "",
            f"Every panel is four wedge sticks in a pinwheel, framed flat on a jig, with the "
            f"stick's flat back on the **outside** and its point toward the inside. A wedge's sides "
            f"lean {f['half']:.1f}° away from square, so where two panels fold together their backs "
            f"close tight along the outside seam and the inside opens into a V of {f['gap_lo']:.1f}° "
            f"to {f['gap_hi']:.1f}° -- the wedge's {f['theta']:.0f}° point less the fold, which runs "
            f"from {f['fold_lo']:.1f}° to {f['fold_hi']:.1f}°. No block fills anything. The inside V "
            f"is a channel for wire, air or water, capped or left open.", ""]
    else:
        lines += [
            "## The idea in one paragraph", "",
            f"Every panel is four square sticks -- two wedges paired slant to slant and planed "
            f"{f['stick_w']:.2f} in square -- in a pinwheel, framed flat. Square-edged panels meet "
            f"on their inside edges and open a V outside of the fold, {f['fold_lo']:.1f}° to "
            f"{f['fold_hi']:.1f}°, which a wedge block fills.", ""]
    lines += ["## What it takes", "",
              _md_table(["", "this method", "the other method"],
                        [["sticks", s["sticks"], f["other_stock"]["sticks"]],
                         [f"wedges, {f['section']:.0f} in long", s["wedges"], f["other_stock"]["wedges"]],
                         [f"log sections, split {f['splits']} ways", s["sections"],
                          f["other_stock"]["sections"]],
                         ["sticks from one wedge", s["sticks_per_wedge"], f["other_stock"]["sticks_per_wedge"]]]),
              ""]
    lines += ["## Every stick, and how to cut it", "",
              "Lay the stick **back down** on the saw table with the edge it runs along against the "
              "fence" + (f", a {f['half']:.1f}° shim under the fence side so the sloping face bears "
                         f"flat -- the shim is a wedge split {2 * f['splits']} ways" if method == "wedge"
                         else "") + ". Mitre is the blade's swing on the table, bevel its tilt.", "",
              _md_table(["stick", "row", "how many", "length, outside edge", "tail: mitre, bevel",
                         "head: mitre, bevel"],
                        [[t["name"], t["row"], t["count"], f"{t['outer']:.2f} in",
                          f"{abs(t['tail'][0]):.1f}° {'L' if t['tail'][0] < 0 else 'R'}, {abs(t['tail'][1]):.1f}°",
                          f"{abs(t['head'][0]):.1f}° {'L' if t['head'][0] < 0 else 'R'}, {abs(t['head'][1]):.1f}°"]
                         for t in types]), ""]
    if method == "wedge":
        bevels = {round(abs(t["tail"][1]), 1) for t in types} | {round(abs(t["head"][1]), 1) for t in types}
        lines += [f"Every end of every stick takes the same bevel, {', '.join(f'{b:.1f}°' for b in sorted(bevels))} "
                  f"-- half the wedge's point. Set it once. Only the mitre changes, once per row, and the "
                  f"two stick types in a row are mirror images: the same mitre swung the other way.", ""]
    lines += ["## The rows", "",
              f"Row 1 is the crown, the {f['rows'][0]['panels']} panels round the point; row "
              f"{len(f['rows'])} stands on the sill.", "",
              _md_table(["row", "panels", "sharp corner", "largest fold",
                         "inside V" if method == "wedge" else "outside V"],
                        [[r["row"], r["panels"], f"{r['acute']:.1f}°", f"{r['fold_max']:.1f}°",
                          f"{r['gap_min']:.1f}°–{r['gap_max']:.1f}°"] for r in f["rows"]]), ""]
    if method == "square":
        lines += ["## The wedge blocks", "",
                  "A block's point is 360° divided by the number of ways its log is split, and the V it "
                  "fills is the fold, so each fold wants a log split 360/fold ways. Mark the split on the "
                  "end grain with the template for that fold.", "",
                  _md_table(["fold", "seams", "split exactly", "split", "off by"],
                            [[f"{b['fold']:.1f}°", b["count"], f"{b['split_exact']:.1f} ways", f"{b['split']} ways",
                              f"{b['split_error']:+.1f}°"] for b in f["blocks"]]), ""]
    lines += ["## Order of work", "",
              f"1. **Buck and split.** Buck {s['sections']} sections, {f['section']:.0f} in long; rip each "
              f"{f['splits']} ways through the pith with the chainsaw, never alone. Trim the backs flat.",
              f"2. **Cut the sticks.** {s['sticks_per_wedge']} sticks from each wedge. Set the bevel once; "
              "cut every stick of a row before changing the mitre.",
              "3. **Build the jig, one per row.** Screw stops to a sheet at the row's rhombus outline, full "
              "size, from the jig drawing for that row.",
              "4. **Frame the panels.** Four sticks in a pinwheel: each runs to the corner ahead of it and "
              "its tail butts the side of the stick behind. Glue and screw at each butt, in the thick part, "
              "pilot holes always.",
              f"5. **The sill and the rim posts.** The rim zigzags: {f['rim_corners']} corners, "
              f"{f['posts']} of them {f['post_h']:.1f} in above the sill. Stand a post under each high "
              f"corner -- two quarters back to back make a square post {f['post_square']:.2f} in on a side.",
              "6. **Raise, bottom row up.** Fasten panels to each other through the outside seam. Brace the "
              "top rows: they sag until the ring closes.",
              "7. **Close the seams.** " + ("The outside seams are closed by the backs: seal them with the "
                                          "seam cap. The inside V is a channel -- run wire or air in it, then "
                                          "cap it." if method == "wedge" else
                                          "Fill each outside V with its wedge block, then seal."),
              "", "## Before anyone lives in it", "",
              "This is a method, not a rated structure. Have a licensed engineer check the frame for wind "
              "and snow, and the fastening schedule, before it is occupied.", ""]
    return "\n".join(lines)


def jig_svg(model: g.ZomeModel, row: int) -> str:
    """One panel of the row, flat, full size: its outline and its four sticks' backs."""
    p = next(p for p in model.panels if p.row == row)
    pts = [model.vertices[k] for k in p.corners]
    x = g.unit(pts[1] - pts[0])
    y = np.cross(p.normal, x)

    def flat(q):
        r = q - pts[0]
        return float(r @ x), float(r @ y)

    outline = [flat(q) for q in pts]
    polys = []
    for s in p.sticks:
        tails, heads = s.ends
        back = [tails[0], heads[0], heads[1], tails[1]]
        polys.append([flat(q) for q in back])
    xs = [u for u, _ in outline] + [u for poly in polys for u, _ in poly]
    ys = [v for _, v in outline] + [v for poly in polys for _, v in poly]
    pad = 2.0
    x0, y0 = min(xs) - pad, min(ys) - pad
    w, h = max(xs) - x0 + pad, max(ys) - y0 + pad

    def pt(u, v):
        return f"{u - x0:.3f},{h - (v - y0):.3f}"

    body = [f'<polygon points="{" ".join(pt(*q) for q in outline)}" fill="none" stroke="#111" stroke-width="0.06"/>']
    for k, poly in enumerate(polys):
        body.append(f'<polygon points="{" ".join(pt(*q) for q in poly)}" fill="#e2b98f" stroke="#7a4a1e" '
                    f'stroke-width="0.05"/>')
        cu = sum(q[0] for q in poly) / 4
        cv = sum(q[1] for q in poly) / 4
        body.append(f'<text x="{cu - x0:.2f}" y="{h - (cv - y0):.2f}" font-size="1.2" text-anchor="middle" '
                    f'font-family="Segoe UI, Arial">{k + 1}</text>')
    body.append(f'<text x="1" y="1.6" font-size="1.1" font-family="Segoe UI, Arial">ROW {row} JIG -- full size, '
                f'inches. Print at 100%. Sharp corner {p.acute:.1f}°.</text>')
    return (f'<svg xmlns="http://www.w3.org/2000/svg" width="{w:.2f}in" height="{h:.2f}in" '
            f'viewBox="0 0 {w:.2f} {h:.2f}">' + "".join(body) + "</svg>")


def template_svg(split: int, diameter_in: float) -> str:
    """An end-grain template: a circle the log's size with `split` radial lines."""
    r = diameter_in / 2
    c = r + 0.6
    lines = [f'<circle cx="{c}" cy="{c}" r="{r}" fill="none" stroke="#111" stroke-width="0.05"/>']
    for k in range(split):
        a = math.tau * k / split
        lines.append(f'<line x1="{c}" y1="{c}" x2="{c + r * math.cos(a):.3f}" y2="{c + r * math.sin(a):.3f}" '
                     f'stroke="#b0601e" stroke-width="0.04"/>')
    lines.append(f'<text x="0.3" y="0.5" font-size="0.45" font-family="Segoe UI, Arial">{split} WAYS -- '
                 f'{360 / split:.2f}° each. Full size for a {diameter_in:.0f} in log.</text>')
    size = 2 * c
    return (f'<svg xmlns="http://www.w3.org/2000/svg" width="{size:.2f}in" height="{size:.2f}in" '
            f'viewBox="0 0 {size:.2f} {size:.2f}">' + "".join(lines) + "</svg>")


def _next_dir(stem: str) -> Path:
    """A new kit folder in the library: the item's folder, ``stem``, ``stem-v2``...
    (returned not yet created, as before)."""
    import medialib
    return medialib.route(OUT_DIR / stem)


def export(method: str = "wedge", model=None) -> Path:
    from two_v_demo import book_export
    from wedge_book import print_edition as pe

    m = model or g.build(method)
    method = m.method
    out = _next_dir(f"wedge-zome-{method}")
    out.mkdir(parents=True)
    md = how_to(method, m)
    (out / "how-to.md").write_text(md, encoding="utf-8")
    body = book_export._markdown_to_html(md)
    page = (f'<!doctype html><html><head><meta charset="utf-8"><title>The Wedge Zome</title>'
            f"<style>{book_export.BOOK_CSS}{pe.PRINT_CSS} table{{font-size:9pt}}</style></head>"
            f'<body><main class="wrap">{body}</main></body></html>')
    (out / "how-to.html").write_text(page, encoding="utf-8")
    chrome = book_export._chrome_path()
    if chrome:
        book_export._pdf_via_chrome(page, out / "how-to.pdf", chrome)
    with (out / "cut-schedule.csv").open("w", newline="", encoding="utf-8") as fh:
        w = csv.writer(fh)
        w.writerow(["stick", "row", "count", "outside_edge_in", "tail_mitre_deg", "tail_bevel_deg",
                    "head_mitre_deg", "head_bevel_deg"])
        for t in g.stick_types(m):
            w.writerow([t["name"], t["row"], t["count"], f"{t['outer']:.3f}", f"{t['tail'][0]:.2f}",
                        f"{t['tail'][1]:.2f}", f"{t['head'][0]:.2f}", f"{t['head'][1]:.2f}"])
    for r in m.rows:
        (out / f"jig-row-{r}.svg").write_text(jig_svg(m, r), encoding="utf-8")
    if method == "square":
        for b in g.blocks(m):
            (out / f"block-template-{b['split']}-ways.svg").write_text(template_svg(b["split"], g.D["log_in"]),
                                                                        encoding="utf-8")
    f = facts(method, m)
    (out / "summary.json").write_text(json.dumps({k: v for k, v in f.items() if k != "types"} | {
        "types": [{k: v for k, v in t.items()} for t in f["types"]]}, indent=2, default=float), encoding="utf-8")
    return out


def main(argv: list[str] | None = None) -> int:
    import argparse

    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--method", choices=("wedge", "square"), default="wedge")
    args = parser.parse_args(argv)
    g.validate()
    print(f"wrote {export(args.method)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
