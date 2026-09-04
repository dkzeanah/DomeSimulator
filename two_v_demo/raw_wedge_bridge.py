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


@lru_cache(maxsize=8)
def model(orientation: str = "point_dome_in",
          seam_join_mode: str = "raw_trapezoid"):
    """The solved physical dome in one wedge orientation.

    Cached because building it solves 120 members and 55 seams, and the film asks for
    the same handful of configurations over and over while it lays out its screens.
    """
    sim = simulator()
    config = sim.DomeConfig(wedge_orientation=orientation,
                            seam_join_mode=seam_join_mode)
    return sim.build_physical_model(config)


def orientations() -> tuple[str, ...]:
    return tuple(simulator().WEDGE_ORIENTATION_ORDER)


def jig_stages() -> tuple[tuple[str, str, str, str], ...]:
    return tuple(simulator().JIG_STAGES)


def seam_pair_reading(orientation: str) -> str:
    """Plain-language description of what a PAIR of points at one seam does."""
    return simulator().SEAM_PAIR_READING[orientation]
