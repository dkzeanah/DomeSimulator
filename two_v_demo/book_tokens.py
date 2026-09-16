"""Live numbers for the manuscript of *2 Trees*.

The manuscript is prose with holes in it.  Where a sentence needs a figure it
writes ``{{dome.diameter_ft}}`` rather than ``21.6``, and this module fills it
in at export time from :mod:`book_math`.

Why bother
----------
Because the alternative has been tried.  A number typed into a paragraph is
correct on the day it is typed and silently wrong from the first time anybody
changes the tree, the gasket, the split count or the geometry.  There is no
way to find those; nothing fails, the book simply becomes untrue in places
nobody remembers.  A token cannot go stale: it is resolved fresh on every
export, and an unknown one is a hard error rather than a blank.

Using them
----------
In a chapter file, write the token in double braces::

    Two trees give {{dome.struts_available}} struts for a frame that needs
    {{frame.members}}.

Every token, its current value and a one-line description are listed in the
writing desk, so an author never has to guess a name.  :func:`resolve` expands
them; :func:`unknown_tokens` finds typos before an export does.
"""

from __future__ import annotations

import re
from dataclasses import dataclass
from typing import Callable

from . import book_math as bm
from . import wedge_geometry as wg


TOKEN_PATTERN = re.compile(r"\{\{([a-z_]+\.[a-z_0-9]+)\}\}")


@dataclass(frozen=True)
class Token:
    """One live figure the manuscript may quote."""

    name: str
    describe: str
    compute: Callable[[], str]

    def value(self) -> str:
        return self.compute()


def _n(value: float, places: int = 0) -> str:
    """A number set the way a book sets numbers: grouped, fixed places."""
    return f"{value:,.{places}f}"


def _build() -> tuple[Token, ...]:
    """Every token, built once against the current geometry."""
    plan = bm.BOOK_TREE
    dome = bm.tree_first()
    work = bm.fortnight(plan)
    members, panels, edges = bm.frame_counts()
    seams = bm.panel_seam_count()
    sawn = wg.tree_yield()
    trip = bm.round_trip(dome.radius_in)

    return (
        # -- the tree --------------------------------------------------
        Token("tree.butt_diameter_in", "trunk diameter at the butt",
              lambda: _n(plan.butt_diameter_in, 0)),
        Token("tree.top_diameter_in", "trunk diameter at the top",
              lambda: _n(plan.top_diameter_in, 0)),
        Token("tree.usable_length_ft", "usable straight trunk",
              lambda: _n(plan.usable_length_ft, 0)),
        Token("tree.section_length_ft", "bucking length",
              lambda: _n(plan.section_length_ft, 0)),
        Token("tree.sections", "sections per tree",
              lambda: str(plan.sections)),
        Token("tree.sectors", "sectors a section is split into",
              lambda: str(plan.sectors)),
        Token("tree.sector_angle_deg", "angle of one sector",
              lambda: _n(360.0 / plan.sectors, 0)),
        Token("tree.struts_per_tree", "struts from one tree",
              lambda: str(plan.struts_per_tree)),
        Token("tree.offcut_ft", "trunk left over after bucking",
              lambda: _n(plan.offcut_ft, 1)),
        Token("tree.solid_bf", "solid wood in one trunk, board feet",
              lambda: _n(plan.solid_bf, 0)),
        Token("tree.kerf_bf", "board feet lost to the saw kerf",
              lambda: _n(plan.kerf_bf, 0)),
        Token("tree.wedge_bf", "usable board feet after splitting",
              lambda: _n(plan.wedge_bf, 0)),
        Token("tree.recovery_pct", "wedge recovery, per cent",
              lambda: _n(plan.recovery * 100.0, 1)),
        Token("tree.sawn_recovery_pct",
              "recovery if the same log were sawn into 2x4s, per cent",
              lambda: _n(sawn.two_by_four_recovery * 100.0, 0)),
        Token("tree.recovery_gain",
              "how many times more usable wood splitting gives",
              lambda: _n(plan.recovery / sawn.two_by_four_recovery, 2)),
        Token("tree.bf_per_strut", "board feet in one strut",
              lambda: _n(plan.bf_per_strut, 2)),

        # -- the member ------------------------------------------------
        Token("member.width_in", "bark-face width of one strut",
              lambda: _n(plan.member_width_in, 2)),
        Token("member.depth_in", "pith-to-bark depth of one strut",
              lambda: _n(plan.member_depth_in, 2)),
        Token("member.area_in2", "cross-section of one strut",
              lambda: _n(plan.member_area_in2, 2)),
        Token("member.as_nominal_2x4s",
              "strut section in nominal 2x4s (8.00 sq in)",
              lambda: _n(plan.equivalent_two_by_fours, 2)),
        Token("member.as_dressed_2x4s",
              "strut section in dressed 2x4s (5.25 sq in)",
              lambda: _n(plan.equivalent_dressed_two_by_fours, 2)),

        # -- the board it replaces -------------------------------------
        Token("board.nominal_in2", "section of a nominal 2x4",
              lambda: _n(bm.NOMINAL_TWO_BY_FOUR_IN2, 2)),
        Token("board.dressed_in2", "section of a dressed 2x4",
              lambda: _n(bm.DRESSED_TWO_BY_FOUR_IN2, 2)),
        Token("board.price_usd", "shelf price of a 2x4x16",
              lambda: f"{bm.declared('two_by_four_price_usd'):,.2f}"),

        # -- the frame -------------------------------------------------
        Token("frame.members", "members in the frame",
              lambda: str(members)),
        Token("frame.panels", "triangular panels in the frame",
              lambda: str(panels)),
        Token("frame.edges", "unique edges in the frame",
              lambda: str(edges)),
        Token("frame.seams", "seams between two panels",
              lambda: str(seams)),
        Token("frame.rim_edges", "rim edges, which join nothing",
              lambda: str(edges - seams)),
        Token("frame.members_per_panel", "members in one panel",
              lambda: str(members // panels)),

        # -- the wedge against the board it replaces --------------------
        # The comparison is quoted on a modest 8-inch log rather than this
        # book's own tree, because the small case is the conservative one
        # and a claim should be made at its weakest.
        Token("versus.diameter_in", "the log the comparison is made on",
              lambda: _n(_versus().diameter_in, 0)),
        Token("versus.wedge_area_in2", "cross-section of one wedge from it",
              lambda: f"{_versus().wedge.area_in2:.2f}"),
        Token("versus.board_area_in2", "cross-section of a dressed 2x4",
              lambda: f"{_versus().board.area_in2:.2f}"),
        Token("versus.area_ratio", "wedge area as a multiple of the board",
              lambda: f"{_versus().area_ratio:.2f}"),
        Token("versus.area_gain_pct", "per cent more wood in the wedge",
              lambda: f"{_versus().area_gain_pct:+.0f}"),
        Token("versus.stiffness_pct",
              "per cent difference in bending stiffness",
              lambda: f"{(_versus().stiffness_ratio - 1) * 100:+.0f}"),
        Token("versus.strength_pct",
              "per cent difference in bending strength",
              lambda: f"{(_versus().strength_ratio - 1) * 100:+.0f}"),
        Token("versus.flat_stiffness_ratio",
              "wedge stiffness against the same board laid flat",
              lambda: f"{_versus().flat_stiffness_ratio:.1f}"),
        Token("versus.verdict", "the whole comparison in one line",
              lambda: _versus().verdict),
        Token("versus.wedge_depth_in", "pith-to-bark depth of that wedge",
              lambda: f"{_versus().wedge.depth_in:.2f}"),
        Token("versus.wedge_width_in", "bark-face width of that wedge",
              lambda: f"{_versus().wedge.width_in:.2f}"),

        # -- the panelised frame's duplicated edges ---------------------
        Token("edges.duplicated", "members that exist because edges repeat",
              lambda: str(bm.edge_accounting().duplicated_members)),
        Token("edges.duplication_ratio", "members per unique edge",
              lambda: f"{bm.edge_accounting().duplication_ratio:.2f}"),

        # -- processing effort ------------------------------------------
        Token("route.mill_steps", "operations from tree to graded board",
              lambda: str(len(bm.MILL_ROUTE))),
        Token("route.wedge_steps", "operations from tree to member in frame",
              lambda: str(len(bm.WEDGE_ROUTE))),

        # -- the seams, which turn out to take only two angles ----------
        Token("seam.half_sector_deg",
              "angle a raw split face sits off the member centreline",
              lambda: f"{180.0 / plan.sectors:.1f}"),
        Token("seam.shave_deep_in",
              "deepest cut the shaved-flat option needs",
              lambda: f"{max(r.depth_in for r in bm.shaving_plan()):.2f}"),
        Token("seam.shave_pct_of_depth",
              "that cut as a per cent of the member's depth",
              lambda: f"{max(r.as_fraction_of_depth for r in bm.shaving_plan()) * 100:.0f}"),
        Token("seam.distinct_angles", "how many fold angles the dome has",
              lambda: str(len(_seam_groups()))),
        Token("seam.fold_a_deg", "the tighter of the two fold angles",
              lambda: f"{_seam_groups()[0][0]:.2f}"),
        Token("seam.fold_b_deg", "the wider of the two fold angles",
              lambda: f"{_seam_groups()[-1][0]:.2f}"),
        Token("seam.count_a", "seams at the tighter angle",
              lambda: str(_seam_groups()[0][1])),
        Token("seam.count_b", "seams at the wider angle",
              lambda: str(_seam_groups()[-1][1])),
        Token("seam.sector_angle_deg",
              "fold plus raw gap, which is one sector",
              lambda: _n(360.0 / plan.sectors, 0)),

        # -- the dome --------------------------------------------------
        Token("dome.radius_in", "dome radius",
              lambda: _n(dome.radius_in, 2)),
        Token("dome.diameter_ft", "dome diameter, feet",
              lambda: _n(dome.diameter_ft, 1)),
        Token("dome.height_ft", "standing height at the centre",
              lambda: _n(dome.height_ft, 1)),
        Token("dome.floor_sqft", "floor area",
              lambda: _n(dome.floor_sqft, 0)),
        Token("dome.longest_member_in", "longest member in the frame",
              lambda: _n(dome.longest_member_in, 2)),
        Token("dome.shortest_member_in", "shortest member in the frame",
              lambda: _n(dome.shortest_member_in, 2)),
        Token("dome.member_lengths", "how many distinct lengths to cut",
              lambda: str(len(dome.member_classes))),
        Token("dome.trees", "trees the book's dome is cut from",
              lambda: str(dome.trees)),
        Token("dome.struts_available", "struts two trees give",
              lambda: str(dome.struts_available)),
        Token("dome.spare_struts", "struts left over",
              lambda: str(dome.spare_struts)),
        Token("dome.trees_strictly_needed",
              "trees the frame actually consumes",
              lambda: _n(dome.trees_strictly_needed, 2)),
        Token("dome.timber_ft", "feet of timber standing in the frame",
              lambda: _n(dome.timber_in_frame_ft, 0)),

        # -- the two methods -------------------------------------------
        Token("roundtrip.residual_in",
              "how far the two methods disagree, inches",
              lambda: f"{trip.radius_error_in:.1e}"),

        # -- Method A's worked example, so the prose can quote it ------
        # Chapter 18 carries one example all the way through. Every one of
        # its intermediate figures is here, because a worked example with
        # typed numbers in it is the easiest place in a book for an error
        # to hide: nothing looks more finished than arithmetic.
        Token("method_a.floor_sqft", "the worked example's floor area",
              lambda: _n(_worked_a().floor_sqft, 0)),
        Token("method_a.radius_in", "radius that gives that floor",
              lambda: _n(_worked_a().radius_in, 0)),
        Token("method_a.radius_ft", "the same radius in feet",
              lambda: _n(_worked_a().radius_in / 12.0, 2)),
        Token("method_a.longest_in", "its longest member",
              lambda: _n(_worked_a().longest_member_in, 1)),
        Token("method_a.shortest_in", "its shortest member",
              lambda: _n(_worked_a().shortest_member_in, 1)),
        Token("method_a.buck_ft", "bucking length it asks for",
              lambda: str(_worked_a().bucking_length_ft)),
        Token("method_a.buck_in", "that bucking length in inches",
              lambda: _n(_worked_a().bucking_length_ft * 12, 0)),
        Token("method_a.sections", "sections of trunk it needs",
              lambda: _n(_worked_a().sections_needed, 0)),
        Token("method_a.trunk_ft", "feet of trunk it needs",
              lambda: _n(_worked_a().trunk_feet_needed, 0)),
        Token("method_a.trees", "trees it needs",
              lambda: _n(_worked_a().trees_needed, 2)),
        Token("method_a.whole_trees", "trees to actually fell",
              lambda: str(_worked_a().whole_trees_needed)),

        # -- the saw and the fortnight ---------------------------------
        Token("saw.displacement_cc", "engine size of the saw used",
              lambda: _n(bm.declared("saw_displacement_cc"), 1)),
        Token("saw.bar_in", "bar length of the saw used",
              lambda: _n(bm.declared("saw_bar_in"), 0)),
        Token("saw.price_usd", "what the saw cost",
              lambda: _n(bm.declared("saw_price_usd"), 0)),
        Token("saw.kerf_in", "width of one chain cut",
              lambda: f"{bm.declared('chain_kerf_in'):.2f}"),
        Token("work.days", "days the build took",
              lambda: _n(work.days, 0)),
        Token("work.struts_per_hour", "struts ripped in an hour",
              lambda: _n(work.struts_per_hour, 1)),
        Token("work.ripping_hours", "hours of ripping for a whole dome",
              lambda: _n(work.ripping_hours, 0)),
        Token("work.afternoons", "afternoons of ripping",
              lambda: _n(work.afternoons_of_ripping, 0)),
        Token("work.rate_nominal_usd",
              "implied hourly rate against nominal 2x4s",
              lambda: f"{work.hourly_rate_usd(plan.equivalent_two_by_fours):,.2f}"),
        Token("work.rate_dressed_usd",
              "implied hourly rate against dressed 2x4s",
              lambda: f"{work.hourly_rate_usd(plan.equivalent_dressed_two_by_fours):,.2f}"),
        Token("work.harvest_days",
              "days from the first felling cut to the last strut ripped",
              lambda: str(bm.harvest_days())),
        Token("work.felling_days", "days the plan gives to felling",
              lambda: str(bm.phase_days("felling"))),
        Token("work.bucking_days", "days the plan gives to bucking",
              lambda: str(bm.phase_days("bucking"))),
        Token("work.ripping_days", "days the plan gives to ripping",
              lambda: str(bm.phase_days("ripping"))),

        # -- the fuel the ripping takes ---------------------------------
        # Measured burn times derived hours times a declared tank, shown as a
        # range because the tank figure rests on listings nobody has checked.
        Token("fuel.tanks_per_hour", "saw fuel tanks emptied per hour, measured",
              lambda: _n(bm.ripping_fuel().tanks_per_hour, 0)),
        Token("fuel.rip_hours", "hours of ripping the fuel figure covers",
              lambda: _n(bm.ripping_fuel().hours, 0)),
        Token("fuel.rip_tanks", "tanks of fuel to rip the whole frame",
              lambda: _n(bm.ripping_fuel().tanks, 0)),
        Token("fuel.tank_l", "the saw's fuel tank, litres, low estimate",
              lambda: f"{bm.ripping_fuel().tank_l:.2f}"),
        Token("fuel.tank_high_l", "the saw's fuel tank, litres, high estimate",
              lambda: f"{bm.ripping_fuel().tank_high_l:.2f}"),
        Token("fuel.rip_litres", "litres of fuel to rip the frame, low estimate",
              lambda: _n(bm.ripping_fuel().litres, 1)),
        Token("fuel.rip_litres_high",
              "litres of fuel to rip the frame, high estimate",
              lambda: _n(bm.ripping_fuel().litres_high, 1)),
        Token("fuel.rip_gallons", "US gallons to rip the frame, low estimate",
              lambda: _n(bm.ripping_fuel().gallons, 1)),
        Token("fuel.rip_gallons_high", "US gallons to rip the frame, high estimate",
              lambda: _n(bm.ripping_fuel().gallons_high, 1)),

        # -- what a house costs, and what the fortnight is worth ---------
        *_house_tokens(),
        *_why_tokens(),
        *_pine_tokens(),
        *_domology_tokens(),

        # -- build choices ---------------------------------------------
        Token("jig.head_overfit_in", "stock deliberately left long",
              lambda: _n(bm.declared("head_overfit_in"), 0)),
        Token("jig.butt_allowance_in", "spare stock past the butt cut",
              lambda: _n(bm.declared("butt_allowance_in"), 0)),
        Token("jig.gasket_in", "thickness of the seam key",
              lambda: f"{bm.declared('gasket_thickness_in'):.2f}"),

        # -- cross-references ------------------------------------------
        # Chapter numbers move whenever one is inserted. Prose writes
        # {{ch.method_a}} and gets the current number, so a structural
        # change cannot silently leave "see Chapter 18" pointing at the
        # wrong chapter -- the same discipline as the arithmetic tokens,
        # applied to the outline.
        *_chapter_tokens(),

        # -- the book itself -------------------------------------------
        Token("book.chapters", "chapters in this book",
              _chapter_count),
        Token("book.parts", "parts in this book", _part_count),
        Token("book.figures", "figures in this book", _figure_count),
    )


def _pct(fraction: float, places: int = 1) -> str:
    """A share as a percentage, without a trailing ``.0``: 15, 7.5, 25.7."""
    text = f"{fraction * 100.0:.{places}f}"
    return text.rstrip("0").rstrip(".") if "." in text else text


def _house_tokens() -> list[Token]:
    """The house, trailer and fortnight figures, all from :mod:`house_economics`.

    Every figure a tally adds up is rounded together with the others in its sum
    (:func:`house_economics.split_round`), so a column on screen that says the parts
    make the whole is true to the dollar it shows.
    """
    from . import house_economics as he

    def house_parts() -> dict[str, int]:
        split = he.house()
        p = split.parts
        return he.split_round({
            "lot": p["lot"], "construction": p["construction"],
            "builder": p["overhead"] + p["profit"],
            "selling": p["commission"] + p["marketing"] + p["financing"]}, 100.0)

    def peak_parts() -> dict[str, int]:
        return he.split_round(dict(he.house(peak=True).buckets), 100.0)

    def trailer_parts() -> dict[str, int]:
        lot = he.trailer()
        return he.split_round({"dealer": lot.dealer, "materials": lot.materials,
                               "payroll": lot.payroll, "other": lot.factory_other},
                              100.0)

    def stack_parts() -> dict[str, int]:
        total = he.stack()
        return he.split_round({"cash": total.cash, "margin": total.margin,
                               "labor": total.labor, "trees": total.trees,
                               "shape": total.shape}, 100.0)

    def frame_shown() -> tuple[int, int]:
        """The frame's bought price and the fortnight's cash, as the tally shows them."""
        frame = he.frame_value()
        return int(round(frame.buy_house)), int(round(frame.cash_total))

    def part(table, key):
        return lambda: _n(table()[key], 0)

    tokens = [
        Token("time.months", "average months, start to finish, new houses 2024",
              lambda: f"{he.value('soc_start_to_finish_months'):.1f}"),
        Token("time.owner_months", "months when the owner builds it",
              lambda: f"{he.value('soc_owner_built_months'):.1f}"),
        Token("time.schedule_weeks", "weeks in the builder's schedule",
              lambda: _n(he.value("schedule_weeks"), 0)),
        Token("time.total_pct", "the schedule's shares, added up",
              lambda: _pct(sum(s for _, _, s, _ in he.time_split()), 0)),
        Token("house.price", "the author's standard house, dollars",
              lambda: _n(he.value("house_price"), 0)),
        Token("house.labor_share_pct", "the author's labor share of building cost",
              lambda: _pct(he.value("labor_share"), 0)),
        Token("house.lot", "the land in that house, dollars",
              part(house_parts, "lot")),
        Token("house.construction", "building it, dollars",
              part(house_parts, "construction")),
        Token("house.builder", "the builder's overhead and profit, dollars",
              part(house_parts, "builder")),
        Token("house.selling", "commission, marketing and financing, dollars",
              part(house_parts, "selling")),
        Token("house.sqft", "new house that price buys at the national average",
              lambda: _n(he.house().sqft, 0)),
        Token("house.labor_pct", "labor as a share of the price",
              lambda: _pct(he.house().share("labor"))),
        Token("house.framing_pct", "framing as a share of building cost",
              lambda: _pct(he.stage_share("framing"))),
        Token("house.framing_price_pct", "framing as a share of the price",
              lambda: _pct(he.stage_share("framing") * he.price_share("construction"))),
        Token("lumber.peak", "record framing lumber price, dollars per 1,000 bd ft",
              lambda: _n(he.value("lumber_flcp_peak"), 0)),
        Token("lumber.added", "what the peak added to an average new home",
              lambda: _n(he.value("lumber_2021_added"), 0)),
        Token("house.peak_price", "the house with lumber at the 2021 peak",
              lambda: _n(sum(peak_parts().values()), 0)),
        Token("house.peak_labor_pct", "labor's share at the lumber peak",
              lambda: _pct(he.house(peak=True).share("labor"))),
        Token("trailer.price", "the author's manufactured home, dollars",
              lambda: _n(he.value("trailer_price"), 0)),
        Token("trailer.dealer", "the dealer's share", part(trailer_parts, "dealer")),
        Token("trailer.materials", "factory materials",
              part(trailer_parts, "materials")),
        Token("trailer.payroll", "factory payroll", part(trailer_parts, "payroll")),
        Token("trailer.other", "factory overhead and profit",
              part(trailer_parts, "other")),
        Token("trailer.labor_pct", "factory payroll as a share of the price",
              lambda: _pct(he.trailer().payroll / he.trailer().price)),
        Token("trailer.per_sqft", "average manufactured home, dollars a sq ft",
              lambda: f"{he.value('mhs_2023_usd_per_sqft'):.2f}"),
        Token("trailer.sqft", "manufactured home that price buys",
              lambda: _n(he.trailer().sqft, 0)),
        Token("value.sqft", "the dome's floor, sq ft",
              lambda: _n(he.dome_floor_sqft(), 0)),
        Token("value.days", "days in the fortnight",
              lambda: _n(bm.declared("build_days"), 0)),
        Token("value.hours", "the author's hands-on hours for the shell",
              lambda: _n(he.frame_value().hours, 0)),
        Token("value.frame_buy", "the frame bought at the national rate",
              lambda: _n(frame_shown()[0], 0)),
        Token("value.frame_cash", "what the fortnight spends in money",
              lambda: _n(frame_shown()[1], 0)),
        Token("value.frame_saved", "what building it keeps",
              lambda: _n(frame_shown()[0] - frame_shown()[1], 0)),
        Token("value.rate", "what each hour of the fortnight keeps",
              lambda: _n((frame_shown()[0] - frame_shown()[1])
                         / he.frame_value().hours, 0)),
        Token("value.rate_trailer", "the same against a manufactured home's rate",
              lambda: _n(he.frame_value().rate_trailer, 0)),
        Token("value.buy_hours", "hours of typical take-home pay to buy the frame",
              lambda: _n(he.frame_value().buy_house / he.after_tax_hourly(), 0)),
        Token("wage.carpenter", "a carpenter's median wage, dollars an hour",
              lambda: f"{he.hourly('wage_carpenters'):.2f}"),
        Token("wage.median", "the median wage, all workers, dollars an hour",
              lambda: f"{he.hourly('wage_all_workers'):.2f}"),
        Token("wage.take_home", "what a median worker keeps of one more hour",
              lambda: f"{he.after_tax_hourly():.2f}"),
        Token("stack.buy", "the dome's floor bought whole",
              lambda: _n(sum(stack_parts().values()), 0)),
        Token("stack.cash", "what the dome way still pays in money",
              part(stack_parts, "cash")),
        Token("stack.margin", "the builder's and seller's share",
              part(stack_parts, "margin")),
        Token("stack.labor", "labor done yourself", part(stack_parts, "labor")),
        Token("stack.trees", "lumber from your own trees, less what they cost",
              part(stack_parts, "trees")),
        Token("stack.shape", "what the dome's shape saves",
              part(stack_parts, "shape")),
        Token("stack.unchanged_pct", "share of building cost the shape cannot touch",
              lambda: _pct(he.stack().unchanged, 0)),
        Token("stack.trailer_floor", "the dome's floor at a trailer's price",
              lambda: _n(he.trailer_floor_price(), 0)),
        Token("stack.cash_factory", "the dome way on only what a trailer includes",
              lambda: _n(he.dome_cash_factory_scope(), 0)),
    ]
    for key, name in (("framing", "framing"), ("skin", "skin"),
                      ("perimeter", "perimeter"), ("runs", "runs")):
        tokens.append(Token(f"shape.{name}_less", f"per cent less {name} in the dome",
                            (lambda k: lambda: _pct(1.0 - he.geometry_ratios()[k], 0))(key)))
    for key in ("materials", "labor", "fees", "land", "builder", "selling"):
        tokens.append(Token(f"house.peak_{key}", f"{key} at the lumber peak",
                            part(peak_parts, key)))
    for stage in he.TIME_ORDER:
        tokens.append(Token(f"time.pct_{stage}", f"share of build time: {stage}",
                            (lambda s: lambda: _pct(he.time_share(s)))(stage)))
    return tokens


def _why_tokens() -> list[Token]:
    """The author's case in *Why Build This Way?*, from :mod:`why_build_economics`."""
    from . import why_build_economics as wb
    return [Token(name, describe, compute)
            for name, describe, compute in wb.token_specs()]


def _pine_tokens() -> list[Token]:
    """One pine's value ladder, from :mod:`pine_value_economics`."""
    from . import pine_value_economics as pv
    return [Token(name, describe, compute)
            for name, describe, compute in pv.token_specs()]


def _domology_tokens() -> list[Token]:
    """*Domology*'s dome science and project history, from :mod:`domology.science`.

    Loaded lazily and only when the ``domology`` package is importable (it sits
    beside ``two_v_demo`` at the repository root), so nothing here depends on it.
    """
    try:
        from domology import science
    except ImportError:
        return []
    return [Token(name, describe, compute)
            for name, describe, compute in science.token_specs()]


WORKED_A_FLOOR_SQFT = 300.0
"""The floor area Chapter 18 carries all the way through. One number, chosen
once, so the chapter's dozen intermediate figures all move together if it
ever changes."""


def _worked_a():
    return bm.design_first_for_floor(WORKED_A_FLOOR_SQFT)


VERSUS_LOG_IN = 8.0
"""The log the wedge-versus-board comparison is made on.

Deliberately modest: a tree most people can fell and move alone. Bigger logs
flatter the wedge, so the claim is made at its weakest."""


def _versus():
    return bm.wedge_versus_board(VERSUS_LOG_IN)


_SEAM_GROUPS: tuple[tuple[float, int], ...] | None = None


def _seam_groups() -> tuple[tuple[float, int], ...]:
    """(fold angle, count) for each distinct seam angle, tightest first.

    Solving the dome is slow enough that this is worth holding on to; the
    book quotes these five or six times.
    """
    global _SEAM_GROUPS
    if _SEAM_GROUPS is None:
        from .raw_wedge_bridge import model
        counts: dict[float, int] = {}
        for seam in model().seams:
            angle = round(float(seam.fold_angle_deg), 3)
            counts[angle] = counts.get(angle, 0) + 1
        _SEAM_GROUPS = tuple(sorted(counts.items()))
    return _SEAM_GROUPS


def _chapter_tokens() -> list[Token]:
    """One ``{{ch.<ref>}}`` token per chapter, resolving to its number.

    Built from the outline, so a chapter added, moved or renumbered updates
    every cross-reference to it on the next export.
    """
    from .book import BOOK

    def number_of(key: str):
        def compute() -> str:
            for chapter in BOOK.chapters:
                if chapter.key == key:
                    return str(chapter.number)
            raise ValueError(f"no chapter with ref {key!r}")
        return compute

    return [
        Token(f"ch.{chapter.key}", f'chapter number of "{chapter.title}"',
              number_of(chapter.key))
        for chapter in BOOK.chapters
    ]


def _chapter_count() -> str:
    from .book import BOOK
    return str(len(BOOK.chapters))


def _part_count() -> str:
    from .book import BOOK
    return str(len(BOOK.parts))


def _figure_count() -> str:
    from .book import BOOK
    return str(len(BOOK.figures))


_TOKENS: tuple[Token, ...] | None = None


def tokens() -> tuple[Token, ...]:
    """Every token, built once per process."""
    global _TOKENS
    if _TOKENS is None:
        _TOKENS = _build()
    return _TOKENS


def token_map() -> dict[str, Token]:
    return {token.name: token for token in tokens()}


def resolve(text: str, strict: bool = True) -> str:
    """Expand every ``{{token}}`` in a piece of manuscript.

    ``strict`` raises on an unknown token, which is what an export wants: a
    book with ``{{dome.diamter_ft}}`` printed in it is worse than one that
    refused to build. The writing desk calls this with ``strict=False`` so a
    half-typed token does not make the preview vanish.
    """
    lookup = token_map()

    def substitute(match: re.Match) -> str:
        name = match.group(1)
        token = lookup.get(name)
        if token is None:
            if strict:
                raise ValueError(
                    f"unknown token {{{{{name}}}}}. The book will not print a "
                    f"blank where a number should be. Known tokens: "
                    f"{', '.join(sorted(lookup))}")
            return f"[?{name}]"
        return token.value()

    return TOKEN_PATTERN.sub(substitute, text)


def unknown_tokens(text: str) -> tuple[str, ...]:
    """Every token in this text that does not exist, in order."""
    lookup = token_map()
    seen: list[str] = []
    for match in TOKEN_PATTERN.finditer(text):
        name = match.group(1)
        if name not in lookup and name not in seen:
            seen.append(name)
    return tuple(seen)


def used_tokens(text: str) -> tuple[str, ...]:
    """Every token this text quotes, in order, without repeats."""
    seen: list[str] = []
    for match in TOKEN_PATTERN.finditer(text):
        name = match.group(1)
        if name not in seen:
            seen.append(name)
    return tuple(seen)


def token_report() -> str:
    """Every token, its value now, and what it means."""
    lines = [f"{len(tokens())} live figures the manuscript can quote", ""]
    group = ""
    for token in tokens():
        prefix = token.name.split(".", 1)[0]
        if prefix != group:
            group = prefix
            lines.append(f"{prefix.upper()}")
        lines.append(f"  {{{{{token.name}}}}}".ljust(36)
                     + f"= {token.value():<12} {token.describe}")
    return "\n".join(lines)


def validate_tokens() -> None:
    """Every token resolves, and the outline's own tokens all exist."""
    from .book import BOOK

    all_tokens = tokens()
    assert all_tokens, "no tokens defined"

    names = [token.name for token in all_tokens]
    assert len(set(names)) == len(names), \
        sorted({n for n in names if names.count(n) > 1})

    for token in all_tokens:
        value = token.value()
        assert isinstance(value, str) and value, token.name
        assert token.describe.strip(), token.name
        # A token that resolves to a literal token is a loop.
        assert "{{" not in value, (token.name, value)

    # Every token used anywhere in the outline -- page titles, figure
    # captions, page purposes -- must exist, or the book prints "[?name]".
    outline_text = []
    for part in BOOK.parts:
        for chapter in part.chapters:
            for page in chapter.pages:
                outline_text += [page.title, page.purpose, *page.beats]
                for fig in page.figures:
                    outline_text += [fig.caption, fig.note]
    for matter in BOOK.front + BOOK.back:
        for page in matter.pages:
            outline_text += [page.title, page.purpose, *page.beats]
            for fig in page.figures:
                outline_text += [fig.caption, fig.note]
    missing = unknown_tokens("\n".join(outline_text))
    assert not missing, f"outline quotes tokens that do not exist: {missing}"

    # Resolution actually substitutes.
    sample = "a {{frame.members}}-member frame"
    assert "{{" not in resolve(sample), resolve(sample)
    assert "120" in resolve(sample), resolve(sample)

    # Strict mode refuses to print a blank.
    try:
        resolve("{{nope.nope}}", strict=True)
    except ValueError:
        pass
    else:  # pragma: no cover - the guard is the point
        raise AssertionError("strict resolve accepted an unknown token")
    assert resolve("{{nope.nope}}", strict=False) == "[?nope.nope]"

    print(f"book_tokens OK: {len(all_tokens)} tokens, all resolving; "
          f"outline quotes {len(used_tokens(chr(10).join(outline_text)))} "
          "of them")


if __name__ == "__main__":
    print(token_report())
    print()
    validate_tokens()
