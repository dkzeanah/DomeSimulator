"""Every dome type in the Dome Creator world, rendered from the real model.

The other lessons in this package draw domes they compute themselves.
This one draws **the simulator's own domes**: each chapter rebuilds a
shipped preset with :class:`dome_model.DomeModel` and paints the struts,
panels and hubs the walkable world would paint, at their real metre
scale.  Nothing is a stand-in.  The Whole Trunk Lodge you see here is
the configuration the Preset button loads, and the numbers beside it are
read off that same model.

That is what makes the film reproducible in the strongest sense: to
check any figure in it, open the tool, load that preset, and read the
bill of materials.
"""

from __future__ import annotations

import math
from dataclasses import replace
from functools import lru_cache

import numpy as np

from .lessons import Chapter, Lesson
from .render_kit import (
    AMBER,
    CYAN,
    GREEN,
    MUTED,
    PURPLE,
    RED,
    WHITE,
    WorldLabel,
    clamp,
    ease_in_out,
)
from .segments import compose
from .world_facts import (
    ALL_SCREENS,
    DomeType,
    by_name,
    dome_geometry,
    dome_types,
    frequency_ladder,
    steps_catalogue,
    steps_economics,
    steps_efficiency,
    steps_frequency,
    steps_hub_vs_hubless,
    steps_scale,
    validate_world_facts,
    world_report,
)


TYPES = dome_types()


def _rgb(colour) -> tuple[int, int, int]:
    return tuple(int(round(channel * 255)) for channel in colour[:3])


@lru_cache(maxsize=32)
def _model(name: str):
    """The built model for one preset, cached.

    Rebuilding a 250-strut dome inside a scene painter would happen
    thirty times a second; every frame is a pure function of progress
    either way, so the cache changes cost and nothing else.
    """
    return dome_geometry(by_name()[name])


@lru_cache(maxsize=32)
def _drawable(name: str):
    """Struts, panels and hubs as plain arrays, ready to paint."""
    model = _model(name)
    struts = tuple((np.asarray(a, dtype=float), np.asarray(b, dtype=float))
                   for a, b, _ in model.struts)
    panels = tuple(np.asarray(panel.world_verts, dtype=float)
                   for panel in model.panels)
    hubs = tuple(np.asarray(point, dtype=float) for point, _ in model.hubs)
    return struts, panels, hubs, model.frame_color_rgb(), model.panel_tint()


def _draw_dome(opaque, transparent, name: str, *, origin=None,
               reveal: float = 1.0, scale: float = 1.0,
               strut_radius: float | None = None, segments: int = 5,
               panels: bool = True, panel_alpha: float = 0.30,
               hubs: bool = True) -> None:
    """Paint one preset's real geometry, optionally elsewhere and smaller.

    ``reveal`` builds it from the ground up, which is how the world's own
    construction simulation puts a dome together: lowest parts first.
    """
    struts, faces, hub_points, frame_rgb, tint = _drawable(name)
    shift = np.zeros(3) if origin is None else np.asarray(origin, dtype=float)
    grown = clamp(reveal)

    def place(point):
        return point * scale + shift

    if strut_radius is None:
        strut_radius = 0.055 * scale
    frame = (frame_rgb[0], frame_rgb[1], frame_rgb[2], 1.0)

    # Build bottom-up: sort by the height of the strut's own midpoint.
    order = sorted(range(len(struts)),
                   key=lambda i: float(struts[i][0][2] + struts[i][1][2]))
    shown = int(len(order) * ease_in_out(grown))
    for index in order[:shown]:
        a, b = struts[index]
        opaque.cylinder(place(a), place(b), strut_radius, frame, segments)

    if hubs and grown > 0.05:
        hub_shown = int(len(hub_points) * ease_in_out(grown))
        for point in sorted(hub_points,
                            key=lambda p: float(p[2]))[:hub_shown]:
            opaque.sphere(place(point), strut_radius * 1.55, MUTED, 3, 6)

    if panels and grown > 0.12:
        face_order = sorted(range(len(faces)),
                            key=lambda i: float(faces[i][:, 2].mean()))
        face_shown = int(len(face_order) * ease_in_out(clamp(grown * 1.15)))
        colour = (tint[0] * 0.62, tint[1] * 0.74, tint[2] * 0.88,
                  panel_alpha)
        for index in face_order[:face_shown]:
            corners = faces[index]
            centre = corners.mean(axis=0)
            normal = centre / (np.linalg.norm(centre) or 1.0)
            transparent.triangle(place(corners[0]), place(corners[1]),
                                 place(corners[2]), colour, normal)


def _ground_disc(opaque, name: str, origin=None, scale: float = 1.0,
                 reveal: float = 1.0) -> None:
    """The pad each design sits on, sized from its own foundation."""
    dome = by_name()[name]
    shift = np.zeros(3) if origin is None else np.asarray(origin, dtype=float)
    radius = dome.radius_m * dome.config.foundation_scale * scale
    opaque.disc(np.array([shift[0], shift[1], 0.04]),
                radius * ease_in_out(clamp(reveal)),
                (0.11, 0.20, 0.29, 1.0), 34)


# ----------------------------------------------------------------------
# One chapter per design
# ----------------------------------------------------------------------

def _showcase_painter(name: str):
    """A painter that raises one design and labels what it is made of."""
    dome = by_name()[name]

    def painter(app, opaque, transparent, p: float) -> None:
        _ground_disc(opaque, name, reveal=clamp(p * 3.0))
        _draw_dome(opaque, transparent, name, reveal=clamp(p * 1.45))
        # Every label stacks ABOVE the dome. Anything placed below the
        # ground plane lands in the headline block this style burns into
        # the bottom of the frame.
        top = dome.height_ft / 3.281
        app.world_labels.append(WorldLabel(
            np.array([0.0, 0.0, top + 3.4]),
            f"{dome.name.upper()}\n{dome.frequency}V  ·  "
            f"{dome.diameter_ft:.0f} FT ACROSS",
            _rgb(CYAN)))
        if p > 0.30:
            app.world_labels.append(WorldLabel(
                np.array([0.0, 0.0, top + 2.1]),
                f"{dome.struts} struts in {dome.strut_classes} length "
                f"class{'es' if dome.strut_classes != 1 else ''}  ·  "
                f"{dome.panels} panels  ·  "
                f"{dome.hubs} hubs  ·  {dome.bolts} bolts",
                _rgb(WHITE)))
        if p > 0.55:
            app.world_labels.append(WorldLabel(
                np.array([0.0, 0.0, top + 1.1]),
                f"{dome.floor_sqft:,.0f} sq ft floor  ·  "
                f"${dome.total_cost:,.0f}  ·  "
                f"${dome.cost_per_sqft:.0f}/sq ft",
                _rgb(GREEN)))
    return painter


# ----------------------------------------------------------------------
# The whole catalogue, at real relative scale
# ----------------------------------------------------------------------

def _lineup_positions() -> tuple[tuple[str, float, float], ...]:
    """Every design placed in two rows, spaced by its own size.

    Real scale is the point: a sixty-five foot lodge should dwarf a
    twenty-eight foot treehouse dome on screen, because it does. But
    twelve domes at true scale in a single row is a hundred and sixty
    units wide, which frames as a thin strip of specks. Two staggered
    rows halve the width and use the depth the side-on camera provides,
    so each dome is twice the size on screen and the true size
    relationship still reads.
    """
    half = (len(TYPES) + 1) // 2
    rows = (TYPES[:half], TYPES[half:])
    depth = max(dome.radius_m for dome in TYPES) * 1.9
    placed: list[tuple[str, float, float]] = []
    spans: list[float] = []
    for index, row in enumerate(rows):
        cursor = 0.0
        # +Y is toward the camera at yaw 90, so row 0 stands in front.
        y = depth * (0.85 if index == 0 else -0.85)
        for dome in row:
            cursor += dome.radius_m * 1.22
            placed.append((dome.name, cursor, y))
            cursor += dome.radius_m * 1.22
        spans.append(cursor)
    span = max(spans)
    # +X is screen left at these cameras, so mirror about the centre and
    # the catalogue reads left to right on film.
    return tuple((name, span * 0.5 - x, y) for name, x, y in placed)


LINEUP = _lineup_positions()
LINEUP_SPAN = max(abs(x) for _, x, _ in LINEUP) * 2.0


def scene_world_lineup(app, opaque, transparent, p: float) -> None:
    """All twelve designs standing together, to true relative size."""
    for index, (name, x, y) in enumerate(LINEUP):
        reveal = clamp(p * (len(LINEUP) + 2.0) - index * 0.9)
        if reveal <= 0.02:
            continue
        origin = np.array([x, y, 0.0])
        _ground_disc(opaque, name, origin=origin, reveal=reveal)
        # Struts only, at a coarser tube: twelve full domes with panels
        # is a quarter of a million triangles a frame for a shot where
        # nothing is legible anyway.
        _draw_dome(opaque, transparent, name, origin=origin, reveal=reveal,
                   segments=4, panels=False, hubs=False)
    if p > 0.55:
        biggest = max(TYPES, key=lambda d: d.floor_sqft)
        smallest = min(TYPES, key=lambda d: d.floor_sqft)
        app.world_labels.extend([
            WorldLabel(np.array([0.0, 0.0, 16.5]),
                       f"{len(TYPES)} DESIGNS, ONE GEOMETRY ENGINE",
                       _rgb(WHITE)),
            WorldLabel(np.array([0.0, 0.0, 13.8]),
                       f"{smallest.floor_sqft:,.0f} to "
                       f"{biggest.floor_sqft:,.0f} square feet -- drawn to "
                       "true relative size", _rgb(MUTED)),
        ])


# ----------------------------------------------------------------------
# The frequency ladder
# ----------------------------------------------------------------------

@lru_cache(maxsize=1)
def _ladder_models():
    """1V through 4V at one radius, built once for drawing."""
    import dome_model

    built = []
    for step in frequency_ladder():
        config = dome_model.DomeConfig()
        config.frequency = step.frequency
        config.radius = step.radius_m
        model = dome_model.DomeModel(config)
        model.rebuild()
        struts = tuple((np.asarray(a, dtype=float), np.asarray(b, dtype=float))
                       for a, b, _ in model.struts)
        built.append((step, struts, model.frame_color_rgb()))
    return tuple(built)


def scene_world_frequency(app, opaque, transparent, p: float) -> None:
    """1V, 2V, 3V and 4V side by side at the same radius."""
    ladder = _ladder_models()
    spacing = 13.0
    for index, (step, struts, frame_rgb) in enumerate(ladder):
        reveal = clamp(p * (len(ladder) + 1.2) - index)
        if reveal <= 0.02:
            continue
        # +X is screen left, so 1V takes the largest +X and the ladder
        # climbs left to right.
        x = (1.5 - index) * spacing
        origin = np.array([x, 0.0, 0.0])
        opaque.disc(np.array([x, 0.0, 0.04]), step.radius_m * 1.12,
                    (0.11, 0.20, 0.29, 1.0), 30)
        colour = (frame_rgb[0], frame_rgb[1], frame_rgb[2], 1.0)
        order = sorted(range(len(struts)),
                       key=lambda i: float(struts[i][0][2] + struts[i][1][2]))
        for slot in order[:int(len(order) * ease_in_out(reveal))]:
            a, b = struts[slot]
            opaque.cylinder(a + origin, b + origin, 0.075, colour, 4)
        if reveal > 0.5:
            # The height each one actually reaches, and whether that is
            # a hemisphere -- the point of the whole comparison.
            mark = GREEN if step.is_hemisphere else AMBER
            opaque.box((x, 0.0, step.radius_m),
                       (step.radius_m * 2.3, 0.06, 0.05),
                       (0.95, 0.72, 0.25, 0.75))
            app.world_labels.append(WorldLabel(
                np.array([x, 0.0, step.height_m + 1.5]),
                f"{step.frequency}V\n{step.struts} struts  "
                f"{step.strut_classes} length"
                f"{'s' if step.strut_classes != 1 else ''}",
                _rgb(mark)))
            app.world_labels.append(WorldLabel(
                np.array([x, 0.0, -1.4]),
                "hemisphere" if step.is_hemisphere
                else f"taller by {step.height_m - step.radius_m:.2f} m",
                _rgb(mark)))
    if p > 0.35:
        app.world_labels.append(WorldLabel(
            np.array([0.0, 0.0, 12.5]),
            "THE GOLD LINE IS ONE RADIUS -- WHERE A HEMISPHERE STOPS",
            _rgb(WHITE)))


# ----------------------------------------------------------------------
# Hub against hubless, both real designs
# ----------------------------------------------------------------------

def scene_world_framing(app, opaque, transparent, p: float) -> None:
    """The hubbed dome and the hubless one, from this world."""
    hubless = next(d for d in TYPES if d.frame_style == "Hubless Doubled")
    hubbed = next(d for d in TYPES if d.frequency == hubless.frequency
                  and d.frame_style == "Hub & Strut")
    # Drawn to a COMMON radius on purpose. These two presets are very
    # different sizes, and at true scale the comparison reads as "big
    # dome versus small dome" when the subject is framing, not size.
    display_radius = 6.0
    gap = display_radius * 1.6
    for index, dome in enumerate((hubbed, hubless)):
        x = gap if index == 0 else -gap
        origin = np.array([x, 0.0, 0.0])
        reveal = clamp(p * 2.2 - index * 0.55)
        if reveal <= 0.02:
            continue
        scale = display_radius / dome.radius_m
        opaque.disc(np.array([x, 0.0, 0.04]),
                    display_radius * 1.12 * ease_in_out(reveal),
                    (0.11, 0.20, 0.29, 1.0), 32)
        _draw_dome(opaque, transparent, dome.name, origin=origin,
                   reveal=reveal, scale=scale, strut_radius=0.075,
                   panels=False,
                   hubs=dome.frame_style == "Hub & Strut")
        if reveal > 0.45:
            top = dome.height_ft / 3.281 * scale
            app.world_labels.append(WorldLabel(
                np.array([x, 0.0, top + 2.6]),
                f"{dome.frame_style.upper()}\n{dome.struts} STRUTS",
                _rgb(CYAN if index == 0 else AMBER)))
            app.world_labels.append(WorldLabel(
                np.array([x, 0.0, top + 1.4]),
                f"{dome.hubs} hubs  ·  {dome.bolts} bolts",
                _rgb(GREEN if dome.hubs == 0 else MUTED)))
    if p > 0.6:
        app.world_labels.append(WorldLabel(
            np.array([0.0, 0.0, display_radius + 5.2]),
            f"{hubless.struts} sticks and no hubs, against "
            f"{hubbed.struts} sticks and {hubbed.hubs} of them",
            _rgb(WHITE)))
        app.world_labels.append(WorldLabel(
            np.array([0.0, 0.0, display_radius + 4.0]),
            "drawn to the same radius -- this is about framing, not size",
            _rgb(MUTED)))


# ----------------------------------------------------------------------
# What the skin costs
# ----------------------------------------------------------------------

def scene_world_economics(app, opaque, transparent, p: float) -> None:
    """Cost per square foot, as a bar per design."""
    ranked = sorted(TYPES, key=lambda d: d.cost_per_sqft)
    tallest = max(d.cost_per_sqft for d in ranked)
    spacing = 3.5
    reveal = clamp(p * 1.35)
    for index, dome in enumerate(ranked):
        if index / len(ranked) > reveal:
            continue
        x = (len(ranked) / 2.0 - index) * spacing
        height = 9.0 * (dome.cost_per_sqft / tallest)
        colour = GREEN if index < 4 else (AMBER if index < 8 else RED)
        opaque.box((x, 0.0, height * 0.5 + 0.2), (2.5, 1.6, max(0.06, height)),
                   colour)
        app.world_labels.append(WorldLabel(
            np.array([x, 0.0, height + 1.1]),
            f"${dome.cost_per_sqft:.0f}", _rgb(colour)))
        if index in (0, len(ranked) - 1):
            app.world_labels.append(WorldLabel(
                np.array([x, 0.0, height + 2.4]),
                dome.name.upper(), _rgb(WHITE)))
    cheapest, dearest = ranked[0], ranked[-1]
    app.world_labels.append(WorldLabel(
        np.array([0.0, 0.0, -1.8]),
        f"${cheapest.cost_per_sqft:.0f} to ${dearest.cost_per_sqft:.0f} a "
        "square foot -- same geometry, different skin",
        _rgb(MUTED)))


def scene_world_efficiency(app, opaque, transparent, p: float) -> None:
    """Envelope per unit floor: the shape's own efficiency, ranked."""
    ranked = sorted(TYPES, key=lambda d: d.skin_per_floor)
    reveal = clamp(p * 1.35)
    spacing = 3.5
    worst = max(d.skin_per_floor for d in ranked)
    for index, dome in enumerate(ranked):
        if index / len(ranked) > reveal:
            continue
        x = (len(ranked) / 2.0 - index) * spacing
        height = 8.5 * (dome.skin_per_floor / worst)
        colour = GREEN if dome.skin_per_floor < 1.9 else AMBER
        opaque.box((x, 0.0, height * 0.5 + 0.2), (2.5, 1.6, max(0.06, height)),
                   colour)
        app.world_labels.append(WorldLabel(
            np.array([x, 0.0, height + 1.1]),
            f"{dome.skin_per_floor:.2f}", _rgb(colour)))
        if index in (0, len(ranked) - 1):
            app.world_labels.append(WorldLabel(
                np.array([x, 0.0, height + 2.4]),
                f"{dome.name.upper()}\n{dome.frequency}V", _rgb(WHITE)))
    app.world_labels.append(WorldLabel(
        np.array([0.0, 0.0, -1.8]),
        "square feet of envelope per square foot of floor -- lower is "
        "less to build, seal and heat", _rgb(MUTED)))


@lru_cache(maxsize=1)
def scale_trio() -> tuple[DomeType, ...]:
    """Three designs with the SAME parts list at genuinely different sizes.

    Sorting the catalogue by radius and taking three is not enough: two
    of the three-frequency presets are both five metres, so the shot
    came out showing the same building twice under a claim about size.
    Group by what the parts list actually is -- frequency and the counts
    it produces -- then take the family with the widest spread of
    distinct radii.
    """
    families: dict[tuple[int, int, int], list[DomeType]] = {}
    for dome in TYPES:
        key = (dome.frequency, dome.struts, dome.panels)
        families.setdefault(key, []).append(dome)

    best: list[DomeType] = []
    best_spread = 0.0
    for members in families.values():
        distinct: dict[float, DomeType] = {}
        for dome in sorted(members, key=lambda d: d.radius_m):
            distinct.setdefault(round(dome.radius_m, 3), dome)
        if len(distinct) < 3:
            continue
        picked = sorted(distinct.values(), key=lambda d: d.radius_m)
        chosen = [picked[0], picked[len(picked) // 2], picked[-1]]
        spread = chosen[-1].radius_m / chosen[0].radius_m
        if spread > best_spread:
            best, best_spread = chosen, spread
    if not best:
        # No family has three distinct sizes; fall back to three
        # distinct radii from the whole catalogue rather than repeating
        # a building.
        distinct = {}
        for dome in sorted(TYPES, key=lambda d: d.radius_m):
            distinct.setdefault(round(dome.radius_m, 3), dome)
        best = sorted(distinct.values(), key=lambda d: d.radius_m)[:3]
    return tuple(best)


def scene_world_scale(app, opaque, transparent, p: float) -> None:
    """The same parts list at three sizes, side by side."""
    chosen = list(scale_trio())
    cursor = 0.0
    spots = []
    for dome in chosen:
        cursor += dome.radius_m * 1.35
        spots.append(cursor)
        cursor += dome.radius_m * 1.35
    centre = cursor * 0.5
    for index, (dome, x) in enumerate(zip(chosen, spots)):
        reveal = clamp(p * 3.9 - index * 0.75)
        if reveal <= 0.02:
            continue
        origin = np.array([centre - x, 0.0, 0.0])
        _ground_disc(opaque, dome.name, origin=origin, reveal=reveal)
        _draw_dome(opaque, transparent, dome.name, origin=origin,
                   reveal=reveal, panels=False, hubs=False, segments=4)
        if reveal > 0.5:
            app.world_labels.append(WorldLabel(
                origin + np.array([0.0, 0.0, dome.height_ft / 3.281 + 1.5]),
                f"{dome.diameter_ft:.0f} FT\n{dome.floor_sqft:,.0f} sq ft",
                _rgb(CYAN)))
            app.world_labels.append(WorldLabel(
                origin + np.array([0.0, 0.0, -1.5]),
                f"{dome.struts} struts · {dome.panels} panels",
                _rgb(GREEN)))
    if p > 0.6:
        app.world_labels.append(WorldLabel(
            np.array([0.0, 0.0, -3.0]),
            "identical parts list, three different buildings",
            _rgb(WHITE)))


# ----------------------------------------------------------------------
# Scenes and chapters
# ----------------------------------------------------------------------

SCENES: dict = {
    "world_lineup": scene_world_lineup,
    "world_frequency": scene_world_frequency,
    "world_framing": scene_world_framing,
    "world_economics": scene_world_economics,
    "world_efficiency": scene_world_efficiency,
    "world_scale": scene_world_scale,
}

for _dome in TYPES:
    SCENES[f"world_show_{_dome.name}"] = _showcase_painter(_dome.name)


def _showcase_camera(dome: DomeType, yaw: float) -> tuple[float, float, float]:
    """Frame one design from its own size, with room for the label stack.

    The three labels sit up to 3.4 units above the dome's own height, so
    the distance has to clear the whole stack rather than just the shell.
    """
    return (yaw, 18.0, max(19.0, dome.radius_m * 3.1 + 7.0))


# What each design is for, in the builder's own terms. These are
# descriptions of the shipped presets, not claims about performance --
# every number the chapter states comes from the model.
SHOWCASE_COPY: dict[str, tuple[str, tuple[str, ...]]] = {
    "Timber Workshop": (
        "The default: a working shop you can actually afford to frame.",
        ("The one the tool opens on. Three frequency, five metre radius,",
         "dimensional lumber on metal brackets, plywood skin, concrete",
         "slab. It is a workshop: assembly bay, two wood shop wedges, a",
         "metal shop, storage and an office, with the benches and machines",
         "already placed. If you want to know what a dome costs as a",
         "building rather than as an idea, this is the honest starting",
         "point."),
    ),
    "Glass Studio Loft": (
        "Four frequency and glazed: the expensive, beautiful end.",
        ("Raise the frequency to four and the shell gets smoother, rounder",
         "and far more complicated. Two hundred and fifty struts in six",
         "length classes instead of sixty-five in two. Every one of those",
         "panels is glass on a wood deck. This is the design that shows you",
         "what smoothness costs: not in dollars first, but in part",
         "variety, which is the thing that actually slows a build down."),
    ),
    "Split-Log Homestead": (
        "Hubless, split from logs, and the cheapest floor in the catalogue.",
        ("This is the one this whole project argues for. Two frequency,",
         "hubless doubled framing, quarter wedges split from logs, cedar",
         "shakes over plywood. No hub connectors anywhere in it. Every",
         "triangle carries its own three boards and bolts to its",
         "neighbours, and the model reports the trees to harvest because",
         "four quarter wedges come out of one log."),
    ),
    "Whole Trunk Lodge - 20 ft": (
        "Whole trunks, scaled so the longest member is just under twenty feet.",
        ("Now go the other way and use the tree whole. The radius here is",
         "set so the longest member lands just under twenty feet, which is",
         "what you can actually move and lift. Sixty-five struts of full",
         "round trunk, canvas over the top. It is the largest floor in the",
         "catalogue by a wide margin, and it is framed from the fewest",
         "pieces of anything here."),
    ),
    "Grow Dome": (
        "Aluminium and polycarbonate: the greenhouse configuration.",
        ("Same three frequency skeleton as the workshop, but aluminium",
         "framed and glazed in polycarbonate, with grow racks and water",
         "storage inside. The geometry does not change at all. Only the",
         "material list does, which is exactly the argument: one frame,",
         "many buildings."),
    ),
    "Hex Cell Pavilion": (
        "A hexagonal cell frame in structural steel.",
        ("Not every dome in this world is triangulated the same way. The",
         "hex cell frame style groups the geometry into hexagonal cells on",
         "a structural steel frame with composite tiles, fitted out as a",
         "presentation space. It is heavier and dearer than the timber",
         "designs, and it looks like nothing else on the site."),
    ),
    "Continuous Steel Arc Hangar": (
        "Large curved ribs instead of straight struts.",
        ("The hangar swaps short straight struts for large curved steel",
         "ribs running continuously over the shell, with fabrication,",
         "access and site power equipment inside. Two frequency, eight",
         "metre radius. This is what the same geometry looks like when it",
         "is built by a steel shop instead of a carpenter."),
    ),
    "Rebar Garden Dome": (
        "A dense meridian-and-ring rebar lattice.",
        ("Rebar is the cheapest structural steel there is, and it bends.",
         "This design runs a dense lattice of it over the same three",
         "frequency shell, with water and climate equipment inside. It is",
         "a garden dome, and it is the configuration closest to what",
         "people actually build in a back yard on a weekend."),
    ),
    "Concrete Monocoque Form": (
        "The frame as formwork for a poured shell.",
        ("Here the frame is not the building. It is the formwork. Rebar and",
         "shuttering carry a poured concrete shell, with shoring, scaffold,",
         "a mixer and a rebar bender on the floor. The dome shape is doing",
         "the thing concrete is best at, which is standing in pure",
         "compression, and this is by some distance the heaviest thing in",
         "the catalogue."),
    ),
    "Woodland Hex Mirror": (
        "Hexagonal mirror tiles that reflect the site back at you.",
        ("The mirror designs exist because the renderer can do it: hex",
         "mirror tiles that genuinely reflect the procedural sky, the",
         "ground and the surrounding trunks. It is a pavilion that",
         "disappears into a wood. Structurally it is the same three",
         "frequency shell as the workshop."),
    ),
    "Woodland Square Mirror": (
        "The same trick at four frequency, on square tiles.",
        ("The square mirror variant raises the frequency to four on a",
         "structural steel frame. More panels, smaller ones, and a finer",
         "reflection. Between the two mirror designs you can see exactly",
         "what frequency does to a facetted surface: it stops looking like",
         "a machine and starts looking like a curve."),
    ),
    "Treehouse Canopy Dome": (
        "An elevated dome on a supported timber platform.",
        ("Last one, and the smallest. A two frequency hex tile dome sitting",
         "on an elevated timber platform with braces and ladder access.",
         "Six hundred square feet of floor, up in the canopy. It is proof",
         "that the same sixty-five stick frame works when the ground it",
         "stands on is not the ground."),
    ),
}


def _math(slug: str, title: str, promise: str, narration: tuple[str, ...],
          steps: tuple[str, ...], duration: float,
          camera: tuple[float, float, float], stage: str) -> Chapter:
    return Chapter(slug, "00", title, promise, narration, steps,
                   duration, camera, stage, "math")


_SHOW_CHAPTERS: list[Chapter] = []
for _index, _dome in enumerate(TYPES):
    _promise, _narration = SHOWCASE_COPY[_dome.name]
    _SHOW_CHAPTERS.append(Chapter(
        f"show_{_index:02d}", "00", _dome.name, _promise, _narration,
        (), 13.0,
        _showcase_camera(_dome, 34.0 + (_index % 4) * 16.0),
        f"world_show_{_dome.name}",
    ))


CHAPTERS: tuple[Chapter, ...] = (
    Chapter(
        "world_open", "00", "Every dome in the world",
        "Twelve designs. One geometry engine.",
        (
            "The Dome Creator is a walkable world with twelve finished",
            "designs already in it, and this film is all of them.",
            "Every dome you are about to see is rebuilt live from the same",
            "configuration the simulator loads when you press the Preset",
            "button, and every number beside it is read straight off that",
            "model. Nothing here is a drawing of a dome. It is the dome.",
        ),
        (), 15.0, (90.0, 14.0, LINEUP_SPAN * 0.94), "world_lineup",
    ),
    _math(
        "math_catalogue", "The catalogue, counted",
        "Twelve buildings, none of them typed in.",
        (
            "Start with the whole catalogue on one screen, because the",
            "spread is the point. The same engine produces a six hundred",
            "square foot treehouse dome and a three thousand square foot",
            "lodge, and the only thing that changed between them is a",
            "frequency, a radius and a material list.",
        ),
        steps_catalogue(), 24.0, (52.0, 16.0, LINEUP_SPAN * 0.62),
        "world_lineup",
    ),
) + tuple(_SHOW_CHAPTERS) + (
    Chapter(
        "ladder", "00", "What frequency actually costs",
        "One radius, four frequencies, all four built.",
        (
            "You have now seen one, two, three and four frequency domes.",
            "Here they are together at exactly the same radius, so the only",
            "difference on screen is the subdivision itself.",
            "Watch the gold line, which sits at one radius above the ground.",
            "That is where a true hemisphere would stop.",
        ),
        (), 15.0, (90.0, 13.0, 62.0), "world_frequency",
    ),
    _math(
        "math_frequency", "Frequency, and where the dome gets cut",
        "Even frequencies stop at the equator. Odd ones do not.",
        (
            "Raising the frequency buys a smoother shell and charges you in",
            "part variety: twenty-five struts in one length becomes two",
            "hundred and fifty in six.",
            "But there is a second effect almost nobody mentions, and the",
            "model shows it plainly. An even frequency puts a ring of hubs",
            "exactly on the equator, so the dome stops at half a sphere and",
            "its height equals its radius. An odd frequency has no such",
            "ring, so the cut lands above the equator and the building",
            "stands taller than a hemisphere, carrying extra skin you did",
            "not ask for.",
        ),
        steps_frequency(), 26.0, (90.0, 13.0, 62.0), "world_frequency",
    ),
    Chapter(
        "framing", "00", "Hubs, or no hubs",
        "Two real designs, two completely different framing systems.",
        (
            "Two of these designs are the same frequency and could not be",
            "more different to build. On one side, hub and strut: sixty-five",
            "sticks meeting at twenty-six connectors. On the other, hubless",
            "doubled: every triangle brings its own three boards and bolts",
            "straight to its neighbours, so there is no hub in the building",
            "at all.",
        ),
        (), 14.0, (90.0, 14.0, 34.0), "world_framing",
    ),
    _math(
        "math_framing", "The trade, counted",
        "More wood, zero hubs, nothing you cannot cut yourself.",
        (
            "Here is that trade as arithmetic, off both real models.",
            "The hubless frame carries nearly twice the sticks. In exchange",
            "it needs exactly zero hub connectors, which is the part you",
            "would otherwise have to weld, buy or wait for. And because its",
            "struts are quarter wedges split from logs, the model even",
            "reports the trees, at four wedges to a log.",
        ),
        steps_hub_vs_hubless(), 24.0, (90.0, 14.0, 34.0), "world_framing",
    ),
    Chapter(
        "cladding", "00", "The skin decides the price",
        "Same geometry, wildly different bills.",
        (
            "Now price all twelve. What is striking is not that they differ.",
            "It is where the difference comes from. The frames are close",
            "cousins. The cladding is not: plywood, glass, canvas,",
            "polycarbonate, composite tile, poured concrete.",
        ),
        (), 13.0, (90.0, 15.0, 46.0), "world_economics",
    ),
    _math(
        "math_economics", "Every design, priced",
        "The shape is cheap. The skin is what costs.",
        (
            "Every bar you just saw comes off that design's own bill of",
            "materials: frame, hubs, panels, cladding layers, foundation and",
            "fit-out. The spread across the catalogue is large, and almost",
            "all of it is the covering rather than the structure.",
            "That is genuinely good news, because the covering is the",
            "decision you can defer, stage, or upgrade later. The frame is",
            "the one you have to get right on day one.",
        ),
        steps_economics(), 26.0, (90.0, 15.0, 46.0), "world_economics",
    ),
    Chapter(
        "efficiency", "00", "The cheapest wall is the one you never build",
        "Envelope per square foot of floor, ranked.",
        (
            "One more comparison, and it is the one the whole shape is for.",
            "For every square foot of floor, how many square feet of",
            "outside do you have to build, seal, insulate and heat? Lower is",
            "better, and the spread here is set by the geometry, not by",
            "what is bolted to it.",
        ),
        (), 13.0, (90.0, 15.0, 46.0), "world_efficiency",
    ),
    _math(
        "math_efficiency", "Envelope per floor, measured",
        "Geometry decides this one, not materials.",
        (
            "The best and worst designs in the catalogue differ by a wide",
            "margin on this measure, and every one of them is a dome. The",
            "driver is frequency and where the shell gets cut, which is the",
            "same parity effect you saw on the gold line.",
            "It is worth knowing before you choose a frequency, because",
            "this number follows you for the whole life of the building.",
        ),
        steps_efficiency(), 24.0, (90.0, 15.0, 46.0), "world_efficiency",
    ),
    Chapter(
        "scale", "00", "Size is a number you type",
        "The same parts list at three different sizes.",
        (
            "And here is why this is a product rather than a craft. These",
            "three designs are all two frequency, so all three have exactly",
            "sixty-five struts and forty panels. The smallest is a twenty-",
            "eight foot treehouse dome. The largest is a sixty-five foot",
            "lodge with five and a half times the floor. The sticks get",
            "longer. The list of operations does not change at all.",
        ),
        (), 14.0, (90.0, 14.0, 44.0), "world_scale",
    ),
    _math(
        "math_scale", "Scale, proved on the catalogue",
        "More house for the same list of operations.",
        (
            "Part counts depend on frequency alone. Never on size. So the",
            "largest dome in this world has several times the floor of the",
            "smallest, off an identical set of repeated operations.",
            "That is the entire economic argument for this shape, and you",
            "can check it yourself in the tool in about a minute: load a",
            "preset, change the radius slider, and watch the part counts",
            "stay exactly where they were.",
        ),
        steps_scale(), 24.0, (90.0, 14.0, 44.0), "world_scale",
    ),
    Chapter(
        "world_close", "00", "Open the tool and check every number",
        "Load the preset. Read the bill of materials.",
        (
            "That is the whole world: twelve designs, four frequencies, six",
            "framing systems, and one geometry engine underneath all of it.",
            "Nothing in this film was asserted. Every count, every area and",
            "every dollar was read off a model that this video rebuilt while",
            "it was rendering, from the same presets the tool ships with.",
            "So do not take my word for any of it. Open the Dome Creator,",
            "press the Preset button until you reach the one you want, and",
            "read the bill of materials. It will say what this film said.",
        ),
        (), 16.0, (90.0, 14.0, LINEUP_SPAN * 0.94), "world_lineup",
    ),
)


CHAPTERS = tuple(
    replace(chapter, number=f"{index + 1:02d}")
    for index, chapter in enumerate(CHAPTERS)
)


def validate_world_lesson() -> None:
    """Prove the lesson draws every design and states nothing extra."""
    from .render_kit import TriangleBatch

    validate_world_facts()

    lesson = WORLD_LESSON
    slugs = [chapter.slug for chapter in lesson.chapters]
    assert len(set(slugs)) == len(slugs), "duplicate slug"

    for chapter in lesson.chapters:
        assert chapter.stage in lesson.scenes, (chapter.slug, chapter.stage)
        assert chapter.narration, chapter.slug
        if chapter.overlay == "math":
            assert len(chapter.equations) >= 5, chapter.slug
            assert len(chapter.equations[-1]) >= 30, chapter.slug

    # Every shipped design gets its own chapter -- the film claims to be
    # all of them, so a preset added later must not silently go unshown.
    shown = {chapter.stage for chapter in lesson.chapters}
    for dome in TYPES:
        assert f"world_show_{dome.name}" in shown, dome.name

    # Every math screen the facts module offers is used exactly once.
    used = {chapter.equations for chapter in lesson.chapters
            if chapter.overlay == "math"}
    offered = {builder() for _, builder in ALL_SCREENS}
    assert used == offered, (
        f"{len(offered - used)} unused, {len(used - offered)} unknown")

    class _App:
        def __init__(self):
            self.world_labels = []

    # Each painter must draw real geometry and label it, at every phase.
    for stage, painter in lesson.scenes.items():
        if not stage.startswith("world_"):
            continue
        for progress in (0.0, 0.4, 0.75, 1.0):
            probe = _App()
            opaque, transparent = TriangleBatch(), TriangleBatch()
            painter(probe, opaque, transparent, progress)
            if progress > 0.0:
                assert opaque.vertices, (stage, progress)
            for label in probe.world_labels:
                assert label.text.strip(), (stage, progress)

    # The scale shot claims three different sizes off one parts list, so
    # the three must genuinely differ in size and genuinely agree on
    # parts. Picking the three smallest once put the same building on
    # screen twice under a caption about size.
    trio = scale_trio()
    assert len(trio) == 3, trio
    radii = [round(dome.radius_m, 3) for dome in trio]
    assert len(set(radii)) == 3, radii
    assert len({(d.frequency, d.struts, d.panels) for d in trio}) == 1, trio
    assert trio[-1].floor_sqft / trio[0].floor_sqft > 2.0, radii

    # A showcase must draw the design it names, not a stand-in: the
    # strut count on screen has to match the model's own.
    for dome in TYPES:
        probe = _App()
        opaque = TriangleBatch()
        lesson.scenes[f"world_show_{dome.name}"](
            probe, opaque, TriangleBatch(), 1.0)
        text = " ".join(label.text for label in probe.world_labels)
        assert f"{dome.struts} struts" in text, (dome.name, text[:120])
        assert dome.name.upper() in text, dome.name


_WORLD_BASE = Lesson(
    key="world",
    brand="DOME CREATOR / EVERY DESIGN",
    title="Every Dome In The World",
    chapters=CHAPTERS,
    scenes=SCENES,
    selftest=validate_world_lesson,
    report=world_report,
    snapshot_prefix="world",
    style="hype",
    voice_rate="+4%",
    label_layout="declutter",
)

WORLD_LESSON = compose(_WORLD_BASE)
