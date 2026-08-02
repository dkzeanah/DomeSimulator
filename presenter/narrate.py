"""Generalized narration: per-shot neural speech, measured and mixed.

Reuses the proven pieces of two_v_demo.audio (executable discovery,
media probing) but works over arbitrary segment lists instead of the
fixed lesson chapters. The final track is built by decoding each stem to
PCM and placing it at its shot's start time — no ffmpeg filter
dependencies, deterministic output.
"""

from __future__ import annotations

import hashlib
import math
import subprocess
import wave
from pathlib import Path

import numpy as np

from two_v_demo.audio import (
    _aac_encoder,
    companion_ffprobe,
    media_duration,
    resolve_executable,
)

SAMPLE_RATE = 44100
SPEECH_DELAY = 0.45      # seconds into each shot before speech begins
TAIL_PAD = 0.75          # minimum silence after speech before the next shot


def _slug(text: str, voice: str, rate: str) -> str:
    digest = hashlib.sha1(
        f"{voice}|{rate}|{text}".encode("utf-8")).hexdigest()[:16]
    return digest


def synthesize_segment(text: str, path: Path, voice: str,
                       rate: str = "-3%", pitch: str = "-2Hz") -> None:
    import edge_tts
    communicate = edge_tts.Communicate(text, voice, rate=rate, pitch=pitch)
    if hasattr(communicate, "save_sync"):
        communicate.save_sync(str(path))
    else:                                    # pragma: no cover
        import asyncio
        asyncio.run(communicate.save(str(path)))


def prepare_narration(segments: list[str], cache_dir: Path, voice: str,
                      rate: str, ffmpeg: str | None = None,
                      ffprobe: str | None = None):
    """Synthesize (with caching) and measure every narration segment.

    Returns (clip paths, speech durations). Empty segments produce
    (None, 0.0) entries."""
    ffmpeg_exe = resolve_executable("ffmpeg", ffmpeg)
    ffprobe_exe = companion_ffprobe(ffmpeg_exe, ffprobe)
    cache_dir.mkdir(parents=True, exist_ok=True)
    clips: list[Path | None] = []
    durations: list[float] = []
    for index, text in enumerate(segments):
        text = " ".join(text.split())
        if not text:
            clips.append(None)
            durations.append(0.0)
            continue
        path = cache_dir / f"seg-{index:02d}-{_slug(text, voice, rate)}.mp3"
        if not path.is_file() or path.stat().st_size == 0:
            print(f"  voicing shot {index + 1}/{len(segments)} ...")
            synthesize_segment(text, path, voice, rate)
        clips.append(path)
        durations.append(media_duration(path, ffprobe_exe))
    return clips, durations


def stretch_durations(min_durations: list[float],
                      speech_durations: list[float]) -> list[float]:
    """A shot must last at least as long as its speech plus padding."""
    out = []
    for base, speech in zip(min_durations, speech_durations):
        need = (SPEECH_DELAY + speech + TAIL_PAD) if speech > 0 else 0.0
        out.append(max(base, need))
    return out


def _decode_pcm(path: Path, ffmpeg: str) -> bytes:
    result = subprocess.run(
        [ffmpeg, "-v", "error", "-i", str(path), "-f", "s16le",
         "-acodec", "pcm_s16le", "-ac", "1", "-ar", str(SAMPLE_RATE), "-"],
        stdout=subprocess.PIPE, check=True)
    return result.stdout


def build_track(clips: list[Path | None], starts: list[float],
                total: float, out_path: Path,
                ffmpeg: str | None = None) -> Path:
    ffmpeg_exe = resolve_executable("ffmpeg", ffmpeg)
    frames = int(math.ceil(total * SAMPLE_RATE)) + SAMPLE_RATE
    mix = np.zeros(frames, dtype=np.int32)
    for clip, start in zip(clips, starts):
        if clip is None:
            continue
        pcm = np.frombuffer(_decode_pcm(clip, ffmpeg_exe), dtype=np.int16)
        offset = int((start + SPEECH_DELAY) * SAMPLE_RATE)
        span = min(frames - offset, len(pcm))
        if span <= 0:
            continue
        mix[offset:offset + span] += pcm[:span].astype(np.int32)
    mix = np.clip(mix, -32768, 32767).astype(np.int16)
    wav_path = out_path.with_suffix(".wav")
    with wave.open(str(wav_path), "wb") as handle:
        handle.setnchannels(1)
        handle.setsampwidth(2)
        handle.setframerate(SAMPLE_RATE)
        handle.writeframes(mix.tobytes())
    subprocess.run(
        [ffmpeg_exe, "-y", "-v", "error", "-i", str(wav_path),
         *_aac_encoder(ffmpeg_exe), "-b:a", "160k", str(out_path)],
        check=True)
    wav_path.unlink(missing_ok=True)
    return out_path


def _timestamp(seconds: float) -> str:
    ms = int(round(seconds * 1000.0))
    hours, ms = divmod(ms, 3_600_000)
    minutes, ms = divmod(ms, 60_000)
    secs, ms = divmod(ms, 1000)
    return f"{hours:02d}:{minutes:02d}:{secs:02d},{ms:03d}"


def write_srt(path: Path, segments: list[str], starts: list[float],
              speech_durations: list[float]) -> Path:
    lines = []
    counter = 1
    for text, start, speech in zip(segments, starts, speech_durations):
        text = " ".join(text.split())
        if not text:
            continue
        begin = start + SPEECH_DELAY
        finish = begin + max(1.2, speech)
        lines.append(str(counter))
        lines.append(f"{_timestamp(begin)} --> {_timestamp(finish)}")
        lines.append(text)
        lines.append("")
        counter += 1
    path.write_text("\n".join(lines), encoding="utf-8")
    return path
