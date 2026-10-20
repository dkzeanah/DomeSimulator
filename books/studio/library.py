"""The Book Studio's pictures: everything in the asset library, and new illustrations made from words.

Pictures live where every picture in the project lives -- ``assets/``, named for what they show,
with ``assets/catalogue.json`` recording where each came from (``origin``) and, for an
illustration made from a description, the words it was made from (``prompt``). New ones go in
``assets/images/illustrations``.

Two ways to turn words into a picture:

* **DeepSeek** draws it as SVG through its API (:func:`deepseek_svg`), in the house style
  (:data:`HOUSE_STYLE`), and the studio files it straight away.
* **Claude, here in the chat**: :func:`claude_prompt` writes a request the owner pastes into a
  Claude Code session in this project; Claude draws the SVG and files it with
  ``py -3.12 -m books.studio.library add <name> <file.svg> --origin claude --prompt "..."``.

Every SVG is cleaned before it is kept (:func:`clean_svg`): no scripts, no event handlers, no
links out of the file.
"""

from __future__ import annotations

import argparse
import json
import re
import sys
import urllib.request
import xml.etree.ElementTree as ET
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

import assetlib  # noqa: E402

CATEGORY = "illustrations"
PICTURE = (".svg", ".png", ".jpg", ".jpeg", ".webp")
SVG_NS = "http://www.w3.org/2000/svg"

HOUSE_STYLE = """House style for this project's illustrations (the picture book "My Own Home, My Own Dome" and the dome books):
- Flat storybook shapes with soft, slightly rounded outlines (stroke #2c1e14 at 3-6 px, round joins), no gradients beyond two-stop sky or glow.
- Palette: paper #faf4e6, ink #2c1e14, rust accent #964818, warm wood #c8914e / #d9b07a, bark #5a3a22, pine #2c5a2a / #3f7a34,
  sky #8fc3e8 to #f0c890 at sunset, dome frame #c8914e, gold #e8b45a.
- A geodesic dome is triangles meeting at nodes: five or six triangles round every node, a flat base ring, never a smooth hemisphere.
- Wedges are pie slices of a log (a 1/8 sector): a sharp point, two straight sawn sides, a curved bark back.
- People are simple, friendly, round-headed figures; Pip is a girl with long brown hair and a green hard hat.
- No words in the picture unless asked. Transparent background unless the request is a whole scene."""


def entries(text: str = "") -> list[dict]:
    """Every picture in the library, newest version of each name, filtered by words in its name."""
    cat = assetlib.load()
    best: dict[str, dict] = {}
    for key, e in cat.items():
        if not e["file"].lower().endswith(PICTURE):
            continue
        if text and text.lower() not in e["name"].lower():
            continue
        if e["name"] not in best or e["version"] > best[e["name"]]["version"]:
            best[e["name"]] = {**e, "key": key}
    out = [{"name": e["name"], "key": e["key"], "file": "assets/" + e["file"], "category": e.get("category", ""),
            "origin": e.get("origin", ""), "prompt": e.get("prompt"), "note": e.get("note", ""), "version": e["version"]}
           for e in best.values()]
    return sorted(out, key=lambda e: (e["category"] != CATEGORY, e["name"]))


def slug(name: str) -> str:
    s = re.sub(r"[^a-z0-9]+", "-", name.lower()).strip("-")
    if not s:
        raise ValueError("a picture needs a name")
    return s[:80]


def clean_svg(text: str) -> str:
    """An SVG safe to keep and show: one <svg> with a viewBox, nothing that runs or reaches out."""
    m = re.search(r"<svg[\s\S]*</svg>", text)
    if not m:
        raise ValueError("no <svg>...</svg> in that")
    src = m.group(0)
    ET.register_namespace("", SVG_NS)
    ET.register_namespace("xlink", "http://www.w3.org/1999/xlink")
    try:
        root = ET.fromstring(src)
    except ET.ParseError as e:
        raise ValueError(f"that SVG does not parse: {e}") from e
    if not root.tag.endswith("svg"):
        raise ValueError("the outer element must be <svg>")
    banned = ("script", "foreignObject", "iframe", "object", "embed", "audio", "video")
    for el in list(root.iter()):
        for child in list(el):
            if any(child.tag.endswith(b) for b in banned):
                el.remove(child)
        for attr in list(el.attrib):
            v = el.attrib[attr]
            if attr.lower().startswith("on"):
                del el.attrib[attr]
            elif attr.endswith("href") and not (v.startswith("#") or v.startswith("data:image/")):
                del el.attrib[attr]
            elif "javascript:" in v.lower():
                del el.attrib[attr]
    if "viewBox" not in root.attrib:
        w, h = root.attrib.get("width", "1000"), root.attrib.get("height", "1000")
        root.attrib["viewBox"] = f"0 0 {re.sub('[^0-9.]', '', w) or 1000} {re.sub('[^0-9.]', '', h) or 1000}"
    root.attrib.pop("xmlns", None)                  # ElementTree writes the namespace itself
    out = ET.tostring(root, encoding="unicode")
    ET.fromstring(out)                               # and what is kept must parse
    if len(out) > 1_500_000:
        raise ValueError("that SVG is over 1.5 MB")
    return out


def add(name: str, data: bytes, ext: str, origin: str, prompt: str | None = None, note: str = "") -> dict:
    """File a picture under its name, as a new version if the name is taken and the picture differs."""
    name = slug(name)
    cat = assetlib.load()
    folder = assetlib.folder(CATEGORY)
    folder.mkdir(parents=True, exist_ok=True)
    versions = [e for e in cat.values() if e["name"] == name]
    if versions:
        newest = max(versions, key=lambda e: e["version"])
        if (assetlib.ASSETS / newest["file"]).read_bytes() == data:
            return {"name": name, "file": "assets/" + newest["file"], "version": newest["version"], "new": False}
    version = max((e["version"] for e in versions), default=0) + 1
    stem = name if version == 1 else f"{name}-v{version}"
    p = folder / f"{stem}{ext}"
    p.write_bytes(data)
    cat[stem] = {"name": name, "version": version, "file": p.relative_to(assetlib.ASSETS).as_posix(), "category": CATEGORY,
                 "note": note, "origin": origin, "original": None, "copy_of": None, "prompt": prompt}
    assetlib.save(cat)
    return {"name": name, "file": "assets/" + cat[stem]["file"], "version": version, "new": True}


def add_svg(name: str, svg: str, origin: str, prompt: str | None = None, note: str = "") -> dict:
    return add(name, clean_svg(svg).encode("utf-8"), ".svg", origin, prompt, note)


def _shape(w: float, h: float) -> str:
    return f'viewBox="0 0 {round(1000 * w / max(w, h))} {round(1000 * h / max(w, h))}"'


def claude_prompt(name: str, description: str, w: float = 1.0, h: float = 1.0, book: str = "") -> str:
    """The words the owner pastes into a Claude Code session here, to have Claude draw it."""
    n = slug(name)
    return f"""Draw an illustration for the Book Studio{f' (book: {book})' if book else ''}, as an SVG, and file it in the library.

Name: {n}
What it shows: {description}
Shape: {_shape(w, h)} (the frame it goes in is {w:.2f} x {h:.2f} in)

{HOUSE_STYLE}

Write the SVG to a scratch file, then file it (it is cleaned and catalogued there):
  py -3.12 -m books.studio.library add {n} <file.svg> --origin claude --prompt "{description.replace('"', "'")}"
Then tell me it is in, and it will show in the studio's Library panel under that name."""


def deepseek_svg(description: str, w: float = 1.0, h: float = 1.0, timeout: int = 180) -> str:
    """Ask DeepSeek to draw it, in the house style, as one SVG."""
    from project_agent import config
    if not config.llm_configured():
        raise RuntimeError("no DeepSeek key: set DEEPSEEK_API_KEY")
    body = {"model": config.llm_model(), "temperature": 0.7, "max_tokens": 8000, "messages": [
        {"role": "system", "content": "You are an illustrator who draws in clean, hand-written SVG. Reply with one complete "
                                      "<svg> element and nothing else: no prose, no code fences, no scripts, no external links.\n\n" + HOUSE_STYLE},
        {"role": "user", "content": f"Draw: {description}\nUse {_shape(w, h)}. Make it rich: layered shapes, a sense of light, "
                                    "and real detail, as a picture-book illustrator would."}]}
    req = urllib.request.Request(config.llm_api_base() + "/chat/completions", data=json.dumps(body).encode("utf-8"),
                                 headers={"Authorization": f"Bearer {config.llm_api_key()}", "Content-Type": "application/json"})
    with urllib.request.urlopen(req, timeout=timeout) as r:
        reply = json.loads(r.read().decode("utf-8"))["choices"][0]["message"]["content"]
    return clean_svg(reply)


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(prog="books.studio.library", description="The Book Studio's picture library.")
    sub = ap.add_subparsers(dest="cmd", required=True)
    a = sub.add_parser("add", help="file an SVG (or PNG/JPG) as an illustration")
    a.add_argument("name"); a.add_argument("file", type=Path)
    a.add_argument("--origin", default="claude"); a.add_argument("--prompt"); a.add_argument("--note", default="")
    ls = sub.add_parser("list", help="list the pictures")
    ls.add_argument("text", nargs="?", default="")
    pr = sub.add_parser("prompt", help="write the request to paste to Claude")
    pr.add_argument("name"); pr.add_argument("description"); pr.add_argument("--w", type=float, default=1); pr.add_argument("--h", type=float, default=1)
    args = ap.parse_args(argv)
    if args.cmd == "add":
        ext = args.file.suffix.lower()
        if ext == ".svg":
            got = add_svg(args.name, args.file.read_text(encoding="utf-8"), args.origin, args.prompt, args.note)
        elif ext in PICTURE:
            got = add(args.name, args.file.read_bytes(), ext, args.origin, args.prompt, args.note)
        else:
            raise SystemExit(f"not a picture: {args.file}")
        print(f"{'filed' if got['new'] else 'already filed'}: {got['file']} (v{got['version']})")
    elif args.cmd == "list":
        for e in entries(args.text):
            print(f"{e['name']:<48} {e['category']:<14} {e['origin']:<10} {e['file']}")
    else:
        print(claude_prompt(args.name, args.description, args.w, args.h))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
