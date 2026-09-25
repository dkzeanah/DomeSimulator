"""The pad, from both sides of it.

A network of serviced pads only works if it is a better deal for the
landowner *and* for the person who arrives with a building. Most
land-rental arrangements are a better deal for exactly one of them, which is
why they end badly, and an argument that only adds up on one side is not an
argument.

So this module works it out twice.

**For the tenant** -- somebody who owns a dome and needs somewhere to put it
-- against the three things they would otherwise do: a hotel, a short let, or
a twelve-month apartment lease.

**For the host** -- somebody who owns ground -- against the two things they
would otherwise do with it: let it sit, or furnish a unit and let it short.

Every rate here is declared in :mod:`park_model` with the assumption written
beside it, and every quantity is this book's own dome. Nothing is a market
figure somebody looked up and nothing is a number typed into a sentence; the
rates are stated guesses and the book says so, because a comparison whose
inputs are invisible is a sales sheet.

WHY A PAD IS NOT AN RV PITCH

Stated here because it is the comparison everybody reaches for first.

An RV park sells nights. Its costs are turnover: booking, cleaning, hookup,
disconnection, and an occupancy that collapses out of season. Its tenant is
leaving, always, and behaves accordingly.

A pad sells years. It is built once, connected once, metered once, and
occupied by somebody who owns the building on it -- which means the tenant's
own asset is the deposit. The host's revenue per square foot is lower and
their cost per occupied month is very much lower, and the difference is
turnover.
"""

from __future__ import annotations

from dataclasses import dataclass

MONTHS = 12.0


@dataclass(frozen=True)
class Option:
    """One way of being housed, per month and at the door."""

    label: str
    monthly: float
    entry: float
    recoverable: float
    """How much of the entry comes back when you leave."""
    asset: float
    """What you own afterwards, at cost."""
    note: str

    def over(self, years: float) -> float:
        """What this costs across ``years``, net of what comes back."""
        return self.monthly * MONTHS * years + self.entry - self.recoverable


@dataclass(frozen=True)
class HostCase:
    """One way of earning from a piece of ground."""

    label: str
    upfront: float
    yearly_income: float
    yearly_cost: float
    note: str

    @property
    def yearly_net(self) -> float:
        return self.yearly_income - self.yearly_cost

    def payback_years(self) -> float:
        if self.yearly_net <= 0.0:
            return float("inf")
        return self.upfront / self.yearly_net


def _declared(name: str) -> float:
    import park_model

    return park_model.declared(name)


def pad_rent_monthly() -> float:
    """What a serviced pad for this dome rents for, per month.

    A base plus a part that scales with the platform's area, both declared
    in park_model against local RV and storage rates.
    """
    import pad_deck

    across = pad_deck.pad_diameter_ft()
    area = pad_deck.decagon_area_sqft(across)
    return (_declared("lease_base_usd_per_month")
            + _declared("lease_usd_per_sqft_month") * area)


def tenant_options() -> tuple[Option, ...]:
    """What it costs to be housed, four ways, for this book's dome."""
    import seed_model

    quote = seed_model.quote()
    dome = quote.price
    life = _declared("dome_service_life_years")
    apartment = _declared("apartment_usd_per_month")

    return (
        Option(
            "hotel room",
            monthly=_declared("hotel_usd_per_night") * 30.0,
            entry=0.0, recoverable=0.0, asset=0.0,
            note="nothing to arrange and nothing owned"),
        Option(
            "short let",
            monthly=_declared("short_let_usd_per_night") * 30.0,
            entry=0.0, recoverable=0.0, asset=0.0,
            note="somebody else's furnished home at the monthly rate"),
        Option(
            "apartment lease",
            monthly=apartment,
            entry=apartment * _declared("apartment_move_in_months"),
            recoverable=apartment * _declared("apartment_deposit_months"),
            asset=0.0,
            note="twelve months, or pay to get out of them"),
        Option(
            "own the dome, rent the pad",
            # The pad's rent, plus the dome wearing out over its life. The
            # dome is an asset rather than a cost, so only its depreciation
            # is a monthly figure -- but it is a real one and it is here.
            monthly=pad_rent_monthly() + dome / (life * MONTHS),
            entry=dome, recoverable=0.0, asset=dome,
            note=f"the building is yours; the ground is not"),
    )


def host_cases() -> tuple[HostCase, ...]:
    """What a piece of ground earns, three ways."""
    import pad_deck
    import seed_model

    pad_build = seed_model.quote().pad_cost
    infrastructure = (_declared("site_infrastructure_usd_per_pad")
                      + _declared("permit_usd_per_pad")
                      + _declared("meter_submeter_usd_per_pad"))
    running = (_declared("management_usd_per_month_per_pad") * MONTHS
               + _declared("tax_insurance_usd_per_year_per_pad")
               + _declared("meter_admin_usd_per_month") * MONTHS)
    rent = pad_rent_monthly() * MONTHS

    # A furnished short let of an equivalent small dwelling: the host builds
    # and owns the building too, and pays for turnover forever.
    nights = _declared("short_let_usd_per_night")
    turnovers = _declared("airbnb_turnovers_per_month")
    short_income = nights * 30.0 * MONTHS
    short_cost = (running
                  + short_income * _declared("airbnb_platform_fee_fraction")
                  + short_income * _declared("airbnb_damage_reserve_fraction")
                  + _declared("rental_renovation_usd_per_year")
                  + turnovers * MONTHS * 45.0)

    return (
        HostCase(
            "bare ground, unused", upfront=0.0, yearly_income=0.0,
            yearly_cost=_declared("tax_insurance_usd_per_year_per_pad"),
            note="it still costs tax and it earns nothing"),
        HostCase(
            "one serviced pad",
            upfront=pad_build + infrastructure,
            yearly_income=rent, yearly_cost=running,
            note="built once; the home on it belongs to the tenant"),
        HostCase(
            "furnish a unit and let it short",
            upfront=pad_build + infrastructure + seed_model.quote().price,
            yearly_income=short_income, yearly_cost=short_cost,
            note=f"the same ground, plus a building to own, clean "
                 f"{turnovers:.0f} times a month and renovate every year -- "
                 f"and this line is given every night of the year full, "
                 f"which nobody achieves"),
    )


def tenant_table(years: float = 10.0) -> str:
    lines = [f"{'':<30}{'per month':>12}{'at the door':>14}"
             f"{f'over {years:.0f} yr':>14}{'owned after':>14}"]
    for option in tenant_options():
        lines.append(
            f"{option.label:<30}"
            f"{'$' + format(option.monthly, ',.0f'):>12}"
            f"{'$' + format(option.entry, ',.0f'):>14}"
            f"{'$' + format(option.over(years), ',.0f'):>14}"
            f"{'$' + format(option.asset, ',.0f'):>14}")
    return "\n".join(lines)


def host_table() -> str:
    lines = [f"{'':<34}{'upfront':>11}{'a year, net':>13}{'payback':>10}"]
    for case in host_cases():
        payback = case.payback_years()
        text = "never" if payback == float("inf") else f"{payback:,.1f} yr"
        lines.append(f"{case.label:<34}"
                     f"{'$' + format(case.upfront, ',.0f'):>11}"
                     f"{'$' + format(case.yearly_net, ',.0f'):>13}"
                     f"{text:>10}")
    return "\n".join(lines)


def crossover_months() -> float:
    """When owning a dome on a pad overtakes the cheapest rental."""
    options = {o.label: o for o in tenant_options()}
    own = options["own the dome, rent the pad"]
    rent = options["apartment lease"]
    gap = rent.monthly - own.monthly
    if gap <= 0.0:
        return float("inf")
    return (own.entry - rent.entry + rent.recoverable) / gap


def validate_network() -> None:
    """Both sides have to come out ahead, or this is not an argument."""
    options = tenant_options()
    assert len(options) == 4, len(options)
    labels = [o.label for o in options]
    assert len(set(labels)) == len(labels)

    own = next(o for o in options if o.label.startswith("own the dome"))
    apartment = next(o for o in options if o.label == "apartment lease")

    # The tenant's monthly has to beat the cheapest rental, or the only
    # argument left is sentiment.
    assert own.monthly < apartment.monthly, (
        f"owning is ${own.monthly:,.0f} a month against an apartment's "
        f"${apartment.monthly:,.0f}; the chapter's argument does not hold")
    # And the entry cost has to be real, because it is the catch.
    assert own.entry > apartment.entry * 2.0, (
        "the entry cost is the honest objection and the model has lost it")

    months = crossover_months()
    assert 6.0 < months < 360.0, months

    cases = host_cases()
    pad = next(c for c in cases if c.label == "one serviced pad")
    bare = next(c for c in cases if c.label.startswith("bare ground"))
    assert pad.yearly_net > 0.0, pad
    assert bare.yearly_net < 0.0, bare
    assert pad.payback_years() < 25.0, (
        f"a pad pays back in {pad.payback_years():,.1f} years, which is not "
        "a proposition anybody accepts")

    for case in cases:
        assert case.note, case.label
        assert case.upfront >= 0.0, case.label

    assert "per month" in tenant_table()
    assert "payback" in host_table()


def main(argv: list[str] | None = None) -> int:
    import argparse

    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--check", action="store_true")
    parser.add_argument("--years", type=float, default=10.0)
    args = parser.parse_args(argv)

    validate_network()
    if args.check:
        print("network ok")
        return 0
    print("THE TENANT\n")
    print(tenant_table(args.years))
    print(f"\n  owning overtakes renting after "
          f"{crossover_months():,.0f} months\n")
    print("THE HOST\n")
    print(host_table())
    print(f"\n  a serviced pad rents for ${pad_rent_monthly():,.0f} a month")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
