"""Give the engine a cinematic display mode and a per-lesson speech rate.

A teaching lesson wants its cards: the promise, the narration and the live
figures all on screen at once.  A montage wants the opposite -- the
picture full-frame with one line of type over it -- so the overlay becomes
a property of the lesson rather than something hardcoded in the renderer.
"""

from pathlib import Path

NL = chr(10)


def sub(path: Path, old: str, new: str) -> None:
    s = path.read_text(encoding="utf-8")
    if old not in s:
        raise SystemExit(f"pattern not found in {path.name}: {old[:200]}")
    path.write_text(s.replace(old, new, 1), encoding="utf-8")


lessons = Path(r"C:\Users\Don\Desktop\DomeSim\two_v_demo\lessons.py")
sub(
    lessons,
    "    report: Callable[[], str] | None = None" + NL
    + '    snapshot_prefix: str = "lesson"',
    "    report: Callable[[], str] | None = None" + NL
    + '    snapshot_prefix: str = "lesson"' + NL
    + '    style: str = "teaching"' + NL
    + '    """``teaching`` draws the cards; ``hype`` goes full-frame with one' + NL
    + '    line of type and no chrome."""' + NL
    + "    voice_rate: str | None = None" + NL
    + '    """Speech rate for this lesson, when it wants its own pacing."""',
)
sub(
    lessons,
    '            raise ValueError(f"lesson {self.key!r} has no chapters")',
    '            raise ValueError(f"lesson {self.key!r} has no chapters")' + NL
    + '        if self.style not in ("teaching", "hype"):' + NL
    + "            raise ValueError(" + NL
    + '                f"lesson {self.key!r} has unknown style {self.style!r}"' + NL
    + "            )",
)

app = Path(r"C:\Users\Don\Desktop\DomeSim\two_v_demo\app.py")

# The lesson's own rate is the default; an explicit launcher field still wins.
sub(
    app,
    '    voice_rate = cfg.get("voice_rate", DEFAULT_RATE)',
    '    voice_rate = cfg.get("voice_rate") or DEFAULT_RATE',
)
sub(
    app,
    "    try:" + NL
    + '        size = parse_size(cfg.get("size", "1600x900"))',
    "    # A montage lesson carries its own pacing, which the launcher can" + NL
    + "    # still override by filling the Rate field in." + NL
    + '    if not cfg.get("voice_rate") and lesson.voice_rate:' + NL
    + "        voice_rate = lesson.voice_rate" + NL
    + "    try:" + NL
    + '        size = parse_size(cfg.get("size", "1600x900"))',
)

# The overlay branches on the lesson's style.
sub(
    app,
    "    def draw_ui(self, width: int, height: int) -> object:" + NL
    + "        pg = self.pygame",
    '    def draw_ui(self, width: int, height: int) -> object:' + NL
    + '        if self.lesson.style == "hype":' + NL
    + "            return self.draw_ui_hype(width, height)" + NL
    + "        return self.draw_ui_teaching(width, height)" + NL
    + NL
    + "    def draw_ui_hype(self, width: int, height: int) -> object:" + NL
    + '        """Full-frame picture, one line of type, no chrome.' + NL
    + NL
    + "        Everything the teaching overlay puts in cards is dropped: a" + NL
    + "        montage is carried by the pictures and the voice, and a" + NL
    + "        sidebar of prose competes with both." + NL
    + '        """' + NL
    + "        pg = self.pygame" + NL
    + "        surface = pg.Surface((width, height), pg.SRCALPHA)" + NL
    + "        scale = min(width / 1600.0, height / 900.0)" + NL
    + "        chapter = self.chapters[self.chapter_index]" + NL
    + "        self.ui_buttons.clear()" + NL
    + NL
    + "        # Labels stay: they are part of the picture, not the chrome." + NL
    + "        for world_label in self.world_labels:" + NL
    + "            screen = project_point(self.mvp, world_label.point, width, height)" + NL
    + "            if screen is None:" + NL
    + "                continue" + NL
    + "            lines = world_label.text.splitlines()" + NL
    + "            label_font = self.font(max(13, int(17 * scale)), True)" + NL
    + "            widest = max(label_font.size(line)[0] for line in lines)" + NL
    + "            label_height = len(lines) * int(22 * scale) + int(14 * scale)" + NL
    + "            rect = pg.Rect(" + NL
    + "                int(screen[0] - widest * 0.5 - 10 * scale)," + NL
    + "                int(screen[1] - label_height * 0.5)," + NL
    + "                int(widest + 20 * scale), label_height)" + NL
    + "            self.rounded_panel(surface, rect, (3, 10, 18, 210)," + NL
    + "                               (*world_label.color, 190), int(7 * scale))" + NL
    + "            line_y = rect.y + int(7 * scale)" + NL
    + "            for line in lines:" + NL
    + "                rendered = label_font.render(line, True, world_label.color)" + NL
    + "                surface.blit(rendered, (" + NL
    + "                    rect.centerx - rendered.get_width() // 2, line_y))" + NL
    + "                line_y += int(22 * scale)" + NL
    + NL
    + "        # A scrim only under the type, so the picture stays clean." + NL
    + "        headline_font = self.font(max(30, int(54 * scale)), True)" + NL
    + "        kicker_font = self.font(max(13, int(19 * scale)), True)" + NL
    + "        margin = int(70 * scale)" + NL
    + "        lines = self.wrap_text(chapter.promise, headline_font," + NL
    + "                               width - 2 * margin)" + NL
    + "        block_height = len(lines) * int(64 * scale) + int(46 * scale)" + NL
    + "        block_top = height - int(96 * scale) - block_height" + NL
    + "        scrim = pg.Surface((width, block_height + int(120 * scale))," + NL
    + "                           pg.SRCALPHA)" + NL
    + "        for row in range(scrim.get_height()):" + NL
    + "            alpha = int(196 * min(1.0, row / (scrim.get_height() * 0.55)))" + NL
    + "            pg.draw.line(scrim, (3, 8, 16, alpha), (0, row), (width, row))" + NL
    + "        surface.blit(scrim, (0, block_top - int(52 * scale)))" + NL
    + NL
    + "        kicker = kicker_font.render(chapter.title.upper(), True, (61, 211, 255))" + NL
    + "        surface.blit(kicker, (margin, block_top - int(6 * scale)))" + NL
    + "        text_y = block_top + int(30 * scale)" + NL
    + "        for line in lines:" + NL
    + "            shadow = headline_font.render(line, True, (2, 6, 12))" + NL
    + "            surface.blit(shadow, (margin + int(3 * scale)," + NL
    + "                                  text_y + int(3 * scale)))" + NL
    + "            surface.blit(headline_font.render(line, True, (240, 247, 252))," + NL
    + "                         (margin, text_y))" + NL
    + "            text_y += int(64 * scale)" + NL
    + NL
    + "        # One hairline of progress, and nothing else." + NL
    + "        played = (self.timeline % self.total_duration) / self.total_duration" + NL
    + "        bar = int(5 * scale)" + NL
    + "        pg.draw.rect(surface, (22, 44, 60, 220)," + NL
    + "                     pg.Rect(0, height - bar, width, bar))" + NL
    + "        pg.draw.rect(surface, (255, 177, 62, 255)," + NL
    + "                     pg.Rect(0, height - bar, int(width * played), bar))" + NL
    + "        return surface" + NL
    + NL
    + "    def draw_ui_teaching(self, width: int, height: int) -> object:" + NL
    + "        pg = self.pygame",
)

print("hype style and per-lesson voice rate added")
