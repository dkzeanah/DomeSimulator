"""Dome Sketch on zeanahlab.com: the modeller's own designs, solved ahead of time.

    py -3.12 -m sketch_claude.web_catalogue                  # solve the grid and every kind (~10 min)
    py -3.12 -m sketch_claude.web_catalogue --kinds          # only the wedge dome, zome, stove and tank presets
    py -3.12 -m sketch_claude.web_catalogue --upload --local  # into wrangler's local media store
    py -3.12 -m sketch_claude.web_catalogue --upload --remote # into zeanahlab-media (sketch/...)

The site cannot run this package's Python, and one design takes 1-11 s to solve, so the site
offers its designs solved here, each sent exactly as the local modeller's server sends it
(``kinds.scene``):

* **framed-panel domes** as a grid of the choices that change the structure. What does not change
  the structure the page does itself, from the same pieces:

  - skin: "none" hides the skin pieces, "clear" swaps their material to the clear one
    (checked here: the cabin and clear builds differ in nothing else);
  - furnished, stove, porch, person: each hides its own group of pieces (room, stove, porch,
    person), again checked against a real build with that option off.

  Every build's model tables were checked identical across those options, so the cut list stays
  exact; the materials table counts the solved design (porch and cabin skin), and the page says so
  when another choice is shown. A buyer's build pack is still solved for their exact choice, on
  the owner's machine (website/scripts/render_packs.py), so nothing in the PDF is approximate.
* **every other kind** -- the wedge dome (the flagship), the zome, the steel stove and the steel
  tank -- as its presets (``kinds.presets``), each with its fabrication pack (``exports.bundle``:
  DXF, CSV, OBJ, STL, glTF) solved beside it.

What is paid is decided on the server (functions/_lib/tools.ts): a trial visitor gets the trial
designs only, and those as a **trial copy** (:func:`trial_copy`) -- the build steps, the cut cards'
drawings beyond the first two, the nesting and the exports are not in it at all, so nothing paid
can be read out of the page.

Files written to ``website/private/sketch-catalogue/`` (gitignored), and their R2 keys:

    <id>.json.gz          sketch/<id>.json.gz          the design, for buyers
    trial/<id>.json.gz    sketch/trial/<id>.json.gz    the trial copy, for everyone
    x/<id>.zip            sketch/x/<id>.zip            the fabrication pack, for buyers
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
FREE_CARDS = 2
"""How many cut cards a trial copy keeps whole."""


def diameters() -> tuple[float, ...]:
    from . import model as M
    return tuple(sorted({4.0, 4.5, round(M.D("diameter_m"), 2), 5.0, 5.5, 6.0, 7.0, 8.0}))


def design_id(spec: dict) -> str:
    return (f"{spec['frequency']}v{spec['cut'].replace('/', '-')}-{spec['diameter_m']:.2f}m"
            f"-door{int(spec['door'])}-win{spec['windows']}-sky{int(spec['skylight'])}")


def kind_id(preset_key: str) -> str:
    return f"k-{preset_key}"


def grid() -> list[dict]:
    from . import model as M
    out = []
    for (f, c), d, door, w, sky in itertools.product(sorted(M.CUTS), diameters(), DOOR, WINDOWS, SKYLIGHT):
        out.append({"frequency": f, "cut": c, "diameter_m": d, "door": door, "windows": w, "skylight": sky,
                    "skin": "cabin", "furnish": True, "porch": True, "stove": True, "people": True})
    return out


TRIAL = ({"frequency": 3, "cut": "5/8", "diameter_m": None, "door": True, "windows": 5, "skylight": True},
         {"frequency": 2, "cut": "1/2", "diameter_m": 4.0, "door": True, "windows": 3, "skylight": False})
"""What anyone may open on the trial page: the reference dome and a small 2V..."""
TRIAL_KINDS = ("wedge", "stove")
"""...and the flagship wedge dome and the steel stove, as trial copies."""


def trial_copy(scene: dict) -> dict:
    """What a visitor who has not bought Dome Sketch receives: the model to look round, its
    summary and materials, and the cut list's first cards; nothing to build it from."""
    t = dict(scene["tables"])
    cards = []
    for i, c in enumerate(t.get("cards") or []):
        if i < FREE_CARDS:
            cards.append(c)
        else:
            cards.append({"mark": c["mark"], "title": c["title"], "count": c["count"], "group": c.get("group", ""),
                          "kind": c.get("kind", ""), "ids": c.get("ids", []), "rows": [], "draw": None, "locked": True})
    t.update(cards=cards, steps=[], sheets=[], edition="trial")
    return {**scene, "tables": t}


def _write(rel: str, raw: bytes, gz: bool = True) -> int:
    f = OUT / rel
    f.parent.mkdir(parents=True, exist_ok=True)
    f.write_bytes(gzip.compress(raw, 9) if gz else raw)
    return len(raw)


def _dump(scene: dict) -> bytes:
    return json.dumps(scene, separators=(",", ":")).encode()


def solve_one(spec: dict) -> dict:
    sys.path.insert(0, str(ROOT))
    from sketch_claude import kinds as KD
    scene = KD.scene({**spec, "kind": "panel"})
    did = design_id(spec)
    n = _write(f"{did}.json.gz", _dump(scene))
    if did in trial_ids():
        _write(f"trial/{did}.json.gz", _dump(trial_copy(scene)))
    t = scene["tables"]
    return {"id": did, "spec": spec, "title": t["title"], "panels": t["panels"], "sticks": t["stick_count"],
            "floor_m2": round(t["floor_m2"], 2), "height_m": round(t["height_m"], 3), "bytes": n}


def trial_ids() -> list[str]:
    from . import model as M
    ref_d = round(M.D("diameter_m"), 2)
    return [design_id({**t, "diameter_m": t["diameter_m"] or ref_d}) for t in TRIAL]


def solve_kind(preset: dict) -> dict:
    """One preset of a kind the site cannot solve: the design, its trial copy and its fabrication pack."""
    sys.path.insert(0, str(ROOT))
    from sketch_claude import exports as X
    from sketch_claude import kinds as KD
    scene = KD.scene(preset["spec"])
    kid = kind_id(preset["key"])
    n = _write(f"{kid}.json.gz", _dump(scene))
    _write(f"trial/{kid}.json.gz", _dump(trial_copy(scene)))
    pack = X.zip_bytes(X.bundle(scene))
    _write(f"x/{kid}.zip", pack, gz=False)
    t = scene["tables"]
    return {"id": kid, "key": preset["key"], "kind": t["kind"], "spec": scene["spec"], "title": t["title"], "label": preset["label"],
            "group": preset["group"], "bytes": n, "pack_bytes": len(pack), "pack_name": f"{X.slug(t['title'])}-fabrication.zip"}


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
    notes.append("model tables identical across every page-side option")
    return notes, sorted(swaps)


def kind_index(done: list[dict]) -> dict:
    """The index's part for every kind but the framed-panel dome."""
    from . import kinds as KD
    ks = KD.defaults()["kinds"]
    return {
        "kinds": {k: v for k, v in ks.items()},
        "kindPresets": [{k: v for k, v in r.items() if k in ("id", "key", "kind", "label", "group", "spec", "title")} for r in done],
        "packs": {r["id"]: {"name": r["pack_name"], "bytes": r["pack_bytes"]} for r in done},
        "default": kind_id("wedge"),
    }


def build_kinds(workers: int = 4) -> dict:
    """Solve the kinds' presets and fold them into the existing index (the grid stays as it is)."""
    from . import kinds as KD
    presets = [p for p in KD.presets() if KD.kind_of(p["spec"]) != "panel"]
    with ProcessPoolExecutor(workers) as pool:
        done = list(pool.map(solve_kind, presets))
    for r in done:
        print(f"solved {r['id']}: {r['title']} ({r['bytes'] / 1e6:.1f} MB, pack {r['pack_bytes'] / 1e6:.1f} MB)", flush=True)
    index = json.loads(INDEX.read_text(encoding="utf-8"))
    index["designs"] = {k: v for k, v in index["designs"].items() if not k.startswith("k-")}
    for r in done:
        index["designs"][r["id"]] = {"spec": r["spec"], "title": r["title"], "kind": r["kind"], "bytes": r["bytes"]}
    index["trial"] = [t for t in index["trial"] if not t.startswith("k-")] + [kind_id(k) for k in TRIAL_KINDS]
    index.update(kind_index(done))
    INDEX.write_text(json.dumps(index, indent=1) + "\n", encoding="utf-8")
    print(f"wrote {INDEX.relative_to(ROOT)}: {len(done)} kind presets added beside {sum(1 for k in index['designs'] if not k.startswith('k-'))} grid designs", flush=True)
    return index


def build(workers: int = 10) -> dict:
    from . import model as M
    from . import server as SV
    notes, swaps = check_client_options()
    for n in notes:
        print("ok:", n, flush=True)
    specs = grid()
    ref_d = round(M.D("diameter_m"), 2)
    trial = trial_ids()
    done = []
    with ProcessPoolExecutor(workers) as pool:
        for k, r in enumerate(pool.map(solve_one, specs), start=1):
            done.append(r)
            if k % 20 == 0:
                print(f"solved {k} of {len(specs)}", flush=True)
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
    return build_kinds()


def _objects() -> list[tuple[Path, str, str, str | None]]:
    """(file, R2 key, content type, content encoding) for everything solved."""
    out = []
    for f in sorted(OUT.glob("*.json.gz")):
        out.append((f, f"sketch/{f.name}", "application/json", "gzip"))
    for f in sorted((OUT / "trial").glob("*.json.gz")):
        out.append((f, f"sketch/trial/{f.name}", "application/json", "gzip"))
    for f in sorted((OUT / "x").glob("*.zip")):
        out.append((f, f"sketch/x/{f.name}", "application/zip", None))
    return out


def upload(remote: bool) -> None:
    npx = shutil.which("npx") or shutil.which("npx.cmd")
    ledger = OUT / f"uploaded-{'remote' if remote else 'local'}.json"
    done = json.loads(ledger.read_text()) if ledger.is_file() else {}
    for f, key, ctype, enc in _objects():
        if done.get(key) == f.stat().st_size or done.get(f.name) == f.stat().st_size and key == f"sketch/{f.name}":
            continue
        cmd = [npx, "wrangler", "r2", "object", "put", f"{BUCKET}/{key}", "--file", str(f), "--content-type", ctype]
        if enc:
            cmd += ["--content-encoding", enc]
        r = subprocess.run(cmd + ["--remote" if remote else "--local"], cwd=ROOT / "website", capture_output=True, text=True,
                           encoding="utf-8", errors="replace")
        if r.returncode:
            sys.exit(f"upload failed for {key}:\n{r.stderr[-1200:]}")
        done[key] = f.stat().st_size
        ledger.write_text(json.dumps(done, indent=1), encoding="utf-8")
    print(f"uploaded: {len(done)} objects", flush=True)


if __name__ == "__main__":
    sys.stdout.reconfigure(errors="replace")
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--upload", action="store_true")
    ap.add_argument("--kinds", action="store_true", help="solve only the kinds' presets and add them to the existing index")
    g = ap.add_mutually_exclusive_group()
    g.add_argument("--local", action="store_true")
    g.add_argument("--remote", action="store_true")
    ap.add_argument("--workers", type=int, default=10)
    a = ap.parse_args()
    if a.upload:
        upload(a.remote)
    elif a.kinds:
        build_kinds(min(a.workers, 6))
    else:
        build(a.workers)
