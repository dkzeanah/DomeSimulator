"""The campaign film: a tiny house you can take apart, and what one costs.

The pitch, in one sentence: we make a bare standard dome -- a *stem cell* --
and you build on it. The frame comes out of trees already standing on the
site, the shell is a boat hull, the services live in a core that unbolts and
moves to the next dome, and the ground it stands on is somebody else's bill.

Three things this film has to do that a normal pitch does not:

**Say whose money is whose.** A landowner and a dome buyer are two different
people paying two different bills, and every existing tiny-house price adds
them together. The pad is amber. The dome is cyan. The line never moves.

**Price the shell like a boat.** It is a wood-cored composite skin, which is a
sixty-year-old trade with a handful of named laminate systems and a published
price list. :mod:`hull_laminate` is those systems; this film shows all four and
says which one is in the box.

**Argue against itself on camera.** The standard dome is not insulated, the
no-mitre frame wastes wood, and the prices are assumptions. All three are
chapters, not footnotes.

Every figure comes from :mod:`two_v_demo.seed_facts`, which reads
:mod:`seed_model` at render time. Every dome on screen is the raw-wedge
solver's own building through :mod:`two_v_demo.seed_bridge`. There is no second
set of numbers and no sketch of a dome anywhere in it.
"""

from __future__ import annotations

import math
from dataclasses import replace

import numpy as np

import seed_model
import seed_world

from . import creator_bridge as creator
from . import seed_bridge as seed
from .lessons import Chapter, Lesson
from .render_kit import (
    AMBER,
    CYAN,
    GREEN,
    MUTED,
    RED,
    WHITE,
    WorldLabel,
    clamp,
    ease_in_out,
)
from .seed_facts import (
    ALL_SCREENS,
    QUILT_COMPARE_LAYERS,
    steps_deck,
    steps_paint,
    steps_solar,
    steps_stemcell,
    seed_film_report,
    steps_against,
    steps_bay,
    steps_duct,
    steps_floating,
    steps_hats,
    steps_layering,
    steps_mast,
    steps_quilt,
    steps_system,
    steps_core,
    steps_declared,
    steps_frame,
    steps_ladder,
    steps_pad,
    steps_price,
    steps_seeds,
    steps_sheet,
    steps_shell,
    validate_seed_facts,
)

FT_PER_M = 3.280839895

HOST = AMBER
"""Everything the landowner pays for. The same colour the dome-park film
uses for the same person, so somebody who has seen both is not relearning it."""

BUYER = CYAN
"""Everything the dome buyer owns."""


def _rgb(colour) -> tuple[int, int, int]:
    return tuple(int(round(channel * 255)) for channel in colour[:3])


def _label(app, point, text: str, colour) -> None:
    if text:
        app.world_labels.append(
            WorldLabel(np.asarray(point, dtype=np.float32), text,
                       _rgb(colour)))


def _screen_left(app) -> np.ndarray:
    """The world direction that reads as leftward at this chapter's camera."""
    yaw = math.radians(float(getattr(app, "camera_yaw", 90.0)))
    return np.array([math.sin(yaw), -math.cos(yaw), 0.0])


def _shift(app) -> np.ndarray:
    """Where the subject stands, given what the overlay is using.

    A math chapter spends the right of the frame on its worksheet, so a stage
    composed for the whole frame comes back cut down the middle. Slide by a
    share of the camera's own distance, so one rule holds at every shot.
    """
    chapters = getattr(app, "chapters", None)
    index = getattr(app, "chapter_index", None)
    if not chapters or index is None:
        return np.zeros(3)
    if (chapters[index].overlay or "") != "math":
        return np.zeros(3)
    # A fifth of the camera's distance, not the quarter the park film uses:
    # this film's subject is one dome rather than a row of them, so it is
    # bigger in frame and slides off the edge sooner.
    distance = float(getattr(app, "camera_distance", 24.0))
    return _screen_left(app) * distance * 0.20


BASE_Z = None


def _base() -> float:
    global BASE_Z
    if BASE_Z is None:
        BASE_Z = seed.base_z()
    return BASE_Z


def _apex() -> float:
    return seed_world.apex_m("hemisphere")


def _ground(app, shift) -> None:
    """The Creator's own field, so the dome is not on an island."""
    creator.draw(app, creator.environment(), offset=tuple(shift))


#: The three skins of the soft shell, kept apart on purpose: wood panels
#: under a quilt under a cap. Drawn in one colour each because the whole
#: point of the chapters that use them is that they are separate objects
#: which come off separately.
PANEL_WOOD = (0.52, 0.38, 0.22)
QUILT_RED = (0.68, 0.26, 0.28)
CAP_BLUE = (0.34, 0.60, 0.74)


# ----------------------------------------------------------------------
# Scenes
# ----------------------------------------------------------------------

def scene_standing(app, opaque, transparent, p: float) -> None:
    """The finished thing: a dome on a pad, shell on, lit."""
    shift = _shift(app)
    _ground(app, shift)
    creator.draw(app, seed.pad(), offset=tuple(shift))
    creator.draw(app, seed.dome(shell=True),
                 offset=tuple(shift + np.array([0.0, 0.0, _base()])))
    if p > 0.30:
        _label(app, shift + np.array([0.0, 0.0, _base() + _apex() + 1.3]),
               "ONE STANDARD DOME", BUYER)
    if p > 0.55:
        priced = seed_model.quote()
        _label(app, shift + np.array([0.0, 0.0, _base() + _apex() + 0.5]),
               f"${priced.price:,.0f}", GREEN)
    if p > 0.75:
        _label(app, shift + np.array([0.0, -2.6, 0.15]),
               "THE PAD IS SOMEBODY ELSE'S", HOST)


def scene_frame(app, opaque, transparent, p: float) -> None:
    """The bare wedge frame, cut from the buyer's own trees."""
    shift = _shift(app)
    _ground(app, shift)
    creator.draw(app, seed.pad(), offset=tuple(shift))
    creator.draw(app, seed.frame(),
                 offset=tuple(shift + np.array([0.0, 0.0, _base()])))
    geometry = seed_model.seed_geometry()
    if p > 0.25:
        _label(app, shift + np.array([0.0, 0.0, _base() + _apex() + 1.2]),
               f"{geometry.member_count} MEMBERS", BUYER)
    if p > 0.5:
        _label(app, shift + np.array([0.0, 0.0, _base() + _apex() + 0.4]),
               f"{geometry.trees_needed:.1f} TREES", GREEN)
    if p > 0.72:
        cut = seed_model.harvest()
        _label(app, shift + np.array([2.2, 0.0, _base() + 0.9]),
               f"{cut.wedge_recovery * 100:.0f}% OF THE TRUNK", MUTED)
    if p > 0.86:
        cut = seed_model.harvest()
        _label(app, shift + np.array([-2.4, 0.0, _base() + 0.9]),
               f"MILLING TAKES {cut.dimensional_recovery * 100:.0f}%", HOST)


def scene_shell_on(app, opaque, transparent, p: float) -> None:
    """The shell lowered onto the frame, by the crane that does it."""
    shift = _shift(app)
    _ground(app, shift)
    creator.draw(app, seed.pad(), offset=tuple(shift))
    creator.draw(app, seed.frame(),
                 offset=tuple(shift + np.array([0.0, 0.0, _base()])))
    # The shell comes down over the whole chapter, which is the one thing a
    # still cannot show and the reason this is a moving picture at all.
    lift = (1.0 - ease_in_out(clamp(p * 1.25))) * 3.4
    creator.draw(app, seed.crane(), offset=tuple(shift))
    creator.draw(app, seed.shell(lift=max(lift, 0.001)),
                 offset=tuple(shift + np.array([0.0, 0.0, _base()])))
    plan = seed_model.shell_plan(None, "boatyard")
    if p > 0.2:
        _label(app, shift + np.array([0.0, 0.0, _base() + _apex() + lift + 1.1]),
               "THE SHELL COMES OFF", BUYER)
    if p > 0.6:
        _label(app, shift + np.array([0.0, 0.0, _base() + _apex() + lift + 0.3]),
               f"{plan.weight_lb:,.0f} LB", MUTED)


def scene_deck(app, opaque, transparent, p: float) -> None:
    """The platform going up, one course at a time, then the dome on it."""
    import pad_deck

    shift = _shift(app)
    _ground(app, shift)
    stages = seed_world.DECK_STAGES
    # The last fifth of the chapter stands the dome on the finished thing,
    # because a platform is only interesting for what lands on it.
    build_p = clamp(p / 0.80)
    span = 1.0 / len(stages)
    index = min(len(stages) - 1, int(build_p / span))
    local = round(clamp((build_p - index * span) / span), 2)
    creator.draw(app, seed.deck(stages[index], local), offset=tuple(shift))

    steps = pad_deck.build_sequence("blocks")
    running = steps[min(index, len(steps) - 1)].cumulative_usd
    if p > 0.10:
        _label(app, shift + np.array([0.0, 0.0, 2.3]),
               stages[index].upper(), BUYER)
    # The running total retires the moment the final one appears, or the two
    # land on the same patch of screen and argue.
    if 0.22 < p <= 0.80:
        _label(app, shift + np.array([0.0, 0.0, 1.7]),
               f"${running:,.0f} SO FAR", GREEN)
    if p > 0.80:
        creator.draw(app, seed.frame(),
                     offset=tuple(shift + np.array([0.0, 0.0, 0.66])))
        total = pad_deck.deck("blocks")
        _label(app, shift + np.array([0.0, -3.4, 0.5]),
               f"${total.cost:,.0f}  ·  {total.boards:.0f} BOARDS", HOST)


def scene_slices(app, opaque, transparent, p: float) -> None:
    """The shell coming apart into the pieces it is moulded in."""
    shift = _shift(app)
    _ground(app, shift)
    creator.draw(app, seed.pad(), offset=tuple(shift))
    creator.draw(app, seed.frame(),
                 offset=tuple(shift + np.array([0.0, 0.0, _base()])))
    # Quantised so the cached builds get reused: the shell is 40 faces and
    # rebuilding it every frame costs more than the motion is worth.
    apart = round(ease_in_out(clamp((p - 0.12) / 0.62)), 2)
    creator.draw(app, seed.shell(split=apart),
                 offset=tuple(shift + np.array([0.0, 0.0, _base()])))
    slices = int(round(seed_model.declared("shell_halves")))
    plan = seed_model.shell_plan(None, "boatyard")
    if p > 0.22:
        _label(app, shift + np.array([0.0, 0.0, _base() + _apex() + 1.1]),
               f"{slices} SLICES", BUYER)
    if p > 0.48:
        _label(app, shift + np.array([0.0, 0.0, _base() + _apex() + 0.3]),
               f"{plan.weight_lb / slices:,.0f} LB EACH", MUTED)
    if p > 0.70:
        _label(app, shift + np.array([0.0, -3.6, 0.5]),
               "S-LIP SEAMS, GASKETED", GREEN)


def scene_core(app, opaque, transparent, p: float) -> None:
    """The utility core alone: pad port to apex and out through it."""
    shift = _shift(app)
    _ground(app, shift)
    creator.draw(app, seed.pad(), offset=tuple(shift))
    creator.draw(app, seed.core(open_cap=p > 0.62),
                 offset=tuple(shift + np.array([0.0, 0.0, _base()])))
    if p > 0.16:
        _label(app, shift + np.array([0.0, 0.0, _base() + 0.35]),
               "POWER AND WATER ARRIVE HERE", HOST)
    if p > 0.36:
        _label(app, shift + np.array([1.0, 0.0, _base() + 1.15]),
               "FIXTURES AT WORKING HEIGHT", BUYER)
    if p > 0.58:
        _label(app, shift + np.array([0.0, 0.0, _base() + _apex() + 0.9]),
               "AND OUT THROUGH THE TOP", GREEN)
    if p > 0.78:
        _label(app, shift + np.array([0.0, 0.0, _base() + _apex() + 0.2]),
               "THE SEAL CAP", MUTED)


def scene_polyp(app, opaque, transparent, p: float) -> None:
    """A dome with its panels, and what snaps into one."""
    shift = _shift(app)
    _ground(app, shift)
    creator.draw(app, seed.pad(), offset=tuple(shift))
    creator.draw(app, seed.dome("home", shell=p > 0.45),
                 offset=tuple(shift + np.array([0.0, 0.0, _base()])))
    radius = seed_world.footprint_radius_m("hemisphere")
    if p > 0.22:
        angle = math.radians(34.0)
        point = shift + np.array([math.cos(angle) * (radius + 0.9),
                                  math.sin(angle) * (radius + 0.9),
                                  _base() + 1.9])
        _label(app, point, "OUTSIDE THE FOOTPRINT", BUYER)
    if p > 0.5:
        _label(app, shift + np.array([0.0, 0.0, _base() + _apex() + 1.0]),
               "FED FROM UNDER THE CAP", GREEN)
    if p > 0.74:
        _label(app, shift + np.array([0.0, 0.0, _base() + 0.8]),
               "NO NEW HOLE IN THE SHELL", MUTED)


def scene_move(app, opaque, transparent, p: float) -> None:
    """Two domes, one core: the modular argument, photographed."""
    shift = _shift(app)
    _ground(app, shift)
    span = seed_world.footprint_radius_m("hemisphere") * 3.4
    left = shift + np.array([-span * 0.5, 0.0, 0.0])
    right = shift + np.array([span * 0.5, 0.0, 0.0])

    creator.draw(app, seed.pad(), offset=tuple(left))
    creator.draw(app, seed.pad(), offset=tuple(right))
    creator.draw(app, seed.dome(shell=True),
                 offset=tuple(left + np.array([0.0, 0.0, _base()])))
    creator.draw(app, seed.dome("home", shell=True),
                 offset=tuple(right + np.array([0.0, 0.0, _base()])))

    # The core is carried across the gap between the two domes, on an arc.
    # Sliding it along the ground put it inside whichever dome it was
    # nearest, which is the one thing this shot must not show.
    travel = ease_in_out(clamp((p - 0.22) / 0.58))
    gap = seed_world.footprint_radius_m("hemisphere") * 1.05
    from_x = left[0] + gap
    to_x = right[0] - gap
    lift = math.sin(math.pi * travel) * 2.4
    where = np.array([from_x + (to_x - from_x) * travel, 0.0, 0.0])
    creator.draw(app, seed.core(),
                 offset=tuple(shift + where
                              + np.array([0.0, 0.0, _base() + lift])))
    priced = seed_model.quote()
    if p > 0.12:
        _label(app, left + np.array([0.0, 0.0, _base() + _apex() + 1.0]),
               "THE FIRST DOME", MUTED)
    if p > 0.12:
        _label(app, right + np.array([0.0, 0.0, _base() + _apex() + 1.0]),
               "THE NEXT ONE", BUYER)
    if p > 0.34:
        _label(app, shift + where + np.array([0.0, 0.0,
                                              _base() + lift + _apex() + 0.7]),
               f"THE CORE: ${priced.core_cost:,.0f}", GREEN)
    if p > 0.66:
        _label(app, shift + where + np.array([0.0, 0.0,
                                              _base() + lift - 0.4]),
               "BOUGHT ONCE", GREEN)


def scene_pad(app, opaque, transparent, p: float) -> None:
    """The pad on its own, then the dome landing on it."""
    shift = _shift(app)
    _ground(app, shift)
    creator.draw(app, seed.pad(), offset=tuple(shift))
    # A short drop, started early. Five metres of it put the dome out of the
    # top of the frame on the chapter that shares the screen with a worksheet.
    drop = (1.0 - ease_in_out(clamp((p - 0.25) / 0.55))) * 3.0
    if p > 0.25:
        creator.draw(app, seed.dome(shell=True),
                     offset=tuple(shift + np.array([0.0, 0.0,
                                                    _base() + drop])))
    priced = seed_model.quote()
    if p > 0.12:
        _label(app, shift + np.array([0.0, 0.0, 0.55]),
               f"BUILT ONCE: ${priced.pad_cost:,.0f}", HOST)
    if p > 0.3:
        _label(app, shift + np.array([0.0, -2.8, 0.2]),
               "AND IT STAYS", HOST)
    if p > 0.72:
        _label(app, shift + np.array([0.0, 0.0,
                                      _base() + drop + _apex() + 1.0]),
               "NONE OF IT IN THE DOME'S PRICE", BUYER)


def scene_close(app, opaque, transparent, p: float) -> None:
    """The dome again, and the number the campaign is asking for."""
    shift = _shift(app)
    _ground(app, shift)
    creator.draw(app, seed.pad(), offset=tuple(shift))
    creator.draw(app, seed.dome("home", shell=True),
                 offset=tuple(shift + np.array([0.0, 0.0, _base()])))
    priced = seed_model.quote()
    _build, floor = seed_model.floor_price()
    if p > 0.2:
        _label(app, shift + np.array([0.0, 0.0, _base() + _apex() + 1.3]),
               f"${floor:,.0f} TO ${priced.price:,.0f}", GREEN)
    if p > 0.45:
        _label(app, shift + np.array([0.0, 0.0, _base() + _apex() + 0.5]),
               f"{priced.geometry.floor_decagon_sqft:,.0f} SQ FT", BUYER)
    if p > 0.68:
        _label(app, shift + np.array([0.0, -2.8, 0.2]),
               "BRING YOUR OWN GROUND", HOST)


def scene_bay(app, opaque, transparent, p: float) -> None:
    """One bay, coming apart: lip, inner panel, cavity, outer panel, shell."""
    shift = _shift(app)
    _ground(app, shift)
    # Quantised, because the bay is cached per explosion and a continuous
    # value would build a new mesh every frame.
    explode = round(ease_in_out(clamp((p - 0.12) / 0.62)) * 0.34, 2)
    creator.draw(app, seed.bay(explode),
                 offset=tuple(shift + np.array([0.0, 0.0, 1.1])))
    geometry = seed_model.seed_geometry()
    lip = seed_model.declared("panel_lip_in")
    if p > 0.16:
        _label(app, shift + np.array([-1.3, 0.0, 1.1]),
               f"THE WEDGE LEAVES A {lip:.2f} IN LIP", BUYER)
    if p > 0.40:
        _label(app, shift + np.array([1.2, 0.0, 1.1 + explode * 1.0]),
               f"CAVITY: {geometry.member_depth_in:.0f} IN", GREEN)
    if p > 0.62:
        _label(app, shift + np.array([0.0, 0.0, 1.1 + explode * 3.6]),
               "THE SHELL LANDS ON THE FRAME", MUTED)
    if p > 0.80:
        _label(app, shift + np.array([0.0, -1.3, 0.75]),
               "NOTHING HERE IS SCREWED DOWN", HOST)


def scene_duct(app, opaque, transparent, p: float) -> None:
    """The seam network lit up, with the air running through it."""
    shift = _shift(app)
    _ground(app, shift)
    creator.draw(app, seed.pad(), offset=tuple(shift))
    creator.draw(app, seed.frame(),
                 offset=tuple(shift + np.array([0.0, 0.0, _base()])))
    # The bead runs the channels; quantised for the same cache reason.
    flow = round((p * 2.4) % 1.0, 2)
    water = p > 0.62
    creator.draw(app, seed.ducts(flow, water),
                 offset=tuple(shift + np.array([0.0, 0.0, _base()])))
    duct = seed_model.seam_duct()
    if p > 0.14:
        _label(app, shift + np.array([0.0, 0.0, _base() + _apex() + 1.0]),
               f"{duct.length_ft:,.0f} FT OF CHANNEL", BUYER)
    if p > 0.36:
        _label(app, shift + np.array([2.4, 0.0, _base() + 1.4]),
               "BLOW: NOTHING STAYS DAMP", GREEN)
    if p > 0.62:
        _label(app, shift + np.array([-2.4, 0.0, _base() + 1.4]),
               f"DRAW: {duct.gallons_per_year:,.0f} GAL A YEAR", HOST)


def scene_swap(app, opaque, transparent, p: float) -> None:
    """One frame, becoming three different buildings while you watch."""
    shift = _shift(app)
    _ground(app, shift)
    creator.draw(app, seed.pad(), offset=tuple(shift))
    creator.draw(app, seed.frame(),
                 offset=tuple(shift + np.array([0.0, 0.0, _base()])))
    # Three fit-outs in turn, each seating its own panels and then clearing.
    order = ("gym", "guest", "garage")
    span = 1.0 / len(order)
    index = min(len(order) - 1, int(p / span))
    local = clamp((p - index * span) / span)
    # Quantised: the panel sets are cached per reveal step.
    reveal = round(min(1.0, local * 1.8), 2)
    creator.draw(app, seed.panels(order[index], reveal),
                 offset=tuple(shift + np.array([0.0, 0.0, _base()])))
    spec = seed_model.fitout(order[index])
    if local > 0.20:
        _label(app, shift + np.array([0.0, 0.0, _base() + _apex() + 1.1]),
               spec.label.upper(), BUYER)
    if local > 0.45:
        _label(app, shift + np.array([0.0, 0.0, _base() + _apex() + 0.3]),
               f"{seed_model.bays_changed(order[index])} BAYS CHANGED", GREEN)
    if p > 0.80:
        _label(app, shift + np.array([0.0, -3.4, 0.4]),
               "SAME FRAME. SAME PAD. SAME CORE.", HOST)


def scene_cap(app, opaque, transparent, p: float) -> None:
    """Hats stacking: the frame, its panels, and a cap a size up each time.

    A hull is moulded once at one size and its cavity holds four layers,
    full stop. A cap is a bag, so every quilted layer under it buys the next
    cap a size up.

    The stack is drawn *apart* in the middle of the chapter, because the
    real spacing -- ``soft_shell.soft_shell(n).added_r`` inches on a radius
    of 116 -- reads as one dome and puts the chapter's whole claim off
    screen. The last beat lowers them, so the picture it ends on is the
    true one and the labels carry the real areas throughout.
    """
    import soft_shell

    shift = _shift(app)
    _ground(app, shift)
    up = np.array([0.0, 0.0, _base()])
    creator.draw(app, seed.pad(), offset=tuple(shift))
    creator.draw(app, seed.frame(), offset=tuple(shift + up))
    # The wood panels first: they are what the cap goes over, and they are
    # on the outside face of the frame, which is the whole reversal.
    if p > 0.12:
        creator.draw(app, seed.cap(0, colour=PANEL_WOOD),
                     offset=tuple(shift + up))
    stack = QUILT_COMPARE_LAYERS
    sizes = soft_shell.hat_sizes(stack)
    # Apart from 0.34, together again from 0.78. Quantised, so the caches
    # hold: each of these is a whole dome mesh.
    spread = round(ease_in_out(clamp((p - 0.34) / 0.22))
                   - ease_in_out(clamp((p - 0.78) / 0.18)), 2)
    shown = clamp((p - 0.20) / 0.40) * stack
    top = _base() + _apex()
    for layer in range(stack):
        if clamp(shown - layer) <= 0.02:
            continue
        rise = spread * 0.78 * (layer + 1)
        creator.draw(app, seed.cap(layer + 1, alpha=0.90, colour=QUILT_RED,
                                   lift=rise),
                     offset=tuple(shift + up))
        if spread > 0.45:
            _label(app, shift + np.array([0.0, 0.0, top + rise + 0.32]),
                   f"CAP {layer + 1}  ·  {sizes[layer + 1]:,.0f} SQ FT",
                   GREEN if layer else BUYER)
    if p > 0.12 and spread > 0.45:
        _label(app, shift + np.array([0.0, 0.0, top + 0.32]),
               f"BARE  ·  {sizes[0]:,.0f} SQ FT", MUTED)
    if p > 0.62:
        creator.draw(app, seed.cap(stack, alpha=0.55, colour=CAP_BLUE,
                                   extra_in=0.9,
                                   lift=spread * 0.78 * (stack + 1)),
                     offset=tuple(shift + up))
    if p < 0.34:
        _label(app, shift + np.array([0.0, 0.0, top + 1.0]),
               "PANELS ON THE OUTSIDE", BUYER)
    if p > 0.82:
        grown = soft_shell.growth_fraction(stack)
        _label(app, shift + np.array([0.0, 0.0, top + 1.0]),
               f"{stack} LAYERS  ·  CAP {grown * 100.0:.1f}% BIGGER", GREEN)
    if p > 0.90:
        soft = soft_shell.soft_shell(stack)
        _label(app, shift + np.array([0.0, -4.4, 0.6]),
               f"SHOWER CAP  ·  ${soft.cost:,.0f}", HOST)


def scene_quilt(app, opaque, transparent, p: float) -> None:
    """One quilted layer going on over the frame and under the cap.

    Recycled clothing, sewn by the owner. It is the cheapest thing in the
    building and the only insulation in it, which is worth seeing on its
    own before the cap covers it up.

    The two prices on screen are both true and mean different things: the
    quilt is fifty dollars and the layer costs sixty-nine, because a layer
    also buys the bigger cap that has to go over it. Shown together, and
    said, rather than left to look like a mistake.
    """
    import soft_shell

    shift = _shift(app)
    _ground(app, shift)
    up = np.array([0.0, 0.0, _base()])
    creator.draw(app, seed.pad(), offset=tuple(shift))
    creator.draw(app, seed.frame(), offset=tuple(shift + up))
    creator.draw(app, seed.cap(0, colour=PANEL_WOOD), offset=tuple(shift + up))
    # The layer arrives from above rather than fading in: it is a blanket,
    # and a blanket goes *over* something.
    drop = round((1.0 - ease_in_out(clamp((p - 0.08) / 0.38))) * 3.0, 2)
    if p > 0.08:
        creator.draw(app, seed.cap(1, alpha=0.95, colour=QUILT_RED,
                                   lift=drop),
                     offset=tuple(shift + up))
    # And the cap straps over the lot, which is what makes the layer
    # removable: the cap comes off and the quilt comes off with it.
    cap_drop = round((1.0 - ease_in_out(clamp((p - 0.58) / 0.26))) * 3.4, 2)
    if p > 0.58:
        creator.draw(app, seed.cap(1, alpha=0.52, colour=CAP_BLUE,
                                   extra_in=0.9, lift=cap_drop),
                     offset=tuple(shift + up))
    top = _base() + _apex()
    quilt = soft_shell.declared("blanket_quilt_usd_per_layer")
    marginal = soft_shell.soft_shell(1).cost - soft_shell.soft_shell(0).cost
    if 0.14 < p < 0.58:
        _label(app, shift + np.array([0.0, 0.0, top + drop + 0.9]),
               "ONE QUILTED LAYER", BUYER)
    if p > 0.62:
        _label(app, shift + np.array([0.0, 0.0, top + cap_drop + 0.9]),
               "THE CAP STRAPS OVER IT", HOST)
    if p > 0.34:
        _label(app, shift + np.array([0.0, -4.4, 1.9]),
               f"THE QUILT  ·  ${quilt:,.0f}", GREEN)
    if p > 0.46:
        _label(app, shift + np.array([0.0, -4.4, 1.2]),
               f"WITH THE BIGGER CAP  ·  ${marginal:,.0f}", GREEN)
    if p > 0.86:
        # The chapter says this out loud, so the picture should carry it.
        _label(app, shift + np.array([0.0, -4.4, 0.5]),
               "MOISTURE TRAP  ·  UNPROVEN", MUTED)


def scene_mast(app, opaque, transparent, p: float) -> None:
    """The mast, then the column round it, then the floor clamped to it.

    In the finished building the mast stands inside the column, which is the
    argument -- one penetration carrying the services and the structure
    both -- and also means it cannot be seen. So it goes up on its own
    first, gets its timber, and only then does the column arrive round it.
    """
    shift = _shift(app)
    _ground(app, shift)
    up = np.array([0.0, 0.0, _base()])
    creator.draw(app, seed.pad(), offset=tuple(shift))
    # Steel first, then the timber boxed round it, so the film shows which
    # of the two is carrying the load.
    clad = round(ease_in_out(clamp((p - 0.18) / 0.24)), 2)
    creator.draw(app, seed.mast(clad=clad), offset=tuple(shift + up))
    if p > 0.46:
        creator.draw(app, seed.core(), offset=tuple(shift + up))
    if p > 0.30:
        creator.draw(app, seed.frame(), offset=tuple(shift + up))
    # The floor is the upgrade and it arrives last, a bay at a time.
    if p > 0.58:
        reveal = round(clamp((p - 0.58) / 0.30), 2)
        creator.draw(app, seed.dome_floor(reveal),
                     offset=tuple(shift + up + np.array([0.0, 0.0, 0.06])))
    ring_z = _base() + seed_world.mast_top_m()
    if p > 0.10:
        _label(app, shift + np.array([0.0, 0.0, ring_z + 0.55]),
               "THE LIFTING RING", BUYER)
    if 0.24 < p < 0.62:
        _label(app, shift + np.array([0.0, 0.0, _base() + 1.55]),
               "STEEL INSIDE, TIMBER OUTSIDE", MUTED)
    if p > 0.66:
        _label(app, shift + np.array([0.0, -4.4, 2.3]),
               f"THE MAST  ·  ${seed_model.mast_group().cost:,.0f}", GREEN)
    if p > 0.76:
        _label(app, shift + np.array([0.0, -4.4, 1.2]),
               f"THE FLOOR, BOUGHT LATER  ·  "
               f"${seed_model.dome_floor_group().cost:,.0f}", HOST)


def scene_floating(app, opaque, transparent, p: float) -> None:
    """The dome hung between two trees on three cables.

    Saddles, not holes. The dome's own floor is what it stands on up there,
    which is why the previous chapter had to come first, and the pad stays
    on the ground because the pad is the host's.
    """
    shift = _shift(app)
    _ground(app, shift)
    radius = seed_world.footprint_radius_m("hemisphere")
    rise = round(ease_in_out(clamp((p - 0.28) / 0.44)) * 3.4, 2)
    creator.draw(app, seed.pad(), offset=tuple(shift))
    up = np.array([0.0, 0.0, _base() + rise])
    cable = round(clamp((p - 0.04) / 0.20), 2)
    creator.draw(app, seed.float_rig(cable=cable, hang=rise),
                 offset=tuple(shift + np.array([0.0, 0.0, _base()])))
    creator.draw(app, seed.mast(), offset=tuple(shift + up))
    # The column goes UP. It unbolts at the pad port and at the apex sleeve
    # and travels with the dome -- that is the modular argument the whole
    # film is built on, and leaving it out of this shot quietly contradicted
    # it. What was left standing on the pad was the host's metered pedestal,
    # which reads at this distance like the dome's services abandoned.
    creator.draw(app, seed.core(), offset=tuple(shift + up))
    creator.draw(app, seed.dome_floor(1.0),
                 offset=tuple(shift + up + np.array([0.0, 0.0, 0.06])))
    creator.draw(app, seed.frame(), offset=tuple(shift + up))
    creator.draw(app, seed.cap(0, alpha=0.72, colour=CAP_BLUE),
                 offset=tuple(shift + up))
    # The label goes on whichever tree reads as screen-left. Naming one of
    # them "the left tree" put it behind the worksheet panel, because which
    # side of the frame a world point lands on is the camera's business and
    # not the scene's.
    spots = seed_world.float_tree_positions(radius)
    leftward = _screen_left(app)
    near = max(spots, key=lambda s: float(np.dot(np.array([s[0], s[1], 0.0]),
                                                 leftward)))
    if p > 0.16:
        _label(app, shift + np.array([near[0], near[1], _base() + 5.4]),
               "SADDLES, NOT HOLES", BUYER)
    if p > 0.44:
        _label(app, shift + np.array([0.0, -4.6, 2.6]),
               f"THREE CABLES  ·  "
               f"${seed_model.suspension_group().cost:,.0f}", GREEN)
    if p > 0.60:
        _label(app, shift + np.array([0.0, -4.6, 1.9]),
               f"FRAME  ·  {seed_model.frame_weight_lb():,.0f} LB", HOST)
    if p > 0.70:
        # Said on the picture, because the one thing still standing down
        # there is the host's meter and it should not read as the dome's.
        _label(app, shift + np.array([radius * 0.55, radius * 0.55, 1.5]),
               "THE PAD AND ITS METER STAY", MUTED)
    if p > 0.78:
        # The one thing this chapter must not let the picture imply.
        _label(app, shift + np.array([0.0, -4.6, 1.2]),
               "NOT AN ENGINEERED STRUCTURE", MUTED)


def scene_secondary(app, opaque, transparent, p: float) -> None:
    """A row of the buildings a homestead actually wants second."""
    shift = _shift(app)
    _ground(app, shift)
    keys = ("gym", "studio", "guest", "workshop", "garage")
    radius = seed_world.footprint_radius_m("hemisphere")
    pitch = radius * 2.0 + 2.2
    start = -(len(keys) - 1) * 0.5 * pitch
    reveal = clamp(p * 1.5)
    for index, key in enumerate(keys):
        if reveal * len(keys) < index:
            continue
        spot = shift + np.array([start + index * pitch, 0.0, 0.0])
        creator.draw(app, seed.pad(), offset=tuple(spot))
        creator.draw(app, seed.dome(key, shell=False),
                     offset=tuple(spot + np.array([0.0, 0.0, _base()])))
        if p > 0.42:
            _label(app, spot + np.array([0.0, 0.0, _base() + _apex() + 1.0]),
                   seed_model.fitout(key).label.upper().replace(" SEED", ""),
                   BUYER)
    if p > 0.74:
        _label(app, shift + np.array([0.0, -radius * 2.4, 1.4]),
               "ONE FRAME, SIX BUILDINGS", GREEN)


SCENES: dict = {
    "sp_deck": scene_deck,
    "sp_slices": scene_slices,
    "sp_swap": scene_swap,
    "sp_secondary": scene_secondary,
    "sp_bay": scene_bay,
    "sp_duct": scene_duct,
    "sp_standing": scene_standing,
    "sp_frame": scene_frame,
    "sp_shell": scene_shell_on,
    "sp_cap": scene_cap,
    "sp_quilt": scene_quilt,
    "sp_mast": scene_mast,
    "sp_floating": scene_floating,
    "sp_core": scene_core,
    "sp_polyp": scene_polyp,
    "sp_move": scene_move,
    "sp_pad": scene_pad,
    "sp_close": scene_close,
}


# ----------------------------------------------------------------------
# Chapters
# ----------------------------------------------------------------------

def _math(slug: str, title: str, promise: str, narration, steps, duration,
          camera, stage: str) -> Chapter:
    return Chapter(slug, "00", title, promise, narration, steps, duration,
                   camera, stage, overlay="math")


CHAPTERS: tuple[Chapter, ...] = (
    Chapter(
        "open", "00", "A house you can take apart",
        "Under ten thousand at the floor. Two hundred and seventy-seven "
        "square feet.",
        ("This is a tiny house. It is nineteen feet across, it has two "
         "hundred and seventy-seven square feet of floor, and it comes apart "
         "into pieces a trailer can take. Under ten thousand dollars "
         "stripped to the bone, twelve as we would "
         "actually ship it.",
         "We are not selling you a finished home. We are selling you the "
         "part of a home that is hard to make -- and leaving you the part "
         "that is yours to decide.",
         "Everything you are about to see is drawn by the same solver that "
         "cuts the real thing, and every number in it comes off the same "
         "model. There is no second set of figures for the brochure."),
        (), 22.0, (42.0, 13.0, 12.0), "sp_standing"),
    _math(
        "declared", "What was typed in, before anything is claimed",
        "Quantities are measured. Prices are assumptions. Kept apart.",
        ("Before a single dollar: this film has two kinds of number in it, "
         "and it is going to keep them in separate boxes the whole way "
         "through.",
         "The measured ones come off the dome's own geometry. How many "
         "members, how much panel, how much floor. Those cannot be argued "
         "with, because the same code that reports them cuts the wood.",
         "The declared ones are prices and rates. A person typed those in. "
         "They live in one table with a unit and a reason on every line, and "
         "a good number of them are lifted straight off a supplier's own "
         "published list.",
         "If you change one, everything after it moves, because this film "
         "reads the table rather than repeating what it said last time."),
        steps_declared(), 26.0, (48.0, 15.0, 13.5), "sp_standing"),
    Chapter(
        "frame", "00", "The frame is already on your land",
        "A trunk split like a cake takes 88% of it. Milling takes 45%.",
        ("Start with the frame, because the frame is the part we do not "
         "ship.",
         "A trunk gets split like a cake into eight wedges, and each wedge "
         "is used exactly as it comes off the saw. No squaring, no edging, "
         "no planing -- and that is not a shortcut, it is the reason this "
         "works. Squaring a round log means throwing the round part away. "
         "Split into wedges, you take about eighty-eight percent of the "
         "trunk. Milled into two-by-fours, you take about forty-five. Same "
         "tree, nearly twice the building.",
         "And a wedge is a triangle in section, so when two of them meet at "
         "a seam they leave a channel. Not a gap to be filled -- a channel, "
         "running the length of every seam in the building, to every "
         "vertex, with nobody routing it.",
         "That channel carries the services. Electrical, water, air. Which "
         "means something quietly enormous on a building site: you always "
         "know where the lines are. They are in the corners of the seams "
         "and nowhere else. Everybody who ever works on this dome knows the "
         "one place not to put a drill."),
        (), 30.0, (28.0, 12.0, 11.0), "sp_frame"),
    _math(
        "frame_cost", "What that is worth, and what it costs",
        "The wood was never the expensive part. Here is the proof.",
        ("Here is the part that surprised us.",
         "We built this model expecting the timber to be the big number. It "
         "is not. Buying that wood outright, at yard prices, is less than a "
         "hundred dollars. The shell over it is four thousand.",
         "So the trees are not really a saving on materials. What they save "
         "is a delivery and a mill bill, and what they buy you is a frame "
         "cut on the site it is going up on.",
         "And the joint has a price of its own, which we are going to put on "
         "screen rather than leave out: giving every triangle its own three "
         "sticks, so no end is mitred, costs eighty percent more wood than "
         "sharing struts would. We think that trade is worth making. We are "
         "not going to pretend it is free."),
        steps_frame(), 30.0, (34.0, 14.0, 12.5), "sp_frame"),
    _math(
        "stemcell", "Why we call it a stem cell",
        "Forty identical openings that have not decided what they are yet.",
        ("So why call it a stem cell.",
         "Because a stem cell has not decided what it is yet, and neither "
         "has this frame. It is forty identical triangular openings. It "
         "does not know or care what is in one. A panel drops in and "
         "compression-fits against the wedge; lift it out and the opening "
         "is back.",
         "So the function of the building is a set of panels. Mirrors and "
         "deadening and it is a gym. Skylights and louvres and it is a "
         "workshop. Take three base bays out, put one wide opening across "
         "them, and it is a garage.",
         "Nothing structural is touched to do any of that. Which means this "
         "is not a building that has a use. It is a building that has a use "
         "*at the moment*, and can have a different one in an afternoon."),
        steps_stemcell(), 30.0, (34.0, 12.0, 11.5), "sp_swap"),
    _math(
        "bay", "What actually closes a triangle",
        "Inner panel, cavity, outer panel, shell. Nothing screwed down.",
        ("A wedge is not a rectangle, and that turns out to matter.",
         "Because its inward face stands proud of where the panel sits, "
         "every bay in this frame has a lip already cut into it. Not "
         "machined in -- left there, by the shape of a split log.",
         "So the wall goes together from the inside out. An inner panel "
         "drops onto that lip. Behind it is a cavity as deep as the member. "
         "An outer panel drops into the same bay from outside and "
         "compression-fits against the frame. Then the shell lands on the "
         "frame itself, not on any of it.",
         "Nothing in that stack is screwed to anything. The shape of the "
         "stick holds it, which means any of it can come out again."),
        steps_bay(), 30.0, (30.0, 18.0, 4.4), "sp_bay"),
    _math(
        "duct", "The gap nobody wanted",
        "Two sawn faces at an angle do not close flush. Good.",
        ("Here is the one that took us longest to see.",
         "Two flat sawn faces meeting at an angle do not close flush. Every "
         "other way of building a dome treats that as a defect and machines "
         "it out. Leave it, and what you have is a continuous channel "
         "running along every seam to every vertex of the building, three "
         "hundred feet of it, that nobody had to route.",
         "Cap it and it is a duct. Blow through it and no part of a wooden "
         "frame ever sits in damp air. Draw through it instead and what "
         "lands on the shell goes down the channels and into the tank under "
         "the floor, rather than looking for a way into a joint.",
         "We are not claiming this works yet. The channel is real and the "
         "arithmetic is real; the airflow is an experiment, and it is a good "
         "part of what we are asking to fund."),
        steps_duct(), 32.0, (48.0, 16.0, 13.5), "sp_duct"),
    Chapter(
        "shell", "00", "The shell is a boat hull",
        "Sheet core, glass, resin, gelcoat. A sixty-year-old trade.",
        ("Over the frame goes a shell, and the shell is where the money is.",
         "It is a wood-cored composite skin: sheet core, chopped strand mat, "
         "stitched biaxial cloth, laminating resin, gelcoat on the weather "
         "face. That is not an invention. That is how small boats have been "
         "built since the nineteen sixties, out of products you can order "
         "this afternoon.",
         "It latches to the pad with over-centre catches -- the kind that "
         "seal a preserving jar -- and it lifts off from a ring laminated "
         "into its own apex. Which is the part that makes this a house you "
         "can take apart rather than a house you can only knock down."),
        (), 28.0, (62.0, 15.0, 13.5), "sp_shell"),
    Chapter(
        "slices", "00", "The roof comes apart too",
        "Four slices, an S-lip seam, and a gasket in the return.",
        ("It does not come off in one piece, either, because one piece of "
         "this size needs a crane and a truck.",
         "It is moulded in four slices, like the segments of an orange. "
         "Where two of them meet there is a moulded S-lip: one slice's edge "
         "folds out, the next one's folds in, they hook into each other with "
         "a gasket in the return, and the latch pulls the joint shut. It is "
         "watertight because of the shape, not because of the sealant -- "
         "water has to travel uphill twice to get through an S.",
         "The same lip runs around the bottom and snaps onto the pad, so "
         "four pieces become one skin and the whole roof goes on a trailer.",
         "And here is the number that goes with that, because it is not the "
         "flattering one. A quarter of this shell weighs about four hundred "
         "and thirty pounds. That is not two people and a good lunch. That "
         "is four people, or the yard crane you have already seen, or eight "
         "slices instead of four -- which halves it to a bit over two "
         "hundred and costs you twice the seam. We would rather say that now "
         "than have you find it out on the day."),
        (), 30.0, (58.0, 16.0, 14.5), "sp_slices"),
    _math(
        "shell_cost", "Four ways to skin it, and what each one costs",
        "Priced by weight of glass and resin, the way a yard prices it.",
        ("So what does a hull skin cost?",
         "Glass and resin are sold by weight, not by the yard, and a "
         "laminate is specified as ounces of glass per square foot and a "
         "resin-to-glass ratio. The resin quantity falls out of the fabric. "
         "Price it any other way and you will be right about one schedule "
         "and wrong about every other one.",
         "Here are four systems anybody in the trade would recognise, over "
         "this dome's real area, at a supplier's published prices. The one "
         "we ship is the boatyard schedule: the cheapest resin anyone builds "
         "a hull out of, over mat and biaxial, with gelcoat on the outside.",
         "The lightest option is cheaper still. It is also a sheathing "
         "rather than a skin, and it will not take the same knock. That is a "
         "real trade and it is on the table so you can make it yourself."),
        steps_shell(), 32.0, (58.0, 14.0, 14.5), "sp_shell"),
    _math(
        "sheet", "A thing we found out the hard way",
        "No panel of this dome fits a four-foot sheet. Not in any rotation.",
        ("One finding, because it changed how the thing gets made.",
         "We assumed the core would be cut triangle by triangle out of "
         "ordinary four-by-eight sheet. It cannot be. A triangle cannot get "
         "narrower than its own shortest altitude no matter how you turn it, "
         "and both of this dome's triangles are wider than forty-eight "
         "inches.",
         "So the core is sheeted across the frame and the joints are taped, "
         "which is how a boat is built anyway. We would rather find that "
         "here, in a model, than halfway through a production run."),
        steps_sheet(), 24.0, (58.0, 14.0, 14.5), "sp_shell"),
    Chapter(
        "core", "00", "The top of the dome is a socket",
        "Power and water come up the middle and out through the apex.",
        ("Now the part the whole system hangs off.",
         "Power, water and drain arrive in the middle of the pad. They come "
         "up through the floor into a column that carries the shower, the "
         "sink, the drain and the outlets at working height. And then they "
         "keep going -- up past the ceiling, through a sleeve at the apex, "
         "and out.",
         "So the top of this dome is not a roof. It is a socket. A gasketed "
         "cap bolts down over it: meant to stay shut for years, meant to "
         "come off in ten minutes.",
         "Which means every service in the building is already on the "
         "outside of the weathertight surface before anybody has decided "
         "what to plug in."),
        (), 30.0, (24.0, 9.0, 6.6), "sp_core"),
    Chapter(
        "polyps", "00", "Everything else snaps onto the outside",
        "Fan, water heater, cooling, shower. None of them cut a new hole.",
        ("Under that cap, a line runs down the outside of the shell to a "
         "panel hanging off the rim.",
         "The panel sits outside the footprint -- it does not eat any of "
         "your two hundred and seventy-seven square feet -- and it reaches "
         "back in through one gasketed port. Modules snap into it. An "
         "exhaust fan. A tankless water heater. A cooling unit. A shower.",
         "The point is what does not happen. Adding a service to this "
         "building never cuts a new hole in a surface that was keeping the "
         "rain out. The hole already exists, it is at the top, and it has a "
         "cap on it."),
        (), 28.0, (36.0, 11.0, 10.5), "sp_polyp"),
    Chapter(
        "modular", "00", "The core moves to the next dome",
        "You buy the plumbing once. The shell is the thing that grows.",
        ("And because the services are a column rather than a system built "
         "into the walls, they come out.",
         "Unbolt it, cap the lines, crate it. It goes into the next dome. "
         "Outgrow this one, build a bigger frame, lift the core across, and "
         "the part you paid a plumber and an electrician for does not get "
         "bought twice.",
         "That is what we mean by modular, and we mean it literally. Not "
         "'our product has options'. The physical object comes out and goes "
         "into the next one."),
        (), 26.0, (76.0, 13.0, 19.0), "sp_move"),
    _math(
        "core_cost", "What buying it once is worth",
        "A fifth of the dome's materials, and it walks to the next build.",
        ("Put a number on it.",
         "The core -- the column, the manifold, the drain, the sub-panel, "
         "the light, the fan and the cooling unit -- is about a fifth of "
         "everything material in the dome.",
         "Moving it costs a couple of hundred dollars. Buying a second one "
         "costs what the first one cost. So every move is that difference, "
         "spent on a bigger shell instead of on the same plumbing again."),
        steps_core(), 25.0, (76.0, 13.0, 20.0), "sp_move"),
    _math(
        "layering", "It gets warmer every winter",
        "Lift the shell. Add a layer. Put the shell back.",
        ("The cavity ships empty, and that is on purpose.",
         "Because the shell comes off, insulation is not a thing you decide "
         "once at the factory. Lift it, lay in a quilted layer, put it back. "
         "Six hundred dollars, an afternoon, and the R-value of the building "
         "goes up. Do it again next season.",
         "People push back on this, so: put on seven t-shirts and tell me "
         "how cold you are. It is the same argument, and the fabric is a "
         "waste stream.",
         "A finished house does not get warmer every winter. This one does, "
         "for as long as somebody owns it and feels like it."),
        steps_layering(), 28.0, (62.0, 15.0, 13.5), "sp_shell"),
    _math(
        "system", "This only works as a system",
        "The landowner rents ground. You own the house. Nobody owns both.",
        ("Step back, because none of this makes sense as a product on its "
         "own.",
         "A landowner builds pads and rents them. That is passive income "
         "with no building to maintain -- nobody can wreck a house they are "
         "renting, because the house is not the landowner's. They own the "
         "ground and the hookups, and that is all.",
         "Which is exactly what lets a dome be sold for what a dome costs, "
         "instead of what a dome plus a foundation plus a piece of land "
         "costs. Nobody is buying all three at the same time.",
         "And the joining hardware is made to fit this dome and the next two "
         "sizes up. So when the time comes for a bigger one, the hardware "
         "goes up with you, and so does the utility core. It is a house that "
         "gets better instead of a house you finish paying for."),
        steps_system(), 32.0, (76.0, 13.0, 19.0), "sp_move"),
    Chapter(
        "pad", "00", "The ground is not ours and it is not yours",
        "The landowner builds the pad. It stays when the dome leaves.",
        ("Here is the half of tiny-house pricing that everybody adds "
         "together and should not.",
         "A dome needs somewhere to stand: a deck on blocks, a moisture "
         "barrier, a port for the services, a tank, some storage under the "
         "floor. That is the landowner's build. It happens once, it stays "
         "in the ground, and the next dome lands on the same port.",
         "We design to hook onto it. We do not sell it, and we do not put "
         "it in the price of the dome -- because if we did, you would be "
         "buying a deck every time you moved."),
        (), 26.0, (44.0, 22.0, 11.5), "sp_pad"),
    _math(
        "deck", "The platform, built one course at a time",
        "Piers, beams, joists, boards. A hundred and sixteen of them.",
        ("Before any of that lands anywhere, somebody builds the thing it "
         "lands on -- and this is the part people imagine is expensive.",
         "It is not. It is a list of boards. Gravel goes down and gets "
         "compacted. Precast piers sit on it. Doubled two-by-six beams go "
         "across the piers, joists across the beams at sixteen inches, and "
         "deck boards across the joists. Two coats of sealer and it is "
         "done. A hundred and sixteen boards, about three thousand dollars, "
         "and two people can do it in a weekend.",
         "And here is the part that surprised us when we costed it "
         "properly. A concrete slab is *cheaper* than this deck. Concrete "
         "is cheap by the yard and this is only a few yards; framing lumber "
         "is not cheap by the foot any more. Pouring a ring and framing the "
         "middle is more expensive than either.",
         "So we are not going to tell you wood is the cheap option, because "
         "it is not. Wood is the option that comes apart. Unbolt the piers "
         "and the ground goes back to being ground -- and that is the whole "
         "reason a pad is a reasonable thing to try instead of a foundation "
         "you are stuck with."),
        steps_deck(), 32.0, (42.0, 26.0, 11.0), "sp_deck"),
    _math(
        "pad_cost", "Whose bill is whose",
        "Seven thousand of ground. None of it in the dome's price.",
        ("The pad, line by line, on the landowner's side of the fence.",
         "It is not nothing. It is most of the price of a small car, and "
         "anybody telling a landowner that hosting is free has not built "
         "one.",
         "But it is built once and it is kept. Which is why the dome price "
         "you are about to see has no floor, no deck and no groundwork in "
         "it at all."),
        steps_pad(), 26.0, (44.0, 22.0, 12.5), "sp_pad"),
    _math(
        "price", "What one costs, line by line",
        "Materials, labour, overhead, margin. Nothing hidden in a lump.",
        ("So here is the whole thing.",
         "Frame, panels, shell, the utility core, the light and the cooling, "
         "one utility panel, and the hours it takes to make all of it. Then "
         "overhead, then a reserve against the ones that come back, then our "
         "margin.",
         "That is the number. It is a house, on a pad, for the price of a "
         "mid-range car -- and the pad is not in it, because the pad is not "
         "ours to sell."),
        steps_price(), 30.0, (42.0, 13.0, 12.5), "sp_standing"),
    _math(
        "ladder", "How far down it goes",
        "Every saving, one at a time, ranked. And the one that is not a saving.",
        ("How cheap can this get?",
         "Here is every lever we have, applied one at a time against that "
         "standard dome, ranked by what it is worth.",
         "One of them is marked, and it is marked because it is not a "
         "saving. Halving our margin lowers the price without making the "
         "dome any cheaper to build. It is us earning less. We put it in the "
         "same table so the two can never be quietly mixed up.",
         "Pull all of the real ones and the floor is sixteen thousand "
         "dollars, at about fifty-seven dollars a square foot."),
        steps_ladder(), 30.0, (42.0, 13.0, 12.5), "sp_standing"),
    _math(
        "against", "Three things this says against itself",
        "Ships with an empty cavity. Wastes wood. And the duct is unproven.",
        ("Three things we are going to say against our own pitch, because a "
         "proposal that only shows its good numbers is not a proposal.",
         "The cavity ships empty. Six hundred dollars and an afternoon buys "
         "a layer, and you can keep doing that for years -- but on day one "
         "this is a weathertight shell, not a winter house, and somebody has "
         "to do that work.",
         "The frame wastes wood. Eighty percent more stock than a dome that "
         "shares its struts. We think the joint is worth it; the arithmetic "
         "does not care what we think.",
         "And you may have noticed that sits awkwardly next to chapter "
         "three, where splitting a log took twice as much of the tree as "
         "milling it. Both are true, and they are about different things -- "
         "one is how much of a trunk you keep, the other is how many sticks "
         "the dome needs. Put them together and this frame takes about "
         "ninety-two percent of the trees a shared-strut dome built out of "
         "milled lumber would. It wins. It wins by eight percent, which is "
         "not a headline, and we are not going to pretend it is one.",
         "And the seam duct is not proven. The channel is real, the "
         "arithmetic is real, and the airflow is an experiment we are "
         "running rather than a result we are reporting. That is a good part "
         "of what the money is for.",
         "The prices, too, are ours. The quantities are measured off the "
         "geometry and we will stand behind those. The rates have a reason "
         "written next to every one of them, and the first useful thing a "
         "backer can do is argue with one."),
        steps_against(), 32.0, (42.0, 13.0, 12.5), "sp_standing"),
    _math(
        "paint", "Two things that multiply",
        "A dome has 41% less skin. The paint takes 15% off what is left.",
        ("Here is where the shape starts paying you back.",
         "A dome of this floor area has about forty-one percent less "
         "outside surface than a box with the same floor. Less skin to lose "
         "heat through in winter and less to gain it through in summer. "
         "That is free and it is already true.",
         "Now paint the weather face with one of the barium sulphate "
         "radiative coatings. Those reflect almost all of the sun and "
         "radiate heat straight out through the atmospheric window, which "
         "means a surface under a clear sky can sit *below* air "
         "temperature. On this shell that takes another fifteen percent off "
         "the cooling load.",
         "And those two multiply rather than add, because the second one "
         "works on what the first one left. Against a painted box of the "
         "same floor, this dome needs about half. Which is why the whole "
         "design cooling load of a two hundred and seventy-seven square "
         "foot house comes out under four thousand BTU an hour."),
        steps_paint(), 32.0, (62.0, 15.0, 13.5), "sp_standing"),
    _math(
        "solar", "Running it on nothing",
        "Eight hundred watts and a bank, against a measured draw.",
        ("If the envelope is that cheap to run, the off-grid arithmetic "
         "gets easy.",
         "And we are not going to size it against a guess. The draw here is "
         "this dome's own heating and cooling year out of the model you have "
         "been watching, plus the lights and the ceiling fan it ships with.",
         "Eight hundred watts of panel -- on the sunward bays, or up a mast "
         "beside the dome -- covers most of a day. A ten kilowatt hour bank "
         "carries it through a couple of days with no sun at all. The whole "
         "set is about five and a half thousand dollars.",
         "One honest note on that. Square solar cells waste the corners of a "
         "triangular bay; triangular cells are the obvious fix and they are "
         "not something you can order yet. And the brief asked for three "
         "thousand on the battery -- at kilowatt hours that is over a "
         "million dollars of cells and two years of autonomy, so almost "
         "certainly watt hours, or the inverter's rating, was what was "
         "meant."),
        steps_solar(), 32.0, (48.0, 16.0, 13.5), "sp_standing"),
    Chapter(
        "catalogue", "00", "The buildings a homestead wants second",
        "A gym. A study. A guest room. A workshop. A garage.",
        ("Last thing, and it is the one most people actually want first.",
         "Not everybody needs a house. Most people who would build one of "
         "these already have somewhere to live, and what they are short of "
         "is a second building. A gym that is not the spare bedroom. A "
         "study with a door that shuts. Somewhere for guests that is not "
         "your sofa. A workshop. A garage with one wide opening across "
         "three base bays.",
         "Every one of those is the same hundred and twenty members, the "
         "same pad, the same core and the same hardware. The difference is "
         "which panels are in the bays.",
         "And because it is panels, the building can change its mind. A "
         "nursery becomes a study becomes a guest room. The gym becomes the "
         "guest house when your parents visit. That is not a marketing "
         "line -- it is what happens when the wall is something that lifts "
         "out."),
        (), 30.0, (74.0, 16.0, 34.0), "sp_secondary"),
    _math(
        "seeds", "The catalogue, priced",
        "Six second buildings. The frame line never changes.",
        ("Every one of them, priced off the same model, cheapest first.",
         "Look at what does not move between them. The frame line is "
         "identical in all six, because the frame is identical in all six. "
         "The difference between a gym and a garage is which panels are in "
         "the bays.",
         "That is the manufacturing argument, and it is the whole reason "
         "any of this is affordable."),
        steps_seeds(), 28.0, (74.0, 16.0, 36.0), "sp_secondary"),
    _math(
        "cap", "The standard article wears a shower cap",
        "The cap replaces the hull and the bays, and it stacks hats.",
        ("We changed what goes over the frame.",
         "The standard article no longer ships the laminated hull. It ships "
         "a shower cap: wood panels, one membrane, quilted layers added over "
         "the years, and a rain-slick cap strapped over the lot.",
         "A cap is a bag, so the dome stacks hats. Each quilted layer gets a "
         "bigger cap, where a rigid hull fills its cavity and then it is "
         "done. The worksheet does the arithmetic.",
         "The hull does not go away. It becomes the upgrade -- the "
         "fifty-year option, sold to the buyer who wants it."),
        steps_hats(), 22.0, (58.0, 17.0, 13.0), "sp_cap"),
    _math(
        "quilt", "A $50 quilt, and a bigger cap for each",
        "Recycled clothing, quilted by the owner, into one layer under the cap.",
        ("The insulation is not a thing we sell you.",
         "Recycled clothing and thrift-store blankets, quilted by the owner "
         "into one monolithic layer. It goes over the frame, under the cap, "
         "and off when the cap is replaced.",
         "The worksheet prices a declared flat rate a layer, and shows what "
         "the same layer would cost yard-priced. The fabric is a waste "
         "stream.",
         "And the caveat, out loud: two impermeable layers with fabric "
         "between them is a moisture trap, and the seam duct is the unproven "
         "answer."),
        steps_quilt(), 22.0, (48.0, 14.0, 11.5), "sp_quilt"),
    _math(
        "mast", "A mast through the column, and a floor that comes later",
        "Steel where the strength is, wood everywhere else. The floor clamps on.",
        ("One more upgrade, and it changes what the dome can do.",
         "A mast runs through the utility column: steel core where the "
         "strength is, timber cladding everywhere else. Structure and "
         "services share one hole in the building.",
         "The dome's own floor is the upgrade, bought after the dome. A "
         "steel hub clamps the mast, radial spokes run to the base ring, and "
         "timber decking covers them.",
         "The apex lifting ring is the hoist point for the whole structure. "
         "What it weighs, and what the hoist is rated for, are the "
         "engineer's numbers, not ours."),
        steps_mast(), 20.0, (70.0, 12.0, 12.5), "sp_mast"),
    _math(
        "floating", "Hang it between two trees",
        "Three cables, three saddles, one winch. And an engineer first.",
        ("The floor is what makes this next part possible.",
         "Hang the dome between two trees. Three cables run from the apex "
         "hanger to tree saddles -- saddles, not holes -- and the brake "
         "winch does the hoisting. The dome's own floor hangs from the mast "
         "while it is up there.",
         "Say it plainly: this is a design possibility, not an engineered "
         "structure. The loads on the trees, the cables and the mast need an "
         "engineer before anyone stands under it."),
        steps_floating(), 20.0, (86.0, 11.0, 22.0), "sp_floating"),
    Chapter(
        "close", "00", "Bring your own ground",
        "Twelve thousand, forty-three dollars a square foot.",
        ("So: we make the stem cell. You build on it.",
         "The standard article wears a shower cap, and it lists at twelve "
         "thousand dollars. Ten thousand of that is what it costs us to "
         "build. Two thousand is our profit -- twenty percent, marked up on "
         "cost, and you can check it with a calculator.",
         "That is forty-three dollars a square foot of floor, and it does "
         "not include the ground. The pad is about six thousand and it is "
         "yours, or your host's, and we do not mark it up.",
         "The laminated hull, the fifty-year option, is twenty-one and a "
         "half thousand. The floor, the mast and the floating rig that turn "
         "the dome into something you can hang between two trees are another "
         "four thousand.",
         "Every figure in this film came out of a model you can run "
         "yourself, including the three that argue against us. If you think "
         "one of our prices is wrong, tell us which one. That is the most "
         "useful thing a backer can do."),
        (), 34.0, (36.0, 12.0, 11.5), "sp_close"),
)


CHAPTERS = tuple(
    replace(chapter, number=f"{index + 1:02d}")
    for index, chapter in enumerate(CHAPTERS)
)
"""Numbered after the fact, so reordering the film is moving one block of
text rather than renumbering nineteen of them by hand."""


# ----------------------------------------------------------------------
# Proof
# ----------------------------------------------------------------------

def validate_seed_pitch() -> None:
    """The film must be buildable, in order, with nothing asserted."""
    from . import seed_bridge

    validate_seed_facts()
    seed_bridge.validate_seed_bridge()

    assert len(CHAPTERS) >= 14, len(CHAPTERS)
    slugs = [chapter.slug for chapter in CHAPTERS]
    assert len(set(slugs)) == len(slugs), slugs

    for chapter in CHAPTERS:
        assert chapter.stage in SCENES, (chapter.slug, chapter.stage)
        assert chapter.narration, chapter.slug
        assert chapter.duration > 0.0
        assert len(chapter.camera) == 3
        if chapter.overlay == "math":
            assert chapter.equations, chapter.slug
        else:
            assert not chapter.equations, chapter.slug

    # The soft-shell chapters each get their own picture. They shipped once
    # pointing at the hull coming off by crane -- four chapters of narration
    # about a fabric cap, a quilt, a mast and a dome in two trees, played
    # over one frozen shot of a laminated shell labelled with its weight.
    # Nothing in the checks caught it, because every field was valid.
    own = {"cap": "sp_cap", "quilt": "sp_quilt", "mast": "sp_mast",
           "floating": "sp_floating"}
    by_slug = {chapter.slug: chapter for chapter in CHAPTERS}
    for slug, stage in own.items():
        assert slug in by_slug, f"{slug} chapter has gone"
        assert by_slug[slug].stage == stage, (
            f"the {slug} chapter is drawing {by_slug[slug].stage!r}; it needs "
            f"its own scene, not a borrowed one")
    borrowed = [chapter.slug for chapter in CHAPTERS
                if chapter.stage in own.values() and chapter.slug not in own]
    assert not borrowed, f"{borrowed} borrowed a soft-shell scene"

    # And every scene in the registry is on a chapter, so a painter cannot
    # be quietly orphaned by a retarget.
    staged = {chapter.stage for chapter in CHAPTERS}
    orphans = sorted(set(SCENES) - staged)
    assert not orphans, f"scenes nothing draws: {orphans}"

    # Every worksheet this module imports has to be on a chapter, or it is a
    # screen nobody will ever see.
    used = {tuple(chapter.equations) for chapter in CHAPTERS
            if chapter.equations}
    for name, builder in ALL_SCREENS:
        assert tuple(builder()) in used, f"{name} is not on any chapter"

    # Every scene has to be reachable.
    staged = {chapter.stage for chapter in CHAPTERS}
    assert staged == set(SCENES), set(SCENES) - staged

    # A pitch cut has to be long enough to make its case and short enough to
    # be watched. Both ends matter, and the upper one has moved: this is now
    # a full explainer rather than a pitch reel -- the frame, the bay, the
    # seam duct, the panels, the paint, the solar and the catalogue are each
    # a thing somebody asked to have explained, and the teaser that every
    # render now cuts is the short form.
    #
    # The written total is not the finished length. The exporter stretches
    # each chapter to fit its own narration, which adds about a quarter.
    total = sum(chapter.duration for chapter in CHAPTERS)
    assert 300.0 <= total <= 900.0, total

    # The film must never say a price the model does not currently give.
    # Every spoken figure that is supposed to be a price is listed here with
    # the model value it is standing in for, and checked against it. A
    # narration line is the one place in this repository where a number
    # cannot be interpolated, so it is the one place that needs a guard.
    priced = seed_model.quote()
    hard = seed_model.quote("stem_cell", shell="hard")
    _build, floor = seed_model.floor_price()
    upgrade = (seed_model.mast_group(priced.geometry).cost
               + seed_model.dome_floor_group(priced.geometry).cost
               + seed_model.suspension_group(priced.geometry).cost)
    # The ground is quoted separately and not marked up, so the close says
    # what it costs and the guard checks that it said the right thing.
    pad_cost = priced.find("pad").cost
    # Promises count as spoken: they are on screen under the picture for the
    # whole chapter, which is longer than the voice says anything.
    spoken = " ".join(" ".join(chapter.narration) + " " + chapter.promise
                      for chapter in CHAPTERS)
    assert "second set of figures" in spoken

    SPOKEN_PRICES = (
        # (what the voice says, the model figure, how far it may round)
        ("Under ten thousand at the floor", floor, 600.0),
        ("Under ten thousand dollars stripped to the bone", floor, 600.0),
        ("twelve as we would", priced.price, 600.0),
        ("twelve thousand dollars", priced.price, 600.0),
        ("Ten thousand of that is what it costs us to build",
         priced.cost_to_build, 400.0),
        ("Two thousand is our profit", priced.gross_profit, 400.0),
        ("forty-three dollars a square foot", priced.price_per_sqft, 3.0),
        ("twenty-one and a half thousand", hard.price, 600.0),
        ("another four thousand", upgrade, 400.0),
        ("The pad is about six thousand", pad_cost, 800.0),
    )
    WORDS = {
        "Under ten thousand at the floor": 9750.0,
        "Under ten thousand dollars stripped to the bone": 9750.0,
        "twelve as we would": 12000.0,
        "twelve thousand dollars": 12000.0,
        "Ten thousand of that is what it costs us to build": 10000.0,
        "Two thousand is our profit": 2000.0,
        "forty-three dollars a square foot": 43.0,
        "twenty-one and a half thousand": 21500.0,
        "another four thousand": 4000.0,
        "The pad is about six thousand": 6000.0,
    }
    for phrase, value, tolerance in SPOKEN_PRICES:
        assert phrase in spoken, f"the film no longer says {phrase!r}"
        assert abs(WORDS[phrase] - value) <= tolerance, (
            f"the voice says {phrase!r} but the model says "
            f"${value:,.0f}; re-word the narration or accept the drift")

    # What the dome breaks down into is a physical claim and it belongs to
    # the laminate, which has moved once already. A shell slice is the
    # heaviest piece there is, and the film is not allowed to imply it is
    # a two-person lift while the model says otherwise.
    _piece, piece_lb = seed_model.heaviest_piece()
    assert "four hundred and thirty pounds" in spoken.lower(), (
        "the film no longer says what a slice weighs")
    assert abs(430.0 - piece_lb) <= 25.0, (
        f"the voice says a slice is 430 lb; the model says {piece_lb:,.0f} lb")
    assert "two people can carry" not in spoken.lower(), (
        f"a slice is {piece_lb:,.0f} lb, which is not two people")

    # The findings chapter is where the two wood numbers meet, and the net
    # is small enough that rounding it the friendly way would be a lie.
    net = seed_model.trees_against_mitred()
    assert "ninety-two percent of the trees" in spoken.lower()
    assert "wins by eight percent" in spoken.lower()
    assert abs(92.0 - net * 100.0) <= 2.0, (
        f"the voice says 92%; the model says {net * 100:.1f}%")

    # A retired claim. The film used to sell the wedge cut on "no mitre
    # anywhere in the building", which is both a weaker reason than the real
    # one and, as chapter 21 admits, the thing that costs 81% more wood. The
    # reason to split a log is that you keep 88% of it instead of 45%. The
    # finding is allowed to name the mitre; the pitch is not allowed to sell
    # on it.
    pitch = " ".join(" ".join(chapter.narration) + " " + chapter.promise
                     + " " + chapter.title
                     for chapter in CHAPTERS if chapter.slug != "against")
    for phrase in ("no mitre anywhere", "not a mitre anywhere",
                   "without a single mitre"):
        assert phrase not in pitch.lower(), (
            f"{phrase!r} is a retired claim; the reason is the harvest")

    # And the reason that replaced it has to actually be on screen, with the
    # numbers the model gives rather than remembered ones.
    cut = seed_model.harvest()
    assert f"{cut.wedge_recovery * 100:.0f}" in " ".join(steps_frame())
    for spelled, said, measured in (
            ("eighty-eight percent", 88.0, cut.wedge_recovery),
            ("forty-five", 45.0, cut.dimensional_recovery)):
        assert spelled in pitch.lower(), f"the film no longer says {spelled!r}"
        assert abs(said - measured * 100.0) <= 3.0, (
            f"the voice says {spelled!r} but the model measures "
            f"{measured * 100:.1f}%")

    # The band moved when the quote stopped billing 75 hours of laminate
    # lay-up for a dome that wears a fabric cap, and again when the price
    # became a 20 per cent markup on cost rather than a 35 per cent margin
    # on price. It is a band rather than a figure so a price change moves
    # the film without breaking it, and a price *collapse* still does.
    assert 9000.0 <= priced.price <= 50000.0, priced.price


SEED_PITCH_LESSON = Lesson(
    key="seed_pitch",
    brand="THE STEM CELL DOME / CAMPAIGN",
    title="A house you can take apart",
    chapters=CHAPTERS,
    scenes=SCENES,
    selftest=validate_seed_pitch,
    report=seed_film_report,
    snapshot_prefix="seedpitch",
    style="hype",
    voice_rate="+2%",
    label_layout="declutter",
    ground="off",
)


if __name__ == "__main__":
    validate_seed_pitch()
    total = sum(chapter.duration for chapter in CHAPTERS)
    print(f"seed pitch ok: {len(CHAPTERS)} chapters, {total / 60.0:.1f} min")
