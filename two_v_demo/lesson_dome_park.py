"""Dome Park: an RV park for houses, and the arithmetic on both sides of it.

The idea, in one sentence: a landowner builds a serviced pad, a dome owner
brings the house and plugs in.  Neither party owns a building the other lives
in, which is the part of every existing arrangement that hurts.

This film has to persuade two different people at once, and they want opposite
things, so the screen says which side it is talking about at all times: the
**host** is amber and the **tenant** is cyan.  Nothing is asserted for either
of them.  Every pad, dome and hookup on screen is drawn by the Dome Creator's
own renderer through :mod:`two_v_demo.park_bridge`, and every figure comes from
:mod:`park_model` -- including the several that argue against the pitch, which
are on camera because a proposal that only shows its good numbers is not a
proposal.

The spine of the argument:

1. what a pad is, built one step at a time
2. what it costs the host, what it returns, and where the short let beats it
3. the hinge -- a dome's foundation is between 8% and 63% of what it cost, and
   on a pad the tenant does not buy it
4. what a place to live costs four ways, and the month at which bringing your
   own home starts winning (it is not month one, and the film says so)
5. the dome the system assumes: one hardware set across sizes, a shell that
   comes off so the insulation can keep going up for as long as you own it
"""

from __future__ import annotations

import math
from dataclasses import replace
from functools import lru_cache

import numpy as np

import park_model
import park_world

from . import creator_bridge as creator
from . import park_bridge as park
from .lessons import Chapter, Lesson
from .park_facts import (
    ALL_SCREENS,
    HOME,
    foundation_showcase,
    home_pad,
    loaded_pad,
    park_film_report,
    steps_ask,
    steps_crossover,
    steps_declared,
    steps_exposure,
    steps_fit,
    steps_foundation,
    steps_hardware,
    steps_layers,
    steps_pad_cost,
    steps_solar,
    steps_stay,
    validate_park_facts,
)
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

FT_PER_M = 3.280839895

HOST = AMBER
"""Everything the pad owner pays for or earns."""

TENANT = CYAN
"""Everything the dome owner pays for or owns."""


def _rgb(colour) -> tuple[int, int, int]:
    return tuple(int(round(channel * 255)) for channel in colour[:3])


def _ft(metres: float) -> float:
    return metres * FT_PER_M


def _m(feet: float) -> float:
    return feet / FT_PER_M


# ----------------------------------------------------------------------
# The site this film is shot on
# ----------------------------------------------------------------------

FILM_PAD_SIZES = (40.0, 44.0, 48.0, 64.0)
"""Four of the six standard sizes, which is what a frame holds.

Not a smaller park because a smaller park is the plan: the renderer's far
plane is 120 metres and a camera far enough back to hold all six standard
pads in one shot would be pushing the ground disc through it.  The chapter
that counts pad sizes counts all six; the one that photographs them shows
four."""

GROUND_RADIUS = 46.0
"""How far the graded field runs, in metres. See above."""


@lru_cache(maxsize=1)
def film_park() -> park_world.Park:
    """The park this film is shot on: four pads, staggered, on open ground.

    Laid out here rather than taken from :func:`park_world.default_park`
    because that one is the tool's demo site and is deliberately too big to
    photograph.  The pads themselves, their costs and the domes that fit them
    are the model's, unchanged.
    """
    catalogue = {dome.name: dome for dome in park_model.dome_catalogue()}
    placements: list[park_world.Placed] = []
    cursor = 0.0
    for index, size_ft in enumerate(FILM_PAD_SIZES):
        radius = _m(size_ft) / 2.0
        cursor += radius
        fits = park_model.domes_that_fit(size_ft)
        # The biggest thing that fits, so each pad is shown doing its job.
        chosen = max(fits, key=lambda dome: dome.floor_sqft) if fits else None
        # One pad stands empty. A park with no vacancy has nothing to lease,
        # and the pitch is asking people to come and lease one.
        vacant = index == 1
        pad_spec = park_model.Pad(
            diameter_ft=size_ft,
            deck="gravel",
            rotating=True,
            utility_column=(index % 2 == 0),
            solar_watts=(park_model.solar_watts_for(chosen)
                         if chosen is not None and not vacant else 0.0),
        )
        placements.append(park_world.Placed(
            pad=pad_spec,
            origin=(cursor, 3.0 if index % 2 else -3.0),
            dome="" if vacant or chosen is None else chosen.name,
            heading_deg=20.0 + index * 18.0,
        ))
        cursor += radius + 2.4
    span = cursor - 2.4
    for placed in placements:
        placed.origin = (placed.origin[0] - span / 2.0, placed.origin[1])
    assert catalogue  # the layout is only meaningful against the catalogue
    return park_world.Park(
        placements=placements,
        bathhouse=(-span * 0.34, -21.0),
        service_point=(span * 0.22, 19.0),
        ground_radius=GROUND_RADIUS,
    )


@lru_cache(maxsize=1)
def film_park_span() -> float:
    park_site = film_park()
    return max(abs(p.origin[0]) + p.radius_m for p in park_site.placements) * 2.0


# ----------------------------------------------------------------------
# Composition helpers
# ----------------------------------------------------------------------

def _screen_left(app) -> np.ndarray:
    """The world direction that reads as leftward at this chapter's camera."""
    yaw = math.radians(float(getattr(app, "camera_yaw", 90.0)))
    return np.array([math.sin(yaw), -math.cos(yaw), 0.0])


def _shift(app) -> np.ndarray:
    """Where this chapter's subject stands, given what the overlay is using.

    A math chapter spends the right 42% of the frame on its worksheet, so a
    stage composed for the whole frame comes back cut down the middle.  The
    same move :mod:`two_v_demo.lesson_all_domes` makes, for the same reason:
    slide by a share of the camera's own distance, so one rule holds at every
    shot rather than needing a hand-set offset per chapter.
    """
    chapters = getattr(app, "chapters", None)
    index = getattr(app, "chapter_index", None)
    if not chapters or index is None:
        return np.zeros(3)
    if (chapters[index].overlay or "") != "math":
        return np.zeros(3)
    distance = float(getattr(app, "camera_distance", 40.0))
    return _screen_left(app) * distance * 0.27


def _label(app, point, text: str, colour) -> None:
    if text:
        app.world_labels.append(
            WorldLabel(np.asarray(point, dtype=np.float32), text,
                       _rgb(colour)))


def _draw_pad(app, placed: park_world.Placed, *, shift=None,
              stage: int | None = None, heading: float | None = None,
              lift: float = 0.0) -> None:
    """One pad where it stands, with whatever is parked on it."""
    shift = np.zeros(3) if shift is None else np.asarray(shift)
    base = np.array([placed.origin[0], placed.origin[1], 0.0]) + shift
    aim = placed.heading_deg if heading is None else heading
    creator.draw(app, park.pad(placed.pad, occupied=placed.occupied,
                               stage=stage, heading=aim),
                 offset=tuple(base))
    if placed.occupied and (stage is None or stage >= 1):
        top = base + np.array([0.0, 0.0, placed.dome_base_z + lift])
        creator.draw(app, park.dome_on_pad(placed.dome), offset=tuple(top),
                     yaw=aim)


def _pad_apex(placed: park_world.Placed) -> float:
    """How high the tallest thing on this pad reaches, for hanging a label."""
    if not placed.occupied:
        return placed.dome_base_z + 1.2
    return placed.dome_base_z + park.dome_on_pad(placed.dome).apex


# ----------------------------------------------------------------------
# The park
# ----------------------------------------------------------------------

MATH_FOCUS = slice(1, 3)
"""Which pads a worksheet chapter looks at.

A sixty-seven metre row will not fit beside a panel that takes the right 42%
of the frame: at any camera far enough to hold it, the row is a smear, and at
any camera close enough to read it, both ends are cut off and so are their
labels.  So a worksheet chapter looks at part of the park -- the vacant pad and
the one next to it -- re-centred on what it is showing.  The whole row is
established full-frame in the opening chapter and again at the close."""


def scene_site(app, opaque, transparent, p: float) -> None:
    """The whole park: ground, trunk services, pads, and what is parked."""
    shift = _shift(app)
    site = film_park()
    shown = site.placements
    if shift.any():
        shown = site.placements[MATH_FOCUS]
        # Re-centre on what is actually being shown, or the subset sits off
        # to one side of the frame the worksheet left for it.
        middle = sum(placed.origin[0] for placed in shown) / len(shown)
        shift = shift - np.array([middle, 0.0, 0.0])
    creator.draw(app, park.field(), offset=tuple(shift))
    creator.draw(app, park.site(site, ground=False), offset=tuple(shift))
    reveal = clamp(p * 1.6)
    count = len(shown)
    for index, placed in enumerate(shown):
        grown = clamp(reveal * (count + 1.0) - index * 0.8)
        if grown <= 0.02:
            continue
        _draw_pad(app, placed, shift=shift)
        if p < 0.35:
            continue
        point = np.array([placed.origin[0], placed.origin[1],
                          _pad_apex(placed) + 1.6]) + shift
        if placed.occupied:
            _label(app, point,
                   f"{placed.pad.diameter_ft:.0f} FT PAD  ·  LEASED", HOST)
            _label(app, point - np.array([0.0, 0.0, 1.3]),
                   placed.dome.upper(), TENANT)
        else:
            _label(app, point, f"{placed.pad.diameter_ft:.0f} FT PAD  ·  "
                               f"VACANT", MUTED)


def scene_legend(app, opaque, transparent, p: float) -> None:
    """The park, with the film's two colours explained on it once."""
    scene_site(app, opaque, transparent, min(p, 0.34))
    site = film_park()
    leased = next(placed for placed in site.placements if placed.occupied)
    base = np.array([leased.origin[0], leased.origin[1], 0.0])
    if p > 0.3:
        _label(app, base + np.array([0.0, 0.0, 0.9]),
               "THE HOST OWNS THIS", HOST)
    if p > 0.55:
        _label(app, base + np.array([0.0, 0.0, _pad_apex(leased) * 0.62]),
               "THE TENANT OWNS THIS", TENANT)
    if p > 0.75:
        _label(app, np.array([0.0, 0.0, 13.0]),
               "AND NEITHER OWNS THE OTHER'S", WHITE)


def scene_network(app, opaque, transparent, p: float) -> None:
    """More pads than a frame needs, which is the whole point of a network."""
    creator.draw(app, park.field())
    spec = park_model.Pad(diameter_ft=44.0, deck="gravel", rotating=True)
    catalogue = [dome for dome in park_model.dome_catalogue()
                 if dome.pad_diameter_ft <= 44.0]
    rows, columns = 3, 5
    step = _m(58.0)
    grown = clamp(p * 1.25)
    for row in range(rows):
        for column in range(columns):
            index = row * columns + column
            if index / (rows * columns) > grown:
                continue
            x = (column - (columns - 1) / 2.0) * step
            y = (row - (rows - 1) / 2.0) * step
            occupied = index % 4 != 3
            # Drawn at true size on purpose. Scaling a pad down brings its
            # deck to within a few centimetres of the ground, and at this
            # camera the two fight for the depth buffer -- which films as a
            # site drawn in horizontal stripes.
            creator.draw(app, park.pad(spec, occupied=occupied),
                         offset=(x, y, 0.0))
            if occupied:
                dome = catalogue[index % len(catalogue)]
                creator.draw(app, park.dome_on_pad(dome.name),
                             offset=(x, y, park.dome_lift(spec)),
                             yaw=index * 23.0)
    if p > 0.5:
        leased = sum(1 for index in range(rows * columns) if index % 4 != 3)
        _label(app, np.array([0.0, 0.0, 16.0]),
               f"{rows * columns} PADS  ·  {leased} LEASED  ·  ONE SITE", WHITE)
        _label(app, np.array([0.0, 0.0, 13.6]),
               "every dome on this field belongs to the person inside it",
               MUTED)


# ----------------------------------------------------------------------
# One pad, close up
# ----------------------------------------------------------------------

def scene_pad_build(app, opaque, transparent, p: float) -> None:
    """A pad assembling itself, in the order it would actually be built."""
    spec = loaded_pad()
    placed = park_world.Placed(pad=spec, origin=(0.0, 0.0), dome="",
                               heading_deg=35.0)
    stage = park.pad_stage_at(clamp(p * 1.05))
    shift = _shift(app)
    creator.draw(app, park.field(), offset=tuple(shift))
    # Stage zero is graded ground, which is a real step and draws nothing.
    # It still gets its caption -- the frame is the site before the pad --
    # but it must not be handed over as geometry.
    if stage >= 1:
        _draw_pad(app, placed, shift=shift, stage=stage)
    top = np.array([0.0, 0.0, 3.3]) + shift
    _label(app, top, park.PAD_STAGES[stage].upper(), HOST)
    _label(app, top - np.array([0.0, 0.0, 1.2]),
           f"step {stage + 1} of {len(park.PAD_STAGES)}", MUTED)
    if stage >= len(park.PAD_STAGES) - 1:
        _label(app, top - np.array([0.0, 0.0, 2.4]),
               f"{spec.diameter_ft:.0f} FT  ·  ${spec.build_cost:,.0f} TO BUILD",
               GREEN)


def scene_pad_detail(app, opaque, transparent, p: float) -> None:
    """The finished pad, labelled part by part."""
    spec = loaded_pad()
    placed = park_world.Placed(pad=spec, origin=(0.0, 0.0), dome="",
                               heading_deg=35.0)
    shift = _shift(app)
    creator.draw(app, park.field(), offset=tuple(shift))
    _draw_pad(app, placed, shift=shift)
    radius = placed.radius_m
    parts = (
        (0.30, (0.0, 0.0, 1.5), "POWER, WATER, DRAIN\nUP THE MIDDLE", HOST),
        (0.48, (-radius * 0.78, radius * 0.34, 1.9), "METERED PEDESTAL", HOST),
        (0.64, (radius * 0.42, -radius * 0.42, 3.0), "UTILITY COLUMN", HOST),
        (0.80, (0.0, -radius * 1.02, 0.9), "ACCEPTOR RIM", HOST),
    )
    for threshold, point, text, colour in parts:
        if p > threshold:
            _label(app, np.asarray(point) + shift, text, colour)


def scene_landing(app, opaque, transparent, p: float) -> None:
    """A dome coming down onto a pad. The pad is the floor."""
    spec = home_pad()
    placed = park_world.Placed(pad=spec, origin=(0.0, 0.0), dome=HOME,
                               heading_deg=20.0)
    shift = _shift(app)
    creator.draw(app, park.field(), offset=tuple(shift))
    drop = 1.0 - ease_in_out(clamp(p / 0.55))
    _draw_pad(app, placed, shift=shift, lift=drop * 9.0)
    top = np.array([0.0, 0.0, _pad_apex(placed) + drop * 9.0 + 1.7]) + shift
    _label(app, top, HOME.upper(), TENANT)
    if p > 0.6:
        _label(app, np.array([0.0, 0.0, 0.9]) + shift,
               f"{spec.diameter_ft:.0f} FT PAD  ·  THE FLOOR IS ALREADY HERE",
               HOST)
    if p > 0.78:
        _label(app, np.array([0.0, 0.0, -0.4]) + shift,
               "no slab poured, no footing dug, nothing left behind", MUTED)


def scene_two_sides(app, opaque, transparent, p: float) -> None:
    """One leased pad, with what each party paid for it."""
    spec = home_pad()
    placed = park_world.Placed(pad=spec, origin=(0.0, 0.0), dome=HOME,
                               heading_deg=20.0)
    shift = _shift(app)
    creator.draw(app, park.field(), offset=tuple(shift))
    _draw_pad(app, placed, shift=shift)
    building = park_model.on_pad(HOME)
    year = spec.year()
    if p > 0.18:
        # On the rim, not the middle. The middle of this pad is inside the
        # tenant's house, and the chapter is about the two being different
        # things owned by different people.
        _label(app, np.array([0.0, -placed.radius_m * 0.98, 0.9]) + shift,
               f"HOST: ${spec.build_cost:,.0f}\na deck and two hookups", HOST)
    if p > 0.42:
        _label(app, np.array([0.0, 0.0, _pad_apex(placed) * 0.70]) + shift,
               f"TENANT: ${building.on_pad_cost:,.0f}\nand it goes with them",
               TENANT)
    if p > 0.66:
        _label(app, np.array([0.0, 0.0, _pad_apex(placed) + 2.2]) + shift,
               f"${year['net']:,.0f} a year to the host  ·  "
               f"${spec.lease_per_month:,.0f} a month from the tenant", GREEN)
    if p > 0.84:
        _label(app, np.array([0.0, 0.0, -0.6]) + shift,
               "nothing on this pad can be wrecked by a tenant except "
               "the tenant's own house", MUTED)


# ----------------------------------------------------------------------
# The hinge: the ground
# ----------------------------------------------------------------------

def scene_foundation(app, opaque, transparent, p: float) -> None:
    """The same design twice: on its own foundation, and on a pad."""
    shift = _shift(app)
    gap = 11.0
    building = foundation_showcase()
    name = building.name
    spec = park_model.Pad(diameter_ft=park_model.pad_for(name), deck="gravel")

    left = np.array([gap, 0.0, 0.0]) + shift
    creator.draw(app, park.field(), offset=tuple(shift))
    creator.draw(app, park.dome_as_shipped(name), offset=tuple(left))
    shipped_apex = park.dome_as_shipped(name).apex
    _label(app, left + np.array([0.0, 0.0, shipped_apex + 1.6]),
           "ON ITS OWN GROUND", WHITE)
    if p > 0.25:
        _label(app, left + np.array([0.0, 0.0, shipped_apex + 0.2]),
               f"${building.full_cost:,.0f}\n"
               f"including ${building.foundation_cost:,.0f} of "
               f"{building.foundation_name.lower()}", MUTED)

    right = np.array([-gap, 0.0, 0.0]) + shift
    if p > 0.40:
        placed = park_world.Placed(pad=spec, origin=(-gap, 0.0), dome=name)
        _draw_pad(app, placed, shift=shift)
        apex = _pad_apex(placed)
        _label(app, right + np.array([0.0, 0.0, apex + 1.6]),
               "ON A PAD", TENANT)
        if p > 0.58:
            _label(app, right + np.array([0.0, 0.0, apex + 0.2]),
                   f"${building.on_pad_cost:,.0f}\nthe host already built "
                   f"the ground", TENANT)
    if p > 0.78:
        share = building.foundation_share * 100.0
        _label(app, np.asarray(shift) + np.array([0.0, 0.0, 13.0]),
               f"the same house, ${building.foundation_cost:,.0f} apart  "
               f"({share:.0f}% of it)", GREEN)


def scene_move(app, opaque, transparent, p: float) -> None:
    """Off one pad, across, onto the next. The whole nomad argument."""
    shift = _shift(app)
    spec = home_pad()
    left_x, right_x = 10.5, -10.5
    creator.draw(app, park.field(), offset=tuple(shift))
    for x in (left_x, right_x):
        placed = park_world.Placed(pad=spec, origin=(x, 0.0), dome="")
        _draw_pad(app, placed, shift=shift)

    lift = spec and park.dome_lift(spec)
    rise = ease_in_out(clamp(p / 0.28))
    travel = ease_in_out(clamp((p - 0.30) / 0.34))
    fall = ease_in_out(clamp((p - 0.66) / 0.28))
    height = lift + (3.4 * rise) - (3.4 * fall)
    x = left_x + (right_x - left_x) * travel
    creator.draw(app, park.dome_on_pad(HOME), offset=(x + shift[0],
                                                      shift[1], height),
                 yaw=travel * 30.0)
    dome_apex = park.dome_on_pad(HOME).apex
    _label(app, np.array([x, 0.0, height + dome_apex + 1.6]) + shift,
           HOME.upper(), TENANT)
    if p > 0.34:
        _label(app, np.array([x, 0.0, height + dome_apex + 0.3]) + shift,
               f"${park_model.declared('dome_transport_usd'):,.0f} to move it",
               MUTED)
    if p > 0.80:
        _label(app, np.array([0.0, 0.0, 13.0]) + shift,
               "no lease broken, no deposit argued over, nothing "
               "left behind", WHITE)


# ----------------------------------------------------------------------
# The dome the system assumes
# ----------------------------------------------------------------------

def scene_hardware(app, opaque, transparent, p: float) -> None:
    """One design at three radii, and the part list that does not move."""
    shift = _shift(app)
    rows = park_model.hardware_invariance()
    creator.draw(app, park.field(), offset=tuple(shift))
    cursor = 0.0
    laid: list[tuple[dict, float]] = []
    for row in rows:
        radius = row["diameter_ft"] / 2.0
        cursor += _m(radius) * 1.10
        laid.append((row, cursor))
        cursor += _m(radius) * 1.10
    span = cursor
    grown = clamp(p * 1.4)
    for index, (row, x) in enumerate(laid):
        if index / len(laid) > grown:
            continue
        config = dict(creator.presets_all()[0][1])
        config["radius"] = row["diameter_ft"] / 2.0 / FT_PER_M
        config["props"] = []
        build = creator.build(config, row["design"])
        point = np.array([span * 0.5 - x, 0.0, 0.0]) + shift
        creator.draw(app, build, offset=tuple(point))
        top = point + np.array([0.0, 0.0, build.apex + 1.5 +
                                (index % 2) * 1.2])
        _label(app, top, f"{row['diameter_ft']:.0f} FT  ·  "
                         f"{row['floor_sqft']:,.0f} SQ FT", TENANT)
        if p > 0.45:
            _label(app, top - np.array([0.0, 0.0, 1.15]),
                   f"{row['struts']} struts · {row['hubs']} hubs · "
                   f"{row['panels']} panels", WHITE)
        if p > 0.68:
            _label(app, top - np.array([0.0, 0.0, 2.3]),
                   f"hardware ${row['hub_cost']:,.0f}", GREEN)


def _layer_config(count: int) -> dict:
    """The flagship design wearing ``count`` cladding layers.

    The Creator models three cladding slots, and the film's argument runs to
    seven quilted layers.  So the picture shows what the tool can actually
    build -- a shell visibly thickening, layer by layer -- and the worksheet
    beside it carries the ladder past where the tool stops.  Saying which is
    which is the whole reason the two are on screen together.
    """
    config = dict(next(data for name, data in creator.presets_all()
                       if name == HOME))
    config["foundation"] = "Bare Ground"
    config["foundation_scale"] = 1.0
    stack = ["House Wrap", "Foam Insulation", "Cedar Shakes"]
    config["layers"] = [stack[index] if index < count else "None"
                        for index in range(3)]
    return config


def scene_layers(app, opaque, transparent, p: float) -> None:
    """The shell coming off, a layer going on, the shell going back."""
    shift = _shift(app)
    spec = home_pad()
    placed = park_world.Placed(pad=spec, origin=(0.0, 0.0), dome="",
                               heading_deg=20.0)
    creator.draw(app, park.field(), offset=tuple(shift))
    _draw_pad(app, placed, shift=shift)

    count = min(3, int(clamp(p * 1.08) * 4))
    build = creator.build(_layer_config(count), f"{HOME} +{count}")
    base = np.array([0.0, 0.0, placed.dome_base_z]) + shift
    creator.draw(app, build, offset=tuple(base), yaw=20.0)

    ladder = park_model.shell_ladder(HOME)
    step = ladder[min(count, len(ladder) - 1)]
    top = base + np.array([0.0, 0.0, build.apex + 1.7])
    _label(app, top, f"{count} LAYER{'S' if count != 1 else ''}  ·  "
                     f"R-{step.r_value:.1f}", TENANT)
    if p > 0.3:
        _label(app, top - np.array([0.0, 0.0, 1.25]),
               f"${step.heating_usd_per_year:,.0f} a year to heat", WHITE)
    if count >= 1 and p > 0.5:
        _label(app, top - np.array([0.0, 0.0, 2.5]),
               f"this layer paid for itself in "
               f"{step.marginal_payback_years * 12:.0f} months", GREEN)
    if p > 0.82:
        _label(app, base + np.array([0.0, 0.0, -1.0]),
               "the shell lifts off, the layer goes under it, "
               "the shell goes back", MUTED)


def _clad_config(layout) -> dict:
    """The flagship shell at the solar reference radius, clad one way.

    ``panel_overrides`` is the Dome Creator's own per-panel assignment, keyed
    by each face's normalised centroid, so "the top half" and "one side" are
    the actual panels the model selected rather than a texture standing in for
    them. Cladding layers come off: a layer sits *over* the panels, and the
    first cut of this chapter filmed solar cells underneath cedar shakes.
    """
    config = dict(next(data for name, data in creator.presets_all()
                       if name == HOME))
    config["foundation"] = "Bare Ground"
    config["foundation_scale"] = 1.0
    config["radius"] = park_model.SOLAR_RADIUS_FT / FT_PER_M
    config["layers"] = ["None", "None", "None"]
    # The floor comes out too. Three domes side by side is a comparison of
    # shells; a room full of furniture in each is noise.
    config["props"] = []
    config["panel_overrides"] = dict(layout.overrides)
    return config


def scene_solar(app, opaque, transparent, p: float) -> None:
    """Three ways to clad a shell, all turning on their pads."""
    shift = _shift(app)
    layouts = park_model.solar_layouts()
    spec = park_model.Pad(diameter_ft=park_model.declared("iris_max_ft"),
                          deck="wood", rotating=True)
    creator.draw(app, park.field(), offset=tuple(shift))
    aim = -55.0 + 110.0 * ease_in_out(clamp(p))
    lift = park.dome_lift(spec)
    gap = _m(spec.diameter_ft) * 1.16
    grown = clamp(p * 1.5)
    for index, layout in enumerate(layouts):
        if index / len(layouts) > grown:
            continue
        x = (1.0 - index) * gap
        base = np.array([x, 0.0, 0.0]) + shift
        creator.draw(app, park.pad(spec, occupied=True, heading=aim),
                     offset=tuple(base))
        build = creator.build(_clad_config(layout), f"clad {layout.name}")
        top = base + np.array([0.0, 0.0, lift])
        creator.draw(app, build, offset=tuple(top), yaw=aim)
        head = top + np.array([0.0, 0.0, build.apex + 1.5 +
                               (index % 2) * 1.1])
        _label(app, head, layout.name.upper(), TENANT)
        if p > 0.35:
            _label(app, head - np.array([0.0, 0.0, 1.1]),
                   f"{layout.panels} of {layout.of_panels} panels  ·  "
                   f"{layout.watts / 1000.0:,.1f} kW", WHITE)
        if p > 0.6:
            _label(app, head - np.array([0.0, 0.0, 2.2]),
                   f"tracking {layout.kwh_tracking:,.0f} kWh/mo", GREEN)
    if p > 0.8:
        _label(app, np.asarray(shift) + np.array([0.0, 0.0, 11.0]),
               f"all three on a {park_model.SOLAR_RADIUS_FT:.0f} ft radius "
               f"dome, on a {spec.diameter_ft:.0f} ft iris pad", MUTED)


def scene_shared(app, opaque, transparent, p: float) -> None:
    """The bathhouse, and two pads behind it."""
    shift = _shift(app)
    creator.draw(app, park.field(), offset=tuple(shift))
    creator.draw(app, park.bathhouse(), offset=tuple(shift))
    spec = park_model.Pad(diameter_ft=44.0, deck="gravel", rotating=True)
    catalogue = [dome for dome in park_model.dome_catalogue()
                 if dome.pad_diameter_ft <= 44.0]
    # Behind the bathhouse, on the far side of it from the camera. Put in
    # front they filled the foreground corners and got cut by the frame and
    # the title band; put out at the edges they left a shed alone in a field.
    for index, x in enumerate((-13.0, 13.0)):
        placed = park_world.Placed(
            pad=spec, origin=(x, -13.0),
            dome=catalogue[index % len(catalogue)].name,
            heading_deg=30.0 + index * 40.0)
        _draw_pad(app, placed, shift=shift)
    _label(app, np.array([0.0, 0.0, 5.2]) + shift, "SHARED BATHHOUSE", HOST)
    if p > 0.4:
        _label(app, np.array([0.0, 0.0, 3.9]) + shift,
               "so a dome need carry no plumbing at all", MUTED)
    if p > 0.7:
        _label(app, np.array([0.0, 0.0, 2.6]) + shift,
               f"or pay ${park_model.declared('utility_column_usd'):,.0f} "
               f"once for a column on the pad", MUTED)


SCENES: dict = {
    "dp_site": scene_site,
    "dp_legend": scene_legend,
    "dp_network": scene_network,
    "dp_pad_build": scene_pad_build,
    "dp_pad_detail": scene_pad_detail,
    "dp_landing": scene_landing,
    "dp_two_sides": scene_two_sides,
    "dp_foundation": scene_foundation,
    "dp_move": scene_move,
    "dp_hardware": scene_hardware,
    "dp_layers": scene_layers,
    "dp_solar": scene_solar,
    "dp_shared": scene_shared,
}


# ----------------------------------------------------------------------
# Chapters
# ----------------------------------------------------------------------

def _math(slug: str, title: str, promise: str, narration: tuple[str, ...],
          steps: tuple[str, ...], duration: float,
          camera: tuple[float, float, float], stage: str) -> Chapter:
    return Chapter(slug, "00", title, promise, narration, steps, duration,
                   camera, stage, "math")


CHAPTERS: tuple[Chapter, ...] = (
    Chapter(
        "open", "00", "An RV park, for houses",
        "Serviced pads. You bring the home.",
        ("Think of it as a fancier trailer park. Or better: a stationary RV "
         "park, where the thing you park is a house you built and can take "
         "apart again.",
         "A landowner builds a circular serviced pad. A dome owner arrives "
         "with their home, sets it down on the pad, and plugs in. The land, "
         "the power and the water are one person's business. The house "
         "standing on them is somebody else's.",
         "Everything you are about to see is drawn by the Dome Creator's own "
         "renderer, and every number comes off the same model the tool "
         "uses."),
        (), 22.0, (88.0, 15.0, 54.0), "dp_site"),
    Chapter(
        "legend", "00", "Two people, and what each of them owns",
        "Amber is the host. Cyan is the tenant. Nothing is shared.",
        ("There are two people in this network and they want opposite "
         "things, so this film keeps them in different colours the whole way "
         "through.",
         "Amber is the pad host: the deck, the trench, the pedestal, the "
         "meter. Cyan is the dome owner: the house, and everything they ever "
         "do to it.",
         "The single most important thing about that line is that it never "
         "moves. The host never owns a building somebody else is living in, "
         "and the tenant never pays rent on something that will never be "
         "theirs.",
         "Which means both sides keep control of their own half. Fewer things "
         "to argue about, because there are fewer things held in common. And "
         "an easy goodbye, which is worth more than people think: if it is "
         "not working, the dome leaves and the pad is exactly as it was."),
        (), 26.0, (80.0, 18.0, 42.0), "dp_legend"),
    _math(
        "declared", "What was typed in, before anything is claimed",
        "Prices are assumptions. Everything else is measured.",
        ("Before a single dollar figure: this film has two kinds of number in "
         "it and it is going to keep them apart.",
         "The prices, the rates and the occupancy were typed in by a person. "
         "They live in one table with a unit and a reason each, and they are "
         "the owner's working assumptions, not market research.",
         "Everything else -- which domes fit which pad, how much deck that "
         "is, how much shell can carry a panel -- is measured off the tool. "
         "Change a number in that table and every figure after it moves, "
         "because the film reads the table rather than repeating it."),
        steps_declared(), 25.0, (78.0, 18.0, 34.0), "dp_site"),
    Chapter(
        "pad_build", "00", "What a pad actually is",
        "A deck, a rim, a ring, and three pipes up the middle.",
        ("So what is a pad? Watch one get built.",
         "Graded ground. A deck -- gravel, concrete or timber, whatever the "
         "host wants to pay for. A wooden acceptor rim around the edge, which "
         "is the part a dome latches to and the reason this is a pad rather "
         "than a patio.",
         "That rim is not a fixed ring. It is an iris: leaves on a track "
         "that open and close like a camera aperture, so one pad takes a "
         "twenty foot dome or a forty foot one without being rebuilt. That "
         "is the whole reason a host can serve a range of domes with a "
         "single piece of hardware.",
         "Then a rotating base, if the host is building that kind. Then power, "
         "water and drain, arriving in the centre. Centre, not edge: the dome "
         "that lands here puts its floor on the pad, so the services have to "
         "come up inside the footprint or they cross the doorway.",
         "A utility column if the host wants one -- toilet, sink, shower "
         "head, outlets, drain. And a metered pedestal at the rim, which is "
         "how the host resells power and water."),
        (), 33.0, (52.0, 44.0, 20.0), "dp_pad_build"),
    Chapter(
        "landing", "00", "The pad is the floor",
        "Nothing is poured. Nothing is dug. Nothing is left behind.",
        ("And this is the move the whole idea turns on.",
         "The dome that arrives does not bring a foundation, because it does "
         "not need one. The pad is the floor. The deck it lands on is the "
         "deck it lives on, the services come up through the middle of it, "
         "and when the owner leaves, the pad is exactly as it was.",
         "No slab poured. No footing dug. No permit pulled for a structure "
         "that will be gone in a year.",
         "We already see dome rentals. They are cheaper to build than a "
         "house, and most glamping domes are, let us be honest, glorified "
         "tents. I do not think their value ever gets realised by renting "
         "them out a weekend at a time. But if a person owned their glorified "
         "tent, and rented the space to put it on instead -- now we are "
         "talking. Now both sides get something."),
        (), 27.0, (36.0, 20.0, 24.0), "dp_landing"),
    _math(
        "fit", "Which domes fit which pad",
        "Arithmetic off the catalogue, not a marketing table.",
        ("Pads come in sizes, and the sizes are not invented. Every design "
         "the Dome Creator ships has a foundation diameter the tool computes "
         "from its own geometry. Round each one up to the next four feet and "
         "you have the pad catalogue.",
         "Four foot steps because decking and ring stock come in even "
         "lengths, and because the second pad a host builds wants the first "
         "one's cut list.",
         "Add a bigger dome to the tool and a bigger pad size appears here on "
         "the next run. Nobody edits a list."),
        steps_fit(), 24.0, (76.0, 18.0, 34.0), "dp_site"),
    Chapter(
        "pad_detail", "00", "Everything the host is responsible for",
        "A deck, two hookups, and a meter. That is the whole exposure.",
        ("Look at what the host actually owns here, because it is a short "
         "list.",
         "A deck. A rim. Three pipes and a conduit. A pedestal with a meter "
         "in it. Maybe a ring and a column.",
         "And it does not have to be poured. The cheapest version that is "
         "still a serviced pad is a framed deck on precast blocks, with one "
         "power panel and water manifold in the middle of four domes instead "
         "of a pedestal and a trench for each. Nothing excavated, nothing "
         "poured.",
         "There is no kitchen to replace. No sofa to re-upholster. No "
         "flooring to pull up because a tenant's dog lived on it. The host's "
         "asset is a piece of civil engineering, and the thing most likely to "
         "damage it is weather."),
        (), 24.0, (28.0, 48.0, 18.0), "dp_pad_detail"),
    _math(
        "pad_cost", "What a pad costs, and what it returns",
        "Every line of it, including the ones people leave out.",
        ("Here is the build cost, line by line, for the smallest pad that "
         "takes a real house.",
         "Note the two lines that are usually missing from a pitch like this. "
         "Site infrastructure: something had to bring a road, a water main "
         "and a service drop to this spot, and that cost is real whether or "
         "not you count it. And permits.",
         "On the income side, the lease is most of it. The utility margin is "
         "a cent or two a unit -- that is payment for metering and paperwork, "
         "not a second rent, and it comes to about ten dollars a month.",
         "Payback is on net, after management, tax and insurance. Payback on "
         "gross is a brochure number."),
        steps_pad_cost(), 27.0, (30.0, 42.0, 20.0), "dp_pad_detail"),
    Chapter(
        "two_sides", "00", "The line that never moves",
        "The host's money is in the ground. The tenant's is in the house.",
        ("Two people, one pad, and a line between them that does not move.",
         "Below the line is the host's money, and it is in the ground. Above "
         "the line is the tenant's money, and it drives away with them.",
         "That is the arrangement, and it is the opposite of every other way "
         "people rent somewhere to live. A landlord's money is in the walls "
         "the tenant is living between. That is where the conflict comes "
         "from, every time."),
        (), 19.0, (44.0, 18.0, 24.0), "dp_two_sides"),
    _math(
        "exposure", "The host's side, against the obvious alternative",
        "Same land, same money, two very different yearly bills.",
        ("The honest comparison for a landowner is not against nothing. It is "
         "against furnishing a place and letting it out, which is what most "
         "people with a spare building actually do.",
         "So both columns carry the same management, the same tax, the same "
         "insurance. The short let then adds cleaning at every turnover, a "
         "damage reserve, a platform fee, and a renovation cycle -- several "
         "times the pad host's yearly bill, for ever.",
         "And now the figure that does not help us. A loaded pad -- rotating, "
         "plumbed, carrying an array -- costs more up front than a bare pad "
         "with a furnished let on it. On day one, the short let wins.",
         "The pad host's case was never that it is cheaper to start. It is "
         "that none of their yearly bill is wear on a building somebody else "
         "is living in."),
        steps_exposure(), 28.0, (48.0, 19.0, 25.0), "dp_two_sides"),
    Chapter(
        "foundation", "00", "The part of a house you never take with you",
        "The same dome, twice, with one difference underneath it.",
        ("Now the tenant's side, and it starts underground.",
         "On the left, the design as the Dome Creator ships it, standing on "
         "its own foundation. On the right, the same design on a pad, with "
         "that foundation taken out from under it -- because the pad is "
         "already there.",
         "It is the same house. The difference is the ground, and the ground "
         "is the one part of a building you can never take with you when you "
         "go."),
        (), 19.0, (72.0, 16.0, 32.0), "dp_foundation"),
    _math(
        "math_foundation", "What the ground is worth, per design",
        "Between eight and sixty three percent, measured.",
        ("This is not an estimate. Ask the Dome Creator for each design "
         "twice: once as shipped, and once with its foundation set to bare "
         "ground. The difference is exactly what the pad stands in for.",
         "Eight of the twelve shipped designs stand on something that costs "
         "real money, and for those the ground is between eight and sixty "
         "three percent of the build cost.",
         "The other four sit on grass, and for those the pad replaces "
         "nothing. That is worth saying out loud, because it is the limit of "
         "this argument: if your dome was going to sit on a lawn, a pad is "
         "not saving you a foundation. It is selling you services."),
        steps_foundation(), 26.0, (76.0, 17.0, 36.0), "dp_foundation"),
    _math(
        "stay", "Four ways to have a roof, for a year",
        "Hotel, short let, apartment, or your own dome on a pad.",
        ("Here is the comparison a person actually makes, and it is priced on "
         "one basis so it is a fair one.",
         "Every line carries power and water, because two of them include it "
         "in the nightly rate and quietly dropping it from the other two "
         "would rig the result.",
         "The dome line carries the two costs an ownership pitch usually "
         "hides: upkeep, and the return the money would have made if it were "
         "not sitting in a house. And it is worth less the day after you buy "
         "it, so a secondhand haircut comes off on day one.",
         "Even carrying all of that, a year in your own dome on a pad costs "
         "less than a year in the cheapest thing you could rent -- and at the "
         "end of it you still own the house."),
        steps_stay(), 28.0, (40.0, 19.0, 26.0), "dp_landing"),
    _math(
        "crossover", "How long you have to stay",
        "And the stay lengths where this is the wrong answer.",
        ("So how long does the stay have to be? Run those same four options "
         "at every length and find the month the dome stops being the "
         "expensive answer.",
         "Under that, this idea loses, and it should. Nobody should buy a "
         "house to stay somewhere for a month. A short let is the right "
         "answer and we are not going to pretend otherwise.",
         "Past it, the gap opens and never closes. That is the stay length "
         "neither a hotel nor a twelve month lease has ever served: too long "
         "to be a guest, too uncertain to sign for a year."),
        steps_crossover(), 26.0, (34.0, 20.0, 25.0), "dp_landing"),
    Chapter(
        "move", "00", "And when you want to be somewhere else",
        "Lift, drive, set down, plug in.",
        ("This is the part a lease cannot do at any price, and it is the "
         "word that describes the whole idea: semi-nomadic.",
         "Not a caravan you tow away on a whim. A house that comes apart. Two "
         "days at the quick end, two weeks for something large or heavily "
         "layered. That is a real burst of effort, and I am not going to "
         "pretend otherwise -- but it is a burst, not a condition. You spend "
         "it when a move is worth it, and the rest of the time you are simply "
         "living in a house.",
         "Off one pad, onto another. A different park, a different city, a "
         "different state. No lease broken, no deposit argued over, no "
         "walkthrough with somebody's clipboard, nothing left behind.",
         "And every improvement the owner has ever made goes with them. The "
         "money they spent is still theirs, standing on the next pad."),
        (), 31.0, (88.0, 20.0, 28.0), "dp_move"),
    Chapter(
        "hardware", "00", "One hardware set, any size of house",
        "Same design, three radii, one part list.",
        ("This is why the dome the system assumes is worth buying properly.",
         "Take one design and move a single slider: the radius. Everything "
         "else is held exactly where it was.",
         "Twenty feet across, thirty three feet across, fifty two feet "
         "across. Two hundred and ninety five square feet up to two thousand "
         "and ninety six. And the part list on the bench in front of you "
         "never changes."),
        (), 19.0, (82.0, 16.0, 36.0), "dp_hardware"),
    _math(
        "math_hardware", "What does not move when the house does",
        "The counts and the hub bill. Not the sticks and not the skin.",
        ("The counts are identical across all three: the same struts, the "
         "same hubs, the same panels. And the hub bill is identical too -- "
         "the same dollars at twenty feet as at fifty two.",
         "What does move is the stick and the skin, because those are priced "
         "by the metre and the square metre.",
         "Seven times the floor, off the same list of parts. That is what "
         "makes one good hardware set worth paying for: it is the part of the "
         "house that does not change when the house does, so it is the part "
         "you buy once and keep."),
        steps_hardware(), 25.0, (86.0, 17.0, 50.0), "dp_hardware"),
    Chapter(
        "layers", "00", "A house that gets warmer every winter",
        "The shell lifts off. A layer goes under it. The shell goes back.",
        ("I stood lookout outside the skin of a ship in the Arctic circle. "
         "There is exactly one way to stay warm out there: layers, on layers, "
         "on layers, and then a wind-breaking, water-tight suit over all of "
         "it. You end up looking like the Michelin man. You also stay alive.",
         "A dome with a removable shell can work the same way. Lift the "
         "shell, add a quilted layer -- including quilted recycled fabric, "
         "which is one of the largest waste streams there is -- and put the "
         "shell back over it.",
         "Which means R-value stops being a number somebody decided on the "
         "day the house was built."),
        (), 24.0, (34.0, 19.0, 25.0), "dp_layers"),
    _math(
        "math_layers", "What each layer is actually worth",
        "The first pays back in months. The seventh takes years.",
        ("The heat loss here is not this film's arithmetic. It is the same "
         "degree-day model the performance film uses, run on this dome's own "
         "shell area, with one declared R-value per quilted layer set "
         "deliberately under the published figure for cotton fibre.",
         "The first layer pays for itself in months. The seventh takes years. "
         "That is one over R, and it is precisely why deciding the whole "
         "R-value on day one is the wrong move: you add the layer that is "
         "worth adding this year, and the house gets warmer for as long as "
         "you own it.",
         "Two honest limits. Seven layers is a good wall, not a code-beating "
         "one. And this prices conduction only -- it does not price the "
         "windbreak, and the windbreak is what makes layers work. That is the "
         "shell's job, and it is the part of the Arctic argument this model "
         "cannot check."),
        steps_layers(), 29.0, (38.0, 20.0, 27.0), "dp_layers"),
    Chapter(
        "solar", "00", "The pad turns",
        "Panels on the shell, the deck aiming them.",
        ("A pad on a rotating base can aim whatever is standing on it. "
         "Everything in this chapter is a ten foot radius dome -- the medium, "
         "two person size -- because kilowatt hours a month mean nothing "
         "without the dome they came off.",
         "Three ways to clad it. One side, so the pad turns that side to the "
         "sun. The top half with a metal skirt below it, where the skirt is "
         "the rain catchment as well as the weather edge. Or the whole shell, "
         "which makes the most power and gives you the least reason to turn "
         "anything, because something is always facing the sun.",
         "The host bought the ring. The tenant bought the panels. Both of "
         "them are better off, which is the shape this whole arrangement "
         "keeps making."),
        (), 29.0, (90.0, 21.0, 40.0), "dp_solar"),
    _math(
        "math_solar", "What tracking is worth, and what it is not",
        "A quarter more power -- and far more than anyone can use.",
        ("Single axis tracking adds about a quarter over a fixed array, and "
         "on this dome that is several hundred kilowatt hours a month. The "
         "ring pays for itself off the difference.",
         "But here is the number that first made this model wrong. A dome's "
         "shell carries far more panel than the household inside it consumes "
         "-- several times more. The first version of this model valued every "
         "generated kilowatt hour at the retail price, which quietly assumed "
         "the tenant was buying power they would never have bought.",
         "So it does not any more. What displaces the tenant's own draw is "
         "worth retail; everything past it is worth export, which is about a "
         "third of that. Correcting it took this pad's solar income down by "
         "well over half.",
         "The ring is still worth fitting. But the real case for cladding a "
         "dome in cells is a park that can sell the surplus, not a tenant who "
         "cannot use it."),
        steps_solar(), 30.0, (86.0, 21.0, 46.0), "dp_solar"),
    Chapter(
        "shared", "00", "What the park provides so the dome does not have to",
        "A bathhouse, so a house need carry no plumbing at all.",
        ("Some of this can be shared, and that changes what a dome has to be.",
         "A bathhouse on the site means a dome owner can skip plumbing "
         "entirely, which is the single most expensive and most regulated "
         "thing in a small dwelling. Or the host fits a utility column on the "
         "pad -- toilet, sink, shower head, drain -- once, for every tenant "
         "who ever parks there.",
         "Either way it is bought once by the person who stays, and used by "
         "everyone who comes and goes.",
         "And note what a host is not obliged to do. Reselling power and "
         "water with a margin is one option, not the model. A host may simply "
         "pass the meter through. What a host is really competing on is the "
         "array of things a site offers, and the price they can ask follows "
         "from that."),
        (), 26.0, (90.0, 20.0, 26.0), "dp_shared"),
    Chapter(
        "network", "00", "Why this has to be a network",
        "One pad is a driveway. A thousand is somewhere to live.",
        ("The closest thing that exists is an RV park, and the comparison is "
         "worth making carefully. An RV park turns over in nights and weeks. "
         "A dome park turns over in seasons and years, because taking a dome "
         "down is a job rather than a decision. Same shape of arrangement, "
         "much longer clock.",
         "One host with one pad is a favour. What makes this worth building "
         "is the second host, and the third, and the four hundredth.",
         "For the dome owner, a network means choice: price, location, "
         "services, and the freedom to leave a bad host by driving away from "
         "them. For the pad host, it means a tenant pool that is not limited "
         "to whoever happens to be in town.",
         "And it means a dome has a resale market, which is the one "
         "assumption in this film doing the most work. A house you can sell "
         "is an asset. A house nobody will buy is a very expensive tent."),
        (), 30.0, (84.0, 30.0, 66.0), "dp_network"),
    _math(
        "ask", "What the first park costs to build",
        "Not a rendering. A pad count, a trench length and a bill.",
        ("The goal is a hundred thousand dollars. I think that is a modest "
         "number to strive for, and it is modest because the expensive parts "
         "are already mine: the land, and somewhere to work.",
         "What the money builds is one to three pads on that land, "
         "as a test group, and the pad architecture itself -- made "
         "repeatable, the way RV hookups are repeatable, so the second site "
         "is a cut list rather than an invention.",
         "Most of it goes into modular design and the means to do it: a "
         "full woodworking and metalworking shop for fabrication and "
         "experiment, a CNC laser, a router. One to three dome designs that "
         "actually suit this, built and measured.",
         "Then the web app and its hosting, and promotion -- real "
         "advertising, on every platform I can reach, because I want this "
         "idea to spread like something contagious rather than sit in a "
         "repository.",
         "A camera, because all of it gets published as it is made. Open "
         "source -- actual open source, not the kind where the word is doing "
         "marketing.",
         "What it does not buy is the tracking foundation. A pad that turns "
         "to follow the sun is a fine thing to own and I intend to build one, "
         "but it is whimsy on a first site and I am not spending anyone "
         "else's money on it."),
        steps_ask(), 40.0, (80.0, 18.0, 34.0), "dp_site"),
    Chapter(
        "close", "00", "Bring your own home",
        "The host keeps the land. You keep the house.",
        ("A hotel sells you a night. A short let sells you a fortnight. A "
         "lease sells you a year and charges you to leave early. None of them "
         "sells you the thing most people actually want, which is to live "
         "somewhere for a while without handing over the value of everything "
         "they do to the place while they are there.",
         "Bring your own home. Pay the host for the ground and the services. "
         "Improve your house as much as you like, because it is your house, "
         "and take every bit of that with you when you go.",
         "Nothing in this film was asserted. Every pad and every dome was "
         "drawn by the tool that designs them, every figure was computed by "
         "the model underneath it, and the numbers that argue against this "
         "idea are in here with the ones that argue for it. Come and check "
         "them.",
         "And one last thing, said plainly. If this campaign does not fund, "
         "my plan and my work are the same. I am building this whether it "
         "takes one year or ten. What a donation changes is the speed, and "
         "whether the drawings reach anybody else on the way."),
        (), 34.0, (88.0, 15.0, 54.0), "dp_site"),
)


CHAPTERS = tuple(
    replace(chapter, number=f"{index + 1:02d}")
    for index, chapter in enumerate(CHAPTERS)
)


# ----------------------------------------------------------------------
# Proof
# ----------------------------------------------------------------------

class _Probe:
    """Enough of the renderer for a painter to run against.

    It carries a chapter and a camera because the painters read both: where a
    subject stands depends on what the overlay is using, so a probe without
    them would test a composition the film never renders.
    """

    def __init__(self, overlay: str | None = None,
                 camera: tuple[float, float, float] = (62.0, 18.0, 40.0)
                 ) -> None:
        self.world_labels: list = []
        self.world_icons: list = []
        self.creator_draws: list = []
        self.chapter_index = 0
        self.chapters = (Chapter("probe", "00", "Probe", "Probe", ("probe",),
                                 (), 10.0, camera, "probe", overlay),)
        self.camera_yaw, self.camera_pitch, self.camera_distance = camera


def validate_dome_park() -> None:
    """Prove the film before it costs an evening of rendering."""
    from .render_kit import TriangleBatch

    validate_park_facts()

    lesson = DOME_PARK_LESSON
    slugs = [chapter.slug for chapter in lesson.chapters]
    assert len(set(slugs)) == len(slugs), "duplicate slug"
    for chapter in lesson.chapters:
        assert chapter.stage in lesson.scenes, (chapter.slug, chapter.stage)
        assert chapter.narration, chapter.slug
        if chapter.overlay == "math":
            assert len(chapter.equations) >= 6, chapter.slug

    # Every worksheet the facts module offers is used exactly once. A screen
    # written and then never cued is the easiest thing in the world to leave
    # behind, and it is invisible in the finished film.
    used = [chapter.equations for chapter in lesson.chapters
            if chapter.overlay == "math"]
    assert len(used) == len(set(used)), "a math screen is used twice"
    offered = {builder() for _name, builder in ALL_SCREENS}
    assert set(used) == offered, (
        f"{len(offered - set(used))} screens unused, "
        f"{len(set(used) - offered)} unknown")

    # Every painter has to put real geometry on the stage and label it, in
    # both the shapes a chapter can take.
    #
    # Zero is in this list because it was not, and a chapter whose first frame
    # handed over an empty build -- the first step of a pad's construction is
    # graded ground, which draws nothing -- took an export down forty minutes
    # in. Every chapter starts at zero; a proof that never looks there is
    # proving the wrong thing.
    for stage, painter in lesson.scenes.items():
        for progress in (0.0, 0.02, 0.2, 0.5, 0.85, 1.0):
            for overlay in (None, "math"):
                probe = _Probe(overlay)
                painter(probe, TriangleBatch(), TriangleBatch(), progress)
                assert probe.creator_draws, (stage, progress, overlay)
                for request in probe.creator_draws:
                    # moderngl refuses an empty vertex buffer, and the
                    # renderer now skips one rather than raising -- but a
                    # painter should not be offering one in the first place.
                    assert len(request.build.mesh.vertices), (
                        stage, progress, overlay, request.build.name)
                    assert request.build.triangles > 0, (
                        stage, request.build.name)
                for label in probe.world_labels:
                    assert label.text.strip(), (stage, progress, overlay)
        probe = _Probe()
        painter(probe, TriangleBatch(), TriangleBatch(), 1.0)
        assert probe.world_labels, f"{stage} never says anything"

    # The park this film is shot on has to be a legal park, not just a
    # pleasing arrangement: no pad may overlap another, every parked dome has
    # to fit the pad it stands on, and one pad has to be vacant.
    site = film_park()
    assert len(site.placements) == len(FILM_PAD_SIZES)
    assert 0 < site.occupied < len(site.placements), (
        "a park with no vacancy has nothing to lease")
    for first in range(len(site.placements)):
        for second in range(first + 1, len(site.placements)):
            one, two = site.placements[first], site.placements[second]
            gap = math.hypot(one.origin[0] - two.origin[0],
                             one.origin[1] - two.origin[1])
            assert gap > one.radius_m + two.radius_m, (first, second, gap)
    for placed in site.placements:
        if not placed.occupied:
            continue
        dome = next(d for d in park_model.dome_catalogue()
                    if d.name == placed.dome)
        assert dome.pad_diameter_ft <= placed.pad.diameter_ft + 1e-9, placed

    # The renderer's far plane is 120 metres. The backdrop field is meant to
    # run past it -- that is what puts a horizon in the frame -- but nothing
    # the film is *about* may fall outside it at the widest camera in the film.
    far = 120.0
    widest = max(chapter.camera[2] for chapter in lesson.chapters)
    reach = max(math.hypot(*placed.origin) + placed.radius_m
                for placed in site.placements)
    assert widest + reach < far * 0.92, (widest, reach)

    # The whole park has to be in frame at the establishing shot, or the
    # opening line is describing something the viewer cannot see. Half the
    # horizontal field at 48 degrees vertical on a 16:9 frame.
    half_field = math.tan(math.radians(48.0) / 2.0) * (16.0 / 9.0)
    opener = next(chapter for chapter in lesson.chapters
                  if chapter.slug == "open")
    assert film_park_span() / 2.0 < opener.camera[2] * half_field, (
        film_park_span(), opener.camera[2])

    # A dome on a pad must never bring its own foundation, on any painter.
    probe = _Probe()
    scene_site(probe, TriangleBatch(), TriangleBatch(), 1.0)
    for request in probe.creator_draws:
        model = request.build.model
        if model is not None:
            assert model.foundation.height == 0.0, request.build.name

    # The two-colour promise: the chapter that sets it up has to use both, and
    # the chapters about money have to use the colour of whoever's money it is.
    probe = _Probe()
    scene_legend(probe, TriangleBatch(), TriangleBatch(), 1.0)
    colours = {label.color for label in probe.world_labels}
    assert _rgb(HOST) in colours and _rgb(TENANT) in colours, colours

    # The solar chapter has to film a dome that is actually wearing solar.
    # A cladding layer sits *over* the panels, so leaving the flagship's cedar
    # shakes on produced a chapter about solar with no solar visible in it.
    layouts = park_model.solar_layouts()
    assert len(layouts) == 3, len(layouts)
    for layout in layouts:
        clad = _clad_config(layout)
        # A cladding layer sits over the panels, so leaving the flagship's
        # cedar shakes on filmed a solar chapter with no solar visible in it.
        assert set(clad["layers"]) == {"None"}, clad["layers"]
        assert clad["panel_overrides"], layout.name
        cells = sum(1 for v in clad["panel_overrides"].values()
                    if v == "Solar Panel")
        assert cells == layout.panels, (layout.name, cells, layout.panels)
    # The three have to actually differ, or the chapter shows one dome thrice.
    assert len({tuple(sorted(_clad_config(l)["panel_overrides"].items()))
                for l in layouts}) == 3
    assert layouts[-1].watts > layouts[0].watts * 1.8

    # Nothing may be drawn at a reduced scale sitting on the backdrop: a
    # scaled pad's deck lands within a few centimetres of the ground and the
    # two fight for the depth buffer, which films as horizontal stripes.
    for stage, painter in lesson.scenes.items():
        probe = _Probe()
        painter(probe, TriangleBatch(), TriangleBatch(), 1.0)
        for request in probe.creator_draws:
            assert abs(request.scale - 1.0) < 1e-9, (stage, request.scale)

    # The foundation chapter must photograph a design whose foundation is
    # worth photographing, and it must not be the one the tenant figures use
    # -- that one saves the least of any design that has a foundation.
    show = foundation_showcase()
    assert show.name != HOME, show.name
    assert show.foundation_share > park_model.on_pad(HOME).foundation_share


DOME_PARK_LESSON = Lesson(
    key="dome_park",
    brand="DOME PARK / BRING YOUR OWN HOME",
    title="Dome Park",
    chapters=CHAPTERS,
    scenes=SCENES,
    selftest=validate_dome_park,
    report=park_film_report,
    snapshot_prefix="domepark",
    style="hype",
    voice_rate="+2%",
    label_layout="declutter",
    ground="off",
)
