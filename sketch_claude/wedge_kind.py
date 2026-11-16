"""The wedge method in Dome Sketch: the raw-wedge dome (the flagship) and the wedge zome.

Nothing here is new geometry. The dome is :func:`wedge_builder.design.solve` -- the solver the
Wedge Builder sells -- and every member is the dihedral raw-wedge solver's own solid
(``add_raw_sector_member``), every seam key its own key (``add_rigid_spacer``), the same calls
``world3d.structures.dome()`` makes. What this module adds is the page's shape: each wedge as a
piece marked with its cut family, a card per family drawn to scale, the log plan, and the build
in order from the log pile to the last ring.

The zome is :func:`wedge_zome.geometry.build` -- every stick from its own tail and head planes.

Solver units are inches; the page's are metres (x 0.0254).
"""

from __future__ import annotations

import math
from dataclasses import dataclass
from functools import lru_cache

import numpy as np

from . import kinds as K
from . import model as M
from . import solids as S
from .model import FT, IN, Model, Piece

M.MATERIALS.update({
    "wedge": {"color": "#d3a66c", "label": "Wedge (split log)"},
    "wedge_b": {"color": "#c4935a", "label": "Wedge (split log), B edge"},
    "wedge_in": {"color": "#f0d6a4", "label": "Wedge, point in"},
    "wedge_out": {"color": "#5a3622", "label": "Wedge, point out"},
    "key": {"color": "#e4c766", "label": "Seam key"},
    "zome": {"color": "#d8ad74", "label": "Zome stick (wedge)"},
    "zome_b": {"color": "#c99b60", "label": "Zome stick (wedge)"},
})


def _seed_diameter_m() -> float:
    from wedge_builder import design as W
    return float(W.defaults()["diameter_ft"]) * FT


@dataclass(frozen=True)
class WedgeSpec:
    kind: str = "wedge"
    diameter_m: float = 19.4 * FT          # floor, vertex to vertex: the seed dome's
    log_m: float = 12 * IN                 # small-end diameter of the logs
    log_len_m: float = 16 * FT
    orientation: str = "point_dome_in"
    seam_join: str = "raw_trapezoid"
    pattern: str = "uniform"
    ground_in: str = "auto"
    keys: bool = True
    skin: bool = False
    people: bool = True

    @property
    def title(self) -> str:
        return f"Wedge dome, {self.diameter_m / FT:.1f} ft"


@dataclass(frozen=True)
class ZomeSpec:
    kind: str = "zome"
    log_m: float = 12 * IN
    side_m: float = 0.0                    # 0: the Complete Edition's panel side
    hand: str = "ccw"
    skin: bool = False
    people: bool = True

    @property
    def title(self) -> str:
        return "Wedge zome"


def _opts(d: dict) -> list[list[str]]:
    return [[k, v] for k, v in d.items()]


def _wedge_form() -> list[dict]:
    from wedge_builder import design as W
    return [
        {"key": "diameter_m", "label": "Floor diameter", "type": "len", "min": W.LIMITS["diameter_ft"][0] * FT, "max": W.LIMITS["diameter_ft"][1] * FT, "step": 0.0254},
        {"key": "log_m", "label": "Log (small end)", "type": "len", "min": W.LIMITS["log_in"][0] * IN, "max": W.LIMITS["log_in"][1] * IN, "step": 0.0127},
        {"key": "log_len_m", "label": "Log length", "type": "len", "min": W.LIMITS["log_ft"][0] * FT, "max": W.LIMITS["log_ft"][1] * FT, "step": 0.3048},
        {"key": "pattern", "label": "Panels", "type": "select", "options": _opts(W.PATTERNS)},
        {"key": "orientation", "label": "Wedge points", "type": "select", "options": _opts(W.ORIENTATIONS)},
        {"key": "seam_join", "label": "Seams", "type": "select", "options": _opts(W.SEAM_JOINS)},
        {"key": "ground_in", "label": "Ground panels in", "type": "select", "options": _opts(W.GROUND_IN)},
        {"key": "keys", "label": "Seam keys", "type": "check"}, {"key": "skin", "label": "Skin", "type": "check"},
        {"key": "people", "label": "Person", "type": "check"},
    ]


WEDGE_FORM = _wedge_form()
ZOME_FORM = [
    {"key": "log_m", "label": "Log (small end)", "type": "len", "min": 6 * IN, "max": 24 * IN, "step": 0.0127},
    {"key": "side_m", "label": "Panel side (0: the book's)", "type": "len", "min": 0.0, "max": 1.5, "step": 0.01},
    {"key": "hand", "label": "Pinwheel", "type": "select", "options": [["ccw", "Counter-clockwise"], ["cw", "Clockwise"]]},
    {"key": "skin", "label": "Skin", "type": "check"}, {"key": "people", "label": "Person", "type": "check"},
]


def _ground(r: float) -> Piece:
    g = S.box((0, 0, -0.03), (2 * r + 6, 2 * r + 6, 0.06))
    return Piece("ground", "Ground", "site", "ground", g, {}, -1, "site")


# ----------------------------------------------------------------------
# The wedge dome
# ----------------------------------------------------------------------

@lru_cache(maxsize=8)
def _design(spec: WedgeSpec):
    from wedge_builder import design as W
    lim = W.LIMITS
    clamp = lambda v, k: min(max(v, lim[k][0]), lim[k][1])
    req = W.Request.from_json({
        "diameter_ft": clamp(spec.diameter_m / FT, "diameter_ft"), "log_in": clamp(spec.log_m / IN, "log_in"),
        "log_ft": clamp(spec.log_len_m / FT, "log_ft"), "orientation": spec.orientation, "seam_join": spec.seam_join,
        "pattern": spec.pattern, "ground_in": spec.ground_in})
    return W.solve(req)


@lru_cache(maxsize=8)
def build_wedge(spec: WedgeSpec) -> Model:
    import geodesic_raw_wedge_dome_dihedral as dd

    d = _design(spec)
    mdl = d.model
    cfg = mdl.config
    fam = {f.name: f for f in d.families}
    faces = mdl.topology.faces
    fz = [float(np.mean(np.asarray(mdl.topology.vertices)[list(f.vertices)][:, 2])) for f in faces]
    ring_of = K.ring_rank(fz, 2)
    mixed = spec.pattern != "uniform"
    pieces: list[Piece] = []
    members_by_face: dict[int, list[Piece]] = {}
    for mem in mdl.members:
        acc = dd.MeshAccumulator()
        dd.add_raw_sector_member(acc, mdl, mem)
        md = acc.finish()
        mesh = K.soup_mesh(md.vertices[:, :3], md.indices.reshape(-1, 3), IN)
        fname = d.family_of[mem.member_id]
        f = fam[fname]
        if mixed:
            mat = "wedge_out" if "out" in str(mem.orientation) else "wedge_in"
        else:
            mat = "wedge" if mem.edge_type == "A" else "wedge_b"
        info = {"mark": fname, "edge": mem.edge_type, "panel": mem.face_index + 1, "ring": ring_of[mem.face_index] + 1,
                "finished_m": f.finished_in * IN, "raw_blank_m": f.raw_blank_in * IN, "butt_setup": f.butt_setup,
                "butt_mitre_deg": f.butt_mitre_deg, "butt_bevel_deg": f.butt_bevel_deg, "head_yaw_deg": f.head_yaw_deg,
                "head_pitch_deg": f.head_pitch_deg, "points": str(mem.orientation).replace("_", " ")}
        nrm = np.asarray(faces[mem.face_index].normal, float)
        p = Piece(mem.member_id, f"Wedge {fname} ({mem.member_id})", "frame", mat, mesh, info, 0, f"P{mem.face_index + 1:03d}", tuple(nrm * 0.7))
        pieces.append(p)
        members_by_face.setdefault(mem.face_index, []).append(p)

    keys_by_ring: dict[int, list[Piece]] = {}
    key_rows = {s["edge_type"]: s for s in d.seams}
    if spec.keys:
        for seam in mdl.seams:
            acc = dd.MeshAccumulator()
            dd.add_rigid_spacer(acc, mdl, seam)
            md = acc.finish()
            if not len(md.indices):
                continue
            mesh = K.soup_mesh(md.vertices[:, :3], md.indices.reshape(-1, 3), IN)
            L = float(np.linalg.norm(np.asarray(seam.end) - np.asarray(seam.start))) * IN
            info = {"mark": f"KEY-{seam.edge_type}", "length_m": L, "gap_deg": seam.raw_gap_angle_deg, "fold_deg": seam.fold_angle_deg}
            r = max(ring_of[seam.face_a], ring_of[seam.face_b])
            nrm = (np.asarray(faces[seam.face_a].normal) + np.asarray(faces[seam.face_b].normal)) / 2
            kp = Piece(seam.seam_id, f"Seam key {seam.edge_type} ({seam.seam_id})", "key", "key", mesh, info, 0, seam.seam_id, tuple(nrm * 0.9))
            keys_by_ring.setdefault(r, []).append(kp)
            pieces.append(kp)
    skins = []
    if spec.skin:
        V = np.asarray(mdl.topology.vertices)
        for i, f in enumerate(faces):
            tri = V[list(f.vertices)] + np.asarray(f.normal) * cfg.skin_offset_in
            mesh = S.prism([q * IN for q in tri], f.normal, 0.5 * IN)
            skins.append(Piece(f"SKIN{i + 1:02d}", f"Skin panel {i + 1}", "skin", "ply", mesh, {"panel": i + 1}, 0, f"P{i + 1:03d}", tuple(np.asarray(f.normal) * 1.2)))
        pieces += skins
    R = d.radius_in * IN
    ctx = [_ground(R)]
    if spec.people:
        ctx += M._person((-(R + 0.9), 0.6, 0.0), -90.0)
    for p in ctx:
        if p.tag == "person":
            p.group = "person"
    K.context(ctx)

    # the build: logs, rounds, splits, saw setups, jigs, then ring by ring
    book = K.Book()
    req = d.request
    frame = [p for p in pieces if p.tag == "frame"]
    heaviest = max(r.green_lb for r in d.rounds) * 0.45359237
    book.prep("Choose your logs",
              f"You need {len(d.logs)} logs at least {K.m(req.log_ft * FT)} long and {K.m(req.log_in * IN)} across at the small end. "
              "The solver cuts every wedge from a round log this size, so measure the small end, not the butt.",
              [], ["Tape", "Calipers or a diameter tape"], f"Every log is at least {K.m(req.log_in * IN)} across its small end.", phase="Logs")
    lens = [r.length_in * IN for r in d.rounds]
    book.prep("Cut the rounds",
              f"Crosscut the logs into {len(d.rounds)} rounds, {K.m(min(lens))} to {K.m(max(lens))} long; the log plan card says which "
              f"round comes from which log and which family its wedges go to. The heaviest green round weighs about {K.kg(heaviest)}: lift with two.",
              [], ["Chainsaw", "Tape", "Log dogs or cant hook"], "Each round's ends are square to its length.", phase="Logs")
    book.prep(f"Split each round {cfg.radial_splits} ways",
              f"Split every round into {cfg.radial_splits} equal wedges through the pith: halves, then quarters, then eighths. "
              f"That is {sum(sum(r.wedges.values()) for r in d.rounds)} wedges for {len(frame)} members, the rest spare.",
              frame, ["Splitting wedges", "Sledge", "Froe"], "Each wedge's point is on the pith and its faces are flat.", phase="Logs")
    for s in d.setups:
        names = [f.name for f in d.families if f.butt_setup == s["name"]]
        ps = [p for p in frame if p.info["mark"] in names]
        book.prep(f"Saw setup {s['name']}: butt cuts",
                  f"Set the saw to {K.deg(s['mitre_deg'])} mitre and {K.deg(s['bevel_deg'])} bevel and cut the butt end of all "
                  f"{s['count']} wedges of {', '.join(names)}. Leave each one long: the head is sawn on the jig.",
                  ps, ["Chainsaw mill or big-blade saw", "Angle gauge", "Stop block"], "Cut a scrap wedge first and check both angles.", phase="Cut")
    book.prep("Build the panel jigs",
              f"Every panel is framed flat on a jig. {len(d.variants)} jigs cover the {len(faces)} panels; the first serves "
              f"{len(d.variants[0])} of them. Each wedge's butt rests on the jig with a {K.m(cfg.jig_butt_hangoff_in * IN)} tail past "
              "the fixture, which is cut off later.", frame, ["Plywood", "Rails", "Screws"], "Check the jig's corners against the panel's angles.", phase="Jigs")
    book.prep("Frame each panel",
              "Lay three wedges on the jig in a pinwheel: each one's butt runs into the side of the next. Saw each head flush in place, "
              "then fasten the corners. Mark the panel's number on it.", frame, ["Saw", "Structural screws", "Clamps"],
              "The three outside corners sit on the jig's marks.", phase="Jigs")
    rings = sorted(set(ring_of))
    for r in rings:
        ps = [p for fi, lst in members_by_face.items() if ring_of[fi] == r for p in lst]
        ks = keys_by_ring.get(r, [])
        nf = len({p.group for p in ps})
        book.add(f"Raise ring {r + 1} of {len(rings)}",
                 ("Stand the ground panels on the floor's edge. " if r == rings[0] else "Lift the next ring onto the one below. ")
                 + f"{nf} panels go up here" + (f", with {len(ks)} seam keys driven into the V between neighbours" if ks else "") + ".",
                 ps + ks, ["Helpers", "Ladder", "Structural screws", "Mallet"],
                 "Every new corner meets its neighbours; measure across the dome at this height in two directions.", phase="Raise")
    if skins:
        book.add("Skin the dome", "Sheath each panel and seal its seams.", skins, ["Drill", "Sealant"], phase="Close in")

    # cards: one per family, the wedge's section, the keys, the logs
    cards = []
    chord = 2 * (req.log_in * IN / 2) * math.sin(math.pi / cfg.radial_splits)
    for f in d.families:
        Lf, Lr = f.finished_in * IN, f.raw_blank_in * IN
        w = chord
        tb = w * math.tan(math.radians(abs(f.butt_mitre_deg)))
        th = w * math.tan(math.radians(abs(f.head_yaw_deg)))
        poly = [(0.0, 0.0), (Lf, 0.0), (Lf - th, w), (tb, w)]
        tail = cfg.jig_butt_hangoff_in * IN
        dr = K.drawing(poly, angles=False, lines=[((-tail, 0), (0, 0)), ((Lf, 0), (Lr - tail, 0))],
                       notes=[{"at": [0.0, w * 2.2], "text": f"butt {K.deg(f.butt_mitre_deg)} / {K.deg(f.butt_bevel_deg)} ({f.butt_setup})"},
                              {"at": [Lf * 0.72, w * 2.2], "text": f"head {K.deg(f.head_yaw_deg)}"}])
        dr["dims"] = [{"a": [0.0, 0.0], "b": [Lf, 0.0], "m": Lf}]
        ids = [p.id for p in frame if p.info["mark"] == f.name]
        cards.append(K.card(f.name, f"Wedge {f.name}", f.count, [
            ["Edge", f.edge_type], ["Finished", K.m(Lf)], ["Raw blank", K.m(Lr)], ["Butt", f"{K.deg(f.butt_mitre_deg)} mitre, {K.deg(f.butt_bevel_deg)} bevel"],
            ["Saw setup", f.butt_setup], ["Head", f"{K.deg(f.head_yaw_deg)} yaw, {K.deg(f.head_pitch_deg)} pitch"]],
            dr, ids, group=f"Saw setup {f.butt_setup}", kind="wedge"))
    r_log = req.log_in * IN / 2
    a = math.pi / cfg.radial_splits
    sector = [(0.0, 0.0)] + [(r_log * math.cos(-a + 2 * a * i / 8), r_log * math.sin(-a + 2 * a * i / 8)) for i in range(9)]
    cards.append(K.card("SECTION", "The wedge's section", sum(f.count for f in d.families), [
        ["Log (small end)", K.m(req.log_in * IN)], ["Split", f"{cfg.radial_splits} ways: {K.deg(360 / cfg.radial_splits)} at the point"],
        ["Back (chord)", K.m(chord)]], K.drawing(sector, dims=False, angles=False,
                                                  notes=[{"at": [r_log * 0.35, 0.0], "text": K.deg(360 / cfg.radial_splits)}]), [], "Logs", "section"))
    for et, s in key_rows.items():
        ks = [p for lst in keys_by_ring.values() for p in lst if p.info["mark"] == f"KEY-{et}"]
        dr = None
        if ks:
            seam = next(x for x in mdl.seams if x.seam_id == ks[0].id)
            tg = S.unit(np.asarray(seam.tangent, float))
            u = S.unit(np.cross(tg, [0, 0, 1.0]) if abs(tg[2]) < 0.9 else np.cross(tg, [1.0, 0, 0]))
            v = np.cross(tg, u)
            P = ks[0].mesh.verts
            pts = sorted({(round(float(q @ u), 5), round(float(q @ v), 5)) for q in P})
            hull = _hull2(pts)
            dr = K.drawing(hull, angles=True)
        cards.append(K.card(f"KEY-{et}", f"Seam key, {et} seams", s["count"], [
            ["Length", K.m(s["length_in"] * IN)], ["Gap it fills", K.deg(s["gap_deg"])], ["Fold", K.deg(s["fold_deg"])],
            ["Outside width", K.m(s["key_outer_in"] * IN)], ["Inside width", K.m(s["key_inner_in"] * IN)]],
            dr, [p.id for p in ks], "Seam keys", "key"))
    for i, log in enumerate(d.logs, 1):
        x = 0.0
        lines, notes = [], []
        for rnd in log:
            L = rnd.length_in * IN
            lines.append(((x + L, -0.05), (x + L, 0.25)))
            notes.append({"at": [x + L / 2, 0.36], "text": ", ".join(f"{v} {k}" for k, v in rnd.wedges.items())})
            x += L
        total = req.log_ft * FT
        cards.append(K.card(f"LOG{i}", f"Log {i}", 1, [["Length", K.m(total)], ["Rounds", " + ".join(K.m(r.length_in * IN) for r in log)],
                                                        ["Green weight", K.kg(sum(r.green_lb for r in log) * 0.45359237)]],
                            K.drawing([(0, 0), (total, 0), (total, req.log_in * IN), (0, req.log_in * IN)], angles=False, lines=lines, notes=notes),
                            [], "Log plan", "log"))

    passed = sum(1 for c in d.checks if c[1])
    summary = [
        ["Across the floor", K.m(req.diameter_ft * FT)], ["Height", K.m(R)], ["Floor", K.m2(d.floor_area_sqft * FT * FT)],
        ["Members", f"{len(frame)} wedges in {len(d.families)} families"],
        ["Logs", f"{len(d.logs)} of {K.m(req.log_ft * FT)}, {K.m(req.log_in * IN)} across"],
        ["Rounds", K.n(len(d.rounds))], ["Saw setups", K.n(len(d.setups))], ["Jigs", K.n(len(d.variants))],
        ["Seams", f"{sum(s['count'] for s in d.seams)}, keyed"], ["Green wood", K.kg(sum(r.green_lb for r in d.rounds) * 0.45359237)],
        ["Solver checks", f"{passed} of {len(d.checks)} pass"],
    ]
    declared = [{"name": n_, "value": v, "kind": k, "why": w} for n_, v, k, w in d.constants()]
    warnings = [f"{name}: {why}" for name, ok, why in d.checks if not ok]
    if mixed:
        warnings.append("Mixed panels: pale wedges point in, dark wedges point out.")
    tables = {
        "title": spec.title, "summary": summary, "cards": cards, "sheets": [], "steps": book.steps, "declared": declared,
        "warnings": warnings,
        "tags": [["frame", "Wedges"], ["key", "Seam keys"], ["skin", "Skin"], ["site", "Ground"], ["person", "Person"]],
        "scenes": [
            {"name": "Exterior", "dir": [0.55, -1, 0.35], "style": "sketch", "off": [], "explode": 0, "step": 999, "door": 0},
            {"name": "Families", "dir": [0.6, -1, 0.45], "style": "sketch", "off": ["skin", "person"], "explode": 0, "step": 999, "door": 0, "colour": True},
            {"name": "Exploded", "dir": [0.55, -1, 0.5], "style": "sketch", "off": ["skin", "person", "site"], "explode": 80, "step": 999, "door": 0},
            {"name": "Seams", "dir": [0.3, -1, 0.9], "style": "xray", "off": ["skin", "person"], "explode": 25, "step": 999, "door": 0},
            {"name": "Top", "dir": [0.0001, -0.0001, 1], "style": "sketch", "off": ["person", "skin"], "explode": 0, "step": 999, "door": 0, "colour": True},
            {"name": "Inside", "dir": [0.2, -1, 0.15], "style": "sketch", "off": ["person", "skin"], "explode": 0, "step": 999, "door": 0, "section": {"axis": "y", "t": 0.5}},
        ],
        "wedge": {"design": d.provenance.get("design"), "families": len(d.families), "members": len(frame), "logs": len(d.logs),
                  "radius_m": R, "family_counts": {f.name: f.count for f in d.families}},
    }
    pieces += ctx
    return Model(spec, pieces, tables, {"centre": [0.0, 0.0, R / 2]})


def _hull2(P):
    P = sorted(set(P))
    if len(P) < 3:
        return [list(p) for p in P]

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
    return [list(p) for p in lo[:-1] + up[:-1]]


# ----------------------------------------------------------------------
# The wedge zome
# ----------------------------------------------------------------------

@lru_cache(maxsize=8)
def build_zome(spec: ZomeSpec) -> Model:
    from wedge_zome import geometry as g

    zm = g.build("wedge", log_in=spec.log_m / IN, side_in=(spec.side_m / IN) or None, hand=spec.hand)
    lift = np.array([0.0, 0.0, g.D["sill_in"]])
    types = g.stick_types(zm)
    name_of = {}
    for s in zm.sticks():
        lens = s.lengths()
        tm, tb = s.cut(s.tail)
        hm, hb = s.cut(s.head)
        key = (s.row, round(lens[0], 2), round(tm, 1), round(tb, 1), round(hm, 1), round(hb, 1))
        name_of[id(s)] = key
    by_key = {(t["row"], round(t["outer"], 2), round(t["tail"][0], 1), round(t["tail"][1], 1), round(t["head"][0], 1), round(t["head"][1], 1)): t for t in types}
    pieces: list[Piece] = []
    by_row: dict[int, list[Piece]] = {}
    for p in zm.panels:
        for k, st in enumerate(p.sticks):
            tails, heads = st.ends
            mesh = K.rings_mesh([(q + lift) * IN for q in tails], [(q + lift) * IN for q in heads])
            t = by_key.get(name_of[id(st)])
            mk = t["name"] if t else f"R{p.row}"
            info = {"mark": mk, "row": p.row, "panel": p.index + 1, "outer_m": float(st.lengths()[0]) * IN,
                    "tail_mitre_deg": t["tail"][0] if t else 0.0, "tail_bevel_deg": t["tail"][1] if t else 0.0,
                    "head_mitre_deg": t["head"][0] if t else 0.0, "head_bevel_deg": t["head"][1] if t else 0.0}
            piece = Piece(f"Z{p.index + 1:02d}{'ABCD'[k]}", f"Stick {mk} (panel {p.index + 1})", "frame", "zome" if k % 2 == 0 else "zome_b",
                          mesh, info, 0, f"Z{p.index + 1:02d}", tuple(np.asarray(p.normal) * 0.6))
            pieces.append(piece)
            by_row.setdefault(p.row, []).append(piece)
    skins = []
    if spec.skin:
        for p in zm.panels:
            quad = [(zm.vertices[k] + lift + p.normal * 0.3) * IN for k in p.corners]
            skins.append(Piece(f"ZS{p.index + 1:02d}", f"Skin panel {p.index + 1}", "skin", "ply", S.prism(quad, p.normal, 0.5 * IN),
                               {"row": p.row}, 0, f"Z{p.index + 1:02d}", tuple(np.asarray(p.normal) * 1.0)))
        pieces += skins
    V = np.asarray(zm.vertices)
    used = sorted({k for p in zm.panels for k in p.corners})
    R = float(np.max(np.hypot(V[used, 0], V[used, 1]))) * IN
    H = float(np.max(V[used, 2]) + lift[2]) * IN
    ctx = [_ground(R)]
    if spec.people:
        ctx += M._person((-(R + 0.9), 0.6, 0.0), -90.0)
    for p in ctx:
        if p.tag == "person":
            p.group = "person"
    K.context(ctx)

    stock = g.stock(zm)
    book = K.Book()
    frame = [p for p in pieces if p.tag == "frame"]
    book.prep("Logs and wedges",
              f"Cut {stock['sections']} log sections and split them {int(g.D['splits'])} ways: {stock['wedges']} wedges, "
              f"{stock['sticks_per_wedge']} sticks from each.", frame, ["Chainsaw", "Splitting wedges", "Sledge"], phase="Logs")
    for t in types:
        ps = [p for p in frame if p.info["mark"] == t["name"]]
        book.prep(f"Cut stick {t['name']}",
                  f"Cut {t['count']} sticks {K.m(t['outer'] * IN)} on the outside face: tail {K.deg(t['tail'][0])} mitre / {K.deg(t['tail'][1])} bevel, "
                  f"head {K.deg(t['head'][0])} mitre / {K.deg(t['head'][1])} bevel.", ps, ["Saw", "Angle gauge", "Stop block"], phase="Cut")
    book.prep("Frame the panels",
              "Each rhombus panel is four sticks in a pinwheel on a jig: each head reaches the corner ahead, each tail butts the stick behind. "
              "The wedge's back lies flat on the outside.", frame, ["Jig", "Structural screws"], phase="Jigs")
    for r in sorted(by_row, reverse=True):
        ps = by_row[r]
        book.add(f"Raise row {len(by_row) - r + 1} of {len(by_row)}",
                 f"Stand the {len({p.group for p in ps})} panels of this row and screw their seams; the outside backs close tight, the inside opens in a V.",
                 ps, ["Helpers", "Ladder", "Screws"], "Every seam's outside meets along its whole length.", phase="Raise")
    if skins:
        book.add("Skin the zome", "Sheath every panel and seal the seams.", skins, ["Drill", "Sealant"], phase="Close in")

    cards = []
    for t in types:
        L = t["outer"] * IN
        w = zm.stick_w * IN if zm.stick_w else 0.05
        dr = K.drawing([(0, 0), (L, 0), (L, w), (0, w)], angles=False,
                       notes=[{"at": [0.0, w * 2.4], "text": f"tail {K.deg(t['tail'][0])} / {K.deg(t['tail'][1])}"},
                              {"at": [L * 0.7, w * 2.4], "text": f"head {K.deg(t['head'][0])} / {K.deg(t['head'][1])}"}])
        cards.append(K.card(t["name"], f"Stick {t['name']}", t["count"], [
            ["Row", str(t["row"])], ["Outside face", K.m(L)], ["Longest face", K.m(t["longest"] * IN)],
            ["Tail", f"{K.deg(t['tail'][0])} mitre, {K.deg(t['tail'][1])} bevel"], ["Head", f"{K.deg(t['head'][0])} mitre, {K.deg(t['head'][1])} bevel"]],
            dr, [p.id for p in frame if p.info["mark"] == t["name"]], f"Row {t['row']}", "stick"))
    summary = [["Across", K.m(2 * R)], ["Height", K.m(H)], ["Panels", f"{len(zm.panels)} in {len(by_row)} rows"],
               ["Sticks", f"{len(frame)} in {len(types)} cuts"], ["Wedges", K.n(stock["wedges"])], ["Log sections", K.n(stock["sections"])],
               ["Log", K.m(zm.log_in * IN)], ["Panel side", K.m(zm.side_in * IN)]]
    declared = [{"name": d.key, "value": f"{d.value:g}", "kind": "declared", "why": d.why} for d in g.DECLARED]
    tables = {"title": spec.title, "summary": summary, "cards": cards, "sheets": [], "steps": book.steps, "declared": declared, "warnings": [],
              "tags": [["frame", "Sticks"], ["skin", "Skin"], ["site", "Ground"], ["person", "Person"]],
              "scenes": [
                  {"name": "Exterior", "dir": [0.55, -1, 0.35], "style": "sketch", "off": [], "explode": 0, "step": 999, "door": 0},
                  {"name": "Rows", "dir": [0.6, -1, 0.4], "style": "sketch", "off": ["skin", "person"], "explode": 0, "step": 999, "door": 0, "colour": True},
                  {"name": "Exploded", "dir": [0.55, -1, 0.5], "style": "sketch", "off": ["skin", "person", "site"], "explode": 70, "step": 999, "door": 0},
                  {"name": "Top", "dir": [0.0001, -0.0001, 1], "style": "sketch", "off": ["person"], "explode": 0, "step": 999, "door": 0, "colour": True}],
              "zome": {"panels": len(zm.panels), "sticks": len(frame), "types": len(types), "sections": stock["sections"],
                       "section_m": g.D["section_in"] * IN, "log_m": zm.log_in * IN, "wedges": stock["wedges"]}}
    pieces += ctx
    return Model(spec, pieces, tables, {"centre": [0.0, 0.0, H / 2]})
