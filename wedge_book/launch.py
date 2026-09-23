"""What the launcher's Wedge Method Book tab actually runs.

One entry point, one ``action`` in the ticket, so the tab stays a dropdown
and a button rather than a form somebody has to be taught.
"""

from __future__ import annotations

import json
import os
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from wedge_book import figures, store  # noqa: E402

EDITOR = ROOT / "wedge_method_book_app" / "app.py"


def _ticket() -> dict:
    """The launcher writes a ticket; read it the way the other tools do."""
    for name in ("LAUNCH_TICKET", "DOMESIM_TICKET"):
        raw = os.environ.get(name)
        if raw:
            try:
                return json.loads(raw)
            except json.JSONDecodeError:
                pass
    for candidate in (ROOT / ".launcher_configs" / "wedge_book.json",
                      ROOT / "wedge_book_ticket.json"):
        if candidate.is_file():
            try:
                return json.loads(candidate.read_text(encoding="utf-8"))
            except json.JSONDecodeError:
                pass
    return {}


def status() -> str:
    book = store.load_json()
    lines = [f"THE WEDGE METHOD", f"  {book.progress()}", ""]
    for title, words, done in store.word_counts():
        flag = " " if done else "*"
        lines.append(f" {flag} {title[:46]:<46} {words:>6,} words  "
                     f"{done} sections")
    missing = figures.outstanding()
    lines.append("")
    if missing:
        lines.append(f"  {len(missing)} figures still to render:")
        for key, chapter, title in missing[:10]:
            lines.append(f"    ch{chapter:>2}  {key:<38} {title[:30]}")
    else:
        lines.append(f"  all {len(figures.catalogue())} figures rendered")
    queue = store.unwritten()
    if queue:
        lines.append("")
        lines.append(f"  next to write: {queue[0][3]}")
    return "\n".join(lines)


def main() -> int:
    ticket = _ticket()
    action = str(ticket.get("action") or
                 (sys.argv[1] if len(sys.argv) > 1 else "status")).strip()

    if action == "open_editor":
        if not EDITOR.is_file():
            print(f"editor not found: {EDITOR}")
            return 1
        return subprocess.call([sys.executable, str(EDITOR)],
                               cwd=str(EDITOR.parent))

    if action in ("sync_from_tree", "sync_from_project"):
        direction = ("tree-wins" if action == "sync_from_tree"
                     else "json-wins")
        result = store.sync(direction)
        for key, value in result.items():
            print(f"  {key}: {value}")
        return 0

    if action == "render_figures":
        result = figures.render()
        print(f"  asked {result['asked']}, made {result['made']}")
        if result["returncode"]:
            print(result["stderr"])
            return result["returncode"]
        print(f"  labelled {figures.label()}")
        print(f"  recorded {figures.record()}")
        return 0

    print(status())
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
