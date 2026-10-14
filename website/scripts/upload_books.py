"""Put the newest edition of each book in the R2 bucket the site serves them from.

The file names in R2 are the ones in web/books.config.json ("file"); the PDFs are the
newest -vN of each in the numbered library (medialib.latest), so publishing a new edition
and running this is the whole release step.

    py -3.12 scripts/upload_books.py --local     # into wrangler's local R2, for npm run preview
    py -3.12 scripts/upload_books.py --remote    # into the real bucket (asks wrangler to log in)
"""

from __future__ import annotations

import argparse
import json
import shutil
import subprocess
import sys
from pathlib import Path

SITE = Path(__file__).resolve().parent.parent
ROOT = SITE.parent
sys.path.insert(0, str(ROOT))

import medialib  # noqa: E402

BUCKET = "zeanahlab-books"


def books() -> list[tuple[str, Path]]:
    cat = json.loads((ROOT / "web" / "books.config.json").read_text(encoding="utf-8"))
    out = []
    for b in cat["books"]:
        if b.get("offer") in ("free", "paid") and b.get("file"):
            stem = b["file"].removesuffix(".pdf")
            pdf = medialib.latest(stem, ".pdf")
            if pdf is None:
                print(f"  no PDF in the library for {stem}; skipped")
                continue
            out.append((b["file"], pdf))
    return out


def main() -> int:
    ap = argparse.ArgumentParser()
    where = ap.add_mutually_exclusive_group(required=True)
    where.add_argument("--local", action="store_true")
    where.add_argument("--remote", action="store_true")
    a = ap.parse_args()
    npx = shutil.which("npx") or shutil.which("npx.cmd")
    if not npx:
        print("npx not found: install Node.js 20+")
        return 1
    for key, pdf in books():
        mb = pdf.stat().st_size / 1e6
        print(f"{key}  <-  {pdf.relative_to(ROOT)}  ({mb:.1f} MB)")
        cmd = [npx, "wrangler", "r2", "object", "put", f"{BUCKET}/{key}", "--file", str(pdf),
               "--content-type", "application/pdf", "--local" if a.local else "--remote"]
        r = subprocess.run(cmd, cwd=SITE)
        if r.returncode:
            return r.returncode
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
