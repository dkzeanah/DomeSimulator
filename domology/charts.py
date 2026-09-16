"""Charts and flat drawings for Domology, drawn from the code the numbers come from.

Each chart reads the same functions the book's tokens read, so a bar and the
sentence beside it cannot disagree. They are drawn in the book's own type and
colours -- Palatino and Segoe UI, amber for the long strut and cyan for the
short -- on white, at print resolution.
"""

from __future__ import annotations

import math
import textwrap
from pathlib import Path

from . import config as C
from . import fonts as F

DPI = 300


def _setup():
    import matplotlib
    matplotlib.use("Agg")
    from matplotlib import font_manager, rcParams
    for family, style in (("serif", "r"), ("serif", "i"), ("sans", "r"), ("sans", "sb"),
                          ("sans", "b")):
        try:
            font_manager.fontManager.addfont(str(F.face_path(family, style)))
        except Exception:
            pass
    rcParams.update({
        "font.family": "sans-serif",
        "font.sans-serif": ["Segoe UI", "DejaVu Sans"],
        "font.serif": ["Palatino Linotype", "DejaVu Serif"],
        "font.size": 10.0, "axes.titlesize": 12.5, "axes.titleweight": "bold",
        "axes.edgecolor": C.RULE, "axes.labelcolor": C.INK, "text.color": C.INK,
        "xtick.color": C.INK, "ytick.color": C.MUTED, "axes.spines.top": False,
        "axes.spines.right": False, "figure.facecolor": "white", "savefig.facecolor": "white",
        "axes.facecolor": "white", "legend.frameon": False,
    })
    import matplotlib.pyplot as plt
    return plt


def _money(value: float) -> str:
    return f"${value:,.0f}"


def _save(fig, path: Path, size) -> Path:
    fig.set_size_inches(size[0] / DPI, size[1] / DPI)
    fig.savefig(path, dpi=DPI)
    import matplotlib.pyplot as plt
    plt.close(fig)
    return path


def chart_skin(path: Path, size) -> Path:
    from . import science
    plt = _setup()
    e = science.efficiency()
    fig, (left, right) = plt.subplots(1, 2, gridspec_kw={"width_ratios": [2.3, 1]})
    names = ["Box house\nwalls + roof", "Hemisphere\ncurved skin", "2V dome\nflat panels"]
    values = [e["box_skin"], e["curved_skin"], e["panel_skin"]]
    colours = [C.MUTED, C.SHORT, C.LONG]
    bars = left.bar(names, values, color=colours, width=0.62)
    for bar, value in zip(bars, values):
        left.text(bar.get_x() + bar.get_width() / 2, value + max(values) * 0.02,
                  f"{value:,.0f} sq ft", ha="center", va="bottom", fontsize=10, fontweight="bold")
    left.set_ylim(0, max(values) * 1.18)
    left.set_ylabel("envelope to build, square feet")
    left.set_title(f"The same {e['floor']:,.0f} sq ft of floor", loc="left")
    left.text(0.99, 0.97, f"{e['skin_saving'] * 100:.0f}% less envelope",
              transform=left.transAxes, ha="right", va="top", color=C.LONG, fontsize=11,
              fontweight="bold")
    ratio = e["sphere_to_cube"]
    bars = right.bar(["Cube", "Sphere"], [1.0, ratio], color=[C.MUTED, C.SHORT], width=0.6)
    for bar, value in zip(bars, [1.0, ratio]):
        right.text(bar.get_x() + bar.get_width() / 2, value + 0.03, f"{value:.3f}",
                   ha="center", va="bottom", fontsize=10, fontweight="bold")
    right.set_ylim(0, 1.25)
    right.set_title("Equal volume", loc="left")
    right.set_ylabel("skin, cube = 1")
    right.text(0.5, 0.93, f"{e['sphere_saving'] * 100:.1f}% less", transform=right.transAxes,
               ha="center", va="top", color=C.SHORT, fontsize=10.5, fontweight="bold")
    fig.tight_layout(pad=1.2)
    return _save(fig, path, size)


def chart_comparison(path: Path, size) -> Path:
    from . import science
    plt = _setup()
    c = science.comparisons()
    fig, axes = plt.subplots(1, 2)
    for axis, key, title in ((axes[0], "shed", "Bare shell, matched on volume"),
                             (axes[1], "home", "Finished home, matched on floor")):
        box, dome = c[key]["box"], c[key]["dome"]
        labels = ["Box", "Dome"]
        totals = [box["build"], dome["build"]]
        if key == "home":
            fitout = [box.get("fitout", 0.0), dome.get("fitout", 0.0)]
            shell = [t - f for t, f in zip(totals, fitout)]
            axis.bar(labels, fitout, color="#d9d2c6", width=0.6, label="fit-out (the same)")
            axis.bar(labels, shell, bottom=fitout, color=[C.MUTED, C.LONG], width=0.6,
                     label="shell and envelope")
            axis.legend(loc="lower center", fontsize=8.5, bbox_to_anchor=(0.5, -0.32), ncol=2)
        else:
            axis.bar(labels, totals, color=[C.MUTED, C.LONG], width=0.6)
        for index, total in enumerate(totals):
            axis.text(index, total * 1.02, _money(total), ha="center", va="bottom",
                      fontsize=10, fontweight="bold")
        cut = 1.0 - totals[1] / totals[0]
        axis.set_ylim(0, max(totals) * 1.2)
        axis.set_title(title, loc="left")
        axis.text(0.98, 0.97, f"dome {cut * 100:.0f}% less", transform=axis.transAxes,
                  ha="right", va="top", color=C.LONG, fontsize=10.5, fontweight="bold")
        axis.yaxis.set_major_formatter(lambda value, _pos: f"${value / 1000:,.0f}k")
    fig.tight_layout(pad=1.2)
    return _save(fig, path, size)


def chart_frequency(path: Path, size) -> Path:
    from . import science
    plt = _setup()
    ladder = science.ladder()
    fig, (left, right) = plt.subplots(1, 2, gridspec_kw={"width_ratios": [1.7, 1]})
    labels = [f"{step.frequency}V" for step in ladder]
    struts = [step.struts for step in ladder]
    bars = left.bar(labels, struts, color=[C.LONG if step.frequency == 2 else C.SHORT
                                           for step in ladder], width=0.62)
    for bar, step in zip(bars, ladder):
        left.text(bar.get_x() + bar.get_width() / 2, step.struts + max(struts) * 0.02,
                  f"{step.struts} struts\n{step.strut_classes} length"
                  f"{'s' if step.strut_classes != 1 else ''}\n{step.hubs} hubs",
                  ha="center", va="bottom", fontsize=8.8)
    left.set_ylim(0, max(struts) * 1.42)
    left.set_title("Parts at one radius", loc="left")
    left.set_ylabel("struts")
    heights = [step.height_m / step.radius_m for step in ladder]
    bars = right.bar(labels, heights, color=[C.LONG if abs(h - 1.0) < 1e-6 else C.MUTED
                                             for h in heights], width=0.62)
    right.axhline(1.0, color=C.RULE, linewidth=1.0, linestyle="--")
    for bar, value in zip(bars, heights):
        right.text(bar.get_x() + bar.get_width() / 2, value + 0.02, f"{value:.2f}",
                   ha="center", va="bottom", fontsize=9, fontweight="bold")
    right.set_ylim(0, max(heights) * 1.25)
    right.set_title("Height over radius", loc="left")
    right.text(0.5, -0.2, "even frequencies stop at the equator", transform=right.transAxes,
               ha="center", fontsize=8.5, color=C.MUTED)
    fig.tight_layout(pad=1.2)
    return _save(fig, path, size)


def chart_house(path: Path, size) -> Path:
    from two_v_demo import house_economics as he
    plt = _setup()
    split = he.house()
    fig, axis = plt.subplots(1, 1)
    parts = [(label, split.parts[key]) for key, label, _d in he.PRICE_PARTS]
    buckets = list(split.buckets.items())
    palette = [C.MUTED, C.LONG, "#8fb3c4", "#c9c1b3", "#e3d7bf", C.SHORT, "#a4905f", "#6b8f71"]
    for row, (name, series) in enumerate((("who is paid", parts), ("what it buys", buckets))):
        total = sum(value for _l, value in series)
        left = 0.0
        small = []
        for index, (label, value) in enumerate(series):
            share = value / total
            axis.barh(row, share, left=left, color=palette[index % len(palette)],
                      edgecolor="white", height=0.62)
            if share >= 0.06:
                axis.text(left + share / 2, row,
                          f"{textwrap.fill(label.capitalize(), 12)}\n{share * 100:.0f}%",
                          ha="center", va="center", fontsize=8.2,
                          color="white" if index in (0, 1, 5) else C.INK)
            else:
                small.append(f"{label.lower()} {share * 100:.0f}%")
            left += share
        if small:
            axis.text(1.0, row + 0.36, "also " + ", ".join(small), ha="right", va="top",
                      fontsize=7.8, color=C.MUTED)
    axis.set_yticks([0, 1], ["who is paid", "what it buys"])
    axis.set_ylim(1.62, -0.45)
    axis.set_xlim(0, 1)
    axis.xaxis.set_major_formatter(lambda value, _pos: f"{value * 100:.0f}%")
    axis.set_title(f"A {_money(split.price)} new house, by share of price", loc="left")
    fig.tight_layout(pad=1.2)
    return _save(fig, path, size)


def _loop(axis, loop, **style):
    xs = [p[0] for p in loop] + [loop[0][0]]
    ys = [p[1] for p in loop] + [loop[0][1]]
    axis.plot(xs, ys, **style)


def chart_pattern(path: Path, size) -> Path:
    from dome_forge import patterns
    from . import science
    plt = _setup()
    pattern = patterns.build_pattern("pentagon", science.REFERENCE_LONG_IN, 2.0)
    fig, axis = plt.subplots(1, 1)
    from matplotlib.patches import Polygon
    axis.add_patch(Polygon(pattern.net, closed=True, facecolor="#f6efe2", edgecolor="none"))
    _loop(axis, pattern.outline, color=C.MUTED, linewidth=1.1, linestyle="--")
    _loop(axis, pattern.net, color=C.INK, linewidth=1.6)
    for a, b in pattern.folds:
        axis.plot([a[0], b[0]], [a[1], b[1]], color=C.SHORT, linewidth=1.2, linestyle=":")
    if pattern.dart:
        axis.add_patch(Polygon(pattern.dart, closed=True, facecolor=C.LONG, alpha=0.35,
                               edgecolor=C.LONG))
        # Label the dart just beyond its open end, clear of the spoke dimensions.
        hub, rim_a, rim_b = pattern.dart[1], pattern.dart[0], pattern.dart[2]
        rim = ((rim_a[0] + rim_b[0]) / 2, (rim_a[1] + rim_b[1]) / 2)
        spot = (hub[0] + (rim[0] - hub[0]) * 1.22, hub[1] + (rim[1] - hub[1]) * 1.22)
        axis.text(spot[0], spot[1], f"dart {pattern.dart_angle:.1f}°", color=C.LONG,
                  ha="left", va="center", fontsize=10, fontweight="bold",
                  bbox={"boxstyle": "round,pad=0.2", "fc": "white", "ec": "none"})
    net = [tuple(map(float, point)) for point in pattern.net]
    for a, b in zip(net, net[1:] + net[:1]):
        length = math.dist(a, b)
        mid = ((a[0] + b[0]) / 2, (a[1] + b[1]) / 2)
        # Round to the sixteenth first, so 71.99 in reads 6' 0", not 5' 12.0".
        feet, inches = divmod(round(length * 16) / 16, 12.0)
        axis.text(mid[0], mid[1], f"{int(feet)}′ {_fraction(inches)}", fontsize=8,
                  color=C.MUTED, ha="center", va="center",
                  bbox={"boxstyle": "round,pad=0.15", "fc": "white", "ec": "none"})
    axis.set_aspect("equal")
    axis.axis("off")
    axis.set_title(f"Pentagon cover, long strut {science.REFERENCE_LONG_IN:.0f} in, "
                   f"seam allowance {pattern.seam:.0f} in", loc="left")
    fig.tight_layout(pad=1.0)
    return _save(fig, path, size)


def chart_nesting(path: Path, size) -> Path:
    from dome_forge import patterns
    from . import science
    plt = _setup()
    long_in, seam = science.REFERENCE_LONG_IN, 2.0
    sheet_w, sheet_h = 25 * 12.0, 10 * 12.0
    keys = ["pentagon_3", "pentagon_2"] * 6
    placements = patterns.auto_nest(keys, long_in, seam, sheet_w, sheet_h)
    sheets = sorted({p.sheet for p in placements})
    usage = patterns.sheet_usage(placements, long_in, seam, sheet_w, sheet_h)
    cols = 2 if len(sheets) > 1 else 1
    rows = math.ceil(len(sheets) / cols)
    fig, axes = plt.subplots(rows, cols, squeeze=False)
    from matplotlib.patches import Polygon, Rectangle
    for spare in range(len(sheets), rows * cols):
        axes[spare // cols][spare % cols].axis("off")
    for number, sheet in enumerate(sheets):
        axis = axes[number // cols][number % cols]
        axis.add_patch(Rectangle((0, 0), sheet_w, sheet_h, facecolor="#f3f1ec", edgecolor=C.RULE))
        for placement in placements:
            if placement.sheet != sheet:
                continue
            _pattern, outline, net, folds, _dart = patterns.placed_geometry(placement, long_in, seam)
            axis.add_patch(Polygon(net, closed=True, facecolor="#f6e6c8", edgecolor=C.INK,
                                   linewidth=0.9))
            _loop(axis, outline, color=C.MUTED, linewidth=0.7, linestyle="--")
            for a, b in folds:
                axis.plot([a[0], b[0]], [a[1], b[1]], color=C.SHORT, linewidth=0.8, linestyle=":")
        axis.set_xlim(-4, sheet_w + 4)
        axis.set_ylim(-4, sheet_h + 4)
        axis.set_aspect("equal")
        axis.axis("off")
        axis.set_title(f"sheet {sheet + 1}: {usage.get(sheet, 0) * 100:.0f}% used", loc="left",
                       fontsize=10)
    fig.tight_layout(pad=0.8)
    return _save(fig, path, size)


def _fraction(inches: float, denominator: int = 16) -> str:
    """Inches as a tape measure reads them, to the nearest sixteenth."""
    whole = int(inches)
    parts = round((inches - whole) * denominator)
    if parts == denominator:
        whole, parts = whole + 1, 0
    if parts == 0:
        return f"{whole}″"
    common = math.gcd(parts, denominator)
    return f"{whole} {parts // common}/{denominator // common}″"


def chart_panel_drawing(path: Path, size) -> Path:
    """Both pinwheel panels, flattened and dimensioned, at the build plan's size."""
    import numpy as np
    from matplotlib.patches import Polygon
    from two_v_demo import wedge_geometry as wg
    from two_v_demo import book_math as bm
    plt = _setup()
    # The book's own dome: the same plan and solve the {{dome.*}} tokens read.
    plan, dome = bm.BOOK_TREE, bm.tree_first()
    gasket = bm.declared("gasket_thickness_in")
    width = plan.member_width_in
    kinds: dict[tuple, list] = {}
    for panel in wg.pinwheel_panels(dome.radius_in, width, gasket):
        signature = tuple(sorted(member.edge_class for member in panel.members))
        kinds.setdefault(signature, []).append(panel)
    order = sorted(kinds, key=lambda signature: signature.count("LONG"), reverse=True)
    fig, axes = plt.subplots(1, len(order))
    gaps = []
    for axis, signature in zip(np.atleast_1d(axes), order):
        panel = kinds[signature][0]
        origin = panel.corners[0]
        axis_u = panel.corners[1] - origin
        axis_u = axis_u / np.linalg.norm(axis_u)
        axis_v = np.cross(panel.normal, axis_u)
        axis_v = axis_v / np.linalg.norm(axis_v)

        def flat(point):
            offset = np.asarray(point) - origin
            return np.array([float(offset @ axis_u), float(offset @ axis_v)])

        corners = [flat(corner) for corner in panel.corners]
        loop = corners + corners[:1]
        axis.plot([p[0] for p in loop], [p[1] for p in loop], color=C.MUTED, linewidth=0.9,
                  linestyle=(0, (4, 3)))
        for member in panel.members:
            tail, head = flat(member.tail), flat(member.head)
            inward = np.array([float(member.inward @ axis_u), float(member.inward @ axis_v)])
            inward = inward / np.linalg.norm(inward)
            half = inward * width / 2.0
            colour = C.LONG if member.edge_class == "LONG" else C.SHORT
            axis.add_patch(Polygon([tail - half, head - half, head + half, tail + half],
                                   closed=True, facecolor=colour, alpha=0.30,
                                   edgecolor=colour, linewidth=1.3))
            angle = math.degrees(math.atan2(head[1] - tail[1], head[0] - tail[0]))
            if angle > 90:
                angle -= 180
            elif angle < -90:
                angle += 180
            middle = (tail + head) / 2.0 + inward * width * 1.45
            axis.text(middle[0], middle[1], _fraction(member.length_in), rotation=angle,
                      rotation_mode="anchor", ha="center", va="center", fontsize=10.5,
                      fontweight="bold", color=C.INK)
            a, b = corners[member.position], corners[(member.position + 1) % 3]
            outside = (a + b) / 2.0 - inward * width * 1.0
            axis.text(outside[0], outside[1], f"edge {_fraction(member.edge_length_in)}",
                      rotation=angle, rotation_mode="anchor", ha="center", va="center",
                      fontsize=8.3, color=C.MUTED)
            gaps += [member.tail_vertex_gap_in, member.head_vertex_gap_in]
        name = "Equilateral" if len(set(signature)) == 1 else "Isosceles"
        makeup = ", ".join(f"{signature.count(c)} {c.lower()}" for c in ("LONG", "SHORT")
                           if signature.count(c))
        axis.set_title(f"{name} panel: {makeup}; {len(kinds[signature])} per dome", loc="left",
                       fontsize=11)
        xs, ys = [p[0] for p in corners], [p[1] for p in corners]
        pad = width * 2.2
        axis.set_xlim(min(xs) - pad, max(xs) + pad)
        axis.set_ylim(min(ys) - pad, max(ys) + pad)
        axis.set_aspect("equal")
        axis.axis("off")
    fig.text(0.5, 0.035,
             f"Build radius {dome.radius_in / 12:.1f} ft; member width {width:.1f} in; gasket "
             f"{gasket:.2f} in. Dashed: the true triangle. Every end stops "
             f"{min(gaps):.1f} to {max(gaps):.1f} in short of its corner.",
             ha="center", fontsize=8.6, color=C.MUTED)
    fig.tight_layout(pad=1.0, rect=(0, 0.06, 1, 1))
    return _save(fig, path, size)


CHARTS = {
    "panel_drawing": chart_panel_drawing,
    "skin": chart_skin,
    "comparison": chart_comparison,
    "frequency": chart_frequency,
    "house": chart_house,
    "pattern": chart_pattern,
    "nesting": chart_nesting,
}


def render(name: str, path: Path, size) -> Path:
    return CHARTS[name](Path(path), size)
