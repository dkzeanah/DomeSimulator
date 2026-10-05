"""Where the dataset lives, and how to open it.

The data directory ``.intelligence/`` sits at the project root and is
gitignored; the source in ``intelligence/`` is not.  Every connection runs in
WAL mode with a busy timeout, because Claude Code can fire hooks for parallel
tool calls at the same moment and each hook is its own process.
"""

from __future__ import annotations

import os
import sqlite3
from datetime import datetime, timezone
from pathlib import Path

#: The repository root: the parent of this package.
PROJECT_ROOT = Path(__file__).resolve().parents[1]
#: Generated, local-only data.
DATA_DIR = PROJECT_ROOT / ".intelligence"
DB_PATH = DATA_DIR / "intelligence.sqlite3"
RAW_DIR = DATA_DIR / "raw"
LOG_DIR = DATA_DIR / "logs"
SCHEMA_PATH = Path(__file__).with_name("schema.sql")

#: Milliseconds a writer waits for a lock held by a concurrent hook.
BUSY_TIMEOUT_MS = 5000


def now() -> str:
    """UTC timestamp with milliseconds, ISO 8601."""
    return datetime.now(timezone.utc).isoformat(timespec="milliseconds")


def ensure_dirs() -> None:
    """Create the data directories if they are missing."""
    for path in (DATA_DIR, RAW_DIR, LOG_DIR):
        path.mkdir(parents=True, exist_ok=True)


def connect(path: Path | None = None, init: bool = True) -> sqlite3.Connection:
    """Open the store. ``init`` applies the (idempotent) schema first.

    The environment variable INTELLIGENCE_DB overrides the path, which is how
    tests run against a scratch database instead of the real one."""
    ensure_dirs()
    target = Path(path or os.environ.get("INTELLIGENCE_DB") or DB_PATH)
    conn = sqlite3.connect(str(target), timeout=BUSY_TIMEOUT_MS / 1000)
    conn.row_factory = sqlite3.Row
    conn.execute(f"PRAGMA busy_timeout = {BUSY_TIMEOUT_MS}")
    conn.execute("PRAGMA journal_mode = WAL")
    conn.execute("PRAGMA synchronous = NORMAL")
    if init:
        apply_schema(conn)
    return conn


def apply_schema(conn: sqlite3.Connection) -> None:
    """Run schema.sql. Every statement in it is IF NOT EXISTS."""
    conn.executescript(SCHEMA_PATH.read_text(encoding="utf-8"))


def init_db() -> Path:
    """Create the database and its directories; return the database path."""
    conn = connect()
    conn.close()
    return DB_PATH


if __name__ == "__main__":
    print(init_db())
