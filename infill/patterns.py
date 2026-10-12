"""Every way to fill or cover a triangle, worked out piece by piece.

Choose a **material**, an **arrangement** (where the runs go in plan) and,
for strip stock, a **lay** (how each piece sits in the frame's thickness and
how it meets the one before). :func:`layout` returns every piece with its
plan outline, its long and short length, and the saw setting for each end;
the section the pieces were packed in; and what the pattern measures --
coverage, voids, light through, weight.

Arrangements
------------
``rings``      concentric pinwheels, the frame repeated inward ring by ring
``parallel``   straight runs parallel to one edge, stepping across
``across``     straight runs square to one edge, stepping along it
``chevron``    runs parallel to the two side edges, meeting on the centre line
``louvers``    slats parallel to one edge, tilted, lapped: covered in plan,
               open to air
``sheet``      one piece (sheet goods, film), or two if it will not fit
``strips``     corrugated metal: strips across the triangle, lapped

Each end of a straight run that meets a 45-degree wall is a compound cut:
the cut plane *is* the wall. :func:`compound` turns that plane into the two
numbers a mitre saw takes -- mitre (table turned from square) and bevel
(blade tilted from upright), with the piece held as it lies in the panel.
"""

from __future__ import annotations

import math
from dataclasses import dataclass, field

import numpy as np

from . import geom2d as g2
from . import section as sec
from .constants import C
from .frame import PanelType, Spec

# ----------------------------------------------------------------------
# What can be chosen
# ----------------------------------------------------------------------

MATERIALS = {
    "w8": ("Wedges (1/8 log)", "log"),
    "s16": ("1/16 slices", "log"),
    "s32": ("1/32 slices", "log"),
    "fence": ("Fence pickets", "board"),
    "milled": ("Milled 1x6 boards", "board"),
    "osb": ("OSB sheet (7/16)", "sheet"),
    "ply": ("Milled panel / plywood (23/32)", "sheet"),
    "metal": ("Corrugated sheet metal", "metal"),
    "film": ("Greenhouse film (6 mil)", "film"),
    "rounds": ("Log rounds (whole-trunk slices)", "round"),
}

ARRANGEMENTS = {
    "rings": "Concentric pinwheel rings",
    "parallel": "Stripes parallel to one edge",
    "across": "Stripes square to one edge",
    "chevron": "Chevron to the centre line",
    "louvers": "Louvers (vent slats)",
    "sheet": "One piece",
    "strips": "Lapped strips",
    "hex": "Honeycomb",
    "square": "Square grid",
    "graded": "Big rounds, small ones in the gaps",
}

LAYS = {
    "flipflop": ("Flip-flop", "every other piece turned upside down: sawn face mates sawn face, "
                 "bark meets bark"),
    "samehand": ("Same hand (shingled)", "every piece lies like the frame, each one's bark against "
                 "the last one's slope"),
    "shim": ("Full runs with shims", "full pieces flipped onto the slope, a thin 1/32 slice standing "
             "in each bark-to-bark seam"),
    "standing": ("Point-down / point-up", "slices standing on their points, every other one hanging "
                 "point-up between them"),
    "comb": ("Point-down comb", "slices all standing on their points: grooves on the open side"),
    "butted": ("Laid flat, gapped", "boards flat, a movement gap between each"),
    "boardonboard": ("Board-on-board", "two layers, the top boards lapping the gaps in the bottom "
                     "layer: covered, and air moves through"),
    "onedge": ("On edge", "boards standing on edge, tight"),
    "aligned": ("Layers aligned", "every layer laid the same"),
    "offset": ("Layers offset", "every other layer slid half a gap over, so each round sits over a gap below"),
    "rotated": ("Layers rotated", "each layer's rows turned to run along the next edge"),
}

OPTIONS = {
    "log": {"arrangements": ["rings", "parallel", "across", "chevron", "louvers"],
            "lays": ["flipflop", "samehand", "shim", "standing", "comb"]},
    "board": {"arrangements": ["parallel", "across", "chevron", "louvers"],
              "lays": ["butted", "boardonboard", "onedge"]},
    "sheet": {"arrangements": ["sheet"], "lays": []},
    "film": {"arrangements": ["sheet"], "lays": []},
    "metal": {"arrangements": ["strips"], "lays": []},
    "round": {"arrangements": ["hex", "square", "graded"], "lays": ["aligned", "offset", "rotated"]},
}


@dataclass(frozen=True)
class Options:
    material: str = "w8"
    arrangement: str = "rings"
    lay: str = "flipflop"
    mode: str = "fill"          # fill: inside the frame. cover: over its open side
    edge: int = 0               # the edge the runs are laid from
    infill_log_in: float = 12.0
    louver_tilt_deg: float = 45.0
    flush: str = "open"         # boards and sheets in fill mode: flush with "open" or "flat" side
    round_t_in: float = 1.5     # rounds: slice thickness
    round_min_in: float = 3.0   # rounds: the smallest round worth cutting
    leftover: str = "cut"       # rounds: "cut" to fit, or "open"
    layer: int = 1              # rounds: which layer the plan shows


def valid(opts: Options) -> Options:
    """The nearest choice that makes sense for this material."""
    kind = MATERIALS[opts.material][1]
    o = OPTIONS[kind]
    arrangement = opts.arrangement if opts.arrangement in o["arrangements"] else o["arrangements"][0]
    lays = o["lays"] if arrangement != "louvers" else []
    lay = opts.lay if opts.lay in lays else (lays[0] if lays else "")
    if opts.material == "s32" and lay == "shim":
        lay = "flipflop"
    from dataclasses import replace
    return replace(opts, arrangement=arrangement, lay=lay, edge=opts.edge % 3)


# ----------------------------------------------------------------------
# What comes out
# ----------------------------------------------------------------------

@dataclass
class EndCut:
    where: str
    meets: str
    mitre: float
    bevel: float

    def text(self) -> str:
        if abs(self.mitre) < 0.05 and abs(self.bevel) < 0.05:
            how = "square"
        else:
            how = f"mitre {abs(self.mitre):.1f}°, bevel {abs(self.bevel):.1f}°"
        return f"{self.where}: {how} ({self.meets})"


@dataclass
class Piece:
    group: str
    material: str
    pose: str
    plan: np.ndarray
    long: float
    short: float
    ends: list[EndCut] = field(default_factory=list)
    stock: sec.Stock | None = None
    trim: float = 0.0
    note: str = ""
    area_in2: float = 0.0       # section area (strip stock) or sheet area (sheet goods)
    spec: dict | None = None    # how to build it as a solid (infill.solids.build)
    solid: object | None = None

    @property
    def cut_text(self) -> str:
        return "; ".join(e.text() for e in self.ends) or "-"


@dataclass
class Layout:
    title: str
    opts: Options
    panel: PanelType
    pieces: list[Piece]
    placed: list[sec.Placed]
    wall: np.ndarray | None
    T: float
    z0: float
    metrics: dict
    steps: list[str]
    fitting: list[str]
    remainder: np.ndarray | None = None
    clip: np.ndarray | None = None
    nest: dict | None = None
    extra: dict | None = None


# ----------------------------------------------------------------------
# Cuts
# ----------------------------------------------------------------------

def compound(axis: np.ndarray, normal3: np.ndarray) -> tuple[float, float]:
    """Mitre and bevel for a cut on ``normal3``, the piece lying as it does
    in the panel, its length along ``axis``. A square cut is (0, 0)."""
    a = g2.unit(axis)
    u = g2.perp(a)
    n = np.asarray(normal3, float)
    n = n / np.linalg.norm(n)
    na = float(n[0] * a[0] + n[1] * a[1])
    nu = float(n[0] * u[0] + n[1] * u[1])
    if na < 0:
        na, nu, nz = -na, -nu, -float(n[2])
    else:
        nz = float(n[2])
    bevel = math.degrees(math.asin(max(-1.0, min(1.0, nz))))
    mitre = math.degrees(math.atan2(nu, na))
    return mitre, bevel


# ----------------------------------------------------------------------
# Strip-stock layouts
# ----------------------------------------------------------------------

def _sequence(stocks: dict, opts: Options) -> list[tuple[sec.Stock, str]]:
    st = stocks[opts.material]
    if st.kind == "board":
        return {"butted": [(st, "BU" if opts.flush == "open" else "BD")],
                "boardonboard": [(st, "BD"), (st, "BU")],
                "onedge": [(st, "BE")]}[opts.lay]
    return {"flipflop": [(st, "FUL"), (st, "FDR")],
            "samehand": [(st, "FDR")],
            "shim": [(st, "FUL"), (stocks["s32"], "PD")],
            "standing": [(st, "PD"), (st, "PU")],
            "comb": [(st, "PD")]}[opts.lay]


def _section_pieces(opts: Options, stocks: dict, T: float, wall: np.ndarray | None,
                    span: float) -> tuple[list[sec.Placed], dict, int]:
    """Pieces end-on, from the wall out past ``span``."""
    seq = _sequence(stocks, opts)
    period = len(seq)
    if wall is None:
        wall = np.array([[-1.0, 0.0], [0.0, 0.0], [0.0, T], [-1.0, T]])
    if opts.lay == "butted":
        placed = sec.pack(T, wall, seq, 1, gap=C["board_gap_in"])
        w = seq[0][0].width
        x0 = placed[0].x_lo
        n = int(span // (w + C["board_gap_in"])) + 3
        placed = sec.spaced(T, x0, [(seq[0][0], seq[0][1], i * (w + C["board_gap_in"]), 0.0) for i in range(n)])
    elif opts.lay == "boardonboard":
        st = seq[0][0]
        w, lap = st.width, C["board_lap_in"]
        first = sec.pack(T, wall, [(st, "BD")], 1)[0]
        x0 = first.x_lo
        n = int(span // (2 * w - 2 * lap)) + 3
        lay = []
        for i in range(n):
            lay.append((st, "BD", i * (2 * w - 2 * lap), 0.0))
            lay.append((st, "BU", i * (2 * w - 2 * lap) + w - lap, 0.0))
        placed = sec.spaced(T, x0, lay)
        period = 2
    else:
        gap = 0.0
        n = 2
        while True:
            placed = sec.pack(T, wall, seq, n, gap=gap)
            if placed[-1].x_lo > span or n > 4000:
                break
            n = int(n * 1.6) + 2
    m = sec.measure(placed, T, period)
    return placed, m, period


def _louver_section(opts: Options, stocks: dict, T: float, wall: np.ndarray, span: float):
    st = stocks[opts.material]
    tilt = opts.louver_tilt_deg
    pose = "BD" if st.kind == "board" else "FDL"
    first = sec.posed(st, pose, T)
    c = first.mean(axis=0)
    a = math.radians(tilt)
    R = np.array([[math.cos(a), -math.sin(a)], [math.sin(a), math.cos(a)]])
    slat = (first - c) @ R.T
    slat = slat - np.array([0.0, slat[:, 1].min()])
    slat = sec.fit(slat, T)
    w_proj = float(slat[:, 0].max() - slat[:, 0].min())
    pitch = max(0.25, w_proj - C["louver_lap_in"])
    # Slide the first slat onto the wall.
    zs = np.linspace(0.0, T, 600)
    _lo, env = sec.extents(wall, zs)
    lo, _hi = sec.extents(slat, zs)
    both = ~np.isnan(lo) & ~np.isnan(env)
    shift = float(np.max(env[both] - lo[both])) if np.any(both) else float(np.nanmax(env))
    slat = slat + np.array([shift, 0.0])
    n = int(span // pitch) + 3
    placed = [sec.Placed(st, pose, slat + np.array([i * pitch, 0.0])) for i in range(n)]
    clear = sec.min_gap(placed[0].poly, placed[1].poly)
    m = sec.measure(placed, T, 1)
    m.update({"pitch": pitch, "air_gap": clear, "lap": C["louver_lap_in"], "tilt": tilt})
    return placed, m, 1


def _clip_at(panel: PanelType, opts: Options, z: float) -> np.ndarray:
    if opts.mode == "cover":
        return g2.inset_triangle(panel.tri, panel.spec.gasket_in / 2 - C["cover_overhang_in"])
    return panel.opening(min(max(z, 0.0), panel.spec.thickness_in))


def _run_piece(panel: PanelType, opts: Options, placed: sec.Placed, origin, along, across,
               z0: float, extra_clip=None) -> tuple[np.ndarray, float, float, list] | None:
    """One straight run in plan: the piece's band at several heights, each
    clipped by the opening at that height (and by ``extra_clip``)."""
    zs_piece = np.linspace(placed.poly[:, 1].min() + 1e-6, placed.poly[:, 1].max() - 1e-6, 5)
    lo, hi = sec.extents(placed.poly, zs_piece)
    pts, lengths = [], []
    for z, l, h in zip(zs_piece, lo, hi):
        if np.isnan(l):
            continue
        band = g2.strip(origin, along, across, l, h)
        poly = g2.clip_convex(band, _clip_at(panel, opts, z + z0))
        if extra_clip is not None and len(poly):
            poly = g2.clip_convex(poly, extra_clip)
        if len(poly) < 3:
            continue
        pts.extend(poly)
        mid = g2.strip(origin, along, across, (l + h) / 2 - 1e-4, (l + h) / 2 + 1e-4)
        chord = g2.clip_convex(mid, _clip_at(panel, opts, z + z0))
        if extra_clip is not None and len(chord):
            chord = g2.clip_convex(chord, extra_clip)
        if len(chord):
            e = chord @ along
            lengths.append(float(e.max() - e.min()))
    if len(pts) < 3 or not lengths:
        return None
    outline = g2.hull(pts)
    if g2.area(outline) < 0.05:
        return None
    return outline, max(lengths), min(lengths), zs_piece


def _ends(panel: PanelType, opts: Options, outline: np.ndarray, along: np.ndarray,
          centre_line: tuple | None = None) -> list[EndCut]:
    """Saw settings for both ends of a straight run."""
    e = outline @ along
    out = []
    for where, val in (("one end", e.min()), ("other end", e.max())):
        end_pts = outline[np.abs(e - val) < 1e-3 + 0.02 * (e.max() - e.min())]
        point = end_pts.mean(axis=0)
        if centre_line is not None and abs(float(np.dot(point - centre_line[0], centre_line[1]))) < 0.6:
            m, b = compound(along, np.array([centre_line[1][0], centre_line[1][1], 0.0]))
            out.append(EndCut(where, "meets its mirror on the centre line", m, b))
            continue
        k = _nearest_wall(panel, point)
        if opts.mode == "cover":
            fold = panel.folds[k]
            bev = (fold or 0.0) / 2
            mvec = panel.inward(k)
            # A cut whose plane leans half the fold off square to the panel.
            n = np.array([mvec[0], mvec[1], math.tan(math.radians(bev))])
            m, b = compound(along, n)
            meets = (f"the panel's {panel.edge_class[k].lower()} edge; bevel half the {fold:.1f}° seam fold"
                     if fold else f"the panel's {panel.edge_class[k].lower()} edge (rim)")
            out.append(EndCut(where, meets, m, b))
        else:
            n, _d = panel.wall_plane(k)
            m, b = compound(along, n)
            out.append(EndCut(where, f"the 45° wall of the {panel.edge_class[k].lower()} edge", m, b))
    return out


def _nearest_wall(panel: PanelType, point: np.ndarray) -> int:
    best, which = 1e9, 0
    for k in range(3):
        a, _b = panel.edge(k)
        d = float(np.dot(point - a, panel.inward(k)))
        if d < best:
            best, which = d, k
    return which


def _span(panel: PanelType, across: np.ndarray, origin: np.ndarray, opts: Options) -> float:
    clip = _clip_at(panel, opts, panel.spec.thickness_in)
    d = (clip - origin) @ across
    return float(d.max())


def _straight(panel: PanelType, opts: Options, stocks: dict, T: float, z0: float,
              along: np.ndarray, across: np.ndarray, origin: np.ndarray, wall,
              label: str, extra_clip=None, centre_line=None, start_index: int = 1):
    span = _span(panel, across, origin, opts)
    if opts.arrangement == "louvers":
        placed, m, period = _louver_section(opts, stocks, T, wall if wall is not None else
                                            np.array([[-1.0, 0.0], [0.0, 0.0], [0.0, T], [-1.0, T]]), span)
    else:
        placed, m, period = _section_pieces(opts, stocks, T, wall, span)
    pieces = []
    for i, pl in enumerate(placed):
        run = _run_piece(panel, opts, pl, origin, along, across, z0, extra_clip)
        if run is None:
            continue
        outline, longest, shortest, _z = run
        ends = _ends(panel, opts, outline, along, centre_line)
        pieces.append(Piece(group=f"{label} {start_index + len(pieces)}", material=opts.material,
                            pose=pl.pose, plan=outline, long=longest, short=shortest, ends=ends,
                            stock=pl.stock, trim=sec.trim(pl.stock, pl.pose, T),
                            area_in2=g2.area(pl.poly),
                            spec={"type": "strip", "section": pl.poly, "origin": np.asarray(origin, float),
                                  "along": np.asarray(along, float), "across": np.asarray(across, float),
                                  "z0": z0, "extra": extra_clip,
                                  "tilt": opts.louver_tilt_deg if opts.arrangement == "louvers" else 0.0}))
    return pieces, placed, m


def _rings(panel: PanelType, opts: Options, stocks: dict, T: float, wall: np.ndarray):
    op0 = panel.opening(0.0)
    span = g2.inradius(panel.opening(T)) + panel.spec.radius_in
    placed, m, period = _section_pieces(opts, stocks, T, wall, span)
    r_open = g2.inradius(op0)
    pieces, rings_used = [], []
    remainder = None
    for i, pl in enumerate(placed):
        z_lo, z_hi = pl.poly[:, 1].min(), pl.poly[:, 1].max()
        zs = np.linspace(z_lo + 1e-6, z_hi - 1e-6, 5)
        lo, hi = sec.extents(pl.poly, zs)
        ok = ~np.isnan(lo)
        lo, hi = lo[ok], hi[ok]
        inner_lo = float(np.min(lo))
        if inner_lo >= r_open - 0.25:
            break
        # Seen straight on, the ring covers from its outermost reach to its innermost.
        x_out, x_in = float(np.min(lo)), float(np.max(hi))
        width = x_in - x_out
        outer = g2.inset_triangle(op0, x_out)
        if g2.inradius(outer) < width * 1.05:
            remainder = g2.inset_triangle(op0, max(x_out, 0.0))
            break
        members = g2.pinwheel(outer, width)
        # Lengths at the piece's lowest and highest reach.
        lens = []
        for lz, hz in ((lo[0], hi[0]), (lo[-1], hi[-1])):
            t = g2.inset_triangle(op0, lz)
            if g2.inradius(t) > (hz - lz):
                lens.append([L for _p, L, _d in g2.pinwheel(t, hz - lz)])
        if not lens:
            remainder = outer
            break
        ring_no = len(rings_used) + 1
        rings_used.append(pl)
        for k, (poly, L, d) in enumerate(members):
            ls = [row[k] for row in lens]
            ea, _eb = panel.edge(k)
            m_in = panel.inward(k)
            org = ea + m_in * panel.inset_at(0.0)
            proj = (poly - org) @ d
            spec = {"type": "strip", "section": pl.poly, "origin": org, "along": d, "across": m_in,
                    "z0": 0.0, "extra": None, "tilt": 0.0, "s_range": (float(proj.min()), float(proj.max()))}
            ends = [EndCut("tail", "runs to the far side of the ring member behind it", 0.0, 0.0),
                    EndCut("head", "butts the side of the ring member ahead (square in plan; "
                           "scribe to its face)", 0.0, 0.0)]
            pieces.append(Piece(group=f"Ring {ring_no}, {panel.edge_class[k].lower()} side",
                                material=opts.material, pose=pl.pose, plan=poly, long=max(ls),
                                short=min(ls), ends=ends, stock=pl.stock, trim=sec.trim(pl.stock, pl.pose, T),
                                area_in2=g2.area(pl.poly), spec=spec))
    else:
        remainder = None
    if remainder is None and rings_used:
        last = rings_used[-1]
        hi_last = float(np.nanmax(sec.extents(last.poly, np.array([last.poly[:, 1].min() + 1e-6]))[1]))
        remainder = g2.inset_triangle(op0, hi_last)
    if remainder is not None and g2.inradius(remainder) < 0.05:
        remainder = None
    return pieces, rings_used if rings_used else placed[:2], m, remainder


def _sheet(panel: PanelType, opts: Options, T: float):
    s = panel.spec
    kind = opts.material
    thick = {"osb": C["osb_in"], "ply": C["ply_in"], "film": 0.006}[kind]
    pieces, fitting = [], []
    if opts.mode == "fill":
        if kind == "film":
            poly = panel.opening(T)
            allowance = s.radius_in  # up the slope, stapled to the wall's face
            note = (f"cut {allowance:.1f} in oversize all round: the film runs down the 45° wall "
                    "and is stapled to its face")
            outline = g2.inset_triangle(poly, -allowance)
        else:
            top = T if opts.flush == "open" else thick
            outline = panel.opening(top)
            poly = outline
            note = ("edges bevelled to lie on the 45° walls; top face flush with the open side"
                    if opts.flush == "open" else "edges bevelled to lie on the 45° walls; sits at the flat side")
        ends = []
        for k in range(3):
            if kind == "film":
                break
            n, _d = panel.wall_plane(k)
            a, b = panel.edge(k)
            m, bev = compound(b - a, np.array([n[0], n[1], n[2]]))
            ends.append(EndCut(f"{panel.edge_class[k].lower()} edge", "the 45° wall", 0.0, bev))
    else:
        outline = g2.inset_triangle(panel.tri, s.gasket_in / 2 - C["cover_overhang_in"])
        if kind == "film":
            outline = g2.inset_triangle(outline, -C["film_wrap_in"])
            note = f"cut {C['film_wrap_in']:.0f} in oversize all round, wrapped over the bark and stapled"
            ends = []
        else:
            note = "laid over the open side; edges bevelled to half each seam's fold so neighbours meet"
            ends = [EndCut(f"{panel.edge_class[k].lower()} edge",
                           f"the seam ({panel.folds[k]:.1f}° fold)" if panel.folds[k] else "the rim",
                           0.0, (panel.folds[k] or 0.0) / 2) for k in range(3)]
    if kind == "film":
        nest = nest_roll(outline, C["film_roll_w_in"])
        zf = T if opts.mode == "fill" else T + 0.02
        pieces.append(Piece("Film", kind, "film", outline, *_extent(outline), ends=[], note=note,
                            area_in2=g2.area(outline),
                            spec={"type": "slab", "plan": outline, "z": (zf, zf + 0.03), "bounds": False}))
        nest["pieces_per_panel"] = 1
        return pieces, fitting, nest, thick
    sheet_w, sheet_l = C["sheet_w_in"], C["sheet_l_in"]
    nest = nest_triangle(outline, sheet_w, sheet_l)
    if nest["per_sheet"] == 0:
        # Too big for one sheet: two halves, split on the altitude from the apex.
        apex = outline[np.argmax(outline[:, 1])]
        halves = [g2.clip_halfplane(outline, apex, (1.0, 0.0)), g2.clip_halfplane(outline, apex, (-1.0, 0.0))]
        fitting.append("too big for one sheet: cut as two halves meeting on the centre line, "
                       "joined over a cleat")
        for i, (h, nx) in enumerate(zip(halves, (1.0, -1.0))):
            pieces.append(Piece(f"Half {i + 1}", kind, "sheet", h, *_extent(h), ends=ends,
                                note=note, area_in2=g2.area(h),
                                spec=_sheet_spec(panel, opts, outline, thick, T, half=(apex, nx))))
        nest = nest_triangle(halves[0], sheet_w, sheet_l)
        nest["pieces_per_panel"] = 2
    else:
        pieces.append(Piece("Sheet", kind, "sheet", outline, *_extent(outline), ends=ends, note=note,
                            area_in2=g2.area(outline), spec=_sheet_spec(panel, opts, outline, thick, T)))
        nest["pieces_per_panel"] = 1
    return pieces, fitting, nest, thick


def _sheet_spec(panel, opts, plan, thick, T, half=None) -> dict:
    """A sheet as a slab cut oversize in plan, trimmed by the walls (or the
    seam bevels) -- and, for a half, by the centre line."""
    z = ((T if opts.flush == "open" else thick) - thick, T if opts.flush == "open" else thick) \
        if opts.mode == "fill" else (T, T + thick)
    return {"type": "slab", "plan": g2.inset_triangle(plan, -thick * 3), "z": z, "bounds": True,
            "half": half}


def _extent(poly) -> tuple[float, float]:
    xs = poly[:, 0]
    w = float(xs.max() - xs.min())
    return w, w


def nest_triangle(tri, sheet_w: float, sheet_l: float, kerf: float = 0.125) -> dict:
    """How many copies of a triangle fit on one sheet: rows of triangles
    turned alternately, each base edge and both sheet ways tried."""
    best = {"per_sheet": 0, "rows": 0, "per_row": 0, "base": None, "height": 0.0, "base_len": 0.0}
    t = g2.hull(np.asarray(tri, float))
    if len(t) != 3:
        h = g2.hull(t)
        xs, ys = h[:, 0], h[:, 1]
        w, l = xs.max() - xs.min() + kerf, ys.max() - ys.min() + kerf
        for W, L in ((sheet_w, sheet_l), (sheet_l, sheet_w)):
            n = int(W // w) * int(L // l)
            if n > best["per_sheet"]:
                best.update(per_sheet=n, rows=int(W // w), per_row=int(L // l), base=0, height=l, base_len=w)
        return best
    for k in range(3):
        a, b = t[k], t[(k + 1) % 3]
        c = t[(k + 2) % 3]
        base = float(np.linalg.norm(b - a)) + kerf
        d = g2.unit(b - a)
        height = abs(float(np.dot(c - a, g2.perp(d)))) + kerf
        apex = float(np.dot(c - a, d))
        for W, L in ((sheet_w, sheet_l), (sheet_l, sheet_w)):
            rows = int(W // height)
            if rows == 0 or L < base:
                continue
            ups = int(L // base)
            # Turned triangles fill the gaps between: each sits one apex-offset along.
            off = min(max(apex, 0.0), base)
            downs = max(0, int((L - off) // base))
            per_row = ups + downs
            n = rows * per_row
            if n > best["per_sheet"]:
                best.update(per_sheet=n, rows=rows, per_row=per_row, base=k, height=height, base_len=base)
    return best


def nest_roll(tri, roll_w: float, kerf: float = 0.5) -> dict:
    """Triangles off a roll: as many rows across the roll as fit, each row
    alternating up and down; how much roll each triangle uses."""
    t = np.asarray(tri, float)
    best = None
    for k in range(3):
        a, b = t[k], t[(k + 1) % 3]
        c = t[(k + 2) % 3]
        base = float(np.linalg.norm(b - a)) + kerf
        d = g2.unit(b - a)
        height = abs(float(np.dot(c - a, g2.perp(d)))) + kerf
        rows = int(roll_w // height)
        if rows == 0:
            continue
        per_in = 2.0 * rows / base          # triangles per inch of roll, alternating
        if best is None or per_in > best["per_in"]:
            best = {"per_in": per_in, "rows": rows, "base_len": base, "height": height, "base": k}
    if best is None:
        # Wider than the roll: one triangle across two widths, seamed.
        h = g2.hull(t)
        span = float(h[:, 0].max() - h[:, 0].min())
        best = {"per_in": 0.5 / max(span, 1.0), "rows": 0, "base_len": span, "height": 0.0, "base": None}
    best["roll_in_per_piece"] = 1.0 / best["per_in"]
    best["per_sheet"] = best["rows"]
    best["per_row"] = 2
    return best


def _metal(panel: PanelType, opts: Options, T: float):
    s = panel.spec
    if opts.mode == "fill":
        poly = panel.opening(T)
        note = "fills the open side; bend a 1 in flange down onto each 45° wall"
    else:
        poly = g2.inset_triangle(panel.tri, s.gasket_in / 2 - C["cover_overhang_in"])
        note = "laid over the open side, ribs running toward the rim"
    a, b = panel.edge(opts.edge)
    along = g2.unit(b - a)
    across = panel.inward(opts.edge)
    origin = a
    d = (poly - origin) @ across
    lo, hi = float(d.min()), float(d.max())
    cover, full = C["metal_cover_in"], C["metal_w_in"]
    pieces = []
    t = lo
    i = 0
    while t < hi - 0.5:
        band = g2.strip(origin, along, across, t, t + full)
        piece = g2.clip_convex(band, poly)
        if len(piece) >= 3:
            e = piece @ along
            i += 1
            ends = []
            for where, val in (("one end", e.min()), ("other end", e.max())):
                pts = piece[np.abs(e - val) < 0.5]
                k = _nearest_wall(panel, pts.mean(axis=0))
                ea, eb = panel.edge(k)
                ang = g2.angle_deg(along, eb - ea)
                ang = min(ang, 180 - ang)
                ends.append(EndCut(where, f"the {panel.edge_class[k].lower()} edge, a straight snip",
                                   90.0 - ang if ang > 0.5 else 0.0, 0.0))
            zm = T if opts.mode == "cover" else T - 0.03
            pieces.append(Piece(f"Strip {i}", "metal", "metal", piece, float(e.max() - e.min()),
                                float(e.max() - e.min()), ends=ends, note=note, area_in2=g2.area(piece),
                                spec={"type": "slab", "plan": piece, "z": (zm, zm + 0.03), "bounds": False}))
        t += cover
    fitting = [f"strips {full:.0f} in wide laid {cover:.0f} in apart: each laps the last by one rib "
               f"({full - cover:.0f} in)"]
    return pieces, fitting


# ----------------------------------------------------------------------
# The one entry point
# ----------------------------------------------------------------------

def layout(panel: PanelType, opts: Options) -> Layout:
    opts = valid(opts)
    spec: Spec = panel.spec
    T = spec.thickness_in
    kind = MATERIALS[opts.material][1]
    stocks = sec.stocks(opts.infill_log_in, spec.max_strut_in)
    title = f"{MATERIALS[opts.material][0]} — {ARRANGEMENTS[opts.arrangement]}"
    if opts.lay:
        title += f", {LAYS[opts.lay][0].lower()}"
    steps: list[str] = []
    fitting: list[str] = []
    remainder = None
    nest = None
    placed: list[sec.Placed] = []
    metrics: dict = {}
    z0 = 0.0
    wall = sec.frame_section(spec.radius_in, spec.wall_deg) if opts.mode == "fill" else None

    if kind == "round":
        return _rounds_layout(panel, opts, title)
    if kind in ("sheet", "film"):
        pieces, fitting, nest, thick = _sheet(panel, opts, T)
        metrics = {"pitch": 0.0, "solid": 1.0, "see_through": 0.0}
    elif kind == "metal":
        pieces, fitting = _metal(panel, opts, T)
        metrics = {"pitch": C["metal_cover_in"], "solid": 1.0, "see_through": 0.0}
    else:
        if opts.mode == "cover":
            # Over the open side: the layer starts at the panel's outside edge.
            z0 = T
            if opts.arrangement == "louvers":
                Tlay = T
            else:
                seq = _sequence(stocks, opts)
                Tc = max(float(sec.posed_raw(s, p, 99.0)[:, 1].max()) for s, p in seq)
                Tlay = min(Tc, T) if any(p in ("PD", "PU") for _s, p in seq) else Tc
        else:
            Tlay = T
        k = opts.edge
        a, b = panel.edge(k)
        along = g2.unit(b - a)
        across = panel.inward(k)
        inset0 = panel.inset_at(0.0) if opts.mode == "fill" else spec.gasket_in / 2 - C["cover_overhang_in"]
        origin = a + across * inset0
        if opts.arrangement == "rings" and opts.mode == "fill":
            pieces, placed, metrics, remainder = _rings(panel, opts, stocks, Tlay, wall)
        elif opts.arrangement in ("parallel", "louvers", "rings"):
            pieces, placed, metrics = _straight(panel, opts, stocks, Tlay, z0, along, across, origin,
                                                wall, "Run")
        elif opts.arrangement == "across":
            # Runs square to edge k, stepping along it from its first corner.
            clip = _clip_at(panel, opts, Tlay + z0)
            start = clip[np.argmin(clip @ along)]
            pieces, placed, metrics = _straight(panel, opts, stocks, Tlay, z0, across, along, start,
                                                None, "Run")
        elif opts.arrangement == "chevron":
            apex = panel.tri[(k + 2) % 3]
            foot = a + along * float(np.dot(apex - a, along))
            ax_dir = g2.unit(apex - foot)
            half_n = g2.perp(ax_dir)
            if float(np.dot(half_n, b - a)) < 0:
                half_n = -half_n
            big = 1e4
            pieces, placed = [], []
            for side, kk, sign in (("Left", (k + 2) % 3, -1), ("Right", (k + 1) % 3, 1)):
                ea, eb = panel.edge(kk)
                al = g2.unit(eb - ea)
                ac = panel.inward(kk)
                org = ea + ac * inset0
                half = np.array([foot, foot + ax_dir * big + half_n * sign * big,
                                 foot - ax_dir * big + half_n * sign * big])
                half = g2.hull(np.array([foot + ax_dir * big, foot - ax_dir * big,
                                         foot + ax_dir * big + half_n * sign * big,
                                         foot - ax_dir * big + half_n * sign * big]))
                pcs, pl, metrics = _straight(panel, opts, stocks, Tlay, z0, al, ac, org, wall,
                                             f"{side} run", extra_clip=half,
                                             centre_line=(foot, half_n))
                pieces += pcs
                placed = placed or pl
        else:
            raise ValueError(opts.arrangement)
        if opts.mode == "cover":
            placed = [sec.Placed(p.stock, p.pose, p.poly + np.array([0.0, z0])) for p in placed]
            wall = sec.frame_section(spec.radius_in, spec.wall_deg)

    # -- what it measures -------------------------------------------------------
    clip_poly = _clip_at(panel, opts, T)
    area_open = g2.area(clip_poly)
    metrics = dict(metrics)
    metrics["pieces"] = len(pieces)
    metrics["open_area_in2"] = area_open
    metrics["longest"] = max((p.long for p in pieces), default=0.0)
    metrics["shortest"] = min((p.short for p in pieces), default=0.0)
    if kind in ("log", "board"):
        vol = sum(p.area_in2 * (p.long + p.short) / 2 for p in pieces)
        density = C["green_pine_kg_m3"] if kind == "log" else C["board_kg_m3"]
        metrics["wood_in3"] = vol
        metrics["kg"] = vol * 1.6387e-5 * density
        metrics["linear_in"] = sum(p.long for p in pieces)
    else:
        per_m2 = {"osb": C["osb_kg_m2"], "ply": C["ply_kg_m2"], "film": C["film_kg_m2"],
                  "metal": C["metal_kg_m2"]}[opts.material]
        sheet_area = sum(g2.area(p.plan) for p in pieces)
        metrics["kg"] = sheet_area * 0.00064516 * per_m2
        metrics["sheet_in2"] = sheet_area
    if remainder is not None:
        metrics["remainder_in2"] = g2.area(remainder)
    if kind == "log" and opts.arrangement != "rings":
        metrics.setdefault("remainder_in2", 0.0)

    from .solids import attach
    attach(pieces, panel, opts)
    steps = how_to(panel, opts, pieces, metrics, stocks, remainder, nest, kind)
    fitting = fitting + fit_notes(panel, opts, pieces, metrics, placed, kind, remainder)
    return Layout(title, opts, panel, pieces, placed, wall, T, z0, metrics, steps, fitting,
                  remainder=remainder, clip=clip_poly, nest=nest)


ROUND_POSE = {"full": "whole round", "wall": "round cut along the wall", "graded": "small round in a gap",
              "copy": "copied round, cut to fit the gaps"}


def _rounds_layout(panel: PanelType, opts: Options, title: str) -> Layout:
    from . import rounds as rd
    spec = panel.spec
    T = spec.thickness_in
    cut = opts.leftover == "cut"
    ls = rd.layers(panel, opts.arrangement, opts.lay, opts.infill_log_in, opts.round_t_in,
                   opts.round_min_in, cut, opts.mode)
    pieces = []
    for L in ls:
        for r in L.rounds + L.copies:
            ends = []
            if r.kind == "wall":
                ends = [EndCut("the chord", "the 45° wall: blade tilted to the slope", 0.0,
                               90.0 - spec.wall_deg if opts.mode == "fill" else 0.0)]
            ext = g2.extent_along(r.poly, (1.0, 0.0))
            if r.kind == "copy":
                rspec = {"type": "extrude", "polys": r.shapes, "z": (L.z0 + (0.0 if opts.mode == "fill" else T),
                                                                    L.z1 + (0.0 if opts.mode == "fill" else T))}
            else:
                zoff = 0.0 if opts.mode == "fill" else T
                rspec = {"type": "slab", "plan": rd.circle(r.c, r.r), "z": (L.z0 + zoff, L.z1 + zoff),
                         "bounds": r.kind == "wall"}
            pieces.append(Piece(group=f"Layer {L.index}", material="rounds", pose=r.kind, plan=r.poly,
                                long=2 * r.r, short=min(2 * r.r, ext[1] - ext[0]), ends=ends,
                                note=(f"cut into {r.frags} gap piece(s)" if r.kind == "copy" else
                                      f"{L.z1 - L.z0:g} in thick"), area_in2=r.area, spec=rspec))
    from .solids import attach
    attach(pieces, panel, opts)
    s = rd.summary(ls)
    clip = panel.opening(T) if opts.mode == "fill" else g2.inset_triangle(panel.tri, spec.gasket_in / 2)
    metrics = {"pieces": len(pieces), "open_area_in2": g2.area(clip), "longest": opts.infill_log_in,
               "shortest": min((p.short for p in pieces), default=0.0),
               "kg": s["wood_in3"] * 1.6387e-5 * C["green_pine_kg_m3"], "wood_in3": s["wood_in3"],
               "solid": s["final_cover"], "pattern_cover": s["pattern_cover"], "layers": s["layers"],
               "see_through": 0.0, "pitch": 0.0}
    return Layout(title, opts, panel, pieces, [], None, T, 0.0, metrics,
                  rd.steps(ls, opts.infill_log_in, opts.round_t_in, cut, opts.arrangement, opts.lay),
                  rd.fitting(ls, cut, opts.lay), clip=clip, extra={"layers": ls, "summary": s, "cut": cut})


# ----------------------------------------------------------------------
# Words
# ----------------------------------------------------------------------

def how_to(panel, opts, pieces, metrics, stocks, remainder, nest, kind) -> list[str]:
    s = panel.spec
    out = []
    if kind == "log":
        st = stocks[opts.material]
        out.append(f"Stock: split {opts.infill_log_in:.0f} in logs into eighths with the chainsaw "
                   f"({C['chainsaw_kerf_in']:.3g} in kerf)" +
                   ("." if opts.material == "w8" else
                    f", then bandsaw each eighth down its length into "
                    f"{2 if opts.material == 's16' else 4} slices ({C['bandsaw_kerf_in']:.3g} in kerf), "
                    f"keeping the cuts on the radius so every slice is a true sector."))
        if opts.lay == "shim" and opts.material != "s32":
            out.append("Shims: bandsaw a few eighths into 1/32 slices for the bark-to-bark seams.")
        trims = sorted({round(p.trim, 2) for p in pieces if p.trim > 0.01})
        if trims:
            out.append(f"Rip flush: the standing pieces are taller than the frame; rip "
                       f"{', '.join(f'{t:.2f}' for t in trims)} in off the bark so they sit flush with both faces.")
    elif kind == "board":
        st = stocks[opts.material]
        out.append(f"Stock: {st.label.lower()}s, {st.width:g} x {st.thick:g} in, {st.length / 12:.0f} ft long.")
    if kind in ("log", "board"):
        if opts.arrangement == "rings":
            out.append("Lay the rings from the frame inward. Each ring is a small frame: three pieces in "
                       "the same pinwheel as the frame -- each runs from the far side of the piece behind "
                       "it to the near side of the piece ahead, square-cut both ends in plan.")
        else:
            settings = {}
            for p in pieces:
                for e in p.ends:
                    key = (round(abs(e.mitre), 1), round(abs(e.bevel), 1), e.meets)
                    settings[key] = settings.get(key, 0) + 1
            out.append("Saw settings, held as the piece lies in the panel:")
            for (m, b, meets), n in sorted(settings.items()):
                how = "square" if m == 0 and b == 0 else f"mitre {m:.1f}°, bevel {b:.1f}°"
                out.append(f"   {n} ends: {how} -- {meets}")
        if opts.mode == "fill":
            out.append("Cut each piece to its long length first, then make the end cuts; measure the "
                       "short length on the flat-side face to check.")
    if kind in ("sheet", "film"):
        if kind == "film":
            out.append(f"Cut list: one piece per triangle; off a {C['film_roll_w_in'] / 12:.0f} ft roll, "
                       f"{nest['rows']} row(s) across, turned alternately, each triangle uses "
                       f"{nest['roll_in_per_piece'] / 12:.1f} ft of roll.")
        else:
            out.append(f"Cut list: {len(pieces)} piece(s) per triangle, {nest['per_sheet']} to a 4 x 8 sheet "
                       f"({nest['rows']} rows of {nest['per_row']}, triangles turned alternately).")
        for p in pieces:
            if p.ends:
                out.append(f"   {p.group}: " + "; ".join(e.text() for e in p.ends))
            if p.note:
                out.append(f"   {p.note}")
    if kind == "metal":
        out.append(f"Cut {len(pieces)} strips from {C['metal_l_in'] / 12:.0f} ft panels with snips or a "
                   "nibbler; each end follows the frame edge it meets.")
    if remainder is not None:
        out.append(f"Centre: a triangle {g2.inradius(remainder) * 2:.1f} in across its inscribed circle is "
                   f"left. Fill it with a plug cut from one wedge laid flat, or leave it open as a vent.")
    return out


def fit_notes(panel, opts, pieces, metrics, placed, kind, remainder) -> list[str]:
    out = []
    if kind == "log" and opts.mode == "fill" and placed:
        first = placed[0]
        if first.pose == "FUL" and first.stock.angle_deg == panel.spec.wall_deg:
            out.append("The first piece, flipped, lies flat on the frame's 45° slope: sawn face on sawn face, "
                       "a full-width bearing.")
        elif first.pose in ("FDR", "FDL"):
            out.append("The first piece meets the 45° slope with its bark: it touches along one line, and "
                       "leaves a wedge-shaped gap above it -- caulk it or pack it.")
        elif first.pose in ("PD", "PU"):
            out.append("Standing pieces meet the 45° slope at an angle: the first one's sawn face leans "
                       f"{abs(45 - first.stock.angle_deg / 2):.1f}° off the slope -- plane it to suit, or "
                       "start with a flipped wedge to turn the slope upright.")
        else:
            out.append("The first piece's sawn face is not at the frame's 45°: it bears on a line, not a face.")
        if opts.lay == "flipflop":
            out.append("Every other seam is sawn-to-sawn (tight, full face); the ones between are "
                       "bark-to-bark, touching on a line, with a lens of air either side.")
        if opts.lay == "shim":
            out.append("The thin slice in each bark-to-bark seam fills the lens of air and wedges the next "
                       "full piece tight.")
    if kind in ("log", "board") and opts.arrangement in ("parallel", "across", "chevron", "louvers"):
        corner = [p for p in pieces if p.long < 6.0]
        if corner:
            out.append(f"{len(corner)} pieces near the corners are under 6 in long: cut them from offcuts.")
        out.append("Where a run meets a side wall at an angle, the end is a compound cut: the cut face "
                   "has to lie on the 45° wall, so it is both mitred and bevelled.")
    if opts.arrangement == "louvers":
        out.append(f"Slats tilted {metrics.get('tilt', 0):.0f}°, lapped {metrics.get('lap', 0):.2f} in in plan: "
                   f"no straight line of sight through, but {metrics.get('air_gap', 0):.2f} in of clear air "
                   "between each pair.")
    if opts.lay == "boardonboard":
        out.append("Covered in plan by the lap; air zig-zags between the layers.")
    if metrics.get("see_through", 0) > 0.005:
        out.append(f"{100 * metrics['see_through']:.0f}% of the run can be seen straight through: light and air pass.")
    return out


def validate_patterns() -> None:
    from .frame import solve
    spec = Spec()
    types = solve(spec)["types"]
    for panel in types:
        for mat, (name, kind) in MATERIALS.items():
            o = OPTIONS[kind]
            for arr in o["arrangements"]:
                for lay in ((o["lays"] if arr != "louvers" else []) or [""]):
                    for mode in ("fill", "cover"):
                        if arr == "rings" and mode == "cover":
                            continue
                        L = layout(panel, Options(mat, arr, lay, mode))
                        assert L.pieces, (panel.name, mat, arr, lay, mode)
                        for p in L.pieces:
                            assert np.all(np.isfinite(p.plan)) and p.long >= p.short >= 0, (mat, arr, lay)
                            assert p.long < spec.max_strut_in * 1.5 or kind in ("sheet", "film", "metal")
    # A run parallel to the base ends on the side walls with a compound cut.
    L = layout(types[1], Options("w8", "parallel", "flipflop", "fill"))
    mid = L.pieces[len(L.pieces) // 2]
    assert all(abs(e.bevel) > 20 and abs(e.mitre) > 10 for e in mid.ends), mid.cut_text
    # Rounds: cutting to fit only ever adds cover; offset layers break the gaps.
    from . import rounds as rd
    panel = types[1]
    for pat in ("hex", "square", "graded"):
        ls = rd.layers(panel, pat, "aligned", 12.0, 1.5, 3.0, True, "fill")
        s_ = rd.summary(ls)
        assert s_["final_cover"] >= s_["pattern_cover"] > 0.5, (pat, s_)
        assert all(r.kind in ("full", "wall", "graded") for L in ls for r in L.rounds)
    def shared_gaps(stacking):
        ls = rd.layers(panel, "hex", stacking, 12.0, 2.0, 3.0, False, "fill")
        grid = rd.Grid(panel.opening(1.0))
        g1 = grid.inside & ~rd._covered(grid, ls[0].rounds)
        g2_ = grid.inside & ~rd._covered(grid, ls[1].rounds)
        return float((g1 & g2_).sum()) / max(1.0, float(g1.sum()))
    assert shared_gaps("offset") < shared_gaps("aligned"), "offset layers cover the gaps below"
    # Rings close in on the middle and leave a plug or nothing.
    R = layout(types[1], Options("w8", "rings", "flipflop", "fill"))
    assert len(R.pieces) % 3 == 0 and len(R.pieces) >= 3
