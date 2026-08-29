"""Read the rhythm and key out of an instrumental.

Everything the rap tools need to know about a beat lives in one
:class:`BeatGrid`: how fast it is, where every beat and bar lands, which
beat is the "one", and what key it is in. The grid is what the flow
aligner snaps syllables to, and the key is what the autotuner snaps
notes to -- so this module runs first and the rest read its output.

Nothing here is hardcoded to a tempo or a time signature: the bar length
is chosen by scoring how much of the track's percussive energy lands on
each candidate, so a beat that is genuinely in 3/4 is not forced into
4/4.
"""

from __future__ import annotations

import json
from dataclasses import dataclass, asdict, field
from pathlib import Path

from . import dsp

# Subdivisions the grid can be asked for, as a fraction of one beat.
SUBDIVISIONS = {
    "bar": 0.0,          # resolved against the bar length, not the beat
    "1/4": 1.0,          # one beat -- quarter note in 4/4
    "1/8": 0.5,
    "1/8t": 1.0 / 3.0,   # eighth-note triplet
    "1/16": 0.25,
    "1/16t": 1.0 / 6.0,
    "1/32": 0.125,
}

NOTE_NAMES = ("C", "C#", "D", "D#", "E", "F", "F#", "G", "G#", "A", "A#", "B")

# Krumhansl-Kessler key profiles: how strongly each scale degree is
# expected to sound in a major and a minor key.
_MAJOR_PROFILE = (6.35, 2.23, 3.48, 2.33, 4.38, 4.09,
                  2.52, 5.19, 2.39, 3.66, 2.29, 2.88)
_MINOR_PROFILE = (6.33, 2.68, 3.52, 5.38, 2.60, 3.53,
                  2.54, 4.75, 3.98, 2.69, 3.34, 3.17)


@dataclass
class BeatGrid:
    """Where every beat, bar and subdivision of a track sits, in seconds."""

    path: str = ""
    sample_rate: int = dsp.MUSIC_RATE
    duration: float = 0.0
    bpm: float = 0.0
    beats: tuple = ()             # every beat time, seconds
    beats_per_bar: int = 4
    downbeat_index: int = 0       # which entry of `beats` is the first "one"
    steadiness: float = 0.0       # 0..1, how metronomic the beat times are
    key: str = ""                 # e.g. "F# minor"
    key_confidence: float = 0.0
    tonic_hz: float = 0.0         # the key's tonic, as a frequency

    # ---- derived views ------------------------------------------------

    @property
    def beat_seconds(self) -> float:
        return 60.0 / self.bpm if self.bpm > 0 else 0.0

    @property
    def bar_seconds(self) -> float:
        return self.beat_seconds * self.beats_per_bar

    @property
    def downbeats(self) -> tuple:
        """Every bar line, in seconds."""
        return tuple(self.beats[i] for i in
                     range(self.downbeat_index, len(self.beats),
                           self.beats_per_bar))

    @property
    def bar_count(self) -> int:
        return len(self.downbeats)

    def grid(self, subdivision: str = "1/8") -> tuple:
        """Every grid line at ``subdivision``, in seconds.

        Built by interpolating *between measured beats* rather than from
        the average tempo, so the grid follows a track that drifts
        instead of walking away from it.
        """
        if subdivision not in SUBDIVISIONS:
            raise ValueError(
                f"unknown subdivision {subdivision!r}; choose one of "
                f"{', '.join(SUBDIVISIONS)}")
        if len(self.beats) < 2:
            return tuple(self.beats)
        if subdivision == "bar":
            return self.downbeats
        step = SUBDIVISIONS[subdivision]
        out: list[float] = []
        for index in range(len(self.beats) - 1):
            start = self.beats[index]
            span = self.beats[index + 1] - start
            count = max(1, int(round(1.0 / step)))
            for k in range(count):
                out.append(start + span * (k * step))
        out.append(self.beats[-1])

        # Beat tracking rarely starts at 0.00 or runs to the last sample,
        # but a vocal usually does. Without extending the grid over the
        # whole track, anything before the first detected beat gets
        # measured against a line hundreds of milliseconds away -- and a
        # quantizer would then drag it there. Extrapolate at the local
        # tempo so every moment of the track has a grid line near it.
        first_span = self.beats[1] - self.beats[0]
        last_span = self.beats[-1] - self.beats[-2]
        # Run one line *past* each end rather than stopping at it. Ending
        # exactly at zero would still leave a moment at 0.00 up to a whole
        # step from the nearest line, when the most it should ever be is
        # half a step.
        if first_span > 0:
            back = out[0] - first_span * step
            limit = -first_span * step
            while back > limit - 1e-9:
                out.insert(0, back)
                back -= first_span * step
        if last_span > 0:
            end = max(self.duration, out[-1]) + last_span * step
            forward = out[-1] + last_span * step
            while forward <= end + 1e-9:
                out.append(forward)
                forward += last_span * step
        return tuple(out)

    def quantize(self, time: float, subdivision: str = "1/8") -> float:
        """The nearest grid line to ``time``."""
        lines = self.grid(subdivision)
        if not lines:
            return time
        best = min(lines, key=lambda value: abs(value - time))
        return float(best)

    def beat_number(self, time: float) -> float:
        """Fractional index into ``beats`` for a moment in seconds.

        Interpolates between the *measured* beats rather than dividing by
        the average tempo, so a track that drifts still reports the beat
        a listener is on. Outside the tracked range it extrapolates at
        the nearest local tempo.
        """
        beats = self.beats
        if not beats:
            return 0.0
        if len(beats) == 1:
            step = self.beat_seconds or 1.0
            return (time - beats[0]) / step
        if time <= beats[0]:
            step = beats[1] - beats[0]
            return (time - beats[0]) / step if step > 0 else 0.0
        if time >= beats[-1]:
            step = beats[-1] - beats[-2]
            base = float(len(beats) - 1)
            return base + ((time - beats[-1]) / step if step > 0 else 0.0)
        # Binary search for the surrounding pair.
        low, high = 0, len(beats) - 1
        while high - low > 1:
            mid = (low + high) // 2
            if beats[mid] <= time:
                low = mid
            else:
                high = mid
        span = beats[high] - beats[low]
        frac = (time - beats[low]) / span if span > 0 else 0.0
        return low + frac

    def position(self, time: float) -> tuple:
        """``(bar, beat_in_bar)`` for a moment, both 1-based, as floats.

        Bar 1 beat 1.0 is the first downbeat. Times before it come back
        with a bar number below 1, which is the honest answer for a
        pickup rather than a clamp that hides it.
        """
        if not self.beats:
            return (0.0, 0.0)
        import math
        relative = self.beat_number(time) - self.downbeat_index
        # Snap away floating-point dust so a time sitting exactly on a
        # bar line reports beat 1.0 and not 4.999 of the bar before.
        if abs(relative - round(relative)) < 1e-6:
            relative = float(round(relative))
        per_bar = max(1, self.beats_per_bar)
        bar_index = math.floor(relative / per_bar)
        beat_in_bar = relative - bar_index * per_bar
        return (bar_index + 1.0, beat_in_bar + 1.0)

    def describe(self) -> str:
        return (f"{self.bpm:.1f} BPM, {self.beats_per_bar}/4, "
                f"{self.bar_count} bars, key {self.key or 'unknown'} "
                f"({self.key_confidence * 100:.0f}% sure), "
                f"steadiness {self.steadiness * 100:.0f}%")

    # ---- persistence --------------------------------------------------

    def to_json(self, path: Path) -> Path:
        path = Path(path)
        path.parent.mkdir(parents=True, exist_ok=True)
        payload = asdict(self)
        payload["beats"] = [round(v, 6) for v in self.beats]
        payload["_derived"] = {
            "bar_seconds": round(self.bar_seconds, 6),
            "bar_count": self.bar_count,
            "downbeats": [round(v, 6) for v in self.downbeats],
            "summary": self.describe(),
        }
        path.write_text(json.dumps(payload, indent=2), encoding="utf-8")
        return path

    @staticmethod
    def from_json(path: Path) -> "BeatGrid":
        raw = json.loads(Path(path).read_text(encoding="utf-8"))
        raw.pop("_derived", None)
        raw["beats"] = tuple(raw.get("beats") or ())
        return BeatGrid(**raw)


# ---------------------------------------------------------------------------
# Analysis
# ---------------------------------------------------------------------------

def _detect_key(y, sample_rate: int) -> tuple:
    """(name, confidence, tonic_hz) by correlating chroma with key profiles."""
    import numpy as np
    import librosa

    chroma = librosa.feature.chroma_cqt(y=y, sr=sample_rate)
    if chroma.size == 0:
        return ("", 0.0, 0.0)
    weights = chroma.mean(axis=1)
    if float(weights.sum()) <= 0:
        return ("", 0.0, 0.0)
    weights = weights / weights.sum()

    scores = []
    for tonic in range(12):
        for profile, quality in ((_MAJOR_PROFILE, "major"),
                                 (_MINOR_PROFILE, "minor")):
            rotated = np.roll(np.asarray(profile, dtype=np.float64), tonic)
            rotated = rotated / rotated.sum()
            # Pearson correlation between observed and expected profile.
            a = weights - weights.mean()
            b = rotated - rotated.mean()
            denom = float(np.sqrt((a ** 2).sum() * (b ** 2).sum()))
            scores.append((float((a * b).sum() / denom) if denom else 0.0,
                           tonic, quality))
    scores.sort(reverse=True)
    best, tonic, quality = scores[0]
    runner_up = scores[1][0]
    # Confidence is how far clear of the next-best key the winner is,
    # not the raw correlation -- a track that fits two keys equally well
    # should not report high confidence just because both fit.
    margin = max(0.0, best - runner_up)
    confidence = max(0.0, min(1.0, margin * 4.0))
    tonic_hz = float(librosa.midi_to_hz(60 + tonic))
    return (f"{NOTE_NAMES[tonic]} {quality}", confidence, tonic_hz)


def _onset_envelopes(y, rate):
    """Return (envelope_for_tempo, full_band_envelope).

    Tempo is read from a **low-band** onset envelope. Hi-hats and shakers
    sit two or three octaves above the kick and snare, and they usually
    play twice as often, so a full-band envelope makes the eighth-note
    pulse look like the beat and the tempo comes out doubled. Restricting
    to the kick/low-snare region measures the pulse a listener would
    actually tap to.

    A track with no low end (a thin loop, a plucked guitar sample) gets
    the full-band envelope instead, since a near-silent low band carries
    no rhythm to track.
    """
    import numpy as np
    import librosa

    full = librosa.onset.onset_strength(y=y, sr=rate)
    # n_mels must fit the number of FFT bins the band actually spans, or
    # librosa builds empty filters and warns. The default 2048-point FFT
    # at 44.1 kHz gives ~21.5 Hz bins, so 0-400 Hz is only ~18 bins.
    bins_in_band = max(4, int(400.0 / (rate / 2048.0)))
    low = librosa.onset.onset_strength(y=y, sr=rate, fmax=400.0,
                                       n_mels=min(24, bins_in_band))
    if low.size == 0 or float(np.sum(low)) <= 0:
        return full, full
    # Is there enough low-end movement to trust? Compare the peakiness of
    # the two envelopes rather than raw loudness, which scales with mix.
    def peakiness(env):
        mean = float(np.mean(env))
        return float(np.std(env) / mean) if mean > 1e-9 else 0.0
    if peakiness(low) < 0.35 * peakiness(full):
        return full, full
    return low, full


def _pick_beats_per_bar(onset_env, beat_frames, candidates=(4, 3)) -> tuple:
    """Choose the bar length and which beat is the "one".

    Scores every (bar length, phase) pair by the mean onset strength on
    the beats that would be downbeats. Music puts more energy on the
    one, so the winning phase is the bar line.
    """
    import numpy as np
    if len(beat_frames) < 4:
        return (candidates[0], 0, 0.0)
    strengths = np.asarray(
        [onset_env[min(int(f), len(onset_env) - 1)] for f in beat_frames],
        dtype=np.float64)
    if float(strengths.sum()) <= 0:
        return (candidates[0], 0, 0.0)
    best = (candidates[0], 0, -1.0)
    for per_bar in candidates:
        if len(strengths) < per_bar * 2:
            continue
        for phase in range(per_bar):
            picked = strengths[phase::per_bar]
            others = np.delete(strengths, np.arange(phase, len(strengths),
                                                    per_bar))
            if not picked.size or not others.size:
                continue
            # How much louder the candidate downbeats are than the rest.
            contrast = float(picked.mean() - others.mean())
            if contrast > best[2]:
                best = (per_bar, phase, contrast)
    per_bar, phase, contrast = best
    return (per_bar, phase, max(0.0, contrast))


def analyze(path: Path, sample_rate: int = dsp.MUSIC_RATE,
            beats_per_bar: int | None = None,
            bpm_hint: float | None = None) -> BeatGrid:
    """Measure an instrumental: tempo, beat grid, bar lines, and key.

    ``beats_per_bar`` forces a time signature instead of detecting one.
    ``bpm_hint`` biases the tempo search, which is the fix when a track
    is detected at half or double its real tempo.
    """
    dsp.require()
    import numpy as np
    import librosa

    y, rate = dsp.load(path, sample_rate)
    if y.size == 0:
        raise ValueError(f"{path} contains no audio")

    onset_env, _full_env = _onset_envelopes(y, rate)
    kwargs = {"onset_envelope": onset_env, "sr": rate, "units": "frames"}
    if bpm_hint:
        kwargs["start_bpm"] = float(bpm_hint)
    tempo, beat_frames = librosa.beat.beat_track(**kwargs)
    tempo = float(np.atleast_1d(tempo)[0])
    beat_times = librosa.frames_to_time(beat_frames, sr=rate)

    # Steadiness: how consistent the gaps between beats are. A live or
    # rubato performance scores low, a programmed beat scores near 1.
    steadiness = 0.0
    if len(beat_times) > 2:
        gaps = np.diff(beat_times)
        mean_gap = float(gaps.mean())
        if mean_gap > 0:
            steadiness = float(max(0.0, 1.0 - (gaps.std() / mean_gap) * 4.0))
        # Prefer the tempo the *measured* beats imply over the estimator's
        # own number; they can disagree slightly and the grid is built
        # from the beats.
        if mean_gap > 0:
            tempo = 60.0 / mean_gap

    if beats_per_bar:
        per_bar, phase = int(beats_per_bar), 0
        if len(beat_frames) >= 4:
            _, phase, _ = _pick_beats_per_bar(onset_env, beat_frames,
                                              (int(beats_per_bar),))
    else:
        per_bar, phase, _contrast = _pick_beats_per_bar(onset_env, beat_frames)

    key, key_confidence, tonic_hz = _detect_key(y, rate)

    return BeatGrid(
        path=str(path),
        sample_rate=rate,
        duration=float(y.size / rate),
        bpm=round(tempo, 3),
        beats=tuple(round(float(t), 6) for t in beat_times),
        beats_per_bar=per_bar,
        downbeat_index=phase,
        steadiness=round(steadiness, 4),
        key=key,
        key_confidence=round(key_confidence, 4),
        tonic_hz=round(tonic_hz, 4),
    )


def click_track(grid: BeatGrid, subdivision: str = "1/4",
                sample_rate: int | None = None):
    """A click at every grid line -- for checking a grid by ear.

    Downbeats get a higher click so the bar lines are audible.
    """
    dsp.require()
    import numpy as np
    rate = sample_rate or grid.sample_rate
    total = int((grid.duration + 0.5) * rate)
    out = np.zeros(total, dtype=np.float32)
    downbeats = set(round(v, 4) for v in grid.downbeats)
    for line in grid.grid(subdivision):
        start = int(line * rate)
        if start >= total:
            continue
        is_down = round(line, 4) in downbeats
        freq = 1800.0 if is_down else 1100.0
        length = int(0.035 * rate)
        length = min(length, total - start)
        if length <= 0:
            continue
        t = np.arange(length, dtype=np.float32) / rate
        env = np.exp(-t * 90.0).astype(np.float32)
        out[start:start + length] += (
            np.sin(2 * np.pi * freq * t) * env * 0.6).astype(np.float32)
    return dsp.soft_limit(out)
