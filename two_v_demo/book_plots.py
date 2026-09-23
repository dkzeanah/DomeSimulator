"""Every table and chart in *2 Trees*, generated from the book's arithmetic.

Not one number here is typed.  Each function reaches into :mod:`book_math`,
:mod:`wedge_geometry`, :mod:`dome_costing` or the solved dome itself, and
draws what it finds.  That is the whole point: a reader who changes the tree
and re-runs gets a book whose tables describe *their* tree.

Tables are drawn rather than typeset because a printed table has to sit at a
fixed width on a fixed page, and a rendered PNG can be dropped into any
layout program without it re-flowing into three columns.  The renderer is
shared -- :func:`table` -- so every table in the book looks the same.
"""

from __future__ import annotations

import math
from pathlib import Path

from . import book_math as bm
from . import wedge_geometry as wg
from .book import Figure
from .book_figures import (HALF_H_IN, PAGE_H_IN, PAGE_W_IN, STYLE,
                           new_figure, save)


# ----------------------------------------------------------------------
# The shared table renderer
# ----------------------------------------------------------------------

def table(title: str, headers: tuple[str, ...],
          rows: tuple[tuple[str, ...], ...],
          note: str = "", align: str = "", key: str = "",
          full_page: bool = False, footer_rows: int = 0):
    """One table, drawn to look the same as every other table in the book.

    ``align`` is one character per column: ``l`` or ``r``. Numbers go right,
    words go left, and getting that wrong is the difference between a table
    you can scan and one you cannot.

    ``footer_rows`` marks the last N rows as a summary block, ruled off from
    the body, for totals and reconciliations.
    """
    columns = len(headers)
    align = align or ("l" + "r" * (columns - 1))
    assert len(align) == columns, (align, headers)

    height = PAGE_H_IN if full_page else min(
        HALF_H_IN + 0.16 * max(0, len(rows) - 8), PAGE_H_IN)
    fig = new_figure(PAGE_W_IN, height)
    axes = fig.add_axes([0, 0, 1, 1])
    axes.set_axis_off()
    axes.set_xlim(0, 1)
    axes.set_ylim(0, 1)

    top = 0.94
    if title:
        axes.text(0.0, 0.985, title, fontsize=10.5, weight="bold",
                  va="top", color=STYLE.ink)
        top = 0.90

    body_rows = len(rows)
    line_height = min(0.052, (top - 0.10) / max(1, body_rows + 2))
    y = top

    # Column positions, measured from the content rather than spread
    # evenly. Even spacing looks fine until one column holds a long header
    # and the next holds a short one, and then they overlap -- which is
    # exactly what happened to the first draft of this book's tables.
    widths = []
    for index in range(columns):
        longest = len(str(headers[index]))
        for row in rows:
            if index < len(row):
                longest = max(longest,
                              max(len(part)
                                  for part in str(row[index]).split("\n")))
        widths.append(longest + 2)
    total = float(sum(widths))
    starts, cursor = [], 0.0
    for width in widths:
        starts.append(cursor / total)
        cursor += width
    positions = []
    for index, kind in enumerate(align):
        if kind == "l":
            positions.append(starts[index])
        else:
            # Right-aligned text is drawn at the column's right edge, one
            # space short of the next column's start.
            right = (starts[index + 1] if index + 1 < columns else 1.0)
            positions.append(right - 1.0 / total)

    def draw_row(values, weight="normal", colour=STYLE.ink, size=8.0):
        for index, (value, kind) in enumerate(zip(values, align)):
            x = positions[index]
            axes.text(x, y, str(value), fontsize=size, weight=weight,
                      va="top", color=colour,
                      ha="left" if kind == "l" else "right",
                      family="monospace" if kind == "r" else "sans-serif")

    draw_row(headers, weight="bold", size=8.0)
    y -= line_height * 0.55
    axes.plot([0.0, 1.0], [y, y], color=STYLE.ink, linewidth=0.9)
    y -= line_height * 0.45

    split_at = body_rows - footer_rows
    for index, row in enumerate(rows):
        if footer_rows and index == split_at:
            y += line_height * 0.12
            axes.plot([0.0, 1.0], [y, y], color=STYLE.rule, linewidth=0.6)
            y -= line_height * 0.30
        draw_row(row,
                 weight="bold" if index >= split_at and footer_rows else
                 "normal")
        y -= line_height

    y -= line_height * 0.2
    axes.plot([0.0, 1.0], [y, y], color=STYLE.rule, linewidth=0.6)
    if note:
        y -= line_height * 0.7
        axes.text(0.0, y, _wrap(note, 78), fontsize=7.2, va="top",
                  color=STYLE.muted, style="italic")
    return fig


def _wrap(text: str, width: int) -> str:
    import textwrap
    return "\n".join(textwrap.wrap(text, width))


def _fmt(value: float, places: int = 2) -> str:
    return f"{value:,.{places}f}"


# ======================================================================
# TABLES
# ======================================================================

def plot_declared_constants(figure: Figure):
    """The inputs table, printed before the book uses any of it."""
    rows = tuple(
        (item.key.replace("_", " "), _fmt(item.value), item.unit, item.kind)
        for item in bm.DECLARED)
    # The count is len(DECLARED), not a word typed into the note. It was
    # "eleven" for a while after the table had grown to fourteen rows, which
    # is exactly the drift this book exists to refuse.
    return table(
        "Declared constants: inputs, not results",
        ("what", "value", "unit", "kind"),
        rows, align="lrll",
        note="Everything else in this book is derived from geometry. These "
             f"{len(bm.DECLARED)} could not be, so they are declared here, "
             "with what kind of number each one is. 'measured' was read off "
             "a real object; 'priced' came from a shelf; 'decided' is a "
             "build choice you may make differently; 'estimated' is a guess, "
             "and is labelled so you can discount it.",
        full_page=True)


def plot_frame_counts(figure: Figure):
    """What the frame contains, counted off the solved geometry."""
    members, panels, edges = bm.frame_counts()
    seams = bm.panel_seam_count()
    rows = (
        ("Panels (triangles)", str(panels)),
        ("Members (struts)", str(members)),
        ("Members per panel", str(members // panels)),
        ("Unique edges", str(edges)),
        ("Seams between two panels", str(seams)),
        ("Rim edges, joining nothing", str(edges - seams)),
    )
    return table(
        "What the frame contains",
        ("", "count"), rows,
        note=f"Counted from the solved dome, not chosen. The distinction "
             f"between edges and seams matters: you close {seams} joints, "
             f"not {edges}.")


def plot_member_classes(figure: Figure):
    """The four member lengths and their counts."""
    result = bm.tree_first()
    rows = tuple(
        (item.edge_class, str(item.count), _fmt(item.length_in, 3),
         _fmt(item.length_in / 12.0, 3))
        for item in result.member_classes)
    total = sum(item.count for item in result.member_classes)
    rows += (("total", str(total), "", _fmt(result.timber_in_frame_ft, 1)),)
    return table(
        "Every stick in the dome",
        ("class", "count", "each (in)", "each (ft) / all (ft)"),
        rows, align="lrrr", footer_rows=1,
        note="Two edge classes become four lengths because the pinwheel "
             "inset differs at each end. Cut to these and the dome closes. "
             "The last column is each member's length in feet, except on "
             "the total row, where it is all of them added together.")


def plot_split_counts(figure: Figure):
    """What other split counts give you."""
    plan = bm.BOOK_TREE
    diameter = plan.mid_diameter_in
    rows = []
    for sectors in (4, 6, 8, 10, 12, 16):
        width = wg.sector_chord_in(diameter, sectors)
        area = wg.sector_area_in2(diameter, sectors)
        rows.append((
            str(sectors), f"{360.0 / sectors:.0f}", _fmt(width),
            _fmt(wg.sector_depth_in(diameter)), _fmt(area),
            _fmt(area / bm.NOMINAL_TWO_BY_FOUR_IN2)))
    return table(
        f"Splitting a {diameter:.0f}-inch section other ways",
        ("splits", "angle", "width in", "depth in", "sq in", "= 2x4s"),
        tuple(rows), align="lrrrrr",
        note="Depth does not change with the split count -- it is always "
             "pith to bark. Only the width does. Eight is the book's "
             "choice: a sixth is too heavy to handle alone and a twelfth is "
             "too slender to bear on its own end.")


def plot_section_rows(figure: Figure):
    """The whole trunk, section by section, both conversions."""
    rows = tuple(
        (str(row.index + 1), _fmt(row.butt_diameter_in, 1),
         _fmt(row.top_diameter_in, 1), _fmt(row.solid_bf, 1),
         _fmt(row.kerf_bf, 1), _fmt(row.wedge_bf, 1),
         str(row.two_by_four_count))
        for row in wg.section_rows())
    yields = wg.tree_yield()
    rows += (("all", "", "", _fmt(yields.solid_bf, 1),
              _fmt(yields.kerf_bf, 1), _fmt(yields.wedge_bf, 1),
              str(yields.two_by_four_count)),)
    return table(
        "Every bucked section, converted both ways",
        ("sec", "butt in", "top in", "solid bf", "kerf bf", "wedge bf",
         "2x4s"),
        rows, align="lrrrrrr", footer_rows=1,
        note="The 2x4 column is the same round section grid-packed the way "
             "a mill would saw it, sized on its small end because a board "
             "has to be full width along its whole length.")


def plot_orientation_table(figure: Figure):
    """What each of the four wedge orientations does at a seam."""
    from . import raw_wedge_bridge as bridge
    rows = tuple(
        (name.replace("_", " "), _wrap(bridge.seam_pair_reading(name), 46))
        for name in bridge.orientations())
    return table(
        "The four orientations, at a seam",
        ("orientation", "what a pair of points does"),
        rows, align="ll",
        note="Read straight from the simulator's own seam readings, so the "
             "book and the tool cannot describe the same rotation "
             "differently.",
        full_page=True)


def _seam_angles() -> tuple[tuple[float, ...], tuple[float, ...]]:
    """(fold angles, raw gap angles) for every seam, from the solved dome.

    Read by attribute, with no default: if the simulator ever renames these
    fields, this raises instead of quietly filling the book with zeroes --
    which is what a defensive ``getattr`` did to an earlier draft.
    """
    from . import raw_wedge_bridge as bridge
    model = bridge.model()
    folds = tuple(sorted(float(seam.fold_angle_deg) for seam in model.seams))
    gaps = tuple(sorted(float(seam.raw_gap_angle_deg)
                        for seam in model.seams))
    return folds, gaps


def plot_seam_schedule(figure: Figure):
    """Every seam by fold angle -- and there turn out to be only two."""
    folds, gaps = _seam_angles()
    distinct = sorted({round(angle, 3) for angle in folds})

    fig = new_figure(PAGE_W_IN, HALF_H_IN)
    axes = fig.add_axes([0.15, 0.22, 0.80, 0.64])
    counts = [sum(1 for angle in folds if abs(angle - value) < 1e-3)
              for value in distinct]
    bars = axes.bar([f"{value:.2f}°" for value in distinct], counts,
                    color=[STYLE.accent, STYLE.good][:len(distinct)],
                    width=0.45)
    for bar, count in zip(bars, counts):
        axes.annotate(f"{count} seams", (bar.get_x() + bar.get_width() * 0.5,
                                         count), xytext=(0, 3),
                      textcoords="offset points", ha="center", fontsize=8,
                      weight="bold")
    axes.set_ylabel("seams")
    axes.set_xlabel("fold angle between the two panels")
    axes.set_title(f"All {len(folds)} seams take only "
                   f"{len(distinct)} angles")
    axes.set_ylim(0, max(counts) * 1.2)
    axes.text(0.0, -0.34,
              _wrap(f"This is better news than it looks. The seams are not "
                    f"all alike -- but they are not all different either. "
                    f"{len(distinct)} fold angles across {len(folds)} seams "
                    f"means {len(distinct)} key profiles, cut once and "
                    f"repeated. The raw gap the key has to fill runs "
                    f"{gaps[0]:.2f}° to {gaps[-1]:.2f}°.", 92),
              transform=axes.transAxes, fontsize=7.2, va="top",
              color=STYLE.muted, style="italic")
    return fig


def plot_method_a_worked(figure: Figure):
    """Design first, carried all the way through, for 300 square feet."""
    wanted = 300.0
    result = bm.design_first_for_floor(wanted)
    plan = result.plan
    rows = (
        ("Floor you want", f"{wanted:,.0f} sq ft", "chosen"),
        ("Radius that gives it", f"{result.radius_in:,.2f} in",
         "sqrt(area/pi)"),
        ("Dome diameter", f"{result.diameter_ft:,.2f} ft", "2 x radius"),
        ("Standing height at centre", f"{result.height_ft:,.2f} ft",
         "= radius"),
        ("Your stock's sector width", f"{result.member_width_in:,.2f} in",
         f"{plan.mid_diameter_in:.0f} in log, {plan.sectors} ways"),
        ("Longest member", f"{result.longest_member_in:,.2f} in", "solved"),
        ("Shortest member", f"{result.shortest_member_in:,.2f} in", "solved"),
        ("Buck to", f"{result.bucking_length_ft} ft",
         "longest member, rounded up"),
        ("Sections needed", f"{result.sections_needed:,.0f}",
         f"{bm.MEMBERS_IN_FRAME} / {plan.sectors}"),
        ("Trunk feet needed", f"{result.trunk_feet_needed:,.0f} ft",
         "sections x bucking length"),
        ("Trees needed", f"{result.trees_needed:,.2f}",
         f"at {plan.usable_length_ft:.0f} usable ft each"),
        ("So fell", f"{result.whole_trees_needed}", "rounded up"),
    )
    return table(
        f"Method A, worked: {wanted:,.0f} square feet",
        ("step", "value", "where it comes from"),
        rows, align="lrl", footer_rows=1,
        note="Every line is computed from the line above it. Change the "
             "floor area and every number below it moves.")


def plot_method_b_worked(figure: Figure):
    """Tree first, carried all the way through, for this book's tree."""
    result = bm.tree_first()
    plan = result.plan
    rows = (
        ("Trunk, butt to top",
         f"{plan.butt_diameter_in:.0f} to {plan.top_diameter_in:.0f} in",
         "measured"),
        ("Usable straight length", f"{plan.usable_length_ft:,.0f} ft",
         "measured"),
        ("Buck to", f"{plan.section_length_ft:,.0f} ft",
         "what you can carry alone"),
        ("Sections", f"{plan.sections}",
         "usable length / bucking length"),
        ("Struts per section", f"{plan.struts_per_section}",
         "one per sector"),
        ("Struts per tree", f"{plan.struts_per_tree}",
         f"{plan.sections} x {plan.sectors}"),
        ("Two trees give", f"{result.struts_available}", "x2"),
        ("The frame needs", f"{result.struts_needed}", "counted"),
        ("Spare", f"{result.spare_struts}",
         f"{result.spare_fraction * 100:.0f}% margin"),
        ("Sector width at mid trunk", f"{plan.member_width_in:,.2f} in",
         "chord of one eighth"),
        ("Radius the stock allows", f"{result.radius_in:,.2f} in", "solved"),
        ("Dome diameter", f"{result.diameter_ft:,.2f} ft", "2 x radius"),
        ("Floor", f"{result.floor_sqft:,.0f} sq ft", "pi r squared"),
    )
    return table(
        "Method B, worked: this book's two trees",
        ("step", "value", "where it comes from"),
        rows, align="lrl", footer_rows=2,
        note="You do not choose the diameter here. The tree chooses it, and "
             "the last two lines are what you find out.")


def plot_design_lookup(figure: Figure):
    """Floor area to trees, so a reader can skip the arithmetic."""
    rows = []
    for floor in (80.0, 120.0, 180.0, 250.0, 320.0, 400.0, 500.0, 650.0):
        result = bm.design_first_for_floor(floor)
        rows.append((
            f"{floor:,.0f}", _fmt(result.diameter_ft, 1),
            _fmt(result.height_ft, 1), _fmt(result.longest_member_in, 1),
            str(result.bucking_length_ft), _fmt(result.trees_needed, 2)))
    return table(
        "Design first: pick a floor, read the rest",
        ("floor sqft", "diam ft", "height ft", "longest in", "buck ft",
         "trees"),
        tuple(rows), align="lrrrrr",
        note=f"Computed at this book's stock: a "
             f"{bm.BOOK_TREE.mid_diameter_in:.0f}-inch log split "
             f"{bm.BOOK_TREE.sectors} ways. A fatter log gives wider "
             "members, which changes the longest-member column and "
             "therefore everything after it.")


def plot_tree_lookup(figure: Figure):
    """Bucking length to dome size."""
    rows = []
    plan = bm.BOOK_TREE
    for section_ft in (4.0, 5.0, 6.0, 7.0, 8.0, 10.0, 12.0):
        variant = bm.TreeCutPlan(
            butt_diameter_in=plan.butt_diameter_in,
            top_diameter_in=plan.top_diameter_in,
            usable_length_ft=plan.usable_length_ft,
            section_length_ft=section_ft)
        result = bm.tree_first(variant, trees=2)
        rows.append((
            f"{section_ft:,.0f}", str(variant.sections),
            str(variant.struts_per_tree), str(result.struts_available),
            "yes" if result.enough else "NO",
            _fmt(result.diameter_ft, 1), _fmt(result.floor_sqft, 0)))
    return table(
        "Tree first: pick a bucking length, read the dome",
        ("buck ft", "sections", "per tree", "2 trees",
         f"covers {bm.MEMBERS_IN_FRAME}?", "diam ft", "floor"),
        tuple(rows), align="lrrrlrr",
        note=f"All from one {plan.usable_length_ft:.0f}-foot trunk. Buck "
             "longer and you get a bigger dome out of fewer, heavier "
             "pieces -- and at some point two trees stop being enough.")


def plot_round_trip(figure: Figure):
    """Out and back: the two methods closing on the same dome."""
    radii = [96.0, 110.0, 129.325104, 144.0, 168.0, 192.0]
    rows = []
    worst = 0.0
    for radius in radii:
        trip = bm.round_trip(radius)
        worst = max(worst, trip.radius_error_in)
        rows.append((
            _fmt(radius, 3), _fmt(trip.longest_member_in, 3),
            _fmt(trip.recovered_radius_in, 3),
            f"{trip.radius_error_in:.1e}"))
    return table(
        "The round trip: design first, then tree first, on the same dome",
        ("start radius in", "longest member in", "recovered radius in",
         "residual in"),
        tuple(rows), align="rrrr",
        note=f"Worst residual across these six domes: {worst:.1e} inches. "
             "A chainsaw kerf is a quarter of an inch. The two methods are "
             "one calculation held at opposite ends.")


def plot_worked_tree(figure: Figure):
    """This book's tree, in one table."""
    plan = bm.BOOK_TREE
    rows = (
        ("Butt diameter", f"{plan.butt_diameter_in:,.1f} in"),
        ("Top diameter", f"{plan.top_diameter_in:,.1f} in"),
        ("Usable straight length", f"{plan.usable_length_ft:,.0f} ft"),
        ("Bucked into", f"{plan.sections} x "
                        f"{plan.section_length_ft:,.0f} ft"),
        ("Offcut", f"{plan.offcut_ft:,.1f} ft"),
        ("Split", f"{plan.sectors} ways, "
                  f"{360.0 / plan.sectors:.0f}° each"),
        ("Struts per tree", f"{plan.struts_per_tree}"),
        ("Member section", f"{plan.member_width_in:,.2f} x "
                           f"{plan.member_depth_in:,.2f} in"),
        ("Member area", f"{plan.member_area_in2:,.2f} sq in"),
        ("Worth, nominal 2x4s", f"{plan.equivalent_two_by_fours:,.2f}"),
        ("Worth, dressed 2x4s",
         f"{plan.equivalent_dressed_two_by_fours:,.2f}"),
        ("Solid wood", f"{plan.solid_bf:,.1f} bf"),
        ("Lost to kerf", f"{plan.kerf_bf:,.1f} bf"),
        ("Usable wood", f"{plan.wedge_bf:,.1f} bf"),
        ("Recovery", f"{plan.recovery * 100:,.1f}%"),
    )
    return table("This book's tree", ("", ""), rows, align="lr",
                 footer_rows=1,
                 note="Change any of the first three lines and every later "
                      "one moves with it.")


def plot_worked_dome(figure: Figure):
    """The dome those two trees produce."""
    result = bm.tree_first()
    rows = (
        ("Radius", f"{result.radius_in:,.2f} in"),
        ("Diameter", f"{result.diameter_ft:,.2f} ft"),
        ("Height at centre", f"{result.height_ft:,.2f} ft"),
        ("Floor", f"{result.floor_sqft:,.1f} sq ft"),
        ("Panels", f"{bm.frame_counts()[1]}"),
        ("Members", f"{result.struts_needed}"),
        ("Seams to close", f"{bm.panel_seam_count()}"),
        ("Longest member", f"{result.longest_member_in:,.2f} in"),
        ("Shortest member", f"{result.shortest_member_in:,.2f} in"),
        ("Timber in the frame", f"{result.timber_in_frame_ft:,.0f} ft"),
        ("Struts available", f"{result.struts_available}"),
        ("Struts spare", f"{result.spare_struts}"),
    )
    return table("The dome those two trees make", ("", ""), rows,
                 align="lr", footer_rows=2,
                 note="The spare eight are your margin for a stick that "
                      "splits, a butt cut that goes wrong, and the one "
                      "panel everybody builds backwards.")


def plot_worked_cutlist(figure: Figure):
    """The full cut list, one row per member class."""
    result = bm.tree_first()
    rows = []
    for index, item in enumerate(result.member_classes, start=1):
        rows.append((
            f"M{index}", item.edge_class, str(item.count),
            _fmt(item.length_in, 3), _fmt(item.bearing_length_in, 3),
            _fmt(item.inset_in, 3)))
    total_ft = result.timber_in_frame_ft
    rows.append(("", "total", str(sum(i.count for i in result.member_classes)),
                 f"{total_ft * 12:,.0f}", "", ""))
    return table(
        "The cut list",
        ("mark", "class", "count", "length in", "bearing in", "inset in"),
        tuple(rows), align="llrrrr", footer_rows=1,
        note="Cut to the length column. The bearing column is how much of "
             "the end actually lands on the next stick's side; the inset is "
             "how far the member sits back from the panel's own corner.")


def plot_worked_seams(figure: Figure):
    """The seam schedule: how many of each key to make."""
    from . import raw_wedge_bridge as bridge
    model = bridge.model()
    thickness = bm.declared("gasket_thickness_in")

    groups: dict[tuple, list] = {}
    for seam in model.seams:
        key = (seam.edge_type, round(float(seam.fold_angle_deg), 3),
               round(float(seam.raw_gap_angle_deg), 3))
        groups.setdefault(key, []).append(seam)

    rows = []
    for index, (key, seams) in enumerate(sorted(groups.items()), start=1):
        edge_type, fold, gap = key
        length_in = sum(
            float(((seam.end - seam.start) ** 2).sum() ** 0.5)
            for seam in seams)
        rows.append((
            f"K{index}", edge_type, str(len(seams)), f"{fold:.3f}",
            f"{gap:.3f}", _fmt(length_in / 12.0, 1)))
    total_ft = sum(float(v[5].replace(",", "")) for v in rows)
    rows.append(("", "all", str(len(model.seams)), "", "",
                 _fmt(total_ft, 1)))

    plan = wg.gasket_plan(bm.tree_first().radius_in, thickness)
    # The two columns are not independent: every seam's raw gap is the
    # sector angle less its fold angle. Checked here rather than asserted
    # in prose, because a book that states an identity should have run it.
    sector = 360.0 / bm.BOOK_TREE.sectors
    closes = all(abs(float(seam.fold_angle_deg)
                     + float(seam.raw_gap_angle_deg) - sector) < 1e-6
                 for seam in model.seams)
    identity = (f"Fold plus raw gap is {sector:.0f}° at every one of them -- "
                f"the sector angle. The key never fills more than one "
                f"wedge's worth of angle."
                if closes else
                "Fold and raw gap do not sum to the sector angle here; that "
                "is worth investigating before cutting keys.")
    return table(
        "The seam schedule: how many of each key",
        ("key", "edge", "seams", "fold deg", "raw gap deg", "length ft"),
        tuple(rows), align="llrrrr", footer_rows=1,
        note=f"{len(groups)} distinct keys close all {len(model.seams)} "
             f"seams. Make one of each to fit, then repeat it. The raw gap "
             f"column is the angle the key actually has to fill when both "
             f"faces are left exactly as split. {identity} Cross-check: the "
             f"pinwheel model reports {plan.interior_seams} interior seams "
             f"and {plan.rim_seams} rim edges over "
             f"{plan.total_length_ft:,.0f} feet.")


def plot_ripping_rhythm(figure: Figure):
    """What thirty struts in an afternoon looks like as a cumulative curve."""
    work = bm.fortnight()
    fig = new_figure(PAGE_W_IN, HALF_H_IN)
    axes = fig.add_axes([0.13, 0.20, 0.83, 0.68])

    hours = [h * 0.25 for h in range(int(work.ripping_hours * 4) + 1)]
    cumulative = [h * work.struts_per_hour for h in hours]
    axes.plot(hours, cumulative, color=STYLE.accent, linewidth=1.6)
    axes.axhline(work.struts_needed, color=STYLE.warn, linewidth=1.0,
                 linestyle="--")
    axes.annotate(f"{work.struts_needed} struts",
                  (0.5, work.struts_needed), xytext=(0, 5),
                  textcoords="offset points", fontsize=7.5, color=STYLE.warn)
    for afternoon in range(1, int(math.ceil(work.afternoons_of_ripping)) + 1):
        edge = afternoon * work.hours_per_afternoon
        if edge <= work.ripping_hours + 1e-9:
            axes.axvline(edge, color=STYLE.faint, linewidth=6.0, zorder=0)
            axes.annotate(f"day {afternoon}", (edge, 3), rotation=90,
                          fontsize=6.5, color=STYLE.muted, ha="right",
                          va="bottom")
    axes.set_xlabel("hours at the saw")
    axes.set_ylabel("struts cut")
    axes.set_title(f"{work.struts_per_hour:.0f} struts an hour, sustained")
    axes.set_xlim(0, work.ripping_hours)
    axes.set_ylim(0, work.struts_needed * 1.12)
    axes.text(0.0, -0.30,
              _wrap(f"{work.afternoons_of_ripping:.0f} afternoons of "
                    f"{work.hours_per_afternoon:.0f} hours. This is one "
                    "measured afternoon extrapolated in a straight line, "
                    "which is optimistic: it assumes the last hour of day "
                    "four goes like the first hour of day one.", 92),
              transform=axes.transAxes, fontsize=7.2, va="top",
              color=STYLE.muted, style="italic")
    return fig


def plot_jig_stages(figure: Figure):
    """The twelve jig stages, named by the simulator itself."""
    from . import raw_wedge_bridge as bridge
    stages = bridge.jig_stages()
    rows = tuple(
        (str(index + 1), str(stage[1] if len(stage) > 1 else stage[0]),
         _wrap(str(stage[2] if len(stage) > 2 else ""), 44))
        for index, stage in enumerate(stages))
    return table(
        "The twelve stages of the jig",
        ("#", "stage", "what happens"),
        rows, align="lll",
        note="Named by the simulator, so pressing 9 and 0 in the Raw Wedge "
             "Dome tool walks exactly this list.",
        full_page=True)


def plot_butt_setups(figure: Figure):
    """How few distinct saw setups the whole dome needs."""
    from . import raw_wedge_bridge as bridge
    sim = bridge.simulator()
    model = bridge.model()
    setups = sim.butt_cut_setups(model)
    rows = []
    for index, setup in enumerate(setups[:24], start=1):
        values = [str(setup.get(name, "")) for name in
                  ("members", "bevel_deg", "mitre_deg")]
        rows.append((str(index), *(
            f"{float(v):.2f}" if _isnum(v) else (v or "-") for v in values)))
    rows.append(("", f"{len(setups)} setups",
                 f"{bm.MEMBERS_IN_FRAME} members", ""))
    return table(
        "Distinct butt-cut setups in the whole dome",
        ("#", "members", "bevel deg", "mitre deg"),
        tuple(rows), align="lrrr", footer_rows=1,
        note=f"{len(setups)} setups for {bm.MEMBERS_IN_FRAME} members. That "
             "ratio is the whole argument for the pinwheel: you change the "
             "saw a handful of times, not a hundred and twenty.",
        full_page=True)


def _isnum(value) -> bool:
    try:
        float(value)
        return True
    except (TypeError, ValueError):
        return False


def plot_offcut_total(figure: Figure):
    """What the head overfit costs in wood, across the whole dome."""
    plan = bm.BOOK_TREE
    overfit_in = bm.declared("head_overfit_in")
    members = bm.MEMBERS_IN_FRAME
    offcut_in3 = overfit_in * plan.member_area_in2 * members
    offcut_bf = offcut_in3 / wg.CUBIC_INCHES_PER_BOARD_FOOT
    frame_bf = (bm.tree_first().timber_in_frame_ft * 12.0
                * plan.member_area_in2 / wg.CUBIC_INCHES_PER_BOARD_FOOT)
    rows = (
        ("Overfit per member", f"{overfit_in:,.1f} in"),
        ("Members", f"{members}"),
        ("Offcut length, all told",
         f"{overfit_in * members / 12.0:,.1f} ft"),
        ("Offcut volume", f"{offcut_bf:,.1f} bf"),
        ("Wood in the finished frame", f"{frame_bf:,.1f} bf"),
        ("Offcut as a share of the frame",
         f"{offcut_bf / frame_bf * 100:,.1f}%"),
        ("Struts that wood would have made",
         f"{offcut_bf / plan.bf_per_strut:,.1f}"),
    )
    return table(
        "What the tolerance costs",
        ("", ""), rows, align="lr", footer_rows=2,
        note="This is the price of never having to measure a head end. It "
             "is paid in wood, deliberately, and it is cheaper than the "
             "alternative -- which is a triangle that will not close "
             "because three small errors all pushed the same way.")


def plot_panel_variants(figure: Figure):
    """How many genuinely distinct panels the dome contains."""
    from . import raw_wedge_bridge as bridge
    sim = bridge.simulator()
    model = bridge.model()
    signatures: dict[tuple, int] = {}
    panels = len(model.topology.faces)
    for index in range(panels):
        signature = sim._panel_variant_signature(model, index)
        signatures[signature] = signatures.get(signature, 0) + 1
    ordered = sorted(signatures.values(), reverse=True)
    rows = tuple(
        (f"type {index}", str(count), f"{count / panels * 100:.0f}%")
        for index, count in enumerate(ordered, start=1))
    rows += (("all", str(panels), "100%"),)
    return table(
        "Distinct panel types",
        ("type", "panels", "share"), rows, align="lrr", footer_rows=1,
        note=f"{len(ordered)} genuinely different panels across {panels}. "
             "Build one of each carefully, then repeat. The types differ in "
             "their seam angles, not in their member lengths.")


def plot_sheet_count(figure: Figure):
    """How much shell there is, and how many sheets it takes."""
    from . import dome_costing
    radius = bm.tree_first().radius_in
    shell = dome_costing.shell_sqft(radius)
    upper = dome_costing.upper_shell_sqft(radius)
    per_sheet = dome_costing.SQFT_PER_OSB
    waste = dome_costing.FLOOR_SHEET_WASTE
    rows = (
        ("Shell area", f"{shell:,.0f} sq ft"),
        ("Upper shell (roof proper)", f"{upper:,.0f} sq ft"),
        ("One sheet covers", f"{per_sheet:,.0f} sq ft"),
        ("Sheets, if nothing were wasted",
         f"{shell / per_sheet:,.1f}"),
        ("Triangles cut from rectangles",
         f"x{waste:,.2f} waste factor"),
        ("Sheets to buy",
         f"{math.ceil(shell / per_sheet * waste)}"),
    )
    return table(
        "Closing the shell",
        ("", ""), rows, align="lr", footer_rows=1,
        note="The waste factor is the honest part: you are cutting "
             "triangles out of rectangles, and no nesting makes that free. "
             "Nesting two panels per sheet gets closer to the ideal than "
             "cutting one at a time.")


def plot_headroom_map(figure: Figure):
    """Floor area against the floor you can actually stand up on."""
    import numpy as np
    result = bm.tree_first()
    radius_ft = result.radius_in / 12.0

    fig = new_figure(PAGE_W_IN, HALF_H_IN + 0.6)
    axes = fig.add_axes([0.13, 0.22, 0.60, 0.68])
    heights = np.linspace(0.1, radius_ft * 0.999, 220)
    # On a hemisphere of radius R, headroom h is available out to a
    # horizontal distance sqrt(R^2 - h^2) from the centre.
    usable = math.pi * (radius_ft ** 2 - heights ** 2)
    axes.plot(usable, heights, color=STYLE.accent, linewidth=1.6)
    axes.fill_betweenx(heights, 0, usable, color=STYLE.faint)
    total = math.pi * radius_ft ** 2
    axes.axvline(total, color=STYLE.rule, linewidth=0.8, linestyle=":")
    for standing, label, colour in ((6.5, "6 ft 6 in", STYLE.warn),
                                    (5.0, "5 ft", STYLE.good)):
        if standing < radius_ft:
            area = math.pi * (radius_ft ** 2 - standing ** 2)
            axes.plot([area], [standing], "o", color=colour, markersize=4)
            axes.annotate(f"{label}: {area:,.0f} sq ft",
                          (area, standing), xytext=(6, 0),
                          textcoords="offset points", fontsize=7,
                          color=colour, va="center")
    axes.set_xlabel("floor with at least this headroom (sq ft)")
    axes.set_ylabel("headroom (ft)")
    axes.set_title(f"{total:,.0f} sq ft of floor. Rather less of it "
                   "lets you stand.")
    axes.set_xlim(0, total * 1.05)
    axes.set_ylim(0, radius_ft * 1.05)
    axes.text(0.0, -0.30,
              _wrap("A hemisphere's floor is honest about its area and "
                    "dishonest about its use. This is the number to quote "
                    "when somebody compares a dome to a rectangle: not the "
                    "floor, the floor you can stand up on.", 92),
              transform=axes.transAxes, fontsize=7.2, va="top",
              color=STYLE.muted, style="italic")
    return fig


def plot_money_spent(figure: Figure):
    """Cash out, itemised, separated from what was avoided."""
    saw = bm.declared("saw_price_usd")
    rows = (
        ("Chainsaw", f"${saw:,.0f}", "priced"),
        ("Fuel, bar oil, files", "$—", "to log"),
        ("Fasteners", "$—", "to log"),
        ("Seam keys / gasket stock", "$—", "to log"),
        ("Sheathing", "$—", "to log"),
        ("Footing", "$—", "to log"),
        ("Timber", "$0", "two trees"),
    )
    return table(
        "What was actually spent",
        ("item", "cost", "source"), rows, align="lrl", footer_rows=1,
        note="The dashes are real: these were not logged at the time, and "
             "this book will not fill them in with plausible numbers. The "
             "last line is the one that matters -- the structural timber "
             "cost nothing but the fuel to cut it.")


def plot_strut_value(figure: Figure):
    """One strut, valued three ways, with the disagreement shown."""
    plan = bm.BOOK_TREE
    work = bm.fortnight(plan)
    nominal = work.substitute_value_usd(plan.equivalent_two_by_fours)
    dressed = work.substitute_value_usd(plan.equivalent_dressed_two_by_fours)
    # The brief's own figure is a declared constant, not a literal typed
    # here, and the rate it implies is derived from it at this build's
    # ripping pace rather than declared alongside it -- two numbers that
    # can disagree are two numbers that eventually will.
    brief = bm.declared("brief_strut_value_usd")
    brief_rate = brief * work.struts_per_hour
    rows = (
        (f"Against a nominal 2x4 "
         f"({plan.member_area_in2 / plan.equivalent_two_by_fours:,.2f} sq in)",
         f"{plan.equivalent_two_by_fours:,.2f} boards", f"${nominal:,.2f}"),
        (f"Against a dressed 2x4 "
         f"({plan.member_area_in2 / plan.equivalent_dressed_two_by_fours:,.2f}"
         f" sq in)",
         f"{plan.equivalent_dressed_two_by_fours:,.2f} boards",
         f"${dressed:,.2f}"),
        ("By board foot", f"{plan.bf_per_strut:,.2f} bf", "market varies"),
        ("Implied rate, nominal", f"{work.struts_per_hour:,.0f}/hr",
         f"${work.hourly_rate_usd(plan.equivalent_two_by_fours):,.2f}/hr"),
        ("Implied rate, dressed", f"{work.struts_per_hour:,.0f}/hr",
         f"${work.hourly_rate_usd(plan.equivalent_dressed_two_by_fours):,.2f}"
         f"/hr"),
        ("The brief's estimate", f"${brief:,.2f}/strut",
         f"${brief_rate:,.2f}/hr"),
    )
    return table(
        "One strut, valued three ways",
        ("basis", "quantity", "value"), rows, align="lrr", footer_rows=1,
        note="The last row is the figure this project started from, and it "
             f"is the highest -- ${brief:,.2f} a strut, reached by doubling "
             "a volume ratio for safety. The rows above compute the ratio "
             "from the actual cross-section instead. Note which way the "
             "honest correction runs: a dressed 2x4 is smaller than its "
             "name, so a strut replaces more of them, and the *dressed* "
             "comparison is the higher of the two computed rows, not the "
             "lower. Both computed rates are real; neither is money anybody "
             "has been paid.")


def plot_hours_log(figure: Figure):
    """Where fourteen days went, as a stacked bar."""
    work = bm.fortnight()
    phases = (
        ("Saw setup", 1, STYLE.muted),
        ("Felling", 2, STYLE.bark),
        ("Bucking", 2, STYLE.wood_dark),
        ("Ripping", int(round(work.afternoons_of_ripping)), STYLE.wood),
        ("Building the jig", 1, STYLE.key),
        ("Panels", 3, STYLE.accent),
        ("Raising", 2, STYLE.good),
    )
    fig = new_figure(PAGE_W_IN, HALF_H_IN)
    axes = fig.add_axes([0.24, 0.20, 0.72, 0.68])
    names = [p[0] for p in phases]
    days = [p[1] for p in phases]
    colours = [p[2] for p in phases]
    axes.barh(range(len(phases)), days, color=colours, height=0.62)
    axes.set_yticks(range(len(phases)))
    axes.set_yticklabels(names, fontsize=8)
    axes.invert_yaxis()
    axes.set_xlabel("days")
    total = sum(days)
    axes.set_title(f"The fortnight: {total} days accounted for")
    for index, value in enumerate(days):
        axes.annotate(f"{value}", (value, index), xytext=(4, 0),
                      textcoords="offset points", va="center", fontsize=7.5,
                      color=STYLE.ink)
    axes.set_xlim(0, max(days) * 1.25)
    axes.text(0.0, -0.28,
              _wrap(f"Ripping is {int(round(work.afternoons_of_ripping))} "
                    "days of the fourteen, and it is the part everybody "
                    "assumes is the whole job. The panels take as long, and "
                    "the jig day pays for both.", 92),
              transform=axes.transAxes, fontsize=7.2, va="top",
              color=STYLE.muted, style="italic")
    return fig


def plot_frequency_compare(figure: Figure):
    """What each frequency asks of the woodpile."""
    plan = bm.BOOK_TREE
    result = bm.tree_first()
    width = plan.member_width_in
    classes = wg.member_classes(result.radius_in, width)
    rows = [(
        "2V (this book)", "40", str(bm.MEMBERS_IN_FRAME),
        str(len(classes)), _fmt(max(i.length_in for i in classes), 1),
        _fmt(min(i.length_in for i in classes), 1))]
    rows.append(("3V", "75", "165", "3 edge classes", "—", "—"))
    rows.append(("4V", "160", "300", "6 edge classes", "—", "—"))
    return table(
        "Frequency, and what it asks of the woodpile",
        ("frequency", "panels", "members", "lengths", "longest in",
         "shortest in"),
        tuple(rows), align="lrrlrr",
        note="Only the 2V row is computed: this repository solves the 2V "
             "hemisphere, and the book will not print numbers for frames it "
             "has not built. The 3V and 4V counts are standard geodesic "
             "results; their member lengths depend on a solve that is not "
             "here yet, and the dashes say so.")


def plot_wedge_versus_board(figure: Figure):
    """The head-to-head, with the columns that lose kept in."""
    versus = bm.wedge_versus_board(8.0)
    wedge, board = versus.wedge, versus.board
    rows = (
        ("Cross-section area", f"{wedge.area_in2:.2f} in2",
         f"{board.area_in2:.2f} in2", f"{versus.area_ratio:.2f}x"),
        ("Depth", f"{wedge.depth_in:.2f} in", f"{board.depth_in:.2f} in",
         f"{wedge.depth_in / board.depth_in:.2f}x"),
        ("Width", f"{wedge.width_in:.2f} in", f"{board.width_in:.2f} in",
         f"{wedge.width_in / board.width_in:.2f}x"),
        ("Second moment, strong", f"{wedge.strong_i_in4:.2f} in4",
         f"{board.strong_i_in4:.2f} in4",
         f"{versus.stiffness_ratio:.2f}x"),
        ("Section modulus, strong", f"{wedge.strong_s_in3:.2f} in3",
         f"{board.strong_s_in3:.2f} in3", f"{versus.strength_ratio:.2f}x"),
        ("Same board laid flat", f"{wedge.strong_i_in4:.2f} in4",
         f"{board.weak_i_in4:.2f} in4",
         f"{versus.flat_stiffness_ratio:.2f}x"),
    )
    return table(
        'One eighth of an 8" log against a dressed 2x4',
        ("", "wedge", "2x4 on edge", "ratio"),
        rows, align="lrrr", footer_rows=1,
        note="The wedge wins on area and loses on bending strength, and "
             "both are printed. Area is what an axial member trades on; "
             "section modulus is what a beam trades on. In a triangulated "
             "frame the members are mostly axial, which is the argument -- "
             "but panels do see wind and snow, and there the last two rows "
             "are the ones that matter. Against the same board laid flat, "
             "which is how a lot of framing ends up loaded, the wedge is "
             "far stiffer.")


def plot_shaving_cost(figure: Figure):
    """What planing the seam faces flat actually removes."""
    plan = bm.BOOK_TREE
    rows = []
    for index, row in enumerate(bm.shaving_plan(2.0), start=1):
        rows.append((
            f"K{index}", str(row.seams), f"{row.fold_angle_deg:.3f}",
            f"{row.half_fold_deg:.3f}", f"{row.raw_face_deg:.1f}",
            f"{row.correction_deg:.3f}", f"{row.depth_in:.3f}",
            f"{row.as_fraction_of_depth * 100:.1f}%"))
    return table(
        "What the shaved-flat option costs, over a 2-inch mating land",
        ("key", "seams", "fold", "half fold", "raw face", "correct",
         "cut in", "of depth"),
        tuple(rows), align="lrrrrrrr",
        note=f"The raw split face already sits at "
             f"{180.0 / plan.sectors:.1f} degrees off the member's own "
             f"centreline, and a flat key wants half the seam's fold angle. "
             f"The difference is all that has to come off -- under half an "
             f"inch, on a member {plan.member_depth_in:.2f} inches deep. "
             "That is the whole price of the option that makes one key "
             "profile fit everywhere.")


def plot_flat_rate(figure: Figure):
    """Three lines: the parts list, the stick, and the floor.

    This is the whole scaling argument in one picture, and it only works
    if all three are indexed to the same dome, so the reader is comparing
    multiples and not units.  Everything is swept out of
    :class:`franken_economics.DomeSize` rather than plotted from a formula,
    so the curve cannot drift from the table on the facing page.
    """
    from . import franken_economics as fe

    base = fe.DomeSize(10.0 * 12.0 / 2.0)
    # Stop the sweep on the last row of the table, so the multiples written
    # at the right-hand end are the ones the facing page prints.
    span = [6.0 + 0.5 * step for step in range(49)]      # 6 ft to 30 ft
    sizes = [fe.DomeSize(feet * 12.0 / 2.0) for feet in span]
    floor = [s.floor_area_sqft / base.floor_area_sqft for s in sizes]
    stick = [s.strut_feet / base.strut_feet for s in sizes]
    parts = [s.struts / base.struts for s in sizes]

    fig = new_figure(PAGE_W_IN, HALF_H_IN)
    axes = fig.add_axes([0.11, 0.20, 0.72, 0.66])
    axes.plot(span, floor, color=STYLE.accent, linewidth=2.0,
              label="floor you get")
    axes.plot(span, stick, color=STYLE.wood, linewidth=2.0,
              label="stick you cut")
    axes.plot(span, parts, color=STYLE.good, linewidth=2.0,
              label="parts to handle")
    axes.axhline(1.0, color=STYLE.rule, linewidth=0.6, zorder=0)

    large = fe.flat_rate_table()[-1]
    ends = (
        (large.floor_area_sqft / base.floor_area_sqft, STYLE.accent),
        (large.strut_feet / base.strut_feet, STYLE.wood),
        (large.struts / base.struts, STYLE.good),
    )
    for value, colour in ends:
        axes.annotate(f"x{value:.0f}", (large.diameter_ft, value),
                      xytext=(7, 0), textcoords="offset points",
                      fontsize=8.5, color=colour, weight="bold",
                      va="center")

    axes.set_xlabel("diameter, feet")
    axes.set_ylabel(f"multiple of the {base.diameter_ft:.0f} ft dome")
    axes.set_title("What actually grows when a dome gets bigger")
    axes.set_xlim(span[0], span[-1] + 2.0)
    axes.set_ylim(0, max(floor) * 1.08)
    axes.legend(loc="upper left", fontsize=7.5, frameon=False)
    axes.text(0.0, -0.26,
              _wrap("Indexed to the "
                    f"{base.diameter_ft:.0f} foot dome. Floor area follows "
                    "the square of the diameter, the stick follows the "
                    "diameter, and the parts list does not follow it at all "
                    f"-- {base.struts} members, {base.brackets} brackets and "
                    f"{base.screws} screws at every point on this chart. The "
                    "gap between the blue line and the green one is the "
                    "whole argument.", 92),
              transform=axes.transAxes, fontsize=7.2, va="top",
              color=STYLE.muted, style="italic")
    return fig


def plot_solo_band(figure: Figure):
    """Where one pair of hands runs out, and what that costs in diameter."""
    from . import franken_economics as fe

    band = fe.solo_band()
    span = [6.0 + 0.5 * step for step in range(53)]
    sizes = [fe.DomeSize(feet * 12.0 / 2.0) for feet in span]
    longs = [s.long_member_ft for s in sizes]
    shorts = [s.short_member_ft for s in sizes]

    fig = new_figure(PAGE_W_IN, HALF_H_IN)
    axes = fig.add_axes([0.11, 0.20, 0.72, 0.66])
    axes.axvspan(span[0], band.diameter_ft, color=STYLE.faint, zorder=0)
    axes.plot(span, longs, color=STYLE.wood_dark, linewidth=2.0,
              label="longest stick to cut")
    axes.plot(span, shorts, color=STYLE.wood, linewidth=1.6,
              linestyle="--", label="shortest stick to cut")
    axes.axhline(band.member_ft, color=STYLE.warn, linewidth=1.2)
    axes.annotate(f"declared limit, {band.member_ft:.0f} ft",
                  (span[0] + 0.4, band.member_ft), xytext=(0, 4),
                  textcoords="offset points", fontsize=7.5,
                  color=STYLE.warn, weight="bold")
    axes.axvline(band.diameter_ft, color=STYLE.warn, linewidth=1.0,
                 linestyle=":")

    for size in fe.flat_rate_table():
        inside = size.within_solo_reach
        axes.plot([size.diameter_ft], [size.long_member_ft], marker="o",
                  markersize=5.0,
                  color=STYLE.good if inside else STYLE.warn, zorder=4)
        # Above the solid line: the gap between the two members is too
        # narrow to label into, and the first draft put "20 ft" straight
        # through the short-member dashes.
        axes.annotate(f"{size.diameter_ft:.0f} ft",
                      (size.diameter_ft, size.long_member_ft),
                      xytext=(0, 7), textcoords="offset points",
                      fontsize=7.2, color=STYLE.ink, ha="center")

    axes.set_xlabel("diameter, feet")
    axes.set_ylabel("member length, feet")
    axes.set_title(f"One pair of hands reaches {band.diameter_ft:.1f} feet")
    axes.set_xlim(span[0], span[-1])
    axes.set_ylim(0, max(longs) * 1.08)
    axes.legend(loc="upper left", fontsize=7.5, frameon=False)
    axes.text(0.0, -0.26,
              _wrap(f"The {band.member_ft:.0f} foot limit is declared, not "
                    "solved: it is the longest stick this builder will carry, "
                    "stand both ends of and set without help. Everything "
                    "downstream of it is computed, and computed by the wedge "
                    "solver rather than by scaling a chord -- a pinwheel "
                    "member is inset from the vertex by an amount that "
                    "depends on its width, so these curves are not straight "
                    "lines through the origin. A "
                    f"{band.member_ft:.0f} foot cut member is a dome "
                    f"{band.diameter_ft:.1f} feet across, "
                    f"{band.floor_area_sqft:.0f} square feet of floor, with "
                    f"{band.short_member_ft:.2f} feet as the other stick -- "
                    "which is also the dome two trees yield. Inside the "
                    "shaded band the parts list, the operations and the "
                    "effort do not change.", 92),
              transform=axes.transAxes, fontsize=7.2, va="top",
              color=STYLE.muted, style="italic")
    return fig


def plot_process_counts(figure: Figure):
    """Every operation's repetition count, indexed, across four diameters.

    The point of the picture is the thing that looks like a drawing error:
    seven of the nine lines land exactly on top of each other at 1.0, so
    the chart shows one flat line where there are seven.  That is said in
    the label rather than fixed by jittering them apart, because the
    superposition *is* the result.  Which operations are flat is read from
    :data:`franken_economics.PROCESSES`, not decided here.
    """
    from . import franken_economics as fe

    span = [10.0 + 0.5 * step for step in range(41)]     # 10 ft to 30 ft
    sizes = [fe.DomeSize(feet * 12.0 / 2.0) for feet in span]
    base = sizes[0]

    fig = new_figure(PAGE_W_IN, HALF_H_IN)
    axes = fig.add_axes([0.11, 0.20, 0.72, 0.66])

    flat = [step for step in fe.PROCESSES if step.flat]
    moving = [step for step in fe.PROCESSES if not step.flat]

    for step in flat:
        axes.plot(span,
                  [step.repetitions(s) / step.repetitions(base)
                   for s in sizes],
                  color=STYLE.good, linewidth=2.0, zorder=3)
    for step, colour, style in zip(moving,
                                   (STYLE.wood, STYLE.accent),
                                   ("-", "-")):
        axes.plot(span,
                  [step.repetitions(s) / step.repetitions(base)
                   for s in sizes],
                  color=colour, linewidth=2.0, linestyle=style,
                  label=f"{step.name.lower()} ({step.unit})", zorder=4)

    axes.plot([], [], color=STYLE.good, linewidth=2.0,
              label=f"{len(flat)} operations, superimposed")
    axes.axhline(1.0, color=STYLE.rule, linewidth=0.6, zorder=0)

    for step, colour in zip(moving, (STYLE.wood, STYLE.accent)):
        end = step.repetitions(sizes[-1]) / step.repetitions(base)
        axes.annotate(f"x{end:.0f}", (span[-1], end), xytext=(6, 0),
                      textcoords="offset points", fontsize=8.5,
                      color=colour, weight="bold", va="center")
    axes.annotate("x1", (span[-1], 1.0), xytext=(6, 0),
                  textcoords="offset points", fontsize=8.5,
                  color=STYLE.good, weight="bold", va="center")

    axes.set_xlabel("diameter, feet")
    axes.set_ylabel(f"multiple of the {base.diameter_ft:.0f} ft dome")
    axes.set_title("How often each of the nine happens")
    axes.set_xlim(span[0], span[-1] + 2.2)
    axes.set_ylim(0, 9.6)
    axes.legend(loc="upper left", fontsize=7.5, frameon=False)
    counts = ", ".join(
        f"{step.repetitions(base):,.0f} {step.unit}"
        for step in flat)
    axes.text(0.0, -0.26,
              _wrap(f"{len(flat)} of the {len(fe.PROCESSES)} operations are "
                    "drawn here and only one line is visible, because they "
                    "are identical: " + counts + ", at every diameter on "
                    "this chart. They are the operations that work on "
                    f"joints, and the joint count is fixed. The other "
                    f"{len(moving)} touch raw material and area instead -- "
                    "felling follows the linear feet of cut member, "
                    "glassing follows the shell, and the shell goes as the "
                    "square. The step in the felling line is a whole tree.",
                    92),
              transform=axes.transAxes, fontsize=7.2, va="top",
              color=STYLE.muted, style="italic")
    return fig


def plot_process_table(figure: Figure):
    """The nine operations against four diameters, count by count.

    The chart on the facing page shows that seven lines coincide; this
    prints what they coincide *at*, because a builder ordering brackets
    wants the number and not the shape of it.  Both read the same
    :data:`franken_economics.PROCESSES`.
    """
    from . import franken_economics as fe

    sizes = fe.flat_rate_table()
    headers = ("operation", "tool", "counted in") + tuple(
        f"{size.diameter_ft:.0f} ft" for size in sizes)
    rows = []
    for index, step in enumerate(fe.PROCESSES):
        counts = tuple(
            f"{size.process_counts[index].count:,.0f}" for size in sizes)
        rows.append((step.name, step.tool, step.unit) + counts)

    flat = sum(1 for step in fe.PROCESSES if step.flat)
    return table(
        "What each of the nine costs you, at four diameters",
        headers, tuple(rows),
        align="lll" + "r" * len(sizes),
        note=(f"{flat} of the {len(fe.PROCESSES)} rows are constant all the "
              "way across, and they are the rows that work on joints: the "
              "joint count is fixed by the frame, and the frame is the same "
              "frame at every diameter. Felling follows the linear feet of "
              "cut member, so it steps a whole tree at a time; glassing "
              "follows the shell, which goes as the square of the diameter. "
              "Nothing else on the list notices how big the dome is."),
        key=figure.key)


def plot_rip_payback(figure: Figure):
    """What a saving at one bench returns as the run of domes lengthens.

    Measured against a whole ripping stage rather than in hours, because
    hours are abstract and "you have been given back the ripping of one
    dome" is not.  The improvement and the length of the run are the same
    declared pair the chapter quotes, read from :mod:`book_tokens` so the
    prose and the picture cannot disagree.
    """
    from . import book_tokens as bt

    work = bm.fortnight()
    fraction = bt.RIP_GAIN_FRACTION
    run = bt.RIP_GAIN_BUILDS
    builds = list(range(1, run * 2 + 1))
    hours = [work.improvement(fraction, n).hours_total for n in builds]

    fig = new_figure(PAGE_W_IN, HALF_H_IN)
    axes = fig.add_axes([0.11, 0.20, 0.72, 0.66])
    axes.plot(builds, hours, color=STYLE.accent, linewidth=2.0,
              marker="o", markersize=3.0,
              label=f"{fraction * 100:.0f}% faster at the rip")

    # The stage lines are labelled on the right, clear of the legend: the
    # first draft put "2 whole ripping stages" straight through it.
    stage = work.ripping_hours
    for multiple in (1, 2):
        axes.axhline(stage * multiple, color=STYLE.rule, linewidth=0.8,
                     linestyle=":", zorder=0)
        axes.annotate(f"{multiple} whole ripping "
                      f"stage{'s' if multiple > 1 else ''}"
                      f" ({stage * multiple:.0f} h)",
                      (builds[-1], stage * multiple), xytext=(-2, 5),
                      textcoords="offset points", fontsize=7.2,
                      color=STYLE.muted, ha="right")

    payoff = work.improvement(fraction, run)
    axes.plot([run], [payoff.hours_total], marker="o", markersize=6.0,
              color=STYLE.warn, zorder=5)
    axes.annotate(f"{run} domes: {payoff.hours_total:.0f} h",
                  (run, payoff.hours_total), xytext=(8, -12),
                  textcoords="offset points", fontsize=7.8,
                  color=STYLE.warn, weight="bold")

    axes.set_xlabel("domes built")
    axes.set_ylabel("hours returned")
    axes.set_title(f"{payoff.seconds_per_strut:.0f} seconds a member, "
                   "compounded")
    axes.set_xlim(0, builds[-1] + 0.5)
    axes.set_ylim(0, hours[-1] * 1.12)
    axes.legend(loc="lower right", fontsize=7.5, frameon=False)
    axes.text(0.0, -0.26,
              _wrap("The ripping is "
                    f"{work.ripping_hours:.0f} hours of the fortnight and "
                    f"moves {work.struts_needed} members, which is "
                    f"{work.minutes_per_strut:.0f} minutes each. Taking "
                    f"{fraction * 100:.0f} per cent off that is "
                    f"{payoff.seconds_per_strut:.0f} seconds a member and "
                    f"{work.improvement(fraction).hours_per_build:.1f} hours "
                    f"on one dome. Over {run} it is "
                    f"{payoff.hours_total:.0f} hours -- "
                    f"{payoff.rip_stages:.0f} entire ripping stage, handed "
                    "back. The member count does not change with diameter, "
                    "so neither does the refund: small domes pay it too.",
                    92),
              transform=axes.transAxes, fontsize=7.2, va="top",
              color=STYLE.muted, style="italic")
    return fig


def _ledger():
    """The costed build the fuel chapter reads, at the pinned serial."""
    from . import book_tokens as bt
    from . import energetics as en
    return en.build_energy(bt.CALORIE_SERIAL, bt.CALORIE_CREW)


_MOTION_LABEL = {
    "walk_out": "walk to the pile",
    "lift": "lift",
    "carry": "carry",
    "position": "place",
    "fasten": "fasten",
    "recover": "stand up",
    "pause": "recovery allowance",
}


def plot_motion_split(figure: Figure):
    """Each motion's share of the clock beside its share of the fuel.

    Drawn as a pair rather than as the fuel alone, because the fuel bar on
    its own would let a reader think fastening is expensive per minute.  It
    is not especially: it is 3.5 METs.  It dominates the ledger by filling
    the day, and only the *gap* between the two bars is intensity.  Saying
    that with one bar is not possible, so there are two.
    """
    energy = _ledger()
    fuel = energy.by_motion()
    clock = energy.seconds_by_motion()
    order = sorted(fuel, key=lambda name: -fuel[name])

    fig = new_figure(PAGE_W_IN, HALF_H_IN)
    axes = fig.add_axes([0.24, 0.20, 0.62, 0.66])

    rows = list(range(len(order)))
    height = 0.36
    fuel_share = [fuel[name] / energy.kcal_per_worker * 100.0 for name in order]
    time_share = [clock[name] / energy.seconds_per_worker * 100.0
                  for name in order]

    axes.barh([r + height / 2 for r in rows], fuel_share, height=height,
              color=STYLE.warn, label="share of the food energy")
    axes.barh([r - height / 2 for r in rows], time_share, height=height,
              color=STYLE.wood, label="share of the clock")

    for row, (food_pct, time_pct) in enumerate(zip(fuel_share, time_share)):
        for offset, value, colour in ((height / 2, food_pct, STYLE.warn),
                                      (-height / 2, time_pct, STYLE.wood)):
            if value < 0.35:
                continue
            # A tenth of a per cent matters down here: the first draft
            # printed "0%" against bars that are the whole reason for the
            # chapter.
            shown = f"{value:.0f}%" if value >= 10.0 else f"{value:.1f}%"
            axes.annotate(shown, (value, row + offset),
                          xytext=(4, 0), textcoords="offset points",
                          fontsize=7.4, color=colour, va="center")

    axes.set_yticks(rows)
    axes.set_yticklabels([_MOTION_LABEL[name] for name in order], fontsize=8.0)
    axes.invert_yaxis()
    axes.set_xlabel("per cent of one worker's build")
    axes.set_title("Where the day goes, and where the fuel goes")
    axes.set_xlim(0, 100)
    axes.legend(loc="lower right", fontsize=7.5, frameon=False)

    fasten_food = fuel["fasten"] / energy.kcal_per_worker * 100.0
    fasten_time = clock["fasten"] / energy.seconds_per_worker * 100.0
    handling = sum(fuel[name] for name in ("lift", "carry", "walk_out")
                   ) / energy.kcal_per_worker * 100.0
    axes.text(0.0, -0.26,
              _wrap(f"Fastening is {fasten_time:.0f} per cent of the clock "
                    f"and {fasten_food:.0f} per cent of the fuel. The "
                    f"{fasten_food - fasten_time:.0f} points between those "
                    "two bars are the only part of it that is intensity; "
                    "the rest is simply where the day goes. The recovery "
                    "allowance runs the other way, costing less fuel than "
                    "clock, because standing still is cheap. Lifting, "
                    "carrying and walking together come to "
                    f"{handling:.1f} per cent of the food, which is the "
                    "finding that decides what is worth designing out.", 92),
              transform=axes.transAxes, fontsize=7.2, va="top",
              color=STYLE.muted, style="italic")
    return fig


def plot_motion_efficiency(figure: Figure):
    """How much of each motion's fuel became height, against the ceiling.

    The whole-build figure and the lift's figure are both true and two
    orders of magnitude apart, which reads as a contradiction until they
    are drawn on the same axis with muscle's own limit on it.  The lift is
    a normal human lift.  The build average is small because a build is
    hardly ever lifting.
    """
    from . import energetics as en

    energy = _ledger()
    shares = energy.motion_efficiency()
    order = sorted(shares, key=lambda name: -shares[name])

    fig = new_figure(PAGE_W_IN, HALF_H_IN)
    axes = fig.add_axes([0.24, 0.20, 0.62, 0.66])

    rows = list(range(len(order)))
    values = [shares[name] * 100.0 for name in order]
    axes.barh(rows, values, height=0.55, color=STYLE.key)
    for row, value in zip(rows, values):
        axes.annotate("nothing" if value < 0.005 else f"{value:.2f}%",
                      (value, row), xytext=(4, 0),
                      textcoords="offset points", fontsize=7.4,
                      color=STYLE.muted if value < 0.005 else STYLE.ink,
                      va="center")

    ceiling = en.CONCENTRIC_EFFICIENCY * 100.0
    axes.axvline(ceiling, color=STYLE.rule, linewidth=0.9, linestyle=":")
    axes.annotate(f"what muscle can convert at best ({ceiling:.0f}%)",
                  (ceiling, rows[-1]), xytext=(-4, 0),
                  textcoords="offset points", fontsize=7.2,
                  color=STYLE.muted, ha="right", va="center")

    average = energy.mechanical_fraction * 100.0
    axes.axvline(average, color=STYLE.warn, linewidth=1.2)
    # Set out in a blank row below the bars, with a leader back to the
    # line. Against the lift it reads as a label for the lift; level with a
    # bar the leader runs through that bar's "nothing". Both were drawn and
    # looked at, which is why there is a spare row here.
    below = rows[-1] + 0.85
    axes.annotate(f"whole build: {average:.1f}%", xy=(average, below),
                  xytext=(ceiling * 0.22, below), textcoords="data",
                  fontsize=7.4, color=STYLE.warn, weight="bold",
                  va="center",
                  arrowprops=dict(arrowstyle="->", color=STYLE.warn,
                                  linewidth=0.9, shrinkB=1.0))

    axes.set_yticks(rows)
    axes.set_yticklabels([_MOTION_LABEL[name] for name in order], fontsize=8.0)
    axes.invert_yaxis()
    axes.set_ylim(rows[-1] + 1.3, rows[0] - 0.6)
    axes.set_xlabel("per cent of that motion's fuel that became height")
    axes.set_title("What actually went upward")
    axes.set_xlim(0, ceiling * 1.12)
    axes.text(0.0, -0.26,
              _wrap("The lift converts "
                    f"{shares['lift'] * 100:.1f} per cent, which is an "
                    "ordinary human lift and not far off the best a muscle "
                    "can do. The build converts "
                    f"{average:.1f} per cent, because across "
                    f"{energy.hours_per_worker:.0f} hours it is hardly ever "
                    f"lifting. Put the other way up: "
                    f"{energy.fuel_per_lifting_kcal:,.0f} calories are "
                    "burned for every one that ends up as height. Fastening "
                    "raises nothing at all, and it is most of the build.",
                    92),
              transform=axes.transAxes, fontsize=7.2, va="top",
              color=STYLE.muted, style="italic")
    return fig


def plot_station_ledger(figure: Figure):
    """Every station of the line, with what it costs a body to pass through."""
    energy = _ledger()
    stages = sorted(energy.by_stage().items(), key=lambda kv: -kv[1]["kcal"])
    rows = tuple(
        (name, f"{row['elements']:,.0f}", f"{row['kg']:,.0f}",
         f"{row['seconds'] / 3600.0:,.1f}", f"{row['kcal']:,.0f}",
         _fmt(row["kcal"] / energy.kcal_per_worker * 100.0, 1))
        for name, row in stages)
    rows += ((
        "whole build", f"{len(energy.elements):,.0f}",
        f"{energy.total_mass_kg:,.0f}", f"{energy.hours_per_worker:,.1f}",
        f"{energy.kcal_per_worker:,.0f}", "100.0"),)
    # The layers that go on over the frame, against the frame. The grouping
    # and the arithmetic live in energetics.SKIN_STAGES, because the chapter
    # quotes these same two multiples in prose.
    return table(
        "One building, counted in parts, hours and calories",
        ("station", "parts", "kg", "hours", "kcal", "% fuel"),
        rows, align="lrrrrr",
        note="Per worker, for a crew of "
             f"{energy.crew}. The hours are task time including the "
             "recovery allowance; the calories are what a "
             f"{energy.body_mass:.0f} kg body spends doing them. The order "
             "is by fuel, and it is not the order of mass. The layers that "
             f"go on over the frame weigh "
             f"{energy.skin_versus_frame('kg'):.1f} times what the frame "
             f"weighs and cost {energy.skin_versus_frame('kcal'):.1f} times "
             "its fuel -- because there are more parts to fasten, and every "
             "fastening is time.",
        full_page=True, footer_rows=1)


# ----------------------------------------------------------------------
# Envelope: the dome against an equal-floor box
# ----------------------------------------------------------------------

def _envelopes():
    """Both buildings at the book's own floor area, not the video's.

    :mod:`dome_advantage` defaults to a round 314 sq ft chosen for a
    campaign film. The book's dome came out of two pines at 365, and
    ``book_tokens.book_floor_sqft`` is the one place that says so. These
    plots and the ``skin.*`` tokens both call it, which is the only reason
    a caption and a paragraph can be trusted to agree.
    """
    from . import book_tokens as bt
    from . import dome_advantage as adv
    floor = bt.book_floor_sqft()
    return floor, adv.dome_envelope(floor), adv.box_envelope(floor)


def plot_envelope_compare(figure: Figure):
    """The two buildings in elevation, to one scale, with their skins.

    Drawn rather than tabulated because the argument is a shape argument.
    The box is taller at the ridge and squarer everywhere, and the reason
    it costs more skin is visible before any number is read.

    The headroom line is on here for the opposite reason: it is the part
    of the comparison that does not flatter the dome, and leaving it off
    would make this a sales drawing.
    """
    from . import dome_advantage as adv

    floor, dome, box = _envelopes()
    radius = adv.dome_radius_ft(floor)
    side = math.sqrt(floor)
    wall = adv.FACT["wall_height_ft"]
    rise = 0.5 * side * adv.FACT["gable_pitch"]
    head = adv.FACT["headroom_ft"]

    # An equal-aspect drawing letterboxes inside whatever box it is given,
    # so the axes is sized to the drawing's own proportions rather than to
    # a round number -- otherwise the slack turns up as a dead band between
    # the buildings and the caption.
    fig = new_figure(PAGE_W_IN, HALF_H_IN)
    axes = fig.add_axes([0.04, 0.30, 0.92, 0.51])
    axes.set_aspect("equal")
    axes.set_axis_off()

    gap = radius * 0.55
    box_left = radius + gap
    box_right = box_left + side

    # The dome, as a real arc rather than a suggestion of one.
    angles = [math.pi * i / 160.0 for i in range(161)]
    arc_x = [radius * math.cos(a) for a in angles]
    arc_y = [radius * math.sin(a) for a in angles]
    axes.fill(arc_x, arc_y, color=STYLE.faint, zorder=1)
    axes.plot(arc_x, arc_y, color=STYLE.accent, linewidth=1.8, zorder=3)

    # The box: walls, then the gable on top of them.
    axes.fill([box_left, box_right, box_right, box_left],
              [0.0, 0.0, wall, wall], color=STYLE.faint, zorder=1)
    axes.fill([box_left, box_right, 0.5 * (box_left + box_right)],
              [wall, wall, wall + rise], color=STYLE.faint, zorder=1)
    axes.plot([box_left, box_left, 0.5 * (box_left + box_right),
               box_right, box_right, box_left],
              [0.0, wall, wall + rise, wall, 0.0, 0.0],
              color=STYLE.wood, linewidth=1.8, zorder=3)

    # Ground, and the height a person needs to stand under.
    axes.plot([-radius * 1.12, box_right + radius * 0.12], [0.0, 0.0],
              color=STYLE.rule, linewidth=1.0, zorder=2)
    axes.plot([-radius * 1.10, box_right + radius * 0.08], [head, head],
              color=STYLE.warn, linewidth=0.8, linestyle="--", zorder=4)
    # Offset far enough to clear the descender in "standing" -- at three
    # points the dashed line ran through the g.
    axes.annotate(f"{head:.0f} ft -- standing room", (-radius * 1.10, head),
                  xytext=(0, 6), textcoords="offset points", fontsize=6.8,
                  color=STYLE.warn, va="bottom")

    # The dome's floor that the line cuts off, shaded on both flanks. This
    # is the concession; it is drawn first and largest so that nobody has
    # to read the caption to find it.
    inner = math.sqrt(max(0.0, radius ** 2 - head ** 2))
    span = [inner + (radius - inner) * i / 48.0 for i in range(49)]
    for sign in (-1.0, 1.0):
        axes.fill_between([sign * x for x in span], 0.0,
                          [math.sqrt(max(0.0, radius ** 2 - x ** 2))
                           for x in span],
                          color=STYLE.warn, alpha=0.18, linewidth=0.0,
                          zorder=2)

    for label, envelope, height, centre, colour in (
            ("2V dome", dome, radius, 0.0, STYLE.accent),
            ("square house", box, wall + rise,
             0.5 * (box_left + box_right), STYLE.wood)):
        axes.annotate(f"{label}\n{envelope.envelope_sqft:,.0f} sq ft of skin\n"
                      f"{envelope.volume_cuft:,.0f} cu ft inside\n"
                      f"{height:.1f} ft tall",
                      (centre, height), xytext=(0, 9),
                      textcoords="offset points", fontsize=7.2,
                      ha="center", va="bottom", color=colour, linespacing=1.45)

    axes.set_xlim(-radius * 1.18, box_right + radius * 0.22)
    axes.set_ylim(-1.0, max(radius, wall + rise) * 1.52)
    axes.set_title(f"{floor:,.0f} square feet of floor, drawn twice",
                   fontsize=9.5)

    saving = adv.envelope_saving(floor)
    stand = adv.standing_sqft(floor)[0]
    fig.text(0.04, 0.215,
             _wrap(f"Same floor, same scale. The dome wraps it in "
                   f"{dome.envelope_sqft:,.0f} square feet of skin against "
                   f"the box's {box.envelope_sqft:,.0f} -- {saving:.1f} per "
                   f"cent less to build, seal and pay for. The shaded rim is "
                   f"the catch: {floor - stand:,.0f} square feet of that "
                   f"floor has less than {head:.0f} feet over it, while "
                   f"every square foot of the box clears the line.", 92),
             fontsize=7.2, va="top", color=STYLE.muted, style="italic")
    return fig


def plot_envelope_versus_size(figure: Figure):
    """The surface margin against floor area, carried past its own death.

    This is the chart that stops the headline being a slogan. The saving
    is large at cabin size, ordinary at house size, and gone entirely at
    the top of the sweep, because a hemisphere has to grow upward to grow
    outward and a stud wall does not.
    """
    from . import dome_advantage as adv

    floor, _dome, _box = _envelopes()
    low, high = min(adv.SWEEP_FLOORS), max(adv.SWEEP_FLOORS)
    steps = 240
    areas = [low + (high - low) * i / steps for i in range(steps + 1)]
    savings = [adv.envelope_saving(area) for area in areas]

    fig = new_figure(PAGE_W_IN, HALF_H_IN + 0.5)
    axes = fig.add_axes([0.14, 0.28, 0.81, 0.56])

    axes.axhline(0.0, color=STYLE.rule, linewidth=1.0)
    axes.fill_between(areas, 0.0, savings,
                      where=[value >= 0.0 for value in savings],
                      color=STYLE.good, alpha=0.15, linewidth=0.0)
    axes.fill_between(areas, 0.0, savings,
                      where=[value <= 0.0 for value in savings],
                      color=STYLE.warn, alpha=0.22, linewidth=0.0)
    axes.plot(areas, savings, color=STYLE.accent, linewidth=1.8)

    crossover = adv.envelope_crossover_sqft()
    volume_line = adv.volume_crossover_sqft()

    # Three labels on one steep curve, and every obvious placement
    # collides with something. The book's dome goes *under* the curve,
    # into the shaded area, which is the only empty quarter near it; the
    # crossover goes up and left rather than down, where it sat on the
    # x-axis label; the volume line goes high, above both.
    axes.axvline(volume_line, color=STYLE.muted, linewidth=0.8, linestyle=":")
    axes.annotate("left of here the dome also\nencloses less air than the box",
                  (volume_line, max(savings) * 0.90), xytext=(6, 0),
                  textcoords="offset points", fontsize=6.6,
                  color=STYLE.muted, ha="left", va="center", linespacing=1.4)

    axes.plot([crossover], [0.0], "o", color=STYLE.warn, markersize=4.5,
              zorder=5)
    axes.annotate(f"the box wins from\n{crossover:,.0f} sq ft up",
                  (crossover, 0.0), xytext=(-12, 30),
                  textcoords="offset points", fontsize=7.0,
                  color=STYLE.warn, ha="right", va="bottom", linespacing=1.4,
                  arrowprops=dict(arrowstyle="->", color=STYLE.warn,
                                  linewidth=0.9, shrinkB=3.0))

    here = adv.envelope_saving(floor)
    axes.plot([floor], [here], "o", color=STYLE.key, markersize=4.5, zorder=5)
    # Set out into the empty third of the plot with a leader back. Beside
    # the marker the second line ran along the curve; above it, the
    # volume-crossover rule went through the middle of the words.
    axes.annotate(f"this book's dome\n{floor:,.0f} sq ft, {here:.1f}%",
                  xy=(floor, here),
                  xytext=(low + (high - low) * 0.34, max(savings) * 0.72),
                  textcoords="data", fontsize=7.0, color=STYLE.key,
                  ha="left", va="center", linespacing=1.4,
                  arrowprops=dict(arrowstyle="->", color=STYLE.key,
                                  linewidth=0.9, shrinkB=3.0))

    axes.set_xlabel("floor area of both buildings (sq ft)")
    axes.set_ylabel("per cent less skin than the box")
    axes.set_title("The saving is a small-building saving")
    axes.set_xlim(low, high)
    # Room under zero so the losing tail is a visible band rather than a
    # thickening of the axis line.
    axes.set_ylim(min(savings) - 5.0, max(savings) * 1.06)
    axes.text(0.0, -0.32,
              _wrap(f"Both buildings keep the same floor at every point on "
                    f"this line. The dome's advantage falls from "
                    f"{adv.envelope_saving(low):.1f} per cent at {low:,.0f} "
                    f"square feet to {adv.envelope_saving(2000.0):.1f} at "
                    f"2,000, and crosses zero at {crossover:,.0f}, where the "
                    f"dome would stand "
                    f"{adv.dome_radius_ft(crossover):.0f} feet tall and be "
                    f"buying skin to wrap air nobody uses. The answer to "
                    f"that is not a bigger sphere.", 92),
              transform=axes.transAxes, fontsize=7.2, va="top",
              color=STYLE.muted, style="italic")
    return fig


def plot_advantage_claims(figure: Figure):
    """The four claims, with the one that is a restatement marked as one.

    Heat loss through the envelope is surface area multiplied by a U-value
    both buildings share, so its margin is the surface margin wearing a
    different unit. Quoting the two together sounds like two findings and
    is one. The column headed "new?" is the whole reason this is a table
    rather than a list of good news.
    """
    from . import dome_advantage as adv

    floor, _dome, _box = _envelopes()
    claims = adv.advantages(floor)
    # Marked here rather than explained per row: a sixth column of prose
    # overflowed the page width, and the table renderer allocates by
    # character count, so it overflowed silently into the column beside it.
    new_fact = ("yes", "yes", "no", "yes")

    rows = []
    for claim, flag in zip(claims, new_fact):
        places = 3 if max(claim.dome, claim.other) < 10.0 else 0
        rows.append((claim.headline, _fmt(claim.dome, places),
                     _fmt(claim.other, places),
                     f"{claim.percent_better:.1f}%", flag))

    honest = adv.equal_standing_advantage(floor)
    rows.append((honest.headline, _fmt(honest.dome, 0), _fmt(honest.other, 0),
                 f"{honest.percent_better:.1f}%", "yes"))

    return table(
        "Four claims, one of which is the first one again",
        ("claim", "dome", "box", "margin", "new?"),
        tuple(rows), align="lrrrl", footer_rows=1,
        note=f"Row one is geometry -- the least skin that will go round a "
             f"given floor. Row two asks a different question, skin per "
             f"cubic foot rather than per square foot of floor, and gets a "
             f"much smaller answer. Row four is two published drag "
             f"coefficients and has nothing to do with area. Row three is "
             f"marked 'no' because at an identical U-value heat loss is "
             f"surface area in warmer units: it can only ever repeat row "
             f"one, and quoting the pair sounds like two findings. The "
             f"ruled-off row is row one re-run honestly. Every building "
             f"above it has {floor:,.0f} square feet of floor; there the "
             f"dome is grown to {adv.floor_for_standing(floor):,.0f} so that "
             f"as much of its floor has {adv.FACT['headroom_ft']:.0f} feet "
             f"over it as the box's does. Still a win. About half the size "
             f"of the headline, and the one to quote at somebody who builds "
             f"for a living.")


PLOTS = {
    "declared_constants": plot_declared_constants,
    "envelope_compare": plot_envelope_compare,
    "envelope_versus_size": plot_envelope_versus_size,
    "advantage_claims": plot_advantage_claims,
    "motion_split": plot_motion_split,
    "motion_efficiency": plot_motion_efficiency,
    "station_ledger": plot_station_ledger,
    "flat_rate": plot_flat_rate,
    "solo_band": plot_solo_band,
    "process_counts": plot_process_counts,
    "process_table": plot_process_table,
    "rip_payback": plot_rip_payback,
    "frame_counts": plot_frame_counts,
    "member_classes": plot_member_classes,
    "split_counts": plot_split_counts,
    "section_rows": plot_section_rows,
    "orientation_table": plot_orientation_table,
    "seam_schedule": plot_seam_schedule,
    "method_a_worked": plot_method_a_worked,
    "method_b_worked": plot_method_b_worked,
    "design_lookup": plot_design_lookup,
    "tree_lookup": plot_tree_lookup,
    "round_trip": plot_round_trip,
    "worked_tree": plot_worked_tree,
    "worked_dome": plot_worked_dome,
    "worked_cutlist": plot_worked_cutlist,
    "worked_seams": plot_worked_seams,
    "ripping_rhythm": plot_ripping_rhythm,
    "jig_stages": plot_jig_stages,
    "butt_setups": plot_butt_setups,
    "offcut_total": plot_offcut_total,
    "panel_variants": plot_panel_variants,
    "sheet_count": plot_sheet_count,
    "headroom_map": plot_headroom_map,
    "money_spent": plot_money_spent,
    "strut_value": plot_strut_value,
    "hours_log": plot_hours_log,
    "frequency_compare": plot_frequency_compare,
    "wedge_versus_board": plot_wedge_versus_board,
    "shaving_cost": plot_shaving_cost,
}


def render(figure: Figure, path_key: str | None = None) -> Path:
    """Draw one plot figure and save it."""
    name = figure.spec.get("plot")
    try:
        drawer = PLOTS[name]
    except KeyError:
        raise ValueError(
            f"figure {figure.key!r} asks for plot {name!r}, which does not "
            f"exist. Known: {', '.join(sorted(PLOTS))}") from None
    fig = drawer(figure)
    return save(fig, path_key or figure.key)
