"""The wedge zome's 3-D world: walk round it, pull it apart, measure every part.

    py -3.12 -m wedge_zome.app                       # the interactive world
    py -3.12 -m wedge_zome.app --still out.png --view front [--person]   # one frame, no window
    py -3.12 -m wedge_zome.app --validate
    py -3.12 -m wedge_zome.app --fabrication         # the cut how-to package

It is the wedge dome's world with a zome in it -- the same renderer, camera,
mesh builder and shaders, imported from ``geodesic_raw_wedge_dome_dihedral`` --
and the same controls wherever the dome's apply. Everything you can see is
:mod:`wedge_zome.geometry`'s, and everything it measures is read off the solids.

Scale is everywhere: a ground grid in feet, rulers on the jig table, a
six-foot person you can pick up and put down, and a click on any stick reads
out its section, its three edge lengths, its two end cuts and its board feet.
F1 prints every control.
"""

from __future__ import annotations

import json
import math
import sys
from pathlib import Path
from types import SimpleNamespace

import numpy as np

from . import fabrication, geometry as g

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "exports" / "wedge_zome"            # an address: medialib files it in the library
CONFIG = Path(__file__).resolve().parent / "settings.json"   # the app's own state, not output

WOOD = (0.86, 0.66, 0.42, 1.0)
WOOD_B = (0.78, 0.55, 0.32, 1.0)
PICK = (1.0, 0.62, 0.22, 1.0)
SELECT = (1.0, 0.86, 0.30, 1.0)
BLOCK = (0.58, 0.40, 0.24, 1.0)
WATER = (0.45, 0.72, 0.92, 0.55)
SKIN = (0.95, 0.93, 0.86, 0.42)
SILL = (0.45, 0.33, 0.22, 1.0)
POST = (0.62, 0.46, 0.30, 1.0)
GRASS = (0.42, 0.55, 0.30, 1.0)
TABLE = (0.72, 0.68, 0.60, 1.0)
TICK = (0.10, 0.10, 0.10, 1.0)
NODE = (0.92, 0.30, 0.25, 1.0)
SHIRT = (0.22, 0.42, 0.66, 1.0)
PANTS = (0.20, 0.22, 0.26, 1.0)
SKINTONE = (0.80, 0.62, 0.48, 1.0)
GROUND_Z = -g.D["sill_in"]

#: The person: declared, not derived -- the height a reader asked to see beside the frame.
PERSON_IN = 72.0
#: Board feet: cubic inches in one.
BF_IN3 = 144.0

CONTROLS = """
THE WEDGE ZOME -- CONTROLS
--------------------------
Mouse                     Look around (Tab frees the mouse to point and click)
Mouse wheel               Zoom on the crosshair; at full zoom the arrows pan
W A S D / arrows          Walk (the arrows move the person when the person is selected)
F                         Walk / fly;  PageUp / PageDown up and down in fly mode
Shift                     Faster
Left click                Measure the stick under the crosshair (or the cursor)
Right click               Put the selected person down where you point

M                         Method: wedge sticks (back out) / square sticks + wedge blocks
U                         Wedge way round: back out (closes outside) / point out (opens outside)
K                         Flip the pinwheel (counter-clockwise / clockwise)
, / .                     Log diameter down / up 0.5 in
- / =                     Panel side down / up 1 in
1 2 3 4 / 0               Pick a row (its cuts in the HUD) / clear
[ / ]                     Previous / next seam (the seam map and its join, bottom right)
Z / X / C                 Explode panels 2 in less / more / back together
Q                         Solo the selected panel
I                         Ideal zome edges           N  Node markers
J                         Pinwheel arrows (tail -> head)
O                         Inside channels (wedge) / outside blocks (square)
P                         Cotton skin                G  Ground grid in feet
V                         Wood on / off              8  Sill and rim posts
T                         Jig table                  Y / Shift+Y  Next / previous row on the jig
9 / 0                     Jig walk-through: step back / forward (0 with no row picked)
L                         Camera to the jig          R  Camera back outside
6                         Select / deselect the 6 ft person      7  Show / hide the person
Home / End                Turn the selected person
B                         Export the bill of materials (CSV)
E                         Export the fabrication package + OBJ of the frame
F12                       Screenshot            F1  These controls      F2  Legend on / off
Esc                       Free the mouse; Esc again quits
"""


def _dome():
    import geodesic_raw_wedge_dome_dihedral as dome
    return dome


def ftin(inches: float) -> str:
    """inches as feet and inches to the nearest sixteenth."""
    sixteenths = round(inches * 16)
    ft, rem = divmod(sixteenths, 12 * 16)
    whole, frac = divmod(rem, 16)
    frac_s = ""
    if frac:
        n, d = frac, 16
        while n % 2 == 0:
            n //= 2
            d //= 2
        frac_s = f" {n}/{d}"
    return (f"{ft} ft " if ft else "") + f"{whole}{frac_s} in"


# ----------------------------------------------------------------------
# State
# ----------------------------------------------------------------------

class State:
    """Everything the world shows, and the zome it is built from."""

    def __init__(self) -> None:
        self.method, self.orient, self.hand = "wedge", "back", "ccw"
        self.log_in = g.D["log_in"]
        z, side = g._zome()
        self.side_in = side
        self.row = 0
        self.explode = 0.0
        self.solo = False
        self.wood = self.channels = self.posts = self.grid = self.jig = self.hud = self.legend = True
        self.ideal = self.nodes = self.pinwheel = self.skin = False
        self.seam = 0
        self.stick = None              # (panel index, stick index)
        self.jig_row, self.jig_step = 2, 4
        self.person = True
        self.person_sel = False
        self.person_at = np.array([-112.0, -58.0])
        self.person_yaw = 120.0

    def model(self):
        return g.build(self.method, round(self.log_in, 2), round(self.side_in, 2), self.hand, self.orient)

    def save(self) -> None:
        data = {k: (v.tolist() if isinstance(v, np.ndarray) else v) for k, v in vars(self).items()}
        CONFIG.write_text(json.dumps(data, indent=1), encoding="utf-8")

    def load(self) -> None:
        if not CONFIG.is_file():
            return
        try:
            data = json.loads(CONFIG.read_text(encoding="utf-8"))
        except (OSError, ValueError):
            return
        for k, v in data.items():
            if hasattr(self, k):
                setattr(self, k, np.array(v) if k == "person_at" else (tuple(v) if k == "stick" and v else v))


# ----------------------------------------------------------------------
# Solids
# ----------------------------------------------------------------------

def _solid(acc, tails, heads, colour) -> None:
    """A prism between two end polygons, every face wound to face outward."""
    centre = np.mean(np.vstack([tails, heads]), axis=0)

    def face(pts):
        n = np.cross(pts[1] - pts[0], pts[2] - pts[0])
        if np.linalg.norm(n) < 1e-12:
            return
        if n @ (np.mean(pts, axis=0) - centre) < 0:
            pts = pts[::-1]
        for k in range(1, len(pts) - 1):
            acc.add_triangle(pts[0], pts[k], pts[k + 1], colour)

    face(list(tails))
    face(list(heads))
    m = len(tails)
    for k in range(m):
        face([tails[k], tails[(k + 1) % m], heads[(k + 1) % m], heads[k]])


def _box(acc, lo, hi, colour) -> None:
    lo, hi = np.asarray(lo, float), np.asarray(hi, float)
    ring = [np.array([lo[0], lo[1], lo[2]]), np.array([hi[0], lo[1], lo[2]]),
            np.array([hi[0], hi[1], lo[2]]), np.array([lo[0], hi[1], lo[2]])]
    _solid(acc, ring, [p + np.array([0, 0, hi[2] - lo[2]]) for p in ring], colour)


def person_mesh(acc, at, yaw_deg: float, selected: bool) -> None:
    """A plain six-foot figure, feet on the ground: legs, body, arms, head."""
    a = math.radians(yaw_deg)
    R = np.array([[math.cos(a), -math.sin(a), 0], [math.sin(a), math.cos(a), 0], [0, 0, 1.0]])
    base = np.array([at[0], at[1], GROUND_Z])
    h = PERSON_IN

    def box(lo, hi, colour):
        lo, hi = np.asarray(lo, float), np.asarray(hi, float)
        corners = [np.array([x, y, lo[2]]) for x, y in ((lo[0], lo[1]), (hi[0], lo[1]), (hi[0], hi[1]), (lo[0], hi[1]))]
        _solid(acc, [base + R @ c for c in corners], [base + R @ (c + np.array([0, 0, hi[2] - lo[2]])) for c in corners],
               colour)

    leg = 0.455 * h
    box((-5.5, -2.6, 0), (-0.6, 2.6, leg), PANTS)
    box((0.6, -2.6, 0), (5.5, 2.6, leg), PANTS)
    box((-7.6, -3.6, leg), (7.6, 3.6, 0.80 * h), SHIRT)
    box((-10.4, -2.0, 0.44 * h), (-7.8, 2.0, 0.79 * h), SHIRT)
    box((7.8, -2.0, 0.44 * h), (10.4, 2.0, 0.79 * h), SHIRT)
    box((-1.8, -1.8, 0.80 * h), (1.8, 1.8, 0.84 * h), SKINTONE)
    r = (h - 0.84 * h) / 2
    acc.add_octa_sphere(base + np.array([0, 0, 0.84 * h + r]), r, SKINTONE)
    if selected:
        for k in range(24):
            t0, t1 = math.tau * k / 24, math.tau * (k + 1) / 24
            p0 = base + np.array([16 * math.cos(t0), 16 * math.sin(t0), 0.3])
            p1 = base + np.array([16 * math.cos(t1), 16 * math.sin(t1), 0.3])
            q0 = base + np.array([19 * math.cos(t0), 19 * math.sin(t0), 0.3])
            q1 = base + np.array([19 * math.cos(t1), 19 * math.sin(t1), 0.3])
            acc.add_quad(p0, q0, q1, p1, SELECT)


def jig_origin(model) -> np.ndarray:
    r = float(np.max(np.linalg.norm(model.vertices[:, :2], axis=1)))
    return np.array([r + 48.0, -30.0, GROUND_Z + 32.0])


def jig_frame(model, row):
    """The jig's flat frame for a row's panel: (origin, x, y, panel, flat())."""
    p = next(q for q in model.panels if q.row == row)
    pts = [model.vertices[k] for k in p.corners]
    x = g.unit(pts[1] - pts[0])
    y = np.cross(p.normal, x)
    o = jig_origin(model)
    # centre the panel's outline over the table's middle
    cx = np.mean([[float((q - pts[0]) @ x), float(-(q - pts[0]) @ y)] for q in pts], axis=0)

    def flat(q):
        r = q - pts[0]
        return o + np.array([float(r @ x) - cx[0], float(-(r @ y)) - cx[1], float(-(r @ p.normal)) + 0.01])

    return p, flat


class Scene:
    """CPU meshes, lines and labels for one state."""

    def __init__(self, state: State) -> None:
        self.s = state
        self.m = state.model()
        self.labels: list[tuple[np.ndarray, str, tuple]] = []

    def shift(self, p) -> np.ndarray:
        return p.normal * self.s.explode

    def selected_panel(self):
        if self.s.stick:
            return self.m.panels[self.s.stick[0]]
        if self.s.row:
            return next(p for p in self.m.panels if p.row == self.s.row)
        sm = self.m.seams[self.s.seam % len(self.m.seams)]
        return self.m.panels[sm.panels[0]]

    def build(self) -> dict:
        dome = _dome()
        s, m = self.s, self.m
        acc = {k: dome.MeshAccumulator() for k in ("wood", "pick", "extra", "clear", "skin", "nodes", "person",
                                                   "ground", "jig")}
        lines = {k: dome.LineAccumulator() for k in ("grid", "ideal", "pinwheel", "seam")}
        seam = m.seams[s.seam % len(m.seams)]
        seam_sticks = {(seam.panels[0], g.stick_on(m.panels[seam.panels[0]], seam.a, seam.b).side),
                       (seam.panels[1], g.stick_on(m.panels[seam.panels[1]], seam.a, seam.b).side)}
        solo = self.selected_panel().index if s.solo else None
        if s.wood:
            for p in m.panels:
                if solo is not None and p.index != solo:
                    continue
                sh = self.shift(p)
                for k, st in enumerate(p.sticks):
                    tails, heads = st.ends
                    key = (p.index, k)
                    if s.stick == key:
                        target, col = acc["pick"], SELECT
                    elif (s.row and p.row == s.row) or key in seam_sticks:
                        target, col = acc["pick"], PICK
                    else:
                        target, col = acc["wood"], (WOOD if k % 2 == 0 else WOOD_B)
                    _solid(target, [t + sh for t in tails], [h + sh for h in heads], col)
        if s.channels and s.explode < 1e-6 and solo is None:
            for sm in m.seams:
                pa, pb = m.panels[sm.panels[0]], m.panels[sm.panels[1]]
                e0, e1 = m.vertices[sm.a], m.vertices[sm.b]
                sa, sb = g.stick_on(pa, sm.a, sm.b), g.stick_on(pb, sm.a, sm.b)
                if m.method == "wedge":
                    da = sa.v * sa.section[2][0] + sa.n * sa.section[2][1]
                    db = sb.v * sb.section[2][0] + sb.n * sb.section[2][1]
                    if m.orient == "point":
                        da = sa.v * sa.section[0][0] + sa.n * sa.section[0][1]
                        db = sb.v * sb.section[0][0] + sb.n * sb.section[0][1]
                    ring = [[x, x + da, x + db] for x in (e0 + (e1 - e0) * 0.18, e0 + (e1 - e0) * 0.82)]
                    _solid(acc["clear"], ring[0], ring[1], WATER)
                else:
                    ring = [[x, x + pa.normal * m.stick_h, x + pb.normal * m.stick_h] for x in (e0, e1)]
                    _solid(acc["extra"], ring[0], ring[1], BLOCK)
        if s.skin and solo is None:
            for p in m.panels:
                pts = [m.vertices[k] + self.shift(p) + p.normal * (0.3 if m.method == "wedge" else m.stick_h + 0.3)
                       for k in p.corners]
                acc["skin"].add_quad(*pts, SKIN)
        if s.posts:
            self._posts(acc["extra"])
        if s.nodes:
            for i in sorted({k for p in m.panels for k in p.corners}):
                acc["nodes"].add_octa_sphere(m.vertices[i], 1.6, NODE)
        if s.ideal:
            for p in m.panels:
                for k in range(4):
                    lines["ideal"].add(m.vertices[p.corners[k]], m.vertices[p.corners[(k + 1) % 4]], (0.2, 0.9, 1.0, 1.0))
        if s.pinwheel:
            for p in m.panels:
                for st in p.sticks:
                    tails, heads = st.ends
                    t, h = np.mean(tails, axis=0) + self.shift(p), np.mean(heads, axis=0) + self.shift(p)
                    lines["pinwheel"].add(t, h, (1.0, 0.25, 0.85, 1.0))
                    tip = h - st.d * 3.0
                    lines["pinwheel"].add(h, tip + st.v * 1.5, (1.0, 0.25, 0.85, 1.0))
        a, b = m.vertices[seam.a], m.vertices[seam.b]
        lines["seam"].add(a, b, (1.0, 0.2, 0.2, 1.0))
        lines["seam"].add(a + np.array([0, 0, 0.6]), b + np.array([0, 0, 0.6]), (1.0, 0.2, 0.2, 1.0))
        self.labels.append(((a + b) / 2 + np.array([0, 0, 4.0]),
                            f"seam {s.seam % len(m.seams) + 1}: fold {seam.fold:.1f}°, V {seam.gap:.1f}° {seam.gap_side}",
                            (255, 120, 110)))
        self._ground(acc["ground"], lines["grid"])
        if s.jig:
            self._jig(acc["jig"])
        if s.person:
            person_mesh(acc["person"], s.person_at, s.person_yaw, s.person_sel)
            head = np.array([s.person_at[0], s.person_at[1], GROUND_Z + PERSON_IN + 4.0])
            self.labels.append((head, f"{ftin(PERSON_IN)}" + (" (selected)" if s.person_sel else ""),
                                (255, 230, 150) if s.person_sel else (240, 240, 240)))
        if s.stick:
            p = m.panels[s.stick[0]]
            st = p.sticks[s.stick[1]]
            tails, heads = st.ends
            mid = (np.mean(tails, axis=0) + np.mean(heads, axis=0)) / 2 + self.shift(p)
            self.labels.append((mid + p.normal * 6.0, f"{part_name(m, st)}: {ftin(st.lengths()[0])}",
                                (255, 220, 120)))
        meshes = {k: v.finish() for k, v in acc.items()}
        meshes.update({f"lines:{k}": v.finish() for k, v in lines.items()})
        return meshes

    def _posts(self, acc) -> None:
        m = self.m
        rim = [m.vertices[i] for i in m.rim]
        low = min(float(v[2]) for v in rim)
        lows = [v for v in rim if float(v[2]) - low < 1e-6]
        for a, b in zip(lows, lows[1:] + lows[:1]):
            out = g.unit(np.array([a[0] + b[0], a[1] + b[1], 0.0]))
            sec = [np.array([0, 0, 0.0]), out * 5.0, np.array([0, 0, -g.D["sill_in"]])]
            _solid(acc, [a + q for q in sec], [b + q for q in sec], SILL)
        side = fabrication.facts(m.method, m)["post_square"]
        for i, height in m.posts:
            top = m.vertices[i]
            foot = top - np.array([0, 0, height + g.D["sill_in"]])
            h = side / 2
            _box(acc, foot - np.array([h, h, 0]), top + np.array([h, h, -1.0]), POST)

    def _ground(self, acc, grid) -> None:
        r = float(np.max(np.linalg.norm(self.m.vertices[:, :2], axis=1))) * 3.4
        for k in range(72):
            a0, a1 = math.tau * k / 72, math.tau * (k + 1) / 72
            acc.add_triangle(np.array([0, 0, GROUND_Z]), np.array([r * math.cos(a0), r * math.sin(a0), GROUND_Z]),
                             np.array([r * math.cos(a1), r * math.sin(a1), GROUND_Z]), GRASS,
                             normal=np.array([0, 0, 1.0]))
        if not self.s.grid:
            return
        span = int(r // 12)
        z = GROUND_Z + 0.15
        for k in range(-span, span + 1):
            c = (0.95, 0.95, 0.85, 1.0) if k % 5 == 0 else (0.78, 0.84, 0.66, 1.0)
            limit = math.sqrt(max(0.0, r * r - (k * 12) ** 2))
            grid.add(np.array([k * 12, -limit, z]), np.array([k * 12, limit, z]), c)
            grid.add(np.array([-limit, k * 12, z]), np.array([limit, k * 12, z]), c)
            if k > 0 and k % 5 == 0:
                # distances from the zome's centre, along one line out to the left of the front view
                self.labels.append((np.array([-k * 12, -6.0, z + 1]), f"{k} ft", (245, 245, 225)))

    def _jig(self, acc) -> None:
        m, s = self.m, self.s
        p, flat = jig_frame(m, s.jig_row)
        o = jig_origin(m)
        side = float(np.linalg.norm(m.vertices[p.corners[1]] - m.vertices[p.corners[0]]))
        half = side * 0.95
        top = o[2] - 0.01
        _box(acc, (o[0] - half, o[1] - half, top - 1.5), (o[0] + half, o[1] + half, top), TABLE)
        for cx in (-half + 2, half - 4):
            for cy in (-half + 2, half - 4):
                _box(acc, (o[0] + cx, o[1] + cy, GROUND_Z), (o[0] + cx + 2, o[1] + cy + 2, top - 1.5), TABLE)
        # rulers along two edges: an inch tick, longer at six inches, longest at the foot
        x0, y0 = o[0] - half, o[1] - half
        n = int(2 * half)
        for k in range(n + 1):
            length = 2.4 if k % 12 == 0 else (1.4 if k % 6 == 0 else 0.7)
            _box(acc, (x0 + k - 0.06, y0, top), (x0 + k + 0.06, y0 + length, top + 0.08), TICK)
            _box(acc, (x0, y0 + k - 0.06, top), (x0 + length, y0 + k + 0.06, top + 0.08), TICK)
            if k and k % 12 == 0:
                self.labels.append((np.array([x0 + k, y0 - 1.5, top + 0.5]), f"{k // 12} ft", (20, 20, 20)))
                self.labels.append((np.array([x0 - 2.0, y0 + k, top + 0.5]), f"{k // 12} ft", (20, 20, 20)))
        # the row's outline, as screwed-down stops
        pts = [flat(m.vertices[k]) for k in p.corners]
        for k in range(4):
            a, b = pts[k], pts[(k + 1) % 4]
            d = g.unit(b - a)
            n_ = np.cross(np.array([0, 0, 1.0]), d)
            c = np.mean(pts, axis=0)
            if n_ @ (c - a) > 0:
                n_ = -n_
            ring = [a, b, b + n_ * 1.5, a + n_ * 1.5]
            _solid(acc, [q + np.array([0, 0, 0.0]) for q in ring], [q + np.array([0, 0, 1.5]) for q in ring], TICK)
        for k, st in enumerate(p.sticks[:s.jig_step]):
            tails, heads = st.ends
            _solid(acc, [flat(t) for t in tails], [flat(h) for h in heads], PICK if k == s.jig_step - 1 else WOOD)
            mid = (np.mean([flat(t) for t in tails], axis=0) + np.mean([flat(h) for h in heads], axis=0)) / 2
            self.labels.append((mid + np.array([0, 0, 7.0]), f"{k + 1}: {ftin(st.lengths()[0])}", (255, 230, 160)))


def part_name(model, stick) -> str:
    """The stick's name in the cut schedule (R2A, R2B, ...)."""
    lens = stick.lengths()
    tm, tb = stick.cut(stick.tail)
    for t in g.stick_types(model):
        if (t["row"] == stick.row and abs(t["outer"] - lens[0]) < 0.01 and abs(t["tail"][0] - tm) < 0.05
                and abs(t["tail"][1] - tb) < 0.05):
            return t["name"]
    return f"R{stick.row}"


def measure_lines(model, key) -> list[str]:
    """Everything a builder needs to know about one stick."""
    p = model.panels[key[0]]
    st = p.sticks[key[1]]
    lens = st.lengths()
    tm, tb = st.cut(st.tail)
    hm, hb = st.cut(st.head)
    area = 0.5 * model.stick_w * model.stick_h if model.method == "wedge" else model.stick_w * model.stick_h
    bf = area * max(lens) / BF_IN3
    from square_book import geometry as sg
    kerf = sg.D["kerf_in"]
    per = int((g.D["section_in"] + kerf) // (max(lens) + kerf))
    sec = (f"wedge: back {model.stick_w:.2f} in wide x {model.stick_h:.2f} in deep, point {model.wedge.theta:.0f}°"
           if model.method == "wedge" else f"square: {model.stick_w:.2f} x {model.stick_h:.2f} in (two wedges, planed)")
    names = ["outer back edge", "inner back edge", "point"] if model.method == "wedge" else \
        ["outer edge", "inner edge", "inner far edge", "outer far edge"]
    out = [f"PART {part_name(model, st)} -- row {st.row}, panel {p.index + 1}, side {st.side + 1}", sec]
    for name, L in zip(names, lens):
        out.append(f"  {name}: {L:.2f} in  ({ftin(L)})")
    out += [f"  tail: mitre {abs(tm):.1f}° {'L' if tm < 0 else 'R'}, bevel {abs(tb):.1f}°",
            f"  head: mitre {abs(hm):.1f}° {'L' if hm < 0 else 'R'}, bevel {abs(hb):.1f}°",
            f"  {bf:.2f} board feet; {per} from one {g.D['section_in']:.0f} in wedge of a {model.log_in:.1f} in log"]
    return out


# ----------------------------------------------------------------------
# HUD panels
# ----------------------------------------------------------------------

def hud_lines(state: State, model) -> list[str]:
    f = fabrication.facts(model.method, model)
    st = f["stock"]
    out = ["THE WEDGE ZOME",
           f"{f['panels']} panels, {len(f['rows'])} rows, {f['rim_ft']:.1f} ft across, {f['height_ft']:.1f} ft tall; "
           f"panel side {ftin(f['side'])}; log {model.log_in:.1f} in, split {f['splits']} ways"]
    if model.method == "wedge":
        out.append(f"WEDGE STICKS, {'BACK' if model.orient == 'back' else 'POINT'} OUT, pinwheel {model.hand.upper()}: "
                   f"seams V {f['gap_lo']:.1f}-{f['gap_hi']:.1f}° {model.seams[0].gap_side}")
        out.append(f"every end: bevel {f['half']:.1f}° (half the wedge's point)" if model.orient == "back" else
                   "point out: the seams open on the weather side -- why the method lays the back out")
    else:
        out.append(f"SQUARE STICKS {f['stick_w']:.2f} in: outside V filled by wedge blocks")
    out.append(f"{st['sticks']} sticks, {st['wedges']} wedges, {st['sections']} log sections of "
               f"{f['section']:.0f} in; explode {state.explode:.0f} in")
    if state.row:
        r = f["rows"][state.row - 1]
        out += ["", f"ROW {state.row}{' (the crown)' if state.row == 1 else ''}: {r['panels']} panels, sharp corner "
                    f"{r['acute']:.1f}°, fold up to {r['fold_max']:.1f}°"]
        for t in f["types"]:
            if t["row"] == state.row:
                out.append(f"  {t['name']} x{t['count']}: {ftin(t['outer'])} outer edge, mitre "
                           f"{abs(t['tail'][0]):.1f}° {'L' if t['tail'][0] < 0 else 'R'}, bevel {abs(t['tail'][1]):.1f}°")
    if state.legend:
        out += ["", "click a stick to measure it  |  F1 every control  |  F2 hide this",
                "M method  U way round  K pinwheel  1-4 row  [ ] seam  Z X C explode  T jig  9 0 jig steps",
                "6 select person, arrows move it, right click place it  |  G grid  , . log  - = side  E export"]
    return out


def jig_lines(state: State, model) -> list[str]:
    p, _flat = jig_frame(model, state.jig_row)
    out = [f"JIG -- ROW {state.jig_row}, STEP {state.jig_step} OF 4",
           f"sharp corner {p.acute:.1f}°; rulers in inches, a long tick every foot"]
    if state.jig_step == 0:
        out.append("Stops screwed to the sheet at the row's rhombus, full size. No sticks yet.")
    else:
        st = p.sticks[state.jig_step - 1]
        tm, tb = st.cut(st.tail)
        out.append(f"Stick {state.jig_step} ({part_name(model, st)}): back down, outer edge on the stop.")
        out.append(f"  {ftin(st.lengths()[0])} on the outer edge; ends mitre {abs(tm):.1f}°, bevel {abs(tb):.1f}°.")
        out.append("  Head into its corner; tail against the side of the stick before it." if state.jig_step > 1 else
                   "  The first stick runs corner to corner of its edge, head into the corner.")
        if state.jig_step == 4:
            out.append("  Glue and screw every butt, in the thick part, pilot holes. The panel comes off true.")
    return out


def join_lines(state: State, model) -> list[str]:
    sm = model.seams[state.seam % len(model.seams)]
    return [f"SEAM {state.seam % len(model.seams) + 1} OF {len(model.seams)}  rows {sm.row_pair[0]} / {sm.row_pair[1]}",
            f"fold {sm.fold:.2f}°  length {ftin(sm.length)}",
            f"V {sm.gap:.2f}° on the {sm.gap_side}" +
            (f" -- a block split {round(360 / sm.fold)} ways" if model.method == "square" else "")]


def text_surface(lines: list[str], width: int, scale: float = 1.0, title_colour=(255, 205, 130)):
    import pygame

    pygame.font.init()
    font = pygame.font.SysFont("segoeui,arial", int(16 * scale))
    bold = pygame.font.SysFont("segoeui,arial", int(18 * scale), bold=True)
    step = int(22 * scale)
    surf = pygame.Surface((width, int(12 * scale) + step * len(lines)), pygame.SRCALPHA)
    surf.fill((12, 14, 18, 195))
    y = int(6 * scale)
    for k, line in enumerate(lines):
        head = k == 0 or line.startswith(("ROW", "PART", "JIG", "SEAM"))
        surf.blit((bold if head else font).render(line, True, title_colour if head else (232, 228, 218)),
                  (int(10 * scale), y))
        y += step
    return surf


def minimap_surface(state: State, model, size: int = 250, scale: float = 1.0):
    """The zome from above: every edge, the picked row, the selected seam in red."""
    import pygame

    s = int(size * scale)
    surf = pygame.Surface((s, s), pygame.SRCALPHA)
    surf.fill((12, 14, 18, 195))
    v = model.vertices
    r = float(np.max(np.linalg.norm(v[:, :2], axis=1)))

    def px(p):
        return (int(s / 2 + p[0] / r * s * 0.44), int(s / 2 - p[1] / r * s * 0.44))

    for p in model.panels:
        pts = [px(v[k]) for k in p.corners]
        if state.row and p.row == state.row:
            pygame.draw.polygon(surf, (180, 110, 40, 255), pts)
        pygame.draw.polygon(surf, (150, 150, 140, 255), pts, max(1, int(scale)))
    sm = model.seams[state.seam % len(model.seams)]
    pygame.draw.line(surf, (255, 70, 60, 255), px(v[sm.a]), px(v[sm.b]), max(3, int(4 * scale)))
    if state.person:
        pygame.draw.circle(surf, (110, 170, 255, 255), px(np.array([*state.person_at, 0])), max(3, int(4 * scale)))
    return surf


def labels_surface(labels, vp, width, height, scale: float = 1.0):
    """World labels projected to the screen, each on a small dark tag."""
    import pygame

    pygame.font.init()
    font = pygame.font.SysFont("segoeui,arial", int(15 * scale), bold=True)
    surf = pygame.Surface((width, height), pygame.SRCALPHA)
    for pos, text, colour in labels:
        clip = vp @ np.array([pos[0], pos[1], pos[2], 1.0])
        if clip[3] <= 1e-6:
            continue
        ndc = clip[:3] / clip[3]
        if abs(ndc[0]) > 1.05 or abs(ndc[1]) > 1.05 or ndc[2] > 1:
            continue
        x, y = (ndc[0] + 1) / 2 * width, (1 - ndc[1]) / 2 * height
        t = font.render(text, True, colour)
        pad = int(3 * scale)
        dark = colour[0] + colour[1] + colour[2] < 150
        bg = pygame.Surface((t.get_width() + 2 * pad, t.get_height() + 2 * pad), pygame.SRCALPHA)
        bg.fill((255, 255, 255, 190) if dark else (10, 12, 16, 170))
        bg.blit(t, (pad, pad))
        surf.blit(bg, (int(x - bg.get_width() / 2), int(y - bg.get_height())))
    return surf


# ----------------------------------------------------------------------
# Views and picking
# ----------------------------------------------------------------------

VIEWS = {
    "front": ((0.0, -330.0, 70.0), (0.0, 0.0, 40.0)),
    "high": ((180.0, -260.0, 230.0), (0.0, 0.0, 30.0)),
    "inside": ((0.0, -20.0, 40.0), (0.0, 30.0, 95.0)),
    "seam": ((60.0, -120.0, 85.0), (40.0, -45.0, 70.0)),
    "jig": ((150.0, -110.0, 80.0), (128.0, -30.0, 20.0)),
    "person": ((150.0, -230.0, 60.0), (60.0, -40.0, 36.0)),
}


def _aim(camera, eye, target) -> None:
    camera.position = np.array(eye, dtype=float)
    d = np.array(target, dtype=float) - camera.position
    camera.yaw_deg = math.degrees(math.atan2(d[1], d[0]))
    camera.pitch_deg = math.degrees(math.atan2(d[2], math.hypot(d[0], d[1])))


def _config():
    return SimpleNamespace(camera_height_in=64.0 + GROUND_Z, mouse_sensitivity_deg_px=0.12,
                           walk_speed_in_s=90.0, sprint_multiplier=3.0)


def pick_stick(model, explode: float, origin, direction):
    """The stick the ray hits first: each stick tested as a capsule round its axis."""
    best, best_t = None, float("inf")
    radius = 0.55 * max(model.stick_w, model.stick_h)
    for p in model.panels:
        sh = p.normal * explode
        for k, st in enumerate(p.sticks):
            tails, heads = st.ends
            a, b = np.mean(tails, axis=0) + sh, np.mean(heads, axis=0) + sh
            u, v, w0 = direction, b - a, origin - a
            A, B, C = u @ u, u @ v, v @ v
            D, E = u @ w0, v @ w0
            den = A * C - B * B
            if abs(den) < 1e-9:
                continue
            sc = (B * E - C * D) / den
            tc = min(1.0, max(0.0, (A * E - B * D) / den))
            sc = max(0.0, (B * tc - D) / A)
            dist = np.linalg.norm(w0 + u * sc - v * tc)
            if dist < radius and sc < best_t:
                best, best_t = (p.index, k), sc
    return best


def ground_hit(origin, direction):
    if direction[2] >= -1e-6:
        return None
    t = (GROUND_Z - origin[2]) / direction[2]
    return origin + direction * t


def ray_through(vp_inv, x, y, width, height):
    nx, ny = 2 * x / width - 1, 1 - 2 * y / height
    near = vp_inv @ np.array([nx, ny, -1.0, 1.0])
    far = vp_inv @ np.array([nx, ny, 1.0, 1.0])
    near, far = near[:3] / near[3], far[:3] / far[3]
    return near, g.unit(far - near)


def draw(renderer, vp, state) -> None:
    renderer.render_mesh("ground", vp)
    renderer.render_lines("lines:grid", vp, 1.0)
    for name in ("wood", "pick", "extra", "jig", "person", "nodes"):
        renderer.render_mesh(name, vp)
    renderer.render_lines("lines:ideal", vp, 2.0)
    renderer.render_lines("lines:pinwheel", vp, 2.5)
    renderer.render_lines("lines:seam", vp, 4.0)
    renderer.render_mesh("clear", vp)
    renderer.render_mesh("skin", vp)


def upload(renderer, meshes: dict) -> None:
    for name, data in meshes.items():
        if name.startswith("lines:"):
            renderer.upload_lines(name, data)
        else:
            renderer.upload_mesh(name, data)


def render_still(path: Path, view: str = "front", state: State | None = None, size=(1600, 900),
                 hud: bool = True) -> Path:
    """One frame, offscreen, no window: for checking the world, and for the film."""
    import moderngl
    from PIL import Image

    dome = _dome()
    state = state or State()
    w, h = size
    ss = 2
    ctx = moderngl.create_standalone_context()
    fbo = ctx.framebuffer(color_attachments=[ctx.texture((w * ss, h * ss), 4)],
                          depth_attachment=ctx.depth_texture((w * ss, h * ss)))
    fbo.use()
    renderer = dome.Renderer(ctx)
    scene = Scene(state)
    upload(renderer, scene.build())
    cam = dome.FirstPersonCamera(_config(), 200.0)
    _aim(cam, *VIEWS[view])
    ctx.viewport = (0, 0, w * ss, h * ss)
    ctx.clear(0.62, 0.74, 0.86, 1.0, depth=1.0)
    proj = dome.perspective_matrix(55.0, w / h, 2.0, 20000.0)
    vp = proj @ cam.view_matrix()
    draw(renderer, vp, state)
    renderer.upload_overlay("labels", labels_surface(scene.labels, vp, w * ss, h * ss, ss))
    renderer.render_overlay("labels", w * ss, h * ss, 0, 0)
    if hud:
        renderer.upload_overlay("hud", text_surface(hud_lines(state, scene.m), 1500, ss))
        renderer.render_overlay("hud", w * ss, h * ss, 28, 28)
        if state.stick:
            surf = text_surface(measure_lines(scene.m, state.stick), 1250, ss)
            renderer.upload_overlay("measure", surf)
            renderer.render_overlay("measure", w * ss, h * ss, w * ss - surf.get_width() - 28, 28)
        if state.jig:
            surf = text_surface(jig_lines(state, scene.m), 1250, ss)
            renderer.upload_overlay("jig", surf)
            renderer.render_overlay("jig", w * ss, h * ss, 28, h * ss - surf.get_height() - 28)
        mm = minimap_surface(state, scene.m, 250, ss)
        js = text_surface(join_lines(state, scene.m), mm.get_width(), ss * 0.8)
        renderer.upload_overlay("minimap", mm)
        renderer.upload_overlay("join", js)
        renderer.render_overlay("minimap", w * ss, h * ss, w * ss - mm.get_width() - 28, h * ss - mm.get_height() - 28)
        renderer.render_overlay("join", w * ss, h * ss, w * ss - js.get_width() - 28,
                                h * ss - mm.get_height() - js.get_height() - 36)
    img = Image.frombytes("RGBA", (w * ss, h * ss), fbo.read(components=4)).transpose(Image.FLIP_TOP_BOTTOM)
    path.parent.mkdir(parents=True, exist_ok=True)
    img.resize((w, h), Image.LANCZOS).convert("RGB").save(path)
    renderer.release()
    ctx.release()
    return path


# ----------------------------------------------------------------------
# The window
# ----------------------------------------------------------------------

class ZomeWorldApp:
    def __init__(self) -> None:
        import moderngl
        import pygame

        dome = _dome()
        self.dome = dome
        pygame.init()
        pygame.display.gl_set_attribute(pygame.GL_CONTEXT_MAJOR_VERSION, 3)
        pygame.display.gl_set_attribute(pygame.GL_CONTEXT_MINOR_VERSION, 3)
        pygame.display.gl_set_attribute(pygame.GL_CONTEXT_PROFILE_MASK, pygame.GL_CONTEXT_PROFILE_CORE)
        pygame.display.gl_set_attribute(pygame.GL_DEPTH_SIZE, 24)
        self.width, self.height = 1440, 860
        pygame.display.set_mode((self.width, self.height), pygame.OPENGL | pygame.DOUBLEBUF | pygame.RESIZABLE)
        pygame.display.set_caption("The Wedge Zome -- framed from split-log wedges")
        self.ctx = moderngl.create_context()
        self.renderer = dome.Renderer(self.ctx)
        self.clock = pygame.time.Clock()
        self.state = State()
        self.state.load()
        self.camera = dome.FirstPersonCamera(_config(), 200.0)
        self.reset_camera()
        self.zoom = 0
        self.running = True
        self._label_key = None
        self._capture(True)
        self.rebuild()
        print(CONTROLS)

    # -- helpers ---------------------------------------------------------
    def reset_camera(self) -> None:
        _aim(self.camera, *VIEWS["front"])
        self.camera.walk_height = self.camera.position[2]

    def fov(self) -> float:
        return 60.0 - self.zoom * (45.0 / 8)

    def _capture(self, on: bool) -> None:
        import pygame
        self.captured = on
        pygame.event.set_grab(on)
        pygame.mouse.set_visible(not on)
        pygame.mouse.get_rel()

    def vp(self) -> np.ndarray:
        proj = self.dome.perspective_matrix(self.fov(), self.width / max(1, self.height), 2.0, 20000.0)
        return proj @ self.camera.view_matrix()

    def ray(self, mouse=None):
        if mouse is None or self.captured:
            return self.camera.position.copy(), self.camera.forward
        return ray_through(np.linalg.inv(self.vp()), mouse[0], mouse[1], self.width, self.height)

    def rebuild(self) -> None:
        s = self.state
        self.scene = Scene(s)
        m = self.scene.m
        s.seam %= len(m.seams)
        if s.stick and (s.stick[0] >= len(m.panels)):
            s.stick = None
        upload(self.renderer, self.scene.build())
        self._label_key = None
        self.renderer.upload_overlay("hud", text_surface(hud_lines(s, m), 760))
        if s.stick:
            self.renderer.upload_overlay("measure", text_surface(measure_lines(m, s.stick), 620))
        else:
            self.renderer.overlays.pop("measure", None)
        if s.jig:
            self.renderer.upload_overlay("jig", text_surface(jig_lines(s, m), 640))
        else:
            self.renderer.overlays.pop("jig", None)
        self.renderer.upload_overlay("minimap", minimap_surface(s, m))
        self.renderer.upload_overlay("join", text_surface(join_lines(s, m), 250, 0.8))
        self.renderer.upload_overlay("cross", self._crosshair())

    def _crosshair(self):
        import pygame
        surf = pygame.Surface((22, 22), pygame.SRCALPHA)
        pygame.draw.line(surf, (255, 255, 255, 220), (11, 2), (11, 20), 2)
        pygame.draw.line(surf, (255, 255, 255, 220), (2, 11), (20, 11), 2)
        return surf

    # -- input -----------------------------------------------------------
    def key(self, e) -> None:
        import pygame

        s, k, shift = self.state, e.key, bool(e.mod & pygame.KMOD_SHIFT)
        m = self.scene.m
        rebuild = True
        if k == pygame.K_ESCAPE:
            if self.captured:
                self._capture(False)
            else:
                self.running = False
            rebuild = False
        elif k == pygame.K_TAB:
            self._capture(not self.captured)
            rebuild = False
        elif k == pygame.K_m:
            s.method = "square" if s.method == "wedge" else "wedge"
            s.stick = None
        elif k == pygame.K_u:
            s.orient = "point" if s.orient == "back" else "back"
        elif k == pygame.K_k:
            s.hand = "cw" if s.hand == "ccw" else "ccw"
            s.stick = None
        elif k == pygame.K_COMMA:
            s.log_in = max(6.0, s.log_in - 0.5)
        elif k == pygame.K_PERIOD:
            s.log_in = min(24.0, s.log_in + 0.5)
        elif k == pygame.K_MINUS:
            s.side_in = max(18.0, s.side_in - 1.0)
        elif k == pygame.K_EQUALS:
            s.side_in = min(72.0, s.side_in + 1.0)
        elif k in (pygame.K_1, pygame.K_2, pygame.K_3, pygame.K_4):
            s.row = k - pygame.K_0
            s.jig_row = s.row
        elif k == pygame.K_0 and not s.row:
            s.jig_step = min(4, s.jig_step + 1)
        elif k == pygame.K_0:
            s.row = 0
        elif k == pygame.K_9:
            s.jig_step = max(0, s.jig_step - 1)
        elif k == pygame.K_LEFTBRACKET:
            s.seam = (s.seam - 1) % len(m.seams)
        elif k == pygame.K_RIGHTBRACKET:
            s.seam = (s.seam + 1) % len(m.seams)
        elif k == pygame.K_z:
            s.explode = max(0.0, s.explode - 2.0)
        elif k == pygame.K_x:
            s.explode += 2.0
        elif k == pygame.K_c:
            s.explode = 0.0
        elif k == pygame.K_q:
            s.solo = not s.solo
        elif k == pygame.K_i:
            s.ideal = not s.ideal
        elif k == pygame.K_n:
            s.nodes = not s.nodes
        elif k == pygame.K_j:
            s.pinwheel = not s.pinwheel
        elif k == pygame.K_o:
            s.channels = not s.channels
        elif k == pygame.K_p:
            s.skin = not s.skin
        elif k == pygame.K_g:
            s.grid = not s.grid
        elif k == pygame.K_v:
            s.wood = not s.wood
        elif k == pygame.K_8:
            s.posts = not s.posts
        elif k == pygame.K_t:
            s.jig = not s.jig
        elif k == pygame.K_y:
            s.jig_row = (s.jig_row - 2) % 4 + 1 if shift else s.jig_row % 4 + 1
        elif k == pygame.K_l:
            o = jig_origin(m)
            _aim(self.camera, o + np.array([20.0, -70.0, 40.0]), o)
            self.camera.fly_mode = True
            rebuild = False
        elif k == pygame.K_r:
            self.camera.fly_mode = False
            self.reset_camera()
            rebuild = False
        elif k == pygame.K_6:
            s.person_sel = not s.person_sel
            s.person = True
        elif k == pygame.K_7:
            s.person = not s.person
            s.person_sel = s.person_sel and s.person
        elif k == pygame.K_f:
            self.camera.fly_mode = not self.camera.fly_mode
            rebuild = False
        elif k == pygame.K_b:
            print(f"bill of materials written to {export_bom(m)}")
            rebuild = False
        elif k == pygame.K_e:
            out = fabrication.export(m.method, m)
            dome = self.dome
            dome.export_mesh_obj(self.scene.build()["wood"], out / "zome-frame.obj", "wedge_zome")
            print(f"fabrication package and OBJ written to {out}")
            rebuild = False
        elif k == pygame.K_F12:
            import medialib
            shot = medialib.route(OUT / "shots" / "wedge-zome-shot.png")
            pygame.image.save(pygame.display.get_surface(), str(shot))
            rebuild = False
        elif k == pygame.K_F1:
            print(CONTROLS)
            rebuild = False
        elif k == pygame.K_F2:
            s.legend = not s.legend
        elif k == pygame.K_h:
            s.hud = not s.hud
        else:
            rebuild = False
        if rebuild:
            self.rebuild()

    def click(self, button: int, pos) -> None:
        s = self.state
        origin, direction = self.ray(pos)
        if button == 1:
            hit = pick_stick(self.scene.m, s.explode, origin, direction)
            s.stick = hit
            if hit:
                print("\n".join(measure_lines(self.scene.m, hit)))
            self.rebuild()
        elif button == 3 and s.person_sel:
            p = ground_hit(origin, direction)
            if p is not None:
                s.person_at = np.array([p[0], p[1]])
                self.rebuild()

    def handle(self) -> None:
        import pygame

        for e in pygame.event.get():
            if e.type == pygame.QUIT:
                self.running = False
            elif e.type == pygame.VIDEORESIZE:
                self.width, self.height = e.w, e.h
                self._label_key = None
            elif e.type == pygame.MOUSEMOTION and self.captured:
                self.camera.mouse_look(*e.rel)
            elif e.type == pygame.MOUSEWHEEL:
                self.zoom = max(0, min(8, self.zoom + (1 if e.y > 0 else -1)))
            elif e.type == pygame.MOUSEBUTTONDOWN and e.button in (1, 3):
                self.click(e.button, e.pos)
            elif e.type == pygame.KEYDOWN:
                self.key(e)

    def update(self, dt: float) -> None:
        import pygame

        keys = pygame.key.get_pressed()
        s = self.state
        sprint = keys[pygame.K_LSHIFT] or keys[pygame.K_RSHIFT]
        arrows = (keys[pygame.K_UP] - keys[pygame.K_DOWN], keys[pygame.K_RIGHT] - keys[pygame.K_LEFT])
        if s.person_sel and any(arrows):
            step = (60.0 if sprint else 24.0) * dt
            fwd = self.camera.horizontal_forward[:2]
            right = self.camera.right[:2]
            s.person_at = s.person_at + (fwd * arrows[0] + right * arrows[1]) * step
            self.rebuild()
            arrows = (0, 0)
        if s.person_sel and (keys[pygame.K_HOME] or keys[pygame.K_END]):
            s.person_yaw += (keys[pygame.K_HOME] - keys[pygame.K_END]) * 90.0 * dt
            self.rebuild()
        fwd = keys[pygame.K_w] + arrows[0] * (self.zoom < 8) - keys[pygame.K_s]
        right = keys[pygame.K_d] - keys[pygame.K_a] + arrows[1] * (self.zoom < 8)
        up = keys[pygame.K_PAGEUP] - keys[pygame.K_PAGEDOWN]
        self.camera.move(fwd, right, up, dt, sprint)
        if self.zoom >= 8 and any(arrows):
            self.camera.pan(arrows[1], arrows[0], dt, sprint)

    def render(self) -> None:
        import pygame

        s = self.state
        self.ctx.viewport = (0, 0, self.width, self.height)
        self.ctx.clear(0.62, 0.74, 0.86, 1.0, depth=1.0)
        vp = self.vp()
        draw(self.renderer, vp, s)
        key = (tuple(np.round(vp.ravel(), 4)), self.width, self.height, id(self.scene))
        if key != self._label_key:
            self.renderer.upload_overlay("labels", labels_surface(self.scene.labels, vp, self.width, self.height))
            self._label_key = key
        self.renderer.render_overlay("labels", self.width, self.height, 0, 0)
        if s.hud:
            r = self.renderer
            r.render_overlay("hud", self.width, self.height, 14, 14)
            if "measure" in r.overlays:
                r.render_overlay("measure", self.width, self.height,
                                 self.width - r.overlays["measure"].width - 14, 14)
            if "jig" in r.overlays:
                r.render_overlay("jig", self.width, self.height, 14, self.height - r.overlays["jig"].height - 14)
            mm, js = r.overlays["minimap"], r.overlays["join"]
            r.render_overlay("minimap", self.width, self.height, self.width - mm.width - 14,
                             self.height - mm.height - 14)
            r.render_overlay("join", self.width, self.height, self.width - js.width - 14,
                             self.height - mm.height - js.height - 20)
        cross = self.renderer.overlays["cross"]
        self.renderer.render_overlay("cross", self.width, self.height, (self.width - cross.width) // 2,
                                     (self.height - cross.height) // 2)
        pygame.display.flip()

    def run(self, smoke: int = 0) -> None:
        """``smoke`` runs that many frames, pressing every rebuilding key on the
        way and clicking the crosshair, then quits."""
        import pygame

        script = {3: pygame.K_m, 5: pygame.K_u, 7: pygame.K_u, 9: pygame.K_m, 11: pygame.K_k, 13: pygame.K_2,
                  15: pygame.K_RIGHTBRACKET, 17: pygame.K_x, 19: pygame.K_c, 21: pygame.K_q, 23: pygame.K_q,
                  25: pygame.K_i, 27: pygame.K_n, 29: pygame.K_j, 31: pygame.K_o, 33: pygame.K_p, 35: pygame.K_g,
                  37: pygame.K_t, 39: pygame.K_t, 41: pygame.K_y, 43: pygame.K_9, 45: pygame.K_6,
                  47: pygame.K_PERIOD, 49: pygame.K_EQUALS, 51: pygame.K_l, 53: pygame.K_r, 55: pygame.K_k,
                  57: pygame.K_COMMA, 59: pygame.K_MINUS, 61: pygame.K_0, 63: pygame.K_F2}
        frame = 0
        while self.running:
            frame += 1
            if smoke:
                if frame in script:
                    pygame.event.post(pygame.event.Event(pygame.KEYDOWN, key=script[frame], mod=0))
                if frame == 40:
                    self.click(1, None)
                if frame == 46:
                    self.click(3, None)
                if frame >= smoke:
                    self.running = False
            dt = min(self.clock.tick(120) / 1000.0, 0.05)
            self.handle()
            self.update(dt)
            self.render()
        self.state.save()
        self.renderer.release()
        pygame.quit()


def export_bom(model) -> Path:
    """Every part, with its count, size and cuts: one CSV."""
    import csv

    import medialib
    path = medialib.route(OUT / f"wedge-zome-bom-{model.method}.csv")
    f = fabrication.facts(model.method, model)
    with path.open("w", newline="", encoding="utf-8") as fh:
        w = csv.writer(fh)
        w.writerow(["part", "count", "section", "length_in", "cut_ends"])
        sec = (f"wedge {model.stick_w:.2f} x {model.stick_h:.2f}" if model.method == "wedge"
               else f"square {model.stick_w:.2f}")
        for t in f["types"]:
            w.writerow([t["name"], t["count"], sec, f"{t['outer']:.2f}",
                        f"mitre {t['tail'][0]:.1f} bevel {t['tail'][1]:.1f}"])
        w.writerow(["rim post", f["posts"], f"square {f['post_square']:.2f}", f"{f['post_h'] + g.D['sill_in']:.2f}", "square"])
        if model.method == "square":
            for b in f["blocks"]:
                w.writerow([f"block, {b['split']}-way split", b["count"], f"wedge {b['fold']:.1f} deg",
                            f"{b['length']:.2f}", "square"])
        st = f["stock"]
        w.writerow(["wedges", st["wedges"], f"{f['section']:.0f} in", "", f"log {model.log_in:.1f} in, 8 ways"])
        w.writerow(["log sections", st["sections"], f"{model.log_in:.1f} in", f"{f['section']:.0f}", ""])
    return path


def main(argv: list[str] | None = None) -> int:
    import argparse

    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--still", type=Path, metavar="PNG")
    parser.add_argument("--view", choices=sorted(VIEWS), default="front")
    parser.add_argument("--method", choices=("wedge", "square"), default="wedge")
    parser.add_argument("--row", type=int, default=0)
    parser.add_argument("--explode", type=float, default=0.0)
    parser.add_argument("--measure", action="store_true", help="still: measure a stick of the picked row")
    parser.add_argument("--no-person", action="store_true")
    parser.add_argument("--validate", action="store_true")
    parser.add_argument("--fabrication", action="store_true")
    parser.add_argument("--smoke", type=int, default=0, help=argparse.SUPPRESS)
    args = parser.parse_args(argv)
    if args.validate:
        g.validate()
        print("ok: 36 flat rhombus panels, every stick solved, seams close outside, the book's rows agree")
        return 0
    if args.fabrication:
        g.validate()
        print(f"wrote {fabrication.export(args.method)}")
        return 0
    if args.smoke:
        ZomeWorldApp().run(smoke=args.smoke)
        print("ok: window opened, every key and both clicks rebuilt, closed")
        return 0
    if args.still:
        s = State()
        s.method, s.row, s.explode = args.method, args.row, args.explode
        s.person = not args.no_person
        if args.row:
            s.jig_row = args.row
        if args.measure:
            m = s.model()
            p = next(q for q in m.panels if q.row == (args.row or 2))
            s.stick = (p.index, 0)
        print(f"wrote {render_still(args.still, args.view, s)}")
        return 0
    ZomeWorldApp().run()
    return 0


if __name__ == "__main__":
    sys.exit(main())
