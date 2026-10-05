"""Initialise the observer's local store and seed its vocabulary.

    py -3.12 -m intelligence.init

Creates ``.intelligence/`` (database, raw/, logs/), applies the schema, and
imports the action vocabulary from ``.claude/settings.local.json``. Safe to
run again: the schema is idempotent and seeding never resets observed counts.
"""

from __future__ import annotations

from .database import DB_PATH, connect
from .seed_actions import seed


def main() -> int:
    conn = connect()
    try:
        entries = seed(conn)
        total = conn.execute("SELECT COUNT(*) FROM action_vocabulary").fetchone()[0]
    finally:
        conn.close()
    print(f"database  {DB_PATH}")
    print(f"seeded    {entries} vocabulary entries from the permission list ({total} in total)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
