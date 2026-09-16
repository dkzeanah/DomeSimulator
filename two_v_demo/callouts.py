"""Numbers that arrive with the words that say them.

When the narration says "two whole pine trees", the screen should say **2 TREES** at
that moment, hold it long enough to read, and let it go. When it walks through
"eight sections, eight wedges a section, six feet each", the screen should build that
as a column, a row at a time, each row landing on its words, and finish with the
total. That is what this module does, and it is the whole of what a good explainer's
number card is for: a figure broken into pieces small enough to take in while
someone is talking.

Two kinds of thing go on a chapter's ``callouts``:

:class:`Callout`  one figure: a value, a unit, a pictogram, a short note.
:class:`Tally`    a column of callouts that is an arithmetic chain: a starting
                  figure, rows that multiply, divide, add or subtract, and ``=``
                  rows that state a result.

The rules are the repository's rules.

* **No typed figures.** A callout's text is a template in the book's own token
  language -- ``{{method_a.whole_trees}}`` -- resolved by
  :func:`two_v_demo.book_tokens.resolve` on every render. The films and the book
  therefore quote the same function for the same figure, and an unknown token stops
  the build rather than printing a blank.
* **The arithmetic is checked.** Every tally's displayed rows are parsed back into
  numbers and the chain has to actually work out, to within the rounding the rows
  are shown at. A column that says 8 x 8 = 65 cannot be built.
* **Timing comes from the voice.** A callout names a *cue*, a phrase from its
  chapter's spoken text. When the narration was synthesized with sentence timings
  (:func:`audio.boundary_path`), the cue lands on its sentence's measured time;
  otherwise its place in the text is converted at the narrator's measured speaking
  rate, :data:`MEASURED_SPEECH`.
"""

from __future__ import annotations

import json
import math
import re
from dataclasses import dataclass, field
from functools import lru_cache
from pathlib import Path


# ----------------------------------------------------------------------
# What was measured
# ----------------------------------------------------------------------

MEASURED_SPEECH = {
    "characters": 80_562,
    "seconds": 4_991.1,
    "clips": 126,
    "rate": "+0%",
    "source": ("the cached chapter clips of three published films "
               "(why-wedges-no-sawmill-v2, eight-cuts-to-a-house, "
               "dome-from-scratch-geometry-to-pixels), measured with ffprobe "
               "against each chapter's spoken text"),
}
"""Characters of narration against seconds of audio, for the house voice.

Only used to place a cue in time when the narration has no sentence timings of its
own -- a live preview, or a clip cached before timings were recorded. It never puts
a figure on screen."""

SPEECH_DELAY = 0.55
"""Seconds of silence before a chapter's voice starts; the same figure
:mod:`two_v_demo.audio` builds the track with. Imported lazily below so the check
that they agree is a test, not a hope."""

FADE_IN = 0.35
FADE_OUT = 0.55
SLOTS = ("centre", "upper", "lower", "left", "right")
TONES = {
    "value": (255, 177, 62),
    "total": (83, 233, 152),
    "note": (61, 211, 255),
    "warn": (255, 96, 96),
}
OPERATORS = ("", "×", "÷", "+", "−", "=", "≈", "·")
"""Blank starts or annotates, times, divide, plus, minus, equals, approximately
(a conversion, not part of the chain), and a middle dot (a note on the row above)."""

CHAIN = {"×": lambda a, b: a * b, "÷": lambda a, b: a / b,
         "+": lambda a, b: a + b, "−": lambda a, b: a - b}


def characters_per_second(rate: str | None = None) -> float:
    """The house voice's speaking speed at an edge-tts rate such as ``-3%``."""
    base = MEASURED_SPEECH["characters"] / MEASURED_SPEECH["seconds"]
    if not rate:
        from .audio import DEFAULT_RATE
        rate = DEFAULT_RATE
    match = re.fullmatch(r"([+-]\d+)%", rate.strip())
    percent = float(match.group(1)) if match else 0.0
    return base * (1.0 + percent / 100.0)


# ----------------------------------------------------------------------
# The model
# ----------------------------------------------------------------------

@dataclass(frozen=True)
class Callout:
    """One figure on screen, for a few seconds, arriving with its words."""

    text: str
    """The figure itself, usually a token: ``{{tree.sections}}``."""
    unit: str = ""
    """What it counts, set smaller beside it: ``SECTIONS``. May hold tokens."""
    note: str = ""
    """A short line under it: ``six feet each``. May hold tokens."""
    icon: str = ""
    """A :mod:`two_v_demo.icons` key drawn beside the figure."""
    cue: str = ""
    """The phrase in the chapter's spoken text that brings it on."""
    at: float | None = None
    """Or a chapter progress from 0 to 1, when no words say it."""
    hold: float | None = 3.5
    """Seconds on screen once it has arrived; ``None`` holds it to the chapter's
    end."""
    slot: str = "centre"
    tone: str = "value"
    op: str = ""
    """The row's operator when it is part of a :class:`Tally`."""
    size: float = 1.0


@dataclass(frozen=True)
class Tally:
    """A column that builds an arithmetic chain, a row at a time."""

    rows: tuple[Callout, ...]
    title: str = ""
    slot: str = "right"
    hold: float | None = None
    """Seconds the finished column stays after its last row arrives; ``None``
    keeps it until the chapter ends, which is what a sum being talked about
    usually wants."""
    check: bool = True
    icon: str = ""
    """A :mod:`two_v_demo.icons` key drawn beside the column's title."""


@dataclass(frozen=True)
class Placed:
    """One callout, resolved and put on the chapter's clock."""

    item: Callout
    text: str
    unit: str
    note: str
    start: float
    end: float
    tally: Tally | None = None
    row: int = 0


# ----------------------------------------------------------------------
# Resolving and checking
# ----------------------------------------------------------------------

def resolve(template: str) -> str:
    """Fill in every ``{{token}}``. An unknown token is an error, never a blank."""
    if "{{" not in template:
        return template
    from .book_tokens import resolve as resolve_tokens
    return resolve_tokens(template, strict=True)


_NUMBER = re.compile(r"[-+]?\d[\d,]*(?:\.\d+)?|[-+]?\.\d+")


def number_in(text: str) -> tuple[float, int] | None:
    """The first number in a displayed string, and how many decimals it shows."""
    match = _NUMBER.search(text.replace("−", "-"))
    if not match:
        return None
    raw = match.group().replace(",", "")
    decimals = len(raw.split(".", 1)[1]) if "." in raw else 0
    return float(raw), decimals


def check_tally(tally: Tally) -> list[str]:
    """Problems with a tally's arithmetic, as sentences. Empty means it adds up.

    Rows are read the way the viewer reads them: the numbers shown, run through the
    operators shown, must give the results shown. Whole numbers here are counts --
    sections, wedges, trees -- so a chain of whole numbers has to come out exactly;
    8 x 8 = 65 is refused. Once a decimal enters the chain, a result may differ
    from it by one unit in its own last shown digit, because every input was rounded
    to fit the screen. After each ``=`` the chain carries on from the number shown,
    as a viewer doing the sum in their head would.
    """
    problems: list[str] = []
    value: float | None = None
    exact = True
    for index, row in enumerate(tally.rows):
        if row.op not in OPERATORS:
            problems.append(f"row {index + 1} has unknown operator {row.op!r}")
            continue
        if row.op in ("≈", "·"):
            continue
        shown = number_in(resolve(row.text))
        if shown is None:
            if row.op or value is None:
                problems.append(f"row {index + 1} ({row.text!r}) shows no number")
            continue
        number, decimals = shown
        if value is None or row.op == "":
            if value is None:
                value, exact = number, decimals == 0
            continue
        if row.op == "=":
            allowed = 1e-9 if exact else 10.0 ** (-decimals) + 1e-9
            if abs(value - number) > allowed:
                problems.append(
                    f"row {index + 1} says {number:g} but the rows above make "
                    f"{value:.6g}")
            value = number
            exact = exact and decimals == 0
            continue
        if row.op == "÷" and number == 0:
            problems.append(f"row {index + 1} divides by zero")
            continue
        value = CHAIN[row.op](value, number)
        exact = exact and decimals == 0 and float(value).is_integer()
    if value is None:
        problems.append("the tally has no numbers at all")
    return problems


# ----------------------------------------------------------------------
# Timing
# ----------------------------------------------------------------------

def spoken_text(chapter, speak_promise: bool = True) -> str:
    """Exactly what the voice reads, joined the way :mod:`audio` joins it."""
    body = " ".join(chapter.narration)
    return f"{chapter.promise}\n\n{body}" if speak_promise else body


def _normalise(text: str) -> str:
    return " ".join(text.lower().split())


def cue_position(spoken: str, cue: str) -> int | None:
    """Where a cue phrase starts in the spoken text, ignoring case and spacing."""
    haystack = _normalise(spoken)
    needle = _normalise(resolve(cue))
    index = haystack.find(needle)
    if index < 0:
        return None
    # Map the index in the normalised text back onto the original text.
    count = 0
    for original, character in enumerate(spoken):
        if count >= index:
            return original
        if not character.isspace() or (original > 0 and not spoken[original - 1].isspace()):
            count += 1
    return len(spoken)


def speech_timings(clip: Path | None) -> tuple[tuple[float, float, str], ...]:
    """(start, duration, text) for every sentence the voice service reported."""
    if clip is None:
        return ()
    from .audio import boundary_path
    path = boundary_path(Path(clip))
    return _read_timings(str(path), path.stat().st_mtime if path.is_file() else 0.0)


@lru_cache(maxsize=256)
def _read_timings(path: str, _mtime: float) -> tuple[tuple[float, float, str], ...]:
    rows: list[tuple[float, float, str]] = []
    try:
        lines = Path(path).read_text(encoding="utf-8").splitlines()
    except OSError:
        return ()
    for line in lines:
        line = line.strip()
        if not line:
            continue
        try:
            data = json.loads(line)
        except json.JSONDecodeError:
            continue
        offset = data.get("offset", data.get("Offset"))
        duration = data.get("duration", data.get("Duration"))
        text = data.get("text", data.get("Text", ""))
        if offset is None or duration is None:
            continue
        # edge-tts reports in ticks of a hundred nanoseconds.
        rows.append((float(offset) / 1e7, float(duration) / 1e7, str(text)))
    return tuple(rows)


def cue_seconds(spoken: str, position: int, speech_seconds: float,
                timings=()) -> float:
    """When the voice reaches a character, from the start of its audio."""
    if timings:
        cursor = 0
        # Where the character falls in the normalised text. A sentinel keeps the
        # space before it, which normalising the bare prefix would strip.
        spot = len(_normalise(spoken[:position] + "\x00")) - 1
        for start, duration, text in timings:
            found = _normalise(spoken).find(_normalise(text), cursor)
            if found < 0:
                continue
            length = max(1, len(_normalise(text)))
            if found <= spot < found + length:
                return start + duration * (spot - found) / length
            cursor = found + length
    return speech_seconds * position / max(1, len(spoken))


def schedule(chapter, chapter_seconds: float, speech_seconds: float | None = None,
             speak_promise: bool = True, timings=(),
             rate: str | None = None) -> tuple[Placed, ...]:
    """Every callout on a chapter, resolved, with its start and end in seconds."""
    from .audio import SPEECH_DELAY as delay

    spoken = spoken_text(chapter, speak_promise)
    if speech_seconds is None:
        speech_seconds = len(spoken) / characters_per_second(rate)
    latest = max(0.5, chapter_seconds - 0.25)

    def arrival(item: Callout) -> float:
        if item.at is not None:
            return max(0.0, min(latest, item.at * chapter_seconds))
        position = cue_position(spoken, item.cue) if item.cue else None
        if position is None:
            return 0.0
        return delay + cue_seconds(spoken, position, speech_seconds, timings)

    placed: list[Placed] = []
    for entry in getattr(chapter, "callouts", ()) or ():
        if isinstance(entry, Tally):
            starts = [arrival(row) for row in entry.rows]
            finish = latest if entry.hold is None else \
                min(latest, max(starts) + entry.hold)
            for index, (row, start) in enumerate(zip(entry.rows, starts)):
                placed.append(Placed(row, resolve(row.text), resolve(row.unit),
                                     resolve(row.note), start, finish, entry, index))
        else:
            start = arrival(entry)
            end = latest if entry.hold is None else min(latest, start + entry.hold)
            placed.append(Placed(entry, resolve(entry.text), resolve(entry.unit),
                                 resolve(entry.note), start, end))
    return tuple(placed)


def validate_chapter(chapter, speak_promise: bool = True) -> None:
    """Everything that would make a chapter's callouts wrong, refused up front."""
    from .icons import ICONS

    spoken = spoken_text(chapter, speak_promise)
    for entry in getattr(chapter, "callouts", ()) or ():
        items = entry.rows if isinstance(entry, Tally) else (entry,)
        if isinstance(entry, Tally):
            assert entry.rows, f"{chapter.slug}: an empty tally"
            assert entry.slot in SLOTS, (chapter.slug, entry.slot)
            if entry.check:
                problems = check_tally(entry)
                assert not problems, f"{chapter.slug}: " + "; ".join(problems)
            positions = [cue_position(spoken, row.cue) for row in entry.rows
                         if row.cue]
            known = [p for p in positions if p is not None]
            assert known == sorted(known), (
                f"{chapter.slug}: a tally's rows are cued out of spoken order")
        for item in items:
            for field_text in (item.text, item.unit, item.note):
                resolve(field_text)
            assert item.slot in SLOTS, (chapter.slug, item.slot)
            assert item.tone in TONES, (chapter.slug, item.tone)
            assert item.op in OPERATORS, (chapter.slug, item.op)
            assert not item.icon or item.icon in ICONS, (chapter.slug, item.icon)
            assert item.cue or item.at is not None, (
                f"{chapter.slug}: {item.text!r} has neither a cue nor a time")
            if item.cue:
                assert cue_position(spoken, item.cue) is not None, (
                    f"{chapter.slug}: cue {item.cue!r} is not in the narration")
            if not isinstance(entry, Tally):
                figure = resolve(item.text)
                assert not re.search(r"\d", item.text) or "{{" in item.text, (
                    f"{chapter.slug}: {item.text!r} types a figure; use a token")
                del figure
        if isinstance(entry, Tally):
            for row in entry.rows:
                if number_in(row.text) and "{{" not in row.text:
                    raise AssertionError(
                        f"{chapter.slug}: tally row {row.text!r} types a figure; "
                        "use a token")


# ----------------------------------------------------------------------
# Drawing
# ----------------------------------------------------------------------

def free_region(style: str, width: int, height: int) -> tuple[int, int, int, int]:
    """The part of the frame no card, panel or headline is using: x, y, w, h."""
    if style == "math":
        return (int(width * 0.03), int(height * 0.06), int(width * 0.50),
                int(height * 0.56))
    if style == "hype":
        return (int(width * 0.05), int(height * 0.06), int(width * 0.90),
                int(height * 0.58))
    return (int(width * 0.31), int(height * 0.13), int(width * 0.66),
            int(height * 0.48))


def _anchor(slot: str, region, block_w: int, block_h: int) -> tuple[int, int]:
    x, y, w, h = region
    centre_x = {"left": x + w * 0.22, "right": x + w * 0.78}.get(slot, x + w * 0.5)
    centre_y = {"upper": y + h * 0.22, "lower": y + h * 0.80}.get(slot, y + h * 0.45)
    return int(centre_x - block_w / 2), int(centre_y - block_h / 2)


def _alpha(now: float, start: float, end: float) -> float:
    if now < start or now > end + FADE_OUT:
        return 0.0
    rise = min(1.0, (now - start) / FADE_IN)
    fall = 1.0 if now <= end else max(0.0, 1.0 - (now - end) / FADE_OUT)
    return max(0.0, min(1.0, rise * rise * (3 - 2 * rise) * fall))


def _blit_faded(pg, surface, block, position, alpha: float) -> None:
    if alpha >= 0.999:
        surface.blit(block, position)
        return
    faded = block.copy()
    faded.fill((255, 255, 255, int(round(255 * alpha))),
               special_flags=pg.BLEND_RGBA_MULT)
    surface.blit(faded, position)


def _single(app, placed: Placed, scale: float):
    """One callout as a finished block: icon, figure, unit, note."""
    from .icons import draw_icon

    pg = app.pygame
    item = placed.item
    figure_font = app.font(max(24, int(96 * scale * item.size)), True)
    unit_font = app.font(max(14, int(38 * scale * item.size)), True)
    note_font = app.font(max(12, int(25 * scale * item.size)))
    tone = TONES[item.tone]
    figure = figure_font.render(placed.text, True, (244, 249, 252))
    unit = unit_font.render(placed.unit.upper(), True, tone) if placed.unit else None
    note = note_font.render(placed.note, True, (190, 206, 218)) if placed.note else None
    icon_size = int(figure.get_height() * 0.82) if item.icon else 0
    pad = int(22 * scale)
    gap = int(16 * scale)
    line_w = icon_size + (gap if icon_size else 0) + figure.get_width() + (
        gap + unit.get_width() if unit else 0)
    width = max(line_w, note.get_width() if note else 0) + 2 * pad + int(8 * scale)
    height = figure.get_height() + (note.get_height() + int(6 * scale) if note else 0) \
        + 2 * pad - int(10 * scale)
    block = pg.Surface((width, height), pg.SRCALPHA)
    app.rounded_panel(block, block.get_rect(), (3, 10, 18, 178), (*tone, 150),
                      int(14 * scale))
    pg.draw.rect(block, (*tone, 255),
                 pg.Rect(0, int(10 * scale), int(6 * scale), height - int(20 * scale)),
                 border_radius=int(3 * scale))
    x = pad + int(8 * scale)
    top = pad - int(6 * scale)
    if icon_size:
        draw_icon(pg, block, item.icon, (x + icon_size / 2,
                                         top + figure.get_height() / 2), icon_size)
        x += icon_size + gap
    block.blit(figure, (x, top))
    if unit:
        baseline = top + figure.get_height() - unit.get_height() - int(12 * scale)
        block.blit(unit, (x + figure.get_width() + gap, baseline))
    if note:
        block.blit(note, (pad + int(8 * scale), top + figure.get_height()))
    return block


def _column(app, rows: list[Placed], now: float, scale: float, room: int):
    """A tally as a column that grows a row at a time.

    The type is sized so the *finished* column fits the free region, and every row
    is measured up front so the width never jumps; but only the rows that have
    arrived take up height, so the panel grows as the sum is built instead of
    standing there half empty.
    """
    from .icons import draw_icon

    pg = app.pygame
    tally = rows[0].tally
    natural = (48 + 34 + 78 * len(rows)) * scale
    scale = scale * min(1.0, room / max(1.0, natural))
    arrived = [placed for placed in rows if now >= placed.start - FADE_IN]
    if not arrived:
        return None
    figure_font = app.font(max(16, int(58 * scale)), True)
    unit_font = app.font(max(11, int(27 * scale)), True)
    op_font = app.font(max(16, int(52 * scale)), True)
    kicker_font = app.font(max(10, int(20 * scale)), True)
    pad = int(22 * scale)
    gutter = int(52 * scale)
    rendered = []
    for placed in rows:
        tone = TONES["total" if placed.item.op == "=" else placed.item.tone]
        figure = figure_font.render(placed.text, True, (244, 249, 252))
        unit = unit_font.render(placed.unit.upper(), True, tone) if placed.unit else None
        op = op_font.render(placed.item.op, True, tone) if placed.item.op else None
        rendered.append((placed, figure, unit, op, tone))
    row_h = max(figure.get_height() for _, figure, *_ in rendered) + int(6 * scale)
    widest = max(figure.get_width() + (unit.get_width() + int(14 * scale) if unit else 0)
                 for _, figure, unit, _, _ in rendered)
    kicker = kicker_font.render(tally.title.upper(), True, (61, 211, 255)) \
        if tally.title else None
    icon_size = int(kicker_font.get_height() * 1.6) if tally.icon else 0
    head_line = max(kicker.get_height() if kicker else 0, icon_size)
    head = head_line + int(10 * scale) if head_line else 0
    title_w = icon_size + (int(10 * scale) if icon_size and kicker else 0) + (
        kicker.get_width() if kicker else 0)
    width = pad * 2 + max(gutter + widest, title_w)
    height = pad * 2 + head + row_h * len(arrived)
    block = pg.Surface((width, height), pg.SRCALPHA)
    app.rounded_panel(block, block.get_rect(), (3, 10, 18, 190), (57, 95, 114, 220),
                      int(14 * scale))
    y = pad
    if head:
        x = pad
        if icon_size:
            draw_icon(pg, block, tally.icon, (x + icon_size / 2, y + head_line / 2),
                      icon_size)
            x += icon_size + int(10 * scale)
        if kicker:
            block.blit(kicker, (x, y + (head_line - kicker.get_height()) // 2))
        y += head
    for placed, figure, unit, op, tone in rendered[:len(arrived)]:
        alpha = _alpha(now, placed.start, placed.end)
        if alpha <= 0.0:
            y += row_h
            continue
        row = pg.Surface((width, row_h), pg.SRCALPHA)
        if placed.item.op == "=":
            pg.draw.line(row, (*tone, 220), (pad, 1), (width - pad, 1),
                         max(1, int(2 * scale)))
        if op:
            row.blit(op, (pad + (gutter - op.get_width()) // 2,
                          (row_h - op.get_height()) // 2))
        row.blit(figure, (pad + gutter, (row_h - figure.get_height()) // 2))
        if unit:
            row.blit(unit, (pad + gutter + figure.get_width() + int(14 * scale),
                            (row_h + figure.get_height()) // 2 - unit.get_height()
                            - int(8 * scale)))
        _blit_faded(pg, block, row, (0, y), alpha)
        y += row_h
    return block


def _world_icons(app, surface, width: int, height: int) -> None:
    from .icons import draw_icon
    from .render_kit import project_point

    for pinned in getattr(app, "world_icons", ()) or ():
        screen = project_point(app.mvp, pinned.point, width, height)
        if screen is None:
            continue
        # An icon that is aimed at something turns to face it on screen,
        # wherever the camera happens to be: a saw points at the trunk it cuts.
        mirror = False
        toward = getattr(pinned, "toward", None)
        if toward is not None:
            aim = project_point(app.mvp, toward, width, height)
            mirror = aim is not None and aim[0] < screen[0]
        draw_icon(app.pygame, surface, pinned.key, screen,
                  pinned.size * height / 1080.0, pinned.color, pinned.alpha,
                  pinned.angle, mirror=mirror)


def draw_extras(app, surface, width: int, height: int, style: str) -> None:
    """Pinned icons, then the chapter's callouts, onto a finished overlay.

    Called by the renderer after its own card, panel or headline is drawn. A lesson
    with no icons and no callouts is untouched, which is what keeps every published
    film re-rendering exactly as it shipped.
    """
    _world_icons(app, surface, width, height)
    chapter = app.chapters[app.chapter_index]
    if not getattr(chapter, "callouts", ()):
        return
    index = app.chapter_index
    seconds = app.chapter_durations[index]
    now = app.chapter_progress * seconds
    speech = getattr(app, "speech_durations", None)
    clips = getattr(app, "speech_clips", None)
    timings = speech_timings(clips[index]) if clips else ()
    placed = schedule(chapter, seconds,
                      speech[index] if speech else None,
                      getattr(app, "speak_promise", True), timings,
                      getattr(app.lesson, "voice_rate", None))
    free = getattr(app, "overlay_free", None)
    if free is not None:
        # A phone frame: callouts go in the picture's own space, set for a phone.
        scale = width / 1080.0
        region = free.as_int()
    else:
        scale = min(width / 1600.0, height / 900.0)
        region = free_region(style, width, height)
    pg = app.pygame

    def squeeze(block):
        # Compress a block wider or taller than the space it has -- which only a
        # narrow frame produces -- rather than let it run off the picture.
        if free is None:
            return block
        factor = min(1.0, region[2] / max(1, block.get_width()),
                     region[3] / max(1, block.get_height()))
        if factor >= 0.999:
            return block
        return pg.transform.smoothscale(block, (max(1, int(block.get_width() * factor)),
                                                max(1, int(block.get_height() * factor))))

    def place(slot: str, block) -> tuple[int, int]:
        # Anchored by slot, then kept inside the free region: a block that ran off
        # the top of the frame is the fault the first stills of this engine showed.
        x, y = _anchor(slot, region, block.get_width(), block.get_height())
        rx, ry, rw, rh = region
        x = max(rx, min(x, rx + rw - block.get_width()))
        y = max(ry, min(y, ry + rh - block.get_height()))
        return x, y

    columns: dict[int, list[Placed]] = {}
    for item in placed:
        if item.tally is not None:
            columns.setdefault(id(item.tally), []).append(item)
            continue
        alpha = _alpha(now, item.start, item.end)
        if alpha <= 0.0:
            continue
        block = squeeze(_single(app, item, scale))
        x, y = place(item.item.slot, block)
        rise = int((1.0 - min(1.0, (now - item.start) / FADE_IN)) * 16 * scale)
        _blit_faded(pg, surface, block, (x, y + rise), alpha)

    for rows in columns.values():
        visible = max(_alpha(now, row.start, row.end) for row in rows)
        if visible <= 0.0:
            continue
        block = _column(app, rows, now, scale, region[3])
        if block is None:
            continue
        block = squeeze(block)
        x, y = place(rows[0].tally.slot, block)
        # The panel behind the rows arrives with the first and leaves with the last.
        frame = min(_alpha(now, rows[0].start, rows[0].end), 1.0)
        _blit_faded(pg, surface, block, (x, y), max(frame, visible))


def validate_callouts() -> None:
    """The engine's own proofs, independent of any lesson."""
    from . import audio

    assert audio.SPEECH_DELAY == SPEECH_DELAY, "callouts and the voice track disagree"
    good = Tally((Callout("8", op=""), Callout("8", op="×"),
                  Callout("64", op="=")))
    assert not check_tally(good), check_tally(good)
    bad = Tally((Callout("8"), Callout("8", op="×"), Callout("65", op="=")))
    assert check_tally(bad), "a wrong total passed"
    rounded = Tally((Callout("2"), Callout("24", op="×"),
                     Callout("0.28", op="×"), Callout("13.4", op="=")))
    assert not check_tally(rounded), check_tally(rounded)
    assert number_in("1,234.5 sq ft") == (1234.5, 1)
    assert 14.0 < characters_per_second("-3%") < 17.0
    text = "It will take me two  whole pine trees to do it."
    assert cue_position(text, "two whole pine") == text.index("two")
    # Sentence timings, when present, beat the estimate.
    timed = cue_seconds("One. Two three.", 5, 10.0,
                        ((0.0, 1.0, "One."), (2.0, 3.0, "Two three.")))
    assert abs(timed - 2.0) < 1e-9, timed
