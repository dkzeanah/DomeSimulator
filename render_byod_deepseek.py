"""Staged, append-only audio / render / mux / release for the annotated BYOD cut.

The film is :mod:`two_v_demo.lesson_byod_deepseek`. Its output lands under
``deliverables/byod-deepseek/`` -- a folder of its own, so the cut being worked
on in ``deliverables/byod/`` is never touched -- and every finished cut is
named ``attempt-v<N>-deepseek.mp4`` with N chosen by looking at what is already
on disk. There is no flag to overwrite one.

Run one stage at a time and watch the clock; the printout at the end of each
stage is the time it took.

    py -3.12 render_byod_deepseek.py check
    py -3.12 render_byod_deepseek.py audio
    py -3.12 render_byod_deepseek.py render --encoder h264_nvenc --preset p5
    py -3.12 render_byod_deepseek.py mux

or all of it, plus the phone cut and the release folder, in one command:

    py -3.12 render_byod_deepseek.py all --both --release
"""
from __future__ import annotations

import argparse
from dataclasses import replace
import json
import math
from pathlib import Path
import re
import shutil
import subprocess
import sys
import time

from render_bring_your_own_dome import (
    companions,
    digest,
    executables,
    load_plan,
    new_directory,
    probe,
    render_stage,
    save_json,
    stream_duration,
    verify_video,
    write_plan,
)

ROOT = Path(__file__).resolve().parent
STAGES = ("check", "script", "shots", "audio", "render", "mux", "all", "smoke",
          "portrait", "release")

DOUBLE_STILL_CHAPTERS = (
    "title", "padding", "storage", "center", "rooms", "pad_build", "decks",
    "iris", "rotation", "channels", "panel_lip", "veins", "floor", "catalog",
    "line", "host_design", "foundation", "move", "growth", "layers", "solar",
    "shared", "network", "rewards", "close",
)
"""Chapters worth two stills rather than one.

A chapter whose subject moves needs its start and its end looked at: an iris
that opens, a pad that builds, a dome that lands. A chapter that holds one
picture is fine with one still. This is a review cost, not a render cost."""


def lesson():
    from two_v_demo.lesson_byod_deepseek import BYOD_DEEPSEEK_LESSON
    return BYOD_DEEPSEEK_LESSON


def attempt_path(root: Path, version: int, *, portrait: bool = False,
                 stem: str = "deepseek") -> Path:
    """``attempt-v1-deepseek.mp4``, or ``-vertical`` for the phone cut.

    A refused overwrite rather than an incremented one: the caller decides the
    number, and if that number is taken the answer is to pick another, not to
    quietly write over an hour of somebody's render. The phone cut carries the
    landscape cut's number, because the two are one attempt.
    """
    suffix = "-vertical.mp4" if portrait else ".mp4"
    path = root / f"attempt-v{version}-{stem}{suffix}"
    if path.exists():
        raise FileExistsError(
            f"{path.name} is already here. Finished cuts are never replaced: "
            f"pick another --version, or move that one aside deliberately.")
    return path


def real_cuts(root: Path, stem: str = "deepseek") -> list[Path]:
    """Finished cuts, excluding anything an integration test wrote.

    The smoke test runs the whole pipeline at a size that finishes in seconds,
    and it names its output the same way a real run does. Counting those would
    make the film's actual first cut land as v2, so the test's own folder is
    stepped over here rather than in the test -- one place, not two.
    """
    return [path for path in root.rglob(f"attempt-v*-{stem}*.mp4")
            if not any(part.startswith("smoke-test") for part in path.parts)]


def next_version(root: Path, stem: str = "deepseek") -> int:
    """The first attempt number not already spoken for on disk."""
    return max((version_of(path) for path in real_cuts(root, stem)),
               default=0) + 1


# ----------------------------------------------------------------------
# Review stills
# ----------------------------------------------------------------------

def shots_stage(args, film) -> Path:
    """A still, or two, from every chapter, then paginated contact sheets."""
    from two_v_demo.app import MasterclassApp
    from PIL import Image, ImageDraw

    portrait = args.orientation == "portrait"
    folder = new_directory(args.output, "review-portrait" if portrait else "review")
    app = MasterclassApp(size=args.size, hidden=True, lesson=film)
    shots: list[Path] = []
    try:
        cursor = 0.0
        for index, chapter in enumerate(film.chapters):
            moments = (.12, .90) if chapter.slug in DOUBLE_STILL_CHAPTERS else (.85,)
            for progress in moments:
                app.timeline = cursor + chapter.duration * progress
                app.chapter_index, app.chapter_progress = index, progress
                app.reset_camera()
                app.render(present=False)
                target = folder / (f"{chapter.number}-{chapter.slug}"
                                   f"-{int(progress * 100):02d}.png")
                app.save_screenshot(target)
                shots.append(target)
            cursor += chapter.duration
    finally:
        app.pygame.quit()

    columns = 1 if portrait else 2
    cell_w, cell_h = (540, 960) if portrait else (640, 386)
    per_sheet = 8 if portrait else 12
    for start in range(0, len(shots), per_sheet):
        page = shots[start:start + per_sheet]
        rows = math.ceil(len(page) / columns)
        sheet = Image.new("RGB", (cell_w * columns, rows * cell_h), "#0a1420")
        draw = ImageDraw.Draw(sheet)
        for offset, path in enumerate(page):
            x = (offset % columns) * cell_w
            y = (offset // columns) * cell_h
            with Image.open(path) as image:
                image.thumbnail((cell_w, cell_h - 26))
                sheet.paste(image, (x, y + 24))
            draw.text((x + 8, y + 5), path.stem, fill="white")
        sheet.save(folder / f"contact-sheet-{start // per_sheet + 1:02d}.jpg")
    companions(folder, film)
    print(f"REVIEW STILLS: {folder}  ({len(shots)} frames)", flush=True)
    return folder


# ----------------------------------------------------------------------
# Mux, with the narration plan the release folder reads
# ----------------------------------------------------------------------

def mux_stage(args, manifest_path=None, destination=None, film=None,
              portrait=False, version=None) -> Path:
    """Put the measured narration under the verified picture.

    A hand-rolled mux rather than the sibling driver's, for two reasons: the
    finished file is named for the attempt it belongs to, and the narration
    plan has to be written beside it, because that is where
    :func:`two_v_demo.release.chapter_marks` reads a cut's real timings from.
    """
    from two_v_demo.audio import SPEECH_DELAY, NarrationPlan

    ffmpeg, ffprobe = executables(args)
    manifest_path = manifest_path or args.render_manifest or newest_render(args)
    manifest = json.loads(Path(manifest_path).read_text(encoding="utf-8"))
    plan_path = Path(manifest["plan"])
    if digest(plan_path) != manifest["plan_sha256"]:
        raise ValueError("The timing plan changed after rendering. Re-render before muxing.")
    payload = load_plan(plan_path, film, ffprobe)
    if payload["byod_speech_sha256"] != manifest["speech_sha256"]:
        raise ValueError("Audio and video refer to different scripts")
    picture = Path(manifest["picture"])
    if digest(picture) != manifest["picture_sha256"]:
        raise ValueError("The picture changed after verification")
    verify_video(picture, ffprobe, manifest["seconds"], manifest["fps"])
    audio = Path(args.audio).resolve() if args.audio else Path(payload["track"])
    if args.audio:
        track = next(s for s in probe(audio, ffprobe)["streams"]
                     if s["codec_type"] == "audio")
        if abs(stream_duration(track) - manifest["seconds"]) > 0.15:
            raise ValueError("Replacement audio must already follow this chapter "
                             "timing and total duration")
        print("Using replacement audio: its chapter alignment is your responsibility.")

    folder = destination or new_directory(args.output, "cut")
    path = attempt_path(args.output,
                        version or next_version(args.output, args.stem),
                        portrait=portrait, stem=args.stem)
    command = [ffmpeg, "-n", "-i", str(picture), "-i", str(audio),
               "-map", "0:v:0", "-map", "1:a:0", "-c:v", "copy",
               "-c:a", "aac", "-b:a", "192k", "-movflags", "+faststart",
               str(path)]
    print("MUX: " + subprocess.list2cmdline(command), flush=True)
    subprocess.run(command, check=True)
    result = verify_video(path, ffprobe, manifest["seconds"], manifest["fps"],
                          audio=True)
    save_json(folder / "verification.json", result)
    for name in ("narration.md", "captions.srt", "storyboard.json",
                 "model-audit.txt"):
        source = plan_path.parent / name
        if source.is_file():
            shutil.copyfile(source, folder / name)

    # The captions also go beside the cut, which is where the release folder
    # looks for them: it picks up `<cut stem>.srt` if it is there. A caption
    # file left behind in a staging folder is a caption file nobody publishes,
    # and subtitles are the one part of a release that is not regenerable.
    captions = plan_path.parent / "captions.srt"
    if captions.is_file():
        shutil.copyfile(captions, path.with_suffix(".srt"))
    save_json(folder / "provenance.json", {
        "render_manifest": str(Path(manifest_path).resolve()),
        "audio": str(audio), "audio_sha256": digest(audio),
        "cut": str(path.resolve()), "smoke_test": manifest.get("smoke_test", False),
    })

    # The plan the release folder times its thumbnails and its chapter list
    # from, in the exporter's own format, written beside the finished cut.
    if film is not None:
        from two_v_demo.app import write_narration_plan
        track_path = Path(payload["track"])
        restored = NarrationPlan(
            payload["voice_profile"], "as rendered", "-2Hz", "+0%",
            tuple(Path(p) for p in payload["clips"]),
            tuple(payload["speech_durations"]),
            tuple(payload["chapter_durations"]),
            tuple(payload["chapter_starts"]),
            sum(payload["chapter_durations"]), track_path)
        write_narration_plan(path.with_name(f"{path.stem}-narration-plan.json"),
                             restored, payload["speech_delay"],
                             chapters=film.chapters)

    print(f"\nFINAL MP4: {path}\nVerified picture frames and audio duration.",
          flush=True)
    return path


def newest_render(args) -> Path:
    from render_bring_your_own_dome import newest
    return newest(args.output / "video", "render-*/render.json")


# ----------------------------------------------------------------------
# The phone cut
# ----------------------------------------------------------------------

def portrait_stage(args, film):
    """The same film in a phone frame.

    Rendered from the same narration plan, so both cuts say the same words at
    the same moments and the speech service is asked once. Its own output
    folder and its own verification; nothing about the landscape cut changes.
    """
    from two_v_demo.frame import size_for
    if film.frame_fit == "off":
        raise ValueError("This lesson opted out of re-framing; it is landscape only.")
    # The phone cut belongs to the landscape cut it was made from, so it
    # carries that cut's number rather than claiming one of its own.
    cut = Path(args.cut) if args.cut else newest_cut(args.output, args.stem)
    version = version_of(cut)
    inner = argparse.Namespace(**vars(args))
    inner.size = size_for("portrait")
    inner.orientation = "portrait"
    plan = args.plan or newest_plan(args)
    print(f"Phone cut at {inner.size[0]}x{inner.size[1]} for {cut.name}, "
          f"from {Path(plan).name}", flush=True)
    folder = new_directory(args.output / "portrait", "render")
    manifest = render_stage(inner, film, plan, folder)
    return mux_stage(inner, manifest, folder, film, portrait=True,
                     version=version)


def newest_plan(args) -> Path:
    from render_bring_your_own_dome import newest
    return newest(args.output / "audio", "take-*/plan.json")


# ----------------------------------------------------------------------
# The release folder
# ----------------------------------------------------------------------

def release_stage(args, film):
    """Thumbnails, captions and platform copy, from the cut that just finished.

    Called by hand because this film is rendered by a staged pipeline rather
    than the exporter, which is the one thing CLAUDE.md asks a pipeline to do
    for itself. It is never allowed to fail the render that came before it.
    """
    from two_v_demo.release import build_release, newest_version

    cut = args.cut or newest_cut(args.output, args.stem)
    cut = newest_version(Path(cut))
    portrait = None
    for candidate in (cut.with_name(f"{cut.stem}-vertical{cut.suffix}"),
                      cut.with_name(f"{cut.stem}-portrait{cut.suffix}")):
        if candidate.is_file():
            portrait = candidate
    result = build_release(film.key, video=cut, portrait=portrait)
    print(result.summary(), flush=True)
    if portrait is None:
        print("No phone cut beside this one: run the portrait stage, then this "
              "again, and the release folder will pick it up.", flush=True)
    return result.folder


def newest_cut(root: Path, stem: str = "deepseek") -> Path:
    """The newest finished attempt under this film's output folder."""
    cuts = [p for p in real_cuts(root, stem)
            if "-vertical" not in p.stem and p.suffix == ".mp4"]
    if not cuts:
        raise FileNotFoundError(f"No finished cut under {root}. Run mux first.")
    return max(cuts, key=lambda p: (version_of(p), p.stat().st_mtime))


def version_of(path: Path) -> int:
    match = re.search(r"attempt-v(\d+)-", path.name)
    return int(match.group(1)) if match else 0


# ----------------------------------------------------------------------
# The integration check
# ----------------------------------------------------------------------

def smoke_stage(args, film):
    """A short silent render, end to end, at a size that finishes in minutes."""
    from two_v_demo.audio import NarrationPlan
    slugs = {"title", "pad_build", "decks", "iris", "veins", "catalog", "line",
             "host_design", "close"}
    chapters = tuple(replace(c, duration=1.2)
                     for c in film.chapters if c.slug in slugs)
    film = replace(film, chapters=chapters)
    args.size, args.fps, args.preset, args.encoder = (960, 540), 6, "ultrafast", "libx264"
    args.orientation = "landscape"
    folder = new_directory(args.output, "smoke-test")
    # Everything the mux writes stays inside the smoke folder. Pointing it at
    # the film's own output would put an eleven-second silent cut under the
    # name attempt-v1-deepseek.mp4 and claim the number a real render wants.
    args.output = folder
    ffmpeg, _ = executables(args)
    track = folder / "TEST-SILENCE.m4a"
    duration = sum(c.duration for c in chapters)
    subprocess.run([ffmpeg, "-n", "-f", "lavfi", "-i", "anullsrc=r=48000:cl=stereo",
                    "-t", str(duration), "-c:a", "aac", str(track)], check=True)
    plan = NarrationPlan("TEST SILENCE", "test", "test", "test", (),
                         (0.0,) * len(chapters),
                         tuple(c.duration for c in chapters),
                         tuple(i * 1.2 for i in range(len(chapters))),
                         duration, track)
    path = folder / "plan.json"
    write_plan(path, plan, film, smoke=True)
    manifest = render_stage(args, film, path, folder)
    mux_stage(args, manifest, new_directory(folder, "mux"), film)
    print("SMOKE TEST PASSED (test silence, not narration).", flush=True)


# ----------------------------------------------------------------------
# Command line
# ----------------------------------------------------------------------

def parse_orientation(args):
    from two_v_demo.frame import size_for
    args.size = size_for(args.orientation)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("stage", choices=STAGES)
    parser.add_argument("--output", type=Path,
                        default=ROOT / "deliverables" / "byod-deepseek")
    parser.add_argument("--orientation", choices=("landscape", "portrait"),
                        default="landscape")
    parser.add_argument("--both", action="store_true",
                        help="with 'all': render the phone cut too")
    parser.add_argument("--release", action="store_true",
                        help="with 'all': build the release folder afterwards")
    parser.add_argument("--fps", type=int, default=30)
    parser.add_argument("--encoder", choices=("libx264", "h264_nvenc"),
                        default="libx264")
    parser.add_argument("--preset", default="medium",
                        help="x264: medium/fast; NVENC: p1-p7")
    parser.add_argument("--voice", default="en-US-AndrewMultilingualNeural")
    parser.add_argument("--rate", help="TTS rate, e.g. --rate=+2%%")
    parser.add_argument("--clips-dir", type=Path,
                        help="Use your recordings: NN-slug.wav/mp3/m4a/flac")
    parser.add_argument("--plan", type=Path, help="Explicit audio plan for render")
    parser.add_argument("--render-manifest", type=Path,
                        help="Explicit render.json for mux")
    parser.add_argument("--audio", type=Path,
                        help="Mux replacement track already aligned to this timeline")
    parser.add_argument("--cut", type=Path,
                        help="Explicit cut: names the attempt the phone cut "
                             "belongs to, and the cut the release folder is "
                             "built from")
    parser.add_argument("--stem", default="deepseek",
                        help="Name stem for finished cuts: attempt-vN-<stem>.mp4")
    parser.add_argument("--version", type=int,
                        help="Attempt number for the finished file. Defaults "
                             "to the first number not already on disk; an "
                             "existing file is never replaced.")
    parser.add_argument("--chapters",
                        help="Comma-separated slugs, for a short preview; "
                             "use a separate --output")
    parser.add_argument("--ffmpeg")
    parser.add_argument("--ffprobe")
    args = parser.parse_args()
    if not 1 <= args.fps <= 60:
        parser.error("fps must be between 1 and 60")
    args.output = args.output.resolve()
    parse_orientation(args)

    film = lesson()
    if args.chapters:
        selected = args.chapters.split(",")
        available = {c.slug: c for c in film.chapters}
        if len(selected) != len(set(selected)) or set(selected) - available.keys():
            parser.error("Chapter slugs must be unique and match the storyboard")
        film = replace(film, chapters=tuple(available[s] for s in selected))

    started = time.perf_counter()
    try:
        if args.stage == "check":
            film.selftest()
            executables(args)
            print(f"PASS: {len(film.chapters)} chapters; arithmetic, scene "
                  f"geometry, FFmpeg and FFprobe.", flush=True)
        elif args.stage == "script":
            directory = new_directory(args.output, "script")
            companions(directory, film)
            print(directory)
        elif args.stage == "shots":
            shots_stage(args, film)
        elif args.stage == "audio":
            from render_bring_your_own_dome import audio_stage
            audio_stage(args, film)
        elif args.stage == "render":
            from render_bring_your_own_dome import newest
            plan = args.plan or newest(args.output / "audio", "take-*/plan.json")
            render_stage(args, film, plan)
        elif args.stage == "mux":
            mux_stage(args, film=film, version=args.version)
        elif args.stage == "portrait":
            portrait_stage(args, film)
        elif args.stage == "release":
            release_stage(args, film)
        elif args.stage == "smoke":
            smoke_stage(args, film)
        else:
            from render_bring_your_own_dome import audio_stage
            plan = audio_stage(args, film)
            manifest = render_stage(args, film, plan)
            mux_stage(args, manifest, film=film, version=args.version)
            if args.both:
                portrait_stage(args, film)
            if args.release:
                release_stage(args, film)
    except (OSError, ValueError, RuntimeError, KeyError,
            subprocess.CalledProcessError) as exc:
        print(f"FAILED: {exc}", file=sys.stderr)
        return 1
    finally:
        print(f"Stage elapsed: {time.perf_counter() - started:.1f} seconds",
              flush=True)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
