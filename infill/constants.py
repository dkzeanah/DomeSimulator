"""Everything the infill calculator takes on trust, with a reason for each.

The frame -- edge lengths, member lengths, the two triangle types and how
many of each -- is solved from the max strut length by
:mod:`two_v_demo.wedge_geometry`. The shapes of the pieces are solved from
the log diameter and the number of splits. What cannot be solved is here:
saw kerfs, the sizes things are sold in, densities, and prices. Each row
says what kind of figure it is, and the viewer shows this table on its own
page before anything is priced.

Kinds: ``nominal`` (a size it is sold in), ``standard`` (a trade rule),
``estimate`` (a typical figure; yours will differ), ``assumption`` (a choice
made for you that you can change in the viewer).
"""

from __future__ import annotations

# name, value, unit, kind, why
CONSTANTS: tuple[tuple[str, float, str, str, str], ...] = (
    # -- saws -------------------------------------------------------------
    ("chainsaw_kerf_in", 0.25, "in", "estimate", "a ripping chain on a big saw; the 1/8 splits"),
    ("bandsaw_kerf_in", 0.0625, "in", "estimate", "a 1/16 in bandsaw blade; 1/16 and 1/32 slices"),
    ("gasket_in", 0.75, "in", "assumption", "the gasket between neighbouring panels, as the frame model uses"),
    # -- the log ----------------------------------------------------------
    ("green_pine_kg_m3", 800.0, "kg/m3", "estimate", "fresh-cut pine; dries toward 500"),
    # -- sheet goods --------------------------------------------------------
    ("sheet_w_in", 48.0, "in", "nominal", "a 4 x 8 sheet, short side"),
    ("sheet_l_in", 96.0, "in", "nominal", "a 4 x 8 sheet, long side"),
    ("osb_in", 0.4375, "in", "nominal", "7/16 in OSB sheathing"),
    ("osb_kg_m2", 6.3, "kg/m2", "estimate", "7/16 OSB"),
    ("osb_usd", 16.0, "$", "estimate", "one 4 x 8 sheet of 7/16 OSB"),
    ("ply_in", 0.71875, "in", "nominal", "23/32 in plywood: the 'milled panel' sheet"),
    ("ply_kg_m2", 9.5, "kg/m2", "estimate", "23/32 plywood"),
    ("ply_usd", 42.0, "$", "estimate", "one 4 x 8 sheet of 23/32 plywood"),
    # -- boards -------------------------------------------------------------
    ("fence_w_in", 5.5, "in", "nominal", "a dog-ear fence picket, face width"),
    ("fence_t_in", 0.625, "in", "nominal", "a fence picket, thickness"),
    ("fence_l_in", 72.0, "in", "nominal", "a 6 ft fence picket"),
    ("fence_usd", 3.0, "$", "estimate", "one 6 ft cedar-tone picket"),
    ("milled_w_in", 5.5, "in", "nominal", "a milled 1x6 board, face width"),
    ("milled_t_in", 0.75, "in", "nominal", "a milled 1x6 board, thickness"),
    ("milled_l_in", 96.0, "in", "nominal", "an 8 ft board"),
    ("milled_usd", 7.0, "$", "estimate", "one 8 ft 1x6"),
    ("board_kg_m3", 450.0, "kg/m3", "estimate", "dry milled softwood"),
    # -- sheet metal ----------------------------------------------------------
    ("metal_cover_in", 24.0, "in", "nominal", "corrugated panel coverage width after one rib of lap"),
    ("metal_w_in", 26.0, "in", "nominal", "corrugated panel full width"),
    ("metal_l_in", 96.0, "in", "nominal", "an 8 ft corrugated panel"),
    ("metal_kg_m2", 4.4, "kg/m2", "estimate", "26 gauge galvanised corrugated"),
    ("metal_usd", 24.0, "$", "estimate", "one 26 in x 8 ft corrugated panel"),
    # -- film -----------------------------------------------------------------
    ("film_roll_w_in", 120.0, "in", "nominal", "a 10 ft wide roll of greenhouse film"),
    ("film_kg_m2", 0.14, "kg/m2", "estimate", "6 mil polyethylene"),
    ("film_usd_ft2", 0.12, "$/ft2", "estimate", "6 mil greenhouse film off a roll"),
    ("film_wrap_in", 3.0, "in", "assumption", "film carried past the edge to staple on"),
    # -- layouts ---------------------------------------------------------------
    ("board_gap_in", 0.25, "in", "assumption", "gap left between boards laid flat, for movement"),
    ("board_lap_in", 1.0, "in", "assumption", "how far board-on-board boards lap their neighbours"),
    ("louver_lap_in", 0.5, "in", "assumption", "how far louvered slats lap in plan view, so rain cannot see through"),
    ("cover_overhang_in", 0.0, "in", "assumption", "how far a covering runs past the frame's outside edge"),
)
C = {name: value for name, value, _u, _k, _w in CONSTANTS}


def table() -> str:
    width = max(len(n) for n, *_ in CONSTANTS)
    return "\n".join(f"{n:<{width}}  {v:>9g} {u:<6} {k:<10} {w}" for n, v, u, k, w in CONSTANTS)
