"""The cut list as a PDF: the pages follow the order of the work.

What it is and what it is not, the declared allowances, the saw setups, the cut families,
the log plan, the jigs, the seams, the jig procedure, the infill takeoff, every member, and
the self-checks with the files they came from. Drawn with reportlab from the solved model;
no GPU, so the site's render script can run it anywhere.
"""

from __future__ import annotations

import math
from pathlib import Path

import numpy as np
from reportlab.graphics.shapes import Drawing, Line, PolyLine, Polygon, Rect, String
from reportlab.lib import colors
from reportlab.lib.enums import TA_LEFT
from reportlab.lib.pagesizes import letter
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import inch
from reportlab.platypus import (KeepTogether, PageBreak, Paragraph, SimpleDocTemplate, Spacer, Table,
                                TableStyle)

from .design import ORIENTATIONS, PATTERNS, SEAM_JOINS, Design, feet, inches

INK = colors.HexColor("#1f2328")
MUTED = colors.HexColor("#5b636b")
ACCENT = colors.HexColor("#9a5b1f")
LINE = colors.HexColor("#d5d0c8")
PAPER = colors.HexColor("#f6f2ea")
VARIANT = ["#e3a64b", "#7fb2d6", "#9cc27a", "#d98b8b", "#b49ad6", "#e0cf6a", "#8fd0c4", "#c9a07a"]
W = letter[0] - 1.5 * inch   # frame width

_ss = getSampleStyleSheet()
H1 = ParagraphStyle("h1", parent=_ss["Heading1"], fontName="Helvetica-Bold", fontSize=20, leading=24, textColor=INK, spaceAfter=6)
H2 = ParagraphStyle("h2", parent=_ss["Heading2"], fontName="Helvetica-Bold", fontSize=13, leading=16, textColor=ACCENT, spaceBefore=10, spaceAfter=4)
P = ParagraphStyle("p", parent=_ss["BodyText"], fontName="Helvetica", fontSize=9.5, leading=13, textColor=INK, alignment=TA_LEFT)
SMALL = ParagraphStyle("small", parent=P, fontSize=8, leading=10.5, textColor=MUTED)
CELL = ParagraphStyle("cell", parent=P, fontSize=8, leading=10)


def _table(rows, widths, header=True, size=8, zebra=True):
    data = [[c if hasattr(c, "wrap") else Paragraph(str(c), CELL) for c in r] for r in rows]
    t = Table(data, colWidths=widths, repeatRows=1 if header else 0)
    style = [("FONT", (0, 0), (-1, -1), "Helvetica", size), ("VALIGN", (0, 0), (-1, -1), "TOP"),
             ("LINEBELOW", (0, 0), (-1, -1), 0.25, LINE), ("LEFTPADDING", (0, 0), (-1, -1), 3),
             ("RIGHTPADDING", (0, 0), (-1, -1), 3), ("TOPPADDING", (0, 0), (-1, -1), 2), ("BOTTOMPADDING", (0, 0), (-1, -1), 2)]
    if header:
        style += [("BACKGROUND", (0, 0), (-1, 0), PAPER), ("LINEBELOW", (0, 0), (-1, 0), 0.8, ACCENT)]
    if zebra:
        style += [("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, colors.HexColor("#fbf9f5")])]
    t.setStyle(TableStyle(style))
    return t


def _b(text):
    return Paragraph(f"<b>{text}</b>", CELL)


def deg(x: float) -> str:
    return f"{x:.2f}°"


# ---------------------------------------------------------------- drawings

def _variant_of(d: Design) -> dict[int, int]:
    return {p: v for v, panels in enumerate(d.variants) for p in panels}


def _view(d: Design, az: float, el: float, width: float, height: float, labels: bool = False) -> Drawing:
    """The dome's panels, painted far to near, coloured by the jig each is built on. A labelled
    view (the plan) is flat-coloured so every number reads."""
    topo = d.model.topology
    a, e = math.radians(az), math.radians(el)
    cam = np.array([math.cos(e) * math.cos(a), math.cos(e) * math.sin(a), math.sin(e)])
    up = np.array([0.0, 0.0, 1.0])
    right = np.cross(up, cam)
    if np.linalg.norm(right) < 1e-9:
        right = np.array([1.0, 0.0, 0.0])
    right /= np.linalg.norm(right)
    upv = np.cross(cam, right)
    V = topo.vertices
    xy = np.stack([V @ right, V @ upv], axis=1)
    lo, hi = xy.min(axis=0), xy.max(axis=0)
    s = min((width - 20) / (hi[0] - lo[0]), (height - 20) / (hi[1] - lo[1]))
    ox = (width - s * (hi[0] - lo[0])) / 2 - s * lo[0]
    oy = (height - s * (hi[1] - lo[1])) / 2 - s * lo[1]
    dr = Drawing(width, height)
    light = np.array([0.4, -0.5, 0.75]) / np.linalg.norm([0.4, -0.5, 0.75])
    vof = _variant_of(d)
    order = sorted(range(len(topo.faces)), key=lambda i: float(topo.faces[i].center @ cam))
    for i in order:
        f = topo.faces[i]
        pts = []
        for vi in f.vertices:
            pts += [ox + s * xy[vi, 0], oy + s * xy[vi, 1]]
        base = colors.HexColor(VARIANT[vof[i] % len(VARIANT)])
        k = 1.0 if labels else 0.55 + 0.45 * max(0.0, float(f.normal @ light))
        if float(f.normal @ cam) < 0:
            k *= 0.6
        fill = colors.Color(base.red * k, base.green * k, base.blue * k)
        dr.add(Polygon(pts, fillColor=fill, strokeColor=INK, strokeWidth=0.6))
        if labels and float(f.normal @ cam) > 0.0:
            c = f.center
            dr.add(String(ox + s * float(c @ right), oy + s * float(c @ upv) - 2.5, f"{i + 1}",
                          fontName="Helvetica", fontSize=6, fillColor=INK, textAnchor="middle"))
    return dr


def _clip_poly(pts, x0, y0, x1, y1):
    """Sutherland-Hodgman: a polygon cut to an axis-aligned box."""
    def cut(ps, inside, meet):
        out = []
        for i, cur in enumerate(ps):
            prev = ps[i - 1]
            if inside(cur):
                if not inside(prev):
                    out.append(meet(prev, cur))
                out.append(cur)
            elif inside(prev):
                out.append(meet(prev, cur))
        return out

    def at_x(x):
        return lambda a, b: (x, a[1] + (b[1] - a[1]) * (x - a[0]) / (b[0] - a[0]))

    def at_y(y):
        return lambda a, b: (a[0] + (b[0] - a[0]) * (y - a[1]) / (b[1] - a[1]), y)

    for inside, meet in ((lambda p: p[0] >= x0, at_x(x0)), (lambda p: p[0] <= x1, at_x(x1)),
                         (lambda p: p[1] >= y0, at_y(y0)), (lambda p: p[1] <= y1, at_y(y1))):
        pts = cut(pts, inside, meet)
        if not pts:
            break
    return pts


def _clip_seg(a, b, x0, y0, x1, y1):
    """Liang-Barsky: the part of segment ab inside the box, or None."""
    dx, dy = b[0] - a[0], b[1] - a[1]
    t0, t1 = 0.0, 1.0
    for p, q in ((-dx, a[0] - x0), (dx, x1 - a[0]), (-dy, a[1] - y0), (dy, y1 - a[1])):
        if abs(p) < 1e-12:
            if q < 0:
                return None
            continue
        t = q / p
        if p < 0:
            t0 = max(t0, t)
        else:
            t1 = min(t1, t)
        if t0 > t1:
            return None
    return (a[0] + t0 * dx, a[1] + t0 * dy), (a[0] + t1 * dx, a[1] + t1 * dy)


def _jig_parts(d: Design, panel: int) -> dict:
    """The jig drawing's pieces in panel inches (exterior view): the same geometry the
    solver's export_panel_jig_svg draws."""
    sim, model = d.sim, d.model
    frame = sim._panel_frame(model, panel)
    face = model.topology.faces[panel]
    tail = model.config.jig_butt_hangoff_in
    xy = lambda p: sim._panel_xy(p, frame)
    members = []
    for m in sorted([m for m in model.members if m.face_index == panel], key=lambda m: m.local_edge_index):
        origin = m.nominal_start + m.point_offset_in * m.inward
        members.append({
            "m": m,
            "head": xy(origin + m.receiving_axis_parameter_in * m.tangent),
            "butt": xy(origin + m.butt_axis_parameter_in * m.tangent),
            "tail": xy(origin + (m.butt_axis_parameter_in + tail) * m.tangent),
            "head_cut": [xy(p) for p in m.receiving_cut_points],
            "butt_cut": [xy(p) for p in m.butt_contact_points],
        })
    return {"tri": [xy(model.topology.vertices[i]) for i in face.vertices], "members": members}


JIG_COLOURS = {"tri": "#1976a8", "axis": "#c57800", "tail": "#ff8800", "head": "#cc00cc", "butt": "#00a8d6"}


def _jig_paint(d: Design, parts: dict, window, width: float, height: float, labels: bool) -> Drawing:
    """Paint the jig parts that fall inside ``window`` (panel inches) into a width x height box."""
    x0, y0, x1, y1 = window
    s = min(width / (x1 - x0), height / (y1 - y0))
    ox = (width - s * (x1 - x0)) / 2 - s * x0
    oy = (height - s * (y1 - y0)) / 2 - s * y0
    T = lambda p: (ox + s * p[0], oy + s * p[1])
    dr = Drawing(width, height)

    def poly(pts, fill, stroke, w):
        c = _clip_poly(list(pts), x0, y0, x1, y1)
        if len(c) >= 3:
            flat = [v for p in c for v in T(p)]
            dr.add(Polygon(flat, fillColor=fill, strokeColor=None))
        closed = list(pts) + [pts[0]]
        for a, b in zip(closed, closed[1:]):
            seg(a, b, stroke, w)

    def seg(a, b, stroke, w, opacity=1.0):
        c = _clip_seg(a, b, x0, y0, x1, y1)
        if c:
            dr.add(Line(*T(c[0]), *T(c[1]), strokeColor=colors.HexColor(stroke), strokeWidth=w, strokeOpacity=opacity))

    poly(parts["tri"], colors.HexColor("#eef4f8"), JIG_COLOURS["tri"], 1.2)
    for p in parts["members"]:
        seg(p["butt"], p["tail"], JIG_COLOURS["tail"], 5, 0.45)
        seg(p["head"], p["butt"], JIG_COLOURS["axis"], 1.2)
        for key, colour in (("head_cut", "head"), ("butt_cut", "butt")):
            ring = p[key] + [p[key][0]]
            for a, b in zip(ring, ring[1:]):
                seg(a, b, JIG_COLOURS[colour], 1.4)
        if labels:
            mx, my = T(((p["head"][0] + p["butt"][0]) / 2, (p["head"][1] + p["butt"][1]) / 2))
            dr.add(String(mx, my + 5, f"{d.family_of[p['m'].member_id]}  {p['m'].physical_stock_length_in:.3f} in",
                          fontName="Helvetica-Bold", fontSize=8, fillColor=INK, textAnchor="middle"))
    dr.add(Rect(0, 0, width, height, fillColor=None, strokeColor=LINE, strokeWidth=0.5))
    # a scale bar: 12 in, or 2 in on a close-up
    bar = 12.0 if (x1 - x0) > 40 else 2.0
    dr.add(Line(6, 8, 6 + s * bar, 8, strokeColor=INK, strokeWidth=1.5))
    dr.add(String(10 + s * bar, 5, f"{bar:g} in", fontName="Helvetica", fontSize=7, fillColor=MUTED))
    return dr


def _jig(d: Design, panel: int, width: float) -> list:
    """The whole panel, then a close-up of each corner, where the two cuts actually are."""
    parts = _jig_parts(d, panel)
    pts = list(parts["tri"]) + [q for p in parts["members"] for q in p["head_cut"] + p["butt_cut"] + [p["tail"]]]
    xs, ys = [p[0] for p in pts], [p[1] for p in pts]
    pad = 3.0
    whole = _jig_paint(d, parts, (min(xs) - pad, min(ys) - pad, max(xs) + pad, max(ys) + pad), width, 4.6 * inch, True)
    legend = Paragraph(" &nbsp; ".join(f'<font color="{JIG_COLOURS[k]}">\u25a0</font> {t}' for k, t in (
        ("head", "head cut (sawn in place on the jig)"), ("butt", "butt plane (where the next butt lands)"),
        ("tail", f"{d.config.jig_butt_hangoff_in:g} in sacrificial tail"), ("tri", "mathematical triangle"))), SMALL)
    box = (width - 12) / 3
    half = 7.0
    insets = []
    for k, corner in enumerate(parts["tri"]):
        insets.append(_jig_paint(d, parts, (corner[0] - half, corner[1] - half, corner[0] + half, corner[1] + half), box, box, False))
    vertices = d.model.topology.faces[panel].vertices
    ms = [p["m"] for p in parts["members"]]

    def caption(k: int) -> Paragraph:
        butt = next(m for m in ms if m.butt_vertex == vertices[k])
        head = next(m for m in ms if m.receiving_vertex == vertices[k])
        return Paragraph(f"Corner {k + 1} ({2 * half:g} in square): {d.family_of[butt.member_id]}'s butt lands on the side of "
                         f"{d.family_of[head.member_id]}, whose head is cut here", SMALL)
    row = Table([insets, [caption(k) for k in range(3)]],
                colWidths=[box + 4] * 3)
    row.setStyle(TableStyle([("LEFTPADDING", (0, 0), (-1, -1), 0), ("RIGHTPADDING", (0, 0), (-1, -1), 4)]))
    return [legend, Spacer(1, 3), whole, Spacer(1, 6), row]


def _logs_drawing(d: Design, width: float) -> Drawing:
    L = d.request.log_ft * 12
    row = 22
    dr = Drawing(width, row * len(d.logs) + 10)
    s = (width - 50) / L
    for i, log in enumerate(d.logs):
        y = dr.height - (i + 1) * row
        dr.add(String(0, y + 6, f"Log {i + 1}", fontName="Helvetica-Bold", fontSize=8, fillColor=INK))
        dr.add(Rect(44, y, s * L, 16, fillColor=colors.HexColor("#efe7da"), strokeColor=LINE))
        x = 44
        for r in log:
            dr.add(Rect(x, y, s * r.length_in, 16, fillColor=colors.HexColor("#d9b98c"), strokeColor=ACCENT, strokeWidth=0.6))
            dr.add(String(x + s * r.length_in / 2, y + 5, f"R{r.number}  {feet(r.length_in)}", fontName="Helvetica",
                          fontSize=7, fillColor=INK, textAnchor="middle"))
            x += s * (r.length_in + 0.125)
    return dr


# ---------------------------------------------------------------- the alternating build

def _orientation_view(d: Design, width: float, height: float) -> Drawing:
    """The dome from above, each panel numbered, pale where its wedges point in and dark where they point out."""
    topo, o = d.model.topology, d.model.panel_orientations
    V = topo.vertices
    lo, hi = V[:, :2].min(axis=0), V[:, :2].max(axis=0)
    s = min((width - 20) / (hi[0] - lo[0]), (height - 20) / (hi[1] - lo[1]))
    ox = (width - s * (hi[0] - lo[0])) / 2 - s * lo[0]
    oy = (height - s * (hi[1] - lo[1])) / 2 - s * lo[1]
    dr = Drawing(width, height)
    for i in sorted(range(len(topo.faces)), key=lambda i: float(topo.faces[i].center[2])):
        f = topo.faces[i]
        pts = [v for vi in f.vertices for v in (ox + s * V[vi, 0], oy + s * V[vi, 1])]
        inn = o[i] == "point_dome_in"
        dr.add(Polygon(pts, fillColor=colors.HexColor("#f3dfb4" if inn else "#5a3a24"), strokeColor=INK, strokeWidth=0.6))
        dr.add(String(ox + s * float(f.center[0]), oy + s * float(f.center[1]) - 2.5, f"{i + 1}", fontName="Helvetica-Bold",
                      fontSize=6.5, fillColor=INK if inn else colors.white, textAnchor="middle"))
    return dr


def _pattern_page(d: Design) -> list:
    sim, model = d.sim, d.model
    topo, o = model.topology, model.panel_orientations
    bands = sim.panel_bands(topo)
    word = lambda i: "IN" if o[i] == "point_dome_in" else "OUT"
    pair = lambda se: "in/out" if o[se.face_a] != o[se.face_b] else ("in/in" if o[se.face_a] == "point_dome_in" else "out/out")
    out = [Paragraph("Which way each panel points", H1), Paragraph(
        "Alternating the wedges cancels their angle: where an in-pointing wedge meets an out-pointing one, their sawn "
        "faces were parallel before the fold, so the key fills only the fold. Where two wedges pointing the same way meet "
        "(a matched seam), the key fills more. Build ground up, band by band, walking round each band in the order listed.", P)]
    out.append(Table([[_orientation_view(d, W * 0.55, 3.0 * inch), Paragraph(
        "Pale: the wedge's point faces the dome's centre (IN). Dark: it faces the sky (OUT); that panel sits one log radius "
        "further out so both kinds share one shell thickness. Numbers are panel numbers, seen from above.", SMALL)]],
        colWidths=[W * 0.58, W * 0.42]))
    rows = [["Seam kind", "Seams", "Key fills (each)", "Against in/out on that edge"]]
    kinds = {}
    for se in model.seams:
        alt = sim.seam_face_gap_deg(model.config, "point_dome_in", "point_dome_out", se.inward_a, se.normal_a, se.inward_b, se.normal_b)
        k = kinds.setdefault((se.edge_type, pair(se)), [0, se.raw_gap_angle_deg, se.raw_gap_angle_deg - alt])
        k[0] += 1
    for (et, pr), (n, gap, extra) in sorted(kinds.items()):
        rows.append([f"{et} seams, {pr}", n, deg(gap), "the same" if abs(extra) < 1e-6 else f"+{extra:.2f}\u00b0"])
    out.append(_table(rows, [1.6 * inch, 0.7 * inch, 1.3 * inch, W - 3.6 * inch]))
    out.append(Spacer(1, 4))
    rows = [["Band", "Walk order: panel (type) IN / OUT", "Matched seams it closes"]]
    for b in sorted(set(bands)):
        ring = sim.ring_order(topo, [i for i in range(len(bands)) if bands[i] == b])
        closes = [se for se in model.seams if max(bands[se.face_a], bands[se.face_b]) == b and pair(se) != "in/out"]
        rows.append([_b(str(b)), ", ".join(f"{i + 1} ({topo.faces[i].face_type}) {word(i)}" for i in ring),
                     ", ".join(f"{se.seam_id} {pair(se)}" for se in closes) or "none"])
    out.append(_table(rows, [0.45 * inch, W * 0.62, W - 0.45 * inch - W * 0.62], size=7))
    out.append(Spacer(1, 4))
    out.append(Paragraph(
        "Why not every seam can alternate: the apex and the five vertices just above the second band each have five panels "
        "round them. In and out cannot alternate round an odd number, so each needs at least one matched seam. This "
        "pattern puts them where they cost least.", SMALL))
    out.append(PageBreak())
    return out


# ---------------------------------------------------------------- pages

def build(d: Design, path: Path, made_for: str = "") -> Path:
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    failed = [c for c in d.checks if not c[1]]
    if failed:
        raise ValueError("Self-checks failed: " + "; ".join(c[0] for c in failed))
    req, cfg, topo = d.request, d.config, d.model.topology
    title = req.label or f"{req.diameter_ft:g} ft wedge dome"

    def chrome(canvas, doc):
        canvas.saveState()
        canvas.setFont("Helvetica", 7.5)
        canvas.setFillColor(MUTED)
        canvas.drawString(0.75 * inch, 0.5 * inch, f"Wedge Dome Cut List  ·  {title}  ·  design {d.provenance['design']}"
                          + (f"  ·  {made_for}" if made_for else ""))
        canvas.drawRightString(letter[0] - 0.75 * inch, 0.5 * inch, f"page {doc.page}")
        canvas.setStrokeColor(ACCENT)
        canvas.setLineWidth(0.8)
        canvas.line(0.75 * inch, letter[1] - 0.55 * inch, letter[0] - 0.75 * inch, letter[1] - 0.55 * inch)
        canvas.restoreState()

    doc = SimpleDocTemplate(str(path), pagesize=letter, leftMargin=0.75 * inch, rightMargin=0.75 * inch,
                            topMargin=0.75 * inch, bottomMargin=0.75 * inch, title=f"Wedge Dome Cut List: {title}",
                            author="zeanahlab.com", subject=f"design {d.provenance['design']}")
    s: list = []
    height = float(topo.vertices[:, 2].max())
    total_finished = sum(m.physical_stock_length_in for m in d.model.members) / 12
    total_raw = sum(f.raw_blank_in * f.count for f in d.families) / 12

    # ---- 1. cover
    s += [Paragraph("Wedge Dome Cut List", H1), Paragraph(title, H2)]
    s.append(_table([
        [_b("Your inputs"), "", _b("Solved"), ""],
        ["Floor diameter", f"{req.diameter_ft:g} ft", "Floor area", f"{d.floor_area_sqft:,.0f} sq ft"],
        ["Log diameter (small end)", f"{req.log_in:g} in", "Height (centreline)", feet(height)],
        ["Usable log length", f"{req.log_ft:g} ft", "Long / short edge", f"{topo.long_edge_in:.2f} / {topo.short_edge_in:.2f} in"],
        ["Wedge orientation", PATTERNS[req.pattern] if req.mixed else ORIENTATIONS[req.orientation], "Panels / members / seams", f"{len(topo.faces)} / {len(d.model.members)} / {sum(x['count'] for x in d.seams)}"],
        ["Seam join", SEAM_JOINS[req.seam_join], "Saw setups / cut families / jigs", f"{len(d.setups)} / {len(d.families)} / {len(d.variants)}"],
        ["", "", "Logs / rounds", f"{len(d.logs)} logs, {len(d.rounds)} rounds"],
        ["", "", "Frame stock finished / raw", f"{total_finished:,.0f} ft / {total_raw:,.0f} ft"],
    ], [1.45 * inch, 1.75 * inch, 1.9 * inch, W - 5.1 * inch], header=True, zebra=False))
    s.append(Spacer(1, 8))
    s.append(Table([[_view(d, -35, 16, W / 2, 3.3 * inch), _view(d, 0, 90, W / 2, 3.3 * inch, labels=True)]],
                   colWidths=[W / 2, W / 2]))
    s.append(Paragraph("Left: the dome from the side. Right: from above, each panel numbered. Colours are jigs: "
                       "panels of one colour are built on one fixture (page 'Jigs').", SMALL))
    s.append(Spacer(1, 6))
    s.append(Paragraph(
        "Every length and angle in this document was solved by the raw-wedge solver for the inputs above. "
        "Nothing was typed in by hand. The few values the solver cannot derive (saw allowances, wood density) are "
        "on the next page, labelled as what they are.", P))
    s.append(PageBreak())

    # ---- 2. what this is
    s.append(Paragraph("Before you cut", H1))
    s.append(Paragraph(
        "<b>What this is.</b> A cutting and assembly plan for a 2V geodesic hemisphere framed from split-log wedges "
        "by the wedge method in <i>The 40 Hour Cabin</i>. Each round of log is split into "
        f"{cfg.radial_splits} wedges. Each triangular panel is three wedges joined end-to-side in a pinwheel on a flat jig. "
        "Panels meet at seams with a key between them.", P))
    s.append(Spacer(1, 4))
    s.append(Paragraph(
        "<b>What this is not.</b> It is not an engineered structural design. Nothing here checks snow, wind or "
        "earthquake loads, foundations, fasteners or the strength of your wood, and it is not stamped for a permit. "
        "Have a local engineer review any dome people will live in. The weights below are estimates for handling, "
        "not loads.", P))
    s.append(Paragraph("Declared values", H2))
    s.append(Paragraph("The solver derives everything else from these. Each is labelled: a declared allowance is a "
                       "choice you can change, an estimate is a typical value, an assumption is something the model takes as true.", SMALL))
    s.append(_table([["Value", "Set to", "Kind", "Why"]] + [list(r) for r in d.constants()],
                    [1.6 * inch, 1.25 * inch, 1.0 * inch, W - 3.85 * inch]))
    s.append(Paragraph("How to read lengths", H2))
    s.append(Paragraph(
        "Lengths are inches to three decimals, with the nearest sixteenth in brackets. <b>Finished</b> is the stick in "
        "the panel. <b>Raw blank</b> is what you crosscut from the round: finished plus the butt tail plus the head "
        f"overfit ({inches(d.allowance_in)} in all). Angles are measured from a square cut.", P))
    s.append(PageBreak())

    # ---- 3. saw setups
    s.append(Paragraph("Saw setups for the butt cut", H1))
    s.append(Paragraph(
        "The butt end of every member is cut <b>before</b> assembly, on the saw bench, in batches. The head end is not "
        "measured at all: it is sawn in place on the jig (page 'Jig procedure'). These are every butt cut in the dome.", P))
    s.append(Spacer(1, 4))
    bevel = abs(float(d.setups[0]["bevel_deg"]))
    half_note = ", half the wedge's sector angle" if math.isclose(bevel, 180 / cfg.radial_splits, abs_tol=1e-3) else ""
    rows = [["Setup", "Mitre", "Bevel", "Members", "Edge types", "Point runs long by", "Families"]]
    if req.mixed:
        rows[0][2] = "Bevel (tilt)"
    for st in d.setups:
        fams = ", ".join(f.name for f in d.families if f.butt_setup == st["name"])
        tilt = "" if not req.mixed else (" (in)" if float(st["bevel_deg"]) > 0 else " (out)")
        rows.append([_b(st["name"]), deg(abs(float(st["mitre_deg"]))), deg(abs(float(st["bevel_deg"]))) + tilt, st["count"], st["edge_types"],
                     inches(float(st["run_max"])), fams])
    s.append(_table(rows, [0.55 * inch, 0.7 * inch, 0.65 * inch, 0.7 * inch, 0.8 * inch, 1.45 * inch, W - 4.85 * inch]))
    s.append(Spacer(1, 6))
    s.append(Paragraph(
        f"The bevel is the same on every setup, {deg(bevel)}{half_note}. It comes from how the log was split and which way "
        "the wedge is turned, not where the member sits, so set it once for the whole dome. Only the mitre changes, "
        "and it takes just the values above: set a fence stop for each one. Both angles are measured from a square cut "
        "in the stick's own frame: the mitre in the plane of the panel, the bevel out of it. Hold the wedge in a cradle "
        "matching its orientation on the jig. The cut runs a long way down the stick because the face it lands on leans "
        "away, which is why the blank runs long on the point side.", P))
    if req.mixed:
        s.append(Spacer(1, 4))
        s.append(Paragraph(
            "<b>In and out panels.</b> A wedge for an out-pointing panel takes the same bevel tilted the other way: it is "
            "the same cut with the wedge turned over in the cradle. The setups marked (out) are those. Keep the in and out "
            "sticks of a family in separate stacks, marked IN and OUT.", P))
    s.append(PageBreak())

    if req.mixed:
        s += _pattern_page(d)

    # ---- 4. cut families
    s.append(Paragraph("Cut families", H1))
    s.append(Paragraph(
        f"The {len(d.model.members)} members fall into {len(d.families)} families. Every member of a family takes the same "
        "two cuts, so cut each family as one batch and mark every stick with its family name.", P))
    s.append(Spacer(1, 4))
    rows = [["Family", "Count", "Nominal edge", "Finished", "Raw blank", "Butt setup", "Head cut (yaw / pitch)"]]
    for f in d.families:
        rows.append([_b(f.name), f.count, f"{f.nominal_in:.3f}\"", inches(f.finished_in), inches(f.raw_blank_in),
                     f.butt_setup, f"{deg(abs(f.head_yaw_deg))} / {deg(abs(f.head_pitch_deg))}"])
    rows.append([_b("Total"), sum(f.count for f in d.families), "", f"{total_finished:,.1f} ft", f"{total_raw:,.1f} ft", "", ""])
    s.append(_table(rows, [0.55 * inch, 0.5 * inch, 0.85 * inch, 1.35 * inch, 1.35 * inch, 0.7 * inch, W - 5.3 * inch]))
    s.append(Spacer(1, 6))
    s.append(Paragraph(
        "The head cut is listed so you can check it. You do not set it on a saw: the head is cut flush against the jig's "
        "head fence after the panel's pinwheel is closed, so its angle comes from the fixture.", SMALL))
    s.append(PageBreak())

    # ---- 5. the log plan
    s.append(Paragraph("The log plan", H1))
    s.append(Paragraph(
        f"Crosscut each log into rounds, split each round into {cfg.radial_splits} wedges, then cut each wedge to its "
        f"family's raw blank. The longest blanks go together, so each round is only as long as its longest wedge. "
        f"You need <b>{len(d.logs)} logs</b> of {req.log_ft:g} ft at {req.log_in:g} in (small end), giving "
        f"{len(d.rounds)} rounds and {sum(r.spare for r in d.rounds)} spare wedges.", P))
    s.append(Spacer(1, 6))
    s.append(_logs_drawing(d, W))
    s.append(Spacer(1, 6))
    rows = [["Round", "From log", "Crosscut length", "Its wedges become", "Spare", "Green weight (est.)"]]
    for r in d.rounds:
        rows.append([_b(f"R{r.number}"), r.log, inches(r.length_in), ", ".join(f"{n} x {k}" for k, n in r.wedges.items()),
                     r.spare, f"{r.green_lb:,.0f} lb"])
    s.append(_table(rows, [0.55 * inch, 0.65 * inch, 1.45 * inch, W - 4.35 * inch, 0.5 * inch, 1.2 * inch]))
    offcut = [req.log_ft * 12 - sum(r.length_in + 0.125 for r in log) for log in d.logs]
    s.append(Spacer(1, 4))
    s.append(Paragraph(
        f"Left over at the end of the logs: {', '.join(f'log {i + 1}: {feet(o)}' for i, o in enumerate(offcut))}. "
        "Heaviest round about " f"{max(r.green_lb for r in d.rounds):,.0f} lb green: plan how you will lift it.", SMALL))
    s.append(PageBreak())

    # ---- 6. jigs
    s.append(Paragraph("Jigs", H1))
    s.append(Paragraph(
        f"The {len(topo.faces)} panels need only {len(d.variants)} different jigs. A panel is built on a jig when its three "
        "members are the same three recipes in the same pinwheel order (turning the panel round is allowed; mirroring it is not).", P))
    rows = [["Jig", "Colour", "Panels", "Members (families)", "Panel numbers"]]
    for v, panels in enumerate(d.variants):
        ms = sorted([m for m in d.model.members if m.face_index == panels[0]], key=lambda m: m.local_edge_index)
        swatch = Table([[""]], colWidths=[14], rowHeights=[10], style=[("BACKGROUND", (0, 0), (-1, -1), colors.HexColor(VARIANT[v % len(VARIANT)]))])
        rows.append([_b(f"J{v + 1}"), swatch, len(panels), ", ".join(d.family_of[m.member_id] for m in ms),
                     ", ".join(str(p + 1) for p in panels)])
    s.append(_table(rows, [0.45 * inch, 0.55 * inch, 0.55 * inch, 1.4 * inch, W - 2.95 * inch]))
    s.append(Spacer(1, 6))
    s.append(_view(d, 0, 90, W, 4.0 * inch, labels=True))
    s.append(PageBreak())
    for v, panels in enumerate(d.variants):
        p0 = panels[0]
        s.append(Paragraph(f"Jig J{v + 1}: {topo.faces[p0].face_type} panel, {len(panels)} panels", H1))
        s.append(Paragraph(f"Drawn for panel {p0 + 1}, seen from outside the dome. Lay the triangle out on the bench once from "
                           f"its three corners and build every J{v + 1} panel on it.", P))
        s += _jig(d, p0, W)
        ms = sorted([m for m in d.model.members if m.face_index == p0], key=lambda m: m.local_edge_index)
        rows = [["Order", "Member", "Family", "Finished", "Butts into", "Receives"]]
        for k, m in enumerate(ms, start=1):
            rows.append([k, m.member_id, d.family_of[m.member_id], inches(m.physical_stock_length_in), m.butt_into_member_id, m.receives_member_id])
        s.append(_table(rows, [0.5 * inch, 1.1 * inch, 0.6 * inch, 1.5 * inch, 1.4 * inch, W - 5.1 * inch]))
        s.append(PageBreak())

    # ---- 7. seams
    s.append(Paragraph("Seams", H1))
    s.append(Paragraph(
        f"Panels meet at {sum(x['count'] for x in d.seams)} seams of {len(d.seams)} kinds. The fold angle is how far the "
        "shell turns at the seam. The gap is the angle left between the two wedges' raw faces, which the key fills.", P))
    rows = [["Seam", "Count", "Length", "Fold", "Included angle", "Raw-face gap", "Key" + (" (outer / inner)" if req.seam_join == "raw_trapezoid" else "")]]
    for x in d.seams:
        key = (f"{inches(x['key_outer_in'])} / {inches(x['key_inner_in'])}" if req.seam_join == "raw_trapezoid"
               else f"{inches(cfg.flat_key_width_in)} x {inches(min(cfg.flat_key_depth_in, req.log_in * 0.75))}")
        rows.append([_b(x["edge_type"]), x["count"], inches(x["length_in"]), deg(x["fold_deg"]), deg(x["dihedral_deg"]), deg(x["gap_deg"]), key])
    s.append(_table(rows, [0.5 * inch, 0.5 * inch, 1.3 * inch, 0.6 * inch, 0.95 * inch, 0.9 * inch, W - 4.75 * inch]))
    s.append(Spacer(1, 6))
    s.append(Paragraph(SEAM_JOINS[req.seam_join] + ". " + (
        "The raw sawn faces stay as split; a trapezoid key, its point truncated, fills the gap along the seam."
        if req.seam_join == "raw_trapezoid" else
        "Both seam faces are shaved parallel to the seam's bisector and a rectangular key goes between them."), P))
    s.append(PageBreak())

    # ---- 8. jig procedure
    s.append(Paragraph("Jig procedure", H1))
    s.append(Paragraph("The same twelve steps for every panel. Two phases: butts off the jig in batches, then heads on the jig, in place.", P))
    for slug, head, looking, enforcing in d.sim.JIG_STAGES:
        s.append(KeepTogether([Paragraph(head.title(), H2), Paragraph(looking, P), Paragraph("<i>What it does:</i> " + enforcing, SMALL)]))
    s.append(PageBreak())

    # ---- 9. infill
    f = d.infill
    s.append(Paragraph("Infill takeoff", H1))
    s.append(Paragraph(
        "If you fill the panels with paired wedges (the infill method), this is the wood it takes. <b>This is a planning "
        "model, not a measured result.</b> It assumes each pair of wedges covers a continuous strip of the face, at "
        "an overlap you choose. Until you measure your own installed coverage, read the whole table as a range.", P))
    s.append(_table([
        ["Panel area (gross)", f"{f['area_sqft']:,.0f} sq ft"],
        ["Opening inside the frame (assumed inset)", f"{f['opening_sqft']:,.0f} sq ft"],
        ["Wedge chord at your log", inches(f["chord_in"])],
        ["Frame members / gross frame stock", f"{f['members']} / {f['gross_frame_ft']:,.0f} ft"],
    ], [3.2 * inch, W - 3.2 * inch], header=False))
    s.append(Spacer(1, 6))
    rows = [["Assumed overlap", "Pair pitch", "Infill wedge ft", "Log ft (frame + infill)", f"Logs of {req.log_ft:g} ft"]]
    for r in f["rows"]:
        rows.append([f"{100 * r['overlap']:.0f}%", f"{r['pair_pitch_in']:.2f} in", f"{r['infill_ft']:,.0f}", f"{r['raw_trunk_ft']:,.0f}",
                     f"{r['whole_tree_equivalents']}"])
    s.append(_table(rows, [1.2 * inch, 1.0 * inch, 1.3 * inch, 1.8 * inch, W - 5.3 * inch]))
    s.append(Spacer(1, 4))
    s.append(Paragraph("No allowance here for kerf, taper, defects, seals or offcuts. The frame figure in this table uses "
                       "the ledger's gross blanks and may differ from the log plan, which packs real blanks.", SMALL))
    s.append(PageBreak())

    # ---- 10. every member
    s.append(Paragraph("Every member", H1))
    rows = [["Member", "Panel", "Family", "Finished", "Raw blank", "Butt", "Butts into", "Receives"]]
    for m in d.model.members:
        fam = next(x for x in d.families if x.name == d.family_of[m.member_id])
        rows.append([m.member_id, m.face_index + 1, fam.name, inches(m.physical_stock_length_in), inches(m.physical_stock_length_in + d.allowance_in),
                     fam.butt_setup, m.butt_into_member_id, m.receives_member_id])
    s.append(_table(rows, [0.95 * inch, 0.45 * inch, 0.5 * inch, 1.3 * inch, 1.3 * inch, 0.45 * inch, 0.9 * inch, W - 5.85 * inch], size=7))
    s.append(PageBreak())

    # ---- 11. checks and provenance
    s.append(Paragraph("Self-checks and where these numbers came from", H1))
    s.append(_table([["Check", "Result", "Detail"]] + [[c[0], "pass" if c[1] else "FAIL", c[2]] for c in d.checks],
                    [2.6 * inch, 0.5 * inch, W - 3.1 * inch]))
    s.append(Spacer(1, 8))
    pv = d.provenance
    s.append(_table([["Design id", pv["design"]], ["Made", pv["made"]], ["Solver", pv["solver"]], ["Ledger", pv["ledger"]],
                     ["Repository commit", pv["commit"]]], [1.5 * inch, W - 1.5 * inch], header=False))
    s.append(Spacer(1, 8))
    s.append(Paragraph(
        "The solver and the ledger are open source in the DomeSimulator repository. Anyone can re-run this design from "
        "its inputs and get the same numbers. The design id is a hash of the inputs, so the same request always gives the same id.", SMALL))

    doc.build(s, onFirstPage=chrome, onLaterPages=chrome)
    return path
