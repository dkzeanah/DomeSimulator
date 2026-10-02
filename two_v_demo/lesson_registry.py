"""Every lesson the masterclass renderer can play.

Kept separate from ``lessons.py`` so that module stays free of scene code:
each lesson module imports ``render_kit`` and its own geometry, and this
registry is the only place that imports all of them.
"""

from __future__ import annotations

from .lesson_all_domes import ALL_DOMES_LESSON
from .lesson_build import BUILD_LESSON
from .lesson_cabin_pilot import CABIN_PILOT_LESSON
from .lesson_cabin_wedge_explained import CABIN_WEDGE_EXPLAINED_LESSON
from .lesson_cabin_linseed_oil import CABIN_LINSEED_OIL_LESSON
from .lesson_seam_climate import CABIN_SEAM_CLIMATE_LESSON
from .lesson_cuts import CUTS_LESSON
from .lesson_dome_park import DOME_PARK_LESSON
from .lesson_bring_your_own_dome import BYOD_LESSON
from .lesson_byod_deepseek import BYOD_DEEPSEEK_LESSON
from .lesson_byod_styled import BYOD_POLISHED, BYOD_SNARKY
from .lesson_drama import DRAMA_LESSON, SERIES_LESSON
from .lesson_franken import FRANKEN_LESSON
from .lesson_harvest import HARVEST_LESSON
from .lesson_hex import HEX_LESSON
from .lesson_kickstarter import KICKSTARTER_LESSON
from .lesson_kickstarter_v2 import KICKSTARTER_V2_LESSON
from .lesson_hype import (
    HYPE_LESSON,
    HYPE_V2_LESSON,
    HYPE_V3_LESSON,
    HYPE_V4_LESSON,
    HYPE_V5_LESSON,
    HYPE_V6_LESSON,
)
from .lesson_line import LINE_LESSON
from .lesson_lookbook import LOOKBOOK_LESSON
from .lesson_master import MASTER_LESSON
from .lesson_pine_value import PINE_VALUE_LESSON
from .lesson_scratch import SCRATCH_LESSON
from .lesson_pitch_hero import PITCH_HERO_LESSON
from .lesson_seed_pitch import SEED_PITCH_LESSON
from .lesson_module_build import MODULE_BUILD_LESSON
from .lesson_seam import SEAM_LESSON
from .lesson_wedge import WEDGE_LESSON
from .lesson_wedge_why import WEDGE_WHY_LESSON
from .lesson_why_build import WHY_BUILD_LESSON
from .lesson_world import WORLD_LESSON
from .lesson_world_chatgpt import WORLD_CHATGPT_LESSON
from .lesson_zome import ZOME_LESSON
from .lesson_pvtwo import PVTWO_LESSON
from .lessons import TWO_V_LESSON, Lesson


LESSONS: dict[str, Lesson] = {
    lesson.key: lesson
    for lesson in (TWO_V_LESSON, BUILD_LESSON, HEX_LESSON, ZOME_LESSON,
                   LINE_LESSON, CUTS_LESSON, FRANKEN_LESSON,
                   HYPE_LESSON, HYPE_V2_LESSON, HYPE_V3_LESSON,
                   HYPE_V4_LESSON, HYPE_V5_LESSON, HYPE_V6_LESSON,
                   KICKSTARTER_LESSON, KICKSTARTER_V2_LESSON,
                   MASTER_LESSON, WORLD_LESSON, WORLD_CHATGPT_LESSON,
                   SCRATCH_LESSON, WEDGE_LESSON, DRAMA_LESSON,
                   SERIES_LESSON, LOOKBOOK_LESSON,
                   WEDGE_WHY_LESSON, HARVEST_LESSON, WHY_BUILD_LESSON,
                   PINE_VALUE_LESSON,
                   PVTWO_LESSON, ALL_DOMES_LESSON, DOME_PARK_LESSON, BYOD_LESSON,
                   BYOD_DEEPSEEK_LESSON, BYOD_POLISHED, BYOD_SNARKY,
                   SEED_PITCH_LESSON, MODULE_BUILD_LESSON,
                   SEAM_LESSON,
                   PITCH_HERO_LESSON,
                   CABIN_PILOT_LESSON,
                   CABIN_WEDGE_EXPLAINED_LESSON,
                   CABIN_LINSEED_OIL_LESSON,
                   CABIN_SEAM_CLIMATE_LESSON)
}

# Every earlier film, re-staged in the Cabin World (two_v_demo/cabin_stage.py):
# the same chapters and painters on the exhibit platform, with cinematic
# cameras. Keyed "cabin_<original key>" -- the re-render queue's target keys.
from .cabin_stage import restage as _restage

for _key in [k for k in LESSONS if not k.startswith("cabin_")]:
    # A drama's own camera direction is its storytelling: keep it. So is the
    # harvest's, which follows one thin tree down and round its wedges.
    LESSONS.setdefault(f"cabin_{_key}", _restage(
        LESSONS[_key], keep_original_cameras=_key in ("drama", "series", "harvest")))

# Concepts from ingested videos (concepts/cards/*.json), filmed in the Cabin World.
try:
    from concepts.film import concept_lessons as _concept_lessons
except ImportError:          # running without the repository root on the path
    _concept_lessons = list
for _lesson in _concept_lessons():
    LESSONS.setdefault(_lesson.key, _lesson)

DEFAULT_LESSON_KEY = TWO_V_LESSON.key


def get_lesson(key: str | None) -> Lesson:
    """Look a lesson up by key, with a clear error rather than a KeyError."""
    if not key:
        return LESSONS[DEFAULT_LESSON_KEY]
    if key.startswith("teaser_") and key not in LESSONS:
        # Every film's teaser is built on request from the film itself.
        from .teasers import teaser_lesson
        return teaser_lesson(key[len("teaser_"):])
    try:
        return LESSONS[key]
    except KeyError:
        raise ValueError(
            f"unknown lesson {key!r}; choose from {', '.join(sorted(LESSONS))}"
        ) from None


def lesson_menu() -> str:
    return "\n".join(
        f"  {lesson.key:<6} {lesson.title} "
        f"({len(lesson.chapters)} chapters)"
        for lesson in LESSONS.values()
    )
