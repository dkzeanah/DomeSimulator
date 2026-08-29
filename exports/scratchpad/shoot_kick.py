"""Still frames from the campaign lesson, one mid-chapter each.

Stills before video, always: a bad layout costs seconds here and forty
minutes in an export.
"""

import sys

sys.path.insert(0, r"C:\Users\Don\Desktop\DomeSim")

import launcher_common as lc
from two_v_demo.app import main
from two_v_demo.lesson_kickstarter import KICKSTARTER_LESSON as L

# Halfway through each chapter, where the reveals have finished animating.
times, clock = [], 0.0
for chapter in L.chapters:
    times.append(round(clock + chapter.duration * 0.55, 2))
    clock += chapter.duration

lc.write_config("two_v_masterclass", {
    "action": "shots",
    "lesson": "kick",
    "shots": ",".join(str(t) for t in times),
    "size": "1920x1080",
    "no_narration": True,
})
raise SystemExit(main())
