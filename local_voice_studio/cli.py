"""Entry point for Local Voice Studio.

Launch and configure this from the consolidated launcher
(``py -3.12 launcher.py``), which exposes the project folder,
self-test, and diagnose actions as GUI fields. Run directly with no
launcher ticket present and it opens the studio's own project GUI with
no project pre-selected.
"""

from __future__ import annotations

import json
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
        payload = {
            "hardware": asdict(detect_hardware()),
            "chatterbox": asdict(chatterbox_status()),
            "faster_whisper": asdict(faster_whisper_status()),
        }
        print(json.dumps(payload, indent=2))
        return 0
    from .gui import launch

    project = cfg.get("project")
    launch(Path(project) if project else None)
    return 0
