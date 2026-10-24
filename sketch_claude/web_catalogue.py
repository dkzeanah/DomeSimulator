"""Dome Sketch on zeanahlab.com: the modeller's own designs, solved ahead of time.

    py -3.12 -m sketch_claude.web_catalogue                  # solve the grid (12 processes, ~10 min)
    py -3.12 -m sketch_claude.web_catalogue --upload --local  # into wrangler's local media store
    py -3.12 -m sketch_claude.web_catalogue --upload --remote # into zeanahlab-media (sketch/<id>.json.gz)

The site cannot run this package's Python, and one design takes 4-11 s to solve, so the site
offers the designs that change the structure as a grid, each solved here by ``model.build`` and
sent exactly as the local modeller's server sends it (``server.scene``). What does not change the
structure the page does itself, from the same pieces:

* skin: "none" hides the skin pieces, "clear" swaps their material to the clear one
  (checked here: the cabin and clear builds differ in nothing else);
* furnished, stove, porch, person: each hides its own group of pieces (room, stove, porch,
  person), again checked against a real build with that option off.

Every build's tables were checked identical across those options, so the cut list and the
materials stay exact. A buyer's build pack is still solved for their exact choice, on the owner's
machine (website/scripts/render_packs.py), so nothing in the PDF is approximate.
"""

from __future__ import annotations

import argparse
import gzip
import itertools
import json
import shutil
import subprocess
import sys
from concurrent.futures import ProcessPoolExecutor
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "website" / "private" / "sketch-catalogue"     # gitignored: the solved designs
INDEX = ROOT / "website" / "src" / "generated" / "sketch-grid.json"
BUCKET = "zeanahlab-media"

WINDOWS = (0, 3, 5)
SKYLIGHT = (True, False)
DOOR = (True, False)


def diameters() -> tuple[float, ...]:
    from . import model as M
    return tuple(sorted({4.0, 4.5, round(M.D("diameter_m"), 2), 5.0, 5.5, 6.0, 7.0, 8.0}))


def design_id(spec: dict) -> str:
    return (f"{spec['frequency']}v{spec['cut'].replace('/', '-')}-{spec['diameter_m']:.2f}m"
            f"-door{int(spec['door'])}-win{spec['windows']}-sky{int(spec['skylight'])}")


def grid() -> list[dict]:
    from . import model as M
    out = []
    for (f, c), d, door, w, sky in itertools.product(sorted(M.CUTS), diameters(), DOOR, WINDOWS, SKYLIGHT):
        out.append({"frequency": f, "cut": c, "diameter_m": d, "door": door, "windows": w, "skylight": sky,
                    "skin": "cabin", "furnish": True, "porch": True, "stove": True, "people": True})
    return out


TRIAL = ({"frequency": 3, "cut": "5/8", "diameter_m": None, "door": True, "windows": 5, "skylight": True},
         {"frequency": 2, "cut": "1/2", "diameter_m": 4.0, "door": True, "windows": 3, "skylight": False})
"""What anyone may open on the trial page: the reference dome and a small 2V."""


def solve_one(spec: dict) -> dict:
    sys.path.insert(0, str(ROOT))
    from sketch_claude import model as M
    from sketch_claude import server as SV
    s = M.Spec.from_dict(spec)
    scene = SV.scene(s)
    did = design_id(spec)
    raw = json.dumps(scene, separators=(",", ":")).encode()
    OUT.mkdir(parents=True, exist_ok=True)
    (OUT / f"{did}.json.gz").write_bytes(gzip.compress(raw, 9))
    t = scene["tables"]
    return {"id": did, "spec": spec, "title": t["title"], "panels": t["panels"], "sticks": t["stick_count"],
            "floor_m2": round(t["floor_m2"], 2), "height_m": round(t["height_m"], 3), "bytes": len(raw)}


def check_client_options() -> list[str]:
    """Prove what the page does for itself matches a real build (on the reference design)."""
    from . import model as M
    notes = []
    base = {p.id: p for p in M.build(M.Spec()).pieces}
    groups = {"furnish": "room", "stove": "stove", "porch": "porch", "people": "person"}
    for opt, group in groups.items():
        off = {p.id for p in M.build(M.Spec(**{opt: False})).pieces}
        gone = {k for k in base if k not in off}
        assert gone == {k for k, p in base.items() if p.group == group}, (opt, group)
        notes.append(f"{opt} off = hide group '{group}' ({len(gone)} pieces)")
    clear = {p.id: p.material for p in M.build(M.Spec(skin="clear")).pieces}
    swaps = {(base[k].material, m) for k, m in clear.items() if base[k].material != m}
    assert all(base[k].tag == "skin" for k, m in clear.items() if base[k].material != m)
    # "none" removes the covered panels (the materials "clear" swaps), not the trim, which stays
    covering = {a for a, _ in swaps}
    none = {p.id for p in M.build(M.Spec(skin="none")).pieces}
    assert {k for k in base if k not in none} == {k for k, p in base.items() if p.tag == "skin" and p.material in covering}
    notes.append(f"skin none = hide skin pieces of {sorted(covering)}; skin clear = materials {sorted(swaps)}")
    tables = M.build(M.Spec()).tables
    for kw in ({"skin": "clear"}, {"skin": "none"}, {"furnish": False}, {"porch": False}, {"stove": False}, {"people": False}):
        other = M.build(M.Spec(**kw)).tables
        assert all(str(tables[k]) == str(other.get(k)) for k in tables), kw
    notes.append("tables identical across every page-side option")
    return notes, sorted(swaps)


def build(workers: int = 10) -> dict:
    from . import model as M
    from . import server as SV
    notes, swaps = check_client_options()
    for n in notes:
        print("ok:", n, flush=True)
    specs = grid()
    done = []
    with ProcessPoolExecutor(workers) as pool:
        for k, r in enumerate(pool.map(solve_one, specs), start=1):
            done.append(r)
            if k % 20 == 0:
                print(f"solved {k} of {len(specs)}", flush=True)
    ref_d = round(M.D("diameter_m"), 2)
    trial = [design_id({**t, "diameter_m": t["diameter_m"] or ref_d}) for t in TRIAL]
    index = {
        "_generated_by": "sketch_claude/web_catalogue.py -- do not edit",
        "tag": __import__("sketch_claude").TAG,
        "cuts": [{"frequency": f, "cut": c} for f, c in sorted(M.CUTS)],
        "diameters": list(diameters()), "windows": list(WINDOWS),
        "defaults": {**M.Spec().to_dict(), "diameter_m": ref_d},
        "presets": {k: p for k, p in SV.PRESETS.items()},
        "declared": {k: {"value": d.value, "unit": d.unit, "why": d.why, "kind": d.kind} for k, d in M.DECLARED.items()},
        "clientOptions": {"groups": {"furnish": "room", "stove": "stove", "porch": "porch", "people": "person"},
                          "clearSkin": dict(swaps)},
        "trial": trial,
        "designs": {r["id"]: {k: v for k, v in r.items() if k != "id"} for r in done},
    }
    INDEX.write_text(json.dumps(index, indent=1) + "\n", encoding="utf-8")
    print(f"wrote {INDEX.relative_to(ROOT)}: {len(done)} designs, {sum(r['bytes'] for r in done) / 1e6:.0f} MB raw", flush=True)
    return index


def upload(remote: bool) -> None:
    npx = shutil.which("npx") or shutil.which("npx.cmd")
    ledger = OUT / f"uploaded-{'remote' if remote else 'local'}.json"
    done = json.loads(ledger.read_text()) if ledger.is_file() else {}
    for f in sorted(OUT.glob("*.json.gz")):
        if done.get(f.name) == f.stat().st_size:
            continue
        r = subprocess.run([npx, "wrangler", "r2", "object", "put", f"{BUCKET}/sketch/{f.name}", "--file", str(f),
                            "--content-type", "application/json", "--content-encoding", "gzip",
                            "--remote" if remote else "--local"], cwd=ROOT / "website", capture_output=True, text=True,
                           encoding="utf-8", errors="replace")
        if r.returncode:
            sys.exit(f"upload failed for {f.name}:\n{r.stderr[-1200:]}")
        done[f.name] = f.stat().st_size
        ledger.write_text(json.dumps(done, indent=1), encoding="utf-8")
    print(f"uploaded: {len(done)} designs", flush=True)


if __name__ == "__main__":
    sys.stdout.reconfigure(errors="replace")
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--upload", action="store_true")
    g = ap.add_mutually_exclusive_group()
    g.add_argument("--local", action="store_true")
    g.add_argument("--remote", action="store_true")
    ap.add_argument("--workers", type=int, default=10)
    a = ap.parse_args()
    if a.upload:
        upload(a.remote)
    else:
        build(a.workers)
