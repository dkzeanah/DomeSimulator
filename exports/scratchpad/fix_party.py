"""Three fixes to the party sting and the timber it is made of."""

from pathlib import Path

NL = chr(10)
Q = chr(34) * 3


def sub(path: Path, old: str, new: str) -> None:
    s = path.read_text(encoding="utf-8")
    if old not in s:
        raise SystemExit(f"pattern not found in {path.name}:" + NL + old[:280])
    path.write_text(s.replace(old, new, 1), encoding="utf-8")


# --- 1. smoother sticks -------------------------------------------------
# Independent random radius per segment made visible steps down the
# length. A smooth function of position keeps the irregularity but loses
# the beading.
timber = Path(r"C:\Users\Don\Desktop\DomeSim\two_v_demo\timber.py")
sub(
    timber,
    "        mid = (t + (index - 1) / steps) * 0.5" + NL
    + "        thickness = radius * (" + NL
    + "            1.0 + style.taper * (_noise(seed, 20 + index) - 0.5) * 2.0" + NL
    + "        )",
    "        mid = (t + (index - 1) / steps) * 0.5" + NL
    + "        # Thickness varies smoothly along the stick rather than" + NL
    + "        # independently per segment: independent draws put a visible" + NL
    + "        # step at every joint and the stick read as a string of beads." + NL
    + "        swell = (" + NL
    + "            math.sin(mid * math.pi * (1.0 + _noise(seed, 21) * 2.0)" + NL
    + "                     + _noise(seed, 22) * math.tau)" + NL
    + "            + 0.45 * math.sin(mid * math.pi * 4.0 + _noise(seed, 23) * 6.0)" + NL
    + "        ) / 1.45" + NL
    + "        thickness = radius * (1.0 + style.taper * swell)",
)

# --- 2. per-chapter overlay override ------------------------------------
lessons = Path(r"C:\Users\Don\Desktop\DomeSim\two_v_demo\lessons.py")
sub(
    lessons,
    "    camera: tuple[float, float, float]" + NL
    + "    stage: str",
    "    camera: tuple[float, float, float]" + NL
    + "    stage: str" + NL
    + "    overlay: str | None = None" + NL
    + "    " + Q + "Override the lesson's style for this chapter alone." + NL + NL
    + "    A sting dropped into a teaching lesson should not wear the" + NL
    + "    teaching cards; set this to 'hype' and it goes full-frame for" + NL
    + "    those few seconds and then hands the cards back." + Q,
)

app = Path(r"C:\Users\Don\Desktop\DomeSim\two_v_demo\app.py")
sub(
    app,
    "    def draw_ui(self, width: int, height: int) -> object:" + NL
    + '        if self.lesson.style == "hype":' + NL
    + "            return self.draw_ui_hype(width, height)" + NL
    + "        return self.draw_ui_teaching(width, height)",
    "    def draw_ui(self, width: int, height: int) -> object:" + NL
    + "        # A chapter may override the lesson's style, which is how a" + NL
    + "        # four-second sting goes full-frame inside a teaching lesson." + NL
    + "        chapter = self.chapters[self.chapter_index]" + NL
    + "        style = chapter.overlay or self.lesson.style" + NL
    + '        if style == "hype":' + NL
    + "            return self.draw_ui_hype(width, height)" + NL
    + "        return self.draw_ui_teaching(width, height)",
)
sub(
    lessons,
    '        if self.style not in ("teaching", "hype"):',
    "        for chapter in self.chapters:" + NL
    + '            if chapter.overlay not in (None, "teaching", "hype"):' + NL
    + "                raise ValueError(" + NL
    + "                    f\"lesson {self.key!r} chapter {chapter.number} has \"" + NL
    + "                    f\"unknown overlay {chapter.overlay!r}\"" + NL
    + "                )" + NL
    + '        if self.style not in ("teaching", "hype"):',
)

# --- 3. hold on raw wood, then cut fast ---------------------------------
segments = Path(r"C:\Users\Don\Desktop\DomeSim\two_v_demo\segments.py")
sub(
    segments,
    "    # Fast at the start, slowing to a stop on the final look." + NL
    + "    eased = 1.0 - (1.0 - clamp(p)) ** 2.2" + NL
    + "    index = min(len(PARTY_LOOKS) - 1, int(eased * len(PARTY_LOOKS)))",
    "    # Open on raw timber and hold it long enough to register -- it is" + NL
    + "    # the shot the whole sting is about -- then cut through the rest" + NL
    + "    # quickly and settle on the last one." + NL
    + "    progress = clamp(p)" + NL
    + "    if progress < 0.20:" + NL
    + "        index = 0" + NL
    + "    else:" + NL
    + "        remaining = (progress - 0.20) / 0.80" + NL
    + "        index = min(len(PARTY_LOOKS) - 1," + NL
    + "                    1 + int((remaining ** 0.72) * (len(PARTY_LOOKS) - 1)))" + NL
    + "    eased = progress",
)
sub(
    segments,
    "            (), 4.0, (28.0, 24.0, 18.0), \"seg_party\",",
    "            (), 4.0, (28.0, 24.0, 18.0), \"seg_party\", \"hype\",",
)

print("timber smoothed, overlay override added, party pacing fixed")
