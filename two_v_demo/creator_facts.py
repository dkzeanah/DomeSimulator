"""What the Dome Creator can build, counted off the tool's own catalogues.

The customizer is a set of menus, and this module reads those menus rather than
describing them: the frame styles come from :data:`dome_model.FRAME_STYLES`, the
panels from :data:`materials.PANEL_TYPES`, the partition modes from
:mod:`workshop`, and the numeric dials' ranges are read out of the menu code
itself, the same way :mod:`two_v_demo.scratch_facts` reads the renderer's field
of view out of the renderer.  Add a panel type to the tool and every count in
this film moves on the next render.

Three separate things get counted here, because lumping them together would be
a con:

* **Shell permutations** -- the options that change the building you look at.
* **Fit-out permutations** -- partitions and the ten room assignments, which
  change what the floor is for and almost nothing about the shell.
* **Dial settings** -- radius, strut width, recess and foundation size, which
  are continuous in principle but move in fixed steps in the tool, so the tool
  itself makes them countable.

And then the deduction, which is the honest part: some options do nothing in
some combinations.  Hub style is inert on a frame that has no hubs; the wedge
curve only bends a quarter wedge.  Both of those are *tested* against the real
code rather than asserted, and the smaller number is the one the film quotes.

Declared inputs: every density, unit price and labour rate below is declared by
``materials.py``, ``workshop.py`` and ``mesh_builder.py``'s construction record.
This module reports them; it does not invent them, and the film puts them on
screen as declared inputs before using them.
"""

from __future__ import annotations

import inspect
import math
import re
from dataclasses import dataclass
from functools import lru_cache

from .creator_bridge import preset, preset_names, presets_all, simulator, variant


BASE_DESIGN = "Timber Workshop"
"""The design the sweeps vary one option at a time from: the tool's default."""

FITOUT_DESIGN = "Split-Log Homestead"
"""The design the fit-out chapter takes apart.

Chosen by what it actually carries rather than by taste: of the shipped
presets it is the one with framed partition walls, plumbed fixtures and a
floor full of equipment at the same time."""


def _config(name: str) -> dict:
    for preset_name, data in presets_all():
        if preset_name == name:
            return data
    raise KeyError(name)


def wired_variant() -> dict:
    """The fit-out design with a power source added, so conduit gets routed.

    This one is not a shipped preset, and the film says so on camera.  Wiring
    runs start at a battery bank or a charge controller
    (:func:`workshop.power_source_entry`), and **no** design in the catalogue
    ships with either, so every one of them reports zero circuits as it stands.
    Placing a battery bank, a controller and two outlets is the smallest change
    that makes the tool's electrical model show itself, and the numbers that
    come back are the model's, not the film's.
    """
    config = dict(_config(FITOUT_DESIGN))
    config["props"] = list(config.get("props", [])) + [
        {"type": "Battery Bank", "x": -3.2, "y": -3.2, "yaw": 30.0},
        {"type": "Charge Controller", "x": -3.9, "y": -2.4, "yaw": 30.0},
        {"type": "Wall Outlet", "x": 3.4, "y": 1.2, "yaw": 250.0},
        {"type": "Wall Outlet", "x": -1.2, "y": 4.2, "yaw": 190.0},
        {"type": "Shop Light", "x": 0.0, "y": 0.0, "yaw": 0.0},
    ]
    return config


# ----------------------------------------------------------------------
# The menus, read off the tool
# ----------------------------------------------------------------------

@dataclass(frozen=True)
class Axis:
    """One menu in the Dome Creator: what it is called, and every setting."""

    name: str
    key: str
    """The design-file field this menu writes."""
    values: tuple[tuple[str, object], ...]
    """(label, value written into the configuration)."""
    group: str
    """``shell`` changes the building; ``fitout`` changes what the floor is for."""
    note: str = ""

    @property
    def count(self) -> int:
        return len(self.values)


def _layer_value(name: str) -> list:
    return [name, "None", "None"]


@lru_cache(maxsize=1)
def axes() -> tuple[Axis, ...]:
    """Every choice menu the customizer offers, read from its own tables."""
    sim = simulator()
    dome_model = sim["dome_model"]
    materials = sim["materials"]
    workshop = sim["workshop"]

    def named(items):
        return tuple((item.name, item.name) for item in items)

    frequencies = tuple((f"{value}V", value) for value in range(1, 5))
    return (
        Axis("Frequency", "frequency", frequencies, "shell",
             "how many times each icosahedron face is divided"),
        Axis("Frame style", "frame_style",
             tuple((name, name) for name in dome_model.FRAME_STYLES), "shell",
             "how the sticks meet each other"),
        Axis("Hub style", "hub_style",
             tuple((name, name) for name in dome_model.HUB_STYLES), "shell",
             "pucks or bracket plates, where there are hubs at all"),
        Axis("Strut shape", "strut_shape", named(materials.STRUT_SHAPES),
             "shell", "the cross section every member is cut to"),
        Axis("Frame material", "frame_material",
             named(materials.FRAME_MATERIALS), "shell",
             "what the frame is made of, with its density and price"),
        Axis("Frame colour", "frame_color", named(materials.FRAME_COLORS),
             "shell", "finish on the frame"),
        Axis("Panel type", "default_panel", named(materials.PANEL_TYPES),
             "shell", "what fills the triangles between the struts"),
        Axis("Panel colour", "panel_color", named(materials.PANEL_COLORS),
             "shell", "tint over a colourable panel"),
        Axis("Cladding layer", "layers",
             tuple((layer.name, _layer_value(layer.name))
                   for layer in materials.LAYER_TYPES), "shell",
             "one of three stacked layers over the sheathing"),
        Axis("Foundation", "foundation", named(materials.FOUNDATION_TYPES),
             "shell", "what the dome stands on"),
        Axis("Wedge curve", "wedge_flip",
             (("Inside", False), ("Outside", True)), "shell",
             "which way a split log's bark faces"),
        Axis("Partitions", "partitions",
             tuple((name, name) for name in workshop.PARTITION_MODES),
             "fitout", "markings, low walls, full walls, or nothing"),
        Axis("Room type", "sections",
             tuple((room.name, room.name) for room in workshop.ROOM_TYPES),
             "fitout", "what each of the ten floor sections is for"),
    )


def axis(name: str) -> Axis:
    for item in axes():
        if item.name == name:
            return item
    raise KeyError(name)


LAYER_SLOTS = 3
SECTION_SLOTS = 10


# ----------------------------------------------------------------------
# The numeric dials, read out of the menu code
# ----------------------------------------------------------------------

@dataclass(frozen=True)
class Dial:
    """One numeric menu item: its range and the step the tool moves it in."""

    name: str
    step: float
    low: float
    high: float
    unit: str

    @property
    def settings(self) -> int:
        """How many distinct values the tool can actually be set to."""
        return int(round((self.high - self.low) / self.step)) + 1


DIAL_UNITS = {
    "Radius": "m",
    "Strut width": "m",
    "Recess depth": "fraction of strut depth",
    "Foundation size": "x radius",
}


@lru_cache(maxsize=1)
def dials() -> tuple[Dial, ...]:
    """Radius, strut width, recess and foundation size, read from the tool.

    These live as literals in the menu builder, which is the only place they
    exist, so they are read out of its source rather than copied here where
    they would quietly go stale.
    """
    import dome_creator

    source = inspect.getsource(dome_creator.DomeCreatorApp._menu_page_dome)
    found: list[Dial] = []
    for name, unit in DIAL_UNITS.items():
        pattern = (r'number\(\s*"' + re.escape(name) +
                   r'".*?,\s*(-?[\d.]+),\s*(-?[\d.]+),\s*(-?[\d.]+),\s*lambda')
        match = re.search(pattern, source, re.DOTALL)
        assert match, (
            f"could not read the {name!r} dial out of the Dome Creator's menu. "
            "The film states its range; it will not guess it.")
        step, low, high = (float(value) for value in match.groups())
        found.append(Dial(name, step, low, high, unit))
    return tuple(found)


# ----------------------------------------------------------------------
# How many buildings that is
# ----------------------------------------------------------------------

def shell_permutations() -> int:
    """Every combination of the options that change the building itself."""
    total = 1
    for item in axes():
        if item.group != "shell":
            continue
        count = item.count ** LAYER_SLOTS if item.key == "layers" else item.count
        total *= count
    return total


def fitout_permutations() -> int:
    """Partition mode, times a room type for each of the ten floor sections."""
    return (axis("Partitions").count
            * axis("Room type").count ** SECTION_SLOTS)


def dial_permutations() -> int:
    total = 1
    for dial in dials():
        total *= dial.settings
    return total


# -- the deduction: options that do nothing, in combinations that ignore them

@lru_cache(maxsize=1)
def hub_style_effect() -> tuple[tuple[str, bool], ...]:
    """Which frame styles actually have hubs for the hub-style menu to change.

    Tested by building the frame both ways rather than claimed: a style that
    reports no hubs and no cost difference is one the menu cannot touch.
    """
    sim = simulator()
    base = dict(preset(BASE_DESIGN).config)
    out = []
    for style in sim["dome_model"].FRAME_STYLES:
        stats = [_stats(dict(base, frame_style=style, hub_style=hub))
                 for hub in sim["dome_model"].HUB_STYLES]
        changes = (stats[0]["hub_count"] > 0
                   and abs(stats[0]["total_cost"] - stats[1]["total_cost"]) > 1e-6)
        out.append((style, bool(changes)))
    return tuple(out)


@lru_cache(maxsize=1)
def wedge_curve_effect() -> tuple[tuple[str, bool], ...]:
    """Which strut shapes the wedge-curve menu actually bends.

    Read off the profile function itself: if flipping produces the same cross
    section, the setting is a no-op for that shape.
    """
    sim = simulator()
    out = []
    for shape in sim["materials"].STRUT_SHAPES:
        straight = shape.profile(0.06, flip=False)
        flipped = shape.profile(0.06, flip=True)
        out.append((shape.name, straight != flipped))
    return tuple(out)


def distinct_shells() -> int:
    """Shell permutations, with the settings that do nothing collapsed.

    Hub style is counted only on frames that have hubs, and the wedge curve only
    on shapes it bends, so the number is buildings that genuinely differ rather
    than rows in a product of menus.
    """
    styles = sum(2 if changes else 1 for _, changes in hub_style_effect())
    shapes = sum(2 if changes else 1 for _, changes in wedge_curve_effect())
    total = styles * shapes
    for item in axes():
        if item.group != "shell":
            continue
        if item.key in ("frame_style", "hub_style", "strut_shape", "wedge_flip"):
            continue
        count = item.count ** LAYER_SLOTS if item.key == "layers" else item.count
        total *= count
    return total


def years_to_watch(seconds_each: float = 3.0, count: int | None = None) -> float:
    """How long a film that showed every one of them would run, in years."""
    if count is None:
        count = distinct_shells()
    return count * seconds_each / (365.25 * 24 * 3600)


# ----------------------------------------------------------------------
# Real buildings, measured
# ----------------------------------------------------------------------

@lru_cache(maxsize=512)
def _stats_key(key: str) -> dict:
    import json

    sim = simulator()
    config = json.loads(key)
    model = sim["dome_model"].DomeModel(
        sim["dome_model"].DomeConfig.from_dict(config))
    return model.stats()


def _stats(config: dict) -> dict:
    """A design's bill of materials, without building its mesh.

    The sweeps price dozens of designs; only the ones that reach the screen
    need geometry, so this path stops at the numbers.
    """
    import json

    return _stats_key(json.dumps(config, sort_keys=True, default=str))


SQFT_PER_SQM = 10.7639104
FT_PER_M = 3.280839895


@dataclass(frozen=True)
class DesignRow:
    name: str
    frequency: int
    diameter_ft: float
    floor_sqft: float
    struts: int
    panels: int
    props: int
    walls: int
    cost: float
    weight_kg: float

    @property
    def cost_per_sqft(self) -> float:
        return self.cost / self.floor_sqft if self.floor_sqft else 0.0


@lru_cache(maxsize=32)
def design_hours(name: str) -> float:
    """The tool's labour estimate for one design, off its construction record.

    Separate from the table below because it is the one figure that needs the
    mesh: the record is emitted while the building is assembled.
    """
    return preset(name).hours


@lru_cache(maxsize=1)
def design_rows() -> tuple[DesignRow, ...]:
    """Every shipped preset, measured, fit-out included.

    Model only, no meshes: filling a table of twelve would otherwise put eight
    seconds on every import of this package, including the ones that only want
    to list the lessons.
    """
    rows = []
    for name, config in presets_all():
        stats = _stats(config)
        floor = float(stats["floor_area"]) * SQFT_PER_SQM
        rows.append(DesignRow(
            name=name,
            frequency=int(stats["frequency"]),
            diameter_ft=float(stats["radius"]) * 2.0 * FT_PER_M,
            floor_sqft=floor,
            struts=int(stats["strut_count"]),
            panels=int(stats["panel_count"]),
            props=int(stats["prop_count"]),
            walls=int(stats["wall_count"]),
            cost=float(stats["total_cost"]),
            weight_kg=float(stats["structure_weight"]),
        ))
    return tuple(rows)


# -- what each menu is worth, in money -----------------------------------

@dataclass(frozen=True)
class Swing:
    axis: str
    cheapest: str
    dearest: str
    low: float
    high: float

    @property
    def span(self) -> float:
        return self.high - self.low


@lru_cache(maxsize=1)
def price_swings() -> tuple[Swing, ...]:
    """What each menu does to the price, one menu at a time.

    Everything else is held at the base design, so the spread is that menu's
    own doing.  This is the question a person actually has when they open the
    tool: which of these choices is the expensive one?
    """
    base = dict(preset(BASE_DESIGN).config)
    swings = []
    for item in axes():
        if item.group != "shell":
            continue
        priced = []
        for label, value in item.values:
            config = dict(base)
            config[item.key] = value
            priced.append((label, float(_stats(config)["total_cost"])))
        priced.sort(key=lambda row: row[1])
        swings.append(Swing(item.name, priced[0][0], priced[-1][0],
                            priced[0][1], priced[-1][1]))
    swings.sort(key=lambda swing: -swing.span)
    return tuple(swings)


# -- the six frame styles, compared on one dome --------------------------

@dataclass(frozen=True)
class StyleRow:
    name: str
    struts: int
    hubs_priced: int
    hubs_built: int
    bolts: int
    hub_cost: float
    cost: float


@lru_cache(maxsize=1)
def frame_style_rows() -> tuple[StyleRow, ...]:
    """Each frame style on the same dome: what it frames, joins and costs.

    ``hubs_built`` is counted off the construction record -- the connectors the
    assembly actually fits -- while ``hubs_priced`` is what the bill of
    materials charges for.  On two of the six styles those disagree, which is
    the sort of thing a film about a tool should say rather than average away.
    """
    sim = simulator()
    base = dict(preset(BASE_DESIGN).config)
    base["props"] = []
    rows = []
    for style in sim["dome_model"].FRAME_STYLES:
        build = variant(base, style, frame_style=style)
        stats = build.stats
        built = sum(1 for event in build.events
                    if str(event["label"]).lower().startswith("fasten hub"))
        rows.append(StyleRow(
            name=style,
            struts=int(stats["strut_count"]),
            hubs_priced=int(stats["hub_count"]),
            hubs_built=built,
            bolts=int(stats["bolt_count"]),
            hub_cost=float(stats["hub_cost"]),
            cost=float(stats["total_cost"]),
        ))
    return tuple(rows)


def hubs_not_drawn() -> tuple[StyleRow, ...]:
    """Styles whose bill charges for hub connectors the assembly never fits."""
    return tuple(row for row in frame_style_rows()
                 if row.hubs_priced > 0 and row.hubs_built == 0)


# -- the labour model ----------------------------------------------------

PHASE_ORDER = ("Site", "Frame", "Joins", "Openings", "Sheathing", "Cladding",
               "Systems", "Fit-out", "Commissioning")

PHASE_KEYS = (
    ("Site", ("site prep", "floor layout")),
    ("Frame", ("install strut", "raise ")),
    ("Joins", ("fasten hub", "through-bolt")),
    ("Openings", ("frame the entrance",)),
    ("Sheathing", ("fit ",)),
    ("Cladding", ("apply ",)),
    ("Systems", ("wire ", "plumb ")),
    ("Fit-out", ("frame ", "install ")),
    ("Commissioning", ("test,",)),
)


def phase_of(label: str) -> str:
    """Which build phase one construction event belongs to."""
    lowered = label.lower()
    for phase, keys in PHASE_KEYS:
        if any(lowered.startswith(key) for key in keys):
            return phase
    return "Fit-out"


@lru_cache(maxsize=32)
def build_phases(name: str) -> tuple[tuple[str, int, float], ...]:
    """(phase, steps, hours) for one design, off its construction record."""
    build = preset(name)
    totals: dict[str, list] = {}
    for event in build.events:
        phase = phase_of(str(event["label"]))
        row = totals.setdefault(phase, [0, 0.0])
        row[0] += 1
        row[1] += float(event["hours"])
    return tuple((phase, totals[phase][0], totals[phase][1])
                 for phase in PHASE_ORDER if phase in totals)


# -- random draws --------------------------------------------------------

def random_designs(seed: int = 7, count: int = 8) -> tuple[dict, ...]:
    """Configurations drawn at random from the shell menus.

    A film cannot show sixty billion buildings, so it shows a handful the dice
    picked, with the seed on screen: run the same seed and you get the same
    domes.  Only the shell menus are drawn; the fit-out is the base design's, so
    the eye compares buildings rather than furniture.
    """
    import random

    rng = random.Random(seed)
    base = dict(preset(BASE_DESIGN).config)
    shell = [item for item in axes() if item.group == "shell"]
    out = []
    for _ in range(count):
        config = dict(base)
        for item in shell:
            label, value = rng.choice(item.values)
            config[item.key] = list(value) if isinstance(value, list) else value
        out.append(config)
    return tuple(out)


# ----------------------------------------------------------------------
# Math screens
# ----------------------------------------------------------------------

def _conclude(steps: list[str], conclusion: str) -> tuple[str, ...]:
    steps.append(conclusion)
    return tuple(steps)


@lru_cache(maxsize=1)
def steps_inputs() -> tuple[str, ...]:
    """The declared inputs, on screen before any price is quoted."""
    sim = simulator()
    materials = sim["materials"]
    workshop = sim["workshop"]
    panels = sorted(materials.PANEL_TYPES, key=lambda p: p.cost_per_m2)
    dearest = panels[-1]
    cheapest = next(p for p in panels if p.cost_per_m2 > 0)
    steps = [
        "nothing below is measured -- these are declared inputs:",
        f"frame materials: {len(materials.FRAME_MATERIALS)} entries, "
        f"density kg/m3 and price per kg",
        f"   timber (SPF)  {materials.FRAME_MATERIALS[4].density:.0f} kg/m3  "
        f"${materials.FRAME_MATERIALS[4].cost_per_kg:.2f}/kg",
        f"panels: {len(materials.PANEL_TYPES)} types, "
        f"${cheapest.cost_per_m2:.2f} to ${dearest.cost_per_m2:.2f} per m2",
        f"   cheapest {cheapest.name}, dearest {dearest.name}",
        f"cladding layers: {len(materials.LAYER_TYPES)}, "
        f"foundations: {len(materials.FOUNDATION_TYPES)} "
        f"(${materials.FOUNDATION_TYPES[3].cost_per_m2:.0f}/m2 for a slab)",
        f"partition walls ${workshop.WALL_COST_PER_M2:.0f}/m2, "
        f"wire ${workshop.WIRE_COST_PER_M:.2f}/m, "
        f"PEX ${workshop.PEX_COST_PER_M:.2f}/m",
        "labour hours come from the mesh builder's construction record,",
        "which is an estimate per work step, not a stopwatch",
    ]
    return _conclude(
        steps,
        "every dollar in this film is one of those numbers multiplied by a "
        "quantity the model measured -- change a price in materials.py and "
        "the next render says the new one")


@lru_cache(maxsize=1)
def steps_catalogue() -> tuple[str, ...]:
    """The shipped designs, as whole buildings rather than frames."""
    rows = design_rows()
    steps = [f"{len(rows)} designs, each rebuilt and measured whole:"]
    for row in rows:
        steps.append(
            f"{row.name[:25]:<25} {row.frequency}V {row.struts:>3} struts "
            f"{row.panels:>3} panels {row.props:>2} items "
            f"{row.floor_sqft:>5.0f} sqft  ${row.cost:>7,.0f}")
    items = sum(row.props for row in rows)
    return _conclude(
        steps,
        f"{items} pieces of equipment stand on those {len(rows)} floors, and "
        f"the workshop alone is {design_hours(BASE_DESIGN):,.0f} hours of work "
        "-- the fit-out is part of the building here, not a picture of one")


@lru_cache(maxsize=1)
def steps_frame_styles() -> tuple[str, ...]:
    """Six ways to join the same sticks -- and where the tool contradicts itself."""
    rows = frame_style_rows()
    steps = [f"one {BASE_DESIGN.lower()} shell, framed six ways:"]
    for row in rows:
        steps.append(
            f"{row.name[:22]:<22} {row.struts:>3} struts  "
            f"{row.hubs_built:>3} hubs fitted  {row.bolts:>3} bolts  "
            f"${row.cost:>7,.0f}")
    odd = hubs_not_drawn()
    if odd:
        steps.append("and one disagreement inside the tool, said out loud:")
        for row in odd:
            steps.append(
                f"{row.name[:22]:<22} bills ${row.hub_cost:,.0f} for "
                f"{row.hubs_priced} hub connectors its own assembly never fits")
    return _conclude(
        steps,
        "the picture follows the assembly, so those two totals are high by "
        "their hub line -- every other figure in this film comes off the same "
        "model that drew the building beside it")


@lru_cache(maxsize=1)
def steps_permutations() -> tuple[str, ...]:
    """How many buildings the menus can actually make."""
    shell = [item for item in axes() if item.group == "shell"]
    steps = ["the shell menus, multiplied:"]
    for item in shell:
        if item.key == "layers":
            steps.append(f"{item.name + ' x3':<22} {item.count} ^ {LAYER_SLOTS} "
                         f"= {item.count ** LAYER_SLOTS:,}")
        else:
            steps.append(f"{item.name:<22} {item.count}")
    raw = shell_permutations()
    distinct = distinct_shells()
    dead_hubs = [name for name, changes in hub_style_effect() if not changes]
    live_curves = [name for name, changes in wedge_curve_effect() if changes]
    steps.extend([
        f"product = {raw:,} shells",
        "but some settings do nothing in some combinations:",
        f"hub style changes nothing on {' and '.join(dead_hubs).lower()}, "
        "which has no hub to change",
        f"the wedge curve bends {len(live_curves)} of "
        f"{len(wedge_curve_effect())} strut shapes "
        f"({', '.join(name.lower() for name in live_curves)})",
        f"count only the ones that differ: {distinct:,} shells",
        f"then the floor: {fitout_permutations():,} partition and room layouts",
        f"and the dials, at the steps the tool moves them in: "
        f"{dial_permutations():,} settings",
    ])
    return _conclude(
        steps,
        f"{distinct:,} distinct shells, at three seconds each, is "
        f"{years_to_watch():,.0f} years of film -- so this one shows every "
        "setting instead, at least once")


@lru_cache(maxsize=1)
def steps_dials() -> tuple[str, ...]:
    """The four continuous dials, countable because the tool has steps."""
    steps = ["the sliders are not continuous -- the tool moves them in steps:"]
    for dial in dials():
        span = f"{dial.low:g} to {dial.high:g}"
        steps.append(
            f"{dial.name:<16}{span:>14}  step {dial.step:<6g}"
            f"{dial.settings:>4} settings   {dial.unit}")
    total = dial_permutations()
    return _conclude(
        steps,
        f"{total:,} settings from four dials, and not one of them changes the "
        "part count: frequency alone decides how many pieces there are")


@lru_cache(maxsize=1)
def steps_price_drivers() -> tuple[str, ...]:
    """Which menu is the expensive one, measured on one design."""
    swings = price_swings()
    base = _stats(dict(preset(BASE_DESIGN).config))
    steps = [
        f"start from {BASE_DESIGN} at ${base['total_cost']:,.0f},",
        "change one menu at a time, price every setting:",
    ]
    for swing in swings[:6]:
        steps.append(
            f"{swing.axis:<16} ${swing.low:>7,.0f} ({swing.cheapest[:14]})"
            f" -> ${swing.high:>8,.0f} ({swing.dearest[:14]})")
    free = [swing.axis.lower() for swing in swings if swing.span < 1.0]
    steps.append(
        f"and {len(free)} menus cost nothing at all: {', '.join(free)}")
    top = swings[0]
    return _conclude(
        steps,
        f"{top.axis.lower()} swings the price by ${top.span:,.0f} on the same "
        f"geometry -- the shape is not what you are paying for")


@lru_cache(maxsize=1)
def steps_construction() -> tuple[str, ...]:
    """The tool's own labour model for one building, phase by phase."""
    name = BASE_DESIGN
    phases = build_phases(name)
    build = preset(name)
    steps = [f"{name}: {len(build.events)} work steps, in build order:"]
    for phase, count, hours in phases:
        steps.append(f"{phase:<15} {count:>4} steps {hours:>7.1f} h")
    total = build.hours
    crew = 2
    steps.extend([
        f"total {total:,.1f} hours of work",
        f"two people, eight hour days: "
        f"{total / (crew * 8.0):.1f} days",
    ])
    return _conclude(
        steps,
        f"{total:,.0f} hours is the tool's estimate, not a stopwatch -- but it "
        "is the same estimate for every design, so the comparisons between "
        "them hold even where the absolute number does not")


@lru_cache(maxsize=1)
def steps_fitout() -> tuple[str, ...]:
    """The part of the building the old catalogue film never showed."""
    rows = design_rows()
    furnished = [row for row in rows if row.props]
    walled = [row for row in rows if row.walls]
    shipped = _stats(_config(FITOUT_DESIGN))
    wired = _stats(wired_variant())
    services = (shipped["prop_cost"] + shipped["wall_cost"]
                + shipped["wire_cost"] + shipped["plumbing_cost"])
    steps = [
        f"{len(furnished)} of {len(rows)} designs ship furnished, "
        f"{len(walled)} with framed walls",
        f"{FITOUT_DESIGN}, as the tool ships it:",
        f"   {shipped['prop_count']} pieces of equipment, "
        f"${shipped['prop_cost']:,.0f}, {shipped['prop_weight']:,.0f} kg, "
        f"{shipped['prop_watts']:,.0f} W connected",
        f"   {shipped['wall_count']} framed partition walls, "
        f"{shipped['wall_area']:.0f} m2, ${shipped['wall_cost']:,.0f}",
        f"   {shipped['pipe_fixtures']} plumbed fixtures, "
        f"{shipped['pex_len']:.0f} m of PEX and "
        f"{shipped['drain_len']:.0f} m of drain, "
        f"${shipped['plumbing_cost']:,.0f}",
        f"   {shipped['wire_runs']} circuits -- and that is not an oversight:",
        "   conduit runs start at a battery bank or a charge controller,",
        "   and no design in this catalogue ships with either",
        "add a battery bank, a controller and two outlets:",
        f"   {wired['wire_runs']} conduit runs, {wired['wire_len']:.0f} m of "
        f"wire, ${wired['wire_cost']:,.0f}",
        f"fit-out and services: ${services:,.0f} of "
        f"${shipped['total_cost']:,.0f}, or "
        f"{services / shipped['total_cost'] * 100:.0f}% of the building",
    ]
    return _conclude(
        steps,
        "the dome is the cheap part of the dome -- which is exactly why a film "
        "about domes should show the plumbing")


ALL_SCREENS: tuple[tuple[str, object], ...] = (
    ("inputs", steps_inputs),
    ("catalogue", steps_catalogue),
    ("frame_styles", steps_frame_styles),
    ("permutations", steps_permutations),
    ("dials", steps_dials),
    ("price_drivers", steps_price_drivers),
    ("construction", steps_construction),
    ("fitout", steps_fitout),
)


def creator_report() -> str:
    """A portable audit of every count this film states."""
    lines = [
        "EVERY DOME THE CREATOR CAN BUILD -- COUNTED",
        "",
        "Menus are read from dome_model.py, materials.py and workshop.py.",
        "Dial ranges are read out of the Dome Creator's own menu code.",
        "Every price is a declared input from materials.py multiplied by a",
        "quantity DomeModel.stats() measured.",
        "",
        "MENUS",
    ]
    for item in axes():
        lines.append(f"  {item.name:<16} {item.count:>3}  ({item.group})  "
                     f"{item.note}")
    lines.append("")
    lines.append("DIALS")
    for dial in dials():
        lines.append(f"  {dial.name:<16} {dial.low:g}..{dial.high:g} "
                     f"step {dial.step:g} -> {dial.settings} settings")
    lines.extend([
        "",
        f"shell permutations        {shell_permutations():,}",
        f"distinct shells           {distinct_shells():,}",
        f"fit-out permutations      {fitout_permutations():,}",
        f"dial settings             {dial_permutations():,}",
        f"years to show them all    {years_to_watch():,.0f} at 3 s each",
        "",
        "DESIGNS",
    ])
    for row in design_rows():
        lines.append(
            f"  {row.name:<28} {row.frequency}V  {row.diameter_ft:5.1f} ft  "
            f"{row.floor_sqft:6.0f} sqft  {row.struts:3} struts  "
            f"{row.props:2} items  {design_hours(row.name):6.1f} h  "
            f"${row.cost:9,.0f}")
    lines.extend(["", "PRICE SWINGS (one menu at a time, from " + BASE_DESIGN + ")"])
    for swing in price_swings():
        lines.append(
            f"  {swing.axis:<16} ${swing.low:>8,.0f} .. ${swing.high:>9,.0f}  "
            f"span ${swing.span:>9,.0f}")
    lines.extend(["", "MATH SCREENS", ""])
    for name, builder in ALL_SCREENS:
        lines.append(f"== {name.upper()} ==")
        lines.extend(f"  {line}" for line in builder())
        lines.append("")
    return "\n".join(lines)


def validate_creator_facts() -> None:
    """Prove the counts come off the tool, and that they are honest."""
    menus = axes()
    assert len(menus) >= 12, len(menus)
    for item in menus:
        assert item.count >= 2, item.name
        assert item.note, item.name
        assert item.group in ("shell", "fitout"), item.group

    # The dial ranges must have been read, not defaulted.
    found = {dial.name for dial in dials()}
    assert found == set(DIAL_UNITS), found
    radius = next(dial for dial in dials() if dial.name == "Radius")
    assert radius.settings > 10 and radius.high > radius.low, radius

    # The deduction must be a real deduction: fewer distinct shells than rows
    # in the product, and the inert settings must genuinely be inert.
    assert distinct_shells() < shell_permutations()
    hubs = dict(hub_style_effect())
    assert hubs["Hub & Strut"] is True, hubs
    assert hubs["Hubless Doubled"] is False, hubs
    curves = dict(wedge_curve_effect())
    assert curves["Quarter Wedge"] is True, curves
    assert curves["Round Tube"] is False, curves

    # Every design must be a whole building, fit-out included.
    rows = design_rows()
    assert len(rows) == len(preset_names()), len(rows)
    assert any(row.props for row in rows), "no design ships furnished"
    for row in rows:
        assert row.struts > 0 and row.panels > 0, row.name
        assert row.cost > 0.0, row.name
    assert design_hours(BASE_DESIGN) > 0.0

    # A price swing has to be measured on real builds, and ordered by size.
    swings = price_swings()
    assert swings[0].span >= swings[-1].span
    assert swings[0].span > 0.0
    for swing in swings:
        assert swing.high >= swing.low, swing

    # The frame styles must be compared on real builds, and the disagreement
    # the film reports has to be a real one, found rather than asserted.
    styles = frame_style_rows()
    assert len(styles) == len(simulator()["dome_model"].FRAME_STYLES)
    hubbed = next(row for row in styles if row.name == "Hub & Strut")
    assert hubbed.hubs_built == hubbed.hubs_priced > 0, hubbed
    hubless = next(row for row in styles if row.name == "Hubless Doubled")
    assert hubless.hubs_built == 0 and hubless.bolts > 0, hubless
    for row in hubs_not_drawn():
        assert row.hubs_priced > 0 and row.hubs_built == 0, row
        assert row.hub_cost > 0.0, row

    # The fit-out claim has to hold on the design the film takes apart: it
    # carries all three systems, it genuinely ships with no circuits, and
    # adding a power source genuinely routes some.
    shipped = _stats(_config(FITOUT_DESIGN))
    assert shipped["prop_count"] > 0 and shipped["wall_count"] > 0, shipped
    assert shipped["pipe_fixtures"] > 0, shipped
    assert shipped["wire_runs"] == 0, shipped["wire_runs"]
    wired = _stats(wired_variant())
    assert wired["wire_runs"] > 0 and wired["wire_len"] > 0.0, wired
    assert wired["wall_count"] == shipped["wall_count"], "the walls moved"

    # The construction record must cover the whole build in known phases.
    phases = build_phases(BASE_DESIGN)
    assert phases, "no construction phases"
    hours = sum(hours for _, _, hours in phases)
    assert abs(hours - preset(BASE_DESIGN).hours) < 1e-6, (hours,)
    assert {phase for phase, _, _ in phases} <= set(PHASE_ORDER)

    # Random draws must be reproducible and must actually vary.
    first = random_designs(7, 6)
    assert first == random_designs(7, 6), "the draw is not reproducible"
    assert len({config["frame_style"] for config in first}) > 1 or \
        len({config["default_panel"] for config in first}) > 1

    # Every screen builds, states something, and ends on a sentence.
    for name, builder in ALL_SCREENS:
        steps = builder()
        assert len(steps) >= 5, (name, len(steps))
        assert all(line.strip() for line in steps), name
        assert len(steps[-1]) >= 30, (name, steps[-1])
