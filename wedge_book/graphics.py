"""The three pictures this book draws for itself.

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


def seam_section_geometry(seam_id: str = "SEAM_A_016") -> dict:
    """The true cross-section of one seam, cut out of the solved meshes.

    The plane is perpendicular to the seam's own tangent at its midpoint, so
    what comes out is what a saw would see if it cut the building across the
    joint. The members and the key are the solver's triangles, intersected --
    not a reconstruction from the angles.
    """
    import numpy as np

    from . import numbers

    rw = numbers.solver()
    model = numbers.reference_model()
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


def render_all() -> dict[str, Path]:
    return {
        "seam-section": seam_section(),
        "mast-and-floor": mast_and_floor(),
        "floating-dome": floating_dome(),
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

    for key in ("seam-section", "mast-and-floor", "floating-dome"):
        path = FIGURE_DIR / f"{key}.png"
        assert path.is_file(), f"{key} has not been drawn yet"
        assert path.stat().st_size > 8_000, f"{key} is suspiciously small"


def main(argv: list[str] | None = None) -> int:
    made = render_all()
    for key, path in made.items():
        print(f"  {key:16s} {path}")
    validate_graphics()
    print("graphics ok")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
