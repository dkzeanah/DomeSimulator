"""Rendering every illustration in *2 Trees*, from the geometry that made it.

The rule this module exists to enforce is the one in ``CLAUDE.md``: a picture
of the wedge dome shows *the simulator's dome*, not a sketch of one.  So the
three-dimensional figures here do not draw a dome -- they ask
``geodesic_raw_wedge_dome_dihedral.py`` for its own solved meshes through
:mod:`raw_wedge_bridge` and put those on the page.  Change the geometry and
the next render of the book shows the change.

Why matplotlib and not the film renderer
----------------------------------------
The masterclass renderer needs an OpenGL context, which means a machine with
PyOpenGL and a GPU driver that will hand out one.  A book has to be
re-illustratable on whatever machine the manuscript is open on, so everything
except :func:`lesson_still` draws through matplotlib, which needs neither.
:func:`lesson_still` is still here because a frame of an existing film is
sometimes exactly the right picture; it degrades to a clear instruction rather
than a stack trace when the context is unavailable.

Renderers
---------
``raw_wedge_world``  the solved dome, in a named view
``raw_wedge_jig``    the fabrication jig at one of its twelve stages
``panel_jig_svg``    a flat, full-size panel drawing, straight from the sim
``lesson_still``     one frame of an existing film (needs OpenGL)
``book_plot``        a table or chart, dispatched by name to book_plots
``book_diagram``     an explanatory line drawing, dispatched to book_diagrams
``photo_slot``       a placeholder card describing the photograph to take

Output
------
Everything lands in ``deliverables/book/figures/`` as a PNG at print
resolution, plus an SVG where the source is vector.  Nothing is ever
overwritten: a re-render of a figure that already exists writes ``-v2``, in
line with this repository's append-only rule for deliverables.
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from .book import BOOK, EXPORT_DIR, Figure, figure_index


FIGURE_DIR = EXPORT_DIR / "figures"

# Print figures at 300 dpi. A full-page plate at this trim is about 5.5 by
# 8 inches inside the margins; a half-page figure is the same width and
# roughly half the height.
DPI = 300
PAGE_W_IN = 5.5
PAGE_H_IN = 8.0
HALF_H_IN = 4.0


# ----------------------------------------------------------------------
# The book's own look
# ----------------------------------------------------------------------

@dataclass(frozen=True)
class Style:
    """One consistent visual language for every figure in the book.

    Printed books are usually one colour plus black. These are chosen to
    survive being printed in greyscale: the accents differ in lightness as
    well as hue, so a bar chart does not collapse into one grey when the
    printer is cheap.
    """

    ink = "#1a1a1a"
    paper = "#ffffff"
    rule = "#b8b0a4"
    faint = "#e8e3da"
    wood = "#a9763f"
    wood_dark = "#6d4522"
    bark = "#4a3a2a"
    key = "#c8a02a"
    accent = "#2f5d7c"
    warn = "#a33a2a"
    good = "#3c6e47"
    muted = "#7a7268"

    serif = ("Georgia", "Times New Roman", "DejaVu Serif", "serif")
    sans = ("Segoe UI", "Helvetica", "DejaVu Sans", "sans-serif")
    mono = ("Consolas", "DejaVu Sans Mono", "monospace")


STYLE = Style()


def apply_style() -> None:
    """Set matplotlib up to draw like this book, once per process."""
    import matplotlib
    matplotlib.use("Agg")
    from matplotlib import rcParams

    rcParams["figure.dpi"] = DPI
    rcParams["savefig.dpi"] = DPI
    rcParams["figure.facecolor"] = STYLE.paper
    rcParams["savefig.facecolor"] = STYLE.paper
    rcParams["axes.facecolor"] = STYLE.paper
    rcParams["text.color"] = STYLE.ink
    rcParams["axes.labelcolor"] = STYLE.ink
    rcParams["axes.edgecolor"] = STYLE.rule
    rcParams["xtick.color"] = STYLE.ink
    rcParams["ytick.color"] = STYLE.ink
    rcParams["font.family"] = "sans-serif"
    rcParams["font.sans-serif"] = list(STYLE.sans)
    rcParams["font.size"] = 8.5
    rcParams["axes.titlesize"] = 10.5
    rcParams["axes.titleweight"] = "bold"
    rcParams["axes.labelsize"] = 8.5
    rcParams["legend.frameon"] = False
    rcParams["axes.spines.top"] = False
    rcParams["axes.spines.right"] = False
    rcParams["axes.grid"] = False
    rcParams["savefig.bbox"] = "tight"
    rcParams["savefig.pad_inches"] = 0.12


def new_figure(width: float = PAGE_W_IN, height: float = HALF_H_IN):
    """A blank figure at book proportions."""
    apply_style()
    import matplotlib.pyplot as plt
    return plt.figure(figsize=(width, height))


def next_version(path: Path) -> Path:
    """Never overwrite: a figure that exists gets ``-v2``, ``-v3``, ...

    The same rule ``two_v_demo.deliverables.next_version_path`` applies to
    video, applied to illustrations. A figure may already be laid into a
    proof, so replacing the file underneath it is not a fix, it is a
    surprise.
    """
    from .deliverables import next_version_path
    return next_version_path(path)


def save(fig, key: str, directory: Path | None = None,
         overwrite_ok: bool = False) -> Path:
    """Write one figure out, without ever clobbering an existing one."""
    directory = directory or FIGURE_DIR
    directory.mkdir(parents=True, exist_ok=True)
    path = directory / f"{key}.png"
    if path.exists() and not overwrite_ok:
        path = next_version(path)
    fig.savefig(path)
    import matplotlib.pyplot as plt
    plt.close(fig)
    return path


# ----------------------------------------------------------------------
# The solved dome, drawn from the simulator's own meshes
# ----------------------------------------------------------------------

VIEWS: dict[str, tuple[float, float, float]] = {
    # name: (elevation, azimuth, zoom) -- zoom < 1 crops in
    "hero": (14.0, -58.0, 0.92),
    "three_quarter": (22.0, -40.0, 0.95),
    "elevation": (2.0, 0.0, 0.98),
    "plan": (62.0, -90.0, 0.98),
    "exploded": (18.0, -52.0, 1.05),
    "seam": (10.0, -72.0, 0.45),
}


def _mesh_triangles(mesh, scale: float = 1.0):
    """(triangles, face colours) from one of the simulator's MeshData batches.

    The simulator packs position, normal and RGBA into ten floats per vertex
    and indexes them; matplotlib wants explicit triangles with one colour
    each, so the face colour is taken from the triangle's first vertex.
    """
    import numpy as np

    vertices = np.asarray(mesh.vertices, dtype=np.float64)
    indices = np.asarray(mesh.indices, dtype=np.int64)
    if len(indices) == 0:
        return np.zeros((0, 3, 3)), np.zeros((0, 4))
    tris = indices.reshape(-1, 3)
    positions = vertices[:, 0:3] * scale
    colours = vertices[:, 6:10]
    return positions[tris], colours[tris[:, 0]]


def _recolour(colours, palette: str):
    """Re-map the simulator's face colours for print.

    The simulator paints a wedge's two sawn faces red and green and its tip
    yellow, because that is how you read the orientation of a stick while
    flying around it. On paper, in a book about a timber building, forty
    panels of that reads as a painted climbing frame rather than as wood.

    ``timber`` keeps every triangle exactly where the solver put it and only
    changes the colour: the two sawn faces become two close shades of pale
    sawn pine, the tip a third, the bark face a darker brown. The face coding
    survives as tonal difference, so a reader can still see which face is
    which -- and the seam keys stay gold, because they are a different piece
    of wood doing a different job.

    ``simulator`` leaves the colours alone. The orientation chapter wants the
    loud version, because there the colour *is* the lesson.
    """
    import numpy as np

    if palette == "simulator":
        return colours

    # (source colour, replacement) pairs, matched by nearest RGB. Taken from
    # the simulator's own constants rather than guessed at.
    mapping = (
        ((0.92, 0.18, 0.14), (0.80, 0.66, 0.47)),   # left sawn face
        ((0.18, 0.82, 0.22), (0.72, 0.58, 0.40)),   # right sawn face
        ((1.00, 0.92, 0.10), (0.86, 0.74, 0.55)),   # tip
        ((0.60, 0.38, 0.18), (0.42, 0.29, 0.18)),   # bark face
        ((0.88, 0.79, 0.60), (0.84, 0.72, 0.53)),   # shaved face
        ((0.85, 0.68, 0.18), (0.85, 0.68, 0.18)),   # seam key: left gold
    )
    sources = np.asarray([pair[0] for pair in mapping])
    targets = np.asarray([pair[1] for pair in mapping])
    rgb = colours[:, 0:3]
    distances = ((rgb[:, None, :] - sources[None, :, :]) ** 2).sum(axis=2)
    nearest = distances.argmin(axis=1)
    out = colours.copy()
    out[:, 0:3] = targets[nearest]
    return out


def _shade(triangles, colours, light=(0.45, 0.35, 0.82)):
    """Lambert-shade the faces so a 3-D form reads as a form on paper.

    Matplotlib's 3-D axes do no lighting of their own, so an unshaded dome
    prints as a flat blob of one colour. This is the cheapest shading that
    makes the curvature legible in greyscale.
    """
    import numpy as np

    light = np.asarray(light, dtype=np.float64)
    light = light / np.linalg.norm(light)
    edge_a = triangles[:, 1] - triangles[:, 0]
    edge_b = triangles[:, 2] - triangles[:, 0]
    normals = np.cross(edge_a, edge_b)
    lengths = np.linalg.norm(normals, axis=1, keepdims=True)
    normals = np.divide(normals, np.where(lengths == 0, 1.0, lengths))
    lambert = np.abs(normals @ light)
    shade = (0.42 + 0.58 * lambert)[:, None]
    out = colours.copy()
    out[:, 0:3] = np.clip(colours[:, 0:3] * shade, 0.0, 1.0)
    return out


def render_dome(figure: Figure, path_key: str | None = None) -> Path:
    """The solved dome, in one of the named views.

    ``spec`` accepts ``orientation``, ``view``, ``parts`` and ``explode_in``.
    Nothing here models a dome: every triangle comes out of
    ``build_world_meshes`` on a model the simulator solved.
    """
    import numpy as np
    from mpl_toolkits.mplot3d.art3d import Poly3DCollection

    from . import raw_wedge_bridge as bridge

    spec = figure.spec
    orientation = spec.get("orientation", "point_dome_in")
    view = spec.get("view", "hero")
    parts = tuple(spec.get("parts", ("wood",)))
    palette = spec.get("palette", "timber")
    explode_in = float(spec.get("explode_in", 0.0))
    elevation, azimuth, zoom = VIEWS.get(view, VIEWS["hero"])

    sim = bridge.simulator()
    # Exploding pushes each panel out along its own normal so the seams open.
    # It is a property of the solved model, not of the drawing, so it is asked
    # for here rather than faked by moving triangles about afterwards.
    if explode_in:
        config = sim.DomeConfig(wedge_orientation=orientation,
                               panel_explode_in=explode_in)
        model = sim.build_physical_model(config)
    else:
        model = bridge.model(orientation)
    meshes = sim.build_world_meshes(model)

    height = PAGE_H_IN if figure.full_page else HALF_H_IN
    fig = new_figure(PAGE_W_IN, height)
    axes = fig.add_subplot(111, projection="3d")
    axes.set_axis_off()
    axes.set_facecolor(STYLE.paper)

    radius = model.topology.sphere_radius_in
    drawn = 0
    for name in parts:
        mesh = meshes.get(name)
        if mesh is None or not hasattr(mesh, "indices"):
            continue
        triangles, colours = _mesh_triangles(mesh)
        if len(triangles) == 0:
            continue
        collection = Poly3DCollection(
            triangles,
            facecolors=_shade(triangles, _recolour(colours, palette)),
            edgecolors="none", linewidths=0.0)
        axes.add_collection3d(collection)
        drawn += len(triangles)

    if drawn == 0:
        raise RuntimeError(
            f"figure {figure.key!r} drew no triangles; parts={parts} are not "
            f"in this model's meshes ({sorted(meshes)})")

    limit = radius * zoom
    axes.set_xlim(-limit, limit)
    axes.set_ylim(-limit, limit)
    axes.set_zlim(0.0, limit * 1.15)
    axes.set_box_aspect((1.0, 1.0, 0.62))
    axes.view_init(elev=elevation, azim=azimuth)
    fig.subplots_adjust(left=0, right=1, top=1, bottom=0)
    return save(fig, path_key or figure.key)


def render_jig(figure: Figure, path_key: str | None = None) -> Path:
    """The fabrication jig, at one of its twelve stages.

    Built by the simulator's own ``build_fabrication_jig`` so the drawing and
    the fabrication package cannot disagree about what the fixture is.
    """
    import numpy as np
    from mpl_toolkits.mplot3d.art3d import Poly3DCollection, Line3DCollection

    from . import raw_wedge_bridge as bridge

    spec = figure.spec
    stage = int(spec.get("stage", 11))
    panel_index = int(spec.get("panel_index", 0))
    orientation = spec.get("orientation", "point_dome_in")
    view = spec.get("view", "three_quarter")
    elevation, azimuth, _zoom = VIEWS.get(view, VIEWS["three_quarter"])

    sim = bridge.simulator()
    model = bridge.model(orientation)
    # (model, panel_index, stage) -- the jig is built for one panel at one
    # step of its twelve, not for a whole dome.
    jig = sim.build_fabrication_jig(model, panel_index, stage)

    height = PAGE_H_IN if figure.full_page else HALF_H_IN
    fig = new_figure(PAGE_W_IN, height)
    axes = fig.add_subplot(111, projection="3d")
    axes.set_axis_off()

    points: list = []
    drawn = 0
    for name, data in sorted(jig.items()):
        vertices = np.asarray(getattr(data, "vertices", []), dtype=np.float64)
        if len(vertices) == 0:
            continue
        indices = getattr(data, "indices", None)
        if indices is not None and len(indices):
            triangles, colours = _mesh_triangles(data)
            if len(triangles) == 0:
                continue
            # The jig keeps the simulator's colours: red and green plates
            # are how a wrongly-rotated sector is made to refuse to seat,
            # and a book that greyed them out would lose the point.
            axes.add_collection3d(Poly3DCollection(
                triangles, facecolors=_shade(triangles, colours),
                edgecolors="none"))
            points.append(triangles.reshape(-1, 3))
            drawn += len(triangles)
        else:
            segments = vertices[:, 0:3].reshape(-1, 2, 3)
            axes.add_collection3d(Line3DCollection(
                segments, colors=STYLE.ink, linewidths=0.5))
            points.append(vertices[:, 0:3])

    if drawn == 0 and not points:
        raise RuntimeError(
            f"figure {figure.key!r}: the jig produced nothing at stage "
            f"{stage}. Stages run 0..11.")

    # A jig is a bench: wide, deep and almost flat. Fitting it into a cube
    # wastes most of the page on empty air above it, so the vertical extent
    # is measured separately and the box squashed to match.
    cloud = np.concatenate(points, axis=0)
    low, high = cloud.min(axis=0), cloud.max(axis=0)
    centre = (low + high) * 0.5
    span = float(max(high[0] - low[0], high[1] - low[1])) * 0.52
    rise = max(float(high[2] - low[2]) * 0.62, span * 0.18)
    axes.set_xlim(centre[0] - span, centre[0] + span)
    axes.set_ylim(centre[1] - span, centre[1] + span)
    axes.set_zlim(centre[2] - rise, centre[2] + rise)
    axes.set_box_aspect((1.0, 1.0, max(0.25, rise / span)))
    axes.view_init(elev=elevation, azim=azimuth)
    fig.subplots_adjust(left=0, right=1, top=1, bottom=0)
    return save(fig, path_key or figure.key)


def render_panel_svg(figure: Figure, path_key: str | None = None) -> Path:
    """A flat, full-size panel drawing, exported by the simulator itself.

    This one stays vector: a panel drawing is something the reader prints at
    full size and lays a stick on, so rasterising it would be actively
    harmful. Returns the SVG path.
    """
    from . import raw_wedge_bridge as bridge

    sim = bridge.simulator()
    model = bridge.model(figure.spec.get("orientation", "point_dome_in"))
    index = int(figure.spec.get("panel_index", 0))
    FIGURE_DIR.mkdir(parents=True, exist_ok=True)
    path = FIGURE_DIR / f"{path_key or figure.key}.svg"
    if path.exists():
        path = next_version(path)
    sim.export_panel_jig_svg(model, index, path)
    return path


def _archived_still(lesson_key: str, prefix: str, second: float) -> Path | None:
    """An already-rendered frame of one film, from the stills archive.

    The launcher's shots action leaves frames named
    ``<prefix>_<time>s.png`` under ``two_v_demo_output/<lesson>/``. A book
    figure that names the same lesson and second can take that exact frame
    -- it is the film's own render, not a re-drawing -- which is what lets
    a machine without PyOpenGL still put real film stills in the book.
    """
    root = Path(__file__).resolve().parent.parent / "two_v_demo_output"
    name = f"{prefix}_{second:07.2f}s.png"
    direct = root / lesson_key / name
    if direct.is_file():
        return direct
    for candidate in root.glob(f"*/{name}"):
        return candidate
    return None


def render_lesson_still(figure: Figure, path_key: str | None = None) -> Path:
    """One frame of an existing film.

    Needs an OpenGL context. When there is not one, an already-rendered
    frame of the same lesson and second is copied out of the stills
    archive instead -- the film's own render, so the book's plate and the
    film cannot disagree. When neither exists, this raises with the
    launcher action that will produce the frame on a machine that has
    OpenGL, rather than failing obscurely inside a GL call.
    """
    spec = figure.spec
    lesson = spec.get("lesson", "why")
    second = float(spec.get("second", 0.0))
    try:
        import OpenGL  # noqa: F401
    except ImportError:
        from .lesson_registry import get_lesson

        prefix = get_lesson(lesson).snapshot_prefix
        archived = _archived_still(lesson, prefix, second)
        if archived is not None:
            target = FIGURE_DIR / f"{path_key or figure.key}.png"
            if target.exists():
                target = next_version(target)
            target.write_bytes(archived.read_bytes())
            return target
        raise RuntimeError(
            f"figure {figure.key!r} is a frame of the {lesson!r} film at "
            f"{second:.1f}s, and rendering it needs PyOpenGL, which is not "
            "installed here -- and the stills archive has no frame at that "
            "second. Render it from the launcher's Masterclass tab: "
            f"Lesson = {lesson}, Action = shots, Shot times = {second:g}. "
            "The frame lands in two_v_demo_output/ and can be copied into "
            f"{FIGURE_DIR}/{figure.key}.png."
        ) from None

    from .app import MasterclassApp
    from .lesson_registry import get_lesson

    app = MasterclassApp(size=(1920, 1080), hidden=True,
                         lesson=get_lesson(lesson))
    try:
        paths = app.render_shots([second], FIGURE_DIR / "stills")
    finally:
        app.pygame.quit()
    source = paths[0]
    target = FIGURE_DIR / f"{path_key or figure.key}.png"
    if target.exists():
        target = next_version(target)
    target.write_bytes(source.read_bytes())
    return target


def render_photo_slot(figure: Figure, path_key: str | None = None) -> Path:
    """A placeholder card for a photograph the author still has to take.

    Not decoration: it is a shot list that lays out at the right size, so a
    proof can be read end to end with the photographs missing and the gaps
    are self-describing.
    """
    height = PAGE_H_IN if figure.full_page else HALF_H_IN
    fig = new_figure(PAGE_W_IN, height)
    axes = fig.add_axes([0, 0, 1, 1])
    axes.set_axis_off()
    axes.add_patch(_dashed_box())
    axes.text(0.5, 0.60, "PHOTOGRAPH", ha="center", va="center",
              fontsize=13, weight="bold", color=STYLE.muted,
              family="sans-serif")
    caption = figure.caption or "(no caption yet)"
    axes.text(0.5, 0.50, _wrap(caption, 44), ha="center", va="top",
              fontsize=9, color=STYLE.ink)
    if figure.note:
        axes.text(0.5, 0.30, _wrap(figure.note, 52), ha="center", va="top",
                  fontsize=7.5, color=STYLE.muted, style="italic")
    axes.text(0.5, 0.06, figure.key, ha="center", va="bottom",
              fontsize=7, color=STYLE.rule, family="monospace")
    axes.set_xlim(0, 1)
    axes.set_ylim(0, 1)
    return save(fig, path_key or figure.key)


def _dashed_box():
    from matplotlib.patches import Rectangle
    return Rectangle((0.04, 0.04), 0.92, 0.92, fill=False,
                     edgecolor=STYLE.rule, linewidth=1.0,
                     linestyle=(0, (6, 4)))


def _wrap(text: str, width: int) -> str:
    import textwrap
    return "\n".join(textwrap.wrap(text, width))


def render_plot(figure: Figure, path_key: str | None = None) -> Path:
    from . import book_plots
    return book_plots.render(figure, path_key)


def render_diagram(figure: Figure, path_key: str | None = None) -> Path:
    from . import book_diagrams
    return book_diagrams.render(figure, path_key)


RENDERERS = {
    "raw_wedge_world": render_dome,
    "raw_wedge_jig": render_jig,
    "panel_jig_svg": render_panel_svg,
    "lesson_still": render_lesson_still,
    "book_plot": render_plot,
    "book_diagram": render_diagram,
    "photo_slot": render_photo_slot,
}


# ----------------------------------------------------------------------
# Rendering the book's figures
# ----------------------------------------------------------------------

def render_figure(key: str) -> Path:
    """Render one figure by key."""
    index = figure_index(BOOK)
    try:
        figure = index[key]
    except KeyError:
        raise ValueError(
            f"no figure {key!r} in the outline. The book has "
            f"{len(index)}: {', '.join(sorted(index))}") from None
    renderer = RENDERERS[figure.source]
    return renderer(figure)


def render_all(keys: tuple[str, ...] = (), skip_slow: bool = False,
               on_line=None) -> dict[str, Path | str]:
    """Render every figure in the book, or the ones named.

    Never stops on one failure: an illustration that cannot be drawn on this
    machine (a film frame with no OpenGL, a photograph nobody has taken)
    records why and the rest of the book still re-illustrates.
    """
    index = figure_index(BOOK)
    wanted = keys or tuple(index)
    slow = {"raw_wedge_world", "raw_wedge_jig", "lesson_still"}
    results: dict[str, Path | str] = {}
    for position, key in enumerate(wanted, start=1):
        figure = index[key]
        if skip_slow and figure.source in slow:
            results[key] = "skipped (slow)"
            continue
        label = f"[{position}/{len(wanted)}] {key} ({figure.source})"
        if on_line:
            on_line(label)
        try:
            results[key] = RENDERERS[figure.source](figure)
            if on_line:
                on_line(f"    saved {results[key]}")
        except Exception as exc:  # noqa: BLE001 - a book renders partially
            results[key] = f"FAILED: {exc}"
            if on_line:
                on_line(f"    FAILED: {exc}")
    return results


def figure_report() -> str:
    """Every figure in the book, what draws it, and whether it exists yet."""
    index = figure_index(BOOK)
    by_source: dict[str, list[str]] = {}
    for key, figure in index.items():
        by_source.setdefault(figure.source, []).append(key)
    lines = [f"{len(index)} figures in {BOOK.title}", ""]
    for source in sorted(by_source):
        keys = sorted(by_source[source])
        lines.append(f"{source}  ({len(keys)})")
        for key in keys:
            existing = FIGURE_DIR / f"{key}.png"
            svg = FIGURE_DIR / f"{key}.svg"
            mark = "rendered" if (existing.exists() or svg.exists()) else "-"
            lines.append(f"    {key:<24} {mark}")
        lines.append("")
    return "\n".join(lines)


def validate_figures() -> None:
    """Every figure the outline asks for has a renderer that can be called."""
    index = figure_index(BOOK)
    assert index, "the book has no figures"

    for key, figure in index.items():
        assert figure.source in RENDERERS, (key, figure.source)
        assert callable(RENDERERS[figure.source]), figure.source

    # The plot and diagram dispatchers have to know every name the outline
    # asks them for, or a render fails hours in on a figure nobody checked.
    from . import book_diagrams, book_plots
    missing: list[str] = []
    for key, figure in index.items():
        if figure.source == "book_plot":
            name = figure.spec.get("plot")
            if name not in book_plots.PLOTS:
                missing.append(f"plot {name!r} (figure {key})")
        elif figure.source == "book_diagram":
            name = figure.spec.get("diagram")
            if name not in book_diagrams.DIAGRAMS:
                missing.append(f"diagram {name!r} (figure {key})")
    assert not missing, "unimplemented figures: " + "; ".join(missing)

    # Every renderer implemented is one the book actually uses. An orphan
    # renderer is code nobody will ever look at again.
    used = {figure.source for figure in index.values()}
    orphans = set(RENDERERS) - used
    assert not orphans, f"renderers nothing uses: {sorted(orphans)}"

    for name in book_plots.PLOTS:
        assert callable(book_plots.PLOTS[name]), name
    for name in book_diagrams.DIAGRAMS:
        assert callable(book_diagrams.DIAGRAMS[name]), name

    print(f"book_figures OK: {len(index)} figures, "
          f"{len(RENDERERS)} renderers, {len(book_plots.PLOTS)} plots, "
          f"{len(book_diagrams.DIAGRAMS)} diagrams")


if __name__ == "__main__":
    print(figure_report())
    validate_figures()
