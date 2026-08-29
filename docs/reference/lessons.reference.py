"""REFERENCE COPY -- do not edit, do not import.

Copied from two_v_demo/lessons.py so an author (human or model) can read the
real thing without touching it. The live file is the source of
truth; this one is a snapshot for imitation.
"""

"""Chapter model, lesson model, and the 2V masterclass timeline.

A *lesson* is a title, a tuple of chapters, and a table of scene painters.
The renderer in ``app.py`` knows how to play any of them; it has no
knowledge of which one it is playing.  New lessons live in their own
``lesson_*.py`` modules and are collected in ``lesson_registry.py``.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Callable, Mapping


@dataclass(frozen=True)
class Chapter:
    slug: str
    number: str
    title: str
    promise: str
    narration: tuple[str, ...]
    equations: tuple[str, ...]
    duration: float
    camera: tuple[float, float, float]
    stage: str
    overlay: str | None = None
    """Override the lesson's style for this chapter alone.

    A sting dropped into a teaching lesson should not wear the
    teaching cards; set this to 'hype' and it goes full-frame for
    those few seconds and then hands the cards back."""


# A scene painter receives the live app, the two geometry batches it should
# fill, and the chapter's 0..1 progress.
ScenePainter = Callable[[object, object, object, float], None]


@dataclass(frozen=True)
class Lesson:
    """One complete teaching video: copy, timeline, and how to draw it."""

    key: str
    brand: str
    title: str
    chapters: tuple["Chapter", ...]
    scenes: Mapping[str, ScenePainter] = field(default_factory=dict)
    equations: Callable[[object, str], list[str]] | None = None
    selftest: Callable[[], None] | None = None
    report: Callable[[], str] | None = None
    snapshot_prefix: str = "lesson"
    style: str = "teaching"
    """``teaching`` draws the cards; ``hype`` goes full-frame with one
    line of type and no chrome."""
    voice_rate: str | None = None
    """Speech rate for this lesson, when it wants its own pacing."""
    label_layout: str = "raw"
    """``raw`` places world labels exactly where they project, letting
    them overlap. ``declutter`` keeps the overlap but nudges labels far
    enough apart that text never lands on text. ``raw`` is the default
    so that re-rendering an already published video reproduces it."""

    def validate(self) -> None:
        """Fail loudly at load time rather than mid-render."""
        if not self.chapters:
            raise ValueError(f"lesson {self.key!r} has no chapters")
        if self.label_layout not in ("raw", "declutter"):
            raise ValueError(
                f"lesson {self.key!r} has unknown label layout "
                f"{self.label_layout!r}"
            )
        for chapter in self.chapters:
            if chapter.overlay not in (None, "teaching", "hype"):
                raise ValueError(
                    f"lesson {self.key!r} chapter {chapter.number} has "
                    f"unknown overlay {chapter.overlay!r}"
                )
        if self.style not in ("teaching", "hype"):
            raise ValueError(
                f"lesson {self.key!r} has unknown style {self.style!r}"
            )
        numbers = [chapter.number for chapter in self.chapters]
        if len(set(numbers)) != len(numbers):
            raise ValueError(f"lesson {self.key!r} repeats a chapter number")
        for chapter in self.chapters:
            if chapter.duration <= 0.5:
                raise ValueError(
                    f"lesson {self.key!r} chapter {chapter.number} is too short"
                )
            if not chapter.narration:
                raise ValueError(
                    f"lesson {self.key!r} chapter {chapter.number} has no narration"
                )


CHAPTERS: tuple[Chapter, ...] = (
    Chapter(
        "welcome", "01", "The question hidden in two boards",
        "Your 72 in and 63.5 in members are already telling us the sphere.",
        (
            "A 2V dome does not ask its two strut classes to be in the golden ratio.",
            "It inherits phi in the parent icosahedron, then changes the edge geometry",
            "when straight midpoints are projected back to a sphere.",
        ),
        ("measured ratio = 72 / 63.5 = 1.133858", "phi = 1.618034  (not the target)"),
        10.0, (28.0, 24.0, 14.5), "hero",
    ),
    Chapter(
        "triangles", "02", "Why domes triangulate",
        "A triangle carries load without changing shape; a square needs a brace.",
        (
            "Push the top node: the force resolves into axial paths along the edges.",
            "Triangulation trades bending-prone panels for a network of tension and",
            "compression members. Real joints and foundations still require engineering.",
        ),
        ("F = F_compression + F_tension", "geometry explains form; engineering sizes members"),
        10.0, (35.0, 30.0, 15.0), "rigidity",
    ),
    Chapter(
        "platonic", "03", "The five regular starting points",
        "The icosahedron wins because twenty small faces begin closest to a sphere.",
        (
            "Each Platonic solid has one regular face type and one vertex arrangement.",
            "More evenly distributed vertices mean a smaller correction when we project",
            "the surface outward. The icosahedron gives twenty equilateral launch pads.",
        ),
        ("faces: 4, 6, 8, 12, 20", "2V means: divide every parent edge into 2 segments"),
        12.0, (32.0, 27.0, 18.0), "platonic",
    ),
    Chapter(
        "phi", "04", "Where the golden ratio really lives",
        "Phi builds the twelve parent vertices—not the finished strut ratio.",
        (
            "The coordinate families (0, ±1, ±phi), (±1, ±phi, 0), and",
            "(±phi, 0, ±1) place twelve points at one common radius.",
            "Any neighboring pair is exactly 2 units apart before normalization.",
        ),
        ("phi = (1 + sqrt(5)) / 2", "R_raw = sqrt(1 + phi^2)", "edge_raw = 2"),
        12.0, (30.0, 22.0, 16.0), "coordinates",
    ),
    Chapter(
        "normalize", "05", "Put the icosahedron on a unit sphere",
        "One division turns raw coordinates into reusable chord factors.",
        (
            "Normalize each vertex by its distance from the origin.",
            "Now the sphere radius is exactly one. Every measured edge is a multiplier",
            "that can later be scaled to inches, feet, meters, or any other unit.",
        ),
        ("v_hat = v / ||v||", "parent chord = 2 / sqrt(1 + phi^2) = 1.051462 R"),
        10.0, (27.0, 25.0, 14.0), "icosahedron",
    ),
    Chapter(
        "subdivide", "06", "Split every parent edge in half",
        "Thirty parent edges create thirty new midpoint candidates.",
        (
            "The arithmetic midpoint is easy: average the two endpoint vectors.",
            "But that point lies inside the sphere. Leaving it there makes a faceted",
            "icosahedron subdivision—not a geodesic sphere.",
        ),
        ("m = (a + b) / 2", "||m|| = 0.850651 < 1"),
        11.0, (30.0, 24.0, 14.0), "midpoints",
    ),
    Chapter(
        "project", "07", "Project the midpoints outward",
        "Normalization is the exact radial projection back to the sphere.",
        (
            "Each midpoint travels on a ray from the origin until its radius is one.",
            "The new point changes the chord distances inside every subdivided face.",
            "That single operation is where the two finished lengths appear.",
        ),
        ("p = m / ||m||", "projection distance = 1 - ||m|| = 0.149349 R"),
        12.0, (29.0, 22.0, 14.0), "projection",
    ),
    Chapter(
        "classes", "08", "Measure and group every chord",
        "120 sphere edges collapse into exactly two numerical classes.",
        (
            "SHORT connects a parent vertex to a projected midpoint.",
            "LONG connects two projected midpoints. Color grouping is numerical:",
            "equal lengths receive equal colors—no letter convention is required.",
        ),
        ("SHORT = 0.546533 R", "LONG = 0.618034 R", "LONG / SHORT = 1.130826"),
        13.0, (31.0, 25.0, 14.0), "classes",
    ),
    Chapter(
        "derive", "09", "Four routes to the same answer",
        "Coordinates, dot products, central angles, and the chord formula agree.",
        (
            "Coordinate route: subtract endpoint vectors and take the magnitude.",
            "Angle route: theta = acos(u dot v), then chord = 2R sin(theta/2).",
            "Law of cosines, a spreadsheet, Python, and CAD must reproduce the same values.",
        ),
        ("c = ||R u - R v||", "theta = acos(u . v)", "c = 2 R sin(theta / 2)"),
        13.0, (29.0, 24.0, 13.0), "derivations",
    ),
    Chapter(
        "your_dome", "10", "Audit the 72 in / 63.5 in dome",
        "Your ratio is close; the two measurements imply radii only fractions apart.",
        (
            "Use each member independently to estimate radius, then use a least-squares",
            "fit when both measurements contain cutting, hub, or tape error.",
            "Center-to-center geometry must be separated from physical cut length.",
        ),
        ("R_long = 72 / 0.618034", "R_short = 63.5 / 0.546533", "best R minimizes both residuals"),
        14.0, (28.0, 25.0, 16.0), "audit",
    ),
    Chapter(
        "cut_list", "11", "From radius to a cut list",
        "Scale the unit model once; then apply a documented connector deduction.",
        (
            "A hemisphere contains 65 unique structural edges and 40 triangular faces.",
            "The theoretical lengths are hub-center to hub-center. Tube, timber, tabs,",
            "and commercial hubs each need their own verified end allowance.",
        ),
        ("center length = chord factor x R", "cut length = center length - connector deduction"),
        13.0, (31.0, 25.0, 15.0), "cutlist",
    ),
    Chapter(
        "triangles_build", "12", "Panels, hubs, and build sequence",
        "Two triangle families repeat; hub angles are connector-system dependent.",
        (
            "Make full-size gauges for SHORT and LONG, batch-cut, and label every part.",
            "Dry-build repeating triangles before raising rings from the base upward.",
            "PVC, timber, and tube share centerlines—not end cuts or structural capacity.",
        ),
        ("30 x SHORT-SHORT-LONG panels", "10 x LONG-LONG-LONG panels", "base ring: 10 vertices"),
        13.0, (34.0, 28.0, 14.0), "assembly",
    ),
    Chapter(
        "verify", "13", "Close the measurement loop",
        "A good build is calculated, fabricated, measured, and corrected.",
        (
            "Check member gauges, base decagon diagonals, hub-center radius, and level.",
            "Small repeated errors accumulate around a ring. Correct them before the apex.",
            "For occupied or load-bearing structures, use local code and an engineer.",
        ),
        ("check: length -> triangle -> ring -> radius -> height", "expected dome height = R"),
        12.0, (30.0, 24.0, 14.0), "verification",
    ),
    Chapter(
        "finale", "14", "The whole transformation",
        "Phi chooses the parent points; projection chooses the finished members.",
        (
            "Raw phi coordinates become a normalized icosahedron.",
            "Midpoints move outward, two chord factors emerge, and one scale factor",
            "turns the unit geometry into a buildable 2V dome.",
        ),
        ("phi -> icosahedron -> 2V subdivision -> projection -> SHORT + LONG -> scale"),
        12.0, (30.0, 28.0, 14.0), "finale",
    ),
)


TOTAL_DURATION = sum(chapter.duration for chapter in CHAPTERS)


def timeline_duration(
    durations: tuple[float, ...] | None = None,
    chapters: tuple[Chapter, ...] = CHAPTERS,
) -> float:
    values = durations or tuple(chapter.duration for chapter in chapters)
    if len(values) != len(chapters):
        raise ValueError("chapter duration count does not match chapter count")
    return sum(values)


def chapter_at_time(
    timeline_seconds: float,
    durations: tuple[float, ...] | None = None,
    chapters: tuple[Chapter, ...] = CHAPTERS,
) -> tuple[int, float]:
    """Return (chapter index, 0..1 local progress) for a looped timeline."""
    if not chapters:
        return 0, 0.0
    values = durations or tuple(chapter.duration for chapter in chapters)
    total = timeline_duration(values, chapters)
    timeline_seconds %= total
    cursor = 0.0
    for index, duration in enumerate(values):
        if timeline_seconds < cursor + duration:
            return index, (timeline_seconds - cursor) / duration
        cursor += duration
    return len(chapters) - 1, 1.0


def chapter_start(
    index: int,
    durations: tuple[float, ...] | None = None,
    chapters: tuple[Chapter, ...] = CHAPTERS,
) -> float:
    values = durations or tuple(chapter.duration for chapter in chapters)
    return sum(values[:index])


def _two_v_selftest() -> None:
    from .geometry import validate_geometry

    validate_geometry()


def _two_v_report() -> str:
    from .geometry import calculation_report

    return calculation_report()


TWO_V_LESSON = Lesson(
    key="2v",
    brand="2V / GEODESIC MASTERCLASS",
    title="2V Geodesic Masterclass",
    chapters=CHAPTERS,
    selftest=_two_v_selftest,
    report=_two_v_report,
    snapshot_prefix="2v",
)
