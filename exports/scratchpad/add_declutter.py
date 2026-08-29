"""Opt-in label decluttering, so old renders reproduce and new ones read.

World labels are placed by projecting their 3-D anchor to the screen with
no awareness of each other, so two anchors that happen to project close
together stack their panels and their text collides.  That layering is
wanted -- it is part of the montage's look -- so this does not separate
labels.  It only stops *text* landing on *text*: panels may still overlap
freely, and a pair is nudged apart only once the overlap passes a
threshold, by the smallest amount that clears it.

Default is ``raw``, which is the behaviour every existing render used, so
re-rendering an old deliverable reproduces it exactly.
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
    '    voice_rate: str | None = None' + NL
    + '    """Speech rate for this lesson, when it wants its own pacing."""',
    '    voice_rate: str | None = None' + NL
    + '    """Speech rate for this lesson, when it wants its own pacing."""' + NL
    + '    label_layout: str = "raw"' + NL
    + '    """``raw`` places world labels exactly where they project, letting' + NL
    + '    them overlap. ``declutter`` keeps the overlap but nudges labels far' + NL
    + '    enough apart that text never lands on text. ``raw`` is the default' + NL
    + '    so that re-rendering an already published video reproduces it."""',
)
sub(
    lessons,
    '        if self.style not in ("teaching", "hype"):',
    '        if self.label_layout not in ("raw", "declutter"):' + NL
    + '            raise ValueError(' + NL
    + '                f"lesson {self.key!r} has unknown label layout "' + NL
    + '                f"{self.label_layout!r}"' + NL
    + '            )' + NL
    + '        if self.style not in ("teaching", "hype"):',
)

app = Path(r"C:\Users\Don\Desktop\DomeSim\two_v_demo\app.py")

# The shared placement pass.
sub(
    app,
    "    def draw_ui_hype(self, width: int, height: int) -> object:",
    '    # Two labels may overlap by this much of the smaller one before the' + NL
    + "    # layout pass intervenes. Generous on purpose: the overlapping look" + NL
    + "    # is wanted, only the unreadable part is not." + NL
    + "    LABEL_OVERLAP_TOLERANCE = 0.28" + NL
    + NL
    + "    def layout_labels(self, rects: list) -> list:" + NL
    + '        """Nudge labels apart only where they would bury each other.' + NL
    + NL
    + "        Returns the rects in the same order, moved vertically by the" + NL
    + "        smallest amount that brings every pairwise overlap under the" + NL
    + "        tolerance. Panels still overlap; glyphs no longer share pixels." + NL
    + '        """' + NL
    + '        if self.lesson.label_layout != "declutter":' + NL
    + "            return rects" + NL
    + "        placed: list = []" + NL
    + "        for rect in rects:" + NL
    + "            moved = rect.copy()" + NL
    + "            for _ in range(24):" + NL
    + "                clash = None" + NL
    + "                for other in placed:" + NL
    + "                    overlap = moved.clip(other)" + NL
    + "                    if not overlap.width or not overlap.height:" + NL
    + "                        continue" + NL
    + "                    smaller = min(moved.width * moved.height," + NL
    + "                                  other.width * other.height) or 1" + NL
    + "                    share = (overlap.width * overlap.height) / smaller" + NL
    + "                    if share > self.LABEL_OVERLAP_TOLERANCE:" + NL
    + "                        clash = other" + NL
    + "                        break" + NL
    + "                if clash is None:" + NL
    + "                    break" + NL
    + "                # Move whichever way is shorter, and only far enough" + NL
    + "                # to bring the pair back under the tolerance." + NL
    + "                if moved.centery >= clash.centery:" + NL
    + "                    moved.y = clash.bottom - int(moved.height * 0.22)" + NL
    + "                else:" + NL
    + "                    moved.y = clash.top - moved.height + int(" + NL
    + "                        moved.height * 0.22)" + NL
    + "            placed.append(moved)" + NL
    + "        return placed" + NL
    + NL
    + "    def draw_ui_hype(self, width: int, height: int) -> object:",
)

# Use it in the montage overlay.
sub(
    app,
    "        # Labels stay: they are part of the picture, not the chrome." + NL
    + "        for world_label in self.world_labels:" + NL
    + "            screen = project_point(self.mvp, world_label.point, width, height)" + NL
    + "            if screen is None:" + NL
    + "                continue" + NL
    + "            lines = world_label.text.splitlines()" + NL
    + "            if not lines:" + NL
    + "                continue" + NL
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
    + "                line_y += int(22 * scale)",
    "        # Labels stay: they are part of the picture, not the chrome." + NL
    + "        label_font = self.font(max(13, int(17 * scale)), True)" + NL
    + "        drawn = []" + NL
    + "        for world_label in self.world_labels:" + NL
    + "            screen = project_point(self.mvp, world_label.point, width, height)" + NL
    + "            if screen is None:" + NL
    + "                continue" + NL
    + "            lines = world_label.text.splitlines()" + NL
    + "            if not lines:" + NL
    + "                continue" + NL
    + "            widest = max(label_font.size(line)[0] for line in lines)" + NL
    + "            label_height = len(lines) * int(22 * scale) + int(14 * scale)" + NL
    + "            drawn.append((pg.Rect(" + NL
    + "                int(screen[0] - widest * 0.5 - 10 * scale)," + NL
    + "                int(screen[1] - label_height * 0.5)," + NL
    + "                int(widest + 20 * scale), label_height), lines," + NL
    + "                world_label.color))" + NL
    + "        laid_out = self.layout_labels([item[0] for item in drawn])" + NL
    + "        # A touch more backing when decluttering, so whatever overlap" + NL
    + "        # survives still reads as layered rather than smeared." + NL
    + '        backing = 232 if self.lesson.label_layout == "declutter" else 210' + NL
    + "        for rect, (_, lines, colour) in zip(laid_out, drawn):" + NL
    + "            self.rounded_panel(surface, rect, (3, 10, 18, backing)," + NL
    + "                               (*colour, 190), int(7 * scale))" + NL
    + "            line_y = rect.y + int(7 * scale)" + NL
    + "            for line in lines:" + NL
    + "                rendered = label_font.render(line, True, colour)" + NL
    + "                surface.blit(rendered, (" + NL
    + "                    rect.centerx - rendered.get_width() // 2, line_y))" + NL
    + "                line_y += int(22 * scale)",
)

print("opt-in label decluttering added; default stays raw")
