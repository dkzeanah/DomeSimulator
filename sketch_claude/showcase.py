"""Showcase renders: the finished dome, lit for a listing, a post or a pitch.

``build_showcase(spec)`` claims a new numbered folder in ``deliverables/`` and renders into
it: golden hour, a clear day, night with the room lit, the room inside, the clear-skinned
greenhouse version, the bare frame, an exploded axonometric, the view from above, and a
portrait crop of the hero for a phone. ``captions.md`` beside them says what each shows
and gives the figures from the model, so a post never quotes a number by hand.
"""

from __future__ import annotations

from dataclasses import replace
from pathlib import Path

import numpy as np

from . import TAG
from . import model as M
from . import render as R
from .draw import both
from .plans import _hero_lights


def _pts(m: M.Model, tags=("frame", "skin", "base", "door", "glass", "deck", "person")) -> np.ndarray:
    return np.vstack([p.mesh.verts for p in m.pieces if p.tag in tags and len(p.mesh.verts)])


def shots(m: M.Model, size=(2400, 1500)):
    """(file stem, caption, model, camera, style, view) for every showcase picture."""
    W, H = size
    lights = _hero_lights(m, 0.6)
    pts = _pts(m)
    door_y = m.landmarks["door"][1]
    out = [
        ("golden-hour", "Golden hour on the hill: shingled skin, the door open, the stove pipe up through one panel.", m,
         R.framed(pts, (-0.55, 1.0, -0.28), fov=30, width=W, height=H, margin=1.05),
         replace(R.GOLDEN, lights=lights), R.View(door_open=65)),
        ("clear-day", "A clear day: the porch, the windows on the eye-level ring and the skylight.", m,
         R.framed(pts, (0.6, 1.0, -0.25), fov=30, width=W, height=H, margin=1.05), R.DAY, R.View(door_open=20)),
        ("night", "At night, the room lit: the windows, the skylight and the open door glow.", m,
         R.framed(pts, (-0.45, 1.0, -0.22), fov=30, width=W, height=H, margin=1.05),
         replace(R.NIGHT, lights=_hero_lights(m, 1.6)), R.View(door_open=55)),
        ("inside", "Inside: bed, sofa, stove and kitchen under a frame of pinwheeled panels.", m,
         R.Camera((0.35, door_y + 0.55, 1.45), (-0.55, 0.9, 0.8), 68, 0, (0, 0, 1), 0.05, 60, W, H),
         replace(R.INTERIOR, lights=_hero_lights(m, 1.0)), R.View(hide_tags=("person",), door_open=60)),
        ("frame", "The bare frame: every stick a solid, every corner pinwheeled.", m,
         R.framed(_pts(m, ("frame", "base", "door")), (-0.6, 1.0, -0.4), fov=28, width=W, height=H, margin=1.05),
         R.SKETCH, R.View(tags=("frame", "base", "door", "deck", "site", "person"))),
        ("exploded", "Exploded: panels, partial panels, door frame and base sections.", m,
         R.framed(np.vstack([p.mesh.verts + np.asarray(p.explode) * 1.1 for p in m.pieces if p.tag in ("frame", "base", "door") and len(p.mesh.verts)]),
                  (-0.55, 1.0, -0.45), fov=28, width=W, height=H, margin=1.04),
         R.SKETCH, R.View(tags=("frame", "base", "door"), explode=1.1)),
        ("from-above", "From above: the skylight, the stove pipe and the porch.", m,
         R.framed(pts, (0.25, 0.75, -1.0), fov=30, width=W, height=H, margin=0.95), R.DAY, R.View()),
    ]
    clear = M.build(replace(m.spec, skin="clear"))
    cpts = _pts(clear)
    out.append(("greenhouse", "The same frame skinned clear: a greenhouse.", clear,
                R.framed(cpts, (-0.4, 1.0, -0.32), fov=30, width=W, height=H, margin=1.05), R.DAY, R.View()))
    out.append(("phone-hero", "Golden hour, cropped for a phone.", m,
                R.framed(pts, (-0.5, 1.0, -0.3), fov=34, width=1080, height=1350, margin=1.04),
                replace(R.GOLDEN, lights=lights), R.View(door_open=65)))
    return out


def captions(m: M.Model, rows) -> str:
    t = m.tables
    lines = [f"# {m.spec.title} -- showcase ({TAG})", "",
             f"Rendered by Dome Sketch ({TAG}) from the same model the plan set is drawn from.", "",
             "## The figures", "",
             f"- {both(t['diameter_m'])} across the base, {both(t['height_m'])} from the deck to the top",
             f"- {t['floor_m2']:.1f} m² of floor ({t['floor_m2'] * 10.7639:.0f} ft²)",
             f"- {t['panels']} panels: {t['whole']} whole and {t['partial']} partial round the door",
             f"- {t['stick_count']} sticks in {len(t['sticks'])} distinct cuts, from {t['boards']} 8 ft 2x3s",
             f"- {t['sheets']} sheets of plywood skin, {t['windows']} windows and a {t['skylights']}-panel skylight",
             "", "## The pictures", ""]
    for stem, cap, *_ in rows:
        lines.append(f"- **{stem}.png** -- {cap}")
    lines += ["", "The framed-panel method is the one taught by Trillium Domes (trilliumdomes.com); "
              "these pictures and figures are this project's own."]
    return "\n".join(lines) + "\n"


def build_showcase(spec: M.Spec | None = None, folder: Path | None = None) -> Path:
    spec = spec or M.Spec()
    m = M.build(spec)
    if folder is None:
        import medialib
        folder = medialib.new_folder(f"{TAG}-showcase")
    folder.mkdir(parents=True, exist_ok=True)
    rows = shots(m)
    for stem, cap, model, cam, style, view in rows:
        img = R.render(model, cam, style, view)
        img.save(folder / f"{stem}.png")
        print(f"rendered {stem}.png", flush=True)
    (folder / "captions.md").write_text(captions(m, rows), encoding="utf-8")
    return folder
