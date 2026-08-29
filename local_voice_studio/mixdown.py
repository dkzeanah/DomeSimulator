"""Put the vocal on the beat and get a file out.

Small, deliberate mixing desk: level the two sources against each other,
optionally duck the instrumental under the vocal so words stay
intelligible, thicken the vocal the way rap records do, and catch the
peaks on the way out.

Levels here are stated in LUFS-ish RMS terms rather than raw gain, so
"vocal 3 dB over the beat" means the same thing whatever the source
files happen to be normalized to.
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from . import dsp


@dataclass
class MixSettings:
    """Everything the desk does, in one inspectable object."""

    vocal_db: float = -12.0        # target RMS for the vocal
    beat_db: float = -16.0         # target RMS for the instrumental
    offset_s: float = 0.0          # where the vocal starts on the beat
    duck_db: float = 0.0           # dip the beat this much under the vocal
    duck_attack_ms: float = 25.0
    duck_release_ms: float = 220.0
    double_track: bool = False     # thicken the vocal
    double_spread_ms: float = 18.0
    double_detune_cents: float = 9.0
    stereo: bool = True
    width: float = 0.55            # how far the doubles sit off-centre
    ceiling_db: float = -1.0       # output limiter ceiling
    tail_s: float = 1.5            # keep this much beat after the vocal ends

    def describe(self) -> str:
        bits = [f"vocal {self.vocal_db:+.1f} dB", f"beat {self.beat_db:+.1f} dB"]
        if self.offset_s:
            bits.append(f"in at {self.offset_s:.2f}s")
        if self.duck_db:
            bits.append(f"duck {self.duck_db:.1f} dB")
        if self.double_track:
            bits.append(f"doubled ({self.double_detune_cents:.0f} cents)")
        bits.append("stereo" if self.stereo else "mono")
        return ", ".join(bits)


def double_track(vocal, sample_rate: int, spread_ms: float = 18.0,
                 detune_cents: float = 9.0):
    """Two extra copies of the vocal, slightly late and slightly detuned.

    This is the standard rap/pop thickening trick. The copies are not
    identical to the original -- if they were, summing them would just
    raise the level -- so each is nudged in time and pitch, which is what
    produces the chorused width rather than a louder mono vocal.

    Returns ``(left_double, right_double)``.
    """
    dsp.require()
    import numpy as np
    from . import autotune

    v = np.asarray(vocal, dtype=np.float32)
    delay = int(sample_rate * spread_ms / 1000.0)
    cents = float(detune_cents)

    left = autotune.shift_semitones(v, sample_rate, +cents / 100.0)
    right = autotune.shift_semitones(v, sample_rate, -cents / 100.0)
    left = np.concatenate([np.zeros(delay, np.float32), left])[:len(v)]
    right = np.concatenate([np.zeros(delay // 2, np.float32), right])[:len(v)]
    return dsp.fit_length(left, len(v)), dsp.fit_length(right, len(v))


def _envelope_fast(y, sample_rate: int, attack_ms: float, release_ms: float):
    """Smoothed amplitude envelope with separate attack and release.

    Drives the duck: the beat should drop quickly when a line starts and
    come back gently, not chatter on every syllable.

    The smoothing is done on a ~1 kHz decimated control signal rather
    than per sample. A sample-rate Python loop over a three-minute track
    is tens of millions of iterations and would take longer than every
    other stage combined; the envelope is deliberately slow anyway, so
    decimating and interpolating back is inaudible.
    """
    import numpy as np

    x = np.abs(np.asarray(y, dtype=np.float32))
    step = max(1, sample_rate // 1000)                 # ~1 kHz control rate
    coarse = np.maximum.reduceat(
        x, np.arange(0, len(x), step)) if len(x) else x
    rate = sample_rate / step
    a = float(np.exp(-1.0 / max(1e-6, rate * attack_ms / 1000.0)))
    r = float(np.exp(-1.0 / max(1e-6, rate * release_ms / 1000.0)))
    env = np.zeros_like(coarse)
    running = 0.0
    for i in range(len(coarse)):
        coeff = a if coarse[i] > running else r
        running = coeff * running + (1.0 - coeff) * coarse[i]
        env[i] = running
    if len(coarse) < 2:
        return np.zeros_like(x)
    full = np.interp(np.arange(len(x)) / step,
                     np.arange(len(coarse)), env)
    return full.astype(np.float32)


def mix(vocal, beat, sample_rate: int,
        settings: MixSettings | None = None):
    """Lay the vocal over the instrumental. Returns ``(audio, report)``.

    ``audio`` is ``(n, 2)`` when ``settings.stereo`` else ``(n,)``.
    """
    dsp.require()
    import numpy as np

    settings = settings or MixSettings()
    v = np.asarray(vocal, dtype=np.float32)
    b = np.asarray(beat, dtype=np.float32)

    v = dsp.normalize_to(v, settings.vocal_db)
    b = dsp.normalize_to(b, settings.beat_db)

    offset = max(0, int(settings.offset_s * sample_rate))
    vocal_end = offset + len(v)
    total = max(len(b), vocal_end + int(settings.tail_s * sample_rate))

    v_track = np.zeros(total, np.float32)
    v_track[offset:offset + len(v)] = v
    b_track = dsp.fit_length(b, total)

    report = {"settings": settings.describe(),
              "duration_s": round(total / sample_rate, 3),
              "vocal_rms_db": round(dsp.rms_dbfs(v), 2),
              "beat_rms_db": round(dsp.rms_dbfs(b), 2)}

    if settings.duck_db > 0:
        env = _envelope_fast(v_track, sample_rate, settings.duck_attack_ms,
                             settings.duck_release_ms)
        peak = float(env.max()) if env.size else 0.0
        if peak > 1e-6:
            depth = 1.0 - 10.0 ** (-abs(settings.duck_db) / 20.0)
            b_track = b_track * (1.0 - depth * (env / peak)).astype(np.float32)
        report["ducked_db"] = settings.duck_db

    if settings.stereo:
        left = b_track.copy()
        right = b_track.copy()
        centre = v_track
        if settings.double_track:
            dl, dr = double_track(v, sample_rate, settings.double_spread_ms,
                                  settings.double_detune_cents)
            pad_l = np.zeros(total, np.float32)
            pad_r = np.zeros(total, np.float32)
            pad_l[offset:offset + len(dl)] = dl
            pad_r[offset:offset + len(dr)] = dr
            side = float(max(0.0, min(1.0, settings.width)))
            # Doubles go out to the sides; the lead stays up the middle so
            # the words still come from one place.
            left += pad_l * side * 0.7
            right += pad_r * side * 0.7
            report["doubled"] = True
        left += centre
        right += centre
        out = np.stack([left, right], axis=1)
    else:
        out = b_track + v_track
        if settings.double_track:
            dl, dr = double_track(v, sample_rate, settings.double_spread_ms,
                                  settings.double_detune_cents)
            pad = np.zeros(total, np.float32)
            pad[offset:offset + len(dl)] = (dl + dr) * 0.5
            out = out + pad * 0.6
            report["doubled"] = True

    report["peak_before_limit_db"] = round(dsp.peak_dbfs(out), 2)
    out = dsp.soft_limit(out, settings.ceiling_db)
    report["peak_db"] = round(dsp.peak_dbfs(out), 2)
    return out.astype(np.float32), report


def render(vocal_path: Path, beat_path: Path, out_path: Path,
           settings: MixSettings | None = None,
           sample_rate: int = dsp.MUSIC_RATE) -> dict:
    """Load two files, mix them, write the result. Returns the report."""
    vocal, _ = dsp.load(Path(vocal_path), sample_rate)
    beat, _ = dsp.load(Path(beat_path), sample_rate)
    audio, report = mix(vocal, beat, sample_rate, settings)
    out_path = Path(out_path)
    if out_path.suffix.lower() in (".wav", ".flac"):
        dsp.save(out_path, audio, sample_rate)
    else:
        dsp.save_compressed(out_path, audio, sample_rate)
    report["output"] = str(out_path)
    return report
