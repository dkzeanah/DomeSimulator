"""The Shop the Campaign Buys: a Kickstarter pitch for the tooling lines.

A 10 x 5 ft CNC plasma table built from the Homemade Madness DIY plans (credited
in the film), scaled by their own two rules; the forty panels it cuts from one
sheet; the steel vessel they weld into; a 3V dome in plate at the size that
nests well; and the router head that shares the frame. Every figure is read
from ``book_tokens.nest_facts`` / ``shop_facts`` -- the same functions the
2 Trees book prints from -- which read :mod:`plate_nesting` and
:mod:`cnc_table`.

    py -3.12 -m rerender stills cabin_shop
    py -3.12 -m rerender render cabin_shop
"""

from __future__ import annotations

from functools import partial

import numpy as np

from . import cabin_stage, cabin_world as cw, cnc_table as ct, shop_scene as ss, shots
from .book_tokens import nest_facts, shop_facts
from .lessons import Chapter, Lesson
from .render_kit import TriangleBatch, WorldLabel

WHITE, AMBER, GREEN, CYAN, RED = (240, 236, 226), (255, 205, 130), (111, 235, 155), (120, 225, 240), (255, 140, 120)


def _figures() -> dict:
    n, s = nest_facts(), shop_facts()
    sp = ct.pinion_steps_per_mm()
    usd = lambda v: f"${v:,.0f}"
    return {
        "sheet": f"{n['sheet_w_in']:.0f} by {n['sheet_h_in']:.0f}",
        "panels": n["panels"], "rows": n["rows"], "util": f"{n['util_pct']:.0f}",
        "dia_ft": f"{n['diameter_ft']:.1f}", "height_ft": f"{n['height_ft']:.1f}", "gal": f"{n['volume_gal']:.0f}",
        "part_lb": f"{n['part_lb_3mm']:.0f}", "lb2": f"{n['part_lb_2mm']:.0f}",
        "seams": n["seams"], "weld_ft": f"{n['weld_ft']:.0f}", "weld_h": f"{n['weld_hours']:.1f}",
        "cut_ft": f"{n['cut_ft']:.0f}", "cut_min": f"{n['cut_minutes']:.0f}",
        "trim_in": f"{n['trim_in']:.2f}", "trim_gain": f"{n['trim_gain_pct']:.1f}", "caps": n["trim_caps"],
        "sweet_ft": f"{n['sweet_ft']:.0f}", "sweet_sheets": n["sweet_sheets"], "sweet_used": f"{n['sweet_used_pct']:.0f}",
        "sweet_lb": f"{n['sweet_lb_2mm']:,.0f}", "next_ft": f"{n['next_ft']:.0f}", "next_sheets": n["next_sheets"],
        "frame": f"{s['frame_mm'][0]:,.0f} by {s['frame_mm'][1]:,.0f}", "gantry_mm": f"{s['gantry_mm']:,.0f}",
        "rails": s["rails"], "kits": s["kits"], "racks": s["racks"], "x_side": s["x_racks_side"],
        "pinions": s["pinions"], "steps": f"{sp['steps_per_mm']:.2f}", "mm_rev": f"{sp['mm_per_rev']:.2f}",
        "pitch": f"{sp['pitch_dia_mm']:.1f}", "accel": f"{s['accel']:.1f}", "kg": f"{s['gantry_kg']:.0f}",
        "build": usd(s["build_usd"]), "router": usd(s["router_usd"]), "both": usd(s["both_usd"]),
        "paid": usd(s["paid_usd"]), "quoted": usd(s["quoted_usd"]), "allow": usd(s["allowance_usd"]),
        "goal_plasma": usd(s["goal_plasma_usd"]), "goal_router": usd(s["goal_router_usd"]),
        "goal_both": usd(s["goal_plasma_usd"] + s["goal_router_usd"]), "saving": usd(s["saving_router_usd"]),
        "sag": f"{ct.gantry_deflection_mm():.2f}", "slats": ct.counts()["slats"],
    }


F = _figures()


def label(app, position, text, colour=WHITE):
    app.world_labels.append(WorldLabel(np.asarray(position, dtype=np.float32), text, colour))


def _table_points():
    L, W = ss.frame_size()
    return [ss.at_table(sx * L / 2, sy * W / 2, z) for sx in (-1, 1) for sy in (-1, 1) for z in (0.0, ss.FRAME_TOP + 0.7)]


def table(app, bed="slats"):
    app.static_layer(f"shop:table-{bed}", partial(ss.table_static, bed), _table_points())


TOP = ss.at_table(0, 0, ss.FRAME_TOP + 0.62)


# ----------------------------------------------------------------------
# Painters
# ----------------------------------------------------------------------

def p_open(app, opaque, transparent, p):
    cw.paint(app)
    table(app)
    opaque.vertices.extend(ss.sheet_batch(40).vertices)
    ss.gantry(opaque, ss.gantry_x(0.35), 0.2)
    app.static_layer("shop:vessel", partial(ss.vessel_batch, ss.VESSEL))
    label(app, TOP + [0, 0, 0.3], "A 10 x 5 FT PLASMA TABLE", AMBER)
    label(app, np.array([*ss.VESSEL, 1.2]), f"{F['panels']} PANELS, ONE SHEET", CYAN)


def p_cutting(app, opaque, transparent, p):
    cw.paint(app, subject=False)
    table(app)
    k, tip = ss.torch_point(min(0.999, p))
    opaque.vertices.extend(ss.sheet_batch(k).vertices)
    x = tip[0] - ss.TABLE[0] + 0.09
    y = tip[1] - ss.TABLE[1]
    ss.gantry(opaque, x, y)
    transparent.sphere(tip + [0, 0, 0.005], 0.03, (0.6, 0.85, 1.0, 0.8), 5, 10)
    label(app, TOP + [0, 0, 0.2], f"PART {k + 1} OF {F['panels']}", AMBER)


def p_nest(app, opaque, transparent, p):
    cw.paint(app, subject=False)
    table(app)
    opaque.vertices.extend(ss.sheet_batch(40).vertices)
    label(app, TOP, f"{F['rows']} STRIPS, ALTERNATELY UP AND DOWN", AMBER)
    label(app, TOP - [0, 0, 0.25], f"{F['util']}% OF THE SHEET IN PARTS", GREEN)


def p_trim(app, opaque, transparent, p):
    cw.paint(app, subject=False)
    table(app)
    opaque.vertices.extend(ss.sheet_batch(40).vertices)
    label(app, TOP, f"TRIM EACH POINT {F['trim_in']} IN: {F['trim_gain']}% BIGGER", AMBER)
    label(app, TOP - [0, 0, 0.25], f"{F['caps']} CAPS OVER THE VERTICES", WHITE)


def p_vessel(app, opaque, transparent, p):
    cw.paint(app)
    app.static_layer("shop:vessel", partial(ss.vessel_batch, ss.VESSEL))
    top = np.array([*ss.VESSEL, 0.95])
    label(app, top + [0, 0, 0.25], f"{F['dia_ft']} FT ACROSS, {F['height_ft']} FT TALL", AMBER)
    label(app, top, f"{F['seams']} SEAMS, {F['weld_ft']} FT OF WELD", CYAN)


def p_uses(app, opaque, transparent, p):
    cw.paint(app)
    app.static_layer("shop:bowl", partial(ss.vessel_batch, ss.VESSEL, True))
    top = np.array([*ss.VESSEL, 1.0])
    label(app, top + [0, 0, 0.25], f"AS A BOWL: {F['gal']} GALLONS", AMBER)
    label(app, top, "A TUB, A STOVE BODY, A FIRE BOWL, A SEAT", WHITE)


def p_scale(app, opaque, transparent, p):
    cw.paint(app)
    app.static_layer("shop:vessel", partial(ss.vessel_batch, ss.VESSEL))
    ss.person(opaque, np.array([ss.VESSEL[0] + 1.25, ss.VESSEL[1] + 0.35, 0.0]))
    label(app, np.array([*ss.VESSEL, 1.3]), "NOT A SHELTER AT ONE SHEET", RED)


def p_steel(app, opaque, transparent, p):
    cw.paint(app)
    app.static_layer("shop:steel3v", ss.steel_dome_batch)
    ss.person(opaque, np.array([ss.STEEL_DOME[0] + 2.55, ss.STEEL_DOME[1] + 0.6, 0.0]))
    top = ss.steel_dome_top()
    label(app, top + [0, 0, 0.6], f"{F['sweet_ft']} FT 3V IN PLATE: {F['sweet_sheets']} SHEETS", AMBER)
    label(app, top + [0, 0, 0.3], f"{F['next_ft']} FT TAKES {F['next_sheets']}", WHITE)


def p_frame(app, opaque, transparent, p):
    cw.paint(app, subject=False)
    table(app)
    label(app, TOP, f"FRAME {F['frame']} MM: SHEET + 250", AMBER)
    label(app, TOP - [0, 0, 0.25], "A MID LEG PAIR FOR THE LONGER SPAN", WHITE)


def p_rails(app, opaque, transparent, p):
    cw.paint(app, subject=False)
    table(app)
    ss.gantry(opaque, ss.gantry_x(0.92), 0.0)
    label(app, TOP, f"{F['rails']} RAILS, JOINED; {F['racks']} RACK LENGTHS", AMBER)
    label(app, TOP - [0, 0, 0.25], "JOINS MARKED: ALIGN ON A STRAIGHT EDGE", RED)


def p_pinion(app, opaque, transparent, p):
    cw.paint(app, subject=False)
    table(app)
    ss.gantry(opaque, ss.gantry_x(0.5), 0.0)
    label(app, TOP, f"{F['steps']} STEPS PER MM", AMBER)
    label(app, TOP - [0, 0, 0.25], f"15 TEETH x MOD 1.5 = {F['pitch']} MM PITCH", WHITE)


def p_motors(app, opaque, transparent, p):
    cw.paint(app, subject=False)
    table(app)
    ss.gantry(opaque, ss.gantry_x(0.5), 0.0)
    label(app, TOP, "NEMA 23, 3 NM, 10 MM SHAFT = THE PINION'S BORE", AMBER)
    label(app, TOP - [0, 0, 0.25], f"GANTRY {F['accel']} M/S2 ON HALF TORQUE", GREEN)


def p_torch(app, opaque, transparent, p):
    cw.paint(app, subject=False)
    table(app)
    opaque.vertices.extend(ss.sheet_batch(0).vertices)
    tip = ss.gantry(opaque, ss.gantry_x(0.5), 0.15, z_down=0.06 * (1 - p))
    label(app, tip + [0, 0, 0.6], "PILOT ARC, FLOATING HEAD", AMBER)
    label(app, tip + [0, 0, 0.35], "NO HIGH-FREQUENCY START NEAR THE WIRING", RED)


def p_bill(app, opaque, transparent, p):
    cw.paint(app, subject=False)
    table(app)
    ss.gantry(opaque, ss.gantry_x(0.5), 0.0)
    label(app, TOP + [0, 0, 0.25], f"BUILT: {F['build']}", AMBER)
    label(app, TOP, f"PAID {F['paid']} / QUOTED {F['quoted']} / ESTIMATED {F['allow']}", WHITE)


def p_router(app, opaque, transparent, p):
    cw.paint(app, subject=False)
    table(app, "mdf")
    tip = ss.router_work(opaque, p)
    ss.gantry(opaque, tip[0] - ss.TABLE[0] + 0.09, tip[1] - ss.TABLE[1], head="spindle")
    label(app, TOP, f"ROUTER HEAD: {F['router']} MORE", AMBER)
    label(app, TOP - [0, 0, 0.25], "CUTTING A PANEL JIG", GREEN)


def p_budget(app, opaque, transparent, p):
    cw.paint(app)
    table(app)
    ss.gantry(opaque, ss.gantry_x(0.6), 0.0)
    app.static_layer("shop:vessel", partial(ss.vessel_batch, ss.VESSEL))
    label(app, TOP + [0, 0, 0.3], f"BUDGETED TO BUY: {F['goal_both']}", WHITE)
    label(app, TOP, f"BUILT, BOTH MACHINES: {F['both']}", AMBER)


def p_close(app, opaque, transparent, p):
    cw.paint(app)
    table(app)
    opaque.vertices.extend(ss.sheet_batch(40).vertices)
    ss.gantry(opaque, ss.gantry_x(0.8), -0.3)
    app.static_layer("shop:vessel", partial(ss.vessel_batch, ss.VESSEL))
    label(app, TOP + [0, 0, 0.2], "WHAT THE BACKING BUILDS", AMBER)


# ----------------------------------------------------------------------
# Chapters
# ----------------------------------------------------------------------

def ch(number, slug, title, promise, narration, equations):
    return Chapter(slug, f"{number:02}", title, promise, (narration,), tuple(equations),
                   max(8, len(narration.split()) / 2.5 + 1.5), (0, 0, 0), slug)


CHAPTERS = (
    ch(1, "open", "The shop the campaign buys", "Two machine lines, one frame.",
       "Part of what backing this project pays for is a shop. Not a building: two machines. A plasma table that cuts a "
       f"whole sheet of steel into the panels of a dome, and a router that cuts the jigs and the wooden panels. This "
       f"film is what those two machines are, what they make, and what they cost when you build them rather than buy "
       f"them. Here is the first thing the table makes: one {F['sheet']} inch sheet of plate, {F['panels']} panels.",
       (f"one sheet: {F['sheet']} in", f"{F['panels']} panels")),
    ch(2, "cutting", "One sheet, forty panels", "The torch follows the nest.",
       f"Steel plate comes in sheets ten feet by five, and the table's bed is exactly that size. The torch walks every "
       f"panel's outline in turn: about {F['cut_ft']} feet of cut, roughly {F['cut_min']} minutes of torch time. What "
       "comes off the table is the whole shell of a dome, every triangle already the right size, already the right angle "
       "at every corner. Nothing is measured with a tape. The machine does the measuring.",
       (f"cut path = {F['cut_ft']} ft", f"about {F['cut_min']} min")),
    ch(3, "nest", "How the panels fit", "Strips of triangles, up and down.",
       f"The panels are laid out in {F['rows']} strips, each one triangles pointing alternately up and down, the way they "
       "tile with nothing between them but the cutting gap. Every panel is slid along until it sits exactly a quarter "
       f"inch from its neighbour, and then the whole layout is checked part by part. {F['util']} percent of the sheet "
       "ends up inside a part. The panels come from the solved dome, so if the geometry changes, the nest changes too.",
       (f"{F['rows']} strips", f"{F['util']}% of the sheet in parts")),
    ch(4, "trim", "Almost fits", "A little off each point.",
       "You can squeeze a slightly bigger shell out of the same sheet by trimming each panel's point and welding a small "
       f"cap over every vertex. Here the best trim is {F['trim_in']} inches off each point, with {F['caps']} caps, and it "
       f"makes the shell {F['trim_gain']} percent bigger. That is real, and it is small: the strips are already full. "
       "Most of the time, cut the panels whole.",
       (f"trim = {F['trim_in']} in", f"gain = {F['trim_gain']}%", f"caps = {F['caps']}")),
    ch(5, "vessel", "Welded up", "Forty panels, one shell.",
       f"Welded together, the forty panels make a steel shell {F['dia_ft']} feet across and {F['height_ft']} feet tall. "
       f"That is {F['seams']} seams and {F['weld_ft']} feet of weld, about {F['weld_h']} hours at a steady hand. In "
       f"three-millimetre plate the panels weigh {F['part_lb']} pounds; in two-millimetre, {F['lb2']}. Every seam is a "
       "butt weld, ground flush where it shows.",
       (f"{F['seams']} seams = {F['weld_ft']} ft of weld", f"{F['part_lb']} lb in 3 mm")),
    ch(6, "uses", "What one sheet becomes", "A tub, a stove, a fire bowl, a seat.",
       f"Turned over on three short legs, the shell is a bowl holding {F['gal']} gallons: a tub. In heavier plate, with a "
       "hinged panel for a door and a flue at the top, it is the body of a wood stove. Smaller jobs are a fire bowl, a "
       "planter, a seat. A hemisphere does not care which way up it is used, and these are the right first projects while "
       "you learn the machine.",
       (f"as a bowl: {F['gal']} gal",)),
    ch(7, "scale", "What it is not", "One sheet does not make a shelter.",
       f"Here is the number that does not help the pitch. At {F['height_ft']} feet tall, a one-sheet shell holds nobody "
       "standing up. It is not a storm shelter, and it is not a room. To shelter a person you need a bigger dome, cut "
       "from several sheets, and that is the next step.",
       (f"height = {F['height_ft']} ft",)),
    ch(8, "steel", "A dome in plate", "Size the dome to the sheet.",
       "The same table cuts the triangles of a building. A three-frequency dome has two panel shapes, and how many sheets "
       f"it takes depends on whether two strips of its biggest panels fit on a five-foot sheet. At {F['sweet_ft']} feet "
       f"across they do: {F['sweet_sheets']} sheets, {F['sweet_used']} percent of the steel in parts, about "
       f"{F['sweet_lb']} pounds in two-millimetre plate. One foot bigger, at {F['next_ft']} feet, they do not, and it "
       f"takes {F['next_sheets']} sheets. Size the dome to the sheet, or cut the big panels in two and weld them.",
       (f"{F['sweet_ft']} ft: {F['sweet_sheets']} sheets", f"{F['next_ft']} ft: {F['next_sheets']} sheets")),
    ch(9, "frame", "The table, by the plans' own rules", "Credit: Homemade Madness.",
       "The table is the Homemade Madness DIY CNC plasma design, and the credit for it is theirs. Their plans are drawn "
       "for a two-by-one-metre sheet and give two rules for building it bigger: the frame is two hundred and fifty "
       f"millimetres longer and wider than the sheet, and the gantry tube is two hundred and fifty-three longer than the "
       f"cut width. For a ten-by-five-foot sheet that makes a frame {F['frame']} millimetres. Ours is half again as long "
       "as theirs, so we add one change: a leg pair at the middle, so no rail span goes unsupported.",
       (f"frame = sheet + 250 mm = {F['frame']} mm", f"gantry tube = {F['gantry_mm']} mm")),
    ch(10, "rails", "Long rails, joined", "Alignment is everything.",
       f"No single rail is three metres long at this price, so each side takes three, joined end to end: {F['rails']} "
       f"rails in all, which is {F['kits']} of the two-rail kits already bought. Both long sides are driven, so both need "
       f"rack: {F['x_side']} half-metre lengths a side, four on the gantry and a spare, {F['racks']} in all. Every joint "
       "is cut on the tooth and aligned with a spare piece held across it. A joint set by eye makes a machine that cuts "
       "a curve.",
       (f"rails = {F['rails']} ({F['kits']} kits)", f"rack = 2 x {F['x_side']} + 4 + 1 = {F['racks']}")),
    ch(11, "pinion", "The number that has to be right", "Steps per millimetre.",
       f"A fifteen-tooth pinion at module one and a half has a {F['pitch']} millimetre pitch diameter, so one turn of the "
       f"motor moves the axis {F['mm_rev']} millimetres. With eight microsteps on a two-hundred-step motor, that is "
       f"{F['steps']} steps per millimetre. That number goes into the controller before anything is cut. The plans "
       "prefer a thirteen-tooth pinion for torque, and say to use what you can find and set the ratio in software.",
       (f"pitch dia = 15 x 1.5 = {F['pitch']} mm", f"per turn = pi x {F['pitch']} = {F['mm_rev']} mm",
        f"1600 / {F['mm_rev']} = {F['steps']} steps/mm")),
    ch(12, "motors", "Motors that fit the pinion", "The bore decides the shaft.",
       "The pinions have a ten-millimetre bore, so the motors must have a ten-millimetre shaft. A NEMA 23 of three "
       f"newton-metres has one, and fits with no sleeve; a bigger NEMA 34's shaft would not. Two of them on the long axis "
       f"push a gantry of about {F['kg']} kilograms at {F['accel']} metres per second squared on half their torque, far "
       "more than a plasma ever asks for, because a plasma torch pushes on nothing.",
       ("shaft 10 mm = pinion bore 10 mm", f"two motors: {F['accel']} m/s^2 at half torque")),
    ch(13, "torch", "Pilot arc and a floating head", "Keep the noise out of the wiring.",
       "The torch rides a floating head that touches the plate to find its height before every cut. Pick a plasma with "
       "a pilot-arc start: a high-frequency start puts electrical noise into the control wiring. A torch height "
       "controller is left out on purpose. The plans' breakout board cannot run one, and touching off the plate again "
       "partway through a long cut does the job for nothing.",
       ("pilot arc, CNC port", "floating head touch-off")),
    ch(14, "bill", "What it costs, and what kind of number each is", "Paid, quoted, estimated.",
       f"Built, the plasma table comes to {F['build']}, and the bill keeps three kinds of price apart. {F['paid']} is "
       f"what we actually paid for rack, pinions and rails. {F['quoted']} is current retail listings for the motors, "
       f"drivers, power supply, Mach3, the plasma cutter and the frame steel. {F['allow']} is still estimates, labelled "
       "as estimates until they are quoted: the slats, the water pan, the plate, the ballscrew and the wiring.",
       (f"paid {F['paid']}", f"quoted {F['quoted']}", f"estimated {F['allow']}", f"= {F['build']}")),
    ch(15, "router", "The router head", "Same frame, different tool.",
       f"For {F['router']} more, the same frame becomes a router. The rails, rack, motors and controls stay. The floating "
       "head becomes a rigid ballscrew axis with a water-cooled spindle, the slats lift out, and a flat spoilboard goes "
       f"in. The gantry tube sags {F['sag']} millimetres under a router's side load, less than the cutter's own wobble. "
       "This is the machine that cuts the jigs, the templates and the wooden panels the rest of the method needs.",
       (f"router head = {F['router']}", f"gantry sag = {F['sag']} mm")),
    ch(16, "budget", "Budgeted, and built", "The honest version of the line item.",
       f"The campaign budgets {F['goal_plasma']} to buy a plasma table and {F['goal_router']} for a router: "
       f"{F['goal_both']} together. Built on one frame, both machines come to {F['both']}. That difference is real, and "
       "so is what it does not include: a bought machine comes with support, a warranty and a phone number. A built "
       "one takes weeks of evenings, and its first troubleshooter is its owner. We print both numbers because the "
       "choice is real.",
       (f"bought: {F['goal_both']}", f"built: {F['both']}")),
    ch(17, "close", "What the backing builds", "A shop that makes shops.",
       "That is what this part of the backing buys: a table that turns a sheet of steel into a dome's panels, a router "
       "that turns a sheet of plywood into the jigs that build the wooden ones, and the first things they make. Every "
       "number in this film comes from the same code as the book. The table's design is Homemade Madness's; the steel "
       "and the sawdust will be ours.",
       ("plasma + router, one frame", "figures: cnc_table.py, plate_nesting.py")),
)

SCENES = {
    "open": p_open, "cutting": p_cutting, "nest": p_nest, "trim": p_trim, "vessel": p_vessel,
    "uses": p_uses, "scale": p_scale, "steel": p_steel, "frame": p_frame, "rails": p_rails,
    "pinion": p_pinion, "motors": p_motors, "torch": p_torch, "bill": p_bill, "router": p_router,
    "budget": p_budget, "close": p_close,
}


# ----------------------------------------------------------------------
# Cameras
# ----------------------------------------------------------------------

def _moves():
    L, W = ss.frame_size()
    t = ss.at_table(0, 0, ss.FRAME_TOP + 0.15)
    v = np.array([*ss.VESSEL, 0.5])
    wide = shots.orbit((t + v) / 2 + [0, 0, 0.3], 6.0, 3.0, -55, 20, 50)
    over = shots.push_in(t, t + [0.6, -3.0, 2.8], t + [0.4, -2.4, 2.3], 46, 42)
    top = shots.push_in(t, t + [0.2, -1.3, 3.3], t + [0.1, -1.0, 3.0], 50, 48)
    vessel = shots.orbit(v, 2.6, 0.9, -70, 30, 44)
    scale = shots.push_in(v + [0.6, 0.15, 0.4], v + [0.9, -5.2, 1.2], v + [0.75, -4.5, 1.1], 44, 42)
    sd = np.array([ss.STEEL_DOME[0], ss.STEEL_DOME[1], 1.2])
    steel = shots.orbit(sd, 6.2, 1.0, -60, 25, 46)
    side = shots.orbit(t, 3.6, 1.0, -75, 25, 46)
    rack = shots.push_in(ss.at_table(-0.5, -W / 2, ss.FRAME_TOP),
                         ss.at_table(-1.6, -W / 2 - 1.5, ss.FRAME_TOP + 0.55),
                         ss.at_table(-1.3, -W / 2 - 1.0, ss.FRAME_TOP + 0.4), 42, 36)
    gx = ss.gantry_x(0.5)
    motor = shots.push_in(ss.at_table(gx, -W / 2, ss.FRAME_TOP + 0.1),
                          ss.at_table(gx + 1.2, -W / 2 - 1.2, ss.FRAME_TOP + 0.6),
                          ss.at_table(gx + 0.8, -W / 2 - 0.8, ss.FRAME_TOP + 0.45), 42, 36)
    torch = shots.push_in(ss.at_table(gx - 0.09, 0.15, ss.FRAME_TOP + 0.2),
                          ss.at_table(gx - 1.3, -0.9, ss.FRAME_TOP + 0.7),
                          ss.at_table(gx - 0.9, -0.6, ss.FRAME_TOP + 0.5), 42, 36)
    close = shots.crane_reveal((t + v) / 2, t + [2.0, -4.5, 1.3], t + [3.5, -9.0, 5.5], 44, 50)
    table = {"open": wide, "cutting": over, "nest": top, "trim": top, "vessel": vessel, "uses": vessel,
             "scale": scale, "steel": steel, "frame": side, "rails": rack, "pinion": motor, "motors": motor,
             "torch": torch, "bill": side, "router": over, "budget": wide, "close": close}
    return {k: cabin_stage.clear_view(m, cabin_stage.safe) for k, m in table.items()}


MOVES = _moves()
camera = shots.by_chapter(MOVES)


def report() -> str:
    return ct.bill_table()


def validate_cabin_shop() -> None:
    ss.validate_shop_scene()
    assert set(SCENES) == set(MOVES) == {c.slug for c in CHAPTERS}
    assert "Homemade Madness" in CHAPTERS[8].narration[0] and "Homemade Madness" in CHAPTERS[-1].narration[0]
    assert "not" in CHAPTERS[6].narration[0], "the film states what one sheet cannot make"
    for chapter in CHAPTERS:
        for p in (0, 0.25, 0.5, 0.75, 1):
            eye, target, fov = MOVES[chapter.slug](p)
            assert np.all(np.isfinite(eye)) and 20 < fov < 70 and eye[2] > 0, chapter.slug
            assert np.linalg.norm(np.asarray(eye) - np.asarray(target)) > 0.3, chapter.slug

    class App:
        def __init__(self):
            self.world_labels = []

        def static_layer(self, key, builder, subject_points=None):
            batch = builder()
            assert np.all(np.isfinite(batch.vertices)), key

    for slug, painter in SCENES.items():
        app, opaque, transparent = App(), TriangleBatch(), TriangleBatch()
        painter(app, opaque, transparent, 0.6)
        assert np.all(np.isfinite(opaque.vertices)) and np.all(np.isfinite(transparent.vertices)), slug
        assert app.world_labels, slug
    CABIN_SHOP_LESSON.validate()


CABIN_SHOP_LESSON = Lesson(
    key="cabin_shop", brand="DOMESIM", title="The Shop the Campaign Buys: A 10 x 5 Plasma Table and Its Router",
    chapters=CHAPTERS, scenes=SCENES, selftest=validate_cabin_shop, report=report,
    snapshot_prefix="cabin_shop", camera_fn=camera, ground="off",
    backdrop=cw.backdrop, light=cw.LIGHT, label_layout="declutter",
    audio_bed="beds/cabin-explained", audio_bed_gain=0.12,
)
