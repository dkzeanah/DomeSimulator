"""Argument 8 of 10: financing, already modeled.

Standardized financing is one of the six requirements for a dome to
work as a manufactured product (see dome_case_manufacturing.py), and
one of presentation.txt's explicit "what must be solved" items. This
argument shows it's not an open question for this project — it's a
computed number, for every product tier the software sells.
"""

from __future__ import annotations

import al_build as ab
from presenter.script import OverlayPanel, Presentation, Scene, Shot
from presentations._numbers import HERO_MONTHLY, HERO_PRICE, R

FIELD = "a calm open field in daylight"
WORLD = (("dome", {"radius": R, "skin_alpha": 0.16}),)

_TIERS = {}
for _key in ("home", "shed", "greenhouse", "shelter"):
    _t = ab.DOME_TYPES[_key]
    _r_mid = sum(_t.radius_range) / 2.0
    _spec = ab.DomeSpec(dtype=_key, radius=_r_mid,
                        frequency=_t.freq_choices[0], serial=1,
                        name="representative")
    _TIERS[_key] = {"name": _t.name, "price": _spec.sale_price,
                    "monthly": _spec.monthly_payment}


def build() -> Presentation:
    scenes = (
        Scene(
            "hook", "The requirement that kills more pitches than "
                   "engineering does",
            FIELD,
            world=WORLD,
            shots=(
                Shot("thesis", 9.0, lens="wide", focus="dome",
                     yaw=-40, pitch=16, orbit=8,
                     caption="A buyer needs a lender before they need "
                             "an argument about geometry",
                     panel=OverlayPanel(
                         title="WHY FINANCING IS THE HARD PART",
                         bullets=("A structurally perfect dome with no "
                                  "lender behind it doesn't sell",
                                  "presentation.txt lists standardized "
                                  "financing as one of the things that "
                                  "must be solved before this scales",
                                  "This project answers it with a "
                                  "computed number, not a promise"),
                         position="right"),
                     narration=(
                         "A structurally perfect dome with no lender "
                         "willing to write a loan against it doesn't "
                         "sell. Standardized financing is on this "
                         "project's own list of things that must be "
                         "solved before any of this scales.",
                         "So here is the answer, computed rather than "
                         "promised: the same buy-here-pay-here math "
                         "this project's sales office actually uses.",
                     )),
            ),
        ),
        Scene(
            "the_model", "The actual computation, one dome",
            FIELD,
            world=WORLD,
            shots=(
                Shot("terms", 9.0, lens="wide", focus="dome",
                     yaw=70, pitch=16, orbit=8,
                     caption=f"${HERO_PRICE:,.0f} at "
                             f"{ab.ASSUMPTIONS['bhph_apr']*100:.1f}% "
                             f"APR over {ab.ASSUMPTIONS['bhph_term_months']} "
                             f"months",
                     panel=OverlayPanel(
                         title="THE TERMS",
                         stats=(("Sale price", f"${HERO_PRICE:,.0f}"),
                                ("Down payment",
                                 f"{ab.ASSUMPTIONS['bhph_down_fraction']*100:.0f}%"),
                                ("APR",
                                 f"{ab.ASSUMPTIONS['bhph_apr']*100:.1f}%"),
                                ("Term",
                                 f"{ab.ASSUMPTIONS['bhph_term_months']} "
                                 f"months")),
                         position="left"),
                     narration=(
                         f"One representative home dome, "
                         f"${HERO_PRICE:,.0f}. "
                         f"{ab.ASSUMPTIONS['bhph_down_fraction']*100:.0f} "
                         "percent down, "
                         f"{ab.ASSUMPTIONS['bhph_apr']*100:.1f} percent "
                         "APR, "
                         f"{ab.ASSUMPTIONS['bhph_term_months']} month "
                         "term — the same terms this project's own "
                         "sales office quotes in the interactive "
                         "simulator.",
                     )),
                Shot("payment", 8.5, lens="macro", focus="apex",
                     yaw=-30, pitch=28, orbit=6,
                     caption=f"${HERO_MONTHLY:,.0f} a month, computed, "
                             f"not guessed",
                     panel=OverlayPanel(
                         title="THE MONTHLY PAYMENT",
                         stats=(("Computed monthly payment",
                                 f"${HERO_MONTHLY:,.0f}"),),
                         bullets=("Standard amortization math over "
                                  "principal, rate, and term",
                                  "The same formula runs for every "
                                  "dome this software prices"),
                         position="right"),
                     narration=(
                         f"Run through standard amortization math, "
                         f"that comes to ${HERO_MONTHLY:,.0f} a month. "
                         "Not a marketing figure — the same "
                         "amortization formula runs identically for "
                         "every dome this software prices, every time.",
                     )),
            ),
        ),
        Scene(
            "across_tiers", "The same math, every product size",
            FIELD,
            world=WORLD,
            shots=(
                Shot("tiers", 10.0, lens="wide", focus="dome",
                     yaw=-100, pitch=18, orbit=8,
                     caption="Financing scales with the product, not "
                             "the other way around",
                     panel=OverlayPanel(
                         title="FOUR TIERS, FOUR COMPUTED PAYMENTS",
                         stats=tuple(
                             (v["name"],
                              f"${v['price']:,.0f} → "
                              f"${v['monthly']:,.0f}/mo")
                             for v in _TIERS.values()),
                         position="right"),
                     narration=(
                         "The same formula runs for every product tier "
                         "this software sells, from a storage shed to "
                         "a turnkey off-grid home — a different price, "
                         "the identical math, every time.",
                         "That consistency is the actual point: a "
                         "lender doesn't have to trust a new formula "
                         "for every size of dome that rolls off the "
                         "line.",
                     )),
            ),
        ),
        Scene(
            "close", "The lending world already has a door open",
            "a calm open field at dusk",
            world=WORLD,
            shots=(
                Shot("fannie", 9.0, lens="wide", focus="dome",
                     yaw=0, pitch=14, orbit=8,
                     caption="Fannie Mae's own selling guide already "
                             "allows dome-secured loans",
                     panel=OverlayPanel(
                         title="THE DOOR THAT'S ALREADY OPEN",
                         bullets=("Fannie Mae's Selling Guide "
                                  "explicitly allows geodesic-dome-"
                                  "secured loans when the appraiser "
                                  "has enough information",
                                  "The work is making sure appraisers "
                                  "have that information — comparables, "
                                  "engineer-stamped plans, repeat "
                                  "regional models",
                                  "Not a legal obstacle. A paperwork "
                                  "one, already being solved"),
                         position="left"),
                     narration=(
                         "Fannie Mae's own selling guide already "
                         "allows geodesic-dome-secured loans, provided "
                         "the appraiser has enough information to "
                         "value it. That's not a legal wall — it's a "
                         "paperwork gap: comparables, engineer-stamped "
                         "plans, repeat regional models.",
                     )),
                Shot("close_shot", 10.0, lens="ultrawide", perspective=6,
                     focus="dome", yaw=-90, pitch=22,
                     caption="Financing solved the way everything else "
                             "in this series is solved: computed, "
                             "checkable, not promised",
                     panel=OverlayPanel(
                         title="THE ACTUAL ANSWER",
                         bullets=("A real amortization formula, run "
                                  "the same way for every product tier",
                                  "A lending pathway that already "
                                  "exists and needs paperwork, not "
                                  "permission",
                                  "Part of a ten-part case for 2V "
                                  "geodesic domes in the housing "
                                  "market"),
                         position="bottom"),
                     narration=(
                         "Financing, solved the way everything else in "
                         "this series is solved: a real formula, run "
                         "consistently, checkable by anyone who reads "
                         "the code. This is one part of a ten part "
                         "case for 2V geodesic domes in the housing "
                         "market.",
                     )),
            ),
        ),
    )
    return Presentation(
        title="Financing, Already Modeled",
        author="DomeSim Presenter Studio",
        scenes=scenes,
    )
