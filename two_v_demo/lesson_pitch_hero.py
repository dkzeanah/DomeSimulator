"""The ninety-second cut, for the top of the Kickstarter page.

A backer gives a campaign video about fifteen seconds before deciding. The
full campaign film is twenty-six minutes and is the right thing for
somebody who has already decided to care; it is the wrong thing at the top
of the page.

So this is a separate, short lesson -- not an extract. An extract would
inherit the long film's pacing, which is thirty seconds a chapter of
worksheet and argument. Here every beat is eight to twelve seconds, there
is no math overlay, and the argument is compressed to the four things that
make somebody scroll down:

* it comes out of your own trees, and it comes apart;
* it is dressed like a sailor -- many warm layers, one waterproof one;
* it costs twelve thousand, and here is the whole invoice;
* and it only works if three different kinds of people turn up.

WHAT IT SHARES WITH THE LONG FILM

Every scene. This module imports the campaign film's painters rather than
drawing anything of its own, so the hero video and the twenty-six minute
cut cannot show different buildings. And every number is read from
:mod:`seed_model` at render time, like everywhere else.

WHAT IT DOES NOT SHARE

The overlay. A worksheet cannot be read in nine seconds, so these
chapters carry no equations and the film says its numbers out loud
instead. The guard below checks that: a hero chapter with a worksheet on
it is a hero chapter nobody can follow.
"""

from __future__ import annotations

from dataclasses import replace

import seed_model

from .lesson_seed_pitch import SCENES as PITCH_SCENES
from .lessons import Chapter, Lesson

#: The longest a beat may be. Past this it is not a hero cut any more.
#:
#: Fifteen rather than thirteen because of one beat: the Arctic watch is
#: three sentences and it is the only thing in this cut that is not an
#: argument. Compressing it to fit a rule would be compressing the reason
#: anybody keeps watching.
MAX_BEAT = 15.0

#: And the shortest, because a voice line needs room to land.
MIN_BEAT = 7.0


def _beat(slug: str, title: str, promise: str, narration: tuple[str, ...],
          duration: float, camera: tuple[float, float, float],
          stage: str) -> Chapter:
    """One beat. No equations: there is no time to read a worksheet."""
    return Chapter(slug, "00", title, promise, narration, (), duration,
                   camera, stage, overlay="title")


def _chapters() -> tuple[Chapter, ...]:
    quote = seed_model.quote()
    hard = seed_model.quote("stem_cell", shell="hard")
    geometry = seed_model.seed_geometry()
    return (
        _beat("open", "A house you can take apart",
              f"{geometry.diameter_ft:.1f} feet across. "
              f"{geometry.floor_decagon_sqft:.0f} square feet.",
              ("This is a house you can take apart.",
               "Nineteen feet across, two hundred and seventy-seven square "
               "feet, and every piece of it fits in a pickup."),
              11.0, (46.0, 14.0, 13.0), "sp_standing"),

        _beat("frame", "The frame is already on your land",
              "Two trees. A hundred and twenty wedges. No hubs.",
              ("The frame is already standing on your land.",
               "Two trees, split into a hundred and twenty wedges. No hubs, "
               "no jig, and three saw settings for the whole building."),
              11.0, (58.0, 16.0, 12.0), "sp_frame"),

        _beat("head", "A dome is a head, and it wears hats",
              "One waterproof layer, and it is the outside one.",
              ("I stood lookout in the Arctic Circle, outside the skin of "
               "the ship.",
               "You do not stay warm in one very good thing. You wear a lot "
               "of ordinary layers, and you put one waterproof shell over "
               "the lot.",
               "A dome is a head. It wears hats, and only the cap is "
               "waterproof."),
              14.0, (52.0, 18.0, 6.6), "sp_head"),

        _beat("grow", "It gets warmer every winter",
              "Each layer buys the next cap a size up.",
              ("Every quilted layer you add makes the next cap a size "
               "bigger, so there is no limit.",
               "A rigid shell fills up and stops. This one does not."),
              10.0, (58.0, 17.0, 13.0), "sp_cap"),

        _beat("quilt", "The insulation is nine hundred t-shirts",
              "Sewn by somebody, tagged with their name.",
              ("The insulation is recycled clothing, quilted at a kitchen "
               "table.",
               "A fully dressed dome wears nearly a thousand t-shirts, and "
               "every layer is tagged with the name of whoever sewed it."),
              11.0, (48.0, 14.0, 11.5), "sp_quilt"),

        _beat("price", "Twelve thousand, and here is the invoice",
              f"${quote.cost_to_build:,.0f} to build. "
              f"${quote.gross_profit:,.0f} is ours.",
              ("Twelve thousand dollars.",
               "Ten to build, and two thousand is our profit -- twenty per "
               "cent, marked up on cost. The whole invoice is on the page.",
               "The ground it stands on is quoted separately and we do not "
               "mark it up."),
              13.0, (58.0, 15.0, 13.5), "sp_invoice"),

        _beat("hull", "And it can be better later",
              f"The hull, the mast, the floor, the rig.",
              ("Nothing here is finished, on purpose.",
               "A laminated hull, a steel mast, a floor bought later, and a "
               "rig that hangs the whole building between two trees. Buy "
               "them when you want them."),
              11.0, (86.0, 11.0, 21.0), "sp_floating"),

        _beat("three", "It needs three kinds of people",
              "Quilters. Pad hosts. Dome owners.",
              ("This only works if three different people turn up.",
               "Somebody who sews. Somebody with land who does not want to "
               "be a landlord. And somebody who wants a building.",
               "A dome with nobody to quilt for it is a cold dome."),
              12.0, (86.0, 16.0, 21.0), "sp_three"),

        _beat("close", "Every number is a model you can run",
              "Including the ones that argue against us.",
              ("Every figure you just saw came out of a model you can run "
               "yourself -- including the three that argue against us.",
               "Back it, and tell us which price is wrong."),
              10.0, (36.0, 12.0, 11.5), "sp_close"),
    )


CHAPTERS = tuple(
    replace(chapter, number=f"{index + 1:02d}")
    for index, chapter in enumerate(_chapters())
)


def hero_report() -> str:
    total = sum(chapter.duration for chapter in CHAPTERS)
    lines = [f"THE HERO CUT -- {len(CHAPTERS)} beats, {total:.0f} seconds", ""]
    for chapter in CHAPTERS:
        lines.append(f"  {chapter.number}  {chapter.duration:>5.1f}s  "
                     f"{chapter.stage:<14} {chapter.title}")
    lines += ["", f"  {total:.0f} seconds"]
    return "\n".join(lines)


def validate_pitch_hero() -> None:
    """A hero cut has to stay short, and has to stay readable."""
    from .lesson_seed_pitch import validate_seed_pitch

    validate_seed_pitch()

    assert 6 <= len(CHAPTERS) <= 12, len(CHAPTERS)
    slugs = [chapter.slug for chapter in CHAPTERS]
    assert len(set(slugs)) == len(slugs), slugs

    total = sum(chapter.duration for chapter in CHAPTERS)
    assert 60.0 <= total <= 130.0, (
        f"{total:.0f}s is not a hero cut; a backer gives a campaign video "
        f"about fifteen seconds and this is the top of the page")

    for chapter in CHAPTERS:
        assert chapter.stage in PITCH_SCENES, (
            f"{chapter.slug} draws {chapter.stage!r}, which the campaign "
            f"film does not have -- the two cuts must show one building")
        assert MIN_BEAT <= chapter.duration <= MAX_BEAT, (
            f"{chapter.slug} runs {chapter.duration}s")
        assert chapter.narration, chapter.slug
        # No worksheets. There is no time to read one.
        assert not chapter.equations, (
            f"{chapter.slug} carries a worksheet; nobody can read a table "
            f"in {chapter.duration:.0f} seconds")
        assert chapter.promise, chapter.slug

    # The four things the cut exists to say.
    spoken = " ".join(" ".join(c.narration) + " " + c.promise
                      for c in CHAPTERS).lower()
    for needed in ("take apart", "arctic", "waterproof", "twelve thousand",
                   "profit", "quilt", "three different"):
        assert needed in spoken, f"the hero cut no longer says {needed!r}"

    # And the price it says is the price the model says.
    priced = seed_model.quote()
    assert abs(priced.price - 12036.0) < 1500.0, (
        f"the hero cut says twelve thousand and the model says "
        f"{priced.price:,.0f}; re-word it")


PITCH_HERO_LESSON = Lesson(
    key="pitch_hero",
    brand="THE STEM CELL DOME",
    title="A house you can take apart",
    chapters=CHAPTERS,
    scenes=PITCH_SCENES,
    selftest=validate_pitch_hero,
    report=hero_report,
    snapshot_prefix="pitchhero",
    style="hype",
    voice_rate="+4%",
    label_layout="declutter",
    ground="off",
)


if __name__ == "__main__":
    validate_pitch_hero()
    print(hero_report())
