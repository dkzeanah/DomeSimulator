"""The facts map: the derive-and-simulate index.

Every numeric claim the agent encounters should first be looked up here.
Each entry points at a real, validated function in the repository whose
output is *computed and proved* (each module has a ``validate_*`` the
selftests run).  Only what no entry covers becomes a declared constant
or a resolution-ledger item.

The map is curated on purpose: ``query_facts`` may only call these
named functions with the declared parameters — never arbitrary code.
"""

from __future__ import annotations

from dataclasses import dataclass, field


@dataclass(frozen=True)
class FactSpec:
    id: str
    description: str
    module: str
    func: str
    params: dict[str, type] = field(default_factory=dict)
    """Allowed keyword arguments (name -> python type) for the call."""
    note: str = ""
    kind: str = "call"
    """``call`` invokes ``func``; ``value`` reads it as data.

    Some of what a film needs is a table rather than a function — the assembly
    line's assumptions, for instance.  Without this the entry pointed at a dict
    and the tool tried to call it, which failed with ``'dict' object is not
    callable`` every single time."""


FACT_SPECS: dict[str, FactSpec] = {}


def _add(spec: FactSpec) -> None:
    FACT_SPECS[spec.id] = spec


# --- 2V geometry --------------------------------------------------------
_add(FactSpec(
    "geometry.demo",
    "The 2V demo geometry: chord factors, strut classes, triangle classes, "
    "area and angle audit for the reference dome.",
    "two_v_demo.geometry", "build_demo_geometry",
    note="validate_geometry() proves it; report via geometry.calculation_report"))
_add(FactSpec(
    "geometry.fit",
    "Fit the two chord classes to supplied strut lengths and return the "
    "resulting radius, counts, and per-class lengths.",
    "two_v_demo.geometry", "fit_measurements",
    {"long_length": float, "short_length": float}))
_add(FactSpec(
    "geometry.report",
    "Plain-text calculation report for the 2V dome.",
    "two_v_demo.geometry", "calculation_report"))

# --- hubless -------------------------------------------------------------
_add(FactSpec(
    "hubless.summary",
    "Hubless frame counts: 40 triangles, 120 members, 65 unique edges, "
    "seam and panel classes.",
    "two_v_demo.hubless_geometry", "hubless_summary"))
_add(FactSpec(
    "hubless.report",
    "Plain-text hubless build report.",
    "two_v_demo.hubless_geometry", "hubless_report",
    {"radius": float}))

# --- trees, wedges, pinwheels --------------------------------------------
_add(FactSpec(
    "wedge.tree_yield",
    "What one log yields: solid board feet, wedge recovery, 2x4 recovery, "
    "and the honest comparison between them.",
    "two_v_demo.wedge_geometry", "tree_yield"))
_add(FactSpec(
    "wedge.build_plan",
    "The full two-tree build plan: blanks, members needed, surplus, and the "
    "dome the stock sizes.",
    "two_v_demo.wedge_geometry", "build_plan",
    {"trees": int, "design_diameter_in": float}))
_add(FactSpec(
    "wedge.radius_for_member",
    "Invert the geometry: which dome radius a given member length sizes.",
    "two_v_demo.wedge_geometry", "radius_for_member_length",
    {"target_in": float}))
_add(FactSpec(
    "wedge.report",
    "Plain-text wedge report (tree, sections, members, gaskets).",
    "two_v_demo.wedge_geometry", "wedge_report"))

# --- costing --------------------------------------------------------------
_add(FactSpec(
    "costing.variants",
    "Costed dome build variants (framing value, shell options) from the "
    "shared cost model.",
    "two_v_demo.dome_costing", "build_variants"))
_add(FactSpec(
    "costing.radius_for_floor",
    "Dome radius that delivers a given floor area.",
    "two_v_demo.dome_costing", "radius_for_floor",
    {"floor_sqft": float}))
_add(FactSpec(
    "costing.report",
    "Plain-text costing report for a floor area.",
    "two_v_demo.dome_costing", "costing_report",
    {"floor_sqft": float}))

# --- the book's arithmetic -------------------------------------------------
_add(FactSpec(
    "book.frame_counts",
    "Book's frame accounting: (120 members, 40 panels, 65 unique edges) "
    "and why 40 triangles need 120 members.",
    "two_v_demo.book_math", "frame_counts"))
_add(FactSpec(
    "book.tree_first",
    "Method B: size the dome from the tree you have (BOOK_TREE).",
    "two_v_demo.book_math", "tree_first"))
_add(FactSpec(
    "book.design_first",
    "Method A: the cut list and felling list from a chosen design.",
    "two_v_demo.book_math", "design_first",
    {"radius_in": float}))
_add(FactSpec(
    "book.round_trip",
    "The proof that Methods A and B are one calculation held at opposite "
    "ends; prints the residual.",
    "two_v_demo.book_math", "round_trip",
    {"radius_in": float}))
_add(FactSpec(
    "book.report",
    "Plain-text calculation audit: declared constants, both methods, the "
    "fortnight, and the unflattering figures printed on purpose.",
    "two_v_demo.book_math", "book_math_report"))

# --- pine value (the worked example) --------------------------------------
_add(FactSpec(
    "pine.model",
    "The pine value-ladder model: solid board feet, wedge vs sawn recovery, "
    "framing value, financed avoided payments, wage per hour.",
    "two_v_demo.pine_value_economics", "pine"))
_add(FactSpec(
    "pine.sources",
    "Every borrowed constant the pine model uses, with its provenance "
    "(author-measured vs published).",
    "two_v_demo.pine_value_economics", "source_lines"))
_add(FactSpec(
    "pine.tokens",
    "The pine model's token specs (the live figures a film would quote).",
    "two_v_demo.pine_value_economics", "token_specs"))

# --- factory economics ------------------------------------------------------
_add(FactSpec(
    "al_build.comparisons",
    "Box-vs-dome comparisons (shed and home tiers) priced by identical "
    "rates.",
    "al_build", "building_comparisons"))
_add(FactSpec(
    "al_build.assumptions",
    "The assembly line's editable assumption table (wages, workers, capex, "
    "pricing, QC).",
    "al_build", "ASSUMPTIONS", kind="value",
    note="a table, not a function: read as data"))


def list_fact_ids() -> tuple[str, ...]:
    return tuple(FACT_SPECS)
