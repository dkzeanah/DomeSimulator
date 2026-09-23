"""The quilt network: the campaign's participatory half, with its arithmetic.

A dome's insulation is a quilted layer of recycled clothing. That is a
technical fact about the building and it is also the only part of the whole
project a stranger can take part in from their own kitchen table -- which
makes it the campaign's recruiting mechanism, not a footnote in it.

WHY IT WORKS AS A MOVEMENT AND NOT A DONATION DRIVE

Four things, and all four are countable:

* **the barrier is a machine and an evening.** Not a workshop, not a
  chainsaw, not land;
* **the unit is an object.** A layer is a real thing with a number on it
  that goes on a named dome, not a contribution to a pool;
* **it diverts something.** Textile waste is a large, boring, well-measured
  problem and a layer is a measurable bite out of it;
* **it has provenance.** A dome can say whose shirts are in which layer and
  which winter they went on, forever, because the layers come off in order.

WHAT THIS MODULE IS

The arithmetic behind those claims, and the registry record that makes the
provenance real. It decides no prices -- the money is in
:mod:`kickstarter`, the physics in :mod:`soft_shell`.
"""

from __future__ import annotations

from dataclasses import dataclass

import kickstarter
import soft_shell

# ----------------------------------------------------------------------
# Declared inputs
# ----------------------------------------------------------------------

EXTERNAL_CONSTANTS: tuple[tuple[str, float, str, str], ...] = (
    ("shirt_sqft", 4.5, "sq ft",
     "assumption: the usable rectangle out of one adult t-shirt once the "
     "collar, sleeves and seams are off. Two panels of roughly 15 x 22 in. "
     "Somebody who has actually cut up a hundred shirts should correct this"),
    ("shirt_lb", 0.36, "lb",
     "assumption: one adult cotton t-shirt, about five and a half ounces. "
     "Heavier for a sweatshirt, lighter for a technical tee"),
    ("us_textile_waste_lb_per_person_year", 81.5, "lb/person/year",
     "external: the EPA's figure for US textile waste per person per year. "
     "Quoted as somebody else's measurement, not ours, and it is the only "
     "number in this module that did not come out of this project"),
    ("quilt_hours_per_layer", 9.0, "hours",
     "assumption: cutting, laying out and quilting one layer, by somebody "
     "who has done it before. The first one takes longer and the campaign "
     "should say so"),
    ("quilt_pay_per_layer", 90.0, "USD",
     "the owner's stated rate for a layer sewn for somebody else's dome. "
     "It is above the $50 of materials because it is paying for the "
     "evening, and it is the number that makes this a network rather than "
     "a request for free labour"),
)

CONSTANTS: dict[str, float] = {name: value
                               for name, value, _u, _w in EXTERNAL_CONSTANTS}


def declared(name: str) -> float:
    if name in CONSTANTS:
        return CONSTANTS[name]
    return soft_shell.declared(name)


# ----------------------------------------------------------------------
# One layer
# ----------------------------------------------------------------------

@dataclass(frozen=True)
class Layer:
    """One quilted layer, as the thing a person actually makes."""

    index: int
    sqft: float
    shirts: int
    pounds: float
    hours: float
    materials_usd: float
    pay_usd: float
    r_value: float

    @property
    def waste_years(self) -> float:
        """Whose annual textile waste this layer is, in person-years."""
        return self.pounds / declared("us_textile_waste_lb_per_person_year")


def layer(index: int = 1) -> Layer:
    """The ``index``-th layer on a dome, which is bigger than the one under.

    Index 1 is the first layer on a bare skin. Every layer after it goes
    over the ones already there, so it is a size up -- which is the same
    arithmetic the cap uses and the reason this is not one number.
    """
    index = max(1, int(index))
    # hat_sizes(n)[k] is the area of the skin with k layers under it.
    sizes = soft_shell.hat_sizes(index)
    sqft = sizes[index - 1]
    shirts = int(-(-sqft // declared("shirt_sqft")))
    pounds = shirts * declared("shirt_lb")
    return Layer(
        index=index,
        sqft=sqft,
        shirts=shirts,
        pounds=pounds,
        hours=declared("quilt_hours_per_layer"),
        materials_usd=declared("blanket_quilt_usd_per_layer"),
        pay_usd=declared("quilt_pay_per_layer"),
        r_value=kickstarter.quilt_economics(index)["r_per_layer"],
    )


def stack(layers: int = 7) -> tuple[Layer, ...]:
    return tuple(layer(n) for n in range(1, max(1, layers) + 1))


def dome_totals(layers: int = 7) -> dict:
    """What a fully-quilted dome represents, added up."""
    rows = stack(layers)
    ladder = kickstarter.quilt_economics(layers)
    return {
        "layers": layers,
        "shirts": sum(row.shirts for row in rows),
        "pounds": sum(row.pounds for row in rows),
        "hours": sum(row.hours for row in rows),
        "materials_usd": sum(row.materials_usd for row in rows),
        "pay_usd": sum(row.pay_usd for row in rows),
        "waste_years": sum(row.waste_years for row in rows),
        "r_value": ladder["stacked_r"],
    }


# ----------------------------------------------------------------------
# The registry: what makes it provenance rather than a slogan
# ----------------------------------------------------------------------

#: What is written on the tag sewn into a layer's hem. It is the whole
#: mechanism: a layer is removable and ordered, so the building can always
#: say what it is wearing and who made it.
TAG_FIELDS: tuple[tuple[str, str], ...] = (
    ("layer", "which layer of the stack this is, counting outward from 1"),
    ("dome", "the dome's registry number, so a layer belongs somewhere"),
    ("sewn by", "the maker's name or handle, as they want it written"),
    ("sewn", "the month and year"),
    ("shirts", "how many garments went into it"),
    ("from", "one line about where the clothes came from, if they want it"),
)

#: The three ways somebody joins, in rising order of commitment.
WAYS_IN: tuple[tuple[str, str], ...] = (
    ("Send shirts",
     "A box of clothes nobody will wear again. It gets weighed, logged "
     "against your name, and cut up by somebody with a machine."),
    ("Sew a layer for your own dome",
     "The kit is the pattern, the binding and the specification -- how big, "
     "how thick, how to close the edge. The dome tells you which size it "
     "needs next, because each layer is bigger than the one under it."),
    ("Sew a layer for somebody else's",
     "Listed, paid, and tagged with your name. This is the part that has to "
     "be paid or it is not a network, it is a request for free labour."),
)


def provenance_card(layers: int = 3) -> tuple[str, ...]:
    """The card that ships with a dome, listing what it is wearing."""
    rows = stack(layers)
    total = dome_totals(layers)
    out = [
        "WHAT THIS DOME IS WEARING",
        "",
        f"{'layer':>6}  {'sq ft':>7}  {'shirts':>7}  {'lb':>6}  {'R':>5}",
    ]
    for row in rows:
        out.append(f"{row.index:>6}  {row.sqft:>7.0f}  {row.shirts:>7}  "
                   f"{row.pounds:>6.1f}  {row.r_value:>5.1f}")
    out += [
        "-" * 38,
        f"{'total':>6}  {'':>7}  {total['shirts']:>7}  "
        f"{total['pounds']:>6.1f}  {total['r_value']:>5.1f}",
        "",
        f"{total['hours']:.0f} hours of somebody's evening.",
        f"{total['waste_years']:.1f} person-years of textile waste, "
        f"against the EPA's "
        f"{declared('us_textile_waste_lb_per_person_year'):.0f} lb a year.",
    ]
    return tuple(out)


def report(layers: int = 7) -> str:
    rows = stack(layers)
    total = dome_totals(layers)
    lines = [
        "THE QUILT NETWORK",
        "",
        f"{'layer':>6}  {'sq ft':>7}  {'shirts':>7}  {'lb':>6}  "
        f"{'hours':>6}  {'materials':>10}  {'paid':>7}",
    ]
    for row in rows:
        lines.append(
            f"{row.index:>6}  {row.sqft:>7.0f}  {row.shirts:>7}  "
            f"{row.pounds:>6.1f}  {row.hours:>6.1f}  "
            f"${row.materials_usd:>9,.0f}  ${row.pay_usd:>6,.0f}")
    lines += [
        "-" * 62,
        f"{'all':>6}  {'':>7}  {total['shirts']:>7}  {total['pounds']:>6.1f}  "
        f"{total['hours']:>6.1f}  ${total['materials_usd']:>9,.0f}  "
        f"${total['pay_usd']:>6,.0f}",
        "",
        f"  a fully quilted dome is R-{total['r_value']:.1f}",
        f"  and {total['waste_years']:.1f} person-years of textile waste",
        "",
        "WAYS IN",
        "",
    ]
    for title, what in WAYS_IN:
        lines.append(f"  {title}")
        lines.append(f"      {what}")
    lines += ["", "ON THE TAG", ""]
    for field, why in TAG_FIELDS:
        lines.append(f"  {field:<10} {why}")
    return "\n".join(lines)


def validate_quilt_network() -> None:
    """The arithmetic, and the promises the campaign makes about it."""
    for name, value, unit, why in EXTERNAL_CONSTANTS:
        assert value > 0.0, name
        assert unit, name
        assert len(why) > 40, f"{name} has no reason attached"
        # The one borrowed figure has to say so.
        if "textile_waste" in name:
            assert why.startswith("external:"), name

    first = layer(1)
    assert first.shirts > 50, first
    assert first.sqft > 300.0, first

    # Every layer is bigger than the one under it, which is the whole
    # "each hat is a size up" argument applied to the person sewing.
    rows = stack(7)
    for under, over in zip(rows, rows[1:]):
        assert over.sqft > under.sqft, (under, over)
        assert over.shirts >= under.shirts, (under, over)

    total = dome_totals(7)
    assert total["shirts"] == sum(r.shirts for r in rows)
    assert total["waste_years"] > 0.5, total
    # A dome should be a meaningful bite out of the problem, or the claim is
    # decoration. Seven layers is several people's yearly textile waste.
    assert total["waste_years"] > 2.0, (
        f"a fully quilted dome is only {total['waste_years']:.1f} "
        f"person-years of waste; the campaign should not make this claim")

    # Paying for a layer has to beat its materials, or this is not a network.
    assert first.pay_usd > first.materials_usd, (
        "a sewn layer is paid less than its materials cost; that is a "
        "request for free labour with extra steps")

    # The provenance card has to hold the real stack.
    card = "\n".join(provenance_card(3))
    assert "WHAT THIS DOME IS WEARING" in card
    assert str(dome_totals(3)["shirts"]) in card

    assert len(WAYS_IN) == 3
    assert len(TAG_FIELDS) >= 5


def main(argv: list[str] | None = None) -> int:
    import argparse

    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--layers", type=int, default=7)
    parser.add_argument("--card", action="store_true",
                        help="print the provenance card instead")
    parser.add_argument("--check", action="store_true")
    args = parser.parse_args(argv)

    validate_quilt_network()
    if args.check:
        print("quilt network ok")
        return 0
    if args.card:
        print("\n".join(provenance_card(args.layers)))
        return 0
    print(report(args.layers))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
