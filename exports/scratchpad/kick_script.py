

# ----------------------------------------------------------------------
# The script
#
# Side-on cameras (yaw 90) wherever two things are compared: the camera
# sits out on +Y, so a row laid along X only reads as a row from there.
# ----------------------------------------------------------------------

_SURFACE = advantages()[0]
_WIND = advantages()[3]
_CHEAP, _BUDGET, _PRISTINE, _FULL = BUILDS
_SMALL, _LARGE = flat_rate_table()[0], flat_rate_table()[-1]


CHAPTERS: tuple[Chapter, ...] = (
    Chapter(
        "title", "01", "A house that costs what its parts cost",
        "One hundred and twenty sticks and a weekend crew.",
        (
            "A house costs what somebody says it costs.",
            "This one costs what its parts cost, and you can count the parts.",
            "One hundred and twenty sticks. Forty triangles. Nine operations,",
            "repeated. That is the whole building.",
        ),
        (), 6.5, (34.0, 20.0, 17.0), "kick_title",
    ),
    Chapter(
        "problem", "02", "The shape everyone builds",
        f"{BOX.envelope_sqft:.0f} square feet of skin for "
        f"{BOX.footprint_sqft:.0f} of floor.",
        (
            "Start with the shape everybody already builds. Four walls, a roof,",
            "and corners. Give it three hundred and fourteen square feet of floor",
            f"and you have to build, wrap, seal and heat {BOX.envelope_sqft:.0f} square",
            "feet of outside. Every one of them costs money twice. Once to put up,",
            "and again every winter for as long as you live there.",
        ),
        (), 8.0, (54.0, 16.0, 21.0), "kick_problem",
    ),
    Chapter(
        "versus", "03", "Same floor, less building",
        f"{_SURFACE.percent_better:.0f}% less exterior, for the same floor.",
        (
            "Now put a dome next to it with exactly the same floor.",
            f"The house needs {BOX.envelope_sqft:.0f} square feet of skin.",
            f"The dome needs {DOME.envelope_sqft:.0f}.",
            f"That is {_SURFACE.percent_better:.0f} percent less to build, less to seal,",
            "less to paint, and less to heat, forever, for the same room to stand in.",
            "Nobody invented that. It is just what the shape does.",
        ),
        (), 9.5, (90.0, 12.0, 27.0), "kick_versus",
    ),
    Chapter(
        "triangle", "04", "Why it stands up",
        "A triangle cannot change shape without breaking.",
        (
            "Here is why it holds. Push on a square and it leans. The corners hinge,",
            "and every rectangular building on earth needs bracing to stop it.",
            "Push on a triangle and nothing happens. To change its shape you have to",
            "change the length of a side, which means breaking something.",
            "A dome is forty triangles. There is nothing left to brace.",
        ),
        (), 8.5, (90.0, 10.0, 24.0), "kick_triangle",
    ),
    Chapter(
        "wind", "05", "Nothing for the wind to push on",
        f"Drag {_WIND.dome:.2f} against {_WIND.other:.2f} for a box.",
        (
            "Wind is the same story. A flat wall catches everything thrown at it.",
            f"A box has a drag coefficient of about {_WIND.other:.2f}. A dome, about",
            f"{_WIND.dome:.2f}. Roughly {_WIND.percent_better:.0f} percent less load out of the",
            "shape alone, before you have bolted anything down. The wind arrives,",
            "finds nothing square to lean on, and goes over the top.",
        ),
        (), 8.0, (68.0, 14.0, 20.0), "kick_wind",
    ),
    Chapter(
        "flatrate", "06", "Nine times the house, same parts list",
        f"{_SMALL.floor_area_sqft:.0f} sq ft or {_LARGE.floor_area_sqft:.0f}: "
        f"{_LARGE.struts} struts either way.",
        (
            "And here is the part that makes it a business instead of a hobby.",
            f"A {_SMALL.diameter_ft:.0f} foot dome has {_SMALL.floor_area_sqft:.0f} square feet of floor.",
            f"A {_LARGE.diameter_ft:.0f} foot dome has {_LARGE.floor_area_sqft:.0f}. Nine times the house.",
            f"Both of them are {_LARGE.struts} struts, {_LARGE.brackets} brackets,",
            f"{_LARGE.screws} screws and {_LARGE.processes} operations. The sticks get longer.",
            "The parts list does not change at all. Learn to build one, and you have",
            "learned to build every size of it.",
        ),
        (), 9.5, (90.0, 12.0, 25.0), "kick_flatrate",
    ),
    Chapter(
        "proof", "07", "One already exists",
        "Four trees, ten days, half a year standing.",
        (
            "This is not a rendering of an idea. One of these is already standing",
            "in a yard. Four trees, cut and milled by hand. Ten days of work.",
            "A hundred and twenty brackets bent out of sheet metal on a bench,",
            "because buying them was not an option. It has been up through half",
            "a year of weather and it has not moved.",
        ),
        (), 8.5, (46.0, 16.0, 19.0), "fk_trees",
    ),
    Chapter(
        "brackets", "08", "Made, not bought",
        "A flat band, six holes, folded in half.",
        (
            "Every joint is a strip of flat steel with holes in it, folded once",
            "down the middle. Washing machine gauge. Four screws into each stick.",
            "That is the entire connector, and it is why the frame does not need",
            "a machine shop, a supplier, or permission from anyone to exist.",
        ),
        (), 7.5, (58.0, 18.0, 16.0), "fk_bracket_fitted",
    ),
    Chapter(
        "hat", "09", "Glass the top, skip the bottom",
        "The lowest twenty triangles are exactly half the shell.",
        (
            "Waterproofing is where the money goes, so here is the trick.",
            "Sort the forty triangles by height and the bottom twenty come to",
            "exactly half the surface. Exactly. That is a property of the shape,",
            "not a rounding. So glass the top twenty like a hat and leave the",
            f"bottom ring to the siding. {_PRISTINE.glass_sqft:.0f} square feet instead of",
            f"{_FULL.glass_sqft:.0f}. Half the resin, and resin is the expensive part.",
        ),
        (), 9.0, (40.0, 22.0, 17.0), "kick_hat",
    ),
    Chapter(
        "bom", "10", "Every part, bought new",
        f"${_PRISTINE.total:,.0f} at the till, nothing salvaged.",
        (
            "So price it honestly. Nothing free, nothing salvaged, nothing",
            "harvested. Pressure treated lumber off the rack. Sheathing, foam,",
            "epoxy, cloth, screws, and a basic kitchen and bathroom.",
            f"It comes to {_PRISTINE.total:,.0f} dollars. Three hundred and fourteen square",
            f"feet of floor at {_PRISTINE.per_sqft:.0f} dollars a square foot, finished.",
        ),
        (), 9.0, (90.0, 12.0, 26.0), "kick_bom",
    ),
    Chapter(
        "ladder", "11", "Four ways to build the same dome",
        f"${_CHEAP.total:,.0f} bare, ${_FULL.total:,.0f} with everything.",
        (
            "And that is the middle of the range. Bare frame, no foam, a hat on",
            f"top: {_CHEAP.total:,.0f} dollars. Pressure treated everywhere and glassed",
            f"all over: {_FULL.total:,.0f}. The same building, four ways, and the",
            "cheapest of them is under the price of a used car.",
            "Cut your own timber and the largest line on the sheet goes to zero.",
        ),
        (), 8.5, (90.0, 12.0, 25.0), "kick_ladder",
    ),
    Chapter(
        "lines", "12", "One skeleton, four products",
        "Home, shed, greenhouse, storm shelter.",
        (
            "One skeleton is already four products. A home. A storage shed.",
            "A greenhouse. A storm shelter you could put in a back yard.",
            "Four price points, four markets, and the same forty triangles",
            "underneath every one of them.",
        ),
        (), 7.5, (90.0, 14.0, 24.0), "hype_lines",
    ),
    Chapter(
        "themes", "13", "The bones do not care",
        "Any skin you like, on the same frame.",
        (
            "The bones do not care what you put on them. A baseball. A basketball.",
            "A disco ball with a facet on every panel. Forty flat faces, all of them",
            "replaceable, all of them pointing somewhere.",
            "It is a house that can also be a sign, a venue, or a greenhouse,",
            "without changing a single stick underneath.",
        ),
        (), 8.0, (34.0, 22.0, 17.0), "kick_themes",
    ),
    Chapter(
        "factory", "14", "What the money buys",
        f"${STARTUP.equipment_total:,.0f} of equipment, and the rest is material.",
        (
            "Which brings me to the ask, and I will be specific about it,",
            "because vague asks deserve to fail.",
            "A used flatbed. A trailer. A used telehandler, because a dome goes up",
            "in panels and panels are heavy. A portable sawmill, so the timber line",
            "on that cost sheet really does go to zero. Saws, jigs, a compressor,",
            "laminating gear and extraction. Six months of rent with the lights on,",
            "and the paperwork that makes it a company instead of a yard.",
        ),
        (), 11.0, (90.0, 12.0, 27.0), "kick_factory",
    ),
    Chapter(
        "ask", "15", "One hundred thousand dollars",
        f"${STARTUP.equipment_total:,.0f} of it is equipment. "
        f"${STARTUP.working_capital:,.0f} is the first domes.",
        (
            "One hundred thousand dollars.",
            f"{STARTUP.equipment_total / 1000:.0f} thousand of that is equipment that",
            "still exists on day three hundred, and the rest is material for the",
            "first units, so the thing can start paying for itself.",
            "I am not asking anyone to believe a projection. One is already built",
            "and standing. I am asking for the tools to build the next one faster",
            "than by hand, and the one after that faster than that.",
        ),
        (), 10.0, (34.0, 20.0, 17.0), "kick_ask",
    ),
)


def scene_kick_themes(app, opaque, transparent, p: float) -> None:
    """Themed skins, borrowed from the montage."""
    HYPE_SCENES["hype_themes"](app, opaque, transparent, p)


SCENES["kick_themes"] = scene_kick_themes


_KICKSTARTER_BASE = Lesson(
    key="kick",
    brand="DOMESIM",
    title="Build A Dome: The Campaign",
    chapters=CHAPTERS,
    scenes=SCENES,
    snapshot_prefix="kick",
    style="hype",
    voice_rate="+6%",
    label_layout="declutter",
)

KICKSTARTER_LESSON = compose(
    _KICKSTARTER_BASE,
    include=("whoami",),
    exclude=("cta_share", "party"),
)


def validate_kickstarter() -> None:
    """No claim on screen that the modules underneath cannot prove."""
    from .dome_advantage import validate_advantage
    from .dome_costing import validate_costing
    from .render_kit import TriangleBatch

    validate_advantage()
    validate_costing()

    lesson = KICKSTARTER_LESSON
    assert lesson.chapters, "no chapters"
    slugs = [chapter.slug for chapter in lesson.chapters]
    assert len(set(slugs)) == len(slugs), "duplicate slug"

    for chapter in lesson.chapters:
        assert chapter.stage in lesson.scenes, (chapter.slug, chapter.stage)
        assert chapter.narration, chapter.slug
        assert chapter.duration > 0.0, chapter.slug
        assert chapter.title and chapter.promise, chapter.slug
        for line in chapter.narration:
            assert line.strip(), chapter.slug

    # Every painter is a pure function of progress and gets both ends of
    # the range, so both ends have to survive being drawn.
    class _App:
        def __init__(self):
            self.world_labels = []

    for chapter in lesson.chapters:
        painter = lesson.scenes[chapter.stage]
        for progress in (0.0, 0.5, 1.0):
            app = _App()
            painter(app, TriangleBatch(), TriangleBatch(), progress)
            for label in app.world_labels:
                assert label.text.strip(), (chapter.stage, progress)
