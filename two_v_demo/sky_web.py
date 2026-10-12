"""The sky web: building the dome in the air, from a cable web between four trees.

The owner's method (October 2026). Two wire ropes cross between four trees in
an X. A spiral of line is woven onto the X over the dome's footprint, so the
web covers the circle the dome will stand in -- but above it. A 12 V winch on
one tree pulls each triangle up to a block and hook hanging at the centre of
the X. The triangle rides up in a harness whose eye sits over its balance
point, so it comes up flat. Before it slips the harness, three pigtails of cord
-- one from each corner -- are thrown over the web, and the triangle is swung
out from the centre to where it belongs and left hanging there. Forty times,
until the whole dome floats, every triangle in its place, none yet joined to
the next. Then the pigtails are gathered to the apex, so that one bigger winch
at one central point can lift the whole dome evenly, up and down; the struts
may be lashed rather than screwed; a cotton skin soaked in silicone dissolved
in naphtha goes over it all; and the dome may simply stay up, off the ground,
in the shade of the trees that hold it. A second, higher web is experimental,
and depends on trees chosen for it beforehand.

Two tables. :data:`OWNER` holds what the owner weighed or owns -- the struts,
the winch -- and is measured. :data:`CONSTANTS` holds everything a person
assumed or estimated, each with a reason. Both go on screen before they are
used. The solver's own frame weight (:func:`cell_wall.frame_mass_kg`) is kept
beside the owner's, because it disagrees.

    py -3.12 -m two_v_demo.sky_web
"""

from __future__ import annotations

import math
from functools import lru_cache

import numpy as np

from . import cell_wall as cwall
from . import channel_facts as cf

IN = 0.0254
G = 9.81
LB_PER_KG = 2.2046226
KN_PER_LB = 0.0044482216

# name, value, unit, kind, why -- what the owner weighed, owns, or plans.
OWNER: tuple[tuple[str, float, str, str, str], ...] = (
    ("strut_kg_lo", 15.0, "kg", "weighed", "the owner's lightest strut"),
    ("strut_kg_hi", 22.0, "kg", "weighed", "the owner's heaviest strut; every load here uses it"),
    ("winch_lb", 1500.0, "lb", "owned", "the owner's 12 V battery winch, as rated"),
    ("upgrade_lo", 4.0, "x", "planned", "the smaller planned winch, times the present one"),
    ("upgrade_hi", 8.0, "x", "planned", "the larger planned winch, times the present one"),
)
O = {name: value for name, value, _u, _k, _w in OWNER}

# name, value, unit, kind, why -- everything a person assumed or estimated.
CONSTANTS: tuple[tuple[str, float, str, str, str], ...] = (
    ("tree_square_m", 9.0, "m", "assumption",
     "the four trees stand at the corners of a square round the pad"),
    ("anchor1_m", 8.0, "m", "assumption", "where the X is tied on each tree, the first web"),
    ("anchor2_m", 12.0, "m", "assumption", "where an experimental second web would be tied"),
    ("sag_ratio", 0.10, "-", "assumption",
     "each rope of the X sags 10% of its span: deep enough not to pull the trees over"),
    ("sag_ratio_taut", 0.05, "-", "assumption", "the flatter alternative: 5% of the span"),
    ("rope_3_8_kn", 67.2, "kN", "nominal", "3/8 in 6x19 IWRC EIPS wire rope, catalogue breaking strength"),
    ("rope_1_2_kn", 118.3, "kN", "nominal", "1/2 in, same construction"),
    ("rope_5_8_kn", 183.3, "kN", "nominal", "5/8 in, same construction"),
    ("rope_3_4_kn", 261.5, "kN", "nominal", "3/4 in, same construction"),
    ("rope_7_8_kn", 354.1, "kN", "nominal", "7/8 in, same construction"),
    ("rope_1_kn", 459.9, "kN", "nominal", "1 in, same construction"),
    ("design_factor", 5.0, "-", "standard", "wire rope is worked at a fifth of its breaking strength"),
    ("spiral_pitch_m", 0.5, "m", "assumption",
     "the spiral's turns half a metre apart, so a thrown pigtail always finds a strand"),
    ("web_margin_m", 0.8, "m", "assumption", "room between the web's lowest point and the top panel"),
    ("pigtail_tie_m", 0.5, "m", "allowance", "cord for the hitch at each end of a pigtail"),
    ("bridle_h_m", 1.0, "m", "assumption", "the harness eye, this far above a triangle's balance point"),
    ("tree_dbh_m", 0.45, "m", "assumption", "an anchor tree's trunk at the base"),
    ("green_mor_mpa", 35.0, "MPa", "estimate", "bending strength of green pine wood, low end"),
    ("green_e_gpa", 7.0, "GPa", "estimate", "stiffness of green pine wood, low end"),
    ("green_crush_mpa", 15.0, "MPa", "estimate", "crushing strength of green pine along the grain"),
    ("post_in", 5.5, "in", "nominal", "a milled 6x6 post, as sold"),
    ("post_e_gpa", 9.0, "GPa", "estimate", "stiffness of a dry milled pine post"),
    ("tree_factor", 3.0, "-", "assumption", "the margin a living tree should keep: they vary, and rot hides"),
    ("next_tree_m", 8.0, "m", "assumption",
     "the next tree out from each anchor tree, where its back-guy ties at the base"),
    ("hook_drop_m", 0.6, "m", "assumption", "block, hook and harness eye below the X's centre"),
    ("winch_m_min", 4.0, "m/min", "estimate", "a small 12 V winch's line speed at a light load"),
    ("winch_eff", 0.35, "-", "estimate", "battery to load: motor, gears and drum together"),
    ("battery_wh", 1200.0, "Wh", "assumption", "one 12 V, 100 Ah deep-cycle battery"),
    ("battery_use", 0.5, "-", "standard", "a lead-acid battery is drawn to half, no further"),
    ("float_gap_m", 0.12, "m", "assumption", "how far apart the hung triangles float before they are joined"),
    ("raise_step_m", 0.5, "m", "assumption", "how far one corner of the dome is winched up at a time"),
    ("rope_ea_mn", 5.0, "MN", "estimate",
     "1/2 in wire rope's stretch stiffness: metal area about 0.4 of the circle, E about 100 GPa"),
    ("pigtail_kn", 9.0, "kN", "nominal", "1/4 in double-braid polyester cord, catalogue breaking strength, approx"),
    ("master_drop_m", 0.5, "m", "assumption", "the free ring where the cords meet, this far under the apex"),
    ("cord_min_deg", 15.0, "deg", "assumption",
     "a cord flatter than this squeezes more than it lifts; that joint hangs on its struts instead"),
    ("lash_per_seam", 3.0, "-", "assumption", "lashings along each seam, if it is lashed rather than screwed"),
    ("lash_wraps", 8.0, "-", "assumption", "turns of cord in one lashing"),
    ("cotton_gsm", 340.0, "g/m2", "nominal", "10 oz cotton duck"),
    ("silicone_gsm", 150.0, "g/m2", "estimate", "silicone left in the cloth after one soak, dry"),
    ("skin_layers", 2.0, "-", "assumption", "layers of the silicone skin"),
    ("skin_overlap", 0.10, "-", "allowance", "laps and edges, on top of the dome's area"),
    ("mix_parts", 4.0, "-", "estimate", "naphtha to silicone, by volume, to make a soak thin enough"),
    ("silicone_kg_l", 1.04, "kg/L", "estimate", "density of 100% silicone sealant"),
    ("tube_ml", 300.0, "mL", "nominal", "one 10.1 oz cartridge"),
    ("tube_usd", 8.0, "$", "estimate", "one cartridge of 100% silicone"),
    ("naphtha_usd_l", 4.0, "$/L", "estimate", "VM&P naphtha by the gallon"),
    ("cotton_usd_m2", 7.0, "$/m2", "estimate", "cotton duck by the roll"),
    ("sailcloth_usd_m2", 25.0, "$/m2", "estimate", "woven polyester sailcloth, mid weight"),
    ("air_kg_m3", 1.2, "kg/m3", "standard", "air at sea level"),
    ("gust_m_s", 25.0, "m/s", "assumption", "a strong gale's gust, 90 km/h"),
    ("gust_hi_m_s", 40.0, "m/s", "assumption", "a storm's gust, 144 km/h"),
    ("dome_cd", 0.5, "-", "estimate", "drag of a skinned dome, side on"),
    ("transpire_l_day", 150.0, "L/day", "estimate", "water a mature pine draws from the ground on a summer day"),
)
C = {name: value for name, value, _u, _k, _w in CONSTANTS}

ROPES = (("3/8 in", "rope_3_8_kn"), ("1/2 in", "rope_1_2_kn"), ("5/8 in", "rope_5_8_kn"),
         ("3/4 in", "rope_3_4_kn"), ("7/8 in", "rope_7_8_kn"), ("1 in", "rope_1_kn"))


def _table(rows) -> str:
    width = max(len(n) for n, *_ in rows)
    return "\n".join(f"{n:<{width}}  {v:>8g} {u:<6} {k:<10} {w}" for n, v, u, k, w in rows)


def constants_table() -> str:
    return "WEIGHED OR OWNED BY THE OWNER\n" + _table(OWNER) + "\n\nDECLARED\n" + _table(CONSTANTS)


# ----------------------------------------------------------------------
# The dome's triangles, off the solver, at the owner's strut weights
# ----------------------------------------------------------------------

def strut_kg(which: str = "hi") -> float:
    return O["strut_kg_hi"] if which == "hi" else O["strut_kg_lo"]


@lru_cache(maxsize=None)
def triangles(which: str = "hi") -> dict:
    """Every face: corners (m, z from the rim), centroid, balance point,
    perimeter, and mass at the owner's strut weight: three struts a triangle."""
    topo = cf.reference_model().topology
    v = np.asarray(topo.vertices, dtype=float) * IN
    rim_z = float(v[:, 2].min())
    v = v - np.array([0.0, 0.0, rim_z])
    faces = []
    for f in topo.faces:
        corners = np.array([v[i] for i in f.vertices])
        edges = [(corners[k], corners[(k + 1) % 3]) for k in range(3)]
        lengths = np.array([np.linalg.norm(b - a) for a, b in edges])
        mids = np.array([(a + b) / 2 for a, b in edges])
        # The members lie along the edges: the panel balances at their length-weighted middle.
        balance = (mids * lengths[:, None]).sum(axis=0) / lengths.sum()
        faces.append({"corners": corners, "centroid": corners.mean(axis=0), "balance": balance,
                      "perimeter": float(lengths.sum()), "lengths": lengths,
                      "vertices": tuple(f.vertices)})
    for f in faces:
        f["mass_kg"] = 3 * strut_kg(which)
    frame = sum(f["mass_kg"] for f in faces)
    height = float(v[:, 2].max())
    return {"faces": faces, "frame_kg": frame, "height_m": height, "vertices": v,
            "radius_m": topo.sphere_radius_in * IN, "struts": 3 * len(faces)}


def weights() -> dict:
    """The owner's frame against the solver's."""
    hi, lo = triangles("hi"), triangles("lo")
    solver = cwall.frame_mass_kg()
    per = solver / hi["struts"]
    tri = [f["mass_kg"] for f in hi["faces"]]
    tri_lo = [f["mass_kg"] for f in lo["faces"]]
    return {"struts": hi["struts"], "frame_hi_kg": hi["frame_kg"], "frame_lo_kg": lo["frame_kg"],
            "tri_hi_kg": max(tri), "tri_lo_kg": min(tri_lo), "solver_kg": solver,
            "solver_strut_kg": per, "ratio_lo": O["strut_kg_lo"] / per, "ratio_hi": O["strut_kg_hi"] / per}


# ----------------------------------------------------------------------
# The X, the trees, the spiral
# ----------------------------------------------------------------------

def span_m() -> float:
    return C["tree_square_m"] * math.sqrt(2.0)


def rope_for(tension_kn: float) -> tuple[str, float]:
    """The smallest rope whose working load covers the tension."""
    for name, key in ROPES:
        if C[key] / C["design_factor"] >= tension_kn:
            return name, C[key] / C["design_factor"]
    return "larger than 1 in", C["rope_1_kn"] / C["design_factor"]


def _x_result(H: float, V: float, s: float, w: float) -> dict:
    tension = math.hypot(H, V)
    rope, wll = rope_for(tension)
    return {"span_m": span_m(), "sag_m": s, "load_kn": w, "horizontal_kn": H, "vertical_kn": V,
            "tension_kn": tension, "rope": rope, "rope_wll_kn": wll}


def x_tension(load_kg: float, sag_ratio: float | None = None) -> dict:
    """Both ropes of the X carrying a load at the crossing: what one central
    lift does, and the worst case for the web."""
    L = span_m()
    s = (sag_ratio if sag_ratio is not None else C["sag_ratio"]) * L
    w = load_kg * G / 1000                       # kN
    per_rope = w / 2
    return _x_result(per_rope * L / (4 * s), per_rope / 2, s, w)


def x_spread(sag_ratio: float | None = None, extra_kg: float = 0.0) -> dict:
    """The same X with the weight where the pigtails really put it: each
    corner's third of its triangle on the rope nearest it. A cable's pull is
    the beam moment at midspan over the sag (H = M / s)."""
    L = span_m()
    s = (sag_ratio if sag_ratio is not None else C["sag_ratio"]) * L
    t = triangles()
    scale = (t["frame_kg"] + extra_kg) / t["frame_kg"]
    ropes = {0: [], 1: []}
    for f in t["faces"]:
        for c in f["corners"]:
            u0, u1 = (c[0] + c[1]) / math.sqrt(2), (c[0] - c[1]) / math.sqrt(2)
            # Nearest rope: the one the corner is closer to, measured across.
            k, u = (0, u0) if abs(u1) <= abs(u0) else (1, u1)
            ropes[k].append((u, f["mass_kg"] * scale / 3 * G / 1000))
    worst = None
    for loads in ropes.values():
        m = sum(p * min(L / 2 + u, L / 2 - u) / 2 for u, p in loads)
        H = m / s
        V = max(sum(p * (L / 2 - u) / L for u, p in loads), sum(p * (L / 2 + u) / L for u, p in loads))
        r = _x_result(H, V, s, sum(p for _u, p in loads))
        if worst is None or r["tension_kn"] > worst["tension_kn"]:
            worst = r
    return worst


def slack_to_tight(sag_ratio: float) -> float:
    """How far the two trees of one rope must lean apart before the rope's sag
    is gone: a parabolic cable is L + 8 s^2 / 3L long."""
    L = span_m()
    s = sag_ratio * L
    return 8 * s * s / (3 * L)


def tree_check(horizontal_kn: float, anchor_m: float, rope_v_kn: float = 0.0) -> dict:
    """A rope's pull at the tie point. Unguyed, the trunk is a lever bent at
    its base. Guyed to the base of the next tree out, it is a post: squeezed
    from above, held at the tie, fixed in its roots."""
    moment = horizontal_kn * 1000 * anchor_m                    # N m
    d = C["tree_dbh_m"]
    section = math.pi * d ** 3 / 32                             # m^3
    stress = moment / section / 1e6                             # MPa
    angle = math.atan2(anchor_m, C["next_tree_m"])
    guy = horizontal_kn / math.cos(angle)
    squeeze = rope_v_kn + horizontal_kn * math.tan(angle)       # kN down the trunk
    area = math.pi * d * d / 4
    inertia = math.pi * d ** 4 / 64
    buckle = math.pi ** 2 * C["green_e_gpa"] * 1e9 * inertia / (0.7 * anchor_m) ** 2 / 1000   # kN
    return {"moment_knm": moment / 1000, "stress_mpa": stress, "factor": C["green_mor_mpa"] / stress,
            "needs_guy": C["green_mor_mpa"] / stress < C["tree_factor"], "guy_kn": guy,
            "guy_rope": rope_for(guy)[0], "guy_deg": math.degrees(angle),
            "guy_anchor_m": C["next_tree_m"], "squeeze_kn": squeeze,
            "crush_mpa": squeeze / area / 1000, "crush_factor": C["green_crush_mpa"] * area * 1000 / squeeze,
            "buckle_kn": buckle, "buckle_factor": buckle / squeeze,
            "uplift_kn": horizontal_kn * math.tan(angle)}


def post_vs_tree(anchor_m: float | None = None) -> dict:
    """The tree as a post, against the milled post it would be sawn into."""
    h = anchor_m or C["anchor1_m"]
    d = C["tree_dbh_m"]
    p = C["post_in"] * IN
    tree = math.pi ** 2 * C["green_e_gpa"] * 1e9 * (math.pi * d ** 4 / 64) / (0.7 * h) ** 2 / 1000
    post = math.pi ** 2 * C["post_e_gpa"] * 1e9 * (p ** 4 / 12) / (0.7 * h) ** 2 / 1000
    return {"tree_kn": tree, "post_kn": post, "times": tree / post, "height_m": h,
            "tree_area_cm2": math.pi * d * d / 4 * 1e4, "post_area_cm2": p * p * 1e4}


def spiral() -> dict:
    """An Archimedean spiral over the footprint, its turns a pitch apart."""
    r = triangles()["radius_m"]
    b = C["spiral_pitch_m"] / (2 * math.pi)
    theta = r / b
    length = b / 2 * (theta * math.sqrt(1 + theta * theta) + math.asinh(theta))
    return {"radius_m": r, "turns": r / C["spiral_pitch_m"], "length_m": length,
            "ties": int(math.ceil(r / C["spiral_pitch_m"])) * 4}


# ----------------------------------------------------------------------
# Hanging the triangles
# ----------------------------------------------------------------------

def web_z(r: float, anchor_m: float) -> float:
    """The web's height over a point r from the centre: the X's parabola,
    turned round the centre."""
    L = span_m()
    s = C["sag_ratio"] * L
    return anchor_m - s * max(0.0, 1.0 - (r / (L / 2)) ** 2)


def hang(anchor_m: float | None = None) -> dict:
    """Where the dome floats, and the pigtail from every corner up to the web."""
    anchor_m = anchor_m or C["anchor1_m"]
    t = triangles()
    apex_web = web_z(0.0, anchor_m)
    lift = apex_web - C["web_margin_m"] - t["height_m"]          # rim height above the ground
    pigtails = []
    for i, f in enumerate(t["faces"]):
        for c in f["corners"]:
            r = math.hypot(c[0], c[1])
            z = c[2] + lift
            pigtails.append({"face": i, "length_m": web_z(r, anchor_m) - z + C["pigtail_tie_m"]})
    lengths = [p["length_m"] for p in pigtails]
    return {"rim_m": lift, "apex_m": lift + t["height_m"], "web_centre_m": apex_web,
            "pigtails": len(pigtails), "pig_min_m": min(lengths), "pig_max_m": max(lengths),
            "cord_m": sum(lengths), "lengths": lengths}


def harness() -> dict:
    """Three legs from a triangle's corners to one eye straight over its
    balance point: hooked there, it comes up flat. Legs per kind of triangle."""
    kinds: dict[tuple, list[float]] = {}
    for f in triangles()["faces"]:
        key = tuple(sorted(round(float(x), 3) for x in f["lengths"]))
        n = np.cross(f["corners"][1] - f["corners"][0], f["corners"][2] - f["corners"][0])
        n /= np.linalg.norm(n)
        eye = f["balance"] + n * C["bridle_h_m"]
        legs = sorted(float(np.linalg.norm(eye - c)) for c in f["corners"])
        kinds.setdefault(key, legs)
    rows = [{"sides_m": list(k), "legs_m": legs} for k, legs in kinds.items()]
    return {"kinds": len(rows), "rows": rows}


def winch_kn(times: float = 1.0) -> float:
    return O["winch_lb"] * times * KN_PER_LB


def battery(mass_kg: float, height_m: float) -> dict:
    """Energy from the battery to lift a mass, through the winch's losses."""
    wh = mass_kg * G * height_m / C["winch_eff"] / 3600
    usable = C["battery_wh"] * C["battery_use"]
    return {"wh": wh, "usable_wh": usable, "lifts": usable / wh}


def hoist() -> dict:
    """One triangle up to the hook: the heaviest one against the 12 V winch."""
    t = triangles()
    h = hang()
    heaviest = max(f["mass_kg"] for f in t["faces"])
    lightest = min(f["mass_kg"] for f in triangles("lo")["faces"])
    hook_m = h["web_centre_m"] - C["hook_drop_m"]
    pull = heaviest * G / 1000
    minutes = hook_m / C["winch_m_min"]
    single = x_tension(heaviest)
    all_wh = sum(battery(f["mass_kg"], hook_m)["wh"] for f in t["faces"])
    return {"heaviest_kg": heaviest, "lightest_kg": lightest, "pull_kn": pull,
            "winch_kn": winch_kn(), "winch_margin": winch_kn() / pull, "hook_m": hook_m,
            "lift_min": minutes, "all_lift_min": minutes * len(t["faces"]),
            "single_tension_kn": single["tension_kn"], "one_wh": battery(heaviest, hook_m)["wh"],
            "all_wh": all_wh, "battery_share": all_wh / (C["battery_wh"] * C["battery_use"])}


def hang_order() -> list[int]:
    """Rim first, crown last: the hook comes down at the centre, so the middle
    has to stay clear until the end."""
    faces = triangles()["faces"]
    return sorted(range(len(faces)), key=lambda i: (-math.hypot(*faces[i]["centroid"][:2]),
                                                   math.atan2(faces[i]["centroid"][1], faces[i]["centroid"][0])))


def reach() -> dict:
    """Which triangles the hook can carry all the way to their place."""
    t = triangles()
    h = hang()
    top = h["web_centre_m"] - C["hook_drop_m"]
    short = []
    for i, f in enumerate(t["faces"]):
        n = np.cross(f["corners"][1] - f["corners"][0], f["corners"][2] - f["corners"][0])
        n /= np.linalg.norm(n)
        if np.dot(n, f["centroid"]) < 0:
            n = -n
        eye = f["balance"][2] + h["rim_m"] + n[2] * C["bridle_h_m"]
        if eye > top:
            short.append((i, eye - top))
    return {"hook_top_m": top, "short": len(short), "haul_max_m": max((d for _i, d in short), default=0.0),
            "short_faces": [i for i, _d in short]}


# ----------------------------------------------------------------------
# Joined: lashings, the cords to the apex, one central lift
# ----------------------------------------------------------------------

def seams() -> list[tuple[int, int]]:
    """Every edge two triangles share, as vertex pairs."""
    owners: dict[tuple, int] = {}
    for f in triangles()["faces"]:
        ids = f["vertices"]
        for k in range(3):
            key = tuple(sorted((ids[k], ids[(k + 1) % 3])))
            owners[key] = owners.get(key, 0) + 1
    return [k for k, n in owners.items() if n == 2]


def lashing() -> dict:
    """The seams lashed with cord instead of screwed: how much cord."""
    import seed_world

    g = seed_world.geometry()
    girth = 2 * (2 * g.member_width_in + g.member_depth_in) * IN      # round two members side by side
    n = len(seams())
    count = int(n * C["lash_per_seam"])
    per = C["lash_wraps"] * girth + C["pigtail_tie_m"]
    return {"seams": n, "lashings": count, "girth_m": girth, "per_m": per, "cord_m": count * per}


def node_loads() -> dict:
    """Each joint of the dome and the weight that hangs on it: a third of
    every triangle that meets there."""
    t = triangles()
    loads: dict[int, float] = {}
    for f in t["faces"]:
        for vid in f["vertices"]:
            loads[vid] = loads.get(vid, 0.0) + f["mass_kg"] / 3
    return loads


def apex_lift(extra_kg: float = 0.0) -> dict:
    """Every cord gathered to the apex. Two ways to run them.

    Lying on the struts under the shell, a cord pressed on a convex surface
    lifts nothing where it lies: what it pulls up at its corner it presses
    back down along its length, and the whole weight arrives at the cap. Run
    straight through the air inside the dome, from each joint to one free ring
    just under the cap, the cords do share it: each joint is lifted by its own
    cord, and one line leaves through the cap."""
    t = triangles()
    v = t["vertices"]
    loads = node_loads()
    scale = (t["frame_kg"] + extra_kg) / t["frame_kg"]
    apex_z = t["height_m"]
    ring = np.array([0.0, 0.0, apex_z - C["master_drop_m"]])
    rows = []
    strutted = []
    apex_vid = None
    for vid, kg in loads.items():
        p = v[vid]
        d = ring - p
        horiz = math.hypot(d[0], d[1])
        w = kg * scale * G / 1000
        if horiz < 1e-6:
            apex_vid = vid
            rows.append({"vid": vid, "w_kn": w, "t_kn": w, "in_kn": 0.0, "len_m": abs(float(d[2])),
                         "deg": 90.0, "r_m": 0.0, "z_m": float(p[2])})
            continue
        ang = math.atan2(d[2], horiz)
        if math.degrees(ang) < C["cord_min_deg"]:
            strutted.append(w)
            continue
        T = w / math.sin(ang)
        rows.append({"vid": vid, "w_kn": w, "t_kn": T, "in_kn": T * math.cos(ang),
                     "len_m": float(np.linalg.norm(d)), "deg": math.degrees(ang),
                     "r_m": horiz, "z_m": float(p[2])})
    # The joints too near the ring hang from the apex joint through the crown's struts.
    for r in rows:
        if r["vid"] == apex_vid:
            r["w_kn"] += sum(strutted)
            r["t_kn"] = r["w_kn"]
    rim = [r for r in rows if abs(r["z_m"]) < 1e-6]
    n_rim = len(rim)
    rim_in = max(r["in_kn"] for r in rim)
    # A ring of n joints each pushed in by F carries F / (2 sin(pi/n)) round it.
    hoop = rim_in / (2 * math.sin(math.pi / n_rim))
    # Where a rim joint's cord passes halfway to the wall, above the rim (the floor).
    half = (apex_z - C["master_drop_m"]) * 0.5
    total = sum(r["w_kn"] for r in rows)
    return {"cords": len(rows), "joints": len(loads), "strutted": len(strutted),
            "apex_kn": next(r["w_kn"] for r in rows if r["vid"] == apex_vid), "max_t_kn": max(r["t_kn"] for r in rows),
            "min_deg": min(r["deg"] for r in rows), "rim_deg": rim[0]["deg"], "rim_joints": n_rim,
            "rim_in_kn": rim_in, "rim_hoop_kn": hoop, "cord_m": sum(r["len_m"] for r in rows),
            "lift_kn": total, "head_half_m": half, "rows": rows,
            "max_in_kn": max(r["in_kn"] for r in rows),
            "pigtails_per_joint": 3 * len(t["faces"]) / len(loads)}


def skin() -> dict:
    """Cotton soaked in silicone thinned with naphtha: what the dome takes."""
    area = cwall.networks().shell_m2 * (1 + C["skin_overlap"])
    layers = C["skin_layers"]
    sil_kg = area * layers * C["silicone_gsm"] / 1000
    sil_l = sil_kg / C["silicone_kg_l"]
    tubes = math.ceil(sil_l * 1000 / C["tube_ml"])
    naphtha = sil_l * C["mix_parts"]
    cotton = area * layers
    mass = area * layers * (C["cotton_gsm"] + C["silicone_gsm"]) / 1000
    diy = tubes * C["tube_usd"] + naphtha * C["naphtha_usd_l"] + cotton * C["cotton_usd_m2"]
    sail = area * layers * C["sailcloth_usd_m2"]
    return {"area_m2": area, "shell_m2": cwall.networks().shell_m2, "layers": layers, "silicone_kg": sil_kg,
            "silicone_l": sil_l, "tubes": tubes, "naphtha_l": naphtha, "cotton_m2": cotton,
            "mass_kg": mass, "diy_usd": diy, "sail_usd": sail, "per_m2_usd": diy / cotton,
            "sail_per_m2_usd": C["sailcloth_usd_m2"]}


def hung_kg() -> float:
    """The dome as it would hang for good: the owner's frame and the skin."""
    return triangles()["frame_kg"] + skin()["mass_kg"]


def one_point() -> dict:
    """The whole dome on one winch at the centre, against the planned winches,
    and what that does to the X: the whole weight now at the crossing."""
    W = hung_kg()
    w = W * G / 1000
    lo, hi = winch_kn(O["upgrade_lo"]), winch_kn(O["upgrade_hi"])
    xd = x_tension(W)
    xt = x_tension(W, C["sag_ratio_taut"])
    rise = hang()["rim_m"] - 0.62
    return {"mass_kg": W, "w_kn": w, "now_kn": winch_kn(), "lo_kn": lo, "hi_kn": hi,
            "now_x": winch_kn() / w, "lo_x": lo / w, "hi_x": hi / w, "xd": xd, "xt": xt,
            # A winch at the tree pulls through a block at the crossing: the line
            # comes in level and leaves straight down, so the block takes both.
            "block_kn": w * math.sqrt(2), "rise_m": rise, "wh": battery(W, rise)["wh"],
            "tree": tree_check(xd["horizontal_kn"], C["anchor1_m"], xd["vertical_kn"])}


def level() -> dict:
    """How level the dome hangs from one point. A symmetric frame's weight is
    on its axis; struts of different weight move it. Unsorted struts, drawn at
    random between the owner's lightest and heaviest, and the worst case --
    every heavy strut on one side."""
    t = triangles()
    topo_v = t["vertices"]
    edges = []
    for f in t["faces"]:
        ids = f["vertices"]
        for k in range(3):
            a, b = topo_v[ids[k]], topo_v[ids[(k + 1) % 3]]
            edges.append((a + b) / 2)
    mids = np.array(edges)
    pivot_z = t["height_m"] - C["master_drop_m"]
    lo, hi = O["strut_kg_lo"], O["strut_kg_hi"]

    def tilt(masses: np.ndarray) -> float:
        com = (mids * masses[:, None]).sum(axis=0) / masses.sum()
        off = math.hypot(com[0], com[1])
        return math.degrees(math.atan2(off, pivot_z - com[2]))
    rng = np.random.default_rng(7)
    random = [tilt(rng.uniform(lo, hi, len(mids))) for _ in range(2000)]
    side = np.where(mids[:, 0] > 0, hi, lo)
    even = tilt(np.full(len(mids), (lo + hi) / 2))
    com_z = float((mids[:, 2]).mean())
    return {"even_deg": even, "random_med_deg": float(np.median(random)),
            "random_95_deg": float(np.percentile(random, 95)), "worst_deg": tilt(side),
            "depth_m": pivot_z - com_z, "rim_drop_mm_95": 1000 * 2 * t["radius_m"]
            * math.sin(math.radians(float(np.percentile(random, 95))))}


def wind() -> dict:
    """What a tree's sway does to a web with no slack left; how a hung
    triangle swings; and how far wind swings the whole skinned dome."""
    L = span_m()
    per_cm = C["rope_ea_mn"] * 1000 * 0.01 / L          # kN of tension per cm of stretch
    lengths = hang()["lengths"]
    lo, hi = min(lengths) - C["pigtail_tie_m"], max(lengths) - C["pigtail_tie_m"]
    t = triangles()
    per_pig = max(f["mass_kg"] for f in t["faces"]) * G / 3 / 1000
    R = t["radius_m"]
    area = math.pi * R * R / 2
    W = hung_kg() * G / 1000

    def push(v: float) -> float:
        return 0.5 * C["air_kg_m3"] * v * v * C["dome_cd"] * area / 1000
    f1, f2 = push(C["gust_m_s"]), push(C["gust_hi_m_s"])
    return {"kn_per_cm": per_cm, "period_lo_s": 2 * math.pi * math.sqrt(lo / G),
            "period_hi_s": 2 * math.pi * math.sqrt(hi / G), "pig_load_kn": per_pig,
            "pig_factor": C["pigtail_kn"] / per_pig, "side_m2": area, "gust_kn": f1, "storm_kn": f2,
            "gust_deg": math.degrees(math.atan2(f1, W)), "storm_deg": math.degrees(math.atan2(f2, W)),
            "w_kn": W}


def nature() -> dict:
    trees = 4
    return {"trees": trees, "drink_l_day": trees * C["transpire_l_day"],
            "ground_contact": 0, "anchors_bought": 0}


def raising() -> dict:
    """Up to an experimental second web a corner at a time, and why the first web has to go."""
    t = triangles()
    h1, h2 = hang(), hang(C["anchor2_m"])
    rise = h2["rim_m"] - h1["rim_m"]
    rounds = int(math.ceil(rise / C["raise_step_m"]))
    span = 2 * t["radius_m"]
    a = C["tree_square_m"] / 2
    trees = [(a, a), (-a, a), (-a, -a), (a, -a)]
    corners = [0.0] * 4
    for f in t["faces"]:
        az = math.atan2(f["centroid"][1], f["centroid"][0])
        near = min(range(4), key=lambda k: abs((math.atan2(trees[k][1], trees[k][0]) - az + math.pi)
                                                 % math.tau - math.pi))
        corners[near] += f["mass_kg"]
    pull = max(corners) * G / 1000
    return {"rise_m": rise, "rounds": rounds, "pulls": rounds * 4,
            "tilt_deg": math.degrees(math.atan(C["raise_step_m"] / span)),
            "corner_kg": corners, "corner_pull_kn": pull, "winch_ok": winch_kn() >= pull,
            "lo_ok": winch_kn(O["upgrade_lo"]) >= pull,
            "clash_m": h2["apex_m"] - h1["web_centre_m"], "web1_centre_m": h1["web_centre_m"],
            "apex2_m": h2["apex_m"]}


def safety() -> dict:
    h = hoist()
    v = math.sqrt(2 * G * h["hook_m"])
    return {"drop_m": h["hook_m"], "impact_m_s": v, "impact_kmh": v * 3.6,
            "energy_kj": 0.5 * h["heaviest_kg"] * v * v / 1000}


def tree_xy() -> list[tuple[float, float]]:
    """The four anchor trees, round the pad's centre; the winch is on the first."""
    a = C["tree_square_m"] / 2
    return [(-a, -a), (a, -a), (a, a), (-a, a)]


def next_tree_xy() -> list[tuple[float, float]]:
    """The next tree out beyond each anchor tree, where its guy ties at the base."""
    out = []
    for x, y in tree_xy():
        r = math.hypot(x, y)
        k = (r + C["next_tree_m"]) / r
        out.append((x * k, y * k))
    return out


def materials() -> dict:
    t = triangles()
    guy = math.hypot(C["anchor1_m"], C["next_tree_m"])
    return {"x_m": span_m() * 2, "spiral_m": spiral()["length_m"], "guys_m": 4 * guy,
            "pigtails_m": hang()["cord_m"], "triangles": len(t["faces"])}


def facts() -> dict:
    t = triangles()
    full = x_tension(t["frame_kg"])
    taut = x_tension(t["frame_kg"], C["sag_ratio_taut"])
    spread = x_spread()
    spread_taut = x_spread(C["sag_ratio_taut"])
    sk = skin()
    return {
        "faces": len(t["faces"]), "frame_kg": t["frame_kg"], "frame_lb": t["frame_kg"] * LB_PER_KG,
        "height_m": t["height_m"], "radius_m": t["radius_m"], "weights": weights(),
        "x": full, "x_taut": taut, "spread": spread, "spread_taut": spread_taut,
        "tree1": tree_check(spread["horizontal_kn"], C["anchor1_m"], spread["vertical_kn"]),
        "tree1_taut": tree_check(spread_taut["horizontal_kn"], C["anchor1_m"], spread_taut["vertical_kn"]),
        "tree2": tree_check(spread["horizontal_kn"], C["anchor2_m"], spread["vertical_kn"]),
        "post": post_vs_tree(),
        "order": hang_order(), "raise": raising(), "wind": wind(), "safety": safety(),
        "materials": materials(), "reach": reach(), "lash": lashing(), "apex": apex_lift(sk["mass_kg"]),
        "skin": sk, "one": one_point(), "level": level(), "nature": nature(),
        "tight_m": slack_to_tight(C["sag_ratio"]), "tight_taut_m": slack_to_tight(C["sag_ratio_taut"]),
        "spiral": spiral(), "hang": hang(), "hang2": hang(C["anchor2_m"]), "harness": harness(),
        "hoist": hoist(), "per_tonne_kn": x_tension(1000.0)["tension_kn"],
        "floor": floor_load(),
    }


def floor_load() -> dict:
    """A floor and its contents, from the cell wall's own table, hung too."""
    n = cwall.networks()
    floor = n.plan_m2 * cwall.C["floor_kg_m2"]
    W = hung_kg() + floor
    x = x_tension(W)
    return {"floor_kg": floor, "mass_kg": W, **x}


def validate_sky_web() -> None:
    f = facts()
    t = triangles()
    w = f["weights"]
    assert f["faces"] == 40 and w["struts"] == 120
    assert abs(w["frame_hi_kg"] - 120 * O["strut_kg_hi"]) < 1e-6 and abs(w["frame_lo_kg"] - 120 * O["strut_kg_lo"]) < 1e-6
    assert w["ratio_lo"] > 2 > 1, "the film says the owner's struts weigh two to three times the solver's"
    assert f["x"]["tension_kn"] > f["spread"]["tension_kn"], "spreading the load lowers the pull"
    assert f["spread_taut"]["tension_kn"] > f["spread"]["tension_kn"], "more sag, less tension"
    assert f["tight_taut_m"] < f["tight_m"] < 1.0
    assert f["hang"]["rim_m"] > 0.62 and f["hang"]["pigtails"] == 120
    assert f["hoist"]["winch_margin"] > 5 and f["hoist"]["battery_share"] < 0.5
    assert f["tree1"]["needs_guy"] and f["tree1_taut"]["factor"] < 1, "every web wants guys; a taut one breaks trees"
    assert f["tree1"]["buckle_factor"] > 10 and f["post"]["times"] > 10, "a guyed tree is a far better post"
    assert f["raise"]["clash_m"] > 0
    o = f["order"]
    r = [math.hypot(*t["faces"][i]["centroid"][:2]) for i in o]
    assert r[0] >= r[-1] and len(set(o)) == 40
    assert f["wind"]["pig_factor"] > 10
    a = f["apex"]
    assert a["joints"] == 26 and abs(a["lift_kn"] - hung_kg() * G / 1000) < 1e-6
    assert f["lash"]["seams"] == 55
    one = f["one"]
    assert one["now_x"] < 1 < one["hi_x"], "the present winch cannot lift the dome; the bigger one can"
    assert 0.95 < one["lo_x"] < 1.2, "the film says the 4x winch lifts it with almost nothing to spare"
    assert one["xt"]["tension_kn"] > 1.8 * one["xd"]["tension_kn"]
    lv = f["level"]
    assert lv["even_deg"] < 0.05 and lv["random_95_deg"] < lv["worst_deg"]
    assert f["wind"]["gust_deg"] < 10
    assert f["skin"]["diy_usd"] < f["skin"]["sail_usd"]


if __name__ == "__main__":
    validate_sky_web()
    f = facts()
    for k, v in f.items():
        if isinstance(v, dict):
            print(k, {a: (round(b, 3) if isinstance(b, float) else b) for a, b in v.items()
                      if a not in ("lengths", "rows")})
        elif isinstance(v, list):
            print(k, v[:6])
        else:
            print(k, round(v, 3) if isinstance(v, float) else v)
