"""The title page of *The 40 Hour Cabin: Zome Zoomer*.

    py -3.12 -m wedge_zome.cover            # a new numbered PNG + PDF in deliverables/book/

The Complete Edition's cover scene -- the sunset, the forest, the ground, the
deck, the log, the saw and the wedges (:mod:`wedge_book.cover_scene`) -- with
the wedge zome standing on the deck where the dome stands, built at true size
from :mod:`wedge_zome.geometry`, and lettered by :func:`wedge_book.cover_type.compose`
so it is plainly a book of the same series.
"""

from __future__ import annotations

import math
from pathlib import Path

import numpy as np

from . import geometry as g

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "deliverables" / "book"
STEM = "zome-zoomer-title-page"
SUBTITLE = "ZOME ZOOMER"
IN = 0.0254


def zome_batch(deck_top: float):
    """The zome in the cover scene's metres, its sill on the deck."""
    from two_v_demo.render_kit import TriangleBatch
    from wedge_book import cover_scene as cs

    m = g.build("wedge")
    b = TriangleBatch()
    lift = deck_top + g.D["sill_in"] * IN

    def w(p):
        return np.array([p[0] * IN, p[1] * IN, p[2] * IN + lift])

    def solid(a_ring, b_ring, colour):
        centre = np.mean(a_ring + b_ring, axis=0)

        def face(pts, col):
            n = np.cross(pts[1] - pts[0], pts[2] - pts[0])
            if np.linalg.norm(n) < 1e-12:
                return
            n = n / np.linalg.norm(n)
            if n @ (np.mean(pts, axis=0) - centre) < 0:
                pts, n = pts[::-1], -n
            for k in range(1, len(pts) - 1):
                b.triangle(pts[0], pts[k], pts[k + 1], col, n)

        face(a_ring, cs.PINE_END)
        face(b_ring, cs.PINE_END)
        n = len(a_ring)
        for k in range(n):
            face([a_ring[k], a_ring[(k + 1) % n], b_ring[(k + 1) % n], b_ring[k]],
                 cs.PINE_FACE if k == 0 else cs.PINE_SAWN)

    for p in m.panels:
        for s in p.sticks:
            tails, heads = s.ends
            solid([w(t) for t in tails], [w(h) for h in heads], cs.PINE_FACE)
    from square_book import geometry as sg
    side = sg.Pair(sg.Wedge(m.log_in, 4), "back").planed[0]
    for i, height in m.posts:
        top = m.vertices[i]
        foot = top - np.array([0, 0, height + g.D["sill_in"]])
        h = side / 2
        sq = [np.array(c) for c in ((-h, -h, 0), (h, -h, 0), (h, h, 0), (-h, h, 0))]
        solid([w(foot + q) for q in sq], [w(top - np.array([0, 0, 1.0]) + q) for q in sq], cs.PINE_SAWN)
    return b


def render():
    from PIL import Image

    from wedge_book import cover_scene as cs

    s = cs.sizes()
    cam = cs.Camera(eye=(0.6, -9.6, 1.45), target=(0.05, -0.6, 1.95), fov=50.0)
    eye = np.array(cam.eye)
    batches = [cs.ground_batch(), cs.deck_batch(s), zome_batch(cs.DECK_TOP), cs.props(s, eye), cs.forest()]
    width, height = cs.FULL_W, cs.FULL_H
    rgba = cs.render_rgba(batches, width, height, cam)
    sky = cs.backdrop(width, height, cs.horizon_row(cam, width, height))
    alpha = rgba[..., 3:4]
    img = cs.grade(rgba[..., :3] * alpha + sky * (1 - alpha))
    return Image.fromarray((img * 255).astype(np.uint8))


def build() -> tuple[Path, Path]:
    from two_v_demo.deliverables import next_version_path
    from wedge_book import cover_type

    page = cover_type.compose(render(), subtitle=SUBTITLE)
    OUT.mkdir(parents=True, exist_ok=True)
    png = next_version_path(OUT / f"{STEM}.png")
    pdf = png.with_suffix(".pdf")
    if pdf.exists():
        raise FileExistsError(f"{pdf.name} already exists; deliverables are never overwritten")
    page.save(png)
    page.convert("RGB").save(pdf, resolution=300.0)
    return png, pdf


if __name__ == "__main__":
    for path in build():
        print(f"wrote {path}")
