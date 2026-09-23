"""Every worksheet the campaign film puts on screen, derived not typed.

The film is an argument about money, so this is the module that has to be
above suspicion. Each function here returns the lines of one math screen, and
every one of those lines is a value read out of :mod:`seed_model`,
:mod:`hull_laminate` or :mod:`park_model` at render time. Nothing is a string
with a number in it.

That matters for one specific reason: the prices in this model are the owner's
declared assumptions, and they will change. When they do, the film has to
change with them or it becomes a recording of a price that no longer exists.
Reading the model at render time is what makes a re-render honest.

The same discipline the dome-park film uses, in
:mod:`two_v_demo.park_facts`, for the same reason.
"""

from __future__ import annotations

import hull_laminate
import park_model
import seed_model
import soft_shell


# ----------------------------------------------------------------------
# Formatting
# ----------------------------------------------------------------------

def usd(value: float, width: int = 0) -> str:
    text = f"${value:,.0f}"
    return f"{text:>{width}}" if width else text


DOT = "  \u00b7  "
"""The separator every table on these screens uses.

Not column padding. The worksheet overlay normalises runs of whitespace, so a
line laid out with ``{label:<34}`` arrives on screen as single-spaced prose and
the columns are gone. A visible separator survives that, and it reads the same
in the printed report as it does in the film -- which is the point, because
the report is how these screens get checked before a ninety-minute render."""


def _row(label: str, *values: str) -> str:
    return DOT.join((label,) + values)


def _rule(width: int = 46) -> str:
    return "-" * width


def quote():
    """The standard article, priced. One call, so every screen agrees."""
    return seed_model.quote()


# ----------------------------------------------------------------------
# The screens
# ----------------------------------------------------------------------

def steps_declared() -> tuple[str, ...]:
    """Two kinds of number, kept apart, before a dollar is claimed."""
    constants = seed_model.external_constants()
    borrowed = [name for name, _v, _u, note in constants
                if note.startswith(("borrowed", "hull laminate"))]
    geometry = seed_model.seed_geometry()
    return (
        "this film has two kinds of number in it.",
        "",
        "MEASURED -- off the dome's own solved geometry:",
        f"   {geometry.member_count} members, {geometry.member_stock_ft:,.0f} "
        "ft of stock",
        f"   {sum(f.count for f in geometry.faces)} panels, "
        f"{geometry.panel_sqft:,.1f} sq ft of surface",
        f"   {geometry.floor_decagon_sqft:,.0f} sq ft of floor, "
        f"{geometry.diameter_ft:.2f} ft across",
        "   none of these can be argued with.",
        "",
        "DECLARED -- prices and rates, typed in by a person:",
        f"   {len(constants)} inputs, each with a unit and a reason",
        f"   {len(borrowed)} of them borrowed from suppliers' own lists",
        "   these are assumptions. they are not market research.",
        "",
        "change one and every figure after it moves,",
        "because this film reads the table rather than repeating it.",
    )


def steps_frame() -> tuple[str, ...]:
    """The frame, priced against a board you can go and buy."""
    geometry = seed_model.seed_geometry()
    priced = quote()
    bought = seed_model.quote(frame_stock="wedge_log")
    dimensional = seed_model.quote(frame_stock="dimensional")
    board = seed_model.declared("lumber_board_usd")
    per_board = seed_model.declared("lumber_struts_per_board")
    harvest = seed_model.harvest()
    return (
        "start with a board anybody can go and price.",
        "",
        "   " + _row(f"one 2x6x12 at Lowes", usd(board)),
        "   " + _row(f"rips and cuts into {per_board:.0f} struts of 2x3x6",
                     usd(seed_model.usd_per_strut()) + " each"),
        "   " + _row(f"{geometry.member_count} of those",
                     usd(geometry.dimensional_frame_usd)),
        "",
        "that is the whole frame of this dome in bought sticks.",
        "",
        "a wedge off a 12 inch trunk is bigger than a 2x3:",
        "   " + _row("one wedge",
                     f"{geometry.wedge_volume_cuin:,.0f} cu in",
                     f"{geometry.wedge_to_strut:.2f} x a 2x3x6"),
        "   " + _row(f"so {geometry.member_count} of them, bought as timber",
                     usd(bought.group("frame").cost)),
        "   " + _row("felled on site instead",
                     usd(priced.group("frame").cost)),
        "",
        "and here is what splitting does to a tree:",
        "   " + _row("split into wedges",
                     f"{harvest.wedge_recovery * 100:.1f}% of the trunk",
                     f"{harvest.wedge_bf:,.0f} bf"),
        "   " + _row("milled into 2x4s",
                     f"{harvest.dimensional_recovery * 100:.1f}% of it",
                     f"{harvest.dimensional_bf:,.0f} bf"),
        "   " + _row("so a wedge takes", f"{harvest.advantage:.2f} x as much",
                     f"+{harvest.wasted_bf:,.0f} bf a tree"),
        "",
        "squaring a round log throws away the round part.",
        "we do not square it.",
        "",
        "the pinwheel costs more stock, though:",
        "   " + _row("shared struts", f"{geometry.shared_strut_ft:,.0f} ft"),
        "   " + _row("pinwheelled", f"{geometry.member_stock_ft:,.0f} ft",
                     f"{geometry.pinwheel_stock_penalty:.2f} x"),
    )


def steps_bay() -> tuple[str, ...]:
    """The wall, from the inside out."""
    geometry = seed_model.seed_geometry()
    priced = quote()
    plan = seed_model.insulation_plan(geometry)
    lip = seed_model.declared("panel_lip_in")
    return (
        "a wedge is not a rectangle, and that is the point.",
        "",
        "its inward face stands proud of the panel seat, so every",
        f"bay has a {lip:.2f} inch lip already cut into it.",
        "",
        "from the inside out:",
        "   " + _row("1  inner panel", "drops onto the lip"),
        "   " + _row("2  the cavity",
                     f"{geometry.member_depth_in:.0f} in deep",
                     f"{plan.cavity_cuft:,.0f} cu ft in all"),
        "   " + _row("3  outer panel", "compression fit from outside"),
        "   " + _row("4  the shell", "lands on the frame, not the panels"),
        "",
        "nothing in that stack is screwed to anything.",
        "the shape of the member holds it.",
        "",
        # A hard-shelled dome prices the bays separately; a shower-capped one
        # carries its outer panels inside the shell line. Ask for whichever
        # this quote has rather than assuming the shell kind.
        "   " + _row(f"{sum(f.count for f in geometry.faces)} bays, "
                     "two panels each",
                     usd(priced.find("envelope", "cap").cost)),
        "",
        "and the cavity ships empty on purpose. an empty cavity",
        "is a duct, and every one of them is connected.",
    )


def steps_duct() -> tuple[str, ...]:
    """The seam channel: the dihedral angle, used."""
    geometry = seed_model.seed_geometry()
    duct = seed_model.seam_duct(geometry)
    # Priced on its own: the duct is an upgrade, so it is not in the
    # standard article's groups and cannot be looked up there.
    fitted = seed_model.airflow_group(geometry).cost
    return (
        "two sawn faces meeting at an angle do not close flush.",
        "everyone machines that out. we cap it instead.",
        "",
        "   " + _row("channels", f"{duct.seams} seams",
                     f"{duct.length_ft:,.0f} ft"),
        "   " + _row("cross-section", f"{duct.channel_in2:.1f} sq in"),
        "   " + _row("junctions", f"{duct.vertices} vertices"),
        "",
        "blow through it and the frame never holds damp air.",
        "draw through it and what lands on the shell goes",
        "down the channels instead of into the joints:",
        "",
        "   " + _row(f"off {duct.catch_sqft:,.0f} sq ft of shell",
                     f"{seed_model.declared('rain_in_per_year'):.0f} in of "
                     "rain a year"),
        "   " + _row("at "
                     f"{seed_model.declared('catch_efficiency') * 100:.0f}% "
                     "to the tank",
                     f"{duct.gallons_per_year:,.0f} gal a year"),
        "",
        "   " + _row("what that costs to fit", usd(fitted)),
        "",
        "and it runs both ways on purpose:",
        "   " + _row("fan inside, blowing out", "dries the frame"),
        "   " + _row("fan outside, sucking in", "pulls water down it"),
        "",
        "it also means you always know where the services are.",
        "they are in the corners of the seams. nowhere else.",
        "everybody on site knows the one place not to drill.",
    )


def steps_stemcell() -> tuple[str, ...]:
    """Why it is called a stem cell."""
    geometry = seed_model.seed_geometry()
    bays = sum(face.count for face in geometry.faces)
    rows = []
    for key in ("gym", "studio", "guest", "workshop", "garage"):
        spec = seed_model.fitout(key)
        # bays_changed, not a count of panels: one open-bay door is three
        # base bays taken out, which is what it is priced and drawn as.
        rows.append((spec.label, seed_model.bays_changed(key),
                     seed_model.panel_mix_cost(spec.panels)))
    steps = [
        "a stem cell has not decided what it is yet.",
        "",
        f"the frame is {bays} identical triangular openings. it does",
        "not know or care what is in one. drop a panel in and it",
        "compression-fits; lift it out and the opening is back.",
        "",
        "so the building's function is a set of panels:",
        "",
        "   " + _row("fit-out", "bays changed", "panels cost"),
        f"   {_rule()}",
    ]
    for label, count, cost in rows:
        steps.append("   " + _row(label, f"{count} of {bays}", usd(cost)))
    steps.extend([
        "",
        "same frame. same pad. same core. same hardware.",
        "a gym becomes a guest house in an afternoon,",
        "and nothing structural is touched to do it.",
    ])
    return tuple(steps)


def steps_paint() -> tuple[str, ...]:
    """Two independent reductions that multiply."""
    plan = seed_model.cooling_paint()
    load = seed_model.cooling_load()
    return (
        "two things make this cheap to cool, and they compound.",
        "",
        "ONE: the shape. a dome has less skin than a box does",
        "over the same floor.",
        "   " + _row("dome envelope", f"{plan.envelope_sqft:,.0f} sq ft"),
        "   " + _row("box, same floor", f"{plan.box_envelope_sqft:,.0f} sq ft"),
        "   " + _row("so", f"{plan.shape_reduction * 100:.1f}% less to lose "
                     "heat through"),
        "",
        "TWO: the paint. barium sulphate reflects almost all",
        "the sun AND radiates through the atmospheric window,",
        "so the surface can sit below air temperature.",
        "   " + _row("surface runs",
                     f"{plan.surface_swing_f:.0f} F cooler than dark"),
        "   " + _row("takes off the cooling load",
                     f"{plan.load_reduction * 100:.1f}%"),
        "   " + _row("the coat costs", usd(plan.paint_usd)),
        "",
        "they multiply, not add:",
        "   " + _row("against a painted box",
                     f"{plan.compounded * 100:.0f}% less"),
        "",
        f"which is why the whole design load is "
        f"{load.total_btu:,.0f} BTU an hour --",
        "a window unit, in a house.",
    )


def steps_solar() -> tuple[str, ...]:
    """An obtainable off-grid set, against the dome's own draw."""
    plan = seed_model.solar_plan()
    steps = [
        "what it takes to run this thing on nothing.",
        "",
        "the draw is not a guess. it is this dome's own",
        "heating and cooling year, plus lights and a fan:",
        "   " + _row("demand", f"{plan.demand_kwh_per_day:.2f} kWh a day"),
        "",
        "   " + _row(f"{plan.panel_watts:,.0f} W of panel",
                     f"{plan.sun_hours:.1f} sun hours",
                     f"{plan.daily_kwh:.2f} kWh a day"),
        "   " + _row("covers", f"{plan.covers * 100:.0f}% of the draw"),
        "   " + _row(f"{plan.battery_kwh:,.0f} kWh bank",
                     f"{plan.autonomy_days:.1f} days with no sun"),
        "   " + _row("refills from empty in",
                     f"{plan.days_to_refill:.1f} days"),
        "",
    ]
    for label, amount in plan.rows():
        steps.append("   " + _row(label, usd(amount)))
    steps.append("   " + _row("the set", usd(plan.total_usd)))
    steps.extend([
        "",
        "one honest note. the brief said three thousand for the",
        f"battery. at kilowatt hours that is "
        f"{usd(3000 * seed_model.declared('battery_usd_per_kwh'))} of cells",
        "and two years of autonomy -- almost certainly watt hours,",
        "or the inverter's rating, was meant.",
    ])
    return tuple(steps)


def steps_layering() -> tuple[str, ...]:
    """What layering buys, a layer at a time."""
    ladder = seed_model.quilt_ladder(7)
    steps = [
        "put on seven t-shirts and tell me how cold you are.",
        "",
        "the shell comes off. a quilted layer goes in. the shell",
        "goes back on. that is the whole operation, and it can",
        "happen once a season for as long as you own the place.",
        "",
        "   " + _row("layers", "R-value", "spent so far"),
        f"   {_rule()}",
    ]
    for count, r_value, cost in ladder.rows():
        steps.append("   " + _row(f"{count}", f"R-{r_value:.1f}", usd(cost)))
    steps.extend([
        "",
        f"   {usd(ladder.usd_per_layer)} a layer, and the fabric is a waste "
        "stream.",
        "",
        "a finished house does not get warmer every winter.",
        "this one does.",
    ])
    return tuple(steps)


def steps_system() -> tuple[str, ...]:
    """Two people, two bills, and why that makes the dome cheap."""
    priced = quote()
    home = seed_model.quote("home")
    return (
        "this only works as a system. here are the two halves.",
        "",
        "THE LANDOWNER builds pads and rents them.",
        "   " + _row("one pad, built once", usd(priced.pad_cost)),
        "   no building to maintain. no tenant can wreck a",
        "   house the landowner does not own.",
        "   " + _row("what is theirs", "the ground and the hookups"),
        "",
        "THE OWNER buys a dome and takes it with them.",
        "   " + _row("the standard dome", usd(priced.price)),
        "   " + _row("the core inside it", usd(priced.core_cost)),
        "   " + _row("which moves to the next dome",
                     f"{priced.core_share * 100:.0f}% of materials"),
        "",
        "the hardware is made to fit this dome and the next",
        f"{seed_model.declared('hardware_size_steps') - 1:.0f} sizes up, so "
        "it goes up with you.",
        "",
        "that is why a dome can cost what it costs. nobody is",
        "buying land, a foundation and a house at the same time.",
    )


def steps_shell() -> tuple[str, ...]:
    """Four hull laminate systems, and the one this ships with."""
    geometry = seed_model.seed_geometry()
    rows = []
    for key in seed_model.laminate_keys():
        plan = seed_model.shell_plan(geometry, key)
        group = seed_model.shell_group(geometry, key)
        system = plan.laminate.system
        rows.append((system.label, group.cost,
                     group.cost / plan.laminated_sqft, plan.weight_lb))
    chosen = seed_model.shell_plan(geometry, "boatyard")
    lam = chosen.laminate
    steps = [
        "the shell is a boat hull. so price it like one.",
        "",
        f"   {chosen.laminated_sqft:,.0f} sq ft laminated, over a "
        f"{chosen.core_sqft:,.0f} sq ft core",
        f"   {lam.glass_lb:,.0f} lb of glass, {lam.resin_lb:,.0f} lb of resin",
        f"   which is {lam.ratio:.2f} to 1 by weight -- hand layup",
        "",
        "   " + _row("system", "cost", "per sq ft", "weight"),
        f"   {_rule()}",
    ]
    for label, cost, per_sqft, weight in rows:
        steps.append("   " + _row(label, usd(cost),
                                  f"${per_sqft:.2f}", f"{weight:,.0f} lb"))
    # What the slicing costs, said out loud: a monocoque shell would not
    # carry these two lines, and it also would not fit on a trailer.
    slices = int(round(seed_model.declared("shell_halves")))
    seam = [line for line in seed_model.shell_group(geometry, "boatyard").lines
            if "S-lip" in line.label or "interlock" in line.label]
    steps.extend([
        "",
        f"   {slices} slices, {sum(l.quantity for l in seam) / 2.0:,.0f} ft "
        f"of S-lip seam {DOT} {usd(sum(l.cost for l in seam))}",
        f"   {chosen.weight_lb / slices:,.0f} lb a slice, against "
        f"{chosen.weight_lb:,.0f} lb in one piece",
        "",
        "glass and resin are sold by weight, not by yardage,",
        "so the quantity follows the fabric, not a rule of thumb.",
    ])
    return tuple(steps)


def steps_sheet() -> tuple[str, ...]:
    """The finding that decides how the core gets cut."""
    geometry = seed_model.seed_geometry()
    plan = seed_model.shell_plan(geometry, "boatyard")
    width = seed_model.declared("shell_sheet_width_in")
    length = seed_model.declared("shell_sheet_length_in")
    steps = [
        f"can a panel be cut whole out of a "
        f"{width:.0f} x {length:.0f} inch sheet?",
        "",
    ]
    for name, fits, min_width in plan.panel_fits_sheet:
        steps.append("   " + _row(f"{name} panel",
                                  f"narrowest across {min_width:.2f} in",
                                  "yes" if fits else "NO"))
    steps.extend([
        "",
        f"   a four-foot sheet is {width:.0f} inches.",
        "",
        "a triangle cannot get narrower than its shortest altitude,",
        "however you turn it. so the core is sheeted across the frame",
        "and the joints are taped -- not cut panel by panel.",
        "",
        "we would rather find that here than in the shop.",
    ])
    return tuple(steps)


def steps_core() -> tuple[str, ...]:
    """The utility core, and what it is worth when it moves."""
    priced = quote()
    life = seed_model.declared("core_service_life_years")
    move = seed_model.declared("core_move_usd")
    return (
        "the utility core is the part that is not part of the dome.",
        "",
        "   " + _row("column, manifold, drain, sub-panel",
                     usd(priced.group("column").cost)),
        "   " + _row("light, fan and cooling",
                     usd(priced.group("services").cost)),
        "   " + _row("THE CORE", usd(priced.core_cost)),
        "",
        f"that is {priced.core_share * 100:.0f}% of everything material in "
        "the dome.",
        "",
        "it unbolts. it crates. it goes into the next one.",
        "   " + _row("moving it", usd(move)),
        "   " + _row("buying a second one", usd(priced.core_cost)),
        "   " + _row("so a move saves", usd(priced.core_cost - move)),
        "",
        f"over a {life:.0f} year core life, that is the same money",
        "buying a bigger shell instead of the same plumbing twice.",
    )


def steps_deck() -> tuple[str, ...]:
    """The platform, counted in boards rather than quoted by the square foot."""
    import pad_deck

    across = pad_deck.pad_diameter_ft()
    blocks = pad_deck.deck("blocks")
    slab = pad_deck.deck("slab")
    ring = pad_deck.deck("ring")
    steps = [
        "a platform is a list of boards. so count them.",
        "",
        f"   {across:.1f} ft decagon {DOT} {blocks.area_sqft:,.0f} sq ft",
        f"   every stick off one 2x6x12 at {usd(pad_deck.board_usd())}",
        "",
    ]
    for step in pad_deck.build_sequence("blocks"):
        steps.append(f"   {step.number}. {step.label[:34]:<34} {DOT} "
                     f"{usd(step.cumulative_usd)}")
    steps.extend([
        "",
        f"   {blocks.boards:.0f} boards {DOT} {usd(blocks.cost)} {DOT} "
        f"${blocks.usd_per_sqft:.2f}/sqft",
        "",
        f"a slab is cheaper: {usd(slab.cost)}. a concrete ring is not:",
        f"{usd(ring.cost)}. wood is not the cheap option --",
        "it is the one that comes apart again.",
    ])
    return tuple(steps)


def steps_pad() -> tuple[str, ...]:
    """Whose bill is whose."""
    priced = quote()
    return tuple([
        "two people are paying here, and they are not the same person.",
        "",
        "THE LANDOWNER builds the pad, once, and keeps it:",
    ] + [
        "   " + _row(line.label[:36], usd(line.cost))
        for line in priced.group("pad").lines
    ] + [
        "   " + _row("THE PAD", usd(priced.pad_cost)),
        "",
        "THE DOME BUYER pays none of that.",
        "",
        "the deck stays when the dome is lifted off.",
        "the next dome lands on the same port.",
        "which is why the dome's price below has no floor in it.",
    ])


def steps_price() -> tuple[str, ...]:
    """The whole quote, to the number the campaign is built on."""
    priced = quote()
    steps = ["what one standard dome costs to build:", ""]
    for group in priced.dome_groups:
        if group.key == "labour":
            continue
        steps.append("   " + _row(group.label[:34], usd(group.cost)))
    margin = seed_model.declared("gross_margin_fraction") * 100.0
    steps.extend([
        "   " + _row("materials", usd(priced.material_cost)),
        "   " + _row(f"labour, {priced.labour_hours:,.0f} hours",
                     usd(priced.labour_cost)),
        "   " + _row("overhead and warranty",
                     usd(priced.overhead + priced.warranty)),
        "   " + _row("COST TO BUILD", usd(priced.cost_to_build)),
        "",
        "   " + _row(f"LIST PRICE at {margin:.0f}% margin", usd(priced.price)),
        "   " + _row("per square foot of floor",
                     f"${priced.price_per_sqft:,.2f}"),
        "   " + _row("delivered", usd(priced.delivered_price)),
    ])
    return tuple(steps)


def steps_ladder() -> tuple[str, ...]:
    """How far down it goes, and which of those are really savings."""
    priced = quote()
    build, floor = seed_model.floor_price()
    steps = [
        f"the standard dome is {usd(priced.price)}.",
        "",
        "each of these on its own, against that:",
        "",
    ]
    for lever, cost, saving in seed_model.lever_prices():
        if saving <= 0.0:
            continue
        mark = "*" if lever.key in seed_model.MARGIN_LEVERS else " "
        steps.append(f"  {mark}" + _row(lever.label[:40], "-" + usd(saving)))
    steps.extend([
        "",
        "   " + _row("all of the real ones at once", usd(floor)),
        "   " + _row("which costs, to build", usd(build)),
        "   " + _row("a square foot",
                     f"${floor / priced.geometry.floor_decagon_sqft:,.2f}"),
        "",
        "* is not a saving. it is us earning less per dome,",
        "  and it is in this table so the two never get confused.",
    ])
    return tuple(steps)


def steps_against() -> tuple[str, ...]:
    """The three things this film says against itself."""
    geometry = seed_model.seed_geometry()
    priced = quote()
    ladder = seed_model.quilt_ladder(7, geometry)
    year = seed_model.running_year(geometry)
    cut = seed_model.harvest()
    net = seed_model.trees_against_mitred()
    return (
        "three things this pitch says against itself.",
        "",
        "1. THE STANDARD DOME SHIPS WITH AN EMPTY CAVITY.",
        f"   {usd(ladder.usd_per_layer)} a layer buys R-"
        f"{ladder.r_per_layer:.1f}, and you add them when",
        "   you want to. that is a real choice and it is also a",
        "   real thing you still have to do. day one, this is a",
        "   weathertight shell, not a winter house.",
        "",
        "2. THE FRAME WASTES WOOD.",
        f"   {geometry.pinwheel_stock_penalty:.2f} times the stock of a "
        "shared-strut dome,",
        f"   against the {cut.advantage:.2f} times more of the tree that",
        "   splitting keeps. put both together and this frame takes",
        f"   {net * 100:.0f}% of the trees a mitred dome would. it wins,",
        f"   by {100 - net * 100:.0f}%, and that is not a headline.",
        "",
        "3. THE SEAM DUCT IS NOT PROVEN.",
        "   the channel is real, the arithmetic is real, and the",
        "   airflow is an experiment we are running, not a result",
        "   we are reporting. that is what the campaign is for.",
        "",
        "and the prices are ours: "
        f"{len(seed_model.external_constants())} declared inputs, each",
        f"   with a reason. a year of heating and cooling at those",
        f"   rates is {usd(year.annual_cost)}.",
    )


def steps_seeds() -> tuple[str, ...]:
    """The catalogue: one cut list, every building."""
    geometry = seed_model.seed_geometry()
    secondary = ("gym", "studio", "nursery", "guest", "workshop", "garage")
    rows = []
    for key in secondary:
        priced = seed_model.quote(key)
        rows.append((priced.fitout, priced.price))
    rows.sort(key=lambda row: row[1])
    steps = [
        "one frame. one cut list. one pad.",
        "",
        f"   {geometry.member_count} members and "
        f"{sum(f.count for f in geometry.faces)} panels, every time.",
        "",
        "the buildings a homestead actually wants second:",
        "",
        "   " + _row("fit-out", "bays changed", "price"),
        f"   {_rule()}",
    ]
    for spec, price in rows:
        steps.append("   " + _row(spec.label,
                                  f"{sum(spec.panels.values())}", usd(price)))
    steps.extend([
        "",
        "the frame line of that table does not change.",
        "that is the manufacturing argument, and it is the",
        "reason any of these can be built at this price at all.",
    ])
    return tuple(steps)


#: How many quilted layers the hats chapter compares at, and how many the
#: scene behind it stacks. One number, because a worksheet that says three
#: over a picture of four is the sort of thing nobody notices for months.
#: The standard article itself ships none -- the layers are the upgrade.
QUILT_COMPARE_LAYERS = 3


def steps_hats() -> tuple[str, ...]:
    """A dome is a structure that wears hats. A cap is a bag, so it grows."""
    row = soft_shell.compare(QUILT_COMPARE_LAYERS)[QUILT_COMPARE_LAYERS]
    soft = quote()
    hard = seed_model.quote("stem_cell", shell="hard")
    return (
        "a dome is a structure that wears hats.",
        "",
        "the cap is a bag. add a quilted layer and the stack",
        "gets thicker, so the next bag is a size up. a rigid",
        "hull is made once, at one size, and cannot grow.",
        "",
        "   " + _row("the hull's cavity holds",
                     f"{soft_shell.cavity_limit()} layers",
                     "then it is full"),
        "   " + _row("seven layers makes the cap",
                     f"{soft_shell.growth_fraction(7) * 100:.1f}% bigger"),
        "",
        "at three quilted layers, skin against skin:",
        "   " + _row("shower cap", usd(row.soft_usd)),
        "   " + _row("hull plus its bays", usd(row.hard_usd)),
        "   " + _row("saving", usd(row.saving)),
        "",
        "and the whole dome, the same way:",
        "   " + _row("standard, shower cap", usd(soft.price)),
        "   " + _row("the same, laminated hull", usd(hard.price)),
        "   " + _row("the hull is the upgrade",
                     usd(hard.price - soft.price)),
    )


def steps_quilt() -> tuple[str, ...]:
    """The blanket quilt: a waste stream, quilted by the owner, $50 a layer."""
    layer = soft_shell.declared("blanket_quilt_usd_per_layer")
    yard = (soft_shell.soft_shell(1, quilt="yard").cost
            - soft_shell.soft_shell(0).cost)
    return (
        "the blanket quilt is the insulation.",
        "",
        "recycled clothing and thrift-store blankets, quilted by the",
        "owner into one monolithic layer. it goes over the frame,",
        "under the cap, and off when the cap is replaced.",
        "",
        "   " + _row("one layer, declared", usd(layer)),
        "   " + _row("the same layer yard-priced", usd(yard)),
        "   " + _row("the fabric is a waste stream"),
        "",
        "honest caveat, on camera:",
        "   two impermeable layers with fabric between them is a",
        "   moisture trap. the seam duct is the answer, and the",
        "   seam duct is not proven.",
    )


def steps_mast() -> tuple[str, ...]:
    """A mast through the column, and the floor that clamps to it."""
    geometry = seed_model.seed_geometry()
    mast = seed_model.mast_group(geometry)
    floor = seed_model.dome_floor_group(geometry)
    return (
        "a mast runs through the utility column, floor to apex.",
        "",
        "steel where the strength is, timber cladding everywhere",
        "else. it stands inside the column, so the structure and",
        "the services share one penetration.",
        "",
        "   " + _row("the mast", usd(mast.cost)),
        "   " + _row("the dome's own floor", usd(floor.cost)),
        "",
        "the floor is the upgrade, bought after the dome. a steel",
        "hub clamps the mast; radial steel spokes run to the base",
        "ring; timber decking covers them.",
        "",
        "   " + _row("frame weight, green pine",
                     f"{seed_model.frame_weight_lb(geometry):,.0f} lb"),
        "",
        "the apex lifting ring is the hoist point for the whole",
        "structure. the lifted whole, and the hoist's rating, are",
        "the engineer's number -- not this model's.",
    )


def steps_floating() -> tuple[str, ...]:
    """The floating dome: hung between trees. A possibility, not a rating."""
    geometry = seed_model.seed_geometry()
    mast = seed_model.mast_group(geometry)
    floor = seed_model.dome_floor_group(geometry)
    rig = seed_model.suspension_group(geometry)
    return (
        "hang the dome between two trees.",
        "",
        "three cables run from the apex hanger to tree saddles --",
        "saddles, not holes. nothing is drilled into the tree. the",
        "brake winch does the hoisting, and the dome's own floor",
        "hangs from the mast while it is up there.",
        "",
        "   " + _row("the rig", usd(rig.cost)),
        "   " + _row("mast, floor and rig",
                     usd(mast.cost + floor.cost + rig.cost)),
        "",
        "say it plainly: this is a design possibility, not an",
        "engineered structure. the loads on the trees, the cables",
        "and the mast need an engineer before anyone is under it.",
    )


ALL_SCREENS = (
    ("declared", steps_declared),
    ("frame", steps_frame),
    ("stemcell", steps_stemcell),
    ("paint", steps_paint),
    ("solar", steps_solar),
    ("bay", steps_bay),
    ("duct", steps_duct),
    ("layering", steps_layering),
    ("system", steps_system),
    ("shell", steps_shell),
    ("sheet", steps_sheet),
    ("core", steps_core),
    ("deck", steps_deck),
    ("pad", steps_pad),
    ("price", steps_price),
    ("ladder", steps_ladder),
    ("against", steps_against),
    ("seeds", steps_seeds),
    ("hats", steps_hats),
    ("quilt", steps_quilt),
    ("mast", steps_mast),
    ("floating", steps_floating),
)


# ----------------------------------------------------------------------
# Report and proof
# ----------------------------------------------------------------------

def seed_film_report() -> str:
    """Every screen, printed, so the film can be read before it is rendered."""
    out = []
    for name, builder in ALL_SCREENS:
        out.append(f"--- {name.upper()} " + "-" * (54 - len(name)))
        out.extend(builder())
        out.append("")
    return "\n".join(out)


MAX_LINE = 66
"""Wider than this and a worksheet line runs off its panel."""

MAX_LINES = 26
"""More than this and a worksheet will not fit the frame."""


def validate_seed_facts() -> None:
    """Every screen has to build, fit, and quote the model it claims to."""
    seed_model.validate_seed_model()
    hull_laminate.validate_hull_laminate()

    priced = quote()
    for name, builder in ALL_SCREENS:
        steps = builder()
        assert steps, name
        assert len(steps) <= MAX_LINES, (name, len(steps))
        for line in steps:
            assert len(line) <= MAX_LINE, (name, len(line), line)
            # The overlay collapses runs of whitespace, so a line that only
            # separates its columns with padding arrives as prose. Anything
            # with two or more values on it has to carry a visible separator.
            stripped = line.strip()
            if "  " in stripped and DOT.strip() not in line:
                raise AssertionError(
                    f"{name}: {line!r} lines up with spaces, which the "
                    "worksheet overlay will collapse")

    # The headline number has to be the model's, on every screen that says
    # it. A film with two prices in it is a film nobody should believe.
    price = usd(priced.price)
    assert any(price in line for line in steps_price()), price
    assert any(price in line for line in steps_ladder()), price

    # The pad screen must quote the pad group and nothing from the dome.
    pad_text = "\n".join(steps_pad())
    assert usd(priced.pad_cost) in pad_text
    assert usd(priced.price) not in pad_text

    # The shell screen has to name every laminate system, or a buyer cannot
    # see which one they are being sold.
    shell_text = "\n".join(steps_shell())
    for system in hull_laminate.LAMINATES:
        assert system.label in shell_text, system.key

    # The film must keep saying the things that argue against it.
    against = "\n".join(steps_against())
    assert "EMPTY CAVITY" in against
    assert "WASTES WOOD" in against
    assert "NOT PROVEN" in against
    assert "prices are ours" in against

    # The film must not frame the insulation as an expense. It is bought one
    # layer at a time out of a waste stream, and calling it costly in the
    # same breath is the fastest way to lose a backer who would otherwise
    # have added a layer a year.
    for name, builder in ALL_SCREENS:
        text = " ".join(builder()).lower()
        for phrase in ("expensive bladder", "bladders are expensive",
                       "costly insulation", "insulation is expensive"):
            assert phrase not in text, (name, phrase)

    # And the campaign's own window has to actually contain the product.
    # The floor moved when the quote stopped billing lay-up labour
    # for a dome with no laminate, and when the markup became 20 per
    # cent on cost rather than 35 per cent on price.
    assert 9000.0 <= priced.price <= 50000.0, priced.price
    _build, floor = seed_model.floor_price()
    assert 8000.0 <= floor <= priced.price, floor


if __name__ == "__main__":
    validate_seed_facts()
    print(seed_film_report())
