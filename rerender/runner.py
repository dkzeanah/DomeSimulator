"""Work the re-render queue unattended, shortest film first.

    py -3.12 -m rerender.runner --stills     # one still per chapter + a contact sheet, every film
    py -3.12 -m rerender.runner              # render them, one after another
    py -3.12 -m rerender.runner --list       # the order it will go in

Order: films the queue marks superseded go last; otherwise shortest first,
measured by the words the narrator will say. Each film is claimed in the
shared queue before it starts, so a Claude session or another model working
the queue at the same time never renders the same film; when it finishes it
is set to ``review`` with its outputs, for the owner to watch and pass.

Only lesson films are handled here -- the presenter decks and slideshows need
a converter first and are listed as waiting.

To stop after the current film, create the file ``rerender/STOP``.
Everything is logged to ``rerender/logs/``.
"""

from __future__ import annotations

import argparse
import subprocess
import sys
import time
from pathlib import Path

from . import catalogue, state

ROOT = catalogue.ROOT
LOGS = ROOT / "rerender" / "logs"
SHEETS = ROOT / "rerender" / "sheets"
STOP = ROOT / "rerender" / "STOP"
BY = "rerender-runner"

HOLD: dict[str, str] = {
    # key: why the runner leaves it for a person
    "pvtwo": "the original is an unfinished scaffold -- its own screen says "
             "'replace these with the real classes', and its narration types "
             "figures by hand. Give it real content before re-rendering.",
}


def words(item) -> int:
    return sum(len(f"{c.promise} {c.narration}".split()) for c in item.chapters)


def order(items=None) -> list:
    items = [i for i in (items or catalogue.load()) if i.kind == "lesson"]
    return sorted(items, key=lambda i: (bool(i.superseded_by), words(i)))


def _log(key: str, text: str) -> None:
    LOGS.mkdir(parents=True, exist_ok=True)
    stamp = time.strftime("%Y-%m-%d %H:%M:%S")
    line = f"{stamp} {key}: {text}"
    print(line, flush=True)
    with (LOGS / "runner.log").open("a", encoding="utf-8") as handle:
        handle.write(line + "\n")


def _run(args: list[str], log_path: Path) -> int:
    with log_path.open("a", encoding="utf-8") as handle:
        handle.write(f"\n=== {time.strftime('%Y-%m-%d %H:%M:%S')} {' '.join(args)}\n")
        handle.flush()
        return subprocess.call([sys.executable, "-m", "rerender", *args], cwd=str(ROOT),
                               stdout=handle, stderr=subprocess.STDOUT)


def contact_sheet(item) -> Path | None:
    from PIL import Image, ImageDraw

    folder = ROOT / "two_v_demo_output" / item.target_key
    stills = sorted(folder.glob("*.png"))
    if not stills:
        return None
    cols = 4
    w, h = 480, 270
    rows = (len(stills) + cols - 1) // cols
    sheet = Image.new("RGB", (cols * w, rows * h), (12, 12, 14))
    for n, path in enumerate(stills):
        tile = Image.open(path).resize((w, h))
        ImageDraw.Draw(tile).text((w - 40, 6), f"#{n + 1}", fill=(255, 220, 90))
        sheet.paste(tile, ((n % cols) * w, (n // cols) * h))
    SHEETS.mkdir(parents=True, exist_ok=True)
    out = SHEETS / f"{item.key}.png"
    sheet.save(out)
    return out


def outputs(item) -> list[str]:
    """What a finished render left: the newest cut, its phone cut, its release."""
    target = ROOT / item.target_file
    cuts = sorted(target.parent.glob(f"{target.stem}*.mp4"), key=lambda p: p.stat().st_mtime)
    cuts = [p for p in cuts if not p.name.startswith(".")]
    found = []
    landscape = [p for p in cuts if "vertical" not in p.name and "teaser" not in p.name]
    if landscape:
        newest = landscape[-1]
        found.append(newest)
        vertical = newest.with_name(f"{newest.stem}-vertical.mp4")
        if vertical.is_file():
            found.append(vertical)
        release = ROOT / "deliverables" / "releases" / newest.stem
        if release.is_dir():
            found.append(release)
    return [p.relative_to(ROOT).as_posix() for p in found]


def work(stills_only: bool, limit: int) -> int:
    done = 0
    for item in order():
        if STOP.exists():
            _log("-", "STOP file found; stopping between films")
            break
        if limit and done >= limit:
            break
        entry = state.entry(state.load(), item)
        if entry["status"] in ("review", "done", "skip"):
            continue
        if item.key in HOLD:
            if not any(HOLD[item.key] in x.get("text", "") for x in entry["log"]):
                state.note(item, BY, "held: " + HOLD[item.key])
            _log(item.key, "held for a person: " + HOLD[item.key])
            continue
        log_path = LOGS / f"{item.key}.log"
        LOGS.mkdir(parents=True, exist_ok=True)
        if stills_only:
            code = _run(["stills", item.key], log_path)
            sheet = contact_sheet(item)
            _log(item.key, f"stills {'ok' if code == 0 else f'FAILED ({code})'}"
                           + (f"; sheet {sheet.relative_to(ROOT).as_posix()}" if sheet else ""))
            done += 1
            continue
        try:
            state.claim(item, BY)
        except PermissionError as exc:
            _log(item.key, f"skipped: {exc}")
            continue
        state.set_status(item, "rendering", BY, text="started by the runner")
        _log(item.key, f"rendering ({len(item.chapters)} chapters, ~{words(item)} words)")
        started = time.time()
        code = _run(["render", item.key], log_path)
        found = outputs(item)
        minutes = (time.time() - started) / 60
        if code == 0 and found:
            state.set_status(item, "review", BY, found,
                             f"rendered in {minutes:.0f} min; watch it and pass it or note what is wrong")
            _log(item.key, f"done in {minutes:.0f} min: {', '.join(found)}")
        else:
            state.note(item, BY, f"render failed (code {code}) after {minutes:.0f} min; "
                                 f"see rerender/logs/{item.key}.log")
            state.set_status(item, "todo", BY, text="back in the queue after a failed render")
            _log(item.key, f"FAILED (code {code}); see its log")
        done += 1
    return 0


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(prog="rerender.runner", description=__doc__.splitlines()[0])
    parser.add_argument("--stills", action="store_true", help="stills and contact sheets only")
    parser.add_argument("--list", action="store_true", help="print the order and stop")
    parser.add_argument("--limit", type=int, default=0, help="stop after this many films")
    args = parser.parse_args(argv)
    if args.list:
        data = state.load()
        for n, item in enumerate(order(), start=1):
            status = state.entry(data, item)["status"]
            flag = " (held)" if item.key in HOLD else (" (superseded)" if item.superseded_by else "")
            print(f"{n:>2}. {item.key:<16} {words(item):>6} words  {len(item.chapters):>3} ch  "
                  f"{status:<9} {item.title}{flag}")
        waiting = [i for i in catalogue.load() if i.kind != "lesson"]
        print(f"\nwaiting for a converter ({len(waiting)}): " + ", ".join(i.key for i in waiting))
        return 0
    if STOP.exists():
        STOP.unlink()
    return work(args.stills, args.limit)


if __name__ == "__main__":
    raise SystemExit(main())
