"""The staple house: the dome as the cheap, fast, known, everywhere-the-same baseline
of housing -- and the papercuts it leaves out.

The owner's analogy, in his words: *the dome is a McDouble*. Cheap, fast, reliable,
consistent, known everywhere -- the staple a whole chain stands on. An eighteen-year-old
does not need his first home to be a five-course meal; he needs one that is filling,
honest and the same every time, so he can save for the rest. Without that baseline in
a market, most people never enter it, and the thousand small cuts belong to somebody
else.

This module counts both sides, from the models that own the numbers:

* **the papercuts** of a new house -- the published NAHB 2024 survey house
  (:mod:`two_v_demo.house_economics`): the fee lines and the margin lines a buyer pays
  that are not a board or an hour of work, every separately priced line of the
  building, and the fifteen sets of hands in one stud
  (:mod:`two_v_demo.wedge_why_facts`);
* **the interest** on the loan the numbers page uses (:mod:`master_book.numbers`);
* **the staple**: the stem cell's one invoice -- every line, one seller, the margin
  printed on it -- and what the same floor costs the other two ways.

The comparison is not like for like and says so: the survey house is far bigger and
comes with land; the dome is a small building on a pad. The point is the *shape* of the
two bills -- how many hands, how many lines that are not the building -- not that one
replaces the other.
"""

from __future__ import annotations

from functools import lru_cache

NAME = "The Staple House"
"""The idea's name. The owner's analogy -- the McDouble of housing -- is used freely,
in titles and headlines too: it is an analogy, and he is free to talk about it."""


@lru_cache(maxsize=1)
def facts() -> dict:
    from master_book import numbers

    from . import house_economics as he
    from . import wedge_why_facts as yf

    n = numbers.facts()
    price_parts = {k: v for k, _, v in he.PRICE_PARTS}
    survey_price = he.price_total()
    fees = [i for i in he.ITEMS if i.work == he.FEE]
    fee_total = sum(i.dollars for i in fees)
    margins = {k: price_parts[k] for k in he.MARGIN_PARTS}
    margin_total = sum(margins.values())
    papercuts = fee_total + margin_total
    building_lines = [i for i in he.ITEMS if i.work != he.FEE]
    invoice = list(n["groups"]) + [("Overhead", n["overhead"]), ("Warranty reserve", n["warranty"]),
                                   (f"Margin ({n['margin_pct']:.0f}%)", n["margin"])]
    assert abs(sum(v for _, v in invoice) - n["price"]) < 1.0, "the invoice must add to the price"
    return {
        "survey_price": survey_price, "survey_lot": price_parts["lot"],
        "fee_lines": len(fees), "fee_total": fee_total, "fees": [(i.name, i.dollars) for i in fees],
        "margin_lines": len(margins), "margin_total": margin_total,
        "margins": [(dict((k, n_) for k, n_, _ in he.PRICE_PARTS)[k], v) for k, v in margins.items()],
        "papercut_lines": len(fees) + len(margins), "papercuts": papercuts,
        "papercut_pct": 100 * papercuts / survey_price,
        "papercut_domes": papercuts / n["price"],
        "building_lines": len(building_lines),
        "hands": len(yf.MIDDLE_MEN),
        "loan": n["loan"], "loan_rate": n["loan_pct"], "loan_years": n["loan_years"],
        "loan_total": n["loan_total"], "interest": n["loan_interest"],
        "interest_domes": n["loan_interest"] / n["price"],
        "interest_pct_of_loan": 100 * n["loan_interest"] / n["loan"],
        "dome_price": n["price"], "dome_standing": n["standing"], "dome_margin": n["margin"],
        "dome_margin_pct": n["margin_pct"], "dome_lines": len(invoice), "invoice": invoice,
        "dome_floor": n["floor"], "dome_per_sqft": n["per_sqft"],
        "site_same": n["site_same"], "mhs_same": n["mhs_same"], "mhs_gap": n["mhs_same"] - n["price"],
        "dome_vs_site_pct": 100 * n["price"] / n["site_same"],
        "dome_vs_mhs_pct": 100 * n["price"] / n["mhs_same"],
        "labour_hours": n["labour_hours"],
    }


def money(v: float) -> str:
    return f"${v:,.0f}"


def steps_papercuts() -> list[str]:
    """The survey house's papercuts, worked."""
    f = facts()
    out = [f"The published new house (NAHB 2024) sells for {money(f['survey_price'])}, of which "
           f"{money(f['survey_lot'])} is the land."]
    out.append(f"{f['fee_lines']} lines are permits, fees and site paperwork, before the foundation:")
    out += [f"  {name}: {money(v)}" for name, v in f["fees"]]
    out.append(f"{f['margin_lines']} lines are what the builder and seller take beyond the building:")
    out += [f"  {name}: {money(v)}" for name, v in f["margins"]]
    out.append(f"Together: {f['papercut_lines']} lines, {money(f['papercuts'])} -- "
               f"{f['papercut_pct']:.0f}% of the price, and none of it a board or an hour of work on the house itself. "
               f"That is the price of {f['papercut_domes']:.0f} stem-cell domes.")
    out.append(f"Under them, the building is {f['building_lines']} separately priced lines, each its own "
               f"trade, and every stud in the frame has passed through {f['hands']} sets of hands.")
    return out


def steps_interest() -> list[str]:
    f = facts()
    return [f"Borrow {money(f['loan'])} at {f['loan_rate']:g}% for {f['loan_years']:.0f} years and you "
            f"pay back {money(f['loan_total'])}.",
            f"The interest alone is {money(f['interest'])} -- {f['interest_pct_of_loan']:.0f}% of what was "
            f"borrowed, and the price of {f['interest_domes']:.1f} stem-cell domes."]


def steps_staple() -> list[str]:
    f = facts()
    out = [f"The stem cell's invoice has {f['dome_lines']} lines, from one seller, and adds to "
           f"{money(f['dome_price'])}:"]
    out += [f"  {name}: {money(v)}" for name, v in f["invoice"]]
    out.append(f"The margin is on the invoice: {money(f['dome_margin'])}, {f['dome_margin_pct']:.0f}%.")
    out.append(f"The same {f['dome_floor']:.0f} sq ft as a new site-built house: {money(f['site_same'])}; "
               f"as a new manufactured home: {money(f['mhs_same'])}. The dome is "
               f"{f['dome_vs_site_pct']:.0f}% and {f['dome_vs_mhs_pct']:.0f}% of them.")
    out.append(f"Standing on its serviced pad: {money(f['dome_standing'])}.")
    return out


def validate() -> None:
    f = facts()
    assert f["fee_lines"] == 5 and f["margin_lines"] == 5, (f["fee_lines"], f["margin_lines"])
    assert abs(f["fee_total"] - 32_719) < 1, "the fee lines must match NAHB's site-work subtotal"
    assert f["papercuts"] < f["survey_price"] and f["papercut_domes"] > 1
    assert f["dome_lines"] >= 7 and f["interest"] > f["dome_price"]
    for fn in (steps_papercuts, steps_interest, steps_staple):
        assert all(isinstance(s, str) and s for s in fn())


if __name__ == "__main__":
    validate()
    for fn in (steps_papercuts, steps_interest, steps_staple):
        print("\n".join(fn()), end="\n\n")
