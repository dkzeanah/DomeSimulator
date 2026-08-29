"""Every video this package produces, and how to rebuild all of them.

One list, in the order they were made.  ``render_all`` walks it and
exports each in turn, so a fresh clone on a fresh machine can reproduce
the whole set without anybody remembering which lesson key made which
file.

How reproducible is "exactly"?
------------------------------
The picture is fully deterministic.  Every scene is a pure function of
``(stage, progress)``; the two places randomness appears -- the lumpy
franken frame and the salvage heap -- both draw from seeded generators,
so they produce the same frame on every machine, every run.

The **timeline** is not sourced locally.  Chapter durations come from
measuring synthesized speech, and that speech comes from a network
service.  If the per-lesson voice cache directory is present, the
measurement is a re-read of the same files and the render is
bit-for-bit repeatable.  If it is absent, the clips are re-synthesized,
and any drift in the service moves chapter boundaries by fractions of a
second -- which moves every frame after it.

So: **ship the ``*-voice-*`` directories with the repository if exact
reproduction matters.**  Without them the result is the same film, not
the same file.
"""

from __future__ import annotations

import subprocess
import sys
from dataclasses import dataclass
from pathlib import Path


OUTPUT_DIR = Path("deliverables/masterclass")


@dataclass(frozen=True)
class Deliverable:
    """One rendered video and the lesson that produces it."""

    lesson: str
    filename: str
    note: str
    compose: bool = False
    """Whether to splice the automatic segments in.

    Off for everything that shipped before segments existed, so those
    files keep reproducing exactly. New work turns it on."""
    segments: tuple[str, ...] = ()
    """Extra segments by key, beyond the automatic ones."""

    def path(self, root: Path = OUTPUT_DIR) -> Path:
        return root / self.filename

    @property
    def voice_cache_glob(self) -> str:
        return f"{Path(self.filename).stem}-voice-*"


# In the order they were made.  Earlier entries are deliberately frozen:
# they were rendered before the label layout became configurable, and
# they default to ``raw`` so a re-render reproduces what shipped.
DELIVERABLES: tuple[Deliverable, ...] = (
    Deliverable("hex", "hex-dome-masterclass.mp4",
                "Hexagonal domes: one strut length, twelve pentagons, "
                "and what frequency costs."),
    Deliverable("zome", "zome-construction-masterclass.mp4",
                "Zomes: flat parallelogram panels, one strut length, a "
                "point on top."),
    Deliverable("build", "dome-construction-masterclass.mp4",
                "The 46-chapter construction lesson, geometry through to "
                "the franken-dome."),
    Deliverable("line", "assembly-line-energy-masterclass.mp4",
                "What building one dome costs the two people who build it."),
    Deliverable("cuts", "hubless-compound-cut.mp4",
                "The compound cut on both machines, with the jig between."),
    Deliverable("franken", "frankendome-build-v2.mp4",
                "Mixed stock, folded brackets, slack and settling, plus "
                "hubless strut coding, the floor deck and the commercial "
                "case. The 13-chapter frankendome-build.mp4 beside it is "
                "archival: the lesson has since grown to 21 chapters and "
                "that file can no longer be reproduced from this code.",
                compose=True),
    Deliverable("hype", "frankendome-montage.mp4",
                "The montage, version one. Raw label placement, as shipped."),
    Deliverable("hype2", "frankendome-montage-v2.mp4",
                "Version two: the asides. Raw label placement, as shipped."),
    Deliverable("hype3", "frankendome-montage-v3.mp4",
                "Version three: the reason, and legible labels."),
    Deliverable("hype4", "frankendome-montage-v4.mp4",
                "Version four: the brand segments, the party sting and the "
                "shared contact outro.",
                compose=True, segments=("party",)),
    Deliverable("hype5", "frankendome-montage-v5.mp4",
                "Version five: no girlfriend remark, and the plain "
                "frankendome in place of the party sting.",
                compose=True, segments=("franken_plain",)),
    Deliverable("hype6", "frankendome-montage-v6.mp4",
                "Version six: themed shells, the four product lines, "
                "a faster cadence and a synthesised beat under it.",
                compose=True, segments=("party",)),
    Deliverable("kick", "dome-kickstarter.mp4",
                "The campaign film: why a dome, what one costs to the "
                "dollar, and what a hundred thousand dollars buys.",
                compose=True, segments=("whoami",)),
    Deliverable("kick2", "dome-kickstarter-v2.mp4",
                "The campaign film with the pony wall, the overhanging "
                "brim and its catchment, running cost at 17 cents a "
                "kilowatt hour, radiative cooling paint, and the ten "
                "points.",
                compose=True, segments=("whoami",)),
    Deliverable("master", "domesim-master-presentation.mp4",
                "The master presentation: the toolchain tour, the whole "
                "construction masterclass, the frankendome, the priced "
                "starter home and the factory case -- with math screens "
                "that derive every figure on camera. Its segments (whoami, "
                "the party sting) are composed inside the lesson module, "
                "so this render must not compose them again.",
                compose=False),
    Deliverable("world", "every-dome-in-the-world.mp4",
                "All twelve Dome Creator presets, each rebuilt live from "
                "the simulator's own modules and rendered at true "
                "relative scale, with math screens for the frequency "
                "ladder, hub versus hubless, price per square foot, "
                "envelope efficiency and scale.",
                compose=False),
)


DELIVERABLE_BY_LESSON = {item.lesson: item for item in DELIVERABLES}


def missing_voice_caches(root: Path = OUTPUT_DIR) -> tuple[Deliverable, ...]:
    """Deliverables whose cached speech is absent, so would re-synthesize."""
    return tuple(
        item for item in DELIVERABLES
        if not any(root.glob(item.voice_cache_glob))
    )


def render_all(
    root: Path = OUTPUT_DIR,
    only: tuple[str, ...] | None = None,
    force: bool = False,
    fps: int = 30,
    size: str = "1920x1080",
    progress=print,
) -> int:
    """Export every deliverable, one at a time.

    Sequential on purpose.  Running exports in parallel makes the speech
    endpoint throttle and start refusing connections, which kills the
    runs that are still synthesizing while sparing the one that is
    already rendering -- a failure that took a while to diagnose the
    first time.
    """
    import launcher_common as _lc

    root.mkdir(parents=True, exist_ok=True)
    wanted = [
        item for item in DELIVERABLES
        if only is None or item.lesson in only
    ]
    if not wanted:
        progress(f"nothing matches {only!r}")
        return 2

    absent = missing_voice_caches(root)
    if absent:
        progress(
            f"note: {len(absent)} of {len(DELIVERABLES)} deliverables have no "
            "cached speech and will be re-synthesized, which can shift "
            "chapter boundaries slightly:"
        )
        for item in absent:
            progress(f"  {item.filename}")

    failures: list[str] = []
    for index, item in enumerate(wanted, start=1):
        target = item.path(root)
        if target.is_file() and not force:
            progress(f"[{index}/{len(wanted)}] {item.filename}: already built")
            continue
        progress(f"[{index}/{len(wanted)}] {item.filename}: rendering "
                 f"from lesson {item.lesson!r}")
        _lc.write_config("two_v_masterclass", {
            "action": "export_video",
            "lesson": item.lesson,
            "export_video": str(target),
            "size": size,
            "fps": fps,
            "compose_segments": item.compose,
            "segments_include": ",".join(item.segments),
        })
        result = subprocess.run(
            [sys.executable, "two_v_masterclass.py"],
            cwd=str(Path.cwd()),
        )
        if result.returncode != 0 or not target.is_file():
            failures.append(item.filename)
            progress(f"    FAILED: {item.filename}")
        else:
            progress(f"    done: {target}")

    if failures:
        progress("")
        progress(f"{len(failures)} of {len(wanted)} failed: "
                 f"{', '.join(failures)}")
        return 1
    progress("")
    progress(f"all {len(wanted)} deliverables built")
    return 0


def deliverables_menu() -> str:
    lines = [f"{len(DELIVERABLES)} deliverables:"]
    for item in DELIVERABLES:
        built = "built" if item.path().is_file() else "     "
        lines.append(f"  {built}  {item.lesson:<8} {item.filename}")
        lines.append(f"          {item.note}")
    absent = missing_voice_caches()
    lines.append("")
    lines.append(
        f"voice caches present for {len(DELIVERABLES) - len(absent)} of "
        f"{len(DELIVERABLES)}; the rest would re-synthesize"
    )
    return "\n".join(lines)


def validate_deliverables() -> None:
    """Every deliverable must name a real lesson and a unique file."""
    from .lesson_registry import LESSONS

    keys = [item.lesson for item in DELIVERABLES]
    assert len(set(keys)) == len(keys), "a lesson is listed twice"
    names = [item.filename for item in DELIVERABLES]
    assert len(set(names)) == len(names), "an output name is listed twice"
    for item in DELIVERABLES:
        assert item.lesson in LESSONS, f"unknown lesson {item.lesson!r}"
        assert item.filename.endswith(".mp4"), item.filename
        assert item.note, f"{item.filename} has no description"
    # Every lesson that produces a video should be listed, so nothing can
    # be rendered once and then quietly forgotten.
    unlisted = set(LESSONS) - set(keys)
    assert unlisted == {"2v"}, (
        f"lessons missing from the deliverable list: {sorted(unlisted)}"
    )
