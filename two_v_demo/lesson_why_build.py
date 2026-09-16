"""Why Build This Way: the macro case for the wedge dome, in the author's own framing.

The film argues that the method changes the exchange rate between an hour of a finite
life and a square foot of shelter. It uses the author's round figures -- bought space
at $100 a square foot, framing as 16 percent of it, 80 hours of shell work, a 6.5
percent thirty-year mortgage, a $25 take-home wage -- and labels them as the author's
own on a screen before any is multiplied, beside the published figures they are cautious
against. Every figure is a token from :mod:`two_v_demo.why_build_economics`, so the
voice, the callouts, the worksheets and the written script cannot disagree.

Three kinds of value per hour are kept apart, because blurring them is how a case like
this overstates itself:

* **production value** -- what the hour substitutes at today's price ($60);
* **debt-avoidance value** -- nominal mortgage payments never made, per hour ($137),
  which is spread over thirty years and is not a wage;
* **life-hours** -- the hours of paid work buying would have cost, against the hours
  building does.

And it says what it does not promise: the 2.5 times is one over the labor share, the
frame is only the frame, and the house-labor comparison is corrected on camera.

The pictures are the simulator's solved dome, the harvest's wedge pile, and three new
scenes: the long chain against the short one, a wedge beside a two-by-four end-on, and
a jig panel whose overlong members are cut flush.
"""

from __future__ import annotations

import math
from collections import namedtuple
from pathlib import Path

import numpy as np

from . import house_economics as he
from . import lesson_harvest as lh
from . import why_build_economics as wb
from .book_tokens import resolve as _resolve
from .callouts import Callout, Tally
from .lessons import Chapter, Lesson
from .render_kit import AMBER, GREEN, WorldLabel, clamp, ease_in_out, smoothstep
from .visual_objects import draw, rgb, stage_for


def _t(text: str) -> str:
    return _resolve(text, strict=True)


CYAN_LABEL = (61, 211, 255)
MUTED_LABEL = (169, 188, 203)
RAIL = (0.16, 0.22, 0.29, 1.0)
POST_LONG = (0.30, 0.36, 0.44, 1.0)
POST_SHORT = (0.62, 0.45, 0.22, 1.0)
JIG_BED = (0.13, 0.19, 0.25, 1.0)
STOP = (0.78, 0.24, 0.24, 1.0)


# ----------------------------------------------------------------------
# Scenes
# ----------------------------------------------------------------------

def scene_wb_dome(app, opaque, transparent, p: float) -> None:
    """The simulator's solved dome, the same one the harvest film prices."""
    lh.scene_hv_dome(app, opaque, transparent, p)


def scene_wb_harvest(app, opaque, transparent, p: float) -> None:
    """Two trees as a pile of wedges, the raw material every figure starts from."""
    lh.scene_hv_harvest(app, opaque, transparent, p)


LONG_CHAIN = (("dollar", "INCOME"), ("cross", "TAX"), ("board", "STORE LUMBER"),
              ("person", "CONTRACTOR"), ("dollar", "MARKUP"), ("calendar", "LOAN"),
              ("clock", "INTEREST"), ("house", "SHELTER"))
SHORT_CHAIN = (("pine", "TREE"), ("split", "WEDGE"), ("ruler", "JIG"),
               ("dome", "SHELL"))


def scene_wb_chain(app, opaque, transparent, p: float) -> None:
    """The long chain from an hour to a house, then the short one, a station at a time."""
    stage = stage_for(app, opaque, transparent)
    rows = ((LONG_CHAIN, 2.4, 2.0, POST_LONG, MUTED_LABEL, 0.02, 0.055),
            (SHORT_CHAIN, -2.2, 2.8, POST_SHORT, rgb(AMBER), 0.50, 0.07))
    for chain, y, spacing, post, label_colour, start, step in rows:
        count = len(chain)
        xs = [(index - (count - 1) * 0.5) * spacing for index in range(count)]
        opaque.box((0.0, y, 0.10), (xs[-1] - xs[0] + 1.8, 0.55, 0.20), RAIL)
        for index, ((icon, label), x) in enumerate(zip(chain, xs)):
            shown = smoothstep(clamp((p - start - index * step) / 0.06))
            if shown <= 0.0:
                continue
            opaque.box((x, y, 0.32), (0.75, 0.75, 0.26), post)
            stage.icon(np.array([x, y, 1.35]), icon, 70.0, None, shown, 0.0)
            if shown > 0.5:
                app.world_labels.append(WorldLabel(np.array([x, y - 0.6, 0.15]),
                                                   label, label_colour))


INCH = 2.0 / 12.0
"""Drawing units per inch in the cross-section scene: the two-by-four object's largest
scale, so the board and the wedge are drawn at the same real size."""


def scene_wb_section(app, opaque, transparent, p: float) -> None:
    """The log split into wedges, end-on, beside a dressed two-by-four end-on.

    Both are drawn at the same real size, so one wedge and one board can be compared by
    eye; the figures are on the callouts. The disc is drawn facing both ways, because
    its drawing has only a front and this camera stands behind the harvest's.
    """
    from .book_tokens import VERSUS_LOG_IN
    radius = VERSUS_LOG_IN * 0.5 * INCH
    spread = smoothstep(clamp(p * 2.2))
    for turn in (0.0, 180.0):
        disc = stage_for(app, opaque, transparent, origin=(-1.3, 0.0, 0.0),
                         yaw_deg=turn)
        draw(disc, "section_disc", radius=radius, pieces=8, spread=spread, lift=0.25)
    board = stage_for(app, opaque, transparent, origin=(1.3, 0.0, 0.0), yaw_deg=90.0)
    draw(board, "board_2x4", length_ft=1.0, units_per_ft=12.0 * INCH, on_edge=1.0,
         lift=0.25)
    top = 0.25 + radius * 2.0 + 0.45
    app.world_labels.extend([
        WorldLabel(np.array([-1.3, 0.0, top]),
                   _t("{{versus.diameter_in}}-INCH LOG IN {{tree.sectors}} WEDGES"),
                   rgb(AMBER)),
        WorldLabel(np.array([1.3, 0.0, top]), "DRESSED 2X4", CYAN_LABEL),
    ])


def _triangle(side: float) -> list[np.ndarray]:
    circum = side / math.sqrt(3.0)
    return [np.array([circum * math.cos(math.radians(a)),
                      circum * math.sin(math.radians(a)), 0.0])
            for a in (90.0, 210.0, 330.0)]


def scene_wb_panel(app, opaque, transparent, p: float) -> None:
    """Three overlong members located in a jig, then cut flush: locate, then cut."""
    side, depth, over = 3.4, 0.34, 0.6
    corners = _triangle(side)
    opaque.box((0.0, 0.0, 0.06), (side * 1.45, side * 1.3, 0.12), JIG_BED)
    for corner in corners:
        opaque.box((corner[0], corner[1], 0.30), (0.34, 0.34, 0.36), STOP)
    arrive = ease_in_out(clamp(p / 0.35))
    cut = smoothstep(clamp((p - 0.58) / 0.22))
    length = side + 2.0 * over * (1.0 - cut)
    for index in range(3):
        a, b = corners[index], corners[(index + 1) % 3]
        middle = (a + b) * 0.5
        outward = middle / max(1e-9, float(np.linalg.norm(middle)))
        middle = middle + outward * 1.6 * (1.0 - arrive)
        direction = b - a
        yaw = math.degrees(math.atan2(direction[1], direction[0]))
        stage = stage_for(app, opaque, transparent, origin=tuple(middle), yaw_deg=yaw)
        draw(stage, "wedge_member", length=length, depth=depth, lift=0.34,
             roll_deg=0.0)
    label_point = corners[0] + np.array([0.0, 0.0, 1.3])
    if p < 0.58:
        app.world_labels.append(WorldLabel(label_point, "LOCATE FIRST", rgb(GREEN)))
        if arrive > 0.9:
            app.world_labels.append(WorldLabel(corners[1] + np.array([-0.8, 0.0, 0.9]),
                                               "LEFT LONG", rgb(AMBER)))
    else:
        app.world_labels.append(WorldLabel(label_point, "CUT SECOND", rgb(AMBER)))


SCENES = {"wb_dome": scene_wb_dome, "wb_harvest": scene_wb_harvest,
          "wb_chain": scene_wb_chain, "wb_section": scene_wb_section,
          "wb_panel": scene_wb_panel}


# ----------------------------------------------------------------------
# Camera
# ----------------------------------------------------------------------

_As = namedtuple("_As", "slug stage overlay")


def why_camera(app, chapter, progress: float, width: int, height: int):
    """(eye, target, field of view): the harvest's own dome and pile cameras, and a
    fixed stage for each new scene."""
    p = clamp(progress)
    if chapter.stage == "wb_dome":
        return lh.harvest_camera(app, _As(chapter.slug, "hv_dome", chapter.overlay),
                                 p, width, height)
    if chapter.stage == "wb_harvest":
        return lh.harvest_camera(app, _As("cost", "hv_harvest", chapter.overlay),
                                 p, width, height)
    if chapter.stage == "wb_chain":
        # Aimed a little in front of the near row, so both rows sit above the headline.
        target = np.array([0.0, -0.8, 0.3])
        eye = lh._orbit(target, -90.0 + 8.0 * (p - 0.5), 30.0, 14.5 - 1.0 * p)
        return eye, target, 46.0
    if chapter.stage == "wb_section":
        # Aimed above the pieces so they sit below the callouts and above the headline.
        target = np.array([0.0, 0.0, 1.5])
        eye = lh._orbit(target, -90.0 + 14.0 * (p - 0.5), 8.0, 8.5)
        return eye, target, 38.0
    target = np.array([0.0, 0.0, 0.35])
    eye = lh._orbit(target, -100.0 + 24.0 * ease_in_out(p), 52.0, 8.2)
    return eye, target, 44.0


# ----------------------------------------------------------------------
# Chapters
# ----------------------------------------------------------------------

def _c(slug: str, title: str, promise: str, narration: str, duration: float,
       stage: str = "wb_dome", overlay: str | None = None,
       equations: tuple[str, ...] = (), callouts: tuple = ()) -> Chapter:
    spoken = _t(narration)
    from .audio import SPEECH_DELAY, TAIL_PADDING
    from .callouts import characters_per_second
    estimated = SPEECH_DELAY + len(spoken) / characters_per_second() + TAIL_PADDING
    return Chapter(slug, "00", title, _t(promise), (spoken,), equations,
                   max(duration, round(estimated, 1)), (0.0, 20.0, 20.0), stage,
                   overlay, callouts)


_AUTHORED: tuple[Chapter, ...] = (
    _c("question", "How much shelter does an hour buy",
       "Not how cheap the house is. How much shelter an hour buys.",
       "The case for this dome is not that it makes a house cheap. It is that it "
       "changes the trade between a person, their time, raw wood and shelter. This "
       "is one shell, {{why.sqft}} square feet, from {{method_a.whole_trees}} trees. "
       "The question worth asking is not how cheap the house is, but how much "
       "shelter one hour of your life can buy, and this way of building changes the "
       "answer.",
       16.0,
       callouts=(
           Callout("{{why.sqft}}", unit="sq ft of shell", icon="dome",
                   cue="{{why.sqft}} square feet", slot="left", hold=None),
           Callout("{{method_a.whole_trees}}", unit="trees", icon="pine",
                   cue="from {{method_a.whole_trees}} trees", slot="right",
                   hold=None),
       )),
    _c("chain", "A long chain, and a short one",
       "Income, tax, store, contractor, loan. Or tree, wedge, jig, shell.",
       "Conventional housing asks you to join a long chain. You sell hours for "
       "money, pay tax on it, buy lumber that was sawn, dried, shipped, stocked and "
       "marked up, hire the labor to put it together, and very often borrow for all "
       "of it for decades. This system shortens the chain. A tree is split into "
       "wedges, the wedges go into a jig, and the jig makes the shell. Part of your "
       "labor turns straight into structure, without passing through a paycheck, a "
       "tax bill, a store and a loan on the way.",
       24.0, stage="wb_chain"),
    _c("tree", "The tree is the product",
       "Split, not sawn: the round log keeps its wood.",
       "A sawmill forces a round tree into rectangles. The wedge does not. An "
       "{{versus.diameter_in}} inch log splits into {{tree.sectors}} sectors, and "
       "each one keeps {{versus.wedge_area_in2}} square inches of wood, against "
       "{{versus.board_area_in2}} in a dressed two by four. That does not make every "
       "wedge stronger than every board; from a log that small, a single wedge is "
       "the weaker stick in bending. What it means is that very little happens "
       "between the tree and the frame: {{route.wedge_steps}} operations, where a "
       "graded board takes {{route.mill_steps}}.",
       26.0, stage="wb_section",
       callouts=(
           Callout("{{versus.wedge_area_in2}}", unit="sq in, one wedge",
                   note="from an {{versus.diameter_in}}-inch log", icon="split",
                   cue="keeps {{versus.wedge_area_in2}}", slot="left", hold=7.0),
           Callout("{{versus.board_area_in2}}", unit="sq in, a dressed 2x4",
                   icon="board", cue="against {{versus.board_area_in2}}",
                   slot="right", hold=6.0),
           Callout("{{versus.strength_pct}}%", unit="bending strength", tone="warn",
                   cue="the weaker stick in bending", slot="left", hold=None),
           Callout("{{route.wedge_steps}}", unit="operations, tree to frame",
                   note="a graded board takes {{route.mill_steps}}", icon="check",
                   cue="{{route.wedge_steps}} operations", slot="right", hold=None),
       )),
    _c("geometry", "The geometry does some of the work",
       "A wedge arrives with its angle already in it.",
       "An eighth of a log arrives with two split faces {{tree.sector_angle_deg}} "
       "degrees apart. The dome's panels fold at only {{seam.distinct_angles}} "
       "angles, {{seam.fold_a_deg}} and {{seam.fold_b_deg}} degrees. The wedge does "
       "not match them exactly, but it starts with useful angle already in it, and a "
       "shaped key takes up the rest, so nobody has to manufacture every angle out "
       "of a rectangle. That is the rule the whole system runs on: do not make every "
       "piece perfect; make the system force imperfect pieces into the right "
       "relationship.",
       26.0,
       callouts=(
           Tally((
               Callout("{{tree.sector_angle_deg}}°", unit="between a wedge's faces",
                       cue="{{tree.sector_angle_deg}} degrees apart"),
               Callout("{{seam.fold_a_deg}}°", unit="the tighter fold", op="·",
                       tone="note", cue="{{seam.fold_a_deg}} and"),
               Callout("{{seam.fold_b_deg}}°", unit="the wider fold", op="·",
                       tone="note", cue="{{seam.fold_b_deg}} degrees"),
           ), title="the angles", slot="right", icon="split", check=False),
       )),
    _c("jig", "Locate first, cut second",
       "The jig solves the geometry once, not for every stick.",
       "Custom timber work means measuring, transferring angles, fitting, checking "
       "and trimming, again and again. Here the jig decides where each member "
       "belongs and which way it turns. The members are left long, their ends hang "
       "past the triangle, and once the jig holds all three in their true "
       "relationship, the excess is cut flush. Locate accurately first; cut "
       "accurately second. The hard geometry is solved once, in the jig, and a "
       "complicated dome becomes {{frame.panels}} repeats of one job.",
       26.0, stage="wb_panel",
       callouts=(
           Callout("{{frame.panels}}", unit="panels, one jig",
                   note="{{frame.members}} members", icon="ruler",
                   cue="becomes {{frame.panels}} repeats", slot="left", hold=None),
       )),
    _c("sources", "The figures this rests on",
       "The author's round numbers, beside the published ones.",
       "Now the money, and first what it rests on. These are my own round figures: "
       "bought space at {{why.usd_per_sqft}} dollars a square foot, framing as "
       "{{why.framing_pct}} percent of it, {{why.hours}} hours of hands-on shell "
       "work, and a {{why.mortgage_pct}} percent mortgage over "
       "{{why.mortgage_years}} years. Beside them are the published ones. A new "
       "manufactured home averages {{trailer.per_sqft}} dollars a square foot, and a "
       "new site-built house about {{why.site_usd_per_sqft}} without the land. My "
       "figures sit on the cautious side of both.",
       26.0, overlay="math", equations=wb.source_lines()),
    _c("production", "What an hour produces",
       "Not a paycheck. Value you no longer have to buy.",
       "{{why.sqft}} square feet in {{why.hours}} hours is {{why.sqft_per_hour}} "
       "square feet an hour. At {{why.usd_per_sqft}} dollars a square foot, that "
       "floor is worth {{why.space_value}} dollars finished, but framing did not "
       "create all of it; plumbing, wiring, windows and finishes are still to come. "
       "So take only the framing, {{why.framing_pct}} percent of it: "
       "{{why.framing_value}} dollars. Divided by {{why.hours}} hours, that is "
       "{{why.rate}} dollars an hour. Nobody hands me that as a wage. A wage is what "
       "someone pays you for your hour; this is what your hour saves you from having "
       "to buy.",
       30.0,
       callouts=(
           Callout("{{why.sqft_per_hour}}", unit="sq ft an hour", icon="ruler",
                   cue="{{why.sqft_per_hour}} square feet an hour", slot="left",
                   hold=4.0),
           Tally((
               Callout("{{why.sqft}} sq ft", unit="of shell",
                       cue="{{why.sqft}} square feet in"),
               Callout("${{why.usd_per_sqft}}", unit="a sq ft", op="×",
                       cue="At {{why.usd_per_sqft}} dollars"),
               Callout("${{why.space_value}}", unit="finished space", op="=",
                       cue="worth {{why.space_value}}"),
               Callout("{{why.framing_share}}", unit="framing's share", op="×",
                       cue="So take only the framing"),
               Callout("${{why.framing_value}}", unit="of framing", op="=",
                       tone="total", cue="{{why.framing_value}} dollars"),
               Callout("{{why.hours}}", unit="hours", op="÷",
                       cue="Divided by {{why.hours}} hours"),
               Callout("${{why.rate}}", unit="an hour", op="=", tone="total",
                       cue="{{why.rate}} dollars an hour"),
           ), title="production value", slot="right", icon="dollar"),
       )),
    _c("leverage", "Why the hour beats a wage",
       "It replaces the wood as well as the work.",
       "Of that {{why.framing_value}} dollars, the labor is {{why.labor_pct}} "
       "percent: {{why.labor_value}} dollars, and over the same {{why.hours}} hours "
       "that is {{why.labor_rate}} dollars an hour. That is the framing labor alone. "
       "The dome way produces {{why.rate}}, which is {{why.leverage}} times as much, "
       "an index of {{why.index}} where framing labor alone scores a hundred. Be "
       "clear about where that comes from: it is one over the labor share. You "
       "supply the labor, and you also replace the wood you would have bought. That "
       "second part is exactly what a wage comparison leaves out.",
       30.0,
       callouts=(
           Callout("{{why.index}}", unit="value index",
                   note="framing labor alone scores a hundred", tone="total",
                   icon="check", cue="an index of {{why.index}}", slot="left",
                   hold=None),
           Tally((
               Callout("${{why.framing_value}}", unit="of framing",
                       cue="Of that {{why.framing_value}} dollars"),
               Callout("{{why.labor_share}}", unit="labor's share", op="×",
                       cue="the labor is {{why.labor_pct}} percent"),
               Callout("${{why.labor_value}}", unit="of labor", op="=",
                       cue="{{why.labor_value}} dollars"),
               Callout("{{why.hours}}", unit="hours", op="÷",
                       cue="same {{why.hours}} hours"),
               Callout("${{why.labor_rate}}", unit="an hour, labor alone", op="=",
                       cue="{{why.labor_rate}} dollars an hour"),
               Callout("{{why.leverage}}×", unit="the dome's hour", op="·",
                       tone="total", cue="{{why.leverage}} times as much"),
           ), title="the labor benchmark", slot="right", icon="person"),
       )),
    _c("debt", "Debt makes it larger",
       "An avoided dollar can be an avoided interest-bearing dollar.",
       "Now suppose that framing would otherwise ride on a {{why.mortgage_years}} "
       "year mortgage at {{why.mortgage_pct}} percent. Then {{why.framing_value}} "
       "dollars does not stay {{why.framing_value}}; it becomes {{why.financed}} "
       "dollars of payments. Spread over the same {{why.hours}} hours, that is "
       "{{why.financed_rate}} dollars an hour. That is not a wage, and it is not "
       "today's money: it is payments that never have to be made, stretched across "
       "{{why.mortgage_years}} years. Today's value is still {{why.rate}} dollars an "
       "hour. But a dollar avoided before it enters a mortgage is a dollar that never "
       "collects interest.",
       30.0,
       callouts=(
           Callout("{{why.mortgage_pct}}%", unit="for {{why.mortgage_years}} years",
                   note="an illustrative rate", icon="calendar",
                   cue="at {{why.mortgage_pct}} percent", slot="left", hold=5.0),
           Tally((
               Callout("${{why.financed}}", unit="of payments",
                       cue="becomes {{why.financed}}"),
               Callout("{{why.hours}}", unit="hours", op="÷",
                       cue="Spread over the same {{why.hours}} hours"),
               Callout("${{why.financed_rate}}", unit="an hour, avoided", op="=",
                       tone="total", cue="{{why.financed_rate}} dollars an hour"),
           ), title="debt-avoidance value", slot="right", icon="calendar"),
       )),
    _c("interest", "Interest builds nothing",
       "No bedroom, no wall, no square foot.",
       "Take a {{why.loan}} dollar mortgage at the same rate. Over "
       "{{why.mortgage_years}} years you pay {{why.loan_interest}} dollars of "
       "interest on it, {{why.loan_total}} in all. At {{why.usd_per_sqft}} dollars a "
       "square foot, the interest alone would buy {{why.interest_sqft}} square feet. "
       "Interest builds no bedroom, no workshop, no wall. It is the price of having "
       "the house before you have the money. Building directly does something else: "
       "effort becomes equity. Hours become members, members become panels, and "
       "panels become square feet.",
       28.0, stage="wb_harvest",
       callouts=(
           Tally((
               Callout("${{why.loan}}", unit="borrowed",
                       cue="a {{why.loan}} dollar mortgage"),
               Callout("${{why.loan_interest}}", unit="interest", op="+",
                       cue="{{why.loan_interest}} dollars of interest"),
               Callout("${{why.loan_total}}", unit="repaid", op="=", tone="total",
                       cue="{{why.loan_total}} in all"),
               Callout("{{why.interest_sqft}} sq ft", unit="the interest would buy",
                       op="·", tone="note",
                       cue="{{why.interest_sqft}} square feet"),
           ), title="a mortgage", slot="right", icon="house"),
       )),
    _c("life_hours", "Count it in hours of your life",
       "Money is stored labor.",
       "Here is the comparison that matters most. Buying that {{why.framing_value}} "
       "dollar frame, at {{why.wage}} dollars an hour take-home, takes "
       "{{why.buy_hours}} hours of work. Building it takes {{why.hours}} hours, plus "
       "{{why.cash_hours}} more to earn its {{why.cash}} dollars of cash, "
       "{{why.build_hours}} hours in all. That keeps {{why.kept_hours}} hours of your "
       "life, {{why.kept_weeks}} full working weeks, on one shell. And the typical "
       "worker takes home less than {{why.wage}}, about {{wage.take_home}} an hour, "
       "which makes buying cost {{why.take_home_buy_hours}} hours instead.",
       30.0,
       callouts=(
           Tally((
               Callout("${{why.framing_value}}", unit="to buy the frame",
                       cue="Buying that {{why.framing_value}} dollar frame"),
               Callout("${{why.wage}}", unit="an hour, take-home", op="÷",
                       cue="at {{why.wage}} dollars an hour"),
               Callout("{{why.buy_hours}}", unit="hours to buy it", op="=",
                       cue="takes {{why.buy_hours}} hours"),
               Callout("{{why.build_hours}}", unit="hours to build it", op="−",
                       cue="{{why.build_hours}} hours in all"),
               Callout("{{why.kept_hours}}", unit="hours of life kept", op="=",
                       tone="total", cue="keeps {{why.kept_hours}} hours"),
           ), title="life-hours", slot="right", icon="clock"),
           Callout("{{why.take_home_buy_hours}}", unit="hours, median pay",
                   note="to buy it at ${{wage.take_home}} an hour take-home",
                   tone="note", icon="clock",
                   cue="cost {{why.take_home_buy_hours}} hours", slot="left",
                   hold=None),
       )),
    _c("rule", "When to build, and when to buy",
       "Build while your hour creates more than it earns.",
       "This is a rule, not an ideology. What building earns per hour is the money "
       "it avoids, less the cash it still costs, over the hours it takes. "
       "{{why.framing_value}} less {{why.cash}} is {{why.net}}, and over "
       "{{why.hours}} hours that is {{why.breakeven}} dollars an hour. If you take "
       "home less than that, those hours are worth more building than working extra "
       "to buy the same frame. If you take home a good deal more, buying may be the "
       "better use of your time. Build while the value your hour creates beats what "
       "it earns after tax.",
       28.0, stage="wb_harvest",
       callouts=(
           Tally((
               Callout("${{why.framing_value}}", unit="avoided",
                       cue="{{why.framing_value}} less"),
               Callout("${{why.cash}}", unit="cash it still costs", op="−",
                       cue="less {{why.cash}}"),
               Callout("${{why.net}}", unit="kept", op="=", cue="is {{why.net}}"),
               Callout("{{why.hours}}", unit="hours", op="÷",
                       cue="over {{why.hours}} hours"),
               Callout("${{why.breakeven}}", unit="an hour: the break-even", op="=",
                       tone="total", cue="{{why.breakeven}} dollars an hour"),
           ), title="the break-even wage", slot="right", icon="check"),
       )),
    _c("shocks", "Out of the commodity chain",
       "Every member from a nearby tree is one less price shock.",
       "A conventional house also runs a long critical path, about {{why.weeks}} "
       "weeks from start to finish, carrying financing, weather, scheduling and "
       "overhead the whole way. And it rides on commodity lumber. In the spring of "
       "twenty twenty one, framing lumber topped {{lumber.peak}} dollars a thousand "
       "board feet and added {{lumber.added}} dollars to an average new home. A dome "
       "still needs fasteners, glazing, wiring, plumbing and a foundation. But every "
       "structural member cut from a nearby tree instead of bought at a yard is one "
       "less exposure to that market. A tree on the land stops being scenery and "
       "becomes inventory.",
       30.0, stage="wb_harvest",
       callouts=(
           Callout("{{why.weeks}}", unit="weeks, a new house",
                   note="start to finish, the Census average", icon="calendar",
                   cue="about {{why.weeks}} weeks", slot="left", hold=6.0),
           Callout("${{lumber.added}}", unit="added by the lumber spike",
                   note="lumber topped ${{lumber.peak}} per thousand board feet",
                   icon="board", cue="added {{lumber.added}}", slot="right",
                   hold=None),
       )),
    _c("score", "The economic score",
       "One shell, on one sheet.",
       "Put one cycle on a single sheet. {{why.sqft}} square feet of shell in "
       "{{why.hours}} hours. {{why.framing_value}} dollars of commercial framing "
       "displaced. {{why.rate}} dollars an hour of production value, "
       "{{why.leverage}} times the framing labor alone. {{why.financed}} dollars of "
       "mortgage payments avoided, {{why.financed_rate}} an hour, and not a wage. "
       "{{why.kept_hours}} hours of life kept. A break-even of {{why.breakeven}} "
       "dollars an hour. And one shell a year for {{why.horizon}} years is "
       "{{why.lifetime}} dollars of framing and {{why.lifetime_sqft}} square feet.",
       30.0, overlay="math", equations=wb.score_lines()),
    _c("honest", "What the model does not promise",
       "A model, not a guarantee.",
       "None of this is a guarantee; it is a model. The {{why.rate}} dollars an hour "
       "is money not spent, not money earned, and it only counts if you would "
       "otherwise have bought the frame. The frame is {{house.framing_pct}} percent "
       "of what a new house costs to build, and permits, wiring, plumbing, windows "
       "and finishes are still ahead, some of it needing a licensed trade and an "
       "inspection. The house labor budget I once compared against was "
       "{{why.author_house_labor}} dollars; the builders' survey puts that house's "
       "labor nearer {{why.house_labor}}, about {{why.burn}} dollars per working "
       "hour of the build, so the dome's {{why.rate}} is {{why.burn_pct}} percent of "
       "it, not the same. And my {{why.framing_value}} dollar frame is cheaper than "
       "either published price, {{why.trailer_value}} at a manufactured home's rate "
       "and {{value.frame_buy}} at a new house's, so the case is made at its "
       "weakest.",
       40.0,
       callouts=(
           Callout("{{why.burn_pct}}%", unit="of the survey's rate",
                   note="${{why.burn}} a work-hour, not ${{why.author_burn}}",
                   tone="warn", cue="is {{why.burn_pct}} percent of it",
                   slot="left", hold=None),
           Callout("${{why.framing_value}}", unit="my frame",
                   note="published: ${{why.trailer_value}} and ${{value.frame_buy}}",
                   tone="note", icon="check",
                   cue="cheaper than either published price", slot="right",
                   hold=None),
       )),
    _c("why", "The why",
       "More shelter from each hour of a finite life.",
       "So the reason to build this way is not that domes look different, or that "
       "ordinary houses are bad, or that lumber is useless. It is that conventional "
       "housing is built around buying highly processed materials and buying "
       "specialized labor, and this asks whether the owner can take back part of "
       "both. If the answer is yes, the rest follows: less processing, less bought "
       "lumber and labor, less financing, less interest, less exposure to prices and "
       "schedules, and more use of what is already standing on the land. The "
       "question is not how cheap the house is, but how much shelter an hour of "
       "your life can buy. On these numbers, this way of building changes that "
       "exchange rate. That is the reason.",
       34.0,
       callouts=(
           Tally((
               Callout("${{why.rate}}", unit="an hour, today's value",
                       cue="how much shelter an hour"),
               Callout("${{why.financed_rate}}", unit="an hour of payments avoided",
                       op="·", tone="note", cue="changes that exchange rate"),
               Callout("{{why.kept_hours}}", unit="hours of life kept, one shell",
                       op="·", tone="total", cue="That is the reason"),
           ), title="one hour, three ways", slot="right", icon="clock", check=False),
       )),
)

CHAPTERS: tuple[Chapter, ...] = tuple(
    Chapter(c.slug, f"{index + 1:02d}", c.title, c.promise, c.narration,
            c.equations, c.duration, c.camera, c.stage, c.overlay, c.callouts)
    for index, c in enumerate(_AUTHORED))

MONEY_CHAPTERS = ("production", "leverage", "debt", "interest", "life_hours", "rule",
                  "shocks", "score", "honest", "why")
"""Every chapter that quotes the author's or a published money figure: all after the
screen that says which is which."""


# ----------------------------------------------------------------------
# The written version
# ----------------------------------------------------------------------

def why_document() -> str:
    """The script as a document: every chapter's words, then what is on screen.

    Generated from the chapters themselves, so the written piece and the film say the
    same thing to the dollar, and the sources close it.
    """
    from .callouts import resolve
    lines = [f"# {WHY_BUILD_LESSON.title}", "",
             "*Every figure below is computed from `two_v_demo/why_build_economics.py` "
             "and `two_v_demo/house_economics.py`; the author's own round figures are "
             "listed at the end and labelled as the author's.*", ""]
    for chapter in WHY_BUILD_LESSON.chapters:
        lines += [f"## {chapter.title}", "", f"**{chapter.promise}**", "",
                  *chapter.narration, ""]
        shown = []
        for entry in chapter.callouts:
            rows = entry.rows if isinstance(entry, Tally) else (entry,)
            if isinstance(entry, Tally) and entry.title:
                shown += ["", f"*{entry.title}*", ""]
            for row in rows:
                text = f"{row.op} {resolve(row.text)} {resolve(row.unit)}".strip()
                note = resolve(row.note)
                shown.append(f"- {text}" + (f" ({note})" if note else ""))
        shown += [f"- {line}" for line in chapter.equations]
        if shown:
            lines += ["On screen:", "", *shown, ""]
    lines += ["## What the figures rest on", "",
              "| Figure | Value | Kind | Why it is believed |", "|---|---|---|---|"]
    for source in wb.SOURCES + tuple(s for s in he.SOURCES
                                      if s.key in ("shell_hours", "labor_share",
                                                   "house_price",
                                                   "mhs_2023_usd_per_sqft",
                                                   "nahb_sale_price",
                                                   "wage_all_workers",
                                                   "lumber_2021_added",
                                                   "lumber_flcp_peak")):
        why = source.note + (f" Source: {source.cite}" if source.cite else "")
        lines.append(f"| `{source.key}` | {source.value:,g} {source.units} | "
                     f"{source.kind} | {why} |")
    lines.append("")
    return "\n".join(lines)


def write_why_document(path: str | Path) -> Path:
    """Write the script document, refusing to replace one that exists."""
    from .deliverables import next_version_path
    target = next_version_path(Path(path))
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(why_document(), encoding="utf-8")
    return target


# ----------------------------------------------------------------------
# Proof
# ----------------------------------------------------------------------

def validate_why_build_lesson() -> None:
    import re

    from .callouts import check_tally
    from .render_kit import TriangleBatch

    wb.validate_why_build()
    he.validate_house_economics()
    WHY_BUILD_LESSON.validate()

    for chapter in WHY_BUILD_LESSON.chapters:
        for text in (chapter.promise, *chapter.narration):
            assert "{{" not in text, (chapter.slug, text)
    order = [chapter.slug for chapter in WHY_BUILD_LESSON.chapters]
    for slug in MONEY_CHAPTERS:
        assert order.index("sources") < order.index(slug), slug
    assert order.index("honest") < order.index("why")
    for chapter in WHY_BUILD_LESSON.chapters:
        for entry in chapter.callouts:
            if isinstance(entry, Tally) and entry.check:
                assert not check_tally(entry), (chapter.slug, check_tally(entry))

    class _Probe:
        def __init__(self, index):
            self.world_labels, self.world_icons = [], []
            self.chapters, self.chapter_index = WHY_BUILD_LESSON.chapters, index

    for index, chapter in enumerate(WHY_BUILD_LESSON.chapters):
        painter = SCENES[chapter.stage]
        for p in (0.0, 0.3, 0.6, 1.0):
            probe = _Probe(index)
            opaque, transparent = TriangleBatch(), TriangleBatch()
            painter(probe, opaque, transparent, p)
            assert opaque.vertices or transparent.vertices, (chapter.slug, p)
            eye, target, fov = why_camera(probe, chapter, p, 1920, 1080)
            assert np.all(np.isfinite(eye)) and np.all(np.isfinite(target))
            assert float(np.linalg.norm(eye - target)) > 1.0, (chapter.slug, p)
    for chapter in _AUTHORED:
        assert not re.search(r"\d", chapter.title), chapter.title
    assert "{{" not in why_document()


WHY_BUILD_LESSON = Lesson(
    key="why_build",
    brand="TWO TREES",
    title="Why Build This Way",
    chapters=CHAPTERS,
    scenes=SCENES,
    selftest=validate_why_build_lesson,
    snapshot_prefix="why_build",
    style="hype",
    camera_fn=why_camera,
    label_layout="declutter",
)
