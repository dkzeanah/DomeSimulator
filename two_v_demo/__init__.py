"""Standalone 2V geodesic-dome masterclass.

This package deliberately has no imports from the assembly-line simulator or
the main dome-creator world.  ``two_v_masterclass.py`` is its public launcher.
"""

from .geometry import (
    DemoGeometry,
    DomeMeasurements,
    MeasurementFit,
    build_demo_geometry,
    fit_measurements,
)

__all__ = [
    "DemoGeometry",
    "DomeMeasurements",
    "MeasurementFit",
    "build_demo_geometry",
    "fit_measurements",
]
