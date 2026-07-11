"""
Flatten the entire project into a single file for uploading to LLMs.

Run:
    py -3.12 flatten.py            -> writes dome_flat.md
    py -3.12 flatten.py out.txt    -> custom output name

The output contains every source file, each preceded by a clear
======== FILE: path ======== marker, plus a table of contents with line
counts, so a model (or a human) can navigate the whole codebase from
one upload. Generated artifacts, caches, and the flat file itself are
excluded.
"""

from __future__ import annotations

import sys
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).parent
DEFAULT_OUTPUT = "dome_flat.md"

INCLUDE_SUFFIXES = {".py", ".md", ".json", ".txt", ".toml", ".cfg"}
EXCLUDE_DIRS = {"__pycache__", ".git", ".claude", ".venv", "venv",
                "node_modules"}
EXCLUDE_FILES = {DEFAULT_OUTPUT, "dome_flat.txt", "dome_bom.txt",
                 "dome_design.json"}

# Read order: overview first, then the code in dependency order.
PRIORITY = ["README.md", "materials.py", "workshop.py", "presets.py",
            "dome_model.py", "mesh_builder.py", "electrical.py",
            "vision.py", "overlay_ui.py", "dome_creator.py",
            "flatten.py"]


def gather_files() -> list[Path]:
    files = []
    for path in sorted(ROOT.rglob("*")):
        if not path.is_file():
            continue
        if path.suffix.lower() not in INCLUDE_SUFFIXES:
            continue
        if path.name in EXCLUDE_FILES:
            continue
        if any(part in EXCLUDE_DIRS for part in path.parts):
            continue
        files.append(path)

    def order(path: Path) -> tuple:
        rel = str(path.relative_to(ROOT)).replace("\\", "/")
        try:
            return (0, PRIORITY.index(rel))
        except ValueError:
            return (1, rel)

    return sorted(files, key=order)


def main() -> None:
    output = ROOT / (sys.argv[1] if len(sys.argv) > 1 else DEFAULT_OUTPUT)
    files = gather_files()

    sections = []
    toc = []
    total_lines = 0
    for path in files:
        rel = str(path.relative_to(ROOT)).replace("\\", "/")
        text = path.read_text(encoding="utf-8", errors="replace")
        lines = text.count("\n") + 1
        total_lines += lines
        toc.append(f"- {rel}  ({lines} lines)")
        lang = {".py": "python", ".md": "markdown",
                ".json": "json"}.get(path.suffix.lower(), "")
        sections.append(
            f"\n\n{'=' * 74}\n"
            f"======== FILE: {rel} ========\n"
            f"{'=' * 74}\n\n"
            f"```{lang}\n{text.rstrip()}\n```"
        )

    stamp = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC")
    header = (
        "# Geodesic Dome Creator — flattened project\n\n"
        f"Generated {stamp} by flatten.py. "
        f"{len(files)} files, {total_lines:,} lines total.\n\n"
        "Each file below is delimited by a `======== FILE: path "
        "========` marker.\n\n"
        "## Table of contents\n\n" + "\n".join(toc)
    )

    output.write_text(header + "".join(sections), encoding="utf-8")
    size_kb = output.stat().st_size / 1024
    print(f"Wrote {output.name}: {len(files)} files, "
          f"{total_lines:,} lines, {size_kb:,.0f} KB")


if __name__ == "__main__":
    main()
