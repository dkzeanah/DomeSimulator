"""One import of the raw-wedge dome simulator, for anything that needs its numbers.

``geodesic_raw_wedge_dome_dihedral.py`` is a deliberately self-contained single file
sitting at the project root: it is the thing you hand somebody who wants the dome and
nothing else.  That means it is not a package and cannot simply be imported by name.

This module loads it once, by path, and hands back the live objects.  Everything the
wedge film says about orientations, seam angles, member lengths, the head-end offcut and
the jig comes through here, so the film and the simulator cannot drift apart: change the
geometry in that file and the next render says the new number.
"""

from __future__ import annotations

import importlib.util
import sys
from functools import lru_cache
from pathlib import Path
from types import ModuleType


ROOT = Path(__file__).resolve().parent.parent
SIMULATOR = ROOT / "geodesic_raw_wedge_dome_dihedral.py"
MODULE_NAME = "geodesic_raw_wedge_dome_dihedral"


@lru_cache(maxsize=1)
def simulator() -> ModuleType:
    """Import the single-file simulator, once per process."""
    if MODULE_NAME in sys.modules:
        return sys.modules[MODULE_NAME]
    # When the simulator is the program that is running, it is already in
    # memory as ``__main__``. Importing the file again would build a second
    # copy of it -- a second solve, a second set of dataclasses, and two
    # modules whose objects fail every isinstance check against each other.
    running = sys.modules.get("__main__")
    main_file = getattr(running, "__file__", None)
    if running is not None and main_file:
        try:
            same = Path(main_file).resolve() == SIMULATOR
        except OSError:
            same = False
        if same:
            sys.modules[MODULE_NAME] = running
            return running
    if not SIMULATOR.is_file():
        raise FileNotFoundError(
            f"the raw-wedge simulator is missing: {SIMULATOR}. The wedge-method "
            "film derives every figure from it and will not invent them.")
    spec = importlib.util.spec_from_file_location(MODULE_NAME, SIMULATOR)
    if spec is None or spec.loader is None:
        raise ImportError(f"could not load {SIMULATOR}")
    module = importlib.util.module_from_spec(spec)
    # Registered before execution because the file defines dataclasses, and the
    # dataclass machinery looks its own module up by name while the class body runs.
    sys.modules[MODULE_NAME] = module
    spec.loader.exec_module(module)
    return module


@lru_cache(maxsize=16)
def model(orientation: str = "point_dome_in",
          seam_join_mode: str = "raw_trapezoid",
          long_edge_in: float | None = None,
          trunk_diameter_in: float | None = None):
    """The solved physical dome in one wedge orientation.

    Cached because building it solves 120 members and 55 seams, and the film asks for
    the same handful of configurations over and over while it lays out its screens.

    ``long_edge_in`` and ``trunk_diameter_in`` are left at the simulator's own defaults
    unless a caller has a reason to move them -- the seed-dome costing does, because a
    product line is defined by the stick it is cut from.
    """
    sim = simulator()
    fields: dict[str, object] = {"wedge_orientation": orientation,
                                 "seam_join_mode": seam_join_mode}
    if long_edge_in is not None:
        fields["long_edge_in"] = float(long_edge_in)
    if trunk_diameter_in is not None:
        fields["trunk_diameter_in"] = float(trunk_diameter_in)
    config = sim.DomeConfig(**fields)
    return sim.build_physical_model(config)


def orientations() -> tuple[str, ...]:
    return tuple(simulator().WEDGE_ORIENTATION_ORDER)


def jig_stages() -> tuple[tuple[str, str, str, str], ...]:
    return tuple(simulator().JIG_STAGES)


def seam_pair_reading(orientation: str) -> str:
    """Plain-language description of what a PAIR of points at one seam does."""
    return simulator().SEAM_PAIR_READING[orientation]


@lru_cache(maxsize=8)
def _world_vertex_floats(orientation: str, parts: tuple[str, ...],
                         scene_radius: float, origin: tuple[float, float, float],
                         alpha: float | None) -> tuple[float, ...]:
    """The simulator's solved dome, flattened once into lesson vertex floats.

    Converting eleven thousand triangles is far too slow to do inside a painter that
    runs thirty times a second, so the conversion happens once per configuration and the
    result is spliced straight into the batch afterwards.
    """
    import numpy as np

    sim = simulator()
    model_ = model(orientation)
    meshes = sim.build_world_meshes(model_)
    scale = scene_radius / model_.topology.sphere_radius_in
    shift = np.asarray(origin, dtype=np.float64)

    out: list[float] = []
    for name in parts:
        data = meshes.get(name)
        if data is None or not hasattr(data, "indices") or len(data.indices) == 0:
            continue
        vertices = np.asarray(data.vertices, dtype=np.float64)
        indices = np.asarray(data.indices, dtype=np.int64)
        positions = vertices[:, 0:3] * scale + shift
        normals = vertices[:, 3:6]
        colours = vertices[:, 6:10].copy()
        if alpha is not None:
            colours[:, 3] = alpha
        for index in indices:
            i = int(index)
            out.extend(positions[i])
            out.extend(normals[i])
            out.extend(colours[i])
    return tuple(out)


def world_batches(
    batch,
    orientation: str = "point_dome_in",
    *,
    scene_radius: float = 5.0,
    parts: tuple[str, ...] = ("wood",),
    origin=None,
    alpha: float | None = None,
) -> int:
    """Draw the simulator's OWN solved dome into a lesson triangle batch.

    The films kept re-drawing the wedge dome as a sketch while the real solved article
    sat one import away, which is how two things that are supposed to be the same
    building end up disagreeing about what a seam looks like.  This puts the simulator's
    finished meshes on screen -- the actual 120 members with their compound butt cuts,
    their seam keys and their clean vertex trims -- in the lesson renderer's own format.

    ``parts`` names batches from :func:`build_world_meshes`: ``wood`` is the frame,
    ``rigid`` the seam keys, ``head_overfit`` the stock that is flush-cut away, ``nodes``
    the vertex markers.

    Returns the triangle count, so a caller can assert it drew something rather than
    silently rendering an empty frame.
    """
    key_origin = (0.0, 0.0, 0.0) if origin is None else (
        float(origin[0]), float(origin[1]), float(origin[2]))
    floats = _world_vertex_floats(orientation, tuple(parts), float(scene_radius),
                                  key_origin, alpha)
    batch.vertices.extend(floats)
    return len(floats) // 30
