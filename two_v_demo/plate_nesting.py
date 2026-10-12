"""How many of a dome's panels fit on one sheet of plate -- nested, then checked.

A 120 by 60 inch sheet is the plasma table's whole bed, so the shop's first
question is: what is the largest two-frequency shell whose forty panels can be
cut from one sheet, and what does that shell become when it is welded up? The
second is how many sheets a bigger dome takes.

The panels come from the solver (:func:`two_v_demo.geometry.build_demo_geometry`
for the 2V hemisphere, :mod:`two_v_demo.panel_method` for the 3V 5/8), not from
copied chord factors. They are nested the way a person with a soapstone and a
straight edge would: in **strips** of triangles pointing alternately up and
down, which tile with nothing between them but the cutting gap. Every
placement is *slid* until the real distance between neighbouring parts equals
the declared gap, and the finished layout is then verified part by part --
inside the margins, and no two parts closer than the gap -- so a "fits" here is
a checked claim, not an estimate.

Two ways to call a panel cut:

``strict``   every panel whole, exactly as the geometry draws it;
``trimmed``  each panel's point cut back a little (at most :data:`MAX_TRIM_IN`),
             with a small round cap welded over every dome vertex to close the
             hole the trimmed points leave. This is "almost fits, with some
             cut off": it buys a bigger vessel from the same sheet, and the
             module reports exactly what it costs in caps and weld.

The 2023 version of this module paired triangles into parallelograms, used the
2V chord factors for a 3V dome, said a 3V dome had five strut classes (it has
three), took floor and volume from a sphere rather than the faceted shell, and
counted weld as five long sides per panel. Those are corrected here.
"""

from __future__ import annotations

import math
from dataclasses import dataclass, field
from functools import lru_cache

import numpy as np

# ----------------------------------------------------------------------
# Declared inputs
# ----------------------------------------------------------------------

#: The sheet, inches, as the shop buys it -- and the table's bed.
SHEET_W_IN = 120.0
SHEET_H_IN = 60.0
#: Plasma kerf, and the clear gap left between parts so the torch never fuses
#: two of them. Allowances: measure your own torch on scrap.
KERF_IN = 0.0625
PART_GAP_IN = 0.25
#: Plate edge kept clear of parts (clamps, a mill edge that is never square).
EDGE_MARGIN_IN = 0.5
#: Mild steel.
STEEL_LB_PER_IN3 = 0.2836
#: The most a panel's point may be trimmed in "trimmed" mode, measured along
#: the panel's height. Past this the vertex caps stop being small.
MAX_TRIM_IN = 1.5
#: Hand welding speed for a thin butt seam, and plasma cutting speed in thin
#: mild steel: allowances, not measurements -- read your machine's chart.
WELD_IN_PER_MIN = 8.0
CUT_IN_PER_MIN = 90.0
#: Gallons per cubic foot.
GAL_PER_FT3 = 7.48052


# ----------------------------------------------------------------------
# Panels, from the solver
# ----------------------------------------------------------------------

@dataclass(frozen=True)
class Shape:
    """One panel kind as it is laid on the sheet: base on the x axis from
    (0, 0) to (base, 0), point at (apex_x, height)."""

    key: str
    base: float
    apex_x: float
    height: float
    count: int

    @property
    def area(self) -> float:
        return self.base * self.height / 2

    def polygon(self, trim: float = 0.0) -> list[tuple[float, float]]:
        """The outline, its point cut back ``trim`` along the height."""
        if trim <= 0:
            return [(0.0, 0.0), (self.base, 0.0), (self.apex_x, self.height)]
        t = trim / self.height
        h = self.height - trim
        left = (self.apex_x * (1 - t), h)
        right = (self.base + (self.apex_x - self.base) * (1 - t), h)
        return [(0.0, 0.0), (self.base, 0.0), right, left]

    def trim_width(self, trim: float) -> float:
        """How wide the cut-off point is: the cap must cover at least this."""
        return self.base * trim / self.height


def _triangle_shape(key: str, a: float, b: float, c: float, count: int) -> Shape:
    """Sides a (base), b, c -> a Shape, base on the axis."""
    x = (b * b - c * c + a * a) / (2 * a)
    return Shape(key, a, x, math.sqrt(max(b * b - x * x, 0.0)), count)


@lru_cache(maxsize=1)
def _two_v():
    from .geometry import build_demo_geometry

    return build_demo_geometry()


def two_v_shapes(radius_in: float) -> tuple[Shape, ...]:
    """The 2V hemisphere's panels at a sphere radius, counted from its faces."""
    g = _two_v()
    v = np.asarray(g.vertices, dtype=float) * radius_in
    kinds: dict[tuple, int] = {}
    for f in g.hemisphere_faces:
        sides = sorted(round(float(np.linalg.norm(v[f[k]] - v[f[(k + 1) % 3]])), 9) for k in range(3))
        kinds[tuple(sides)] = kinds.get(tuple(sides), 0) + 1
    out = []
    for sides, n in sorted(kinds.items()):
        short, mid, long = sides
        if abs(short - long) < 1e-6:
            out.append(_triangle_shape("equilateral", long, long, long, n))
        else:
            # the odd side is the base
            base = long if abs(short - mid) < 1e-6 else short
            leg = short if base == long else long
            out.append(_triangle_shape("isosceles", base, leg, leg, n))
    return tuple(sorted(out, key=lambda s: -s.height))


@dataclass(frozen=True)
class PanelSet:
    """One 2V hemisphere's panels at a given sphere radius."""

    radius_in: float
    shapes: tuple[Shape, ...]

    @property
    def panels(self) -> int:
        return sum(s.count for s in self.shapes)

    @property
    def area(self) -> float:
        return sum(s.count * s.area for s in self.shapes)

    def shape(self, key: str) -> Shape:
        return next(s for s in self.shapes if s.key == key)

    @property
    def long_in(self) -> float:
        return self.shape("equilateral").base

    @property
    def short_in(self) -> float:
        iso = self.shape("isosceles")
        return math.hypot(iso.apex_x, iso.height)

    @property
    def diameter_in(self) -> float:
        return 2 * self.radius_in

    @property
    def diameter_ft(self) -> float:
        return self.diameter_in / 12


def panel_set(radius_in: float) -> PanelSet:
    return PanelSet(radius_in, two_v_shapes(radius_in))


# ----------------------------------------------------------------------
# Geometry of the cut: convex polygons, distances
# ----------------------------------------------------------------------

def _seg_point(p, a, b) -> float:
    ax, ay = a
    bx, by = b
    px, py = p
    dx, dy = bx - ax, by - ay
    L = dx * dx + dy * dy
    t = 0.0 if L == 0 else max(0.0, min(1.0, ((px - ax) * dx + (py - ay) * dy) / L))
    return math.hypot(px - ax - t * dx, py - ay - t * dy)


def _overlap(p, q) -> bool:
    """Separating-axis test for two convex polygons."""
    for poly in (p, q):
        n = len(poly)
        for i in range(n):
            x1, y1 = poly[i]
            x2, y2 = poly[(i + 1) % n]
            nx, ny = y1 - y2, x2 - x1
            pa = [nx * x + ny * y for x, y in p]
            qa = [nx * x + ny * y for x, y in q]
            if max(pa) < min(qa) - 1e-12 or max(qa) < min(pa) - 1e-12:
                return False
    return True


def distance(p, q) -> float:
    """Clear distance between two convex polygons (0 if they touch or overlap)."""
    if _overlap(p, q):
        return 0.0
    best = math.inf
    for a, b in ((p, q), (q, p)):
        for pt in a:
            for i in range(len(b)):
                best = min(best, _seg_point(pt, b[i], b[(i + 1) % len(b)]))
    return best


# ----------------------------------------------------------------------
# Nesting
# ----------------------------------------------------------------------

@dataclass(frozen=True)
class Part:
    key: str
    polygon: tuple[tuple[float, float], ...]
    up: bool


@dataclass
class Layout:
    """A nested sheet, and whether it was checked to fit."""

    parts: list[Part] = field(default_factory=list)
    rows: list = field(default_factory=list)       # (y, height, count)
    used_area: float = 0.0
    fits: bool = False
    detail: str = ""
    trim: float = 0.0
    rotated: bool = False


def _place(shape: Shape, x: float, y0: float, row_h: float, up: bool, trim: float):
    poly = shape.polygon(trim)
    h = shape.height - trim
    if up:
        return tuple((x + px, y0 + py) for px, py in poly)
    # turned half a turn: base on the row's top line
    return tuple((x + shape.base - px, y0 + row_h - py) for px, py in poly)


def _strip(queue: list[Shape], y0: float, row_h: float, width: float, trim: float,
           gap: float) -> list[Part]:
    """Fill one row with triangles pointing alternately up and down, each slid
    left until it sits exactly ``gap`` from its neighbour."""
    row: list[Part] = []
    up = True
    while queue:
        s = queue[0]
        if s.height - trim > row_h + 1e-9:
            break
        if not row:
            x = EDGE_MARGIN_IN
        else:
            prev = row[-1].polygon
            lo = min(px for px, _ in prev) - s.base
            hi = max(px for px, _ in prev) + gap + 1e-6
            near = [r.polygon for r in row[-2:]]
            if min(distance(_place(s, hi, y0, row_h, up, trim), p) for p in near) < gap - 1e-9:
                hi += s.base
            for _ in range(40):
                mid = (lo + hi) / 2
                cand = _place(s, mid, y0, row_h, up, trim)
                if min(distance(cand, p) for p in near) >= gap:
                    hi = mid
                else:
                    lo = mid
            x = max(hi, EDGE_MARGIN_IN)
        poly = _place(s, x, y0, row_h, up, trim)
        if max(px for px, _ in poly) > width - EDGE_MARGIN_IN + 1e-9:
            break
        row.append(Part(s.key, poly, up))
        queue.pop(0)
        up = not up
    return row


def _nest(shapes: tuple[Shape, ...], w: float, h: float, trim: float, gap: float) -> Layout:
    queue = [s for s in shapes for _ in range(s.count)]
    parts, rows = [], []
    y = EDGE_MARGIN_IN
    while queue:
        row_h = queue[0].height - trim
        if y + row_h > h - EDGE_MARGIN_IN + 1e-9:
            return Layout(parts, rows, fits=False, detail=f"ran out of sheet after {len(rows)} rows", trim=trim)
        row = _strip(queue, y, row_h, w, trim, gap)
        if not row:
            return Layout(parts, rows, fits=False, detail="a single panel is wider than the sheet", trim=trim)
        parts += row
        rows.append((y, row_h, len(row)))
        y += row_h + gap
    return Layout(parts, rows, sum(_area(p.polygon) for p in parts), True,
                  f"{len(rows)} rows", trim)


def _area(poly) -> float:
    return abs(sum(poly[i][0] * poly[(i + 1) % len(poly)][1] - poly[(i + 1) % len(poly)][0] * poly[i][1]
                   for i in range(len(poly)))) / 2


def verify(layout: Layout, w: float = SHEET_W_IN, h: float = SHEET_H_IN, gap: float = PART_GAP_IN) -> list[str]:
    """Every part inside the margins; no two parts closer than the gap."""
    problems = []
    for i, p in enumerate(layout.parts):
        if (min(x for x, _ in p.polygon) < EDGE_MARGIN_IN - 1e-6 or max(x for x, _ in p.polygon) > w - EDGE_MARGIN_IN + 1e-6
                or min(y for _, y in p.polygon) < EDGE_MARGIN_IN - 1e-6 or max(y for _, y in p.polygon) > h - EDGE_MARGIN_IN + 1e-6):
            problems.append(f"part {i} leaves the margin")
        for j in range(i + 1, len(layout.parts)):
            if distance(p.polygon, layout.parts[j].polygon) < gap - 1e-6:
                problems.append(f"parts {i} and {j} closer than the gap")
    return problems


def layout(radius_in: float, sheet_w: float = SHEET_W_IN, sheet_h: float = SHEET_H_IN,
           trim: float = 0.0, gap: float = PART_GAP_IN) -> Layout:
    """The best checked nest of one hemisphere's panels, either way round."""
    shapes = panel_set(radius_in).shapes
    best = None
    for rotated, (w, h) in ((False, (sheet_w, sheet_h)), (True, (sheet_h, sheet_w))):
        lay = _nest(shapes, w, h, trim, gap)
        lay.rotated = rotated
        if lay.fits and not verify(lay, w, h, gap):
            if rotated:
                lay.parts = [Part(p.key, tuple((y, x) for x, y in p.polygon), p.up) for p in lay.parts]
            return lay
        best = best or lay
    best.fits = False
    return best


def _bisect(fits, lo: float, hi: float) -> float:
    for _ in range(40):
        mid = (lo + hi) / 2
        if fits(mid):
            lo = mid
        else:
            hi = mid
    return lo


@lru_cache(maxsize=4)
def max_radius(trim_mode: str = "strict") -> tuple[float, Layout]:
    """The largest hemisphere whose forty panels come out of one sheet.

    ``trim_mode="trimmed"`` lets each point be cut back up to
    :data:`MAX_TRIM_IN`; the trim used is the least that makes the size fit.
    """
    if trim_mode == "strict":
        r = _bisect(lambda R: layout(R).fits, 6.0, 80.0)
        return r, layout(r)

    def fits_trimmed(R: float) -> bool:
        return layout(R, trim=MAX_TRIM_IN).fits

    r = _bisect(fits_trimmed, 6.0, 80.0)
    t = _bisect(lambda T: not layout(r, trim=T).fits, 0.0, MAX_TRIM_IN)
    t = min(MAX_TRIM_IN, t + 1e-3)
    return r, layout(r, trim=t)


# ----------------------------------------------------------------------
# What the shell becomes
# ----------------------------------------------------------------------

def _mesh(radius_in: float):
    g = _two_v()
    v = np.asarray(g.vertices, dtype=float) * radius_in
    faces = [tuple(int(k) for k in f) for f in g.hemisphere_faces]
    return v, faces


def shell(radius_in: float) -> dict:
    """The welded shell's own numbers, measured off the faceted solid."""
    v, faces = _mesh(radius_in)
    # volume: tetrahedra from the sphere's centre, which lies in the base plane
    vol = sum(abs(float(np.dot(v[a], np.cross(v[b], v[c])))) / 6 for a, b, c in faces)
    edges: dict[tuple[int, int], int] = {}
    for f in faces:
        for k in range(3):
            e = tuple(sorted((f[k], f[(k + 1) % 3])))
            edges[e] = edges.get(e, 0) + 1
    seams = [e for e, n in edges.items() if n == 2]
    rim = [e for e, n in edges.items() if n == 1]
    length = lambda e: float(np.linalg.norm(v[e[0]] - v[e[1]]))
    rim_v = sorted({k for e in rim for k in e}, key=lambda k: math.atan2(v[k][1], v[k][0]))
    floor = abs(sum(v[rim_v[i]][0] * v[rim_v[(i + 1) % len(rim_v)]][1]
                    - v[rim_v[(i + 1) % len(rim_v)]][0] * v[rim_v[i]][1] for i in range(len(rim_v)))) / 2
    verts = {k for f in faces for k in f}
    return {
        "volume_in3": vol, "floor_in2": floor,
        "height_in": float(max(v[k][2] for k in verts) - min(v[k][2] for k in verts)),
        "across_in": 2 * max(math.hypot(v[k][0], v[k][1]) for k in rim_v),
        "seams": len(seams), "seam_in": sum(length(e) for e in seams),
        "rim_in": sum(length(e) for e in rim), "vertices": len(verts),
        "inner_vertices": len(verts) - len(rim_v),
    }


def vessel(radius_in: float, thickness_mm: float = 3.0, trim: float = 0.0) -> dict:
    """What a welded forty-panel shell becomes, at a given radius and plate."""
    ps = panel_set(radius_in)
    s = shell(radius_in)
    t_in = thickness_mm / 25.4
    trim_loss = 0.0
    if trim > 0:
        for sh in ps.shapes:
            trim_loss += sh.count * (sh.trim_width(trim) * trim / 2)
    part_in2 = ps.area - trim_loss
    sheet_in2 = SHEET_W_IN * SHEET_H_IN
    perims = sum(sh.count * sum(math.dist(a, b) for a, b in zip(sh.polygon(trim), sh.polygon(trim)[1:] + sh.polygon(trim)[:1]))
                 for sh in ps.shapes)
    return {
        "radius_in": radius_in, "diameter_in": s["across_in"], "diameter_ft": s["across_in"] / 12,
        "height_in": s["height_in"], "height_ft": s["height_in"] / 12,
        "floor_sqft": s["floor_in2"] / 144, "volume_ft3": s["volume_in3"] / 1728,
        "volume_gal": s["volume_in3"] / 1728 * GAL_PER_FT3,
        "thickness_mm": thickness_mm,
        "part_lb": part_in2 * t_in * STEEL_LB_PER_IN3,
        "sheet_lb": sheet_in2 * t_in * STEEL_LB_PER_IN3,
        "offcut_lb": (sheet_in2 - part_in2) * t_in * STEEL_LB_PER_IN3,
        "cut_in": perims, "cut_minutes": perims / CUT_IN_PER_MIN, "pierces": ps.panels,
        "seam_in": s["seam_in"], "seams": s["seams"], "rim_in": s["rim_in"],
        "caps": s["inner_vertices"] if trim > 0 else 0,
        "cap_in": max((sh.trim_width(trim) for sh in ps.shapes), default=0.0) if trim > 0 else 0.0,
    }


def seam_weld(seam_in: float, travel_in_per_min: float = WELD_IN_PER_MIN) -> dict:
    """Welding the shell's seams, as length and as bench time."""
    return {"weld_in": seam_in, "weld_ft": seam_in / 12, "minutes": seam_in / travel_in_per_min}


# ----------------------------------------------------------------------
# A bigger dome in plate: sheets per 3V shell
# ----------------------------------------------------------------------

def three_v_sheets(sheet_w: float = SHEET_W_IN, sheet_h: float = SHEET_H_IN,
                   base_ft: float | None = None) -> dict:
    """A 3V 5/8 dome cut from plate: how many sheets, nesting each sheet with
    the same checked strips. ``base_ft`` defaults to the panel method's
    reference dome."""
    from . import panel_method as pm

    d = pm.reference()
    if base_ft is not None:
        d = pm.PanelDome(base_ft * 0.3048 / 2 / d.cut.base_radius, d.stick_width_m, d.stick_depth_m, d.cut)
    else:
        base_ft = pm.CONSTANTS["base_ft"].value
    IN = 1 / 0.0254
    shapes = []
    for pc in d.panel_classes():
        shapes.append(_triangle_shape(pc.kind, pc.sides[0] * IN, pc.sides[1] * IN, pc.sides[2] * IN, pc.count))
    shapes.sort(key=lambda s: -s.height)
    # Sheet by sheet: nest what is left, either way round, keep the fuller.
    left = {s.key: s.count for s in shapes}
    per_sheet, sheets = [], 0
    while sum(left.values()):
        best = None
        for w, h in ((sheet_w, sheet_h), (sheet_h, sheet_w)):
            todo = tuple(Shape(s.key, s.base, s.apex_x, s.height, left[s.key]) for s in shapes if left[s.key])
            lay = _nest(todo, w, h, 0.0, PART_GAP_IN)
            if best is None or len(lay.parts) > len(best.parts):
                best = lay
        if not best.parts:
            raise RuntimeError("a 3V panel is larger than the sheet")
        for part in best.parts:
            left[part.key] -= 1
        per_sheet.append(len(best.parts))
        sheets += 1
    area = sum(s.count * s.area for s in shapes)
    return {"base_ft": base_ft, "panels": sum(s.count for s in shapes),
            "per_sheet": per_sheet, "sheets": sheets, "area_in2": area,
            "lb_2mm": area * (2 / 25.4) * STEEL_LB_PER_IN3,
            "lb_3mm": area * (3 / 25.4) * STEEL_LB_PER_IN3,
            "largest_side_in": max(s.base for s in shapes),
            "used_pct": 100 * area / (sheets * sheet_w * sheet_h)}


def three_v_sweet_spot(lo_ft: int = 8, hi_ft: int = 16) -> list[dict]:
    """Sheets and plate use for every whole-foot 3V dome in a range: where a
    size lets two rows of the big panels share a sheet, the count drops."""
    return [three_v_sheets(base_ft=float(ft)) for ft in range(lo_ft, hi_ft + 1)]


def plate_limit_3v(sheet_w: float = SHEET_W_IN, sheet_h: float = SHEET_H_IN) -> dict:
    """Kept for the book tokens: the 3V dome in plate, by sheets."""
    t = three_v_sheets(sheet_w, sheet_h)
    from . import panel_method as pm
    f = pm.facts()
    return {"side_in": t["largest_side_in"], "diameter_ft": t["base_ft"],
            "floor_sqft": f["floor_m2"] / 0.3048 ** 2, "sheets": t["sheets"], **t}


def validate_plate_nesting() -> None:
    """Checks that keep this module honest."""
    ps = panel_set(30.0)
    assert ps.panels == 40, ps.panels
    assert {s.key: s.count for s in ps.shapes} == {"equilateral": 10, "isosceles": 30}
    r, lay = max_radius("strict")
    assert lay.fits and not verify(lay), "the strict nest is checked in sheet coordinates"
    assert len(lay.parts) == 40
    # the area bound: no nest can beat the sheet's own area
    assert panel_set(r).area < SHEET_W_IN * SHEET_H_IN
    assert not layout(r * 1.05).fits, "the strict maximum is a maximum"
    rt, lt = max_radius("trimmed")
    assert rt >= r and lt.fits and lt.trim <= MAX_TRIM_IN + 1e-6
    s = shell(r)
    assert s["seams"] == 55 and s["vertices"] == 26
    # faceted volume is under the sphere's
    assert s["volume_in3"] < 2 / 3 * math.pi * r ** 3
    t = three_v_sheets()
    assert t["panels"] == 105 and t["sheets"] > 1
