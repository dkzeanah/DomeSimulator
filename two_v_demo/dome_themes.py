"""Skins for the same shell: what a dome can be dressed as.

The structural argument in every other lesson is that one skeleton
carries any covering.  This is that argument made visible -- a baseball,
a basketball, a disco ball, a wall of advertising, a video billboard --
all painted onto the identical 2V hemisphere, changing nothing but the
surface.

Also here: the four product lines ``al_build`` actually defines, read off
the catalogue rather than typed, so the list cannot drift from the code
that builds them.
"""

from __future__ import annotations

import math
from dataclasses import dataclass
from functools import lru_cache

import numpy as np

from .geometry import build_demo_geometry, normalize


GEOMETRY = build_demo_geometry()
FACES = list(GEOMETRY.hemisphere_faces)
EDGES = list(GEOMETRY.hemisphere_edges)


@dataclass(frozen=True)
class Theme:
    """One skin, and the pitch that goes with it."""

    key: str
    label: str
    pitch: str

    def face_colour(self, index: int, centre: np.ndarray, phase: float):
        raise NotImplementedError

    def edge_colour(self, index: int, phase: float):
        return (0.86, 0.88, 0.92, 1.0)


class Baseball(Theme):
    def face_colour(self, index, centre, phase):
        return (0.94, 0.93, 0.90, 0.92)

    def edge_colour(self, index, phase):
        # Stitching: the seam is red, everything else is the hide.
        return (0.80, 0.16, 0.18, 1.0) if index % 3 == 0 else (0.90, 0.89, 0.86, 1.0)


class Basketball(Theme):
    def face_colour(self, index, centre, phase):
        return (0.88, 0.44, 0.14, 0.94)

    def edge_colour(self, index, phase):
        return (0.08, 0.07, 0.07, 1.0)


class DiscoBall(Theme):
    def face_colour(self, index, centre, phase):
        # Each facet catches the light at its own moment.
        glint = 0.5 + 0.5 * math.sin(phase * math.tau * 1.6 + index * 0.9)
        base = 0.34 + 0.62 * glint
        return (base, base * 0.98, min(1.0, base * 1.06), 0.95)

    def edge_colour(self, index, phase):
        return (0.55, 0.58, 0.64, 1.0)


class AdSpace(Theme):
    PANEL = (
        (0.86, 0.20, 0.22), (0.18, 0.46, 0.86), (0.95, 0.72, 0.16),
        (0.22, 0.66, 0.38), (0.62, 0.30, 0.78),
    )

    def face_colour(self, index, centre, phase):
        tone = self.PANEL[index % len(self.PANEL)]
        return (tone[0], tone[1], tone[2], 0.90)

    def edge_colour(self, index, phase):
        return (0.92, 0.92, 0.94, 1.0)


class VideoWall(Theme):
    def face_colour(self, index, centre, phase):
        # One image spanning many panels: brightness comes from position
        # on the shell, not from the panel index, so a picture appears to
        # cross the seams instead of stopping at them.
        sweep = (centre[0] * 0.5 + centre[2] * 0.3) * 0.22 + phase * 1.4
        value = 0.5 + 0.5 * math.sin(sweep * math.tau)
        return (0.10 + value * 0.30, 0.35 + value * 0.55,
                0.75 + value * 0.25, 0.94)

    def edge_colour(self, index, phase):
        return (0.12, 0.14, 0.18, 1.0)


class Greenhouse(Theme):
    def face_colour(self, index, centre, phase):
        return (0.60, 0.86, 0.92, 0.26)

    def edge_colour(self, index, phase):
        return (0.72, 0.76, 0.80, 1.0)


THEMES: tuple[Theme, ...] = (
    Baseball("baseball", "BASEBALL",
             "A hide-white shell with a red seam. It is already the shape."),
    Basketball("basketball", "BASKETBALL",
               "Orange, black seams, and nobody has to be told what it is."),
    DiscoBall("disco", "DISCO BALL",
              "Every panel is a facet. A venue that is its own light rig."),
    AdSpace("adspace", "ADVERTISING SPACE",
            "Forty panels, forty rentable faces, on a building you already own."),
    VideoWall("video", "VIDEO BILLBOARD",
              "One picture spanning many panels, aimed at a road."),
    Greenhouse("greenhouse", "GREENHOUSE",
               "The same shell in glazing, which is a product line already."),
)

THEME_BY_KEY = {item.key: item for item in THEMES}


def draw_theme(opaque, transparent, theme: Theme, scale: float,
               phase: float = 0.0, edge_radius: float = 0.06) -> None:
    """Paint the standard hemisphere in one theme."""
    for index, face in enumerate(FACES):
        corners = GEOMETRY.vertices[[int(v) for v in face]] * scale
        centre = corners.mean(axis=0)
        colour = theme.face_colour(index, centre, phase)
        normal = normalize(centre)
        transparent.triangle(corners[0], corners[1], corners[2], colour, normal)
    for index, edge in enumerate(EDGES):
        a, b = (GEOMETRY.vertices[i] * scale for i in edge)
        opaque.cylinder(a, b, edge_radius, theme.edge_colour(index, phase), 7)


# ----------------------------------------------------------------------
# The product lines, read off the catalogue
# ----------------------------------------------------------------------

@dataclass(frozen=True)
class ProductLine:
    """One dome type the creator actually defines."""

    key: str
    name: str
    frequencies: tuple[int, ...]
    radius_range: tuple[float, float]
    stages: int

    @property
    def diameter_ft_range(self) -> tuple[float, float]:
        return (self.radius_range[0] * 2 * 3.28084,
                self.radius_range[1] * 2 * 3.28084)


@lru_cache(maxsize=1)
def product_lines() -> tuple[ProductLine, ...]:
    """Read the product lines from al_build rather than restating them."""
    import al_build as AL

    return tuple(
        ProductLine(
            key=key,
            name=item.name,
            frequencies=tuple(sorted(set(item.freq_choices))),
            radius_range=tuple(item.radius_range),
            stages=len(item.stage_keys),
        )
        for key, item in AL.DOME_TYPES.items()
    )


def themes_report() -> str:
    lines = ["DOME THEMES AND PRODUCT LINES - AUDIT", ""]
    lines.append(f"  {len(THEMES)} themes, all on the same "
                 f"{len(FACES)}-panel hemisphere:")
    for theme in THEMES:
        lines.append(f"    {theme.key:<11} {theme.label:<20} {theme.pitch}")
    lines.append("")
    lines.append("  product lines defined in al_build:")
    for line in product_lines():
        low, high = line.diameter_ft_range
        lines.append(
            f"    {line.key:<11} {line.name:<16} "
            f"{low:.0f}-{high:.0f} ft   freq {line.frequencies}   "
            f"{line.stages} stages")
    return "\n".join(lines)


def validate_themes() -> None:
    """Every theme must paint, and the product lines must match al_build."""
    from .render_kit import TriangleBatch

    assert len(THEMES) >= 5
    keys = [item.key for item in THEMES]
    assert len(set(keys)) == len(keys)

    for theme in THEMES:
        assert theme.label and theme.pitch, theme.key
        opaque, transparent = TriangleBatch(), TriangleBatch()
        draw_theme(opaque, transparent, theme, 5.0, 0.3)
        assert opaque.vertices, f"{theme.key} drew no frame"
        assert transparent.vertices, f"{theme.key} drew no panels"
        for index in range(len(FACES)):
            colour = theme.face_colour(index, np.array([1.0, 0.0, 1.0]), 0.4)
            assert len(colour) == 4, colour
            assert all(0.0 <= channel <= 1.0 for channel in colour), (
                theme.key, colour)
        for index in range(len(EDGES)):
            colour = theme.edge_colour(index, 0.4)
            assert all(0.0 <= channel <= 1.0 for channel in colour), (
                theme.key, colour)

    # The disco ball and the video wall must actually change with time,
    # or they are just flat paint with a fancy name.
    disco = THEME_BY_KEY["disco"]
    assert disco.face_colour(3, np.zeros(3), 0.0) != \
        disco.face_colour(3, np.zeros(3), 0.4)
    video = THEME_BY_KEY["video"]
    assert video.face_colour(3, np.array([2.0, 0.0, 1.0]), 0.2) != \
        video.face_colour(3, np.array([-2.0, 0.0, 1.0]), 0.2), \
        "the video wall must vary across the shell, not just in time"

    lines = product_lines()
    assert len(lines) >= 4, lines
    import al_build as AL
    assert {item.key for item in lines} == set(AL.DOME_TYPES)
    for line in lines:
        assert line.stages > 0 and line.frequencies
        low, high = line.radius_range
        assert 0 < low <= high
