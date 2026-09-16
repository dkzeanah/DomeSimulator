"""One pine, valued at every rung it can climb: standing, burned, sawn, split, built, financed.

*The $20 Pine* argues that a tree has no single value, only a ladder of them, and that
the rung it reaches depends on what somebody does to it. The essay's representative
pine is the wedge film's log (:data:`wedge_geometry.DEFAULT_LOG`: 60 feet of usable
stem, 15 inches at the butt, 5.5 at the top) -- a modelled log, not a measured one, and
bigger than the book's tree -- so its volume and both of its recovery checks come
straight from :func:`wedge_geometry.tree_yield`, not from a new sum.

The author's figures -- 60 percent kept by a mill, 88 percent by splitting, a sawing
rate, a cord price -- are marked as the author's in :data:`SOURCES`, and each is set
beside what the simulator or a published figure says. Two of those checks help the
argument: the simulator packs this very log with two-by-fours and keeps only 45
percent, so 60 is generous to the mill, and it splits the log and keeps 88.4 percent
before any trimming, so 88 is no more than the model allows. One does not: a 2010
survey found portable mills charging well under the sawing rate used here.

The rungs above the wood itself -- the framing a tree replaces, the payments that
framing would have cost -- are the same figures *Why Build This Way* uses, so the two
films cannot disagree about them. Each is divided between the whole trees the shell
needs when it is cut from this pine (:func:`essay_design`): the frame uses one and a
half of them and two are felled, and dividing by the two is the cautious choice.
"""

from __future__ import annotations

from dataclasses import dataclass
from functools import lru_cache

from . import book_math as bm
from . import house_economics as he
from . import wedge_geometry as wg
from . import why_build_economics as wb
from .house_economics import AUTHOR, PUBLISHED, Source


SOURCES: tuple[Source, ...] = (
    Source("pine_usable_ft", wg.DEFAULT_LOG.usable_length_ft, "feet of usable stem",
           AUTHOR,
           f"The essay's representative pine, {wg.DEFAULT_LOG.butt_diameter_in:g} in at "
           f"the butt tapering to {wg.DEFAULT_LOG.top_diameter_in:g} in: the wedge "
           "film's modelled log (wedge_geometry.DEFAULT_LOG), bigger than the book's "
           "tree."),
    Source("pine_mill_recovery", 0.60, "of the stem", AUTHOR,
           "What a good dimensional-lumber mill keeps as the product wanted. The "
           "simulator packs this log with two-by-fours and keeps less; see the checks."),
    Source("pine_wedge_recovery", 0.88, "of the stem", AUTHOR,
           "What splitting keeps after defects, trimming, end geometry and mating "
           "lands. The simulator's kerf-only figure for this log is a little higher."),
    Source("pine_usd_per_bf", 1.50, "USD per board foot", PUBLISHED,
           "Common 1x and 2x pine at one sawmill's current list price. Species, "
           "grade, moisture and region all move it.",
           "Fireside Sawmill & Lumber, Graham NC, lumber price list (2026)."),
    Source("pine_milling_usd_per_bf", 0.60, "USD per board foot", AUTHOR,
           "A custom-sawing rate for pine under 16 feet. A 2010 survey found "
           "portable mills charging less; see the checks."),
    Source("survey_milling_low", 0.20, "USD per board foot", PUBLISHED,
           "Low end of what portable-sawmill owners charged for custom sawing.",
           "Alabama Cooperative Extension System, 'Milling Dimensions' (Auburn "
           "University survey, 2010)."),
    Source("survey_milling_high", 0.30, "USD per board foot", PUBLISHED,
           "High end of the same average.",
           "Alabama Cooperative Extension System, as above."),
    Source("survey_milling_year", 2010.0, "year", PUBLISHED,
           "When that survey was taken; sawing rates have risen since.",
           "Alabama Cooperative Extension System, as above."),
    Source("cord_stacked_ft3", 128.0, "cubic feet", PUBLISHED,
           "A full cord: four by four by eight feet of stacked wood, of which 80 to "
           "90 cubic feet is solid wood.",
           "Northern Woodlands, 'How Solid is a Cord of Wood?'"),
    Source("cord_solid_ft3", 90.0, "cubic feet", AUTHOR,
           "Solid wood in a cord of southern pine: the top of the published 80 to 90."),
    Source("cord_pickup_usd", 275.0, "USD", AUTHOR,
           "A Tuscaloosa-area seller's full cord, picked up."),
    Source("cord_delivered_usd", 300.0, "USD", AUTHOR,
           "The same cord, delivered."),
)

SOURCE_BY_KEY = {source.key: source for source in SOURCES}


def value(key: str) -> float:
    return SOURCE_BY_KEY[key].value


@lru_cache(maxsize=1)
def essay_plan() -> bm.TreeCutPlan:
    """The essay's pine as a cutting plan: the films' log, bucked to the length the
    priced shell asks for, so the shell can be sized from this tree and not the
    book's smaller one."""
    log = wg.DEFAULT_LOG
    rough = bm.TreeCutPlan(log.butt_diameter_in, log.top_diameter_in,
                           log.usable_length_ft, log.section_length_ft)
    buck = bm.design_first_for_floor(he.dome_floor_sqft(), rough).bucking_length_ft
    return bm.TreeCutPlan(log.butt_diameter_in, log.top_diameter_in,
                          log.usable_length_ft, float(buck))


@lru_cache(maxsize=1)
def essay_design() -> bm.DesignFirstResult:
    """The priced shell sized from the essay's pine: the trunk it uses, and how many
    whole trees that means felling."""
    return bm.design_first_for_floor(he.dome_floor_sqft(), essay_plan())


BOARD_FEET_PER_CUBIC_FOOT = 1728.0 / wg.CUBIC_INCHES_PER_BOARD_FOOT
"""Twelve: a board foot is 144 cubic inches, a cubic foot 1,728."""

CORD_FT = (8.0, 4.0, 4.0)
"""A full cord's stack, long by deep by high, in feet: the published cord's own
definition, and the size the firewood scene draws it."""


@dataclass(frozen=True)
class Pine:
    """The essay's pine, and every value it can be given."""

    solid_bf: float
    kerf_only: float
    sawn_model: float
    mill: float
    wedge: float
    trees: int
    trees_consumed: float
    trunk_ft: float
    framing_value: float
    financed_value: float
    hours_per_shell: float
    wage: float
    cash_per_shell: float
    measured_cash_per_shell: float

    # -- the wood -------------------------------------------------------------
    @property
    def solid_ft3(self) -> float:
        return self.solid_bf / BOARD_FEET_PER_CUBIC_FOOT

    @property
    def mill_bf(self) -> float:
        return self.solid_bf * self.mill

    @property
    def wedge_bf(self) -> float:
        return self.solid_bf * self.wedge

    @property
    def extra_bf(self) -> float:
        return self.wedge_bf - self.mill_bf

    @property
    def gain_ratio(self) -> float:
        return self.wedge / self.mill

    @property
    def waste_cut(self) -> float:
        """How much less of the tree is left behind, as a share of the mill's loss."""
        return ((1.0 - self.mill) - (1.0 - self.wedge)) / (1.0 - self.mill)

    @property
    def mill_lost_bf(self) -> float:
        return self.solid_bf - self.mill_bf

    @property
    def wedge_lost_bf(self) -> float:
        return self.solid_bf - self.wedge_bf

    @property
    def shell_bf(self) -> float:
        return self.trees * self.wedge_bf

    @property
    def trees_equivalent(self) -> float:
        """Mill-recovered trees it takes to match the shell's split wood."""
        return self.shell_bf / self.mill_bf

    # -- the rungs ------------------------------------------------------------
    @property
    def stump_tons(self) -> float:
        return self.solid_ft3 * he.value("green_pine_lb_per_ft3") / 2000.0

    @property
    def stump_usd(self) -> float:
        return self.stump_tons * he.value("stumpage_pine_usd_per_ton")

    @property
    def cords(self) -> float:
        return self.solid_ft3 / value("cord_solid_ft3")

    @property
    def firewood_usd(self) -> float:
        return self.cords * value("cord_pickup_usd")

    @property
    def firewood_delivered_usd(self) -> float:
        return self.cords * value("cord_delivered_usd")

    @property
    def mill_usd(self) -> float:
        return self.mill_bf * value("pine_usd_per_bf")

    @property
    def wedge_usd(self) -> float:
        return self.wedge_bf * value("pine_usd_per_bf")

    @property
    def milling_usd(self) -> float:
        return self.mill_bf * value("pine_milling_usd_per_bf")

    @property
    def use_usd(self) -> float:
        """Framing function this tree's share of the shell replaces."""
        return self.framing_value / self.trees

    @property
    def financed_usd(self) -> float:
        """Nominal payments that framing would have cost, this tree's share."""
        return self.financed_value / self.trees

    # -- the tree's value to its owner --------------------------------------------
    @property
    def hours(self) -> float:
        return self.hours_per_shell / self.trees

    @property
    def labor_usd(self) -> float:
        return self.hours * self.wage

    @property
    def cash_usd(self) -> float:
        return self.cash_per_shell / self.trees

    @property
    def net_usd(self) -> float:
        """Function replaced, less the owner's hours at their wage, less the cash."""
        return self.use_usd - self.labor_usd - self.cash_usd

    @property
    def net_measured_usd(self) -> float:
        """The same with the fortnight's own receipts instead of the author's $800."""
        return self.use_usd - self.labor_usd - self.measured_cash_per_shell / self.trees


@lru_cache(maxsize=1)
def pine() -> Pine:
    yields = wg.tree_yield()
    case = wb.case()
    design = essay_design()
    return Pine(solid_bf=yields.solid_bf, kerf_only=yields.wedge_recovery,
                sawn_model=yields.two_by_four_recovery,
                mill=value("pine_mill_recovery"), wedge=value("pine_wedge_recovery"),
                trees=design.whole_trees_needed, trees_consumed=design.trees_needed,
                trunk_ft=design.trunk_feet_needed, framing_value=case.framing_value,
                financed_value=case.financed, hours_per_shell=case.hours,
                wage=case.wage, cash_per_shell=case.cash,
                measured_cash_per_shell=he.frame_value().cash_total)


# ----------------------------------------------------------------------
# Screens
# ----------------------------------------------------------------------

def source_lines() -> tuple[str, ...]:
    """What the ladder rests on, for the screen that shows it before any rung."""
    t, log, case = pine(), wg.DEFAULT_LOG, wb.case()
    return (
        f"THE AUTHOR'S  a representative pine: {log.usable_length_ft:.0f} ft of stem, "
        f"{log.butt_diameter_in:.0f} in to {log.top_diameter_in:g} in",
        f"THE AUTHOR'S  {t.mill * 100:.0f}% kept by a mill; {t.wedge * 100:.0f}% by "
        f"splitting; {value('cord_solid_ft3'):.0f} cu ft of wood a cord",
        f"THE AUTHOR'S  sawing ${value('pine_milling_usd_per_bf'):.2f}/bd ft; a cord "
        f"${value('cord_pickup_usd'):.0f} picked up, ${value('cord_delivered_usd'):.0f} "
        "delivered",
        f"THE AUTHOR'S  ${case.framing_value:,.0f} of framing for the shell; it uses "
        f"{t.trees_consumed:g} trees, {t.trees} felled",
        f"PUBLISHED  pine ${value('pine_usd_per_bf'):.2f}/bd ft; stumpage "
        f"${he.value('stumpage_pine_usd_per_ton'):.2f}/ton; a cord "
        f"{value('cord_stacked_ft3'):.0f} cu ft stacked",
        f"CHECK  this log in the simulator: sawn to 2x4s {t.sawn_model * 100:.0f}%, "
        f"split {t.kerf_only * 100:.1f}% before trimming",
        "So the mill gets the benefit of the doubt, not the wedge",
    )


# ----------------------------------------------------------------------
# Live figures for the book-token language
# ----------------------------------------------------------------------

def token_specs() -> list[tuple[str, str, object]]:
    """(name, description, compute) for every ``{{pine.*}}`` token."""
    from .book_tokens import _n, _pct

    def t():
        return pine()

    log = wg.DEFAULT_LOG
    return [
        ("pine.length_ft", "the pine's usable stem, feet",
         lambda: _n(log.usable_length_ft, 0)),
        ("pine.butt_in", "its diameter at the butt, inches",
         lambda: _n(log.butt_diameter_in, 0)),
        ("pine.top_in", "its diameter at the usable top, inches",
         lambda: f"{log.top_diameter_in:g}"),
        ("pine.solid_ft3", "solid wood in the stem, cubic feet",
         lambda: _n(t().solid_ft3, 1)),
        ("pine.bf_per_ft3", "board feet in a cubic foot",
         lambda: _n(BOARD_FEET_PER_CUBIC_FOOT, 0)),
        ("pine.solid_bf", "the stem in board-foot units",
         lambda: _n(t().solid_bf, 0)),
        ("pine.mill_pct", "the author's mill recovery, per cent",
         lambda: _pct(t().mill, 0)),
        ("pine.wedge_pct", "the author's wedge recovery, per cent",
         lambda: _pct(t().wedge, 0)),
        ("pine.wedge_share", "the wedge recovery as a fraction",
         lambda: f"{t().wedge:.2f}"),
        ("pine.mill_bf", "board feet a mill keeps", lambda: _n(t().mill_bf, 0)),
        ("pine.wedge_bf", "board feet splitting keeps", lambda: _n(t().wedge_bf, 0)),
        ("pine.extra_bf", "board feet more from the same tree",
         lambda: _n(t().extra_bf, 0)),
        ("pine.gain_ratio", "split recovery over sawn",
         lambda: f"{t().gain_ratio:.3f}"),
        ("pine.gain_pct", "per cent more usable wood",
         lambda: _pct(t().gain_ratio - 1.0, 1)),
        ("pine.per_hundred", "split units for every hundred sawn",
         lambda: _n(t().gain_ratio * 100.0, 0)),
        ("pine.mill_waste_pct", "per cent a mill leaves behind",
         lambda: _pct(1.0 - t().mill, 0)),
        ("pine.wedge_waste_pct", "per cent splitting leaves behind",
         lambda: _pct(1.0 - t().wedge, 0)),
        ("pine.waste_cut_pct", "per cent less wood left behind",
         lambda: _pct(t().waste_cut, 0)),
        ("pine.mill_lost_bf", "board feet a mill leaves behind",
         lambda: _n(t().mill_lost_bf, 0)),
        ("pine.wedge_lost_bf", "board feet splitting leaves behind",
         lambda: _n(t().wedge_lost_bf, 0)),
        ("pine.shell_bf", "split wood in the shell's trees",
         lambda: _n(t().shell_bf, 0)),
        ("pine.shell_trees", "the essay's pines felled for the shell",
         lambda: str(t().trees)),
        ("pine.trees_consumed", "how many of them the frame uses",
         lambda: _n(t().trees_consumed, 1)),
        ("pine.trunk_ft", "feet of this trunk the frame uses",
         lambda: _n(t().trunk_ft, 0)),
        ("pine.trees_equiv", "mill-recovered trees to match it",
         lambda: f"{t().trees_equivalent:.2f}"),
        ("pine.usd_per_bf", "a sawmill's price for common pine, a board foot",
         lambda: f"{value('pine_usd_per_bf'):.2f}"),
        ("pine.mill_usd", "the sawn lumber, at that price",
         lambda: _n(t().mill_usd, 0)),
        ("pine.wedge_usd", "the split wood, at that price",
         lambda: _n(t().wedge_usd, 0)),
        ("pine.value_gain", "what splitting adds, one tree",
         lambda: _n(round(t().wedge_usd) - round(t().mill_usd), 0)),
        ("pine.value_gain_shell", "what splitting adds, the shell's trees",
         lambda: _n((round(t().wedge_usd) - round(t().mill_usd)) * t().trees, 0)),
        ("pine.milling_usd_per_bf", "the author's sawing rate, a board foot",
         lambda: f"{value('pine_milling_usd_per_bf'):.2f}"),
        ("pine.milling_usd", "sawing the conventional lumber",
         lambda: _n(t().milling_usd, 0)),
        ("pine.survey_milling_low", "a 2010 survey's low sawing charge",
         lambda: f"{value('survey_milling_low'):.2f}"),
        ("pine.survey_milling_high", "the same survey's high charge",
         lambda: f"{value('survey_milling_high'):.2f}"),
        ("pine.survey_year", "the year of that survey",
         lambda: f"{value('survey_milling_year'):.0f}"),
        ("pine.cord_ft3", "a cord, stacked, cubic feet",
         lambda: _n(value("cord_stacked_ft3"), 0)),
        ("pine.cord_solid_ft3", "solid wood in a cord, cubic feet",
         lambda: _n(value("cord_solid_ft3"), 0)),
        ("pine.cords", "the tree as cords of firewood", lambda: f"{t().cords:.2f}"),
        ("pine.cord_usd", "a cord, picked up", lambda: _n(value("cord_pickup_usd"), 0)),
        ("pine.cord_delivered_usd", "a cord, delivered",
         lambda: _n(value("cord_delivered_usd"), 0)),
        ("pine.cord_length_ft", "a cord's stack, long, feet",
         lambda: _n(CORD_FT[0], 0)),
        ("pine.cord_depth_ft", "a cord's stack, deep, feet",
         lambda: _n(CORD_FT[1], 0)),
        ("pine.cord_height_ft", "a cord's stack, high, feet",
         lambda: _n(CORD_FT[2], 0)),
        ("pine.firewood_usd", "the tree as firewood, picked up",
         lambda: _n(t().firewood_usd, 0)),
        ("pine.firewood_delivered_usd", "the tree as firewood, delivered",
         lambda: _n(t().firewood_delivered_usd, 0)),
        ("pine.stump_tons", "the stem, green, tons", lambda: f"{t().stump_tons:.2f}"),
        ("pine.stumpage", "pine sawtimber stumpage, a ton",
         lambda: f"{he.value('stumpage_pine_usd_per_ton'):.2f}"),
        ("pine.stump_usd", "the tree on the stump", lambda: _n(t().stump_usd, 0)),
        ("pine.use_usd", "framing function one tree replaces",
         lambda: _n(t().use_usd, 0)),
        ("pine.financed_usd", "that framing's payments, one tree",
         lambda: _n(t().financed_usd, 0)),
        ("pine.fire_ratio", "structure against firewood",
         lambda: _n(t().use_usd / round(t().firewood_usd), 0)),
        ("pine.mill_ratio", "structure against sawn lumber",
         lambda: _n(t().use_usd / round(t().mill_usd), 0)),
        ("pine.wedge_ratio", "structure against split stock",
         lambda: f"{t().use_usd / round(t().wedge_usd):.1f}"),
        ("pine.hours", "the owner's hours, one tree", lambda: _n(t().hours, 0)),
        ("pine.labor_usd", "those hours at the author's wage",
         lambda: _n(t().labor_usd, 0)),
        ("pine.cash_usd", "cash, one tree's half of the shell's",
         lambda: _n(t().cash_usd, 0)),
        ("pine.net_usd", "what the tree is worth to its owner",
         lambda: _n(t().net_usd, 0)),
        ("pine.net_measured_usd", "the same with the fortnight's receipts",
         lambda: _n(t().net_measured_usd, 0)),
        ("pine.kerf_only_pct", "the simulator's split recovery for this log",
         lambda: _pct(t().kerf_only, 1)),
        ("pine.sawn_model_pct", "the simulator's sawn recovery for this log",
         lambda: _pct(t().sawn_model, 0)),
    ]


# ----------------------------------------------------------------------
# Proof
# ----------------------------------------------------------------------

def validate_pine_value() -> None:
    """The author's stated figures, reproduced, then the checks, in their direction."""
    keys = ([s.key for s in SOURCES] + [s.key for s in he.SOURCES]
            + [s.key for s in wb.SOURCES])
    assert len(keys) == len(set(keys)), "a source key is defined twice"
    for source in SOURCES:
        assert source.kind in he.KINDS and source.note.strip(), source.key
        if source.kind == PUBLISHED:
            assert source.cite.strip(), source.key

    t = pine()
    plan, log = essay_plan(), wg.DEFAULT_LOG
    assert abs(plan.solid_bf - log.solid_bf) < 1e-9, (plan.solid_bf, log.solid_bf)
    assert t.trees == 2 and abs(t.trees_consumed - 1.5) < 1e-9, (t.trees,
                                                                 t.trees_consumed)
    # The author's worked example, figure by figure.
    assert abs(t.solid_ft3 - 36.8) < 0.1, t.solid_ft3
    assert abs(t.solid_bf - 442.0) < 1.0, t.solid_bf
    assert abs(t.mill_bf - 265.0) < 1.0 and abs(t.wedge_bf - 389.0) < 1.0
    assert abs(t.extra_bf - 124.0) < 1.0, t.extra_bf
    assert abs(t.gain_ratio - 88.0 / 60.0) < 1e-12
    assert abs(t.waste_cut - 0.70) < 1e-9, t.waste_cut
    assert abs(t.trees_equivalent - 2.0 * 88.0 / 60.0) < 1e-9
    assert abs(t.mill_usd - 398.0) < 1.0 and abs(t.wedge_usd - 584.0) < 1.0
    assert abs(t.firewood_usd - 113.0) < 1.0, t.firewood_usd
    assert abs(t.mill_lost_bf - 177.0) < 1.0 and abs(t.wedge_lost_bf - 53.0) < 1.0
    length, depth, height = CORD_FT
    assert length * depth * height == value("cord_stacked_ft3"), CORD_FT
    assert abs(t.use_usd - 2_400.0) < 1e-6 and abs(t.net_usd - 1_000.0) < 1e-6
    assert abs(t.financed_usd - wb.case().financed / 2.0) < 1e-6
    # The checks the film states, in the direction it states them.
    assert t.sawn_model < t.mill, (t.sawn_model, t.mill)
    assert t.kerf_only >= t.wedge, (t.kerf_only, t.wedge)
    assert value("survey_milling_high") < value("pine_milling_usd_per_bf")
    assert 15.0 < t.stump_usd < 35.0, t.stump_usd      # "the twenty-dollar pine"
    # The ladder climbs.
    rungs = (t.stump_usd, t.firewood_usd, t.mill_usd, t.wedge_usd, t.use_usd,
             t.financed_usd)
    assert all(a < b for a, b in zip(rungs, rungs[1:])), rungs


if __name__ == "__main__":
    validate_pine_value()
    for name, _describe, compute in token_specs():
        print(f"{name:<28} {compute()}")
