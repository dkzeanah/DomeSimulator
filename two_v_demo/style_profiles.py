"""One script, several registers: how a cut behaves rather than what it says.

A film here has always had exactly one look. ``Lesson.style`` chooses a *chrome*
-- cards, or one big headline, or nothing -- and that is the whole vocabulary. So
the same script can only ever come out one way, which is a problem the moment
you want a considered presentation cut and a snarky vertical one from the same
research.

A profile is that missing axis, kept as **data** rather than as more chrome
branches. It carries how the camera behaves, how fast the film moves, how much
of the character it uses, and what is laid over the finished frame. Two films
that share a chapter tuple and differ only in profile are recognisably two cuts
without a single number between them changing.

**Empty means unchanged.** :data:`DEFAULT` is deliberately the behaviour every
shipped film already has -- the house camera, the house pace, no treatment and
no character -- so ``profile=""`` (the default on :class:`~two_v_demo.lessons.Lesson`)
reproduces every existing film frame for frame. That is the same promise the
trailing fields on ``Chapter`` make, and it is the reason this is a table of
values rather than a rewrite of the renderer.
"""

from __future__ import annotations

import math
from dataclasses import dataclass

import numpy as np

from .render_kit import clamp


@dataclass(frozen=True)
class StyleProfile:
    """How one cut behaves."""

    key: str
    label: str
    note: str

    accent: tuple[int, int, int] = (255, 177, 62)
    """The chrome's accent, where a chrome reads one. The default is the house
    amber that every existing hype film already draws with."""
    headline_scale: float = 1.0
    """Multiplier on the headline's type size."""

    pace: float = 1.0
    """Multiplier on the authored chapter durations. Below 1.0 is faster.

    Only a floor: the audio stage still stretches a chapter that cannot say its
    lines in the time this leaves. A cut cannot get faster than its own speech.
    """
    motion: str = "lockoff"
    """``lockoff`` is the house orbit. ``drift`` pushes in slowly across a
    chapter. ``handheld`` adds a small unsteady wobble."""
    lean_in: float = 0.0
    """How far the camera closes on the subject while the character is
    speaking, as a fraction of the shot's distance. 0 disables it."""
    mascot: str = "none"
    """``none``, ``rare`` or ``present``. Decides whether a chapter's mascot
    cues are drawn at all -- the cues themselves live on the chapter, so one
    script can be cut with the character and without."""
    treatment: str = "clean"
    """``clean``, or ``vignette`` for the rough-edged register."""


DEFAULT = StyleProfile(
    "default", "As shipped", "The house look: the house camera, no treatment, "
    "no character. Every film made before profiles existed behaves like this.")

PROFILES: dict[str, StyleProfile] = {
    "": DEFAULT,
    "polished": StyleProfile(
        "polished", "Polished",
        "A considered presentation: locked-off camera that drifts in slowly, "
        "generous pace, no character butting in, nothing laid over the frame.",
        accent=(255, 177, 62), headline_scale=1.0, pace=1.06,
        motion="drift", lean_in=0.0, mascot="none", treatment="clean"),
    "snarky": StyleProfile(
        "snarky", "Snappy / snarky",
        "The social cut: handheld, leans in when the character speaks, a "
        "little faster, vignetted at the edges, and the pink jelly all "
        "through it.",
        accent=(255, 92, 184), headline_scale=1.14, pace=0.93,
        motion="handheld", lean_in=0.10, mascot="present",
        treatment="vignette"),
}

PROFILE_KEYS: tuple[str, ...] = tuple(PROFILES)


def profile_for(key: str | None) -> StyleProfile:
    """One profile by name, with the list of them in the error rather than a KeyError."""
    if not key:
        return DEFAULT
    try:
        return PROFILES[key]
    except KeyError:
        raise KeyError(
            f"no style profile {key!r}; choose from "
            f"{', '.join(k for k in PROFILE_KEYS if k)}") from None


# ----------------------------------------------------------------------
# The camera
# ----------------------------------------------------------------------

FOV_DEGREES = 48.0
"""The house field of view. A literal, and it stays one: films were composed
against it and a profile changes where the camera stands, never the lens."""

ORBIT_SWING_DEGREES = 7.0
"""The slow yaw sweep the renderer already applies across a chapter."""


def orbit(app, progress: float) -> tuple[np.ndarray, float]:
    """The house camera's eye and distance, exactly as the renderer builds them.

    Reproduced rather than imported because ``Lesson.camera_fn`` *replaces* the
    renderer's camera: a profile camera that computed its eye a slightly
    different way would move every shot the profile was applied to, which is a
    re-composition rather than a restyle.
    """
    yaw = app.camera_yaw
    if not getattr(app, "camera_override", False) and (
            getattr(app, "playing", False) or getattr(app, "exporting", False)):
        yaw += math.sin(progress * math.pi) * ORBIT_SWING_DEGREES
    pitch = math.radians(clamp(app.camera_pitch, 8.0, 78.0))
    distance = app.camera_distance
    target = np.array([0.0, 0.0, 2.25], dtype=np.float64)
    eye = target + np.array([
        distance * math.cos(pitch) * math.cos(math.radians(yaw)),
        distance * math.cos(pitch) * math.sin(math.radians(yaw)),
        distance * math.sin(pitch),
    ])
    return eye, float(np.linalg.norm(eye - target))


def shake(time_s: float, amount: float) -> tuple[float, float, float]:
    """A small unsteady offset, in metres and degrees.

    Three sines at frequencies that do not divide into one another, so the
    motion takes a long time to repeat and does not read as a loop. Sampled
    from the film's own clock rather than a frame counter, which is what keeps
    a re-render identical.
    """
    if amount <= 0.0:
        return 0.0, 0.0, 0.0
    return tuple(component * amount for component in (
        math.sin(time_s * 0.73) * 0.55 + math.sin(time_s * 1.87 + 1.1) * 0.30,
        math.sin(time_s * 1.31 + 2.3) * 0.42 + math.sin(time_s * 2.71 + 0.4) * 0.22,
        math.sin(time_s * 0.41 + 3.7) * 0.35 + math.sin(time_s * 1.03 + 0.9) * 0.18,
    ))


def camera_fn(profile: StyleProfile):
    """A :attr:`two_v_demo.lessons.Lesson.camera_fn` for this profile.

    Returns ``None`` for a lock-off profile, so the lesson keeps the renderer's
    own camera instead of a re-implementation of it -- the fewer films that
    route through this function, the fewer chances for the two cameras to
    drift apart.
    """
    if profile.motion == "lockoff" and profile.lean_in <= 0.0:
        return None

    def camera(app, chapter, progress, width, height):
        from . import mascot

        eye, distance = orbit(app, progress)
        time_s = float(getattr(app, "timeline", 0.0))
        # A slow push across the chapter. Never enough to re-compose the shot:
        # the subject stays where the framing put it.
        if profile.motion == "drift":
            distance *= 1.0 - 0.07 * progress
        elif profile.motion == "handheld":
            distance *= 1.0 - 0.05 * progress
            offset = shake(time_s, 0.012)
            eye = eye + np.array(offset)
        # Lean in when the character speaks. This is the one camera move that
        # is about the script rather than the shot, so it is driven by the
        # character's own cue and not by a stopwatch.
        if profile.lean_in > 0.0:
            distance *= 1.0 - profile.lean_in * mascot.active_alpha(app)
        direction = eye - np.array([0.0, 0.0, 2.25])
        length = float(np.linalg.norm(direction))
        if length > 1e-6:
            eye = np.array([0.0, 0.0, 2.25]) + direction * (distance / length)
        return eye, np.array([0.0, 0.0, 2.25]), FOV_DEGREES

    return camera


# ----------------------------------------------------------------------
# What is laid over the finished frame
# ----------------------------------------------------------------------

VIGNETTE_DEPTH = 150
"""How dark the corners get, out of 255. Enough to feel like a lens, not enough
to hide the picture -- a worksheet that cannot be read is a worse film."""


def apply_treatment(app, surface, width: int, height: int) -> None:
    """Grade the finished overlay, for the profiles that ask for it.

    Drawn onto the overlay surface rather than the GL frame, so it costs
    nothing when no profile asks for it and cannot touch a film that predates
    profiles.
    """
    profile = getattr(app, "profile", DEFAULT)
    if profile.treatment != "vignette" or width < 32 or height < 32:
        return
    pg = app.pygame
    band = int(min(width, height) * 0.34)
    # Four gradient strips, one per edge, blitted and flipped into place. A
    # radial falloff would be prettier and would also be a per-pixel loop over
    # two million pixels thirty times a second.
    strip = pg.Surface((band, height), pg.SRCALPHA)
    for column in range(band):
        share = 1.0 - column / band
        alpha = int(VIGNETTE_DEPTH * share * share)
        pg.draw.line(strip, (4, 6, 14, alpha), (column, 0), (column, height))
    surface.blit(strip, (0, 0))
    surface.blit(pg.transform.flip(strip, True, False), (width - band, 0))
    top = pg.Surface((width, band), pg.SRCALPHA)
    for row in range(band):
        share = 1.0 - row / band
        alpha = int(VIGNETTE_DEPTH * share * share)
        pg.draw.line(top, (4, 6, 14, alpha), (0, row), (width, row))
    surface.blit(top, (0, 0))
    surface.blit(pg.transform.flip(top, False, True), (0, height - band))


# ----------------------------------------------------------------------
# Proof
# ----------------------------------------------------------------------

def validate_style_profiles() -> None:
    """Every profile has to be usable and the default has to be a no-op."""
    assert PROFILES[""] is DEFAULT
    assert DEFAULT.pace == 1.0 and DEFAULT.motion == "lockoff"
    assert DEFAULT.treatment == "clean" and DEFAULT.mascot == "none"
    assert DEFAULT.lean_in == 0.0 and DEFAULT.headline_scale == 1.0
    assert DEFAULT.accent == (255, 177, 62), (
        "the default accent must be the amber the existing chrome already "
        "draws with, or every hype film changes colour")
    # A profile that neither moves the camera nor leans on it must hand it
    # back untouched; anything that does something must supply a function.
    assert camera_fn(DEFAULT) is None, (
        "the default profile overrode the renderer's own camera")
    assert camera_fn(StyleProfile("still", "Still", "no motion, no lean")) is None
    assert camera_fn(PROFILES["polished"]) is not None, (
        "a drifting profile has to supply a camera or the drift never happens")
    assert camera_fn(PROFILES["snarky"]) is not None

    for key, profile in PROFILES.items():
        assert key == profile.key or (key == "" and profile is DEFAULT), key
        assert profile.label and profile.note, key
        assert 0.5 <= profile.pace <= 1.5, key
        assert profile.motion in ("lockoff", "drift", "handheld"), key
        assert profile.mascot in ("none", "rare", "present"), key
        assert profile.treatment in ("clean", "vignette"), key
        assert 0.0 <= profile.lean_in <= 0.4, key
        assert len(profile.accent) == 3, key
        assert all(0 <= channel <= 255 for channel in profile.accent), key
        assert 0.5 <= profile.headline_scale <= 2.0, key

    # The shake has to be bounded and repeatable, or a long chapter would
    # wander off its own framing.
    samples = [shake(t * 0.37, 0.012) for t in range(200)]
    assert all(abs(value) <= 0.012 for triple in samples for value in triple)
    assert shake(1.234, 0.012) == shake(1.234, 0.012)
    assert shake(1.0, 0.0) == (0.0, 0.0, 0.0)

    # The snarky register has to actually differ, or the two cuts are one cut.
    snarky = PROFILES["snarky"]
    assert snarky.mascot == "present" and PROFILES["polished"].mascot == "none"
    assert snarky.motion != PROFILES["polished"].motion
    assert snarky.treatment != PROFILES["polished"].treatment
    assert snarky.accent != PROFILES["polished"].accent
    try:
        profile_for("nonesuch")
    except KeyError as exc:
        assert "polished" in str(exc), exc
    else:
        raise AssertionError("an unknown profile was accepted")
