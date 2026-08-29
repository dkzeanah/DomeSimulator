"""Render every ```mermaid block in docs/ to an SVG beside the document.

Mermaid already renders natively on GitHub and in most Markdown viewers,
so this is only needed when you want image files -- for slides, for a
README that has to work offline, or to drop a diagram into a video.

Setup, once:

    npm install

That puts ``@mermaid-js/mermaid-cli`` in ``node_modules``.  It needs a
Chromium to rasterise with; rather than downloading a second browser,
``.puppeteerrc.json`` points it at the Chrome already installed on this
machine.  If that path is wrong on yours, edit that file -- it is two
lines -- or run ``npx puppeteer browsers install chrome`` to fetch one.
"""

from __future__ import annotations

import argparse
import re
import shutil
import subprocess
import sys
from pathlib import Path


DOCS = Path("docs")
OUTPUT = DOCS / "diagrams"
PUPPETEER_CONFIG = Path(".puppeteerrc.json")

BLOCK = re.compile(r"^```mermaid\s*$(.*?)^```\s*$", re.M | re.S)
HEADING = re.compile(r"^#{1,6}\s+(.+?)\s*$", re.M)


def _slug(text: str) -> str:
    text = re.sub(r"[^A-Za-z0-9]+", "-", text).strip("-").lower()
    return text or "diagram"


def _nearest_heading(source: str, position: int) -> str:
    """The last heading before this block, which names it usefully."""
    best = "diagram"
    for match in HEADING.finditer(source):
        if match.start() > position:
            break
        best = match.group(1)
    return best


def extract(document: Path) -> list[tuple[str, str]]:
    """Return (name, mermaid source) for every fenced block."""
    source = document.read_text(encoding="utf-8")
    found: list[tuple[str, str]] = []
    seen: dict[str, int] = {}
    for match in BLOCK.finditer(source):
        heading = _nearest_heading(source, match.start())
        name = f"{document.stem}-{_slug(heading)}"
        seen[name] = seen.get(name, 0) + 1
        if seen[name] > 1:
            name = f"{name}-{seen[name]}"
        found.append((name, match.group(1).strip()))
    return found


def render(
    documents: list[Path],
    output: Path = OUTPUT,
    fmt: str = "svg",
    theme: str = "dark",
    background: str = "transparent",
) -> int:
    # Call the CLI's entry script with node directly. Going through npx
    # means a .cmd shim on Windows, which CreateProcess cannot launch by
    # bare name and which mangles the argument list when given a full
    # path -- two failures for no benefit, since the package is local.
    node = shutil.which("node")
    if node is None:
        print("node not found; install Node.js, then run: npm install")
        return 1
    cli = Path("node_modules/@mermaid-js/mermaid-cli/src/cli.js")
    if not cli.is_file():
        print("mermaid-cli is not installed. Run:  npm install")
        return 1

    output.mkdir(parents=True, exist_ok=True)
    scratch = output / ".mmd"
    scratch.mkdir(exist_ok=True)

    total = 0
    failed: list[str] = []
    for document in documents:
        blocks = extract(document)
        if not blocks:
            continue
        print(f"{document}: {len(blocks)} diagram(s)")
        for name, body in blocks:
            source = scratch / f"{name}.mmd"
            source.write_text(body + "\n", encoding="utf-8")
            target = output / f"{name}.{fmt}"
            command = [
                node, str(cli),
                "-i", str(source), "-o", str(target),
                "-t", theme, "-b", background,
            ]
            if PUPPETEER_CONFIG.is_file():
                command += ["-p", str(PUPPETEER_CONFIG)]
            result = subprocess.run(command, capture_output=True, text=True)
            if result.returncode != 0 or not target.is_file():
                failed.append(name)
                tail = (result.stderr or result.stdout).strip().splitlines()
                print(f"  FAILED {name}: {tail[-1] if tail else 'no output'}")
            else:
                total += 1
                print(f"  {target}")

    shutil.rmtree(scratch, ignore_errors=True)
    print()
    if failed:
        print(f"{total} rendered, {len(failed)} failed: {', '.join(failed)}")
        return 1
    print(f"{total} diagram(s) rendered into {output}")
    return 0


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("documents", nargs="*", type=Path,
                        help="Markdown files (default: every .md in docs/)")
    parser.add_argument("--format", default="svg", choices=("svg", "png", "pdf"))
    parser.add_argument("--theme", default="dark",
                        choices=("dark", "default", "forest", "neutral"))
    parser.add_argument("--background", default="transparent")
    parser.add_argument("--output", type=Path, default=OUTPUT)
    args = parser.parse_args()

    documents = args.documents or sorted(DOCS.glob("*.md"))
    if not documents:
        print(f"no Markdown found in {DOCS}")
        return 2
    return render(documents, args.output, args.format, args.theme,
                  args.background)


if __name__ == "__main__":
    raise SystemExit(main())
