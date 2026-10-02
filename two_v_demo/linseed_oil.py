"""Linseed oil in a wedge dome: traceable inputs, scope and planning arithmetic.

Source record 1629 is a subtitle transcript, not a materials test. The reference
geometry comes from seed_world; estimates below are explicitly NOT measured.
Run with ``py -3.12 -m two_v_demo.linseed_oil``.
"""
from __future__ import annotations

import math
from functools import lru_cache

SOURCE = {
    "record_id": 1629,
    "title": "20 LOST Linseed Oil Tricks Old-Timers Swore By That Outperform Anything at the Hardware Store",
    "creator": "The Lost Handyman",
    "url": "https://www.youtube.com/watch?v=7P6on1q9X_g",
}
REFERENCES = {
    "danish": "https://www.triedandtruewoodfinish.com/products/danish-oil/",
    "wax": "https://www.triedandtruewoodfinish.com/products/original-wood-finish/",
    "faq": "https://www.triedandtruewoodfinish.com/resources/faq/",
    "rags": "https://www.mass.gov/info-details/disposing-of-oily-rags",
    "fire": "https://fireline.seattle.gov/2026/04/02/spring-clean-for-a-safer-household/",
    "wood": "https://research.fs.usda.gov/download/treesearch/37432.pdf",
    "bond": "https://www.westsystem.com/instruction/epoxy-basics/surface-preparation/",
    "glass": "https://images.dap.com/33%20Window%20Glazing%20TDS_5.9.19.pdf",
}

# name, value, unit, kind, reason/reference. Each input used by the film is
# declared on camera before its calculation or application demonstration.
CONSTANTS = (
    ("coats", 2, "coats", "assumption", "Planning example; follow the selected finish's actual coat schedule."),
    ("faces", 2, "flat faces/member", "assumption", "Reference allowance for both sawn faces; not a directive to oil bonding surfaces."),
    ("coverage", 350, "sq ft/US gal/coat", "estimate", "Conservative sensitivity case, not a product claim or a measurement."),
    ("handling", 15, "% extra volume", "assumption", "Planning allowance for application losses; validate on an offcut."),
    ("minutes", 2, "min/member/coat", "estimate", "Illustrative active wipe-on/wipe-off labour only; excludes preparation and curing."),
    ("danish_wait", 5, "min minimum", "claimed", REFERENCES["danish"] + " application instructions; accessed 2026-09-30."),
    ("danish_cure", 8, "hours minimum", "claimed", REFERENCES["danish"] + " minimum cure interval, not guaranteed service-ready time."),
    ("wax_wait", 60, "min minimum", "claimed", REFERENCES["wax"] + " application instructions; accessed 2026-09-30."),
    ("wax_cure", 24, "hours minimum", "claimed", REFERENCES["wax"] + " minimum cure interval, not guaranteed service-ready time."),
    ("label_coverage", 1000, "sq ft/US gal", "claimed", REFERENCES["danish"] + " UP TO coverage; not a rough-sawn timber prediction."),
)
C = {name: value for name, value, _unit, _kind, _reason in CONSTANTS}

# All twenty transcript topics accounted for. Application to the dome is our
# synthesis; source time is the start of the relevant caption, not new narration.
TOPICS = (
    (20, "03:33", "Furniture finish", "apply", "Shelves, trim and accessible interior wood; thin coats."),
    (19, "04:34", "Tool handles", "qualify", "Finish sound handles only; replace cracked or loose handles."),
    (18, "05:30", "Outdoor wood", "qualify", "No roof, rot, UV or water-barrier credit for plain oil."),
    (17, "06:54", "Thinning", "qualify", "Only when the exact product permits it; no universal solvent recipe."),
    (16, "07:51", "Leather", "exclude", "Not a dome assembly; follow leather/PPE manufacturer care."),
    (15, "08:46", "Glazing putty", "qualify", "Specified sash glazing only; not overhead dome glazing or structural retention."),
    (14, "09:40", "Tool rust", "qualify", "Nonmoving steel storage surfaces only; no chain or bearing lubrication."),
    (13, "12:03", "Pigmented oil", "qualify", "Compatible formulated stain; homemade pigment is no durability rating."),
    (12, "12:53", "Gunstock", "exclude", "No additional dome-building use beyond wood finishing."),
    (11, "13:54", "Decorative iron", "qualify", "Decorative surfaces; structural fasteners keep specified protection."),
    (10, "14:51", "Toolbox joints", "correct", "Repair joints mechanically; oil does not restore structural strength."),
    (9, "17:12", "Floors", "qualify", "Use a floor-rated system; assess cure, abrasion and slip."),
    (8, "18:03", "Water resistance", "correct", "Splash resistance is not a building water/air barrier."),
    (7, "18:54", "Weathered wood", "correct", "Appearance change cannot reverse decay or certify a member."),
    (6, "19:54", "Masonry", "exclude", "No foundation, freeze-thaw or below-grade waterproofing claim."),
    (5, "20:52", "Wooden machinery parts", "qualify", "Sound jig handles; keep glue lands and precision fits clean."),
    (4, "21:46", "Oil and beeswax", "qualify", "Use a labelled blend; no heating of unknown solvent-bearing oil."),
    (3, "22:41", "Raw versus boiled", "correct", "Raw, drier-modified and heat-polymerized oils vary by product."),
    (2, "23:46", "Food contact", "correct", "Select an explicitly suitable product and follow its cure instructions."),
    (1, "24:51", "Oily rags", "apply", "Provide a rag station before opening the oil; safe disposal is part of the job."),
)


def allowance(area_sqft: float, coverage: float, coats: float, extra_pct: float = 0) -> float:
    """US gallons for a scenario, not a performance or service-life prediction."""
    if not all(math.isfinite(x) for x in (area_sqft, coverage, coats, extra_pct)):
        raise ValueError("inputs must be finite")
    if area_sqft < 0 or coverage <= 0 or coats <= 0 or extra_pct < 0:
        raise ValueError("area/loss must be nonnegative; coverage/coats positive")
    return area_sqft * coats / coverage * (1 + extra_pct / 100)


@lru_cache(maxsize=1)
def facts() -> dict:
    import seed_world

    g = seed_world.geometry()
    # The stock lengths already include the reference model's fabrication
    # allowance. This is a deliberately labelled flat-face planning envelope.
    area = g.member_stock_ft * (g.member_depth_in / 12) * C["faces"]
    base = allowance(area, C["coverage"], C["coats"])
    nominal = allowance(area, C["label_coverage"], C["coats"])
    return {
        "members": g.member_count, "stock_ft": g.member_stock_ft,
        "depth_in": g.member_depth_in, "area_sqft": area,
        "base_gal": base, "allowance_gal": allowance(area, C["coverage"], C["coats"], C["handling"]),
        "label_gal": nominal, "sensitivity": base / nominal,
        "labour_hours": g.member_count * C["coats"] * C["minutes"] / 60,
        "topic_count": len(TOPICS),
    }


def validate_linseed_oil() -> None:
    assert allowance(350, 350, 2, 15) == 2.3
    assert allowance(0, 350, 2) == 0
    for bad in ((1, 0, 2), (-1, 350, 2), (1, 350, 0), (math.nan, 350, 2)):
        try:
            allowance(*bad)
        except ValueError:
            pass
        else:
            raise AssertionError(bad)
    f = facts()
    assert sorted(t[0] for t in TOPICS) == list(range(1, len(TOPICS) + 1))
    assert f["labour_hours"] >= 8, "Retain the unflattering labour estimate."
    assert f["sensitivity"] > 2 and f["allowance_gal"] > f["base_gal"] > f["label_gal"]
    assert f["area_sqft"] > 0 and len(C) == len(CONSTANTS)
    assert all(k in ("claimed", "estimate", "assumption", "standard", "nominal", "measured")
               and u and why for _, _, u, k, why in CONSTANTS)


def report() -> str:
    f = facts()
    rows = ["LINSEED OIL FOR A WEDGE DOME", "No measured finishing performance is available."]
    rows += [f"{n}: {v:g} {u} ({k}) -- {why}" for n, v, u, k, why in CONSTANTS]
    rows += [f"{k}: {v:.4f}" if isinstance(v, float) else f"{k}: {v}" for k, v in f.items()]
    rows += ["Planning envelope excludes curved backs, ends, panels, floor and trim.",
             "Subtract glue, gasket and sealant lands; measure actual selected surfaces.",
             "Labour excludes sanding, access, inspection and curing. No lifespan/cost comparison is established."]
    return "\n".join(rows)


if __name__ == "__main__":
    validate_linseed_oil()
    print(report())
