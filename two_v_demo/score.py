"""Original music for the Cabin World films, made from arithmetic.

Like ``make_beat.py``, nothing here is sampled or downloaded: every sound is
sines, shaped noise and envelopes, so the result belongs to whoever renders
it and no platform can match it to anybody else's recording.

One cue, shaped to a film's structure rather than looped under it:

* a low **drone** from the first frame, the ground the film stands on;
* a sparse **pluck** motif that grows denser through a *build*;
* a warm **pad** that swells across the build;
* a noise **riser** into each *hit*;
* at each hit, a **bloom** -- a sub drop and a bell chord -- the reveal;
* a woody **knock** wherever the picture shows wood being struck or cut.

    track = compose(11.0, build=(1.6, 8.0), hits=(8.0,), knocks=(0.05,))
    write_wav(track, Path("cue.wav"))

For a narrated film, pass ``bed=True``: the same palette without the loud
moments, meant to sit at soundboard gain under a voice.
"""

from __future__ import annotations

import math
import wave
from pathlib import Path

import numpy as np

SAMPLE_RATE = 44100


def _t(seconds: float) -> np.ndarray:
    return np.arange(int(seconds * SAMPLE_RATE), dtype=np.float64) / SAMPLE_RATE


def _hz(midi: float) -> float:
    return 440.0 * 2 ** ((midi - 69) / 12)


# D major, the key of the sunset: root, and the chord the reveal lands on.
ROOT = 38                                  # D2
CHORD = (50, 57, 64, 66, 73)               # D3 A3 E4 F#4 C#5 -- Dmaj9
MOTIF = (62, 64, 66, 69, 71, 74, 76, 78)   # D major pentatonic, D4 up


def _place(track: np.ndarray, sound: np.ndarray, at: float, pan: float = 0.0) -> None:
    start = int(at * SAMPLE_RATE)
    if start >= len(track):
        return
    end = min(len(track), start + len(sound))
    left, right = math.cos((pan + 1) * math.pi / 4), math.sin((pan + 1) * math.pi / 4)
    track[start:end, 0] += sound[:end - start] * left * math.sqrt(2)
    track[start:end, 1] += sound[:end - start] * right * math.sqrt(2)


def drone(seconds: float) -> np.ndarray:
    t = _t(seconds)
    out = np.zeros((len(t), 2))
    for midi, gain in ((ROOT, 0.28), (ROOT + 7, 0.14), (ROOT + 12, 0.08)):
        f = _hz(midi)
        for ch, detune in ((0, -0.18), (1, 0.18)):
            wobble = 1 + 0.12 * np.sin(math.tau * 0.07 * t + ch)
            out[:, ch] += gain * wobble * np.sin(math.tau * (f + detune) * t)
    fade = np.clip(t / 1.4, 0, 1)
    return out * fade[:, None]


def pad(seconds: float, level) -> np.ndarray:
    """The chord, soft-sawtooth voices detuned across the stereo field."""
    t = _t(seconds)
    out = np.zeros((len(t), 2))
    for i, midi in enumerate(CHORD):
        f = _hz(midi)
        for ch, detune in ((0, -0.9 - i * 0.1), (1, 0.9 + i * 0.1)):
            voice = sum(np.sin(math.tau * (f + detune) * n * t) / n ** 1.6 for n in range(1, 7))
            out[:, ch] += voice * 0.07
    return out * np.asarray(level)[:, None]


def pluck(midi: float, seconds: float = 1.6) -> np.ndarray:
    t = _t(seconds)
    f = _hz(midi)
    tone = (np.sin(math.tau * f * t) + 0.35 * np.sin(math.tau * 2 * f * t) * np.exp(-t * 6)
            + 0.12 * np.sin(math.tau * 3 * f * t) * np.exp(-t * 9))
    return tone * np.exp(-t * 3.2) * np.clip(t / 0.004, 0, 1) * 0.16


def knock(seconds: float = 0.5, seed: int = 3) -> np.ndarray:
    """A woody tock: a pitched body and a click."""
    t = _t(seconds)
    rng = np.random.default_rng(seed)
    body = np.sin(math.tau * (190 - 60 * t) * t) * np.exp(-t * 22)
    click = rng.standard_normal(len(t)) * np.exp(-t * 180) * 0.35
    return (body + click) * 0.55


def riser(seconds: float, seed: int = 5) -> np.ndarray:
    """Noise brightening and swelling into a hit, cut dead at the end."""
    from scipy.signal import lfilter

    n = int(seconds * SAMPLE_RATE)
    rng = np.random.default_rng(seed)
    noise = rng.standard_normal(n)
    out = np.zeros(n)
    block = 1024
    state = np.zeros(1)
    for start in range(0, n, block):
        k = start / max(1, n)
        cutoff = 300 * (1 - k) + 6000 * k ** 2
        a = math.exp(-math.tau * cutoff / SAMPLE_RATE)
        seg, state = lfilter([1 - a], [1, -a], noise[start:start + block], zi=state)
        out[start:start + block] = seg
    env = np.linspace(0, 1, n) ** 2.2
    return out * env * 0.45


def bloom(seconds: float = 4.0) -> np.ndarray:
    """The reveal: a sub drop under a bell chord."""
    t = _t(seconds)
    sub = np.sin(math.tau * np.cumsum(62 - 24 * np.clip(t / 0.9, 0, 1)) / SAMPLE_RATE) * np.exp(-t * 1.6) * 0.8
    bell = sum(np.sin(math.tau * _hz(m + 12) * t) * g for m, g in ((62, 0.20), (69, 0.14), (66, 0.12), (74, 0.08)))
    bell = bell * np.exp(-t * 0.9) * np.clip(t / 0.01, 0, 1)
    return sub + bell


def reverb(track: np.ndarray, seconds: float = 2.2, wet: float = 0.28, seed: int = 11) -> np.ndarray:
    from scipy.signal import fftconvolve

    t = _t(seconds)
    rng = np.random.default_rng(seed)
    out = track.copy()
    for ch in range(2):
        impulse = rng.standard_normal(len(t)) * np.exp(-t * 3.0 / seconds * 2.3)
        impulse /= np.sqrt(np.sum(impulse ** 2))
        out[:, ch] = track[:, ch] * (1 - wet) + fftconvolve(track[:, ch], impulse)[:len(track)] * wet * 1.6
    return out


def compose(seconds: float, build=None, hits=(), knocks=(), bed: bool = False,
            seed: int = 7) -> np.ndarray:
    """A cue ``seconds`` long, shaped to the picture's timings. Stereo float."""
    n = int(seconds * SAMPLE_RATE)
    track = np.zeros((n, 2))
    t = _t(seconds)
    track += drone(seconds) * (0.7 if bed else 1.0)

    # The pad: low from the start, swelling across the build, held after.
    b0, b1 = build if build else (0.0, seconds)
    swell = np.clip((t - b0) / max(1e-6, b1 - b0), 0, 1) ** 1.5
    level = 0.25 + 0.75 * swell if not bed else 0.35 + 0.25 * swell
    for hit in hits:
        level = level + 0.25 * np.clip((t - hit) / 0.3, 0, 1) * np.exp(-np.clip(t - hit, 0, None) / 3.0)
    track += pad(seconds, level)

    # Plucks: eighth notes at 96 bpm, more of them as the build climbs.
    rng = np.random.default_rng(seed)
    step = 60 / 96 / 2
    at = 0.4
    while at < seconds - 0.5:
        k = np.clip((at - b0) / max(1e-6, b1 - b0), 0, 1)
        chance = (0.18 + 0.62 * k) if not bed else 0.22
        if any(0 <= at - h < 1.2 for h in hits):
            chance = 0.0       # let the bloom ring alone
        if rng.random() < chance:
            idx = int(min(len(MOTIF) - 1, rng.integers(0, 4) + k * 4))
            _place(track, pluck(MOTIF[idx]), at, pan=rng.uniform(-0.6, 0.6))
        at += step

    if not bed:
        for hit in hits:
            lead = min(3.5, hit - b0) if build else min(3.5, hit)
            if lead > 0.3:
                _place(track, riser(lead, seed + int(hit * 10)), hit - lead)
            _place(track, bloom(min(4.5, seconds - hit + 0.5)), hit)
    for k in knocks:
        _place(track, knock(seed=seed + int(k * 100)), k, pan=-0.2)

    track = reverb(track)
    fade = np.clip((seconds - t) / 0.9, 0, 1)
    track *= fade[:, None]
    track = np.tanh(track * 1.1)
    peak = float(np.max(np.abs(track))) or 1.0
    return track / peak * 0.89     # about -1 dBFS


def loop_bed(seconds: float = 150.0, xfade: float = 8.0, seed: int = 7) -> np.ndarray:
    """A bed that tiles without a seam, for a narrated film longer than it.

    The soundboard loops a bed under the whole narration, so the end has to
    flow into the start: compose a little extra and cross-fade that tail
    over the head, equal-power.
    """
    n, x = int(seconds * SAMPLE_RATE), int(xfade * SAMPLE_RATE)
    track = compose(seconds + xfade + 1.0, bed=True, seed=seed)
    body = track[:n].copy()
    k = np.linspace(0.0, 1.0, x)[:, None]
    body[:x] = track[n:n + x] * np.cos(k * np.pi / 2) + track[:x] * np.sin(k * np.pi / 2)
    peak = float(np.max(np.abs(body))) or 1.0
    return body / peak * 0.89


def write_wav(track: np.ndarray, path: Path) -> Path:
    """Stereo 16-bit PCM."""
    data = np.clip(track * 32767.0, -32768, 32767).astype("<i2")
    path.parent.mkdir(parents=True, exist_ok=True)
    with wave.open(str(path), "wb") as handle:
        handle.setnchannels(2)
        handle.setsampwidth(2)
        handle.setframerate(SAMPLE_RATE)
        handle.writeframes(data.tobytes())
    return path


def validate_score() -> None:
    track = compose(6.0, build=(1.0, 4.0), hits=(4.0,), knocks=(0.1,))
    assert track.shape == (6 * SAMPLE_RATE, 2)
    assert np.all(np.isfinite(track)) and 0.8 < np.max(np.abs(track)) <= 0.9
    # The hit is the loudest moment; the tail fades to silence.
    rms = lambda a, b: float(np.sqrt(np.mean(track[int(a * SAMPLE_RATE):int(b * SAMPLE_RATE)] ** 2)))
    assert rms(4.0, 4.6) > rms(1.0, 1.6), "the reveal lands louder than the build begins"
    assert rms(5.95, 6.0) < 0.02
    bed = compose(6.0, bed=True)
    assert np.all(np.isfinite(bed))
