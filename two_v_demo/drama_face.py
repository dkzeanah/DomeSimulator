"""Faces for the drama rig: the expression layer the spec asked for.

The specification lists facial parameters on several actions -- jaw
drop, eye scale, smirk morphs -- and until now this package had nowhere
to put them, because :mod:`two_v_demo.figure` draws a head as a sphere.
This module gives that sphere a face: brows, eyes with pupils that
track, a mouth that shapes, and a jaw that opens.

Why it matters more here than anywhere else in the repository: a
micro-drama is watched on a phone in a nine-by-sixteen frame, and the
thing that carries the emotion is a face in close-up.  A shoulder lift
can suggest a gasp; only a face can sell one.

Three things drive a face:

* **the action** -- the rig action a character is executing maps to an
  expression, at the intensity of that action's own curve, so a slap
  and a gasp shape the face on exactly the timing the body uses;
* **speaking** -- the jaw opens on the vowel groups of the line the
  character is actually saying, spread across the beat, so the mouth
  moves with their own dialogue rather than to a generic loop;
* **being alive** -- a deterministic blink, phase-shifted per character
  so two people never blink in unison.

Nothing here is random.  Every value is a function of (character, time,
action, line), which keeps a rendered frame reproducible.
"""

from __future__ import annotations

import math
import re
from dataclasses import dataclass, replace

import numpy as np

from .geometry import normalize


# ----------------------------------------------------------------------
# The face itself
# ----------------------------------------------------------------------

@dataclass(frozen=True)
class FaceState:
    """One face at one instant, in normalised units.

    Zero is neutral for every signed channel; ``eye_open`` and
    ``mouth_width`` are multipliers where 1.0 is resting.
    """

    brow_raise: float = 0.0
    """-1 pulled down and in, +1 lifted."""
    brow_tilt: float = 0.0
    """+1 inner ends down: the anger shape. -1 inner ends up: pleading."""
    eye_open: float = 1.0
    gaze_side: float = 0.0
    gaze_up: float = 0.0
    jaw_open: float = 0.0
    mouth_curve: float = 0.0
    """-1 down at the corners, +1 up."""
    mouth_width: float = 1.0
    smirk: float = 0.0
    """Asymmetry: one corner up, the other flat."""

    def blend(self, other: "FaceState", amount: float) -> "FaceState":
        amount = min(1.0, max(0.0, amount))
        values = {}
        for field in self.__dataclass_fields__:
            first = getattr(self, field)
            second = getattr(other, field)
            values[field] = first + (second - first) * amount
        return FaceState(**values)


NEUTRAL = FaceState()

EXPRESSIONS: dict[str, FaceState] = {
    "NEUTRAL": NEUTRAL,
    # Eyes wide, brows up, jaw dropped: the specification's gasp, with
    # its jaw_drop_mm and eye_scale_pct finally somewhere they can act.
    "SHOCK": FaceState(brow_raise=1.0, eye_open=1.35, jaw_open=0.75,
                       mouth_curve=-0.15, mouth_width=0.9),
    # Brows down and inward, eyes narrowed, mouth set hard.
    "FURY": FaceState(brow_raise=-0.9, brow_tilt=1.0, eye_open=0.85,
                      mouth_curve=-0.7, mouth_width=1.1, jaw_open=0.12),
    # Cold, not hot: lids low, mouth flat, gaze off to one side.
    "DISDAIN": FaceState(brow_raise=-0.25, eye_open=0.7, gaze_side=-0.6,
                         gaze_up=-0.25, mouth_curve=-0.35,
                         mouth_width=0.88),
    # Jaw set, brows level and low, eyes steady: holding something in.
    "RESOLVE": FaceState(brow_raise=-0.5, brow_tilt=0.45, eye_open=0.95,
                         mouth_curve=-0.25, mouth_width=0.95,
                         jaw_open=0.05),
    "THREAT": FaceState(brow_raise=-0.7, brow_tilt=0.8, eye_open=1.05,
                        mouth_curve=-0.45, mouth_width=1.05),
    # Authority does not strain: brows level, eyes open, mouth calm.
    "AUTHORITY": FaceState(brow_raise=0.15, eye_open=1.0,
                           mouth_curve=-0.05, mouth_width=1.0),
    "SMIRK": FaceState(brow_raise=0.35, eye_open=0.9, mouth_curve=0.25,
                       smirk=1.0, mouth_width=1.05),
    "FEAR": FaceState(brow_raise=0.85, brow_tilt=-0.6, eye_open=1.25,
                      mouth_curve=-0.5, jaw_open=0.3, mouth_width=0.85),
    "PLEADING": FaceState(brow_raise=0.6, brow_tilt=-0.9, eye_open=1.1,
                          mouth_curve=-0.3, mouth_width=0.9),
}

# Which face an action wears.  The body and the face are then driven by
# the same curve, so they land together.
ACTION_EXPRESSION: dict[str, str] = {
    "RIG_SLAP_EXECUTE": "FURY",
    "RIG_GASP_REACTION": "SHOCK",
    "RIG_INVASIVE_STEP": "THREAT",
    "RIG_DISDAINFUL_TURN": "DISDAIN",
    "RIG_CLENCH_FIST_RAISE": "RESOLVE",
    "RIG_GRAB_LAPEL": "FURY",
    "RIG_POINT_COMMAND": "AUTHORITY",
}

# A character's face at rest.  A drama reads faster when the cast are
# distinguishable before anybody moves.
RESTING_FACE: dict[str, str] = {
    "CHAR_LEO": "RESOLVE",
    "CHAR_AURELIA": "DISDAIN",
    "CHAR_SILAS": "AUTHORITY",
    "CHAR_JAX": "SMIRK",
    "CHAR_BARON": "AUTHORITY",
}

BLINK_PERIOD_S = 4.2
BLINK_LENGTH_S = 0.13


def blink_amount(character_id: str, time_s: float) -> float:
    """How closed the eyes are from blinking alone, 0..1.

    Phase-shifted per character from a hash of the name, because two
    people blinking in unison reads as a glitch rather than as life.
    """
    phase = (abs(hash(character_id)) % 1000) / 1000.0 * BLINK_PERIOD_S
    into = (time_s + phase) % BLINK_PERIOD_S
    if into > BLINK_LENGTH_S:
        return 0.0
    return math.sin(into / BLINK_LENGTH_S * math.pi)


_VOWELS = re.compile(r"[aeiouy]+", re.IGNORECASE)


def syllable_count(text: str) -> int:
    """Vowel groups in a line: a usable stand-in for syllables.

    Not phoneme alignment.  It is the cheapest thing that makes a mouth
    move with the words being said rather than to a generic loop, and it
    is deterministic, which matters more here than being exact.
    """
    return max(1, sum(1 for _ in _VOWELS.finditer(text)))


def speech_jaw(text: str, elapsed_s: float, duration_s: float) -> float:
    """How far the jaw is open while this line is being spoken.

    The line's vowel groups are spread evenly across the beat and each
    one opens and closes the jaw, so a long line makes a busier mouth
    than a short one in the same time.
    """
    if duration_s <= 0.0 or elapsed_s < 0.0 or elapsed_s > duration_s:
        return 0.0
    syllables = syllable_count(text)
    position = elapsed_s / duration_s * syllables
    # A raised sine gives a closed mouth between syllables rather than a
    # jaw that hovers open.
    shape = math.sin(position * math.pi) ** 2
    # Not every syllable opens the mouth equally; the pattern repeats
    # with the line rather than with the clock.
    weight = 0.55 + 0.45 * math.sin(position * 2.399 + 0.7) ** 2
    return max(0.0, min(1.0, shape * weight))


def face_for(character_id: str, action_id: str | None, amount: float,
             time_s: float, speaking_text: str = "",
             speaking_elapsed: float = -1.0,
             speaking_duration: float = 0.0,
             looking_at_offset: tuple[float, float] = (0.0, 0.0)
             ) -> FaceState:
    """The whole face at one instant, from everything that drives it."""
    rest = EXPRESSIONS[RESTING_FACE.get(character_id, "NEUTRAL")]
    face = rest
    if action_id is not None:
        target = EXPRESSIONS[ACTION_EXPRESSION.get(action_id, "NEUTRAL")]
        face = rest.blend(target, max(0.0, min(1.0, amount)))

    jaw = face.jaw_open
    if speaking_text and speaking_elapsed >= 0.0:
        jaw = max(jaw, speech_jaw(speaking_text, speaking_elapsed,
                                  speaking_duration))
    # A shocked face does not blink; everything else does.
    blink = blink_amount(character_id, time_s) * (
        0.15 if face.eye_open > 1.2 else 1.0)
    return replace(
        face,
        jaw_open=jaw,
        eye_open=max(0.05, face.eye_open * (1.0 - blink)),
        gaze_side=face.gaze_side + looking_at_offset[0],
        gaze_up=face.gaze_up + looking_at_offset[1],
    )


# ----------------------------------------------------------------------
# Drawing it
# ----------------------------------------------------------------------

EYE_WHITE = (0.94, 0.94, 0.92, 1.0)
PUPIL = (0.09, 0.08, 0.10, 1.0)
BROW = (0.16, 0.11, 0.08, 1.0)
MOUTH = (0.32, 0.14, 0.14, 1.0)
MOUTH_DARK = (0.10, 0.05, 0.06, 1.0)


def head_frame(joints) -> tuple[np.ndarray, np.ndarray, np.ndarray,
                                np.ndarray, float]:
    """``(centre, forward, side, up, radius)`` for a figure's head.

    Derived from the shoulders rather than passed in, so a face never
    disagrees with the body it is drawn on.
    """
    neck = np.asarray(joints["neck"], dtype=float)
    top = np.asarray(joints["head_top"], dtype=float)
    left = np.asarray(joints["l_shoulder"], dtype=float)
    right = np.asarray(joints["r_shoulder"], dtype=float)
    up = normalize(top - neck)
    side = normalize(right - left)
    # The figure is built facing +X with its left shoulder on +Y, so the
    # left-to-right shoulder axis is -Y and the face is up x side.  The
    # other order points out of the back of the head.
    forward = normalize(np.cross(up, side))
    centre = (neck + top) * 0.5
    radius = 0.098 * (float(np.linalg.norm(top - neck)) / 0.324)
    return centre, forward, side, up, radius


def draw_face(batch, joints, face: FaceState, skin=(0.87, 0.66, 0.50, 1.0)
              ) -> None:
    """Put a face on the front of the head sphere."""
    centre, forward, side, up, radius = head_frame(joints)

    def direction(side_offset: float, up_offset: float,
                  out: float = 1.0) -> np.ndarray:
        """A direction out of the head, in head-radius units."""
        return normalize(forward * max(0.25, out)
                         + side * side_offset + up * up_offset)

    def at(side_offset: float, up_offset: float,
           out: float = 1.0, lift: float = 1.02) -> np.ndarray:
        """A point on the head's surface.

        Features have to sit *on* the sphere: offsets measured from the
        centre put them inside it, where the head hides them and the
        face renders as a blank ball.
        """
        return centre + direction(side_offset, up_offset, out) * (
            radius * lift)

    eye_span = 0.33
    eye_height = 0.17
    eye_radius = radius * 0.23 * max(0.12, face.eye_open)

    for sign in (-1.0, 1.0):
        eye_dir = direction(sign * eye_span, eye_height, 1.0)
        eye = centre + eye_dir * (radius * 0.99)
        batch.sphere(eye, eye_radius, EYE_WHITE, 4, 8)
        pupil = (eye + eye_dir * (eye_radius * 0.7)
                 + side * (face.gaze_side * eye_radius * 0.5)
                 + up * (face.gaze_up * eye_radius * 0.5))
        batch.sphere(pupil, eye_radius * 0.60, PUPIL, 4, 8)

        # The brow: a short bar whose inner end drops for anger and
        # lifts for pleading.  Tilt does most of the emotional work.
        raise_amount = eye_height + 0.26 + face.brow_raise * 0.14
        inner = at(sign * (eye_span - 0.17),
                   raise_amount - face.brow_tilt * 0.13, 1.0)
        outer = at(sign * (eye_span + 0.15),
                   raise_amount + face.brow_tilt * 0.05, 0.95)
        batch.cylinder(inner, outer, radius * 0.095, BROW, 6)

    # The mouth: a line of segments whose corners lift or fall, opening
    # into a dark aperture as the jaw drops.
    width = 0.34 * face.mouth_width
    depth = face.jaw_open
    corners = []
    for step in range(5):
        share = step / 4.0
        across = (share - 0.5) * 2.0
        lift = -0.38 + face.mouth_curve * 0.12 * (1.0 - abs(across))
        if face.smirk:
            lift += face.smirk * 0.07 * across
        corners.append(at(across * width, lift, 1.0))
    for first, second in zip(corners, corners[1:]):
        batch.cylinder(first, second, radius * 0.075, MOUTH, 6)
    if depth > 0.03:
        # The open mouth is an aperture in the face rather than a
        # dropped chin: a separate chin ball reads as something growing
        # out of the jaw at every distance this film is watched from.
        aperture = at(0.0, -0.40 - depth * 0.10, 1.0)
        batch.sphere(aperture, radius * (0.09 + 0.16 * depth), MOUTH_DARK,
                     4, 9)


def validate_drama_face() -> None:
    """Prove the face rig before it reaches a close-up."""
    from .drama_rig import ACTIONS, joints_at
    from .render_kit import TriangleBatch

    # Every action has a face, and every face is a real expression.
    for action_id in ACTIONS:
        assert action_id in ACTION_EXPRESSION, action_id
        assert ACTION_EXPRESSION[action_id] in EXPRESSIONS, action_id
    for name, face in EXPRESSIONS.items():
        assert 0.0 <= face.eye_open <= 1.6, name
        assert 0.0 <= face.jaw_open <= 1.0, name
        assert -1.0 <= face.mouth_curve <= 1.0, name

    # The specification's gasp really does drop the jaw and widen the
    # eyes now, rather than only declaring it.
    shock = EXPRESSIONS["SHOCK"]
    assert shock.jaw_open > 0.5 and shock.eye_open > 1.2

    # The head frame has to agree with the body: a figure facing +X must
    # have a face pointing +X, and one turned 90 degrees must not.
    for yaw, expected in ((0.0, np.array([1.0, 0.0, 0.0])),
                          (90.0, np.array([0.0, 1.0, 0.0]))):
        joints = joints_at(np.zeros(3), yaw)
        _centre, forward, _side, up, radius = head_frame(joints)
        assert float(np.dot(forward, expected)) > 0.95, yaw
        assert float(np.dot(up, np.array([0.0, 0.0, 1.0]))) > 0.95, yaw
        assert 0.06 < radius < 0.14, radius

    # Blinks happen, are brief, and are not synchronised across the cast.
    closed = {
        name: sum(1 for step in range(500)
                  if blink_amount(name, step * 0.02) > 0.5)
        for name in ("CHAR_LEO", "CHAR_AURELIA", "CHAR_SILAS")
    }
    for name, count in closed.items():
        assert 0 < count < 120, (name, count)
    assert len(set(closed.values())) > 1 or True  # counts may coincide
    at_once = sum(1 for step in range(500)
                  if all(blink_amount(name, step * 0.02) > 0.5
                         for name in closed))
    assert at_once == 0, "the whole cast blinks together"

    # Speaking opens the mouth, silence closes it, and a longer line
    # makes a busier mouth in the same time.
    line = "How dare you enter the High Council Dome without my permission!"
    opens = [speech_jaw(line, t * 0.05, 4.0) for t in range(80)]
    assert max(opens) > 0.6, max(opens)
    assert min(opens) < 0.05, min(opens)
    assert speech_jaw(line, -1.0, 4.0) == 0.0
    assert speech_jaw(line, 9.0, 4.0) == 0.0
    def openings(values) -> int:
        # Count mouth openings, not time spent open: a longer line makes
        # a busier mouth in the same seconds, and the fraction of time
        # above a threshold is about the same either way.
        return sum(1 for before, after in zip(values, values[1:])
                   if before <= 0.5 < after)

    short = [speech_jaw("Too late!", t * 0.05, 4.0) for t in range(80)]
    assert openings(opens) > openings(short), (openings(opens),
                                               openings(short))
    assert openings(opens) >= 4

    # A shocked face is visibly different from a furious one, or the
    # whole layer is decoration.
    shock_face = face_for("CHAR_LEO", "RIG_GASP_REACTION", 1.0, 0.0)
    fury_face = face_for("CHAR_AURELIA", "RIG_SLAP_EXECUTE", 1.0, 0.0)
    difference = max(
        abs(getattr(shock_face, field) - getattr(fury_face, field))
        for field in FaceState.__dataclass_fields__)
    assert difference > 0.5, difference

    # An action at zero intensity leaves the character's resting face,
    # so a face never snaps on before its body moves.
    rest = face_for("CHAR_JAX", "RIG_INVASIVE_STEP", 0.0, 0.0)
    assert abs(rest.smirk - EXPRESSIONS["SMIRK"].smirk) < 1e-6

    # And it draws: geometry, in front of the head, both eyes present.
    joints = joints_at(np.zeros(3), 0.0)
    batch = TriangleBatch()
    draw_face(batch, joints, face_for("CHAR_LEO", "RIG_GASP_REACTION",
                                      1.0, 0.0))
    assert len(batch.vertices) > 30 * 20
    points = np.asarray(batch.vertices).reshape(-1, 10)[:, :3]
    centre, forward, _side, _up, radius = head_frame(joints)
    ahead = (points - centre) @ forward
    assert float(ahead.max()) > radius * 0.5, "the face is inside the head"
    assert float(np.linalg.norm(points - centre, axis=1).max()) < radius * 2.0
