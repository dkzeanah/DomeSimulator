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

import math
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


def _deck(kind: str, across_ft: float = 48.0):
    """One pad deck, taken off rather than rated. See :mod:`pad_deck`."""
    import pad_deck

    return pad_deck.deck(kind, across_ft)


def _n(value: float, places: int = 0) -> str:
    """A number set the way a book sets numbers: grouped, fixed places."""
    return f"{value:,.{places}f}"


def _flat_sizes():
    """The four diameters the flat-rate table covers, from the model."""
    from . import franken_economics as fe
    return fe.flat_rate_table()


def _solo():
    """The declared solo handling limit, and what it reaches."""
    from . import franken_economics as fe
    return fe.solo_band()


def _band_size():
    """The dome sitting exactly at the top of the handling band."""
    from . import franken_economics as fe
    return fe.DomeSize(_solo().radius_in)


def _processes():
    """The nine shop operations, in the order they happen."""
    from . import franken_economics as fe
    return fe.PROCESSES


def _process(key):
    """One of the nine operations, by key."""
    from . import franken_economics as fe
    return fe.PROCESS[key]


def _reps(index, key, places=0):
    """How many times one process repeats at one of the table diameters."""
    def value():
        size = _flat_sizes()[index]
        return _n(_process(key).repetitions(size), places)
    return value


# The worked improvement in "Nine Processes at Any Size".  The size of the
# saving and the length of the run are choices -- they are what the chapter
# asks you to imagine -- so they are declared once, here, and both the prose
# and the arithmetic read them from this pair.  Change them and the chapter
# rewrites itself rather than contradicting itself.
RIP_GAIN_FRACTION = 0.10
RIP_GAIN_BUILDS = 10


def _rip(attribute, builds=1, places=0):
    """A proportional speed-up at the rip, spent over a run of domes."""
    def value():
        gain = bm.fortnight().improvement(RIP_GAIN_FRACTION, builds)
        return _n(getattr(gain, attribute), places)
    return value


def _flat(index, attribute, places=None):
    """One cell of the flat-rate table, as text. Whole numbers stay whole."""
    def value():
        raw = getattr(_flat_sizes()[index], attribute)
        if places is None or not isinstance(raw, float):
            return str(raw)
        return _n(raw, places)
    return value

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
        # -- the flat rate ---------------------------------------------
        Token("flat.struts", "members in the frame, at every size",
              _flat(0, "struts")),
        Token("flat.triangles", "triangles in the frame, at every size",
              _flat(0, "triangles")),
        Token("flat.brackets", "brackets, at every size",
              _flat(0, "brackets")),
        Token("flat.screws", "screws, at every size", _flat(0, "screws")),
        Token("flat.processes", "distinct processes, at every size",
              _flat(0, "processes")),
        Token("flat.small_ft", "the smallest diameter here",
              _flat(0, "diameter_ft", 0)),
        Token("flat.large_ft", "the largest diameter here",
              _flat(3, "diameter_ft", 0)),
        Token("flat.small_floor", "floor at the smallest",
              _flat(0, "floor_area_sqft", 0)),
        Token("flat.large_floor", "floor at the largest",
              _flat(3, "floor_area_sqft", 0)),
        Token("flat.small_stick", "stick at the smallest",
              _flat(0, "strut_feet", 0)),
        Token("flat.large_stick", "stick at the largest",
              _flat(3, "strut_feet", 0)),
        Token("flat.mid_ft", "the middle diameter",
              _flat(2, "diameter_ft", 0)),
        Token("flat.mid_floor", "floor at the twenty foot dome",
              _flat(2, "floor_area_sqft", 0)),
        Token("flat.mid_stick", "stick at the twenty foot dome",
              _flat(2, "strut_feet", 0)),
        Token("flat.small_per_floor", "stick per square foot, smallest",
              lambda: _n(_flat_sizes()[0].strut_feet
                         / _flat_sizes()[0].floor_area_sqft, 2)),
        Token("flat.large_per_floor", "stick per square foot, largest",
              lambda: _n(_flat_sizes()[3].strut_feet
                         / _flat_sizes()[3].floor_area_sqft, 2)),
        # -- the handling band the flat rate actually lives in ----------
        Token("flat.solo_member_ft", "declared longest member one person handles",
              lambda: _n(_solo().member_ft, 0)),
        Token("flat.solo_dome_ft", "the dome that member limit reaches",
              lambda: _n(_solo().diameter_ft, 1)),
        Token("flat.solo_floor", "floor at the top of the solo band",
              lambda: _n(_solo().floor_area_sqft, 0)),
        Token("flat.solo_short_ft", "the other member at that diameter",
              lambda: _n(_solo().short_member_ft, 2)),
        Token("flat.small_long", "longest cut member at the smallest dome",
              _flat(0, "long_member_ft", 2)),
        Token("flat.band_ft", "the largest table row inside the band",
              lambda: _n(_solo().sizes_inside[-1].diameter_ft, 0)),
        Token("flat.band_long", "longest cut member at that row",
              lambda: _n(_solo().sizes_inside[-1].long_member_ft, 2)),
        Token("flat.mid_long", "longest cut member at the twenty foot dome",
              _flat(2, "long_member_ft", 2)),
        Token("flat.mid_spare_in", "inches of margin the twenty foot dome has",
              lambda: _n((_solo().member_ft
                          - _flat_sizes()[2].long_member_ft) * 12.0, 0)),
        Token("flat.large_long", "longest cut member at the largest dome",
              _flat(3, "long_member_ft", 2)),
        Token("flat.large_over_ft", "how far past the limit the largest is",
              lambda: _n(_flat_sizes()[3].long_member_ft
                         - _solo().member_ft, 2)),
        Token("flat.solo_chord", "the edge that 6 ft member actually spans",
              lambda: _n(_band_size().measurements.long_center_length
                         / 12.0, 2)),
        Token("flat.band_inside", "table rows one person can frame alone",
              lambda: str(len(_solo().sizes_inside))),
        # -- cut stock, which is not the edge network -------------------
        Token("flat.small_cut", "cut member feet in the smallest frame",
              _flat(0, "member_feet", 0)),
        Token("flat.mid_cut", "cut member feet at the twenty foot dome",
              _flat(2, "member_feet", 0)),
        Token("flat.large_cut", "cut member feet in the largest frame",
              _flat(3, "member_feet", 0)),
        Token("flat.edge_ratio", "how the edge network grows, smallest to largest",
              lambda: _n(_flat_sizes()[3].strut_feet
                         / _flat_sizes()[0].strut_feet, 2)),
        Token("flat.cut_ratio", "how the cut stock grows over the same range",
              lambda: _n(_flat_sizes()[3].member_feet
                         / _flat_sizes()[0].member_feet, 2)),
        Token("flat.small_per_cut", "cut member feet per square foot, smallest",
              lambda: _n(_flat_sizes()[0].member_feet
                         / _flat_sizes()[0].floor_area_sqft, 2)),
        Token("flat.large_per_cut", "cut member feet per square foot, largest",
              lambda: _n(_flat_sizes()[3].member_feet
                         / _flat_sizes()[3].floor_area_sqft, 2)),
        Token("flat.cut_gain", "how much further cut member reaches, largest vs smallest",
              lambda: _n((_flat_sizes()[0].member_feet
                          / _flat_sizes()[0].floor_area_sqft)
                         / (_flat_sizes()[3].member_feet
                            / _flat_sizes()[3].floor_area_sqft), 1)),
        # -- the nine operations ---------------------------------------
        Token("nine.count", "operations in the shop list",
              lambda: str(len(_processes()))),
        Token("nine.flat_count", "of the nine that repeat identically",
              lambda: str(sum(1 for s in _processes() if s.flat))),
        Token("nine.moving_count", "of the nine whose count follows size",
              lambda: str(sum(1 for s in _processes() if not s.flat))),
        Token("nine.names", "the nine, in the order they happen",
              lambda: ", ".join(s.name.lower() for s in _processes())),
        Token("nine.holes", "holes drilled, at every size",
              _reps(0, "drill")),
        Token("nine.panels", "panels raised, at every size",
              _reps(0, "raise")),
        Token("nine.trees_small", "trees felled for the smallest dome",
              _reps(0, "fell")),
        Token("nine.trees_large", "trees felled for the largest dome",
              _reps(3, "fell")),
        Token("nine.glass_small", "shell area at the smallest dome",
              _reps(0, "glass")),
        Token("nine.glass_large", "shell area at the largest dome",
              _reps(3, "glass")),
        # -- what one process is worth ----------------------------------
        #
        # The hours, afternoons and days of ripping already have tokens under
        # ``work.*``; they are not repeated here.  These are only the figures
        # that did not exist before: the per-member scale, and what a
        # proportional saving at that scale returns over a run of domes.
        Token("rip.day_share", "per cent of the fortnight spent ripping",
              lambda: _n(100.0 * bm.phase_days("ripping") / work.days, 0)),
        Token("rip.minutes_per_strut", "minutes one member spends at the rip",
              lambda: _n(work.minutes_per_strut, 0)),
        Token("rip.gain_pct", "the improvement the worked example assumes",
              lambda: _n(RIP_GAIN_FRACTION * 100.0, 0)),
        Token("rip.builds", "domes the worked example spends it over",
              lambda: str(RIP_GAIN_BUILDS)),
        Token("rip.gain_seconds", "seconds per member that improvement buys",
              _rip("seconds_per_strut")),
        Token("rip.gain_hours", "hours it returns on one build",
              _rip("hours_per_build", places=1)),
        Token("rip.run_hours", "hours it returns over the whole run",
              _rip("hours_total", RIP_GAIN_BUILDS)),
        Token("rip.run_afternoons", "afternoons that is",
              _rip("afternoons_total", RIP_GAIN_BUILDS)),
        Token("rip.run_stages", "whole ripping stages that is",
              _rip("rip_stages", RIP_GAIN_BUILDS)),
        # -- what an hour at the log is worth ---------------------------
        Token("log.member_area", "cross-section of one strut, square inches",
              lambda: _n(plan.member_area_in2, 2)),
        Token("log.nominal_area", "cross-section a 2x4 is named for",
              lambda: _n(plan.member_area_in2
                         / plan.equivalent_two_by_fours, 2)),
        Token("log.dressed_area", "cross-section a 2x4 actually has",
              lambda: _n(plan.member_area_in2
                         / plan.equivalent_dressed_two_by_fours, 2)),
        Token("log.equiv_nominal", "2x4s one strut replaces, at the named size",
              lambda: _n(plan.equivalent_two_by_fours, 2)),
        Token("log.equiv_dressed", "2x4s one strut replaces, at the real size",
              lambda: _n(plan.equivalent_dressed_two_by_fours, 2)),
        Token("log.section_price", "shelf price of one strut-length of 2x4",
              lambda: _n(work.price_per_board_section_usd, 2)),
        Token("log.value_nominal", "one strut valued against the named 2x4",
              lambda: _n(work.substitute_value_usd(
                  plan.equivalent_two_by_fours), 2)),
        Token("log.value_dressed", "one strut valued against the real 2x4",
              lambda: _n(work.substitute_value_usd(
                  plan.equivalent_dressed_two_by_fours), 2)),
        Token("log.rate_nominal", "hourly rate that implies, named size",
              lambda: _n(work.hourly_rate_usd(
                  plan.equivalent_two_by_fours), 2)),
        Token("log.rate_dressed", "hourly rate that implies, real size",
              lambda: _n(work.hourly_rate_usd(
                  plan.equivalent_dressed_two_by_fours), 2)),
        Token("log.nominal_gap_pct",
              "per cent the named-size comparison understates the rate by",
              lambda: _n(100.0 * (1.0 - plan.equivalent_two_by_fours
                                  / plan.equivalent_dressed_two_by_fours), 0)),
        Token("log.frame_dressed", "the whole frame at the honest rate",
              lambda: _n(work.substitute_value_usd(
                  plan.equivalent_dressed_two_by_fours) * bm.MEMBERS_IN_FRAME,
                  0)),
        Token("log.brief_strut", "what this project's brief put a strut at",
              lambda: _n(bm.declared("brief_strut_value_usd"), 2)),
        Token("log.brief_rate", "the hourly rate that brief implies",
              lambda: _n(bm.declared("brief_strut_value_usd")
                         * work.struts_per_hour, 2)),
        Token("log.brief_over", "how many times the honest rate the brief was",
              lambda: _n(bm.declared("brief_strut_value_usd")
                         * work.struts_per_hour
                         / work.hourly_rate_usd(
                             plan.equivalent_dressed_two_by_fours), 1)),
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
        *_skin_tokens(),
        *_calorie_tokens(),
        *_domology_tokens(),
        *_part3_tokens(),

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


def book_floor_sqft() -> float:
    """The floor of *this book's* dome, which is the one two trees make.

    :mod:`dome_advantage` defaults to ``dome_costing.FLOOR_SQFT``, a round
    314 chosen for a campaign video.  The book's dome is the one the first
    chapter cut out of two pines, and it is 365.  Quoting the video's floor
    in a book that has said 365 for fifty chapters would be exactly the
    drift tokens exist to stop, so every ``skin.*`` figure and the envelope
    plots all call this.
    """
    return math.pi * (bm.tree_first().radius_in / 12.0) ** 2


def _skin_tokens() -> list[Token]:
    """Envelope against an equal-floor box, from :mod:`dome_advantage`.

    ``skin.*`` rather than ``dome.*`` because the subject is the surface,
    and because half of these tokens exist to take the headline apart rather
    than to state it.  The crossovers, the standing-room deduction and the
    per-cubic-foot restatement sit here beside the number they qualify, so a
    chapter cannot quote the good one without the awkward ones being a line
    away in the writing desk.
    """
    from . import dome_advantage as adv
    from . import dome_costing as dc

    def dome(area: float | None = None):
        return adv.dome_envelope(book_floor_sqft() if area is None else area)

    def box(area: float | None = None):
        return adv.box_envelope(book_floor_sqft() if area is None else area)

    def saving(area: float, places: int = 1):
        return lambda: _n(adv.envelope_saving(area), places)

    def claim(index: int):
        """One of the four headline margins, by its place in ``advantages()``."""
        return lambda: _n(adv.advantages(book_floor_sqft())[index].percent_better, 1)

    def fact(key: str, places: int = 2):
        return lambda: _n(adv.FACT[key], places)

    return [
        # -- the two buildings being compared ----------------------------
        Token("skin.floor", "floor area both buildings have, sq ft",
              lambda: _n(book_floor_sqft())),
        Token("skin.dome_env", "the dome's exterior surface, sq ft",
              lambda: _n(dome().envelope_sqft)),
        Token("skin.box_env", "the box's exterior surface, sq ft",
              lambda: _n(box().envelope_sqft)),
        Token("skin.saved_sqft", "exterior surface the dome does not have, sq ft",
              lambda: _n(box().envelope_sqft - dome().envelope_sqft)),
        Token("skin.saving_pct", "percent less surface, at the reference floor",
              saving(book_floor_sqft())),
        Token("skin.dome_ht", "the dome's height, ft -- which is its radius",
              lambda: _n(adv.dome_radius_ft(book_floor_sqft()), 1)),
        Token("skin.box_side", "the box's side, ft",
              lambda: _n(math.sqrt(book_floor_sqft()), 1)),
        Token("skin.box_ridge", "the box's ridge height, ft",
              lambda: _n(adv.FACT["wall_height_ft"] + 0.5
                         * math.sqrt(book_floor_sqft()) * adv.FACT["gable_pitch"], 1)),
        Token("skin.wall_ht", "the box's wall height, ft", fact("wall_height_ft", 0)),

        # -- what the saved surface buys, four ways ----------------------
        Token("skin.dome_sheets", "sheets of 4x8 to clad the dome",
              lambda: _n(dome().envelope_sqft / dc.SQFT_PER_OSB)),
        Token("skin.box_sheets", "sheets of 4x8 to clad the box",
              lambda: _n(box().envelope_sqft / dc.SQFT_PER_OSB)),
        Token("skin.saved_sheets", "sheets the dome does not buy",
              lambda: _n((box().envelope_sqft - dome().envelope_sqft)
                         / dc.SQFT_PER_OSB)),
        Token("skin.dome_btu_f", "the dome's envelope loss, BTU/hr/F",
              lambda: _n(dome().heat_loss_btu_hr_f(), 1)),
        Token("skin.box_btu_f", "the box's envelope loss, BTU/hr/F",
              lambda: _n(box().heat_loss_btu_hr_f(), 1)),
        Token("skin.dome_mbtu", "the dome's seasonal envelope loss, million BTU",
              lambda: _n(dome().seasonal_btu() / 1e6, 1)),
        Token("skin.box_mbtu", "the box's seasonal envelope loss, million BTU",
              lambda: _n(box().seasonal_btu() / 1e6, 1)),
        Token("skin.heat_pct", "percent less heat through the envelope", claim(2)),
        Token("skin.wind_pct", "percent less drag on the shape", claim(3)),
        Token("skin.cd_dome", "drag coefficient, hemisphere", fact("cd_hemisphere")),
        Token("skin.cd_box", "drag coefficient, cube", fact("cd_cube")),
        Token("skin.wall_u", "assembly U-value both buildings are given",
              fact("wall_u", 3)),
        Token("skin.hdd", "heating degree days the season assumes",
              fact("heating_degree_days", 0)),

        # -- the restatement: volume, and surface per cubic foot ---------
        Token("skin.dome_vol", "the dome's enclosed volume, cu ft",
              lambda: _n(dome().volume_cuft)),
        Token("skin.box_vol", "the box's enclosed volume, cu ft",
              lambda: _n(box().volume_cuft)),
        Token("skin.vol_deficit_pct", "percent less air the dome encloses",
              lambda: _pct(1.0 - dome().volume_cuft / box().volume_cuft, 1)),
        Token("skin.per_cuft_pct", "percent less surface per cubic foot enclosed",
              claim(1)),
        Token("skin.vol_cross", "floor where the dome starts enclosing more, sq ft",
              lambda: _n(adv.volume_crossover_sqft())),

        # -- the size dependence, including where it reverses ------------
        Token("skin.sweep_n", "how many sizes the sweep compares",
              lambda: _n(len(adv.SWEEP_FLOORS))),
        Token("skin.sweep_lo", "smallest floor in the sweep, sq ft",
              lambda: _n(min(adv.SWEEP_FLOORS))),
        Token("skin.sweep_hi", "largest floor in the sweep, sq ft",
              lambda: _n(max(adv.SWEEP_FLOORS))),
        Token("skin.save_80", "percent less surface at 80 sq ft", saving(80.0)),
        Token("skin.save_707", "percent less surface at 707 sq ft", saving(707.0)),
        Token("skin.save_vol_cross",
              "percent less surface where the volumes cross",
              lambda: _n(adv.envelope_saving(adv.volume_crossover_sqft()), 1)),
        Token("skin.save_2000", "percent less surface at 2,000 sq ft", saving(2000.0)),
        Token("skin.env_cross", "floor where the box takes less skin, sq ft",
              lambda: _n(adv.envelope_crossover_sqft())),
        Token("skin.env_cross_ht", "how tall the dome stands at that crossover, ft",
              lambda: _n(adv.dome_radius_ft(adv.envelope_crossover_sqft()))),

        # -- the deduction that equal floor area hides -------------------
        Token("skin.head_ft", "height this comparison calls standing room, ft",
              fact("headroom_ft", 0)),
        Token("skin.stand_sqft", "the dome's floor with headroom over it, sq ft",
              lambda: _n(adv.standing_sqft(book_floor_sqft())[0])),
        Token("skin.stand_pct", "percent of the dome's floor you can stand on",
              lambda: _pct(adv.standing_sqft(book_floor_sqft())[0] / book_floor_sqft(), 1)),
        Token("skin.stand_lost", "dome floor with no headroom over it, sq ft",
              lambda: _n(book_floor_sqft() - adv.standing_sqft(book_floor_sqft())[0])),
        Token("skin.stand_floor",
              "dome floor needed to match the box's standing room, sq ft",
              lambda: _n(adv.floor_for_standing(book_floor_sqft()))),
        Token("skin.honest_env", "that bigger dome's surface, sq ft",
              lambda: _n(adv.equal_standing_advantage(book_floor_sqft()).dome)),
        Token("skin.honest_pct", "percent less surface at equal standing room",
              lambda: _n(adv.equal_standing_advantage(book_floor_sqft()).percent_better, 1)),
    ]


CALORIE_SERIAL = 1
CALORIE_CREW = 2
"""Which build the metabolic ledger costs, and with how many people.

``energetics.home_spec`` picks a product line from a seeded generator, so the
serial pins *which* dome got costed; leaving it to chance would let the
chapter's numbers move between exports.  The crew of two is what that model
was written for, and the chapter says so rather than quietly presenting a
two-person shift as the solo fortnight."""


def _calorie_tokens() -> list[Token]:
    """The metabolic ledger of one build, from :mod:`energetics`.

    Note the prefix.  ``fuel.*`` is already the chainsaw's petrol; this is
    the *other* fuel, the one the body runs on, and the two must never end
    up sharing a name in a book that puts them three chapters apart.

    Costing a build walks 1,300-odd elements through seven motions each, so
    it is slow the first time and cached after -- hence the module-level
    lookup rather than a value captured when this list is built.
    """
    from . import energetics as en

    def build():
        return en.build_energy(CALORIE_SERIAL, CALORIE_CREW)

    def motion_kcal(name: str, places: int = 0):
        return lambda: _n(build().by_motion()[name], places)

    def motion_fuel_pct(name: str, places: int = 1):
        return lambda: _pct(build().by_motion()[name]
                            / build().kcal_per_worker, places)

    def motion_time_pct(name: str, places: int = 1):
        return lambda: _pct(build().seconds_by_motion()[name]
                            / build().seconds_per_worker, places)

    def motion_hours(name: str, places: int = 0):
        return lambda: _n(build().seconds_by_motion()[name] / 3600.0, places)

    def limb_pct(group: str, places: int = 1):
        def value() -> str:
            limbs = build().by_limb()
            return _pct(limbs[group] / sum(limbs.values()), places)
        return value

    def food(index: int, places: int = 0):
        return lambda: _n(build().food_equivalent()[index][1], places)

    def top_stage():
        return max(build().by_stage().items(), key=lambda kv: kv[1]["kcal"])

    def _skin_ratio(field: str) -> float:
        return build().skin_versus_frame(field)

    return [
        # -- what was costed, and with whom ------------------------------
        Token("cal.product", "the product the metabolic ledger costed",
              lambda: en.home_spec(CALORIE_SERIAL).name),
        Token("cal.radius_m", "that product's radius, metres",
              lambda: f"{en.home_spec(CALORIE_SERIAL).radius:.2f}"),
        Token("cal.stations", "stations on the line that builds it",
              lambda: str(len(en.home_spec(CALORIE_SERIAL).stages))),
        Token("cal.crew", "people the ledger assumes", lambda: str(CALORIE_CREW)),
        Token("cal.body_kg", "the modelled body, kilograms",
              lambda: _n(en.BODY_MASS_KG, 0)),
        Token("cal.elements", "parts the ledger costs one at a time",
              lambda: _n(len(build().elements), 0)),
        Token("cal.material_kg", "material in the finished building, kg",
              lambda: _n(build().total_mass_kg, 0)),
        Token("cal.lifted_kg", "mass one worker personally raises, kg",
              lambda: _n(build().lifted_mass_kg, 0)),
        Token("cal.team_lift_kg", "above this, two people take the load",
              lambda: _n(en.TWO_PERSON_LIFT_KG, 0)),

        # -- the shift ---------------------------------------------------
        Token("cal.motions", "motions every part is broken into",
              lambda: str(len(en.element_motions(
                  build().elements[0].element, crew=CALORIE_CREW)))),
        Token("cal.hours", "hours of work per person for the whole build",
              lambda: _n(build().hours_per_worker, 0)),
        Token("cal.shift_hours", "hours this model calls a working day",
              lambda: _n(en.SHIFT_HOURS, 0)),
        Token("cal.shifts", "working days that comes to",
              lambda: _n(build().shifts, 1)),
        Token("cal.per_worker", "food energy one worker spends, kcal",
              lambda: _n(build().kcal_per_worker, 0)),
        Token("cal.crew_total", "food energy for the whole crew, kcal",
              lambda: _n(build().kcal_crew, 0)),
        Token("cal.per_shift", "food energy one working day costs, kcal",
              lambda: _n(build().kcal_per_shift, 0)),
        Token("cal.watts", "mean working rate across the build, watts",
              lambda: _n(build().mean_watts, 0)),
        Token("cal.mets", "that rate in METs",
              lambda: f"{build().mean_met:.2f}"),
        Token("cal.watt_bound", "sustainable whole-shift rate, watts",
              lambda: _n(en.SUSTAINABLE_SHIFT_WATTS, 0)),
        Token("cal.rmr_kcal_day", "the same body at rest, kcal a day",
              lambda: _n(en.resting_metabolic_watts() * 86400.0
                         * en.KCAL_PER_JOULE, 0)),
        Token("cal.rest_pct", "share of the timeline that is recovery",
              lambda: _pct(build().rest_fraction, 1)),
        Token("cal.rest_hours", "hours of that recovery",
              lambda: _n(build().rest_seconds / 3600.0, 0)),

        # -- the fastening surprise --------------------------------------
        Token("cal.mech_mj", "mechanical work actually done, megajoules",
              lambda: f"{build().mechanical_joules / 1e6:.3f}"),
        Token("cal.mech_kcal", "that work in kcal",
              lambda: _n(build().mechanical_kcal, 0)),
        Token("cal.mech_pct", "what share of the food became height",
              lambda: _pct(build().mechanical_fraction, 1)),
        Token("cal.fuel_per_lift", "kcal burned per kcal that went upward",
              lambda: _n(build().fuel_per_lifting_kcal, 0)),
        Token("cal.muscle_pct", "the most muscle can convert, per cent",
              lambda: _pct(en.CONCENTRIC_EFFICIENCY, 0)),
        Token("cal.fasten_kcal", "food energy spent fastening, kcal",
              motion_kcal("fasten")),
        Token("cal.fasten_pct", "fastening's share of the fuel",
              motion_fuel_pct("fasten")),
        Token("cal.fasten_time_pct", "fastening's share of the clock",
              motion_time_pct("fasten")),
        Token("cal.fasten_hours", "hours spent fastening",
              motion_hours("fasten")),
        Token("cal.fasten_gap_pct", "points by which fastening's fuel share "
                                    "exceeds its time share",
              lambda: _pct(build().by_motion()["fasten"]
                           / build().kcal_per_worker
                           - build().seconds_by_motion()["fasten"]
                           / build().seconds_per_worker, 0)),
        Token("cal.lift_kcal", "food energy spent lifting, kcal",
              motion_kcal("lift")),
        Token("cal.lift_pct", "lifting's share of the fuel",
              motion_fuel_pct("lift")),
        Token("cal.lift_eff_pct", "how much of the lift's fuel became height",
              lambda: _pct(build().motion_efficiency()["lift"], 1)),
        Token("cal.carry_pct", "carrying's share of the fuel",
              motion_fuel_pct("carry")),
        Token("cal.handling_pct",
              "lifting, carrying and walking together, share of the fuel",
              lambda: _pct(sum(build().by_motion()[name]
                               for name in ("lift", "carry", "walk_out"))
                           / build().kcal_per_worker, 1)),
        Token("cal.pause_pct", "the recovery allowance's share of the fuel",
              motion_fuel_pct("pause")),

        # -- where the lifting lands -------------------------------------
        Token("cal.trunk_pct", "share of the lifting work done by the trunk",
              limb_pct("trunk")),
        Token("cal.arms_pct", "share done by the arms", limb_pct("arms")),
        Token("cal.legs_pct", "share done by the legs", limb_pct("legs")),

        # -- stations and food -------------------------------------------
        Token("cal.top_stage", "the station that costs the most fuel",
              lambda: top_stage()[0]),
        Token("cal.top_stage_kcal", "what that station costs, kcal",
              lambda: _n(top_stage()[1]["kcal"], 0)),
        Token("cal.top_stage_parts", "how many parts pass through it",
              lambda: _n(top_stage()[1]["elements"], 0)),
        Token("cal.skin_fuel_ratio",
              "the layers over the frame, as a multiple of the frame's fuel",
              lambda: f"{_skin_ratio('kcal'):.1f}"),
        Token("cal.skin_mass_ratio",
              "the same layers as a multiple of the frame's mass",
              lambda: f"{_skin_ratio('kg'):.1f}"),
        Token("cal.bread", "the crew's total in slices of bread", food(0)),
        Token("cal.bananas", "the crew's total in bananas", food(1)),
        Token("cal.diet_days", "the crew's total in days of a normal diet",
              food(2)),
        Token("cal.constants", "published constants this model takes on trust",
              lambda: str(len(en.EXTERNAL_CONSTANTS))),
    ]


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


# ----------------------------------------------------------------------
# Part 2 of the book: Why It Scales (chapters 58-68)
# ----------------------------------------------------------------------
#
# These tokens feed the second part of the book. Every value comes from the
# same modules the park films teach from -- ``dome_performance`` for the
# pony wall, the brim and the running costs, ``park_model`` for the pad and
# its economics -- so a chapter and its film cannot drift apart.
#
# The few numbers that are choices rather than derived facts are declared
# here, next to their reason, the way ``RIP_GAIN_FRACTION`` is above.

BRIM_FT = 1.5
"""The brim overhang the water chapter's worked example uses (18 inches).

Same value the ten-points list and the park film quote, so all three agree."""

TANK_GALLONS = 1000.0
TANK_USE_GAL_DAY = 50.0
"""The tank the water chapter sizes: a 1,000-gallon tank against a two-person
household's 50 gallons a day. Both are the chapter's declared example, not a
claim about what a reader needs."""

RETROFIT_MULTIPLIER = 2.0
"""How much more the same service upgrade costs retrofitted under a finished
pad than laid in while it is being built.

An estimate, declared rather than derived: cutting a finished deck or slab,
re-trenching and patching roughly doubles the job. The chapter names it as
such rather than presenting it as a measured price."""


def _dp():
    """The performance module, imported lazily so the package stays light."""
    from . import dome_performance as dp
    return dp


def _pm():
    """The park model, which sits beside the package at the repository root."""
    import park_model as pm
    return pm


def _rung(index: int, attr: str, places: int = 0):
    """One cell of the pony-wall ladder."""
    def value() -> str:
        rung = _dp().pony_wall_ladder()[index]
        return _n(getattr(rung, attr), places)
    return value


def _rung_gain(index: int):
    """Usable floor a rung buys over no wall at all."""
    def value() -> str:
        ladder = _dp().pony_wall_ladder()
        return _n(ladder[index].gain_over(ladder[0]))
    return value


def _rung_rate(index: int):
    """Dollars per square foot a rung buys its gain at."""
    def value() -> str:
        ladder = _dp().pony_wall_ladder()
        return _n(ladder[index].cost_per_gained_sqft(ladder[0]), 1)
    return value


def _step(index: int, attr: str, places: int = 0):
    """One rung of the shell ladder, for the flagship dome."""
    def value() -> str:
        return _n(getattr(_pm().shell_ladder(_pm().FLAGSHIP_DOME)[index], attr),
                  places)
    return value


def _bin(index: int, key: str, places: int = 0):
    """One cell of the hardware-invariance table (small, mid, large)."""
    def value() -> str:
        return _n(_pm().hardware_invariance()[index][key], places)
    return value


def _pad_year(which: str, key: str, places: int = 0):
    """One line of a pad's first-year ledger."""
    def value() -> str:
        pad = _pm().standard_pad() if which == "standard" else _pm().basic_pad()
        return _n(pad.year()[key], places)
    return value


def _layout(index: int, attr: str, places: int = 0):
    """One figure from the three solar cladding layouts."""
    def value() -> str:
        return _n(getattr(_pm().solar_layouts()[index], attr), places)
    return value


def _part3_tokens() -> list[Token]:
    """The live figures behind chapters 58-68 (Why It Scales)."""
    from . import dome_performance as dp
    import park_model as pm

    ladder = pm.shell_ladder(pm.FLAGSHIP_DOME)
    options = pm.housing_options(pm.FLAGSHIP_DOME)
    dome_option = options[-1]
    shares = pm.foundation_share()
    flagship = pm.on_pad(pm.FLAGSHIP_DOME)
    solar_one = pm.solar_layouts()[0]
    solar_all = pm.solar_layouts()[2]

    # The retrofit worked example: the three service lines a pad is built
    # with, priced at build time and again as a retrofit.
    service_lines = (pm.declared("electric_pedestal_usd")
                     + pm.declared("water_connection_usd")
                     + pm.declared("site_infrastructure_usd_per_pad"))

    out: list[Token] = []

    # ---- 58: the pony wall ---------------------------------------------
    out += [
        Token("pony.floor", "the reference floor the ladder is drawn on, sq ft",
              lambda: _n(dp.FLOOR_SQFT)),
        Token("pony.headroom", "head height the ceiling must clear, ft",
              lambda: _n(dp.FACT["headroom_ft"], 1)),
        Token("pony.radius_ft", "the reference dome's radius, ft",
              lambda: _n(dp.pony_wall_ladder()[0].radius_ft)),
        Token("pony.wall_rate", "declared cost of a foot of stem wall, per sq ft",
              lambda: _n(dp.FACT["pony_wall_cost_sqft"], 2)),
        Token("pony.usable_0", "usable floor with no wall at all, sq ft",
              _rung(0, "usable_sqft")),
        Token("pony.pct_0", "share of the floor that is usable, no wall",
              lambda: _pct(dp.pony_wall_ladder()[0].usable_fraction, 0)),
        Token("pony.usable_2", "usable floor on a 2 ft wall, sq ft",
              _rung(1, "usable_sqft")),
        Token("pony.pct_2", "share usable on a 2 ft wall", 
              lambda: _pct(dp.pony_wall_ladder()[1].usable_fraction, 0)),
        Token("pony.cost_2", "what a 2 ft wall costs, dollars", _rung(1, "cost")),
        Token("pony.gain_2", "floor the 2 ft wall buys back, sq ft",
              _rung_gain(1)),
        Token("pony.rate_2", "dollars per sq ft the 2 ft wall buys at",
              _rung_rate(1)),
        Token("pony.usable_3", "usable floor on a 3 ft wall, sq ft",
              _rung(2, "usable_sqft")),
        Token("pony.pct_3", "share usable on a 3 ft wall",
              lambda: _pct(dp.pony_wall_ladder()[2].usable_fraction, 0)),
        Token("pony.cost_3", "what a 3 ft wall costs, dollars", _rung(2, "cost")),
        Token("pony.wall_3", "square feet of wall the 3 ft rung is, sq ft",
              _rung(2, "wall_sqft")),
        Token("pony.gain_3", "floor the 3 ft wall buys back, sq ft",
              _rung_gain(2)),
        Token("pony.rate_3", "dollars per sq ft the 3 ft wall buys at",
              _rung_rate(2)),
        Token("pony.gain_pct_3", "per cent more usable floor than no wall",
              lambda: _pct(dp.pony_wall_ladder()[2].gain_over(
                  dp.pony_wall_ladder()[0]) / dp.pony_wall_ladder()[0].usable_sqft, 0)),
        Token("pony.usable_4", "usable floor on a 4 ft wall, sq ft",
              _rung(3, "usable_sqft")),
        Token("pony.pct_4", "share usable on a 4 ft wall",
              lambda: _pct(dp.pony_wall_ladder()[3].usable_fraction, 0)),
        Token("pony.cost_4", "what a 4 ft wall costs, dollars", _rung(3, "cost")),
        Token("pony.gain_4", "floor the 4 ft wall buys back, sq ft",
              _rung_gain(3)),
        Token("pony.rate_4", "dollars per sq ft the 4 ft wall buys at",
              _rung_rate(3)),
    ]

    # ---- 59: the brim is a gutter --------------------------------------
    water = dp.WaterCatch(BRIM_FT)
    out += [
        Token("brim.floor", "the reference floor the catch is computed on, sq ft",
              lambda: _n(dp.FLOOR_SQFT)),
        Token("brim.overhang_in", "brim overhang the worked example uses, inches",
              lambda: _n(BRIM_FT * 12.0)),
        Token("brim.overhang_ft", "the same overhang, feet",
              lambda: _n(BRIM_FT, 1)),
        Token("brim.rim_ft", "plan radius where the hat stops, ft",
              lambda: _n(water.rim_radius_ft, 1)),
        Token("brim.catch_ft", "catchment radius with the brim on, ft",
              lambda: _n(water.catch_radius_ft, 1)),
        Token("brim.catch_sqft", "catchment area, plan view, sq ft",
              lambda: _n(water.catchment_sqft)),
        Token("brim.rain_in", "annual rainfall the catch assumes, inches",
              lambda: _n(dp.FACT["rainfall_in_year"], 0)),
        Token("brim.gal_per_in", "gallons a square foot collects per inch of rain",
              lambda: _n(dp.FACT["gallons_per_sqft_inch"], 3)),
        Token("brim.runoff_pct", "share of rain that becomes runoff, per cent",
              lambda: _pct(dp.FACT["runoff_coefficient"], 0)),
        Token("brim.gallons_yr", "gallons the brim collects in a year",
              lambda: _n(water.gallons_year)),
        Token("brim.gallons_day", "the same catch, per day",
              lambda: _n(water.gallons_day, 1)),
        Token("brim.value_yr", "what that water is worth at utility rates, dollars",
              lambda: _n(water.value_year, 0)),
        Token("brim.tank_gal", "the tank the worked example sizes, gallons",
              lambda: _n(TANK_GALLONS)),
        Token("brim.use_gal_day", "daily use the tank is sized against, gallons",
              lambda: _n(TANK_USE_GAL_DAY)),
        Token("brim.tank_days", "days a full tank covers at that use",
              lambda: _n(water.tank_days(TANK_GALLONS, TANK_USE_GAL_DAY))),
    ]

    # ---- 60: the shell ladder ------------------------------------------
    out += [
        Token("ladder.dome", "the dome the ladder is computed on",
              lambda: pm.FLAGSHIP_DOME),
        Token("ladder.diameter_ft", "that dome's diameter, ft",
              lambda: _n(next(d.dome_diameter_ft for d in pm.dome_catalogue()
                              if d.name == pm.FLAGSHIP_DOME), 1)),
        Token("ladder.floor", "that dome's floor, sq ft",
              lambda: _n(next(d.floor_sqft for d in pm.dome_catalogue()
                              if d.name == pm.FLAGSHIP_DOME))),
        Token("ladder.layers", "layers the ladder runs to",
              lambda: _n(len(ladder) - 1)),
        Token("ladder.r0", "R-value of the bare shell",
              lambda: _n(ladder[0].r_value, 1)),
        Token("ladder.r1", "R-value with one layer",
              lambda: _n(ladder[1].r_value, 1)),
        Token("ladder.r2", "R-value with two layers",
              lambda: _n(ladder[2].r_value, 1)),
        Token("ladder.r3", "R-value with three layers",
              lambda: _n(ladder[3].r_value, 1)),
        Token("ladder.r7", "R-value with every layer on",
              lambda: _n(ladder[-1].r_value, 1)),
        Token("ladder.per_layer_r", "declared R-value each quilted layer adds",
              lambda: _n(pm.declared("quilt_r_per_layer"), 1)),
        Token("ladder.layer_sqft", "declared cost of one layer, per sq ft",
              lambda: _n(pm.declared("quilt_usd_per_sqft_layer"), 1)),
        Token("ladder.heat0", "heating bill of the bare shell, dollars a year",
              _step(0, "heating_usd_per_year")),
        Token("ladder.heat1", "heating bill with one layer, dollars a year",
              _step(1, "heating_usd_per_year")),
        Token("ladder.heat2", "heating bill with two layers, dollars a year",
              _step(2, "heating_usd_per_year")),
        Token("ladder.heat3", "heating bill with three layers, dollars a year",
              _step(3, "heating_usd_per_year")),
        Token("ladder.heat7", "heating bill with every layer on, dollars a year",
              _step(7, "heating_usd_per_year")),
        Token("ladder.drop_pct", "per cent of the heating bill the layers remove",
              lambda: _pct(1.0 - ladder[-1].heating_usd_per_year
                           / ladder[0].heating_usd_per_year, 0)),
        Token("ladder.layer_cost", "what one layer costs, dollars",
              _step(1, "marginal_cost")),
        Token("ladder.add1", "cumulative cost after one layer, dollars",
              _step(1, "added_cost")),
        Token("ladder.add2", "cumulative cost after two layers, dollars",
              _step(2, "added_cost")),
        Token("ladder.add3", "cumulative cost after three layers, dollars",
              _step(3, "added_cost")),
        Token("ladder.add7", "cumulative cost of all seven layers, dollars",
              _step(7, "added_cost")),
        Token("ladder.save1", "first layer's yearly saving, dollars",
              _step(1, "marginal_saving")),
        Token("ladder.save2", "second layer's yearly saving, dollars",
              _step(2, "marginal_saving")),
        Token("ladder.save3", "third layer's yearly saving, dollars",
              _step(3, "marginal_saving")),
        Token("ladder.save7", "seventh layer's yearly saving, dollars",
              _step(7, "marginal_saving")),
        Token("ladder.payback1", "months for the first layer to pay for itself",
              lambda: _n(ladder[1].marginal_cost
                         / ladder[1].marginal_saving * 12.0, 0)),
        Token("ladder.payback7", "years for the seventh layer to pay for itself",
              lambda: _n(ladder[7].marginal_cost
                         / ladder[7].marginal_saving, 1)),
    ]

    # ---- 61: one hardware set, three sizes -----------------------------
    bins = pm.hardware_invariance()
    out += [
        Token("bin.design", "the shipped design the table is drawn on",
              lambda: str(bins[0]["design"])),
        Token("bin.small_ft", "smallest diameter in the table, ft",
              _bin(0, "diameter_ft", 1)),
        Token("bin.mid_ft", "middle diameter in the table, ft",
              _bin(1, "diameter_ft", 1)),
        Token("bin.large_ft", "largest diameter in the table, ft",
              _bin(2, "diameter_ft", 1)),
        Token("bin.small_floor", "floor at the smallest, sq ft",
              _bin(0, "floor_sqft")),
        Token("bin.mid_floor", "floor at the middle, sq ft",
              _bin(1, "floor_sqft")),
        Token("bin.large_floor", "floor at the largest, sq ft",
              _bin(2, "floor_sqft")),
        Token("bin.floor_gain", "how many times the floor grows, small to large",
              lambda: _n(bins[2]["floor_sqft"] / bins[0]["floor_sqft"], 1)),
        Token("bin.struts", "struts in the frame, at every size",
              _bin(0, "struts")),
        Token("bin.hubs", "hubs in the frame, at every size", _bin(0, "hubs")),
        Token("bin.panels", "panels in the frame, at every size",
              _bin(0, "panels")),
        Token("bin.hub_cost", "the hub bill, dollars, identical at every size",
              _bin(0, "hub_cost")),
        Token("bin.frame_small", "frame cost at the smallest, dollars",
              _bin(0, "frame_cost")),
        Token("bin.frame_mid", "frame cost at the middle, dollars",
              _bin(1, "frame_cost")),
        Token("bin.frame_large", "frame cost at the largest, dollars",
              _bin(2, "frame_cost")),
        Token("bin.panel_small", "panel cost at the smallest, dollars",
              _bin(0, "panel_cost")),
        Token("bin.panel_mid", "panel cost at the middle, dollars",
              _bin(1, "panel_cost")),
        Token("bin.panel_large", "panel cost at the largest, dollars",
              _bin(2, "panel_cost")),
        Token("bin.foundation_small", "foundation at the smallest, dollars",
              _bin(0, "foundation_cost")),
        Token("bin.foundation_mid", "foundation at the middle, dollars",
              _bin(1, "foundation_cost")),
        Token("bin.foundation_large", "foundation at the largest, dollars",
              _bin(2, "foundation_cost")),
        Token("bin.total_small", "whole build at the smallest, dollars",
              _bin(0, "total_cost")),
        Token("bin.total_mid", "whole build at the middle, dollars",
              _bin(1, "total_cost")),
        Token("bin.total_large", "whole build at the largest, dollars",
              _bin(2, "total_cost")),
    ]

    # ---- 62: buy for the next two steps --------------------------------
    apartment = options[2]
    out += [
        Token("growth.crossover", "month the dome becomes the cheapest roof",
              lambda: _n(pm.crossover_months(pm.FLAGSHIP_DOME))),
        Token("growth.hotel_mo", "a hotel room, a month, dollars",
              lambda: _n(options[0].monthly)),
        Token("growth.short_mo", "a short let, a month, dollars",
              lambda: _n(options[1].monthly)),
        Token("growth.apartment_mo", "a leased apartment, a month, dollars",
              lambda: _n(options[2].monthly, 0)),
        Token("growth.dome_mo", "the dome on a pad, a month, dollars",
              lambda: _n(options[3].monthly)),
        Token("growth.apartment_entry", "moving into the apartment, dollars",
              lambda: _n(apartment.entry)),
        Token("growth.deposit", "the part of that which comes back, dollars",
              lambda: _n(apartment.recoverable)),
        Token("growth.break_fee", "leaving the lease early, dollars",
              lambda: _n(apartment.early_exit_months)),
        Token("growth.lease_months", "the lease you sign, months",
              lambda: _n(apartment.lease_months)),
        Token("growth.dome_entry", "moving onto a pad, dollars",
              lambda: _n(dome_option.entry)),
        Token("growth.dome_asset", "of that, the dome you keep, dollars",
              lambda: _n(dome_option.asset_cost)),
        Token("growth.transport", "moving the dome between pads, dollars",
              lambda: _n(pm.declared("dome_transport_usd"))),
        Token("growth.pad_step", "the step pad sizes come in, ft",
              lambda: _n(pm.PAD_STEP_FT)),
        Token("growth.setup_fast", "days to put the dome up, quick end",
              lambda: _n(pm.declared("setup_days_fast"))),
        Token("growth.setup_slow", "days at the slow end, large or layered",
              lambda: _n(pm.declared("setup_days_slow"))),
        Token("growth.retrofit_mult", "declared cost multiple for retrofitting",
              lambda: _n(RETROFIT_MULTIPLIER, 1)),
        Token("growth.service_low", "service upgrade laid in at build time, dollars",
              lambda: _n(service_lines)),
        Token("growth.service_high", "the same upgrade retrofitted, dollars",
              lambda: _n(service_lines * RETROFIT_MULTIPLIER)),
        Token("growth.service_delta", "what not leaving room costs, dollars",
              lambda: _n(service_lines * (RETROFIT_MULTIPLIER - 1.0))),
    ]

    # ---- 63: the ground is what you cannot take with you ----------------
    ordered = sorted(shares, key=lambda row: row.foundation_share)
    out += [
        Token("ground.designs", "shipped designs the measure covers",
              lambda: _n(len(shares))),
        Token("ground.min_name", "the design whose ground is cheapest",
              lambda: ordered[0].name),
        Token("ground.min_share", "its foundation as a share of the whole, per cent",
              lambda: _pct(ordered[0].foundation_share, 1)),
        Token("ground.max_name", "the design whose ground is dearest",
              lambda: ordered[-1].name),
        Token("ground.max_share", "its foundation share, per cent",
              lambda: _pct(ordered[-1].foundation_share, 0)),
        Token("ground.flagship_full", "the flagship's full cost, dollars",
              lambda: _n(flagship.full_cost)),
        Token("ground.flagship_foundation", "of that, the foundation, dollars",
              lambda: _n(flagship.foundation_cost)),
        Token("ground.flagship_share", "its foundation share, per cent",
              lambda: _pct(flagship.foundation_share, 1)),
        Token("ground.flagship_on_pad", "the flagship without its foundation, dollars",
              lambda: _n(flagship.on_pad_cost)),
        Token("ground.mean_share", "foundation share averaged over the catalogue, per cent",
              lambda: _pct(sum(row.foundation_share for row in shares)
                           / len(shares), 1)),
        Token("ground.over_half", "designs whose foundation is over half the cost",
              lambda: _n(sum(1 for row in shares
                             if row.foundation_share > 0.5))),
    ]
    for _name in (row.name for row in shares):
        _slug = re.sub(r"[^a-z0-9]+", "_", _name.lower()).strip("_")
        out.append(Token(
            f"ground.share_{_slug}",
            f"foundation share of the {_name}, per cent",
            (lambda name: lambda: _pct(pm.on_pad(name).foundation_share, 1))(
                _name)))

    # ---- 64: a pad, not a plot ------------------------------------------
    sizes = pm.pad_sizes()
    standard, basic = pm.standard_pad(), pm.basic_pad()
    out += [
        Token("pad.sizes_count", "how many standard pad sizes there are",
              lambda: _n(len(sizes))),
        Token("pad.sizes_list", "the standard pad sizes, feet",
              lambda: ", ".join(f"{size:.0f}" for size in sizes[:-1])
                      + f" and {sizes[-1]:.0f}"),
        Token("pad.smallest", "the smallest standard pad, ft",
              lambda: _n(sizes[0])),
        Token("pad.biggest", "the largest standard pad, ft",
              lambda: _n(sizes[-1])),
        Token("pad.step", "the step between pad sizes, ft",
              lambda: _n(pm.PAD_STEP_FT)),
        Token("pad.standard_ft", "the flagship's pad diameter, ft",
              lambda: _n(standard.diameter_ft)),
        Token("pad.standard_area", "that pad's area, sq ft",
              lambda: _n(standard.area_sqft)),
        Token("pad.standard_build", "what the loaded pad costs to build, dollars",
              lambda: _n(standard.build_cost)),
        Token("pad.standard_net", "what it nets its host in a year, dollars",
              _pad_year("standard", "net")),
        Token("pad.standard_payback", "years for the loaded pad to pay for itself",
              _pad_year("standard", "payback_years", 1)),
        Token("pad.basic_build", "what the bare pad costs to build, dollars",
              lambda: _n(basic.build_cost)),
        Token("pad.basic_net", "what the bare pad nets in a year, dollars",
              _pad_year("basic", "net")),
        Token("pad.basic_payback", "years for the bare pad to pay for itself",
              _pad_year("basic", "payback_years", 1)),
        Token("pad.lease_mo", "what the pad rents for, dollars a month",
              lambda: _n(standard.lease_per_month)),
        Token("pad.occupancy_pct", "share of the year the host plans to lease it",
              lambda: _pct(pm.declared("occupancy_fraction"), 0)),
        # These used to read three flat rates off park_model. Those rates
        # were contractor prices carrying an "owner-built" description, and
        # they are gone; pad_deck counts the piers, beams, joists and boards
        # instead. The tokens ask it, so the book moves when the takeoff does.
        Token("pad.gravel_rate", "gravel base, dollars per sq ft",
              lambda: _n(_deck("gravel").usd_per_sqft, 1)),
        Token("pad.concrete_rate", "concrete slab, dollars per sq ft",
              lambda: _n(_deck("slab").usd_per_sqft)),
        Token("pad.wood_rate", "framed deck, dollars per sq ft",
              lambda: _n(_deck("blocks").usd_per_sqft)),
        Token("pad.gravel_48", "a 48 ft gravel base, dollars",
              lambda: _n(_deck("gravel").cost)),
        Token("pad.concrete_48", "a 48 ft slab, dollars",
              lambda: _n(_deck("slab").cost)),
        Token("pad.wood_48", "a 48 ft framed deck, dollars",
              lambda: _n(_deck("blocks").cost)),
        Token("pad.cheap_area", "the cheap pad's area, sq ft",
              lambda: _n(pm.pad_area_sqft(pm.declared("iris_max_ft")))),
        Token("pad.cheap_deck", "its deck on blocks, dollars",
              lambda: _n(pm.cheap_pad_rows()[0][1])),
        Token("pad.cheap_hub", "its share of the hub, dollars",
              lambda: _n(pm.cheap_pad_rows()[1][1])),
        Token("pad.cheap_spur", "its spur from the hub, dollars",
              lambda: _n(pm.cheap_pad_rows()[2][1])),
        Token("pad.cheap_permits", "its permits, dollars",
              lambda: _n(pm.cheap_pad_rows()[3][1])),
        Token("pad.cheap_total", "the whole cheap pad, dollars",
              lambda: _n(pm.cheap_pad_cost())),
        Token("pad.rotating", "the rotating base on the loaded pad, dollars",
              lambda: _n(standard.diameter_ft
                         * pm.declared("rotation_ring_usd_per_ft"))),
        Token("pad.column", "the utility column, dollars",
              lambda: _n(pm.declared("utility_column_usd"))),
        Token("pad.pedestal", "the electrical pedestal, dollars",
              lambda: _n(pm.declared("electric_pedestal_usd"))),
        Token("pad.water_line", "the water and drain tie-in, dollars",
              lambda: _n(pm.declared("water_connection_usd"))),
        Token("pad.infra", "share of road and trunk services, dollars",
              lambda: _n(pm.declared("site_infrastructure_usd_per_pad"))),
        Token("pad.solar_watts", "array the loaded pad carries, watts",
              lambda: _n(standard.solar_watts)),
        Token("pad.solar_cost", "what that array costs, dollars",
              lambda: _n(standard.solar_watts
                         * pm.declared("solar_usd_per_watt"))),
        Token("pad.hub_served", "pads one hub panel serves",
              lambda: _n(pm.declared("hub_pads_served"))),
        Token("pad.fits_48", "shipped domes a 48 ft pad can take",
              lambda: _n(len(pm.domes_that_fit(48.0)))),
    ]

    # ---- 65: turning the house toward the sun ----------------------------
    ring40 = 40.0 * pm.declared("rotation_ring_usd_per_ft")
    gain_yr = solar_one.tracking_gain_kwh * 12.0
    out += [
        Token("sun.radius", "the dome radius every solar figure is for, ft",
              lambda: _n(pm.SOLAR_RADIUS_FT)),
        Token("sun.panels_one", "panels on one side of that shell",
              lambda: _n(solar_one.panels)),
        Token("sun.of_panels", "panels the whole shell has",
              lambda: _n(solar_one.of_panels)),
        Token("sun.area", "clad area of one side, sq ft",
              lambda: _n(solar_one.area_sqft)),
        Token("sun.kw", "array size of one side, kW",
              lambda: _n(solar_one.watts / 1000.0, 1)),
        Token("sun.fixed", "one side, fixed, kWh a month",
              lambda: _n(solar_one.kwh_fixed)),
        Token("sun.tracked", "one side, tracking, kWh a month",
              lambda: _n(solar_one.kwh_tracking)),
        Token("sun.gain_mo", "what turning the pad adds, kWh a month",
              lambda: _n(solar_one.tracking_gain_kwh)),
        Token("sun.gain_pct", "declared tracking gain over fixed, per cent",
              lambda: _pct(pm.declared("tracking_gain_fraction"), 0)),
        Token("sun.hours", "peak sun hours a day the model assumes",
              lambda: _n(pm.declared("sun_hours_per_day"), 1)),
        Token("sun.tenant", "what a tenant uses, kWh a month",
              lambda: _n(pm.declared("tenant_kwh_per_month"))),
        Token("sun.surplus_pct", "share of the tracked output a tenant cannot use",
              lambda: _pct((solar_one.kwh_tracking
                            - pm.declared("tenant_kwh_per_month"))
                           / solar_one.kwh_tracking, 0)),
        Token("sun.all_fixed", "whole shell, fixed, kWh a month",
              lambda: _n(solar_all.kwh_fixed)),
        Token("sun.all_tracked", "whole shell, tracking, kWh a month",
              lambda: _n(solar_all.kwh_tracking)),
        Token("sun.all_gain", "what turning a fully clad dome adds, kWh a month",
              lambda: _n(solar_all.tracking_gain_kwh)),
        Token("sun.all_mult", "times a tenant's use a full shell makes",
              lambda: _n(solar_all.kwh_tracking
                         / pm.declared("tenant_kwh_per_month"), 1)),
        Token("sun.retail", "what bought power costs, dollars per kWh",
              lambda: _n(pm.declared("power_buy_usd_per_kwh"), 2)),
        Token("sun.export", "what sent-back power earns, dollars per kWh",
              lambda: _n(pm.declared("power_export_usd_per_kwh"), 3)),
        Token("sun.gain_yr", "the tracking gain, a year, kWh",
              lambda: _n(gain_yr)),
        Token("sun.gain_export", "a year of that gain, valued at export rate, dollars",
              lambda: _n(gain_yr * pm.declared("power_export_usd_per_kwh"), 0)),
        Token("sun.gain_retail", "the same gain valued at retail, dollars",
              lambda: _n(gain_yr * pm.declared("power_buy_usd_per_kwh"), 0)),
        Token("sun.ring_ft", "the rotating ring, dollars per foot of diameter",
              lambda: _n(pm.declared("rotation_ring_usd_per_ft"))),
        Token("sun.ring_40", "the ring under a 40 ft pad, dollars",
              lambda: _n(ring40)),
        Token("sun.payback_export", "years the ring takes to repay, at export value",
              lambda: _n(ring40 / (gain_yr
                                   * pm.declared("power_export_usd_per_kwh")), 0)),
        Token("sun.payback_retail", "the same, if every gained kWh were worth retail",
              lambda: _n(ring40 / (gain_yr
                                   * pm.declared("power_buy_usd_per_kwh")), 0)),
    ]

    # ---- 66: one pad, every dome size ------------------------------------
    classes = pm.DOME_CLASSES
    pad_small = pm.cheap_pad_cost(classes[0].diameter_ft)
    pad_mid = pm.cheap_pad_cost(classes[1].diameter_ft)
    pad_large = pm.cheap_pad_cost(classes[2].diameter_ft)
    one_iris = pm.cheap_pad_cost(pm.declared("iris_max_ft")) + pm.iris_cost()
    out += [
        Token("iris.min", "the smallest aperture, ft",
              lambda: _n(pm.iris_span()[0])),
        Token("iris.max", "the largest aperture, ft",
              lambda: _n(pm.iris_span()[1])),
        Token("iris.rate", "the mechanism, dollars per foot of aperture",
              lambda: _n(pm.declared("iris_usd_per_ft"))),
        Token("iris.cost_max", "the mechanism at full aperture, dollars",
              lambda: _n(pm.iris_cost())),
        Token("iris.small_ft", "the small dome's diameter, ft",
              lambda: _n(classes[0].diameter_ft, 1)),
        Token("iris.mid_ft", "the medium dome's diameter, ft",
              lambda: _n(classes[1].diameter_ft, 1)),
        Token("iris.large_ft", "the large dome's diameter, ft",
              lambda: _n(classes[2].diameter_ft, 1)),
        Token("iris.small_floor", "the small dome's floor, sq ft",
              lambda: _n(classes[0].floor_sqft)),
        Token("iris.mid_floor", "the medium dome's floor, sq ft",
              lambda: _n(classes[1].floor_sqft)),
        Token("iris.large_floor", "the large dome's floor, sq ft",
              lambda: _n(classes[2].floor_sqft)),
        Token("iris.small_member", "the small dome's longest member, ft",
              lambda: _n(classes[0].longest_member_ft, 1)),
        Token("iris.mid_member", "the medium dome's longest member, ft",
              lambda: _n(classes[1].longest_member_ft, 1)),
        Token("iris.large_member", "the large dome's longest member, ft",
              lambda: _n(classes[2].longest_member_ft, 1)),
        Token("iris.covers", "of the three sizes the one iris covers",
              lambda: _n(sum(1 for dome in classes if pm.iris_covers(dome)))),
        Token("iris.pad_small", "a fixed cheap pad at the small size, dollars",
              lambda: _n(pad_small)),
        Token("iris.pad_mid", "a fixed cheap pad at the medium size, dollars",
              lambda: _n(pad_mid)),
        Token("iris.pad_large", "a fixed cheap pad at the large size, dollars",
              lambda: _n(pad_large)),
        Token("iris.three_pads", "three fixed pads, one per size, dollars",
              lambda: _n(pad_small + pad_mid + pad_large)),
        Token("iris.one_pad", "one iris pad at full aperture, dollars",
              lambda: _n(one_iris)),
        Token("iris.saving", "what the iris saves over three fixed pads, dollars",
              lambda: _n(pad_small + pad_mid + pad_large - one_iris)),
    ]

    # ---- 67: why a network beats a park ----------------------------------
    host = pm.host_comparison(pm.standard_pad())
    out += [
        Token("net.crossover", "month the dome becomes the cheapest roof",
              lambda: _n(pm.crossover_months(pm.FLAGSHIP_DOME))),
        Token("net.hotel_mo", "a hotel room, a month, dollars",
              lambda: _n(options[0].monthly)),
        Token("net.short_mo", "a short let, a month, dollars",
              lambda: _n(options[1].monthly)),
        Token("net.apartment_mo", "a leased apartment, a month, dollars",
              lambda: _n(options[2].monthly, 0)),
        Token("net.dome_mo", "the dome on a pad, a month, dollars",
              lambda: _n(options[3].monthly)),
        Token("net.apartment_entry", "moving into the apartment, dollars",
              lambda: _n(options[2].entry)),
        Token("net.deposit", "the part of that which comes back, dollars",
              lambda: _n(options[2].recoverable)),
        Token("net.break_fee", "leaving the lease early, dollars",
              lambda: _n(options[2].early_exit_months)),
        Token("net.lease_months", "the lease you sign, months",
              lambda: _n(options[2].lease_months)),
        Token("net.dome_entry", "moving onto a pad, dollars",
              lambda: _n(dome_option.entry)),
        Token("net.dome_asset", "of that, the dome you keep, dollars",
              lambda: _n(dome_option.asset_cost)),
        Token("net.transport", "moving the dome between pads, dollars",
              lambda: _n(pm.declared("dome_transport_usd"))),
        Token("net.haircut_pct", "what a dome loses the day it is secondhand",
              lambda: _pct(pm.declared("resale_haircut_fraction"), 0)),
        Token("net.life_yr", "declared service life of a maintained dome, years",
              lambda: _n(pm.declared("dome_service_life_years"))),
        Token("net.residual_pct", "share of its value a dome never falls below",
              lambda: _pct(pm.declared("dome_residual_fraction"), 0)),
        Token("net.recovered_12", "what a dome is worth leaving after a year, dollars",
              lambda: _n(dome_option.recovered(12.0))),
        Token("net.recovered_60", "after five years, dollars",
              lambda: _n(dome_option.recovered(60.0))),
        Token("net.utilities", "a tenant's power and water, a month, dollars",
              lambda: _n(pm.tenant_utilities(margin=True), 1)),
        Token("net.utilities_raw", "the same without the host's margin, dollars",
              lambda: _n(pm.tenant_utilities(margin=False), 1)),
        Token("net.host_pad_upfront", "a host's upfront cost, dome pad, dollars",
              lambda: _n(host[0].upfront)),
        Token("net.host_let_upfront", "a host's upfront cost, furnished let, dollars",
              lambda: _n(host[1].upfront)),
        Token("net.host_pad_yearly", "what the dome pad costs its host a year, dollars",
              lambda: _n(host[0].yearly_costs)),
        Token("net.host_let_yearly", "what the furnished let costs a year, dollars",
              lambda: _n(host[1].yearly_costs)),
        Token("net.hub_panel", "one hub panel and manifold, dollars",
              lambda: _n(pm.declared("hub_panel_usd"))),
        Token("net.hub_share", "one pad's quarter of the hub, dollars",
              lambda: _n(pm.declared("hub_panel_usd")
                         / pm.declared("hub_pads_served"))),
        Token("net.spur", "the spur from hub to pad, dollars",
              lambda: _n(pm.declared("spur_usd_per_pad"))),
        Token("net.hub_pads", "pads one hub serves",
              lambda: _n(pm.declared("hub_pads_served"))),
        Token("net.infra", "share of road and trunk services, dollars",
              lambda: _n(pm.declared("site_infrastructure_usd_per_pad"))),
    ]

    # ---- 68: what would have to be true ---------------------------------
    from . import house_economics as he
    from . import lexicon_concepts as lc
    from .dome_costing import build_variants
    national_sqft = he.value("nahb_finished_sqft")
    per_sqft = he.construction_total() / national_sqft
    points = dp.ten_points()
    finished = build_variants()[2]  # PRISTINE, HAT -- the ten-points figure
    national_floor = dp.FLOOR_SQFT * per_sqft
    out += [
        Token("honest.price", "the national average new-home price, dollars",
              lambda: _n(he.price_total())),
        Token("honest.construction", "of that, the building cost, dollars",
              lambda: _n(he.construction_total())),
        Token("honest.nahb_sqft", "the finished home that price builds, sq ft",
              lambda: _n(national_sqft)),
        Token("honest.per_sqft", "national construction cost per square foot, dollars",
              lambda: _n(per_sqft, 0)),
        Token("honest.finished_usd", "the finished dome the ten points quote, dollars",
              lambda: _n(finished.total)),
        Token("honest.finished_per_sqft", "that finished dome, dollars per sq ft",
              lambda: _n(finished.per_sqft)),
        Token("honest.finished_figure", "the ten-points finished-dome figure",
              lambda: points[5].figure),
        Token("honest.finished_detail", "how that figure is composed",
              lambda: points[5].detail),
        Token("honest.ref_floor", "the reference floor both numbers cover, sq ft",
              lambda: _n(dp.FLOOR_SQFT)),
        Token("honest.national_floor", "the reference floor at the national rate, dollars",
              lambda: _n(national_floor)),
        Token("honest.gap", "the gap between the two ways of pricing one floor, dollars",
              lambda: _n(national_floor - finished.total)),
        Token("honest.ratio", "how many times the national rate is the finished figure",
              lambda: _n(national_floor / finished.total, 1)),
        Token("honest.points", "claims in the ten-points list",
              lambda: _n(len(points))),
        Token("honest.concepts", "concepts in the corpus taxonomy",
              lambda: _n(len(lc.CONCEPTS))),
    ]

    return out


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
