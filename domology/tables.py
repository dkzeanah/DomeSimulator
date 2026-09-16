"""Tables the manuscript prints with ``[[table: key]]``, generated from code.

A table here is rows of text computed when the book is built -- the first row
is the header -- so a printed table and the geometry cannot drift apart.
"""

from __future__ import annotations


def _fraction(inches: float) -> str:
    from .charts import _fraction as tape
    return tape(inches)


def member_classes() -> list[tuple]:
    """The book dome's cut list: every member length, counted over forty panels."""
    from two_v_demo import book_math as bm
    rows = [("Member", "Cut", "Cut length", "True edge", "Stops short of the corner")]
    for item in bm.tree_first().member_classes:
        rows.append((item.edge_class.title(), str(item.count), _fraction(item.length_in),
                     _fraction(item.edge_length_in), f"{item.vertex_gap_in:.1f} in"))
    return rows


def frequency_ladder() -> list[tuple]:
    from . import science
    rows = [("Frequency", "Struts", "Lengths", "Hubs", "Panels", "Height / radius")]
    for step in science.ladder():
        rows.append((f"{step.frequency}V", str(step.struts), str(step.strut_classes),
                     str(step.hubs), str(step.panels), f"{step.height_m / step.radius_m:.2f}"))
    return rows


def catalogue() -> list[tuple]:
    """The Dome Creator's designs, measured the way the simulator builds them."""
    from two_v_demo.world_facts import dome_types
    rows = [("Design", "Floor, sq ft", "Struts", "Lengths", "Cost / sq ft", "Skin / floor")]
    for dome in dome_types():
        rows.append((dome.name, f"{dome.floor_sqft:,.0f}", str(dome.struts),
                     str(dome.strut_classes), f"${dome.cost_per_sqft:,.0f}",
                     f"{dome.skin_per_floor:.2f}"))
    return rows


def fortnight() -> list[tuple]:
    from two_v_demo.book_math import FORTNIGHT_PLAN
    rows = [("Work", "Days")]
    for name, first, last, *_rest in FORTNIGHT_PLAN:
        rows.append((name, str(first) if first == last else f"{first}–{last}"))
    return rows


TABLES = {
    "member-classes": member_classes,
    "frequency-ladder": frequency_ladder,
    "catalogue": catalogue,
    "fortnight": fortnight,
}


def rows(key: str) -> tuple | None:
    function = TABLES.get(key)
    return None if function is None else tuple(function())
