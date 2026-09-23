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
import pathlib
import re
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
    Deliverable("series", "the-vance-network-mini-series.mp4",
                "The whole mini-series in one file: six vertical "
                "episodes, an arc where every cliffhanger is answered "
                "by the next episode's hook, and a finale that leaves "
                "one thread open. Same engine as the single episode, "
                "playing six directors back to back."),
    Deliverable("drama", "ep-dome-001-high-council.mp4",
                "The first micro-drama out of the narrative module: a "
                "60-second vertical episode staged inside the dome, "
                "with the blocking, the proximity rings, the rig "
                "actions and every camera move computed by the drama "
                "director from a script JSON. Rendered 1080x1920 -- the "
                "9:16 framing is the point, and a landscape render "
                "would discard it."),
    Deliverable("look", "dome-house-lookbook.mp4",
                "The interiors film: two furnished domes, a cast of "
                "eight built out of the same skeleton the lifting "
                "lesson uses, hair modelled as strands, a wardrobe "
                "lofted from the body's own cross-section, and the "
                "composer refusing a fitting pod because the shell has "
                "come down to meet it."),
    Deliverable("wedge", "eight-cuts-to-a-house.mp4",
                "The dome built straight from the tree: raw log sectors "
                "as structural members, forty independent pinwheel "
                "frames with no mitres anywhere, and gasketed seams "
                "instead of shared struts. Its math screens compute the "
                "trunk's board feet, pack 2x4s into the same sections "
                "honestly, cost the kerf, measure the joint and size "
                "the dome from the strut length the tree gives."),
    Deliverable("scratch", "dome-from-scratch-geometry-to-pixels.mp4",
                "From scratch, for somebody who has never written code: "
                "every calculation between one irrational number and a "
                "lit pixel. The shape (phi, subdivision, projection, two "
                "chord factors, a cut list) and then the picture (tubes, "
                "normals, the vertex buffer, the camera, the view and "
                "projection matrices, the divide by w, the viewport, the "
                "depth buffer, culling and the lighting sum), with 18 "
                "math screens deriving every figure on camera."),
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
    Deliverable("world_chatgpt",
                "ten-dome-builds-master-20260829-135242-chatgpt.mp4",
                "A unique ChatGPT master cut: ten real Dome Creator "
                "presets, Dome Forge and Assembly Line context, plus a "
                "per-build material breakdown, construction-event labor "
                "breakdown and modeled direct-sale price.",
                compose=False),
    Deliverable("why", "why-wedges-no-sawmill.mp4",
                "The combined cut. Where the method came from (the "
                "frankendome and its V brackets), what it is (borrowing "
                "the mechanism chapters and three math screens from "
                "`wedge` so the two films cannot disagree), and what it "
                "is worth -- from two timed cutting sessions that agree "
                "with a geometric prediction to 12%, a wedge valued two "
                "independent ways that land 1% apart, the store-bought "
                "overheads nobody counts, and a structural claim stated "
                "as a crossover diameter rather than a verdict.",
                compose=False),
    Deliverable("harvest", "two-trees-all-at-once.mp4",
                "Registered by the project agent repair step: the harvest lesson was in the registry without a deliverable entry.",
                compose=True),
    Deliverable("pine_value", "the-20-dollar-pine.mp4",
                "Registered by the project agent repair step: the pine_value lesson was in the registry without a deliverable entry.",
                compose=True),
    Deliverable("why_build", "why-build-this-way.mp4",
                "Registered by the project agent repair step: the why_build lesson was in the registry without a deliverable entry.",
                compose=True),
    Deliverable("all_domes", "all-domes-every-permutation.mp4",
                "The Dome Creator's whole catalogue drawn by the Creator's own "
                "renderer -- grain, glass, mirrors, foundations and the fit-out "
                "inside -- one dome built step by step in the tool's own "
                "construction order, then every menu swept one setting at a "
                "time, eight random draws, and the permutation count.",
                compose=True),
    Deliverable("pvtwo", "pvtwo-masterclass.mp4",
                "Generated by the project agent film recipe: The Twenty Dollar Pine, Part Two.",
                compose=True),
    Deliverable("byod", "bring-your-own-dome.mp4",
                "The annotated-transcript revision: animated iris, central services, "
                "movable partitions, wedge channels, staged growth, and a "
                "starter-first budget. Includes the shared contact outro.",
                compose=False),
    Deliverable("byod_deepseek", "attempt-v1-deepseek.mp4",
                "Bring Your Own Dome cut to the author's marked-up transcript: "
                "the assumptions lecture, the foundation-share section, the "
                "R-value payback figure and the utility-resale line are out; "
                "a pad built step by step, the deck materials, the pad "
                "catalogue, the line between the two people's money and the "
                "host's feature branches are in; and the iris was redrawn as a "
                "mechanism whose aperture is solved from the size it claims "
                "rather than drawn at a convenient radius.",
                compose=False),
    Deliverable("byod_snarky", "attempt-v1-byod_snarky.mp4",
                "Bring Your Own Dome in the social register: handheld camera "
                "that leans in when the character speaks, a little faster, "
                "vignetted, and the pink cyber jelly on thirteen cues, taking "
                "the tone of each passage it stands in. Same script, same "
                "numbers, same claims as the deepseek cut.",
                compose=False),
    Deliverable("byod_polished", "attempt-v1-byod_polished.mp4",
                "Bring Your Own Dome as a considered presentation: the camera "
                "drifts in slowly, the pace is generous, nothing is laid over "
                "the frame, and no character appears. The control for the "
                "snarky cut -- one script, two registers.",
                compose=False),
    Deliverable("dome_park", "dome-park-bring-your-own-home.mp4",
                "The Kickstarter cut. An RV park for domes: what a pad is, "
                "built one step at a time; what it costs a host and what it "
                "returns; the measured hinge -- a dome's foundation is 8% to "
                "63% of its build cost and on a pad the tenant never buys it; "
                "four ways to have a roof priced on one basis, and the month "
                "at which bringing your own home starts winning; one hardware "
                "set across three sizes; and a shell that comes off so the "
                "R-value can keep going up for as long as you own the house.",
                compose=True),
    Deliverable("seed_pitch", "stem-cell-dome-campaign.mp4",
                "The campaign cut for the stem-cell dome. A 277 sq ft tiny "
                "house that comes apart: a frame split out of the buyer's "
                "own trees with no mitre in it anywhere, a boat-hull shell "
                "priced off four named laminate systems at a supplier's "
                "published rates, a utility core that unbolts and moves to "
                "the next dome, and a pad that belongs to the landowner and "
                "is kept out of the dome's price. Ends on the three things "
                "it says against itself: not insulated as standard, eighty "
                "percent more wood than a shared-strut frame, and a price "
                "list that is an assumption.",
                compose=True),
    Deliverable("module_build", "stem-cell-utility-core-build.mp4",
                "The shop-floor cut: building one utility core, in the order "
                "you would actually build one. Fourteen steps, five stages, "
                "nine tools and twenty-three material lines, all generated "
                "from column_build.py's process sheet so the film cannot "
                "show a step the sheet does not have. Wet before dry, heavy "
                "before fragile, nothing buried -- and the two places you do "
                "not get a second chance: the crimp gauge and the pressure "
                "test. 7.2 hours practised, 17.2 for a first build, which is "
                "the number nobody quotes.",
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


def next_version_path(path: Path) -> Path:
    """A free filename beside ``path``, never ``path`` itself if it exists.

    Rendered output is append-only in this repository. ``foo.mp4`` becomes
    ``foo-v2.mp4``, then ``foo-v3.mp4``; an existing ``foo-v7.mp4`` is respected, so
    versions keep climbing rather than filling gaps and colliding with a file somebody
    already shared.

    The companion files a render writes -- narration, subtitles, the voice cache -- are
    derived from the returned stem, so a versioned render keeps its own set and does not
    tread on the previous one's.
    """
    if not path.exists():
        return path
    stem = path.stem
    # Strip a version suffix already on the name so -v2 does not become -v2-v2.
    match = re.match(r"^(.*)-v(\d+)$", stem)
    base = match.group(1) if match else stem
    # Climb above the highest version that has ever existed here, rather than
    # taking the first free number. Those are the same thing until somebody
    # deletes an old cut -- and then they are not: filling the gap gives a
    # brand new film the name of one that was already shared, which is
    # exactly what this function's docstring promises never to do. Found
    # after deleting a v2 and a v3 sent the next render back to v2.
    version = 2
    for sibling in path.parent.glob(f"{base}-v*{path.suffix}"):
        found = re.match(rf"^{re.escape(base)}-v(\d+)$", sibling.stem)
        if found:
            version = max(version, int(found.group(1)) + 1)
    while True:
        candidate = path.with_name(f"{base}-v{version}{path.suffix}")
        if not candidate.exists():
            return candidate
        version += 1


def _validate_versioning() -> None:
    """A new render may never take a name an old one already had."""
    import tempfile

    with tempfile.TemporaryDirectory() as folder:
        root = pathlib.Path(folder)
        base = root / "cut.mp4"
        assert next_version_path(base) == base, "a free name should be used"

        base.write_bytes(b"")
        assert next_version_path(base).name == "cut-v2.mp4"

        (root / "cut-v2.mp4").write_bytes(b"")
        (root / "cut-v3.mp4").write_bytes(b"")
        (root / "cut-v4.mp4").write_bytes(b"")
        assert next_version_path(base).name == "cut-v5.mp4"

        # The case this exists for: delete the middle versions and the next
        # render must still climb, not refill the gap with a different film.
        (root / "cut-v2.mp4").unlink()
        (root / "cut-v3.mp4").unlink()
        assert next_version_path(base).name == "cut-v5.mp4", (
            "deleting an old cut handed its name to a new one")

        # And deleting the highest does not hand that name out again either.
        (root / "cut-v4.mp4").unlink()
        assert next_version_path(base).name == "cut-v2.mp4"


def validate_deliverables() -> None:
    """Every deliverable must name a real lesson and a unique file."""
    from .lesson_registry import LESSONS

    _validate_versioning()

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
