"""Shared float audio plumbing for the rap production tools.

The rest of Local Voice Studio deliberately sticks to the standard
library (see ``audio_tools``) so the dataset workflow runs anywhere. Beat
tracking, pitch correction and time-warping cannot be done that way, so
this module is the single place where numpy / scipy / librosa /
soundfile get imported, and the single place that knows how to turn any
file on disk into a float array.

Everything here works in **mono float32 at a music sample rate** (44.1
kHz by default), which is a different world from the 24 kHz PCM-16 the
voice dataset uses. ``to_project_rate`` bridges the two.
"""

from __future__ import annotations

import shutil
import subprocess
import tempfile
import wave
from dataclasses import dataclass
from pathlib import Path

MUSIC_RATE = 44_100
PROJECT_RATE = 24_000

# Formats libsndfile reads directly. Anything else goes through ffmpeg.
_NATIVE_SUFFIXES = {".wav", ".flac", ".ogg", ".aiff", ".aif", ".au", ".w64"}


@dataclass(frozen=True)
class DependencyStatus:
    ready: bool
    detail: str
    missing: tuple[str, ...] = ()


def dependency_status() -> DependencyStatus:
    """What the production tools need, and what is actually installed."""
    missing: list[str] = []
    detail: list[str] = []
    for module, label in (("numpy", "numpy"), ("scipy", "scipy"),
                          ("librosa", "librosa"), ("soundfile", "soundfile")):
        try:
            mod = __import__(module)
            detail.append(f"{label} {getattr(mod, '__version__', '?')}")
        except Exception:                                   # noqa: BLE001
            missing.append(label)
    if missing:
        return DependencyStatus(
            False,
            "Missing: " + ", ".join(missing) + ". Install the core "
            "requirements (local_voice_studio/requirements-core.txt).",
            tuple(missing),
        )
    return DependencyStatus(True, ", ".join(detail))


def require() -> None:
    status = dependency_status()
    if not status.ready:
        raise RuntimeError(status.detail)


def _ffmpeg() -> str:
    """Prefer the project's newest-ffmpeg resolver; fall back to PATH."""
    try:
        from two_v_demo.audio import resolve_executable
        return resolve_executable("ffmpeg")
    except Exception:                                       # noqa: BLE001
        found = shutil.which("ffmpeg")
        if not found:
            raise RuntimeError(
                "FFmpeg was not found. It is needed to read compressed "
                "audio such as .mp3 or .m4a."
            )
        return found


def load(path: Path, sample_rate: int = MUSIC_RATE):
    """Read any audio file as mono float32 at ``sample_rate``.

    Returns ``(samples, sample_rate)``. Compressed formats are decoded
    through ffmpeg into a temporary WAV rather than relying on optional
    librosa codecs, so behaviour does not change with the install.
    """
    require()
    import numpy as np
    import soundfile as sf
    import librosa

    path = Path(path)
    if not path.is_file():
        raise FileNotFoundError(path)

    if path.suffix.lower() in _NATIVE_SUFFIXES:
        data, native_rate = sf.read(str(path), dtype="float32", always_2d=True)
    else:
        with tempfile.TemporaryDirectory(prefix="lvs-decode-") as tmp:
            decoded = Path(tmp) / "decoded.wav"
            subprocess.run(
                [_ffmpeg(), "-y", "-v", "error", "-i", str(path),
                 "-c:a", "pcm_s16le", str(decoded)],
                check=True, capture_output=True)
            data, native_rate = sf.read(str(decoded), dtype="float32",
                                        always_2d=True)

    mono = data.mean(axis=1).astype(np.float32, copy=False)
    if native_rate != sample_rate:
        mono = librosa.resample(mono, orig_sr=native_rate,
                                target_sr=sample_rate, res_type="soxr_hq")
    return np.ascontiguousarray(mono, dtype=np.float32), sample_rate


def save(path: Path, samples, sample_rate: int = MUSIC_RATE,
         subtype: str = "PCM_16") -> Path:
    """Write float samples to a WAV, clipped to full scale."""
    require()
    import numpy as np
    import soundfile as sf

    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    data = np.clip(np.asarray(samples, dtype=np.float32), -1.0, 1.0)
    sf.write(str(path), data, int(sample_rate), subtype=subtype)
    return path


def save_compressed(path: Path, samples, sample_rate: int = MUSIC_RATE,
                    bitrate: str = "320k") -> Path:
    """Write an MP3 (or whatever the suffix implies) through ffmpeg."""
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    with tempfile.TemporaryDirectory(prefix="lvs-encode-") as tmp:
        staging = Path(tmp) / "staging.wav"
        save(staging, samples, sample_rate)
        subprocess.run(
            [_ffmpeg(), "-y", "-v", "error", "-i", str(staging),
             "-b:a", bitrate, str(path)],
            check=True, capture_output=True)
    return path


def to_project_rate(samples, sample_rate: int):
    """Resample to the 24 kHz PCM-16 world the voice dataset lives in."""
    require()
    import numpy as np
    import librosa
    if sample_rate == PROJECT_RATE:
        out = np.asarray(samples, dtype=np.float32)
    else:
        out = librosa.resample(np.asarray(samples, dtype=np.float32),
                               orig_sr=sample_rate, target_sr=PROJECT_RATE,
                               res_type="soxr_hq")
    return out, PROJECT_RATE


def write_project_wav(path: Path, samples, sample_rate: int) -> Path:
    """Save as the canonical 24 kHz mono PCM-16 the clip tools expect."""
    import numpy as np
    resampled, rate = to_project_rate(samples, sample_rate)
    values = np.clip(resampled, -1.0, 1.0)
    ints = (values * 32767.0).astype("<i2")
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    with wave.open(str(path), "wb") as handle:
        handle.setnchannels(1)
        handle.setsampwidth(2)
        handle.setframerate(rate)
        handle.writeframes(ints.tobytes())
    return path


# ---------------------------------------------------------------------------
# Level helpers -- the small amount of "mixing desk" the tools need.
# ---------------------------------------------------------------------------

def rms_dbfs(samples) -> float:
    import numpy as np
    data = np.asarray(samples, dtype=np.float64)
    if not data.size:
        return -120.0
    value = float(np.sqrt(np.mean(data ** 2)))
    return 20.0 * np.log10(value) if value > 1e-12 else -120.0


def peak_dbfs(samples) -> float:
    import numpy as np
    data = np.asarray(samples, dtype=np.float64)
    if not data.size:
        return -120.0
    value = float(np.max(np.abs(data)))
    return 20.0 * np.log10(value) if value > 1e-12 else -120.0


def apply_gain_db(samples, db: float):
    import numpy as np
    return (np.asarray(samples, dtype=np.float32)
            * np.float32(10.0 ** (db / 20.0)))


def normalize_to(samples, target_dbfs: float = -14.0):
    """Scale so the RMS sits at ``target_dbfs``. Does not limit."""
    current = rms_dbfs(samples)
    if current <= -119.0:
        return samples
    return apply_gain_db(samples, target_dbfs - current)


def soft_limit(samples, ceiling_dbfs: float = -1.0):
    """Tanh-based soft clipper -- catches overs without hard edges.

    Below the knee the curve is essentially linear, so quiet material is
    untouched; only material approaching the ceiling gets bent.
    """
    import numpy as np
    ceiling = 10.0 ** (ceiling_dbfs / 20.0)
    data = np.asarray(samples, dtype=np.float32)
    peak = float(np.max(np.abs(data))) if data.size else 0.0
    if peak <= ceiling:
        return data
    # Normalize into the tanh's linear region, bend, then rescale.
    drive = data / ceiling
    return (np.tanh(drive) * ceiling).astype(np.float32)


def fit_length(samples, length: int):
    """Trim or zero-pad to exactly ``length`` samples."""
    import numpy as np
    data = np.asarray(samples, dtype=np.float32)
    if data.size == length:
        return data
    if data.size > length:
        return data[:length]
    return np.concatenate([data, np.zeros(length - data.size, np.float32)])
