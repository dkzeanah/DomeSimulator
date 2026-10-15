#!/usr/bin/env python3
"""Add a neural narration track to the generated launcher trailer.

Uses the SAME engine and voice as the project's presentation/2V video exports:
edge-tts with `en-US-AndrewMultilingualNeural` (see two_v_demo/audio.py's
DEFAULT_VOICE and presenter/narrate.py). Each scene's caption line is
synthesized, padded to that scene's exact duration so it stays in sync,
concatenated into one track, and muxed onto the silent trailer.

Non-overwriting for the mp4 output name pattern; writes *_narrated.mp4 beside
the original. Requires network access (edge-tts streams from Microsoft's
neural endpoint), exactly like the real exporters.

Usage:
    py -3.12 add_narration.py <render_dir>
        [--voice en-US-AndrewMultilingualNeural] [--rate +0%] [--pitch +0Hz]
"""
from __future__ import annotations

import argparse
import asyncio
import json
import shutil
import subprocess
from pathlib import Path

DEFAULT_VOICE = "en-US-AndrewMultilingualNeural"  # matches two_v_demo/audio.py


def run(cmd: list[str]) -> None:
    p = subprocess.run(cmd, check=False)
    if p.returncode != 0:
        raise SystemExit(f"command failed ({p.returncode}): {cmd[0]}")


async def synth_all(scenes, out_dir: Path, voice: str, rate: str,
                    pitch: str) -> None:
    import edge_tts
    out_dir.mkdir(parents=True, exist_ok=True)
    for i, sc in enumerate(scenes, 1):
        dst = out_dir / f"line-{i:02d}.mp3"
        communicate = edge_tts.Communicate(sc["narration"], voice,
                                            rate=rate, pitch=pitch)
        await communicate.save(str(dst))


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("render_dir", type=Path)
    ap.add_argument("--voice", default=DEFAULT_VOICE)
    ap.add_argument("--rate", default="+0%", help="edge-tts rate, e.g. -5%%")
    ap.add_argument("--pitch", default="+0Hz")
    args = ap.parse_args()

    ffmpeg = shutil.which("ffmpeg")
    if not ffmpeg:
        raise SystemExit("ffmpeg not found on PATH")

    run_dir = args.render_dir.resolve()
    manifest = json.loads((run_dir / "video_manifest.json").read_text("utf-8"))
    scenes = manifest["scenes"]
    video = run_dir / "dome_simulator_trailer.mp4"
    if not video.is_file():
        raise SystemExit(f"trailer video not found: {video}")

    voice_dir = run_dir / "narration"
    asyncio.run(synth_all(scenes, voice_dir, args.voice, args.rate, args.pitch))

    # Pad each spoken line to its scene's exact duration, uniform PCM format.
    seg_paths = []
    for i, sc in enumerate(scenes, 1):
        src = voice_dir / f"line-{i:02d}.mp3"
        seg = voice_dir / f"seg-{i:02d}.wav"
        dur = float(sc["duration_seconds"])
        run([ffmpeg, "-y", "-i", str(src), "-af", "aresample=48000,apad",
             "-ac", "1", "-t", f"{dur:.3f}", "-c:a", "pcm_s16le", str(seg)])
        seg_paths.append(seg)

    concat_list = voice_dir / "segments.txt"
    concat_list.write_text(
        "".join(f"file '{p.as_posix()}'\n" for p in seg_paths),
        encoding="utf-8", newline="\n")
    full = run_dir / "narration_full.wav"
    run([ffmpeg, "-y", "-f", "concat", "-safe", "0", "-i", str(concat_list),
         "-c", "copy", str(full)])

    out = run_dir / "dome_simulator_trailer_narrated.mp4"
    out.unlink(missing_ok=True)
    run([ffmpeg, "-y", "-i", str(video), "-i", str(full), "-map", "0:v:0",
         "-map", "1:a:0", "-c:v", "copy", "-c:a", "aac", "-strict", "-2",
         "-ar", "48000", "-b:a", "128k", "-shortest", "-movflags",
         "+faststart", str(out)])

    print(json.dumps({"narrated_video": str(out), "audio_track": str(full),
                      "voice": args.voice, "rate": args.rate,
                      "scenes": len(scenes)}, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
