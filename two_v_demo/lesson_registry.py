"""Every lesson the masterclass renderer can play.

Kept separate from ``lessons.py`` so that module stays free of scene code:
each lesson module imports ``render_kit`` and its own geometry, and this
registry is the only place that imports all of them.
"""

from __future__ import annotations

from .lesson_build import BUILD_LESSON
from .lesson_cuts import CUTS_LESSON
from .lesson_franken import FRANKEN_LESSON
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
from .lesson_master import MASTER_LESSON
from .lesson_world import WORLD_LESSON
from .lesson_world_chatgpt import WORLD_CHATGPT_LESSON
from .lesson_zome import ZOME_LESSON
from .lessons import TWO_V_LESSON, Lesson


LESSONS: dict[str, Lesson] = {
    lesson.key: lesson
    for lesson in (TWO_V_LESSON, BUILD_LESSON, HEX_LESSON, ZOME_LESSON,
                   LINE_LESSON, CUTS_LESSON, FRANKEN_LESSON,
                   HYPE_LESSON, HYPE_V2_LESSON, HYPE_V3_LESSON,
                   HYPE_V4_LESSON, HYPE_V5_LESSON, HYPE_V6_LESSON,
                   KICKSTARTER_LESSON, KICKSTARTER_V2_LESSON,
                   MASTER_LESSON, WORLD_LESSON, WORLD_CHATGPT_LESSON)
}

DEFAULT_LESSON_KEY = TWO_V_LESSON.key


def get_lesson(key: str | None) -> Lesson:
    """Look a lesson up by key, with a clear error rather than a KeyError."""
    if not key:
        return LESSONS[DEFAULT_LESSON_KEY]
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
