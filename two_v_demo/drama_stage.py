"""Geodesic dome staging: the CNEE's environment layer (the GDE).

The dome is not a backdrop here, it is the blocking.  Every anchor in
this module is computed from the same 2V hemisphere the rest of the
package uses -- :func:`two_v_demo.geometry.build_demo_geometry` -- so a
character standing at ``DOME_APEX_CENTER`` really is under the apex
vertex of the model being drawn, and a character pinned to the curved
wall really is against the strut pattern the renderer paints.

Three staging rules from the specification are implemented:

* **Apex central stage.**  The floor point under the top vertex, lit
  from the apex facets: the power position.
* **Curved structural wall pinning.**  Floor points close to the base
  ring, where the shell curves in overhead and closes the frame down on
  whoever is standing there.
* **Facet rim lighting.**  LED runs along real struts, used as back
  light so a silhouette separates from the dark of the dome.

Distances are metres.  The dome radius is a set decision, not a
geometric one, so it is a parameter with a stated default rather than a
constant buried in the code.
"""

from __future__ import annotations

import math
from dataclasses import dataclass
from functools import lru_cache

import numpy as np

from .geometry import build_demo_geometry


GEOMETRY = build_demo_geometry()

DEFAULT_SET_RADIUS_M = 6.0
"""A dome big enough to stage two people arguing under: 12 m across,
6 m to the crown.  The workshop set of the example episode."""


@dataclass(frozen=True)
class DomePreset:
    """One set: how big the dome is and how it is lit."""

    preset_id: str
    radius_m: float
    lighting_theme: str
    structural_lights_intensity: float
    description: str


DOME_PRESETS: dict[str, DomePreset] = {
    "GEODESIC_GARAGE_WORKSHOP": DomePreset(
        preset_id="GEODESIC_GARAGE_WORKSHOP",
        radius_m=DEFAULT_SET_RADIUS_M,
        lighting_theme="NIGHT_RAIN_CYAN_AMBER",
        structural_lights_intensity=0.8,
        description="A working dome: hoist, benches, wet cyan night "
                    "outside, amber worklight inside.",
    ),
    "GEODESIC_COUNCIL_HALL": DomePreset(
        preset_id="GEODESIC_COUNCIL_HALL",
        radius_m=9.0,
        lighting_theme="COLD_WHITE_APEX_SHAFT",
        structural_lights_intensity=0.45,
        description="The High Council dome: bigger, colder, a shaft of "
                    "light down the apex and nothing on the walls.",
    ),
}


@dataclass(frozen=True)
class StageAnchor:
    """A named place to stand, and what the dome does to whoever stands there."""

    anchor_id: str
    position: np.ndarray
    facing_deg: float
    """Default facing: anchors point at the middle of the floor."""
    staging_note: str
    height_m: float = 0.0
    """Floor height of the anchor: zero on the deck, higher on a strut."""


def _floor_facing(position: np.ndarray) -> float:
    """Anchors face the centre of the dome unless told otherwise."""
    if float(np.linalg.norm(position[:2])) < 1e-9:
        return 0.0
    return math.degrees(math.atan2(-position[1], -position[0]))


@lru_cache(maxsize=8)
def stage_anchors(radius_m: float = DEFAULT_SET_RADIUS_M
                  ) -> dict[str, StageAnchor]:
    """Every named standing position in a dome of this size."""
    vertices = GEOMETRY.vertices
    anchors: dict[str, StageAnchor] = {}

    apex = np.array([0.0, 0.0, 0.0])
    anchors["DOME_APEX_CENTER"] = StageAnchor(
        "DOME_APEX_CENTER", apex, 0.0,
        "Directly under the top vertex, in the apex light shaft. The "
        "dominating position: everything else in the dome looks in at it.")

    # The curved wall: stand just inside the base ring, where the shell
    # is already leaning in overhead.
    ring = [vertices[index] for index in GEOMETRY.base_ring]
    inset = radius_m * 0.78
    for quadrant, index in (("NORTH", 0), ("EAST", 2), ("SOUTH", 5),
                            ("WEST", 7)):
        direction = np.asarray(ring[index % len(ring)], dtype=float)
        direction = direction / max(1e-9, float(np.linalg.norm(direction[:2])))
        spot = np.array([direction[0] * inset, direction[1] * inset, 0.0])
        anchors[f"DOME_CURVED_WALL_{quadrant}"] = StageAnchor(
            f"DOME_CURVED_WALL_{quadrant}", spot, _floor_facing(spot),
            "Backed into the curve, where the struts close in overhead "
            "and the frame tightens on a cornered character.")

    # A perch: the highest vertex that is not the apex, which is where
    # the upper strut network is climbable in a real dome.
    heights = sorted(range(len(vertices)), key=lambda i: -vertices[i][2])
    perch_index = next(i for i in heights if vertices[i][2] < 0.98)
    perch = np.asarray(vertices[perch_index], dtype=float) * radius_m
    anchors["DOME_STRUT_TOP"] = StageAnchor(
        "DOME_STRUT_TOP", np.array([perch[0], perch[1], 0.0]),
        _floor_facing(perch),
        "Up on the strut network, above everyone's eye-line: the "
        "position an intruder takes.",
        height_m=float(perch[2]))
    # The specification's example script spells this anchor
    # "DOME_SCORD_STRUT_TOP".  Accepted as an alias rather than silently
    # failing an episode that is otherwise valid.
    anchors["DOME_SCORD_STRUT_TOP"] = anchors["DOME_STRUT_TOP"]

    anchors["DOME_FLOOR_CENTER"] = StageAnchor(
        "DOME_FLOOR_CENTER", np.array([0.0, 0.0, 0.0]), 0.0,
        "The middle of the deck: neutral ground for a dialogue beat.")
    return anchors


@dataclass(frozen=True)
class RimLight:
    """One LED run along a strut, used as back light."""

    start: np.ndarray
    end: np.ndarray
    intensity: float


@lru_cache(maxsize=8)
def rim_lights(radius_m: float = DEFAULT_SET_RADIUS_M,
               intensity: float = 0.8,
               count: int = 14) -> tuple[RimLight, ...]:
    """LED runs on real struts, spread around the shell.

    Taken from the hemisphere's own edge list, so every light strip
    lies on a strut the renderer actually draws.
    """
    edges = list(GEOMETRY.hemisphere_edges)
    step = max(1, len(edges) // count)
    chosen = edges[::step][:count]
    return tuple(
        RimLight(
            start=np.asarray(GEOMETRY.vertices[edge[0]],
                             dtype=float) * radius_m,
            end=np.asarray(GEOMETRY.vertices[edge[1]], dtype=float) * radius_m,
            intensity=intensity,
        )
        for edge in chosen
    )


def apex_light(radius_m: float = DEFAULT_SET_RADIUS_M) -> np.ndarray:
    """The point light in the apex facets, straight over the power position."""
    return np.array([0.0, 0.0, radius_m * 0.98])


def key_light_direction(theme: str) -> np.ndarray:
    """Which way the key light travels, by lighting theme.

    Returned as the direction light *moves*, matching the renderer's own
    ``u_light`` convention.
    """
    themes = {
        "NIGHT_RAIN_CYAN_AMBER": np.array([-0.35, -0.50, -0.79]),
        "COLD_WHITE_APEX_SHAFT": np.array([-0.05, -0.08, -0.99]),
    }
    return themes.get(theme, np.array([-0.45, -0.55, -0.72]))


def headroom_at(position, radius_m: float = DEFAULT_SET_RADIUS_M) -> float:
    """How much dome is over a character's head at that floor spot.

    A sphere, so this is exact: it is what makes wall pinning read as
    confinement rather than as standing next to a wall.
    """
    position = np.asarray(position, dtype=float)
    reach = float(np.linalg.norm(position[:2]))
    if reach >= radius_m:
        return 0.0
    return math.sqrt(radius_m * radius_m - reach * reach)


def validate_drama_stage() -> None:
    """Prove the staging against the dome the renderer really draws."""
    for preset in DOME_PRESETS.values():
        assert preset.radius_m > 2.0, preset.preset_id
        assert 0.0 <= preset.structural_lights_intensity <= 1.0
        assert preset.description.endswith("."), preset.preset_id

    anchors = stage_anchors()
    for name in ("DOME_APEX_CENTER", "DOME_STRUT_TOP", "DOME_FLOOR_CENTER",
                 "DOME_CURVED_WALL_NORTH", "DOME_SCORD_STRUT_TOP"):
        assert name in anchors, name
    for anchor in anchors.values():
        assert anchor.staging_note.endswith("."), anchor.anchor_id
        assert anchor.position.shape == (3,)

    # The apex position is under the apex, and it is the roomiest spot
    # in the dome: that is what makes it the power position.
    radius = DEFAULT_SET_RADIUS_M
    apex = anchors["DOME_APEX_CENTER"]
    assert abs(headroom_at(apex.position, radius) - radius) < 1e-9
    for quadrant in ("NORTH", "EAST", "SOUTH", "WEST"):
        wall = anchors[f"DOME_CURVED_WALL_{quadrant}"]
        over = headroom_at(wall.position, radius)
        assert over < radius * 0.7, quadrant
        assert over > 1.9, ("a pinned character still has to fit", quadrant)
        # Wall anchors face back into the room.
        toward = -wall.position[:2]
        facing = np.array([math.cos(math.radians(wall.facing_deg)),
                           math.sin(math.radians(wall.facing_deg))])
        assert float(np.dot(facing, toward)) > 0.0, quadrant

    # The perch really is up in the struts, and on the model.
    perch = anchors["DOME_STRUT_TOP"]
    assert perch.height_m > 2.5, perch.height_m
    assert perch.height_m < radius, "the perch cannot be above the crown"

    # Every rim light lies on a strut of the hemisphere, at set scale.
    for light in rim_lights(radius):
        for point in (light.start, light.end):
            assert abs(float(np.linalg.norm(point)) - radius) < 1e-6
            assert point[2] >= -1e-9, "rim lights stay on the upper shell"
    assert len(rim_lights(radius)) >= 10

    assert abs(float(np.linalg.norm(key_light_direction(
        "COLD_WHITE_APEX_SHAFT"))) - 1.0) < 0.02
