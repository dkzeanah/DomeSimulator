"""A house's money and time, and what a fortnight of one person's work is worth against it.

The films' dome is framed from two trees in two weeks. This module prices that fortnight
against the two things a buyer could pay for instead: a new site-built house and a new
manufactured home. Nothing here is typed onto a screen. Each figure is computed from one
of four kinds of number, and :data:`SOURCES` says which kind, with where it came from:

* **published** -- a survey or statistic, cited (NAHB, Census, BLS, TimberMart-South);
* **author** -- the author's own round figures: a $200,000 house, a $100,000 trailer,
  40% of construction cost as labor;
* **decided** -- a choice this model makes and says so (a median earner's tax
  bracket);
* **estimated** -- a guess with its reason (a dealer markup, how much a curve slows
  finishing), shown on screen as a guess.

Three things the numbers turned up that the argument has to live with:

**Labor is not most of what a new house costs.** Even taking the author's 40% of
construction cost, labor is about a quarter of the sale price; land, materials, fees and
the builder's and seller's share are the rest. At the 2021 lumber peak it is less.

**The fortnight is the frame, not the house.** It fells, bucks, rips, jigs and raises a
frame. Everything after that still has to be done by somebody.

**Most of the saving is not the shape.** The biggest pieces are the builder's share and
the labor, which anyone building their own house of any shape keeps. The shape's own
contribution -- less skin, less foundation, shorter runs from a central column -- is real
and computed here, and it is the smaller part.
"""

from __future__ import annotations

import math
from dataclasses import dataclass
from functools import lru_cache

from . import book_math as bm


PUBLISHED, AUTHOR, DECIDED, ESTIMATED = "published", "author", "decided", "estimated"
KINDS = (PUBLISHED, AUTHOR, DECIDED, ESTIMATED)


@dataclass(frozen=True)
class Source:
    """One number the model rests on, and why it is believed."""

    key: str
    value: float
    units: str
    kind: str
    note: str
    cite: str = ""


NAHB_2024 = ("NAHB, Cost of Constructing a Home 2024 (Eric Lynch, 20 Jan 2025), Table 1. "
             "41 usable builder responses; NAHB warns the sample is not representative.")
SOC_2024 = ("U.S. Census Bureau Survey of Construction, completions in 2024, via NAHB "
            "Eye on Housing, Sept 2025.")
BLS_2025 = "BLS Occupational Outlook Handbook and OEWS, May 2025 medians."

SOURCES: tuple[Source, ...] = (
    # -- time --------------------------------------------------------------
    Source("soc_start_to_finish_months", 7.6, "months", PUBLISHED,
           "Average time from start to completion, single-family homes finished in "
           "2024. The Census publishes an average, not a median.", SOC_2024),
    Source("soc_owner_built_months", 15.1, "months", PUBLISHED,
           "Authorization to completion for houses built by their owners.", SOC_2024),
    Source("schedule_weeks", 20.0, "weeks", PUBLISHED,
           "One builder-style week-by-week schedule, used only for its proportions.",
           "The Plan Collection, 'What to expect when you're building a home'."),
    # -- the new house ------------------------------------------------------
    Source("nahb_sale_price", 665_298.0, "USD", PUBLISHED,
           "Average sale price in the survey; every share below comes from its table.",
           NAHB_2024),
    Source("nahb_finished_sqft", 2_647.0, "sq ft", PUBLISHED,
           "Average finished floor area in the same survey.", NAHB_2024),
    Source("nahb_2019_sale_price", 485_128.0, "USD", PUBLISHED,
           "Average sale price in NAHB's 2019 survey, the last before the lumber spike.",
           "NAHB, Cost of Constructing a Home 2019 (Carmel Ford, 2 Jan 2020)."),
    Source("lumber_2021_added", 35_872.0, "USD", PUBLISHED,
           "What the spring-2021 softwood lumber prices added to the price of an "
           "average new single-family home.",
           "NAHB, April 2021, as reported by Atlanta Agent Magazine (7 May 2021) and CNBC."),
    Source("lumber_flcp_peak", 1_500.0, "USD per 1,000 board feet", PUBLISHED,
           "Random Lengths framing lumber composite price, topped in May 2021: the "
           "highest on record, and a record even after inflation.",
           "NAHB Eye on Housing, Feb 2022."),
    # -- the manufactured home ------------------------------------------------
    Source("mhs_2023_usd_per_sqft", 86.62, "USD per sq ft", PUBLISHED,
           "Average new manufactured home, 2023, land excluded. Dealers are told to "
           "include their set-up cost in the price they report.",
           "Census Manufactured Housing Survey via NAHB Eye on Housing, Apr 2025; "
           "MHS methodology."),
    Source("mhs_2023_single_price", 84_800.0, "USD", PUBLISHED,
           "Average single-section home in 2023, for scale: a $100,000 home is a large "
           "single or a small double.", "Census MHS via NAHB Eye on Housing, Oct 2024."),
    Source("mh_materials_musd", 3_847.0, "million USD", PUBLISHED,
           "Cost of materials, manufactured home factories (NAICS 321991), 2002.",
           "2002 Economic Census via Encyclopedia.com, NAICS 321991. The newest "
           "material and payroll split found; it is old."),
    Source("mh_payroll_musd", 1_407.4, "million USD", PUBLISHED,
           "Payroll, the same factories, same year.", "2002 Economic Census, as above."),
    Source("mh_shipments_musd", 6_695.0, "million USD", PUBLISHED,
           "Value of shipments, the same factories, same year.",
           "2002 Economic Census, as above."),
    Source("mh_lumber_musd", 330.6, "million USD", PUBLISHED,
           "Dressed lumber bought by those factories, the largest single material.",
           "2002 Economic Census, as above."),
    # -- labor ------------------------------------------------------------------
    Source("craftsman_labor_share", 0.50, "of direct cost", PUBLISHED,
           "Labor across all trades in a new house, from the Craftsman estimator.",
           "Construction Physics, 'Construction Cost Breakdown and Partial "
           "Industrialization'."),
    Source("labor_site_built", 0.65, "of item cost", ESTIMATED,
           "Midpoint of the 60-70% labor given for trades built on site: framing, "
           "concrete, drywall, painting, plumbing.", "Construction Physics, as above."),
    Source("labor_prefab", 0.15, "of item cost", ESTIMATED,
           "Midpoint of the 10-20% given for items that arrive finished: cabinets, "
           "appliances, lighting, windows.", "Construction Physics, as above."),
    Source("labor_mixed", 0.40, "of item cost", ESTIMATED,
           "Between the two, for costly materials installed on site: siding, roofing, "
           "flooring, HVAC."),
    # -- wages and tax ------------------------------------------------------
    Source("wage_all_workers", 50_980.0, "USD a year", PUBLISHED,
           "Median annual wage, all workers.", BLS_2025),
    Source("wage_carpenters", 60_580.0, "USD a year", PUBLISHED,
           "Median annual wage, carpenters.", BLS_2025),
    Source("wage_electricians", 63_190.0, "USD a year", PUBLISHED,
           "Median annual wage, electricians.", BLS_2025),
    Source("wage_plumbers", 63_800.0, "USD a year", PUBLISHED,
           "Median annual wage, plumbers, pipefitters and steamfitters.", BLS_2025),
    Source("wage_hvac", 61_010.0, "USD a year", PUBLISHED,
           "Median annual wage, heating, air-conditioning and refrigeration mechanics.",
           BLS_2025),
    Source("wage_drywall", 59_780.0, "USD a year", PUBLISHED,
           "Median annual wage, drywall and ceiling tile installers and tapers.",
           BLS_2025),
    Source("wage_roofers", 55_440.0, "USD a year", PUBLISHED,
           "Median annual wage, roofers.", BLS_2025),
    Source("wage_masonry", 58_270.0, "USD a year", PUBLISHED,
           "Median annual wage, masonry workers, which includes concrete.", BLS_2025),
    Source("wage_laborers", 46_680.0, "USD a year", PUBLISHED,
           "Median annual wage, construction laborers and helpers.", BLS_2025),
    Source("hours_per_year", 2_080.0, "hours", PUBLISHED,
           "The hours BLS divides by to turn an annual wage into an hourly one.",
           BLS_2025),
    Source("fica_rate", 0.0765, "of wages", PUBLISHED,
           "Social Security and Medicare withheld from every paycheck dollar.",
           "IRS."),
    Source("federal_bracket", 0.12, "of the last dollar", DECIDED,
           "The federal bracket a median earner's last dollar falls in. State tax is "
           "left out, which makes the take-home figure generous."),
    # -- the trees, the fuel ------------------------------------------------
    Source("stumpage_pine_usd_per_ton", 23.23, "USD per ton", PUBLISHED,
           "South-wide pine sawtimber stumpage, fourth quarter 2025: what a standing "
           "tree sells for.", "TimberMart-South via Southern Ag Today, Jan 2026."),
    Source("green_pine_lb_per_ft3", 55.0, "lb per cubic foot", ESTIMATED,
           "What green pine weighs, for turning the two trunks into tons."),
    Source("gas_usd_per_gallon", 2.98, "USD per gallon", PUBLISHED,
           "US average regular gasoline, 1 Dec 2025.", "EIA Gasoline and Diesel Fuel "
           "Update."),
    # -- the author's figures ------------------------------------------------
    Source("house_price", 200_000.0, "USD", AUTHOR,
           "The author's standard house, split in NAHB's shares."),
    Source("trailer_price", 100_000.0, "USD", AUTHOR,
           "The author's manufactured home."),
    Source("labor_share", 0.40, "of construction cost", AUTHOR,
           "The author's labor share. The item-by-item estimate here gives a little "
           "more, Craftsman about half; 40% is the conservative of the three."),
    Source("shell_hours", 80.0, "hours", AUTHOR,
           "The author's hands-on hours for the shell, felling to raising. Only the "
           "ripping was timed; the rest is the author's count."),
    # -- estimated ---------------------------------------------------------------
    Source("dealer_markup", 0.25, "over the factory invoice", ESTIMATED,
           "Buying guides give 20 to 35 percent."),
    Source("run_share", 0.35, "of rough-in cost", ESTIMATED,
           "The part of plumbing, wiring and ductwork cost that grows with the length "
           "of the runs. Fixtures, panels and equipment do not."),
    Source("curve_penalty", 0.25, "extra per square foot", ESTIMATED,
           "How much more a square foot of triangles costs to sheathe, skin, insulate, "
           "board and paint than a flat wall. Nobody has measured this."),
    Source("lumber_tripled", 3.0, "times", PUBLISHED,
           "NAHB: lumber prices tripled in the twelve months to April 2021.",
           "NAHB via Atlanta Agent Magazine, 7 May 2021."),
)

SOURCE_BY_KEY = {source.key: source for source in SOURCES}


def value(key: str) -> float:
    return SOURCE_BY_KEY[key].value


# ----------------------------------------------------------------------
# NAHB 2024, Table 1, as published
# ----------------------------------------------------------------------

PRICE_PARTS: tuple[tuple[str, str, float], ...] = (
    ("lot", "Finished lot", 91_057.0),
    ("construction", "Construction", 428_215.0),
    ("financing", "Financing", 10_220.0),
    ("overhead", "Overhead and general expenses", 38_248.0),
    ("marketing", "Marketing", 5_633.0),
    ("commission", "Sales commission", 18_955.0),
    ("profit", "Profit", 72_971.0),
)
"""The sale price, by who gets it. The parts add to $1 more than the published total,
which is NAHB's rounding; the shares here are taken over the parts."""

MARGIN_PARTS = ("financing", "overhead", "marketing", "commission", "profit")
"""What a buyer pays a builder beyond the land and the building itself."""

STAGES: tuple[tuple[str, str], ...] = (
    ("site", "Site work: permits, fees, design"),
    ("foundations", "Foundations"),
    ("framing", "Framing"),
    ("exterior", "Exterior: siding, roof, windows"),
    ("rough_ins", "Plumbing, electrical, HVAC"),
    ("interior", "Interior finishes"),
    ("final", "Final steps: yard, driveway"),
    ("other", "Other"),
)
STAGE_NAME = dict(STAGES)

STAGE_TOTALS = {"site": 32_719.0, "foundations": 44_748.0, "framing": 70_982.0,
                "exterior": 57_510.0, "rough_ins": 82_319.0, "interior": 103_391.0,
                "final": 27_710.0, "other": 8_835.0}
"""Published stage subtotals, kept only to check the items against."""

FEE, SITE_BUILT, MIXED, PREFAB = "fee", "site-built", "mixed", "prefab"


@dataclass(frozen=True)
class Item:
    """One line of NAHB's construction cost table."""

    key: str
    stage: str
    name: str
    dollars: float
    work: str
    """How it is built: a fee, built on site, mixed, or arriving finished."""
    dome: str
    """What the dome method does to it: fee, perimeter, frame, skin, runs or same."""


ITEMS: tuple[Item, ...] = (
    Item("permits", "site", "Building permit fees", 7_640, FEE, "fee"),
    Item("impact", "site", "Impact fee", 6_367, FEE, "fee"),
    Item("water_sewer", "site", "Water and sewer fees, inspections", 6_260, FEE, "fee"),
    Item("design", "site", "Architecture, engineering", 6_480, FEE, "fee"),
    Item("site_other", "site", "Other site work", 5_972, FEE, "fee"),
    Item("excavation", "foundations",
         "Excavation, foundation, concrete, retaining walls, backfill", 43_002,
         SITE_BUILT, "perimeter"),
    Item("foundation_other", "foundations", "Other foundation", 1_747, MIXED,
         "perimeter"),
    Item("frame", "framing", "Framing, including roof", 49_763, SITE_BUILT, "frame"),
    Item("trusses", "framing", "Trusses", 12_903, PREFAB, "frame"),
    Item("sheathing", "framing", "Sheathing", 6_513, MIXED, "skin"),
    Item("metal", "framing", "General metal, steel", 1_718, PREFAB, "frame"),
    Item("framing_other", "framing", "Other framing", 85, MIXED, "frame"),
    Item("wall_finish", "exterior", "Exterior wall finish", 24_450, MIXED, "skin"),
    Item("roofing", "exterior", "Roofing", 16_732, MIXED, "skin"),
    Item("windows", "exterior", "Windows and doors", 15_990, PREFAB, "same"),
    Item("exterior_other", "exterior", "Other exterior", 338, MIXED, "same"),
    Item("plumbing", "rough_ins", "Plumbing, except fixtures", 27_180, SITE_BUILT,
         "runs"),
    Item("electrical", "rough_ins", "Electrical, except fixtures", 27_383, SITE_BUILT,
         "runs"),
    Item("hvac", "rough_ins", "HVAC", 26_938, MIXED, "runs"),
    Item("rough_other", "rough_ins", "Other rough-ins", 817, MIXED, "runs"),
    Item("insulation", "interior", "Insulation", 6_992, MIXED, "skin"),
    Item("drywall", "interior", "Drywall", 13_962, SITE_BUILT, "skin"),
    Item("trim", "interior", "Interior trims, doors, mirrors", 12_920, MIXED, "same"),
    Item("painting", "interior", "Painting", 11_150, SITE_BUILT, "skin"),
    Item("lighting", "interior", "Lighting", 5_392, PREFAB, "same"),
    Item("cabinets", "interior", "Cabinets, countertops", 19_056, PREFAB, "same"),
    Item("appliances", "interior", "Appliances", 7_499, PREFAB, "same"),
    Item("flooring", "interior", "Flooring", 15_388, MIXED, "same"),
    Item("fixtures", "interior", "Plumbing fixtures", 7_922, PREFAB, "same"),
    Item("fireplace", "interior", "Fireplace", 2_378, PREFAB, "same"),
    Item("interior_other", "interior", "Other interior", 732, MIXED, "same"),
    Item("landscaping", "final", "Landscaping", 9_269, MIXED, "same"),
    Item("outdoor", "final", "Outdoor structures", 4_722, SITE_BUILT, "same"),
    Item("driveway", "final", "Driveway", 9_635, MIXED, "same"),
    Item("cleanup", "final", "Clean up", 3_183, SITE_BUILT, "same"),
    Item("final_other", "final", "Other final steps", 902, MIXED, "same"),
    Item("other", "other", "Other", 8_835, MIXED, "same"),
)
ITEM_BY_KEY = {item.key: item for item in ITEMS}

FACTORY_STAGES = ("framing", "exterior", "rough_ins", "interior", "other")
"""The stages a manufactured-home factory builds. Site work, the foundation and the yard
are not in a trailer's price."""


def price_total() -> float:
    return sum(dollars for _, _, dollars in PRICE_PARTS)


def price_share(key: str) -> float:
    return dict((k, d) for k, _, d in PRICE_PARTS)[key] / price_total()


def margin_share() -> float:
    """The builder's and seller's share, as a fraction of construction cost."""
    parts = dict((k, d) for k, _, d in PRICE_PARTS)
    return sum(parts[k] for k in MARGIN_PARTS) / parts["construction"]


def construction_total() -> float:
    return sum(item.dollars for item in ITEMS)


def item_share(item: Item) -> float:
    return item.dollars / construction_total()


def stage_share(stage: str) -> float:
    return sum(item_share(i) for i in ITEMS if i.stage == stage)


# ----------------------------------------------------------------------
# Rounding that keeps a sum a sum
# ----------------------------------------------------------------------

def split_round(parts: dict[str, float], unit: float) -> dict[str, int]:
    """Round every part to ``unit`` so the rounded parts add to the rounded total.

    A tally that says 27,400 + 128,700 + 33,400 + 10,500 = 200,000 has to be true on
    screen, and rounding each part on its own does not guarantee that. The largest
    remainders take the leftover units.
    """
    total = round(sum(parts.values()) / unit)
    floors = {k: math.floor(v / unit) for k, v in parts.items()}
    short = int(total - sum(floors.values()))
    order = sorted(parts, key=lambda k: parts[k] / unit - floors[k], reverse=True)
    for key in order[:max(0, short)]:
        floors[key] += 1
    return {k: int(v * unit) for k, v in floors.items()}


# ----------------------------------------------------------------------
# Where a house's time goes
# ----------------------------------------------------------------------

SCHEDULE: tuple[tuple[str, int, int, str], ...] = (
    ("Site prep, excavation, footings", 1, 1, "foundations"),
    ("Foundation", 2, 3, "foundations"),
    ("Framing", 4, 5, "framing"),
    ("Plumbing, electrical, HVAC rough-in", 6, 7, "rough_ins"),
    ("Insulation and drywall", 7, 8, "interior"),
    ("Flooring, trim, paint", 9, 11, "interior"),
    ("Exterior facade", 12, 13, "exterior"),
    ("Fixtures, appliances, finishes", 14, 14, "interior"),
    ("Driveway, walkways, exterior doors", 15, 15, "final"),
    ("Interior clean-up", 16, 16, "final"),
    ("Landscaping", 17, 17, "final"),
    ("Final inspection", 18, 18, "closing"),
    ("Walk-through", 19, 19, "closing"),
    ("Closing", 20, 20, "closing"),
)
"""The builder's week-by-week schedule, and the NAHB stage each phase belongs to.
Weeks 6-7 and 7-8 overlap; the shared week is split between them."""

TIME_ORDER = ("foundations", "framing", "rough_ins", "interior", "exterior", "final",
              "closing")
TIME_NAME = {"foundations": "Ground and foundation", "framing": "Framing",
             "rough_ins": "Pipes, wires, ducts", "interior": "Inside finishes",
             "exterior": "Outside finishes", "final": "Driveway, yard, clean-up",
             "closing": "Inspection and closing"}


def stage_weeks() -> dict[str, float]:
    weeks = {stage: 0.0 for stage in TIME_ORDER}
    last = max(row[2] for row in SCHEDULE)
    for week in range(1, last + 1):
        active = [row for row in SCHEDULE if row[1] <= week <= row[2]]
        for row in active:
            weeks[row[3]] += 1.0 / len(active)
    return weeks


def time_split() -> tuple[tuple[str, float, float, float], ...]:
    """(stage, schedule weeks, share of the build, months at the Census average)."""
    weeks = stage_weeks()
    total = sum(weeks.values())
    months = value("soc_start_to_finish_months")
    return tuple((stage, weeks[stage], weeks[stage] / total,
                  weeks[stage] / total * months) for stage in TIME_ORDER)


def time_share(stage: str) -> float:
    return next(share for s, _, share, _ in time_split() if s == stage)


# ----------------------------------------------------------------------
# Labor inside the construction cost
# ----------------------------------------------------------------------

def item_labor_share() -> float:
    """Labor as a share of construction cost, item by item, before any scaling."""
    fraction = {FEE: 0.0, SITE_BUILT: value("labor_site_built"),
                MIXED: value("labor_mixed"), PREFAB: value("labor_prefab")}
    return sum(item_share(i) * fraction[i.work] for i in ITEMS)


def labor_fraction(item: Item, overall: float | None = None) -> float:
    """The item's labor fraction, scaled so the whole house matches ``overall``.

    The item estimates keep their relative sizes -- drywall is mostly labor, an
    appliance mostly not -- and are scaled together until the house as a whole carries
    the labor share asked for, which by default is the author's.
    """
    overall = value("labor_share") if overall is None else overall
    fraction = {FEE: 0.0, SITE_BUILT: value("labor_site_built"),
                MIXED: value("labor_mixed"), PREFAB: value("labor_prefab")}
    return fraction[item.work] * overall / item_labor_share()


# ----------------------------------------------------------------------
# The author's $200,000 house
# ----------------------------------------------------------------------

BUCKETS = ("materials", "labor", "fees", "land", "builder", "selling")
BUCKET_NAME = {"materials": "materials", "labor": "labor",
               "fees": "permits, fees, design", "land": "land",
               "builder": "builder's overhead, profit",
               "selling": "selling, financing"}


@dataclass(frozen=True)
class HouseSplit:
    price: float
    parts: dict
    """Price by who gets it, NAHB's shares."""
    buckets: dict
    """Price by what it pays for: materials, labor, fees, land, builder, selling."""

    @property
    def construction(self) -> float:
        return self.parts["construction"]

    @property
    def sqft(self) -> float:
        """How much new house this buys at the survey's national average."""
        return self.price / (value("nahb_sale_price") / value("nahb_finished_sqft"))

    def share(self, bucket: str) -> float:
        return self.buckets[bucket] / self.price


def house(price: float | None = None, peak: bool = False) -> HouseSplit:
    """A new house in NAHB's shares; ``peak`` prices its lumber at the 2021 high.

    At the peak NAHB found lumber added $35,872 to an average new home whose price in
    the last survey before the spike was $485,128. That premium, as a share of price, is
    added to this house's materials and to its price, all of it counted as material --
    the reading that makes materials as large as the record allows.
    """
    price = value("house_price") if price is None else price
    parts = {key: price * price_share(key) for key, _, _ in PRICE_PARTS}
    construction = parts["construction"]
    labor = sum(construction * item_share(i) * labor_fraction(i) for i in ITEMS)
    fees = sum(construction * item_share(i) for i in ITEMS if i.work == FEE)
    buckets = {
        "materials": construction - labor - fees,
        "labor": labor,
        "fees": fees,
        "land": parts["lot"],
        "builder": parts["overhead"] + parts["profit"],
        "selling": parts["commission"] + parts["marketing"] + parts["financing"],
    }
    if peak:
        added = price * lumber_premium_share()
        buckets["materials"] += added
        price += added
    return HouseSplit(price=price, parts=parts, buckets=buckets)


def lumber_premium_share() -> float:
    """What the 2021 peak added, as a share of an average new home's price."""
    return value("lumber_2021_added") / value("nahb_2019_sale_price")


def framing_dollars(price: float | None = None) -> dict[str, float]:
    """The framing stage of the author's house, item by item."""
    split = house(price)
    return {item.key: split.construction * item_share(item)
            for item in ITEMS if item.stage == "framing"}


# ----------------------------------------------------------------------
# The author's $100,000 manufactured home
# ----------------------------------------------------------------------

@dataclass(frozen=True)
class TrailerSplit:
    price: float
    dealer: float
    materials: float
    payroll: float
    factory_other: float
    peak_materials_added: float

    @property
    def invoice(self) -> float:
        return self.materials + self.payroll + self.factory_other

    @property
    def production(self) -> float:
        """What the factory spends building it: materials and payroll."""
        return self.materials + self.payroll

    @property
    def sqft(self) -> float:
        return self.price / value("mhs_2023_usd_per_sqft")


def trailer(price: float | None = None) -> TrailerSplit:
    """A new manufactured home: the dealer's share, then the factory's.

    The factory's split is the 2002 Economic Census for manufactured home plants, the
    newest published at that detail. The dealer's share is an estimate from buying
    guides. The Census price already includes the dealer's set-up, so nothing is added
    for it.
    """
    price = value("trailer_price") if price is None else price
    markup = value("dealer_markup")
    invoice = price / (1.0 + markup)
    shipments = value("mh_shipments_musd")
    materials = invoice * value("mh_materials_musd") / shipments
    payroll = invoice * value("mh_payroll_musd") / shipments
    lumber = materials * value("mh_lumber_musd") / value("mh_materials_musd")
    return TrailerSplit(price=price, dealer=price - invoice, materials=materials,
                        payroll=payroll, factory_other=invoice - materials - payroll,
                        peak_materials_added=lumber * (value("lumber_tripled") - 1.0))


# ----------------------------------------------------------------------
# What the dome method does to each item
# ----------------------------------------------------------------------

@lru_cache(maxsize=1)
def geometry_ratios() -> dict[str, float]:
    """Dome against box for the same floor, from the same model the housing case uses.

    ``al_build`` prices the box-and-dome comparisons in the presenter's housing case;
    reading its quantities here means a film and a presentation cannot disagree about
    how much skin or framing the shape saves.
    """
    import al_build as ab

    floor = dome_floor_sqft()
    width = math.sqrt(floor / 1.3)
    box = ab.box_shell_quantities(width, floor / width, ab.COMPARE_HOME_WALL_FT)
    dome = ab.dome_shell_quantities(ab._solve_dome_radius(floor, 2, "floor_sf"), 2)
    radius_ft = math.sqrt(floor / math.pi)
    box_perimeter = 2.0 * (width + floor / width)
    circle_perimeter = 2.0 * math.pi * radius_ft
    # Runs: every outlet on the wall served from the service point. A box's panel sits
    # on one wall and its runs follow the walls, a quarter of the way round on average;
    # the dome's column is at the centre and every run is one radius.
    box_run = box_perimeter / 4.0
    return {
        "framing": dome["framing_lf"] / box["framing_lf"],
        "skin": dome["cladding_sf"] / box["cladding_sf"],
        "perimeter": circle_perimeter / box_perimeter,
        "runs": radius_ft / box_run,
        "box_framing_lf": box["framing_lf"], "dome_framing_lf": dome["framing_lf"],
        "box_skin_sqft": box["cladding_sf"], "dome_skin_sqft": dome["cladding_sf"],
        "box_perimeter_ft": box_perimeter, "dome_perimeter_ft": circle_perimeter,
        "box_run_ft": box_run, "dome_run_ft": radius_ft,
    }


def dome_factor(item: Item) -> float:
    """How much of this item the dome still needs, against a box of the same floor."""
    ratio = geometry_ratios()
    if item.dome == "perimeter":
        return ratio["perimeter"]
    if item.dome == "skin":
        return ratio["skin"] * (1.0 + value("curve_penalty"))
    if item.dome == "runs":
        return 1.0 - value("run_share") * (1.0 - ratio["runs"])
    if item.dome == "frame":
        return 0.0          # the fortnight replaces it; priced on its own below
    return 1.0              # fees, fixtures, windows, floors: same in any shape


def dome_floor_sqft() -> float:
    from .book_tokens import WORKED_A_FLOOR_SQFT
    return WORKED_A_FLOOR_SQFT


# ----------------------------------------------------------------------
# The fortnight's frame, priced
# ----------------------------------------------------------------------

@dataclass(frozen=True)
class FrameValue:
    buy_house: float
    """The frame for this floor, bought at the national rate with the builder's share."""
    buy_trailer: float
    """The same frame at a manufactured home's rate, dealer and factory share in."""
    hours: float
    cash: dict

    @property
    def cash_total(self) -> float:
        return sum(self.cash.values())

    @property
    def saved_house(self) -> float:
        return self.buy_house - self.cash_total

    @property
    def saved_trailer(self) -> float:
        return self.buy_trailer - self.cash_total

    @property
    def rate_house(self) -> float:
        return self.saved_house / self.hours

    @property
    def rate_trailer(self) -> float:
        return self.saved_trailer / self.hours


def two_trees_tons() -> float:
    """What the two usable trunks weigh, green."""
    plan = bm.BOOK_TREE
    trees = bm.design_first_for_floor(dome_floor_sqft()).whole_trees_needed
    cubic_ft = plan.solid_bf * 144.0 / 1728.0 * trees
    return cubic_ft * value("green_pine_lb_per_ft3") / 2000.0


def frame_value() -> FrameValue:
    """The fortnight against buying the frame it produces.

    The frame is NAHB's framing stage without the sheathing, which the dome still buys
    and which is priced with the rest of the skin. The cash is everything the fortnight
    spends: the saw, the fuel, the hardware, and the two trees at what a timber buyer
    would have paid for them standing -- because a tree on your own land is not free,
    it is just already paid for.
    """
    floor = dome_floor_sqft()
    frame_share = sum(item_share(i) for i in ITEMS if i.dome == "frame")
    per_sqft = construction_total() / value("nahb_finished_sqft")
    buy_house = frame_share * per_sqft * floor * (1.0 + margin_share())
    buy_trailer = trailer_item_rate(frame_items=True) * floor
    from .dome_costing import PRICE
    fuel = bm.ripping_fuel()
    cash = {
        "saw": bm.declared("saw_price_usd"),
        "fuel": fuel.gallons_high * value("gas_usd_per_gallon"),
        "trees": two_trees_tons() * value("stumpage_pine_usd_per_ton"),
        "hardware": PRICE["hardware"],
    }
    hours = value("shell_hours")
    return FrameValue(buy_house=buy_house, buy_trailer=buy_trailer, hours=hours,
                      cash=cash)


def trailer_item_rate(frame_items: bool = False, item: Item | None = None) -> float:
    """Retail dollars per square foot a manufactured home spends on some items.

    No survey splits a manufactured home by trade, so its production cost is shared out
    in the site builder's proportions over the stages a factory builds. That is an
    assumption, and it is flagged wherever the result is shown.
    """
    split = trailer()
    production_per_sqft = split.production / split.sqft
    factory_total = sum(i.dollars for i in ITEMS if i.stage in FACTORY_STAGES)
    if frame_items:
        dollars = sum(i.dollars for i in ITEMS if i.dome == "frame")
    elif item is not None:
        dollars = item.dollars if item.stage in FACTORY_STAGES else 0.0
    else:
        dollars = factory_total
    return production_per_sqft * dollars / factory_total * (split.price / split.production)


# ----------------------------------------------------------------------
# Every item, for the dome's floor
# ----------------------------------------------------------------------

@dataclass(frozen=True)
class Line:
    """One NAHB item, bought for the dome's floor, against doing it the dome way."""

    item: Item
    buy: float
    """Bought, national rate, builder's share in."""
    base: float
    """The same at the builder's cost."""
    factor: float
    labor_fraction: float
    cash: float
    """What the dome way still pays in money."""

    @property
    def saved(self) -> float:
        return self.buy - self.cash

    @property
    def margin(self) -> float:
        return self.buy - self.base

    @property
    def shape(self) -> float:
        return self.base * (1.0 - self.factor) if self.item.dome != "frame" else 0.0

    @property
    def labor(self) -> float:
        if self.item.dome == "frame":
            return self.base * self.labor_fraction
        return self.base * self.factor * self.labor_fraction

    @property
    def trees(self) -> float:
        """Lumber from your own trees instead of the yard, less what the method costs."""
        if self.item.dome != "frame":
            return 0.0
        return self.base * (1.0 - self.labor_fraction) - self.cash


def lines() -> tuple[Line, ...]:
    floor = dome_floor_sqft()
    per_sqft = construction_total() / value("nahb_finished_sqft")
    frame = frame_value()
    frame_base = sum(i.dollars for i in ITEMS if i.dome == "frame")
    rows = []
    for item in ITEMS:
        base = item_share(item) * per_sqft * floor
        factor = dome_factor(item)
        labor = labor_fraction(item)
        if item.dome == "frame":
            # The fortnight's cash, shared over the frame items by their size.
            cash = frame.cash_total * item.dollars / frame_base
        else:
            cash = base * factor * (1.0 - labor)
        rows.append(Line(item, base * (1.0 + margin_share()), base, factor, labor, cash))
    return tuple(rows)


def after_tax_hourly() -> float:
    """What a median worker takes home from one more hour."""
    hourly = value("wage_all_workers") / value("hours_per_year")
    return hourly * (1.0 - value("federal_bracket") - value("fica_rate"))


def hourly(key: str) -> float:
    return value(key) / value("hours_per_year")


@dataclass(frozen=True)
class Stack:
    buy: float
    cash: float
    margin: float
    labor: float
    trees: float
    shape: float
    shape_parts: dict
    unchanged: float

    @property
    def saved(self) -> float:
        return self.buy - self.cash


def stack() -> Stack:
    """The whole floor: bought, against the dome way, the saving by where it comes from."""
    rows = lines()
    parts: dict[str, float] = {}
    for row in rows:
        if row.shape:
            parts[row.item.dome] = parts.get(row.item.dome, 0.0) + row.shape
    unchanged = sum(r.base for r in rows if r.item.dome in ("same", "fee"))
    return Stack(buy=sum(r.buy for r in rows), cash=sum(r.cash for r in rows),
                 margin=sum(r.margin for r in rows), labor=sum(r.labor for r in rows),
                 trees=sum(r.trees for r in rows), shape=sum(r.shape for r in rows),
                 shape_parts=parts, unchanged=unchanged / sum(r.base for r in rows))


def stage_lines() -> tuple[tuple[str, float, float, float], ...]:
    """(stage, buy, dome cash, saved) for the dome's floor, stage by stage."""
    rows = lines()
    out = []
    for stage, _name in STAGES:
        mine = [r for r in rows if r.item.stage == stage]
        out.append((stage, sum(r.buy for r in mine), sum(r.cash for r in mine),
                    sum(r.saved for r in mine)))
    return tuple(out)


def trailer_floor_price() -> float:
    """The dome's floor at a manufactured home's average price per square foot."""
    return value("mhs_2023_usd_per_sqft") * dome_floor_sqft()


def dome_cash_factory_scope() -> float:
    """The dome way's cash on only what a trailer's price covers: no site, footing, yard."""
    return sum(r.cash for r in lines() if r.item.stage in FACTORY_STAGES)


# ----------------------------------------------------------------------
# Screens
# ----------------------------------------------------------------------

def source_lines() -> tuple[str, ...]:
    """The table the house figures rest on, for the screen that shows it first."""
    split = house()
    return (
        "PUBLISHED  NAHB 2024 cost survey: who gets a house's price, "
        "and 37 line items of building it (41 builders; not representative)",
        f"PUBLISHED  Census: {value('soc_start_to_finish_months'):.1f} months, start "
        f"to finish; BLS wages, May 2025",
        f"PUBLISHED  Lumber peak: ${value('lumber_flcp_peak'):,.0f} per 1,000 bd ft; "
        f"+${value('lumber_2021_added'):,.0f} on an average home",
        f"PUBLISHED  Manufactured homes: ${value('mhs_2023_usd_per_sqft'):.2f} a sq ft; "
        "factory split from 2002",
        f"THE AUTHOR'S  ${split.price:,.0f} house, ${value('trailer_price'):,.0f} "
        f"trailer, {value('labor_share') * 100:.0f}% labor, "
        f"{value('shell_hours'):.0f} hours of shell work",
        f"DECIDED    the {value('federal_bracket') * 100:.0f}% federal bracket; "
        "state tax left out",
        f"ESTIMATED  dealer {value('dealer_markup') * 100:.0f}%, labor by item, "
        f"run share {value('run_share') * 100:.0f}%, curve "
        f"+{value('curve_penalty') * 100:.0f}%",
        "So every estimate below is a guess that can be changed, and says so",
    )


SHORT_NAME = {"site": "Site work", "foundations": "Foundations", "framing": "Framing",
              "exterior": "Exterior", "rough_ins": "Pipes, wires, HVAC",
              "interior": "Interior", "final": "Yard, driveway", "other": "Other"}


def category_lines() -> tuple[str, ...]:
    """Stage by stage for the dome's floor: buy it, the dome way, and the pay it equals.

    The last column is the saving in hours of a typical worker's take-home pay: what
    doing that stage the dome way is worth, measured in the hours it would take to
    earn the difference.
    """
    take_home = after_tax_hourly()
    out = []
    for stage, buy, cash, saved in stage_lines():
        out.append(f"{SHORT_NAME[stage]}: buy ${buy:,.0f} · dome ${cash:,.0f} · "
                   f"{saved / take_home:,.0f} h of pay")
    total = stack()
    out.append(f"All: buy ${total.buy:,.0f}, dome way ${total.cash:,.0f}, "
               f"if every hour of the work is yours")
    return tuple(out)


# ----------------------------------------------------------------------
# Proof
# ----------------------------------------------------------------------

def validate_house_economics() -> None:
    """Check every table against itself before a figure of it is shown."""
    for source in SOURCES:
        assert source.kind in KINDS, source.key
        assert source.note.strip(), source.key
        if source.kind == PUBLISHED:
            assert source.cite.strip(), f"published figure {source.key} has no citation"
    keys = [source.key for source in SOURCES]
    assert len(keys) == len(set(keys)), "duplicate source keys"

    # NAHB's items add to its published construction total, and every stage to its
    # published subtotal within the table's own $1 rounding.
    assert abs(construction_total() - dict((k, d) for k, _, d in PRICE_PARTS)
               ["construction"]) < 0.5, construction_total()
    for stage, published in STAGE_TOTALS.items():
        mine = sum(i.dollars for i in ITEMS if i.stage == stage)
        assert abs(mine - published) <= 1.0, (stage, mine, published)
    assert abs(price_total() - value("nahb_sale_price")) <= 1.0, price_total()
    assert {i.stage for i in ITEMS} == set(STAGE_NAME)

    # The schedule accounts for every week exactly once.
    weeks = stage_weeks()
    assert abs(sum(weeks.values()) - value("schedule_weeks")) < 1e-9, weeks
    assert abs(sum(share for _, _, share, _ in time_split()) - 1.0) < 1e-9

    # The labor split lands on the author's share, and the buckets rebuild the price.
    split = house()
    assert abs(split.buckets["labor"] / split.construction - value("labor_share")) < 1e-9
    assert abs(sum(split.buckets.values()) - split.price) < 1e-6
    peak = house(peak=True)
    assert peak.price > split.price
    assert peak.share("labor") < split.share("labor")
    assert abs(sum(peak.buckets.values()) - peak.price) < 1e-6
    # The finding the film states: labor is nowhere near most of the price.
    assert split.share("labor") < 0.34, split.share("labor")

    lot = trailer()
    assert abs(lot.dealer + lot.invoice - lot.price) < 1e-6
    assert lot.factory_other > 0.0

    # The geometry says the dome needs less of everything that scales with shape.
    ratio = geometry_ratios()
    for key in ("framing", "skin", "perimeter", "runs"):
        assert 0.0 < ratio[key] < 1.0, (key, ratio[key])

    # The saving decomposes exactly into where it comes from.
    total = stack()
    assert abs(total.margin + total.labor + total.trees + total.shape
               - total.saved) < 1e-6, total
    assert abs(sum(total.shape_parts.values()) - total.shape) < 1e-6
    # Bought whole, the floor costs the survey's price less its land, per square foot.
    assert abs(total.buy - dome_floor_sqft() * price_total()
               * (1.0 - price_share("lot")) / value("nahb_finished_sqft")) < 1e-6
    frame = frame_value()
    assert frame.hours > 0 and frame.rate_house > frame.rate_trailer > 0.0
    # Rounded tallies still add up.
    parts = {"a": 1.4, "b": 2.4, "c": 3.2}
    assert sum(split_round(parts, 1.0).values()) == round(sum(parts.values()))


def house_report() -> str:
    """Every figure, for reading at a console."""
    out = ["WHAT A HOUSE COSTS, AND WHAT THE FORTNIGHT IS WORTH", ""]
    out.append("Time, builder's schedule stretched to the Census average:")
    for stage, weeks, share, months in time_split():
        out.append(f"  {TIME_NAME[stage]:<26} {weeks:4.1f} wk  {share * 100:5.1f}%  "
                   f"{months:4.2f} months")
    for peak in (False, True):
        split = house(peak=peak)
        out.append("")
        out.append(f"The ${value('house_price'):,.0f} house"
                   f"{' with lumber at the 2021 peak' if peak else ''}: "
                   f"${split.price:,.0f}, about {split.sqft:,.0f} sq ft")
        for bucket in BUCKETS:
            out.append(f"  {BUCKET_NAME[bucket]:<28} ${split.buckets[bucket]:>9,.0f}  "
                       f"{split.share(bucket) * 100:5.1f}%")
    lot = trailer()
    out += ["", f"The ${lot.price:,.0f} manufactured home, about {lot.sqft:,.0f} sq ft:",
            f"  dealer                       ${lot.dealer:>9,.0f}",
            f"  factory materials            ${lot.materials:>9,.0f}",
            f"  factory payroll              ${lot.payroll:>9,.0f}",
            f"  factory overhead, profit     ${lot.factory_other:>9,.0f}",
            f"  lumber at the 2021 peak adds ${lot.peak_materials_added:>9,.0f}"]
    ratio = geometry_ratios()
    out += ["", f"Shape, dome against box on {dome_floor_sqft():.0f} sq ft: framing "
            f"{ratio['framing']:.2f}, skin {ratio['skin']:.2f}, perimeter "
            f"{ratio['perimeter']:.2f}, runs {ratio['runs']:.2f}"]
    frame = frame_value()
    out += ["", f"The frame: buy ${frame.buy_house:,.0f} (house rate) or "
            f"${frame.buy_trailer:,.0f} (trailer rate); the fortnight "
            f"{frame.hours:.0f} h and ${frame.cash_total:,.0f} "
            f"({', '.join(f'{k} ${v:,.0f}' for k, v in frame.cash.items())})",
            f"  = ${frame.rate_house:,.2f} an hour against the house, "
            f"${frame.rate_trailer:,.2f} against the trailer; median take-home "
            f"${after_tax_hourly():.2f}, carpenter ${hourly('wage_carpenters'):.2f}"]
    out += ["", "Stage by stage for the dome's floor:"]
    for stage, buy, cash, saved in stage_lines():
        out.append(f"  {STAGE_NAME[stage]:<34} buy ${buy:>8,.0f}  dome way "
                   f"${cash:>8,.0f}  saved ${saved:>8,.0f}")
    total = stack()
    out += [f"  {'ALL':<34} buy ${total.buy:>8,.0f}  dome way ${total.cash:>8,.0f}  "
            f"saved ${total.saved:>8,.0f}",
            f"  from: builder's share ${total.margin:,.0f}, your labor "
            f"${total.labor:,.0f}, your trees ${total.trees:,.0f}, the shape "
            f"${total.shape:,.0f} ({', '.join(f'{k} ${v:,.0f}' for k, v in total.shape_parts.items())})",
            f"  {total.unchanged * 100:.0f}% of the building cost is untouched by the shape",
            f"  trailer at ${value('mhs_2023_usd_per_sqft')}/sq ft for the same floor: "
            f"${trailer_floor_price():,.0f}; dome way on the same scope: "
            f"${dome_cash_factory_scope():,.0f}"]
    return "\n".join(out)


if __name__ == "__main__":
    validate_house_economics()
    print(house_report())
