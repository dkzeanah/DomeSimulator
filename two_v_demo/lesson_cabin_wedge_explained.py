"""The Wedge Dome, Explained -- and the channel in every seam.

A complete explanation in the Cabin World: the log, the eight rip cuts,
the member, the pinwheel, the doubled seams, and then the part this film
exists for -- the V two sawn faces leave at every seam, the hollow key that
turns it into a service channel, what fits in it (water and wire), what
does not (a round duct), why the channel does not need one (it *is* one),
the Peltier plates and the three-way gate, the key becoming a spacer and
what that costs in dome size, printing the key in halves, and where the
channels meet.

Every figure comes from :mod:`two_v_demo.channel_facts` (which reads the
raw-wedge solver), :mod:`wedge_book.systems` and :mod:`seed_world`. The
sizes of pipe, cable and duct are declared there with a reason each, and
are put on screen before they are used.

    py -3.12 -m rerender stills cabin_wedge_explained
    py -3.12 -m rerender render cabin_wedge_explained
"""

from __future__ import annotations

import math

import numpy as np

from . import cabin_world as cw
from . import channel_facts as cf
from . import channel_scene as sc
from . import shots
from .lessons import Chapter, Lesson
from .render_kit import WorldLabel

WHITE = (240, 236, 226)
AMBER = (255, 205, 130)
GREEN = (111, 235, 155)
BLUE = (120, 200, 255)
RED = (255, 140, 120)


# ----------------------------------------------------------------------
# Every number the film states
# ----------------------------------------------------------------------

def _facts() -> dict:
    import seed_world
    from wedge_book import systems

    g = seed_world.geometry()
    clock = systems.build_clock()
    m = cw.landmarks()
    types = cf.seam_types()
    wide = max(types, key=lambda t: t.gap_deg)
    tight = min(types, key=lambda t: t.gap_deg)
    rw, rt = cf.room(wide), cf.room(tight)
    fill_t = cf.fits(rt)[1]
    fill_w = cf.fits(rw)[1]
    air = cf.air()
    air_t = next(x for x in air["per_type"] if x["seam"] == tight)
    sp3 = cf.spacer_for(("duct_3",))
    sp4 = cf.spacer_for(("duct_4",) + cf.BUNDLE)
    hub = cf.hubs(sp4.shift_in)
    ways = dict(hub.by_valence)
    node = dict(hub.node_radius_in)
    pr = cf.printing()
    water = systems.water_comparison()
    seams = g.seam_count
    long_ = next(x for x in g.members if x.edge_type == "A")
    short = next(x for x in g.members if x.edge_type == "B")
    logs = cf.by_log()
    return {
        "splits": m.splits, "sector": 360.0 / m.splits,
        "members": int(clock["members"]), "faces": len(cf.reference_model().topology.faces),
        "long": long_.stock_length_in, "short": short.stock_length_in,
        "long_n": long_.count, "short_n": short.count,
        "seams": seams, "rim": int(clock["members"]) - 2 * seams,
        "trunk": cf.reference_model().config.trunk_diameter_in,
        "fold_w": wide.fold_deg, "fold_t": tight.fold_deg,
        "gap_w": wide.gap_deg, "gap_t": tight.gap_deg,
        "n_w": wide.count, "n_t": tight.count, "depth": tight.depth_in,
        "open_t": tight.opening_in, "open_w": wide.opening_in,
        "seam_ft": g.seam_length_in / 12.0,
        "bolts": int(systems.declared("bolts_per_seam")),
        "wall_mm": cf.K["key_wall_in"] * cf.MM_PER_IN,
        "area_t": rt.inside_in2, "area_w": rw.inside_in2,
        "round_t": rt.inside_round_in, "round_w": rw.inside_round_in,
        "eqduct_t": rt.equal_area_duct_in,
        "fill_t": fill_t * 100, "fill_w": fill_w * 100, "fill_rule": cf.K["fill_fraction"] * 100,
        "need_cfm": air["need_cfm"], "cfm_t": air_t["cfm"], "fpm": cf.K["quiet_air_fpm"],
        "seams_for_air": math.ceil(air_t["seams_for_the_dome"]),
        "shift3": sp3.shift_in, "grow3": sp3.radius_growth_pct,
        "shift4": sp4.shift_in, "grow4": sp4.radius_growth_pct,
        "sp4_t": sp4.actual_in[types.index(tight)], "sp4_w": sp4.actual_in[types.index(wide)],
        "n5": ways.get("5-way", 0), "n6": ways.get("6-way", 0), "nrim": ways.get("rim", 0),
        "node5": 2 * node.get(5, 0.0), "node6": 2 * node.get(6, 0.0),
        "half_keys": pr.half_keys, "profiles": pr.profiles, "segments": pr.segments,
        "seg_each": max(pr.segments_each), "bed_mm": cf.K["printer_bed_in"] * cf.MM_PER_IN,
        "kg": pr.mass_kg, "usd": pr.cost_usd, "hours": pr.print_hours,
        "days": pr.print_hours / 24.0,
        "kg_seam": pr.mass_kg / seams, "h_seam": pr.print_hours / seams,
        "usd_seam": pr.cost_usd / seams,
        "pel_w": water["peltier_watts"], "pel_gal": water["peltier_gallons_per_year"],
        "pel_rain": water["rain_inches_equal_to_a_year"],
        "pel_hours": systems.declared("peltier_run_hours"),
        "module_usd": systems.seam_module().cost,
        "logs": logs,
    }


F = _facts()


def _label(app, point, text, colour=WHITE) -> None:
    app.world_labels.append(WorldLabel(np.asarray(point, dtype=np.float32), text, colour))


# ----------------------------------------------------------------------
# Painters
# ----------------------------------------------------------------------

def _bench(app, transparent, *, bundle=True, bolted=True, key=True, subject_world=False):
    cw.paint(app, subject=subject_world)
    frame = sc.paint_bench(app, "a", bundle=bundle, bolted=bolted)
    if key:
        sc.key_shell(transparent, frame, sc.tight(), 0.0)
    return frame


def p_grain(app, opaque, transparent, p):
    cw.paint(app)
    m = cw.landmarks()
    _label(app, m.log_end + [0, 0, m.trunk_r * 1.4], f"{F['splits']} WEDGES, ONE LOG", AMBER)


def p_member(app, opaque, transparent, p):
    cw.paint(app)
    m = cw.landmarks()
    _label(app, m.stack + [0.9, 0.9, 0.75], f"{F['sector']:.0f} DEGREE SECTOR", AMBER)
    _label(app, m.stack + [0.9, 0.9, 0.55], "ROUND FACE OUT, POINT IN", WHITE)


def p_counts(app, opaque, transparent, p):
    cw.paint(app)
    m = cw.landmarks()
    _label(app, m.apex + [0, 0, 0.7], f"{F['members']} MEMBERS", AMBER)
    _label(app, m.apex + [0, 0, 0.35], f"{F['faces']} FLAT PANELS", WHITE)


def p_pinwheel(app, opaque, transparent, p):
    cw.paint(app)
    m = cw.landmarks()
    _label(app, m.gap + [0, 0, 0.55], "NO HUBS: A PINWHEEL", AMBER)


def p_doubled(app, opaque, transparent, p):
    cw.paint(app)
    sc.paint_seams(app)
    m = cw.landmarks()
    _label(app, m.apex + [0, 0, 0.6], f"{F['seams']} DOUBLED SEAMS", AMBER)


def p_vee(app, opaque, transparent, p):
    frame = _bench(app, transparent, bundle=False, bolted=False, key=False)
    _label(app, frame.at(0, 0.6, 0), f"{F['gap_t']:.1f} DEG V", AMBER)
    _label(app, frame.at(3.2, -3.0, 0), f"{F['depth']:.0f} IN DEEP", WHITE)


def p_key(app, opaque, transparent, p):
    frame = _bench(app, transparent, bundle=False)
    _label(app, frame.at(0, 0.8, 0), "THE KEY", AMBER)
    _label(app, frame.at(-3.5, -1.0, 0.22), f"{F['bolts']} BOLTS A SEAM", WHITE)


def p_room(app, opaque, transparent, p):
    frame = _bench(app, transparent, bundle=False)
    _label(app, frame.at(0, 0.8, 0), f"{F['area_t']:.1f} SQ IN INSIDE", AMBER)
    _label(app, frame.at(0, -3.4, 0), f"{F['round_t']:.2f} IN ROUND", BLUE)


def p_sizes(app, opaque, transparent, p):
    frame = _bench(app, transparent)
    _label(app, frame.at(0, 0.8, 0), "THE SIZES WE ASSUMED", AMBER)


def p_bundle(app, opaque, transparent, p):
    frame = _bench(app, transparent)
    _label(app, frame.at(0, 0.8, 0), f"4 SERVICES, {F['fill_t']:.0f}% FULL", GREEN)
    _label(app, frame.at(3.4, -5.2, 0), "PEX, 14/2, 12 V, DRAIN", WHITE)


def p_ducts(app, opaque, transparent, p):
    frame = _bench(app, transparent)
    duct = cf.SERVICE["duct_3"]
    centre = sc.inner(sc.tight())
    mid = (min(q[1] for q in centre) + max(q[1] for q in centre)) / 2
    grow = 0.3 + 0.7 * min(1.0, p * 2.0)
    # The duct's outline on the end face: plainly wider than the V it would go in.
    r = duct.width_in / 2 * grow
    steps = 48
    for k in range(steps):
        a, b = math.tau * k / steps, math.tau * (k + 1) / steps
        ring = [frame.at(rr * math.cos(t), mid + rr * math.sin(t), -0.004)
                for rr, t in ((r - 0.12, a), (r + 0.12, a), (r + 0.12, b), (r - 0.12, b))]
        opaque.quad(*ring, (1.0, 0.25, 0.20, 1.0), np.array([0.0, -1.0, 0.0]))
    _label(app, frame.at(0, 1.2, 0), "A 3 IN DUCT DOES NOT FIT", RED)


def p_air(app, opaque, transparent, p):
    cw.paint(app)
    for a, b in sc.air_seams():
        opaque.cylinder(a, b, 0.05, sc.CYAN, 10)
        d = b - a
        for k in range(4):
            c = a + d * ((k / 4 + p * 0.9) % 1.0)
            opaque.cone(c, c + d / np.linalg.norm(d) * 0.28, 0.11, sc.AIR, 12)
    m = cw.landmarks()
    _label(app, m.apex + [0, 0, 0.7], f"DOME NEEDS {F['need_cfm']:.0f} CFM", AMBER)
    _label(app, m.apex + [0, 0, 0.35], f"ONE SEAM MOVES {F['cfm_t']:.0f}", BLUE)


def p_dehumid(app, opaque, transparent, p):
    frame = _bench(app, transparent)
    t = sc.tight()
    where = sc.peltier_and_gate(opaque, frame, t)
    sc.air_arrows(opaque, frame, t, 0.0, p)
    _label(app, where["fins"] + [0, 0, -0.07], "PELTIER: COLD IN, HEAT TO ROOM", BLUE)
    _label(app, where["along"] + [0, 0, 0.12], "3-WAY GATE", AMBER)
    _label(app, where["silica"] + [0, 0, -0.09], "SILICA", WHITE)
    _label(app, where["isolate"] + [0.03, 0, 0.03], "ISOLATE", WHITE)


def p_water(app, opaque, transparent, p):
    cw.paint(app)
    m = cw.landmarks()
    _label(app, m.apex + [0, 0, 0.7], f"{F['pel_gal']:.0f} GAL A YEAR", BLUE)
    _label(app, m.apex + [0, 0, 0.35], f"= {F['pel_rain']:.1f} IN OF RAIN", RED)


def p_spacer(app, opaque, transparent, p):
    cw.paint(app, subject=False)
    frame_a = sc.paint_bench(app, "a")
    sc.key_shell(transparent, frame_a, sc.tight(), 0.0)
    frame_b = sc.paint_bench(app, "b")
    sc.key_shell(transparent, frame_b, sc.tight(), sc.spacer_4())
    _label(app, frame_a.at(0, 0.9, 0), "AS BUILT", WHITE)
    _label(app, frame_b.at(0, 0.9, 0), f"SPACER: 4 IN DUCT", AMBER)
    _label(app, frame_b.at(0, -7.5, 0), f"DOME +{F['grow4']:.0f}%", RED)


def p_ring(app, opaque, transparent, p):
    cw.paint(app)
    m = cw.landmarks()
    z = m.deck_centre[2] + 0.03
    sc.footprint_ring(transparent, m.dome_r, (1.0, 1.0, 1.0, 0.45), z, 0.03)
    grown = m.dome_r + F["shift4"] * sc.M * min(1.0, p * 1.6)
    sc.footprint_ring(transparent, grown, (1.0, 0.45, 0.35, 0.6), z + 0.01, 0.04)
    _label(app, m.deck_centre + [0, -grown, 0.4], f"+{F['shift4']:.1f} IN ALL ROUND", RED)


def p_logs(app, opaque, transparent, p):
    frame = _bench(app, transparent, bundle=False)
    _label(app, frame.at(0, 0.8, 0), "BIGGER LOG, BIGGER CHANNEL", AMBER)


def p_print(app, opaque, transparent, p):
    cw.paint(app, subject=False)
    frame = sc.paint_bench(app, "a", bundle=False, bolted=False)
    apart = 0.10 * (1.0 - min(1.0, max(0.0, (p - 0.35) / 0.45)))
    sc.half_keys(transparent, frame, sc.tight(), apart)
    _label(app, frame.at(0, 1.0, 0), "TWO HALF-KEYS", AMBER)
    _label(app, frame.at(0, -7.0, 0), f"{F['profiles']} PROFILES, {F['half_keys']} HALVES", WHITE)


def p_print_cost(app, opaque, transparent, p):
    frame = _bench(app, transparent, bundle=False, bolted=False)
    _label(app, frame.at(0, 0.8, 0), f"{F['kg_seam']:.1f} KG, {F['h_seam']:.0f} H A SEAM", AMBER)


def p_hubs(app, opaque, transparent, p):
    cw.paint(app)
    sc.paint_seams(app)
    for ways, colour in ((5, sc.CYAN), (6, (0.45, 0.92, 0.62, 1.0))):
        v = sc.facing_vertex(ways)
        sc.rosette(opaque, v, 0.11, colour)
        _label(app, v["point"] + v["normal"] * 0.35, f"{ways}-WAY", AMBER)


def p_rules(app, opaque, transparent, p):
    frame = _bench(app, transparent)
    _label(app, frame.at(0, 0.8, 0), "NO FITTINGS INSIDE A SEAM", RED)


def p_cost(app, opaque, transparent, p):
    cw.paint(app)
    sc.paint_seams(app)
    m = cw.landmarks()
    _label(app, m.apex + [0, 0, 0.6], f"SEAM MODULE ${F['module_usd']:,.0f}", AMBER)


def p_reveal(app, opaque, transparent, p):
    cw.paint(app)
    m = cw.landmarks()
    _label(app, m.apex + [0, 0, 0.7], "THE WEDGE DOME", AMBER)


# ----------------------------------------------------------------------
# Cameras
# ----------------------------------------------------------------------

def _moves() -> dict:
    m = cw.landmarks()
    near = sc.Frame(sc.BENCH_A, sc.tight()).near
    near_b = sc.Frame(sc.BENCH_B, sc.tight()).near
    back = -m.log_axis
    close = shots.push_in(near + [-0.07, 0.10, 0.0], near + [0.30, -0.85, 0.26],
                          near + [0.18, -0.58, 0.16], fov_start=38, fov_end=33)
    side = shots.push_in(near + [0.0, 0.40, -0.06], near + [0.62, -0.60, 0.04],
                         near + [0.46, -0.40, 0.02], fov_start=46, fov_end=42)
    dome = m.dome_centre + [0, 0, m.dome_r * 0.45]
    v5 = sc.facing_vertex(5)["point"]
    v6 = sc.facing_vertex(6)["point"]
    hub_target = (v5 + v6) / 2
    return {
        "grain": shots.push_in(m.log_end, m.log_end + back * 2.4 + [0.3, 0, 0.9],
                               m.log_end + back * 1.1 + [0.1, 0, 0.35], 44, 36),
        "member": shots.orbit(m.stack + [0.85, 0.85, 0.3], 2.4, 1.1, -120, 30, 44),
        "counts": shots.orbit(dome, 10.5, 2.8, -115, 40, 46),
        "pinwheel": shots.push_in(m.gap, m.gap + [1.5, -7.5, 1.8], m.gap + [1.0, -5.6, 1.2], 42, 36),
        "doubled": shots.orbit(dome, 9.5, 4.6, -80, -35, 46),
        "vee": close, "key": close, "room": close, "sizes": close, "bundle": close,
        "ducts": close, "logs": close, "rules": close, "print_cost": close,
        "print": shots.push_in(near + [-0.07, 0.10, 0.0], near + [0.25, -0.95, 0.30],
                               near + [0.15, -0.70, 0.20], 40, 36),
        "air": shots.orbit(dome, 9.0, 2.2, -100, 25, 48),
        "dehumid": side,
        "water": shots.orbit(dome, 11.0, 3.5, -60, -25, 46),
        "spacer": shots.push_in((near + near_b) / 2 + [-0.05, 0.1, -0.02],
                                (near + near_b) / 2 + [0.1, -1.8, 0.45],
                                (near + near_b) / 2 + [0.05, -1.35, 0.32], 42, 40),
        "ring": shots.orbit(m.deck_centre, 11.5, 7.0, -95, 30, 46),
        # From inside the dome: the rosettes sit on the inner face of each vertex.
        "hubs": shots.push_in(hub_target, m.dome_centre + [-0.9, 0.9, 0.9],
                              m.dome_centre + [-0.6, 0.4, 1.0], 52, 46),
        "cost": shots.orbit(dome, 10.0, 3.0, -130, 30, 46),
        "reveal": shots.crane_reveal(m.dome_centre + [0, -0.6, 1.4], near + [0.4, -0.9, 0.3],
                                     cw.HERO_EYE, 40, 46, look_start=near),
    }


MOVES = _moves()
camera = shots.by_chapter(MOVES)


# ----------------------------------------------------------------------
# The script
# ----------------------------------------------------------------------

def _ch(n: int, slug: str, title: str, promise: str, narration: str, equations=()) -> Chapter:
    seconds = max(8.0, len(narration.split()) / 2.5 + 1.5)
    return Chapter(slug, f"{n:02d}", title, promise, (narration,), tuple(equations),
                   seconds, (0.0, 0.0, 0.0), slug)


def _chapters() -> tuple[Chapter, ...]:
    f = F
    services = [cf.SERVICE[k] for k in cf.BUNDLE]
    sizes = [f"{s.label}: {s.width_in:.3f} in" + (f" x {s.thick_in:.2f}" if s.thick_in else "")
             for s in services]
    sizes += [f"round ducts: {cf.SERVICE['duct_3'].width_in:.0f} and "
              f"{cf.SERVICE['duct_4'].width_in:.0f} in",
              f"fill allowance: {f['fill_rule']:.0f}% (conduit rule)"]
    kinds = ["nominal" if s.source.startswith("nominal") else "estimate" for s in services]
    rows = [
        (1, "grain", "One log", "A whole house frame, before it is cut.",
         f"This is a house frame before it is cut. One log, ripped with a chainsaw straight "
         f"through its heart into {f['splits']} wedges. Every stick in the dome behind it is "
         f"one of those wedges. By the end of this film you will know what each one does, and "
         f"what the gap between two of them can carry.",
         [f"wedges per log = {f['splits']}"]),
        (2, "member", "Point in, round face out", "Nothing is squared.",
         f"Each wedge is a {f['sector']:.0f} degree slice of the log. In the frame the round "
         f"outer face looks out at the weather and the point faces the centre of the dome. "
         f"Nothing is squared, so the only wood that leaves the log is the width of the saw.",
         [f"sector = 360 / {f['splits']} = {f['sector']:.0f} deg"]),
        (3, "counts", "Two lengths, flat panels", "Built on the ground, one triangle at a time.",
         f"There are {f['members']} members in two lengths: {f['long_n']} cut to "
         f"{f['long']:.1f} inches and {f['short_n']} to {f['short']:.1f}. Three of them make a "
         f"triangle, and each triangle is built flat on the ground as its own panel. "
         f"{f['faces']} panels make the dome.",
         [f"members = {f['members']}", f"long {f['long']:.1f} in x {f['long_n']}",
          f"short {f['short']:.1f} in x {f['short_n']}", f"panels = {f['faces']}"]),
        (4, "pinwheel", "No hubs", "The sticks hold each other.",
         "Inside a panel the three members do not meet at a point. Each one butts into the "
         "side of the next, all turning the same way, like a pinwheel. That is why this dome "
         "has no hubs. The corners hold because the sticks lean on each other, not because a "
         "steel star is holding them.", []),
        (5, "doubled", "Every edge is two sticks", "And between them, a seam.",
         f"Where two panels meet, each one brings its own member, so every inside edge is two "
         f"sticks side by side. That is {f['seams']} seams, and {2 * f['seams']} of the "
         f"{f['members']} members. The last {f['rim']} sit on the rim. Everything interesting "
         f"from here on happens inside those seams.",
         [f"seams = {f['seams']}", f"members in seams = 2 x {f['seams']} = {2 * f['seams']}",
          f"rim members = {f['rim']}"]),
        (6, "vee", "The V", "Two sawn faces cannot close flat.",
         f"Look at the two members end on. Their sawn faces touch at the ridge on the outside "
         f"and open toward the inside, at the sector angle less the fold between the two "
         f"panels. This dome has only two folds: {f['fold_w']:.1f} degrees at {f['n_w']} seams "
         f"and {f['fold_t']:.1f} at {f['n_t']}. So every V is {f['gap_w']:.1f} or "
         f"{f['gap_t']:.1f} degrees, and {f['depth']:.0f} inches deep: the radius of the "
         f"{f['trunk']:.0f} inch log.",
         [f"V = {f['sector']:.0f} - fold", f"{f['sector']:.0f} - {f['fold_w']:.2f} = {f['gap_w']:.2f} deg x {f['n_w']}",
          f"{f['sector']:.0f} - {f['fold_t']:.2f} = {f['gap_t']:.2f} deg x {f['n_t']}",
          f"depth = log radius = {f['depth']:.1f} in"]),
        (7, "key", "The key", "Solid, a spline. Hollow, a pipe.",
         f"The key fills the V, and it is what {f['bolts']} bolts a seam pull the two panels "
         f"against. Make it solid and it is just a spline. Make it hollow and it is a pipe "
         f"running the length of every seam: {f['seam_ft']:.0f} feet of it, touching every "
         f"panel, reaching the crown and the ground.",
         [f"bolts per seam = {f['bolts']}", f"channel = {f['seam_ft']:.0f} ft"]),
        (8, "room", "How much room", "That is the whole budget.",
         f"Inside a key with {f['wall_mm']:.0f} millimetre walls there are {f['area_t']:.1f} "
         f"square inches in the tighter seam and {f['area_w']:.1f} in the wider one. The "
         f"largest round thing that passes through is {f['round_t']:.2f} inches, or "
         f"{f['round_w']:.2f}. Everything that follows has to fit in that.",
         [f"inside, tight seam = {f['area_t']:.2f} sq in", f"inside, wide seam = {f['area_w']:.2f} sq in",
          f"largest round = {f['round_t']:.2f} / {f['round_w']:.2f} in"]),
        (9, "sizes", "The sizes we assumed", "Nominal where there is a standard; estimates where there is not.",
         "Before anything goes in, here are the sizes this film counts on. Pipe and tubing "
         "sizes are nominal, from their standards. Cable sizes are estimates, because every "
         "brand differs. And the rule for how full a channel may be is borrowed from "
         f"conduit: {f['fill_rule']:.0f} percent of the area, so things can still be pulled "
         "through.",
         [f"{line}  ({kind})" for line, kind in zip(sizes, kinds)] + sizes[len(kinds):]),
        (10, "bundle", "Water and wire fit", "Room to spare.",
         f"A half-inch PEX water line, a fifteen-amp circuit, the twelve-volt pair to the "
         f"cooling plates and the condensate drain. All four fit in either seam, and together "
         f"they fill {f['fill_t']:.0f} percent of the tighter one, against the "
         f"{f['fill_rule']:.0f} allowed. There is room left over, and that room matters next.",
         [f"bundle fill, tight seam = {f['fill_t']:.0f}%", f"bundle fill, wide seam = {f['fill_w']:.0f}%",
          f"allowed = {f['fill_rule']:.0f}%"]),
        (11, "ducts", "Round ducts do not", "The number that does not help.",
         f"Now the number that does not help. The smallest ordinary air duct is three inches "
         f"round, and the key's largest opening is {f['round_w']:.2f} inches at best. A "
         f"three-inch duct does not fit. A four-inch one is nowhere close. If the plan was "
         f"round ducts through the seams, the plan does not work as drawn.",
         [f"3 in duct > {f['round_w']:.2f} in opening"]),
        (12, "air", "The channel is the duct", "It does not need a duct in it.",
         f"But the channel does not need a duct in it, because it already is one. With the "
         f"water, wire and drain inside, one seam still moves {f['cfm_t']:.0f} cubic feet a "
         f"minute at a quiet {f['fpm']:.0f} feet a minute. The whole dome needs "
         f"{f['need_cfm']:.0f} for fresh air. {f['seams_for_air']} seams carry the building.",
         [f"dome needs {f['need_cfm']:.1f} cfm", f"one seam = {f['cfm_t']:.1f} cfm at {f['fpm']:.0f} fpm",
          f"seams needed = {f['seams_for_air']}"]),
        (13, "dehumid", "Peltier plates and the three-way gate", "Drying the air where the wood is.",
         "That air runs past a thermoelectric plate, a Peltier: cold on the channel side, "
         "throwing its heat into the room below. Water drops out on the cold plate and runs "
         "to the drain. A three-way gate on each seam sends the air along the wood faces to "
         "dry them, through a silica cartridge when the weather is too wet, or shuts the air "
         "path off from the water path entirely.",
         [f"plates = {f['pel_w']:.0f} W", f"run {f['pel_hours']:.0f} h a day"]),
        (14, "water", "What the plates are worth", "A dehumidifier, not a water supply.",
         f"And honestly: {f['pel_w']:.0f} watts of plates, run {f['pel_hours']:.0f} hours a "
         f"day, make {f['pel_gal']:.0f} gallons a year. That is {f['pel_rain']:.1f} inches of "
         f"rain on this roof. The plates are a dehumidifier that happens to make water. They "
         f"are not a water supply. The roof is the water supply.",
         [f"{f['pel_gal']:.0f} gal / year", f"= {f['pel_rain']:.2f} in of rain"]),
        (15, "spacer", "If you want a duct: the key becomes a spacer", "Every panel moves out.",
         f"If you do want a round duct, the key stops being a filler and becomes a spacer. "
         f"Push every panel out along its own face and every seam opens. A three-inch duct "
         f"needs the panels moved out {f['shift3']:.1f} inches. A four-inch duct with "
         f"everything else beside it needs {f['shift4']:.1f}, and the seams open to "
         f"{f['sp4_t']:.1f} and {f['sp4_w']:.1f} inches at the ridge, each needing a cap.",
         [f"3 in duct: panels out {f['shift3']:.1f} in", f"4 in + bundle: panels out {f['shift4']:.1f} in",
          f"seams open {f['sp4_t']:.1f} / {f['sp4_w']:.1f} in"]),
        (16, "ring", "What the spacer costs", "A bigger dome, all round.",
         f"And a spacer is not free. Moving every panel out makes the whole dome bigger: "
         f"{f['grow3']:.0f} percent for the three-inch duct, {f['grow4']:.0f} percent for the "
         f"four. More wood, more skin, a bigger pad, to carry air the plain channel was "
         f"already carrying.",
         [f"3 in duct: radius +{f['grow3']:.1f}%", f"4 in duct: radius +{f['grow4']:.1f}%"]),
        (17, "logs", "Or start with a bigger log", "The room grows with the square of the radius.",
         "The other lever is the log. The room in the channel grows with the square of the "
         "log's radius: " + ", ".join(f"a {d:.0f} inch log gives {a:.1f} square inches"
                                      for d, a, _r in f["logs"])
         + f". Even the {f['logs'][-1][0]:.0f} inch log opens only {f['logs'][-1][2]:.2f} "
         f"inches round: still not a three-inch duct.",
         [f"{d:.0f} in log: {a:.1f} sq in, {r:.2f} in round" for d, a, r in f["logs"]]),
        (18, "print", "Printing the key in halves", "Each member carries its own half.",
         f"Here is how the key gets made. Split it down the middle and each member carries its "
         f"own half, printed and screwed to its sawn face before the panel is built. When two "
         f"panels meet, the halves close into one channel. The whole dome is "
         f"{f['half_keys']} half-keys in just {f['profiles']} profiles, printed "
         f"{f['seg_each']} pieces to a stick on a {f['bed_mm']:.0f} millimetre printer.",
         [f"half-keys = {f['half_keys']}", f"profiles = {f['profiles']}",
          f"printed pieces = {f['segments']}", f"printer bed = {f['bed_mm']:.0f} mm (assumed)"]),
        (19, "print_cost", "What printing costs", "Print the seams that carry something.",
         f"Printing every seam is {f['kg']:.0f} kilograms of plastic, about "
         f"{f['usd']:,.0f} dollars and {f['hours']:,.0f} printer hours: {f['days']:.0f} days "
         f"of one printer running flat out. So print only the seams that carry something, "
         f"{f['kg_seam']:.1f} kilograms and {f['h_seam']:.0f} hours each, and cut solid keys "
         f"from the offcuts for the rest.",
         [f"all seams: {f['kg']:.0f} kg, ${f['usd']:,.0f}, {f['hours']:,.0f} h",
          f"one seam: {f['kg_seam']:.1f} kg, ${f['usd_seam']:.0f}, {f['h_seam']:.0f} h",
          "PETG 1.27 g/cm3, $20/kg, 15 mm3/s (assumed)"]),
        (20, "hubs", "Where the channels meet", "The frame has no hubs. The services do.",
         f"The frame has no hubs, but the services need them. The channels meet at "
         f"{f['n5']} five-way and {f['n6']} six-way points, and {f['nrim']} more on the rim, "
         f"where they drop to the pad. As built, the V's close to a point there, so each "
         f"junction is a printed rosette box on the inside of the vertex, where a pipe turns "
         f"and a wire is spliced, somewhere you can reach. With the four-inch spacer the "
         f"vertex opens into a hole about {f['node5']:.0f} inches across, and the hub becomes "
         f"a printed node the channels plug into.",
         [f"5-way = {f['n5']}, 6-way = {f['n6']}, rim = {f['nrim']}",
          f"node with spacer: {f['node5']:.1f} / {f['node6']:.1f} in across"]),
        (21, "rules", "Two rules", "A hidden leak is the failure this exists to prevent.",
         "Two rules. Keep pressure joints out of the seams: run the PEX continuous, and make "
         "every fitting in a rosette you can open. A hidden leak inside a wooden seam is the "
         "one failure this whole system exists to prevent. And whether a cable may run in "
         "this chase is your inspector's call, not this film's.", []),
        (22, "cost", "What the fitted seam costs", "Before a single printed key.",
         f"Fitted out as gutter, vent and dehumidifier, the seam module across the whole dome "
         f"is {f['module_usd']:,.0f} dollars, before a single printed key. If you fit one "
         f"part of it, fit the gutter.",
         [f"seam module = ${f['module_usd']:,.0f}", f"printed keys, per seam = ${f['usd_seam']:.0f}"]),
        (23, "reveal", "The wedge dome", "One log at a time.",
         f"One log, {f['splits']} rip cuts, {f['members']} sticks, {f['seams']} seams, and a "
         f"channel in every one of them. Water and wire for free, air if you let the channel "
         f"be the duct, and a round duct only if you pay for it in size. That is the wedge "
         f"dome.", []),
    ]
    return tuple(_ch(*row) for row in rows)


CHAPTERS = _chapters()

SCENES = {
    "grain": p_grain, "member": p_member, "counts": p_counts, "pinwheel": p_pinwheel,
    "doubled": p_doubled, "vee": p_vee, "key": p_key, "room": p_room, "sizes": p_sizes,
    "bundle": p_bundle, "ducts": p_ducts, "air": p_air, "dehumid": p_dehumid,
    "water": p_water, "spacer": p_spacer, "ring": p_ring, "logs": p_logs,
    "print": p_print, "print_cost": p_print_cost, "hubs": p_hubs, "rules": p_rules,
    "cost": p_cost, "reveal": p_reveal,
}


def validate_wedge_explained() -> None:
    sc.validate_channel_scene()
    cw.validate_cabin_world()
    for ch in CHAPTERS:
        assert ch.stage in SCENES, ch.stage
        eye, target, fov = MOVES[ch.slug](0.5)
        assert np.all(np.isfinite(eye)) and 20 < fov < 70, ch.slug
        assert np.linalg.norm(np.asarray(eye) - np.asarray(target)) > 0.2, ch.slug
    # The film's claims, checked against the facts they come from.
    assert F["fill_t"] < F["fill_rule"], "the bundle must fit"
    assert F["round_w"] < cf.SERVICE["duct_3"].width_in, "the no-duct chapter must be true"
    assert F["cfm_t"] * F["seams_for_air"] >= F["need_cfm"]
    assert F["logs"][-1][2] < cf.SERVICE["duct_3"].width_in


CABIN_WEDGE_EXPLAINED_LESSON = Lesson(
    key="cabin_wedge_explained", brand="DOMESIM", title="The Wedge Dome, Explained",
    chapters=CHAPTERS, scenes=SCENES, selftest=validate_wedge_explained,
    snapshot_prefix="cabin_wedge_explained", camera_fn=camera, ground="off",
    backdrop=cw.backdrop, light=cw.LIGHT, label_layout="declutter",
    audio_bed="beds/cabin-explained", audio_bed_gain=0.12,
)
