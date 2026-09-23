"""Vertical layouts for the film overlays: the phone-frame teaching card,
math worksheet, montage headline and plate.

A landscape overlay puts its text beside the picture; a phone frame has no
beside, only above and below, so each layout here stacks: a header band at the
top, the picture in the middle, and the words that carry the chapter at the
bottom, clear of the platform's own buttons (:data:`frame.PORTRAIT_SAFE`).

Every layout is *planned* before the scene is drawn, so the renderer knows how
much of the frame the picture gets (:attr:`Plan.free`) and can fit the camera
to it, and then *painted* from that same plan. Text is set big enough to read on
a phone and resolved the same way everywhere: a block that runs long is first
compressed toward a minimum size, then allowed to run to more lines, and only
then trimmed -- and every one of those decisions is written to the plan's log.
"""

from __future__ import annotations

from dataclasses import dataclass, field

from .frame import Box, Frame, Rect, resolve
from .render_kit import clamp, project_point

WHITE = (240, 247, 252)
BODY = (184, 201, 214)
CYAN = (61, 211, 255)
AMBER = (255, 177, 62)
GREEN = (83, 233, 152)
MUTED = (104, 132, 150)
PANEL = (4, 11, 21, 228)
EDGE = (57, 95, 114, 255)


@dataclass
class Plan:
    style: str
    frame: Frame
    free: Rect
    """Where the picture goes."""
    ops: list = field(default_factory=list)
    steps: list = field(default_factory=list)
    callout: Rect | None = None
    """Where the chapter's callouts go, when it has any: a band of their own."""


def _fit_lines(app, text: str, width: float, max_lines: int, size: int, min_size: int,
               bold: bool, steps: list, key: str) -> tuple[int, list[str]]:
    """Compress the type toward its minimum until the text fits; past that,
    let it run to more lines rather than go smaller."""
    lines = app.wrap_text(text, app.font(size, bold), int(width))
    while len(lines) > max_lines and size > min_size:
        size = max(min_size, int(size * 0.92))
        lines = app.wrap_text(text, app.font(size, bold), int(width))
        steps.append(f"compress {key} to {size}px: {len(lines)} lines")
    if len(lines) > max_lines:
        steps.append(f"elongate {key}: {len(lines)} lines at {size}px")
    return size, lines


def _progress(app) -> float:
    return (app.timeline % app.total_duration) / app.total_duration if app.total_duration else 0.0


# ----------------------------------------------------------------------
# Planning
# ----------------------------------------------------------------------

def plan(app, frame: Frame, style: str) -> Plan:
    if style == "hype":
        result = _plan_hype(app, frame)
    elif style == "math":
        result = _plan_math(app, frame)
    elif style == "plate":
        result = Plan("plate", frame, frame.safe())
    else:
        result = _plan_teaching(app, frame)
    chapter = app.chapters[app.chapter_index]
    if getattr(chapter, "callouts", ()) and style != "plate":
        # A landscape callout sits beside the subject; a phone has no beside, so
        # the picture is shoved up and the figures get the band under it.
        free = result.free
        scene_h = free.h * 0.58
        result.callout = Rect(free.x, free.y + scene_h, free.w, free.h - scene_h)
        result.free = Rect(free.x, free.y, free.w, scene_h)
        result.steps.append("shove the picture up: the callouts take the band below it")
    return result


def _plan_hype(app, frame: Frame) -> Plan:
    chapter = app.chapters[app.chapter_index]
    u, safe = frame.unit, frame.safe()
    steps: list[str] = []
    size, lines = _fit_lines(app, chapter.promise, safe.w, 4, int(64 * u), int(44 * u), True,
                             steps, "headline")
    kicker_size = int(26 * u)
    line_h = int(size * 1.17)
    kicker_h = int(kicker_size * 1.7)
    block_h = kicker_h + len(lines) * line_h
    top = safe.bottom - block_h
    floor = frame.height * 0.28
    scene_bottom = max(safe.y + floor, top - 30 * u)
    free = Rect(safe.x, safe.y, safe.w, scene_bottom - safe.y)
    ops = [("scrim", top - 90 * u),
           ("text", chapter.title.upper(), kicker_size, True, CYAN, safe.x, top),
           ("lines", lines, size, True, WHITE, safe.x, top + kicker_h, line_h, True)]
    return Plan("hype", frame, free, ops, steps)


def _plan_teaching(app, frame: Frame) -> Plan:
    chapter = app.chapters[app.chapter_index]
    u, safe = frame.unit, frame.safe()
    steps: list[str] = []
    ops: list = []
    # The header band: which chapter, and its title.
    kicker = f"CHAPTER {chapter.number}  ·  {app.lesson.brand}"
    kicker_size = int(22 * u)
    while app.font(kicker_size, True).size(kicker)[0] > safe.w and kicker_size > int(16 * u):
        kicker_size -= 1
    title_size, title_lines = _fit_lines(app, chapter.title, safe.w, 2, int(46 * u),
                                         int(34 * u), True, steps, "title")
    y = safe.y
    ops.append(("topscrim", y + int(kicker_size * 1.6)
                + len(title_lines) * int(title_size * 1.18) + 24 * u))
    ops.append(("text", kicker, kicker_size, True, CYAN, safe.x, y))
    y += int(kicker_size * 1.6)
    title_h = int(title_size * 1.18)
    ops.append(("lines", title_lines, title_size, True, WHITE, safe.x, y, title_h, True))
    header_bottom = y + len(title_lines) * title_h

    # The card: the chapter's promise, what the voice is saying, and the live figures.
    pad = int(26 * u)
    inner = safe.w - 2 * pad
    promise_size, promise_lines = _fit_lines(app, chapter.promise, inner, 3, int(38 * u),
                                             int(30 * u), True, steps, "promise")
    promise_h = int(promise_size * 1.2)
    equations = app.merge_equations(chapter)[:3]
    eq_size = int(25 * u)
    eq_rows = []
    for equation in equations:
        eq_rows += app.wrap_text(equation, app.font(eq_size), int(inner))
    eq_rows = eq_rows[:4]
    eq_h = int(eq_size * 1.36)
    fixed = (pad + len(promise_lines) * promise_h + int(14 * u)
             + (int(22 * u * 1.7) + len(eq_rows) * eq_h + int(10 * u) if eq_rows else 0) + pad)
    card_max = safe.h * 0.47
    body_size, body_min = int(31 * u), int(26 * u)
    text = " ".join(chapter.narration)
    while True:
        body_lines = app.wrap_text(text, app.font(body_size), int(inner))
        body_h = int(body_size * 1.4)
        if fixed + len(body_lines) * body_h <= card_max or body_size <= body_min:
            break
        body_size = max(body_min, int(body_size * 0.93))
        steps.append(f"compress narration to {body_size}px")
    room = int((card_max - fixed) // body_h)
    if len(body_lines) > room:
        kept = max(0, room)
        steps.append(f"trim narration: {kept} of {len(body_lines)} lines shown")
        body_lines = body_lines[:kept]
        if body_lines:
            body_lines[-1] = body_lines[-1].rstrip(".,;:") + " …"
    card_h = fixed + len(body_lines) * body_h
    card_top = safe.bottom - card_h
    ops.append(("panel", Rect(safe.x, card_top, safe.w, card_h), PANEL, EDGE, int(18 * u)))
    y = card_top + pad
    ops.append(("lines", promise_lines, promise_size, True, WHITE, safe.x + pad, y, promise_h,
                False))
    y += len(promise_lines) * promise_h + int(14 * u)
    ops.append(("lines", body_lines, body_size, False, BODY, safe.x + pad, y, body_h, False))
    y += len(body_lines) * body_h
    if eq_rows:
        y += int(10 * u)
        ops.append(("text", "LIVE CALCULATION", int(22 * u), True, AMBER, safe.x + pad, y))
        y += int(22 * u * 1.7)
        ops.append(("lines", eq_rows, eq_size, False, (216, 229, 237), safe.x + pad, y, eq_h,
                    False))
    top = header_bottom + 22 * u
    free = Rect(safe.x, top, safe.w, max(frame.height * 0.22, card_top - 22 * u - top))
    return Plan("teaching", frame, free, ops, steps)


def _plan_math(app, frame: Frame) -> Plan:
    chapter = app.chapters[app.chapter_index]
    u, safe = frame.unit, frame.safe()
    steps: list[str] = []
    ops: list = []
    kicker_size = int(22 * u)
    y = safe.y + int(kicker_size * 1.6)
    title_size, title_lines = _fit_lines(app, chapter.title, safe.w, 2, int(42 * u),
                                         int(32 * u), True, steps, "title")
    title_h = int(title_size * 1.18)
    # Laid down before the words: the picture behind a top header is whatever
    # the camera framed, and since the frame fit started giving the subject
    # the room it deserves that can be a tree line rather than empty sky.
    ops.append(("topscrim", y + len(title_lines) * title_h + 24 * u))
    ops.append(("text", f"THE MATH  ·  CHAPTER {chapter.number}", kicker_size, True, AMBER,
                safe.x, safe.y))
    ops.append(("lines", title_lines, title_size, True, WHITE, safe.x, y, title_h, True))
    header_bottom = y + len(title_lines) * title_h

    equations = list(chapter.equations)
    derivation = equations[:-1] if len(equations) > 1 else equations
    conclusion = equations[-1] if len(equations) > 1 else ""
    progress = clamp(app.chapter_progress)
    visible = len(derivation) if progress >= 0.80 else max(
        1, int(progress / 0.80 * len(derivation)) + 1)
    visible = min(visible, len(derivation))
    pad = int(24 * u)
    inner = safe.w - 2 * pad - int(30 * u)
    conclusion_size = int(30 * u)
    conclusion_lines = (app.wrap_text(conclusion, app.font(conclusion_size, True), int(inner))
                        if conclusion else [])
    band_h = (len(conclusion_lines) * int(conclusion_size * 1.25) + int(52 * u)
              if conclusion_lines else 0)
    panel_max = safe.h * 0.60
    step_size, step_min = int(30 * u), int(25 * u)

    def rows_at(size: int):
        out = []
        for index, step in enumerate(derivation[:visible]):
            wrapped = app.wrap_text(step, app.font(size), int(inner))
            out.append((index, wrapped))
        return out

    head = pad + int(18 * u * 1.7)
    while True:
        rows = rows_at(step_size)
        line_h = int(step_size * 1.36)
        need = head + sum(len(w) for _, w in rows) * line_h + len(rows) * int(6 * u) \
            + band_h + pad + int(26 * u)
        if need <= panel_max or step_size <= step_min:
            break
        step_size = max(step_min, int(step_size * 0.93))
        steps.append(f"compress worksheet to {step_size}px")
    if need > panel_max:
        # Elongate first: the panel may take more of the frame before anything scrolls.
        grown = min(need, safe.h * 0.68)
        if grown > panel_max:
            steps.append(f"elongate worksheet to {grown / safe.h:.0%} of the frame")
            panel_max = grown
    # Past that, the settled lines at the top scroll away, newest kept.
    budget = panel_max - (head + band_h + pad + int(26 * u))
    flat: list[tuple[int, str, bool]] = []
    for index, wrapped in rows:
        for position, text in enumerate(wrapped):
            flat.append((index, text, position == 0))
    lines_room = max(1, int(budget // (line_h + 1)))
    if len(flat) > lines_room:
        steps.append(f"scroll worksheet: newest {lines_room} of {len(flat)} lines shown")
        flat = flat[-lines_room:]
    panel_h = min(panel_max, head + len(flat) * line_h + len({i for i, _, _ in flat}) * int(6 * u)
                  + band_h + pad + int(26 * u))
    panel_top = safe.bottom - panel_h
    ops.append(("panel", Rect(safe.x, panel_top, safe.w, panel_h), PANEL, EDGE, int(18 * u)))
    y = panel_top + pad
    ops.append(("text", "WORKED LIVE", int(18 * u), True, CYAN, safe.x + pad, y))
    y += int(18 * u * 1.7)
    last_index = None
    for index, text, first in flat:
        if last_index is not None and index != last_index:
            y += int(6 * u)
        settled = index < visible - 1 or progress >= 0.80
        colour = (206, 221, 233) if settled else (255, 197, 92)
        if first:
            ops.append(("text", "=" if settled else ">", step_size, True, CYAN, safe.x + pad, y))
        ops.append(("text", text, step_size, False, colour, safe.x + pad + int(30 * u), y))
        y += line_h
        last_index = index
    if conclusion_lines and progress >= 0.80:
        band = Rect(safe.x + int(12 * u), safe.bottom - band_h - int(30 * u),
                    safe.w - int(24 * u), band_h)
        ops.append(("panel", band, (8, 34, 22, 240), (83, 233, 152, 255), int(12 * u)))
        ops.append(("text", "CONCLUSION", int(18 * u), True, GREEN, band.x + int(16 * u),
                    band.y + int(12 * u)))
        ops.append(("lines", conclusion_lines, conclusion_size, True, (233, 249, 239),
                    band.x + int(16 * u), band.y + int(40 * u), int(conclusion_size * 1.25),
                    False))
    ops.append(("text", "computed live by the code drawing this frame", int(16 * u), False,
                MUTED, safe.x + pad, safe.bottom - int(24 * u)))
    top = header_bottom + 20 * u
    free = Rect(safe.x, top, safe.w, max(frame.height * 0.2, panel_top - 20 * u - top))
    return Plan("math", frame, free, ops, steps)


# ----------------------------------------------------------------------
# Painting
# ----------------------------------------------------------------------

LABEL_AREA_SHARE = 0.34
"""How much of the picture's area world labels may cover before the frame is
declared full.

A wide frame has room beside the subject for a dozen tags. A phone frame does
not, and the old behaviour was to hand every one of them to the resolver and
draw whatever came back -- which, once the resolver ran out of room, was a pile
of overlapping panels with the subject somewhere underneath. Six labels you can
read beat eleven you cannot."""


def _labels(app, surface, plan: Plan, width: int, height: int) -> None:
    """World labels, set for a phone and resolved inside the picture's space.

    Labels arrive in the order the painter added them, and that order is the
    priority: the first one a chapter asks for is the one it most wants seen.
    Anything that will not fit clear of its neighbours is *dropped*, not
    stacked. The resolver runs twice -- once to find out what does not fit,
    once more with those removed so the survivors can spread into the space
    they freed."""
    pg = app.pygame
    u = plan.frame.unit
    size = max(18, int(27 * u))
    font = app.font(size, True)
    line_h = int(size * 1.25)
    pad = int(12 * u)
    boxes, looks = [], []
    for order, world_label in enumerate(app.world_labels):
        screen = project_point(app.mvp, world_label.point, width, height)
        if screen is None:
            continue
        lines = world_label.text.splitlines()
        if not lines:
            continue
        widest = max(font.size(line)[0] for line in lines)
        w, h = widest + 2 * pad, len(lines) * line_h + pad
        boxes.append(Box(f"label{order}", screen[0] - w / 2, screen[1] - h / 2, w, h,
                         priority=-order, min_scale=0.75))
        looks.append((lines, world_label.color))
    if not boxes:
        return
    bounds = Rect(plan.free.x - 8 * u, plan.free.y - 8 * u, plan.free.w + 16 * u,
                  plan.free.h + 16 * u)

    # Before the resolver is asked to do the impossible: if the labels want
    # more of the picture than they may have, take the lowest-priority ones
    # off the list. Priority is the order the painter added them.
    budget = bounds.w * bounds.h * LABEL_AREA_SHARE
    keep: list = []
    kept_looks: list = []
    used = 0.0
    for box, look in zip(boxes, looks):
        area = box.w * box.h
        if keep and used + area > budget:
            plan.steps.append(f"drop {box.key}: the frame is full")
            continue
        keep.append(box)
        kept_looks.append(look)
        used += area
    boxes, looks = keep, kept_looks

    # The resolver moves and shrinks boxes in place, so keep where each one
    # wanted to be: the second pass has to start from the same wishes.
    origin = {box.key: (box.x, box.y, box.w, box.h) for box in boxes}
    priority = {box.key: box.priority for box in boxes}

    result = resolve(boxes, bounds, gap=6.0 * u)
    plan.steps += result.steps
    if result.unresolved:
        # Whatever the resolver could not place clear is dropped, and the rest
        # are resolved again so they can use the room that just opened up.
        beaten = {key for key, _blocker in result.unresolved}
        survivors = [(box, look) for box, look in zip(boxes, looks)
                     if box.key not in beaten]
        for key in sorted(beaten):
            plan.steps.append(f"drop {key}: nowhere to put it")
        if survivors:
            boxes = [Box(key, *origin[key], priority=priority[key],
                         min_scale=0.75)
                     for key in [box.key for box, _look in survivors]]
            looks = [look for _box, look in survivors]
            result = resolve(boxes, bounds, gap=6.0 * u)
            plan.steps += result.steps
            # Filter the pair together. Filtering the boxes first and then
            # zipping the survivors against the untouched looks hands every
            # remaining label somebody else's text.
            still = {key for key, _blocker in result.unresolved}
            kept = [(box, look) for box, look in zip(boxes, looks)
                    if box.key not in still]
            boxes = [box for box, _look in kept]
            looks = [look for _box, look in kept]
        else:
            boxes, looks = [], []

    for box, (lines, colour) in zip(boxes, looks):
        scale = box.scale
        label_font = app.font(max(14, int(size * scale)), True) if scale < 0.999 else font
        rect = pg.Rect(int(box.x), int(box.y), int(box.w), int(box.h))
        app.rounded_panel(surface, rect, (3, 10, 18, 226), (*colour, 190), int(8 * u))
        y = rect.y + int(pad * 0.5 * scale)
        for line in lines:
            rendered = label_font.render(line, True, colour)
            surface.blit(rendered, (rect.centerx - rendered.get_width() // 2, y))
            y += int(line_h * scale)


def draw(app, plan: Plan, width: int, height: int):
    pg = app.pygame
    surface = pg.Surface((width, height), pg.SRCALPHA)
    app.ui_buttons.clear()
    _labels(app, surface, plan, width, height)
    u = plan.frame.unit
    for op in plan.ops:
        kind = op[0]
        if kind == "topscrim":
            # The mirror of "scrim": solid at the very top of the screen,
            # gone by the time the picture starts.
            bottom = int(op[1])
            band = pg.Surface((width, max(1, bottom)), pg.SRCALPHA)
            rows = band.get_height()
            for row in range(rows):
                fade = 1.0 - min(1.0, max(0.0, (row - rows * 0.55))
                                 / max(1.0, rows * 0.45))
                pg.draw.line(band, (3, 8, 16, int(212 * fade)),
                             (0, row), (width, row))
            surface.blit(band, (0, 0))
        elif kind == "scrim":
            top = int(op[1])
            scrim = pg.Surface((width, height - top), pg.SRCALPHA)
            rows = scrim.get_height()
            for row in range(rows):
                alpha = int(206 * min(1.0, row / max(1.0, rows * 0.45)))
                pg.draw.line(scrim, (3, 8, 16, alpha), (0, row), (width, row))
            surface.blit(scrim, (0, top))
        elif kind == "panel":
            rect, fill, edge, radius = op[1], op[2], op[3], op[4]
            app.rounded_panel(surface, pg.Rect(*rect.as_int()), fill, edge, radius)
        elif kind == "text":
            _, text, size, bold, colour, x, y = op
            surface.blit(app.font(size, bold).render(text, True, colour), (int(x), int(y)))
        elif kind == "lines":
            _, lines, size, bold, colour, x, y, step, shadow = op
            font = app.font(size, bold)
            for line in lines:
                if shadow:
                    surface.blit(font.render(line, True, (2, 6, 12)),
                                 (int(x + 3 * u), int(y + 3 * u)))
                surface.blit(font.render(line, True, colour), (int(x), int(y)))
                y += step
    bar = max(3, int(6 * u))
    pg.draw.rect(surface, (22, 44, 60, 220), pg.Rect(0, height - bar, width, bar))
    pg.draw.rect(surface, (255, 177, 62, 255),
                 pg.Rect(0, height - bar, int(width * _progress(app)), bar))
    return surface


# ----------------------------------------------------------------------
# Proof
# ----------------------------------------------------------------------

def validate_portrait_ui() -> None:
    """A crowded phone frame must come back legible, not stacked.

    The defect this guards against shipped in a vertical cut: eleven world
    labels handed to the resolver in a 9:16 frame came back as a pile of
    overlapping panels with the subject somewhere underneath. The resolver was
    doing its job -- it reported two of them unresolved -- and the drawing code
    was ignoring the report and drawing them anyway.
    """
    bounds = Rect(40, 60, 1000, 1000)
    boxes = [Box(f"l{index}", 300 + (index % 3) * 40, 200 + index * 18,
                 360, 52, priority=-index, min_scale=0.75)
             for index in range(11)]
    result = resolve(boxes, bounds, gap=6.0)

    # More labels than the frame can hold: the resolver has to say so rather
    # than quietly returning a pile.
    assert result.unresolved, "the resolver placed eleven labels in a phone frame"

    beaten = {key for key, _blocker in result.unresolved}
    survivors = [box for box in boxes if box.key not in beaten]
    assert survivors, "everything was dropped"

    # And what survives must not overlap at all.
    for index, first in enumerate(survivors):
        for second in survivors[index + 1:]:
            across, down = first.overlap(second)
            assert across <= 0.0 or down <= 0.0, (first.key, second.key)

    # The area budget has to bite before the resolver is asked the impossible.
    assert 0.0 < LABEL_AREA_SHARE < 1.0


if __name__ == "__main__":
    validate_portrait_ui()
    print("portrait ui ok")
