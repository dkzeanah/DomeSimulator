"""The case for building a dome out of raw log wedges, derived rather than asserted.

Four kinds of number appear in this module and they are kept strictly apart, because
the difference between them is the whole reason to believe any of it.

**Geometry.**  Section area, second moment, section modulus, seam fold angles, member
lengths, the head-end offcut.  All of it is computed here from the cross-section and the
solved dome that :mod:`two_v_demo.raw_wedge_bridge` imports out of the simulator itself.
Nothing is typed in.

**Yield.**  Board feet and the rectangle packing come from
:mod:`two_v_demo.wedge_geometry`, which the earlier wedge lesson already uses, so the two
films cannot quote different figures for the same tree.

**Measured.**  :data:`MEASURED_CONSTANTS` is what the builder actually recorded on site:
two timed cutting sessions, the fuel and oil they took, a shelf price read off a rack,
and the diameter of the log being cut.  These are observations, not estimates, and the
film says which session each one came from.

**Assumed.**  :data:`ASSUMED_CONSTANTS` is the remainder -- the overheads on the
store-bought side that nobody times because they feel like part of life.  Every one is
declared with a reason and :func:`steps_assumptions` puts the whole table on screen
before any money is discussed.

An earlier cut of this module got a conclusion badly wrong, and the wreckage is worth
recording.  It priced cutting from invented minutes-per-operation, concluded that
milling your own lumber costs more than buying it, and stated a flat "one wedge is the
weaker stick".  Both fell over against real data.  The first was an artefact of made-up
rates.  The second was true only at the eight-inch trunk the simulator defaults to:
section modulus grows with the cube of the radius, so there is a **crossover diameter**
(:func:`crossover_diameters`) above which a raw sector is the stiffer member, and the
logs actually being cut are well above it.  Both facts are now derived and both are on
screen.
"""

from __future__ import annotations

import math
import re
from functools import lru_cache

import numpy as np

from . import raw_wedge_bridge as bridge
# TYPICAL_MITRE_SAW_MAX_DEG is shared with the hubless lesson so the two films agree
# about what a shop can actually set on a saw.
from .hubless_geometry import TYPICAL_MITRE_SAW_MAX_DEG, hubless_summary
from .wedge_geometry import (
    DEFAULT_LOG,
    SECTOR_ANGLE_DEG,
    SECTORS_PER_LOG,
    build_plan,
    section_rows,
    tree_yield,
)


LOG = DEFAULT_LOG
# One true two-by-four, the same figure the earlier wedge lesson compares against.
TWO_BY_FOUR_BF = 8.0
YIELD = tree_yield(LOG)
PLAN = build_plan()
SUMMARY = hubless_summary()

# A dressed stud and a full-dimension stick are different objects and get compared to
# the wedge separately, because using only one of them would be picking a side.
DRESSED_STUD_IN = (1.5, 3.5)
FULL_STUD_IN = (2.0, 4.0)
STUD_LENGTH_FT = 8.0


# ======================================================================
# What was actually measured
# ======================================================================

MEASURED_CONSTANTS: tuple[tuple[str, float, str, str], ...] = (
    ("session_a_wedges", 12.0, "wedges",
     "SESSION A: wedges ripped in one timed sitting."),
    ("session_a_hours", 2.0, "h",
     "SESSION A: how long that sitting took."),
    ("session_a_consumables_usd", 10.00, "USD",
     "SESSION A: fuel and bar oil burned, the only cash the job spent."),
    ("session_b_rip_feet", 42.0, "ft",
     "SESSION B: linear feet of rip cut -- six passes at seven feet."),
    ("session_b_hours", 1.0, "h",
     "SESSION B: how long that took, including one chain sharpening."),
    ("session_b_depth_in", 6.0, "in",
     "SESSION B: depth of cut those passes were taken at."),
    ("session_b_fuel_tanks", 2.0, "tanks",
     "SESSION B: chainsaw fuel tanks emptied in the hour."),
    ("session_b_oil_tanks", 2.0, "tanks",
     "SESSION B: bar oil tanks emptied in the hour."),
    ("planning_wedges", 30.0, "wedges",
     "The rate used for planning: wedges off in one afternoon. Deliberately "
     "below both measured sessions."),
    ("planning_hours", 6.0, "h",
     "Length of that afternoon."),
    ("stud_shelf_usd", 8.88, "USD",
     "Shelf price of one 2x4x16 untreated pine, read off the rack."),
    ("stud_with_tax_usd", 10.00, "USD",
     "The same stud rounded up to cover sales tax."),
    ("measured_log_diameter_in", 12.0, "in",
     "Trunk diameter the wedge-value comparison was made at. The trees run "
     "12 to 15 inches at the butt."),
    ("builder_volume_multiplier", 2.5, "x",
     "The builder's own estimate of how many two-by-fours' worth of wood is "
     "in one such wedge. The geometry below computes it independently."),
    ("used_volume_multiplier", 2.0, "x",
     "The multiplier actually used for planning -- lower than either the "
     "estimate or the computed figure, on purpose."),
    ("wedge_length_ft", 6.0, "ft",
     "Finished length of one wedge strut."),
    ("wedge_recovery_share", 0.88, "fraction",
     "Share of a trunk's board feet that survives radial splitting, measured "
     "across a whole tree."),
    ("traditional_recovery_low", 0.50, "fraction",
     "Low end of what square milling recovers from the same trunk."),
    ("traditional_recovery_high", 0.65, "fraction",
     "High end of the same."),
)

ASSUMED_CONSTANTS: tuple[tuple[str, float, str, str], ...] = (
    ("store_round_trip_miles", 40.0, "mi",
     "Round trip to the lumber yard and back."),
    ("truck_usd_per_mile", 0.55, "USD/mi",
     "Fuel plus wear on a loaded pickup, per mile."),
    ("store_run_hours", 1.5, "h",
     "One run: drive there, pick through the rack, queue, load, drive back, "
     "unload."),
    ("studs_per_load", 40.0, "studs",
     "How many sixteen-foot studs go in one truck load."),
    ("cull_share", 0.10, "fraction",
     "Boards bought and then not used: bowed, twisted, wet or split. You pay "
     "for these."),
    ("transit_damage_share", 0.03, "fraction",
     "Further loss to handling and weather between yard and site."),
    ("labour_usd_per_hour", 25.00, "USD/h",
     "Only used to price the store run's TIME. The cutting side is valued by "
     "what it produces instead, which is the honest way round for work you "
     "do on your own land."),
)

_MEASURED = {name: value for name, value, _u, _w in MEASURED_CONSTANTS}
_ASSUMED = {name: value for name, value, _u, _w in ASSUMED_CONSTANTS}


# The chain of hands a board passes through between a standing tree and a rack.
# Enumerated rather than counted from memory, because "about fifteen middle men" is
# the kind of claim that deserves a list.
MIDDLE_MEN: tuple[tuple[str, str], ...] = (
    ("timber broker", "sells the standing timber"),
    ("logging contractor", "fells and skids it"),
    ("log haulier", "trucks it to the mill yard"),
    ("log scaler", "measures and grades the log"),
    ("headrig sawyer", "breaks the log down"),
    ("edger operator", "squares the waney sides"),
    ("trimmer operator", "squares the ends"),
    ("kiln operator", "dries it to a moisture spec"),
    ("lumber grader", "stamps a grade on it"),
    ("planing mill", "surfaces four sides to dimension"),
    ("bundler", "packs and wraps a unit"),
    ("mill sales", "sells the unit"),
    ("freight broker", "books the flatbed"),
    ("distributor", "holds stock and breaks bulk"),
    ("retail yard", "sells you one stick"),
)

# Each station is (name, machine, in the sawn path?, in the wedge path?, note).
PROCESS_CHAIN: tuple[tuple[str, str, bool, bool, str], ...] = (
    ("fell and buck", "chainsaw", True, True,
     "identical in both, so it cancels"),
    ("primary breakdown", "SAWMILL", True, False,
     "wedge path splits radially with the same chainsaw"),
    ("edging", "EDGER", True, False,
     "there is no waney edge to remove from a split face"),
    ("drying and grading", "kiln / grader", True, False,
     "wedges are used green; the shell is not a graded-lumber assembly"),
    ("surfacing to dimension", "PLANING MILL", True, False,
     "the sawn faces come off the split already flat and already exact"),
    ("crosscut to length", "crosscut saw", True, True,
     "one square cut, both paths"),
    ("end joinery", "compound saw / jig", True, True,
     "sawn path measures two compound ends; wedge path cuts one butt "
     "and flush-cuts the head in place"),
)


def machines_dropped() -> tuple[str, ...]:
    """The named machines the wedge path does not need at all."""
    return tuple(
        machine for _name, machine, sawn, wedge, _note in PROCESS_CHAIN
        if sawn and not wedge and machine.isupper()
    )


# ======================================================================
# Cross-section arithmetic, from the simulator's own sector outline
# ======================================================================

def _closed_polygon(orientation: str) -> list[tuple[float, float]]:
    """The raw sector outline in LOCAL (panel-in, dome-out) inches.

    Taken straight out of the simulator so the section this film measures is the section
    the dome is built from, in the same rotation.
    """
    sim = bridge.simulator()
    config = sim.DomeConfig(wedge_orientation=orientation)
    points = list(sim._geometry_sector_local_points(config))
    # Shoelace wants a consistent winding; the sector is authored tip-first, which comes
    # out clockwise, so it is reversed when the signed area says so.
    signed = 0.0
    for i, (y0, z0) in enumerate(points):
        y1, z1 = points[(i + 1) % len(points)]
        signed += y0 * z1 - y1 * z0
    if signed < 0.0:
        points.reverse()
    return points


class Section:
    """Area, centroid and second moments of one closed cross-section polygon.

    Plain polygon integration, so it works for the raw sector in any of its four
    rotations and for a rectangle, without a special case for either.
    """

    def __init__(self, points: list[tuple[float, float]], label: str) -> None:
        self.label = label
        self.points = points
        area2 = 0.0
        cy = 0.0
        cz = 0.0
        i_yy = 0.0   # about the local Y axis: integral of z^2 dA
        i_zz = 0.0   # about the local Z axis: integral of y^2 dA
        for i, (y0, z0) in enumerate(points):
            y1, z1 = points[(i + 1) % len(points)]
            cross = y0 * z1 - y1 * z0
            area2 += cross
            cy += (y0 + y1) * cross
            cz += (z0 + z1) * cross
            i_yy += (z0 * z0 + z0 * z1 + z1 * z1) * cross
            i_zz += (y0 * y0 + y0 * y1 + y1 * y1) * cross
        self.area_in2 = area2 * 0.5
        if abs(self.area_in2) < 1.0e-12:
            raise ValueError(f"{label}: degenerate cross-section")
        self.centroid_y_in = cy / (6.0 * self.area_in2)
        self.centroid_z_in = cz / (6.0 * self.area_in2)
        # Parallel-axis back to the centroid, which is where a section modulus lives.
        self.i_yy_in4 = i_yy / 12.0 - self.area_in2 * self.centroid_z_in ** 2
        self.i_zz_in4 = i_zz / 12.0 - self.area_in2 * self.centroid_y_in ** 2

    @property
    def depth_in(self) -> float:
        zs = [z for _, z in self.points]
        return max(zs) - min(zs)

    @property
    def extreme_fibre_in(self) -> float:
        """Distance from the centroid to the furthest fibre, dome-out direction."""
        zs = [z for _, z in self.points]
        return max(abs(max(zs) - self.centroid_z_in),
                   abs(min(zs) - self.centroid_z_in))

    @property
    def section_modulus_in3(self) -> float:
        """Bending capacity about the axis that matters in a shell.

        A shell member is pushed in and out along the dome's own radius, so it bends
        in the dome-out direction and the relevant modulus is I_yy over the extreme
        fibre in that same direction.
        """
        return self.i_yy_in4 / self.extreme_fibre_in


@lru_cache(maxsize=8)
def sector_section(orientation: str = "point_dome_in") -> Section:
    return Section(_closed_polygon(orientation), orientation)


@lru_cache(maxsize=64)
def sector_at_diameter(diameter_in: float, splits: int = SECTORS_PER_LOG) -> Section:
    """One raw sector of any trunk, in the dome-in rotation.

    Closed-form for the circular sector rather than a resampled polygon, because these
    are used to solve for a crossover diameter and a polygon's small facet error would
    move the answer.
    """
    radius = diameter_in * 0.5
    half = math.pi / splits
    segments = 96
    points = [(0.0, 0.0)]
    for index in range(segments + 1):
        angle = -half + 2.0 * half * index / segments
        points.append((radius * math.sin(angle), radius * math.cos(angle)))
    points.reverse()
    return Section(points, f"sector d={diameter_in:.2f}")


@lru_cache(maxsize=4)
def rectangle_section(width_in: float, depth_in: float, label: str) -> Section:
    half_w, half_d = width_in * 0.5, depth_in * 0.5
    points = [(-half_w, -half_d), (half_w, -half_d), (half_w, half_d), (-half_w, half_d)]
    return Section(points, label)


def dressed_stud() -> Section:
    return rectangle_section(DRESSED_STUD_IN[0], DRESSED_STUD_IN[1], "dressed 2x4")


def full_stud() -> Section:
    return rectangle_section(FULL_STUD_IN[0], FULL_STUD_IN[1], "full-dimension 2x4")


def _solve_diameter(target: float, prop: str) -> float:
    """Trunk diameter at which one sector's ``prop`` equals ``target``.

    Bisection rather than the closed form, so that changing SECTORS_PER_LOG changes the
    answer instead of silently invalidating it.
    """
    low, high = 2.0, 60.0
    for _ in range(120):
        mid = (low + high) * 0.5
        if getattr(sector_at_diameter(round(mid, 6)), prop) < target:
            low = mid
        else:
            high = mid
    return (low + high) * 0.5


@lru_cache(maxsize=1)
def crossover_diameters() -> dict[str, float]:
    """Trunk diameters where one raw sector catches each kind of two-by-four.

    This is the fact that decides the whole structural argument, and it is a diameter
    rather than a yes or no. Below it the sector is the weaker member; above it, the
    stronger. Nothing else in the method changes.
    """
    dressed = dressed_stud()
    full = full_stud()
    return {
        "area_vs_dressed_in": _solve_diameter(dressed.area_in2, "area_in2"),
        "modulus_vs_dressed_in": _solve_diameter(dressed.section_modulus_in3,
                                                 "section_modulus_in3"),
        "area_vs_full_in": _solve_diameter(full.area_in2, "area_in2"),
        "modulus_vs_full_in": _solve_diameter(full.section_modulus_in3,
                                              "section_modulus_in3"),
    }


# ======================================================================
# The dome the simulator actually solves
# ======================================================================

@lru_cache(maxsize=1)
def dome_facts() -> dict[str, float]:
    """Counts and lengths straight out of the solved raw-wedge dome."""
    sim = bridge.simulator()
    model = bridge.model()
    config = model.config
    members = model.members
    seams = model.seams

    finished_in = sum(m.physical_stock_length_in for m in members)
    head_offcut_in = config.head_overfit_in * len(members)
    folds = [s.fold_angle_deg for s in seams]
    gaps = [s.raw_gap_angle_deg for s in seams]
    bases = [s.spacer_base_width_in for s in seams]

    return {
        "panels": float(len(model.topology.faces)),
        "members": float(len(members)),
        "seams": float(len(seams)),
        "joints": float(len(model.joints)),
        "trunk_diameter_in": config.trunk_diameter_in,
        "radial_splits": float(config.radial_splits),
        "sector_angle_deg": 360.0 / config.radial_splits,
        "long_edge_in": model.topology.long_edge_in,
        "short_edge_in": model.topology.short_edge_in,
        "finished_ft": finished_in / 12.0,
        "longest_member_in": max(m.physical_stock_length_in for m in members),
        "shortest_member_in": min(m.physical_stock_length_in for m in members),
        "head_overfit_in": config.head_overfit_in,
        "head_offcut_ft": head_offcut_in / 12.0,
        "head_offcut_share": head_offcut_in / (finished_in + head_offcut_in),
        "fold_min_deg": min(folds),
        "fold_max_deg": max(folds),
        "fold_spread_deg": max(folds) - min(folds),
        "gap_min_deg": min(gaps),
        "gap_max_deg": max(gaps),
        "key_base_min_in": min(bases),
        "key_base_max_in": max(bases),
        "jig_steps": float(len(sim.JIG_STAGES)),
        "jig_variants": float(_jig_variant_count()),
    }


def _jig_variant_count() -> int:
    """How many physically different fixtures forty panels actually need."""
    sim = bridge.simulator()
    model = bridge.model()
    signatures = {
        sim._panel_variant_signature(model, index)
        for index in range(len(model.topology.faces))
    }
    return len(signatures)


@lru_cache(maxsize=1)
def orientation_table() -> tuple[tuple[str, str, float, float, float], ...]:
    """(orientation, what a pair at one seam does, area, I_yy, section modulus)."""
    rows = []
    for orientation in bridge.orientations():
        section = sector_section(orientation)
        rows.append((
            orientation,
            bridge.seam_pair_reading(orientation),
            section.area_in2,
            section.i_yy_in4,
            section.section_modulus_in3,
        ))
    return tuple(rows)


# ======================================================================
# Cutting: two timed sessions, cross-checked against each other
# ======================================================================

@lru_cache(maxsize=1)
def cut_rate_model() -> dict[str, float]:
    """What the saw actually does, and whether the two sessions agree.

    The sessions were timed separately and measure different things -- one counted
    finished wedges, the other counted linear feet of cut. Dividing one by the other
    gives feet of rip per wedge, which the geometry can also predict: splitting a round
    into ``n`` sectors takes ``n - 1`` passes down its whole length. The two answers
    landing near each other is the only evidence here that either is real.
    """
    a_wedges = _MEASURED["session_a_wedges"]
    a_hours = _MEASURED["session_a_hours"]
    b_feet = _MEASURED["session_b_rip_feet"]
    b_hours = _MEASURED["session_b_hours"]

    wedges_per_hour = a_wedges / a_hours
    consumables_per_hour = _MEASURED["session_a_consumables_usd"] / a_hours
    rip_feet_per_hour = b_feet / b_hours

    measured_ft_per_wedge = rip_feet_per_hour / wedges_per_hour
    # Halve, halve again, halve again: eight sectors take seven passes, each one the
    # full length of the section.
    passes = SECTORS_PER_LOG - 1
    section_ft = b_feet / 6.0            # session B was six passes at that length
    geometric_ft_per_wedge = passes * section_ft / SECTORS_PER_LOG

    planning_rate = _MEASURED["planning_wedges"] / _MEASURED["planning_hours"]
    return {
        "wedges_per_hour": wedges_per_hour,
        "rip_feet_per_hour": rip_feet_per_hour,
        "consumables_usd_per_hour": consumables_per_hour,
        "section_ft": section_ft,
        "passes_per_section": float(passes),
        "measured_ft_per_wedge": measured_ft_per_wedge,
        "geometric_ft_per_wedge": geometric_ft_per_wedge,
        "agreement": geometric_ft_per_wedge / measured_ft_per_wedge,
        "overhead_share": 1.0 - geometric_ft_per_wedge / measured_ft_per_wedge,
        "planning_wedges_per_hour": planning_rate,
        "planning_margin": 1.0 - planning_rate / wedges_per_hour,
        "fuel_tanks_per_hour": _MEASURED["session_b_fuel_tanks"],
        "cut_depth_in": _MEASURED["session_b_depth_in"],
    }


@lru_cache(maxsize=1)
def wedge_value_model() -> dict[str, float]:
    """What one wedge strut is worth, computed two independent ways.

    The builder's rule of thumb prices a wedge as a flat multiple of a stud's
    section-price. The strict version counts the actual cross-section and scales for
    the length difference between a six-foot wedge and an eight-foot stud. The two
    should not agree as closely as they do; the conservative multiplier and the
    generous length happen to cancel.
    """
    diameter = _MEASURED["measured_log_diameter_in"]
    wedge = sector_at_diameter(diameter)
    dressed = dressed_stud()
    full = full_stud()

    usd_per_stud_section = _MEASURED["stud_with_tax_usd"] / 2.0   # a 2x4x16 is two 8s
    length_ratio = _MEASURED["wedge_length_ft"] / STUD_LENGTH_FT

    computed_multiplier = wedge.area_in2 / dressed.area_in2
    strict_usd = computed_multiplier * length_ratio * usd_per_stud_section
    rule_usd = _MEASURED["used_volume_multiplier"] * usd_per_stud_section

    return {
        "diameter_in": diameter,
        "wedge_area_in2": wedge.area_in2,
        "dressed_area_in2": dressed.area_in2,
        "full_area_in2": full.area_in2,
        "computed_multiplier": computed_multiplier,
        "computed_multiplier_full": wedge.area_in2 / full.area_in2,
        "builder_multiplier": _MEASURED["builder_volume_multiplier"],
        "used_multiplier": _MEASURED["used_volume_multiplier"],
        "usd_per_stud_section": usd_per_stud_section,
        "length_ratio": length_ratio,
        "strict_usd_per_wedge": strict_usd,
        "rule_usd_per_wedge": rule_usd,
        "disagreement": abs(strict_usd - rule_usd) / max(strict_usd, rule_usd),
    }


@lru_cache(maxsize=1)
def earnings_model() -> dict[str, float]:
    """What an afternoon of ripping is worth, at the planning rate."""
    rates = cut_rate_model()
    value = wedge_value_model()
    per_wedge = value["rule_usd_per_wedge"]
    per_hour = rates["planning_wedges_per_hour"]

    gross_per_hour = per_wedge * per_hour
    consumables = rates["consumables_usd_per_hour"]
    afternoon_wedges = _MEASURED["planning_wedges"]
    afternoon_hours = _MEASURED["planning_hours"]
    return {
        "usd_per_wedge": per_wedge,
        "wedges_per_hour": per_hour,
        "gross_usd_per_hour": gross_per_hour,
        "consumables_usd_per_hour": consumables,
        "net_usd_per_hour": gross_per_hour - consumables,
        "afternoon_wedges": afternoon_wedges,
        "afternoon_hours": afternoon_hours,
        "afternoon_gross_usd": afternoon_wedges * per_wedge,
        "afternoon_consumables_usd": afternoon_hours * consumables,
        "afternoon_net_usd": afternoon_wedges * per_wedge - afternoon_hours * consumables,
        "strict_usd_per_hour": value["strict_usd_per_wedge"] * per_hour,
        "measured_rate_usd_per_hour": per_wedge * rates["wedges_per_hour"],
    }


@lru_cache(maxsize=1)
def purchase_model() -> dict[str, float]:
    """What the same frame costs bought, with the small stuff counted.

    The comparison is by cross-section, not by piece: a wedge is thicker than a stud,
    so buying "one stud per member" would silently build a weaker dome and call it
    cheaper. What is priced here is enough dressed studs to match the section the
    wedges provide -- plus the boards you buy and then reject, the damage between yard
    and site, and the truck runs it takes to bring them home.
    """
    facts = dome_facts()
    value = wedge_value_model()
    members = facts["members"]
    wedge_ft = _MEASURED["wedge_length_ft"]

    # Studs of the same length needed to match one wedge's section, then converted to
    # the sixteen-foot sticks that are actually on the rack.
    studs_per_wedge = value["computed_multiplier"]
    stud_feet = members * wedge_ft * studs_per_wedge
    sticks_net = stud_feet / 16.0
    cull = _ASSUMED["cull_share"]
    damage = _ASSUMED["transit_damage_share"]
    sticks_bought = sticks_net / max(1.0e-6, (1.0 - cull) * (1.0 - damage))

    stick_usd = _MEASURED["stud_with_tax_usd"]
    lumber_usd = sticks_bought * stick_usd

    loads = math.ceil(sticks_bought / _ASSUMED["studs_per_load"])
    trip_miles = loads * _ASSUMED["store_round_trip_miles"]
    trip_usd = trip_miles * _ASSUMED["truck_usd_per_mile"]
    trip_hours = loads * _ASSUMED["store_run_hours"]
    trip_time_usd = trip_hours * _ASSUMED["labour_usd_per_hour"]

    rates = cut_rate_model()
    cut_hours = members / rates["planning_wedges_per_hour"]
    cut_usd = cut_hours * rates["consumables_usd_per_hour"]

    return {
        "members": members,
        "studs_per_wedge": studs_per_wedge,
        "stud_feet": stud_feet,
        "sticks_net": sticks_net,
        "sticks_bought": sticks_bought,
        "lumber_usd": lumber_usd,
        "loads": float(loads),
        "trip_miles": trip_miles,
        "trip_usd": trip_usd,
        "trip_hours": trip_hours,
        "trip_time_usd": trip_time_usd,
        "buy_cash_usd": lumber_usd + trip_usd,
        "buy_all_in_usd": lumber_usd + trip_usd + trip_time_usd,
        "cut_hours": cut_hours,
        "cut_cash_usd": cut_usd,
        "cash_saved_usd": lumber_usd + trip_usd - cut_usd,
        "all_in_saved_usd": lumber_usd + trip_usd + trip_time_usd - cut_usd,
        "cull_boards": sticks_bought - sticks_net,
        "cull_usd": (sticks_bought - sticks_net) * stick_usd,
    }


@lru_cache(maxsize=1)
def defect_model() -> dict[str, float]:
    """What one bend or one bad knot costs, short members against long ones.

    A defect does not destroy wood; it destroys whatever length has to be thrown away
    around it. That length is set by the piece you are trying to make, so the shorter
    the piece the cheaper the defect.
    """
    facts = dome_facts()
    short_ft = _MEASURED["wedge_length_ft"]
    long_ft = 16.0                     # the stick the same trunk would otherwise make
    usable_ft = LOG.usable_length_ft

    short_pieces = math.floor(usable_ft / short_ft)
    long_pieces = math.floor(usable_ft / long_ft)
    return {
        "short_ft": short_ft,
        "long_ft": long_ft,
        "usable_ft": usable_ft,
        "short_pieces": float(short_pieces),
        "long_pieces": float(long_pieces),
        "short_loss_share": short_ft / usable_ft,
        "long_loss_share": long_ft / usable_ft,
        "loss_ratio": long_ft / short_ft,
        "longest_member_ft": facts["longest_member_in"] / 12.0,
        "shortest_member_ft": facts["shortest_member_in"] / 12.0,
    }


@lru_cache(maxsize=1)
def structure_model() -> dict[str, float]:
    """The wedge against both kinds of two-by-four, at both diameters that matter."""
    dome_d = dome_facts()["trunk_diameter_in"]
    measured_d = _MEASURED["measured_log_diameter_in"]
    dome_w = sector_at_diameter(dome_d)
    real_w = sector_at_diameter(measured_d)
    dressed = dressed_stud()
    full = full_stud()
    cross = crossover_diameters()
    return {
        "dome_diameter_in": dome_d,
        "measured_diameter_in": measured_d,
        "dome_area": dome_w.area_in2,
        "dome_modulus": dome_w.section_modulus_in3,
        "real_area": real_w.area_in2,
        "real_i": real_w.i_yy_in4,
        "real_modulus": real_w.section_modulus_in3,
        "dressed_area": dressed.area_in2,
        "dressed_modulus": dressed.section_modulus_in3,
        "full_area": full.area_in2,
        "full_modulus": full.section_modulus_in3,
        "dome_area_vs_dressed": dome_w.area_in2 / dressed.area_in2,
        "dome_modulus_vs_dressed": dome_w.section_modulus_in3 / dressed.section_modulus_in3,
        "real_area_vs_dressed": real_w.area_in2 / dressed.area_in2,
        "real_modulus_vs_dressed": real_w.section_modulus_in3 / dressed.section_modulus_in3,
        "real_area_vs_full": real_w.area_in2 / full.area_in2,
        "real_modulus_vs_full": real_w.section_modulus_in3 / full.section_modulus_in3,
        "doubled_area_vs_dressed": 2.0 * real_w.area_in2 / dressed.area_in2,
        "doubled_modulus_vs_dressed": 2.0 * real_w.section_modulus_in3 / dressed.section_modulus_in3,
        "crossover_area_dressed": cross["area_vs_dressed_in"],
        "crossover_modulus_dressed": cross["modulus_vs_dressed_in"],
        "crossover_area_full": cross["area_vs_full_in"],
        "crossover_modulus_full": cross["modulus_vs_full_in"],
        "interior_edges": float(SUMMARY.doubled_edges),
        "rim_edges": float(SUMMARY.rim_edges),
        "log_fraction": 1.0 / SECTORS_PER_LOG,
    }




# ======================================================================
# The butt cut: the hardest operation in the build, and the one the
# earlier cut of this film wrongly said did not exist
# ======================================================================

@lru_cache(maxsize=8)
def butt_cut_model(orientation: str = "point_dome_in") -> dict:
    """The compound cut that lands one member's end on the next member's side.

    THIS IS A MITRE, and an earlier cut of this film said it was not. The pinwheel
    removes the *shared vertex* -- no stick is coped or shaved to a point, and no two
    ends meet each other -- but the butt end is still a compound cut, and it is the
    trickiest operation in the whole build.

    Two things come out of the solve that make it jiggable rather than hand-fitted:

    * the BEVEL is the same on every member in the dome, and equals half the sector
      angle. It is set by how the log was split, not by where the member sits in the
      shell, so it is set once and never touched again;
    * the MITRE takes only a handful of values across all 120 members.

    The cut also runs a long way along the axis, because it lands on a face that is
    itself tilted: the sector's point reaches further than its bark corner by
    ``axial_run_in``. That is why the blank has to be long on that side, and it is the
    part that gets gauged by eye when there is no fixture.
    """
    sim = bridge.simulator()
    model = bridge.model(orientation)
    local = sim._geometry_sector_local_points(model.config)

    settings: dict[tuple[float, float], int] = {}
    runs: list[float] = []
    leads: set[int] = set()
    trails: set[int] = set()
    for member in model.members:
        _, _, _, mitre, bevel = sim._cut_plane_components(member, member.butt_plane_normal)
        key = (round(mitre, 3), round(bevel, 3))
        settings[key] = settings.get(key, 0) + 1

        origin = member.nominal_start + member.point_offset_in * member.inward
        along: list[float] = []
        for (y, z), point in zip(local, member.butt_contact_points):
            generator = origin + y * member.inward + z * member.face_normal
            along.append(float(np.dot(point - generator, member.tangent)))
        runs.append(max(along) - min(along))
        leads.add(int(max(range(len(along)), key=along.__getitem__)))
        trails.add(int(min(range(len(along)), key=along.__getitem__)))

    bevels = {bevel for _mitre, bevel in settings}
    mitres = sorted({abs(mitre) for mitre, _bevel in settings})
    recipes = {sim._member_recipe_signature(member) for member in model.members}
    return {
        "orientation": orientation,
        "members": float(len(model.members)),
        "settings": tuple(sorted(
            ((mitre, bevel, count) for (mitre, bevel), count in settings.items()),
            key=lambda row: -row[2])),
        "setting_count": float(len(settings)),
        "mitres": tuple(mitres),
        "bevel_deg": float(next(iter(bevels))) if len(bevels) == 1 else float("nan"),
        "bevel_is_constant": len(bevels) == 1,
        "half_sector_deg": 180.0 / model.config.radial_splits,
        "max_mitre_deg": max(mitres),
        "within_common_saw": max(mitres) <= TYPICAL_MITRE_SAW_MAX_DEG,
        "saw_limit_deg": TYPICAL_MITRE_SAW_MAX_DEG,
        "axial_run_min_in": min(runs),
        "axial_run_max_in": max(runs),
        "lead_is_point": leads == {0},
        "trail_is_bark": trails == {len(local) - 1},
        "recipes": float(len(recipes)),
    }


@lru_cache(maxsize=1)
def orientation_features() -> tuple[dict, ...]:
    """What each of the four rotations gives the *building*, not just the stick.

    Stiffness is only one axis of the choice and it is the one already covered. These
    are the others, and each is measured off the same cross-section:

    ``lip_in``      how much further the member intrudes into the panel opening at the
                    inner surface than at the outer one. Positive means the opening
                    narrows going inward, so a panel dropped in from OUTSIDE is caught
                    like a keystone and cannot fall through. Negative means it installs
                    from inside. Zero means the opening is parallel-sided and the panel
                    is held by fasteners alone.
    ``channel_in2`` cross-section of the V that the two seam faces leave open along
                    every seam. Fill it with key and it is a joint; leave it and it is
                    a continuous conduit through the whole shell.
    ``face_tilt``   angle between a sawn radial face and the dome surface. The smaller
                    it is, the closer the frame comes to presenting flat wood for
                    sheathing on both sides.
    ``bevel_deg``   the butt cut's bevel in that rotation. One of the four turns the
                    hardest cut in the build into a plain mitre with no bevel at all.
    """
    sim = bridge.simulator()
    rows: list[dict] = []
    for orientation in bridge.orientations():
        config = sim.DomeConfig(wedge_orientation=orientation)
        points = sim._geometry_sector_local_points(config)
        zs = [z for _y, z in points]
        band = (max(zs) - min(zs)) * 0.09 + 1.0e-6
        outer = max(y for y, z in points if z >= max(zs) - band)
        inner = max(y for y, z in points if z <= min(zs) + band)

        tip = np.array(points[0], dtype=np.float64)
        first = np.array(points[1], dtype=np.float64)
        edge = first - tip
        edge = edge / np.linalg.norm(edge)
        face_tilt = math.degrees(math.acos(min(1.0, abs(float(edge[0])))))

        model = bridge.model(orientation)
        gaps = [seam.raw_gap_angle_deg for seam in model.seams]
        radius = config.trunk_diameter_in * 0.5
        # The open region between the two seam faces is a triangle: two sides of one
        # sector radius each, meeting at the included gap angle. An earlier version
        # used r^2*tan(gap/2), which is only the V's area while the gap stays acute --
        # past ninety degrees it runs away and claimed 159 cubic feet of conduit for a
        # seam that has actually splayed flat and has no channel in it at all.
        channel = [0.5 * radius * radius * math.sin(math.radians(gap)) for gap in gaps]
        seam_length_in = sum(
            float(np.linalg.norm(seam.end - seam.start)) for seam in model.seams)

        cut = butt_cut_model(orientation)
        mean_gap = sum(gaps) / len(gaps)
        rows.append({
            "is_duct": mean_gap < 90.0,
            "orientation": orientation,
            "reading": bridge.seam_pair_reading(orientation),
            "depth_in": max(zs) - min(zs),
            "lip_in": inner - outer,
            "modulus_in3": sector_section(orientation).section_modulus_in3,
            "gap_min_deg": min(gaps),
            "gap_max_deg": max(gaps),
            "channel_in2": sum(channel) / len(channel),
            "channel_ft3": sum(channel) / len(channel) * seam_length_in / 1728.0,
            "seam_length_ft": seam_length_in / 12.0,
            "face_tilt_deg": face_tilt,
            "bevel_deg": cut["bevel_deg"],
        })
    return tuple(rows)


@lru_cache(maxsize=1)
def mixed_diameter_model() -> dict:
    """A dome built from whatever the woodlot gives, not from graded matched stock.

    The film's other numbers assume one trunk diameter throughout. Real trees do not
    cooperate, so this solves the same dome at both ends of a 10 to 15 inch range and
    reports what actually moves.

    Almost nothing does. Not one angle in the shell changes -- the dihedral is a
    property of the geodesic subdivision and has never heard of the log. What changes
    is how far each member sits back from its ideal edge, and therefore how wide the
    key between two panels has to be. Both land in the one part that is already
    variable and already replaceable.
    """
    sim = bridge.simulator()
    low, high = 10.0, 15.0
    out: dict[str, float] = {"low_in": low, "high_in": high}
    per_end = {}
    for label, diameter in (("low", low), ("high", high)):
        config = sim.DomeConfig(trunk_diameter_in=diameter)
        model = sim.build_physical_model(config)
        offsets = [member.point_offset_in for member in model.members]
        stock = [member.physical_stock_length_in for member in model.members]
        keys = [seam.spacer_base_width_in for seam in model.seams]
        folds = [seam.fold_angle_deg for seam in model.seams]
        section = sector_at_diameter(diameter)
        per_end[label] = {
            "offset_min": min(offsets), "offset_max": max(offsets),
            "stock_min": min(stock), "stock_max": max(stock),
            "key_min": min(keys), "key_max": max(keys),
            "fold_min": min(folds), "fold_max": max(folds),
            "area": section.area_in2, "modulus": section.section_modulus_in3,
        }
    dressed = dressed_stud()
    cross = crossover_diameters()
    out.update({
        "fold_identical": abs(per_end["low"]["fold_min"] - per_end["high"]["fold_min"]) < 1.0e-6
        and abs(per_end["low"]["fold_max"] - per_end["high"]["fold_max"]) < 1.0e-6,
        "fold_min": per_end["low"]["fold_min"],
        "fold_max": per_end["low"]["fold_max"],
        "offset_step_in": per_end["high"]["offset_max"] - per_end["low"]["offset_max"],
        "stock_shift_in": abs(per_end["high"]["stock_max"] - per_end["low"]["stock_max"]),
        "key_low_min": per_end["low"]["key_min"], "key_low_max": per_end["low"]["key_max"],
        "key_high_min": per_end["high"]["key_min"], "key_high_max": per_end["high"]["key_max"],
        "key_span_in": per_end["high"]["key_max"] - per_end["low"]["key_min"],
        "area_low": per_end["low"]["area"], "area_high": per_end["high"]["area"],
        "modulus_low": per_end["low"]["modulus"], "modulus_high": per_end["high"]["modulus"],
        "weakest_vs_dressed_area": per_end["low"]["area"] / dressed.area_in2,
        "weakest_vs_dressed_modulus": per_end["low"]["modulus"] / dressed.section_modulus_in3,
        "crossover_in": cross["modulus_vs_dressed_in"],
        "whole_range_clears": low > cross["modulus_vs_dressed_in"],
        "surface_step_in": (high - low) * 0.5,
    })
    return out


# ======================================================================
# The screens, one step per line
# ======================================================================

def _conclude(steps: list[str], conclusion: str) -> tuple[str, ...]:
    steps.append(conclusion)
    return tuple(steps)


@lru_cache(maxsize=1)
def steps_assumptions() -> tuple[str, ...]:
    """Screen 1 -- what was measured, and what is only estimated."""
    steps = [
        "geometry, board feet and angles in this film are computed. The rest",
        "splits into two piles, and the difference matters:",
        "MEASURED ON SITE -- timed, weighed or read off a price rack:",
    ]
    for name, value, unit, _why in MEASURED_CONSTANTS:
        if unit == "fraction":
            steps.append(f"  {name:30s} {value * 100:7.1f} %")
        else:
            steps.append(f"  {name:30s} {value:7.2f} {unit}")
    steps.append("ASSUMED -- overheads nobody times, so they are estimates:")
    for name, value, unit, _why in ASSUMED_CONSTANTS:
        if unit == "fraction":
            steps.append(f"  {name:30s} {value * 100:7.1f} %")
        else:
            steps.append(f"  {name:30s} {value:7.2f} {unit}")
    return _conclude(
        steps,
        "Every figure in the second pile is an estimate and is on the "
        "store-bought side of the comparison, which is the side it flatters "
        "least to guess about.")


@lru_cache(maxsize=1)
def steps_yield() -> tuple[str, ...]:
    """Screen 2 -- how much of the tree each method actually keeps."""
    rows = section_rows(LOG)
    facts = dome_facts()
    steps = [
        f"one trunk: {LOG.butt_diameter_in:.1f} in at the butt, "
        f"{LOG.top_diameter_in:.1f} in at the top, "
        f"{LOG.usable_length_ft:.0f} ft usable",
        f"bucked into {len(rows)} sections of "
        f"{LOG.section_length_ft:.0f} ft",
        f"solid wood in those sections = {YIELD.solid_bf:.1f} board feet",
        "SPLIT RADIALLY:",
        f"  {SECTORS_PER_LOG} sectors per section, "
        f"{SECTOR_ANGLE_DEG:.0f} deg each = {YIELD.wedge_count} full-length "
        "sectors from one tree",
        f"  the saw passes remove {YIELD.kerf_bf:.1f} bf of kerf",
        f"  wood kept = {YIELD.solid_bf:.1f} - {YIELD.kerf_bf:.1f} = "
        f"{YIELD.wedge_bf:.1f} bf = {YIELD.wedge_recovery * 100:.1f} %",
        f"  measured across whole trees on site: "
        f"{_MEASURED['wedge_recovery_share'] * 100:.0f} %",
        "SAWN INTO TRUE TWO-BY-FOURS, same sections:",
        f"  rectangles that grid-pack inside the round = "
        f"{YIELD.two_by_four_count} pieces",
        f"  {YIELD.two_by_four_count} x {TWO_BY_FOUR_BF:.0f} bf = "
        f"{YIELD.two_by_four_bf:.1f} bf = "
        f"{YIELD.two_by_four_recovery * 100:.1f} %",
        f"  square milling in practice recovers "
        f"{_MEASURED['traditional_recovery_low'] * 100:.0f}-"
        f"{_MEASURED['traditional_recovery_high'] * 100:.0f} %, losing wood to "
        "slabs, edgings, trim, drying degrade and planer shavings",
        f"crosscut once, one tree gives {YIELD.strut_count} members; the dome "
        f"needs {facts['members']:.0f} and {PLAN.trees} trees give "
        f"{PLAN.members_available}",
    ]
    return _conclude(
        steps,
        f"The same two trees yield {YIELD.gain_over_computed:.2f} times as "
        "much usable structure split as sawn, because a wedge is not trying "
        "to be a rectangle and so throws none of the round away.")


@lru_cache(maxsize=1)
def steps_mills() -> tuple[str, ...]:
    """Screen 3 -- the machines that stop being necessary."""
    steps = ["what has to happen to a log before it can hold a roof up:"]
    for name, machine, sawn, wedge, note in PROCESS_CHAIN:
        mark = "BOTH " if (sawn and wedge) else ("SAWN " if sawn else "WEDGE")
        steps.append(f"  {mark} {name:24s} {machine}")
        steps.append(f"        {note}")
    dropped = machines_dropped()
    steps.append(
        f"machines the wedge path never buys, feeds or houses: {len(dropped)}")
    steps.append("  " + ", ".join(dropped))
    steps.append("what is left on the wedge side is one chainsaw and a flat board")
    return _conclude(
        steps,
        f"The dome removes {len(dropped)} whole machines from the chain, "
        "and it can only do that because a triangulated shell does not "
        "care whether its sticks are rectangular.")


@lru_cache(maxsize=1)
def steps_middlemen() -> tuple[str, ...]:
    """Screen 4 -- the hands between a standing tree and a rack."""
    steps = ["a stud on a rack has been sold and handled this many times:"]
    for index, (who, what) in enumerate(MIDDLE_MEN, start=1):
        steps.append(f"  {index:2d}. {who:20s} {what}")
    price = _MEASURED["stud_with_tax_usd"]
    shelf = _MEASURED["stud_shelf_usd"]
    steps.append(
        f"then sales tax: ${shelf:.2f} on the rack becomes ${price:.2f} paid")
    steps.append(
        f"every one of the {len(MIDDLE_MEN)} took a margin, and every margin "
        "is in that price")
    steps.append(
        "the wedge path is: fell the tree, rip the trunk, use the wood")
    return _conclude(
        steps,
        f"Cutting your own wedges removes {len(MIDDLE_MEN)} separate parties "
        "from between the tree and the wall, none of whom did anything to "
        "the wood that a geodesic shell needed done.")


@lru_cache(maxsize=1)
def steps_rate() -> tuple[str, ...]:
    """Screen 5 -- two timed sessions, and whether they agree."""
    r = cut_rate_model()
    steps = [
        "SESSION A, timed:",
        f"  {_MEASURED['session_a_wedges']:.0f} wedges in "
        f"{_MEASURED['session_a_hours']:.1f} h = "
        f"{r['wedges_per_hour']:.1f} wedges/hour",
        f"  ${_MEASURED['session_a_consumables_usd']:.2f} of fuel and bar oil "
        f"= ${r['consumables_usd_per_hour']:.2f}/hour, the only cash spent",
        "SESSION B, timed separately:",
        f"  6 passes at {r['section_ft']:.0f} ft = "
        f"{r['rip_feet_per_hour']:.0f} ft of rip in "
        f"{_MEASURED['session_b_hours']:.0f} h, at "
        f"{r['cut_depth_in']:.0f} in+ of depth",
        f"  {r['fuel_tanks_per_hour']:.0f} tanks of fuel and "
        f"{_MEASURED['session_b_oil_tanks']:.0f} of bar oil, one sharpening",
        "the two sessions measured different things, so divide them:",
        f"  {r['rip_feet_per_hour']:.0f} ft/h / "
        f"{r['wedges_per_hour']:.1f} wedges/h = "
        f"{r['measured_ft_per_wedge']:.2f} ft of rip per wedge",
        "and the geometry predicts the same number independently:",
        f"  {SECTORS_PER_LOG} sectors takes "
        f"{r['passes_per_section']:.0f} passes down a "
        f"{r['section_ft']:.0f} ft section",
        f"  {r['passes_per_section']:.0f} x {r['section_ft']:.0f} / "
        f"{SECTORS_PER_LOG} = {r['geometric_ft_per_wedge']:.2f} ft per wedge",
        f"the pure cutting is {r['agreement'] * 100:.0f} % of the measured "
        f"time; the other {r['overhead_share'] * 100:.0f} % is rolling the "
        "log, setting up and sharpening",
        f"planning uses {r['planning_wedges_per_hour']:.1f} wedges/hour, "
        f"{r['planning_margin'] * 100:.0f} % below the measured rate",
    ]
    return _conclude(
        steps,
        f"Two independent measurements and a geometric prediction agree to "
        f"within {abs(1.0 - r['agreement']) * 100:.0f} percent, which is why "
        "the rate below is worth anything at all.")


@lru_cache(maxsize=1)
def steps_value() -> tuple[str, ...]:
    """Screen 6 -- what one wedge is worth, two independent ways."""
    v = wedge_value_model()
    e = earnings_model()
    steps = [
        f"a 2x4x16 untreated pine is ${_MEASURED['stud_shelf_usd']:.2f} on the "
        f"rack, ${_MEASURED['stud_with_tax_usd']:.2f} with tax",
        f"  = ${v['usd_per_stud_section']:.2f} per eight-foot section",
        f"one 1/{SECTORS_PER_LOG} wedge of a "
        f"{v['diameter_in']:.0f} in trunk has "
        f"{v['wedge_area_in2']:.2f} in2 of section",
        f"a dressed 2x4 has {v['dressed_area_in2']:.2f} in2",
        f"  computed multiplier = {v['wedge_area_in2']:.2f} / "
        f"{v['dressed_area_in2']:.2f} = {v['computed_multiplier']:.2f} x",
        f"  the estimate on site was {v['builder_multiplier']:.1f} x",
        f"  the multiplier actually used for planning was "
        f"{v['used_multiplier']:.1f} x -- lower than both",
        "RULE OF THUMB:",
        f"  {v['used_multiplier']:.1f} x ${v['usd_per_stud_section']:.2f} = "
        f"${v['rule_usd_per_wedge']:.2f} per wedge",
        "STRICT, counting section AND the length difference:",
        f"  {v['computed_multiplier']:.2f} x "
        f"{v['length_ratio']:.2f} x ${v['usd_per_stud_section']:.2f} = "
        f"${v['strict_usd_per_wedge']:.2f} per wedge",
        f"  the two disagree by {v['disagreement'] * 100:.1f} %",
        f"at {e['wedges_per_hour']:.0f} wedges an hour that is "
        f"${e['gross_usd_per_hour']:.2f}/hour gross, "
        f"${e['net_usd_per_hour']:.2f} after fuel",
        f"one {e['afternoon_hours']:.0f}-hour afternoon: "
        f"{e['afternoon_wedges']:.0f} wedges, "
        f"${e['afternoon_gross_usd']:.0f} of wood, "
        f"${e['afternoon_consumables_usd']:.0f} of fuel",
    ]
    return _conclude(
        steps,
        f"A conservative multiplier and a generous length cancel almost "
        f"exactly, so both methods say the same thing: about "
        f"${e['net_usd_per_hour']:.0f} an hour, in wood you would otherwise "
        "have had to buy.")


@lru_cache(maxsize=1)
def steps_overhead() -> tuple[str, ...]:
    """Screen 7 -- the small stuff on the store-bought side."""
    b = purchase_model()
    facts = dome_facts()
    steps = [
        f"to match the section {b['members']:.0f} wedges provide you would "
        f"need {b['studs_per_wedge']:.2f} dressed studs alongside each one",
        f"  {b['members']:.0f} x {_MEASURED['wedge_length_ft']:.0f} ft x "
        f"{b['studs_per_wedge']:.2f} = {b['stud_feet']:.0f} stud-feet",
        f"  / 16 ft = {b['sticks_net']:.0f} sticks of actual wood needed",
        "then the part nobody counts:",
        f"  {_ASSUMED['cull_share'] * 100:.0f} % bought and rejected -- bowed, "
        "twisted, wet, split",
        f"  {_ASSUMED['transit_damage_share'] * 100:.0f} % lost to handling "
        "and weather on the way",
        f"  so you buy {b['sticks_bought']:.0f} sticks, "
        f"{b['cull_boards']:.0f} of which become firewood "
        f"(${b['cull_usd']:.0f})",
        f"lumber = {b['sticks_bought']:.0f} x "
        f"${_MEASURED['stud_with_tax_usd']:.2f} = ${b['lumber_usd']:.0f}",
        f"{b['loads']:.0f} truck loads x "
        f"{_ASSUMED['store_round_trip_miles']:.0f} mi = "
        f"{b['trip_miles']:.0f} mi at "
        f"${_ASSUMED['truck_usd_per_mile']:.2f}/mi = ${b['trip_usd']:.0f}",
        f"  and {b['trip_hours']:.1f} h of driving, picking, queuing, loading "
        f"and unloading = ${b['trip_time_usd']:.0f} of time",
        f"BOUGHT: ${b['buy_cash_usd']:.0f} cash, "
        f"${b['buy_all_in_usd']:.0f} with the time",
        f"CUT: {b['cut_hours']:.0f} h of ripping, "
        f"${b['cut_cash_usd']:.0f} of fuel and oil, no trips at all",
    ]
    return _conclude(
        steps,
        f"The chainsaw's fuel bill roughly replaces the truck's, so the real "
        f"difference is ${b['cash_saved_usd']:.0f} of cash that never leaves, "
        "and a stack of wood that was already on the property.")


@lru_cache(maxsize=1)
def steps_defects() -> tuple[str, ...]:
    """Screen 8 -- why short members forgive a bent tree."""
    d = defect_model()
    facts = dome_facts()
    steps = [
        "a knot or a bend does not ruin wood. It ruins whatever length has",
        "  to be thrown away around it -- and that length is the piece you",
        "  were trying to make.",
        f"this dome's members run "
        f"{d['shortest_member_ft']:.2f} to {d['longest_member_ft']:.2f} ft, "
        f"cut from {d['short_ft']:.0f} ft stock",
        f"a {d['long_ft']:.0f} ft stick from the same trunk is "
        f"{d['loss_ratio']:.1f} times longer",
        f"one defect costs, out of {d['usable_ft']:.0f} usable ft:",
        f"  short members  {d['short_ft']:.0f} ft = "
        f"{d['short_loss_share'] * 100:.1f} % of the tree",
        f"  long sticks   {d['long_ft']:.0f} ft = "
        f"{d['long_loss_share'] * 100:.1f} % of the tree",
        f"and the trunk gives {d['short_pieces']:.0f} short pieces against "
        f"{d['long_pieces']:.0f} long ones, so there are more places for a",
        "  defect to fall harmlessly between",
        "a real bend is cut out at its middle: go six feet clear either side",
        "  and the sections above and below it are both still good",
        "in square milling the same bend follows the board down its whole",
        "  length, because the rectangle has to be straight before it exists",
    ]
    return _conclude(
        steps,
        f"Short modular members make a defect {d['loss_ratio']:.1f} times "
        "cheaper, which is what lets a crooked farm tree be structure "
        "instead of firewood.")


@lru_cache(maxsize=1)
def steps_structure() -> tuple[str, ...]:
    """Screen 9 -- the comparison, and the diameter it turns on."""
    s = structure_model()
    steps = [
        f"a raw sector is literally 1/{SECTORS_PER_LOG} of the tree, and how "
        "strong that is depends entirely on how big the tree was.",
        f"AT THE SIMULATOR'S {s['dome_diameter_in']:.0f} IN TRUNK:",
        f"  area {s['dome_area']:.2f} in2, S {s['dome_modulus']:.2f} in3",
        f"  = {s['dome_area_vs_dressed'] * 100:.0f} % of a dressed 2x4's area "
        f"but only {s['dome_modulus_vs_dressed'] * 100:.0f} % of its bending",
        f"AT THE {s['measured_diameter_in']:.0f} IN TRUNKS ACTUALLY BEING CUT:",
        f"  area {s['real_area']:.2f} in2, I {s['real_i']:.2f} in4, "
        f"S {s['real_modulus']:.2f} in3",
        f"  = {s['real_area_vs_dressed'] * 100:.0f} % of a dressed 2x4's area "
        f"and {s['real_modulus_vs_dressed'] * 100:.0f} % of its bending",
        f"  and {s['real_area_vs_full'] * 100:.0f} % / "
        f"{s['real_modulus_vs_full'] * 100:.0f} % against a FULL-dimension 2x4",
        "section grows with the square of the radius and bending with the",
        "  cube, so there is a diameter where the sector overtakes the stud:",
        f"  more area than a dressed 2x4 above "
        f"{s['crossover_area_dressed']:.2f} in",
        f"  stiffer than a dressed 2x4 above "
        f"{s['crossover_modulus_dressed']:.2f} in",
        f"  stiffer than a FULL 2x4 above "
        f"{s['crossover_modulus_full']:.2f} in",
        f"and neighbouring panels never share a stick, so all "
        f"{s['interior_edges']:.0f} interior edges carry TWO sectors:",
        f"  {s['doubled_area_vs_dressed'] * 100:.0f} % of a stud's area, "
        f"{s['doubled_modulus_vs_dressed'] * 100:.0f} % of its bending",
    ]
    return _conclude(
        steps,
        f"Under {s['crossover_modulus_dressed']:.1f} inches of trunk the wedge "
        f"is the weaker member and this argument fails. The trees being cut "
        f"are {s['measured_diameter_in']:.0f} to 15 inches, which is why it "
        "does not.")


@lru_cache(maxsize=1)
def steps_orientation() -> tuple[str, ...]:
    """Screen 10 -- the same stick, four ways up, and what each costs."""
    rows = orientation_table()
    best = max(rows, key=lambda row: row[4])
    worst = min(rows, key=lambda row: row[4])
    steps = [
        "the wedge is not symmetric, so which way it faces is a decision.",
        "turn it about its own long axis and the SHAPE stays the same",
        "  while the STIFFNESS does not, because bending in a shell is",
        "  radial: in and out along the dome's own radius.",
    ]
    for orientation, reading, area, i_yy, modulus in rows:
        name = orientation.replace("point_", "").replace("_", "-").upper()
        steps.append(f"  {name:10s} I {i_yy:5.2f} in4   S {modulus:5.2f} in3")
        steps.append(f"             a pair at one seam: {reading}")
    steps.append(
        f"area is {rows[0][2]:.2f} in2 in all four -- rotation moves no wood")
    steps.append(
        f"but S runs {worst[4]:.2f} to {best[4]:.2f} in3, a factor of "
        f"{best[4] / worst[4]:.2f}")
    return _conclude(
        steps,
        f"Pointing the wedge at the dome's centre puts "
        f"{best[4] / worst[4]:.2f} times the bending stiffness under the "
        "same wood, for free, by turning the stick before it goes down.")


@lru_cache(maxsize=1)
def steps_dihedral() -> tuple[str, ...]:
    """Screen 11 -- why there is a key in the seam at all."""
    facts = dome_facts()
    steps = [
        "two panels meeting along one edge are not in the same plane.",
        f"the fold between them runs {facts['fold_min_deg']:.2f} to "
        f"{facts['fold_max_deg']:.2f} deg",
        f"  a spread of {facts['fold_spread_deg']:.2f} deg across "
        f"{facts['seams']:.0f} interior seams",
        "each panel brings its own member, so a seam has two raw sawn",
        f"  faces {SECTOR_ANGLE_DEG:.0f} deg apart before anything folds",
        f"after folding, the gap left between them runs "
        f"{facts['gap_min_deg']:.2f} to {facts['gap_max_deg']:.2f} deg",
        f"  which is exactly {SECTOR_ANGLE_DEG:.0f} deg minus the fold",
        "there are only two ways to close a gap that is never the same:",
        "  shave the wood to suit each seam -- a different bevel, "
        f"{facts['seams']:.0f} times",
        "  or leave the wood alone and fit a key that varies instead",
        f"the key's base runs {facts['key_base_min_in']:.2f} to "
        f"{facts['key_base_max_in']:.2f} in",
        "  one part, cut on a taper, doing what would otherwise be "
        "a setup change per seam",
    ]
    return _conclude(
        steps,
        f"The key exists so the {facts['fold_spread_deg']:.2f} degrees "
        "of dihedral variation live in a small replaceable part instead "
        "of in every structural member of the building.")


@lru_cache(maxsize=1)
def steps_jig() -> tuple[str, ...]:
    """Screen 12 -- the fixture, and why the head end is cut last."""
    facts = dome_facts()
    stages = bridge.jig_stages()
    steps = [
        f"{facts['panels']:.0f} triangles, {facts['members']:.0f} members, "
        f"{facts['joints']:.0f} corner joints -- all off one flat board",
        f"the fixture comes in {len(stages)} steps and holds three things:",
        "  a RAIL per member, set to the sawn point-axis, not the bark",
        "  a RED and a GREEN plate that make a wrongly-turned wedge "
        "physically refuse to seat",
        "  a FENCE at each head end, which is the plane the saw runs on",
        "each member arrives with ONE cut already made:",
        "  the butt, cut to the angle its neighbour presents, batched",
        f"and one deliberate error: the head is left "
        f"{facts['head_overfit_in']:.0f} in too long",
        "three butts are pulled up, the loop closes, and only then is",
        "  each head sawn against its fence -- unmeasured, in place",
        f"the offcut is {facts['head_offcut_ft']:.0f} ft per dome "
        f"= {facts['head_offcut_share'] * 100:.1f} % of raw length",
        f"and {facts['panels']:.0f} panels need only "
        f"{facts['jig_variants']:.0f} physically different fixtures",
    ]
    return _conclude(
        steps,
        f"Leaving {facts['head_offcut_share'] * 100:.1f} percent of the "
        "length as offcut is what buys the accuracy: error in stock "
        "length or butt angle leaves in the offcut instead of "
        "accumulating around the triangle.")


@lru_cache(maxsize=1)
def steps_close() -> tuple[str, ...]:
    """Screen 13 -- the whole argument on one page."""
    r = cut_rate_model()
    e = earnings_model()
    b = purchase_model()
    s = structure_model()
    facts = dome_facts()
    dropped = machines_dropped()
    steps = [
        f"WOOD     {YIELD.wedge_recovery * 100:.0f} % of the tree kept split, "
        f"{YIELD.two_by_four_recovery * 100:.0f} % sawn -- "
        f"{YIELD.gain_over_computed:.2f}x",
        f"MACHINE  {len(dropped)} fewer: {', '.join(dropped)}",
        f"HANDS    {len(MIDDLE_MEN)} middle men removed between tree and wall",
        f"RATE     {r['wedges_per_hour']:.0f} wedges/hour measured, "
        f"{r['planning_wedges_per_hour']:.0f} used for planning",
        f"VALUE    ${e['usd_per_wedge']:.2f} of wood per wedge, "
        f"${e['net_usd_per_hour']:.0f}/hour net of fuel",
        f"COST     ${b['cut_cash_usd']:.0f} to cut this dome's frame against "
        f"${b['buy_cash_usd']:.0f} to buy it",
        f"STICK    {s['real_modulus_vs_dressed'] * 100:.0f} % of a dressed "
        f"stud in bending at {s['measured_diameter_in']:.0f} in trunk; "
        f"under {s['crossover_modulus_dressed']:.1f} in it would lose",
        f"EDGE     every interior edge carries two, "
        f"{s['doubled_area_vs_dressed'] * 100:.0f} % of a stud's section",
        f"ANGLE    {facts['fold_spread_deg']:.2f} deg of dihedral variation "
        "lives in the key, not the timber",
        f"CUTS     one batched butt per member, one flush cut in place, "
        f"{facts['jig_variants']:.0f} fixtures for {facts['panels']:.0f} panels",
    ]
    return _conclude(
        steps,
        "Not one of those lines works on a rectangular building. They "
        "work because a triangulated shell will take any stick whose ends "
        "can be made to meet, and a split log is already that stick.")



@lru_cache(maxsize=1)
def steps_buttcut() -> tuple[str, ...]:
    """The compound cut, and how many settings it really takes."""
    c = butt_cut_model()
    steps = [
        "correction first. An earlier cut of this film said nothing in this",
        "  frame is mitred. That is wrong, and it is the most important",
        "  thing on this screen.",
        "the PINWHEEL removes the shared vertex: no two ends ever meet each",
        "  other, nothing is coped, nothing is shaved to a point.",
        "but every butt end still lands on the SIDE of the next member, and",
        "  that side is tilted two ways at once -- by the sector angle, and",
        "  by the turn the member makes to close the triangle.",
        "so the butt is a compound cut, and it is the hardest operation in",
        "  the build. Here is what the solve says it costs:",
        f"  BEVEL {c['bevel_deg']:.3f} deg on every one of "
        f"{c['members']:.0f} members",
        f"  and {c['bevel_deg']:.3f} = half the sector angle "
        f"({c['half_sector_deg']:.3f}), set by the SPLIT, not by the dome",
        f"  MITRE takes {len(c['mitres'])} values in the whole shell:",
    ]
    for mitre, bevel, count in c["settings"]:
        steps.append(f"    {abs(mitre):7.3f} deg   x{count:3.0f} members")
    steps.append(
        f"  largest is {c['max_mitre_deg']:.3f} deg, inside a common saw's "
        f"{c['saw_limit_deg']:.0f} deg swing")
    steps.append(
        f"the cut runs {c['axial_run_min_in']:.2f} to "
        f"{c['axial_run_max_in']:.2f} in along the member, because it lands "
        "on a slope:")
    steps.append(
        "  the sector's POINT reaches furthest and the bark corner least, so"
        if c["lead_is_point"] else
        "  one corner reaches further than the other, so")
    steps.append(
        "  the blank has to be long on the point side and the cut is walked "
        "from the short corner up")
    return _conclude(
        steps,
        f"One bevel, locked at {c['bevel_deg']:.1f} degrees and never touched, "
        f"and {len(c['mitres'])} mitre stops. That is what turns the hardest "
        "cut in the build from gauging by hand into a fixture.")


@lru_cache(maxsize=1)
def steps_features() -> tuple[str, ...]:
    """The four rotations as four different buildings."""
    rows = orientation_features()
    steps = [
        "stiffness is one axis of the choice and it is already covered.",
        "here is what each rotation does to the BUILDING:",
    ]
    for row in rows:
        name = row["orientation"].replace("point_", "").replace("_", "-").upper()
        steps.append(f"  {name}")
        steps.append(
            f"    S {row['modulus_in3']:5.2f} in3   depth {row['depth_in']:4.2f} in   "
            f"butt bevel {row['bevel_deg']:+6.2f} deg")
        if abs(row["lip_in"]) < 1.0e-6:
            lip = "no lip: opening is parallel-sided, panels held by fixings"
        elif row["lip_in"] > 0.0:
            lip = (f"lip {row['lip_in']:+.2f} in -- panel drops in from OUTSIDE "
                   "and cannot fall through")
        else:
            lip = (f"lip {row['lip_in']:+.2f} in -- panel goes in from INSIDE "
                   "and cannot fall out")
        steps.append(f"    {lip}")
        if row["is_duct"]:
            steps.append(
                f"    seam V {row['gap_min_deg']:.1f}-{row['gap_max_deg']:.1f} deg, "
                f"{row['channel_in2']:.1f} in2 -> {row['channel_ft3']:.1f} cu ft of "
                "continuous conduit")
        else:
            steps.append(
                f"    seam opens to {row['gap_min_deg']:.0f}-"
                f"{row['gap_max_deg']:.0f} deg: a shallow dish, not a duct")
        steps.append(
            f"    sawn faces sit {row['face_tilt_deg']:.1f} deg off the dome "
            "surface")
    def _name(row) -> str:
        return row["orientation"].replace("point_", "").replace("_", "-").upper()

    best_cut = min(rows, key=lambda row: abs(row["bevel_deg"]))
    flattest_tilt = min(row["face_tilt_deg"] for row in rows)
    # Two rotations tie on this, so name both rather than let min() pick one silently.
    flattest = [_name(row) for row in rows
                if abs(row["face_tilt_deg"] - flattest_tilt) < 1.0e-6]
    keystone = max(rows, key=lambda row: row["lip_in"])
    inside = min(rows, key=lambda row: row["lip_in"])
    steps.append(
        f"so: {_name(keystone)} catches a panel from OUTSIDE like a keystone, "
        f"and puts {keystone['channel_ft3']:.0f} cu ft of conduit out there too")
    steps.append(
        f"    {_name(inside)} catches it from INSIDE and runs the services in "
        "the warm")
    steps.append(
        f"    {' and '.join(flattest)} present the flattest wood to sheathing, "
        f"{flattest_tilt:.1f} deg off the surface")
    steps.append(
        f"    {_name(best_cut)} makes the hardest cut in the build a plain "
        f"mitre, bevel {best_cut['bevel_deg']:.1f} deg")
    return _conclude(
        steps,
        "Four rotations, four different buildings out of one stick: where "
        "the panel is caught, which side the services run, what sheathing "
        "lands on, and how hard the one difficult cut is.")


@lru_cache(maxsize=1)
def steps_mixed() -> tuple[str, ...]:
    """A dome from whatever the woodlot gives."""
    m = mixed_diameter_model()
    steps = [
        f"the rest of this film assumes one trunk diameter. Real trees run "
        f"{m['low_in']:.0f} to {m['high_in']:.0f} in and do not sort themselves.",
        "solve the same dome at both ends of that range and see what moves:",
        f"  fold angles: {m['fold_min']:.3f} to {m['fold_max']:.3f} deg at "
        f"{m['low_in']:.0f} in",
        f"  fold angles: {m['fold_min']:.3f} to {m['fold_max']:.3f} deg at "
        f"{m['high_in']:.0f} in",
        "  IDENTICAL. not one angle in the shell depends on the log size,",
        "    because the dihedral is a property of the subdivision",
        "what does move:",
        f"  member sits back from its ideal edge, further by "
        f"{m['offset_step_in']:.2f} in on the fat logs",
        f"  key base {m['key_low_min']:.2f}-{m['key_low_max']:.2f} in thin, "
        f"{m['key_high_min']:.2f}-{m['key_high_max']:.2f} in fat",
        f"  blank length shifts by {m['stock_shift_in']:.2f} in across the "
        "whole range",
        f"  outer surface steps by up to {m['surface_step_in']:.2f} in where a "
        "thin member meets a fat one",
        "and the strength question is settled by the THINNEST member present:",
        f"  {m['low_in']:.0f} in sector = {m['area_low']:.2f} in2, "
        f"S {m['modulus_low']:.2f} in3",
        f"  = {m['weakest_vs_dressed_area'] * 100:.0f} % of a dressed 2x4's "
        f"area and {m['weakest_vs_dressed_modulus'] * 100:.0f} % of its bending",
        f"  and {m['low_in']:.0f} in clears the "
        f"{m['crossover_in']:.2f} in crossover, so the whole range does",
    ]
    return _conclude(
        steps,
        f"Mixing {m['low_in']:.0f} to {m['high_in']:.0f} inch logs changes no "
        f"angle, moves the blank by {m['stock_shift_in']:.2f} in, and lands the "
        "rest in the key. You get a shell with a slightly restless surface and "
        "a house that is entirely sound.")


ALL_SCREENS: tuple[tuple[str, object], ...] = (
    ("assumptions", steps_assumptions),
    ("yield", steps_yield),
    ("mills", steps_mills),
    ("middlemen", steps_middlemen),
    ("rate", steps_rate),
    ("value", steps_value),
    ("overhead", steps_overhead),
    ("defects", steps_defects),
    ("buttcut", steps_buttcut),
    ("structure", steps_structure),
    ("orientation", steps_orientation),
    ("features", steps_features),
    ("mixed", steps_mixed),
    ("dihedral", steps_dihedral),
    ("jig", steps_jig),
    ("close", steps_close),
)


def wedge_why_report() -> str:
    """Every screen as plain text, for reading without rendering a frame."""
    out: list[str] = ["WHY WEDGES — THE WHOLE ARGUMENT, DERIVED", "=" * 68, ""]
    for name, builder in ALL_SCREENS:
        out.append(name.upper())
        out.append("-" * 68)
        out.extend(builder())
        out.append("")
    return "\n".join(out)


def validate_wedge_why_facts() -> None:
    """Prove the arithmetic before a frame of it renders."""
    facts = dome_facts()
    assert facts["members"] == 120.0, facts["members"]
    assert facts["panels"] == 40.0, facts["panels"]
    assert facts["seams"] == 55.0, facts["seams"]
    assert 0.0 < facts["head_offcut_share"] < 0.25, facts["head_offcut_share"]
    assert facts["fold_spread_deg"] > 0.0

    # The section arithmetic is polygon integration, so it is checked against the closed
    # form for a circular sector rather than trusted.
    sim = bridge.simulator()
    radius = sim.DomeConfig().trunk_diameter_in * 0.5
    half = math.radians(SECTOR_ANGLE_DEG * 0.5)
    section = sector_section("point_dome_in")
    exact_area = radius * radius * half
    assert abs(section.area_in2 - exact_area) / exact_area < 2.0e-3, (
        section.area_in2, exact_area)
    exact_i_apex = (radius ** 4 / 4.0) * (half + math.sin(half) * math.cos(half))
    exact_centroid = 4.0 * radius * math.sin(half) / (3.0 * 2.0 * half)
    exact_i = exact_i_apex - exact_area * exact_centroid ** 2
    assert abs(section.i_yy_in4 - exact_i) / exact_i < 5.0e-3, (
        section.i_yy_in4, exact_i)
    assert abs(section.centroid_z_in - exact_centroid) / exact_centroid < 5.0e-3

    # The two sector builders must agree, or the crossover solved with one would not
    # describe the wood drawn with the other.
    twin = sector_at_diameter(sim.DomeConfig().trunk_diameter_in)
    assert abs(twin.area_in2 - section.area_in2) / section.area_in2 < 5.0e-3
    assert abs(twin.section_modulus_in3 - section.section_modulus_in3) \
        / section.section_modulus_in3 < 1.0e-2

    # A rectangle must come out of the same integrator as b*h^3/12, or the integrator
    # is wrong and every wedge figure above it is wrong too.
    rect = dressed_stud()
    b, h = DRESSED_STUD_IN
    assert abs(rect.area_in2 - b * h) < 1.0e-9
    assert abs(rect.i_yy_in4 - b * h ** 3 / 12.0) < 1.0e-9

    # Rotation must move no wood, only stiffness.
    areas = {round(row[2], 9) for row in orientation_table()}
    assert len(areas) == 1, areas
    moduli = {round(row[4], 6) for row in orientation_table()}
    assert len(moduli) > 1, "rotating the wedge has to change its stiffness"

    # The crossovers are the load-bearing structural claim. They must be real diameters,
    # in the right order, and must actually separate weaker from stronger.
    cross = crossover_diameters()
    for key, value in cross.items():
        assert 2.0 < value < 60.0, (key, value)
    assert cross["area_vs_dressed_in"] < cross["modulus_vs_dressed_in"]
    assert cross["area_vs_full_in"] < cross["modulus_vs_full_in"]
    dressed = dressed_stud()
    below = sector_at_diameter(cross["modulus_vs_dressed_in"] - 1.0)
    above = sector_at_diameter(cross["modulus_vs_dressed_in"] + 1.0)
    assert below.section_modulus_in3 < dressed.section_modulus_in3
    assert above.section_modulus_in3 > dressed.section_modulus_in3

    s = structure_model()
    assert s["dome_modulus_vs_dressed"] < 1.0, (
        "at the simulator's own trunk the single stick is supposed to lose; "
        "if that has changed, the narration has to change with it")
    assert s["real_modulus_vs_dressed"] > 1.0, (
        "at the measured trunk it is supposed to win")
    assert s["doubled_area_vs_dressed"] > s["real_area_vs_dressed"]

    # The two cutting sessions were timed independently; if they stop agreeing with
    # the geometry the film must not keep claiming that they do.
    r = cut_rate_model()
    assert 0.75 < r["agreement"] < 1.0, r["agreement"]
    assert r["planning_wedges_per_hour"] < r["wedges_per_hour"], (
        "planning is supposed to be slower than the measured rate")

    # The rule of thumb and the strict calculation are presented as agreeing; check it.
    v = wedge_value_model()
    assert v["disagreement"] < 0.10, v["disagreement"]
    assert v["used_multiplier"] < v["builder_multiplier"] <= v["computed_multiplier"], (
        "the multiplier used for planning must stay the conservative one")

    b = purchase_model()
    assert b["cut_cash_usd"] < b["buy_cash_usd"]
    assert b["sticks_bought"] > b["sticks_net"]

    d = defect_model()
    assert d["loss_ratio"] > 1.0
    assert d["short_pieces"] > d["long_pieces"]

    for name, builder in ALL_SCREENS:
        steps = builder()
        assert len(steps) >= 5, name
        assert len(steps[-1]) >= 30, name
        for line in steps:
            assert line.strip(), name
            # A formatting bug shows up as a stray repr in otherwise fine prose, so
            # the check is for those tokens as words, not as substrings: "infill" and
            # "None of this" are English, "nan" and "None" on their own are not.
            assert not re.search(r"\b(nan|inf|None)\b", line), (name, line)
            assert "{" not in line and "}" not in line, (name, line)
