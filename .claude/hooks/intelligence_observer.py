"""Claude Code hook: hand one event to the Project Intelligence Observer.

Registered in .claude/settings.json for SessionStart, UserPromptSubmit,
PreToolUse, PostToolUse, PostToolUseFailure, Stop and SessionEnd.

It is a recorder, never a gate. Whatever happens it:
  * prints nothing to stdout or stderr (stdout from some events would be
    added to Claude's context; this hook must add nothing);
  * exits 0 (exit 2 would block a tool or a prompt);
  * logs its own failures to .intelligence/logs/observer.log and moves on.
"""

import io
import json
import os
import sys
import time
import traceback
from pathlib import Path

PROJECT_ROOT = Path(os.environ.get("CLAUDE_PROJECT_DIR") or Path(__file__).resolve().parents[2])
LOG_FILE = PROJECT_ROOT / ".intelligence" / "logs" / "observer.log"


def _log(message: str) -> None:
    """Append one line to the observer's own log; swallow any failure."""
    try:
        LOG_FILE.parent.mkdir(parents=True, exist_ok=True)
        with open(LOG_FILE, "a", encoding="utf-8") as handle:
            handle.write(f"{time.strftime('%Y-%m-%dT%H:%M:%S')} {message}\n")
    except Exception:
        pass


def main() -> None:
    # Silence both streams for the whole run: nothing may reach Claude.
    real_out, real_err = sys.stdout, sys.stderr
    sys.stdout = sys.stderr = io.StringIO()
    started = time.perf_counter()
    name = "?"
    try:
        raw = sys.stdin.buffer.read()
        if not raw.strip():
            return
        event = json.loads(raw.decode("utf-8-sig", errors="replace"))   # tolerate a BOM
        if not isinstance(event, dict):
            return
        name = event.get("hook_event_name", "?")
        sys.path.insert(0, str(PROJECT_ROOT))
        from intelligence.observer import record
        record(event)
        elapsed = (time.perf_counter() - started) * 1000
        if elapsed > 2000:                   # worth knowing if the hook ever gets slow
            _log(f"slow {name}: {elapsed:.0f} ms")
    except BaseException:                    # including SystemExit/KeyboardInterrupt
        _log(f"error in {name}:\n{traceback.format_exc()}")
    finally:
        sys.stdout, sys.stderr = real_out, real_err


if __name__ == "__main__":
    try:
        main()
    finally:
        os._exit(0)                          # always succeed, whatever happened above
