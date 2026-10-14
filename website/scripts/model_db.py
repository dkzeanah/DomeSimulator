"""The database, modelled first in plain SQLite.

D1 is SQLite at the edge, so the model is the real thing: this applies every migration in
migrations/ in order to a fresh file, db/model.sqlite, checks it, and writes db/SCHEMA.md --
every table, column and relationship in words. Open model.sqlite in any SQLite browser to
see the catalogue and the empty tables exactly as the live site starts.

The checks are the catalogue's rules, so a bad price row fails here before it ships:
  * foreign keys and integrity hold;
  * every product that is shown has at least one active price;
  * an honor-system price says what the buyer must describe;
  * a physical product says where it ships and what the buyer is promised;
  * a digital product that is sold names its file.

    py -3.12 scripts/model_db.py
"""

from __future__ import annotations

import sqlite3
import sys
from pathlib import Path

SITE = Path(__file__).resolve().parent.parent
MIGRATIONS = SITE / "migrations"
OUT = SITE / "db"


def build(path: Path) -> sqlite3.Connection:
    if path.exists():
        path.unlink()
    db = sqlite3.connect(path)
    db.execute("PRAGMA foreign_keys = ON")
    for m in sorted(MIGRATIONS.glob("*.sql")):
        db.executescript(m.read_text(encoding="utf-8"))
    db.commit()
    return db


def check(db: sqlite3.Connection) -> list[str]:
    problems = []
    if db.execute("PRAGMA integrity_check").fetchone()[0] != "ok":
        problems.append("integrity_check failed")
    for row in db.execute("PRAGMA foreign_key_check"):
        problems.append(f"foreign key broken: {row}")
    for slug, in db.execute("SELECT slug FROM products WHERE status != 'hidden' AND slug NOT IN "
                            "(SELECT product FROM prices WHERE active = 1)"):
        problems.append(f"{slug}: shown but has no active price")
    for product, key in db.execute("SELECT product, key FROM prices WHERE honor = 1 AND COALESCE(honor_prompt, '') = ''"):
        problems.append(f"{product}/{key}: honor price without a prompt")
    for slug, in db.execute("SELECT slug FROM products WHERE kind = 'physical' AND "
                            "(COALESCE(ship_countries, '') = '' OR COALESCE(ships_note, '') = '')"):
        problems.append(f"{slug}: physical but no ship_countries / ships_note")
    for slug, in db.execute("SELECT p.slug FROM products p JOIN prices r ON r.product = p.slug "
                            "WHERE p.kind = 'digital' AND COALESCE(p.file_key, '') = '' GROUP BY p.slug"):
        problems.append(f"{slug}: digital but no file_key")
    return problems


def schema_md(db: sqlite3.Connection) -> str:
    lines = ["# The zeanahlab.com database", "",
             "Written by `scripts/model_db.py` from `migrations/` -- do not edit. "
             "`model.sqlite` beside this file is the same database, built fresh.", ""]
    tables = [r[0] for r in db.execute("SELECT name FROM sqlite_master WHERE type = 'table' "
                                       "AND name NOT LIKE 'sqlite_%' AND name NOT LIKE 'd1_%' ORDER BY name")]
    for t in tables:
        lines += [f"## {t}", "", "| column | type | null | default | key |", "| --- | --- | --- | --- | --- |"]
        fks = {r[3]: f"-> {r[2]}.{r[4]}" for r in db.execute(f"PRAGMA foreign_key_list({t})")}
        for cid, name, typ, notnull, default, pk in db.execute(f"PRAGMA table_info({t})"):
            key = "PK" if pk else fks.get(name, "")
            lines.append(f"| {name} | {typ} | {'' if notnull else 'yes'} | {default if default is not None else ''} | {key} |")
        n = db.execute(f"SELECT COUNT(*) FROM {t}").fetchone()[0]
        lines += ["", f"{n} row(s) in the model.", ""]
    lines += ["## The catalogue as seeded", "", "| product | kind | status | price | amount | honor |", "| --- | --- | --- | --- | --- | --- |"]
    for slug, kind, status, key, cents, honor in db.execute(
            "SELECT p.slug, p.kind, p.status, r.key, r.amount_cents, r.honor FROM products p "
            "JOIN prices r ON r.product = p.slug ORDER BY p.sort, r.sort"):
        lines.append(f"| {slug} | {kind} | {status} | {key} | ${cents / 100:,.2f} | {'yes' if honor else ''} |")
    return "\n".join(lines) + "\n"


def main() -> int:
    OUT.mkdir(exist_ok=True)
    db = build(OUT / "model.sqlite")
    problems = check(db)
    (OUT / "SCHEMA.md").write_text(schema_md(db), encoding="utf-8")
    db.close()
    if problems:
        print("model has problems:\n  " + "\n  ".join(problems))
        return 1
    print(f"model ok: {OUT.relative_to(SITE)}/model.sqlite and SCHEMA.md")
    return 0


if __name__ == "__main__":
    sys.exit(main())
