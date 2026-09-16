"""Maintenance: reconstruct pristine pre-agent snapshots of the three
registration files by reversing the agent's known insertions.

The recipe machinery edits exactly three files with known shapes:
``lesson_registry.py`` (one import + one tuple entry per lesson),
``deliverables.py`` (one Deliverable block per lesson),
``render_presets.py`` (one _video block per lesson).  Reversing those
insertions reproduces the pre-agent state exactly — no git needed.

    py -3.12 -m project_agent.pristine
"""

from __future__ import annotations

import re
from pathlib import Path

from . import config

AGENT_KEYS = ("pvtwo", "harvest", "pine_value", "why_build")


def reverse_registry(text: str) -> str:
    for key in AGENT_KEYS:
        text = text.replace(f"from .lesson_{key} import {key.upper()}_LESSON\n", "")
        text = text.replace(f",\n                   {key.upper()}_LESSON", "")
    return text


def reverse_deliverables(text: str) -> str:
    pattern = re.compile(
        r'\n    Deliverable\("(' + "|".join(AGENT_KEYS) + r')".*?compose=True\),',
        re.DOTALL)
    return pattern.sub("", text)


def reverse_presets(text: str) -> str:
    pattern = re.compile(
        r'\n    _video\("(' + "|".join(AGENT_KEYS) + r')".*?"\),',
        re.DOTALL)
    return pattern.sub("", text)


def main() -> int:
    jobs = [
        (config.REPO_ROOT / "two_v_demo" / "lesson_registry.py",
         reverse_registry),
        (config.REPO_ROOT / "two_v_demo" / "deliverables.py",
         reverse_deliverables),
        (config.REPO_ROOT / "render_presets.py", reverse_presets),
    ]
    for path, reverse in jobs:
        current = path.read_text(encoding="utf-8")
        pristine = reverse(current)
        target = path.with_name(path.name + ".agent-bak-pristine")
        target.write_text(pristine, encoding="utf-8")
        print(f"wrote {target.name} ({len(pristine)} bytes, "
              f"{len(current) - len(pristine)} bytes of agent edits reversed)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
