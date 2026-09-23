"""The dome park: pads, hookups, and the arithmetic of hosting one.

A pad is a foundation plus services. A dome owner brings the house and plugs
in. This module is the numbers underneath that idea, and every figure the
tool or the film puts on screen comes from here.

Two kinds of number live in this file, and they are kept apart on purpose:

**Measured.** Anything derived from the project's own geometry. Which domes
fit which pad, how much deck a pad needs, how much solar an exterior carries
-- these are computed from the Dome Creator's shipped catalogue and cannot be
argued with.

**Declared.** Prices, rates and occupancy. These are inputs, not findings.
They are gathered in :data:`EXTERNAL_CONSTANTS` with a note on each, they are
printed by :func:`park_report`, and the film puts that table on screen before
it quotes a dollar. Change one and every downstream figure moves with it.

Nothing here is market research. The declared values are the owner's working
assumptions, set where a reader can see and replace them.
"""

from __future__ import annotations

import math
from dataclasses import dataclass
from functools import lru_cache

FT_PER_M = 3.280839895
SQFT_PER_SQM = 10.7639104


# ----------------------------------------------------------------------
# Declared inputs. Every one is an assumption, named and sourced.
# ----------------------------------------------------------------------

EXTERNAL_CONSTANTS: tuple[tuple[str, float, str, str], ...] = (
    # --- what a pad costs the host to build ---
    # The three flat rates that used to live here -- $22/sq ft for wood,
    # $9 for concrete, $2.50 for gravel -- are gone. They were contractor
    # rates carrying an "owner-built" description, and applying $22 to a
    # 48 ft pad produced a $39,810 deck, which is not a thing anybody would
    # build. :mod:`pad_deck` counts the piers, beams, joists and boards and
    # prices them off the one measured 2x6x12 this project already uses.
    # ``deck_gravel_usd_per_sqft`` survives only because a handful of
    # scaling checks reference it as a per-area proxy.
    ("deck_gravel_usd_per_sqft", 1.2, "USD/sq ft",
     "borrowed: pad_deck's gravel_base_usd_per_sqft, kept here so the "
     "area-scaling checks have a per-square-foot figure to multiply"),
    ("electric_pedestal_usd", 1400.0, "USD/pad",
     "assumption: 50 A pedestal, breaker, conduit run and trenching"),
    ("water_connection_usd", 1100.0, "USD/pad",
     "assumption: supply stub, frost protection, drain tie-in"),
    ("rotation_ring_usd_per_ft", 190.0, "USD per ft of diameter",
     "assumption: turntable ring, bearings and drive, scaling with diameter"),
    ("utility_column_usd", 2600.0, "USD/pad",
     "assumption: toilet, sink, shower head, outlets and drain in one column"),
    ("solar_usd_per_watt", 1.15, "USD/W",
     "assumption: panels, mounts and inverter, installed by the host"),

    # --- what it costs to have a pad at all, before any deck is poured ---
    # Left out of the first version of this model, which made hosting look
    # far easier than it is. A pad does not exist on its own: something had
    # to bring a road, a water main and a service drop to it, somebody had
    # to permit it, and somebody has to answer the phone every month.
    ("site_infrastructure_usd_per_pad", 6500.0, "USD/pad",
     "assumption: share of access road, trunk water and service drop, "
     "amortised over the pads they serve"),
    ("permit_usd_per_pad", 1200.0, "USD/pad",
     "assumption: siting, septic or sewer and electrical permits"),
    ("management_usd_per_month_per_pad", 45.0, "USD/month/pad",
     "assumption: bookings, metering, invoicing and turnover admin"),
    ("tax_insurance_usd_per_year_per_pad", 380.0, "USD/year/pad",
     "assumption: property tax and liability cover attributable to one pad"),

    # --- what the host charges ---
    # A flat base plus a small area term. Priced purely per square foot, an
    # 80 ft pad came out at $2,760 a month, which nobody would pay: a tenant
    # is buying a serviced place to stand, not floor area.
    ("lease_base_usd_per_month", 450.0, "USD/month",
     "assumption: what a serviced pad rents for, against local RV pad rates"),
    ("lease_usd_per_sqft_month", 0.12, "USD per sq ft of pad per month",
     "assumption: the part of the rent that does scale with size"),
    ("power_buy_usd_per_kwh", 0.14, "USD/kWh",
     "assumption: what the host pays the utility"),
    ("power_margin_usd_per_kwh", 0.02, "USD/kWh",
     "the owner's stated margin for metering and clerical work"),
    ("water_buy_usd_per_kgal", 4.50, "USD per 1000 gal",
     "assumption: what the host pays for water and sewer"),
    ("water_margin_usd_per_kgal", 0.50, "USD per 1000 gal",
     "the owner's stated margin, in the same spirit as the power margin"),
    ("power_export_usd_per_kwh", 0.045, "USD/kWh",
     "assumption: what the utility pays for a kilowatt hour sent back, "
     "which is nothing like what it charges for one"),

    # --- what a tenant uses ---
    ("tenant_kwh_per_month", 420.0, "kWh/month",
     "assumption: a small, well-insulated dwelling on grid power"),
    ("tenant_kgal_per_month", 2.6, "1000 gal/month",
     "assumption: one to two occupants, ordinary use"),
    ("meter_submeter_usd_per_pad", 340.0, "USD/pad",
     "a revenue-grade submeter and its enclosure on the pedestal, installed. "
     "Only the rebilling cases need one"),
    ("meter_admin_usd_per_month", 12.00, "USD/month",
     "assumption: a flat monthly charge for reading a meter and issuing a "
     "bill. Billing for the service rather than marking up the commodity is "
     "the form most US jurisdictions allow without a reseller licence"),
    ("utility_allowance_usd_per_month", 95.00, "USD/month",
     "assumption: a flat utility allowance bundled into a lease, set above "
     "the modelled draw so the host is not underwater on an average tenant. "
     "The host keeps the difference and carries the overage"),
    ("heavy_tenant_multiple", 2.10, "multiple of the modelled draw",
     "assumption: what a tenant running a workshop or a grow light does to "
     "the bill. It is what makes a flat allowance a risk rather than a fee"),
    ("guarantee_months", 12.0, "months",
     "assumption: how long the manufacturer underwrites a new host's "
     "occupancy. Long enough to cover a first summer season and a first "
     "winter, short enough to price"),
    ("occupancy_fraction", 0.80, "fraction of the year leased",
     "assumption: the owner's planning figure for a mature park"),

    # --- the alternatives a host is choosing between ---
    ("airbnb_furnishing_usd", 18000.0, "USD per unit",
     "assumption: furnishing a small rental to listing standard"),
    ("airbnb_turnover_usd", 95.0, "USD per turnover",
     "assumption: cleaning and linen for one changeover"),
    ("airbnb_turnovers_per_month", 3.0, "turnovers/month",
     "assumption: short-stay cadence"),
    ("airbnb_damage_reserve_fraction", 0.06, "fraction of revenue",
     "assumption: the owner's reserve against tenant damage and wear"),
    ("airbnb_platform_fee_fraction", 0.03, "fraction of revenue",
     "assumption: platform's host-side fee"),
    ("rental_renovation_usd_per_year", 2200.0, "USD/year",
     "assumption: amortised repaint, flooring and fittings on a let home"),

    # --- what the tenant is choosing between ---
    # The host side of this model came first, which made it a business plan
    # rather than an argument. A dome owner is comparing the pad against the
    # places they would otherwise sleep, and those have prices too.
    ("hotel_usd_per_night", 140.0, "USD/night",
     "assumption: a mid-range room, utilities and cleaning included"),
    ("short_let_usd_per_night", 95.0, "USD/night",
     "assumption: a whole-home short let at its monthly-discount rate"),
    ("apartment_usd_per_month", 1450.0, "USD/month",
     "assumption: a one-bedroom on a twelve-month lease"),
    ("apartment_move_in_months", 2.5, "months of rent",
     "assumption: first month plus a deposit and a half"),
    ("apartment_deposit_months", 1.5, "months of rent",
     "assumption: the refundable part of the above"),
    ("lease_break_months", 2.0, "months of rent",
     "assumption: what leaving a twelve-month lease early costs"),
    ("dome_transport_usd", 1800.0, "USD per move",
     "assumption: packing, a trailer and a day of two people's time"),
    ("dome_service_life_years", 30.0, "years",
     "assumption: straight-line life for a dome that is maintained"),
    ("dome_residual_fraction", 0.35, "fraction of cost",
     "assumption: the floor a maintained dome's value does not fall below"),
    ("resale_haircut_fraction", 0.15, "fraction of cost",
     "assumption: what a secondhand dome loses the day it becomes "
     "secondhand -- and the thing a real network would shrink"),
    ("dome_upkeep_usd_per_year", 600.0, "USD/year",
     "assumption: the owner maintaining their own home"),
    ("capital_rate_annual", 0.06, "fraction/year",
     "assumption: what the money tied up in a dome would otherwise earn"),

    # --- the cheapest pad that is still a pad ---
    ("deck_on_blocks_usd_per_sqft", 14.0, "USD/sq ft",
     "assumption: framed timber deck on precast blocks, owner-built, no "
     "excavation and no concrete"),
    ("hub_panel_usd", 2400.0, "USD",
     "assumption: one central power panel and water manifold serving a "
     "cluster of pads"),
    ("hub_pads_served", 4.0, "pads",
     "the owner's stated cluster: one hub in the middle of four domes, so "
     "each pad carries a quarter of it and a short spur instead of a run"),
    ("spur_usd_per_pad", 450.0, "USD/pad",
     "assumption: the wire and pipe from a central hub to a pad beside it"),

    # --- the iris pad ---
    ("iris_min_ft", 19.0, "ft",
     "the owner's stated smallest aperture: a one-person dome"),
    ("iris_max_ft", 40.0, "ft",
     "the owner's stated largest aperture: the large two-person dome"),
    ("iris_usd_per_ft", 310.0, "USD per ft of diameter",
     "assumption: leaves, track and the mechanism that opens and closes "
     "them, over a fixed rim at the same size"),

    # --- the campaign, and what a test site actually costs ---
    ("kickstarter_goal_usd", 100000.0, "USD",
     "the owner's stated raise: a test site, repeatable pad architecture, "
     "web infrastructure and documentation"),
    ("test_pad_count", 3.0, "pads",
     "the owner's stated first build: one to three pads on land they "
     "already hold"),
    ("setup_days_fast", 2.0, "days",
     "the owner's estimate for putting a dome up or taking it down at the "
     "quick end"),
    ("setup_days_slow", 14.0, "days",
     "the same at the slow end, for a large or heavily layered dome"),

    # --- the layered shell ---
    # The owner's Arctic argument, given a number. Cotton fibre insulation is
    # published near R-3.5 per inch; a quilted layer with roughly half an inch
    # of loft is set below that, deliberately.
    ("quilt_r_per_layer", 1.60, "hr sq ft F/BTU per layer",
     "assumption: one quilted recycled-fabric layer at about half an inch "
     "of loft, set under the published R-3.5/in for cotton fibre"),
    ("quilt_usd_per_sqft_layer", 1.10, "USD/sq ft per layer",
     "assumption: thread, backing and the labour to quilt it; the fabric "
     "itself is a waste stream"),

    # --- solar, for a tracking pad ---
    ("panel_watts_per_sqft", 18.0, "W/sq ft",
     "assumption: module output per square foot of exterior at standard test"),
    ("sun_hours_per_day", 4.6, "peak hours/day",
     "assumption: annual average for the owner's region"),
    ("tracking_gain_fraction", 0.25, "fraction",
     "assumption: single-axis tracking gain over a fixed array"),
    ("exterior_usable_fraction", 0.35, "fraction of shell area",
     "assumption: the share of a dome's shell that can carry panels"),
)

CONSTANTS: dict[str, float] = {name: value
                               for name, value, _unit, _note in EXTERNAL_CONSTANTS}


def declared(name: str) -> float:
    """One declared input, by name, so a caller cannot typo a figure in."""
    try:
        return CONSTANTS[name]
    except KeyError:
        raise KeyError(f"no declared constant {name!r}; "
                       f"choose from {', '.join(sorted(CONSTANTS))}") from None


# ----------------------------------------------------------------------
# Measured: which domes exist, and what footprint each needs
# ----------------------------------------------------------------------

@dataclass(frozen=True)
class DomeFootprint:
    """One shipped Dome Creator design, as a thing that has to fit on a pad."""

    name: str
    frequency: int
    dome_diameter_ft: float
    pad_diameter_ft: float
    """The dome's own foundation disc: what the pad has to cover."""
    floor_sqft: float
    height_ft: float


@lru_cache(maxsize=1)
def dome_catalogue() -> tuple[DomeFootprint, ...]:
    """Every shipped dome, measured. Read from the Creator, never typed."""
    import dome_model
    import presets

    out: list[DomeFootprint] = []
    for name, data in presets.PRESETS:
        config = dome_model.DomeConfig.from_dict(data)
        model = dome_model.DomeModel(config)
        stats = model.stats()
        out.append(DomeFootprint(
            name=name,
            frequency=int(stats["frequency"]),
            dome_diameter_ft=float(stats["radius"]) * 2.0 * FT_PER_M,
            pad_diameter_ft=(float(stats["radius"]) * config.foundation_scale
                             * 2.0 * FT_PER_M),
            floor_sqft=float(stats["floor_area"]) * SQFT_PER_SQM,
            height_ft=float(stats["height"]) * FT_PER_M,
        ))
    return tuple(out)


PAD_STEP_FT = 4.0
"""Pad sizes come in four-foot steps.

Not an aesthetic choice: decking and ring stock come in even lengths, and a
host building a second pad wants the same cut list as the first."""


@lru_cache(maxsize=1)
def pad_sizes() -> tuple[float, ...]:
    """The standard pad diameters, derived from the domes that must fit them.

    Every shipped dome's foundation is rounded up to the next four-foot step;
    the distinct results are the catalogue. Add a bigger dome to the Creator
    and a bigger pad size appears here on the next run.
    """
    sizes = {math.ceil(dome.pad_diameter_ft / PAD_STEP_FT) * PAD_STEP_FT
             for dome in dome_catalogue()}
    return tuple(sorted(sizes))


def domes_that_fit(pad_ft: float) -> tuple[DomeFootprint, ...]:
    """Which shipped domes a pad of this diameter can actually take."""
    return tuple(dome for dome in dome_catalogue()
                 if dome.pad_diameter_ft <= pad_ft + 1e-9)


def pad_area_sqft(pad_ft: float) -> float:
    return math.pi * (pad_ft / 2.0) ** 2


# ----------------------------------------------------------------------
# A pad, costed
# ----------------------------------------------------------------------

DECKS = ("gravel", "concrete", "wood")


@dataclass(frozen=True)
class Pad:
    """One serviced pad: the size, the deck, and what the host added to it."""

    diameter_ft: float
    deck: str = "concrete"
    rotating: bool = False
    utility_column: bool = False
    solar_watts: float = 0.0

    @property
    def area_sqft(self) -> float:
        return pad_area_sqft(self.diameter_ft)

    @property
    def fits(self) -> tuple[DomeFootprint, ...]:
        return domes_that_fit(self.diameter_ft)

    # -- what it costs to build ---------------------------------------
    # What each of this model's deck names is actually built as.
    DECK_BUILDS = {"gravel": "gravel", "concrete": "slab", "wood": "blocks"}

    def cost_rows(self) -> tuple[tuple[str, float], ...]:
        """Every line of the build cost, so the total can be audited."""
        import pad_deck

        built = pad_deck.deck(self.DECK_BUILDS[self.deck], self.diameter_ft)
        rows = [
            (f"{built.label.lower()}, {self.area_sqft:.0f} sq ft",
             built.cost),
            ("electrical pedestal", declared("electric_pedestal_usd")),
            ("water and drain", declared("water_connection_usd")),
            ("site infrastructure, per pad",
             declared("site_infrastructure_usd_per_pad")),
            ("permits", declared("permit_usd_per_pad")),
        ]
        if self.rotating:
            rows.append(("rotating base",
                         self.diameter_ft * declared("rotation_ring_usd_per_ft")))
        if self.utility_column:
            rows.append(("utility column", declared("utility_column_usd")))
        if self.solar_watts > 0.0:
            rows.append((f"solar, {self.solar_watts:,.0f} W",
                         self.solar_watts * declared("solar_usd_per_watt")))
        return tuple(rows)

    @property
    def build_cost(self) -> float:
        return sum(amount for _label, amount in self.cost_rows())

    # -- what it earns -------------------------------------------------
    @property
    def lease_per_month(self) -> float:
        return (declared("lease_base_usd_per_month")
                + self.area_sqft * declared("lease_usd_per_sqft_month"))

    @property
    def yearly_costs(self) -> float:
        """What the host pays every year just to keep the pad available.

        Not zero, and the film must not say it is. What a pad host does *not*
        pay is the cost of somebody else wearing out a building they own.
        """
        return (declared("management_usd_per_month_per_pad") * 12.0
                + declared("tax_insurance_usd_per_year_per_pad"))

    @property
    def utility_margin_per_month(self) -> float:
        """The host's cut of metered power and water.

        Deliberately small. It is payment for metering and paperwork, not a
        second rent, and the film says so.
        """
        power = (declared("tenant_kwh_per_month")
                 * declared("power_margin_usd_per_kwh"))
        water = (declared("tenant_kgal_per_month")
                 * declared("water_margin_usd_per_kgal"))
        return power + water

    @property
    def solar_kwh_per_month(self) -> float:
        """What a tracking pad's array makes in a month."""
        if self.solar_watts <= 0.0:
            return 0.0
        daily = self.solar_watts / 1000.0 * declared("sun_hours_per_day")
        if self.rotating:
            daily *= 1.0 + declared("tracking_gain_fraction")
        return daily * 30.4

    @property
    def solar_credit_per_month(self) -> float:
        """What that generation is actually worth, which is two rates.

        The first version of this valued every generated kilowatt hour at the
        retail price, and on a dome this size that is simply wrong: the shell
        carries several times the panel its occupant consumes, and you cannot
        save money on power you were never going to buy. So the part that
        displaces the tenant's draw is worth the retail rate, and everything
        past it is worth export -- a third of the price, if that.
        """
        generated = self.solar_kwh_per_month
        if generated <= 0.0:
            return 0.0
        used = min(generated, declared("tenant_kwh_per_month"))
        exported = generated - used
        return (used * declared("power_buy_usd_per_kwh")
                + exported * declared("power_export_usd_per_kwh"))

    @property
    def solar_surplus_fraction(self) -> float:
        """How much of the array's output the tenant cannot use.

        On screen, because a pitch that quietly valued the surplus at retail
        would be overstating a host's return by a factor of several.
        """
        generated = self.solar_kwh_per_month
        if generated <= 0.0:
            return 0.0
        used = min(generated, declared("tenant_kwh_per_month"))
        return (generated - used) / generated

    def year(self) -> dict:
        """One year of hosting this pad, at the declared occupancy."""
        occupancy = declared("occupancy_fraction")
        lease = self.lease_per_month * 12.0 * occupancy
        margin = self.utility_margin_per_month * 12.0 * occupancy
        solar = self.solar_credit_per_month * 12.0
        gross = lease + margin + solar
        costs = self.yearly_costs
        net = gross - costs
        return {
            "lease": lease,
            "utility_margin": margin,
            "solar_credit": solar,
            "gross": gross,
            "yearly_costs": costs,
            "net": net,
            "build_cost": self.build_cost,
            # Payback is on net, not gross. On gross it is a brochure number.
            "payback_years": (self.build_cost / net) if net > 0 else 0.0,
        }


def solar_watts_for(dome: DomeFootprint) -> float:
    """What a dome of this size could carry on its exterior.

    Measured off the shell the Creator computes, then reduced by the declared
    share of it that can actually hold a panel.
    """
    shell_sqft = 2.0 * math.pi * (dome.dome_diameter_ft / 2.0) ** 2
    usable = shell_sqft * declared("exterior_usable_fraction")
    return usable * declared("panel_watts_per_sqft")


# ----------------------------------------------------------------------
# The comparison the whole idea rests on
# ----------------------------------------------------------------------

@dataclass(frozen=True)
class HostComparison:
    """What a host carries, hosting a pad against hosting a furnished home."""

    label: str
    upfront: float
    yearly_costs: float
    note: str


def host_comparison(pad: Pad, nightly_equivalent: float | None = None
                    ) -> tuple[HostComparison, HostComparison]:
    """The pad host and the short-let host, side by side.

    The short-let side is costed against the *same* revenue the pad earns, so
    the comparison is about what each host spends to earn it, not about which
    business is bigger.
    """
    year = pad.year()
    revenue = year["gross"]

    turnovers = (declared("airbnb_turnovers_per_month")
                 * 12.0 * declared("occupancy_fraction"))
    # The short let carries everything the pad carries -- it is also managed,
    # taxed and insured -- plus the costs that come with owning the building
    # the tenant lives in. Giving it a clean slate would be a rigged compare.
    short_let_costs = (
        pad.yearly_costs
        + turnovers * declared("airbnb_turnover_usd")
        + revenue * declared("airbnb_damage_reserve_fraction")
        + revenue * declared("airbnb_platform_fee_fraction")
        + declared("rental_renovation_usd_per_year")
    )
    return (
        HostComparison(
            "dome pad", pad.build_cost, pad.yearly_costs,
            "management, tax and insurance; the home on it belongs to the "
            "tenant"),
        HostComparison(
            "furnished short let",
            pad.build_cost + declared("airbnb_furnishing_usd"),
            short_let_costs,
            "the same, plus cleaning, damage reserve, platform fee and "
            "renovation, every year"),
    )


# ----------------------------------------------------------------------
# Who pays the power bill, and the five ways that can be arranged
# ----------------------------------------------------------------------

@dataclass(frozen=True)
class Metering:
    """One arrangement for a pad's power and water.

    The five of these are not variations on a theme; they differ in who holds
    the utility account, who carries a heavy month, and how much regulation
    applies. What they do *not* differ in, much, is what the host earns --
    which is the finding, and the reason a host should pick on paperwork and
    risk rather than on return.
    """

    key: str
    label: str
    host_extra_build: float
    host_earns_per_month: float
    tenant_pays_per_month: float
    carries_overage: str
    regulated: bool
    note: str

    def share_of(self, gross_per_year: float) -> float:
        """What this arrangement is worth as a fraction of a year's gross."""
        earned = self.host_earns_per_month * 12.0 * declared("occupancy_fraction")
        return earned / gross_per_year if gross_per_year else 0.0


def metering_options() -> tuple[Metering, ...]:
    """Every way a pad's utilities can be handled, priced on one basis.

    Ordered by how much the host touches: from holding the account and
    marking up the commodity, to not being in the transaction at all.
    """
    at_cost = tenant_utilities(False)
    with_margin = tenant_utilities(True)
    allowance = declared("utility_allowance_usd_per_month")
    submeter = declared("meter_submeter_usd_per_pad")
    admin = declared("meter_admin_usd_per_month")

    return (
        Metering(
            "markup", "Submeter, rebill at cost plus a margin",
            submeter, with_margin - at_cost, with_margin,
            "nobody -- the tenant pays what they used",
            True,
            "The host holds the utility account and sells on. Simple to "
            "explain and the hardest to do legally: many US states and most "
            "utility tariffs restrict reselling power above cost, and some "
            "require a reseller registration. Check the tariff before "
            "promising a host this line of income."),
        Metering(
            "admin", "Submeter, rebill at cost, flat admin fee",
            submeter, admin, at_cost + admin,
            "nobody -- the tenant pays what they used",
            False,
            "The same meter, but the host charges for the service of reading "
            "it and issuing a bill rather than marking up the commodity. "
            "This is the form most jurisdictions allow without a licence, "
            "and it earns the host slightly more than the markup does."),
        Metering(
            "allowance", "Flat allowance bundled into the lease",
            0.0, allowance - at_cost, allowance,
            "the host -- every kilowatt hour over the allowance",
            False,
            "No meter, no bill, no regulator: it is rent. The host keeps the "
            "difference on an average tenant and eats it on a heavy one, "
            "which is a real risk and a bounded one, because the thing on "
            "the pad is a 277 sq ft dome and not a house."),
        Metering(
            "direct", "Utility meters the pad and bills the tenant",
            0.0, 0.0, at_cost,
            "nobody -- the host is not in the transaction",
            False,
            "The cleanest arrangement and the one that earns nothing. The "
            "obstacle is not money, it is whether the utility will open an "
            "account against a pad with a removable building on it; many "
            "will not without a permanent address."),
        Metering(
            "generate", "The pad generates and the tenant draws from it",
            0.0, 0.0, at_cost,
            "the host -- the array is the host's asset",
            False,
            "Solar on the pad, priced separately in solar_credit_per_month "
            "because it is an asset return and not a metering arrangement. "
            "Its limit is already on camera: most of what a dome-sized array "
            "makes is surplus the tenant cannot use."),
    )


def metering(key: str) -> Metering:
    for option in metering_options():
        if option.key == key:
            return option
    raise KeyError(f"unknown metering arrangement {key!r}")


def heavy_tenant_exposure() -> float:
    """What a flat allowance costs the host when the tenant is a heavy one.

    Per month, and negative means the host is underwater. Stated because the
    allowance is the arrangement a host will reach for first -- it is the one
    with no meter and no paperwork -- and it is the only one of the five that
    can lose money.
    """
    heavy = tenant_utilities(False) * declared("heavy_tenant_multiple")
    return declared("utility_allowance_usd_per_month") - heavy


# ----------------------------------------------------------------------
# The guarantee that gets the first pads built
# ----------------------------------------------------------------------

@dataclass(frozen=True)
class Guarantee:
    """An occupancy guarantee written to a host who builds a pad.

    The network has a chicken-and-egg problem: nobody buys a dome without
    somewhere to put it, and nobody builds a pad without a dome to put on it.
    A guarantee breaks it from the pad side, because the pad is the cheaper
    half and the one with the longer payback.
    """

    months: float
    lease_per_month: float
    occupancy: float

    @property
    def worst_case(self) -> float:
        """The pad never rents for the whole term and the writer pays it all."""
        return self.lease_per_month * self.months

    @property
    def expected(self) -> float:
        """What it costs on average, which is only the empty share."""
        return self.worst_case * (1.0 - self.occupancy)

    def payback_without(self, pad: "Pad") -> float:
        return pad.year()["payback_years"]

    def payback_with(self, pad: "Pad") -> float:
        """Payback when the guaranteed months are certain rather than likely.

        The guarantee does not add revenue -- it removes the discount a
        rational host would apply for the chance of an empty pad. So the
        first year is modelled at full occupancy and the rest at the declared
        rate.
        """
        year = pad.year()
        if year["net"] <= 0.0:
            return 0.0
        certain = (self.lease_per_month * self.months) - pad.yearly_costs * (
            self.months / 12.0)
        remaining = pad.build_cost - certain
        if remaining <= 0.0:
            return self.months / 12.0
        return self.months / 12.0 + remaining / year["net"]


def guarantee(pad: "Pad | None" = None, months: float | None = None
              ) -> Guarantee:
    pad = pad or basic_pad()
    return Guarantee(
        months=declared("guarantee_months") if months is None else months,
        lease_per_month=pad.lease_per_month,
        occupancy=declared("occupancy_fraction"))


# ----------------------------------------------------------------------
# The three domes this system is actually for, and the pad that takes all of them
# ----------------------------------------------------------------------

@dataclass(frozen=True)
class DomeClass:
    """One of the three sizes the pad range is designed around."""

    name: str
    floor_sqft: float
    longest_member_ft: float
    sleeps: str

    @property
    def diameter_ft(self) -> float:
        """Across, derived from the floor area. A dome's floor is a circle."""
        return 2.0 * math.sqrt(self.floor_sqft / math.pi)


DOME_CLASSES = (
    DomeClass("small personal", 314.00, 6.0, "one"),
    DomeClass("medium", 822.49, 10.0, "two"),
    DomeClass("large", 1184.39, 12.0, "two, with room"),
)
"""The owner's own three sizes: floor area and longest member, as stated.

The diameters are computed from the floor areas rather than typed, and they
are the reason the pad has to be adjustable at all."""


def iris_span():
    """The aperture range one pad needs to take all three classes."""
    return (declared("iris_min_ft"), declared("iris_max_ft"))


def iris_covers(dome) -> bool:
    low, high = iris_span()
    return low - 1e-9 <= dome.diameter_ft <= high + 1e-9


def iris_cost(diameter_ft=None) -> float:
    """The mechanism, priced at the aperture you build it to open to."""
    diameter_ft = diameter_ft or declared("iris_max_ft")
    return diameter_ft * declared("iris_usd_per_ft")


def cheap_pad_rows(diameter_ft=None):
    """The cheapest thing that is still a serviced pad.

    A framed deck on precast blocks rather than a slab, and one power panel
    and water manifold in the middle of four domes rather than a pedestal and
    a trench each. Nothing excavated, nothing poured.
    """
    diameter_ft = diameter_ft or declared("iris_max_ft")
    area = pad_area_sqft(diameter_ft)
    served = declared("hub_pads_served")
    return (
        (f"deck on blocks, {area:.0f} sq ft",
         area * declared("deck_on_blocks_usd_per_sqft")),
        (f"share of one hub panel, 1 of {served:.0f}",
         declared("hub_panel_usd") / served),
        ("spur from the hub", declared("spur_usd_per_pad")),
        ("permits", declared("permit_usd_per_pad")),
    )


def cheap_pad_cost(diameter_ft=None) -> float:
    return sum(amount for _label, amount in cheap_pad_rows(diameter_ft))


# ----------------------------------------------------------------------
# Solar, where it actually goes on a shell
# ----------------------------------------------------------------------

SOLAR_RADIUS_FT = 10.0
"""Every solar figure in the film is for a dome of this radius, and the film
says so: kilowatt hours a month mean nothing without the dome they came off."""


@dataclass(frozen=True)
class SolarLayout:
    """One way of cladding part of a shell, measured off the real panels."""

    name: str
    panels: int
    of_panels: int
    area_sqft: float
    watts: float
    overrides: dict
    note: str

    @property
    def kwh_fixed(self) -> float:
        return self.watts / 1000.0 * declared("sun_hours_per_day") * 30.4

    @property
    def kwh_tracking(self) -> float:
        return self.kwh_fixed * (1.0 + declared("tracking_gain_fraction"))

    @property
    def tracking_gain_kwh(self) -> float:
        return self.kwh_tracking - self.kwh_fixed


@lru_cache(maxsize=1)
def solar_layouts(radius_ft: float = SOLAR_RADIUS_FT):
    """Three ways to clad a shell, off the tool's own panel areas.

    Not a fraction of a hemisphere: the Dome Creator knows every panel's area
    and where its centroid points, so "the top half" and "one side" are
    selections rather than estimates.
    """
    import dome_model
    import presets

    data = dict(next(d for name, d in presets.PRESETS
                     if name == FLAGSHIP_DOME))
    data["radius"] = radius_ft / FT_PER_M
    base = dome_model.DomeModel(dome_model.DomeConfig.from_dict(dict(data)))
    panels = list(base.panels)
    total = len(panels)
    half = total // 2
    by_height = sorted(panels, key=lambda slot: -float(slot.centroid[2]))
    by_side = sorted(panels, key=lambda slot: -float(slot.centroid[0]))

    def build(name, chosen, skirt, note):
        keys = {slot.key for slot in chosen}
        overrides = {slot.key: "Solar Panel" for slot in chosen}
        if skirt:
            overrides.update({slot.key: "Metal Panel" for slot in panels
                              if slot.key not in keys})
        area = sum(slot.area for slot in chosen) * SQFT_PER_SQM
        return SolarLayout(
            name=name, panels=len(chosen), of_panels=total, area_sqft=area,
            watts=area * declared("panel_watts_per_sqft"),
            overrides=overrides, note=note)

    return (
        build("one side", by_side[:half], False,
              "half the shell, turned to face the sun. the other half stays "
              "whatever the owner wanted it to be"),
        build("top half, skirt below", by_height[:half], True,
              "cells on the upper panels, a metal skirt on the lower ones. "
              "the skirt is not decoration, it is the catchment"),
        build("whole shell", panels, False,
              "every panel a cell. the most power, and the case where "
              "turning the pad to face the sun stops meaning much"),
    )


# ----------------------------------------------------------------------
# The dome, once the pad is underneath it
# ----------------------------------------------------------------------

@dataclass(frozen=True)
class OnPad:
    """One shipped design, priced as a building that arrives on a pad.

    A dome standing on its own ground pays for its own foundation. A dome
    standing on a pad does not: the pad *is* the foundation, which is the
    single sentence this whole idea rests on. So the honest price of a dome
    in this system is the tool's price with the foundation line removed.
    """

    name: str
    full_cost: float
    """What the Dome Creator quotes, foundation included."""
    foundation_cost: float
    foundation_name: str

    @property
    def on_pad_cost(self) -> float:
        return self.full_cost - self.foundation_cost

    @property
    def foundation_share(self) -> float:
        return self.foundation_cost / self.full_cost if self.full_cost else 0.0


@lru_cache(maxsize=1)
def foundation_share() -> tuple[OnPad, ...]:
    """Every shipped design, and how much of it is the ground it stands on.

    Measured, not argued: the Creator is asked for each preset twice, once as
    shipped and once with its foundation set to bare ground, and the
    difference is what the pad host is buying on the tenant's behalf.
    """
    import dome_model
    import presets

    out: list[OnPad] = []
    for name, data in presets.PRESETS:
        stats = dome_model.DomeModel(
            dome_model.DomeConfig.from_dict(dict(data))).stats()
        out.append(OnPad(
            name=name,
            full_cost=float(stats["total_cost"]),
            foundation_cost=float(stats["foundation_cost"]),
            foundation_name=str(stats["foundation_name"]),
        ))
    return tuple(out)


def on_pad(name: str) -> OnPad:
    for row in foundation_share():
        if row.name == name:
            return row
    raise KeyError(f"no shipped design named {name!r}")


@lru_cache(maxsize=1)
def hardware_invariance(
        radii_m: tuple[float, ...] = (3.0, 5.0, 8.0)) -> tuple[dict, ...]:
    """The same design at three sizes, and what does *not* change with size.

    The owner's claim is that one hardware set carries across a cheap dome, a
    mid dome and a large one. The Creator settles it: hold every menu and move
    only the radius slider. The strut, hub and panel *counts* do not move, and
    neither does the hub bill -- what moves is the length of stick and the
    area of skin, because those are priced by the metre and the square metre.
    """
    import dome_model
    import presets

    base = dict(presets.PRESETS[0][1])
    rows: list[dict] = []
    for radius in radii_m:
        config = dict(base)
        config["radius"] = radius
        stats = dome_model.DomeModel(
            dome_model.DomeConfig.from_dict(config)).stats()
        rows.append({
            "radius_ft": radius * FT_PER_M,
            "diameter_ft": radius * 2.0 * FT_PER_M,
            "floor_sqft": float(stats["floor_area"]) * SQFT_PER_SQM,
            "struts": int(stats["strut_count"]),
            "hubs": int(stats["hub_count"]),
            "panels": int(stats["panel_count"]),
            "hub_cost": float(stats["hub_cost"]),
            "frame_cost": float(stats["frame_cost"]),
            "panel_cost": float(stats["panel_cost"]),
            "foundation_cost": float(stats["foundation_cost"]),
            "total_cost": float(stats["total_cost"]),
            "design": presets.PRESETS[0][0],
        })
    return tuple(rows)


# ----------------------------------------------------------------------
# The tenant's side: what a place to live costs, four ways
# ----------------------------------------------------------------------

MONTH_DAYS = 30.4
"""Days in an average month. 365.25 / 12, rounded where it is printed."""


@dataclass(frozen=True)
class HousingOption:
    """One way to have somewhere to live, costed over a stay of N months.

    Every option carries power and water, because two of them include those
    in the nightly rate and a comparison that quietly dropped them from the
    other two would be rigged.
    """

    label: str
    monthly: float
    """Out of pocket every month, utilities included."""
    entry: float
    """Paid once at the start."""
    note: str
    recoverable: float = 0.0
    """The part of ``entry`` that comes back when you leave."""
    depreciates: bool = False
    """True for the dome: what comes back shrinks with time, not with nothing."""
    asset_cost: float = 0.0
    """What the depreciating asset cost, if there is one."""
    early_exit_months: float = 0.0
    """Months of rent owed for leaving before a lease is up."""
    lease_months: float = 0.0

    def recovered(self, months: float) -> float:
        """What you can get back after a stay this long."""
        if not self.depreciates:
            return self.recoverable
        years = months / 12.0
        life = declared("dome_service_life_years")
        floor = declared("dome_residual_fraction")
        straight = max(floor, 1.0 - years / life)
        # The day a dome is secondhand it is worth less than a new one, and
        # pretending otherwise is what makes an ownership pitch dishonest.
        return self.asset_cost * straight * (
            1.0 - declared("resale_haircut_fraction"))

    def penalty(self, months: float) -> float:
        if self.lease_months and months < self.lease_months:
            return self.early_exit_months
        return 0.0

    def total(self, months: float) -> float:
        """Everything this stay costs, net of what you walk away with."""
        return (self.entry
                + self.monthly * months
                + self.penalty(months)
                - self.recovered(months))

    def per_month(self, months: float) -> float:
        return self.total(months) / months if months else 0.0


def tenant_utilities(margin: bool) -> float:
    """A month of power and water, with or without the host's margin."""
    power_rate = declared("power_buy_usd_per_kwh")
    water_rate = declared("water_buy_usd_per_kgal")
    if margin:
        power_rate += declared("power_margin_usd_per_kwh")
        water_rate += declared("water_margin_usd_per_kgal")
    return (declared("tenant_kwh_per_month") * power_rate
            + declared("tenant_kgal_per_month") * water_rate)


def housing_options(dome_name: str, pad: Pad | None = None
                    ) -> tuple[HousingOption, ...]:
    """The four ways a nomad can have a roof, priced on the same basis."""
    rent = declared("apartment_usd_per_month")
    building = on_pad(dome_name)
    pad = pad or basic_pad()
    return (
        HousingOption(
            "hotel room",
            declared("hotel_usd_per_night") * MONTH_DAYS, 0.0,
            "nothing to arrange, nothing to leave behind, nothing owned"),
        HousingOption(
            "short let",
            declared("short_let_usd_per_night") * MONTH_DAYS, 0.0,
            "someone else's furnished home at the monthly rate"),
        HousingOption(
            "apartment lease",
            rent + tenant_utilities(margin=False),
            rent * declared("apartment_move_in_months"),
            "twelve months, or pay to get out of them",
            recoverable=rent * declared("apartment_deposit_months"),
            early_exit_months=rent * declared("lease_break_months"),
            lease_months=12.0),
        HousingOption(
            f"own dome on a pad",
            (pad.lease_per_month
             + tenant_utilities(margin=True)
             + declared("dome_upkeep_usd_per_year") / 12.0
             + building.on_pad_cost * declared("capital_rate_annual") / 12.0),
            building.on_pad_cost + declared("dome_transport_usd"),
            f"{dome_name}, minus the {building.foundation_name.lower()} the "
            f"pad replaces; the lease is the only thing you cannot take",
            depreciates=True,
            asset_cost=building.on_pad_cost),
    )


def crossover_months(dome_name: str, pad: Pad | None = None,
                     limit: int = 120) -> int:
    """The first whole month at which bringing your own home is cheapest.

    Below it, this idea is worse than a hotel, and the film says so. That is
    the number that decides who this is for, and it is the reason the pitch
    is "longer than a hotel" rather than "cheaper than everything".
    """
    options = housing_options(dome_name, pad)
    dome = options[-1]
    others = options[:-1]
    for months in range(1, limit + 1):
        if dome.total(months) <= min(other.total(months) for other in others):
            return months
    return 0


# ----------------------------------------------------------------------
# The shell that gets warmer every winter
# ----------------------------------------------------------------------

@dataclass(frozen=True)
class ShellStep:
    """One quilted layer added under a removable shell."""

    layers: int
    r_value: float
    heating_usd_per_year: float
    added_cost: float
    marginal_cost: float = 0.0
    """What this one layer cost, on its own."""
    marginal_saving: float = 0.0
    """What this one layer takes off the yearly heating bill."""

    @property
    def marginal_payback_years(self) -> float:
        """How long *this* layer takes to pay for itself.

        The number that makes the owner's argument: the first layer pays back
        in months and the seventh takes years, so the right time to decide how
        warm a house is is never "when it was built".
        """
        if self.marginal_saving <= 0.0:
            return 0.0
        return self.marginal_cost / self.marginal_saving


def shell_ladder(dome_name: str, layers: int = 7) -> tuple[ShellStep, ...]:
    """What each added layer does to R-value and to a heating bill.

    The arithmetic is not this module's: heat loss comes from
    :mod:`two_v_demo.dome_performance`, which already models a degree-day year
    against an assembly's R-value, so the park film and the performance film
    cannot disagree about what R-20 is worth.

    What this file supplies is the dome's own shell area, measured off the
    Creator, and the declared R of one quilted layer.
    """
    from two_v_demo.dome_performance import FACT, Assembly, RunningCost

    import dome_model
    import presets

    data = next(d for name, d in presets.PRESETS if name == dome_name)
    stats = dome_model.DomeModel(
        dome_model.DomeConfig.from_dict(dict(data))).stats()
    shell_sqft = float(stats["surface_area"]) * SQFT_PER_SQM

    base_r = FACT["r_air_films"] + FACT["r_osb_half"]
    per_layer = declared("quilt_r_per_layer")
    cost_per_layer = shell_sqft * declared("quilt_usd_per_sqft_layer")

    steps: list[ShellStep] = []
    previous = 0.0
    for count in range(layers + 1):
        assembly = Assembly(f"{count} layers", base_r + per_layer * count)
        year = RunningCost("dome", shell_sqft, assembly)
        steps.append(ShellStep(
            layers=count,
            r_value=assembly.r_value,
            heating_usd_per_year=year.annual_cost,
            added_cost=cost_per_layer * count,
            marginal_cost=cost_per_layer if count else 0.0,
            marginal_saving=(previous - year.annual_cost) if count else 0.0,
        ))
        previous = year.annual_cost
    return tuple(steps)


FLAGSHIP_DOME = "Split-Log Homestead"
"""The design the tenant arithmetic is run on.

Not chosen to flatter it: it is the design this whole project argues for, it
is a plausible home rather than a workshop or a hangar, and its foundation is
the cheap kind, so the "the pad replaces your foundation" saving is at its
*smallest* on this one."""


def pad_for(dome_name: str) -> float:
    """The smallest standard pad this design will stand on."""
    dome = next(d for d in dome_catalogue() if d.name == dome_name)
    return next(size for size in pad_sizes() if size >= dome.pad_diameter_ft)


# ----------------------------------------------------------------------
# Report and proof
# ----------------------------------------------------------------------

def default_diameter() -> float:
    sizes = pad_sizes()
    return sizes[len(sizes) // 2]


def basic_pad(diameter_ft: float | None = None) -> Pad:
    """The cheapest thing that is still a pad: gravel and two hookups.

    Gravel rather than concrete, and not to flatter the figure: the deck is
    the cost of a pad, it scales with the square of the diameter, and a host
    building their first pad builds the one an RV park builds. Concrete is an
    upgrade, and the report prices it as one.
    """
    return Pad(diameter_ft=diameter_ft or default_diameter(), deck="gravel")


def standard_pad(diameter_ft: float | None = None) -> Pad:
    """The loaded pad: rotating, plumbed, and carrying solar.

    Sized so the array matches the largest dome that fits, because the panels
    live on the dome's exterior and the pad turns to aim them.
    """
    diameter_ft = diameter_ft or default_diameter()
    dome = max(domes_that_fit(diameter_ft),
               key=lambda d: d.floor_sqft, default=None)
    watts = solar_watts_for(dome) if dome is not None else 0.0
    return Pad(diameter_ft=diameter_ft, deck="concrete", rotating=True,
               utility_column=True, solar_watts=watts)


def park_report() -> str:
    """A portable audit: the declared inputs, then everything derived."""
    lines = [
        "DOME PARK -- THE NUMBERS",
        "",
        "Declared inputs. Every one is an assumption, not a finding.",
        "Change them here and every figure below moves.",
        "",
    ]
    for name, value, unit, note in EXTERNAL_CONSTANTS:
        lines.append(f"  {name:<34} {value:>10,.2f}  {unit:<28} {note}")
    lines.extend(["", "PAD SIZES (derived from the domes that must fit)", ""])
    for size in pad_sizes():
        fits = domes_that_fit(size)
        lines.append(f"  {size:>5.0f} ft  {pad_area_sqft(size):>7,.0f} sq ft  "
                     f"takes {len(fits)} of {len(dome_catalogue())} designs")
    lines.extend(["", "DOME CATALOGUE (measured)", ""])
    for dome in dome_catalogue():
        lines.append(f"  {dome.name:<28} {dome.dome_diameter_ft:>5.1f} ft dome  "
                     f"{dome.pad_diameter_ft:>5.1f} ft pad  "
                     f"{dome.floor_sqft:>6,.0f} sq ft floor")
    pad = standard_pad()
    year = pad.year()
    lines.extend(["", f"WORKED EXAMPLE -- a {pad.diameter_ft:.0f} ft "
                      f"{pad.deck} pad, rotating, with a utility column", ""])
    for label, amount in pad.cost_rows():
        lines.append(f"  {label:<38} ${amount:>10,.0f}")
    lines.append(f"  {'build cost':<38} ${pad.build_cost:>10,.0f}")
    lines.extend([
        "",
        f"  lease            ${year['lease']:>10,.0f} / year",
        f"  utility margin   ${year['utility_margin']:>10,.0f} / year",
        f"  solar credit     ${year['solar_credit']:>10,.0f} / year",
        f"  gross            ${year['gross']:>10,.0f} / year",
        f"  yearly costs    -${year['yearly_costs']:>10,.0f} / year  "
        "(management, tax, insurance)",
        f"  net              ${year['net']:>10,.0f} / year",
        f"  payback          {year['payback_years']:>10.1f} years  "
        "(on net, not gross)",
        "",
        "HOST COMPARISON",
        "",
    ])
    basic = basic_pad()
    basic_year = basic.year()
    lines.append(f"  a bare {basic.diameter_ft:.0f} ft pad -- slab and two "
                 f"hookups -- costs ${basic.build_cost:,.0f} to build")
    lines.append(f"  and nets ${basic_year['net']:,.0f} a year after "
                 f"management, tax and insurance, paying back in "
                 f"{basic_year['payback_years']:.1f} years")
    lines.append("")
    for row in host_comparison(basic):
        lines.append(f"  {row.label:<22} upfront ${row.upfront:>9,.0f}   "
                     f"yearly ${row.yearly_costs:>8,.0f}   {row.note}")
    lines.extend(["", "WHAT DRIVES A PAD'S COST", ""])
    for deck in DECKS:
        sample = Pad(basic.diameter_ft, deck)
        deck_cost = sample.area_sqft * declared(f"deck_{deck}_usd_per_sqft")
        share = deck_cost / sample.build_cost * 100.0
        lines.append(f"  {deck:<9} deck on {sample.diameter_ft:.0f} ft: "
                     f"${sample.build_cost:>9,.0f} total, deck is "
                     f"{share:>4.0f}% of it")
    lines.append("  the deck is priced by area, and area is diameter squared")
    lines.append("  (deck alone, so the fixed costs do not hide the shape):")
    for size in (24.0, 48.0):
        sample = Pad(size, "gravel")
        deck_only = sample.area_sqft * declared("deck_gravel_usd_per_sqft")
        lines.append(f"    {size:.0f} ft -> {sample.area_sqft:>6,.0f} sq ft  "
                     f"deck ${deck_only:>7,.0f}  total ${sample.build_cost:>8,.0f}")
    lines.append("  double the diameter and the deck quadruples; everything "
                 "else stays put.")
    lines.extend([
        "",
        "  And the figure that does not flatter the pitch:",
        f"  the loaded pad above costs ${pad.build_cost:,.0f} to build, against "
        f"${basic.build_cost + declared('airbnb_furnishing_usd'):,.0f} to build",
        "  a bare pad and furnish a short let on it. Rotation and an array are",
        "  not cheap, and on upfront cost alone the short let wins.",
        "",
        "  What the pad host does not carry is the yearly one: "
        f"${host_comparison(basic)[1].yearly_costs:,.0f} against "
        f"${basic.yearly_costs:,.0f},",
        "  and none of the pad host's is wear on a building they own.",
    ])

    lines.extend(["", "THE GROUND IS THE PART THE PAD REPLACES", ""])
    for row in sorted(foundation_share(), key=lambda r: -r.foundation_share):
        lines.append(f"  {row.name:<28} {row.foundation_name:<20} "
                     f"${row.foundation_cost:>8,.0f} of ${row.full_cost:>9,.0f} "
                     f"({row.foundation_share * 100:>4.1f}%)  "
                     f"on a pad: ${row.on_pad_cost:>9,.0f}")
    real = [r for r in foundation_share() if r.foundation_cost > 500.0]
    lines.append(f"  {len(real)} of {len(foundation_share())} designs stand on "
                 "something that costs real money;")
    lines.append("  for those the ground is "
                 f"{min(r.foundation_share for r in real) * 100:.0f}% to "
                 f"{max(r.foundation_share for r in real) * 100:.0f}% "
                 "of the build cost.")

    lines.extend(["", "ONE HARDWARE SET, THREE SIZES", ""])
    for row in hardware_invariance():
        lines.append(f"  {row['diameter_ft']:>5.1f} ft across  "
                     f"{row['floor_sqft']:>6,.0f} sq ft  "
                     f"{row['struts']:>4} struts  {row['hubs']:>3} hubs  "
                     f"{row['panels']:>4} panels  "
                     f"hubs ${row['hub_cost']:>7,.0f}  "
                     f"total ${row['total_cost']:>9,.0f}")
    lines.append("  the counts and the hub bill do not move; the stick length "
                 "and the skin area do.")

    home = FLAGSHIP_DOME
    home_pad = Pad(diameter_ft=pad_for(home), deck="gravel")
    lines.extend(["", f"WHAT A PLACE TO LIVE COSTS -- {home} on a "
                      f"{home_pad.diameter_ft:.0f} ft pad", ""])
    months = crossover_months(home, home_pad)
    for stay in (1, 3, 6, 12, 36):
        lines.append(f"  over {stay:>2} month(s):")
        for option in housing_options(home, home_pad):
            lines.append(f"    {option.label:<22} "
                         f"${option.per_month(stay):>7,.0f}/month   "
                         f"${option.total(stay):>9,.0f} for the stay")
    lines.append("")
    lines.append(f"  bringing your own home becomes the cheapest option at "
                 f"month {months}.")
    lines.append("  under that, a hotel or a short let is the right answer, "
                 "and this idea is not.")

    lines.extend(["", "THE SHELL THAT GETS WARMER EVERY WINTER", ""])
    for step in shell_ladder(home):
        payback = (f"{step.marginal_payback_years * 12.0:>5.1f} months"
                   if step.layers else "        --   ")
        lines.append(f"  {step.layers} layer(s)  R-{step.r_value:>5.1f}  "
                     f"heating ${step.heating_usd_per_year:>7,.0f}/year  "
                     f"spent ${step.added_cost:>7,.0f}  "
                     f"this layer pays back in {payback}")
    ladder = shell_ladder(home)
    lines.append(f"  seven layers take R-{ladder[0].r_value:.1f} to "
                 f"R-{ladder[-1].r_value:.1f} and the heating bill from "
                 f"${ladder[0].heating_usd_per_year:,.0f} to "
                 f"${ladder[-1].heating_usd_per_year:,.0f} a year.")
    lines.append(f"  the first layer pays for itself in "
                 f"{ladder[1].marginal_payback_years * 12.0:.0f} months; the "
                 f"seventh takes {ladder[-1].marginal_payback_years:.0f} years.")
    lines.append("  that is the argument: you add the layer that is worth "
                 "adding this year, and")
    lines.append("  the house gets warmer for as long as you own it.")
    lines.append("  this prices conduction only. It does not price the "
                 "windbreak, and the windbreak")
    lines.append("  is what makes layers work -- which is the shell's job, "
                 "and the part of the")
    lines.append("  Arctic argument this model cannot check.")
    return "\n".join(lines)



def _validate_metering() -> None:
    """The five arrangements, and the claim the brief makes about them."""
    options = metering_options()
    assert len(options) == 5, len(options)
    assert len({o.key for o in options}) == 5

    pad = basic_pad()
    gross = pad.year()["gross"]
    at_cost = tenant_utilities(False)

    for option in options:
        assert option.note, option.key
        assert option.host_earns_per_month >= 0.0, option.key
        # Nobody may be billed less than the power actually cost.
        assert option.tenant_pays_per_month >= at_cost - 1e-6, option.key
        # The claim the section rests on: metering is not the business. If any
        # arrangement ever earns a tenth of a host's gross, that sentence has
        # to be rewritten rather than left standing.
        assert option.share_of(gross) < 0.10, (
            f"{option.key} earns {option.share_of(gross) * 100:.1f}% of gross; "
            "the brief says metering is a rounding error")

    # Exactly one of them is the regulated one, and it is not the best-paying
    # one -- which is the whole reason the brief tells a host to pick on
    # paperwork rather than on return.
    regulated = [o for o in options if o.regulated]
    assert len(regulated) == 1, [o.key for o in regulated]
    best = max(options, key=lambda o: o.host_earns_per_month)
    assert not best.regulated, "the best-paying arrangement is the regulated one"
    assert metering("admin").host_earns_per_month > metering(
        "markup").host_earns_per_month, (
        "billing for the service earns less than marking up the commodity; "
        "the brief's advice to use the admin fee no longer holds")

    # And the flat allowance has to be able to lose money, or calling it a
    # risk in the brief is theatre.
    assert heavy_tenant_exposure() < 0.0, heavy_tenant_exposure()


def _validate_guarantee() -> None:
    """What underwriting a host's first year costs, and what it does not do."""
    pad = basic_pad()
    g = guarantee(pad)
    assert g.months > 0.0
    assert g.worst_case > g.expected > 0.0
    # Expected cost is only the empty share of the term.
    assert abs(g.expected - g.worst_case * (1.0 - declared("occupancy_fraction"))
               ) < 1e-6

    # The honest part: the guarantee removes risk, it does not add return. If
    # it ever starts halving a payback, the brief is understating it.
    without = g.payback_without(pad)
    with_it = g.payback_with(pad)
    assert with_it > 0.0 and without > 0.0
    assert with_it > without * 0.5, (
        f"guarantee moved payback {without:.1f} -> {with_it:.1f} yr; the brief "
        "says it buys certainty rather than return")


def validate_park() -> None:
    """Prove the model before anything quotes it."""
    _validate_metering()
    _validate_guarantee()
    catalogue = dome_catalogue()
    assert len(catalogue) >= 12, len(catalogue)
    for dome in catalogue:
        assert dome.pad_diameter_ft > dome.dome_diameter_ft, dome.name
        assert dome.floor_sqft > 0.0 and dome.height_ft > 0.0, dome.name

    sizes = pad_sizes()
    assert sizes == tuple(sorted(sizes)), sizes
    assert all(size % PAD_STEP_FT == 0 for size in sizes), sizes
    # Every dome must fit on at least one standard pad, or the catalogue of
    # pads does not actually serve the catalogue of domes.
    for dome in catalogue:
        assert any(dome.pad_diameter_ft <= size for size in sizes), dome.name
    # The largest pad takes everything; the smallest does not take everything,
    # or there would be no reason to offer sizes at all.
    assert len(domes_that_fit(sizes[-1])) == len(catalogue)
    assert len(domes_that_fit(sizes[0])) < len(catalogue)

    pad = standard_pad()
    assert pad.build_cost > 0.0
    assert abs(pad.build_cost - sum(a for _l, a in pad.cost_rows())) < 1e-6
    year = pad.year()
    assert year["gross"] > 0.0 and year["payback_years"] > 0.0
    # Rotation must be worth something, or the film should not claim it is.
    still = Pad(pad.diameter_ft, pad.deck, False, pad.utility_column,
                pad.solar_watts)
    assert pad.solar_kwh_per_month > still.solar_kwh_per_month
    assert pad.solar_credit_per_month > still.solar_credit_per_month

    # An array bigger than the tenant's draw must not be valued as though the
    # tenant bought all of it. This caught a model that overstated a loaded
    # pad's return by a factor of three.
    assert 0.0 < pad.solar_surplus_fraction < 1.0, pad.solar_surplus_fraction
    retail = pad.solar_kwh_per_month * declared("power_buy_usd_per_kwh")
    assert pad.solar_credit_per_month < retail, (
        "surplus generation is being credited at the retail rate")
    small = Pad(pad.diameter_ft, pad.deck, pad.rotating, pad.utility_column,
                solar_watts=declared("tenant_kwh_per_month") * 0.2)
    assert small.solar_surplus_fraction == 0.0, small.solar_surplus_fraction
    assert abs(small.solar_credit_per_month
               - small.solar_kwh_per_month
               * declared("power_buy_usd_per_kwh")) < 1e-6

    # The margin is meant to be small: it pays for paperwork, not rent.
    assert pad.utility_margin_per_month < pad.lease_per_month * 0.25

    # The claim the whole idea rests on is about *yearly* exposure, not
    # upfront cost, and the model says so plainly: a bare pad is far cheaper
    # to build than a rental is to furnish, while a loaded pad -- rotating,
    # plumbed, carrying an array -- can cost more upfront than the furnishing.
    # What neither version carries is a yearly bill for someone else's wear.
    basic = basic_pad()
    basic_host, short_let = host_comparison(basic)
    # A pad host's yearly cost is not zero, and the model refuses to pretend
    # it is. The claim is that it is smaller, and that none of it is wear on
    # a building the host owns.
    assert basic_host.yearly_costs > 0.0
    assert short_let.yearly_costs > basic_host.yearly_costs * 2.0
    assert basic.build_cost < declared("airbnb_furnishing_usd"), (
        "a bare pad should undercut furnishing a rental")
    loaded_host, _ = host_comparison(pad)
    assert loaded_host.yearly_costs > 0.0
    assert pad.build_cost > basic.build_cost

    # The deck dominates, and it dominates quadratically: doubling the
    # diameter roughly quadruples the area, and the deck is priced by area.
    # This is the single most useful thing a host can know before building,
    # so it is checked rather than mentioned.
    small, large = Pad(24.0, "gravel"), Pad(48.0, "gravel")
    small_deck = small.area_sqft * declared("deck_gravel_usd_per_sqft")
    large_deck = large.area_sqft * declared("deck_gravel_usd_per_sqft")
    assert 3.8 < (large_deck / small_deck) < 4.2, large_deck / small_deck

    # -- the tenant's side ----------------------------------------------
    # The pad replaces the dome's foundation, so the on-pad price has to be
    # lower than the catalogue price for every design that has a foundation
    # worth the name, and identical for the ones standing on grass.
    shares = foundation_share()
    assert len(shares) == len(dome_catalogue())
    for row in shares:
        assert 0.0 <= row.foundation_share < 1.0, row.name
        assert row.on_pad_cost < row.full_cost + 1e-6, row.name
    real = [row for row in shares if row.foundation_cost > 500.0]
    assert len(real) >= 6, len(real)
    assert max(row.foundation_share for row in real) > 0.35, (
        "if no design's foundation is a serious share of its cost, the pad "
        "is not replacing anything worth replacing")

    # One hardware set across three sizes: the counts and the hub bill must
    # not move, and the material must.
    sizes = hardware_invariance()
    assert len({row["struts"] for row in sizes}) == 1, sizes
    assert len({row["hubs"] for row in sizes}) == 1, sizes
    assert len({row["panels"] for row in sizes}) == 1, sizes
    assert max(row["hub_cost"] for row in sizes) - min(
        row["hub_cost"] for row in sizes) < 1e-6, sizes
    assert sizes[-1]["panel_cost"] > sizes[0]["panel_cost"] * 2.0, sizes
    assert sizes[-1]["floor_sqft"] > sizes[0]["floor_sqft"] * 5.0, sizes

    home = FLAGSHIP_DOME
    home_pad = Pad(diameter_ft=pad_for(home), deck="gravel")
    assert on_pad(home).on_pad_cost > 0.0
    options = housing_options(home, home_pad)
    assert len(options) == 4
    dome_option = options[-1]
    assert dome_option.depreciates and dome_option.asset_cost > 0.0
    # A dome is worth less the day after it is bought, and less again later.
    assert dome_option.recovered(1) < dome_option.asset_cost
    assert dome_option.recovered(120) < dome_option.recovered(12)
    # And it never falls to nothing, because it is a building.
    assert dome_option.recovered(600) > 0.0

    months = crossover_months(home, home_pad)
    assert months > 0, "bringing your own home never wins, at any stay length"
    # The claim being made is "longer than a hotel", so the crossover has to
    # be long enough that a hotel really is the better answer below it. If
    # this ever came out at one month the pitch would be wrong, not lucky.
    assert 2 <= months <= 24, months
    below = months - 1
    if below >= 1:
        cheapest = min(option.total(below) for option in options[:-1])
        assert dome_option.total(below) > cheapest, (
            "the crossover is not actually a crossover")
    assert dome_option.total(months) <= min(
        option.total(months) for option in options[:-1])

    # -- the layered shell -----------------------------------------------
    ladder = shell_ladder(home)
    assert len(ladder) == 8, len(ladder)
    assert ladder[0].layers == 0 and ladder[0].added_cost == 0.0
    for earlier, later in zip(ladder, ladder[1:]):
        assert later.r_value > earlier.r_value
        # Each layer helps, and each layer helps less than the one before it:
        # R-value is additive but the bill goes as one over R.
        assert later.heating_usd_per_year < earlier.heating_usd_per_year
        assert later.added_cost > earlier.added_cost
    gains = [earlier.heating_usd_per_year - later.heating_usd_per_year
             for earlier, later in zip(ladder, ladder[1:])]
    assert gains == sorted(gains, reverse=True), (
        "diminishing returns are a fact about 1/R, and the film says so")
    # Seven layers has to be worth having, or the Arctic argument is a story.
    assert ladder[-1].heating_usd_per_year < ladder[0].heating_usd_per_year * 0.5

    for name, value, unit, note in EXTERNAL_CONSTANTS:
        assert value > 0.0, name
        assert unit and note, name
        assert name in CONSTANTS


if __name__ == "__main__":
    print(park_report())
