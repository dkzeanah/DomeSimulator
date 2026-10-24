"""The web video engine, as the agent uses it: episodes and lesson films (sketch_claude).

These are the steps the episodes and the web-engine masterclass were actually made with, written
down so the agent repeats them instead of improvising (docs/llm-episode-guide.md is the long form):

1. read the episode (sketch_claude/episodes/sNNeNN.json) and validate it with writers.check;
2. a draft render first (--draft, into tmp/), and look at its folder: a landscape cut, a phone
   cut, captions and a thumbnail per scene, each non-empty;
3. only then the release render, which takes a new numbered folder in deliverables/;
4. for a lesson film: stills in both orientations first (film stills <key> --engine web), then
   the film (film make <key> --engine web), whose release folder is built by release.build_release.

Every render runs as its own process with its log in the agent's run directory; nothing here
edits a script or an output in place.
"""

from __future__ import annotations

import json
import re
import subprocess
import time
from pathlib import Path

from . import config

EPISODES = config.REPO_ROOT / "sketch_claude" / "episodes"


def _run(args: list[str], label: str, timeout: int) -> dict:
    run_dir = config.RUNS_DIR / "_last"
    run_dir.mkdir(parents=True, exist_ok=True)
    log = run_dir / f"{label}_{time.strftime('%H%M%S')}.log"
    t0 = time.monotonic()
    try:
        with log.open("w", encoding="utf-8") as f:
            p = subprocess.run([config.agent_python(), "-m", *args], cwd=str(config.REPO_ROOT),
                               stdout=f, stderr=subprocess.STDOUT, timeout=timeout)
        code = p.returncode
    except subprocess.TimeoutExpired:
        code = -9
    text = log.read_text(encoding="utf-8", errors="replace") if log.is_file() else ""
    outputs = []
    for line in re.findall(r"^OUTPUT (.+)$", text, re.M):
        try:
            outputs.append(json.loads(line))
        except ValueError:                       # the episode command prints the folder itself
            outputs.append({"folder": line.strip()})
    return {"ok": code == 0, "returncode": code, "elapsed_s": round(time.monotonic() - t0, 1), "log": str(log),
            "tail": "\n".join(text.splitlines()[-25:]), "outputs": outputs}


def episodes(args: dict) -> dict:
    """List every episode, or validate one (args: episode)."""
    import sys
    sys.path.insert(0, str(config.REPO_ROOT))
    from sketch_claude import writers
    series = json.loads((EPISODES / "series.json").read_text(encoding="utf-8"))
    eid = str(args.get("episode") or "")
    if eid:
        f = EPISODES / f"{eid}.json"
        if not f.is_file():
            return {"ok": False, "error": f"no episode {eid}"}
        ep = json.loads(f.read_text(encoding="utf-8"))
        problems = writers.check(ep, series)
        kinds: dict[str, int] = {}
        for b in ep.get("beats", []):
            kinds[b.get("k", "?")] = kinds.get(b.get("k", "?"), 0) + 1
        return {"ok": not problems, "episode": eid, "title": ep.get("title"), "beats": len(ep.get("beats", [])),
                "kinds": kinds, "problems": problems}
    out = []
    for f in sorted(EPISODES.glob("s[0-9][0-9]e[0-9][0-9].json")):
        ep = json.loads(f.read_text(encoding="utf-8"))
        out.append({"id": ep["id"], "number": ep.get("number"), "title": ep.get("title"), "beats": len(ep.get("beats", [])),
                    "scenes": sum(1 for b in ep.get("beats", []) if b.get("k") == "scene")})
    return {"ok": True, "episodes": out, "cast": list(series.get("cast", {}))}


def _folder_ok(folder: Path) -> list[str]:
    """What a finished render must have left: the release checklist."""
    missing = []
    mp4 = [p for p in folder.glob("*.mp4") if "vertical" not in p.name]
    if not mp4 or mp4[0].stat().st_size < 100_000:
        missing.append("landscape cut")
    if not [p for p in folder.glob("*-vertical.mp4") if p.stat().st_size > 100_000]:
        missing.append("phone cut")
    if not list(folder.glob("*.srt")):
        missing.append("captions")
    if not list(folder.glob("thumb-*.jpg")) and not (folder / "release" / "thumbnails").is_dir():
        missing.append("thumbnails")
    if not (folder / "description.md").is_file() and not (folder / "release" / "description.md").is_file():
        missing.append("description")
    return missing


def episode_render(args: dict) -> dict:
    """Render one episode headless (args: episode, draft). Checks the folder it leaves."""
    eid = str(args.get("episode") or "")
    if not re.fullmatch(r"s\d{2}e\d{2}", eid):
        return {"ok": False, "error": "episode looks like s01e03"}
    draft = bool(args.get("draft", True))
    r = _run(["sketch_claude", "episode", "--episode", eid] + (["--draft"] if draft else []), f"episode_{eid}",
             config.TIMEOUT_EXPORT)
    folder = None
    for o in r["outputs"]:
        if o.get("folder"):
            folder = config.REPO_ROOT / o["folder"]
    r["folder"] = str(folder) if folder else None
    if folder and folder.is_dir():
        r["missing"] = _folder_ok(folder)
        r["ok"] = r["ok"] and not r["missing"]
    return r


def lesson(args: dict) -> dict:
    """A lesson film on the web engine (args: lesson, mode = stills | render)."""
    key = str(args.get("lesson") or "2v")
    mode = "stills" if str(args.get("mode", "stills")) == "stills" else "make"
    r = _run(["film", mode, key, "--engine", "web"], f"lesson_{key}_{mode}",
             config.TIMEOUT_STILLS if mode == "stills" else config.TIMEOUT_EXPORT)
    if mode == "stills":
        shots = config.REPO_ROOT / "tmp" / "lesson-stills" / key
        r["stills"] = sorted(str(p) for p in shots.rglob("*.png"))
    else:
        folders = {o.get("folder") for o in r["outputs"] if o.get("folder")}
        r["missing"] = [f"{f}: {m}" for f in folders for m in _folder_ok(config.REPO_ROOT / f)]
        r["ok"] = r["ok"] and not r["missing"]
    return r
