"""Entry point for Dome Forge.

Launch and configure this from the consolidated launcher
(``py -3.12 launcher.py``). Run it directly with no launcher ticket and
it opens the builder with the default dome.
"""

from __future__ import annotations

import json
from pathlib import Path

import launcher_common as _lc


def _selftest() -> int:
    from .build import build_scene, scene_stats
    from .jigs import STEPS, jig_specs, step_lines, verify as verify_jigs
    from .layers import LAYER_KINDS, LayerStack, default_stack

    stack = default_stack()
    stats = scene_stats(stack)
    # These are the 2V hemisphere's real counts; if the shared geometry
    # ever changes, this fails loudly instead of drawing a wrong dome.
    assert stats["struts"] == 65, stats
    assert stats["short_struts"] + stats["long_struts"] == stats["struts"], stats
    assert stats["panels"] == 40, stats
    assert stats["hubs"] == 26, stats

    opaque, translucent = build_scene(stack, 0.0)
    assert opaque.v and translucent.v, "empty scene"
    assert len(opaque.v) % 10 == 0 and len(translucent.v) % 10 == 0

    # Every registered layer kind must actually build something on its own.
    for kind in LAYER_KINDS:
        solo = LayerStack()
        solo.add(kind.key)
        op, tr = build_scene(solo, 0.4)
        assert op.v or tr.v, f"layer kind produced no geometry: {kind.key}"

    # Animated layers must actually differ over time.
    assert build_scene(stack, 0.0)[1].v != build_scene(stack, 2.0)[1].v

    # Preset round-trip.
    restored = LayerStack.from_json(json.loads(json.dumps(stack.to_json())))
    assert restored.to_json() == stack.to_json()

    # Every strut profile must combine with every fill without blowing up,
    # including deliberately mismatched sets where the three edges have
    # different widths.
    from .catalog import FILL_KEYS, PROFILE_KEYS, PROFILE_BY_KEY
    from .panel import build_panel, inner_outline
    from .build import tint
    from presenter.world import Batch
    import numpy as _np

    corners = [_np.array([0.0, 0.0, 0.0]), _np.array([2.6, 0.0, 0.0]),
               _np.array([1.3, 1.9, 0.0])]
    for profile_key in PROFILE_KEYS:
        for fill_key in FILL_KEYS:
            op, tr = Batch(), Batch()
            build_panel(op, tr, corners, [profile_key] * 3, fill_key, tint)
            assert op.v or tr.v, (profile_key, fill_key)
    mixed = ["log_half", "lumber_2x2", "log_quarter"]
    op, tr = Batch(), Batch()
    build_panel(op, tr, corners, mixed, "wood_planks", tint)
    assert op.v or tr.v, mixed

    # With mismatched widths, each inner corner must still sit exactly its
    # own edge's width in from that edge -- the whole reason the outline is
    # built by intersecting offset lines instead of scaling the triangle.
    flat = _np.array([[0.0, 0.0], [2.6, 0.0], [1.3, 1.9]])
    widths = [PROFILE_BY_KEY[k].width for k in mixed]
    inner = inner_outline(flat, widths)
    for i in range(3):
        p0, p1 = flat[i], flat[(i + 1) % 3]
        direction = (p1 - p0) / _np.linalg.norm(p1 - p0)
        normal = _np.array([-direction[1], direction[0]])
        if _np.dot(normal, flat.mean(axis=0) - p0) < 0:
            normal = -normal
        for corner in (i, (i + 1) % 3):
            distance = float(_np.dot(inner[corner] - p0, normal))
            assert abs(distance - widths[i]) < 1e-9, (i, corner, distance)

    # Pentagons and hourglasses are found from the geometry, so their
    # counts and shapes are asserted rather than assumed.
    from .groups import (JOINT_KEYS, emit_waist, hourglasses, pentagons)
    from .build import DomeContext

    pents, hours = pentagons(), hourglasses()
    assert len(pents) == 6, pents
    assert len(hours) == 10, hours
    assert all(len(set(p.faces)) == 5 for p in pents)
    assert all(len(set(h.faces)) == 2 for h in hours)
    geo_faces = DomeContext(stack.settings.radius).faces
    for hourglass in hours:
        # An hourglass is point-to-point: its two triangles must share
        # exactly one vertex. Sharing two would make them edge
        # neighbours, which is a different thing entirely.
        a = set(int(i) for i in geo_faces[hourglass.faces[0]])
        b = set(int(i) for i in geo_faces[hourglass.faces[1]])
        assert len(a & b) == 1, hourglass
        assert hourglass.waist in (a & b), hourglass
    ctx = DomeContext(stack.settings.radius)
    for key in JOINT_KEYS:
        probe = Batch()
        emit_waist(probe, ctx, hours[0], key, tint)
        assert (probe.v == []) == (key == "none"), key

    # The jig cut list is re-measured off the assembled 3D faces, so the
    # shop drawings and the dome on screen cannot disagree.
    verify_jigs()
    specs = jig_specs(stack.settings.radius)
    assert len(specs) == 2, specs
    assert sum(spec.triangles_needed for spec in specs) == 40, specs
    for spec in specs:
        for step in STEPS:
            step_lines(spec, step)

    print(f"Dome Forge selftest OK "
          f"({len(LAYER_KINDS)} layer kinds, {stats['struts']} struts, "
          f"{stats['panels']} panels, {stats['hubs']} hubs; "
          f"{len(PROFILE_KEYS)}x{len(FILL_KEYS)}="
          f"{len(PROFILE_KEYS) * len(FILL_KEYS)} strut/fill combos; "
          f"{len(pents)} pentagons + {len(hours)} hourglasses, "
          f"{len(JOINT_KEYS)} waist joints; "
          f"jigs verified against the 3D faces, "
          f"{'+'.join(str(s.triangles_needed) for s in specs)} triangles)")
    return 0


def _shots(cfg: dict) -> int:
    """Render stills headlessly -- used to check the dome really looks
    right without needing someone to sit and watch the window."""
    from .app import DomeForgeApp
    from .layers import LayerStack, default_stack

    out = Path(cfg.get("shot_dir") or "dome_forge_shots")
    preset = cfg.get("preset")
    stack = LayerStack.load(Path(preset)) if preset else default_stack()
    size = cfg.get("size", "1600x900")
    width, height = _lc.parse_size(size)
    app = DomeForgeApp(size=(width, height), hidden=True)
    app.stack = stack
    views = [
        ("exterior", 38.0, 22.0, 15.0, False, 0.0),
        ("cutaway", 200.0, 10.0, 7.0, True, 1.3),
        ("top", 90.0, 78.0, 16.0, False, 2.1),
        ("ground", 300.0, -4.0, 12.0, False, 3.4),
    ]
    written = []
    for name, yaw, pitch, distance, cut, when in views:
        app.yaw, app.pitch, app.distance = yaw, pitch, distance
        app.stack.settings.cut_enabled = cut
        app.clock_t = when
        written.append(app.capture(out / f"{name}.png"))
    app.pygame.quit()
    for path in written:
        print(f"saved {path}")
    return 0


def main() -> int:
    cfg = _lc.consume_config("dome_forge")
    action = cfg.get("action", "run")
    if action == "selftest":
        return _selftest()
    if action == "shots":
        return _shots(cfg)
    from .app import launch

    preset = cfg.get("preset")
    if cfg.get("start") == "splitlog":
        from .layers import split_log_stack
        from .app import DomeForgeApp
        size = cfg.get("size", "1600x900")
        try:
            width, height = _lc.parse_size(size)
        except ValueError:
            width, height = 1600, 900
        app = DomeForgeApp(size=(width, height),
                           fullscreen=bool(cfg.get("fullscreen", False)))
        app.stack = split_log_stack()
        app.stack.selected_face = -1
        app.run()
        return 0
    size = cfg.get("size", "1600x900")
    try:
        width, height = _lc.parse_size(size)
    except ValueError:
        width, height = 1600, 900
    launch(
        preset=Path(preset) if preset else None,
        size=(width, height),
        fullscreen=bool(cfg.get("fullscreen", False)),
    )
    return 0
