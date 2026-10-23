"""The staging site: its own database and file store, and a fresh copy of live data on demand.

    py -3.12 scripts/staging.py setup
        Once. Creates the staging database (D1 zeanahlab-staging) and file store (R2
        zeanahlab-books-staging) if they are missing, writes the database's id into
        wrangler.toml, puts the books in the staging store, and prints the two Preview secrets
        to paste into Cloudflare (this wrangler cannot set Preview secrets itself).

    py -3.12 scripts/staging.py refresh
        Replace the staging database with a copy of the live one, then apply any migrations the
        staging branch has that live does not: the same thing "Promote to live" will do to the
        live database, rehearsed on real data. Reads live; never writes to it.

    py -3.12 scripts/staging.py refresh --local
        The same rehearsal on this computer's two local databases (npm run db:local's and
        staging's), touching nothing online.

The live export holds customers' emails, so it is written to website/private/staging/
(gitignored) and deleted once it is imported, unless --keep.

What staging must never do, and why it cannot:
  * send mail -- the mail program collects only with MAILER_TOKEN, and staging has none;
  * charge a card -- staging has no Stripe keys and runs checkout in test mode;
  * call out -- webhook automations copied from live are switched off on every refresh;
  * run the clock -- the ops Worker knocks only on the live site.
Book PDFs are copied by `setup`; story narration and cut-list PDFs in live R2 are not, so on
staging those play or download only once re-made there.
"""

from __future__ import annotations

import argparse
import datetime as dt
import json
import re
import secrets
import shutil
import subprocess
import sys
from pathlib import Path

SITE = Path(__file__).resolve().parent.parent
TOML = SITE / "wrangler.toml"
PRIVATE = SITE / "private" / "staging"
LIVE_DB, STAGING_DB = "zeanahlab", "zeanahlab-staging"
STAGING_BUCKET = "zeanahlab-books-staging"
PLACEHOLDER = "00000000-0000-0000-0000-000000000000"

# After every refresh: nothing on staging may reach the outside world.
AFTER_REFRESH = """
UPDATE automations SET active = 0 WHERE actions LIKE '%"webhook"%';
"""


def wrangler(*args: str, capture: bool = True, check: bool = True) -> str:
    npx = shutil.which("npx") or shutil.which("npx.cmd")
    if not npx:
        sys.exit("npx not found: install Node.js 20+")
    r = subprocess.run([npx, "wrangler", *args], cwd=SITE, capture_output=capture, text=True, encoding="utf-8", errors="replace")
    if check and r.returncode:
        sys.exit(f"wrangler {' '.join(args)} failed:\n{(r.stdout or '')[-2000:]}\n{(r.stderr or '')[-2000:]}")
    return r.stdout or ""


def where(local: bool) -> list[str]:
    return ["--local"] if local else ["--remote"]


def query(db: str, sql: str, local: bool, staging: bool) -> list[dict]:
    out = wrangler("d1", "execute", db, *where(local), *(["--env", "preview"] if staging else []), "--json", "--command", sql)
    data = json.loads(out[out.index("["):])
    return data[0]["results"]


def staging_id_in_toml() -> str:
    m = re.search(r'database_name = "zeanahlab-staging"\s*\n# [^\n]*\ndatabase_id = "([^"]+)"', TOML.read_text(encoding="utf-8"))
    if not m:
        sys.exit("wrangler.toml has no [env.preview] database for zeanahlab-staging")
    return m.group(1)


def setup() -> None:
    dbs = json.loads(wrangler("d1", "list", "--json"))
    found = next((d for d in dbs if d.get("name") == STAGING_DB), None)
    if found:
        print(f"database {STAGING_DB} exists: {found['uuid']}")
    else:
        out = wrangler("d1", "create", STAGING_DB)
        m = re.search(r'"?database_id"?\s*[=:]\s*"([0-9a-f-]{36})"', out)
        if not m:
            sys.exit(f"created {STAGING_DB} but could not read its id:\n{out}")
        found = {"uuid": m.group(1)}
        print(f"created database {STAGING_DB}: {found['uuid']}")
    text = TOML.read_text(encoding="utf-8")
    if PLACEHOLDER in text:
        TOML.write_text(text.replace(PLACEHOLDER, found["uuid"]), encoding="utf-8")
        print("wrote its id into wrangler.toml -- commit that change")
    elif staging_id_in_toml() != found["uuid"]:
        sys.exit(f"wrangler.toml names a different staging database id than Cloudflare ({found['uuid']}); fix it by hand")
    buckets = wrangler("r2", "bucket", "list")
    if re.search(rf"name:\s+{re.escape(STAGING_BUCKET)}\b", buckets):
        print(f"file store {STAGING_BUCKET} exists")
    else:
        wrangler("r2", "bucket", "create", STAGING_BUCKET, capture=False)
        print(f"created file store {STAGING_BUCKET}")
    print("putting the books in the staging file store ...")
    r = subprocess.run([sys.executable, str(SITE / "scripts" / "upload_books.py"), "--remote", "--bucket", STAGING_BUCKET], cwd=SITE)
    if r.returncode:
        sys.exit("uploading the books failed")
    print("\nNow, in Cloudflare: Workers & Pages -> zeanahlab -> Settings -> Variables and Secrets.")
    print("Switch the environment to PREVIEW and add exactly these two secrets (nothing else):")
    print(f"  SESSION_SECRET = {secrets.token_urlsafe(48)}")
    print("  ADMIN_EMAILS   = the email you sign in with")
    print("If any Stripe, MAILER_TOKEN or OPS_TOKEN value is listed under Preview, delete it there.")


def refresh(local: bool, keep: bool) -> None:
    if not local and staging_id_in_toml() == PLACEHOLDER:
        sys.exit("Run `py -3.12 scripts/staging.py setup` first: the staging database does not exist yet.")
    PRIVATE.mkdir(parents=True, exist_ok=True)
    dump = PRIVATE / f"live-{dt.datetime.now().strftime('%Y%m%d-%H%M%S')}.sql"
    print(f"1/4 copying the {'local' if local else 'live'} database (read only) ...", flush=True)
    wrangler("d1", "export", LIVE_DB, *where(local), "--output", str(dump))
    try:
        print("2/4 emptying the staging database ...", flush=True)
        # newest first, so a table is dropped before the tables its foreign keys point at
        tables = [r["name"] for r in query(STAGING_DB, "SELECT name FROM sqlite_master WHERE type = 'table' "
                                           "AND name NOT LIKE 'sqlite_%' AND name NOT LIKE '_cf_%' ORDER BY rowid DESC", local, True)]
        if tables:
            drop = PRIVATE / "drop.sql"
            drop.write_text("PRAGMA defer_foreign_keys = true;\n" + "".join(f'DROP TABLE IF EXISTS "{t}";\n' for t in tables), encoding="utf-8")
            wrangler("d1", "execute", STAGING_DB, *where(local), "--env", "preview", "--file", str(drop), "--yes")
            drop.unlink()
        print(f"3/4 loading the copy ({dump.stat().st_size / 1e6:.1f} MB) ...", flush=True)
        wrangler("d1", "execute", STAGING_DB, *where(local), "--env", "preview", "--file", str(dump), "--yes")
        print("4/4 applying staging's newer migrations and switching off anything that calls out ...", flush=True)
        print(wrangler("d1", "migrations", "apply", STAGING_DB, *where(local), "--env", "preview").strip()[-1500:])
        wrangler("d1", "execute", STAGING_DB, *where(local), "--env", "preview", "--command", AFTER_REFRESH.strip())
    finally:
        if not keep and dump.exists():
            dump.unlink()
    counts = query(STAGING_DB, "SELECT (SELECT COUNT(*) FROM subscribers) subscribers, (SELECT COUNT(*) FROM users) users, "
                   "(SELECT COUNT(*) FROM orders) orders, (SELECT name FROM d1_migrations ORDER BY id DESC LIMIT 1) newest_migration",
                   local, True)[0]
    print("staging now holds: " + ", ".join(f"{k} {v}" for k, v in counts.items()))


if __name__ == "__main__":
    sys.stdout.reconfigure(errors="replace")   # wrangler prints emoji; a Windows console cannot
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = ap.add_subparsers(dest="cmd", required=True)
    sub.add_parser("setup")
    r = sub.add_parser("refresh")
    r.add_argument("--local", action="store_true", help="rehearse on this computer's local databases")
    r.add_argument("--keep", action="store_true", help="keep the copied SQL in website/private/staging/")
    a = ap.parse_args()
    if a.cmd == "setup":
        setup()
    else:
        refresh(a.local, a.keep)
