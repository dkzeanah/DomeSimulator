"""One import of the Dome Creator, so a film can show its real product.

``dome_creator.py`` is the walkable customizer: frequency, radius, strut shape,
frame style, panels, cladding layers, foundation, partitions, rooms and a floor
full of equipment.  Its buildings are assembled by :func:`mesh_builder.build_dome_mesh`
and drawn by a fragment shader that knows what shingles, glass, mirrors, solar
cells, deck boards, gravel and concrete look like.

Until this module, none of that reached a film.  The lessons rebuilt a preset's
*geometry* with :class:`dome_model.DomeModel` and then re-drew it with the film
engine's own primitives -- plain cylinders for struts, flat translucent triangles
for panels.  That is a sketch of the building, and it is why the presets never
looked like the product the tool actually renders.

This is the same trick :mod:`two_v_demo.raw_wedge_bridge` plays for the raw-wedge
simulator: import the real thing, hand the film its finished meshes, and let the
tool's own shader draw them.  A painter calls :func:`draw`; the renderer picks the
requests up from ``app.creator_draws`` and runs them through the Creator's own
program.  Change a price, a profile or a prop in the tool and the next render says
the new thing, because the film is drawing the tool's output rather than an
impression of it.

What the draw request carries, beyond the building itself:

* ``limits`` -- how much of the mesh to draw.  :func:`mesh_builder.build_dome_mesh`
  emits the dome in real construction order and records an index count at every
  work step, which is how the Creator animates a crew building a dome.  Passing a
  prefix here puts that same half-built dome in a film.
* ``cut_z`` -- the Creator's roof fade.  Everything above this height is discarded
  by the shader, so an interior fit-out can be shown without moving the camera
  inside.
* ``lights`` -- lamp props are point lights in that shader.  A dome whose tripod
  lights are on lights its own floor.
"""

from __future__ import annotations

import json
import math
import sys
from dataclasses import dataclass, field
from functools import lru_cache
from pathlib import Path

import numpy as np


# The simulator's modules live at the repository root, one level above this
# package, and are imported by name once the root is on the path.
ROOT = Path(__file__).resolve().parent.parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))


VERTEX_FLOATS = 11
"""position(3) normal(3) rgba(4) mat_id(1) -- mesh_builder's own layout."""


@lru_cache(maxsize=1)
def simulator():
    """The Dome Creator's model, mesh and material modules."""
    import dome_model
    import materials
    import mesh_builder
    import presets
    import workshop
    return {
        "dome_model": dome_model,
        "materials": materials,
        "mesh_builder": mesh_builder,
        "presets": presets,
        "workshop": workshop,
    }


@lru_cache(maxsize=1)
def shaders() -> tuple[str, str]:
    """The Creator's own scene shaders, imported rather than copied.

    The material patterns are in the fragment shader, keyed by the ``mat_id``
    every vertex carries.  A film that re-implemented this would start drifting
    the day somebody adds a material to the tool, so it reads the real strings.
    """
    import dome_creator
    return (dome_creator.SCENE_VERTEX_SHADER, dome_creator.SCENE_FRAGMENT_SHADER)


# ----------------------------------------------------------------------
# One building
# ----------------------------------------------------------------------

@dataclass
class Build:
    """One Dome Creator design: its config, its model, its finished mesh.

    ``events`` is the construction record the mesh builder emits: a label, an
    hours estimate from the tool's own labour model, and the index counts that
    show the dome built that far.
    """

    key: str
    name: str
    config: dict
    model: object
    mesh: object
    events: tuple[dict, ...]
    stats: dict
    _sample: object = field(default=None, repr=False)

    # -- what it is ----------------------------------------------------
    @property
    def radius(self) -> float:
        return float(self.stats.get("radius", 0.0))

    @property
    def height(self) -> float:
        return float(self.stats.get("height", 0.0))

    @property
    def apex(self) -> float:
        """Top of the building above grade: the shell's height plus its pad.

        A treehouse platform lifts the whole dome four and a half metres, so a
        label hung at the shell's own height lands inside the roof.
        """
        model = self.model
        lift = 0.0 if model is None else float(model.foundation.height)
        return self.height + lift

    @property
    def foundation_radius(self) -> float:
        cfg = self.model.config
        return float(cfg.radius * cfg.foundation_scale)

    @property
    def hours(self) -> float:
        """The tool's own labour estimate for building this dome."""
        return float(sum(event["hours"] for event in self.events))

    @property
    def triangles(self) -> int:
        return (len(self.mesh.opaque) + len(self.mesh.transparent)) // 3

    # -- drawing a partly built dome -----------------------------------
    def phase(self, fraction: float) -> dict:
        """The construction checkpoint at ``fraction`` through the build.

        Returns the step's label, the hours spent up to it, and the index
        counts that draw the dome exactly that far along.
        """
        if not self.events:
            return {"label": "", "hours": 0.0, "limits": None, "index": 0,
                    "steps": 0}
        index = int(min(len(self.events) - 1,
                        max(0.0, fraction) * len(self.events)))
        event = self.events[index]
        hours = sum(e["hours"] for e in self.events[:index + 1])
        return {
            "label": str(event["label"]),
            "hours": float(hours),
            "limits": (int(event["opaque"]), int(event["transparent"])),
            "index": index,
            "steps": len(self.events),
            "position": tuple(float(v) for v in event["pos"]),
        }

    def sample(self, count: int = 260) -> np.ndarray:
        """A thin scatter of this building's points, for framing decisions.

        A phone frame is fitted to what the scene painted (see :mod:`two_v_demo.frame`),
        and this geometry never passes through the film's own batches, so the
        fit is given these points instead.  A few hundred are plenty to bound a
        dome; all forty thousand would only cost time, on every frame.
        """
        if self._sample is None:
            vertices = self.mesh.vertices
            if not len(vertices):
                self._sample = np.zeros((0, 3), dtype=np.float32)
            else:
                stride = max(1, len(vertices) // max(1, count))
                self._sample = np.ascontiguousarray(vertices[::stride, 0:3],
                                                    dtype=np.float32)
        return self._sample


def config_key(config: dict) -> str:
    return json.dumps(config, sort_keys=True, default=str)


@lru_cache(maxsize=256)
def _build(key: str, name: str) -> Build:
    sim = simulator()
    config = json.loads(key)
    cfg = sim["dome_model"].DomeConfig.from_dict(config)
    model = sim["dome_model"].DomeModel(cfg)
    events: list[dict] = []
    mesh = sim["mesh_builder"].build_dome_mesh(model, events=events)
    return Build(key=key, name=name, config=config, model=model, mesh=mesh,
                 events=tuple(events), stats=model.stats())


def build(config: dict, name: str = "") -> Build:
    """Build one design exactly as the Creator would, cached by its config.

    Every dome in a film is a pure function of its configuration, and a film
    asks for the same one on every frame, so the mesh is built once.  A preset
    costs roughly half a second and a megabyte, which is why a film can afford
    to show dozens of them.
    """
    return _build(config_key(config), name)


def presets_all() -> tuple[tuple[str, dict], ...]:
    """Every design the Creator ships, in the order its Preset button cycles."""
    return tuple((name, data) for name, data in simulator()["presets"].PRESETS)


def preset_names() -> tuple[str, ...]:
    return tuple(name for name, _ in presets_all())


@lru_cache(maxsize=64)
def preset(name: str) -> Build:
    """One shipped preset, built."""
    for preset_name, data in presets_all():
        if preset_name == name:
            return build(data, preset_name)
    raise KeyError(f"no Dome Creator preset named {name!r}")


def variant(base: dict, name: str = "", **changes) -> Build:
    """One design with some options changed -- the sweeps a showcase needs.

    Written as a helper rather than inline so that a sweep states only what it
    varies, and so the unchanged half of the configuration is provably the same
    between two domes the film puts side by side.
    """
    config = json.loads(json.dumps(base, default=str))
    config.update(changes)
    return build(config, name)


# Builds that are scenery wherever they appear. A painter can still say so
# explicitly with ``draw(..., backdrop=True)``; this is the default for the
# one build that is never the subject of anything.
BACKDROP_KEYS = frozenset({"environment"})


@lru_cache(maxsize=1)
def environment() -> Build:
    """The Creator's own site: the graded field, its grid, and the tree line.

    Used by the chapters that put a dome back in the world it is designed in,
    and by the mirror panels, which reflect a stylised version of exactly this.
    """
    sim = simulator()
    mesh = sim["mesh_builder"].build_environment()
    return Build(key="environment", name="Build field", config={}, model=None,
                 mesh=mesh, events=(), stats={})


# ----------------------------------------------------------------------
# Draw requests
# ----------------------------------------------------------------------

@dataclass
class Draw:
    """One Dome Creator mesh, placed, and how much of it to show."""

    build: Build
    offset: tuple[float, float, float] = (0.0, 0.0, 0.0)
    scale: float = 1.0
    yaw: float = 0.0
    limits: tuple[int, int] | None = None
    cut_z: float | None = None
    exposure: float = 1.0
    lights: tuple[tuple[float, float, float], ...] = ()
    # Scenery: drawn, but never part of what the camera is asked to frame.
    # ``None`` means decide from the build, which is the right answer for
    # every painter that has not thought about it.
    backdrop: bool | None = None

    @property
    def is_backdrop(self) -> bool:
        if self.backdrop is not None:
            return self.backdrop
        return self.build.key in BACKDROP_KEYS

    def matrix(self) -> np.ndarray:
        angle = math.radians(self.yaw)
        cos, sin = math.cos(angle), math.sin(angle)
        scale = float(self.scale)
        return np.array([
            [cos * scale, -sin * scale, 0.0, float(self.offset[0])],
            [sin * scale, cos * scale, 0.0, float(self.offset[1])],
            [0.0, 0.0, scale, float(self.offset[2])],
            [0.0, 0.0, 0.0, 1.0],
        ], dtype=np.float32)

    def points(self) -> np.ndarray:
        """Where this building sits in the world, thinned, for the frame fit."""
        local = self.build.sample()
        if not len(local):
            return local
        matrix = self.matrix()
        return (local @ matrix[:3, :3].T + matrix[:3, 3]).astype(np.float32)

    def world_lights(self) -> tuple[tuple[float, float, float], ...]:
        if self.lights:
            return self.lights
        model = self.build.model
        if model is None:
            return ()
        matrix = self.matrix()
        placed = []
        for position in model.light_positions():
            point = matrix[:3, :3] @ np.asarray(position, dtype=np.float32)
            placed.append(tuple(float(v) for v in point + matrix[:3, 3]))
        return tuple(placed[:16])


def draw(app, item: Build, **kwargs) -> Draw:
    """Ask the renderer to draw this building, in the Creator's own shader.

    Painters call this instead of filling a triangle batch.  A lesson that never
    calls it renders exactly as it always did: the renderer only touches the
    Creator's program when a painter has put something in the list.
    """
    request = Draw(item, **kwargs)
    requests = getattr(app, "creator_draws", None)
    if requests is None:
        requests = []
        app.creator_draws = requests
    requests.append(request)
    return request


def draw_points(app) -> list[np.ndarray]:
    """The points a frame of another shape should fit the camera to.

    Scenery is left out, and that matters more than it sounds. The Creator's
    build field is a sixty-metre graded site with a tree line around it; a
    phone cut that fits *that* puts a nineteen-foot dome in the middle of a
    lot of grass, which is what the vertical cuts used to look like. The
    backdrop is still drawn -- a dome on a bare disc looks like it is
    floating -- it just does not get a vote on the framing.
    """
    return [request.points() for request in getattr(app, "creator_draws", ())
            if not request.is_backdrop and len(request.points())]


# ----------------------------------------------------------------------
# Proof
# ----------------------------------------------------------------------

class _Stage:
    """Just enough of an app for a draw list."""

    creator_draws: list = []


def _validate_backdrop() -> None:
    """Scenery is drawn but never framed."""
    stage = _Stage()
    stage.creator_draws = []
    field = Draw(environment())
    assert field.is_backdrop, "the build field is scenery"
    assert not Draw(preset(preset_names()[0])).is_backdrop

    draw(stage, environment())
    assert draw_points(stage) == [], "the tree line is deciding the framing"

    # A dome on the same stage is what the camera should see, and the points
    # it hands over have to be the dome's, not the dome's plus the field's.
    dome = preset(preset_names()[0])
    draw(stage, dome)
    points = draw_points(stage)
    assert len(points) == 1, len(points)
    reach = float(np.abs(points[0][:, 0:2]).max())
    field_reach = float(np.abs(Draw(environment()).points()[:, 0:2]).max())
    assert reach < field_reach * 0.5, (reach, field_reach)

    # And a painter can overrule it either way.
    assert Draw(dome, backdrop=True).is_backdrop
    assert not Draw(environment(), backdrop=False).is_backdrop


def validate_creator_bridge() -> None:
    """The bridge must hand back the tool's real building, not an empty one."""
    _validate_backdrop()
    names = preset_names()
    assert len(names) >= 12, names

    first = preset(names[0])
    assert first.triangles > 5000, first.triangles
    assert len(first.mesh.vertices[0]) == VERTEX_FLOATS, first.mesh.vertices.shape
    assert first.events, "the construction record is empty"
    assert first.hours > 0.0, first.hours
    # The mesh has to agree with the model it was built from, or the film is
    # showing one dome and captioning another.
    assert first.stats["strut_count"] == len(first.model.struts)

    # Caching is what makes this affordable inside a painter: the same config
    # must come back as the same object rather than being rebuilt per frame.
    assert preset(names[0]) is first
    assert build(dict(first.config), names[0]) is first

    # A changed option must produce a different building.
    changed = variant(first.config, "probe", frequency=4)
    assert changed is not first
    assert changed.stats["strut_count"] > first.stats["strut_count"]

    # The construction record must run from nothing to the whole mesh.
    start = first.phase(0.0)
    end = first.phase(1.0)
    assert start["limits"][0] <= end["limits"][0]
    assert end["limits"][0] == len(first.mesh.opaque), (
        end["limits"], len(first.mesh.opaque))
    assert end["hours"] > start["hours"]
    assert start["label"] and end["label"]

    # Placement has to move the points a frame fit will be given.
    class _App:
        pass

    probe = _App()
    request = draw(probe, first, offset=(12.0, 0.0, 0.0))
    points = request.points()
    assert len(points) > 20, len(points)
    assert abs(float(points[:, 0].mean()) - 12.0) < first.radius * 2.0
    assert len(draw_points(probe)) == 1

    vertex, fragment = shaders()
    assert "in_mat" in vertex and "u_cut_z" in fragment
