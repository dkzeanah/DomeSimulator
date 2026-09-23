"""The seed dome: one product, priced from its own geometry.

A *stem-cell dome* is the bare standard article this shop manufactures: a 2V
hemisphere built on a six-foot longest member out of wedge-cut framing, an
open floor that ports onto a standard pad, forty insulated triangles closed by
pop-in panels, a removable OSB-lined fibreglass shell, and one utility column
that carries power and water from the pad up through the apex. Everything a
customer adds afterwards -- a shower, a serving hatch, a wall of lit adverts --
is a *seed*: the stem cell plus a named module set.

This module is the arithmetic of that product. Nothing here is drawn and
nothing here is guessed at twice.

Three kinds of number live in this file, and they are kept apart on purpose:

**Measured.** Anything that follows from the dome's own geometry. How many
struts, how long, how much panel area, how much cavity volume, how much shell.
These come out of :mod:`geodesic_raw_wedge_dome_dihedral` -- the same solver
the Raw Wedge Dome tool draws -- and cannot be argued with.

**Borrowed.** Rates this project already declared somewhere else: resin
coverage and cloth prices from :mod:`two_v_demo.dome_costing`, R-values and
degree days from :mod:`two_v_demo.dome_performance`, the cheapest pad that is
still a pad from :mod:`park_model`. They are re-exported here with a note
saying where they came from, never retyped.

**Declared.** Prices, labour rates and margins. These are the owner's inputs,
gathered in :data:`EXTERNAL_CONSTANTS` with a unit and a reason on every one,
and overridable at runtime from ``seed_prices.json`` so the configuration
interface can change one and watch every downstream figure move.

The cross-check
---------------
Zip Tie Domes' published 2V calculator, run at a six-foot "A" strut, prints:
19' 5" across, 9' 8-1/2" tall, 35 A struts at 6' 0", 30 B struts at 5' 3-5/8",
296.1 sq ft of circular floor, 40 panels totalling 549.75 sq ft, 369.18 ft of
strut. :func:`validate_seed_model` checks this module's geometry against every
one of those figures. They agree to four decimal places, because both are the
same icosahedron.

Where this dome is *not* that dome is the member count, and it is the most
expensive fact in the file. A zip-tie dome shares one strut between two
triangles: 65 struts, 369 ft. A pinwheel wedge dome gives every triangle its
own three sticks so no end is ever mitred: 120 members, 666 ft of stock. The
method that removes the mitre costs eighty percent more wood, and the quote
says so out loud rather than quietly averaging it away.
"""

from __future__ import annotations

import json
import math
from dataclasses import dataclass, field, replace
from functools import lru_cache
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parent
OVERRIDE_PATH = ROOT / "seed_prices.json"

SQIN_PER_SQFT = 144.0
CUIN_PER_CUFT = 1728.0
OZ_PER_GALLON = 128.0
SQFT_PER_SQYD = 9.0
FT_PER_M = 3.280839895


# ----------------------------------------------------------------------
# Measured: the dome itself
# ----------------------------------------------------------------------

SEED_LONG_EDGE_IN = 72.0
"""The longest geodesic member, in inches. Six feet, and the one dimension
every other measured figure in this file follows from.

Not a preference. It is the longest stick a single bucked log section yields
two of, it is the length the published 2V calculator was run at, and it is what
makes the whole product line one cut list."""

SEED_TRUNK_DIAMETER_IN = 12.0
"""Diameter of the log the wedge members are split from.

Sets the member's depth -- pith to bark, half the diameter -- which is the
cavity behind each panel, and therefore also the offset the shell stands at.

Twelve inches, not the solver's own default of eight, and the reason is a
weight. The owner's wedges run three to four times the mass of a 2x3x6, and at
an eight-inch trunk a wedge is only 1.68 times one. Twelve gives 3.77, which is
inside the range they measured. The trunk is what sets that ratio and nothing
else does, so this is where the correction belongs -- not in a fudge factor on
the price."""

SEED_RADIAL_SPLITS = 8
"""Sectors per log: halve, halve, halve again. Gives the 45-degree wedge."""


@dataclass(frozen=True)
class FaceClass:
    """One of the two triangles a 2V hemisphere is made of."""

    name: str
    count: int
    area_sqft: float
    """Flat area of one panel."""
    perimeter_in: float
    min_width_in: float
    """Narrowest the triangle gets between parallel lines, over every
    rotation. This is what decides whether it can be cut out of a sheet."""

    @property
    def total_sqft(self) -> float:
        return self.area_sqft * self.count


@dataclass(frozen=True)
class MemberClass:
    """One family of physical stick, as the solver actually cuts it."""

    edge_type: str
    count: int
    stock_length_in: float
    """Longest length of raw stock the member is cut from."""
    axis_length_in: float

    @property
    def total_stock_ft(self) -> float:
        return self.stock_length_in * self.count / 12.0


@dataclass(frozen=True)
class SeedGeometry:
    """Everything the seed dome is, measured off the solved model."""

    long_edge_in: float
    short_edge_in: float
    radius_in: float
    height_in: float
    faces: tuple[FaceClass, ...]
    members: tuple[MemberClass, ...]
    geodesic_edges: tuple[tuple[str, int, float], ...]
    """(edge type, count, length) for the *shared* geodesic edges -- what a
    zip-tie dome would buy. Kept so the two methods can be compared."""
    base_sides: int
    vertex_count: int
    """Nodes in the frame. Every one of them is a junction of seam channels,
    so it is also a place the duct network can be tapped."""
    member_depth_in: float
    member_width_in: float
    seam_count: int
    seam_length_in: float
    """Total run of interior seam: every edge two panels share.

    Not the same as the total edge length -- the ten base edges are the rim
    and have no panel on the other side of them."""

    # -- the sizes a customer reads off a brochure ---------------------
    @property
    def diameter_ft(self) -> float:
        return self.radius_in * 2.0 / 12.0

    @property
    def height_ft(self) -> float:
        return self.height_in / 12.0

    @property
    def floor_circle_sqft(self) -> float:
        """The full circle the dome sits over."""
        return math.pi * (self.radius_in / 12.0) ** 2

    @property
    def floor_decagon_sqft(self) -> float:
        """What the frame actually stands on: the ten-sided base ring.

        The honest floor number. The circle is bigger and the dome does not
        reach it."""
        n = self.base_sides
        r = self.radius_in / 12.0
        return 0.5 * n * r * r * math.sin(2.0 * math.pi / n)

    @property
    def base_perimeter_ft(self) -> float:
        return self.base_sides * self.long_edge_in / 12.0

    # -- surfaces ------------------------------------------------------
    @property
    def panel_sqft(self) -> float:
        """Flat area of all forty triangles: what has to be closed."""
        return sum(face.total_sqft for face in self.faces)

    @property
    def spherical_sqft(self) -> float:
        """2*pi*r*h -- the sphere the panels approximate, always larger."""
        return 2.0 * math.pi * (self.radius_in / 12.0) * self.height_ft

    def shell_sqft(self, offset_in: float) -> float:
        """Faceted area of a shell standing ``offset_in`` outside the frame."""
        scale = (self.radius_in + offset_in) / self.radius_in
        return self.panel_sqft * scale * scale

    def base_perimeter_at(self, offset_in: float) -> float:
        scale = (self.radius_in + offset_in) / self.radius_in
        return self.base_perimeter_ft * scale

    # -- what goes inside the triangles --------------------------------
    @property
    def cavity_cuft(self) -> float:
        """Volume the insulation bladders fill: panel area times cavity depth.

        The cavity is the member's depth, because the bladder sits between the
        three sticks of its own triangle and is as deep as they are."""
        return self.panel_sqft * (self.member_depth_in / 12.0)

    # -- framing -------------------------------------------------------
    @property
    def member_count(self) -> int:
        return sum(m.count for m in self.members)

    @property
    def member_stock_ft(self) -> float:
        return sum(m.total_stock_ft for m in self.members)

    @property
    def member_section_in2(self) -> float:
        """Cross-section of one wedge: a 45-degree slice of the round log."""
        radius = self.member_depth_in
        return math.pi * radius * radius / SEED_RADIAL_SPLITS

    @property
    def member_volume_cuft(self) -> float:
        return self.member_stock_ft * 12.0 * self.member_section_in2 / CUIN_PER_CUFT

    @property
    def dimensional_frame_usd(self) -> float:
        """The same count of sticks, bought as 2x3x6 at the shelf price.

        The owner's own back-of-envelope: a hundred and twenty struts at three
        dollars fifty. It is in the model so the film can quote it and so the
        wedge price beside it has something to be a multiple of."""
        return self.member_count * usd_per_strut()

    @property
    def seam_length_ft(self) -> float:
        return self.seam_length_in / 12.0

    @property
    def wedge_volume_cuin(self) -> float:
        """One wedge member, in cubic inches: its section times its length."""
        return self.member_section_in2 * self.long_edge_in

    @property
    def wedge_to_strut(self) -> float:
        """How many 2x3x6 struts of wood are in one wedge member.

        The number the owner measured by weight. It is set entirely by the
        trunk diameter, and it is the thing to change if the wedges coming off
        the saw are not this heavy."""
        return self.wedge_volume_cuin / strut_volume_cuin()

    @property
    def trees_needed(self) -> float:
        """How many of the project's own example trunks the frame takes.

        Asked of :mod:`two_v_demo.wedge_geometry`, which already models one
        real tapered pine and how much usable wedge comes out of it. Answering
        it here with a guess would put a second, quieter tree in the project."""
        from two_v_demo import wedge_geometry

        per_tree = wedge_geometry.tree_yield().strut_count
        if per_tree <= 0:
            return 0.0
        # Counted in sticks rather than in cubic feet, because a tapered
        # trunk does not give up its volume evenly: the top of it makes
        # short members or none. The strut count already knows that.
        return self.member_count / float(per_tree)

    @property
    def shared_strut_ft(self) -> float:
        """What the same dome costs in stick if struts were shared, not
        pinwheeled. The zip-tie number, kept for the comparison."""
        return sum(count * length for _t, count, length in self.geodesic_edges) / 12.0

    @property
    def shared_strut_count(self) -> int:
        return sum(count for _t, count, _l in self.geodesic_edges)

    @property
    def pinwheel_stock_penalty(self) -> float:
        """How much more stock the no-mitre method needs. Above 1.0."""
        return self.member_stock_ft / self.shared_strut_ft


def _min_triangle_width_in(sides: tuple[float, float, float]) -> float:
    """Narrowest a triangle gets between two parallel lines.

    For a triangle that is its shortest altitude, and it is the number that
    decides whether the panel can be cut whole out of a sheet of anything.
    """
    a, b, c = sides
    half = (a + b + c) * 0.5
    area = math.sqrt(max(0.0, half * (half - a) * (half - b) * (half - c)))
    longest = max(sides)
    return 2.0 * area / longest


@lru_cache(maxsize=4)
def seed_geometry(long_edge_in: float = SEED_LONG_EDGE_IN,
                  trunk_diameter_in: float = SEED_TRUNK_DIAMETER_IN
                  ) -> SeedGeometry:
    """Solve the seed dome, once, out of the project's own wedge solver.

    This imports the live Raw Wedge Dome tool rather than re-deriving an
    icosahedron, so the dome this module prices is byte-for-byte the dome that
    tool draws and the fabrication package cuts.
    """
    from two_v_demo import raw_wedge_bridge

    sim = raw_wedge_bridge.simulator()
    topo = sim.build_2v_hemisphere(float(long_edge_in))
    model = raw_wedge_bridge.model(long_edge_in=float(long_edge_in),
                                   trunk_diameter_in=float(trunk_diameter_in))

    vertices = topo.vertices
    buckets: dict[str, list[tuple[float, float, float]]] = {}
    for face in topo.faces:
        points = vertices[list(face.vertices)]
        sides = (
            float(np.linalg.norm(points[1] - points[0])),
            float(np.linalg.norm(points[2] - points[1])),
            float(np.linalg.norm(points[0] - points[2])),
        )
        buckets.setdefault(face.face_type, []).append(sides)

    faces: list[FaceClass] = []
    for name in sorted(buckets):
        rows = buckets[name]
        sides = rows[0]
        half = sum(sides) * 0.5
        area_in2 = math.sqrt(max(0.0, half * (half - sides[0])
                                 * (half - sides[1]) * (half - sides[2])))
        faces.append(FaceClass(
            name=name,
            count=len(rows),
            area_sqft=area_in2 / SQIN_PER_SQFT,
            perimeter_in=sum(sides),
            min_width_in=_min_triangle_width_in(sides),
        ))

    member_buckets: dict[str, list] = {}
    for member in model.members:
        member_buckets.setdefault(member.edge_type, []).append(member)
    members = tuple(
        MemberClass(
            edge_type=name,
            count=len(rows),
            stock_length_in=max(m.physical_stock_length_in for m in rows),
            axis_length_in=max(m.physical_axis_length_in for m in rows),
        )
        for name, rows in sorted(member_buckets.items())
    )

    edge_buckets: dict[str, list[float]] = {}
    for edge in topo.edges.values():
        edge_buckets.setdefault(edge.edge_type, []).append(edge.length)
    geodesic_edges = tuple(
        (name, len(lengths), sum(lengths) / len(lengths))
        for name, lengths in sorted(edge_buckets.items())
    )

    base_sides = sum(1 for edge in topo.edges.values() if edge.is_base)
    seam_length = sum(edge.length for edge in topo.edges.values()
                      if not edge.is_base)
    vertex_count = len(vertices)
    member_depth = float(trunk_diameter_in) * 0.5
    member_width = 2.0 * member_depth * math.sin(math.pi / SEED_RADIAL_SPLITS)

    return SeedGeometry(
        long_edge_in=float(topo.long_edge_in),
        short_edge_in=float(topo.short_edge_in),
        radius_in=float(topo.sphere_radius_in),
        height_in=float(vertices[:, 2].max()),
        faces=tuple(faces),
        members=members,
        geodesic_edges=geodesic_edges,
        base_sides=base_sides,
        vertex_count=vertex_count,
        member_depth_in=member_depth,
        member_width_in=member_width,
        seam_count=len(model.seams),
        seam_length_in=seam_length,
    )


# ----------------------------------------------------------------------
# Borrowed: rates this project already declared elsewhere
# ----------------------------------------------------------------------

def _borrowed_price(key: str) -> tuple[float, str, str]:
    """One price out of :mod:`two_v_demo.dome_costing`, with its own note."""
    from two_v_demo import dome_costing

    for item in dome_costing.PRICES:
        if item.key == key:
            return (item.value, item.units,
                    f"borrowed from two_v_demo.dome_costing: {item.note}")
    raise KeyError(f"dome_costing declares no price named {key!r}")


def _borrowed_fact(key: str) -> tuple[float, str, str]:
    """One fact out of :mod:`two_v_demo.dome_performance`."""
    from two_v_demo import dome_performance

    for item in dome_performance.EXTERNAL:
        if item.key == key:
            return (item.value, item.units,
                    f"borrowed from two_v_demo.dome_performance: {item.source}")
    raise KeyError(f"dome_performance declares no fact named {key!r}")


def _borrowed_constants() -> tuple[tuple[str, float, str, str], ...]:
    """Every borrowed rate, as constant rows, so they print in the table."""
    import hull_laminate

    rows: list[tuple[str, float, str, str]] = [
        (name, value, unit, f"hull laminate: {note}")
        for name, value, unit, note in hull_laminate.EXTERNAL_CONSTANTS
    ]
    for key in ("osb_half_4x8",):
        value, units, note = _borrowed_price(key)
        rows.append((key, value, units, note))
    for key in ("r_osb_half", "r_air_films", "ac_seer", "btu_per_kwh",
                "power_price"):
        value, units, note = _borrowed_fact(key)
        rows.append((key, value, units, note))
    return tuple(rows)


# ----------------------------------------------------------------------
# Declared: the owner's inputs
# ----------------------------------------------------------------------

DECLARED_CONSTANTS: tuple[tuple[str, float, str, str], ...] = (
    # --- the frame -------------------------------------------------
    ("lumber_board_usd", 14.00, "USD per 2x6x12",
     "measured: a 2x6x12 on the shelf at Lowes. Every timber figure in this "
     "model is scaled off this one price, because it is the one price the "
     "owner can walk in and check"),
    ("lumber_struts_per_board", 4.0, "struts per board",
     "measured: one 2x6x12 rips and crosscuts into four 2x3x6 struts. The "
     "arithmetic is 1.5 x 5.5 x 144 into four of 1.5 x 2.5 x 72, with the "
     "kerf as the difference"),
    ("strut_thickness_in", 1.5, "in",
     "actual thickness of a nominal 2x, which is not two inches"),
    ("strut_width_in", 2.5, "in",
     "actual width of a nominal 3x, which is not three inches"),
    ("strut_length_in", 72.0, "in",
     "six feet: the same longest member the whole product line is built on"),
    ("frame_waste_fraction", 0.12, "fraction",
     "assumption: sweep, checks and short offcuts that never become a "
     "member"),
    ("frame_fastener_usd_per_member", 1.60, "USD per member",
     "assumption: the structural screws and glue at one pinwheel joint"),
    ("seam_key_usd_each", 2.20, "USD per seam",
     "assumption: one tapered seam key, cut from the same stock"),
    ("seam_hose_usd_per_ft", 1.40, "USD/ft",
     "assumption: compressible EPDM tube in the seam instead of a timber "
     "key, bought by the foot. What a building meant to come apart and go "
     "back together wants: a gasket that recovers, rather than a key that "
     "was made to fit one particular seam"),

    # --- the floor and the port ------------------------------------
    ("floor_port_usd", 340.0, "USD",
     "assumption: the collar, gasket and cover where the pad's power, water "
     "and drain come up through the middle of the floor"),
    ("moisture_barrier_usd_per_sqft", 0.55, "USD/sq ft",
     "assumption: sheet barrier and tape under the floor"),
    ("underfloor_storage_usd", 420.0, "USD",
     "assumption: hatches and framing for the space between the floor and "
     "the blocked-up deck"),
    ("water_tank_usd_per_gal", 1.35, "USD/gal",
     "assumption: potable polyethylene tank, bought by capacity"),
    ("water_tank_gal", 120.0, "gal",
     "the owner's stated under-floor tank: a week for two people"),
    ("blocking_usd_per_point", 14.0, "USD per pier",
     "assumption: one precast block, pad and shim stack"),
    ("blocking_spacing_ft", 4.0, "ft",
     "assumption: pier spacing under the rim and the mid beams"),

    # --- the shell -------------------------------------------------
    ("shell_standoff_in", 0.50, "in",
     "assumption: clearance between the pop-in panels and the inside of the "
     "shell, so the shell lands on the frame and not on the panels"),
    ("shell_skirt_in", 9.0, "in",
     "assumption: depth of the rim band that drops past the floor line and "
     "carries the latches"),
    ("shell_core_thickness_in", 0.4375, "in",
     "assumption: 7/16 in OSB, the sheathing the laminate is built on"),
    ("shell_core_lb_per_sqft", 1.45, "lb/sq ft",
     "assumption: 7/16 in OSB at about 40 lb per cubic foot"),
    ("shell_sheet_width_in", 48.0, "in",
     "assumption: sheet stock width. A four-foot sheet is the cheap one; "
     "whether a dome panel fits on it is computed, not assumed"),
    ("shell_sheet_length_in", 96.0, "in",
     "assumption: sheet stock length"),
    ("shell_core_waste_fraction", 0.22, "fraction",
     "assumption: what is thrown away cutting curved triangles out of "
     "rectangles"),
    ("rim_latch_usd_each", 9.50, "USD each",
     "assumption: one over-centre wire-bail latch and its keeper, the kind "
     "that seals a preserving jar"),
    ("rim_latch_spacing_ft", 2.5, "ft",
     "the owner's stated latch pitch around the rim"),
    ("rim_gasket_usd_per_ft", 2.10, "USD/ft",
     "assumption: closed-cell rim gasket between the shell and the pad"),
    ("lift_ring_usd", 260.0, "USD",
     "assumption: the apex lifting ring, bridle plate and four rigging "
     "points laminated into the shell"),
    ("shell_halves", 4.0, "pieces",
     "the owner's stated shell: slices, not one monocoque. Four of them fit "
     "a trailer and two people can carry one; eight is the version one "
     "person can. They snap to each other down an S-lip seam and then snap "
     "to the pad, so the joint seals by shape rather than by sealant"),
    ("shell_slice_lip_usd_per_ft", 6.80, "USD/ft",
     "assumption: the moulded S-lip down a slice seam -- the interlocking "
     "return that makes two pieces behave like one skin, plus its gasket"),
    ("shell_joint_usd_per_ft", 18.50, "USD/ft",
     "assumption: the joint down the middle of a split shell -- moulded "
     "lap, compression gasket, and over-centre latches at a close pitch. "
     "It is the one seam that has to shed water by shape rather than by "
     "sealant, so it is not cheap"),

    # --- the seam channel, and what it is used for ---
    ("seam_duct_usd_per_ft", 1.90, "USD/ft",
     "assumption: closing the outside of the seam channel into a duct -- "
     "cap strip, end fittings and the clips that hold it"),
    ("duct_fan_usd", 165.0, "USD each",
     "assumption: one small in-line fan and its controller, driving the "
     "seam network either way"),
    ("duct_fans", 2.0, "fans",
     "the owner's stated arrangement: one pushing, one pulling, so the "
     "network runs in either direction"),
    ("duct_port_usd_each", 6.50, "USD each",
     "assumption: one through-hole fitting where a seam duct meets a "
     "vertex or a panel bay"),
    ("catchment_usd", 240.0, "USD",
     "assumption: the manifold, filter and downpipe that take what the seam "
     "channels collect into the pad's tank"),
    ("rain_in_per_year", 40.0, "in/year",
     "borrowed in spirit from two_v_demo.dome_performance: US average "
     "annual precipitation. Substitute your own"),
    # --- solar and storage ---
    ("solar_panel_watts", 800.0, "W",
     "the owner's stated array: four to eight hundred watts, on the sunward "
     "side of the dome or up a mast beside it. Eight hundred is the top of "
     "that and the one costed here"),
    ("solar_usd_per_watt_diy", 0.95, "USD/W",
     "assumption: panels, rails, charge controller and wiring, fitted by "
     "the owner. Lower than the park model's installed rate because nobody "
     "is being paid to climb the dome"),
    ("battery_kwh", 10.0, "kWh",
     "the owner's stated bank, read as usable kilowatt hours. Ten is about "
     "three ordinary days in this dome. NOTE: the brief said 3000, which at "
     "kilowatt hours is two hundred Powerwalls and $1.2m of cells -- almost "
     "certainly 3000 watt-hours or a 3000 watt inverter was meant. The "
     "figure is here so the scale of the two readings is visible"),
    ("battery_usd_per_kwh", 410.0, "USD/kWh",
     "assumption: LiFePO4 cells with a BMS, bought as a rack unit"),
    ("inverter_watts", 3000.0, "W",
     "the owner's stated inverter: three thousand watts continuous"),
    ("inverter_usd_per_kw", 210.0, "USD/kW",
     "assumption: a low-frequency hybrid inverter-charger"),
    ("solar_derate", 0.78, "fraction",
     "assumption: what actually reaches the battery after temperature, "
     "wiring, controller and dirt"),

    # --- radiative cooling paint ---
    ("paint_usd_per_sqft", 1.35, "USD/sq ft",
     "assumption: two coats of a barium-sulphate radiative cooling "
     "formulation on the shell's weather face"),

    ("catch_efficiency", 0.72, "fraction",
     "assumption: what a channel network actually delivers to the tank "
     "after wetting, splash and first-flush loss. Lower than a solid roof "
     "with a gutter, because this is a seam and not a gutter"),

    # --- hardware sized to outlive this dome ---
    ("hardware_size_steps", 3.0, "dome sizes",
     "the owner's stated rule: the triangle joining hardware is made to fit "
     "this dome and the next two sizes up, so it is carried forward rather "
     "than replaced"),
    ("hardware_oversize_fraction", 0.35, "fraction",
     "assumption: what making one hardware set fit three sizes costs over "
     "making it fit one"),

    # --- what closes each triangle ---------------------------------
    ("bladder_fabric_usd_per_sqft", 0.85, "USD/sq ft",
     "assumption: coated fabric for the insulation bladder, both faces"),
    ("bladder_zip_usd_each", 3.40, "USD each",
     "assumption: one long zip and its flap per triangle, so a bladder can "
     "be opened and refilled"),
    ("bladder_labour_min_each", 22.0, "minutes each",
     "assumption: cutting and sewing one ravioli bladder to a panel's shape"),
    ("insulation_usd_per_cuft", 1.10, "USD/cu ft",
     "assumption: loose-fill cellulose blown into the bladder"),
    ("insulation_r_per_in", 3.50, "hr sq ft F/BTU per in",
     "assumption: settled loose-fill cellulose"),
    ("insulation_lb_per_cuft", 2.20, "lb/cu ft",
     "assumption: settled density of the same fill"),
    ("hard_panel_usd_per_sqft", 2.40, "USD/sq ft",
     "assumption: one pop-in panel -- corrugated or solid poly sheet -- cut "
     "to the triangle. Two of these go in every bay, one against the inside "
     "lip and one from the outside, with the cavity between them"),
    ("panel_bays_panels", 2.0, "panels per bay",
     "the owner's stated bay: an inner panel onto the wedge's lip, a cavity, "
     "and an outer panel compression-fitted from outside. Ship it at one and "
     "the bay is open to the inside until the owner closes it"),
    ("panel_lip_in", 0.75, "in",
     "the owner's stated lip: how far the wedge's inward face stands proud "
     "of the panel seat, which is what the inner panel sits on and what "
     "makes the whole bay a compression fit rather than a fastened one"),
    ("inject_fill_usd_per_cuft", 0.0, "USD/cu ft",
     "left at zero: the standard article ships the cavity EMPTY, as a "
     "ventilated void. Filling it is a choice made later, and what it costs "
     "depends on what goes in"),
    ("hard_panel_gasket_usd_per_ft", 0.70, "USD/ft",
     "assumption: the compression gasket around a pop-in panel's edge"),

    # --- the utility column and the interface boundary -------------
    ("column_housing_usd", 380.0, "USD",
     "assumption: the metal column itself -- folded shell, base flange, "
     "access doors and the apex penetration sleeve"),
    ("column_manifold_usd", 240.0, "USD",
     "assumption: hot and cold manifold, shutoffs and the pressure-tested "
     "rise from the pad port"),
    ("column_drain_usd", 165.0, "USD",
     "assumption: the drain stack, trap and floor-port tie-in"),
    ("column_electrical_usd", 310.0, "USD",
     "assumption: a small sub-panel, breakers, GFCI and the outlet ring on "
     "the column"),
    ("column_riser_usd_per_ft", 11.0, "USD/ft",
     "assumption: conduit, PEX pair and drain carried in one chase, priced "
     "by the foot of rise"),
    ("seal_cap_usd", 195.0, "USD",
     "assumption: the gasketed apex cap -- moulded cap, compression gasket, "
     "backing ring and the bolts that make it removable but not casual"),
    ("exterior_routing_usd_per_ft", 6.40, "USD/ft",
     "assumption: service line run down the outside of the shell from the "
     "seal cap to a panel, clipped and UV-sleeved"),

    # --- the polyp panels ------------------------------------------
    ("polyp_frame_usd", 210.0, "USD each",
     "assumption: the panel's own frame, back and weather lid, sized to "
     "stand outside the dome's footprint"),
    ("polyp_service_usd", 95.0, "USD each",
     "assumption: the quick-connect water, drain and power tails that make "
     "a panel a socket rather than a box"),
    ("polyp_wall_port_usd", 88.0, "USD each",
     "assumption: the gasketed pass-through where a polyp reaches back "
     "through the shell to the inside"),

    # --- the modules the stem cell ships with ----------------------
    ("ac_usd_per_kbtu", 78.0, "USD per 1000 BTU/h",
     "assumption: a small inverter mini-split, installed cost per unit of "
     "capacity. Not what this dome ships with -- see the window unit "
     "below -- but kept so the two can be compared"),
    ("ac_window_usd_per_kbtu", 30.0, "USD per 1000 BTU/h",
     "assumption: a window or through-wall unit, which is what a 277 sq ft "
     "floor with a computed 3,700 BTU/h load actually needs. A mini-split "
     "on this envelope is equipment bought for the brochure"),
    ("ac_design_delta_f", 20.0, "F",
     "assumption: 95 F outside against 75 F inside, the cooling design day"),
    ("ac_internal_gain_btu", 1200.0, "BTU/h",
     "assumption: two people, lights and a fridge"),
    ("ac_solar_gain_btu_per_sqft", 2.6, "BTU/h per sq ft of shell",
     "assumption: what a light-coloured sunlit shell drives inward at the "
     "design hour"),
    ("ac_sizes_kbtu", 6.0, "1000 BTU/h",
     "assumption: capacity comes in steps this big, so the computed load is "
     "rounded up to one"),
    ("light_fan_usd", 165.0, "USD",
     "assumption: the central DC ceiling fan and light fixture"),
    ("lighting_circuit_usd", 140.0, "USD",
     "assumption: the ring of fittings, switches and cable that feeds it"),
    ("wood_stove_usd", 640.0, "USD",
     "assumption: the little all-metal stove dome -- rolled shell, flat "
     "cooktop, door, grate and flue collar, made in-house"),
    ("flue_usd_per_ft", 46.0, "USD/ft",
     "assumption: insulated flue pipe, by the foot, through the shell"),
    ("stove_shield_usd", 120.0, "USD",
     "assumption: the heat shield and the hearth pad under it"),

    # --- what it costs to make ------------------------------------
    ("labour_usd_per_hour", 28.0, "USD/hour",
     "the owner's stated shop rate, loaded"),
    ("frame_min_per_member", 12.0, "minutes per member",
     "assumption: split one wedge off a log on site, butt cut, head cut, "
     "drill and fix it on the jig. Higher than the nine minutes a shop "
     "takes with prepared stock, because milling from the customer's own "
     "standing timber is real work and it has to land somewhere"),
    ("panel_min_each", 14.0, "minutes per panel",
     "assumption: squaring up, gluing and pulling one triangle together "
     "once its three members exist"),
    ("shell_min_per_sqft", 3.4, "minutes per sq ft",
     "assumption: cut, fit, tape, laminate and fair one square foot of "
     "shell, averaged over the whole job"),
    ("column_hours", 6.5, "hours",
     "assumption: building, plumbing and wiring one utility column"),
    ("polyp_hours_each", 2.2, "hours",
     "assumption: building and connecting one utility panel"),
    ("assembly_hours", 9.0, "hours",
     "assumption: standing the dome, setting the shell and commissioning "
     "the services, in the yard, before it is taken apart to ship"),

    # --- what it costs to sell ------------------------------------
    ("shop_overhead_fraction", 0.18, "fraction of cost",
     "the owner's stated overhead: rent, power, tooling and the hours that "
     "are not on any one dome"),
    ("warranty_reserve_fraction", 0.04, "fraction of cost",
     "the owner's stated reserve against a shell that leaks or a column "
     "that has to come back"),
    ("gross_margin_fraction", 0.35, "fraction of price",
     "the owner's stated margin, taken on the selling price, not on cost"),
    ("freight_usd", 1250.0, "USD",
     "assumption: one flat-packed dome on a trailer, regional"),
    ("core_service_life_years", 25.0, "years",
     "assumption: how long a utility core lasts before it is worn out "
     "rather than merely outgrown"),
    ("core_move_usd", 260.0, "USD per move",
     "assumption: unbolting a core, capping the lines, crating it and "
     "commissioning it again in the next dome"),
    ("sales_tax_fraction", 0.0, "fraction of price",
     "left at zero: it is the buyer's jurisdiction, not a manufacturing "
     "cost"),
)


@lru_cache(maxsize=1)
def external_constants() -> tuple[tuple[str, float, str, str], ...]:
    """Every input this model takes, borrowed rows first, then declared."""
    return _borrowed_constants() + DECLARED_CONSTANTS


_OVERRIDES: dict[str, float] = {}


def load_overrides(path: Path | None = None) -> dict[str, float]:
    """Read the owner's saved prices, if there are any.

    Absent file, unreadable file or an unknown key is not an error: the model
    has a complete set of defaults and simply uses them.
    """
    global _OVERRIDES
    target = Path(path) if path is not None else OVERRIDE_PATH
    data: dict[str, float] = {}
    if target.exists():
        try:
            raw = json.loads(target.read_text(encoding="utf-8"))
        except (OSError, ValueError):
            raw = {}
        known = {name for name, _v, _u, _n in external_constants()}
        for key, value in (raw or {}).items():
            if key in known:
                try:
                    data[key] = float(value)
                except (TypeError, ValueError):
                    continue
    _OVERRIDES = data
    return dict(data)


def save_overrides(path: Path | None = None) -> Path:
    """Write the owner's changed prices beside the tools."""
    target = Path(path) if path is not None else OVERRIDE_PATH
    target.write_text(json.dumps(_OVERRIDES, indent=2, sort_keys=True),
                      encoding="utf-8")
    return target


def set_override(name: str, value: float) -> float:
    """Change one input. Unknown names are refused rather than ignored."""
    known = {key for key, _v, _u, _n in external_constants()}
    if name not in known:
        raise KeyError(f"no seed constant {name!r}")
    _OVERRIDES[name] = float(value)
    return float(value)


def clear_override(name: str) -> None:
    _OVERRIDES.pop(name, None)


def is_overridden(name: str) -> bool:
    return name in _OVERRIDES


def strut_volume_cuin() -> float:
    """One 2x3x6, in cubic inches. The unit every timber price is scaled to."""
    return (declared("strut_thickness_in") * declared("strut_width_in")
            * declared("strut_length_in"))


def usd_per_strut() -> float:
    """What one 2x3x6 costs, out of the board it comes from."""
    return declared("lumber_board_usd") / declared("lumber_struts_per_board")


def usd_per_cuin() -> float:
    """Shelf timber, priced by the cubic inch of usable stock.

    This is the rate everything wooden in the model is costed at, including
    the wedges -- because the honest way to price a stick that is not sold in
    shops is to ask what the same volume of wood costs in one that is.
    """
    return usd_per_strut() / strut_volume_cuin()


@lru_cache(maxsize=1)
def _defaults() -> dict[str, float]:
    return {name: value for name, value, _u, _n in external_constants()}


def declared(name: str) -> float:
    """One input, by name: the owner's value if they set one, else the default."""
    if name in _OVERRIDES:
        return _OVERRIDES[name]
    try:
        return _defaults()[name]
    except KeyError:
        raise KeyError(f"no seed constant {name!r}; choose from "
                       f"{', '.join(sorted(_defaults()))}") from None


def units_of(name: str) -> str:
    for key, _value, unit, _note in external_constants():
        if key == name:
            return unit
    raise KeyError(name)


def note_of(name: str) -> str:
    for key, _value, _unit, note in external_constants():
        if key == name:
            return note
    raise KeyError(name)


# ----------------------------------------------------------------------
# A line on the bill
# ----------------------------------------------------------------------

@dataclass(frozen=True)
class Line:
    """One priced line: what it is, how many, and where the price came from."""

    label: str
    quantity: float
    unit: str
    unit_cost: float
    source: str = ""
    """The declared constant this line's rate came from, for the audit."""

    @property
    def cost(self) -> float:
        return self.quantity * self.unit_cost


@dataclass(frozen=True)
class Group:
    """A named block of lines: the frame, the shell, the column."""

    key: str
    label: str
    lines: tuple[Line, ...]
    optional: bool = False
    """True if the configuration interface may switch this group off."""
    side: str = "dome"
    """``dome`` or ``pad``.

    The most important field in this file. A dome buyer and a pad host are
    two different people paying two different bills, and a model that adds
    them together answers a question nobody asked. The deck, the barrier, the
    service port, the tank and the under-floor storage are the *host's*: they
    are built once, they stay when the dome leaves, and the dome's price must
    not carry them."""

    @property
    def cost(self) -> float:
        return sum(line.cost for line in self.lines)


# ----------------------------------------------------------------------
# The shell: the expensive part, and the one with a real choice in it
# ----------------------------------------------------------------------

def laminates():
    """The hull laminate systems this shell can be built with."""
    import hull_laminate

    return hull_laminate.LAMINATES


def laminate_keys() -> tuple[str, ...]:
    import hull_laminate

    return hull_laminate.LAMINATE_KEYS


RESINS = ("boatyard", "sheathed", "marine", "vinylester")
"""Kept under its old name so nothing that imported it breaks. These are now
laminate *systems* out of :mod:`hull_laminate`, not bare resin types: a shell
is a schedule of fabrics in a resin, and pricing the resin alone was the thing
that made the first version of this model wrong."""


@dataclass(frozen=True)
class ShellPlan:
    """The removable shell, measured and weighed before it is priced."""

    resin: str
    outer_sqft: float
    inner_sqft: float
    skirt_sqft: float
    core_sqft: float
    core_sheets: float
    latches: int
    rim_gasket_ft: float
    core_lb: float
    laminate: object
    """The :class:`hull_laminate.LaminatePlan` for this skin."""
    panel_fits_sheet: tuple[tuple[str, bool, float], ...]
    """(face name, fits a whole sheet, min width in inches) -- the finding
    that decides whether the core can be cut triangle by triangle."""

    @property
    def laminated_sqft(self) -> float:
        return self.laminate.laminated_sqft

    @property
    def resin_gal(self) -> float:
        return self.laminate.resin_gal

    @property
    def glass_lb(self) -> float:
        return self.laminate.glass_lb

    @property
    def weight_lb(self) -> float:
        """Core plus laminate: what the crane has to pick up."""
        return self.core_lb + self.laminate.skin_lb


def shell_plan(geometry: SeedGeometry | None = None,
               resin: str = "boatyard") -> ShellPlan:
    """Work out the shell: its area, its laminate, and what it weighs.

    The shell stands off the frame by the member's depth plus a declared
    clearance, because it lands on the sticks and the pop-in panels sit inside
    that depth. Everything else follows from the area that gives, and the
    laminate itself is weighed and priced by :mod:`hull_laminate` out of the
    marine composites trade's own product list.
    """
    import hull_laminate

    if resin not in laminate_keys():
        raise ValueError(f"laminate must be one of {laminate_keys()}, "
                         f"not {resin!r}")
    geometry = geometry or seed_geometry()

    standoff = geometry.member_depth_in + declared("shell_standoff_in")
    inner_sqft = geometry.shell_sqft(standoff)
    outer_sqft = geometry.shell_sqft(standoff + declared("shell_core_thickness_in"))
    skirt_ft = geometry.base_perimeter_at(standoff)
    skirt_sqft = skirt_ft * declared("shell_skirt_in") / 12.0

    core_sqft = inner_sqft + skirt_sqft
    sheet_sqft = (declared("shell_sheet_width_in")
                  * declared("shell_sheet_length_in") / SQIN_PER_SQFT)
    core_sheets = (core_sqft * (1.0 + declared("shell_core_waste_fraction"))
                   / sheet_sqft)

    # The weather face carries the structural plies and the gelcoat; the
    # inside face only has to be sealed. The skirt is glassed both sides,
    # because both of its sides are outside.
    laminate_plan = hull_laminate.plan(
        resin, outer_sqft + skirt_sqft, inner_sqft + skirt_sqft, declared)

    spacing = declared("rim_latch_spacing_ft")
    latches = max(6, int(math.ceil(skirt_ft / spacing)))

    sheet_min_side = min(declared("shell_sheet_width_in"),
                         declared("shell_sheet_length_in"))
    fits = tuple(
        (face.name, face.min_width_in <= sheet_min_side + 1e-9, face.min_width_in)
        for face in geometry.faces
    )

    return ShellPlan(
        resin=resin,
        outer_sqft=outer_sqft,
        inner_sqft=inner_sqft,
        skirt_sqft=skirt_sqft,
        core_sqft=core_sqft,
        core_sheets=core_sheets,
        latches=latches,
        rim_gasket_ft=skirt_ft,
        core_lb=core_sqft * declared("shell_core_lb_per_sqft"),
        laminate=laminate_plan,
        panel_fits_sheet=fits,
    )


def resin_price(resin: str) -> float:
    """What a gallon of this system's resin costs."""
    import hull_laminate

    return declared(hull_laminate.laminate(resin).resin_key)


def shell_group(geometry: SeedGeometry | None = None,
                resin: str = "boatyard") -> Group:
    geometry = geometry or seed_geometry()
    plan = shell_plan(geometry, resin)
    laminate = plan.laminate
    sheet_sqft = (declared("shell_sheet_width_in")
                  * declared("shell_sheet_length_in") / SQIN_PER_SQFT)

    lines = [
        Line(f"sheet core, {plan.core_sqft:,.0f} sq ft at {sheet_sqft:.0f} "
             "sq ft a sheet", plan.core_sheets, "sheets",
             declared("osb_half_4x8"), "osb_half_4x8"),
    ]
    # One line per ply, because a laminate schedule is a list of fabrics and
    # a single "fibreglass" line hides which one the money is in.
    for ply in laminate.plies:
        lines.append(Line(f"{ply.label}, {ply.sqft:,.0f} sq ft "
                          f"({ply.glass_lb:,.0f} lb)",
                          ply.sqft, "sq ft",
                          ply.fabric_usd / ply.sqft if ply.sqft else 0.0,
                          "hull_laminate"))
    lines.append(Line(f"{laminate.system.resin_label}, "
                      f"{laminate.resin_lb:,.0f} lb at "
                      f"{laminate.ratio:.2f}:1", laminate.resin_gal, "gal",
                      resin_price(resin), laminate.system.resin_key))
    if laminate.gelcoat_usd:
        lines.append(Line("gelcoat on the weather face", laminate.gelcoat_gal,
                          "gal", declared("gelcoat_usd_per_gal"),
                          "gelcoat_usd_per_gal"))
    slices = max(1.0, declared("shell_halves"))
    if slices > 1.0:
        # The shell arrives in slices, like the segments of an orange, and
        # every seam between them has to shed water by its shape rather than
        # by something squeezed into it: a moulded S-lip that interlocks, a
        # gasket in the return, and latches at a close pitch. Four slices fit
        # a trailer; eight can be carried by one person.
        #
        # Each seam runs from the rim to the apex, which is a quarter of the
        # shell's own circumference, and there are as many seams as slices.
        quarter_ft = 0.5 * math.pi * (geometry.radius_in / 12.0)
        joint_ft = quarter_ft * slices
        lines.append(Line(
            f"S-lip seams, {slices:.0f}-slice shell", joint_ft, "ft",
            declared("shell_joint_usd_per_ft"), "shell_joint_usd_per_ft"))
        lines.append(Line(
            "moulded interlock and gasket", joint_ft, "ft",
            declared("shell_slice_lip_usd_per_ft"),
            "shell_slice_lip_usd_per_ft"))
    lines.extend([
        Line("layup consumables", laminate.laminated_sqft, "sq ft",
             declared("consumables_usd_per_sqft"), "consumables_usd_per_sqft"),
        Line("rim latches", float(plan.latches), "each",
             declared("rim_latch_usd_each"), "rim_latch_usd_each"),
        Line("rim gasket", plan.rim_gasket_ft, "ft",
             declared("rim_gasket_usd_per_ft"), "rim_gasket_usd_per_ft"),
        Line("apex lifting ring and rigging points", 1.0, "set",
             declared("lift_ring_usd"), "lift_ring_usd"),
    ])
    return Group("shell", "Removable shell", tuple(lines))


# ----------------------------------------------------------------------
# The frame
# ----------------------------------------------------------------------

FRAME_STOCK = ("customer_trees", "wedge_log", "dimensional")
SEAMS = ("hose", "rigid", "none")
"""What sits between two panels. Kept in step with :data:`seed_world.SEAMS`;
one of them decides what it costs and the other decides what it looks like."""


def frame_group(geometry: SeedGeometry | None = None,
                stock: str = "wedge_log", seam: str = "hose") -> Group:
    """The wedge-cut frame: 120 members, and what the stock for them costs."""
    geometry = geometry or seed_geometry()
    waste = 1.0 + declared("frame_waste_fraction")

    # Every timber option is priced against the same shelf rate: what a
    # cubic inch of usable wood costs at Lowes, out of a 2x6x12.
    rate = usd_per_cuin()
    wedge_cuin = geometry.wedge_volume_cuin * waste

    if stock == "customer_trees":
        # The frame is not shipped. It is split out of the buyer's own
        # standing timber on the site the dome is going up on, which is the
        # single largest thing that can come off the price of one of these.
        stock_line = Line(
            f"wedges: the buyer's own trees, {geometry.trees_needed:.1f} of "
            f"them, {geometry.member_count} members",
            float(geometry.member_count), "members", 0.0, "customer supplied")
    elif stock == "wedge_log":
        stock_line = Line(
            f"wedges bought as timber, {geometry.wedge_to_strut:.1f} x a "
            f"2x3x6 each",
            float(geometry.member_count), "members", wedge_cuin * rate,
            "lumber_board_usd")
    elif stock == "dimensional":
        # The comparison everybody asks for: the same dome in bought sticks.
        # Not the same dome, in fact -- a 2x3 is a fraction of a wedge -- and
        # that is the point of putting the two side by side.
        stock_line = Line(
            f"2x3x6 struts at ${usd_per_strut():.2f}, "
            f"{declared('lumber_struts_per_board'):.0f} to a 2x6x12",
            float(geometry.member_count) * waste, "struts", usd_per_strut(),
            "lumber_board_usd")
    else:
        raise ValueError(f"frame stock must be one of {FRAME_STOCK}")

    if seam not in SEAMS:
        raise ValueError(f"seam must be one of {SEAMS}, not {seam!r}")
    if seam == "rigid":
        seam_line = Line(f"timber seam keys, {geometry.seam_count} seams",
                         float(geometry.seam_count), "seams",
                         declared("seam_key_usd_each"), "seam_key_usd_each")
    elif seam == "hose":
        seam_line = Line(f"seam hose, {geometry.seam_count} seams",
                         geometry.seam_length_ft, "ft",
                         declared("seam_hose_usd_per_ft"),
                         "seam_hose_usd_per_ft")
    else:
        seam_line = None

    lines = [
        stock_line,
        Line(f"joining hardware, sized for this dome and "
             f"{declared('hardware_size_steps') - 1:.0f} sizes up",
             float(geometry.member_count), "joints",
             declared("frame_fastener_usd_per_member")
             * (1.0 + declared("hardware_oversize_fraction")),
             "frame_fastener_usd_per_member"),
    ]
    if seam_line is not None:
        lines.append(seam_line)
    return Group("frame", "Wedge-cut frame", tuple(lines))


# ----------------------------------------------------------------------
# The floor, and the port it lands on
# ----------------------------------------------------------------------

PAD_DECK_KIND = "blocks"
"""Which platform the standard pad quotes.

``blocks`` -- piers, beams, joists, boards, sealed -- because it is the one
that comes apart again, which is the whole argument for a pad over a
foundation. :mod:`pad_deck` prices the alternatives.
"""


def declared_deck() -> str:
    return PAD_DECK_KIND


def wet_group(glazed: bool = False) -> Group:
    """The shower: a fabricated insert, not a curtain and a hope.

    Optional and off by default, because the Shelter and Serviced rungs of
    the deferment ladder do not have one and the price should say so.
    """
    import fitout_wet

    area = fitout_wet.wet_area(glazed)
    lines = [Line(line.label, line.quantity, line.unit, line.unit_cost,
                  f"fitout_wet.{line.source}") for line in area.lines]
    return Group("wet", "Shower and wet area", tuple(lines), optional=True)


def pad_group(geometry: SeedGeometry | None = None) -> Group:
    """The pad: the host's bill, not the dome buyer's.

    This is the change that makes the rest of the model mean anything. A dome
    buyer does not pay for a deck, a moisture barrier, a service port, a tank
    or the storage under the floor: those are built into the ground once, they
    stay behind when the dome is lifted off, and the next dome lands on them.
    Putting them in the dome's price makes the dome look three thousand
    dollars worse than it is and makes hosting look free, and both halves of
    that are wrong.

    Sized on the decagon the frame actually stands on, not the circle it is
    drawn inside. The difference is nineteen square feet, and paying for
    nineteen square feet of deck that is not under the dome is exactly the
    kind of quiet rounding this file exists to stop.

    The deck itself is a *takeoff*, not a rate. It used to be one number a
    square foot borrowed from the park model, which is how a platform for a
    nineteen-foot dome came out looking like a contractor's finished deck.
    :mod:`pad_deck` counts the piers, the beams, the joists and the boards
    and prices every one of them off the same 2x6x12 the dome's own frame is
    priced against, so there is one shelf price in this project and not two.
    """
    import pad_deck
    import park_model

    geometry = geometry or seed_geometry()
    area = geometry.floor_decagon_sqft
    built = pad_deck.deck(declared_deck())
    lines = [
        Line(f"{built.label.lower()}, {built.area_sqft:,.0f} sq ft "
             f"({built.boards:.0f} boards)" if built.boards
             else f"{built.label.lower()}, {built.area_sqft:,.0f} sq ft",
             1.0, "platform", built.cost, "pad_deck"),
        Line("moisture barrier", area, "sq ft",
             declared("moisture_barrier_usd_per_sqft"),
             "moisture_barrier_usd_per_sqft"),
        Line("service port up through the deck", 1.0, "each",
             declared("floor_port_usd"), "floor_port_usd"),
        Line(f"water tank, {declared('water_tank_gal'):.0f} gal",
             declared("water_tank_gal"), "gal",
             declared("water_tank_usd_per_gal"), "water_tank_usd_per_gal"),
        Line("under-floor storage", 1.0, "set",
             declared("underfloor_storage_usd"), "underfloor_storage_usd"),
        Line(f"share of one hub panel, 1 of "
             f"{park_model.declared('hub_pads_served'):.0f}", 1.0, "share",
             park_model.declared("hub_panel_usd")
             / park_model.declared("hub_pads_served"), "park_model"),
        Line("spur from the hub", 1.0, "each",
             park_model.declared("spur_usd_per_pad"), "park_model"),
        Line("permits", 1.0, "each",
             park_model.declared("permit_usd_per_pad"), "park_model"),
    ]
    return Group("pad", "The pad, built by the host", tuple(lines),
                 side="pad")


def floor_group(geometry: SeedGeometry | None = None) -> Group:
    """Kept under its old name. See :func:`pad_group`."""
    return pad_group(geometry)


# ----------------------------------------------------------------------
# What closes each triangle: the bladder, then the pop-in panel
# ----------------------------------------------------------------------

@dataclass(frozen=True)
class InsulationPlan:
    """The ravioli bladders, and what filling them buys."""

    triangles: int
    cavity_cuft: float
    fill_lb: float
    bladder_fabric_sqft: float
    cavity_r: float
    assembly_r: float

    @property
    def u_value(self) -> float:
        return 1.0 / self.assembly_r


def insulation_plan(geometry: SeedGeometry | None = None) -> InsulationPlan:
    geometry = geometry or seed_geometry()
    triangles = sum(face.count for face in geometry.faces)
    cavity = geometry.cavity_cuft
    # A bladder is a flat sack: two faces the size of the triangle, plus a
    # gusset the depth of the cavity all the way round its perimeter.
    faces_sqft = geometry.panel_sqft * 2.0
    gusset_sqft = sum(
        face.count * face.perimeter_in * geometry.member_depth_in
        for face in geometry.faces) / SQIN_PER_SQFT
    fabric = faces_sqft + gusset_sqft

    cavity_r = declared("insulation_r_per_in") * geometry.member_depth_in
    assembly_r = (cavity_r + declared("r_osb_half") + declared("r_air_films"))
    return InsulationPlan(
        triangles=triangles,
        cavity_cuft=cavity,
        fill_lb=cavity * declared("insulation_lb_per_cuft"),
        bladder_fabric_sqft=fabric,
        cavity_r=cavity_r,
        assembly_r=assembly_r,
    )


def envelope_group(geometry: SeedGeometry | None = None) -> Group:
    """What closes the forty triangles: two panels and the void between them.

    The bay used to be a sandwich held by friction: an inner panel onto the
    wedge's lip from inside and an outer panel compression-fitted from
    outside. That is optimistic on a dome, because most of a dome's bays are
    overhead, and a friction fit overhead spends the life of the building
    arguing with gravity.

    So the panel sits on the **outside face** and is pulled *into* the frame
    by screws landing in threaded inserts. Gravity works with the fixing; the
    panel is itself the barrier to the weather; and it comes off with a
    driver rather than a pry bar. :mod:`fitout_wet` prices it, and the
    inserts it leaves behind are a grid of anchor points a shelf or a bunk
    can span three triangles and bolt to.

    The cavity behind it still ships EMPTY. That is not a saving, it is the
    design: an empty cavity is a duct, and the seam channels connect all
    forty of them.
    """
    import fitout_wet

    geometry = geometry or seed_geometry()
    lines = [Line(line.label, line.quantity, line.unit, line.unit_cost,
                  f"fitout_wet.{line.source}")
             for line in fitout_wet.panel_lines(geometry)]
    return Group("envelope", "Panel bays", tuple(lines))


# ----------------------------------------------------------------------
# The seam channel: the thing the dihedral angle gives you for free
# ----------------------------------------------------------------------

@dataclass(frozen=True)
class SeamDuct:
    """The seam network, treated as air and water rather than as a joint.

    Two flat sawn faces meeting at a dihedral angle do not close flush, and
    the usual response is to machine them until they do. Left alone, the gap
    is a continuous channel that already runs to every vertex of the dome.
    Cap it and it is a duct.
    """

    length_ft: float
    seams: int
    vertices: int
    channel_in2: float
    """Cross-section of one channel, from the angle the two faces leave."""

    @property
    def volume_cuft(self) -> float:
        return self.length_ft * 12.0 * self.channel_in2 / CUIN_PER_CUFT

    @property
    def catch_sqft(self) -> float:
        """Roof area draining into the network: the whole shell."""
        return seed_geometry().panel_sqft

    @property
    def gallons_per_year(self) -> float:
        """What the seams could put in the pad's tank in a year.

        One inch of rain on one square foot is 144/231 of a gallon, exactly.
        """
        inches = declared("rain_in_per_year")
        gallons_per_sqft_inch = 144.0 / 231.0
        return (self.catch_sqft * inches * gallons_per_sqft_inch
                * declared("catch_efficiency"))


def seam_duct(geometry: SeedGeometry | None = None) -> SeamDuct:
    """The seam network of one dome, measured.

    The channel's cross-section is the wedge's own leftover angle: two sawn
    faces meeting at the seam's dihedral, times the depth of the member. The
    solver already knows that angle for every seam, so this asks it rather
    than assuming a rectangle.
    """
    from two_v_demo import raw_wedge_bridge

    geometry = geometry or seed_geometry()
    model = raw_wedge_bridge.model(
        long_edge_in=geometry.long_edge_in,
        trunk_diameter_in=geometry.member_depth_in * 2.0)
    gaps = [seam.raw_gap_angle_deg for seam in model.seams]
    mean_gap = sum(gaps) / len(gaps) if gaps else 0.0
    depth = geometry.member_depth_in
    # A wedge of angle g, depth d, taken twice -- one face each side.
    channel = depth * depth * math.tan(math.radians(max(0.0, mean_gap) * 0.5))
    return SeamDuct(
        length_ft=geometry.seam_length_ft,
        seams=geometry.seam_count,
        vertices=geometry.vertex_count,
        channel_in2=channel,
    )


def airflow_group(geometry: SeedGeometry | None = None) -> Group:
    """Closing the seam channels into a ducted network. Optional.

    Two fans, one pushing and one pulling, so the network runs either way:
    blown out, it keeps water from ever sitting in a joint; drawn in, it
    pulls what lands on the shell down the channels and into the pad's tank.
    """
    geometry = geometry or seed_geometry()
    duct = seam_duct(geometry)
    lines = (
        Line(f"cap the seam channels, {duct.seams} seams", duct.length_ft,
             "ft", declared("seam_duct_usd_per_ft"), "seam_duct_usd_per_ft"),
        Line("through-hole fittings at the vertices",
             float(duct.vertices), "each", declared("duct_port_usd_each"),
             "duct_port_usd_each"),
        Line("fans, one pushing and one pulling", declared("duct_fans"),
             "each", declared("duct_fan_usd"), "duct_fan_usd"),
        Line("catchment manifold into the pad's tank", 1.0, "set",
             declared("catchment_usd"), "catchment_usd"),
    )
    return Group("airflow", "Seam duct and catchment", lines, optional=True)


@dataclass(frozen=True)
class QuiltLadder:
    """What layering the shell buys, one layer at a time.

    The shell comes off. A quilted layer goes on. The shell goes back on. Do
    that once a season and the R-value of the building climbs for as long as
    you own it, which is not a thing a finished house does.

    Both figures here are :mod:`park_model`'s, not new ones: it already
    declared what a quilted layer of recycled fabric is worth and what it
    costs, for the dome-park film, and two modules disagreeing about a layer
    of cloth would be exactly the sort of drift this project exists to stop.
    """

    layers: int
    sqft: float
    r_per_layer: float
    usd_per_sqft_layer: float
    base_r: float

    @property
    def usd_per_layer(self) -> float:
        return self.sqft * self.usd_per_sqft_layer

    @property
    def added_r(self) -> float:
        return self.layers * self.r_per_layer

    @property
    def total_r(self) -> float:
        return self.base_r + self.added_r

    def rows(self) -> tuple[tuple[int, float, float], ...]:
        """(layer number, R after it, cumulative cost)."""
        return tuple(
            (n, self.base_r + n * self.r_per_layer, n * self.usd_per_layer)
            for n in range(0, self.layers + 1))


def quilt_ladder(layers: int = 7,
                 geometry: SeedGeometry | None = None) -> QuiltLadder:
    """Seven layers, because seven shirts is the argument."""
    import park_model

    geometry = geometry or seed_geometry()
    plan = insulation_plan(geometry)
    return QuiltLadder(
        layers=int(layers),
        sqft=geometry.panel_sqft,
        r_per_layer=park_model.declared("quilt_r_per_layer"),
        usd_per_sqft_layer=park_model.declared("quilt_usd_per_sqft_layer"),
        base_r=declared("r_osb_half") + declared("r_air_films"),
    )


def quilt_group(layers: int = 0,
                geometry: SeedGeometry | None = None) -> Group:
    """Quilted layers in the cavity. Bought one at a time, not all at once."""
    geometry = geometry or seed_geometry()
    if layers <= 0:
        return Group("quilt", "Quilted layers", (), optional=True)
    ladder = quilt_ladder(layers, geometry)
    lines = (
        Line(f"{layers} quilted layers, R-{ladder.added_r:.0f} added",
             ladder.sqft * layers, "sq ft", ladder.usd_per_sqft_layer,
             "park_model quilt_usd_per_sqft_layer"),
    )
    # Not optional once layers have been asked for: naming a layer count IS
    # the opt-in, and a group that answered "how many?" and was then filtered
    # out by an unrelated include list is a silently wrong quote.
    return Group("quilt", "Quilted layers", lines, optional=False)


def insulation_group(geometry: SeedGeometry | None = None) -> Group:
    """The ravioli bladders and what goes in them. Optional, and priced apart.

    Off by default in the standard article: it is the upgrade a buyer adds
    when they know which climate the dome is going to, and forty sewn bladders
    is a real line of cost that should not hide inside a shell price."""
    geometry = geometry or seed_geometry()
    plan = insulation_plan(geometry)
    lines = (
        Line("sack fabric, both faces", plan.bladder_fabric_sqft, "sq ft",
             declared("bladder_fabric_usd_per_sqft"),
             "bladder_fabric_usd_per_sqft"),
        Line("zips, so a bay can be opened again",
             float(plan.triangles), "each",
             declared("bladder_zip_usd_each"), "bladder_zip_usd_each"),
        Line(f"blown fill, R-{plan.cavity_r:.0f} in the cavity",
             plan.cavity_cuft, "cu ft",
             declared("insulation_usd_per_cuft"), "insulation_usd_per_cuft"),
    )
    return Group("insulation", "Blown cavity fill", lines, optional=True)


# ----------------------------------------------------------------------
# The utility column and the interface boundary at the apex
# ----------------------------------------------------------------------

def column_rise_ft(geometry: SeedGeometry | None = None) -> float:
    """How far the column's chase runs: floor to apex, plus the stub above it.

    The column does not stop at the ceiling. It carries the services up
    through the apex and out, which is what makes the top of the dome an
    interface rather than a roof."""
    geometry = geometry or seed_geometry()
    return geometry.height_ft + declared("shell_skirt_in") / 12.0


def column_group(geometry: SeedGeometry | None = None) -> Group:
    geometry = geometry or seed_geometry()
    rise = column_rise_ft(geometry)
    lines = (
        Line("column housing and apex sleeve", 1.0, "each",
             declared("column_housing_usd"), "column_housing_usd"),
        Line("water manifold and rise from the pad", 1.0, "each",
             declared("column_manifold_usd"), "column_manifold_usd"),
        Line("drain stack and floor-port tie-in", 1.0, "each",
             declared("column_drain_usd"), "column_drain_usd"),
        Line("sub-panel, breakers and outlet ring", 1.0, "each",
             declared("column_electrical_usd"), "column_electrical_usd"),
        Line(f"service chase, floor to apex, {rise:.1f} ft", rise, "ft",
             declared("column_riser_usd_per_ft"), "column_riser_usd_per_ft"),
        Line("gasketed seal cap over the apex penetration", 1.0, "each",
             declared("seal_cap_usd"), "seal_cap_usd"),
    )
    return Group("column", "Utility column and seal cap", lines)


# ----------------------------------------------------------------------
# Sizing the machinery off the envelope
# ----------------------------------------------------------------------

@dataclass(frozen=True)
class CoolingLoad:
    """What the dome actually needs, and what size unit that rounds up to."""

    envelope_sqft: float
    ua: float
    conduction_btu: float
    internal_btu: float
    solar_btu: float

    @property
    def total_btu(self) -> float:
        return self.conduction_btu + self.internal_btu + self.solar_btu

    @property
    def unit_kbtu(self) -> float:
        step = declared("ac_sizes_kbtu")
        return step * math.ceil(self.total_btu / 1000.0 / step)


def cooling_load(geometry: SeedGeometry | None = None) -> CoolingLoad:
    """Size the air conditioner from the envelope, not from a rule of thumb.

    The dome's own insulated assembly, its own shell area and its own solar
    exposure. A square-foot rule would put a two-and-a-half ton unit on a 277
    square foot floor; this does not.
    """
    geometry = geometry or seed_geometry()
    plan = insulation_plan(geometry)
    envelope = geometry.panel_sqft + geometry.floor_decagon_sqft
    ua = envelope * plan.u_value
    conduction = ua * declared("ac_design_delta_f")
    solar = geometry.panel_sqft * declared("ac_solar_gain_btu_per_sqft")
    return CoolingLoad(
        envelope_sqft=envelope,
        ua=ua,
        conduction_btu=conduction,
        internal_btu=declared("ac_internal_gain_btu"),
        solar_btu=solar,
    )


AC_KINDS = ("window", "mini_split")
"""What kind of machine the cooling load is met with.

The load on this envelope is under four thousand BTU an hour. A window or
through-wall unit covers that for a few hundred dollars; a mini-split covers
it for a few thousand. The dome is small and the standard article ships the
small machine."""


def ac_rate(kind: str = "window") -> tuple[float, str]:
    if kind == "window":
        return declared("ac_window_usd_per_kbtu"), "ac_window_usd_per_kbtu"
    if kind == "mini_split":
        return declared("ac_usd_per_kbtu"), "ac_usd_per_kbtu"
    raise ValueError(f"ac must be one of {AC_KINDS}, not {kind!r}")


def services_group(geometry: SeedGeometry | None = None,
                   ac: str = "window") -> Group:
    """The machinery every stem cell ships with.

    Not the stove. That moved out into its own optional group, because a
    homemade steel stove dome is a nine-hundred-dollar decision about heating
    and it has no business hiding inside a line called "machinery"."""
    geometry = geometry or seed_geometry()
    load = cooling_load(geometry)
    rate, source = ac_rate(ac)
    kind = "window unit" if ac == "window" else "mini-split"
    lines = (
        Line(f"{kind}, {load.unit_kbtu:,.0f}k BTU/h "
             f"({load.total_btu:,.0f} BTU/h computed)",
             load.unit_kbtu, "1000 BTU/h", rate, source),
        Line("central light and ceiling fan", 1.0, "each",
             declared("light_fan_usd"), "light_fan_usd"),
        Line("lighting circuit and fittings", 1.0, "set",
             declared("lighting_circuit_usd"), "lighting_circuit_usd"),
    )
    return Group("services", "Light, fan and cooling", lines)


def stove_group(geometry: SeedGeometry | None = None) -> Group:
    """The metal stove dome. Optional, and off in the standard article."""
    geometry = geometry or seed_geometry()
    flue_ft = geometry.height_ft + 2.0
    lines = (
        Line("metal stove dome with cooktop", 1.0, "each",
             declared("wood_stove_usd"), "wood_stove_usd"),
        Line(f"flue, {flue_ft:.0f} ft through the shell", flue_ft, "ft",
             declared("flue_usd_per_ft"), "flue_usd_per_ft"),
        Line("heat shield and hearth", 1.0, "set",
             declared("stove_shield_usd"), "stove_shield_usd"),
    )
    return Group("stove", "Wood stove", lines, optional=True)


# ----------------------------------------------------------------------
# The polyp panels
# ----------------------------------------------------------------------

def polyp_group(count: int, routing_ft: float | None = None,
                geometry: SeedGeometry | None = None) -> Group:
    """``count`` utility panels, and the run of line that reaches them.

    A polyp hangs off the outside of the footprint and reaches back in
    through a gasketed port. Its services come from the seal cap, down the
    outside of the shell, which is why the routing is priced by the foot of
    shell it crosses rather than as a fitting.
    """
    geometry = geometry or seed_geometry()
    if count <= 0:
        return Group("polyps", "Utility panels", (), optional=True)
    if routing_ft is None:
        # From the apex, over the shell, to the rim: a quarter of the
        # circumference of the sphere the shell approximates, once per panel.
        quarter = 0.5 * math.pi * (geometry.radius_in / 12.0)
        routing_ft = quarter * count
    lines = (
        Line("panel frame and weather lid", float(count), "each",
             declared("polyp_frame_usd"), "polyp_frame_usd"),
        Line("quick-connect service tails", float(count), "each",
             declared("polyp_service_usd"), "polyp_service_usd"),
        Line("gasketed pass-through to the inside", float(count), "each",
             declared("polyp_wall_port_usd"), "polyp_wall_port_usd"),
        Line("exterior routing from the seal cap", routing_ft, "ft",
             declared("exterior_routing_usd_per_ft"),
             "exterior_routing_usd_per_ft"),
    )
    return Group("polyps", "Utility panels", lines, optional=True)


# ----------------------------------------------------------------------
# Labour
# ----------------------------------------------------------------------

def labour_hours(geometry: SeedGeometry | None = None,
                 resin: str = "boatyard", polyps: int = 0,
                 insulated: bool = False) -> tuple[tuple[str, float], ...]:
    """Every operation, in hours, derived from what there is to do."""
    geometry = geometry or seed_geometry()
    plan = shell_plan(geometry, resin)
    insulation = insulation_plan(geometry)
    triangles = insulation.triangles
    sewing = ((f"sew {triangles} insulation bladders",
               triangles * declared("bladder_labour_min_each") / 60.0),
              ) if insulated else ()
    return sewing + (
        (f"mill and fit {geometry.member_count} wedge members from "
         f"{geometry.trees_needed:.1f} trees",
         geometry.member_count * declared("frame_min_per_member") / 60.0),
        (f"assemble {triangles} panels",
         triangles * declared("panel_min_each") / 60.0),
        (f"lay up {plan.laminated_sqft:,.0f} sq ft of shell",
         plan.laminated_sqft * declared("shell_min_per_sqft") / 60.0),
        ("build and plumb the utility core", declared("column_hours")),
        (f"build {polyps} utility panels",
         polyps * declared("polyp_hours_each")),
        ("stand, fit out and commission", declared("assembly_hours")),
    )


def labour_group(geometry: SeedGeometry | None = None,
                 resin: str = "boatyard", polyps: int = 0,
                 insulated: bool = False) -> Group:
    rate = declared("labour_usd_per_hour")
    lines = tuple(
        Line(label, hours, "hours", rate, "labour_usd_per_hour")
        for label, hours in labour_hours(geometry, resin, polyps, insulated)
        if hours > 0.0
    )
    return Group("labour", "Build labour", lines)


# ----------------------------------------------------------------------
# Modules, and the seeds they make
# ----------------------------------------------------------------------

@dataclass(frozen=True)
class Panel:
    """One face of the dome, as a thing you buy and swap.

    This is what "stem cell" means in one object. The frame does not know or
    care what is in a bay: forty identical triangular openings, each closed by
    a panel that drops in and compression-fits. Change the panels and the
    building changes function without a saw coming near it.
    """

    key: str
    label: str
    usd: float
    note: str
    glazed: bool = False
    opening: bool = False
    """True if it is a way in and out rather than a wall."""

    @property
    def premium(self) -> float:
        """What this costs over the plain closed panel it replaces."""
        return max(0.0, self.usd - PLAIN_PANEL_USD)


PLAIN_PANEL_USD = 0.0
"""Filled in below, once the plain panel's own price is known."""


def plain_panel_usd(geometry: SeedGeometry | None = None) -> float:
    """What one blank bay costs: two panels and their gasket, averaged."""
    geometry = geometry or seed_geometry()
    group = envelope_group(geometry)
    count = sum(face.count for face in geometry.faces)
    return group.cost / count if count else 0.0


PANELS: tuple[Panel, ...] = (
    Panel("blank", "Blank panel", 0.0,
          "the standard bay, closed. What every dome ships with."),
    Panel("window", "Window panel", 210.0,
          "a fixed triangular light. The shape is the frame's, so there is "
          "no header and no trimming out", glazed=True),
    Panel("vent_window", "Opening window", 340.0,
          "the same light on a hinge, with a screen behind it", glazed=True),
    Panel("door", "Door panel", 620.0,
          "a bay cut to a door and its frame, at the base ring where the "
          "wall is nearly upright", opening=True),
    Panel("bay_door", "Open-bay door", 1480.0,
          "three base bays taken out and replaced by one wide opening with "
          "a roll-up door: what turns a dome into a garage", opening=True),
    Panel("skylight", "Skylight panel", 395.0,
          "a light in the upper ring, which on a dome is most of the roof",
          glazed=True),
    Panel("louvre", "Louvre panel", 260.0,
          "fixed slats and a screen: how a workshop or a gym gets air "
          "without a fan"),
    Panel("exhaust", "Exhaust panel", 290.0,
          "a blanked bay with a fan and a backdraft damper in it"),
    Panel("solar", "Solar panel bay", 330.0,
          "rails and a triangular cell array on the sunward face. Square "
          "cells waste the corners today; triangular cells are the fix and "
          "they are not on the shelf yet"),
    Panel("stove_flue", "Flue panel", 180.0,
          "a blanked bay with a lined penetration for the stove pipe"),
    Panel("acoustic", "Acoustic panel", 240.0,
          "mass-loaded and absorbent, for the bays a gym or a studio wants "
          "deadened"),
    Panel("mirror", "Mirror panel", 275.0,
          "a full-height mirror in the bay. Cheap in a gym, and a dome is "
          "already the shape that wants one"),
    Panel("serving", "Serving hatch", 780.0,
          "a counter-height opening with an awning", opening=True),
)

PANEL = {item.key: item for item in PANELS}


def panel_mix_cost(mix: dict, geometry: SeedGeometry | None = None) -> float:
    """What a named panel mix costs over a dome of blanks."""
    geometry = geometry or seed_geometry()
    total = 0.0
    for key, count in mix.items():
        total += PANEL[key].usd * count
    return total


def panel_group(mix: dict, geometry: SeedGeometry | None = None) -> Group:
    """The panels that make this dome the building it is."""
    geometry = geometry or seed_geometry()
    bays = sum(face.count for face in geometry.faces)
    used = sum(mix.values())
    lines = [
        Line(f"{PANEL[key].label}, {count} of {bays} bays", float(count),
             "bays", PANEL[key].usd, f"panel:{key}")
        for key, count in mix.items() if PANEL[key].usd > 0.0
    ]
    if used < bays:
        lines.append(Line(f"blank bays", float(bays - used), "bays", 0.0,
                          "panel:blank"))
    return Group("panels", "Snap-in panels", tuple(lines), optional=True)


@dataclass(frozen=True)
class Module:
    """One snap-in module: what it is, where it mounts, what it costs."""

    key: str
    label: str
    mount: str
    """``polyp``, ``column``, ``floor``, ``panel`` or ``apex``."""
    cost: float
    note: str
    water: bool = False
    drain: bool = False
    watts: float = 0.0

    @property
    def needs_polyp(self) -> bool:
        return self.mount == "polyp"


MODULES: tuple[Module, ...] = (
    Module("exhaust_fan", "Exhaust fan", "polyp", 180.0,
           "inline fan, hood and backdraft damper", watts=45.0),
    Module("tankless_heater", "Tankless water heater", "polyp", 520.0,
           "on-demand heater, mounted outside the footprint",
           water=True, watts=1800.0),
    Module("shower_module", "Shower module", "column", 610.0,
           "head, mixer, pan and trap on the column",
           water=True, drain=True),
    Module("sink_module", "Sink and drain", "column", 340.0,
           "sink, tap and P-trap on the column", water=True, drain=True),
    Module("grey_tank", "Grey water tank", "floor", 290.0,
           "under-floor grey tank and pump-out", drain=True),
    Module("cooktop", "Cooktop", "panel", 260.0,
           "two-burner propane or induction top", watts=1500.0),
    Module("fridge", "Fridge", "panel", 430.0,
           "compressor fridge that will run off a battery", watts=60.0),
    Module("camera_ring", "360 camera ring", "apex", 470.0,
           "camera ring sitting on top of the seal cap", watts=15.0),
    Module("interior_screen", "Interior screen", "panel", 380.0,
           "the inside display the camera ring feeds", watts=55.0),
    Module("solar_battery", "Solar and battery", "polyp", 1650.0,
           "panels, charge controller and a battery in one panel"),
    Module("serving_hatch", "Serving hatch", "panel", 780.0,
           "counter-height serving window and awning"),
    Module("prep_counter", "Prep counter", "panel", 520.0,
           "stainless counter and hand sink", water=True, drain=True),
    Module("grease_hood", "Vented grease hood", "polyp", 940.0,
           "hood, filters and make-up air", watts=300.0),
    Module("three_bay_sink", "Three-bay sink", "column", 610.0,
           "wash, rinse and sanitise", water=True, drain=True),
    Module("ad_panel", "Backlit advert panel", "panel", 118.0,
           "one lit advert face in one triangle, seen from outside",
           watts=18.0),
    Module("ad_controller", "Advert controller", "polyp", 690.0,
           "dimming, scheduling and metering for the whole face"),
    Module("roller_shutter", "Roller shutter door", "panel", 860.0,
           "the opening a storage dome is loaded through"),
    Module("shelving_bay", "Shelving bay", "floor", 145.0,
           "one bay of racking against the wall"),
    Module("dehumidifier", "Dehumidifier", "polyp", 330.0,
           "what makes a storage dome climate controlled", watts=300.0),
    Module("bunker_liner", "Bunker liner and collar", "panel", 2100.0,
           "waterproof membrane, drainage collar and backfill plate"),
    Module("bunker_vent", "Bunker ventilation", "apex", 780.0,
           "powered intake and exhaust up the apex riser", watts=120.0),
    Module("tree_saddle", "Tree saddle set", "floor", 1450.0,
           "the brackets and beams that put a pad in a tree"),
    Module("access_stair", "Access stair", "floor", 620.0,
           "the way up to a raised or treed dome"),
    Module("sauna_heater", "Sauna heater and benches", "panel", 1250.0,
           "stove, guard and two tiers of bench", watts=4500.0),
    Module("tub_liner", "Tub liner, pump and heater", "floor", 2400.0,
           "the inverted dome used as a tub", water=True, drain=True,
           watts=1500.0),
)

MODULE = {item.key: item for item in MODULES}


@dataclass(frozen=True)
class Fitout:
    """A seed: the stem cell plus a named set of modules."""

    key: str
    label: str
    shape: str
    """``hemisphere``, ``tall``, ``inverted`` or ``buried``."""
    modules: tuple[str, ...]
    polyps: int
    blurb: str
    module_counts: dict[str, int] = field(default_factory=dict)
    """How many of a module, where it is not one."""
    panels: dict[str, int] = field(default_factory=dict)
    """Which of the forty bays carry something other than a blank panel.

    This is the fit-out. Not the modules, not the fixtures -- the *panels*.
    A gym and a guest house are the same frame, the same pad and the same
    core with a different set of triangles dropped into the bays, and that
    is the entire reason one building can become another in an afternoon."""

    def count_of(self, key: str) -> int:
        return int(self.module_counts.get(key, 1))

    def module_group(self) -> Group:
        lines = tuple(
            Line(MODULE[key].label, float(self.count_of(key)), "each",
                 MODULE[key].cost, f"module:{key}")
            for key in self.modules
        )
        return Group("modules", f"{self.label} modules", lines, optional=True)

    def panel_group(self, geometry=None) -> Group:
        return panel_group(self.panels, geometry)

    @property
    def opening_bays(self) -> int:
        """How many bays are a way in or out rather than a wall."""
        return sum(count for key, count in self.panels.items()
                   if PANEL[key].opening)

    @property
    def glazed_bays(self) -> int:
        return sum(count for key, count in self.panels.items()
                   if PANEL[key].glazed)

    @property
    def module_watts(self) -> float:
        return sum(MODULE[key].watts * self.count_of(key)
                   for key in self.modules)


def _ad_panel_count() -> int:
    """One lit advert per triangle, which is what forty panels means."""
    return sum(face.count for face in seed_geometry().faces)


FITOUT_ORDER = ("stem_cell", "gym", "studio", "nursery", "guest",
                "workshop", "garage", "home", "sauna", "food", "advertiser",
                "storage", "bunker", "treehouse", "jacuzzi")
"""The catalogue, in the order the film shows it.

Secondary spaces first, on purpose. A gym, a study, a nursery, a guest room,
a workshop and a garage are what somebody already living on a homestead
actually wants, and they are the cheapest fit-outs because they are mostly
panels. The dwellings come after them, and the odd shapes after that."""


@lru_cache(maxsize=1)
def fitouts() -> tuple[Fitout, ...]:
    """Every seed this shop sells, in the order they are shown."""
    ads = _ad_panel_count()
    return (
        Fitout("stem_cell", "Stem cell", "hemisphere", (), 1,
               "The bare standard article: frame, floor, shell, panels, "
               "column, seal cap and one blank utility panel. Everything "
               "else is built on top of this."),
        Fitout("home", "Home seed", "hemisphere",
               ("shower_module", "sink_module", "grey_tank", "cooktop",
                "fridge", "tankless_heater", "camera_ring",
                "interior_screen"), 2,
               "A starter domicile: wash, cook, drain and see out. The "
               "camera ring sits on the seal cap and the screen inside "
               "shows what it sees.",
               {}, {"window": 6, "skylight": 2, "door": 1, "vent_window": 2,
                    "stove_flue": 1}),
        Fitout("food", "Food seed", "hemisphere",
               ("serving_hatch", "prep_counter", "grease_hood",
                "three_bay_sink", "fridge", "tankless_heater",
                "exhaust_fan"), 3,
               "Food-truck service in a fixed shell: a hatch to the "
               "outside, a hood, three bays of sink and a cold box.",
               {}, {"serving": 2, "window": 4, "exhaust": 2, "door": 1,
                    "louvre": 2}),
        Fitout("advertiser", "Advertiser seed", "hemisphere",
               ("ad_panel", "ad_controller", "solar_battery"), 2,
               f"Every one of the {ads} triangles is a lit advert facing "
               "out. Park it beside a highway and the shell is the "
               "product.",
               {"ad_panel": ads}),
        Fitout("storage", "Cold storage seed", "hemisphere",
               ("roller_shutter", "shelving_bay", "dehumidifier"), 1,
               "A conditioned storage building: a shutter to load "
               "through, racking, and the dehumidifier that makes the "
               "difference between a shed and a store.",
               {"shelving_bay": 6}, {"bay_door": 1, "exhaust": 2}),
        Fitout("bunker", "Bunker seed", "buried",
               ("bunker_liner", "bunker_vent", "access_stair",
                "shelving_bay"), 1,
               "The same dome, buried. The liner and collar keep the "
               "ground out; the apex riser is the only thing above grade, "
               "which is exactly what the interface boundary was for.",
               {"shelving_bay": 4}),
        Fitout("treehouse", "Treehouse seed", "treed",
               ("tree_saddle", "access_stair", "solar_battery",
                "grey_tank"), 1,
               "A pad in a tree instead of on the ground. Same dome, same "
               "port, and the services come up the trunk."),
        Fitout("sauna", "Sauna seed", "hemisphere",
               ("sauna_heater", "exhaust_fan"), 1,
               "The same frame, lined and sealed. Blank bays hold the heat "
               "in and one louvre lets it out when you are done.",
               {}, {"louvre": 1, "door": 1, "window": 1}),
        Fitout("gym", "Gym seed", "hemisphere",
               ("exhaust_fan",), 1,
               "A second building for the thing that does not fit in the "
               "house. Mirrors on the low bays, deadening on the rest, and "
               "a door wide enough to get a rack through.",
               {}, {"mirror": 5, "acoustic": 8, "window": 4, "door": 1,
                    "louvre": 2}),
        Fitout("guest", "Guest house seed", "hemisphere",
               ("shower_module", "sink_module", "grey_tank", "cooktop",
                "fridge", "tankless_heater"), 2,
               "Somewhere for people to stay that is not your sofa. The "
               "home fit-out at a smaller module count, on a pad at the "
               "other end of the property.",
               {}, {"window": 6, "skylight": 3, "door": 1,
                    "vent_window": 2}),
        Fitout("workshop", "Workshop seed", "hemisphere",
               ("exhaust_fan", "solar_battery"), 2,
               "Light, air and power, and nothing precious about the "
               "floor. Skylights do the work a strip light would, because "
               "on a dome the upper ring IS the roof.",
               {}, {"skylight": 6, "louvre": 4, "window": 3, "door": 1,
                    "solar": 4}),
        Fitout("garage", "Garage seed", "hemisphere",
               ("solar_battery",), 1,
               "One wide opening instead of three base bays, and a roll-up "
               "door across it. The frame does not care -- the ring above "
               "the opening is already carrying itself.",
               {}, {"bay_door": 1, "skylight": 4, "louvre": 3, "window": 2,
                    "solar": 4}),
        Fitout("studio", "Studio seed", "hemisphere",
               ("fridge", "exhaust_fan"), 1,
               "The room that is not in the house: a study, a den, a place "
               "to make a noise in. Acoustic bays and one good window.",
               {}, {"acoustic": 12, "window": 3, "skylight": 2, "door": 1}),
        Fitout("nursery", "Nursery seed", "hemisphere",
               ("exhaust_fan",), 1,
               "A room that attaches to the house rather than replacing "
               "it, and then becomes something else when it is grown out "
               "of. Which is the whole argument in one building.",
               {}, {"window": 5, "skylight": 3, "acoustic": 6, "door": 1}),
        Fitout("jacuzzi", "Jacuzzi seed", "inverted",
               ("tub_liner", "tankless_heater", "exhaust_fan"), 2,
               "The dome turned over and used as the vessel. The shell "
               "becomes the tub and the frame becomes its cradle."),
    )


def fitout(key: str) -> Fitout:
    for item in fitouts():
        if item.key == key:
            return item
    raise KeyError(f"no seed named {key!r}; choose from "
                   f"{', '.join(item.key for item in fitouts())}")


SHAPE_NOTE = {
    "hemisphere": "the standard 2V hemisphere",
    "tall": "the same frame, stretched upward",
    "inverted": "the same frame, turned over",
    "buried": "the same frame, bermed over",
    "treed": "the same frame, up a tree",
}
"""Five shapes, one cut list.

Worth saying plainly, because it is the manufacturing argument: a sauna, a
bunker, a tub and a treehouse are not four products. They are the same forty
panels and the same hundred and twenty members, stretched, bermed, turned over
or lifted. Nothing in :func:`seed_geometry` changes between them, which is why
nothing in the frame line of the quote changes either."""


# ----------------------------------------------------------------------
# A whole quote
# ----------------------------------------------------------------------

@dataclass(frozen=True)
class Quote:
    """One dome, costed to build and priced to sell."""

    fitout: Fitout
    resin: str
    frame_stock: str
    groups: tuple[Group, ...]
    geometry: SeedGeometry
    seam: str = "hose"
    ac: str = "window"

    def group(self, key: str) -> Group:
        for item in self.groups:
            if item.key == key:
                return item
        raise KeyError(key)

    def has(self, key: str) -> bool:
        return any(item.key == key for item in self.groups)

    @property
    def dome_groups(self) -> tuple[Group, ...]:
        """What the dome buyer pays for."""
        return tuple(g for g in self.groups if g.side == "dome")

    @property
    def pad_groups(self) -> tuple[Group, ...]:
        """What the landowner already built, and keeps."""
        return tuple(g for g in self.groups if g.side == "pad")

    @property
    def pad_cost(self) -> float:
        return sum(g.cost for g in self.pad_groups)

    @property
    def material_cost(self) -> float:
        return sum(g.cost for g in self.dome_groups if g.key != "labour")

    @property
    def labour_cost(self) -> float:
        return self.group("labour").cost if self.has("labour") else 0.0

    @property
    def labour_hours(self) -> float:
        if not self.has("labour"):
            return 0.0
        return sum(line.quantity for line in self.group("labour").lines)

    @property
    def core_cost(self) -> float:
        """What the utility core is worth as a thing on its own.

        The column, the seal cap and the machinery hung off them. This is the
        part of the dome that is not really part of the dome: it unbolts, it
        crates, and it goes into the next one. A buyer who upgrades their
        shell in ten years does not buy a second one of these."""
        total = 0.0
        for key in ("column", "services"):
            if self.has(key):
                total += self.group(key).cost
        return total

    @property
    def core_share(self) -> float:
        """How much of the dome's materials walk to the next dome."""
        return self.core_cost / self.material_cost if self.material_cost else 0.0

    @property
    def direct_cost(self) -> float:
        return self.material_cost + self.labour_cost

    @property
    def overhead(self) -> float:
        return self.direct_cost * declared("shop_overhead_fraction")

    @property
    def warranty(self) -> float:
        return self.direct_cost * declared("warranty_reserve_fraction")

    @property
    def cost_to_build(self) -> float:
        """What it costs this shop to put one on a trailer."""
        return self.direct_cost + self.overhead + self.warranty

    @property
    def price(self) -> float:
        """The list price at the declared margin.

        Margin is taken on price, not on cost, because that is how a margin
        is quoted: at 35 percent the price is cost divided by 0.65, not cost
        times 1.35. The two differ by eight percent of the price and the
        difference is the whole profit on a shell."""
        margin = declared("gross_margin_fraction")
        margin = min(max(margin, 0.0), 0.95)
        return self.cost_to_build / (1.0 - margin)

    @property
    def gross_profit(self) -> float:
        return self.price - self.cost_to_build

    @property
    def delivered_price(self) -> float:
        return self.price + declared("freight_usd")

    @property
    def price_per_sqft(self) -> float:
        return self.price / self.geometry.floor_decagon_sqft

    def rows(self) -> tuple[tuple[str, float], ...]:
        """Group totals, for a panel that has no room for every line."""
        return tuple((g.label, g.cost) for g in self.dome_groups if g.lines)


STANDARD_OPTIONS: tuple[str, ...] = ("polyps", "modules", "panels")
"""Which optional groups the standard article ships with.

The seam duct is NOT in it, and that is the owner's own call: the channel is
real and the arithmetic is real, but the airflow is an experiment being run
rather than a result being reported, and a standard price should not carry
something that is still being proved.

The quilt and the wood stove are not in it either. They are what an
owner adds once they know the climate and the fuel, and a standard price that
quietly includes them is a standard price nobody can compare against
anything."""


def quote(fitout_key: str = "stem_cell", *, resin: str = "boatyard",
          frame_stock: str = "customer_trees", seam: str = "hose",
          ac: str = "window", polyps: int | None = None, quilt: int = 0,
          shell: str = "hard",
          include: tuple[str, ...] | None = STANDARD_OPTIONS,
          geometry: SeedGeometry | None = None) -> Quote:
    """Price one dome.

    ``include`` names the optional groups to keep. The default is
    :data:`STANDARD_OPTIONS` -- what the standard article ships with -- and
    ``None`` keeps every optional group, which is the fully loaded dome.
    Everything not marked optional is mandatory, because a dome without a
    shell is not a cheaper dome.

    The pad group is always built and always carried, but it sits on the
    *pad* side: it is in the quote so the whole picture is visible, and it is
    out of the dome's price because a dome buyer does not pay for it.

    ``shell`` picks the skin. ``"hard"`` is the default and the best case: a
    laminated hull, a fifty-year object, and what the standard article ships
    with. ``"soft"`` is the shower-cap stack -- cheaper to buy and, unlike a
    hull, able to grow a layer at a time -- and it replaces both the hull and
    the bay panels, because the cap carries its own. See :mod:`soft_shell`.
    """
    if shell not in ("hard", "soft"):
        raise ValueError(f"shell must be 'hard' or 'soft', not {shell!r}")
    geometry = geometry or seed_geometry()
    spec = fitout(fitout_key)
    polyp_count = spec.polyps if polyps is None else int(polyps)

    # The cap carries its own outer panels, so a soft-shelled dome buys one
    # group where a hard-shelled one buys two.
    soft = shell == "soft"
    groups = [
        frame_group(geometry, frame_stock, seam),
    ]
    if soft:
        groups.append(soft_shell_group(quilt))
    else:
        groups.append(envelope_group(geometry))
        groups.append(shell_group(geometry, resin))
    groups += [
        column_group(geometry),
        services_group(geometry, ac),
        stove_group(geometry),
        paint_group(geometry),
        solar_group(geometry=geometry),
        insulation_group(geometry),
        quilt_group(quilt, geometry),
        airflow_group(geometry),
        polyp_group(polyp_count, geometry=geometry),
        spec.panel_group(geometry),
        spec.module_group(),
        labour_group(geometry, resin, polyp_count,
                     insulated=include is None or "insulation" in (include or ())),
        pad_group(geometry),
    ]
    if include is not None:
        keep = set(include)
        groups = [g for g in groups if not g.optional or g.key in keep]
    return Quote(fitout=spec, resin=resin, frame_stock=frame_stock,
                 groups=tuple(g for g in groups if g.lines), geometry=geometry,
                 seam=seam, ac=ac)


def cheapest_quote(geometry: SeedGeometry | None = None) -> Quote:
    """The floor: the bare stem cell, cheapest laminate, no optional groups.

    The lowest this product goes without ceasing to be the product."""
    return quote("stem_cell", resin="boatyard", frame_stock="customer_trees",
                 polyps=0, include=(), geometry=geometry)


# ----------------------------------------------------------------------
# What a wedge does to a tree
# ----------------------------------------------------------------------

@dataclass(frozen=True)
class Harvest:
    """One trunk, converted two ways, and what is left on the ground."""

    solid_bf: float
    wedge_bf: float
    dimensional_bf: float

    @property
    def wedge_recovery(self) -> float:
        return self.wedge_bf / self.solid_bf if self.solid_bf else 0.0

    @property
    def dimensional_recovery(self) -> float:
        return self.dimensional_bf / self.solid_bf if self.solid_bf else 0.0

    @property
    def advantage(self) -> float:
        """How many times more of the tree a wedge takes."""
        return (self.wedge_recovery / self.dimensional_recovery
                if self.dimensional_recovery else 0.0)

    @property
    def wasted_bf(self) -> float:
        """What squaring a round log throws away that splitting does not."""
        return self.wedge_bf - self.dimensional_bf


# One open-bay door is priced as three base bays taken out, and
# ``seed_world.BAY_DOOR_FACES`` draws it across three. Counting it as one
# panel would make the caption disagree with both.
PANEL_BAYS: dict[str, int] = {"bay_door": 3}


def bays_changed(fitout: str = "stem_cell") -> int:
    """How many of the forty openings a fit-out actually alters."""
    spec = globals()["fitout"](fitout)
    return sum(count * PANEL_BAYS.get(key, 1)
               for key, count in spec.panels.items())


def soft_shell_group(layers: int = 0) -> Group:
    """The shower cap, as a drop-in replacement for the hull *and* the bays.

    It replaces both, which is the thing to keep hold of when comparing: the
    cap stack carries its own outer panels, so a dome that buys a cap does
    not also buy the bay sandwich. Priced in :mod:`soft_shell`.
    """
    import soft_shell as soft

    built = soft.soft_shell(layers)
    lines = [Line(line.label, line.quantity, line.unit, line.unit_cost,
                  f"soft_shell.{line.source}") for line in built.lines]
    return Group("shell", "Shower-cap shell", tuple(lines))


# ----------------------------------------------------------------------
# Deferment: what "it works, barely" actually buys
# ----------------------------------------------------------------------

@dataclass(frozen=True)
class Rung:
    """One step of the upgrade ladder, and what you have when you stop there.

    The product is not a dome, it is a dome you are allowed to stop building.
    Every rung is a place a buyer can live indefinitely, which is a stronger
    claim than "modular" and a harder one to design for: it means no rung may
    require the next one to be weathertight, safe or legal.
    """

    key: str
    label: str
    adds: str
    lives_here: str
    groups: tuple[str, ...]
    quilt_layers: int = 0

    def cost(self, priced: "Quote | None" = None, soft: bool = False
             ) -> float:
        """What this rung costs to reach.

        ``soft`` swaps the laminated hull and the bay sandwich for the
        shower-cap stack, which is the configuration the deferment argument
        actually depends on: a hull cannot be bought a layer at a time.
        """
        priced = priced or quote()
        skip = {"shell", "envelope"} if soft else set()
        total = sum(g.cost for g in priced.groups
                    if g.key in self.groups and g.side == "dome"
                    and g.key not in skip)
        if soft:
            total += soft_shell_group(self.quilt_layers).cost
        elif self.quilt_layers:
            total += quilt_group(self.quilt_layers).cost
        return total


DEFERMENT_LADDER: tuple[Rung, ...] = (
    Rung("shelter", "Shelter",
         "frame, outer panels, membrane, cap, tie-downs",
         "Dry, lockable, unheated, unplumbed. A workshop or a dry store, "
         "and a place to sleep in a mild season. This is the rung the "
         "campaign is actually selling.",
         ("frame", "envelope", "shell")),
    Rung("serviced", "Serviced",
         "the utility column, sub-panel, light and fan",
         "Power and light. Still no water, still no heating beyond a plug-in "
         "heater. The difference between camping and living somewhere.",
         ("frame", "envelope", "shell", "column", "services")),
    Rung("plumbed", "Plumbed",
         "manifold, fixture tails, drain stack and the shower tray",
         "A bathroom. This is the rung that makes it a dwelling in most "
         "jurisdictions, and the one most likely to need an inspection.",
         ("frame", "envelope", "shell", "column", "services", "polyps")),
    Rung("warm", "Warm",
         "quilted layers, one at a time, and a bigger cap for each",
         "A winter house. Bought over years out of a waste stream rather "
         "than in one cheque, which is the whole reason the cap is soft.",
         ("frame", "envelope", "shell", "column", "services", "polyps"),
         quilt_layers=7),
)


def ladder_costs(soft: bool = False
                 ) -> tuple[tuple[Rung, float, float], ...]:
    """Each rung, what it costs to reach, and the step up from the last."""
    priced = quote()
    out, previous = [], 0.0
    for rung in DEFERMENT_LADDER:
        total = rung.cost(priced, soft=soft)
        out.append((rung, total, total - previous))
        previous = total
    return tuple(out)


# ----------------------------------------------------------------------
# The joint: bought once, at the size of the dome after next
# ----------------------------------------------------------------------

@dataclass(frozen=True)
class Joint:
    """How one triangle is fastened to the next, and why it is oversized.

    The first build screws triangle frames together. That is deliberately not
    the clever answer -- a demountable strut is the clever answer and it is a
    later problem -- but the *hardware* is chosen now for the later one, so
    that upgrading a dome does not mean re-buying every fastener in it.
    """

    name: str
    detail: str
    per_joint: float
    why_oversized: str


def joint_hardware() -> tuple[Joint, ...]:
    steps = declared("hardware_size_steps")
    over = declared("hardware_oversize_fraction")
    return (
        Joint("Threaded insert",
              "A stainless insert driven into the side face of each wedge, "
              "on the centreline, at the two points where the neighbouring "
              "triangle's members cross it. The insert takes the thread so "
              "the wood never does, which is what lets a joint be undone and "
              "remade without chewing out.",
              2.0,
              "An insert is sized by the bolt it accepts, not by the member "
              "it sits in, so the same insert serves every dome size."),
        Joint("Bolt through the side",
              "A stainless bolt passed through the adjacent member's web and "
              "into that insert. Triangle to triangle, from outside, with a "
              "driver -- no jig, no clamping, and it comes apart in the same "
              "order it went together.",
              2.0,
              f"Cut {over * 100:.0f}% longer than this dome needs, so the "
              f"same bolt reaches through the thicker members of the next "
              f"{steps:.0f} sizes up. The extra length costs pennies now and "
              "saves re-buying 240 fasteners later."),
        Joint("Washer and nyloc",
              "A wide washer to spread the pull into the wedge's sawn face, "
              "and a nylon-insert nut so a building that moves in the wind "
              "does not slowly undo itself.",
              2.0,
              "Sized to the bolt, so it inherits the same oversizing."),
    )


def joints_per_dome() -> float:
    """How many triangle-to-triangle joints there are to make."""
    return float(seed_geometry().member_count)


def fasteners_per_dome() -> float:
    """Every discrete piece of stainless in the frame."""
    return joints_per_dome() * sum(j.per_joint for j in joint_hardware())


def deferment_report() -> str:
    lines = ["DEFERMENT LADDER  (shower cap)", ""]
    for rung, total, step in ladder_costs(soft=True):
        lines.append(f"  {rung.label:<10} ${total:>8,.0f}  (+${step:,.0f})")
        lines.append(f"    adds: {rung.adds}")
        lines.append(f"    {rung.lives_here}")
        lines.append("")
    lines.append("THE JOINT")
    for joint in joint_hardware():
        lines.append(f"  {joint.name} x{joint.per_joint:.0f} per joint")
        lines.append(f"    {joint.detail}")
        lines.append(f"    oversized because: {joint.why_oversized}")
    lines.append(f"  {joints_per_dome():.0f} joints, "
                 f"{fasteners_per_dome():.0f} pieces of stainless")
    return "\n".join(lines)


def validate_deferment() -> None:
    """The ladder has to be a ladder, and the hardware has to be oversized."""
    assert len(DEFERMENT_LADDER) >= 4
    priced = quote()
    keys = {g.key for g in priced.groups}
    seen: set[str] = set()
    previous = 0.0
    for rung, total, step in ladder_costs():
        # Every rung names real groups.
        for key in rung.groups:
            assert key in keys, (rung.key, key)
        # And every rung contains the one below it, or it is not a ladder.
        assert seen <= set(rung.groups), (rung.key, seen - set(rung.groups))
        seen = set(rung.groups)
        # Each rung costs more than the last, and the step is real money.
        assert total > previous, (rung.key, total, previous)
        assert step > 0.0, rung.key
        previous = total
        assert rung.adds and rung.lives_here

    # The soft ladder has to be a ladder too, and cheaper at every rung --
    # that is the reason the cap exists.
    for (_r, hard, _s), (_r2, soft_total, _s2) in zip(ladder_costs(),
                                                      ladder_costs(True)):
        assert soft_total < hard, (soft_total, hard)

    # The first rung has to be genuinely cheap, or "it works, barely" is a
    # slogan rather than a price.
    first = ladder_costs(soft=True)[0][1]
    assert first < priced.price * 0.55, (
        f"the shelter rung is ${first:,.0f} against a list of "
        f"${priced.price:,.0f}; deferment has to start lower than that")

    assert declared("hardware_oversize_fraction") > 0.0
    assert declared("hardware_size_steps") >= 2.0
    assert len(joint_hardware()) >= 3
    assert fasteners_per_dome() > joints_per_dome()


def trees_against_mitred() -> float:
    """How many trees this dome takes against a shared-strut one. Below 1 wins.

    The film makes two claims about wood that sound like they disagree: a
    split log yields ~1.95x what a milled one does, and the pinwheel needs
    ~1.80x the stock of a dome that shares its struts. They are about
    different things -- conversion and member count -- and the honest answer
    is what happens when you put them together, which is that splitting wins
    by a margin small enough to state out loud rather than lean on.
    """
    return seed_geometry().pinwheel_stock_penalty / harvest().advantage


# ----------------------------------------------------------------------
# The core, component by component, and what it plugs into
# ----------------------------------------------------------------------

@dataclass(frozen=True)
class Part:
    """One orderable object in the utility core or on the pad.

    The quote's core line says "sub-panel, breakers and outlet ring, $310".
    That is the right granularity for a price and the wrong one for a buyer,
    who wants to know whether that is one breaker or six and whether they
    own it or the landowner does. This is that level.
    """

    service: str          # power | water | drain | air | structure
    name: str
    detail: str
    owner: str            # "dome" or "pad"
    connects_to: str      # the part on the other side of the joint


CORE_PARTS: tuple[Part, ...] = (
    # -- structure -----------------------------------------------------
    Part("structure", "Column housing",
         "A 12 in square insulated chase standing on the floor port and "
         "rising to the apex. Everything below is inside it, which is why "
         "one cover panel gets you at all of it.",
         "dome", "the floor port in the pad's deck"),
    Part("structure", "Apex sleeve",
         "A flanged collar laminated into the shell's apex ring. The chase "
         "lands in it and is gasketed to it; it is the only penetration in "
         "the weather surface.",
         "dome", "the seal cap above and the column housing below"),
    Part("structure", "Seal cap",
         "A gasketed lid over the apex sleeve with six over-centre "
         "catches. Meant to stay shut for years and come off in ten "
         "minutes. Under it is where an added service leaves the building.",
         "dome", "the apex sleeve, and any exterior run to a utility panel"),

    # -- power ---------------------------------------------------------
    Part("power", "Feeder tail and inlet",
         "A 50 A four-wire cord from the pad's pedestal to a recessed inlet "
         "at the base of the column. It unplugs; that is what makes the "
         "dome moveable without an electrician.",
         "dome", "the pad's electrical pedestal"),
    Part("power", "Sub-panel",
         "An eight-space load centre inside the column with a 50 A main. "
         "The dome's own distribution starts here and nothing upstream of "
         "it belongs to the dome owner.",
         "dome", "the feeder inlet below it"),
    Part("power", "Branch breakers",
         "Four: outlet ring, lighting, the window unit, and one spare that "
         "exists so the first snap-in module does not need a panel change.",
         "dome", "the sub-panel busbar"),
    Part("power", "Outlet ring",
         "A circuit around the base ring with receptacles between the "
         "wedges, run in the seam channel rather than through a panel.",
         "dome", "its breaker, and the seam channel it lies in"),
    Part("power", "Lighting circuit",
         "One drop at the apex for the central light and fan, taken off "
         "the chase where it is already vertical.",
         "dome", "its breaker, and the light and fan at the apex"),

    # -- water ---------------------------------------------------------
    Part("water", "Riser and shutoff",
         "A single PEX rise from the pad's stub through the floor port, "
         "with a full-port shutoff at knee height. One valve isolates the "
         "whole dome.",
         "dome", "the pad's water stub under the deck"),
    Part("water", "Manifold",
         "A four-port PEX manifold on the column with a valve per port, so "
         "a fixture can be added or isolated without draining anything "
         "else.",
         "dome", "the riser below it"),
    Part("water", "Fixture tails",
         "Capped stubs off the manifold. A dome with no plumbing still "
         "ships with these, because the alternative is opening the chase "
         "later.",
         "dome", "the manifold, and whatever fixture gets added"),

    # -- drain ---------------------------------------------------------
    Part("drain", "Trap and stack",
         "A 2 in stack down the column with a trap at its foot, taking "
         "whatever the fixture tails eventually feed.",
         "dome", "the floor port's drain side"),
    Part("drain", "Floor-port tie-in",
         "The gasketed boot where the stack passes through the deck into "
         "the pad's drain. Made once, by the host, and not disturbed when "
         "a dome is swapped.",
         "dome", "the pad's drain connection"),

    # -- air -----------------------------------------------------------
    Part("air", "Seam manifold",
         "Where the 309 ft of seam channel is gathered and capped so it "
         "can be blown or drawn. Not in the standard article -- it is the "
         "experiment the campaign is asking to fund.",
         "dome", "the seam channels, and a fan at the apex or the pad"),
)


PAD_PARTS: tuple[Part, ...] = (
    Part("power", "Electrical pedestal",
         "A 50 A RV-style pedestal on the pad edge with a breaker and a "
         "lockable cover. The host's meter is upstream of it; everything "
         "downstream is the tenant's draw.",
         "pad", "the dome's feeder tail"),
    Part("power", "Submeter",
         "Optional, and only for the two rebilling arrangements. A "
         "revenue-grade meter in the pedestal enclosure.",
         "pad", "the pedestal's supply side"),
    Part("water", "Water stub and frost valve",
         "A stub up through the deck inside the dome's footprint, fed from "
         "a frost-proof shutoff at the pad edge so the line can be drained "
         "for winter without going under the building.",
         "pad", "the dome's riser and shutoff"),
    Part("water", "Water tank",
         "120 gal under the floor. It is the host's because it stays when "
         "the dome leaves, and it is what the seam catchment would feed if "
         "that experiment works.",
         "pad", "the water stub, and the seam catchment if fitted"),
    Part("drain", "Drain connection",
         "A 2 in stub to the pad's greywater or sewer, terminating in the "
         "same floor port. Capped when no dome is on the pad.",
         "pad", "the dome's floor-port tie-in"),
    Part("structure", "Service port",
         "One framed opening through the deck, about 14 in square, that "
         "power, water and drain all come up through. The single opening "
         "is the design: a dome lands over it and three services are "
         "connected in one place.",
         "pad", "the base of the dome's column housing"),
    Part("structure", "Under-floor storage",
         "The rest of the void the piers create, boarded and hatched. It "
         "is the host's and it is the reason a framed deck beats a slab "
         "for anything but thermal mass.",
         "pad", "the deck above it"),
)


def core_parts(service: str | None = None) -> tuple[Part, ...]:
    """The dome's own hardware, optionally one service at a time."""
    if service is None:
        return CORE_PARTS
    return tuple(p for p in CORE_PARTS if p.service == service)


def pad_parts(service: str | None = None) -> tuple[Part, ...]:
    """The host's hardware, optionally one service at a time."""
    if service is None:
        return PAD_PARTS
    return tuple(p for p in PAD_PARTS if p.service == service)


SERVICES: tuple[str, ...] = ("power", "water", "drain", "air", "structure")


def interfaces() -> tuple[tuple[str, str, str], ...]:
    """Every joint where the dome's hardware meets the host's.

    Four, and that is the whole point: a dome arriving on a pad is four
    connections and a lift, not a trade call-out.
    """
    return (
        ("power", "50 A feeder tail -> pedestal",
         "unplugs; no electrician to move the dome"),
        ("water", "PEX riser -> water stub",
         "one shutoff isolates the building"),
        ("drain", "2 in stack -> drain connection",
         "gasketed boot, made once by the host"),
        ("structure", "column base -> service port",
         "all three of the above arrive through this one opening"),
    )


def hardware_report() -> str:
    """The core and the pad, component by component, as text."""
    lines = ["UTILITY CORE -- what the dome owner gets", ""]
    for service in SERVICES:
        parts = core_parts(service)
        if not parts:
            continue
        lines.append(f"  {service.upper()}")
        for part in parts:
            lines.append(f"    - {part.name}")
            lines.append(f"        {part.detail}")
            lines.append(f"        connects to: {part.connects_to}")
        lines.append("")
    lines.append("THE PAD -- what the host builds and keeps")
    lines.append("")
    for service in SERVICES:
        parts = pad_parts(service)
        if not parts:
            continue
        lines.append(f"  {service.upper()}")
        for part in parts:
            lines.append(f"    - {part.name}")
            lines.append(f"        {part.detail}")
            lines.append(f"        connects to: {part.connects_to}")
        lines.append("")
    lines.append("THE FOUR JOINTS")
    for service, joint, why in interfaces():
        lines.append(f"    {service:<10} {joint:<38} {why}")
    return "\n".join(lines)


def validate_hardware() -> None:
    """The component list has to describe the thing the quote prices."""
    assert len(CORE_PARTS) >= 12, len(CORE_PARTS)
    assert len(PAD_PARTS) >= 6, len(PAD_PARTS)
    for part in CORE_PARTS + PAD_PARTS:
        assert part.service in SERVICES, part.name
        assert part.detail and part.connects_to, part.name
        assert part.owner in ("dome", "pad"), part.name
    assert all(p.owner == "dome" for p in CORE_PARTS)
    assert all(p.owner == "pad" for p in PAD_PARTS)

    # Every service the core carries has to be met on the pad side, or the
    # dome arrives with a tail that plugs into nothing.
    core_services = {p.service for p in CORE_PARTS} - {"air"}
    pad_services = {p.service for p in PAD_PARTS}
    assert core_services <= pad_services, core_services - pad_services

    # The claim the brief makes: four joints, and only four.
    assert len(interfaces()) == 4, len(interfaces())

    # The apex has to stay the one hole in the weather surface.
    apex = [p for p in CORE_PARTS if "apex" in p.name.lower()
            or "seal cap" in p.name.lower()]
    assert len(apex) == 2, [p.name for p in apex]


def heaviest_piece(laminate: str = "boatyard") -> tuple[str, float]:
    """The heaviest single object a disassembled dome comes apart into.

    Anything claiming the dome breaks down into pieces of a given size is
    making a claim about *this* number, and it is a shell slice every time --
    a frame member is a dozen pounds and a panel is under fifty. It lives here
    so the claim and the number cannot drift apart; the pitch film's selftest
    checks its narration against it.
    """
    plan = shell_plan(None, laminate)
    slices = max(1.0, declared("shell_halves"))
    return (f"one of {slices:.0f} shell slices", plan.weight_lb / slices)


def harvest() -> Harvest:
    """What splitting gets out of a trunk against what milling does.

    Both numbers are :mod:`two_v_demo.wedge_geometry`'s, computed off one real
    tapered pine: it packs the same bucked sections both ways and counts what
    comes out. A wedge is the log minus the saw kerf, because nothing is
    squared; a 2x4 is whatever rectangles fit inside a circle, which is not
    most of it.
    """
    from two_v_demo import wedge_geometry

    yield_ = wedge_geometry.tree_yield()
    return Harvest(solid_bf=yield_.solid_bf, wedge_bf=yield_.wedge_bf,
                   dimensional_bf=yield_.two_by_four_bf)


# ----------------------------------------------------------------------
# Solar, storage, and the paint that throws heat at the sky
# ----------------------------------------------------------------------

@dataclass(frozen=True)
class SolarPlan:
    """An array, a bank and an inverter, sized and priced."""

    panel_watts: float
    battery_kwh: float
    inverter_watts: float
    sun_hours: float
    derate: float
    demand_kwh_per_day: float

    @property
    def daily_kwh(self) -> float:
        return self.panel_watts / 1000.0 * self.sun_hours * self.derate

    @property
    def yearly_kwh(self) -> float:
        return self.daily_kwh * 365.0

    @property
    def covers(self) -> float:
        """Share of the dome's own draw the array makes."""
        return (self.daily_kwh / self.demand_kwh_per_day
                if self.demand_kwh_per_day else 0.0)

    @property
    def autonomy_days(self) -> float:
        """How long the bank runs the dome with no sun at all."""
        return (self.battery_kwh / self.demand_kwh_per_day
                if self.demand_kwh_per_day else 0.0)

    @property
    def days_to_refill(self) -> float:
        """How long the array takes to put the bank back, from empty."""
        return self.battery_kwh / self.daily_kwh if self.daily_kwh else 0.0

    def rows(self) -> tuple[tuple[str, float], ...]:
        return (
            (f"{self.panel_watts:,.0f} W of panel",
             self.panel_watts * declared("solar_usd_per_watt_diy")),
            (f"{self.battery_kwh:,.0f} kWh of battery",
             self.battery_kwh * declared("battery_usd_per_kwh")),
            (f"{self.inverter_watts / 1000.0:,.1f} kW inverter",
             self.inverter_watts / 1000.0 * declared("inverter_usd_per_kw")),
        )

    @property
    def total_usd(self) -> float:
        return sum(amount for _label, amount in self.rows())


def solar_plan(panel_watts: float | None = None,
               battery_kwh: float | None = None,
               geometry: SeedGeometry | None = None) -> SolarPlan:
    """Size an off-grid set for this dome, against its own measured draw.

    The demand is not a guess: it is the dome's own heating and cooling year
    from :func:`running_year`, plus the lighting and fan the standard article
    ships, divided over 365 days. Sizing an array against a made-up load is
    how people end up with a bank they cannot fill.
    """
    geometry = geometry or seed_geometry()
    year = running_year(geometry)
    # Lights and the ceiling fan, running the hours somebody is awake.
    household_kwh = 1.4 * 365.0
    demand = (year.total_kwh + household_kwh) / 365.0
    return SolarPlan(
        panel_watts=(declared("solar_panel_watts") if panel_watts is None
                     else float(panel_watts)),
        battery_kwh=(declared("battery_kwh") if battery_kwh is None
                     else float(battery_kwh)),
        inverter_watts=declared("inverter_watts"),
        sun_hours=_park_declared("sun_hours_per_day"),
        derate=declared("solar_derate"),
        demand_kwh_per_day=demand,
    )


def _park_declared(name: str) -> float:
    """One of the park model's declared rates, borrowed by name."""
    import park_model

    return park_model.declared(name)


def solar_group(panel_watts: float | None = None,
                battery_kwh: float | None = None,
                geometry: SeedGeometry | None = None) -> Group:
    """The off-grid set, as an optional group on the quote."""
    plan = solar_plan(panel_watts, battery_kwh, geometry)
    lines = tuple(
        Line(label, 1.0, "set", amount, "solar")
        for label, amount in plan.rows()
    )
    return Group("solar", "Solar and storage", lines, optional=True)


@dataclass(frozen=True)
class CoolingPaint:
    """What a radiative coating is worth on this shell, and why it compounds.

    Two separate effects, and the film has to keep them apart:

    **The shape.** A dome of this floor area has less skin than a box of the
    same floor area, so it has less to lose heat through and less to gain it
    through. That is free and it is already true.

    **The paint.** A barium-sulphate radiative coating reflects almost all the
    sun *and* radiates through the atmospheric window, so a surface under a
    clear sky can sit below air temperature. That is a second, independent
    reduction on top of the first -- which is why the two multiply rather than
    add.
    """

    envelope_sqft: float
    box_envelope_sqft: float
    shell_sqft: float
    paint_usd: float
    solar_delta_f: float
    radiative_delta_f: float
    season_kwh: float
    annual_saving: float
    load_cut_btu_hr: float
    cooling_load_btu_hr: float

    @property
    def shape_reduction(self) -> float:
        """How much less skin the dome has than an equal-floor box."""
        return 1.0 - self.envelope_sqft / self.box_envelope_sqft

    @property
    def surface_swing_f(self) -> float:
        """How much cooler the painted surface runs than a dark one."""
        return self.solar_delta_f + self.radiative_delta_f

    @property
    def load_reduction(self) -> float:
        """Share of this dome's design cooling load the paint removes."""
        return (self.load_cut_btu_hr / self.cooling_load_btu_hr
                if self.cooling_load_btu_hr else 0.0)

    @property
    def compounded(self) -> float:
        """Both effects together, as a share of what a painted box would need.

        They multiply rather than add: the shape removes skin, and the paint
        removes gain through the skin that is left. Halving each of two
        independent terms is a quarter, not nothing.
        """
        return 1.0 - (1.0 - self.shape_reduction) * (1.0 - self.load_reduction)


def cooling_paint(geometry: SeedGeometry | None = None) -> CoolingPaint:
    """The paint, on this dome, out of the performance model that owns it."""
    from two_v_demo import dome_performance

    geometry = geometry or seed_geometry()
    floor = geometry.floor_decagon_sqft
    sky = dome_performance.sky_cooling(floor_sqft=floor)
    return CoolingPaint(
        envelope_sqft=dome_performance.dome_envelope().envelope_sqft,
        box_envelope_sqft=dome_performance.box_envelope().envelope_sqft,
        shell_sqft=geometry.panel_sqft,
        paint_usd=geometry.panel_sqft * declared("paint_usd_per_sqft"),
        solar_delta_f=sky.solar_delta_f,
        radiative_delta_f=sky.radiative_delta_f,
        season_kwh=sky.season_kwh_electric,
        annual_saving=sky.annual_saving,
        load_cut_btu_hr=sky.load_reduction_btu_hr,
        cooling_load_btu_hr=cooling_load(geometry).total_btu,
    )


def paint_group(geometry: SeedGeometry | None = None) -> Group:
    """Radiative cooling paint on the weather face. Optional."""
    geometry = geometry or seed_geometry()
    plan = cooling_paint(geometry)
    lines = (
        Line(f"radiative cooling coat, {plan.shell_sqft:,.0f} sq ft",
             plan.shell_sqft, "sq ft", declared("paint_usd_per_sqft"),
             "paint_usd_per_sqft"),
    )
    return Group("paint", "Radiative cooling paint", lines, optional=True)


# ----------------------------------------------------------------------
# What it costs to live in, once it is built
# ----------------------------------------------------------------------

def running_year(geometry=None):
    """A year of heating and cooling this envelope.

    Handed straight to :class:`two_v_demo.dome_performance.RunningCost`, which
    already models a degree-day year against a U-value. The only thing this
    module supplies is its own assembly -- the bladder cavity, the sheet core
    and the surface films -- and its own area. Two modules agreeing about a
    kilowatt hour is the point of borrowing rather than retyping.
    """
    from two_v_demo import dome_performance

    geometry = geometry or seed_geometry()
    plan = insulation_plan(geometry)
    assembly = dome_performance.Assembly(
        f"seed dome, R-{plan.cavity_r:.0f} bladder cavity", plan.assembly_r)
    envelope = geometry.panel_sqft + geometry.floor_decagon_sqft
    return dome_performance.RunningCost("seed dome", envelope, assembly)


# ----------------------------------------------------------------------
# Getting the price down, which is the whole brief
# ----------------------------------------------------------------------

@dataclass(frozen=True)
class Lever:
    """One single change, and what it is worth off the price."""

    key: str
    label: str
    note: str
    overrides: dict = field(default_factory=dict)
    resin: str | None = None
    frame_stock: str | None = None
    polyps: int | None = None
    seam: str | None = None
    quilt: int | None = None
    shell: str | None = None
    include: tuple | None = None


def levers() -> tuple:
    """Every way of making the stem cell cheaper, one at a time.

    Each is applied on its own against the standard stem cell, so the saving
    is that lever's and not the stack's. Several of them are real decisions
    with a cost elsewhere -- a single-layer laminate is a thinner shell, no
    stove is a colder dome -- and the note says which.
    """
    return (
        Lever("no_ac", "Ship without the cooling unit",
              "Leaves the circuit and the panel for one, so a buyer adds it "
              "in an afternoon for what a window unit costs anywhere.",
              {"ac_window_usd_per_kbtu": 0.0}),
        Lever("no_polyp", "No utility panel in the standard article",
              "The seal cap and its routing stay, so a panel can be hung on "
              "later without touching the shell.", {}, polyps=0),
        Lever("thin_panels", "Thinner pop-in panels",
              "The panels are placeholders the shell covers; they hold the "
              "envelope closed and nothing else.",
              {"hard_panel_usd_per_sqft": 1.40}),
        # "One panel a bay, not two" used to live here. It is gone because
        # the bay is no longer a sandwich: the panel moved to the outside
        # face and is screwed into inserts, so one panel is the design and
        # not an economy. A lever that saves nothing is worse than no lever,
        # because it makes the floor price look reachable by a route that
        # does not exist.
        Lever("soft_shell", "A shower cap instead of a laminated hull",
              "Outer panels, a monolithic membrane, quilted layers and a "
              "strapped rain cap in place of the boatyard laminate. Cheaper "
              "to buy and, unlike a hull, it can be added to a layer at a "
              "time. See soft_shell.py for what it gives up.",
              {}, shell="soft"),
        Lever("two_slices", "Two shell halves instead of four slices",
              "Half the S-lip seam to mould and gasket. Cheaper, and it "
              "takes two people and a trailer instead of one person and a "
              "pickup.",
              {"shell_halves": 2.0}),
        Lever("eight_slices", "Eight shell slices instead of four",
              "The other direction: one person can carry any piece of it, "
              "and you pay for twice the seam to get that.",
              {"shell_halves": 8.0}),
        Lever("painted", "Radiative cooling paint on the weather face",
              "The other direction, and it compounds with the shape: the "
              "dome already has 41% less skin than a box of the same floor, "
              "and the paint takes 15% off the gain through what is left.",
              {}, include=("polyps", "modules", "panels", "paint")),
        Lever("offgrid", "Solar and a battery",
              "The other direction: panels on the sunward bays and a bank "
              "under the floor, sized against this dome's own measured "
              "draw rather than a guess.",
              {}, include=("polyps", "modules", "panels", "solar")),
        Lever("ducted", "Cap the seam channels and run air through them",
              "The other direction. Three hundred feet of channel the "
              "dihedral angle already cut, closed into a duct, with fans "
              "either way and a catchment into the tank. An experiment, "
              "priced, and not in the standard article until it is proved.",
              {}, include=("polyps", "modules", "airflow")),
        Lever("no_seam_hose", "Solid seam keys instead of hose",
              "Cheaper per seam, and it gives up the gasket that recovers "
              "when the dome is taken apart and put back up.",
              {}, seam="rigid"),
        Lever("owner_build", "Customer assembles it, shop only makes parts",
              "Takes the standing, fit-out and commissioning hours out of "
              "the price and puts them on the buyer's weekend.",
              {"assembly_hours": 0.0, "panel_min_each": 0.0}),
        Lever("sheathed", "Sheathe the core instead of skinning it",
              "One layer of light cloth in epoxy each side rather than a "
              "mat-and-biaxial hull skin. Lighter, cheaper, and far less "
              "impact resistance -- a real trade, not a free one.",
              {}, resin="sheathed"),
        Lever("half_margin", "Half the margin",
              "Not a cost saving. It is the owner choosing to earn less per "
              "dome, and it is here so the two kinds of reduction are never "
              "confused with each other.",
              {"gross_margin_fraction": declared("gross_margin_fraction") / 2.0}),
        Lever("bought_logs", "Buy the timber instead of felling it",
              "The other direction: what the frame costs when the customer "
              "has no trees.", {}, frame_stock="wedge_log"),
        Lever("quilted", "Seven quilted layers under the shell",
              "The other direction, and the one that is meant to happen "
              "slowly: lift the shell, add a layer, put the shell back. "
              "One layer at a time, for as long as you own it.",
              {}, quilt=7),
        Lever("vinylester", "Vinyl ester hull skin",
              "The other direction: what a below-the-waterline laminate "
              "costs on a building that only has to keep rain out.",
              {}, resin="vinylester"),
    )


SAVING_LEVERS = ("no_ac", "no_polyp", "thin_panels", "soft_shell",
                 "no_seam_hose", "owner_build", "sheathed", "two_slices")
MARGIN_LEVERS = ("half_margin",)
"""Levers that lower the price without lowering a cost. Kept apart from the
saving levers and left out of the floor, because a shop that reaches its
target price by earning less has not made the dome any cheaper to make."""
"""The levers that take money out. The rest run the other way, on purpose:
a margin cut is the owner earning less, and insulation, bought timber and a
vinyl ester skin are things you pay MORE for. They share the table so the two
kinds of change can never be mistaken for one another."""


def lever_prices(geometry=None) -> tuple:
    """Each lever's own price and what it saves, ranked by saving."""
    geometry = geometry or seed_geometry()
    base = quote("stem_cell", geometry=geometry).price
    rows = []
    saved = dict(_OVERRIDES)
    try:
        for lever in levers():
            _OVERRIDES.clear()
            _OVERRIDES.update(saved)
            _OVERRIDES.update(lever.overrides)
            priced = quote(
                "stem_cell",
                resin=lever.resin or "boatyard",
                frame_stock=lever.frame_stock or "customer_trees",
                seam=lever.seam or "hose",
                polyps=lever.polyps,
                quilt=lever.quilt or 0,
                shell=lever.shell or "hard",
                include=(lever.include if lever.include is not None
                         else STANDARD_OPTIONS),
                geometry=geometry).price
            rows.append((lever, priced, base - priced))
    finally:
        _OVERRIDES.clear()
        _OVERRIDES.update(saved)
    rows.sort(key=lambda row: row[2], reverse=True)
    return tuple(rows)


def floor_price(geometry=None) -> tuple:
    """The lowest this product goes, and what it costs to build there.

    Every saving lever pulled at once, margin left alone. Below this the
    thing being sold is no longer a weathertight domicile, so this is a floor
    and not a target.
    """
    geometry = geometry or seed_geometry()
    saved = dict(_OVERRIDES)
    try:
        for lever in levers():
            if lever.key in SAVING_LEVERS:
                _OVERRIDES.update(lever.overrides)
        priced = quote("stem_cell", resin="boatyard", seam="rigid", polyps=0,
                       include=(), geometry=geometry)
        return priced.cost_to_build, priced.price
    finally:
        _OVERRIDES.clear()
        _OVERRIDES.update(saved)


def lever_report(geometry=None) -> str:
    geometry = geometry or seed_geometry()
    base = quote("stem_cell", geometry=geometry)
    out = ["HOW FAR DOWN THE STEM CELL GOES", "",
           f"  {'standard stem cell':<50} ${base.price:>9,.0f}", ""]
    for lever, priced, saving in lever_prices(geometry):
        sign = "-" if saving >= 0 else "+"
        out.append(f"  {lever.label[:50]:<50} ${priced:>9,.0f}  "
                   f"{sign}${abs(saving):>8,.0f}")
    build, price = floor_price(geometry)
    out.extend([
        "",
        f"  {'every saving lever at once':<50} ${price:>9,.0f}",
        f"  {'which costs, to build':<50} ${build:>9,.0f}",
        f"  {'per square foot of floor':<50} "
        f"${price / geometry.floor_decagon_sqft:>9,.2f}",
        "",
        "  The levers do not simply add up. Overhead, warranty and margin",
        "  are all fractions, so a dollar out of materials takes about a",
        "  dollar and eighty cents out of the price.",
    ])
    return "\n".join(out)


# ----------------------------------------------------------------------
# The pad the seed lands on
# ----------------------------------------------------------------------

def seed_pad_rows(geometry: SeedGeometry | None = None):
    """The cheapest pad that will still take a seed dome.

    One source, :func:`pad_group`, so the figure the dome park shows and the
    figure the quote shows cannot drift apart.
    """
    return tuple((line.label, line.cost)
                 for line in pad_group(geometry).lines)


def seed_pad_cost(geometry: SeedGeometry | None = None) -> float:
    return sum(amount for _label, amount in seed_pad_rows(geometry))


# ----------------------------------------------------------------------
# Reports
# ----------------------------------------------------------------------

def constants_report() -> str:
    """The input table. Printed before any dollar figure is quoted."""
    lines = ["WHAT THIS MODEL WAS TOLD", ""]
    borrowed = {name for name, _v, _u, note in external_constants()
                if note.startswith("borrowed")}
    for heading, wanted in (("Borrowed from elsewhere in this project", True),
                            ("Declared here", False)):
        lines.append(heading)
        lines.append("-" * len(heading))
        for name, value, unit, note in external_constants():
            if (name in borrowed) != wanted:
                continue
            flag = "*" if is_overridden(name) else " "
            lines.append(f"{flag}{name:<34} {declared(name):>12,.4f}  "
                         f"{unit}")
            lines.append(f"  {note}")
        lines.append("")
    lines.append("* = changed from the default in seed_prices.json")
    return "\n".join(lines)


def geometry_report(geometry: SeedGeometry | None = None) -> str:
    geometry = geometry or seed_geometry()
    plan = insulation_plan(geometry)
    lines = [
        "THE SEED DOME, MEASURED",
        "",
        f"  longest member        {geometry.long_edge_in / 12.0:>10.4f} ft",
        f"  short member          {geometry.short_edge_in / 12.0:>10.4f} ft",
        f"  across                {geometry.diameter_ft:>10.4f} ft",
        f"  tall                  {geometry.height_ft:>10.4f} ft",
        f"  floor, {geometry.base_sides}-sided       "
        f"{geometry.floor_decagon_sqft:>10.2f} sq ft",
        f"  floor, full circle    {geometry.floor_circle_sqft:>10.2f} sq ft",
        f"  base perimeter        {geometry.base_perimeter_ft:>10.2f} ft",
        "",
    ]
    for face in geometry.faces:
        lines.append(f"  {face.count:>3} {face.name} panels at "
                     f"{face.area_sqft:>7.3f} sq ft = "
                     f"{face.total_sqft:>8.2f} sq ft")
    lines.append(f"  {sum(f.count for f in geometry.faces):>3} panels total"
                 f"{'':>16}{geometry.panel_sqft:>10.2f} sq ft")
    lines.append("")
    lines.append("  Framing, two ways of counting it")
    lines.append(f"    shared struts (zip-tie method)  "
                 f"{geometry.shared_strut_count:>4} sticks, "
                 f"{geometry.shared_strut_ft:>8.2f} ft")
    lines.append(f"    pinwheel members (this dome)    "
                 f"{geometry.member_count:>4} sticks, "
                 f"{geometry.member_stock_ft:>8.2f} ft")
    lines.append(f"    the no-mitre method costs       "
                 f"{geometry.pinwheel_stock_penalty:>8.2f} x the stock")
    lines.append("")
    lines.append(f"  cavity behind the panels  {plan.cavity_cuft:>10.2f} cu ft")
    lines.append(f"  cavity R-value            R-{plan.cavity_r:<9.1f}")
    lines.append(f"  assembly R-value          R-{plan.assembly_r:<9.1f}")
    return "\n".join(lines)


def shell_report(geometry: SeedGeometry | None = None) -> str:
    """The shell, every laminate system, and the sheet finding."""
    geometry = geometry or seed_geometry()
    lines = ["THE SHELL", ""]
    for resin in laminate_keys():
        plan = shell_plan(geometry, resin)
        group = shell_group(geometry, resin)
        lines.append(f"  {resin.upper()}")
        for line in group.lines:
            lines.append(f"    {line.label[:44]:<44} "
                         f"{line.quantity:>9,.1f} {line.unit:<9} "
                         f"${line.cost:>9,.0f}")
        lines.append(f"    {'shell total':<44} {'':>9} {'':<9} "
                     f"${group.cost:>9,.0f}")
        lines.append(f"    {'per square foot of shell':<44} "
                     f"{plan.laminated_sqft:>9,.0f} {'sq ft':<9} "
                     f"${group.cost / plan.laminated_sqft:>9,.2f}")
        lines.append(f"    {'weighs':<44} {plan.weight_lb:>9,.0f} "
                     f"{'lb':<9}")
        lines.append("")

    plan = shell_plan(geometry, "boatyard")
    width = declared("shell_sheet_width_in")
    length = declared("shell_sheet_length_in")
    lines.append(f"  Can a panel be cut whole out of a "
                 f"{width:.0f} x {length:.0f} in sheet?")
    for name, fits, min_width in plan.panel_fits_sheet:
        verdict = "yes" if fits else "NO"
        lines.append(f"    {name:<6} narrowest across {min_width:>6.2f} in"
                     f"  ->  {verdict}")
    if not all(fits for _n, fits, _w in plan.panel_fits_sheet):
        lines.append("    A triangle cannot get narrower than its shortest")
        lines.append("    altitude no matter how it is turned, so the core")
        lines.append("    is sheeted across the frame and the joints are")
        lines.append("    taped, not cut panel by panel.")
    return "\n".join(lines)


def quote_report(fitout_key: str = "stem_cell", *, resin: str = "boatyard",
                 frame_stock: str = "customer_trees") -> str:
    """One quote, every line, with the inputs printed first."""
    result = quote(fitout_key, resin=resin, frame_stock=frame_stock)
    geometry = result.geometry
    out = [constants_report(), "", geometry_report(geometry), "",
           shell_report(geometry), "",
           f"QUOTE: {result.fitout.label.upper()} "
           f"({SHAPE_NOTE[result.fitout.shape]}, {resin} shell, "
           f"{frame_stock.replace('_', ' ')} frame)", ""]
    for group in result.groups:
        out.append(f"  {group.label}")
        for line in group.lines:
            out.append(f"    {line.label[:46]:<46} "
                       f"{line.quantity:>9,.1f} {line.unit:<10} "
                       f"${line.cost:>10,.0f}")
        out.append(f"    {'':<46} {'':>9} {'subtotal':<10} "
                   f"${group.cost:>10,.0f}")
        out.append("")
    out.extend([
        f"  {'materials':<46} ${result.material_cost:>32,.0f}",
        f"  {'labour, ' + format(result.labour_hours, ',.1f') + ' hours':<46} "
        f"${result.labour_cost:>32,.0f}",
        f"  {'overhead at ' + format(declared('shop_overhead_fraction') * 100, '.0f') + '%':<46} "
        f"${result.overhead:>32,.0f}",
        f"  {'warranty reserve':<46} ${result.warranty:>32,.0f}",
        f"  {'COST TO BUILD':<46} ${result.cost_to_build:>32,.0f}",
        "",
        f"  {'LIST PRICE at ' + format(declared('gross_margin_fraction') * 100, '.0f') + '% margin':<46} "
        f"${result.price:>32,.0f}",
        f"  {'gross profit':<46} ${result.gross_profit:>32,.0f}",
        f"  {'delivered, with freight':<46} ${result.delivered_price:>32,.0f}",
        f"  {'per square foot of floor':<46} ${result.price_per_sqft:>32,.2f}",
        "",
        f"  {'cheapest pad it can stand on':<46} "
        f"${seed_pad_cost(geometry):>32,.0f}",
    ])

    year = running_year(geometry)
    frame = result.group("frame").cost
    shell = result.group("shell").cost
    out.extend([
        "",
        "  TWO THINGS THIS QUOTE SAYS THAT THE BROCHURE WILL NOT",
        f"    The frame costs ${frame:,.0f} and the shell costs "
        f"${shell:,.0f}.",
        f"    The wood is {shell / frame:.0f} times cheaper than the skin "
        "over it.",
        f"    Every route to a cheaper dome runs through the resin line, "
        "not",
        "    through the timber.",
        "",
        f"    Running it costs {year.total_kwh:,.0f} kWh a year, or "
        f"${year.annual_cost:,.0f},",
        f"    at R-{year.assembly.r_value:.1f} over "
        f"{year.envelope_sqft:,.0f} sq ft of envelope.",
    ])
    return "\n".join(out)


def ladder_report() -> str:
    """Every seed, side by side, cheapest first."""
    rows = []
    for spec in fitouts():
        result = quote(spec.key)
        rows.append((result.price, spec, result))
    rows.sort(key=lambda row: row[0])
    out = ["EVERY SEED, CHEAPEST FIRST", "",
           f"  {'seed':<18} {'shape':<11} {'build':>10} {'price':>10} "
           f"{'$/sq ft':>9}  modules"]
    for _price, spec, result in rows:
        out.append(f"  {spec.label:<18} {spec.shape:<11} "
                   f"${result.cost_to_build:>9,.0f} ${result.price:>9,.0f} "
                   f"{result.price_per_sqft:>9,.2f}  {len(spec.modules)}")
    return "\n".join(out)


# ----------------------------------------------------------------------
# Proof
# ----------------------------------------------------------------------

PUBLISHED_2V_AT_6FT: tuple[tuple[str, float, float], ...] = (
    # (what, published figure, tolerance) -- Zip Tie Domes' 2V calculator,
    # run at a 6 ft "A" strut, as captured 9 December 2024.
    ("dome height, ft", 9.7083, 0.001),
    ("dome diameter, ft", 19.4165, 0.001),
    ("A strut, ft", 6.0, 0.0005),
    ("B strut, ft", 5.3059, 0.001),
    ("radius, ft", 9.7083, 0.001),
    ("circular floor, sq ft", 296.1, 0.05),
    ("ten-sided floor, sq ft", 276.99, 0.05),
    ("base perimeter, ft", 60.0, 0.01),
    ("panel area total, sq ft", 549.75, 0.02),
    ("AAA panel, sq ft", 15.588, 0.002),
    ("BAB panel, sq ft", 13.129, 0.002),
    ("all struts, ft", 369.18, 0.02),
    ("A strut count", 35.0, 0.0),
    ("B strut count", 30.0, 0.0),
    ("panel count", 40.0, 0.0),
)


def published_check(geometry: SeedGeometry | None = None
                    ) -> tuple[tuple[str, float, float, bool], ...]:
    """This model against the published calculator, figure by figure."""
    geometry = geometry or seed_geometry()
    faces = {face.name: face for face in geometry.faces}
    edges = {name: (count, length) for name, count, length
             in geometry.geodesic_edges}
    ours = {
        "dome height, ft": geometry.height_ft,
        "dome diameter, ft": geometry.diameter_ft,
        "A strut, ft": edges["A"][1] / 12.0,
        "B strut, ft": edges["B"][1] / 12.0,
        "radius, ft": geometry.radius_in / 12.0,
        "circular floor, sq ft": geometry.floor_circle_sqft,
        "ten-sided floor, sq ft": geometry.floor_decagon_sqft,
        "base perimeter, ft": geometry.base_perimeter_ft,
        "panel area total, sq ft": geometry.panel_sqft,
        "AAA panel, sq ft": faces["AAA"].area_sqft,
        "BAB panel, sq ft": faces["BAB"].area_sqft,
        "all struts, ft": geometry.shared_strut_ft,
        "A strut count": float(edges["A"][0]),
        "B strut count": float(edges["B"][0]),
        "panel count": float(sum(f.count for f in geometry.faces)),
    }
    rows = []
    for label, published, tolerance in PUBLISHED_2V_AT_6FT:
        mine = ours[label]
        rows.append((label, published, mine,
                     abs(mine - published) <= tolerance))
    return tuple(rows)


def published_report() -> str:
    out = ["AGAINST THE PUBLISHED 2V CALCULATOR, AT A SIX-FOOT A STRUT", "",
           f"  {'figure':<26} {'published':>12} {'this model':>12}  ok"]
    for label, published, mine, ok in published_check():
        out.append(f"  {label:<26} {published:>12,.4f} {mine:>12,.4f}  "
                   f"{'yes' if ok else 'NO'}")
    return "\n".join(out)


def validate_seed_model() -> None:
    """Everything this module claims, checked."""
    validate_hardware()
    import hull_laminate

    hull_laminate.validate_hull_laminate()

    # Two rows with the same name means one of them silently wins and the
    # other is a lie printed on the inputs page.
    names = [name for name, _v, _u, _n in external_constants()]
    assert len(names) == len(set(names)), \
        [n for n in names if names.count(n) > 1]

    # Every declared input has to be read by something. An input nothing
    # reads is a promise the model does not keep.
    source = Path(__file__).read_text(encoding="utf-8")
    for name in names:
        if name in ("sales_tax_fraction",):
            continue
        used = (f'"{name}"' in source
                or name in {k for k, _v, _u, _n in
                            hull_laminate.EXTERNAL_CONSTANTS})
        assert used, f"nothing reads {name}"

    geometry = seed_geometry()

    # The published calculator is an independent source. If this module and
    # that page disagree, one of them has the wrong dome.
    for label, published, mine, ok in published_check(geometry):
        assert ok, f"{label}: published {published}, computed {mine}"

    assert geometry.member_count == 120, geometry.member_count
    assert geometry.shared_strut_count == 65, geometry.shared_strut_count
    assert geometry.pinwheel_stock_penalty > 1.5, geometry.pinwheel_stock_penalty
    assert geometry.base_sides == 10, geometry.base_sides
    assert geometry.floor_decagon_sqft < geometry.floor_circle_sqft

    # The flat panels must be less than the sphere they approximate. If this
    # ever inverts, the shell area is being computed off the wrong surface.
    assert geometry.panel_sqft < geometry.spherical_sqft

    plan = shell_plan(geometry, "boatyard")
    assert plan.outer_sqft > plan.inner_sqft > geometry.panel_sqft
    assert plan.weight_lb > 100.0, plan.weight_lb
    assert plan.latches >= 6
    # The whole point of the sheet check: neither panel fits a 4x8.
    assert not any(fits for _n, fits, _w in plan.panel_fits_sheet), \
        "a 2V panel at a six-foot member cannot fit a four-foot sheet"

    # Every laminate system has to price, and the order has to be the one
    # the trade would expect: the same schedule in a dearer resin costs
    # more and weighs the same.
    shells = {key: shell_group(geometry, key).cost for key in laminate_keys()}
    assert shells["marine"] > shells["boatyard"], shells
    assert shells["vinylester"] > shells["marine"], shells
    assert (shell_plan(geometry, "sheathed").weight_lb
            < shell_plan(geometry, "boatyard").weight_lb)
    # The laminate is the shell. If the core and the fittings ever outweigh
    # the glass and resin, the wrong thing is being argued about.
    boatyard = shell_plan(geometry, "boatyard")
    assert boatyard.laminate.total_usd > shells["boatyard"] * 0.5

    load = cooling_load(geometry)
    assert 1000.0 < load.total_btu < 40000.0, load.total_btu
    assert load.unit_kbtu * 1000.0 >= load.total_btu

    for spec in fitouts():
        assert spec.shape in SHAPE_NOTE, (spec.key, spec.shape)
        result = quote(spec.key)
        assert result.material_cost > 0.0
        assert result.labour_cost > 0.0
        assert result.price > result.cost_to_build > result.direct_cost
        assert result.delivered_price > result.price
        for key in spec.modules:
            assert key in MODULE, key

    # Margin is taken on price. At 35 percent, price times 0.65 is the cost.
    stem = quote("stem_cell")
    margin = declared("gross_margin_fraction")
    assert abs(stem.price * (1.0 - margin) - stem.cost_to_build) < 1e-6

    # The floor: no optional group, the cheap laminate. It must be cheaper
    # than the same dome with everything, or "cheapest" means nothing.
    bare = cheapest_quote(geometry).price
    assert bare < quote("home", resin="vinylester", include=None).price

    # The pad is on the host's side of the fence and out of the dome price.
    assert stem.pad_cost > 0.0
    assert all(g.side == "dome" for g in stem.dome_groups)
    assert not any(g.key == "pad" for g in stem.dome_groups)
    assert stem.material_cost == sum(g.cost for g in stem.dome_groups
                                     if g.key != "labour")

    # The standard article ships without insulation or a stove, and adding
    # either has to cost money rather than quietly being in there already.
    assert not stem.has("insulation") and not stem.has("stove")
    loaded = quote("stem_cell", include=None)
    assert loaded.has("insulation") and loaded.has("stove")
    assert loaded.price > stem.price

    # The frame is the customer's trees by default, so it costs nothing and
    # the timber option costs something.
    assert stem.group("frame").cost < quote(
        "stem_cell", frame_stock="wedge_log").group("frame").cost
    assert 1.0 <= geometry.trees_needed <= 3.0, geometry.trees_needed

    # A window unit, not a mini-split, and the difference is real money.
    assert stem.ac == "window"
    assert quote("stem_cell", ac="mini_split").price > stem.price

    # The utility core is a real share of the dome and it is the part that
    # moves to the next one.
    assert 0.10 < stem.core_share < 0.50, stem.core_share
    assert stem.core_cost > 0.0

    # Overriding an input has to move the answer, or the configuration
    # interface is a decoration.
    before = quote("stem_cell").price
    set_override("labour_usd_per_hour", declared("labour_usd_per_hour") * 2.0)
    after = quote("stem_cell").price
    clear_override("labour_usd_per_hour")
    assert after > before, (before, after)
    assert abs(quote("stem_cell").price - before) < 1e-6

    assert seed_pad_cost(geometry) > 0.0

    # The seam is a real choice with a real price, and the hose runs the
    # interior edges only -- the rim has no panel on the other side of it.
    assert geometry.seam_count == 55, geometry.seam_count
    assert geometry.seam_length_ft < geometry.shared_strut_ft
    prices = {s: quote("stem_cell", seam=s).price for s in SEAMS}
    assert prices["none"] < prices["hose"], prices
    assert prices["none"] < prices["rigid"], prices

    year = running_year(geometry)
    assert year.total_kwh > 0.0 and year.annual_cost > 0.0

    # Every lever must actually move the price, and the ones that are meant
    # to save must save. A lever worth nothing is a lever that is wired to
    # a constant nothing reads.
    for lever, priced, saving in lever_prices(geometry):
        if lever.key in SAVING_LEVERS:
            assert saving > 0.0, lever.key          # takes cost out
        elif lever.key in MARGIN_LEVERS:
            assert saving > 0.0, lever.key          # takes price out, not cost
        else:
            assert saving < 0.0, lever.key          # the other direction
    build, price = floor_price(geometry)
    assert 0.0 < build < price < quote("stem_cell").price

    # Pulling levers must leave no residue: the standard quote after the
    # ladder has to be the standard quote before it.
    assert abs(quote("stem_cell").price - stem.price) < 1e-6


def main() -> int:
    load_overrides()
    print(published_report())
    print()
    print(quote_report())
    print()
    print(lever_report())
    print()
    print(ladder_report())
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
