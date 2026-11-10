"""The four pictures this book draws for itself.

Everything else in *The Wedge Method* is a photograph: either the raw-wedge
solver operated with settings that make one idea visible
(:mod:`wedge_book.figures`) or a frame of one of the project's films
(:mod:`wedge_book.plates`). Three pictures are not photographs, because the
thing they have to show is a *section*, and no camera in this project can cut
a building in half.

All three replace drawings that were wrong.

**The seam.** The old one showed two brown blobs with a yellow bar between
them, labelled "panel A + key + panel B". The blobs were not triangles, the
bar was not the shape of a key, and the angle between them -- which is the
entire point of a seam -- was not in the picture at all. This one is the real
cross-section: the two sectors at the solved dihedral, and the key that fills
what they leave, every coordinate read off the solver.

**The mast and the floor**, and **the floating dome**, come from the shared
renderer in :mod:`two_v_demo.book_figures`, which had two faults this module's
fixes corrected: a floor that kept the base ring's radius however high it was
lifted, so it overhung the frame; and a drawing box locked at 1:1:0.66 while
the limits grew sideways for the trees, which stretched the hanging dome into
a cone.
"""

from __future__ import annotations

import math
from pathlib import Path

from . import store

FIGURE_DIR = store.BOOK_DIR / "figures"

#: Ink, matched to the book's other line drawings.
PAPER = "#ffffff"
TIMBER = "#a8763f"
TIMBER_EDGE = "#6d4a24"
SAWN_A = "#c9423a"
SAWN_B = "#3f9a45"
KEY = "#d9ae2e"
KEY_EDGE = "#8a6c15"
RULE = "#8b949e"
INK = "#1d2429"


# ----------------------------------------------------------------------
# The seam, in section
# ----------------------------------------------------------------------

def _slice_mesh(mesh, origin, normal, across, up) -> list[list[tuple]]:
    """Closed loops where ``mesh`` crosses the plane through ``origin``.

    A triangle crosses a plane in one segment. Collect every segment, then
    join them end to end into loops, which is what the outline of a solid cut
    by a plane is. Segments that do not close -- a mesh with an open edge at
    the cut -- are returned as open runs rather than dropped, because a
    picture that silently loses part of a member is worse than one that shows
    a gap.
    """
    import numpy as np

    vertices = np.asarray(mesh.vertices, dtype=np.float64)
    if vertices.size == 0:
        return []
    stride = vertices.size // max(1, (vertices.size // 10))
    points = vertices.reshape(-1, 10)[:, :3]
    indices = np.asarray(mesh.indices, dtype=np.int64).reshape(-1, 3)

    signed = (points - origin) @ normal
    segments: list[tuple[tuple[float, float], tuple[float, float]]] = []
    for tri in indices:
        d = signed[tri]
        if (d > 0).all() or (d < 0).all():
            continue
        hits = []
        for a, b in ((0, 1), (1, 2), (2, 0)):
            da, db = d[a], d[b]
            if da == db:
                continue
            if (da > 0) == (db > 0):
                continue
            t = da / (da - db)
            hits.append(points[tri[a]] + (points[tri[b]] - points[tri[a]]) * t)
        if len(hits) != 2:
            continue
        flat = []
        for hit in hits:
            delta = hit - origin
            flat.append((float(delta @ across), float(delta @ up)))
        if flat[0] != flat[1]:
            segments.append((flat[0], flat[1]))

    return _join(segments)


def _join(segments, tolerance: float = 1.0e-6) -> list[list[tuple]]:
    """Chain segments end to end into loops."""
    def key(point):
        return (round(point[0] / tolerance), round(point[1] / tolerance))

    remaining = list(segments)
    loops: list[list[tuple]] = []
    while remaining:
        chain = list(remaining.pop())
        grew = True
        while grew:
            grew = False
            for index, (a, b) in enumerate(remaining):
                if key(a) == key(chain[-1]):
                    chain.append(b)
                elif key(b) == key(chain[-1]):
                    chain.append(a)
                elif key(a) == key(chain[0]):
                    chain.insert(0, b)
                elif key(b) == key(chain[0]):
                    chain.insert(0, a)
                else:
                    continue
                remaining.pop(index)
                grew = True
                break
        if len(chain) >= 3:
            loops.append(chain)
    return loops


def seam_section_geometry(seam_id: str = "SEAM_A_016",
                          orientation: str = "point_dome_in",
                          seam_join_mode: str = "raw_trapezoid") -> dict:
    """The true cross-section of one seam, cut out of the solved meshes.

    The plane is perpendicular to the seam's own tangent at its midpoint, so
    what comes out is what a saw would see if it cut the building across the
    joint. The members and the key are the solver's triangles, intersected --
    not a reconstruction from the angles.

    ``orientation`` is one of the four cardinal wedge orientations the dome
    can be built in (``point_dome_in``, ``point_panel_in``,
    ``point_dome_out``, ``point_panel_out``). Rotating a member about its own
    axis does not change the 45-degree sector, but it does change which of
    its faces meets the key -- which is the whole subject of the book's
    orientation chapter, so the section is worth being able to cut in each.

    ``seam_join_mode`` is the solver's own choice of joint: ``raw_trapezoid``
    (the split faces left exactly as sawn, with a tapered key) or
    ``shaved_flat`` (a land planed parallel and one flat key throughout).
    """
    import numpy as np

    from . import numbers

    rw = numbers.solver()
    model = numbers.reference_model(wedge_orientation=orientation,
                                    seam_join_mode=seam_join_mode)
    seam = next(s for s in model.seams if s.seam_id == seam_id)

    # Only this seam's own parts. A plane through one seam cuts the whole
    # building, so slicing build_world_meshes gave every member anywhere on
    # that plane -- a scatter of unrelated offcuts with the subject lost in
    # it. The two members that meet here are the two that share this edge,
    # one from each of the panels either side.
    wood = rw.MeshAccumulator()
    for member in model.members:
        if member.edge_key != seam.edge_key:
            continue
        if member.face_index not in (seam.face_a, seam.face_b):
            continue
        rw.add_raw_sector_member(wood, model, member,
                                 np.zeros(3, dtype=np.float64))
    rigid = rw.MeshAccumulator()
    rw.add_rigid_spacer(rigid, model, seam)
    meshes = {"wood": wood.finish(), "rigid": rigid.finish()}

    tangent = np.asarray(seam.tangent, dtype=np.float64)
    tangent = tangent / np.linalg.norm(tangent)
    origin = (np.asarray(seam.start) + np.asarray(seam.end)) * 0.5

    # A frame in the cutting plane: "up" is radially outward from the sphere
    # centre, so the picture has the weather at the top.
    radial = origin / np.linalg.norm(origin)
    up = radial - tangent * float(np.dot(radial, tangent))
    up = up / np.linalg.norm(up)
    across = np.cross(up, tangent)
    across = across / np.linalg.norm(across)

    def flat(point) -> tuple[float, float]:
        delta = np.asarray(point, dtype=np.float64) - origin
        return (float(delta @ across), float(delta @ up))

    return {
        "members": _slice_mesh(meshes["wood"], origin, tangent, across, up),
        "key": _slice_mesh(meshes["rigid"], origin, tangent, across, up),
        "apex": flat((np.asarray(seam.apex_start)
                      + np.asarray(seam.apex_end)) * 0.5),
        "point_a": flat((np.asarray(seam.point_a_start)
                         + np.asarray(seam.point_a_end)) * 0.5),
        "point_b": flat((np.asarray(seam.point_b_start)
                         + np.asarray(seam.point_b_end)) * 0.5),
        "fold_deg": seam.fold_angle_deg,
        "gap_deg": seam.raw_gap_angle_deg,
        "dihedral_deg": seam.internal_dihedral_deg,
        "key_base_in": seam.spacer_base_width_in,
        "contact_in": seam.contact_depth_in,
        "seam_id": seam.seam_id,
        "orientation": orientation,
        "seam_join_mode": model.config.seam_join_mode,
        "edge_type": seam.edge_type,
        "sector_deg": 360.0 / model.config.radial_splits,
        "trunk_in": model.config.trunk_diameter_in,
    }


def seam_section(path: Path | None = None,
                 seam_id: str = "SEAM_A_016") -> Path:
    """Draw the seam in section: two sectors, the gap, and the key in it."""
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    from matplotlib.patches import Polygon

    facts = seam_section_geometry(seam_id)
    fig, axes = plt.subplots(figsize=(7.1, 3.9), dpi=200)
    fig.patch.set_facecolor(PAPER)
    axes.set_facecolor(PAPER)
    axes.set_aspect("equal")
    axes.axis("off")

    for loop in facts["members"]:
        axes.add_patch(Polygon(loop, closed=True, facecolor=TIMBER,
                               edgecolor=TIMBER_EDGE, linewidth=1.0,
                               zorder=2))
    for loop in facts["key"]:
        axes.add_patch(Polygon(loop, closed=True, facecolor=KEY,
                               edgecolor=KEY_EDGE, linewidth=1.2, zorder=4))

    everything = [p for loop in facts["members"] + facts["key"]
                  for p in loop]
    xs = [p[0] for p in everything]
    ys = [p[1] for p in everything]
    top = max(ys)
    bottom = min(ys)

    axes.annotate("outside \u2014 the weather", (0.0, top + 0.9), color=RULE,
                  fontsize=8.5, ha="center", va="bottom", zorder=6)
    axes.annotate("inside", (0.0, bottom - 0.9), color=RULE, fontsize=8.5,
                  ha="center", va="top", zorder=6)
    axes.annotate("panel A", (min(xs) - 0.6, (top + bottom) * 0.5),
                  color=INK, fontsize=9.0, ha="right", va="center", zorder=6)
    axes.annotate("panel B", (max(xs) + 0.6, (top + bottom) * 0.5),
                  color=INK, fontsize=9.0, ha="left", va="center", zorder=6)
    axes.annotate(
        f"the key \u2014 {facts['key_base_in']:.2f} in across its base",
        (0.0, top + 2.6), color=KEY_EDGE, fontsize=9.5, ha="center",
        va="bottom", weight="bold", zorder=6)
    axes.annotate(
        f"{facts['edge_type']} seam \u00b7 the two sawn faces are "
        f"{facts['gap_deg']:.2f}\u00b0 apart \u00b7 fold "
        f"{facts['fold_deg']:.2f}\u00b0 \u00b7 "
        f"{facts['sector_deg']:.0f}\u00b0 sector of a "
        f"{facts['trunk_in']:.0f} in log",
        (0.5, 0.015), xycoords="axes fraction", color=RULE, fontsize=8.0,
        ha="center", va="bottom")

    pad = 1.6
    axes.set_xlim(min(xs) - pad * 3.4, max(xs) + pad * 3.4)
    axes.set_ylim(bottom - pad * 1.8, top + pad * 3.2)
    fig.tight_layout(pad=0.2)

    path = path or (FIGURE_DIR / "seam-section.png")
    path.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(path, facecolor=PAPER)
    plt.close(fig)
    return path


# ----------------------------------------------------------------------
# The mast, the floor and the rig -- through the shared renderer
# ----------------------------------------------------------------------

def _mast(key: str, rig: bool, floor_height_in: float, view: str) -> Path:
    from two_v_demo.book import Figure as BookFigure
    from two_v_demo.book_figures import render_mast_floor

    figure = BookFigure(
        key=key, caption="", source="mast_floor",
        spec={"rig": rig, "floor": True,
              "floor_height_in": floor_height_in, "view": view})
    target = FIGURE_DIR / f"{key}.png"
    if target.exists():
        target.unlink()
    return render_mast_floor(figure, key, FIGURE_DIR)


def mast_and_floor() -> Path:
    """The mast through the column, and the floor clamped to it.

    The floor sits a foot off the ground -- where a floor goes -- and is
    inset to the dome at that height, which the earlier render was not.
    """
    return _mast("mast-and-floor", rig=False, floor_height_in=12.0,
                 view="three_quarter")


def floating_dome() -> Path:
    """The same mast and floor, hung on three cables."""
    return _mast("floating-dome", rig=True, floor_height_in=12.0,
                 view="hero")


def breathing_cap(path: Path | None = None) -> Path:
    """A section through the dome: how a cap with no hole in it breathes.

    The profile is the solver's own -- the apex, the pentagon ring, the belt
    and the rim at their solved heights and radii -- and every number on it
    comes from :mod:`two_v_demo.seam_vent`. Blue is the cap, unbroken; amber
    is the exhaust falling through the seam channels; green is fresh air.
    """
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    from matplotlib.patches import FancyArrowPatch

    from two_v_demo import seam_climate as sc, seam_vent as sv

    rings = sc.rings()
    R = rings["apex_height_ft"]
    levels = rings["levels"]                       # heights as fractions of R, rim to apex
    pts = [(math.sqrt(max(0.0, 1 - z * z)) * R, z * R) for z in levels]
    route = sv.descending_seams()
    table = sv.weather_table()
    winter = next(r for r in table if r["weather"] == "winter")
    summer = table[-1]

    fig, ax = plt.subplots(figsize=(7.2, 4.6), dpi=220)
    fig.patch.set_facecolor(PAPER)
    cap = "#2f6fae"
    exhaust = "#d98a1c"
    fresh = "#3f9a45"
    for side in (-1, 1):
        xs = [side * x for x, _ in pts]
        ys = [y for _, y in pts]
        ax.plot(xs, ys, color=cap, linewidth=3.2, solid_capstyle="round", zorder=3)
        inner = [(side * x * 0.93, y * 0.93) for x, y in pts]
        ax.plot([q[0] for q in inner], [q[1] for q in inner], color=TIMBER, linewidth=6, alpha=0.35, zorder=2)
        # exhaust falling in the channel, crown to rim
        for (x0, y0), (x1, y1) in zip(inner[::-1][:-1], inner[::-1][1:]):
            ax.add_patch(FancyArrowPatch((x0, y0), (x1, y1), arrowstyle="-|>", mutation_scale=11,
                                         color=exhaust, linewidth=1.8, zorder=4))
        # the brim and a port under it, facing the ground
        bx = side * R
        ax.plot([bx, bx + side * 0.9], [0.25, -0.05], color=cap, linewidth=3.2, zorder=3)
        ax.add_patch(FancyArrowPatch((bx * 0.97, 0.0), (bx * 0.97, -0.9), arrowstyle="-|>", mutation_scale=12,
                                     color=exhaust, linewidth=2.0, zorder=4))
    # fresh air in, low, through its own downward ports
    ax.add_patch(FancyArrowPatch((-R * 0.80, -0.9), (-R * 0.80, 0.1), arrowstyle="-|>", mutation_scale=12,
                                 color=fresh, linewidth=2.0, zorder=4))
    ax.add_patch(FancyArrowPatch((-R * 0.78, 0.4), (-R * 0.45, 1.2), arrowstyle="-|>", mutation_scale=12,
                                 color=fresh, linewidth=1.6, zorder=4))
    # room air rising to the crown grille
    ax.add_patch(FancyArrowPatch((0, 1.0), (0, R * 0.86), arrowstyle="-|>", mutation_scale=14,
                                 color="#b0552a", linewidth=2.2, zorder=4))
    ax.plot([-0.5, 0.5], [R * 0.9, R * 0.9], color=INK, linewidth=2.4, zorder=5)
    ax.axhline(0, color=RULE, linewidth=1.0, zorder=1)

    def say(x, y, text, colour=INK, ha="center", size=6.6):
        ax.text(x, y, text, color=colour, ha=ha, va="center", fontsize=size, zorder=6)

    say(0, R * 1.07, f"the cap: {route.cap_penetrations} holes above the rim", cap)
    say(0.7, R * 0.70, "the crown grille,\ninside the shell", INK, ha="left")
    say(0.4, R * 0.45, "the room's warm, wet air\nrises to the crown", "#b0552a", ha="left")
    say(R * 0.78, R * 1.0, f"down {route.seams_down} falling seams,\ninside the keys", exhaust, ha="left")
    say(R * 1.08, -1.25, "stale air out,\nfacing the ground", exhaust)
    say(-R * 0.80, -1.25, "fresh air in,\nfacing the ground", fresh)
    say(0, -2.05, f"winter: the falling air pulls itself down -- {winter['drive_pa']:.1f} Pa, "
        f"{100 * winter['share']:.0f}% of the {sv.need_cfm():.1f} cfm the dome needs, no fan. "
        f"Summer sun: a {summer['fan_pa']:.0f} Pa fan does it.", INK, size=6.3)
    ax.set_xlim(-R * 1.35, R * 1.45)
    ax.set_ylim(-2.4, R * 1.18)
    ax.set_aspect("equal")
    ax.axis("off")
    target = path or FIGURE_DIR / "breathing-cap.png"
    fig.savefig(target, facecolor=PAPER, bbox_inches="tight")
    plt.close(fig)
    return target


# ----------------------------------------------------------------------
# The structural grammar: the wedge as a general member.  These are the
# sections and assemblies Part 16 argues, every outline read off the same
# solver the dome is built from (two_v_demo.wedge_why_facts.sector_at_diameter)
# and every bar read off two_v_demo.wedge_grammar.
# ----------------------------------------------------------------------

WEAK = "#c9b79a"
"""A muted tan for the weak-axis bars, against TIMBER for the strong axis."""


def _xform(points, scale: float = 1.0, rot_deg: float = 0.0,
           dx: float = 0.0, dy: float = 0.0) -> list[tuple[float, float]]:
    """Scale, rotate and translate a section outline for the page."""
    a = math.radians(rot_deg)
    ca, sa = math.cos(a), math.sin(a)
    out = []
    for y, z in points:
        y, z = y * scale, z * scale
        out.append((dx + y * ca - z * sa, dy + y * sa + z * ca))
    return out


def wedge_families(path: Path | None = None) -> Path:
    """The equal-area split families: the profiles, and their second moments.

    Left, the four sectors and a dressed two-by-four, every one holding the
    same cross-sectional area, drawn to a common scale so the deepening and
    narrowing is the thing you see.  Right, the strong- and weak-axis second
    moment of each, so the crossing lines -- strong up, weak down -- are on
    the same page as the shapes that cause them.
    """
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    from matplotlib.patches import Polygon

    from two_v_demo import wedge_grammar as g, wedge_why_facts as yf

    rows = g.equal_area_families()
    stud = yf.dressed_stud()

    fig, (axl, axr) = plt.subplots(1, 2, figsize=(7.4, 4.2), dpi=200,
                                   gridspec_kw={"width_ratios": [1.15, 1.0]})
    fig.patch.set_facecolor(PAPER)
    for ax in (axl, axr):
        ax.set_facecolor(PAPER)

    # Left: the profiles, apex down, on a shared baseline.
    axl.set_aspect("equal")
    axl.axis("off")
    x = 0.0
    specs = [("2x4", stud.points, stud.depth_in)] + [
        (r.name, yf.sector_at_diameter(round(g.diameter_for_area(stud.area_in2,
         r.splits), 6), r.splits).points, r.radial_depth_in) for r in rows]
    gap = 1.1
    allpts: list[tuple[float, float]] = []
    for label, pts, depth in specs:
        low = min(p[0] for p in pts)
        shifted = _xform(pts, dx=x - low)
        allpts += shifted
        axl.add_patch(Polygon(shifted, closed=True, facecolor=TIMBER,
                              edgecolor=TIMBER_EDGE, linewidth=0.9, zorder=2))
        left = min(p[0] for p in shifted)
        right = max(p[0] for p in shifted)
        axl.annotate(label, ((left + right) * 0.5, -0.6),
                     color=INK, fontsize=8.5, ha="center", va="top")
        x = right + gap
    # Patches do not autoscale the axes, so set the window to the shapes.
    xs = [p[0] for p in allpts]
    ys = [p[1] for p in allpts]
    axl.set_xlim(min(xs) - 0.8, max(xs) + 0.8)
    axl.set_ylim(min(ys) - 1.6, max(ys) + 0.8)

    # Right: strong- and weak-axis second moment, side by side.
    names = ["2x4"] + [r.name for r in rows]
    strong = [stud.i_yy_in4] + [r.i_strong_in4 for r in rows]
    weak = [stud.i_zz_in4] + [r.i_weak_in4 for r in rows]
    ys = list(range(len(names)))[::-1]
    h = 0.38
    axr.barh([y + h / 2 for y in ys], strong, height=h, color=TIMBER,
             edgecolor=TIMBER_EDGE, linewidth=0.6, label="I, strong axis")
    axr.barh([y - h / 2 for y in ys], weak, height=h, color=WEAK,
             edgecolor=TIMBER_EDGE, linewidth=0.6, label="I, weak axis")
    axr.set_yticks(ys)
    axr.set_yticklabels(names, fontsize=8.5, color=INK)
    axr.set_xlabel("second moment of area, in⁴", fontsize=8.5, color=INK)
    axr.tick_params(labelsize=7.5, colors=RULE)
    for spine in ("top", "right"):
        axr.spines[spine].set_visible(False)
    axr.legend(fontsize=7.5, frameon=False, loc="lower right")

    fig.suptitle("One two-by-four's worth of wood, as four different blades",
                 fontsize=10.0, color=INK, weight="bold")
    fig.tight_layout(rect=(0, 0, 1, 0.95))
    path = path or (FIGURE_DIR / "grammar-families.png")
    path.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(path, facecolor=PAPER)
    plt.close(fig)
    return path


def wedge_composite(path: Path | None = None) -> Path:
    """The connection law: the same wood, loose and composite.

    Left, planks stacked one to eight, each at its loose bound (members
    sliding) and its glued bound (one section) -- the ratio is n squared.
    Right, two wedge chords held apart by a web, the composite stiffness
    climbing with the square of the spacing.  The point of both is the gap:
    it is the work the connection has to do, and it is not free.
    """
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt

    from two_v_demo import wedge_grammar as g

    stack = g.lamina_stack_bounds()
    chords = g.separated_chord_bounds()

    fig, (axl, axr) = plt.subplots(1, 2, figsize=(7.4, 4.0), dpi=200)
    fig.patch.set_facecolor(PAPER)
    for ax in (axl, axr):
        ax.set_facecolor(PAPER)
        for spine in ("top", "right"):
            ax.spines[spine].set_visible(False)
        ax.tick_params(labelsize=8.0, colors=RULE)

    xs = list(range(len(stack)))
    w = 0.38
    axl.bar([x - w / 2 for x in xs], [b.i_independent_in4 for b in stack],
            width=w, color=WEAK, edgecolor=TIMBER_EDGE, linewidth=0.6,
            label="loose (slides)")
    axl.bar([x + w / 2 for x in xs], [b.i_composite_in4 for b in stack],
            width=w, color=TIMBER, edgecolor=TIMBER_EDGE, linewidth=0.6,
            label="glued (one section)")
    for x, b in zip(xs, stack):
        axl.annotate(f"{b.premium:.0f}×", (x + w / 2, b.i_composite_in4),
                     color=INK, fontsize=8.0, ha="center", va="bottom")
    axl.set_yscale("log")
    axl.set_xticks(xs)
    axl.set_xticklabels([f"{b.members}" for b in stack])
    axl.set_xlabel("planks stacked", fontsize=8.5, color=INK)
    axl.set_ylabel("stiffness, in⁴ (log)", fontsize=8.5, color=INK)
    axl.set_title("n planks: glued is n² stiffer", fontsize=9.0, color=INK)
    axl.legend(fontsize=7.5, frameon=False, loc="upper left")

    sx = [c.separation_depths for c in chords]
    axr.plot(sx, [c.premium for c in chords], marker="o", color=TIMBER,
             linewidth=2.0)
    axr.axhline(1.0, color=RULE, linewidth=1.0, linestyle="--")
    for c in chords:
        axr.annotate(f"{c.premium:.1f}×", (c.separation_depths, c.premium),
                     color=INK, fontsize=8.0, ha="left", va="bottom")
    axr.set_xlabel("chord spacing, in member depths", fontsize=8.5, color=INK)
    axr.set_ylabel("composite ÷ loose", fontsize=8.5, color=INK)
    axr.set_title("separated chords: spread them apart", fontsize=9.0, color=INK)
    axr.annotate("loose = 1×", (sx[0], 1.0), color=RULE, fontsize=7.5,
                 ha="left", va="top")

    fig.suptitle("A bundle is not a beam until the shear is carried",
                 fontsize=10.0, color=INK, weight="bold")
    fig.tight_layout(rect=(0, 0, 1, 0.95))
    path = path or (FIGURE_DIR / "grammar-composite.png")
    path.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(path, facecolor=PAPER)
    plt.close(fig)
    return path


def wedge_dyad(path: Path | None = None) -> Path:
    """The dyad in elevation: opposite sector, reversed fat-to-thin.

    A single tapered member runs fat at one end to thin at the other.  Its
    diametric mate, turned end for end, runs the other way, so the pair's
    outer edges come back to parallel and the lengthwise variation averages
    out.  The taper is the example pine's own, from its two measured
    circumferences.
    """
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    from matplotlib.patches import Polygon

    from two_v_demo import wedge_grammar as g

    r_fat = g.BUTT_CIRCUMFERENCE_IN / (2.0 * math.pi)
    r_thin = g.TOP_CIRCUMFERENCE_IN / (2.0 * math.pi)
    # One section's depth tapers from the fat radius to the thin radius over
    # a strut length; draw it long and low so the taper reads.
    length = 60.0
    gap = 1.2

    def member(flip: bool, base: float):
        # bark edge is the depth; point edge sits on the member's own centre.
        left_d = r_thin if flip else r_fat
        right_d = r_fat if flip else r_thin
        return [(0.0, base), (length, base),
                (length, base + right_d), (0.0, base + left_d)]

    fig, ax = plt.subplots(figsize=(7.6, 4.0), dpi=240)
    fig.patch.set_facecolor(PAPER)
    ax.set_facecolor(PAPER)
    ax.set_aspect("equal")
    ax.axis("off")

    top = member(flip=False, base=gap)
    bottom = member(flip=True, base=-gap - r_fat)
    for loop, tag in ((top, "sector i"), (bottom, "mate  i + N/2, reversed")):
        ax.add_patch(Polygon(loop, closed=True, facecolor=TIMBER,
                             edgecolor=TIMBER_EDGE, linewidth=1.2, zorder=2))
        ax.annotate(tag, (length * 0.5, loop[0][1] + (loop[3][1] - loop[0][1]) * 0.5),
                    color=PAPER, fontsize=9.5, ha="center", va="center",
                    zorder=5, weight="bold")
    # The envelope: the two reversed tapers make a parallel-sided pair.
    env_top = gap + r_fat
    env_bot = -gap - r_fat + r_thin
    for yy in (env_top, env_bot):
        ax.plot([0, length], [yy, yy], color=RULE, linewidth=0.8,
                linestyle=":", zorder=1)

    ax.annotate("fat", (-1.5, gap + r_fat * 0.5), color=RULE, fontsize=8.0,
                ha="right", va="center")
    ax.annotate("thin", (length + 1.5, gap + r_thin * 0.5), color=RULE,
                fontsize=8.0, ha="left", va="center")
    ax.annotate("thin", (-1.5, -gap - r_fat + r_thin * 0.5), color=RULE,
                fontsize=8.0, ha="right", va="center")
    ax.annotate("fat", (length + 1.5, -gap - r_fat + r_fat * 0.5), color=RULE,
                fontsize=8.0, ha="left", va="center")
    ax.set_title("The dyad: reverse the taper and the pair runs parallel",
                 fontsize=10.0, color=INK, weight="bold")
    ax.set_xlim(-8, length + 8)
    fig.tight_layout()
    path = path or (FIGURE_DIR / "grammar-dyad.png")
    path.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(path, facecolor=PAPER, bbox_inches="tight")
    plt.close(fig)
    return path


def wedge_archetypes(path: Path | None = None) -> Path:
    """Three assemblies the sector wants to become, in real section.

    The separated-chord beam, the hollow column and the box, each drawn from
    the actual split outline rather than a cartoon of one, so the void in the
    middle and the depth in the flanges are the member's own geometry.
    """
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    from matplotlib.patches import Polygon, Rectangle

    from two_v_demo import wedge_grammar as g, wedge_why_facts as yf

    stud = yf.dressed_stud()
    dia = g.diameter_for_area(stud.area_in2, 8)
    sector = yf.sector_at_diameter(round(dia, 6), 8).points
    R = dia * 0.5

    fig, axes = plt.subplots(1, 3, figsize=(7.6, 3.4), dpi=200)
    fig.patch.set_facecolor(PAPER)

    def draw(ax, loops, title, extra=None):
        ax.set_facecolor(PAPER)
        ax.set_aspect("equal")
        ax.axis("off")
        for loop in loops:
            ax.add_patch(Polygon(loop, closed=True, facecolor=TIMBER,
                                 edgecolor=TIMBER_EDGE, linewidth=0.9, zorder=2))
        if extra is not None:
            extra(ax)
        ax.set_title(title, fontsize=8.8, color=INK)
        allp = [p for loop in loops for p in loop]
        xs = [p[0] for p in allp]
        ys = [p[1] for p in allp]
        m = 0.18 * max(max(xs) - min(xs), max(ys) - min(ys))
        ax.set_xlim(min(xs) - m, max(xs) + m)
        ax.set_ylim(min(ys) - m * 2.4, max(ys) + m)

    # Separated-chord beam: two sectors, points toward a web between them.
    web = 0.9 * R
    top = _xform(sector, rot_deg=0.0, dy=web * 0.5)
    bottom = _xform(sector, rot_deg=180.0, dy=-web * 0.5)

    def beam_web(ax):
        ax.add_patch(Rectangle((-0.15 * R, -web * 0.5), 0.30 * R, web,
                               facecolor=KEY, edgecolor=KEY_EDGE,
                               linewidth=0.8, zorder=1))
    draw(axes[0], [top, bottom], "separated-chord beam", beam_web)

    # Hollow column: eight sectors, points inward, round a void.
    void = 0.55 * R
    ring = [_xform(_xform(sector, dy=void), rot_deg=k * 45.0) for k in range(8)]
    draw(axes[1], ring, "hollow column")

    # Box: four sectors, points inward, round a larger void.
    boxvoid = 0.7 * R
    box = [_xform(_xform(sector, dy=boxvoid), rot_deg=k * 90.0) for k in range(4)]
    draw(axes[2], box, "four-piece box")

    fig.suptitle("What the shape wants to become", fontsize=10.0, color=INK,
                 weight="bold")
    fig.tight_layout(rect=(0, 0, 1, 0.93))
    path = path or (FIGURE_DIR / "grammar-archetypes.png")
    path.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(path, facecolor=PAPER)
    plt.close(fig)
    return path


def render_all() -> dict[str, Path]:
    return {
        "seam-section": seam_section(),
        "mast-and-floor": mast_and_floor(),
        "floating-dome": floating_dome(),
        "breathing-cap": breathing_cap(),
        "grammar-families": wedge_families(),
        "grammar-composite": wedge_composite(),
        "grammar-dyad": wedge_dyad(),
        "grammar-archetypes": wedge_archetypes(),
    }


def validate_graphics() -> None:
    """The section is the solver's, and the two renders are on disk."""
    facts = seam_section_geometry()
    # The seam has to actually open: if the two faces closed flush there
    # would be no key, and the whole method would be a different one.
    assert facts["gap_deg"] > 1.0, facts["gap_deg"]
    assert facts["key_base_in"] > 0.5, facts["key_base_in"]
    # The cut has to have found something. Two members and one key is three
    # closed loops; fewer means the plane missed, which is silent otherwise.
    assert len(facts["members"]) >= 2, (
        f"the cutting plane found {len(facts['members'])} member sections; "
        "it should cross two")
    assert len(facts["key"]) >= 1, "the cutting plane missed the key"
    # The key sits outside the two members' points, which is why it can be
    # reached from outside and why the picture puts the weather at the top.
    key_top = max(p[1] for loop in facts["key"] for p in loop)
    assert key_top >= facts["apex"][1] - 1.0, (key_top, facts["apex"])
    # A and B are on opposite sides of the seam.
    assert facts["point_a"][0] * facts["point_b"][0] < 0.0, facts

    for key in ("seam-section", "mast-and-floor", "floating-dome", "breathing-cap",
                "grammar-families", "grammar-composite", "grammar-dyad",
                "grammar-archetypes"):
        path = FIGURE_DIR / f"{key}.png"
        assert path.is_file(), f"{key} has not been drawn yet"
        assert path.stat().st_size > 8_000, f"{key} is suspiciously small"

    # The grammar figures must agree with the grammar module's own numbers.
    from two_v_demo import wedge_grammar as g
    fam = {r.splits: r for r in g.equal_area_families()}
    assert fam[32].i_strong_in4 > fam[8].i_strong_in4 > fam[32].i_weak_in4


def main(argv: list[str] | None = None) -> int:
    made = render_all()
    for key, path in made.items():
        print(f"  {key:16s} {path}")
    validate_graphics()
    print("graphics ok")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
