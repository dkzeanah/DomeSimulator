"""Wood that looks like wood: irregular, knotted, and discoloured.

A strut drawn as one clean cylinder reads as a pipe.  Real milled timber
is none of those things -- it is slightly bent, it changes thickness
along its length, its colour drifts between heartwood and sapwood, and it
has knots where branches were.

Everything here is deterministic: colour, bend, taper and knot placement
all come from a hash of the strut's index, so the same stick is the same
stick in every frame and every render.  That matters more than it
sounds -- a frame-varying grain would strobe horribly at thirty frames a
second.
"""

from __future__ import annotations

import math
from dataclasses import dataclass

import numpy as np

from .geometry import normalize


# Heartwood through sapwood through weathered grey.  Real timber sits
# somewhere on this line and wanders along it down the length of a board.
WOOD_TONES: tuple[tuple[float, float, float], ...] = (
    (0.42, 0.28, 0.15),
    (0.58, 0.40, 0.22),
    (0.71, 0.53, 0.31),
    (0.80, 0.64, 0.42),
    (0.62, 0.50, 0.38),
    (0.49, 0.41, 0.34),
)

KNOT_TONE = (0.20, 0.13, 0.08, 1.0)
BARK_TONE = (0.26, 0.19, 0.13, 1.0)
GLUE_TONE = (0.92, 0.90, 0.78, 0.75)
CARDBOARD_TONES: tuple[tuple[float, float, float], ...] = (
    (0.66, 0.51, 0.33),
    (0.74, 0.59, 0.39),
    (0.58, 0.45, 0.30),
    (0.70, 0.56, 0.42),
)


def _noise(seed: int, salt: int = 0) -> float:
    """A stable pseudo-random number in 0..1 from two integers.

    Deliberately not ``random`` and not seeded per frame: the same strut
    must produce the same grain every time it is drawn, or the timber
    boils under motion.
    """
    value = (seed * 73856093) ^ (salt * 19349663)
    value = (value ^ (value >> 13)) * 1274126177
    return ((value ^ (value >> 16)) & 0xFFFF) / 65535.0


def wood_colour(seed: int, position: float, weathered: float = 0.0
                ) -> tuple[float, float, float, float]:
    """A tone from the wood line, drifting along the length of a stick."""
    drift = _noise(seed, 11) * 3.0 + position * (1.4 + _noise(seed, 12) * 2.2)
    index = int(drift) % len(WOOD_TONES)
    following = WOOD_TONES[(index + 1) % len(WOOD_TONES)]
    current = WOOD_TONES[index]
    blend = drift - math.floor(drift)
    tone = tuple(
        current[channel] * (1.0 - blend) + following[channel] * blend
        for channel in range(3)
    )
    if weathered > 0.0:
        grey = (0.52, 0.50, 0.47)
        tone = tuple(
            tone[channel] * (1.0 - weathered) + grey[channel] * weathered
            for channel in range(3)
        )
    return (tone[0], tone[1], tone[2], 1.0)


@dataclass(frozen=True)
class TimberStyle:
    """How rough a stick should look."""

    segments: int = 7
    """Pieces along the length. More pieces, more grain variation."""
    bend: float = 0.055
    """Sideways wander as a fraction of length."""
    taper: float = 0.22
    """How much the thickness varies end to end."""
    knots: float = 0.55
    """Chance per stick of carrying a visible knot."""
    weathered: float = 0.0
    bark: float = 0.0
    """Chance per stick of keeping a strip of bark."""


ROUGH = TimberStyle()
MILLED = TimberStyle(segments=4, bend=0.012, taper=0.06, knots=0.25)
CHAINSAW = TimberStyle(segments=9, bend=0.085, taper=0.34, knots=0.75, bark=0.45)
WEATHERED = TimberStyle(segments=8, bend=0.065, taper=0.26, knots=0.6,
                        weathered=0.55, bark=0.2)


def draw_timber(
    batch,
    a,
    b,
    radius: float,
    seed: int,
    style: TimberStyle = ROUGH,
    sides: int = 7,
    tint: tuple[float, float, float, float] | None = None,
) -> None:
    """Draw one stick of real-looking timber between two points.

    ``tint`` overrides the wood colour entirely, which is how the same
    geometry becomes a painted frame or a lit one without changing shape.
    """
    a = np.asarray(a, dtype=np.float64)
    b = np.asarray(b, dtype=np.float64)
    axis = b - a
    length = float(np.linalg.norm(axis))
    if length < 1e-9:
        return
    direction = axis / length

    # A stable pair of axes across the stick, for the bend and the knots.
    reference = np.array([0.0, 0.0, 1.0])
    if abs(float(np.dot(reference, direction))) > 0.9:
        reference = np.array([1.0, 0.0, 0.0])
    across = normalize(np.cross(direction, reference))
    other = np.cross(direction, across)

    # The stick bows slightly, in a direction of its own choosing.
    bow_angle = _noise(seed, 3) * math.tau
    bow = (across * math.cos(bow_angle) + other * math.sin(bow_angle))
    bow_depth = style.bend * length * (_noise(seed, 4) - 0.5) * 2.0

    steps = max(2, style.segments)
    previous = a
    for index in range(1, steps + 1):
        t = index / steps
        # Sine bow: zero at both ends, maximum in the middle.
        offset = bow * bow_depth * math.sin(math.pi * (t - 0.5) + math.pi * 0.5)
        offset = bow * bow_depth * math.sin(math.pi * t)
        point = a + axis * t + offset
        mid = (t + (index - 1) / steps) * 0.5
        # Thickness varies smoothly along the stick rather than
        # independently per segment: independent draws put a visible
        # step at every joint and the stick read as a string of beads.
        swell = (
            math.sin(mid * math.pi * (1.0 + _noise(seed, 21) * 2.0)
                     + _noise(seed, 22) * math.tau)
            + 0.45 * math.sin(mid * math.pi * 4.0 + _noise(seed, 23) * 6.0)
        ) / 1.45
        thickness = radius * (1.0 + style.taper * swell)
        colour = tint or wood_colour(seed, mid, style.weathered)
        batch.cylinder(previous, point, max(0.01, thickness), colour, sides)
        previous = point

    if tint is None and _noise(seed, 5) < style.knots:
        # One knot, somewhere along the middle two thirds.
        t = 0.18 + _noise(seed, 6) * 0.64
        centre = a + axis * t + bow * bow_depth * math.sin(math.pi * t)
        face = across * math.cos(_noise(seed, 7) * math.tau) + \
            other * math.sin(_noise(seed, 7) * math.tau)
        batch.sphere(centre + face * radius * 0.55, radius * 0.52,
                     KNOT_TONE, 4, 8)

    if tint is None and _noise(seed, 8) < style.bark:
        # A strip of bark still clinging to one face.
        start_t = _noise(seed, 9) * 0.5
        end_t = start_t + 0.25 + _noise(seed, 10) * 0.35
        face = across * math.cos(_noise(seed, 13) * math.tau) + \
            other * math.sin(_noise(seed, 13) * math.tau)
        batch.cylinder(
            a + axis * start_t + face * radius * 0.75,
            a + axis * min(1.0, end_t) + face * radius * 0.75,
            radius * 0.36, BARK_TONE, 5)


def draw_glue(batch, point, radius: float, seed: int) -> None:
    """A blob of adhesive that squeezed out and was never cleaned off."""
    point = np.asarray(point, dtype=np.float64)
    blobs = 1 + int(_noise(seed, 31) * 2.9)
    for index in range(blobs):
        angle = _noise(seed, 32 + index) * math.tau
        tilt = _noise(seed, 40 + index) * math.pi
        offset = np.array([
            math.cos(angle) * math.sin(tilt),
            math.sin(angle) * math.sin(tilt),
            math.cos(tilt),
        ]) * radius * (0.6 + _noise(seed, 50 + index) * 0.8)
        batch.sphere(point + offset,
                     radius * (0.30 + _noise(seed, 60 + index) * 0.45),
                     GLUE_TONE, 3, 7)


def draw_patch(batch, corners, seed: int, thickness: float = 0.06) -> None:
    """Sideways planks nailed over a panel, because the sheet was short."""
    corners = np.asarray(corners, dtype=np.float64)
    centre = corners.mean(axis=0)
    edge = corners[1] - corners[0]
    span = float(np.linalg.norm(edge))
    if span < 1e-6:
        return
    along = edge / span
    normal = normalize(np.cross(edge, corners[2] - corners[0]))
    across = np.cross(normal, along)
    planks = 3 + int(_noise(seed, 71) * 2.9)
    for index in range(planks):
        t = (index + 0.5) / planks - 0.5
        offset = across * t * span * 0.62
        wobble = along * (_noise(seed, 80 + index) - 0.5) * span * 0.16
        start = centre + offset + wobble - along * span * 0.34
        end = centre + offset + wobble + along * span * 0.34
        batch.cylinder(start + normal * thickness, end + normal * thickness,
                       span * 0.055, wood_colour(seed + index * 7, 0.5, 0.25),
                       4)


def draw_cardboard(batch, corners, seed: int, bind: float,
                   offset: float = 0.10) -> None:
    """Shredded cardboard, flying in and binding down onto a panel.

    ``bind`` runs 0 to 1: at 0 the strips are still out in the air, at 1
    they have laid down flat and become the shell.
    """
    corners = np.asarray(corners, dtype=np.float64)
    centre = corners.mean(axis=0)
    normal = normalize(centre)
    strips = 5 + int(_noise(seed, 90) * 4.9)
    for index in range(strips):
        a_index = index % 3
        b_index = (index + 1) % 3
        base_a = corners[a_index] * 0.82 + centre * 0.18
        base_b = corners[b_index] * 0.82 + centre * 0.18
        drift = normal * (1.0 - bind) * (1.6 + _noise(seed, 91 + index) * 2.4)
        spin = (1.0 - bind) * (_noise(seed, 100 + index) - 0.5) * 2.2
        swirl = np.cross(normal, base_b - base_a) * spin * 0.35
        tone = CARDBOARD_TONES[index % len(CARDBOARD_TONES)]
        batch.cylinder(
            base_a + drift + swirl + normal * offset,
            base_b + drift - swirl + normal * offset,
            0.075 + _noise(seed, 110 + index) * 0.05,
            (tone[0], tone[1], tone[2], 0.55 + 0.45 * bind), 4)


def led_colour(index: int, phase: float) -> tuple[float, float, float, float]:
    """A saturated colour off a rotating rainbow, for strip lighting."""
    hue = (index * 0.137 + phase) % 1.0
    sector = hue * 6.0
    fraction = sector - math.floor(sector)
    q, t = 1.0 - fraction, fraction
    table = (
        (1.0, t, 0.0), (q, 1.0, 0.0), (0.0, 1.0, t),
        (0.0, q, 1.0), (t, 0.0, 1.0), (1.0, 0.0, q),
    )
    r, g, b = table[int(sector) % 6]
    return (0.25 + r * 0.75, 0.25 + g * 0.75, 0.25 + b * 0.75, 1.0)


def draw_led_run(batch, a, b, seed: int, phase: float, spacing: float = 0.42,
                 radius: float = 0.075) -> None:
    """A run of individually coloured lamps along an edge."""
    a = np.asarray(a, dtype=np.float64)
    b = np.asarray(b, dtype=np.float64)
    length = float(np.linalg.norm(b - a))
    count = max(2, int(length / spacing))
    for index in range(count + 1):
        t = index / count
        batch.sphere(a + (b - a) * t, radius,
                     led_colour(seed + index, phase), 3, 7)


def validate_timber() -> None:
    """Grain must be stable, and every helper must draw something."""
    from .render_kit import TriangleBatch

    # The same stick must produce the same colour every single time.
    for seed in (0, 7, 41, 999):
        first = wood_colour(seed, 0.4)
        assert wood_colour(seed, 0.4) == first, seed
        assert all(0.0 <= channel <= 1.0 for channel in first), first
    # Different sticks must not all look identical.
    tones = {wood_colour(seed, 0.5) for seed in range(24)}
    assert len(tones) > 8, len(tones)
    # Weathering must move colour toward grey, never past it.
    fresh = wood_colour(3, 0.5, 0.0)
    aged = wood_colour(3, 0.5, 1.0)
    assert aged != fresh
    assert all(0.0 <= channel <= 1.0 for channel in aged), aged

    batch = TriangleBatch()
    before = len(batch.vertices)
    draw_timber(batch, (0, 0, 0), (4, 0, 0), 0.2, 5, CHAINSAW)
    assert len(batch.vertices) > before, "timber drew nothing"

    for helper, args in (
        (draw_glue, ((0, 0, 1), 0.3, 5)),
        (draw_patch, (np.array([[0, 0, 0], [2, 0, 0], [1, 2, 0]]), 5)),
        (draw_cardboard, (np.array([[0, 0, 2], [2, 0, 2], [1, 2, 2]]), 5, 0.5)),
        (draw_led_run, ((0, 0, 0), (3, 0, 0), 1, 0.25)),
    ):
        mark = len(batch.vertices)
        helper(batch, *args)
        assert len(batch.vertices) > mark, helper.__name__

    # A zero-length stick must be skipped, not crash.
    mark = len(batch.vertices)
    draw_timber(batch, (1, 1, 1), (1, 1, 1), 0.2, 3)
    assert len(batch.vertices) == mark

    # LED colours must stay in gamut across the whole rotation.
    for index in range(12):
        for phase in (0.0, 0.33, 0.9):
            colour = led_colour(index, phase)
            assert all(0.0 <= channel <= 1.0 for channel in colour), colour
