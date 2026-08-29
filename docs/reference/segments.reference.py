"""REFERENCE COPY -- do not edit, do not import.

Copied from two_v_demo/segments.py so an author (human or model) can read the
real thing without touching it. The live file is the source of
truth; this one is a snapshot for imitation.
"""

"""Reusable scene packages that get composed into lessons automatically.

A *segment* is a small run of chapters plus the painters they need,
packaged so it can be dropped into any lesson without being rewritten.
The outro is the clearest case: every video should end with the same
contact card, and nobody should be maintaining nine copies of it.

Placement is declared by the segment, not by the lesson:

``start``      before everything
``end``        after everything
``after:SLUG`` immediately after the chapter with that slug, if present
``manual``     never automatic; the lesson asks for it by key

Composition happens in one place -- :func:`compose` -- and renumbers the
finished film, so a lesson never has to know what got inserted.
"""

from __future__ import annotations

import math
from dataclasses import dataclass, field, replace
from typing import Callable, Mapping

import numpy as np

from .geometry import build_demo_geometry, normalize
from .lessons import Chapter, Lesson
from .render_kit import (
    AMBER,
    CYAN,
    GREEN,
    MUTED,
    PURPLE,
    RED,
    WHITE,
    WorldLabel,
    clamp,
    ease_in_out,
    smoothstep,
)
from .timber import (
    CHAINSAW,
    draw_cardboard,
    draw_glue,
    draw_led_run,
    draw_patch,
    draw_timber,
    led_colour,
)


GEOMETRY = build_demo_geometry()
SCALE = 5.2


def _rgb(colour) -> tuple[int, int, int]:
    return (int(colour[0] * 255), int(colour[1] * 255), int(colour[2] * 255))


# ----------------------------------------------------------------------
# The segment model
# ----------------------------------------------------------------------

@dataclass(frozen=True)
class AudioCue:
    """One soundboard hit, placed relative to a chapter in the segment."""

    sound: str
    """Soundboard key, ``category/name``. Missing sounds are skipped."""
    chapter_slug: str
    offset: float = 0.0
    gain: float = 1.0
    loop: bool = False


@dataclass(frozen=True)
class Segment:
    """A packaged run of chapters, its painters, and its sound."""

    key: str
    title: str
    kind: str
    chapters: tuple[Chapter, ...]
    scenes: Mapping[str, Callable] = field(default_factory=dict)
    placement: str = "manual"
    audio: tuple[AudioCue, ...] = ()
    default_on: bool = False
    """Whether composition includes it unless a lesson opts out."""
    order: int = 0
    """Tie-break among segments sharing a placement; higher goes
    later. An outro is forced last regardless, because that is what an
    outro is."""
    note: str = ""

    def validate(self) -> None:
        if not self.chapters:
            raise ValueError(f"segment {self.key!r} has no chapters")
        for chapter in self.chapters:
            if chapter.stage not in self.scenes:
                raise ValueError(
                    f"segment {self.key!r} chapter {chapter.slug!r} wants "
                    f"stage {chapter.stage!r}, which it does not provide"
                )
            if not chapter.narration:
                raise ValueError(
                    f"segment {self.key!r} chapter {chapter.slug!r} is silent"
                )
        if not (self.placement in ("start", "end", "manual")
                or self.placement.startswith("after:")):
            raise ValueError(
                f"segment {self.key!r} has unknown placement "
                f"{self.placement!r}"
            )
        slugs = {cue.chapter_slug for cue in self.audio}
        known = {chapter.slug for chapter in self.chapters}
        missing = slugs - known
        if missing:
            raise ValueError(
                f"segment {self.key!r} cues sound on unknown chapters: "
                f"{sorted(missing)}"
            )


# ----------------------------------------------------------------------
# Where to reach me -- the outro on every video
# ----------------------------------------------------------------------

CONTACTS: tuple[tuple[str, str, tuple], ...] = (
    ("@DonovanZeanah", "Instagram", CYAN),
    ("facebook.com/zeanah", "Facebook", PURPLE),
    ("@shortcircuitr5", "TikTok", AMBER),
    ("github.com/dkzeanah", "GitHub", WHITE),
    ("zeanahlab.com", "(soon)", GREEN),
    ("kickstarter.com/frankendome", "(soon)", RED),
)


def scene_seg_outro(app, opaque, transparent, p: float) -> None:
    """The contact card: six handles in one readable band."""
    reveal = clamp(p * 1.4)
    for index, edge in enumerate(GEOMETRY.hemisphere_edges):
        a, b = (GEOMETRY.vertices[i] * 3.0 for i in edge)
        draw_timber(opaque, a, b, 0.055, index, CHAINSAW, sides=6)
    columns = 3
    for index, (handle, label, colour) in enumerate(CONTACTS):
        if index / len(CONTACTS) > reveal:
            continue
        row, column = divmod(index, columns)
        x = -7.4 + column * 7.4
        z = 7.4 - row * 1.9
        opaque.box((x, 0.0, z), (6.2, 0.42, 1.05), colour)
        app.world_labels.append(WorldLabel(
            np.array([x, 0.0, z]),
            handle if label in ("Instagram", "Facebook", "TikTok", "GitHub")
            else f"{handle}  {label}",
            _rgb(colour)))
    app.world_labels.append(WorldLabel(
        np.array([0.0, 0.0, -1.2]),
        "everything is documented, including the parts that failed",
        (169, 188, 203)))


OUTRO = Segment(
    key="outro",
    title="Where to reach me",
    kind="outro",
    placement="end",
    default_on=True,
    note="The contact card. Ends every video.",
    scenes={"seg_outro": scene_seg_outro},
    chapters=(
        Chapter(
            "outro", "00", "Follow the experiments",
            "Follow the experiments.",
            (
                "Everything is documented, including the parts that failed.",
                "Instagram, Donovan Zeanah. Facebook dot com slash zeanah. TikTok,",
                "short circuiter five. GitHub dot com slash d k zeanah. Zeanah Lab dot",
                "com and a Kickstarter for Frankendome are both coming soon.",
            ),
            (), 5.0, (90.0, 20.0, 20.0), "seg_outro",
        ),
    ),
)


# ----------------------------------------------------------------------
# Who am I -- droppable anywhere
# ----------------------------------------------------------------------

def scene_seg_bio(app, opaque, transparent, p: float) -> None:
    """The stack of things one person happens to be."""
    rows = (
        ("NAVY VETERAN", CYAN), ("PROGRAMMER", GREEN),
        ("AVIONICS TECHNICIAN", AMBER), ("FABRICATOR", PURPLE),
        ("AEROSPACE STUDENT", RED),
    )
    reveal = clamp(p * 1.4)
    for index, (label, colour) in enumerate(rows):
        if index / len(rows) > reveal:
            continue
        z = 0.8 + index * 1.30
        width = 9.4 - index * 0.55
        opaque.box((0.0, 0.0, z), (width, 0.6, 1.02), colour)
        app.world_labels.append(WorldLabel(
            np.array([0.0, 0.0, z]), label, _rgb(colour)))
    app.world_labels.append(WorldLabel(
        np.array([0.0, 0.0, -1.0]),
        "a perfectly stable combination", (169, 188, 203)))


WHOAMI = Segment(
    key="whoami",
    title="Who is behind this",
    kind="bio",
    placement="manual",
    note="The credentials stack. Insert wherever a video needs it.",
    scenes={"seg_bio": scene_seg_bio},
    chapters=(
        Chapter(
            "whoami", "00", "Who is behind this",
            "For anyone wondering who is behind all these triangles.",
            (
                "For anyone wondering who is behind all of this: I am a Navy veteran,",
                "a programmer, an F.A.A. accredited avionics bench technician, and a",
                "fabricator, now using the G.I. Bill to study aerospace engineering.",
                "A perfectly stable combination.",
            ),
            (), 5.0, (90.0, 18.0, 15.0), "seg_bio",
        ),
    ),
)


# ----------------------------------------------------------------------
# Calls to action -- a family, one of them default
# ----------------------------------------------------------------------

def scene_seg_share(app, opaque, transparent, p: float) -> None:
    """One dome becomes many, outward."""
    spread = ease_in_out(clamp(p * 1.25))
    for index, edge in enumerate(GEOMETRY.hemisphere_edges):
        a, b = (GEOMETRY.vertices[i] * 2.3 for i in edge)
        draw_timber(opaque, a, b, 0.05, index, CHAINSAW, sides=6)
    for index in range(20):
        angle = math.tau * index / 20
        distance = 4.2 + spread * (7.2 + (index % 3) * 2.4)
        centre = np.array([distance * math.cos(angle),
                           distance * math.sin(angle), 0.0])
        size = 0.95 * spread
        for edge in list(GEOMETRY.hemisphere_edges)[::5]:
            a, b = (GEOMETRY.vertices[i] * size + centre for i in edge)
            opaque.cylinder(a, b, 0.03, CYAN, 5)
        if spread > 0.25:
            opaque.arrow(
                np.array([2.7 * math.cos(angle), 2.7 * math.sin(angle), 0.9]),
                centre + np.array([0.0, 0.0, 0.9]), 0.028, GREEN)
    app.world_labels.append(WorldLabel(
        np.array([0.0, 0.0, 4.8]), "SEND IT TO ONE PERSON", (111, 235, 155)))


CTA_SHARE = Segment(
    key="cta_share",
    title="Share it",
    kind="cta",
    placement="end",
    default_on=True,
    note="The default call to action. One share, one person.",
    scenes={"seg_share": scene_seg_share},
    chapters=(
        Chapter(
            "cta_share", "00", "Do the one thing",
            "Send this to one person who can carry it further than I can.",
            (
                "If any of this was worth your time, send it to one person who can",
                "carry it further than I can. That is the whole ask. One share from",
                "somebody with reach does more for this than a month of me in a field",
                "with a chainsaw.",
            ),
            (), 5.0, (36.0, 26.0, 22.0), "seg_share",
        ),
    ),
)


def scene_seg_build_along(app, opaque, transparent, p: float) -> None:
    """An alternate call: build one yourself."""
    build = ease_in_out(clamp(p * 1.2))
    edges = list(GEOMETRY.hemisphere_edges)
    count = int(len(edges) * build)
    for index, edge in enumerate(edges[:count]):
        a, b = (GEOMETRY.vertices[i] * SCALE for i in edge)
        draw_timber(opaque, a, b, 0.085, index, CHAINSAW, sides=7)
    app.world_labels.extend([
        WorldLabel(np.array([0.0, 0.0, SCALE + 1.6]),
                   f"{count} OF {len(edges)} STRUTS", (255, 177, 62)),
        WorldLabel(np.array([0.0, 0.0, -1.0]),
                   "the cut lists are all in the description", (169, 188, 203)),
    ])


CTA_BUILD = Segment(
    key="cta_build",
    title="Build one",
    kind="cta",
    placement="manual",
    note="Alternate call to action, for the construction lessons.",
    scenes={"seg_build_along": scene_seg_build_along},
    chapters=(
        Chapter(
            "cta_build", "00", "Build one",
            "Every number you need is in the description.",
            (
                "And if you would rather build one than watch one: every cut list,",
                "every angle and every count in this video came out of a program that",
                "proves its own arithmetic, and all of it is in the description.",
            ),
            (), 5.0, (32.0, 24.0, 17.0), "seg_build_along",
        ),
    ),
)


# ----------------------------------------------------------------------
# FRANKENDOME PARTY -- the sting
# ----------------------------------------------------------------------

# Each look is a different night out for the same set of bones.
PARTY_LOOKS = (
    "raw", "painted", "greenhouse", "led_frame", "led_panels",
    "cardboard", "patched",
)


def scene_seg_party(app, opaque, transparent, p: float) -> None:
    """The same frame, seven ways, cut fast.

    In hard and sudden, then it settles: the look changes quickly through
    the first half and holds on the last one while the cheering fades.
    """
    # Open on raw timber and hold it long enough to register -- it is
    # the shot the whole sting is about -- then cut through the rest
    # quickly and settle on the last one.
    progress = clamp(p)
    if progress < 0.20:
        index = 0
    else:
        remaining = (progress - 0.20) / 0.80
        index = min(len(PARTY_LOOKS) - 1,
                    1 + int((remaining ** 0.72) * (len(PARTY_LOOKS) - 1)))
    eased = progress
    look = PARTY_LOOKS[index]
    phase = p * 2.4

    rng = np.random.default_rng(7)
    jitter = rng.normal(0.0, 1.0, GEOMETRY.vertices.shape) * 0.055
    points = GEOMETRY.vertices + jitter
    edges = list(GEOMETRY.hemisphere_edges)
    faces = list(GEOMETRY.hemisphere_faces)

    tint = None
    if look == "painted":
        tint = (0.24, 0.62, 0.32, 1.0)
    elif look == "greenhouse":
        tint = (0.72, 0.78, 0.80, 1.0)

    for edge_index, edge in enumerate(edges):
        a, b = (points[i] * SCALE for i in edge)
        draw_timber(opaque, a, b, 0.095, edge_index, CHAINSAW, sides=7,
                    tint=tint)
        if look == "led_frame":
            draw_led_run(opaque, a, b, edge_index * 3, phase)

    if look == "greenhouse":
        for face_index, face in enumerate(faces):
            corners = points[[int(v) for v in face]] * SCALE
            normal = normalize(corners.mean(axis=0))
            transparent.triangle(corners[0], corners[1], corners[2],
                                 (0.55, 0.85, 0.92, 0.24), normal)
    elif look == "led_panels":
        for face_index, face in enumerate(faces):
            corners = points[[int(v) for v in face]] * SCALE
            colour = led_colour(face_index, phase)
            normal = normalize(corners.mean(axis=0))
            transparent.triangle(corners[0], corners[1], corners[2],
                                 (colour[0], colour[1], colour[2], 0.40), normal)
    elif look == "cardboard":
        local = clamp((eased * len(PARTY_LOOKS)) - index)
        for face_index, face in enumerate(faces):
            corners = points[[int(v) for v in face]] * SCALE
            draw_cardboard(transparent, corners, face_index * 5, local)
    elif look == "patched":
        for face_index, face in enumerate(faces[::3]):
            corners = points[[int(v) for v in face]] * SCALE
            normal = normalize(corners.mean(axis=0))
            transparent.triangle(corners[0], corners[1], corners[2],
                                 (0.74, 0.60, 0.38, 0.55), normal)
            draw_patch(opaque, corners, face_index * 11, 0.08)

    # Glue at a scattering of joints, in every look. It never comes off.
    used = sorted({i for edge in edges for i in edge})
    for slot, vertex in enumerate(used[::4]):
        draw_glue(transparent, points[vertex] * SCALE, 0.16, vertex * 13 + slot)

    app.world_labels.append(WorldLabel(
        np.array([0.0, 0.0, SCALE + 2.0]), "FRANKENDOME!", (255, 177, 62)))


PARTY = Segment(
    key="party",
    title="Frankendome party",
    kind="sting",
    placement="manual",
    note="4-7 second sting. Hard in, settles out. Cheering under it.",
    scenes={"seg_party": scene_seg_party},
    audio=(
        AudioCue("oneshots/cheer", "party", offset=0.0, gain=0.45),
        AudioCue("stingers/airhorn", "party", offset=0.05, gain=0.35),
    ),
    chapters=(
        Chapter(
            "party", "00", "Frankendome",
            "FRANKENDOME!",
            ("Frankendome!",),
            (), 4.0, (28.0, 24.0, 18.0), "seg_party", "hype",
        ),
    ),
)


def scene_seg_franken_plain(app, opaque, transparent, p: float) -> None:
    """The frankendome as it actually is: static, lumpy, unflattered.

    No cycling looks, no lighting, no celebration. The only motion is the
    renderer's own slow camera drift, which is enough to read the shape
    without turning it into an event.
    """
    rng = np.random.default_rng(7)
    jitter = rng.normal(0.0, 1.0, GEOMETRY.vertices.shape) * 0.055
    points = GEOMETRY.vertices + jitter
    edges = list(GEOMETRY.hemisphere_edges)

    for index, edge in enumerate(edges):
        a, b = (points[i] * SCALE for i in edge)
        draw_timber(opaque, a, b, 0.095, index, CHAINSAW, sides=7)

    # Two patched panels and a scatter of glue, because that is what it
    # looked like. Nothing here is animated.
    faces = list(GEOMETRY.hemisphere_faces)
    for face_index, face in enumerate(faces[::9]):
        corners = points[[int(v) for v in face]] * SCALE
        normal = normalize(corners.mean(axis=0))
        transparent.triangle(corners[0], corners[1], corners[2],
                             (0.60, 0.50, 0.36, 0.42), normal)
        draw_patch(opaque, corners, face_index * 11 + 3, 0.08)

    used = sorted({i for edge in edges for i in edge})
    for slot, vertex in enumerate(used[::5]):
        draw_glue(transparent, points[vertex] * SCALE, 0.15, vertex * 13 + slot)

    app.world_labels.append(WorldLabel(
        np.array([0.0, 0.0, SCALE + 1.7]), "FRANKENDOME", (169, 188, 203)))


FRANKEN_PLAIN = Segment(
    key="franken_plain",
    title="Frankendome, plainly",
    kind="sting",
    placement="manual",
    note="The static, unflattered frankendome. No looks, no lights, no "
         "cheering. Use instead of 'party' when a celebration would be "
         "the wrong note.",
    scenes={"seg_franken_plain": scene_seg_franken_plain},
    chapters=(
        Chapter(
            "franken_plain", "00", "Frankendome",
            "Frankendome.",
            ("Frankendome.",),
            (), 4.0, (34.0, 22.0, 18.0), "seg_franken_plain", "hype",
        ),
    ),
)


SEGMENTS: dict[str, Segment] = {
    item.key: item
    for item in (OUTRO, WHOAMI, CTA_SHARE, CTA_BUILD, PARTY, FRANKEN_PLAIN)
}


# ----------------------------------------------------------------------
# Composition
# ----------------------------------------------------------------------

def compose(
    lesson: Lesson,
    include: tuple[str, ...] | None = None,
    exclude: tuple[str, ...] = (),
) -> Lesson:
    """Return the lesson with its segments spliced in and renumbered.

    Segments marked ``default_on`` are included unless excluded; anything
    named in ``include`` is added regardless of its default. Placement is
    the segment's own business, so a lesson never states where the outro
    goes.
    """
    wanted: list[Segment] = []
    for segment in SEGMENTS.values():
        if segment.key in exclude:
            continue
        if segment.default_on or (include and segment.key in include):
            wanted.append(segment)

    if not wanted:
        return lesson

    chapters = list(lesson.chapters)
    scenes = dict(lesson.scenes)

    starts = [s for s in wanted if s.placement == "start"]
    ends = [s for s in wanted if s.placement == "end"]
    anchored = [s for s in wanted if s.placement.startswith("after:")]
    manual = [
        s for s in wanted
        if s.placement == "manual" and include and s.key in include
    ]

    for segment in anchored:
        slug = segment.placement.split(":", 1)[1]
        position = next(
            (index for index, chapter in enumerate(chapters)
             if chapter.slug == slug), None)
        if position is None:
            # A lesson without that anchor simply does not get it.
            continue
        chapters[position + 1:position + 1] = list(segment.chapters)
        scenes.update(segment.scenes)

    # Closing segments run in order, and an outro is always genuinely
    # last -- otherwise whichever happened to be declared first wins,
    # which is how the contact card landed mid-film the first time.
    ends.sort(key=lambda item: (item.kind == "outro", item.order))
    manual.sort(key=lambda item: item.order)
    for segment in manual + ends:
        chapters.extend(segment.chapters)
        scenes.update(segment.scenes)
    for segment in reversed(starts):
        chapters[0:0] = list(segment.chapters)
        scenes.update(segment.scenes)

    renumbered = tuple(
        replace(chapter, number=f"{index + 1:02d}")
        for index, chapter in enumerate(chapters)
    )
    return replace(lesson, chapters=renumbered, scenes=scenes)


def segment_menu() -> str:
    lines = [f"{len(SEGMENTS)} reusable segments:"]
    for segment in SEGMENTS.values():
        mark = "auto" if segment.default_on else "    "
        lines.append(
            f"  {mark}  {segment.key:<11} {segment.kind:<6} "
            f"{segment.placement:<12} {segment.title}")
        lines.append(f"            {segment.note}")
        for cue in segment.audio:
            lines.append(f"            sound: {cue.sound} "
                         f"(+{cue.offset:.2f}s, gain {cue.gain:.2f})")
    return "\n".join(lines)


def validate_segments() -> None:
    """Every segment must be self-consistent, and composition must be sane."""
    from .lesson_registry import LESSONS

    for segment in SEGMENTS.values():
        segment.validate()
        assert segment.kind in ("outro", "intro", "cta", "sting", "bio"), segment.kind

    # Exactly one outro, and it is automatic.
    outros = [s for s in SEGMENTS.values() if s.kind == "outro"]
    assert len(outros) == 1, outros
    assert outros[0].default_on and outros[0].placement == "end"

    # Exactly one default call to action.
    defaults = [s for s in SEGMENTS.values()
                if s.kind == "cta" and s.default_on]
    assert len(defaults) == 1, defaults

    base = LESSONS["hex"]
    composed = compose(base)
    assert len(composed.chapters) > len(base.chapters)
    numbers = [chapter.number for chapter in composed.chapters]
    assert numbers == [f"{index + 1:02d}" for index in range(len(numbers))]
    # The outro is genuinely last, and the CTA sits just before it.
    assert composed.chapters[-1].slug == "outro", composed.chapters[-1].slug
    assert "cta_share" in {chapter.slug for chapter in composed.chapters}
    # Every stage a composed chapter names must be paintable.
    for chapter in composed.chapters:
        assert chapter.stage in composed.scenes, chapter.stage
    composed.validate()

    # Opting out has to work, and must not disturb the numbering.
    bare = compose(base, exclude=("outro", "cta_share"))
    assert len(bare.chapters) == len(base.chapters), len(bare.chapters)

    # Asking for a manual segment adds it.
    with_party = compose(base, include=("party",))
    assert "party" in {chapter.slug for chapter in with_party.chapters}
