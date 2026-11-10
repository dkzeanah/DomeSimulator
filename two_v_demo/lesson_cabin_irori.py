"""The Irori: a Japanese sunken hearth under the wedge dome's apex, in the Cabin World.

What an irori is, the seven jobs it did, and what happens when you put one in the middle
of the solver's 2V dome: the pothook hangs from the apex hub, the drying rack from the
upper ring, the seats fit with room to spare -- and an open charcoal fire in a tight
dome is a carbon-monoxide problem, so the film ends with the hood and flue that keep
the circle and lose the smoke. Every figure is :func:`two_v_demo.irori.facts`.
"""
from __future__ import annotations

import math

import numpy as np

from . import cabin_world as cw, cabin_stage, shots
from . import irori as ir
from .lesson_cabin_linseed_oil import solid_cylinder
from .lessons import Chapter, Lesson
from .render_kit import TriangleBatch, WorldLabel

F, C = ir.facts(), ir.C
WHITE, AMBER, GREEN, RED = (240, 236, 226), (255, 205, 130), (111, 235, 155), (255, 140, 120)

FRAME_WOOD = (0.36, 0.22, 0.12, 1.0)      # the robuchi, dark with years of smoke
STONE = (0.52, 0.50, 0.47, 1.0)
ASH = (0.66, 0.64, 0.60, 1.0)
COAL = (0.16, 0.13, 0.12, 1.0)
EMBER = (1.00, 0.42, 0.10, 1.0)
FLAME = (1.00, 0.62, 0.18, 0.55)
SMOKE = (0.55, 0.55, 0.58, 0.22)
IRON = (0.18, 0.18, 0.20, 1.0)
BAMBOO = (0.62, 0.55, 0.30, 1.0)
FISH = (0.30, 0.20, 0.13, 1.0)
STEEL = (0.38, 0.40, 0.43, 1.0)
LATTICE = (0.55, 0.40, 0.24, 1.0)
CORD = (0.80, 0.74, 0.60, 1.0)
CUSHIONS = ((0.55, 0.20, 0.18, 1.0), (0.24, 0.36, 0.52, 1.0),
            (0.36, 0.46, 0.30, 1.0), (0.70, 0.58, 0.36, 1.0))

M = cw.landmarks()
H = M.deck_centre.copy()                   # the hearth sits on the floor's centre, under the apex
ENTRY = np.array([0.0, -1.0, 0.0])
"""The entry (the doma) side: toward the hero camera, where the world's builder faces.
A declared staging choice -- the Cabin World's dome has no door cut yet."""


def label(app, position, text, colour=WHITE):
    app.world_labels.append(WorldLabel(np.asarray(position, dtype=np.float32), text, colour))


def world(app, subject: bool = False):
    """The Cabin World without the builder, who stands where the seats go."""
    cw.paint(app, hide=("builder",), subject=subject)


def hub(z_in_m: float) -> np.ndarray:
    """The solver's hubs at one ring height (metres above the floor), in scene coordinates."""
    v, _ = ir.dome()
    ring = v[np.abs(v[:, 2] - z_in_m) < 0.02]
    return ring + M.dome_centre


def upper_ring() -> np.ndarray:
    v, _ = ir.dome()
    heights = sorted(set(np.round(v[:, 2], 3)))
    return hub(heights[-2])                 # the ring just below the apex


# ----------------------------------------------------------------------
# The hearth and what hangs over it
# ----------------------------------------------------------------------

def hearth(opaque, transparent, p, lit=True):
    """The pit as seen from the room: border, stone edge, ash bed, coals."""
    s, w = C["hearth_side_m"], C["frame_w_m"]
    top = H + [0, 0, 0.025]
    for sx, sy in ((1, 0), (-1, 0), (0, 1), (0, -1)):
        # Left and right rails run the full outer width; front and back sit between them.
        size = (w, s + 2 * w, 0.05) if sx else (s, w, 0.05)
        opaque.box(top + [sx * (s + w) / 2, sy * (s + w) / 2, 0], size, FRAME_WOOD)
    # A stone course just inside the border, then the ash bed, set a little down.
    for sx, sy in ((1, 0), (-1, 0), (0, 1), (0, -1)):
        size = (s, 0.06, 0.02) if sx == 0 else (0.06, s, 0.02)
        opaque.box(H + [sx * (s - 0.06) / 2, sy * (s - 0.06) / 2, 0.012], size, STONE)
    opaque.box(H + [0, 0, 0.004], (s - 0.12, s - 0.12, 0.008), ASH)
    if not lit:
        return
    rng = np.random.default_rng(7)
    for k in range(14):
        x, y = rng.uniform(-0.16, 0.16, 2)
        glow = 0.5 + 0.5 * math.sin(p * 9 + k)
        colour = tuple(np.array(COAL) * (1 - glow) + np.array(EMBER) * glow)
        opaque.box(H + [x, y, 0.022], (0.06, 0.05, 0.035), colour)
    for k in range(5):
        a = math.tau * k / 5 + p * 2
        base = H + [0.07 * math.cos(a), 0.07 * math.sin(a), 0.035]
        transparent.cone(base, base + [0, 0, 0.10 + 0.04 * math.sin(p * 13 + k)], 0.035, FLAME, 8)


def kettle(opaque, at):
    """A cast-iron kettle (tetsubin) hanging by its bail from ``at``."""
    body = at - [0, 0, 0.17]
    opaque.sphere(body, 0.12, IRON, 6, 10)
    solid_cylinder(opaque, body + [0.08, 0, 0.02], body + [0.17, 0, 0.07], 0.018, IRON, 8)
    for a, b in ((at, body + [-0.09, 0, 0.06]), (at, body + [0.09, 0, 0.06])):
        solid_cylinder(opaque, a, b, 0.006, IRON, 6)


def jizaikagi(opaque, hook_h=None):
    """The adjustable pothook from the apex hub: bamboo tube, iron rod, fish lever, kettle.

    ``hook_h`` is the hook's height above the floor; the rod slides in the tube.
    """
    hook_h = C["pot_hang_m"] if hook_h is None else hook_h
    tube_top, tube_bot = M.apex - [0, 0, 0.12], M.apex - [0, 0, 1.25]
    solid_cylinder(opaque, M.apex, tube_top, 0.008, CORD, 6)      # lashed to the apex hub
    solid_cylinder(opaque, tube_top, tube_bot, 0.035, BAMBOO, 12)
    hook = H + [0, 0, hook_h]
    solid_cylinder(opaque, tube_bot + [0, 0, 0.3], hook + [0, 0, 0.02], 0.011, IRON, 8)
    opaque.box(hook, (0.03, 0.012, 0.05), IRON)
    # The fish: the lever that locks the rod by friction where the cord passes through it.
    fish = tube_bot - [0, 0, 0.12]
    opaque.box(fish, (0.24, 0.035, 0.085), FISH)
    for side in (-1, 1):
        n = np.array([0.0, side, 0.0])
        tail = fish + [0.12, side * 0.018, 0]
        opaque.triangle(tail, tail + [0.09, 0, 0.06], tail + [0.09, 0, -0.06], FISH, n)
        opaque.box(fish + [-0.08, side * 0.019, 0.015], (0.018, 0.002, 0.018), (0.9, 0.85, 0.6, 1))
    kettle(opaque, hook)
    return hook


def hidana(opaque):
    """The drying lattice, hung from the solver's upper ring of hubs."""
    z = H[2] + C["hood_m"] + 0.15
    half = 0.65
    for k in np.linspace(-half, half, 6):
        opaque.box([H[0] + k, H[1], z], (0.03, 2 * half, 0.03), LATTICE)
        opaque.box([H[0], H[1] + k, z + 0.03], (2 * half, 0.03, 0.03), LATTICE)
    ring = upper_ring()
    for cx, cy in ((1, 1), (1, -1), (-1, 1), (-1, -1)):
        corner = np.array([H[0] + cx * half, H[1] + cy * half, z])
        nearest = ring[np.argmin(np.linalg.norm(ring[:, :2] - corner[:2], axis=1))]
        solid_cylinder(opaque, corner, nearest, 0.006, CORD, 6)
    return z


def seat_positions():
    """(name, who, centre) for the four seats, the kijiri on the entry side."""
    r = F["hearth_outer_m"] / 2 + C["seat_depth_m"] / 2
    ent = ENTRY[:2]
    side = np.array([-ent[1], ent[0]])
    places = (-ent, side, -side, ent)               # yokoza, kakaza, kyakuza, kijiri
    return [(name, who, H + [*(d * r), 0]) for (name, who, _where), d in zip(ir.SEATS, places)]


def seats(app, opaque, labels=True):
    for (name, who, at), colour in zip(seat_positions(), CUSHIONS):
        opaque.box(at + [0, 0, 0.035], (0.55, 0.55, 0.07), colour)
        if labels:
            label(app, at + [0, 0, 0.25], name.upper(), AMBER)


def smoke(transparent, p, top=None):
    """Smoke rising from the coals; it pools under the apex unless ``top`` takes it away."""
    top = M.apex[2] - 0.15 if top is None else top
    for k in range(16):
        t = (k / 16 + p * 0.6) % 1
        z = H[2] + 0.15 + t * (top - H[2] - 0.15)
        spread = 0.08 + t * 0.55
        a = k * 2.4
        transparent.sphere([H[0] + spread * math.cos(a), H[1] + spread * math.sin(a), z],
                           0.10 + t * 0.18, SMOKE, 4, 8)


def hood_and_flue(opaque):
    """A steel hood over the pit and a flue straight up through the apex."""
    base = H + [0, 0, C["hood_m"]]
    opaque.cone(base, base + [0, 0, 0.42], 0.62, STEEL, 16)
    solid_cylinder(opaque, base + [0, 0, 0.30], M.apex + [0, 0, 0.75], 0.08, STEEL, 14)
    solid_cylinder(opaque, M.apex + [0, 0, 0.75], M.apex + [0, 0, 0.80], 0.14, STEEL, 14)
    return base


def pit_box(opaque):
    """The lined box under the floor, between the pad's piers."""
    outer = F["hearth_outer_m"]
    d = C["pit_depth_m"]
    # Pale masonry against the dark deck framing, so it reads between the piers.
    opaque.box(H - [0, 0, d / 2 + 0.06], (outer, outer, d), (0.80, 0.74, 0.64, 1))
    opaque.box(H - [0, 0, d + 0.08], (outer + 0.16, outer + 0.16, 0.04), (0.95, 0.55, 0.20, 1))


# ----------------------------------------------------------------------
# Painters, one per kind of shot
# ----------------------------------------------------------------------

def p_dome(app, opaque, transparent, p):
    world(app, subject=True)
    hearth(opaque, transparent, p)
    jizaikagi(opaque)
    seats(app, opaque, labels=False)
    label(app, M.apex + [0, 0, 0.6], "A FIRE IN THE MIDDLE OF THE FLOOR", AMBER)


def p_hearth(app, opaque, transparent, p):
    world(app)
    hearth(opaque, transparent, p)
    s = C["hearth_side_m"]
    label(app, H + [s / 2 + 0.05, 0, 0.12], "ROBUCHI (BORDER)", AMBER)
    label(app, H + [0, -s / 3, 0.05], "STONE-LINED PIT, ASH BED", WHITE)
    label(app, H + [0, 0, 0.30], "CHARCOAL", GREEN)


def p_hook(app, opaque, transparent, p):
    world(app)
    hearth(opaque, transparent, p)
    hook_h = C["pot_hang_m"] + 0.25 * math.sin(math.pi * p)     # the pot raised and lowered
    hook = jizaikagi(opaque, hook_h)
    label(app, M.apex - [0, 0, 0.6], "BAMBOO TUBE FROM THE APEX HUB", AMBER)
    label(app, M.apex - [0, 0, 1.35] + [0.25, 0, 0], "FISH LEVER LOCKS THE ROD", GREEN)
    label(app, hook + [0.25, 0, 0.05], f"ROD {F['rod_m']:.2f} M APEX TO HOOK", WHITE)


def p_jobs(app, opaque, transparent, p):
    world(app)
    hearth(opaque, transparent, p)
    jizaikagi(opaque)
    seats(app, opaque, labels=False)
    for k, (_slug, name, _then, _now) in enumerate(ir.JOBS):
        a = math.tau * k / len(ir.JOBS) - math.pi / 2
        label(app, H + [1.25 * math.cos(a), 1.25 * math.sin(a), 0.55 + 0.12 * (k % 2)],
              name.upper(), AMBER if k < 6 else GREEN)


def p_seats(app, opaque, transparent, p):
    world(app)
    hearth(opaque, transparent, p)
    seats(app, opaque)
    door = H + [*(ENTRY[:2] * (F["inner_r_m"] - 0.2)), 0.1]
    opaque.arrow(door + [*(ENTRY[:2] * 0.6), 0], door, 0.03, (0.4, 0.8, 0.5, 1))
    label(app, door + [0, 0, 0.35], "ENTRY (DOMA) SIDE", GREEN)


def p_inputs(app, opaque, transparent, p):
    world(app)
    hearth(opaque, transparent, p, lit=False)
    seats(app, opaque, labels=False)
    label(app, H + [0, 0, 0.45], "DECLARED INPUTS, NOT MEASUREMENTS", RED)


def p_fit(app, opaque, transparent, p):
    world(app)
    hearth(opaque, transparent, p, lit=False)
    seats(app, opaque, labels=False)
    r = F["seat_out_m"]
    for sx, sy in ((1, 0), (-1, 0), (0, 1), (0, -1)):
        size = (2 * r, 0.025, 0.012) if sx == 0 else (0.025, 2 * r, 0.012)
        opaque.box(H + [sx * r, sy * r, 0.01], size, (0.95, 0.75, 0.25, 1))
    label(app, H + [0, 0, 0.5], f"{F['circle_share'] * 100:.0f}% OF THE FLOOR", AMBER)
    label(app, H + [r, 0, 1.05], f"HEADROOM SEATED {F['seat_headroom_m']:.2f} M", GREEN)


def p_dry(app, opaque, transparent, p):
    world(app)
    hearth(opaque, transparent, p)
    for k in range(6):
        a = math.tau * k / 6
        start = H + [0.25 * math.cos(a), 0.25 * math.sin(a), 0.4]
        end = H + [1.6 * math.cos(a), 1.6 * math.sin(a), 2.0 + 0.2 * math.sin(p * 4 + k)]
        opaque.arrow(start, end, 0.02, (1.0, 0.55, 0.25, 1))
    label(app, M.apex - [0, 0, 0.4], f"WOOD EMC {F['emc_out']:.0f}% -> {F['emc_in']:.0f}%", AMBER)


def p_hidana(app, opaque, transparent, p):
    world(app)
    hearth(opaque, transparent, p)
    jizaikagi(opaque)
    z = hidana(opaque)
    label(app, [H[0] + 0.7, H[1], z + 0.15], "HIDANA, HUNG FROM THE UPPER RING", AMBER)


def p_smoke(app, opaque, transparent, p):
    world(app)
    hearth(opaque, transparent, p)
    jizaikagi(opaque)
    smoke(transparent, p)
    label(app, M.apex + [0, 0, 0.45], "SMOKE POOLS UNDER THE APEX", RED)


def p_co(app, opaque, transparent, p):
    world(app, subject=True)
    hearth(opaque, transparent, p)
    smoke(transparent, p)
    transparent.sphere(M.dome_centre, M.dome_r * 0.96, (0.95, 0.35, 0.25, 0.10), 8, 20)
    label(app, M.apex + [0, 0, 0.6], f"{F['volume_m3']:.0f} M3 OF AIR, SEALED", RED)


def p_flue(app, opaque, transparent, p):
    world(app, subject=True)
    hearth(opaque, transparent, p)
    jizaikagi(opaque)
    base = hood_and_flue(opaque)
    seats(app, opaque, labels=False)
    label(app, base + [0.7, 0, 0.2], "HOOD", AMBER)
    label(app, M.apex + [0, 0, 1.0], f"FLUE {F['flue_m']:.2f} M TO THE APEX", GREEN)


def p_under(app, opaque, transparent, p):
    world(app)
    hearth(opaque, transparent, p, lit=False)
    pit_box(opaque)
    label(app, H - [0, 0, 0.55], "NONCOMBUSTIBLE BOX UNDER THE FLOOR", AMBER)


def p_close(app, opaque, transparent, p):
    world(app, subject=True)
    hearth(opaque, transparent, p)
    jizaikagi(opaque)
    hood_and_flue(opaque)
    seats(app, opaque, labels=False)
    label(app, M.apex + [0, 0, 1.1], "KEEP THE CIRCLE, LOSE THE SMOKE", AMBER)


# ----------------------------------------------------------------------
# The chapters
# ----------------------------------------------------------------------

def ch(number, slug, title, promise, narration, equations):
    return Chapter(slug, f"{number:02}", title, promise, (narration,), tuple(equations),
                   max(8, len(narration.split()) / 2.5 + 1.5), (0, 0, 0), slug)


def m_ft(x: float) -> str:
    return f"{x:.2f} m ({x / 0.3048:.1f} ft)"


CHAPTERS = (
    ch(1, "purpose", "A fire in the middle of the floor", "The Japanese irori, under the wedge dome's apex.",
       "For centuries, Japanese farmhouses were built around a hole in the floor. The irori is a sunken hearth: "
       "a square pit lined with stone, burning charcoal, in the middle of the main room. "
       "A dome has its middle exactly where an irori wants to be, straight under the apex. "
       "So we put one in the solver's dome and checked what fits and what does not. "
       "Most of it fits beautifully. One part does not, and we will show you that number too.",
       (f"SOURCE: {ir.SOURCE['title']}, {ir.SOURCE['creator']} ({ir.SOURCE['licence']})",
        "Dome: the raw-wedge solver's 2V hemisphere", "No fire was lit or measured for this film")),
    ch(2, "hearth", "A square pit, lined with stone", "Border, stone, ash and charcoal.",
       "Here is the hearth in plan. A wooden border frames the opening and gives you a ledge for a cup. "
       "Inside it, stone lines the pit, and a deep bed of ash fills it. The charcoal sits in the ash. "
       "Ash is the insulation: it keeps the heat off the floor beneath and lets you bank the fire for the night. "
       "Food can be buried in it to roast, and skewered fish stood up around the coals. "
       f"Our pit is {C['hearth_side_m']:.2f} metres across inside, a size we chose for a three-metre dome.",
       ("Wooden border -> stone lining -> ash bed -> charcoal",
        f"ASSUMED: pit {C['hearth_side_m']:.2f} m inside; border {C['frame_w_m']:.2f} m",
        "Traditional sizes vary by house and region")),
    ch(3, "hook", "The hook that moves the pot", "The jizaikagi hangs from the apex hub.",
       "The pot hangs from a jizaikagi: an iron rod inside a bamboo tube, with a lever that locks it. "
       "The lever is often carved as a fish. Lift the kettle and the fish tilts and lets the rod slide; "
       "let go and friction holds it. Raise it to simmer, lower it to boil. "
       "In a farmhouse it hung from a beam. In the dome it hangs from the apex hub, where every member climbs to. "
       f"The solver puts the apex {m_ft(F['apex_m'])} above the floor, so the hook assembly spans "
       f"{m_ft(F['rod_m'])} from hub to hook.",
       ("Iron rod in a bamboo tube; a fish-shaped lever locks it",
        f"Solver: apex {F['apex_m']:.2f} m above the floor",
        f"ASSUMED: hook {C['pot_hang_m']:.2f} m above the floor",
        f"Hub to hook = {F['apex_m']:.2f} - {C['pot_hang_m']:.2f} = {F['rod_m']:.2f} m")),
    ch(4, "jobs", "Seven jobs for one fire", "Heat, cook, light, dry, keep fire, gather -- and the house itself.",
       "The irori did six jobs at once. It heated the whole room from the middle. It cooked. "
       "At night it was the light. A lattice above it dried clothes, food and firewood. "
       "Its coals were kept alive to light everything else, in the days before matches. "
       "And it was where the family gathered, every meal and every evening. "
       "There was a seventh job, for the building: its warm air dried the timbers, and its smoke coated them. "
       "Two of those jobs, light and keeping fire, are done better now by a lamp and a match.",
       (" / ".join(name for _slug, name, _then, _now in ir.JOBS[:3]),
        " / ".join(name for _slug, name, _then, _now in ir.JOBS[3:6]),
        f"+ {ir.JOBS[6][1]}: {ir.JOBS[6][3]}",
        "Light and keeping fire: done now by a lamp and a match")),
    ch(5, "seats", "Everyone has a place", "The seats round the hearth carried the household's order.",
       "Each person had a fixed seat. The yokoza, on the far side from the entry, belonged to the head of the household. "
       "The seats on either side went to the head's wife and to guests. "
       "The kijiri, nearest the entry, was the lowest seat, often the children's, beside the firewood. "
       "Names and customs varied from region to region. "
       "A round room with a centre is already arranged for this, and in the dome the entry side is the one facing you.",
       tuple(f"{name.upper()}: {who} ({where})" for name, who, where in ir.SEATS)),
    ch(6, "inputs", "Declare the inputs", "Choices we made, put on screen before we use them.",
       "Before we test the fit, here is what we chose rather than measured. "
       f"A pit {C['hearth_side_m']:.2f} metres wide inside, with a {C['frame_w_m']:.2f} metre border. "
       f"{C['seat_depth_m']:.2f} metres of floor for each person sitting at a side. "
       f"A seated head height of {C['seated_head_m']:.2f} metres. "
       f"A smoke hood with its underside at {C['hood_m']:.2f} metres. "
       f"And for the drying test, outside air at {C['out_t_c']:.0f} degrees and {C['out_rh'] * 100:.0f} percent humidity, "
       f"warmed to {C['in_t_c']:.0f} degrees. Change any of these and every figure after it changes with it.",
       tuple(f"{k.upper()}: {n} = {v:g} {u}" for n, v, u, k, _why in ir.CONSTANTS[:5])
       + (f"ASSUMPTION: outside {C['out_t_c']:.0f} C at {C['out_rh'] * 100:.0f}% RH, warmed to {C['in_t_c']:.0f} C",)),
    ch(7, "fit", "What the circle costs the floor", "It fits. It also takes a quarter of the room.",
       f"The solver's dome stands on a {F['base_sides']}-sided base with {F['floor_m2']:.1f} square metres of floor, "
       f"{F['floor_ft2']:.0f} square feet. The hearth with its border takes {F['hearth_share'] * 100:.1f} percent of that. "
       "That is the flattering number. The honest one counts the people: "
       f"the hearth and four seated people need a square {2 * F['seat_out_m']:.1f} metres on a side, "
       f"{F['circle_share'] * 100:.0f} percent of the floor, in the middle, where you cannot put a bed. "
       f"It does fit: the seat backs stop {F['seat_room_m']:.2f} metres short of the base ring, "
       f"and a seated head clears the frame by at least {F['seat_headroom_m']:.2f} metres.",
       (f"Solver: floor {F['floor_m2']:.1f} m2 ({F['floor_ft2']:.0f} ft2), {F['base_sides']}-sided base",
        f"Hearth: {F['hearth_outer_m']:.2f}^2 = {F['hearth_m2']:.2f} m2 = {F['hearth_share'] * 100:.1f}%",
        f"Circle: {2 * F['seat_out_m']:.1f}^2 = {F['circle_m2']:.2f} m2 = {F['circle_share'] * 100:.0f}% of the floor",
        f"Seated headroom: {F['seat_head_min_m']:.2f} - {C['seated_head_m']:.2f} = {F['seat_headroom_m']:.2f} m")),
    ch(8, "dry", "Warm air dries the frame", "The one claim about the building this book can compute.",
       "The article says the irori's warm air lowered the moisture in the house's wood and slowed decay. "
       "That part we can work out. "
       f"Outside air at {C['out_t_c']:.0f} degrees and {C['out_rh'] * 100:.0f} percent humidity, warmed to "
       f"{C['in_t_c']:.0f} degrees with no water added, falls to {F['rh_in'] * 100:.0f} percent. "
       "The Wood Handbook's equilibrium formula says wood left in the cold, damp air settles near "
       f"{F['emc_out']:.0f} percent moisture, and in the warmed air near {F['emc_in']:.0f} percent. "
       "Decay fungi need wet wood, so that is the right direction by a long way. "
       "It is where the wood ends up after weeks, not how fast it gets there.",
       (f"RH warmed = {C['out_rh']:.2f} x es({C['out_t_c']:.0f}) / es({C['in_t_c']:.0f}) = {F['rh_in']:.2f}",
        f"EMC outside ({C['out_t_c']:.0f} C, {C['out_rh'] * 100:.0f}%) = {F['emc_out']:.1f}%",
        f"EMC warmed ({C['in_t_c']:.0f} C, {F['rh_in'] * 100:.0f}%) = {F['emc_in']:.1f}%",
        "STANDARD: Hailwood-Horrobin fit, USDA Wood Handbook ch. 4")),
    ch(9, "hidana", "The rack overhead", "A drying lattice, hung from the upper ring.",
       "Above many irori hung a wooden lattice called the hidana. Clothes, food and green wood dried on it in the rising heat, "
       "and it spread out sparks before they reached the roof. "
       "The dome has a ready place to hang one. The ring of hubs just below the apex is directly above the hearth, "
       "so four cords to four of those hubs carry the lattice level, out of a standing person's way. "
       "Nothing on it should be anywhere near the coals, and nothing should drip into them.",
       ("Hidana: a lattice for drying and for catching sparks",
        f"Hung {C['hood_m'] + 0.15:.2f} m above the floor from the solver's upper ring",
        "Keep combustibles clear of the fire")),
    ch(10, "smoke", "What the smoke did for a thatched roof", "A claim from the source, and its cost.",
       "The article makes a second claim about the building: tar in the smoke soaked into the beams and thatch "
       "and helped keep insects and water out. That is the source's claim, not something this film has tested. "
       "It also names the cost. The smoke filled the house and caused eye disease and other illness. "
       "Watch where the smoke goes in a dome. A thatched roof leaks smoke everywhere. "
       "A dome concentrates it under the apex, the one place this book has worked hardest to seal.",
       ("CLAIMED (source): smoke tar protected beams and thatch",
        "CLAIMED (source): smoke caused eye disease and other illness",
        "Not tested in this film")),
    ch(11, "co", "The number that argues against it", "An open charcoal fire in a tight room.",
       f"Here is the number that argues against it. The solver's dome holds {F['volume_m3']:.0f} cubic metres of air, "
       f"{F['volume_ft3']:,.0f} cubic feet. A farmhouse with an irori was tall, open to its roof, and leaky by design. "
       "This book spends whole chapters making the dome tight. "
       "Charcoal burns without much visible smoke, but it makes carbon monoxide, which you cannot see or smell, "
       "and burning charcoal in a closed room is a known cause of carbon monoxide poisoning. "
       "So, plainly: do not burn an open charcoal irori in a sealed dome.",
       (f"Solver: {F['volume_m3']:.1f} m3 ({F['volume_ft3']:,.0f} ft3) inside the facets",
        "Open charcoal fire -> carbon monoxide",
        "Tight envelope: no open fire without a flue")),
    ch(12, "flue", "Keep the circle, give the fire a chimney", "A hood and a flue through the apex.",
       "The answer keeps everything people loved about the irori and removes the smoke. "
       f"A steel hood over the pit, its underside {C['hood_m']:.2f} metres up, and a flue straight up through the apex: "
       f"{m_ft(F['flue_m'])} of pipe from hood to hub before it leaves the shell. "
       "The apex is already the dome's one designed penetration, the same exit this book gives a wood stove. "
       "Use a listed appliance or a design an inspector will approve, follow its clearances to the timber, "
       "give it a supply of combustion air, and fit a carbon monoxide alarm. The hook can hang beside the hood or from it.",
       (f"Flue from hood to apex = {F['apex_m']:.2f} - {C['hood_m']:.2f} = {F['flue_m']:.2f} m",
        "Listed appliance or approved design; its clearances govern",
        "Combustion air + carbon monoxide alarm")),
    ch(13, "under", "A pit in a raised floor", "The box between the piers.",
       "The Cabin World's floor stands on piers, with air beneath it, so the pit cannot be dug into the ground. "
       "It becomes a box framed into the floor, hanging between the joists. "
       f"Ours is {C['pit_depth_m']:.2f} metres deep, which leaves room under the pad. "
       "It must be noncombustible and separated from the framing, holding the ash bed that keeps the heat from the floor. "
       "How it is lined, how far it stands off the joists and how it is supported are set by the appliance's "
       "instructions and your local code, not by this film.",
       (f"ASSUMED: box {C['pit_depth_m']:.2f} m deep; pad top 0.62 m above grade",
        "Noncombustible box; ash bed; separated from the joists",
        "Clearances and support: manufacturer and local code")),
    ch(14, "close", "A circle with a chimney", "The irori's room, with the smoke taken away.",
       "So the irori and the dome agree about almost everything. Both put the fire in the middle. "
       "The hook hangs from the apex, the drying rack from the ring below it, and four people sit round it "
       f"with room behind them. It costs {F['circle_share'] * 100:.0f} percent of the floor, and that is the price of the gathering. "
       "What does not carry over is the open smoke. Give the fire a hood, a flue and an alarm, "
       "and you keep the oldest arrangement of a home: everyone facing the same fire.",
       ("Keep: centre, hook, rack, seats", "Change: hood + flue + CO alarm",
        f"Cost: {F['circle_share'] * 100:.0f}% of the floor")),
)

SCENES = {
    "purpose": p_dome, "hearth": p_hearth, "hook": p_hook, "jobs": p_jobs, "seats": p_seats,
    "inputs": p_inputs, "fit": p_fit, "dry": p_dry, "hidana": p_hidana, "smoke": p_smoke,
    "co": p_co, "flue": p_flue, "under": p_under, "close": p_close,
}


# ----------------------------------------------------------------------
# Cameras
# ----------------------------------------------------------------------

def _moves():
    r = M.dome_r
    # Outside, through the open frame: guarded against the pines like every Cabin World shot.
    hero = cabin_stage.clear_view(shots.orbit(M.dome_centre + [0, 0, r * 0.45], r * 3.3, r * 0.9, -100, 14, 44))
    wide = cabin_stage.clear_view(shots.orbit(M.dome_centre + [0, 0, r * 0.55], r * 3.8, r * 1.4, -80, -18, 46))
    above = cabin_stage.clear_view(shots.orbit(H, r * 1.55, r * 1.5, -100, 30, 44))
    # Low, between the piers, to see the box hanging under the floor.
    under = cabin_stage.clear_view(shots.push_in(H - [0, 0, 0.25], H + [2.5, -5.6, -0.26],
                                                 H + [2.3, -5.4, -0.26], 40, 36))
    # Inside, at a seated person's eye height on the entry side; no pine can be in the way
    # and cabin_stage.clear_view would push any eye inside the dome back out of it.
    seated = shots.push_in(H + [0, 0, 0.12], H + [0.35, -2.05, 1.05], H + [0.25, -1.65, 0.85], 50, 40)
    hook = shots.crane_reveal(M.apex - [0, 0, 0.9], H + [0.45, -1.75, 0.70], H + [0.55, -2.15, 1.25],
                              40, 52, look_start=H + [0, 0, 0.30])
    up = shots.push_in(M.apex - [0, 0, 0.9], H + [0.6, -2.1, 0.9], H + [0.5, -1.9, 0.95], 56, 50)
    # Low by the wall, the hearth at the bottom of frame and the warm air rising past the frame.
    rising = shots.push_in(H + [0, 0, 1.15], H + [0.6, -2.35, 0.50], H + [0.5, -2.25, 0.55], 62, 58)
    return {"purpose": hero, "hearth": seated, "hook": hook, "jobs": above, "seats": above,
            "inputs": above, "fit": above, "dry": rising, "hidana": up, "smoke": up, "co": hero,
            "flue": hero, "under": under, "close": wide}


MOVES = _moves()
camera = shots.by_chapter(MOVES)


def validate_cabin_irori():
    ir.validate_irori()
    cw.validate_cabin_world()
    assert set(SCENES) == set(MOVES) == {c.slug for c in CHAPTERS}
    slugs = [c.slug for c in CHAPTERS]
    # Inputs go on screen before the figures that use them; the CO number before the fix.
    assert slugs.index("inputs") < slugs.index("fit") < slugs.index("dry")
    assert slugs.index("co") < slugs.index("flue")
    assert f"{F['circle_share'] * 100:.0f} percent" in next(c for c in CHAPTERS if c.slug == "fit").narration[0]
    assert f"{F['volume_m3']:.0f} cubic metres" in next(c for c in CHAPTERS if c.slug == "co").narration[0]
    # The hook really hangs from the hub the solver put at the top.
    assert abs(M.apex[2] - (M.dome_centre[2] + F["apex_m"])) < 1e-6
    for name, _who, at in seat_positions():
        assert np.linalg.norm(at[:2] - H[:2]) + 0.4 < F["inner_r_m"], name
    assert len(upper_ring()) == 5, "the ring of five hubs below the apex"
    for c in CHAPTERS:
        for p in (0, 0.25, 0.5, 0.75, 1):
            eye, target, fov = MOVES[c.slug](p)
            eye, target = np.asarray(eye), np.asarray(target)
            assert np.all(np.isfinite(eye)) and np.all(np.isfinite(target))
            assert 20 < fov < 70 and eye[2] > 0.3, c.slug
            assert np.linalg.norm(eye - target) > 0.3
            assert not cabin_stage.blocked(eye, target), c.slug
            if np.hypot(*eye[:2]) < M.dome_r:                    # an inside camera stays under the shell
                assert eye[2] - M.dome_centre[2] < ir.shell_height(*eye[:2]) - 0.2, c.slug
    # Exercise every painter without a GPU.
    class App:
        def __init__(self):
            self.world_labels = []

        def static_layer(self, key, builder, subject_points=None):
            assert np.all(np.isfinite(builder().vertices)), key
    for painter in set(SCENES.values()):
        app, opaque, transparent = App(), TriangleBatch(), TriangleBatch()
        painter(app, opaque, transparent, 0.6)
        assert np.all(np.isfinite(opaque.vertices)) and np.all(np.isfinite(transparent.vertices))
        assert app.world_labels, painter.__name__
        for item in app.world_labels:
            assert np.all(np.isfinite(item.point))
            assert all(isinstance(x, int) and 0 <= x <= 255 for x in item.color)
    CABIN_IRORI_LESSON.validate()


CABIN_IRORI_LESSON = Lesson(
    key="cabin_irori", brand="DOMESIM", title="The Irori: A Sunken Hearth Under the Dome's Apex",
    chapters=CHAPTERS, scenes=SCENES, selftest=validate_cabin_irori, report=ir.report,
    snapshot_prefix="cabin_irori", camera_fn=camera, ground="off",
    backdrop=cw.backdrop, light=cw.LIGHT, label_layout="declutter",
    audio_bed="beds/cabin-explained", audio_bed_gain=0.12,
)
