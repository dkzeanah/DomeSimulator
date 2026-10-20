"""The plan set: every sheet a builder needs, drawn from the model.

``build_plans(spec)`` writes a new numbered PDF in ``deliverables/`` (never over an old
one) and returns its path. The sheets follow the order of the work -- what it is, what to
buy, every panel and stick, then the method step by step on the bench and on the site, the
door, the room it makes -- and end with the declared inputs and the self-checks, so every
figure in the set can be traced.

The method (framed panels built flat on a plywood jig, sticks ripped on their bevel,
pinwheel corners, initial and compound final mitres, sections skinned in the shop) is the
one Trillium Domes teaches, credited on the first and last sheets. The drawings, words and
figures here are this repository's own: re-solved from the sphere, not copied from a plan.
"""

from __future__ import annotations

import datetime as dt
import hashlib
import json
import math
import tempfile
from dataclasses import replace
from pathlib import Path

import numpy as np
from PIL import Image
from reportlab.pdfgen import canvas

from . import TAG
from . import draw as Dr
from . import model as M
from . import render as R
from . import shop as SH
from .draw import ACCENT, GREY, INK, PH, PW, X0, X1, Y0, Sheet, both, deg, imp, mm

ROOT = Path(__file__).resolve().parents[1]
CLASS_COLOURS = ["#e3a64b", "#7fb2d6", "#9cc27a", "#d98b8b", "#b49ad6", "#e0cf6a", "#8fd0c4", "#c9a07a"]


# ----------------------------------------------------------------------
# Renders, cached by what they show
# ----------------------------------------------------------------------

class Shots:
    def __init__(self, model: M.Model, folder: Path | None = None):
        self.m = model
        self.dir = folder or Path(tempfile.mkdtemp(prefix="sketch-claude-"))
        self.cams: dict[str, R.Camera] = {}

    def dome_points(self, tags=("frame", "skin", "base", "door", "glass")) -> np.ndarray:
        return np.vstack([p.mesh.verts for p in self.m.pieces if p.tag in tags and len(p.mesh.verts)])

    def shot(self, key: str, cam: R.Camera, style: R.Style, view: R.View | None = None, extra=None, model=None) -> Image.Image:
        self.cams[key] = cam
        f = self.dir / f"{key}.png"
        if f.exists():
            return Image.open(f)
        img = R.render(model or self.m, cam, style, view, extra=extra)
        img.save(f)
        return img

    def scene(self, key: str, pieces: list[M.Piece], direction, style=R.SKETCH, size=(1400, 900), fov=30.0, frame_tags=None,
              view=None, target=None, margin=1.1, ortho=False) -> Image.Image:
        sc = M.Model(self.m.spec, pieces, {}, {})
        pts = np.vstack([p.mesh.verts for p in pieces if (frame_tags is None or p.tag in frame_tags) and p.tag != "site" and len(p.mesh.verts)])
        cam = R.framed(pts, direction, fov=fov, width=size[0], height=size[1], margin=margin, target=target, ortho=ortho)
        return self.shot(key, cam, style, view, model=sc)


def _hero_lights(m: M.Model, strength: float = 1.0):
    lm = m.landmarks
    return [((0.0, -0.05, 1.85), (1.0, 0.72, 0.42), 5.0 * strength),
            ((0.0, 0.42 * m.spec.diameter_m / 2, 0.45), (1.0, 0.45, 0.15), 2.5 * strength),
            ((0.0, lm["door"][1] - 0.35, 2.05), (1.0, 0.78, 0.5), 2.2 * strength)]


# ----------------------------------------------------------------------
# The plan set
# ----------------------------------------------------------------------

class PlanSet:
    def __init__(self, model: M.Model, path: Path, shots: Shots | None = None):
        self.m = model
        self.t = model.tables
        self.path = path
        self.c = canvas.Canvas(str(path), pagesize=(PW, PH))
        self.c.setTitle(f"Dome Sketch plans: {model.spec.title} ({TAG})")
        self.c.setAuthor(f"Dome Sketch ({TAG})")
        self.c.setSubject("Construction plans for a framed-panel geodesic dome")
        self.n = 0
        self.date = dt.date.today().isoformat()
        self.shots = shots or Shots(model)
        self.project = f"{model.spec.frequency}V {model.spec.cut} DOME · {model.spec.diameter_m:.2f} m"
        self.contents: list[tuple[int, str]] = []

    def sheet(self, title: str, subtitle: str = "") -> Sheet:
        if self.n:
            self.c.showPage()
        self.n += 1
        self.contents.append((self.n, title))
        return Sheet(self.c, self.n, title, self.project, TAG, self.date, subtitle)

    def save(self):
        self.c.showPage()
        self.c.save()

    # -- shared views --
    def hero(self, style=R.GOLDEN, size=(1800, 1100), key="hero", direction=(-0.55, 1.0, -0.30), door=65, fov=30, extra_lights=True):
        st = replace(style, lights=_hero_lights(self.m, 0.6 if style.name != "night" else 1.6)) if extra_lights else style
        pts = self.shots.dome_points(("frame", "skin", "base", "door", "glass", "deck", "person"))
        cam = R.framed(pts, direction, fov=fov, width=size[0], height=size[1], margin=1.05)
        return self.shots.shot(key, cam, st, R.View(door_open=door)), cam

    def cls_colour(self, name: str) -> str:
        names = [c["name"] for c in self.t["classes"]]
        return CLASS_COLOURS[names.index(name) % len(CLASS_COLOURS)] if name in names else "#cfcfcf"


def build_plans(spec: M.Spec | None = None, out: Path | None = None, shots_dir: Path | None = None) -> Path:
    spec = spec or M.Spec()
    m = M.build(spec)
    if out is None:
        import medialib
        out = medialib.new_path(f"{TAG}-plans.pdf")
    out.parent.mkdir(parents=True, exist_ok=True)
    ps = PlanSet(m, out, Shots(m, shots_dir))
    for fn in SHEETS:
        fn(ps)
    ps.save()
    return out


# ----------------------------------------------------------------------
# Sheets
# ----------------------------------------------------------------------

def s_cover(ps: PlanSet):
    t, sp = ps.t, ps.m.spec
    s = ps.sheet("Dome Sketch Plans", f"{sp.frequency}V {sp.cut} framed-panel geodesic dome · {both(sp.diameter_m)} across")
    img, cam = ps.hero(size=(1900, 1150))
    pl = s.image(img, X0, Y0 + 70, X1 - X0, s.top - Y0 - 76)
    figs = [("Across the base", both(t["diameter_m"])), ("Height to the top", both(t["height_m"])),
            ("Floor area", f"{t['floor_m2']:.1f} m² ({t['floor_m2'] * 10.7639:.0f} ft²)"),
            ("Panels", f"{t['whole']} whole + {t['partial']} partial"),
            ("Sticks", f"{t['stick_count']} in {len(t['sticks'])} cuts"),
            ("Sheets of plywood", f"{t['sheets']}")]
    w = (X1 - X0) / len(figs)
    for i, (k, v) in enumerate(figs):
        x = X0 + i * w
        s.box(x + 2, Y0, w - 4, 58)
        s.text(k.upper(), x + w / 2, Y0 + 44, 6.4, "Sans-B", GREY, anchor="c")
        s.text(v, x + w / 2, Y0 + 26, 9.5, "Sans-B", anchor="c")
    s.text(f"{TAG} · drawn {ps.date}", X1, Y0 + 64, 6.5, color=GREY, anchor="r")


def s_welcome(ps: PlanSet):
    t, sp = ps.t, ps.m.spec
    s = ps.sheet("Before You Start", "what these plans are, and how to read them")
    colw = (X1 - X0 - 24) / 2
    y = s.top - 6
    h = s.para(f"""
<b>A cabin you build at a bench.</b> This dome is made of {t['panels']} flat triangular panels. Each panel is a frame of
three sawn sticks, built on a plywood jig in the shop, skinned there, and only then carried to the site and screwed to
its neighbours. Nothing in the frame is a hub or a bracket: the sticks' own bevels make the curve.

The plans run in the order of the work: what you are building and what to buy; every panel, stick and angle; the method
on the bench, one step a sheet; the base, the deck and the raising; the door; and the room it makes.

<b>Where the numbers come from.</b> Every length and angle on these sheets is computed by <font name="Mono">sketch_claude.model</font>
from the solved {sp.frequency}V sphere, the cut, and the stock sizes. The few inputs geometry cannot supply -- stock,
door size, screw spacing -- are listed with their reasons on the last sheet. Change the dome's size in the Dome Sketch app and
every sheet is redrawn to match.

<b>The method.</b> Building a dome as framed panels on a jig, with each stick ripped on its bevel and the corners
pinwheeled, is the method taught by <b>Trillium Domes</b> (trilliumdomes.com), whose plan sets showed the way. These sheets
re-solve that method from first principles for this dome; the drawings, words and figures are this project's own.
""", X0, y, colw, 8.6)
    x2 = X0 + colw + 24
    s.heading("Reading the sheets", x2, y)
    s.para("""
<b>Mitre</b> is measured off square: 0° is a square cut, and it is the number you set on a mitre saw's scale.
<b>Bevel</b> is the blade's tilt off vertical, also off square.

<b>Long point</b> is the far tip of an angled cut; a stick's length is long point to long point unless a sheet says otherwise.

<b>Outer face</b> is the face of a stick on the outside of the dome. On the jig it lies face down, so you look at the
<b>inner face</b> while you work, and the drawings of the jig show the panel as you will see it: from the inside.

<b>Pinwheel.</b> At every corner one stick runs through to the corner (its <b>head</b>) and the next stops against
its inside edge (its <b>tail</b>). The tail is a plain mitre; the head is a compound mitre-and-bevel.

Lengths are given in millimetres with feet and inches to the nearest 1/16 in. Cut to the millimetre figure when you can.
""", x2, y - 16, colw, 8.4)
    pts = ps.shots.dome_points(("frame", "base", "door"))
    cam = R.framed(pts, (-0.6, 1.0, -0.35), fov=28, width=1000, height=640)
    img = ps.shots.shot("welcome-frame", cam, R.MONO, R.View(tags=("frame", "base", "door", "deck")))
    s.image(img, x2, Y0, colw, 210)


def s_glance(ps: PlanSet):
    t, sp = ps.t, ps.m.spec
    s = ps.sheet("The Dome at a Glance", "front elevation, side elevation and plan")
    pts = ps.shots.dome_points(("frame", "skin", "base", "door", "glass"))
    view = R.View(tags=("frame", "skin", "base", "door", "glass", "deck"), hide={"porch"})
    w = (X1 - X0 - 20) / 2
    hgt = s.top - Y0 - 14
    for i, (name, d) in enumerate((("front", (0, 1, 0)), ("side", (1, 0, 0)))):
        cam = R.framed(pts, d, width=1100, height=1000, ortho=True, margin=1.25)
        img = ps.shots.shot(f"elev-{name}", cam, R.HIDDEN, view)
        pl = s.image(img, X0 + i * (w + 20), Y0 + 150, w, hgt - 150)
        lo, hi = pts.min(axis=0), pts.max(axis=0)
        ax = 0 if name == "front" else 1
        ends = cam.project([[lo[0], lo[1], 0], [hi[0], hi[1], 0]] if name == "front" else [[lo[0], hi[1], 0], [lo[0], lo[1], 0]])
        a, b = (pl.at(*q) for q in ends)
        if a[0] > b[0]:
            a, b = b, a
        yb = pl.y + 6
        s.dim((b[0], yb), (a[0], yb), f"{both(hi[ax] - lo[ax])} widest", off=-0.01, size=6.6)
        top = pl.at(*cam.project([[0, 0, hi[2]]])[0])
        flo = pl.at(*cam.project([[0, 0, 0.0]])[0])
        xr = pl.x + pl.w - 4
        s.line((top[0] + 20, top[1]), (xr + 4, top[1]), 0.3, GREY)
        s.dim((xr, top[1]), (xr, flo[1]), f"{both(hi[2])} deck to top", off=-0.01, size=6.6)
        door = t["door"]
        if door and name == "front":
            q = cam.project([[-door["W"] / 2, door["y_post"], 0.02], [door["W"] / 2, door["y_post"], 0.02], [door["W"] / 2, door["y_post"], door["H"]]])
            q = [pl.at(*x) for x in q]
            s.dim(q[0], q[1], f"{mm(door['W'])}", off=12, size=6.0, color=ACCENT)
            s.dim(q[1], q[2], f"{mm(door['H'])}", off=12, size=6.0, color=ACCENT)
        s.text(f"{name.upper()} ELEVATION", pl.x + pl.w / 2, pl.y - 8, 7.5, "Sans-B", anchor="c")
    # plan
    cam = R.framed(pts, (0, 0, -1), width=900, height=900, ortho=True, up=(0, 1, 0), margin=1.12)
    img = ps.shots.shot("plan-top", cam, R.HIDDEN, view)
    pl = s.image(img, X0, Y0, 140, 140)
    s.text("PLAN", pl.x + pl.w + 6, pl.y + 10, 7.5, "Sans-B")
    s.para(f"""
The base is a {t['base_edges']}-sided ring. On this cut {t['tapered']} of its edges rise from one corner height to the
other by {mm(t['taper_m'])} and {t['level']} are level, so the base sections under them are made in two shapes
(sheet {_sheet_no(ps, 'Base Layout')}). Inside, the floor is {t['floor_m2']:.1f} m² and the frame is
{both(t['inside_height_m'] - t['base_top_m'] + M.D('base_h_m') + M.D('plate_t_m'))} high at the top on the inside.
""", pl.x + pl.w + 6, pl.y + 130, w * 2 - 150, 8.2)


def _sheet_no(ps: PlanSet, name: str) -> str:
    """The number a later sheet will have: the order is fixed, so it is known in advance."""
    for i, fn in enumerate(SHEETS, 1):
        if getattr(fn, "title", "") == name:
            return str(i + _extra_before(ps, fn))
    return "?"


def _extra_before(ps: PlanSet, fn) -> int:
    # the cut list may run to more than one sheet
    rows = len(ps.t["sticks"])
    pages = math.ceil(rows / CUT_ROWS)
    idx = SHEETS.index(fn)
    return pages - 1 if idx > SHEETS.index(s_cutlist) else 0


def s_materials(ps: PlanSet):
    t, sp = ps.t, ps.m.spec
    s = ps.sheet("Tools and Materials", "everything counted from the model")
    tools = ["Table saw (a sharp rip blade)", "Compound mitre saw, dual bevel if you can", "Circular saw or track saw",
             "Drill and impact driver", "Countersink bit", "Tape measure, straightedge and chalk line",
             "Trammel: a stick with a nail and a pencil", "Digital angle gauge", "Four to six quick clamps",
             "Stapler (pneumatic or electric)", "Utility knife and hand saw", "Ladder or a light scaffold"]
    y = s.top - 6
    y -= s.heading("Tools", X0, y)
    for k in tools:
        s.text("•  " + k, X0 + 4, y - 4, 8.2)
        y -= 12.5
    D = M.D
    base_lengths = [b["length_m"] for b in t["base_sections"]]
    base_boards = M._boards_needed(base_lengths + base_lengths, D("board_l_m"), D("kerf_m")) * 2 // 2
    plates = math.ceil(sum(base_lengths) / D("board_l_m") * (1 + D("waste")))
    deck_boards = math.ceil(t["deck_m2"] / D("deck_board_m") / D("deck_board_l_m") * (1 + D("waste")))
    porch = (D("porch_w_m") * D("deck_front_m")) if sp.porch else 0.0
    porch_boards = math.ceil(porch / D("deck_board_m") / D("deck_board_l_m") * (1 + D("waste")))
    door = t["door"]
    rows = [
        ("2x3 studs, 8 ft (each ripped into two sticks)", f"{t['boards']}", f"{t['stick_count']} sticks, {t['stick_m']:.0f} m of stick"),
        ("1/2 in plywood, 4x8 sheets, for the skin", f"{t['sheets']}", f"{t['skin_m2']:.1f} m² of panel, nested on sheet {_sheet_no(ps, 'Sheet Layout')}"),
        ("Window glazing, 1/4 in polycarbonate", f"{t['glass_m2']:.1f} m²", f"{t['windows']} windows, {t['skylights']} skylight panels"),
        ("2x6, 8 ft, base boards", f"{math.ceil(sum(base_lengths) / D('board_l_m') * (1 + D('waste')))}", f"{len(base_lengths)} sections, {sum(base_lengths):.1f} m"),
        ("Pressure-treated 2x4, 8 ft, bottom plates", f"{plates}", f"{sum(base_lengths):.1f} m"),
        ("2x4, 8 ft, door posts and head", "3" if door else "0", (f"posts {mm(door['H'])}, head {mm(2 * door['X'])}" if door else "")),
        ("3/4 in plywood, door cards", "1" if door else "0", "two cards from one sheet"),
        ("2x8 joists and rim, deck framing", f"{2 * t['base_edges']}", f"one joist to each base corner, one rim board each side"),
        ("5/4x6 decking, 12 ft", f"{deck_boards + porch_boards}", f"floor {t['deck_m2']:.1f} m²" + (f", porch {porch:.1f} m²" if porch else "")),
        ("75 mm (3 in) screws, panel corners", f"{t['screws_corner']}", f"{t['corners']} corners x {int(D('screws_per_corner'))}"),
        ("75 mm (3 in) screws, panel to panel", f"{t['screws_seam']}", f"{t['seam_m']:.0f} m of seam, both sides every {mm(D('seam_screw_m'))}"),
        ("Staples", f"{t['staples']}", f"every {mm(D('staple_m'))} round each skinned panel"),
        ("Seam tape", f"{t['tape_m']:.0f} m", f"{t['seam_m']:.0f} m of seam plus {D('waste') * 100:.0f}%"),
        ("Shingles or cladding", f"{t['skin_m2'] * (1 + D('waste')):.1f} m²", "over the plywood skin"),
        ("Piers", f"{t['base_edges'] // 3 + 1 + (4 if sp.porch else 0)}", "under every third corner, the centre and the porch"),
    ]
    x = X0 + 210
    y = s.top - 6
    y -= s.heading("Materials", x, y)
    s.table(x, y - 2, [("Item", 205, "l"), ("Qty", 52, "r"), ("Counted from", X1 - x - 257, "l")], rows, 7.4)
    s.para(f"""Quantities for screws, staples and sheet goods use the spacings and the {D('waste') * 100:.0f}% allowance declared on
sheet {_sheet_no(ps, 'Declared Inputs and Checks')}; lumber is counted by laying every cut length out on a stock board
(first fit, longest first, a kerf between cuts).""", x, Y0 + 40, X1 - x, 7.6, color=GREY)


def s_exploded(ps: PlanSet):
    t = ps.t
    s = ps.sheet("Exploded View", "what goes where, and how many of each")
    pts = ps.shots.dome_points(("frame", "base", "door"))
    view = R.View(tags=("frame", "base", "door"), explode=1.1)
    ex = np.vstack([p.mesh.verts + np.asarray(p.explode) * 1.1 for p in ps.m.pieces if p.tag in ("frame", "base", "door") and len(p.mesh.verts)])
    cam = R.framed(ex, (-0.55, 1.0, -0.45), fov=28, width=1500, height=1150, margin=1.04)
    img = ps.shots.shot("exploded", cam, R.SKETCH, view)
    pl = s.image(img, X0 + 120, Y0, X1 - X0 - 240, s.top - Y0)
    m = ps.m
    def at(pid):
        p = next(q for q in m.pieces if q.id == pid)
        return p.mesh.centre + np.asarray(p.explode) * 1.1
    items = []
    pent = next(p for p in m.pieces if p.tag == "frame" and p.info["cls"] == "A")
    hexa = next(p for p in m.pieces if p.tag == "frame" and p.info["cls"] == "B" and p.mesh.centre[2] > 1.5 and p.mesh.centre[0] < 0)
    part = next((p for p in m.pieces if p.tag == "frame" and p.info["cls"] == "partial"), None)
    items.append((at(pent.id), f"Pentagon panels (A)\n{next(c['count'] for c in t['classes'] if c['name'] == 'A')}"))
    items.append((at(hexa.id), f"Hexagon panels (B)\n{next(c['built'] for c in t['classes'] if c['name'] == 'B')} whole"))
    if part:
        items.append((at(part.id), f"Partial panels\n{t['partial']} round the door"))
    base = [p for p in m.pieces if p.tag == "base" and p.id.endswith("board")]
    tap = next(p for p in base if p.info["tapered"])
    lev = next((p for p in base if not p.info["tapered"]), None)
    items.append((at(tap.id), f"Tapered base sections\n{sum(1 for b in base if b.info['tapered'])}"))
    if lev:
        items.append((at(lev.id), f"Level base sections\n{sum(1 for b in base if not b.info['tapered'])}"))
    plate = next(p for p in m.pieces if p.id.endswith("plate"))
    items.append((at(plate.id), "Bottom plates (PT)"))
    if t["door"]:
        items.append((at("door-card-R"), "Door cards (2)"))
        items.append((at("door-post-L"), "Door posts (2)"))
        items.append((at("door-head"), "Door head"))
    s.callouts(pl, cam, items, 7.2)


def s_panel_map(ps: PlanSet):
    t, m = ps.t, ps.m
    s = ps.sheet("Panel Map", "where every panel goes: colour is its class")
    hl = {}
    cls_of = {p.id: p.cls for p in m.panels}
    for p in m.pieces:
        if p.tag in ("skin", "glass") and p.group in cls_of:
            c = cls_of[p.group]
            hl[p.id] = ps.cls_colour(c) if c != "partial" else "#c9c3b8"
    pts = ps.shots.dome_points(("frame",))
    w = (X1 - X0 - 20) / 3
    labels = []
    for i, (name, d, up) in enumerate((("top", (0, 0, -1), (0, 1, 0)), ("front", (0, 1, -0.35), (0, 0, 1)), ("back", (0, -1, -0.35), (0, 0, 1)))):
        cam = R.framed(pts, d, width=900, height=900, ortho=True, up=up, margin=1.08)
        img = ps.shots.shot(f"map-{name}", cam, replace(R.MONO, skin_edges=0.0), R.View(tags=("skin", "glass", "base", "door"), highlight=hl,
                                                                                     hide={q.id for q in m.pieces if q.name.startswith("Window frame")}))
        pl = s.image(img, X0 + i * (w + 10), Y0 + 70, w, s.top - Y0 - 80)
        s.text(name.upper() if name == "top" else f"FROM THE {name.upper()}", pl.x + pl.w / 2, pl.y - 6, 7.5, "Sans-B", anchor="c")
        # panel names at their centres, on the side facing the camera
        dirn = np.asarray(d, float) / np.linalg.norm(d)
        for p in m.panels:
            c = np.mean(p.poly, axis=0)
            if np.dot(p.normal, dirn) < -0.25:
                x, y = pl.at(*cam.project([c])[0])
                tag = p.cls if not p.partial else "P"
                mark = (" W" if p.window else "") + (" S" if p.skylight else "") + (" F" if p.pipe else "")
                s.text(tag + mark, x, y, 5.2, "Sans-B", anchor="c")
    x = X0
    for c in t["classes"]:
        s.c.setFillColorRGB(*R.hex_rgb(ps.cls_colour(c["name"])))
        s.c.rect(x, Y0 + 30, 14, 14, stroke=0, fill=1)
        s.text(f"{c['name']}: {c['kind']} panel, {c['built']} built" + (f" (+{c['count'] - c['built']} cut for the door)" if c['count'] != c['built'] else ""), x + 18, Y0 + 37, 7.6)
        x += 230
    s.c.setFillColorRGB(*R.hex_rgb("#c9c3b8"))
    s.c.rect(x, Y0 + 30, 14, 14, stroke=0, fill=1)
    s.text(f"P: partial panel ({t['partial']})", x + 18, Y0 + 37, 7.6)
    s.para(f"W window ({t['windows']}) · S skylight ({t['skylights']}) · F the panel the stove pipe passes through. "
           f"Rings are counted up from the base; there are {t['rings']}.", X0, Y0 + 20, X1 - X0, 7.4, color=GREY)


def _tri_page(pts2d, box):
    """Scale 2-D points (metres) into a page box (x, y, w, h), keeping shape; returns mapper."""
    P = np.asarray(pts2d, float)
    lo, hi = P.min(axis=0), P.max(axis=0)
    x, y, w, h = box
    k = min(w / max(hi[0] - lo[0], 1e-9), h / max(hi[1] - lo[1], 1e-9))
    ox = x + (w - (hi[0] - lo[0]) * k) / 2
    oy = y + (h - (hi[1] - lo[1]) * k) / 2
    return lambda q: (ox + (q[0] - lo[0]) * k, oy + (q[1] - lo[1]) * k), k


def s_panel_dims(ps: PlanSet):
    t = ps.t
    s = ps.sheet("Panel Dimensions", "outlines to the outer face, as scribed on the jig")
    n = len(t["classes"])
    w = (X1 - X0) / n
    for i, c in enumerate(t["classes"]):
        base, left, right = c["sides_m"]
        ax, ay = c["trammel"]
        tri = [(0, 0), (base, 0), (ax, ay)]
        f, k = _tri_page(tri, (X0 + i * w + 40, Y0 + 120, w - 80, s.top - Y0 - 200))
        P = [f(q) for q in tri]
        s.poly(P, 1.2, fill=R.hex_rgb(ps.cls_colour(c["name"])) )
        s.dim(P[1], P[0], f"{c['letters'][0]}  {both(base)}", off=16)
        s.dim(P[2], P[1], f"{c['letters'][2]}  {both(right)}", off=14)
        s.dim(P[0], P[2], f"{c['letters'][1]}  {both(left)}", off=14)
        foot = f((ax, 0))
        s.line(P[2], foot, 0.4, GREY, dash=([3, 2], 0))
        s.dim(foot, P[2], f"height {mm(c['height_m'])}", off=-12, size=6.2, color=GREY)
        cx = sum(p[0] for p in P) / 3
        cy = sum(p[1] for p in P) / 3
        s.text(c["name"], cx, cy + 8, 22, "Sans-B", anchor="c")
        s.text(c["kind"].upper(), cx, cy - 12, 7.5, "Sans-B", anchor="c")
        s.text(f"× {c['count']}", cx, cy - 24, 9, "Sans-B", anchor="c")
        y = Y0 + 96
        s.text(f"Panel {c['name']}: area {c['area_m2']:.3f} m²; chord letters {', '.join(c['letters'])}", X0 + i * w + w / 2, y, 7.6, anchor="c")
        s.text(f"apex {mm(ax)} along the base from its left corner", X0 + i * w + w / 2, y - 12, 7.2, color=GREY, anchor="c")
    s.para("""Chord letters name the dome's distinct edge lengths, shortest first (A, B, C). Every whole panel is one of the
classes on this sheet; the partial panels round the door have their own sheet. Dimensions are to the outer face's outline:
the line the sticks' outer edges sit on.""", X0, Y0 + 52, X1 - X0, 7.8, color=GREY)


def s_angles(ps: PlanSet):
    t, m = ps.t, ps.m
    s = ps.sheet("Panel Angles", "corner angles, the tail mitres they give, and the rip bevel on each side")
    n = len(t["classes"])
    w = (X1 - X0) / n
    for i, c in enumerate(t["classes"]):
        base, left, right = c["sides_m"]
        ax, ay = c["trammel"]
        tri = [(0, 0), (base, 0), (ax, ay)]
        f, k = _tri_page(tri, (X0 + i * w + 50, Y0 + 170, w - 100, s.top - Y0 - 210))
        P = [np.array(f(q)) for q in tri]
        s.poly([tuple(p) for p in P], 1.1, fill=(0.97, 0.95, 0.9))
        A_base, A_left, A_right = c["angles"]       # opposite base, left, right
        # corner at P0 (between base and left) is opposite right; P1 opposite left; P2 opposite base
        corners = [(P[0], P[1], P[2], A_right), (P[1], P[2], P[0], A_left), (P[2], P[0], P[1], A_base)]
        for v, a, b, ang in corners:
            s.angle(v, a - v, b - v, 18, deg(ang), size=7.2, out=12)
        for (a, b), letter, bev in (((P[0], P[1]), c["letters"][0], c["bevels"][0]), ((P[1], P[2]), c["letters"][2], c["bevels"][2]),
                                    ((P[2], P[0]), c["letters"][1], c["bevels"][1])):
            mid = (a + b) / 2
            out = mid - (np.mean(P, axis=0) - mid) * 0.22
            s.text(f"{letter}: rip {deg(bev)}", out[0], out[1], 7.0, "Sans-B", anchor="c")
        s.text(f"PANEL {c['name']}", float(np.mean([p[0] for p in P])), float(np.mean([p[1] for p in P])), 11, "Sans-B", anchor="c")
        rows = [(f"{deg(ang)}", f"{deg(90 - ang)}") for ang in sorted({round(a, 4) for a in c["angles"]}, reverse=True)]
        s.table(X0 + i * w + w / 2 - 90, Y0 + 150, [("Corner angle", 90, "c"), ("Tail mitre (off square)", 90, "c")], rows, 7.4, head_size=6.6)
    lo, hi = t["bevel_lo"], t["bevel_hi"]
    s.para(f"""The rip bevel on a side is half the fold between the two panels that meet there; across this dome it runs from
{deg(lo, 2)} to {deg(hi, 2)}. A shop that sets one bevel for every stick can use their middle, {deg((lo + hi) / 2, 2)}, and lose at most
{deg((hi - lo) / 2, 2)} at any seam; the cut list gives each stick its exact figure. A tail mitre is 90° less the corner's angle;
the head's compound cut is on the cut list.""", X0, Y0 + 52, X1 - X0, 7.8, color=GREY)


def _stick_outline(m: M.Model, piece_id: str):
    """A stick laid on the bench: its outer and inner faces in 2-D, the stick's length along x."""
    p = next(q for q in m.pieces if q.id == piece_id)
    panel = next(q for q in m.panels if q.id == p.info["panel"])
    k = p.info["k"]
    n = len(panel.poly)
    a, b = panel.poly[k], panel.poly[(k + 1) % n]
    e = M.unit(b - a)
    u = M.unit(np.cross(panel.normal, b - a))
    V = p.mesh.verts - a
    xs, ys, zs = V @ e, V @ u, V @ (-panel.normal)
    outer = [(x, y) for x, y, z in zip(xs, ys, zs) if abs(z) < 1e-6]
    inner = [(x, y) for x, y, z in zip(xs, ys, zs) if abs(z - m.spec.stick_d_m) < 1e-6]
    def hull(P):
        P = sorted(set((round(x, 9), round(y, 9)) for x, y in P))
        if len(P) < 3:
            return P
        def cross(o, a, b):
            return (a[0] - o[0]) * (b[1] - o[1]) - (a[1] - o[1]) * (b[0] - o[0])
        lo, up = [], []
        for q in P:
            while len(lo) >= 2 and cross(lo[-2], lo[-1], q) <= 0:
                lo.pop()
            lo.append(q)
        for q in reversed(P):
            while len(up) >= 2 and cross(up[-2], up[-1], q) <= 0:
                up.pop()
            up.append(q)
        return lo[:-1] + up[:-1]
    return hull(outer), hull(inner), p


def _stretch(pts2d, box, k_y: float):
    """Like _tri_page, but drawn ``k_y`` times taller than its scale: a long thin stick made readable."""
    P = np.asarray(pts2d, float)
    lo, hi = P.min(axis=0), P.max(axis=0)
    x, y, w, h = box
    kx = w / max(hi[0] - lo[0], 1e-9)
    ky = min(kx * k_y, h / max(hi[1] - lo[1], 1e-9))
    oy = y + (h - (hi[1] - lo[1]) * ky) / 2
    return lambda q: (x + (q[0] - lo[0]) * kx, oy + (q[1] - lo[1]) * ky)


def s_sections(ps: PlanSet):
    t, sp = ps.t, ps.m.spec
    s = ps.sheet("Member Sections and Bevels", "every stick is the same section; only its rip bevel changes")
    w, d = sp.stick_w_m, sp.stick_d_m
    bevels = sorted({round(r["rip_deg"], 2) for r in t["sticks"]})
    items = [(f"Rip {deg(b, 2)}", b, [r["mark"] for r in t["sticks"] if round(r["rip_deg"], 2) == b]) for b in bevels]
    cols = min(len(items), 5)
    cw = (X1 - X0) / cols
    rows = math.ceil(len(items) / cols)
    ch = min(170, (s.top - Y0 - 120) / max(rows, 1))
    scale = min(cw * 0.42 / w, ch * 0.55 / d)
    for i, (label, b, marks) in enumerate(items):
        cx = X0 + (i % cols) * cw + cw / 2
        cy = s.top - (i // cols) * ch - ch / 2 + 6
        off = d * math.tan(math.radians(b))
        # outer face at the top, the bevelled edge on the right, the square inside edge on the left
        P = [(-w / 2, d / 2), (w / 2, d / 2), (w / 2 - off, -d / 2), (-w / 2, -d / 2)]
        Q = [(cx + x * scale, cy + y * scale) for x, y in P]
        s.poly(Q, 1.0, fill=R.hex_rgb("#efd9b4"))
        s.dim(Q[0], Q[1], mm(w), off=8, size=6.4)
        s.dim(Q[3], Q[0], mm(d), off=8, size=6.4)
        s.text("outer face", cx, Q[0][1] + 20, 5.8, color=GREY, anchor="c")
        s.line(Q[1], (Q[1][0], Q[2][1]), 0.4, GREY, dash=([2, 2], 0))
        s.angle(Q[1], (0, -1), (Q[2][0] - Q[1][0], Q[2][1] - Q[1][1]), 22, deg(b, 2), size=6.8, out=10)
        s.text(label, cx, cy - d / 2 * scale - 14, 8, "Sans-B", anchor="c")
        s.text(", ".join(marks[:10]) + (" ..." if len(marks) > 10 else ""), cx, cy - d / 2 * scale - 25, 6.0, color=GREY, anchor="c")
    s.para(f"""Each stick is half a 2x3: {mm(w)} wide on the jig by {mm(d)} through the wall. The rip that halves the board is the
bevel, so both halves come off the saw with their bevelled edge already cut; the square edge is the board's own. Marks are
the cut-list rows each bevel serves.""", X0, Y0 + 40, X1 - X0, 7.8, color=GREY)


CUT_ROWS = 30


def s_cutlist(ps: PlanSet):
    t = ps.t
    rows = t["sticks"]
    pages = math.ceil(len(rows) / CUT_ROWS)
    cols = [("Mark", 34, "c"), ("Panel", 42, "c"), ("Side", 30, "c"), ("Edge", 36, "c"), ("Qty", 30, "r"),
            ("Long point to long point", 128, "r"), ("Head: mitre / bevel", 92, "c"), ("Tail mitre", 56, "c"), ("Rip bevel", 56, "c"),
            ("Panels", 120, "l")]
    for pg in range(pages):
        s = ps.sheet("Cut List: Panel Sticks" + (f" ({pg + 1} of {pages})" if pages > 1 else ""),
                     "every distinct stick; cut the tail first, then the head")
        chunk = rows[pg * CUT_ROWS:(pg + 1) * CUT_ROWS]
        body = []
        for r in chunk:
            pan = r["panels"]
            body.append((r["mark"], r["cls"] if r["cls"] != "partial" else "P", r["side"] if r["kind"] != "cut" else "cut",
                         r["kind"], r["count"], both(r["long_m"]), f"{deg(r['head_mitre'])} / {deg(r['head_bevel'])}",
                         deg(r["tail_mitre"]), deg(r["rip_deg"], 2), (pan[0] if len(pan) == 1 else f"{len(pan)} panels")))
        s.table(X0, s.top - 4, cols, body, 7.1)
        if pg == pages - 1:
            s.para(f"""{t['stick_count']} sticks in {len(rows)} distinct cuts; {t['boards']} 8 ft 2x3s when every stick (plus
{mm(M.D('trim_m'))} to trim) is laid out on a board ripped in two. <b>Head</b> is the compound cut at the corner the stick runs
through to; <b>tail</b> the plain cut where it stops against the next stick. Cut a test pair on scrap first.""",
                   X0, Y0 + 44, X1 - X0, 7.6, color=GREY)


def s_stick_details(ps: PlanSet):
    t, m = ps.t, ps.m
    s = ps.sheet("Member Lengths and Mitres", "the three sticks of each panel, drawn on the bench as cut")
    whole = [r for r in t["sticks"] if r["cls"] != "partial"]
    seen, picks = set(), []
    for c in t["classes"]:
        for r in sorted([r for r in whole if r["cls"] == c["name"]], key=lambda r: -r["count"]):
            key = (r["cls"], r["side"], r["kind"])
            if key in seen:
                continue
            seen.add(key)
            picks.append(r)
    picks = picks[:8]
    cols = 2
    cw = (X1 - X0 - 20) / cols
    rh = (s.top - Y0 - 30) / math.ceil(len(picks) / cols)
    for i, r in enumerate(picks):
        outer, inner, piece = _stick_outline(m, r["sample"])
        x = X0 + (i % cols) * (cw + 20)
        y = s.top - (i // cols + 1) * rh + 18
        L = max(q[0] for q in outer) - min(q[0] for q in outer)
        f = _stretch(outer + inner, (x + 10, y + 22, cw - 20, rh - 58), 5.0)
        s.poly([f(q) for q in outer], 1.0, fill=R.hex_rgb("#efd9b4"))
        s.poly([f(q) for q in inner], 0.5, color=GREY, dash=([2, 2], 0))
        xs = [q[0] for q in outer]
        a = f((min(xs), min(q[1] for q in outer)))
        b = f((max(xs), min(q[1] for q in outer)))
        s.dim(b, a, f"{r['mark']}  {both(r['long_m'])} long point to long point", off=10, size=6.6)
        s.text(f"head  {deg(r['head_mitre'])} mitre, {deg(r['head_bevel'])} bevel", x + 12, y + rh - 26, 7.2, "Sans-B")
        s.text(f"tail  {deg(r['tail_mitre'])} mitre, square", x + cw - 12, y + rh - 26, 7.2, "Sans-B", anchor="r")
        s.text(f"Panel {r['cls']}, side {r['side']} ({r['kind']}), ×{r['count']}  ·  rip {deg(r['rip_deg'], 2)}",
               x + cw / 2, y + 4, 6.8, color=GREY, anchor="c")
    s.para("Solid: the outer face, which lies on the jig. Dashed: the inner face you see from above. Widths are drawn five times "
           "their scale so the cuts can be seen; lengths are to scale.", X0, Y0 + 12, X1 - X0, 7.2, color=GREY)


# -- the method, step by step --

def _sample_panel(m: M.Model, cls: str) -> M.Panel:
    return next(p for p in m.panels if p.cls == cls and not p.partial and not p.window and not p.skylight)


def _step(ps: PlanSet, n: int, title: str, sub: str) -> Sheet:
    return ps.sheet(f"Step {n}: {title}", sub)


def s_step_rip(ps: PlanSet):
    t, m = ps.t, ps.m
    s = _step(ps, 1, "Finish, then Rip on the Bevel", "the most important angle in the build")
    r = max(t["sticks"], key=lambda r: r["count"])
    pieces = SH.table_saw(r["rip_deg"])
    img = ps.shots.scene("step-rip", pieces, (0.75, 0.95, -0.62), size=(1400, 1000), fov=28)
    cam = ps.shots.cams["step-rip"]
    pl = s.image(img, X0 + 250, Y0, X1 - X0 - 330, s.top - Y0)
    s.callouts(pl, cam, [(np.array([0.0, 0.0, 0.86]), f"blade tilted\n{deg(r['rip_deg'], 2)}"),
                         (np.array([0.3, 0.0, 0.88]), "a 2x3, flat"),
                         (np.array([-0.35, -0.02, 0.9]), "two sticks off\none rip"),
                         (np.array([0.1, 0.06, 0.92]), "fence")], 7.0)
    y = s.top - 6
    h = s.para(f"""
<b>Finish first.</b> Stain or oil the 2x3s while they are whole: the rip face ends up hidden in the seam, so finishing
before ripping is the quickest way to a dome that looks finished inside.

<b>Rip every 2x3 in half</b> with the blade tilted to the stick's rip bevel. The cut runs down the middle of the board's
2-1/2 in face, through its 1-1/2 in thickness, so it leaves two sticks {mm(m.spec.stick_w_m)} wide with the bevel
already on one edge.

<b>The bevel matters more than the width.</b> If a batch of sticks comes out a millimetre narrow, the jig takes it up;
a bevel that is off opens every seam on the dome. Set the blade with a digital angle gauge and check the first cut on scrap.

Bevels on this dome run {deg(t['bevel_lo'], 2)} to {deg(t['bevel_hi'], 2)}. Rip the sticks for each bevel as one batch and
label the batch (sheet {_sheet_no(ps, 'Member Sections and Bevels')}).
""", X0, y, 240, 8.3)
    # inset: the board's end, and the cut through it
    w2, t2 = 2.5 * M.IN, 1.5 * M.IN
    off = t2 * math.tan(math.radians(r["rip_deg"]))
    k = 150 / w2
    ox, oy = X0 + 40, Y0 + 30
    box = [(0, 0), (w2, 0), (w2, t2), (0, t2)]
    s.poly([(ox + x * k, oy + y * k) for x, y in box], 1.0, fill=R.hex_rgb("#efd9b4"))
    s.line((ox + (w2 / 2 - off / 2) * k, oy), (ox + (w2 / 2 + off / 2) * k, oy + t2 * k), 1.2, ACCENT, dash=([4, 2], 0))
    s.dim((ox, oy + t2 * k), (ox + w2 * k, oy + t2 * k), "2-1/2 in", off=8, size=6.4)
    s.dim((ox, oy), (ox, oy + t2 * k), "1-1/2 in", off=8, size=6.4)
    s.text("the board's end: the rip is the bevel", ox + w2 * k / 2, oy - 10, 6.8, color=GREY, anchor="c")


def s_step_jig(ps: PlanSet):
    t, m = ps.t, ps.m
    s = _step(ps, 2, "Draw the Jig with a Trammel", "one jig for each panel class; each is a full-size drawing of the panel")
    n = len(t["classes"])
    w = (X1 - X0 - 250) / n
    for i, c in enumerate(t["classes"]):
        base, left, right = c["sides_m"]
        ax, ay = c["trammel"]
        tri = [(0, 0), (base, 0), (ax, ay)]
        f, k = _tri_page([(-0.08, -0.08), (base + 0.08, ay + 0.1)], (X0 + 250 + i * w + 14, Y0 + 60, w - 28, s.top - Y0 - 90))
        P = [np.array(f(q)) for q in tri]
        sheet = [f((-0.06, -0.07)), f((base + 0.06, -0.07)), f((base + 0.06, ay + 0.07)), f((-0.06, ay + 0.07))]
        s.poly(sheet, 0.6, fill=R.hex_rgb("#efe3c6"), color=GREY)
        s.line(f((-0.05, 0)), f((base + 0.05, 0)), 0.5, GREY, dash=([5, 2], 0))
        for cen, rad, lab in ((P[0], left * k, f"{c['letters'][1]} {mm(left)}"), (P[1], right * k, f"{c['letters'][2]} {mm(right)}")):
            a0 = math.degrees(math.atan2(P[2][1] - cen[1], P[2][0] - cen[0]))
            s.c.setStrokeColorRGB(*ACCENT)
            s.c.setLineWidth(0.6)
            s.c.arc(cen[0] - rad, cen[1] - rad, cen[0] + rad, cen[1] + rad, a0 - 10, 20)
            s.line(cen, P[2], 0.35, ACCENT, dash=([2, 2], 0))
            mid = (cen + P[2]) / 2
            s.text(lab, mid[0] + (-12 if cen is P[0] else 12), mid[1], 6.4, color=ACCENT, anchor="r" if cen is P[0] else "l")
        s.poly([tuple(p) for p in P], 1.1)
        s.dim(P[1], P[0], f"{c['letters'][0]} {both(base)}", off=12, size=6.4)
        for p in P:
            s.c.circle(p[0], p[1], 1.6, stroke=0, fill=1)
        s.text(f"PANEL {c['name']} JIG", (P[0][0] + P[1][0]) / 2, P[2][1] + 22, 8, "Sans-B", anchor="c")
    s.para(f"""
<b>1. The base line.</b> On a sheet of 3/4 in plywood a little bigger than the panel, snap a straight line near one edge and
mark the base's two corners on it, the base length apart.

<b>2. Two arcs.</b> Set a trammel (a stick with a nail at one end and a pencil at the length) to one side's length, put the
nail on one base mark and scratch an arc where the apex will be. Reset it to the other side's length and scratch an arc from
the other mark. Where the arcs cross is the third corner.

<b>3. Check it.</b> Measure all three sides again and the height from base to apex. Then connect the dots: that triangle is
the outer outline of the panel. Nothing you build on this jig should stick out past it.

Trim the plywood to an inch or two outside the line. Panel {t['classes'][0]['name']}'s apex lands {mm(t['classes'][0]['trammel'][0])}
along the base from its left corner{', and the others are on their own jigs' if len(t['classes']) > 1 else ''}.
""", X0, s.top - 6, 236, 8.2)


def s_step_rails(ps: PlanSet):
    t, m = ps.t, ps.m
    s = _step(ps, 3, "Rails and the First Stick", "set each stick on the line and fix a rail behind it")
    p = _sample_panel(m, t["classes"][-1]["name"])
    pieces = SH.bench() + SH.jig(m, p) + SH.panel_on_jig(m, p, "first")
    R_, o = SH.flat(p)
    first = pieces[-1]
    c = first.mesh.centre
    pieces += SH.clamp(c + [0.0, 0.0, 0.0], 15)
    img = ps.shots.scene("step-rails", pieces, (0.45, 0.85, -0.95), size=(1400, 1000), fov=28, frame_tags=("frame", "jig"))
    cam = ps.shots.cams["step-rails"]
    pl = s.image(img, X0 + 250, Y0, X1 - X0 - 330, s.top - Y0)
    rails = [q for q in pieces if q.name == "Rail"]
    ink = next(q for q in pieces if q.name == "Scribed outline")
    s.callouts(pl, cam, [(c, "first stick: bevel out,\nouter face down,\nouter edge on the line"),
                         (rails[1].mesh.centre, "rail, screwed down\nbehind the stick"),
                         (ink.mesh.verts[0], "the scribed outline\n(the panel's outer edge)"),
                         (c + [0.0, 0.0, 0.12], "clamp")], 7.0)
    s.para(f"""
Work one side at a time. Lay a stick on the line with its bevelled edge on the outside and its outer face down, and slide it
until its outer edge just splits the line. Clamp it there.

Butt a straight scrap rail (3/4 x 1-1/2 in is plenty) against the stick's inside edge and screw the rail to the jig. Unclamp the
stick and put it back: it should land on the line again by itself, every time.

Do the same on all three sides. From now on every stick for this panel class is set against these rails, so every panel
comes out the same: the line is the check, and if a stick strays inside or outside it the rail has moved.

The method works for any stick size: as long as the sticks are consistent and the bevel is right, the rails do the rest.
""", X0, s.top - 6, 236, 8.3)


def s_step_tails(ps: PlanSet):
    t, m = ps.t, ps.m
    s = _step(ps, 4, "Initial Mitres: the Tails", "the plain cut where each stick stops against the next")
    p = _sample_panel(m, t["classes"][-1]["name"])
    pieces = SH.bench() + SH.jig(m, p) + SH.panel_on_jig(m, p, "all")
    img = ps.shots.scene("step-tails", pieces, (-0.35, 0.8, -1.0), size=(1300, 1000), fov=26, frame_tags=("frame", "jig"))
    cam = ps.shots.cams["step-tails"]
    pl = s.image(img, X0 + 250, Y0 + 150, (X1 - X0 - 250) * 0.62, s.top - Y0 - 150)
    # the corner detail, drawn from the panel's own geometry
    cls = next(c for c in t["classes"] if c["name"] == p.cls)
    ang = cls["angles"][0]
    ox, oy = X0 + 250 + (X1 - X0 - 250) * 0.66, Y0 + 220
    k = 900
    w = m.spec.stick_w_m
    L = 0.09
    a = math.radians(ang)
    d1 = np.array([1.0, 0.0])
    d2 = np.array([math.cos(a), math.sin(a)])
    v = np.array([ox, oy])
    n1 = np.array([0.0, 1.0])
    m2 = np.array([math.sin(a), -math.cos(a)])        # side 2's inward normal, towards side 1
    L1, L2 = 0.11 * k, 0.11 * k
    t0 = w / math.sin(a) * k
    t1 = w * (1 + math.cos(a)) / math.sin(a) * k
    T0, T1 = v + d2 * t0, v + d2 * t1 + m2 * w * k
    s1 = [v, v + d1 * L1, v + d1 * L1 + n1 * w * k, T0]
    s2 = [T0, v + d2 * (t0 + L2), v + d2 * (t0 + L2) + m2 * w * k, T1]
    s.poly([tuple(q) for q in s1], 0.9, fill=R.hex_rgb("#efd9b4"))
    s.poly([tuple(q) for q in s2], 0.9, fill=R.hex_rgb("#e3c08a"))
    s.angle(tuple(v), d1, d2, 30, f"corner {deg(ang)}", size=6.8, out=14)
    s.angle(tuple(T1), -(T1 - T0), m2 * -1, 14, f"tail {deg(90 - ang)}", size=6.8, out=12, color=INK)
    s.text("runs through (head)", *(v + d1 * L1 * 0.6 - n1 * 9), 6.2, color=GREY, anchor="c")
    s.text("stops (tail)", *(v + d2 * (t0 + L2 * 0.75) + m2 * w * k * 3.2), 6.2, color=GREY, anchor="c")
    s.text("detail: one corner, seen from above", ox + 70, oy - 24, 6.8, color=GREY, anchor="c")
    s.para(f"""
Cut every stick's <b>tail</b> first: the end that butts into the inside edge of the next stick round the panel. It is a
plain mitre with the blade square, {deg(90 - cls['angles'][0])} to {deg(90 - max(cls['angles']))} on this panel,
90° less the corner's angle. Cut it a hair long and trim to fit.

The other end of the stick, its <b>head</b>, is left long for now and hangs past the jig. It is cut in the next step
against the stick it meets, so it ends exactly on the outline.

Stay organised: a panel has its sticks in a ring, each with a head and a tail. Multiply the panels by three for the
sticks you need and label each pile with its cut-list mark.
""", X0, s.top - 6, 236, 8.3)
    s.para("""All three sticks on the jig, tails cut, heads still long. Seen from above you are looking at the panel's inside.""",
           X0 + 250, Y0 + 140, (X1 - X0 - 250) * 0.62, 7.2, color=GREY)


def s_step_heads(ps: PlanSet):
    t, m = ps.t, ps.m
    s = _step(ps, 5, "Final Mitres: the Heads", "a compound cut: mitre and bevel at once, set from the cut list")
    r = max([r for r in t["sticks"] if r["cls"] != "partial"], key=lambda r: r["count"])
    pieces = SH.miter_saw(r["head_mitre"], r["head_bevel"], 0.75, m.spec.stick_w_m, m.spec.stick_d_m)
    img = ps.shots.scene("step-heads", pieces, (0.55, 0.95, -0.75), size=(1300, 950), fov=30, frame_tags=("frame", "shop"), margin=1.0)
    cam = ps.shots.cams["step-heads"]
    pl = s.image(img, X0 + 250, Y0 + 170, X1 - X0 - 330, s.top - Y0 - 170)
    s.callouts(pl, cam, [(np.array([0, -0.02, 0.98]), f"blade: {deg(r['head_mitre'])} mitre,\n{deg(r['head_bevel'])} bevel"),
                         (np.array([-0.4, 0.09, 0.88]), "stick: outer face down,\nsquare edge on the fence"),
                         (np.array([0.2, 0.12, 0.9]), "fence")], 7.0)
    heads = {}
    for x in t["sticks"]:
        if x["cls"] == "partial":
            continue
        key = (round(x["head_mitre"], 1), round(x["head_bevel"], 1))
        heads.setdefault(key, []).append(x["mark"])
    rows = [(deg(a), deg(b), ", ".join(v[:9]) + (" ..." if len(v) > 9 else "")) for (a, b), v in sorted(heads.items())]
    s.table(X0 + 250, Y0 + 160, [("Mitre", 60, "c"), ("Bevel", 60, "c"), ("Cut-list marks", X1 - X0 - 370, "l")], rows[:8], 7.2)
    s.para(f"""
With all three tails cut and the sticks back on their rails, mark the <b>head</b> of each stick where it crosses the next
stick: a pencil line on its top where it meets the corner, and the direction of the cut.

The head has to finish flush with the next stick's bevelled edge, so it is cut at a mitre <i>and</i> a bevel at once.
Set both from the cut list: {len(heads)} settings serve every whole panel on this dome.

Take the stick to the saw, square edge against the fence and outer face down, line the blade up on the mark and cut. Clamp a
stop block at the length for the repeats, and put every fifth stick back on the jig to check the block has not crept.

A hand saw along the next stick works too, slowly; a dual-bevel saw saves flipping the stick for the mirror cuts.
""", X0, s.top - 6, 236, 8.2)


def s_step_assemble(ps: PlanSet):
    t, m = ps.t, ps.m
    s = _step(ps, 6, "Fasten the Panel", "on the jig, corner by corner")
    p = _sample_panel(m, t["classes"][0]["name"])
    pieces = SH.bench() + SH.jig(m, p) + SH.panel_on_jig(m, p, "all")
    for q in [x for x in pieces if x.tag == "frame"]:
        pieces += SH.clamp(q.mesh.centre, 30)
    img = ps.shots.scene("step-assemble", pieces, (0.5, 0.75, -0.9), size=(1300, 1000), fov=28, frame_tags=("frame", "jig"))
    cam = ps.shots.cams["step-assemble"]
    pl = s.image(img, X0 + 250, Y0, X1 - X0 - 330, s.top - Y0)
    sticks = [x for x in pieces if x.tag == "frame"]
    corners = [((x.mesh.verts.max(axis=0) + x.mesh.verts.min(axis=0)) / 2) for x in sticks]
    s.callouts(pl, cam, [(sticks[0].mesh.verts[np.argmax(sticks[0].mesh.verts[:, 0])], f"{int(M.D('screws_per_corner'))} screws through\nevery corner"),
                         (corners[1], "every stick against\nits rail"),
                         (corners[2] + [0, 0, 0.12], "clamps hold it\nwhile you drive")], 7.0)
    s.para(f"""
With every stick cut, put the three back on the jig against their rails and clamp them. Check the outline: every outer edge
should sit on the scribed line all the way round.

Drill and countersink, then drive {int(M.D('screws_per_corner'))} screws through each corner: through the stick that runs
through, into the end of the one that stops. Run a bead of glue in the joint first if the panel will see weather before
it is skinned.

Lift the finished frame off and start the next. A panel takes minutes once the jig and the stop blocks are set; this dome
needs {t['whole']} whole panels in {len(t['classes'])} classes, and every one of them comes off a jig the same.
""", X0, s.top - 6, 236, 8.3)


def s_partials(ps: PlanSet):
    t, m = ps.t, ps.m
    if not t["partials"]:
        return
    s = _step(ps, 7, "Partial Panels round the Door", "the door's planes clip the panels it passes through; each piece is framed on its own")
    parts = [p for p in m.panels if p.partial]
    uniq = []
    for p in parts:
        sides = [round(float(np.linalg.norm(p.poly[(k + 1) % len(p.poly)] - p.poly[k])), 3) for k in range(len(p.poly))]
        key = tuple(sorted(sides))
        hit = next((u for u in uniq if u[0] == key), None)
        if hit:
            hit[2].append(p.id)
        else:
            uniq.append((key, p, [p.id]))
    cols = min(len(uniq), 4)
    rows = math.ceil(len(uniq) / cols)
    cw = (X1 - X0) / cols
    rh = (s.top - Y0 - 50) / rows
    for i, (key, p, ids) in enumerate(uniq):
        R_, o = SH.flat(p)
        P2 = [((q - o) @ R_.T)[:2] for q in p.poly]
        x = X0 + (i % cols) * cw
        y = s.top - (i // cols + 1) * rh
        f, k = _tri_page(P2, (x + 30, y + 40, cw - 60, rh - 70))
        Q = [np.array(f(q)) for q in P2]
        s.poly([tuple(q) for q in Q], 1.0, fill=R.hex_rgb("#e6dfd2"))
        cen = np.mean(Q, axis=0)
        for kk in range(len(Q)):
            a, b = Q[kk], Q[(kk + 1) % len(Q)]
            L = float(np.linalg.norm(p.poly[(kk + 1) % len(p.poly)] - p.poly[kk]))
            # dimension on the outside of the polygon
            mid = (a + b) / 2
            dirn = b - a
            nrm = np.array([-dirn[1], dirn[0]])
            off = 10 if np.dot(nrm, mid - cen) > 0 else -10
            kind = p.sides[kk].kind
            s.dim(a, b, f"{mm(L)}" + (" (cut)" if kind == "cut" else ""), off=off, size=6.0, color=ACCENT if kind == "cut" else INK)
        s.text(" / ".join(ids) + ("" if len(ids) == 1 else ""), cen[0], cen[1], 6.6, "Sans-B", anchor="c")
        s.text(f"×{len(ids)}" + ("  (mirror pairs)" if len(ids) > 1 else ""), cen[0], cen[1] - 10, 6.2, color=GREY, anchor="c")
    s.para(f"""Build these on a jig drawn from these outlines, the same way as the whole panels. Sides marked <b>(cut)</b> are new edges
along the door cards' planes: their sticks are ripped to {_cut_bevels(t)} so they lie flat on the plywood card. The cut list carries every partial-panel stick under mark P. {('Notes: ' + '; '.join(t['warnings'])) if t['warnings'] else ''}""",
           X0, Y0 + 40, X1 - X0, 7.6, color=GREY)


def _cut_bevels(t) -> str:
    b = sorted({round(r["rip_deg"], 2) for r in t["sticks"] if r["kind"] == "cut" and r["rip_deg"] > 0.01})
    return " and ".join(deg(x, 2) for x in b) if b else "the card's angle"


def s_windows(ps: PlanSet):
    t, m = ps.t, ps.m
    s = _step(ps, 8, "Windows and the Skylight", "a window is a panel with glazing in place of skin")
    win = next((p for p in m.panels if p.window), None)
    if win is None:
        return
    c = np.mean(win.poly, axis=0)
    eye_dir = -win.normal + np.array([0.15, 0, -0.1])
    focus = [q for q in m.pieces if q.group == win.id or (q.tag in ("skin", "frame") and np.linalg.norm(q.mesh.centre - c) < 1.4)]
    pts = np.vstack([q.mesh.verts for q in focus])
    cam = R.framed(pts, eye_dir, fov=30, width=1300, height=950, margin=0.95, target=c)
    img = ps.shots.shot("step-window", cam, replace(R.DAY, fog=0.0), R.View(tags=("frame", "skin", "glass", "base", "door", "deck", "furniture")))
    pl = s.image(img, X0 + 250, Y0, X1 - X0 - 330, s.top - Y0)
    s.callouts(pl, cam, [(c + win.normal * 0.02, "glazing on a\npainted sash"),
                         (win.poly[0] + win.normal * 0.02, "hinge along\nthe top seam"),
                         (np.mean([win.poly[1], win.poly[2]], axis=0), "flash this seam\nwith tape after\nthe dome is up")], 7.0)
    s.para(f"""
Build one extra panel frame for each window, from the same jig as the panel it replaces. This dome has
{t['windows']} windows on the ring at eye height, spaced round from the door, and a {t['skylights']}-panel skylight
round the top: {t['glass_m2']:.1f} m² of glazing in all.

Skin the window panel's frame with the glazing instead of plywood, set on a bead of sealant and screwed through oversized
holes so the polycarbonate can move. A window that opens is a second, lighter frame hinged to the panel along its top seam,
held open by a gas strut fixed to a short cross member inside the panel.

Run weather-strip round the sash's face so rain cannot run under it.
""", X0, s.top - 6, 236, 8.3)


def s_sections_step(ps: PlanSet):
    t, m = ps.t, ps.m
    s = _step(ps, 9, "Pre-Assemble Sections", "panels screwed together in the shop into pentagons and hexagons")
    groups = t["section_groups"]
    face_ids = {p.face: p.id for p in m.panels if not p.partial}
    plain = {p.face for p in m.panels if not p.partial and not p.window and not p.skylight}
    pent = next(fs for k, fs in groups if k == "pentagon" and set(fs) <= plain)
    hexa = next(fs for k, fs in groups if k == "hexagon" and set(fs) <= plain)
    w = (X1 - X0 - 250) / 2
    for i, (name, fs) in enumerate((("pentagon", pent), ("hexagon", hexa))):
        ids = {face_ids[f] for f in fs if f in face_ids}
        pieces = [q for q in m.pieces if q.tag == "frame" and q.group in ids]
        cen = np.mean([q.mesh.centre for q in pieces], axis=0)
        nrm = M.unit(cen - np.array(m.landmarks["centre"]))
        img = ps.shots.scene(f"section-{name}", pieces, -nrm + np.array([0.2, 0.1, -0.3]), size=(900, 900), fov=28)
        pl = s.image(img, X0 + 250 + i * w, Y0 + 130, w, s.top - Y0 - 140)
        s.text(f"{name.upper()} SECTION: {len(fs)} panels", pl.x + pl.w / 2, pl.y - 8, 7.6, "Sans-B", anchor="c")
    p_sec, h_sec, single = t["sections_counts"]
    s.para(f"""
Before covering, screw panels together in the shop into sections. A section covers in one piece, so it goes up faster,
seals better, and can be taken off again to repair one part of the dome without stripping the rest.

This dome makes {p_sec} pentagon sections (5 panels round a five-way corner) and {h_sec} hexagon sections (6 round a six-way
corner); the other {single} panels go up one at a time.

Lay the panels of a section out with their bottoms down. In a hexagon the panels are nearly equilateral, so mark each
one's base before you start. Clamp two panels with their bevels meeting, check the faces are flush, and drive the seam
screws {mm(M.D('seam_screw_m'))} apart from both sides alternately.
""", X0, s.top - 6, 236, 8.3)
    # the groups on a plan
    hl = {}
    for gi, (k, fs) in enumerate(groups):
        col = CLASS_COLOURS[gi % len(CLASS_COLOURS)]
        for f in fs:
            pid = face_ids.get(f)
            if pid:
                for q in m.pieces:
                    if q.tag == "frame" and q.group == pid:
                        hl[q.id] = col
    pts = ps.shots.dome_points(("frame",))
    cam = R.framed(pts, (0, 0, -1), width=700, height=700, ortho=True, up=(0, 1, 0))
    img = ps.shots.shot("sections-map", cam, R.MONO, R.View(tags=("frame",), highlight=hl))
    pl = s.image(img, X0 + 250, Y0, 120, 120)
    s.text("sections from above (grey: single panels)", pl.x + pl.w + 6, pl.y + 60, 6.8, color=GREY)


def s_covering(ps: PlanSet):
    t, m = ps.t, ps.m
    s = _step(ps, 10, "Cover the Sections", "skin in the shop, staples on the bevel where the seams will hide them")
    groups = t["section_groups"]
    plain = {p.face for p in m.panels if not p.partial and not p.window and not p.skylight}
    hexa = next(fs for k, fs in groups if k == "hexagon" and set(fs) <= plain)
    face_ids = {p.face: p.id for p in m.panels if not p.partial}
    ids = {face_ids[f] for f in hexa if f in face_ids}
    pieces = [q for q in m.pieces if q.group in ids and q.tag in ("frame", "skin", "glass")]
    cen = np.mean([q.mesh.centre for q in pieces], axis=0)
    nrm = M.unit(cen - np.array(m.landmarks["centre"]))
    img = ps.shots.scene("covering", pieces, -nrm + np.array([0.35, 0.2, -0.2]), style=replace(R.DAY, fog=0, sky="paper", tone="aces"), size=(1000, 900), fov=28)
    cam = ps.shots.cams["covering"]
    pl = s.image(img, X0 + 250, Y0, (X1 - X0 - 250) * 0.6, s.top - Y0)
    skin = next(q for q in pieces if q.tag == "skin")
    s.callouts(pl, cam, [(skin.mesh.centre, "1/2 in plywood,\nthen shingles"), (pieces[0].mesh.centre, "frame inside")], 7.0)
    # staple order diagram
    ox, oy = X0 + 250 + (X1 - X0 - 250) * 0.66, Y0 + 120
    r = 60
    hexpts = [(ox + r * math.cos(math.radians(60 * i + 30)), oy + r * math.sin(math.radians(60 * i + 30))) for i in range(6)]
    s.poly(hexpts, 0.8, fill=(0.97, 0.95, 0.9))
    for i in range(6):
        s.line((ox, oy), hexpts[i], 0.4, GREY)
    order = [0, 3, 1, 4, 2, 5]
    for n, i in enumerate(order, 1):
        a, b = hexpts[i], hexpts[(i + 1) % 6]
        mid = ((a[0] + b[0]) / 2 * 1.12 - ox * 0.12, (a[1] + b[1]) / 2 * 1.12 - oy * 0.12)
        s.c.setFillColorRGB(*INK)
        s.c.circle(mid[0], mid[1], 6, stroke=0, fill=1)
        s.text(str(n), mid[0], mid[1], 6.6, "Sans-B", (1, 1, 1), anchor="c")
    s.text("pull tight and fix in this order", ox, oy - r - 16, 6.8, color=GREY, anchor="c")
    s.para(f"""
<b>Plywood skin (this cabin).</b> Cut each panel's skin from the nested sheets (sheet {_sheet_no(ps, 'Sheet Layout')}), glue
and staple it to the frame's outer face, then shingle the section with courses parallel to its lowest edge. Leave the
shingles short of the seams; the seam is taped and capped once the dome is up.

<b>Film or clear skin (a greenhouse).</b> Stretch the sheet over the whole section and staple it on the bevelled edges, so
the staples are hidden when the sections come together. Tack each side with a few staples first, in the order shown, then
fill in at {mm(M.D('staple_m'))}. Warm film stretches better than cold.

This dome takes {t['skin_m2']:.1f} m² of skin and {t['staples']:,} staples.
""", X0, s.top - 6, 236, 8.2)


def s_base_step(ps: PlanSet):
    t, m = ps.t, ps.m
    s = _step(ps, 11, "Deck and Base Sections", "a level platform, then the ring the first panels stand on")
    pts = ps.shots.dome_points(("base", "deck"))
    pieces_view = R.View(tags=("base", "deck", "site"), hide={p.id for p in m.pieces if p.group == "porch"})
    cam = R.framed(pts, (-0.5, 0.9, -0.6), fov=30, width=1400, height=950, margin=1.0)
    img = ps.shots.shot("step-base", cam, R.SKETCH, pieces_view)
    pl = s.image(img, X0 + 250, Y0, X1 - X0 - 330, s.top - Y0)
    base = [p for p in m.pieces if p.tag == "base" and p.id.endswith("board")]
    tap = next(p for p in base if p.info["tapered"])
    lev = next((p for p in base if not p.info["tapered"]), tap)
    plate = next(p for p in m.pieces if p.id.endswith("plate"))
    joist = next(p for p in m.pieces if p.id.startswith("deck-joist"))
    s.callouts(pl, cam, [(tap.mesh.centre, "tapered base section"), (lev.mesh.centre, "level base section"),
                         (plate.mesh.centre, "PT bottom plate"), (np.array([0, 0, 0.0]), "deck: one joist to\neach base corner")], 7.0)
    s.para(f"""
Build the deck first: piers, a girder ring, {t['base_edges']} joists running out to the base corners and a rim board between
each pair, then decking. Its outline is the base's own {t['base_edges']}-sided ring; check its diagonals before you deck it.

On a {ps.m.spec.cut} cut the base is not level: it zig-zags between two corner heights, {mm(t['taper_m'])} apart. So the
base sections come in two shapes. {sum(1 for b in base if not b.info['tapered'])} are level boards; {sum(1 for b in base if b.info['tapered'])}
taper from low to high (sheet {_sheet_no(ps, 'Base Layout')} gives them all). Each is a board on edge, standing on a
pressure-treated plate, its ends mitred {deg(t['base_mitre'])} so neighbours meet at the corners.

Lay the sections out on the deck, check every corner against the base layout and stake or screw them down. Getting this
first ring right is what makes everything above it go together.
""", X0, s.top - 6, 236, 8.2)


def s_base_layout(ps: PlanSet):
    t, m = ps.t, ps.m
    s = ps.sheet("Base Layout", "the ring of base corners on the deck, and every base section")
    # base corners from the model's panel corners at the lowest level
    lows = {}
    for p in m.panels:
        for q in p.poly:
            if q[2] < m.tables["base_top_m"] + m.tables["taper_m"] + 1e-6 and q[2] > 0:
                lows[(round(q[0], 5), round(q[1], 5))] = q
    pts = sorted(lows.values(), key=lambda q: math.atan2(q[1], q[0]))
    box = (X0 + 10, Y0 + 20, (X1 - X0) * 0.52, s.top - Y0 - 30)
    f, k = _tri_page([(q[0], q[1]) for q in pts] + [(0, 0)], box)
    P = [np.array(f((q[0], q[1]))) for q in pts]
    C = np.array(f((0, 0)))
    s.poly([tuple(p) for p in P], 1.2, fill=(0.97, 0.95, 0.9))
    hi_z = max(q[2] for q in pts)
    for i, (q, p) in enumerate(zip(pts, P)):
        high = abs(q[2] - hi_z) < 1e-6
        s.line(tuple(C), tuple(p), 0.3, GREY, dash=([2, 3], 0))
        s.c.setFillColorRGB(*(ACCENT if high else INK))
        s.c.circle(p[0], p[1], 2.4, stroke=0, fill=1)
        nb = P[(i + 1) % len(P)]
        L = float(np.linalg.norm(np.array(pts[(i + 1) % len(pts)][:2]) - np.array(q[:2])))
        mid = (p + nb) / 2
        out = M.unit(np.r_[mid - C, 0])[:2]
        s.text(f"{mm(L)}", mid[0] + out[0] * 12, mid[1] + out[1] * 12, 6.0, anchor="c")
    rads = sorted({round(float(np.linalg.norm(q[:2])), 4) for q in pts})
    s.text(f"centre", C[0], C[1] - 8, 6.4, color=GREY, anchor="c")
    p0 = next(p for q, p in zip(pts, P) if abs(float(np.linalg.norm(q[:2])) - rads[-1]) < 1e-3)
    s.dim(tuple(C), tuple(p0), f"r {mm(rads[-1])}", off=7, size=6.2)
    if len(rads) > 1:
        p1 = next(p for q, p in zip(pts, P) if abs(float(np.linalg.norm(q[:2])) - rads[0]) < 1e-3)
        s.dim(tuple(C), tuple(p1), f"r {mm(rads[0])}", off=-7, size=6.2, color=GREY)
    s.text("DOOR (no base section)", C[0], min(p[1] for p in P) - 14, 7, "Sans-B", anchor="c")
    s.c.setFillColorRGB(*ACCENT)
    s.c.circle(box[0] + 6, Y0 + 12, 2.4, stroke=0, fill=1)
    s.text("high corners", box[0] + 12, Y0 + 12, 6.6)
    s.c.setFillColorRGB(*INK)
    s.c.circle(box[0] + 76, Y0 + 12, 2.4, stroke=0, fill=1)
    s.text("low corners", box[0] + 82, Y0 + 12, 6.6)
    # the sections table
    bs = t["base_sections"]
    kinds = {}
    for b in bs:
        key = (b["tapered"], round(b["length_m"], 4), round(b["low_m"], 4), round(b["high_m"], 4))
        kinds.setdefault(key, []).append(b["id"])
    rows = [("tapered" if tp else "level", len(ids), mm(L), mm(lo), mm(hi), deg(t["base_mitre"])) for (tp, L, lo, hi), ids in sorted(kinds.items())]
    x = X0 + (X1 - X0) * 0.56
    y = s.top - 6
    y -= s.heading("Base sections", x, y)
    s.table(x, y, [("Shape", 46, "l"), ("Qty", 24, "r"), ("Length", 52, "r"), ("Low end", 48, "r"), ("High end", 48, "r"), ("End mitres", X1 - x - 218, "c")], rows, 7.0)
    # a tapered section drawn
    tb = next((b for b in bs if b["tapered"]), bs[0])
    ox, oy = x + 10, Y0 + 70
    kk = (X1 - x - 40) / tb["length_m"]
    kz = kk
    q = [(ox, oy), (ox + tb["length_m"] * kk, oy), (ox + tb["length_m"] * kk, oy + tb["high_m"] * kz), (ox, oy + tb["low_m"] * kz)]
    s.poly(q, 1.0, fill=R.hex_rgb("#efd9b4"))
    s.dim(q[0], q[1], f"{both(tb['length_m'])}", off=-10, size=6.4)
    s.dim(q[3], q[0], f"{mm(tb['low_m'])}", off=8, size=6.2)
    s.dim(q[1], q[2], f"{mm(tb['high_m'])}", off=8, size=6.2)
    s.text("a tapered base board, outside face", (q[0][0] + q[1][0]) / 2, q[2][1] + 14, 7, "Sans-B", anchor="c")
    s.para(f"""Heights are from the top of the bottom plate. The ring is not a regular polygon: its corners sit on two radii because
the {ps.m.spec.cut} cut passes between two rows of the sphere's vertices, so set out each corner from the centre by its own radius
and check the side lengths.""", x, y - 150, X1 - x, 7.4, color=GREY)


def s_assembly(ps: PlanSet):
    t, m = ps.t, ps.m
    s = _step(ps, 12, "Raise the Dome", "from the ground up, ring by ring")
    stages = [(1, "the base sections on the deck"), (2 + 1, "the first two rings and the door frame"),
              (2 + t["rings"] // 2, "halfway"), (2 + t["rings"], "the last panels round the top")]
    w = (X1 - X0) / 2
    h = (s.top - Y0 - 70) / 2
    pts = ps.shots.dome_points(("frame", "base", "door"))
    cam = R.framed(pts, (-0.6, 1.0, -0.42), fov=30, width=1100, height=720, margin=1.04)
    for i, (step, label) in enumerate(stages):
        img = ps.shots.shot(f"stage-{i}", cam, R.SKETCH, R.View(tags=("frame", "base", "door", "deck", "site"), max_step=step,
                                                                     hide={p.id for p in m.pieces if p.group == "porch"}))
        pl = s.image(img, X0 + (i % 2) * w + 4, Y0 + 66 + (1 - i // 2) * h, w - 8, h - 14)
        s.text(f"{i + 1}.  {label}", pl.x + 4, pl.y + pl.h - 8, 7.8, "Sans-B")
    s.para(f"""Start from the ground and work up and round, the way the plan's rings run. The door frame (posts, head and cards) goes in
with the second ring, so the partial panels have something to land on. Put in only a few screws per seam until the whole dome is
up: the frame is flexible until it is closed, and a little play lets the last panels in. Then drive every seam screw. Do not
raise sections in a wind. A bead of sealant or a strip of gasket between the panels as they go together is the best weather
seal you will get.""", X0, Y0 + 58, X1 - X0, 7.8)


def s_door(ps: PlanSet):
    t, m = ps.t, ps.m
    door = t["door"]
    if not door:
        return
    s = _step(ps, 13, "The Door", "posts, head, plywood cards to the skin, and a framed leaf")
    focus = [q for q in m.pieces if q.group in ("door", "door-leaf")]
    pts = np.vstack([q.mesh.verts for q in focus])
    cam = R.framed(pts, (-0.75, 0.95, -0.25), fov=30, width=1100, height=1100, margin=1.08)
    img = ps.shots.shot("door-frame", cam, R.SKETCH, R.View(tags=("frame", "base", "door", "deck"), ghost={q.id for q in m.pieces if q.tag == "frame"},
                                                                 hide={q.id for q in m.pieces if q.group == "door-leaf"}))
    pl = s.image(img, X0, Y0, 260, s.top - Y0)
    card = next(q for q in m.pieces if q.id == "door-card-R")
    s.callouts(pl, cam, [(card.mesh.centre, "card"), (next(q for q in m.pieces if q.id == "door-post-R").mesh.centre, "post"),
                         (next(q for q in m.pieces if q.id == "door-head").mesh.centre, "head")], 7.0, side="r")
    # the card drawn
    info = door["cards"][1] if 1 in door["cards"] else list(door["cards"].values())[-1]
    yz = info["outline_yz"]
    x = X0 + 330
    f, k = _tri_page([(y, z) for y, z in yz], (x, Y0 + 50, 170, s.top - Y0 - 90))
    Q = [np.array(f((y, z))) for y, z in yz]
    s.poly([tuple(q) for q in Q], 1.0, fill=R.hex_rgb("#e9d3a8"))
    back = max(y for y, _ in yz)
    s.dim(f((back, 0)), f((back, door["Z"])), f"{both(door['Z'])}", off=-12, size=6.4)
    s.dim(f((yz[0][0], 0)), f((back, 0)), f"{mm(info['depth_bottom_m'])}", off=-10, size=6.2)
    s.dim(f((back, door["Z"])), f((yz[-3][0], door["Z"])), f"{mm(info['depth_top_m'])}", off=-10, size=6.2)
    s.text("DOOR CARD (×2, mirrored)", x + 85, s.top - 20, 7.6, "Sans-B", anchor="c")
    s.text("its slanted edge follows the skin", x + 85, s.top - 31, 6.6, color=GREY, anchor="c")
    s.para(f"""
The opening is {both(door['W'])} wide and {both(door['H'])} high. The door was fitted to the dome: the cards are moved out to the
nearest panel corners so no panel is left with a sliver too thin to frame.

<b>Posts</b> are 2x4s, {both(door['H'])} long, standing on the deck inside the cards. The <b>head</b> spans the cards,
{both(2 * door['X'])}, its front ripped to follow the skin.

<b>Cards</b> are 3/4 in plywood fins, one each side, filling from the post back to the dome's skin. Their slanted edge is
where the partial panels' cut sticks land. Cut two from one sheet, one mirrored.

The <b>leaf</b> is {mm(door['leaf_w'])} x {mm(door['leaf_h'])}, built to leave {mm(M.D('door_gap_m'))} all round: 2x stiles and
rails, a panel below the lock rail and a glazed lite above. Hang it on the left post, swinging out so rain is shed off
the threshold.
""", X0 + 520, s.top - 6, X1 - X0 - 520, 8.0)


def s_finish(ps: PlanSet):
    t, m = ps.t, ps.m
    s = _step(ps, 14, "Seams, Stove Pipe and Anchors", "make it weather-tight and hold it down")
    img, cam = ps.hero(style=R.DAY, size=(1300, 950), key="finish-day", direction=(0.6, 1.0, -0.25), door=0)
    pl = s.image(img, X0 + 250, Y0, X1 - X0 - 330, s.top - Y0)
    pipe = next((q for q in m.pieces if q.id == "stove-pipe"), None)
    items = [(np.array(m.landmarks["apex"]), "skylight"), (np.array([0, m.landmarks["door"][1], 1.0]), "door")]
    if pipe is not None:
        items.append((pipe.mesh.verts[pipe.mesh.verts[:, 2].argmax()], "stove pipe through\na flashed panel"))
    s.callouts(pl, cam, items, 7.0)
    s.para(f"""
<b>Seams.</b> Clean and dry the open seams between sections, then tape them: start at the bottom and work up, lapping each
upper strip over the one below so water runs off, never into, a lap. {t['seam_m']:.0f} m of seam needs about {t['tape_m']:.0f} m of
tape. Cap the shingle seams over the tape.

<b>Stove pipe.</b> The pipe leaves through one whole panel near the top, through an insulated thimble and a roof boot
sealed to the skin. Keep the clearances the stove's maker gives.

<b>Anchors.</b> On piers and a deck, fix every base section to the deck framing with structural screws or angle
brackets, and tie the deck to its piers. On gravel or bare ground, drive rebar stakes at 20-30° through the plates and
strap them. A light dome in a wind is a kite until it is anchored.

Then move in.
""", X0, s.top - 6, 236, 8.2)


def s_nest(ps: PlanSet):
    t = ps.t
    s = ps.sheet("Sheet Layout", "panel skins nested on 4x8 sheets of plywood")
    sheets = t["nest"]
    sw, sl = M.D("sheet_w_m"), M.D("sheet_l_m")
    cols = 4
    shown = sheets[: 12]
    rows = math.ceil(len(shown) / cols)
    cw = (X1 - X0) / cols
    rh = (s.top - Y0 - 50) / rows
    k = min((cw - 16) / sl, (rh - 22) / sw)
    for i, sh in enumerate(shown):
        x = X0 + (i % cols) * cw + 8
        y = s.top - (i // cols + 1) * rh + 16
        s.c.setStrokeColorRGB(*GREY)
        s.c.setLineWidth(0.5)
        s.c.setFillColorRGB(0.97, 0.95, 0.9)
        s.c.rect(x, y, sl * k, sw * k, stroke=1, fill=1)
        for name, tri in sh:
            s.poly([(x + px * k, y + py * k) for px, py in tri], 0.5, fill=R.hex_rgb(ps.cls_colour(name)))
            cx = sum(p[0] for p in tri) / 3
            cy = sum(p[1] for p in tri) / 3
            s.text(name, x + cx * k, y + cy * k, 5, "Sans-B", anchor="c")
        s.text(f"sheet {i + 1}: {len(sh)} panels", x, y - 7, 6.4, color=GREY)
    s.para(f"""{len(sheets)} sheets for the {sum(len(x) for x in sheets)} whole skinned panels, laid in rows of alternate points up and
points down with a double kerf between; {t['partial_sheets']} more for the partial panels round the door, cut to their own outlines.
{'Showing the first 12 of ' + str(len(sheets)) + '.' if len(sheets) > 12 else ''}""", X0, Y0 + 30, X1 - X0, 7.6, color=GREY)


def s_floor_plan(ps: PlanSet):
    t, m = ps.t, ps.m
    s = ps.sheet("Living in It", "floor plan cut at 1.2 m, and the room it makes")
    pts = ps.shots.dome_points(("frame", "base", "deck"))
    cam = R.framed(pts, (0, 0, -1), width=1100, height=1100, ortho=True, up=(0, 1, 0), margin=1.05)
    img = ps.shots.shot("floor-plan", cam, replace(R.SKETCH, shadows=False, sun=0.45, ambient=0.7),
                        R.View(tags=("frame", "base", "door", "deck", "furniture", "skin", "glass"), clip=(0, 0, 1, -1.2),
                               hide={q.id for q in m.pieces if q.group == "porch"}))
    pl = s.image(img, X0 + 40, Y0, 330, s.top - Y0)
    labels = {"Bed frame": "bed", "Sofa": "sofa", "Table": "table", "Counter": "kitchen", "Wood stove": "wood stove",
              "Rug": "rug", "Shelf": "shelves"}
    items, seen = [], set()
    for q in m.pieces:
        if q.name in labels and labels[q.name] not in seen:
            seen.add(labels[q.name])
            items.append((q.mesh.centre, labels[q.name]))
    if t["door"]:
        items.append((np.array([0, t["door"]["y_post"], 0.5]), "door"))
    s.callouts(pl, cam, items, 7.0, side="l", pad=6)
    st = replace(R.INTERIOR, lights=_hero_lights(m, 1.0))
    r = m.spec.diameter_m / 2
    door_y = m.landmarks["door"][1]
    cam2 = R.Camera((0.35, door_y + 0.55, 1.45), (-0.55, 0.9, 0.8), 68, 0, (0, 0, 1), 0.05, 60, 1300, 900)
    img2 = ps.shots.shot("interior", cam2, st, R.View(hide_tags=("person",), door_open=60))
    x = pl.x + pl.w + 16
    pl2 = s.image(img2, x, Y0 + 130, X1 - x, s.top - Y0 - 130)
    s.para(f"""One room of {t['floor_m2']:.1f} m² under a frame {mm(t['inside_height_m'] - t['base_top_m'] + M.D('base_h_m') + M.D('plate_t_m'))}
high: a double bed against the back wall, a sofa, a table by the door, a kitchen run and a wood stove on a hearth, its pipe
straight up through one panel. The windows sit at eye height on the ring round from the door, and the skylight lights the
middle of the room from above.""", x, Y0 + 110, X1 - x, 8.0)


def s_gallery(ps: PlanSet):
    m = ps.m
    s = ps.sheet("Showcase", "the finished dome")
    w = (X1 - X0 - 10) / 2
    h = (s.top - Y0 - 10) / 2
    a, _ = ps.hero(style=R.GOLDEN, size=(1300, 860), key="g-golden", direction=(-0.6, 1.0, -0.25))
    b, _ = ps.hero(style=R.NIGHT, size=(1300, 860), key="g-night", direction=(-0.5, 1.0, -0.2), door=50)
    clear = M.build(replace(m.spec, skin="clear", furnish=True))
    pts = np.vstack([p.mesh.verts for p in clear.pieces if p.tag in ("frame", "base", "deck") and len(p.mesh.verts)])
    cam = R.framed(pts, (-0.4, 1.0, -0.35), fov=30, width=1300, height=860, margin=1.05)
    c_img = ps.shots.shot("g-clear", cam, replace(R.DAY, lights=[]), R.View(door_open=0), model=clear)
    pts = ps.shots.dome_points(("frame", "skin", "base", "door", "glass", "deck"))
    cam = R.framed(pts, (0.25, 0.75, -1.0), fov=30, width=1300, height=860, margin=0.92)
    d_img = ps.shots.shot("g-aerial", cam, R.DAY, R.View())
    for i, (img, cap) in enumerate(((a, "Golden hour"), (b, "At night"), (c_img, "As a greenhouse: clear skin"), (d_img, "From above"))):
        pl = s.image(img, X0 + (i % 2) * (w + 10), Y0 + (1 - i // 2) * (h + 10), w, h)
        s.text(cap, pl.x + 6, pl.y + 8, 7.8, "Sans-B", (1, 1, 1))


def s_declared(ps: PlanSet):
    t, m = ps.t, ps.m
    s = ps.sheet("Declared Inputs and Checks", "what the model was told, and how its figures were checked")
    rows = []
    for k, d in M.DECLARED.items():
        v = d.value
        shown = (both(v) if d.unit == "m" else f"{v:g} {d.unit}")
        rows.append((k, shown, d.kind, d.why[:118] + ("..." if len(d.why) > 118 else "")))
    y = s.top - 4
    s.table(X0, y, [("Input", 92, "l"), ("Value", 110, "l"), ("Kind", 42, "l"), ("Why", X1 - X0 - 244, "l")], rows, 6.2)
    checks = M.validate(m.spec)
    y2 = Y0 + 98
    s.heading("Self-checks against two_v_demo.panel_method", X0, y2 + 6, 8.5)
    for i, c in enumerate(checks):
        s.text("•  " + c, X0 + 4, y2 - 12 - i * 10, 7.0)
    s.para("""<b>Credits.</b> The framed-panel jig method is the one taught by Trillium Domes (trilliumdomes.com); buy their plans for
their own designs. These sheets were drawn by Dome Sketch (sketch-claude) from this repository's solver, two_v_demo.panel_method,
for this dome alone. Choices are declared above and estimates are labelled as estimates. Check every figure against your own
stock before cutting, and build one panel and one seam before you build a dome.""", X0, Y0 + 44, X1 - X0, 7.4, color=GREY)


s_glance.title = "The Dome at a Glance"
s_materials.title = "Tools and Materials"
s_sections.title = "Member Sections and Bevels"
s_base_layout.title = "Base Layout"
s_nest.title = "Sheet Layout"
s_declared.title = "Declared Inputs and Checks"

SHEETS = [s_cover, s_welcome, s_glance, s_materials, s_exploded, s_panel_map, s_panel_dims, s_angles, s_sections, s_cutlist,
          s_stick_details, s_step_rip, s_step_jig, s_step_rails, s_step_tails, s_step_heads, s_step_assemble, s_partials,
          s_windows, s_sections_step, s_covering, s_base_step, s_base_layout, s_assembly, s_door, s_finish, s_nest,
          s_floor_plan, s_gallery, s_declared]
