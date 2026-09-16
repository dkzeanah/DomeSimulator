"""Measuring text with the exact font files the printed PDF embeds.

The paginator decides where every line breaks and where every page ends, so it
has to know how wide each word is. It asks Pillow, reading the same TrueType
files Chrome embeds when it prints the PDF, so the two agree. Words are then
placed one at a time at computed positions, which means a small difference in
how two programs round a glyph can never push a line past its margin.

The body face is Palatino Linotype and the display face is Segoe UI; both ship
with Windows and both permit embedding in a document (fsType 8, "editable").
If either is missing the book falls back to DejaVu, which is freely licensed.
"""

from __future__ import annotations

import struct
from functools import lru_cache
from pathlib import Path

WINDOWS_FONTS = Path(r"C:\Windows\Fonts")

FACES: dict[tuple[str, str], tuple[str, ...]] = {
    ("serif", "r"): ("pala.ttf",),
    ("serif", "i"): ("palai.ttf",),
    ("serif", "b"): ("palab.ttf",),
    ("serif", "bi"): ("palabi.ttf", "palab.ttf"),
    ("sans", "r"): ("segoeui.ttf",),
    ("sans", "i"): ("segoeuii.ttf", "segoeui.ttf"),
    ("sans", "b"): ("segoeuib.ttf",),
    ("sans", "bi"): ("segoeuiz.ttf", "segoeuib.ttf"),
    ("sans", "sb"): ("seguisb.ttf", "segoeuib.ttf"),
    ("mono", "r"): ("consola.ttf",),
    ("mono", "b"): ("consolab.ttf", "consola.ttf"),
    ("mono", "i"): ("consolai.ttf", "consola.ttf"),
    ("mono", "bi"): ("consolaz.ttf", "consola.ttf"),
}

FALLBACK: dict[str, str] = {"serif": "DejaVuSerif.ttf", "sans": "DejaVuSans.ttf",
                            "mono": "DejaVuSansMono.ttf"}

CSS_FAMILY = {
    "serif": "'Palatino Linotype','Book Antiqua',Palatino,'DejaVu Serif',serif",
    "sans": "'Segoe UI','DejaVu Sans',Arial,sans-serif",
    "mono": "Consolas,'DejaVu Sans Mono','Courier New',monospace",
}
"""How the SVG pages name the same faces."""

STYLE_CSS = {
    "r": ("normal", 400), "i": ("italic", 400), "b": ("normal", 700),
    "bi": ("italic", 700), "sb": ("normal", 600),
}

MEASURE_SCALE = 16
"""Glyphs are measured at 16 times their size, then scaled back, so a width
is known to a sixteenth of a point rather than a whole pixel."""


def _fallback_dir() -> Path | None:
    try:
        import matplotlib
        return Path(matplotlib.get_data_path()) / "fonts" / "ttf"
    except Exception:
        return None


@lru_cache(maxsize=None)
def face_path(family: str, style: str) -> Path:
    """The font file for one face, or the freely licensed fallback."""
    for name in FACES.get((family, style), FACES.get((family, "r"), ())):
        candidate = WINDOWS_FONTS / name
        if candidate.exists():
            return candidate
    folder = _fallback_dir()
    if folder is not None:
        candidate = folder / FALLBACK[family]
        if candidate.exists():
            return candidate
    raise FileNotFoundError(f"no font for {family}/{style}")


@lru_cache(maxsize=512)
def font(family: str, style: str, pixel_size: int):
    from PIL import ImageFont
    return ImageFont.truetype(str(face_path(family, style)), max(1, pixel_size))


@lru_cache(maxsize=512)
def font_px(family: str, style: str, pixel_size: float):
    """A face at a fractional pixel size, for drawing pages as images. Rounding
    small type to whole pixels makes it several percent too wide, which is
    enough to run neighbouring words together in a proof."""
    from PIL import ImageFont
    return ImageFont.truetype(str(face_path(family, style)), max(1.0, round(pixel_size * 20) / 20))


@lru_cache(maxsize=400_000)
def width(text: str, family: str, style: str, size: float) -> float:
    """Advance width of ``text`` in points at ``size`` points."""
    if not text:
        return 0.0
    face = font(family, style, int(round(size * MEASURE_SCALE)))
    return face.getlength(text) / MEASURE_SCALE


@lru_cache(maxsize=512)
def metrics(family: str, style: str, size: float) -> tuple[float, float]:
    """(ascent, descent) in points."""
    face = font(family, style, int(round(size * MEASURE_SCALE)))
    ascent, descent = face.getmetrics()
    return ascent / MEASURE_SCALE, descent / MEASURE_SCALE


def baseline_offset(family: str, style: str, size: float, leading: float) -> float:
    """Distance from the top of a line box to its baseline, glyphs centred."""
    ascent, descent = metrics(family, style, size)
    return (leading - (ascent + descent)) * 0.5 + ascent


def embedding_permission(path: Path) -> int | None:
    """The font's OS/2 fsType: 0 installable, 4 print, 8 editable, 2 restricted."""
    data = Path(path).read_bytes()
    tables = struct.unpack(">H", data[4:6])[0]
    for index in range(tables):
        tag, _checksum, offset, _length = struct.unpack(
            ">4sIII", data[12 + 16 * index: 28 + 16 * index])
        if tag == b"OS/2":
            return struct.unpack(">H", data[offset + 8: offset + 10])[0]
    return None


def embedding_report() -> list[tuple[str, str, int | None]]:
    """Every face the book uses, and whether the PDF may embed it."""
    rows = []
    for (family, style) in FACES:
        path = face_path(family, style)
        rows.append((f"{family}/{style}", path.name, embedding_permission(path)))
    return rows


def validate_fonts() -> None:
    for name, file, permission in embedding_report():
        # 2 is "restricted licence embedding": the PDF may not carry it.
        assert permission is None or not (permission & 0x0002), (name, file)
    assert width("dome", "serif", "r", 10) > 10.0
    assert width("dome dome", "serif", "r", 10) > 2 * width("dome", "serif", "r", 10)
