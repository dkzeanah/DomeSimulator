"""Offline regression checks. Run with unittest; FFmpeg supplies a tiny fixture."""
import asyncio
import json
from pathlib import Path
import shutil
import tempfile
import threading
import unittest
from unittest.mock import patch
import wave

from . import presentation_voice as voice


class VoiceTests(unittest.TestCase):
    def test_transcript_cleanup_preserves_spoken_numbers(self):
        self.assertEqual(voice.clean_transcript(
            "WEBVTT\n\n1\n00:00:01.000 --> 00:00:03.000\n40 triangles.\n"
            "1:24 Two lengths.\n2026\n[01:25] Another sentence."),
            "40 triangles.\nTwo lengths.\n2026\nAnother sentence.")

    def test_long_script_retains_all_words_and_bounds_sections(self):
        text = ("One triangle. Two lengths of wood, and a complete frame!\n" * 100)
        chunks = voice.split_text(text)
        self.assertGreater(len(chunks), 2)
        self.assertEqual(" ".join(chunks), " ".join(text.split()))
        self.assertTrue(all(len(chunk) <= 450 for chunk in chunks))

    def test_validation(self):
        for settings in (voice.VoiceSettings(rate="3"), voice.VoiceSettings(voice=""),
                         voice.VoiceSettings(rate="-100%")):
            with self.assertRaises(ValueError):
                settings.validate()

    def test_cancellation_interrupts_network_wait(self):
        cancelled = threading.Event()
        closed = []

        async def slow(*args):
            try:
                await asyncio.sleep(20)
            finally:
                closed.append(True)

        async def check():
            asyncio.get_running_loop().call_later(0.15, cancelled.set)
            with self.assertRaises(voice.RenderCancelled):
                await voice._speak("Hello", Path("unused.mp3"), voice.VoiceSettings(), cancelled, None)
        with patch.object(voice, "_synthesize_one", slow):
            asyncio.run(check())
        self.assertEqual(closed, [True])

    def test_export_and_receipt_cannot_overwrite_or_escape(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            source, destination = root / "source.wav", root / "existing.wav"
            source.write_bytes(b"new")
            destination.write_bytes(b"original")
            with self.assertRaises(FileExistsError):
                voice.export_copy(source, destination)
            self.assertEqual(destination.read_bytes(), b"original")
            folder = root / "take"
            folder.mkdir()
            with self.assertRaises(ValueError):
                voice.take_audio(folder, {"wav": "../existing.wav"})


class RenderTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.temporary = tempfile.TemporaryDirectory()
        cls.root = Path(cls.temporary.name)
        cls.fixture = cls.root / "fixture.mp3"
        voice.convert_audio([voice.ffmpeg_path(), "-v", "error", "-f", "lavfi", "-i",
                             "sine=frequency=440:duration=0.2", str(cls.fixture)], threading.Event())

    @classmethod
    def tearDownClass(cls):
        cls.temporary.cleanup()

    async def fake_speak(self, text, path, settings, cancel, progress):
        shutil.copyfile(self.fixture, path)

    def render(self, root, cancel, emit):
        with patch.object(voice, "_speak", self.fake_speak), \
             patch("two_v_demo.audio._edge_tts_module", return_value=object()):
            return voice.render_clip(root, "Test clip", "A test sentence. " * 75,
                                     voice.VoiceSettings(), cancel, emit)

    def test_render_writes_complete_audio_and_reopenable_take(self):
        library = self.root / "library"
        events = []
        folder = self.render(library, threading.Event(), lambda k, v: events.append((k, v)))
        receipt = json.loads((folder / "take.json").read_text())
        self.assertEqual(receipt["status"], "complete")
        self.assertEqual(receipt["settings"]["voice"], voice.DEFAULT_VOICE)
        sections = [value for kind, value in events if kind == "section"]
        self.assertGreater(len(sections), 1)
        total = 0
        for section in sections:
            with wave.open(str(section)) as wav:
                total += wav.getnframes()
        with wave.open(str(voice.take_audio(folder, receipt))) as wav:
            self.assertEqual(wav.getnframes(), total)
        self.assertGreater(voice.take_audio(folder, receipt, "mp3").stat().st_size, 0)
        again = self.render(library, threading.Event(), lambda *_: None)
        self.assertNotEqual(folder, again)
        self.assertEqual(len(voice.list_takes(library)), 2)
        self.assertEqual((folder / "script.txt").read_text(), "A test sentence. " * 75)

    def test_cancel_keeps_script_and_does_not_publish_partial_track(self):
        library = self.root / "cancelled"
        cancelled = threading.Event()
        def emit(kind, _value):
            if kind == "section":
                cancelled.set()
        with self.assertRaises(voice.RenderCancelled):
            self.render(library, cancelled, emit)
        folder, receipt = voice.list_takes(library)[0]
        self.assertEqual(receipt["status"], "cancelled")
        self.assertTrue((folder / "script.txt").is_file())
        self.assertFalse((folder / "audio.wav").exists())

    def test_provider_failure_is_visible_and_not_a_complete_take(self):
        library = self.root / "failed"
        async def fail(*_args):
            raise RuntimeError("Test provider offline")
        with patch.object(voice, "_speak", fail), \
             patch("two_v_demo.audio._edge_tts_module", return_value=object()):
            with self.assertRaisesRegex(RuntimeError, "offline"):
                voice.render_clip(library, "Failure", "Hello", voice.VoiceSettings(), threading.Event())
        folder, receipt = voice.list_takes(library)[0]
        self.assertEqual(receipt["status"], "failed")
        self.assertIn("offline", receipt["error"])
        self.assertFalse((folder / "audio.mp3").exists())


class PlayerTests(unittest.TestCase):
    def test_queue_pause_and_finish(self):
        import numpy as np
        import sounddevice as sd
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "part.wav"
            with wave.open(str(path), "wb") as wav:
                wav.setnchannels(1)
                wav.setsampwidth(2)
                wav.setframerate(voice.SAMPLE_RATE)
                wav.writeframes(np.array([100, 200, 300, 400], dtype=np.int16).tobytes())
            player = voice.ClipPlayer()
            player.finished = False
            player.append(path)
            player.append(path)
            out = np.zeros((4, 1), dtype=np.int16)
            player.paused = True
            player._callback(out, 4, None, None)
            self.assertEqual(player.position, 0)
            player.paused = False
            player._callback(out, 4, None, None)
            self.assertEqual(out[:, 0].tolist(), [100, 200, 300, 400])
            player._callback(out, 4, None, None)
            self.assertEqual(player.position, 8)
            player._callback(out, 4, None, None)
            self.assertFalse(out.any())
            player.finished = True
            with self.assertRaises(sd.CallbackStop):
                player._callback(out, 4, None, None)
            player.stop()


class GuiTests(unittest.TestCase):
    def setUp(self):
        import tkinter as tk
        from .presentation_voice_gui import PresentationVoicePanel
        self.tmp = tempfile.TemporaryDirectory()
        self.root = tk.Tk()
        self.root.withdraw()
        self.root.geometry("980x500")
        self.panel = PresentationVoicePanel(self.root, library=Path(self.tmp.name), persist=False)
        self.panel.pack(fill="both", expand=True)
        self.root.update()

    def tearDown(self):
        self.panel.close()
        self.root.destroy()
        self.tmp.cleanup()

    def test_worker_finishes_and_take_reloads(self):
        import time
        panel = self.panel
        panel.text.insert("1.0", "This is a saved script.")
        panel.live.set(False)
        def fake_render(library, title, text, settings, cancel, emit):
            folder, receipt = voice.new_take(library, title, text, settings)
            receipt["status"] = "complete"
            voice.write_json(folder / "take.json", receipt)
            emit("progress", (0.5, "Rendering"))
            return folder
        with patch("local_voice_studio.presentation_voice_gui.render_clip", fake_render):
            panel.generate()
            with self.assertRaises(ValueError):
                panel.generate()
            deadline = time.monotonic() + 5
            while panel.busy and time.monotonic() < deadline:
                self.root.update()
                time.sleep(0.01)
        self.assertFalse(panel.busy)
        self.assertEqual(len(panel.tree.get_children()), 1)
        self.assertTrue(panel.tree.selection())
        panel.text.delete("1.0", "end")
        panel.load_take()
        self.assertEqual(panel.text.get("1.0", "end-1c"), "This is a saved script.")
        self.assertFalse(panel.generate_button.instate(["disabled"]))

    def test_empty_and_invalid_selection_do_not_start_jobs(self):
        with self.assertRaises(ValueError):
            self.panel.generate()
        with self.assertRaises(ValueError):
            self.panel.generate(selection=True)
        self.assertFalse(self.panel.busy)

    def test_microphone_take_is_saved_and_listed(self):
        panel = self.panel
        def fake_stop(path):
            with wave.open(str(path), "wb") as wav:
                wav.setnchannels(1)
                wav.setsampwidth(2)
                wav.setframerate(24000)
                wav.writeframes(b"\x00\x00" * 2400)
            return path
        with patch.object(panel.recorder, "start"), patch.object(panel.recorder, "stop", fake_stop):
            panel.start_recording()
            self.assertTrue(panel.generate_button.instate(["disabled"]))
            panel.stop_recording()
        folder, receipt = panel._selected()
        self.assertEqual(receipt["kind"], "Microphone")
        self.assertEqual(receipt["status"], "complete")
        self.assertTrue(voice.take_audio(folder, receipt).exists())


if __name__ == "__main__":
    unittest.main()
