"""The seam, fitted out: gutter, vent, desiccant, condenser and air barrier.

A short film about one void. Every seam in a wedge dome carries a channel
that is there whether or not anybody uses it -- the space two sawn faces
leave when they meet at a dihedral angle -- and this is what happens when
you decide to use it for four things at once.

The film exists because the argument is hard to believe on a page and
obvious the moment you can see into a seam. It is also the film that has to
carry the number that does not flatter the idea: thermoelectric condensing
makes less water in a year than half an inch of rain, and the chapter that
says so is in the cut rather than in a footnote.

Everything on screen comes out of :mod:`wedge_book.systems` and the solved
dome in :mod:`raw_wedge_bridge`. No figure here is typed.
"""

from __future__ import annotations

import numpy as np

from wedge_book import systems

from . import raw_wedge_bridge as bridge
from .lessons import Chapter, Lesson
from .render_kit import WorldLabel

WATER = (0.42, 0.75, 1.00)
AIR = (0.45, 0.92, 0.62)
DRY = (1.00, 0.76, 0.32)
MUTED = (0.74, 0.78, 0.84)
WARN = (1.00, 0.55, 0.45)

SCENE_RADIUS = 5.0


def _label(app, point, text, colour) -> None:
    app.world_labels.append(
        WorldLabel(np.asarray(point, dtype=np.float32), text, colour))


def _dome(app, opaque, transparent, *, parts=("wood",), alpha=None) -> int:
    """Solid geometry into the opaque batch, anything see-through into the
    transparent one -- which is the renderer's contract and the reason a
    faded frame does not black out what is behind it."""
    batch = opaque if alpha is None else transparent
    return bridge.world_batches(batch, "point_dome_in",
                                scene_radius=SCENE_RADIUS, parts=parts,
                                alpha=alpha)


# ----------------------------------------------------------------------
# Scenes
# ----------------------------------------------------------------------

def scene_channel(app, opaque, transparent, progress: float) -> None:
    """The dome, and the fact that every seam has a void in it."""
    _dome(app, opaque, transparent, parts=("wood", "rigid"))
    geometry = systems._geometry()
    _label(app, (0.0, 0.0, SCENE_RADIUS * 0.62),
           f"{geometry.seam_count} seams", MUTED)
    _label(app, (0.0, 0.0, SCENE_RADIUS * 0.40),
           f"{geometry.seam_length_in / 12.0:,.0f} ft of channel", WATER)


def scene_open(app, opaque, transparent, progress: float) -> None:
    """The same dome opened, so the channel is visible."""
    _dome(app, opaque, transparent, parts=("wood",), alpha=0.55)
    _dome(app, opaque, transparent, parts=("rigid",))
    _label(app, (0.0, 0.0, SCENE_RADIUS * 0.72),
           "the key is in every one", DRY)


def scene_water(app, opaque, transparent, progress: float) -> None:
    """Rain in at the ridge, water out at the bottom."""
    _dome(app, opaque, transparent, parts=("wood",), alpha=0.42)
    _dome(app, opaque, transparent, parts=("rigid",))
    water = systems.water_comparison()
    _label(app, (0.0, 0.0, SCENE_RADIUS * 0.86),
           "rain in at the ridge", WATER)
    _label(app, (0.0, 0.0, SCENE_RADIUS * 0.30),
           f"{water['gallons_per_inch']:,.0f} gal an inch", WATER)


def scene_air(app, opaque, transparent, progress: float) -> None:
    """Positive pressure, so every seam blows outward."""
    _dome(app, opaque, transparent, parts=("wood",), alpha=0.50)
    air = systems.air_barrier()
    _label(app, (0.0, 0.0, SCENE_RADIUS * 0.80),
           f"+{air['pressure_pa']:.0f} Pa inside", AIR)
    _label(app, (0.0, 0.0, SCENE_RADIUS * 0.52),
           f"{air['cfm']:,.0f} cu ft a minute", AIR)
    _label(app, (0.0, 0.0, SCENE_RADIUS * 0.24),
           "every seam flows out", AIR)


def scene_dry(app, opaque, transparent, progress: float) -> None:
    """The desiccant leg."""
    _dome(app, opaque, transparent, parts=("wood", "rigid"), alpha=0.72)
    _label(app, (0.0, 0.0, SCENE_RADIUS * 0.70),
           "air along the wood faces", AIR)
    _label(app, (0.0, 0.0, SCENE_RADIUS * 0.42),
           "or through the silica", DRY)


def scene_condense(app, opaque, transparent, progress: float) -> None:
    """The thermoelectric plates, and the number that judges them."""
    _dome(app, opaque, transparent, parts=("wood",), alpha=0.45)
    water = systems.water_comparison()
    _label(app, (0.0, 0.0, SCENE_RADIUS * 0.88),
           f"{water['peltier_watts']:,.0f} W of plates", WARN)
    _label(app, (0.0, 0.0, SCENE_RADIUS * 0.58),
           f"{water['peltier_gallons_per_year']:,.0f} gal a year", WARN)
    _label(app, (0.0, 0.0, SCENE_RADIUS * 0.28),
           f"= {water['rain_inches_equal_to_a_year']:.1f} in of rain", WATER)


def scene_bill(app, opaque, transparent, progress: float) -> None:
    """What the module costs, against the dome."""
    _dome(app, opaque, transparent, parts=("wood", "rigid"))
    bill = {b.key: b for b in systems.bills()}
    _label(app, (0.0, 0.0, SCENE_RADIUS * 0.74),
           f"${bill['seam'].cost:,.0f} the module", DRY)


SCENES = {
    "sm_channel": scene_channel,
    "sm_open": scene_open,
    "sm_water": scene_water,
    "sm_air": scene_air,
    "sm_dry": scene_dry,
    "sm_condense": scene_condense,
    "sm_bill": scene_bill,
}


# ----------------------------------------------------------------------
# The film
# ----------------------------------------------------------------------

def _chapters() -> tuple[Chapter, ...]:
    geometry = systems._geometry()
    air = systems.air_barrier()
    water = systems.water_comparison()
    bill = {b.key: b for b in systems.bills()}
    feet = geometry.seam_length_in / 12.0

    return (
        Chapter(
            "channel", "01", "The channel is already there",
            f"{geometry.seam_count} seams, {feet:,.0f} feet of void.",
            ("Two sawn faces meeting at an angle cannot close flush.",
             f"So every one of this dome's {geometry.seam_count} seams "
             f"carries a void running its whole length. {feet:,.0f} feet of "
             "it, threaded through the structure, touching every panel, "
             "arriving at the apex and at the base ring.",
             "You are going to fill it with something. This film is about "
             "what."),
            (), 26.0, (48.0, 14.0, 13.0), "sm_channel"),
        Chapter(
            "open", "02", "What is actually in there",
            "A key, and room around it.",
            ("Open the frame and you can see the shape of the problem.",
             "The key fills the angle the two faces leave. It does not fill "
             "the channel -- there is a run of usable section above it and "
             "below it, the whole length of every seam, and it is the only "
             "continuous void in the building that reaches both the weather "
             "and the ground."),
            (), 24.0, (34.0, 10.0, 8.5), "sm_open"),
        Chapter(
            "water", "03", "Rain in at the ridge",
            f"{water['gallons_per_inch']:,.0f} gallons an inch.",
            ("First job: guttering.",
             "A slot along the outer cap takes water where it already runs. "
             "The seam is the low line between two panels, which is where a "
             "roof sends water anyway. Under the slot is a gutter with "
             "suction inlets, and under that a drain to the tank.",
             f"One inch of rain on this roof is "
             f"{water['gallons_per_inch']:,.0f} gallons. The building's "
             "guttering is inside its structure rather than bolted onto its "
             "edge."),
            (), 28.0, (40.0, 16.0, 12.0), "sm_water"),
        Chapter(
            "air", "04", "The air barrier",
            f"{air['pressure_pa']:.0f} pascals, and a leak stops being a "
            f"leak.",
            ("Second job, and it is the one that changes how you think "
             "about leaks.",
             f"Run the fan so the inside sits about "
             f"{air['pressure_pa']:.0f} pascals above outside, and the net "
             f"flow at every gap is outward. A gap in an inward-leaking "
             f"building admits weather. The same gap in an outward-flowing "
             f"one does not, because the air is going the wrong way for "
             f"anything to ride in on.",
             f"It is {air['cfm']:,.0f} cubic feet a minute over "
             f"{feet:,.0f} feet of seam -- a bathroom extractor. And it "
             "only works while it runs, which is why it is a second line "
             "behind the cap rather than a replacement for it."),
            (), 30.0, (44.0, 12.0, 12.6), "sm_air"),
        Chapter(
            "dry", "05", "Drying the wood",
            "Air along the faces, or through the silica.",
            ("Third job.",
             "A perforated liner washes air down both sawn faces of every "
             "member. That is the surface most at risk in a timber frame "
             "and the hardest to reach, and it now has moving air on it "
             "permanently.",
             "When the weather is too wet for moving air to dry anything, a "
             "three-way gate routes the same flow through a silica "
             "cartridge instead. The cartridge pulls out of a hatch and "
             "goes in an oven."),
            (), 26.0, (52.0, 15.0, 13.4), "sm_dry"),
        Chapter(
            "condense", "06", "Condensing on purpose",
            f"{water['peltier_gallons_per_year']:,.0f} gallons a year, and "
            f"here is what that is worth.",
            ("Fourth job, and this is the one the film has to be honest "
             "about.",
             "Thermoelectric plates on the cold side of the channel, "
             "dropping moisture out of the air as liquid straight into the "
             "gutter the rain already uses. The appeal is obvious: the "
             "plate sits exactly where the moisture is highest and the "
             "drain is right there.",
             f"Now the number. {water['peltier_watts']:,.0f} watts of "
             f"plates make {water['peltier_gallons_per_year']:,.0f} gallons "
             f"in a year. That is "
             f"{water['rain_inches_equal_to_a_year']:.1f} inches of rain. "
             f"At {water['kwh_per_litre']:.1f} kilowatt hours a litre it is "
             "several times worse than a compressor, and a compressor is "
             "already not how anybody sensible makes water on a roof.",
             "So they are a dehumidifier that happens to yield liquid. They "
             "are not a water supply. The water supply is the roof."),
            (), 34.0, (58.0, 13.0, 12.0), "sm_condense"),
        Chapter(
            "bill", "07", "What it costs",
            f"${bill['seam'].cost:,.0f} of module on a dome that lists at "
            f"${_dome_price():,.0f}.",
            ("And the price, because a system that is half the cost of the "
             "building it is fitted to has to argue for itself.",
             f"The module is ${bill['seam'].cost:,.0f} across the whole "
             f"dome. The cap, the liner, the gutter and the drain are per "
             f"foot of seam and grow with the building; the gates, the "
             f"cartridges and the plates are per seam and grow more slowly.",
             "If you fit one part of it, fit the gutter. Water off the roof "
             "is the best return here, it needs no power, and it is the "
             "only piece that pays for itself in a season."),
            (), 28.0, (50.0, 14.0, 13.0), "sm_bill"),
    )


def _dome_price() -> float:
    import seed_model

    return seed_model.quote().price


CHAPTERS = _chapters()


def seam_report() -> str:
    return systems.report()


def validate_seam_lesson() -> None:
    """Every chapter has a scene, and the honest number is still in the cut."""
    systems.validate_systems()

    slugs = [c.slug for c in CHAPTERS]
    assert len(set(slugs)) == len(slugs), slugs
    for chapter in CHAPTERS:
        assert chapter.stage in SCENES, (chapter.slug, chapter.stage)
        assert chapter.narration, chapter.slug
        assert chapter.duration > 10.0, chapter.slug
        assert chapter.promise, chapter.slug

    # Every scene the film declares is used, or it is dead code on screen.
    used = {c.stage for c in CHAPTERS}
    assert used == set(SCENES), sorted(set(SCENES) - used)

    # The chapter that has to stay in: the film may not quietly drop the
    # comparison that judges its own best idea.
    condense = next(c for c in CHAPTERS if c.slug == "condense")
    spoken = " ".join(condense.narration).lower()
    assert "not a water supply" in spoken, (
        "the condensing chapter no longer states that the plates are not a "
        "water supply; that sentence is the point of the chapter")

    total = sum(c.duration for c in CHAPTERS)
    assert 120.0 <= total <= 420.0, total


SEAM_LESSON = Lesson(
    key="seam",
    brand="THE STEM CELL DOME / THE SEAM",
    title="The seam does four jobs",
    chapters=CHAPTERS,
    scenes=SCENES,
    selftest=validate_seam_lesson,
    report=seam_report,
    snapshot_prefix="seam",
    style="teaching",
    label_layout="declutter",
)


if __name__ == "__main__":
    validate_seam_lesson()
    total = sum(c.duration for c in CHAPTERS)
    print(f"seam lesson ok: {len(CHAPTERS)} chapters, {total / 60.0:.1f} min")
