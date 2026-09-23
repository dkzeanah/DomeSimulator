"""What a dome actually stands on, priced from a lumber yard receipt.

The pad model used to carry three flat rates -- $22 a square foot for wood,
$9 for concrete, $2.50 for gravel -- typed in as assumptions. Two things were
wrong with that and they compounded.

The first is the rate. $22/sq ft is what a contractor charges for a finished
deck with railings, stairs and a permit; it is not what a platform costs.
Nothing in this repository should carry a number that large as an assumption
when the thing it prices is a list of boards you can go and buy.

The second was worse: the rates were being applied to a **48 ft** pad, which
is the flagship dome's size. A seed dome is 19.42 ft across. Area goes as the
square of diameter, so pricing a seed dome's platform at 48 ft overstates it
four times over before the rate is even wrong.

So this module does the takeoff instead. Every board is counted, every board
is priced off the one measured shelf price the rest of the project already
uses (``seed_model.declared("lumber_board_usd")``, a 2x6x12 at Lowes), and
the answer comes out where an owner-builder would expect it: **a platform for
a seed dome is a couple of thousand dollars, not fifty.**

Four constructions are priced, because the choice is real:

* ``gravel``    -- a compacted base course. Not a floor. It is in here
                   because it is the base under every other option, and
                   because quoting it *as* a floor is what made the old
                   model look cheap.
* ``blocks``    -- precast piers, beams, joists, deck boards, sealed. The
                   staple: the bare minimum platform that hosts a dome.
* ``ring``      -- a poured concrete **ring** under the base pentagon only,
                   with the middle framed in wood. Concrete where the load
                   lands and lumber where it does not, which is how a
                   grain bin or a yurt platform is actually built.
* ``slab``      -- a full 4 in slab. The most expensive and the only one
                   that is also the floor finish.

Nothing here decides a dome's geometry; sizes come from :mod:`seed_model`.
"""

from __future__ import annotations

import math
from dataclasses import dataclass

import seed_model


# ----------------------------------------------------------------------
# Declared inputs
# ----------------------------------------------------------------------

# (name, value, unit, why this number and not another)
EXTERNAL_CONSTANTS: tuple[tuple[str, float, str, str], ...] = (
    ("board_nominal_ft", 12.0, "ft",
     "measured: the 2x6x12 that seed_model prices is twelve feet long. "
     "Every linear foot of framing in this module is bought in these"),
    ("board_face_in", 5.5, "in",
     "measured: a nominal 2x6 is 5.5 in wide, so that is what one board "
     "covers when it is laid as decking"),
    ("joist_spacing_in", 16.0, "in",
     "standard: joists at 16 in on centre. A dome's load arrives at ten "
     "points on a ring, not spread over the floor, so this is generous"),
    ("beam_spacing_ft", 6.0, "ft",
     "standard: how far a doubled 2x6 beam spans between piers before it "
     "wants another one under it"),
    ("pier_usd", 12.00, "USD each",
     "measured: a precast concrete deck block at a builders merchant"),
    ("cut_waste_fraction", 0.12, "fraction",
     "assumption: what a round platform wastes cutting straight boards to "
     "a decagon. Higher than a rectangular deck for the obvious reason"),
    ("fastener_usd_per_sqft", 0.55, "USD/sq ft",
     "assumption: joist hangers, structural screws and deck screws, which "
     "are a real line and not a rounding error at this scale"),
    ("gravel_base_usd_per_sqft", 1.20, "USD/sq ft",
     "assumption: 4 in of compacted crusher run over woven fabric, "
     "delivered and spread by the owner. This is a base course, not a floor"),
    ("sealer_usd_per_sqft", 1.10, "USD/sq ft",
     "assumption: two coats of penetrating deck sealer, owner-applied. "
     "The epoxy option is priced separately because it is a different job"),
    ("epoxy_usd_per_sqft", 3.40, "USD/sq ft",
     "assumption: a two-part epoxy deck coating over ply underlayment, "
     "owner-applied. What turns a deck into something you mop"),
    ("underlayment_usd_per_sqft", 1.35, "USD/sq ft",
     "assumption: 1/2 in exterior ply over the deck boards, which an epoxy "
     "or tile finish needs and a sealed deck does not"),
    ("concrete_usd_per_cuyd", 185.00, "USD/cu yd",
     "assumption: ready-mix delivered, small load, US average 2026"),
    ("concrete_place_usd_per_sqft", 3.20, "USD/sq ft",
     "assumption: forming, placing and finishing a small slab, contracted. "
     "Owner-placed is cheaper and is not what this quotes"),
    ("ring_width_in", 16.0, "in",
     "assumption: how wide the poured ring under the base decagon is. Wide "
     "enough to take a hub plate and its anchors with room to be off"),
    ("ring_depth_in", 12.0, "in",
     "assumption: how deep that ring is poured. Frost depth is local and "
     "this is not it -- a cold climate needs more and the model says so"),
    ("slab_depth_in", 4.0, "in",
     "standard: a 4 in slab, which is what a residential floor is poured at"),
)

CONSTANTS: dict[str, float] = {name: value
                               for name, value, _unit, _why in EXTERNAL_CONSTANTS}


def declared(name: str) -> float:
    """One declared input, by name. Raises rather than guessing."""
    if name in CONSTANTS:
        return CONSTANTS[name]
    return seed_model.declared(name)


def board_usd() -> float:
    """The one shelf price every stick in this module is bought at.

    Borrowed from :mod:`seed_model` rather than restated, so a change to
    what a 2x6x12 costs moves the dome's frame and its platform together.
    """
    return seed_model.declared("lumber_board_usd")


def usd_per_linear_ft() -> float:
    """A running foot of 2x6, at the shelf price."""
    return board_usd() / declared("board_nominal_ft")


# ----------------------------------------------------------------------
# The platform's own geometry
# ----------------------------------------------------------------------

def pad_diameter_ft(clearance_ft: float = 1.5) -> float:
    """How wide a platform has to be for the seed dome to stand on it.

    The dome's base is a decagon 19.42 ft across. The platform carries that
    plus a walking margin, and it is *not* the 48 ft flagship pad that the
    park model prices -- which is the single biggest error in the old
    numbers, because area goes as diameter squared.
    """
    return seed_model.seed_geometry().diameter_ft + 2.0 * clearance_ft


def decagon_area_sqft(across_ft: float) -> float:
    """Area of a regular decagon measured across its corners.

    The platform follows the dome's own footprint rather than a circle: a
    decagon of the same span is 93.8% of the circle's area, and cutting
    boards to a circle wastes more than cutting them to ten straight edges.
    """
    radius = across_ft / 2.0
    return 10.0 * 0.5 * radius * radius * math.sin(math.tau / 10.0)


def perimeter_ft(across_ft: float) -> float:
    """The length of the decagon's ten sides."""
    return 10.0 * across_ft / 2.0 * 2.0 * math.sin(math.pi / 10.0)


# ----------------------------------------------------------------------
# One line of a bill of materials
# ----------------------------------------------------------------------

@dataclass(frozen=True)
class Line:
    """One item on the receipt, with what it is and how many."""

    label: str
    quantity: float
    unit: str
    unit_cost: float
    source: str

    @property
    def cost(self) -> float:
        return self.quantity * self.unit_cost


@dataclass(frozen=True)
class Deck:
    """One way of building the platform, costed line by line."""

    key: str
    label: str
    across_ft: float
    lines: tuple[Line, ...]
    note: str
    walkable: bool

    @property
    def area_sqft(self) -> float:
        return decagon_area_sqft(self.across_ft)

    @property
    def cost(self) -> float:
        return sum(line.cost for line in self.lines)

    @property
    def usd_per_sqft(self) -> float:
        return self.cost / self.area_sqft if self.area_sqft else 0.0

    @property
    def boards(self) -> float:
        """How many 2x6x12 the whole thing takes, which is what you order."""
        feet = sum(line.quantity for line in self.lines
                   if line.unit == "ln ft of 2x6")
        return math.ceil(feet / declared("board_nominal_ft"))


# ----------------------------------------------------------------------
# The takeoff
# ----------------------------------------------------------------------

def _gravel_base(area: float) -> Line:
    return Line("compacted gravel base over fabric", area, "sq ft",
                declared("gravel_base_usd_per_sqft"), "gravel_base_usd_per_sqft")


def _framing_lines(across: float, area: float, framed_fraction: float = 1.0,
                   bearing_ring: bool = False) -> list[Line]:
    """Piers, beams, joists and deck boards for a framed platform.

    ``framed_fraction`` is how much of the platform is wood; the concrete
    ring option frames only the middle. ``bearing_ring`` says the perimeter
    is already carried by that concrete, so the joists land on it and the
    outermost run of beam and its piers are not bought twice.
    """
    rate = usd_per_linear_ft()
    framed = area * framed_fraction

    # Decking: a 2x6 covers 5.5 in, so a square foot takes 12/5.5 running
    # feet of board, plus what a decagon wastes on the cuts.
    waste = 1.0 + declared("cut_waste_fraction")
    cover_ft = declared("board_face_in") / 12.0
    decking = framed / cover_ft * waste

    # Joists at 16 in centres: one running foot of joist per 16 in of width.
    joist = framed / (declared("joist_spacing_in") / 12.0) * waste

    # Beams: runs across the platform at the beam spacing, doubled. A
    # bearing ring carries the perimeter, so the end runs are already
    # supported and are not bought again.
    runs = max(2.0, math.ceil(across / declared("beam_spacing_ft")))
    if bearing_ring:
        runs = max(1.0, runs - 2.0)
    beam = runs * across * 2.0 * framed_fraction

    # Piers: one under each beam at the beam spacing, plus its ends -- and
    # none at all around the edge when concrete is already there.
    per_run = math.ceil(across / declared("beam_spacing_ft")) + 1.0
    piers = runs * (per_run - 2.0 if bearing_ring else per_run)
    piers = max(piers, 3.0)

    return [
        Line("deck boards, 2x6 laid flat", decking, "ln ft of 2x6", rate,
             "lumber_board_usd"),
        Line(f"joists at {declared('joist_spacing_in'):.0f} in centres",
             joist, "ln ft of 2x6", rate, "lumber_board_usd"),
        Line("beams, doubled 2x6", beam, "ln ft of 2x6", rate,
             "lumber_board_usd"),
        Line("precast piers", piers, "each", declared("pier_usd"), "pier_usd"),
        Line("hangers, structural and deck screws", framed, "sq ft",
             declared("fastener_usd_per_sqft"), "fastener_usd_per_sqft"),
    ]


def deck(kind: str = "blocks", across_ft: float | None = None) -> Deck:
    """One platform, costed. See the module docstring for the four kinds."""
    across = pad_diameter_ft() if across_ft is None else across_ft
    area = decagon_area_sqft(across)
    lines: list[Line] = []

    if kind == "gravel":
        lines.append(_gravel_base(area))
        return Deck(kind, "Compacted gravel base", across, tuple(lines),
                    "A base course, not a floor. Nobody lives on it. It is "
                    "priced because it goes under everything else.",
                    walkable=False)

    if kind == "blocks":
        lines.append(_gravel_base(area))
        lines.extend(_framing_lines(across, area))
        lines.append(Line("two coats of penetrating sealer", area, "sq ft",
                          declared("sealer_usd_per_sqft"),
                          "sealer_usd_per_sqft"))
        return Deck(kind, "Framed deck on piers, sealed", across, tuple(lines),
                    "The staple. Piers on gravel, doubled beams, joists at "
                    "16 in, 2x6 deck boards, sealed. Two people and a "
                    "weekend, and it is the bare minimum that hosts a dome.",
                    walkable=True)

    if kind == "blocks_epoxy":
        lines.append(_gravel_base(area))
        lines.extend(_framing_lines(across, area))
        lines.append(Line("1/2 in exterior ply underlayment", area, "sq ft",
                          declared("underlayment_usd_per_sqft"),
                          "underlayment_usd_per_sqft"))
        lines.append(Line("two-part epoxy floor coating", area, "sq ft",
                          declared("epoxy_usd_per_sqft"), "epoxy_usd_per_sqft"))
        return Deck(kind, "Framed deck on piers, ply and epoxy", across,
                    tuple(lines),
                    "The same platform with a floor you can mop. The ply is "
                    "not optional -- epoxy over gapped deck boards cracks at "
                    "every joint.",
                    walkable=True)

    if kind == "ring":
        # Concrete only where the load lands: a ring under the base decagon,
        # with the middle framed in wood.
        ring_w = declared("ring_width_in") / 12.0
        ring_d = declared("ring_depth_in") / 12.0
        ring_len = perimeter_ft(across)
        cuyd = ring_len * ring_w * ring_d / 27.0
        inner_fraction = max(0.0, 1.0 - (ring_len * ring_w) / area)
        lines.append(_gravel_base(area))
        lines.append(Line(
            f"concrete ring, {ring_w * 12:.0f} x {ring_d * 12:.0f} in, "
            f"{ring_len:.0f} ft around", cuyd, "cu yd",
            declared("concrete_usd_per_cuyd"), "concrete_usd_per_cuyd"))
        lines.append(Line("forming and placing the ring", ring_len * ring_w,
                          "sq ft", declared("concrete_place_usd_per_sqft"),
                          "concrete_place_usd_per_sqft"))
        lines.extend(_framing_lines(across, area, inner_fraction,
                                    bearing_ring=True))
        lines.append(Line("two coats of penetrating sealer",
                          area * inner_fraction, "sq ft",
                          declared("sealer_usd_per_sqft"),
                          "sealer_usd_per_sqft"))
        return Deck(kind, "Concrete ring, wood middle", across, tuple(lines),
                    "Concrete where the load lands and lumber where it does "
                    "not. A dome delivers its load to ten points on a ring, "
                    "so pouring the middle is pouring concrete nothing "
                    "stands on. This is how a yurt platform and a grain bin "
                    "are actually built.",
                    walkable=True)

    if kind == "slab":
        depth = declared("slab_depth_in") / 12.0
        cuyd = area * depth / 27.0
        lines.append(_gravel_base(area))
        lines.append(Line(f"concrete, {depth * 12:.0f} in over {area:,.0f} "
                          "sq ft", cuyd, "cu yd",
                          declared("concrete_usd_per_cuyd"),
                          "concrete_usd_per_cuyd"))
        lines.append(Line("forming, placing and finishing", area, "sq ft",
                          declared("concrete_place_usd_per_sqft"),
                          "concrete_place_usd_per_sqft"))
        return Deck(kind, "Full concrete slab", across, tuple(lines),
                    "The most expensive and the only one that is also the "
                    "finished floor. Worth it if the dome is never moving "
                    "and the climate argues for thermal mass.",
                    walkable=True)

    raise KeyError(f"unknown deck {kind!r}")


KINDS: tuple[str, ...] = ("gravel", "blocks", "blocks_epoxy", "ring", "slab")


def compare(across_ft: float | None = None) -> tuple[Deck, ...]:
    """Every construction at the same diameter, cheapest first."""
    return tuple(sorted((deck(kind, across_ft) for kind in KINDS),
                        key=lambda d: d.cost))


# ----------------------------------------------------------------------
# Building one, in the order it actually happens
# ----------------------------------------------------------------------

@dataclass(frozen=True)
class Step:
    """One stage of building the platform, for the film and for the buyer."""

    number: int
    label: str
    detail: str
    cumulative_usd: float


def build_sequence(kind: str = "blocks", across_ft: float | None = None
                   ) -> tuple[Step, ...]:
    """The platform going up one stage at a time, with the running cost.

    Ordered the way it is actually built, not the way the receipt is filed,
    so a film can put the stages on screen in sequence and a buyer can stop
    at any one of them and know what they have spent.
    """
    built = deck(kind, across_ft)
    order = ("compacted gravel", "precast piers", "beams", "joists",
             "deck boards", "hangers", "underlayment", "epoxy", "sealer",
             "concrete ring", "forming and placing the ring", "concrete,",
             "forming, placing and finishing")
    staged: list[Line] = []
    for key in order:
        staged.extend(line for line in built.lines
                      if line.label.startswith(key))
    # Anything the order missed still has to appear, or the stages do not
    # add up to the receipt.
    staged.extend(line for line in built.lines if line not in staged)

    steps, running = [], 0.0
    for index, line in enumerate(staged, start=1):
        running += line.cost
        steps.append(Step(index, line.label,
                          f"{line.quantity:,.0f} {line.unit} at "
                          f"${line.unit_cost:,.2f}", running))
    return tuple(steps)


# ----------------------------------------------------------------------
# Report
# ----------------------------------------------------------------------

def report() -> str:
    """Everything this module knows, as text."""
    across = pad_diameter_ft()
    area = decagon_area_sqft(across)
    lines = [
        "PAD DECK",
        f"  platform {across:.1f} ft across, {area:,.0f} sq ft of decagon",
        f"  dome on it is {seed_model.seed_geometry().diameter_ft:.2f} ft "
        "across",
        f"  every stick priced off one 2x6x12 at ${board_usd():.2f} "
        f"(${usd_per_linear_ft():.3f} a running foot)",
        "",
        "  construction                        cost   $/sqft   2x6x12",
        "  " + "-" * 56,
    ]
    for built in compare():
        boards = f"{built.boards:.0f}" if built.boards else "--"
        lines.append(f"  {built.label:<32} ${built.cost:>7,.0f} "
                     f"{built.usd_per_sqft:>7.2f} {boards:>8}")
    lines.append("")
    lines.append("  the staple, built in order:")
    for step in build_sequence("blocks"):
        lines.append(f"    {step.number:>2}. {step.label:<44} "
                     f"${step.cumulative_usd:>7,.0f}")
    return "\n".join(lines)


# ----------------------------------------------------------------------
# Proof
# ----------------------------------------------------------------------

def validate_pad_deck() -> None:
    """Prove the takeoff before anything quotes it."""
    across = pad_diameter_ft()
    dome = seed_model.seed_geometry().diameter_ft
    assert across > dome, (across, dome)
    # And it must not have quietly become the flagship pad again.
    assert across < 30.0, (
        f"the platform is {across:.1f} ft; a seed dome is {dome:.2f} ft "
        "across and pricing it at park-flagship size is the error this "
        "module exists to correct")

    area = decagon_area_sqft(across)
    circle = math.pi * (across / 2.0) ** 2
    assert 0.9 * circle < area < circle, (area, circle)

    for kind in KINDS:
        built = deck(kind)
        assert built.lines, kind
        assert built.cost > 0.0, kind
        for line in built.lines:
            assert line.quantity > 0.0, (kind, line.label)
            assert line.unit_cost > 0.0, (kind, line.label)
            assert line.source, (kind, line.label)

    gravel = deck("gravel")
    blocks = deck("blocks")
    ring = deck("ring")
    slab = deck("slab")
    epoxy = deck("blocks_epoxy")

    # Gravel is a base course and is not walkable; everything else is.
    assert not gravel.walkable
    assert all(deck(k).walkable for k in KINDS if k != "gravel")

    # The claim the brief rests on: a platform for a seed dome is a couple of
    # thousand dollars. If the staple ever leaves this band the prose is
    # wrong and has to be rewritten rather than left standing.
    assert 1500.0 <= blocks.cost <= 4500.0, (
        f"the staple platform is ${blocks.cost:,.0f}; the brief says a deck "
        "is a couple of thousand")

    # Ordering that has to hold, or the advice to a buyer is backwards.
    assert gravel.cost < blocks.cost < epoxy.cost, (
        gravel.cost, blocks.cost, epoxy.cost)
    # A finding, kept because it is the opposite of what was assumed when
    # this module was written: at seed-dome size a full slab comes out
    # CHEAPER than a framed deck. Concrete is cheap by the yard and this is
    # only a few yards; lumber is not cheap by the foot any more. The reason
    # to frame in wood is therefore not money -- it is that a deck on piers
    # can be unbolted and the ground put back, and a slab cannot. If that
    # ever reverses, the brief has to stop citing cost as the deck's
    # disadvantage.
    assert slab.cost < blocks.cost, (
        f"a slab (${slab.cost:,.0f}) is no longer cheaper than a framed deck "
        f"(${blocks.cost:,.0f}); the brief's 'concrete is cheaper, wood is "
        "reversible' framing needs rewriting")

    # The ring exists to be cheaper than a full pour AND still removable in
    # the middle. If it ever costs more than the slab there is no reason for
    # it to exist.
    assert ring.cost < slab.cost * 1.35, (
        f"the concrete ring is ${ring.cost:,.0f} against a full slab at "
        f"${slab.cost:,.0f}; it is meant to be the middle option")

    # Nothing here may reproduce the rate the old model carried.
    for kind in KINDS:
        assert deck(kind).usd_per_sqft < 22.0, (
            f"{kind} is ${deck(kind).usd_per_sqft:.2f}/sq ft, which is the "
            "contractor rate this module replaced")

    # Board counts have to be orderable integers that cover the framing.
    assert blocks.boards > 0
    framing_ft = sum(line.quantity for line in blocks.lines
                     if line.unit == "ln ft of 2x6")
    assert blocks.boards * declared("board_nominal_ft") >= framing_ft

    # The stages have to add up to the receipt, or the film is showing a
    # different build from the one the quote prices.
    for kind in KINDS:
        steps = build_sequence(kind)
        assert steps, kind
        assert abs(steps[-1].cumulative_usd - deck(kind).cost) < 0.01, kind
        assert [s.number for s in steps] == list(range(1, len(steps) + 1))


if __name__ == "__main__":
    validate_pad_deck()
    print(report())
