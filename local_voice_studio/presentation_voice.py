"""Presentation narration clips: the films' voice, portable takes, and playback.

No local voice model or dataset is required. Network synthesis runs in a worker;
completed short sections can be played while later sections are still rendering.
"""
from __future__ import annotations

import asyncio
from collections import deque
from dataclasses import asdict, dataclass
from datetime import datetime, timezone
import json
import os
from pathlib import Path
import re
import shutil
import subprocess
import threading
import time
import uuid
import wave

from two_v_demo.audio import (
    DEFAULT_PITCH, DEFAULT_RATE, DEFAULT_VOICE, DEFAULT_VOLUME,
    _synthesize_one, _validate_prosody, resolve_executable,
)
from .project import safe_slug

DEFAULT_LIBRARY = Path(__file__).resolve().parents[1] / "voice_clips"
SAMPLE_RATE = 48000


class RenderCancelled(Exception):
    pass


@dataclass(frozen=True)
class VoiceSettings:
    voice: str = DEFAULT_VOICE
    rate: str = DEFAULT_RATE
    pitch: str = DEFAULT_PITCH
    volume: str = DEFAULT_VOLUME

    def validate(self):
        _validate_prosody(self.rate, self.pitch, self.volume)
        if not self.voice.strip():
            raise ValueError("Choose a neural voice.")
        for value, low, high in ((self.rate[:-1], -90, 200),
                                 (self.pitch[:-2], -100, 100),
                                 (self.volume[:-1], -100, 100)):
            if not low <= int(value) <= high:
                raise ValueError("Use rate -90 to +200%, pitch -100 to +100Hz, "
                                 "and voice volume -100 to +100%.")


def clean_transcript(text: str) -> str:
    """Remove caption timing lines/prefixes without removing ordinary numbers."""
    lines = text.replace("\r\n", "\n").splitlines()
    result = []
    stamp = r"(?:\d{1,2}:)?\d{1,2}:\d{2}(?:[.,]\d{1,3})?"
    for i, line in enumerate(lines):
        stripped = line.strip()
        if stripped == "WEBVTT" or "-->" in stripped:
            continue
        if stripped.isdigit() and i + 1 < len(lines) and "-->" in lines[i + 1]:
            continue
        stripped = re.sub(rf"^\[?{stamp}\]?\s*", "", stripped)
        if stripped:
            result.append(stripped)
    return "\n".join(result)


def split_text(text: str, limit: int = 450) -> list[str]:
    """Bound requests while preserving every word, preferring sentence endings."""
    remaining = " ".join(text.split())
    parts = []
    while len(remaining) > limit:
        window = remaining[:limit + 1]
        endings = list(re.finditer(r"[.!?][\"']?\s", window))
        cut = endings[-1].end() if endings else window.rfind(" ")
        if cut <= 0:
            cut = limit
        parts.append(remaining[:cut].strip())
        remaining = remaining[cut:].lstrip()
    if remaining:
        parts.append(remaining)
    return parts


def write_json(path: Path, data: dict):
    temporary = path.with_suffix(".tmp")
    temporary.write_text(json.dumps(data, indent=2, ensure_ascii=False), encoding="utf-8")
    temporary.replace(path)


def new_take(library: Path, title: str, text: str, settings: VoiceSettings,
             kind: str = "Neural") -> tuple[Path, dict]:
    library.mkdir(parents=True, exist_ok=True)
    now = datetime.now(timezone.utc)
    folder = library / (now.strftime("%Y%m%d-%H%M%S-") +
                        safe_slug(title or "clip")[:60] + "-" + uuid.uuid4().hex[:8])
    folder.mkdir()
    (folder / "script.txt").write_text(text, encoding="utf-8")
    receipt = {"title": title.strip() or "Untitled clip", "created": now.isoformat(),
               "kind": kind, "status": "recording" if kind == "Microphone" else "rendering",
               "settings": asdict(settings), "duration": 0.0, "wav": "", "mp3": ""}
    write_json(folder / "take.json", receipt)
    return folder, receipt


def list_takes(library: Path) -> list[tuple[Path, dict]]:
    takes = []
    for path in library.glob("*/take.json"):
        try:
            data = json.loads(path.read_text(encoding="utf-8"))
            if isinstance(data, dict):
                takes.append((path.parent, data))
        except (OSError, ValueError):
            continue
    return sorted(takes, key=lambda pair: pair[1].get("created", ""), reverse=True)


def take_audio(folder: Path, receipt: dict, format: str = "wav") -> Path:
    """Receipts must never point outside their take folder."""
    value = receipt.get(format)
    if not value:
        raise ValueError(f"This take has no completed {format.upper()} file.")
    path = (folder / value).resolve()
    if path.parent != folder.resolve() or not path.is_file():
        raise ValueError("The audio file is missing or outside its take folder.")
    return path


def export_copy(source: Path, destination: Path) -> Path:
    """Exclusive creation protects both old exports and the library's master."""
    destination.parent.mkdir(parents=True, exist_ok=True)
    with source.open("rb") as src, destination.open("xb") as dst:
        shutil.copyfileobj(src, dst)
    return destination


def ffmpeg_path() -> str:
    try:
        return resolve_executable("ffmpeg")
    except RuntimeError:
        try:
            import imageio_ffmpeg
            return imageio_ffmpeg.get_ffmpeg_exe()
        except ImportError as exc:
            raise RuntimeError("Audio conversion needs FFmpeg. Install the studio's "
                               "requirements-core.txt in the Python running this window.") from exc


def convert_audio(args: list[str], cancel: threading.Event):
    # communicate drains both pipes; short waits keep cancellation responsive.
    process = subprocess.Popen(args, stdout=subprocess.PIPE, stderr=subprocess.PIPE,
                               creationflags=getattr(subprocess, "CREATE_NO_WINDOW", 0))
    started = time.monotonic()
    try:
        while True:
            if cancel.is_set():
                raise RenderCancelled("Cancelled; the script and completed sections were kept.")
            if time.monotonic() - started > 600:
                raise RuntimeError("Audio conversion timed out.")
            try:
                _, stderr = process.communicate(timeout=0.15)
                break
            except subprocess.TimeoutExpired:
                continue
        if process.returncode:
            raise RuntimeError(stderr.decode("utf-8", errors="replace")[-1800:])
    finally:
        if process.poll() is None:
            process.kill()
            process.communicate()


async def _speak(text, path, settings, cancel, progress):
    task = asyncio.create_task(_synthesize_one(text, path, settings.voice,
        settings.rate, settings.pitch, settings.volume, progress))
    try:
        while not task.done():
            if cancel.is_set():
                raise RenderCancelled("Cancelled; the script and completed sections were kept.")
            await asyncio.wait({task}, timeout=0.1)
        await task
    finally:
        if not task.done():
            task.cancel()
            try:
                await task
            except asyncio.CancelledError:
                pass


def render_clip(library: Path, title: str, text: str, settings: VoiceSettings,
                cancel: threading.Event, emit=lambda kind, value: None) -> Path:
    settings.validate()
    parts = split_text(text)
    if not parts:
        raise ValueError("Paste or type something to read first.")
    # Fail before making a take if the provider/dependencies are missing.
    from two_v_demo.audio import _edge_tts_module
    _edge_tts_module()
    ffmpeg = ffmpeg_path()
    folder, receipt = new_take(library, title, text, settings)
    emit("take", folder)
    chunks = folder / "sections"
    chunks.mkdir()
    try:
        with wave.open(str(folder / "audio.partial.wav"), "wb") as track:
            track.setnchannels(1)
            track.setsampwidth(2)
            track.setframerate(SAMPLE_RATE)
            for index, part in enumerate(parts):
                if cancel.is_set():
                    raise RenderCancelled("Cancelled; the script and completed sections were kept.")
                emit("progress", (index / len(parts), f"Voicing section {index + 1} of {len(parts)}…"))
                mp3 = chunks / f"{index + 1:04d}.mp3"
                wav = mp3.with_suffix(".wav")
                asyncio.run(_speak(part, mp3, settings, cancel,
                                  lambda msg: emit("message", msg)))
                convert_audio([ffmpeg, "-nostdin", "-v", "error", "-n", "-i", str(mp3),
                               "-ac", "1", "-ar", str(SAMPLE_RATE), "-c:a", "pcm_s16le",
                               str(wav)], cancel)
                with wave.open(str(wav), "rb") as section:
                    while data := section.readframes(SAMPLE_RATE):
                        track.writeframesraw(data)
                emit("section", wav)
        if cancel.is_set():
            raise RenderCancelled("Cancelled; the script and completed sections were kept.")
        (folder / "audio.partial.wav").rename(folder / "audio.wav")
        receipt["wav"] = "audio.wav"
        with wave.open(str(folder / "audio.wav"), "rb") as wav:
            receipt["duration"] = wav.getnframes() / wav.getframerate()
        emit("progress", (0.98, "Saving MP3 and WAV…"))
        convert_audio([ffmpeg, "-nostdin", "-v", "error", "-n", "-i", str(folder / "audio.wav"),
                       "-codec:a", "libmp3lame", "-b:a", "192k",
                       str(folder / "audio.partial.mp3")], cancel)
        (folder / "audio.partial.mp3").rename(folder / "audio.mp3")
        receipt.update(status="complete", mp3="audio.mp3")
    except Exception as exc:
        receipt.update(status="cancelled" if isinstance(exc, RenderCancelled) else "failed",
                       error=str(exc))
        raise
    finally:
        write_json(folder / "take.json", receipt)
    return folder


class ClipPlayer:
    """A single output stream, with queued WAVs for live render audition.

    Uses bounded file reads (not a transcript-sized PCM array). Only this
    stream is stopped; other Studio playback isn't stopped globally.
    """
    def __init__(self):
        self.lock = threading.RLock()
        self.stream = None
        self.reader = None
        self.paths = deque()
        self.paused = False
        self.finished = True
        self.position = 0
        self.total = 0
        self.rate = SAMPLE_RATE
        self.volume = 1.0
        self.error = ""

    @property
    def seconds(self):
        return self.position / self.rate

    def start(self, rate=SAMPLE_RATE):
        self.stop()
        import sounddevice as sd
        self.rate = rate
        self.finished = False
        self.error = ""
        self.stream = sd.OutputStream(samplerate=rate, channels=1, dtype="int16",
                                      blocksize=2048, callback=self._callback)
        try:
            self.stream.start()
        except Exception:
            self.stop()
            raise

    def append(self, path: Path):
        with wave.open(str(path), "rb") as wav:
            if (wav.getframerate(), wav.getnchannels(), wav.getsampwidth()) != (self.rate, 1, 2):
                raise ValueError("Playback needs mono PCM16 WAV at the stream's sample rate.")
            count = wav.getnframes()
        with self.lock:
            self.paths.append(path)
            self.total += count

    def play(self, path: Path):
        with wave.open(str(path), "rb") as wav:
            rate = wav.getframerate()
        self.start(rate)
        self.append(path)
        self.finished = True

    def seek(self, path: Path, seconds: float):
        self.play(path)
        with self.lock:
            if self.reader is None:
                self.reader = wave.open(str(self.paths.popleft()), "rb")
            frame = max(0, min(int(seconds * self.rate), self.reader.getnframes()))
            self.reader.setpos(frame)
            self.position = frame

    def _callback(self, outdata, frames, _time, _status):
        import numpy as np
        import sounddevice as sd
        outdata.fill(0)
        with self.lock:
            if self.paused:
                return
            written = 0
            try:
                while written < frames:
                    if self.reader is None:
                        if not self.paths:
                            if self.finished:
                                raise sd.CallbackStop
                            break
                        self.reader = wave.open(str(self.paths.popleft()), "rb")
                    data = self.reader.readframes(frames - written)
                    if not data:
                        self.reader.close()
                        self.reader = None
                        continue
                    samples = np.frombuffer(data, dtype=np.int16)
                    count = len(samples)
                    outdata[written:written + count, 0] = (samples * self.volume).astype(np.int16)
                    self.position += count
                    written += count
            except sd.CallbackStop:
                raise
            except Exception as exc:
                self.error = str(exc)
                raise sd.CallbackAbort

    def stop(self):
        # Stop outside the lock: PortAudio may be waiting for its callback.
        if self.stream is not None:
            self.stream.abort()
            self.stream.close()
            self.stream = None
        with self.lock:
            if self.reader:
                self.reader.close()
                self.reader = None
            self.paths.clear()
            self.position = self.total = 0
            self.paused = False
            self.finished = True
