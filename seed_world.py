"""The seed dome as a thing you can walk around: frame, column, cap, polyps.

:mod:`seed_model` says what the seed dome *is* and what it costs. This says
what it looks like, in the Dome Creator's own :class:`mesh_builder.MeshBuilder`
so the park renders it through the same shader as everything else standing on
the same ground.

The frame is not drawn here. It is fetched from
:mod:`geodesic_raw_wedge_dome_dihedral` -- the live raw-wedge solver, through
:mod:`two_v_demo.raw_wedge_bridge` -- and converted into builder vertices, so
the dome on a pad is the dome the fabrication package cuts, with its real
compound butt cuts, its real seam keys and its real vertex trims. A sketch of
a wedge dome would be a different building.

What this module adds around that frame is the service architecture, and it
is one idea drawn four ways:

**The pad port.** Power, water and drain arrive in the middle of the pad,
come up through the floor, and stop at a flange. Nothing crosses a doorway.

**The utility column.** It stands on that flange, carries the fixtures at
working height on its inside faces, and then keeps going -- up past the
ceiling, through a sleeve at the apex, and out. That is the whole trick: the
top of the dome is not a roof, it is an interface, and the services are
already on the other side of it before anybody decides what to plug in.

**The seal cap.** A gasketed cap over the apex penetration, bolted down. It
is meant to stay shut for years and come off in ten minutes, which is a
different object from a hatch you open every day.

**The polyps.** Utility panels hanging off the rim, mostly outside the
footprint, reaching back through the shell to the inside. Their services come
from under the seal cap and down the outside of the shell, so adding one never
cuts a new hole in a weathertight surface.
"""

from __future__ import annotations

import math
from dataclasses import dataclass

import numpy as np

import seed_model
from materials import (
    MAT_CANVAS,
    MAT_MIRROR,
    MAT_SOLAR,
    MAT_CONCRETE,
    MAT_EMISSIVE,
    MAT_GLASS,
    MAT_METAL,
    MAT_PLAIN,
    MAT_SHINGLE,
    MAT_WOOD,
)
from mesh_builder import Mesh, MeshBuilder

M_PER_IN = 0.0254
FT_PER_M = 3.280839895


def m(inches: float) -> float:
    """Inches to metres. The solver speaks inches; the park speaks metres."""
    return inches * M_PER_IN


# ----------------------------------------------------------------------
# Palette
# ----------------------------------------------------------------------

STEEL = (0.60, 0.63, 0.67)
DARK_STEEL = (0.24, 0.26, 0.29)
BRASS = (0.72, 0.60, 0.30)
PIPE_BLUE = (0.22, 0.38, 0.78)
PIPE_RED = (0.72, 0.24, 0.24)
CONDUIT = (0.26, 0.27, 0.30)
DRAIN = (0.42, 0.43, 0.46)
GASKET = (0.13, 0.14, 0.16)
SHELL_WHITE = (0.86, 0.87, 0.85)
PANEL_POLY = (0.72, 0.78, 0.80)
CAST_IRON = (0.17, 0.17, 0.18)
EMBER = (1.00, 0.46, 0.12)
LIT_AD = (1.00, 0.95, 0.72)
AD_TINTS: tuple[tuple[float, float, float], ...] = (
    (1.00, 0.95, 0.72), (0.98, 0.86, 0.62), (0.84, 0.94, 1.00),
    (1.00, 0.88, 0.86), (0.88, 1.00, 0.88), (1.00, 0.97, 0.90),
    (0.92, 0.90, 1.00),
)
"""Seven lightbox tints, dealt round the shell.

Drawn as one colour, forty lit panels render as a single white blob and the
whole product disappears: the thing being sold is forty separately rented
faces, and a picture that cannot be counted is not showing it. Each face also
gets a dark margin around it, because that is what a lightbox actually looks
like from the road."""

AD_INSET = 0.055
"""How far a lit face is pulled in from its own edges, leaving the mullion."""
ASPHALT = (0.19, 0.19, 0.21)
STRIPE = (0.92, 0.88, 0.40)


# ----------------------------------------------------------------------
# The shapes a seed can take
# ----------------------------------------------------------------------

SHAPES: dict[str, tuple[float, float, float]] = {
    # name -> (horizontal scale, vertical scale, z mirror)
    "hemisphere": (1.0, 1.0, 1.0),
    "tall": (0.72, 1.55, 1.0),
    "inverted": (1.0, 1.0, -1.0),
    "buried": (1.0, 1.0, 1.0),
    "treed": (1.0, 1.0, 1.0),
}
"""How each seed distorts the one frame it is built from.

A sauna is the same forty panels pulled in and stretched up; a jacuzzi is the
same forty panels turned over. Neither is a second cut list, which is the
reason the product line is one product."""


SEAMS = ("hose", "rigid", "none")
"""What sits between two panels.

``hose`` is a compressible tube, sized to the largest circle that fits the
gap, and it is the seed dome's default: a building meant to come apart and go
back together wants a gasket that recovers, not a timber key that has to be
made to fit one particular seam and then found again. ``rigid`` is that timber
key, which is what a dome that is only ever built once wants. ``none`` leaves
the raw gap showing, which is how you look at the angle it has to close."""


@dataclass(frozen=True)
class SeedPlacement:
    """One seed dome standing somewhere, in metres."""

    fitout: str = "stem_cell"
    origin: tuple[float, float] = (0.0, 0.0)
    base_z: float = 0.0
    heading_deg: float = 0.0
    polyps: int | None = None
    show_shell: bool = False
    shell_open: bool = False
    """Draw the shell lifted clear of the frame, as a crane would hold it."""
    seam: str = "hose"
    """``hose``, ``rigid`` or ``none`` -- see :data:`SEAMS`."""

    @property
    def spec(self):
        return seed_model.fitout(self.fitout)

    @property
    def shape(self) -> str:
        return self.spec.shape

    @property
    def polyp_count(self) -> int:
        return self.spec.polyps if self.polyps is None else int(self.polyps)


def geometry():
    return seed_model.seed_geometry()


def radius_m() -> float:
    return m(geometry().radius_in)


def apex_m(shape: str = "hemisphere") -> float:
    """How high the apex stands above the floor, for this shape."""
    _h, v, mirror = SHAPES.get(shape, SHAPES["hemisphere"])
    return m(geometry().height_in) * v * (1.0 if mirror > 0 else 0.0)


SHAPE_LIFT_M: dict[str, float] = {"treed": 3.6}
"""How far off its pad a shape stands.

Only one does. A treehouse seed is the same dome on the same port, carried on
a saddle instead of on blocks, and the lift is what makes the picture of that
different from the picture of every other seed."""


def base_lift_m(shape: str = "hemisphere") -> float:
    return SHAPE_LIFT_M.get(shape, 0.0)


def footprint_radius_m(shape: str = "hemisphere") -> float:
    h, _v, _mirror = SHAPES.get(shape, SHAPES["hemisphere"])
    return radius_m() * h


def pad_diameter_ft(shape: str = "hemisphere") -> float:
    """The pad a seed of this shape needs, in feet."""
    return footprint_radius_m(shape) * 2.0 * FT_PER_M


# ----------------------------------------------------------------------
# The frame, taken from the solver rather than drawn
# ----------------------------------------------------------------------

_FRAME_CACHE: dict[tuple, tuple[np.ndarray, np.ndarray]] = {}

ANALYSIS_COLOURS: tuple[tuple[tuple[float, float, float],
                             tuple[float, float, float]], ...] = (
    # (what the solver paints it, what the park paints it)
    ((0.18, 0.82, 0.22), (0.88, 0.80, 0.52)),
    ((0.92, 0.18, 0.14), (0.78, 0.62, 0.40)),
)
"""The solver's two marker colours, and the timber they become out here.

Every wedge member has two radial sawn faces, and the solver paints one green
and one red so that which face receives the next stick's butt can be read at a
glance. That is the right colour in a fabrication tool and the wrong colour on
a house: a dome on a pad came out wearing its own assembly diagram, a hundred
and twenty green stripes visible from across the site.

So the park repaints those two faces as sawn timber, distinct enough from each
other that the pinwheel is still legible up close. Pass ``analysis=True`` to
get the solver's own colours back -- when the question is how it goes together
rather than what it looks like, the stripes are the point."""

BLUE_FLOOR = 0.42
"""How much blue a frame colour has to keep to survive daylight.

The solver draws a freshly sawn wedge face bright yellow -- (1.0, 0.92, 0.10)
-- against its own near-black background, where that is exactly the colour of
new pine. The park lights the same triangles under a blue sky, and the shader's
ambient term is albedo times sky: a colour with no blue in it comes back green.
Every sawn face in the dome turned lime, which looked like a bug in the solver
and was really a bug in the lighting.

So colours arriving from the solver get a floor under their blue channel, set
as a fraction of their red and green. Nothing else is touched -- brown bark is
already past the floor and does not move -- and the solver's own file is left
alone, because it is right about what a sawn face looks like in its own
window."""


def _solved_frame(parts: tuple[str, ...], analysis: bool = False
                  ) -> tuple[np.ndarray, np.ndarray]:
    """The simulator's own meshes for these parts, in inches.

    Cached, because solving 120 members and 55 seams to draw one pad's worth
    of dome six times a frame would make the park unusable.
    """
    key = (tuple(parts), bool(analysis))
    hit = _FRAME_CACHE.get(key)
    if hit is not None:
        return hit

    from two_v_demo import raw_wedge_bridge

    sim = raw_wedge_bridge.simulator()
    model = raw_wedge_bridge.model(
        long_edge_in=seed_model.SEED_LONG_EDGE_IN,
        trunk_diameter_in=seed_model.SEED_TRUNK_DIAMETER_IN)
    world = sim.build_world_meshes(model)

    positions: list[np.ndarray] = []
    colours: list[np.ndarray] = []
    for name in parts:
        data = world.get(name)
        if data is None or not len(getattr(data, "indices", ())):
            continue
        verts = np.asarray(data.vertices, dtype=np.float64)
        index = np.asarray(data.indices, dtype=np.int64)
        # 3f position, 3f normal, 4f colour.
        positions.append(verts[index, 0:3])
        part_colours = verts[index, 6:10].copy()
        if not analysis:
            for source, target in ANALYSIS_COLOURS:
                hit = np.all(np.abs(part_colours[:, 0:3]
                                    - np.asarray(source)) < 0.02, axis=1)
                part_colours[hit, 0:3] = target
        floor = BLUE_FLOOR * part_colours[:, 0:2].mean(axis=1)
        part_colours[:, 2] = np.maximum(part_colours[:, 2], floor)
        colours.append(part_colours)
    if not positions:
        empty = np.zeros((0, 3)), np.zeros((0, 4))
        _FRAME_CACHE[key] = empty
        return empty
    result = (np.concatenate(positions), np.concatenate(colours))
    _FRAME_CACHE[key] = result
    return result


def seam_parts(seam: str) -> tuple[str, ...]:
    """Which of the solver's meshes draw this seam choice."""
    if seam == "none":
        return ("wood",)
    if seam not in SEAMS:
        raise ValueError(f"seam must be one of {SEAMS}, not {seam!r}")
    return ("wood", seam)


def build_seed_frame(b: MeshBuilder, placement: SeedPlacement,
                     parts: tuple[str, ...] | None = None,
                     mat_id: int = MAT_WOOD, analysis: bool = False) -> int:
    """Draw the solved wedge dome where this placement stands.

    Returns the triangle count, so a caller can tell the difference between a
    dome that is not there and a dome that failed to load.
    """
    if parts is None:
        parts = seam_parts(placement.seam)
    points_in, colours = _solved_frame(parts, analysis)
    if not len(points_in):
        return 0

    h, v, mirror = SHAPES.get(placement.shape, SHAPES["hemisphere"])
    scale = np.array([M_PER_IN * h, M_PER_IN * h, M_PER_IN * v * mirror])
    points = points_in * scale

    angle = math.radians(placement.heading_deg)
    cos, sin = math.cos(angle), math.sin(angle)
    x = points[:, 0] * cos - points[:, 1] * sin + placement.origin[0]
    y = points[:, 0] * sin + points[:, 1] * cos + placement.origin[1]
    z = points[:, 2] + placement.base_z + base_lift_m(placement.shape)
    if mirror < 0:
        # Turned over, the dome hangs below its own floor line. Lift it so
        # the rim -- now the top -- sits at the floor.
        z = z + m(geometry().height_in) * v

    points = np.stack([x, y, z], axis=1)
    count = len(points) // 3
    for tri in range(count):
        p0, p1, p2 = points[tri * 3:tri * 3 + 3]
        colour = colours[tri * 3]
        b.triangle(p0, p1, p2,
                   (float(colour[0]), float(colour[1]), float(colour[2])),
                   alpha=1.0, mat_id=mat_id)
    return count


# ----------------------------------------------------------------------
# Small helpers
# ----------------------------------------------------------------------

def box(b: MeshBuilder, centre, size, colour, mat=MAT_PLAIN,
        alpha: float = 1.0) -> None:
    """An axis-aligned box. Every face gets its own outward normal.

    A zero or shared normal here renders a face black, because the shader has
    nothing to take a dot product against."""
    cx, cy, cz = centre
    hx, hy, hz = (value / 2.0 for value in size)
    bottom = ((cx - hx, cy - hy, cz - hz), (cx + hx, cy - hy, cz - hz),
              (cx + hx, cy + hy, cz - hz), (cx - hx, cy + hy, cz - hz))
    top = ((cx - hx, cy - hy, cz + hz), (cx + hx, cy - hy, cz + hz),
           (cx + hx, cy + hy, cz + hz), (cx - hx, cy + hy, cz + hz))
    b.quad(*top, (0.0, 0.0, 1.0), colour, alpha, mat)
    b.quad(*tuple(reversed(bottom)), (0.0, 0.0, -1.0), colour, alpha, mat)
    normals = ((0.0, -1.0, 0.0), (1.0, 0.0, 0.0),
               (0.0, 1.0, 0.0), (-1.0, 0.0, 0.0))
    for index in range(4):
        nxt = (index + 1) % 4
        b.quad(bottom[index], bottom[nxt], top[nxt], top[index],
               normals[index], colour, alpha, mat)


def _ring(centre, radius: float, count: int, phase: float = 0.0):
    cx, cy, cz = centre
    for index in range(count):
        angle = phase + math.tau * index / count
        yield (cx + math.cos(angle) * radius, cy + math.sin(angle) * radius,
               cz), angle


# ----------------------------------------------------------------------
# The utility column, and what makes the apex an interface
# ----------------------------------------------------------------------

COLUMN_RADIUS_M = 0.30
RISER_RADIUS_M = 0.085
SLEEVE_RADIUS_M = 0.19
CAP_RADIUS_M = 0.34


def build_pad_port(b: MeshBuilder, origin, z: float) -> None:
    """Where the pad's services stop and the dome's begin.

    A flange, and three stubs of three different colours, because power,
    water and drain are three different things and a picture that draws them
    all grey is a picture that has stopped explaining anything.
    """
    ox, oy = origin
    b.cylinder((ox, oy, z), (ox, oy, z + 0.10), 0.46, 24, DARK_STEEL,
               mat_id=MAT_METAL)
    b.disc((ox, oy, z + 0.101), 0.46, 24, (0.30, 0.32, 0.35), mat_id=MAT_METAL)
    for offset, radius, colour in ((-0.20, 0.045, CONDUIT),
                                   (0.02, 0.038, PIPE_BLUE),
                                   (0.22, 0.062, DRAIN)):
        b.cylinder((ox + offset, oy, z + 0.10), (ox + offset, oy, z + 0.34),
                   radius, 10, colour, mat_id=MAT_PLAIN)


# ----------------------------------------------------------------------
# The core on the bench, stage by stage
# ----------------------------------------------------------------------

CORE_STAGES: tuple[str, ...] = ("chase", "drain", "water", "power", "close")
"""The five stages :mod:`column_build` sequences, in build order."""

FLANGE = (0.44, 0.46, 0.50)
CHASE = (0.55, 0.57, 0.60)
STACK_ABS = (0.18, 0.18, 0.20)
PEX_RED = (0.70, 0.24, 0.24)
PEX_BLUE = (0.24, 0.40, 0.70)
PANEL_GREY = (0.32, 0.34, 0.38)
CAP_GOLD = (0.78, 0.62, 0.26)


def build_core_stage(b: MeshBuilder, stage: str, origin=(0.0, 0.0),
                     base_z: float = 0.0, partial: float = 1.0) -> int:
    """The utility core, built up to and including ``stage``.

    Laid out the way :mod:`column_build` says to build it -- on a bench, with
    water on one face and power on the opposite one -- so a film following
    this is following the process sheet and not an artist's impression.
    """
    if stage not in CORE_STAGES:
        raise KeyError(f"unknown core stage {stage!r}")
    reached = CORE_STAGES.index(stage)
    ox, oy = origin
    height = 2.9
    half = 0.16
    drawn = 0

    def part(centre, size, colour, mat=MAT_METAL):
        nonlocal drawn
        box(b, centre, size, colour, mat)
        drawn += 6

    # 1. The chase: base flange, four sections, grommets.
    if reached >= 0:
        share = partial if reached == 0 else 1.0
        part((ox, oy, base_z + 0.04), (0.62, 0.62, 0.08), FLANGE, MAT_METAL)
        sections = 4
        built = max(1, int(round(sections * share)))
        for index in range(built):
            z = base_z + 0.10 + (index + 0.5) * (height / sections)
            part((ox, oy, z), (half * 2, half * 2, height / sections - 0.03),
                 CHASE, MAT_METAL)

    # 2. Drain: the 2 in stack down the back face, trap at its foot.
    if reached >= 1:
        share = partial if reached == 1 else 1.0
        run = height * share
        b.cylinder((ox, oy - half - 0.05, base_z + 0.18),
                   (ox, oy - half - 0.05, base_z + 0.18 + run), 0.052, 10,
                   STACK_ABS, mat_id=MAT_PLAIN)
        drawn += 10
        if share > 0.85:
            part((ox, oy - half - 0.05, base_z + 0.12), (0.16, 0.16, 0.12),
                 STACK_ABS, MAT_PLAIN)

    # 3. Water: valve low, manifold at chest, four capped tails. West face.
    if reached >= 2:
        share = partial if reached == 2 else 1.0
        if share > 0.15:
            part((ox - half - 0.06, oy, base_z + 0.55), (0.10, 0.14, 0.12),
                 PEX_BLUE, MAT_PLAIN)
        if share > 0.35:
            part((ox - half - 0.06, oy, base_z + 1.35), (0.09, 0.34, 0.14),
                 (0.72, 0.70, 0.66), MAT_METAL)
        tails = int(4 * min(1.0, max(0.0, (share - 0.45) / 0.55)))
        for index in range(tails):
            y = oy - 0.12 + index * 0.08
            b.cylinder((ox - half - 0.06, y, base_z + 1.35),
                       (ox - half - 0.22, y, base_z + 1.35), 0.016, 8,
                       PEX_RED if index % 2 else PEX_BLUE, mat_id=MAT_PLAIN)
            drawn += 8
        if share > 0.9:
            # The riser, once the run is proved.
            b.cylinder((ox - half - 0.06, oy, base_z + 0.20),
                       (ox - half - 0.06, oy, base_z + 1.30), 0.018, 8,
                       PEX_BLUE, mat_id=MAT_PLAIN)
            drawn += 8

    # 4. Power: inlet low, load centre at chest, branches out. East face.
    if reached >= 3:
        share = partial if reached == 3 else 1.0
        if share > 0.12:
            part((ox + half + 0.05, oy, base_z + 0.35), (0.09, 0.16, 0.16),
                 PANEL_GREY, MAT_METAL)
        if share > 0.30:
            part((ox + half + 0.06, oy, base_z + 1.45), (0.11, 0.30, 0.42),
                 PANEL_GREY, MAT_METAL)
        branches = int(4 * min(1.0, max(0.0, (share - 0.5) / 0.5)))
        for index in range(branches):
            y = oy - 0.10 + index * 0.07
            b.cylinder((ox + half + 0.06, y, base_z + 1.45),
                       (ox + half + 0.30, y, base_z + 1.62 + index * 0.05),
                       0.013, 6, (0.16, 0.16, 0.17), mat_id=MAT_PLAIN)
            drawn += 6

    # 5. Close: apex sleeve, seal cap, cover panel.
    if reached >= 4:
        share = partial if reached == 4 else 1.0
        top = base_z + 0.10 + height
        part((ox, oy, top + 0.10), (0.30, 0.30, 0.14), (0.62, 0.64, 0.66),
             MAT_METAL)
        if share > 0.35:
            part((ox, oy, top + 0.26), (0.36, 0.36, 0.09), CAP_GOLD,
                 MAT_METAL)
        if share > 0.7:
            # The cover panel goes on the face the camera is looking at, so
            # the film can show it closing over everything just made.
            part((ox, oy + half + 0.04, base_z + 1.55),
                 (half * 2, 0.03, 2.2), (0.46, 0.48, 0.52), MAT_METAL)
    return drawn


def build_utility_column(b: MeshBuilder, origin, base_z: float,
                         apex_z: float, *, fixtures: bool = True,
                         face_deg: float = 0.0) -> None:
    """The column: pad port to apex, and out through the top.

    ``apex_z`` is where the frame's apex sits above ``base_z``. The riser does
    not stop there. It passes through a sleeve, and the part standing proud of
    it is the interface boundary -- the place a line can be picked up from
    outside without opening the building.
    """
    ox, oy = origin
    z = base_z
    build_pad_port(b, origin, z)

    top = z + apex_z
    # The housing: an eight-sided metal column, stopping short of the apex so
    # the sleeve and the cap have somewhere to sit.
    housing_top = top - 0.55
    b.cylinder((ox, oy, z + 0.10), (ox, oy, housing_top), COLUMN_RADIUS_M, 8,
               STEEL, mat_id=MAT_METAL, cap_ends=False)
    b.disc((ox, oy, housing_top), COLUMN_RADIUS_M, 8, (0.50, 0.53, 0.56),
           mat_id=MAT_METAL)

    if fixtures:
        _column_fixtures(b, origin, z, face_deg)

    # The riser: one chase, all the way up and out.
    b.cylinder((ox, oy, housing_top), (ox, oy, top + 0.46), RISER_RADIUS_M,
               10, CONDUIT, mat_id=MAT_METAL)
    b.cylinder((ox + 0.10, oy, housing_top), (ox + 0.10, oy, top + 0.40),
               0.034, 8, PIPE_BLUE, mat_id=MAT_PLAIN)
    b.cylinder((ox - 0.10, oy, housing_top), (ox - 0.10, oy, top + 0.40),
               0.034, 8, PIPE_RED, mat_id=MAT_PLAIN)

    # The sleeve through the apex: the hole, lined.
    b.cylinder((ox, oy, top - 0.12), (ox, oy, top + 0.14), SLEEVE_RADIUS_M,
               16, DARK_STEEL, mat_id=MAT_METAL, cap_ends=False)


def build_seal_cap(b: MeshBuilder, origin, base_z: float, apex_z: float,
                   *, open_cap: bool = False) -> None:
    """The gasketed cap that closes the apex penetration.

    Drawn as three separate things on purpose -- a compression gasket, a cap
    and a ring of bolts -- because that is the difference between this and a
    hatch. It is meant to stay shut for years.
    """
    ox, oy = origin
    top = base_z + apex_z
    lift = 0.55 if open_cap else 0.0

    # Backing ring laminated into the shell, and the gasket on top of it.
    b.cylinder((ox, oy, top + 0.13), (ox, oy, top + 0.17), CAP_RADIUS_M, 24,
               (0.42, 0.44, 0.47), mat_id=MAT_METAL)
    b.cylinder((ox, oy, top + 0.17), (ox, oy, top + 0.20), CAP_RADIUS_M - 0.01,
               24, GASKET, mat_id=MAT_PLAIN)

    # The cap: a shallow dished disc, sitting on the gasket or held above it.
    cap_z = top + 0.20 + lift
    b.cylinder((ox, oy, cap_z), (ox, oy, cap_z + 0.06), CAP_RADIUS_M, 24,
               (0.78, 0.80, 0.82), mat_id=MAT_METAL, cap_ends=False)
    b.disc((ox, oy, cap_z + 0.06), CAP_RADIUS_M, 24, (0.80, 0.82, 0.84),
           mat_id=MAT_METAL)
    b.cone((ox, oy, cap_z + 0.06), (ox, oy, cap_z + 0.16), CAP_RADIUS_M * 0.62,
           20, (0.74, 0.76, 0.79), mat_id=MAT_METAL)

    for point, _angle in _ring((ox, oy, top + 0.18), CAP_RADIUS_M - 0.045, 8):
        b.cylinder(point, (point[0], point[1], point[2] + 0.10 + lift), 0.016,
                   6, BRASS, mat_id=MAT_METAL)


def build_camera_ring(b: MeshBuilder, origin, base_z: float, apex_z: float,
                      *, lenses: int = 6) -> None:
    """The 360 camera, standing on the seal cap.

    It goes on top of the cap rather than through it, which is the whole
    reason the cap is where it is: the highest point on the building already
    has power at it, so the one thing that wants to see in every direction can
    be bolted on without opening anything.
    """
    ox, oy = origin
    top = base_z + apex_z + 0.42
    b.cylinder((ox, oy, top), (ox, oy, top + 0.10), 0.09, 10, DARK_STEEL,
               mat_id=MAT_METAL)
    b.cylinder((ox, oy, top + 0.10), (ox, oy, top + 0.26), 0.15, lenses,
               (0.22, 0.23, 0.26), mat_id=MAT_METAL, cap_ends=False)
    b.disc((ox, oy, top + 0.26), 0.16, lenses, (0.30, 0.32, 0.35),
           mat_id=MAT_METAL)
    for point, angle in _ring((ox, oy, top + 0.18), 0.152, lenses):
        b.sphere(point, 0.035, (0.10, 0.14, 0.22), mat_id=MAT_GLASS,
                 rings=3, sides=6)


def build_exterior_routing(b: MeshBuilder, origin, base_z: float,
                           apex_z: float, radius: float, bearing_deg: float,
                           *, drop_to: float | None = None) -> None:
    """A service line from under the cap, over the shell, down to a panel.

    Followed as an arc over the dome rather than a straight line, because a
    line clipped to the outside of a curved surface is what it actually is,
    and a chord would pass through the shell.
    """
    ox, oy = origin
    angle = math.radians(bearing_deg)
    dx, dy = math.cos(angle), math.sin(angle)
    top = base_z + apex_z
    steps = 14
    points = []
    for index in range(steps + 1):
        t = index / steps
        theta = t * math.pi * 0.5
        r = radius * math.sin(theta) * 1.02
        height = apex_z * math.cos(theta)
        points.append((ox + dx * r, oy + dy * r, base_z + height + 0.05))
    points[0] = (ox, oy, top + 0.30)
    if drop_to is not None:
        last = points[-1]
        points.append((last[0], last[1], drop_to))
    # The water line runs beside the conduit, not on top of it: the offset is
    # across the bearing, so the pair stays side by side all the way round.
    px, py = -dy * 0.085, dx * 0.085
    for start, end in zip(points, points[1:]):
        b.cylinder(start, end, 0.034, 8, CONDUIT, mat_id=MAT_PLAIN)
        b.cylinder((start[0] + px, start[1] + py, start[2]),
                   (end[0] + px, end[1] + py, end[2]), 0.026, 8, PIPE_BLUE,
                   mat_id=MAT_PLAIN)


def _column_fixtures(b: MeshBuilder, origin, z: float,
                     face_deg: float) -> None:
    """Shower head, sink, drain and the outlet ring, on the column's faces."""
    ox, oy = origin
    angle = math.radians(face_deg)
    dx, dy = math.cos(angle), math.sin(angle)
    px, py = -dy, dx
    reach = COLUMN_RADIUS_M

    # Sink: a shallow basin on a bracket, with a tap and a trap below it.
    sink = (ox + dx * (reach + 0.22), oy + dy * (reach + 0.22), z + 0.92)
    b.cylinder((sink[0], sink[1], sink[2]),
               (sink[0], sink[1], sink[2] + 0.12), 0.21, 16,
               (0.88, 0.89, 0.90), mat_id=MAT_METAL, cap_ends=False)
    b.disc((sink[0], sink[1], sink[2]), 0.21, 16, (0.82, 0.84, 0.86),
           mat_id=MAT_METAL)
    b.cylinder((ox + dx * reach, oy + dy * reach, z + 1.06),
               (sink[0], sink[1], sink[2] + 0.18), 0.022, 8, BRASS,
               mat_id=MAT_METAL)
    b.cylinder((sink[0], sink[1], sink[2] - 0.35),
               (sink[0], sink[1], sink[2]), 0.05, 10, DRAIN, mat_id=MAT_PLAIN)

    # Shower: an arm out of the opposite face and a head pointing down.
    head = (ox - dx * (reach + 0.30), oy - dy * (reach + 0.30), z + 1.95)
    b.cylinder((ox - dx * reach, oy - dy * reach, z + 1.95), head, 0.022, 8,
               BRASS, mat_id=MAT_METAL)
    b.cone((head[0], head[1], head[2] - 0.10), (head[0], head[1], head[2]),
           0.10, 12, (0.86, 0.88, 0.90), mat_id=MAT_METAL)
    # The pan and its drain, on the floor under it.
    b.cylinder((head[0], head[1], z), (head[0], head[1], z + 0.06), 0.52, 20,
               (0.74, 0.76, 0.78), mat_id=MAT_PLAIN, cap_ends=False)
    b.disc((head[0], head[1], z + 0.03), 0.52, 20, (0.70, 0.72, 0.74),
           mat_id=MAT_PLAIN)

    # The outlet ring: four plates around the column at working height.
    for index in range(4):
        theta = angle + math.tau * (index + 0.5) / 4.0
        cx = ox + math.cos(theta) * (reach + 0.015)
        cy = oy + math.sin(theta) * (reach + 0.015)
        box(b, (cx, cy, z + 1.15), (0.13, 0.13, 0.17), (0.92, 0.92, 0.90),
            MAT_PLAIN)

    # A small sub-panel door low on the face at ninety degrees.
    door = (ox + px * (reach + 0.02), oy + py * (reach + 0.02), z + 1.45)
    box(b, door, (0.30, 0.05, 0.42), (0.36, 0.38, 0.42), MAT_METAL)


# ----------------------------------------------------------------------
# The polyps
# ----------------------------------------------------------------------

POLYP_SLOTS = 4
"""Snap-in module bays in one utility panel."""


def polyp_bearings(count: int, start_deg: float = 34.0) -> tuple[float, ...]:
    """Where ``count`` panels sit around the rim, spread so none overlaps."""
    if count <= 0:
        return ()
    return tuple(start_deg + 360.0 * index / count for index in range(count))


def build_polyp(b: MeshBuilder, origin, base_z: float, radius: float,
                bearing_deg: float, *, modules: int = 0,
                lit: bool = False) -> None:
    """One utility panel hanging off the rim, outside the footprint.

    Its body sits past the dome's edge -- that is the point, it does not eat
    floor -- while its back face reaches in through a gasketed port, so
    whatever is snapped into it is reachable from inside.
    """
    angle = math.radians(bearing_deg)
    dx, dy = math.cos(angle), math.sin(angle)
    px, py = -dy, dx

    depth = 0.62
    width = 1.05
    height = 1.35
    # Clear of the rim, not lapped over it. "Mainly outside the footprint"
    # has to be visibly true or the drawing is arguing against the claim.
    centre_r = radius + depth * 0.5 + 0.10
    cx = origin[0] + dx * centre_r
    cy = origin[1] + dy * centre_r
    cz = base_z + height * 0.5 + 0.12

    # The body, built from four walls so it can face any bearing.
    corners_low = []
    corners_high = []
    for su, sv in ((-0.5, -0.5), (0.5, -0.5), (0.5, 0.5), (-0.5, 0.5)):
        x = cx + dx * (su * depth) + px * (sv * width)
        y = cy + dy * (su * depth) + py * (sv * width)
        corners_low.append((x, y, cz - height * 0.5))
        corners_high.append((x, y, cz + height * 0.5))
    shell = (0.46, 0.48, 0.52)
    for index in range(4):
        nxt = (index + 1) % 4
        edge = np.asarray(corners_low[nxt]) - np.asarray(corners_low[index])
        normal = np.array([edge[1], -edge[0], 0.0])
        norm = float(np.linalg.norm(normal)) or 1.0
        b.quad(corners_low[index], corners_low[nxt], corners_high[nxt],
               corners_high[index], tuple(normal / norm), shell,
               mat_id=MAT_METAL)
    b.quad(*corners_high, (0.0, 0.0, 1.0), (0.38, 0.40, 0.44),
           mat_id=MAT_METAL)

    # A weather lid, hinged along the inboard edge and propped open a crack.
    lid_lift = 0.10
    lid = [(x + dx * 0.06, y + dy * 0.06,
            z + lid_lift * (0.4 if index < 2 else 1.0))
           for index, (x, y, z) in enumerate(corners_high)]
    b.quad(*lid, (0.0, 0.0, 1.0), (0.30, 0.33, 0.37), mat_id=MAT_METAL)

    # Module bays on the outboard face.
    face_r = centre_r + depth * 0.5 + 0.01
    for slot in range(POLYP_SLOTS):
        offset = (slot - (POLYP_SLOTS - 1) / 2.0) * (width / POLYP_SLOTS)
        fx = origin[0] + dx * face_r + px * offset
        fy = origin[1] + dy * face_r + py * offset
        filled = slot < modules
        colour = (0.82, 0.84, 0.86) if filled else (0.28, 0.30, 0.33)
        mat = MAT_METAL if filled else MAT_PLAIN
        box(b, (fx, fy, cz), (0.16, width / POLYP_SLOTS * 0.82, height * 0.68),
            colour, mat)
        if filled and lit:
            box(b, (fx + dx * 0.09, fy + dy * 0.09, cz + 0.42),
                (0.03, width / POLYP_SLOTS * 0.5, 0.10), (0.35, 1.0, 0.55),
                MAT_EMISSIVE)

    # The pass-through: a short gasketed sleeve reaching back under the shell.
    inner = (origin[0] + dx * (radius - 0.30), origin[1] + dy * (radius - 0.30),
             base_z + 0.95)
    outer = (origin[0] + dx * centre_r, origin[1] + dy * centre_r,
             base_z + 0.95)
    b.cylinder(inner, outer, 0.085, 12, DARK_STEEL, mat_id=MAT_METAL)
    b.cylinder(inner, (inner[0] + dx * 0.06, inner[1] + dy * 0.06, inner[2]),
               0.115, 12, GASKET, mat_id=MAT_PLAIN)

    # Feet, because it is a panel standing on the ground and not a growth.
    for sign in (-1.0, 1.0):
        fx = cx + px * sign * width * 0.42
        fy = cy + py * sign * width * 0.42
        b.cylinder((fx, fy, base_z - 0.12), (fx, fy, cz - height * 0.5),
                   0.045, 8, DARK_STEEL, mat_id=MAT_METAL)


# ----------------------------------------------------------------------
# The platform, built in the order it is actually built
# ----------------------------------------------------------------------

DECK_STAGES: tuple[str, ...] = (
    "gravel", "piers", "beams", "joists", "boards", "sealed",
)
"""The stages :func:`build_deck_stage` can draw, in build order.

The same order :func:`pad_deck.build_sequence` costs them in, so a film that
walks through these is walking through the quote.
"""

GRAVEL = (0.46, 0.45, 0.42)
PIER = (0.62, 0.62, 0.60)
BEAM = (0.42, 0.31, 0.20)
JOIST = (0.52, 0.39, 0.25)
BOARD = (0.62, 0.47, 0.30)
SEALED = (0.46, 0.33, 0.20)


def build_deck_stage(b: MeshBuilder, stage: str, origin=(0.0, 0.0),
                     base_z: float = 0.0, across_ft: float | None = None,
                     partial: float = 1.0) -> int:
    """The platform, drawn up to and including ``stage``.

    ``partial`` is how much of that last stage is laid, 0 to 1, which is what
    lets a film show boards going down one at a time rather than appearing.
    Everything is a decagon because the dome's base is, and because cutting
    straight boards to ten flats is what the takeoff prices.
    """
    import pad_deck

    if stage not in DECK_STAGES:
        raise KeyError(f"unknown deck stage {stage!r}")
    reached = DECK_STAGES.index(stage)
    across = pad_deck.pad_diameter_ft() if across_ft is None else across_ft
    radius = m(across * 12.0 / 2.0)
    ox, oy = origin
    sides = 10
    drawn = 0

    def ring(r: float, z: float, colour, thickness: float, mat=MAT_WOOD):
        nonlocal drawn
        for index in range(sides):
            a0 = math.tau * index / sides
            a1 = math.tau * (index + 1) / sides
            p0 = (ox + math.cos(a0) * r, oy + math.sin(a0) * r, z)
            p1 = (ox + math.cos(a1) * r, oy + math.sin(a1) * r, z)
            q0 = (p0[0], p0[1], z - thickness)
            q1 = (p1[0], p1[1], z - thickness)
            b.quad(p0, p1, q1, q0, (math.cos((a0 + a1) / 2),
                                    math.sin((a0 + a1) / 2), 0.0),
                   colour, mat_id=mat)
            b.triangle((ox, oy, z), p0, p1, colour, mat_id=mat)
            drawn += 2

    # 1. Gravel: a shallow decagonal pad of crusher run.
    if reached >= 0:
        share = partial if reached == 0 else 1.0
        ring(radius * 1.04 * share, base_z + 0.04, GRAVEL, 0.10, MAT_PLAIN)

    # 2. Piers: precast blocks on a grid, only where a beam will land.
    if reached >= 1:
        spacing = m(pad_deck.declared("beam_spacing_ft") * 12.0)
        points = []
        steps = int(radius / spacing) + 1
        for ix in range(-steps, steps + 1):
            for iy in range(-steps, steps + 1):
                x, y = ix * spacing, iy * spacing
                if math.hypot(x, y) <= radius * 0.92:
                    points.append((x, y))
        points.sort(key=lambda pt: math.hypot(pt[0], pt[1]))
        share = partial if reached == 1 else 1.0
        for x, y in points[:max(1, int(len(points) * share))]:
            box(b, (ox + x, oy + y, base_z + 0.20), (0.30, 0.30, 0.22),
                PIER, MAT_PLAIN)
            drawn += 6

    # 3. Beams: doubled runs across the platform, on the piers.
    if reached >= 2:
        spacing = m(pad_deck.declared("beam_spacing_ft") * 12.0)
        runs = [i * spacing for i in range(-3, 4)
                if abs(i * spacing) <= radius * 0.92]
        share = partial if reached == 2 else 1.0
        for y in runs[:max(1, int(len(runs) * share))] if share < 1.0 else runs:
            half = math.sqrt(max(0.0, radius ** 2 - y ** 2)) * 0.96
            box(b, (ox, oy + y, base_z + 0.38), (half * 2.0, 0.16, 0.14),
                BEAM, MAT_WOOD)
            drawn += 6

    # 4. Joists: at 16 in centres, across the beams.
    if reached >= 3:
        spacing = m(pad_deck.declared("joist_spacing_in"))
        count = int(radius * 2.0 / spacing)
        xs = [(-radius + (i + 0.5) * spacing) for i in range(count)]
        share = partial if reached == 3 else 1.0
        for x in xs[:max(1, int(len(xs) * share))]:
            half = math.sqrt(max(0.0, radius ** 2 - x ** 2)) * 0.97
            if half <= 0.05:
                continue
            box(b, (ox + x, oy, base_z + 0.50), (0.09, half * 2.0, 0.14),
                JOIST, MAT_WOOD)
            drawn += 6

    # 5. Boards: laid across the joists, one at a time.
    if reached >= 4:
        width = m(pad_deck.declared("board_face_in"))
        count = int(radius * 2.0 / width)
        colour = SEALED if reached >= 5 else BOARD
        ys = [(-radius + (i + 0.5) * width) for i in range(count)]
        share = partial if reached in (4, 5) else 1.0
        for y in ys[:max(1, int(len(ys) * share))]:
            half = math.sqrt(max(0.0, radius ** 2 - y ** 2)) * 0.98
            if half <= 0.05:
                continue
            box(b, (ox, oy + y, base_z + 0.60),
                (half * 2.0, width * 0.92, 0.05), colour, MAT_WOOD)
            drawn += 6

    return drawn


def deck_top_m(base_z: float = 0.0) -> float:
    """Where the finished platform's surface sits, for standing a dome on."""
    return base_z + 0.63


def build_open_floor(b: MeshBuilder, origin, base_z: float, radius: float,
                     sides: int = 10, port_radius: float = 0.55) -> None:
    """The dome's own floor: a deck with a hole in the middle of it.

    Open in the literal sense. The services arrive in the centre of the pad
    and the floor is built around that opening rather than over it, so the
    port stays reachable with the dome standing on it. Drawn as an annulus,
    never as a disc with something laid on top: two surfaces a few
    millimetres apart z-fight and the floor comes out striped.
    """
    ox, oy = origin
    z = base_z + 0.02
    deck = (0.50, 0.38, 0.25)
    joist = (0.38, 0.28, 0.18)
    for index in range(sides):
        a0 = math.tau * index / sides
        a1 = math.tau * (index + 1) / sides
        inner0 = (ox + math.cos(a0) * port_radius,
                  oy + math.sin(a0) * port_radius, z)
        inner1 = (ox + math.cos(a1) * port_radius,
                  oy + math.sin(a1) * port_radius, z)
        outer0 = (ox + math.cos(a0) * radius, oy + math.sin(a0) * radius, z)
        outer1 = (ox + math.cos(a1) * radius, oy + math.sin(a1) * radius, z)
        b.quad(inner0, inner1, outer1, outer0, (0.0, 0.0, 1.0), deck,
               mat_id=MAT_WOOD)
        # One joist per bay, under the deck, so the floor has a thickness.
        mid = (a0 + a1) * 0.5
        b.cylinder((ox + math.cos(mid) * port_radius,
                    oy + math.sin(mid) * port_radius, z - 0.09),
                   (ox + math.cos(mid) * radius,
                    oy + math.sin(mid) * radius, z - 0.09),
                   0.055, 6, joist, mat_id=MAT_WOOD)
    b.cylinder((ox, oy, base_z), (ox, oy, z), radius, sides, joist,
               mat_id=MAT_WOOD, cap_ends=False)


# ----------------------------------------------------------------------
# The stove: a little all-metal dome with a flat top
# ----------------------------------------------------------------------

def build_stove_dome(b: MeshBuilder, centre, base_z: float,
                     radius: float = 0.42, *, lit: bool = True,
                     flue_top: float = 3.4) -> None:
    """The heater: the same shape, in steel, with the top cut flat to cook on.

    Drawn as a faceted half-dome rather than a smooth one because it is made
    the way the building is made -- panels, not a pressing -- and at this size
    that is visible.
    """
    cx, cy = centre
    rings, sides = 3, 10
    flat_at = 0.62
    for row in range(rings):
        t0 = row / rings * flat_at
        t1 = (row + 1) / rings * flat_at
        for col in range(sides):
            a0 = math.tau * col / sides
            a1 = math.tau * (col + 1) / sides

            def point(t, a):
                pitch = t * math.pi * 0.5
                return (cx + math.cos(pitch) * radius * math.cos(a),
                        cy + math.cos(pitch) * radius * math.sin(a),
                        base_z + math.sin(pitch) * radius * 1.25)

            q0, q1 = point(t0, a0), point(t0, a1)
            q2, q3 = point(t1, a1), point(t1, a0)
            b.quad(q0, q1, q2, q3,
                   (math.cos(a0), math.sin(a0), 0.35), CAST_IRON,
                   mat_id=MAT_METAL)

    top_z = base_z + math.sin(flat_at * math.pi * 0.5) * radius * 1.25
    plate_r = math.cos(flat_at * math.pi * 0.5) * radius
    b.disc((cx, cy, top_z), plate_r, sides, (0.22, 0.22, 0.23),
           mat_id=MAT_METAL)
    b.cylinder((cx, cy, top_z), (cx, cy, top_z + 0.04), plate_r, sides,
               (0.26, 0.26, 0.27), mat_id=MAT_METAL, cap_ends=False)

    # The door, and the fire behind it when it is lit.
    door = (cx + radius * 0.94, cy, base_z + radius * 0.42)
    box(b, door, (0.05, 0.30, 0.26), (0.12, 0.12, 0.13), MAT_METAL)
    if lit:
        box(b, (door[0] + 0.03, door[1], door[2]), (0.02, 0.20, 0.16),
            EMBER, MAT_EMISSIVE)

    # The flue, out of the side of the flat top and up through the shell.
    fx = cx - plate_r * 0.45
    b.cylinder((fx, cy, top_z), (fx, cy, base_z + flue_top), 0.075, 10,
               (0.30, 0.31, 0.33), mat_id=MAT_METAL)
    b.cylinder((fx, cy, base_z + flue_top - 0.18),
               (fx, cy, base_z + flue_top - 0.06), 0.11, 12, DARK_STEEL,
               mat_id=MAT_METAL)


def build_berm(b: MeshBuilder, origin, base_z: float, radius: float,
               height: float, *, sides: int = 24) -> None:
    """Earth heaped over a buried dome, leaving the riser above grade.

    The bunker seed is not a different dome. It is this dome with soil
    against it, and the only thing left showing is the apex -- which is
    exactly what the interface boundary was built for: one penetration, one
    gasketed cap, and every service on the outside of the ground.
    """
    ox, oy = origin
    outer = radius * 1.75
    soil = (0.34, 0.28, 0.20)
    grass = (0.28, 0.38, 0.22)
    for index in range(sides):
        a0 = math.tau * index / sides
        a1 = math.tau * (index + 1) / sides
        inner0 = (ox + math.cos(a0) * radius * 0.86,
                  oy + math.sin(a0) * radius * 0.86, base_z + height)
        inner1 = (ox + math.cos(a1) * radius * 0.86,
                  oy + math.sin(a1) * radius * 0.86, base_z + height)
        out0 = (ox + math.cos(a0) * outer, oy + math.sin(a0) * outer, base_z)
        out1 = (ox + math.cos(a1) * outer, oy + math.sin(a1) * outer, base_z)
        mid = (a0 + a1) * 0.5
        normal = (math.cos(mid) * 0.45, math.sin(mid) * 0.45, 0.89)
        b.quad(out0, out1, inner1, inner0, normal, grass, mat_id=materials_grass())
        b.quad((out0[0], out0[1], base_z - 0.35),
               (out1[0], out1[1], base_z - 0.35), out1, out0,
               (math.cos(mid), math.sin(mid), 0.0), soil, mat_id=MAT_PLAIN)


def materials_grass() -> int:
    """The grass material id, looked up rather than imported at the top.

    Kept as a function because :mod:`materials` is the Creator's table and
    this module should not grow a second import list beside the first."""
    import materials

    return materials.MAT_GRASS


def build_tree_support(b: MeshBuilder, origin, base_z: float, radius: float,
                       lift: float) -> None:
    """The trunk, the saddle beams and the stair under a treed dome.

    The pad does not disappear when the dome goes up a tree; it moves. The
    saddle is the pad, the trunk carries the services, and the port on the
    underside of the floor is the same port.
    """
    ox, oy = origin
    trunk = (0.30, 0.24, 0.17)
    limb = (0.36, 0.28, 0.19)

    b.cylinder((ox, oy, base_z - 0.20), (ox, oy, base_z + lift + 1.6), 0.46,
               12, trunk, mat_id=MAT_WOOD)
    # Roots flaring out, so the trunk does not look like a post.
    for point, angle in _ring((ox, oy, base_z + 0.05), radius * 0.30, 6):
        b.cylinder((ox, oy, base_z + 0.85), (point[0], point[1], base_z - 0.05),
                   0.13, 6, trunk, mat_id=MAT_WOOD)
    # Saddle beams under the floor, and the braces back to the trunk.
    for index in range(3):
        angle = math.tau * index / 3.0
        end = (ox + math.cos(angle) * radius * 1.05,
               oy + math.sin(angle) * radius * 1.05, base_z + lift - 0.18)
        b.cylinder((ox, oy, base_z + lift - 0.18), end, 0.14, 8, limb,
                   mat_id=MAT_WOOD)
        b.cylinder(end, (ox, oy, base_z + lift - 1.45), 0.10, 6, limb,
                   mat_id=MAT_WOOD)
        # Canopy, so it reads as a tree rather than a mast. Set outboard
        # and low: heaped on top it swallows the dome, which is the one
        # thing the picture is supposed to show.
        b.sphere((ox + math.cos(angle) * radius * 1.30,
                  oy + math.sin(angle) * radius * 1.30,
                  base_z + lift - 0.30), radius * 0.66, (0.24, 0.42, 0.22),
                 mat_id=materials_grass(), rings=4, sides=8)
    # A stair up to the floor.
    steps = 12
    for index in range(steps):
        t = (index + 1) / steps
        x = ox + radius * 1.35 * (1.0 - t * 0.45)
        box(b, (x, oy - radius * 0.65, base_z + lift * t),
            (0.42, 0.90, 0.07), (0.46, 0.34, 0.22), MAT_WOOD)


# ----------------------------------------------------------------------
# The mast, the dome's own floor, and the floating rig
# ----------------------------------------------------------------------

def build_mast(b: MeshBuilder, origin, base_z: float, *,
               clad: float = 1.0, ring: bool = True) -> None:
    """The mast that stands *inside* the utility column.

    Steel where the strength is, timber everywhere else, which is the whole
    argument of the upgrade: the services and the structure share one
    penetration and one object to look at. ``clad`` winds the timber on from
    the bottom, so a chapter can show the core before it is boxed in.

    The rise is :func:`seed_model.mast_rise_ft`, the same length that
    :func:`seed_model.mast_group` prices, so the picture and the invoice are
    the same mast.
    """
    ox, oy = origin
    rise = m(seed_model.mast_rise_ft() * 12.0)
    top = base_z + rise
    # The base flange, landing the mast on the service port.
    b.cylinder((ox, oy, base_z), (ox, oy, base_z + 0.06), 0.30, 12,
               DARK_STEEL, mat_id=MAT_METAL)
    b.cylinder((ox, oy, base_z + 0.04), (ox, oy, top), 0.075, 10,
               STEEL, mat_id=MAT_METAL)
    # Timber boxed round the core. Square in section, because that is what
    # four boards make, and it is the quickest way to read "wood over steel".
    grown = clamp01(clad)
    clad_base = base_z + 0.20
    clad_top = clad_base + (top - 0.55 - clad_base) * grown
    if clad_top - clad_base > 0.02:
        half = 0.13
        for sx, sy in ((1, 0), (-1, 0), (0, 1), (0, -1)):
            box(b, (ox + sx * half, oy + sy * half,
                    (clad_base + clad_top) * 0.5),
                (0.075 if sx else 0.30, 0.30 if sx else 0.075,
                 clad_top - clad_base),
                (0.52, 0.40, 0.26), MAT_WOOD)
    if ring:
        # The forged lifting ring, above the shell and under the seal cap.
        # This is the hoist point for the whole structure and the thing the
        # floating rig hangs from.
        b.cylinder((ox, oy, top - 0.10), (ox, oy, top + 0.02), 0.165, 14,
                   DARK_STEEL, mat_id=MAT_METAL, cap_ends=False)
        b.disc((ox, oy, top + 0.02), 0.165, 14, (0.42, 0.45, 0.48),
               mat_id=MAT_METAL)
        for point, _ in _ring((ox, oy, top + 0.10), 0.125, 3):
            b.sphere(point, 0.055, (0.70, 0.73, 0.76), mat_id=MAT_METAL,
                     rings=4, sides=8)


def mast_top_m(base_z: float = 0.0) -> float:
    """Where the mast's lifting ring sits: what the floating rig hangs from."""
    return base_z + m(seed_model.mast_rise_ft() * 12.0)


def build_dome_floor(b: MeshBuilder, origin, base_z: float, radius: float, *,
                     sides: int = 10, reveal: float = 1.0,
                     rail: bool = True) -> None:
    """The dome's own floor, clamped to the mast: hub, spokes, deck, rail.

    The pad's deck is the host's and stays when the dome leaves. This floor
    is the buyer's and goes with the dome, which is the only reason a
    floating dome is possible at all -- there is no ground under it to
    stand on.

    ``reveal`` deals the spokes and their decking out one bay at a time, so
    a chapter can show it being built rather than appearing.
    """
    ox, oy = origin
    z = base_z
    hub_r = 0.42
    deck = (0.50, 0.38, 0.25)
    b.cylinder((ox, oy, z - 0.06), (ox, oy, z + 0.10), hub_r, 14, DARK_STEEL,
               mat_id=MAT_METAL)
    b.disc((ox, oy, z + 0.10), hub_r, 14, (0.46, 0.49, 0.52), mat_id=MAT_METAL)
    shown = clamp01(reveal) * sides
    for index in range(sides):
        local = clamp01(shown - index)
        if local <= 0.001:
            continue
        a0 = math.tau * index / sides
        a1 = math.tau * (index + 1) / sides
        mid = (a0 + a1) * 0.5
        # The spoke draws out to the base ring, then its bay decks over.
        reach = hub_r + (radius - hub_r) * local
        b.cylinder((ox + math.cos(mid) * hub_r, oy + math.sin(mid) * hub_r,
                    z - 0.02),
                   (ox + math.cos(mid) * reach, oy + math.sin(mid) * reach,
                    z - 0.02), 0.045, 6, STEEL, mat_id=MAT_METAL)
        if local < 0.999:
            continue
        inner0 = (ox + math.cos(a0) * hub_r, oy + math.sin(a0) * hub_r, z)
        inner1 = (ox + math.cos(a1) * hub_r, oy + math.sin(a1) * hub_r, z)
        outer0 = (ox + math.cos(a0) * radius, oy + math.sin(a0) * radius, z)
        outer1 = (ox + math.cos(a1) * radius, oy + math.sin(a1) * radius, z)
        b.quad(inner0, inner1, outer1, outer0, (0.0, 0.0, 1.0), deck,
               mat_id=MAT_WOOD)
        if rail:
            b.cylinder((outer0[0], outer0[1], z + 0.02),
                       (outer1[0], outer1[1], z + 0.02), 0.035, 6,
                       (0.40, 0.30, 0.20), mat_id=MAT_WOOD)


def float_tree_positions(radius: float, spread: float = 2.35
                         ) -> tuple[tuple[float, float], ...]:
    """Where the trees stand for the floating rig.

    Two trees, because that is what the chapter says -- and three cables, so
    one tree takes two legs. Kept in one place so the picture and anything
    that checks it read the same arrangement.
    """
    return ((-radius * spread, -radius * 0.35),
            (radius * spread, radius * 0.30))


def build_float_rig(b: MeshBuilder, origin, base_z: float, hang_z: float,
                    radius: float, *, cable: float = 1.0,
                    trees: bool = True) -> None:
    """Three cables from the apex hanger to saddles on two trees.

    Saddles, not holes: nothing is drilled into a tree. ``cable`` runs the
    legs out from the hanger, so a chapter can show them being rigged.

    This draws what :func:`seed_model.suspension_group` prices. It does not
    draw a rating -- the loads on the trees, the cables and the mast are the
    engineer's number, and the chapter says so out loud.
    """
    ox, oy = origin
    trunk = (0.34, 0.26, 0.18)
    canopy = (0.20, 0.38, 0.20)
    spots = float_tree_positions(radius)
    # The saddles have to stand well clear of the hanger or the three legs
    # come out near horizontal and read as one clothesline strung between
    # two trees, which is not what is holding the building up.
    tree_h = hang_z + 6.4
    if trees:
        for tx, ty in spots:
            b.cylinder((ox + tx, oy + ty, base_z - 0.4),
                       (ox + tx, oy + ty, base_z + tree_h), 0.40, 10, trunk,
                       mat_id=MAT_WOOD)
            for dz, rad in ((0.15, 1.75), (1.05, 1.40), (1.85, 0.95)):
                b.sphere((ox + tx, oy + ty, base_z + tree_h * 0.70 + dz),
                         rad, canopy, mat_id=materials_grass(),
                         rings=5, sides=10)
    # Two legs to the first tree, one to the second: three cables, two trees.
    saddles = (spots[0], spots[0], spots[1])
    hanger = (ox, oy, base_z + hang_z)
    b.sphere(hanger, 0.14, (0.38, 0.41, 0.44), mat_id=MAT_METAL,
             rings=5, sides=10)
    run = clamp01(cable)
    for index, (tx, ty) in enumerate(saddles):
        # The two legs sharing a tree land either side of its saddle, or they
        # draw as one cable and the picture quietly loses a leg.
        skew = (index - 0.5) * 1.30 if index < 2 else 0.0
        anchor = (ox + tx + skew, oy + ty, base_z + tree_h * 0.80)
        end = tuple(hanger[k] + (anchor[k] - hanger[k]) * run
                    for k in range(3))
        b.cylinder(hanger, end, 0.035, 5, (0.62, 0.64, 0.66),
                   mat_id=MAT_METAL)
    if run > 0.985:
        # The saddle: a strap round the trunk, no hole in the tree.
        for tx, ty in spots:
            b.cylinder((ox + tx, oy + ty, base_z + tree_h * 0.80 - 0.14),
                       (ox + tx, oy + ty, base_z + tree_h * 0.80 + 0.14),
                       0.46, 10, (0.30, 0.32, 0.34), mat_id=MAT_METAL,
                       cap_ends=False)

# ----------------------------------------------------------------------
# The wall in section, and the member we would rather make
# ----------------------------------------------------------------------

def build_layer_stack(b: MeshBuilder, origin, base_z: float, *,
                      layers: int = 3, spread: float = 1.0,
                      width: float = 2.6) -> tuple[tuple[str, float], ...]:
    """The cap stack cut through, laid flat, so the ORDER is legible.

    A dome wearing hats shows that the stack grows. It cannot show which
    layer keeps the water out, and that is the thing the campaign is
    actually claiming: exactly one watertight layer, on the outside, with
    everything under it free to dry.

    Returns each layer's name and the height it was drawn at, so the scene
    can label them without guessing where they landed.
    """
    import soft_shell as soft

    ox, oy = origin
    depth = width * 0.62
    gap = m(soft.declared("cap_vent_gap_in"))
    quilt = m(soft.declared("layer_thickness_in"))

    # Thicknesses, bottom (inside) to top (outside). The sheet layers have
    # no real thickness worth drawing, so they get a readable minimum and
    # the label carries the truth.
    sheet = 0.035
    plan: list[tuple[str, float, tuple[float, float, float]]] = [
        ("THE FRAME", m(seed_model.seed_geometry().member_depth_in) * 0.5,
         (0.46, 0.34, 0.22)),
        ("WOOD PANEL", sheet * 1.6, (0.56, 0.44, 0.30)),
        ("BREATHER", sheet, (0.86, 0.86, 0.80)),
    ]
    for index in range(max(0, layers)):
        plan.append((f"QUILT {index + 1}", quilt, (0.68, 0.26, 0.28)))
    plan.append(("VENTED GAP", gap, (0.30, 0.34, 0.38)))
    plan.append(("THE CAP", sheet * 1.3, (0.34, 0.60, 0.74)))

    placed: list[tuple[str, float]] = []
    z = base_z
    for index, (name, thickness, colour) in enumerate(plan):
        # The exploded view separates them along the wall's normal, which is
        # the only way a sheet 0.03 m thick is visible at all.
        z += spread * 0.30 * (1 if index else 0)
        box(b, (ox, oy, z + thickness * 0.5), (width, depth, thickness),
            colour, MAT_WOOD if "PANEL" in name or "FRAME" in name
            else MAT_PLAIN)
        placed.append((name, z + thickness * 0.5))
        z += thickness
    return tuple(placed)


def build_composite_member(b: MeshBuilder, origin, base_z: float, *,
                           length: float = 1.83, explode: float = 0.0
                           ) -> tuple[tuple[str, tuple[float, float, float]], ...]:
    """The member the campaign wants to make: hardware moulded in.

    Steel core where the strength has to be, a moulded body around it,
    metal inserts where a fixing lands, and a spline ridge where the gasket
    sits. It does not exist. It is drawn because a chapter asking for the
    tooling to make it should show what the tooling is for.

    Returns each part's name and a point to hang a label on.
    """
    import soft_shell as soft

    ox, oy = origin
    geometry = seed_model.seed_geometry()
    # DRAWN AT 2.2x SECTION. A real member is 6 ft long and 4.6 in across,
    # and at that ratio the inserts -- which are the point of the chapter --
    # are three specks on a stick. The length is true; the section is not,
    # and the scene says so on screen.
    fat = 2.2
    depth = m(geometry.member_depth_in) * fat
    width = m(geometry.member_width_in) * fat
    lift = explode * 0.55

    # The moulded body: the wedge section, as a box tapering is not worth
    # the vertices at this size.
    box(b, (ox, oy, base_z + depth * 0.5), (length, width, depth),
        (0.30, 0.33, 0.38), MAT_PLAIN)

    # The steel core, drawn proud so it reads as inside rather than behind.
    b.cylinder((ox - length * 0.5, oy, base_z + depth * 0.5 + lift * 0.35),
               (ox + length * 0.5, oy, base_z + depth * 0.5 + lift * 0.35),
               width * 0.22, 10, STEEL, mat_id=MAT_METAL)

    # Threaded inserts along the face a panel screws into. They lift a
    # little less than the core does and they are drawn fat, because at a
    # full 0.55 m of explode they read as four brass discs somebody left on
    # the grass nearby rather than as parts of this member.
    count = int(soft.declared("panel_inserts_per_bay"))
    insert_lift = lift * 0.34
    for index in range(count):
        t = (index + 0.5) / count
        x = ox - length * 0.5 + length * t
        b.cylinder((x, oy, base_z + depth + insert_lift),
                   (x, oy, base_z + depth + insert_lift + 0.10),
                   width * 0.22, 12, (0.72, 0.66, 0.36), mat_id=MAT_METAL)
        # A stalk back down to the hole it came out of, so the eye joins
        # them up while they are apart.
        if insert_lift > 0.02:
            b.cylinder((x, oy, base_z + depth),
                       (x, oy, base_z + depth + insert_lift),
                       width * 0.05, 6, (0.55, 0.50, 0.28), mat_id=MAT_METAL)

    # The spline ridge, where the seam gasket sits: a rib down one edge.
    b.cylinder((ox - length * 0.5, oy + width * 0.5, base_z + depth * 0.62),
               (ox + length * 0.5, oy + width * 0.5, base_z + depth * 0.62),
               0.018, 8, (0.80, 0.52, 0.24), mat_id=MAT_PLAIN)

    return (
        ("MOULDED BODY", (ox, oy, base_z + depth * 0.5)),
        ("STEEL CORE", (ox - length * 0.30, oy,
                        base_z + depth * 0.5 + lift * 0.35)),
        (f"{count} INSERTS, MOULDED IN",
         (ox + length * 0.22, oy, base_z + depth + lift * 0.34 + 0.22)),
        ("SPLINE RIDGE FOR THE SEAL",
         (ox, oy + width * 0.5, base_z + depth * 0.62)),
    )
# ----------------------------------------------------------------------
# The removable shell
# ----------------------------------------------------------------------

def _shell_faces(offset_in: float) -> list[tuple[np.ndarray, str]]:
    """The forty panels of the shell, in inches, at an offset radius."""
    from two_v_demo import raw_wedge_bridge

    sim = raw_wedge_bridge.simulator()
    topo = sim.build_2v_hemisphere(seed_model.SEED_LONG_EDGE_IN)
    scale = (topo.sphere_radius_in + offset_in) / topo.sphere_radius_in
    out = []
    for face in topo.faces:
        points = topo.vertices[list(face.vertices)] * scale
        out.append((points, face.face_type))
    return out


def build_seed_shell(b: MeshBuilder, placement: SeedPlacement, *,
                     lift: float = 0.0, lit_faces: int = 0,
                     alpha: float = 1.0, split: float = 0.0,
                     grow_in: float = 0.0, colour=None) -> int:
    """The shell that fits over the frame and latches to the pad.

    ``lift`` raises it clear, which is the only way to show what a removable
    shell means. ``lit_faces`` turns that many panels into lit advert faces,
    which is the advertiser seed's whole product.

    ``split`` fans the shell into the slices it is moulded in --
    ``seed_model.declared("shell_halves")`` of them, meeting down S-lip seams.
    At 0 they are closed and it reads as one skin; wind it up and each slice
    draws out along its own bearing, which is the only way to show that a
    piece of this roof is something two people can carry.

    ``grow_in`` stands the skin further off the frame, in inches. That is
    what a soft cap does and a hull cannot: every quilted layer underneath
    makes the next cap a size bigger, by
    :func:`soft_shell.soft_shell(n).added_r`. ``colour`` overrides the skin,
    so a stack of them can be told apart.
    """
    geo = geometry()
    offset = (geo.member_depth_in + seed_model.declared("shell_standoff_in")
              + float(grow_in))
    faces = _shell_faces(offset)
    h, v, mirror = SHAPES.get(placement.shape, SHAPES["hemisphere"])
    ox, oy = placement.origin
    angle = math.radians(placement.heading_deg)
    cos, sin = math.cos(angle), math.sin(angle)
    base = placement.base_z + lift + base_lift_m(placement.shape)
    if mirror < 0:
        base += m(geo.height_in) * v

    def place(point):
        x, y, z = point[0] * M_PER_IN * h, point[1] * M_PER_IN * h, point[2]
        z = z * M_PER_IN * v * mirror
        return (ox + x * cos - y * sin, oy + x * sin + y * cos, base + z)

    # Lit panels are dealt out around the dome rather than clustered, so a
    # partial advertiser shell reads as "some sold" and not "one side built".
    # Which slice a face belongs to is decided by where its middle sits
    # around the dome, so a slice comes out as a wedge of the orange rather
    # than a scatter of triangles.
    slices = max(1, int(round(seed_model.declared("shell_halves"))))
    part = m(geo.radius_in + offset) * h * 0.55 * clamp01(split)

    def slice_of(bearing: float) -> int:
        return int(((bearing - angle) % math.tau) / math.tau * slices)

    def drawn_apart(slot: int) -> tuple[float, float]:
        """How far this slice has moved, along the middle of its own arc."""
        if part <= 0.0:
            return (0.0, 0.0)
        away = angle + math.tau * (slot + 0.5) / slices
        return (math.cos(away) * part, math.sin(away) * part)

    count = 0
    for index, (points, _kind) in enumerate(faces):
        corners = [place(points[i]) for i in range(3)]
        if part > 0.0:
            cx = sum(c[0] for c in corners) / 3.0 - ox
            cy = sum(c[1] for c in corners) / 3.0 - oy
            # A face right over the apex has no bearing of its own worth
            # trusting, so it goes with the slice the dome is facing.
            bearing = (math.atan2(cy, cx) if (cx * cx + cy * cy) > 1e-6
                       else angle)
            dx, dy = drawn_apart(slice_of(bearing))
            corners = [(x + dx, y + dy, z) for x, y, z in corners]
        lit = index < lit_faces
        if lit:
            # The shell itself, dark, so the lit face has something to sit in.
            b.triangle(*corners, (0.16, 0.16, 0.18), alpha=1.0,
                       mat_id=MAT_PLAIN)
            centre = [sum(c[axis] for c in corners) / 3.0 for axis in range(3)]
            inset = [
                tuple(centre[axis] + (c[axis] - centre[axis]) * (1.0 - AD_INSET)
                      for axis in range(3))
                for c in corners
            ]
            # Stand the lit face a few millimetres proud, or it z-fights with
            # the frame it is mounted in.
            lift_out = 0.012
            inset = [(x, y, z + lift_out) for x, y, z in inset]
            b.triangle(*inset, AD_TINTS[index % len(AD_TINTS)], alpha=1.0,
                       mat_id=MAT_EMISSIVE)
        else:
            # A fabric cap is not shingled, so an overridden colour drops the
            # shingle material with it -- otherwise the quilt comes out tiled.
            b.triangle(*corners, colour or SHELL_WHITE, alpha=alpha,
                       mat_id=MAT_PLAIN if colour else MAT_SHINGLE)
        count += 1

    # The rim skirt and the latches that hold it to the pad.
    skirt = seed_model.declared("shell_skirt_in") * M_PER_IN
    rim_r = m(geo.radius_in + offset) * h
    sides = geo.base_sides
    if mirror > 0:
        for index in range(sides):
            a0 = angle + math.tau * index / sides
            a1 = angle + math.tau * (index + 1) / sides
            sx, sy = drawn_apart(slice_of((a0 + a1) * 0.5))
            low0 = (ox + sx + math.cos(a0) * rim_r,
                    oy + sy + math.sin(a0) * rim_r, base - skirt)
            low1 = (ox + sx + math.cos(a1) * rim_r,
                    oy + sy + math.sin(a1) * rim_r, base - skirt)
            high0 = (low0[0], low0[1], base)
            high1 = (low1[0], low1[1], base)
            mid = (a0 + a1) * 0.5
            b.quad(low0, low1, high1, high0,
                   (math.cos(mid), math.sin(mid), 0.0), (0.78, 0.79, 0.77),
                   alpha, MAT_SHINGLE)
        latches = seed_model.shell_plan(geo).latches
        for point, bearing in _ring((ox, oy, base - skirt * 0.45),
                                    rim_r + 0.03, latches, angle):
            sx, sy = drawn_apart(slice_of(bearing))
            box(b, (point[0] + sx, point[1] + sy, point[2]),
                (0.07, 0.07, 0.16), STEEL, MAT_METAL)
    return count


# ----------------------------------------------------------------------
# The crane that moves a dome around the park
# ----------------------------------------------------------------------

@dataclass(frozen=True)
class Crane:
    """A yacht crane, in metres: where it stands and where it is pointed."""

    origin: tuple[float, float] = (0.0, 0.0)
    height: float = 9.5
    reach: float = 11.0
    bearing_deg: float = 0.0
    hook_drop: float = 6.2
    carrying: bool = False


def crane_hook(crane: Crane) -> tuple[float, float, float]:
    """Where the hook hangs. The park uses this to park a shell under it."""
    angle = math.radians(crane.bearing_deg)
    return (crane.origin[0] + math.cos(angle) * crane.reach,
            crane.origin[1] + math.sin(angle) * crane.reach,
            crane.height - crane.hook_drop)


def build_crane(b: MeshBuilder, crane: Crane, ground_z: float = 0.0) -> None:
    """A tower, a slewing boom and a hook block on a fall of wire.

    Same idea as the travel lift in a boatyard, minus the slings: a dome is
    picked up from the top, by the ring laminated into its shell, because that
    is the one place on it that is designed to take the whole weight.
    """
    ox, oy = crane.origin
    angle = math.radians(crane.bearing_deg)
    dx, dy = math.cos(angle), math.sin(angle)

    # Base and tower.
    b.cylinder((ox, oy, ground_z), (ox, oy, ground_z + 0.35), 1.65, 20,
               (0.55, 0.56, 0.58), mat_id=MAT_CONCRETE)
    b.cylinder((ox, oy, ground_z + 0.35), (ox, oy, ground_z + crane.height),
               0.42, 12, (0.92, 0.66, 0.16), mat_id=MAT_METAL)
    # Lattice, so the tower reads as a structure at a distance.
    for index in range(6):
        low = ground_z + 0.6 + index * (crane.height - 1.2) / 6.0
        high = low + (crane.height - 1.2) / 6.0
        for sign in (-1.0, 1.0):
            b.cylinder((ox - 0.40 * sign, oy - 0.40, low),
                       (ox + 0.40 * sign, oy + 0.40, high), 0.045, 6,
                       (0.80, 0.58, 0.14), mat_id=MAT_METAL)

    top = ground_z + crane.height
    # Slewing head and the boom out to the hook.
    b.cylinder((ox, oy, top), (ox, oy, top + 0.40), 0.60, 14, DARK_STEEL,
               mat_id=MAT_METAL)
    tip = (ox + dx * crane.reach, oy + dy * crane.reach, top + 0.20)
    b.cylinder((ox, oy, top + 0.20), tip, 0.22, 10, (0.92, 0.66, 0.16),
               mat_id=MAT_METAL)
    # Counter-jib, so it is not a crane that falls over.
    tail = (ox - dx * crane.reach * 0.42, oy - dy * crane.reach * 0.42,
            top + 0.20)
    b.cylinder((ox, oy, top + 0.20), tail, 0.18, 10, (0.86, 0.60, 0.15),
               mat_id=MAT_METAL)
    box(b, (tail[0], tail[1], tail[2] - 0.30), (1.0, 0.9, 0.7), DARK_STEEL,
        MAT_CONCRETE)

    # Pendant stays from the head to the boom, which is what holds it up.
    b.cylinder((ox, oy, top + 1.30), tip, 0.035, 6, (0.30, 0.31, 0.33),
               mat_id=MAT_METAL)
    b.cylinder((ox, oy, top), (ox, oy, top + 1.40), 0.13, 8, DARK_STEEL,
               mat_id=MAT_METAL)

    # The fall of wire, the hook block, and the hook itself.
    hook = crane_hook(crane)
    hook = (hook[0], hook[1], ground_z + hook[2])
    b.cylinder(tip, (hook[0], hook[1], hook[2] + 0.30), 0.022, 6,
               (0.24, 0.25, 0.27), mat_id=MAT_METAL)
    box(b, (hook[0], hook[1], hook[2] + 0.18), (0.30, 0.22, 0.34), DARK_STEEL,
        MAT_METAL)
    b.cylinder((hook[0], hook[1], hook[2] - 0.05),
               (hook[0], hook[1], hook[2] + 0.02), 0.10, 10,
               (0.86, 0.72, 0.22) if crane.carrying else STEEL,
               mat_id=MAT_METAL)


# ----------------------------------------------------------------------
# The highway an advertiser seed is parked beside
# ----------------------------------------------------------------------

def build_highway(b: MeshBuilder, y: float, length: float, *,
                  width: float = 11.0, z: float = 0.02,
                  lanes: int = 4) -> None:
    """A road running past the site, and the reason an advertiser pays rent.

    Billboard space is not a property of a dome. It is a property of a dome
    that is beside something people drive along, and a park that draws the
    domes but not the road is quietly assuming the expensive half.
    """
    half = length * 0.5
    b.quad((-half, y - width * 0.5, z), (half, y - width * 0.5, z),
           (half, y + width * 0.5, z), (-half, y + width * 0.5, z),
           (0.0, 0.0, 1.0), ASPHALT, mat_id=MAT_PLAIN)
    # Lane lines: dashed between lanes, solid at the edges.
    for index in range(1, lanes):
        lane_y = y - width * 0.5 + width * index / lanes
        if index == lanes // 2:
            b.quad((-half, lane_y - 0.12, z + 0.005),
                   (half, lane_y - 0.12, z + 0.005),
                   (half, lane_y + 0.12, z + 0.005),
                   (-half, lane_y + 0.12, z + 0.005),
                   (0.0, 0.0, 1.0), STRIPE, mat_id=MAT_PLAIN)
            continue
        dash, gap = 3.0, 4.5
        x = -half
        while x < half:
            end = min(x + dash, half)
            b.quad((x, lane_y - 0.08, z + 0.005), (end, lane_y - 0.08, z + 0.005),
                   (end, lane_y + 0.08, z + 0.005), (x, lane_y + 0.08, z + 0.005),
                   (0.0, 0.0, 1.0), (0.86, 0.86, 0.84), mat_id=MAT_PLAIN)
            x += dash + gap
    # Shoulder and a guard rail on the park side.
    rail_y = y + width * 0.5 + 1.1
    for x in np.arange(-half, half, 4.0):
        b.cylinder((float(x), rail_y, z), (float(x), rail_y, z + 0.72), 0.06,
                   6, DARK_STEEL, mat_id=MAT_METAL)
    b.quad((-half, rail_y - 0.05, z + 0.58), (half, rail_y - 0.05, z + 0.58),
           (half, rail_y - 0.05, z + 0.78), (-half, rail_y - 0.05, z + 0.78),
           (0.0, -1.0, 0.0), (0.70, 0.71, 0.72), mat_id=MAT_METAL)


# ----------------------------------------------------------------------
# One whole seed, standing on a pad
# ----------------------------------------------------------------------

def build_seed(b: MeshBuilder, placement: SeedPlacement, *,
               frame: bool = True, column: bool = True,
               polyps: bool = True, stove: bool = True,
               analysis: bool = False, panels: float = 1.0) -> int:
    """Everything that arrives with a seed dome, in one call.

    ``panels`` is how much of the fit-out's panel set is seated: 0 leaves
    every bay blank, 1 seats them all. It is a number rather than a flag so a
    film can swap a gym into a guest house on camera."""
    geo = geometry()
    triangles = 0
    if frame:
        triangles += build_seed_frame(b, placement, analysis=analysis)
        if panels > 0.0:
            triangles += build_panels(b, placement, reveal=panels)

    apex = apex_m(placement.shape)
    radius = footprint_radius_m(placement.shape)
    inverted = SHAPES.get(placement.shape, SHAPES["hemisphere"])[2] < 0

    lift = base_lift_m(placement.shape)
    if placement.shape == "treed":
        build_tree_support(b, placement.origin, placement.base_z, radius, lift)
    if frame and not inverted:
        build_open_floor(b, placement.origin, placement.base_z + lift,
                         radius * 0.97)
    if placement.shape == "buried":
        # Heaped after the dome, so the soil reads as being against it.
        build_berm(b, placement.origin, placement.base_z, radius,
                   apex * 0.62)

    if column and not inverted:
        build_utility_column(b, placement.origin, placement.base_z + lift,
                             apex, face_deg=placement.heading_deg)
        build_seal_cap(b, placement.origin, placement.base_z + lift, apex,
                       open_cap=placement.shell_open)
        if "camera_ring" in placement.spec.modules and not placement.shell_open:
            build_camera_ring(b, placement.origin, placement.base_z + lift,
                              apex)

    if placement.show_shell:
        lit = (sum(f.count for f in geo.faces)
               if placement.fitout == "advertiser" else 0)
        lift = 2.6 if placement.shell_open else 0.0
        triangles += build_seed_shell(b, placement, lift=lift, lit_faces=lit,
                                      alpha=0.62 if placement.shell_open else 1.0)

    if polyps and not inverted:
        spec = placement.spec
        bearings = polyp_bearings(placement.polyp_count,
                                  start_deg=placement.heading_deg + 34.0)
        filled = min(len(spec.modules), POLYP_SLOTS)
        for bearing in bearings:
            build_polyp(b, placement.origin, placement.base_z + lift, radius,
                        bearing, modules=filled, lit=True)
            build_exterior_routing(b, placement.origin, placement.base_z + lift,
                                   apex, radius, bearing,
                                   drop_to=placement.base_z + 1.0)

    if stove and not inverted and "sauna" not in placement.fitout:
        offset = radius * 0.58
        angle = math.radians(placement.heading_deg + 150.0)
        centre = (placement.origin[0] + math.cos(angle) * offset,
                  placement.origin[1] + math.sin(angle) * offset)
        build_stove_dome(b, centre, placement.base_z + lift + 0.04,
                         radius=0.52, flue_top=apex * 0.94)
    return triangles


def seed_mesh(placement: SeedPlacement | None = None, **kwargs) -> Mesh:
    """One seed dome as a standalone mesh, for a still or a film."""
    b = MeshBuilder()
    build_seed(b, placement or SeedPlacement(), **kwargs)
    return b.build()


# ----------------------------------------------------------------------
# Proof
# ----------------------------------------------------------------------

def _validate_deck_stages() -> None:
    """The platform has to actually accumulate, stage by stage."""
    import pad_deck

    seen = 0
    for stage in DECK_STAGES[:-1]:
        builder = MeshBuilder()
        build_deck_stage(builder, stage)
        count = len(builder.build().vertices)
        assert count > seen, (stage, count, seen)
        seen = count

    # Sealing is a colour, not a course: it must not add geometry, and it
    # must change what is there.
    boards = MeshBuilder()
    build_deck_stage(boards, "boards")
    sealed = MeshBuilder()
    build_deck_stage(sealed, "sealed")
    assert len(sealed.build().vertices) == len(boards.build().vertices)
    assert not np.array_equal(sealed.build().vertices,
                              boards.build().vertices), (
        "sealing the deck changed nothing on screen")

    # Half a stage has to be half-built, or the film cannot show boards
    # going down one at a time.
    half = MeshBuilder()
    build_deck_stage(half, "boards", partial=0.5)
    assert 0 < len(half.build().vertices) < len(boards.build().vertices)

    # And the thing drawn has to be the thing priced.
    assert len(DECK_STAGES) >= len(set(
        line.label.split(",")[0] for line in pad_deck.deck("blocks").lines)) - 2


def _validate_float_rig() -> None:
    """The saddles have to be clear above the hanger, and the caps apart.

    Both of these were wrong in a render and neither was wrong in a number.
    The three legs came out near horizontal and read as one clothesline
    strung between two trees, and a stack of caps 1.6 inches apart on a
    116-inch radius read as one dome, which is the opposite of what the
    chapter using it claims.
    """
    import soft_shell

    hang = mast_top_m() + 3.4
    spots = float_tree_positions(footprint_radius_m("hemisphere"))
    assert len(spots) == 2, spots
    saddle_z = (hang + 6.4) * 0.80
    run = max(abs(x) for x, _ in spots)
    assert saddle_z - hang > 1.8, (
        f"the saddles are only {saddle_z - hang:.2f} m above the hanger; the "
        f"cables will draw as one horizontal line")
    assert (saddle_z - hang) / run > 0.25, (
        "the cable legs are too shallow to read as three")

    # And the growth the cap chapter shows is the model's, not a guess.
    added = [soft_shell.soft_shell(n).added_r for n in range(4)]
    assert added[0] == 0.0, added
    assert all(b > a for a, b in zip(added, added[1:])), added
    assert added[3] < 8.0, ("a three-layer stack should be inches, not feet; "
                            f"got {added[3]:.1f} in")


def validate_seed_world() -> None:
    _validate_deck_stages()
    _validate_float_rig()
    """Everything this module draws has to be there and be the right size."""
    seed_model.validate_seed_model()
    geo = geometry()

    frame = MeshBuilder()
    triangles = build_seed_frame(frame, SeedPlacement())
    assert triangles > 2000, triangles
    mesh = frame.build()
    assert mesh.vertices.shape[1] == 11, mesh.vertices.shape

    # No frame colour may arrive with an empty blue channel, or that part of
    # the dome renders green under the sky. Checked here rather than looked
    # at, because it is the kind of thing that only shows up in a still.
    rgb = mesh.vertices[:, 6:9]
    assert float((rgb[:, 2] - BLUE_FLOOR * rgb[:, 0:2].mean(axis=1)).min()) \
        > -1e-6

    # And no marker colour may survive into the park view, or a house on a
    # pad is wearing its own assembly diagram.
    for source, _target in ANALYSIS_COLOURS:
        hit = np.all(np.abs(rgb - np.asarray(source)) < 0.03, axis=1)
        assert not hit.any(), source
    # With analysis on, they have to come back.
    marked = MeshBuilder()
    build_seed_frame(marked, SeedPlacement(), analysis=True)
    marked_rgb = marked.build().vertices[:, 6:9]
    for source, _target in ANALYSIS_COLOURS:
        hit = np.all(np.abs(marked_rgb[:, 0:2]
                            - np.asarray(source[0:2])) < 0.03, axis=1)
        assert hit.any(), source

    # The drawn frame has to be the measured dome. If these drift, the park
    # is showing a building the quote does not price.
    width = float(mesh.vertices[:, 0].max() - mesh.vertices[:, 0].min())
    top = float(mesh.vertices[:, 2].max())
    expected_width = geo.diameter_ft / FT_PER_M
    assert abs(width - expected_width) < 0.35, (width, expected_width)
    assert abs(top - m(geo.height_in)) < 0.35, (top, m(geo.height_in))
    assert float(mesh.vertices[:, 2].min()) > -0.30

    # Every shape has to stand on the ground and stay on its pad.
    for shape in SHAPES:
        spec = next((f for f in seed_model.fitouts() if f.shape == shape), None)
        if spec is None:
            continue
        builder = MeshBuilder()
        build_seed(builder, SeedPlacement(fitout=spec.key))
        built = builder.build()
        assert len(built.vertices) > 1000, (shape, len(built.vertices))
        assert float(built.vertices[:, 2].min()) > -1.0, shape

    # The column must reach the apex and out the top of it, or the interface
    # boundary is a drawing of a ceiling.
    column = MeshBuilder()
    apex = apex_m("hemisphere")
    build_utility_column(column, (0.0, 0.0), 0.0, apex)
    build_seal_cap(column, (0.0, 0.0), 0.0, apex)
    built = column.build()
    assert float(built.vertices[:, 2].max()) > apex + 0.25, (
        float(built.vertices[:, 2].max()), apex)

    # A polyp has to sit outside the footprint. That is the entire claim,
    # so the body has to clear the rim rather than lap over it.
    polyp = MeshBuilder()
    radius = footprint_radius_m("hemisphere")
    build_polyp(polyp, (0.0, 0.0), 0.0, radius, 0.0)
    built = polyp.build()
    assert float(built.vertices[:, 0].max()) > radius, (
        float(built.vertices[:, 0].max()), radius)
    outside = built.vertices[built.vertices[:, 0] >= radius + 0.09]
    assert len(outside) > 50, len(outside)
    # ...while still reaching back under the rim, or it is a shed, not a port.
    inside = built.vertices[built.vertices[:, 0] < radius]
    assert len(inside) > 0

    # The floor is an annulus: it must leave the port in the middle open.
    floor = MeshBuilder()
    build_open_floor(floor, (0.0, 0.0), 0.0, radius)
    built = floor.build()
    flat = built.vertices[np.abs(built.vertices[:, 2] - 0.02) < 1e-6]
    reach = np.hypot(flat[:, 0], flat[:, 1])
    assert float(reach.min()) > 0.4, float(reach.min())

    # The shell must stand off the frame, not through it.
    shell = MeshBuilder()
    count = build_seed_shell(shell, SeedPlacement(show_shell=True))
    assert count == sum(face.count for face in geo.faces), count
    built = shell.build()
    shell_top = float(built.vertices[:, 2].max())
    assert shell_top > m(geo.height_in), (shell_top, m(geo.height_in))

    # A treed dome has to be off the ground, and a bermed one has to have
    # soil against it. Both are the point of the seed they belong to.
    treed = MeshBuilder()
    build_seed(treed, SeedPlacement(fitout="treehouse"))
    built = treed.build()
    frame_only = MeshBuilder()
    build_seed_frame(frame_only, SeedPlacement(fitout="treehouse"))
    assert float(frame_only.build().vertices[:, 2].min()) \
        > base_lift_m("treed") * 0.8
    assert float(built.vertices[:, 2].min()) < 0.2, "the tree reaches the ground"

    bermed = MeshBuilder()
    build_seed(bermed, SeedPlacement(fitout="bunker"))
    built = bermed.build()
    reach = np.hypot(built.vertices[:, 0], built.vertices[:, 1])
    assert float(reach.max()) > footprint_radius_m("buried") * 1.5

    # Every seam choice has to draw, and they must not all draw the same
    # thing -- otherwise the option is a label on nothing.
    counts = {}
    for seam in SEAMS:
        builder = MeshBuilder()
        build_seed_frame(builder, SeedPlacement(seam=seam))
        counts[seam] = len(builder.build().vertices)
    assert counts["none"] < counts["rigid"], counts
    assert counts["none"] < counts["hose"], counts
    assert counts["hose"] != counts["rigid"], counts

    # The camera ring belongs to the seed that has the module, and stands on
    # top of the cap rather than inside the dome.
    with_camera = MeshBuilder()
    build_seed(with_camera, SeedPlacement(fitout="home"))
    without = MeshBuilder()
    build_seed(without, SeedPlacement(fitout="stem_cell"))
    high = float(with_camera.build().vertices[:, 2].max())
    plain = float(without.build().vertices[:, 2].max())
    assert high > plain, (high, plain)

    crane = MeshBuilder()
    build_crane(crane, Crane())
    assert len(crane.build().vertices) > 200

    road = MeshBuilder()
    build_highway(road, y=-40.0, length=160.0)
    assert len(road.build().vertices) > 100


if __name__ == "__main__":
    validate_seed_world()
    geo = geometry()
    print(f"seed dome: {geo.diameter_ft:.2f} ft across, "
          f"{geo.height_ft:.2f} ft tall, "
          f"{geo.floor_decagon_sqft:.0f} sq ft of floor")
    mesh = seed_mesh()
    print(f"  drawn as {len(mesh.vertices):,} vertices, "
          f"{len(mesh.opaque) // 3:,} opaque triangles")
    for spec in seed_model.fitouts():
        print(f"  {spec.label:<18} {spec.shape:<11} "
              f"pad {pad_diameter_ft(spec.shape):>5.1f} ft  "
              f"{spec.polyps} panel(s)")


# ----------------------------------------------------------------------
# The bay: what actually closes one triangle
# ----------------------------------------------------------------------

def build_bay_cutaway(b: MeshBuilder, origin, base_z: float, *,
                      side_m: float = 1.83, explode: float = 0.0) -> None:
    """One triangular bay, taken apart, at a size a camera can read.

    Drawn flat and face-on rather than in the dome, because the thing being
    explained is a *stack* and a stack seen edge-on at three metres is a
    smudge. From the inside out: the three wedge members with the lip their
    shape leaves, the inner panel that drops onto that lip, the cavity, the
    outer panel that compression-fits from outside, and the shell that lands
    on the frame rather than on any of it.

    ``explode`` separates the layers along the bay's normal. Zero is the
    assembled wall.
    """
    ox, oy = origin
    depth = m(seed_model.seed_geometry().member_depth_in)
    width = m(seed_model.seed_geometry().member_width_in)
    lip = m(seed_model.declared("panel_lip_in"))
    half = side_m * 0.5
    height = side_m * math.sqrt(3.0) / 2.0

    corners = [
        (ox - half, oy - height / 3.0),
        (ox + half, oy - height / 3.0),
        (ox, oy + height * 2.0 / 3.0),
    ]

    def triangle_at(z, inset, colour, mat, alpha=1.0):
        centre = (sum(c[0] for c in corners) / 3.0,
                  sum(c[1] for c in corners) / 3.0)
        pts = [(centre[0] + (x - centre[0]) * inset,
                centre[1] + (y - centre[1]) * inset, z) for x, y in corners]
        b.triangle(*pts, colour, alpha=alpha, mat_id=mat)

    # The three members, laid on the bay's edges, each a real wedge section.
    for index in range(3):
        start = corners[index]
        end = corners[(index + 1) % 3]
        b.cylinder((start[0], start[1], base_z + depth * 0.5),
                   (end[0], end[1], base_z + depth * 0.5),
                   width * 0.5, 8, (0.60, 0.38, 0.206), mat_id=MAT_WOOD)
        # The lip: a thin ledge on the inward face, which is what the inner
        # panel lands on and the reason nothing here needs a screw.
        b.cylinder((start[0], start[1], base_z + lip * 0.5),
                   (end[0], end[1], base_z + lip * 0.5),
                   width * 0.62, 6, (0.72, 0.52, 0.30), mat_id=MAT_WOOD)

    # 1 inner panel, on the lip.
    triangle_at(base_z + lip + explode * 0.0, 0.86, PANEL_POLY, MAT_PLAIN)
    # 2 the cavity -- drawn as a translucent slab so it reads as a space.
    triangle_at(base_z + depth * 0.5 + explode * 1.0, 0.86,
                (0.35, 0.62, 0.78), MAT_GLASS, alpha=0.30)
    # 3 outer panel, compression fit from outside.
    triangle_at(base_z + depth + explode * 2.0, 0.86, (0.62, 0.68, 0.72),
                MAT_PLAIN)
    # 4 the shell, landing on the frame.
    triangle_at(base_z + depth + m(seed_model.declared("shell_standoff_in"))
                + explode * 3.0, 1.06, SHELL_WHITE, MAT_SHINGLE)


# ----------------------------------------------------------------------
# The seam channel, used as a duct
# ----------------------------------------------------------------------

DUCT_AIR = (0.42, 0.86, 1.00)
DUCT_WATER = (0.28, 0.54, 0.95)


def build_seam_ducts(b: MeshBuilder, placement: SeedPlacement, *,
                     flow: float = 0.0, water: bool = False) -> int:
    """The seam network, lit up along every interior edge.

    Every edge two panels share is a channel, because two sawn faces meeting
    at a dihedral angle do not close flush. This draws that network as what
    it is once it is capped: a duct that already reaches every vertex of the
    building without anybody routing it.

    ``flow`` 0..1 runs a bead along each channel, so the direction reads.
    """
    from two_v_demo import raw_wedge_bridge

    sim = raw_wedge_bridge.simulator()
    topo = sim.build_2v_hemisphere(seed_model.SEED_LONG_EDGE_IN)
    h, v, mirror = SHAPES.get(placement.shape, SHAPES["hemisphere"])
    ox, oy = placement.origin
    angle = math.radians(placement.heading_deg)
    cos, sin = math.cos(angle), math.sin(angle)
    base = placement.base_z + base_lift_m(placement.shape)
    colour = DUCT_WATER if water else DUCT_AIR

    def place(point):
        x, y = point[0] * M_PER_IN * h, point[1] * M_PER_IN * h
        z = point[2] * M_PER_IN * v * mirror
        return (ox + x * cos - y * sin, oy + x * sin + y * cos, base + z)

    drawn = 0
    for key, edge in topo.edges.items():
        if edge.is_base:
            continue
        start = place(topo.vertices[key[0]])
        end = place(topo.vertices[key[1]])
        b.cylinder(start, end, 0.045, 6, colour, mat_id=MAT_EMISSIVE)
        drawn += 1
        if flow <= 0.0:
            continue
        # One bead per channel, running start to end, so the direction of
        # the air is a thing you can see rather than a thing you are told.
        t = (flow + (key[0] * 0.13 + key[1] * 0.07)) % 1.0
        bead = tuple(start[i] + (end[i] - start[i]) * t for i in range(3))
        b.sphere(bead, 0.085, (1.0, 0.98, 0.86), mat_id=MAT_EMISSIVE,
                 rings=3, sides=6)

    # The vertices are junctions, and a junction is where you tap a network.
    for index, point in enumerate(topo.vertices):
        if point[2] < 1.0e-6:
            continue
        b.sphere(place(point), 0.075, (0.92, 0.94, 0.98), mat_id=MAT_METAL,
                 rings=3, sides=6)
    return drawn


# ----------------------------------------------------------------------
# Panels: the thing that makes the frame a particular building
# ----------------------------------------------------------------------

PANEL_LOOK: dict[str, tuple[tuple[float, float, float], int, float]] = {
    # key -> (colour, shader material, alpha)
    "blank":       ((0.70, 0.72, 0.74), MAT_PLAIN, 1.00),
    "window":      ((0.52, 0.74, 0.86), MAT_GLASS, 0.42),
    "vent_window": ((0.46, 0.70, 0.84), MAT_GLASS, 0.46),
    "skylight":    ((0.62, 0.82, 0.92), MAT_GLASS, 0.38),
    "door":        ((0.40, 0.29, 0.20), MAT_WOOD, 1.00),
    "bay_door":    ((0.34, 0.36, 0.40), MAT_METAL, 1.00),
    "louvre":      ((0.55, 0.57, 0.60), MAT_METAL, 1.00),
    "exhaust":     ((0.42, 0.44, 0.48), MAT_METAL, 1.00),
    "solar":       ((0.10, 0.12, 0.22), MAT_SOLAR, 1.00),
    "stove_flue":  ((0.30, 0.31, 0.33), MAT_METAL, 1.00),
    "acoustic":    ((0.32, 0.30, 0.34), MAT_CANVAS, 1.00),
    "mirror":      ((0.80, 0.86, 0.90), MAT_MIRROR, 1.00),
    "serving":     ((0.62, 0.55, 0.36), MAT_WOOD, 1.00),
}
"""How each snap-in panel reads on screen.

One colour per kind, because the whole argument is that you can look at a
dome and see what it is for. A gym is mirrors and deadening; a workshop is
skylights and louvres; a garage is one big grey opening at the bottom."""


# How many base bays one open-bay door replaces. The number comes from
# seed_model.PANELS["bay_door"], which prices exactly that many.
BAY_DOOR_FACES = 3


def topo_base_count(topo) -> int:
    """How many faces sit on the base ring, found rather than assumed."""
    heights = [float(face.center[2]) for face in topo.faces]
    floor = min(heights)
    span = max(1e-6, max(heights) - floor)
    return sum(1 for h in heights if (h - floor) / span < 0.25)


def _face_height_order(topo) -> list[int]:
    """Face indices, lowest first. Doors go low, skylights go high."""
    return sorted(range(len(topo.faces)),
                  key=lambda i: float(topo.faces[i].center[2]))


def panel_assignment(mix: dict, topo) -> dict:
    """Decide which bay gets which panel, sensibly rather than at random.

    Openings go to the base ring, because that is where the wall is nearly
    upright and where a person walks in. Skylights go to the top ring,
    because on a dome the upper ring *is* the roof. Everything else fills in
    around them from the bottom up, so a mirror ends up at eye level and not
    over your head.
    """
    order = _face_height_order(topo)
    taken: dict[int, str] = {}
    low = [i for i in order]
    high = list(reversed(order))

    def take(pool, count, key):
        given = 0
        for index in pool:
            if given >= count:
                break
            if index in taken:
                continue
            taken[index] = key
            given += 1

    # The open bay is the one panel that is not one panel. Its price says
    # "three base bays taken out and replaced by one wide opening", so it has
    # to be three faces on screen as well -- and *next to each other*, or it
    # is three separate doors and the picture says something the quote does
    # not. Height alone cannot order them: every face on the base ring sits
    # at the same height, so the tie has to be broken by where they stand
    # around the dome.
    if mix.get("bay_door"):
        ring = sorted(low[:topo_base_count(topo)],
                      key=lambda i: math.atan2(float(topo.faces[i].center[1]),
                                               float(topo.faces[i].center[0])))
        run = mix["bay_door"] * BAY_DOOR_FACES
        take(ring + low, run, "bay_door")
    for key in ("door", "serving"):
        if mix.get(key):
            take(low, mix[key], key)
    for key in ("skylight", "solar", "stove_flue", "exhaust"):
        if mix.get(key):
            take(high, mix[key], key)
    for key, count in mix.items():
        if key in taken.values() and key in ("bay_door", "door", "serving",
                                             "skylight", "solar",
                                             "stove_flue", "exhaust"):
            continue
        if count:
            take(low, count, key)
    return taken


def build_panels(b: MeshBuilder, placement: SeedPlacement,
                 mix: dict | None = None, *, reveal: float = 1.0) -> int:
    """Drop the fit-out's panels into the bays that carry them.

    ``reveal`` swaps them in over time: at zero every bay is blank, at one
    every panel in the mix is seated. That is the shot the whole "stem cell"
    idea needs -- one frame, and the building becoming a different building
    while you watch.
    """
    from two_v_demo import raw_wedge_bridge

    if mix is None:
        mix = placement.spec.panels
    sim = raw_wedge_bridge.simulator()
    topo = sim.build_2v_hemisphere(seed_model.SEED_LONG_EDGE_IN)
    taken = panel_assignment(mix, topo)
    if not taken:
        return 0

    h, v, mirror = SHAPES.get(placement.shape, SHAPES["hemisphere"])
    ox, oy = placement.origin
    angle = math.radians(placement.heading_deg)
    cos, sin = math.cos(angle), math.sin(angle)
    offset = geometry().member_depth_in * 0.45
    base = placement.base_z + base_lift_m(placement.shape)
    if mirror < 0:
        base += m(geometry().height_in) * v

    def place(point, scale):
        x, y = point[0] * M_PER_IN * h * scale, point[1] * M_PER_IN * h * scale
        z = point[2] * M_PER_IN * v * mirror * scale
        return (ox + x * cos - y * sin, oy + x * sin + y * cos, base + z)

    shown = sorted(taken)[:max(0, int(round(len(taken) * clamp01(reveal))))]
    scale = (geometry().radius_in + offset) / geometry().radius_in
    drawn = 0
    for index in shown:
        key = taken[index]
        colour, mat, alpha = PANEL_LOOK.get(key, PANEL_LOOK["blank"])
        points = topo.vertices[list(topo.faces[index].vertices)]
        corners = [place(points[i], scale) for i in range(3)]
        centre = [sum(c[axis] for c in corners) / 3.0 for axis in range(3)]
        inset = [tuple(centre[axis] + (c[axis] - centre[axis]) * 0.90
                       for axis in range(3)) for c in corners]
        b.triangle(*inset, colour, alpha=alpha, mat_id=mat)
        drawn += 1
    return drawn


def clamp01(value: float) -> float:
    return max(0.0, min(1.0, float(value)))
