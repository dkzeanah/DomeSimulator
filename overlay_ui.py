"""
2D overlay widgets for the dome creator, rendered with pygame fonts into
RGBA surfaces. The main app uploads these surfaces as GL textures and
composites them over the 3D view.
"""

from __future__ import annotations

from dataclasses import dataclass
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

    line1 = aim_text or "Aim at a panel and click to swap it"
    color1 = VALUE if aim_text else DIM
    if flash:
        line1 = flash
        color1 = GOOD
    surf.blit(fonts.body.render(line1, True, color1), (12, 4))

    help_line = (
        "Click: walk / pick up / take helm | Shift+Click: swap panel | "
        "C camera control | Mid-drag+arrows: view | Wheel: zoom | "
        "R roof | B bag | P first-person | M menu | F5/F9/F6 file"
    )
    surf.blit(fonts.small.render(help_line, True, DIM), (12, 26))
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


def render_context_menu(
    fonts: Fonts,
    entries: list[str],
    hover: int = -1,
) -> tuple[pygame.Surface, list[pygame.Rect]]:
    """RuneScape-style 'Choose Option' popup."""
    row_h = 19
    width = max(
        [fonts.small.render(e, True, TEXT).get_width()
         for e in entries] + [110]) + 20
    height = 22 + row_h * len(entries) + 6
    surf = pygame.Surface((width, height), pygame.SRCALPHA)
    surf.fill((30, 26, 20, 245))
    pygame.draw.rect(surf, (10, 8, 6), surf.get_rect(), 1)
    pygame.draw.rect(surf, (94, 80, 56),
                     pygame.Rect(1, 1, width - 2, 18))
    surf.blit(fonts.small.render("Choose Option", True, (20, 16, 10)),
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
    ("L-click   walk / use / next", TEXT),
    ("R-click   options menu", TEXT),
    ("Alt-drag  move widgets", TEXT),
    ("Mid-drag  rotate view", TEXT),
    ("Wheel     zoom", TEXT),
    ("KEYS", HEADER),
    ("Arrows    rotate camera", TEXT),
    ("          (PTZ at helm)", DIM),
    ("P         first-person (WASD)", TEXT),
    ("C         camera helm", TEXT),
    ("R         roof on/off", TEXT),
    ("B         backpack", TEXT),
    ("N         power meter", TEXT),
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
