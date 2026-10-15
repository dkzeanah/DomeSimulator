"""The three structures and their jigs, built by their own solvers, as pieces.

* **The foundation** -- :mod:`infill.base`: five 20 ft half trunks on edge, round
  back out, mitred into a pentagon, and the five-point star inside it (ten long
  pieces and five short, which is how one 20 ft log yields one of each). Its jig
  is the layout on the ground: a stake at every corner and every star crossing,
  and string between them.
* **The dome** -- :mod:`geodesic_raw_wedge_dome_dihedral`: every raw-wedge member as
  the solver cuts it, standing on the foundation's top. Its jig is the solver's
  own fabrication jig for one panel.
* **The zome** -- :mod:`wedge_zome.geometry`: every stick of every panel. Its jig is
  the zome world's jig table, with its rulers.

Each also has a skin layer: the foundation's deck, the dome's triangles, the
zome's panels. Units are inches, z up, the ground at z = 0.
"""

from __future__ import annotations

import math
from functools import lru_cache

import numpy as np

from infill import solids as so

from . import pieces as pc
from .pieces import Piece

ZOME_AT = np.array([640.0, 0.0, 0.0])
FOUNDATION_JIG_AT = np.array([0.0, -600.0, 0.0])
DOME_JIG_AT = np.array([-560.0, 0.0, 0.0])
ZOME_JIG_AT = np.array([640.0, -430.0, 0.0])

WOOD = (0.86, 0.66, 0.42, 1.0)
WOOD_B = (0.78, 0.55, 0.32, 1.0)
LOG = (0.66, 0.47, 0.30, 1.0)
STAR = (0.80, 0.60, 0.38, 1.0)
PIER = (0.55, 0.50, 0.44, 1.0)
DECK = (0.74, 0.60, 0.44, 1.0)
SKIN = (0.95, 0.93, 0.86, 0.45)
JIG = (0.60, 0.62, 0.66, 1.0)
STAKE = (0.85, 0.30, 0.20, 1.0)
STRING = (0.95, 0.85, 0.20, 1.0)
PERSON = (0.22, 0.42, 0.66, 1.0)

#: The layers, in the panel's order: (key, label, structure, on at start).
LAYERS: tuple[tuple[str, str, str, bool], ...] = (
    ("foundation", "Foundation: half trunks + star", "foundation", True),
    ("foundation_deck", "Foundation: deck (skin)", "foundation", False),
    ("foundation_jig", "Foundation: layout jig", "foundation", True),
    ("dome", "Dome: wedge members", "dome", True),
    ("dome_skin", "Dome: skin", "dome", False),
    ("dome_jig", "Dome: panel jig", "dome", True),
    ("zome", "Zome: wedge sticks", "zome", True),
    ("zome_skin", "Zome: skin", "zome", False),
    ("zome_jig", "Zome: jig table", "zome", True),
    ("mine", "My pieces", "", True),
    ("person", "Six-foot person", "", True),
)
LAYER_KEYS = tuple(k for k, *_ in LAYERS)


def _recentre(pieces: list[Piece], at: np.ndarray) -> list[Piece]:
    """Move a group so its footprint centre sits on ``at`` and its lowest point on the ground."""
    pts = np.concatenate([p.points() for p in pieces])
    lo, hi = pts.min(axis=0), pts.max(axis=0)
    delta = np.array([at[0] - (lo[0] + hi[0]) / 2, at[1] - (lo[1] + hi[1]) / 2, at[2] - lo[2]])
    for p in pieces:
        p.solid = pc.moved(p.solid, delta)
        for k in ("a", "b"):
            if k in p.meta:
                p.meta[k] = (np.asarray(p.meta[k], float) + delta).tolist()
    return pieces


def _box(lo, hi) -> so.Solid:
    lo, hi = np.asarray(lo, float), np.asarray(hi, float)
    plan = np.array([[lo[0], lo[1]], [hi[0], lo[1]], [hi[0], hi[1]], [lo[0], hi[1]]], float)
    return so.slab(plan, float(lo[2]), float(hi[2]))


# ----------------------------------------------------------------------
# The foundation
# ----------------------------------------------------------------------

@lru_cache(maxsize=1)
def foundation_model():
    from infill import base
    return base.build(base.BaseOptions(pattern="star", frame_mat="half", prim_mat="half", support="piers"),
                      with_recipes=False)


def foundation() -> list[Piece]:
    B = foundation_model()
    out = []
    for k, bp in enumerate(B.pieces):
        if bp.solid is None:
            continue
        ref = bp.ref
        name = getattr(ref, "label", "") or getattr(ref, "name", "") or f"{bp.group} {k + 1}"
        colour = {"frame": LOG, "pier": PIER}.get(bp.kind, STAR)
        meta = {"group": bp.group, "material": bp.material}
        if hasattr(ref, "a") and hasattr(ref, "length"):
            meta.update(centreline_in=round(float(ref.length), 2),
                        cut_in=round(float(ref.s_hi - ref.s_lo), 2) if ref.s_hi > ref.s_lo else None,
                        number=getattr(ref, "number", 0))
        out.append(Piece(f"F{k + 1:02d}", "foundation", name, bp.solid, colour, "member", meta))
    return out


def foundation_top() -> float:
    return float(foundation_model().top)


def foundation_deck() -> list[Piece]:
    B = foundation_model()
    plan = np.asarray(B.crown, float)[:, :2]
    top = foundation_top()
    return [Piece("FD", "foundation_deck", "Deck over the pentagon", so.slab(plan, top, top + 1.5), DECK, "skin")]


def foundation_jig() -> list[Piece]:
    """The layout on the ground before a log is moved: stakes and string."""
    B = foundation_model()
    corners = [np.array([p[0], p[1], 0.0]) for p in B.crown]
    n = len(corners)
    stars = []
    for i in range(n):           # where the star's lines cross: the inner pentagon
        a0, a1 = corners[i], corners[(i + 2) % n]
        b0, b1 = corners[(i + 1) % n], corners[(i + 4) % n]
        d1, d2 = a1 - a0, b1 - b0
        t = np.cross(b0[:2] - a0[:2], d2[:2]) / np.cross(d1[:2], d2[:2])
        stars.append(a0 + d1 * t)
    out = []
    for k, p in enumerate(corners + stars):
        out.append(Piece(f"FJ{k + 1:02d}", "foundation_jig", ("corner stake" if k < n else "star stake") + f" {k % n + 1}",
                         _box(p - [1, 1, 0], p + [1, 1, 18]), STAKE, "jig"))
    lines = [(corners[i], corners[(i + 1) % n]) for i in range(n)] + [(corners[i], corners[(i + 2) % n]) for i in range(n)]
    for k, (a, b) in enumerate(lines):
        s = pc.strut(a + [0, 0, 6], b + [0, 0, 6], "square", 2.0)      # string, drawn thick enough to see
        out.append(Piece(f"FS{k + 1:02d}", "foundation_jig", ("side string" if k < n else "star string") + f" {k % n + 1}",
                         s, STRING, "jig", {"a": (a + [0, 0, 6]).tolist(), "b": (b + [0, 0, 6]).tolist()}))
    return _recentre(out, FOUNDATION_JIG_AT)


# ----------------------------------------------------------------------
# The dome
# ----------------------------------------------------------------------

@lru_cache(maxsize=1)
def dome_model():
    import geodesic_raw_wedge_dome_dihedral as d
    return d.build_physical_model(d.DomeConfig())


def dome() -> list[Piece]:
    import geodesic_raw_wedge_dome_dihedral as d
    m = dome_model()
    lift = np.array([0.0, 0.0, foundation_top()])
    out = []
    for k, member in enumerate(m.members):
        acc = d.MeshAccumulator()
        d.add_raw_sector_member(acc, m, member)
        md = acc.finish()
        sol = pc.moved(pc.from_mesh(md.vertices, md.indices), lift)
        out.append(Piece(f"D{k + 1:03d}", "dome", f"member {member.member_id} ({member.edge_type})", sol,
                         WOOD if member.edge_type == "A" else WOOD_B, "member",
                         {"edge_type": member.edge_type, "stock_in": round(float(member.physical_stock_length_in), 2)}))
    return out


def dome_skin() -> list[Piece]:
    m = dome_model()
    lift = np.array([0.0, 0.0, foundation_top()])
    out = []
    off = float(m.config.skin_offset_in)
    for k, face in enumerate(m.topology.faces):
        tri = m.topology.vertices[list(face.vertices)] + face.normal * off + lift
        sol = pc.from_rings(list(tri), list(tri + face.normal * 0.25), "skin")
        out.append(Piece(f"DS{k + 1:02d}", "dome_skin", f"skin panel {k + 1}", sol, SKIN, "skin"))
    return out


def dome_jig() -> list[Piece]:
    import geodesic_raw_wedge_dome_dihedral as d
    m = dome_model()
    meshes = d.build_fabrication_jig(m, 0, None)
    out = []
    for name, md in meshes.items():
        if not isinstance(md, d.MeshData) or not len(md.indices):
            continue
        out.append(Piece(f"DJ-{name}", "dome_jig", f"jig: {name.replace('jig_', '').replace('_', ' ')}",
                         pc.from_mesh(md.vertices, md.indices), JIG if "fixture" in name else WOOD, "jig"))
    return _recentre(out, DOME_JIG_AT) if out else out


# ----------------------------------------------------------------------
# The zome
# ----------------------------------------------------------------------

@lru_cache(maxsize=1)
def zome_model():
    from wedge_zome import geometry as g
    return g.build("wedge")


def _zome_lift():
    from wedge_zome import geometry as g
    return ZOME_AT + np.array([0.0, 0.0, g.D["sill_in"]])


def zome() -> list[Piece]:
    m = zome_model()
    lift = _zome_lift()
    out = []
    for p in m.panels:
        for k, st in enumerate(p.sticks):
            tails, heads = st.ends
            sol = pc.from_rings([t + lift for t in tails], [h + lift for h in heads])
            out.append(Piece(f"Z{p.index + 1:02d}{'ABCD'[k]}", "zome", f"row {p.row} panel {p.index + 1} stick {k + 1}",
                             sol, WOOD if k % 2 == 0 else WOOD_B, "member",
                             {"row": p.row, "length_in": round(float(st.lengths()[0]), 2)}))
    return out


def zome_skin() -> list[Piece]:
    m = zome_model()
    lift = _zome_lift()
    out = []
    for p in m.panels:
        quad = [m.vertices[k] + p.normal * 0.3 + lift for k in p.corners]
        sol = pc.from_rings(quad, [q + p.normal * 0.25 for q in quad], "skin")
        out.append(Piece(f"ZS{p.index + 1:02d}", "zome_skin", f"skin panel {p.index + 1}", sol, SKIN, "skin"))
    return out


def zome_jig() -> list[Piece]:
    """The zome world's jig table and its rulers, with the row-2 panel laid on it."""
    from wedge_zome import app as za
    s = za.State()
    for flag in ("wood", "skin", "grid", "person", "posts", "nodes", "ideal", "pinwheel", "channels"):
        if hasattr(s, flag):
            setattr(s, flag, False)
    s.jig, s.jig_row, s.jig_step = True, 2, 4
    meshes = za.Scene(s).build()
    md = meshes["jig"]
    if not len(md.indices):
        return []
    return _recentre([Piece("ZJ", "zome_jig", "jig table, row 2, rulers", pc.from_mesh(md.vertices, md.indices),
                            JIG, "jig")], ZOME_JIG_AT)


# ----------------------------------------------------------------------

def person(at=(200.0, -300.0)) -> list[Piece]:
    """A six-foot person for scale: declared, not derived."""
    x, y = at
    body = _box((x - 7, y - 4, 0), (x + 7, y + 4, 60))
    head = _box((x - 4, y - 4, 62), (x + 4, y + 4, 72))
    return [Piece("P1", "person", "a person, 6 ft", body, PERSON, "person"),
            Piece("P2", "person", "a person, 6 ft (head)", head, (0.80, 0.62, 0.48, 1.0), "person")]


BUILDERS = {"foundation": foundation, "foundation_deck": foundation_deck, "foundation_jig": foundation_jig,
            "dome": dome, "dome_skin": dome_skin, "dome_jig": dome_jig,
            "zome": zome, "zome_skin": zome_skin, "zome_jig": zome_jig,
            "mine": lambda: [], "person": person}


def build_all() -> dict[str, list[Piece]]:
    return {key: BUILDERS[key]() for key in LAYER_KEYS}


def foundation_facts() -> dict:
    """The pentagon and its star, from the solver: the book's figures."""
    B = foundation_model()
    side = float(np.linalg.norm(B.crown[1] - B.crown[0]))
    phi = (1 + 5 ** 0.5) / 2
    star = [m for m in B.members if m.role == "primary"]
    longs = sorted({round(m.length, 2) for m in star})
    cuts = sorted({round(m.s_hi - m.s_lo, 2) for m in star})
    by_len = {}
    for m in star:
        by_len.setdefault(round(m.length, 2), []).append(m)
    long_c, short_c = max(by_len), min(by_len)
    long_cut = round(float(np.mean([m.s_hi - m.s_lo for m in by_len[long_c]])), 2)
    short_cut = round(float(np.mean([m.s_hi - m.s_lo for m in by_len[short_c]])), 2)
    return {"side_in": side, "diagonal_in": phi * side, "phi": phi,
            "long_centre_in": long_c, "short_centre_in": short_c,
            "long_count": len(by_len[long_c]), "short_count": len(by_len[short_c]),
            "long_cut_in": long_cut, "short_cut_in": short_cut,
            "frame_count": sum(1 for m in B.members if m.role == "frame"),
            "spare_in": side - long_cut - short_cut, "top_in": float(B.top),
            "interior_deg": 108.0, "star_point_deg": 36.0, "lengths": longs, "cuts": cuts}


def validate_structures() -> None:
    layers = build_all()
    assert len(layers["dome"]) == len(dome_model().members)
    assert len(layers["zome"]) == sum(len(p.sticks) for p in zome_model().panels)
    assert len(layers["foundation"]) >= 20
    f = foundation_facts()
    assert abs(f["long_centre_in"] + f["short_centre_in"] - f["side_in"]) < 0.05, f
    assert f["long_count"] == 10 and f["short_count"] == 5 and f["frame_count"] == 5
    assert f["spare_in"] >= 0, "one log must yield one long and one short piece"
    # the dome stands on the foundation, the zome on the ground, nothing below it
    for key, ps in layers.items():
        for p in ps:
            assert np.all(np.isfinite(p.points())), (key, p.pid)
    dz = min(float(p.points()[:, 2].min()) for p in layers["dome"])
    assert abs(dz - foundation_top()) < 6.0, dz
