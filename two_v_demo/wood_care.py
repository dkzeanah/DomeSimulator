"""The wedge as wood: drying it, charring it, oiling it, and the metal beside it.

The frame is green pine split into 45-degree sectors, and three things follow
from that which the geometry alone does not say:

* **it moves as it dries.** Wood shrinks about twice as much round the rings
  as across them, so a sector's angle *closes* as it dries. The seam's V is
  the sector angle less the fold (:mod:`two_v_demo.channel_facts`), so a key
  fitted green is loose by the same amount once the frame is dry
  (:func:`sector_after_drying`). The same freedom is why a split wedge checks
  less than a squared, boxed-heart timber: it can close its angle instead of
  tearing.
* **it is finished on the outside only.** The bark face can be charred
  (yakisugi) and oiled; the two sawn faces carry the key, the bolts and the
  seam's air, and are left bare until the wood is dry (:func:`finish`).
* **the metal in the seam has to agree with itself.** Aluminium and copper
  liners, stainless bolts and wet condensate make a battery unless the pairs
  are chosen (:func:`galvanic`), and a metal liner grows and shrinks against
  the wood beside it (:func:`expansion`).

Constants are ``standard`` (a handbook value, with the book), ``nominal`` or
``estimate`` / ``assumption`` with a reason, in :data:`CONSTANTS`.

    py -3.12 -m two_v_demo.wood_care
"""

from __future__ import annotations

import math
from dataclasses import dataclass

from . import channel_facts as cf
from . import seam_climate as scl

MM_PER_IN = 25.4
M3_PER_CUFT = 0.028316846592
KG_PER_LB = 0.45359237
LITRES_PER_GAL = 3.785411784


CONSTANTS: tuple[tuple[str, float, str, str, str], ...] = (
    # -- how pine moves ------------------------------------------------
    ("fibre_saturation", 0.30, "kg/kg", "standard",
     "wood does not shrink until its moisture falls below about 30% (USDA Wood Handbook)"),
    ("shrink_radial", 0.048, "-", "standard",
     "loblolly pine, green to oven-dry, across the rings (USDA Wood Handbook, Table 4-3)"),
    ("shrink_tangential", 0.074, "-", "standard",
     "loblolly pine, green to oven-dry, round the rings (same table)"),
    ("board_thick_in", 1.5, "in", "nominal", "a dressed two-by, for comparison"),
    # -- the finish ------------------------------------------------------
    ("char_mm", 3.0, "mm", "assumption",
     "a single-pass yakisugi char, the middle of the usual 2 to 4 mm"),
    ("oil_m2_per_l", 8.0, "m2/L", "estimate",
     "raw linseed oil on rough-sawn or charred softwood, first coat; planed wood "
     "takes 10 to 20 m2 a litre, rough wood drinks more"),
    ("oil_coats", 3.0, "coats", "assumption",
     "thin coats, each wiped off after it soaks in, a day or more apart"),
    # -- the metal -----------------------------------------------------
    ("k_aluminium", 205.0, "W/m K", "standard", "thermal conductivity"),
    ("k_copper", 385.0, "W/m K", "standard", "thermal conductivity"),
    ("k_stainless", 16.0, "W/m K", "standard", "thermal conductivity, 304"),
    ("k_petg", 0.20, "W/m K", "nominal", "thermal conductivity of the printed key"),
    ("k_pine", 0.12, "W/m K", "standard", "thermal conductivity across the grain"),
    ("alpha_aluminium", 23e-6, "1/K", "standard", "linear thermal expansion"),
    ("alpha_copper", 17e-6, "1/K", "standard", "linear thermal expansion"),
    ("alpha_pine", 4e-6, "1/K", "standard", "linear thermal expansion along the grain"),
    ("seam_swing_k", 50.0, "K", "assumption",
     "a seam's metal liner seeing minus ten in a winter night and forty on a "
     "summer afternoon under the cap"),
    ("wet_limit_v", 0.15, "V", "standard",
     "largest anodic-index difference allowed between metals that stay wet "
     "(MIL-STD-889 practice for harsh service); 0.25 V indoors, 0.50 V dry"),
)
C = {name: value for name, value, _u, _k, _w in CONSTANTS}

ANODIC_INDEX_V: dict[str, float] = {
    # MIL-STD-889 anodic index, as tabulated in engineering handbooks (standard).
    "copper": 0.35,
    "stainless (passive 304/316)": 0.50,
    "aluminium": 0.90,
    "galvanised steel": 1.20,
}


# ----------------------------------------------------------------------
# Drying
# ----------------------------------------------------------------------

def shrinkage_fraction(mc: float) -> float:
    """Share of total green-to-oven-dry shrinkage reached at moisture ``mc``."""
    return max(0.0, (C["fibre_saturation"] - mc) / C["fibre_saturation"])


@dataclass(frozen=True)
class Drying:
    mc: float                  # the moisture the frame dries to
    sector_green_deg: float
    sector_dry_deg: float
    close_deg: float           # how far each wedge's angle closes
    depth_green_in: float
    depth_dry_in: float
    gap_green_deg: float       # the tighter seam's V, as cut green
    gap_dry_deg: float         # and once the frame is dry
    opening_green_in: float    # the V's width at the room side
    opening_dry_in: float
    thick_in: float            # thickest point of a wedge: its inscribed circle
    log_in: float
    times_faster_than_log: float
    times_slower_than_board: float
    water_lb: float            # water the frame loses, green to this moisture
    water_gal: float

    @property
    def face_tilt_in(self) -> float:
        """How far each sawn face swings at the room side as the angle opens.

        The width barely changes (the faces shorten as they tilt), but a key
        cut to the green V now bears on one edge only."""
        return self.depth_dry_in * math.sin(math.radians(self.close_deg / 2))


def sector_after_drying(mc: float | None = None) -> Drying:
    """A green 45-degree sector, dried: its angle closes and the V opens."""
    import seed_model
    import seed_world

    mc = scl.C["mc_target"] if mc is None else mc
    f = shrinkage_fraction(mc)
    g = seed_world.geometry()
    theta = 360.0 / seed_model.SEED_RADIAL_SPLITS
    r = g.member_depth_in
    tang, rad = C["shrink_tangential"] * f, C["shrink_radial"] * f
    theta_dry = theta * (1.0 - tang) / (1.0 - rad)
    close = theta - theta_dry
    tight = min(cf.seam_types(), key=lambda t: t.gap_deg)
    gap_dry = tight.gap_deg + close          # each face turns away by half of it
    depth_dry = r * (1.0 - rad)
    s = math.sin(math.radians(theta / 2))
    thick = 2 * r * s / (1 + s)
    log = 2 * r
    green_lb = g.member_volume_cuft * seed_model.declared("pine_green_lb_per_cuft")
    dry_kg_m3 = scl.C["pine_dry_density"] * (1.0 + mc)
    dry_lb = g.member_volume_cuft * M3_PER_CUFT * dry_kg_m3 / KG_PER_LB
    water = green_lb - dry_lb
    return Drying(mc, theta, theta_dry, close, r, depth_dry, tight.gap_deg, gap_dry,
                  2 * r * math.sin(math.radians(tight.gap_deg / 2)),
                  2 * depth_dry * math.sin(math.radians(gap_dry / 2)),
                  thick, log, (log / thick) ** 2, (thick / C["board_thick_in"]) ** 2,
                  water, water * KG_PER_LB / LITRES_PER_GAL)


# ----------------------------------------------------------------------
# The finish
# ----------------------------------------------------------------------

@dataclass(frozen=True)
class Finish:
    bark_m2: float             # the round outer faces: charred and oiled
    sawn_m2: float             # the two sawn faces of every member: left bare
    char_mm: float
    section_loss_pct: float    # of a member's cross-section, lost to the char
    oil_litres: float          # every coat, bark faces only
    oil_litres_all: float      # what it would take to oil the sawn faces too


def finish() -> Finish:
    import seed_model
    import seed_world

    g = seed_world.geometry()
    r_m = g.member_depth_in * MM_PER_IN / 1000.0
    theta = math.radians(360.0 / seed_model.SEED_RADIAL_SPLITS)
    length_m = g.member_stock_ft * 0.3048
    bark = r_m * theta * length_m
    sawn = 2 * r_m * length_m
    c = C["char_mm"] / 1000.0
    loss = (r_m * theta * c - theta * c * c / 2) / (theta * r_m * r_m / 2)
    per_coat = bark / C["oil_m2_per_l"]
    return Finish(bark, sawn, C["char_mm"], loss * 100, per_coat * C["oil_coats"],
                  (bark + sawn) / C["oil_m2_per_l"] * C["oil_coats"])


# ----------------------------------------------------------------------
# The metal
# ----------------------------------------------------------------------

def galvanic() -> list[tuple[str, str, float, bool]]:
    """Every pair of the seam's metals: difference, and whether it may stay wet."""
    names = list(ANODIC_INDEX_V)
    out = []
    for i, a in enumerate(names):
        for b in names[i + 1:]:
            d = abs(ANODIC_INDEX_V[a] - ANODIC_INDEX_V[b])
            out.append((a, b, d, d <= C["wet_limit_v"] + 1e-9))
    return out


def pair(a: str, b: str) -> tuple[float, bool]:
    for x, y, d, ok in galvanic():
        if {x, y} == {a, b}:
            return d, ok
    raise KeyError((a, b))


@dataclass(frozen=True)
class Expansion:
    seam_in: float
    aluminium_mm: float        # a liner's change in length over the swing
    copper_mm: float
    pine_mm: float
    slip_aluminium_mm: float   # what the liner moves against the wood


def expansion() -> Expansion:
    types = cf.seam_types()
    longest = max(t.length_in for t in types)
    mm = longest * MM_PER_IN
    dt = C["seam_swing_k"]
    al, cu, pine = (mm * C[k] * dt for k in ("alpha_aluminium", "alpha_copper", "alpha_pine"))
    return Expansion(longest, al, cu, pine, al - pine)


def conduction_ratio() -> dict:
    """How much more heat a metal liner carries than the key wall it replaces."""
    return {"aluminium_vs_petg": C["k_aluminium"] / C["k_petg"],
            "copper_vs_aluminium": C["k_copper"] / C["k_aluminium"],
            "stainless_vs_aluminium": C["k_stainless"] / C["k_aluminium"],
            "petg_vs_pine": C["k_petg"] / C["k_pine"]}


# ----------------------------------------------------------------------
# Report and checks
# ----------------------------------------------------------------------

def report() -> str:
    d = sector_after_drying()
    f = finish()
    e = expansion()
    out = ["THE WEDGE AS WOOD", "",
           f"dried to {d.mc * 100:.0f}%: sector {d.sector_green_deg:.2f} -> {d.sector_dry_deg:.2f} deg "
           f"(closes {d.close_deg:.2f}); depth {d.depth_green_in:.2f} -> {d.depth_dry_in:.2f} in",
           f"tight V {d.gap_green_deg:.2f} -> {d.gap_dry_deg:.2f} deg; opening "
           f"{d.opening_green_in:.3f} -> {d.opening_dry_in:.3f} in",
           f"thickest point {d.thick_in:.2f} in: dries {d.times_faster_than_log:.0f}x faster than "
           f"the round log, {d.times_slower_than_board:.1f}x slower than a two-by",
           f"water lost from the frame: {d.water_lb:,.0f} lb = {d.water_gal:,.0f} gal", "",
           f"bark faces {f.bark_m2:.1f} m2, sawn faces {f.sawn_m2:.1f} m2",
           f"{f.char_mm:.0f} mm char costs {f.section_loss_pct:.1f}% of the section",
           f"linseed, {C['oil_coats']:.0f} coats on the bark faces: {f.oil_litres:.1f} L "
           f"(every face: {f.oil_litres_all:.1f} L)", ""]
    out += [f"{a:<28} {b:<28} {dv:.2f} V {'ok wet' if ok else 'NOT when wet'}"
            for a, b, dv, ok in galvanic()]
    out += ["", f"a {e.seam_in:.0f} in liner over {C['seam_swing_k']:.0f} K: aluminium "
                f"{e.aluminium_mm:.2f} mm, copper {e.copper_mm:.2f} mm, pine {e.pine_mm:.2f} mm"]
    return "\n".join(out)


def validate_wood_care() -> None:
    d = sector_after_drying()
    # Tangential shrinkage beats radial, so the sector closes and the V opens.
    assert C["shrink_tangential"] > C["shrink_radial"]
    assert 0 < d.close_deg < 3 and d.gap_dry_deg > d.gap_green_deg
    assert d.opening_dry_in != d.opening_green_in
    # Green wood never shrinks above fibre saturation.
    assert shrinkage_fraction(0.35) == 0.0 and shrinkage_fraction(0.0) == 1.0
    # A wedge's thickest point is its inscribed circle, well under the log.
    assert d.thick_in < d.log_in / 2 and d.times_faster_than_log > 1
    assert d.water_lb > 0
    f = finish()
    assert 0 < f.section_loss_pct < 10 and f.oil_litres < f.oil_litres_all
    # The pairs the chapter warns about, and the one it allows.
    assert not pair("copper", "aluminium")[1]
    assert not pair("stainless (passive 304/316)", "aluminium")[1]
    assert pair("copper", "stainless (passive 304/316)")[1]
    e = expansion()
    assert e.aluminium_mm > e.copper_mm > e.pine_mm > 0


if __name__ == "__main__":
    validate_wood_care()
    print(report())
