"""Files a builder takes away from Dome Sketch, made from the same scene the page draws.

Every export reads :func:`kinds.scene` -- the JSON the page itself loads -- so a file can never
disagree with the screen:

* **DXF** (R12, ASCII: every CAM program reads it). Layer ``CUT`` holds exactly what gets cut,
  once each: for the steel domes every nested sheet's plates plus the parts that are not nested
  (cap, floor pieces); for framed-panel domes the plywood skin's nesting. ``SHEET`` is each
  sheet's edge, ``ETCH`` each part's mark, ``BEVEL`` the inside face of a bevelled stick,
  ``NOTES`` the bevel on every plate edge and the dimensions, and ``OUTLINE`` one reference
  drawing of every cut family (wedges, sticks, plates, keys, logs) to scale, never to be cut.
  Inches or millimetres; sizes are true, the CAM program adds the kerf.
* **CSV cut list** -- one row per family, its count and every figure on its card, in the units
  chosen.
* **CSV materials** -- counted quantities, the declared prices, the estimated cost.
* **OBJ** (+ MTL), **STL** (binary, millimetres, Z up) and **glTF** (``.glb``, metres, Y up) of
  every built piece, the way it stands assembled.
* **design.json** -- the design itself, to open again with ``?spec=``.

:func:`bundle` makes all of them; :func:`zip_bytes` packs them for one download, and
:func:`write_pack` saves them to a new numbered folder in ``deliverables/`` (never an old one).
"""

from __future__ import annotations

import base64
import csv
import io
import json
import math
import re
import struct
import zipfile
from fractions import Fraction

import numpy as np

from . import TAG

IN = 0.0254
FT = 0.3048

FORMATS = {
    "dxf": ("application/dxf", ".dxf", "Cut outlines (DXF)"),
    "csv": ("text/csv", "-cutlist.csv", "Cut list (CSV)"),
    "materials": ("text/csv", "-materials.csv", "Materials and cost (CSV)"),
    "obj": ("application/zip", "-obj.zip", "3-D model (OBJ + MTL)"),
    "stl": ("model/stl", ".stl", "3-D model (STL, mm)"),
    "glb": ("model/gltf-binary", ".glb", "3-D model (glTF)"),
    "zip": ("application/zip", "-fabrication.zip", "Everything (zip)"),
}


# ----------------------------------------------------------------------
# Unit tokens, formatted the way the page's units.js does
# ----------------------------------------------------------------------

def _frac16(x: float) -> tuple[int, str]:
    s = round(abs(x) * 16)
    whole, f = divmod(s, 16)
    if not f:
        return whole, ""
    fr = Fraction(f, 16)
    return whole, f"{fr.numerator}/{fr.denominator}"


def ftin(m: float) -> str:
    neg, inches = m < 0, abs(m) / IN
    whole, f = _frac16(inches)
    ft, inch = divmod(whole, 12)
    ins = (f"{inch}-{f}" if (inch or ft) else f) if f else f"{inch}"
    return ("-" if neg else "") + (f"{ft}' " if ft else "") + f'{ins}"'


def inches(m: float) -> str:
    whole, f = _frac16(abs(m) / IN)
    return f"{'-' if m < 0 else ''}{whole:,}{' ' + f if f else ''} in"


def length(m: float, units: str) -> str:
    if units == "m":
        return f"{round(m * 1000):,} mm" if abs(m) < 2 else f"{m:.3f} m"
    return inches(m) if units == "in" else ftin(m)


def fmt(kind: str, v: float, units: str) -> str:
    met = units == "m"
    k = kind.lower()
    if k == "m":
        return length(v, units)
    if k == "m2":
        return f"{v:.{3 if v < 10 else 1}f} m²" if met else f"{v * 10.7639:.{2 if v < 1 else 1}f} ft²"
    if k == "l":
        return f"{round(v):,} L" if met else f"{round(v / 3.78541):,} gal"
    if k == "kg":
        return f"{round(v):,} kg" if met else f"{round(v * 2.20462):,} lb"
    if k == "kpa":
        return f"{v:.1f} kPa" if met else f"{v * 0.145038:.2f} psi"
    if k == "mpa":
        return f"{v:.1f} MPa" if met else f"{v * 0.145038:.2f} ksi"
    if k == "deg":
        return f"{v:.1f}°"
    return f"{v:g}"


TOKEN = re.compile(r"\{(m|m2|L|kg|kPa|MPa|deg):(-?[0-9.]+(?:e[-+]?[0-9]+)?)\}", re.I)


def tokens(text, units: str = "ftin") -> str:
    return TOKEN.sub(lambda mt: fmt(mt.group(1), float(mt.group(2)), units), str(text if text is not None else ""))


def ascii_text(s: str) -> str:
    """DXF R12 text: plain ASCII (degrees spelled out, feet and inches kept)."""
    s = s.replace("°", " deg").replace("²", "2").replace("³", "3").replace("×", "x").replace("–", "-").replace("—", "-")
    return s.encode("ascii", "replace").decode("ascii")


def slug(s: str) -> str:
    return re.sub(r"[^a-z0-9]+", "-", str(s).lower()).strip("-") or "dome"


# ----------------------------------------------------------------------
# DXF (R12)
# ----------------------------------------------------------------------

LAYERS = {"CUT": 7, "SHEET": 8, "ETCH": 3, "BEVEL": 5, "NOTES": 1, "OUTLINE": 4}


class Dxf:
    def __init__(self, units: str):
        self.k = 1000.0 if units == "mm" else 1 / IN       # metres -> file units
        self.units = units
        self.ents: list[str] = []

    def _p(self, code, value) -> None:
        self.ents.append(f"{code}\n{value}")

    def _xy(self, x: float, y: float, base: int = 10) -> None:
        self._p(base, f"{x * self.k:.5f}")
        self._p(base + 10, f"{y * self.k:.5f}")
        self._p(base + 20, "0.0")

    def poly(self, pts, layer: str, closed: bool = True) -> None:
        self._p(0, "POLYLINE"); self._p(8, layer); self._p(66, 1); self._p(70, 1 if closed else 0); self._xy(0, 0)
        for x, y in pts:
            self._p(0, "VERTEX"); self._p(8, layer); self._xy(x, y)
        self._p(0, "SEQEND"); self._p(8, layer)

    def line(self, a, b, layer: str) -> None:
        self._p(0, "LINE"); self._p(8, layer); self._xy(*a); self._xy(*b, base=11)

    def circle(self, c, r: float, layer: str) -> None:
        self._p(0, "CIRCLE"); self._p(8, layer); self._xy(*c); self._p(40, f"{r * self.k:.5f}")

    def text(self, at, s: str, h: float, layer: str = "NOTES", centre: bool = False, rot: float = 0.0) -> None:
        self._p(0, "TEXT"); self._p(8, layer); self._xy(*at); self._p(40, f"{h * self.k:.5f}"); self._p(1, ascii_text(s))
        if rot:
            self._p(50, f"{rot:.3f}")
        if centre:
            self._p(72, 1); self._p(73, 2); self._xy(*at, base=11)

    def dumps(self) -> str:
        head = ["0", "SECTION", "2", "HEADER", "9", "$ACADVER", "1", "AC1009", "9", "$INSUNITS", "70", "4" if self.units == "mm" else "1",
                "9", "$MEASUREMENT", "70", "1" if self.units == "mm" else "0", "0", "ENDSEC",
                "0", "SECTION", "2", "TABLES",
                "0", "TABLE", "2", "LTYPE", "70", "1", "0", "LTYPE", "2", "CONTINUOUS", "70", "0", "3", "Solid line", "72", "65", "73", "0", "40", "0.0",
                "0", "ENDTAB", "0", "TABLE", "2", "LAYER", "70", str(len(LAYERS))]
        for name, col in LAYERS.items():
            head += ["0", "LAYER", "2", name, "70", "0", "62", str(col), "6", "CONTINUOUS"]
        head += ["0", "ENDTAB", "0", "ENDSEC", "0", "SECTION", "2", "ENTITIES"]
        return "\n".join(head + self.ents + ["0", "ENDSEC", "0", "EOF", ""])


def _bbox(pts):
    xs, ys = [p[0] for p in pts], [p[1] for p in pts]
    return min(xs), min(ys), max(xs), max(ys)


def _shift(pts, dx, dy):
    return [(x + dx, y + dy) for x, y in pts]


def _edge_bevels(card: dict) -> list[tuple[float, float]]:
    """(edge length, bevel) for a plate card, read from its drawing's dims and its bevel notes (same order)."""
    d = card.get("draw") or {}
    bev = [float(mt.group(1)) for n in d.get("notes", []) for mt in [re.search(r"bevel \{deg:(-?[0-9.e+-]+)\}", n.get("text", ""))] if mt]
    lens = [float(x["m"]) for x in d.get("dims", [])]
    return list(zip(lens, bev)) if len(bev) == len(lens) else []


def _inward_offset(a, b, c, dist):
    """A point beside edge ab's midpoint, toward the polygon's centre c."""
    mx, my = (a[0] + b[0]) / 2, (a[1] + b[1]) / 2
    dx, dy = c[0] - mx, c[1] - my
    ln = math.hypot(dx, dy) or 1.0
    return mx + dx / ln * dist, my + dy / ln * dist


def dxf(scene: dict, units: str = "in") -> str:
    """The cutting file: nested sheets and loose parts on CUT, reference drawings on OUTLINE."""
    t = scene["tables"]
    cards = t.get("cards") or []
    sheets = t.get("sheets") or []
    D = Dxf("mm" if units in ("mm", "m") else "in")
    fmt_u = "m" if D.units == "mm" else "in"
    gap = 0.15
    steel = t.get("kind") in ("stove", "tank")
    bevels = {c["mark"]: _edge_bevels(c) for c in cards if c.get("kind") == "plate"}
    nested = {p["mark"] for s in sheets for p in s["parts"]}
    title_h = 0.04

    # nested sheets, four to a row, rows going down
    per_row = 4
    sw = max((float(s["w"]) for s in sheets), default=0.0)
    shh = max((float(s["h"]) for s in sheets), default=0.0)
    for i, s in enumerate(sheets):
        w, h = float(s["w"]), float(s["h"])
        x0 = (i % per_row) * (sw + gap)
        y0 = -(i // per_row) * (shh + 0.2)
        D.poly([(x0, y0), (x0 + w, y0), (x0 + w, y0 + h), (x0, y0 + h)], "SHEET")
        D.text((x0, y0 + h + 0.02), f"Sheet {i + 1} of {len(sheets)}: {length(w, fmt_u)} x {length(h, fmt_u)}", title_h, "NOTES")
        for part in s["parts"]:
            pts = _shift([tuple(map(float, p)) for p in part["pts"]], x0, y0)
            D.poly(pts, "CUT")
            cx, cy = sum(p[0] for p in pts) / len(pts), sum(p[1] for p in pts) / len(pts)
            size = max(_bbox(pts)[2] - _bbox(pts)[0], _bbox(pts)[3] - _bbox(pts)[1])
            D.text((cx, cy), part["mark"], max(0.012, size * 0.06), "ETCH", centre=True)
            eb = bevels.get(part["mark"]) or []
            own = part.get("bevels") or []          # each edge's own bevel, in the outline's order
            for j in range(len(pts)):
                a, b = pts[j], pts[(j + 1) % len(pts)]
                L = math.hypot(b[0] - a[0], b[1] - a[1])
                hits = [round(own[j], 2)] if len(own) == len(pts) else sorted({round(bv, 2) for ln, bv in eb if abs(ln - L) < 1e-4})
                if hits:
                    D.text(_inward_offset(a, b, (cx, cy), size * 0.12), "bevel " + " / ".join(f"{x:.1f}" for x in hits), max(0.008, size * 0.035), "NOTES",
                           centre=True, rot=math.degrees(math.atan2(b[1] - a[1], b[0] - a[0])) % 180)

    # every family once, to scale: loose steel parts (cap, floor) go on CUT, count times; the rest is reference
    row_w = max(min(len(sheets), per_row) * (sw + gap) - gap, 2.5)
    y = -((len(sheets) - 1) // per_row) * (shh + 0.2) - 0.35 if sheets else -0.35
    x, row_h = 0.0, 0.0
    for c in cards:
        d = c.get("draw")
        if not d or not d.get("poly"):
            continue
        poly = [tuple(map(float, p)) for p in d["poly"]]
        bx0, by0, bx1, by1 = _bbox(poly)
        w, h = bx1 - bx0, by1 - by0
        size = max(w, h, 0.05)
        th = min(max(0.012, size * 0.045), 0.035)
        # the drawing's notes and guide lines stand above and below it: the label goes over all of them
        ext = [p_[1] for p_ in poly] + [float(nt["at"][1]) for nt in d.get("notes", [])] + [float(q[1]) for ln_ in d.get("lines", []) for q in ln_]
        top = max(ext) + th * 1.2
        bottom = min(ext) - th * 2.2
        loose = steel and c.get("kind") == "plate" and c["mark"] not in nested
        copies = max(1, int(c.get("count", 1))) if loose else 1
        head = f"{c['mark']}  x{c['count']}  {tokens(c['title'], fmt_u)}" + ("" if loose else "  (reference: do not cut)")
        for k in range(copies):
            # wide enough for the drawing and for its label (text runs about 0.62 of its height a character)
            notes_w = max((float(nt["at"][0]) - bx0 + len(tokens(nt.get("text", ""), fmt_u)) * th * 0.85 * 0.75 for nt in d.get("notes", [])), default=0.0)
            cw = max(w + 0.35 * size + 0.1, len(head) * th * 1.15 * 0.75 + 0.08, notes_w + 0.08)
            if x + cw > row_w and x > 0:
                y -= row_h + 0.25
                x, row_h = 0.0, 0.0
            dx, dy = x - bx0, y - top
            pts = _shift(poly, dx, dy)
            D.poly(pts, "CUT" if loose else "OUTLINE")
            if d.get("inner"):
                D.poly(_shift([tuple(map(float, p)) for p in d["inner"]], dx, dy), "BEVEL")
            for hole in d.get("holes", []):
                at = hole.get("at") or hole.get("c") or [0, 0]
                D.circle((float(at[0]) + dx, float(at[1]) + dy), float(hole.get("r", 0.0)), "CUT" if loose else "OUTLINE")
            for a, b in d.get("lines", []):
                D.line((a[0] + dx, a[1] + dy), (b[0] + dx, b[1] + dy), "NOTES")
            D.text((x, y + 0.03), head if k == 0 else f"{c['mark']} ({k + 1} of {copies})", th * 1.15, "ETCH" if loose else "NOTES")
            if k == 0:
                for dm in d.get("dims", []):
                    a, b = dm["a"], dm["b"]
                    mid = ((a[0] + b[0]) / 2 + dx, (a[1] + b[1]) / 2 + dy - th * 1.6)
                    D.text(mid, length(float(dm["m"]), fmt_u), th, "NOTES", centre=True,
                           rot=math.degrees(math.atan2(b[1] - a[1], b[0] - a[0])) % 180)
                for ang in d.get("angles", []):
                    D.text((ang["at"][0] + dx, ang["at"][1] + dy), f"{float(ang['deg']):.1f} deg", th * 0.85, "NOTES")
                for nt in d.get("notes", []):
                    D.text((nt["at"][0] + dx, nt["at"][1] + dy), tokens(nt.get("text", ""), fmt_u), th * 0.85, "NOTES")
            x += cw
            row_h = max(row_h, top - bottom + 0.1)
    D.text((0, y - row_h - 0.2), f"{t.get('title', 'Dome')} -- Dome Sketch ({TAG}). Units: {'millimetres' if D.units == 'mm' else 'inches'}. "
           "CUT is cut once each; OUTLINE is a reference drawing; true size, add your kerf.", 0.03, "NOTES")
    return D.dumps()


def read_dxf(text: str) -> dict:
    """A small reader for the DXF this module writes: closed polylines by layer, circles, texts."""
    lines = text.splitlines()
    pairs = [(lines[i].strip(), lines[i + 1]) for i in range(0, len(lines) - 1, 2)]
    out = {"polys": {}, "circles": {}, "texts": [], "units": None}
    cur, layer, verts = None, None, []
    for i, (code, val) in enumerate(pairs):
        if code == "9" and val == "$INSUNITS":
            out["units"] = int(pairs[i + 1][1])
        if code == "0":
            if cur == "POLYLINE" and val == "SEQEND":
                out["polys"].setdefault(layer, []).append(verts)
                cur = None
                continue
            if val == "POLYLINE":
                cur, verts, layer = "POLYLINE", [], None
            elif val == "VERTEX" and cur == "POLYLINE":
                verts.append([None, None])
            elif val in ("CIRCLE", "TEXT", "LINE"):
                cur = val
                if val == "TEXT":
                    out["texts"].append("")
            elif cur != "POLYLINE":
                cur = None
            continue
        if code == "8" and cur == "POLYLINE" and layer is None:
            layer = val
        if cur == "POLYLINE" and verts and code in ("10", "20"):
            verts[-1][0 if code == "10" else 1] = float(val)
        if cur == "CIRCLE" and code == "8":
            out["circles"][val] = out["circles"].get(val, 0) + 1
        if cur == "TEXT" and code == "1":
            out["texts"][-1] = val
    return out


# ----------------------------------------------------------------------
# CSV
# ----------------------------------------------------------------------

def cutlist_csv(scene: dict, units: str = "ftin") -> str:
    cards = scene["tables"].get("cards") or []
    labels: list[str] = []
    for c in cards:
        for k, _v in c["rows"]:
            if k not in labels:
                labels.append(k)
    buf = io.StringIO()
    w = csv.writer(buf, lineterminator="\n")
    w.writerow(["Mark", "Item", "Quantity", "Group", "Kind"] + labels)
    for c in cards:
        row = dict(c["rows"])
        w.writerow([c["mark"], tokens(c["title"], units), c["count"], c.get("group", ""), c.get("kind", "")] + [tokens(row.get(k, ""), units) for k in labels])
    w.writerow([])
    w.writerow(["", f"{scene['tables'].get('title', '')}: {len(cards)} cut families", sum(int(c['count']) for c in cards)])
    return buf.getvalue()


def materials_csv(scene: dict, units: str = "ftin") -> str:
    mt = scene["tables"].get("materials")
    buf = io.StringIO()
    w = csv.writer(buf, lineterminator="\n")
    if not mt:
        w.writerow(["No materials table for this design."])
        return buf.getvalue()
    prices = {p["key"]: p for p in mt["prices"]}
    w.writerow(["Item", "Quantity", "Counted from", "Price used (estimate)", "Per", "Cost, USD (estimate)"])
    for r in mt["rows"]:
        p = prices.get(r["price"]) or {}
        w.writerow([tokens(r["item"], units), tokens(r["qty_text"], units), tokens(r["from"], units),
                    f"{p.get('usd', 0):.2f}" if p else "", p.get("per", ""), f"{r['usd']:.2f}" if r.get("usd") is not None else ""])
    w.writerow(["Total, materials (estimate)", "", "", "", "", f"{mt['total']:.2f}"])
    w.writerow([])
    w.writerow(["Declared prices", "USD", "Per", "Kind", "Why", "From"])
    for p in mt["prices"]:
        w.writerow([p["label"], f"{p['usd']:.2f}", p["per"], p["kind"], p["why"], p["source"]])
    w.writerow([])
    w.writerow([mt["note"]])
    return buf.getvalue()


# ----------------------------------------------------------------------
# Meshes: OBJ, STL, glTF
# ----------------------------------------------------------------------

def built(scene: dict) -> list[dict]:
    """The pieces that are built (not the ground, a room's walls or the people), with their meshes."""
    out = []
    for p in scene["pieces"]:
        if p["tag"] in ("site", "person", "clear") or p["step"] < 0:
            continue
        v = np.frombuffer(base64.b64decode(p["v"]), "<f4").reshape(-1, 3).astype(float)
        t = np.frombuffer(base64.b64decode(p["t"]), "<u4").reshape(-1, 3).astype(np.int64)
        if len(t):
            out.append({"id": p["id"], "name": p["name"], "material": p["material"], "tag": p["tag"], "v": v, "t": t})
    return out


def _yup(v: np.ndarray) -> np.ndarray:
    return np.column_stack([v[:, 0], v[:, 2], -v[:, 1]])


def _rgb(hexcol: str) -> tuple[float, float, float]:
    h = hexcol.lstrip("#")
    return tuple(int(h[i:i + 2], 16) / 255 for i in (0, 2, 4))


def obj(scene: dict, name: str = "dome") -> tuple[str, str]:
    mats = scene.get("materials") or {}
    o = [f"# {scene['tables'].get('title', 'Dome')} -- Dome Sketch ({TAG}). Metres, Y up.", f"mtllib {name}.mtl"]
    base = 1
    used = []
    for p in built(scene):
        o.append(f"o {re.sub(r'[^A-Za-z0-9_.-]+', '_', p['id'])}")
        o.append(f"usemtl {p['material']}")
        if p["material"] not in used:
            used.append(p["material"])
        o += [f"v {x:.6f} {y:.6f} {z:.6f}" for x, y, z in _yup(p["v"])]
        o += [f"f {a + base} {b + base} {c + base}" for a, b, c in p["t"]]
        base += len(p["v"])
    mtl = [f"# materials for {name}.obj"]
    for k in used:
        m = mats.get(k, {})
        r, g, b = _rgb(m.get("color", "#cccccc"))
        mtl += [f"newmtl {k}", f"Kd {r:.4f} {g:.4f} {b:.4f}", f"d {float(m.get('opacity', 1)):.3f}", "illum 1", ""]
    return "\n".join(o) + "\n", "\n".join(mtl)


def stl(scene: dict) -> bytes:
    """Binary STL in millimetres, Z up: every built piece."""
    tris = []
    for p in built(scene):
        tris.append(p["v"][p["t"]] * 1000.0)
    T = np.concatenate(tris) if tris else np.zeros((0, 3, 3))
    n = np.cross(T[:, 1] - T[:, 0], T[:, 2] - T[:, 0])
    ln = np.linalg.norm(n, axis=1, keepdims=True)
    n = np.divide(n, ln, out=np.zeros_like(n), where=ln > 1e-15)
    head = f"Dome Sketch {TAG}: {scene['tables'].get('title', '')} (mm, Z up)".encode("ascii", "replace")[:80].ljust(80, b" ")
    rec = np.zeros(len(T), dtype=[("n", "<f4", 3), ("v", "<f4", (3, 3)), ("a", "<u2")])
    rec["n"], rec["v"] = n, T
    return head + struct.pack("<I", len(T)) + rec.tobytes()


def glb(scene: dict) -> bytes:
    """glTF 2.0 binary: one node per built piece, a material per Dome Sketch material. Metres, Y up."""
    mats = scene.get("materials") or {}
    bin_ = bytearray()
    views, accs, meshes, nodes, mat_ix, materials = [], [], [], [], {}, []

    def view(data: bytes, target: int) -> int:
        while len(bin_) % 4:
            bin_.append(0)
        views.append({"buffer": 0, "byteOffset": len(bin_), "byteLength": len(data), "target": target})
        bin_.extend(data)
        return len(views) - 1

    for p in built(scene):
        if p["material"] not in mat_ix:
            m = mats.get(p["material"], {})
            r, g, b = _rgb(m.get("color", "#cccccc"))
            a = float(m.get("opacity", 1.0))
            steel = "steel" in p["material"]
            mat = {"name": p["material"], "doubleSided": True,
                   "pbrMetallicRoughness": {"baseColorFactor": [r, g, b, a], "metallicFactor": 0.6 if steel else 0.0, "roughnessFactor": 0.7}}
            if a < 1:
                mat["alphaMode"] = "BLEND"
            mat_ix[p["material"]] = len(materials)
            materials.append(mat)
        v = _yup(p["v"]).astype("<f4")
        t = p["t"].astype("<u4")
        pv = view(v.tobytes(), 34962)
        accs.append({"bufferView": pv, "componentType": 5126, "count": len(v), "type": "VEC3",
                     "min": [float(x) for x in v.min(axis=0)], "max": [float(x) for x in v.max(axis=0)]})
        ti = view(t.tobytes(), 34963)
        accs.append({"bufferView": ti, "componentType": 5125, "count": int(t.size), "type": "SCALAR"})
        meshes.append({"name": p["name"], "primitives": [{"attributes": {"POSITION": len(accs) - 2}, "indices": len(accs) - 1,
                                                          "material": mat_ix[p["material"]], "mode": 4}]})
        nodes.append({"name": p["id"], "mesh": len(meshes) - 1})
    while len(bin_) % 4:
        bin_.append(0)
    doc = {"asset": {"version": "2.0", "generator": f"Dome Sketch ({TAG})"},
           "scene": 0, "scenes": [{"name": scene["tables"].get("title", "Dome"), "nodes": list(range(len(nodes)))}],
           "nodes": nodes, "meshes": meshes, "materials": materials, "accessors": accs, "bufferViews": views,
           "buffers": [{"byteLength": len(bin_)}]}
    js = json.dumps(doc, separators=(",", ":")).encode("utf-8")
    js += b" " * (-len(js) % 4)
    total = 12 + 8 + len(js) + 8 + len(bin_)
    return (struct.pack("<III", 0x46546C67, 2, total) + struct.pack("<II", len(js), 0x4E4F534A) + js
            + struct.pack("<II", len(bin_), 0x004E4942) + bytes(bin_))


def read_glb(data: bytes) -> dict:
    magic, ver, total = struct.unpack_from("<III", data, 0)
    assert magic == 0x46546C67 and ver == 2 and total == len(data), "not a glTF 2.0 binary"
    jl, jt = struct.unpack_from("<II", data, 12)
    assert jt == 0x4E4F534A
    doc = json.loads(data[20:20 + jl])
    bl, bt = struct.unpack_from("<II", data, 20 + jl)
    assert bt == 0x004E4942 and bl == doc["buffers"][0]["byteLength"]
    for v in doc["bufferViews"]:
        assert v["byteOffset"] + v["byteLength"] <= bl
    return doc


# ----------------------------------------------------------------------
# All of it
# ----------------------------------------------------------------------

def design_json(scene: dict) -> str:
    spec = scene["spec"]
    return json.dumps({"made_by": f"Dome Sketch ({TAG})", "title": scene["tables"].get("title", ""), "spec": spec,
                       "open": "/?spec=" + json.dumps(spec, separators=(",", ":"))}, indent=1, ensure_ascii=False)


def readme(scene: dict, name: str) -> str:
    t = scene["tables"]
    lines = [f"# {t.get('title', 'Dome')}", "", f"Made in Dome Sketch ({TAG}) from this design's own solved model.", "",
             "| File | What it is |", "|---|---|",
             f"| {name}-in.dxf, {name}-mm.dxf | Cut outlines in inches and in millimetres. Layer CUT is what gets cut, once each; "
             "SHEET is the sheet's edge; ETCH the part marks; NOTES the bevels and dimensions; OUTLINE a reference drawing of every "
             "cut family, never to be cut. True size: your CAM program adds the kerf. |",
             f"| {name}-cutlist-imperial.csv, {name}-cutlist-metric.csv | One row per cut family: how many, and every figure on its card. |",
             f"| {name}-materials.csv | Quantities counted from the design, the declared prices used, and the estimated cost. |",
             f"| {name}.obj + {name}.mtl | The assembled model, metres, Y up. |",
             f"| {name}.stl | The assembled model, millimetres, Z up. |",
             f"| {name}.glb | The assembled model as glTF 2.0, metres, Y up, one node per piece. |",
             "| design.json | The design itself: open it again in Dome Sketch with the link inside. |", "",
             "## The design", ""]
    lines += [f"* {k}: {tokens(v, 'ftin')} ({tokens(v, 'm')})" for k, v in t.get("summary", [])]
    if t.get("warnings"):
        lines += ["", "## Warnings", ""] + [f"* {tokens(w, 'ftin')}" for w in t["warnings"]]
    mt = t.get("materials")
    if mt:
        lines += ["", f"Materials, estimated: ${mt['total']:,.0f}. {mt['note']}"]
    return "\n".join(lines) + "\n"


def bundle(scene: dict) -> dict[str, bytes]:
    name = slug(scene["tables"].get("title", "dome"))
    o, mtl = obj(scene, name)
    return {
        "README.md": readme(scene, name).encode("utf-8"),
        f"{name}-in.dxf": dxf(scene, "in").encode("ascii"),
        f"{name}-mm.dxf": dxf(scene, "mm").encode("ascii"),
        f"{name}-cutlist-imperial.csv": cutlist_csv(scene, "ftin").encode("utf-8-sig"),
        f"{name}-cutlist-metric.csv": cutlist_csv(scene, "m").encode("utf-8-sig"),
        f"{name}-materials.csv": materials_csv(scene, "ftin").encode("utf-8-sig"),
        f"{name}.obj": o.encode("utf-8"),
        f"{name}.mtl": mtl.encode("utf-8"),
        f"{name}.stl": stl(scene),
        f"{name}.glb": glb(scene),
        "design.json": design_json(scene).encode("utf-8"),
    }


def zip_bytes(files: dict[str, bytes]) -> bytes:
    buf = io.BytesIO()
    with zipfile.ZipFile(buf, "w", zipfile.ZIP_DEFLATED) as z:
        for k, v in files.items():
            z.writestr(k, v)
    return buf.getvalue()


def one(scene: dict, fmt_: str, units: str = "ftin") -> tuple[str, str, bytes]:
    """(filename, content type, bytes) for one export, in the viewer's units."""
    if fmt_ not in FORMATS:
        raise ValueError(f"no such export: {fmt_}")
    name = slug(scene["tables"].get("title", "dome"))
    ctype, suffix, _label = FORMATS[fmt_]
    if fmt_ == "dxf":
        u = "mm" if units == "m" else "in"
        return f"{name}-{u}.dxf", ctype, dxf(scene, u).encode("ascii")
    if fmt_ == "csv":
        return f"{name}-cutlist.csv", ctype, cutlist_csv(scene, units).encode("utf-8-sig")
    if fmt_ == "materials":
        return f"{name}-materials.csv", ctype, materials_csv(scene, units).encode("utf-8-sig")
    if fmt_ == "obj":
        o, mtl = obj(scene, name)
        return f"{name}-obj.zip", ctype, zip_bytes({f"{name}.obj": o.encode(), f"{name}.mtl": mtl.encode()})
    if fmt_ == "stl":
        return f"{name}.stl", ctype, stl(scene)
    if fmt_ == "glb":
        return f"{name}.glb", ctype, glb(scene)
    return f"{name}-fabrication.zip", ctype, zip_bytes(bundle(scene))


def write_pack(spec: dict) -> dict:
    """Every export for this design, in a new numbered folder in deliverables/ (never an old one)."""
    import medialib

    from . import kinds as KD
    sc = KD.scene(spec)
    files = bundle(sc)
    folder, _version = medialib.new_output(f"{TAG}-fabrication-{sc['tables']['kind']}-{slug(sc['tables'].get('title', 'dome'))}")
    for k, v in files.items():
        (folder / k).write_bytes(v)
    return {"folder": folder.as_posix(), "files": sorted(files)}


# ----------------------------------------------------------------------
# Checks
# ----------------------------------------------------------------------

def validate_exports(scene: dict) -> list[str]:
    """Each export read back and held against the scene it came from."""
    t = scene["tables"]
    cards = t.get("cards") or []
    notes = []
    parts = built(scene)
    ntri = sum(len(p["t"]) for p in parts)

    for u, k in (("in", 1 / IN), ("mm", 1000.0)):
        r = read_dxf(dxf(scene, u))
        assert r["units"] == (1 if u == "in" else 4), r["units"]
        cut = r["polys"].get("CUT", [])
        sheet_parts = sum(len(s["parts"]) for s in t.get("sheets") or [])
        if t.get("kind") in ("stove", "tank"):
            nested = {p["mark"] for s in t["sheets"] for p in s["parts"]}
            loose = sum(int(c["count"]) for c in cards if c.get("kind") == "plate" and c["mark"] not in nested)
            plates = sum(int(c["count"]) for c in cards if c.get("kind") == "plate")
            assert len(cut) == sheet_parts + loose == plates, (len(cut), sheet_parts, loose, plates)
            # every nested plate keeps its card's edge lengths, to the file's precision
            by = {c["mark"]: sorted(float(d["m"]) for d in c["draw"]["dims"]) for c in cards if c.get("kind") == "plate" and c.get("draw")}
            sheets_seen = 0
            for s in t["sheets"]:
                for part in s["parts"]:
                    pts = part["pts"]
                    L = sorted(math.dist(pts[i], pts[(i + 1) % len(pts)]) for i in range(len(pts)))
                    assert all(abs(a - b) < 1e-6 for a, b in zip(L, by[part["mark"]])), (part["mark"], L, by[part["mark"]])
                    sheets_seen += 1
            for poly in cut[:sheet_parts]:
                assert all(x is not None and y is not None for x, y in poly)
            bevel_texts = [x for x in r["texts"] if x.startswith("bevel ")]
            assert len(bevel_texts) >= sheet_parts * 2, len(bevel_texts)
        else:
            assert len(cut) == sheet_parts, (len(cut), sheet_parts)
        outline = r["polys"].get("OUTLINE", [])
        nested = {p["mark"] for s in t.get("sheets") or [] for p in s["parts"]}
        ref = [c for c in cards if c.get("draw") and c["draw"].get("poly")
               and not (t.get("kind") in ("stove", "tank") and c.get("kind") == "plate" and c["mark"] not in nested)]
        assert len(outline) == len(ref), (len(outline), len(ref))
        # every reference drawing, read back from the file, is its card's outline to scale
        for got_poly, c in zip(outline, ref):
            want_poly = c["draw"]["poly"]
            got = sorted(math.dist(got_poly[i], got_poly[(i + 1) % len(got_poly)]) / k for i in range(len(got_poly)))
            want = sorted(math.dist(want_poly[i], want_poly[(i + 1) % len(want_poly)]) for i in range(len(want_poly)))
            assert len(got) == len(want) and all(abs(a - b) < 1e-4 for a, b in zip(got, want)), (c["mark"], got, want)
    notes.append(f"DXF: {sum(len(s['parts']) for s in t.get('sheets') or [])} nested parts, {len(cards)} families, true size in inches and mm")

    rows = list(csv.reader(io.StringIO(cutlist_csv(scene, "ftin"))))
    body = [r for r in rows[1:] if r and r[0]]
    assert [r[0] for r in body] == [c["mark"] for c in cards]
    assert all(int(r[2]) == int(c["count"]) for r, c in zip(body, cards))
    assert "{" not in "".join(",".join(r) for r in rows), "an unformatted unit token in the CSV"
    notes.append(f"CSV cut list: {len(body)} families, counts equal the cards")

    if t.get("materials"):
        mrows = list(csv.reader(io.StringIO(materials_csv(scene, "ftin"))))
        tot = next(r for r in mrows if r and r[0].startswith("Total"))
        assert abs(float(tot[-1]) - t["materials"]["total"]) < 0.01
        notes.append(f"materials CSV: total ${t['materials']['total']:,.2f}")

    o, _mtl = obj(scene)
    nv = sum(1 for ln in o.splitlines() if ln.startswith("v "))
    nf = sum(1 for ln in o.splitlines() if ln.startswith("f "))
    assert nv == sum(len(p["v"]) for p in parts) and nf == ntri, (nv, nf)
    s = stl(scene)
    assert struct.unpack_from("<I", s, 80)[0] == ntri and len(s) == 84 + 50 * ntri
    doc = read_glb(glb(scene))
    assert len(doc["nodes"]) == len(parts)
    assert sum(a["count"] for a in doc["accessors"] if a["type"] == "SCALAR") == 3 * ntri
    # the glTF is Y up and in metres: its height is the model's z extent
    if parts:
        zmax = max(float(p["v"][:, 2].max()) for p in parts)
        ymax = max(a["max"][1] for a in doc["accessors"] if a["type"] == "VEC3")
        assert abs(zmax - ymax) < 1e-4, (zmax, ymax)
    notes.append(f"OBJ/STL/glTF: {len(parts)} pieces, {ntri:,} triangles each")
    z = zipfile.ZipFile(io.BytesIO(zip_bytes(bundle(scene))))
    assert z.testzip() is None and len(z.namelist()) == 11
    notes.append("zip: 11 files, readable")
    return notes
