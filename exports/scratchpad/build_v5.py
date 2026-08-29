"""Version five: v4 without the girlfriend remark, and plain instead of party."""

from pathlib import Path

NL = chr(10)
p = Path(r"C:\Users\Don\Desktop\DomeSim\two_v_demo\lesson_hype.py")
s = p.read_text(encoding="utf-8")

if "HYPE_V5_LESSON" in s:
    raise SystemExit("v5 already present")

body = '''

# ----------------------------------------------------------------------
# Version five: v4, but sober
# ----------------------------------------------------------------------

# The endgame beat reverts to the shorter form -- the projection cratering
# and nothing further.
CHAPTERS_V5 = tuple(
    replace(chapter, narration=(
        "And I will be completely transparent about the endgame. Somewhere there",
        "is a man on his seventh holiday of the year, watching the projected yield",
        "on a portfolio of rental houses, and I would like that line to do",
        "something sudden and downward on account of this. That is the strategy.",
        "It is entirely transparent and only slightly relatable, and I have made",
        "my peace with it.",
    ))
    if chapter.slug == "hr" else chapter
    for chapter in CHAPTERS_V4
)


_HYPE_V5_BASE = Lesson(
    key="hype5",
    brand="FRANKENDOME",
    title="Frankendome, Version Five",
    chapters=CHAPTERS_V5,
    scenes=SCENES_V3,
    snapshot_prefix="hype5",
    style="hype",
    voice_rate="+7%",
    label_layout="declutter",
)

# The plain frankendome stands in for the party sting: same bones, no
# celebration.
HYPE_V5_LESSON = compose(
    _HYPE_V5_BASE,
    include=("franken_plain",),
    exclude=("cta_share",),
)
'''

p.write_text(s.rstrip() + NL + body, encoding="utf-8")
print("v5 written")

registry = Path(r"C:\Users\Don\Desktop\DomeSim\two_v_demo\lesson_registry.py")
r = registry.read_text(encoding="utf-8")
r = r.replace(
    "    HYPE_V4_LESSON," + NL + ")",
    "    HYPE_V4_LESSON," + NL + "    HYPE_V5_LESSON," + NL + ")", 1)
r = r.replace(
    "                   HYPE_V4_LESSON)",
    "                   HYPE_V4_LESSON, HYPE_V5_LESSON)", 1)
registry.write_text(r, encoding="utf-8")
print("hype5 registered")

deliv = Path(r"C:\Users\Don\Desktop\DomeSim\two_v_demo\deliverables.py")
d = deliv.read_text(encoding="utf-8")
old = ('                compose=True, segments=("party",)),' + NL + ")")
new = ('                compose=True, segments=("party",)),' + NL
       + '    Deliverable("hype5", "frankendome-montage-v5.mp4",' + NL
       + '                "Version five: no girlfriend remark, and the plain "' + NL
       + '                "frankendome in place of the party sting.",' + NL
       + '                compose=True, segments=("franken_plain",)),' + NL
       + ")")
if old not in d:
    raise SystemExit("deliverable anchor not found")
deliv.write_text(d.replace(old, new, 1), encoding="utf-8")
print("v5 added to the manifest")
