"""A cinematic cold open, shot in the Cabin World.

Hold on the log's end grain -- its growth rings and the eight rip cuts
through its heart -- then crane up and back until the dome stands on its
deck at sunset, and set the title. The world is
:mod:`two_v_demo.cabin_world` (every object from
:mod:`wedge_book.cover_scene`, the dome the raw-wedge solver's own), the
move is :func:`two_v_demo.shots.crane_reveal`, and the music is an original
cue from :mod:`two_v_demo.score`, timed to the move: a knock on the grain,
the build through the crane, the bloom as the dome lands.

This is also the worked example every Cabin World re-render starts from.
Output is append-only, like every render here:

    py -3.12 -m wedge_book.cold_open --stills     # four frames per cut
    py -3.12 -m wedge_book.cold_open              # both cuts and the release folder
    py -3.12 -m wedge_book.cold_open --release A.mp4 [B.mp4]   # folder for cuts on disk
"""

from __future__ import annotations

import argparse
import shutil
import subprocess
from dataclasses import dataclass
from pathlib import Path

import numpy as np
from PIL import Image

from two_v_demo import cabin_world as cw
from two_v_demo import score, shots
from two_v_demo.deliverables import next_version_path

from . import outline

FPS = 30
HOLD_GRAIN = 1.6    # s on the end grain, drifting in
CRANE = 6.4         # s rising to the reveal
HOLD_REVEAL = 3.0   # s on the dome, the title fading up
OUT_DIR = outline.ROOT / "deliverables" / "teasers"
STILLS_DIR = outline.ROOT / "book_wedge" / "cover" / "cold-open-stills"
STEM = "the-40-hour-cabin-cold-open"


@dataclass(frozen=True)
class Cut:
    name: str
    width: int
    height: int
    end_eye: tuple
    end_target: tuple
    end_fov: float
    start_back: float = 3.4   # opening distance from the end grain, in trunk radii


# The phone cut is narrower, so it ends farther back and on a taller lens.
CUTS = {
    "landscape": Cut("landscape", 1920, 1080, cw.HERO_EYE, (0.0, -0.6, 2.10), 46.0),
    "phone": Cut("phone", 1080, 1920, (1.00, -13.0, 3.10), (0.0, -0.6, 2.35), 58.0, 5.2),
}


def log_end() -> tuple[np.ndarray, np.ndarray]:
    """Where the split end of the log is, and which way it faces."""
    m = cw.landmarks()
    return m.log_end, m.log_axis


def total_seconds() -> float:
    return HOLD_GRAIN + CRANE + HOLD_REVEAL


def camera_path(cut: Cut):
    """The whole move as one function of time: hold, crane, hold."""
    grain, along = log_end()
    r = cw.landmarks().trunk_r
    near = grain - along * (r * cut.start_back) + np.array([0.0, 0.0, r * 0.25])
    closer = grain - along * (r * (cut.start_back - 0.5)) + np.array([0.0, 0.0, r * 0.22])
    crane = shots.crane_reveal(cut.end_target, closer, cut.end_eye,
                               fov_start=40.0, fov_end=cut.end_fov, look_start=grain)

    def at(t: float):
        if t < HOLD_GRAIN:
            k = t / HOLD_GRAIN
            return near + (closer - near) * k, grain, 40.0
        if t < HOLD_GRAIN + CRANE:
            return crane((t - HOLD_GRAIN) / CRANE)
        # A last slow drift so the held frame still breathes.
        eye, target, fov = crane(1.0)
        k = shots.ease((t - HOLD_GRAIN - CRANE) / HOLD_REVEAL)
        return eye + np.array([0.0, 0.35, 0.05]) * k, target, fov - 1.5 * k
    return at, total_seconds()


def title_lines():
    return [(outline.TITLE.upper(), "bold", 0.036), (outline.SUBTITLE.upper(), "heavy", 0.085),
            (outline.AUTHOR, "bold", 0.036)]


def frames(cut: Cut, studio: cw.Studio, times):
    at, _total = camera_path(cut)
    fade_from = HOLD_GRAIN + CRANE + 0.3
    for t in times:
        eye, target, fov = at(t)
        img = studio.frame(eye, target, fov)
        # In from black over the first half second, title over the held reveal.
        img = img * min(1.0, t / 0.5)
        img = cw.letter(img, title_lines(), shots.ease((t - fade_from) / 1.2),
                        top=0.12 if cut.height > cut.width else 0.10)
        yield t, img


def cue() -> np.ndarray:
    """The music, cut to the move."""
    return score.compose(total_seconds(), build=(HOLD_GRAIN, HOLD_GRAIN + CRANE),
                         hits=(HOLD_GRAIN + CRANE,), knocks=(0.05,))


def stills(cut: Cut) -> list[Path]:
    STILLS_DIR.mkdir(parents=True, exist_ok=True)
    marks = [0.8, HOLD_GRAIN + CRANE * 0.35, HOLD_GRAIN + CRANE * 0.7, total_seconds() - 0.05]
    studio = cw.Studio(cut.width, cut.height)
    paths = []
    for t, img in frames(cut, studio, marks):
        path = STILLS_DIR / f"{cut.name}-{t:05.2f}s.png"
        Image.fromarray((img * 255).astype(np.uint8)).save(path)
        paths.append(path)
    studio.release()
    return paths


def film(cut: Cut, music: Path, ffmpeg: str = "") -> Path:
    from two_v_demo.soundboard import bed_encoder

    ffmpeg = ffmpeg or shutil.which("ffmpeg") or "ffmpeg"
    stem = STEM + ("-vertical" if cut.name == "phone" else "")
    path = next_version_path(OUT_DIR / f"{stem}.mp4")
    path.parent.mkdir(parents=True, exist_ok=True)
    count = int(round(total_seconds() * FPS))
    studio = cw.Studio(cut.width, cut.height)
    encoder = subprocess.Popen(
        [ffmpeg, "-y", "-loglevel", "error", "-f", "rawvideo", "-pix_fmt", "rgb24",
         "-s", f"{cut.width}x{cut.height}", "-r", str(FPS), "-i", "-", "-i", str(music),
         "-c:v", "libx264", "-preset", "slow", "-crf", "17", "-pix_fmt", "yuv420p",
         *bed_encoder(ffmpeg), "-b:a", "192k", "-shortest",
         "-movflags", "+faststart", str(path)], stdin=subprocess.PIPE)
    for n, (_t, img) in enumerate(frames(cut, studio, (i / FPS for i in range(count)))):
        encoder.stdin.write((img * 255).astype(np.uint8).tobytes())
        if n % 30 == 0:
            print(f"  {cut.name}: frame {n}/{count}", flush=True)
    encoder.stdin.close()
    if encoder.wait():
        raise RuntimeError(f"ffmpeg failed on {path}")
    studio.release()
    return path


RELEASE_KEY = "cabin_cold_open"


def release_folder(landscape: Path, phone: Path | None) -> Path:
    """The release set, as :mod:`two_v_demo.release` lays one out.

    That builder reads a lesson's chapters; a cold open has none, so the
    three moments of the move stand in for them. Figures come from the
    book's own sources, not from this file.
    """
    from two_v_demo import release
    from wedge_book import systems

    folder = next_version_path(outline.ROOT / release.RELEASE_DIR / landscape.stem)
    folder.mkdir(parents=True)
    total = total_seconds()
    # grab_thumbnails steps 1.5 s into each mark.
    marks = [(-1.1, "the end grain", ""), (HOLD_GRAIN + CRANE * 0.45 - 1.5, "the crane", ""),
             (total - 1.6, "the reveal", "")]
    thumbs = release.grab_thumbnails(landscape, folder / "thumbnails", marks)
    m = cw.landmarks()
    clock = systems.build_clock()
    tags = " ".join(release.hashtags(RELEASE_KEY))
    hook = (f"One log, ripped into {m.splits} wedges with a chainsaw. "
            f"{clock['members']:.0f} of them make this dome.")
    lines = [
        f"# {outline.SUBTITLE} -- cold open", "",
        f"Landscape: `{landscape.name}`  ", f"Phone: `{phone.name if phone else '(none)'}`  ",
        f"Length: {total:.1f} s. Picture from the Cabin World (`wedge_book.cold_open`); every "
        "member is the raw-wedge solver's. Music: an original cue synthesised by "
        "`two_v_demo.score` -- no samples, no licence.", "",
        "## YouTube", "", f"**Title:** {outline.SUBTITLE}: a dome from one log", "",
        hook, "", f"From *{outline.TITLE}: {outline.SUBTITLE}* by {outline.AUTHOR}.", "",
        "0:00 the end grain  ", f"0:{int(HOLD_GRAIN):02d} the crane  ",
        f"0:{int(HOLD_GRAIN + CRANE):02d} the reveal", "", tags, "",
        "## Facebook", "", f"{hook} {outline.SUBTITLE}, by {outline.AUTHOR}.", "", tags, "",
        "## Instagram / TikTok / Shorts", "", hook, "", tags, "",
        "## Numbers used", "",
        f"* wedges per log section: `cabin_world.landmarks().splits` = {m.splits}",
        f"* members in the dome: `systems.build_clock()['members']` = {clock['members']:.0f}",
    ]
    (folder / "description.md").write_text("\n".join(lines) + "\n", encoding="utf-8")
    print(f"release: {folder} ({len(thumbs)} thumbnails)")
    return folder


def validate_cold_open() -> None:
    for cut in CUTS.values():
        at, total = camera_path(cut)
        grain, _ = log_end()
        eye, target, _ = at(0.0)
        assert np.allclose(target, grain), "the film must open on the end grain"
        assert np.linalg.norm(eye - grain) < 1.0, "the opening frame is close on the log"
        eye, target, fov = at(total)
        assert eye[2] > 3.0 and np.allclose(target, cut.end_target), "it ends craned up on the dome"
        # The path is continuous across the joins between hold, crane and hold.
        for join in (HOLD_GRAIN, HOLD_GRAIN + CRANE):
            a, b = at(join - 1e-4), at(join + 1e-4)
            assert np.linalg.norm(a[0] - b[0]) < 1e-2 and abs(a[2] - b[2]) < 0.1, join


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--stills", action="store_true")
    parser.add_argument("--cut", choices=["both", *CUTS], default="both")
    parser.add_argument("--release", nargs="+", metavar="MP4")
    args = parser.parse_args(argv)
    if args.release:
        cuts = [Path(p) for p in args.release]
        release_folder(cuts[0], cuts[1] if len(cuts) > 1 else None)
        return 0
    validate_cold_open()
    chosen = list(CUTS.values()) if args.cut == "both" else [CUTS[args.cut]]
    if args.stills:
        for cut in chosen:
            for p in stills(cut):
                print(p)
        return 0
    music = score.write_wav(cue(), next_version_path(OUT_DIR / f"{STEM}-score.wav"))
    print(f"wrote {music}")
    made = {cut.name: film(cut, music) for cut in chosen}
    for path in made.values():
        print(f"wrote {path}")
    if "landscape" in made:
        release_folder(made["landscape"], made.get("phone"))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
