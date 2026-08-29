"""Insert the call-to-action act into the montage, after the business model."""

import re
from pathlib import Path

NL = chr(10)
base = Path(r"C:\Users\Don\Desktop\DomeSim\two_v_demo\lesson_hype.py")
scratch = Path(r"C:\Users\Don\AppData\Local\Temp\claude"
               r"\C--Users-Don-Desktop-DomeSim"
               r"\bb2f0342-d0bb-4db9-b958-9985ff7ceb8f\scratchpad")

s = base.read_text(encoding="utf-8")
scenes = (scratch / "cta_scenes.txt").read_text(encoding="utf-8")
chapters = (scratch / "cta_chapters.txt").read_text(encoding="utf-8")

if "scene_hype_asymmetry" not in s:
    # Scenes go in ahead of the SCENES table.
    anchor = "SCENES = {"
    index = s.index(anchor)
    s = s[:index] + scenes.strip() + NL + NL + NL + s[index:]
    # And into the table itself.
    s = s.replace(
        '    "hype_socials": scene_hype_socials,',
        '    "hype_asymmetry": scene_hype_asymmetry,' + NL
        + '    "hype_friend": scene_hype_friend,' + NL
        + '    "hype_share": scene_hype_share,' + NL
        + '    "hype_audiences": scene_hype_audiences,' + NL
        + '    "hype_needs": scene_hype_needs,' + NL
        + '    "hype_number": scene_hype_number,' + NL
        + '    "hype_hr": scene_hype_hr,' + NL
        + '    "hype_socials": scene_hype_socials,', 1)

if '"serious", "27"' not in s:
    # The act lands after the empire collapses and before "that is the
    # point", so the film turns serious exactly where the joke runs out.
    anchor = '    Chapter(' + NL + '        "thepoint", "27",'
    index = s.index(anchor)
    s = s[:index] + chapters.rstrip() + NL + s[index:]
    # Renumber every beat from the insertion point onward.
    head, tail = s[:index], s[index:]
    numbers = re.findall(r'^        "(\w+)", "(\d\d)"', tail, flags=re.M)
    for offset, (slug, number) in enumerate(numbers):
        tail = tail.replace(f'"{slug}", "{number}"',
                            f'"{slug}", "{27 + len(chapters.strip().split("Chapter(")) - 1 + offset:02d}"',
                            1)
    s = head + tail

base.write_text(s, encoding="utf-8")
print("call to action inserted")
