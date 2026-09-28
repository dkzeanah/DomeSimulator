"""The seam channel, measured: how much room there is and what fits in it.

Every seam of the wedge dome is a V. Two sawn faces -- one from each panel's
member -- meet at a ridge on the outside and open toward the inside of the
dome, at an included angle of the sector angle less the fold between the two
panels. The key fills that V. Make the key hollow and the V becomes a
service channel running the length of every seam: water, wire, the
condensate drain and the air of :mod:`wedge_book.systems`'s seam module.

Everything here is derived from the raw-wedge solver's own seams
(``SeamInfo``: fold angle, gap angle, contact depth, opening width) for the
book's reference build -- a 12 in log, the seed dome's 72 in long edge --
except the sizes of the things that go *in* the channel, which cannot be
derived and are declared in :data:`SERVICES` and :data:`KEY_CONSTANTS` with
a reason each.

Three answers the film has to give, including the one that does not help:

* **Water and wire fit.** A 1/2 in PEX line, a 14/2 cable, the Peltier
  pair and the condensate drain go into one seam's key together.
* **Ducted air does not.** The largest round thing the key holds is smaller
  than the smallest common duct. The channel itself is the air path, or the
  key becomes a spacer.
* **A spacer costs a bigger dome.** Opening the seams far enough for a duct
  means moving every panel outward, which :func:`spacer_for` sizes.

    py -3.12 -m two_v_demo.channel_facts        # the whole report
"""

from __future__ import annotations

import math
from dataclasses import dataclass
from functools import lru_cache

IN3_TO_CM3 = 16.387064
MM_PER_IN = 25.4


# ----------------------------------------------------------------------
# Declared: what goes in the channel, and how a key is made
# ----------------------------------------------------------------------

@dataclass(frozen=True)
class Service:
    key: str
    label: str
    shape: str          # round | flat
    width_in: float     # outside diameter, or the flat cable's width
    thick_in: float     # the flat cable's thickness; 0 for round
    source: str

    @property
    def area_in2(self) -> float:
        if self.shape == "round":
            return math.pi * self.width_in ** 2 / 4.0
        # A flat cable is a stadium: a rectangle with round ends.
        r = self.thick_in / 2.0
        return (self.width_in - self.thick_in) * self.thick_in + math.pi * r * r

    @property
    def span_in(self) -> float:
        """The size that has to clear the channel's narrowest round opening."""
        return self.width_in


SERVICES: tuple[Service, ...] = (
    Service("pex_half", "1/2 in PEX water line", "round", 0.625, 0.0,
            "nominal: copper-tube-size outside diameter of 1/2 in PEX (ASTM F876)"),
    Service("pex_three_quarter", "3/4 in PEX water line", "round", 0.875, 0.0,
            "nominal: copper-tube-size outside diameter of 3/4 in PEX (ASTM F876)"),
    Service("nm_14_2", "14/2 NM-B cable, 15 A circuit", "flat", 0.40, 0.20,
            "estimate: typical outside size of 14/2 with ground; brands differ"),
    Service("nm_12_2", "12/2 NM-B cable, 20 A circuit", "flat", 0.46, 0.22,
            "estimate: typical outside size of 12/2 with ground; brands differ"),
    Service("peltier_pair", "12 V pair to the Peltier plates, 14 AWG", "round", 0.30, 0.0,
            "estimate: a jacketed two-conductor 14 AWG cable"),
    Service("drain", "condensate drain, 1/4 in ID vinyl", "round", 0.375, 0.0,
            "nominal: 1/4 in inside x 3/8 in outside tubing"),
    Service("duct_3", "3 in round air duct", "round", 3.0, 0.0,
            "nominal: the smallest common residential exhaust duct"),
    Service("duct_4", "4 in round air duct", "round", 4.0, 0.0,
            "nominal: the usual bathroom-fan duct"),
)
SERVICE = {s.key: s for s in SERVICES}

BUNDLE = ("pex_half", "nm_14_2", "peltier_pair", "drain")
"""What one fitted seam carries: water, a circuit, the plates' power, the drain."""

KEY_CONSTANTS: tuple[tuple[str, float, str, str], ...] = (
    ("fill_fraction", 0.40, "of area",
     "rule borrowed from conduit fill (NEC Chapter 9, Table 1): more than two "
     "conductors may fill 40% of a raceway. Used here as the packing allowance "
     "for a mixed bundle -- the channel is not a listed raceway"),
    ("key_wall_in", 3.0 / MM_PER_IN, "in",
     "assumption: a printed key wall of 3 mm, stiff enough to carry the bolt "
     "bosses and the clips"),
    ("printer_bed_in", 250.0 / MM_PER_IN, "in",
     "assumption: the longest axis of a common desktop printer, 250 mm"),
    ("filament_g_per_cm3", 1.27, "g/cm3",
     "nominal: density of PETG, which takes outdoor heat better than PLA"),
    ("filament_usd_per_kg", 20.0, "USD/kg",
     "assumption: a spool of PETG bought by the kilogram"),
    ("print_mm3_per_s", 15.0, "mm3/s",
     "assumption: a 0.4 mm nozzle laying walls at a brisk but reliable speed"),
    ("quiet_air_fpm", 400.0, "ft/min",
     "rule of thumb: keep air in a small residential duct under about 400 to "
     "600 ft/min or it is heard; the low end is used"),
    ("log_diameters_in", 0.0, "in",
     "the diameters the capacity-by-log table is drawn for: 10, 12, 15, 18 in "
     "(listed in LOG_DIAMETERS_IN)"),
)
K = {name: value for name, value, _u, _w in KEY_CONSTANTS}
LOG_DIAMETERS_IN = (10.0, 12.0, 15.0, 18.0)


# ----------------------------------------------------------------------
# The solver's seams, for the reference build
# ----------------------------------------------------------------------

@lru_cache(maxsize=4)
def reference_model(trunk_diameter_in: float | None = None):
    import seed_model
    import seed_world

    from . import raw_wedge_bridge as bridge

    trunk = trunk_diameter_in or seed_model.SEED_TRUNK_DIAMETER_IN
    return bridge.model("point_dome_in", long_edge_in=seed_world.geometry().long_edge_in,
                        trunk_diameter_in=trunk)


@dataclass(frozen=True)
class SeamType:
    """One of the dome's two seam profiles."""

    fold_deg: float          # the angle between the two panels' planes
    gap_deg: float           # the V's included angle: sector angle - fold
    count: int
    edge_types: str
    length_in: float         # mean seam length
    depth_in: float          # the sawn face's length: the log's radius
    opening_in: float        # the V's width at the inside, from the solver
    hose_in: float           # the solver's largest hose touching both faces
    nose_in: float           # the key starts this far down the faces


@lru_cache(maxsize=4)
def seam_types(trunk_diameter_in: float | None = None) -> tuple[SeamType, ...]:
    import numpy as np

    model = reference_model(trunk_diameter_in)
    groups: dict[float, list] = {}
    for seam in model.seams:
        groups.setdefault(round(seam.fold_angle_deg, 3), []).append(seam)
    out = []
    for fold, seams in sorted(groups.items()):
        out.append(SeamType(
            fold_deg=float(np.mean([s.fold_angle_deg for s in seams])),
            gap_deg=float(np.mean([s.raw_gap_angle_deg for s in seams])),
            count=len(seams),
            edge_types="".join(sorted({s.edge_type for s in seams})),
            length_in=float(np.mean([np.linalg.norm(s.end - s.start) for s in seams])),
            depth_in=float(seams[0].contact_depth_in),
            opening_in=float(np.mean([s.spacer_base_width_in for s in seams])),
            hose_in=float(np.mean([s.hose_max_diameter_in for s in seams])),
            nose_in=float(model.config.trapezoid_nose_depth_in)))
    return tuple(out)


# ----------------------------------------------------------------------
# Cross-sections: a convex polygon per profile
# ----------------------------------------------------------------------

def v_polygon(t: SeamType, spacer_in: float = 0.0, nose_in: float = 0.0):
    """The V (or, with a spacer, the flat-topped V) in the seam's cross-section.

    x runs across the seam, y outward; the ridge is at y = 0 and the V opens
    downward, toward the inside of the dome. ``nose_in`` cuts the tip off,
    as the key does, measured down the faces.
    """
    h = math.radians(t.gap_deg / 2.0)
    s = spacer_in / 2.0
    top = [(-s - nose_in * math.sin(h), -nose_in * math.cos(h)),
           (s + nose_in * math.sin(h), -nose_in * math.cos(h))]
    bottom = [(s + t.depth_in * math.sin(h), -t.depth_in * math.cos(h)),
              (-s - t.depth_in * math.sin(h), -t.depth_in * math.cos(h))]
    poly = top + bottom
    if spacer_in == 0.0 and nose_in == 0.0:
        poly = [(0.0, 0.0)] + bottom
    return [tuple(p) for p in poly]


def area(poly) -> float:
    return abs(sum(x0 * y1 - x1 * y0 for (x0, y0), (x1, y1)
                   in zip(poly, poly[1:] + poly[:1]))) / 2.0


def perimeter(poly) -> float:
    return sum(math.dist(a, b) for a, b in zip(poly, poly[1:] + poly[:1]))


def _ccw(poly):
    signed = sum(x0 * y1 - x1 * y0 for (x0, y0), (x1, y1) in zip(poly, poly[1:] + poly[:1]))
    return poly if signed > 0 else list(reversed(poly))


def inset(poly, d: float):
    """A convex polygon moved in by ``d`` on every side -- the key's inside."""
    poly = _ccw(poly)
    n = len(poly)
    lines = []
    for i in range(n):
        (x0, y0), (x1, y1) = poly[i], poly[(i + 1) % n]
        ex, ey = x1 - x0, y1 - y0
        length = math.hypot(ex, ey)
        nx, ny = -ey / length, ex / length       # inward for a CCW polygon
        lines.append(((x0 + nx * d, y0 + ny * d), (ex, ey)))
    out = []
    for i in range(n):
        (p, r), (q, s) = lines[i - 1], lines[i]
        cross = r[0] * s[1] - r[1] * s[0]
        u = ((q[0] - p[0]) * s[1] - (q[1] - p[1]) * s[0]) / cross
        out.append((p[0] + r[0] * u, p[1] + r[1] * u))
    return out


def incircle_diameter(poly) -> float:
    """The largest circle inside a polygon symmetric about x = 0."""
    poly = _ccw(poly)
    edges = list(zip(poly, poly[1:] + poly[:1]))
    ys = [p[1] for p in poly]

    def clearance(y: float) -> float:
        best = float("inf")
        for (x0, y0), (x1, y1) in edges:
            ex, ey = x1 - x0, y1 - y0
            # signed distance from (0, y) to the edge line, positive inside
            best = min(best, (ex * (y - y0) - ey * (0.0 - x0)) / math.hypot(ex, ey))
        return best
    lo, hi = min(ys), max(ys)
    for _ in range(80):                    # the clearance is concave in y
        a, b = lo + (hi - lo) / 3, hi - (hi - lo) / 3
        if clearance(a) < clearance(b):
            lo = a
        else:
            hi = b
    return 2.0 * max(0.0, clearance((lo + hi) / 2))


# ----------------------------------------------------------------------
# The answers
# ----------------------------------------------------------------------

@dataclass(frozen=True)
class Room:
    """How much room one seam profile offers."""

    seam: SeamType
    spacer_in: float
    v_area_in2: float           # the whole V
    key_outer_in2: float        # the key's outline (V less its nose)
    inside_in2: float           # inside the key's walls: the service space
    inside_round_in: float      # largest round thing inside the key
    equal_area_duct_in: float   # a round duct of the same area as the inside
    wall_in2: float             # plastic in the key's cross-section

    @property
    def usable_in2(self) -> float:
        return self.inside_in2 * K["fill_fraction"]


def room(t: SeamType, spacer_in: float = 0.0) -> Room:
    v = v_polygon(t, spacer_in)
    outer = v_polygon(t, spacer_in, t.nose_in)
    inner = inset(outer, K["key_wall_in"])
    a_inner = area(inner)
    return Room(seam=t, spacer_in=spacer_in, v_area_in2=area(v),
                key_outer_in2=area(outer), inside_in2=a_inner,
                inside_round_in=incircle_diameter(inner),
                equal_area_duct_in=math.sqrt(4.0 * a_inner / math.pi),
                wall_in2=area(outer) - a_inner)


@dataclass(frozen=True)
class Fit:
    service: Service
    fits_alone: bool


def fits(r: Room, keys=BUNDLE) -> tuple[list[Fit], float, bool]:
    """Each item against the inside's round opening, and the bundle against the fill rule."""
    items = [SERVICE[k] for k in keys]
    each = [Fit(s, s.span_in <= r.inside_round_in) for s in items]
    fill = sum(s.area_in2 for s in items) / r.inside_in2
    return each, fill, all(f.fits_alone for f in each) and fill <= K["fill_fraction"]


def spacer_needed(t: SeamType, keys) -> float:
    """The narrowest spacer that lets ``keys`` fit this profile, by the rules above."""
    def ok(s: float) -> bool:
        return fits(room(t, s), keys)[2]
    if ok(0.0):
        return 0.0
    lo, hi = 0.0, 1.0
    while not ok(hi):
        hi *= 2.0
    for _ in range(60):
        mid = (lo + hi) / 2
        lo, hi = (lo, mid) if ok(mid) else (mid, hi)
    return hi


@dataclass(frozen=True)
class Spacer:
    """Opening every seam: panels move out along their normals by ``shift_in``."""

    keys: tuple[str, ...]
    needed_in: tuple[float, ...]     # per seam type, before rounding up to one shift
    shift_in: float                  # how far every panel moves out
    actual_in: tuple[float, ...]     # the spacer each seam type then gets
    radius_in: float
    radius_growth_pct: float
    rooms: tuple[Room, ...]


def spacer_for(keys) -> Spacer:
    """The panel shift that opens *every* seam enough for ``keys``.

    A panel moved out along its own normal by d separates from its
    neighbour, across the seam, by 2 d sin(fold / 2). The two seam types
    have different folds, so one shift gives them different spacers; the
    shift is set by whichever type needs it most.
    """
    import seed_world

    types = seam_types()
    needed = tuple(spacer_needed(t, keys) for t in types)
    shift = max(s / (2.0 * math.sin(math.radians(t.fold_deg / 2.0)))
                for s, t in zip(needed, types))
    actual = tuple(2.0 * shift * math.sin(math.radians(t.fold_deg / 2.0)) for t in types)
    radius = seed_world.geometry().radius_in
    return Spacer(tuple(keys), needed, shift, actual, radius, 100.0 * shift / radius,
                  tuple(room(t, s) for t, s in zip(types, actual)))


@dataclass(frozen=True)
class Hubs:
    by_valence: tuple[tuple[str, int], ...]   # ("5-way", 6), ...
    node_radius_in: tuple[tuple[int, float], ...]  # (faces meeting, node circumradius) at a shift


def hubs(shift_in: float = 0.0) -> Hubs:
    """Where the channels meet, and how big a node the spacer's shift opens there."""
    import numpy as np

    model = reference_model()
    topo = model.topology
    faces_at: dict[int, list] = {}
    for face in topo.faces:
        for v in face.vertices:
            faces_at.setdefault(v, []).append(face)
    rim = {v for e in topo.edges.values() if e.is_base for v in e.key}
    counts: dict[str, int] = {}
    radii: dict[int, list[float]] = {}
    for v, faces in faces_at.items():
        label = "rim" if v in rim else f"{len(faces)}-way"
        counts[label] = counts.get(label, 0) + 1
        if v in rim or shift_in <= 0:
            continue
        corners = np.array([topo.vertices[v] + shift_in * f.normal for f in faces])
        centre = corners.mean(axis=0)
        radii.setdefault(len(faces), []).append(float(np.linalg.norm(corners - centre, axis=1).mean()))
    order = sorted(counts, key=lambda k: (k == "rim", k))
    return Hubs(tuple((k, counts[k]) for k in order),
                tuple((k, float(np.mean(r))) for k, r in sorted(radii.items())))


@dataclass(frozen=True)
class Printing:
    """Half-keys: every member carries half of its seam's key."""

    half_keys: int
    profiles: int
    segments: int
    segments_each: tuple[int, ...]   # per seam type
    plastic_in3: float
    mass_kg: float
    cost_usd: float
    print_hours: float


def printing(spacer_in: float = 0.0) -> Printing:
    types = seam_types()
    bed = K["printer_bed_in"]
    half_keys = segments = 0
    volume = 0.0
    per_type = []
    for t in types:
        r = room(t, spacer_in)
        n_half = 2 * t.count
        each = math.ceil(t.length_in / bed)
        per_type.append(each)
        half_keys += n_half
        segments += n_half * each
        volume += n_half * (r.wall_in2 / 2.0) * t.length_in
    cm3 = volume * IN3_TO_CM3
    kg = cm3 * K["filament_g_per_cm3"] / 1000.0
    hours = cm3 * 1000.0 / K["print_mm3_per_s"] / 3600.0
    return Printing(half_keys, len(types), segments, tuple(per_type), volume, kg,
                    kg * K["filament_usd_per_kg"], hours)


def air() -> dict:
    """The channel as the air path itself, against what the dome needs."""
    from wedge_book import systems

    need = systems.air_barrier()
    out = {"need_cfm": need["cfm"], "per_type": []}
    for t in seam_types():
        r = room(t)
        _each, fill, _ok = fits(r)
        free_in2 = r.inside_in2 * (1.0 - fill)
        cfm = free_in2 / 144.0 * K["quiet_air_fpm"]
        out["per_type"].append({"seam": t, "free_in2": free_in2, "cfm": cfm,
                                "seams_for_the_dome": need["cfm"] / cfm})
    return out


def by_log() -> list[tuple[float, float, float]]:
    """(log diameter, inside area, largest round) for the tighter seam type."""
    out = []
    for d in LOG_DIAMETERS_IN:
        tight = min(seam_types(d), key=lambda t: t.gap_deg)
        r = room(tight)
        out.append((d, r.inside_in2, r.inside_round_in))
    return out


def report() -> str:
    types = seam_types()
    lines = ["THE SEAM CHANNEL -- reference build: "
             f"{reference_model().config.trunk_diameter_in:.0f} in log", ""]
    for t in types:
        r = room(t)
        each, fill, ok = fits(r)
        lines += [f"seam profile: fold {t.fold_deg:.2f} deg, V {t.gap_deg:.2f} deg, "
                  f"{t.count} seams ({t.edge_types}), {t.length_in:.1f} in long",
                  f"  V depth {t.depth_in:.2f} in, opening {t.opening_in:.2f} in, "
                  f"V area {r.v_area_in2:.2f} in2",
                  f"  inside the key {r.inside_in2:.2f} in2, largest round "
                  f"{r.inside_round_in:.2f} in, equal-area duct {r.equal_area_duct_in:.2f} in",
                  f"  bundle fill {fill * 100:.0f}% -> {'fits' if ok else 'does NOT fit'}"]
        lines += [f"    {f.service.label:<42} {'yes' if f.fits_alone else 'no'}" for f in each]
    for keys in (("duct_3",), ("duct_4",), BUNDLE + ("duct_4",)):
        sp = spacer_for(keys)
        lines += ["", f"spacer for {', '.join(keys)}: panels out {sp.shift_in:.2f} in, "
                      f"seams open {', '.join(f'{a:.2f}' for a in sp.actual_in)} in, "
                      f"dome radius +{sp.radius_growth_pct:.1f}%"]
    h = hubs(spacer_for(("duct_4",)).shift_in)
    lines += ["", "hubs: " + ", ".join(f"{n} {k}" for k, n in h.by_valence),
              "  node radius with the 4 in duct spacer: "
              + ", ".join(f"{k}-way {r:.2f} in" for k, r in h.node_radius_in)]
    p = printing()
    lines += ["", f"printing: {p.half_keys} half-keys, {p.profiles} profiles, "
                  f"{p.segments} segments, {p.mass_kg:.1f} kg, ${p.cost_usd:,.0f}, "
                  f"{p.print_hours:,.0f} h"]
    a = air()
    lines += ["", f"air: dome needs {a['need_cfm']:.1f} cfm"] + [
        f"  profile {x['seam'].gap_deg:.1f} deg: {x['cfm']:.1f} cfm per seam with the "
        f"bundle in, {x['seams_for_the_dome']:.1f} seams carry the dome" for x in a["per_type"]]
    lines += ["", "by log: " + "; ".join(f"{d:.0f} in -> {ai:.1f} in2, round {rd:.2f} in"
                                         for d, ai, rd in by_log())]
    return "\n".join(lines)


def validate_channel() -> None:
    types = seam_types()
    assert len(types) == 2, "a 2V dome closes with two seam profiles"
    for t in types:
        # The solver's identity: fold + V angle = the sector angle.
        assert abs(t.fold_deg + t.gap_deg - 45.0) < 1e-6
        # The V's opening agrees with the solver's own spacer base width.
        h = math.radians(t.gap_deg / 2)
        assert abs(2 * t.depth_in * math.sin(h) - t.opening_in) < 1e-6
        r = room(t)
        assert 0 < r.inside_in2 < r.key_outer_in2 < r.v_area_in2
        assert r.inside_round_in < t.hose_in, "the key's walls cost room"
        # An inset triangle's incircle is the V's incircle less the wall.
        v = v_polygon(t)
        assert abs(incircle_diameter(inset(v, 0.1)) - (incircle_diameter(v) - 0.2)) < 1e-6
    # Opening the seam only ever adds room.
    t = types[0]
    assert room(t, 0.5).inside_in2 > room(t).inside_in2
    sp = spacer_for(("duct_4",))
    assert all(a >= n - 1e-9 for a, n in zip(sp.actual_in, sp.needed_in))
    assert all(r.inside_round_in >= SERVICE["duct_4"].width_in - 1e-6 for r in sp.rooms)
    h = hubs()
    assert sum(n for _k, n in h.by_valence) == 26
    assert printing().half_keys == 2 * sum(t.count for t in types)


def spec_markdown() -> str:
    """The channel as a reference sheet: every figure from the functions above."""
    import seed_world

    types = seam_types()
    out = ["# The seam channel: specification", "",
           f"Reference build: {reference_model().config.trunk_diameter_in:.0f} in log, "
           f"{seed_world.geometry().long_edge_in:.0f} in long edge, "
           f"{sum(t.count for t in types)} seams. Generated by "
           "`py -3.12 -m two_v_demo.channel_facts --md` from the raw-wedge solver; do not "
           "edit by hand.", "",
           "## Room in each seam profile", "",
           "| | " + " | ".join(f"fold {t.fold_deg:.2f} deg ({t.count} seams, {t.edge_types})"
                             for t in types) + " |",
           "|---|" + "---|" * len(types)]
    rooms = [room(t) for t in types]
    for label, fn in (
            ("V angle", lambda t, r: f"{t.gap_deg:.2f} deg"),
            ("depth (log radius)", lambda t, r: f"{t.depth_in:.2f} in"),
            ("opening at the room side", lambda t, r: f"{t.opening_in:.2f} in"),
            ("seam length", lambda t, r: f"{t.length_in:.1f} in"),
            ("whole V", lambda t, r: f"{r.v_area_in2:.2f} sq in"),
            ("inside the key", lambda t, r: f"{r.inside_in2:.2f} sq in"),
            ("usable at the fill allowance", lambda t, r: f"{r.usable_in2:.2f} sq in"),
            ("largest round item", lambda t, r: f"{r.inside_round_in:.2f} in"),
            ("equal-area duct", lambda t, r: f"{r.equal_area_duct_in:.2f} in")):
        out.append(f"| {label} | " + " | ".join(fn(t, r) for t, r in zip(types, rooms)) + " |")
    out += ["", "## What fits", "",
            "| item | size | source | " + " | ".join(f"{t.gap_deg:.1f} deg seam" for t in types) + " |",
            "|---|---|---|" + "---|" * len(types)]
    for s in SERVICES:
        size = f"{s.width_in:.3f} in" + (f" x {s.thick_in:.2f} in" if s.thick_in else " OD")
        cells = ["fits" if s.span_in <= r.inside_round_in else "**no**" for r in rooms]
        out.append(f"| {s.label} | {size} | {s.source} | " + " | ".join(cells) + " |")
    out += ["", "The standard bundle -- " + ", ".join(SERVICE[k].label for k in BUNDLE) + " -- fills "
            + " and ".join(f"{fits(r)[1] * 100:.0f}%" for r in rooms)
            + f" of the inside, against a {K['fill_fraction'] * 100:.0f}% allowance.", ""]
    a = air()
    out += ["## Air", "", f"The dome's ventilation needs {a['need_cfm']:.1f} cfm. With the bundle "
            f"inside, one seam moves " + " / ".join(f"{x['cfm']:.1f}" for x in a["per_type"])
            + f" cfm at {K['quiet_air_fpm']:.0f} ft/min, so "
            f"{math.ceil(max(x['seams_for_the_dome'] for x in a['per_type']))} seams carry the "
            "building. The channel is the duct.", "",
            "## The key as a spacer", "",
            "| to fit | panels move out | seams open (ridge) | dome radius |", "|---|---|---|---|"]
    for keys in (("duct_3",), ("duct_4",), BUNDLE + ("duct_4",)):
        sp = spacer_for(keys)
        out.append(f"| {' + '.join(SERVICE[k].label for k in keys)} | {sp.shift_in:.2f} in | "
                   + " / ".join(f"{x:.2f}" for x in sp.actual_in) + f" in | +{sp.radius_growth_pct:.1f}% |")
    sp4 = spacer_for(("duct_4",) + BUNDLE)
    h = hubs(sp4.shift_in)
    p = printing()
    out += ["", "## Hubs (service junctions; the frame itself stays hubless)", "",
            ", ".join(f"{n} {k}" for k, n in h.by_valence) + ". As built the channels close to a "
            "point at each vertex: fit a printed rosette junction box on the inside of the vertex. "
            "With the 4 in duct spacer each vertex opens to a node "
            + ", ".join(f"{2 * r:.1f} in across ({k}-way)" for k, r in h.node_radius_in) + ".", "",
            "## Making the key", "",
            "1. **Profile.** One per seam type: the V less its nose, "
            f"{types[0].nose_in:.2f} in down the faces, with {K['key_wall_in'] * MM_PER_IN:.0f} mm walls.",
            "2. **Split it** on the seam's centre plane. Each member carries its own half, screwed "
            "to its sawn face before the panel is built; two panels meeting close the channel.",
            f"3. **Print** in pieces no longer than the bed ({K['printer_bed_in'] * MM_PER_IN:.0f} mm): "
            + ", ".join(f"{n} per stick" for n in p.segments_each) + ", joined end to end.",
            f"4. **Whole dome:** {p.half_keys} half-keys, {p.profiles} profiles, {p.segments} pieces, "
            f"{p.mass_kg:.0f} kg of PETG, about ${p.cost_usd:,.0f}, {p.print_hours:,.0f} printer hours. "
            f"**Per seam:** {p.mass_kg / sum(t.count for t in types):.1f} kg, "
            f"{p.print_hours / sum(t.count for t in types):.0f} h. Print the seams that carry "
            "services; cut solid keys from the offcuts for the rest.",
            "5. **Bolts** cross near the ridge, where the V is narrowest; route services in the "
            "wide belly below them.",
            "6. **No pressure fittings inside a seam.** Run PEX continuous; make every joint in a "
            "rosette you can open. Whether cable may run in this chase is the inspector's call.",
            "", "## Assumptions", ""]
    out += [f"- **{name}** = {value:g} {unit} -- {why}" for name, value, unit, why in KEY_CONSTANTS
            if name != "log_diameters_in"]
    return "\n".join(out) + "\n"


if __name__ == "__main__":
    import sys

    validate_channel()
    if "--md" in sys.argv:
        from pathlib import Path

        path = Path(__file__).resolve().parent.parent / "docs" / "seam-channel-spec.md"
        path.write_text(spec_markdown(), encoding="utf-8")
        print(f"wrote {path}")
    else:
        print(report())
