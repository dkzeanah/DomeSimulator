"""Focused tests for the Codex edition's read-only scene matching boundary."""
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

from two_trees_codex import scene_catalog as sc


def fixture():
    scenes = [
        {"id": "harvest:explode", "lesson_key": "harvest", "chapter_slug": "explode",
         "title": "Split the trunk into wedges", "summary": "Eight sections, eight wedges in each section.",
         "narration": ["Two trees yield one hundred twenty eight wedge struts."],
         "equations": [], "stage": "hv_harvest", "terms": ["wedge", "section"],
         "concepts": ["harvest"], "source": {"ref": "film:harvest/explode"}},
        {"id": "wedge:pinwheel", "lesson_key": "wedge", "chapter_slug": "pinwheel",
         "title": "The pinwheel joint", "summary": "Each butt end meets the side of the next strut.",
         "narration": ["Two separate members follow each triangle axis."], "equations": [],
         "stage": "wg_pinwheel", "terms": ["pinwheel", "strut"], "concepts": [],
         "source": {"ref": "film:wedge/pinwheel"}},
    ]
    terms = [
        {"key": "wedge", "name": "Wedge", "aliases": [], "scene": "harvest:hv_harvest"},
        {"key": "section", "name": "Section", "aliases": ["six foot section"], "scene": "harvest:hv_harvest"},
        {"key": "pinwheel", "name": "Pinwheel joint", "aliases": ["cyclic joint"], "scene": "wedge:wg_pinwheel"},
        {"key": "strut", "name": "Strut", "aliases": [], "scene": ""},
    ]
    return {"scenes": scenes, "terms": terms, "concepts": [{"key": "harvest", "name": "Harvest yield", "terms": ["wedge", "section"]}]}


class CatalogTests(unittest.TestCase):
    def test_plural_phrase_match_has_real_evidence(self):
        result = sc.suggest_scenes("The trunk gives six-foot sections and eight wedges each.", fixture())
        self.assertEqual(result[0]["scene"]["id"], "harvest:explode")
        self.assertIn("section", result[0]["matched_terms"])
        self.assertIn("wedges", result[0]["evidence"]["book_excerpt"])
        self.assertEqual(result[0]["evidence"]["source_ref"], "film:harvest/explode")
        self.assertTrue(any("Concept:" in reason for reason in result[0]["reasons"]))

    def test_alias_maps_to_existing_painter(self):
        result = sc.suggest_scenes("A cyclic joint places the butt end at the next member's side.", fixture())
        self.assertEqual(result[0]["scene"]["id"], "wedge:pinwheel")
        self.assertIn("pinwheel", result[0]["matched_terms"])
        self.assertTrue(any("maps to" in reason for reason in result[0]["reasons"]))

    def test_no_substring_match_or_empty_fallback(self):
        self.assertEqual(sc.suggest_scenes("strutting sectional pinwheelsauce", fixture()), [])
        self.assertEqual(sc.suggest_scenes("the and of", fixture()), [])
        self.assertEqual(sc.suggest_scenes("wedge", fixture(), limit=0), [])

    def test_deterministic_and_does_not_mutate_input(self):
        catalog = fixture()
        before = json.dumps(catalog, sort_keys=True)
        result = sc.suggest_scenes("wedges struts and pinwheel joints", catalog)
        self.assertEqual(result, sc.suggest_scenes("wedges struts and pinwheel joints", catalog))
        self.assertEqual(before, json.dumps(catalog, sort_keys=True))
        self.assertEqual(sc.get_scene("wedge:pinwheel", catalog)["chapter_slug"], "pinwheel")
        with self.assertRaises(KeyError):
            sc.get_scene("wedge:unknown", catalog)

    def test_export_is_new_file_and_cannot_leave_codex(self):
        with tempfile.TemporaryDirectory(dir=sc.PACKAGE) as folder:
            first = sc.export_catalog(folder, fixture())
            second = sc.export_catalog(folder, fixture())
            self.assertNotEqual(first, second)
            self.assertEqual(json.loads(first.read_text(encoding="utf-8")), fixture())
        with self.assertRaises(ValueError):
            sc.export_catalog(sc.ROOT / "book", fixture())

    def test_import_failure_is_isolated_and_reported(self):
        row = dict(fixture()["scenes"][0], chapter_index=0, camera=[0, 20, 20], progress=.88, duration=26)
        row.update(terms=[], concepts=[])
        metadata = {"terms": [], "concepts": [], "categories": [], "objects": [], "warnings": []}
        def worker(mode, timeout=30):
            if mode == "registry":
                return None, "registry failed"
            if mode == "two_v_demo.lesson_broken":
                return None, "broken timed out"
            if mode == "metadata":
                return dict(metadata), None
            return {"scenes": [row]}, None
        with patch.object(sc, "_run_worker", side_effect=worker), patch.object(sc, "_registry_modules", return_value={"two_v_demo.lesson_broken": [], "two_v_demo.lesson_good": []}):
            data = sc.build_catalog(refresh=True, include_inventory=False)
        self.assertEqual(len(data["scenes"]), 1)
        self.assertIn("broken timed out", data["source"]["warnings"])
        sc._CACHE = None

    def test_graphics_import_blocker(self):
        with self.assertRaises(ImportError):
            sc._NoGraphics().find_spec("moderngl")
        with self.assertRaises(ImportError):
            sc._NoGraphics().find_spec("two_v_demo.app")
        self.assertIsNone(sc._NoGraphics().find_spec("numpy"))


if __name__ == "__main__":
    unittest.main()
