"""RENDER_COMMANDS.txt: every video this project makes, and the one command that makes it again.

    py -3.12 -m render_commands            # write RENDER_COMMANDS.txt in the repository root
    py -3.12 -m render_commands --check    # exit 1 if it is out of date, or a video has no command

Videos are not kept in git, so a new machine has the library's folders and none of its films.
This file is the way back without anyone having to work anything out: one command per video,
run from the repository folder, each rendering into a new numbered folder in ``deliverables/``.

Everything is read from the code that makes the videos, never typed here:

* the films -- ``two_v_demo.deliverables.DELIVERABLES`` (``py -3.12 -m film make <lesson>``,
  which also makes the film's phone cut, release folder and teaser);
* the Level With Me episodes -- ``sketch_claude/episodes/s01eNN.json``;
* the bedtime stories -- ``website/public/storytime/<slug>/``;
* the presentations -- ``presenter_studio.DEMOS``;
* the Cabin World re-renders -- every ``cabin_<film>`` re-staging (``two_v_demo/cabin_stage.py``),
  in the re-render queue's order of priority.

The library's own index (``deliverables/INDEX.md``) only annotates: which numbered outputs a
command made before. ``--check`` also fails if the index holds a video that no command makes and
that :data:`RECORDS` does not explain, so a new kind of video cannot slip in without its line.
``film make`` rewrites this file after every render.
"""

from __future__ import annotations

import argparse
import json
import os
import re
import sys
from collections import defaultdict
from pathlib import Path

os.environ.setdefault("PYGAME_HIDE_SUPPORT_PROMPT", "1")
ROOT = Path(__file__).resolve().parent
OUT = ROOT / "RENDER_COMMANDS.txt"
INDEX = ROOT / "deliverables" / "INDEX.md"

#: Videos in the library that no command makes, and why. A new entry needs a reason.
RECORDS = {
    "testo": "an early test render of the presenter engine",
    "presenter-all": "a trial run of the presenter studio exporting every presentation; each is in its own line above",
    "wheelchair1": "most likely the accessibility presentation (the wheelchair on the ramp) under a working name; "
                   "`presenter_studio.py export accessibility` makes that presentation",
    "launcher_trailer": "the launcher's silent trailer, built by the script kept in its folder "
                        "(deliverables/0021-launcher_trailer/build_launcher_trailer.py) over renders of the time",
    "tree-value-video": "a slideshow assembled from a PowerPoint deck by the scripts in its folder (build/)",
    "pvtwo-check": "a short check render of the pvtwo film before its full render",
    "triangle-authoring-demo": "a screen recording of the triangle authoring tool",
    "byod": "a working folder of the Bring Your Own Dome experiments (the films are `film make byod` and its variants)",
    "byod-deepseek": "a working folder of the Bring Your Own Dome experiments (the films are `film make byod_deepseek`)",
    "byod-styled": "a working folder of the Bring Your Own Dome experiments (the films are `film make byod_snarky` and `byod_polished`)",
}

#: Library names that an older version of a command used.
ALIASES = {
    "cabin-2v-geodesic-masterclass": "film:cabin_2v",
}

QUEUE_ORDER = {"high": 0, "normal": 1, "low": 2}


# ----------------------------------------------------------------------
# What the library has made
# ----------------------------------------------------------------------

def library() -> dict[str, list[tuple[str, str, int]]]:
    """Every video concept in the library's index: slug -> [(number, date, iteration)]."""
    out: dict[str, list[tuple[str, str, int]]] = defaultdict(list)
    if not INDEX.is_file():
        return out
    pat = re.compile(r"\| (\d{4,}) \| \[([^\]]+)\]\([^)]*\) \| v(\d+) \| ([\d-]+) \| video \|")
    for ln in INDEX.read_text(encoding="utf-8").splitlines():
        m = pat.match(ln)
        if m and not m.group(2).startswith(".") and not m.group(2).endswith("-silent-backup"):
            out[m.group(2)].append((m.group(1), m.group(4), int(m.group(3))))
    return out


def made(names, lib) -> str:
    """The library outputs a command made: a name is a slug, or (slug, iteration) where several
    films share one name (the six Frankendome montages are frankendome-montage v1 to v6)."""
    hits = set()
    for nm in names:
        slug, it = nm if isinstance(nm, tuple) else (nm, None)
        hits |= {(n, d) for n, d, i in lib.get(slug, []) if it is None or i == it}
    return ", ".join(f"{n} ({d})" for n, d in sorted(hits))


# ----------------------------------------------------------------------
# Every video, from the code that makes it
# ----------------------------------------------------------------------

def _minutes(lesson) -> str:
    try:
        s = sum(float(c.duration) for c in lesson.chapters)
    except Exception:          # a lesson whose chapters cannot be timed without building it
        return ""
    return f"about {s / 60:.0f} min" if s >= 90 else f"about {s:.0f} s"


def films() -> tuple[list[dict], list[dict]]:
    """(the films, the Cabin World re-stagings), each a dict with its command and the library names it makes."""
    import medialib
    from two_v_demo import teasers
    from two_v_demo.deliverables import DELIVERABLES
    from two_v_demo.lesson_registry import LESSONS

    queue = {}
    try:                       # the re-render queue's own status, priority and latest note
        from rerender import catalogue as RC
        from rerender import state as RS
        data = RS.load()
        for item in RC.load():
            e = RS.entry(data, item)
            log = e.get("log") or []
            queue[item.key] = {"status": e["status"], "priority": e["priority"], "note": log[-1]["text"] if log else ""}
    except Exception as exc:   # the commands stand without the queue's annotations
        print(f"(the re-render queue could not be read: {exc})", file=sys.stderr)
    shared = defaultdict(int)
    for d in DELIVERABLES:
        shared[medialib.slug_of(d.filename)] += 1
    originals, restaged = [], []
    for d in DELIVERABLES:
        L = LESSONS.get(d.lesson)
        title = getattr(L, "title", d.lesson) if L else d.lesson
        slug = medialib.slug_of(d.filename)
        mv = re.search(r"-v(\d+)\.mp4$", d.filename)
        names = {slug if shared[slug] == 1 else (slug, int(mv.group(1)) if mv else 1), f"{d.lesson}-teaser"}
        try:
            names.add(medialib.slug_of(teasers.output_path(d.lesson).name))
        except Exception:
            pass
        if L is not None and getattr(L, "engine", "") == "web":
            names.add(f"web-{slug}")
        names |= {a for a, t in ALIASES.items() if t == f"film:{d.lesson}"}
        row = {"key": d.lesson, "title": title, "cmd": f"py -3.12 -m film make {d.lesson}", "names": names,
               "length": _minutes(L) if L else "", "engine": getattr(L, "engine", "") if L else ""}
        base = d.lesson[len("cabin_"):] if d.lesson.startswith("cabin_") else None
        if base and base in LESSONS and LESSONS[base].engine != "web":
            q = queue.get(base, {})
            row.update(base=base, status=q.get("status", "todo"), priority=q.get("priority", "normal"), note=q.get("note", ""))
            restaged.append(row)
        else:
            originals.append(row)
    restaged.sort(key=lambda r: (QUEUE_ORDER.get(r["priority"], 1), r["key"]))
    return originals, restaged


def episodes() -> list[dict]:
    out = []
    for f in sorted((ROOT / "sketch_claude" / "episodes").glob("s[0-9][0-9]e[0-9][0-9].json")):
        e = json.loads(f.read_text(encoding="utf-8"))
        out.append({"key": e["id"], "title": e.get("title", e["id"]), "cmd": f"py -3.12 -m sketch_claude episode --episode {e['id']}",
                    "prefix": f"sketch-claude-level-with-me-{e['id']}-", "names": set()})
    return out


def stories() -> list[dict]:
    out = []
    for f in sorted((ROOT / "website" / "public" / "storytime").glob("*/manifest.json")):
        slug = f.parent.name
        m = json.loads(f.read_text(encoding="utf-8"))
        out.append({"key": slug, "title": m.get("title", slug), "cmd": f"py -3.12 -m sketch_claude storytime {slug}",
                    "names": {f"storytime-{slug}"}})
    return out


def presentations() -> list[dict]:
    import presenter_studio as ps
    out = []
    import importlib
    for key, mod in ps.DEMOS.items():
        stem = mod.rsplit(".", 1)[1]
        para = (importlib.import_module(mod).__doc__ or stem.replace("_", " ")).strip().split("\n\n")[0]
        doc = " ".join(para.split()).rstrip(".")
        doc = doc if len(doc) <= 140 else doc[:137].rsplit(" ", 1)[0] + "..."
        out.append({"key": key, "title": doc, "cmd": f"py -3.12 presenter_studio.py export {key}", "names": {stem}})
    return out


def others() -> list[dict]:
    return [{"key": "cold_open", "title": "The 40-Hour Cabin: the cold open (both cuts and the release)",
             "cmd": "py -3.12 -m wedge_book.cold_open", "names": {"the-40-hour-cabin-cold-open"}}]


# ----------------------------------------------------------------------
# The file
# ----------------------------------------------------------------------

HEAD = """\
# RENDER_COMMANDS.txt -- every video this project makes, and the one command that makes it again.
#
# Videos are not kept in git. On a new machine (or after the library is lost), run these from the
# repository folder -- a clone of github.com/dkzeanah/DomeSimulator -- one line at a time, or several
# at once in separate terminals. Each renders into a NEW numbered folder in deliverables/ and never
# overwrites anything.
#
# Written by `py -3.12 -m render_commands` from the code that makes each video; `film make` rewrites
# it after every render, so a new film adds its own line. Do not edit by hand.
#
# Once, on a new machine:
#   * Python 3.12 (`py -3.12`), with the packages the project imports:
#       py -3.12 -m pip install numpy scipy pillow pygame moderngl soundfile edge-tts matplotlib playwright
#   * ffmpeg on the PATH.
#   * Chrome or Edge (the episodes, the bedtime stories and the web-engine films render in a headless browser).
#   * Node.js and npm, then `npm install` in website/ (a bedtime story renders from the website's own page).
#   * An internet connection: the house voice (en-US-AndrewMultilingualNeural) is spoken by edge-tts.
#
# Every film here shipped in the house voice. For the owner's own voice instead, add
#   --voice mine --pace 1.5
# to a `film make` line (it needs local_voice_studio set up). A film takes about one to two hours to
# render; `py -3.12 -m film show <lesson>` says what a make will do without rendering anything.
"""


def block(title: str, rows: list[dict], lib, note: str = "", extra=None) -> list[str]:
    out = ["", "#" + "=" * 98, f"# {title} ({len(rows)})"]
    if note:
        out += [f"# {ln}" for ln in note.splitlines()]
    out.append("#" + "=" * 98)
    for r in rows:
        names = set(r["names"])
        if r.get("prefix"):
            names |= {s for s in lib if s.startswith(r["prefix"])}
        bits = [r["title"]]
        if r.get("length"):
            bits.append(r["length"])
        if extra:
            bits += extra(r)
        hist = made(names, lib)
        bits.append(f"made before: {hist}" if hist else "not rendered yet")
        out.append(f"# {r['key']}: " + "; ".join(bits))
        out.append(r["cmd"])
    return out


def text() -> str:
    lib = library()
    originals, restaged = films()
    shipped = [r for r in originals if made(r["names"], lib)]
    unshipped = [r for r in originals if not made(r["names"], lib)]
    lines = [HEAD.rstrip("\n")]
    lines += block("1. The films, as they shipped", shipped, lib,
                   "Each also makes its phone cut, its release folder (thumbnails, captions, descriptions) and its teaser.")
    lines += block("2. Level With Me, the dome's own series", episodes(), lib)
    lines += block("3. Bedtime stories", stories(), lib, "These build the website first (npm run build in website/) if it is out of date.")
    lines += block("4. The Dome Case and the other presentations", presentations(), lib)
    lines += block("5. Other films", others(), lib)
    lines += block("6. Cabin World re-renders: the re-render queue, high priority first", restaged, lib,
                   "Every earlier film re-staged in the Cabin World (two_v_demo/cabin_stage.py), its narration and\n"
                   "figures unchanged. After watching one: py -3.12 -m rerender status <queue key> done --by <your name>",
                   extra=lambda r: [f"queue: {r['base']}, {r['status']}, {r['priority']}"]
                   + ([f"queue note: {r['note'][:160]}"] if r.get("note") and r["status"] != "done" else []))
    lines += block("7. Written, never rendered yet", unshipped, lib)
    lines += ["", "#" + "=" * 98, f"# 8. Kept for the record, no command ({len(RECORDS)})", "#" + "=" * 98]
    for slug, why in RECORDS.items():
        hist = made({slug}, lib)
        lines.append(f"# {slug}{f' ({hist})' if hist else ''}: {why}")
    return "\n".join(lines) + "\n"


def commands(s: str) -> list[str]:
    return [ln for ln in s.splitlines() if ln and not ln.startswith("#")]


def unaccounted() -> list[str]:
    """Videos in the library that no line makes and no record explains."""
    lib = library()
    originals, restaged = films()
    rows = originals + restaged + episodes() + stories() + presentations() + others()
    covered = set(RECORDS)
    for r in rows:
        covered |= {n[0] if isinstance(n, tuple) else n for n in r["names"]}
        if r.get("prefix"):
            covered |= {s for s in lib if s.startswith(r["prefix"])}
    return sorted(s for s in lib if s not in covered)


def write() -> Path:
    OUT.write_text(text(), encoding="utf-8", newline="\n")
    return OUT


def check() -> list[str]:
    problems = []
    missing = unaccounted()
    if missing:
        problems.append("videos in the library with no command and no record (add a line or a RECORDS entry): " + ", ".join(missing))
    want = commands(text())
    have = commands(OUT.read_text(encoding="utf-8")) if OUT.is_file() else []
    if want != have:
        problems.append(f"{OUT.name} is out of date: run py -3.12 -m render_commands")
    return problems


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(prog="render_commands", description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--check", action="store_true")
    a = ap.parse_args(argv)
    if a.check:
        problems = check()
        for p in problems:
            print("FAIL:", p)
        if not problems:
            n = len(commands(OUT.read_text(encoding="utf-8")))
            print(f"ok: {OUT.name} has {n} commands, and every video in the library is accounted for")
        return 1 if problems else 0
    f = write()
    print(f"wrote {f.name}: {len(commands(f.read_text(encoding='utf-8')))} commands")
    return 0


if __name__ == "__main__":
    sys.stdout.reconfigure(errors="replace")
    raise SystemExit(main())
