"""The layer model for the single-dome builder.

A dome here is a *stack of layers*, the way an image is a stack of layers
in a paint program: a structural frame, panels over it, a vein network
inside the seams, liners, insulation, plumbing, water. Each layer can be
hidden, faded, reordered, duplicated, and tuned through its own named
parameters.

This module is deliberately free of OpenGL, pygame, and geometry: it is
just the description of what layers exist, what knobs each one has, and
what the user has currently set them to. That keeps it testable without a
display, and keeps the "what can be built" list in one readable place.
"""

from __future__ import annotations

import json
from dataclasses import dataclass, field, replace
from pathlib import Path


@dataclass(frozen=True)
class ParamSpec:
    """One tunable knob on a layer.

    ``kind`` is "float", "int", "bool", or "choice". ``help`` is written
    for someone who has never built a dome and never written code -- it
    says what the number physically means, not what the variable does.
    """

    key: str
    label: str
    kind: str
    default: float | int | bool | str
    low: float = 0.0
    high: float = 1.0
    step: float = 0.01
    choices: tuple[str, ...] = ()
    unit: str = ""
    help: str = ""

    def clamp(self, value):
        if self.kind == "bool":
            return bool(value)
        if self.kind == "choice":
            return value if value in self.choices else self.default
        if self.kind == "int":
            return int(max(self.low, min(self.high, int(value))))
        return float(max(self.low, min(self.high, float(value))))

    def format(self, value) -> str:
        if self.kind == "bool":
            return "on" if value else "off"
        if self.kind == "choice":
            return str(value)
        if self.kind == "int":
            return f"{int(value)}{self.unit}"
        return f"{float(value):.3g}{self.unit}"


@dataclass(frozen=True)
class LayerKind:
    """A type of layer that can be added to the stack."""

    key: str
    label: str
    blurb: str
    params: tuple[ParamSpec, ...] = ()
    default_opacity: float = 1.0
    translucent: bool = False

    def spec(self, key: str) -> ParamSpec | None:
        for param in self.params:
            if param.key == key:
                return param
        return None

    def defaults(self) -> dict:
        return {param.key: param.default for param in self.params}


def _color(key: str, label: str, default: str, choices: tuple[str, ...]) -> ParamSpec:
    return ParamSpec(
        key, label, "choice", default, choices=choices,
        help="Surface colour, so overlapping layers stay tellable apart.",
    )


PALETTE = (
    "steel", "aluminium", "timber", "glass", "copper",
    "water", "amber", "moss", "charcoal", "white",
)


# ---------------------------------------------------------------------------
# The catalogue of buildable layers.
#
# Order here is the order they appear in the "add layer" list. The default
# stack below picks a sensible subset; every one of these can be added,
# removed, duplicated, and reordered freely.
# ---------------------------------------------------------------------------

LAYER_KINDS: tuple[LayerKind, ...] = (
    LayerKind(
        key="ground",
        label="Ground pad",
        blurb=(
            "The slab the dome sits on. Mostly a visual reference so you "
            "can tell which way is down and how big the dome really is."
        ),
        params=(
            ParamSpec("extent", "Pad size", "float", 1.6, 1.0, 4.0, 0.05, unit="x",
                      help="How far the pad reaches past the dome's base, "
                           "as a multiple of the dome radius."),
            _color("tint", "Colour", "charcoal", PALETTE),
        ),
    ),
    LayerKind(
        key="frame",
        label="Strut frame",
        blurb=(
            "The load-bearing skeleton: one strut per triangle edge. A 2V "
            "dome uses exactly two strut lengths, and this layer can colour "
            "them differently so the pattern is obvious."
        ),
        params=(
            ParamSpec("thickness", "Strut thickness", "float", 0.055, 0.01, 0.2, 0.005,
                      unit="m", help="Radius of each strut. Thicker looks "
                                     "heavier and hides more of what's behind."),
            ParamSpec("sides", "Roundness", "int", 8, 3, 16, 1,
                      help="How many flat faces make up each round strut. "
                           "Higher is smoother and slower."),
            ParamSpec("split_classes", "Colour by length", "bool", True,
                      help="Show the two strut lengths in different colours."),
            _color("tint", "Colour", "aluminium", PALETTE),
        ),
    ),
    LayerKind(
        key="hubs",
        label="Hub connectors",
        blurb=(
            "The joints where struts meet. A 2V hemisphere has a fixed "
            "number of them, and they are where most of a real build's "
            "cost and precision goes."
        ),
        params=(
            ParamSpec("size", "Hub size", "float", 0.11, 0.02, 0.35, 0.005, unit="m",
                      help="Radius of the connector ball at each joint."),
            _color("tint", "Colour", "steel", PALETTE),
        ),
    ),
    LayerKind(
        key="panels",
        label="Panels",
        blurb=(
            "The triangular skin between the struts. Set 'Dish depth' above "
            "zero and each panel curves inward like a golf-ball dimple, so "
            "rain runs to the middle instead of sheeting off the seams."
        ),
        params=(
            ParamSpec("inset", "Gap from struts", "float", 0.05, 0.0, 0.3, 0.005, unit="m",
                      help="How far each panel stops short of the struts."),
            ParamSpec("dish", "Dish depth", "float", 0.10, 0.0, 0.45, 0.005,
                      help="0 is a flat panel. Higher dishes the panel inward "
                           "toward its centre, like a golf-ball dimple, so "
                           "water collects at one low point."),
            ParamSpec("resolution", "Curve detail", "int", 6, 1, 14, 1,
                      help="How finely the dish is subdivided. Higher is "
                           "smoother and slower."),
            ParamSpec("lift", "Stand-off", "float", 0.0, -0.25, 0.25, 0.005, unit="m",
                      help="Push the whole panel outward (+) or inward (-) "
                           "from the frame surface."),
            _color("tint", "Colour", "glass", PALETTE),
        ),
        default_opacity=0.55,
        translucent=True,
    ),
    LayerKind(
        key="micro_drains",
        label="Micro-drains",
        blurb=(
            "A small outlet at the low point of each dished panel. This is "
            "what makes the dimple useful: water that pools in the dish "
            "leaves through here instead of finding a seam."
        ),
        params=(
            ParamSpec("bore", "Outlet size", "float", 0.045, 0.01, 0.14, 0.002, unit="m",
                      help="Radius of the drain opening."),
            ParamSpec("spout", "Spout length", "float", 0.13, 0.0, 0.5, 0.01, unit="m",
                      help="How far the drain tube pokes inward before it "
                           "hands water to the vein network."),
            _color("tint", "Colour", "copper", PALETTE),
        ),
    ),
    LayerKind(
        key="veins",
        label="Seam veins (gasket)",
        blurb=(
            "A channel running along the inside of every seam, held clear "
            "of the outer skin by a deliberate gap. Anything that gets past "
            "a seam lands in a vein instead of dripping into the room -- "
            "which turns the classic leaky-dome complaint into plumbing."
        ),
        params=(
            ParamSpec("gap", "Gap from skin", "float", 0.16, 0.02, 0.6, 0.01, unit="m",
                      help="Clear distance between the outer skin and the "
                           "vein. This gap is the whole point: it leaves an "
                           "inspectable air space instead of sealing wet "
                           "material against the structure."),
            ParamSpec("bore", "Channel width", "float", 0.075, 0.02, 0.22, 0.005, unit="m",
                      help="Radius of the channel's cross-section."),
            ParamSpec("wrap", "Channel wrap", "float", 0.62, 0.25, 1.0, 0.01,
                      help="How far the channel curls around. Low is a shallow "
                           "open gutter, high is nearly a closed pipe."),
            ParamSpec("segments", "Cross-section detail", "int", 7, 3, 16, 1,
                      help="Facets across the channel's curve."),
            ParamSpec("samples", "Length detail", "int", 9, 2, 24, 1,
                      help="How many points along each seam. Higher follows "
                           "the dome's curve more closely."),
            _color("tint", "Colour", "copper", PALETTE),
        ),
    ),
    LayerKind(
        key="vein_water",
        label="Water in the veins",
        blurb=(
            "Animated flow inside the vein network. Every seam drains "
            "downhill toward the collector ring at the base, so you can "
            "watch where water actually goes."
        ),
        params=(
            ParamSpec("speed", "Flow speed", "float", 0.35, 0.02, 1.5, 0.01,
                      help="How fast the water travels along the seams."),
            ParamSpec("density", "Droplets per seam", "int", 4, 1, 14, 1,
                      help="How many parcels of water are in each seam at once."),
            ParamSpec("size", "Droplet size", "float", 0.055, 0.01, 0.16, 0.002, unit="m",
                      help="Radius of each parcel of water."),
            _color("tint", "Colour", "water", PALETTE),
        ),
        translucent=True,
        default_opacity=0.9,
    ),
    LayerKind(
        key="panel_runoff",
        label="Runoff on panels",
        blurb=(
            "Droplets sliding down the face of each dished panel toward its "
            "micro-drain. Only makes visual sense when Panels have some "
            "dish depth."
        ),
        params=(
            ParamSpec("speed", "Runoff speed", "float", 0.5, 0.02, 2.0, 0.01,
                      help="How fast droplets slide to the low point."),
            ParamSpec("density", "Droplets per panel", "int", 3, 1, 10, 1),
            ParamSpec("size", "Droplet size", "float", 0.04, 0.01, 0.12, 0.002, unit="m"),
            _color("tint", "Colour", "water", PALETTE),
        ),
        translucent=True,
        default_opacity=0.85,
    ),
    LayerKind(
        key="shell",
        label="Shell surface",
        blurb=(
            "A continuous surface at a chosen depth -- use it as an outer "
            "rain skin, an inner liner, a vapour barrier, or a layer of "
            "insulation. Add several at different offsets to build up a "
            "real wall section."
        ),
        params=(
            ParamSpec("offset", "Depth", "float", -0.30, -1.2, 0.5, 0.01, unit="m",
                      help="Distance from the frame surface. Negative is "
                           "inside the dome, positive is outside it."),
            ParamSpec("thickness", "Thickness", "float", 0.0, 0.0, 0.6, 0.01, unit="m",
                      help="Give the surface real depth instead of being "
                           "paper-thin. Useful for insulation."),
            ParamSpec("rings", "Detail", "int", 10, 3, 26, 1),
            _color("tint", "Colour", "timber", PALETTE),
        ),
        default_opacity=0.4,
        translucent=True,
    ),
    LayerKind(
        key="collector_ring",
        label="Collector ring",
        blurb=(
            "The gutter around the base that every vein empties into. This "
            "is where all those separate seam channels become one flow."
        ),
        params=(
            ParamSpec("bore", "Gutter size", "float", 0.11, 0.03, 0.3, 0.005, unit="m"),
            ParamSpec("drop", "Height above pad", "float", 0.14, -0.3, 1.0, 0.01, unit="m",
                      help="How high the ring sits. Slightly above the pad "
                           "keeps it serviceable."),
            ParamSpec("inset", "Pull inward", "float", 0.10, -0.3, 0.8, 0.01, unit="m"),
            _color("tint", "Colour", "copper", PALETTE),
        ),
    ),
    LayerKind(
        key="downpipe",
        label="Downpipe",
        blurb="The single pipe carrying collected water down into the tank.",
        params=(
            ParamSpec("bore", "Pipe size", "float", 0.1, 0.03, 0.3, 0.005, unit="m"),
            ParamSpec("azimuth", "Position around dome", "float", 210.0, 0.0, 360.0, 1.0,
                      unit="deg", help="Where around the base the pipe drops."),
            _color("tint", "Colour", "steel", PALETTE),
        ),
    ),
    LayerKind(
        key="cistern",
        label="Cistern",
        blurb=(
            "The tank under the dome that everything drains into. The fill "
            "level is adjustable so you can see the captured volume."
        ),
        params=(
            ParamSpec("radius", "Tank radius", "float", 1.15, 0.3, 3.0, 0.05, unit="m"),
            ParamSpec("depth", "Tank depth", "float", 1.5, 0.3, 4.0, 0.05, unit="m"),
            ParamSpec("sink", "Buried depth", "float", 0.25, 0.0, 2.0, 0.05, unit="m",
                      help="How far below the pad the tank top sits."),
            ParamSpec("fill", "Water level", "float", 0.55, 0.0, 1.0, 0.01,
                      help="How full the tank is, as a fraction."),
            _color("tint", "Colour", "steel", PALETTE),
        ),
        default_opacity=0.5,
        translucent=True,
    ),
    LayerKind(
        key="rain",
        label="Rain",
        blurb=(
            "Falling rain above the dome, so the capture story reads at a "
            "glance. Purely visual -- it does not drive the other layers."
        ),
        params=(
            ParamSpec("count", "Drop count", "int", 220, 10, 900, 10),
            ParamSpec("speed", "Fall speed", "float", 3.2, 0.3, 12.0, 0.1),
            ParamSpec("spread", "Spread", "float", 1.5, 0.8, 3.5, 0.05, unit="x",
                      help="How wide the rain field is, as a multiple of the "
                           "dome radius."),
            ParamSpec("length", "Streak length", "float", 0.26, 0.03, 1.0, 0.01, unit="m"),
            _color("tint", "Colour", "water", PALETTE),
        ),
        translucent=True,
        default_opacity=0.5,
    ),
)


KIND_BY_KEY = {kind.key: kind for kind in LAYER_KINDS}


@dataclass
class Layer:
    """One entry in the stack."""

    kind: str
    name: str = ""
    visible: bool = True
    opacity: float = 1.0
    params: dict = field(default_factory=dict)

    def __post_init__(self) -> None:
        spec = KIND_BY_KEY.get(self.kind)
        if spec is None:
            raise KeyError(f"Unknown layer kind: {self.kind}")
        if not self.name:
            self.name = spec.label
        merged = spec.defaults()
        merged.update(self.params or {})
        self.params = {
            key: (spec.spec(key).clamp(value) if spec.spec(key) else value)
            for key, value in merged.items()
        }

    @property
    def spec(self) -> LayerKind:
        return KIND_BY_KEY[self.kind]

    def get(self, key: str):
        return self.params.get(key, KIND_BY_KEY[self.kind].defaults().get(key))

    def set(self, key: str, value) -> None:
        spec = self.spec.spec(key)
        self.params[key] = spec.clamp(value) if spec else value

    def to_json(self) -> dict:
        return {
            "kind": self.kind,
            "name": self.name,
            "visible": self.visible,
            "opacity": round(float(self.opacity), 4),
            "params": dict(self.params),
        }

    @staticmethod
    def from_json(data: dict) -> "Layer":
        return Layer(
            kind=data["kind"],
            name=data.get("name", ""),
            visible=bool(data.get("visible", True)),
            opacity=float(data.get("opacity", 1.0)),
            params=dict(data.get("params", {})),
        )


@dataclass
class DomeSettings:
    """Whole-dome settings that are not themselves a layer."""

    radius: float = 4.2
    cut_enabled: bool = False
    cut_start: float = 20.0
    cut_sweep: float = 110.0

    def to_json(self) -> dict:
        return {
            "radius": self.radius,
            "cut_enabled": self.cut_enabled,
            "cut_start": self.cut_start,
            "cut_sweep": self.cut_sweep,
        }

    @staticmethod
    def from_json(data: dict) -> "DomeSettings":
        return DomeSettings(
            radius=float(data.get("radius", 4.2)),
            cut_enabled=bool(data.get("cut_enabled", False)),
            cut_start=float(data.get("cut_start", 20.0)),
            cut_sweep=float(data.get("cut_sweep", 110.0)),
        )


class LayerStack:
    """An ordered list of layers, bottom-most first."""

    def __init__(self, layers: list[Layer] | None = None,
                 settings: DomeSettings | None = None) -> None:
        self.layers: list[Layer] = list(layers or [])
        self.settings = settings or DomeSettings()
        self.selected = 0 if self.layers else -1

    # -- editing ---------------------------------------------------------

    def add(self, kind: str, at: int | None = None) -> Layer:
        layer = Layer(kind=kind)
        index = len(self.layers) if at is None else max(0, min(at, len(self.layers)))
        self.layers.insert(index, layer)
        layer.opacity = KIND_BY_KEY[kind].default_opacity
        self.selected = index
        return layer

    def remove(self, index: int) -> None:
        if 0 <= index < len(self.layers):
            self.layers.pop(index)
            self.selected = min(self.selected, len(self.layers) - 1)

    def duplicate(self, index: int) -> Layer | None:
        if not (0 <= index < len(self.layers)):
            return None
        source = self.layers[index]
        clone = replace(source, name=f"{source.name} copy", params=dict(source.params))
        self.layers.insert(index + 1, clone)
        self.selected = index + 1
        return clone

    def move(self, index: int, delta: int) -> None:
        target = index + delta
        if 0 <= index < len(self.layers) and 0 <= target < len(self.layers):
            self.layers[index], self.layers[target] = (
                self.layers[target], self.layers[index]
            )
            self.selected = target

    @property
    def active(self) -> Layer | None:
        if 0 <= self.selected < len(self.layers):
            return self.layers[self.selected]
        return None

    # -- persistence -----------------------------------------------------

    def to_json(self) -> dict:
        return {
            "schema": 1,
            "settings": self.settings.to_json(),
            "layers": [layer.to_json() for layer in self.layers],
        }

    @staticmethod
    def from_json(data: dict) -> "LayerStack":
        layers = []
        for entry in data.get("layers", []):
            try:
                layers.append(Layer.from_json(entry))
            except KeyError:
                # An unknown layer kind (an older or newer preset) is
                # skipped rather than taking the whole file down with it.
                continue
        return LayerStack(layers, DomeSettings.from_json(data.get("settings", {})))

    def save(self, path: Path) -> Path:
        path = Path(path)
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(json.dumps(self.to_json(), indent=2) + "\n", encoding="utf-8")
        return path

    @staticmethod
    def load(path: Path) -> "LayerStack":
        return LayerStack.from_json(
            json.loads(Path(path).read_text(encoding="utf-8"))
        )


def default_stack() -> LayerStack:
    """The dome you get on first launch: a water-harvesting shell with the
    vein network and dished panels already switched on, because that is the
    idea this tool exists to make visible."""
    stack = LayerStack()
    for kind in (
        "ground", "cistern", "downpipe", "collector_ring",
        "veins", "vein_water", "frame", "hubs",
        "panels", "micro_drains", "panel_runoff", "rain",
    ):
        stack.add(kind)
    # Rain starts off: the static dome reads more clearly on first open,
    # and it is a one-click reveal from the panel.
    for layer in stack.layers:
        if layer.kind == "rain":
            layer.visible = False
    stack.selected = next(
        (i for i, layer in enumerate(stack.layers) if layer.kind == "veins"), 0
    )
    return stack
