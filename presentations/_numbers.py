"""Shared, verified real numbers for every ``dome_case_*`` presentation.

Every number here is computed from ``al_build`` / ``two_v_demo.geometry``
— the same modules the interactive tools use — not a hardcoded marketing
figure. Every presentation in this package imports from here instead of
recomputing its own copy, so a claim can never drift out of sync with
what the software actually computes, and the same figure can never end
up calculated two different (possibly inconsistent) ways in two files.
"""

from __future__ import annotations

import math

import al_build as ab
from two_v_demo.geometry import build_demo_geometry

# ---------------------------------------------------------------------------
# 2V geometry: strut/panel counts and the golden-ratio myth debunk.
# ---------------------------------------------------------------------------

GEO = build_demo_geometry()
SHORT = next(c for c in GEO.edge_classes if c.name == "SHORT")
LONG = next(c for c in GEO.edge_classes if c.name == "LONG")
TRI_ISO = next(t for t in GEO.triangle_classes if t.name == "LONG-SHORT-SHORT")
TRI_EQU = next(t for t in GEO.triangle_classes if t.name == "LONG-LONG-LONG")
HUB_COUNT = len(set(i for e in GEO.hemisphere_edges for i in e))

# ---------------------------------------------------------------------------
# Box-vs-dome cost comparison, both tiers, straight from al_build's own
# apples-to-apples rate model.
# ---------------------------------------------------------------------------

COMPARE = ab.building_comparisons()
SHED = COMPARE["shed"]
HOME = COMPARE["home"]

FT_M = 1.0 / ab.FT_PER_M
SHED_BOX_W, SHED_BOX_L, SHED_BOX_H = (v * FT_M for v in ab.COMPARE_SHED_BOX)
SHED_DOME_R_M = SHED["dome"]["r_ft"] * FT_M
_home_hw_ft = math.sqrt(ab.COMPARE_HOME_FLOOR_SF / 1.3)
HOME_BOX_W = _home_hw_ft * FT_M
HOME_BOX_L = (ab.COMPARE_HOME_FLOOR_SF / _home_hw_ft) * FT_M
HOME_BOX_H = ab.COMPARE_HOME_WALL_FT * FT_M
HOME_DOME_R_M = HOME["dome"]["r_ft"] * FT_M


def pct_less(a: float, b: float) -> float:
    """Percent by which ``b`` is less than ``a``."""
    return 100.0 * (1.0 - b / a)


SHED_SAVE_PCT = pct_less(SHED["box"]["build"], SHED["dome"]["build"])
SHED_FRAME_PCT = pct_less(SHED["box"]["framing_lf"], SHED["dome"]["framing_lf"])
SHED_CLAD_PCT = pct_less(SHED["box"]["cladding_sf"], SHED["dome"]["cladding_sf"])
HOME_SAVE_PCT = pct_less(HOME["box"]["build"], HOME["dome"]["build"])
HOME_FRAME_PCT = pct_less(HOME["box"]["framing_lf"], HOME["dome"]["framing_lf"])
HOME_VOL_PCT = 100.0 * (HOME["dome"]["vol_ft3"] / HOME["box"]["vol_ft3"] - 1.0)

# ---------------------------------------------------------------------------
# One representative "hero" home dome, radius inside the real product
# line's own "home" radius range (3.2-4.6 m), used for every build/teaching
# scene and every per-unit economics figure.
# ---------------------------------------------------------------------------

R = 4.2

HERO_SPEC = ab.DomeSpec(dtype="home", radius=R, frequency=3, serial=1,
                        name="Meridian")
HERO_CAT, _HERO_INFO = ab.build_dome_catalog(HERO_SPEC)
HERO_PRICE = HERO_SPEC.sale_price
HERO_MATERIAL = sum(e.material_cost for e in HERO_CAT.elements)
HERO_LABOR_HOURS = sum(e.labor_min for e in HERO_CAT.elements) / 60.0
HERO_THROUGHPUT = ab.throughput(HERO_CAT)
HERO_BUILD_DAYS = 1.0 / HERO_THROUGHPUT["single_flow_per_day"]
HERO_BENCH = ab.benchmark(HERO_CAT, HERO_SPEC,
                          {"price": HERO_PRICE, "material": HERO_MATERIAL},
                          build_days=HERO_BUILD_DAYS,
                          labor_hours=HERO_LABOR_HOURS)
HERO_VALUE = ab.product_value(HERO_CAT, HERO_SPEC)
HERO_BREAK_EVEN = ab.break_even(avg_margin=HERO_PRICE - HERO_MATERIAL)
HERO_MONTHLY = HERO_SPEC.monthly_payment

BENCH_PRICE_PCT = pct_less(HERO_BENCH["conventional"]["price"],
                           HERO_BENCH["dome"]["price"])
BENCH_LABOR_PCT = pct_less(HERO_BENCH["conventional"]["labor_hours"],
                           HERO_BENCH["dome"]["labor_hours"])
BENCH_DAYS_PCT = pct_less(HERO_BENCH["conventional"]["build_days"],
                          HERO_BENCH["dome"]["build_days"])
