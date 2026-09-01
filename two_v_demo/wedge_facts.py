"""Every derivation the radial-wedge lesson puts on film.

The arithmetic lives in :mod:`two_v_demo.wedge_geometry`; this module
only formats it into the ordered step lists the math overlay reveals
one line at a time.  Nothing here computes a figure of its own.

One screen is unusual and deliberately so.  The brief this lesson comes
from estimates 32 true two-by-fours per tree.  Packing rectangles into
the same five sections gives fewer, so :func:`steps_rectangles` shows
the packing row by row, states both numbers, and
:func:`steps_compare` then makes the comparison twice -- once against
the computed figure and once against the brief's kinder one -- because
the conclusion survives either and a film that quietly picked the
flattering number would not deserve to be believed.
"""

from __future__ import annotations

import math
from functools import lru_cache

from .hubless_geometry import hubless_summary
from .wedge_geometry import (
    DEFAULT_LOG,
    EXTERNAL_CONSTANTS,
    SECTOR_ANGLE_DEG,
    SECTORS_PER_LOG,
    build_plan,
    member_classes,
    pinwheel_panels,
    section_rows,
    sector_area_in2,
    sector_chord_in,
    sector_depth_in,
    tree_yield,
    two_by_four_packing,
    wedge_report,
)


LOG = DEFAULT_LOG
YIELD = tree_yield(LOG)
PLAN = build_plan()
SUMMARY = hubless_summary()

# One true two-by-four, for every comparison on every screen.
TWO_BY_FOUR_AREA_IN2 = 8.0
TWO_BY_FOUR_BF = 8.0


def _conclude(steps: list[str], conclusion: str) -> tuple[str, ...]:
    steps.append(conclusion)
    return tuple(steps)


# ======================================================================
# The tree
# ======================================================================

@lru_cache(maxsize=1)
def steps_trunk() -> tuple[str, ...]:
    """Screen 1 -- how much wood is standing there."""
    rows = section_rows(LOG)
    steps = [
        "one pine, measured before anything is cut:",
        f"  {LOG.butt_diameter_in:.1f} in across at the bottom of the "
        f"usable length",
        f"  {LOG.top_diameter_in:.1f} in across where it stops being "
        "useful",
        f"  {LOG.usable_length_ft:.0f} ft of usable trunk between them",
        "a trunk is a cone with its tip cut off, so its volume is",
        "  V = pi L (r1^2 + r1 r2 + r2^2) / 3",
        "  r1 and r2 are the two end radii, L the length",
        "  one board foot is 144 cubic inches, so divide by 144:",
        f"  solid wood = {YIELD.solid_bf:.1f} board feet",
        f"buck it into {LOG.sections} lengths of "
        f"{LOG.section_length_ft:.0f} ft:",
    ]
    steps.extend(
        f"  section {row.index + 1}: {row.butt_diameter_in:.1f} -> "
        f"{row.top_diameter_in:.1f} in, {row.solid_bf:.1f} bf"
        for row in rows
    )
    return _conclude(
        steps,
        f"{YIELD.solid_bf:.0f} board feet of wood is standing in one "
        "tree. Every method below starts from exactly this much.")


@lru_cache(maxsize=1)
def steps_rectangles() -> tuple[str, ...]:
    """Screen 2 -- what is left after squaring the circle."""
    rows = section_rows(LOG)
    brief = YIELD.brief_two_by_four_count
    steps = [
        "to get true 2 in x 4 in sticks, rectangles have to be packed",
        "into a circle. A mill saws parallel rows, and a row is only as",
        "wide as its narrowest edge, because a stick has to be full",
        "width along its whole length:",
    ]
    steps.extend(
        f"  section {row.index + 1} ({row.top_diameter_in:.1f} in small "
        f"end): {' + '.join(str(value) for value in row.two_by_four_rows)}"
        f" = {row.two_by_four_count}"
        for row in rows
    )
    steps.extend([
        f"  total = {YIELD.two_by_four_count} true 2x4x"
        f"{LOG.section_length_ft:.0f} per tree",
        f"  each one holds {TWO_BY_FOUR_BF:.0f} bf, so "
        f"{YIELD.two_by_four_count} x {TWO_BY_FOUR_BF:.0f} = "
        f"{YIELD.two_by_four_bf:.0f} bf",
        f"  out of {YIELD.solid_bf:.1f} bf standing, that is "
        f"{YIELD.two_by_four_recovery * 100:.1f}% recovery",
        f"the brief this lesson works from estimates {brief} pieces",
        f"  ({YIELD.brief_two_by_four_bf:.0f} bf, "
        f"{YIELD.brief_two_by_four_bf / YIELD.solid_bf * 100:.1f}%),",
        "  which is kinder to the mill than this packing. Both numbers",
        "  are carried through to the comparison.",
    ])
    return _conclude(
        steps,
        f"Squaring a round log throws away more than half of it: "
        f"{YIELD.solid_bf - YIELD.two_by_four_bf:.0f} board feet does "
        "not become the thing we came for.")


@lru_cache(maxsize=1)
def steps_radial() -> tuple[str, ...]:
    """Screen 3 -- what is left after splitting it instead."""
    mid = LOG.diameter_at(LOG.usable_length_ft * 0.5)
    steps = [
        "now split the same sections instead of squaring them:",
        "  one cut halves the log            (a full diameter of kerf)",
        "  one more cut makes quarters       (another full diameter)",
        f"  four cuts pith to bark make {SECTORS_PER_LOG} eighths",
        "  four radius-long cuts are two more diameters of kerf,",
        "  so each section loses four diameters of kerf in total:",
        "  kerf volume = 4 x diameter x kerf width x length",
        f"  at a {LOG.kerf_in} in chainsaw kerf and a {mid:.1f} in "
        "middle diameter",
        f"  the whole tree gives up {YIELD.kerf_bf:.1f} bf to the saw",
        f"  {YIELD.solid_bf:.1f} - {YIELD.kerf_bf:.1f} = "
        f"{YIELD.wedge_bf:.1f} bf left in the wedges",
        f"  = {YIELD.wedge_recovery * 100:.1f}% of the standing tree",
        "nothing was squared, edged or trimmed: the curved outside of",
        "  the tree is still part of the structural member",
        f"  {LOG.sections} sections x {SECTORS_PER_LOG} sectors = "
        f"{YIELD.wedge_count} wedges, crosscut once each",
        f"  = {YIELD.strut_count} struts of "
        f"{LOG.strut_length_ft:.0f} ft, at "
        f"{YIELD.bf_per_strut:.2f} bf apiece",
    ]
    return _conclude(
        steps,
        f"Splitting keeps {YIELD.wedge_recovery * 100:.0f}% of the tree "
        "because the only wood lost is the wood the blade turned into "
        "sawdust.")


@lru_cache(maxsize=1)
def steps_compare() -> tuple[str, ...]:
    """Screen 4 -- the two methods side by side, twice."""
    two_trees_wedge = YIELD.wedge_bf * 2
    two_trees_rect = YIELD.two_by_four_bf * 2
    two_trees_brief = YIELD.brief_two_by_four_bf * 2
    steps = [
        "the same two trees, converted both ways:",
        f"  radial wedges   {two_trees_wedge:6.0f} bf   "
        f"{YIELD.strut_count * 2} struts",
        f"  packed 2x4s     {two_trees_rect:6.0f} bf   "
        f"{YIELD.two_by_four_struts * 2} struts",
        f"  ratio = {two_trees_wedge:.0f} / {two_trees_rect:.0f} = "
        f"x{YIELD.gain_over_computed:.2f}",
        "against the brief's kinder estimate for the mill:",
        f"  brief's 2x4s    {two_trees_brief:6.0f} bf   "
        f"{YIELD.brief_two_by_four_count * 4} struts",
        f"  ratio = {two_trees_wedge:.0f} / {two_trees_brief:.0f} = "
        f"x{YIELD.gain_over_brief:.2f}",
        f"  = {(YIELD.gain_over_brief - 1.0) * 100:.0f}% more wood, "
        "which is the figure the brief quotes",
        "either way the direction is the same, and the member count",
        "  moves with it:",
        f"  {YIELD.strut_count * 2} wedge struts against "
        f"{YIELD.brief_two_by_four_count * 4} sawn ones = "
        f"{YIELD.strut_count * 2 - YIELD.brief_two_by_four_count * 4} more",
    ]
    return _conclude(
        steps,
        f"Between x{YIELD.gain_over_brief:.2f} and "
        f"x{YIELD.gain_over_computed:.2f} more structural wood out of "
        "the same two trees, for one fewer machine.")


# ======================================================================
# The member
# ======================================================================

@lru_cache(maxsize=1)
def steps_sector() -> tuple[str, ...]:
    """Screen 5 -- what one eighth of a log actually is."""
    design = PLAN.design_diameter_in
    equal = math.sqrt(TWO_BY_FOUR_AREA_IN2 * SECTORS_PER_LOG / math.pi) * 2.0
    steps = [
        f"one sector is {SECTOR_ANGLE_DEG:.0f} degrees of the round:",
        "  area  = pi r^2 / 8",
        "  width = 2 r sin(180 deg / 8)   across the bark face",
        "  depth = r                      pith to bark",
        f"at the design diameter of {design:.1f} in:",
        f"  area  = {sector_area_in2(design):.2f} sq in",
        f"  width = {sector_chord_in(design):.2f} in",
        f"  depth = {sector_depth_in(design):.2f} in",
        f"a true 2x4 is 2 x 4 = {TWO_BY_FOUR_AREA_IN2:.0f} sq in, so this",
        f"  sector is worth {PLAN.equivalent_two_by_fours:.2f} of them",
        "and the depth is the useful part: bending stiffness grows with",
        "  the cube of depth, and this section is deep and narrow",
        "the break-even diameter, where one eighth equals one 2x4:",
        f"  pi r^2 / 8 = {TWO_BY_FOUR_AREA_IN2:.0f}  ->  diameter = "
        f"{equal:.2f} in",
        f"  check: sector at {equal:.1f} in = "
        f"{sector_area_in2(equal):.2f} sq in",
    ]
    return _conclude(
        steps,
        f"Above about {equal:.0f} inches of trunk, every eighth of the "
        "log already holds more wood than a two-by-four -- before any "
        "milling at all.")


# ======================================================================
# The panel
# ======================================================================

@lru_cache(maxsize=1)
def steps_pinwheel() -> tuple[str, ...]:
    """Screen 6 -- the joint inside one triangle."""
    panels = pinwheel_panels(PLAN.radius_in, PLAN.member_width_in)
    member = panels[0].members[0]
    steps = [
        "three members, one triangle, and not a single mitre:",
        "  each member lies with its bark face on its own edge line",
        f"  so its centre sits {PLAN.member_width_in / 2:.2f} in inside "
        "that line -- half its width",
        "each end is a square crosscut, and the two ends do different",
        "  jobs, the same way round for all three members:",
        "  the HEAD is cut against the side of the next member",
        "  the TAIL runs on through the previous member's band, so that",
        "  member's head has a full face to bear on",
        f"  bearing length = {member.bearing_length_in:.3f} in of contact",
        "the corner is where the two bands cross, so no wood reaches it:",
        f"  nearest end to the mathematical vertex = "
        f"{min(member.tail_vertex_gap_in, member.head_vertex_gap_in):.3f} in",
        "which is why the triangle's corners are references, not",
        "  endpoints -- the geometry is exact even though no stick is",
        "  cut to it",
        "the price is that the sticks are shorter than their edges:",
        f"  edge {member.edge_length_in:.3f} in, member "
        f"{member.length_in:.3f} in, inset {member.inset_in:.3f} in",
    ]
    return _conclude(
        steps,
        "Every end in the whole frame is a square crosscut: the "
        "pinwheel trades a little length for the hardest operation in "
        "dome building disappearing entirely.")


@lru_cache(maxsize=1)
def steps_lengths() -> tuple[str, ...]:
    """Screen 7 -- two edge classes become four stick lengths."""
    classes = member_classes(PLAN.radius_in, PLAN.member_width_in)
    steps = [
        "a 2V hemisphere has two edge lengths, SHORT and LONG.",
        "the pinwheel gives four stick lengths, because where an end",
        "stops depends on the corner it stops in:",
    ]
    steps.extend(
        f"  {item.edge_class:<5} x{item.count:<3} {item.length_in:7.3f} in"
        f"   (edge {item.edge_length_in:.3f} in)"
        for item in classes
    )
    total = sum(item.count for item in classes)
    steps.extend([
        f"  {total} sticks in {len(classes)} lengths, three per panel",
        "cut them in that order and the saw stop moves four times for",
        "  the whole building",
        f"  longest  {max(item.length_in for item in classes):.3f} in",
        f"  shortest {min(item.length_in for item in classes):.3f} in",
        f"  spread   "
        f"{max(item.length_in for item in classes) - min(item.length_in for item in classes):.3f} in",
    ])
    return _conclude(
        steps,
        f"{total} members, {len(classes)} lengths, every end square: "
        "the whole cut list fits on the back of a hand.")


@lru_cache(maxsize=1)
def steps_seams() -> tuple[str, ...]:
    """Screen 8 -- what happens between two panels."""
    gasket = PLAN.gasket
    steps = [
        "neighbouring panels do not share a stick. Each one carries its",
        "own member along the shared edge, so the shell has:",
        f"  {SUMMARY.doubled_edges} interior seams, two members each",
        f"  {SUMMARY.rim_edges} seams at the rim, one member each",
        f"  {SUMMARY.doubled_edges} x 2 + {SUMMARY.rim_edges} = "
        f"{SUMMARY.strut_check} members, which is the frame",
        "between each pair goes a spline, key or hose gasket:",
        f"  thickness {gasket.thickness_in:.2f} in, so each panel sits "
        f"{gasket.thickness_in / 2:.3f} in inside its true edge",
        f"  seam length = {gasket.total_length_ft:.1f} ft in total",
        "the gasket has to close the angle between the two panels, and",
        "  that angle is not one number:",
        f"  dihedral runs {gasket.min_dihedral_deg:.2f} to "
        f"{gasket.max_dihedral_deg:.2f} deg",
        f"  a spread of "
        f"{gasket.max_dihedral_deg - gasket.min_dihedral_deg:.2f} deg "
        "across the whole shell",
        "a compressible gasket absorbs that spread. Shaving the wood to",
        "  suit each neighbour would mean a different bevel per seam.",
    ]
    return _conclude(
        steps,
        f"One gasket takes up {gasket.max_dihedral_deg - gasket.min_dihedral_deg:.1f} "
        "degrees of variation that would otherwise have to be cut into "
        "the timber, seam by seam.")


# ======================================================================
# The shell
# ======================================================================

@lru_cache(maxsize=1)
def steps_dome() -> tuple[str, ...]:
    """Screen 9 -- the building the two trees actually make."""
    steps = [
        "the tree sets the strut length, so it also sets the dome:",
        f"  {LOG.section_length_ft:.0f} ft section, cut once = "
        f"{LOG.strut_length_ft:.0f} ft members",
        f"  the longest pinwheel member is {PLAN.longest_member_in:.1f} in",
        "  solve for the radius that makes that true:",
        f"  R = {PLAN.radius_in:.2f} in = {PLAN.radius_in / 12:.2f} ft",
        f"  span   {PLAN.diameter_ft:.2f} ft across",
        f"  height {PLAN.height_ft:.2f} ft at the crown",
        f"  floor  {PLAN.floor_sqft:.0f} sq ft",
        "and the stock:",
        f"  {PLAN.trees} trees x {LOG.struts_per_tree} struts = "
        f"{PLAN.members_available} members",
        f"  the frame needs {PLAN.members_needed}",
        f"  {PLAN.members_available} - {PLAN.members_needed} = "
        f"{PLAN.spare_members} left for the floor and the fit-out",
        f"  timber standing in the frame = "
        f"{PLAN.timber_in_frame_ft:.0f} ft of member",
    ]
    return _conclude(
        steps,
        f"Two trees, {PLAN.members_needed} members, a "
        f"{PLAN.diameter_ft:.0f} foot dome with "
        f"{PLAN.floor_sqft:.0f} square feet of floor -- and "
        f"{PLAN.spare_members} sticks still spare.")


@lru_cache(maxsize=1)
def steps_actions() -> tuple[str, ...]:
    """Screen 10 -- counting operations rather than dollars."""
    rows = section_rows(LOG)
    # Splitting: two full cuts plus four radial cuts per section, then
    # one crosscut per wedge.
    splits_per_section = 2 + SECTORS_PER_LOG // 2
    radial_cuts = LOG.sections * splits_per_section
    crosscuts = LOG.wedges_per_tree
    radial_total = radial_cuts + crosscuts
    # Milling: a rip down each side of the cant, then a cut between each
    # pair of rows, then edging each board, then crosscutting.
    mill_rows = sum(len(row.two_by_four_rows) for row in rows)
    mill_rips = LOG.sections * 2 + mill_rows
    mill_edges = YIELD.two_by_four_count * 2
    mill_total = mill_rips + mill_edges + YIELD.two_by_four_count
    steps = [
        "count operations instead of money. One tree, to strut:",
        "  splitting:",
        f"    {LOG.sections} sections x {splits_per_section} rip cuts = "
        f"{radial_cuts}",
        f"    {crosscuts} crosscuts, one per wedge",
        f"    total {radial_total} cuts for "
        f"{YIELD.strut_count} struts",
        f"    = {radial_total / YIELD.strut_count:.2f} cuts per member",
        "  milling to true 2x4:",
        f"    {mill_rips} rips to open the cant and part the rows",
        f"    {mill_edges} edging passes, two per board",
        f"    {YIELD.two_by_four_count} crosscuts",
        f"    total {mill_total} cuts for "
        f"{YIELD.two_by_four_struts} struts",
        f"    = {mill_total / YIELD.two_by_four_struts:.2f} cuts per member",
        "and that is only the cuts: not the setting out, the handling,",
        "  the sorting, the stacking or the hauling between machines",
    ]
    return _conclude(
        steps,
        f"About {radial_total / YIELD.strut_count:.1f} cuts a member "
        f"instead of {mill_total / YIELD.two_by_four_struts:.1f} -- and "
        "the shorter chain is the one that keeps more of the tree.")


# ----------------------------------------------------------------------
# The registry, the audit, and the proof
# ----------------------------------------------------------------------

ALL_SCREENS: tuple[tuple[str, object], ...] = (
    ("trunk", steps_trunk),
    ("rectangles", steps_rectangles),
    ("radial", steps_radial),
    ("compare", steps_compare),
    ("sector", steps_sector),
    ("pinwheel", steps_pinwheel),
    ("lengths", steps_lengths),
    ("seams", steps_seams),
    ("dome", steps_dome),
    ("actions", steps_actions),
)


def wedge_facts_report() -> str:
    """The audit: the model, then every screen line for line."""
    lines = [wedge_report(), "", "=" * 68, "",
             "MATH SCREENS, AS THE FILM SHOWS THEM", ""]
    for name, builder in ALL_SCREENS:
        lines.append(f"== {name.upper()} ==")
        lines.extend(f"  {line}" for line in builder())
        lines.append("")
    return "\n".join(lines)


def validate_wedge_facts() -> None:
    """Prove the screens against the module they cite."""
    from .wedge_geometry import validate_wedge_geometry

    validate_wedge_geometry()

    for name, builder in ALL_SCREENS:
        steps = builder()
        assert len(steps) >= 5, (name, len(steps))
        assert all(line.strip() for line in steps), name
        assert len(steps[-1]) >= 30, (name, steps[-1])

    # The comparison screen must state both ratios, and the honest one
    # must be the less flattering of the two.
    assert YIELD.gain_over_brief < YIELD.gain_over_computed
    text = " ".join(steps_compare())
    assert f"x{YIELD.gain_over_brief:.2f}" in text
    assert f"x{YIELD.gain_over_computed:.2f}" in text
    assert "brief" in text

    # The rectangles screen must own up to the disagreement rather than
    # quietly using whichever number suits.
    assert "brief" in " ".join(steps_rectangles())

    # The frame the seam screen counts is the frame the panels build.
    assert SUMMARY.strut_check == PLAN.members_needed == 120
    assert f"{SUMMARY.doubled_edges}" in " ".join(steps_seams())

    # The break-even diameter really is where a sector equals a 2x4.
    equal = math.sqrt(TWO_BY_FOUR_AREA_IN2 * SECTORS_PER_LOG / math.pi) * 2.0
    assert abs(sector_area_in2(equal) - TWO_BY_FOUR_AREA_IN2) < 1e-6

    # The packing screen's rows must add up to its own total.
    for row in section_rows(LOG):
        assert sum(row.two_by_four_rows) == row.two_by_four_count
        assert two_by_four_packing(row.top_diameter_in) == \
            row.two_by_four_rows

    # External constants are declared, not smuggled in.
    keys = {key for key, _v, _u, _s in EXTERNAL_CONSTANTS}
    for expected in ("butt_diameter_in", "kerf_in", "gasket_thickness_in",
                     "brief_two_by_fours_per_tree"):
        assert expected in keys, expected
