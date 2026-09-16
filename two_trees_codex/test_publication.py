"""Behavior checks for the additive Codex publication exporter."""
import json
import math
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

from .storage import SCHEMA, new_page, seed_pages
from .publication import export_publication, export_readthrough, _pdf_available
from .placement import body_segments, figure_groups, prose_paragraph_count, prose_paragraphs


def fixture_book(body="A tree becomes eight sections, and each section offers eight possible wedges."):
    page = new_page("A counted inventory", body=body)
    page["id"] = "sample-inventory"
    return {"schema": SCHEMA, "title": "2 trees: Build your (D)Home", "author": "", "edition": "Publication test", "pages": [page], "assets": {}}


class PublicationChecks(unittest.TestCase):
    def test_anchors_count_only_prose_and_preserve_markdown(self):
        body = ("## Heading\r\n\r\nFIRST paragraph\r\ncontinued text.\r\n\r\n"
                "- a list entry\r\n> a quoted explanation\r\n"
                "| column | value |\r\n| --- | --- |\r\n| row | 8 |\r\n\r\n"
                "```text\r\nnot a prose paragraph\r\n\r\nwithin code\r\n```\r\n\r\n"
                "SECOND paragraph.\r\n\r\n### Trailing heading\r\n- last item\r\n")
        segments = body_segments(body)
        self.assertEqual("".join(segment["markdown"] for segment in segments), body)
        self.assertEqual([segment["paragraph"] for segment in segments], [1, 2, None])
        self.assertEqual(prose_paragraph_count(body), 2)
        self.assertEqual(prose_paragraphs(body), ["FIRST paragraph\r\ncontinued text.", "SECOND paragraph."])
        self.assertIn("within code", segments[1]["markdown"])
        self.assertEqual(body_segments(""), [])
        self.assertEqual(body_segments("## A heading"), [{"paragraph": None, "markdown": "## A heading"}])

    def test_figure_anchors_resolve_with_stable_tail_fallback(self):
        page = fixture_book("First.\n\nSecond.")["pages"][0]
        anchors = [None, 1, 0, 1, 2, 99, -1, True, "1", 1.0, {}, []]
        assets = {}
        for number, anchor in enumerate(anchors):
            key = "figure-" + str(number)
            assets[key] = {"book_placement": {"after_paragraph": anchor}}
            page["figures"].append(key)
        assets["legacy"] = {}
        page["figures"].append("legacy")
        groups = figure_groups(page, assets)
        self.assertEqual(groups[0], ["figure-2"])
        self.assertEqual(groups[1], ["figure-1", "figure-3"])
        self.assertEqual(groups[2], ["figure-4"])
        self.assertEqual(groups[None], ["figure-0", *["figure-" + str(n) for n in range(5, 12)], "legacy"])

    @unittest.skipUnless(_pdf_available(), "PDF dependencies are optional in the launcher interpreter")
    def test_illustrations_print_at_prose_anchors_and_legacy_tail(self):
        from PIL import Image
        with tempfile.TemporaryDirectory() as temporary:
            home = Path(temporary)
            (home / "assets").mkdir()
            Image.new("RGB", (1000, 200), "#d2b783").save(home / "assets/strip.png")
            book = fixture_book("OPENING SENTINEL.\n\n## Explanation\n\nENDING SENTINEL.\n\n- FINAL LIST SENTINEL")
            definitions = [("legacy", None), ("between", 1), ("before", 0), ("stale", 99)]
            for key, anchor in definitions:
                asset = {"path": "assets/strip.png", "caption": key.upper() + " PLATE"}
                if anchor is not None:
                    asset["book_placement"] = {"after_paragraph": anchor}
                book["assets"][key] = asset
                book["pages"][0]["figures"].append(key)
            result = export_publication(book, home)
            text = "\n".join(page["text"] for page in result["pages"] if page["source_page_id"] == "sample-inventory")
            markers = ["BEFORE PLATE", "OPENING SENTINEL", "BETWEEN PLATE", "ENDING SENTINEL", "FINAL LIST SENTINEL", "LEGACY PLATE", "STALE PLATE"]
            positions = [text.index(marker) for marker in markers]
            self.assertEqual(positions, sorted(positions))
            self.assertEqual([figure["asset_id"] for figure in result["figures"]], ["before", "between", "legacy", "stale"])
            self.assertEqual([figure["figure_number"] for figure in result["figures"]], [1, 2, 3, 4])
            self.assertEqual([figure["placement"]["after_paragraph"] for figure in result["figures"]], [0, 1, None, None])

    @unittest.skipUnless(_pdf_available(), "PDF dependencies are optional in the launcher interpreter")
    def test_pagination_text_mapping_image_and_append_only(self):
        from PIL import Image
        from pypdf import PdfReader
        with tempfile.TemporaryDirectory() as temporary:
            home = Path(temporary)
            (home / "assets").mkdir()
            image = home / "assets/plate.png"
            Image.new("RGB", (1600, 400), "#446b51").save(image)
            body = "\n\n".join(f"Paragraph {i}: " + "Eight wedge blanks from each section preserve a clear counted inventory. "*12 for i in range(14))
            body += "\n\n## Last measurement\n\nFINAL SENTINEL: 128 gross blanks, 120 intended members."
            book = fixture_book(body)
            book["assets"]["plate"] = {"path": "assets/plate.png", "caption": "Wide plate, original aspect ratio.", "provenance": "Programmatic test illustration"}
            book["pages"][0]["figures"] = ["plate"]
            original = json.dumps(book, sort_keys=True)
            result = export_publication(book, home)
            pages = result["pages"]
            mapped = [p for p in pages if p["source_page_id"] == "sample-inventory"]
            self.assertGreater(len(mapped), 2)
            self.assertEqual([p["page_number"] for p in pages], list(range(1, len(pages)+1)))
            all_text = "\n".join(p["text"] for p in pages)
            self.assertIn("FINAL SENTINEL", all_text)
            self.assertIn("Programmatic test illustration", all_text)
            self.assertGreater(sum(p["word_count"] for p in mapped), 1800)
            drawn = result["figures"][0]["draw_size_points"]
            self.assertAlmostEqual(drawn[0]/drawn[1], 4)
            self.assertTrue(all(Path(p["path"]).is_file() for p in pages))
            self.assertEqual(len(PdfReader(result["pdf"]).pages), len(pages))
            short = fixture_book()
            again = export_publication(short, home)
            self.assertNotEqual(result["output_dir"], again["output_dir"])
            self.assertTrue(Path(result["pdf"]).is_file())
            self.assertEqual(original, json.dumps(book, sort_keys=True))
            self.assertEqual(result["book_source_ids"], ["sample-inventory"])
            self.assertEqual(len(result["book_sha256"]), 64)

    @unittest.skipUnless(_pdf_available(), "PDF dependencies are optional in the launcher interpreter")
    def test_journal_form_fits_one_physical_page(self):
        with tempfile.TemporaryDirectory() as temporary:
            book = fixture_book()
            book["pages"] = [next(p for p in seed_pages() if p["id"] == "codex-day-14")]
            result = export_publication(book, Path(temporary))
            journal = [p for p in result["pages"] if p["source_page_id"] == "codex-day-14"]
            self.assertEqual(len(journal), 1)
            self.assertIn("Next step: [record]", journal[0]["text"])

    def test_missing_asset_and_escape_are_not_silently_skipped(self):
        with tempfile.TemporaryDirectory() as temporary:
            book = fixture_book()
            book["pages"][0]["figures"] = ["missing"]
            with self.assertRaisesRegex(ValueError, "Missing attached"):
                export_publication(book, Path(temporary))
            book["assets"]["missing"] = {"path": "../outside.png"}
            with self.assertRaisesRegex(ValueError, "leaves"):
                export_publication(book, Path(temporary))

    def test_video_validates_settings_before_ffmpeg(self):
        for kwargs in ({"words_per_minute": math.nan}, {"minimum_seconds": math.inf}, {"fps": 23.5}, {"size": (1919, 1080)}, {"size": (0, 1080)}, {"words_per_minute": True}):
            with self.assertRaises(ValueError):
                export_readthrough({"pages": []}, **kwargs)
        with self.assertRaises(ValueError):
            export_readthrough({"pages": []})

    def test_video_missing_page(self):
        with self.assertRaises(FileNotFoundError):
            export_readthrough({"pages": [{"path": "missing-physical-page.png", "word_count": 20}]})


if __name__ == "__main__":
    unittest.main()
