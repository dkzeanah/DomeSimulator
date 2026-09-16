"""Tests for Codex-only video scene capture and its export boundary.

Set TWO_TREES_TEST_OPENGL=1 for the optional real GPU integration test.
The default suite does not open a window or need video dependencies.
"""
from __future__ import annotations

import json
import os
from pathlib import Path
import subprocess
import tempfile
import unittest
from unittest.mock import patch

from . import scene_stills as stills


SCENE = {"id": "harvest:tree", "lesson_key": "harvest", "chapter_slug": "tree",
         "title": "Two trees", "stage": "hv_harvest", "progress": 0.3}


class SceneRequestTests(unittest.TestCase):
    def test_catalog_progress_and_explicit_progress(self):
        request = stills._validated_request(SCENE, None, 1600, 1000, "original")
        self.assertEqual(request["progress"], 0.3)
        self.assertEqual(stills._validated_request(SCENE, 0, 1600, 1000, "clean")["progress"], 0)
        self.assertEqual(stills._validated_request(SCENE, 1, 1600, 1000, "math")["progress"], 1)
        self.assertEqual(SCENE["progress"], 0.3)

    def test_invalid_progress_fails_before_starting_worker(self):
        for progress in (-0.001, 1.001, float("nan"), float("inf"), "later"):
            with self.subTest(progress=progress), self.assertRaises(ValueError):
                stills.render_scene_still(SCENE, Path("unused"), progress)

    def test_unknown_overlay_and_missing_identity_fail(self):
        for scene, overlay in ((SCENE, "approximate"), ({"lesson_key": "harvest"}, "original")):
            with self.assertRaises(ValueError):
                stills._validated_request(scene, None, 1600, 1000, overlay)

    def test_dimensions_are_bounded_integers(self):
        for width in (0, -1, 200, 5000, True, 1600.5, "1600"):
            with self.subTest(width=width), self.assertRaises(ValueError):
                stills._validated_request(SCENE, None, width, 1000, "original")

    def test_metadata_cannot_send_nonfinite_values(self):
        with self.assertRaises(ValueError):
            stills._validated_request({**SCENE, "camera": [float("nan"), 20, 25]},
                                      None, 1600, 1000, "original")


class ExportBoundaryTests(unittest.TestCase):
    def fake_worker(self, command, **options):
        self.assertNotIn("shell", options)
        self.assertIn("-B", command)
        self.assertEqual(options["env"]["PYTHONDONTWRITEBYTECODE"], "1")
        self.assertEqual(Path(options["cwd"]), stills.ROOT)
        request_path = Path(command[-1])
        job = request_path.parent
        request = json.loads(request_path.read_text(encoding="utf-8"))
        self.assertEqual(request["scene"]["id"], "harvest:tree")
        (job / "still.png").write_bytes(b"test-png")
        stills._json_write(job / "provenance.json", {"recipe": request})
        result = {"path": str(job / "still.png"),
                  "provenance_path": str(job / "provenance.json")}
        stills._json_write(job / "result.json", result)
        return subprocess.CompletedProcess(command, 0)

    def test_repeated_exports_never_overwrite_artifacts(self):
        with tempfile.TemporaryDirectory() as temp, \
                patch.object(stills, "_select_python", return_value="test-python"), \
                patch.object(stills.subprocess, "run", side_effect=self.fake_worker):
            first = stills.render_scene_still(SCENE, Path(temp))
            Path(first["path"]).write_bytes(b"keep-first-version")
            second = stills.render_scene_still(SCENE, Path(temp))
            self.assertNotEqual(first["path"], second["path"])
            self.assertEqual(Path(first["path"]).read_bytes(), b"keep-first-version")
            for result in (first, second):
                job = Path(result["path"]).parent
                self.assertTrue((job / "stdout.log").exists())
                self.assertTrue((job / "stderr.log").exists())

    def test_failure_retains_diagnostics_and_request(self):
        def failed_worker(command, **options):
            options["stderr"].write("GPU driver example failure")
            return subprocess.CompletedProcess(command, 3)

        with tempfile.TemporaryDirectory() as temp, \
                patch.object(stills, "_select_python", return_value="test-python"), \
                patch.object(stills.subprocess, "run", side_effect=failed_worker):
            with self.assertRaisesRegex(stills.SceneRenderError, "GPU driver example failure"):
                stills.render_scene_still(SCENE, Path(temp))
            jobs = list(Path(temp).iterdir())
            self.assertEqual(len(jobs), 1)
            self.assertTrue((jobs[0] / "request.json").is_file())
            self.assertFalse((jobs[0] / "result.json").exists())

    def test_missing_dependencies_identifies_required_runtime(self):
        with patch.dict(os.environ, {"TWO_TREES_SCENE_PYTHON": "chosen-python"}), \
                patch.object(stills.subprocess, "run", return_value=subprocess.CompletedProcess(
                    [], 0, '["pygame", "moderngl"]', "")):
            with self.assertRaisesRegex(stills.SceneRenderError, "TWO_TREES_SCENE_PYTHON"):
                stills._select_python()


@unittest.skipUnless(os.environ.get("TWO_TREES_TEST_OPENGL") == "1", "Optional real OpenGL capture")
class OpenGLSceneTests(unittest.TestCase):
    def test_real_harvest_camera_and_repeatability(self):
        destination = Path(__file__).parent / "workspace" / "scene_test"
        first = stills.render_scene_still(SCENE, destination, width=960, height=600)
        second = stills.render_scene_still(SCENE, destination, width=960, height=600)
        self.assertEqual(first["render_metadata"]["image_sha256"], second["render_metadata"]["image_sha256"])
        self.assertIn("harvest_camera", first["render_metadata"]["resolved_camera"]["function"])
        self.assertEqual(first["recipe"]["chapter_slug"], "tree")
        self.assertTrue(first["render_metadata"]["source_files_sha256"])
        self.assertTrue(first["render_metadata"]["callouts"])
        self.assertIsInstance(first["provenance"], str)


if __name__ == "__main__":
    unittest.main()
