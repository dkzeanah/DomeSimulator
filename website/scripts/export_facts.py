"""Write zeanahlab.com's numbers from the project's own models.

The site never types a figure. This script asks the same functions the films and books
read -- web/export_facts.build() (seed_model + kickstarter: the stem cell, its price, the
goal and the tiers), the book catalogue in web/books.config.json, and the stem cell's own
panel count for the founder plaques -- and writes src/generated/facts.json, which the
React pages import and the API reads.

    py -3.12 scripts/export_facts.py            # regenerate
    py -3.12 scripts/export_facts.py --check    # fail if the committed file is stale
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
SITE = HERE.parent
ROOT = SITE.parent
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "web"))

import export_facts as web_facts  # noqa: E402  (web/export_facts.py: the existing reader)
import seed_model  # noqa: E402
import creator_export  # noqa: E402  (website/scripts/creator_export.py: the Dome Creator's tables)
import portal_tools_export  # noqa: E402  (the 3D Wedge Method and 3D Zome spaces' tables and meshes)
import portal_spaces_export  # noqa: E402  (the Panel Creator, Cell Wall and Masterclass spaces)

OUT = SITE / "src" / "generated" / "facts.json"
CLASSES_OUT = SITE / "src" / "generated" / "dome-classes.json"
MESH_OUT = SITE / "src" / "generated" / "dome-mesh.json"
CREATOR_OUT = SITE / "src" / "generated" / "creator.json"
ZOME_OUT = SITE / "src" / "generated" / "zome.json"
WEDGE_OUT = SITE / "src" / "generated" / "wedge-method.json"
PANEL_OUT = SITE / "src" / "generated" / "panel-creator.json"
CELL_OUT = SITE / "src" / "generated" / "cell-wall.json"
LESSONS_OUT = SITE / "public" / "portal" / "masterclass.json"


def dome_mesh() -> dict:
    """The book's dome as the raw-wedge solver builds it -- nodes, struts and triangles, in
    feet -- so the website's 3-D world stands the solver's own dome, not a drawing of one."""
    from two_v_demo import raw_wedge_bridge
    long_in = float(seed_model.SEED_LONG_EDGE_IN)
    topo = raw_wedge_bridge.simulator().build_2v_hemisphere(long_in)
    ft = lambda v: [round(float(x) / 12.0, 4) for x in v]  # noqa: E731
    return {
        "_generated_by": "website/scripts/export_facts.py from raw_wedge_bridge.simulator().build_2v_hemisphere -- do not edit",
        "longIn": long_in, "radiusFt": round(float(topo.sphere_radius_in) / 12.0, 4), "up": "z",
        "vertices": [ft(v) for v in topo.vertices],
        "edges": [[int(k[0]), int(k[1]), e.edge_type, bool(e.is_base)] for k, e in topo.edges.items()],
        "faces": [[*map(int, f.vertices), f.face_type] for f in topo.faces],
    }

# The dome classes: a 2V wedge dome is fixed by one number, its longest strut. Two domes
# with the same longest strut take the same panels, so members who own one are a class.
# One class per whole inch, solved by the project's own solver at that length.
CLASS_RANGE_IN = range(36, 145)


def classes() -> dict:
    return {
        "_generated_by": "website/scripts/export_facts.py from seed_model.dome_class(long_in) -- do not edit",
        "method": "2V hemisphere, wedge members split from a "
                  f"{seed_model.SEED_TRUNK_DIAMETER_IN:.0f}-inch log, {seed_model.SEED_RADIAL_SPLITS} wedges per log",
        "logIn": seed_model.SEED_TRUNK_DIAMETER_IN, "wedgesPerLog": seed_model.SEED_RADIAL_SPLITS,
        "bookLongIn": seed_model.SEED_LONG_EDGE_IN,
        "notes": {
            "frameLb": "Frame alone, green pine: wood volume x "
                       f"{seed_model.declared('pine_green_lb_per_cuft'):.0f} lb/cu ft "
                       "(seed_model: pine_green_lb_per_cuft, a published density).",
            "cost": "Frame cost from seed_model.frame_group: wedges priced as shelf timber by the cubic inch, "
                    "joining hardware at an assumed rate per joint, seam hose by the foot.",
            "hardware": "Hardware is modelled by cost, not weight, so its share is a share of the frame's cost.",
        },
        "classes": [seed_model.dome_class(n) for n in CLASS_RANGE_IN],
    }


KIDS_VERSE = ROOT / "books" / "my-own-home-my-own-dome" / "verse.md"
KIDS_PREVIEW_STANZAS = 4


def kids_book() -> dict:
    """The children's book's title and opening stanzas, from its manuscript."""
    text = KIDS_VERSE.read_text(encoding="utf-8")
    title = text.splitlines()[0].lstrip("# ").strip()
    verse = text.split("\n---\n", 1)[1]
    stanzas = [s.strip() for s in verse.strip().split("\n\n") if s.strip()]
    return {"title": title, "stanzaCount": len(stanzas), "preview": stanzas[:KIDS_PREVIEW_STANZAS]}


def build() -> dict:
    facts = web_facts.build()
    geo = seed_model.seed_geometry()
    catalogue = json.loads((ROOT / "web" / "books.config.json").read_text(encoding="utf-8"))
    site = json.loads((ROOT / "web" / "site.config.json").read_text(encoding="utf-8"))
    books = [{k: b[k] for k in ("slug", "title", "subtitle", "author", "blurb", "offer", "priceCents",
                                "currency", "includes", "kind", "bookingNote", "codebaseUrl", "amazonUrl", "file")
              if k in b}
             for b in catalogue["books"] if b.get("offer") != "none"]
    facts.update({
        "_generated_by": "website/scripts/export_facts.py from web/export_facts.build(), seed_model and "
                         "web/books.config.json -- do not edit",
        "plaques": {"slots": sum(f.count for f in geo.faces),
                    "source": "seed_model.seed_geometry().faces -- one plaque per panel of the stem cell"},
        "books": books,
        # contents, page counts and headline figures of each book, from the books' own
        # token resolvers -- the same values the books print (web/export_facts.books())
        "bookFacts": web_facts.books(),
        "site": {k: site[k] for k in ("name", "url", "tagline", "email", "kickstarterUrl", "youtubeChannelUrl", "youtubeChannelId", "tiktokHandle", "links")
                 if k in site},
    })
    facts["kidsBook"] = kids_book()
    facts["sources"]["kidsBook"] = KIDS_VERSE.relative_to(ROOT).as_posix()
    facts["sources"]["plaques"] = facts["plaques"]["source"]
    facts["sources"]["books"] = "web/books.config.json"
    return facts


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--check", action="store_true")
    a = ap.parse_args()
    outputs = {OUT: json.dumps(build(), indent=2, ensure_ascii=False) + "\n",
               CLASSES_OUT: json.dumps(classes(), separators=(",", ":"), ensure_ascii=False) + "\n",
               MESH_OUT: json.dumps(dome_mesh(), separators=(",", ":")) + "\n",
               CREATOR_OUT: json.dumps(creator_export.tables(), separators=(",", ":")) + "\n",
               ZOME_OUT: json.dumps(portal_tools_export.zome_tables(), separators=(",", ":")) + "\n"}
    wedge, blobs = portal_tools_export.wedge_tables()
    outputs[WEDGE_OUT] = json.dumps(wedge, separators=(",", ":")) + "\n"
    panel, panel_files = portal_spaces_export.panel_creator()
    blobs.update(panel_files)
    outputs[PANEL_OUT] = json.dumps(panel, separators=(",", ":")) + "\n"
    outputs[CELL_OUT] = json.dumps(portal_spaces_export.cell_wall(), separators=(",", ":"), ensure_ascii=False) + "\n"
    outputs[LESSONS_OUT] = json.dumps(portal_spaces_export.masterclass(), separators=(",", ":"), ensure_ascii=False) + "\n"
    if a.check:
        stale = [p for p, text in outputs.items() if not p.exists() or p.read_text(encoding="utf-8") != text]
        stale += [p for p, blob in blobs.items() if not p.exists() or p.read_bytes() != blob]
        for p in stale:
            print(f"{p} is stale: run py -3.12 scripts/export_facts.py")
        if not stale:
            print("facts.json and dome-classes.json are current")
        return 1 if stale else 0
    OUT.parent.mkdir(parents=True, exist_ok=True)
    for p, text in outputs.items():
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_text(text, encoding="utf-8")
        print(f"wrote {p.relative_to(ROOT)}")
    for p, blob in blobs.items():
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_bytes(blob)
        print(f"wrote {p.relative_to(ROOT)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
