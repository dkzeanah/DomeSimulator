"""The seed dome's cost calculator, drawn inside a 3-D window.

The Raw Wedge Dome tool already shows the dome that gets built. What it did
not show was what building one costs, and that number lived in a report you
had to leave the tool to read. This is that report made clickable, drawn as a
Pygame surface the tool uploads as an overlay, so the price and the building
are in the same window.

Nothing here decides a figure. Every quantity comes from
:func:`seed_model.seed_geometry` and every price from
:data:`seed_model.EXTERNAL_CONSTANTS`; this module lays them out, takes the
clicks, and writes changed prices back through
:func:`seed_model.set_override`. Change a rate on the PRICES page and the
QUOTE page moves on the next frame, because it is the same function being
asked again rather than a cached answer.

Four pages
----------
**QUOTE**   every line of one dome, grouped, with the totals and the price.
**PRICES**  every input, its unit, its reason, and a way to change it.
**LEVERS**  what each single saving is worth off the price, ranked.
**SEEDS**   the whole catalogue side by side, cheapest first.

Typing a price
--------------
Click a row on PRICES to select it, type a number, press Enter. Nothing is
saved to disk until SAVE is pressed, and RESET puts one row back to the
value the model shipped with. That is the whole editing model, and it is
deliberately small: this is a calculator, not a spreadsheet.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path

import pygame

import seed_model

ROOT = Path(__file__).resolve().parent
EXPORT_DIR = ROOT / "exports"

BG = (10, 14, 20, 238)
EDGE = (62, 96, 126)
INK = (232, 240, 248)
DIM = (152, 170, 188)
FAINT = (104, 120, 138)
ACCENT = (95, 210, 255)
MONEY = (120, 226, 160)
WARN = (255, 178, 90)
BAD = (255, 122, 122)
BUTTON = (26, 38, 52)
BUTTON_ON = (30, 84, 118)
BUTTON_EDGE = (76, 118, 152)

PAGES = ("quote", "prices", "levers", "seeds")
PAGE_LABEL = {"quote": "QUOTE", "prices": "PRICES", "levers": "LEVERS",
              "seeds": "SEEDS"}

STEP_FRACTION = 0.05
"""One click on a nudge button moves a price five percent. Shift makes it
twenty-five, because some of these are guesses a factor out rather than a
percent out."""

ROWS_PER_PAGE = 16


@dataclass
class Region:
    """A clickable rectangle and what pressing it means."""

    rect: pygame.Rect
    action: str
    label: str = ""


@dataclass
class Console:
    """The calculator's state. The drawing is a function of this and nothing else."""

    page: str = "quote"
    fitout_index: int = 0
    resin: str = "boatyard"
    """Which hull laminate system. Named after the resin for short."""
    frame_stock: str = "customer_trees"
    seam: str = "hose"
    ac: str = "window"
    insulated: bool = False
    stove: bool = False
    polyps: int | None = None
    scroll: int = 0
    selected: str = ""
    """Which declared constant the keyboard is editing, if any."""
    edit_buffer: str = ""
    message: str = ""
    regions: list[Region] = field(default_factory=list)
    width: int = 980
    height: int = 720

    # -- what is being priced -----------------------------------------
    @property
    def fitout_key(self) -> str:
        order = seed_model.FITOUT_ORDER
        return order[self.fitout_index % len(order)]

    def quote(self):
        return seed_model.quote(self.fitout_key, resin=self.resin,
                                frame_stock=self.frame_stock,
                                seam=self.seam, ac=self.ac,
                                polyps=self.polyps,
                                include=self.options())

    def options(self) -> tuple:
        """Which optional groups are switched on right now."""
        keep = list(seed_model.STANDARD_OPTIONS)
        if self.insulated:
            keep.append("insulation")
        if self.stove:
            keep.append("stove")
        return tuple(keep)

    def constants(self):
        return seed_model.external_constants()

    # -- input ---------------------------------------------------------
    def click(self, x: int, y: int, shift: bool = False) -> str:
        """Take a click in console coordinates. Returns what it did."""
        for region in reversed(self.regions):
            if region.rect.collidepoint(x, y):
                return self.act(region.action, shift)
        return ""

    def act(self, action: str, shift: bool = False) -> str:
        if not action:
            return ""
        head, _, rest = action.partition(":")

        if head == "page":
            self.page = rest
            self.scroll = 0
            self.selected = ""
            self.edit_buffer = ""
            return f"page {rest}"
        if head == "fitout":
            order = seed_model.FITOUT_ORDER
            step = 1 if rest == "next" else -1
            self.fitout_index = (self.fitout_index + step) % len(order)
            return f"seed {self.fitout_key}"
        if head == "pick":
            order = list(seed_model.FITOUT_ORDER)
            if rest in order:
                self.fitout_index = order.index(rest)
                self.page = "quote"
            return f"seed {rest}"
        if head == "resin":
            order = seed_model.laminate_keys()
            self.resin = order[(order.index(self.resin) + 1) % len(order)]
            return f"laminate {self.resin}"
        if head == "stock":
            order = seed_model.FRAME_STOCK
            self.frame_stock = order[
                (order.index(self.frame_stock) + 1) % len(order)]
            return f"frame {self.frame_stock.replace('_', ' ')}"
        if head == "seam":
            order = seed_model.SEAMS
            self.seam = order[(order.index(self.seam) + 1) % len(order)]
            return f"seam {self.seam}"
        if head == "ac":
            self.ac = ("mini_split" if self.ac == "window" else "window")
            return f"cooling {self.ac.replace('_', ' ')}"
        if head == "stock":
            pass
        if head == "insulation":
            self.insulated = not self.insulated
            return ("insulation bladders on" if self.insulated
                    else "insulation bladders off")
        if head == "stove":
            self.stove = not self.stove
            return "wood stove on" if self.stove else "wood stove off"
        if head == "polyp":
            spec = seed_model.fitout(self.fitout_key)
            current = spec.polyps if self.polyps is None else self.polyps
            self.polyps = max(0, min(8, current + (1 if rest == "up" else -1)))
            return f"panels {self.polyps}"
        if head == "scroll":
            step = ROWS_PER_PAGE if shift else 4
            self.scroll = max(0, self.scroll + (step if rest == "down"
                                                else -step))
            return ""
        if head == "select":
            self.selected = "" if self.selected == rest else rest
            self.edit_buffer = ""
            return f"editing {self.selected}" if self.selected else ""
        if head == "nudge":
            name, _, direction = rest.partition("|")
            factor = 0.25 if shift else STEP_FRACTION
            value = seed_model.declared(name)
            if value == 0.0:
                value = 1.0 if direction == "up" else 0.0
            else:
                value *= (1.0 + factor) if direction == "up" else (1.0 - factor)
            seed_model.set_override(name, max(0.0, value))
            return f"{name} = {seed_model.declared(name):,.4g}"
        if head == "reset":
            seed_model.clear_override(rest)
            return f"{rest} back to default"
        if head == "reset_all":
            for name, _value, _unit, _note in self.constants():
                seed_model.clear_override(name)
            return "every price back to default"
        if head == "save":
            path = seed_model.save_overrides()
            return f"saved {path.name}"
        if head == "load":
            loaded = seed_model.load_overrides()
            return f"loaded {len(loaded)} changed price(s)"
        if head == "export":
            return f"wrote {self.export().name}"
        if head == "close":
            return "close"
        return ""

    def key(self, unicode_char: str, keyname: str) -> str:
        """Typing, for the one thing worth typing: a price."""
        if not self.selected:
            return ""
        if keyname == "backspace":
            self.edit_buffer = self.edit_buffer[:-1]
            return ""
        if keyname in ("return", "enter"):
            try:
                value = float(self.edit_buffer)
            except ValueError:
                self.edit_buffer = ""
                return "not a number"
            seed_model.set_override(self.selected, value)
            name, self.selected, self.edit_buffer = self.selected, "", ""
            return f"{name} = {value:,.4g}"
        if keyname == "escape":
            self.selected, self.edit_buffer = "", ""
            return ""
        if unicode_char and (unicode_char.isdigit() or unicode_char == "."):
            if unicode_char == "." and "." in self.edit_buffer:
                return ""
            self.edit_buffer += unicode_char
        return ""

    # -- output ---------------------------------------------------------
    def export(self) -> Path:
        """Write the current quote out as a CSV, never over an old one."""
        from two_v_demo.deliverables import next_version_path

        EXPORT_DIR.mkdir(parents=True, exist_ok=True)
        result = self.quote()
        path = next_version_path(
            EXPORT_DIR / f"seed_quote_{self.fitout_key}.csv")
        lines = ["group,line,quantity,unit,unit cost,cost,rate source"]
        for group in result.groups:
            for line in group.lines:
                label = line.label.replace(",", ";")
                lines.append(
                    f"{group.label},{label},{line.quantity:.4f},{line.unit},"
                    f"{line.unit_cost:.4f},{line.cost:.2f},{line.source}")
        lines.extend([
            f"TOTAL,materials,,,,{result.material_cost:.2f},",
            f"TOTAL,labour hours,{result.labour_hours:.2f},hours,,"
            f"{result.labour_cost:.2f},labour_usd_per_hour",
            f"TOTAL,overhead,,,,{result.overhead:.2f},shop_overhead_fraction",
            f"TOTAL,warranty,,,,{result.warranty:.2f},"
            "warranty_reserve_fraction",
            f"TOTAL,cost to build,,,,{result.cost_to_build:.2f},",
            f"TOTAL,list price,,,,{result.price:.2f},gross_margin_fraction",
            f"TOTAL,delivered,,,,{result.delivered_price:.2f},freight_usd",
        ])
        path.write_text("\n".join(lines) + "\n", encoding="utf-8")
        return path


# ----------------------------------------------------------------------
# Drawing
# ----------------------------------------------------------------------

class ConsoleRenderer:
    """Turns a :class:`Console` into a surface, and records where to click."""

    def __init__(self, size: int = 15) -> None:
        pygame.font.init()
        self.mono = pygame.font.SysFont("consolas", size)
        self.mono_bold = pygame.font.SysFont("consolas", size, bold=True)
        self.title = pygame.font.SysFont("consolas", size + 4, bold=True)
        self.line_h = self.mono.get_linesize() + 3

    # -- pieces --------------------------------------------------------
    def _text(self, surface, x, y, text, colour=INK, font=None) -> None:
        surface.blit((font or self.mono).render(text, True, colour), (x, y))

    def _button(self, surface, console, rect, label, action, *,
                on: bool = False, colour=INK) -> None:
        pygame.draw.rect(surface, BUTTON_ON if on else BUTTON, rect,
                         border_radius=4)
        pygame.draw.rect(surface, BUTTON_EDGE, rect, width=1, border_radius=4)
        text = self.mono_bold.render(label, True, ACCENT if on else colour)
        surface.blit(text, (rect.x + (rect.w - text.get_width()) // 2,
                            rect.y + (rect.h - text.get_height()) // 2))
        console.regions.append(Region(rect, action, label))

    # -- the whole thing -----------------------------------------------
    def build(self, console: Console) -> pygame.Surface:
        console.regions = []
        width, height = console.width, console.height
        surface = pygame.Surface((width, height), pygame.SRCALPHA)
        surface.fill(BG)
        pygame.draw.rect(surface, EDGE, surface.get_rect(), width=1,
                         border_radius=8)

        result = console.quote()
        geo = result.geometry

        self._text(surface, 16, 12,
                   f"SEED DOME COST  --  {result.fitout.label}", ACCENT,
                   self.title)
        self._text(surface, 16, 36,
                   f"{geo.diameter_ft:.2f} ft across, {geo.height_ft:.2f} ft "
                   f"tall, {geo.floor_decagon_sqft:.0f} sq ft of floor, "
                   f"{geo.member_count} members, "
                   f"{sum(f.count for f in geo.faces)} panels", DIM)

        # Page tabs.
        x = 16
        for page in PAGES:
            rect = pygame.Rect(x, 60, 86, 26)
            self._button(surface, console, rect, PAGE_LABEL[page],
                         f"page:{page}", on=console.page == page)
            x += 92
        self._button(surface, console, pygame.Rect(width - 74, 60, 58, 26),
                     "CLOSE", "close:", colour=WARN)
        if console.page in ("quote", "prices"):
            self._button(surface, console,
                         pygame.Rect(width - 142, 60, 30, 26), "^",
                         "scroll:up")
            self._button(surface, console,
                         pygame.Rect(width - 108, 60, 30, 26), "v",
                         "scroll:down")

        # The four switches that change what is being priced.
        x = 16
        y = 94
        panels = (result.fitout.polyps if console.polyps is None
                  else console.polyps)
        # Anything with two directions gets two buttons. A right-click or a
        # modifier would be quicker to write and impossible to guess.
        self._button(surface, console, pygame.Rect(x, y, 24, 26), "<",
                     "fitout:prev")
        self._button(surface, console, pygame.Rect(x + 26, y, 170, 26),
                     result.fitout.label, f"page:seeds")
        self._button(surface, console, pygame.Rect(x + 198, y, 24, 26), ">",
                     "fitout:next")
        x += 230
        for label, action, w, on in (
                (f"hull: {console.resin}", "resin:", 160,
                 console.resin != "boatyard"),
                (f"frame: {console.frame_stock.replace('_', ' ')}", "stock:",
                 190, console.frame_stock != "customer_trees"),
                (f"seam: {console.seam}", "seam:", 118,
                 console.seam != "hose")):
            self._button(surface, console, pygame.Rect(x, y, w, 26), label,
                         action, on=on)
            x += w + 8
        self._button(surface, console, pygame.Rect(x, y, 24, 26), "-",
                     "polyp:down")
        self._button(surface, console, pygame.Rect(x + 26, y, 108, 26),
                     f"panels: {panels}", "")
        self._button(surface, console, pygame.Rect(x + 136, y, 24, 26), "+",
                     "polyp:up")

        # Second switch row: the choices that change what is in the box.
        x, y = 16, 124
        for label, action, w, on in (
                (f"cooling: {'window' if console.ac == 'window' else 'mini-split'}",
                 "ac:", 180, console.ac != "window"),
                (f"insulation: {'yes' if console.insulated else 'no'}",
                 "insulation:", 168, console.insulated),
                (f"wood stove: {'yes' if console.stove else 'no'}",
                 "stove:", 168, console.stove)):
            self._button(surface, console, pygame.Rect(x, y, w, 26), label,
                         action, on=on)
            x += w + 8
        self._text(surface, x + 6, y + 5,
                   f"pad, host side:  ${result.pad_cost:,.0f}", MONEY)

        # The body stops short of the footer and the note line under it, so
        # a long table never runs into the buttons that control it.
        body = pygame.Rect(16, 160, width - 32, height - 160 - 88)
        drawer = {
            "quote": self._page_quote,
            "prices": self._page_prices,
            "levers": self._page_levers,
            "seeds": self._page_seeds,
        }[console.page]
        drawer(surface, console, body, result)

        # Footer: the actions, and whatever the last click said.
        foot_y = height - 36
        self._button(surface, console, pygame.Rect(16, foot_y, 74, 26),
                     "SAVE", "save:", colour=MONEY)
        self._button(surface, console, pygame.Rect(96, foot_y, 74, 26),
                     "LOAD", "load:")
        self._button(surface, console, pygame.Rect(176, foot_y, 90, 26),
                     "EXPORT", "export:")
        self._button(surface, console, pygame.Rect(272, foot_y, 90, 26),
                     "DEFAULTS", "reset_all:", colour=WARN)
        if console.message:
            self._text(surface, 374, foot_y + 5, console.message[:70], DIM)
        return surface

    # -- pages ----------------------------------------------------------
    def _page_quote(self, surface, console, body, result) -> None:
        y = body.y
        col = body.x
        money_x = body.right - 110
        qty_x = body.right - 300

        rows: list[tuple[str, str, str, tuple[int, int, int], object]] = []
        for group in result.dome_groups:
            rows.append((group.label.upper(), "", "", ACCENT, self.mono_bold))
            for line in group.lines:
                rows.append((f"   {line.label}",
                             f"{line.quantity:,.1f} {line.unit}",
                             f"${line.cost:,.0f}", DIM, self.mono))
            rows.append((f"   {group.label} subtotal", "",
                         f"${group.cost:,.0f}", INK, self.mono))
            rows.append(("", "", "", DIM, self.mono))

        visible = (body.height // self.line_h) - 9
        total = len(rows)
        console.scroll = max(0, min(console.scroll, max(0, total - visible)))
        for label, qty, money, colour, font in rows[console.scroll:
                                                    console.scroll + visible]:
            if label:
                self._text(surface, col, y, label[:58], colour, font)
                if qty:
                    self._text(surface, qty_x, y, f"{qty:>16}", FAINT)
                if money:
                    self._text(surface, money_x, y, f"{money:>10}", colour,
                               font)
            y += self.line_h

        if total > visible:
            self._text(surface, body.x, body.bottom + 24,
                       f"line {console.scroll + 1}-"
                       f"{min(total, console.scroll + visible)} of {total}"
                       "   --   use the arrows by CLOSE", FAINT)

        y = body.bottom - self.line_h * 7
        pygame.draw.line(surface, EDGE, (body.x, y - 6), (body.right, y - 6))
        summary = (
            ("materials", result.material_cost, DIM),
            (f"labour, {result.labour_hours:,.0f} hours", result.labour_cost,
             DIM),
            ("overhead and warranty", result.overhead + result.warranty, DIM),
            ("COST TO BUILD", result.cost_to_build, INK),
            (f"LIST PRICE at "
             f"{seed_model.declared('gross_margin_fraction') * 100:.0f}% margin",
             result.price, MONEY),
            (f"delivered, and ${result.price_per_sqft:,.0f} a square foot",
             result.delivered_price, MONEY),
            (f"the pad, which the landowner built and keeps",
             result.pad_cost, DIM),
        )
        for label, amount, colour in summary:
            font = self.mono_bold if colour is not DIM else self.mono
            self._text(surface, body.x, y, label, colour, font)
            self._text(surface, money_x, y, f"${amount:>9,.0f}", colour, font)
            y += self.line_h

    def _page_prices(self, surface, console, body, result) -> None:
        rows = list(console.constants())
        visible = body.height // self.line_h
        console.scroll = max(0, min(console.scroll, max(0, len(rows) - visible)))
        y = body.y
        for name, default, unit, note in rows[console.scroll:
                                              console.scroll + visible]:
            value = seed_model.declared(name)
            changed = seed_model.is_overridden(name)
            editing = console.selected == name
            colour = WARN if changed else DIM
            if editing:
                colour = ACCENT
            row = pygame.Rect(body.x, y - 1, body.width - 150, self.line_h)
            console.regions.append(Region(row, f"select:{name}", name))
            if editing:
                pygame.draw.rect(surface, (22, 46, 64), row, border_radius=3)
            shown = console.edit_buffer + "_" if editing else f"{value:,.4g}"
            self._text(surface, body.x + 4, y, name[:34], colour,
                       self.mono_bold if changed else self.mono)
            self._text(surface, body.x + 290, y, f"{shown:>14}", INK)
            self._text(surface, body.x + 410, y, unit[:22], FAINT)
            self._button(surface, console,
                         pygame.Rect(body.right - 116, y - 1, 24, self.line_h - 2),
                         "-", f"nudge:{name}|down")
            self._button(surface, console,
                         pygame.Rect(body.right - 88, y - 1, 24, self.line_h - 2),
                         "+", f"nudge:{name}|up")
            if changed:
                self._button(surface, console,
                             pygame.Rect(body.right - 60, y - 1, 52,
                                         self.line_h - 2),
                             "undo", f"reset:{name}", colour=WARN)
            else:
                self._text(surface, body.right - 56, y,
                           "default" if not note.startswith("borrowed")
                           else "borrowed", FAINT)
            y += self.line_h

        # Whatever is selected, say WHY it holds the value it does. A price
        # with no reason attached is the thing this whole model exists to
        # avoid, and it should not be editable without the reason in view.
        if console.selected:
            note = seed_model.note_of(console.selected)
            self._text(surface, body.x, body.bottom + 6,
                       f"{console.selected}  ({seed_model.units_of(console.selected)})"
                       "   type digits, Enter to set, Esc to cancel", ACCENT)
            self._text(surface, body.x, body.bottom + 6 + self.line_h,
                       note[:108], FAINT)
        else:
            self._text(surface, body.x, body.bottom + 6,
                       "click a row to type a value; + and - nudge it 5% "
                       "(hold Shift for 25%)", FAINT)
            self._text(surface, body.x, body.bottom + 6 + self.line_h,
                       f"{len([1 for n, _v, _u, _t in rows if seed_model.is_overridden(n)])}"
                       f" of {len(rows)} changed from the default; SAVE "
                       "writes them to seed_prices.json", FAINT)

    def _page_levers(self, surface, console, body, result) -> None:
        # Redrawn from the standard article every time, so a lever's saving
        # is always measured against the same baseline the QUOTE page shows.
        base = seed_model.quote("stem_cell").price
        y = body.y
        self._text(surface, body.x, y,
                   "Each change on its own, against the standard stem cell.",
                   DIM)
        y += self.line_h
        self._text(surface, body.x, y, f"{'standard stem cell':<52}", INK,
                   self.mono_bold)
        self._text(surface, body.right - 210, y, f"${base:>10,.0f}", INK,
                   self.mono_bold)
        y += self.line_h * 2

        for lever, priced, saving in seed_model.lever_prices():
            colour = MONEY if saving > 0 else BAD
            self._text(surface, body.x, y, lever.label[:52], DIM)
            self._text(surface, body.right - 210, y, f"${priced:>10,.0f}", INK)
            sign = "-" if saving >= 0 else "+"
            self._text(surface, body.right - 96, y,
                       f"{sign}${abs(saving):>8,.0f}", colour)
            y += self.line_h

        build, price = seed_model.floor_price()
        y += self.line_h
        pygame.draw.line(surface, EDGE, (body.x, y - 6), (body.right, y - 6))
        geo = result.geometry
        for label, amount, colour in (
                ("every saving lever at once", price, MONEY),
                ("which costs, to build", build, INK),
                (f"per square foot of "
                 f"{geo.floor_decagon_sqft:.0f} sq ft of floor",
                 price / geo.floor_decagon_sqft, MONEY)):
            self._text(surface, body.x, y, label[:52], colour, self.mono_bold)
            self._text(surface, body.right - 210, y, f"${amount:>10,.2f}",
                       colour, self.mono_bold)
            y += self.line_h

    def _page_seeds(self, surface, console, body, result) -> None:
        y = body.y
        self._text(surface, body.x, y,
                   f"{'seed':<20}{'shape':<12}{'build':>11}{'price':>11}"
                   f"{'$/sq ft':>10}  modules", ACCENT, self.mono_bold)
        y += self.line_h * 2
        rows = []
        for key in seed_model.FITOUT_ORDER:
            priced = seed_model.quote(key, resin=console.resin,
                                      frame_stock=console.frame_stock)
            rows.append((priced.price, key, priced))
        rows.sort(key=lambda row: row[0])
        for _price, key, priced in rows:
            spec = priced.fitout
            on = key == console.fitout_key
            row = pygame.Rect(body.x, y - 2, body.width, self.line_h)
            console.regions.append(Region(row, f"pick:{key}", key))
            if on:
                pygame.draw.rect(surface, (22, 46, 64), row, border_radius=3)
            colour = ACCENT if on else DIM
            self._text(surface, body.x + 4, y,
                       f"{spec.label:<20}{spec.shape:<12}"
                       f"{'$' + format(priced.cost_to_build, ',.0f'):>11}"
                       f"{'$' + format(priced.price, ',.0f'):>11}"
                       f"{priced.price_per_sqft:>10,.2f}  "
                       f"{len(spec.modules)}", colour)
            y += self.line_h
        y += self.line_h
        spec = seed_model.fitout(console.fitout_key)
        self._text(surface, body.x, y, spec.blurb[:88], FAINT)
        y += self.line_h
        if len(spec.blurb) > 88:
            self._text(surface, body.x, y, spec.blurb[88:176], FAINT)


# ----------------------------------------------------------------------
# The strip of buttons that opens it
# ----------------------------------------------------------------------

TOOLBAR_BUTTONS: tuple[tuple[str, str], ...] = (
    ("$ COST", "page:quote"),
    ("PRICES", "page:prices"),
    ("LEVERS", "page:levers"),
    ("SEEDS", "page:seeds"),
)
"""What the toolbar offers. Every one of them opens the same calculator on a
different page, because a tool with four buttons that open four windows is
four tools."""


class Toolbar:
    """A small always-visible strip: the way into the calculator.

    Kept separate from the console so a 3-D tool can show the way in without
    paying to draw the whole calculator every frame."""

    def __init__(self, size: int = 15) -> None:
        pygame.font.init()
        self.font = pygame.font.SysFont("consolas", size, bold=True)
        self.regions: list[Region] = []
        self.height = 32

    def build(self, open_page: str | None = None) -> pygame.Surface:
        self.regions = []
        pad, gap = 10, 6
        widths = [max(74, self.font.size(label)[0] + 22)
                  for label, _action in TOOLBAR_BUTTONS]
        width = pad * 2 + sum(widths) + gap * (len(widths) - 1)
        surface = pygame.Surface((width, self.height), pygame.SRCALPHA)
        surface.fill((8, 12, 18, 208))
        pygame.draw.rect(surface, EDGE, surface.get_rect(), width=1,
                         border_radius=6)
        x = pad
        for (label, action), w in zip(TOOLBAR_BUTTONS, widths):
            rect = pygame.Rect(x, 5, w, self.height - 10)
            on = open_page is not None and action == f"page:{open_page}"
            pygame.draw.rect(surface, BUTTON_ON if on else BUTTON, rect,
                             border_radius=4)
            pygame.draw.rect(surface, BUTTON_EDGE, rect, width=1,
                             border_radius=4)
            text = self.font.render(label, True, ACCENT if on else INK)
            surface.blit(text, (rect.x + (rect.w - text.get_width()) // 2,
                                rect.y + (rect.h - text.get_height()) // 2))
            self.regions.append(Region(rect, action, label))
            x += w + gap
        return surface

    def hit(self, x: int, y: int) -> str:
        for region in self.regions:
            if region.rect.collidepoint(x, y):
                return region.action
        return ""


# ----------------------------------------------------------------------
# Proof
# ----------------------------------------------------------------------

def validate_seed_console() -> None:
    """Every page must draw, and every button must do what it says."""
    import os

    os.environ.setdefault("SDL_VIDEODRIVER", "dummy")
    pygame.init()
    pygame.display.set_mode((32, 32))
    renderer = ConsoleRenderer()
    console = Console()

    for page in PAGES:
        console.act(f"page:{page}")
        surface = renderer.build(console)
        assert surface.get_size() == (console.width, console.height)
        assert console.regions, page

    # The switches have to change the price, or they are decoration.
    console.act("page:quote")
    before = console.quote().price
    # Every laminate system has to price, and cycling all the way round
    # has to come back to where it started.
    seen = set()
    for _ in seed_model.laminate_keys():
        console.act("resin:")
        seen.add(console.resin)
        assert console.quote().price > 0.0
    assert seen == set(seed_model.laminate_keys())
    assert console.resin == "boatyard"
    assert abs(console.quote().price - before) < 1e-6

    # The switches that change what is in the box.
    console.act("ac:")
    assert console.ac == "mini_split" and console.quote().price > before
    console.act("ac:")
    console.act("insulation:")
    assert console.insulated and console.quote().price > before
    console.act("insulation:")
    console.act("stove:")
    assert console.stove and console.quote().price > before
    console.act("stove:")
    assert abs(console.quote().price - before) < 1e-6

    # Cycling the frame stock all the way round returns to the customer's
    # own trees, which is the standard article.
    for _ in seed_model.FRAME_STOCK:
        console.act("stock:")
    assert console.frame_stock == "customer_trees"

    console.act("seam:")
    assert console.seam != "hose"
    assert abs(console.quote().price - before) > 1.0
    console.act("seam:"); console.act("seam:")
    assert console.seam == "hose"

    console.act("fitout:next")
    assert console.fitout_key != "stem_cell"
    console.act("fitout:prev")
    assert console.fitout_key == "stem_cell"

    console.act("polyp:up")
    assert console.quote().price > before
    console.polyps = None

    # Nudging a price has to move the quote and be undoable.
    console.act("nudge:labour_usd_per_hour|up")
    assert seed_model.is_overridden("labour_usd_per_hour")
    assert console.quote().price > before
    console.act("reset:labour_usd_per_hour")
    assert not seed_model.is_overridden("labour_usd_per_hour")
    assert abs(console.quote().price - before) < 1e-6

    # Typing a price: select, type, Enter.
    #
    # The price typed here has to be one the *standard article* actually
    # contains, or the quote does not move and this proves nothing. That is
    # not hypothetical: this test used to type a polyester resin price, and
    # when the standard article became the shower cap -- which has no resin
    # in it -- the quote stopped moving and the assertion failed. Worse, it
    # failed *after* the override was applied and before it was reset, so the
    # inflated price leaked into every selftest that ran afterwards and three
    # unrelated modules reported a $10,173 laminate.
    #
    # So: pick the column housing, which the standard article carries
    # whichever shell it wears, and reset in a finally so a failure here can
    # never poison anything downstream. (The frame's own timber will not do:
    # it defaults to the buyer's standing trees and costs nothing.)
    typed = "column_housing_usd"
    console.act("page:prices")
    console.act("select:" + typed)
    assert console.selected == typed
    try:
        for char in "9", "9", ".", "5":
            console.key(char, char)
        console.key("", "return")
        assert abs(seed_model.declared(typed) - 99.5) < 1e-9
        # Changed, not increased. 99.5 happened to be a rise on the resin
        # price this test used to type and is a fall on most others, so
        # asserting a direction tests the constant that was picked rather
        # than the thing under test -- which is that a typed price reaches
        # the quote at all.
        assert abs(console.quote().price - before) > 1.0, (
            f"typing a price for {typed!r} did not move the quote; it is not "
            "in the standard article any more")
    finally:
        console.act("reset_all:")
    assert abs(console.quote().price - before) < 1e-6

    # A click has to land on the button that was drawn there.
    console.act("page:quote")
    renderer.build(console)
    target = next(r for r in console.regions if r.action == "page:prices")
    console.click(target.rect.centerx, target.rect.centery)
    assert console.page == "prices"

    # Export writes a new file every time and never over an old one.
    console.act("page:quote")
    first = console.export()
    second = console.export()
    assert first.exists() and second.exists() and first != second
    for path in (first, second):
        assert "cost to build" in path.read_text(encoding="utf-8")
        path.unlink()

    # The toolbar has to be clickable, and has to say which page is open.
    bar = Toolbar()
    surface = bar.build(open_page="prices")
    assert surface.get_width() > 200 and surface.get_height() == bar.height
    assert len(bar.regions) == len(TOOLBAR_BUTTONS)
    spot = next(r for r in bar.regions if r.action == "page:levers")
    assert bar.hit(spot.rect.centerx, spot.rect.centery) == "page:levers"
    assert bar.hit(-5, -5) == ""

    pygame.quit()


if __name__ == "__main__":
    validate_seed_console()
    print("seed console ok: "
          f"{len(PAGES)} pages, "
          f"{len(seed_model.external_constants())} inputs, "
          f"{len(seed_model.FITOUT_ORDER)} seeds")
