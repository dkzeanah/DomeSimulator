"""Hull laminate systems, priced the way a boatyard prices them.

The seed dome's shell is a wood-cored composite skin, which is not a novel
thing to build: it is how small craft have been built for sixty years, and
there are only a handful of laminate systems anybody actually uses. This
module is those systems -- named products, their real specifications, and
what a supplier charges for them -- so the shell can be costed out of the
marine composites trade instead of out of a rule of thumb.

**Priced by weight, not by yardage.** That is the industry's own method, and
it is the thing the first version of this model got wrong. Glass and resin are
sold by weight in bulk; a laminate is specified as ounces of glass per square
foot and a *resin-to-glass ratio*, and the resin quantity falls out of that.
Pricing a laminate at so many ounces of resin per square foot regardless of
what fabric is under it will be right for one schedule and wrong for every
other one.

**Watch the units.** Woven and stitched fabrics are sold by ounces per square
*yard*. Chopped strand mat is sold by ounces per square *foot*. So "1708" is
17 oz/sq yd of stitched biaxial backed with 0.8 oz/sq ft of mat, and that
comes to 24.2 oz per square yard, not 17.8. Getting this wrong understates a
1708 laminate by a third, and it is the single easiest mistake to make in the
whole subject.

Where the numbers come from
---------------------------
Fabric and resin prices are US Composites' published list (August 2026),
converted from their per-linear-yard-at-50-inches pricing to square feet.
Fabric weights are the products' own specifications. Resin-to-glass ratios are
hand-layup figures, checked in :func:`validate_hull_laminate` against two
independently published rules of thumb: about 30 oz of resin wets out one
50-inch yard of 1708, and one layer of 1708 over ten square feet takes one and
a half to two pounds of mixed resin.

Every one of those is a declared input. They are the prices to replace with
your own supplier's quote, and replacing them moves every figure downstream.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Callable

SQFT_PER_LINEAR_YARD_50IN = 50.0 * 36.0 / 144.0
"""12.5 sq ft. A supplier's "per yard" fabric price is per linear yard of a
50-inch roll, which is not a square yard and not a square foot."""

OZ_PER_LB = 16.0
SQFT_PER_SQYD = 9.0


# ----------------------------------------------------------------------
# Declared inputs
# ----------------------------------------------------------------------

EXTERNAL_CONSTANTS: tuple[tuple[str, float, str, str], ...] = (
    # --- resins, per gallon at pail pricing ---
    ("resin_gp_polyester_usd_per_gal", 26.60, "USD/gal",
     "US Composites 816 general-purpose boatyard polyester, $133.00 per "
     "5-gallon pail, catalysed. The cheapest resin anybody builds a hull "
     "out of"),
    ("resin_marine_polyester_usd_per_gal", 37.60, "USD/gal",
     "US Composites 435 premium marine-grade polyester, $188.00 per "
     "5-gallon pail"),
    ("resin_vinylester_usd_per_gal", 61.70, "USD/gal",
     "US Composites 700 vinyl ester, $308.50 per 5-gallon pail. Bought for "
     "water resistance, not for strength"),
    ("resin_epoxy_usd_per_gal", 79.90, "USD/gal",
     "US Composites 635 thin epoxy with 556 hardener, 20-gallon kit at "
     "$1,598.00. A gallon kit is $97.50; a shop buying by the drum is not "
     "paying that"),
    ("resin_lb_per_gal", 9.10, "lb/gal",
     "density of catalysed laminating resin, polyester and epoxy alike to "
     "within a few percent"),
    ("gelcoat_usd_per_gal", 54.60, "USD/gal",
     "US Composites white gelcoat, $273.00 per 5-gallon pail"),
    ("gelcoat_sqft_per_gal", 45.0, "sq ft/gal",
     "one gallon of gelcoat at 18 mil wet, which is what a weather face "
     "wants"),

    # --- fabrics, converted to price and weight per square foot ---
    ("fabric_1708_usd_per_sqft", 0.736, "USD/sq ft",
     "US Composites 1708 biaxial, $9.20 per yard of 50-inch roll over "
     "12.5 sq ft"),
    ("fabric_1708_oz_per_sqft", 2.689, "oz/sq ft",
     "17 oz/sq yd stitched biaxial plus 0.8 oz/sq ft mat backing: "
     "17/9 + 0.8. The mat is specified per square FOOT and the biaxial per "
     "square YARD"),
    ("fabric_csm15_usd_per_sqft", 0.320, "USD/sq ft",
     "US Composites 1-1/2 oz chopped strand mat, $4.00 per yard of "
     "50-inch roll"),
    ("fabric_csm15_oz_per_sqft", 1.50, "oz/sq ft",
     "1-1/2 oz mat, by definition: ounces per square foot"),
    ("fabric_csm075_usd_per_sqft", 0.236, "USD/sq ft",
     "US Composites 3/4 oz chopped strand mat, $2.95 per yard of 50-inch "
     "roll"),
    ("fabric_csm075_oz_per_sqft", 0.75, "oz/sq ft",
     "3/4 oz mat, by definition"),
    ("fabric_cloth6_usd_per_sqft", 0.580, "USD/sq ft",
     "US Composites 6 oz cloth, $7.25 per yard of 50-inch roll"),
    ("fabric_cloth6_oz_per_sqft", 0.667, "oz/sq ft",
     "6 oz/sq yd plain weave: 6/9. This is the cloth every plywood boat is "
     "sheathed in"),
    ("fabric_cloth10_usd_per_sqft", 0.700, "USD/sq ft",
     "US Composites 10 oz cloth, $8.75 per yard of 50-inch roll"),
    ("fabric_cloth10_oz_per_sqft", 1.111, "oz/sq ft", "10 oz/sq yd: 10/9"),

    # --- how much resin each fabric drinks, hand layup ---
    ("ratio_stitched", 1.15, "lb resin per lb glass",
     "hand layup over stitched biaxial. Two published rules of thumb -- "
     "about 30 oz of resin per 50-inch yard of 1708, and 1.5 to 2 lb per "
     "ten square feet -- bracket 0.89 to 1.19; suppliers quote 1:1 to "
     "1.4:1. This sits in the middle of the two. Vacuum bagging would beat "
     "it and hand layup will not"),
    ("ratio_mat", 2.50, "lb resin per lb glass",
     "chopped strand mat, which drinks far more than any woven fabric. "
     "This is why a mat-heavy schedule is heavy and resin-hungry"),
    ("ratio_cloth", 1.60, "lb resin per lb glass",
     "light plain-weave cloth over a porous wood substrate, which takes "
     "more than the cloth alone would"),
    ("seal_coat_lb_per_sqft", 0.075, "lb/sq ft",
     "the first coat straight onto bare sheet, before any glass goes on. "
     "It is drunk by the wood and it is not optional"),

    # --- the rest of the job ---
    ("layup_waste_fraction", 0.15, "fraction",
     "offcuts, overlaps at every seam, and resin left in the pot. A "
     "compound-curved shell wastes more fabric than a flat panel"),
    ("consumables_usd_per_sqft", 0.14, "USD/sq ft",
     "rollers, brushes, squeegees, tape, mixing pots, acetone and gloves, "
     "over the laminated area"),
)

DEFAULTS: dict[str, float] = {name: value
                              for name, value, _u, _n in EXTERNAL_CONSTANTS}


def _default_declared(name: str) -> float:
    return DEFAULTS[name]


Declared = Callable[[str], float]


# ----------------------------------------------------------------------
# What a laminate is made of
# ----------------------------------------------------------------------

@dataclass(frozen=True)
class Ply:
    """One layer of reinforcement, by the constants that describe it."""

    label: str
    weight_key: str
    price_key: str
    ratio_key: str

    def oz_per_sqft(self, declared: Declared) -> float:
        return declared(self.weight_key)

    def usd_per_sqft(self, declared: Declared) -> float:
        return declared(self.price_key)

    def ratio(self, declared: Declared) -> float:
        return declared(self.ratio_key)


BIAX_1708 = Ply("1708 biaxial", "fabric_1708_oz_per_sqft",
                "fabric_1708_usd_per_sqft", "ratio_stitched")
MAT_15 = Ply("1-1/2 oz mat", "fabric_csm15_oz_per_sqft",
             "fabric_csm15_usd_per_sqft", "ratio_mat")
MAT_075 = Ply("3/4 oz mat", "fabric_csm075_oz_per_sqft",
              "fabric_csm075_usd_per_sqft", "ratio_mat")
CLOTH_6 = Ply("6 oz cloth", "fabric_cloth6_oz_per_sqft",
              "fabric_cloth6_usd_per_sqft", "ratio_cloth")
CLOTH_10 = Ply("10 oz cloth", "fabric_cloth10_oz_per_sqft",
               "fabric_cloth10_usd_per_sqft", "ratio_cloth")


@dataclass(frozen=True)
class Laminate:
    """One named way of skinning a wood core, as a yard would spec it."""

    key: str
    label: str
    resin_label: str
    resin_key: str
    outer: tuple[Ply, ...]
    inner: tuple[Ply, ...]
    gelcoat: bool
    note: str

    @property
    def schedule(self) -> str:
        outside = " + ".join(ply.label for ply in self.outer) or "resin only"
        inside = " + ".join(ply.label for ply in self.inner) or "seal coat only"
        return f"outside {outside}; inside {inside}"


LAMINATES: tuple[Laminate, ...] = (
    Laminate(
        "sheathed", "Sheathed ply",
        "epoxy", "resin_epoxy_usd_per_gal",
        outer=(CLOTH_6,), inner=(CLOTH_6,), gelcoat=False,
        note="How a plywood boat is built: one layer of light cloth in "
             "epoxy on each face, to seal the wood and take abrasion. The "
             "lightest and the least structural, and the resin is the most "
             "expensive one on the list"),
    Laminate(
        "boatyard", "Boatyard polyester",
        "general-purpose polyester", "resin_gp_polyester_usd_per_gal",
        outer=(MAT_15, BIAX_1708), inner=(MAT_075,), gelcoat=True,
        note="The production hull skin: a mat bond coat onto the core, "
             "stitched biaxial over it for strength, gelcoat on the "
             "weather face. Cheapest resin there is, and the heaviest "
             "laminate"),
    Laminate(
        "marine", "Premium marine polyester",
        "marine-grade polyester", "resin_marine_polyester_usd_per_gal",
        outer=(MAT_15, BIAX_1708), inner=(MAT_075,), gelcoat=True,
        note="The same schedule in a better resin. What a yard uses when "
             "the hull has to last without being babied"),
    Laminate(
        "vinylester", "Vinyl ester hull",
        "vinyl ester", "resin_vinylester_usd_per_gal",
        outer=(MAT_15, BIAX_1708, CLOTH_10), inner=(MAT_075,), gelcoat=True,
        note="What goes below the waterline on a boat that is expected to "
             "stay there. Bought for water resistance rather than for "
             "strength, which is exactly the argument for a shell that "
             "lives outdoors"),
)

LAMINATE = {item.key: item for item in LAMINATES}
LAMINATE_KEYS = tuple(item.key for item in LAMINATES)


def laminate(key: str) -> Laminate:
    try:
        return LAMINATE[key]
    except KeyError:
        raise KeyError(f"no laminate system {key!r}; choose from "
                       f"{', '.join(LAMINATE_KEYS)}") from None


# ----------------------------------------------------------------------
# Working one out
# ----------------------------------------------------------------------

@dataclass(frozen=True)
class PlyLine:
    """One ply over one area: its glass, its resin, its cost."""

    label: str
    sqft: float
    glass_lb: float
    resin_lb: float
    fabric_usd: float


@dataclass(frozen=True)
class LaminatePlan:
    """A whole skin, weighed and priced."""

    system: Laminate
    plies: tuple[PlyLine, ...]
    seal_lb: float
    resin_gal: float
    resin_usd: float
    fabric_usd: float
    gelcoat_gal: float
    gelcoat_usd: float
    consumables_usd: float
    laminated_sqft: float

    @property
    def glass_lb(self) -> float:
        return sum(ply.glass_lb for ply in self.plies)

    @property
    def laminate_resin_lb(self) -> float:
        """Resin in the laminate itself, which is what a ratio is about."""
        return sum(ply.resin_lb for ply in self.plies)

    @property
    def resin_lb(self) -> float:
        """Every pound of resin the job takes, seal coat included."""
        return self.laminate_resin_lb + self.seal_lb

    @property
    def ratio(self) -> float:
        """Resin to glass in the laminate, by weight.

        The seal coat is deliberately left out. It goes into the wood, not
        into the laminate, and counting it makes a light schedule look badly
        wetted out when what is really happening is that a thirsty substrate
        is drinking most of a cheap first coat."""
        return self.laminate_resin_lb / self.glass_lb if self.glass_lb else 0.0

    @property
    def glass_fraction(self) -> float:
        """Share of the laminate that is glass rather than resin."""
        total = self.glass_lb + self.laminate_resin_lb
        return self.glass_lb / total if total else 0.0

    @property
    def skin_lb(self) -> float:
        """What the laminate weighs, core not included."""
        return self.glass_lb + self.resin_lb

    @property
    def total_usd(self) -> float:
        return (self.resin_usd + self.fabric_usd + self.gelcoat_usd
                + self.consumables_usd)

    @property
    def usd_per_sqft(self) -> float:
        return self.total_usd / self.laminated_sqft if self.laminated_sqft else 0.0

    @property
    def lb_per_sqft(self) -> float:
        return self.skin_lb / self.laminated_sqft if self.laminated_sqft else 0.0


def plan(system: Laminate | str, outer_sqft: float, inner_sqft: float,
         declared: Declared | None = None) -> LaminatePlan:
    """Weigh and price one skin: this schedule over these two areas.

    ``outer_sqft`` is the weather face, which carries the structural plies
    and the gelcoat. ``inner_sqft`` is the face that only has to be sealed.
    Both get the bare-substrate seal coat, because both are bare sheet before
    anybody starts.
    """
    if isinstance(system, str):
        system = laminate(system)
    if declared is None:
        declared = _default_declared

    waste = 1.0 + declared("layup_waste_fraction")
    lines: list[PlyLine] = []
    for plies, area in ((system.outer, outer_sqft), (system.inner, inner_sqft)):
        for ply in plies:
            glass_lb = area * ply.oz_per_sqft(declared) / OZ_PER_LB * waste
            lines.append(PlyLine(
                label=ply.label,
                sqft=area,
                glass_lb=glass_lb,
                resin_lb=glass_lb * ply.ratio(declared),
                fabric_usd=area * ply.usd_per_sqft(declared) * waste,
            ))

    laminated = outer_sqft + inner_sqft
    seal_lb = laminated * declared("seal_coat_lb_per_sqft")
    resin_lb = sum(line.resin_lb for line in lines) + seal_lb
    resin_gal = resin_lb / declared("resin_lb_per_gal")
    gelcoat_gal = (outer_sqft / declared("gelcoat_sqft_per_gal")
                   if system.gelcoat else 0.0)

    return LaminatePlan(
        system=system,
        plies=tuple(lines),
        seal_lb=seal_lb,
        resin_gal=resin_gal,
        resin_usd=resin_gal * declared(system.resin_key),
        fabric_usd=sum(line.fabric_usd for line in lines),
        gelcoat_gal=gelcoat_gal,
        gelcoat_usd=gelcoat_gal * declared("gelcoat_usd_per_gal"),
        consumables_usd=laminated * declared("consumables_usd_per_sqft"),
        laminated_sqft=laminated,
    )


def compare(outer_sqft: float, inner_sqft: float,
            declared: Declared | None = None) -> tuple[LaminatePlan, ...]:
    """Every system over the same two areas, cheapest first."""
    plans = [plan(system, outer_sqft, inner_sqft, declared)
             for system in LAMINATES]
    plans.sort(key=lambda item: item.total_usd)
    return tuple(plans)


def report(outer_sqft: float, inner_sqft: float,
           declared: Declared | None = None) -> str:
    out = [f"HULL LAMINATE SYSTEMS over {outer_sqft:,.0f} sq ft outside and "
           f"{inner_sqft:,.0f} sq ft inside", ""]
    for item in compare(outer_sqft, inner_sqft, declared):
        out.append(f"  {item.system.label.upper()}  --  {item.system.resin_label}")
        out.append(f"    {item.system.schedule}")
        for line in item.plies:
            out.append(f"      {line.label:<16} {line.sqft:>7,.0f} sq ft  "
                       f"{line.glass_lb:>7,.1f} lb glass  "
                       f"{line.resin_lb:>7,.1f} lb resin  "
                       f"${line.fabric_usd:>8,.0f}")
        out.append(f"      {'seal coat':<16} {'':>7} {'':>16} "
                   f"{item.seal_lb:>7,.1f} lb resin")
        out.append(f"      {'resin':<16} {item.resin_gal:>7,.1f} gal    "
                   f"{'':>16} {'':>7}  ${item.resin_usd:>8,.0f}")
        if item.gelcoat_usd:
            out.append(f"      {'gelcoat':<16} {item.gelcoat_gal:>7,.1f} gal"
                       f"    {'':>16} {'':>7}  ${item.gelcoat_usd:>8,.0f}")
        out.append(f"      {'consumables':<16} {'':>7} {'':>16} {'':>7}  "
                   f"${item.consumables_usd:>8,.0f}")
        out.append(f"      TOTAL ${item.total_usd:>9,.0f}   "
                   f"${item.usd_per_sqft:>5.2f}/sq ft   "
                   f"{item.skin_lb:>6,.0f} lb skin   "
                   f"resin:glass {item.ratio:.2f}:1   "
                   f"{item.glass_fraction * 100:.0f}% glass")
        out.append("")
    return "\n".join(out)


# ----------------------------------------------------------------------
# Proof
# ----------------------------------------------------------------------

def validate_hull_laminate() -> None:
    """Check this against what the trade publishes about these materials."""
    declared = _default_declared

    # 1708 is 17 oz/sq yd of biaxial plus 0.8 oz/sq ft of mat. Anyone who
    # reads it as 17.8 oz/sq yd understates the laminate by a third.
    expected = 17.0 / SQFT_PER_SQYD + 0.8
    assert abs(declared("fabric_1708_oz_per_sqft") - expected) < 0.01, expected

    # A 50-inch linear yard covers 12.5 sq ft, and the list price divided by
    # that has to be the per-square-foot price this module uses.
    assert abs(SQFT_PER_LINEAR_YARD_50IN - 12.5) < 1e-9
    assert abs(declared("fabric_1708_usd_per_sqft")
               - 9.20 / SQFT_PER_LINEAR_YARD_50IN) < 0.005

    # Two published rules of thumb, each turned into the resin-to-glass
    # ratio it implies. The declared ratio has to sit inside the envelope
    # they define together, and inside the 1:1 to 1.4:1 suppliers quote.
    ratio = declared("ratio_stitched")
    oz_per_sqft = declared("fabric_1708_oz_per_sqft")

    # "About 30 oz of resin wets out one 50-inch yard of 1708."
    yard_glass_lb = SQFT_PER_LINEAR_YARD_50IN * oz_per_sqft / OZ_PER_LB
    from_yard = (30.0 / OZ_PER_LB) / yard_glass_lb

    # "One layer over ten square feet takes 1.5 to 2 lb of mixed resin."
    ten_glass_lb = 10.0 * oz_per_sqft / OZ_PER_LB
    from_ten_low = 1.5 / ten_glass_lb
    from_ten_high = 2.0 / ten_glass_lb

    low = min(from_yard, from_ten_low)
    high = max(from_ten_high, 1.40)
    assert low - 1e-9 <= ratio <= high + 1e-9, (low, ratio, high)
    assert 1.0 <= high <= 1.45, high

    # Mat drinks more than any woven fabric. If this ever inverts, the
    # schedules are wrong about which way round the economics run.
    assert declared("ratio_mat") > declared("ratio_cloth")
    assert declared("ratio_cloth") > declared("ratio_stitched")

    # Every system has to plan, weigh something, and cost something.
    for system in LAMINATES:
        item = plan(system, 600.0, 560.0)
        assert item.plies, system.key
        assert item.glass_lb > 0.0 and item.resin_lb > item.seal_lb
        assert item.total_usd > 0.0
        # Hand layup runs between the stitched ratio and the mat ratio,
        # whatever the schedule. Outside that band, something is wired up
        # to the wrong fabric.
        assert (declared("ratio_stitched") - 1e-9 <= item.ratio
                <= declared("ratio_mat") + 1e-9), (system.key, item.ratio)
        assert 0.27 < item.glass_fraction < 0.55, (system.key,
                                                   item.glass_fraction)
        assert item.resin_lb > item.laminate_resin_lb  # the seal coat exists
        assert item.system.gelcoat == (item.gelcoat_usd > 0.0)

    # The order has to be the order the trade would expect: sheathed ply is
    # the lightest skin, and the vinyl ester schedule is the heaviest.
    plans = {item.system.key: item for item in compare(600.0, 560.0)}
    assert plans["sheathed"].skin_lb < plans["boatyard"].skin_lb
    assert plans["boatyard"].skin_lb < plans["vinylester"].skin_lb
    # And the same schedule in a dearer resin has to cost more and weigh
    # the same, or the resin line is not doing what it says.
    assert plans["marine"].total_usd > plans["boatyard"].total_usd
    assert abs(plans["marine"].skin_lb - plans["boatyard"].skin_lb) < 1e-6

    # Substituting a price has to move the answer.
    def dearer(name: str) -> float:
        if name == "resin_gp_polyester_usd_per_gal":
            return DEFAULTS[name] * 2.0
        return DEFAULTS[name]

    assert (plan("boatyard", 600.0, 560.0, dearer).total_usd
            > plans["boatyard"].total_usd)


if __name__ == "__main__":
    validate_hull_laminate()
    print(report(597.0, 640.0))
