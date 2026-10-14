"""The project's images and clips: one place, named for what they show, catalogued.

    py -3.12 -m assetlib                     # list the catalogue
    py -3.12 -m assetlib find cover          # assets whose name contains "cover"
    py -3.12 -m assetlib adopt               # dry run: the loose images and clips, and their new names
    py -3.12 -m assetlib adopt --go          # move and rename them (git mv where tracked)

Every picture the books, films, slides and site draw from lives under ``assets/``::

    assets/images/covers/        finished covers, every version (wedge-method-cover, -v2 ...)
    assets/images/cover-art/     cover paintings without lettering
    assets/images/promo/         posters, banners, campaign sheets
    assets/images/scenes/        illustrated scenes: the log, the build, the lab
    assets/images/diagrams/      drawings that carry measurements
    assets/images/infographics/  explainers
    assets/images/photos/        photographs
    assets/video/clips/          short clips
    assets/reference/            other people's documents, kept for reference
    assets/catalogue.json        name, file, what it is, where it came from

A name says what the picture *shows*; nothing in a name says what made it. Where it
came from is kept in the catalogue's ``origin`` field instead (``generated``, with the
prompt when there was one; ``author``; or ``unrecorded``) -- because a publisher may ask
(Amazon KDP asks whether a book's images are AI-generated), and because the prompt is
what makes a picture repeatable. Versions of one picture are squashed under one name:
``name``, ``name-v2``, ``name-v3`` in the order they were made; byte-identical copies are
kept as versions and marked as copies, never deleted.

Code finds an asset by name, never by path: ``assetlib.image("wedge-method-cover", 7)``.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import re
import shutil
import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parent
ASSETS = ROOT / "assets"
CATALOGUE = ASSETS / "catalogue.json"
GALLERY = ROOT / "galleries" / "general"

# The loose files in the project folder: (old name, category, new name, note).
# A new name that appears more than once is one picture in several versions;
# they are numbered in the order the files were made.
LOOSE: tuple[tuple[str, str, str, str], ...] = (
    ("08123fd6-046a-4110-b5a7-87d5517e768a.png", "diagrams", "domesim-knowledge-graph",
     "The project as a media factory: engines, chains, books, voice, agents."),
    ("12b028b8-8b1e-49b7-84ad-3ac71c1e6324.jpg", "scenes", "log-split-eight-wedges-with-chainsaw",
     "A log end split into eight wedges, chainsaw beside it."),
    ("1efc742e-cc2d-4eb1-a290-14ac6988a80b.jpg", "scenes", "quilt-insulation-in-panel",
     "A hand fitting quilted insulation into a triangular frame panel."),
    ("2v_dome_joinery_options_guide.png", "diagrams", "2v-dome-joinery-options",
     "Option A keep raw wedges / option B shave the meeting edges, with seam angles."),
    ("3e9a0d6b-89f3-4012-aa03-7069f4aeae1a.png", "promo", "frankendome-festival-poster",
     "Portrait poster: the dome lit up at night, crowd, jellyfish."),
    ("ChatGPT Image Sep 26, 2026, 01_10_37 AM.png", "promo", "frankendome-festival-poster", "Second take."),
    ("45e61f2a-5fc3-46a7-8dce-25e0655f72ef.jpg", "scenes", "chainsaw-kit-flat-lay",
     "Saw, chaps, helmet, gloves, files, fuel and oil laid out on boards."),
    ("4d953821-14b8-427b-8a01-14efe03d41d4.jpg", "scenes", "wedge-dome-frame-forest-clearing",
     "A finished wedge frame in a pine clearing, portrait."),
    ("Gemini_Generated_Image_tjw0chtjw0chtjw0.jpg", "cover-art", "wedge-method-cover-art",
     "Builder on the frame at sunset, split log and stacked wedges, no lettering."),
    ("Gemini_Generated_Image_tjw0chtjw0chtjw0 (1).jpg", "cover-art", "wedge-method-cover-art",
     "Byte-identical copy of the previous version."),
    ("ChatGPT Image Sep 26, 2026, 12_23_14 AM.png", "cover-art", "wedge-method-cover-art", ""),
    ("ChatGPT Image Sep 27, 2026, 10_21_58 PM.png", "cover-art", "wedge-method-cover-art", ""),
    ("Book-cover-final3.png", "cover-art", "wedge-method-cover-art", "The painting under the lettered final."),
    ("62773c93-df01-4a7f-b049-23969f099e05.png", "scenes", "zeanah-lab-workshop-collage",
     "Zeanah Lab: the dome, the Prius, the workshop, the screens, the books."),
    ("edbb2716-38e8-4222-914d-b9a017e8a315.png", "scenes", "zeanah-lab-workshop-collage", ""),
    ("edbb2716-38e8-4222-914d-b9a017e8a315 (1).png", "scenes", "zeanah-lab-workshop-collage",
     "Byte-identical copy of the previous version."),
    ("c6626206-bc92-4013-a0f2-77006d09cefd.jpg", "scenes", "zeanah-lab-workshop-collage", "Wide version."),
    ("6593b78b-4e7f-49da-a257-2ed5980be985.png", "diagrams", "sheet-cut-40-equilateral-triangles",
     "5 x 10 ft sheet: 40 equilateral triangles, numbered."),
    ("a03229c8-a78e-4056-b00a-f0ba8c7b6da6.png", "diagrams", "sheet-cut-10-equilateral-30-isosceles",
     "5 x 10 ft sheet: 10 equilateral and 30 isosceles triangles."),
    ("824f752a-aca9-495d-a280-5b6536450533.jpg", "scenes", "builder-raising-dome-frame-sunset",
     "A builder inside a half-raised frame at sunset."),
    ("a07448cc-906c-490a-b62c-05af28b88bc4.png", "infographics", "metal-panel-2v-dome-system",
     "An all-metal modular-panel 2V dome, its panels and fixings."),
    ("a5a70720-892b-40a1-b2ac-81d6a90c59f1.jpg", "scenes", "wedge-dome-frame-sunset-clearing",
     "A finished frame among stumps and offcuts, portrait."),
    ("Book_Cover.jpg", "covers", "the-40-hour-cabin-timberframe-cover",
     "The author's illustration under the first title (Geodesic Dome: 2V Timberframe)."),
    ("ChatGPT Image Sep 26, 2026, 12_34_01 AM.png", "covers", "wedge-method-cover",
     "Title set small: 'Geodesic Dome Wedge Method / The 40 Hour Cabin'."),
    ("Book-Cover-Final.png", "covers", "wedge-method-cover", "Was 'final_small' in wedge_book.cover (superseded)."),
    ("Book-Cover-Final2.png", "covers", "wedge-method-cover", ""),
    ("Book_Cover_final.png", "covers", "wedge-method-cover", "Painted, 1792 x 2368: 'final' in wedge_book.cover."),
    ("Gemini_Generated_Image_n2hnp0n2hnp0n2hn.jpg", "covers", "wedge-method-cover", ""),
    ("ChatGPT Image Sep 27, 2026, 09_31_39 PM.png", "covers", "wedge-method-cover", ""),
    ("Gemini_Generated_Image_ilko1gilko1gilko.jpg", "covers", "wedge-method-cover", ""),
    ("ChatGPT Image Sep 27, 2026, 09_35_23 PM.png", "covers", "wedge-method-cover", ""),
    ("book-cover-asyma.png", "covers", "wedge-method-cover", "The asymmetric layout."),
    ("Book-cover-final4.png", "covers", "wedge-method-cover", "The painting wedge_book.cover_type letters."),
    ("image-1790564995231.png", "covers", "wedge-method-cover-3d-render",
     "The cover as a 3-D render (the cover scene), lettered."),
    ("channel.png", "infographics", "seam-module-channel",
     "The seam module: water capture, ventilation, desiccant; cross-sections and modes."),
    ("ChatGPT Image Sep 20, 2026, 02_23_35 AM.png", "promo", "frankendome-dome-park-brochure",
     "A dome park brochure sheet: the hero dome and seven fit-outs."),
    ("ChatGPT Image Sep 26, 2026, 01_06_34 AM.png", "promo", "polygonal-jellyfish-poster",
     "Portrait poster: a lit faceted jellyfish over a crowd."),
    ("Codex Image Sep 8, 2026, 09_36_05 PM.png", "scenes", "wedge-dome-frame-hilltop",
     "A finished frame on a hill, logs and a stump in front."),
    ("dodeca.png", "diagrams", "nested-polygons-construction",
     "Triangle to dodecagon, each inscribed in a circle, stacked."),
    ("dome1.png", "photos", "dome-model-photo", "A small dome model on a stand."),
    ("ec190b5a-1c63-4158-a544-053a4e1c846f.jpg", "scenes", "fallen-tree-forest", "A wind-thrown pine across a forest floor."),
    ("Gemini_Generated_Image_i3cfuyi3cfuyi3cf.jpg", "scenes", "fallen-tree-forest", "Misty, with a chainsaw on the trunk."),
    ("frank.jpg", "scenes", "frankendome-salvage-dome-backyard", "A patched salvage dome under a blue tarp."),
    ("Frankendome-kickstarter.png", "promo", "frankendome-interior-cutaway",
     "A wedge dome cut away to show the furnished room, the core and the deck."),
    ("Gemini_Generated_Image_6h8xhq6h8xhq6h8x.jpg", "promo", "frankendome-party-banner",
     "Wide banner: the lit dome, dancers, 'FRANKENDOME! 2V wedge dome -- built from raw timber'."),
    ("FrankenDomeCover.jpg", "promo", "frankendome-party-banner", ""),
    ("Gemini_Generated_Image_lzme2qlzme2qlzme.jpg", "promo", "frankendome-party-banner", ""),
    ("Gemini_Generated_Image_p8n8cxp8n8cxp8n8.jpg", "promo", "frankendome-party-banner", ""),
    ("Gemini_Generated_Image_p8n8cxp8n8cxp8n8 (1).jpg", "promo", "frankendome-party-banner",
     "Byte-identical copy of the previous version."),
    ("Gemini_Generated_Image_1jz4q51jz4q51jz4.jpg", "promo", "frankendome-party-banner", ""),
    ("Gemini_Generated_Image.jpeg", "diagrams", "geo-home-2v-kit-exploded-blueprint",
     "An exploded blueprint of a 2V dome kit."),
    ("Gemini_Generated_Image_5s9cqj5s9cqj5s9c.jpg", "scenes", "builder-at-finished-dome-lakeside",
     "Builder beside a skinned dome at a lake, sunset."),
    ("Gemini_Generated_Image_7i6elq7i6elq7i6e.jpg", "scenes", "wedge-frame-hub-closeup",
     "The pinwheel of wedge members from inside."),
    ("Gemini_Generated_Image_83jtyv83jtyv83jt.jpg", "scenes", "log-split-eight-wedges-painted",
     "A painted log end split in eight, chainsaw behind."),
    ("Gemini_Generated_Image_8lfq0e8lfq0e8lfq.jpg", "scenes", "prius-powered-sawmill",
     "A Prius on stands driving a sawmill in a yard."),
    ("Gemini_Generated_Image_ou3i5qou3i5qou3i.jpg", "diagrams", "prius-mobile-power-plant-schematic",
     "Technical schematic: the Prius as a mobile power plant for a sawmill."),
    ("Gemini_Generated_Image_nvqyaanvqyaanvqy.jpg", "scenes", "builder-with-coffee-quilted-dome",
     "A man with a mug before a quilt-skinned dome at dawn."),
    ("Gemini_Generated_Image_o7ybifo7ybifo7yb.jpg", "scenes", "quilt-skin-seam-closeup",
     "A gloved hand pressing the quilt skin into a seam."),
    ("Gemini_Generated_Image_ojhj89ojhj89ojhj.jpg", "scenes", "wedge-joint-threaded-rod-closeup",
     "Two wedge ends with threaded rod, close."),
    ("image-1789236638297.png", "infographics", "one-tree-every-rung-value-ladder",
     "One pine: standing, burned, sawn, split, the structure it replaces."),
    ("rings-render.png", "diagrams", "2v-hemisphere-ring-heights",
     "2V hemisphere: level heights and ring diameters, with the table."),
    ("seam.png", "diagrams", "seam-key-cross-section", "The key in a seam between two panels."),
    ("watermarked_img_5892202830459649691.jpg", "scenes", "wedge-dome-forest-golden-light",
     "A frame in a forest in low gold light, a figure beside it."),
    ("wedges-edges.png", "diagrams", "wedge-pair-edge-arrangements", "Four ways two wedges can meet."),
    # clips
    ("Create_a_highly_detailed_anima.mp4", "clips", "chainsaw-mill-rig-exploded",
     "The chainsaw mill rig, exploded and labelled."),
    ("ks-gemini.mp4", "clips", "utility-core-column-interior", "The utility column inside a skinned dome."),
    ("Stem_cell_dome_campaign_i.mp4", "clips", "brick-dome-crane-lift",
     "A brick-built dome, its cap lifted by a toy crane."),
    ("Stem_cell_dome_campaign_i (1).mp4", "clips", "pinwheel-hub-closeup", "Wedge pinwheel, close."),
    # other people's documents
    ("FireShot Capture 011 - 2V Geodesic Dome Calculator Software in Feet and Inches for Calcula_ - "
     "[www.ziptiedomes.com].pdf", "reference", "ziptiedomes-2v-calculator-page",
     "A saved web page: the ziptiedomes.com 2V calculator. Someone else's work; reference only."),
    ("f8b9f1ac-3fed-4c60-ab55-de4c2f30d07b.pdf", "reference", "ziptiedomes-2v-calculator-page",
     "A second save of the same page."),
)
AUTHOR = {"Book_Cover.jpg"}                 # wedge_book/cover.py: "the author's illustration"
_GENERATED = re.compile(r"ChatGPT|Gemini|Codex|^Create_a_|ks-gemini|Stem_cell_dome_campaign|^watermarked_img")

# The gallery: generated images, each with its prompt beside it. Named by prompt.
GALLERY_SERIES = (
    ("Frankendome", "promo", "frankendome-hero-square", "Square hero image for the Frankendome campaign."),
    ("Book cover illustration", "cover-art", "wedge-method-cover-line-drawing",
     "Black-and-white technical-drawing cover illustration."),
    ("POLYGONAL JELLYFISH", "promo", "polygonal-jellyfish-hero-square", "Square hero image: the faceted jellyfish."),
)

DIRS = {"clips": Path("video") / "clips", "reference": Path("reference")}


def folder(category: str) -> Path:
    return ASSETS / DIRS.get(category, Path("images") / category)


def _md5(p: Path) -> str:
    h = hashlib.md5()
    with p.open("rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def _tracked() -> set[str]:
    out = subprocess.run(["git", "ls-files", "-z"], cwd=ROOT, capture_output=True, text=True).stdout
    return set(out.split("\0"))


def plan() -> list[dict]:
    """Every loose file and gallery image, with where it goes and its catalogue entry."""
    rows = []
    for old, category, name, note in LOOSE:
        src = ROOT / old
        if src.is_file():
            origin = "author" if old in AUTHOR else ("generated" if _GENERATED.search(old) else "unrecorded")
            rows.append(dict(src=src, category=category, name=name, note=note, origin=origin,
                             original=old, prompt=None, made=src.stat().st_mtime))
    if GALLERY.is_dir():
        for meta in sorted(GALLERY.glob("*.info.json")):
            data = json.loads(meta.read_text(encoding="utf-8"))
            prompt = data.get("info", {}).get("prompt", "") or ""
            image = next((p for p in GALLERY.glob(meta.name.replace(".info.json", ".*")) if p != meta), None)
            if image is None:
                continue
            for key, category, name, note in GALLERY_SERIES:
                if key in prompt:
                    break
            else:
                category, name, note = "promo", "gallery-image", "Unmatched gallery image."
            rows.append(dict(src=image, category=category, name=name, note=note, origin="generated",
                             original=f"galleries/general/{image.name}", prompt=prompt,
                             made=data.get("meta", {}).get("date", 0) / 1000 or image.stat().st_mtime))
    # Number the versions of each name in the order made; mark byte-identical repeats.
    by_name: dict[tuple[str, str], list[dict]] = {}
    for r in rows:
        by_name.setdefault((r["category"], r["name"]), []).append(r)
    for (category, name), group in by_name.items():
        group.sort(key=lambda r: r["made"])
        seen: dict[str, str] = {}
        existing = _existing_versions(category, name)
        for k, r in enumerate(group, start=existing + 1):
            stem = name if k == 1 else f"{name}-v{k}"
            r["dst"] = folder(category) / f"{stem}{r['src'].suffix.lower().replace('.jpeg', '.jpg')}"
            digest = _md5(r["src"])
            r["copy_of"] = seen.get(digest)
            if r["copy_of"] and r["origin"] == "unrecorded":      # a copy is what its original is
                r["origin"] = next(x["origin"] for x in group if x.get("dst") is not None
                                   and x["dst"].stem == r["copy_of"])
            seen.setdefault(digest, r["dst"].stem)
            r["version"] = k
    return rows


def _existing_versions(category: str, name: str) -> int:
    d = folder(category)
    if not d.is_dir():
        return 0
    found = [p for p in d.iterdir() if re.fullmatch(rf"{re.escape(name)}(-v\d+)?", p.stem)]
    return max((int(m.group(1)) if (m := re.search(r"-v(\d+)$", p.stem)) else 1 for p in found), default=0)


def adopt(go: bool = False) -> None:
    rows = plan()
    for r in rows:
        tag = f"  (copy of {r['copy_of']})" if r["copy_of"] else ""
        print(f"{r['original'][:58]:58s} -> {r['dst'].relative_to(ROOT).as_posix()}{tag}")
    print(f"{len(rows)} files")
    if not go:
        print("dry run; add --go to move")
        return
    tracked = _tracked()
    catalogue = load()
    for r in rows:
        r["dst"].parent.mkdir(parents=True, exist_ok=True)
        if r["dst"].exists():
            raise FileExistsError(r["dst"])
        rel = r["src"].relative_to(ROOT).as_posix()
        if rel in tracked:
            subprocess.run(["git", "mv", rel, r["dst"].relative_to(ROOT).as_posix()], cwd=ROOT, check=True)
        else:
            os.replace(r["src"], r["dst"])
        if r["prompt"]:
            meta = GALLERY / r["src"].name.rsplit(".", 1)[0]
            sidecar = meta.with_name(meta.name + ".info.json")
            if sidecar.is_file():
                if sidecar.relative_to(ROOT).as_posix() in tracked:
                    subprocess.run(["git", "rm", "-q", "--cached", sidecar.relative_to(ROOT).as_posix()],
                                   cwd=ROOT, check=True)
                sidecar.unlink()
            r["dst"].with_name(r["dst"].stem + ".prompt.md").write_text(r["prompt"], encoding="utf-8")
        catalogue[r["dst"].stem] = {
            "name": r["name"], "version": r["version"], "file": r["dst"].relative_to(ASSETS).as_posix(),
            "category": r["category"], "note": r["note"], "origin": r["origin"], "original": r["original"],
            "copy_of": r["copy_of"], "prompt": (r["dst"].stem + ".prompt.md") if r["prompt"] else None}
    save(catalogue)
    if GALLERY.is_dir() and not any(GALLERY.iterdir()):
        GALLERY.rmdir()
        if not any(GALLERY.parent.iterdir()):
            GALLERY.parent.rmdir()
    print(f"moved; catalogue {CATALOGUE.relative_to(ROOT)}")


# ---------------------------------------------------------------------------


def load() -> dict:
    return json.loads(CATALOGUE.read_text(encoding="utf-8")) if CATALOGUE.is_file() else {}


def save(catalogue: dict) -> None:
    CATALOGUE.parent.mkdir(parents=True, exist_ok=True)
    CATALOGUE.write_text(json.dumps(dict(sorted(catalogue.items())), indent=1, ensure_ascii=False) + "\n",
                         encoding="utf-8")


def image(name: str, version: int | None = None) -> Path:
    """An asset's file by name: the newest version, or the one asked for."""
    entries = [e for e in load().values() if e["name"] == name]
    if version is not None:
        entries = [e for e in entries if e["version"] == version]
    if not entries:
        raise KeyError(f"no asset named {name!r}" + (f" version {version}" if version else ""))
    return ASSETS / max(entries, key=lambda e: e["version"])["file"]


def find(text: str) -> list[dict]:
    return [e for e in load().values() if text.lower() in e["name"]]


def renamed(original: str) -> Path | None:
    """Where a file that used to be called ``original`` went."""
    for e in load().values():
        if e["original"] == original:
            return ASSETS / e["file"]
    return None


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(prog="assetlib")
    sub = ap.add_subparsers(dest="cmd")
    f = sub.add_parser("find")
    f.add_argument("text")
    a = sub.add_parser("adopt")
    a.add_argument("--go", action="store_true")
    args = ap.parse_args(argv)
    if args.cmd == "adopt":
        adopt(args.go)
        return 0
    rows = find(args.text) if args.cmd == "find" else list(load().values())
    for e in sorted(rows, key=lambda e: (e["category"], e["name"], e["version"])):
        print(f"{e['category']:13s} {e['name']:42s} v{e['version']:<3d} {e['origin']:10s} {e['file']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
