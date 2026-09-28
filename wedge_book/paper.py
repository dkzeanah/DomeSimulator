"""The book's figures, rendered again for paper.

Every figure in :mod:`wedge_book.figures` and :mod:`wedge_book.plates` was made
for a screen: a near-black field, and -- for the film frames -- the film's own
headline, cards and floating labels drawn over the picture. On a printed page
that is a black rectangle with small text burned into it, and it is most of
the book's pictures.

This renders the same shots again, with two differences and no others:

* **the background is paper** -- a light cool grey, not white, so that white
  and pale parts of a scene (the seams, a pale panel) still read against it.
  Both renderers blend their soft edges against whatever they were cleared
  to, so clearing to the paper tone gives clean edges with no matting step;
* **the films' dark stage is light** -- the slab and grid many lessons stand
  their subject on are drawn in pale greys (``paper_stage``);
* **the film frames are bare** -- no headline, card, callout or floating
  label. The book prints its own caption under every figure, so the words
  were being said twice, once too small to read.

The camera, the geometry, the time in the film and the solver settings are
the originals', read from the same recipes, so a print figure is the same
picture on a different page. They are written to ``figures-print/`` beside the
screen versions, which the web reader and the films keep using; only the
print edition reads these.

    py -3.12 -m wedge_book.paper            # render every figure the book uses
    py -3.12 -m wedge_book.paper --check    # just the checks
"""

from __future__ import annotations

import argparse
import json
import re
import shutil
import subprocess
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

from . import figures, plates, store

PRINT_DIR = store.BOOK_DIR / "figures-print"
#: The page the pictures sit on, as the renderers' 0-1 clear colour.
PAPER = (0.925, 0.935, 0.945)
PAPER_RGB = tuple(round(c * 255) for c in PAPER)
#: The screens' own fields, which must not survive into a print figure.
SCREEN_FIELDS = ((5, 7, 13), (9, 11, 15))


def used_keys() -> list[str]:
    """Every figure key the book actually prints, in page order."""
    from . import print_edition

    document = print_edition._engine_html()
    names = re.findall(r'<img [^>]*src="file:///[^"]*/([^/"]+)\.(?:png|jpg|svg)"', document)
    return list(dict.fromkeys(names))


def render_plates(keys: set[str], timeout: int = 5400) -> dict:
    """Film frames, bare, on paper -- one film at a time."""
    registry = plates.lessons()
    wanted: dict[str, list[plates.Plate]] = {}
    for plate in plates.PLATES:
        if plate.key in keys:
            wanted.setdefault(plate.lesson, []).append(plate)
    made, failed = [], []
    PRINT_DIR.mkdir(parents=True, exist_ok=True)
    for key, group in wanted.items():
        lesson = registry[key]
        times = {plate: plates.shot_time(lesson, plate.chapter, plate.at) for plate in group}
        ticket = {"lesson": key, "action": "shots", "plate": True, "bare": True,
                  "background": list(PAPER), "paper_stage": True,
                  "shots": ",".join(f"{t:.2f}" for t in times.values())}
        print(f"  {key}: {len(group)} frames", flush=True)
        result = subprocess.run(
            [plates.PYTHON, *plates.PYTHON_ARGS, "-c",
             "import json,sys;from two_v_demo import app;"
             "raise SystemExit(app.main(config=json.loads(sys.argv[1])))",
             json.dumps(ticket)],
            cwd=str(plates.ROOT), capture_output=True, text=True, timeout=timeout)
        if result.returncode != 0:
            failed.append(f"{key}: {result.stderr[-300:]}")
            continue
        for plate, when in times.items():
            source = plates.SHOT_DIR / key / f"{lesson.snapshot_prefix}_{when:07.2f}s.png"
            if source.is_file():
                shutil.copyfile(source, PRINT_DIR / f"{plate.key}.png")
                made.append(plate.key)
            else:
                failed.append(f"{plate.key}: no frame at {when:.2f}s")
    return {"made": made, "failed": failed}


def render_figures(keys: set[str], timeout: int = 3600) -> dict:
    """Solver figures, same recipes, on paper."""
    chosen = [f for f in figures.catalogue() if f.key in keys]
    shots = []
    for figure in chosen:
        shot = figure.shot()
        shot["path"] = str(PRINT_DIR / f"{figure.key}.png")
        shot["background"] = list(PAPER)
        shots.append(shot)
    if not shots:
        return {"made": [], "failed": []}
    PRINT_DIR.mkdir(parents=True, exist_ok=True)
    spec = PRINT_DIR / "_shots.json"
    spec.write_text(json.dumps({"shots": shots}, indent=2), encoding="utf-8")
    print(f"  solver: {len(shots)} figures", flush=True)
    result = subprocess.run(
        ["py", "-3.12", str(figures.SOLVER), "--figures", str(spec)],
        cwd=str(figures.ROOT), capture_output=True, text=True, timeout=timeout)
    made = [f.key for f in chosen if (PRINT_DIR / f"{f.key}.png").is_file()]
    failed = [] if result.returncode == 0 else [result.stderr[-400:]]
    return {"made": made, "failed": failed}


#: The book's own line drawings (:mod:`wedge_book.graphics`), drawn on white
#: already. They go into the print set as they are.
DRAWN = ("seam-section", "mast-and-floor", "floating-dome")


def copy_drawn(keys: set[str]) -> list[str]:
    copied = []
    for key in DRAWN:
        source = figures.FIGURE_DIR / f"{key}.png"
        if key in keys and source.is_file():
            PRINT_DIR.mkdir(parents=True, exist_ok=True)
            shutil.copyfile(source, PRINT_DIR / f"{key}.png")
            copied.append(key)
    return copied


def credit(keys: list[str]) -> int:
    """The credit line the screen figures carry, in the page's colours."""
    done = 0
    for key in keys:
        path = PRINT_DIR / f"{key}.png"
        if not path.is_file():
            continue
        image = Image.open(path).convert("RGB")
        draw = ImageDraw.Draw(image)
        try:
            font = ImageFont.truetype("arial.ttf", max(12, image.width // 110))
        except OSError:
            font = ImageFont.load_default()
        box = draw.textbbox((0, 0), store.CREDIT, font=font)
        pad = max(6, image.width // 240)
        height = box[3] - box[1] + pad * 2
        draw.rectangle([0, image.height - height, image.width, image.height], fill=PAPER_RGB)
        draw.text((pad, image.height - height + pad), store.CREDIT, fill=(96, 104, 114), font=font)
        image.save(path)
        done += 1
    return done


def validate_paper() -> None:
    """Every printed figure has a paper version, and none is a screen field."""
    keys = used_keys()
    missing = [k for k in keys if not (PRINT_DIR / f"{k}.png").is_file()]
    assert not missing, f"{len(missing)} figures have no paper version: {missing[:6]}"
    dark = []
    for key in keys:
        with Image.open(PRINT_DIR / f"{key}.png") as im:
            small = im.convert("RGB").resize((160, 90))
            pixels = [tuple(p) for p in small.get_flattened_data()]                 if hasattr(small, "get_flattened_data") else list(small.getdata())
        field = sum(1 for p in pixels if any(
            all(abs(a - b) <= 3 for a, b in zip(p, f)) for f in SCREEN_FIELDS))
        if field > len(pixels) * 0.05:
            dark.append(key)
    assert not dark, f"figures still on the screen's dark field: {dark[:6]}"


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--check", action="store_true")
    parser.add_argument("--only", default="", help="comma-separated figure keys")
    parser.add_argument("--drawn-only", action="store_true",
                        help="only copy the line drawings (no rendering)")
    args = parser.parse_args(argv)
    if not args.check:
        keys = used_keys()
        if args.only:
            keys = [k for k in keys if k in set(args.only.split(","))]
        plate_keys = {p.key for p in plates.PLATES} & set(keys)
        drawn_keys = set(DRAWN) & set(keys)
        figure_keys = set(keys) - plate_keys - drawn_keys
        print(f"{len(keys)} figures: {len(plate_keys)} film frames, "
              f"{len(figure_keys)} solver shots, {len(drawn_keys)} drawings")
        a = render_plates(plate_keys) if not args.drawn_only else {"made": [], "failed": []}
        b = render_figures(figure_keys) if not args.drawn_only else {"made": [], "failed": []}
        print(f"copied drawings: {copy_drawn(drawn_keys)}")
        labelled = credit(sorted(figure_keys)) if not args.drawn_only else 0
        print(f"made {len(a['made']) + len(b['made'])}, credited {labelled}")
        for problem in a["failed"] + b["failed"]:
            print(f"  FAILED: {problem}")
    validate_paper()
    print("paper figures: ok")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
