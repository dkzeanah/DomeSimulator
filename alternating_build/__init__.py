"""The alternating build: wedges point in and out panel by panel, so their faces cancel.

Where an in-pointing wedge meets an out-pointing one across a seam, their sawn faces are
parallel before the fold, and the key fills only the fold (18.03 deg on A seams, 22.46 on
B). Both pointing in leaves sector minus fold; both out, sector plus fold. The live solver
(``geodesic_raw_wedge_dome_dihedral.py``, ``orientation_pattern``) cuts every member of
such a dome; this package reads it as a builder needs it, ground up.

    py -3.12 -m alternating_build                       # the plan for your ground ring
    py -3.12 -m alternating_build --pattern alternate_lower
    py -3.12 -m alternating_build --sheet               # the build sheet PDF, into deliverables/
    py -3.12 -m alternating_build.selftest

``py -3.12 -m world3d`` shows it beside the uniform dome: N grows it band by band, M changes the pattern.
"""
