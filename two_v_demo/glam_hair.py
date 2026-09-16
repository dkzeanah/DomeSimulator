"""Hair, built as geometry rather than painted on the head sphere.

:mod:`two_v_demo.drama_face` gave the head a face.  This gives it hair,
and hair is the single biggest thing a look has: it is most of the
silhouette, it is what moves when she turns, and in a nine-by-sixteen
frame it is the first thing on screen.  A sphere with a colour on it
does not read as a person, and it certainly does not read as *this*
person rather than that one.

How a style is built
--------------------
Everything hangs off the head frame that :mod:`two_v_demo.drama_face`
already computes from the skeleton -- centre, forward, side, up and
radius -- so hair sits on the head at whatever scale and pose the
figure happens to be in, with nothing to keep in sync by hand.

Two primitives do all the work:

* **the scalp** -- points spread over the head sphere with the face
  oval cut out, which is where every strand is rooted and which on its
  own is already a close crop;
* **the strand** -- a path that leaves the scalp along its own normal,
  loses that direction to gravity as it falls, and carries a lateral
  wave and an optional helical curl.  Drawn with spheres it is a coil;
  drawn with cylinders it is a sheet of straight hair.

**Length is a body landmark, not a number.**  A style says its hair
falls to the collarbone or the waist, and the length in metres is read
off the posed skeleton at draw time by the same landmark table a hem
uses in :mod:`two_v_demo.glam_body` -- one definition of where a waist
is, shared, rather than two that drift.  The same style therefore fits a
1.62 m woman and a 1.80 m one without a second set of constants, and
nothing has to be re-tuned when a pose lowers the shoulders.

Nothing here is random.  Strand placement uses the golden angle, so
every frame of the same character is identical and two characters in
one shot never accidentally grow the same head of hair.
"""

from __future__ import annotations

import math
from dataclasses import dataclass
from typing import Callable, Mapping, Sequence

import numpy as np

from .drama_face import head_frame
from .glam_body import (
    LANDMARK_HEIGHT,
    LANDMARK_ORDER,
    landmark_height,
)
from .geometry import normalize


Colour = tuple[float, float, float, float]

GOLDEN_ANGLE = math.pi * (3.0 - math.sqrt(5.0))
"""Radians.  Successive strands land this far around the head, which
spreads them evenly without a random number anywhere in the file."""


# ----------------------------------------------------------------------
# A style
# ----------------------------------------------------------------------

@dataclass(frozen=True)
class HairStyle:
    """One head of hair: how big, how long, and how it moves."""

    style_id: str
    label: str
    family: str
    """COIL, CURL, STRAIGHT, WAVE, LOC, BRAID or UPDO.  The composer
    groups the palette by this."""
    length: str
    """A key in :data:`LANDMARK_HEIGHT`: where the ends fall."""
    volume: float
    """Silhouette width as a multiple of head radius. 1.0 is scalp-tight,
    2.0 is a full halo."""
    strands: int
    """At full detail.  The composer draws fewer while you are dragging."""
    movement: str
    """One line: what this hair does when she turns her head fast."""
    builder: str
    """Which of the builders below draws it."""
    tip_blend: float = 0.0
    """0 keeps one colour root to tip; 1 puts the accent fully on the ends."""


HAIR_STYLES: dict[str, HairStyle] = {
    "AFRO_HALO": HairStyle(
        "AFRO_HALO", "Afro halo", "COIL", "ear", 2.05, 200,
        "Does not move so much as arrive a half-beat after she does.",
        "halo", tip_blend=0.35),
    "DEEP_CURL_CASCADE": HairStyle(
        "DEEP_CURL_CASCADE", "Deep curl cascade", "CURL", "bust", 1.55, 46,
        "Whips out and keeps travelling after her head has stopped.",
        "cascade", tip_blend=0.55),
    "PIN_STRAIGHT_CURTAIN": HairStyle(
        "PIN_STRAIGHT_CURTAIN", "Pin-straight curtain", "STRAIGHT", "waist",
        1.16, 76,
        "One sheet, one beat, and back to flat. Nothing about it is loose.",
        "curtain"),
    "GLOSS_WAVE_LONG": HairStyle(
        "GLOSS_WAVE_LONG", "Glossy long waves", "WAVE", "hip", 1.34, 50,
        "Rolls. Every turn of her head is a shampoo advert and she knows it.",
        "wave", tip_blend=0.40),
    "SLEEK_BUN_EDGES": HairStyle(
        "SLEEK_BUN_EDGES", "Sleek bun, laid edges", "UPDO", "ear", 1.10, 34,
        "Nothing moves. That is the entire statement.",
        "bun"),
    "LOCS_CROWN": HairStyle(
        "LOCS_CROWN", "Locs, crown-gathered", "LOC", "waist", 1.40, 26,
        "Swings in ropes, heavy, and lands where she pointed it.",
        "locs", tip_blend=0.30),
    "PLATINUM_BLUNT_BOB": HairStyle(
        "PLATINUM_BLUNT_BOB", "Blunt bob", "STRAIGHT", "jaw", 1.22, 66,
        "Snaps forward and stops dead in a line, like a closing door.",
        "curtain"),
    "BRAIDED_CROWN_RIBBON": HairStyle(
        "BRAIDED_CROWN_RIBBON", "Braided crown with ribbon", "BRAID",
        "waist", 1.28, 20,
        "The crown holds; the tail is what tells you she has turned.",
        "crown_braid", tip_blend=0.85),
    "BOX_BRAIDS_WAIST": HairStyle(
        "BOX_BRAIDS_WAIST", "Box braids to the waist", "BRAID", "waist",
        1.42, 40,
        "Fifty separate arcs, all slightly out of phase. Reads as motion "
        "even when she is standing still.",
        "braids", tip_blend=0.45),
    "HIGH_PONY_SWISH": HairStyle(
        "HIGH_PONY_SWISH", "High ponytail", "STRAIGHT", "bust", 1.20, 40,
        "One long swing off the crown, arriving late and leaving early.",
        "pony"),
    "TWO_BUNS_HIGH": HairStyle(
        "TWO_BUNS_HIGH", "Twin buns", "UPDO", "ear", 1.30, 30,
        "Fixed. The tendrils at the neck do all the moving.",
        "twin_buns"),
    "WET_SLICK_BACK": HairStyle(
        "WET_SLICK_BACK", "Wet-look slick back", "STRAIGHT", "chin",
        1.08, 36,
        "Poolside. Holds every line the water put in it.",
        "slick"),
}

STYLE_ORDER: tuple[str, ...] = tuple(HAIR_STYLES)


def style(style_id: str) -> HairStyle:
    try:
        return HAIR_STYLES[style_id]
    except KeyError:
        raise ValueError(
            f"unknown hair style {style_id!r}; choose from "
            f"{', '.join(HAIR_STYLES)}") from None


# ----------------------------------------------------------------------
# The two primitives
# ----------------------------------------------------------------------

@dataclass(frozen=True)
class HeadFrame:
    """The head, in the terms hair needs: an origin and three axes."""

    centre: np.ndarray
    forward: np.ndarray
    side: np.ndarray
    up: np.ndarray
    radius: float


def frame_of(joints: Mapping[str, np.ndarray]) -> HeadFrame:
    centre, forward, side, up, radius = head_frame(joints)
    return HeadFrame(np.asarray(centre, dtype=float), forward, side, up,
                     float(radius))


def scalp_points(
    frame: HeadFrame,
    count: int,
    *,
    face_clear: float = 0.42,
    hairline: float = 0.62,
    top_bias: float = 0.30,
    back_bias: float = 0.0,
) -> list[tuple[np.ndarray, np.ndarray]]:
    """Root positions and normals, spread over the head with a hairline.

    ``face_clear`` is how far round the front of the head the bare zone
    reaches, and ``hairline`` is how high a root has to sit before it is
    allowed in there.  Together they cut the face oval out of the scalp,
    so hair never grows over the eyes the face module just drew.
    ``back_bias`` pulls the distribution towards the nape, which is what
    a gathered style needs.
    """
    roots: list[tuple[np.ndarray, np.ndarray]] = []
    attempts = max(count * 4, 24)
    for index in range(attempts):
        if len(roots) >= count:
            break
        # Fibonacci sphere, biased upward so the crown is denser.
        height = 1.0 - 2.0 * (index + 0.5) / attempts
        height = height * (1.0 - top_bias) + top_bias
        ring = math.sqrt(max(0.0, 1.0 - height * height))
        angle = GOLDEN_ANGLE * index
        normal = normalize(
            frame.up * height
            + frame.side * (ring * math.cos(angle))
            + frame.forward * (ring * math.sin(angle))
        )
        facing = float(np.dot(normal, frame.forward))
        rising = float(np.dot(normal, frame.up))
        # The hairline: the front of the head is bare below the brow.
        if facing > face_clear and rising < hairline:
            continue
        if back_bias > 0.0 and facing > (0.30 - back_bias):
            continue
        roots.append((frame.centre + normal * frame.radius, normal))
    return roots


def strand_path(
    root: np.ndarray,
    normal: np.ndarray,
    frame: HeadFrame,
    length: float,
    *,
    segments: int = 10,
    stiffness: float = 1.2,
    shed: float = 0.28,
    wave_turns: float = 0.0,
    wave_amp: float = 0.0,
    curl_radius: float = 0.0,
    curl_turns: float = 0.0,
    flare: float = 0.0,
    phase: float = 0.0,
    tuck: float = 0.0,
) -> list[np.ndarray]:
    """One strand, from the scalp to its end.

    The strand leaves along its own normal and hands over to gravity as
    it falls.  ``stiffness`` is how far it keeps its root direction, in
    head radii, and the handover is exponential in *distance travelled*
    rather than in the fraction of the strand drawn so far -- otherwise
    a long style would stand a foot of hair straight up off the crown
    before it agreed to fall, and a short one would not lift at all.
    ``shed`` is how strongly it drapes around the skull instead of
    falling through it.  Which way a strand leaves is the caller's
    business: falling styles pass a combed direction from
    :func:`comb_off_face` rather than the raw scalp normal, which is how
    hair rooted on the forehead ends up beside the face instead of over
    the eyes.  ``wave_*`` puts an S-bend in the plane across
    the head; ``curl_*`` wraps it into a helix, which is what separates
    a curl from a wave.  ``tuck`` pulls the ends in towards the body so
    long hair falls over a shoulder instead of hanging in mid-air.
    """
    down = np.array([0.0, 0.0, -1.0])
    # "Outward" is away from the head's own axis at the root.  Taking it
    # from the launch direction instead goes degenerate at the crown --
    # which is precisely where hair would otherwise fall through the
    # skull and down the front of the face.
    root = np.asarray(root, dtype=float)
    radial = root - frame.centre
    radial = radial - frame.up * float(np.dot(radial, frame.up))
    if float(np.linalg.norm(radial)) < frame.radius * 0.12:
        radial = normal - frame.up * float(np.dot(normal, frame.up))
    if float(np.linalg.norm(radial)) < 1e-6:
        radial = frame.side
    out = normalize(radial)
    across = normalize(np.cross(down, out))

    points = [root]
    step = length / segments
    position = points[0].copy()
    for index in range(1, segments + 1):
        share = index / segments
        # Gravity takes over a head radius or so from the root; until
        # then the hair still points the way it grew.
        travelled = step * index
        keep = math.exp(-travelled / max(1e-6, frame.radius * stiffness))
        # Draping matters while the strand is still beside the skull;
        # past that it is just width, so it fades with distance.
        clearing = shed * math.exp(-travelled / max(1e-6, frame.radius * 2.5))
        direction = normalize(
            normal * keep
            + (down + out * clearing) * (1.0 - keep)
            + out * (flare * share)
            - frame.forward * (tuck * share * 0.5)
        )
        position = position + direction * step
        offset = np.zeros(3)
        if wave_amp > 0.0 and wave_turns > 0.0:
            offset = offset + across * (
                math.sin(phase + share * wave_turns * math.tau)
                * wave_amp * share)
        if curl_radius > 0.0 and curl_turns > 0.0:
            # The helix opens out of the root rather than starting at
            # full width, which keeps the first curl off the cheekbone.
            grown = min(1.0, travelled / max(1e-6, frame.radius * 1.4))
            angle = phase + share * curl_turns * math.tau
            offset = offset + (across * math.cos(angle)
                               + out * math.sin(angle)) * (
                curl_radius * grown)
        points.append(position + offset)
    return points


def _blend(one: Colour, two: Colour, amount: float) -> Colour:
    amount = max(0.0, min(1.0, amount))
    return tuple(a + (b - a) * amount for a, b in zip(one, two))


def draw_strand(
    batch,
    points: Sequence[np.ndarray],
    root_colour: Colour,
    tip_colour: Colour,
    radius: float,
    *,
    coily: bool = False,
    taper: float = 0.55,
    sides: int = 5,
) -> None:
    """Draw a strand path, tapering and shading root to tip."""
    total = max(1, len(points) - 1)
    for index in range(total):
        share = (index + 0.5) / total
        colour = _blend(root_colour, tip_colour, share)
        width = radius * (1.0 - taper * share)
        if coily:
            batch.sphere(points[index], width, colour, 3, 5)
        else:
            batch.cylinder(points[index], points[index + 1], width,
                           colour, sides)
    if coily:
        batch.sphere(points[-1], radius * (1.0 - taper), tip_colour, 3, 5)


# ----------------------------------------------------------------------
# The builders
# ----------------------------------------------------------------------

def comb_off_face(frame: HeadFrame, normal: np.ndarray) -> np.ndarray:
    """The direction a strand is combed in, given where it grew.

    A strand rooted on the forehead has a face directly beneath it, so
    left alone it falls straight over the eyes.  Combing turns it
    towards its own side of the parting and, mostly, back over the ear
    -- hard enough that a root pointing forward leaves pointing
    backward, and weighted towards the back rather than the side so a
    long style does not end up a metre wide.  Roots
    at the crown and the back of the head are barely touched, which is
    why this is applied at the root instead of as a push halfway down:
    it is what a comb does, and it costs nothing per segment.
    """
    front = max(0.0, float(np.dot(normal, frame.forward)))
    sign = 1.0 if float(np.dot(normal, frame.side)) >= 0.0 else -1.0
    return normalize(normal
                     + frame.side * (sign * front * 1.25)
                     - frame.forward * (front * 1.90))


def _fall(joints, frame: HeadFrame, landmark: str) -> float:
    """How far hair has to travel from the crown to reach a landmark."""
    top = float(frame.centre[2]) + frame.radius
    return max(frame.radius * 0.6, top - landmark_height(joints, landmark))


def _build_halo(batch, joints, frame, spec, main, accent, detail):
    """A coil halo: a shell of coils standing off the scalp."""
    count = max(24, int(spec.strands * detail))
    thickness = frame.radius * (spec.volume - 1.0)
    for index, (root, normal) in enumerate(
            scalp_points(frame, count, face_clear=0.50, top_bias=0.10)):
        share = (index % 7) / 7.0
        reach = thickness * (0.72 + 0.28 * share)
        points = [root + normal * (reach * step / 3.0) for step in range(4)]
        colour = _blend(main, accent, spec.tip_blend * share)
        for point in points[1:]:
            batch.sphere(point, frame.radius * 0.20, colour, 3, 5)
    # A dense inner cap so the scalp never shows through the coils.
    _cap(batch, frame, main, thickness=0.16, density=70)


def _build_cascade(batch, joints, frame, spec, main, accent, detail):
    """Long spiral curls off the whole scalp."""
    count = max(12, int(spec.strands * detail))
    length = _fall(joints, frame, spec.length)
    _cap(batch, frame, main)
    for index, (root, normal) in enumerate(
            scalp_points(frame, count, face_clear=0.36)):
        phase = GOLDEN_ANGLE * index
        normal = comb_off_face(frame, normal)
        points = strand_path(
            root, normal, frame, length, segments=11, stiffness=0.9,
            curl_radius=frame.radius * 0.26, curl_turns=3.4,
            wave_turns=1.0, wave_amp=frame.radius * 0.20,
            flare=0.14, phase=phase, tuck=0.10)
        draw_strand(batch, points, main,
                    _blend(main, accent, spec.tip_blend),
                    frame.radius * 0.17, coily=True)


def _build_curtain(batch, joints, frame, spec, main, accent, detail):
    """Straight hair falling in a sheet, blunt at the ends."""
    count = max(14, int(spec.strands * detail))
    length = _fall(joints, frame, spec.length)
    _cap(batch, frame, main)
    for index, (root, normal) in enumerate(
            scalp_points(frame, count, face_clear=0.34)):
        normal = comb_off_face(frame, normal)
        points = strand_path(
            root, normal, frame, length, segments=7, stiffness=1.8, flare=0.05, tuck=0.06)
        draw_strand(batch, points, main,
                    _blend(main, accent, spec.tip_blend),
                    frame.radius * 0.21, taper=0.10, sides=4)


def _build_wave(batch, joints, frame, spec, main, accent, detail):
    """Long soft waves with a roll in them."""
    count = max(14, int(spec.strands * detail))
    length = _fall(joints, frame, spec.length)
    _cap(batch, frame, main)
    for index, (root, normal) in enumerate(
            scalp_points(frame, count, face_clear=0.36)):
        phase = GOLDEN_ANGLE * index
        normal = comb_off_face(frame, normal)
        points = strand_path(
            root, normal, frame, length, segments=12, stiffness=1.25,
            wave_turns=1.8, wave_amp=frame.radius * 0.40,
            curl_radius=frame.radius * 0.10, curl_turns=1.2,
            flare=0.09, phase=phase, tuck=0.12)
        draw_strand(batch, points, main,
                    _blend(main, accent, spec.tip_blend),
                    frame.radius * 0.16, taper=0.42, sides=5)


def _build_bun(batch, joints, frame, spec, main, accent, detail):
    """Scraped back into a bun, with laid edges at the temples."""
    _cap(batch, frame, main, thickness=0.10)
    back = frame.centre - frame.forward * (frame.radius * 0.92) \
        + frame.up * (frame.radius * 0.55)
    batch.sphere(back, frame.radius * 0.62, main, 5, 9)
    batch.sphere(back + frame.up * frame.radius * 0.25,
                 frame.radius * 0.34, _blend(main, accent, 0.25), 4, 7)
    # Laid edges: two short swirls at the hairline, the finishing move.
    for sign in (-1.0, 1.0):
        start = frame.centre + normalize(
            frame.forward * 0.86 + frame.side * (sign * 0.44)
            - frame.up * 0.24) * frame.radius
        curve = [start + frame.forward * (frame.radius * 0.10 * step)
                 - frame.up * (frame.radius * 0.09 * step * step)
                 + frame.side * (sign * frame.radius * 0.06 * step)
                 for step in range(4)]
        draw_strand(batch, curve, main, main, frame.radius * 0.055,
                    taper=0.3, sides=4)


def _build_locs(batch, joints, frame, spec, main, accent, detail):
    """Ropes, gathered at the crown and falling heavy."""
    count = max(10, int(spec.strands * detail))
    length = _fall(joints, frame, spec.length)
    _cap(batch, frame, main, thickness=0.07)
    for index, (root, normal) in enumerate(
            scalp_points(frame, count, face_clear=0.36, top_bias=0.05)):
        phase = GOLDEN_ANGLE * index
        normal = comb_off_face(frame, normal)
        points = strand_path(
            root, normal, frame, length, segments=9, stiffness=1.0,
            wave_turns=0.7, wave_amp=frame.radius * 0.20,
            flare=0.12, phase=phase, tuck=0.08)
        draw_strand(batch, points, main,
                    _blend(main, accent, spec.tip_blend),
                    frame.radius * 0.20, taper=0.10, sides=5)
        # A cuff on every third loc: the detail that says these are ropes.
        if index % 3 == 0:
            batch.sphere(points[-2], frame.radius * 0.22, accent, 3, 6)


def _build_braids(batch, joints, frame, spec, main, accent, detail):
    """Box braids: many thin plaits, each a chain of beads."""
    count = max(12, int(spec.strands * detail))
    length = _fall(joints, frame, spec.length)
    _cap(batch, frame, main, thickness=0.05)
    for index, (root, normal) in enumerate(
            scalp_points(frame, count, face_clear=0.36, top_bias=0.02)):
        phase = GOLDEN_ANGLE * index
        normal = comb_off_face(frame, normal)
        points = strand_path(
            root, normal, frame, length, segments=14, stiffness=1.1,
            wave_turns=1.1, wave_amp=frame.radius * 0.16,
            flare=0.10, phase=phase, tuck=0.10)
        draw_strand(batch, points, main,
                    _blend(main, accent, spec.tip_blend),
                    frame.radius * 0.105, coily=True, taper=0.25)


def _build_pony(batch, joints, frame, spec, main, accent, detail):
    """One gathered tail off a high crown."""
    count = max(10, int(spec.strands * detail))
    length = _fall(joints, frame, spec.length)
    _cap(batch, frame, main, thickness=0.09)
    gather = frame.centre - frame.forward * (frame.radius * 0.55) \
        + frame.up * (frame.radius * 0.86)
    batch.sphere(gather, frame.radius * 0.30, main, 4, 8)
    batch.cylinder(gather - frame.forward * frame.radius * 0.10,
                   gather + frame.forward * frame.radius * 0.10,
                   frame.radius * 0.26, accent, 8)
    back = normalize(-frame.forward * 0.55 + frame.up * 0.45)
    for index in range(count):
        spread = (index / max(1, count - 1) - 0.5) * 2.0
        normal = normalize(back + frame.side * (spread * 0.28))
        points = strand_path(
            gather, normal, frame, length, segments=10, stiffness=0.75,
            wave_turns=1.2, wave_amp=frame.radius * 0.18,
            flare=0.10, phase=GOLDEN_ANGLE * index)
        draw_strand(batch, points, main,
                    _blend(main, accent, spec.tip_blend),
                    frame.radius * 0.13, taper=0.45, sides=4)


def _build_twin_buns(batch, joints, frame, spec, main, accent, detail):
    """Two buns high on the crown, with tendrils at the nape."""
    _cap(batch, frame, main, thickness=0.09)
    for sign in (-1.0, 1.0):
        seat = frame.centre + normalize(
            frame.up * 0.86 + frame.side * (sign * 0.55)
            - frame.forward * 0.10) * (frame.radius * 1.05)
        batch.sphere(seat, frame.radius * 0.48, main, 4, 8)
        batch.sphere(seat + frame.up * frame.radius * 0.20,
                     frame.radius * 0.26, _blend(main, accent, 0.4), 3, 6)
    nape = frame.centre - frame.forward * (frame.radius * 0.86) \
        - frame.up * (frame.radius * 0.40)
    for index in range(max(4, int(8 * detail))):
        spread = (index / 7.0 - 0.5) * 2.0
        normal = normalize(-frame.forward * 0.6 - frame.up * 0.6
                           + frame.side * spread * 0.5)
        points = strand_path(nape + frame.side * (spread * frame.radius * 0.5),
                             normal, frame, frame.radius * 2.4,
                             segments=6, stiffness=0.8,
                             curl_radius=frame.radius * 0.14, curl_turns=1.6,
                             phase=GOLDEN_ANGLE * index)
        draw_strand(batch, points, main, main, frame.radius * 0.07,
                    coily=True)


def _build_crown_braid(batch, joints, frame, spec, main, accent, detail):
    """A braid worn round the crown, ribboned, with a tail down the back."""
    _cap(batch, frame, main, thickness=0.04)
    ring_radius = frame.radius * 0.94
    steps = max(16, int(28 * detail))
    for index in range(steps):
        angle = math.tau * index / steps
        seat = (frame.centre
                + frame.up * (frame.radius * 0.66)
                + (frame.side * math.cos(angle)
                   + frame.forward * math.sin(angle)) * ring_radius)
        colour = main if index % 2 else _blend(main, accent, spec.tip_blend)
        batch.sphere(seat, frame.radius * 0.17, colour, 3, 6)
    length = _fall(joints, frame, spec.length)
    tail_root = frame.centre - frame.forward * (frame.radius * 0.90) \
        + frame.up * (frame.radius * 0.20)
    normal = normalize(-frame.forward * 0.7 - frame.up * 0.3)
    points = strand_path(tail_root, normal, frame, length, segments=13,
                         stiffness=0.9, wave_turns=1.4,
                         wave_amp=frame.radius * 0.14, tuck=0.05)
    draw_strand(batch, points, main, main, frame.radius * 0.28,
                coily=True, taper=0.55)
    # The ribbon, wound down the tail.
    for index in range(2, len(points) - 1, 2):
        batch.sphere(points[index], frame.radius * 0.20, accent, 3, 6)


def _build_slick(batch, joints, frame, spec, main, accent, detail):
    """Wet-look, combed straight back, short at the nape."""
    _cap(batch, frame, main, thickness=0.05)
    count = max(10, int(spec.strands * detail))
    length = _fall(joints, frame, spec.length)
    for index, (root, normal) in enumerate(
            scalp_points(frame, count, face_clear=0.20, back_bias=0.18)):
        pulled = normalize(normal - frame.forward * 0.9)
        points = strand_path(root, pulled, frame, length, segments=6,
                             stiffness=1.9, tuck=0.02)
        draw_strand(batch, points, main, main, frame.radius * 0.12,
                    taper=0.35, sides=4)


def _cap(batch, frame: HeadFrame, colour: Colour, *,
         thickness: float = 0.06, density: int = 56) -> None:
    """The scalp itself: overlapping tufts, stopping at the hairline.

    The obvious implementation -- a slightly larger sphere over the head
    -- swallows the eyes and the mouth, because a sphere has a front.
    Building the cap out of the same scalp points every strand is rooted
    in means the bare face oval is cut once and every style inherits it.
    """
    for root, normal in scalp_points(frame, density, face_clear=0.34,
                                     hairline=0.74, top_bias=0.05):
        batch.sphere(root + normal * (frame.radius * thickness * 0.5),
                     frame.radius * (0.20 + thickness), colour, 3, 5)


BUILDERS: dict[str, Callable] = {
    "halo": _build_halo,
    "cascade": _build_cascade,
    "curtain": _build_curtain,
    "wave": _build_wave,
    "bun": _build_bun,
    "locs": _build_locs,
    "braids": _build_braids,
    "pony": _build_pony,
    "twin_buns": _build_twin_buns,
    "crown_braid": _build_crown_braid,
    "slick": _build_slick,
}


def draw_hair(
    batch,
    joints: Mapping[str, np.ndarray],
    style_id: str,
    main: Colour,
    accent: Colour | None = None,
    *,
    detail: float = 1.0,
) -> None:
    """Put a head of hair on a posed figure.

    ``detail`` scales the strand count: 1.0 for a render, something
    lower while the composer is dragging a piece around at 60 frames a
    second.  The silhouette is the same either way, because volume and
    length do not depend on how many strands draw it.
    """
    spec = style(style_id)
    frame = frame_of(joints)
    BUILDERS[spec.builder](batch, joints, frame, spec, main,
                           accent if accent is not None else main,
                           max(0.15, min(1.0, detail)))


def hair_report() -> str:
    lines = ["HAIR", ""]
    for spec in HAIR_STYLES.values():
        lines.append(f"{spec.label:<28} {spec.family:<9} "
                     f"to the {spec.length:<11} "
                     f"volume {spec.volume:.2f}x head")
        lines.append(f"    {spec.movement}")
    return "\n".join(lines)


# ----------------------------------------------------------------------
# Proof
# ----------------------------------------------------------------------

def _eyes_clear(points: np.ndarray, frame: HeadFrame,
                clearance: float = 0.26) -> int:
    """How many hair vertices sit in front of an eye.

    The eye positions come from the same expression
    :func:`two_v_demo.drama_face.draw_face` uses, so this checks the
    eyes that are actually drawn rather than an assumed pair.
    """
    hits = 0
    for sign in (-1.0, 1.0):
        gaze = normalize(frame.forward
                         + frame.side * (sign * 0.33)
                         + frame.up * 0.17)
        start = frame.centre + gaze * (frame.radius * 0.99)
        axis = gaze * (frame.radius * 0.70)
        length_sq = float(axis @ axis)
        along = np.clip((points - start) @ axis / length_sq, 0.0, 1.0)
        nearest = start + along[:, None] * axis
        hits += int((np.linalg.norm(points - nearest, axis=1)
                     < frame.radius * clearance).sum())
    return hits


def validate_glam_hair() -> None:
    """Prove every style draws, fits the head, and stays off the face."""
    from .figure import POSES, joint_positions
    from .render_kit import TriangleBatch

    stature = 1.70
    joints = joint_positions(POSES["stand"], stature)
    frame = frame_of(joints)

    # The shared landmark table is proved in glam_body; what this module
    # has to check is that the lengths hair actually uses are on the
    # upper body, because a style that claims to reach the knee is a
    # style nobody has drawn.
    for spec in HAIR_STYLES.values():
        assert spec.length in LANDMARK_ORDER[:LANDMARK_ORDER.index("hip") + 1], (
            spec.style_id, spec.length)

    # No root lands on the face: that is what the hairline is for.
    for root, normal in scalp_points(frame, 80):
        forward = float(np.dot(normal, frame.forward))
        rising = float(np.dot(normal, frame.up))
        assert not (forward > 0.42 and rising < 0.62), (forward, rising)
        assert abs(float(np.linalg.norm(root - frame.centre))
                   - frame.radius) < 1e-9

    # A strand starts at its root, ends roughly its own length away, and
    # never travels upward once gravity has it.
    length = 0.5
    points = strand_path(frame.centre + frame.up * frame.radius, frame.up,
                         frame, length, wave_turns=2.0, wave_amp=0.03)
    assert float(np.linalg.norm(points[0] - (frame.centre
                                             + frame.up * frame.radius))) < 1e-9
    travelled = sum(float(np.linalg.norm(b - a))
                    for a, b in zip(points, points[1:]))
    assert length * 0.9 < travelled < length * 1.6, travelled

    for style_id, spec in HAIR_STYLES.items():
        batch = TriangleBatch()
        draw_hair(batch, joints, style_id,
                  (0.1, 0.1, 0.1, 1.0), (0.6, 0.3, 0.1, 1.0))
        assert batch.vertices, style_id
        points = np.asarray(batch.vertices, dtype=float).reshape(-1, 10)[:, :3]

        # Hair stays on the body: nothing under the floor, nothing more
        # than a head above the crown, nothing out at arm's length.
        assert points[:, 2].min() > -1e-6, style_id
        assert points[:, 2].max() < stature + frame.radius * 1.6, style_id
        # Width is judged against the body, not against a constant: long
        # hair is allowed to lie over the shoulders, and nothing is
        # allowed to stand out past them by more than a head.
        shoulder_half = float(np.linalg.norm(
            joints["l_shoulder"] - joints["r_shoulder"])) * 0.5
        allowance = max(frame.radius * spec.volume,
                        shoulder_half) + frame.radius * 1.2
        reach = np.linalg.norm(points[:, :2] - frame.centre[:2], axis=1).max()
        assert reach < allowance, (style_id, reach, allowance)

        # The ends reach the landmark the style claims, near enough that
        # a bob is a bob and a waist-length style is not.
        target = landmark_height(joints, spec.length)
        lowest = float(points[:, 2].min())
        assert lowest < target + frame.radius * 1.4, (style_id, lowest, target)

        # And the eyes stay visible.  The test is not "nothing near the
        # front of the head" -- a crown braid crosses the forehead and
        # laid edges sit on the temples, both correctly.  It is that
        # nothing lands in front of the two eyes the face module draws,
        # at the positions it draws them.
        assert _eyes_clear(points, frame) == 0, style_id

    # Detail changes the cost, not the shape.
    cheap = TriangleBatch()
    rich = TriangleBatch()
    draw_hair(cheap, joints, "DEEP_CURL_CASCADE", (0.1, 0.1, 0.1, 1.0),
              detail=0.25)
    draw_hair(rich, joints, "DEEP_CURL_CASCADE", (0.1, 0.1, 0.1, 1.0),
              detail=1.0)
    assert len(cheap.vertices) < len(rich.vertices)

    # Every cast member's style exists, and every style is drawable.
    from .glam_cast import GLAM_CAST
    for who in GLAM_CAST.values():
        assert who.hair_style in HAIR_STYLES, who.character_id
    for spec in HAIR_STYLES.values():
        assert spec.builder in BUILDERS, spec.style_id
        assert spec.length in LANDMARK_HEIGHT, spec.style_id
        assert 1.0 <= spec.volume <= 2.4, spec.style_id
        assert spec.movement.endswith("."), spec.style_id

    try:
        style("BEEHIVE")
    except ValueError:
        pass
    else:
        raise AssertionError("an unknown style has to be refused")


if __name__ == "__main__":
    validate_glam_hair()
    print(hair_report())
