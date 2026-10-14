"""Put zeanahlab.com online, start to finish, from this computer.

Wrangler is Cloudflare's own command-line tool (it comes with this folder's packages; npx
runs it). This script drives it so nobody has to: it signs in (your browser opens once and
you click Allow), makes the database, the book store and the site, gives the site its
secrets, uploads the books, and -- when you say yes -- publishes. Safe to run again: every
step checks what already exists and skips it.

    py -3.12 scripts/cloudflare_setup.py          (or: npm run setup)

The two things it cannot do for you are said plainly when it reaches them: switching R2 on
(Cloudflare wants a card on file, even for the free tier) and attaching www.zeanahlab.com
(two clicks; the script opens the right page).
"""

from __future__ import annotations

import getpass
import json
import re
import secrets
import shutil
import subprocess
import sys
import webbrowser
from pathlib import Path

SITE = Path(__file__).resolve().parent.parent
TOML = SITE / "wrangler.toml"
PROJECT, DB, BUCKET = "zeanahlab", "zeanahlab", "zeanahlab-books"
NPX = shutil.which("npx.cmd") or shutil.which("npx")


def say(msg: str) -> None:
    print(f"\n== {msg}")


def run(*args: str, capture: bool = True, stdin: str | None = None, check: bool = False) -> subprocess.CompletedProcess:
    r = subprocess.run([NPX, "wrangler", *args], cwd=SITE, text=True, input=stdin,
                       capture_output=capture, encoding="utf-8", errors="replace")
    if check and r.returncode:
        print(r.stdout or "", r.stderr or "")
        raise SystemExit(f"wrangler {' '.join(args)} failed")
    return r


def ask(prompt: str, default: str = "") -> str:
    got = input(f"{prompt}{f' [{default}]' if default else ''}: ").strip()
    return got or default


def yes(prompt: str) -> bool:
    return input(f"{prompt} [y/N]: ").strip().lower() in ("y", "yes")


# ---------------------------------------------------------------- the steps

def sign_in() -> None:
    say("1. Signing in to Cloudflare")
    r = run("whoami")
    if "not authenticated" in (r.stdout + r.stderr).lower() or r.returncode:
        print("Your browser will open. Sign in to the Cloudflare account that holds zeanahlab.com and click Allow.")
        run("login", capture=False, check=True)
    else:
        print("Already signed in.")


def database() -> None:
    say("2. The database")
    text = TOML.read_text(encoding="utf-8")
    r = run("d1", "list", "--json")
    found = None
    try:
        found = next((d for d in json.loads(r.stdout) if d.get("name") == DB), None)
    except json.JSONDecodeError:
        pass
    if found:
        db_id = found.get("uuid") or found.get("database_id")
        print(f"Exists ({db_id}).")
    else:
        out = run("d1", "create", DB, check=True)
        m = re.search(r'"?database_id"?\s*[=:]\s*"([0-9a-f-]{36})"', out.stdout)
        if not m:
            print(out.stdout)
            raise SystemExit("Made the database but could not read its id; paste it into wrangler.toml and run again.")
        db_id = m.group(1)
        print(f"Made ({db_id}).")
    new = re.sub(r'database_id = "[^"]*"', f'database_id = "{db_id}"', text)
    if new != text:
        TOML.write_text(new, encoding="utf-8")
        print("Wrote its id into wrangler.toml.")
    run("d1", "migrations", "apply", DB, "--remote", capture=False, stdin="y\n", check=True)


def book_store() -> None:
    say("3. The book store (R2)")
    while True:
        r = run("r2", "bucket", "list")
        out = r.stdout + r.stderr
        if r.returncode == 0 and BUCKET in out:
            print("Exists.")
            break
        if r.returncode == 0:
            c = run("r2", "bucket", "create", BUCKET)
            if c.returncode == 0:
                print("Made.")
                break
            out = c.stdout + c.stderr
        print(out.strip()[-400:])
        print("\nR2 has to be switched on once in the dashboard (Cloudflare asks for a card; nothing is charged under 10 GB).")
        webbrowser.open("https://dash.cloudflare.com/?to=/:account/r2/overview")
        input("Switch it on in the page that just opened, then press Enter here to try again... ")
    r = subprocess.run([sys.executable, str(SITE / "scripts" / "upload_books.py"), "--remote"], cwd=SITE)
    if r.returncode:
        raise SystemExit("uploading the books failed")


def site_and_secrets() -> None:
    say("4. The site and its secrets")
    r = run("pages", "project", "list", "--json")
    exists = False
    try:
        exists = any(p.get("Project Name", p.get("name")) == PROJECT for p in json.loads(r.stdout))
    except json.JSONDecodeError:
        exists = PROJECT in (r.stdout or "")
    if not exists:
        run("pages", "project", "create", PROJECT, "--production-branch", "main", capture=False, check=True)
    else:
        print("Site exists.")
    have = run("pages", "secret", "list", "--project-name", PROJECT).stdout or ""

    def put(name: str, value: str) -> None:
        run("pages", "secret", "put", name, "--project-name", PROJECT, stdin=value + "\n", check=True)
        print(f"  {name} set.")

    if "SESSION_SECRET" not in have:
        put("SESSION_SECRET", secrets.token_urlsafe(48))   # made here, never shown
    if "ADMIN_EMAILS" not in have:
        git_email = subprocess.run(["git", "config", "user.email"], capture_output=True, text=True).stdout.strip()
        put("ADMIN_EMAILS", ask("Email that gets the Admin page", git_email))
    print("\nOptional keys. Each one says what it starts with; press Enter alone to skip it.")
    print("What you paste stays hidden, and a key with the wrong beginning is refused.\n")
    for name, hint, prefixes in (
            ("RESEND_API_KEY", "RESEND key (from resend.com), starts with re_", ("re_",)),
            ("MAIL_FROM", "FROM address for emails, e.g. Zeanah Lab <hello@zeanahlab.com>", None),
            ("STRIPE_SECRET_KEY", "STRIPE secret or restricted key, starts with sk_live_ / rk_live_ (or sk_test_ / rk_test_)",
             ("sk_live_", "rk_live_", "sk_test_", "rk_test_")),
            ("STRIPE_WEBHOOK_SECRET", "STRIPE WEBHOOK signing secret, starts with whsec_", ("whsec_",))):
        if name in have:
            print(f"  {name}: already set (to change it: npx wrangler pages secret delete {name} --project-name {PROJECT}, then run this again).")
            continue
        while True:
            v = (getpass.getpass(f"  {hint}\n  > ") if prefixes else ask(f"  {hint}\n  >")).strip()
            if not v or not prefixes or v.startswith(prefixes):
                break
            print(f"  That starts with '{v[:6]}...', not {' or '.join(prefixes)} -- it belongs in a different box. Try again, or press Enter to skip.")
        if v:
            put(name, v)


def publish() -> None:
    say("5. Publish")
    if not yes("Build the site and publish it to the internet now?"):
        print("Not published. Run this again when you are ready.")
        return
    subprocess.run(["npm.cmd" if sys.platform == "win32" else "npm", "run", "build"], cwd=SITE, check=True)
    run("pages", "deploy", "dist", "--project-name", PROJECT, "--branch", "main", "--commit-dirty=true", capture=False, check=True)
    say("6. The address")
    import urllib.request
    try:
        live = urllib.request.urlopen("https://www.zeanahlab.com/api/shop", timeout=15).status == 200
    except Exception:
        live = False
    if live:
        print("www.zeanahlab.com is already serving the site.")
        return
    print("Last step, two clicks: in the page that opens, choose 'Set up a custom domain', type www.zeanahlab.com, confirm.")
    print("Cloudflare already runs zeanahlab.com, so it adds the record itself. Do the same for zeanahlab.com.")
    webbrowser.open(f"https://dash.cloudflare.com/?to=/:account/pages/view/{PROJECT}/domains")


def main() -> int:
    if not NPX:
        print("Node.js is needed (it gives you npx). Install it from nodejs.org and run this again.")
        return 1
    if not (SITE / "node_modules").exists():
        subprocess.run(["npm.cmd" if sys.platform == "win32" else "npm", "install"], cwd=SITE, check=True)
    sign_in()
    database()
    book_store()
    site_and_secrets()
    publish()
    print("\nDone. Everything above can be run again safely.")
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except KeyboardInterrupt:
        print("\nStopped. Run it again to carry on; finished steps are skipped.")
        raise SystemExit(130)
