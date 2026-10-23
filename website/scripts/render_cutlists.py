"""Render the Wedge Builder's queue: buyers' cut-list requests, solved here, delivered there.

    py -3.12 website/scripts/render_cutlists.py --site https://www.zeanahlab.com
        Claim each waiting request in turn, solve and render it with wedge_builder, upload the
        PDF and move on; stop when the queue is empty.

    py -3.12 website/scripts/render_cutlists.py --site https://www.zeanahlab.com --watch [--every 60]
        Keep going: when the queue is empty, wait and look again.

Needs an agent key with the cutlists:render scope (Admin -> Agents and keys) in ZL_AGENT_KEY.
The site never runs the solver; this script is the only thing that does, so a request waits
until it runs. A request the solver refuses (logs too short for the size, say) is marked failed
with the solver's own reason, which the buyer reads on their page, and their credit comes back.
A crash is reported the same way and stops the script, so a bug is not repeated down the queue.
Each PDF is also kept in website/private/cutlists/ (gitignored) as the owner's copy.
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
KEPT = ROOT / "website" / "private" / "cutlists"


def call(site: str, method: str, path: str, body: dict | None = None) -> dict:
    key = os.environ.get("ZL_AGENT_KEY")
    if not key:
        sys.exit("Set ZL_AGENT_KEY to an agent key with the cutlists:render scope (Admin -> Agents and keys).")
    req = urllib.request.Request(site.rstrip("/") + "/api" + path, method=method,
                                 data=json.dumps(body).encode() if body is not None else None,
                                 headers={"Authorization": f"Bearer {key}", "Content-Type": "application/json"})
    try:
        with urllib.request.urlopen(req, timeout=120) as r:
            return json.loads(r.read())
    except urllib.error.HTTPError as e:
        detail = e.read().decode(errors="replace")
        sys.exit(f"{method} {path}: {e.code} {detail}")


def render(job: dict) -> tuple[Path, dict]:
    from wedge_builder import design, pdf
    req = design.Request.from_json(job["params"])   # ValueError: refused, with a reason
    d = design.solve(req)
    KEPT.mkdir(parents=True, exist_ok=True)
    out = KEPT / f"{job['order']}-{job['ref']}.pdf"
    pdf.build(d, out, made_for=f"order {job['order']}")
    summary = {"design": req.key(), "logs": len(d.logs), "rounds": len(d.rounds), "families": len(d.families),
               "setups": len(d.setups), "jigs": len(d.variants), "floor_sqft": round(d.floor_area_sqft),
               "pages": None}
    try:
        import pymupdf
        with pymupdf.open(out) as doc:
            summary["pages"] = doc.page_count
    except ImportError:
        pass
    return out, summary


def run(site: str) -> int:
    """Render until the queue is empty. Returns how many were made."""
    made = 0
    while True:
        job = call(site, "POST", "/agent/cutlists/claim")["job"]
        if not job:
            return made
        p = job["params"]
        print(f"{job['ref']}: {p['diameter_ft']} ft dome, {p['log_in']} in x {p['log_ft']} ft logs (attempt {job['attempt']})", flush=True)
        try:
            out, summary = render(job)
        except ValueError as e:
            call(site, "POST", f"/agent/cutlists/{job['ref']}/failed", {"error": str(e)[:500]})
            print(f"  refused: {e}", flush=True)
            continue
        except Exception:
            traceback.print_exc()
            call(site, "POST", f"/agent/cutlists/{job['ref']}/failed",
                 {"error": "Something went wrong solving this dome. Your credit is returned; reply to your receipt email and it will be fixed."})
            raise
        call(site, "POST", f"/agent/cutlists/{job['ref']}/done",
             {"pdf": base64.b64encode(out.read_bytes()).decode(), "design": summary["design"], "summary": summary})
        made += 1
        print(f"  done: {summary['logs']} logs, {summary['families']} families, {summary['pages']} pages -> {out.name}", flush=True)


if __name__ == "__main__":
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--site", required=True)
    ap.add_argument("--watch", action="store_true")
    ap.add_argument("--every", type=int, default=60, help="seconds between looks when watching")
    a = ap.parse_args()
    while True:
        n = run(a.site)
        if not a.watch:
            print(f"queue empty; {n} rendered", flush=True)
            break
        time.sleep(max(10, a.every))
