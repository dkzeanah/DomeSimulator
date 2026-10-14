#!/usr/bin/env python3
"""Create a uniquely versioned slideshow video from rendered slide PNGs.

The script never overwrites. Each invocation creates a timestamp-plus-random-suffix
subdirectory, asks FFmpeg to refuse overwrite with -n, writes an SRT sidecar, and
optionally muxes a mastered narration track.
"""

from __future__ import annotations

import argparse
import json
import shutil
import subprocess
import sys
import uuid
from datetime import datetime
from pathlib import Path


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--manifest", required=True, type=Path)
    parser.add_argument("--slides-dir", required=True, type=Path)
    parser.add_argument("--out-dir", required=True, type=Path)
    parser.add_argument("--audio", type=Path, help="Optional mastered narration WAV/MP3/M4A")
    parser.add_argument("--ffmpeg", default="ffmpeg", help="FFmpeg executable or absolute path")
    return parser.parse_args()


def assert_file(path: Path, label: str) -> Path:
    resolved = path.expanduser().resolve()
    if not resolved.is_file():
        raise FileNotFoundError(f"{label} not found: {resolved}")
    return resolved


def assert_dir(path: Path, label: str) -> Path:
    resolved = path.expanduser().resolve()
    if not resolved.is_dir():
        raise FileNotFoundError(f"{label} not found: {resolved}")
    return resolved


def unique_run_dir(parent: Path) -> Path:
    parent.mkdir(parents=True, exist_ok=True)
    stamp = datetime.now().strftime("%Y%m%d_%H%M%S_%f")[:-3]
    suffix = uuid.uuid4().hex[:6]
    target = parent / f"video_render_{stamp}_{suffix}"
    target.mkdir(exist_ok=False)
    return target


def resolve_slide(slides_dir: Path, slide_number: int) -> Path:
    candidates = [
        slides_dir / f"slide-{slide_number}.png",
        slides_dir / f"slide-{slide_number:02d}.png",
        slides_dir / f"slide-{slide_number:03d}.png",
    ]
    for candidate in candidates:
        if candidate.is_file():
            return candidate.resolve()
    raise FileNotFoundError(
        f"No slide image found for slide {slide_number}. Tried: "
        + ", ".join(str(item) for item in candidates)
    )


def ffconcat_quote(path: Path) -> str:
    return str(path).replace("\\", "/").replace("'", "'\\''")


def srt_time(seconds: float) -> str:
    millis = round(seconds * 1000)
    hours, millis = divmod(millis, 3_600_000)
    minutes, millis = divmod(millis, 60_000)
    secs, millis = divmod(millis, 1000)
    return f"{hours:02d}:{minutes:02d}:{secs:02d},{millis:03d}"


def write_text_new(path: Path, content: str) -> None:
    with path.open("x", encoding="utf-8", newline="\n") as handle:
        handle.write(content)


def run_ffmpeg(command: list[str]) -> None:
    completed = subprocess.run(command, check=False)
    if completed.returncode != 0:
        raise RuntimeError(f"FFmpeg failed with exit code {completed.returncode}")


def main() -> int:
    args = parse_args()
    manifest_path = assert_file(args.manifest, "Manifest")
    slides_dir = assert_dir(args.slides_dir, "Slides directory")
    audio_path = assert_file(args.audio, "Audio") if args.audio else None

    ffmpeg = shutil.which(args.ffmpeg) or (
        str(Path(args.ffmpeg).expanduser().resolve()) if Path(args.ffmpeg).is_file() else None
    )
    if not ffmpeg:
        raise FileNotFoundError(
            "FFmpeg was not found. Install it or pass --ffmpeg with the executable path."
        )

    with manifest_path.open("r", encoding="utf-8") as handle:
        manifest = json.load(handle)
    scenes = manifest.get("scenes")
    if not isinstance(scenes, list) or not scenes:
        raise ValueError("Manifest must contain a non-empty 'scenes' list")

    run_dir = unique_run_dir(args.out_dir.expanduser().resolve())
    concat_path = run_dir / "slides.ffconcat"
    captions_path = run_dir / "captions.srt"
    silent_video = run_dir / "slideshow_silent.mp4"
    final_video = run_dir / ("slideshow_with_narration.mp4" if audio_path else "slideshow_final_silent.mp4")
    receipt_path = run_dir / "render_receipt.json"

    concat_lines = ["ffconcat version 1.0"]
    caption_blocks: list[str] = []
    elapsed = 0.0
    last_slide: Path | None = None

    for index, scene in enumerate(scenes, start=1):
        slide_number = int(scene["slide_number"])
        duration = float(scene["duration_seconds"])
        if duration <= 0:
            raise ValueError(f"Scene {scene.get('id', index)} has a non-positive duration")
        slide = resolve_slide(slides_dir, slide_number)
        concat_lines.extend([f"file '{ffconcat_quote(slide)}'", f"duration {duration:.3f}"])
        last_slide = slide
        caption_blocks.append(
            f"{index}\n{srt_time(elapsed)} --> {srt_time(elapsed + duration)}\n"
            f"{str(scene.get('narration', '')).strip()}\n"
        )
        elapsed += duration

    if last_slide is None:
        raise ValueError("No slide images were resolved")
    concat_lines.append(f"file '{ffconcat_quote(last_slide)}'")
    write_text_new(concat_path, "\n".join(concat_lines) + "\n")
    write_text_new(captions_path, "\n".join(caption_blocks))

    resolution = manifest.get("resolution", [1920, 1080])
    width, height = int(resolution[0]), int(resolution[1])
    fps = int(manifest.get("frame_rate", 30))
    video_filter = (
        f"scale={width}:{height}:force_original_aspect_ratio=decrease,"
        f"pad={width}:{height}:(ow-iw)/2:(oh-ih)/2:color=white,format=yuv420p"
    )
    run_ffmpeg([
        ffmpeg, "-n", "-f", "concat", "-safe", "0", "-i", str(concat_path),
        "-vf", video_filter, "-r", str(fps), "-c:v", "libx264", "-preset", "medium",
        "-crf", "18", "-movflags", "+faststart", str(silent_video),
    ])

    if audio_path:
        run_ffmpeg([
            ffmpeg, "-n", "-i", str(silent_video), "-i", str(audio_path),
            "-map", "0:v:0", "-map", "1:a:0", "-c:v", "copy", "-c:a", "aac",
            "-b:a", "192k", "-shortest", "-movflags", "+faststart", str(final_video),
        ])
    else:
        silent_video.rename(final_video)

    receipt = {
        "run_directory": str(run_dir),
        "manifest": str(manifest_path),
        "slides_directory": str(slides_dir),
        "audio": str(audio_path) if audio_path else None,
        "scene_count": len(scenes),
        "timeline_seconds": elapsed,
        "captions": str(captions_path),
        "video": str(final_video),
        "overwrite_policy": "unique directory + exclusive writes + ffmpeg -n",
    }
    write_text_new(receipt_path, json.dumps(receipt, indent=2) + "\n")
    print(json.dumps(receipt, indent=2))
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except Exception as error:
        print(f"ERROR: {error}", file=sys.stderr)
        raise SystemExit(1)
