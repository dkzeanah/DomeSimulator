"""Cutting instructions, piece by piece, worked out from the solids.

For every piece: the stock it starts as, every measurement to mark, and each
cut written out the way you'd make it -- which face goes down on the saw
table, which side against the fence, which end to the right of the blade,
the mitre and which way it swings, the bevel and which way it tilts, where
the marks are, and what the offcut looks like when it falls away.

Saw conventions, used everywhere (and drawn in the 3-D tool):

* You stand in front of the saw. The fence is behind the blade. Left and
  right are yours.
* **Mitre** turns the cut across the table. "Front end right" means the cut
  line, followed from the fence toward you, drifts to the right.
* **Bevel** tilts the blade. Every setup here is chosen so the blade tilts
  to the **left**, the way a single-bevel mitre saw tilts; if a cut needs the
  other tilt, the piece is turned end for end instead.
* A cut the mitre saw cannot reach (more than 55° of mitre, or a cut
  running nearly along the stick) is given as marks for a circular saw,
  bandsaw or handsaw.

Each cut also carries what the 3-D tool needs to animate it: the stick, the
keeper and the offcut as solids, and the saw frame they sit in.
"""

from __future__ import annotations

import math
from dataclasses import dataclass, field

import numpy as np

from . import geom2d as g2
from . import solids as so
from .constants import C
from .patterns import MATERIALS, Layout, Piece

MITRE_MAX = 55.0
BEVEL_MAX = 46.0
END_MARGIN = 0.5     # the first cut takes this much past the stick's raw end


@dataclass
class Step:
    kind: str
    title: str
    text: str
    anim: dict | None = None


@dataclass
class Recipe:
    number: int
    name: str
    summary: str
    dims: list[tuple[str, str]]
    steps: list[Step]
    piece: Piece | None = None


# ----------------------------------------------------------------------
# Naming faces in words
# ----------------------------------------------------------------------

def _face_normal(solid: so.Solid, tag: str) -> np.ndarray | None:
    best, area = None, 0.0
    centre = solid.vertices().mean(axis=0)
    for poly, t in solid.faces:
        if t != tag:
            continue
        n = np.zeros(3)
        for i in range(len(poly)):
            n += np.cross(poly[i], poly[(i + 1) % len(poly)])
        a = float(np.linalg.norm(n))
        if a > area:
            area = a
            n = n / a
            if float(n @ (poly.mean(axis=0) - centre)) < 0:
                n = -n
            best = n
    return best


def face_words(solid: so.Solid, tag: str) -> str:
    n = _face_normal(solid, tag)
    if tag.startswith("ripped"):
        return "the ripped face"
    if n is None:
        return tag
    kind = "sawn face" if tag.startswith("sawn") else ("face" if tag.startswith("face") else "edge")
    if n[2] < -0.98:
        return f"the {kind} that lies on the flat side"
    if n[2] > 0.98:
        return f"the {kind} that lies on the open side"
    return f"the slanted {kind}" if kind == "sawn face" else f"the {kind}"


def corner_words(name: str, solid: so.Solid) -> str:
    if name.startswith("the bark corner of "):
        tag = name[len("the bark corner of "):]
        return "the bark corner of " + face_words(solid, tag)
    if " / " in name:
        a, b = name.split(" / ")
        return f"the corner between {face_words(solid, a)} and {face_words(solid, b)}"
    if name.startswith("corner "):
        a, b = name[len("corner "):].split("/")
        return f"the corner between {face_words(solid, a)} and {face_words(solid, b)}"
    return name


# ----------------------------------------------------------------------
# The saw
# ----------------------------------------------------------------------

@dataclass
class Setup:
    table_tag: str
    rot: int
    mitre: float
    bevel: float
    keeper_right: bool
    fence_corner: str
    frame: np.ndarray          # rows: saw x, y, z in panel coordinates
    feasible: bool
    score: float


def _section_corners(solid: so.Solid) -> list[tuple[str, float, float]]:
    out = []
    sect, tags = solid.section, solid.tags
    for i in range(len(sect)):
        if tags[i - 1] != tags[i]:
            out.append((so.corner_name(tags[i - 1], tags[i]), float(sect[i][0]), float(sect[i][1])))
    return out


def setups(solid: so.Solid, plane: so.Plane) -> list[Setup]:
    """Every way the stick can lie on the saw for this cut, best first."""
    out = []
    table_tags = [t for t in dict.fromkeys(solid.tags) if t.startswith(("sawn", "face", "ripped"))]
    corners = _section_corners(solid)
    for tag in table_tags:
        n_out = _face_normal(solid, tag)
        if n_out is None:
            continue
        z_s = -n_out
        for rot in (1, -1):
            x_s = solid.along * rot
            x_s = x_s - z_s * float(x_s @ z_s)
            if np.linalg.norm(x_s) < 1e-6:
                continue
            x_s /= np.linalg.norm(x_s)
            y_s = np.cross(z_s, x_s)
            n = plane.n
            ns = np.array([n @ x_s, n @ y_s, n @ z_s])
            keeper_right = ns[0] > 0
            if ns[0] < 0:
                ns = -ns
            mitre = math.degrees(math.atan2(ns[1], ns[0]))
            bevel = math.degrees(math.asin(max(-1.0, min(1.0, ns[2]))))
            # Which long corner sits against the fence (furthest back).
            back = max(corners, key=lambda c: float(solid.point(c[1], c[2], 0.0) @ y_s)) if corners else ("", 0, 0)
            feasible = 0.0 - 0.05 <= bevel <= BEVEL_MAX and abs(mitre) <= MITRE_MAX
            horizontal = abs(float(n_out[2])) > 0.98
            score = (1000 if feasible else 0) + (100 if horizontal else 0) + \
                (10 if back[0] == "the point" else 0) - abs(mitre) * 0.01
            out.append(Setup(tag, rot, mitre, bevel, keeper_right, back[0],
                             np.array([x_s, y_s, z_s]), feasible, score))
    out.sort(key=lambda s: -s.score)
    return out


def mitre_words(m: float) -> str:
    if abs(m) < 0.05:
        return "0° (square across)"
    side = "RIGHT" if m > 0 else "LEFT"
    return f"{abs(m):.1f}° — followed from the fence toward you, the cut drifts to the {side}"


def bevel_words(b: float) -> str:
    if abs(b) < 0.05:
        return "0° (blade upright)"
    return f"{abs(b):.1f}° — top of the blade tilted to the LEFT"


def _plane_hits(solid: so.Solid, plane: so.Plane, s0: float) -> list[tuple[str, float]]:
    """Where a cut plane crosses each long corner, measured from ``s0``."""
    out = []
    for name, x, z in _section_corners(solid):
        P0 = solid.point(x, z, 0.0)
        na = float(plane.n @ solid.along)
        if abs(na) < 1e-9:
            continue
        t = (plane.d - float(plane.n @ P0)) / na
        out.append((name, t - s0))
    return out


def _shape_words(lengths: list[tuple[str, float]], solid) -> str:
    ls = [(corner_words(n, solid), v) for n, v in lengths if v > 0.02]
    if not ls:
        return "only a sliver"
    hi = max(ls, key=lambda x: x[1])
    lo = min(ls, key=lambda x: x[1])
    if hi[1] - lo[1] < 0.1:
        return f"a square-ended block {hi[1]:.2f} in long"
    return (f"a tapered piece: {hi[1]:.2f} in along {hi[0]}, down to {lo[1]:.2f} in along {lo[0]}")


# ----------------------------------------------------------------------
# Recipes
# ----------------------------------------------------------------------

def strip_recipe(number: int, piece: Piece, L: Layout) -> Recipe:
    solid: so.Solid = piece.solid
    st = piece.stock
    cs = so.corners(solid)
    lengths = {n: hi - lo for n, lo, hi in cs}
    s_lo = min(lo for _n, lo, _hi in cs)
    s_hi = max(hi for _n, _lo, hi in cs)
    need = s_hi - s_lo
    stick = st.length
    s0 = s_lo - END_MARGIN
    dims = [("Stock", st.label + (f", from a {L.opts.infill_log_in:g} in log" if st.kind == "sector" else "")),
            ("Stick at least", f"{need + END_MARGIN + 0.25:.2f} in (sticks come {stick:.0f} in)")]
    for n, v in sorted(lengths.items(), key=lambda kv: -kv[1]):
        dims.append((f"Length along {corner_words(n, solid)}", f"{v:.2f} in"))
    if piece.trim > 0.01:
        dims.append(("Rip off first", f"{piece.trim:.2f} in at the bark, to sit flush"))
    steps: list[Step] = []
    steps.append(Step("stock", "Take the stock",
                      f"Take a {st.label.lower()} stick at least {need + END_MARGIN + 0.25:.2f} in long. "
                      f"Write {number} on it in chalk." +
                      ("" if stick >= need + END_MARGIN else
                       f" It is longer than a {stick:.0f} in stick: splice two, or cut it from a longer log.")))
    if piece.trim > 0.01:
        steps.append(Step("rip", "Rip it flush",
                          f"This piece stands taller than the frame. Rip {piece.trim:.2f} in off the bark side, "
                          f"parallel to the stick's length, so it sits flush with both faces of the panel. "
                          f"Lay it on a sawn face on the bandsaw or table saw; tilt the blade "
                          f"{st.angle_deg / 2:.2f}° (half the slice's angle) so the cut runs square to the "
                          f"slice's centre line."))
    cuts = [pl for pl in solid.planes]
    end1 = [pl for pl in cuts if float(pl.n @ solid.along) > math.sin(math.radians(15))]
    end2 = [pl for pl in cuts if float(pl.n @ solid.along) < -math.sin(math.radians(15))]
    rips = [pl for pl in cuts if not any(pl is q for q in end1 + end2)]
    stick_solid = so.prism(solid.section, solid.tags, solid.origin[:2], solid.along[:2], solid.across[:2],
                           float(solid.origin[2]))
    stick_solid = so.clip(stick_solid, so.Plane(solid.along, float(solid.along @ solid.origin) + s0, "raw end"))
    stick_solid = so.clip(stick_solid, so.Plane(-solid.along, -(float(solid.along @ solid.origin) + s0 + stick),
                                                "raw end"))
    current = stick_solid
    k = 0
    for group, label in ((end1, "first end"), (end2, "second end"), (rips, "along the length")):
        for pl in group:
            k += 1
            keeper = so.clip(current, pl)
            offcut = so.clip(current, so.Plane(-pl.n, -pl.d, "cut"))
            sets = setups(solid, pl)
            best = sets[0] if sets else None
            hits = _plane_hits(solid, pl, s0)
            meets = _meets(pl)
            off_len = []
            for name, x, z in _section_corners(solid):
                P0 = solid.point(x, z, 0.0)
                na = float(pl.n @ solid.along)
                if abs(na) < 1e-9:
                    continue
                t = (pl.d - float(pl.n @ P0)) / na
                off_len.append((name, (t - s0) if group is end1 else (s0 + stick - t)))
            if best is not None and best.feasible and group is not rips:
                place = (f"Lay the stick on {face_words(solid, best.table_tag)} on the saw table, with "
                         f"{corner_words(best.fence_corner, solid) or 'its back edge'} against the fence, "
                         f"the {'keeper' if True else ''} {'to the RIGHT' if best.keeper_right else 'to the LEFT'} "
                         f"of the blade.")
                if group is end1:
                    where = ("Slide it so the blade just clears the raw end everywhere -- about "
                             f"{END_MARGIN:g} in in from the end at its longest.")
                else:
                    marks = "; ".join(f"{_len_for(lengths, n):.2f} in along {corner_words(n, solid)}"
                                      for n, _v in hits if n in lengths)
                    where = (f"Measure from the first cut and mark: {marks}. Join the marks across "
                             f"{face_words(solid, best.table_tag)} -- the blade follows that line.")
                text = (f"{place} Mitre {mitre_words(best.mitre)}. Bevel {bevel_words(best.bevel)}. {where} "
                        f"The offcut, {'left' if best.keeper_right else 'right'} of the blade, is "
                        f"{_shape_words(off_len, solid)}"
                        + (" -- keep it: it is long enough for a shorter piece." if group is end2 and
                           max((v for _n, v in off_len), default=0) > 12 else ".") + f" This cut meets {meets}.")
                anim = {"type": "mitre", "frame": best.frame, "plane": pl, "stick": current,
                        "keeper": keeper, "offcut": offcut, "mitre": best.mitre, "bevel": best.bevel,
                        "keeper_right": best.keeper_right}
                steps.append(Step("saw", f"Cut {k} ({label}) on the mitre saw", text, anim))
            else:
                # Freehand: marks on the stick, and the tilt.
                marks = "; ".join(f"{max(0.0, v):.2f} in along {corner_words(n, solid)}" for n, v in off_len)
                tilt = math.degrees(math.acos(min(1.0, abs(float(pl.n[2]))))) if abs(pl.n[2]) < 1 else 0.0
                text = (f"Too steep for the mitre saw. Mark where this cut crosses each long corner, measured "
                        f"from the {'raw end' if group is end1 else 'far end'}: {marks}. Join the marks on every "
                        f"face and cut to the lines with a circular saw, bandsaw or handsaw. "
                        f"The cut face has to lie on {meets}: it leans "
                        f"{90 - tilt:.1f}° from the panel's plane.")
                anim = {"type": "freehand", "plane": pl, "stick": current, "keeper": keeper, "offcut": offcut}
                steps.append(Step("mark", f"Cut {k} ({label}), marked and cut by hand", text, anim))
            current = keeper
    finished = ", ".join(f"{v:.2f} in along {corner_words(n, solid)}" for n, v in
                         sorted(lengths.items(), key=lambda kv: -kv[1]))
    steps.append(Step("check", "Check it", f"Finished: {finished}. Measure each against the list before it "
                      f"goes in."))
    steps.append(Step("place", "Put it in",
                      f"It goes in as {piece.group.lower()}: {_pose_words(piece)}.",
                      {"type": "place", "solid": solid}))
    summary = f"{st.label}, {max(lengths.values()):.2f} / {min(lengths.values()):.2f} in"
    return Recipe(number, piece.group, summary, dims, steps, piece)


def _len_for(lengths: dict, name: str) -> float:
    return lengths.get(name, 0.0)


def _meets(pl: so.Plane) -> str:
    t = pl.tag
    if t.startswith("wall"):
        return "the frame's 45° wall"
    if t.startswith("edge"):
        return "the panel's edge (bevelled to the seam)"
    if t == "centre line":
        return "its mirror on the centre line"
    if t.startswith("end (square)"):
        return "the side of the next ring piece"
    return t


def _pose_words(piece: Piece) -> str:
    from .section import POSES
    return POSES.get(piece.pose, piece.pose)


def round_recipe(number: int, piece: Piece, L: Layout) -> Recipe:
    sp = piece.spec
    z0, z1 = sp["z"]
    t = z1 - z0
    D = 2 * float(np.linalg.norm(np.asarray(sp["plan"])[0] - np.asarray(sp["plan"]).mean(axis=0))) \
        if sp["type"] == "slab" else piece.long
    steps = [Step("stock", "Cut the round",
                  f"From a Ø{D:.1f} in log, square one end, mark {t:.2f} in (+{C['chainsaw_kerf_in']:g} in for "
                  f"the kerf) and cut across square with a guide. Write {number} on it.")]
    dims = [("Round", f"Ø{D:.1f} in, {t:.2f} in thick"), ("Layer", piece.group)]
    if piece.pose == "wall" and piece.solid is not None:
        c = np.asarray(sp["plan"]).mean(axis=0)
        for pl in piece.solid.planes:
            nxy = pl.n[:2]
            h = float(np.linalg.norm(nxy))
            if h < 1e-9:
                continue
            d_bot = (pl.d - float(nxy @ c) - pl.n[2] * z0) / h
            d_top = (pl.d - float(nxy @ c) - pl.n[2] * z1) / h
            dims.append(("Chord from the centre", f"{abs(d_bot):.2f} in (bottom face), {abs(d_top):.2f} in (top face)"))
            steps.append(Step("mark", "Mark and cut the chord",
                              f"On the face that goes down, draw a straight chord {abs(d_bot):.2f} in from the centre; "
                              f"on the face that goes up, the same chord {abs(d_top):.2f} in from the centre, parallel "
                              f"and on the same side. Cut joining the two lines -- the blade tilted "
                              f"{90 - math.degrees(math.atan2(h, abs(pl.n[2]))):.1f}° -- so the cut face lies on "
                              f"{_meets(pl)}.", {"type": "freehand", "plane": pl, "stick": piece.solid}))
    if piece.pose == "copy":
        shapes = sp.get("polys", [])
        sizes = []
        for s in shapes:
            w = s[:, 0].max() - s[:, 0].min()
            h = s[:, 1].max() - s[:, 1].min()
            sizes.append(f"{w:.1f} x {h:.1f} in")
        dims.append(("Gap pieces", ", ".join(sizes) or "-"))
        steps.append(Step("mark", "Trace and cut to fit",
                          f"Lay the round over the gap it is drawn on (the dashed circle). Trace the gap's outline "
                          f"onto it from below -- {len(shapes)} piece(s): {', '.join(sizes)}. Bandsaw on the lines; "
                          f"where a piece meets the frame, tilt the blade to the 45° wall.", None))
    steps.append(Step("place", "Put it in", f"{piece.group}: {_pose_words_round(piece)}.",
                      {"type": "place", "solid": piece.solid}))
    return Recipe(number, f"{piece.group} · {_pose_words_round(piece)}", f"Ø{D:.1f} x {t:.2f} in", dims,
                  steps, piece)


def _pose_words_round(piece: Piece) -> str:
    return {"full": "whole round", "wall": "round cut to the wall", "graded": "small round in a gap",
            "copy": "copied round, cut to fit"}.get(piece.pose, piece.pose)


def sheet_recipe(number: int, piece: Piece, L: Layout) -> Recipe:
    s = piece.solid
    v = s.vertices()
    top = v[v[:, 2] > v[:, 2].max() - 1e-6][:, :2]
    bot = v[v[:, 2] < v[:, 2].min() + 1e-6][:, :2]
    ht, hb = g2.hull(top), g2.hull(bot)

    def sides(h):
        return [float(np.linalg.norm(h[(i + 1) % len(h)] - h[i])) for i in range(len(h))]
    lo = ht.min(axis=0)
    marks = ", ".join(f"({x - lo[0]:.2f}, {y - lo[1]:.2f})" for x, y in ht)
    dims = [("Material", MATERIALS[piece.material][0]),
            ("Corners on the top face, from the sheet corner (x, y in)", marks),
            ("Sides, top face", ", ".join(f"{d:.2f}" for d in sides(ht)) + " in"),
            ("Sides, bottom face", ", ".join(f"{d:.2f}" for d in sides(hb)) + " in")]
    bev = [e.bevel for e in piece.ends]
    steps = [Step("mark", "Mark it on the sheet",
                  f"Measure in from one corner of the sheet and mark the corners {marks}. Snap a chalk line "
                  f"between each pair."),
             Step("saw", "Cut it",
                  ("Circular saw along each line, the blade bevelled " + ", ".join(f"{b:.1f}°" for b in bev)
                   + " on the edges in that order, the narrow face down, so each cut edge lies on the "
                   "frame's slope (or meets the next panel's covering).") if bev else
                  "Cut along the lines (snips or a knife for film; a nibbler or snips for metal).",
                  {"type": "freehand", "plane": s.planes[0] if s.planes else None, "stick": s}),
             Step("place", "Put it in", f"{piece.group}: {piece.note}", {"type": "place", "solid": s})]
    return Recipe(number, piece.group, f"{MATERIALS[piece.material][0]}", dims, steps, piece)


def recipes(L: Layout) -> list[Recipe]:
    out = []
    for i, p in enumerate(L.pieces):
        n = i + 1
        if p.solid is None:
            out.append(Recipe(n, p.group, "", [], [Step("note", "Cut", p.cut_text)], p))
        elif p.spec["type"] == "strip" and p.solid.tags:
            out.append(strip_recipe(n, p, L))
        elif p.material == "rounds":
            out.append(round_recipe(n, p, L))
        else:
            out.append(sheet_recipe(n, p, L))
    return out


def prep_card(L: Layout) -> Recipe | None:
    """Making the stock itself: logs to wedges, wedges to slices."""
    mat = L.opts.material
    if MATERIALS[mat][1] != "log":
        return None
    D = L.opts.infill_log_in
    R = D / 2
    chord8 = 2 * R * math.sin(math.radians(22.5))
    chord16 = 2 * R * math.sin(math.radians(11.25))
    steps = [Step("prep", "Split the log in eighths",
                  f"Buck the {D:g} in log to the strut length. Halve it through the pith with the chainsaw "
                  f"({C['chainsaw_kerf_in']:g} in kerf), quarter each half, then halve each quarter: eight "
                  f"wedges, each with two sawn faces {R:.2f} in wide meeting at the pith, bark {chord8:.2f} in "
                  f"across.")]
    if mat in ("s16", "s32"):
        steps.append(Step("prep", "Bandsaw each wedge in two",
                          f"Make a V-cradle: two boards meeting at 135° (each leaning 22.5° from upright). Lay "
                          f"the wedge in it on its two sawn faces, bark up -- no, point down, bark up -- so the "
                          f"wedge's centre line stands vertical. Set the fence {chord8 / 2:.2f} in from the "
                          f"blade, measured to the bark corner, and saw straight down the length: two 1/16 "
                          f"slices, 22.5° each."))
    if mat == "s32":
        steps.append(Step("prep", "And each half in two again",
                          f"Same again for each 1/16 slice in a cradle of 157.5° (boards leaning 11.25°), fence "
                          f"{chord16 / 2:.2f} in to the bark corner: four 1/32 slices, 11.25° each."))
    return Recipe(0, "Stock: from log to " + MATERIALS[mat][0].lower(), "", [("Log", f"Ø{D:g} in")], steps)


def validate_recipes() -> None:
    from .frame import Spec, solve
    from .patterns import Options, layout
    t = solve(Spec())["types"]
    for o in (Options("w8", "parallel", "flipflop"), Options("w8", "rings", "flipflop"),
              Options("s32", "across", "standing"), Options("fence", "chevron", "butted"),
              Options("rounds", "hex", "offset"), Options("osb", "sheet")):
        L = layout(t[0], o)
        rs = recipes(L)
        assert len(rs) == len(L.pieces)
        for r in rs:
            assert r.steps and r.dims is not None
    # Parallel runs ending on 45° walls: a feasible mitre-saw setup, bevel tilting left.
    L = layout(t[0], Options("w8", "parallel", "flipflop"))
    r = strip_recipe(5, L.pieces[4], L)
    saws = [s for s in r.steps if s.kind == "saw"]
    assert saws and all(0 <= s.anim["bevel"] <= BEVEL_MAX for s in saws)
    # The keeper and offcut of a cut add back up to the stick.
    s = saws[0].anim
    def vol(sol):
        v = sol.vertices()
        return 0 if len(v) == 0 else 1
    assert vol(s["keeper"]) and vol(s["offcut"])
