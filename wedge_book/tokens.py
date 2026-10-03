"""Live numbers for the manuscript of *The Wedge Method*.

The prose writes ``{{dome.diameter_ft}}`` rather than ``19.4``, and this
module fills it in at export time from the solver, the geometry and the cost
model. A number typed into a paragraph is correct on the day it is typed and
silently wrong from the first time anybody changes the tree, the trunk or a
price -- and nothing fails, so nobody finds it.

An unknown token is a hard error rather than a blank, because a book that
quietly prints ``{{dome.diamter_ft}}`` as nothing is worse than one that
refuses to build.

THE NAMESPACES

``dome``   the building: how big, how many of what
``cut``    what you actually saw: chords, cuts, the bite, the angles
``seam``   the joint: folds, gaps, what fits in the channel
``money``  what it costs, from the cost model
``ch``     cross-references: ``{{ch.nine}}`` is the chapter number of the
           nine-processes chapter, so prose never says "see Chapter 8" and
           goes stale when a chapter is inserted
``tool``   counts about the software the last part documents

Every name, its value and a one-line description is printed by
``py -3.12 -m wedge_book.tokens``, so a writer never has to guess one.
"""

from __future__ import annotations

import re
from dataclasses import dataclass
from typing import Callable

TOKEN = re.compile(r"\{\{([a-z_]+\.[a-z_0-9]+)\}\}")


@dataclass(frozen=True)
class Token:
    """One live figure the manuscript may quote."""

    name: str
    describe: str
    compute: Callable[[], str]

    def value(self) -> str:
        return self.compute()


def _table() -> dict[str, Token]:
    from . import numbers, outline, tooling

    values = numbers.quantities()
    money = numbers.money()
    book = outline.BOOK

    def q(name: str) -> str:
        return values[name].text()

    def m(name: str, digits: int = 0) -> str:
        return f"{money[name].value:,.{digits}f}"

    entries: list[Token] = []

    def add(name: str, describe: str, compute) -> None:
        entries.append(Token(name, describe, compute))

    # -- the building ------------------------------------------------
    add("dome.diameter_ft", "across the base, in feet",
        lambda: f"{values['diameter_ft'].value:,.2f}")
    add("dome.height_ft", "apex height, in feet",
        lambda: f"{values['height_ft'].value:,.2f}")
    add("dome.radius_in", "sphere radius, in inches", lambda: q("radius_in"))
    add("dome.floor_sqft", "floor inside the base ring, square feet",
        lambda: q("floor_sqft"))
    add("dome.panel_sqft", "flat area of all forty triangles",
        lambda: q("panel_sqft"))
    add("dome.members", "structural members in the frame",
        lambda: q("member_count"))
    add("dome.panels", "triangular panels", lambda: q("face_count"))
    add("dome.vertices", "geodesic vertices", lambda: q("vertex_count"))
    add("dome.edges", "geodesic edges", lambda: q("edge_count"))
    add("dome.seams", "interior seams", lambda: q("seam_count"))
    add("dome.base_sides", "sides of the base polygon",
        lambda: q("base_sides"))
    add("dome.seam_ft", "total run of interior seam, in feet",
        lambda: q("seam_run_ft"))
    add("dome.timber_ft", "timber in the frame, in feet",
        lambda: q("member_stock_ft"))
    add("dome.aaa", "equilateral panels", lambda: q("aaa_count"))
    add("dome.bab", "isosceles panels", lambda: q("bab_count"))

    # -- what you cut ------------------------------------------------
    add("cut.a_chord", "long chord, inches", lambda: q("a_chord_in"))
    add("cut.b_chord", "short chord, inches", lambda: q("b_chord_in"))
    add("cut.a_cut", "long member's cut length, inches",
        lambda: q("a_cut_in"))
    add("cut.b_cut", "short member's cut length, inches",
        lambda: q("b_cut_in"))
    add("cut.a_bite", "what the pinwheel takes off a long member",
        lambda: q("a_bite_in"))
    add("cut.b_bite", "what the pinwheel takes off a short member",
        lambda: q("b_bite_in"))
    add("cut.width", "the member's width across the bark face",
        lambda: q("member_width_in"))
    add("cut.depth", "the member's depth, point to bark",
        lambda: q("member_depth_in"))
    add("cut.bevel", "the butt cut's bevel, degrees",
        lambda: q("bevel_deg"))
    add("cut.mitres", "how many mitre settings across all 120 members",
        lambda: q("mitre_settings"))
    add("cut.sector", "the log sector's angle, degrees",
        lambda: q("sector_deg"))
    add("cut.splits", "how many sectors the trunk splits into",
        lambda: q("radial_splits"))
    add("cut.trunk", "trunk diameter, inches", lambda: q("trunk_diameter_in"))
    add("cut.a_factor", "long chord as a fraction of the radius",
        lambda: q("a_factor"))
    add("cut.b_factor", "short chord as a fraction of the radius",
        lambda: q("b_factor"))
    add("cut.band_bite", "the same bite for a rectangular stick",
        lambda: q("band_bite_in"))

    # -- the joint ---------------------------------------------------
    add("seam.fold_a", "an A seam's fold angle, degrees",
        lambda: q("a_fold_deg"))
    add("seam.fold_b", "a B seam's fold angle, degrees",
        lambda: q("b_fold_deg"))
    add("seam.gap_a", "sector angle left over at an A seam",
        lambda: q("a_gap_deg"))
    add("seam.gap_b", "sector angle left over at a B seam",
        lambda: q("b_gap_deg"))
    add("seam.key_a", "the A seam key's base width, inches",
        lambda: q("a_spline_base_in"))
    add("seam.key_b", "the B seam key's base width, inches",
        lambda: q("b_spline_base_in"))
    add("seam.hose_a", "largest hose an A seam channel takes",
        lambda: q("a_hose_max_in"))
    add("seam.narrowest", "narrowest panel's altitude, inches",
        lambda: q("bab_min_width_in"))
    add("seam.widest", "widest panel's altitude, inches",
        lambda: q("aaa_min_width_in"))

    # -- money -------------------------------------------------------
    add("money.price", "list price of the standard article",
        lambda: m("price"))
    add("money.cost", "what it costs to build", lambda: m("cost_to_build"))
    add("money.profit", "the maker's markup, in dollars",
        lambda: m("profit"))
    add("money.per_sqft", "price per square foot of floor",
        lambda: m("price_per_sqft", 2))
    add("money.frame", "the wedge-cut frame", lambda: m("group_frame"))
    add("money.cap", "the shower-cap shell", lambda: m("group_cap"))
    add("money.column", "the utility column and its cap",
        lambda: m("group_column"))
    add("money.pad", "the platform, which is the host's bill",
        lambda: m("group_pad"))
    add("money.labour_hours", "hours of build labour",
        lambda: m("labour_hours", 0))
    add("money.hard_price", "the same dome with a laminated hull",
        lambda: m("hard_price"))
    add("money.cap_bare", "a bare shower cap", lambda: m("cap_bare"))
    add("money.frame_weight", "the frame's weight in green pine, pounds",
        lambda: m("frame_weight_lb"))
    add("money.mast", "the mast through the column", lambda: m("mast"))
    add("money.float_rig", "the floating rig", lambda: m("float_rig"))
    add("money.float_total", "mast, floor and rig together",
        lambda: m("float_total"))
    add("money.deck", "the staple platform: a framed deck on piers",
        lambda: m("pad_blocks"))
    add("money.slab", "a full concrete slab", lambda: m("pad_slab"))
    add("money.gravel", "a compacted gravel base", lambda: m("pad_gravel"))

    # -- the pad network, from both sides ----------------------------
    from . import network

    options = {o.label: o for o in network.tenant_options()}
    own = options["own the dome, rent the pad"]
    apartment = options["apartment lease"]
    cases = {c.label: c for c in network.host_cases()}
    pad_case = cases["one serviced pad"]

    add("net.tenant_table", "four ways to be housed, compared",
        network.tenant_table)
    add("net.host_table", "three things to do with a piece of ground",
        network.host_table)
    add("net.own_monthly", "owning a dome on a pad, per month",
        lambda: f"{own.monthly:,.0f}")
    add("net.apartment_entry", "what an apartment costs at the door",
        lambda: f"{apartment.entry:,.0f}")
    add("net.crossover_months", "months before owning overtakes renting",
        lambda: f"{network.crossover_months():,.0f}")
    add("net.ten_year_gap", "ten-year difference against an apartment",
        lambda: f"{apartment.over(10.0) - own.over(10.0):,.0f}")
    add("net.dome_life", "the dome's assumed service life, years",
        lambda: f"{network._declared('dome_service_life_years'):,.0f}")
    add("net.pad_rent", "what a serviced pad rents for, per month",
        lambda: f"{network.pad_rent_monthly():,.0f}")
    add("net.pad_upfront", "what one serviced pad costs the host",
        lambda: f"{pad_case.upfront:,.0f}")
    add("net.pad_net", "what one pad earns the host a year, net",
        lambda: f"{pad_case.yearly_net:,.0f}")
    add("net.pad_payback", "how long a pad takes to pay back",
        lambda: f"{pad_case.payback_years():,.1f} years")

    # -- the geometry, from scratch ----------------------------------
    from two_v_demo import scratch_facts

    phi = scratch_facts.PHI
    add("phi.value", "the golden ratio", lambda: f"{phi:.9f}")
    add("phi.short", "the golden ratio, to three places",
        lambda: f"{phi:.3f}")
    add("phi.reciprocal", "one over the golden ratio",
        lambda: f"{1.0 / phi:.9f}")
    add("phi.radius", "how far the twelve points sit from the centre",
        lambda: f"{(1.0 + phi * phi) ** 0.5:.6f}")
    add("phi.chord_ratio", "the long chord over the short chord",
        lambda: f"{values['a_chord_in'].value / values['b_chord_in'].value:.6f}")
    add("phi.icosa_points", "points in an icosahedron", lambda: "12")
    add("phi.icosa_faces", "faces in an icosahedron", lambda: "20")

    # -- the stem cell -----------------------------------------------
    import seed_model

    catalogue = []
    for key in seed_model.FITOUT_ORDER:
        try:
            catalogue.append((key, seed_model.fitout(key).label,
                              seed_model.quote(key).price))
        except Exception:
            continue
    quote = seed_model.quote()

    def seed_table() -> str:
        rows = sorted(catalogue, key=lambda r: r[2])
        return "\n".join(f"{label:<26}${price:>10,.0f}"
                          for _key, label, price in rows)

    add("seed.count", "structures in the catalogue",
        lambda: str(len(catalogue)))
    add("seed.cheapest", "the cheapest structure in the catalogue",
        lambda: min(catalogue, key=lambda r: r[2])[1])
    add("seed.dearest", "the dearest structure in the catalogue",
        lambda: max(catalogue, key=lambda r: r[2])[1])
    add("seed.cheapest_usd", "what the cheapest one lists at",
        lambda: f"{min(catalogue, key=lambda r: r[2])[2]:,.0f}")
    add("seed.dearest_usd", "what the dearest one lists at",
        lambda: f"{max(catalogue, key=lambda r: r[2])[2]:,.0f}")
    add("seed.table", "the whole catalogue, priced", seed_table)

    # -- the core that transfers -------------------------------------
    add("core.cost", "what the utility core costs to build",
        lambda: f"{quote.core_cost:,.0f}")
    add("core.share", "the core as a percentage of the dome's cost",
        lambda: f"{quote.core_share * 100.0:,.0f}")
    add("core.parts", "how many parts the core is documented as",
        lambda: str(len(seed_model.core_parts())))
    add("core.services", "how many services the core carries",
        lambda: str(len({p.service for p in seed_model.core_parts()})))
    add("core.moves", "what moving a core to the next dome costs",
        lambda: f"{seed_model.declared('core_move_usd'):,.0f}")
    add("core.life", "how long a core lasts, in years",
        lambda: f"{seed_model.declared('core_service_life_years'):,.0f}")

    # -- the systems: seam module, air barrier, water, bench ---------
    from . import systems

    bill = {b.key: b for b in systems.bills()}
    air = systems.air_barrier()
    water = systems.water_comparison()
    bracket = systems.v_bracket()

    add("sys.seam", "the seam module, whole dome",
        lambda: f"{bill['seam'].cost:,.0f}")
    add("sys.column", "the utility column, complete",
        lambda: f"{bill['column'].cost:,.0f}")
    add("sys.power", "the power bench", lambda: f"{bill['power'].cost:,.0f}")
    add("sys.water", "the water bench", lambda: f"{bill['water'].cost:,.0f}")
    add("sys.hardware", "stainless joining hardware",
        lambda: f"{bill['hardware'].cost:,.0f}")
    add("sys.pad", "the pad's own materials",
        lambda: f"{bill['pad'].cost:,.0f}")
    add("sys.total", "every system on this page, added up",
        lambda: f"{systems.total():,.0f}")
    add("sys.seam_table", "the seam module, line by line",
        lambda: bill["seam"].table())
    add("sys.column_table", "the utility column, line by line",
        lambda: bill["column"].table())
    add("sys.power_table", "the power bench, line by line",
        lambda: bill["power"].table())
    add("sys.water_table", "the water bench, line by line",
        lambda: bill["water"].table())
    add("sys.hardware_table", "the hardware, line by line",
        lambda: bill["hardware"].table())
    add("sys.pad_table", "the pad's materials, line by line",
        lambda: bill["pad"].table())

    clock = systems.build_clock()
    add("hr.split_session", "wedges from one session at the log",
        lambda: f"{clock['wedges_per_session']:,.0f}")
    add("hr.session", "how long that session is, in hours",
        lambda: f"{clock['session_hours']:,.0f}")
    add("hr.split", "hours to split every member",
        lambda: f"{clock['split_hours']:,.0f}")
    add("hr.minutes", "minutes per member, tree to standing",
        lambda: f"{clock['minutes_per_member']:,.0f}")
    add("hr.straight", "hours for the whole frame, straight through",
        lambda: f"{clock['straight_hours']:,.0f}")
    add("hr.redundancy", "what is added for error, as a percentage",
        lambda: f"{clock['redundancy'] * 100:,.0f}")
    add("hr.total", "the build, with error allowed for",
        lambda: f"{clock['with_error']:,.1f}")
    add("hr.week", "the working week this book is named after",
        lambda: f"{clock['week']:,.0f}")
    add("hr.split_share", "splitting as a share of the whole build",
        lambda: f"{clock['split_share'] * 100:,.0f}")

    add("air.cfm", "cubic feet a minute the barrier needs",
        lambda: f"{air['cfm']:,.0f}")
    add("air.volume", "the interior, in cubic feet",
        lambda: f"{air['volume_cuft']:,.0f}")
    add("air.ach", "air changes an hour", lambda: f"{air['ach']:.2f}")
    add("air.pressure", "how far above outside, in pascals",
        lambda: f"{air['pressure_pa']:.0f}")
    add("air.fans", "how many fans", lambda: f"{air['fans']:.0f}")

    add("cond.gallons_per_inch", "gallons off the roof per inch of rain",
        lambda: f"{water['gallons_per_inch']:,.0f}")
    add("cond.watts", "what the condensing plates draw",
        lambda: f"{water['peltier_watts']:,.0f}")
    add("cond.gal_day", "gallons the plates make in a day",
        lambda: f"{water['peltier_gallons_per_day']:,.2f}")
    add("cond.gal_year", "gallons the plates make in a year",
        lambda: f"{water['peltier_gallons_per_year']:,.0f}")
    add("cond.rain_equal", "inches of rain that equal a year of plates",
        lambda: f"{water['rain_inches_equal_to_a_year']:,.1f}")
    add("cond.kwh_per_litre", "kilowatt hours per litre condensed",
        lambda: f"{water['kwh_per_litre']:,.2f}")

    add("brk.flap", "how long a V bracket's flap may be, in inches",
        lambda: f"{bracket['flap_in']:,.1f}")
    add("brk.holes", "holes in each flap",
        lambda: str(bracket["holes_per_flap"]))
    add("brk.spacing", "inches between holes along a flap",
        lambda: f"{bracket['spacing_in']:,.1f}")
    add("brk.each", "what one V bracket costs",
        lambda: f"{bracket['usd_each']:,.2f}")

    _parts_list_tokens(add)
    _geometry_tokens(add)
    _channel_tokens(add)
    _climate_tokens(add)
    _wood_tokens(add)

    # -- cross-references --------------------------------------------
    for chapter in book.chapters:
        add(f"ch.{chapter.key}", f"chapter number of {chapter.title!r}",
            (lambda number=chapter.number: str(number)))

    # -- the software ------------------------------------------------
    add("tool.worlds", "three-dimensional environments that ship with this",
        lambda: str(len(tooling.by_kind("world"))))
    add("tool.models", "arithmetic tools that ship with this",
        lambda: str(len(tooling.by_kind("model"))))
    add("tool.total", "programs documented in the last part",
        lambda: str(len(tooling.catalogue())))
    add("tool.chapters", "chapters in this book",
        lambda: str(len(book.chapters)))
    add("tool.figures", "pictures in this book",
        lambda: str(len(book.figures)))
    add("tool.table", "the whole catalogue of programs", tooling.table)

    # The nine processes are a list this book leans its scaling argument on,
    # so it reads them rather than printing its own copy.
    from two_v_demo import franken_economics

    processes = franken_economics.PROCESSES
    add("nine.count", "how many processes turn timber into a shell",
        lambda: str(len(processes)))
    add("nine.list", "the nine, in the order they happen",
        lambda: ", ".join(p.key for p in processes))
    add("nine.flat", "how many of them happen on a bench",
        lambda: str(sum(1 for p in processes if p.flat)))

    return {token.name: token for token in entries}


def _table_text(rows, widths) -> str:
    """Aligned plain-text rows, the way the manuscript prints its tables."""
    return "\n".join("".join(f"{cell:<{w}}" for cell, w in zip(row, widths)).rstrip()
                     for row in rows)


FLAT_RATE_SIZES_FT = (10.0, 30.0)
"""The two dome sizes the flat-rate argument compares: the film's own pair,
the smallest and largest in the product range. Declared, not derived."""


def _parts_list_tokens(add) -> None:
    """``parts`` and ``flat``: the model counting itself, and the flat rate."""
    import math

    import numpy as np
    import seed_world

    from two_v_demo import channel_facts as cf

    topo = cf.reference_model().topology
    lengths = [float(np.linalg.norm(np.asarray(topo.vertices[a]) - np.asarray(topo.vertices[b])))
               for a, b in (e.key for e in topo.edges.values())]
    cut = (max(lengths) + min(lengths)) / 2
    g = seed_world.geometry()
    members = {}
    for m in g.members:
        members[m.edge_type] = members.get(m.edge_type, 0) + m.count
    small, big = FLAT_RATE_SIZES_FT

    def area(d: float) -> float:
        return math.pi * (d / 2) ** 2

    add("parts.long_edges", "edges of the long length", lambda: str(sum(l > cut for l in lengths)))
    add("parts.short_edges", "edges of the short length", lambda: str(sum(l <= cut for l in lengths)))
    add("parts.long_members", "members cut to the long length", lambda: str(members.get("A", 0)))
    add("parts.short_members", "members cut to the short length", lambda: str(members.get("B", 0)))
    import seed_model

    add("parts.sections", "log sections the frame is split from",
        lambda: str(math.ceil(g.member_count / seed_model.SEED_RADIAL_SPLITS)))
    add("flat.small_ft", "the small dome, feet across", lambda: f"{small:.0f}")
    add("flat.big_ft", "the big dome, feet across", lambda: f"{big:.0f}")
    add("flat.small_sqft", "the small dome's floor, sq ft", lambda: f"{area(small):,.0f}")
    add("flat.big_sqft", "the big dome's floor, sq ft", lambda: f"{area(big):,.0f}")
    add("flat.ratio", "how many times the floor the big one has",
        lambda: f"{area(big) / area(small):.0f}")


RING_ERROR_IN = 0.125
"""The strut error the ring-error argument is worked for: an eighth of an
inch, the film's own example. Declared, not measured."""


def _geometry_tokens(add) -> None:
    """``geo``: subdivision and projection, the measurement audit, ring error,
    and what changes when the same dome is solved for a thin or a fat log."""
    import math

    from two_v_demo import book_math, channel_facts as cf, scratch_facts as sf
    from . import numbers

    q = numbers.quantities()
    R = q["radius_in"].value
    phi = (1 + math.sqrt(5)) / 2
    raw_r = math.sqrt(1 + phi * phi)
    icosa = 2 / raw_r
    mid = math.sqrt(1 - (icosa / 2) ** 2)
    ring = 1 / (2 * math.sin(math.pi / 10))
    fit = sf.FIT
    thin, fat = 10.0, 15.0
    t_thin, t_fat = cf.seam_types(thin), cf.seam_types(fat)
    folds = sorted(t.fold_deg for t in t_thin)
    wvb = book_math.wedge_versus_board(thin)

    add("geo.raw_r", "the twelve raw points' distance from the centre", lambda: f"{raw_r:.6f}")
    add("geo.icosa_chord", "the icosahedron's edge on a unit sphere", lambda: f"{icosa:.6f}")
    add("geo.mid_r", "how far out an edge's midpoint sits, in radii", lambda: f"{mid:.6f}")
    add("geo.sag", "how far short of the sphere the midpoint falls, in radii", lambda: f"{1 - mid:.6f}")
    add("geo.sag_pct", "the same, as a percentage", lambda: f"{100 * (1 - mid):.1f}")
    add("geo.sag_in", "the same on this book's dome, inches", lambda: f"{(1 - mid) * R:.1f}")
    # The icosahedron's counts from its twenty faces: three edges a face, each
    # shared by two; Euler's V - E + F = 2 then gives the corners. 2V halves
    # every edge (one new corner each) and cuts every face into four.
    faces = 20
    edges = faces * 3 // 2
    corners = edges - faces + 2
    add("geo.parent_edges", "edges of the icosahedron", lambda: str(edges))
    add("geo.parent_corners", "corners of the icosahedron", lambda: str(corners))
    add("geo.parent_faces", "faces of the icosahedron", lambda: str(faces))
    add("geo.sphere_corners", "corners of the whole 2V sphere", lambda: str(corners + edges))
    add("geo.sphere_edges", "edges of the whole 2V sphere", lambda: str(edges * 2 + faces * 3))
    add("geo.sphere_faces", "faces of the whole 2V sphere", lambda: str(faces * 4))
    add("geo.ring_gain", "how much the base ring multiplies a strut error", lambda: f"{ring:.6f}")
    add("geo.ring_err", "the strut error worked, inches", lambda: f"{RING_ERROR_IN:.3f}")
    add("geo.ring_r_err", "what it does to the base radius, inches", lambda: f"{RING_ERROR_IN * ring:.3f}")
    add("geo.ring_d_err", "and to the diameter, inches", lambda: f"{2 * RING_ERROR_IN * ring:.3f}")
    add("geo.fit_long", "a measured long board, inches", lambda: f"{sf.MEASURED_LONG_IN:.1f}")
    add("geo.fit_short", "a measured short board, inches", lambda: f"{sf.MEASURED_SHORT_IN:.1f}")
    add("geo.fit_r_long", "the radius the long board implies", lambda: f"{fit.radius_from_long:.3f}")
    add("geo.fit_r_short", "the radius the short board implies", lambda: f"{fit.radius_from_short:.3f}")
    add("geo.fit_r", "the radius that misses both least", lambda: f"{fit.best_fit_radius:.3f}")
    add("geo.fit_res_long", "how far the long board misses it, inches", lambda: f"{fit.long_residual:+.3f}")
    add("geo.fit_res_short", "how far the short board misses it, inches", lambda: f"{fit.short_residual:+.3f}")
    add("geo.fit_ratio", "the measured boards' ratio", lambda: f"{fit.measured_ratio:.4f}")
    add("geo.true_ratio", "the geometry's ratio of the two lengths", lambda: f"{fit.theoretical_ratio:.4f}")
    add("geo.thin", "the thin log solved, inches", lambda: f"{thin:.0f}")
    add("geo.fat", "the fat log solved, inches", lambda: f"{fat:.0f}")
    add("geo.fold_lo", "the smaller fold angle, at either log", lambda: f"{folds[0]:.3f}")
    add("geo.fold_hi", "the larger fold angle, at either log", lambda: f"{folds[1]:.3f}")
    add("geo.key_thin", "the key's base on the thin log, inches",
        lambda: " to ".join(f"{t.opening_in:.2f}" for t in sorted(t_thin, key=lambda t: t.opening_in)))
    add("geo.key_fat", "the key's base on the fat log, inches",
        lambda: " to ".join(f"{t.opening_in:.2f}" for t in sorted(t_fat, key=lambda t: t.opening_in)))
    add("geo.wedge_s", "a thin-log wedge's weakest section modulus, in3",
        lambda: f"{min(wvb.wedge.strong_s_in3, wvb.wedge.weak_s_in3):.2f}")
    add("geo.stud_s", "a two-by-four's section modulus, on edge, in3",
        lambda: f"{wvb.board.strong_s_in3:.2f}")


def _channel_tokens(add) -> None:
    """``chan``: what fits in the seam's channel (two_v_demo.channel_facts)."""
    import math

    from two_v_demo import channel_facts as cf

    types = cf.seam_types()
    wide = max(types, key=lambda t: t.gap_deg)
    tight = min(types, key=lambda t: t.gap_deg)
    rw, rt = cf.room(wide), cf.room(tight)
    air = cf.air()
    air_t = next(x for x in air["per_type"] if x["seam"] == tight)
    sp3 = cf.spacer_for(("duct_3",))
    sp4 = cf.spacer_for(("duct_4",) + cf.BUNDLE)
    hub = cf.hubs(sp4.shift_in)
    ways, node = dict(hub.by_valence), dict(hub.node_radius_in)
    pr = cf.printing()
    seams = sum(t.count for t in types)

    def fits_table() -> str:
        rows = [("item", "size", f"{tight.gap_deg:.1f} deg seam", f"{wide.gap_deg:.1f} deg seam")]
        for s in cf.SERVICES:
            size = f"{s.width_in:.2f} in" + (f" x {s.thick_in:.2f}" if s.thick_in else " round")
            rows.append((s.label, size,
                         "fits" if s.span_in <= rt.inside_round_in else "no",
                         "fits" if s.span_in <= rw.inside_round_in else "no"))
        return _table_text(rows, (42, 18, 16, 16))

    def sizes_table() -> str:
        rows = [(s.label, s.source.split(":")[0]) for s in cf.SERVICES]
        rows += [(name.replace("_", " "), f"{value:g} {unit}: {why.split(':')[0]}")
                 for name, value, unit, why in cf.KEY_CONSTANTS if name != "log_diameters_in"]
        return _table_text(rows, (44, 60))

    add("chan.area_t", "inside the key, tighter seam, sq in", lambda: f"{rt.inside_in2:.1f}")
    add("chan.area_w", "inside the key, wider seam, sq in", lambda: f"{rw.inside_in2:.1f}")
    add("chan.round_t", "largest round item, tighter seam, in", lambda: f"{rt.inside_round_in:.2f}")
    add("chan.round_w", "largest round item, wider seam, in", lambda: f"{rw.inside_round_in:.2f}")
    add("chan.gap_t", "the tighter seam's V, degrees", lambda: f"{tight.gap_deg:.1f}")
    add("chan.gap_w", "the wider seam's V, degrees", lambda: f"{wide.gap_deg:.1f}")
    add("chan.wall_mm", "the printed key's wall, mm", lambda: f"{cf.K['key_wall_in'] * cf.MM_PER_IN:.0f}")
    add("chan.fill_t", "the standard bundle's fill, tighter seam, %",
        lambda: f"{cf.fits(rt)[1] * 100:.0f}")
    add("chan.fill_w", "the standard bundle's fill, wider seam, %",
        lambda: f"{cf.fits(rw)[1] * 100:.0f}")
    add("chan.fill_rule", "the fill allowance borrowed from conduit, %",
        lambda: f"{cf.K['fill_fraction'] * 100:.0f}")
    add("chan.fits_table", "every service against both seams", fits_table)
    add("chan.sizes_table", "the declared sizes and rules, with their kind", sizes_table)
    add("chan.need_cfm", "the dome's ventilation, cfm", lambda: f"{air['need_cfm']:.0f}")
    add("chan.cfm_t", "one tighter seam's air with the bundle in, cfm", lambda: f"{air_t['cfm']:.0f}")
    add("chan.fpm", "the quiet air speed, ft/min", lambda: f"{cf.K['quiet_air_fpm']:.0f}")
    add("chan.seams_for_air", "seams that carry the dome's air",
        lambda: f"{math.ceil(air_t['seams_for_the_dome'])}")
    add("chan.shift3", "panels move out for a 3 in duct, in", lambda: f"{sp3.shift_in:.1f}")
    add("chan.grow3", "dome radius growth for a 3 in duct, %", lambda: f"{sp3.radius_growth_pct:.0f}")
    add("chan.shift4", "panels move out for a 4 in duct and the bundle, in", lambda: f"{sp4.shift_in:.1f}")
    add("chan.grow4", "dome radius growth for that, %", lambda: f"{sp4.radius_growth_pct:.0f}")
    add("chan.open4_t", "the tighter seam's opening with that spacer, in",
        lambda: f"{sp4.actual_in[types.index(tight)]:.1f}")
    add("chan.open4_w", "the wider seam's opening with that spacer, in",
        lambda: f"{sp4.actual_in[types.index(wide)]:.1f}")
    add("chan.n5", "five-way junctions", lambda: str(ways.get("5-way", 0)))
    add("chan.n6", "six-way junctions", lambda: str(ways.get("6-way", 0)))
    add("chan.nrim", "rim junctions", lambda: str(ways.get("rim", 0)))
    add("chan.node5", "a five-way node with the spacer, in across", lambda: f"{2 * node.get(5, 0):.0f}")
    add("chan.half_keys", "printed half-keys for the whole dome", lambda: str(pr.half_keys))
    add("chan.profiles", "key profiles", lambda: str(pr.profiles))
    add("chan.pieces", "printed pieces", lambda: f"{pr.segments:,}")
    add("chan.per_stick", "printed pieces per member", lambda: str(max(pr.segments_each)))
    add("chan.bed_mm", "the printer bed assumed, mm", lambda: f"{cf.K['printer_bed_in'] * cf.MM_PER_IN:.0f}")
    add("chan.kg", "plastic to print every seam, kg", lambda: f"{pr.mass_kg:.0f}")
    add("chan.usd", "what that plastic costs", lambda: f"{pr.cost_usd:,.0f}")
    add("chan.hours", "printer hours for every seam", lambda: f"{pr.print_hours:,.0f}")
    add("chan.kg_seam", "plastic per seam, kg", lambda: f"{pr.mass_kg / seams:.1f}")
    add("chan.h_seam", "printer hours per seam", lambda: f"{pr.print_hours / seams:.0f}")
    add("chan.usd_seam", "plastic cost per seam", lambda: f"{pr.cost_usd / seams:.0f}")


def _climate_tokens(add) -> None:
    """``clim``: the seam as a climate system (two_v_demo.seam_climate)."""
    from two_v_demo import seam_climate as scl

    r = scl.rings()
    bands = {b.key: b for b in r["bands"]}
    b = scl.beds()
    g = scl.regeneration()
    c = scl.cold_channel()
    cd = next(s for s in scl.SCENARIOS if s.key == "cold_dry").sensors
    lv = r["levels"]

    def deg(x: float, places: int = 1) -> str:
        return f"{x:.{places}f}".replace("-", "minus ")

    def modes_table() -> str:
        return _table_text([(k, scl.MODES[k][0]) for k in scl.ACTIVE_MODES], (14, 60))

    def weathers_table() -> str:
        rows = [("weather (estimated)", "out", "in", "dew out/in", "mode")]
        for s in scl.SCENARIOS:
            d = scl.decide(s.sensors)
            x = s.sensors
            rows.append((s.label, f"{x.t_out:.0f} C {x.rh_out * 100:.0f}%",
                         f"{x.t_in:.0f} C {x.rh_in * 100:.0f}%",
                         f"{d.dp_out:.0f} / {d.dp_in:.0f}", d.mode))
        return _table_text(rows, (34, 12, 12, 12, 12))

    def bands_table() -> str:
        rows = [("band", "seams", "feet", "slope", "")]
        rows += [(x.label, str(x.seams), f"{x.length_ft:.0f}", f"{x.slope_deg:.0f} deg",
                  "drains" if x.drains else "dead level") for x in r["bands"]]
        return _table_text(rows, (32, 8, 8, 10, 12))

    def constants_table() -> str:
        return _table_text([(n, f"{v:g} {u}", k) for n, v, u, k, _w in scl.CONSTANTS],
                           (22, 16, 12))

    add("clim.cd_t_out", "the cold, dry example: outside temperature, C", lambda: deg(cd.t_out, 0))
    add("clim.cd_rh_out", "its outside humidity, %", lambda: f"{cd.rh_out * 100:.0f}")
    add("clim.cd_t_in", "its inside temperature, C", lambda: f"{cd.t_in:.0f}")
    add("clim.cd_rh_in", "its inside humidity, %", lambda: f"{cd.rh_in * 100:.0f}")
    add("clim.cd_dp_out", "its outside dew point, C", lambda: deg(scl.dew_point(cd.t_out, cd.rh_out)))
    add("clim.cd_dp_in", "its inside dew point, C", lambda: deg(scl.dew_point(cd.t_in, cd.rh_in)))
    add("clim.cd_w_out", "grams of water per kg of that outside air",
        lambda: f"{scl.humidity_ratio(cd.t_out, cd.rh_out):.1f}")
    add("clim.cd_w_in", "grams of water per kg of that inside air",
        lambda: f"{scl.humidity_ratio(cd.t_in, cd.rh_in):.1f}")
    add("clim.modes", "how many modes the channel has", lambda: str(len(scl.ACTIVE_MODES)))
    add("clim.modes_table", "every mode and its air path", modes_table)
    add("clim.weathers", "weathers the controller is tested on", lambda: str(len(scl.SCENARIOS)))
    add("clim.weathers_table", "each weather, its dew points and the mode chosen", weathers_table)
    add("clim.constants_table", "the controller's declared constants, with their kind", constants_table)
    add("clim.margin", "how far wood is kept above the dew point, K", lambda: f"{scl.C['wood_margin_k']:.0f}")
    add("clim.below", "how far under the dew point the plate is held, K",
        lambda: f"{scl.C['plate_below_dp_k']:.0f}")
    add("clim.frost", "the plate's floor, C", lambda: f"{scl.C['frost_floor_c']:.0f}")
    add("clim.approach", "air leaving the plate, K above it", lambda: f"{scl.C['plate_approach_k']:.0f}")
    add("clim.room_t", "the example room, C", lambda: f"{c['t_air']:.0f}")
    add("clim.room_rh", "the example room, %", lambda: f"{c['rh_air'] * 100:.0f}")
    add("clim.room_dp", "the example room's dew point, C", lambda: deg(c["dp"]))
    add("clim.owner_below", "the middle of the owner's range under the dew point, K",
        lambda: f"{c['below']:.1f}")
    add("clim.owner_plate", "the owner's plate, C", lambda: deg(c["owners_plate"]))
    add("clim.plate", "the plate as held, C", lambda: deg(c["plate"]))
    add("clim.dp_after", "the dew point of air leaving the plate, C", lambda: deg(c["dp_after"]))
    add("clim.wood_min", "the coldest wood that is safe after the plate, C", lambda: deg(c["wood_min_dried"]))
    add("clim.rim", "corners on the rim", lambda: str(r["counts"][lv[0]]))
    add("clim.belt_low", "belt corners at the lower height", lambda: str(r["counts"][lv[1]]))
    add("clim.belt_high", "belt corners at the upper height", lambda: str(r["counts"][lv[2]]))
    add("clim.penta", "corners round the crown", lambda: str(r["counts"][lv[3]]))
    add("clim.bands_table", "the seams by band, with slope", bands_table)
    for key in ("lower", "belt", "upper", "pentagon", "cap"):
        add(f"clim.{key}_seams", f"seams in the {key} band", lambda k=key: str(bands[k].seams))
        add(f"clim.{key}_slope", f"the {key} band's slope, degrees",
            lambda k=key: f"{bands[k].slope_deg:.0f}")
    add("clim.stack", "stack pull at 10 K, Pa", lambda: f"{scl.stack_pa(10.0):.1f}")
    add("clim.meridian", "the rim-apex-rim seam path, feet", lambda: f"{r['meridian_ft']:.0f}")
    add("clim.seam_flow", "one seam's share of the air, cfm", lambda: f"{b.seam_flow_cfm:.0f}")
    add("clim.packed_pa", "that air through a packed seam, Pa", lambda: f"{b.seam_drop_pa:,.0f}")
    add("clim.fan_pa", "what a small in-line fan pushes, Pa", lambda: f"{scl.C['fan_static_pa']:.0f}")
    add("clim.packed_cfm", "what a packed seam passes at the fan's pressure, cfm",
        lambda: f"{b.seam_flow_at_fan_cfm:.2f}")
    add("clim.seams_sieve", "beads to pack every seam, kg", lambda: f"{b.seams_sieve_kg:.0f}")
    add("clim.seams_hold", "the water those beads would hold, kg", lambda: f"{b.seams_hold_kg:.0f}")
    add("clim.drawer_cm", "a drawer's face, cm", lambda: f"{scl.C['drawer_face_m'] * 100:.0f}")
    add("clim.drawer_depth", "a drawer's depth, cm", lambda: f"{scl.C['drawer_depth_m'] * 100:.0f}")
    add("clim.drawer_kg", "beads in a drawer, kg", lambda: f"{b.drawer_sieve_kg:.1f}")
    add("clim.drawer_hold", "water a drawer holds, kg", lambda: f"{b.drawer_hold_kg:.2f}")
    add("clim.drawer_pa", "the dome's air through a drawer, Pa", lambda: f"{b.drawer_drop_pa:.0f}")
    add("clim.frame_water", "water a wet frame must lose, kg", lambda: f"{b.frame_water_kg:.0f}")
    add("clim.drawer_fills", "drawer fills that water is", lambda: f"{b.drawers_for_frame:.0f}")
    add("clim.sieve_c", "13X regenerates at, C", lambda: f"{g['sieve_c']:.0f}")
    add("clim.silica_c", "silica gel regenerates at, C", lambda: f"{g['silica_c']:.0f}")
    add("clim.petg_c", "the printed key softens at, C", lambda: f"{g['petg_c']:.0f}")
    add("clim.seam_max_c", "the hottest air sent through a seam, C", lambda: f"{g['seam_max_c']:.0f}")
    add("clim.drawer_kwh", "heat to regenerate one drawer, kWh", lambda: f"{g['drawer_kwh']:.2f}")
    add("clim.stove_kw", "what a stove exchanger hands to clean air, kW",
        lambda: f"{scl.C['stove_exchanger_kw']:.0f}")
    add("clim.stove_min", "minutes of that per drawer", lambda: f"{g['stove_minutes']:.0f}")
    add("clim.frame_kwh", "heat to regenerate a wet frame's worth, kWh", lambda: f"{g['frame_kwh']:.0f}")
    add("clim.mc_wet", "the moisture line for wet lumber, %", lambda: f"{scl.C['mc_wet'] * 100:.0f}")
    add("clim.mc_target", "what framing settles to indoors, %", lambda: f"{scl.C['mc_target'] * 100:.0f}")


def _wood_tokens(add) -> None:
    """``wood`` and ``metal``: drying, finishing, and the metal in the seam."""
    from two_v_demo import wood_care as wc

    d = wc.sector_after_drying()
    f = wc.finish()
    e = wc.expansion()
    k = wc.conduction_ratio()
    cu_al = wc.pair("copper", "aluminium")
    ss_al = wc.pair("stainless (passive 304/316)", "aluminium")
    cu_ss = wc.pair("copper", "stainless (passive 304/316)")

    def pairs_table() -> str:
        rows = [("metal", "against", "difference", "wet service")]
        rows += [(a, b, f"{dv:.2f} V", "yes" if ok else "no") for a, b, dv, ok in wc.galvanic()]
        return _table_text(rows, (30, 30, 13, 12))

    metal_names = ("k_", "alpha_", "wet_", "seam_swing")

    def constants_table(metal: bool) -> str:
        return _table_text([(n.replace("_", " "), f"{v:g} {u}", kind)
                            for n, v, u, kind, _w in wc.CONSTANTS
                            if n.startswith(metal_names) == metal], (22, 16, 12))

    add("wood.shrink_t", "tangential shrinkage, green to oven-dry, %",
        lambda: f"{wc.C['shrink_tangential'] * 100:.1f}")
    add("wood.shrink_r", "radial shrinkage, green to oven-dry, %",
        lambda: f"{wc.C['shrink_radial'] * 100:.1f}")
    add("wood.fsp", "fibre saturation, %", lambda: f"{wc.C['fibre_saturation'] * 100:.0f}")
    add("wood.mc", "the moisture the frame dries to, %", lambda: f"{d.mc * 100:.0f}")
    add("wood.sector_dry", "a 45 degree wedge's angle once dry", lambda: f"{d.sector_dry_deg:.2f}")
    add("wood.close", "how far the wedge's angle closes, degrees", lambda: f"{d.close_deg:.2f}")
    add("wood.gap_green", "the tighter V, cut green, degrees", lambda: f"{d.gap_green_deg:.2f}")
    add("wood.gap_dry", "the tighter V once dry, degrees", lambda: f"{d.gap_dry_deg:.2f}")
    add("wood.depth_dry", "a wedge's depth once dry, in", lambda: f"{d.depth_dry_in:.2f}")
    add("wood.open_green", "the V's width at the room side, green, in", lambda: f"{d.opening_green_in:.2f}")
    add("wood.open_dry", "and dry, in", lambda: f"{d.opening_dry_in:.2f}")
    add("wood.tilt", "how far each face swings at the room side, in", lambda: f"{d.face_tilt_in:.3f}")
    add("wood.thick", "a wedge's thickest point, in", lambda: f"{d.thick_in:.1f}")
    add("wood.faster", "how many times faster a wedge dries than its log",
        lambda: f"{d.times_faster_than_log:.0f}")
    add("wood.slower", "how many times slower than a two-by", lambda: f"{d.times_slower_than_board:.0f}")
    add("wood.water_lb", "water the frame loses drying, lb", lambda: f"{d.water_lb:,.0f}")
    add("wood.water_gal", "the same, in US gallons", lambda: f"{d.water_gal:,.0f}")
    add("wood.bark_m2", "the frame's bark faces, m2", lambda: f"{f.bark_m2:.0f}")
    add("wood.sawn_m2", "the frame's sawn faces, m2", lambda: f"{f.sawn_m2:.0f}")
    add("wood.char_mm", "the char depth assumed, mm", lambda: f"{f.char_mm:.0f}")
    add("wood.char_loss", "section lost to the char, %", lambda: f"{f.section_loss_pct:.1f}")
    add("wood.oil_l", "linseed for the bark faces, every coat, litres", lambda: f"{f.oil_litres:.0f}")
    add("wood.oil_all", "linseed for every face, litres", lambda: f"{f.oil_litres_all:.0f}")
    add("wood.coats", "coats of oil", lambda: f"{wc.C['oil_coats']:.0f}")
    add("wood.oil_rate", "square metres a litre of oil covers", lambda: f"{wc.C['oil_m2_per_l']:.0f}")
    add("wood.constants_table", "the wood and finish constants, with their kind",
        lambda: constants_table(False))
    add("metal.constants_table", "the metal constants, with their kind",
        lambda: constants_table(True))

    add("metal.pairs_table", "every pair of the seam's metals", pairs_table)
    add("metal.wet_limit", "the largest difference allowed wet, V", lambda: f"{wc.C['wet_limit_v']:.2f}")
    add("metal.cu_al", "copper against aluminium, V", lambda: f"{cu_al[0]:.2f}")
    add("metal.ss_al", "stainless against aluminium, V", lambda: f"{ss_al[0]:.2f}")
    add("metal.cu_ss", "copper against stainless, V", lambda: f"{cu_ss[0]:.2f}")
    add("metal.liner_in", "the longest seam liner, in", lambda: f"{e.seam_in:.0f}")
    add("metal.swing", "the temperature swing assumed, K", lambda: f"{wc.C['seam_swing_k']:.0f}")
    add("metal.al_mm", "an aluminium liner's movement, mm", lambda: f"{e.aluminium_mm:.1f}")
    add("metal.cu_mm", "a copper liner's movement, mm", lambda: f"{e.copper_mm:.1f}")
    add("metal.pine_mm", "the pine's movement, mm", lambda: f"{e.pine_mm:.1f}")
    add("metal.al_petg", "aluminium carries heat this many times better than the key",
        lambda: f"{k['aluminium_vs_petg']:,.0f}")
    add("metal.cu_al_k", "copper against aluminium, heat", lambda: f"{k['copper_vs_aluminium']:.1f}")


def tokens() -> dict[str, Token]:
    """Every token, rebuilt. Not cached: the numbers are the point."""
    return _table()


def resolve(text: str, strict: bool = True) -> str:
    """Fill every ``{{group.name}}`` in ``text``.

    ``strict`` raises on an unknown token, which is what an export wants. The
    writing desk passes ``strict=False`` so a half-written page still renders
    with the typo visible in it.
    """
    table = tokens()

    def swap(match: re.Match) -> str:
        name = match.group(1)
        found = table.get(name)
        if found is None:
            if strict:
                near = [key for key in table
                        if key.split(".")[0] == name.split(".")[0]]
                raise KeyError(
                    f"no token {name!r}. The {name.split('.')[0]!r} "
                    f"namespace has {sorted(near)[:8]}")
            return match.group(0)
        return found.value()

    return TOKEN.sub(swap, text)


def unknown_tokens(text: str) -> tuple[str, ...]:
    """Every token in ``text`` that this module cannot fill."""
    table = tokens()
    return tuple(sorted({name for name in TOKEN.findall(text)
                         if name not in table}))


def report() -> str:
    lines = ["TOKENS", ""]
    group = ""
    for name, token in sorted(tokens().items()):
        head = name.split(".")[0]
        if head != group:
            group, _ = head, lines.append("")
            lines.append(f"  {head}")
        lines.append(f"    {{{{{name}}}}}"
                     f"{'':<{max(0, 30 - len(name))}} "
                     f"{token.value():>14}   {token.describe}")
    return "\n".join(lines)


def validate_tokens() -> None:
    """Every token resolves, and the ones the book leans on are right."""
    table = tokens()
    assert len(table) > 60, len(table)

    for name, token in table.items():
        assert "." in name, name
        assert token.describe, name
        value = token.value()
        assert value, name
        assert "{{" not in value, name

    # The book's own headline figures.
    assert resolve("{{cut.a_chord}}") == "72.000"
    assert resolve("{{dome.members}}") == "120"
    assert resolve("{{dome.panels}}") == "40"

    # Cross-references point at real chapters and move when the outline does.
    from . import outline

    for chapter in outline.BOOK.chapters:
        assert resolve(f"{{{{ch.{chapter.key}}}}}") == str(chapter.number)

    # An unknown token is loud in an export and quiet at the desk.
    try:
        resolve("{{dome.not_a_thing}}")
    except KeyError:
        pass
    else:
        raise AssertionError("an unknown token should not resolve")
    assert resolve("{{dome.not_a_thing}}", strict=False) \
        == "{{dome.not_a_thing}}"
    assert unknown_tokens("{{dome.nope}} {{cut.a_chord}}") \
        == ("dome.nope",)

    assert "TOKENS" in report()


def main(argv: list[str] | None = None) -> int:
    import argparse

    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--check", action="store_true")
    args = parser.parse_args(argv)

    validate_tokens()
    if args.check:
        print("tokens ok")
        return 0
    print(report())
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
