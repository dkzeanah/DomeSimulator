"""Contracts for the manually copied packet, GUI, and standalone renderer."""
from dataclasses import replace
import types
import unittest
from unittest.mock import patch

from . import starter_element
from .render_lesson import find_lesson, parse_size, validate_timeline
from .workbench import build_manual_prompt, commands, starter_source, validate_key


class PacketTests(unittest.TestCase):
    def test_generated_starter_is_valid_and_uses_exact_destination(self):
        source = starter_source("roof_reveal")
        self.assertIn("SAVE THIS AS: two_v_demo/lesson_roof_reveal.py", source)
        self.assertIn("--module two_v_demo.lesson_roof_reveal --selftest", source)
        module = types.ModuleType("generated_starter")
        exec(compile(source, "lesson_roof_reveal.py", "exec"), module.__dict__)
        lesson = find_lesson(module)
        lesson.validate()
        lesson.selftest()
        self.assertEqual(lesson.key, "roof_reveal")
        self.assertEqual(len(lesson.chapters), 1)
        self.assertEqual(lesson.chapters[0].duration, 8)

    def test_prompt_sizes_and_required_save_usage_contract(self):
        compact = build_manual_prompt("roof_reveal", "Make a roof appear.")
        full = build_manual_prompt("roof_reveal", "Make a roof appear.", full=True)
        self.assertGreater(len(full), len(compact))
        for packet in (compact, full):
            self.assertIn("SAVE THIS AS: two_v_demo/lesson_roof_reveal.py", packet)
            self.assertIn("HOW TO USE and WHAT TO CHANGE", packet)
            self.assertIn("--silent --size 960x540 --fps 24", packet)
            self.assertIn("Do not claim to have rendered or tested it here", packet)
            self.assertIn("Make a roof appear.", packet)
        self.assertIn("creator.preset", full)
        self.assertIn("Ready-made objects", full)

    def test_keys_and_model_role(self):
        for key in ("../evil", "bad-key", "1clip", "a; exit", "MyClip", "a" * 49):
            with self.assertRaises(ValueError):
                validate_key(key)
        with self.assertRaises(ValueError):
            build_manual_prompt(model="embeddinggemma:latest")
        with self.assertRaises(ValueError):
            build_manual_prompt(brief=" ")
        self.assertIn("two_v_demo.lesson_my_element", commands("my_element"))


class RunnerTests(unittest.TestCase):
    def test_ambiguous_lesson_is_rejected_but_alias_is_allowed(self):
        module = types.ModuleType("test")
        module.LESSON = starter_element.LESSON
        module.ALIAS = module.LESSON
        self.assertIs(find_lesson(module), module.LESSON)
        module.SECOND = replace(module.LESSON, key="other")
        with self.assertRaises(SystemExit):
            find_lesson(module)

    def test_invalid_geometry_settings_and_wrapped_times_fail_before_gl(self):
        lesson = starter_element.LESSON
        self.assertEqual(validate_timeline(lesson, ["0", "7.9"]), [0, 7.9])
        for times in (["8"], ["-1"], ["nan"], ["abc"]):
            with self.assertRaises(SystemExit):
                validate_timeline(lesson, times)
        chapter = lesson.chapters[0]
        for changed in (replace(chapter, stage="missing"), replace(chapter, duration=float("inf")),
                        replace(chapter, camera=(90, 18, -1))):
            with self.assertRaises(SystemExit):
                validate_timeline(replace(lesson, chapters=(changed,)), [])
        self.assertEqual(parse_size("960x540"), (960, 540))
        for value in ("-10x540", "961x540", "wrong"):
            with self.assertRaises(SystemExit):
                parse_size(value)


class GuiTests(unittest.TestCase):
    def setUp(self):
        import tkinter as tk
        from .gui import ManualAuthoringPanel
        self.root = tk.Tk()
        self.root.withdraw()
        self.panel = ManualAuthoringPanel(self.root)
        self.panel.pack(fill="both", expand=True)
        self.root.update()

    def tearDown(self):
        self.root.destroy()

    def test_key_updates_code_and_commands_and_copy_rebuilds(self):
        import time
        panel = self.panel
        panel.key.set("roof_reveal")
        self.assertIn("lesson_roof_reveal.py", panel.location.get())
        self.assertIn("two_v_demo.lesson_roof_reveal", panel.views["Commands"].get("1.0", "end"))
        with patch.object(panel, "_copy") as copied:
            panel.build("copy")
            deadline = time.monotonic() + 20
            while panel.busy and time.monotonic() < deadline:
                self.root.update()
                time.sleep(0.01)
            self.assertFalse(panel.busy)
            copied.assert_called_once()
            self.assertIn("lesson_roof_reveal.py", copied.call_args.args[0])
        self.assertIn("Copied prompt", panel.status.get())

    def test_embedding_and_bad_key_do_not_build(self):
        self.panel.model.set("embeddinggemma")
        self.panel.build()
        self.assertFalse(self.panel.busy)
        self.assertIn("embeddinggemma", self.panel.status.get())
        self.panel.key.set("../outside")
        self.assertIn("lowercase", self.panel.location.get())


if __name__ == "__main__":
    unittest.main()
