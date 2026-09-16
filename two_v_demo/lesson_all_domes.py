"""All domes: the Dome Creator's whole catalogue, and every menu in it.

There is already a film about the twelve shipped presets.  It rebuilt their
geometry and then re-drew it with the film engine's own primitives -- tubes for
struts, flat translucent triangles for panels -- because that was the only thing
the renderer could draw.  So the presets were in a film, but the *product* never
was: no wood grain, no glass, no mirror tiles reflecting a tree line, no cedar
shakes, no wood deck or treehouse platform, no partition walls, no benches,
lamps, conduit or plumbing, and no way to look inside.

This film draws the buildings with :mod:`two_v_demo.creator_bridge`, which hands
the renderer the tool's own finished meshes and runs them through the tool's own
shader.  Every dome on screen is the thing the Dome Creator renders when you
press its Preset button, assembled in the order its construction record says,
and every number beside it is read off the same model that produced the picture.

The second half is the part the title promises: every menu in the customizer,
swept one setting at a time, and then the arithmetic of how many buildings that
adds up to -- with the honest deduction for settings that do nothing, and the
honest admission that a film cannot show sixteen billion of anything.
"""

from __future__ import annotations

import math
from dataclasses import replace
from functools import lru_cache

import numpy as np

from . import creator_bridge as creator
from .creator_facts import (
    ALL_SCREENS,
    BASE_DESIGN,
    FITOUT_DESIGN,
    axis,
    design_rows,
    dials,
    distinct_shells,
    frame_style_rows,
    random_designs,
    price_swings,
    shell_permutations,
    steps_catalogue,
    steps_construction,
    steps_dials,
    steps_fitout,
    steps_frame_styles,
    steps_inputs,
    steps_permutations,
    steps_price_drivers,
    validate_creator_facts,
    wired_variant,
    years_to_watch,
    creator_report,
)
from .lessons import Chapter, Lesson
from .render_kit import (
    AMBER,
    CYAN,
    GREEN,
    MUTED,
    PURPLE,
    WHITE,
    WorldLabel,
    clamp,
    ease_in_out,
)


FT_PER_M = 3.280839895
SQFT_PER_SQM = 10.7639104

SWEEP_RADIUS = 3.2
"""Radius every sweep dome is built at.

The sweeps compare one menu at a time, so every dome in them is the same size:
what changes on screen is the setting and nothing else.  Small enough that
sixteen of them fit in one frame without the camera leaving the renderer's far
plane behind."""

ROW_RADIUS = 4.0
"""Radius for the sweeps that fit in a single row, where there is more room."""

WEDGE_OUT_LABEL = "Quarter Wedge, curve out"
"""The ninth stand in the strut-shape sweep.

The wedge curve menu bends exactly one of the eight shapes, so it gets its own
dome beside that shape rather than being the one setting the film skips."""


def _rgb(colour) -> tuple[int, int, int]:
    return tuple(int(round(channel * 255)) for channel in colour[:3])


# ----------------------------------------------------------------------
# Configurations
# ----------------------------------------------------------------------

@lru_cache(maxsize=1)
def _presets() -> tuple[tuple[str, dict], ...]:
    return creator.presets_all()


@lru_cache(maxsize=32)
def _preset_config(name: str) -> dict:
    for preset_name, data in _presets():
        if preset_name == name:
            return data
    raise KeyError(name)


def _sweep_base(radius: float = SWEEP_RADIUS) -> dict:
    """The design every sweep varies from: the tool's default, unfurnished.

    The equipment comes out for the sweeps on purpose.  A row of eight domes is
    about the shells; a floor of benches at that size is noise, and the fit-out
    gets a chapter of its own.
    """
    config = dict(_preset_config(BASE_DESIGN))
    config["props"] = []
    config["radius"] = radius
    return config


def _variant(radius: float = SWEEP_RADIUS, **changes) -> dict:
    config = _sweep_base(radius)
    config.update(changes)
    return config


# ----------------------------------------------------------------------
# Placing buildings on the stage
# ----------------------------------------------------------------------

def _footprint(config: dict) -> float:
    return float(config.get("radius", 5.0)) * float(
        config.get("foundation_scale", 1.15))


def _row(items: tuple[tuple[str, dict], ...], gap: float = 1.18,
         y: float = 0.0) -> tuple[tuple, float]:
    """Lay labelled designs left to right, each given its own footprint."""
    cursor = 0.0
    placed = []
    for label, config in items:
        half = _footprint(config) * gap
        cursor += half
        placed.append((label, config, cursor, y))
        cursor += half
    span = cursor
    # +X is screen left at these cameras, so mirroring about the centre makes
    # the sweep read left to right on film.
    return tuple((label, config, span * 0.5 - x, y)
                 for label, config, x, y in placed), span


def _grid(items: tuple[tuple[str, dict], ...], columns: int,
          gap: float = 1.18) -> tuple[tuple, float, float]:
    """The same, in rows, with the first row nearest the camera."""
    rows = [items[index:index + columns]
            for index in range(0, len(items), columns)]
    depth = max(_footprint(config) for _, config in items) * 2.5
    placed: list = []
    spans = []
    for index, row in enumerate(rows):
        offset = (len(rows) - 1) / 2.0 - index
        laid, span = _row(tuple(row), gap, depth * offset)
        placed.extend(laid)
        spans.append(span)
    return tuple(placed), max(spans), depth * max(1, len(rows) - 1)


def _screen_left(app) -> np.ndarray:
    """The world direction that reads as leftward at this chapter's camera."""
    yaw = math.radians(float(getattr(app, "camera_yaw", 90.0)))
    return np.array([math.sin(yaw), -math.cos(yaw), 0.0])


def _shift(app) -> np.ndarray:
    """Where this chapter's stage stands, given what the overlay is using.

    A math chapter spends the right half of the frame on its worksheet, so a
    stage composed for the whole frame comes back sliced down the middle.
    Everything in one of those chapters moves left by a share of the camera's
    own distance, which holds the composition at every chapter's camera rather
    than needing a hand-set offset per shot.
    """
    chapter = app.chapters[app.chapter_index]
    if (chapter.overlay or "") != "math":
        return np.zeros(3)
    distance = float(getattr(app, "camera_distance", 40.0))
    return _screen_left(app) * distance * 0.27


def _stage(app, stands, *, reveal: float = 1.0, cut: float | None = None,
           stagger: float = 0.9, caption=None, colour=CYAN,
           sub=None, sub_colour=MUTED, lift: float = 1.5,
           step: float = 1.35) -> None:
    """Draw a laid-out set of buildings, each rising in its own build order.

    ``reveal`` walks every dome through the tool's construction record rather
    than fading it in: the shells assemble themselves, foundation first, in the
    order the Creator's own crew would work.

    Labels alternate between two heights along a row.  Sixteen domes side by
    side have names wider than the gaps between them, and a single label line
    turns into one unreadable band; two lines of them read cleanly.
    """
    shift = _shift(app)
    if shift.any() and len(stands) > 3:
        # A worksheet chapter has half a frame for its picture, and sixteen
        # domes squeezed into it are sixteen smudges. Show three of them --
        # the ends and the middle -- re-laid on their own.
        picked = (stands[0], stands[len(stands) // 2], stands[-1])
        stands, _span = _row(tuple((label, config)
                                   for label, config, _x, _y in picked))
    count = max(1, len(stands))
    for index, (label, config, x, y) in enumerate(stands):
        grown = clamp(reveal * (count + 2.0) - index * stagger)
        if grown <= 0.02:
            continue
        build = creator.build(config, label)
        limits = None if grown >= 0.999 else build.phase(grown)["limits"]
        point = np.array([float(x), float(y), 0.0]) + shift
        creator.draw(app, build, offset=tuple(point), limits=limits,
                     cut_z=cut)
        top = build.apex + lift + (index % 2) * step
        text = caption(label, build) if caption else label.upper()
        if text:
            app.world_labels.append(WorldLabel(
                np.array([point[0], point[1], top]), text, _rgb(colour)))
        if sub is not None:
            line = sub(label, build)
            if line:
                app.world_labels.append(WorldLabel(
                    np.array([point[0], point[1], top - 1.15]), line,
                    _rgb(sub_colour)))


# ----------------------------------------------------------------------
# The catalogue
# ----------------------------------------------------------------------

@lru_cache(maxsize=1)
def _catalogue_layout():
    items = _presets()
    half = (len(items) + 1) // 2
    return _grid(tuple(items), half)


def scene_lineup(app, opaque, transparent, p: float) -> None:
    """All twelve shipped designs, at true relative size, building themselves."""
    stands, span, depth = _catalogue_layout()
    _stage(app, stands, reveal=clamp(p * 1.15), stagger=0.75,
           caption=lambda label, build: label.upper(),
           sub=lambda label, build: f"{build.radius * 2 * FT_PER_M:.0f} FT",
           lift=2.0)
    if p > 0.55:
        rows = design_rows()
        smallest = min(rows, key=lambda row: row.floor_sqft)
        largest = max(rows, key=lambda row: row.floor_sqft)
        # These two ride with the stage: in a worksheet chapter the stage has
        # moved left and shrunk to three domes, so the banner comes down with
        # it rather than floating off the top of the frame.
        shift = _shift(app)
        head = 11.0 if shift.any() else 19.0
        app.world_labels.extend([
            WorldLabel(np.array([shift[0], shift[1], head]),
                       f"{len(rows)} DESIGNS, DRAWN BY THE TOOL THAT BUILDS THEM",
                       _rgb(WHITE)),
            WorldLabel(np.array([shift[0], shift[1], head - 2.4]),
                       f"{smallest.floor_sqft:,.0f} to {largest.floor_sqft:,.0f} "
                       "square feet, at true relative size", _rgb(MUTED)),
        ])


def _showcase(name: str):
    """One design: raised in its own build order, then opened up."""
    config = _preset_config(name)

    def painter(app, opaque, transparent, p: float) -> None:
        build = creator.build(config, name)
        stats = build.stats
        raise_to = clamp(p / 0.45)
        limits = None if raise_to >= 0.999 else build.phase(raise_to)["limits"]
        # The roof comes off in the last third, because the fit-out is half of
        # what the tool actually models and no exterior shot will ever show it.
        cut = None
        if p > 0.62:
            open_by = ease_in_out(clamp((p - 0.62) / 0.22))
            floor = build.apex - build.height + 2.05
            cut = build.apex - (build.apex - floor) * open_by
        creator.draw(app, build, limits=limits, cut_z=cut)

        top = build.apex + 2.6
        app.world_labels.append(WorldLabel(
            np.array([0.0, 0.0, top]),
            f"{name.upper()}\n{stats['frequency']}V  ·  "
            f"{build.radius * 2 * FT_PER_M:.0f} FT ACROSS  ·  "
            f"{stats['floor_area'] * SQFT_PER_SQM:,.0f} SQ FT",
            _rgb(CYAN)))
        if p > 0.22:
            app.world_labels.append(WorldLabel(
                np.array([0.0, 0.0, top - 1.5]),
                f"{stats['strut_count']} struts  ·  {stats['panel_count']} "
                f"{build.model.config.default_panel.lower()} panels  ·  "
                f"{stats['hub_count']} hubs  ·  {stats['bolt_count']} bolts",
                _rgb(WHITE)))
        if p > 0.40:
            app.world_labels.append(WorldLabel(
                np.array([0.0, 0.0, top - 2.7]),
                f"{stats['foundation_name'].lower()}  ·  "
                f"{stats['structure_weight']:,.0f} kg  ·  "
                f"${stats['total_cost']:,.0f}",
                _rgb(AMBER)))
        if p > 0.62 and stats["prop_count"]:
            app.world_labels.append(WorldLabel(
                np.array([0.0, 0.0, top - 3.9]),
                f"inside: {stats['prop_count']} pieces of equipment  ·  "
                f"{stats['wall_count']} partition walls  ·  "
                f"{build.hours:,.0f} hours of work",
                _rgb(GREEN)))
    return painter


def scene_hero(app, opaque, transparent, p: float) -> None:
    """The default design, whole, for the screens that quote its numbers."""
    build = creator.build(_preset_config(BASE_DESIGN), BASE_DESIGN)
    shift = _shift(app)
    cut = None
    if p > 0.5:
        cut = build.apex - (build.apex - 2.05) * ease_in_out(
            clamp((p - 0.5) / 0.3))
    creator.draw(app, build, offset=tuple(shift), cut_z=cut)
    app.world_labels.append(WorldLabel(
        np.array([shift[0], shift[1], build.apex + 1.8]),
        f"{BASE_DESIGN.upper()}  ·  ${build.stats['total_cost']:,.0f}",
        _rgb(CYAN)))


# ----------------------------------------------------------------------
# One dome, built the way the tool builds it
# ----------------------------------------------------------------------

def scene_build(app, opaque, transparent, p: float) -> None:
    """The construction record, played: every work step, in order, with hours."""
    build = creator.build(_preset_config(BASE_DESIGN), BASE_DESIGN)
    shift = _shift(app)
    phase = build.phase(clamp(p * 1.02))
    creator.draw(app, build, offset=tuple(shift), limits=phase["limits"])

    # Where the crew is standing for this step, marked on the floor, because
    # the record carries a work station for every one of them.
    station = np.asarray(phase["position"], dtype=float) + shift
    for index in range(24):
        a = math.tau * index / 24
        b = math.tau * (index + 1) / 24
        radius = 0.55
        opaque.cylinder(
            station + np.array([radius * math.cos(a), radius * math.sin(a), 0.02]),
            station + np.array([radius * math.cos(b), radius * math.sin(b), 0.02]),
            0.035, AMBER, 5)

    top = build.apex + 2.2
    app.world_labels.extend([
        WorldLabel(np.array([shift[0], shift[1], top]),
                   f"STEP {phase['index'] + 1} OF {phase['steps']}",
                   _rgb(WHITE)),
        WorldLabel(np.array([shift[0], shift[1], top - 1.2]), phase["label"],
                   _rgb(CYAN)),
        WorldLabel(np.array([shift[0], shift[1], top - 2.3]),
                   f"{phase['hours']:,.1f} hours of work so far, of "
                   f"{build.hours:,.0f}", _rgb(AMBER)),
    ])


# ----------------------------------------------------------------------
# The sweeps: one menu at a time
# ----------------------------------------------------------------------

@lru_cache(maxsize=1)
def _frequency_layout():
    items = tuple((f"{value}V", _variant(ROW_RADIUS, frequency=value))
                  for value in range(1, 5))
    return _row(items)


def scene_frequency(app, opaque, transparent, p: float) -> None:
    """One radius, four subdivisions, all four built."""
    stands, span = _frequency_layout()
    _stage(app, stands, reveal=clamp(p * 1.2), stagger=0.7,
           caption=lambda label, build: label,
           sub=lambda label, build: (
               f"{build.stats['strut_count']} struts  ·  "
               f"{len(build.stats['strut_classes'])} lengths  ·  "
               f"{build.stats['panel_count']} panels"))
    if p > 0.5:
        app.world_labels.append(WorldLabel(
            np.array([0.0, 0.0, 12.0]),
            f"same {ROW_RADIUS:.1f} m radius, four frequencies", _rgb(MUTED)))


@lru_cache(maxsize=1)
def _style_layout():
    values = axis("Frame style").values
    items = tuple((label, _variant(ROW_RADIUS, frame_style=value))
                  for label, value in values)
    return _row(items)


def scene_styles(app, opaque, transparent, p: float) -> None:
    """Six ways to join the same sticks."""
    stands, span = _style_layout()
    rows = {row.name: row for row in frame_style_rows()}

    def sub(label, build):
        row = rows.get(label)
        if row is None:
            return ""
        return (f"{row.struts} struts  ·  {row.hubs_built} hubs fitted  ·  "
                f"{row.bolts} bolts")

    _stage(app, stands, reveal=clamp(p * 1.2), stagger=0.6,
           caption=lambda label, build: label.upper(), sub=sub)


@lru_cache(maxsize=1)
def _shape_layout():
    values = axis("Strut shape").values
    items = tuple((label, _variant(SWEEP_RADIUS, strut_shape=value,
                                   strut_width=0.09))
                  for label, value in values)
    # The wedge curve menu is the one setting that only means something on one
    # of these shapes, so the ninth stand is the quarter wedge turned the other
    # way -- otherwise the film would claim every setting and skip that one.
    items += ((WEDGE_OUT_LABEL,
               _variant(SWEEP_RADIUS, strut_shape="Quarter Wedge",
                        strut_width=0.09, wedge_flip=True)),)
    return _grid(items, 3)


def scene_shapes(app, opaque, transparent, p: float) -> None:
    """Every cross section the tool can cut a member to."""
    stands, span, depth = _shape_layout()
    sim = creator.simulator()
    shapes = {shape.name: shape for shape in sim["materials"].STRUT_SHAPES}

    def sub(label, build):
        if label == WEDGE_OUT_LABEL:
            return "bark turned outward"
        shape = shapes[label]
        area = shape.cross_section_area(0.09) * 1e4
        return f"{shape.kind}  ·  {area:.0f} cm2"

    _stage(app, stands, reveal=clamp(p * 1.25), stagger=0.5,
           caption=lambda label, build: label.upper(), sub=sub, lift=1.2)


@lru_cache(maxsize=1)
def _material_layout():
    values = axis("Frame material").values
    items = tuple((label, _variant(SWEEP_RADIUS, frame_material=value))
                  for label, value in values)
    return _grid(items, 4)


def scene_materials(app, opaque, transparent, p: float) -> None:
    """The same frame, in all eight materials, priced and weighed."""
    stands, span, depth = _material_layout()
    _stage(app, stands, reveal=clamp(p * 1.25), stagger=0.5,
           caption=lambda label, build: label.upper(),
           sub=lambda label, build: (
               f"{build.stats['frame_weight']:,.0f} kg  ·  "
               f"${build.stats['frame_cost']:,.0f}"),
           lift=1.2)


@lru_cache(maxsize=1)
def _colour_layout():
    frame_values = axis("Frame colour").values
    panel_values = axis("Panel colour").values
    items = tuple(
        (f"FRAME · {label}", _variant(SWEEP_RADIUS, frame_color=value))
        for label, value in frame_values
    ) + tuple(
        (f"PANEL · {label}", _variant(SWEEP_RADIUS, panel_color=value))
        for label, value in panel_values
    )
    return _grid(items, 4)


def scene_colours(app, opaque, transparent, p: float) -> None:
    """Sixteen finishes: eight on the frame, eight on the skin."""
    stands, span, depth = _colour_layout()
    _stage(app, stands, reveal=clamp(p * 1.3), stagger=0.35,
           caption=lambda label, build: label,
           colour=AMBER, sub=None, lift=1.0)


@lru_cache(maxsize=1)
def _panel_layout():
    values = axis("Panel type").values
    items = tuple((label, _variant(SWEEP_RADIUS, default_panel=value))
                  for label, value in values)
    return _grid(items, 4)


def scene_panels(app, opaque, transparent, p: float) -> None:
    """Every panel type, on the same shell."""
    stands, span, depth = _panel_layout()
    sim = creator.simulator()
    panels = {panel.name: panel for panel in sim["materials"].PANEL_TYPES}

    def sub(label, build):
        panel = panels[label]
        if panel.cost_per_m2 <= 0.0:
            return "no panel at all"
        return f"${panel.cost_per_m2:,.0f}/m2"

    _stage(app, stands, reveal=clamp(p * 1.3), stagger=0.35,
           caption=lambda label, build: label.upper(), sub=sub, lift=1.2)


@lru_cache(maxsize=1)
def _layer_layout():
    values = axis("Cladding layer").values
    items = tuple((label, _variant(SWEEP_RADIUS, layers=value))
                  for label, value in values)
    return _grid(items, 3)


def scene_layers(app, opaque, transparent, p: float) -> None:
    """The nine cladding layers, over the same sheathing."""
    stands, span, depth = _layer_layout()
    _stage(app, stands, reveal=clamp(p * 1.3), stagger=0.4,
           caption=lambda label, build: label.upper(),
           sub=lambda label, build: (
               "no layer" if not build.stats["layer_rows"] else
               f"{build.stats['layer_rows'][0][1]:.0f} m2  ·  "
               f"${build.stats['layer_cost']:,.0f}"),
           lift=1.2)


@lru_cache(maxsize=1)
def _foundation_layout():
    values = axis("Foundation").values
    items = tuple((label, _variant(SWEEP_RADIUS, foundation=value))
                  for label, value in values)
    return _grid(items, 4)


def scene_foundations(app, opaque, transparent, p: float) -> None:
    """What the same dome can stand on."""
    stands, span, depth = _foundation_layout()
    _stage(app, stands, reveal=clamp(p * 1.25), stagger=0.45,
           caption=lambda label, build: label.upper(),
           sub=lambda label, build: (
               "no pad" if build.stats["foundation_area"] <= 0.0 else
               f"{build.stats['foundation_area']:.0f} m2  ·  "
               f"${build.stats['foundation_cost']:,.0f}"),
           lift=1.2)


@lru_cache(maxsize=1)
def _floor_layout():
    values = axis("Partitions").values
    items = tuple((label, _variant(ROW_RADIUS, partitions=value))
                  for label, value in values)
    return _row(items)


def scene_floor(app, opaque, transparent, p: float) -> None:
    """The four partition modes, with the roofs off."""
    stands, span = _floor_layout()
    def sub(label, build):
        walls = build.stats["wall_count"]
        if walls:
            return (f"{walls} walls  ·  {build.stats['wall_area']:.0f} m2  ·  "
                    f"${build.stats['wall_cost']:,.0f}")
        # No walls means one of two different things, and saying "markings"
        # under the mode that draws nothing would be a caption that lies.
        return ("painted on the slab" if label == "Markings"
                else "no divisions at all")

    _stage(app, stands, reveal=clamp(p * 1.3), stagger=0.5, cut=2.4,
           caption=lambda label, build: label.upper(), sub=sub, lift=0.9)


def scene_fitout(app, opaque, transparent, p: float) -> None:
    """The equipment, the walls, the pipe -- and then the conduit."""
    shift = _shift(app)
    # As the tool ships it first; then the same dome with a power source added,
    # because a wiring run has to start somewhere and no shipped design gives
    # it anywhere to start.
    powered = p > 0.58
    config = wired_variant() if powered else _preset_config(FITOUT_DESIGN)
    name = f"{FITOUT_DESIGN} + power" if powered else FITOUT_DESIGN
    build = creator.build(config, name)
    stats = build.stats
    creator.draw(app, build, offset=tuple(shift), cut_z=build.apex - 2.1)

    groups = sorted(stats["prop_groups"].items(),
                    key=lambda item: -item[1]["cost"])[:6]
    shown = max(1, int(clamp(p * 1.9) * len(groups)))
    for index, (item, group) in enumerate(groups[:shown]):
        app.world_labels.append(WorldLabel(
            np.array([shift[0], shift[1], build.apex + 1.4 + index * 0.95]),
            f"{group['count']} x {item}  ·  ${group['cost']:,.0f}",
            _rgb(WHITE if index % 2 else CYAN)))
    if p > 0.32:
        app.world_labels.append(WorldLabel(
            np.array([shift[0], shift[1], 1.4]),
            f"{stats['wall_count']} framed walls  ·  "
            f"{stats['pipe_fixtures']} plumbed fixtures, "
            f"{stats['pex_len']:.0f} m of PEX", _rgb(GREEN)))
    if powered:
        app.world_labels.append(WorldLabel(
            np.array([shift[0], shift[1], 0.4]),
            f"battery bank added  ·  {stats['wire_runs']} conduit runs, "
            f"{stats['wire_len']:.0f} m of wire", _rgb(AMBER)))


@lru_cache(maxsize=1)
def _random_layout():
    designs = random_designs(RANDOM_SEED, 8)
    items = []
    for index, config in enumerate(designs):
        config = dict(config)
        config["radius"] = SWEEP_RADIUS
        config["props"] = []
        items.append((f"draw {index + 1}", config))
    return _grid(tuple(items), 4)


RANDOM_SEED = 7


def scene_random(app, opaque, transparent, p: float) -> None:
    """Eight buildings the dice picked out of the whole option space."""
    stands, span, depth = _random_layout()

    def caption(label, build):
        config = build.config
        return (f"{config['frame_style'].upper()}\n"
                f"{config['default_panel'].lower()} on "
                f"{config['frame_material'].lower()}")

    _stage(app, stands, reveal=clamp(p * 1.25), stagger=0.45,
           caption=caption,
           sub=lambda label, build: (
               f"{build.stats['frequency']}V  ·  "
               f"{build.stats['foundation_name'].lower()}  ·  "
               f"${build.stats['total_cost']:,.0f}"),
           lift=1.6)
    if p > 0.45:
        app.world_labels.append(WorldLabel(
            np.array([0.0, 0.0, 11.6]),
            f"eight of {distinct_shells():,}, drawn with seed {RANDOM_SEED}",
            _rgb(MUTED)))


SCENES: dict = {
    "ad_lineup": scene_lineup,
    "ad_hero": scene_hero,
    "ad_build": scene_build,
    "ad_frequency": scene_frequency,
    "ad_styles": scene_styles,
    "ad_shapes": scene_shapes,
    "ad_materials": scene_materials,
    "ad_colours": scene_colours,
    "ad_panels": scene_panels,
    "ad_layers": scene_layers,
    "ad_foundations": scene_foundations,
    "ad_floor": scene_floor,
    "ad_fitout": scene_fitout,
    "ad_random": scene_random,
}

for _name, _ in _presets():
    SCENES[f"ad_show_{_name}"] = _showcase(_name)


# ----------------------------------------------------------------------
# Chapters
# ----------------------------------------------------------------------

def _math(slug: str, title: str, promise: str, narration: tuple[str, ...],
          steps: tuple[str, ...], duration: float,
          camera: tuple[float, float, float], stage: str) -> Chapter:
    return Chapter(slug, "00", title, promise, narration, steps, duration,
                   camera, stage, "math")


def _showcase_camera(config: dict) -> tuple[float, float, float]:
    radius = float(config.get("radius", 5.0))
    return (18.0, max(21.0, radius * 3.2 + 8.0))


SHOWCASE_COPY: dict[str, tuple[str, tuple[str, ...]]] = {
    "Timber Workshop": (
        "The one the tool opens on, and the one every sweep starts from.",
        ("Dimensional lumber on metal brackets, plywood between the struts, a",
         "concrete slab under all of it, and a working shop on the floor:",
         "benches, a machine station, a tool chest, shelving, an office corner.",
         "Watch what happens when the roof comes off. That equipment is not",
         "set dressing. Every piece has a weight, a price and a power draw in",
         "the model, and the wiring on the floor was routed to reach it."),
    ),
    "Glass Studio Loft": (
        "Four frequency, glazed, on a deck: the expensive, beautiful end.",
        ("Raise the frequency and the shell gets rounder and much more",
         "complicated: two hundred and fifty struts instead of a hundred and",
         "sixty five. Every panel here is glass, which is why you can see the",
         "furniture through the wall, and why the shader is putting a highlight",
         "on the panels facing the sun. It stands on a wood deck rather than a",
         "slab."),
    ),
    "Split-Log Homestead": (
        "Hubless, framed from split logs, cedar shakes over the top.",
        ("This is the design this whole project argues for. Two frequency,",
         "hubless doubled framing, quarter wedges split straight from logs.",
         "There is not one hub connector in the building. Every triangle brings",
         "its own three members and bolts to its neighbours, and the cedar",
         "shakes you can see are a cladding layer sitting over the sheathing,",
         "not a texture painted on it."),
    ),
    "Whole Trunk Lodge - 20 ft": (
        "Whole trunks, sized so the longest member is just under twenty feet.",
        ("Now use the tree whole. The radius is set so the longest member lands",
         "just under twenty feet, which is what two people can actually move.",
         "Sixty five round trunks, canvas stretched between them, gravel",
         "underneath. It is the largest floor in the catalogue by a wide",
         "margin and it is framed from the fewest pieces of anything here."),
    ),
    "Grow Dome": (
        "Aluminium and polycarbonate: the greenhouse configuration.",
        ("The same three frequency skeleton as the workshop, framed in",
         "aluminium and glazed in twinwall polycarbonate, with grow racks and",
         "water storage inside. The geometry did not change at all. Only the",
         "material list did, and the price came down by nearly half."),
    ),
    "Hex Cell Pavilion": (
        "A hexagonal cell frame in structural steel.",
        ("Not everything here is triangulated the same way. The hex cell style",
         "groups the geometry into hexagonal tiles on a steel frame, and the",
         "panels are composite hexagons with a seam bead around each one. It is",
         "heavier and dearer than anything timber, and it looks like nothing",
         "else on the site."),
    ),
    "Continuous Steel Arc Hangar": (
        "Curved ribs running over the shell instead of straight struts.",
        ("The hangar swaps short straight struts for twelve continuous steel",
         "arcs and three rings, with fabrication and site power equipment",
         "inside it. Two frequency, eight metre radius, open between the ribs.",
         "This is what the same geometry looks like when a steel shop builds it",
         "instead of a carpenter."),
    ),
    "Rebar Garden Dome": (
        "A dense meridian and ring lattice, bent from rebar.",
        ("Rebar is the cheapest structural steel there is, and it bends, so the",
         "tool draws it as twenty two meridians and seven rings rather than",
         "sticks between hubs. Seven thousand dollars, which is the cheapest",
         "building in the catalogue, and it is the one closest to what people",
         "actually put up in a back yard on a weekend."),
    ),
    "Concrete Monocoque Form": (
        "The frame as formwork for a poured shell.",
        ("Here the frame is not the building, it is the formwork. Rebar and",
         "shuttering panels carry a poured concrete shell, with shoring jacks,",
         "scaffold, a mixer and a bender on the floor. The dome is doing the",
         "thing concrete is best at, standing in pure compression, and it is by",
         "some distance the heaviest thing here."),
    ),
    "Woodland Hex Mirror": (
        "Hexagonal mirror tiles that reflect the site back at you.",
        ("The mirror designs exist because the renderer can do it. Those tiles",
         "are reflecting a sky and a tree line the shader computes per pixel,",
         "which is why the dome looks different from every angle as the camera",
         "moves. Structurally it is the same three frequency shell as the",
         "workshop."),
    ),
    "Woodland Square Mirror": (
        "The same trick at four frequency, on square tiles.",
        ("Four frequency on a steel frame, square mirror tiles instead of",
         "hexagons. More panels, each smaller, so the reflection breaks up",
         "finer. Between the two mirror designs you can see exactly what",
         "frequency does to a faceted surface: it stops looking like a machine",
         "and starts looking like a curve."),
    ),
    "Treehouse Canopy Dome": (
        "An elevated dome on a supported timber platform.",
        ("The smallest one, and the only one that is not on the ground. A two",
         "frequency hex tile dome on a timber platform with a central trunk,",
         "six posts, braces and a ladder, all of which the tool builds because",
         "the foundation menu has a treehouse platform in it. Six hundred",
         "square feet, up in the canopy."),
    ),
}


_SHOWCASES: list[Chapter] = []
for _index, (_name, _config) in enumerate(_presets()):
    _promise, _narration = SHOWCASE_COPY[_name]
    _pitch, _distance = _showcase_camera(_config)
    _SHOWCASES.append(Chapter(
        f"show_{_index:02d}", "00", _name, _promise, _narration, (), 14.0,
        (30.0 + (_index % 5) * 22.0, _pitch, _distance),
        f"ad_show_{_name}"))


CHAPTERS: tuple[Chapter, ...] = (
    Chapter(
        "open", "00", "All domes",
        "Every building the Dome Creator makes, drawn by the Dome Creator.",
        ("The Dome Creator is a walkable customizer with twelve finished",
         "designs in it, and this is all of them -- but not the way a film has",
         "shown them before. Until now the films rebuilt a preset's geometry",
         "and then re-drew it with their own tubes and triangles, which is a",
         "sketch of the building.",
         "These are the tool's own meshes, running through the tool's own",
         "shader. The wood has grain, the glass has a highlight, the mirror",
         "tiles are reflecting a tree line, and each of these is assembling",
         "itself in the order its construction record says to build it."),
        (), 16.0, (90.0, 13.0, 78.0), "ad_lineup"),
    _math(
        "math_catalogue", "The catalogue, counted",
        "Twelve buildings, fit-out included, none of it typed in.",
        ("Start with all twelve on one screen, because the spread is the",
         "point. The same engine makes a six hundred square foot treehouse",
         "dome and a three thousand square foot lodge, and the only things",
         "that changed are a frequency, a radius and a material list.",
         "The equipment count on the right is the part the old catalogue film",
         "could not show at all."),
        steps_catalogue(), 26.0, (74.0, 15.0, 42.0), "ad_lineup"),
    _math(
        "inputs", "What is declared, and what is measured",
        "Prices are declared inputs. Everything else is read off the model.",
        ("Before any dollar figure, here is where the dollars come from. The",
         "densities and unit prices live in one file in this project, they are",
         "declared inputs, and they are the only numbers in this film that",
         "were typed by a person.",
         "Every quantity they get multiplied by -- areas, lengths, counts,",
         "weights -- is measured off the model that drew the building you are",
         "looking at. Change a price in that file and the next render says the",
         "new number without anybody editing a script."),
        steps_inputs(), 24.0, (46.0, 18.0, 27.0), "ad_hero"),
) + tuple(_SHOWCASES) + (
    Chapter(
        "build", "00", "One dome, step by step",
        "The tool's own construction order, played end to end.",
        ("The mesh is not assembled in a random order. The builder emits it the",
         "way a trailer home is manufactured: site prep, then the slab, then",
         "the floor layout, the frame from the base ring upward, the hubs, the",
         "doorway, the sheathing bottom to top, the cladding, then rough",
         "electrical, rough plumbing, partitions, equipment, and finally the",
         "monitoring system.",
         "The ring on the floor is where the record says the crew is standing",
         "for the step on screen, and the hours are the tool's own estimate for",
         "the work done so far."),
        (), 30.0, (52.0, 16.0, 31.0), "ad_build"),
    _math(
        "math_build", "The labour model, phase by phase",
        "Three hundred and forty eight work steps, grouped.",
        ("Those steps add up, and grouping them says something useful about",
         "where a dome's time actually goes. The frame, which is the part",
         "everybody pictures when they think about building a dome, is not the",
         "expensive phase in hours.",
         "This is a model, not a stopwatch, and I want to be clear about that:",
         "it is an estimate attached to each work step. But it is the same",
         "estimate applied to every design, so comparing two of them is fair",
         "even where the absolute number is soft."),
        steps_construction(), 26.0, (52.0, 16.0, 35.0), "ad_build"),
    Chapter(
        "frequency", "00", "Frequency",
        "One radius, four subdivisions, all four built.",
        ("Now the menus, one at a time, and this is the first of them. Same",
         "radius, same material, same foundation: only the number of times each",
         "face is divided changes.",
         "One frequency is twenty five struts in one length. Four frequency is",
         "two hundred and fifty in six lengths. Frequency buys you a smoother",
         "shell and charges you in part variety, which is the thing that",
         "actually slows a build down."),
        (), 16.0, (90.0, 13.0, 34.0), "ad_frequency"),
    _math(
        "math_dials", "The four dials, and why they are countable",
        "Radius, strut width, recess and pad size move in fixed steps.",
        ("The tool also has sliders, and sliders look like they have infinite",
         "settings. They do not: each one moves in a fixed step, and those",
         "steps are written in the menu code, so they can be counted exactly",
         "like the drop-downs can.",
         "And not one of them changes the part count. Doubling the radius gives",
         "you four times the floor off the same list of operations, which is",
         "the whole economic argument for this shape."),
        steps_dials(), 24.0, (86.0, 14.0, 31.0), "ad_frequency"),
    Chapter(
        "styles", "00", "Six ways to join the same sticks",
        "Hub and strut, hubless, hex cell, arcs, lattice, formwork.",
        ("The frame style menu changes how the members meet, and it changes the",
         "building far more than the material does. Hub and strut is the",
         "classic. Hubless doubled gives every triangle its own three members.",
         "Hex cell groups them into hexagons. The arc and lattice styles throw",
         "out straight struts entirely and run continuous ribs over the shell.",
         "Formwork treats the frame as shuttering for something poured."),
        (), 18.0, (90.0, 14.0, 50.0), "ad_styles"),
    _math(
        "math_styles", "The six, counted -- including where the tool argues with itself",
        "And one disagreement inside the tool, said out loud.",
        ("Here they are as numbers, off the same shell. The interesting one is",
         "at the bottom, and it is not flattering.",
         "Two of these styles report hub connectors in the bill of materials",
         "that their own assembly never fits. The picture and the price",
         "disagree. The picture is the one to believe, because it is the",
         "assembly, so treat those two totals as high by their hub line.",
         "I would rather this film state that than quietly average it away."),
        steps_frame_styles(), 28.0, (86.0, 15.0, 33.0), "ad_styles"),
    Chapter(
        "shapes", "00", "Eight cross sections",
        "Round tube to quarter wedge, all at the same width.",
        ("The strut shape menu decides what every member is cut from. Round",
         "tube, solid rod, rebar, whole trunk, square tube, dimensional lumber,",
         "hex strut, and the quarter wedge this project is built around.",
         "All eight are drawn at the same nominal width, so what you are seeing",
         "is the profile the tool sweeps along each member, and the amount of",
         "material each one actually contains.",
         "The ninth is the same quarter wedge with its bark turned outward,",
         "because that is a menu of its own and it only means anything here."),
        (), 17.0, (78.0, 19.0, 32.0), "ad_shapes"),
    Chapter(
        "materials", "00", "Eight materials",
        "The same frame, priced and weighed eight ways.",
        ("The material menu carries a density and a price per kilogram, so",
         "changing it changes what the frame weighs and what it costs without",
         "touching a single dimension.",
         "Structural steel and timber frame the identical building. One of them",
         "is fifteen times the weight of the other."),
        (), 16.0, (84.0, 18.0, 34.0), "ad_materials"),
    Chapter(
        "colours", "00", "Sixteen finishes",
        "Eight frame colours in front, eight panel tints behind.",
        ("Two menus that change everything about how a building looks and",
         "nothing at all about what it costs: the frame colour and the panel",
         "tint. Front row is the frame, back row is the skin.",
         "It is worth knowing which of these decisions are free, because they",
         "are the ones you can change your mind about on the day."),
        (), 14.0, (88.0, 21.0, 42.0), "ad_colours"),
    Chapter(
        "panels", "00", "Sixteen panel types",
        "Everything the tool can put between the struts.",
        ("This is the menu that decides both what a dome looks like and what it",
         "costs. Open, plywood, glass, acrylic, twinwall, sheeting, insulated",
         "panel, shingle, metal, solar, canvas, hex composite, hex mirror,",
         "square mirror, concrete form, precast.",
         "Every one of these is the same shell underneath. Watch the mirrors on",
         "the bottom row and the solar cells above them: those are patterns the",
         "shader computes, not pictures pasted on."),
        (), 20.0, (90.0, 22.0, 42.0), "ad_panels"),
    _math(
        "math_price", "Which menu is the expensive one",
        "One design, one menu at a time, every setting priced.",
        ("So which of these choices actually costs money? Hold everything else",
         "at the workshop and price every setting of each menu in turn.",
         "The answer is that the covering and the frame material swing the",
         "price by tens of thousands, the geometry barely moves it, and three",
         "of the menus are free.",
         "That is good news, because the covering is the decision you can",
         "defer, stage, or upgrade later. The frame is the one you have to get",
         "right on day one."),
        steps_price_drivers(), 26.0, (86.0, 18.0, 30.0), "ad_panels"),
    Chapter(
        "layers", "00", "Nine cladding layers",
        "What goes over the sheathing, in three stackable slots.",
        ("Over the panels the tool will stack up to three cladding layers:",
         "plastic film, house wrap, foam, asphalt shingles, cedar shakes, an",
         "EPDM membrane, a green roof, or a poured concrete shell.",
         "Each one has a thickness, so they sit visibly outside the shell, and",
         "each covers only the panels that are neither open nor windows --",
         "which is the model being careful for you."),
        (), 15.0, (86.0, 19.0, 32.0), "ad_layers"),
    Chapter(
        "foundations", "00", "Seven foundations",
        "Bare ground to a treehouse platform.",
        ("Underneath, seven choices, and the tool builds each one properly:",
         "grass, gravel, a slab, a wood deck, stone pavers, bare ground, and a",
         "treehouse platform that comes with a trunk, six posts, braces and a",
         "ladder.",
         "The pad is sized from the dome's own radius, and it is priced by the",
         "square metre, which is why the platform is the dearest thing in this",
         "row by a long way."),
        (), 15.0, (90.0, 14.0, 33.0), "ad_foundations"),
    Chapter(
        "floor", "00", "Four ways to divide a floor",
        "Nothing, markings, low walls, full walls.",
        ("Inside, the floor is split into ten sections -- a centre hub and nine",
         "wedges -- and each one can be assigned a room type from a list of",
         "sixteen. The partition menu decides whether those sections are just",
         "painted on the slab or actually framed.",
         "Roofs off for this one, because there is no other way to see it."),
        (), 15.0, (68.0, 38.0, 33.0), "ad_floor"),
    Chapter(
        "fitout", "00", "The part nobody films",
        "Equipment, framed walls, plumbing -- and the circuits nobody has.",
        ("Here is the whole reason to draw the tool's real mesh rather than a",
         "shell. The homestead has twelve pieces of equipment on the floor,",
         "each with a price, a weight and a power draw. It has seven partition",
         "walls framed to a real height. It has hot, cold and drain lines run",
         "from a utility stub to every fixture in it.",
         "What it does not have is a single circuit, and neither does any other",
         "design in the catalogue. Conduit runs have to start at a battery bank",
         "or a charge controller, and not one preset ships with either. Put a",
         "battery bank on the floor and the wiring appears on its own."),
        (), 19.0, (40.0, 32.0, 27.0), "ad_fitout"),
    _math(
        "math_fitout", "What the fit-out costs",
        "The dome is the cheap part of the dome.",
        ("Add the equipment, the walls and the plumbing up, and they are a",
         "serious fraction of what this building costs -- on a design whose",
         "shell is split logs and plywood.",
         "The electrical line is the one to read carefully. Zero is what the",
         "catalogue reports, and that is a fact about the presets rather than",
         "about domes: add the power source and the model routes twenty two",
         "metres of conduit without being asked twice.",
         "The shape saves you on envelope. It does not save you on anything",
         "that plugs in."),
        steps_fitout(), 26.0, (44.0, 30.0, 31.0), "ad_fitout"),
    Chapter(
        "random", "00", "Eight the dice picked",
        "Random settings, built and priced, seed on screen.",
        ("Every dome so far was chosen. These eight were not: the film drew",
         "them at random from the menus, built whatever came out, and priced",
         "it.",
         "The seed is on screen, so anyone can run the same draw and get the",
         "same eight buildings. Some of them are sensible. At least one of them",
         "is a thing nobody would ever build, which is the honest shape of a",
         "combination space this large."),
        (), 19.0, (90.0, 18.0, 35.0), "ad_random"),
    _math(
        "math_permutations", "How many domes that is",
        "Sixteen billion shells, and the film that would take.",
        ("So how many buildings can this tool actually make? Multiply the",
         "menus.",
         "Then take the honest deduction, because some settings do nothing in",
         "some combinations, and count only the shells that genuinely differ.",
         "The number is still sixteen and a half billion. At three seconds",
         "each, showing every one of them would take fifteen centuries of",
         "film, so this one does the only sane thing instead: every setting of",
         "every menu, at least once, which is what you have just watched."),
        steps_permutations(), 28.0, (86.0, 16.0, 30.0), "ad_random"),
    Chapter(
        "close", "00", "Open the tool and check any of it",
        "Load the preset. Read the bill of materials.",
        ("That is the catalogue, every menu in the customizer, and the count of",
         "what they add up to. Nothing here was asserted: every figure was read",
         "off a model this film rebuilt while it was rendering, and every",
         "building was drawn by the tool's own renderer rather than an",
         "impression of it.",
         "So do not take my word for any of it. Open the Dome Creator, press",
         "the preset button until you reach the one you want, and read the bill",
         "of materials. It will say what this film said."),
        (), 17.0, (90.0, 13.0, 78.0), "ad_lineup"),
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
    stage stands depends on what the overlay is using, so a probe without them
    would test a composition the film never renders.
    """

    def __init__(self, overlay: str | None = None,
                 camera: tuple[float, float, float] = (90.0, 16.0, 40.0)) -> None:
        self.world_labels: list = []
        self.world_icons: list = []
        self.creator_draws: list = []
        self.chapter_index = 0
        self.chapters = (Chapter("probe", "00", "Probe", "Probe", ("probe",),
                                 (), 10.0, camera, "probe", overlay),)
        self.camera_yaw, self.camera_pitch, self.camera_distance = camera


def validate_all_domes() -> None:
    """Prove the film shows what its title claims, before anything renders."""
    from .render_kit import TriangleBatch

    validate_creator_facts()

    lesson = ALL_DOMES_LESSON
    slugs = [chapter.slug for chapter in lesson.chapters]
    assert len(set(slugs)) == len(slugs), "duplicate slug"
    for chapter in lesson.chapters:
        assert chapter.stage in lesson.scenes, (chapter.slug, chapter.stage)
        assert chapter.narration, chapter.slug
        if chapter.overlay == "math":
            assert len(chapter.equations) >= 5, chapter.slug

    # Every shipped design gets its own chapter: the film says "all domes", so
    # a preset added to the tool later must not quietly go unshown.
    shown = {chapter.stage for chapter in lesson.chapters}
    for name, _ in _presets():
        assert f"ad_show_{name}" in shown, name

    # Every math screen the facts module offers is used exactly once.
    used = {chapter.equations for chapter in lesson.chapters
            if chapter.overlay == "math"}
    offered = {builder() for _, builder in ALL_SCREENS}
    assert used == offered, (
        f"{len(offered - used)} unused, {len(used - offered)} unknown")

    # Every painter must put a real building on the stage and label it.
    drawn: list = []
    for stage, painter in lesson.scenes.items():
        for progress in (0.35, 0.8, 1.0):
            # Both ways a stage gets used: full frame, and beside a worksheet,
            # which moves it and thins it out.
            for overlay in (None, "math"):
                probe = _Probe(overlay)
                painter(probe, TriangleBatch(), TriangleBatch(), progress)
                assert probe.creator_draws, (stage, progress, overlay)
                for request in probe.creator_draws:
                    assert request.build.triangles > 100, (stage,
                                                           request.build.name)
                for label in probe.world_labels:
                    assert label.text.strip(), (stage, progress, overlay)
        probe = _Probe()
        painter(probe, TriangleBatch(), TriangleBatch(), 1.0)
        drawn.extend(request.build.config for request in probe.creator_draws)

    # The claim in the title, tested: every setting of every menu that changes
    # a building has to appear somewhere in the film at least once.
    from .creator_facts import axes

    for item in axes():
        if item.group != "shell":
            continue
        for label, value in item.values:
            wanted = value[0] if item.key == "layers" else value
            seen = any(
                (config.get(item.key, [None])[0] if item.key == "layers"
                 else config.get(item.key)) == wanted
                for config in drawn)
            assert seen, f"{item.name} setting {label!r} is never shown"

    # The partition menu is swept too, even though it is a fit-out menu.
    partitions = {config.get("partitions") for config in drawn}
    for label, value in axis("Partitions").values:
        assert value in partitions, f"partition mode {label!r} is never shown"

    # A showcase must draw the design it names, and quote that model's numbers.
    for name, _ in _presets():
        probe = _Probe()
        lesson.scenes[f"ad_show_{name}"](probe, TriangleBatch(),
                                         TriangleBatch(), 0.9)
        text = " ".join(label.text for label in probe.world_labels)
        assert name.upper() in text, name
        build = probe.creator_draws[0].build
        assert f"{build.stats['strut_count']} struts" in text, (name, text[:140])


ALL_DOMES_LESSON = Lesson(
    key="all_domes",
    brand="DOME CREATOR / EVERY PERMUTATION",
    title="All Domes",
    chapters=CHAPTERS,
    scenes=SCENES,
    selftest=validate_all_domes,
    report=creator_report,
    snapshot_prefix="alldomes",
    style="hype",
    voice_rate="+4%",
    label_layout="declutter",
    ground="off",
)
