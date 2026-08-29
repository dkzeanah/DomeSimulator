"""Every dome type in the Dome Creator world, measured off the real model.

The other facts modules in this package compute a 2V hemisphere from
first principles.  This one is different on purpose: it reaches into the
**interactive simulator's own modules** -- :mod:`presets`,
:mod:`dome_model` and :mod:`materials` -- builds each of the twelve
shipped preset designs exactly as the walkable world builds them, and
reads its numbers off the finished model.

That is the whole point of the lesson it feeds.  When the film says a
Glass Studio Loft has 250 struts in six length classes and costs what it
costs, that is not a figure typed into a script: it is
``DomeModel(...).stats()`` on the same configuration the simulator loads
when you press the Preset button.  If somebody edits a price in
``materials.py``, this film's numbers move with it.

Derived: every count, length, area, weight and dollar total below, all
of them read off a built model.  Borrowed: the material densities and
unit prices in ``materials.py``, which are that module's own declared
inputs and are reported rather than recomputed here.
"""

from __future__ import annotations

import math
import sys
from dataclasses import dataclass
from functools import lru_cache
from pathlib import Path


# The simulator's modules live at the repository root, one level above
# this package.  A lesson is normally run from the root, but the import
# is made robust so the audit can also be taken from anywhere.
_ROOT = str(Path(__file__).resolve().parent.parent)
if _ROOT not in sys.path:
    sys.path.insert(0, _ROOT)

import dome_model  # noqa: E402
import presets  # noqa: E402


SQFT_PER_SQM = 10.7639104
FT_PER_M = 3.280839895


@dataclass(frozen=True)
class DomeType:
    """One preset design from the walkable world, fully measured."""

    name: str
    config: object
    stats: dict

    # -- what it is ---------------------------------------------------
    @property
    def frequency(self) -> int:
        return int(self.stats["frequency"])

    @property
    def radius_m(self) -> float:
        return float(self.stats["radius"])

    @property
    def frame_style(self) -> str:
        return str(self.stats["frame_style"])

    @property
    def strut_shape(self) -> str:
        return dome_model.STRUT_SHAPES[self.config.strut_shape].name

    @property
    def frame_material(self) -> str:
        return dome_model.FRAME_MATERIALS[self.config.frame_material].name

    @property
    def panel_type(self) -> str:
        """The panel that covers the most area on this dome."""
        groups = self.stats["panel_groups"]
        if not groups:
            return self.config.default_panel
        return max(groups.items(), key=lambda kv: kv[1]["area"])[0]

    # -- how big ------------------------------------------------------
    @property
    def floor_sqft(self) -> float:
        return float(self.stats["floor_area"]) * SQFT_PER_SQM

    @property
    def shell_sqft(self) -> float:
        return float(self.stats["surface_area"]) * SQFT_PER_SQM

    @property
    def height_ft(self) -> float:
        return float(self.stats["height"]) * FT_PER_M

    @property
    def diameter_ft(self) -> float:
        return self.radius_m * 2.0 * FT_PER_M

    # -- what it is made of -------------------------------------------
    @property
    def struts(self) -> int:
        return int(self.stats["strut_count"])

    @property
    def strut_classes(self) -> int:
        return len(self.stats["strut_classes"])

    @property
    def panels(self) -> int:
        return int(self.stats["panel_count"])

    @property
    def hubs(self) -> int:
        return int(self.stats["hub_count"])

    @property
    def bolts(self) -> int:
        return int(self.stats["bolt_count"])

    @property
    def trees(self) -> int:
        return int(self.stats["trees_required"])

    # -- what it costs ------------------------------------------------
    @property
    def total_cost(self) -> float:
        return float(self.stats["total_cost"])

    @property
    def weight_kg(self) -> float:
        return float(self.stats["structure_weight"])

    @property
    def cost_per_sqft(self) -> float:
        return self.total_cost / self.floor_sqft if self.floor_sqft else 0.0

    @property
    def solar_watts(self) -> float:
        return float(self.stats["solar_watts"])

    @property
    def skin_per_floor(self) -> float:
        """Shell area per unit of floor -- the shape's efficiency."""
        return self.shell_sqft / self.floor_sqft if self.floor_sqft else 0.0


def _build(name: str, data: dict) -> DomeType:
    config = dome_model.DomeConfig.from_dict(data)
    model = dome_model.DomeModel(config)
    model.rebuild()
    return DomeType(name=name, config=config, stats=model.stats())


@lru_cache(maxsize=1)
def dome_types() -> tuple[DomeType, ...]:
    """All twelve shipped presets, built exactly as the simulator builds
    them."""
    return tuple(_build(name, data) for name, data in presets.PRESETS)


@lru_cache(maxsize=1)
def by_name() -> dict[str, DomeType]:
    return {dome.name: dome for dome in dome_types()}


def dome_geometry(dome: DomeType):
    """A freshly built model for drawing: struts, panels and hubs.

    Kept separate from :func:`dome_types` because the painters want the
    live geometry arrays and the facts only want the numbers.
    """
    model = dome_model.DomeModel(dome.config)
    model.rebuild()
    return model


# ----------------------------------------------------------------------
# The frequency ladder, built rather than quoted
# ----------------------------------------------------------------------

@dataclass(frozen=True)
class FrequencyStep:
    frequency: int
    struts: int
    strut_classes: int
    panels: int
    hubs: int
    shell_sqm: float
    floor_sqm: float
    height_m: float
    radius_m: float

    @property
    def is_hemisphere(self) -> bool:
        """Whether the cut lands on the equator.

        Even frequencies put a ring of vertices exactly on the equator,
        so the dome stops at half a sphere and its height equals its
        radius.  Odd ones have no such ring: the nearest one sits above
        it, so the dome is taller than a hemisphere and carries more
        skin for the same floor.
        """
        return abs(self.height_m - self.radius_m) < 1e-6


@lru_cache(maxsize=1)
def frequency_ladder(radius_m: float = 5.0) -> tuple[FrequencyStep, ...]:
    """Build 1V through 4V at one radius and measure each."""
    steps: list[FrequencyStep] = []
    for frequency in (1, 2, 3, 4):
        config = dome_model.DomeConfig()
        config.frequency = frequency
        config.radius = radius_m
        model = dome_model.DomeModel(config)
        model.rebuild()
        stats = model.stats()
        steps.append(FrequencyStep(
            frequency=frequency,
            struts=int(stats["strut_count"]),
            strut_classes=len(stats["strut_classes"]),
            panels=int(stats["panel_count"]),
            hubs=int(stats["hub_count"]),
            shell_sqm=float(stats["surface_area"]),
            floor_sqm=float(stats["floor_area"]),
            height_m=float(stats["height"]),
            radius_m=radius_m,
        ))
    return tuple(steps)


# ----------------------------------------------------------------------
# Math screens
# ----------------------------------------------------------------------

def _conclude(steps: list[str], conclusion: str) -> tuple[str, ...]:
    steps.append(conclusion)
    return tuple(steps)


@lru_cache(maxsize=1)
def steps_catalogue() -> tuple[str, ...]:
    """Every preset in the world, counted off its own built model."""
    types = dome_types()
    steps = [
        f"{len(types)} shipped designs, each rebuilt live:",
    ]
    for dome in types:
        steps.append(
            f"{dome.name[:26]:<26} {dome.frequency}V  "
            f"{dome.struts:>3} struts  {dome.panels:>3} panels  "
            f"{dome.floor_sqft:>5.0f} sq ft")
    biggest = max(types, key=lambda d: d.floor_sqft)
    smallest = min(types, key=lambda d: d.floor_sqft)
    return _conclude(
        steps,
        f"one geometry engine, {len(types)} buildings, "
        f"{smallest.floor_sqft:.0f} to {biggest.floor_sqft:.0f} square "
        "feet -- and not one of these numbers was typed in")


@lru_cache(maxsize=1)
def steps_frequency() -> tuple[str, ...]:
    """What raising the frequency actually costs."""
    ladder = frequency_ladder()
    steps = ["same 5 m radius, four frequencies, all built and measured:"]
    for step in ladder:
        steps.append(
            f"{step.frequency}V: {step.struts:>3} struts in "
            f"{step.strut_classes} length class"
            f"{'es' if step.strut_classes != 1 else ' '}, "
            f"{step.panels:>3} panels, {step.hubs:>2} hubs")
    even = [s for s in ladder if s.is_hemisphere]
    odd = [s for s in ladder if not s.is_hemisphere]
    steps.extend([
        "now the part nobody mentions -- where the dome gets cut:",
        f"even frequencies ({', '.join(f'{s.frequency}V' for s in even)}) "
        "have a ring of hubs exactly on the equator,",
        f"so height = radius exactly: "
        + ", ".join(f"{s.height_m:.2f} m" for s in even),
        f"odd frequencies ({', '.join(f'{s.frequency}V' for s in odd)}) "
        "have no such ring; the cut lands above it,",
        f"so they stand taller than a hemisphere: "
        + ", ".join(f"{s.height_m:.2f} m" for s in odd),
    ])
    return _conclude(
        steps,
        "frequency buys smoothness and costs part variety -- and an odd "
        "frequency quietly buys you extra height you may not have wanted")


@lru_cache(maxsize=1)
def steps_hub_vs_hubless() -> tuple[str, ...]:
    """The two framing systems, on real designs from the world."""
    hubless = next(d for d in dome_types()
                   if d.frame_style == "Hubless Doubled")
    hubbed = next(d for d in dome_types()
                  if d.frequency == hubless.frequency
                  and d.frame_style == "Hub & Strut")
    steps = [
        f"both are {hubless.frequency}V domes from this world:",
        f"{hubbed.name}  --  {hubbed.frame_style}",
        f"  struts {hubbed.struts},  hubs {hubbed.hubs},  "
        f"bolts {hubbed.bolts}",
        f"{hubless.name}  --  {hubless.frame_style}",
        f"  struts {hubless.struts},  hubs {hubless.hubs},  "
        f"bolts {hubless.bolts}",
        f"the hubless frame carries "
        f"{hubless.struts / hubbed.struts:.1f}x the sticks",
        f"and exactly {hubless.hubs} hub connectors",
        "every triangle brings its own three boards, so each shared",
        "seam ends up two boards thick and bolts to its neighbour",
    ]
    if hubless.trees:
        steps.append(
            f"and because its struts are split logs, the model reports "
            f"{hubless.trees} trees to harvest at 4 wedges a log")
    return _conclude(
        steps,
        "you trade wood for hardware: more sticks, zero hubs, and "
        "nothing on the critical path you cannot cut yourself")


@lru_cache(maxsize=1)
def steps_economics() -> tuple[str, ...]:
    """Cost per square foot across the whole catalogue."""
    types = sorted(dome_types(), key=lambda d: d.cost_per_sqft)
    steps = [
        "every design priced off its own bill of materials",
        "(frame + hubs + panels + layers + foundation + fit-out):",
    ]
    for dome in types:
        steps.append(
            f"{dome.name[:26]:<26} ${dome.total_cost:>8,.0f}   "
            f"${dome.cost_per_sqft:>5.0f}/sq ft   "
            f"{dome.panel_type[:14]}")
    cheapest, dearest = types[0], types[-1]
    return _conclude(
        steps,
        f"${cheapest.cost_per_sqft:.0f} to "
        f"${dearest.cost_per_sqft:.0f} a square foot across the same "
        "geometry -- what you clad it in decides the price, not the shape")


@lru_cache(maxsize=1)
def steps_efficiency() -> tuple[str, ...]:
    """Skin per unit floor, measured across the catalogue."""
    types = sorted(dome_types(), key=lambda d: d.skin_per_floor)
    best, worst = types[0], types[-1]
    steps = [
        "skin you must build and seal, per square foot of floor:",
    ]
    for dome in types[:4]:
        steps.append(
            f"{dome.name[:26]:<26} {dome.shell_sqft:>6.0f} / "
            f"{dome.floor_sqft:>5.0f} = {dome.skin_per_floor:.2f}")
    steps.append("...")
    for dome in types[-3:]:
        steps.append(
            f"{dome.name[:26]:<26} {dome.shell_sqft:>6.0f} / "
            f"{dome.floor_sqft:>5.0f} = {dome.skin_per_floor:.2f}")
    steps.extend([
        f"best: {best.name} at {best.skin_per_floor:.2f}",
        f"worst: {worst.name} at {worst.skin_per_floor:.2f}",
        "the spread is frequency and where the dome gets cut,",
        "not the material bolted to it",
    ])
    return _conclude(
        steps,
        f"{best.skin_per_floor:.2f} against {worst.skin_per_floor:.2f} "
        "square feet of envelope per square foot of floor -- the cheapest "
        "wall is the one the geometry never asks you to build")


@lru_cache(maxsize=1)
def steps_scale() -> tuple[str, ...]:
    """What radius does to a fixed parts list, measured in this engine."""
    smallest = min(dome_types(), key=lambda d: d.radius_m)
    largest = max(dome_types(), key=lambda d: d.radius_m)
    same = [d for d in dome_types() if d.frequency == 3]
    steps = [
        "part counts depend on frequency alone, never on size:",
    ]
    for dome in same[:4]:
        steps.append(
            f"{dome.name[:26]:<26} r = {dome.radius_m:.1f} m -> "
            f"{dome.struts} struts, {dome.panels} panels")
    steps.extend([
        "same three numbers, different buildings",
        f"smallest in the catalogue: {smallest.name}, "
        f"{smallest.diameter_ft:.0f} ft across, "
        f"{smallest.floor_sqft:.0f} sq ft",
        f"largest: {largest.name}, {largest.diameter_ft:.0f} ft across, "
        f"{largest.floor_sqft:.0f} sq ft",
        f"that is {largest.floor_sqft / smallest.floor_sqft:.1f}x the "
        "floor from the same list of operations",
    ])
    return _conclude(
        steps,
        f"{largest.floor_sqft / smallest.floor_sqft:.1f} times the house "
        "for the same parts list -- size is a number you type, not a "
        "harder build")


ALL_SCREENS: tuple[tuple[str, object], ...] = (
    ("catalogue", steps_catalogue),
    ("frequency", steps_frequency),
    ("hub_vs_hubless", steps_hub_vs_hubless),
    ("economics", steps_economics),
    ("efficiency", steps_efficiency),
    ("scale", steps_scale),
)


def world_report() -> str:
    """A portable audit of every dome type and every math screen."""
    lines = [
        "THE DOME CREATOR WORLD -- EVERY DESIGN, MEASURED",
        "",
        "Each design below was rebuilt with dome_model.DomeModel and its",
        "numbers read off the finished model, exactly as the walkable",
        "simulator does it.  Material densities and unit prices come from",
        "materials.py, which declares them as its own inputs.",
        "",
    ]
    for dome in dome_types():
        lines.extend([
            f"== {dome.name} ==",
            f"  {dome.frequency}V, radius {dome.radius_m:.2f} m "
            f"({dome.diameter_ft:.0f} ft across), {dome.frame_style}",
            f"  frame     {dome.frame_material}, {dome.strut_shape}",
            f"  skin      {dome.panel_type}",
            f"  struts    {dome.struts} in {dome.strut_classes} "
            f"length class(es)",
            f"  panels    {dome.panels}    hubs {dome.hubs}    "
            f"bolts {dome.bolts}",
            f"  floor     {dome.floor_sqft:,.0f} sq ft   "
            f"shell {dome.shell_sqft:,.0f} sq ft   "
            f"height {dome.height_ft:.1f} ft",
            f"  weight    {dome.weight_kg:,.0f} kg",
            f"  cost      ${dome.total_cost:,.0f} "
            f"(${dome.cost_per_sqft:.0f}/sq ft)",
        ])
        if dome.trees:
            lines.append(f"  trees     {dome.trees} to harvest")
        if dome.solar_watts:
            lines.append(f"  solar     {dome.solar_watts:,.0f} W")
        lines.append("")
    lines.append("MATH SCREENS")
    lines.append("")
    for name, builder in ALL_SCREENS:
        lines.append(f"== {name.upper()} ==")
        lines.extend(f"  {line}" for line in builder())
        lines.append("")
    return "\n".join(lines)


def validate_world_facts() -> None:
    """Prove the bridge into the simulator's own modules."""
    types = dome_types()
    assert len(types) == len(presets.PRESETS), len(types)
    assert len(types) >= 12, len(types)

    names = [dome.name for dome in types]
    assert len(set(names)) == len(names), "a preset name is repeated"

    for dome in types:
        # Every design must actually be a dome: real parts, real size,
        # real money. A preset that silently failed to build would
        # otherwise reach the screen as a row of zeros.
        assert dome.struts > 0 and dome.panels > 0, dome.name
        assert dome.floor_sqft > 0.0 and dome.shell_sqft > 0.0, dome.name
        assert dome.total_cost > 0.0, dome.name
        assert 1 <= dome.frequency <= 4, dome.name
        # A dome encloses less skin than a box would, so its envelope
        # can never be more than about three times its own floor.
        assert 1.0 < dome.skin_per_floor < 3.0, (dome.name,
                                                 dome.skin_per_floor)
        # The drawable model must agree with the counted one.
        model = dome_geometry(dome)
        assert len(model.struts) == dome.struts, dome.name
        assert len(model.panels) == dome.panels, dome.name

    # Hubless framing is the whole point of one preset: it must have no
    # hubs and it must carry more sticks than the hubbed dome of the
    # same frequency, or the comparison screen is telling a story the
    # model does not support.
    hubless = [d for d in types if d.frame_style == "Hubless Doubled"]
    assert hubless, "no hubless preset in the world"
    for dome in hubless:
        assert dome.hubs == 0, (dome.name, dome.hubs)
        assert dome.bolts > 0, dome.name
        peer = next(d for d in types if d.frequency == dome.frequency
                    and d.frame_style == "Hub & Strut")
        assert dome.struts > peer.struts, (dome.name, peer.name)

    # The frequency ladder must be monotonic in parts, and the parity
    # claim the screen makes has to hold on the built models.
    ladder = frequency_ladder()
    assert [s.frequency for s in ladder] == [1, 2, 3, 4]
    for earlier, later in zip(ladder, ladder[1:]):
        assert later.struts > earlier.struts, (earlier, later)
        assert later.panels > earlier.panels, (earlier, later)
    for step in ladder:
        assert step.is_hemisphere == (step.frequency % 2 == 0), step
        # An odd frequency must genuinely stand taller than its radius.
        if not step.is_hemisphere:
            assert step.height_m > step.radius_m, step

    # Every screen builds, and ends on a sentence rather than a number.
    for name, builder in ALL_SCREENS:
        steps = builder()
        assert len(steps) >= 5, (name, len(steps))
        assert all(line.strip() for line in steps), name
        assert len(steps[-1]) >= 30, (name, steps[-1])
