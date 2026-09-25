"""Live numbers for the manuscript of *The Wedge Method*.

The prose writes ``{{dome.diameter_ft}}`` rather than ``19.4``, and this
module fills it in at export time from the solver, the geometry and the cost
model. A number typed into a paragraph is correct on the day it is typed and
silently wrong from the first time anybody changes the tree, the trunk or a
price -- and nothing fails, so nobody finds it.

An unknown token is a hard error rather than a blank, because a book that
quietly prints ``{{dome.diamter_ft}}`` as nothing is worse than one that
refuses to build.

THE NAMESPACES

``dome``   the building: how big, how many of what
``cut``    what you actually saw: chords, cuts, the bite, the angles
``seam``   the joint: folds, gaps, what fits in the channel
``money``  what it costs, from the cost model
``ch``     cross-references: ``{{ch.nine}}`` is the chapter number of the
           nine-processes chapter, so prose never says "see Chapter 8" and
           goes stale when a chapter is inserted
``tool``   counts about the software the last part documents

Every name, its value and a one-line description is printed by
``py -3.12 -m wedge_book.tokens``, so a writer never has to guess one.
"""

from __future__ import annotations

import re
from dataclasses import dataclass
from typing import Callable

TOKEN = re.compile(r"\{\{([a-z_]+\.[a-z_0-9]+)\}\}")


@dataclass(frozen=True)
class Token:
    """One live figure the manuscript may quote."""

    name: str
    describe: str
    compute: Callable[[], str]

    def value(self) -> str:
        return self.compute()


def _table() -> dict[str, Token]:
    from . import numbers, outline, tooling

    values = numbers.quantities()
    money = numbers.money()
    book = outline.BOOK

    def q(name: str) -> str:
        return values[name].text()

    def m(name: str, digits: int = 0) -> str:
        return f"{money[name].value:,.{digits}f}"

    entries: list[Token] = []

    def add(name: str, describe: str, compute) -> None:
        entries.append(Token(name, describe, compute))

    # -- the building ------------------------------------------------
    add("dome.diameter_ft", "across the base, in feet",
        lambda: f"{values['diameter_ft'].value:,.2f}")
    add("dome.height_ft", "apex height, in feet",
        lambda: f"{values['height_ft'].value:,.2f}")
    add("dome.radius_in", "sphere radius, in inches", lambda: q("radius_in"))
    add("dome.floor_sqft", "floor inside the base ring, square feet",
        lambda: q("floor_sqft"))
    add("dome.panel_sqft", "flat area of all forty triangles",
        lambda: q("panel_sqft"))
    add("dome.members", "structural members in the frame",
        lambda: q("member_count"))
    add("dome.panels", "triangular panels", lambda: q("face_count"))
    add("dome.vertices", "geodesic vertices", lambda: q("vertex_count"))
    add("dome.edges", "geodesic edges", lambda: q("edge_count"))
    add("dome.seams", "interior seams", lambda: q("seam_count"))
    add("dome.base_sides", "sides of the base polygon",
        lambda: q("base_sides"))
    add("dome.seam_ft", "total run of interior seam, in feet",
        lambda: q("seam_run_ft"))
    add("dome.timber_ft", "timber in the frame, in feet",
        lambda: q("member_stock_ft"))
    add("dome.aaa", "equilateral panels", lambda: q("aaa_count"))
    add("dome.bab", "isosceles panels", lambda: q("bab_count"))

    # -- what you cut ------------------------------------------------
    add("cut.a_chord", "long chord, inches", lambda: q("a_chord_in"))
    add("cut.b_chord", "short chord, inches", lambda: q("b_chord_in"))
    add("cut.a_cut", "long member's cut length, inches",
        lambda: q("a_cut_in"))
    add("cut.b_cut", "short member's cut length, inches",
        lambda: q("b_cut_in"))
    add("cut.a_bite", "what the pinwheel takes off a long member",
        lambda: q("a_bite_in"))
    add("cut.b_bite", "what the pinwheel takes off a short member",
        lambda: q("b_bite_in"))
    add("cut.width", "the member's width across the bark face",
        lambda: q("member_width_in"))
    add("cut.depth", "the member's depth, point to bark",
        lambda: q("member_depth_in"))
    add("cut.bevel", "the butt cut's bevel, degrees",
        lambda: q("bevel_deg"))
    add("cut.mitres", "how many mitre settings across all 120 members",
        lambda: q("mitre_settings"))
    add("cut.sector", "the log sector's angle, degrees",
        lambda: q("sector_deg"))
    add("cut.splits", "how many sectors the trunk splits into",
        lambda: q("radial_splits"))
    add("cut.trunk", "trunk diameter, inches", lambda: q("trunk_diameter_in"))
    add("cut.a_factor", "long chord as a fraction of the radius",
        lambda: q("a_factor"))
    add("cut.b_factor", "short chord as a fraction of the radius",
        lambda: q("b_factor"))
    add("cut.band_bite", "the same bite for a rectangular stick",
        lambda: q("band_bite_in"))

    # -- the joint ---------------------------------------------------
    add("seam.fold_a", "an A seam's fold angle, degrees",
        lambda: q("a_fold_deg"))
    add("seam.fold_b", "a B seam's fold angle, degrees",
        lambda: q("b_fold_deg"))
    add("seam.gap_a", "sector angle left over at an A seam",
        lambda: q("a_gap_deg"))
    add("seam.gap_b", "sector angle left over at a B seam",
        lambda: q("b_gap_deg"))
    add("seam.key_a", "the A seam key's base width, inches",
        lambda: q("a_spline_base_in"))
    add("seam.key_b", "the B seam key's base width, inches",
        lambda: q("b_spline_base_in"))
    add("seam.hose_a", "largest hose an A seam channel takes",
        lambda: q("a_hose_max_in"))
    add("seam.narrowest", "narrowest panel's altitude, inches",
        lambda: q("bab_min_width_in"))
    add("seam.widest", "widest panel's altitude, inches",
        lambda: q("aaa_min_width_in"))

    # -- money -------------------------------------------------------
    add("money.price", "list price of the standard article",
        lambda: m("price"))
    add("money.cost", "what it costs to build", lambda: m("cost_to_build"))
    add("money.profit", "the maker's markup, in dollars",
        lambda: m("profit"))
    add("money.per_sqft", "price per square foot of floor",
        lambda: m("price_per_sqft", 2))
    add("money.frame", "the wedge-cut frame", lambda: m("group_frame"))
    add("money.cap", "the shower-cap shell", lambda: m("group_cap"))
    add("money.column", "the utility column and its cap",
        lambda: m("group_column"))
    add("money.pad", "the platform, which is the host's bill",
        lambda: m("group_pad"))
    add("money.labour_hours", "hours of build labour",
        lambda: m("labour_hours", 0))
    add("money.hard_price", "the same dome with a laminated hull",
        lambda: m("hard_price"))
    add("money.cap_bare", "a bare shower cap", lambda: m("cap_bare"))
    add("money.frame_weight", "the frame's weight in green pine, pounds",
        lambda: m("frame_weight_lb"))
    add("money.float_rig", "the floating rig", lambda: m("float_rig"))
    add("money.float_total", "mast, floor and rig together",
        lambda: m("float_total"))
    add("money.deck", "the staple platform: a framed deck on piers",
        lambda: m("pad_blocks"))
    add("money.slab", "a full concrete slab", lambda: m("pad_slab"))
    add("money.gravel", "a compacted gravel base", lambda: m("pad_gravel"))

    # -- the pad network, from both sides ----------------------------
    from . import network

    options = {o.label: o for o in network.tenant_options()}
    own = options["own the dome, rent the pad"]
    apartment = options["apartment lease"]
    cases = {c.label: c for c in network.host_cases()}
    pad_case = cases["one serviced pad"]

    add("net.tenant_table", "four ways to be housed, compared",
        network.tenant_table)
    add("net.host_table", "three things to do with a piece of ground",
        network.host_table)
    add("net.own_monthly", "owning a dome on a pad, per month",
        lambda: f"{own.monthly:,.0f}")
    add("net.apartment_entry", "what an apartment costs at the door",
        lambda: f"{apartment.entry:,.0f}")
    add("net.crossover_months", "months before owning overtakes renting",
        lambda: f"{network.crossover_months():,.0f}")
    add("net.ten_year_gap", "ten-year difference against an apartment",
        lambda: f"{apartment.over(10.0) - own.over(10.0):,.0f}")
    add("net.dome_life", "the dome's assumed service life, years",
        lambda: f"{network._declared('dome_service_life_years'):,.0f}")
    add("net.pad_rent", "what a serviced pad rents for, per month",
        lambda: f"{network.pad_rent_monthly():,.0f}")
    add("net.pad_upfront", "what one serviced pad costs the host",
        lambda: f"{pad_case.upfront:,.0f}")
    add("net.pad_net", "what one pad earns the host a year, net",
        lambda: f"{pad_case.yearly_net:,.0f}")
    add("net.pad_payback", "how long a pad takes to pay back",
        lambda: f"{pad_case.payback_years():,.1f} years")

    # -- cross-references --------------------------------------------
    for chapter in book.chapters:
        add(f"ch.{chapter.key}", f"chapter number of {chapter.title!r}",
            (lambda number=chapter.number: str(number)))

    # -- the software ------------------------------------------------
    add("tool.worlds", "three-dimensional environments that ship with this",
        lambda: str(len(tooling.by_kind("world"))))
    add("tool.models", "arithmetic tools that ship with this",
        lambda: str(len(tooling.by_kind("model"))))
    add("tool.total", "programs documented in the last part",
        lambda: str(len(tooling.catalogue())))
    add("tool.chapters", "chapters in this book",
        lambda: str(len(book.chapters)))
    add("tool.figures", "pictures in this book",
        lambda: str(len(book.figures)))
    add("tool.table", "the whole catalogue of programs", tooling.table)

    # The nine processes are a list this book leans its scaling argument on,
    # so it reads them rather than printing its own copy.
    from two_v_demo import franken_economics

    processes = franken_economics.PROCESSES
    add("nine.count", "how many processes turn timber into a shell",
        lambda: str(len(processes)))
    add("nine.list", "the nine, in the order they happen",
        lambda: ", ".join(p.key for p in processes))
    add("nine.flat", "how many of them happen on a bench",
        lambda: str(sum(1 for p in processes if p.flat)))

    return {token.name: token for token in entries}


def tokens() -> dict[str, Token]:
    """Every token, rebuilt. Not cached: the numbers are the point."""
    return _table()


def resolve(text: str, strict: bool = True) -> str:
    """Fill every ``{{group.name}}`` in ``text``.

    ``strict`` raises on an unknown token, which is what an export wants. The
    writing desk passes ``strict=False`` so a half-written page still renders
    with the typo visible in it.
    """
    table = tokens()

    def swap(match: re.Match) -> str:
        name = match.group(1)
        found = table.get(name)
        if found is None:
            if strict:
                near = [key for key in table
                        if key.split(".")[0] == name.split(".")[0]]
                raise KeyError(
                    f"no token {name!r}. The {name.split('.')[0]!r} "
                    f"namespace has {sorted(near)[:8]}")
            return match.group(0)
        return found.value()

    return TOKEN.sub(swap, text)


def unknown_tokens(text: str) -> tuple[str, ...]:
    """Every token in ``text`` that this module cannot fill."""
    table = tokens()
    return tuple(sorted({name for name in TOKEN.findall(text)
                         if name not in table}))


def report() -> str:
    lines = ["TOKENS", ""]
    group = ""
    for name, token in sorted(tokens().items()):
        head = name.split(".")[0]
        if head != group:
            group, _ = head, lines.append("")
            lines.append(f"  {head}")
        lines.append(f"    {{{{{name}}}}}"
                     f"{'':<{max(0, 30 - len(name))}} "
                     f"{token.value():>14}   {token.describe}")
    return "\n".join(lines)


def validate_tokens() -> None:
    """Every token resolves, and the ones the book leans on are right."""
    table = tokens()
    assert len(table) > 60, len(table)

    for name, token in table.items():
        assert "." in name, name
        assert token.describe, name
        value = token.value()
        assert value, name
        assert "{{" not in value, name

    # The book's own headline figures.
    assert resolve("{{cut.a_chord}}") == "72.000"
    assert resolve("{{dome.members}}") == "120"
    assert resolve("{{dome.panels}}") == "40"

    # Cross-references point at real chapters and move when the outline does.
    from . import outline

    for chapter in outline.BOOK.chapters:
        assert resolve(f"{{{{ch.{chapter.key}}}}}") == str(chapter.number)

    # An unknown token is loud in an export and quiet at the desk.
    try:
        resolve("{{dome.not_a_thing}}")
    except KeyError:
        pass
    else:
        raise AssertionError("an unknown token should not resolve")
    assert resolve("{{dome.not_a_thing}}", strict=False) \
        == "{{dome.not_a_thing}}"
    assert unknown_tokens("{{dome.nope}} {{cut.a_chord}}") \
        == ("dome.nope",)

    assert "TOKENS" in report()


def main(argv: list[str] | None = None) -> int:
    import argparse

    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--check", action="store_true")
    args = parser.parse_args(argv)

    validate_tokens()
    if args.check:
        print("tokens ok")
        return 0
    print(report())
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
