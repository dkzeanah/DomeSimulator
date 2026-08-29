"""Entry point for Local Voice Studio.

Launch and configure this from the consolidated launcher
(``py -3.12 launcher.py``), which exposes the project folder,
self-test, and diagnose actions as GUI fields. Run directly with no
launcher ticket present and it opens the studio's own project GUI with
no project pre-selected.
"""

from __future__ import annotations

import json
import sys
from dataclasses import asdict
from pathlib import Path

import launcher_common as _lc
from .backends import (
    chatterbox_status,
    detect_hardware,
    faster_whisper_status,
)
from .selftest import run_selftest


def main() -> int:
    cfg = _lc.consume_config("local_voice_studio")
    action = cfg.get("action", "run")
    if action == "selftest":
        run_selftest()
        # The rap tools need numpy/librosa, which the dataset workflow
        # above deliberately does not. Run their checks too when those
        # libraries are present, and say so plainly when they are not.
        from .rap_selftest import run_rap_selftest
        run_rap_selftest()
        return 0

    if action == "rap_selftest":
        from .rap_selftest import run_rap_selftest
        return 0 if run_rap_selftest() else 1

    if action == "rap_analyze":
        from . import rapkit
        beat = cfg.get("beat")
        if not beat:
            print("Set 'beat' to the instrumental you want measured.")
            return 2
        grid = rapkit.analyze_beat(
            Path(beat),
            bpm_hint=float(cfg["bpm_hint"]) if cfg.get("bpm_hint") else None,
            beats_per_bar=(int(cfg["beats_per_bar"])
                           if cfg.get("beats_per_bar") else None))
        print(grid.describe())
        print(f"  bar length      {grid.bar_seconds:.4f} s")
        print(f"  first downbeat  {grid.downbeats[0]:.4f} s"
              if grid.downbeats else "  no downbeats found")
        print(f"  beats found     {len(grid.beats)}")
        if cfg.get("grid_json"):
            grid.to_json(Path(cfg["grid_json"]))
            print(f"  wrote {cfg['grid_json']}")
        return 0

    if action == "rap_preview":
        from . import rapkit
        if not (cfg.get("beat") and cfg.get("vocal")):
            print("Set both 'beat' and 'vocal'.")
            return 2
        report = rapkit.preview_flow(
            Path(cfg["vocal"]), Path(cfg["beat"]),
            subdivision=cfg.get("subdivision", "1/8"),
            swing=float(cfg.get("swing", 0.0)))
        print(json.dumps(report, indent=2))
        return 0

    if action == "rap_produce":
        from . import rapkit
        if not (cfg.get("beat") and cfg.get("vocal")):
            print("Set both 'beat' and 'vocal'.")
            return 2
        fields = {f.name for f in
                  __import__("dataclasses").fields(rapkit.TrackPlan)}
        plan = rapkit.TrackPlan(**{k: v for k, v in cfg.items()
                                   if k in fields})
        out_root = Path(cfg.get("out_dir") or "rap_output")
        receipt = rapkit.produce(plan, out_root)
        print()
        print(json.dumps({k: receipt[k] for k in
                          ("run_directory", "output", "beat", "flow", "tune")
                          if k in receipt}, indent=2))
        return 0
    if action == "diagnose":
        chatterbox = chatterbox_status()
        whisper = faster_whisper_status()
        payload = {
            "python_executable": sys.executable,
            "hardware": asdict(detect_hardware()),
            "chatterbox": asdict(chatterbox),
            "faster_whisper": asdict(whisper),
        }
        print(json.dumps(payload, indent=2))
        if not chatterbox.ready or not whisper.ready:
            print()
            print("Not ready above? Install the missing backend(s) into a")
            print("dedicated environment this program picks up automatically:")
            print("  local_voice_studio/setup-windows.ps1 -WithLocalAI")
            print("(creates .venv-voice with chatterbox-tts + faster-whisper,")
            print("used regardless of which Python started the launcher.)")
        return 0
    from .gui import launch

    project = cfg.get("project")
    launch(Path(project) if project else None)
    return 0
