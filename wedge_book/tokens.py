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
    _worked_tokens(add)
    _economics_tokens(add)
    _channel_tokens(add)
    _climate_tokens(add)
    _wood_tokens(add)
    _panel_tokens(add)
    _vent_tokens(add)
    _ring_tokens(add)
    _web_tokens(add)
    _ep_tokens(add)
    _sty_tokens(add)
    _clock_tokens(add)
    _borrowed_tokens(add)
    _park_tokens(add)
    _shape_tokens(add)
    _catalogue_tokens(add)
    _kick_tokens(add)
    _staple_tokens(add)
    _foundation_tokens(add)
    _coverage_tokens(add)
    _methodology_tokens(add)
    _core_build_tokens(add)
    _franken_tokens(add)
    _hub_tokens(add)
    _pixel_tokens(add)

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


def _worked_tokens(add) -> None:
    """``work``: the films' own worked arithmetic, printed as it runs.

    Each is a ``steps_*`` function the film's math screen calls, so the book
    and the film cannot show different working. The last line of each is its
    conclusion, which the prose usually says in its own words; the block
    stops before it.
    """
    from two_v_demo import wedge_facts as wf, wedge_why_facts as yf

    def block(fn):
        return lambda: "\n".join(fn()[:-1]).rstrip()

    for name, fn in (("trunk", wf.steps_trunk), ("rectangles", wf.steps_rectangles),
                     ("compare", wf.steps_compare), ("sector", wf.steps_sector),
                     ("pinwheel_lengths", wf.steps_lengths), ("dome", wf.steps_dome),
                     ("actions", wf.steps_actions), ("assumptions", yf.steps_assumptions),
                     ("rate", yf.steps_rate), ("jig", yf.steps_jig), ("structure", yf.steps_structure),
                     ("orientation", yf.steps_orientation), ("defects", yf.steps_defects),
                     ("yield", yf.steps_yield)):
        add(f"work.{name}", f"the films' worked {name.replace('_', ' ')}, as computed", block(fn))
    # The harvest's model-independent figures: ripping the frame's members at
    # the measured rate, the fuel that took, and the day plan.
    from two_v_demo import book_math as bm

    fuel = bm.ripping_fuel()
    gal = 3.785411784
    add("rip.tanks_hour", "fuel tanks an hour while ripping (measured)", lambda: f"{fuel.tanks_per_hour:.0f}")
    add("rip.hours", "hours of ripping for the frame", lambda: f"{fuel.hours:.0f}")
    add("rip.tank_lo", "the saw's tank, low estimate, litres", lambda: f"{fuel.tank_l:.2f}")
    add("rip.tank_hi", "the saw's tank, high estimate, litres", lambda: f"{fuel.tank_high_l:.2f}")
    add("rip.tanks", "tanks of fuel for all the ripping",
        lambda: f"{fuel.tanks_per_hour * fuel.hours:.0f}")
    add("rip.gal_lo", "fuel for the ripping, low, US gal",
        lambda: f"{fuel.tanks_per_hour * fuel.hours * fuel.tank_l / gal:.1f}")
    add("rip.gal_hi", "fuel for the ripping, high, US gal",
        lambda: f"{fuel.tanks_per_hour * fuel.hours * fuel.tank_high_l / gal:.1f}")
    for phase in bm.HARVEST_PHASES:
        add(f"rip.days_{phase}", f"days of {phase}", lambda p=phase: str(bm.phase_days(p)))
    add("rip.days", "days of saw work in all", lambda: str(bm.harvest_days()))

    # Linseed oil, from the linseed film's own module.
    from two_v_demo import linseed_oil as lo

    lf = lo.facts()
    add("lin.area", "the flat-face planning envelope, sq ft", lambda: f"{lf['area_sqft']:,.0f}")
    add("lin.stock_ft", "member stock the envelope is measured on, ft", lambda: f"{lf['stock_ft']:,.1f}")
    add("lin.depth_in", "a radial face's depth, in", lambda: f"{lf['depth_in']:.1f}")
    add("lin.base_gal", "oil for the declared coats, US gal", lambda: f"{lf['base_gal']:.2f}")
    add("lin.allow_gal", "with the handling allowance, US gal", lambda: f"{lf['allowance_gal']:.2f}")
    add("lin.label_gal", "the same at the label's best coverage, US gal", lambda: f"{lf['label_gal']:.2f}")
    add("lin.labour_h", "active hand work for every coat, hours", lambda: f"{lf['labour_hours']:.1f}")
    for key in ("coats", "faces", "coverage", "handling", "minutes", "danish_wait",
                "danish_cure", "wax_wait", "wax_cure", "label_coverage"):
        add(f"lin.{key}", f"linseed constant {key}", lambda k=key: f"{lo.C[k]:g}")
    add("lin.constants_table", "the linseed constants, with their kind",
        lambda: _table_text([(n, f"{v:g} {u}", k) for n, v, u, k, _w in lo.CONSTANTS], (16, 26, 12)))
    add("lin.source", "the video the linseed film adapts",
        lambda: f"{lo.SOURCE['title']}, by {lo.SOURCE['creator']}")
    # The compound-cut audit and the assembly-line energy audit, by section.
    from two_v_demo import energetics as en, sawing as sw

    def section(report_fn, starts: str, drop_head: bool = False):
        def get() -> str:
            for part in report_fn().split("\n\n"):
                if part.lstrip().lower().startswith(starts.lower()):
                    lines = part.split("\n")
                    return "\n".join(lines[1:] if drop_head else lines).rstrip()
            raise KeyError(f"no section starting {starts!r}")
        return get

    add("saw.stock", "the stock and the saws the audit assumes", section(sw.sawing_report, "stock"))
    add("saw.settings", "every saw setup for the hubless compound cut",
        section(sw.sawing_report, "6 distinct setups"))
    add("saw.bevel_check", "the bevel check by pairing offcuts", section(sw.sawing_report, "bevel verification"))
    add("saw.five_cut", "the five-cut check on the sled fence", section(sw.sawing_report, "five-cut check"))
    add("saw.max_tilt", "how far a table saw tilts, degrees", lambda: f"{sw.TABLE_SAW_MAX_TILT_DEG:.0f}")
    add("saw.max_mitre", "how far a common mitre saw swings, degrees", lambda: f"{sw.TYPICAL_MITRE_SAW_MAX_DEG:.0f}")
    add("saw.setups", "distinct saw setups for the whole dome", lambda: str(len(sw.cut_plans())))
    add("saw.steps", "the cutting procedure, with the reason for each step",
        lambda: "\n\n".join(f"**{title}** {why}" for title, why in sw.STEPS))
    add("saw.failures", "the five ways the cut goes wrong",
        lambda: "\n".join(f"- **{title}.** {why}" for title, why in sw.FAILURES))
    for key, starts in (("product", "product"), ("energy", "elements"), ("mechanical", "mechanical work"),
                        ("by_motion", "food energy by motion"), ("mech_share", "mechanical share"),
                        ("by_limb", "mechanical lifting work"), ("by_station", "by station"),
                        ("in_food", "the crew's total"), ("constants", "external constants")):
        add(f"en.{key}", f"the energy audit's {starts} section", section(en.energy_report, starts))
    add("en.two_person_kg", "above this a lift takes two people, kg", lambda: f"{en.TWO_PERSON_LIFT_KG:.0f}")
    add("en.overhead_m", "the height above which a lift counts as overhead, m", lambda: f"{en.OVERHEAD_HEIGHT_M:.2f}")
    add("en.body_kg", "the worker the model is built for, kg", lambda: f"{en.BODY_MASS_KG:.0f}")
    # The skin: envelope and running cost, layers, solar, the shell as a
    # filter, one-sheet nesting, and this book's own ring heights.
    from two_v_demo import byod_facts as bf, hubless_geometry as hg, master_facts as mf

    def steps(fn):
        return lambda: "\n".join(fn()[:-1]).rstrip()

    add("work.water", "the roof's water plant, worked", steps(mf.steps_water))
    from two_v_demo import park_facts as pf
    add("pad.fit", "pad sizes from the catalogue's own foundations", steps(pf.steps_fit))
    add("pad.solar", "a turning pad's solar, worked", steps(pf.steps_solar))
    add("pad.starter", "the cheapest working pad, priced", lambda: "\n".join(bf.steps_starter()))
    from two_v_demo import channel_facts as _cf
    add("chan.logs", "room in the tighter seam by log size",
        lambda: "\n".join(f"{d:.0f} in log    {a:.1f} sq in inside, {r:.2f} in round"
                          for d, a, r in _cf.by_log()))
    add("skin.envelope", "dome against box, same floor: skin, volume, drag", steps(mf.steps_envelope))
    add("skin.energy", "a year of heating and cooling, both shapes", steps(mf.steps_energy))
    add("skin.layers", "the R-value ladder, layer by layer", lambda: "\n".join(bf.steps_layers()))
    add("skin.solar", "solar capacity by layout", lambda: "\n".join(bf.steps_solar()))

    def air_table() -> str:
        m = hg.airflow_model(60.0)
        rows = [f"dome radius {m.radius_in:.0f} in: shell {m.shell_area_m2:.1f} m2, "
                f"air {m.volume_cuft:.0f} cu ft"]
        rows += [f"  {c.air_changes_per_hour:4.0f} ACH -> {c.cfm:5.0f} cfm, through the wall at "
                 f"{c.face_velocity_fpm:4.2f} ft/min" for c in m.cases]
        return "\n".join(rows)
    add("skin.air", "a small dome's air pushed through its own wall", air_table)
    nest = hg.sheet_nesting()
    add("skin.nest_sheet", "the sheet the shell is nested on, ft",
        lambda: f"{nest.sheet_width / 12:.0f} ft x {nest.sheet_height / 12:.0f} ft")
    add("skin.nest_r", "the largest dome one sheet makes, radius in", lambda: f"{nest.radius:.0f}")
    add("skin.nest_d", "and its diameter, in", lambda: f"{nest.diameter:.0f}")
    add("skin.nest_floor", "and its floor, sq ft", lambda: f"{nest.floor_area_sqft:.0f}")

    import numpy as np

    from two_v_demo import channel_facts as cf

    topo = cf.reference_model().topology
    verts = np.asarray(topo.vertices, dtype=float)
    heights = sorted({round(float(z), 3) for z in verts[:, 2]})
    names = ("floor ring", "belt, low corners", "belt, high corners", "pentagon ring", "apex")

    def ring_table() -> str:
        rows = [("ring", "corners", "height", "across")]
        for name, z in zip(names, heights):
            on = verts[np.isclose(verts[:, 2], z, atol=1e-3)]
            r = float(np.mean(np.hypot(on[:, 0], on[:, 1])))
            rows.append((name, str(len(on)), f"{z / 12:.2f} ft",
                         f"{2 * r / 12:.2f} ft" if r > 1e-6 else "--"))
        return _table_text(rows, (22, 10, 10, 10))
    add("ring.table", "every ring's corners, height and diameter, this dome", ring_table)

    # The raising courses, counted from the solver's faces by the heights of
    # their corners: a face with two corners on the floor ring stands on it.
    rim_z, low_z, high_z, penta_z, apex_z = heights
    courses = {"up": 0, "down": 0, "second": 0, "cap": 0}
    for face in topo.faces:
        zs = sorted(round(float(verts[v][2]), 3) for v in face.vertices)
        if zs[2] == apex_z:
            courses["cap"] += 1
        elif zs[0] == rim_z and zs[1] == rim_z:
            courses["up"] += 1
        elif zs[0] == rim_z:
            courses["down"] += 1
        else:
            courses["second"] += 1
    add("ring.first_up", "first-course panels standing on the floor ring", lambda: str(courses["up"]))
    add("ring.first_down", "first-course panels inverted between them", lambda: str(courses["down"]))
    add("ring.first", "panels in the first course", lambda: str(courses["up"] + courses["down"]))
    add("ring.second", "panels in the second course", lambda: str(courses["second"]))
    add("ring.cap", "panels round the apex", lambda: str(courses["cap"]))
    add("work.log_butt", "the worked tree's butt diameter, inches", lambda: f"{wf.LOG.butt_diameter_in:.0f}")
    add("work.log_top", "the worked tree's top diameter, inches", lambda: f"{wf.LOG.top_diameter_in:.1f}")
    add("work.log_ft", "the worked tree's usable length, feet", lambda: f"{wf.LOG.usable_length_ft:.0f}")


def _economics_tokens(add) -> None:
    """``pine``, ``why`` and ``econ``: what a tree and an hour are worth.

    ``pine.*`` and ``why.*`` are the two economics modules' own token
    specifications -- the same names the 2 Trees book reads -- so the two books
    and the films cannot quote different figures. ``econ.*`` are the films'
    worked blocks for the chain, the house, the price guides and the pads.
    """
    from two_v_demo import (byod_facts as bf, house_economics as he, master_facts as mf,
                            park_facts as pf, pine_value_economics as pv, seed_facts as sf,
                            wedge_why_facts as yf, why_build_economics as wb)

    for name, describe, value in list(pv.token_specs()) + list(wb.token_specs()):
        add(name, describe, (lambda v=value: str(v() if callable(v) else v)))

    def steps(fn, keep_last: bool = False):
        return lambda: "\n".join(fn() if keep_last else fn()[:-1]).rstrip()

    def lines(fn):
        return lambda: "\n".join(fn()).rstrip()

    add("econ.pine_sources", "what the pine ladder rests on", lines(pv.source_lines))
    add("econ.why_score", "one cycle of the shell on one sheet", lines(wb.score_lines))
    add("econ.why_sources", "what the shelter-an-hour argument rests on", lines(wb.source_lines))
    add("econ.house_sources", "what the house numbers rest on", lines(he.source_lines))
    add("econ.house_categories", "every part of the house, bought against the dome way",
        lines(he.category_lines))
    for name, fn in (("mills", yf.steps_mills), ("middlemen", yf.steps_middlemen),
                     ("value", yf.steps_value), ("overhead", yf.steps_overhead),
                     ("why_close", yf.steps_close)):
        add(f"econ.{name}", f"the Why Wedges film's worked {name}", steps(fn))
    for name, fn in (("seed_declared", sf.steps_declared), ("seed_frame", sf.steps_frame),
                     ("seed_pad", sf.steps_pad), ("seed_invoice", sf.steps_invoice),
                     ("master_price", mf.steps_price), ("master_labour", mf.steps_labour),
                     ("park_declared", pf.steps_declared), ("park_pad_cost", pf.steps_pad_cost),
                     ("park_stay", pf.steps_stay)):
        add(f"econ.{name}", f"worked {name.replace('_', ' ')}", steps(fn))
    add("econ.deluxe", "the deluxe pad, priced", lines(bf.steps_deluxe))

    h, tr, st = he.house(), he.trailer(), he.stack()
    b = h.buckets
    money = lambda v: f"{v:,.0f}"
    add("house.price", "the survey house's price", lambda: money(h.price))
    add("house.land", "its land", lambda: money(b["land"]))
    add("house.building", "the building itself", lambda: money(b["materials"] + b["labor"] + b["fees"]))
    add("house.builder", "the builder's overhead and profit", lambda: money(b["builder"]))
    add("house.selling", "selling it: commission, marketing, financing", lambda: money(b["selling"]))
    add("house.labor", "the labor in the building", lambda: money(b["labor"]))
    add("house.labor_pct", "labor as a share of the price, %", lambda: f"{100 * b['labor'] / h.price:.1f}")
    add("house.materials", "materials in the building", lambda: money(b["materials"]))
    add("trailer.price", "the manufactured home's price", lambda: money(tr.price))
    add("trailer.dealer", "the dealer's share", lambda: money(tr.dealer))
    add("trailer.materials", "the factory's materials", lambda: money(tr.materials))
    add("trailer.payroll", "the factory's payroll", lambda: money(tr.payroll))
    add("trailer.other", "the factory's overhead and profit", lambda: money(tr.factory_other))
    add("trailer.labor_pct", "factory labor as a share of the price, %", lambda: f"{100 * tr.payroll / tr.price:.1f}")
    add("stack.buy", "the floor, bought whole", lambda: money(st.buy))
    add("stack.cash", "the dome way's cash, every hour yours", lambda: money(st.cash))
    add("stack.margin", "the builder's and seller's share you keep", lambda: money(st.margin))
    add("stack.labor", "labor you do yourself", lambda: money(st.labor))
    add("stack.trees", "lumber from your own trees", lambda: money(st.trees))
    add("stack.shape", "what the shape itself saves", lambda: money(st.shape))
    add("stack.unchanged_pct", "share of building cost the shape does not touch, %",
        lambda: f"{100 * st.unchanged:.0f}")


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


def resolve(text: str, strict: bool = True, *, table: dict[str, Token] | None = None) -> str:
    """Fill every ``{{group.name}}`` in ``text``.

    ``strict`` raises on an unknown token, which is what an export wants. The
    writing desk passes ``strict=False`` so a half-written page still renders
    with the typo visible in it.
    """
    table = tokens() if table is None else table

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
        value = found.value()
        if "\n" in value:
            # A multi-line value in an indented block (a code block, a
            # worked table) keeps the block's indentation on every line.
            line_start = text.rfind("\n", 0, match.start()) + 1
            prefix = text[line_start:match.start()]
            if prefix and not prefix.strip():
                value = value.replace("\n", "\n" + prefix)
        return value

    return TOKEN.sub(swap, text)


def export_resolver():
    """Fresh values per export, reusing its token catalogue across chapters."""
    from functools import partial
    return partial(resolve, table=tokens())


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


def _panel_tokens(add) -> None:
    """``pm`` and ``zm``: the framed-panel method -- a 3V 5/8 dome of panels
    built on a jig, its deck, and the zome framed without a bevel -- all from
    :mod:`two_v_demo.panel_method`."""
    from two_v_demo import panel_method as pm
    from . import numbers

    f = pm.facts()
    q = numbers.quantities()
    IN, FT, SQFT = 1 / 0.0254, 1 / 0.3048, 1 / 0.3048 ** 2
    pent, hexa = f["pent_class"], f["hex_class"]
    deck = f["deck"]

    def n(v, d=0):
        return lambda: f"{v:,.{d}f}"

    add("pm.constants", "the panel method's declared inputs", lambda: pm.constants_table())
    add("pm.base_ft", "the reference 3V dome across its base corners, ft", n(pm.CONSTANTS["base_ft"].value))
    add("pm.diameter_m", "the same, metres", n(f["diameter_m"], 2))
    add("pm.radius_ft", "its sphere radius, ft", n(f["radius_m"] * FT, 2))
    add("pm.height_ft", "apex above the lowest base corner, ft", n(f["height_m"] * FT, 2))
    add("pm.height_m", "the same, metres", n(f["height_m"], 2))
    add("pm.floor_sqft", "floor inside the fifteen-sided base, sq ft", n(f["floor_m2"] * SQFT))
    add("pm.fraction", "height over diameter of the 5/8 cut", n(f["height_fraction"], 3))
    add("pm.panels", "panels in the 5/8 dome", n(f["panels"]))
    add("pm.pent", "panels that belong to pentagons", n(f["pent"]))
    add("pm.hex", "panels that belong to hexagons", n(f["hex"]))
    add("pm.base_edges", "edges round the base", n(f["base_edges"]))
    add("pm.tapered", "base sections that must be tapered", n(f["tapered"]))
    add("pm.level", "base sections that sit level", n(f["level"]))
    add("pm.taper_in", "how much higher a tapered section's high end sits, in", n(f["taper_m"] * IN, 2))
    add("pm.taper_mm", "the same, mm", n(f["taper_m"] * 1000))
    for x in "ABC":
        add(f"pm.{x.lower()}_in", f"chord {x}, inches", n(f["chords"][x] * IN, 2))
        add(f"pm.{x.lower()}_mm", f"chord {x}, mm", n(f["chords"][x] * 1000))
    add("pm.pent_apex", "a pentagon panel's apex angle", n(pent.angles[0], 2))
    add("pm.pent_foot", "a pentagon panel's base angles", n(pent.angles[1], 2))
    add("pm.hex_apex", "a hexagon panel's apex angle", n(hexa.angles[0], 2))
    add("pm.hex_foot", "a hexagon panel's base angles", n(hexa.angles[1], 2))
    add("pm.hex_height_in", "a hexagon panel's apex above its base, in", n(hexa.height * IN, 2))
    add("pm.pent_height_in", "a pentagon panel's apex above its base, in", n(pent.height * IN, 2))
    add("pm.bevel_lo", "the smallest exact stick bevel, degrees", n(f["bevel_lo"], 1))
    add("pm.bevel_hi", "the largest exact stick bevel, degrees", n(f["bevel_hi"], 1))
    add("pm.bevel_mid", "one setting halfway between, degrees", n(f["bevel_mid"], 1))
    add("pm.bevel_err", "how far that one setting is off at worst, degrees",
        n((f["bevel_hi"] - f["bevel_lo"]) / 2, 1))
    b_lo, b_hi = f["folds"]["B"]
    add("pm.fold_b_lo", "the smallest fold across a B edge, degrees", n(b_lo, 1))
    add("pm.fold_b_hi", "the largest fold across a B edge, degrees", n(b_hi, 1))
    add("pm.sticks", "sticks in the whole dome (three per panel)", n(f["sticks"]))
    add("pm.stick_ft", "total stick length, ft", n(f["stick_m"] * FT))
    add("pm.distinct", "distinct sticks (length and miter)", n(f["distinct_sticks"]))
    add("pm.stick_w_in", "stick width, flat on the jig, in", n(f["stick_w_m"] * IN, 2))
    add("pm.stick_d_in", "stick depth, through the wall, in", n(f["stick_d_m"] * IN, 2))
    add("pm.sections_pent", "whole pentagons skinned in one piece", n(f["sections_pent"]))
    add("pm.sections_hex", "whole hexagons skinned in one piece", n(f["sections_hex"]))
    add("pm.sections_single", "panels left to skin one by one", n(f["sections_single"]))
    add("pm.skin_sqft", "flat area of all the panels, sq ft", n(f["skin_m2"] * SQFT))
    add("pm.deck_sides", "joists, and rim boards, in the radial deck", n(deck.sides))
    add("pm.deck_rim_in", "one rim board, long point to long point, in", n(deck.rim_length_m * IN, 1))
    add("pm.deck_rim_miter", "a rim board's end cut, off square, degrees", n(deck.rim_miter_deg))
    add("pm.deck_girders", "sides of the girder ring", n(deck.girders))
    add("pm.deck_girder_miter", "a girder's end cut, off square, degrees", n(deck.girder_miter_deg))
    add("pm.deck_sqft", "the deck's area, sq ft", n(deck.area_m2 * SQFT))

    def jig_table() -> str:
        rows = ["                     pentagon      hexagon",
                f"panels                  {pent.count:>5}        {hexa.count:>5}",
                f"sides (letters)     {'-'.join(pent.letters):>9}    {'-'.join(hexa.letters):>9}"]
        for label, k in (("base, in", 0), ("left side, in", 1), ("right side, in", 2)):
            rows.append(f"{label:<18}{pent.sides[k] * IN:>9.2f}    {hexa.sides[k] * IN:>9.2f}")
        rows.append(f"{'apex angle, deg':<18}{pent.angles[0]:>9.2f}    {hexa.angles[0]:>9.2f}")
        rows.append(f"{'base angles, deg':<18}{pent.angles[1]:>9.2f}    {hexa.angles[1]:>9.2f}")
        rows.append(f"{'height on jig, in':<18}{pent.height * IN:>9.2f}    {hexa.height * IN:>9.2f}")
        return "\n".join(rows)

    def stick_table() -> str:
        rows = ["panel      side   each panel   outer edge, in   tail miter   bevel"]
        for key, count, s in f["stick_rows"]:
            rows.append(f"{key:<10} {s.letter:>4}   {count:>10}   {s.outer_length * IN:>14.2f}   "
                        f"{s.tail_miter:>9.1f}   {s.bevel:>5.1f}")
        return "\n".join(rows)

    def zome_table() -> str:
        rows = ["row   panels   sharp corner   miter both ends   fold   outside gap, in   block bevel"]
        for r in f["zome_rows"]:
            rows.append(f"{r.row:>3}   {r.count:>6}   {r.acute_deg:>12.1f}   {r.miter_deg:>15.1f}   "
                        f"{r.fold_deg:>4.1f}   {r.gap_m * IN:>15.2f}   {r.block_bevel_deg:>11.1f}")
        return "\n".join(rows)

    def compare() -> str:
        rows = [
            "                              2V wedge dome     3V panel dome",
            f"across the base, ft           {q['diameter_ft'].value:>13.2f}     {pm.CONSTANTS['base_ft'].value:>13.2f}",
            f"height, ft                    {q['height_ft'].value:>13.2f}     {f['height_m'] * FT:>13.2f}",
            f"floor, sq ft                  {q['floor_sqft'].value:>13.0f}     {f['floor_m2'] * SQFT:>13.0f}",
            f"triangles                     {q['face_count'].value:>13.0f}     {f['panels']:>13.0f}",
            f"sticks                        {q['member_count'].value:>13.0f}     {f['sticks']:>13.0f}",
            f"distinct sticks               {2:>13}     {f['distinct_sticks']:>13}",
            f"base sections that taper      {0:>13}     {f['tapered']:>13}",
        ]
        return "\n".join(rows)

    add("pm.jig_table", "the two panels as drawn on the jig", jig_table)
    add("pm.stick_table", "every stick, cut", stick_table)
    add("pm.compare", "the wedge dome beside the panel dome", compare)
    add("zm.table", "the zome's rows, framed without a bevel", zome_table)
    add("zm.panels", "panels in the zome", n(f["zome_panels"]))
    add("zm.rows", "rows of panels", n(len(f["zome_rows"])))
    add("zm.per_row", "panels in a row", n(f["zome_rows"][0].count))
    add("zm.rim_ft", "across the zome's rim, ft", n(f["zome_rim_m"] * FT, 1))
    add("zm.height_ft", "the zome's height above its rim, ft", n(f["zome_height_m"] * FT, 1))
    add("zm.side_in", "a panel side, in", n(pm.CONSTANTS["zome_side_m"].value * IN, 1))
    gaps = [r.gap_m * IN for r in f["zome_rows"]]
    add("zm.gap_lo", "the narrowest outside gap, in", n(min(gaps), 2))
    add("zm.gap_hi", "the widest outside gap, in", n(max(gaps), 2))


def _vent_tokens(add) -> None:
    """``vent``: the cap that breathes downward -- exhaust taken at the crown,
    down the seam channels, out at the rim facing the ground -- from
    :mod:`two_v_demo.seam_vent`."""
    from two_v_demo import seam_vent as sv

    r = sv.descending_seams()
    cap = sv.capacity()
    rows = {row["weather"]: row for row in sv.weather_table()}

    def n(v, d=0):
        return lambda: f"{v:,.{d}f}"

    add("vent.constants", "the breathing cap's declared inputs", sv.constants_table)
    add("vent.table", "the cold siphon, weather by weather", sv.table_text)
    add("vent.holes", "holes through the cap above the rim", n(r.cap_penetrations))
    add("vent.falling", "seams that fall all the way from the apex to the rim", n(r.seams_down))
    add("vent.level", "dead-level seams kept out of the exhaust", n(r.level_seams))
    add("vent.path_ft", "the shortest falling path, apex to rim, ft", n(r.path_ft, 1))
    add("vent.outlets", "rim corners for ports", n(r.rim_outlets))
    add("vent.need_cfm", "fresh air the dome needs, cfm", n(cap["need_cfm"], 1))
    add("vent.seam_cfm", "one empty channel at a quiet speed, cfm", n(cap["per_seam_cfm"], 1))
    add("vent.cap_cfm", "the five cap seams together, cfm", n(cap["cap_seams_cfm"], 1))
    add("vent.headroom", "how many times the need they carry", n(cap["headroom"], 1))
    for key, row in (("hard", rows["hard winter"]), ("winter", rows["winter"]), ("cool", rows["cool"]),
                     ("mild", rows["mild"]), ("summer", rows["summer sun"])):
        add(f"vent.{key}_t", f"the {row['weather']} case, outside C", n(row["t_out"]))
        add(f"vent.{key}_pa", f"siphon in the {row['weather']} case, Pa", n(row["drive_pa"], 2))
        add(f"vent.{key}_share", f"share of the need it carries, {row['weather']}, %", n(100 * row["share"]))
        add(f"vent.{key}_fan", f"fan pressure for the rest, {row['weather']}, Pa", n(row["fan_pa"], 1))
        add(f"vent.{key}_water", f"water dropped in the keys, {row['weather']}, litres a day",
            n(row["litres_day"], 2))
    add("vent.dew", "the room air's dew point in winter, C", n(rows["winter"]["dew_point_c"], 1))
    add("vent.freeze", "outside temperature below which an outlet can ice, C", n(sv.freeze_limit()))
    add("vent.fan_static", "what the small fan can push, Pa",
        lambda: f"{__import__('two_v_demo.seam_climate', fromlist=['C']).C['fan_static_pa']:,.0f}")


def _borrowed_tokens(add) -> None:
    """``tt_<group>``: the 2 Trees book's own live figures, borrowed whole.

    Parts 9 to 14 -- the network, the pads, the catalogue, the stem cell, the
    variations and the tools -- quote the same models 2 Trees already
    tokenises (park, pad, iris, ground share, solar, product, campaign...).
    Borrowing them by name means one function behind both books' figure, which
    is the rule; re-deriving them here would be two. They are prefixed so a
    group that both books have (``pad``, ``net``, ``core``) never collides.
    The 2 Trees chapter cross-references are not borrowed: they number that
    book, not this one."""
    from two_v_demo import book_tokens as bt

    for token in bt.tokens():
        group, _, rest = token.name.partition(".")
        if group == "ch" or not re.fullmatch(r"[a-z_]+", group) or not re.fullmatch(r"[a-z_0-9]+", rest):
            continue
        add(f"tt_{group}.{rest}", f"{token.describe} (2 Trees' figure)", token.value)


def _park_tokens(add) -> None:
    """``park``: the pad, the host and the tenant, from the Dome Park and
    Bring Your Own Dome films' own worksheets (:mod:`two_v_demo.park_facts`,
    :mod:`two_v_demo.byod_facts`) -- the screens the films print, and the
    scalars the book's prose quotes out of them."""
    import park_model as pmod
    from two_v_demo import byod_facts as bf, park_facts as pf

    def steps(fn):
        return lambda: "\n".join(fn()[:-1]).rstrip()

    def lines(fn):
        return lambda: "\n".join(fn()).rstrip()

    def n(fn, d=0):
        return lambda: f"{fn():,.{d}f}"

    add("park.w_pad_cost", "a pad built and paid back, line by line", steps(pf.steps_pad_cost))
    add("park.w_exposure", "the host's two ways to earn off one piece of land", steps(pf.steps_exposure))
    add("park.w_foundation", "what the ground is worth, design by design", steps(pf.steps_foundation))
    add("park.w_hardware", "one hardware set across three sizes", steps(pf.steps_hardware))
    add("park.w_layers", "a quilted layer at a time, and what each pays back", steps(pf.steps_layers))
    add("park.w_solar", "three ways to clad the shell, fixed and tracking", steps(pf.steps_solar))
    add("park.w_ask", "what the first site's money is for", steps(pf.steps_ask))
    add("park.w_target", "the ten-thousand-dollar pad at three rents", lines(bf.steps_target))
    add("park.w_deluxe", "the deluxe pad, every line", lines(bf.steps_deluxe))
    add("park.w_growth", "the hardware brief, sized for two upgrades", lines(bf.steps_growth))
    add("park.w_capacity", "how much solar a shell can carry", lines(bf.steps_solar))

    rows = bf.payback_rows()
    for tag, (rent, net, months) in zip(("low", "mid", "high"), rows):
        add(f"park.rent_{tag}", f"the {tag} rent scenario, dollars a month", lambda v=rent: f"{v:,.0f}")
        add(f"park.net_{tag}", f"what the {tag} rent nets a year", lambda v=net: f"{v:,.0f}")
        add(f"park.months_{tag}", f"months the ten-thousand-dollar pad repays in at the {tag} rent",
            lambda v=months: f"{v:.1f}")
    add("park.pad_target", "the author's all-in pad target, dollars", n(lambda: bf.declared("pad_target")))
    add("park.dome_target", "the author's basic dome target, dollars", n(lambda: bf.declared("starter_target")))
    add("park.life_target", "the pad's service-life goal, years", n(lambda: bf.declared("life_target")))
    add("park.starter_ft", "the starter pad's diameter, ft", n(bf.starter_diameter))
    add("park.starter_cost", "the starter pad, computed, dollars", n(bf.starter_pad_cost))
    add("park.starter_gap", "how far the starter pad is over the target",
        n(lambda: bf.starter_pad_cost() - bf.declared("pad_target")))
    add("park.deluxe_cost", "the deluxe pad with its iris, dollars",
        n(lambda: pf.loaded_pad().build_cost + pmod.iris_cost(pf.loaded_pad().diameter_ft)))
    add("park.yearly_costs", "management, tax and insurance on a pad, a year",
        n(lambda: pf.home_pad().yearly_costs))
    add("park.occupancy", "share of the year a pad is leased, per cent",
        n(lambda: 100 * pmod.declared("occupancy_fraction")))

    hw = pmod.hardware_invariance()
    small, large = hw[0], hw[-1]
    add("park.hw_struts", "struts at every size of the scaled design", lambda: f"{small['struts']}")
    add("park.hw_hubs", "hubs at every size", lambda: f"{small['hubs']}")
    add("park.hw_panels", "panels at every size", lambda: f"{small['panels']}")
    add("park.hw_hub_usd", "the hub bill, the same at every size", lambda: f"{small['hub_cost']:,.0f}")
    add("park.hw_small_ft", "the smallest of the three, ft across", lambda: f"{small['diameter_ft']:.0f}")
    add("park.hw_large_ft", "the largest, ft across", lambda: f"{large['diameter_ft']:.0f}")
    add("park.hw_floor_x", "times the floor off the same parts",
        lambda: f"{large['floor_sqft'] / small['floor_sqft']:.1f}")

    goal = pmod.declared("kickstarter_goal_usd")
    count = int(pmod.declared("test_pad_count"))
    pads = [pmod.Pad(diameter_ft=s, deck="gravel") for s in pmod.pad_sizes()[:count]]
    build = sum(p.build_cost for p in pads)
    whole = pf.reference_park().economics()
    add("park.ask_goal", "the first site's goal, dollars", lambda: f"{goal:,.0f}")
    add("park.ask_pads", "test pads it builds", lambda: f"{count}")
    add("park.ask_build", "what those pads cost", lambda: f"{build:,.0f}")
    add("park.ask_rest", "what is left for everything that is not concrete", lambda: f"{goal - build:,.0f}")
    add("park.whole_pads", "pads in a whole reference park", lambda: f"{whole['pads']}")
    add("park.whole_build", "what a whole park costs to build", lambda: f"{whole['build_cost']:,.0f}")


#: The hexagon film's dome: twenty feet across, its radius in inches.
HEX_RADIUS_IN = 120.0


def _shape_tokens(add) -> None:
    """``hx`` and ``zx``: the hexagon cage and the zome, measured by
    :mod:`two_v_demo.hex_geometry` and :mod:`two_v_demo.zome_geometry` at the
    sizes their films build -- a twenty-foot hexagon dome, and a six-direction
    zome at fifty-four degrees on four-foot struts."""
    from two_v_demo import hex_geometry as hg, zome_geometry as zg
    from two_v_demo.lesson_zome import LESSON_COUNT, LESSON_PITCH, LESSON_STRUT_IN, TALL, WIDE

    r = HEX_RADIUS_IN

    def v(x, d=0):
        return lambda: f"{x:,.{d}f}"

    ti = hg.truncated_icosahedron()
    cages = (("ti", ti), ("gp2", hg.goldberg(2)), ("gp3", hg.goldberg(3)), ("gp4", hg.goldberg(4)))
    add("hx.radius_ft", "the hexagon film's dome radius, ft", v(r / 12))
    add("hx.diameter_ft", "and its diameter, ft", v(2 * r / 12))
    add("hx.pent_spare", "angle a pentagon corner leaves spare, degrees",
        v(360.0 - hg.flat_vertex_angle_sum(5)))
    add("hx.hex_sum", "three hexagon corners, degrees", v(hg.flat_vertex_angle_sum(6)))
    add("hx.ti_hubs", "hubs in the football cage", lambda: str(len(ti.vertices)))
    add("hx.ti_struts", "struts in the football cage", lambda: str(len(ti.edges)))
    add("hx.ti_panels", "panels in the football cage", lambda: str(len(ti.faces)))
    add("hx.ti_hexagons", "hexagons in it", lambda: str(ti.hexagons))
    add("hx.ti_dome_panels", "panels in its dome half", lambda: str(len(ti.dome_faces)))
    add("hx.ti_dome_struts", "struts in its dome half", lambda: str(len(ti.dome_edges)))
    build = hg.HexBuild(ti, r, 0.0)
    add("hx.ti_strut_in", "the football cage's one strut, centre to centre, in",
        v(build.strut_table()[0][2], 1))
    add("hx.ti_rim_in", "how far the football cage's rim zigzags at that size, in",
        v(build.base_wobble, 1))
    add("hx.ti_rim_ft", "the same, ft", v(build.base_wobble / 12, 1))
    for tag, cage in cages:
        add(f"hx.{tag}_lengths", f"strut lengths, {cage.notation}", lambda c=cage: str(c.strut_lengths))
        add(f"hx.{tag}_shapes", f"hexagon shapes, {cage.notation}", lambda c=cage: str(c.hex_shapes))
        add(f"hx.{tag}_panels", f"panels, {cage.notation}", lambda c=cage: str(len(c.faces)))
        add(f"hx.{tag}_warp_in", f"worst panel warp at twenty feet, {cage.notation}, in",
            lambda c=cage: f"{c.worst_planarity * r:.2f}")

    def ladder() -> str:
        rows = [f"{'cage':<26} {'panels':>6} {'strut lengths':>13} {'hexagon shapes':>14} {'worst warp, in':>14}"]
        for _tag, cage in cages:
            rows.append(f"{cage.name + ' ' + cage.notation:<26} {len(cage.faces):>6} {cage.strut_lengths:>13} "
                        f"{cage.hex_shapes:>14} {cage.worst_planarity * r:>14.2f}")
        return "\n".join(rows)
    add("hx.ladder", "every step up multiplies the shapes", ladder)

    zome = zg.polar_zonohedron(LESSON_COUNT, LESSON_PITCH)
    tall, wide = TALL, WIDE
    gold = zg.golden_zonohedron()
    s = LESSON_STRUT_IN / zome.strut_length

    def middle_cut(z):
        rings = z.level_rings
        k = len(rings) // 2
        return z.level_cut((rings[k - 1] + rings[k]) / 2)

    add("zx.n", "directions in the zome film's star", lambda: str(LESSON_COUNT))
    add("zx.pitch", "their lean from the axis, degrees", v(LESSON_PITCH))
    add("zx.strut_in", "its one strut, in", v(LESSON_STRUT_IN))
    add("zx.panels", "panels on the whole closed zome", lambda: str(len(zome.faces)))
    add("zx.struts", "struts on the whole closed zome", lambda: str(len(zome.edges)))
    add("zx.hubs", "hubs on it", lambda: str(len(zome.vertices)))
    add("zx.euler", "V - E + F", lambda: str(zome.euler))
    add("zx.dome_panels", "panels in the roof that is built", lambda: str(len(zome.dome_faces)))
    add("zx.dome_struts", "struts in the roof that is built", lambda: str(len(zome.dome_edges)))
    add("zx.templates", "panel templates", lambda: str(zome.panel_shapes))
    add("zx.hub_types", "kinds of hub", lambda: str(len(zome.hub_classes)))
    add("zx.rings", "level rings of hubs", lambda: str(len(zome.level_rings)))
    add("zx.apex_sum", "panel corners meeting at the point, degrees", v(zome.apex_angle_sum, 1))
    add("zx.apex_missing", "what they fall short of a full turn by, degrees", v(360 - zome.apex_angle_sum, 1))
    add("zx.height_ft", "the zome's height above its rim, ft", v(zome.dome_height * s / 12, 1))
    add("zx.rim_ft", "across its rim, ft", v(2 * zome.rim_radius * s / 12, 1))
    add("zx.tall_pitch", "the film's steep pitch, degrees", v(tall.pitch_deg))
    add("zx.wide_pitch", "the film's shallow pitch, degrees", v(wide.pitch_deg))
    add("zx.tall_ft", "the same struts at the steep pitch: height, ft", v(tall.dome_height * s / 12, 1))
    add("zx.wide_ft", "the same struts at the shallow pitch: height, ft", v(wide.dome_height * s / 12, 1))
    add("zx.cuts", "cut settings a level floor line needs, this zome", lambda: str(middle_cut(zome).distinct_cuts))
    add("zx.gold_faces", "faces of the golden zome", lambda: str(len(gold.faces)))
    add("zx.gold_templates", "its panel templates", lambda: str(gold.panel_shapes))
    add("zx.gold_ratio", "its panels' diagonal ratio", v(gold.rhombus_classes[0].diagonal_ratio, 4))
    add("zx.gold_cuts", "cut settings a level line needs, golden zome", lambda: str(middle_cut(gold).distinct_cuts))


def _catalogue_tokens(add) -> None:
    """``cat``: the Dome Creator's twelve shipped designs, its menus and their
    count, from the catalogue films' own worksheets
    (:mod:`two_v_demo.creator_facts`, :mod:`two_v_demo.world_facts`,
    :mod:`two_v_demo.world_chatgpt_facts`)."""
    from two_v_demo import creator_facts as cf, world_chatgpt_facts as wcf, world_facts as wf

    def steps(fn):
        return lambda: "\n".join(fn()[:-1]).rstrip()

    for key, fn in (("catalogue", cf.steps_catalogue), ("inputs", cf.steps_inputs),
                    ("styles", cf.steps_frame_styles), ("perms", cf.steps_permutations),
                    ("dials", cf.steps_dials), ("price", cf.steps_price_drivers),
                    ("build", cf.steps_construction), ("fitout", cf.steps_fitout),
                    ("framing", wf.steps_hub_vs_hubless), ("efficiency", wf.steps_efficiency),
                    ("scale", wf.steps_scale), ("frequency", wf.steps_frequency),
                    ("production", wcf.steps_production)):
        add(f"cat.w_{key}", f"the catalogue worksheet: {key}", steps(fn))

    rows = cf.design_rows()
    add("cat.count", "designs the Dome Creator ships", lambda: str(len(rows)))
    for i, row in enumerate(rows):
        t = f"cat.d{i:02d}"
        add(f"{t}_name", f"design {i}'s name", lambda r=row: r.name)
        add(f"{t}_freq", f"{row.name}: frequency", lambda r=row: str(r.frequency))
        add(f"{t}_ft", f"{row.name}: across, ft", lambda r=row: f"{r.diameter_ft:.0f}")
        add(f"{t}_sqft", f"{row.name}: floor, sq ft", lambda r=row: f"{r.floor_sqft:,.0f}")
        add(f"{t}_struts", f"{row.name}: struts", lambda r=row: str(r.struts))
        add(f"{t}_panels", f"{row.name}: panels", lambda r=row: str(r.panels))
        add(f"{t}_items", f"{row.name}: pieces of equipment", lambda r=row: str(r.props))
        add(f"{t}_usd", f"{row.name}: bill of materials, dollars", lambda r=row: f"{r.cost:,.0f}")
        add(f"{t}_per_sqft", f"{row.name}: dollars per sq ft", lambda r=row: f"{r.cost_per_sqft:,.0f}")
        add(f"{t}_tonnes", f"{row.name}: weight, tonnes", lambda r=row: f"{r.weight_kg / 1000:,.1f}")
    cheap = min(rows, key=lambda r: r.cost)
    dear = max(rows, key=lambda r: r.cost)
    add("cat.cheapest", "the cheapest design", lambda: cheap.name)
    add("cat.cheapest_usd", "its bill, dollars", lambda: f"{cheap.cost:,.0f}")
    add("cat.dearest", "the dearest design", lambda: dear.name)
    add("cat.dearest_usd", "its bill, dollars", lambda: f"{dear.cost:,.0f}")
    add("cat.cost_x", "how many times dearer the dearest is", lambda: f"{dear.cost / cheap.cost:.0f}")
    add("cat.distinct", "shells that genuinely differ", lambda: f"{cf.distinct_shells():,}")
    add("cat.years", "years of film to show each for three seconds", lambda: f"{cf.years_to_watch():,.0f}")
    add("cat.dial_settings", "settings the four dials admit", lambda: f"{cf.dial_permutations():,}")

    def random_table() -> str:
        out = [f"{'#':<3}{'freq':>5}  {'frame style':<22}{'frame material':<24}{'panels':<22}{'bill':>10}"]
        for i, config in enumerate(cf.random_designs(), 1):
            s = cf._stats(config)
            out.append(f"{i:<3}{config['frequency']:>4}V  {str(config['frame_style'])[:21]:<22}"
                       f"{str(config['frame_material'])[:23]:<24}{str(config['default_panel'])[:21]:<22}"
                       f"${s['total_cost']:>9,.0f}")
        return "\n".join(out)
    add("cat.w_random", "eight domes the dice picked, seed 7", random_table)


def _franken_tokens(add) -> None:
    """``fk``: the Frankendome -- the author's first dome, framed from whatever
    the chainsaw made -- from the Franken film's own models
    (:mod:`two_v_demo.lesson_franken`, :mod:`two_v_demo.franken_economics`)."""
    from two_v_demo import franken_economics as fe, lesson_franken as lf

    hw, hs = lf.FRANKEN, lf.SUMMARY
    bc = fe.BuildCost(120.0)
    g, fl = bc.glass, bc.floor
    brackets = hw.triangles * hw.brackets_per_triangle
    screws = brackets * hw.screws_per_bracket
    bolts = hw.unique_edges * hw.bolts_per_edge
    vals = {
        "triangles": hw.triangles, "brackets": brackets, "screws": screws,
        "screws_per_bracket": hw.screws_per_bracket, "bolts": bolts, "washers": 2 * bolts,
        "days": hw.build_days, "months": hw.stood_months,
        "per_day": hw.triangles / hw.build_days,
        "screws_day": screws / hw.build_days,
        "times_build": hw.stood_months * 30 / hw.build_days,
        "struts": hs.struts, "hubbed_struts": hs.unique_edges, "doubled": hs.doubled_edges,
        "rim": hs.rim_edges,
        "deck_sqft": fl.area_sqft, "joists": fl.joists, "joist_ft": fl.joist_feet, "blocks": fl.blocks,
        "shell_sqft": g.shell_sqft, "under_sqft": g.floor_under_sqft, "tower_sqft": g.tower_sqft,
        "laminate_sqft": g.total_sqft, "resin_gal": g.resin_gallons, "cloth_sqyd": g.cloth_sqyd,
        "screw_usd": bc.screw_cost, "glass_usd": g.total_cost, "total_usd": bc.total,
        "per_sqft": bc.cost_per_sqft,
    }
    for name, value in vals.items():
        add(f"fk.{name}", f"the Frankendome: {name.replace('_', ' ')}",
            lambda v=value: f"{v:,.0f}" if float(v).is_integer() or v >= 100 else f"{v:,.1f}")


def _hub_tokens(add) -> None:
    """``hub``: the conventional hubbed 2V dome's end cuts, from the chord
    factors the 2 Trees book already computes (``tt_dm``): a strut is a chord,
    and it leaves the sphere at half the central angle it spans."""
    import math

    from two_v_demo import book_tokens as bt

    def factor(name: str) -> float:
        return float(next(t for t in bt.tokens() if t.name == f"dm.{name}").value())

    for tag in ("short", "long"):
        add(f"hub.endcut_{tag}", f"the {tag} strut's end cut off the sphere, degrees",
            lambda t=tag: f"{math.degrees(math.asin(factor(t + '_factor') / 2)):.2f}")


def _pixel_tokens(add) -> None:
    """``pix``: the From Scratch film's worksheets for the picture half of the
    chain -- tube, normal, buffer, camera, view, projection, pixel, depth,
    light, frame -- from :mod:`two_v_demo.scratch_facts`, computed by the same
    code that draws the film."""
    from two_v_demo import scratch_facts as sf

    for key in ("tube", "normal", "buffer", "eye", "view", "projection", "pixel",
                "depth", "light", "frame"):
        fn = getattr(sf, f"steps_{key}")
        add(f"pix.w_{key}", f"the From Scratch worksheet: {key}",
            lambda f=fn: "\n".join(f()[:-1]).rstrip())


def _core_build_tokens(add) -> None:
    """``corebuild``: one utility core built on a bench, from
    :mod:`column_build` through the module-build film's own worksheets."""
    import column_build as cb
    from two_v_demo import lesson_module_build as mb

    # The film's worksheets clip every line to fit a screen; the page has room
    # for the whole sentence, so the book prints the steps at full length.
    def tools() -> str:
        return "\n".join(f"{tool:<34} {why}" for tool, why in cb.TOOLS)

    def stage_text(stage: str) -> str:
        rows = []
        for step in cb.steps(stage):
            rows.append(f"{step.number:>2}. {step.title}   {step.minutes:.0f} min   "
                        f"{', '.join(step.tools) or 'no tool'}")
            if step.checkpoint:
                rows.append(f"    check: {step.checkpoint}")
        rows.append(f"    stage total: {cb.stage_minutes(stage):.0f} min")
        return "\n".join(rows)

    add("corebuild.w_tools", "what has to be on the bench, and why", tools)
    add("corebuild.w_materials", "everything you buy for one core",
        lambda: "\n".join(mb.steps_materials()[2:]).rstrip())
    for stage, _title in cb.STAGES:
        add(f"corebuild.w_{stage}", f"the {stage} stage, step by step",
            lambda s=stage: stage_text(s))
        add(f"corebuild.{stage}_min", f"minutes in the {stage} stage",
            lambda s=stage: f"{cb.stage_minutes(s):.0f}")
    add("corebuild.steps", "steps in the core's build", lambda: str(len(cb.STEPS)))
    add("corebuild.stages", "stages", lambda: str(len(cb.STAGES)))
    add("corebuild.tools", "tools on the bench", lambda: str(len(cb.TOOLS)))
    add("corebuild.lines", "lines on the shopping list", lambda: str(len(cb.MATERIALS)))
    add("corebuild.hours", "hours once practised", lambda: f"{cb.practised_hours():.1f}")
    add("corebuild.first_hours", "hours the first one takes", lambda: f"{cb.first_build_hours():.1f}")
    add("corebuild.labour_usd", "labour at shop rate, practised", lambda: f"{cb.labour_usd():,.0f}")
    add("corebuild.psi", "the pressure test, psi", lambda: f"{cb.declared('pressure_test_psi'):.0f}")
    add("corebuild.test_min", "and how long it is held, minutes", lambda: f"{cb.declared('pressure_test_min'):.0f}")


def _kick_tokens(add) -> None:
    """``kick``: the campaign films' own figures -- the shape against a box,
    the four builds, the hat, the startup, the running cost and the paint --
    from the models those films import (:mod:`two_v_demo.dome_advantage`,
    :mod:`two_v_demo.dome_costing`, :mod:`two_v_demo.dome_performance`)."""
    from two_v_demo.dome_advantage import advantages, box_envelope, dome_envelope
    from two_v_demo.dome_costing import Startup, build_variants
    from two_v_demo.dome_performance import assemblies, running_costs, sky_cooling

    def v(fn, d=0):
        return lambda: f"{fn():,.{d}f}"

    surface, _vol, _heat, wind = advantages()
    add("kick.box_skin", "skin the box house needs for the reference floor, sq ft", v(lambda: surface.other))
    add("kick.dome_skin", "skin the dome needs for the same floor, sq ft", v(lambda: surface.dome))
    add("kick.skin_pct", "per cent less exterior", v(lambda: surface.percent_better))
    add("kick.skin_gap", "square feet of skin the box has over the dome",
        v(lambda: box_envelope().envelope_sqft - dome_envelope().envelope_sqft))
    add("kick.drag_dome", "a dome's drag coefficient", v(lambda: wind.dome, 2))
    add("kick.drag_box", "a box's drag coefficient", v(lambda: wind.other, 2))
    add("kick.drag_pct", "per cent less wind load from the shape", v(lambda: wind.percent_better))
    builds = build_variants()
    for tag, b in zip(("bare", "budget", "standard", "full"), builds):
        add(f"kick.{tag}_name", f"the {tag} build's name", lambda b=b: b.name)
        add(f"kick.{tag}_usd", f"the {tag} build, at the till, dollars", lambda b=b: f"{b.total:,.0f}")
        add(f"kick.{tag}_per_sqft", f"the {tag} build per sq ft", lambda b=b: f"{b.per_sqft:,.0f}")
    hat = builds[2]
    add("kick.floor", "the campaign dome's floor, sq ft", v(lambda: hat.floor_sqft))
    add("kick.hat_sqft", "glass on the top twenty triangles, sq ft", v(lambda: hat.glass_sqft))
    add("kick.shell_sqft", "the whole shell, sq ft", v(lambda: hat.shell_sqft))
    s = Startup()
    add("kick.equipment_usd", "the campaign's equipment, dollars", v(lambda: s.equipment_total))
    add("kick.working_usd", "the rest, for the first domes, dollars", v(lambda: s.working_capital))
    add("kick.capital_usd", "the whole ask, dollars", v(lambda: s.capital))
    dome_run, box_run = running_costs()
    add("kick.run_dome", "a year to heat and cool the dome, dollars", v(lambda: dome_run.annual_cost))
    add("kick.run_box", "the same floor in a square house, dollars", v(lambda: box_run.annual_cost))
    add("kick.run_saved", "a year never spent, dollars", v(lambda: box_run.annual_cost - dome_run.annual_cost))
    def builds_table() -> str:
        rows = [f"{'build':<22} {'at the till':>12} {'per sq ft':>10}"]
        rows += [f"{b.name.title():<22} {'$' + format(b.total, ',.0f'):>12} {'$' + format(b.per_sqft, ',.0f'):>10}"
                 for b in builds]
        return "\n".join(rows)
    add("kick.w_builds", "four ways to build the same dome", builds_table)

    def equipment() -> str:
        rows = []
        for item in s.EQUIPMENT:
            label, cost = (item[0], item[1]) if isinstance(item, tuple) else (str(item), 0.0)
            rows.append(f"{label[:44]:<44} ${cost:>9,.0f}")
        rows.append(f"{'equipment':<44} ${s.equipment_total:>9,.0f}")
        rows.append(f"{'material for the first domes':<44} ${s.working_capital:>9,.0f}")
        return "\n".join(rows)
    add("kick.w_equipment", "what the first campaign's equipment is", equipment)

    from two_v_demo import seed_facts as sf

    def steps(fn):
        return lambda: "\n".join(fn()[:-1]).rstrip()
    add("kick.w_invoice", "the standard article's invoice", steps(sf.steps_invoice))
    add("kick.w_offgrid", "running it on nothing", lambda: "\n".join(sf.steps_solar()).rstrip())

    def goal() -> str:
        # The film clips each line to fit a screen; the page prints it whole.
        import kickstarter
        lines = kickstarter.goal_lines()
        width = max(len(line.what) for line in lines)
        rows = [f"{line.what:<{width}}  ${line.usd:>8,.0f}" for line in lines]
        rows.append(f"{'the goal':<{width}}  ${kickstarter.goal():>8,.0f}")
        return "\n".join(rows)
    add("kick.w_goal", "the second campaign's goal, as a list", goal)

    paint, thin = sky_cooling(), sky_cooling(assembly=assemblies()[0])
    add("kick.paint_f", "how much cooler the painted shell runs, F",
        v(lambda: paint.solar_delta_f + paint.radiative_delta_f))
    add("kick.paint_usd", "what the paint saves a year on an insulated shell, dollars", v(lambda: paint.annual_saving))
    add("kick.paint_thin_usd", "and on a thin wall, dollars", v(lambda: thin.annual_saving))


def _methodology_tokens(add) -> None:
    """Core methodology values shared unchanged with the films and other books."""
    from infill.methodology import token_values
    for name, value in token_values().items():
        add(name, "core wedge methodology: " + name.split(".", 1)[1],
            lambda value=value: value)


def _coverage_tokens(add) -> None:
    """``cov``: how much wedge a whole dome takes -- the frame, and closing every triangle with
    pairs of wedges -- from :mod:`two_v_demo.wedge_coverage_facts` (lazy: it reads the solver)."""
    from two_v_demo import wedge_coverage_facts as wc

    def f(key, fmt):
        return lambda: fmt.format(wc.facts()[key])

    for key, fmt, describe in (
            ("long_in", "{:.2f}", "the long strut, in"), ("short_in", "{:.2f}", "the short strut, in"),
            ("members", "{:.0f}", "wedge members in the frame"), ("unique_edges", "{:.0f}", "unique edges"),
            ("iso_faces", "{:.0f}", "isosceles faces"), ("eq_faces", "{:.0f}", "equilateral faces"),
            ("frame_nominal_ft", "{:,.1f}", "the frame's wedge, nominal, ft"),
            ("frame_cut_ft", "{:,.1f}", "the frame's wedge as the solver cuts it, ft"),
            ("frame_saving_ft", "{:.1f}", "what the pinwheel cuts take off the frame, ft"),
            ("area_ft2", "{:,.1f}", "the 40 triangles' area, sq ft"),
            ("face_in_12", "{:.2f}", "a 12 in log's wedge face, in"), ("depth_in_12", "{:.2f}", "its depth, in"),
            ("open_area_ft2_12", "{:,.1f}", "open area after the frame's strip, sq ft"),
            ("infill_min_ft_12", "{:,.0f}", "infill at widest assumed continuous pitch, ft"), ("infill_max_ft_12", "{:,.0f}", "infill at narrowest assumed continuous pitch, ft"),
            ("total_min_ft_12", "{:,.0f}", "frame and infill, least, ft"), ("total_max_ft_12", "{:,.0f}", "frame and infill, most, ft"),
            ("trees_min_12", "{:.0f}", "60 ft trees, least"), ("trees_max_12", "{:.0f}", "60 ft trees, most"),
            ("trunk_min_ft_12", "{:,.0f}", "trunk, least, ft"), ("trunk_max_ft_12", "{:,.0f}", "trunk, most, ft"),
            ("frame_trunk_ft", "{:.0f}", "trunk for the frame alone, ft"), ("solver_log_in", "{:.0f}", "the simulator's log, in")):
        add(f"cov.{key.replace('_ft2', '').replace('_12', '')}", describe, f(key, fmt))
    add("cov.solver_min", "frame and infill with the simulator's log, least, ft",
        lambda: f"{wc.facts()['solver_lo']['total_ft']:,.0f}")
    add("cov.solver_max", "frame and infill with the simulator's log, most, ft",
        lambda: f"{wc.facts()['solver_hi']['total_ft']:,.0f}")
    add("cov.solver_trees_max", "60 ft trees with the simulator's log, most",
        lambda: f"{wc.facts()['solver_hi']['trees']}")
    add("cov.checked", "the session's figures that agree with the solver",
        lambda: f"{sum(ok for *_x, ok in wc.verification())} of {len(wc.verification())}")
    add("cov.calc_excess", "how far the area method runs above real pieces, %",
        lambda: f"{wc.calculator_check()['excess_pct']:.0f}")
    add("cov.table", "the overlap table",
        lambda: chr(10).join(wc.steps_infill()[4:]))
    add("cov.frame_steps", "the frame, worked", lambda: chr(10).join(wc.steps_frame()))


def _foundation_tokens(add) -> None:
    """``found`` and ``world``: the pentagonal foundation of half trunks and its star, from
    :func:`world3d.structures.foundation_facts` (which reads :mod:`infill.base`), and the
    counts of the one 3-D world that holds the foundation, the dome and the zome."""
    def f(key, fmt="{:.2f}"):
        return lambda: fmt.format(_found()[key])

    for key, describe, fmt in (
            ("side_in", "the pentagon's side, in", "{:.0f}"), ("diagonal_in", "its diagonal, in", "{:.1f}"),
            ("phi", "the golden ratio", "{:.3f}"), ("long_centre_in", "a long star piece, centreline, in", "{:.1f}"),
            ("short_centre_in", "a short star piece, centreline, in", "{:.1f}"),
            ("long_cut_in", "a long star piece, as cut, in", "{:.1f}"),
            ("short_cut_in", "a short star piece, as cut, in", "{:.1f}"),
            ("spare_in", "what one 20 ft log has left after one long and one short, in", "{:.1f}"),
            ("long_count", "long star pieces", "{:.0f}"), ("short_count", "short star pieces", "{:.0f}"),
            ("frame_count", "half trunks in the frame", "{:.0f}"), ("top_in", "the floor's top above grade, in", "{:.0f}"),
            ("interior_deg", "the pentagon's corner, degrees", "{:.0f}"),
            ("star_point_deg", "a star point, degrees", "{:.0f}")):
        add(f"found.{key.replace('_in', '').replace('_deg', '')}", describe, f(key, fmt))
    add("found.side_ft", "the pentagon's side, ft", lambda: f"{_found()['side_in'] / 12:.0f}")
    add("found.star_pieces", "star pieces in all", lambda: f"{_found()['long_count'] + _found()['short_count']}")
    add("found.all_pieces", "frame and star pieces in all",
        lambda: f"{_found()['long_count'] + _found()['short_count'] + _found()['frame_count']}")
    add("found.star_logs", "logs the star takes: one per long piece", lambda: f"{_found()['long_count']}")
    add("found.logs", "logs in the whole foundation", lambda: f"{_found()['long_count'] + _found()['frame_count']}")
    add("found.offcut", "what is left of a log after one long piece, in",
        lambda: f"{_found()['side_in'] - _found()['long_cut_in']:.1f}")
    add("found.long_minus_cut", "how much the frame's face takes off a long piece, in",
        lambda: f"{_found()['long_centre_in'] - _found()['long_cut_in']:.1f}")

    def w(key):
        return lambda: str(_world_counts()[key])
    for key, describe in (("dome", "dome members in the world"), ("zome", "zome sticks in the world"),
                          ("foundation", "foundation pieces in the world"), ("layers", "layers in the world's panel")):
        add(f"world.{key}", describe, w(key))


_FOUND: dict = {}


def _found() -> dict:
    if not _FOUND:
        from world3d import structures as ws
        _FOUND.update(ws.foundation_facts())
    return _FOUND


def _world_counts() -> dict:
    from world3d import structures as ws
    return {"dome": len(ws.dome_model().members), "zome": sum(len(p.sticks) for p in ws.zome_model().panels),
            "foundation": len(ws.foundation()), "layers": len(ws.LAYERS)}


def _staple_tokens(add) -> None:
    """``staple``: the staple house -- the papercuts of a new house against the dome's
    one invoice, from :mod:`two_v_demo.staple_facts`."""
    from two_v_demo import staple_facts as sf

    # Lazy: the facts read the numbers page, which itself resolves this table's tokens,
    # so nothing may be computed while the table is being built.
    money = lambda key: (lambda: f"{sf.facts()[key]:,.0f}")
    for key, describe in (("papercuts", "the survey house's fee and margin lines, $"),
                          ("fee_total", "its fee lines, $"), ("margin_total", "its margin lines, $"),
                          ("survey_price", "the survey house's price, $"), ("survey_lot", "its land, $"),
                          ("interest", "interest on the numbers page's loan, $"),
                          ("loan", "the loan, $"), ("loan_total", "paid back in all, $"),
                          ("dome_price", "the stem cell's price, $"), ("dome_margin", "its printed margin, $"),
                          ("dome_standing", "standing on its pad, $"), ("site_same", "the same floor, site-built, $"),
                          ("mhs_same", "the same floor, manufactured, $"),
                          ("mhs_gap", "what a manufactured home of the same floor costs beyond the dome, $")):
        add(f"staple.{key}", describe, money(key))
    for key, describe, fmt in (("papercut_lines", "how many fee and margin lines", "{:.0f}"),
                               ("fee_lines", "fee lines", "{:.0f}"), ("margin_lines", "margin lines", "{:.0f}"),
                               ("building_lines", "separately priced lines of the building", "{:.0f}"),
                               ("hands", "sets of hands in one stud", "{:.0f}"),
                               ("papercut_pct", "the papercuts as a share of the price, %", "{:.0f}"),
                               ("papercut_domes", "the papercuts, in stem cells", "{:.0f}"),
                               ("interest_domes", "the interest, in stem cells", "{:.1f}"),
                               ("interest_pct_of_loan", "interest as a share of the loan, %", "{:.0f}"),
                               ("loan_rate", "the loan's rate, %", "{:g}"), ("loan_years", "its years", "{:.0f}"),
                               ("dome_lines", "lines on the stem cell's invoice", "{:.0f}"),
                               ("dome_margin_pct", "its margin, %", "{:.0f}"),
                               ("dome_floor", "its floor, sq ft", "{:.0f}"),
                               ("dome_vs_site_pct", "the dome as a share of site-built, %", "{:.0f}"),
                               ("dome_vs_mhs_pct", "the dome as a share of manufactured, %", "{:.0f}")):
        add(f"staple.{key}", describe, (lambda k, fm: (lambda: fm.format(sf.facts()[k])))(key, fmt))
    add("staple.worked_papercuts", "the papercuts, worked", lambda: chr(10).join(sf.steps_papercuts()))
    add("staple.worked_interest", "the interest, worked", lambda: chr(10).join(sf.steps_interest()))
    add("staple.worked_invoice", "the staple's invoice, worked", lambda: chr(10).join(sf.steps_staple()))


def _clock_tokens(add) -> None:
    """``clock``: the forty-hour clock in the margins of the how-to chapters,
    stage by stage, from :func:`wedge_book.systems.build_stages`."""
    from . import systems

    stages = systems.build_stages()
    week = systems.declared("working_week_hours")
    BASIS = {"measured": "the owner's measured rate", "estimate": "this book's estimate",
             "allowance": "the owner's own allowance"}

    def bar(s) -> str:
        done, now = 100 * s.before / week, 100 * s.hours / week
        return ('<span class="clockbar" role="img" aria-label="'
                f'{s.after:.1f} of {week:.0f} hours">'
                f'<span class="done" style="width:{done:.1f}%"></span>'
                f'<span class="now" style="left:{done:.1f}%;width:{now:.1f}%"></span></span>')

    for s in stages:
        add(f"clock.{s.key}_h", f"hours of {s.label}", lambda s=s: f"{s.hours:.1f}")
        add(f"clock.{s.key}_from", f"clock reading before {s.label}", lambda s=s: f"{s.before:.1f}")
        add(f"clock.{s.key}_to", f"clock reading after {s.label}", lambda s=s: f"{s.after:.1f}")
        add(f"clock.{s.key}_left", f"hours of the week left after {s.label}",
            lambda s=s: f"{week - s.after:.1f}")
        add(f"clock.{s.key}_kind", f"whether {s.label} is measured or estimated",
            lambda s=s: BASIS[s.basis])
        add(f"clock.{s.key}_bar", f"the clock drawn after {s.label}", lambda s=s: bar(s))
    add("clock.week", "the week the book is named after, hours", lambda: f"{week:.0f}")
    add("clock.total", "the clock at the end, error allowed for", lambda: f"{stages[-1].after:.1f}")

    def table() -> str:
        rows = [f"{'stage':<44} {'hours':>6} {'clock':>6}   basis"]
        rows += [f"{s.label:<44} {s.hours:>6.1f} {s.after:>6.1f}   "
                 f"{s.basis}" for s in stages]
        rows.append(f"{'the week':<44} {'':>6} {week:>6.0f}")
        return "\n".join(rows)
    add("clock.table", "the forty-hour clock, stage by stage", table)
    add("clock.off", "the work the clock does not count",
        lambda: ", ".join(label for _ref, label in systems.OFF_THE_CLOCK))


def _md_table(head, rows) -> str:
    """Columns aligned with spaces: an indented block in the manuscript keeps
    them, and the print edition turns aligned text into a real table."""
    cells = [tuple(str(c) for c in head)] + [tuple(str(c) for c in r) for r in rows]
    w = [max(len(r[i]) for r in cells) for i in range(len(head))]
    return "\n".join("  ".join(c.ljust(w[i]) for i, c in enumerate(r)).rstrip() for r in cells)


def _sty_tokens(add) -> None:
    """``sty``: the cabin styled every way the Dome Creator can style it, from
    :func:`two_v_demo.cabin_styles.facts` -- one Creator rebuild per row."""
    from two_v_demo import cabin_styles as cs

    f = cs.facts()
    pl, b = f["price_list"], f["base"]
    LB = cs.LB

    def n(v, d=0):
        return lambda: f"{v:,.{d}f}"

    def usd(v):
        return f"${v:,.0f}"

    def by(rows, label):
        return next(r for r in rows if r["label"] == label)

    # -- the cabin in the Creator ------------------------------------------
    add("sty.diameter", "the cabin's diameter, in the Creator, ft", n(f["diameter_ft"], 2))
    add("sty.radius_m", "the cabin's sphere radius, m", n(f["radius_m"], 2))
    add("sty.floor", "the Creator's floor area for the cabin, sq ft", n(f["floor_sqft"]))
    add("sty.shell", "the Creator's shell area for the cabin, sq ft", n(f["surface_sqft"]))
    add("sty.struts", "struts in the Creator's cabin", n(f["struts"]))
    add("sty.panels", "panels in the Creator's cabin", n(f["panels"]))
    add("sty.base_frame_mat", "the bare cabin's frame material", lambda: f["base_parts"]["frame_material"])
    add("sty.base_shape", "the bare cabin's strut shape", lambda: f["base_parts"]["strut_shape"])
    add("sty.base_panel", "the bare cabin's panels", lambda: f["base_parts"]["default_panel"])
    add("sty.base_layer", "the bare cabin's cladding",
        lambda: ", ".join(x for x in f["base_parts"]["layers"] if x != "None") or "none")
    add("sty.base_foundation", "the bare cabin's foundation", lambda: f["base_parts"]["foundation"])
    add("sty.bare_total", "the bare cabin, priced by the Creator, $", n(b["total"]))
    add("sty.bare_frame", "the Creator's frame line for the cabin, $", n(b["frame"]))
    add("sty.bare_panels", "the Creator's panel line, $", n(b["panels"]))
    add("sty.bare_cladding", "the Creator's cladding line, $", n(b["cladding"]))
    add("sty.bare_foundation", "the Creator's foundation line, $", n(b["foundation"]))
    add("sty.bare_hours", "the Creator's hours for the bare cabin", n(b["hours"]))
    add("sty.bare_lb", "the bare cabin's weight, lb", n(b["weight_kg"] * LB))
    add("sty.frame_lb", "the Creator's frame weight, lb", n(b["frame_kg"] * LB))
    # -- twelve styles ------------------------------------------------------
    st = sorted(f["styles"], key=lambda r: r["total"])
    add("sty.styles", "the cabin in each design's finish",
        lambda: _md_table(("Style", "Panels", "Cladding", "Foundation", "Total", "Weight", "Hours"),
                          [(r["label"], r["panel_name"], ", ".join(r["layer_names"]) or "-", r["foundation_name"],
                            usd(r["total"]), f"{r['weight_kg'] * LB:,.0f} lb", f"{r['hours']:.0f}") for r in st]))
    add("sty.style_lines", "each style, line by line",
        lambda: _md_table(("Style", "Frame", "Panels", "Cladding", "Foundation", "Total"),
                          [(r["label"], usd(r["frame"]), usd(r["panels"]), usd(r["cladding"]), usd(r["foundation"]),
                            usd(r["total"])) for r in st]))
    add("sty.cheap_style", "the cheapest style", lambda: st[0]["label"])
    add("sty.cheap_total", "the cheapest style, $", n(st[0]["total"]))
    add("sty.dear_style", "the dearest style", lambda: st[-1]["label"])
    add("sty.dear_total", "the dearest style, $", n(st[-1]["total"]))
    add("sty.style_ratio", "dearest style over cheapest", n(st[-1]["total"] / st[0]["total"], 1))
    add("sty.tree_found", "the treehouse platform under the cabin, $",
        n(by(f["styles"], "Treehouse Canopy Dome")["foundation"]))
    # -- one menu at a time ---------------------------------------------------
    def sweep(key, title, line):
        rows = sorted(f[key], key=lambda r: r["total"])
        add(f"sty.{key}", f"the cabin, {title}",
            lambda: _md_table((title.title(), "Its line", "Weight", "Cabin total"),
                              [(r["label"], usd(r[line]), f"{r['weight_kg'] * LB:,.0f} lb", usd(r["total"]))
                               for r in rows]))
        add(f"sty.{key}_lo", f"cheapest {title}", lambda: rows[0]["label"])
        add(f"sty.{key}_lo_usd", f"the cabin at the cheapest {title}, $", n(rows[0]["total"]))
        add(f"sty.{key}_hi", f"dearest {title}", lambda: rows[-1]["label"])
        add(f"sty.{key}_hi_usd", f"the cabin at the dearest {title}, $", n(rows[-1]["total"]))
        add(f"sty.{key}_span", f"what the {title} menu swings, $", n(rows[-1]["total"] - rows[0]["total"]))
    sweep("by_frame", "frame material", "frame")
    fr_rows = sorted(f["by_frame"], key=lambda r: r["total"])
    add("sty.by_frame", "the cabin, each frame material in its own section",
        lambda: _md_table(("Frame material", "Made as", "Width", "Taken from", "Frame line", "Frame weight",
                           "Cabin total"),
                          [(r["label"], r["shape"], f"{r['width_cm']:g} cm", r["source"], usd(r["frame"]),
                            f"{r['frame_kg'] * LB:,.0f} lb", usd(r["total"])) for r in fr_rows]))
    sweep("by_panel", "panel", "panels")
    sweep("by_layer", "cladding", "cladding")
    sweep("by_foundation", "foundation", "foundation")
    spans = sorted(((t, max(r["total"] for r in f[k]) - min(r["total"] for r in f[k]))
                    for k, t in (("by_frame", "the frame material"), ("by_panel", "the panels"),
                                 ("by_layer", "the cladding"), ("by_foundation", "the foundation"))),
                   key=lambda x: -x[1])
    add("sty.ranking", "the menus, ranked by what each swings on its own",
        lambda: ", ".join(f"{t} (${v:,.0f})" for t, v in spans[:-1]) + f" and {spans[-1][0]} (${spans[-1][1]:,.0f})")

    def lead(r):
        return max(("frame", "panels", "cladding", "foundation"), key=lambda k: r[k])
    leads = [lead(r) for r in f["styles"]]
    for k in ("frame", "panels", "cladding", "foundation"):
        add(f"sty.lead_{k}", f"styles whose biggest line is the {k}", n(leads.count(k)))
    # -- every skin on every frame --------------------------------------------
    fp = f["frame_panel"]
    short = {"Galvanized Steel": "Galv", "Structural Steel": "Steel", "Rebar Steel": "Rebar",
             "Aluminum": "Alum", "Timber (SPF)": "Timber", "Whole Tree Trunk": "Trunk", "PVC Pipe": "PVC",
             "Bamboo": "Bamboo"}
    add("sty.grid", "the cabin, every panel on every frame material, $",
        lambda: _md_table(("Panel \\ frame",) + tuple(short.get(x, x) for x in fp["frames"]),
                          [(pa,) + tuple(f"{fp['cost'][f'{fr}|{pa}']:,.0f}" for fr in fp["frames"])
                           for pa in fp["panels"]]))
    cells = sorted(fp["cost"].items(), key=lambda kv: kv[1])
    add("sty.grid_cells", "combinations in the frame x panel table", n(len(cells)))
    add("sty.grid_lo", "the cheapest frame and panel",
        lambda: " with ".join(reversed(cells[0][0].split("|"))))
    add("sty.grid_lo_usd", "the cheapest frame and panel, $", n(cells[0][1]))
    add("sty.grid_hi", "the dearest frame and panel", lambda: " with ".join(reversed(cells[-1][0].split("|"))))
    add("sty.grid_hi_usd", "the dearest frame and panel, $", n(cells[-1][1]))
    lf = f["layer_foundation"]
    add("sty.grid2", "the cabin, every cladding on every foundation, $",
        lambda: _md_table(("Cladding \\ foundation",) + tuple(lf["foundations"]),
                          [(la,) + tuple(f"{lf['cost'][f'{la}|{fo}']:,.0f}" for fo in lf["foundations"])
                           for la in lf["layers"]]))
    c = f["counts"]
    add("sty.shells", "shells the Creator's menus multiply to", n(c["shells"]))
    add("sty.distinct", "distinct shells, inert settings removed", n(c["distinct"]))
    add("sty.fitouts", "fit-outs the room menus multiply to", n(c["fitouts"]))
    add("sty.dials", "dial settings", n(c["dials"]))
    # -- the price list -------------------------------------------------------
    add("sty.list_frame", "frame materials, as declared",
        lambda: _md_table(("Frame material", "Density", "Price", "A hub"),
                          [(r["name"], f"{r['density']:,.0f} kg/m3", f"${r['per_kg']:.2f}/kg", f"${r['hub']:.2f}")
                           for r in pl["frame"]]))
    add("sty.list_panels", "panel types, as declared",
        lambda: _md_table(("Panel", "Price", "Weight", "Note"),
                          [(r["name"], f"${r['per_m2']:.2f}/m2 (${r['per_m2'] / 10.7639:.2f}/sq ft)",
                            f"{r['kg_m2']:g} kg/m2",
                            "window" if r["window"] else (f"{r['watts_m2']:.0f} W/m2" if r["watts_m2"] else ""))
                           for r in pl["panels"]]))
    add("sty.list_layers", "cladding layers, as declared",
        lambda: _md_table(("Cladding", "Price", "Thickness"),
                          [(r["name"], f"${r['per_m2']:.2f}/m2 (${r['per_m2'] / 10.7639:.2f}/sq ft)",
                            f"{r['thick_mm']:.0f} mm") for r in pl["layers"]]))
    add("sty.list_foundations", "foundations, as declared",
        lambda: _md_table(("Foundation", "Price", "Weight"),
                          [(r["name"], f"${r['per_m2']:.2f}/m2 (${r['per_m2'] / 10.7639:.2f}/sq ft)",
                            f"{r['kg_m2']:,.0f} kg/m2") for r in pl["foundations"]]))
    add("sty.list_parts", "panel fixings, as declared",
        lambda: _md_table(("Part", "Each", "Minutes to fit"),
                          [(r["name"], f"${r['cost']:.2f}", f"{r['minutes']:g}") for r in pl["components"]]))
    rt = pl["rates"]
    add("sty.wire", "wire, $ a metre", n(rt["wire_m"], 2))
    add("sty.pex", "PEX, $ a metre", n(rt["pex_m"], 2))
    add("sty.drain", "drain, $ a metre", n(rt["drain_m"], 2))
    add("sty.rough", "rough-in per fixture, $", n(rt["fixture_rough"]))
    add("sty.screw", "a screw, $", n(rt["screw"], 2))
    props = sorted(pl["props"], key=lambda r: (r["category"], r["name"]))
    add("sty.items", "every piece of equipment the Creator stocks",
        lambda: _md_table(("Category", "Item", "Price", "Weight", "Power"),
                          [(r["category"], r["name"], usd(r["cost"]), f"{r['kg'] * LB:,.0f} lb",
                            f"{r['watts']:,.0f} W" if r["watts"] else "-") for r in props]))
    add("sty.item_count", "items in the Creator's equipment list", n(len(props)))
    add("sty.item_cats", "categories they fall in", n(len({r["category"] for r in props})))
    pk = sorted(f["packages"], key=lambda r: r["cost"])
    add("sty.packages", "each design's fit-out, priced",
        lambda: _md_table(("Fit-out of", "Items", "Price", "Weight", "Power"),
                          [(r["name"], str(r["items"]), usd(r["cost"]), f"{r['kg'] * LB:,.0f} lb",
                            f"{r['watts']:,.0f} W") for r in pk]))
    add("sty.rooms", "what a floor section can be assigned to", lambda: ", ".join(pl["rooms"]).lower())
    add("sty.room_count", "room types", n(len(pl["rooms"])))


def _ep_tokens(add) -> None:
    """``ep``: every piece numbered -- a triangle filled and the floor framed,
    from :func:`infill.facts.facts`, the same function the film reads."""
    from infill import base as bs
    from infill.constants import table as infill_table
    from infill.facts import by, facts

    f = facts()
    B, W = f["base"], f["wedge"]
    t0, t1 = f["types"]
    c1, c2 = W["cuts"][0], W["cuts"][1]

    def n(v, d=0):
        return lambda: f"{v:,.{d}f}"

    add("ep.infill_declared", "figures the triangle calculator declares", n(f["infill_constants"]))
    add("ep.infill_table", "the triangle calculator's declared table", infill_table)
    add("ep.base_declared", "figures the floor calculator declares", n(B["declared"]))
    add("ep.base_table", "the floor calculator's declared table",
        lambda: _md_table(("Figure", "Value", "Kind", "Why"),
                          [(n, f"{v:g} {u}".strip(), k, w) for n, v, u, k, w in bs.BASE_CONSTANTS]))
    add("ep.strut", "the dome's longest stick, in", n(f["strut_in"]))
    add("ep.dome_ft", "the dome's diameter, ft", n(f["dome_diameter_ft"], 1))
    add("ep.lss", "triangles with a long base and two short sides", n(t0["count"]))
    add("ep.lll", "triangles with three long sides", n(t1["count"]))
    add("ep.long_in", "a long edge, in", n(t0["edges"][0], 2))
    add("ep.short_in", "a short edge, in", n(t0["edges"][1], 2))
    add("ep.frame_log", "the frame's log, in", n(f["frame_log_in"]))
    add("ep.infill_log", "the infill's log, in", n(f["infill_log_in"]))
    add("ep.depth", "how deep the frame's tray is, in", n(f["thickness_in"], 2))
    add("ep.fold_a", "the smaller seam fold, deg", n(f["folds"][0], 2))
    add("ep.fold_b", "the larger seam fold, deg", n(f["folds"][1], 2))
    add("ep.wedges", "wedges in the striped, flip-flopped fill", n(W["pieces"]))
    add("ep.wedge_long", "the longest wedge, in", n(W["longest"], 1))
    add("ep.wedge_short", "the shortest wedge, in", n(W["shortest"], 1))
    add("ep.piece", "the worked piece's number", n(W["piece"]))
    add("ep.point", "the worked piece along its point, in", n(W["corners"][0], 2))
    add("ep.corner_b", "the worked piece's second long corner, in", n(W["corners"][1], 2))
    add("ep.corner_c", "the worked piece's third long corner, in", n(W["corners"][2], 2))
    add("ep.mitre", "the worked piece's mitre, deg", n(c1["mitre"], 1))
    add("ep.bevel", "the worked piece's bevel, deg", n(c1["bevel"]))
    add("ep.keeper1", "which side of the blade the keeper lies, cut 1",
        lambda: "right" if c1["keeper_right"] else "left")
    add("ep.off1_long", "first offcut at its longest, in", n(c1["off_long"], 2))
    add("ep.off1_short", "first offcut at its shortest, in", n(c1["off_short"], 2))
    add("ep.off2_long", "second offcut at its longest, in", n(c2["off_long"], 2))
    add("ep.sheet_halves", "pieces a covering sheet is cut into", n(f["sheet"]["pieces"]))
    for k, v in enumerate(f["sheet"]["bevels"]):
        add(f"ep.sheet_bevel{k + 1}", f"a covering sheet's edge bevel {k + 1}, deg", n(v, 1))
    perms = f["perms"]
    add("ep.perm_count", "ways to fill the triangle shown", n(len(perms)))
    add("ep.perm_table", "every way to fill it, and how many pieces",
        lambda: _md_table(("Material", "Pattern", "Lay", "Fill or cover", "Pieces"),
                          [(p["material"], p["arrangement"], p["lay"] or "-", p["mode"], str(p["pieces"]))
                           for p in perms]))
    rd = f["rounds"]
    add("ep.round_layers", "layers of log rounds", n(rd["layers"]))
    add("ep.round_thick", "a log round's thickness, in", n(rd["thick_in"], 1))
    add("ep.round_whole", "rounds that go in whole", n(rd["kinds"].get("full", 0)))
    add("ep.round_wall", "rounds cut at the wall", n(rd["kinds"].get("wall", 0)))
    add("ep.round_gaps", "gap pieces copied and traced", n(rd["kinds"].get("copy", 0)))
    add("ep.round_pieces", "pieces in the rounds fill", n(rd["pieces"]))
    add("ep.side_ft", "the floor pentagon's side, along the round backs, ft", n(B["side_ft"]))
    add("ep.apothem", "the pentagon's crown apothem, ft", n(B["apothem_ft"], 2))
    add("ep.inner_r", "biggest circle inside the flat faces, ft", n(B["inner_r_ft"], 2))
    add("ep.corner_r", "corner to centre, ft", n(B["corner_r_ft"], 2))
    add("ep.area", "floor area, ft2", n(B["area_ft2"]))
    add("ep.dome_need", "radius the dome's foot needs, ft", n(B["dome_need_ft"], 2))
    add("ep.overhang", "allowance for the dome's frame at its foot, in", n(B["overhang_in"]))
    add("ep.margin", "spare between the dome's foot and the flat faces, ft", n(B["margin_ft"], 2))
    add("ep.corner_deg", "a frame corner's cut, deg off square", n(B["corner_deg"]))
    add("ep.back_in", "a frame trunk along its round back, in", n(B["frame_back_in"], 2))
    add("ep.top_in", "a frame trunk along its top, in", n(B["frame_top_in"], 2))
    add("ep.trim_in", "what a corner cut takes off the top, each end, in",
        n((B["frame_back_in"] - B["frame_top_in"]) / 2, 2))
    add("ep.star_pieces", "star pieces", n(B["star_members"]))
    add("ep.star_long", "a star piece, outer, in", n(B["star_pieces"][1], 1))
    add("ep.star_short", "a star piece, inner, in", n(B["star_pieces"][0], 1))
    star = by(f["patterns"], "star")
    add("ep.star_gap", "the widest deck gap under the star alone, in", n(star["deck_gap_in"]))
    add("ep.deck_allow", "the most a 2x6 deck may cross, in", n(B["deck_allow_in"]))
    add("ep.joists", "joists in the star + joists floor", n(B["roles"]["joist"]))
    add("ep.joist_name", "the joists", lambda: B["joist_name"])
    add("ep.spacing", "joist spacing, in on centre", n(B["spacing_in"]))
    add("ep.deck_gap", "the widest deck gap, star + joists, in", n(B["deck_gap_in"], 1))
    add("ep.joist_depth", "a 2x8 on edge, in", n(B["joist_depth_in"], 2))
    add("ep.saw_h", "what the mitre saw cuts standing on edge, in", n(B["saw_height_in"]))
    add("ep.joist_bevel", "the worked joist's bevel laid flat, deg", n(B["joist"]["bevel"]))
    add("ep.joist_end1", "the worked joist's other end", lambda: B["joist"]["end1"])
    add("ep.bevel_max", "the most a single-bevel saw tilts, deg", n(B["bevel_max"]))
    add("ep.live", "floor live load, lb/ft2", n(B["live_psf"]))
    add("ep.dead", "floor dead load, lb/ft2", n(B["dead_psf"]))
    add("ep.total_lb", "the floor's whole load, lb", n(B["total_lb"]))
    add("ep.pier_sum", "what the piers carry, lb", n(B["pier_sum_lb"]))
    add("ep.fb", "the wood's declared bending strength, psi", n(B["fb_psi"]))
    add("ep.extra", "piers added under spans that failed", n(B["extra_piers"]))
    add("ep.worst", "the hardest span, % of what it carries", n(100 * B["worst"]))
    add("ep.members", "members in the star + joists floor", n(B["members"]))
    add("ep.piers", "piers under it", n(B["piers"]))
    add("ep.soil", "soil bearing, lb/ft2", n(B["soil_psf"]))
    add("ep.pad_min", "the smallest pad, in square", n(B["pad_min_in"]))
    add("ep.pier_max", "the heaviest pier, lb", n(B["pier_max_lb"]))
    add("ep.pad_max", "its pad, in square", n(B["pad_max_in"]))
    add("ep.hangers", "joist ends hung on a hanger or notched", n(B["hangers"]))
    add("ep.logs", "logs to fell or buy, star + joists", n(B["logs"]))
    add("ep.usd", "bought materials, star + joists, $", n(B["usd"]))
    add("ep.patterns", "every floor pattern, side by side",
        lambda: _md_table(("Pattern", "Pieces", "Piers", "Hardest span", "Deck gap", "Logs", "Bought"),
                          [(r["name"], str(r["members"]), str(r["piers"]), f"{100 * r['worst']:.0f}%",
                            f"{r['deck_gap_in']:.1f} in " + ("ok" if r["deck_ok"] else "FAILS"), str(r["logs"]),
                            f"${r['usd']:,.0f}") for r in f["patterns"]]))
    add("ep.gravel", "every floor pattern on a gravel bed",
        lambda: _md_table(("Pattern", "Pieces", "Logs", "Bought"),
                          [(r["name"], str(r["members"]), str(r["logs"]), f"${r['usd']:,.0f}")
                           for r in f["gravel"]]))
    add("ep.materials", "the star + joists floor with its star in each material",
        lambda: _md_table(("The star in", "Piers", "Added mid-span", "Logs", "Bought"),
                          [(r["material"], str(r["piers"]), str(r["extra"]), str(r["logs"]), f"${r['usd']:,.0f}")
                           for r in f["materials"]]))
    beams, fan, wheel, rings = (by(f["patterns"], k) for k in ("beams", "fan", "wheel", "rings"))
    add("ep.beams_worst", "beams + joists, hardest span, %", n(100 * beams["worst"]))
    add("ep.rings_worst", "nested rings on piers, hardest span, %", n(100 * rings["worst"]))
    add("ep.rings_piers", "nested rings on piers, piers", n(rings["piers"]))
    add("ep.fan_pier", "the fan's centre pier, lb", n(fan["pier_max_lb"]))
    add("ep.fan_pad", "the fan's centre pad, in", n(fan["pad_max_in"]))
    add("ep.wheel_pier", "the wheel's centre pier, lb", n(wheel["pier_max_lb"]))
    g_rings, g_sj = by(f["gravel"], "rings"), by(f["gravel"], "star_joists")
    add("ep.rings", "nested rings inside the frame", n(B["rings"]))
    add("ep.rings_usd", "nested rings on gravel, bought, $", n(g_rings["usd"]))
    add("ep.rings_logs", "nested rings on gravel, logs", n(g_rings["logs"]))
    add("ep.gravel_sj_logs", "star + joists on gravel, logs", n(g_sj["logs"]))
    mats = {r["prim"]: r for r in f["materials"]}
    add("ep.m4_piers", "the star in 4x4, piers", n(mats["4x4"]["piers"]))
    add("ep.m4_extra", "the star in 4x4, piers added", n(mats["4x4"]["extra"]))
    add("ep.m6_usd", "the star in 6x6, bought, $", n(mats["6x6"]["usd"]))
    add("ep.mround_logs", "the star in whole logs, logs", n(mats["round"]["logs"]))


def _web_tokens(add) -> None:
    """``web``: the dome built in the air from a cable web between four trees,
    from :mod:`two_v_demo.sky_web` -- at the owner's weighed strut weights."""
    from two_v_demo import sky_web as sw

    f = sw.facts()
    C, O = sw.C, sw.O

    def n(v, d=0):
        return lambda: f"{v:,.{d}f}"

    w8, x, sp, st = f["weights"], f["x"], f["spread"], f["spread_taut"]
    t1, tt, t2, pv = f["tree1"], f["tree1_taut"], f["tree2"], f["post"]
    h, ho, w, r, sf, rc = f["hang"], f["hoist"], f["wind"], f["raise"], f["safety"], f["reach"]
    la, ap, sk, one, lv, fl, mat, spi = (f["lash"], f["apex"], f["skin"], f["one"], f["level"],
                                         f["floor"], f["materials"], f["spiral"])
    legs = f["harness"]["rows"]
    add("web.constants", "the sky web's two tables: weighed or owned, and declared", sw.constants_table)
    add("web.declared", "how many figures the sky web declares", n(len(sw.CONSTANTS)))
    add("web.strut_lo", "the owner's lightest strut, kg", n(O["strut_kg_lo"]))
    add("web.strut_hi", "the owner's heaviest strut, kg", n(O["strut_kg_hi"]))
    add("web.solver_strut", "the solver's estimate of a strut, kg", n(w8["solver_strut_kg"], 1))
    add("web.solver_kg", "the solver's estimate of the frame, kg", n(w8["solver_kg"]))
    add("web.ratio_lo", "owner's lightest strut over the solver's", n(w8["ratio_lo"], 1))
    add("web.ratio_hi", "owner's heaviest strut over the solver's", n(w8["ratio_hi"], 1))
    add("web.tri_lo", "lightest triangle, kg", n(w8["tri_lo_kg"]))
    add("web.tri_hi", "heaviest triangle, kg", n(w8["tri_hi_kg"]))
    add("web.frame_lo", "frame at the lightest struts, kg", n(w8["frame_lo_kg"]))
    add("web.frame_hi", "frame at the heaviest struts, kg", n(w8["frame_hi_kg"]))
    add("web.frame_lb", "frame at the heaviest struts, lb", n(w8["frame_hi_kg"] * sw.LB_PER_KG))
    add("web.winch_lb", "the owner's 12 V winch, lb", n(O["winch_lb"]))
    add("web.winch_kn", "the owner's 12 V winch, kN", n(ho["winch_kn"], 1))
    add("web.up_lo", "the smaller planned winch, times", n(O["upgrade_lo"]))
    add("web.up_hi", "the larger planned winch, times", n(O["upgrade_hi"]))
    add("web.square_m", "side of the tree square, m", n(C["tree_square_m"]))
    add("web.span_m", "the X's span, corner to corner, m", n(x["span_m"], 1))
    add("web.tie1_m", "height of the web's ties, m", n(C["anchor1_m"]))
    add("web.tie2_m", "height of an experimental second web, m", n(C["anchor2_m"]))
    add("web.sag_pct", "the X's design sag, % of span", n(100 * C["sag_ratio"]))
    add("web.taut_pct", "the flatter alternative, % of span", n(100 * C["sag_ratio_taut"]))
    add("web.sag_m", "the X's sag, m", n(sp["sag_m"], 1))
    add("web.t_kn", "the worse rope's tension at the design sag, kN", n(sp["tension_kn"]))
    add("web.rope", "rope the X needs at the design sag", lambda: sp["rope"])
    add("web.taut_kn", "the worse rope's tension at 5% sag, kN", n(st["tension_kn"]))
    add("web.taut_rope", "rope the X needs at 5% sag", lambda: st["rope"])
    add("web.dbh_cm", "anchor tree trunk, cm", n(100 * C["tree_dbh_m"]))
    add("web.mor", "green pine bending strength, MPa", n(C["green_mor_mpa"]))
    add("web.tree_want", "margin a living tree should keep", n(C["tree_factor"]))
    add("web.tree1", "unguyed tree margin, design sag", n(t1["factor"], 1))
    add("web.tree1_taut", "unguyed tree margin, 5% sag", n(tt["factor"], 2))
    add("web.tree2", "unguyed tree margin, second web", n(t2["factor"], 1))
    add("web.next_m", "the next tree out, m", n(C["next_tree_m"]))
    add("web.guy_kn", "back-guy tension at the design sag, kN", n(t1["guy_kn"]))
    add("web.guy_rope", "rope a back-guy needs", lambda: t1["guy_rope"])
    add("web.guy2_kn", "back-guy tension, second web, kN", n(t2["guy_kn"]))
    add("web.squeeze_kn", "a guyed tree's squeeze, kN", n(t1["squeeze_kn"]))
    add("web.buckle_x", "a guyed tree's margin against buckling", n(t1["buckle_factor"]))
    add("web.post_kn", "a milled 6x6 post's buckling load at the tie height, kN", n(pv["post_kn"]))
    add("web.tree_mn", "the living trunk's buckling load, MN", n(pv["tree_kn"] / 1000, 1))
    add("web.tree_x", "the trunk over the post", n(pv["times"]))
    add("web.pitch_cm", "spacing of the spiral's turns, cm", n(100 * C["spiral_pitch_m"]))
    add("web.turns", "turns of the spiral", n(spi["turns"], 1))
    add("web.spiral_m", "length of the spiral, m", n(spi["length_m"]))
    add("web.seizings", "seizings where the spiral crosses the X", n(spi["ties"]))
    add("web.footprint_m", "the footprint's diameter, m", n(2 * spi["radius_m"], 1))
    add("web.pull_kn", "the heaviest triangle's pull, kN", n(ho["pull_kn"], 2))
    add("web.winch_x", "winch rating over the heaviest triangle", n(ho["winch_margin"]))
    add("web.one_wh", "battery energy for one lift, Wh", n(ho["one_wh"]))
    add("web.all_wh", "battery energy for all forty, Wh", n(ho["all_wh"]))
    add("web.battery_pct", "share of one battery's usable charge, %", n(100 * ho["battery_share"]))
    add("web.hook_m", "the hook's highest point, m", n(ho["hook_m"], 1))
    add("web.lift_min", "minutes to raise one triangle", n(ho["lift_min"], 1))
    add("web.bridle_m", "harness eye above the balance point, m", n(C["bridle_h_m"]))
    add("web.legs_a", "harness legs, the two-short-sided triangle, m",
        lambda: " / ".join(f"{l:.2f}" for l in legs[0]["legs_m"]))
    add("web.legs_b", "harness legs, the equal triangle, m",
        lambda: " / ".join(f"{l:.2f}" for l in legs[1]["legs_m"]))
    add("web.pigtails", "pigtails, three per triangle", n(h["pigtails"]))
    add("web.pig_min_m", "shortest pigtail, m", n(h["pig_min_m"], 1))
    add("web.pig_max_m", "longest pigtail, m", n(h["pig_max_m"], 1))
    add("web.cord_m", "cord in all the pigtails, m", n(h["cord_m"]))
    add("web.pig_n", "load on one pigtail, N", n(w["pig_load_kn"] * 1000))
    add("web.pig_x", "cord strength over a pigtail's load", n(w["pig_factor"]))
    add("web.short", "crown triangles the hook cannot reach", n(rc["short"]))
    add("web.haul_cm", "furthest a crown triangle is hauled by hand, cm", n(100 * rc["haul_max_m"]))
    add("web.rim_m", "the hung dome's rim height, m", n(h["rim_m"], 1))
    add("web.apex_m", "the hung dome's crown height, m", n(h["apex_m"], 1))
    add("web.seams", "seams two triangles share", n(la["seams"]))
    add("web.lash_per", "lashings a seam", n(C["lash_per_seam"]))
    add("web.lash_wraps", "turns in one lashing", n(C["lash_wraps"]))
    add("web.lashings", "lashings in all", n(la["lashings"]))
    add("web.lash_m", "cord for the lashings, m", n(la["cord_m"]))
    add("web.joints", "the dome's joints", n(ap["joints"]))
    add("web.apex_cords", "cords to the free ring, besides the apex", n(ap["cords"] - 1))
    add("web.strutted", "joints too close to the ring for a cord", n(ap["strutted"]))
    add("web.rim_deg", "the rim cords' angle, degrees", n(ap["rim_deg"]))
    add("web.rim_hoop", "the rim ring's squeeze from the cords, kN", n(ap["rim_hoop_kn"], 1))
    add("web.apex_kn", "what the apex line itself carries, kN", n(ap["apex_kn"], 1))
    add("web.head_m", "a rim cord's height halfway out, m", n(ap["head_half_m"], 1))
    add("web.hung_kg", "frame and skin, kg", n(one["mass_kg"]))
    add("web.hung_kn", "frame and skin, kN", n(one["w_kn"], 1))
    add("web.now_pct", "today's winch, % of the whole dome", n(100 * one["now_x"]))
    add("web.lo_x", "the smaller planned winch over the dome", n(one["lo_x"], 2))
    add("web.hi_x", "the larger planned winch over the dome", n(one["hi_x"], 1))
    add("web.block_kn", "the crossing's load with the winch at a tree, kN", n(one["block_kn"]))
    add("web.one_kn", "the X's tension with all the weight at the crossing, kN", n(one["xd"]["tension_kn"]))
    add("web.one_rope", "rope for one central lift", lambda: one["xd"]["rope"])
    add("web.one_guy", "guy tension for one central lift, kN", n(one["tree"]["guy_kn"]))
    add("web.tilt_med", "median tilt with unsorted struts, degrees", n(lv["random_med_deg"], 1))
    add("web.tilt_95", "1-in-20 tilt with unsorted struts, degrees", n(lv["random_95_deg"], 1))
    add("web.tilt_cm", "1-in-20 drop across the rim, cm", n(lv["rim_drop_mm_95"] / 10))
    add("web.tilt_worst", "tilt with every heavy strut on one side, degrees", n(lv["worst_deg"]))
    add("web.skin_m2", "the dome's shell, m2", n(sk["shell_m2"]))
    add("web.skin_layers", "layers of skin", n(sk["layers"]))
    add("web.tubes", "cartridges of silicone", n(sk["tubes"]))
    add("web.naphtha_l", "naphtha, litres", n(sk["naphtha_l"]))
    add("web.mix", "naphtha to silicone, by volume", n(C["mix_parts"]))
    add("web.cotton_m2", "cotton, m2", n(sk["cotton_m2"]))
    add("web.skin_usd", "the silicone skin, $", n(sk["diy_usd"]))
    add("web.sail_usd", "the same in sailcloth, $", n(sk["sail_usd"]))
    add("web.sail_m2", "sailcloth, $/m2", n(C["sailcloth_usd_m2"]))
    add("web.skin_kg", "the skin's mass, kg", n(sk["mass_kg"]))
    add("web.tight_cm", "tree spread before the design web goes taut, cm", n(100 * f["tight_m"]))
    add("web.tight_taut_cm", "tree spread before a 5% web goes taut, cm", n(100 * f["tight_taut_m"], 1))
    add("web.kn_cm", "added tension per cm of stretch, kN", n(w["kn_per_cm"], 1))
    add("web.side_m2", "the dome's side area, m2", n(w["side_m2"], 1))
    add("web.gust_kmh", "a strong gale's gust, km/h", n(C["gust_m_s"] * 3.6))
    add("web.gust_kn", "the gust's push, kN", n(w["gust_kn"], 1))
    add("web.gust_deg", "the swing in that gust, degrees", n(w["gust_deg"]))
    add("web.storm_kmh", "a storm's gust, km/h", n(C["gust_hi_m_s"] * 3.6))
    add("web.storm_kn", "the storm's push, kN", n(w["storm_kn"], 1))
    add("web.storm_deg", "the swing in that storm, degrees", n(w["storm_deg"]))
    add("web.drink_l", "water a pine draws a summer day, L", n(C["transpire_l_day"]))
    add("web.drink4_l", "water the four draw a summer day, L", n(f["nature"]["drink_l_day"]))
    add("web.clash_m", "how far the dome would pass up through the first web, m", n(r["clash_m"], 1))
    add("web.step_cm", "one corner's raise, cm", n(100 * C["raise_step_m"]))
    add("web.pulls", "pulls to raise the dome", n(r["pulls"]))
    add("web.corner_kn", "heaviest corner's pull, kN", n(r["corner_pull_kn"], 1))
    add("web.floor_t", "a floor and its contents, tonnes", n(fl["floor_kg"] / 1000, 1))
    add("web.house_t", "the shell with a floor, tonnes", n(fl["mass_kg"] / 1000, 1))
    add("web.house_kn", "the shell with a floor, rope tension, kN", n(fl["tension_kn"]))
    add("web.house_rope", "rope for the shell with a floor", lambda: fl["rope"])
    add("web.drop_m", "the hoist's height, m", n(sf["drop_m"], 1))
    add("web.impact_kmh", "a dropped triangle's speed, km/h", n(sf["impact_kmh"]))
    add("web.impact_kj", "a dropped triangle's energy, kJ", n(sf["energy_kj"], 1))
    add("web.guys_m", "rope in the back-guys, m", n(mat["guys_m"]))


def _ring_tokens(add) -> None:
    """``ring``: ten TEC1-12706 modules at the rim ports, run day and night on
    the sun, from :mod:`two_v_demo.peltier_ring`."""
    from two_v_demo import peltier_ring as pr
    from two_v_demo import seam_climate as sc

    f = pr.facts()
    lc, hum, ld, cmp, plan, day = f["listing"], f["humid"], f["loads"], f["compared"], f["plan"], f["daylight"]
    p = hum["point"]
    room = pr.weather("humid")

    def n(v, d=0):
        return lambda: f"{v:,.{d}f}"

    add("ring.constants", "the ring's declared inputs", pr.constants_table)
    add("ring.volts_table", "one module and ten, by voltage", pr.voltage_text)
    add("ring.weather_table", "ten modules in three weathers, against the room's loads", pr.weather_text)
    add("ring.plan_table", "the array and bank for 24/7, priced", pr.plan_text)
    add("ring.modules", "modules in the ring", n(pr.C["modules"]))
    add("ring.module_usd", "what one module cost", n(pr.C["module_usd"]))
    add("ring.listed_w", "cooling power on the listing, W", n(lc["q_max_listed"]))
    add("ring.true_w", "the module's real maximum, no temperature difference, W", n(lc["q_max_true"]))
    add("ring.dt_max", "the listed maximum temperature difference, K", n(pr.C["dt_max"]))
    add("ring.ideal_amps", "amps at 12 V with no back-voltage", n(lc["i_at_12v_ideal"], 1))
    add("ring.amps", "amps at 12 V, mounted, humid day", n(p.amps, 1))
    add("ring.listed_amps", "the listing's working current, middle", n(pr.C["i_listed"], 1))
    add("ring.room_t", "the humid day's room, C", n(room[2]))
    add("ring.room_rh", "and its relative humidity, %", n(100 * room[3]))
    add("ring.out_t", "the humid day's outside, C", n(room[4]))
    add("ring.dew_c", "the room's dew point that day, C", n(sc.dew_point(room[2], room[3]), 1))
    add("ring.cold_c", "where the cold face settles at 12 V, C", n(p.t_cold, 1))
    add("ring.hot_c", "where the hot face settles at 12 V, C", n(p.t_hot, 1))
    add("ring.under_k", "how far under the dew point that is, K",
        n(sc.dew_point(room[2], room[3]) - p.t_cold, 1))
    setpoint = sc.plate_setpoint(sc.dew_point(room[2], room[3]))
    add("ring.setpoint_c", "where the controller asks the plate to be, C", n(setpoint, 1))
    add("ring.short_k", "how far the 12 V plate falls short of it, K", n(p.t_cold - setpoint, 1))
    add("ring.q_each", "heat one module moves at 12 V, mounted, W", n(p.q_cold, 0))
    add("ring.draw_each", "what one station draws, module and fans, W", n(p.p_station, 0))
    add("ring.cop", "heat moved per watt, one module", n(p.cop, 2))
    add("ring.latent_pct", "share of that heat that is water, %", n(100 * p.latent_share))
    add("ring.water_each", "litres a day one module condenses", n(p.water_l_day, 2))
    add("ring.cooling_w", "heat ten take out of the room, W", n(hum["cooling_w"]))
    add("ring.outside_w", "heat ten throw outside, W", n(hum["outside_w"]))
    add("ring.draw_w", "what ten draw, all day and night, W", n(hum["draw_w"]))
    add("ring.kwh", "kWh a day, 24/7", n(hum["draw_kwh"], 1))
    add("ring.water", "litres a day ten condense, humid day", n(hum["water_l_day"], 1))
    add("ring.l_per_kwh", "litres per kWh", n(hum["litres_per_kwh"], 2))
    add("ring.muggy_water", "litres a day on a muggy night", n(f["muggy"]["water_l_day"], 1))
    add("ring.spring_water", "litres a day on a wet spring day", n(f["spring"]["water_l_day"], 1))
    add("ring.load_water", "litres a day the room takes on, humid day", n(ld["water_l_day"], 1))
    add("ring.people_water", "of it from two people breathing", n(ld["people_water_l_day"], 1))
    add("ring.vent_water", "of it on the fresh air", n(ld["vent_water_l_day"], 1))
    add("ring.water_pct", "share of the day's water ten remove, %",
        n(100 * hum["water_l_day"] / ld["water_l_day"]))
    add("ring.load_heat", "heat the room takes on, people and fresh air, W", n(ld["heat_w"]))
    for v in (3, 6, 9):
        r = f["volts"][v]
        add(f"ring.v{v}_cold", f"cold face at {v} V, C", n(r["point"].t_cold, 1))
        add(f"ring.v{v}_water", f"litres a day, ten at {v} V", n(r["water_l_day"], 1))
        add(f"ring.v{v}_kwh", f"kWh a day, ten at {v} V", n(r["draw_kwh"], 1))
        add(f"ring.v{v}_cop", f"heat moved per watt at {v} V", n(r["point"].cop, 2))
    add("ring.best_v", "the voltage that makes the most water per kWh", n(f["best"]["point"].volts))
    add("ring.best_lpk", "and its litres per kWh", n(f["best"]["litres_per_kwh"], 2))
    add("ring.night_kwh", "kWh off the bank each night", n(plan.night_kwh, 1))
    add("ring.array_w", "array to run ten 24/7, W", n(plan.array_w))
    add("ring.array_usd", "and its price, USD", n(plan.array_usd))
    add("ring.bank_kwh", "bank for a night and a dark day, kWh", n(plan.bank_nameplate_kwh, 1))
    add("ring.bank_usd", "and its price, USD", n(plan.bank_usd))
    add("ring.total_usd", "modules, array and bank, USD", n(plan.total_usd))
    add("ring.times_modules", "power system against the modules' price",
        n((plan.array_usd + plan.bank_usd) / plan.modules_usd))
    add("ring.modules_usd", "ten modules, USD", n(plan.modules_usd))
    add("ring.sun_hours", "peak sun hours a day (borrowed)", n(pr._borrowed("sun_hours_per_day"), 1))
    add("ring.window_h", "hours the array outruns the load", n(pr.C["solar_window_h"]))
    add("ring.dehum_kwh", "kWh a compressor dehumidifier takes for the same water", n(cmp["dehumidifier_kwh"], 1))
    add("ring.times_dehum", "how many times more the ring takes", n(cmp["ratio_vs_dehumidifier"]))
    add("ring.ac_cool_w", "the smallest window AC's cooling, W", n(cmp["ac_cool_w"]))
    add("ring.ac_draw_w", "and what it draws, W", n(cmp["ac_draw_w"]))
    add("ring.ac_cop", "its heat moved per watt", n(cmp["ac_cop"], 1))
    add("ring.ring_cop", "the ring's heat moved per watt, fans included", n(cmp["ring_cop"], 2))
    add("ring.day_hours", "daylight-surplus hours the book runs them", n(day["hours"]))
    add("ring.day_kwh", "kWh a day on daylight surplus", n(day["kwh"], 1))
    add("ring.day_litres", "litres a day on daylight surplus", n(day["litres"], 2))
    add("ring.old_modules", "modules the book assumed before", n(pr.C["old_modules"]))
    add("ring.old_watts", "watts each it assumed", n(pr.C["old_watts_each"]))
    add("ring.old_lpk", "litres per kWh it assumed", n(pr.C["old_litres_per_kwh"], 2))
    add("ring.old_kpl", "kWh a litre it implied", n(day["old_kwh_per_litre"], 2))
    add("ring.new_kpl", "kWh a litre now", n(day["kwh_per_litre"], 2))


if __name__ == "__main__":
    raise SystemExit(main())
