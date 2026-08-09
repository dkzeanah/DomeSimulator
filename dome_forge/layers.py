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
        key="assemblies",
        label="Panel assemblies",
        blurb=(
            "The real dome: 40 individual triangles, each with its own "
            "three struts and its own fill. Click any triangle in the 3D "
            "view to select it, then change what it is made of -- a "
            "window here, a vent there, solar on the sunny side. The "
            "three edges of one triangle do not have to use the same "
            "strut."
        ),
        params=(
            ParamSpec("seam", "Seam gap", "float", 0.004, 0.0, 0.05, 0.001,
                      unit="m",
                      help="A sliver left at each seam so the two struts "
                           "meeting there stay tellable apart on screen."),
            ParamSpec("show_fills", "Show fills", "bool", True,
                      help="Turn off to see the bare frame."),
            ParamSpec("highlight", "Highlight selection", "bool", True,
                      help="Light up whichever triangle is selected."),
        ),
    ),
    LayerKind(
        key="waist_joints",
        label="Hourglass waist joints",
        blurb=(
            "Where two equilateral triangles meet point to point, "
            "something has to make that into a real joint -- banding, "
            "wooden braces, a gusset plate, or one continuous piece. "
            "There are ten of these waists in a hemisphere."
        ),
        params=(
            ParamSpec("size", "Joint size", "float", 1.0, 0.3, 2.5, 0.05,
                      unit="x", help="Scale the hardware up or down."),
        ),
    ),
    LayerKind(
        key="triangle_frames",
        label="Triangle frames (uniform)",
        blurb=(
            "How these domes are actually built: 40 separate triangular "
            "frames, each three flat-laid boards mitered at the corners, "
            "bolted to their neighbours. Every seam ends up two boards "
            "thick because each triangle brings its own -- so there are no "
            "hubs anywhere in the dome."
        ),
        params=(
            ParamSpec("width", "Board width", "float", 0.089, 0.03, 0.30, 0.001,
                      unit="m", help="The face width of the board, measured "
                                     "inward from the seam. 0.089m is a "
                                     "nominal 2x4's real 3-1/2 inch width."),
            ParamSpec("thickness", "Board thickness", "float", 0.038, 0.01, 0.15,
                      0.001, unit="m",
                      help="How deep the board is, measured toward the "
                           "centre of the dome. 0.038m is a 2x4's real "
                           "1-1/2 inch thickness."),
            ParamSpec("seam", "Seam gap", "float", 0.004, 0.0, 0.05, 0.001,
                      unit="m",
                      help="A sliver of space left at each seam so the two "
                           "boards meeting there stay tellable apart on "
                           "screen. Set it to 0 for the true built position."),
            ParamSpec("bolts", "Show bolts", "bool", True,
                      help="Draw the bolts that clamp each pair of boards "
                           "together along a seam."),
            ParamSpec("bolt_count", "Bolts per seam", "int", 3, 1, 8, 1),
            ParamSpec("bolt_size", "Bolt size", "float", 0.016, 0.004, 0.05, 0.001,
                      unit="m"),
            ParamSpec("split_classes", "Colour by triangle type", "bool", True,
                      help="Show the 10 equilateral triangles and the 30 "
                           "isosceles ones in different shades -- these are "
                           "the two shapes you build jigs for."),
            _color("tint", "Colour", "timber", PALETTE),
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
class Assignments:
    """What each individual triangle is made of.

    A dome is rarely all one thing: a few panels are windows, one is a
    door, the south face carries solar. Rather than force every triangle
    to match, this holds a sensible default plus per-triangle overrides,
    keyed by face index. Struts default per edge *class*, since the two
    strut lengths are usually different stock in a real build.
    """

    fill: str = "polycarbonate"
    strut_long: str = "lumber_2x4"
    strut_short: str = "lumber_2x4"
    face_fill: dict = field(default_factory=dict)
    face_struts: dict = field(default_factory=dict)
    # How the two points of each hourglass are joined. Keyed by the
    # hourglass's waist, because the joint belongs to the waist rather
    # than to either triangle -- one triangle sits in several hourglasses.
    joint: str = "banding"
    waist_joint: dict = field(default_factory=dict)

    def joint_for(self, hourglass_index: int) -> str:
        return self.waist_joint.get(str(hourglass_index), self.joint)

    def fill_for(self, face_index: int) -> str:
        return self.face_fill.get(str(face_index), self.fill)

    def strut_for(self, face_index: int, edge_class: str) -> str:
        override = self.face_struts.get(str(face_index))
        if isinstance(override, list) and len(override) == 3:
            return override[0]
        return self.strut_long if edge_class == "LONG" else self.strut_short

    def strut_triple(self, face_index: int, edge_classes) -> list[str]:
        override = self.face_struts.get(str(face_index))
        if isinstance(override, list) and len(override) == 3:
            return list(override)
        return [self.strut_long if name == "LONG" else self.strut_short
                for name in edge_classes]

    def set_face_struts(self, face_index: int, triple) -> None:
        self.face_struts[str(face_index)] = list(triple)

    def clear_face(self, face_index: int) -> None:
        self.face_fill.pop(str(face_index), None)
        self.face_struts.pop(str(face_index), None)

    def to_json(self) -> dict:
        return {
            "fill": self.fill,
            "strut_long": self.strut_long,
            "strut_short": self.strut_short,
            "face_fill": dict(self.face_fill),
            "face_struts": {k: list(v) for k, v in self.face_struts.items()},
            "joint": self.joint,
            "waist_joint": dict(self.waist_joint),
        }

    @staticmethod
    def from_json(data: dict) -> "Assignments":
        return Assignments(
            fill=data.get("fill", "polycarbonate"),
            strut_long=data.get("strut_long", "lumber_2x4"),
            strut_short=data.get("strut_short", "lumber_2x4"),
            face_fill=dict(data.get("face_fill", {})),
            face_struts={k: list(v)
                         for k, v in data.get("face_struts", {}).items()},
            joint=data.get("joint", "banding"),
            waist_joint=dict(data.get("waist_joint", {})),
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
                 settings: DomeSettings | None = None,
                 assignments: Assignments | None = None) -> None:
        self.layers: list[Layer] = list(layers or [])
        self.settings = settings or DomeSettings()
        self.assignments = assignments or Assignments()
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
            "schema": 2,
            "settings": self.settings.to_json(),
            "assignments": self.assignments.to_json(),
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
        return LayerStack(
            layers,
            DomeSettings.from_json(data.get("settings", {})),
            Assignments.from_json(data.get("assignments", {})),
        )

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
        "veins", "vein_water", "assemblies", "waist_joints",
        "micro_drains", "panel_runoff", "rain",
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


def split_log_stack() -> LayerStack:
    """A dome framed the way a split-log build actually goes together:
    half-round logs on the long seams, quarter-round on the short ones,
    and 2x2 where a lighter stick will do. Mixing sections like this is
    normal, and it is why the panel geometry has to cope with three
    different strut widths meeting at one corner."""
    stack = default_stack()
    stack.assignments = Assignments(
        fill="polycarbonate",
        strut_long="log_half",
        strut_short="log_quarter",
    )
    # The equilateral caps get the lighter 2x2 on every edge.
    for index in _EQUILATERAL_FACES:
        stack.assignments.set_face_struts(
            index, ["lumber_2x2", "lumber_2x2", "lumber_2x2"])
    return stack


def _equilateral_face_indices() -> tuple[int, ...]:
    """The 10 all-LONG faces, found from the geometry rather than typed
    out, so this keeps working if the geometry is ever regenerated."""
    from two_v_demo.geometry import build_demo_geometry
    geo = build_demo_geometry()
    class_by_edge = {tuple(sorted(edge)): name
                     for edge, name in zip(geo.edges, geo.edge_class_by_edge)}
    found = []
    for index, face in enumerate(geo.hemisphere_faces):
        names = [class_by_edge[tuple(sorted((int(face[i]),
                                             int(face[(i + 1) % 3]))))]
                 for i in range(3)]
        if names.count("LONG") == 3:
            found.append(index)
    return tuple(found)


_EQUILATERAL_FACES = _equilateral_face_indices()
