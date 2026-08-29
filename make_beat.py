"""Synthesise a plain beat bed for the soundboard.

No audio is downloaded and none is sampled.  Every sound here is
generated from arithmetic -- a decaying sine for the kick, filtered noise
for the snare, short bright noise for the hat -- so the result is yours
outright and there is no licence attached to it.

    py -3.12 make_beat.py                 # 84 bpm, 32 bars, into beds/
    py -3.12 make_beat.py --bpm 92 --bars 48

The output lands at ``assets/audio/beds/frankenbeat.wav`` and becomes
available to any segment or lesson as ``beds/frankenbeat``.
"""

from __future__ import annotations

import argparse
import math
from pathlib import Path

import numpy as np

from two_v_demo.soundboard import ROOT, SAMPLE_RATE, write_wav


def _envelope(length: int, attack: int, decay: float) -> np.ndarray:
    """A percussive envelope: near-instant attack, exponential decay."""
    time = np.arange(length, dtype=np.float32)
    rise = np.clip(time / max(1, attack), 0.0, 1.0)
    fall = np.exp(-time / max(1.0, decay))
    return rise * fall


def kick(duration: float = 0.34, start_hz: float = 118.0,
         end_hz: float = 42.0) -> np.ndarray:
    """A pitch-swept sine. The sweep is what makes it read as a kick."""
    length = int(duration * SAMPLE_RATE)
    time = np.arange(length, dtype=np.float32) / SAMPLE_RATE
    sweep = end_hz + (start_hz - end_hz) * np.exp(-time * 22.0)
    phase = 2.0 * np.pi * np.cumsum(sweep) / SAMPLE_RATE
    body = np.sin(phase) * _envelope(length, 40, SAMPLE_RATE * 0.055)
    return body * 0.95


def snare(duration: float = 0.20) -> np.ndarray:
    """Noise plus a little tone, which is roughly what a snare is."""
    length = int(duration * SAMPLE_RATE)
    rng = np.random.default_rng(11)
    noise = rng.standard_normal(length).astype(np.float32)
    # A cheap band-pass: difference twice to lose the low end.
    noise = np.diff(noise, prepend=0.0)
    time = np.arange(length, dtype=np.float32) / SAMPLE_RATE
    tone = np.sin(2.0 * np.pi * 190.0 * time) * 0.35
    return (noise * 0.55 + tone) * _envelope(length, 20, SAMPLE_RATE * 0.020)


def hat(duration: float = 0.06) -> np.ndarray:
    """Short bright noise."""
    length = int(duration * SAMPLE_RATE)
    rng = np.random.default_rng(29)
    noise = rng.standard_normal(length).astype(np.float32)
    noise = np.diff(noise, prepend=0.0)
    noise = np.diff(noise, prepend=0.0)
    return noise * _envelope(length, 8, SAMPLE_RATE * 0.006) * 0.42


def build(bpm: float = 84.0, bars: int = 32, swing: float = 0.06
          ) -> np.ndarray:
    """A two-bar pattern, repeated, with a little swing on the offbeats."""
    beat = 60.0 / bpm
    bar = beat * 4.0
    total = int(bar * bars * SAMPLE_RATE) + SAMPLE_RATE
    track = np.zeros(total, dtype=np.float32)

    kick_sound, snare_sound, hat_sound = kick(), snare(), hat()

    def place(sound: np.ndarray, at: float, gain: float) -> None:
        start = int(at * SAMPLE_RATE)
        end = min(track.size, start + sound.size)
        if start >= track.size:
            return
        track[start:end] += sound[:end - start] * gain

    for index in range(bars):
        origin = index * bar
        # Kick on 1 and the and-of-3; snare on 2 and 4. Plain, which is
        # what a bed should be -- it sits under a voice, not over it.
        place(kick_sound, origin + 0.0, 1.0)
        place(kick_sound, origin + beat * 2.5, 0.82)
        place(snare_sound, origin + beat * 1.0, 0.85)
        place(snare_sound, origin + beat * 3.0, 0.85)
        for step in range(8):
            offset = step * beat * 0.5
            if step % 2:
                offset += beat * swing
            place(hat_sound, origin + offset, 0.5 if step % 2 else 0.7)

    peak = float(np.max(np.abs(track)))
    if peak > 0.0:
        track = track / peak * 0.72
    return track


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--bpm", type=float, default=84.0)
    parser.add_argument("--bars", type=int, default=32)
    parser.add_argument("--name", default="frankenbeat")
    parser.add_argument("--swing", type=float, default=0.06)
    args = parser.parse_args()

    track = build(args.bpm, args.bars, args.swing)
    target = ROOT / "beds" / f"{args.name}.wav"
    target.parent.mkdir(parents=True, exist_ok=True)
    write_wav(track, target)
    seconds = track.size / SAMPLE_RATE
    print(f"wrote {target}")
    print(f"  {args.bpm:g} bpm, {args.bars} bars, {seconds:.1f}s")
    print(f"  available to segments and lessons as beds/{args.name}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
