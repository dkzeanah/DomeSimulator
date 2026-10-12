"""What the viewer saves: a cut list (CSV), a cut sheet (SVG, to print) and a
picture (PNG), plus a gallery of every pattern for one material. Saved
files never overwrite each other: a name already used gets -v2, -v3 ..."""

from __future__ import annotations

import csv
import textwrap
from pathlib import Path

from . import render
from .constants import table as constants_table
from .draw import PALETTE as P
from .draw import PilPainter, SvgPainter
from .patterns import ARRANGEMENTS, LAYS, MATERIALS, OPTIONS, Layout, Options, layout

ROOT = Path(__file__).resolve().parent.parent
OUT = ROOT / "deliverables" / "infill"


def free_path(path: Path) -> Path:
    from two_v_demo.deliverables import next_version_path
    path.parent.mkdir(parents=True, exist_ok=True)
    return next_version_path(path)


def slug(L: Layout) -> str:
    bits = [L.panel.name, L.opts.mode, L.opts.material, L.opts.arrangement, L.opts.lay]
    return "-".join(b for b in bits if b).lower()


def rows(L: Layout, count: int = 1) -> list[list[str]]:
    out = []
    for i, p in enumerate(L.pieces):
        ends = [e.text() for e in p.ends] + ["", ""]
        out.append([str(i + 1), p.group, MATERIALS[p.material][0], render.POSE_NAME.get(p.pose, p.pose),
                    f"{p.long:.2f}", f"{p.short:.2f}", ends[0], ends[1],
                    f"{p.trim:.2f}" if p.trim > 0.01 else "", str(count), p.note])
    return out


HEADER = ["#", "piece", "material", "how it lies", "long (in)", "short (in)", "end 1", "end 2",
          "rip flush (in)", "triangles", "note"]


def write_csv(layouts: list[tuple[Layout, int]], path: Path) -> Path:
    path = free_path(path)
    with open(path, "w", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        for L, n in layouts:
            w.writerow([f"{L.title} -- {L.panel.label} ({n} triangles)"])
            w.writerow(HEADER)
            w.writerows(rows(L, n))
            w.writerow([])
    return path


def _block(painter, x, y, lines, width_chars=95, size=11, color=P["ink"], line_h=15):
    for line in lines:
        for i, part in enumerate(textwrap.wrap(line, width_chars) or [""]):
            painter.text(x + (14 if i else 0), y, part, color, size, "lt")
            y += line_h
    return y


def sheet(L: Layout, totals: list[tuple[str, str]], painter_cls=SvgPainter, w: int = 1700) -> object:
    """A whole cut sheet: drawings, cut list, steps, fitting, totals."""
    n = len(L.pieces)
    list_rows = min(n, 120)
    h = 880 + 16 * (list_rows + 4) + 16 * (len(L.steps) + len(L.fitting) + len(totals) + 12)
    p = painter_cls(w, h)
    p.text(24, 22, L.title, P["ink"], 22, "lt", bold=True)
    lay = f" — {LAYS[L.opts.lay][1]}" if L.opts.lay else ""
    p.text(24, 54, f"{L.panel.label} ({L.panel.count} on the dome), {L.opts.mode}{lay}", P["muted"], 13, "lt")
    render.plan(p, L, 10, 80, int(w * 0.55), 700)
    render.section(p, L, int(w * 0.56), 80, int(w * 0.42), 330)
    render.legend(p, L, int(w * 0.58), 430)
    y = 800
    p.text(24, y, "Cut list", P["ink"], 15, "lt", bold=True)
    y += 24
    cols = [24, 60, 280, 470, 690, 770, 850]
    for x, head in zip(cols, ["#", "piece", "material", "how it lies", "long", "short", "ends"]):
        p.text(x, y, head, P["muted"], 11, "lt", bold=True)
    y += 17
    for r in rows(L)[:list_rows]:
        vals = [r[0], r[1], r[2], r[3], r[4], r[5], (r[6] + ("; " + r[7] if r[7] else ""))[:120]]
        for x, v in zip(cols, vals):
            p.text(x, y, v, P["ink"], 10, "lt")
        y += 16
    if n > list_rows:
        p.text(24, y, f"... and {n - list_rows} more (see the CSV)", P["muted"], 10, "lt")
        y += 16
    y += 12
    p.text(24, y, "How to cut it", P["ink"], 15, "lt", bold=True)
    y = _block(p, 24, y + 24, L.steps, 150)
    y += 8
    p.text(24, y, "Fitting it", P["ink"], 15, "lt", bold=True)
    y = _block(p, 24, y + 24, L.fitting, 150)
    y += 8
    p.text(24, y, "Totals", P["ink"], 15, "lt", bold=True)
    y += 24
    for a, b in totals:
        p.text(24, y, a, P["ink"], 11, "lt")
        p.text(420, y, b, P["ink"], 11, "lt")
        y += 16
    return p


def write_svg(L: Layout, totals, path: Path) -> Path:
    path = free_path(path)
    path.write_text(sheet(L, totals, SvgPainter).svg(), encoding="utf-8")
    return path


def write_png(L: Layout, totals, path: Path) -> Path:
    path = free_path(path)
    sheet(L, totals, PilPainter).img.save(str(path))
    return path


def gallery(panel, base: Options, path: Path, painter="png") -> Path:
    """Every arrangement and lay this material allows, one tile each."""
    kind = MATERIALS[base.material][1]
    o = OPTIONS[kind]
    combos = []
    for arr in o["arrangements"]:
        for lay in ((o["lays"] if arr != "louvers" else []) or [""]):
            if arr == "rings" and base.mode == "cover":
                continue
            if lay == "shim" and base.material == "s32":
                continue
            combos.append((arr, lay))
    cols = 3
    tw, th = 620, 470
    rows_n = (len(combos) + cols - 1) // cols
    W, H = cols * tw, rows_n * th + 70
    p = PilPainter(W, H) if painter == "png" else SvgPainter(W, H)
    p.text(20, 18, f"{MATERIALS[base.material][0]}: every pattern, {panel.label}, {base.mode}",
           P["ink"], 22, "lt", bold=True)
    for i, (arr, lay) in enumerate(combos):
        L = layout(panel, Options(base.material, arr, lay, base.mode, base.edge, base.infill_log_in,
                                  base.louver_tilt_deg, base.flush))
        x, y = (i % cols) * tw, 60 + (i // cols) * th
        p.rect(x + 4, y + 4, x + tw - 4, y + th - 4, outline=P["grid"])
        name = ARRANGEMENTS[arr] + (f", {LAYS[lay][0].lower()}" if lay else "")
        p.text(x + 14, y + 12, name, P["ink"], 13, "lt", bold=True)
        m = L.metrics
        cover = (f"pattern covers {100 * m['pattern_cover']:.0f}%, cut to fit {100 * m['solid']:.1f}%"
                 if "pattern_cover" in m else f"wood {100 * m.get('solid', 0):.0f}% of the thickness")
        p.text(x + 14, y + 32, f"{len(L.pieces)} pieces · {m.get('kg', 0):.0f} kg · {cover}",
               P["muted"], 11, "lt")
        render.plan(p, L, x, y + 46, int(tw * 0.62), th - 60, numbers=False)
        render.section(p, L, x + int(tw * 0.58), y + 60, int(tw * 0.42), 170)
    path = free_path(path)
    if painter == "png":
        p.img.save(str(path))
    else:
        path.write_text(p.svg(), encoding="utf-8")
    return path


def declared_text(spec, solved) -> str:
    lines = ["SOLVED from your max strut length (two_v_demo.wedge_geometry):",
             f"   dome {solved['diameter_ft']:.2f} ft across, {solved['panels']} triangles"]
    for t in solved["types"]:
        lines.append(f"   {t.label}: {t.count} of them; edges "
                     + ", ".join(f"{c.lower()} {L:.2f} in" for c, L in zip(t.edge_class, t.edge_len))
                     + "; frame sticks " + ", ".join(f"{m:.2f}" for m in t.member_len) + " in; seam folds "
                     + ", ".join(f"{f:.2f}°" if f else "rim" for f in t.folds))
    lines += [f"   frame member: {spec.frame_log_in:g} in log, 1/{spec.splits} sector, lying on a sawn face",
              f"   frame thickness {spec.thickness_in:.2f} in; opening walls at {spec.wall_deg:.1f}°", "",
              "DECLARED (typed in by a person; change them in infill/constants.py):", constants_table()]
    return "\n".join(lines)
