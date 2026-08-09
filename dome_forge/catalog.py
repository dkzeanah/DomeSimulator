"""What a panel can be made of: a library of struts and a library of fills.

Two separate ideas, deliberately kept apart:

* A **strut profile** is a stick of material with a cross-section -- a
  2x4, a length of PVC, or a tree trunk split down the middle. It runs
  along one edge of a triangle. Nothing says the three edges of a panel
  have to use the same one.
* A **panel fill** is whatever spans the middle -- glass, a solar panel,
  louvers, shingles, or nothing at all.

Cross-sections are given as real 2D outlines so the shape you pick
actually shows up in the render. The section is drawn in the plane
across the strut, with **x running inward** from the seam line into the
triangle, and **y running down** toward the centre of the dome. So a
flat-laid 2x4 is 0.089 wide in x and 0.038 deep in y, while a half-round
log is a flat top with a curved belly hanging below it.
"""

from __future__ import annotations

import math
from dataclasses import dataclass
from typing import Callable


Section = tuple[tuple[float, float], ...]


def _rect(width: float, depth: float) -> Section:
    return ((0.0, 0.0), (width, 0.0), (width, -depth), (0.0, -depth))


def _round(diameter: float, steps: int = 20) -> Section:
    """A full round stick -- a pole, a dowel, a whole small trunk."""
    r = diameter * 0.5
    return tuple(
        (r + r * math.cos(math.tau * i / steps),
         -r + r * math.sin(math.tau * i / steps))
        for i in range(steps)
    )


def _half_round(diameter: float, steps: int = 14) -> Section:
    """A trunk split down the middle once: flat face up, curved belly
    below. The flat face is what the panel and its neighbour bolt to."""
    r = diameter * 0.5
    points = [(0.0, 0.0), (diameter, 0.0)]
    for i in range(1, steps):
        angle = math.pi * i / steps
        points.append((r + r * math.cos(angle), -r * math.sin(angle)))
    return tuple(points)


def _quarter_round(diameter: float, steps: int = 10) -> Section:
    """That same half-round split again through its middle: two flat
    faces meeting at a right angle, with one curved face. Cheap to make
    from a single trunk and it gives four struts per log."""
    r = diameter * 0.5
    points = [(0.0, 0.0), (r, 0.0)]
    for i in range(steps + 1):
        angle = (math.pi * 0.5) * i / steps
        points.append((r * math.cos(angle), -r * math.sin(angle)))
    return tuple(points)


def _tube(diameter: float, wall: float, steps: int = 18) -> Section:
    """A hollow round section, drawn as a closed ring by running out
    along the outer wall and back along the inner one."""
    r = diameter * 0.5
    inner = max(0.001, r - wall)
    outer_pts = [(r + r * math.cos(math.tau * i / steps),
                  -r + r * math.sin(math.tau * i / steps))
                 for i in range(steps + 1)]
    inner_pts = [(r + inner * math.cos(math.tau * i / steps),
                  -r + inner * math.sin(math.tau * i / steps))
                 for i in range(steps, -1, -1)]
    return tuple(outer_pts + inner_pts)


def _square_tube(width: float, wall: float) -> Section:
    outer = [(0.0, 0.0), (width, 0.0), (width, -width), (0.0, -width),
             (0.0, 0.0)]
    inner = [(wall, -wall), (wall, -(width - wall)),
             (width - wall, -(width - wall)), (width - wall, -wall),
             (wall, -wall)]
    return tuple(outer + inner)


def _angle(width: float, wall: float) -> Section:
    """An L-section: one leg flat against the panel, one turned down."""
    return ((0.0, 0.0), (width, 0.0), (width, -wall),
            (wall, -wall), (wall, -width), (0.0, -width))


@dataclass(frozen=True)
class StrutProfile:
    key: str
    label: str
    family: str
    width: float
    depth: float
    section: Section
    tint: str
    blurb: str

    @property
    def summary(self) -> str:
        return f"{self.width * 1000:.0f} x {self.depth * 1000:.0f} mm"


def _profile(key, label, family, section, tint, blurb) -> StrutProfile:
    xs = [p[0] for p in section]
    ys = [p[1] for p in section]
    return StrutProfile(key, label, family,
                        max(xs) - min(xs), max(ys) - min(ys),
                        section, tint, blurb)


STRUT_PROFILES: tuple[StrutProfile, ...] = (
    # --- split logs: the cheapest structural timber there is ----------
    _profile("log_quarter", "Quarter-round log", "wood",
             _quarter_round(0.180), "timber",
             "A trunk split in half, then split again through the middle "
             "of that half. Two flat faces meet at a right angle, one "
             "face stays round. Four struts out of one log."),
    _profile("log_half", "Half-round log", "wood",
             _half_round(0.180), "timber",
             "A trunk cut down the middle once. Flat face up to take the "
             "panel and the neighbouring triangle, round belly below."),
    _profile("log_round", "Full round log", "wood",
             _round(0.150), "timber",
             "A whole small trunk or pole, left round."),
    # --- dimensional lumber, laid flat --------------------------------
    _profile("lumber_2x2", "2x2 lumber", "wood",
             _rect(0.038, 0.038), "timber",
             "Real size 38 x 38 mm. Light infill and blocking."),
    _profile("lumber_2x4", "2x4 lumber", "wood",
             _rect(0.089, 0.038), "timber",
             "Real size 89 x 38 mm, laid flat. The default everywhere."),
    _profile("lumber_2x6", "2x6 lumber", "wood",
             _rect(0.140, 0.038), "timber",
             "Real size 140 x 38 mm. Deeper seat for insulation."),
    _profile("plank", "Wide plank", "wood",
             _rect(0.190, 0.025), "timber",
             "A wide, thin board -- more bearing surface, less depth."),
    # --- metal --------------------------------------------------------
    _profile("steel_rod", "Steel rod", "metal",
             _round(0.025), "steel", "Solid round bar."),
    _profile("steel_tube", "Steel tube", "metal",
             _tube(0.048, 0.003), "steel",
             "Round hollow section -- strong for its weight."),
    _profile("steel_square", "Steel square tube", "metal",
             _square_tube(0.050, 0.003), "steel",
             "Square hollow section. Flat faces make bolting easy."),
    _profile("steel_angle", "Steel angle", "metal",
             _angle(0.050, 0.005), "steel",
             "L-section: one leg flat to the panel, one turned down."),
    _profile("alu_tube", "Aluminium tube", "metal",
             _tube(0.048, 0.003), "aluminium",
             "Same shape as steel tube, lighter and corrosion-free."),
    _profile("alu_square", "Aluminium square tube", "metal",
             _square_tube(0.050, 0.003), "aluminium",
             "Light square hollow section."),
    _profile("alu_angle", "Aluminium angle", "metal",
             _angle(0.050, 0.004), "aluminium",
             "Light L-section, common for glazing frames."),
    # --- plastic ------------------------------------------------------
    _profile("pvc_pipe", "PVC pipe", "plastic",
             _tube(0.060, 0.004), "white",
             "Cheap, light, and weatherproof. Low stiffness."),
    _profile("pvc_square", "PVC square tube", "plastic",
             _square_tube(0.050, 0.004), "white",
             "Flat-faced plastic section."),
    _profile("plastic_solid", "Solid plastic bar", "plastic",
             _rect(0.050, 0.030), "white",
             "Solid recycled-plastic stick."),
    _profile("bamboo", "Bamboo pole", "wood",
             _tube(0.070, 0.008), "moss",
             "Naturally hollow and very stiff for its weight."),
)

PROFILE_BY_KEY = {p.key: p for p in STRUT_PROFILES}
PROFILE_KEYS = tuple(p.key for p in STRUT_PROFILES)


@dataclass(frozen=True)
class PanelFill:
    key: str
    label: str
    category: str
    style: str
    tint: str
    alpha: float
    thickness: float
    blurb: str


PANEL_FILLS: tuple[PanelFill, ...] = (
    PanelFill("open", "Open (no fill)", "none", "none", "glass", 0.0, 0.0,
              "Nothing between the struts -- bare frame."),
    PanelFill("glass", "Glass window", "glazing", "plain", "glass", 0.34, 0.006,
              "Clear glazing. Heaviest and most fragile, best clarity."),
    PanelFill("polycarbonate", "Polycarbonate", "glazing", "plain", "glass",
              0.46, 0.010,
              "Twin-wall plastic glazing: light, tough, slightly hazy."),
    PanelFill("acrylic", "Acrylic", "glazing", "plain", "glass", 0.30, 0.005,
              "Clearer than polycarbonate, scratches more easily."),
    PanelFill("fresnel", "Fresnel lens", "optical", "rings", "glass", 0.42,
              0.008,
              "A flat lens cut as concentric rings -- concentrates light "
              "or heat to a point."),
    PanelFill("mirror", "Mirror", "optical", "plain", "white", 0.94, 0.006,
              "Reflective panel: bounce daylight deeper inside, or aim "
              "it at a collector."),
    PanelFill("solar", "Solar panel", "energy", "cells", "charcoal", 1.0,
              0.035, "Photovoltaic module with its cell grid."),
    PanelFill("vent", "Louvered vent", "air", "louvers", "aluminium", 1.0,
              0.05, "Angled slats: airflow in, rain out."),
    PanelFill("ac_unit", "Air conditioner", "air", "box", "aluminium", 1.0,
              0.28, "A through-wall unit filling the panel."),
    PanelFill("fabric", "Fabric", "light", "plain", "white", 0.55, 0.002,
              "Tensioned cloth or membrane. Lightest option."),
    PanelFill("mesh", "Screen mesh", "light", "mesh", "steel", 0.8, 0.002,
              "Insect screen or a safety grille."),
    PanelFill("stone", "Stone", "solid", "plain", "charcoal", 1.0, 0.08,
              "Heavy masonry infill: thermal mass, no light."),
    PanelFill("metal_sheet", "Metal sheet", "solid", "plain", "steel", 1.0,
              0.004, "A single flat sheet of steel or aluminium."),
    PanelFill("wood_sheet", "Wooden sheet", "solid", "plain", "timber", 1.0,
              0.018, "One continuous panel -- plywood or OSB."),
    PanelFill("wood_planks", "Wooden planks", "solid", "planks", "timber",
              1.0, 0.020,
              "Several flat boards laid side by side to make up a sheet. "
              "Uses offcuts instead of a full panel."),
    PanelFill("shingles", "Shingles", "solid", "shingles", "timber", 1.0,
              0.022,
              "Overlapping courses, each shedding onto the one below."),
    PanelFill("plastic_sheet", "Plastic sheet", "solid", "plain", "white",
              1.0, 0.005, "Solid opaque plastic panel."),
    PanelFill("sip", "Insulated panel", "solid", "plain", "moss", 1.0, 0.10,
              "A thick sandwich panel: foam core, skins both sides."),
    PanelFill("door", "Door", "access", "box", "timber", 1.0, 0.06,
              "A hinged opening filling the triangle."),
)

FILL_BY_KEY = {f.key: f for f in PANEL_FILLS}
FILL_KEYS = tuple(f.key for f in PANEL_FILLS)


def profiles_by_family() -> dict[str, tuple[StrutProfile, ...]]:
    families: dict[str, list[StrutProfile]] = {}
    for profile in STRUT_PROFILES:
        families.setdefault(profile.family, []).append(profile)
    return {name: tuple(items) for name, items in families.items()}


def fills_by_category() -> dict[str, tuple[PanelFill, ...]]:
    groups: dict[str, list[PanelFill]] = {}
    for fill in PANEL_FILLS:
        groups.setdefault(fill.category, []).append(fill)
    return {name: tuple(items) for name, items in groups.items()}
