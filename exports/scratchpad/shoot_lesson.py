"""Still frames from any lesson, mid-chapter, for named chapter slugs.

    py -3.12 shoot_lesson.py franken bracket_flat,bracket_bend,bracket_fitted
    py -3.12 shoot_lesson.py kick            # every chapter
"""

import sys

sys.path.insert(0, r"C:\Users\Don\Desktop\DomeSim")

import launcher_common as lc
from two_v_demo.app import main
from two_v_demo.lesson_registry import get_lesson

key = sys.argv[1]
wanted = set(sys.argv[2].split(",")) if len(sys.argv) > 2 else None
lesson = get_lesson(key)

times, clock = [], 0.0
for chapter in lesson.chapters:
    if wanted is None or chapter.slug in wanted:
        times.append(round(clock + chapter.duration * 0.62, 2))
    clock += chapter.duration

lc.write_config("two_v_masterclass", {
    "action": "shots",
    "lesson": key,
    "shots": ",".join(str(t) for t in times),
    "size": "1920x1080",
    "no_narration": True,
})
raise SystemExit(main())
