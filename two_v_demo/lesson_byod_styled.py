"""Bring Your Own Dome, cut twice: polished, and snarky with the jelly.

Same script, same numbers, same claims. What changes is the register.

* **``byod_polished``** -- a considered presentation. The camera drifts in
  slowly, the pace is generous, nothing is laid over the frame and the
  character never appears.
* **``byod_snarky``** -- the social cut. Handheld, leaning in whenever the
  character speaks, a little faster, vignetted at the edges, and the pink
  cyber jelly all through it, turning up on the lines that have an attitude.

The two differ only in :mod:`two_v_demo.style_profiles` data and in the
per-chapter ``mood`` / ``mascot`` metadata below. No sentence is rewritten,
which is the point: a register is a way of saying something, not a different
thing to say.

**This module reads the deepseek cut and never edits it.** ``CHAPTERS`` is
imported and copied with :func:`dataclasses.replace`, so
``lesson_byod_deepseek.py`` and the already-rendered
``attempt-v1-deepseek.mp4`` are untouched and still reproduce exactly.
"""

from __future__ import annotations

from dataclasses import replace

from . import style_profiles
from .lesson_byod_deepseek import CHAPTERS as BASE_CHAPTERS
from .lesson_byod_deepseek import BYOD_DEEPSEEK_LESSON
from .lessons import Lesson
from .mascot import MascotCue, MOODS

# ----------------------------------------------------------------------
# Tone: where the script is warm, dry, grave or pleased with itself
# ----------------------------------------------------------------------

MOOD_BY_SLUG: dict[str, str] = {
    # The opening is a proposition, not a joke.
    "title": "neutral", "open": "neutral", "why_host": "warm",
    "arrive": "neutral", "legend": "neutral", "storage": "dry",
    "center": "neutral", "rooms": "warm", "pad_build": "neutral",
    "decks": "neutral",
    # The mechanism is the one place it is allowed to be pleased with itself.
    "iris": "hyped", "rotation": "hyped", "channels": "smug",
    "panel_lip": "neutral", "veins": "smug",
    # The floor chapter is the emotional centre: the carpet, the dog, the way
    # out. It starts warm and ends grave.
    "floor": "warm",
    "catalog": "neutral", "host_scope": "neutral", "starter": "grave",
    "target": "grave", "line": "grave", "operating": "grave",
    "host_design": "neutral", "deluxe": "smug", "foundation": "grave",
    "stay": "grave", "crossover": "grave", "my_story": "grave",
    "little_guy": "warm", "move": "neutral", "hardware": "neutral",
    "growth": "neutral", "layers": "warm", "r_value": "warm",
    "solar": "neutral", "solar_range": "grave", "shared": "neutral",
    "network": "neutral", "ask": "neutral", "rewards": "warm",
    "close": "warm", "share": "warm",
}
"""Where the tone actually moves, chapter by chapter.

Most of this film is a measured argument and stays neutral, which is honest:
a character that is excited about everything is excited about nothing. The
moods are placed where the script itself raises its voice -- the iris, the
rotating foundation, the college story, his mother, the money shredder."""


MASCOT_LINES: dict[str, tuple[MascotCue, ...]] = {
    "why_host": (
        MascotCue(
            line="and each other.",
            cue="both sides love the arrangement",
            hold=2.6, mood="smug", role="cutin",
            note="the aside the author laughed at himself for writing"),
    ),
    "storage": (
        MascotCue(
            line="it is a shed.",
            cue="air-conditioned storage",
            hold=2.8, mood="dry", role="cutin",
            note="the deadpan on a side thought"),
    ),
    "iris": (
        MascotCue(
            line="one pad. every size.",
            cue="twenty foot dome or a forty foot one",
            hold=3.0, mood="hyped", role="cutin",
            note="the mechanism doing the talking"),
    ),
    "rotation": (
        MascotCue(
            line="just freaking cool.",
            cue="honestly, it is just freaking cool",
            hold=2.8, mood="hyped", role="cutin",
            note="the author's own words, handed to the character"),
    ),
    "veins": (
        MascotCue(
            line="brainiac build.",
            cue="looking like a Brainiac build",
            hold=3.0, mood="smug", role="cutin",
            note="the Frankendome joke"),
    ),
    "floor": (
        MascotCue(
            line="glorified tents.",
            cue="glorified tents",
            hold=3.2, mood="dry", role="cutin",
            note="the sharpest line in the film"),
        MascotCue(
            line="that is the whole point.",
            cue="my job here is done",
            hold=3.4, mood="warm", role="cutin",
            note="it lands on the emotional ending of the chapter"),
    ),
    "deluxe": (
        MascotCue(
            line="the one that does not help.",
            cue="the figure that does not help us",
            hold=3.2, mood="grave", role="cutin",
            note="the character meeting the unflattering number"),
    ),
    "my_story": (
        MascotCue(
            line="it cost me. tremendously.",
            cue="it cost me greatly",
            hold=3.6, mood="grave", role="cutin",
            note="no jokes here, and the mood says so"),
    ),
    "little_guy": (
        MascotCue(
            line="the little guy. that is who.",
            cue="the small people, that is who I can impact",
            hold=3.4, mood="warm", role="cutin",
            note="the thesis of the whole project"),
    ),
    "crossover": (
        MascotCue(
            line="not a month. never a month.",
            cue="nobody should buy a house to stay somewhere for a month",
            hold=3.0, mood="dry", role="cutin",
            note="agreeing with the narrator for once"),
    ),
    "close": (
        MascotCue(
            line="a money shredder. at your convenience.",
            cue="a money shredder at your convenience",
            hold=3.6, mood="smug", role="cutin",
            note="the author's own parenthetical, given a face"),
    ),
    "share": (
        MascotCue(
            line="one person. that is the whole ask.",
            cue="one person who can carry it further",
            hold=3.4, mood="warm", role="cutin",
            note="the last thing the audience hears"),
    ),
}
"""The character's lines, cued to the narrator's words rather than to a clock.

Each one is cued on a phrase the narrator says, so the character reacts to the
script instead of interrupting on a schedule. Re-time the narration and every
line moves with it -- which is what :func:`two_v_demo.mascot.resolve` is for.

Nothing is invented here that the author did not already say. The lines are
his own phrases, handed back to a character who agrees, disagrees, or rolls its
eyes at them."""


def styled_chapters(moods: bool, mascot: bool, pace: float):
    """The shared chapters, with a mood on every one and cues where they belong."""
    out = []
    for chapter in BASE_CHAPTERS:
        changes = {}
        if moods:
            changes["mood"] = MOOD_BY_SLUG.get(chapter.slug, "neutral")
        if mascot:
            changes["mascot"] = MASCOT_LINES.get(chapter.slug, ())
        if pace != 1.0:
            # A floor, not a schedule: the audio stage still stretches any
            # chapter whose speech cannot fit the time this leaves it.
            changes["duration"] = round(chapter.duration * pace, 2)
        out.append(replace(chapter, **changes) if changes else chapter)
    return tuple(out)


def _lesson(key: str, title: str, profile_key: str, moods: bool, mascot: bool,
            brand: str = "BRING YOUR OWN DOME") -> Lesson:
    profile = style_profiles.profile_for(profile_key)
    return Lesson(
        key=key, brand=brand, title=title,
        chapters=styled_chapters(moods, mascot, profile.pace),
        scenes=BYOD_DEEPSEEK_LESSON.scenes,
        selftest=lambda: validate_styled(key),
        report=BYOD_DEEPSEEK_LESSON.report,
        snapshot_prefix=key.replace("_", "-"),
        style=BYOD_DEEPSEEK_LESSON.style,
        voice_rate=BYOD_DEEPSEEK_LESSON.voice_rate,
        label_layout=BYOD_DEEPSEEK_LESSON.label_layout,
        ground=BYOD_DEEPSEEK_LESSON.ground,
        frame_fit=BYOD_DEEPSEEK_LESSON.frame_fit,
        profile=profile_key,
        camera_fn=style_profiles.camera_fn(profile),
        audio_bed=BYOD_DEEPSEEK_LESSON.audio_bed,
        audio_bed_gain=BYOD_DEEPSEEK_LESSON.audio_bed_gain,
    )


BYOD_POLISHED = _lesson("byod_polished", "Bring Your Own Dome (polished)",
                        "polished", moods=True, mascot=False)
"""The presentation cut. Moods are on -- they cost nothing without a character
on screen -- and the camera drifts in slowly over each chapter."""

BYOD_SNARKY = _lesson("byod_snarky", "Bring Your Own Dome (snarky)",
                      "snarky", moods=True, mascot=True)
"""The social cut. Handheld, vignetted, leaning in whenever the jelly speaks."""

STYLED_LESSONS = (BYOD_POLISHED, BYOD_SNARKY)


# ----------------------------------------------------------------------
# Proof
# ----------------------------------------------------------------------

def validate_styled(key: str) -> None:
    """Prove a styled cut before it costs a render."""
    lesson = next(entry for entry in STYLED_LESSONS if entry.key == key)
    lesson.validate()

    base = {chapter.slug: chapter for chapter in BASE_CHAPTERS}
    assert len(lesson.chapters) == len(BASE_CHAPTERS), (
        "a styled cut changed the chapter count")

    spoken = 0
    for chapter in lesson.chapters:
        original = base[chapter.slug]
        # The script is identical. This is the whole promise of a register:
        # the words, the numbers and the claims do not move.
        assert chapter.narration == original.narration, chapter.slug
        assert chapter.promise == original.promise, chapter.slug
        assert chapter.equations == original.equations, chapter.slug
        assert chapter.stage == original.stage, chapter.slug
        assert chapter.camera == original.camera, chapter.slug
        assert chapter.callouts == original.callouts, chapter.slug
        assert chapter.mood in MOODS, (chapter.slug, chapter.mood)
        spoken += len(" ".join(chapter.narration))

    # Every cue names a phrase the narrator actually says, which is what makes
    # it land on the words rather than beside them.
    for slug, cues in MASCOT_LINES.items():
        chapter = base[slug]
        text = " ".join(chapter.narration).lower()
        for cue in cues:
            assert cue.cue, (slug, "a cue with no phrase")
            # The cue is matched against the promise as well as the body.
            haystack = f"{chapter.promise} {text}".lower()
            assert " ".join(cue.cue.lower().split()) in haystack, (
                f"{slug}: cue {cue.cue!r} is not in the spoken text")

    if lesson.profile == "snarky":
        assert any(chapter.mascot for chapter in lesson.chapters), (
            "the snarky cut has no mascot cues at all")
        assert sum(len(chapter.mascot) for chapter in lesson.chapters) >= 10, (
            "the snarky cut should use the character, not cameo it")
    if lesson.profile == "polished":
        assert not any(chapter.mascot for chapter in lesson.chapters), (
            "the polished cut is not supposed to have a character in it")

    profile = style_profiles.profile_for(lesson.profile)
    assert profile.key == lesson.profile
    if lesson.profile == "snarky":
        assert profile.mascot == "present" and profile.treatment == "vignette"
        assert profile.motion == "handheld"
    assert spoken > 0


def validate_byod_styled() -> None:
    """Both cuts, and the promise that neither one moved the script."""
    from .mascot import validate_mascot
    from .style_profiles import validate_style_profiles

    validate_mascot()
    validate_style_profiles()
    for lesson in STYLED_LESSONS:
        validate_styled(lesson.key)

    # The two cuts have to actually differ, or this is one film and a spare.
    polished, snarky = BYOD_POLISHED, BYOD_SNARKY
    assert polished.profile != snarky.profile
    assert polished.camera_fn is not snarky.camera_fn
    assert sum(c.duration for c in snarky.chapters) < sum(
        c.duration for c in polished.chapters), (
        "the snarky cut is not faster than the polished one")

    # And the film they came from is untouched.
    assert BYOD_DEEPSEEK_LESSON.key == "byod_deepseek"
    assert not any(getattr(chapter, "mascot", ())
                   for chapter in BYOD_DEEPSEEK_LESSON.chapters), (
        "the deepseek cut grew a mascot; it must stay exactly as it rendered")
    assert all(getattr(chapter, "mood", "neutral") == "neutral"
               for chapter in BYOD_DEEPSEEK_LESSON.chapters), (
        "the deepseek cut's chapters were given moods; it must stay as rendered")
