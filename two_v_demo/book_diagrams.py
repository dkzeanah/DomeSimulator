"""The explanatory line drawings in *Geodesic Dome Wedge Method*.

A diagram in this book is not decoration and it is not a photograph of an
idea.  Where the thing being drawn exists as geometry in this repository, the
diagram is drawn *from* that geometry -- the trunk taper from
:class:`book_math.TreeCutPlan`, the sector wedges from
:func:`wedge_geometry.sector_chord_in`, the pinwheel from
:func:`wedge_geometry.pinwheel_panels`.  A drawing that disagreed with the
solver would be a drawing that teaches the wrong thing.

Where the subject is a process rather than a shape -- the supply chain, the
decision between the two methods -- the drawing is a diagram of that process,
and its labels come from the same constants the prose uses.

Every drawing is flat, black-line, and legible in one colour, because that is
what survives being printed.
"""

from __future__ import annotations

import math
from pathlib import Path

import numpy as np

from . import book_math as bm
from . import wedge_geometry as wg
from .book import Figure
from .book_figures import (HALF_H_IN, PAGE_H_IN, PAGE_W_IN, STYLE,
                           new_figure, save)


# ----------------------------------------------------------------------
# Drawing helpers shared by every diagram
# ----------------------------------------------------------------------

def canvas(width: float = PAGE_W_IN, height: float = HALF_H_IN,
           title: str = "", note: str = "", equal: bool = True):
    """A blank drawing area with the book's title and note furniture.

    ``equal`` keeps one unit horizontal the same size as one unit vertical,
    which is essential when the drawing is of a real shape and actively
    harmful when it is a chart of a process: a flow chart forced to equal
    aspect squeezes itself into a strip and its labels collide.
    """
    fig = new_figure(width, height)
    top = 0.90 if title else 0.98
    bottom = 0.16 if note else 0.03
    axes = fig.add_axes([0.02, bottom, 0.96, top - bottom])
    axes.set_axis_off()
    if equal:
        axes.set_aspect("equal", adjustable="datalim")
    if title:
        fig.text(0.02, 0.975, title, fontsize=10.5, weight="bold",
                 va="top", color=STYLE.ink)
    if note:
        fig.text(0.02, bottom - 0.02, _wrap(note, 96), fontsize=7.2,
                 va="top", color=STYLE.muted, style="italic")
    return fig, axes


def _wrap(text: str, width: int) -> str:
    import textwrap
    return "\n".join(textwrap.wrap(text, width))


def label(axes, x: float, y: float, text: str, size: float = 7.5,
          colour: str | None = None, weight: str = "normal",
          ha: str = "center", va: str = "center") -> None:
    axes.text(x, y, text, fontsize=size, color=colour or STYLE.ink,
              weight=weight, ha=ha, va=va, zorder=6)


def leader(axes, x0: float, y0: float, x1: float, y1: float,
           text: str = "", size: float = 7.0) -> None:
    """A thin leader line from a label to the thing it names."""
    axes.annotate(
        text, xy=(x0, y0), xytext=(x1, y1), fontsize=size,
        color=STYLE.ink, ha="center", va="center",
        arrowprops=dict(arrowstyle="-", linewidth=0.5, color=STYLE.rule,
                        shrinkA=0, shrinkB=2))


def dimension(axes, x0: float, y0: float, x1: float, y1: float,
              text: str, offset: float = 0.0, size: float = 7.0) -> None:
    """A dimension line with arrowheads and a value, drawn like a drawing."""
    axes.annotate("", xy=(x1, y1), xytext=(x0, y0),
                  arrowprops=dict(arrowstyle="<->", linewidth=0.7,
                                  color=STYLE.accent))
    midpoint = ((x0 + x1) * 0.5, (y0 + y1) * 0.5)
    axes.text(midpoint[0], midpoint[1] + offset, text, fontsize=size,
              color=STYLE.accent, ha="center", va="bottom",
              bbox=dict(boxstyle="round,pad=0.16", facecolor=STYLE.paper,
                        edgecolor="none"))


def box(axes, x: float, y: float, width: float, height: float,
        text: str = "", fill: str | None = None, edge: str | None = None,
        size: float = 7.5, weight: str = "normal", wrap_at: int = 18):
    from matplotlib.patches import FancyBboxPatch
    patch = FancyBboxPatch(
        (x, y), width, height, boxstyle="round,pad=0.02,rounding_size=0.06",
        facecolor=fill or STYLE.paper, edgecolor=edge or STYLE.rule,
        linewidth=0.8, zorder=3)
    axes.add_patch(patch)
    if text:
        axes.text(x + width * 0.5, y + height * 0.5, _wrap(text, wrap_at),
                  fontsize=size, ha="center", va="center", zorder=4,
                  weight=weight, color=STYLE.ink)
    return patch


def arrow(axes, x0: float, y0: float, x1: float, y1: float,
          colour: str | None = None, width: float = 0.9) -> None:
    axes.annotate("", xy=(x1, y1), xytext=(x0, y0),
                  arrowprops=dict(arrowstyle="-|>", linewidth=width,
                                  color=colour or STYLE.ink,
                                  shrinkA=2, shrinkB=2), zorder=2)


def sector_polygon(diameter: float, sectors: int, index: int,
                   segments: int = 14) -> np.ndarray:
    """One pie sector of a round log, as a closed polygon.

    The bark face is an arc, not a chord -- drawing it as a straight line is
    the single most common way these illustrations lie about the shape.
    """
    radius = diameter * 0.5
    start = 2.0 * math.pi * index / sectors
    end = 2.0 * math.pi * (index + 1) / sectors
    angles = np.linspace(start, end, segments)
    points = [(0.0, 0.0)]
    points += [(radius * math.cos(a), radius * math.sin(a)) for a in angles]
    return np.asarray(points)


# ======================================================================
# DIAGRAMS
# ======================================================================

def diagram_strand_map(figure: Figure):
    """Three tracks through the book, so a reader can pick one."""
    from .book import BOOK, STRANDS, strand_chapters

    fig, axes = canvas(PAGE_W_IN, HALF_H_IN + 0.9,
                       "Three ways through this book",
                       "Every chapter belongs to one strand. Read straight "
                       "down the book, or follow one track. The manual "
                       "strand alone is a complete set of instructions.",
                       equal=False)
    order = ("story", "howto", "explain", "reference")
    colours = {"story": STYLE.bark, "howto": STYLE.accent,
               "explain": STYLE.good, "reference": STYLE.muted}
    total = len(BOOK.chapters)

    for row, strand in enumerate(order):
        y = len(order) - row
        axes.plot([0, total + 1], [y, y], color=STYLE.faint, linewidth=6,
                  solid_capstyle="butt", zorder=0)
        label(axes, -0.4, y, strand, ha="right", size=8, weight="bold",
              colour=colours[strand])
        chapters = strand_chapters(strand)
        for chapter in chapters:
            axes.plot([chapter.number], [y], "o", markersize=3.4,
                      color=colours[strand], zorder=3)
        label(axes, total + 2.6, y, f"{len(chapters)} ch", size=7,
              colour=colours[strand], ha="left")

    for part in BOOK.parts:
        first = part.chapters[0].number
        axes.axvline(first - 0.5, color=STYLE.rule, linewidth=0.4,
                     linestyle=":", zorder=0)
        label(axes, first - 0.5, len(order) + 0.55, f"{part.number}",
              size=6.5, colour=STYLE.muted)
    label(axes, total / 2, len(order) + 1.05, "parts", size=7,
          colour=STYLE.muted)
    label(axes, total / 2, 0.25, "chapter number", size=7,
          colour=STYLE.muted)
    axes.set_xlim(-6, total + 6)
    axes.set_ylim(0, len(order) + 1.4)
    return fig


def diagram_tree_taper(figure: Figure):
    """The book's tree, measured, with its sections marked."""
    plan = bm.BOOK_TREE
    fig, axes = canvas(
        PAGE_W_IN, HALF_H_IN + 0.4, "The book's tree, measured",
        f"{plan.usable_length_ft:.0f} feet of usable trunk, "
        f"{plan.butt_diameter_in:.0f} inches at the butt and "
        f"{plan.top_diameter_in:.0f} at the top, bucked into "
        f"{plan.sections} sections of {plan.section_length_ft:.0f} feet. "
        "Every number in this book descends from these three measurements.")

    length = plan.usable_length_ft
    heights = np.linspace(0.0, length, 120)
    radii = np.asarray([plan.diameter_at(h) * 0.5 for h in heights])
    axes.fill_between(heights, -radii, radii, color=STYLE.wood,
                      edgecolor=STYLE.bark, linewidth=0.8)

    for index in range(plan.sections + 1):
        position = index * plan.section_length_ft
        radius = plan.diameter_at(min(position, length)) * 0.5
        axes.plot([position, position], [-radius, radius],
                  color=STYLE.paper, linewidth=1.1, zorder=4)
        if index < plan.sections:
            centre = position + plan.section_length_ft * 0.5
            label(axes, centre, 0, str(index + 1), size=7.5,
                  colour=STYLE.paper, weight="bold")

    butt_r = plan.butt_diameter_in * 0.5
    top_r = plan.top_diameter_in * 0.5
    dimension(axes, -1.6, -butt_r, -1.6, butt_r,
              f"{plan.butt_diameter_in:.0f} in", offset=0.4)
    dimension(axes, length + 1.6, -top_r, length + 1.6, top_r,
              f"{plan.top_diameter_in:.0f} in", offset=0.4)
    dimension(axes, 0, -butt_r - 3.2, length, -butt_r - 3.2,
              f"{plan.usable_length_ft:.0f} ft usable", offset=0.4)
    label(axes, plan.section_length_ft * 0.5, butt_r + 1.6,
          f"{plan.sections} x {plan.section_length_ft:.0f} ft "
          f"= {plan.struts_per_tree} struts", size=7.5, ha="left",
          colour=STYLE.accent)
    axes.set_xlim(-5, length + 5)
    axes.set_ylim(-butt_r - 5, butt_r + 4)
    return fig


def diagram_trunk_eighths(figure: Figure):
    """One round section becoming eight structural members."""
    plan = bm.BOOK_TREE
    diameter = plan.mid_diameter_in
    fig, axes = canvas(
        PAGE_W_IN, HALF_H_IN + 0.5, "One trunk, eight sticks",
        f"A {diameter:.0f}-inch section split {plan.sectors} ways gives "
        f"{plan.sectors} members of "
        f"{plan.member_width_in:.2f} by {plan.member_depth_in:.2f} inches, "
        f"{plan.member_area_in2:.1f} square inches each. Nothing is "
        "squared, edged or planed. The bark face stays curved.")

    for index in range(plan.sectors):
        polygon = sector_polygon(diameter, plan.sectors, index)
        axes.fill(polygon[:, 0], polygon[:, 1],
                  facecolor=STYLE.wood if index % 2 else "#c08a51",
                  edgecolor=STYLE.bark, linewidth=0.7, zorder=2)
    circle = plt_circle(diameter * 0.5)
    axes.plot(circle[0], circle[1], color=STYLE.bark, linewidth=1.4,
              zorder=3)

    # The exploded stick, off to the side, with its dimensions.
    offset = diameter * 1.15
    polygon = sector_polygon(diameter, plan.sectors, 0)
    axes.fill(polygon[:, 0] + offset, polygon[:, 1],
              facecolor=STYLE.wood, edgecolor=STYLE.bark, linewidth=1.0,
              zorder=3)
    radius = diameter * 0.5
    dimension(axes, offset, -radius * 0.30, offset + radius, -radius * 0.30,
              f"{plan.member_depth_in:.2f} in deep", offset=0.25)
    chord_y = radius * math.sin(math.pi / plan.sectors)
    dimension(axes, offset + radius * 0.96, -chord_y,
              offset + radius * 0.96, chord_y,
              f"{plan.member_width_in:.2f} in", offset=0.25)
    label(axes, offset + radius * 0.45, radius * 0.52,
          f"{360.0 / plan.sectors:.0f}°", size=8, colour=STYLE.accent,
          weight="bold")
    label(axes, 0, -radius - 1.6,
          f"{plan.sectors} sectors, 3 saw passes", size=7.5,
          colour=STYLE.muted)
    label(axes, offset + radius * 0.5, -radius - 1.6,
          "one member, as it comes off the saw", size=7.5,
          colour=STYLE.muted)
    axes.set_xlim(-radius - 2, offset + radius + 4)
    axes.set_ylim(-radius - 3, radius + 2)
    return fig


def plt_circle(radius: float, segments: int = 200):
    angles = np.linspace(0, 2 * math.pi, segments)
    return radius * np.cos(angles), radius * np.sin(angles)


def diagram_split_sequence(figure: Figure):
    """The order of the saw passes: halve, quarter, eighth."""
    plan = bm.BOOK_TREE
    diameter = plan.mid_diameter_in
    radius = diameter * 0.5
    fig, axes = canvas(
        PAGE_W_IN, HALF_H_IN, "Three passes, in this order",
        "The halving pass goes first every time: it is the only cut with a "
        "flat reference on both sides afterwards. Cut the eighths first and "
        "the last two sectors have nothing to hold them.")

    stages = (
        ("1. halve", ((0, 1),)),
        ("2. quarter", ((0, 1), (2, 3))),
        ("3. eighths", ((0, 1), (2, 3), (1, 2), (3, 0))),
    )
    step = diameter * 1.35
    for index, (name, cuts) in enumerate(stages):
        centre = index * step
        circle = plt_circle(radius)
        axes.fill(circle[0] + centre, circle[1], facecolor=STYLE.wood,
                  edgecolor=STYLE.bark, linewidth=1.0, zorder=1)
        for a, b in cuts:
            angle_a = math.pi * a / 4.0
            angle_b = math.pi * b / 4.0
            mid = (angle_a + angle_b) * 0.5
            axes.plot([centre - radius * math.cos(mid),
                       centre + radius * math.cos(mid)],
                      [-radius * math.sin(mid), radius * math.sin(mid)],
                      color=STYLE.paper, linewidth=2.0, zorder=3)
        label(axes, centre, -radius - 1.4, name, size=8, weight="bold")
        label(axes, centre, -radius - 2.6,
              f"{len(cuts)} cut{'s' if len(cuts) != 1 else ''}", size=7,
              colour=STYLE.muted)
        if index < len(stages) - 1:
            arrow(axes, centre + radius * 1.06, 0,
                  centre + step - radius * 1.06, 0, colour=STYLE.rule)
    axes.set_xlim(-radius - 2, (len(stages) - 1) * step + radius + 2)
    axes.set_ylim(-radius - 4, radius + 1.5)
    return fig


def diagram_recovery_compare(figure: Figure):
    """The same section, converted twice."""
    plan = bm.BOOK_TREE
    diameter = plan.mid_diameter_in
    radius = diameter * 0.5
    yields = wg.tree_yield()

    fig, axes = canvas(
        PAGE_W_IN, HALF_H_IN + 0.4, "The same log, converted two ways",
        f"Left: grid-packed into 2x4s the way a mill saws, sized on the "
        f"small end -- {yields.two_by_four_recovery * 100:.0f}% of the solid "
        f"wood. Right: split into {plan.sectors} sectors, losing only the "
        f"kerf -- {plan.recovery * 100:.0f}%. The shaded area on the left is "
        "slabs, edgings and trim.")

    from matplotlib.patches import Rectangle

    # Left: the sawn conversion.
    circle = plt_circle(radius)
    axes.fill(circle[0], circle[1], facecolor=STYLE.faint,
              edgecolor=STYLE.bark, linewidth=1.0, zorder=1)
    rows = wg.two_by_four_packing(diameter)
    thickness, width = 2.0, 4.0
    bottom = -radius
    for count in rows:
        if count:
            span = count * width
            for piece in range(count):
                axes.add_patch(Rectangle(
                    (-span * 0.5 + piece * width, bottom), width, thickness,
                    facecolor=STYLE.wood, edgecolor=STYLE.bark,
                    linewidth=0.5, zorder=2))
        bottom += thickness
    label(axes, 0, -radius - 1.5,
          f"{sum(rows)} boards, {yields.two_by_four_recovery * 100:.0f}%",
          size=8, weight="bold")

    # Right: the split conversion.
    offset = diameter * 1.3
    for index in range(plan.sectors):
        polygon = sector_polygon(diameter, plan.sectors, index)
        axes.fill(polygon[:, 0] + offset, polygon[:, 1],
                  facecolor=STYLE.wood if index % 2 else "#c08a51",
                  edgecolor=STYLE.bark, linewidth=0.7, zorder=2)
    label(axes, offset, -radius - 1.5,
          f"{plan.sectors} members, {plan.recovery * 100:.0f}%",
          size=8, weight="bold")

    gain = plan.recovery / yields.two_by_four_recovery
    label(axes, offset * 0.5, radius + 1.2,
          f"x{gain:.2f} the usable wood", size=8.5, colour=STYLE.good,
          weight="bold")
    axes.set_xlim(-radius - 2, offset + radius + 2)
    axes.set_ylim(-radius - 3, radius + 2.4)
    return fig


def seam_sections(orientation: str = "point_dome_in",
                  seam_join_mode: str = "raw_trapezoid",
                  seam_id: str = "SEAM_A_016") -> dict:
    """One seam's true cross-section, cut out of the solver's own meshes.

    This is the same cut the wedge book's ``graphics`` module makes: a plane
    perpendicular to the seam's tangent, through the solved member and key
    meshes, with the section framed so that the weather is up. The book draws
    the joint from *this* rather than from a sketch, because the orientation
    of a wedge against the key is exactly the kind of thing a sketch gets
    wrong -- the key's taper, which faces bound it, and where the members'
    points sit all change with the orientation.
    """
    from wedge_book import graphics

    return graphics.seam_section_geometry(seam_id, orientation=orientation,
                                          seam_join_mode=seam_join_mode)


def _draw_section(axes, facts: dict, width: float = 1.0) -> None:
    """Fill one seam section: two members and the key between them."""
    from matplotlib.patches import Polygon

    for loop in facts["members"]:
        axes.add_patch(Polygon(loop, closed=True, facecolor=STYLE.wood,
                               edgecolor=STYLE.bark, linewidth=0.8,
                               zorder=2))
    for loop in facts["key"]:
        axes.add_patch(Polygon(loop, closed=True, facecolor=STYLE.key,
                               edgecolor=STYLE.wood_dark, linewidth=0.9,
                               zorder=4))
    everything = [point for loop in facts["members"] + facts["key"]
                  for point in loop]
    if not everything:
        return
    xs = [point[0] for point in everything]
    ys = [point[1] for point in everything]
    centre_x = (min(xs) + max(xs)) * 0.5
    centre_y = (min(ys) + max(ys)) * 0.5
    # A square window about the section's own centre, so the equal aspect is
    # honest and the narrower axis does not get stretched to fill the pane.
    half = max(max(xs) - min(xs), max(ys) - min(ys)) * 0.62
    axes.set_xlim(centre_x - half, centre_x + half)
    axes.set_ylim(centre_y - half, centre_y + half)
    axes.set_aspect("equal", adjustable="box")
    axes.set_axis_off()


def diagram_orientation_quad(figure: Figure):
    """The same seam in all four orientations, cut from the solver's meshes."""
    from . import raw_wedge_bridge as bridge

    names = bridge.orientations()
    readings = {
        "point_dome_in": "points inward, bark to the weather",
        "point_panel_in": "points apart, into each panel's middle",
        "point_dome_out": "points outward, at the weather",
        "point_panel_out": "points at each other, across the seam",
    }
    sections = {name: seam_sections(name) for name in names}

    fig = new_figure(PAGE_W_IN, PAGE_H_IN)
    fig.text(0.02, 0.975, "The same stick, four ways up",
             fontsize=10.5, weight="bold", va="top", color=STYLE.ink)
    fig.text(0.02, 0.945,
             _wrap("Each pane is one seam cut across, out of the solver's "
                   "own meshes: two members, one from each panel, and the "
                   "key in gold between them. The weather is up in every "
                   "pane. Rotating a member about its own axis does not "
                   "change the 45-degree sector -- it changes which faces "
                   "meet the key, and so what shape the key has to be.",
                   92),
             fontsize=7.0, va="top", color=STYLE.muted, style="italic")

    positions = ((0.03, 0.50), (0.52, 0.50), (0.03, 0.06), (0.52, 0.06))
    for (x0, y0), name in zip(positions, names):
        axes = fig.add_axes([x0, y0, 0.44, 0.40])
        facts = sections[name]
        _draw_section(axes, facts)
        title = name.replace("_", " ").upper()
        axes.set_title(f"{title}\n{readings[name]}", fontsize=7.4,
                       weight="bold", color=STYLE.ink, pad=3.0)
        axes.text(0.5, 1.005, "", transform=axes.transAxes)
        axes.annotate(
            f"key {facts['key_base_in']:.2f} in across its base  ·  "
            f"sawn faces {facts['gap_deg']:.1f}° apart",
            (0.5, -0.03), xycoords="axes fraction", ha="center", va="top",
            fontsize=6.6, color=STYLE.muted)

    fig.text(0.02, 0.015,
             _wrap("In the default frame the key is a narrow spline between "
                   "the two sawn faces. Put the points into the panel "
                   "middles and the same seam wants a key more than four "
                   "times as wide across its base; turn the points outward "
                   "and the key moves outside the members' meeting point. "
                   "That is why the orientation is chosen before the first "
                   "panel is cut and not after.", 96),
             fontsize=7.0, va="bottom", color=STYLE.muted, style="italic")
    return fig


def diagram_pinwheel_exploded(figure: Figure):
    """One panel taken apart: three members, three end-to-side joints."""
    plan = bm.BOOK_TREE
    result = bm.tree_first()
    panels = wg.pinwheel_panels(result.radius_in, plan.member_width_in,
                                bm.declared("gasket_thickness_in"))
    panel = panels[0]

    fig, axes = canvas(
        PAGE_W_IN, HALF_H_IN + 0.5, "One panel: three sticks, pinwheeled",
        "Each member's end lands on the SIDE of the next one, never on its "
        "point, so no end is ever mitred to another end. The dashed outline "
        "is the true triangle; the members sit inside it by the inset. "
        "Drawn from the rectangular-band model, where both ends come out "
        "square. Split a real log sector and the tail becomes a compound "
        "cut -- a mitre plus a bevel of half the sector angle. Chapter 31 "
        "is about that cut and does not pretend it is square.")

    corners = np.asarray(panel.corners, dtype=np.float64)
    origin = corners[0]
    x_axis = corners[1] - origin
    x_axis = x_axis / np.linalg.norm(x_axis)
    normal = np.cross(corners[1] - origin, corners[2] - origin)
    normal = normal / np.linalg.norm(normal)
    y_axis = np.cross(normal, x_axis)

    def flat(point):
        delta = np.asarray(point, dtype=np.float64) - origin
        return np.asarray([float(delta @ x_axis), float(delta @ y_axis)])

    outline = np.asarray([flat(corner) for corner in corners])
    axes.add_patch(_dashed_triangle(outline))

    colours = (STYLE.wood, "#c08a51", STYLE.wood_dark)
    for index, member in enumerate(panel.members):
        tail = flat(member.tail)
        head = flat(member.head)
        direction = head - tail
        length = float(np.linalg.norm(direction))
        direction = direction / length
        across = np.asarray([-direction[1], direction[0]])
        half = plan.member_width_in * 0.5
        quad = np.asarray([tail + across * half, head + across * half,
                           head - across * half, tail - across * half])
        axes.fill(quad[:, 0], quad[:, 1], facecolor=colours[index],
                  edgecolor=STYLE.bark, linewidth=0.8, zorder=3)
        mid = (tail + head) * 0.5
        label(axes, mid[0], mid[1],
              f"{member.edge_class}\n{member.length_in:.1f} in",
              size=6.6, colour=STYLE.paper, weight="bold")
        # The tail runs past the vertex and receives the previous member;
        # the head is cut against the next member's side. Marking both,
        # because which one is which is the whole joint.
        axes.plot([tail[0]], [tail[1]], "o", markersize=3.8,
                  color=STYLE.warn, zorder=6)
        axes.plot([head[0]], [head[1]], "s", markersize=3.4,
                  color=STYLE.accent, zorder=6)

    bearing = panel.members[0].bearing_length_in
    label(axes, outline[:, 0].mean(), outline[:, 1].min() - 5.5,
          f"circle = tail, receives the member behind it "
          f"({bearing:.1f} in of bearing)", size=6.8, colour=STYLE.warn)
    label(axes, outline[:, 0].mean(), outline[:, 1].min() - 8.5,
          "square = head, lands on the next member's side", size=6.8,
          colour=STYLE.accent)
    axes.set_xlim(outline[:, 0].min() - 10, outline[:, 0].max() + 10)
    axes.set_ylim(outline[:, 1].min() - 12, outline[:, 1].max() + 8)
    return fig


def _dashed_triangle(points):
    from matplotlib.patches import Polygon
    return Polygon(points, closed=True, fill=False, edgecolor=STYLE.rule,
                   linewidth=0.8, linestyle=(0, (5, 3)), zorder=1)


def diagram_seam_modes(figure: Figure):
    """One seam, closed two ways: the solver's own two sections, side by side."""
    raw = seam_sections(seam_join_mode="raw_trapezoid")
    flat = seam_sections(seam_join_mode="shaved_flat")

    fig = new_figure(PAGE_W_IN, HALF_H_IN + 0.9)
    fig.text(0.02, 0.975, "One seam, closed two ways", fontsize=10.5,
             weight="bold", va="top", color=STYLE.ink)
    fig.text(0.02, 0.940,
             _wrap("Both panes are the same seam -- cut across it through the "
                   "solver's own meshes, weather up. Left: the split faces "
                   "left exactly as sawn, so the key has to be a taper that "
                   "fills the V between them. Right: a land planed flat on "
                   "each face, which takes the points in and lets one "
                   "parallel-sided key fit every seam in the dome. The two "
                   "keys are the same job done two ways, and only one of them "
                   "can be cut by the dozen.", 94),
             fontsize=7.0, va="top", color=STYLE.muted, style="italic")

    for column, (title, facts, subtitle) in enumerate((
            ("as sawn: a tapered key", raw,
             f"the key's base is {raw['key_base_in']:.2f} in across, between "
             f"the two points"),
            ("shaved flat: one key", flat,
             f"the flat key is {_key_span(flat):.2f} in across, with a land "
             f"planed on each face"))):
        axes = fig.add_axes([0.02 + column * 0.50, 0.10, 0.46, 0.66])
        _draw_section(axes, facts)
        axes.set_title(title, fontsize=8.4, weight="bold", color=STYLE.ink,
                       pad=4.0)
        axes.annotate(_wrap(subtitle, 54), (0.5, -0.02),
                      xycoords="axes fraction", ha="center", va="top",
                      fontsize=6.8, color=STYLE.muted)
    fig.text(0.5, 0.965, "outside — the weather", fontsize=7.0,
             ha="center", va="top", color=STYLE.muted)
    fig.text(0.5, 0.045, "inside", fontsize=7.0, ha="center", va="bottom",
             color=STYLE.muted)
    return fig


def _key_span(facts: dict) -> float:
    """The width of the key's own cut section, measured."""
    loops = facts.get("key") or ()
    if not loops:
        return facts["key_base_in"]
    xs = [point[0] for loop in loops for point in loop]
    return max(xs) - min(xs)
    return fig


def diagram_racking_compare(figure: Figure):
    """A rectangle racks; a triangle does not."""
    fig, axes = canvas(
        PAGE_W_IN, HALF_H_IN, "The same load, two frames",
        "A rectangle of four pinned members is a mechanism: it folds. It "
        "needs a sheet, a brace or a stiff joint to stand. A triangle of "
        "three cannot change shape without one of them changing length, so "
        "the joint is only asked to hold the ends together -- which is why "
        "the shape of the stick stops mattering.")

    from matplotlib.patches import Polygon

    for column, (name, points, racked) in enumerate((
            ("rectangle: folds", [(0, 0), (4, 0), (4, 4), (0, 4)],
             [(0, 0), (4, 0), (5.1, 3.85), (1.1, 3.85)]),
            ("triangle: cannot", [(0, 0), (4, 0), (2, 3.8)], None))):
        cx = column * 7.0
        shifted = [(x + cx, y) for x, y in points]
        axes.add_patch(Polygon(shifted, closed=True, fill=False,
                               edgecolor=STYLE.ink, linewidth=1.6,
                               zorder=3))
        for x, y in shifted:
            axes.plot([x], [y], "o", markersize=4, color=STYLE.accent,
                      zorder=4)
        if racked:
            axes.add_patch(Polygon(
                [(x + cx, y) for x, y in racked], closed=True, fill=False,
                edgecolor=STYLE.warn, linewidth=1.0,
                linestyle=(0, (4, 3)), zorder=2))
        arrow(axes, cx + 1.4, 5.1, cx + 3.0, 5.1, colour=STYLE.warn)
        label(axes, cx + 2.2, 5.55, "push", size=7, colour=STYLE.warn)
        label(axes, cx + 2.0, -0.9, name, size=8.5, weight="bold")

    axes.set_xlim(-1.2, 12.2)
    axes.set_ylim(-1.8, 6.4)
    return fig


def diagram_middlemen_chain(figure: Figure):
    """Every step between a standing tree and a board on a rack."""
    # Both lists live in book_math so the prose and the drawing cannot
    # disagree about how many operations each route takes.
    steps = bm.MILL_ROUTE
    ours = bm.WEDGE_ROUTE
    fig, axes = canvas(
        PAGE_W_IN, HALF_H_IN + 0.4,
        "Two routes from a standing tree to a structural member",
        f"{len(steps)} operations against {len(ours)}. The wedge route does "
        "not do any of it better -- it skips it, and it can only skip it "
        "because the dome will accept the shape that falls out of a split "
        "log. The two lists do not stop in the same place, and that is "
        "stated rather than hidden: the mill route ends at a graded board, "
        "which still has to be bought, carried and jointed. The wedge route "
        "already includes its joint cuts.", equal=False)

    y_top, y_bottom = 2.6, 0.4
    width = 1.42
    pitch = 1.50
    for index, (step, _full) in enumerate(steps):
        x = index * pitch
        box(axes, x, y_top, width, 1.30, step, size=6.4,
            fill=STYLE.faint, wrap_at=9)
        if index:
            arrow(axes, x - 0.08, y_top + 0.65, x, y_top + 0.65,
                  colour=STYLE.rule, width=0.6)
    label(axes, -0.35, y_top + 0.65, "industrial", ha="right", size=8,
          weight="bold", colour=STYLE.muted)

    for index, (step, _full) in enumerate(ours):
        x = index * pitch
        box(axes, x, y_bottom, width, 1.30, step, size=6.6,
            fill="#dfe9dd", edge=STYLE.good, weight="bold", wrap_at=9)
        if index:
            arrow(axes, x - 0.08, y_bottom + 0.65, x, y_bottom + 0.65,
                  colour=STYLE.good, width=0.7)
    label(axes, -0.35, y_bottom + 0.65, "this book", ha="right", size=8,
          weight="bold", colour=STYLE.good)
    label(axes, len(ours) * pitch + 0.35, y_bottom + 0.65,
          "-> a member in the frame", ha="left", size=7, colour=STYLE.good)

    axes.set_xlim(-3.6, max(len(steps), len(ours) + 5) * pitch + 0.6)
    axes.set_ylim(0.1, 4.3)
    return fig


def diagram_bracket_attempts(figure: Figure):
    """Four joints that nearly worked, and the one thing each could not do."""
    attempts = (
        ("plate", "flat plate\nacross the joint",
         "needs two flat faces\nthat meet in a plane"),
        ("pocket", "pocket the end\ninto a block",
         "one block per angle,\nand every angle differs"),
        ("strap", "strap around\nboth members",
         "holds them together,\ndoes not locate them"),
        ("V bracket", "V that takes any\nsection at any angle",
         "absorbs every difference,\nso nothing repeats"),
    )
    fig, axes = canvas(
        PAGE_W_IN, HALF_H_IN + 0.5, "Four joints that nearly worked",
        "The V bracket was the best of them, and that was the problem: a "
        "connector that tolerates any difference removes the pressure to "
        "make the parts the same. The wedge went the other way -- make the "
        "parts identical and the joint gets to be simple.", equal=False)

    for index, (name, what, fails) in enumerate(attempts):
        x = index * 3.2
        box(axes, x, 2.0, 2.7, 1.15, what, size=6.8, fill=STYLE.faint,
            wrap_at=20)
        label(axes, x + 1.35, 3.45, name, size=8.5, weight="bold")
        arrow(axes, x + 1.35, 1.9, x + 1.35, 1.35, colour=STYLE.warn)
        label(axes, x + 1.35, 0.85, fails, size=6.4, colour=STYLE.warn)
    axes.set_xlim(-0.4, len(attempts) * 3.2 + 0.2)
    axes.set_ylim(0.2, 3.9)
    return fig


def diagram_bent_trunk(figure: Figure):
    """A bend a mill would refuse, and the sections either side of it."""
    plan = bm.BOOK_TREE
    fig, axes = canvas(
        PAGE_W_IN, HALF_H_IN, "A bend costs a section, not a tree",
        f"A mill wants a straight log: the bend spoils the whole length "
        f"because a board has to be straight along all of it. Bucked into "
        f"{plan.section_length_ft:.0f}-foot pieces, the bend costs one "
        "section. Cut it out and carry on either side of it.")

    length = 36.0
    heights = np.linspace(0, length, 200)
    bend = 2.6 * np.exp(-((heights - 18.0) ** 2) / 12.0)
    radius = 3.0
    axes.fill_between(heights, bend - radius, bend + radius,
                      color=STYLE.wood, edgecolor=STYLE.bark, linewidth=0.8)

    spoilt = (15.0, 21.0)
    axes.fill_between(
        heights, bend - radius, bend + radius,
        where=(heights >= spoilt[0]) & (heights <= spoilt[1]),
        color=STYLE.warn, alpha=0.55, edgecolor="none")

    position = 0.0
    index = 1
    while position + plan.section_length_ft <= length + 1e-9:
        end = position + plan.section_length_ft
        overlaps = not (end <= spoilt[0] or position >= spoilt[1])
        colour = STYLE.warn if overlaps else STYLE.good
        axes.plot([position, position], [-radius - 1.4, -radius - 0.5],
                  color=STYLE.ink, linewidth=0.7)
        label(axes, position + plan.section_length_ft * 0.5,
              -radius - 2.4, "reject" if overlaps else f"{index}",
              size=7, colour=colour,
              weight="bold" if not overlaps else "normal")
        if not overlaps:
            index += 1
        position = end
    axes.plot([length, length], [-radius - 1.4, -radius - 0.5],
              color=STYLE.ink, linewidth=0.7)

    label(axes, 18.0, radius + 3.4, "the bend", size=8, colour=STYLE.warn,
          weight="bold")
    label(axes, 18.0, -radius - 4.2,
          f"one section lost, {index - 1} kept", size=7.5,
          colour=STYLE.good)
    axes.set_xlim(-2, length + 2)
    axes.set_ylim(-radius - 5.4, radius + 4.6)
    return fig


def diagram_method_decision(figure: Figure):
    """Start from what you actually have."""
    fig, axes = canvas(
        PAGE_W_IN, HALF_H_IN + 0.5, "Which method are you in?",
        "Almost everybody thinks they are designing first. If the trees are "
        "already down, or already chosen, you are in Method B and choosing "
        "a diameter is a wish, not a decision.", equal=False)

    box(axes, 3.0, 5.4, 4.2, 0.95,
        "What is already fixed?", size=8.5, weight="bold",
        fill=STYLE.faint, wrap_at=24)

    box(axes, 0.2, 3.4, 4.0, 1.15,
        "The dome. You need a certain floor, or a permit says a size.",
        size=7, wrap_at=30)
    box(axes, 6.0, 3.4, 4.0, 1.15,
        "The trees. They are down, or they are the ones you have.",
        size=7, wrap_at=30)
    arrow(axes, 4.4, 5.35, 2.2, 4.6)
    arrow(axes, 5.8, 5.35, 8.0, 4.6)

    box(axes, 0.2, 1.5, 4.0, 1.15,
        "METHOD A\nRadius in, cut list out. Ch. 18.",
        size=7.5, weight="bold", fill="#dde7ee", edge=STYLE.accent,
        wrap_at=28)
    box(axes, 6.0, 1.5, 4.0, 1.15,
        "METHOD B\nSection length in, dome out. Ch. 19.",
        size=7.5, weight="bold", fill="#dfe9dd", edge=STYLE.good,
        wrap_at=28)
    arrow(axes, 2.2, 3.35, 2.2, 2.7)
    arrow(axes, 8.0, 3.35, 8.0, 2.7)

    box(axes, 3.0, 0.0, 4.2, 0.95,
        "Then check the other one. Ch. 20.", size=7.5,
        fill=STYLE.paper, edge=STYLE.rule, wrap_at=30)
    arrow(axes, 2.6, 1.45, 4.2, 0.95, colour=STYLE.rule)
    arrow(axes, 7.6, 1.45, 6.0, 0.95, colour=STYLE.rule)

    axes.set_xlim(-0.3, 10.5)
    axes.set_ylim(-0.4, 6.8)
    return fig


def diagram_bucking_plan(figure: Figure):
    """The whole trunk laid out with its sections and its offcut."""
    plan = bm.BOOK_TREE
    fig, axes = canvas(
        PAGE_W_IN, HALF_H_IN, "Bucking the trunk",
        f"Mark from the butt, not from the top: the tape drifts, and an "
        f"error at the top is a short stick you cannot use. "
        f"{plan.sections} sections of {plan.section_length_ft:.0f} feet "
        f"leaves {plan.offcut_ft:.1f} feet over on this tree.")

    length = plan.usable_length_ft
    for index in range(plan.sections):
        start = index * plan.section_length_ft
        radius = plan.diameter_at(start + plan.section_length_ft * 0.5) * 0.5
        axes.add_patch(_rect(start + 0.12, -radius,
                             plan.section_length_ft - 0.24, radius * 2,
                             STYLE.wood))
        label(axes, start + plan.section_length_ft * 0.5, 0,
              f"{index + 1}", size=8, colour=STYLE.paper, weight="bold")
        label(axes, start + plan.section_length_ft * 0.5, radius + 0.55,
              f"{plan.sectors} struts", size=6.2, colour=STYLE.muted)

    if plan.offcut_ft > 0:
        radius = plan.top_diameter_in * 0.5
        axes.add_patch(_rect(plan.sections * plan.section_length_ft, -radius,
                             plan.offcut_ft, radius * 2, STYLE.faint))

    dimension(axes, 0, -plan.butt_diameter_in * 0.5 - 2.0, length,
              -plan.butt_diameter_in * 0.5 - 2.0,
              f"{length:.0f} ft = {plan.sections} x "
              f"{plan.section_length_ft:.0f} ft", offset=0.3)
    label(axes, 0, plan.butt_diameter_in * 0.5 + 1.8, "butt", size=7.5,
          weight="bold", ha="left")
    label(axes, length, plan.butt_diameter_in * 0.5 + 1.8, "top", size=7.5,
          weight="bold", ha="right")
    label(axes, length * 0.5, -plan.butt_diameter_in * 0.5 - 4.2,
          f"{plan.struts_per_tree} struts from this tree", size=8,
          colour=STYLE.good, weight="bold")
    axes.set_xlim(-2, length + 2)
    axes.set_ylim(-plan.butt_diameter_in * 0.5 - 5.4,
                  plan.butt_diameter_in * 0.5 + 3.0)
    return fig


def _rect(x, y, width, height, colour):
    from matplotlib.patches import Rectangle
    return Rectangle((x, y), width, height, facecolor=colour,
                     edgecolor=STYLE.bark, linewidth=0.7, zorder=2)


def diagram_felling_hinge(figure: Figure):
    """What the hinge does, and what happens when it is wrong."""
    fig, axes = canvas(
        PAGE_W_IN, HALF_H_IN, "The hinge steers the tree",
        "The notch decides the direction; the hinge holds the tree to that "
        "direction while it falls. Cut through the hinge and the tree is no "
        "longer attached to anything that is aiming it. This drawing is not "
        "a felling course -- take one.")

    from matplotlib.patches import Wedge

    for column, (name, hinge_ok) in enumerate((("even hinge", True),
                                               ("cut through", False))):
        cx = column * 7.0
        circle = plt_circle(2.4)
        axes.fill(circle[0] + cx, circle[1], facecolor=STYLE.wood,
                  edgecolor=STYLE.bark, linewidth=1.0, zorder=1)
        axes.add_patch(Wedge((cx, 0), 2.42, -32, 32, facecolor=STYLE.paper,
                             edgecolor=STYLE.bark, linewidth=0.8, zorder=2))
        axes.plot([cx - 2.42, cx - 0.55], [-0.34, -0.34],
                  color=STYLE.paper, linewidth=3.2, zorder=3)
        if hinge_ok:
            axes.plot([cx - 0.55, cx + 1.55], [0.0, 0.0], color=STYLE.good,
                      linewidth=4.0, solid_capstyle="butt", zorder=4)
            label(axes, cx + 0.5, 0.75, "hinge", size=7.5,
                  colour=STYLE.good, weight="bold")
            arrow(axes, cx + 2.7, 0, cx + 4.4, 0, colour=STYLE.good,
                  width=1.4)
            label(axes, cx + 3.5, 0.6, "falls here", size=7,
                  colour=STYLE.good)
        else:
            axes.plot([cx - 0.55, cx + 1.55], [0.0, 0.0], color=STYLE.warn,
                      linewidth=4.0, solid_capstyle="butt", zorder=4,
                      linestyle=(0, (2, 2)))
            label(axes, cx + 0.5, 0.75, "no hinge", size=7.5,
                  colour=STYLE.warn, weight="bold")
            for angle in (-38, 0, 41):
                radians = math.radians(angle)
                arrow(axes, cx + 2.7, 0,
                      cx + 2.7 + 1.7 * math.cos(radians),
                      1.7 * math.sin(radians), colour=STYLE.warn)
            label(axes, cx + 3.7, -1.5, "anywhere", size=7,
                  colour=STYLE.warn)
        label(axes, cx, -3.3, name, size=8.5, weight="bold")
        label(axes, cx - 2.9, 0, "back\ncut", size=6.6, colour=STYLE.muted,
              ha="right")
        label(axes, cx + 2.0, -1.9, "notch", size=6.6, colour=STYLE.muted)
    axes.set_xlim(-4.4, 12.6)
    axes.set_ylim(-4.2, 2.6)
    return fig


def diagram_tolerance_budget(figure: Figure):
    """Where a sixteenth of an inch ends up."""
    overfit = bm.declared("head_overfit_in")
    fig, axes = canvas(
        PAGE_W_IN, HALF_H_IN + 0.4, "Where error goes",
        f"Three of the four are absorbed by the method itself. The fourth "
        f"accumulates around the bottom ring, which is why the ring is the "
        f"one thing you check as you go rather than at the end.",
        equal=False)

    sources = (
        ("stock length varies", "head is cut long anyway",
         f"absorbed: {overfit:.0f} in of overfit", True),
        ("butt angle off", "head end flush-cuts in place",
         "absorbed: leaves as offcut", True),
        ("seam gap varies", "key is fitted to the gap",
         "absorbed: the key takes it", True),
        ("panel edge length", "next panel starts where this one ended",
         "ACCUMULATES around the ring", False),
    )
    for index, (source, mechanism, outcome, absorbed) in enumerate(sources):
        y = (len(sources) - index - 1) * 1.5
        colour = STYLE.good if absorbed else STYLE.warn
        box(axes, 0.0, y, 3.0, 1.05, source, size=6.8, fill=STYLE.faint,
            wrap_at=18)
        arrow(axes, 3.1, y + 0.52, 3.9, y + 0.52, colour=STYLE.rule)
        box(axes, 4.0, y, 3.4, 1.05, mechanism, size=6.6, wrap_at=22)
        arrow(axes, 7.5, y + 0.52, 8.3, y + 0.52, colour=colour)
        box(axes, 8.4, y, 3.4, 1.05, outcome, size=6.6, edge=colour,
            weight="bold" if not absorbed else "normal", wrap_at=22)
    label(axes, 1.5, len(sources) * 1.5 - 0.25, "error appears", size=7.5,
          weight="bold", colour=STYLE.muted)
    label(axes, 5.7, len(sources) * 1.5 - 0.25, "what the method does",
          size=7.5, weight="bold", colour=STYLE.muted)
    label(axes, 10.1, len(sources) * 1.5 - 0.25, "where it ends up",
          size=7.5, weight="bold", colour=STYLE.muted)
    axes.set_xlim(-0.3, 12.1)
    axes.set_ylim(-0.4, len(sources) * 1.5 + 0.3)
    return fig


def diagram_openings(figure: Figure):
    """Three ways to open a dome without un-triangulating it."""
    fig, axes = canvas(
        PAGE_W_IN, HALF_H_IN + 0.3,
        "Three openings that do not un-triangulate the shell",
        "A dome works because every panel is a triangle. Remove a member "
        "and the panel becomes a mechanism. All three of these keep every "
        "remaining triangle whole: the rim door removes nothing, the panel "
        "window sits inside a triangle, and the riser moves the whole shell "
        "up onto a wall that can have anything in it.")

    from matplotlib.patches import Polygon, Rectangle

    def triangle(cx, cy, size):
        return [(cx, cy + size), (cx - size * 0.87, cy - size * 0.5),
                (cx + size * 0.87, cy - size * 0.5)]

    # 1. Rim door.
    axes.add_patch(Polygon(triangle(2.0, 2.2, 1.6), closed=True, fill=False,
                           edgecolor=STYLE.ink, linewidth=1.4))
    axes.add_patch(Rectangle((1.45, 0.7), 1.1, 1.35, facecolor=STYLE.faint,
                             edgecolor=STYLE.accent, linewidth=1.0))
    label(axes, 2.0, -0.1, "rim door", size=8, weight="bold")
    label(axes, 2.0, -0.75, "between two rim members\nnothing removed",
          size=6.4, colour=STYLE.muted)

    # 2. Panel window.
    axes.add_patch(Polygon(triangle(6.4, 2.2, 1.6), closed=True, fill=False,
                           edgecolor=STYLE.ink, linewidth=1.4))
    axes.add_patch(Polygon(triangle(6.4, 2.05, 0.85), closed=True,
                           facecolor="#dde7ee", edgecolor=STYLE.accent,
                           linewidth=1.0))
    label(axes, 6.4, -0.1, "panel window", size=8, weight="bold")
    label(axes, 6.4, -0.75, "inside one triangle\nframe stays whole",
          size=6.4, colour=STYLE.muted)

    # 3. Riser wall.
    axes.add_patch(Polygon(triangle(10.8, 2.6, 1.4), closed=True, fill=False,
                           edgecolor=STYLE.ink, linewidth=1.4))
    axes.add_patch(Rectangle((9.4, 0.55), 2.8, 1.35, facecolor=STYLE.faint,
                             edgecolor=STYLE.good, linewidth=1.0))
    axes.add_patch(Rectangle((10.4, 0.75), 0.85, 0.95,
                             facecolor="#dfe9dd", edgecolor=STYLE.good,
                             linewidth=0.8))
    label(axes, 10.8, -0.1, "riser wall", size=8, weight="bold")
    label(axes, 10.8, -0.75, "dome sits on a wall\nopenings are ordinary",
          size=6.4, colour=STYLE.muted)

    axes.set_xlim(-0.4, 13.0)
    axes.set_ylim(-1.5, 4.4)
    return fig


def diagram_section_compare(figure: Figure):
    """One wedge and one board, drawn at the same scale."""
    versus = bm.wedge_versus_board(8.0)
    wedge, board = versus.wedge, versus.board
    diameter = versus.diameter_in
    radius = diameter * 0.5

    fig, axes = canvas(
        PAGE_W_IN, HALF_H_IN + 0.6, "The two sections, at the same scale",
        f"An eighth of an {diameter:.0f}-inch log holds "
        f"{wedge.area_in2:.2f} square inches of wood against the dressed "
        f"2x4's {board.area_in2:.2f} -- {versus.area_gain_pct:+.0f} per "
        f"cent. It is also deeper: {wedge.depth_in:.2f} inches pith to bark "
        f"against {board.depth_in:.1f}. What it is not is stronger in "
        "bending, because so much of that wood sits near the pith, where it "
        "does the least work.")

    from matplotlib.patches import Rectangle

    # The wedge, lying the way it does in a dome wall: depth radial.
    polygon = sector_polygon(diameter, 8, 0)
    axes.fill(polygon[:, 0], polygon[:, 1], facecolor=STYLE.wood,
              edgecolor=STYLE.bark, linewidth=1.1, zorder=2)
    dimension(axes, 0, -radius * 0.66, radius, -radius * 0.66,
              f"{wedge.depth_in:.2f} in deep", offset=0.12)
    label(axes, radius * 0.55, radius * 1.02,
          f"{wedge.area_in2:.2f} sq in", size=8, weight="bold",
          colour=STYLE.bark)
    label(axes, radius * 0.5, -radius * 1.02, "one eighth of the log",
          size=7.5, colour=STYLE.muted, va="top")

    # The board, beside it, stood on edge.
    left = diameter * 0.95
    axes.add_patch(Rectangle((left, -board.depth_in * 0.5),
                             board.width_in, board.depth_in,
                             facecolor="#cbb894", edgecolor=STYLE.bark,
                             linewidth=1.1, zorder=2))
    dimension(axes, left + board.width_in + 0.45, -board.depth_in * 0.5,
              left + board.width_in + 0.45, board.depth_in * 0.5,
              f"{board.depth_in:.1f} in", offset=0.12)
    label(axes, left + board.width_in * 0.5, board.depth_in * 0.5 + 0.55,
          f"{board.area_in2:.2f} sq in", size=8, weight="bold",
          colour=STYLE.bark)
    label(axes, left + board.width_in * 0.5, -radius * 1.02,
          "dressed 2x4, on edge", size=7.5, colour=STYLE.muted, va="top")

    label(axes, diameter * 0.70, radius * 1.02,
          f"{versus.area_ratio:.2f}x the wood", size=9, weight="bold",
          colour=STYLE.good)
    label(axes, diameter * 0.70, radius * 0.78,
          f"{versus.strength_ratio:.2f}x the bending strength", size=7.5,
          colour=STYLE.warn)
    axes.set_xlim(-1.4, left + board.width_in + 2.6)
    axes.set_ylim(-radius * 1.45, radius * 1.25)
    return fig


def diagram_precision_location(figure: Figure):
    """Machine every member, or machine one key and repeat it."""
    members = bm.MEMBERS_IN_FRAME
    seams = bm.panel_seam_count()
    keys = len(bm.shaving_plan())

    fig, axes = canvas(
        PAGE_W_IN, HALF_H_IN + 0.3, "Where the precision lives",
        f"Both routes end with a dome that closes. One asks for accuracy "
        f"{members} times, on the largest and most awkward pieces in the "
        f"build. The other asks for it {keys} times, on the smallest, then "
        f"repeats the result {seams} times. This is not a way of avoiding "
        "accuracy. It is putting it where it is cheapest to buy.",
        equal=False)

    rows = (
        ("Accuracy in the member",
         f"machine all {members} members to fit",
         "big pieces, awkward to hold, one chance each", STYLE.warn),
        ("Accuracy in the connector",
         f"machine {keys} key profiles, repeat them",
         "small pieces, easy to hold, easy to remake", STYLE.good),
    )
    for index, (name, what, why, colour) in enumerate(rows):
        y = (len(rows) - index - 1) * 1.7
        box(axes, 0.0, y, 3.2, 1.15, name, size=7.6, weight="bold",
            fill=STYLE.faint, edge=colour, wrap_at=20)
        arrow(axes, 3.3, y + 0.57, 4.0, y + 0.57, colour=colour)
        box(axes, 4.1, y, 3.6, 1.15, what, size=7.0, wrap_at=24)
        arrow(axes, 7.8, y + 0.57, 8.5, y + 0.57, colour=colour)
        box(axes, 8.6, y, 3.9, 1.15, why, size=6.8, edge=colour, wrap_at=26)

    label(axes, 6.2, len(rows) * 1.7 - 0.15,
          "The tree supplies the mass. The jig supplies the repeatability. "
          "The connector supplies the precision.",
          size=8, weight="bold", colour=STYLE.accent)
    axes.set_xlim(-0.3, 12.8)
    axes.set_ylim(-0.4, len(rows) * 1.7 + 0.5)
    return fig


def diagram_seam_sandwich(figure: Figure):
    """An interior seam holds two members and a key, not one strut."""
    plan = bm.BOOK_TREE
    edges = bm.edge_accounting()
    diameter = plan.mid_diameter_in
    radius = diameter * 0.5
    gasket = bm.declared("gasket_thickness_in")

    fig, axes = canvas(
        PAGE_W_IN, HALF_H_IN + 0.5, "One seam, two members",
        f"{edges.panels} panels x {edges.members_per_panel} members is "
        f"{edges.members}, but the shell has only {edges.unique_edges} "
        f"edges: {edges.duplicated_members} members exist twice over, once "
        f"for each panel meeting there. That is "
        f"{edges.duplication_ratio:.2f} times the timber a shared-strut "
        "frame would use, and it is what lets every panel be built flat, "
        "checked, skinned and lifted as a finished thing.")

    from matplotlib.patches import Polygon

    # Left: the shared-strut frame this book is NOT building.
    cx = -diameter * 1.55
    polygon = sector_polygon(diameter, plan.sectors, 0)
    axes.fill(polygon[:, 0] + cx, polygon[:, 1], facecolor="#cbb894",
              edgecolor=STYLE.bark, linewidth=0.9, zorder=2)
    label(axes, cx + radius * 0.4, radius * 1.05, "one shared strut",
          size=8, weight="bold", colour=STYLE.muted)
    label(axes, cx + radius * 0.4, -radius * 1.0,
          f"{edges.unique_edges} members\n(a different frame)", size=6.8,
          colour=STYLE.muted, va="top")

    # Right: this book's panelised seam -- member, key, member.
    for side in (-1, 1):
        polygon = sector_polygon(diameter, plan.sectors, 0)
        xs = polygon[:, 0] * side
        axes.fill(xs + side * (gasket * 0.5 + radius * 0.08), polygon[:, 1],
                  facecolor=STYLE.wood, edgecolor=STYLE.bark, linewidth=0.9,
                  zorder=2)
    half = gasket * 0.5
    top = radius * 0.55
    axes.add_patch(Polygon([(-half, top), (half, top), (half, -top),
                            (-half, -top)], closed=True,
                           facecolor=STYLE.key, edgecolor=STYLE.bark,
                           linewidth=0.8, zorder=4))
    label(axes, 0, radius * 1.20, "panel A + key + panel B", size=8,
          weight="bold")
    label(axes, 0, -radius * 1.0, f"{edges.members} members\n(this book)",
          size=6.8, colour=STYLE.good, va="top")
    label(axes, -radius * 1.85, 0, "A", size=9, weight="bold",
          colour=STYLE.bark)
    label(axes, radius * 1.85, 0, "B", size=9, weight="bold",
          colour=STYLE.bark)

    axes.set_xlim(cx - radius * 1.4, radius * 2.5)
    axes.set_ylim(-radius * 1.85, radius * 1.45)
    return fig


def diagram_master_cutlist(figure: Figure):
    """The master cut list: three resultant lengths, and how a panel sits.

    The list is what the members measure once they are cut to make a panel
    the right size -- not stock left long. This drawing puts the numbers on
    the two panel shapes they belong to: three long members in an
    equilateral, and in an isosceles the long member at the base, the middle
    length on the left and the short one on the right. The triangle is
    solved from the three lengths themselves, so the shape cannot quietly
    disagree with the numbers beside it.
    """
    long_in = bm.declared("master_cut_long_in")
    mid_in = bm.declared("master_cut_mid_in")
    short_in = bm.declared("master_cut_short_in")

    fig, axes = canvas(
        PAGE_W_IN, HALF_H_IN + 1.0,
        "The master cut list: three lengths, and the side each one takes",
        "These are resultant lengths: cut to these and the panel is the size "
        "the dome wants. An equilateral panel is three of the long member. "
        "An isosceles panel, laid with its base nearest you, takes the long "
        "member as the base, the middle length on the left and the short one "
        "on the right -- the left member is the longer of the two and so "
        "reaches over to the top point, while the base butts up to the short "
        "right side. That single sentence is the bench rule; nothing about "
        "the pair is obvious by eye, so the sides are picked from their own "
        "stacks in order.")

    def member(points, colour, width=6.5):
        for start, end in points:
            axes.plot([start[0], end[0]], [start[1], end[1]], color=colour,
                      linewidth=width, solid_capstyle="round", zorder=3)

    # -- the equilateral panel -----------------------------------------
    base = long_in
    apex = (base / 2.0, math.sqrt(base ** 2 - (base / 2.0) ** 2))
    left = ((0.0, 0.0), apex)
    right = ((base, 0.0), apex)
    bottom = ((0.0, 0.0), (base, 0.0))
    member((left, right, bottom), STYLE.wood)
    label(axes, base * 0.5, -6.0, f"{long_in:g} in", size=7.6,
          weight="bold", colour=STYLE.accent)
    label(axes, base * 0.22, apex[1] * 0.55, f"{long_in:g} in", size=7.6,
          weight="bold", colour=STYLE.ink)
    label(axes, base * 0.80, apex[1] * 0.55, f"{long_in:g} in", size=7.6,
          weight="bold", colour=STYLE.ink)
    label(axes, base * 0.5, apex[1] * 0.42,
          "equilateral:\nthree of the long member",
          size=7.0, colour=STYLE.muted)
    label(axes, base * 0.5, apex[1] + 5.0, "ten panels", size=8.0,
          weight="bold")

    # -- the isosceles panel, solved from its own three lengths --------
    offset = base + 26.0
    # Law of cosines on the two sides, so the drawn triangle IS the list.
    cosine = (mid_in ** 2 + base ** 2 - short_in ** 2) / (2.0 * mid_in * base)
    x = float(cosine) * mid_in
    y = math.sqrt(mid_in ** 2 - x ** 2)
    peak = (offset + x, y)
    member((((offset, 0.0), peak), ((offset + base, 0.0), peak),
            ((offset, 0.0), (offset + base, 0.0))), STYLE.wood_dark)
    label(axes, offset + base * 0.5, -6.0, f"{long_in:g} in  (base)",
          size=7.6, weight="bold", colour=STYLE.accent)
    label(axes, offset + x * 0.42, y * 0.52, f"{mid_in:g} in\n(left)",
          size=7.6, weight="bold", colour=STYLE.good)
    label(axes, offset + x + (base - x) * 0.62, y * 0.52,
          f"{short_in:g} in\n(right)", size=7.6, weight="bold",
          colour=STYLE.warn)
    # The short side is where the base lands: mark the butt, and the top
    # point the longer left member reaches over to.
    axes.plot([offset + base], [0.0], "o", markersize=5.0, color=STYLE.warn,
              zorder=6)
    label(axes, offset + base + 1.0, 3.4,
          "the base\nbutts up\nhere", size=6.6, colour=STYLE.warn, ha="left",
          va="bottom")
    axes.plot([offset + x], [y], "o", markersize=4.4, color=STYLE.ink,
              zorder=6)
    label(axes, offset + x - 1.5, y + 3.0,
          "top point: the left member reaches over", size=6.6,
          colour=STYLE.ink, ha="center", va="bottom")
    label(axes, offset + base * 0.5, y + 9.0, "thirty panels", size=8.0,
          weight="bold")

    axes.set_xlim(-10.0, offset + base + 22.0)
    axes.set_ylim(-18.0, max(apex[1], y) + 18.0)
    return fig


DIAGRAMS = {
    "strand_map": diagram_strand_map,
    "master_cutlist": diagram_master_cutlist,
    "tree_taper": diagram_tree_taper,
    "trunk_eighths": diagram_trunk_eighths,
    "split_sequence": diagram_split_sequence,
    "recovery_compare": diagram_recovery_compare,
    "orientation_quad": diagram_orientation_quad,
    "pinwheel_exploded": diagram_pinwheel_exploded,
    "seam_modes": diagram_seam_modes,
    "racking_compare": diagram_racking_compare,
    "middlemen_chain": diagram_middlemen_chain,
    "bracket_attempts": diagram_bracket_attempts,
    "bent_trunk": diagram_bent_trunk,
    "method_decision": diagram_method_decision,
    "bucking_plan": diagram_bucking_plan,
    "felling_hinge": diagram_felling_hinge,
    "tolerance_budget": diagram_tolerance_budget,
    "openings": diagram_openings,
    "section_compare": diagram_section_compare,
    "precision_location": diagram_precision_location,
    "seam_sandwich": diagram_seam_sandwich,
}


def render(figure: Figure, path_key: str | None = None) -> Path:
    """Draw one diagram and save it."""
    name = figure.spec.get("diagram")
    try:
        drawer = DIAGRAMS[name]
    except KeyError:
        raise ValueError(
            f"figure {figure.key!r} asks for diagram {name!r}, which does "
            f"not exist. Known: {', '.join(sorted(DIAGRAMS))}") from None
    fig = drawer(figure)
    return save(fig, path_key or figure.key)
