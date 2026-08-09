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
