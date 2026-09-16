"""Populate this edition's library and make append-only review exports."""
from pathlib import Path
import json

from .storage import BookStore, PACKAGE, words, new_page


def prepare():
    store = BookStore()
    book = store.book
    renders = sorted((store.home / "rendered").glob("*/inventory.png"))
    if not renders:
        from .render import render_all
        records = render_all(store.home / "rendered")
        render_dir = records[0][0].parent
    else:
        render_dir = renders[-1].parent
    existing = {a.get("source_key") for a in book["assets"].values()}
    placement = {
        "point_dome_in": ("codex-title", "Raw-wedge dome: point toward dome interior; 120 independent panel members."),
        "point_dome_out": ("codex-wedge-orientations", "Raw-wedge dome: point toward exterior."),
        "point_panel_in": ("codex-wedge-orientations", "Raw-wedge dome: point toward the triangular panel interior."),
        "point_panel_out": ("codex-wedge-orientations", "Raw-wedge dome: point across the panel boundary."),
        "pinwheel-pair": ("codex-joint-geometry", "Two separate cyclic pinwheel triangles, each with three members. Two members remain at their shared axis. Colors identify member ownership."),
        "geodesic": ("codex-counts", "2V reference topology: 40 faces, 26 vertices, 65 unique edges."),
        "hex-dome": ("codex-project-atlas", "The hex tool's truncated-icosahedron dome selection; a distinct construction study."),
        "zome": ("codex-project-atlas", "The zome tool's default polar zome; a distinct rhombic-panel geometry."),
        "inventory": ("codex-tree-ledger", "Eight sections per tree, eight potential blanks per section: 128 gross blanks and a target of 120 members."),
    }
    for name, (page_id, caption) in placement.items():
        source_key = "initial-plate-" + name
        if source_key in existing:
            continue
        key = store.add_asset(render_dir / (name + ".png"), caption,
                              "Rendered from existing DomeSim model geometry; see two_trees_codex/render.py. Print colors are illustrative.")
        book["assets"][key]["source_key"] = source_key
        next(p for p in book["pages"] if p["id"] == page_id)["figures"].append(key)
    # Preserve generative artwork as clearly labeled alternatives. Technical pages
    # keep the actual model plates, including the author's pinwheel correction.
    for path in sorted((PACKAGE / "artwork").glob("*.png")):
        source_key = "art-" + path.stem
        if source_key in existing:
            continue
        caption = "Concept artwork — " + path.stem + ". Geometry review required before technical use."
        key = store.add_asset(path, caption, "AI-generated editorial artwork; not a build photograph or cut diagram.")
        book["assets"][key]["source_key"] = source_key
        if path.stem == 'pinwheel-illustrated-v1':
            book['assets'][key]['caption'] = 'Each central member belongs to a different triangle. Around each triangle, the butt of one member meets the side near the front of the next.'
            book['assets'][key]['provenance'] = 'AI-finished illustration using the actual simulator pinwheel-pair render as the geometry reference; original model plate retained in Chapter 17.'
            page = new_page('Plate — Two triangles, two members at the seam', 'plate', 'explanation',
                'Follow the three differently colored members around either triangle. Each member receives its neighbor near one end and terminates against the side of the next. The two central members are separate pieces, one owned by each panel. This is the cyclic pinwheel arrangement clarified by the author.\n')
            page['id'] = 'codex-pinwheel-illustrated'
            page['figures'] = [key]
            index = next(i+1 for i,p in enumerate(book['pages']) if p['id'] == 'codex-joint-geometry')
            book['pages'].insert(index, page)
    store.save()
    exports = dict(markdown=str(store.export_markdown()), html=str(store.export_html()),
                   bundle=str(store.export_bundle()))
    print(json.dumps(dict(pages=len(book["pages"]), words=sum(words(p["body"]) for p in book["pages"]),
                          images=len(book["assets"]), **exports), indent=2))


if __name__ == "__main__":
    prepare()
