"""The dome park's screens: every worksheet the film puts on the right.

:mod:`park_model` holds the arithmetic and :mod:`park_world` holds the
geometry.  This module holds neither.  It turns what those two already know
into the ordered lines a math chapter reveals, so that the film's copy and the
film's numbers cannot drift apart: change a declared input and the sentence on
screen changes with it, because the sentence is an f-string over the model.

Each ``steps_*`` function returns a derivation whose **last line is the
conclusion** -- the renderer holds it back and presents it in its own band.
Several of those conclusions are unflattering, which is the point: a pitch that
only shows the numbers that help is a pitch nobody should fund.
"""

from __future__ import annotations

from functools import lru_cache

import park_model
import park_world
from park_model import declared


def _conclude(steps: list[str], conclusion: str) -> tuple[str, ...]:
    steps.append(conclusion)
    return tuple(steps)


def usd(amount: float, width: int = 0) -> str:
    """A dollar figure, padded as one token.

    ``f"${x:>9,.0f}"`` pads the *digits* and leaves the dollar sign stranded
    at the left of the column -- "$    14,724" -- which is what the first cut
    of these screens put on film. Format first, pad after.
    """
    text = f"${amount:,.0f}"
    return f"{text:>{width}}" if width else text


def number(value: float, width: int = 0, places: int = 1) -> str:
    """The same, for anything with a prefix or a sign in front of it."""
    text = f"{value:,.{places}f}"
    return f"{text:>{width}}" if width else text


HOME = park_model.FLAGSHIP_DOME
"""The design every tenant figure is run on."""


@lru_cache(maxsize=1)
def foundation_showcase() -> park_model.OnPad:
    """The design the foundation chapter photographs.

    Not :data:`HOME`. The flagship sits on a gravel pad, so it saves the least
    of any design that has a foundation at all -- which is exactly why the
    tenant arithmetic uses it, and exactly why it is the wrong thing to point
    a camera at when the subject is "the ground is expensive". This picks the
    largest ordinary foundation share instead, and the screen names both, so
    the choice is visible rather than flattering.
    """
    real = [row for row in park_model.foundation_share()
            if row.foundation_cost > 500.0]
    # Skip anything standing on a treehouse platform: that is a support
    # structure, not a slab, and setting a pad against it would be comparing
    # a pad to a different building.
    ordinary = [row for row in real
                if "platform" not in row.foundation_name.lower()]
    return max(ordinary, key=lambda row: row.foundation_share)


@lru_cache(maxsize=1)
def home_pad() -> park_model.Pad:
    """The smallest standard pad the flagship design will stand on."""
    return park_model.Pad(diameter_ft=park_model.pad_for(HOME), deck="gravel")


@lru_cache(maxsize=1)
def loaded_pad() -> park_model.Pad:
    """The same pad with everything on it: rotation, plumbing, an array."""
    base = home_pad()
    dome = max(park_model.domes_that_fit(base.diameter_ft),
               key=lambda d: d.floor_sqft)
    return park_model.Pad(
        diameter_ft=base.diameter_ft, deck="concrete", rotating=True,
        utility_column=True, solar_watts=park_model.solar_watts_for(dome))


# ----------------------------------------------------------------------
# Before any dollar figure
# ----------------------------------------------------------------------

@lru_cache(maxsize=1)
def steps_declared() -> tuple[str, ...]:
    """What was typed in by a person, said before anything is claimed."""
    def value(name: str) -> str:
        for key, amount, unit, _note in park_model.EXTERNAL_CONSTANTS:
            if key == name:
                if unit.startswith("USD") or "USD" in unit:
                    return f"${amount:,.2f}".rstrip("0").rstrip(".")
                return f"{amount:,.2f}".rstrip("0").rstrip(".")
        raise KeyError(name)

    total = len(park_model.EXTERNAL_CONSTANTS)
    steps = [
        f"{total} numbers in this film were typed by a person.",
        "they live in one table, with a unit and a reason each:",
        f"   a serviced pad rents for {value('lease_base_usd_per_month')} a "
        f"month, plus "
        f"{value('lease_usd_per_sqft_month')} per square foot",
        f"   power costs the host {value('power_buy_usd_per_kwh')} a kWh; the "
        f"host adds {value('power_margin_usd_per_kwh')}",
        f"   a hotel room is {value('hotel_usd_per_night')} a night, a short "
        f"let {value('short_let_usd_per_night')}",
        f"   a one-bedroom is {value('apartment_usd_per_month')} a month",
        f"   the sun delivers {value('sun_hours_per_day')} peak hours a day "
        "here",
        f"   pads are leased {declared('occupancy_fraction') * 100:.0f}% of "
        "the year",
        "everything else on screen is measured off the Dome Creator:",
        "which domes fit which pad, how much deck that is, how much",
        "shell can carry panels, what the frame and the skin cost.",
        "none of the typed numbers are market research. they are the",
        "owner's working assumptions, printed where you can replace them.",
    ]
    return _conclude(
        steps,
        "change one of those and every figure after it moves, because "
        "the film reads the table rather than repeating it")


# ----------------------------------------------------------------------
# The measured part: what fits where
# ----------------------------------------------------------------------

@lru_cache(maxsize=1)
def steps_fit() -> tuple[str, ...]:
    """Which domes a pad takes -- arithmetic, not opinion."""
    catalogue = park_model.dome_catalogue()
    sizes = park_model.pad_sizes()
    steps = [
        f"the Dome Creator ships {len(catalogue)} designs, and each one has a",
        "foundation diameter the tool computes from its own geometry.",
        f"round each up to the next {park_model.PAD_STEP_FT:.0f} ft and you "
        "have the pad sizes:",
    ]
    for size in sizes:
        fits = park_model.domes_that_fit(size)
        steps.append(
            f"   {size:>5.0f} ft   {park_model.pad_area_sqft(size):>6,.0f} sq "
            f"ft   takes {len(fits):>2} of {len(catalogue)}")
    low, high = park_model.iris_span()
    steps.append("")
    steps.append("but one pad does not have to be one size. the three domes")
    steps.append("this system is for, by floor area and longest member:")
    for dome in park_model.DOME_CLASSES:
        steps.append(
            f"   {dome.name:<15} {number(dome.floor_sqft, 8, 2)} sq ft  ·  "
            f"{number(dome.diameter_ft, 4)} ft across  ·  "
            f"{dome.longest_member_ft:.0f} ft member")
    steps.append(f"an iris rim -- leaves on a track, opening and closing like")
    steps.append(f"a camera aperture -- spans {low:.0f} to {high:.0f} ft and "
                 "takes all three.")
    steps.append(f"the mechanism is {usd(park_model.iris_cost())} on top of "
                 "the deck.")
    steps.append("")
    smallest = min(catalogue, key=lambda d: d.pad_diameter_ft)
    largest = max(catalogue, key=lambda d: d.pad_diameter_ft)
    steps.extend([
        f"the {smallest.name.lower()} needs "
        f"{smallest.pad_diameter_ft:.0f} ft of pad;",
        f"the {largest.name.lower()} needs "
        f"{largest.pad_diameter_ft:.0f} ft.",
        f"{park_model.PAD_STEP_FT:.0f} ft steps because decking and ring "
        "stock come in even lengths,",
        "and the second pad a host builds wants the first one's cut list.",
    ])
    return _conclude(
        steps,
        f"add a bigger dome to the tool and a bigger pad size appears here "
        f"on the next run -- nobody edits a list")


# ----------------------------------------------------------------------
# The host's side
# ----------------------------------------------------------------------

@lru_cache(maxsize=1)
def steps_pad_cost() -> tuple[str, ...]:
    """What one pad costs to build, line by line, and what it returns."""
    pad = home_pad()
    year = pad.year()
    steps = [f"a {pad.diameter_ft:.0f} ft {pad.deck} pad, built:"]
    for label, amount in pad.cost_rows():
        steps.append(f"   {label:<34} {usd(amount, 9)}")
    steps.extend([
        f"   {'to build':<34} {usd(pad.build_cost, 9)}",
        "",
        f"lease         {usd(pad.lease_per_month, 7)} a month, leased "
        f"{declared('occupancy_fraction') * 100:.0f}% of the year",
        f"utility margin {usd(pad.utility_margin_per_month, 6)} a month -- "
        "paperwork money, not rent",
        f"management, tax  {"-" + usd(pad.yearly_costs):>8} a year "
        f"(insurance too)",
        f"net           {usd(year['net'], 7)} a year",
    ])
    cheap = park_model.cheap_pad_cost()
    services_cheap = cheap - park_model.cheap_pad_rows()[0][1]
    services_std = (pad.build_cost
                    - pad.area_sqft * declared(f"deck_{pad.deck}_usd_per_sqft"))
    steps.extend([
        "",
        "and the cheap version, for a host starting with nothing:",
        "a framed deck on precast blocks, and one power panel and water",
        f"manifold in the middle of {declared('hub_pads_served'):.0f} domes "
        "instead of a pedestal and a trench each.",
    ])
    for label, amount in park_model.cheap_pad_rows():
        steps.append(f"   {label:<34} {usd(amount, 9)}")
    steps.append(f"   {'built':<34} {usd(cheap, 9)}")
    steps.append(f"services: {usd(services_cheap)} against "
                 f"{usd(services_std)} -- nothing dug, nothing poured.")
    steps.append("the deck is still the cost of a pad. it always is.")
    return _conclude(
        steps,
        f"${pad.build_cost:,.0f} in, ${year['net']:,.0f} a year out, paid "
        f"back in {year['payback_years']:.1f} years -- on net, because "
        f"payback on gross is a brochure number")


@lru_cache(maxsize=1)
def steps_exposure() -> tuple[str, ...]:
    """The host's real argument, with the number that argues against it."""
    pad = home_pad()
    loaded = loaded_pad()
    host, short_let = park_model.host_comparison(pad)
    furnish = declared("airbnb_furnishing_usd")
    steps = [
        "two ways to earn the same money off the same piece of land.",
        "",
        f"pad host        {usd(host.upfront, 9)} up front   "
        f"{usd(host.yearly_costs, 7)} a year",
        f"short-let host  {usd(short_let.upfront, 9)} up front   "
        f"{usd(short_let.yearly_costs, 7)} a year",
        "",
        "the short-let host's yearly bill is the same management, tax",
        "and insurance, plus cleaning at "
        f"${declared('airbnb_turnover_usd'):.0f} a turnover,",
        f"a {declared('airbnb_damage_reserve_fraction') * 100:.0f}% damage "
        f"reserve, a {declared('airbnb_platform_fee_fraction') * 100:.0f}% "
        "platform fee, and "
        f"${declared('rental_renovation_usd_per_year'):,.0f} of renovation.",
        f"that is {short_let.yearly_costs / host.yearly_costs:.1f} times the "
        "pad host's, every year, for ever.",
        "",
        "and the figure that does not help: a loaded pad -- rotating,",
        f"plumbed, carrying an array -- costs ${loaded.build_cost:,.0f} to "
        "build,",
        f"against ${pad.build_cost + furnish:,.0f} for a bare pad and a "
        "furnished let on it.",
        "on up-front cost alone, the short let wins.",
    ]
    return _conclude(
        steps,
        "the pad host's case is not that it is cheaper to start. it is "
        "that none of their yearly bill is wear on a building somebody "
        "else is living in")


# ----------------------------------------------------------------------
# The hinge: the ground is the part the pad replaces
# ----------------------------------------------------------------------

@lru_cache(maxsize=1)
def steps_foundation() -> tuple[str, ...]:
    """The measured reason a dome on a pad is a cheaper dome."""
    rows = sorted(park_model.foundation_share(),
                  key=lambda row: -row.foundation_share)
    real = [row for row in rows if row.foundation_cost > 500.0]
    steps = [
        "ask the Dome Creator for each design twice: once as shipped,",
        "once with its foundation set to bare ground. the difference",
        "is what the pad is standing in for.",
    ]
    for row in rows[:5]:
        steps.append(
            f"   {row.name[:27]:<27} {number(row.foundation_share * 100, 4)}%   "
            f"{usd(row.foundation_cost, 8)}")
    steps.extend([
        f"   ... and {len(rows) - 5} more",
        f"{len(real)} of {len(rows)} designs stand on something that costs",
        f"real money: {min(r.foundation_share for r in real) * 100:.0f}% to "
        f"{max(r.foundation_share for r in real) * 100:.0f}% of the build.",
        "the other four sit on grass, and for those the pad replaces",
        "nothing -- which is worth saying out loud.",
    ])
    home = park_model.on_pad(HOME)
    show = foundation_showcase()
    steps.append(f"the {show.name.lower()} is the one in the picture:")
    steps.append(f"{usd(show.full_cost)} on its own "
                 f"{show.foundation_name.lower()}, "
                 f"{usd(show.on_pad_cost)} on a pad.")
    return _conclude(
        steps,
        f"and the {HOME.lower()}, which every tenant figure in this film "
        f"is run on, saves the least of any design that has a foundation at "
        f"all: {usd(home.foundation_cost)}. that is the one we costed with")


# ----------------------------------------------------------------------
# The tenant's side
# ----------------------------------------------------------------------

@lru_cache(maxsize=1)
def steps_stay() -> tuple[str, ...]:
    """Four ways to have a roof, on one basis, over one stay."""
    pad = home_pad()
    options = park_model.housing_options(HOME, pad)
    months = 12
    steps = [
        f"a year in one place, four ways. every line carries power",
        "and water, because two of them include it in the nightly rate",
        "and dropping it from the other two would rig the compare.",
        "",
    ]
    for option in options:
        steps.append(f"   {option.label:<20} "
                     f"{usd(option.per_month(months), 7)} / month   "
                     f"{usd(option.total(months), 8)} for the year")
    dome = options[-1]
    cheapest_rental = min(options[:-1], key=lambda o: o.total(months))
    steps.extend([
        "",
        f"the dome line is the {HOME.lower()} at "
        f"${dome.asset_cost:,.0f} on a pad,",
        f"plus ${declared('dome_transport_usd'):,.0f} to move it, and it "
        "carries the two",
        "costs an ownership pitch usually hides: "
        f"${declared('dome_upkeep_usd_per_year'):,.0f} a year of upkeep",
        f"and {declared('capital_rate_annual') * 100:.0f}% on the money tied "
        "up in it.",
        f"at the end of the year it is worth ${dome.recovered(months):,.0f}, "
        "after a",
        f"{declared('resale_haircut_fraction') * 100:.0f}% secondhand haircut "
        "taken on day one.",
    ])
    return _conclude(
        steps,
        f"${dome.total(months):,.0f} against ${cheapest_rental.total(months):,.0f} "
        f"for the cheapest thing you could rent -- and at the end of it "
        f"you still own the house")


@lru_cache(maxsize=1)
def steps_crossover() -> tuple[str, ...]:
    """How long the stay has to be. Including where this idea loses."""
    pad = home_pad()
    options = park_model.housing_options(HOME, pad)
    dome = options[-1]
    months = park_model.crossover_months(HOME, pad)
    steps = [
        "so how long do you have to stay for this to make sense?",
        "run the same four options at every stay length and find",
        "the month the dome stops being the expensive answer.",
        "",
    ]
    for stay in (1, 2, 3, 6, 12, 36):
        best = min(options[:-1], key=lambda o: o.total(stay))
        marker = "<--" if stay == months else "   "
        steps.append(
            f"   {stay:>2} month(s)  dome {usd(dome.total(stay), 8)}   "
            f"best rental {usd(best.total(stay), 8)} {marker}")
    below = months - 1
    steps.extend([
        "",
        f"under {months} months this idea loses, and it should: at "
        f"{below} month(s)",
        f"a short let costs ${min(o.total(below) for o in options[:-1]):,.0f} "
        f"and the dome costs ${dome.total(below):,.0f}.",
        "nobody should buy a house to stay somewhere for a month.",
    ])
    return _conclude(
        steps,
        f"it starts working at month {months} and never stops. that is "
        f"the stay length neither a hotel nor a lease serves")


# ----------------------------------------------------------------------
# The dome the system assumes
# ----------------------------------------------------------------------

@lru_cache(maxsize=1)
def steps_hardware() -> tuple[str, ...]:
    """One hardware set across three sizes, settled by the tool."""
    rows = park_model.hardware_invariance()
    small, large = rows[0], rows[-1]
    steps = [
        f"take the {rows[0]['design'].lower()} and move one slider:",
        "the radius. every other menu is held where it was.",
        "",
    ]
    for row in rows:
        steps.append(
            f"   {number(row['diameter_ft'], 5)} ft  ·  "
            f"{number(row['floor_sqft'], 6, 0)} sq ft  ·  "
            f"{row['struts']} struts  ·  {row['hubs']} hubs  ·  "
            f"{row['panels']} panels")
    steps.extend([
        "",
        f"the counts do not move. the hub bill does not move either:",
        f"{usd(small['hub_cost'])} at {small['diameter_ft']:.0f} ft and "
        f"{usd(large['hub_cost'])} at {large['diameter_ft']:.0f} ft.",
        f"what moves is the stick and the skin -- panels go from",
        f"{usd(small['panel_cost'])} to {usd(large['panel_cost'])}, "
        "because those are priced by area.",
        f"{large['floor_sqft'] / small['floor_sqft']:.1f} times the floor off "
        "the same list of parts.",
    ])
    return _conclude(
        steps,
        "that is what makes one good hardware set worth buying: it is "
        "the part of the house that does not change when the house does")


@lru_cache(maxsize=1)
def steps_layers() -> tuple[str, ...]:
    """R-value added a layer at a time, and what each layer is worth."""
    ladder = park_model.shell_ladder(HOME)
    first, last = ladder[1], ladder[-1]
    steps = [
        f"one quilted layer is declared at "
        f"R-{declared('quilt_r_per_layer'):.1f}: half an inch of loft,",
        "set under the published R-3.5 an inch for cotton fibre.",
        "the heat loss is the same degree-day model the performance",
        "film uses, run on this dome's own shell area.",
        "",
    ]
    # Every other rung. The whole ladder is eight rows, and eight rows plus
    # the prose either side of them shrinks the worksheet font to nothing.
    for step in (ladder[0], ladder[1], ladder[3], ladder[5], ladder[7]):
        label = "bare    " if step.layers == 0 else (
            f"{step.layers} layer{'s' if step.layers > 1 else ' '}")
        rating = f"{'R-' + format(step.r_value, '.1f'):>6}"
        pays = ("" if step.layers == 0 else
                f"  ·  pays back in "
                f"{number(step.marginal_payback_years * 12, 5)} months")
        steps.append(f"   {label}  ·  {rating}  ·  "
                     f"{usd(step.heating_usd_per_year, 6)} a year{pays}")
    steps.extend([
        "",
        f"the first layer pays for itself in "
        f"{first.marginal_payback_years * 12:.0f} months; the seventh takes "
        f"{last.marginal_payback_years:.0f} years.",
        "that is 1 over R, and it is why deciding the whole R-value",
        "on day one is the wrong move.",
        f"seven layers is R-{last.r_value:.1f} -- a good wall, not a "
        "code-beating one --",
        f"and it cost {usd(last.added_cost)} spread over years.",
        "this prices conduction only. it does not price the windbreak,",
        "and the windbreak is what makes layers work.",
    ])
    return _conclude(
        steps,
        "the shell is the pumpkin suit. the layers are everything you "
        "put on under it, and you never have to decide how many at once")


# ----------------------------------------------------------------------
# What the pad gives back
# ----------------------------------------------------------------------

@lru_cache(maxsize=1)
def steps_solar() -> tuple[str, ...]:
    """Three ways to clad a shell, and where tracking stops paying."""
    layouts = park_model.solar_layouts()
    side, skirt, whole = layouts
    steps = [
        f"every figure here is for a {park_model.SOLAR_RADIUS_FT:.0f} ft "
        "radius dome -- the medium,",
        "two-person size. a number a month means nothing without that.",
        f"the panels are on the dome, not the pad. the pad turns.",
        "",
    ]
    for layout in layouts:
        steps.append(
            f"   {layout.name:<22} {layout.panels:>2} of {layout.of_panels} "
            f"panels  ·  {number(layout.area_sqft, 5, 0)} sq ft  ·  "
            f"{number(layout.watts / 1000.0, 5)} kW")
    steps.append("")
    for layout in layouts:
        steps.append(
            f"   {layout.name:<22} fixed "
            f"{number(layout.kwh_fixed, 5, 0)}  ·  tracking "
            f"{number(layout.kwh_tracking, 5, 0)} kWh a month")
    steps.extend([
        "",
        f"the skirt below the cells is the catchment -- the same metal that",
        "keeps rain off the bottom ring collects it.",
        f"a tenant uses about {declared('tenant_kwh_per_month'):,.0f} kWh a "
        "month.",
        f"and the one that does not flatter the tracking ring: cover the",
        "whole shell and it is always facing the sun with something, so",
        "turning the pad buys much less than it does on a half-clad dome.",
        f"the whole shell also makes "
        f"{whole.kwh_tracking / declared('tenant_kwh_per_month'):.1f} times "
        "what a tenant uses. that is surplus,",
        f"and the model refuses to credit surplus at retail: it is worth "
        f"${declared('power_export_usd_per_kwh'):.3f} sent back,",
        f"not the ${declared('power_buy_usd_per_kwh'):.2f} it would have "
        "saved.",
    ])
    return _conclude(
        steps,
        f"clad one side and turning is worth "
        f"{number(side.tracking_gain_kwh, 0, 0)} kWh a month. clad all of it "
        f"and you have more power than you can use, a bigger bill to buy it, "
        f"and less reason to turn anything")


# ----------------------------------------------------------------------
# What the money is for
# ----------------------------------------------------------------------

def reference_park() -> park_world.Park:
    """The park the ask is costed against: one row, one of each pad size."""
    return park_world.default_park(pad_count=6, rotating=True, deck="gravel")


@lru_cache(maxsize=1)
def steps_ask() -> tuple[str, ...]:
    """What the raise is for, costed with the same model as everything else."""
    goal = declared("kickstarter_goal_usd")
    count = int(declared("test_pad_count"))
    sizes = park_model.pad_sizes()[:count]
    pads = [park_model.Pad(diameter_ft=size, deck="gravel") for size in sizes]
    build = sum(pad.build_cost for pad in pads)
    rest = goal - build
    whole = reference_park().economics()
    steps = [
        f"the goal is {usd(goal)}. here is what it is actually for.",
        "",
        f"   {count} pads on land already held, {sizes[0]:.0f} to "
        f"{sizes[-1]:.0f} ft:",
    ]
    for pad in pads:
        steps.append(f"      {pad.diameter_ft:>2.0f} ft gravel pad, "
                     f"{pad.area_sqft:>5,.0f} sq ft   {usd(pad.build_cost, 9)}")
    steps.extend([
        f"      {'built':<28} {usd(build, 9)}",
        "",
        f"   the remaining {usd(rest)} is the part that is not concrete:",
        "      a website, and a list of people who want to host or park",
        "      one to three dome designs that suit this, built and measured",
        "      a camera, because all of it is published as it is made",
        "",
        "what the money does not buy: the tracking foundation. a pad that",
        "turns is a nice thing to own and it is not what a first site needs,",
        "so it is not on this list.",
        "",
        f"a whole {whole['pads']}-pad park costs {usd(whole['build_cost'])} "
        "to build.",
        "this raise is not that. it is the first three pads and the",
        "drawings that let anyone else build the fourth.",
    ]) 
    return _conclude(
        steps,
        "and the honest part: this gets built either way. the raise decides "
        "whether it takes a year or ten, and whether the drawings reach "
        "anyone else while it happens")


ALL_SCREENS: tuple[tuple[str, object], ...] = (
    ("declared", steps_declared),
    ("fit", steps_fit),
    ("pad_cost", steps_pad_cost),
    ("exposure", steps_exposure),
    ("foundation", steps_foundation),
    ("stay", steps_stay),
    ("crossover", steps_crossover),
    ("hardware", steps_hardware),
    ("layers", steps_layers),
    ("solar", steps_solar),
    ("ask", steps_ask),
)


def park_film_report() -> str:
    """Every screen in the film, as text, for reading without rendering."""
    lines = ["DOME PARK -- THE FILM'S SCREENS", ""]
    for name, builder in ALL_SCREENS:
        lines.append(f"--- {name} ---")
        steps = builder()
        for step in steps[:-1]:
            lines.append(f"   {step}")
        lines.append(f"   => {steps[-1]}")
        lines.append("")
    lines.append(park_model.park_report())
    return "\n".join(lines)


def validate_park_facts() -> None:
    """Every screen must build, say something, and end in a conclusion."""
    park_model.validate_park()
    from .park_bridge import validate_park_bridge
    validate_park_bridge()

    seen: set[tuple[str, ...]] = set()
    for name, builder in ALL_SCREENS:
        steps = builder()
        assert len(steps) >= 6, (name, len(steps))
        assert steps not in seen, f"{name} repeats another screen"
        seen.add(steps)
        for step in steps[:-1]:
            assert isinstance(step, str), (name, step)
            # A blank line is a deliberate spacer; anything else must carry
            # text, because an empty step renders as a gap the viewer reads
            # as a missing figure.
            assert step == "" or step.strip(), (name, repr(step))
            # Steps are one line of a worksheet in a panel 42% of the frame
            # wide. Past this they wrap into two and the derivation stops
            # reading as a column of statements.
            assert len(step) < 130, (name, len(step), step[:60])
        # The conclusion gets its own band and wraps there, so it is allowed
        # to be a sentence rather than a line.
        assert len(steps[-1]) < 230, (name, len(steps[-1]))
        assert steps[-1].strip(), name
        assert "{" not in "".join(steps), f"{name} has an unformatted field"

    # The screens that are supposed to be unflattering must actually contain
    # the unflattering figure, or the discipline is decorative.
    exposure = " ".join(steps_exposure())
    assert "short let wins" in exposure, exposure[-200:]
    crossover = " ".join(steps_crossover())
    assert "loses" in crossover
    layers = " ".join(steps_layers())
    assert "conduction only" in layers
    assert "not price the windbreak" in layers
    solar = " ".join(steps_solar())
    assert "surplus" in solar and "refuses" in solar, (
        "the solar screen must admit that most of the array's output is "
        "worth export, not retail")

    # The crossover screen has to name the same month the model computes.
    months = park_model.crossover_months(HOME, home_pad())
    assert f"month {months}" in crossover, (months, crossover[-200:])

    # A loaded pad must be a genuinely different pad from the plain one, or
    # two screens are describing the same thing with different words.
    assert loaded_pad().build_cost > home_pad().build_cost
    assert loaded_pad().solar_watts > 0.0
