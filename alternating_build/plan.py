"""A mixed in/out dome, read ground up: bands, the walk round each, every seam it closes.

Everything comes from the solver's model (``orientation_pattern``): which panel points
which way, the gap at each seam, the key it needs. This module adds the builder's order
and the reasons: why a ring closes, why a matched seam had to be somewhere, and what each
one costs in degrees against an alternating seam on the same edge.
"""

from __future__ import annotations

from collections import Counter, defaultdict
from dataclasses import dataclass, field
from functools import lru_cache

PATTERNS = {
    "alternate_ground": "The ten ground panels alternate in and out around the base",
    "alternate_lower": "The whole lower ring of twenty alternates (ground panels one way, the panels between them the other)",
    "least_angle": "Every panel chosen for the least extra seam angle, nothing fixed",
}
IN, OUT = "point_dome_in", "point_dome_out"
WORD = {IN: "IN", OUT: "OUT"}


@dataclass
class Seam:
    seam_id: str
    edge_type: str
    a: int
    b: int
    pair: str                 # in/out | in/in | out/out
    gap_deg: float            # what the key fills
    fold_deg: float           # the dome's own turn at this seam
    alt_gap_deg: float        # what an in/out seam on this edge would leave
    key_width_in: float       # the key's wide side
    band: int                 # the band whose panel closes it (the higher of the two)

    @property
    def matched(self) -> bool:
        return self.pair != "in/out"

    @property
    def extra_deg(self) -> float:
        return self.gap_deg - self.alt_gap_deg


@dataclass
class Panel:
    index: int
    face_type: str
    band: int
    orientation: str
    height_in: float
    walk: int = 0             # its place in the walk round its band


@dataclass
class Plan:
    pattern: str
    ground_in: str
    model: object
    panels: list[Panel]
    seams: list[Seam]
    bands: dict[int, list[int]]
    vertex_rings: list[dict] = field(default_factory=list)

    def panels_in(self, band: int) -> list[Panel]:
        return [self.panels[i] for i in self.bands[band]]

    def seams_closed_by(self, band: int) -> list[Seam]:
        return [s for s in self.seams if s.band == band]

    def matched(self) -> list[Seam]:
        return [s for s in self.seams if s.matched]

    def total_extra_deg(self) -> float:
        return sum(s.extra_deg for s in self.seams)

    def counts(self) -> Counter:
        return Counter(s.pair for s in self.seams)

    def band_summary(self, band: int) -> str:
        ps = self.panels_in(band)
        o = Counter(WORD[p.orientation] for p in ps)
        closed = self.seams_closed_by(band)
        m = [s for s in closed if s.matched]
        extra = sum(s.extra_deg for s in m)
        return (f"band {band}: {len(ps)} panels, {o['IN']} in / {o['OUT']} out; closes {len(closed)} seams, "
                f"{len(m)} matched" + (f" (+{extra:.2f} deg in all)" if m else ""))


def _solver():
    from two_v_demo import raw_wedge_bridge
    return raw_wedge_bridge.simulator()


@lru_cache(maxsize=16)
def plan(pattern: str = "alternate_ground", ground_in: str = "auto", long_edge_in: float | None = None,
         log_in: float | None = None) -> Plan:
    import numpy as np
    sim = _solver()
    fields = {"orientation_pattern": pattern, "pattern_ground_in": ground_in}
    if long_edge_in is not None:
        fields["long_edge_in"] = float(long_edge_in)
    if log_in is not None:
        fields["trunk_diameter_in"] = float(log_in)
    model = sim.build_physical_model(sim.DomeConfig(**fields))
    topo = model.topology
    bands_of = sim.panel_bands(topo)
    o = model.panel_orientations
    panels = [Panel(i, f.face_type, bands_of[i], o[i], float(f.center[2])) for i, f in enumerate(topo.faces)]
    bands: dict[int, list[int]] = defaultdict(list)
    for b in sorted(set(bands_of)):
        ring = sim.ring_order(topo, [i for i in range(len(panels)) if bands_of[i] == b])
        for k, i in enumerate(ring, start=1):
            panels[i].walk = k
        bands[b] = ring
    seams = []
    for s in model.seams:
        pair = "in/out" if o[s.face_a] != o[s.face_b] else ("in/in" if o[s.face_a] == IN else "out/out")
        alt = sim.seam_face_gap_deg(model.config, IN, OUT, s.inward_a, s.normal_a, s.inward_b, s.normal_b)
        seams.append(Seam(s.seam_id, s.edge_type, s.face_a, s.face_b, pair, float(s.raw_gap_angle_deg),
                          float(s.fold_angle_deg), float(alt), float(s.spacer_base_width_in),
                          max(bands_of[s.face_a], bands_of[s.face_b])))
    # every vertex the panels close round: how many, and whether in/out can go all the way round
    rings = []
    around: dict[int, list[int]] = defaultdict(list)
    for f in topo.faces:
        for v in f.vertices:
            around[v].append(f.index)
    for v, fs in sorted(around.items(), key=lambda kv: -float(topo.vertices[kv[0]][2])):
        if float(topo.vertices[v][2]) <= 1e-6:
            continue                      # the ground: an open fan, not a ring
        matched = sum(1 for s in seams if s.matched and s.a in fs and s.b in fs)
        rings.append({"vertex": v, "height_in": float(topo.vertices[v][2]), "panels": len(fs),
                      "closes": len(fs) % 2 == 0, "matched": matched})
    chosen = ground_in
    if pattern == "alternate_ground":
        ground = bands[1]
        chosen = next(p.face_type for p in panels if p.index in ground and p.orientation == IN)
    return Plan(pattern, chosen, model, panels, seams, dict(bands), rings)


def explain(p: Plan) -> list[str]:
    """The plan as sentences, ground up."""
    lines = [f"Pattern: {PATTERNS.get(p.pattern, p.pattern)}."]
    if p.pattern == "alternate_ground":
        lines.append(f"Ground panels: the {p.ground_in} ground panels point IN, the others OUT. That is the choice "
                     "that puts every forced matched seam on a B seam; the other choice puts them on A seams.")
    c = p.counts()
    lines.append(f"Seams: {c['in/out']} alternate, {c['in/in']} matched in/in, {c['out/out']} matched out/out; "
                 f"{p.total_extra_deg():.2f} deg of key beyond an all-alternating dome, in total.")
    odd = [r for r in p.vertex_rings if not r["closes"]]
    lines.append(f"Why it cannot alternate everywhere: {len(odd)} vertices inside the dome have five panels round "
                 "them (the apex and the five at " + f"{min(r['height_in'] for r in odd) / 12:.1f} ft" +
                 "). Five is odd, so in/out cannot alternate all the way round any of them: each needs at least "
                 "one matched seam. Every other vertex has six and closes.")
    for b in sorted(p.bands):
        lines.append(p.band_summary(b))
    return lines
