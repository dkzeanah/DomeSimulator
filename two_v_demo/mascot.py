"""The project's character: a polygonal jellyfish who talks the script.

Every film in this repository had one voice and no face. This adds a second
presence that can stand in the frame, speak in its own voice at the moments it
is cued for, and wear the tone of the passage it is standing in -- so a film can
say "this part is warm" or "this part is a joke" with something other than
typography.

What is new here is only the body. The expression layer is
:mod:`two_v_demo.drama_face`, which already had everything needed and is not
humanoid anywhere that matters:

* :class:`~two_v_demo.drama_face.FaceState` is ten signed channels, nothing else;
* :data:`~two_v_demo.drama_face.EXPRESSIONS` is the vocabulary
  (SHOCK, DISDAIN, SMIRK, RESOLVE, ...);
* :func:`~two_v_demo.drama_face.speech_jaw` opens a mouth on the vowel groups of
  the actual line being said, and :func:`~two_v_demo.drama_face.blink_amount`
  keeps it alive.

Reusing that vocabulary rather than inventing a second one means a jellyfish and
a human in the same repository express surprise the same way, which is the whole
argument for having a shared expression layer.

**Determinism.** These films are re-rendered, and a re-render that blinks at a
different moment is a different film. ``drama_face.blink_amount`` phases blinks
from ``abs(hash(character_id))``, and Python randomises string hashing per
process, so its blinks already differ run to run. This module does not repeat
that: :func:`blink_phase` uses CRC32, which is stable across interpreters.

Nothing here is random. Every value is a function of (mood, time, line), which
is what keeps a frame reproducible.
"""

from __future__ import annotations

import math
import zlib
from dataclasses import dataclass

import numpy as np

from .drama_face import EXPRESSIONS, FaceState, speech_jaw
from .geometry import normalize

MASCOT_NAME = "Lumen"
"""What it is called on screen. One constant, because a character's name should
not be spelled out in forty-two chapters."""

VOICE = "en-US-AvaMultilingualNeural"
"""A different voice from the house narrator, and the reason the character is a
character rather than a caption. The narrator is ``en-US-AndrewMultilingualNeural``
at ``+2%``; this is another voice entirely, quicker and higher, so the two are
never mistaken for one person changing tone."""

RATE = "+16%"
PITCH = "+14Hz"
VOLUME = "+0%"


def voice_settings() -> tuple[str, str, str, str]:
    """The character's voice, as the audio layer wants it."""
    return VOICE, RATE, PITCH, VOLUME


# ----------------------------------------------------------------------
# Moods: the tone of a passage, as colour and expression
# ----------------------------------------------------------------------

class Mood:
    """One register the character can be in.

    The shape copies :data:`two_v_demo.callouts.TONES` -- a string key into a
    module-level table -- because that is how this repository already keys a
    colour off a word. It is called *mood* rather than *tone* on purpose:
    ``Callout.tone`` already exists one level down and two different tones in
    one codebase would be a real collision rather than a tidy coincidence.
    """

    __slots__ = ("key", "body", "glow", "rim", "expression", "energy", "note")

    def __init__(self, key: str, body, glow, rim, expression: str,
                 energy: float, note: str) -> None:
        self.key = key
        self.body = body
        self.glow = glow
        self.rim = rim
        self.expression = expression
        self.energy = energy
        self.note = note

    def face(self) -> FaceState:
        return EXPRESSIONS[self.expression]


PINK = (1.00, 0.36, 0.72, 1.0)
CYBER = (0.35, 0.95, 1.00, 1.0)

MOODS: dict[str, Mood] = {
    # The character's own resting skin. Everything else is a departure from it.
    "neutral": Mood(
        "neutral", (0.86, 0.47, 0.78, 1.0), (0.55, 0.92, 1.00, 0.30),
        (0.98, 0.62, 0.88, 1.0), "NEUTRAL", 0.35,
        "the resting pink cyber jelly"),
    # Something generous is being said -- a gift, a wish, somebody's mother.
    "warm": Mood(
        "warm", (0.98, 0.55, 0.58, 1.0), (1.00, 0.80, 0.55, 0.32),
        (1.00, 0.78, 0.66, 1.0), "PLEADING", 0.30,
        "soft, open, leaning in"),
    # The dry aside. This is the one the snarky cut lives in.
    "dry": Mood(
        "dry", (0.72, 0.42, 0.66, 1.0), (0.42, 0.72, 0.86, 0.22),
        (0.86, 0.52, 0.72, 1.0), "DISDAIN", 0.18,
        "flat, unimpressed, one eyebrow"),
    # The pitch when it is actually excited, and the jokes that land.
    "hyped": Mood(
        "hyped", PINK, CYBER, (0.70, 1.00, 0.95, 1.0), "SHOCK", 1.00,
        "full pink, maximum bounce"),
    # Money, risk, the failure, the number that does not help the argument.
    "grave": Mood(
        "grave", (0.44, 0.40, 0.72, 1.0), (0.35, 0.55, 0.90, 0.24),
        (0.62, 0.60, 0.92, 1.0), "RESOLVE", 0.15,
        "dim, still, no jokes"),
    # A claim that is doing a lot of work.
    "smug": Mood(
        "smug", (0.95, 0.46, 0.70, 1.0), (0.60, 1.00, 0.78, 0.28),
        (0.62, 1.00, 0.72, 1.0), "SMIRK", 0.45,
        "pleased with itself, green rim"),
    # The opposite number, the banking system, the thing that does not work.
    "alarmed": Mood(
        "alarmed", (1.00, 0.36, 0.42, 1.0), (1.00, 0.66, 0.30, 0.34),
        (1.00, 0.72, 0.35, 1.0), "FEAR", 0.85,
        "wide-eyed, hot, orange rim"),
}

MOOD_KEYS: tuple[str, ...] = tuple(MOODS)


def mood(key: str | None) -> Mood:
    """One mood by name, with the list of them in the error rather than a KeyError."""
    if not key:
        return MOODS["neutral"]
    try:
        return MOODS[key]
    except KeyError:
        raise KeyError(
            f"no mood {key!r}; choose from {', '.join(MOOD_KEYS)}") from None


# ----------------------------------------------------------------------
# Being alive
# ----------------------------------------------------------------------

BLINK_PERIOD_S = 5.1
BLINK_LENGTH_S = 0.14


def blink_phase(name: str) -> float:
    """A stable phase offset for one character, in seconds.

    CRC32 rather than ``hash()``: Python salts string hashing per process, so a
    blink driven by ``hash`` lands somewhere different every run and the film
    stops being reproducible. This is the same number in every interpreter.
    """
    return (zlib.crc32(name.encode("utf-8")) % 1000) / 1000.0 * BLINK_PERIOD_S


def blink_amount(name: str, time_s: float) -> float:
    """How closed the eyes are from blinking alone, 0..1."""
    into = (time_s + blink_phase(name)) % BLINK_PERIOD_S
    if into > BLINK_LENGTH_S:
        return 0.0
    return math.sin(into / BLINK_LENGTH_S * math.pi)


def face_at(mood_key: str, time_s: float, *, speaking: str = "",
            elapsed: float = -1.0, duration: float = 0.0,
            gaze: tuple[float, float] = (0.0, 0.0),
            blend_to: str | None = None, blend: float = 0.0) -> FaceState:
    """The whole face at one instant, from everything that drives it.

    The mood sets the resting expression; speaking overrides the jaw on the
    vowel groups of the line actually being said; the blink rides on top. A
    mood can also be blended toward another, which is how the character changes
    its mind partway through a chapter.
    """
    state = mood(mood_key).face()
    if blend_to is not None and blend > 0.0:
        state = state.blend(mood(blend_to).face(), min(1.0, blend))

    jaw = state.jaw_open
    if speaking and elapsed >= 0.0:
        jaw = max(jaw, speech_jaw(speaking, elapsed, duration))
    # A shocked face does not blink; everything else does.
    blink = blink_amount(MASCOT_NAME, time_s) * (
        0.15 if state.eye_open > 1.2 else 1.0)
    return FaceState(
        brow_raise=state.brow_raise, brow_tilt=state.brow_tilt,
        eye_open=max(0.05, state.eye_open * (1.0 - blink)),
        gaze_side=state.gaze_side + gaze[0],
        gaze_up=state.gaze_up + gaze[1],
        jaw_open=jaw, mouth_curve=state.mouth_curve,
        mouth_width=state.mouth_width, smirk=state.smirk,
    )


# ----------------------------------------------------------------------
# The body
# ----------------------------------------------------------------------

BELL_SEGMENTS = 8
BELL_RINGS = 3
"""Deliberately low. At any higher count the bell reads as a smooth dome, and
the whole point of this character is that it is visibly polygonal -- the same
argument the dome films make about triangles, made in a single object."""

TENTACLES = 6


def _bell(batch, centre, radius: float, height: float, colour,
          segments: int, rings: int, squash: float) -> None:
    """A faceted bell, open at the bottom, closed at the apex."""
    centre = np.asarray(centre, dtype=float)

    def on_surface(latitude: float, longitude: float) -> np.ndarray:
        ring = radius * math.cos(latitude)
        return centre + np.array([
            ring * math.cos(longitude),
            ring * math.sin(longitude),
            height * math.sin(latitude) * squash,
        ])

    top = (rings - 1) / rings * (math.pi * 0.5)
    for band in range(rings - 1):
        low = band / rings * (math.pi * 0.5)
        high = (band + 1) / rings * (math.pi * 0.5)
        for index in range(segments):
            a = math.tau * index / segments
            b = math.tau * (index + 1) / segments
            batch.quad(on_surface(low, a), on_surface(low, b),
                       on_surface(high, b), on_surface(high, a), colour)
    apex = centre + np.array([0.0, 0.0, height * squash])
    for index in range(segments):
        a = math.tau * index / segments
        b = math.tau * (index + 1) / segments
        batch.triangle(on_surface(top, a), on_surface(top, b), apex, colour)


def _rim(batch, centre, radius: float, colour, segments: int,
         drop: float) -> None:
    """The flange under the bell: a short skirt that gives it a silhouette."""
    centre = np.asarray(centre, dtype=float)
    for index in range(segments):
        a = math.tau * index / segments
        b = math.tau * (index + 1) / segments
        inner_a = centre + np.array([radius * math.cos(a), radius * math.sin(a), 0.0])
        inner_b = centre + np.array([radius * math.cos(b), radius * math.sin(b), 0.0])
        outer = radius * 1.13
        outer_a = centre + np.array([outer * math.cos(a), outer * math.sin(a), -drop])
        outer_b = centre + np.array([outer * math.cos(b), outer * math.sin(b), -drop])
        batch.quad(inner_a, inner_b, outer_b, outer_a, colour)


def _tentacles(batch, centre, radius: float, colour, *, phase: float,
               energy: float, time_s: float, count: int = TENTACLES,
               length: float = 1.5) -> None:
    """Tapered ribbons hanging off the rim, waving on their own offsets.

    Every tentacle gets its own phase from its index, so they never move as one
    body -- a jellyfish that pulses in unison reads as a machine.
    """
    centre = np.asarray(centre, dtype=float)
    steps = 4
    for which in range(count):
        angle = math.tau * which / count + phase
        anchor = centre + np.array([radius * 0.86 * math.cos(angle),
                                    radius * 0.86 * math.sin(angle), -0.05])
        drift = math.tau * which / count + 0.8
        for step in range(steps):
            share_a = step / steps
            share_b = (step + 1) / steps
            radius_a = radius * (0.052 - 0.034 * share_a)
            radius_b = radius * (0.052 - 0.034 * share_b)
            wave_a = math.sin(time_s * (1.4 + energy) + drift + share_a * 3.1)
            wave_b = math.sin(time_s * (1.4 + energy) + drift + share_b * 3.1)
            swing = 0.20 + 0.34 * energy
            a = anchor + np.array([
                wave_a * swing * share_a * radius,
                math.cos(drift) * wave_a * swing * share_a * radius * 0.6,
                -length * radius * share_a,
            ])
            b = anchor + np.array([
                wave_b * swing * share_b * radius,
                math.cos(drift) * wave_b * swing * share_b * radius * 0.6,
                -length * radius * share_b,
            ])
            batch.cylinder(a, b, (radius_a + radius_b) * 0.5, colour, 4)


# ----------------------------------------------------------------------
# The face
# ----------------------------------------------------------------------

EYE_WHITE = (0.98, 0.98, 1.00, 1.0)
PUPIL = (0.10, 0.06, 0.16, 1.0)
BROW = (0.34, 0.10, 0.32, 1.0)
MOUTH = (0.30, 0.06, 0.26, 1.0)
MOUTH_DARK = (0.08, 0.02, 0.10, 1.0)


def draw_jelly_face(batch, centre, radius: float, height: float,
                    forward, side, up, face: FaceState) -> None:
    """A face on the front of the bell.

    Not :func:`two_v_demo.drama_face.draw_face`, which derives its scale from
    humanoid shoulder joints. The channels are the same: jelly proportions want
    a bigger eye and a wider mouth than a person, but SHOCK means the same
    thing on both.
    """
    centre = np.asarray(centre, dtype=float)
    forward = normalize(np.asarray(forward, dtype=float))
    side = normalize(np.asarray(side, dtype=float))
    up = normalize(np.asarray(up, dtype=float))

    def on_bell(side_offset: float, up_offset: float,
                out: float = 1.0, lift: float = 1.0) -> np.ndarray:
        """A point on the bell's surface, from a direction out of its centre.

        Scaling each axis by its own radius is what puts the point *on* the
        ellipsoid: a unit direction times (rx, ry, rz) satisfies the ellipsoid
        equation exactly. Offsets measured from the centre instead drop the
        features *inside* the bell, where it hides them and the character
        renders with a blank face -- which is exactly what the first cut of
        this did, at ``lift=0.99``.

        ``lift`` pushes a feature proud of the surface, so a brow or a mouth
        cylinder is half-exposed rather than half-swallowed.
        """
        direction = normalize(forward * max(0.25, out)
                              + side * side_offset + up * up_offset)
        return centre + np.array([direction[0] * radius,
                                  direction[1] * radius,
                                  direction[2] * height]) * lift

    eye_span = 0.30
    eye_height = 0.16
    eye_radius = radius * 0.24 * max(0.12, face.eye_open)

    for sign in (-1.0, 1.0):
        eye_direction = normalize(forward + side * (sign * eye_span)
                                  + up * eye_height)
        # Sits ON the surface, so half the eye protrudes and half is held by
        # the bell. Any deeper and the bell simply covers it.
        eye = on_bell(sign * eye_span, eye_height)
        batch.sphere(eye, eye_radius, EYE_WHITE, 4, 8)
        pupil = (eye + eye_direction * (eye_radius * 0.62)
                 + side * (face.gaze_side * eye_radius * 0.55)
                 + up * (face.gaze_up * eye_radius * 0.55))
        batch.sphere(pupil, eye_radius * 0.62, PUPIL, 4, 8)

        # The brow: a bar whose inner end drops for anger and lifts for
        # pleading. Tilt does most of the emotional work, same as on a person.
        brow_height = eye_height + 0.26 + face.brow_raise * 0.13
        inner = on_bell(sign * (eye_span - 0.15),
                        brow_height - face.brow_tilt * 0.12, lift=1.04)
        outer = on_bell(sign * (eye_span + 0.14),
                        brow_height + face.brow_tilt * 0.05, 0.94, lift=1.04)
        batch.cylinder(inner, outer, radius * 0.085, BROW, 6)

    # The mouth: five points across, corners lifting or falling, opening into a
    # dark aperture as the jaw drops.
    width = 0.36 * face.mouth_width
    corners = []
    for step in range(5):
        across = (step / 4.0 - 0.5) * 2.0
        lift = -0.30 + face.mouth_curve * 0.13 * (1.0 - abs(across))
        if face.smirk:
            lift += face.smirk * 0.08 * across
        corners.append(on_bell(across * width, lift, lift=1.04))
    for first, second in zip(corners, corners[1:]):
        batch.cylinder(first, second, radius * 0.070, MOUTH, 6)
    if face.jaw_open > 0.03:
        aperture = on_bell(0.0, -0.32 - face.jaw_open * 0.10, lift=1.03)
        batch.sphere(aperture, radius * (0.08 + 0.17 * face.jaw_open),
                     MOUTH_DARK, 4, 9)


# ----------------------------------------------------------------------
# The whole character
# ----------------------------------------------------------------------

def draw_jelly(opaque, transparent, centre, *, mood_key: str = "neutral",
               time_s: float = 0.0, yaw_deg: float = 0.0, size: float = 1.0,
               face: FaceState | None = None, glow: bool = True) -> FaceState:
    """The character, in the world, at one instant.

    ``size`` is the bell's radius in metres, so a caller places a jellyfish the
    same way it places anything else in a scene. Returns the face it wore, so a
    cut-in drawn later in the same frame can wear the identical one.
    """
    state = mood(mood_key)
    if face is None:
        face = face_at(mood_key, time_s)

    centre = np.asarray(centre, dtype=float)
    radius = 0.30 * size
    height = radius * 1.05
    yaw = math.radians(yaw_deg)
    forward = np.array([math.cos(yaw), math.sin(yaw), 0.0])
    side = np.array([-math.sin(yaw), math.cos(yaw), 0.0])
    up = np.array([0.0, 0.0, 1.0])

    # A slow bob and squash, at the mood's own energy. Still at `grave`,
    # bouncing at `hyped`, which is most of what makes the mood legible from
    # across a room before the face is even read.
    energy = state.energy
    bob = math.sin(time_s * (0.9 + energy * 1.5)) * radius * (0.05 + 0.16 * energy)
    squash = 1.0 + math.sin(time_s * (1.4 + energy * 1.7)) * (0.03 + 0.10 * energy)
    body_centre = centre + np.array([0.0, 0.0, bob])

    _bell(opaque, body_centre, radius / sqrt_squash(squash), height * squash,
          state.body, BELL_SEGMENTS, BELL_RINGS, 1.0)
    _rim(opaque, body_centre, radius / sqrt_squash(squash), state.rim,
         BELL_SEGMENTS, radius * 0.14)
    _tentacles(opaque, body_centre, radius, state.rim, phase=yaw * 0.5,
               energy=energy, time_s=time_s)
    draw_jelly_face(opaque, body_centre, radius, height, forward, side, up, face)

    if glow and transparent is not None:
        _bell(transparent, body_centre - np.array([0.0, 0.0, radius * 0.05]),
              radius * 0.66 / sqrt_squash(squash), height * squash * 0.66,
              state.glow, BELL_SEGMENTS, BELL_RINGS, 1.0)
    return face


def sqrt_squash(squash: float) -> float:
    """Widen what the squash narrows, so the bell keeps its volume.

    A bell that only stretched would look like it was being pulled rather than
    breathing, and the correction is one term rather than an animation.
    """
    return math.sqrt(max(0.2, squash))


# ----------------------------------------------------------------------
# The cut-in
# ----------------------------------------------------------------------

def jelly_cutin(pg, surface, centre, size: float, *, mood_key: str = "neutral",
                face: FaceState | None = None, alpha: float = 1.0,
                time_s: float = 0.0) -> None:
    """The same character, drawn flat, for when it is speaking to camera.

    Vector rather than a rendered sprite: it costs nothing, it is sharp at any
    frame size, and it stays in step with the 3-D one because both read the
    same :class:`FaceState`.
    """
    if alpha <= 0.004 or size < 8.0:
        return
    state = mood(mood_key)
    if face is None:
        face = face_at(mood_key, time_s)

    def rgba(colour, scale=1.0):
        """A render colour as a pygame one, clamped. `scale` above 1.0 is how a
        lighter shade of a mood is asked for, and it has to saturate rather
        than raise: pygame rejects a channel over 255."""
        return tuple(
            min(255, max(0, int(colour[channel] * 255 * scale)))
            for channel in range(3)
        ) + (int(255 * alpha),)

    cx, cy = centre
    radius = size * 0.5
    height = radius * 0.88
    layer = pg.Surface((int(size * 2.6), int(size * 3.2)), pg.SRCALPHA)
    lx = layer.get_width() * 0.5
    rim_y = layer.get_height() * 0.42
    """The bell's rim line. Everything else is placed relative to it: the dome
    above, the tentacles below, the face across it."""

    body = rgba(state.body)
    rim = rgba(state.rim)

    # A soft halo. Concentric circles at one low alpha, added together: the
    # overlaps accumulate toward the middle and fall off at the rim, which is
    # a gradient without needing one. A single filled disc read as a coloured
    # plate the character was standing in front of, and multiplying a stack of
    # them just made a darker plate.
    halo = pg.Surface(layer.get_size(), pg.SRCALPHA)
    glow_rgb = tuple(min(255, max(0, int(channel * 255)))
                     for channel in state.glow[:3])
    halo_y = int(rim_y - height * 0.35)
    steps = 9
    for step in range(steps):
        share = 1.0 - step / steps
        pg.draw.circle(halo, glow_rgb + (20,), (int(lx), halo_y),
                       int(radius * (0.62 + 0.74 * share)), 0)
    layer.blit(halo, (0, 0), special_flags=pg.BLEND_RGBA_ADD)

    # The bell: a dome over the rim, closed by a shallow bulge underneath.
    # The first cut of this swept `pi + tau*i/n`, which is more than half a
    # turn and doubled back on itself -- the character came out as a
    # five-sided arrowhead rather than a jellyfish.
    dome = []
    for index in range(BELL_SEGMENTS + 1):
        angle = math.pi - math.pi * index / BELL_SEGMENTS
        dome.append((lx + radius * math.cos(angle),
                     rim_y - height * math.sin(angle)))
    belly = []
    steps = max(3, BELL_SEGMENTS // 2)
    for index in range(1, steps):
        share = index / steps
        belly.append((lx + radius * (1.0 - 2.0 * share),
                      rim_y + radius * 0.16 * math.sin(math.pi * share)))
    outline = dome + belly
    pg.draw.polygon(layer, body, outline)
    pg.draw.lines(layer, rim, True, outline, max(2, int(radius * 0.045)))

    # An inner shelf, so the bell has a lit upper face rather than reading flat.
    shelf = [(lx + radius * 0.66 * math.cos(math.pi - math.pi * i / 6),
              rim_y - height * 0.62 - height * 0.30 * math.sin(math.pi * i / 6))
             for i in range(7)]
    pg.draw.lines(layer, rgba(state.glow, 1.6), False, shelf,
                  max(1, int(radius * 0.05)))

    # Tentacles from points along the rim, each on its own phase, tapering as
    # they fall. Drawn segment by segment because a single polyline has one
    # width and a jellyfish with thick tentacle tips looks like a caterpillar.
    for which in range(TENTACLES):
        share = (which + 0.5) / TENTACLES
        x = lx + radius * (1.0 - 2.0 * share)
        wave = math.sin(time_s * (1.4 + state.energy) + which * 1.1)
        swing = (0.10 + 0.24 * state.energy) * radius
        points = [(x, rim_y + radius * 0.10 * math.sin(math.pi * share))]
        for step in range(1, 4):
            fall = step / 3.0
            points.append((
                x + wave * swing * fall + math.sin(share * 6.0) * radius * 0.06 * fall,
                rim_y + radius * 0.14 + radius * 0.60 * fall,
            ))
        for index in range(len(points) - 1):
            width = max(1, int(radius * (0.050 - 0.012 * index)))
            pg.draw.line(layer, rim, points[index], points[index + 1], width)

    # The face, from the same FaceState the 3-D body wears.
    eye_radius = max(1.0, radius * 0.155 * max(0.12, face.eye_open))
    for sign in (-1.0, 1.0):
        ex = lx + sign * radius * 0.30
        ey = rim_y - height * 0.46
        pg.draw.circle(layer, rgba(EYE_WHITE, 1.0), (int(ex), int(ey)),
                       int(eye_radius))
        px = ex + face.gaze_side * eye_radius * 0.55
        py = ey - face.gaze_up * eye_radius * 0.55
        pg.draw.circle(layer, rgba(PUPIL), (int(px), int(py)),
                       max(1, int(eye_radius * 0.56)))
        brow_y = ey - eye_radius - radius * (0.11 + face.brow_raise * 0.07)
        tilt = face.brow_tilt * radius * 0.11
        pg.draw.line(layer, rgba(BROW),
                     (ex - sign * eye_radius * 1.30, brow_y + sign * tilt),
                     (ex + sign * eye_radius * 1.30, brow_y - sign * tilt),
                     max(2, int(radius * 0.052)))

    mouth_y = rim_y - height * 0.19
    mouth_w = radius * 0.26 * face.mouth_width
    mouth = []
    for step in range(5):
        across = (step / 4.0 - 0.5) * 2.0
        lift = -face.mouth_curve * radius * 0.11 * (1.0 - abs(across))
        if face.smirk:
            lift -= face.smirk * radius * 0.075 * across
        mouth.append((lx + across * mouth_w, mouth_y + lift))
    pg.draw.lines(layer, rgba(MOUTH), False, mouth, max(2, int(radius * 0.050)))
    if face.jaw_open > 0.03:
        pg.draw.ellipse(layer, rgba(MOUTH_DARK), (
            int(lx - mouth_w * 0.40), int(mouth_y + radius * 0.02),
            int(mouth_w * 0.80), int(radius * (0.07 + 0.24 * face.jaw_open))))

    surface.blit(layer, (int(cx - layer.get_width() * 0.5),
                         int(cy - rim_y)))


# ----------------------------------------------------------------------
# Cues: when the character is on screen, and what it says
# ----------------------------------------------------------------------

DEFAULT_HOLD_S = 3.0

MASCOT_CHARS_PER_SECOND = 15.0
"""Only used to guess how long a line takes when its audio has not been
measured. The mascot speaks faster than the narrator, so this cannot borrow
the narrator's figure -- it would put the mouth out of step with the words."""


@dataclass(frozen=True)
class MascotCue:
    """One appearance, cued to the script rather than to a stopwatch.

    Shaped after :class:`two_v_demo.callouts.Callout`, and for the same reason:
    a cue written as "the phrase in the narration that summons it" survives the
    narration being re-timed by a slower or faster voice, and a cue written as
    "second 41.2" does not.
    """

    line: str = ""
    """What the character says. Empty means it appears and says nothing."""
    cue: str = ""
    """The phrase in the chapter's spoken text that brings it on."""
    at: float | None = None
    """Or a chapter progress from 0 to 1, when no words summon it."""
    hold: float | None = DEFAULT_HOLD_S
    """Seconds on screen; ``None`` holds it to the end of the chapter."""
    mood: str = ""
    """Overrides the chapter's mood for this appearance. Empty means inherit."""
    role: str = "cutin"
    """``cutin`` speaks to camera; ``wide`` stands in the scene with the subject."""
    note: str = ""
    """Why this one is here, for whoever reads the lesson next."""

    def seconds(self, measured: float | None = None) -> float:
        return max(0.7, len(self.line) / MASCOT_CHARS_PER_SECOND) if measured is None \
            else measured


@dataclass(frozen=True)
class Showing:
    """One cue, resolved onto the chapter's own clock."""

    cue: MascotCue
    start: float
    end: float
    mood: str

    def alpha(self, now: float) -> float:
        """Fade in and out, so the character arrives rather than switches on."""
        if now < self.start or now > self.end:
            return 0.0
        rise = min(1.0, (now - self.start) / 0.45)
        fall = min(1.0, (self.end - now) / 0.45)
        share = min(rise, fall)
        return share * share * (3.0 - 2.0 * share)


def resolve(chapter, chapter_seconds: float, speech_seconds: float | None = None,
            speak_promise: bool = True, timings=(),
            measured: dict | None = None) -> tuple[Showing, ...]:
    """Every mascot cue on a chapter, resolved, with start and end in seconds.

    Deliberately the same arithmetic as :func:`two_v_demo.callouts.schedule`,
    including the ``SPEECH_DELAY`` the mixer puts in front of every clip. A
    cue resolved by a different rule would drift away from the words that
    summoned it.
    """
    from .audio import SPEECH_DELAY as delay
    from .callouts import cue_position, cue_seconds, spoken_text

    from .audio import TAIL_PADDING

    spoken = spoken_text(chapter, speak_promise)
    if speech_seconds is None:
        # How long the narrator actually speaks, before any audio exists.
        # A chapter's authored duration is its speech plus the mixer's lead-in
        # and tail, so subtracting those back out recovers the span the words
        # occupy -- and a cue placed across that span lands where the words
        # are. Estimating it from a characters-per-second constant instead
        # overshot the chapter, which put the last cue past the end of the
        # chapter and produced a window that ended before it began.
        speech_seconds = max(1.0, chapter_seconds - delay - TAIL_PADDING)
    chapter_mood = getattr(chapter, "mood", "neutral")
    latest = max(0.5, chapter_seconds - 0.25)

    def arrival(item: MascotCue) -> float:
        if item.at is not None:
            return max(0.0, min(latest, item.at * chapter_seconds))
        position = cue_position(spoken, item.cue) if item.cue else None
        if position is None:
            return 0.0
        return delay + cue_seconds(spoken, position, speech_seconds, timings)

    showings: list[Showing] = []
    for cue in getattr(chapter, "mascot", ()) or ():
        # Always leave room for the character to be there at all. A cue whose
        # phrase falls in the last half-second of a chapter would otherwise
        # resolve to a window of zero, or of negative, length.
        start = max(0.0, min(arrival(cue), latest - 0.5))
        spoken_for = cue.seconds((measured or {}).get(cue.line))
        end = (latest if cue.hold is None
               else max(start + 0.5, min(latest, start + max(cue.hold,
                                                      spoken_for + 0.35))))
        showings.append(Showing(cue, start, end, cue.mood or chapter_mood))
    return tuple(showings)


def validate_cues(chapter, speak_promise: bool = True) -> None:
    """Everything that would make a chapter's mascot wrong, refused up front."""
    from .callouts import cue_position, spoken_text

    spoken = spoken_text(chapter, speak_promise)
    for cue in getattr(chapter, "mascot", ()) or ():
        if cue.mood and cue.mood not in MOODS:
            raise ValueError(
                f"chapter {chapter.number}: mascot cue has unknown mood "
                f"{cue.mood!r}; choose from {', '.join(MOOD_KEYS)}")
        if cue.role not in ("cutin", "wide"):
            raise ValueError(
                f"chapter {chapter.number}: mascot role must be 'cutin' or "
                f"'wide', not {cue.role!r}")
        if not cue.line and not cue.cue and cue.at is None:
            raise ValueError(
                f"chapter {chapter.number}: a mascot cue with no line, no cue "
                f"phrase and no position would never appear")
        if cue.cue and cue_position(spoken, cue.cue) is None:
            raise ValueError(
                f"chapter {chapter.number}: mascot cue {cue.cue!r} is not in "
                f"the spoken text, so the character would never be summoned")
        if cue.at is not None and not 0.0 <= cue.at <= 1.0:
            raise ValueError(
                f"chapter {chapter.number}: mascot cue at={cue.at} is not a "
                f"chapter progress")


# ----------------------------------------------------------------------
# Reading the renderer
# ----------------------------------------------------------------------

def _film_state(app):
    """(chapter, chapter_seconds, speech_seconds, timings) for the frame being drawn.

    Read defensively: a scene painter also runs against the selftest probe,
    which has a chapter and a camera and nothing else.
    """
    chapters = getattr(app, "chapters", None)
    index = getattr(app, "chapter_index", None)
    if not chapters or index is None:
        return None, 0.0, 0.0, ()
    try:
        chapter = chapters[index]
    except (IndexError, TypeError, KeyError):
        return None, 0.0, 0.0, ()
    durations = getattr(app, "chapter_durations", None) or ()
    speech = getattr(app, "speech_durations", None) or ()
    clips = getattr(app, "speech_clips", None) or ()
    chapter_seconds = float(durations[index]) if index < len(durations) else chapter.duration
    speech_seconds = float(speech[index]) if index < len(speech) else None
    timings = ()
    if index < len(clips):
        from .callouts import speech_timings
        try:
            timings = speech_timings(clips[index])
        except (OSError, ValueError):
            timings = ()
    return chapter, chapter_seconds, speech_seconds, timings


def showings_for(app) -> tuple[tuple[Showing, ...], float]:
    """What the character is doing right now, and how far into the chapter."""
    chapter, chapter_seconds, speech_seconds, timings = _film_state(app)
    if chapter is None:
        return (), 0.0
    progress = float(getattr(app, "chapter_progress", 0.0))
    showings = resolve(chapter, chapter_seconds, speech_seconds,
                       speak_promise=getattr(getattr(app, "lesson", None),
                                             "style", "teaching") != "hype",
                       timings=timings,
                       measured=getattr(app, "mascot_speech", None))
    return showings, progress * chapter_seconds


def active(app) -> Showing | None:
    """The appearance in progress, if there is one."""
    showings, now = showings_for(app)
    for showing in showings:
        if showing.alpha(now) > 0.004:
            return showing
    return None


def active_alpha(app) -> float:
    """How present the character is right now, 0..1.

    Split out because two callers want the number without the showing: the
    cut-in fades with it, and a profile's camera leans in on it.
    """
    showing = active(app)
    if showing is None:
        return 0.0
    _showings, now = showings_for(app)
    return showing.alpha(now)


def _phase(showing: Showing, now: float) -> tuple[FaceState, float, str]:
    """The face, the mouth's progress through its line, and the mood."""
    into = max(0.0, now - showing.start)
    face = face_at(showing.mood, now, speaking=showing.cue.line,
                   elapsed=into if showing.cue.line else -1.0,
                   duration=showing.cue.seconds())
    return face, into, showing.mood


# ----------------------------------------------------------------------
# Putting the character in a scene
# ----------------------------------------------------------------------

def in_scene(app, opaque, transparent, anchor, *, size: float = 1.35,
             yaw_deg: float | None = None, bob: float = 0.0) -> Showing | None:
    """Draw the character at a world anchor, for the cue that is live now.

    A painter calls this once and gets the wide-shot presence for free: if no
    cue is running, nothing is drawn and the chapter is exactly the chapter it
    was. ``yaw_deg=None`` turns it to face the camera, which is what a
    character addressing the audience should do.
    """
    showing = active(app)
    if showing is None or showing.cue.role not in ("cutin", "wide"):
        return None
    showings, now = showings_for(app)
    face, _into, mood_key = _phase(showing, now)
    yaw = float(getattr(app, "camera_yaw", 90.0)) if yaw_deg is None else yaw_deg
    # Fade by scale: the renderer's batches have no per-vertex alpha worth
    # fighting, and a character that eases in reads as arriving anyway.
    alpha = showing.alpha(now)
    scale = size * (0.55 + 0.45 * alpha)
    draw_jelly(opaque, transparent, np.asarray(anchor, dtype=float) +
               np.array([0.0, 0.0, bob]), mood_key=mood_key,
               time_s=getattr(app, "timeline", 0.0), yaw_deg=yaw,
               size=scale, face=face)
    return showing


def cutin(app):
    """What the cut-in should draw right now, or ``None``.

    Returns ``(showing, mood, face, alpha)``. The overlay owns placement; this
    owns the character, so the flat and the solid one can never disagree about
    what it looks like or what it is saying.
    """
    showing = active(app)
    if showing is None or showing.cue.role != "cutin":
        return None
    showings, now = showings_for(app)
    face, _into, mood_key = _phase(showing, now)
    return showing, mood_key, face, showing.alpha(now)


def draw_mascot_ui(app, surface, width: int, height: int,
                   style: str = "hype") -> bool:
    """The speaking cut-in, in the overlay, when the character is talking.

    Placed in a corner rather than in a reserved region. Reserving one would
    put the character into :func:`two_v_demo.callouts.free_region`, which also
    drives the camera fit -- so a cue arriving mid-chapter would shove the
    camera sideways at the exact moment it is supposed to be a beat. A fixed
    corner never moves the picture.

    Returns whether it drew, so a caller can tell "no cue" from "drew nothing".
    """
    state = cutin(app)
    if state is None:
        return False
    showing, mood_key, face, alpha = state
    if alpha <= 0.004:
        return False

    portrait = bool(getattr(getattr(app, "frame", None), "portrait", False))
    size = min(width, height) * (0.26 if not portrait else 0.20)
    if portrait:
        # Above the card, which owns the bottom of a phone frame.
        centre = (width * 0.5, height * 0.28)
    else:
        # Left flank, vertically centred. The hype headline and its scrim own
        # the bottom of the frame and the worksheet owns the right, so this is
        # the one large area neither of them claims. Set in far enough that the
        # character's own line -- which is always wider than the character --
        # sits fully inside the frame rather than clamped against the edge.
        centre = (max(width * 0.19, size * 0.85), height * 0.44)
    jelly_cutin(app.pygame, surface, centre, size, mood_key=mood_key,
                face=face, alpha=alpha,
                time_s=float(getattr(app, "timeline", 0.0)))

    if not showing.cue.line:
        return True
    # Its words, beside it. The film already carries subtitles, but a character
    # speaking to camera without its line next to it reads as a logo.
    pg = app.pygame
    accent = mood(mood_key).rim
    colour = (min(255, int(accent[0] * 255)), min(255, int(accent[1] * 255)),
              min(255, int(accent[2] * 255)), int(255 * alpha))
    text = app.font(int(size * 0.24), bold=True).render(
        showing.cue.line, True, colour[:3])
    text.set_alpha(colour[3])
    # Clamped inside the frame, with room for the backdrop's own margin: a line
    # wider than the space the character sits in ran off the left edge, which
    # is the one place a caption is unreadable rather than badly placed.
    pad = 16
    x = int(min(max(centre[0] - text.get_width() * 0.5, pad),
                max(pad, width - text.get_width() - pad)))
    y = int(min(centre[1] + size * (0.62 if portrait else 0.78),
                height - text.get_height() - 14))
    backdrop = pg.Surface((text.get_width() + 22, text.get_height() + 12),
                          pg.SRCALPHA)
    backdrop.fill((6, 10, 20, int(190 * alpha)))
    surface.blit(backdrop, (x - 11, y - 6))
    surface.blit(text, (x, y))
    return True


# ----------------------------------------------------------------------
# Proof
# ----------------------------------------------------------------------

def validate_mascot() -> None:
    """Prove the character before it appears in a film.

    Three things are checked, and the third is the one that matters: this
    repository re-renders films, and a character that blinks at a different
    moment every run is a different film every run.
    """
    from .render_kit import TriangleBatch

    assert MOODS, "no moods defined"
    for key, entry in MOODS.items():
        assert key == entry.key, (key, entry.key)
        assert entry.expression in EXPRESSIONS, (key, entry.expression)
        assert 0.0 <= entry.energy <= 1.0, (key, entry.energy)
        assert entry.note, key
        for channel in (entry.body, entry.glow, entry.rim):
            assert len(channel) == 4, (key, channel)
            assert all(0.0 <= value <= 1.0 for value in channel), (key, channel)
    assert "neutral" in MOODS, "the resting mood has to exist"

    # Geometry: real, finite and non-empty at every mood and phase, and at the
    # extremes of the face channels rather than only at rest.
    for key in MOODS:
        for phase in (0.0, 0.25, 0.5, 0.75):
            for speaking in ("", "a line long enough to move a mouth"):
                opaque, transparent = TriangleBatch(), TriangleBatch()
                face = face_at(key, phase * BLINK_PERIOD_S * 3,
                               speaking=speaking, elapsed=0.1 * len(speaking),
                               duration=1.2)
                worn = draw_jelly(opaque, transparent, (1.0, 2.0, 0.5),
                                  mood_key=key, time_s=phase * 7.0,
                                  yaw_deg=phase * 360.0, face=face)
                assert worn is face
                assert opaque.vertices, (key, phase, speaking)
                assert transparent.vertices, (key, phase)
                assert np.isfinite(np.asarray(opaque.vertices)).all(), (key, phase)
                assert np.isfinite(np.asarray(transparent.vertices)).all(), (key, phase)

    # A mood's own face has to actually differ from neutral, or the colour is
    # carrying the whole performance and the "expression" is decoration.
    for key, entry in MOODS.items():
        if key == "neutral":
            continue
        assert entry.face() != MOODS["neutral"].face(), key

    # Determinism. Two separate processes must agree, which `hash()` cannot do.
    phases = [blink_phase(MASCOT_NAME), blink_phase("someone else")]
    assert all(isinstance(value, float) for value in phases)
    assert blink_phase(MASCOT_NAME) == blink_phase(MASCOT_NAME)
    assert blink_phase(MASCOT_NAME) != blink_phase("someone else"), (
        "two characters would blink in unison")
    samples = [blink_amount(MASCOT_NAME, t) for t in (0.0, 1.0, 5.1, 9.9)]
    assert all(0.0 <= value <= 1.0 for value in samples), samples

    # The cut-in has to be drawable without a renderer.
    import pygame
    pygame.init()
    surface = pygame.Surface((640, 640), pygame.SRCALPHA)
    for key in MOODS:
        jelly_cutin(pygame, surface, (320.0, 320.0), 200.0, mood_key=key,
                    face=face_at(key, 0.0, speaking="hello", elapsed=0.2,
                                 duration=0.8))
    blank = pygame.Surface((640, 640), pygame.SRCALPHA)
    jelly_cutin(pygame, blank, (320.0, 320.0), 200.0, alpha=0.0)
    assert not blank.get_bounding_rect().width, (
        "alpha=0 must draw nothing")
    tiny = pygame.Surface((640, 640), pygame.SRCALPHA)
    jelly_cutin(pygame, tiny, (320.0, 320.0), 4.0)
    assert not tiny.get_bounding_rect().width, "a tiny cut-in drew something"
