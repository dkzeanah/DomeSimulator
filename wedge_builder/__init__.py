"""The Wedge Builder: one buyer's wedge dome, solved and written out as a cut list.

``design.solve(Request(...))`` runs the live raw-wedge solver
(``geodesic_raw_wedge_dome_dihedral.py``, through ``two_v_demo.raw_wedge_bridge``) at the
buyer's size and log, and ``pdf.build(design, path)`` writes every page a builder needs:
saw setups, cut families, the log plan, jigs, seams and the infill takeoff. Nothing in it
is typed by hand; the declared allowances are on their own page.

    py -3.12 -m wedge_builder --diameter-ft 19.4 --log-in 10 --log-ft 16
    py -3.12 -m wedge_builder.selftest

zeanahlab.com sells it: website/functions/_lib/cutlists.ts queues a buyer's request and
website/scripts/render_cutlists.py renders the queue with this package.
"""
