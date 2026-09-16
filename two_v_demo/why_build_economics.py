"""The author's case for building this way, priced the author's way and then checked.

*Why Build This Way?* argues from a few round figures the author chose: bought space at
$100 a square foot, framing as 16 percent of it, 80 hours of hands-on shell work, a
6.5 percent thirty-year mortgage, a $25 after-tax wage and $800 of direct cost. They are
the author's, so :data:`SOURCES` marks them that way, and every figure the film derives
from them is computed here -- the $60 an hour, the 2.5 times, the $137 an hour of
payments that never have to be made.

Then each is checked against the published figures in :mod:`house_economics`, and the
film shows the checks whichever way they fall. Two help the argument: the author's
$4,800 frame is cheaper than either published rate would price it, and the typical
worker takes home less than $25 an hour. Two do not: the 2.5 times is exactly one
over the labor share and nothing more, and the house labor budget the author compared
against was 40 percent of the whole price, where the builders' survey puts all of the
building at 64 percent of it.
"""

from __future__ import annotations

from dataclasses import dataclass
from functools import lru_cache

from . import house_economics as he
from .house_economics import AUTHOR, DECIDED, Source


SOURCES: tuple[Source, ...] = (
    Source("why_usd_per_sqft", 100.0, "USD per sq ft", AUTHOR,
           "The author's price for bought space: above the average new manufactured "
           "home, well under a new site-built house."),
    Source("why_framing_share", 0.16, "of that price", AUTHOR,
           "The author's share for the framing function. NAHB's framing is 16.6% of "
           "building cost and 10.7% of a new house's price."),
    Source("why_mortgage_rate", 0.065, "a year", AUTHOR,
           "An illustrative thirty-year fixed rate."),
    Source("why_mortgage_years", 30.0, "years", AUTHOR, "The loan's term."),
    Source("why_after_tax_wage", 25.0, "USD an hour", AUTHOR,
           "An example take-home wage. The median worker keeps less; see the checks."),
    Source("why_direct_cash", 800.0, "USD", AUTHOR,
           "An example of what the shell costs in money. The fortnight's own "
           "receipts come to less; see the checks."),
    Source("why_loan", 100_000.0, "USD", AUTHOR,
           "An example mortgage, for what its interest buys."),
    Source("why_house_labor_share", 0.40, "of the house price", AUTHOR,
           "The house-labor budget the author compared against: 40% of the whole "
           "price, where the builders' survey puts all of the building at 64%."),
    Source("why_horizon_years", 30.0, "years", AUTHOR,
           "One shell a year, for as long as the mortgage would have run."),
    Source("week_hours", 40.0, "hours", DECIDED,
           "A working week, for turning the Census months into work-hours."),
)

SOURCE_BY_KEY = {source.key: source for source in SOURCES}


def value(key: str) -> float:
    return SOURCE_BY_KEY[key].value


def payments(principal: float, rate: float | None = None,
             years: float | None = None) -> float:
    """Every payment on a fixed-rate loan, added up: principal and interest, nominal."""
    rate = value("why_mortgage_rate") if rate is None else rate
    years = value("why_mortgage_years") if years is None else years
    monthly = rate / 12.0
    count = int(round(years * 12.0))
    payment = principal * monthly / (1.0 - (1.0 + monthly) ** -count)
    return payment * count


@dataclass(frozen=True)
class Case:
    """One shell, priced the author's way."""

    sqft: float
    hours: float
    usd_per_sqft: float
    framing_share: float
    labor_share: float
    wage: float
    cash: float
    loan: float
    horizon: float

    @property
    def sqft_per_hour(self) -> float:
        return self.sqft / self.hours

    @property
    def space_value(self) -> float:
        return self.sqft * self.usd_per_sqft

    @property
    def framing_value(self) -> float:
        """The framing function the shell displaces, at the author's price."""
        return self.space_value * self.framing_share

    @property
    def rate(self) -> float:
        """Production value: what each hour substitutes at today's price."""
        return self.framing_value / self.hours

    @property
    def labor_value(self) -> float:
        return self.framing_value * self.labor_share

    @property
    def labor_rate(self) -> float:
        """The framing-labor benchmark: the labor part alone, per hour of shell work."""
        return self.labor_value / self.hours

    @property
    def leverage(self) -> float:
        """Production value over the labor benchmark. Always one over the labor share:
        the hour replaces the wood as well as the work."""
        return self.rate / self.labor_rate

    @property
    def financed(self) -> float:
        """What the framing would cost in payments, carried on the mortgage."""
        return payments(self.framing_value)

    @property
    def financed_rate(self) -> float:
        """Debt-avoidance value: nominal payments never made, per hour. Not a wage."""
        return self.financed / self.hours

    @property
    def financed_leverage(self) -> float:
        return self.financed_rate / self.labor_rate

    @property
    def loan_total(self) -> float:
        return payments(self.loan)

    @property
    def loan_interest(self) -> float:
        return self.loan_total - self.loan

    @property
    def interest_sqft(self) -> float:
        """The loan's interest, as square feet at the author's price."""
        return self.loan_interest / self.usd_per_sqft

    @property
    def buy_hours(self) -> float:
        """Hours of take-home pay to buy the framing instead."""
        return self.framing_value / self.wage

    @property
    def cash_hours(self) -> float:
        """Hours of take-home pay to earn the shell's cash cost."""
        return self.cash / self.wage

    @property
    def build_hours(self) -> float:
        return self.hours + self.cash_hours

    @property
    def kept_hours(self) -> float:
        return self.buy_hours - self.build_hours

    @property
    def breakeven(self) -> float:
        """Above this take-home wage, working and buying beats building."""
        return (self.framing_value - self.cash) / self.hours

    def over_years(self, years: float) -> float:
        return self.framing_value * years

    def sqft_over_years(self, years: float) -> float:
        return self.sqft * years


@lru_cache(maxsize=1)
def case() -> Case:
    return Case(sqft=he.dome_floor_sqft(), hours=he.value("shell_hours"),
                usd_per_sqft=value("why_usd_per_sqft"),
                framing_share=value("why_framing_share"),
                labor_share=he.value("labor_share"),
                wage=value("why_after_tax_wage"), cash=value("why_direct_cash"),
                loan=value("why_loan"), horizon=value("why_horizon_years"))


@dataclass(frozen=True)
class Checks:
    """The author's figures against the published ones, whichever way they fall."""

    trailer_value: float
    """The same frame at a manufactured home's price (Census, NAHB proportions)."""
    house_value: float
    """The same frame at a new site-built house's national price (NAHB)."""
    measured_cash: float
    take_home: float
    take_home_buy_hours: float
    site_usd_per_sqft: float
    weeks: float
    work_hours: float
    house_labor: float
    author_house_labor: float

    @property
    def burn(self) -> float:
        """The survey-based house labor budget, per work-hour of the build."""
        return self.house_labor / self.work_hours

    @property
    def author_burn(self) -> float:
        return self.author_house_labor / self.work_hours


@lru_cache(maxsize=1)
def checks() -> Checks:
    frame = he.frame_value()
    weeks = round(he.value("soc_start_to_finish_months") * 52.0 / 12.0)
    work_hours = weeks * value("week_hours")
    site = he.price_total() * (1.0 - he.price_share("lot")) / he.value("nahb_finished_sqft")
    return Checks(
        trailer_value=frame.buy_trailer, house_value=frame.buy_house,
        measured_cash=frame.cash_total, take_home=he.after_tax_hourly(),
        take_home_buy_hours=case().framing_value / he.after_tax_hourly(),
        site_usd_per_sqft=site, weeks=weeks, work_hours=work_hours,
        house_labor=he.house().buckets["labor"],
        author_house_labor=he.value("house_price") * value("why_house_labor_share"))


# ----------------------------------------------------------------------
# Screens
# ----------------------------------------------------------------------

def source_lines() -> tuple[str, ...]:
    """What the case rests on, for the screen that shows it before any figure."""
    c, k = case(), checks()
    return (
        f"THE AUTHOR'S  ${c.usd_per_sqft:,.0f} a sq ft; framing "
        f"{c.framing_share * 100:.0f}% of it; {c.hours:.0f} hours of shell work",
        f"THE AUTHOR'S  {value('why_mortgage_rate') * 100:.1f}% for "
        f"{value('why_mortgage_years'):.0f} years; ${c.wage:.0f} an hour take-home; "
        f"${c.cash:,.0f} cash",
        f"PUBLISHED  new manufactured home: ${he.value('mhs_2023_usd_per_sqft'):.2f} "
        "a sq ft (Census)",
        f"PUBLISHED  new site-built house: ${k.site_usd_per_sqft:,.2f} a sq ft "
        "without land (NAHB)",
        f"PUBLISHED  framing {he.stage_share('framing') * 100:.1f}% of building cost; "
        f"median take-home ${k.take_home:.2f} an hour (BLS)",
        "So the author's figures sit on the cautious side of the published ones",
    )


def score_lines() -> tuple[str, ...]:
    """The whole case on one worksheet, last line the verdict."""
    c = case()
    years = value("why_mortgage_years")
    return (
        f"{c.sqft:.0f} sq ft of shell in {c.hours:.0f} hours: "
        f"{c.sqft_per_hour:.2f} sq ft an hour",
        f"${c.framing_value:,.0f} of commercial framing displaced",
        f"${c.rate:,.0f} an hour production value; {c.leverage:.1f}x the framing "
        "labor alone",
        f"${c.financed:,.0f} of {years:.0f}-year payments avoided: "
        f"${c.financed_rate:,.2f} an hour, not a wage",
        f"{c.kept_hours:.0f} hours of life kept, against earning ${c.wage:.0f} an "
        "hour to buy it",
        f"Worth building while your take-home is under ${c.breakeven:,.0f} an hour",
        f"One shell a year for {c.horizon:.0f} years: "
        f"${c.over_years(c.horizon):,.0f} of framing, "
        f"{c.sqft_over_years(c.horizon):,.0f} sq ft",
        f"One hour: ${c.rate:,.0f} of shelter today, ${c.financed_rate:,.0f} of "
        "payments never made",
    )


# ----------------------------------------------------------------------
# Live figures for the book-token language
# ----------------------------------------------------------------------

def token_specs() -> list[tuple[str, str, object]]:
    """(name, description, compute) for every ``{{why.*}}`` token."""
    from .book_tokens import _n, _pct

    def c():
        return case()

    def k():
        return checks()

    years = value("why_mortgage_years")
    specs = [
        ("why.net", "framing avoided, less the cash it still costs",
         lambda: _n(c().framing_value - c().cash, 0)),
        ("why.kept_weeks", "the hours kept, as working weeks",
         lambda: _n(c().kept_hours / value("week_hours"), 0)),
        ("why.hours", "the author's hands-on hours for the shell",
         lambda: _n(c().hours, 0)),
        ("why.sqft", "the shell's floor, sq ft", lambda: _n(c().sqft, 0)),
        ("why.sqft_per_hour", "square feet of shell an hour",
         lambda: f"{c().sqft_per_hour:.2f}"),
        ("why.usd_per_sqft", "the author's price for bought space, a sq ft",
         lambda: _n(c().usd_per_sqft, 0)),
        ("why.space_value", "the shell's floor at that price",
         lambda: _n(c().space_value, 0)),
        ("why.framing_pct", "the author's framing share, per cent",
         lambda: _pct(c().framing_share, 0)),
        ("why.framing_share", "the same share as a fraction",
         lambda: f"{c().framing_share:.2f}"),
        ("why.framing_value", "commercial framing the shell displaces",
         lambda: _n(c().framing_value, 0)),
        ("why.rate", "production value, dollars an hour", lambda: _n(c().rate, 0)),
        ("why.labor_pct", "labor's share of the framing, per cent",
         lambda: _pct(c().labor_share, 0)),
        ("why.labor_share", "the same share as a fraction",
         lambda: f"{c().labor_share:.1f}"),
        ("why.labor_value", "the labor inside the framing",
         lambda: _n(c().labor_value, 0)),
        ("why.labor_rate", "the framing-labor benchmark, dollars an hour",
         lambda: _n(c().labor_rate, 0)),
        ("why.leverage", "production value over the labor benchmark",
         lambda: f"{c().leverage:.1f}"),
        ("why.index", "the same as an index, benchmark 100",
         lambda: _n(c().leverage * 100.0, 0)),
        ("why.mortgage_pct", "the illustrative mortgage rate, per cent",
         lambda: f"{value('why_mortgage_rate') * 100:.1f}"),
        ("why.mortgage_years", "the mortgage's term", lambda: _n(years, 0)),
        ("why.financed", "the framing's cost, carried on the mortgage",
         lambda: _n(c().financed, 0)),
        ("why.financed_rate", "debt-avoidance value, dollars an hour",
         lambda: _n(c().financed_rate, 0)),
        ("why.financed_rate_exact", "the same to the cent",
         lambda: f"{c().financed_rate:.2f}"),
        ("why.financed_leverage", "debt-avoidance value over the labor benchmark",
         lambda: f"{c().financed_leverage:.1f}"),
        ("why.financed_index", "the same as an index, benchmark 100",
         lambda: _n(c().financed_leverage * 100.0, 0)),
        ("why.loan", "the example mortgage", lambda: _n(c().loan, 0)),
        ("why.loan_total", "every payment on it, added up",
         lambda: _n(c().loan_total, 0)),
        ("why.loan_interest", "the interest in those payments",
         lambda: _n(c().loan_interest, 0)),
        ("why.interest_sqft", "that interest as square feet at the author's price",
         lambda: _n(c().interest_sqft, 0)),
        ("why.wage", "the author's example take-home wage", lambda: _n(c().wage, 0)),
        ("why.buy_hours", "hours of that pay to buy the framing",
         lambda: _n(c().buy_hours, 0)),
        ("why.cash", "the author's example cash cost", lambda: _n(c().cash, 0)),
        ("why.cash_hours", "hours of pay to earn that cash",
         lambda: _n(c().cash_hours, 0)),
        ("why.build_hours", "building it: shell hours plus the cash's hours",
         lambda: _n(c().build_hours, 0)),
        ("why.kept_hours", "hours of life kept", lambda: _n(c().kept_hours, 0)),
        ("why.breakeven", "take-home wage above which buying wins",
         lambda: _n(c().breakeven, 0)),
        ("why.horizon", "years of one shell a year",
         lambda: _n(c().horizon, 0)),
        ("why.decade", "framing displaced in ten years",
         lambda: _n(c().over_years(10), 0)),
        ("why.two_decades", "framing displaced in twenty years",
         lambda: _n(c().over_years(20), 0)),
        ("why.lifetime", "framing displaced over the horizon",
         lambda: _n(c().over_years(c().horizon), 0)),
        ("why.lifetime_sqft", "shell built over the horizon",
         lambda: _n(c().sqft_over_years(c().horizon), 0)),
        ("why.trailer_value", "the same frame at a manufactured home's price",
         lambda: _n(k().trailer_value, 0)),
        ("why.site_usd_per_sqft", "a new site-built house a sq ft, without land",
         lambda: _n(k().site_usd_per_sqft, 0)),
        ("why.take_home_buy_hours", "hours of median take-home to buy the framing",
         lambda: _n(k().take_home_buy_hours, 0)),
        ("why.weeks", "the Census build time in weeks", lambda: _n(k().weeks, 0)),
        ("why.work_hours", "those weeks as work-hours",
         lambda: _n(k().work_hours, 0)),
        ("why.author_house_labor", "the author's house-labor budget",
         lambda: _n(k().author_house_labor, 0)),
        ("why.author_burn", "that budget per work-hour",
         lambda: f"{k().author_burn:.2f}"),
        ("why.house_labor", "the survey-based labor in the same house",
         lambda: _n(k().house_labor, 0)),
        ("why.burn", "that labor per work-hour", lambda: f"{k().burn:.2f}"),
        ("why.burn_pct", "production value against the survey-based burn rate",
         lambda: _n(c().rate / k().burn * 100.0, 0)),
    ]
    return specs


# ----------------------------------------------------------------------
# Proof
# ----------------------------------------------------------------------

def validate_why_build() -> None:
    """The author's arithmetic as stated, then every check the film makes."""
    keys = [source.key for source in SOURCES] + [source.key for source in he.SOURCES]
    assert len(keys) == len(set(keys)), "a source key is defined twice"
    for source in SOURCES:
        assert source.kind in he.KINDS and source.note.strip(), source.key

    c = case()
    # The figures the author's own worked example states, reproduced.
    assert abs(c.framing_value - 4_800.0) < 1e-6, c.framing_value
    assert abs(c.rate - 60.0) < 1e-9, c.rate
    assert abs(c.labor_rate - 24.0) < 1e-9, c.labor_rate
    assert abs(c.financed - 10_922.0) < 1.0, c.financed
    assert abs(c.financed_rate - 136.53) < 0.01, c.financed_rate
    assert abs(c.loan_total - 227_544.0) < 2.0, c.loan_total
    assert abs(c.kept_hours - 80.0) < 1e-9, c.kept_hours
    assert abs(c.breakeven - 50.0) < 1e-9, c.breakeven
    # A textbook check on the payment formula: $100,000 at 6.5% over 30 years is
    # $632.07 a month.
    assert abs(payments(100_000.0) / 360.0 - 632.07) < 0.01
    # The leverage is exactly one over the labor share -- the film says so.
    assert abs(c.leverage - 1.0 / c.labor_share) < 1e-12

    k = checks()
    # The checks the film states, in the direction it states them.
    assert c.framing_value < k.trailer_value < k.house_value, (
        c.framing_value, k.trailer_value, k.house_value)
    assert k.take_home < c.wage, (k.take_home, c.wage)
    assert k.measured_cash < c.cash, (k.measured_cash, c.cash)
    assert k.burn < k.author_burn, (k.burn, k.author_burn)
    assert abs(k.author_burn - 60.61) < 0.01, k.author_burn


if __name__ == "__main__":
    validate_why_build()
    for name, _describe, compute in token_specs():
        print(f"{name:<26} {compute()}")
