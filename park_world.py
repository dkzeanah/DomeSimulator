"""The dome park as geometry: pads, hookups, and the site they sit on.

A pad is a foundation plus services, and this is what one looks like. The
numbers -- how big a pad is, which domes fit it, what it cost to build -- all
come from :mod:`park_model`; nothing here decides a figure.

Built with the Dome Creator's own :class:`mesh_builder.MeshBuilder`, so the
park renders through the same shader as the domes that stand on it. That is
what keeps a dome on a pad looking like one scene rather than two programs
sharing a window.

The domes themselves are *not* merged into this mesh. They are the Creator's
own buildings, drawn separately with their own model matrix, exactly as the
films draw them. This module builds everything that is not a dome.
"""

from __future__ import annotations

import math
from dataclasses import dataclass, field

import numpy as np

import materials
import park_model
import seed_model
import seed_world
from materials import (
    MAT_CONCRETE,
    MAT_DECK,
    MAT_EMISSIVE,
    MAT_GRASS,
    MAT_GRAVEL,
    MAT_METAL,
    MAT_PLAIN,
    MAT_WOOD,
)
from mesh_builder import Mesh, MeshBuilder

FT_PER_M = 3.280839895


def ft(feet: float) -> float:
    """Feet to metres. park_model speaks feet; the renderer speaks metres."""
    return feet / FT_PER_M


# ----------------------------------------------------------------------
# What a deck is made of
# ----------------------------------------------------------------------

DECK_LOOK = {
    "gravel": ((0.55, 0.53, 0.50), (0.45, 0.43, 0.40), MAT_GRAVEL, 0.10),
    "concrete": ((0.62, 0.62, 0.61), (0.52, 0.52, 0.51), MAT_CONCRETE, 0.16),
    "wood": ((0.55, 0.38, 0.22), (0.42, 0.29, 0.17), MAT_DECK, 0.34),
}
"""deck -> (top colour, side colour, shader material, height above grade)."""

STEEL = (0.58, 0.61, 0.65)
DARK_STEEL = (0.26, 0.28, 0.31)
PIPE_BLUE = (0.20, 0.35, 0.75)
CONDUIT = (0.25, 0.26, 0.29)


# ----------------------------------------------------------------------
# One pad on the ground
# ----------------------------------------------------------------------

@dataclass
class Placed:
    """One pad, where it stands, and what is parked on it."""

    pad: park_model.Pad
    origin: tuple[float, float]
    """Metres, on the site plane."""
    dome: str = ""
    """Dome Creator preset name, or empty for a vacant pad."""
    heading_deg: float = 0.0
    """Which way the rotating base is currently aimed."""
    seed: str = ""
    """A :mod:`seed_model` fit-out key, for a pad carrying a seed dome.

    A pad holds one or the other. ``dome`` is a building out of the Dome
    Creator's shipped catalogue -- somebody else's design, parked here. ``seed``
    is this shop's own product: the 2V wedge dome on a six-foot member, its
    utility column, its seal cap and its panels. They are drawn by different
    code because they are different buildings, and the park has to be able to
    show both standing on the same ground."""
    show_shell: bool = True
    """Whether the seed's removable shell is on it."""
    shell_open: bool = False
    """Shell held clear, as a crane would hold it."""
    seam: str = "hose"
    """What sits between two panels: hose, rigid or none."""

    @property
    def radius_m(self) -> float:
        return ft(self.pad.diameter_ft) / 2.0

    @property
    def occupied(self) -> bool:
        return bool(self.dome or self.seed)

    @property
    def is_seed(self) -> bool:
        return bool(self.seed)

    @property
    def label(self) -> str:
        if self.seed:
            return seed_model.fitout(self.seed).label
        return self.dome or "vacant"

    def seed_placement(self) -> "seed_world.SeedPlacement":
        """This pad's seed dome, positioned on top of the deck."""
        if not self.seed:
            raise ValueError("this pad carries no seed dome")
        return seed_world.SeedPlacement(
            fitout=self.seed,
            origin=self.origin,
            base_z=self.dome_base_z,
            heading_deg=self.heading_deg,
            show_shell=self.show_shell,
            shell_open=self.shell_open,
            seam=self.seam,
        )

    @property
    def deck_height(self) -> float:
        return DECK_LOOK[self.pad.deck][3]

    @property
    def dome_base_z(self) -> float:
        """Where a dome's floor lands: on top of the deck, lip and ring."""
        base = self.deck_height + 0.12
        if self.pad.rotating:
            base += 0.14
        return base

    def dome_config(self) -> dict:
        """The parked dome's configuration, with its own foundation removed.

        This is the whole idea in one line of code: the pad is the floor, so
        the dome that lands on it brings no foundation of its own. Leave the
        Creator's default in and every dome arrives with a second slab under
        it, sitting on top of the one the host built.
        """
        import presets

        for name, data in presets.PRESETS:
            if name == self.dome:
                config = dict(data)
                config["foundation"] = "Bare Ground"
                config["foundation_scale"] = 1.0
                return config
        raise KeyError(f"no Dome Creator preset named {self.dome!r}")


PAD_STAGES: tuple[str, ...] = (
    "graded ground",
    "deck poured",
    "acceptor rim fitted",
    "rotating base set",
    "power, water and drain up the middle",
    "utility column plumbed",
    "meter pedestal live",
    "aimed at the sun",
)
"""The order a pad gets built in, so a film can build one on camera.

The tool does not need this and neither does the arithmetic; it exists because
"a pad is just a deck and two hookups" is a claim best made by showing the deck
and the two hookups arriving one at a time."""


def build_pad(b: MeshBuilder, placed: Placed, stage: int | None = None) -> None:
    """The deck, the ring, and every service that comes up through it.

    ``stage`` draws only the steps up to and including that index of
    :data:`PAD_STAGES`; ``None`` draws the finished pad, which is what every
    existing caller gets.
    """
    def upto(step: int) -> bool:
        return stage is None or stage >= step

    pad = placed.pad
    ox, oy = placed.origin
    radius = placed.radius_m
    top_colour, side_colour, mat, height = DECK_LOOK[pad.deck]

    # -- the deck itself ------------------------------------------------
    if not upto(1):
        return
    b.disc((ox, oy, height), radius, 64, top_colour, mat_id=mat)
    b.cylinder((ox, oy, 0.0), (ox, oy, height), radius, 64, side_colour,
               mat_id=MAT_PLAIN, cap_ends=False)

    # A wooden acceptor lip: the raised edge a dome latches to, which is what
    # makes this a pad rather than a patio. Drawn as a wall and a narrow
    # annulus, never as a disc under the deck surface: two discs five
    # millimetres apart z-fight at forty metres and the deck comes out
    # mottled brown.
    if not upto(2):
        return
    lip = 0.12
    inner = radius - 0.30
    b.cylinder((ox, oy, height), (ox, oy, height + lip), radius, 64,
               (0.42, 0.30, 0.18), mat_id=MAT_WOOD, cap_ends=False)
    b.cylinder((ox, oy, height), (ox, oy, height + lip), inner, 64,
               (0.40, 0.28, 0.17), mat_id=MAT_WOOD, cap_ends=False)
    for index in range(64):
        a0 = math.tau * index / 64
        a1 = math.tau * (index + 1) / 64
        b.quad(
            (ox + math.cos(a0) * inner, oy + math.sin(a0) * inner, height + lip),
            (ox + math.cos(a1) * inner, oy + math.sin(a1) * inner, height + lip),
            (ox + math.cos(a1) * radius, oy + math.sin(a1) * radius, height + lip),
            (ox + math.cos(a0) * radius, oy + math.sin(a0) * radius, height + lip),
            (0.0, 0.0, 1.0), (0.46, 0.33, 0.20), mat_id=MAT_WOOD)
    # The deck surface sits inside the lip, on its own plane.
    b.disc((ox, oy, height + lip * 0.55), inner, 64, top_colour, mat_id=mat)

    # -- the rotating base ----------------------------------------------
    if not upto(3):
        return
    if pad.rotating:
        ring_r = radius - 0.55
        b.cylinder((ox, oy, height + lip), (ox, oy, height + lip + 0.14),
                   ring_r, 72, STEEL, mat_id=MAT_METAL, cap_ends=False)
        # Spokes, so the turning is legible when the pad is aimed elsewhere.
        for index in range(8):
            angle = math.radians(placed.heading_deg) + math.tau * index / 8
            b.cylinder(
                (ox, oy, height + lip + 0.07),
                (ox + math.cos(angle) * ring_r, oy + math.sin(angle) * ring_r,
                 height + lip + 0.07),
                0.06, 6, DARK_STEEL, mat_id=MAT_METAL)
        # Drive motor on the rim.
        angle = math.radians(placed.heading_deg)
        mx, my = ox + math.cos(angle) * ring_r, oy + math.sin(angle) * ring_r
        _box(b, (mx, my, height + lip + 0.3), (0.34, 0.30, 0.34), DARK_STEEL,
             MAT_METAL)

    # -- the hookups come up through the middle --------------------------
    if not upto(4):
        return
    _service_core(b, ox, oy, height + lip)

    if pad.utility_column and upto(5):
        _utility_column(b, ox + radius * 0.42, oy - radius * 0.42,
                        height + lip)

    # -- the pedestal at the edge, where a tenant plugs in ---------------
    if not upto(6):
        return
    px = ox - radius * 0.78
    py = oy + radius * 0.34
    _pedestal(b, px, py, height + lip, occupied=placed.occupied)

    if pad.solar_watts > 0.0 and upto(7):
        _sun_marker(b, ox, oy, height + lip + 0.2, placed.heading_deg, radius)


def _box(b: MeshBuilder, centre, size, colour, mat=MAT_PLAIN) -> None:
    """An axis-aligned box, which MeshBuilder does not offer directly."""
    cx, cy, cz = centre
    hx, hy, hz = (value / 2.0 for value in size)
    corners = {
        "bottom": ((cx - hx, cy - hy, cz - hz), (cx + hx, cy - hy, cz - hz),
                   (cx + hx, cy + hy, cz - hz), (cx - hx, cy + hy, cz - hz)),
        "top": ((cx - hx, cy - hy, cz + hz), (cx + hx, cy - hy, cz + hz),
                (cx + hx, cy + hy, cz + hz), (cx - hx, cy + hy, cz + hz)),
    }
    bottom, top = corners["bottom"], corners["top"]
    b.quad(*top, (0.0, 0.0, 1.0), colour, mat_id=mat)
    b.quad(*tuple(reversed(bottom)), (0.0, 0.0, -1.0), colour, mat_id=mat)
    # Each side gets its own outward normal. A zero normal here renders the
    # face black, because the shader has nothing to take a dot product with.
    side_normals = ((0.0, -1.0, 0.0), (1.0, 0.0, 0.0),
                    (0.0, 1.0, 0.0), (-1.0, 0.0, 0.0))
    for index in range(4):
        nxt = (index + 1) % 4
        b.quad(bottom[index], bottom[nxt], top[nxt], top[index],
               side_normals[index], colour, mat_id=mat)


def _service_core(b: MeshBuilder, ox: float, oy: float, z: float) -> None:
    """Power, water and drain arriving in the centre of the pad.

    Centre, not edge, because the dome that lands here has its floor on the
    pad: services have to come up inside the footprint or they cross the
    doorway.
    """
    b.disc((ox, oy, z + 0.02), 0.62, 24, (0.30, 0.31, 0.34),
           mat_id=MAT_METAL)
    b.cylinder((ox, oy, z), (ox, oy, z + 0.34), 0.62, 24,
               (0.24, 0.25, 0.27), mat_id=MAT_METAL, cap_ends=False)
    # Power stub, water stub, drain -- three different things, three colours.
    b.cylinder((ox - 0.22, oy, z + 0.02), (ox - 0.22, oy, z + 0.52), 0.05, 10,
               CONDUIT, mat_id=MAT_PLAIN)
    b.cylinder((ox + 0.10, oy, z + 0.02), (ox + 0.10, oy, z + 0.46), 0.04, 10,
               PIPE_BLUE, mat_id=MAT_PLAIN)
    b.cylinder((ox + 0.30, oy, z + 0.02), (ox + 0.30, oy, z + 0.30), 0.07, 10,
               (0.45, 0.46, 0.48), mat_id=MAT_PLAIN)


def _pedestal(b: MeshBuilder, x: float, y: float, z: float,
              occupied: bool) -> None:
    """The metered pedestal: what the host resells power and water through."""
    _box(b, (x, y, z + 0.55), (0.34, 0.26, 1.10), (0.32, 0.34, 0.38),
         MAT_METAL)
    # Meter face, lit green when a tenant is drawing power.
    face = (0.30, 0.90, 0.40) if occupied else (0.35, 0.36, 0.38)
    _box(b, (x, y - 0.15, z + 0.82), (0.20, 0.03, 0.14), face,
         MAT_EMISSIVE if occupied else MAT_PLAIN)
    b.cylinder((x, y, z), (x, y, z + 0.04), 0.26, 12, DARK_STEEL,
               mat_id=MAT_METAL)


def _utility_column(b: MeshBuilder, x: float, y: float, z: float) -> None:
    """Toilet, sink, shower head, outlets and drain, in one column."""
    _box(b, (x, y, z + 1.15), (0.68, 0.68, 2.30), (0.58, 0.60, 0.62),
         MAT_PLAIN)
    _box(b, (x, y - 0.35, z + 1.30), (0.42, 0.04, 1.30), (0.30, 0.32, 0.35),
         MAT_PLAIN)
    b.cylinder((x, y, z + 2.30), (x, y, z + 2.48), 0.10, 10, STEEL,
               mat_id=MAT_METAL)


def _sun_marker(b: MeshBuilder, ox: float, oy: float, z: float,
                heading_deg: float, radius: float) -> None:
    """A short arrow on the deck showing where a tracking pad is aimed."""
    angle = math.radians(heading_deg)
    tip = (ox + math.cos(angle) * radius * 0.82,
           oy + math.sin(angle) * radius * 0.82, z + 0.04)
    tail = (ox + math.cos(angle) * radius * 0.42,
            oy + math.sin(angle) * radius * 0.42, z + 0.04)
    b.cylinder(tail, tip, 0.05, 8, (1.00, 0.78, 0.25), mat_id=MAT_EMISSIVE)


# ----------------------------------------------------------------------
# Shared things the park provides
# ----------------------------------------------------------------------

def build_bathhouse(b: MeshBuilder, origin: tuple[float, float]) -> None:
    """A shared shower house, so a dome owner need carry no plumbing."""
    ox, oy = origin
    _box(b, (ox, oy, 1.40), (7.0, 4.4, 2.80), (0.74, 0.72, 0.68), MAT_PLAIN)
    # A shallow pitched roof, made of two quads.
    peak = 3.70
    left = (ox - 3.5, oy, peak)
    right = (ox + 3.5, oy, peak)
    for sign in (-1.0, 1.0):
        edge_a = (ox - 3.5, oy + sign * 2.2, 2.80)
        edge_b = (ox + 3.5, oy + sign * 2.2, 2.80)
        b.quad(edge_a, edge_b, right, left, (0.0, sign, 0.4),
               (0.36, 0.33, 0.31), mat_id=materials.MAT_SHINGLE)
    for sign in (-1.0, 1.0):
        b.triangle((ox + sign * 3.5, oy - 2.2, 2.80),
                   (ox + sign * 3.5, oy + 2.2, 2.80),
                   (ox + sign * 3.5, oy, peak),
                   (0.70, 0.68, 0.64), mat_id=MAT_PLAIN)
    # Doors, so it reads as a building people walk into.
    for offset in (-1.6, 1.6):
        _box(b, (ox + offset, oy - 2.22, 1.05), (1.0, 0.08, 2.10),
             (0.30, 0.34, 0.40), MAT_PLAIN)


def build_service_spine(b: MeshBuilder, placements: list[Placed],
                        origin: tuple[float, float]) -> float:
    """The trunk run from the service point to every pad.

    Drawn because it is the cost nobody counts: a pad is cheap, and getting
    power and water *to* the pad is not. Returns the total run in metres.
    """
    ox, oy = origin
    _box(b, (ox, oy, 1.05), (1.6, 1.0, 2.10), (0.42, 0.44, 0.47), MAT_METAL)
    if not placements:
        return 0.0

    # A trunk along the row, then a short spur up to each pad edge. Running a
    # separate line from the service point to every pad crosses the other
    # pads, which is neither how it is built nor something you want to look
    # at. Buried depth is faked by keeping it low and thin.
    z = 0.03
    xs = [p.origin[0] for p in placements]
    trunk_y = min(p.origin[1] - p.radius_m for p in placements) - 2.2
    left, right = min(xs), max(xs)
    total = 0.0

    def run(start, end, radius: float, colour) -> float:
        b.cylinder(start, end, radius, 8, colour, mat_id=MAT_PLAIN)
        return float(np.linalg.norm(np.asarray(end) - np.asarray(start)))

    total += run((ox, oy, z), (ox, trunk_y, z), 0.055, CONDUIT)
    run((ox + 0.22, oy, z), (ox + 0.22, trunk_y, z), 0.045, PIPE_BLUE)
    total += run((left, trunk_y, z), (right, trunk_y, z), 0.055, CONDUIT)
    run((left, trunk_y + 0.22, z), (right, trunk_y + 0.22, z), 0.045, PIPE_BLUE)
    for placed in placements:
        px, py = placed.origin
        edge = py - placed.radius_m
        total += run((px, trunk_y, z), (px, edge, z), 0.05, CONDUIT)
        run((px + 0.22, trunk_y + 0.22, z), (px + 0.22, edge, z), 0.04,
            PIPE_BLUE)
    return total


def build_ground(b: MeshBuilder, radius: float) -> None:
    """The site: graded ground with a service track running through it."""
    b.disc((0.0, 0.0, -0.02), radius, 72, (0.30, 0.40, 0.24),
           mat_id=MAT_GRASS)
    b.disc((0.0, 0.0, -0.01), radius * 0.16, 36, (0.52, 0.50, 0.47),
           mat_id=MAT_GRAVEL)


# ----------------------------------------------------------------------
# A whole park
# ----------------------------------------------------------------------

@dataclass
class Park:
    """A site, its pads, and what the arithmetic says about it."""

    placements: list[Placed] = field(default_factory=list)
    bathhouse: tuple[float, float] | None = None
    service_point: tuple[float, float] = (0.0, 0.0)
    crane: seed_world.Crane | None = None
    """The yard crane, when the site has one.

    A park of removable shells needs a way to lift one, and pretending
    otherwise is how a plan ends up with a building nobody can service. It
    picks a dome up from the ring in its own shell, the way a boatyard picks a
    hull up, and it is drawn because it is a real cost and a real obstacle."""
    highway_y: float | None = None
    """Where the road runs, when the site is beside one.

    Only an advertiser seed cares, and it cares completely: billboard space is
    a property of the road, not of the dome."""
    ground_radius: float | None = None
    """How far the graded ground runs, when the caller wants to say.

    The tool lets the layout decide. A film cannot: the renderer's far plane
    sits at 120 metres, so a site disc sized for a walkthrough disappears into
    clipping the moment a camera pulls back far enough to see the whole row."""

    @property
    def spine_metres(self) -> float:
        """Total trunk run to reach every pad.

        A property, not a number stashed during drawing: it is a fact about
        the layout, and asking for it should not depend on whether anybody
        has built the mesh yet.
        """
        ox, oy = self.service_point
        return sum(math.hypot(p.origin[0] - ox, p.origin[1] - oy)
                   for p in self.placements)

    @property
    def site_radius(self) -> float:
        if self.ground_radius is not None:
            return float(self.ground_radius)
        reach = max((math.hypot(*p.origin) + p.radius_m
                     for p in self.placements), default=12.0)
        if self.crane is not None:
            reach = max(reach, math.hypot(*self.crane.origin) + 4.0)
        if self.highway_y is not None:
            reach = max(reach, abs(self.highway_y) + 9.0)
        if self.bathhouse is not None:
            reach = max(reach, math.hypot(*self.bathhouse) + 5.0)
        return reach * 1.45 + 6.0

    @property
    def occupied(self) -> int:
        return sum(1 for p in self.placements if p.occupied)

    def economics(self) -> dict:
        """What this park cost and what it returns, from park_model."""
        build = sum(p.pad.build_cost for p in self.placements)
        net = sum(p.pad.year()["net"] for p in self.placements)
        gross = sum(p.pad.year()["gross"] for p in self.placements)
        return {
            "pads": len(self.placements),
            "occupied": self.occupied,
            "build_cost": build,
            "gross_year": gross,
            "net_year": net,
            "payback_years": (build / net) if net > 0 else 0.0,
            "spine_metres": self.spine_metres,
        }


def default_park(pad_count: int = 6, rotating: bool = True,
                 deck: str = "gravel") -> Park:
    """A believable starter park: a row of pads, sized to the domes that fit.

    Sizes are taken from :func:`park_model.pad_sizes`, and each pad is given
    the largest shipped dome that will actually stand on it, so the layout
    demonstrates the fit rule rather than asserting it.
    """
    sizes = park_model.pad_sizes()
    catalogue = park_model.dome_catalogue()
    chosen = [sizes[index % len(sizes)] for index in range(pad_count)]
    # Biggest at the back of the row, so nothing hides behind a lodge.
    chosen.sort()

    placements: list[Placed] = []
    cursor = 0.0
    for index, size_ft in enumerate(chosen):
        radius = ft(size_ft) / 2.0
        cursor += radius + 3.0
        fits = park_model.domes_that_fit(size_ft)
        dome = max(fits, key=lambda d: d.floor_sqft).name if fits else ""
        # Every third pad is left vacant: a park with no vacancy is a park
        # with nothing to lease, and the tool should show both states.
        if index % 3 == 2:
            dome = ""
        pad = park_model.Pad(
            diameter_ft=size_ft, deck=deck, rotating=rotating,
            utility_column=(index % 2 == 0),
            solar_watts=(park_model.solar_watts_for(
                max(fits, key=lambda d: d.floor_sqft)) if fits and dome else 0.0),
        )
        placements.append(Placed(
            pad=pad, origin=(cursor, 0.0), dome=dome,
            heading_deg=25.0 + index * 12.0))
        cursor += radius + 3.0

    span = cursor
    for placed in placements:
        placed.origin = (placed.origin[0] - span / 2.0, placed.origin[1])

    park = Park(placements=placements,
                bathhouse=(0.0, -ft(52.0)),
                service_point=(0.0, ft(34.0)))
    return park


def park_mesh(park: Park) -> Mesh:
    """Everything on the site except the domes themselves."""
    b = MeshBuilder()
    build_ground(b, park.site_radius)
    if park.highway_y is not None:
        # Shorter than the site is wide, so the tarmac stops inside the
        # grass rather than running off the edge of the world.
        seed_world.build_highway(b, park.highway_y, park.site_radius * 1.75)
    build_service_spine(b, park.placements, park.service_point)
    for placed in park.placements:
        build_pad(b, placed)
    if park.bathhouse is not None:
        build_bathhouse(b, park.bathhouse)
    if park.crane is not None:
        seed_world.build_crane(b, park.crane)
    return b.build()


def seed_pad_ft(shape: str = "hemisphere") -> float:
    """The standard pad a seed of this shape stands on.

    Rounded up to the same four-foot step every other pad in this project
    uses, so a host who built a pad for a bought dome can take a seed and a
    host who built one for a seed can take a bought dome."""
    needed = seed_world.pad_diameter_ft(shape)
    step = park_model.PAD_STEP_FT
    return math.ceil(needed / step) * step


def seed_park(pad_count: int | None = None, deck: str = "gravel",
              rotating: bool = False, highway: bool = True,
              crane: bool = True) -> Park:
    """A site of this shop's own product rather than other people's domes.

    One pad per seed in the catalogue, in the order the catalogue lists them,
    so every fit-out is standing somewhere and can be walked up to. The pads
    are all the same size because the seeds are all the same dome; that is the
    entire manufacturing argument, made by the layout instead of by a caption.
    """
    specs = [seed_model.fitout(key) for key in seed_model.FITOUT_ORDER]
    if pad_count is not None:
        specs = specs[:max(1, int(pad_count))]

    # Laid in short rows rather than one long line. Nine pads end to end is
    # a hundred and forty metres of row: from far enough back to see it all,
    # every dome is four pixels across, and from close enough to see one, it
    # is the only one on screen.
    per_row = SEEDS_PER_ROW
    spacing = 4.5
    row_gap = 9.0
    widest = max(ft(seed_pad_ft(spec.shape)) for spec in specs)

    placements: list[Placed] = []
    rows = [specs[i:i + per_row] for i in range(0, len(specs), per_row)]
    for row_index, row in enumerate(rows):
        cursor = 0.0
        row_y = row_index * (widest + row_gap)
        for index, spec in enumerate(row):
            size_ft = seed_pad_ft(spec.shape)
            radius = ft(size_ft) / 2.0
            cursor += radius + spacing
            pad = park_model.Pad(
                diameter_ft=size_ft, deck=deck, rotating=rotating,
                utility_column=True, solar_watts=0.0)
            placements.append(Placed(
                pad=pad, origin=(cursor, row_y), seed=spec.key,
                heading_deg=((row_index * per_row + index) * 24.0) % 360.0,
                show_shell=spec.key != "stem_cell"))
            cursor += radius + spacing
        # Centre each row on its own, so a short last row is not left hanging
        # off one end of the site.
        for placed in placements[-len(row):]:
            placed.origin = (placed.origin[0] - cursor / 2.0, placed.origin[1])

    span = max(abs(p.origin[0]) for p in placements) * 2.0 + widest
    depth = (len(rows) - 1) * (widest + row_gap)

    # The advertiser dome goes in the front row nearest the road, because
    # that is the only place it is worth anything. It swaps places with
    # whatever was there rather than being dropped on top of it.
    road_y = -(widest * 0.5 + 13.0) if highway else None
    advertiser = next((p for p in placements if p.seed == "advertiser"), None)
    if advertiser is not None and road_y is not None:
        front = min(p.origin[1] for p in placements)
        roadside = min((p for p in placements if p.origin[1] == front),
                       key=lambda p: abs(p.origin[0]))
        if roadside is not advertiser:
            roadside.origin, advertiser.origin = (advertiser.origin,
                                                  roadside.origin)

    yard = crane_for(placements, setback=row_gap + widest * 0.8) if crane else None
    return Park(placements=placements,
                bathhouse=(-span * 0.34, depth + widest + 14.0),
                service_point=(span * 0.30, depth + widest + 10.0),
                crane=yard,
                highway_y=road_y)


SEEDS_PER_ROW = 5
"""How many pads go in one row before the layout starts another.

A park is not a catalogue page. Nine domes in a line is a row nobody can
photograph; two short rows is a site."""

CRANE_MAX_REACH_M = 22.0
"""How far the boom goes. A crane that reaches every pad on a long row is a
crane nobody can afford, so the reach is capped and the row is served in
sections -- which is also how a boatyard does it."""


def crane_for(placements: list[Placed], setback: float = 15.0
              ) -> seed_world.Crane:
    """Stand the crane clear of the row, with its boom aimed back at it.

    Reach is solved rather than chosen: enough to cover the pads nearest it,
    capped at :data:`CRANE_MAX_REACH_M`. Setting it in the middle of the row
    would draw a crane standing where a dome has to go."""
    if not placements:
        return seed_world.Crane()
    xs = [p.origin[0] for p in placements]
    ys = [p.origin[1] for p in placements]
    stand = (sum(xs) / len(xs), max(ys) + setback)
    reach = min(CRANE_MAX_REACH_M,
                max(setback + 1.5,
                    min(math.hypot(p.origin[0] - stand[0],
                                   p.origin[1] - stand[1])
                        for p in placements) + 2.0))
    return seed_world.Crane(origin=stand, reach=reach,
                            bearing_deg=-90.0, height=10.5,
                            hook_drop=6.0)


def Crane_for(placements: list[Placed]) -> seed_world.Crane:
    """Kept so anything that already called this name still works."""
    return crane_for(placements)


# ----------------------------------------------------------------------
# Proof
# ----------------------------------------------------------------------

def validate_park_world() -> None:
    """The site must be buildable, and the pads must not overlap."""
    park_model.validate_park()

    park = default_park()
    assert len(park.placements) == 6, len(park.placements)
    assert park.occupied and park.occupied < len(park.placements), (
        "the demo park should show both leased and vacant pads")

    # No pad may overlap another, or the layout is a picture of a mistake.
    for first in range(len(park.placements)):
        for second in range(first + 1, len(park.placements)):
            a, b_ = park.placements[first], park.placements[second]
            gap = math.hypot(a.origin[0] - b_.origin[0],
                             a.origin[1] - b_.origin[1])
            assert gap > a.radius_m + b_.radius_m, (first, second, gap)

    # Every parked dome has to actually fit the pad it is standing on.
    for placed in park.placements:
        if not placed.occupied:
            continue
        dome = next(d for d in park_model.dome_catalogue()
                    if d.name == placed.dome)
        assert dome.pad_diameter_ft <= placed.pad.diameter_ft + 1e-9, (
            placed.dome, placed.pad.diameter_ft)

    mesh = park_mesh(park)
    assert len(mesh.vertices) > 5000, len(mesh.vertices)
    assert len(mesh.opaque) > 9000, len(mesh.opaque)
    assert mesh.vertices.shape[1] == 11, mesh.vertices.shape
    assert park.spine_metres > 0.0

    # The mesh must sit on the ground, not through it.
    lowest = float(mesh.vertices[:, 2].min())
    assert lowest > -0.5, lowest

    figures = park.economics()
    assert figures["build_cost"] > 0.0 and figures["net_year"] > 0.0
    assert figures["payback_years"] > 0.5

    # A seed park has to hold together on the same terms as a bought-dome one.
    seeds = seed_park()
    assert len(seeds.placements) == len(seed_model.FITOUT_ORDER)
    assert all(p.is_seed and p.occupied for p in seeds.placements)
    for first in range(len(seeds.placements)):
        for second in range(first + 1, len(seeds.placements)):
            a, b_ = seeds.placements[first], seeds.placements[second]
            gap = math.hypot(a.origin[0] - b_.origin[0],
                             a.origin[1] - b_.origin[1])
            assert gap > a.radius_m + b_.radius_m, (first, second, gap)

    # Every seed has to fit the pad the layout gave it.
    for placed in seeds.placements:
        needed = seed_world.pad_diameter_ft(placed.seed_placement().shape)
        assert needed <= placed.pad.diameter_ft + 1e-9, (placed.seed, needed)

    seed_mesh_out = park_mesh(seeds)
    assert len(seed_mesh_out.vertices) > 5000
    assert seeds.crane is not None and seeds.highway_y is not None
    # The road must not run under a pad, and neither must the crane.
    for placed in seeds.placements:
        assert abs(placed.origin[1] - seeds.highway_y) > placed.radius_m
        gap = math.hypot(placed.origin[0] - seeds.crane.origin[0],
                         placed.origin[1] - seeds.crane.origin[1])
        assert gap > placed.radius_m + 2.0, (placed.seed, gap)
    # The boom has to reach at least the nearest pad, or it is scenery.
    nearest = min(math.hypot(p.origin[0] - seeds.crane.origin[0],
                             p.origin[1] - seeds.crane.origin[1])
                  for p in seeds.placements)
    assert seeds.crane.reach >= nearest, (seeds.crane.reach, nearest)
    # And the grass has to reach past everything standing on it.
    radius = seeds.site_radius
    assert radius > abs(seeds.highway_y)
    assert radius > math.hypot(*seeds.crane.origin) + seeds.crane.reach * 0.5
    # Nothing the site draws may stand off the edge of the grass.
    assert radius > math.hypot(*seeds.bathhouse) + 5.0


if __name__ == "__main__":
    validate_park_world()
    site = default_park()
    numbers = site.economics()
    print(f"park: {numbers['pads']} pads, {numbers['occupied']} leased")
    print(f"  build      ${numbers['build_cost']:>12,.0f}")
    print(f"  gross/yr   ${numbers['gross_year']:>12,.0f}")
    print(f"  net/yr     ${numbers['net_year']:>12,.0f}")
    print(f"  payback     {numbers['payback_years']:>12.1f} years")
    print(f"  service run {numbers['spine_metres']:>12.0f} m")
    mesh = park_mesh(site)
    print(f"  mesh        {len(mesh.vertices):>12,} vertices, "
          f"{len(mesh.opaque) // 3:,} triangles")
