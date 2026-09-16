"""Pages as pictures: SVG for print and the reader, PNG for proofs and video.

Everything here draws the positioned items :mod:`layout` produced, and nothing
here decides where anything goes. That is what keeps the four editions -- the
PDF, the live reader, the editor and the reading video -- the same book.

* :func:`svg_page` -- one page as SVG. Text stays text (so the PDF is vector
  and searchable), pictures are referenced, and in the reader every live
  number carries the name of the token it came from.
* :func:`print_html` -- all pages in one HTML file sized for KDP, which Chrome
  prints to the PDF (:func:`print_pdf`).
* :func:`png_page` -- one page as an image, drawn with Pillow from the same
  font files, for proofs, thumbnails and the reading video.
"""

from __future__ import annotations

import html
import re
import subprocess
from functools import lru_cache
from pathlib import Path
from typing import Callable

from . import config as C
from . import fonts as F


def _attr(value) -> str:
    return html.escape(str(value), quote=True)


def _same_run(a, b) -> bool:
    return (a.y == b.y and a.family == b.family and a.style == b.style
            and a.size == b.size and a.color == b.color)


def svg_page(page, href: Callable[[str], str] = lambda src: src,
             interactive: bool = False, proof: bool = False) -> str:
    width, height = C.TRIM.canvas_w, C.TRIM.canvas_h
    out = [f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {width:.2f} {height:.2f}" '
           f'width="{width:.2f}pt" height="{height:.2f}pt" data-page="{page.index}" '
           f'data-folio="{_attr(page.folio)}">',
           f'<rect x="0" y="0" width="{width:.2f}" height="{height:.2f}" '
           f'fill="{page.background or C.PAPER_WHITE}"/>']
    run: list = []

    def flush() -> None:
        if not run:
            return
        first = run[0]
        font_style, weight = F.STYLE_CSS.get(first.style, ("normal", 400))
        spans = []
        for word in run:
            extra = ""
            if interactive and word.token:
                extra = f' class="tok" data-tok="{_attr(word.token)}"'
            elif interactive and word.link:
                extra = f' class="lnk" data-href="{_attr(word.link)}"'
            spans.append(f'<tspan x="{word.x:.2f}"{extra}>{html.escape(word.text)}</tspan>')
        out.append(f'<text y="{first.y:.2f}" font-family="{_attr(F.CSS_FAMILY[first.family])}" '
                   f'font-size="{first.size:.2f}" font-style="{font_style}" '
                   f'font-weight="{weight}" fill="{first.color}" xml:space="preserve">'
                   f'{"".join(spans)}</text>')
        run.clear()

    for item in page.items:
        kind = item.kind
        if kind == "word":
            if run and not _same_run(run[-1], item):
                flush()
            run.append(item)
            continue
        flush()
        if kind == "rect":
            fill = item.fill or "none"
            stroke = (f' stroke="{item.stroke}" stroke-width="{item.sw:.2f}"'
                      if item.stroke else "")
            dash = f' stroke-dasharray="{item.dash}"' if item.dash else ""
            radius = f' rx="{item.r:.2f}" ry="{item.r:.2f}"' if item.r else ""
            opacity = f' opacity="{item.opacity:.2f}"' if item.opacity < 1 else ""
            out.append(f'<rect x="{item.x:.2f}" y="{item.y:.2f}" width="{item.w:.2f}" '
                       f'height="{item.h:.2f}" fill="{fill}"{stroke}{dash}{radius}{opacity}/>')
        elif kind == "rule":
            dash = f' stroke-dasharray="{item.dash}"' if item.dash else ""
            out.append(f'<line x1="{item.x1:.2f}" y1="{item.y1:.2f}" x2="{item.x2:.2f}" '
                       f'y2="{item.y2:.2f}" stroke="{item.color}" stroke-width="{item.w:.2f}" '
                       f'stroke-linecap="round"{dash}/>')
        elif kind == "picture":
            if item.src:
                fit = "xMidYMid slice" if item.fit == "cover" else "xMidYMid meet"
                opacity = f' opacity="{item.opacity:.2f}"' if item.opacity < 1 else ""
                out.append(f'<image x="{item.x:.2f}" y="{item.y:.2f}" width="{item.w:.2f}" '
                           f'height="{item.h:.2f}" preserveAspectRatio="{fit}"{opacity} '
                           f'href="{_attr(href(item.src))}" data-plate="{_attr(item.plate)}"/>')
            else:
                out.append(f'<rect x="{item.x:.2f}" y="{item.y:.2f}" width="{item.w:.2f}" '
                           f'height="{item.h:.2f}" fill="#eef1f4" stroke="#9aa7b3" '
                           f'stroke-width="0.8" stroke-dasharray="4 3"/>')
                label = f"PLATE NOT YET RENDERED · {item.label or item.plate}"
                label_w = F.width(label, "sans", "b", 7.6)
                out.append(f'<text x="{item.x + (item.w - label_w) / 2:.2f}" '
                           f'y="{item.y + item.h / 2:.2f}" font-family="'
                           f'{_attr(F.CSS_FAMILY["sans"])}" font-size="7.6" font-weight="700" '
                           f'fill="#7b8794">{html.escape(label)}</text>')
    flush()
    if proof:
        recto = page.recto
        x0 = C.TRIM.x0(recto)
        out.append(f'<rect x="{x0:.2f}" y="{C.TRIM.y0:.2f}" width="{C.TRIM.width:.2f}" '
                   f'height="{C.TRIM.height:.2f}" fill="none" stroke="#e0439a" '
                   f'stroke-width="0.5"/>')
        inside = C.GRID.inside if recto else C.GRID.outside
        out.append(f'<rect x="{x0 + inside:.2f}" y="{C.TRIM.y0 + C.GRID.top:.2f}" '
                   f'width="{C.TRIM.width - C.GRID.inside - C.GRID.outside:.2f}" '
                   f'height="{C.TRIM.height - C.GRID.top - C.GRID.bottom:.2f}" fill="none" '
                   f'stroke="#23a6d5" stroke-width="0.4" stroke-dasharray="2 3"/>')
    out.append("</svg>")
    return "".join(out)


def print_html(pages, href: Callable[[str], str] = lambda src: src,
               title: str = C.TITLE) -> str:
    width_in = C.TRIM.width_in + C.TRIM.bleed_in
    height_in = C.TRIM.height_in + 2 * C.TRIM.bleed_in
    sheets = "".join(f'<div class="sheet">{svg_page(page, href)}</div>' for page in pages)
    return (f'<!doctype html><html><head><meta charset="utf-8"><title>{html.escape(title)}</title>'
            f'<style>@page {{ size: {width_in}in {height_in}in; margin: 0; }} '
            f'html, body {{ margin: 0; padding: 0; background: #fff; }} '
            f'.sheet {{ width: {width_in}in; height: {height_in}in; overflow: hidden; '
            f'break-after: page; page-break-after: always; }} '
            f'.sheet:last-child {{ break-after: auto; page-break-after: auto; }} '
            f'.sheet svg {{ display: block; width: {width_in}in; height: {height_in}in; }}'
            f'</style></head><body>{sheets}</body></html>')


# ----------------------------------------------------------------------
# PNG
# ----------------------------------------------------------------------

@lru_cache(maxsize=48)
def _image(path: str):
    from PIL import Image
    return Image.open(path).convert("RGB")


def _fitted(image, width: int, height: int, fit: str):
    from PIL import Image
    source_w, source_h = image.size
    if fit == "cover":
        scale = max(width / source_w, height / source_h)
    else:
        scale = min(width / source_w, height / source_h)
    new = image.resize((max(1, round(source_w * scale)), max(1, round(source_h * scale))),
                       Image.LANCZOS)
    if fit == "cover":
        left = (new.width - width) // 2
        top = (new.height - height) // 2
        new = new.crop((left, top, left + width, top + height))
    return new


def _dashed(draw, x1, y1, x2, y2, colour, width, on=4.0, off=3.0):
    length = ((x2 - x1) ** 2 + (y2 - y1) ** 2) ** 0.5
    if length <= 0:
        return
    dx, dy = (x2 - x1) / length, (y2 - y1) / length
    position = 0.0
    while position < length:
        end = min(length, position + on)
        draw.line([x1 + dx * position, y1 + dy * position, x1 + dx * end, y1 + dy * end],
                  fill=colour, width=width)
        position = end + off


def png_page(page, dpi: float = 100.0):
    from PIL import Image, ImageDraw
    scale = dpi / 72.0
    size = (round(C.TRIM.canvas_w * scale), round(C.TRIM.canvas_h * scale))
    image = Image.new("RGB", size, page.background or C.PAPER_WHITE)
    draw = ImageDraw.Draw(image)
    for item in page.items:
        kind = item.kind
        if kind == "rect":
            box = [item.x * scale, item.y * scale, (item.x + item.w) * scale,
                   (item.y + item.h) * scale]
            if item.opacity < 1 and item.fill:
                layer = Image.new("RGB", size, item.fill)
                mask = Image.new("L", size, 0)
                ImageDraw.Draw(mask).rounded_rectangle(box, radius=item.r * scale,
                                                       fill=round(255 * item.opacity))
                image.paste(layer, (0, 0), mask)
                draw = ImageDraw.Draw(image)
                continue
            width = max(1, round(item.sw * scale)) if item.stroke else 0
            outline = item.stroke if item.stroke and not item.dash else None
            if item.r:
                draw.rounded_rectangle(box, radius=item.r * scale, fill=item.fill,
                                       outline=outline, width=width)
            else:
                draw.rectangle(box, fill=item.fill, outline=outline, width=width)
            if item.stroke and item.dash:
                x1, y1, x2, y2 = box
                for a, b, c, d in ((x1, y1, x2, y1), (x2, y1, x2, y2), (x2, y2, x1, y2),
                                   (x1, y2, x1, y1)):
                    _dashed(draw, a, b, c, d, item.stroke, width)
        elif kind == "rule":
            coords = (item.x1 * scale, item.y1 * scale, item.x2 * scale, item.y2 * scale)
            width = max(1, round(item.w * scale))
            if item.dash:
                _dashed(draw, *coords, item.color, width, on=1.2 * scale, off=3.0 * scale)
            else:
                draw.line(coords, fill=item.color, width=width)
        elif kind == "picture":
            box_w, box_h = round(item.w * scale), round(item.h * scale)
            left, top = round(item.x * scale), round(item.y * scale)
            if item.src and Path(item.src).exists() and box_w > 0 and box_h > 0:
                fitted = _fitted(_image(item.src), box_w, box_h, item.fit)
                x = left + (box_w - fitted.width) // 2
                y = top + (box_h - fitted.height) // 2
                if item.opacity < 1:
                    region = image.crop((x, y, x + fitted.width, y + fitted.height))
                    fitted = Image.blend(region, fitted, item.opacity)
                image.paste(fitted, (x, y))
                draw = ImageDraw.Draw(image)
            else:
                draw.rectangle([left, top, left + box_w, top + box_h], fill="#eef1f4")
        elif kind == "word":
            face = F.font_px(item.family, item.style, item.size * scale)
            draw.text((item.x * scale, item.y * scale), item.text, font=face, fill=item.color,
                      anchor="ls")
    return image


# ----------------------------------------------------------------------
# PDF
# ----------------------------------------------------------------------

def chrome_path() -> str | None:
    try:
        from two_v_demo.book_export import _chrome_path
        return _chrome_path()
    except Exception:
        return None


def print_pdf(html_path: Path, pdf_path: Path, timeout: int = 1800) -> None:
    exe = chrome_path()
    if not exe:
        raise RuntimeError("Printing the PDF needs Google Chrome or Microsoft Edge.")
    command = [exe, "--headless=new", "--disable-gpu", "--no-sandbox", "--hide-scrollbars",
               "--no-pdf-header-footer", "--print-to-pdf-no-header",
               "--allow-file-access-from-files", "--disable-extensions",
               f"--print-to-pdf={pdf_path}", Path(html_path).resolve().as_uri()]
    result = subprocess.run(command, capture_output=True, text=True, timeout=timeout)
    if not Path(pdf_path).exists() or Path(pdf_path).stat().st_size < 1000:
        raise RuntimeError(f"Chrome did not write the PDF: {result.stderr[-1200:]}")


PAGE_OBJECT = re.compile(rb"/Type\s*/Page(?![a-zA-Z])")
PAGES_COUNT = re.compile(rb"/Type\s*/Pages\b.*?/Count\s+(\d+)", re.S)
MEDIABOX = re.compile(rb"/MediaBox\s*\[\s*([\d.\-]+)\s+([\d.\-]+)\s+([\d.\-]+)\s+([\d.\-]+)\s*\]")


def pdf_facts(pdf: Path) -> dict:
    """Page count and page size of a PDF, read straight from its bytes."""
    data = Path(pdf).read_bytes()
    count = len(PAGE_OBJECT.findall(data))
    counted = PAGES_COUNT.search(data)
    if counted:
        count = max(count, int(counted.group(1)))
    box = MEDIABOX.search(data)
    size = None
    if box:
        size = (float(box.group(3)) - float(box.group(1)),
                float(box.group(4)) - float(box.group(2)))
    return {"pages": count, "size_pt": size, "bytes": len(data)}
