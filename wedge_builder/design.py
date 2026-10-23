"""From a buyer's request to a solved, grouped, stock-planned wedge dome.

Every length and angle here is read from the live solver's model. What this module adds is
grouping (120 members into the few families a builder actually cuts), the log plan (which
wedges come from which round of which log), and the declared allowances those plans need.
"""

from __future__ import annotations

import datetime as dt
import hashlib
import json
import math
import subprocess
from dataclasses import asdict, dataclass, field
from functools import lru_cache
from pathlib import Path

import numpy as np

from infill.stock import CROSSCUT_KERF as KERF_IN

ROOT = Path(__file__).resolve().parent.parent

ORIENTATIONS = {
    "point_dome_in": "Point to the dome's centre",
    "point_panel_in": "Point to the panel's centre",
    "point_dome_out": "Point to the sky",
    "point_panel_out": "Point across the seam",
}
SEAM_JOINS = {
    "raw_trapezoid": "Raw faces with a trapezoid key",
    "shaved_flat": "Shaved faces with a flat key",
}

# What a request may ask for. The limits are the range the solver has been checked over
# by selftest, not a structural limit: nothing here says a dome of any size will stand.
LIMITS = {
    "diameter_ft": (8.0, 40.0),
    "log_in": (4.0, 24.0),
    "log_ft": (4.0, 60.0),
}


DEFAULT_LOG_FT = 16.0  # declared: a common sawlog length, only the order form's starting value


def defaults() -> dict:
    """The order form's starting values: the book's own seed dome and its log."""
    import seed_model
    return {"diameter_ft": round(2 * seed_model.SEED_LONG_EDGE_IN * _edge_per_radius() / 12.0, 1),
            "log_in": float(seed_model.SEED_TRUNK_DIAMETER_IN), "log_ft": DEFAULT_LOG_FT,
            "orientation": "point_dome_in", "seam_join": "raw_trapezoid"}


@dataclass(frozen=True)
class Request:
    """What the buyer types. ``diameter_ft`` is the floor's vertex-to-vertex diameter."""
    diameter_ft: float
    log_in: float
    log_ft: float
    orientation: str = "point_dome_in"
    seam_join: str = "raw_trapezoid"
    label: str = ""

    @classmethod
    def from_json(cls, data: dict) -> "Request":
        def number(key: str) -> float:
            try:
                value = float(data[key])
            except (KeyError, TypeError, ValueError):
                raise ValueError(f"{key} must be a number") from None
            lo, hi = LIMITS[key]
            if not math.isfinite(value) or not lo <= value <= hi:
                raise ValueError(f"{key} must be between {lo:g} and {hi:g}")
            return value
        orientation = str(data.get("orientation") or "point_dome_in")
        seam = str(data.get("seam_join") or "raw_trapezoid")
        if orientation not in ORIENTATIONS:
            raise ValueError("orientation must be one of " + ", ".join(ORIENTATIONS))
        if seam not in SEAM_JOINS:
            raise ValueError("seam_join must be one of " + ", ".join(SEAM_JOINS))
        label = " ".join(str(data.get("label") or "").split())[:60]
        return cls(number("diameter_ft"), number("log_in"), number("log_ft"), orientation, seam, label)

    def key(self) -> str:
        """The design's id: the same request always solves to the same dome."""
        raw = json.dumps({k: round(float(v), 6) if isinstance(v, (int, float)) else v
                          for k, v in asdict(self).items() if k != "label"}, sort_keys=True)
        return hashlib.sha256(raw.encode()).hexdigest()[:10]


@dataclass
class Family:
    """Members that take exactly the same two cuts: one batch on the saw bench."""
    name: str
    edge_type: str
    count: int
    nominal_in: float
    finished_in: float
    raw_blank_in: float
    butt_setup: str
    butt_mitre_deg: float
    butt_bevel_deg: float
    head_yaw_deg: float
    head_pitch_deg: float
    members: list[str] = field(default_factory=list)


@dataclass
class Round:
    """One crosscut length of log, split into ``splits`` wedges."""
    number: int
    log: int
    length_in: float
    wedges: dict[str, int]          # family -> how many of this round's wedges it takes
    spare: int
    green_lb: float


@dataclass
class Design:
    request: Request
    model: object
    sim: object
    long_edge_in: float
    radius_in: float
    floor_area_sqft: float
    families: list[Family]
    setups: list[dict]
    family_of: dict[str, str]
    rounds: list[Round]
    logs: list[list[Round]]
    variants: list[list[int]]       # panels (0-based) sharing one jig, largest group first
    seams: list[dict]
    infill: dict
    checks: list[tuple[str, bool, str]]
    provenance: dict

    @property
    def config(self):
        return self.model.config

    @property
    def allowance_in(self) -> float:
        return self.config.jig_butt_hangoff_in + self.config.head_overfit_in

    def constants(self) -> list[tuple[str, str, str, str]]:
        """Every value on these pages that the solver does not derive: (name, value, kind, why)."""
        c = self.config
        return [
            ("Butt-end tail (jig hang-off)", inches(c.jig_butt_hangoff_in), "declared allowance",
             "Raw stock past the butt plane so the fixture can hold the stick while it is flush-cut. Becomes offcut."),
            ("Head-end overfit", inches(c.head_overfit_in), "declared allowance",
             "Left long so the head is sawn in place on the jig. Absorbs stock and angle error. Becomes offcut."),
            ("Crosscut kerf", inches(KERF_IN), "declared allowance", "Lost between two rounds cut from one log (a chainsaw takes more: add it)."),
            ("Radial splits per round", str(c.radial_splits), "solver input", "Each round is split into this many equal wedges."),
            ("Green wood density", f"{c.green_wood_density_lb_ft3:g} lb/ft3", "estimate", "For the weight of a round you have to lift. Species varies widely."),
            ("Dry wood density", f"{c.dry_wood_density_lb_ft3:g} lb/ft3", "estimate", "For the weight of the finished frame."),
            ("Trapezoid key nose", inches(c.trapezoid_nose_depth_in), "declared", "How far the seam key is truncated (raw trapezoid joins)."),
            ("Flat key", f"{inches(c.flat_key_width_in)} x {inches(c.flat_key_depth_in)}", "declared", "Key section for shaved-flat seams."),
            ("Uniform log", f"{self.request.log_in:g} in", "assumption",
             "The solver cuts every wedge from a perfectly round log of this diameter. Measure the SMALL end of your logs."),
        ]


def inches(x: float) -> str:
    """Decimal inches plus the nearest sixteenth, the way a tape is read."""
    sixteenths = round(x * 16)
    whole, rest = divmod(abs(sixteenths), 16)
    sign = "-" if sixteenths < 0 else ""
    if rest == 0:
        frac = f"{whole}"
    else:
        g = math.gcd(rest, 16)
        frac = f"{whole} {rest // g}/{16 // g}" if whole else f"{rest // g}/{16 // g}"
    return f'{x:.3f}" ({sign}{frac}")'


def feet(x_in: float) -> str:
    f, i = divmod(x_in, 12.0)
    return f"{int(f)}' {i:.1f}\""


@lru_cache(maxsize=1)
def _edge_per_radius() -> float:
    from two_v_demo import raw_wedge_bridge
    topo = raw_wedge_bridge.simulator().build_2v_hemisphere(1.0)
    return float(topo.sphere_radius_in)


def long_edge_for(diameter_ft: float) -> float:
    """The nominal long edge whose hemisphere has this floor diameter (the base vertices sit on the sphere)."""
    return diameter_ft * 12.0 / 2.0 / _edge_per_radius()


def _sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()[:12]


def _git() -> str:
    try:
        return subprocess.run(["git", "rev-parse", "--short", "HEAD"], cwd=ROOT, capture_output=True,
                              text=True, timeout=10).stdout.strip() or "unknown"
    except (OSError, subprocess.SubprocessError):
        return "unknown"


def solve(request: Request) -> Design:
    from infill import methodology
    from infill.stock import first_fit
    from two_v_demo import raw_wedge_bridge as bridge

    sim = bridge.simulator()
    long_edge = long_edge_for(request.diameter_ft)
    try:
        model = bridge.model(orientation=request.orientation, seam_join_mode=request.seam_join,
                             long_edge_in=round(long_edge, 6), trunk_diameter_in=request.log_in)
        sim.validate_topology(model.topology)
        sim.validate_physical_model(model)
    except (AssertionError, ValueError) as e:
        raise ValueError(f"The solver could not build this dome: {e}") from e
    cfg, topo = model.config, model.topology
    allowance = cfg.jig_butt_hangoff_in + cfg.head_overfit_in

    # ---- saw setups (the butt cut), straight from the solver
    setups = sim.butt_cut_setups(model)
    for i, s in enumerate(setups, start=1):
        s["name"] = f"S{i}"

    def setup_of(mitre: float, bevel: float) -> dict:
        return next(s for s in setups if math.isclose(s["mitre_deg"], round(mitre, 3)) and math.isclose(s["bevel_deg"], round(bevel, 3)))

    # ---- cut families: sticks the saw cannot tell apart (same length, same two cut planes).
    # The solver's own recipe signature also holds where the stick sits on the jig; two
    # families that differ only there are one batch at the saw, and the jig pages place them.
    def cut_signature(m) -> tuple:
        _, _, _, hy, hp = sim._cut_plane_components(m, m.receiving_plane_normal)
        _, _, _, by, bp = sim._cut_plane_components(m, m.butt_plane_normal)
        return (m.edge_type, round(m.physical_stock_length_in, 3), *(round(v, 3) + 0.0 for v in (hy, hp, by, bp)))
    buckets: dict[tuple, list] = {}
    for m in model.members:
        buckets.setdefault(cut_signature(m), []).append(m)
    ordered = sorted(buckets.values(), key=lambda ms: (ms[0].edge_type, -ms[0].physical_stock_length_in))
    families: list[Family] = []
    family_of: dict[str, str] = {}
    for i, ms in enumerate(ordered, start=1):
        m = ms[0]
        _, _, _, hy, hp = sim._cut_plane_components(m, m.receiving_plane_normal)
        _, _, _, by, bp = sim._cut_plane_components(m, m.butt_plane_normal)
        s = setup_of(by, bp)
        name = f"{m.edge_type}{i}"
        families.append(Family(name, m.edge_type, len(ms), m.nominal_length_in, max(x.physical_stock_length_in for x in ms),
                               max(x.physical_stock_length_in for x in ms) + allowance, s["name"], by, bp, hy, hp,
                               [x.member_id for x in ms]))
        for x in ms:
            family_of[x.member_id] = name

    # ---- rounds: the longest blanks first, `splits` wedges to a round, a round as long as its longest wedge
    blanks = sorted(((f.raw_blank_in, f.name) for f in families for _ in range(f.count)), reverse=True)
    splits = cfg.radial_splits
    log_len = request.log_ft * 12.0
    if blanks[0][0] > log_len:
        raise ValueError(f"The longest raw blank is {blanks[0][0] / 12:.2f} ft but your logs are {request.log_ft:g} ft. "
                         "Use longer logs or a smaller dome.")
    r = request.log_in / 2.0
    rounds: list[Round] = []
    for n, start in enumerate(range(0, len(blanks), splits), start=1):
        chunk = blanks[start:start + splits]
        takes: dict[str, int] = {}
        for _, fam in chunk:
            takes[fam] = takes.get(fam, 0) + 1
        length = chunk[0][0]
        lb = math.pi * r * r * length / 1728.0 * cfg.green_wood_density_lb_ft3
        rounds.append(Round(n, 0, length, takes, splits - len(chunk), lb))
    packed = first_fit([x.length_in for x in rounds], log_len, KERF_IN)
    pool = sorted(rounds, key=lambda x: -x.length_in)
    logs: list[list[Round]] = []
    for li, lengths in enumerate(packed, start=1):
        row = []
        for L in lengths:
            pick = next(x for x in pool if x.length_in == L)
            pool.remove(pick)
            pick.log = li
            row.append(pick)
        logs.append(row)

    # ---- jig variants: panels whose three members are the same recipe, rotation allowed
    groups: dict[tuple, list[int]] = {}
    for i in range(len(topo.faces)):
        groups.setdefault(sim._panel_variant_signature(model, i), []).append(i)
    variants = sorted(groups.values(), key=lambda g: (-len(g), g[0]))

    # ---- seams, by family
    seam_rows: dict[str, dict] = {}
    for s in model.seams:
        length = float(np.linalg.norm(s.end - s.start))
        frac = min(max(cfg.trapezoid_nose_depth_in / max(s.contact_depth_in, 1e-9), 0.0), 0.95)
        row = seam_rows.setdefault(s.edge_type, {
            "edge_type": s.edge_type, "count": 0, "length_in": length, "fold_deg": s.fold_angle_deg,
            "dihedral_deg": s.internal_dihedral_deg, "gap_deg": s.raw_gap_angle_deg,
            "key_outer_in": s.spacer_base_width_in * frac, "key_inner_in": s.spacer_base_width_in, "ids": []})
        row["count"] += 1
        row["ids"].append(s.seam_id)
    seams = [seam_rows[k] for k in sorted(seam_rows)]

    # ---- the infill takeoff, from the same ledger the books use
    infill = methodology.dome_budget(long_edge, request.log_in, max(f.raw_blank_in for f in families), request.log_ft,
                                     finished_ft=sum(m.physical_stock_length_in for m in model.members) / 12.0)

    base = [i for e in topo.edges.values() if e.is_base for i in e.key]
    ring = topo.vertices[sorted(set(base))][:, :2]
    angles = np.arctan2(ring[:, 1], ring[:, 0])
    ring = ring[np.argsort(angles)]
    floor_area = 0.5 * abs(float(np.dot(ring[:, 0], np.roll(ring[:, 1], -1)) - np.dot(ring[:, 1], np.roll(ring[:, 0], -1)))) / 144.0

    d = Design(request, model, sim, long_edge, float(topo.sphere_radius_in), floor_area, families, setups,
               family_of, rounds, logs, variants, seams, infill, [], {})
    d.checks = _checks(d)
    d.provenance = {
        "design": request.key(),
        "made": dt.datetime.now(dt.timezone.utc).strftime("%Y-%m-%d %H:%M UTC"),
        "solver": f"geodesic_raw_wedge_dome_dihedral.py sha256 {_sha(ROOT / 'geodesic_raw_wedge_dome_dihedral.py')}",
        "ledger": f"infill/methodology.py sha256 {_sha(ROOT / 'infill' / 'methodology.py')}",
        "commit": _git(),
    }
    return d


def _checks(d: Design) -> list[tuple[str, bool, str]]:
    """What the solve has to satisfy before anybody cuts a log. A failure stops the render."""
    m, cfg = d.model, d.config
    topo = m.topology
    half = 180.0 / cfg.radial_splits
    out = [
        ("Solver's own model checks pass", True, "validate_topology and validate_physical_model ran without error"),
        ("Three members per panel", len(m.members) == 3 * len(topo.faces), f"{len(m.members)} members, {len(topo.faces)} panels"),
        ("Every member is in exactly one family", sum(f.count for f in d.families) == len(m.members) == len(d.family_of),
         f"{len(d.families)} families hold {sum(f.count for f in d.families)} members"),
        ("Saw setups cover every butt cut", sum(int(s['count']) for s in d.setups) == len(m.members),
         f"{len(d.setups)} setups, {sum(int(s['count']) for s in d.setups)} cuts"),
        ("Butt bevel is one value for the whole dome", len({abs(round(float(s['bevel_deg']), 3)) for s in d.setups}) == 1,
         f"{abs(float(d.setups[0]['bevel_deg'])):g} deg" + (f", half of 360/{cfg.radial_splits}" if math.isclose(abs(float(d.setups[0]['bevel_deg'])), half, abs_tol=1e-3) else "")),
        ("Rounds supply every wedge", sum(sum(r.wedges.values()) for r in d.rounds) == len(m.members),
         f"{len(d.rounds)} rounds x {cfg.radial_splits} wedges, {sum(r.spare for r in d.rounds)} spare"),
        ("Every round fits its log", all(sum(r.length_in for r in log) + KERF_IN * len(log) <= d.request.log_ft * 12 + 1e-6 for log in d.logs),
         f"{len(d.logs)} logs of {d.request.log_ft:g} ft"),
        ("Every panel has a jig", sum(len(v) for v in d.variants) == len(topo.faces), f"{len(d.variants)} jigs for {len(topo.faces)} panels"),
        ("Seams = edges not on the floor", sum(s["count"] for s in d.seams) == sum(not e.is_base for e in topo.edges.values()),
         f"{sum(s['count'] for s in d.seams)} seams"),
        ("Floor diameter matches the request", math.isclose(2 * d.radius_in / 12, d.request.diameter_ft, rel_tol=1e-6),
         f"{2 * d.radius_in / 12:.3f} ft"),
    ]
    return out
