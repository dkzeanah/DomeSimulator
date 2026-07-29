"""Command line entry point for Local Voice Studio."""

from __future__ import annotations

import argparse
import json
from dataclasses import asdict
from pathlib import Path

from .backends import (
    chatterbox_status,
    detect_hardware,
    faster_whisper_status,
)
from .selftest import run_selftest


def parser() -> argparse.ArgumentParser:
    result = argparse.ArgumentParser(
        description="Local recording, dataset, voice-profile, and synthesis studio"
    )
    result.add_argument("--project", type=Path, help="open a project directory")
    result.add_argument(
        "--selftest",
        action="store_true",
        help="run core checks without optional ML packages",
    )
    result.add_argument(
        "--diagnose",
        action="store_true",
        help="print hardware and backend readiness as JSON",
    )
    return result


def main(argv: list[str] | None = None) -> int:
    args = parser().parse_args(argv)
    if args.selftest:
        run_selftest()
        return 0
    if args.diagnose:
        payload = {
            "hardware": asdict(detect_hardware()),
            "chatterbox": asdict(chatterbox_status()),
            "faster_whisper": asdict(faster_whisper_status()),
        }
        print(json.dumps(payload, indent=2))
        return 0
    from .gui import launch

    launch(args.project)
    return 0
