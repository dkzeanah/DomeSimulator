"""Put a vocal take in the pocket.

Rapping "in time" means the syllables land where the beat says they
should. This module finds where the syllables actually landed, compares
that to the grid from :mod:`beatgrid`, and time-warps the take so they
land on it -- without moving the pitch, and without the take getting
longer or shorter overall than you asked for.

The warp is done by the same PSOLA grain engine the autotuner uses
(:func:`local_voice_studio.autotune.psola_map`). Running the output
timeline faster or slower through the input, while keeping each grain's
own period, moves syllables in time and leaves pitch alone -- the exact
mirror of what the tuner does.

Two knobs matter more than the rest:

``strength``
    How far toward the grid to drag each syllable. 1.0 is fully
    quantized and machine-tight; around 0.6 keeps the human push-and-pull
    while fixing the syllables that were properly late.

``swing``
    Delays every second subdivision. 0 is straight, ~0.3 is a relaxed
    hip-hop shuffle, 0.66 approaches triplet feel.
"""

from __future__ import annotations

import math
import re
from dataclasses import dataclass
from pathlib import Path

from . import autotune, dsp
from .beatgrid import BeatGrid

# Rap sits roughly between 3 and 12 syllables a second; outside that the
# onset detector is almost certainly finding something other than speech.
MIN_SYLLABLE_GAP = 0.055


@dataclass
class FlowAnalysis:
    """How a take sits against a beat."""

    onsets: tuple = ()
    duration: float = 0.0
    subdivision: str = "1/8"
    offsets_ms: tuple = ()        # signed distance to nearest grid line
    tightness: float = 0.0        # 0..1; 1 = already dead on the grid
    syllables_per_second: float = 0.0
    syllables_per_bar: float = 0.0
    late_fraction: float = 0.0    # share of syllables behind the beat

    def describe(self) -> str:
        import statistics
        if not self.offsets_ms:
            return "no syllables detected"
        mean_abs = statistics.fmean(abs(v) for v in self.offsets_ms)
        drift = statistics.fmean(self.offsets_ms)
        feel = ("behind the beat" if drift > 8 else
                "ahead of the beat" if drift < -8 else "on the beat")
        return (f"{len(self.onsets)} syllables, "
                f"{self.syllables_per_bar:.1f} per bar, "
                f"{self.syllables_per_second:.1f}/sec | "
                f"average {mean_abs:.0f} ms off the {self.subdivision} grid "
                f"({drift:+.0f} ms, {feel}) | "
                f"tightness {self.tightness * 100:.0f}%")


def detect_syllables(y, sample_rate: int, sensitivity: float = 1.0) -> tuple:
    """Onset times of the syllables in a vocal, in seconds.

    Tuned for speech rather than music: a short hop so fast delivery is
    not smeared, and backtracking so each onset sits at the quiet moment
    *before* the consonant rather than on its peak. Cutting there is what
    lets the warp move a syllable without slicing through it.
    """
    dsp.require()
    import numpy as np
    import librosa

    y = np.asarray(y, dtype=np.float32)
    if y.size == 0:
        return ()
    hop = 128
    env = librosa.onset.onset_strength(y=y, sr=sample_rate, hop_length=hop,
                                       aggregate=np.median)
    frames = librosa.onset.onset_detect(
        onset_envelope=env, sr=sample_rate, hop_length=hop,
        backtrack=True, units="frames",
        delta=float(max(0.01, 0.07 / max(0.05, sensitivity))))
    times = librosa.frames_to_time(frames, sr=sample_rate, hop_length=hop)

    # Collapse onsets that are too close together to be separate
    # syllables -- usually one consonant cluster detected twice.
    out: list[float] = []
    for t in times:
        if not out or (t - out[-1]) >= MIN_SYLLABLE_GAP:
            out.append(float(t))
    return tuple(out)


def swung_grid(grid: BeatGrid, subdivision: str = "1/8",
               swing: float = 0.0) -> tuple:
    """Grid lines with every second subdivision pushed late.

    Swing is expressed as a fraction of the gap: 0 is straight, 1/3 gives
    a triplet-ish shuffle. The downbeat-side lines never move, so bar
    lines stay where the beat put them.
    """
    lines = list(grid.grid(subdivision))
    if swing <= 0 or len(lines) < 3:
        return tuple(lines)
    swing = float(min(0.9, swing))
    step = _step_of(subdivision)
    out = list(lines)
    # Which lines are "off" is decided by where each one sits inside its
    # beat, not by its index in this list. The grid is extrapolated past
    # the detected beats at both ends, so the number of leading lines
    # varies -- keying off list parity would swing the on-beats instead
    # whenever that count came out odd.
    for i in range(len(lines) - 1):
        position = grid.beat_number(lines[i])
        within = position - math.floor(position)
        slot = int(round(within / step)) if step > 0 else 0
        if slot % 2 == 1:
            gap = lines[i + 1] - lines[i]
            out[i] = lines[i] + gap * swing
    return tuple(out)


def analyze(y, sample_rate: int, grid: BeatGrid,
            subdivision: str = "1/8", swing: float = 0.0,
            onsets: tuple | None = None) -> FlowAnalysis:
    """Measure a take against the beat without changing it."""
    import numpy as np

    y = np.asarray(y, dtype=np.float32)
    duration = float(y.size / sample_rate)
    times = onsets if onsets is not None else detect_syllables(y, sample_rate)
    if not times:
        return FlowAnalysis(duration=duration, subdivision=subdivision)

    lines = np.asarray(swung_grid(grid, subdivision, swing), dtype=np.float64)
    offsets = []
    for t in times:
        nearest = lines[int(np.argmin(np.abs(lines - t)))]
        offsets.append((t - float(nearest)) * 1000.0)

    step_ms = 1000.0 * grid.beat_seconds * _step_of(subdivision)
    # Tightness: 0 ms off is 1.0, half a subdivision off is 0.0.
    half = max(1e-6, step_ms / 2.0)
    tight = float(np.mean([max(0.0, 1.0 - abs(o) / half) for o in offsets]))
    bars = max(1e-6, duration / grid.bar_seconds) if grid.bar_seconds else 1.0
    return FlowAnalysis(
        onsets=tuple(times),
        duration=duration,
        subdivision=subdivision,
        offsets_ms=tuple(round(o, 2) for o in offsets),
        tightness=round(tight, 4),
        syllables_per_second=round(len(times) / max(1e-6, duration), 3),
        syllables_per_bar=round(len(times) / bars, 2),
        late_fraction=round(float(np.mean([o > 0 for o in offsets])), 3),
    )


def _step_of(subdivision: str) -> float:
    from .beatgrid import SUBDIVISIONS
    return SUBDIVISIONS.get(subdivision, 0.5) or 1.0


def align_to_grid(y, sample_rate: int, grid: BeatGrid,
                  subdivision: str = "1/8", strength: float = 1.0,
                  swing: float = 0.0, max_shift_ms: float = 140.0,
                  onsets: tuple | None = None):
    """Time-warp a take so its syllables land on the grid.

    Returns ``(audio, before, after)`` -- the warped take plus a
    :class:`FlowAnalysis` from either side of the move, so the effect is
    measurable rather than a matter of opinion.
    """
    dsp.require()
    import numpy as np

    y = np.asarray(y, dtype=np.float32)
    before = analyze(y, sample_rate, grid, subdivision, swing, onsets)
    if not before.onsets or strength <= 0:
        return y, before, before

    lines = np.asarray(swung_grid(grid, subdivision, swing), dtype=np.float64)
    max_shift = max_shift_ms / 1000.0

    sources: list[float] = []
    targets: list[float] = []
    for t in before.onsets:
        nearest = float(lines[int(np.argmin(np.abs(lines - t)))])
        shift = (nearest - t) * float(max(0.0, min(1.0, strength)))
        shift = max(-max_shift, min(max_shift, shift))
        sources.append(float(t))
        # The grid runs one line either side of the recording so that
        # every moment has a line within half a step. Those outer lines
        # are legitimate targets to measure against but not to move audio
        # to -- nothing can start before the take does.
        targets.append(max(0.0, float(t + shift)))

    # The map has to stay strictly increasing or the warp folds back on
    # itself and syllables overwrite each other. Enforce a floor gap.
    floor = MIN_SYLLABLE_GAP * 0.5
    for i in range(1, len(targets)):
        if targets[i] <= targets[i - 1] + floor:
            targets[i] = targets[i - 1] + floor

    duration = float(y.size / sample_rate)
    src = [0.0] + sources + [duration]
    dst = [0.0] + targets + [max(duration, targets[-1] + 0.05)]
    # Deduplicate any collapsed anchors before interpolating.
    clean_src, clean_dst = [src[0]], [dst[0]]
    for s, d in zip(src[1:], dst[1:]):
        if s > clean_src[-1] + 1e-4 and d > clean_dst[-1] + 1e-4:
            clean_src.append(s)
            clean_dst.append(d)
    src_samples = np.asarray(clean_src, dtype=np.float64) * sample_rate
    dst_samples = np.asarray(clean_dst, dtype=np.float64) * sample_rate

    def source_of_output(out_sample: float) -> float:
        return float(np.interp(out_sample, dst_samples, src_samples))

    track = autotune.track_pitch(y, sample_rate)
    warped = autotune.psola_map(
        y, sample_rate, track,
        source_of_output=source_of_output,
        output_length=int(dst_samples[-1]))

    after = analyze(warped, sample_rate, grid, subdivision, swing)
    return warped, before, after


def stretch_to_length(y, sample_rate: int, seconds: float):
    """Fit a take to an exact duration, pitch unchanged."""
    dsp.require()
    import numpy as np
    y = np.asarray(y, dtype=np.float32)
    target = int(seconds * sample_rate)
    if target <= 0 or y.size == 0:
        return y
    scale = y.size / float(target)
    track = autotune.track_pitch(y, sample_rate)
    return autotune.psola_map(
        y, sample_rate, track,
        source_of_output=lambda out_sample: out_sample * scale,
        output_length=target)


def fit_to_bars(y, sample_rate: int, grid: BeatGrid, bars: float):
    """Fit a take to an exact number of bars of this beat."""
    return stretch_to_length(y, sample_rate, grid.bar_seconds * float(bars))


# ---------------------------------------------------------------------------
# Writing side: how many syllables actually fit in a bar
# ---------------------------------------------------------------------------

_VOWEL_RUN = re.compile(r"[aeiouy]+", re.IGNORECASE)
_SYLLABIC_TAIL = re.compile(r"[^aeiouylr][lmn]$")


def count_syllables(word: str) -> int:
    """Approximate English syllable count for one word.

    Vowel-group counting with the usual silent-e correction. It is an
    estimate, not a dictionary -- good enough to tell a writer that a bar
    is overfull, not good enough to be quoted as fact.
    """
    text = re.sub(r"[^A-Za-z]", "", word).lower()
    if not text:
        return 0
    groups = _VOWEL_RUN.findall(text)
    count = len(groups)
    if text.endswith("e") and count > 1 and not text.endswith(("le", "ee", "ye")):
        count -= 1
    # Syllabic consonants: "rhythm", "prism", "chasm" end in a sounded
    # m/n/l that no vowel letter accounts for. Liquids before it (film,
    # kiln) stay in the same syllable, so they are excluded.
    if _SYLLABIC_TAIL.search(text):
        count += 1
    return max(1, count)


def layout_bars(text: str, grid: BeatGrid, subdivision: str = "1/8",
                swing: float = 0.0) -> list:
    """Lay written bars onto grid positions, one line per bar.

    Returns a list of dicts describing each line: its syllable count, how
    many grid slots a bar actually has, and whether it overruns. This is
    a writing aid -- it says whether the words can physically fit the
    pocket at this tempo before anything is recorded.
    """
    slots_per_bar = int(round(grid.beats_per_bar / _step_of(subdivision)))
    lines = [line.strip() for line in (text or "").splitlines() if line.strip()]
    grid_lines = swung_grid(grid, subdivision, swing)
    out = []
    cursor = 0
    for index, line in enumerate(lines):
        words = line.split()
        counts = [count_syllables(w) for w in words]
        total = sum(counts)
        placements = []
        for word, syllables in zip(words, counts):
            at = grid_lines[cursor] if cursor < len(grid_lines) else None
            placements.append({
                "word": word,
                "syllables": syllables,
                "at_seconds": round(at, 4) if at is not None else None,
                "bar_beat": (grid.position(at) if at is not None else None),
            })
            cursor += syllables
        out.append({
            "line": index + 1,
            "text": line,
            "syllables": total,
            "slots_per_bar": slots_per_bar,
            "overfull": total > slots_per_bar,
            "words": placements,
        })
    return out
