"""Version four: v3 plus the segments, the girlfriend line, and 'Psych'."""

from pathlib import Path

NL = chr(10)
Q = chr(34) * 3
p = Path(r"C:\Users\Don\Desktop\DomeSim\two_v_demo\lesson_hype.py")
s = p.read_text(encoding="utf-8")

if "HYPE_V4_LESSON" in s:
    raise SystemExit("v4 already present")

body = '''

# ----------------------------------------------------------------------
# Version four: v3, plus the brand segments and two corrections
# ----------------------------------------------------------------------

# 1. The endgame, stated in full this time.
CHAPTERS_V4 = tuple(
    replace(chapter, narration=(
        "And I will be completely transparent about the endgame. Somewhere there",
        "is a man on his seventh holiday of the year, watching the projected yield",
        "on a portfolio of rental houses, and I would like that line to do",
        "something sudden and downward on account of this. And I would like his",
        "girlfriend to leave him over it. That is the strategy. It is entirely",
        "transparent and only slightly relatable, and I have made my peace with it.",
    ))
    if chapter.slug == "hr" else chapter
    for chapter in CHAPTERS_V3
)

# 2. "Sike" came out drawn to almost twice the length of "bike", which is
#    not the sound. "Psych" measures closest to it and carries the hard
#    final K, so it is spelled the way the dictionary spells it.
CHAPTERS_V4 = tuple(
    replace(chapter, narration=tuple(
        line.replace("Sike.", "Psych.") for line in chapter.narration))
    if chapter.slug == "psyche" else chapter
    for chapter in CHAPTERS_V4
)

# 3. The hand-written contact beat is dropped in favour of the modular
#    outro segment, which carries the corrected handles and is shared with
#    every other video.
CHAPTERS_V4 = tuple(
    chapter for chapter in CHAPTERS_V4 if chapter.slug != "follow"
)

CHAPTERS_V4 = tuple(
    replace(chapter, number=f"{index + 1:02d}")
    for index, chapter in enumerate(CHAPTERS_V4)
)


_HYPE_V4_BASE = Lesson(
    key="hype4",
    brand="FRANKENDOME",
    title="Frankendome, Version Four",
    chapters=CHAPTERS_V4,
    scenes=SCENES_V3,
    snapshot_prefix="hype4",
    style="hype",
    voice_rate="+7%",
    label_layout="declutter",
)

# The party sting lands before the outro; the montage keeps its own long
# call to action rather than taking the short generic one.
HYPE_V4_LESSON = compose(
    _HYPE_V4_BASE,
    include=("party",),
    exclude=("cta_share",),
)
'''

s = s.replace(
    "from .lessons import Chapter, Lesson",
    "from .lessons import Chapter, Lesson" + NL
    + "from .segments import compose", 1)
p.write_text(s.rstrip() + NL + body, encoding="utf-8")
print("v4 written")

registry = Path(r"C:\Users\Don\Desktop\DomeSim\two_v_demo\lesson_registry.py")
r = registry.read_text(encoding="utf-8")
r = r.replace(
    "from .lesson_hype import HYPE_LESSON, HYPE_V2_LESSON, HYPE_V3_LESSON",
    "from .lesson_hype import (" + NL
    + "    HYPE_LESSON," + NL
    + "    HYPE_V2_LESSON," + NL
    + "    HYPE_V3_LESSON," + NL
    + "    HYPE_V4_LESSON," + NL
    + ")", 1)
r = r.replace(
    "                   HYPE_LESSON, HYPE_V2_LESSON, HYPE_V3_LESSON)",
    "                   HYPE_LESSON, HYPE_V2_LESSON, HYPE_V3_LESSON," + NL
    + "                   HYPE_V4_LESSON)", 1)
registry.write_text(r, encoding="utf-8")
print("hype4 registered")
