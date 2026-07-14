"""
2D overlay widgets for the dome creator, rendered with pygame fonts into
RGBA surfaces. The main app uploads these surfaces as GL textures and
composites them over the 3D view.
"""

from __future__ import annotations

from dataclasses import dataclass
import math
from typing import Callable

import pygame

BG = (14, 18, 22, 215)
BG_SOFT = (14, 18, 22, 170)
HEADER = (120, 200, 255)
TEXT = (225, 230, 235)
DIM = (150, 158, 165)
VALUE = (255, 220, 130)
SELECT_BG = (40, 80, 110, 235)
ACCENT = (255, 170, 60)
GOOD = (140, 230, 150)


@dataclass
class MenuItem:
    label: str
    kind: str                               # "header", "choice", "action"
    value: Callable[[], str] | None = None  # current value as display text
    change: Callable[[int], None] | None = None  # left/right delta
    activate: Callable[[], str | None] | None = None  # enter; returns message
    hint: str = ""


class Fonts:
    def __init__(self) -> None:
        pygame.font.init()
        self.body = pygame.font.SysFont("consolas,couriernew,monospace", 15)
        self.small = pygame.font.SysFont("consolas,couriernew,monospace", 13)
        self.title = pygame.font.SysFont(
            "consolas,couriernew,monospace", 17, bold=True
        )


def render_menu(
    fonts: Fonts,
    items: list[MenuItem],
    selected: int,
    pages: list[str] | None = None,
    active_page: int = 0,
) -> tuple[pygame.Surface, dict]:
    """Returns (surface, hit_map). hit_map: {"tabs": [(page, Rect)],
    "rows": [(item_index, Rect, arrows_bool)]} in panel-local coords."""
    width = 380
    row_h = 22
    header_h = 30
    tabs_h = 22 if pages else 0
    pad = 10
    height = pad * 2 + header_h + tabs_h + row_h * len(items) + 24
    hit_map: dict = {"tabs": [], "rows": []}

    surf = pygame.Surface((width, height), pygame.SRCALPHA)
    surf.fill(BG)
    pygame.draw.rect(surf, (70, 130, 170, 255), surf.get_rect(), 1)

    surf.blit(
        fonts.title.render("DOME CREATOR", True, HEADER), (pad, pad)
    )
    y = pad + header_h

    if pages:
        x = pad
        for i, name in enumerate(pages):
            label = f"{name}"
            color = ACCENT if i == active_page else DIM
            rendered = fonts.body.render(label, True, color)
            tab_rect = pygame.Rect(x - 3, y - 2,
                                   rendered.get_width() + 6, 20)
            if i == active_page:
                pygame.draw.rect(surf, SELECT_BG, tab_rect)
            surf.blit(rendered, (x, y))
            hit_map["tabs"].append((i, tab_rect))
            x += rendered.get_width() + 14
        y += tabs_h

    for i, item in enumerate(items):
        if item.kind == "header":
            pygame.draw.line(surf, (60, 90, 110), (pad, y + row_h // 2),
                             (width - pad, y + row_h // 2), 1)
            label = fonts.small.render(f" {item.label} ", True, HEADER)
            surf.blit(label, (pad + 8, y + row_h // 2 - 8))
            y += row_h
            continue

        row_rect = pygame.Rect(pad - 4, y, width - pad * 2 + 8, row_h)
        hit_map["rows"].append((i, row_rect))
        if i == selected:
            pygame.draw.rect(surf, SELECT_BG, row_rect)
            surf.blit(fonts.body.render(">", True, ACCENT), (pad - 2, y + 2))

        surf.blit(fonts.body.render(item.label, True, TEXT), (pad + 12, y + 2))
        if item.value is not None:
            value_text = f"< {item.value()} >" if item.kind == "choice" \
                else item.value()
            rendered = fonts.body.render(value_text, True, VALUE)
            surf.blit(rendered, (width - pad - rendered.get_width() - 2, y + 2))
        elif item.kind == "action":
            rendered = fonts.body.render("[CLICK]", True, GOOD)
            surf.blit(rendered, (width - pad - rendered.get_width() - 2, y + 2))
        y += row_h

    tip = fonts.small.render(
        "Click: next / apply    Right-click: previous", True, DIM
    )
    surf.blit(tip, (pad, height - 20))
    return surf, hit_map


def render_stats(fonts: Fonts, stats: dict) -> pygame.Surface:
    lines: list[tuple[str, tuple]] = []

    def add(text: str, color=TEXT) -> None:
        lines.append((text, color))

    add("LIVE MATERIAL BREAKDOWN", HEADER)
    add(f"{stats['frequency']}V  r={stats['radius']:.1f}m  "
        f"h={stats['height']:.1f}m", DIM)
    add(f"Floor {stats['floor_area']:.1f} m2   "
        f"Shell {stats['surface_area']:.1f} m2", DIM)
    add("")
    add("FRAME", HEADER)
    add(f" Struts {stats['strut_count']} pcs  "
        f"{stats['strut_total_len']:.1f} m")
    for label, length, count in stats["strut_classes"][:6]:
        add(f"   {label}: {count:3d} x {length:.2f} m", DIM)
    if stats.get("trunk_stock_count"):
        add(f" Trunks {stats['trunk_stock_count']} x "
            f"{stats['trunk_stock_length'] * 3.28084:.1f} ft", DIM)
        if stats.get("trunk_too_short"):
            add(" Longest strut exceeds stock", ACCENT)
    add(f" Hubs {stats['hub_count']} pcs")
    add(f" {stats['frame_weight'] + stats['hub_weight']:,.0f} kg    "
        f"${stats['frame_cost'] + stats['hub_cost']:,.0f}", VALUE)
    add("")
    add("PANELS", HEADER)
    for name, g in sorted(stats["panel_groups"].items()):
        add(f" {name:<17}{g['count']:3d}  {g['area']:6.1f} m2", DIM)
    add(f" {stats['panel_weight']:,.0f} kg    "
        f"${stats['panel_cost']:,.0f}", VALUE)
    if stats["solar_watts"] > 0:
        add(f" Solar {stats['solar_watts'] / 1000.0:.2f} kW", GOOD)
    add("")
    if stats["layer_rows"]:
        add("LAYERS", HEADER)
        for name, area, weight, cost in stats["layer_rows"]:
            add(f" {name:<17}{weight:6.0f} kg  ${cost:,.0f}", DIM)
        add(f" {stats['layer_weight']:,.0f} kg    "
            f"${stats['layer_cost']:,.0f}", VALUE)
        add("")
    add("FOUNDATION", HEADER)
    add(f" {stats['foundation_name']:<16} "
        f"{stats['foundation_weight']:,.0f} kg", DIM)
    add(f" ${stats['foundation_cost']:,.0f}", VALUE)
    add("")
    if stats["prop_count"] or stats["wall_count"] \
            or stats["assigned_sections"]:
        add("WORKSHOP FIT-OUT", HEADER)
        if stats["assigned_sections"]:
            add(f" Rooms assigned  {stats['assigned_sections']}/10", DIM)
        if stats["wall_count"]:
            add(f" Partitions {stats['wall_count']} pcs "
                f"{stats['wall_weight']:,.0f} kg  "
                f"${stats['wall_cost']:,.0f}", DIM)
        for name, g in sorted(stats["prop_groups"].items()):
            add(f" {name:<17}x{g['count']}", DIM)
        if stats["prop_count"]:
            add(f" {stats['prop_weight']:,.0f} kg    "
                f"${stats['prop_cost']:,.0f}", VALUE)
        if stats["prop_watts"]:
            add(f" Power draw {stats['prop_watts']:,.0f} W", GOOD)
        add("")
    add(f"WEIGHT {stats['structure_weight']:,.0f} kg", ACCENT)
    add(f"COST   ${stats['total_cost']:,.0f}", ACCENT)

    width = 300
    row_h = 18
    pad = 10
    height = pad * 2 + row_h * len(lines)
    surf = pygame.Surface((width, height), pygame.SRCALPHA)
    surf.fill(BG)
    pygame.draw.rect(surf, (70, 130, 170, 255), surf.get_rect(), 1)

    y = pad
    for text, color in lines:
        if text:
            surf.blit(fonts.small.render(text, True, color), (pad, y))
        y += row_h
    return surf


def render_help(
    fonts: Fonts,
    width: int,
    aim_text: str,
    flash: str,
) -> pygame.Surface:
    height = 46
    surf = pygame.Surface((width, height), pygame.SRCALPHA)
    surf.fill(BG_SOFT)

    line1 = str(aim_text or "Outside: click panels | Inside: click floor or items")
    color1 = VALUE if aim_text else DIM
    if flash:
        line1 = str(flash)
        color1 = GOOD
    surf.blit(fonts.body.render(line1, True, color1), (12, 4))

    help_line = (
        "Ctrl+panel: walk | Right-click floor: add item | "
        "Shift/Ctrl-drag: move/resize UI | C camera | Arrows: view | "
        "Wheel: zoom | T note | R roof | B bag | P POV | M suite"
    )
    surf.blit(fonts.small.render(help_line, True, DIM), (12, 26))
    return surf


def _wrap_words(font, text: str, max_width: int) -> list[str]:
    lines: list[str] = []
    current = ""
    for word in text.split():
        trial = word if not current else current + " " + word
        if font.size(trial)[0] <= max_width:
            current = trial
        else:
            if current:
                lines.append(current)
            current = word
    if current:
        lines.append(current)
    return lines or [""]


def render_tooltip(
    fonts: Fonts,
    title: str,
    body: str,
    note: str = "",
) -> pygame.Surface:
    width = 390
    max_text = width - 24
    body_lines = _wrap_words(fonts.small, body, max_text)[:5]
    note_lines = _wrap_words(fonts.small, note, max_text)[:4] if note else []
    height = 54 + len(body_lines) * 17 + len(note_lines) * 17
    if note_lines:
        height += 20
    surf = pygame.Surface((width, height), pygame.SRCALPHA)
    surf.fill((18, 22, 26, 238))
    pygame.draw.rect(surf, (255, 190, 70, 255), surf.get_rect(), 2)
    surf.blit(fonts.body.render(title[:46], True, VALUE), (12, 8))
    surf.blit(fonts.small.render("Hover insight  |  T edit  |  Enter save",
                                 True, DIM), (12, 29))
    y = 52
    for line in body_lines:
        surf.blit(fonts.small.render(line, True, TEXT), (12, y))
        y += 17
    if note_lines:
        y += 6
        surf.blit(fonts.small.render("Saved investor note", True, HEADER),
                  (12, y))
        y += 17
        for line in note_lines:
            surf.blit(fonts.small.render(line, True, GOOD), (12, y))
            y += 17
    return surf


def render_note_editor(fonts: Fonts, title: str, text: str) -> pygame.Surface:
    width = 560
    lines = _wrap_words(fonts.body, text + "|", width - 28)[:7]
    height = 78 + len(lines) * 20
    surf = pygame.Surface((width, height), pygame.SRCALPHA)
    surf.fill((10, 12, 14, 245))
    pygame.draw.rect(surf, (120, 200, 255, 255), surf.get_rect(), 2)
    surf.blit(fonts.title.render("EDIT PRESENTATION NOTE", True, HEADER),
              (14, 10))
    surf.blit(fonts.small.render(title[:64], True, VALUE), (14, 35))
    surf.blit(fonts.small.render("Type note. Enter saves. Esc cancels.",
                                 True, DIM), (14, 54))
    y = 76
    for line in lines:
        surf.blit(fonts.body.render(line, True, TEXT), (14, y))
        y += 20
    return surf


def render_video_osd(
    fonts: Fonts,
    size: tuple[int, int],
    pan: float,
    tilt: float,
    fov: float,
    helm: bool,
    aiming_screen: bool,
    area_label: str = "",
    area_hint: str = "",
    detect_text: str = "",
    cam_label: str = "CAM-01",
) -> pygame.Surface:
    """Frame drawn over the PTZ video window: border, readout, prompts.

    The center is transparent so the live feed shows through.
    """
    w, h = size
    surf = pygame.Surface((w, h), pygame.SRCALPHA)
    surf.fill((0, 0, 0, 0))

    border = ACCENT if helm else (70, 130, 170)
    pygame.draw.rect(surf, border, (0, 0, w, h), 2)

    strip = pygame.Surface((w - 4, 20), pygame.SRCALPHA)
    strip.fill((10, 14, 18, 195))
    surf.blit(strip, (2, 2))
    zoom = 80.0 / max(fov, 1.0)
    readout = (
        f"{cam_label}  PAN {pan % 360.0:05.1f}  TILT {tilt:04.1f}  "
        f"ZOOM {zoom:.1f}x"
    )
    surf.blit(fonts.small.render(readout, True, TEXT), (8, 4))
    pygame.draw.circle(surf, (230, 60, 50), (w - 40, 12), 4)
    surf.blit(fonts.small.render("LIVE", True, DIM), (w - 32, 4))

    # Contextual awareness: which section the camera is watching and
    # what the vision system should expect to see happening there.
    if area_label:
        strip = pygame.Surface((w - 4, 18), pygame.SRCALPHA)
        strip.fill((10, 14, 18, 195))
        surf.blit(strip, (2, 22))
        context = f"WATCH {area_label}"
        if area_hint:
            context += f" · {area_hint}"
        surf.blit(fonts.small.render(context[:64], True, GOOD), (8, 23))
    if detect_text:
        strip = pygame.Surface((w - 4, 18), pygame.SRCALPHA)
        strip.fill((10, 14, 18, 195))
        surf.blit(strip, (2, 40))
        surf.blit(fonts.small.render(detect_text[:70], True,
                                     (255, 220, 130)), (8, 41))

    prompt = ""
    color = DIM
    if helm:
        prompt = "HELM  ARROWS pan/tilt  PGUP/PGDN zoom  ESC release"
        color = ACCENT
    elif aiming_screen:
        prompt = "CLICK SCREEN TO TAKE HELM"
        color = GOOD
    if prompt:
        strip = pygame.Surface((w - 4, 18), pygame.SRCALPHA)
        strip.fill((10, 14, 18, 195))
        surf.blit(strip, (2, h - 20))
        surf.blit(fonts.small.render(prompt, True, color), (8, h - 19))
    return surf


def render_toolbar(
    fonts: Fonts,
    buttons: list[tuple[str, str, bool]],   # (id, label, active)
) -> tuple[pygame.Surface, list[tuple[str, pygame.Rect]]]:
    """Clickable button strip. Returns the surface plus per-button rects
    (relative to the surface origin) for hit testing."""
    pad = 6
    btn_h = 30
    widths = []
    for _, label, _ in buttons:
        widths.append(fonts.body.size(label)[0] + 18)
    width = pad * 2 + sum(widths) + 6 * (len(buttons) - 1)
    height = btn_h + pad * 2

    surf = pygame.Surface((width, height), pygame.SRCALPHA)
    surf.fill(BG)
    pygame.draw.rect(surf, (70, 130, 170, 255), surf.get_rect(), 1)

    rects: list[tuple[str, pygame.Rect]] = []
    x = pad
    for (bid, label, active), w in zip(buttons, widths):
        rect = pygame.Rect(x, pad, w, btn_h)
        if active:
            pygame.draw.rect(surf, SELECT_BG, rect, border_radius=4)
            pygame.draw.rect(surf, ACCENT, rect, 1, border_radius=4)
        else:
            pygame.draw.rect(surf, (35, 45, 55, 235), rect,
                             border_radius=4)
            pygame.draw.rect(surf, (80, 100, 120), rect, 1,
                             border_radius=4)
        text = fonts.body.render(label, True,
                                 ACCENT if active else TEXT)
        surf.blit(text, (x + (w - text.get_width()) // 2,
                         pad + (btn_h - text.get_height()) // 2))
        rects.append((bid, rect))
        x += w + 6
    return surf, rects


def _item_abbrev(name: str) -> str:
    words = name.split()
    if len(words) >= 2:
        return (words[0][0] + words[1][0] + words[-1][-1]).upper()
    return name[:3].upper()


def _item_color(name: str) -> tuple[int, int, int]:
    h = sum(ord(c) * (i + 7) for i, c in enumerate(name))
    return (70 + (h * 37) % 140, 70 + (h * 61) % 140, 70 + (h * 89) % 140)


def render_inventory(
    fonts: Fonts,
    items: list[str],
    selected: int | None,
) -> tuple[pygame.Surface, list[pygame.Rect]]:
    """RuneScape-style 4x7 backpack grid. Returns surface + slot rects."""
    cols, rows = 4, 7
    cell = 42
    pad = 8
    header = 24
    width = pad * 2 + cols * cell
    height = pad * 2 + header + rows * cell

    surf = pygame.Surface((width, height), pygame.SRCALPHA)
    surf.fill(BG)
    pygame.draw.rect(surf, (150, 110, 60, 255), surf.get_rect(), 2)
    surf.blit(fonts.body.render(
        f"BACKPACK  {len(items)}/{cols * rows}", True, VALUE), (pad, pad))

    rects: list[pygame.Rect] = []
    for i in range(cols * rows):
        cx = pad + (i % cols) * cell
        cy = pad + header + (i // cols) * cell
        rect = pygame.Rect(cx + 2, cy + 2, cell - 4, cell - 4)
        rects.append(rect)
        pygame.draw.rect(surf, (30, 36, 42, 220), rect, border_radius=3)
        if i < len(items):
            color = _item_color(items[i])
            inner = rect.inflate(-8, -8)
            pygame.draw.rect(surf, color, inner, border_radius=3)
            abbrev = fonts.small.render(
                _item_abbrev(items[i]), True, (15, 15, 15))
            surf.blit(abbrev, (rect.centerx - abbrev.get_width() // 2,
                               rect.centery - abbrev.get_height() // 2))
        if selected == i:
            pygame.draw.rect(surf, ACCENT, rect, 2, border_radius=3)
        else:
            pygame.draw.rect(surf, (60, 70, 80), rect, 1, border_radius=3)
    return surf, rects


def render_energy(fonts: Fonts, energy, dome_count: int) -> pygame.Surface:
    """LCD-style power system panel: battery, solar, per-dome loads."""
    width = 300
    lines = 7 + dome_count
    height = 14 + lines * 19
    surf = pygame.Surface((width, height), pygame.SRCALPHA)
    surf.fill((8, 14, 12, 225))
    pygame.draw.rect(surf, (60, 200, 140, 255), surf.get_rect(), 2)
    lcd = (120, 255, 180)
    dim = (70, 150, 110)

    y = 8
    surf.blit(fonts.body.render("POWER SYSTEM", True, lcd), (10, y))
    surf.blit(fonts.small.render("x600 time", True, dim), (width - 80, y + 2))
    y += 24
    if not energy.has_system:
        surf.blit(fonts.small.render(
            "No battery bank installed.", True, lcd), (10, y))
        y += 19
        surf.blit(fonts.small.render(
            "Lamps run standalone. See File >", True, dim), (10, y))
        y += 19
        surf.blit(fonts.small.render(
            "'Electrify dome' to build the system.", True, dim), (10, y))
        y += 19
    else:
        frac = energy.charge_fraction()
        bar_w = width - 20
        pygame.draw.rect(surf, (25, 45, 35), (10, y, bar_w, 14))
        color = (90, 230, 140) if frac > 0.25 else (230, 120, 60)
        pygame.draw.rect(surf, color,
                         (10, y, int(bar_w * frac), 14))
        y += 18
        surf.blit(fonts.small.render(
            f"BATTERY {frac * 100:5.1f}%   "
            f"{energy.charge_kwh:.2f}/{energy.capacity_kwh:.0f} kWh",
            True, lcd), (10, y))
        y += 19
        net = energy.net_watts
        sign = "+" if net >= 0 else ""
        surf.blit(fonts.small.render(
            f"NET {sign}{net:,.0f} W", True,
            (120, 255, 180) if net >= 0 else (255, 150, 90)), (10, y))
        y += 19
        if energy.battery_empty:
            surf.blit(fonts.small.render(
                "!! BATTERY EMPTY - LOADS SHED !!", True,
                (255, 110, 80)), (10, y))
            y += 19
    surf.blit(fonts.small.render(
        f"SOLAR IN  {energy.solar_watts:,.0f} W", True, lcd), (10, y))
    y += 19
    for i in range(dome_count):
        load = energy.load_by_dome[i] if i < len(energy.load_by_dome) else 0
        lights = (energy.lights_by_dome[i]
                  if i < len(energy.lights_by_dome) else 0)
        surf.blit(fonts.small.render(
            f"DOME {i + 1} LOAD  {load:,.0f} W  ({lights} lights on)",
            True, dim), (10, y))
        y += 19
    return surf


def render_construction(
    fonts: Fonts,
    width: int,
    dome_label: str,
    step_label: str,
    step_index: int,
    step_count: int,
    elapsed_h: float,
    total_h: float,
    speed: float,
) -> pygame.Surface:
    height = 64
    surf = pygame.Surface((width, height), pygame.SRCALPHA)
    surf.fill((20, 16, 8, 225))
    pygame.draw.rect(surf, (240, 180, 60, 255), surf.get_rect(), 2)

    title = (f"CONSTRUCTING {dome_label} — step {step_index}/{step_count}: "
             f"{step_label}")
    surf.blit(fonts.body.render(title[:110], True, (255, 210, 120)),
              (12, 6))
    days = total_h / 8.0
    info = (f"{elapsed_h:,.1f} / {total_h:,.0f} labor-hours "
            f"(~{days:,.0f} days @ 8 h, 1 worker)   "
            f"speed: 1 s = {speed:.2f} h   [ - / + ]")
    surf.blit(fonts.small.render(info, True, (210, 190, 150)), (12, 26))

    bar_w = width - 24
    frac = min(elapsed_h / max(total_h, 0.01), 1.0)
    pygame.draw.rect(surf, (50, 42, 25), (12, 46, bar_w, 10))
    pygame.draw.rect(surf, (240, 180, 60),
                     (12, 46, int(bar_w * frac), 10))
    return surf


def render_workers(
    fonts: Fonts,
    sim: dict | None,
    workers: list[dict],
    trackers: list,
) -> pygame.Surface:
    width = 360
    rows = max(3, min(8, len(workers)))
    height = 76 + rows * 42
    surf = pygame.Surface((width, height), pygame.SRCALPHA)
    surf.fill((15, 20, 24, 230))
    pygame.draw.rect(surf, (80, 160, 210, 255), surf.get_rect(), 2)
    pygame.draw.rect(surf, (22, 42, 52, 235), (2, 2, width - 4, 25))

    title = "WORKER MANAGEMENT"
    surf.blit(fonts.body.render(title, True, HEADER), (10, 6))
    if sim:
        dome = int(sim.get("dome", 0)) + 1
        progress = float(sim.get("elapsed", 0.0)) / max(
            float(sim.get("total", 1.0)), 0.01)
        task = str(sim.get("task", "Construct dome"))
        surf.blit(fonts.small.render(
            f"DOME {dome}  {task}  {progress * 100:4.0f}%",
            True, VALUE), (10, 33))
        pygame.draw.rect(surf, (40, 58, 62), (10, 55, width - 20, 8))
        pygame.draw.rect(surf, GOOD,
                         (10, 55, int((width - 20) * min(progress, 1.0)), 8))
    else:
        surf.blit(fonts.small.render(
            "No active assignment. Right-click a dome to dispatch.",
            True, DIM), (10, 35))

    if not workers:
        surf.blit(fonts.small.render(
            "Crew idle.", True, DIM), (10, 76))
        return surf

    y = 72
    for worker in workers[:rows]:
        name = str(worker.get("name", "Worker"))
        action = str(worker.get("action", "Idle"))
        task = str(worker.get("task", "Unassigned"))
        dome = int(worker.get("dome", 0)) + 1
        hours = float(worker.get("hours", 0.0))
        visible = ""
        if 0 <= dome - 1 < len(trackers):
            tracker = trackers[dome - 1]
            if action in getattr(tracker, "current_actions", []):
                visible = "  CAM"
        surf.blit(fonts.small.render(
            f"{name}  D{dome}  {action}{visible}", True, TEXT), (10, y))
        y += 17
        surf.blit(fonts.small.render(
            f"  {task[:30]:30} {hours:5.1f} h",
            True, DIM), (10, y))
        y += 25
    return surf


def render_selected_dome_panel(fonts: Fonts, model, idx: int, moving: bool) -> pygame.Surface:
    stats = model.stats()
    width = 316
    height = 168
    surf = pygame.Surface((width, height), pygame.SRCALPHA)
    surf.fill((18, 22, 26, 238))
    pygame.draw.rect(surf, (100, 76, 42, 255), surf.get_rect(), 2)
    pygame.draw.rect(surf, (58, 45, 28, 240), (2, 2, width - 4, 25))
    surf.blit(fonts.body.render(f"SELECTED DOME {idx + 1}", True, VALUE),
              (10, 6))
    cfg = model.config
    x, y = float(model.origin[0]), float(model.origin[1])
    lines = [
        f"Style: {cfg.frequency}V {model.shape.name}",
        f"Position: X {x:6.1f} m   Y {y:6.1f} m",
        f"Radius: {cfg.radius:.2f} m   Height: {stats['height']:.1f} m",
        f"Floor: {stats['floor_area']:.0f} m2   Frame: {stats['frame_weight'] + stats['hub_weight']:,.0f} kg",
    ]
    if stats.get("trunk_stock_count"):
        lines.append(
            f"Trunks: {stats['trunk_stock_count']} x "
            f"{stats['trunk_stock_length'] * 3.28084:.0f} ft")
    yoff = 36
    for line in lines:
        surf.blit(fonts.small.render(line, True, TEXT), (10, yoff))
        yoff += 17
    if moving:
        prompt = "MOVE MODE: click open ground, Esc cancels"
        color = GOOD
    else:
        prompt = "Actions: Move | Resize +/- | Delete | Build sim"
        color = DIM
    surf.blit(fonts.small.render(prompt, True, color), (10, height - 24))
    return surf


def minimap_geometry(domes: list, player_pos,
                     size: int = 316) -> tuple[pygame.Rect, float]:
    map_rect = pygame.Rect(18, 36, size - 36, size - 54)
    pts = [(float(d.origin[0]), float(d.origin[1]),
            float(d.config.radius) * float(d.config.foundation_scale))
           for d in domes]
    px, py = float(player_pos[0]), float(player_pos[1])
    extent = max([abs(px), abs(py), 12.0] +
                 [max(abs(x) + r, abs(y) + r) for x, y, r in pts])
    scale = min(map_rect.width, map_rect.height) / (extent * 2.2)
    return map_rect, scale


def minimap_world_position(domes: list, player_pos, local_pos) \
        -> tuple[float, float] | None:
    map_rect, scale = minimap_geometry(domes, player_pos)
    if not map_rect.collidepoint(local_pos):
        return None
    x = (float(local_pos[0]) - map_rect.centerx) / scale
    y = -(float(local_pos[1]) - map_rect.centery) / scale
    return x, y


def render_minimap(fonts: Fonts, domes: list, active_idx: int,
                   player_pos, moving_idx: int | None = None,
                   navigation_target=None) -> pygame.Surface:
    size = 316
    surf = pygame.Surface((size, size), pygame.SRCALPHA)
    surf.fill((11, 15, 17, 245))
    pygame.draw.rect(surf, (112, 84, 45, 255), surf.get_rect(), 2)
    surf.blit(fonts.body.render("SITE MAP", True, VALUE), (10, 8))
    map_rect, scale = minimap_geometry(domes, player_pos, size)
    pygame.draw.rect(surf, (20, 32, 25), map_rect)
    pygame.draw.rect(surf, (58, 78, 56), map_rect, 1)
    pts = [(float(d.origin[0]), float(d.origin[1]),
            float(d.config.radius) * float(d.config.foundation_scale))
           for d in domes]
    px, py = float(player_pos[0]), float(player_pos[1])
    def map_xy(x, y):
        return (map_rect.centerx + int(x * scale),
                map_rect.centery - int(y * scale))

    for i, (x, y, r) in enumerate(pts):
        mx, my = map_xy(x, y)
        rr = max(5, int(r * scale))
        fill = (90, 150, 95) if i != active_idx else (230, 190, 80)
        if moving_idx == i:
            fill = (120, 220, 255)
        pygame.draw.circle(surf, fill, (mx, my), rr, 2)
        surf.blit(fonts.small.render(str(i + 1), True, TEXT),
                  (mx - 4, my - 7))
    mx, my = map_xy(px, py)
    pygame.draw.circle(surf, (120, 200, 255), (mx, my), 4)
    surf.blit(fonts.small.render("You", True, HEADER), (mx + 6, my - 7))
    if navigation_target is not None:
        tx, ty = map_xy(float(navigation_target[0]),
                        float(navigation_target[1]))
        pygame.draw.circle(surf, ACCENT, (tx, ty), 7, 2)
        pygame.draw.line(surf, ACCENT, (tx - 4, ty), (tx + 4, ty), 1)
        pygame.draw.line(surf, ACCENT, (tx, ty - 4), (tx, ty + 4), 1)
        surf.blit(fonts.small.render("Go", True, VALUE), (tx + 8, ty - 7))
    surf.blit(fonts.small.render("Click map to walk", True, DIM),
              (map_rect.x + 6, map_rect.bottom - 18))
    return surf


def _ellipsize(font, text: str, max_width: int) -> str:
    text = str(text)
    if font.size(text)[0] <= max_width:
        return text
    while text and font.size(text + "...")[0] > max_width:
        text = text[:-1]
    return text + "..."


def render_management_suite(
    fonts: Fonts,
    size: tuple[int, int],
    page: str,
    tabs: list[tuple[str, str]],
    items: list[MenuItem],
    scroll: int,
    domes: list,
    active_idx: int,
    workers: list[dict],
    sim: dict | None,
    trackers: list,
    stats: dict,
    energy,
    player_pos,
    status: str = "",
) -> tuple[pygame.Surface, dict]:
    """Opaque, full-window workspace for management-heavy workflows."""
    width, height = size
    surf = pygame.Surface(size, pygame.SRCALPHA)
    surf.fill((11, 14, 17, 255))
    hit: dict = {"tabs": [], "controls": [], "scroll_max": 0}

    nav_w = 184
    summary_w = max(300, min(380, width // 4))
    top_h = 66
    bottom_h = 34
    content = pygame.Rect(nav_w + 20, top_h + 18,
                          max(300, width - nav_w - summary_w - 52),
                          max(260, height - top_h - bottom_h - 36))
    summary = pygame.Rect(width - summary_w - 16, top_h + 18,
                          summary_w, content.height)

    pygame.draw.rect(surf, (27, 31, 34), (0, 0, width, top_h))
    pygame.draw.line(surf, (142, 103, 52), (0, top_h - 1),
                     (width, top_h - 1), 2)
    pygame.draw.rect(surf, (17, 21, 24), (0, top_h, nav_w, height - top_h))
    pygame.draw.line(surf, (66, 75, 81), (nav_w, top_h),
                     (nav_w, height), 1)

    surf.blit(fonts.title.render("DOME OPERATIONS SUITE", True, VALUE),
              (20, 13))
    surf.blit(fonts.small.render(
        "Design, staffing, materials, utilities, and site control",
        True, DIM), (20, 38))

    close_rect = pygame.Rect(width - 190, 15, 170, 34)
    pygame.draw.rect(surf, (56, 45, 30), close_rect, border_radius=3)
    pygame.draw.rect(surf, (180, 132, 67), close_rect, 1, border_radius=3)
    label = fonts.body.render("RETURN TO WORLD", True, VALUE)
    surf.blit(label, (close_rect.centerx - label.get_width() // 2,
                      close_rect.centery - label.get_height() // 2))
    hit["close"] = close_rect

    surf.blit(fonts.small.render("WORKSPACES", True, HEADER), (16, top_h + 18))
    y = top_h + 42
    for key, label_text in tabs:
        rect = pygame.Rect(10, y, nav_w - 20, 36)
        if key == page:
            pygame.draw.rect(surf, (42, 68, 79), rect)
            pygame.draw.rect(surf, ACCENT, (rect.x, rect.y, 3, rect.height))
            color = TEXT
        else:
            color = DIM
        surf.blit(fonts.body.render(label_text, True, color),
                  (rect.x + 13, rect.y + 9))
        hit["tabs"].append((key, rect))
        y += 40

    def add_control(action: str, rect: pygame.Rect) -> None:
        hit["controls"].append((action, rect))

    def button(label_text: str, rect: pygame.Rect, action: str,
               accent: bool = False) -> None:
        fill = (53, 67, 72) if not accent else (72, 58, 34)
        edge = (91, 112, 119) if not accent else (182, 132, 67)
        pygame.draw.rect(surf, fill, rect, border_radius=3)
        pygame.draw.rect(surf, edge, rect, 1, border_radius=3)
        txt = fonts.small.render(_ellipsize(fonts.small, label_text,
                                            rect.width - 12), True, TEXT)
        surf.blit(txt, (rect.centerx - txt.get_width() // 2,
                        rect.centery - txt.get_height() // 2))
        add_control(action, rect)

    def section_title(title: str, subtitle: str = "") -> None:
        surf.blit(fonts.title.render(title, True, HEADER),
                  (content.x, content.y))
        if subtitle:
            surf.blit(fonts.small.render(
                _ellipsize(fonts.small, subtitle, content.width), True, DIM),
                (content.x, content.y + 24))

    # Persistent active-dome pane.
    pygame.draw.rect(surf, (18, 23, 26), summary)
    pygame.draw.rect(surf, (62, 72, 78), summary, 1)
    sx = summary.x + 16
    sy = summary.y + 14
    surf.blit(fonts.small.render("ACTIVE STRUCTURE", True, HEADER), (sx, sy))
    sy += 24
    surf.blit(fonts.title.render(f"DOME {active_idx + 1}", True, VALUE),
              (sx, sy))
    prev_rect = pygame.Rect(summary.right - 82, sy - 3, 30, 26)
    next_rect = pygame.Rect(summary.right - 46, sy - 3, 30, 26)
    button("<", prev_rect, "active_prev")
    button(">", next_rect, "active_next")
    sy += 34
    model = domes[active_idx]
    cfg = model.config
    info = [
        f"{cfg.frequency}V {model.shape.name}",
        f"Radius {cfg.radius:.1f} m | Height {stats['height']:.1f} m",
        f"Position {float(model.origin[0]):.1f}, {float(model.origin[1]):.1f}",
        f"Floor {stats['floor_area']:.0f} m2 | Shell {stats['surface_area']:.0f} m2",
        f"Cost ${stats['total_cost']:,.0f}",
    ]
    for line in info:
        surf.blit(fonts.small.render(
            _ellipsize(fonts.small, line, summary.width - 32), True, TEXT),
            (sx, sy))
        sy += 18

    diagram = pygame.Rect(summary.x + 24, sy + 8,
                          summary.width - 48, min(220, summary.width - 48))
    center = diagram.center
    radius = max(45, min(diagram.width, diagram.height) // 2 - 14)
    pygame.draw.circle(surf, (31, 48, 43), center, radius)
    pygame.draw.circle(surf, (120, 170, 128), center, radius, 2)
    for i in range(10):
        angle = math.radians(i * 36 - 90)
        end = (center[0] + int(math.cos(angle) * radius),
               center[1] + int(math.sin(angle) * radius))
        pygame.draw.line(surf, (61, 86, 73), center, end, 1)
    player_x = float(player_pos[0]) - float(model.origin[0])
    player_y = float(player_pos[1]) - float(model.origin[1])
    floor_r = max(float(model.floor_radius), 0.01)
    if math.hypot(player_x, player_y) <= floor_r * 1.15:
        dot = (center[0] + int(player_x / floor_r * radius),
               center[1] - int(player_y / floor_r * radius))
        pygame.draw.circle(surf, (120, 205, 255), dot, 5)
    sy = diagram.bottom + 10
    edit_rect = pygame.Rect(sx, sy, summary.width - 32, 30)
    button("OPEN DOME EDITOR", edit_rect, "summary_edit", True)
    sy += 38
    world_rect = pygame.Rect(sx, sy, summary.width - 32, 30)
    button("RETURN NEAR THIS DOME", world_rect, "summary_world")

    if page in {"DOME", "ROOMS", "LAB", "FILES"}:
        titles = {
            "DOME": ("DOME EDITOR", "Structure, dimensions, shell, and foundation"),
            "ROOMS": ("INTERIOR PLANNER", "Partitions and ten-section room assignments"),
            "LAB": ("PANEL LAB", "Compose production-ready custom panel assemblies"),
            "FILES": ("SITE ADMINISTRATION", "Presets, construction, persistence, and exports"),
        }
        section_title(*titles[page])
        row_y = content.y + 54
        row_h = 36
        visible_rows = max(1, (content.bottom - row_y - 8) // row_h)
        max_scroll = max(0, len(items) - visible_rows)
        scroll = max(0, min(scroll, max_scroll))
        hit["scroll_max"] = max_scroll
        for index in range(scroll, min(len(items), scroll + visible_rows)):
            item = items[index]
            rect = pygame.Rect(content.x, row_y, content.width, row_h - 3)
            if item.kind == "header":
                pygame.draw.line(surf, (63, 78, 84),
                                 (rect.x, rect.centery),
                                 (rect.right, rect.centery), 1)
                text = fonts.small.render(f" {item.label} ", True, HEADER)
                pygame.draw.rect(surf, (11, 14, 17),
                                 (rect.x + 12, rect.y, text.get_width() + 8,
                                  rect.height))
                surf.blit(text, (rect.x + 16, rect.y + 9))
            else:
                pygame.draw.rect(surf, (22, 28, 32), rect)
                pygame.draw.rect(surf, (48, 59, 65), rect, 1)
                value_width = min(310, content.width // 3)
                label_max = content.width - value_width - 118
                surf.blit(fonts.body.render(
                    _ellipsize(fonts.body, item.label, label_max), True, TEXT),
                    (rect.x + 12, rect.y + 8))
                if item.kind == "choice":
                    prev = pygame.Rect(rect.right - value_width - 76,
                                       rect.y + 4, 30, rect.height - 8)
                    nxt = pygame.Rect(rect.right - 36, rect.y + 4,
                                      30, rect.height - 8)
                    pygame.draw.rect(surf, (48, 58, 63), prev)
                    pygame.draw.rect(surf, (48, 58, 63), nxt)
                    surf.blit(fonts.body.render("<", True, VALUE),
                              (prev.centerx - 4, prev.y + 4))
                    surf.blit(fonts.body.render(">", True, VALUE),
                              (nxt.centerx - 4, nxt.y + 4))
                    value = item.value() if item.value else ""
                    value_rect = pygame.Rect(prev.right + 5, rect.y + 4,
                                             nxt.x - prev.right - 10,
                                             rect.height - 8)
                    txt = fonts.small.render(_ellipsize(
                        fonts.small, value, value_rect.width), True, VALUE)
                    surf.blit(txt, (value_rect.centerx - txt.get_width() // 2,
                                    value_rect.centery - txt.get_height() // 2))
                    add_control(f"item_prev:{index}", prev)
                    add_control(f"item_next:{index}", nxt)
                    add_control(f"item:{index}", rect)
                else:
                    action_rect = pygame.Rect(rect.right - 96, rect.y + 4,
                                              90, rect.height - 8)
                    pygame.draw.rect(surf, (51, 70, 59), action_rect)
                    pygame.draw.rect(surf, (92, 142, 104), action_rect, 1)
                    txt = fonts.small.render("RUN", True, GOOD)
                    surf.blit(txt, (action_rect.centerx - txt.get_width() // 2,
                                    action_rect.centery - txt.get_height() // 2))
                    add_control(f"item:{index}", rect)
            row_y += row_h
        if max_scroll:
            scroll_text = f"Rows {scroll + 1}-{min(len(items), scroll + visible_rows)} of {len(items)} | mouse wheel"
            surf.blit(fonts.small.render(scroll_text, True, DIM),
                      (content.x, content.bottom - 18))

    elif page == "SITE":
        section_title("SITE COMMAND", "Select, move, resize, construct, or remove any dome")
        map_area = pygame.Rect(content.x, content.y + 52,
                               max(260, content.width // 2 - 10),
                               content.height - 56)
        pygame.draw.rect(surf, (18, 31, 24), map_area)
        pygame.draw.rect(surf, (66, 88, 69), map_area, 1)
        points = [(float(d.origin[0]), float(d.origin[1]),
                   float(d.config.radius) * float(d.config.foundation_scale))
                  for d in domes]
        extent = max([12.0] + [max(abs(x) + r, abs(y) + r)
                              for x, y, r in points])
        map_scale = min(map_area.width, map_area.height) / (extent * 2.35)
        for i, (x, y0, radius0) in enumerate(points):
            center0 = (map_area.centerx + int(x * map_scale),
                       map_area.centery - int(y0 * map_scale))
            rr = max(8, int(radius0 * map_scale))
            color = VALUE if i == active_idx else (116, 170, 124)
            pygame.draw.circle(surf, color, center0, rr, 2)
            surf.blit(fonts.body.render(str(i + 1), True, color),
                      (center0[0] - 4, center0[1] - 8))
        px = map_area.centerx + int(float(player_pos[0]) * map_scale)
        py = map_area.centery - int(float(player_pos[1]) * map_scale)
        pygame.draw.circle(surf, (120, 205, 255), (px, py), 5)

        list_x = map_area.right + 14
        list_w = content.right - list_x
        y0 = content.y + 52
        add_rect = pygame.Rect(list_x, y0, list_w, 32)
        button("ADD DOME TO SITE", add_rect, "site_add", True)
        y0 += 40
        visible = max(1, (content.bottom - y0) // 88)
        max_scroll = max(0, len(domes) - visible)
        scroll = max(0, min(scroll, max_scroll))
        hit["scroll_max"] = max_scroll
        for i in range(scroll, min(len(domes), scroll + visible)):
            dome = domes[i]
            card = pygame.Rect(list_x, y0, list_w, 82)
            pygame.draw.rect(surf, (22, 28, 32), card)
            pygame.draw.rect(surf, VALUE if i == active_idx else (52, 64, 70),
                             card, 1)
            title = f"DOME {i + 1} | {dome.config.frequency}V | r={dome.config.radius:.1f}m"
            surf.blit(fonts.small.render(
                _ellipsize(fonts.small, title, list_w - 16), True, TEXT),
                (card.x + 8, card.y + 7))
            labels = [("EDIT", "edit"), ("MOVE", "move"),
                      ("+10%", "grow"), ("-10%", "shrink"),
                      ("BUILD", "build"), ("DELETE", "delete")]
            bw = max(42, (list_w - 22) // 3)
            for j, (label_text, action) in enumerate(labels):
                bx = card.x + 7 + (j % 3) * (bw + 4)
                by = card.y + 29 + (j // 3) * 24
                rect = pygame.Rect(bx, by, bw, 21)
                button(label_text, rect, f"site_{action}:{i}",
                       action == "edit")
            y0 += 88

    elif page == "CREW":
        section_title("WORKFORCE CONTROL", "Dispatch workers, set task focus, and control build tempo")
        y0 = content.y + 52
        controls = [
            ("START ACTIVE DOME", "crew_start"),
            ("ADD WORKER", "crew_add"),
            ("REMOVE WORKER", "crew_remove"),
            ("SPEED x2", "crew_fast"),
            ("SPEED /2", "crew_slow"),
            ("STOP BUILD", "crew_stop"),
        ]
        bw = max(110, (content.width - 25) // 3)
        for i, (label_text, action) in enumerate(controls):
            rect = pygame.Rect(content.x + (i % 3) * (bw + 8),
                               y0 + (i // 3) * 38, bw, 30)
            button(label_text, rect, action, i == 0)
        y0 += 88
        tasks = ["Frame assembly", "Panel install", "Electrical rough-in",
                 "Interior setup", "Safety inspection"]
        surf.blit(fonts.small.render("TASK FOCUS", True, HEADER),
                  (content.x, y0))
        y0 += 24
        tw = max(110, (content.width - 32) // 5)
        for i, task in enumerate(tasks):
            rect = pygame.Rect(content.x + i * (tw + 6), y0, tw, 30)
            button(task, rect, f"crew_task:{i}")
        y0 += 48
        if sim:
            progress = float(sim.get("elapsed", 0.0)) / max(
                float(sim.get("total", 1.0)), 0.01)
            pygame.draw.rect(surf, (39, 47, 50),
                             (content.x, y0, content.width, 18))
            pygame.draw.rect(surf, GOOD,
                             (content.x, y0,
                              int(content.width * min(progress, 1.0)), 18))
            surf.blit(fonts.small.render(
                f"Dome {int(sim['dome']) + 1} | {sim.get('task', '')} | {progress * 100:.0f}% | {sim.get('workers', 1)} workers | speed {sim.get('speed', 1.0):.1f}x",
                True, TEXT), (content.x + 8, y0 + 2))
        else:
            surf.blit(fonts.body.render("No active construction assignment", True, DIM),
                      (content.x, y0))
        y0 += 34
        headers = ["WORKER", "DOME", "TASK", "ACTION", "HOURS", "DISTANCE"]
        col_x = [content.x, content.x + 90, content.x + 145,
                 content.x + content.width // 2 + 20,
                 content.right - 150, content.right - 75]
        for hx, label_text in zip(col_x, headers):
            surf.blit(fonts.small.render(label_text, True, HEADER), (hx, y0))
        y0 += 22
        pygame.draw.line(surf, (66, 78, 84), (content.x, y0 - 4),
                         (content.right, y0 - 4), 1)
        for worker in workers[:12]:
            values = [str(worker.get("name", "Worker")),
                      str(int(worker.get("dome", 0)) + 1),
                      str(worker.get("task", "Unassigned")),
                      str(worker.get("action", "Idle")),
                      f"{float(worker.get('hours', 0.0)):.1f}",
                      f"{float(worker.get('distance', 0.0)):.1f}m"]
            limits = [80, 45, max(100, content.width // 3 - 20),
                      max(90, content.width // 4 - 20), 60, 70]
            for hx, value, limit in zip(col_x, values, limits):
                surf.blit(fonts.small.render(
                    _ellipsize(fonts.small, value, limit), True, TEXT),
                    (hx, y0))
            y0 += 24

    elif page == "MATERIALS":
        section_title("MATERIAL INTELLIGENCE", "Live quantities, weight, cost, and procurement signals")
        y0 = content.y + 58
        cards = [
            ("FRAME", stats['frame_weight'] + stats['hub_weight'],
             stats['frame_cost'] + stats['hub_cost'],
             f"{stats['strut_count']} struts | {stats['hub_count']} hubs"),
            ("PANELS", stats['panel_weight'], stats['panel_cost'],
             f"{sum(g['count'] for g in stats['panel_groups'].values())} panels"),
            ("LAYERS", stats['layer_weight'], stats['layer_cost'],
             f"{len(stats['layer_rows'])} shell layers"),
            ("FOUNDATION", stats['foundation_weight'], stats['foundation_cost'],
             stats['foundation_name']),
            ("INTERIOR", stats['wall_weight'] + stats['prop_weight'],
             stats['wall_cost'] + stats['prop_cost'],
             f"{stats['prop_count']} placed objects"),
        ]
        card_h = 70
        for i, (title, weight, cost, detail) in enumerate(cards):
            col = i % 2
            row = i // 2
            cw = (content.width - 10) // 2
            rect = pygame.Rect(content.x + col * (cw + 10),
                               y0 + row * (card_h + 10), cw, card_h)
            pygame.draw.rect(surf, (22, 28, 32), rect)
            pygame.draw.rect(surf, (58, 72, 78), rect, 1)
            surf.blit(fonts.small.render(title, True, HEADER),
                      (rect.x + 10, rect.y + 8))
            surf.blit(fonts.body.render(
                f"{weight:,.0f} kg   ${cost:,.0f}", True, VALUE),
                (rect.x + 10, rect.y + 27))
            surf.blit(fonts.small.render(
                _ellipsize(fonts.small, detail, rect.width - 20), True, DIM),
                (rect.x + 10, rect.y + 49))
        y0 += 3 * (card_h + 10)
        total = max(stats['total_cost'], 1.0)
        surf.blit(fonts.small.render("COST DISTRIBUTION", True, HEADER),
                  (content.x, y0))
        y0 += 24
        for title, _weight, cost, _detail in cards:
            bar_w = max(2, int((content.width - 130) * cost / total))
            surf.blit(fonts.small.render(title, True, DIM), (content.x, y0))
            pygame.draw.rect(surf, (38, 45, 49),
                             (content.x + 110, y0 + 2, content.width - 110, 12))
            pygame.draw.rect(surf, (192, 137, 67),
                             (content.x + 110, y0 + 2, bar_w, 12))
            y0 += 21
        button("EXPORT BILL OF MATERIALS",
               pygame.Rect(content.x, content.bottom - 38, 250, 30),
               "materials_export", True)

    elif page == "POWER":
        section_title("ENERGY CONTROL", "Battery health, generation, loads, and dome electrification")
        y0 = content.y + 60
        gauge = pygame.Rect(content.x, y0, content.width, 46)
        pygame.draw.rect(surf, (17, 31, 25), gauge)
        frac = energy.charge_fraction() if energy.has_system else 0.0
        pygame.draw.rect(surf, (37, 49, 43),
                         (gauge.x + 12, gauge.y + 24, gauge.width - 24, 12))
        pygame.draw.rect(surf, (93, 213, 139),
                         (gauge.x + 12, gauge.y + 24,
                          int((gauge.width - 24) * frac), 12))
        label_text = (f"BATTERY {frac * 100:.1f}% | {energy.charge_kwh:.1f} / "
                      f"{energy.capacity_kwh:.0f} kWh" if energy.has_system
                      else "NO SHARED BATTERY SYSTEM INSTALLED")
        surf.blit(fonts.body.render(label_text, True, GOOD if energy.has_system else ACCENT),
                  (gauge.x + 12, gauge.y + 4))
        y0 += 66
        metrics = [
            ("SOLAR", f"{energy.solar_watts:,.0f} W"),
            ("SITE LOAD", f"{sum(energy.load_by_dome):,.0f} W"),
            ("NET", f"{energy.net_watts:+,.0f} W"),
        ]
        mw = (content.width - 20) // 3
        for i, (title, value) in enumerate(metrics):
            rect = pygame.Rect(content.x + i * (mw + 10), y0, mw, 70)
            pygame.draw.rect(surf, (22, 29, 31), rect)
            surf.blit(fonts.small.render(title, True, HEADER),
                      (rect.x + 10, rect.y + 9))
            surf.blit(fonts.title.render(value, True, VALUE),
                      (rect.x + 10, rect.y + 34))
        y0 += 92
        surf.blit(fonts.small.render("LOAD BY DOME", True, HEADER),
                  (content.x, y0))
        y0 += 28
        visible = max(1, (content.bottom - y0 - 44) // 39)
        max_scroll = max(0, len(domes) - visible)
        scroll = max(0, min(scroll, max_scroll))
        hit["scroll_max"] = max_scroll
        for i in range(scroll, min(len(domes), scroll + visible)):
            load = energy.load_by_dome[i] if i < len(energy.load_by_dome) else 0.0
            lights = energy.lights_by_dome[i] if i < len(energy.lights_by_dome) else 0
            rect = pygame.Rect(content.x, y0, content.width, 34)
            pygame.draw.rect(surf, (21, 27, 30), rect)
            surf.blit(fonts.body.render(
                f"DOME {i + 1}", True, TEXT), (rect.x + 10, rect.y + 8))
            surf.blit(fonts.small.render(
                f"{load:,.0f} W | {lights} lights on", True, DIM),
                (rect.right - 210, rect.y + 9))
            y0 += 39
        button("ELECTRIFY ACTIVE DOME",
               pygame.Rect(content.x, content.bottom - 38, 230, 30),
               "power_electrify", True)

    if status:
        pygame.draw.rect(surf, (29, 34, 37),
                         (nav_w, height - bottom_h,
                          width - nav_w, bottom_h))
        surf.blit(fonts.small.render(
            _ellipsize(fonts.small, status, width - nav_w - 30),
            True, GOOD), (nav_w + 14, height - bottom_h + 9))
    else:
        surf.blit(fonts.small.render(
            "Esc returns to world | Mouse wheel scrolls command lists",
            True, DIM), (nav_w + 14, height - bottom_h + 9))
    return surf, hit


def render_side_rail(fonts: Fonts, width: int, height: int) -> pygame.Surface:
    surf = pygame.Surface((width, height), pygame.SRCALPHA)
    surf.fill((8, 10, 12, 238))
    pygame.draw.rect(surf, (86, 64, 36, 255), surf.get_rect(), 2)
    pygame.draw.rect(surf, (38, 30, 20, 245), (0, 0, width, 34))
    surf.blit(fonts.body.render("DOME COMMAND", True, VALUE), (12, 9))
    return surf


def render_context_menu(
    fonts: Fonts,
    entries: list[str],
    hover: int = -1,
    title: str = "Choose Option",
) -> tuple[pygame.Surface, list[pygame.Rect]]:
    """RuneScape-style 'Choose Option' popup."""
    row_h = 19
    width = max(
        [fonts.small.render(e, True, TEXT).get_width()
         for e in entries] +
        [fonts.small.render(title, True, TEXT).get_width(), 110]) + 20
    height = 22 + row_h * len(entries) + 6
    surf = pygame.Surface((width, height), pygame.SRCALPHA)
    surf.fill((30, 26, 20, 245))
    pygame.draw.rect(surf, (10, 8, 6), surf.get_rect(), 1)
    pygame.draw.rect(surf, (94, 80, 56),
                     pygame.Rect(1, 1, width - 2, 18))
    surf.blit(fonts.small.render(title, True, (20, 16, 10)),
              (8, 3))
    rects = []
    y = 22
    for i, entry in enumerate(entries):
        rect = pygame.Rect(2, y, width - 4, row_h)
        if i == hover:
            pygame.draw.rect(surf, (74, 62, 40), rect)
        color = (235, 225, 200) if i != hover else (255, 255, 240)
        surf.blit(fonts.small.render(entry, True, color), (8, y + 2))
        rects.append(rect)
        y += row_h
    return surf, rects


LEGEND_LINES = [
    ("MOUSE", HEADER),
    ("L-click   contextual action", TEXT),
    ("R-click   options menu", TEXT),
    ("Ctrl+panel walk outside", TEXT),
    ("R-click floor add item", TEXT),
    ("Shift-drag move widgets", TEXT),
    ("Ctrl-drag resize widgets", TEXT),
    ("Minimap click to walk", TEXT),
    ("Mid-drag  rotate view", TEXT),
    ("Wheel     zoom", TEXT),
    ("KEYS", HEADER),
    ("Arrows    rotate camera", TEXT),
    ("          (PTZ at helm)", DIM),
    ("P         first-person (WASD)", TEXT),
    ("C         camera helm", TEXT),
    ("R         roof on/off", TEXT),
    ("B         backpack", TEXT),
    ("N         energy suite", TEXT),
    ("K         this legend", TEXT),
    (", .       rotate placement", TEXT),
    ("[ ]       sim speed", TEXT),
    ("Del       pack up prop", TEXT),
    ("Tab       360 view", TEXT),
    ("F5/F9/F6  save/load/BOM", TEXT),
]


def render_legend(fonts: Fonts, collapsed: bool) -> pygame.Surface:
    if collapsed:
        surf = pygame.Surface((92, 22), pygame.SRCALPHA)
        surf.fill(BG_SOFT)
        pygame.draw.rect(surf, (70, 130, 170, 255), surf.get_rect(), 1)
        surf.blit(fonts.small.render("K: keys ▸", True, DIM), (8, 4))
        return surf
    width = 196
    height = 14 + len(LEGEND_LINES) * 17
    surf = pygame.Surface((width, height), pygame.SRCALPHA)
    surf.fill(BG_SOFT)
    pygame.draw.rect(surf, (70, 130, 170, 255), surf.get_rect(), 1)
    y = 6
    for text, color in LEGEND_LINES:
        font = fonts.small
        surf.blit(font.render(text, True, color), (8, y))
        y += 17
    return surf


def render_dome_manager(
    fonts: Fonts,
    rows: list[dict],
    active: int,
) -> tuple[pygame.Surface, list[pygame.Rect], pygame.Rect]:
    """Site overview: one row per dome + an 'Add dome' row.
    Returns (surface, row_rects, add_rect)."""
    width = 430
    row_h = 34
    pad = 8
    height = pad + 24 + row_h * len(rows) + 26 + pad
    surf = pygame.Surface((width, height), pygame.SRCALPHA)
    surf.fill(BG)
    pygame.draw.rect(surf, (70, 130, 170, 255), surf.get_rect(), 1)
    surf.blit(fonts.title.render("SITE — DOMES", True, HEADER),
              (pad + 2, pad))
    y = pad + 24
    rects = []
    for i, row in enumerate(rows):
        rect = pygame.Rect(4, y, width - 8, row_h - 2)
        if i == active:
            pygame.draw.rect(surf, SELECT_BG, rect)
        pygame.draw.rect(surf, (50, 70, 88), rect, 1)
        title = f"DOME {i + 1}  {row['title']}"
        surf.blit(fonts.body.render(title, True,
                                    ACCENT if i == active else TEXT),
                  (12, y + 2))
        surf.blit(fonts.small.render(row["info"], True, DIM),
                  (12, y + 17))
        rects.append(rect)
        y += row_h
    add_rect = pygame.Rect(4, y + 2, width - 8, 20)
    pygame.draw.rect(surf, (30, 60, 42), add_rect)
    pygame.draw.rect(surf, (60, 140, 90), add_rect, 1)
    surf.blit(fonts.body.render("+ Add dome  (choose style, then click "
                                "the ground)", True, GOOD), (12, y + 3))
    return surf, rects, add_rect


def render_crosshair() -> pygame.Surface:
    size = 22
    surf = pygame.Surface((size, size), pygame.SRCALPHA)
    c = size // 2
    pygame.draw.circle(surf, (255, 255, 255, 200), (c, c), 7, 1)
    pygame.draw.circle(surf, (255, 180, 60, 255), (c, c), 2)
    return surf


def render_mouse_cursor() -> pygame.Surface:
    """High-contrast software cursor for fullscreen OpenGL mode."""
    surf = pygame.Surface((24, 30), pygame.SRCALPHA)
    points = [(2, 1), (2, 23), (7, 18), (12, 28),
              (16, 26), (11, 17), (20, 17)]
    shadow = [(x + 2, y + 2) for x, y in points]
    pygame.draw.polygon(surf, (0, 0, 0, 210), shadow)
    pygame.draw.polygon(surf, (245, 247, 242, 255), points)
    pygame.draw.lines(surf, (20, 24, 27, 255), True, points, 2)
    pygame.draw.line(surf, (255, 184, 70, 255), (4, 4), (4, 18), 1)
    return surf
