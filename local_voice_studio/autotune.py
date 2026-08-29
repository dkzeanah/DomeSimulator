"""Pitch correction and pitch shifting for vocals.

Three jobs, in order:

1. **Measure** the sung/spoken pitch over time (``track_pitch``).
2. **Decide** what the pitch should have been -- the nearest note in the
   chosen key, approached at a chosen speed (``correction_curve``).
3. **Rebuild** the audio at the new pitch without turning the singer into
   a chipmunk (``retune``).

Step 3 uses TD-PSOLA (time-domain pitch-synchronous overlap-add): the
waveform is cut into individual pitch periods and those periods are laid
back down at new spacing. Because each period is *moved* rather than
*resampled*, the vocal tract resonances inside it are untouched, so the
formants -- the thing that makes a voice sound like a person of a
particular size -- stay where they were. Naive resampling moves them,
which is exactly the chipmunk artifact.

The ``retune_ms`` knob is the one that decides the genre. Near zero the
pitch jumps to each note instantly and you get the hard, stepped,
unmistakably-tuned rap and R&B sound. Above roughly 60 ms the correction
glides and just sounds like a singer with good pitch.
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from . import dsp

NOTE_NAMES = ("C", "C#", "D", "D#", "E", "F", "F#", "G", "G#", "A", "A#", "B")

# Semitone offsets from the tonic.
SCALES = {
    "chromatic":        (0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11),
    "major":            (0, 2, 4, 5, 7, 9, 11),
    "minor":            (0, 2, 3, 5, 7, 8, 10),      # natural minor
    "harmonic minor":   (0, 2, 3, 5, 7, 8, 11),
    "dorian":           (0, 2, 3, 5, 7, 9, 10),
    "mixolydian":       (0, 2, 4, 5, 7, 9, 10),
    "phrygian":         (0, 1, 3, 5, 7, 8, 10),
    "major pentatonic": (0, 2, 4, 7, 9),
    "minor pentatonic": (0, 3, 5, 7, 10),
    "blues":            (0, 3, 5, 6, 7, 10),
}

# Sensible starting points rather than a wall of knobs.
PRESETS = {
    "off":       {"strength": 0.0, "retune_ms": 60.0},
    "natural":   {"strength": 0.72, "retune_ms": 95.0},
    "tight":     {"strength": 0.92, "retune_ms": 38.0},
    "hard":      {"strength": 1.0,  "retune_ms": 8.0},
    "robot":     {"strength": 1.0,  "retune_ms": 0.0},
}

PRESET_HELP = {
    "off": "measure the pitch but leave the audio alone",
    "natural": "gently nudges flat/sharp notes; still sounds human",
    "tight": "clearly tuned, still glides a little between notes",
    "hard": "the stepped, obviously-tuned rap and R&B sound",
    "robot": "snaps instantly with no glide at all",
}

FMIN = 65.0     # ~C2, below a low male speaking voice
FMAX = 1000.0   # ~B5, above a high sung note


# ---------------------------------------------------------------------------
# Notes and keys
# ---------------------------------------------------------------------------

def parse_key(key: str) -> tuple:
    """``"F# minor"`` -> ``(tonic_pitch_class, scale_name)``.

    Accepts flats, and any scale named in :data:`SCALES`. A bare note
    name means major.
    """
    text = (key or "").strip().replace("_", " ")
    if not text:
        return (0, "chromatic")

    # A bare scale name means "these intervals, tonic irrelevant" --
    # "chromatic" is the common one, and it lets every note through, so
    # there is nothing for a tonic to change.
    if text.lower() in SCALES:
        return (0, text.lower())

    parts = text.split()
    raw = parts[0].strip()
    # Accept c, C, c#, Db, bb ... and normalize flats to their sharp.
    letter = raw[0].upper()
    accidental = raw[1:].strip().replace("B", "b")
    note = letter + accidental
    flats = {"Cb": "B", "Db": "C#", "Eb": "D#", "Fb": "E",
             "Gb": "F#", "Ab": "G#", "Bb": "A#"}
    note = flats.get(note, note)
    if note not in NOTE_NAMES:
        raise ValueError(f"unknown note {raw!r} in key {key!r}")

    scale = " ".join(parts[1:]).lower().strip() or "major"
    scale = {"min": "minor", "m": "minor", "maj": "major"}.get(scale, scale)
    if scale not in SCALES:
        raise ValueError(
            f"unknown scale {scale!r}; choose one of {', '.join(SCALES)}")
    return (NOTE_NAMES.index(note), scale)


def allowed_midi(key: str) -> tuple:
    """Every MIDI note number permitted by ``key``, across all octaves."""
    tonic, scale = parse_key(key)
    degrees = SCALES[scale]
    return tuple(sorted(
        note for note in range(0, 128)
        if (note - tonic) % 12 in degrees))


def hz_to_midi(hz):
    import numpy as np
    hz = np.asarray(hz, dtype=np.float64)
    out = np.full(hz.shape, np.nan)
    good = hz > 0
    out[good] = 69.0 + 12.0 * np.log2(hz[good] / 440.0)
    return out


def midi_to_hz(midi):
    import numpy as np
    return 440.0 * (2.0 ** ((np.asarray(midi, dtype=np.float64) - 69.0) / 12.0))


def note_name(midi_value: float) -> str:
    import math
    if midi_value != midi_value:                    # NaN
        return "-"
    nearest = int(round(midi_value))
    return f"{NOTE_NAMES[nearest % 12]}{nearest // 12 - 1}"


# ---------------------------------------------------------------------------
# Measure
# ---------------------------------------------------------------------------

@dataclass
class PitchTrack:
    hop: int
    sample_rate: int
    f0: object = None            # numpy array, NaN where unvoiced
    voiced: object = None        # numpy bool array
    times: object = None

    @property
    def voiced_fraction(self) -> float:
        import numpy as np
        if self.voiced is None or not len(self.voiced):
            return 0.0
        return float(np.mean(self.voiced))

    def summary(self) -> dict:
        """Median pitch, range, and how far off the notes it sits."""
        import numpy as np
        good = self.f0[self.voiced] if self.voiced is not None else None
        if good is None or good.size == 0:
            return {"voiced_pct": 0.0, "median_hz": 0.0, "median_note": "-",
                    "low_note": "-", "high_note": "-", "mean_cents_off": 0.0}
        midi = hz_to_midi(good)
        cents_off = (midi - np.round(midi)) * 100.0
        return {
            "voiced_pct": round(self.voiced_fraction * 100.0, 1),
            "median_hz": round(float(np.median(good)), 2),
            "median_note": note_name(float(np.median(midi))),
            "low_note": note_name(float(np.percentile(midi, 5))),
            "high_note": note_name(float(np.percentile(midi, 95))),
            "mean_cents_off": round(float(np.mean(np.abs(cents_off))), 1),
        }


def track_pitch(y, sample_rate: int, hop: int = 256,
                method: str = "yin") -> PitchTrack:
    """Measure fundamental frequency over time.

    ``method="yin"`` (the default) is roughly **130x faster than pyin**
    on this machine -- 0.03x realtime against 4.4x -- which is the
    difference between a three-minute verse taking two seconds and taking
    thirteen minutes. It returns no voicing decision of its own, so
    voicing is derived here from frame energy and whether the estimate
    sits in a plausible vocal range.

    ``method="pyin"`` uses librosa's HMM tracker, whose voiced/unvoiced
    decision is better on breathy or noisy takes. Worth the wait for a
    final pass on a difficult vocal; too slow to sit behind a preview
    button.
    """
    dsp.require()
    import numpy as np
    import librosa

    y = np.asarray(y, dtype=np.float32)
    if method not in ("yin", "pyin"):
        raise ValueError(f"unknown pitch method {method!r}; use yin or pyin")

    if method == "pyin":
        f0, voiced_flag, _prob = librosa.pyin(
            y, fmin=FMIN, fmax=FMAX, sr=sample_rate,
            frame_length=2048, hop_length=hop)
        voiced = np.asarray(voiced_flag, dtype=bool) & np.isfinite(f0)
    else:
        f0 = librosa.yin(y, fmin=FMIN, fmax=FMAX, sr=sample_rate,
                         frame_length=2048, hop_length=hop)
        f0 = np.asarray(f0, dtype=np.float64)
        rms = librosa.feature.rms(y=y, frame_length=2048,
                                  hop_length=hop)[0]
        # Match lengths: rms and yin can differ by a frame at the edges.
        size = min(len(f0), len(rms))
        f0, rms = f0[:size], rms[:size]
        with np.errstate(divide="ignore"):
            level = 20.0 * np.log10(np.maximum(rms, 1e-10))
        # Voiced where there is real signal (relative to this take's own
        # loudest moment, so a quiet recording is not written off) and
        # the estimate is inside the range we asked for.
        floor = max(level.max() - 40.0, -70.0) if level.size else -70.0
        voiced = (level > floor) & np.isfinite(f0)
        voiced &= (f0 > FMIN * 1.02) & (f0 < FMAX * 0.98)
        f0 = np.where(voiced, f0, np.nan)

    times = librosa.times_like(f0, sr=sample_rate, hop_length=hop)
    return PitchTrack(hop=hop, sample_rate=sample_rate, f0=f0,
                      voiced=voiced, times=times)


# ---------------------------------------------------------------------------
# Decide
# ---------------------------------------------------------------------------

def correction_curve(track: PitchTrack, key: str = "chromatic",
                     strength: float = 0.9, retune_ms: float = 20.0):
    """Target f0 per frame: the nearest allowed note, approached smoothly.

    ``strength`` 0..1 is how far toward the note to move. ``retune_ms``
    is how long the move takes -- it smooths the *correction*, not the
    pitch, so vibrato and slides survive while the average stays in
    tune.
    """
    import numpy as np

    f0 = np.asarray(track.f0, dtype=np.float64)
    voiced = np.asarray(track.voiced, dtype=bool)
    target = f0.copy()
    if not voiced.any():
        return target

    permitted = np.asarray(allowed_midi(key), dtype=np.float64)
    midi = hz_to_midi(f0)

    # Nearest permitted note for every voiced frame.
    snapped = midi.copy()
    idx = np.searchsorted(permitted, midi[voiced])
    idx = np.clip(idx, 1, len(permitted) - 1)
    lower = permitted[idx - 1]
    upper = permitted[idx]
    chosen = np.where(np.abs(midi[voiced] - lower) <= np.abs(upper - midi[voiced]),
                      lower, upper)
    snapped[voiced] = chosen

    # The correction, in semitones, is what gets smoothed.
    delta = np.zeros_like(midi)
    delta[voiced] = (snapped[voiced] - midi[voiced]) * float(
        max(0.0, min(1.0, strength)))

    if retune_ms > 0:
        frame_ms = 1000.0 * track.hop / track.sample_rate
        # One-pole smoother; the coefficient is set so the correction
        # reaches ~63% of its target in retune_ms.
        alpha = float(np.exp(-frame_ms / max(1e-6, retune_ms)))
        smoothed = np.zeros_like(delta)
        running = 0.0
        for i in range(len(delta)):
            if not voiced[i]:
                running = 0.0
                smoothed[i] = 0.0
                continue
            running = alpha * running + (1.0 - alpha) * delta[i]
            smoothed[i] = running
        delta = smoothed

    target[voiced] = midi_to_hz(midi[voiced] + delta[voiced])
    return target


# ---------------------------------------------------------------------------
# Rebuild -- TD-PSOLA
# ---------------------------------------------------------------------------

def _pitch_marks(y, sample_rate: int, track: PitchTrack):
    """Sample positions of successive pitch periods, plus each period.

    Marks are advanced by the local period so they stay pitch
    synchronous; in unvoiced stretches a nominal period is used, which
    makes consonants pass through as ordinary overlap-add.
    """
    import numpy as np

    n = len(y)
    hop = track.hop
    f0 = np.asarray(track.f0, dtype=np.float64)
    voiced = np.asarray(track.voiced, dtype=bool)
    nominal = sample_rate / 200.0

    def period_at(sample_index: int) -> tuple:
        frame = int(sample_index // hop)
        frame = max(0, min(len(f0) - 1, frame))
        if voiced[frame] and f0[frame] > 0:
            return (sample_rate / f0[frame], True)
        return (nominal, False)

    marks: list[int] = []
    periods: list[float] = []
    is_voiced: list[bool] = []
    position = 0.0
    while position < n:
        period, v = period_at(int(position))
        marks.append(int(position))
        periods.append(period)
        is_voiced.append(v)
        position += period
    return (np.asarray(marks, dtype=np.int64),
            np.asarray(periods, dtype=np.float64),
            np.asarray(is_voiced, dtype=bool))


def psola_map(y, sample_rate: int, track: PitchTrack,
              source_of_output=None, ratio_at_sample=None,
              output_length: int | None = None):
    """The shared PSOLA engine: pitch shift, time warp, or both.

    Walks the *output* timeline one grain at a time. For each output
    position it asks ``source_of_output`` which moment of the input to
    take the grain from, copies one windowed pitch period from the
    nearest analysis mark there, and advances by ``period / ratio``.

    That single loop covers both jobs:

    * **pitch** -- leave ``source_of_output`` as identity and vary
      ``ratio_at_sample``; output grains are spaced closer or wider than
      the source periods, so the pitch moves and the duration does not.
    * **time** -- leave ``ratio_at_sample`` at 1 and make
      ``source_of_output`` run through the input faster or slower;
      grains keep their original spacing, so the duration moves and the
      pitch does not.

    Both are pure grain bookkeeping, so combining them is free.
    """
    import numpy as np

    y = np.asarray(y, dtype=np.float64)
    n = len(y)
    marks, periods, _voiced = _pitch_marks(y, sample_rate, track)
    if marks.size < 2:
        return np.asarray(y, dtype=np.float32)

    if source_of_output is None:
        def source_of_output(t):                    # noqa: E306
            return t
    if ratio_at_sample is None:
        def ratio_at_sample(_i):                    # noqa: E306
            return 1.0

    total = int(output_length if output_length is not None else n)
    out = np.zeros(total + int(sample_rate), dtype=np.float64)
    weight = np.zeros_like(out)

    position = float(source_of_output(0.0) if output_length else marks[0])
    position = max(0.0, position)
    out_pos = float(marks[0]) if output_length is None else 0.0

    while out_pos < total:
        source = float(source_of_output(out_pos))
        if source < 0 or source >= n:
            break
        # Nearest analysis mark to the moment we are sampling from.
        j = int(np.searchsorted(marks, source))
        j = max(0, min(len(marks) - 1, j))
        if j > 0 and abs(marks[j - 1] - source) < abs(marks[j] - source):
            j -= 1
        centre = int(marks[j])
        period = float(periods[j])
        ratio = float(ratio_at_sample(centre))
        ratio = max(0.5, min(2.0, ratio if ratio > 0 else 1.0))

        half = max(8, int(round(period)))
        seg_start = max(0, centre - half)
        seg_end = min(n, centre + half)
        if seg_end <= seg_start:
            out_pos += period / ratio
            continue
        window = np.hanning(seg_end - seg_start + 2)[1:-1]
        grain = y[seg_start:seg_end] * window

        write = int(round(out_pos)) - (centre - seg_start)
        w_start = max(0, write)
        offset = w_start - write
        length = min(len(grain) - offset, len(out) - w_start)
        if length > 0:
            out[w_start:w_start + length] += grain[offset:offset + length]
            weight[w_start:w_start + length] += window[offset:offset + length]

        out_pos += period / ratio

    # Normalize by accumulated window weight so a changing overlap factor
    # does not change the level.
    safe = weight > 1e-6
    out[safe] /= weight[safe]
    return np.asarray(out[:total], dtype=np.float32)


def _psola(y, sample_rate: int, track: PitchTrack, ratio_at_sample):
    """Pitch-only PSOLA: same length in, same length out."""
    return psola_map(y, sample_rate, track, None, ratio_at_sample)


@dataclass
class TuneResult:
    audio: object
    sample_rate: int
    key: str
    before: dict
    after: dict
    preset: str = ""

    def report(self) -> str:
        return (f"key {self.key} | voiced {self.before['voiced_pct']:.0f}% | "
                f"off-note {self.before['mean_cents_off']:.0f} cents -> "
                f"{self.after['mean_cents_off']:.0f} cents | "
                f"range {self.before['low_note']}-{self.before['high_note']}")


def retune(y, sample_rate: int, key: str = "chromatic",
           strength: float = 0.9, retune_ms: float = 20.0,
           preset: str | None = None,
           method: str = "yin") -> TuneResult:
    """Pitch-correct a vocal into ``key``.

    Pass ``preset`` (see :data:`PRESETS`) instead of the two numbers for
    the usual cases.
    """
    dsp.require()
    import numpy as np

    if preset:
        if preset not in PRESETS:
            raise ValueError(
                f"unknown preset {preset!r}; choose one of "
                f"{', '.join(PRESETS)}")
        strength = PRESETS[preset]["strength"]
        retune_ms = PRESETS[preset]["retune_ms"]

    y = np.asarray(y, dtype=np.float32)
    track = track_pitch(y, sample_rate, method=method)
    before = track.summary()

    if strength <= 0 or not track.voiced.any():
        return TuneResult(y, sample_rate, key, before, before, preset or "off")

    target = correction_curve(track, key, strength, retune_ms)
    f0 = np.asarray(track.f0, dtype=np.float64)
    hop = track.hop

    ratios = np.ones(len(f0), dtype=np.float64)
    good = track.voiced & np.isfinite(target) & (f0 > 0)
    ratios[good] = target[good] / f0[good]

    def ratio_at(sample_index: int) -> float:
        frame = int(sample_index // hop)
        frame = max(0, min(len(ratios) - 1, frame))
        return float(ratios[frame])

    tuned = _psola(y, sample_rate, track, ratio_at)
    after = track_pitch(tuned, sample_rate, method=method).summary()
    return TuneResult(tuned, sample_rate, key, before, after, preset or "")


def shift_semitones(y, sample_rate: int, semitones: float,
                    method: str = "yin"):
    """Transpose by a fixed interval, keeping length and formants."""
    dsp.require()
    import numpy as np
    y = np.asarray(y, dtype=np.float32)
    if abs(semitones) < 1e-6:
        return y
    track = track_pitch(y, sample_rate, method=method)
    ratio = float(2.0 ** (semitones / 12.0))
    return _psola(y, sample_rate, track, lambda _i: ratio)
