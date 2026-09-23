"""Pictures for the annotated Bring Your Own Dome cut.

The author's marked-up transcript asks for several things the first cut either
drew as a still or did not draw at all: a pad being built a step at a time, the
iris as a mechanism whose aperture actually changes, the service runs leaving
the centre of the floor and climbing the shell as veins, the standard pad
catalogue, and the line between the two people's money.

Everything here is the project's own geometry. Pads and the domes that stand
on them come from :mod:`park_bridge`, which carries the Dome Creator's meshes;
the wedge shell comes from :mod:`raw_wedge_bridge`, which carries the
simulator's solved article; and every size, price and span is read from
:mod:`park_model`. Nothing in this file decides a number.

The scene painters that already worked are imported from :mod:`byod_scenes`
rather than copied, so a fix to one is a fix to both.
"""
from __future__ import annotations

import math
from functools import lru_cache

import numpy as np
import park_model as pm
import park_world
from . import creator_bridge as creator, park_bridge as park, raw_wedge_bridge as wedge
from . import lesson_dome_park as old
from . import byod_scenes as base
from .render_kit import (
    AMBER,
    CYAN,
    GREEN,
    MUTED,
    RED,
    WHITE,
    clamp,
    ease_in_out,
)

FT_PER_M = pm.FT_PER_M

label = base.label
ring = base.ring

DECK_TINT = {
    "gravel": (0.55, 0.53, 0.50),
    "concrete": (0.62, 0.62, 0.61),
    "wood": (0.55, 0.38, 0.22),
}


# ----------------------------------------------------------------------
# The title
# ----------------------------------------------------------------------

def scene_title(app, opaque, transparent, p):
    """The park arriving under the title, with nothing else on the frame.

    The overlay owns this chapter: the statement, the brand and the strap are
    drawn in screen space by the renderer, and a world label underneath them
    would be a second caption arguing with the first. So the site is built and
    then every label the site painter hung off it is dropped.
    """
    old.scene_site(app, opaque, transparent, 0.20 + 0.60 * ease_in_out(p))
    app.world_labels.clear()


# ----------------------------------------------------------------------
# A side thought: storage
# ----------------------------------------------------------------------

@lru_cache(maxsize=1)
def storage_dome():
    """An insulated shell with no rooms in it, because nothing lives here.

    The same Creator that designs the houses designs this: hold every menu
    still, take the furniture and the partitions out, and put one insulating
    layer on. What makes it worth showing is that it stands on the same pad as
    everything else, which is the point of the aside rather than a claim about
    cold storage.
    """
    config = dict(creator.presets_all()[0][1])
    config.update(
        radius=16.0 / FT_PER_M,
        foundation="Bare Ground",
        foundation_scale=1.0,
        props=[],
        partitions="None",
        layers=["Foam Insulation", "None", "None"],
    )
    return creator.build(config, "storage shell")


def scene_storage(app, opaque, transparent, p):
    """A pad, an insulated dome on it, and goods going in and out."""
    # The Creator's field, or the shell hangs in a black void and reads as a
    # product render rather than as a building standing somewhere.
    creator.draw(app, park.field())
    old._draw_pad(app, park_world.Placed(
        pad=pm.Pad(diameter_ft=36.0, deck="concrete"), origin=(0.0, 0.0),
        dome="", heading_deg=0.0))
    build = storage_dome()
    lift = park.dome_lift(pm.Pad(diameter_ft=36.0, deck="concrete"))
    creator.draw(app, build, offset=(0.0, 0.0, lift))
    # Crates, so the frame says what the building is for. Stacked outside
    # rather than inside: an opaque shell has no interior to show.
    for index in range(5):
        stage = clamp(p * 1.7 - index * 0.16)
        if stage <= 0.0:
            continue
        x = -6.4 - index * 0.42
        opaque.box((x, 1.6 + (index % 2) * 0.9, 0.34 + stage * 0.5),
                   (1.15, 1.15, 0.9), (0.52, 0.38, 0.24, 1))
    apex = lift + build.apex
    label(app, (0, 0, apex + 1.9),
          "A DOME WITH NOTHING LIVING IN IT\n"
          "insulated shell, no rooms, no plumbing", CYAN)
    if p > 0.55:
        label(app, (0, -4.6, 1.2), "THE SAME PAD AS EVERYTHING ELSE", AMBER)
    if p > 0.78:
        label(app, (0, 0, -1.2),
              "a side thought, not a second business plan", MUTED)


# ----------------------------------------------------------------------
# What a pad is, and how one gets built
# ----------------------------------------------------------------------

@lru_cache(maxsize=1)
def buildable_pad() -> pm.Pad:
    """The pad the build chapter watches go up, with every stage switched on.

    Not the cheapest pad: half of :data:`park_world.PAD_STAGES` is the
    rotating base, the column and the aim arrow, and a pad without them would
    sit at stage two while the caption counted to eight.
    """
    diameter = pm.pad_for(pm.FLAGSHIP_DOME)
    dome = max(pm.domes_that_fit(diameter), key=lambda d: d.floor_sqft)
    return pm.Pad(diameter_ft=diameter, deck="gravel", rotating=True,
                  utility_column=True, solar_watts=pm.solar_watts_for(dome))


def scene_pad_build(app, opaque, transparent, p):
    """One pad assembling itself in the order it would actually be built."""
    spec = buildable_pad()
    placed = park_world.Placed(pad=spec, origin=(0.0, 0.0), dome="",
                               heading_deg=35.0)
    stage = park.pad_stage_at(clamp(p * 1.04))
    creator.draw(app, park.field())
    # Stage zero is graded ground, which is a real step and draws nothing. It
    # still gets its caption -- the frame is the site before the pad is -- but
    # an empty mesh must not be handed to the renderer.
    if stage >= 1:
        old._draw_pad(app, placed, stage=stage)
    label(app, np.array([0.0, 0.0, 5.6]),
          f"{park.PAD_STAGES[stage].upper()}\n"
          f"step {stage + 1} of {len(park.PAD_STAGES)}", AMBER)
    if stage >= 2:
        # The rim is the part a dome latches to. It is the whole difference
        # between this and a patio, so it is named the moment it exists.
        label(app, np.array([0.0, -placed.radius_m * 1.06, 1.2]),
              "ACCEPTOR RIM\nWHAT A DOME LATCHES TO", AMBER)
    if stage >= len(park.PAD_STAGES) - 1:
        label(app, np.array([0.0, 0.0, -1.0]),
              f"{spec.diameter_ft:.0f} FT  ·  {spec.deck.upper()} DECK  ·  "
              f"${spec.build_cost:,.0f} TO BUILD", GREEN)


def scene_decks(app, opaque, transparent, p):
    """The same pad in the three deck materials, priced as each one costs."""
    diameter = pm.basic_pad().diameter_ft
    span = _m(diameter) + 4.0
    creator.draw(app, park.field())
    reveal = clamp(p * 1.5)
    for index, deck in enumerate(pm.DECKS):
        if index / len(pm.DECKS) > reveal:
            continue
        x = (index - (len(pm.DECKS) - 1) / 2.0) * span
        spec = pm.Pad(diameter_ft=diameter, deck=deck)
        # park_bridge builds every pad at the origin and places it with the
        # draw request, so one deck mesh per material serves any number of
        # pads and the three here are the same object three times.
        creator.draw(app, park.pad(spec), offset=(x, 0.0, 0.0))
        # The three flat deck rates this used to read are gone; pad_deck
        # counts the boards instead, so the rate is derived from the real
        # takeoff for this diameter rather than looked up.
        import pad_deck

        built = pad_deck.deck(pm.Pad.DECK_BUILDS[deck], diameter)
        rate = built.usd_per_sqft
        # One label, not three. Three stacked world labels on one subject
        # cannot be kept apart by the declutter pass, and the first cut of
        # this chapter had them printing through each other.
        label(app, np.array([x, 0.0, 5.6]),
              f"{deck.upper()}\n"
              f"${rate:,.2f}/sq ft  ·  {spec.area_sqft:,.0f} sq ft\n"
              f"pad total ${spec.build_cost:,.0f}",
              DECK_TINT[deck])
    label(app, np.array([0.0, 0.0, 8.6]),
          "whatever the host wants to pay for", MUTED)


def _m(feet: float) -> float:
    return feet / FT_PER_M


# ----------------------------------------------------------------------
# The iris
# ----------------------------------------------------------------------

IRIS_LEAVES = 32
"""How many blades the aperture is drawn with.

Not a style choice. A blade has to span one blade-pitch of the pivot ring,
and the pitch divided by the blade's length is what decides whether the
picture reads as a mechanism or as a ring of fat wedges. At sixteen the blades
come out wider than they are long and the aperture looks like a hole cut in a
pie; at thirty-two the taper is legible and neighbouring blades still overlap
at the widest the aperture ever gets."""

IRIS_PIVOT_MARGIN_M = 0.55
"""How far outside the widest aperture the blade pins sit."""


def iris_geometry(radius: float) -> tuple[float, float, float]:
    """The pivot ring, the blade length, and the swing that gives this radius.

    A camera iris closes because its leaves turn on pins set in the outer
    ring; the aperture is the polygon their inner ends leave behind. Put the
    pins on a ring of radius ``P`` and give every blade the same length ``L``,
    and a tip swung ``psi`` away from pointing straight at the centre sits at

        ``sqrt(P^2 + L^2 - 2 P L cos(psi))``

    from the middle. ``P`` and ``L`` are properties of the mechanism; ``psi``
    is the one thing the drive changes. So the film shows the aperture it is
    talking about by solving for the swing, rather than by drawing a circle at
    a convenient size and calling it an iris.
    """
    low, high = pm.iris_span()
    r_low, r_high = low / FT_PER_M / 2, high / FT_PER_M / 2
    pivot = r_high + IRIS_PIVOT_MARGIN_M
    # With no swing at all the tip lands on the smallest aperture, so the
    # blade is exactly long enough to close the pad down to a one-person dome.
    blade = pivot - r_low
    cosine = (pivot * pivot + blade * blade - radius * radius) / (2.0 * pivot * blade)
    return pivot, blade, math.acos(clamp(cosine, -1.0, 1.0))


def scene_iris(app, opaque, transparent, p):
    """The acceptor rim opening and closing, with the range it spans."""
    low, high = pm.iris_span()
    radius = base.iris_radius(p)
    pivot, blade, swing = iris_geometry(radius)
    outer = pivot + 0.55

    creator.draw(app, park.field())
    # The pad under the mechanism. Drawn as a disc rather than through
    # park_bridge because this rim is a concept, not one of the standard pad
    # sizes, and the deck here exists only to give the blades something to
    # sit on.
    opaque.disc((0, 0, 0.10), outer + 0.30, (0.30, 0.30, 0.29, 1), 72)
    ring(opaque, outer, 0.26, MUTED, thickness=.10)

    # The track the leaves run on, and the pins they turn about.
    ring(opaque, pivot, 0.42, AMBER, thickness=.055)
    for index in range(IRIS_LEAVES):
        angle = math.tau * index / IRIS_LEAVES
        radial = np.array([math.cos(angle), math.sin(angle), 0.0])
        tangent = np.array([-math.sin(angle), math.cos(angle), 0.0])
        pin = radial * pivot
        opaque.sphere(pin + (0, 0, 0.46), 0.085, AMBER, 3, 6)

        # The blade. Cross sections are taken tangential to the pin's own
        # radius, so blades tile the annulus and overlap by a fixed share at
        # every aperture: the tip narrows as the iris closes, the way a real
        # leaf does, and the opening is never a ring of gaps.
        direction = _rotate(-radial, swing)
        tip = pin + direction * blade
        pitch_pivot = math.tau * pivot / IRIS_LEAVES
        pitch_tip = math.tau * max(radius, 0.02) / IRIS_LEAVES
        # Overlap by a fixed share of the local pitch at BOTH ends, so the
        # blades tile the annulus whether the aperture is wide open or nearly
        # shut. A fixed metric width would leave gaps at one end and a blocked
        # hole at the other.
        half_p = pitch_pivot * 0.78
        half_t = pitch_tip * 0.78
        axis = tip - pin
        length = float(np.linalg.norm(axis))
        if length > 1e-6:
            axis = axis / length
            across = np.array([-axis[1], axis[0], 0.0])
            corners = (
                pin + tangent * half_p + (0, 0, 0.40),
                tip + across * half_t + (0, 0, 0.40),
                tip - across * half_t + (0, 0, 0.40),
                pin - tangent * half_p + (0, 0, 0.40),
            )
            # Two tones alternating, so the overlap between neighbours is
            # visible as a shape rather than inferred from an outline.
            tint = (.62, .44, .20, 1) if index % 2 else (.72, .52, .24, 1)
            opaque.quad(corners[0], corners[1], corners[2], corners[3], tint)
        # A radial shoe, so each leaf reads as riding a track.
        opaque.cylinder(radial * (outer - 0.05) + (0, 0, 0.30),
                        radial * (pivot - 0.30) + (0, 0, 0.30),
                        .04, MUTED, 5)

    # The aperture itself, drawn where it currently is rather than where it
    # will end up. This is the one line on screen that has to be believed.
    ring(opaque, radius, 0.52, CYAN, thickness=.05)
    opaque.arrow((-radius, 0, 0.86), (radius, 0, 0.86), .028, CYAN)
    label(app, (0, 0, 1.9), f"{radius * 2 * FT_PER_M:.1f} FT ACCEPTOR", CYAN)

    if p > 0.55:
        # The two ends of the range, so the sentence "twenty or forty" has a
        # picture: both outlines are drawn at their true size.
        for feet, name in ((low, "SMALLEST"), (high, "LARGEST")):
            r = feet / FT_PER_M / 2
            ring(opaque, r, 0.34, MUTED, thickness=.022)
            label(app, (0, r * 1.03, 0.62),
                  f"{feet:.0f} FT / {name}", MUTED)
    if p > 0.84:
        label(app, (0, -outer * 1.02, 1.1),
              "ONE PAD · 20 FT OR 40 FT · NOT REBUILT", WHITE)


def _rotate(vector: np.ndarray, angle: float) -> np.ndarray:
    """A 2-D rotation about +Z, applied to an XY vector."""
    cos, sin = math.cos(angle), math.sin(angle)
    return np.array([
        vector[0] * cos - vector[1] * sin,
        vector[0] * sin + vector[1] * cos,
        0.0,
    ])


# ----------------------------------------------------------------------
# The deluxe foundation
# ----------------------------------------------------------------------

def scene_rotation(app, opaque, transparent, p):
    """The top-line pad, turning the house to face whatever the owner wants."""
    creator.draw(app, park.field())
    spec = pm.Pad(diameter_ft=36.0, deck="concrete", rotating=True)
    angle = -65 + 165 * ease_in_out(clamp((p - 0.15) / 0.70))
    creator.draw(app, park.pad(spec, occupied=True, heading=angle))
    build = base.compact_dome(True)
    creator.draw(app, build, offset=(0, 0, park.dome_lift(spec)), yaw=angle)

    a = math.radians(angle)
    direction = np.array([math.cos(a), math.sin(a), 0.0])
    opaque.arrow(direction * 3.4 + (0, 0, 2.1), direction * 5.4 + (0, 0, 2.1),
                 .065, CYAN)
    # The sun, and the two things a person actually aims a window at.
    opaque.sphere((6.4, -2.2, 7.0), .52, AMBER, 6, 12)
    label(app, (6.4, -2.2, 8.0), "MORNING SUN", AMBER)
    label(app, (-5.0, -1.0, 1.4), "PRIVATE CORNER", CYAN)
    label(app, (5.0, 3.2, 1.4), "STREET / VIEW", WHITE)
    label(app, (0, 0, 9.2),
          "A FOUNDATION THAT AIMS THE HOUSE\n"
          "no panels needed to want this", AMBER)
    if p > 0.60:
        label(app, (0, 0, 6.4),
              "bearing, drive and rotating services\nare their own design",
              MUTED)
    if p > 0.80:
        label(app, (0, 0, -1.1),
              "THE UTMOST TOP-LINE KIND  ·  DELUXE PRICING", RED)


# ----------------------------------------------------------------------
# Services: up the middle, then out along the shell
# ----------------------------------------------------------------------

def scene_veins(app, opaque, transparent, p):
    """Supply leaving the centre, climbing, and running the outside skin.

    The shell is the simulator's solved article, and the runs follow its own
    seams: a vein drawn down the middle of a panel would be a drawing of a
    thing that cannot be built, because the panel is what comes off.
    """
    radius = 5.0
    # The Creator's own field, so the shell stands somewhere. Drawing the
    # simulator's dome straight onto black was the first cut of this picture
    # and it read as a diagram rather than as a building.
    creator.draw(app, park.field())
    wedge.world_batches(opaque, "point_dome_out", scene_radius=radius,
                        parts=("wood",))
    model = wedge.model("point_dome_out")
    scale = radius / model.topology.sphere_radius_in

    # Up the middle first. This is the run the whole chapter is named for.
    riser = 0.10 + 0.92 * ease_in_out(clamp(p / 0.30))
    opaque.cylinder((0, 0, 0.08), (0, 0, radius * riser * 1.02), .075, AMBER, 10)
    if p <= 0.30:
        label(app, (0, 0, radius * riser + 1.2), "UP THE MIDDLE", AMBER)

    # Then outward along the seams, lit in the order the eye should follow
    # them: up the shell, over the shoulder, down to the perimeter.
    travel = clamp((p - 0.24) / 0.52)
    terminals = {0: "LIGHT", len(model.seams) // 3: "OUTLET",
                 (2 * len(model.seams)) // 3: "WATER"}
    shown = 0
    for index, seam in enumerate(model.seams):
        a = np.asarray(seam.start) * scale
        b = np.asarray(seam.end) * scale
        share = clamp(travel * len(model.seams) * 1.6 - index * 0.35)
        if share <= 0.0:
            continue
        shown += 1
        opaque.cylinder(a, b, .035, CYAN, 5)
        if index in terminals:
            opaque.sphere(b, .12, AMBER, 4, 8)
            label(app, b + np.array([0, 0, 0.55]), terminals[index], AMBER)
    if shown:
        label(app, (0, 0, radius + 1.4),
              "OUT ALONG THE SEAMS / LATCHED / STILL REACHABLE", CYAN)
    if p > 0.80:
        label(app, (0, 0, -1.0),
              "out of the way, accessible, semi-permanent", MUTED)


def scene_veins_joke(app, opaque, transparent, p):
    """The channels, and the joke about what the author's domes keep becoming.

    The joke is the author's and it is in the spoken script; the frame carries
    it because the two buildings it names are both real and both in this
    repository, so the audience can be shown the first one.
    """
    scene_veins(app, opaque, transparent, min(p, 0.62))
    if p > 0.55:
        label(app, (0, 0, 9.4), "BRAINIAC BUILD", CYAN)
        label(app, (0, 0, 7.9),
              "the first one was the Frankendome\n"
              "a conglomerate of strut types", MUTED)


# ----------------------------------------------------------------------
# The pad catalogue
# ----------------------------------------------------------------------

def scene_catalog(app, opaque, transparent, p):
    """Every standard pad size, and the designs each one actually takes.

    Drawn as a stepped stack rather than a row because the sizes are not
    evenly spaced -- six pads laid end to end need sixty metres of camera and
    the smallest two come out as specks. Nested, every ring keeps its true
    diameter and the four-foot step between neighbours is visible as a gap.
    """
    creator.draw(app, park.field())
    sizes = pm.pad_sizes()
    total = len(pm.dome_catalogue())
    count = len(sizes)
    reveal = clamp(p * 1.55)
    for index, size in enumerate(sizes):
        if index / count > reveal:
            continue
        radius = _m(size) / 2.0
        # Smallest ring on top, so each size is a terrace rather than a lid.
        # The steps are deliberately tall and the alternate decks light and
        # dark: at a quarter of this spacing the stack read as one flat disc
        # with a few faint circles drawn on it.
        height = 0.08 + (count - 1 - index) * 0.16
        shade = (0.40, 0.38, 0.36, 1) if index % 2 else (0.26, 0.25, 0.24, 1)
        opaque.disc((0, 0, height), radius, shade, 72)
        ring(opaque, radius, height + 0.07, AMBER, thickness=.075)
        fits = len(pm.domes_that_fit(size))
        # Two lines per ring, fanned around the stack rather than stacked on
        # one ray. Six rings of similar radius do not leave room for three
        # lines each: the detail lines were printing through one another.
        angle = math.radians(90.0 + index * 47.0)
        point = np.array([math.cos(angle) * radius * 1.16,
                          math.sin(angle) * radius * 1.16, height + 1.0])
        label(app, point,
              f"{size:.0f} FT  ·  {fits} OF {total} DESIGNS\n"
              f"{pm.pad_area_sqft(size):,.0f} SQ FT", CYAN)
    # The pad is the host's, so the catalogue wears the host's colour.
    label(app, np.array([0.0, 0.0, len(sizes) * 0.055 + 4.2]),
          "PAD SIZES, ROUNDED UP FROM THE DOMES THAT MUST FIT", AMBER)


# ----------------------------------------------------------------------
# The line between the two people
# ----------------------------------------------------------------------

def scene_line(app, opaque, transparent, p):
    """Where each side's money is, drawn on the two sides of one line.

    The sentence this picture exists for is "below the line is the host's
    money and it is in the ground; above the line is the tenant's money and a
    drive away with them". So the line is not a figure of speech on screen: it
    is a bar in the world, with the pad under it and the house over it.
    """
    spec = pm.basic_pad()
    height = 4.4
    creator.draw(app, park.field())
    placed = park_world.Placed(pad=spec, origin=(0.0, 0.0), dome="",
                               heading_deg=20.0)
    old._draw_pad(app, placed)
    build = park.dome_on_pad(pm.FLAGSHIP_DOME)
    creator.draw(app, build, offset=(0.0, 0.0, park.dome_lift(spec)), yaw=20.0)

    # The line. The bar is chunky on purpose: this is the one graphic in the
    # film that has to be unmistakable from across a room.
    reach = 11.0
    # A halo under the bar as well as the bar itself. Drawn as one cylinder
    # the line disappeared into the grass at any distance the whole pad fitted.
    opaque.cylinder((-reach, 0.0, height), (reach, 0.0, height), .30, WHITE, 12)
    opaque.cylinder((-reach, 0.0, height), (reach, 0.0, height), .15, WHITE, 12)
    transparent.box((0.0, 0.0, height), (reach * 2.0, 3.4, 0.02),
                    (0.91, 0.95, 0.98, 0.09))

    # Every label sits in its own quarter of the frame. The first cut put four
    # of them within a metre of the bar and they printed on top of one another.
    label(app, (-reach - 1.6, 0.0, height + 1.1), "ABOVE THE LINE", CYAN)
    label(app, (-reach - 1.6, 0.0, height - 1.3), "BELOW THE LINE", AMBER)
    if p > 0.22:
        label(app, (-4.2, 0.0, 1.0),
              "HOST MONEY\nIN THE GROUND\nIT STAYS", AMBER)
    if p > 0.44:
        label(app, (0.0, 0.0, park.dome_lift(spec) + build.apex + 3.4),
              "TENANT MONEY\nA DRIVE AWAY\nIT GOES", CYAN)
    if p > 0.84:
        # The comparison the sentence is really drawing: a landlord's money is
        # in the walls the tenant is living between, which is where the
        # argument between them comes from.
        label(app, (6.4, -2.4, height + 6.4),
              "A LANDLORD'S MONEY IS IN THE WALLS\nTHE TENANT LIVES BETWEEN",
              RED)


# ----------------------------------------------------------------------
# What a host can choose to build
# ----------------------------------------------------------------------

HOST_FEATURES = (
    ("FLOOR HEATING", AMBER),
    ("WATER STORAGE", CYAN),
    ("FREEZER STORAGE", CYAN),
    ("SUN TRACKING", AMBER),
    ("SHOP FLOOR", GREEN),
    ("SMART SYSTEMS", WHITE),
)
"""The development branches a host might fit, in the author's own order.

None of these is priced, and the caption says so: the chapter is about what
the pad standard could grow into, not about what a host should buy.

The names are kept short on purpose. Six bays across a 16:9 frame leave about
260 pixels between neighbouring captions, and the first cut's "deep freeze
storage" ran straight through the bay beside it."""


def scene_host_design(app, opaque, transparent, p):
    """Six things a host could add to the pad standard, as six bays."""
    creator.draw(app, park.field())
    columns, spacing = 3, 7.6
    reveal = clamp(p * 1.5)
    for index, (name, colour) in enumerate(HOST_FEATURES):
        if index / len(HOST_FEATURES) > reveal:
            continue
        x = (index % columns - 1) * spacing
        y = (0.5 - index // columns) * spacing
        opaque.box((x, y, 0.30), (5.4, 5.0, 0.42), (0.14, 0.19, 0.24, 1))
        ring(opaque, 1.70, 0.62, AMBER, origin=(x, y, 0), thickness=.05)
        if index % 3 == 0:
            opaque.cylinder((x, y, 0.55), (x, y, 2.0), .18, colour, 10)
        elif index % 3 == 1:
            opaque.box((x, y, 1.25), (2.2, 2.2, 1.6), colour)
        else:
            opaque.sphere((x, y, 1.55), .84, colour, 5, 10)
        # Staggered by column, so neighbouring captions never share a baseline.
        label(app, (x, y, 3.5 + (index % columns) * 1.15), name, colour)
    if p > 0.72:
        label(app, (0, 0, -6.0),
              "the first job is still the simple pad built well", MUTED)


# ----------------------------------------------------------------------
# The three chapters that already worked, with this cut's words
# ----------------------------------------------------------------------

def scene_layers(app, opaque, transparent, p):
    """The Arctic argument, without a payback figure anywhere on the frame.

    The author cut the "first layer pays for itself in months" line. What is
    left is the claim that survives it: the number is not fixed on the day the
    house is built, and it only moves one way.
    """
    base.scene_layers(app, opaque, transparent, p)
    app.world_labels[:] = [item for item in app.world_labels
                           if "pays back" not in item.text
                           and "paid for itself" not in item.text]
    shift = old._shift(app)
    if p > 0.55:
        label(app, shift + (0.0, 0.0, 7.6),
              "THE R-VALUE IS NOT DECIDED ON DAY ONE", WHITE)
    if p > 0.80:
        label(app, shift + (0.0, 0.0, 6.6),
              "BETTER AT HEATING AND COOLING EVERY YEAR YOU OWN IT", GREEN)


def scene_growth(app, opaque, transparent, p):
    """The three sizes the hardware is bought for: this one and two beyond.

    Redrawn rather than borrowed because the shell has to stand on the
    Creator's field and to move aside for the worksheet. The first cut put it
    on black at the origin, which left it floating and ran its captions under
    the panel.
    """
    shift = old._shift(app)
    creator.draw(app, park.field(), offset=tuple(shift))
    stage = min(len(pm.DOME_CLASSES) - 1, int(p * len(pm.DOME_CLASSES)))
    size = pm.DOME_CLASSES[stage]
    radius = 3.0 * size.longest_member_ft / pm.DOME_CLASSES[0].longest_member_ft
    wedge.world_batches(opaque, "point_dome_out", scene_radius=radius,
                        parts=("wood", "rigid"), origin=tuple(shift))
    count = len(wedge.model("point_dome_out").members)
    steps = len(pm.DOME_CLASSES) - 1 - stage
    top = np.asarray(shift) + np.array([0.0, 0.0, radius + 1.5])
    label(app, top, f"{size.longest_member_ft:.0f} FT LONG MEMBER  ·  "
                    f"~{size.floor_sqft:,.0f} SQ FT", CYAN)
    label(app, top - np.array([0.0, 0.0, 1.15]),
          f"{count} WEDGE MEMBERS  ·  QUALIFIED HARDWARE KEPT", AMBER)
    if p > 0.30:
        # The brief is a range, not one house: buy the connectors for where
        # the build is going, and collect the longer members on the way.
        label(app, top - np.array([0.0, 0.0, 2.3]),
              "SIZE THE HARDWARE TWO STEPS AHEAD" if steps else
              "THE LAST OF THE THREE PLANNED SIZES", GREEN)
        label(app, top - np.array([0.0, 0.0, 3.45]),
              f"{steps} size{'s' if steps != 1 else ''} of headroom left in "
              f"this hardware set", MUTED)
    # Collection rack: the longer members arrive beside the current shell.
    for index in range(8):
        if index / 8 > p:
            continue
        x = shift[0] + 7.0 + (index % 4) * 0.18
        opaque.cylinder((x, -2, .3 + (index // 4) * .18),
                        (x, 2, .3 + (index // 4) * .18),
                        .075, (.62, .39, .18, 1), 3)


def scene_channels(app, opaque, transparent, p):
    """The wedge buildout, drawn on the Creator's field and off the panel."""
    shift = old._shift(app)
    creator.draw(app, park.field(), offset=tuple(shift))
    radius = 5.0
    wedge.world_batches(opaque, "point_dome_out", scene_radius=radius,
                        parts=("wood",), origin=tuple(shift))
    model = wedge.model("point_dome_out")
    scale = radius / model.topology.sphere_radius_in
    # Separate supply and conduit traces rise from the known central service
    # spot. Drains stay at the floor: the picture must not imply uphill flow.
    for index, colour in enumerate((CYAN, AMBER)):
        x = shift[0] + (index - 0.5) * 0.20
        opaque.cylinder((x, shift[1], 0.15), (x, shift[1], radius + 0.08),
                        .06, colour, 8)
    for index, seam in enumerate(model.seams):
        if index / len(model.seams) > 0.15 + 0.85 * clamp(p * 1.6):
            continue
        a = np.asarray(seam.start) * scale + shift
        b = np.asarray(seam.end) * scale + shift
        opaque.cylinder(a, b, .035, CYAN, 5)
        t = (p * 3 + index * 0.09) % 1
        opaque.sphere(a + (b - a) * t, .085, AMBER, 3, 6)
    top = np.asarray(shift) + np.array([0.0, 0.0, radius + 1.7])
    label(app, top, "CENTER UP / OUT / AROUND THE SHELL", CYAN)
    label(app, top - np.array([0.0, 0.0, 1.2]),
          "THE PAIRED MEMBERS LEAVE A CHANNEL AT EVERY SEAM", AMBER)
    label(app, np.asarray(shift) + np.array([0.0, 0.0, -1.0]),
          "ACCESSIBLE CHANNELS / DRAIN AT FLOOR", MUTED)


def scene_hardware(app, opaque, transparent, p):
    """One design at three radii, framed as a range rather than a trick."""
    old.scene_hardware(app, opaque, transparent, p)
    shift = old._shift(app)
    if p > 0.68:
        label(app, np.asarray(shift) + np.array([0.0, 0.0, 12.0]),
              "THE SAME LIST OF PARTS AT EVERY SIZE", WHITE)
    if p > 0.86:
        label(app, np.asarray(shift) + np.array([0.0, 0.0, 10.8]),
              "ONE HARDWARE SET IS A RANGE OF SIZES, NOT ONE HOUSE", GREEN)


def scene_rewards(app, opaque, transparent, p):
    """The three reward categories, standing on the Creator's field.

    The first cut drew them on black, which reads as a slide rather than as
    objects somebody is being offered.
    """
    creator.draw(app, park.field())
    base.scene_rewards(app, opaque, transparent, p)


def scene_close(app, opaque, transparent, p):
    """The park, with the four answers to "what does a stay cost" named.

    Held on separate lines rather than stacked at one height: four captions
    that arrive one after another and share a plane end up printing through
    each other in the declutter pass.
    """
    old.scene_site(app, opaque, transparent, 0.35 + 0.5 * clamp(p))
    app.world_labels.clear()
    shift = np.asarray(old._shift(app))
    rows = (
        (0.20, 15.4, "A HOTEL SELLS YOU A NIGHT", MUTED),
        (0.42, 13.8, "A SHORT LET SELLS YOU A FORTNIGHT", MUTED),
        (0.64, 12.2, "A LEASE SELLS YOU A YEAR, AND CHARGES YOU TO LEAVE EARLY",
         MUTED),
        (0.84, 10.4, "BRING YOUR OWN HOME", CYAN),
    )
    for threshold, height, text, colour in rows:
        if p > threshold:
            label(app, shift + np.array([0.0, 0.0, height]), text, colour)


SCENES: dict = {
    "byod_title": scene_title,
    "byod_storage": scene_storage,
    "byod_pad_build": scene_pad_build,
    "byod_decks": scene_decks,
    "byod_iris": scene_iris,
    "byod_rotation": scene_rotation,
    "byod_veins": scene_veins,
    "byod_veins_joke": scene_veins_joke,
    "byod_catalog": scene_catalog,
    "byod_line": scene_line,
    "byod_host_design": scene_host_design,
    "byod_layers": scene_layers,
    "byod_growth": scene_growth,
    "byod_channels": scene_channels,
    "byod_hardware": scene_hardware,
    "byod_rewards": scene_rewards,
    "byod_close": scene_close,
}


def validate_byod_attempt_scenes() -> None:
    """Prove the new painters before a ninety-minute render finds out.

    Same contract every lesson's painters are held to: real geometry at the
    first frame as well as the last, no empty mesh handed to the renderer, and
    finite numbers throughout.
    """
    from .render_kit import TriangleBatch
    from .lesson_dome_park import _Probe

    for name, painter in SCENES.items():
        for progress in (0.0, 0.02, 0.35, 0.7, 1.0):
            probe = _Probe(None, (90.0, 20.0, 40.0))
            opaque, transparent = TriangleBatch(), TriangleBatch()
            painter(probe, opaque, transparent, progress)
            # The project's contract, not a stricter one: a painter draws
            # through the Dome Creator *or* through the simulator bridge, and
            # both are first class. What is not allowed is drawing nothing.
            assert (probe.creator_draws or opaque.vertices
                    or transparent.vertices), (name, progress)
            for batch in (opaque, transparent):
                assert np.isfinite(np.asarray(batch.vertices)).all(), (
                    name, progress)
            for request in probe.creator_draws:
                assert len(request.build.mesh.vertices), (
                    name, progress, request.build.name)
                assert request.build.triangles > 0, (name, request.build.name)
            for item in probe.world_labels:
                assert item.text.strip(), (name, progress)
        probe = _Probe(None, (90.0, 20.0, 40.0))
        painter(probe, TriangleBatch(), TriangleBatch(), 1.0)
        if name == "byod_title":
            # The one painter that is supposed to say nothing: the statement
            # is the renderer's title overlay, and a world label under it
            # would be a second caption arguing with the first.
            assert not probe.world_labels, probe.world_labels
        else:
            assert probe.world_labels, f"{name} never says anything"

    # The iris has to actually move the aperture, which is the whole reason
    # this painter was rewritten. A blade that never swings is a still.
    closed, open_ = base.iris_radius(0.0), base.iris_radius(1.0)
    assert open_ > closed * 1.9, (closed, open_)
    swings = [iris_geometry(r)[2] for r in (closed, open_)]
    assert swings[1] > swings[0] + 0.5, swings
    for radius in (closed, open_):
        pivot, blade, swing = iris_geometry(radius)
        reached = math.sqrt(pivot ** 2 + blade ** 2
                            - 2 * pivot * blade * math.cos(swing))
        assert abs(reached - radius) < 1e-6, (radius, reached)

    # The catalogue is the model's own sizes, and every one of them has to
    # take at least one shipped design or it is not a pad size.
    for size in pm.pad_sizes():
        assert pm.domes_that_fit(size), size
