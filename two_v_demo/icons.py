"""Flat pictograms for the overlay: a chainsaw at the fell line, a fuel can beside a
number, a calendar beside a day count.

A figure on its own asks the viewer to remember what it counts. The same figure with
a small picture of the thing beside it does not, which is most of what a good
explainer's number card is doing. These are drawn with pygame's primitives rather
than loaded from image files, for the same reasons the timber is procedural: they
scale to any resolution, take any colour a theme gives them, and look identical in
every frame and every render.

Every icon is drawn in a unit box -- x to the right, y up, both from -1 to 1 -- by a
:class:`Pen` that maps that box onto the screen at any centre, size and angle. So an
icon can be spun, pulsed or faded by the caller without the icon knowing.
"""

from __future__ import annotations

import math
from dataclasses import dataclass
from typing import Callable


Colour = tuple[int, int, int]


def shade(colour: Colour, factor: float) -> Colour:
    """Darken (factor < 1) or lighten (factor > 1) toward black or white."""
    if factor <= 1.0:
        return tuple(int(channel * factor) for channel in colour)
    lift = factor - 1.0
    return tuple(int(channel + (255 - channel) * min(1.0, lift)) for channel in colour)


class Pen:
    """Unit-box coordinates in, pixels out."""

    def __init__(self, pg, surface, centre: tuple[float, float], size: float,
                 angle_deg: float = 0.0, mirror: bool = False):
        self.pg = pg
        self.surface = surface
        self.cx, self.cy = centre
        self.r = size * 0.5
        self.cos = math.cos(math.radians(angle_deg))
        self.sin = math.sin(math.radians(angle_deg))
        self.mirror = mirror

    def p(self, x: float, y: float) -> tuple[int, int]:
        if self.mirror:
            x = -x  # facing the other way, not upside down
        rx = x * self.cos - y * self.sin
        ry = x * self.sin + y * self.cos
        return (int(round(self.cx + rx * self.r)), int(round(self.cy - ry * self.r)))

    def w(self, width: float) -> int:
        return max(1, int(round(width * self.r)))

    def poly(self, points, colour: Colour) -> None:
        self.pg.draw.polygon(self.surface, colour, [self.p(x, y) for x, y in points])

    def line(self, a, b, colour: Colour, width: float = 0.08) -> None:
        self.pg.draw.line(self.surface, colour, self.p(*a), self.p(*b), self.w(width))
        # Round the ends, or thick strokes meet at a visible notch.
        for x, y in (a, b):
            self.pg.draw.circle(self.surface, colour, self.p(x, y),
                                max(1, self.w(width) // 2))

    def lines(self, points, colour: Colour, width: float = 0.08,
              closed: bool = False) -> None:
        seq = list(points) + ([points[0]] if closed else [])
        for a, b in zip(seq, seq[1:]):
            self.line(a, b, colour, width)

    def circle(self, x: float, y: float, radius: float, colour: Colour,
               width: float = 0.0) -> None:
        self.pg.draw.circle(self.surface, colour, self.p(x, y),
                            max(1, int(round(radius * self.r))),
                            self.w(width) if width else 0)

    def box(self, x0: float, y0: float, x1: float, y1: float, colour: Colour) -> None:
        self.poly(((x0, y0), (x1, y0), (x1, y1), (x0, y1)), colour)

    def arc_points(self, x: float, y: float, radius: float, start_deg: float,
                   end_deg: float, steps: int = 18) -> list[tuple[float, float]]:
        return [(x + radius * math.cos(math.radians(start_deg + (end_deg - start_deg)
                                                    * i / steps)),
                 y + radius * math.sin(math.radians(start_deg + (end_deg - start_deg)
                                                    * i / steps)))
                for i in range(steps + 1)]


# ----------------------------------------------------------------------
# The icons
# ----------------------------------------------------------------------

def _chainsaw(pen: Pen, c: Colour) -> None:
    steel = (190, 198, 208)
    pen.box(-0.15, -0.16, 0.86, 0.10, steel)                    # the bar
    pen.circle(0.86, -0.03, 0.13, steel)                        # its nose
    for i in range(9):                                          # chain teeth
        x = -0.08 + i * 0.11
        pen.poly(((x, 0.10), (x + 0.07, 0.10), (x + 0.02, 0.19)), shade(steel, 0.7))
        pen.poly(((x, -0.16), (x + 0.07, -0.16), (x + 0.02, -0.25)),
                 shade(steel, 0.7))
    pen.poly(((-0.95, -0.36), (-0.12, -0.36), (-0.05, 0.05), (-0.12, 0.38),
              (-0.9, 0.38), (-0.98, 0.1)), c)                   # the engine body
    pen.lines(((-0.82, 0.38), (-0.72, 0.74), (-0.28, 0.74), (-0.2, 0.38)),
              shade(c, 0.6), 0.1)                               # top handle
    pen.line((-0.1, 0.38), (0.02, 0.62), shade(c, 0.6), 0.09)   # hand guard
    pen.circle(-0.62, -0.02, 0.14, shade(c, 0.55))              # starter cover


def _pine(pen: Pen, c: Colour) -> None:
    pen.box(-0.09, -1.0, 0.09, -0.52, (122, 84, 50))
    for base, top, half in ((-0.62, 0.12, 0.72), (-0.18, 0.55, 0.57),
                            (0.26, 0.98, 0.42)):
        pen.poly(((-half, base), (half, base), (0.0, top)), c)
        pen.poly(((0.0, base), (half, base), (0.0, top)), shade(c, 0.75))


def _log(pen: Pen, c: Colour) -> None:
    bark = (116, 80, 48)
    pen.box(-0.86, -0.34, 0.55, 0.34, bark)
    pen.circle(-0.86, 0.0, 0.34, shade(bark, 0.8))
    end = (214, 170, 110)
    for radius, colour in ((0.34, bark), (0.3, end), (0.2, shade(end, 0.85)),
                           (0.1, end)):
        pen.circle(0.55, 0.0, radius, colour)
    pen.circle(0.55, 0.0, 0.03, shade(end, 0.6))


def _slice(pen: Pen, c: Colour) -> None:
    """A bucked section seen end-on: bark, rings, pith."""
    end = (214, 170, 110)
    pen.circle(0, 0, 0.92, (116, 80, 48))
    pen.circle(0, 0, 0.82, end)
    for radius in (0.64, 0.46, 0.28):
        pen.circle(0, 0, radius, shade(end, 0.78), 0.035)
    pen.circle(0, 0, 0.06, shade(end, 0.5))


def _split(pen: Pen, c: Colour) -> None:
    """The same end view, split into eight."""
    _slice(pen, c)
    for i in range(4):
        angle = math.radians(i * 45.0)
        dx, dy = 0.92 * math.cos(angle), 0.92 * math.sin(angle)
        pen.line((-dx, -dy), (dx, dy), c, 0.07)


def _wedge(pen: Pen, c: Colour) -> None:
    """One eighth of the section, lifted out."""
    pen.circle(0, 0, 0.9, shade(c, 0.35), 0.05)
    points = [(0.0, 0.0)] + pen.arc_points(0.0, 0.0, 0.9, 67.5, 112.5, 8)
    lifted = [(x, y + 0.08) for x, y in points]
    pen.poly(lifted, (214, 170, 110))
    pen.lines(pen.arc_points(0.0, 0.08, 0.9, 67.5, 112.5, 8), (116, 80, 48), 0.09)
    pen.lines(((0.0, 0.08), lifted[1]), c, 0.04)
    pen.lines(((0.0, 0.08), lifted[-1]), c, 0.04)


def _fuel(pen: Pen, c: Colour) -> None:
    pen.poly(((-0.6, -0.92), (0.62, -0.92), (0.62, 0.52), (0.36, 0.72),
              (-0.6, 0.72)), c)
    pen.poly(((-0.55, 0.62), (-0.72, 0.98), (-0.52, 0.98), (-0.36, 0.62)),
             shade(c, 0.7))                                    # spout
    pen.box(-0.05, 0.42, 0.42, 0.58, shade(c, 0.45))            # handle slot
    pen.lines(((-0.4, -0.7), (0.4, 0.2)), shade(c, 0.7), 0.07)
    pen.lines(((-0.4, 0.2), (0.4, -0.7)), shade(c, 0.7), 0.07)


def _calendar(pen: Pen, c: Colour) -> None:
    pen.box(-0.82, -0.86, 0.82, 0.66, (236, 240, 244))
    pen.box(-0.82, 0.36, 0.82, 0.66, c)
    for x in (-0.45, 0.45):
        pen.line((x, 0.56), (x, 0.9), shade(c, 0.6), 0.1)
    for row in range(3):
        for col in range(4):
            x = -0.62 + col * 0.4
            y = 0.1 - row * 0.32
            pen.box(x - 0.11, y - 0.1, x + 0.11, y + 0.1,
                    c if (row, col) == (1, 2) else (150, 160, 172))


def _clock(pen: Pen, c: Colour) -> None:
    pen.circle(0, 0, 0.92, c)
    pen.circle(0, 0, 0.78, (236, 240, 244))
    for i in range(12):
        angle = math.radians(i * 30.0)
        pen.line((0.66 * math.cos(angle), 0.66 * math.sin(angle)),
                 (0.74 * math.cos(angle), 0.74 * math.sin(angle)), (90, 100, 112),
                 0.05)
    pen.line((0, 0), (0.0, 0.52), (30, 36, 44), 0.1)
    pen.line((0, 0), (0.38, -0.2), (30, 36, 44), 0.1)
    pen.circle(0, 0, 0.07, c)


def _dollar(pen: Pen, c: Colour) -> None:
    pen.circle(0, 0, 0.92, c)
    ink = shade(c, 0.35)
    upper = pen.arc_points(0.0, 0.22, 0.3, 20.0, 270.0, 16)
    lower = pen.arc_points(0.0, -0.22, 0.3, 90.0, -160.0, 16)
    pen.lines(upper, ink, 0.12)
    pen.lines(lower, ink, 0.12)
    pen.line((0.0, 0.7), (0.0, -0.7), ink, 0.1)


def _dome(pen: Pen, c: Colour) -> None:
    base = -0.62
    ring = [(0.92 * math.cos(math.radians(a)), base + 0.92 * math.sin(math.radians(a)))
            for a in (180, 150, 120, 90, 60, 30, 0)]
    mid = [(0.56 * math.cos(math.radians(a)), base + 0.82 * math.sin(math.radians(a)))
           for a in (165, 105, 75, 15)]
    pen.lines(ring, c, 0.07)
    pen.line(ring[0], ring[-1], c, 0.07)
    for a, b in ((ring[0], mid[0]), (mid[0], ring[1]), (mid[0], mid[1]),
                 (mid[1], ring[3]), (ring[3], mid[2]), (mid[1], mid[2]),
                 (mid[2], mid[3]), (mid[3], ring[5]), (mid[3], ring[6]),
                 (mid[1], ring[2]), (mid[2], ring[4])):
        pen.line(a, b, c, 0.05)


def _ruler(pen: Pen, c: Colour) -> None:
    pen.box(-0.95, -0.28, 0.95, 0.28, c)
    for i in range(13):
        x = -0.85 + i * 0.1417
        pen.line((x, 0.28), (x, 0.28 - (0.26 if i % 4 == 0 else 0.14)),
                 shade(c, 0.4), 0.04)


def _person(pen: Pen, c: Colour) -> None:
    pen.circle(0.0, 0.62, 0.24, c)
    pen.poly(((-0.42, 0.3), (0.42, 0.3), (0.3, -0.36), (-0.3, -0.36)), c)
    pen.line((-0.18, -0.34), (-0.26, -0.95), c, 0.16)
    pen.line((0.18, -0.34), (0.26, -0.95), c, 0.16)


def _truck(pen: Pen, c: Colour) -> None:
    pen.box(-0.95, -0.4, 0.2, 0.28, c)                          # the bed
    pen.poly(((0.22, -0.4), (0.95, -0.4), (0.95, 0.05), (0.72, 0.4),
              (0.22, 0.4)), shade(c, 0.8))                      # the cab
    pen.poly(((0.42, 0.06), (0.82, 0.06), (0.66, 0.3), (0.42, 0.3)),
             (200, 225, 240))
    for x in (-0.6, 0.6):
        pen.circle(x, -0.46, 0.2, (40, 44, 50))
        pen.circle(x, -0.46, 0.08, (170, 176, 184))


def _factory(pen: Pen, c: Colour) -> None:
    pen.box(-0.95, -0.85, 0.95, 0.05, c)
    for i in range(3):
        x = -0.95 + i * 0.63
        pen.poly(((x, 0.05), (x + 0.63, 0.05), (x + 0.63, 0.45)), shade(c, 0.8))
    pen.box(0.55, 0.05, 0.75, 0.9, shade(c, 0.65))
    for x in (-0.6, -0.05, 0.5):
        pen.box(x - 0.14, -0.55, x + 0.14, -0.25, (200, 225, 240))


def _board(pen: Pen, c: Colour) -> None:
    wood = (214, 170, 110)
    pen.poly(((-0.95, -0.1), (0.55, 0.3), (0.95, 0.12), (-0.55, -0.28)), wood)
    pen.poly(((-0.55, -0.28), (0.95, 0.12), (0.95, -0.02), (-0.55, -0.42)),
             shade(wood, 0.78))
    pen.poly(((-0.95, -0.1), (-0.55, -0.28), (-0.55, -0.42), (-0.95, -0.24)),
             shade(wood, 0.62))


def _house(pen: Pen, c: Colour) -> None:
    pen.box(-0.7, -0.9, 0.7, 0.2, c)
    pen.poly(((-0.9, 0.18), (0.9, 0.18), (0.0, 0.9)), shade(c, 0.75))
    pen.box(-0.16, -0.9, 0.16, -0.3, shade(c, 0.45))


def _drop(pen: Pen, c: Colour) -> None:
    pen.circle(0.0, -0.3, 0.58, c)
    pen.poly(((-0.5, -0.02), (0.5, -0.02), (0.0, 0.95)), c)
    pen.circle(-0.2, -0.38, 0.14, shade(c, 1.6))


def _bolt(pen: Pen, c: Colour) -> None:
    pen.poly(((0.2, 0.95), (-0.55, -0.08), (-0.05, -0.08), (-0.25, -0.95),
              (0.55, 0.12), (0.05, 0.12)), c)


def _check(pen: Pen, c: Colour) -> None:
    pen.lines(((-0.7, 0.0), (-0.2, -0.55), (0.75, 0.6)), c, 0.2)


def _cross(pen: Pen, c: Colour) -> None:
    pen.line((-0.6, -0.6), (0.6, 0.6), c, 0.2)
    pen.line((-0.6, 0.6), (0.6, -0.6), c, 0.2)


def _arrow(pen: Pen, c: Colour) -> None:
    pen.poly(((-0.9, -0.18), (0.25, -0.18), (0.25, -0.5), (0.95, 0.0),
              (0.25, 0.5), (0.25, 0.18), (-0.9, 0.18)), c)


def _sun(pen: Pen, c: Colour) -> None:
    for i in range(8):
        angle = math.radians(i * 45.0)
        pen.line((0.55 * math.cos(angle), 0.55 * math.sin(angle)),
                 (0.9 * math.cos(angle), 0.9 * math.sin(angle)), c, 0.1)
    pen.circle(0, 0, 0.42, c)


def _flame(pen: Pen, c: Colour) -> None:
    """A flame: what a tree is worth when it is valued only for the heat in it."""
    pen.poly(((0.0, 0.95), (0.3, 0.52), (0.58, 0.12), (0.64, -0.3), (0.46, -0.72),
              (0.0, -0.92), (-0.46, -0.72), (-0.64, -0.3), (-0.58, 0.12),
              (-0.26, 0.4), (-0.12, 0.62)), c)
    pen.poly(((0.02, 0.28), (0.22, -0.02), (0.3, -0.38), (0.14, -0.7), (0.0, -0.76),
              (-0.14, -0.7), (-0.3, -0.38), (-0.2, -0.06)), shade(c, 1.7))


@dataclass(frozen=True)
class Icon:
    key: str
    label: str
    draw: Callable[[Pen, Colour], None]
    tint: Colour
    """The colour the icon has when a caller does not choose one."""


ICONS: dict[str, Icon] = {icon.key: icon for icon in (
    Icon("chainsaw", "chainsaw", _chainsaw, (255, 140, 40)),
    Icon("pine", "a pine tree", _pine, (60, 150, 80)),
    Icon("log", "a log", _log, (116, 80, 48)),
    Icon("slice", "a bucked section, end-on", _slice, (116, 80, 48)),
    Icon("split", "a section split into eight", _split, (40, 44, 50)),
    Icon("wedge", "one eighth of a section", _wedge, (116, 80, 48)),
    Icon("fuel", "a fuel can", _fuel, (220, 60, 50)),
    Icon("calendar", "a calendar", _calendar, (61, 170, 255)),
    Icon("clock", "a clock", _clock, (61, 170, 255)),
    Icon("dollar", "money", _dollar, (111, 210, 120)),
    Icon("dome", "a geodesic dome", _dome, (61, 211, 255)),
    Icon("ruler", "a measurement", _ruler, (255, 197, 92)),
    Icon("person", "a person", _person, (220, 228, 236)),
    Icon("truck", "a truck", _truck, (150, 160, 172)),
    Icon("factory", "a mill or factory", _factory, (150, 160, 172)),
    Icon("board", "a sawn board", _board, (214, 170, 110)),
    Icon("house", "a house", _house, (220, 228, 236)),
    Icon("drop", "water", _drop, (80, 170, 255)),
    Icon("bolt", "power", _bolt, (255, 210, 60)),
    Icon("check", "yes", _check, (83, 233, 152)),
    Icon("cross", "no", _cross, (255, 90, 95)),
    Icon("arrow", "leads to", _arrow, (220, 228, 236)),
    Icon("sun", "the sun", _sun, (255, 200, 60)),
    Icon("flame", "fire, firewood", _flame, (255, 128, 40)),
)}


def icon_keys() -> tuple[str, ...]:
    return tuple(ICONS)


def draw_icon(pg, surface, key: str, centre: tuple[float, float], size: float,
              colour: Colour | None = None, alpha: float = 1.0,
              angle_deg: float = 0.0, mirror: bool = False) -> None:
    """Draw one icon onto ``surface`` with its centre at ``centre`` pixels.

    Drawn on a scratch surface first and faded as a whole, because fading each
    primitive separately makes the places where two overlap show through darker.
    """
    icon = ICONS.get(key)
    if icon is None:
        raise KeyError(f"unknown icon {key!r}; known: {', '.join(ICONS)}")
    alpha = max(0.0, min(1.0, alpha))
    if alpha <= 0.004 or size < 2:
        return
    span = int(size * 1.25) + 4
    scratch = pg.Surface((span, span), pg.SRCALPHA)
    pen = Pen(pg, scratch, (span / 2.0, span / 2.0), size, angle_deg, mirror)
    icon.draw(pen, colour or icon.tint)
    if alpha < 0.999:
        scratch.fill((255, 255, 255, int(round(255 * alpha))),
                     special_flags=pg.BLEND_RGBA_MULT)
    surface.blit(scratch, (int(centre[0] - span / 2.0), int(centre[1] - span / 2.0)))


def validate_icons() -> None:
    """Every icon draws something, inside its own box, at any size and angle."""
    import pygame as pg

    for key in ICONS:
        for size, angle in ((48, 0.0), (17, 12.0)):
            surface = pg.Surface((96, 96), pg.SRCALPHA)
            draw_icon(pg, surface, key, (48, 48), size, angle_deg=angle)
            bounds = surface.get_bounding_rect()
            assert bounds.width > 2 and bounds.height > 2, (key, size)
            # An icon that spills far outside its box would land on its caption.
            assert bounds.width <= size * 1.3 + 4, (key, size, bounds)
        faded = pg.Surface((96, 96), pg.SRCALPHA)
        draw_icon(pg, faded, key, (48, 48), 48, alpha=0.0)
        assert faded.get_bounding_rect().width == 0, key
    try:
        draw_icon(pg, pg.Surface((8, 8), pg.SRCALPHA), "nope", (4, 4), 8)
    except KeyError:
        pass
    else:  # pragma: no cover - the guard is the point
        raise AssertionError("an unknown icon drew silently")
