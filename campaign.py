"""The Kickstarter campaign, written out with its numbers still attached.

The copy lives here rather than in a document so it cannot go stale. Every
price, every count and the goal itself are read out of :mod:`kickstarter`
and :mod:`seed_model` when the page is generated, which means the campaign
page and the film and the book cannot quietly disagree about what a dome
costs.

What is NOT computed is the story, and it is marked where it appears. The
Arctic watch is the owner's and belongs to him; everything around it is
arithmetic.

    py -3.12 -m campaign                 # write the page
    py -3.12 -m campaign --check         # just the checks
"""

from __future__ import annotations

from pathlib import Path

import kickstarter
import pad_deck
import seed_model
import soft_shell

ROOT = Path(__file__).resolve().parent
OUT_DIR = ROOT / "deliverables" / "campaign"

#: The three people this campaign is talking to. A dome needs all three to
#: exist, which is why they are one campaign and not three.
AUDIENCES: tuple[tuple[str, str, str], ...] = (
    ("Quilters",
     "You sew. You have a machine, an evening, and a pile of clothes nobody "
     "will wear again.",
     "A dome's insulation is a quilted layer of recycled fabric. One layer "
     "is about 132 t-shirts. Sew one for your own dome, or sew one for "
     "somebody else's and get paid for it. This is the only building "
     "insulation we know of that a person can make at a kitchen table."),
    ("Pad hosts",
     "You have land. You do not want to be a landlord.",
     "Build a serviced platform and let somebody park a building on it. "
     "You maintain a deck and a service connection -- not a roof, not a "
     "boiler, not somebody's kitchen. The building is theirs and it leaves "
     "when they do."),
    ("Dome owners",
     "You want a building. You may or may not have trees.",
     "If you have trees, the frame is already standing on your land and we "
     "send you everything else. If you do not, we send the timber too and "
     "charge you honestly for somebody else's milling waste."),
)

#: The personal part. Not computed, not derived, and the only thing in this
#: campaign that is nobody's business but the owner's.
ARCTIC = """\
I spent time in the Navy standing lookout inside the Arctic Circle.

Forward and aft lookout means you are outside the skin of the ship, in the
weather, for hours. You do not stay warm by wearing one very good thing. You
stay warm by wearing a lot of ordinary things -- base layer, wool, fleece,
whatever else you own -- and then putting one waterproof shell over the lot.
Ours was a pumpkin suit, and it was the only waterproof layer any of us had
on.

That is the whole design of this dome and I did not realise it for years.

The layers underneath are not waterproof and must not be. They are warm
because they are dry, and they stay dry because the water stops at the
outside. Put a second waterproof layer *underneath* them and you have built
a bag that collects your own sweat -- which, on a building, is called a
moisture trap, and it rots the thing from the inside.

So: a dome is a head. Bare, it is a head in the cold. Put a knit hat on it.
Put another over that -- and notice that the second hat has to be a size up,
because the first one is in the way. Keep going. Then put one waterproof cap
over everything.

That is a shower cap for your house, and it is the only part of this
building that has to keep water out."""


def _usd(value: float) -> str:
    return f"${value:,.0f}"


def _cents(value: float) -> str:
    return f"${value:,.2f}"


def numbers() -> dict:
    """Every figure the page quotes, in one place, read from the model."""
    stack = kickstarter.cost_stack()
    quote = seed_model.quote()
    hard = seed_model.quote("stem_cell", shell="hard")
    geometry = seed_model.seed_geometry()
    quilt = kickstarter.quilt_economics()
    upgrade = (seed_model.mast_group().cost
               + seed_model.dome_floor_group().cost
               + seed_model.suspension_group().cost)
    return {
        "stack": stack,
        "quote": quote,
        "hard": hard,
        "geometry": geometry,
        "quilt": quilt,
        "goal": kickstarter.goal(),
        "upgrade": upgrade,
        "cheapest_pad": pad_deck.deck("gravel").cost,
        "staple_pad": pad_deck.deck("blocks").cost,
        "cavity_limit": soft_shell.cavity_limit(),
        "growth_7": soft_shell.growth_fraction(7),
    }


def page() -> str:
    """The campaign page, as Markdown, with its numbers filled in."""
    n = numbers()
    stack = n["stack"]
    geo = n["geometry"]
    quilt = n["quilt"]
    out: list[str] = []
    add = out.append

    add("# A house you can take apart")
    add("")
    add(f"A {geo.diameter_ft:.1f}-foot geodesic dome for "
        f"**{_usd(stack.price)}**, cut from trees you already own, that "
        f"comes apart into pieces a pickup can carry.")
    add("")
    add(f"{geo.floor_decagon_sqft:.0f} square feet of floor. "
        f"{_cents(stack.per_sqft)} a square foot. No mitre saw, no jig, no "
        f"shop, and no hub.")
    add("")
    add("---")
    add("")

    # -- the story ----------------------------------------------------
    add("## Why a house should be dressed like a sailor")
    add("")
    add(ARCTIC)
    add("")
    add("---")
    add("")

    # -- how it works -------------------------------------------------
    add("## How the hats work")
    add("")
    add("From the frame outwards:")
    add("")
    add("1. **Wood panels** on the outside face of the frame. They screw "
        "into threaded inserts and pull *into* the frame, so gravity works "
        "with the fixing. Four per bay, "
        f"{soft_shell.declared('panel_inserts_per_bay') * 40:.0f} in the dome.")
    add("2. **A breather** over all of it. Vapour-permeable, "
        f"{soft_shell.declared('membrane_perms'):.0f} perms -- it lets water "
        "vapour out. It is not a poly sheet and it must never be one.")
    add(f"3. **Quilted layers** of recycled clothing, "
        f"{_usd(quilt['usd_per_layer'])} a layer, added one at a time over "
        f"years. Each adds about R-{quilt['r_per_layer']:.1f}.")
    add("4. **One rain-slick cap** pulled over the lot and strapped down. "
        "**This is the only watertight layer in the building.**")
    add("")
    add("### Why a cap and not a shell")
    add("")
    add("A rigid shell is moulded once, at one size. Its cavity holds "
        f"{n['cavity_limit']} quilted layers and then it is full. After that, "
        "insulating further means losing floor area or building a second "
        "shell outside the first, and neither ever happens. So a rigid shell "
        "quietly caps how good the building is ever allowed to get.")
    add("")
    add("A cap is a bag. Every layer under it buys the next cap a size up. "
        f"Seven layers makes the cap {n['growth_7'] * 100:.1f}% bigger and "
        "nothing else about the building changes.")
    add("")
    add(f"Bare, the skin is about R-{quilt['base_r']:.1f}. That is a tent "
        f"with opinions. At {quilt['layers']} layers it is "
        f"R-{quilt['stacked_r']:.1f}. At seven it is a real wall.")
    add("")
    add("**The building works on day one and it gets warmer every winter "
        "after that.** That is the whole product.")
    add("")
    add("---")
    add("")

    # -- the money ----------------------------------------------------
    add("## What it costs, all of it")
    add("")
    add("We are going to show you the whole invoice, because a campaign that "
        "will not say its margin is hiding one.")
    add("")
    add("| | |")
    add("|---|---:|")
    for _key, label, cost in stack.groups:
        add(f"| {label} | {_usd(cost)} |")
    add(f"| **Materials and labour** | **{_usd(stack.direct)}** |")
    add(f"| Shop overhead | {_usd(stack.overhead)} |")
    add(f"| Warranty reserve | {_usd(stack.warranty)} |")
    add(f"| **What it costs us to build** | **{_usd(stack.built)}** |")
    add(f"| Our profit — {kickstarter.MARGIN * 100:.0f}%, marked up on "
        f"cost | {_usd(stack.margin)} |")
    add(f"| **What you pay** | **{_usd(stack.price)}** |")
    add("")
    add(f"That is {_cents(stack.per_sqft)} a square foot of floor.")
    add("")
    add(f"**Twenty percent, marked up on cost.** Not a margin on price, "
        f"which would be more. {_usd(stack.built)} times 1.20 is "
        f"{_usd(stack.price)}, and you can check that on your phone.")
    add("")
    add("### What is not in that number")
    add("")
    add(f"**The ground.** A platform to stand it on is about "
        f"{_usd(stack.ground)} and **we do not mark it up.** It is yours, or "
        f"your host's, and you can build it yourself. A compacted gravel pad "
        f"is {_usd(n['cheapest_pad'])}; the framed deck most people build is "
        f"{_usd(n['staple_pad'])}.")
    add("")
    add(f"Dome plus ground, standing: **{_usd(stack.standing)}**.")
    add("")
    add("**The upgrades**, which are upgrades because you buy them later or "
        "never:")
    add("")
    add(f"- the laminated hull, the fifty-year skin: {_usd(n['hard'].price)}")
    add(f"- the mast, the dome's own floor, and the rig that hangs it "
        f"between two trees: {_usd(n['upgrade'])}")
    add("")
    add("---")
    add("")

    # -- the goal -----------------------------------------------------
    add(f"## What {_usd(n['goal'])} buys")
    add("")
    add("This is not a pre-order dressed up as a campaign. The geometry is "
        "solved and the first dome can be built by hand. What we do not have "
        "is any way to make the *second* one, or any measurement of the "
        "first one standing through a winter.")
    add("")
    add("The goal is the sum of this list. It is not a round number we "
        "liked.")
    add("")
    add("| | |")
    add("|---|---:|")
    for line in kickstarter.goal_lines():
        add(f"| **{line.what}**<br>{line.why} | {_usd(line.usd)} |")
    add(f"| **Total — the goal** | **{_usd(n['goal'])}** |")
    add("")
    add("---")
    add("")

    # -- the next product ---------------------------------------------
    add("## What we want to make next")
    add("")
    add("Everything above is a building made of split logs, and that is on "
        "purpose -- it is the version somebody can build with a chainsaw and "
        "two trees. But the same geometry can be made a much better way, and "
        "that is what most of the tooling budget is for.")
    add("")
    add("**A moulded member with its hardware already in it.** Screw holes, "
        "threaded inserts and the spline ridge for the seal, moulded or "
        "printed in from the start. The hardware set that joins two members "
        "becomes a standard part, reusable, and it comes off with a driver. "
        "Today every insert is set by hand, 160 of them a dome.")
    add("")
    add("**A composite triangle.** A steel core where the strength has to "
        "be, a moulded body around it, metal inserts where hardware lands, "
        "and a spline ridge where the gasket sits. One part, no joinery, and "
        "a load rating that came off a test rig rather than an argument.")
    add("")
    add("**And the honest part:** neither of those exists yet. The budget "
        "above pays for three rounds of samples and destructive testing, and "
        "we will publish what breaks.")
    add("")
    add("---")
    add("")

    # -- audiences ----------------------------------------------------
    add("## Three things at once")
    add("")
    add("A dome with nobody to quilt for it is a cold dome. A dome with "
        "nowhere to stand is a kit in a garage. A pad with no dome on it is "
        "a deck. So this is one campaign and not three.")
    add("")
    for title, who, what in AUDIENCES:
        add(f"### {title}")
        add("")
        add(f"*{who}*")
        add("")
        add(what)
        add("")
    add("---")
    add("")

    # -- the quilt network --------------------------------------------
    add("## The quilt")
    add("")
    add("One layer covers about "
        f"{quilt['sqft_per_layer']:,.0f} square feet and is roughly "
        f"**{quilt['shirts_per_layer']:,} t-shirts**.")
    add("")
    add(f"It costs {_usd(quilt['usd_per_layer'])} in materials if the fabric "
        f"is a waste stream, which it is. Including the bigger cap it forces, "
        f"a layer costs {_usd(quilt['marginal_usd_per_layer'])} and adds "
        f"about R-{quilt['r_per_layer']:.1f}.")
    add("")
    add("We want a register of people who will sew them. Not a charity "
        "drive -- a paid, listed, ongoing thing, where somebody with a dome "
        "can find somebody with a machine.")
    add("")
    add("---")
    add("")

    # -- tiers --------------------------------------------------------
    add("## Tiers")
    add("")
    add("| Pledge | What you get | |")
    add("|---:|---|---|")
    for tier in kickstarter.tiers():
        add(f"| **{_usd(tier.pledge)}** | **{tier.label}**<br>{tier.why} | |")
    add("")
    add("---")
    add("")

    # -- risks --------------------------------------------------------
    add("## What could go wrong")
    add("")
    add("Every one of these is in the model, on camera in the film, and "
        "in the book.")
    add("")
    for head, body in soft_shell.CONCERNS:
        add(f"**{head}** {body}")
        add("")
    add("**It is not engineered.** The frame's wind and snow loads, the "
        "mast, and the hoist rating for the floating rig are an engineer's "
        "numbers and we have not paid one yet. That is a line in the budget "
        "above. Until it is done, nothing here is a structure anybody should "
        "stand under without a professional looking at it first.")
    add("")
    add("**Nobody has lived in one.** The geometry is solved, the costs are "
        "modelled, and the first dome is not built. That is what the test "
        "platform is for and it is the first thing the money buys.")
    add("")
    return "\n".join(out).rstrip() + "\n"


def write(path: Path | None = None) -> Path:
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    path = Path(path) if path else OUT_DIR / "campaign-page.md"
    path.write_text(page(), encoding="utf-8")
    return path


def validate_campaign() -> None:
    """The page must quote the model, and must not lose an audience."""
    kickstarter.validate_kickstarter()
    text = page()
    n = numbers()
    stack = n["stack"]

    # Every headline figure is present, as the model says it.
    for needed in (_usd(stack.price), _usd(stack.built), _usd(stack.margin),
                   _usd(stack.ground), _usd(n["goal"]),
                   _cents(stack.per_sqft)):
        assert needed in text, f"the page no longer quotes {needed}"

    # The page may not contain a price the model does not know about. A
    # stray "$18,834" from an older draft is exactly the failure this
    # repository keeps having.
    import re

    known = {
        _usd(v) for v in (
            stack.price, stack.built, stack.margin, stack.direct,
            stack.overhead, stack.warranty, stack.ground, stack.standing,
            n["goal"], n["hard"].price, n["upgrade"], n["cheapest_pad"],
            n["staple_pad"], n["quilt"]["usd_per_layer"],
            n["quilt"]["marginal_usd_per_layer"],
        )
    }
    known |= {_usd(cost) for _k, _l, cost in stack.groups}
    known |= {_usd(line.usd) for line in kickstarter.goal_lines()}
    known |= {_usd(t.pledge) for t in kickstarter.tiers()}
    known |= {_cents(stack.per_sqft)}
    # The pattern must not end on a comma, or "$12,036, and you can check"
    # is read as the figure "$12,036," and nothing matches it.
    for found in set(re.findall(r"\$\d[\d,]*\d(?:\.\d\d)?|\$\d", text)):
        assert found in known, (
            f"the page quotes {found}, which is not a figure the model "
            f"produces -- it has been typed in or has gone stale")

    # The story is present and is the owner's.
    assert "Arctic" in text and "pumpkin suit" in text
    assert "only waterproof layer" in text or "only watertight layer" in text

    # All three audiences, and something each of them can back.
    for title, _who, _what in AUDIENCES:
        assert title in text, f"{title} have dropped off the page"
    assert len(AUDIENCES) == 3

    # The risks are the model's own, not a softened retelling.
    for head, _body in soft_shell.CONCERNS:
        assert head in text, f"the page drops the concern {head!r}"

    # And the hand-written kit beside it, which is where a stale number
    # actually hides -- the generated page cannot go stale and a document
    # somebody typed can.
    validate_kit()



# ----------------------------------------------------------------------
# The handoff kit
# ----------------------------------------------------------------------

KIT_DIR = ROOT / "docs" / "kickstarter"

#: The table in the kit's README, regenerated rather than remembered.
KIT_TABLE_START = "| figure | value |"
#: A blank line ends the table.
KIT_TABLE_END = "\n\n"


def kit_numbers() -> set[str]:
    """Every dollar figure the model can currently produce.

    The kit is written by hand -- image prompts, a video outline, tier
    copy -- and a hand-written number goes stale the moment a constant
    moves. This is the set anything in the kit is allowed to say, and
    :func:`validate_kit` fails on anything outside it.
    """
    values: set[float] = set()
    quote = seed_model.quote()
    hard = seed_model.quote("stem_cell", shell="hard")
    values |= {
        quote.price, quote.cost_to_build, quote.gross_profit,
        quote.direct_cost, quote.overhead, quote.warranty, quote.pad_cost,
        quote.delivered_price, quote.price_per_sqft,
        hard.price, hard.cost_to_build, hard.price - quote.price,
        kickstarter.goal(),
        seed_model.declared("freight_usd"),
        seed_model.frame_weight_lb(),
        soft_shell.declared("blanket_quilt_usd_per_layer"),
    }
    values |= set(seed_model.floor_price())
    upgrade = 0.0
    for group in (seed_model.mast_group(), seed_model.dome_floor_group(),
                  seed_model.suspension_group()):
        values.add(group.cost)
        upgrade += group.cost
    # The sums the copy actually quotes, as well as the parts.
    stack = kickstarter.cost_stack()
    values |= {upgrade, stack.standing, stack.price, stack.margin,
               stack.built, stack.ground}
    quilt = kickstarter.quilt_economics()
    values |= {quilt["usd_per_layer"], quilt["marginal_usd_per_layer"]}
    for group in quote.groups:
        values.add(group.cost)
    for layers in range(0, 9):
        values.add(soft_shell.soft_shell(layers).cost)
    for kind in pad_deck.KINDS:
        values.add(pad_deck.deck(kind).cost)
    for line in kickstarter.goal_lines():
        values.add(line.usd)
    for tier in kickstarter.tiers():
        values |= {tier.pledge, tier.cost, tier.contribution}
    # Every fit-out, because the catalogue chapter quotes them.
    for key in seed_model.FITOUT_ORDER:
        try:
            priced = seed_model.quote(key)
        except Exception:
            continue
        values |= {priced.price, priced.cost_to_build}
    # The cap-against-hull comparison at every layer count, and the saving,
    # because the copy quotes both sides of it.
    for row in soft_shell.compare(8):
        values |= {row.soft_usd, row.hard_usd, row.hard_usd - row.soft_usd}
    # And the yard-priced quilt, which is the alternative the copy names.
    for layers in range(0, 4):
        yard = soft_shell.soft_shell(layers, quilt="yard")
        values.add(yard.cost)
        values.add(yard.cost - soft_shell.soft_shell(0, quilt="yard").cost)
    out: set[str] = set()
    for value in values:
        out.add(f"${value:,.0f}")
        out.add(f"${value:,.2f}")
    return out


def kit_table() -> str:
    """The live-numbers table for the kit's README."""
    n = numbers()
    stack = n["stack"]
    geo = n["geometry"]
    quilt = n["quilt"]
    rows = [
        ("the stem cell: dome across / tall",
         f"{geo.diameter_ft:.2f} ft / {geo.diameter_ft / 2:.2f} ft"),
        ("floor (ten-sided) / bays / members",
         f"{geo.floor_decagon_sqft:.0f} sq ft / 40 / {geo.member_count}"),
        ("**standard article, shower cap -- what you pay**",
         f"**{_usd(stack.price)}**"),
        ("... what it costs us to build", _usd(stack.built)),
        ("... our profit, 20% marked up on cost", _usd(stack.margin)),
        ("... per square foot of floor", _cents(stack.per_sqft)),
        ("the same dome, laminated hull", _usd(n["hard"].price)),
        ("the hull is dearer by", _usd(n["hard"].price - stack.price)),
        ("one blanket-quilted layer", _usd(quilt["usd_per_layer"])),
        ("... with the bigger cap it forces",
         _usd(quilt["marginal_usd_per_layer"])),
        ("... in t-shirts", f"{quilt['shirts_per_layer']:,}"),
        ("watertight layers in the building", "1 -- the outer cap"),
        ("mast + floor + rig", _usd(n["upgrade"])),
        ("the host's pad", _usd(stack.ground)),
        ("dome + ground, standing", _usd(stack.standing)),
        ("**the campaign goal**", f"**{_usd(n['goal'])}**"),
    ]
    lines = ["| figure | value |", "|---|---|"]
    lines += [f"| {label} | {value} |" for label, value in rows]
    return "\n".join(lines)


def refresh_kit() -> Path:
    """Rewrite the kit README's number table from the model."""
    readme = KIT_DIR / "README.md"
    text = readme.read_text(encoding="utf-8")
    start = text.index(KIT_TABLE_START)
    end = text.index(KIT_TABLE_END, start)
    text = text[:start] + kit_table() + text[end:]
    readme.write_text(text, encoding="utf-8")
    return readme


def validate_kit() -> dict:
    """No file in the kit may quote a figure the model does not produce."""
    import re

    known = kit_numbers()
    pattern = re.compile(r"\$\d[\d,]*\d(?:\.\d\d)?|\$\d")
    stale: list[str] = []
    checked = 0
    for path in sorted(KIT_DIR.glob("*.md")):
        checked += 1
        for number, line in enumerate(
                path.read_text(encoding="utf-8").splitlines(), start=1):
            for found in pattern.findall(line):
                if found not in known:
                    stale.append(f"{path.name}:{number}  {found}")
    bullet = "\n  "
    assert not stale, (
        "the campaign kit quotes figures the model does not produce:"
        + bullet + bullet.join(stale[:24])
        + (f"{bullet}... and {len(stale) - 24} more"
           if len(stale) > 24 else ""))
    return {"files": checked}


def main(argv: list[str] | None = None) -> int:
    import argparse

    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--out", default=None)
    parser.add_argument("--check", action="store_true")
    args = parser.parse_args(argv)

    validate_campaign()
    if args.check:
        print("campaign ok")
        return 0
    path = write(args.out)
    print(f"wrote {path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
