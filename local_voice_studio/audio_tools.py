"""Dependency-light WAV metrics, conversion, segmentation, and profile building."""

from __future__ import annotations

import hashlib
import math
import shutil
import struct
import subprocess
import wave
from dataclasses import dataclass
from pathlib import Path
from typing import Iterable

from .models import ClipRecord, VoiceProfile, utc_now
from .project import VoiceProject, safe_slug, sha256_file


CANONICAL_RATE = 24_000
CANONICAL_CHANNELS = 1
CANONICAL_WIDTH = 2


@dataclass(frozen=True)
class WavMetrics:
    duration_s: float
    peak_dbfs: float
    rms_dbfs: float
    clipped_pct: float
    silence_pct: float
    sample_rate: int
    channels: int
    sample_width: int


def _dbfs(amplitude: float) -> float:
    if amplitude <= 1e-12:
        return -120.0
    return 20.0 * math.log10(amplitude)


def read_pcm16_mono(path: Path) -> tuple[int, list[int]]:
    with wave.open(str(path), "rb") as wav:
        channels = wav.getnchannels()
        sample_width = wav.getsampwidth()
        sample_rate = wav.getframerate()
        frames = wav.readframes(wav.getnframes())
    if sample_width != 2:
        raise ValueError("Only PCM-16 WAV is supported by the lightweight analyzer")
    samples = list(struct.unpack(f"<{len(frames) // 2}h", frames))
    if channels > 1:
        mono: list[int] = []
        for index in range(0, len(samples), channels):
            mono.append(round(sum(samples[index:index + channels]) / channels))
        samples = mono
    return sample_rate, samples


def inspect_wav(path: Path, silence_dbfs: float = -42.0) -> WavMetrics:
    with wave.open(str(path), "rb") as wav:
        channels = wav.getnchannels()
        sample_width = wav.getsampwidth()
        sample_rate = wav.getframerate()
        frame_count = wav.getnframes()
    rate, samples = read_pcm16_mono(path)
    if rate != sample_rate:
        raise AssertionError("WAV sample-rate read mismatch")
    if not samples:
        return WavMetrics(0.0, -120.0, -120.0, 0.0, 100.0,
                          sample_rate, channels, sample_width)
    full_scale = 32768.0
    peak = max(abs(value) for value in samples) / full_scale
    mean_square = sum(float(value) ** 2 for value in samples) / len(samples)
    rms = math.sqrt(mean_square) / full_scale
    clipped = sum(1 for value in samples if abs(value) >= 32760)
    window = max(1, int(sample_rate * 0.03))
    silent_windows = 0
    window_count = 0
    for start in range(0, len(samples), window):
        block = samples[start:start + window]
        if not block:
            continue
        block_rms = math.sqrt(sum(float(v) ** 2 for v in block) / len(block))
        block_db = _dbfs(block_rms / full_scale)
        silent_windows += int(block_db < silence_dbfs)
        window_count += 1
    return WavMetrics(
        duration_s=frame_count / sample_rate if sample_rate else 0.0,
        peak_dbfs=_dbfs(peak),
        rms_dbfs=_dbfs(rms),
        clipped_pct=clipped / len(samples) * 100.0,
        silence_pct=silent_windows / max(1, window_count) * 100.0,
        sample_rate=sample_rate,
        channels=channels,
        sample_width=sample_width,
    )


def find_ffmpeg(explicit: str | None = None) -> str:
    if explicit:
        path = Path(explicit)
        if path.is_file():
            return str(path)
    result = shutil.which(explicit or "ffmpeg")
    if result:
        return result
    raise RuntimeError("FFmpeg was not found. Add it to PATH or configure its path.")


def normalize_audio(source: Path, destination: Path, ffmpeg: str | None = None) -> Path:
    destination.parent.mkdir(parents=True, exist_ok=True)
    executable = find_ffmpeg(ffmpeg)
    command = [
        executable, "-y", "-i", str(source),
        "-vn", "-ac", "1", "-ar", str(CANONICAL_RATE),
        "-c:a", "pcm_s16le", str(destination),
    ]
    subprocess.run(command, check=True, capture_output=True)
    return destination


def write_pcm16_mono(path: Path, sample_rate: int, samples: Iterable[int]) -> None:
    values = [max(-32768, min(32767, int(value))) for value in samples]
    path.parent.mkdir(parents=True, exist_ok=True)
    with wave.open(str(path), "wb") as wav:
        wav.setnchannels(1)
        wav.setsampwidth(2)
        wav.setframerate(sample_rate)
        wav.writeframes(struct.pack(f"<{len(values)}h", *values))


def energy_segments(
    path: Path,
    threshold_dbfs: float = -40.0,
    min_seconds: float = 1.5,
    max_seconds: float = 15.0,
    merge_gap_seconds: float = 0.28,
    padding_seconds: float = 0.12,
) -> list[tuple[int, int]]:
    """Return sample ranges around voiced regions for a canonical WAV."""
    sample_rate, samples = read_pcm16_mono(path)
    if not samples:
        return []
    window = max(1, int(sample_rate * 0.03))
    voiced: list[bool] = []
    for start in range(0, len(samples), window):
        block = samples[start:start + window]
        rms = math.sqrt(sum(float(value) ** 2 for value in block) / max(1, len(block)))
        voiced.append(_dbfs(rms / 32768.0) >= threshold_dbfs)
    runs: list[tuple[int, int]] = []
    start_index: int | None = None
    for index, is_voiced in enumerate(voiced + [False]):
        if is_voiced and start_index is None:
            start_index = index
        elif not is_voiced and start_index is not None:
            runs.append((start_index * window, min(index * window, len(samples))))
            start_index = None
    merge_gap = int(sample_rate * merge_gap_seconds)
    merged: list[list[int]] = []
    for start, end in runs:
        if merged and start - merged[-1][1] <= merge_gap:
            merged[-1][1] = end
        else:
            merged.append([start, end])
    padding = int(sample_rate * padding_seconds)
    minimum = int(sample_rate * min_seconds)
    maximum = int(sample_rate * max_seconds)
    segments: list[tuple[int, int]] = []
    for start, end in merged:
        start = max(0, start - padding)
        end = min(len(samples), end + padding)
        if end - start < minimum:
            continue
        cursor = start
        while end - cursor > maximum:
            segments.append((cursor, cursor + maximum))
            cursor += maximum
        if end - cursor >= minimum:
            segments.append((cursor, end))
    return segments


def create_clip_record(
    project: VoiceProject,
    wav_path: Path,
    clip_id: str,
    text: str = "",
    source_id: str = "",
) -> ClipRecord:
    metrics = inspect_wav(wav_path)
    return ClipRecord(
        clip_id=clip_id,
        audio_file=project.relative(wav_path),
        text=text.strip(),
        duration_s=metrics.duration_s,
        peak_dbfs=metrics.peak_dbfs,
        rms_dbfs=metrics.rms_dbfs,
        clipped_pct=metrics.clipped_pct,
        silence_pct=metrics.silence_pct,
        sample_rate=metrics.sample_rate,
        channels=metrics.channels,
        sha256=sha256_file(wav_path),
        source_id=source_id,
    )


def build_voice_profile(
    project: VoiceProject,
    name: str,
    clips: list[ClipRecord],
    target_seconds: float = 16.0,
) -> VoiceProfile:
    if not project.consented:
        raise PermissionError("A valid ownership statement is required")
    accepted = [clip for clip in clips if clip.accepted and not clip.quality_issues]
    if not accepted:
        raise ValueError("No accepted, quality-clean clips are available")
    accepted.sort(
        key=lambda clip: (
            clip.clipped_pct,
            abs(clip.rms_dbfs + 22.0),
            clip.silence_pct,
        )
    )
    selected: list[ClipRecord] = []
    duration = 0.0
    for clip in accepted:
        selected.append(clip)
        duration += clip.duration_s
        if duration >= target_seconds:
            break
    profile_index = len(project.profiles()) + 1
    profile_id = f"{safe_slug(name)}-v{profile_index:03d}"
    directory = project.root / "profiles" / profile_id
    if directory.exists():
        raise FileExistsError(directory)
    directory.mkdir(parents=True)
    reference_path = directory / "reference.wav"
    all_samples: list[int] = []
    silence = [0] * int(CANONICAL_RATE * 0.18)
    transcript_parts: list[str] = []
    for clip in selected:
        rate, samples = read_pcm16_mono(project.resolve_relative(clip.audio_file))
        if rate != CANONICAL_RATE:
            raise ValueError(f"Clip {clip.clip_id} is not 24 kHz")
        if all_samples:
            all_samples.extend(silence)
        all_samples.extend(samples)
        transcript_parts.append(clip.text.strip())
    write_pcm16_mono(reference_path, CANONICAL_RATE, all_samples)
    reference_text = " ".join(part for part in transcript_parts if part)
    (directory / "reference.txt").write_text(reference_text + "\n", encoding="utf-8")
    profile = VoiceProfile(
        schema=1,
        profile_id=profile_id,
        name=name.strip(),
        created_at=utc_now(),
        reference_wav=project.relative(reference_path),
        reference_text=reference_text,
        source_clip_ids=[clip.clip_id for clip in selected],
        sha256=sha256_file(reference_path),
        duration_s=len(all_samples) / CANONICAL_RATE,
    )
    # Directory was created above to assemble the immutable profile. Write the
    # manifest here rather than calling save_profile(), which owns directory
    # creation for externally assembled profiles.
    manifest_path = directory / "profile.json"
    import json
    manifest_path.write_text(
        json.dumps(profile.to_dict(), indent=2) + "\n", encoding="utf-8"
    )
    project.audit(
        "profile_locked",
        {"profile_id": profile.profile_id, "sha256": profile.sha256},
    )
    return profile
