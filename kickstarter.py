"""The campaign: what a dome costs, what the maker keeps, what the goal buys.

Three separate questions, and the campaign loses if any of them is fudged.

**What does it cost?** Every dollar, in the open. The materials, the labour,
the shop, the freight. This module does not invent any of it -- it asks
:mod:`seed_model` and lays out what comes back.

**What does the maker keep?** Twenty percent, on top of the built cost,
named on screen as profit. Not buried in an overhead fraction, not called a
"contribution", and not left for a backer to work out. A campaign that will
not say its margin is a campaign that is hiding one.

**What does the goal buy?** Tooling and a test platform, itemised, each line
with what it is for and why that number. The goal is the sum of the list,
so it cannot be a round number somebody liked the look of.

THE THREE AUDIENCES

This is not a campaign to sell domes. It is a campaign to start three
things at once, and each one needs the other two:

* **quilters** -- people who sew recycled clothing into insulating layers.
  A dome's insulation is a waste stream and somebody's evening;
* **pad hosts** -- people with land who build a serviced platform and let
  somebody park a building on it;
* **dome owners** -- people who want a building and have trees, or do not.

A dome with nobody to quilt for it is a cold dome. A dome with nowhere to
stand is a kit in a garage. A pad with no dome on it is a deck.

THE ANALOGY THE CAMPAIGN IS BUILT ON

A dome is a head, and it wears hats.

Bare, it is a head in the cold. Put a knit hat on it and it is warmer; put
another over that and it is warmer again, and each hat has to be a size up
from the last. Over the lot goes one waterproof cap, and only that one is
waterproof -- which is why the hats underneath stay dry and keep working.

That is not a metaphor reached for afterwards. It is the design: the
quilted layers are the hats, the cap is the cap, and exactly one layer in
the building is watertight.
"""

from __future__ import annotations

import math
from dataclasses import dataclass

import seed_model
import soft_shell

# ----------------------------------------------------------------------
# What the maker keeps
# ----------------------------------------------------------------------

#: The margin, stated. Applied to the built cost of a dome and named on
#: screen as profit to the maker.
#:
#: The model's own ``gross_margin_fraction`` is a manufacturing figure that
#: also carries warranty, returns and the cost of the next unit's mistakes.
#: This is the simpler, more honest thing a backer asked for: what is the
#: markup, and who gets it.
MARGIN = 0.20

#: What the campaign is raising for, line by line. The goal is the sum.
#:
#: Each line is (key, dollars, what it is, why that number). None of it is
#: salary and none of it is marketing -- it is the equipment and the
#: prototypes that turn a solved geometry into something that can be made
#: more than once.
GOAL_LINES: tuple[tuple[str, float, str, str], ...] = (
    ("test_platform", 4200.0, "A full test platform and one standing dome",
     "A serviced pad and a complete 19.4-foot dome on it, built and left "
     "up through a full year of weather. Everything in this project is "
     "solved and almost none of it is measured. A dome that has stood "
     "through one winter is worth more than any amount of arithmetic"),

    ("instrumentation", 1850.0, "Sensors in the wall, logging for a year",
     "Temperature and humidity at each layer of the cap stack, inside and "
     "out, logged continuously. This is what turns the moisture question "
     "from a design argument into a measurement -- and it is the number "
     "the campaign has promised to publish whichever way it comes out"),

    ("hub_rnd", 9500.0, "Utility hub: three iterations to a design that ships",
     "The centre column is the one part that has to be right, because it "
     "carries every service and it is the part an owner cannot make. Three "
     "builds: one to find what breaks, one to fix it, one to prove the fix. "
     "Tooling, fittings, test rig and the parts thrown away"),

    ("cnc_router", 14500.0, "CNC router, 4x8 bed",
     "Panel prototyping. No panel of this dome fits a 4-foot sheet, so "
     "every panel is a cut somebody has to get right forty times. A router "
     "with a 4x8 bed cuts a panel set in an afternoon and cuts the same "
     "set again next year"),

    ("cnc_plasma", 11800.0, "CNC plasma table",
     "Steel: hub rings, floor spokes, mast flanges, threaded-insert "
     "carriers, the brackets a composite member needs moulded into it. "
     "Plasma rather than laser because the work is plate steel and plate "
     "steel is what plasma is for"),

    ("laser_cutter", 8900.0, "Laser cutter, for gaskets and templates",
     "Spline gaskets, seam seals, panel templates, insert jigs. The parts "
     "that are thin, flat, and have to be identical a hundred and twenty "
     "times. It is also the fastest way to make the fixture that holds a "
     "member for its compound butt cut"),

    ("strut_tooling", 18000.0, "Tooling to mould a strut with its hardware in it",
     "The largest single line and the one that changes the product. A "
     "moulded or printed member arrives with its screw holes, its threaded "
     "inserts and its spline ridge already in it -- so the hardware set "
     "that joins two members is standard, reusable, and comes off with a "
     "driver. Pattern, mould and the first run of members"),

    ("composite_rnd", 12500.0, "Composite triangle: steel core, moulded shell",
     "A member with a steel core for the strength, a moulded plastic body "
     "around it, metal inserts where hardware lands and a spline ridge "
     "where the seal sits. Materials, three rounds of samples, and "
     "destructive testing, because the point of a core is the number it "
     "survives to"),

    ("automation", 7600.0, "Automated processing for the repetitive work",
     "Feed, index, cut, repeat. One dome is 120 members, 160 threaded "
     "inserts and 40 panels, and all of it is the same operation done "
     "many times. This is the difference between making one dome and "
     "being able to make the second one"),

    ("quilt_seed", 5000.0, "Seeding the quilt network",
     "Sewing machines, shipping, and paying the first quilters for the "
     "first layers. Insulation in this building is a waste stream and "
     "somebody's evening, and the network has to exist before the first "
     "dome needs it"),

    ("engineering", 6800.0, "An engineer, for the things that carry people",
     "The frame's wind and snow loads, the mast, and the hoist rating for "
     "the floating rig. This project prices those parts and refuses to "
     "rate them, and that refusal has a cost attached. It is on this list "
     "so nobody has to wonder whether it got skipped"),

    ("fulfilment", 9350.0, "Making and shipping what backers are owed",
     "Kits, plans, hardware sets and freight for the reward tiers. "
     "Budgeted at cost rather than at the tier price, because a campaign "
     "that funds its tooling out of its shipping budget delivers neither"),
)

#: A reward tier. ``cost`` is what it costs to make and send.
TIER_ROWS: tuple[tuple[str, str, float, float, str], ...] = (
    ("plans", "The drawings and the numbers", 35.0, 2.0,
     "Every table in the book, the cut list for any diameter, and the "
     "solver that made them. It is a download; the two dollars is card "
     "fees and hosting"),
    ("quilter", "Quilter's kit", 95.0, 58.0,
     "Pattern, thread, the binding, and the layer specification -- how big, "
     "how thick, how to close the edge. Sew a layer for your own dome, or "
     "sew one for somebody else's and get paid for it"),
    ("hardware", "One bay's hardware set", 180.0, 112.0,
     "Four threaded inserts, the flange screws, the spline gasket and the "
     "seam key for one triangle. The smallest piece of the building that "
     "is a real object rather than a drawing"),
    ("cap", "A shower cap for your dome", 1450.0, 980.0,
     "The rain-slick outer cap, made to the reference diameter, hemmed "
     "with grommets and strapping. The only watertight layer in the "
     "building, and the one you cannot sew at home"),
    ("core", "The utility hub", 2400.0, 1620.0,
     "The centre column, assembled and tested: pad port, water manifold, "
     "drain stack, sub-panel, riser and seal cap. The part an owner "
     "cannot make and the part the goal exists to get right"),
    ("kit_notrees", "Dome kit, frame included", 19800.0, 14900.0,
     "Everything, including the timber, for somebody with no trees. The "
     "expensive version, honestly priced: you are paying for somebody "
     "else's 45 percent recovery"),
    ("kit_trees", "Dome kit, bring your own trees", 11400.0, 8100.0,
     "Everything except the frame. You fell, split and cut the members "
     "from your own land -- which is the whole argument -- and we send the "
     "rest"),
    ("pad", "Pad host's pack", 640.0, 395.0,
     "The platform drawings at five foundation types, the service-port "
     "spec, the rim latch pattern, and the host's costing sheet. For "
     "somebody with land who wants a dome to be able to land on it"),
)


# ----------------------------------------------------------------------
# Records
# ----------------------------------------------------------------------

@dataclass(frozen=True)
class GoalLine:
    key: str
    usd: float
    what: str
    why: str


@dataclass(frozen=True)
class Tier:
    key: str
    label: str
    pledge: float
    cost: float
    why: str

    @property
    def contribution(self) -> float:
        """What this tier puts toward the goal after it is delivered."""
        return self.pledge - self.cost

    @property
    def margin_fraction(self) -> float:
        return self.contribution / self.pledge if self.pledge else 0.0


@dataclass(frozen=True)
class CostStack:
    """What a dome costs, and what the maker adds to it.

    Read off the model's own quote rather than re-summed here. Adding the
    group costs up again gave $14,462 where the model said $10,030, because
    the groups include the pad -- which is the ground, not the dome, and is
    not marked up -- and exclude the overhead and warranty reserve that are
    part of what it really costs to build one.
    """

    groups: tuple[tuple[str, str, float], ...]
    direct: float
    overhead: float
    warranty: float
    built: float
    ground: float
    margin_fraction: float

    @property
    def margin(self) -> float:
        """The maker's profit: a markup on cost, not a margin on price."""
        return self.built * self.margin_fraction

    @property
    def price(self) -> float:
        return self.built + self.margin

    @property
    def standing(self) -> float:
        """Price of the dome plus the ground it needs, at cost."""
        return self.price + self.ground

    @property
    def per_sqft(self) -> float:
        return self.price / seed_model.seed_geometry().floor_decagon_sqft


def goal_lines() -> tuple[GoalLine, ...]:
    return tuple(GoalLine(k, usd, what, why) for k, usd, what, why in GOAL_LINES)


def goal() -> float:
    """The campaign goal: the sum of the list, not a number somebody liked."""
    return sum(line.usd for line in goal_lines())


def tiers() -> tuple[Tier, ...]:
    return tuple(Tier(*row) for row in TIER_ROWS)


def cost_stack(fitout: str = "stem_cell", margin: float = MARGIN) -> CostStack:
    """A dome's cost, group by group, with the markup named separately.

    Asked of :func:`seed_model.quote`, so this cannot disagree with the
    films or the book. What this adds is the split a backer actually wants:
    here is what it costs to build, and here is what we keep.
    """
    quote = seed_model.quote(fitout)
    groups = tuple((group.key, group.label, group.cost)
                   for group in quote.dome_groups if group.cost > 0.0)
    return CostStack(
        groups=groups,
        direct=quote.direct_cost,
        overhead=quote.overhead,
        warranty=quote.warranty,
        built=quote.cost_to_build,
        ground=quote.pad_cost,
        margin_fraction=margin,
    )


def quilt_economics(layers: int = 3) -> dict:
    """What a quilted layer is worth, to the owner and to the quilter.

    The campaign asks people to sew insulation out of clothing that would
    otherwise be landfill. That only works if the arithmetic is good for
    the person sewing as well as the person keeping warm.
    """
    rate = soft_shell.declared("blanket_quilt_usd_per_layer")
    ladder = seed_model.quilt_ladder(max(layers, 1))
    bare = soft_shell.soft_shell(0)
    one = soft_shell.soft_shell(1)
    return {
        "usd_per_layer": rate,
        "marginal_usd_per_layer": one.cost - bare.cost,
        "r_per_layer": ladder.r_per_layer,
        "base_r": ladder.base_r,
        "layers": layers,
        "stacked_r": ladder.base_r + ladder.r_per_layer * layers,
        "sqft_per_layer": soft_shell.hat_sizes(layers)[0],
        # A layer is roughly a queen duvet's worth of area. Shirts are the
        # unit people actually have, so the campaign counts in shirts.
        "shirts_per_layer": math.ceil(soft_shell.hat_sizes(layers)[0] / 4.5),
    }


# ----------------------------------------------------------------------
# Report
# ----------------------------------------------------------------------

def _row(label: str, *cells: str, width: int = 44) -> str:
    return f"  {label:<{width}}" + "".join(f"{c:>13}" for c in cells)


def report(margin: float = MARGIN) -> str:
    stack = cost_stack(margin=margin)
    lines = [
        "WHAT A DOME COSTS, AND WHAT WE KEEP",
        "",
    ]
    for _key, label, cost in stack.groups:
        lines.append(_row(label[:44], f"${cost:,.0f}"))
    lines += [
        "  " + "-" * 57,
        _row("materials and labour", f"${stack.direct:,.0f}"),
        _row("shop overhead", f"${stack.overhead:,.0f}"),
        _row("warranty reserve", f"${stack.warranty:,.0f}"),
        _row("COST TO BUILD", f"${stack.built:,.0f}"),
        "",
        _row(f"our profit, {margin * 100:.0f}% marked up on cost",
             f"${stack.margin:,.0f}"),
        _row("WHAT YOU PAY", f"${stack.price:,.0f}"),
        "",
        _row("per square foot of floor", f"${stack.per_sqft:,.2f}"),
        "",
        _row("the ground it stands on, at cost", f"${stack.ground:,.0f}"),
        _row("standing, all in", f"${stack.standing:,.0f}"),
        "",
        "  We do not mark up the pad. It is yours, or your host's, and you",
        "  can build it yourself for the number above.",
        "",
        "",
        "WHAT THE GOAL BUYS",
        "",
    ]
    for line in goal_lines():
        lines.append(_row(line.what[:44], f"${line.usd:,.0f}"))
    lines += [
        "  " + "-" * 57,
        _row("the goal", f"${goal():,.0f}"),
        "",
        "",
        "TIERS",
        "",
        _row("", "pledge", "to make", "to the goal"),
    ]
    for tier in tiers():
        lines.append(_row(tier.label[:44], f"${tier.pledge:,.0f}",
                          f"${tier.cost:,.0f}",
                          f"${tier.contribution:,.0f}"))
    quilt = quilt_economics()
    lines += [
        "",
        "",
        "THE QUILT",
        "",
        _row("declared, a layer", f"${quilt['usd_per_layer']:,.0f}"),
        _row("with the bigger cap it forces",
             f"${quilt['marginal_usd_per_layer']:,.0f}"),
        _row("R-value it adds", f"{quilt['r_per_layer']:.1f}"),
        _row("bare skin", f"R-{quilt['base_r']:.1f}"),
        _row(f"with {quilt['layers']} layers",
             f"R-{quilt['stacked_r']:.1f}"),
        _row("area of one layer", f"{quilt['sqft_per_layer']:,.0f} sq ft"),
        _row("t-shirts in one layer, roughly",
             f"{quilt['shirts_per_layer']:,}"),
    ]
    return "\n".join(lines)


# ----------------------------------------------------------------------
# Checks
# ----------------------------------------------------------------------

def validate_kickstarter() -> None:
    """The campaign's arithmetic, and the promises it makes about itself."""
    stack = cost_stack()
    assert stack.groups, "no cost groups"
    assert stack.built > 5000.0, stack.built
    # The parts of the cost have to add up to the cost, or the breakdown on
    # screen is decoration.
    assert abs(stack.direct + stack.overhead + stack.warranty
               - stack.built) < 0.01, stack
    # And the ground is quoted beside the dome, never inside it.
    assert stack.ground > 0.0, "the pad has vanished from the quote"
    assert all(key != "pad" for key, _l, _c in stack.groups), (
        "the pad is inside the dome's cost again; it is the ground and it "
        "is not marked up")
    # The margin is exactly what it says. A backer can check this one.
    assert abs(stack.price - stack.built * (1.0 + MARGIN)) < 0.01
    assert abs(stack.margin / stack.built - MARGIN) < 1e-9
    assert abs(MARGIN - 0.20) < 1e-9, (
        "the campaign says twenty percent on camera and in the copy")

    # The dome's price here and the model's quote are the same building
    # costed two ways, so they must not diverge wildly. The model's own
    # margin is a manufacturing figure and this one is the stated markup.
    # The campaign quotes the model, so these are the same number and not
    # merely close. If they ever differ, one of them is being made up.
    quoted = seed_model.quote()
    assert abs(stack.price - quoted.price) < 0.01, (
        f"the campaign says {stack.price:,.2f} and the model says "
        f"{quoted.price:,.2f}")
    assert abs(stack.margin - quoted.gross_profit) < 0.01
    assert abs(seed_model.declared("maker_markup_fraction") - MARGIN) < 1e-9, (
        "the model prices at a different markup from the one the campaign "
        "says on camera")

    # The goal is the sum of the list.
    lines = goal_lines()
    assert len(lines) >= 8, len(lines)
    assert abs(goal() - sum(line.usd for line in lines)) < 1e-9
    keys = [line.key for line in lines]
    assert len(set(keys)) == len(keys), keys
    for line in lines:
        assert line.usd > 0.0, line.key
        assert len(line.why) > 60, f"{line.key} has no reason attached"
        assert len(line.what) > 10, line.key

    # Every promise the user made about what the money is for has a line.
    for needed in ("test_platform", "hub_rnd", "cnc_router", "cnc_plasma",
                   "laser_cutter", "strut_tooling", "composite_rnd",
                   "automation"):
        assert needed in keys, f"the goal has no line for {needed}"

    # No tier may lose money, and no tier may pretend to be a donation.
    for tier in tiers():
        assert tier.cost >= 0.0, tier.key
        assert tier.contribution > 0.0, (
            f"tier {tier.key} costs more to deliver than it raises")
        assert tier.margin_fraction < 0.95, (
            f"tier {tier.key} is priced as a donation, not a reward")
        assert len(tier.why) > 40, tier.key
    tier_keys = [tier.key for tier in tiers()]
    assert len(set(tier_keys)) == len(tier_keys), tier_keys

    # The three audiences each have something to buy.
    assert "quilter" in tier_keys, "nothing for a quilter to back"
    assert "pad" in tier_keys, "nothing for a pad host to back"
    assert any(k.startswith("kit") for k in tier_keys), "no dome to back"

    # And the shell really does have one watertight layer, because the
    # campaign's whole story is that it does.
    concerns = " ".join(head for head, _body in soft_shell.CONCERNS).lower()
    assert "moisture trap" not in concerns, (
        "the shell is back to two impermeable layers; the campaign's Arctic "
        "layering story is then a lie")
    assert soft_shell.declared("membrane_perms") >= 5.0, (
        "the inner layer is no longer vapour-permeable")

    quilt = quilt_economics()
    assert quilt["r_per_layer"] > 0.5, quilt
    assert quilt["shirts_per_layer"] > 20, quilt


def main(argv: list[str] | None = None) -> int:
    import argparse

    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--margin", type=float, default=MARGIN)
    parser.add_argument("--check", action="store_true")
    args = parser.parse_args(argv)

    if args.check:
        validate_kickstarter()
        print("kickstarter ok")
        return 0
    print(report(args.margin))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
