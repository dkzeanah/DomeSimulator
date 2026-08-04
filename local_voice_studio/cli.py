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
