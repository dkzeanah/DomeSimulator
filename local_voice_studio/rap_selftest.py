"""Vertical-slice check of the rap production chain, on synthetic audio.

Kept out of :mod:`local_voice_studio.selftest` because that one is
deliberately dependency-free (standard library only, so the dataset
workflow can be checked anywhere) while everything here needs numpy /
scipy / librosa / soundfile. If those are missing this reports and
returns False instead of failing the program: the studio still records,
curates and clones without them, it just cannot do beat or pitch work.

Every assertion is against ground truth we constructed -- a beat built
at a known tempo in a known key, and a vocal deliberately placed late
and sung sharp. A pass therefore means the numbers came out right, not
merely that nothing raised an exception.
"""

from __future__ import annotations

import tempfile
from pathlib import Path

from .dsp import dependency_status

BPM = 96.0
BARS = 8


def _build_beat(np, dsp, sr: int):
    """A drum-and-bass-note loop at a known tempo, bar length and key."""
    beat_s = 60.0 / BPM
    total = int((BARS * 4 * beat_s + 1.0) * sr)
    track = np.zeros(total, np.float32)
    rng = np.random.default_rng(4)

    def place(sig, at):
        i = int(at * sr)
        end = min(total, i + len(sig))
        if end > i:
            track[i:end] += sig[:end - i]

    def snare(n):
        t = np.arange(n) / sr
        return (rng.standard_normal(n) * np.exp(-t * 26) * 0.7).astype(np.float32)

    def kick(n):
        t = np.arange(n) / sr
        f = 120 * np.exp(-t * 30) + 45
        return (np.sin(2 * np.pi * np.cumsum(f) / sr)
                * np.exp(-t * 14)).astype(np.float32)

    def tone(freq, n, amp=0.2):
        t = np.arange(n) / sr
        return (np.sin(2 * np.pi * freq * t)
                * np.exp(-t * 1.5) * amp).astype(np.float32)

    root = 220.0                                   # A -> expect an A-ish key
    for step in range(BARS * 4):
        at = step * beat_s
        slot = step % 4
        if slot == 0:
            place(kick(int(0.30 * sr)), at)
            for interval in (0, 3, 7):             # minor triad
                place(tone(root * 2 ** (interval / 12),
                           int(beat_s * 3.6 * sr)), at)
        elif slot == 2:
            place(kick(int(0.24 * sr)) * 0.75, at)
        if slot in (1, 3):
            place(snare(int(0.16 * sr)), at)
    return dsp.soft_limit(track * 0.8), total


def _build_sloppy_vocal(np, grid, sr: int, total: int):
    """A take that is both off-grid and 55 cents sharp, on purpose."""
    beat_s = 60.0 / BPM
    vocal = np.zeros(total, np.float32)
    rng = np.random.default_rng(21)
    placed = 0
    for index, line in enumerate(grid.grid("1/8")):
        if index % 3 == 2 or line > BARS * 4 * beat_s - 1.0:
            continue                                # gaps, like real phrasing
        at = line + float(rng.uniform(-0.075, 0.075))
        f0 = 165.0 * 2 ** ((index % 5 + 0.55) / 12)
        n = int(0.17 * sr)
        t = np.arange(n) / sr
        grain = np.zeros(n, np.float32)
        for harmonic in range(1, 12):
            grain += (np.sin(2 * np.pi * f0 * harmonic * t)
                      / harmonic).astype(np.float32)
        grain *= (np.minimum(1.0, t * 30) * np.exp(-t * 5.0)).astype(np.float32)
        i = int(max(0.0, at) * sr)
        end = min(total, i + n)
        if end > i:
            vocal[i:end] += grain[:end - i] * 0.5
            placed += 1
    return np.clip(vocal, -1, 1).astype(np.float32), placed


def run_rap_selftest() -> bool:
    """Returns True on pass, False when the audio libraries are absent."""
    status = dependency_status()
    if not status.ready:
        print(f"Rap tools selftest SKIPPED -- {status.detail}")
        return False

    import numpy as np

    from . import autotune, beatgrid, dsp, flow, mixdown, rapkit

    sr = dsp.MUSIC_RATE

    with tempfile.TemporaryDirectory(prefix="lvs-rap-") as temporary:
        tmp = Path(temporary)
        beat_audio_src, total = _build_beat(np, dsp, sr)
        beat_path = tmp / "beat.wav"
        dsp.save(beat_path, beat_audio_src, sr)

        # ---- the beat is read correctly --------------------------------
        grid = beatgrid.analyze(beat_path)
        assert abs(grid.bpm - BPM) < 2.0, f"tempo {grid.bpm} != {BPM}"
        assert grid.beats_per_bar == 4, grid.beats_per_bar
        assert grid.key.startswith("A"), f"key came out {grid.key}"
        assert grid.bar_count >= 6, grid.bar_count
        assert len(grid.grid("1/16")) > len(grid.grid("1/8")) > len(grid.beats)
        near = grid.beats[3] + 0.017
        assert abs(grid.quantize(near, "1/8") - grid.beats[3]) < 1e-6

        # The grid has to span the whole track, not just the stretch
        # where beats were detected. Beat tracking typically starts a
        # beat or two in, but a vocal starts at 0.00 -- and if the grid
        # does not reach back that far, early syllables get measured
        # against a line most of a bar away and a quantizer drags them
        # there. Caught on real speech, where the reported error was
        # 477 ms against a 1/8 grid whose lines are only 341 ms apart.
        for subdivision in ("1/8", "1/16"):
            lines = np.asarray(grid.grid(subdivision))
            step = grid.beat_seconds * {"1/8": 0.5, "1/16": 0.25}[subdivision]
            assert lines[0] <= step, \
                f"{subdivision} grid starts at {lines[0]:.3f}s, not near zero"
            assert lines[-1] >= grid.duration - step * 2, \
                f"{subdivision} grid stops at {lines[-1]:.3f}s of " \
                f"{grid.duration:.3f}s"
            # No moment in the track may sit further than half a
            # subdivision from a line -- that is what "a grid" means.
            probes = np.linspace(0.0, grid.duration, 97)
            worst = max(float(np.min(np.abs(lines - t))) for t in probes)
            assert worst <= step / 2 + 1e-3, \
                f"{subdivision}: a moment sits {worst * 1000:.0f} ms from " \
                f"the nearest line (half a step is {step * 500:.0f} ms)"
        bar, beat_in_bar = grid.position(grid.downbeats[2])
        assert abs(bar - 3.0) < 0.05 and abs(beat_in_bar - 1.0) < 0.05, \
            (bar, beat_in_bar)
        round_trip = beatgrid.BeatGrid.from_json(
            grid.to_json(tmp / "grid.json"))
        assert round_trip.beats == grid.beats

        vocal_src, placed = _build_sloppy_vocal(np, grid, sr, total)
        assert placed > 10, placed
        vocal_path = tmp / "vocal.wav"
        dsp.save(vocal_path, vocal_src, sr)

        # ---- alignment tightens the timing, without moving pitch -------
        loaded, _ = dsp.load(vocal_path, sr)
        aligned, before, after = flow.align_to_grid(loaded, sr, grid, "1/8",
                                                    strength=1.0)
        assert before.onsets, "no syllables detected"
        assert after.tightness > before.tightness + 0.1, \
            f"tightness {before.tightness} -> {after.tightness}"
        f_in = float(np.nanmedian(autotune.track_pitch(loaded, sr).f0))
        f_out = float(np.nanmedian(autotune.track_pitch(aligned, sr).f0))
        drift = abs(1200.0 * np.log2(f_out / f_in))
        assert drift < 60.0, f"the time warp moved pitch {drift:.0f} cents"

        # ---- tuning reduces how off-note it is, without changing length -
        result = autotune.retune(aligned, sr, key=grid.key, preset="hard")
        assert result.after["mean_cents_off"] < result.before["mean_cents_off"]
        assert len(result.audio) == len(aligned)
        bypass = autotune.retune(aligned, sr, preset="off")
        assert np.array_equal(np.asarray(bypass.audio), aligned), \
            "'off' must be a true bypass"
        up = autotune.shift_semitones(aligned, sr, 4.0)
        assert len(up) == len(aligned)
        moved = 1200.0 * np.log2(
            float(np.nanmedian(autotune.track_pitch(up, sr).f0)) / f_out)
        assert abs(moved - 400.0) < 90.0, f"+4 st moved {moved:.0f} cents"

        # ---- keys and scales -------------------------------------------
        assert autotune.parse_key("F# minor") == (6, "minor")
        assert autotune.parse_key("Bb") == (10, "major")
        assert autotune.parse_key("chromatic") == (0, "chromatic")
        assert 60 in autotune.allowed_midi("C major")
        assert 61 not in autotune.allowed_midi("C major")

        # ---- swing delays offbeats and leaves the beats alone ----------
        straight = np.asarray(flow.swung_grid(grid, "1/8", 0.0))
        swung = np.asarray(flow.swung_grid(grid, "1/8", 1 / 3))
        assert np.allclose(straight[0::2], swung[0::2])
        assert np.all(swung[1:-1:2] > straight[1:-1:2])

        # ---- exact bar fitting ------------------------------------------
        four = flow.fit_to_bars(loaded, sr, grid, 4.0)
        assert abs(len(four) / sr - grid.bar_seconds * 4) < 0.05

        # ---- the writing aid --------------------------------------------
        assert flow.count_syllables("rhythm") == 2
        assert flow.count_syllables("fire") == 1
        rows = flow.layout_bars("keep it tight\n" + "syllable " * 20,
                                grid, "1/8")
        assert rows[0]["overfull"] is False and rows[1]["overfull"] is True

        # ---- the desk ----------------------------------------------------
        beat_audio, _ = dsp.load(beat_path, sr)
        mixed, report = mixdown.mix(
            result.audio, beat_audio, sr,
            mixdown.MixSettings(duck_db=4.0, double_track=True, stereo=True))
        assert mixed.ndim == 2 and mixed.shape[1] == 2, mixed.shape
        assert np.isfinite(mixed).all(), "mix produced NaN or inf"
        assert dsp.peak_dbfs(mixed) <= 0.0, report

        # ---- the whole chain, twice, without collision -------------------
        plan = rapkit.TrackPlan(beat=str(beat_path), vocal=str(vocal_path),
                                align_strength=1.0, tune_preset="tight",
                                out_format="wav")
        first = rapkit.produce(plan, tmp / "out", progress=lambda _m: None)
        second = rapkit.produce(plan, tmp / "out", progress=lambda _m: None)
        assert first["run_directory"] != second["run_directory"], \
            "two runs must never share a folder"
        output = Path(first["output"])
        assert output.is_file() and output.stat().st_size > 1000
        assert (first["flow"]["tightness_after"]
                > first["flow"]["tightness_before"])
        for key in ("plan", "beat", "flow", "tune", "mix", "output"):
            assert key in first, key

    print(f"Rap tools selftest OK ({status.detail}) -- "
          f"{grid.describe()}; timing {before.tightness * 100:.0f}% -> "
          f"{after.tightness * 100:.0f}%; off-note "
          f"{result.before['mean_cents_off']:.0f} -> "
          f"{result.after['mean_cents_off']:.0f} cents")
    return True
