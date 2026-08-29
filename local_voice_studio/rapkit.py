"""The whole chain in one call: beat in, vocal in, finished track out.

Order matters and is fixed here so results are reproducible:

1. **Read the beat** -- tempo, grid, bar lines, key (:mod:`beatgrid`).
2. **Place the vocal in time** -- syllables onto the grid (:mod:`flow`).
   This happens *before* tuning, because warping changes which pitch
   lands where, and tuning a take that is about to be moved wastes the
   work.
3. **Tune the vocal** -- into the beat's own key unless told otherwise
   (:mod:`autotune`).
4. **Mix** -- levels, ducking, doubling, limiting (:mod:`mixdown`).

Every run writes to a fresh, uniquely named folder and never overwrites
a previous one, and drops a JSON receipt recording every setting and
every measured number, so a mix can be explained after the fact.
"""

from __future__ import annotations

import json
import uuid
from dataclasses import dataclass, asdict, field
from datetime import datetime
from pathlib import Path

from . import autotune, beatgrid, dsp, flow, mixdown


@dataclass
class TrackPlan:
    """Everything a run needs. Serializes straight to the receipt."""

    beat: str = ""
    vocal: str = ""

    # Rhythm
    subdivision: str = "1/8"
    align_strength: float = 0.85     # 0 = leave the timing alone
    swing: float = 0.0
    max_shift_ms: float = 140.0
    fit_bars: float = 0.0            # >0 forces the take to N bars first

    # Pitch
    tune_preset: str = "tight"       # see autotune.PRESETS
    key: str = ""                    # blank = use the key detected in the beat
    transpose: float = 0.0           # semitones, applied after tuning
    pitch_method: str = "yin"

    # Desk
    vocal_db: float = -12.0
    beat_db: float = -16.0
    offset_bars: float = 0.0         # start the vocal N bars into the beat
    duck_db: float = 3.0
    double_track: bool = True
    stereo: bool = True

    # Output
    out_format: str = "wav"          # wav | mp3
    keep_stems: bool = True

    def mix_settings(self, bar_seconds: float) -> mixdown.MixSettings:
        return mixdown.MixSettings(
            vocal_db=self.vocal_db, beat_db=self.beat_db,
            offset_s=self.offset_bars * bar_seconds,
            duck_db=self.duck_db, double_track=self.double_track,
            stereo=self.stereo)


def _run_dir(root: Path, label: str) -> Path:
    stamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    path = Path(root) / f"{label}_{stamp}_{uuid.uuid4().hex[:6]}"
    path.mkdir(parents=True, exist_ok=False)
    return path


def analyze_beat(path: Path, bpm_hint: float | None = None,
                 beats_per_bar: int | None = None) -> beatgrid.BeatGrid:
    """Just the beat analysis, for the 'what is this track?' button."""
    return beatgrid.analyze(Path(path), bpm_hint=bpm_hint,
                            beats_per_bar=beats_per_bar)


def produce(plan: TrackPlan, out_root: Path,
            progress=print, sample_rate: int = dsp.MUSIC_RATE) -> dict:
    """Run the full chain. Returns the receipt dict."""
    dsp.require()
    import numpy as np

    beat_path = Path(plan.beat)
    vocal_path = Path(plan.vocal)
    for label, path in (("beat", beat_path), ("vocal", vocal_path)):
        if not path.is_file():
            raise FileNotFoundError(f"{label} file not found: {path}")

    run = _run_dir(Path(out_root), "track")
    receipt: dict = {"run_directory": str(run), "plan": asdict(plan),
                     "created_at": datetime.now().isoformat(timespec="seconds")}

    progress("Reading the beat ...")
    grid = beatgrid.analyze(beat_path, sample_rate=sample_rate)
    grid.to_json(run / "beatgrid.json")
    receipt["beat"] = {
        "bpm": grid.bpm, "beats_per_bar": grid.beats_per_bar,
        "bars": grid.bar_count, "key": grid.key,
        "key_confidence": grid.key_confidence,
        "steadiness": grid.steadiness, "summary": grid.describe(),
    }
    progress(f"  {grid.describe()}")

    beat_audio, _ = dsp.load(beat_path, sample_rate)
    vocal, _ = dsp.load(vocal_path, sample_rate)
    receipt["vocal_in"] = {"seconds": round(len(vocal) / sample_rate, 3)}

    if plan.fit_bars and plan.fit_bars > 0:
        progress(f"Fitting the take to {plan.fit_bars:g} bars ...")
        vocal = flow.fit_to_bars(vocal, sample_rate, grid, plan.fit_bars)

    if plan.align_strength > 0:
        progress(f"Aligning syllables to the {plan.subdivision} grid ...")
        vocal, before, after = flow.align_to_grid(
            vocal, sample_rate, grid, plan.subdivision,
            strength=plan.align_strength, swing=plan.swing,
            max_shift_ms=plan.max_shift_ms)
        receipt["flow"] = {"before": before.describe(),
                           "after": after.describe(),
                           "tightness_before": before.tightness,
                           "tightness_after": after.tightness,
                           "syllables": len(before.onsets)}
        progress(f"  tightness {before.tightness * 100:.0f}% -> "
                 f"{after.tightness * 100:.0f}%")
        if plan.keep_stems:
            dsp.save(run / "vocal_aligned.wav", vocal, sample_rate)

    key = plan.key or grid.key or "chromatic"
    if plan.tune_preset and plan.tune_preset != "off":
        progress(f"Tuning to {key} ({plan.tune_preset}) ...")
        result = autotune.retune(vocal, sample_rate, key=key,
                                 preset=plan.tune_preset,
                                 method=plan.pitch_method)
        vocal = result.audio
        receipt["tune"] = {"key": key, "preset": plan.tune_preset,
                           "before": result.before, "after": result.after,
                           "summary": result.report()}
        progress(f"  {result.report()}")
        if plan.keep_stems:
            dsp.save(run / "vocal_tuned.wav", vocal, sample_rate)

    if abs(plan.transpose) > 1e-6:
        progress(f"Transposing {plan.transpose:+g} semitones ...")
        vocal = autotune.shift_semitones(vocal, sample_rate, plan.transpose,
                                         method=plan.pitch_method)

    progress("Mixing ...")
    audio, mix_report = mixdown.mix(vocal, beat_audio, sample_rate,
                                    plan.mix_settings(grid.bar_seconds))
    receipt["mix"] = mix_report

    suffix = ".mp3" if plan.out_format.lower() == "mp3" else ".wav"
    out_path = run / f"track{suffix}"
    if suffix == ".wav":
        dsp.save(out_path, audio, sample_rate)
    else:
        dsp.save_compressed(out_path, audio, sample_rate)
    receipt["output"] = str(out_path)
    progress(f"Saved {out_path}")

    # A click track makes it possible to check the grid by ear.
    if plan.keep_stems:
        dsp.save(run / "click.wav",
                 beatgrid.click_track(grid, plan.subdivision, sample_rate),
                 sample_rate)

    (run / "receipt.json").write_text(
        json.dumps(receipt, indent=2), encoding="utf-8")
    return receipt


def preview_flow(vocal_path: Path, beat_path: Path,
                 subdivision: str = "1/8", swing: float = 0.0,
                 sample_rate: int = dsp.MUSIC_RATE) -> dict:
    """Measure a take against a beat without rendering anything.

    The 'am I even close?' check -- fast, non-destructive, and the thing
    to run before deciding how hard to quantize.
    """
    grid = beatgrid.analyze(Path(beat_path), sample_rate=sample_rate)
    vocal, _ = dsp.load(Path(vocal_path), sample_rate)
    analysis = flow.analyze(vocal, sample_rate, grid, subdivision, swing)
    track = autotune.track_pitch(vocal, sample_rate)
    return {
        "beat": grid.describe(),
        "bpm": grid.bpm,
        "key": grid.key,
        "flow": analysis.describe(),
        "tightness": analysis.tightness,
        "syllables_per_bar": analysis.syllables_per_bar,
        "late_fraction": analysis.late_fraction,
        "pitch": track.summary(),
    }
