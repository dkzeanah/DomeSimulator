"""Natural neural narration and FFmpeg audio-track assembly.

The default provider is Microsoft Edge's online neural TTS service through the
``edge-tts`` Python package.  It needs an internet connection while generating
audio, but no API key.  Generated chapter clips are cached beside the video.
"""

from __future__ import annotations

import asyncio
import hashlib
import re
import shutil
import subprocess
import tempfile
import wave
from dataclasses import dataclass
from pathlib import Path
from typing import Callable, Sequence

from .lessons import CHAPTERS


DEFAULT_VOICE = "en-US-AndrewMultilingualNeural"
DEFAULT_RATE = "-3%"
DEFAULT_PITCH = "-2Hz"
DEFAULT_VOLUME = "+0%"
SPEECH_DELAY = 0.55
TAIL_PADDING = 0.85


@dataclass(frozen=True)
class NarrationPlan:
    voice: str
    rate: str
    pitch: str
    volume: str
    clip_paths: tuple[Path, ...]
    speech_durations: tuple[float, ...]
    chapter_durations: tuple[float, ...]
    chapter_starts: tuple[float, ...]
    total_duration: float
    track_path: Path


def spoken_chapter_text(index: int) -> str:
    """Return fluent prose for one chapter, without reading equations aloud."""
    chapter = CHAPTERS[index]
    return f"{chapter.promise}\n\n{' '.join(chapter.narration)}"


def voice_cache_slug(
    voice: str,
    rate: str,
    pitch: str,
    volume: str,
) -> str:
    """Key cached stems by voice settings and the complete spoken script."""
    payload = "\n".join(
        [voice, rate, pitch, volume]
        + [spoken_chapter_text(index) for index in range(len(CHAPTERS))]
    )
    digest = hashlib.sha256(payload.encode("utf-8")).hexdigest()[:10]
    readable = re.sub(
        r"[^A-Za-z0-9]+", "-", f"{voice}-{rate}-{pitch}-{volume}"
    ).strip("-")
    return f"{readable}-{digest}"


def resolve_executable(name: str, explicit: str | None = None) -> str:
    """Resolve FFmpeg tools with a helpful error for Windows users."""
    if explicit:
        candidate = Path(explicit)
        if candidate.is_file():
            return str(candidate)
        resolved = shutil.which(explicit)
        if resolved:
            return resolved
        raise RuntimeError(f"{name} executable not found: {explicit}")
    resolved = shutil.which(name)
    if resolved:
        return resolved
    raise RuntimeError(
        f"{name} was not found on PATH. Pass --{name} with its full path."
    )


def companion_ffprobe(ffmpeg: str, explicit: str | None = None) -> str:
    if explicit:
        return resolve_executable("ffprobe", explicit)
    sibling = Path(ffmpeg).with_name(
        "ffprobe.exe" if Path(ffmpeg).suffix.lower() == ".exe" else "ffprobe"
    )
    if sibling.is_file():
        return str(sibling)
    return resolve_executable("ffprobe")


def media_duration(path: Path, ffprobe: str) -> float:
    command = [
        ffprobe, "-v", "error", "-show_entries", "format=duration",
        "-of", "default=noprint_wrappers=1:nokey=1", str(path),
    ]
    result = subprocess.run(
        command, check=True, capture_output=True, text=True
    )
    try:
        duration = float(result.stdout.strip())
    except ValueError as exc:
        raise RuntimeError(f"Could not read audio duration for {path}") from exc
    if duration <= 0.0:
        raise RuntimeError(f"Generated audio is empty: {path}")
    return duration


def _validate_prosody(rate: str, pitch: str, volume: str) -> None:
    if not re.fullmatch(r"[+-]\d+%", rate):
        raise ValueError("voice rate must look like -3% or +10%")
    if not re.fullmatch(r"[+-]\d+Hz", pitch):
        raise ValueError("voice pitch must look like -2Hz or +5Hz")
    if not re.fullmatch(r"[+-]\d+%", volume):
        raise ValueError("voice volume must look like +0% or -5%")


def _edge_tts_module():
    try:
        import edge_tts
    except ModuleNotFoundError as exc:
        raise RuntimeError(
            "Natural narration needs edge-tts. Install it with: "
            "py -3.12 -m pip install edge-tts"
        ) from exc
    return edge_tts


async def _synthesize_one(
    text: str,
    path: Path,
    voice: str,
    rate: str,
    pitch: str,
    volume: str,
) -> None:
    edge_tts = _edge_tts_module()
    communicator = edge_tts.Communicate(
        text,
        voice=voice,
        rate=rate,
        pitch=pitch,
        volume=volume,
        boundary="SentenceBoundary",
    )
    await communicator.save(str(path))


def synthesize_preview(
    path: Path,
    voice: str = DEFAULT_VOICE,
    rate: str = DEFAULT_RATE,
    pitch: str = DEFAULT_PITCH,
    volume: str = DEFAULT_VOLUME,
) -> Path:
    """Generate a short sample so the presenter can audition a voice."""
    _validate_prosody(rate, pitch, volume)
    path.parent.mkdir(parents=True, exist_ok=True)
    preview = (
        "Welcome to the two V geodesic dome masterclass. "
        "We will begin with the golden ratio, reconstruct the icosahedron, "
        "and finish with a practical, verified cut list."
    )
    asyncio.run(_synthesize_one(preview, path, voice, rate, pitch, volume))
    return path


def list_neural_voices(locale: str = "en-US") -> list[dict]:
    """Return currently available Edge neural voices for a locale."""
    edge_tts = _edge_tts_module()
    voices = asyncio.run(edge_tts.list_voices())
    return sorted(
        (voice for voice in voices if voice.get("Locale") == locale),
        key=lambda voice: voice.get("ShortName", ""),
    )


def _chapter_starts(durations: Sequence[float]) -> tuple[float, ...]:
    starts: list[float] = []
    cursor = 0.0
    for duration in durations:
        starts.append(cursor)
        cursor += duration
    return tuple(starts)


def _build_mixed_track(
    clip_paths: Sequence[Path],
    starts: Sequence[float],
    total_duration: float,
    output_path: Path,
    ffmpeg: str,
    progress: Callable[[str], None] = print,
) -> None:
    """Place every chapter clip on one normalized stereo teaching track."""
    filter_probe = subprocess.run(
        [ffmpeg, "-filters"],
        capture_output=True,
        text=True,
        check=False,
    )
    available_filters = filter_probe.stdout + filter_probe.stderr
    if (
        not re.search(r"\badelay\b", available_filters)
        or not re.search(r"\bloudnorm\b", available_filters)
    ):
        progress(
            "FFmpeg compatibility mode: assembling timed PCM audio without "
            "adelay/loudnorm."
        )
        _build_compatible_track(
            clip_paths,
            starts,
            total_duration,
            output_path,
            ffmpeg,
        )
        return
    command = [
        ffmpeg, "-y",
        "-f", "lavfi", "-t", f"{total_duration:.6f}",
        "-i", "anullsrc=r=48000:cl=stereo",
    ]
    for clip_path in clip_paths:
        command.extend(["-i", str(clip_path)])
    filters = [
        f"[0:a]atrim=duration={total_duration:.6f},"
        "asetpts=N/SR/TB,aformat=sample_fmts=fltp:channel_layouts=stereo[base]"
    ]
    labels = ["[base]"]
    for input_index, start in enumerate(starts, 1):
        delay_ms = int(round((start + SPEECH_DELAY) * 1000.0))
        label = f"voice{input_index}"
        filters.append(
            f"[{input_index}:a]aresample=48000,"
            "aformat=sample_fmts=fltp:channel_layouts=stereo,"
            f"adelay={delay_ms}|{delay_ms}[{label}]"
        )
        labels.append(f"[{label}]")
    filters.append(
        "".join(labels)
        + f"amix=inputs={len(labels)}:duration=first:"
        "dropout_transition=0:normalize=0,"
        "highpass=f=70,lowpass=f=14500,"
        "loudnorm=I=-16:TP=-1.5:LRA=11[narration]"
    )
    command.extend([
        "-filter_complex", ";".join(filters),
        "-map", "[narration]",
        "-c:a", "aac", "-b:a", "192k",
        str(output_path),
    ])
    try:
        subprocess.run(command, check=True)
    except subprocess.CalledProcessError:
        progress(
            "FFmpeg filter mixer failed; retrying with the compatibility mixer."
        )
        try:
            output_path.unlink()
        except OSError:
            pass
        _build_compatible_track(
            clip_paths,
            starts,
            total_duration,
            output_path,
            ffmpeg,
        )


def _write_silence(wav: wave.Wave_write, frames: int) -> None:
    bytes_per_frame = 4  # signed PCM-16 stereo
    block_frames = 16_384
    silent_block = b"\x00" * (block_frames * bytes_per_frame)
    remaining = max(0, frames)
    while remaining:
        count = min(block_frames, remaining)
        wav.writeframesraw(silent_block[: count * bytes_per_frame])
        remaining -= count


def _aac_encoder(ffmpeg: str) -> tuple[str, ...]:
    probe = subprocess.run(
        [ffmpeg, "-encoders"],
        capture_output=True,
        text=True,
        check=False,
    )
    encoders = probe.stdout + probe.stderr
    if re.search(r"\blibfdk_aac\b", encoders):
        return ("-c:a", "libfdk_aac")
    if re.search(r"\blibvo_aacenc\b", encoders):
        return ("-c:a", "libvo_aacenc")
    # The native AAC encoder in older FFmpeg builds was marked experimental.
    return ("-c:a", "aac", "-strict", "-2")


def _build_compatible_track(
    clip_paths: Sequence[Path],
    starts: Sequence[float],
    total_duration: float,
    output_path: Path,
    ffmpeg: str,
) -> None:
    """Build a synchronized AAC track using only basic FFmpeg codecs.

    FFmpeg builds from before 2015 may not contain ``adelay`` or ``loudnorm``.
    The lesson chapters never overlap, so we can decode each clip to canonical
    PCM and write the required silence between clips without filter support.
    """
    if len(clip_paths) != len(starts):
        raise ValueError("Narration clip/start counts do not match")
    output_path.parent.mkdir(parents=True, exist_ok=True)
    temporary_parent = output_path.parent.resolve()
    with tempfile.TemporaryDirectory(
        prefix=f".{output_path.stem}-pcm-",
        dir=str(temporary_parent),
    ) as temporary_text:
        temporary = Path(temporary_text)
        decoded_paths: list[Path] = []
        for index, clip_path in enumerate(clip_paths, 1):
            decoded = temporary / f"clip_{index:02d}.wav"
            subprocess.run(
                [
                    ffmpeg,
                    "-y",
                    "-i",
                    str(clip_path),
                    "-vn",
                    "-ac",
                    "2",
                    "-ar",
                    "48000",
                    "-c:a",
                    "pcm_s16le",
                    str(decoded),
                ],
                check=True,
                capture_output=True,
            )
            decoded_paths.append(decoded)

        mixed_pcm = temporary / "narration.wav"
        current_frame = 0
        final_frame = int(round(total_duration * 48_000))
        with wave.open(str(mixed_pcm), "wb") as destination:
            destination.setnchannels(2)
            destination.setsampwidth(2)
            destination.setframerate(48_000)
            for decoded, start in zip(decoded_paths, starts):
                target_frame = int(round((start + SPEECH_DELAY) * 48_000))
                if target_frame < current_frame:
                    raise ValueError("Narration clips overlap in compatibility mode")
                _write_silence(destination, target_frame - current_frame)
                current_frame = target_frame
                with wave.open(str(decoded), "rb") as source:
                    if (
                        source.getnchannels() != 2
                        or source.getsampwidth() != 2
                        or source.getframerate() != 48_000
                    ):
                        raise RuntimeError(
                            f"FFmpeg produced an unexpected PCM format: {decoded}"
                        )
                    while True:
                        block = source.readframes(16_384)
                        if not block:
                            break
                        destination.writeframesraw(block)
                        current_frame += len(block) // 4
            if current_frame > final_frame:
                raise ValueError("Narration exceeds the planned track duration")
            _write_silence(destination, final_frame - current_frame)

        encode_command = [
            ffmpeg,
            "-y",
            "-i",
            str(mixed_pcm),
            *_aac_encoder(ffmpeg),
            "-b:a",
            "192k",
            str(output_path),
        ]
        subprocess.run(encode_command, check=True)


def synthesize_narration(
    output_directory: Path,
    track_path: Path,
    ffmpeg: str,
    ffprobe: str,
    voice: str = DEFAULT_VOICE,
    rate: str = DEFAULT_RATE,
    pitch: str = DEFAULT_PITCH,
    volume: str = DEFAULT_VOLUME,
    progress: Callable[[str], None] = print,
) -> NarrationPlan:
    """Generate cached chapter clips and a chapter-synchronized AAC track.

    Visual chapter durations grow to fit measured speech duration. Speech is
    never time-compressed to force it into the original silent-video timing.
    """
    _validate_prosody(rate, pitch, volume)
    _edge_tts_module()
    output_directory.mkdir(parents=True, exist_ok=True)
    clip_paths: list[Path] = []
    speech_durations: list[float] = []
    for index, chapter in enumerate(CHAPTERS):
        clip_path = output_directory / f"chapter_{chapter.number}.mp3"
        clip_paths.append(clip_path)
        if clip_path.exists() and clip_path.stat().st_size > 1024:
            progress(f"voice {chapter.number}/{len(CHAPTERS):02d}: cached")
        else:
            progress(
                f"voice {chapter.number}/{len(CHAPTERS):02d}: "
                f"{chapter.title}"
            )
            asyncio.run(_synthesize_one(
                spoken_chapter_text(index),
                clip_path,
                voice,
                rate,
                pitch,
                volume,
            ))
        speech_durations.append(media_duration(clip_path, ffprobe))

    chapter_durations = tuple(
        max(
            chapter.duration,
            SPEECH_DELAY + speech_duration + TAIL_PADDING,
        )
        for chapter, speech_duration in zip(CHAPTERS, speech_durations)
    )
    starts = _chapter_starts(chapter_durations)
    total_duration = sum(chapter_durations)
    track_path.parent.mkdir(parents=True, exist_ok=True)
    _build_mixed_track(
        clip_paths,
        starts,
        total_duration,
        track_path,
        ffmpeg,
        progress,
    )
    return NarrationPlan(
        voice=voice,
        rate=rate,
        pitch=pitch,
        volume=volume,
        clip_paths=tuple(clip_paths),
        speech_durations=tuple(speech_durations),
        chapter_durations=chapter_durations,
        chapter_starts=starts,
        total_duration=total_duration,
        track_path=track_path,
    )
