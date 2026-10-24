"""Drafting on a sheet: the title strip, text, pictures with labels, dimensions, angles, tables.

A thin layer over reportlab's canvas in points (1/72 in), origin bottom-left. Every
sheet is US Letter landscape with the title strip down the right-hand edge, the way a
builder's plan set is laid out.
"""

from __future__ import annotations

import io
import math
from dataclasses import dataclass

import numpy as np
from reportlab.lib.styles import ParagraphStyle
from reportlab.lib.utils import ImageReader
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.platypus import Paragraph

from .model import IN

PW, PH = 792.0, 612.0
MARGIN = 20.0
STRIP = 74.0
X0, Y0 = MARGIN, MARGIN
X1, Y1 = PW - MARGIN - STRIP - 8, PH - MARGIN
INK = (0.11, 0.10, 0.09)
GREY = (0.45, 0.44, 0.42)
ACCENT = (0.74, 0.36, 0.16)
PAPER = (1, 1, 1)

_FONTS = False


def fonts() -> None:
    global _FONTS
    if _FONTS:
        return
    try:
        pdfmetrics.registerFont(TTFont("Sans", r"C:\Windows\Fonts\segoeui.ttf"))
        pdfmetrics.registerFont(TTFont("Sans-B", r"C:\Windows\Fonts\segoeuib.ttf"))
        pdfmetrics.registerFont(TTFont("Sans-L", r"C:\Windows\Fonts\segoeuil.ttf"))
        pdfmetrics.registerFont(TTFont("Sans-I", r"C:\Windows\Fonts\segoeuii.ttf"))
        pdfmetrics.registerFont(TTFont("Mono", r"C:\Windows\Fonts\consola.ttf"))
        from reportlab.lib.fonts import addMapping
        addMapping("Sans", 0, 0, "Sans")
        addMapping("Sans", 1, 0, "Sans-B")
        addMapping("Sans", 0, 1, "Sans-I")
        addMapping("Sans", 1, 1, "Sans-B")
    except Exception:            # no Windows fonts: reportlab's own
        for a, b in (("Sans", "Helvetica"), ("Sans-B", "Helvetica-Bold"), ("Sans-L", "Helvetica"),
                     ("Sans-I", "Helvetica-Oblique"), ("Mono", "Courier")):
            pdfmetrics._fonts[a] = pdfmetrics.getFont(b)
    _FONTS = True


# ----------------------------------------------------------------------
# Units
# ----------------------------------------------------------------------

def mm(m: float) -> str:
    return f"{m * 1000:,.0f} mm"


def imp(m: float) -> str:
    """Feet and inches to the nearest sixteenth."""
    sixteenths = round(m / IN * 16)
    neg = sixteenths < 0
    sixteenths = abs(sixteenths)
    inch, frac = divmod(sixteenths, 16)
    ft, inch = divmod(inch, 12)
    f = ""
    if frac:
        g = math.gcd(frac, 16)
        f = f"-{frac // g}/{16 // g}" if inch or ft else f"{frac // g}/{16 // g}"
    s = (f"{ft}' " if ft else "") + (f"{inch}{f}\"" if (inch or f) else ("0\"" if not ft else "0\""))
    if ft and not inch and not frac:
        s = f"{ft}' 0\""
    return ("-" if neg else "") + s


def both(m: float) -> str:
    return f"{mm(m)} ({imp(m)})"


def deg(a: float, nd: int = 1) -> str:
    return f"{a:.{nd}f}\u00b0"


# ----------------------------------------------------------------------
# The sheet
# ----------------------------------------------------------------------

@dataclass
class Placed:
    """Where a picture landed: page rectangle and the pixel size it was drawn from."""

    x: float
    y: float
    w: float
    h: float
    px_w: int
    px_h: int

    def at(self, px, py) -> tuple[float, float]:
        return self.x + px / self.px_w * self.w, self.y + self.h - py / self.px_h * self.h


class Sheet:
    def __init__(self, c, number: int, title: str, project: str, tag: str, date: str, subtitle: str = ""):
        fonts()
        self.c = c
        self.n = number
        c.setFillColorRGB(*PAPER)
        c.rect(0, 0, PW, PH, stroke=0, fill=1)
        self.strip(project, tag, date, title)
        c.setFillColorRGB(*INK)
        c.setFont("Sans-B", 15)
        c.drawCentredString((X0 + X1) / 2, Y1 - 14, title)
        if subtitle:
            c.setFont("Sans", 10)
            c.setFillColorRGB(*GREY)
            c.drawCentredString((X0 + X1) / 2, Y1 - 28, subtitle)
            c.setFillColorRGB(*INK)
        self.top = Y1 - (36 if subtitle else 26)

    # -- the title strip: brand, project, sheet title, number --
    def strip(self, project, tag, date, title):
        c = self.c
        x = PW - MARGIN - STRIP
        c.setStrokeColorRGB(*INK)
        c.setLineWidth(0.8)
        c.rect(x, MARGIN, STRIP, PH - 2 * MARGIN, stroke=1, fill=0)
        # the mark: a little framed dome
        cx, cy, r = x + STRIP / 2, PH - MARGIN - 34, 20
        dome_mark(c, cx, cy, r)
        c.setFont("Sans-B", 8.5)
        c.drawCentredString(cx, cy - r - 14, "DOME SKETCH")
        c.setFont("Sans", 6.5)
        c.setFillColorRGB(*ACCENT)
        c.drawCentredString(cx, cy - r - 23, tag)
        c.setFillColorRGB(*INK)
        c.line(x, cy - r - 30, x + STRIP, cy - r - 30)
        # vertical texts
        c.saveState()
        c.translate(x + STRIP / 2 + 3, (MARGIN + 110 + cy - r - 30) / 2)
        c.rotate(90)
        c.setFont("Sans-B", 10.5)
        c.drawCentredString(0, 6, project)
        c.setFont("Sans", 7.5)
        c.setFillColorRGB(*GREY)
        c.drawCentredString(0, -6, title)
        c.restoreState()
        c.setFillColorRGB(*INK)
        c.line(x, MARGIN + 110, x + STRIP, MARGIN + 110)
        c.setFont("Sans", 5.6)
        lines = ["Every figure computed", "by sketch_claude.model", "from the solved sphere.", "Panel method after",
                 "Trillium Domes.", date]
        for i, s in enumerate(lines):
            c.drawCentredString(x + STRIP / 2, MARGIN + 100 - i * 7.2, s)
        c.setFillColorRGB(*INK)
        c.rect(x, MARGIN, STRIP, 48, stroke=0, fill=1)
        c.setFillColorRGB(1, 1, 1)
        c.setFont("Sans-B", 24)
        c.drawCentredString(x + STRIP / 2, MARGIN + 14, str(self.n))
        c.setFillColorRGB(*INK)

    # -- text --
    def para(self, text: str, x: float, y_top: float, width: float, size: float = 8.6, leading: float | None = None,
             font: str = "Sans", color=INK, align: int = 0) -> float:
        st = ParagraphStyle("p", fontName=font, fontSize=size, leading=leading or size * 1.32, textColor=color,
                            alignment=align, spaceAfter=0)
        h = 0.0
        for block in text.strip().split("\n\n"):
            p = Paragraph(block.replace("\n", " "), st)
            _, ph = p.wrap(width, 1000)
            p.drawOn(self.c, x, y_top - h - ph)
            h += ph + size * 0.6
        return h

    def heading(self, text: str, x: float, y: float, size: float = 10.5) -> float:
        self.c.setFont("Sans-B", size)
        self.c.setFillColorRGB(*INK)
        self.c.drawString(x, y - size, text)
        return size * 1.5

    def text(self, s: str, x: float, y: float, size: float = 7.5, font: str = "Sans", color=INK, anchor: str = "l",
             angle: float = 0.0):
        c = self.c
        c.saveState()
        c.setFillColorRGB(*color)
        c.setFont(font, size)
        c.translate(x, y)
        if angle:
            c.rotate(angle)
        {"l": c.drawString, "c": c.drawCentredString, "r": c.drawRightString}[anchor](0, -size * 0.35, s)
        c.restoreState()

    # -- pictures --
    def image(self, img, x: float, y: float, w: float, h: float, frame: bool = False) -> Placed:
        """Fit a PIL image in the box, keeping its shape; returns where it went."""
        iw, ih = img.size
        k = min(w / iw, h / ih)
        dw, dh = iw * k, ih * k
        px, py = x + (w - dw) / 2, y + (h - dh) / 2
        buf = io.BytesIO()
        img.save(buf, "PNG")
        buf.seek(0)
        self.c.drawImage(ImageReader(buf), px, py, dw, dh)
        if frame:
            self.c.setLineWidth(0.4)
            self.c.setStrokeColorRGB(*GREY)
            self.c.rect(px, py, dw, dh, stroke=1, fill=0)
        return Placed(px, py, dw, dh, iw, ih)

    def callouts(self, placed: Placed, cam, items, size: float = 7.0, side: str = "auto", pad: float = 8.0,
                 keep_in: tuple | None = None):
        """Label 3-D points in a picture: leaders out to labels stacked down its sides."""
        if not items:
            return
        P = cam.project([p for p, _ in items])
        anchors = [placed.at(px, py) for px, py in P]
        cx = placed.x + placed.w / 2
        left, right = [], []
        for (ax, ay), (_, label) in zip(anchors, items):
            s = side if side != "auto" else ("l" if ax < cx else "r")
            (left if s == "l" else right).append((ay, ax, label))
        bounds = keep_in or (placed.y + 6, placed.y + placed.h - 6)
        for group, s in ((left, "l"), (right, "r")):
            if not group:
                continue
            group.sort(key=lambda g: -g[0])
            n = len(group)
            lo, hi = bounds
            # a label's further lines hang below its leader, so the gap under one grows with its lines
            gap = [size * 1.9 + (g[2].count("\n")) * size * 1.15 for g in group]
            ys = [g[0] for g in group]
            # spread them so they never overlap, keeping each near its anchor
            for i in range(1, n):
                ys[i] = min(ys[i], ys[i - 1] - gap[i - 1])
            if ys and ys[-1] < lo:
                shift = lo - ys[-1]
                ys = [y + shift for y in ys]
            for i in range(n - 2, -1, -1):
                ys[i] = max(ys[i], ys[i + 1] + gap[i])
            ys = [min(y, hi) for y in ys]
            lx = placed.x - pad if s == "l" else placed.x + placed.w + pad
            for (ay, ax, label), ly in zip(group, ys):
                c = self.c
                c.setStrokeColorRGB(*INK)
                c.setLineWidth(0.45)
                elbow = lx + (6 if s == "l" else -6)
                c.line(ax, ay, elbow, ly)
                c.line(elbow, ly, lx, ly)
                c.setFillColorRGB(*INK)
                c.circle(ax, ay, 1.3, stroke=0, fill=1)
                lines = label.split("\n")
                for j, t in enumerate(lines):
                    self.text(t, lx - 2 if s == "l" else lx + 2, ly - j * size * 1.15, size, anchor="r" if s == "l" else "l")

    # -- drafting --
    def line(self, a, b, w: float = 0.6, color=INK, dash=None):
        c = self.c
        c.setStrokeColorRGB(*color)
        c.setLineWidth(w)
        c.setDash(*(dash if dash else ([], 0)))
        c.line(a[0], a[1], b[0], b[1])
        c.setDash([], 0)

    def poly(self, pts, w: float = 0.8, fill=None, color=INK, close: bool = True, dash=None):
        c = self.c
        p = c.beginPath()
        p.moveTo(*pts[0])
        for q in pts[1:]:
            p.lineTo(*q)
        if close:
            p.close()
        c.setStrokeColorRGB(*color)
        c.setLineWidth(w)
        c.setDash(*(dash if dash else ([], 0)))
        if fill is not None:
            c.setFillColorRGB(*fill)
        c.drawPath(p, stroke=1, fill=1 if fill is not None else 0)
        c.setDash([], 0)

    def dim(self, a, b, label: str, off: float = 12.0, size: float = 6.8, color=INK):
        """A dimension between page points ``a`` and ``b``, drawn ``off`` points to their left."""
        a, b = np.asarray(a, float), np.asarray(b, float)
        d = b - a
        L = float(np.linalg.norm(d))
        if L < 1e-6:
            return
        u = d / L
        n = np.array([-u[1], u[0]])
        pa, pb = a + n * off, b + n * off
        self.line(a + n * 2, pa + n * 3, 0.35, color)
        self.line(b + n * 2, pb + n * 3, 0.35, color)
        self.line(pa, pb, 0.45, color)
        for p, s in ((pa, 1), (pb, -1)):
            t = p + u * 4.5 * s
            self.poly([tuple(p), tuple(t + n * 1.6), tuple(t - n * 1.6)], 0.1, fill=color, color=color)
        ang = math.degrees(math.atan2(u[1], u[0]))
        if ang > 90 or ang < -90:
            ang += 180
        mid = (pa + pb) / 2 + n * (size * 0.75 if off >= 0 else -size * 0.75)
        self.text(label, mid[0], mid[1], size, anchor="c", angle=ang, color=color)

    def angle(self, v, d1, d2, r: float, label: str, size: float = 6.6, color=ACCENT, out: float = 9.0):
        """An angle arc at ``v`` between directions ``d1`` and ``d2`` (page space)."""
        a1 = math.degrees(math.atan2(d1[1], d1[0]))
        a2 = math.degrees(math.atan2(d2[1], d2[0]))
        ext = (a2 - a1) % 360
        if ext > 180:
            a1, ext = a2, 360 - ext
        if ext < 0.5:
            return
        c = self.c
        c.setStrokeColorRGB(*color)
        c.setLineWidth(0.6)
        c.arc(v[0] - r, v[1] - r, v[0] + r, v[1] + r, a1, ext)
        mid = math.radians(a1 + ext / 2)
        self.text(label, v[0] + (r + out) * math.cos(mid), v[1] + (r + out) * math.sin(mid), size, anchor="c", color=color)

    def table(self, x: float, y_top: float, cols, rows, size: float = 7.0, zebra: bool = True, head_size: float | None = None) -> float:
        """``cols``: [(header, width, align)]; returns the height used."""
        c = self.c
        rh = size * 1.55
        hs = head_size or size
        c.setFillColorRGB(*INK)
        c.rect(x, y_top - rh, sum(w for _, w, _ in cols), rh, stroke=0, fill=1)
        cx = x
        for head, w, al in cols:
            self.text(head, cx + (3 if al == "l" else w - 3 if al == "r" else w / 2), y_top - rh / 2, hs, "Sans-B",
                      (1, 1, 1), anchor=al)
            cx += w
        y = y_top - rh
        for i, row in enumerate(rows):
            if zebra and i % 2:
                c.setFillColorRGB(0.95, 0.94, 0.92)
                c.rect(x, y - rh, sum(w for _, w, _ in cols), rh, stroke=0, fill=1)
            cx = x
            for (head, w, al), val in zip(cols, row):
                self.text(str(val), cx + (3 if al == "l" else w - 3 if al == "r" else w / 2), y - rh / 2, size, anchor=al)
                cx += w
            y -= rh
        c.setStrokeColorRGB(*GREY)
        c.setLineWidth(0.4)
        c.rect(x, y, sum(w for _, w, _ in cols), y_top - y, stroke=1, fill=0)
        return y_top - y

    def box(self, x, y, w, h, fill=(0.97, 0.95, 0.91), stroke=GREY):
        self.c.setFillColorRGB(*fill)
        self.c.setStrokeColorRGB(*stroke)
        self.c.setLineWidth(0.4)
        self.c.rect(x, y, w, h, stroke=1, fill=1)
        self.c.setFillColorRGB(*INK)


def dome_mark(c, cx, cy, r):
    """The strip's mark: a 3V-ish dome in a circle, drawn in a few strokes."""
    c.setStrokeColorRGB(*INK)
    c.setLineWidth(0.9)
    c.circle(cx, cy, r, stroke=1, fill=0)
    base = cy - r * 0.45
    pts = []
    for i in range(7):
        t = math.pi * i / 6
        pts.append((cx - r * 0.78 * math.cos(t), base + r * 0.95 * math.sin(t)))
    p = c.beginPath()
    p.moveTo(*pts[0])
    for q in pts[1:]:
        p.lineTo(*q)
    c.drawPath(p, stroke=1, fill=0)
    c.line(cx - r * 0.85, base, cx + r * 0.85, base)
    c.setLineWidth(0.5)
    mid = []
    for i in range(5):
        t = math.pi * (i + 0.5) / 5
        mid.append((cx - r * 0.5 * math.cos(t), base + r * 0.55 * math.sin(t)))
    for i in range(len(mid)):
        c.line(*mid[i], *pts[i + 1 if i + 1 < len(pts) else -1])
        c.line(*mid[i], *pts[i])
        if i + 1 < len(mid):
            c.line(*mid[i], *mid[i + 1])
    for q in mid:
        c.line(*q, cx, base) if False else None
    c.setFillColorRGB(*ACCENT)
    c.rect(cx - r * 0.1, base, r * 0.2, r * 0.32, stroke=0, fill=1)
    c.setFillColorRGB(*INK)
