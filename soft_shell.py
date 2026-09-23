"""The shower cap: a soft shell that grows, against a hard one that cannot.

The boatyard laminate is the single most expensive line in the dome --
$6,045 of glass, resin and gelcoat, about half the material cost of the whole
building. It is also the line that *stops the building improving*, and that
second problem is the more interesting one.

A laminated shell is made once at one size. The cavity behind it holds seven
quilted layers and then it is full: after that, insulating further means
either losing floor area on the inside or building a second shell outside the
first. Neither happens. So the hard shell quietly caps how good the building
is ever allowed to get.

The alternative modelled here is the owner's, and the image is his: **a shower
cap for the house.** From the frame outwards --

1. **wood panels on the outside face** of the frame, which is also the
   barrier to the weather. They are screwed from outside and pull *into* the
   frame, so gravity is working with the fixing rather than against a
   friction fit;
2. a **breather** over all of it -- one continuous vapour-permeable sheet,
   no seams to fail. It sheds the water that gets past the cap and it lets
   water vapour out, which is the whole reason it is not a poly sheet;
3. **quilted layers** of recycled fabric -- thrift-store blankets and
   clothing, quilted by the owner, a declared $50 a layer -- added one at a
   time over years;
4. a **rain-slick outer cap** pulled over the lot and strapped down. This is
   the ONLY watertight layer in the building.

The point is 4 over 3. A cap is a bag: when the stack under it gets thicker,
you buy a bigger bag. A rigid shell cannot do that, which is the whole
argument -- "stacking hats", where each hat has to be a size up from the last.

And the point of 2 being a breather rather than a sheet is the other half.
Two waterproof layers with insulation between them is a moisture trap: the
dew point lands in the fabric, and fabric that gets damp stops insulating
and starts rotting. One waterproof layer, on the outside, with everything
under it free to dry, is how a person dresses for cold and wet -- wool and
fleece under one shell -- and it is how this dome is dressed.

This module prices that, including the part that is easy to forget: **every
layer makes the next one bigger.** Area goes as the square of radius, so the
seventh hat is not the same price as the first. That arithmetic is here
rather than hand-waved, because it is the only thing that could make the
idea not work.

Nothing here decides geometry; the dome comes from :mod:`seed_model`.
"""

from __future__ import annotations

import math
from dataclasses import dataclass

import seed_model


# ----------------------------------------------------------------------
# Declared inputs
# ----------------------------------------------------------------------

EXTERNAL_CONSTANTS: tuple[tuple[str, float, str, str], ...] = (
    ("membrane_usd_per_sqft", 0.34, "USD/sq ft",
     "assumption: vapour-permeable building wrap, the grade sold in 9-ft "
     "rolls for house sheathing. NOT a poly sheet -- it has to let vapour "
     "out, or the quilt over it is a moisture trap and the building rots "
     "from the inside. One piece, lapped, no seams over the dome"),
    ("membrane_perms", 10.0, "US perms",
     "assumption: the permeance of that wrap. Anything under 1 perm is a "
     "vapour barrier and would put this layer back in the trap it exists "
     "to avoid. Stated so a substitute can be checked against it"),
    ("membrane_life_years", 12.0, "years",
     "assumption: how long that wrap lasts under it, protected from UV by "
     "everything stacked on top of it. Exposed it would be a third of that"),
    ("cap_vent_gap_in", 0.75, "in",
     "assumption: the drained, vented gap between the quilt and the cap, "
     "held open by the strapping. Without it the cap lies on the quilt and "
     "the breather has nowhere to breathe to"),
    ("cap_panel_min_each", 11.0, "minutes each",
     "assumption: hanging one outer wood panel on its four threaded "
     "inserts, working from outside. Measured against the insert-setting "
     "time in fitout_wet, which is the same operation from the other side"),
    ("cap_breather_min_per_sqft", 0.55, "minutes/sq ft",
     "assumption: lapping and taping the breather over the panels. It is "
     "housewrap over a faceted surface, which is slower than a wall and "
     "faster than a boat"),
    ("cap_strap_hours", 3.5, "hours",
     "assumption: pulling the cap over, hemming it to the rim and "
     "tensioning ten ratchet straps to their ground anchors. Two people"),
    ("cap_usd_per_sqft", 1.45, "USD/sq ft",
     "assumption: coated ripstop with a UV-stable face -- the rain-slick "
     "outer. Bought as a made cover with a hem and grommets"),
    ("cap_life_years", 8.0, "years",
     "assumption: how long the outer cap lasts before UV takes it. It is "
     "the sacrificial layer and it is meant to be replaced"),
    ("cap_seam_usd_per_ft", 1.90, "USD/ft",
     "assumption: welded seam on the made cover, per running foot of seam"),
    ("tiedown_usd_each", 26.00, "USD each",
     "assumption: a webbing strap, ratchet and ground anchor at each base "
     "vertex. A fabric cap has no stiffness of its own, so uplift is "
     "carried here rather than by the shell"),
    ("layer_thickness_in", 1.25, "in",
     "measured: how thick one quilted layer of recycled fabric compresses "
     "to under a strapped cap. It is what makes the next cap bigger"),
    ("blanket_quilt_usd_per_layer", 50.0, "USD/layer",
     "assumption: one quilted layer made of thrift-store blankets and "
     "recycled clothing -- the fabric is a waste stream, and the owner does "
     "the quilting. What a $50 layer buys, and the reason the soft shell is "
     "the first choice before the yard-priced quilt"),
    ("outer_panel_usd_per_sqft", 2.40, "USD/sq ft",
     "borrowed: seed_model's hard_panel_usd_per_sqft. The panel that used "
     "to compression-fit from outside becomes the weather barrier, screwed "
     "through into the frame"),
    ("panel_insert_usd_each", 1.35, "USD each",
     "assumption: a threaded insert set into the wedge face, four per bay, "
     "that a panel screw pulls against. What makes the panel removable "
     "without chewing the wood out"),
    ("panel_inserts_per_bay", 4.0, "each",
     "assumption: four fixings per triangular panel, one near each corner "
     "and one at the middle of the longest edge"),
)

CONSTANTS: dict[str, float] = {name: value
                               for name, value, _u, _w in EXTERNAL_CONSTANTS}


def declared(name: str) -> float:
    if name in CONSTANTS:
        return CONSTANTS[name]
    return seed_model.declared(name)


# ----------------------------------------------------------------------
# Stacking hats: every layer makes the next one bigger
# ----------------------------------------------------------------------

def dome_radius_ft() -> float:
    """The frame's own outer radius, which every hat is measured from."""
    return seed_model.seed_geometry().diameter_ft / 2.0


def envelope_sqft(extra_in: float = 0.0) -> float:
    """Surface of a hemisphere standing ``extra_in`` proud of the frame.

    A hemisphere is 2*pi*r^2. The point of the function is the square: add an
    inch and you do not add an inch of fabric, you add a ring of it, and by
    the seventh layer that ring is what you are paying for.
    """
    radius = dome_radius_ft() + extra_in / 12.0
    return 2.0 * math.pi * radius * radius


def hat_sizes(layers: int) -> tuple[float, ...]:
    """The area of the outer cap with 0, 1, 2 ... ``layers`` under it."""
    thickness = declared("layer_thickness_in")
    return tuple(envelope_sqft(index * thickness)
                 for index in range(layers + 1))


def growth_fraction(layers: int) -> float:
    """How much bigger the last hat is than the first. The cost of stacking."""
    sizes = hat_sizes(layers)
    return sizes[-1] / sizes[0] - 1.0 if sizes[0] else 0.0


# ----------------------------------------------------------------------
# The stack, priced
# ----------------------------------------------------------------------

@dataclass(frozen=True)
class Line:
    label: str
    quantity: float
    unit: str
    unit_cost: float
    source: str

    @property
    def cost(self) -> float:
        return self.quantity * self.unit_cost


@dataclass(frozen=True)
class SoftShell:
    """One soft shell, at one number of insulating layers."""

    layers: int
    lines: tuple[Line, ...]

    @property
    def cost(self) -> float:
        return sum(line.cost for line in self.lines)

    @property
    def cap_sqft(self) -> float:
        return hat_sizes(self.layers)[-1]

    @property
    def added_r(self) -> float:
        geometry = seed_model.seed_geometry()
        return seed_model.quilt_ladder(max(1, self.layers), geometry).added_r \
            if self.layers else 0.0


def _panel_lines() -> list[Line]:
    """Wood panels on the outside face, screwed into threaded inserts."""
    geometry = seed_model.seed_geometry()
    bays = geometry.panel_count if hasattr(geometry, "panel_count") else 40.0
    area = geometry.panel_sqft
    inserts = bays * declared("panel_inserts_per_bay")
    return [
        Line("outer wood panels, one per bay", area, "sq ft",
             declared("outer_panel_usd_per_sqft"), "outer_panel_usd_per_sqft"),
        Line("threaded inserts in the wedge faces", inserts, "each",
             declared("panel_insert_usd_each"), "panel_insert_usd_each"),
    ]


def soft_shell(layers: int = 0, quilt: str = "blanket") -> SoftShell:
    """The whole cap stack at ``layers`` of quilted insulation.

    ``quilt`` prices the insulation layers. ``blanket`` (the first choice)
    is thrift-store blankets and recycled clothing quilted by the owner --
    one declared $50 layer of waste-stream fabric. ``yard`` is the
    purchased quilt fabric priced per square foot, which is what the
    hard-shell comparison and the park model use.
    """
    geometry = seed_model.seed_geometry()
    cap_area = hat_sizes(layers)[-1]
    membrane_area = hat_sizes(0)[0]

    lines = _panel_lines()
    lines.append(Line("breather over the panels (vapour-permeable)",
                      membrane_area, "sq ft",
                      declared("membrane_usd_per_sqft"),
                      "membrane_usd_per_sqft"))

    if layers > 0:
        if quilt == "blanket":
            for index in range(layers):
                lines.append(Line(
                    f"blanket-quilted layer {index + 1} "
                    f"(recycled clothing)", 1.0, "layer",
                    declared("blanket_quilt_usd_per_layer"),
                    "blanket_quilt_usd_per_layer"))
        else:
            ladder = seed_model.quilt_ladder(layers, geometry)
            # Each layer is bought at the size it actually has to be, not the
            # size of the first one. This is the stacking-hats cost.
            sizes = hat_sizes(layers)
            per_sqft = ladder.usd_per_sqft_layer
            for index in range(layers):
                lines.append(Line(
                    f"quilted layer {index + 1}", sizes[index], "sq ft",
                    per_sqft, "quilt_ladder"))

    # The outer cap is sized for the finished stack, and its seam runs the
    # ten base edges plus the ten meridians it is panelled from.
    seam_ft = geometry.base_perimeter_ft + 10.0 * dome_radius_ft() * 1.6
    lines.append(Line("rain-slick outer cap", cap_area, "sq ft",
                      declared("cap_usd_per_sqft"), "cap_usd_per_sqft"))
    lines.append(Line("welded seams on the cap", seam_ft, "ft",
                      declared("cap_seam_usd_per_ft"), "cap_seam_usd_per_ft"))
    lines.append(Line("strap, ratchet and ground anchor per base vertex",
                      float(geometry.base_sides), "each",
                      declared("tiedown_usd_each"), "tiedown_usd_each"))
    return SoftShell(layers, tuple(lines))


# ----------------------------------------------------------------------
# Against the hard shell
# ----------------------------------------------------------------------

@dataclass(frozen=True)
class Comparison:
    layers: int
    soft_usd: float
    hard_usd: float
    soft_r: float
    hard_r: float

    @property
    def saving(self) -> float:
        return self.hard_usd - self.soft_usd


def hard_equivalent(layers: int) -> float:
    """The laminated shell plus the same number of quilted layers.

    The hard shell's layers go in the *cavity*, so they do not grow -- which
    is exactly why it runs out of room. Up to the cavity's capacity this is
    the fair comparison; past it, see :func:`cavity_limit`.
    """
    geometry = seed_model.seed_geometry()
    shell = seed_model.shell_group(geometry, "boatyard").cost
    bays = seed_model.envelope_group(geometry).cost
    quilt = seed_model.quilt_group(layers, geometry).cost if layers else 0.0
    return shell + bays + quilt


def cavity_limit() -> int:
    """How many quilted layers fit in the hard shell's cavity before it is full.

    The cavity is as deep as the member. Past this the rigid shell has no
    answer that does not cost floor area or a second shell.
    """
    depth_in = seed_model.seed_geometry().member_depth_in
    return int(depth_in // declared("layer_thickness_in"))


def compare(max_layers: int = 12, quilt: str = "blanket"
            ) -> tuple[Comparison, ...]:
    """Soft against hard, layer by layer, including past the cavity's limit.

    ``quilt`` chooses how the soft side's layers are priced: ``blanket``
    (thrift blankets and clothing, $50 a layer -- the campaign's first
    choice) or ``yard`` (purchased quilt fabric per square foot).
    """
    geometry = seed_model.seed_geometry()
    out = []
    for layers in range(max_layers + 1):
        soft = soft_shell(layers, quilt)
        added = (seed_model.quilt_ladder(layers, geometry).added_r
                 if layers else 0.0)
        capped = min(layers, cavity_limit())
        hard_added = (seed_model.quilt_ladder(capped, geometry).added_r
                      if capped else 0.0)
        out.append(Comparison(layers, soft.cost, hard_equivalent(capped),
                              added, hard_added))
    return tuple(out)


# ----------------------------------------------------------------------
# What it costs to keep, and what is wrong with it
# ----------------------------------------------------------------------

def lifetime_usd_per_year(layers: int = 3, years: float = 30.0) -> tuple[float, float]:
    """Thirty years of each shell, because the soft one is replaced and the
    hard one is not.

    A gelcoat hull is a fifty-year object. A polymer cap is a sacrificial
    layer with a UV clock on it. Comparing the two on purchase price alone
    flatters the cap, so this does not.
    """
    soft = soft_shell(layers)
    cap = next(line for line in soft.lines
               if line.label.startswith("rain-slick"))
    membrane = next(line for line in soft.lines
                    if line.label.startswith("breather"))
    replacements = (math.ceil(years / declared("cap_life_years")) - 1) * cap.cost
    replacements += (math.ceil(years / declared("membrane_life_years")) - 1
                     ) * membrane.cost
    return ((soft.cost + replacements) / years,
            hard_equivalent(min(layers, cavity_limit())) / years)


CONCERNS: tuple[tuple[str, str], ...] = (
    ("It is not structural.",
     "The laminated shell was a stressed skin; a strapped cap is not. Uplift "
     "is carried by ten ground anchors and the frame alone, so the frame has "
     "to be good for the whole wind load rather than sharing it."),
    ("The outer layer is sacrificial and the arithmetic has to say so.",
     f"A cap is assumed to last {declared('cap_life_years'):.0f} years and "
     f"the membrane {declared('membrane_life_years'):.0f}. A gelcoat hull "
     "outlives both several times over, which is why this module prices "
     "thirty years and not one purchase."),
    ("The breather has to actually breathe, and the cap has to be vented.",
     "This is the design that replaced a real defect, so it is worth saying "
     "what it now depends on. The cap is the only watertight layer, and "
     "everything under it dries outward through the breather into a vented "
     "gap the strapping holds open. Substitute a poly sheet for the "
     "breather, or strap the cap down flat onto the quilt, and the moisture "
     "trap is back: the dew point lands in the fabric and the fabric rots. "
     "The seam-duct airflow still helps and is still unproven. The "
     "difference is that the building no longer depends on it."),
    ("It looks like a tarp.",
     "That is a planning objection, a resale problem and a neighbour "
     "problem, and no amount of arithmetic answers it."),
)


def report() -> str:
    lines = [
        "SOFT SHELL -- the shower cap",
        f"  frame {dome_radius_ft() * 2:.2f} ft across, "
        f"{envelope_sqft():,.0f} sq ft at the skin",
        f"  one quilted layer is {declared('layer_thickness_in'):.2f} in "
        "thick, so every hat is a size up",
        f"  a blanket-quilted layer is a declared "
        f"${declared('blanket_quilt_usd_per_layer'):,.0f} of thrift fabric",
        f"  the hard shell's cavity holds {cavity_limit()} layers and then "
        "it is full",
        "",
        "  layers   soft     hard    saving    soft R   hard R   cap sq ft",
        "  " + "-" * 62,
    ]
    for row in compare(10):
        cap = soft_shell(row.layers).cap_sqft
        lines.append(
            f"  {row.layers:>4}  ${row.soft_usd:>7,.0f} ${row.hard_usd:>7,.0f} "
            f"${row.saving:>8,.0f}  {row.soft_r:>7.1f}  {row.hard_r:>6.1f}  "
            f"{cap:>8,.0f}")
    yard_first = soft_shell(1, quilt="yard").cost - soft_shell(0).cost
    lines.append(f"  (a yard-priced quilted layer would cost "
                 f"${yard_first:,.0f} at the first size instead)")
    grow = growth_fraction(7) * 100.0
    lines.append("")
    lines.append(f"  seven layers makes the outer cap {grow:.1f}% bigger "
                 "than the first one")
    soft_year, hard_year = lifetime_usd_per_year(3)
    lines.append(f"  over 30 years, replacements in: soft ${soft_year:,.0f}/yr "
                 f"against hard ${hard_year:,.0f}/yr")
    lines.append("")
    lines.append("  AND THE PROBLEMS")
    for title, detail in CONCERNS:
        lines.append(f"    - {title}")
        lines.append(f"      {detail}")
    return "\n".join(lines)


# ----------------------------------------------------------------------
# Proof
# ----------------------------------------------------------------------

def validate_soft_shell() -> None:
    """Prove the stack before anything quotes it."""
    assert cavity_limit() >= 2, cavity_limit()

    # Stacking hats: every hat must be strictly bigger than the one under it,
    # or the central claim of this module is a picture rather than a fact.
    sizes = hat_sizes(7)
    assert len(sizes) == 8
    assert all(b > a for a, b in zip(sizes, sizes[1:])), sizes
    assert growth_fraction(7) > 0.05, growth_fraction(7)

    for layers in (0, 1, 7, 12):
        shell = soft_shell(layers)
        assert shell.lines
        assert shell.cost > 0.0
        for line in shell.lines:
            assert line.quantity > 0.0, line.label
            assert line.unit_cost > 0.0, line.label
            assert line.source, line.label
        # The blanket-quilted layers are one declared $50 layer each.
        quilted = [l for l in shell.lines if l.label.startswith("blanket-")]
        assert len(quilted) == layers, (layers, len(quilted))
        # The yard-priced layers must be bought at growing sizes.
        yard = soft_shell(layers, quilt="yard")
        yard_quilted = [l for l in yard.lines if l.label.startswith("quilted")]
        assert len(yard_quilted) == layers, (layers, len(yard_quilted))
        assert all(b.quantity > a.quantity
                   for a, b in zip(yard_quilted, yard_quilted[1:])), layers
        # A blanket layer is the declared flat price, wherever the stack is.
        if layers:
            blanket = next(l for l in shell.lines
                           if l.label.startswith("blanket-"))
            assert blanket.cost == declared("blanket_quilt_usd_per_layer")

    # The claim worth making: the soft shell is cheaper to buy. If it ever
    # stops being, the argument for it is only the growth and the prose has
    # to be rewritten.
    bare = compare(0)[0]
    assert bare.soft_usd < bare.hard_usd, (bare.soft_usd, bare.hard_usd)

    # Past the cavity's limit the hard shell stops gaining R and the soft one
    # does not. That divergence is the whole point.
    rows = compare(cavity_limit() + 3)
    last = rows[-1]
    assert last.soft_r > last.hard_r, (last.soft_r, last.hard_r)
    assert rows[cavity_limit()].hard_r == last.hard_r, "the cavity never filled"

    # Thirty years with replacements must not quietly still be free. The
    # module exists to make that cost visible, so it has to be non-zero.
    soft_year, hard_year = lifetime_usd_per_year(3)
    assert soft_year > 0.0 and hard_year > 0.0
    assert soft_year * 30.0 > soft_shell(3).cost, (
        "thirty years of a sacrificial cap costs no more than buying it once")

    assert len(CONCERNS) >= 4
    for title, detail in CONCERNS:
        assert title and detail


if __name__ == "__main__":
    validate_soft_shell()
    print(report())
