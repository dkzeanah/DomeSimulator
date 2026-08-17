#!/usr/bin/env python3
"""Add an offline narration track to the generated launcher trailer.

Uses Windows' built-in SAPI voices (System.Speech) via PowerShell -- fully
offline, nothing to install, and it does NOT touch any personal voice profile.
Each scene's caption line is synthesized, padded to that scene's exact duration
so it stays in sync, concatenated into one track, and muxed onto the silent
trailer. Non-overwriting: writes a *_narrated.mp4 beside the original.

Usage:
    py -3.12 add_narration.py <render_dir> [--voice "Microsoft David Desktop"]
"""
from __future__ import annotations

import argparse
import json
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path


def run(cmd: list[str]) -> None:
    p = subprocess.run(cmd, check=False)
    if p.returncode != 0:
        raise SystemExit(f"command failed ({p.returncode}): {cmd[0]}")


def ascii_speak(text: str) -> str:
    """Normalize unicode punctuation so PowerShell 5.1 parses the string."""
    repl = {"—": " - ", "–": "-", "‘": "'", "’": "'",
            "“": "'", "”": "'", "·": ",", "…": "...",
            "&": "and", '"': "'"}
    for k, v in repl.items():
        text = text.replace(k, v)
    return text.encode("ascii", "ignore").decode("ascii")


def synth_all(scenes, out_dir: Path, voice: str, rate: int) -> None:
    """Drive SAPI once via a generated PowerShell script."""
    out_dir.mkdir(parents=True, exist_ok=True)
    lines = [
        "Add-Type -AssemblyName System.Speech",
        "$s = New-Object System.Speech.Synthesis.SpeechSynthesizer",
        f'$s.SelectVoice("{voice}")',
        f"$s.Rate = {rate}",
        "$s.Volume = 100",
    ]
    for i, sc in enumerate(scenes, 1):
        wav = (out_dir / f"line-{i:02d}.wav").as_posix().replace("/", "\\")
        text = ascii_speak(sc["narration"])
        lines.append(f'$s.SetOutputToWaveFile("{wav}")')
        lines.append(f'$s.Speak("{text}")')
    lines.append("$s.Dispose()")
    with tempfile.NamedTemporaryFile("w", suffix=".ps1", delete=False,
                                     encoding="utf-8-sig") as fh:
        fh.write("\n".join(lines))
        ps1 = fh.name
    run(["powershell", "-NoProfile", "-ExecutionPolicy", "Bypass", "-File", ps1])
    Path(ps1).unlink(missing_ok=True)


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("render_dir", type=Path)
    ap.add_argument("--voice", default="Microsoft David Desktop")
    ap.add_argument("--rate", type=int, default=-1,
                    help="SAPI rate -10..10 (slightly slow reads best)")
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
    synth_all(scenes, voice_dir, args.voice, args.rate)

    # Pad each spoken line to its scene's exact duration, uniform PCM format.
    seg_paths = []
    for i, sc in enumerate(scenes, 1):
        src = voice_dir / f"line-{i:02d}.wav"
        seg = voice_dir / f"seg-{i:02d}.wav"
        dur = float(sc["duration_seconds"])
        run([ffmpeg, "-y", "-i", str(src), "-af", "aresample=24000,apad",
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
                      "voice": args.voice, "scenes": len(scenes)}, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
