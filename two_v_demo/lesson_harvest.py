"""Two Trees, All at Once: the harvest, from a standing pine to a cloud of wedges.

A short film, and the worked example for three pieces of the engine used together:

* **visual objects** -- :mod:`two_v_demo.visuals_forest`'s ``harvest`` object, one
  thing with four knobs (fell, limb, buck, explode) driven across the chapters;
* **number callouts** -- :mod:`two_v_demo.callouts`: single figures and checked
  tallies that land on the words that say them;
* **pinned icons** -- the chainsaw pictogram at the fell line and at every cut.

Nothing in the words or on the screen is typed. The narration and headlines are
written in the book's token language and resolved when this module loads, so the
voice says what :mod:`two_v_demo.book_math` computes; the callouts quote the same
tokens; and the one figure that rests on a guess -- the saw's fuel tank -- is shown
as a range, after a screen that says which numbers were measured and which were not.

The second half asks what the fortnight is worth. Where a new house's time and money
go, what labor really is of its price, how a manufactured home splits instead, what
the frame is worth an hour, and where the saving actually comes from -- all from
:mod:`two_v_demo.house_economics`, after a screen that says which of those figures
are published, which are the author's, which are decided and which are guesses. It
ends on the half of the sum that does not flatter the dome, and shows the simulator's
own solved dome while it talks about the dome.
"""

from __future__ import annotations

import math

import numpy as np

from . import house_economics as he
from . import visuals_forest as vf
from .book_tokens import resolve as _resolve
from .callouts import Callout, Tally
from .lessons import Chapter, Lesson
from .render_kit import AMBER, GREEN, WHITE, WorldLabel, clamp, ease_in_out, smoothstep
from .visual_objects import draw, rgb, stage_for


UPF = 0.25
"""Scene units per real foot: a seventy-foot pine stands 17.5 units tall."""
ORIGIN = np.array([-9.0, 0.0, 0.0])
"""Where the tree stands, so that it lands across the middle of the stage."""
DOME_ORIGIN = np.array([0.0, 0.0, 0.0])
"""Where the finished dome stands in the chapters that price it."""


def _t(text: str) -> str:
    """Resolve the book's number tokens in a line the film speaks or shows."""
    return _resolve(text, strict=True)


def _world(point_ft) -> np.ndarray:
    return ORIGIN + np.asarray(point_ft, dtype=np.float64) * UPF


def _span(p: float, start: float, end: float) -> float:
    return clamp((p - start) / (end - start))


def _dome_radius() -> float:
    """The priced floor's radius, at the same scale as the tree it came from."""
    return math.sqrt(he.dome_floor_sqft() / math.pi) * UPF


# ----------------------------------------------------------------------
# What the harvest object is doing in each chapter
# ----------------------------------------------------------------------

def _knobs(slug: str, p: float) -> dict[str, float]:
    if slug == "tree":
        return {"fell": 0.0, "limb": 0.0, "buck": 0.0, "explode": 0.0}
    if slug == "fell":
        return {"fell": _span(p, 0.06, 0.92), "limb": 0.0, "buck": 0.0,
                "explode": 0.0}
    if slug == "explode":
        return {"fell": 1.0, "limb": smoothstep(_span(p, 0.0, 0.16)),
                "buck": _span(p, 0.17, 0.30),
                "explode": ease_in_out(_span(p, 0.32, 0.66))}
    return {"fell": 1.0, "limb": 1.0, "buck": 1.0, "explode": 1.0}


def _slug(app) -> str:
    chapters = getattr(app, "chapters", None)
    index = getattr(app, "chapter_index", None)
    if not chapters or index is None:
        return "tree"
    return chapters[index].slug


def scene_hv_harvest(app, opaque, transparent, p: float) -> None:
    """The harvest object, and the words that name its parts while they matter."""
    slug = _slug(app)
    knobs = _knobs(slug, p)
    stage = stage_for(app, opaque, transparent, origin=ORIGIN)
    anchors = draw(stage, "harvest", units_per_ft=UPF, **knobs)
    if slug != "fell":
        return
    fell = knobs["fell"]
    notch, back = vf._phase(fell, "notch"), vf._phase(fell, "back_cut")
    point = anchors["fell_point"]
    lift = np.array([0.0, 0.0, 1.6])
    if 0.15 < notch < 1.0:
        app.world_labels.append(WorldLabel(point + lift, "FACE NOTCH", rgb(AMBER)))
    elif 0.1 < back < 1.0:
        app.world_labels.append(WorldLabel(point + lift, "BACK CUT", rgb(AMBER)))
    elif vf.FELL_PHASES["fall"][0] <= fell < 0.7:
        app.world_labels.append(WorldLabel(point + lift, "THE HINGE STEERS IT",
                                           rgb(GREEN)))


def scene_hv_dome(app, opaque, transparent, p: float) -> None:
    """The dome the wedges make: the simulator's solved dome, keys and all.

    A film that talks about the wedge dome shows the simulator's dome, sized to the
    floor the value chapters price, at the scale the tree was drawn.
    """
    stage = stage_for(app, opaque, transparent, origin=DOME_ORIGIN)
    draw(stage, "solved_dome", radius=_dome_radius(), orientation=0, keys=1.0,
         alpha=1.0)


# ----------------------------------------------------------------------
# The camera, which follows the tree down and then walks round the wedges
# ----------------------------------------------------------------------

def _orbit(target, yaw_deg: float, pitch_deg: float, distance: float) -> np.ndarray:
    yaw, pitch = math.radians(yaw_deg), math.radians(pitch_deg)
    return np.asarray(target, dtype=np.float64) + distance * np.array([
        math.cos(pitch) * math.cos(yaw), math.cos(pitch) * math.sin(yaw),
        math.sin(pitch)])


def _slide(eye, target, amount: float):
    """Move eye and target sideways together, so the subject sits left of a panel."""
    forward = (target - eye) / np.linalg.norm(target - eye)
    right = np.cross(forward, np.array([0.0, 0.0, 1.0]))
    shift = right / np.linalg.norm(right) * amount
    return eye + shift, target + shift


def _log_centre(explode: float) -> np.ndarray:
    x_start, axis = vf.log_layout()
    length = vf.PLAN.sections * vf.PLAN.section_length_ft
    spread = (vf.PLAN.sections - 1) * vf._d("gap_ft") * explode
    radius = vf.trunk_radius_ft(vf._d("stump_ft") + length * 0.5)
    lift = explode * vf._d("push") * radius * 1.1
    return _world((x_start + (length + spread) * 0.5, 0.0, axis + lift))


def _first_section(explode: float) -> np.ndarray:
    x_start, axis = vf.log_layout()
    radius = vf.trunk_radius_ft(vf._d("stump_ft") + vf.PLAN.section_length_ft * 0.5)
    lift = explode * vf._d("push") * radius * 1.1
    return _world((x_start + vf.PLAN.section_length_ft * 0.5, 0.0, axis + lift))


def harvest_camera(app, chapter, progress: float, width: int, height: int):
    """(eye, target, field of view) for every chapter of the harvest."""
    p = clamp(progress)
    slug = chapter.slug
    if chapter.stage == "hv_dome":
        # A slow walk round the finished dome, sitting low in the frame so the upper
        # left stays free for a callout. The worksheet covers the right 42% of the
        # frame and a tally about a quarter, so the dome slides left by what each
        # leaves: at 4.4 radii and this lens, 1.27 radii puts it in the middle of the
        # space a worksheet leaves, 0.72 radii in the middle of what a tally leaves.
        radius = _dome_radius()
        target = DOME_ORIGIN + np.array([0.0, 0.0, radius * 0.75])
        eye = _orbit(target, -62.0 + 48.0 * ease_in_out(p), 20.0, radius * 4.4)
        amount = radius * (1.27 if chapter.overlay == "math" else 0.72)
        eye, target = _slide(eye, target, amount)
        return eye, target, 42.0
    if slug == "tree":
        # The whole pine, crown and all, from a little below its middle.
        target = _world((0.0, 0.0, 36.0))
        return _orbit(target, -96.0 + 10.0 * p, 5.0 + 4.0 * p, 34.0 - 3.0 * p), \
            target, 44.0
    if slug == "fell":
        fell = _knobs(slug, p)["fell"]
        stump = vf._d("stump_ft")
        pivot = np.array([vf.hinge_x_ft(fell), 0.0, stump])
        centre = vf._rotated_point(np.array([0.0, 0.0, 26.0]), pivot,
                                   vf.fall_angle_deg(fell), vf._drop(fell))
        follow = _world(centre)
        # Wide enough to hold the standing crown and the landing spot at once.
        wide = _world((30.0, 0.0, 24.0))
        target = wide * 0.6 + follow * 0.4
        return _orbit(target, -90.0 + 6.0 * (p - 0.5), 7.0, 31.0), target, 50.0
    if slug == "explode":
        explode = _knobs(slug, p)["explode"]
        target = _log_centre(explode)
        yaw = -118.0 + 58.0 * ease_in_out(p)
        eye = _orbit(target, yaw, 20.0 + 6.0 * p, 19.0 - 1.5 * p)
        # The tally stands on the right of the frame; slide the whole view right
        # so the log sits in the space the column leaves. Fitted by projecting
        # every section's corners: all eight clear the column's left edge.
        eye, target = _slide(eye, target, 5.2)
        return eye, target, 46.0
    if slug == "why":
        target = _first_section(1.0)
        yaw = -168.0 + 22.0 * ease_in_out(p)
        return _orbit(target, yaw, 12.0, 3.4 + 0.4 * p), target, 42.0
    if slug in ("assume", "sources"):
        centre = _log_centre(1.0)
        eye = _orbit(centre, -72.0, 26.0, 15.0)
        # The worksheet covers the right of the frame, so aim right of the log and
        # let the picture sit in the space the panel leaves.
        forward = centre - eye
        right = np.cross(forward / np.linalg.norm(forward), np.array([0.0, 0.0, 1.0]))
        right = right / np.linalg.norm(right)
        return eye, centre + right * 4.2, 46.0
    target = _log_centre(1.0) * 0.8 + _world((0.0, 0.0, 2.0)) * 0.2
    return _orbit(target, -70.0 - 40.0 * ease_in_out(p), 34.0, 19.0), target, 46.0


# ----------------------------------------------------------------------
# What was measured, for the screen that says so before any fuel is spent
# ----------------------------------------------------------------------

def assumption_lines() -> tuple[str, ...]:
    """The table the fuel and day figures rest on, computed, last line the verdict."""
    from .book_math import FORTNIGHT_PLAN, HARVEST_PHASES, fortnight, ripping_fuel

    fuel = ripping_fuel()
    work = fortnight()
    days = {name: (first, last) for name, first, last, _ in FORTNIGHT_PLAN}
    plan = ", ".join(f"{name} days {days[name][0]}-{days[name][1]}"
                     for name in HARVEST_PHASES)
    return (
        f"MEASURED   fuel while ripping: {fuel.tanks_per_hour:.0f} tanks an hour, "
        "one timed sitting",
        f"MEASURED   cutting rate: {work.struts_per_afternoon:.0f} struts in a "
        f"{work.hours_per_afternoon:.0f}-hour afternoon",
        f"DERIVED    ripping time: {work.struts_needed} struts at "
        f"{work.struts_per_hour:.1f} an hour = {work.ripping_hours:.0f} hours",
        f"DECIDED    the plan: {plan}",
        f"ESTIMATED  the saw's tank: {fuel.tank_l:.2f} to {fuel.tank_high_l:.2f} L; "
        "the listings disagree",
        "NOT METERED  fuel for felling and bucking: left out, not guessed",
        "So the fuel is a range, and it is the ripping only",
    )


# ----------------------------------------------------------------------
# The chapters
# ----------------------------------------------------------------------

def _c(slug: str, title: str, promise: str, narration: str, duration: float,
       stage: str = "hv_harvest", overlay: str | None = None,
       equations: tuple[str, ...] = (), callouts: tuple = ()) -> Chapter:
    spoken = _t(narration)
    # The floor covers the voice at the narrator's measured pace, so a silent
    # preview or a still lands callouts inside their chapter; an export still
    # stretches each chapter to the speech it actually measures.
    from .audio import SPEECH_DELAY, TAIL_PADDING
    from .callouts import characters_per_second
    estimated = SPEECH_DELAY + len(spoken) / characters_per_second() + TAIL_PADDING
    return Chapter(slug, "00", title, _t(promise), (spoken,), equations,
                   max(duration, round(estimated, 1)), (0.0, 20.0, 20.0), stage,
                   overlay, callouts)


_AUTHORED: tuple[Chapter, ...] = (
    _c("tree", "Two trees",
       "The whole woodpile is standing up.",
       "It will take me {{method_a.whole_trees}} whole pine trees to harvest all "
       "of the wood a {{method_a.floor_sqft}} square foot house needs. No lumber "
       "yard and no delivery truck, just the trees already standing on the "
       "property, and one small chainsaw.",
       12.0,
       callouts=(
           Callout("{{method_a.whole_trees}}", unit="trees", icon="pine",
                   cue="{{method_a.whole_trees}} whole pine trees", slot="left",
                   hold=3.6),
           Callout("{{method_a.floor_sqft}}", unit="sq ft",
                   note="the house those trees frame", icon="house",
                   cue="{{method_a.floor_sqft}} square foot", slot="right",
                   hold=4.0),
       )),
    _c("fell", "The fell line",
       "The hinge steers the tree. The saw only sets it free.",
       "It starts with a notch, cut into the side I want it to fall toward, and "
       "then a back cut from the other side, a little higher. The strip of wood "
       "left between the two is the hinge. It steers the tree all the way over, "
       "and it is why felling gets a chapter of its own before any of this is "
       "safe to try. The saw is a {{saw.displacement_cc}} cc hardware-store model "
       "with a {{saw.bar_in}} inch bar.",
       26.0,
       callouts=(
           Callout("{{saw.displacement_cc}}", unit="cc saw",
                   note="{{saw.bar_in}}-inch bar, off the shelf", icon="chainsaw",
                   cue="{{saw.displacement_cc}} cc", slot="right", hold=4.5),
       )),
    _c("explode", "All at once",
       "Every section splits at the same time.",
       "Then everything happens at once. The crown comes off, the trunk is cut "
       "into {{tree.sections}} sections, {{tree.section_length_ft}} feet each, "
       "and every section splits into {{tree.sectors}} wedges. That is "
       "{{tree.struts_per_tree}} struts from one tree. With {{dome.trees}} trees "
       "it is {{dome.struts_available}}, for a frame that needs "
       "{{frame.members}}.",
       26.0,
       callouts=(
           Tally((
               Callout("{{tree.sections}}", unit="sections",
                       cue="cut into {{tree.sections}} sections"),
               Callout("{{tree.section_length_ft}} ft", unit="each", op="·",
                       tone="note", cue="{{tree.section_length_ft}} feet each"),
               Callout("{{tree.sectors}}", unit="wedges a section", op="×",
                       cue="splits into {{tree.sectors}} wedges"),
               Callout("{{tree.struts_per_tree}}", unit="struts a tree", op="=",
                       cue="{{tree.struts_per_tree}} struts from one tree"),
               Callout("{{dome.trees}}", unit="trees", op="×",
                       cue="with {{dome.trees}} trees"),
               Callout("{{dome.struts_available}}", unit="struts", op="=",
                       cue="it is {{dome.struts_available}}"),
               Callout("{{frame.members}}", unit="the frame needs", op="·",
                       tone="note", cue="needs {{frame.members}}"),
           ), title="one tree, then two", slot="right", icon="split"),
       )),
    _c("why", "Why split it",
       "Split, the log keeps most of itself.",
       "Why split it instead of milling it square? Because the only wood a split "
       "loses is the width of the cut. Of the {{tree.solid_bf}} board feet in "
       "this trunk, the saw takes {{tree.kerf_bf}} and the wedges keep "
       "{{tree.wedge_bf}}, which is {{tree.recovery_pct}} percent of the tree "
       "standing in the frame. The honest cost is the stick itself. From a small "
       "log, a single wedge is the weaker stick in bending, and it is the "
       "triangulated shell, not the wedge, that makes it enough.",
       30.0,
       callouts=(
           Tally((
               Callout("{{tree.solid_bf}}", unit="board feet solid",
                       cue="{{tree.solid_bf}} board feet"),
               Callout("{{tree.kerf_bf}}", unit="to the kerf", op="−",
                       cue="the saw takes {{tree.kerf_bf}}"),
               Callout("{{tree.wedge_bf}}", unit="in the wedges", op="=",
                       cue="the wedges keep {{tree.wedge_bf}}"),
               Callout("{{tree.recovery_pct}}%", unit="of the tree", op="·",
                       tone="total", cue="{{tree.recovery_pct}} percent"),
           ), title="one trunk", slot="right", icon="log"),
           Callout("{{versus.strength_pct}}%", unit="bending strength",
                   note="{{versus.diameter_in}}-inch log: one wedge against a "
                        "dressed two-by-four",
                   tone="warn", cue="the weaker stick in bending", slot="left",
                   hold=None),
       )),
    _c("assume", "Measured, and guessed",
       "What the next figures rest on.",
       "Before the days and the fuel, here is what those figures rest on. The fuel "
       "rate was measured, in one timed sitting with the tanks counted. The "
       "ripping hours come from the cutting rate, which was also measured. The "
       "day plan is a decision, not a result. And the size of the saw's tank is an "
       "estimate, because the listings disagree and nobody has checked this saw, "
       "so the fuel comes out as a range.",
       24.0, overlay="math", equations=assumption_lines()),
    _c("cost", "What it took",
       "{{work.harvest_days}} days of saw work, and a few gallons.",
       "The whole harvest takes {{work.harvest_days}} days: "
       "{{work.felling_days}} of felling, {{work.bucking_days}} of bucking, and "
       "{{work.ripping_days}} of ripping. Ripping is the part that was timed with "
       "the fuel written down: {{fuel.tanks_per_hour}} tanks an hour, for "
       "{{fuel.rip_hours}} hours. That is {{fuel.rip_tanks}} tanks, and at "
       "{{fuel.tank_l}} to {{fuel.tank_high_l}} litres a tank, somewhere between "
       "{{fuel.rip_gallons}} and {{fuel.rip_gallons_high}} US gallons. Felling "
       "and bucking were never metered, so they are not in that number.",
       32.0,
       callouts=(
           Callout("{{work.harvest_days}}", unit="days",
                   note="{{work.felling_days}} felling · "
                        "{{work.bucking_days}} bucking · "
                        "{{work.ripping_days}} ripping",
                   icon="calendar", cue="takes {{work.harvest_days}} days",
                   slot="left", hold=None),
           Tally((
               Callout("{{fuel.tanks_per_hour}}", unit="tanks an hour",
                       cue="{{fuel.tanks_per_hour}} tanks an hour"),
               Callout("{{fuel.rip_hours}}", unit="hours", op="×",
                       cue="for {{fuel.rip_hours}} hours"),
               Callout("{{fuel.rip_tanks}}", unit="tanks", op="=",
                       cue="that is {{fuel.rip_tanks}} tanks"),
               Callout("{{fuel.tank_l}}–{{fuel.tank_high_l}}",
                       unit="litres a tank", op="×",
                       cue="at {{fuel.tank_l}} to"),
               Callout("{{fuel.rip_litres}}–{{fuel.rip_litres_high}}",
                       unit="litres", op="=", cue="somewhere between"),
               Callout("{{fuel.rip_gallons}}–{{fuel.rip_gallons_high}}",
                       unit="US gallons", op="≈", tone="total",
                       cue="somewhere between"),
           ), title="ripping fuel", slot="right", icon="fuel"),
       )),

    # -- what the fortnight is worth ------------------------------------------
    _c("sources", "What the house numbers rest on",
       "Published, the author's, decided, estimated.",
       "Now the question every build gets asked: what is it worth? Before a single "
       "house figure, here is what they rest on. The published ones come from the "
       "home builders' association's cost survey, the Census Bureau and the Bureau "
       "of Labor Statistics, and the builders' survey is a small one, which its "
       "own authors say. The {{house.price}} dollar house, the {{trailer.price}} "
       "dollar trailer, the {{house.labor_share_pct}} percent labor share and the "
       "{{value.hours}} hours of shell work are my own round figures. The tax "
       "bracket is a decision. Everything else is an estimate, and it is labelled "
       "as one.",
       26.0, overlay="math", equations=he.source_lines()),
    _c("house_time", "Where a house's time goes",
       "{{time.months}} months, most of it inside.",
       "A new house takes {{time.months}} months on average, from the first "
       "shovel to finished, by the Census Bureau's count, and "
       "{{time.owner_months}} months when its owner builds it. One builder's week "
       "by week schedule shows where that time goes. {{time.pct_foundations}} "
       "percent is the ground and the foundation. {{time.pct_framing}} percent is "
       "framing. {{time.pct_rough_ins}} percent is pipes, wires and ducts. "
       "{{time.pct_interior}} percent is the inside: insulation, drywall, floors, "
       "trim, paint and fixtures. {{time.pct_exterior}} percent is the outside, "
       "{{time.pct_final}} percent the driveway, yard and clean up, and the last "
       "{{time.pct_closing}} percent is inspection and closing.",
       30.0,
       callouts=(
           Callout("{{time.months}}", unit="months",
                   note="average, start to finish, Census", icon="calendar",
                   cue="{{time.months}} months on average", slot="left", hold=None),
           Tally((
               Callout("{{time.pct_foundations}}%", unit="ground, foundation",
                       cue="{{time.pct_foundations}} percent is the ground"),
               Callout("{{time.pct_framing}}%", unit="framing", op="+",
                       cue="{{time.pct_framing}} percent is framing"),
               Callout("{{time.pct_rough_ins}}%", unit="pipes, wires, ducts",
                       op="+", cue="{{time.pct_rough_ins}} percent is pipes"),
               Callout("{{time.pct_interior}}%", unit="inside finishes", op="+",
                       cue="{{time.pct_interior}} percent is the inside"),
               Callout("{{time.pct_exterior}}%", unit="outside", op="+",
                       cue="{{time.pct_exterior}} percent is the outside"),
               Callout("{{time.pct_final}}%", unit="yard, driveway, clean-up",
                       op="+", cue="{{time.pct_final}} percent the driveway"),
               Callout("{{time.pct_closing}}%", unit="inspection, closing", op="+",
                       cue="last {{time.pct_closing}} percent"),
               Callout("{{time.total_pct}}%", unit="of the build", op="=",
                       tone="total", cue="inspection and closing"),
           ), title="where the weeks go", slot="right", icon="clock"),
       )),
    _c("house_money", "Where a house's money goes",
       "The land, the building, and the people who sell it.",
       "Now the money, in the shares the builders' survey found. Of a "
       "{{house.price}} dollar new house, {{house.lot}} dollars is the land. "
       "{{house.construction}} is the building itself. {{house.builder}} is the "
       "builder's overhead and profit, and {{house.selling}} is the commission, "
       "marketing and financing it takes to sell it. At the survey's national "
       "average, that much new house is only about {{house.sqft}} square feet.",
       26.0,
       callouts=(
           Tally((
               Callout("${{house.lot}}", unit="land",
                       cue="{{house.lot}} dollars is the land"),
               Callout("${{house.construction}}", unit="the building", op="+",
                       cue="{{house.construction}} is the building"),
               Callout("${{house.builder}}", unit="builder's overhead, profit",
                       op="+", cue="{{house.builder}} is the builder"),
               Callout("${{house.selling}}", unit="selling, financing", op="+",
                       cue="{{house.selling}} is the commission"),
               Callout("${{house.price}}", unit="a new house", op="=",
                       tone="total", cue="it takes to sell it"),
               Callout("{{house.sqft}} sq ft", unit="at the national average",
                       op="·", tone="note", cue="about {{house.sqft}} square feet"),
           ), title="a new house", slot="right", icon="house"),
       )),
    _c("labor_share", "Labor is not most of it",
       "Even at the record lumber price, labor is about a quarter.",
       "So is labor most of what you pay for? Not in a new house. Take my "
       "{{house.labor_share_pct}} percent of the building as labor, and it is "
       "{{house.labor_pct}} percent of the price. Then put the lumber at its "
       "record. In the spring of twenty twenty one, framing lumber topped "
       "{{lumber.peak}} dollars a thousand board feet, and the builders worked out "
       "it added {{lumber.added}} dollars to an average new home. Price this house "
       "that way and it comes to {{house.peak_price}}: {{house.peak_materials}} in "
       "materials, {{house.peak_labor}} in labor, {{house.peak_fees}} in permits, "
       "fees and design, {{house.peak_land}} for the land, {{house.peak_builder}} "
       "to the builder and {{house.peak_selling}} to sell it. Labor is "
       "{{house.peak_labor_pct}} percent. About a quarter.",
       34.0,
       callouts=(
           Callout("{{house.labor_pct}}%", unit="of the price is labor",
                   note="{{house.labor_share_pct}}% of the building, before the "
                        "lumber peak",
                   tone="warn", cue="it is {{house.labor_pct}} percent of the price",
                   slot="left", hold=5.0),
           Callout("${{lumber.peak}}", unit="per thousand board feet",
                   note="framing lumber, the record", icon="board",
                   cue="topped {{lumber.peak}}", slot="left", hold=5.0),
           Tally((
               Callout("${{house.peak_materials}}", unit="materials",
                       cue="{{house.peak_materials}} in materials"),
               Callout("${{house.peak_labor}}", unit="labor", op="+",
                       cue="{{house.peak_labor}} in labor"),
               Callout("${{house.peak_fees}}", unit="permits, fees, design",
                       op="+", cue="{{house.peak_fees}} in permits"),
               Callout("${{house.peak_land}}", unit="land", op="+",
                       cue="{{house.peak_land}} for the land"),
               Callout("${{house.peak_builder}}", unit="builder", op="+",
                       cue="{{house.peak_builder}} to the builder"),
               Callout("${{house.peak_selling}}", unit="selling it", op="+",
                       cue="{{house.peak_selling}} to sell it"),
               Callout("${{house.peak_price}}", unit="at the lumber peak",
                       op="=", tone="total",
                       cue="Labor is {{house.peak_labor_pct}} percent"),
           ), title="the same house, peak lumber", slot="right", icon="board"),
       )),
    _c("trailer", "The trailer is built the other way",
       "A factory's labor is a smaller share still.",
       "A new manufactured home splits another way. Of a {{trailer.price}} dollar "
       "home, about {{trailer.dealer}} is the dealer's share. {{trailer.materials}} "
       "is what the factory spends on materials, {{trailer.payroll}} is its "
       "payroll, and {{trailer.other}} is its overhead and profit. Factory labor "
       "is only {{trailer.labor_pct}} percent of the price. At the Census average "
       "of {{trailer.per_sqft}} dollars a square foot, that buys about "
       "{{trailer.sqft}} square feet, set up, without the land. The factory split "
       "is from the two thousand two Economic Census, the newest published in that "
       "detail, so read it as a shape more than a figure.",
       30.0,
       callouts=(
           Tally((
               Callout("${{trailer.dealer}}", unit="the dealer",
                       cue="{{trailer.dealer}} is the dealer"),
               Callout("${{trailer.materials}}", unit="factory materials", op="+",
                       cue="{{trailer.materials}} is what the factory"),
               Callout("${{trailer.payroll}}", unit="factory payroll", op="+",
                       cue="{{trailer.payroll}} is its payroll"),
               Callout("${{trailer.other}}", unit="factory overhead, profit",
                       op="+", cue="{{trailer.other}} is its overhead"),
               Callout("${{trailer.price}}", unit="a new manufactured home",
                       op="=", tone="total", cue="Factory labor is only"),
               Callout("{{trailer.sqft}} sq ft", unit="at the Census average",
                       op="·", tone="note",
                       cue="about {{trailer.sqft}} square feet"),
           ), title="a manufactured home", slot="right", icon="truck"),
           Callout("{{trailer.labor_pct}}%", unit="of the price is factory labor",
                   tone="warn", cue="Factory labor is only {{trailer.labor_pct}}",
                   slot="left", hold=6.0),
       )),
    _c("worth", "What the fortnight is worth",
       "Two weeks of one person, against buying the frame.",
       "Now the frame this film has been building. Framing is "
       "{{house.framing_pct}} percent of what it costs to build a new house, which "
       "is {{house.framing_price_pct}} percent of its price. For {{value.sqft}} "
       "square feet, bought at the national rate with the builder's share, the "
       "frame costs {{value.frame_buy}} dollars. The fortnight spends "
       "{{value.frame_cash}} dollars: the saw, the fuel, the hardware, and the two "
       "trees at what a timber buyer would pay for them standing. That keeps "
       "{{value.frame_saved}} dollars, for {{value.hours}} hours of hands-on work. "
       "{{value.rate}} dollars an hour. Against a manufactured home's cheaper rate "
       "it is {{value.rate_trailer}}. A carpenter's median wage is "
       "{{wage.carpenter}} an hour, and a typical worker takes home "
       "{{wage.take_home}}, so buying that frame would cost {{value.buy_hours}} "
       "hours of ordinary pay.",
       38.0, stage="hv_dome",
       callouts=(
           Tally((
               Callout("${{value.frame_buy}}", unit="the frame, bought",
                       cue="frame costs {{value.frame_buy}}"),
               Callout("${{value.frame_cash}}", unit="the fortnight's cash",
                       op="−", cue="spends {{value.frame_cash}}"),
               Callout("${{value.frame_saved}}", unit="kept", op="=",
                       cue="keeps {{value.frame_saved}}"),
               Callout("{{value.hours}}", unit="hours", op="÷",
                       cue="for {{value.hours}} hours"),
               Callout("${{value.rate}}", unit="an hour", op="=", tone="total",
                       cue="{{value.rate}} dollars an hour"),
               Callout("${{value.rate_trailer}}", unit="against a trailer",
                       op="·", tone="note", cue="it is {{value.rate_trailer}}"),
               Callout("${{wage.carpenter}}", unit="a carpenter's median",
                       op="·", tone="note",
                       cue="median wage is {{wage.carpenter}}"),
           ), title="the frame, bought or built", slot="right", icon="dollar"),
           Callout("{{value.buy_hours}}", unit="hours of ordinary pay",
                   note="to buy the frame instead", icon="clock", tone="note",
                   cue="cost {{value.buy_hours}} hours", slot="left", hold=None),
       )),
    _c("categories", "Every part of the house",
       "The same sum, stage by stage.",
       "Here is every part of the house, done the same way for {{value.sqft}} "
       "square feet: what it costs to buy, what the dome way still pays in money, "
       "and how many hours of a typical worker's take-home pay the difference is "
       "worth. Fees stay fees. The foundation is shorter, because a circle has the "
       "least edge for its floor. The skin is smaller but harder to finish, and "
       "the pipes and wires run from a central column instead of around the "
       "walls. The last line is the whole floor, if every hour of the work is "
       "yours.",
       28.0, stage="hv_dome", overlay="math", equations=he.category_lines()),
    _c("stacking", "Where the saving comes from",
       "Most of it is building your own, not the shape.",
       "Stack it all up and the saving has four sources. Bought whole, the floor "
       "costs {{stack.buy}} dollars. {{stack.margin}} of that is the builder's and "
       "the seller's share, which anyone who builds their own house keeps, "
       "whatever its shape. {{stack.labor}} is labor you do yourself, paid in "
       "hours instead of money. {{stack.trees}} is lumber from your own trees "
       "instead of a yard. And {{stack.shape}} is the shape itself: "
       "{{shape.framing_less}} percent less framing, {{shape.skin_less}} percent "
       "less skin, a {{shape.perimeter_less}} percent shorter foundation, and runs "
       "{{shape.runs_less}} percent shorter from the central column. That leaves "
       "{{stack.cash}} dollars to pay.",
       34.0, stage="hv_dome",
       callouts=(
           Tally((
               Callout("${{stack.buy}}", unit="to buy the floor",
                       cue="the floor costs {{stack.buy}}"),
               Callout("${{stack.margin}}", unit="builder's share", op="−",
                       cue="{{stack.margin}} of that"),
               Callout("${{stack.labor}}", unit="your labor", op="−",
                       cue="{{stack.labor}} is labor"),
               Callout("${{stack.trees}}", unit="your trees", op="−",
                       cue="{{stack.trees}} is lumber"),
               Callout("${{stack.shape}}", unit="the shape", op="−",
                       cue="{{stack.shape}} is the shape"),
               Callout("${{stack.cash}}", unit="left to pay", op="=",
                       tone="total", cue="leaves {{stack.cash}}"),
           ), title="where the saving comes from", slot="right", icon="dome"),
       )),
    _c("limits", "What this does not show",
       "The half of the sum that does not flatter the dome.",
       "And what it does not show. {{stack.unchanged_pct}} percent of what a house "
       "costs to build does not care about its shape: fees, windows, cabinets, "
       "appliances, floors, the driveway. Only the frame's hours were measured; "
       "the rest of that labor is weeks more of somebody's time, and wiring, "
       "plumbing and gas usually need a licensed trade and an inspection. A "
       "triangle is harder to finish than a flat wall, and the dome's laminate "
       "skin is its most expensive material. Against a manufactured home the gap "
       "is small: {{value.sqft}} square feet at a trailer's average price is "
       "{{stack.trailer_floor}} dollars, and the dome way pays "
       "{{stack.cash_factory}} for the same parts, before your hours. And the "
       "biggest saving here, the builder's share and the labor, belongs to anyone "
       "who builds their own house, whatever its shape.",
       38.0, stage="hv_dome",
       callouts=(
           Callout("{{stack.unchanged_pct}}%",
                   unit="of the building cost the shape can't touch", tone="warn",
                   cue="{{stack.unchanged_pct}} percent of what a house",
                   slot="left", hold=7.0),
           Callout("${{stack.trailer_floor}}", unit="as a trailer",
                   note="dome way ${{stack.cash_factory}}, before your hours",
                   tone="warn", icon="truck",
                   cue="is {{stack.trailer_floor}} dollars", slot="right",
                   hold=None),
       )),
)

CHAPTERS: tuple[Chapter, ...] = tuple(
    Chapter(c.slug, f"{index + 1:02d}", c.title, c.promise, c.narration,
            c.equations, c.duration, c.camera, c.stage, c.overlay, c.callouts)
    for index, c in enumerate(_AUTHORED))

SCENES = {"hv_harvest": scene_hv_harvest, "hv_dome": scene_hv_dome}

VALUE_CHAPTERS = ("house_time", "house_money", "labor_share", "trailer", "worth",
                  "categories", "stacking", "limits")
"""Every chapter that quotes a house, trailer or wage figure. All of them come after
the screen that says what those figures rest on."""


def validate_harvest_lesson() -> None:
    """Prove the film before a frame of it renders."""
    import re

    from .book_math import validate_fortnight_plan
    from .callouts import check_tally, validate_callouts
    from .icons import validate_icons
    from .render_kit import TriangleBatch
    from .visual_objects import validate_visual_objects
    from .visuals_forest import validate_forest

    validate_icons()
    validate_visual_objects()
    validate_forest()
    validate_callouts()
    validate_fortnight_plan()
    he.validate_house_economics()
    HARVEST_LESSON.validate()          # includes every chapter's callouts

    # Words and headlines were resolved from tokens; none may still hold one.
    for chapter in HARVEST_LESSON.chapters:
        for text in (chapter.promise, *chapter.narration):
            assert "{{" not in text, (chapter.slug, text)
    # Every estimated figure arrives after the screen that declares it.
    order = [chapter.slug for chapter in HARVEST_LESSON.chapters]
    assert order.index("assume") < order.index("cost")
    for slug in VALUE_CHAPTERS:
        assert order.index("sources") < order.index(slug), slug
    # The unflattering half closes the argument; it is not buried in the middle.
    assert order[-1] == "limits", order[-1]
    # Every tally in the film adds up.
    for chapter in HARVEST_LESSON.chapters:
        for entry in chapter.callouts:
            if isinstance(entry, Tally):
                assert not check_tally(entry), (chapter.slug, check_tally(entry))

    class _Probe:
        def __init__(self, index):
            self.world_labels, self.world_icons = [], []
            self.chapters, self.chapter_index = HARVEST_LESSON.chapters, index

    for index, chapter in enumerate(HARVEST_LESSON.chapters):
        painter = SCENES[chapter.stage]
        for p in (0.0, 0.3, 0.6, 1.0):
            probe = _Probe(index)
            opaque, transparent = TriangleBatch(), TriangleBatch()
            painter(probe, opaque, transparent, p)
            assert opaque.vertices or transparent.vertices, (chapter.slug, p)
            eye, target, fov = harvest_camera(probe, chapter, p, 1920, 1080)
            assert np.all(np.isfinite(eye)) and np.all(np.isfinite(target))
            assert float(np.linalg.norm(eye - target)) > 1.0, (chapter.slug, p)
            assert 20.0 < fov < 80.0
    # The saw appears while the tree is being cut, and the fall ends lying down.
    probe = _Probe(order.index("fell"))
    scene_hv_harvest(probe, TriangleBatch(), TriangleBatch(), 0.2)
    assert probe.world_icons, "no chainsaw at the fell line during the notch"
    # No figure is typed in the words of the montage-style headline either.
    for chapter in _AUTHORED:
        assert not re.search(r"\d", chapter.title), chapter.title


def harvest_report() -> str:
    """Every figure the film shows or says, with its estimated arrival time."""
    from .callouts import schedule

    lines = ["TWO TREES, ALL AT ONCE -- what the film says and shows", ""]
    for chapter in HARVEST_LESSON.chapters:
        lines.append(f"{chapter.number}  {chapter.title}")
        lines.append(f"    headline: {chapter.promise}")
        for placed in schedule(chapter, chapter.duration * 1.6,
                               speak_promise=HARVEST_LESSON.style != "hype"):
            prefix = placed.item.op or " "
            lines.append(f"    {placed.start:5.1f}s  {prefix} {placed.text} "
                         f"{placed.unit}  {placed.note}".rstrip())
        for equation in chapter.equations:
            lines.append(f"    | {equation}")
        lines.append("")
    # A Windows console in its default code page has no minus sign, approximately-
    # equals or middle dot; the report is for reading, so it says them in ASCII.
    return "\n".join(lines).translate({0x2212: "-", 0x2248: "~", 0x00b7: "."})


HARVEST_LESSON = Lesson(
    key="harvest",
    brand="TWO TREES",
    title="Two Trees, All at Once",
    chapters=CHAPTERS,
    scenes=SCENES,
    selftest=validate_harvest_lesson,
    report=harvest_report,
    snapshot_prefix="harvest",
    style="hype",
    camera_fn=harvest_camera,
    label_layout="declutter",
)
