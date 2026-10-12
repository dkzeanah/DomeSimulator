"""One way to draw, three places to draw it: the viewer's canvas, an SVG to
print, and a PNG (which is also how the drawings are checked headless).

A :class:`View` maps inches to pixels, y up. Painters take pixel
coordinates and plain hex colours.
"""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np

PALETTE = {
    "paper": "#f7f3ea", "ink": "#2b2620", "muted": "#7a7064", "grid": "#e4dccd",
    "frame": "#8a5a36", "bark": "#5c3b22", "air": "#cfe6f2", "vent": "#3d8fd1",
    "FDR": "#d9a066", "FUL": "#e8c08a", "FDL": "#c98d52", "FUR": "#f0d2a4",
    "PD": "#d4995c", "PU": "#ebc58f", "BD": "#c9a173", "BU": "#ddb98b", "BE": "#b88c5e",
    "louver": "#d7a86e", "sheet": "#c7b08a", "metal": "#9aa4ad", "film": "#bfe3d6",
    "cut": "#c0392b", "plug": "#a3c58a", "shim": "#b5651d",
    "full": "#e3b679", "wall": "#d29a5e", "graded": "#efcf98", "copy": "#f3dfb8", "ring": "#b07a45",
    "cutfit": "#f1dcb2",
}


@dataclass
class View:
    """Inches to pixels: ``bounds`` (xmin, ymin, xmax, ymax) fitted into a
    ``w`` x ``h`` pixel box with a margin, y pointing up."""

    bounds: tuple[float, float, float, float]
    w: int
    h: int
    margin: int = 24
    ox: int = 0
    oy: int = 0

    def __post_init__(self):
        x0, y0, x1, y1 = self.bounds
        sx = (self.w - 2 * self.margin) / max(1e-9, x1 - x0)
        sy = (self.h - 2 * self.margin) / max(1e-9, y1 - y0)
        self.s = min(sx, sy)
        self.cx = self.ox + self.w / 2 - (x0 + x1) / 2 * self.s
        self.cy = self.oy + self.h / 2 + (y0 + y1) / 2 * self.s

    def px(self, pts) -> list[tuple[float, float]]:
        p = np.asarray(pts, dtype=float).reshape(-1, 2)
        return [(self.cx + x * self.s, self.cy - y * self.s) for x, y in p]

    def pt(self, x: float, y: float) -> tuple[float, float]:
        return self.cx + x * self.s, self.cy - y * self.s


class Painter:
    def poly(self, pts, fill=None, outline=None, width=1.0, dash=False): ...
    def line(self, pts, color, width=1.0, dash=False): ...
    def text(self, x, y, s, color="#2b2620", size=11, anchor="mm", bold=False): ...
    def rect(self, x0, y0, x1, y1, fill=None, outline=None, width=1.0):
        self.poly([(x0, y0), (x1, y0), (x1, y1), (x0, y1)], fill, outline, width)


class PilPainter(Painter):
    def __init__(self, w: int, h: int, bg: str = PALETTE["paper"]):
        from PIL import Image, ImageDraw, ImageFont
        self.Image, self.ImageFont = Image, ImageFont
        self.img = Image.new("RGB", (w, h), bg)
        self.d = ImageDraw.Draw(self.img)
        self._fonts: dict = {}

    def font(self, size: int, bold: bool):
        key = (size, bold)
        if key not in self._fonts:
            name = "C:/Windows/Fonts/segoeuib.ttf" if bold else "C:/Windows/Fonts/segoeui.ttf"
            try:
                self._fonts[key] = self.ImageFont.truetype(name, size)
            except OSError:
                self._fonts[key] = self.ImageFont.load_default()
        return self._fonts[key]

    def poly(self, pts, fill=None, outline=None, width=1.0, dash=False):
        pts = [tuple(map(float, p)) for p in pts]
        if len(pts) < 2:
            return
        if fill:
            self.d.polygon(pts, fill=fill)
        if outline:
            self.line(pts + [pts[0]], outline, width, dash)

    def line(self, pts, color, width=1.0, dash=False):
        pts = [tuple(map(float, p)) for p in pts]
        if not dash:
            self.d.line(pts, fill=color, width=max(1, int(round(width))))
            return
        for a, b in zip(pts, pts[1:]):
            a, b = np.array(a), np.array(b)
            L = float(np.linalg.norm(b - a))
            n = max(1, int(L // 8))
            for i in range(0, n, 2):
                p, q = a + (b - a) * i / n, a + (b - a) * min(n, i + 1) / n
                self.d.line([tuple(p), tuple(q)], fill=color, width=max(1, int(round(width))))

    def text(self, x, y, s, color="#2b2620", size=11, anchor="mm", bold=False):
        self.d.text((x, y), s, fill=color, font=self.font(size, bold), anchor=anchor)


class SvgPainter(Painter):
    def __init__(self, w: int, h: int, bg: str = PALETTE["paper"]):
        self.w, self.h = w, h
        self.parts = [f'<rect width="{w}" height="{h}" fill="{bg}"/>']

    def poly(self, pts, fill=None, outline=None, width=1.0, dash=False):
        p = " ".join(f"{x:.2f},{y:.2f}" for x, y in pts)
        d = ' stroke-dasharray="6,5"' if dash else ""
        self.parts.append(f'<polygon points="{p}" fill="{fill or "none"}" '
                          f'stroke="{outline or "none"}" stroke-width="{width}"{d}/>')

    def line(self, pts, color, width=1.0, dash=False):
        p = " ".join(f"{x:.2f},{y:.2f}" for x, y in pts)
        d = ' stroke-dasharray="6,5"' if dash else ""
        self.parts.append(f'<polyline points="{p}" fill="none" stroke="{color}" stroke-width="{width}"{d}/>')

    def text(self, x, y, s, color="#2b2620", size=11, anchor="mm", bold=False):
        ta = {"l": "start", "m": "middle", "r": "end"}[anchor[0]]
        base = {"t": "hanging", "m": "middle", "b": "auto", "s": "auto"}[anchor[1]]
        s = s.replace("&", "&amp;").replace("<", "&lt;")
        w = ' font-weight="bold"' if bold else ""
        self.parts.append(f'<text x="{x:.1f}" y="{y:.1f}" font-family="Segoe UI, Arial" font-size="{size}" '
                          f'fill="{color}" text-anchor="{ta}" dominant-baseline="{base}"{w}>{s}</text>')

    def svg(self) -> str:
        return (f'<svg xmlns="http://www.w3.org/2000/svg" width="{self.w}" height="{self.h}" '
                f'viewBox="0 0 {self.w} {self.h}">' + "".join(self.parts) + "</svg>")


class TkPainter(Painter):
    def __init__(self, canvas):
        self.c = canvas

    def poly(self, pts, fill=None, outline=None, width=1.0, dash=False):
        flat = [v for p in pts for v in p]
        if len(flat) < 4:
            return
        self.c.create_polygon(*flat, fill=fill or "", outline=outline or "", width=width,
                              dash=(6, 5) if dash else None)

    def line(self, pts, color, width=1.0, dash=False):
        flat = [v for p in pts for v in p]
        if len(flat) < 4:
            return
        self.c.create_line(*flat, fill=color, width=width, dash=(6, 5) if dash else None)

    def text(self, x, y, s, color="#2b2620", size=11, anchor="mm", bold=False):
        a = {"lm": "w", "mm": "center", "rm": "e", "mt": "n", "mb": "s", "lt": "nw", "rt": "ne",
             "lb": "sw", "rb": "se", "ls": "sw", "ms": "s"}.get(anchor, "center")
        self.c.create_text(x, y, text=s, fill=color, anchor=a,
                           font=("Segoe UI", max(7, size - 2), "bold" if bold else "normal"))
