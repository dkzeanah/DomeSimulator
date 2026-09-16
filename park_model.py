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
    ("deck_wood_usd_per_sqft", 22.0, "USD/sq ft",
     "assumption: pressure-treated deck, owner-built, materials plus hardware"),
    ("deck_concrete_usd_per_sqft", 9.0, "USD/sq ft",
     "assumption: 4 in slab, poured by a local contractor"),
    ("deck_gravel_usd_per_sqft", 2.5, "USD/sq ft",
     "assumption: compacted gravel over fabric, owner-built"),
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

    # --- what a tenant uses ---
    ("tenant_kwh_per_month", 420.0, "kWh/month",
     "assumption: a small, well-insulated dwelling on grid power"),
    ("tenant_kgal_per_month", 2.6, "1000 gal/month",
     "assumption: one to two occupants, ordinary use"),
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
    def cost_rows(self) -> tuple[tuple[str, float], ...]:
        """Every line of the build cost, so the total can be audited."""
        deck_rate = declared(f"deck_{self.deck}_usd_per_sqft")
        rows = [
            (f"{self.deck} deck, {self.area_sqft:.0f} sq ft",
             self.area_sqft * deck_rate),
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
        """Value of that generation at what the host would otherwise buy for."""
        return self.solar_kwh_per_month * declared("power_buy_usd_per_kwh")

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
    return "\n".join(lines)


def validate_park() -> None:
    """Prove the model before anything quotes it."""
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

    for name, value, unit, note in EXTERNAL_CONSTANTS:
        assert value > 0.0, name
        assert unit and note, name
        assert name in CONSTANTS


if __name__ == "__main__":
    print(park_report())
