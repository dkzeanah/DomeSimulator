"""Draw the Dome Sketch build packs buyers ask for, on this machine, and deliver them.

    py -3.12 website/scripts/render_packs.py --site https://www.zeanahlab.com [--watch]

A build pack is the modeller's full plan set (sketch_claude/plans.py) for the buyer's exact design:
the dome at a glance, tools and materials, the price estimate, the panel map and dimensions, every
angle, the cut list, each stick's details, the jig steps, the base, assembly, the door, the finish,
the floor plan and the declared inputs. The site cannot run it, so it waits for this script, as cut
lists wait for render_cutlists.py. Needs an agent key with the packs:render scope in ZL_AGENT_KEY.
A pack that fails is reported with the reason and the buyer's credit comes back. A copy of every
pack is kept in website/private/packs/ (gitignored).
"""

from __future__ import annotations

import argparse
import base64
import json
import os
import sys
import time
import traceback
import urllib.error
import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))
KEPT = ROOT / "website" / "private" / "packs"


def call(site: str, method: str, path: str, body: dict | None = None) -> dict:
    key = os.environ.get("ZL_AGENT_KEY")
    if not key:
        sys.exit("Set ZL_AGENT_KEY to an agent key with the packs:render scope (Admin -> Agents and keys).")
    req = urllib.request.Request(site.rstrip("/") + "/api" + path, method=method,
                                 data=json.dumps(body).encode() if body is not None else None,
                                 headers={"Authorization": f"Bearer {key}", "Content-Type": "application/json"})
    try:
        with urllib.request.urlopen(req, timeout=300) as r:
            return json.loads(r.read())
    except urllib.error.HTTPError as e:
        sys.exit(f"{method} {path}: {e.code} {e.read().decode(errors='replace')}")


def run(site: str) -> int:
    from sketch_claude import model as M
    from sketch_claude.plans import build_plans
    made = 0
    while True:
        job = call(site, "POST", "/agent/packs/claim")["job"]
        if not job:
            return made
        spec = M.Spec.from_dict(job["spec"])
        print(f"{job['ref']}: {spec.title} (attempt {job['attempt']})", flush=True)
        KEPT.mkdir(parents=True, exist_ok=True)
        out = KEPT / f"{job['ref']}.pdf"
        try:
            build_plans(spec, out)
        except Exception:
            traceback.print_exc()
            call(site, "POST", f"/agent/packs/{job['ref']}/failed",
                 {"error": "Something went wrong drawing this pack. Your credit is returned; it will be fixed."})
            raise
        call(site, "POST", f"/agent/packs/{job['ref']}/done",
             {"pdf": base64.b64encode(out.read_bytes()).decode(), "summary": {"title": spec.title, "bytes": out.stat().st_size}})
        made += 1
        print(f"  done: {out.stat().st_size / 1e6:.1f} MB", flush=True)


if __name__ == "__main__":
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--site", required=True)
    ap.add_argument("--watch", action="store_true")
    ap.add_argument("--every", type=int, default=60)
    a = ap.parse_args()
    while True:
        n = run(a.site)
        if not a.watch:
            print(f"queue empty; {n} drawn", flush=True)
            break
        time.sleep(max(10, a.every))
