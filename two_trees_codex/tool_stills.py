"""Print illustrations from the existing native tools, with no shared edits.

Run with the project's graphics Python: ``-m two_trees_codex.tool_stills``.
Every run writes a fresh folder, clean native renders, and reproducible recipes.
The native Forge jig is the mitered-board demonstration; it must not be labeled
as the book's raw-wedge pinwheel connection.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import math
import os
from pathlib import Path
import uuid

from .storage import stamp

ROOT = Path(__file__).resolve().parents[1]


def _hash_sources(names):
    return {name: hashlib.sha256((ROOT / name).read_bytes()).hexdigest()
            for name in names}


def render_tool_stills(output_dir=None, families=("forge", "assembly"), size=(2000, 1400)):
    """Render native clean stills; return asset records plus a manifest path."""
    import numpy as np
    import pygame

    destination = Path(output_dir or ROOT / "two_trees_codex/workspace/expanded-art")
    destination = destination / ("tools-" + stamp() + "-" + uuid.uuid4().hex[:6])
    destination.mkdir(parents=True, exist_ok=False)
    assets = []

    def record(name, title, purpose, caption, source, recipe):
        result = {"path": str((destination / (name + ".png")).resolve()),
                  "title": title, "purpose": purpose, "caption": caption,
                  "provenance": f"Native {source} render; clean scene; source files unchanged.",
                  "recipe": {"schema": "two-trees-native-tool-still/v1",
                             "tool": source, "size": list(size), "overlay": "none",
                             **recipe}}
        assets.append(result)
        (destination / (name + ".json")).write_text(
            json.dumps(result, indent=2) + "\n", encoding="utf-8")
        print(f"Rendered {name}", flush=True)

    if "forge" in families:
        from dome_forge.app import DomeForgeApp
        from dome_forge.layers import default_stack, split_log_stack
        from dome_forge.jigs import STEPS

        app = DomeForgeApp(size=size, hidden=True)
        # Only this instance's overlay is blank. Native shader/meshes are intact.
        app.draw_ui = lambda w, h: pygame.Surface((w, h), pygame.SRCALPHA)
        original_camera = app.camera

        def center_camera():
            if app.mode not in ("panel", "jigs"):
                return original_camera()
            pitch, yaw = math.radians(app.pitch), math.radians(app.yaw)
            target = np.zeros(3, dtype=np.float32)
            eye = target + np.array([app.distance * math.cos(pitch) * math.cos(yaw),
                                    app.distance * math.cos(pitch) * math.sin(yaw),
                                    app.distance * math.sin(pitch)], dtype=np.float32)
            return eye, target

        app.camera = center_camera
        hashes = _hash_sources(["dome_forge/app.py", "dome_forge/build.py",
                                "dome_forge/panel.py", "dome_forge/jigs.py",
                                "dome_forge/layers.py"])

        def forge_shot(name, title, purpose, caption):
            app.capture(destination / (name + ".png"))
            record(name, title, purpose, caption, "Dome Forge", {
                "source_hashes": hashes, "mode": app.mode,
                "yaw": app.yaw, "pitch": app.pitch, "distance": app.distance,
                "centered_without_ui_pan": True, "clock_t": app.clock_t,
                "stack": app.stack.to_json(), "jig_index": app.jig_index,
                "jig_step": STEPS[app.step_index].stage,
                "bench_struts": app.bench_struts, "bench_fill": app.bench_fill})

        try:
            app.stack = split_log_stack()
            app.stack.selected_faces = set()
            app.stack.explode = 0.0
            app.yaw, app.pitch, app.distance = 36, 25, 14
            forge_shot("forge-split-log-shell", "A shell made from individual panels",
                       "Compare interchangeable triangle assemblies and mixed log sections.",
                       "Dome Forge's split-log preset: half-round long seams, quarter-round short seams, and lighter equilateral panels. This is a modeled material option, not the raw-wedge cutting specification.")
            for layer in app.stack.layers:
                layer.visible = layer.kind in ("ground", "assemblies")
                if layer.kind == "assemblies":
                    layer.params["show_fills"] = False
            app.pitch = 38
            forge_shot("forge-double-frame", "Each triangle carries its own frame",
                       "Reveal double members at panel seams and the triangular repetition.",
                       "With infill and water layers hidden, Dome Forge exposes the separate frames of forty triangular panels. Neighboring frames bring separate members to a seam; the pictured joinery remains the Forge preset.")
            app.stack = default_stack()
            app.stack.selected_faces = set()
            app.stack.explode = 0.0
            app.stack.settings.cut_enabled = True
            app.stack.settings.cut_start = 150
            app.stack.settings.cut_sweep = 105
            app.yaw, app.pitch, app.distance = 198, 20, 12.5
            app.clock_t = 1.4
            forge_shot("forge-water-cutaway", "Water collection inside the shell",
                       "Explain enclosure layers, seams, drainage paths, and a central collection system.",
                       "A cutaway of Dome Forge's water-harvesting concept reveals the collector network beneath the panels. The cutaway explains layer relationships; drainage performance still requires project testing.")

            app.set_mode("panel")
            app.yaw, app.pitch, app.distance = 52, 57, 5.7
            app.bench_struts = ["log_half", "lumber_2x2", "log_quarter"]
            app.bench_fill = "polycarbonate"
            forge_shot("forge-panel-profiles", "Three profiles, one panel",
                       "Compare mixed strut sections and an infill opening on the bench.",
                       "Dome Forge's panel bench combines half-round, rectangular, and quarter-round stock around one infill panel. The geometry shows why changing a profile changes the usable opening.")

            app.set_mode("jigs")
            app.jig_index = 1
            app.yaw, app.pitch, app.distance = 64, 65, 7.0
            for stage, name, title, purpose in [
                ("scribe", "forge-jig-layout", "Transfer the triangle to a jig", "Show the layout reference before fences and stops are added."),
                ("fences", "forge-jig-fences", "Fences establish repeatable edges", "Explain locating edges rather than remeasuring each assembly."),
                ("loaded", "forge-jig-loaded", "Load the same shape repeatedly", "Show boards seated against the jig's locating surfaces."),
                ("deficit", "forge-angular-deficit", "Why a flat fan rises into a dome", "Explain angular deficit through an assembled spatial fan.")]:
                app.step_index = next(i for i, step in enumerate(STEPS) if step.stage == stage)
                app.distance = 8.3 if stage == "deficit" else 7.0
                forge_shot(name, title, purpose,
                           title + ". Native Dome Forge jig demonstration using mitered board frames. Use its locating and repeatability principle as a comparison; the book's butt-to-side wedge pinwheel requires its own contact layout.")
        finally:
            pygame.quit()

    if "assembly" in families:
        from assembly_line_simple import AssemblyLineApp, STAGES
        app = AssemblyLineApp(headless=True, size=size)
        app.draw_hud = lambda: None
        hashes = _hash_sources(["assembly_line_simple.py", "dome_model.py", "mesh_builder.py"])
        try:
            shots = [
                ("floor", .98, False, 52, "line-floor", "Begin with the floor", "Show the base platform and floor before the shell hides access."),
                ("frame", .97, False, 32, "line-frame", "Raise the structural shell", "Show the geodesic frame on the transfer carriage before enclosure."),
                ("power", .99, False, 60, "line-services", "Route services while access is open", "Show floor and central service routing before insulation and finishes."),
                ("insulation", .80, True, 55, "line-insulation", "Insulate after the concealed work", "Locate insulation in the build sequence with the shell cut away."),
                ("interior", .98, True, 62, "line-interior", "Fit daily life inside the dome", "Reveal kitchen, bathroom, and sleeping areas through a roof cutaway."),
                ("solar", .99, False, 28, "line-completed", "The enclosed shell at the end of the line", "Compare the finished enclosure with the earlier structural frame.")]
            for stage, fraction, cutaway, pitch, name, title, purpose in shots:
                app.reset()
                idx = next(i for i, phase in enumerate(app.phases)
                           if phase.kind == "work" and STAGES[phase.station].key == stage)
                app.phase_idx = idx
                app.phase_t = app.phase.dur * fraction
                app.force_cutaway = cutaway
                app.update(0)
                x, y, z, *_ = app.dome_pose()
                app.cam_target = np.array([x, y, z + 1.8], dtype=np.float32)
                # View down the track through the gantry opening, so a near
                # upright does not cover the frame or interior demonstration.
                app.cam_yaw, app.cam_pitch = math.radians(0), math.radians(pitch)
                app.cam_dist = 13.8
                app.render()
                app.ctx.finish()
                pixels = app.fbo.read(components=3)
                surface = pygame.image.fromstring(pixels, app.size, "RGB", True)
                pygame.image.save(surface, str(destination / (name + ".png")))
                record(name, title, purpose,
                       f"{title}. Native Assembly Line (Simple) scene at the {stage} station. This factory concept uses its own 3V dome and layered enclosure, and illustrates sequence rather than the two-tree project's measured schedule or final specification.",
                       "Assembly Line (Simple)", {"source_hashes": hashes,
                       "phase_index": idx, "stage": stage, "stage_progress": fraction,
                       "cutaway": cutaway, "cam_target": app.cam_target.tolist(),
                       "yaw_degrees": 0, "pitch_degrees": pitch, "distance": 13.8})
        finally:
            pygame.quit()

    manifest = destination / "manifest.json"
    result = {"schema": "two-trees-native-tool-illustrations/v1", "assets": assets,
              "manifest": str(manifest.resolve()), "count": len(assets)}
    manifest.write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")
    return result


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output-dir")
    parser.add_argument("--families", default="forge,assembly")
    args = parser.parse_args()
    print(json.dumps(render_tool_stills(args.output_dir, args.families.split(",")), indent=2))
