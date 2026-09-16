"""Codified visual objects: the nouns the films show, as drawable, knob-driven things.

The catalogue in :mod:`two_v_demo.lexicon` says what a word *means*; this module says
what it *looks like*. Each :class:`VisualObject` is a pure function of a handful of
named knobs -- a tree with a ``fell`` knob that runs from standing to on the ground, a
log with an ``explode`` knob that runs from whole to sixty-four wedges in the air -- so
a film animates it by moving one number across a chapter, the same way the presenter
engine moves an object's ``progress`` across a shot.

Most of the objects here are *wrappers*, not drawings. The wedge prism, the pinwheel
shell, the simulator's own solved dome, the rough timber and the articulated worker
already exist in this repository, and a film about the wedge dome must show those
rather than a sketch of them. A wrapper draws the real thing into a scratch batch and
splices it into the stage at any position, size and heading, so code that was written
to draw at the origin becomes placeable without being edited.

Two engines use the same objects:

* the masterclass renderer: a scene painter calls ``draw(stage_for(app, opaque,
  transparent), "pine_tree", fell=p)``;
* the presenter engine: :func:`presenter_emitter` adapts any object to its
  ``emit(o, tr, params, t, targets)`` contract, and :func:`presenter_object_specs`
  describes the knobs to the Studio in its own ``ParamSpec`` terms.

New drawings live in their own modules (:mod:`two_v_demo.visuals_forest` for the tree
and everything cut from it) and register themselves here.
"""

from __future__ import annotations

import math
from dataclasses import dataclass, field
from typing import Callable, Mapping

import numpy as np

from .render_kit import (
    AMBER,
    CYAN,
    RED,
    WHITE,
    TriangleBatch,
    WorldIcon,
    WorldLabel,
    clamp,
)


# ----------------------------------------------------------------------
# Knobs and the stage an object draws onto
# ----------------------------------------------------------------------

@dataclass(frozen=True)
class Knob:
    """One number an object can be given, and what it physically means."""

    key: str
    label: str
    default: float
    low: float
    high: float
    unit: str = ""
    help: str = ""
    animate: bool = False
    """Meant to be driven from 0 to 1 across a chapter or a shot."""

    def clamp(self, value) -> float:
        return float(max(self.low, min(self.high, float(value))))


def rgb(colour) -> tuple[int, int, int]:
    """A 0..1 render colour as the 0..255 triple the overlay wants."""
    if all(isinstance(c, int) for c in colour[:3]) and max(colour[:3]) > 1:
        return (int(colour[0]), int(colour[1]), int(colour[2]))
    return tuple(int(round(clamp(float(c)) * 255)) for c in colour[:3])


@dataclass
class Stage:
    """Where an object draws: two batches, the overlay's lists, and a placement.

    Objects are written in their own frame -- standing on the ground at the origin,
    facing +X -- and the stage moves, turns and scales them. ``labels`` and ``icons``
    are the app's ``world_labels`` and ``world_icons`` lists, so text and pictograms
    an object pins to itself land in the overlay like any painter's.
    """

    opaque: TriangleBatch
    transparent: TriangleBatch
    labels: list = field(default_factory=list)
    icons: list = field(default_factory=list)
    origin: tuple[float, float, float] = (0.0, 0.0, 0.0)
    scale: float = 1.0
    yaw_deg: float = 0.0

    def _rotation(self) -> np.ndarray:
        angle = math.radians(self.yaw_deg)
        c, s = math.cos(angle), math.sin(angle)
        return np.array([[c, -s, 0.0], [s, c, 0.0], [0.0, 0.0, 1.0]])

    def at(self, point) -> np.ndarray:
        """A point in the object's own frame, in the world."""
        local = np.asarray(point, dtype=np.float64) * self.scale
        return self._rotation() @ local + np.asarray(self.origin, dtype=np.float64)

    def direction(self, vector) -> np.ndarray:
        return self._rotation() @ np.asarray(vector, dtype=np.float64)

    def splice(self, source: TriangleBatch, transparent: bool = False) -> int:
        """Move everything drawn into ``source`` onto the stage, placed.

        This is what lets an existing drawing function -- one that only knows how to
        draw at the origin -- be put anywhere at any size without being changed.
        Returns the number of triangles moved.
        """
        if not source.vertices:
            return 0
        data = np.asarray(source.vertices, dtype=np.float64).reshape(-1, 10)
        rotation = self._rotation()
        data[:, 0:3] = (data[:, 0:3] * self.scale) @ rotation.T \
            + np.asarray(self.origin, dtype=np.float64)
        data[:, 3:6] = data[:, 3:6] @ rotation.T
        target = self.transparent if transparent else self.opaque
        target.vertices.extend(data.ravel().tolist())
        return len(data) // 3

    def label(self, point, text: str, colour=WHITE) -> None:
        self.labels.append(WorldLabel(self.at(point), text, rgb(colour)))

    def icon(self, point, key: str, size: float = 64.0, colour=None,
             alpha: float = 1.0, angle: float = 0.0, toward=None) -> None:
        if alpha <= 0.004:
            return
        self.icons.append(WorldIcon(self.at(point), key, size,
                                    rgb(colour) if colour is not None else None,
                                    clamp(alpha), angle,
                                    self.at(toward) if toward is not None else None))


def stage_for(app, opaque: TriangleBatch, transparent: TriangleBatch,
              origin=(0.0, 0.0, 0.0), scale: float = 1.0,
              yaw_deg: float = 0.0) -> Stage:
    """A stage that writes into a live masterclass frame."""
    if not hasattr(app, "world_icons"):
        app.world_icons = []
    return Stage(opaque, transparent, app.world_labels, app.world_icons,
                 tuple(float(v) for v in origin), float(scale), float(yaw_deg))


# ----------------------------------------------------------------------
# The object model and the registry
# ----------------------------------------------------------------------

Anchors = dict[str, np.ndarray]
Drawer = Callable[[Stage, Mapping[str, float]], Anchors]


@dataclass(frozen=True)
class VisualObject:
    """One drawable noun."""

    key: str
    label: str
    category: str
    """The taxonomy category key this object draws nouns from."""
    blurb: str
    knobs: tuple[Knob, ...]
    draw: Drawer
    source: str
    """``new``, or the dotted path of the existing code it wraps."""
    reach: float = 5.0
    """Roughly how far the object extends from its origin, for framing a camera."""
    words: tuple[str, ...] = ()
    """The nouns this object is the picture of."""

    def knob(self, key: str) -> Knob | None:
        return next((k for k in self.knobs if k.key == key), None)

    def defaults(self) -> dict[str, float]:
        return {k.key: k.default for k in self.knobs}

    def resolve(self, given: Mapping[str, object]) -> dict:
        """Defaults, overridden by what was given, clamped to what is drawable.

        Unknown numeric names are refused: a misspelt knob silently doing nothing is
        the animated equivalent of a misspelt token printing a blank.
        """
        values: dict = self.defaults()
        for name, value in given.items():
            knob = self.knob(name)
            if knob is not None:
                values[name] = knob.clamp(value)
            elif isinstance(value, (int, float)) and not isinstance(value, bool):
                raise KeyError(f"{self.key!r} has no knob {name!r}; knobs: "
                               f"{', '.join(k.key for k in self.knobs)}")
            else:
                values[name] = value  # text, colours and other extras pass through
        return values


REGISTRY: dict[str, VisualObject] = {}


def register(obj: VisualObject) -> VisualObject:
    if obj.key in REGISTRY:
        raise ValueError(f"visual object {obj.key!r} registered twice")
    REGISTRY[obj.key] = obj
    return obj


def registry() -> dict[str, VisualObject]:
    """Every visual object, including those defined in their own modules."""
    from . import visuals_forest  # noqa: F401  (registers on import)
    return REGISTRY


def visual(key: str) -> VisualObject:
    objects = registry()
    if key not in objects:
        raise KeyError(f"unknown visual object {key!r}; known: {', '.join(objects)}")
    return objects[key]


def draw(stage: Stage, key: str, **knobs) -> Anchors:
    """Draw one object on a stage and return its named anchor points."""
    obj = visual(key)
    anchors = obj.draw(stage, obj.resolve(knobs))
    return {name: stage.at(point) for name, point in (anchors or {}).items()}


# ----------------------------------------------------------------------
# Wrappers around what the repository already draws
# ----------------------------------------------------------------------

def _wedge_member(stage: Stage, k: Mapping) -> Anchors:
    from .lesson_wedge import _wedge_prism
    length, depth, lift = k["length"], k["depth"], k["lift"]
    roll = math.radians(k["roll_deg"])
    scratch = TriangleBatch()
    start = np.array([-length * 0.5, 0.0, lift])
    end = np.array([length * 0.5, 0.0, lift])
    out = np.array([0.0, -math.sin(roll), math.cos(roll)])
    _wedge_prism(scratch, start, end, out, depth, segments=6)
    stage.splice(scratch)
    return {"pith_start": start, "pith_end": end,
            "bark": (start + end) * 0.5 + out * depth}


def _timber_stick(stage: Stage, k: Mapping) -> Anchors:
    from .timber import CHAINSAW, MILLED, ROUGH, WEATHERED, draw_timber
    styles = (ROUGH, MILLED, CHAINSAW, WEATHERED)
    style = styles[int(round(k["style"])) % len(styles)]
    scratch = TriangleBatch()
    a = np.array([-k["length"] * 0.5, 0.0, k["lift"]])
    b = np.array([k["length"] * 0.5, 0.0, k["lift"]])
    draw_timber(scratch, a, b, k["radius"], int(k["seed"]), style, sides=8)
    stage.splice(scratch)
    return {"start": a, "end": b}


BOARD_WOOD = (0.80, 0.64, 0.42, 1.0)


def _board(stage: Stage, k: Mapping) -> Anchors:
    """A dressed two-by-four: 1.5 by 3.5 inches, whatever the drawing scale."""
    foot = k["units_per_ft"]
    length = k["length_ft"] * foot
    thick, wide = 1.5 / 12.0 * foot, 3.5 / 12.0 * foot
    size = (length, thick, wide) if k["on_edge"] >= 0.5 else (length, wide, thick)
    centre = np.array([0.0, 0.0, size[2] * 0.5 + k["lift"]])
    scratch = TriangleBatch()
    scratch.box(centre, size, BOARD_WOOD)
    stage.splice(scratch)
    return {"centre": centre, "end": centre + np.array([length * 0.5, 0.0, 0.0])}


def _section_disc(stage: Stage, k: Mapping) -> Anchors:
    """A bucked section end-on, whole or split, the way the wedge films draw it."""
    from .lesson_wedge import BARK, WOOD, _disc_xz
    radius = k["radius"]
    pieces = max(1, int(round(k["pieces"])))
    spread = k["spread"] * radius * 0.25
    centre = np.array([0.0, 0.0, radius + k["lift"]])
    scratch = TriangleBatch()
    for index in range(pieces):
        start = 360.0 * index / pieces
        end = 360.0 * (index + 1) / pieces
        middle = math.radians((start + end) * 0.5)
        push = np.array([math.cos(middle), 0.0, math.sin(middle)]) * spread
        gap = 0.6 if pieces > 1 else 0.0
        _disc_xz(scratch, centre + push, radius, WOOD, 64, start + gap, end - gap)
        for step in range(8):
            t0 = math.radians(start + gap + (end - start - 2 * gap) * step / 8.0)
            t1 = math.radians(start + gap + (end - start - 2 * gap) * (step + 1) / 8.0)
            a = centre + push + np.array([radius * math.cos(t0), 0.0,
                                          radius * math.sin(t0)])
            b = centre + push + np.array([radius * math.cos(t1), 0.0,
                                          radius * math.sin(t1)])
            scratch.cylinder(a, b, radius * 0.035, BARK, 5)
    stage.splice(scratch)
    return {"centre": centre, "top": centre + np.array([0.0, 0.0, radius])}


def _wedge_shell(stage: Stage, k: Mapping) -> Anchors:
    from .lesson_wedge import SCENE_RADIUS, _shell
    scratch = TriangleBatch()
    _shell(scratch, k["reveal"], scale=k["radius"] / SCENE_RADIUS)
    stage.splice(scratch)
    return {"apex": np.array([0.0, 0.0, k["radius"]]), "centre": np.zeros(3)}


def _solved_dome(stage: Stage, k: Mapping) -> Anchors:
    from . import raw_wedge_bridge as bridge
    orientations = bridge.orientations()
    orientation = orientations[int(round(k["orientation"])) % len(orientations)]
    parts = ("wood", "rigid") if k["keys"] >= 0.5 else ("wood",)
    alpha = k["alpha"]
    scratch = TriangleBatch()
    bridge.world_batches(scratch, orientation, scene_radius=k["radius"], parts=parts,
                         alpha=None if alpha >= 0.999 else alpha)
    stage.splice(scratch, transparent=alpha < 0.999)
    return {"apex": np.array([0.0, 0.0, k["radius"]]), "centre": np.zeros(3)}


def _hub_dome(stage: Stage, k: Mapping) -> Anchors:
    """The ordinary 2V dome: sixty-five struts on hubs, as rough or milled timber."""
    from .geometry import build_demo_geometry
    from .timber import CHAINSAW, MILLED, draw_timber
    geometry = build_demo_geometry()
    edges = list(geometry.hemisphere_edges)
    shown = int(round(len(edges) * clamp(k["reveal"])))
    style = CHAINSAW if k["rough"] >= 0.5 else MILLED
    scratch = TriangleBatch()
    for index, edge in enumerate(edges[:shown]):
        a, b = (geometry.vertices[i] * k["radius"] for i in edge)
        draw_timber(scratch, a, b, k["radius"] * 0.018, index, style, sides=6)
    stage.splice(scratch)
    return {"apex": np.array([0.0, 0.0, k["radius"]]), "centre": np.zeros(3)}


POSE_ORDER = ("stand", "stride", "carry", "squat_mid", "squat_deep", "stoop",
              "reach_high", "reach_out", "kneel", "fasten", "fasten_high",
              "team_carry")


def _person(stage: Stage, k: Mapping) -> Anchors:
    from .figure import POSES, draw_figure, joint_positions, walk_pose
    pose = walk_pose(k["walk"]) if k["walk"] > 0.0 else \
        POSES[POSE_ORDER[int(round(k["pose"])) % len(POSE_ORDER)]]
    joints = joint_positions(pose, stature=k["height"], yaw_deg=k["heading_deg"])
    scratch = TriangleBatch()
    draw_figure(scratch, joints, scale=k["height"] / 1.75)
    stage.splice(scratch)
    return {"head": joints["head_top"], "pelvis": joints["pelvis"]}


def _force_arrow(stage: Stage, k: Mapping) -> Anchors:
    """Compression points in; tension points out. Same member, opposite arrows."""
    half = k["length"] * 0.5
    lift = k["lift"]
    tension = k["kind"] >= 0.5
    colour = CYAN if tension else RED
    scratch = TriangleBatch()
    scratch.cylinder(np.array([-half * 0.55, 0.0, lift]),
                     np.array([half * 0.55, 0.0, lift]), k["thickness"] * 1.4,
                     (0.62, 0.50, 0.36, 1.0), 10)
    for sign in (-1.0, 1.0):
        outer = np.array([sign * half, 0.0, lift])
        inner = np.array([sign * half * 0.6, 0.0, lift])
        a, b = (inner, outer) if tension else (outer, inner)
        scratch.arrow(a, b, k["thickness"], colour)
    stage.splice(scratch)
    return {"centre": np.array([0.0, 0.0, lift])}


def _dimension(stage: Stage, k: Mapping) -> Anchors:
    """A dimension line with end ticks, and its text pinned above the middle."""
    half = k["length"] * 0.5
    lift = k["lift"]
    tick = max(0.08, k["length"] * 0.04)
    scratch = TriangleBatch()
    a, b = np.array([-half, 0.0, lift]), np.array([half, 0.0, lift])
    scratch.cylinder(a, b, tick * 0.12, AMBER, 6)
    for end in (a, b):
        scratch.cylinder(end - np.array([0.0, 0.0, tick]),
                         end + np.array([0.0, 0.0, tick]), tick * 0.12, AMBER, 6)
    text = str(k.get("text") or "")
    if text:
        stage.label(np.array([0.0, 0.0, lift + tick * 3.0]), text, AMBER)
    stage.splice(scratch)
    return {"middle": np.array([0.0, 0.0, lift]), "start": a, "end": b}


def _icon(stage: Stage, k: Mapping) -> Anchors:
    """An overlay pictogram pinned in the world, like a label with no words."""
    key = str(k.get("icon") or "chainsaw")
    point = np.array([0.0, 0.0, k["lift"]])
    stage.icon(point, key, k["size"], k.get("colour"), k["alpha"], k["angle"])
    # Nothing is drawn in 3-D; a degenerate triangle keeps probes honest about that.
    return {"point": point}


def _k(key, label, default, low, high, unit="", help="", animate=False) -> Knob:
    return Knob(key, label, float(default), float(low), float(high), unit, help,
                animate)


_LIFT = _k("lift", "Height above the ground", 0.6, 0.0, 20.0, "units",
           "How far above the floor the object is drawn.")

for _obj in (
    VisualObject(
        "wedge_member", "Raw wedge member", "wood",
        "One eighth of a log used as a stick: pith edge in, bark face out, two flat "
        "sawn faces. The same prism the wedge films draw.",
        (_k("length", "Length", 3.0, 0.2, 20.0, "units"),
         _k("depth", "Pith-to-bark depth", 0.5, 0.05, 3.0, "units"),
         _LIFT,
         _k("roll_deg", "Turn about its length", 0.0, -180.0, 180.0, "deg",
            "0 puts the bark face up; 180 puts the pith edge up.")),
        _wedge_member, "two_v_demo.lesson_wedge._wedge_prism", 2.0,
        ("wedge", "sector", "member", "strut", "stick")),
    VisualObject(
        "timber_stick", "Rough timber", "wood",
        "A stick that looks like wood: bowed, tapered, knotted, sometimes barked.",
        (_k("length", "Length", 3.0, 0.2, 20.0, "units"),
         _k("radius", "Thickness", 0.08, 0.01, 1.0, "units"),
         _LIFT,
         _k("seed", "Which stick", 7, 0, 9999, "",
            "Every seed is a different stick, identical in every frame."),
         _k("style", "Finish", 2, 0, 3, "",
            "0 rough, 1 milled, 2 chainsawn, 3 weathered.")),
        _timber_stick, "two_v_demo.timber.draw_timber", 2.0,
        ("timber", "lumber", "stick", "beam")),
    VisualObject(
        "board_2x4", "Dressed two-by-four", "wood",
        "The store-bought board the wedge replaces, at its real 1.5 by 3.5 inch "
        "section.",
        (_k("length_ft", "Length", 8.0, 1.0, 20.0, "ft"),
         _k("units_per_ft", "Drawing scale", 0.25, 0.01, 2.0, "units/ft"),
         _k("on_edge", "Stood on edge", 0.0, 0.0, 1.0),
         _k("lift", "Height above the ground", 0.0, 0.0, 20.0, "units")),
        _board, "new", 1.5, ("board", "stud", "two-by-four", "2x4", "lumber")),
    VisualObject(
        "section_disc", "Bucked section, end-on", "wood",
        "A slice of trunk seen from the end, whole or split into halves, quarters "
        "or eighths, with the pieces pushed apart.",
        (_k("radius", "Radius", 1.5, 0.1, 6.0, "units"),
         _k("pieces", "Pieces", 1, 1, 8, "", "1, 2, 4 or 8.", animate=True),
         _k("spread", "Pushed apart", 0.0, 0.0, 1.0, "", animate=True),
         _k("lift", "Height above the ground", 0.3, 0.0, 20.0, "units")),
        _section_disc, "two_v_demo.lesson_wedge._disc_xz", 2.0,
        ("section", "slice", "round", "log")),
    VisualObject(
        "wedge_shell", "Pinwheel wedge dome", "structure",
        "Forty independent pinwheel panels of raw wedges -- the dome the wedge "
        "films build.",
        (_k("radius", "Radius", 5.0, 0.5, 20.0, "units"),
         _k("reveal", "How much is built", 1.0, 0.0, 1.0, "", animate=True)),
        _wedge_shell, "two_v_demo.lesson_wedge._shell", 5.5,
        ("dome", "shell", "frame", "panel", "pinwheel")),
    VisualObject(
        "solved_dome", "The simulator's solved dome", "structure",
        "The raw-wedge simulator's own finished meshes: 120 members with their "
        "compound butt cuts and, optionally, the seam keys.",
        (_k("radius", "Radius", 5.0, 0.5, 20.0, "units"),
         _k("orientation", "Wedge orientation", 0, 0, 3, "",
            "Which of the four ways the wedge is turned."),
         _k("keys", "Show seam keys", 1.0, 0.0, 1.0),
         _k("alpha", "Solidity", 1.0, 0.05, 1.0)),
        _solved_dome, "two_v_demo.raw_wedge_bridge.world_batches", 5.5,
        ("dome", "shell", "seam", "key", "spline")),
    VisualObject(
        "hub_dome", "2V hub dome", "structure",
        "The ordinary 2V hemisphere: sixty-five struts meeting at hubs.",
        (_k("radius", "Radius", 5.0, 0.5, 20.0, "units"),
         _k("reveal", "How much is built", 1.0, 0.0, 1.0, "", animate=True),
         _k("rough", "Rough-sawn", 0.0, 0.0, 1.0)),
        _hub_dome, "two_v_demo.geometry.build_demo_geometry", 5.5,
        ("dome", "hub", "strut", "2v")),
    VisualObject(
        "person", "Person", "people",
        "The articulated worker, posed or walking, at any height.",
        (_k("height", "Height", 1.75, 0.2, 6.0, "units"),
         _k("pose", "Pose", 0, 0, len(POSE_ORDER) - 1, "",
            ", ".join(f"{i} {name}" for i, name in enumerate(POSE_ORDER))),
         _k("walk", "Walking phase", 0.0, 0.0, 1.0, "",
            "Above 0 the figure walks; one full stride per unit.", animate=True),
         _k("heading_deg", "Facing", 0.0, -180.0, 180.0, "deg")),
        _person, "two_v_demo.figure.draw_figure", 1.2,
        ("person", "builder", "worker", "crew")),
    VisualObject(
        "force_arrow", "Compression or tension", "forces",
        "One member with its load drawn as arrows: pointing in for compression, "
        "out for tension.",
        (_k("length", "Length", 3.0, 0.5, 20.0, "units"),
         _k("kind", "Kind", 0.0, 0.0, 1.0, "", "0 compression, 1 tension."),
         _k("thickness", "Arrow weight", 0.06, 0.01, 0.5, "units"),
         _LIFT),
        _force_arrow, "two_v_demo.render_kit.TriangleBatch.arrow", 2.0,
        ("compression", "tension", "force", "load")),
    VisualObject(
        "dimension", "Dimension line", "measure",
        "A measured length with end ticks and its figure above it. Pass the text "
        "as ``text``; it should come from a token, never be typed.",
        (_k("length", "Length", 3.0, 0.1, 40.0, "units"), _LIFT),
        _dimension, "new", 2.0, ("length", "width", "height", "diameter")),
    VisualObject(
        "icon", "Pinned pictogram", "media",
        "A flat icon from two_v_demo.icons, pinned to a point in the world. Pass "
        "the icon key as ``icon``.",
        (_k("size", "Size", 64.0, 8.0, 400.0, "px at 1080p"),
         _k("alpha", "Opacity", 1.0, 0.0, 1.0, "", animate=True),
         _k("angle", "Tilt", 0.0, -180.0, 180.0, "deg"), _LIFT),
        _icon, "two_v_demo.icons.draw_icon", 0.5, ("icon",)),
):
    register(_obj)


# ----------------------------------------------------------------------
# The presenter engine's side of the bridge
# ----------------------------------------------------------------------

PRESENTER_PREFIX = "vo:"
PLACEMENT = (
    _k("x", "Across", 0.0, -40.0, 40.0, "m"),
    _k("y", "Along", 0.0, -40.0, 40.0, "m"),
    _k("z", "Up", 0.0, -5.0, 40.0, "m"),
    _k("yaw_deg", "Heading", 0.0, -180.0, 180.0, "deg"),
    _k("scale", "Size", 1.0, 0.05, 20.0, "x"),
)


def presenter_emitter(key: str) -> Callable:
    """Adapt a visual object to the presenter engine's ``emit`` contract."""
    obj = visual(key)

    def emit(o, tr, p: dict, t: float, targets: dict) -> None:
        opaque, transparent = TriangleBatch(), TriangleBatch()
        stage = Stage(opaque, transparent,
                      origin=(float(p.get("x", 0.0)), float(p.get("y", 0.0)),
                              float(p.get("z", 0.0))),
                      scale=float(p.get("scale", 1.0)),
                      yaw_deg=float(p.get("yaw_deg", 0.0)))
        knobs = {name: value for name, value in p.items()
                 if obj.knob(name) is not None}
        anchors = obj.draw(stage, obj.resolve(knobs)) or {}
        o.v.extend(opaque.vertices)
        tr.v.extend(transparent.vertices)
        reach = obj.reach * stage.scale
        # Prefixed like the forge layers' targets, so "person" here cannot shadow
        # a presenter object of the same name.
        targets[f"vo_{key}"] = (stage.at((0.0, 0.0, obj.reach * 0.4)), max(0.5, reach))
        for name, point in anchors.items():
            targets[f"vo_{key}_{name}"] = (stage.at(point), max(0.5, reach * 0.5))

    return emit


def presenter_emitters() -> dict[str, Callable]:
    return {PRESENTER_PREFIX + key: presenter_emitter(key) for key in registry()}


def presenter_object_specs() -> tuple:
    """The same objects described in the presenter library's own terms."""
    from dome_forge.layers import ParamSpec
    from presenter.library import ObjectSpec

    specs = []
    for obj in registry().values():
        params = tuple(
            ParamSpec(k.key, k.label, "float", k.default, k.low, k.high,
                      max(0.001, (k.high - k.low) / 200.0), unit=k.unit, help=k.help)
            for k in PLACEMENT + obj.knobs)
        specs.append(ObjectSpec(PRESENTER_PREFIX + obj.key, obj.label,
                                "Visual lexicon", obj.blurb, params))
    return tuple(specs)


# ----------------------------------------------------------------------
# Proof
# ----------------------------------------------------------------------

def validate_visual_objects() -> None:
    """Every object draws, at its defaults and at the ends of every knob."""
    from .lexicon_taxonomy import categories

    category_keys = {c.key for c in categories()}
    for obj in registry().values():
        assert obj.category in category_keys, (obj.key, obj.category)
        assert obj.blurb.strip() and obj.label.strip(), obj.key
        for knob in obj.knobs:
            assert knob.low <= knob.default <= knob.high, (obj.key, knob.key)
        trials = [(obj.defaults(), False)]
        for knob in obj.knobs:
            for value in (knob.low, knob.high):
                # An animated knob at its start may honestly show nothing: a dome
                # with none of it built yet, an icon that has not faded in.
                may_be_empty = knob.animate and value == knob.low
                trials.append(({**obj.defaults(), knob.key: value}, may_be_empty))
        for values, may_be_empty in trials:
            stage = Stage(TriangleBatch(), TriangleBatch())
            anchors = obj.draw(stage, obj.resolve(values)) or {}
            drew = stage.opaque.vertices or stage.transparent.vertices or stage.icons
            assert drew or may_be_empty, (obj.key, values)
            for name, point in anchors.items():
                assert np.all(np.isfinite(np.asarray(point, float))), (obj.key, name)
        try:
            obj.resolve({"no_such_knob": 1.0})
        except KeyError:
            pass
        else:  # pragma: no cover - the guard is the point
            raise AssertionError(f"{obj.key} accepted an unknown knob")
    # Placement must move and turn a drawing without deforming it.
    stage = Stage(TriangleBatch(), TriangleBatch(), origin=(3.0, -2.0, 1.0),
                  scale=2.0, yaw_deg=90.0)
    moved = stage.at((1.0, 0.0, 0.0))
    assert np.allclose(moved, (3.0, 0.0, 1.0)), moved
