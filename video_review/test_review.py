"""Offline regression checks for review persistence, lineage, media and overlays."""
from dataclasses import dataclass, replace
import http.client
import json
from pathlib import Path
import tempfile
import threading
import unittest

from video_review.model import ReviewStore, read_json, write_new
from video_review.render_bridge import apply_packet, load_packet, write_render_receipt
from video_review.server import make_server


@dataclass(frozen=True)
class Chapter:
    slug: str = "intro"
    title: str = "Opening"
    narration: tuple = ("The original line.",)


@dataclass(frozen=True)
class Lesson:
    key: str = "sample"
    title: str = "Sample film"
    chapters: tuple = (Chapter(),)

    def validate(self):
        if not self.chapters[0].narration:
            raise ValueError("empty narration")


class ReviewTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.root = Path(self.temp.name)
        self.video = self.root / "first.mp4"
        self.video.write_bytes(b"0123456789abcdef")
        write_render_receipt(self.video, Lesson(), [10], {"fps": 24})
        self.store = ReviewStore(self.root)
        self.state = self.store.create({"video": "first.mp4", "title": "Film", "prompt": "Keep the story grounded."})
        self.ident = self.state["project"]["id"]

    def tearDown(self):
        self.temp.cleanup()

    def note(self, **changes):
        data = dict(revision=self.state["revision"], start=2.5, end=4, kind="visual", text="Show the joint closer.", chapter="intro")
        data.update(changes)
        self.state = self.store.save_note(self.ident, self.state["round"]["number"], data)
        return self.state["notes"][-1]

    def packet(self):
        self.state = self.store.build_packet(self.ident, self.state["round"]["number"], self.state["revision"])
        return self.store.packet_path(self.ident, self.state["round"]["number"], self.state["packets"][-1]["packet"])

    def narration(self):
        return self.note(kind="narration", original="The original line.", replacement="The revised line.", text="Simplify the opening.")

    def advance(self, packet, index=2, with_metadata=False):
        path = self.root / f"render-{index}.mp4"
        path.write_bytes(b"new video " + str(index).encode())
        if with_metadata:
            write_render_receipt(path, replace(Lesson(), chapters=(replace(Chapter(), narration=("The revised line.",)),)), [12])
        self.state = self.store.advance(self.ident, self.state["round"]["number"], {
            "video": str(path), "packet": read_json(packet)["packet"], "revision": self.state["revision"]})

    def test_receipt_import_and_restart(self):
        self.note()
        reopened = ReviewStore(self.root).state(self.ident)
        self.assertEqual(reopened["notes"][0]["start"], 2.5)
        self.assertEqual(reopened["round"]["chapters"][0]["end"], 10)
        self.assertEqual(reopened["project"]["lesson"], "sample")

    def test_exact_script_overlay_and_original_preserved(self):
        self.narration()
        packet = self.packet()
        before = packet.read_bytes()
        lesson = Lesson()
        updated = apply_packet(lesson, packet)
        self.assertEqual(updated.chapters[0].narration, ("The revised line.",))
        self.assertEqual(lesson.chapters[0].narration, ("The original line.",))
        self.assertIn("The original line.", (packet.parent / "script-before.md").read_text())
        self.assertIn("The revised line.", (packet.parent / "script-updated.md").read_text())
        self.assertIn("Keep the story grounded.", (packet.parent / "next-build-prompt.md").read_text())
        self.note(text="New note after snapshot.")
        self.packet()
        self.assertEqual(packet.read_bytes(), before)

    def test_edits_append_events_and_do_not_change_packet(self):
        note = self.note()
        packet = self.packet()
        self.note(id=note["id"], text="Even closer; show the seam.")
        first = read_json(self.store.round_dir(self.ident, 1) / "event-000001.json")
        self.assertEqual(first["note"]["text"], "Show the joint closer.")
        self.assertEqual(self.state["notes"][0]["text"], "Even closer; show the seam.")
        self.assertEqual(read_json(packet)["notes"][0]["text"], "Show the joint closer.")

    def test_conflicting_or_ambiguous_replacement_is_blocked(self):
        self.narration()
        self.note(kind="narration", original="The original line.", replacement="Conflicting edit.")
        with self.assertRaisesRegex(ValueError, "conflict"):
            self.packet()

    def test_changed_source_lesson_and_wrong_lesson_are_blocked(self):
        self.narration()
        packet = self.packet()
        with self.assertRaisesRegex(ValueError, "changed since review"):
            apply_packet(replace(Lesson(), chapters=(replace(Chapter(), narration=("A later authored sentence.",)),)), packet)
        with self.assertRaisesRegex(ValueError, "different lesson"):
            apply_packet(replace(Lesson(), key="another"), packet)

    def test_tampered_script_is_blocked(self):
        packet = self.packet()
        (packet.parent / "script-updated.md").write_text("tampered")
        with self.assertRaisesRegex(ValueError, "changed after"):
            load_packet(packet)

    def test_stale_client_cannot_overwrite_notes(self):
        self.note()
        with self.assertRaisesRegex(ValueError, "another window"):
            self.note(revision=0)

    def test_changed_media_is_not_silently_substituted(self):
        self.video.write_bytes(b"replaced")
        with self.assertRaisesRegex(ValueError, "changed on disk"):
            self.store.media(self.ident, 1)

    def test_nonfinite_and_reversed_times_rejected(self):
        for start, end in ((float("nan"), None), (-1, None), (4, 2), (1, float("inf"))):
            with self.assertRaises(ValueError):
                self.note(start=start, end=end)

    def test_resolved_and_dismissed_not_carried(self):
        first = self.note()
        self.state = self.store.save_note(self.ident, 1, {"revision": self.state["revision"], "id": first["id"], "status": "resolved"})
        self.advance(self.packet())
        self.assertEqual(self.state["notes"], [])
        self.assertEqual(self.store.state(self.ident, 1)["notes"][0]["status"], "resolved")

    def test_eight_rounds_preserve_lineage_and_cumulative_script(self):
        self.narration()
        self.note()
        first_packet = self.packet()
        first_bytes = first_packet.read_bytes()
        for index in range(2, 9):
            packet = first_packet if index == 2 else self.packet()
            self.advance(packet, index)
            self.assertEqual(self.state["round"]["number"], index)
            self.assertIn("The revised line.", self.state["round"]["script"])
            self.assertIsNone(self.state["notes"][0]["start"])
            self.assertEqual(self.state["notes"][0]["source_start"], 2.5)
            self.assertEqual(self.state["notes"][0]["status"], "verify")
            self.assertNotIn("start", self.state["round"]["chapters"][0])
        self.assertEqual(len(self.state["rounds"]), 8)
        self.assertEqual(first_packet.read_bytes(), first_bytes)
        with self.assertRaisesRegex(ValueError, "Earlier rounds"):
            self.store.save_note(self.ident, 1, {"revision": 2, "text": "new"})
        final_packet = self.packet()
        self.assertEqual(apply_packet(Lesson(), final_packet).chapters[0].narration, ("The revised line.",))

    def test_new_measured_timeline_replaces_old_timings(self):
        self.narration()
        self.advance(self.packet(), with_metadata=True)
        self.assertEqual(self.state["round"]["chapters"][0]["end"], 12)
        self.assertIsNone(self.state["notes"][0]["start"])

    def test_new_chapters_and_updated_render_settings_survive_iterations(self):
        packet = self.packet()
        video = self.root / "new-chapter.mp4"
        video.write_bytes(b"new chapter render")
        later = replace(Lesson(), chapters=(Chapter(), Chapter(slug="detail", title="Detail", narration=("Added detail.",))))
        write_render_receipt(video, later, [12, 8], {"fps": 60})
        self.state = self.store.advance(self.ident, 1, {"video":str(video), "revision":0, "packet":1})
        self.note(kind="narration", chapter="detail", original="Added detail.", replacement="Improved detail.")
        latest = self.packet()
        self.assertEqual(read_json(latest)["render_config"]["fps"], 60)
        self.assertEqual(apply_packet(later, latest).chapters[1].narration, ("Improved detail.",))
        self.advance(latest, 3)
        self.assertEqual(apply_packet(later, self.packet()).chapters[1].narration, ("Improved detail.",))

    def test_round_snapshot_accepts_reviewed_source_updates(self):
        self.packet()
        video = self.root / "authored.mp4"
        video.write_bytes(b"authored render")
        authored = replace(Lesson(), chapters=(replace(Chapter(), narration=("New authored line.",)),))
        write_render_receipt(video, authored, [12])
        self.state = self.store.advance(self.ident, 1, {"video":str(video), "revision":0, "packet":1})
        self.note(kind="narration", original="New authored line.", replacement="Reviewed authored line.")
        latest = self.packet()
        self.assertEqual(apply_packet(authored, latest).chapters[0].narration, ("Reviewed authored line.",))
        self.advance(latest, 3)
        self.assertEqual(apply_packet(authored, self.packet()).chapters[0].narration, ("Reviewed authored line.",))

    def test_wrong_lesson_cannot_join_review(self):
        self.packet()
        video = self.root / "different.mp4"
        video.write_bytes(b"different lesson")
        write_render_receipt(video, replace(Lesson(),key="different"), [10])
        with self.assertRaisesRegex(ValueError, "different lesson"):
            self.store.advance(self.ident, 1, {"video":str(video), "revision":0, "packet":1})

    def test_stale_packet_and_reused_video_cannot_advance(self):
        packet = self.packet()
        with self.assertRaisesRegex(ValueError, "new video"):
            self.store.advance(self.ident, 1, {"video":"first.mp4", "packet":1, "revision":0})
        self.note()
        with self.assertRaisesRegex(ValueError, "latest notes"):
            self.advance(packet)

    def test_plain_script_video_still_produces_handoff(self):
        raw = self.root / "raw.mp4"
        raw.write_bytes(b"raw")
        self.state = self.store.create({"video":"raw.mp4", "script":"An old line."})
        self.ident = self.state["project"]["id"]
        self.note(kind="narration", chapter="", original="old", replacement="improved")
        packet = self.packet()
        self.assertEqual((packet.parent / "script-updated.md").read_text(), "An improved line.")
        self.assertIn("No renderer lesson", (packet.parent / "next-build-prompt.md").read_text())

    def test_paths_cannot_escape_root(self):
        with self.assertRaises(ValueError):
            self.store.local_file("../outside.mp4")
        with self.assertRaises(ValueError):
            self.store.project_dir("../")

    def test_atomic_history_files_refuse_overwrite(self):
        target = self.root / "record.json"
        write_new(target, {"version":1})
        with self.assertRaises(ValueError):
            write_new(target, {"version":2})
        self.assertEqual(read_json(target), {"version":1})


class ServerTests(unittest.TestCase):
    setUp = ReviewTests.setUp
    tearDown = ReviewTests.tearDown
    # Exercise the actual browser-facing HTTP path, including partial video.
    def test_http_api_range_auth_and_seek(self):
        server = make_server(self.root)
        worker = threading.Thread(target=server.serve_forever, daemon=True)
        worker.start()
        conn = http.client.HTTPConnection("127.0.0.1", server.server_port)
        try:
            conn.request("GET", "/api/bootstrap")
            res = conn.getresponse()
            boot = json.loads(res.read())
            self.assertEqual(res.status, 200)
            media = f"/media?id={self.ident}&round=1"
            for header, expected in (("bytes=3-6", b"3456"), ("bytes=10-", b"abcdef"), ("bytes=-3", b"def")):
                conn.request("GET", media, headers={"Range":header})
                res = conn.getresponse()
                self.assertEqual(res.status, 206)
                self.assertEqual(res.read(), expected)
            conn.request("GET", media, headers={"Range":"bytes=999-"})
            res = conn.getresponse()
            self.assertEqual(res.status, 416)
            res.read()
            conn.request("HEAD", media)
            res = conn.getresponse()
            self.assertEqual(res.getheader("Content-Length"), "16")
            self.assertEqual(res.read(), b"")
            payload = json.dumps({"id":self.ident,"round":1,"revision":0,"text":"API note", "start":1})
            conn.request("POST", "/api/note", body=payload, headers={"Content-Type":"application/json"})
            res = conn.getresponse()
            self.assertEqual(res.status, 403)
            res.read()
            headers={"Content-Type":"application/json", "X-Review-Token":boot["token"]}
            conn.request("POST", "/api/note", body=payload, headers=headers)
            res = conn.getresponse()
            self.assertEqual(res.status, 200)
            saved=json.loads(res.read())
            self.assertEqual(saved["notes"][0]["text"], "API note")
            headers["Origin"]="https://unrelated.example"
            conn.request("POST", "/api/note", body=payload, headers=headers)
            res = conn.getresponse()
            self.assertEqual(res.status, 403)
            res.read()
            conn.request("GET", "/api/bootstrap", headers={"Host":"unrelated.example"})
            res = conn.getresponse()
            self.assertEqual(res.status, 403)
            res.read()
        finally:
            conn.close()
            server.shutdown()
            server.server_close()
            worker.join()


if __name__ == "__main__":
    unittest.main()
