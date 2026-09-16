"""File-backed review history and deterministic next-build handoffs (stdlib only)."""
from __future__ import annotations

from contextlib import contextmanager
from copy import deepcopy
from datetime import datetime, timezone
import hashlib
import json
import math
import os
from pathlib import Path
import re
import threading
import uuid

VIDEO_EXTENSIONS = {".mp4", ".webm", ".mov", ".m4v"}
KINDS = {"visual", "narration", "pacing", "audio", "cut", "keep", "other"}
STATUSES = {"open", "verify", "resolved", "dismissed"}
SKIP_DIRS = {".git", "node_modules", ".venv-voice", ".venv-f5", "F5-TTS", "__pycache__", ".codex", ".agents"}


def now():
    return datetime.now(timezone.utc).isoformat(timespec="microseconds")


def read_json(path):
    return json.loads(Path(path).read_text(encoding="utf-8-sig"))


def write_new(path, value):
    """Commit a complete, immutable JSON file; exclusive final name."""
    path = Path(path)
    temp = path.with_name(f".{path.name}-{uuid.uuid4().hex}.tmp")
    try:
        with temp.open("x", encoding="utf-8") as stream:
            json.dump(value, stream, indent=2, ensure_ascii=False, allow_nan=False)
            stream.flush()
            os.fsync(stream.fileno())
        # All store writes hold the process + OS lock. Never replace history.
        if path.exists():
            raise ValueError(f"Already exists: {path.name}")
        temp.rename(path)
    finally:
        temp.unlink(missing_ok=True)


def text_hash(value):
    return hashlib.sha256(value.encode("utf-8")).hexdigest()


def stamp(seconds):
    if seconds is None:
        return "previous round"
    ms = round(seconds * 1000)
    hours, ms = divmod(ms, 3600000)
    minutes, ms = divmod(ms, 60000)
    sec, ms = divmod(ms, 1000)
    return f"{hours:02}:{minutes:02}:{sec:02}.{ms:03}"


def script_for(chapters):
    return "\n\n".join(f"## {c['slug']} — {c['title']}\n\n" + " ".join(c["narration"]) for c in chapters) + "\n"


def normalized_chapters(values):
    result = []
    for index, value in enumerate(values):
        narration = value.get("narration", [])
        if isinstance(narration, str):
            narration = [narration]
        if not isinstance(narration, list) or any(not isinstance(line, str) for line in narration):
            raise ValueError("Chapter narration must be text or a list of text lines")
        slug = str(value.get("slug") or f"chapter-{index + 1}")
        if any(c["slug"] == slug for c in result):
            raise ValueError(f"Duplicate chapter slug: {slug}")
        item = {"slug": slug, "title": str(value.get("title", slug)), "narration": narration}
        if value.get("start") is not None and value.get("end") is not None:
            start, end = float(value["start"]), float(value["end"])
            if not all(math.isfinite(n) for n in (start, end)) or start < 0 or end <= start:
                raise ValueError("Invalid chapter timing")
            item.update(start=start, end=end)
        result.append(item)
    return result


class ReviewStore:
    def __init__(self, root, library=None):
        self.root = Path(root).resolve()
        self.library = Path(library or self.root / "video_reviews").resolve()
        self.library.mkdir(parents=True, exist_ok=True)
        self.mutex = threading.RLock()

    @contextmanager
    def locked(self):
        """Serialize independent server processes too; OS releases locks on crash."""
        with self.mutex, (self.library / ".lock").open("a+b") as stream:
            stream.seek(0)
            if os.name == "nt":
                import msvcrt
                if stream.read(1) == b"":
                    stream.write(b"0")
                    stream.flush()
                stream.seek(0)
                msvcrt.locking(stream.fileno(), msvcrt.LK_LOCK, 1)
            else:
                import fcntl
                fcntl.flock(stream, fcntl.LOCK_EX)
            try:
                yield
            finally:
                stream.seek(0)
                if os.name == "nt":
                    msvcrt.locking(stream.fileno(), msvcrt.LK_UNLCK, 1)
                else:
                    fcntl.flock(stream, fcntl.LOCK_UN)

    def local_file(self, value, extensions=None):
        value = str(value).strip().strip('"').replace("\\", "/")
        if os.name != "nt" and re.match(r"^[A-Za-z]:/", value):
            value = f"/mnt/{value[0].lower()}/{value[3:]}"
        candidate = Path(value)
        path = (candidate if candidate.is_absolute() else self.root / candidate).resolve()
        if not path.is_relative_to(self.root) or not path.is_file():
            raise ValueError("Choose an existing file inside the DomeSim project folder")
        if extensions and path.suffix.lower() not in extensions:
            raise ValueError("Unsupported file type")
        return path

    def rel(self, path):
        return Path(path).relative_to(self.root).as_posix()

    def project_dir(self, ident):
        if not re.fullmatch(r"[a-f0-9]{32}", str(ident)):
            raise ValueError("Invalid review ID")
        directory = self.library / ident
        if not (directory / "project.json").is_file():
            raise ValueError("Review not found")
        return directory

    def round_dir(self, ident, number):
        if not isinstance(number, int) or isinstance(number, bool) or number < 1:
            raise ValueError("Invalid round")
        folder = self.project_dir(ident) / f"round-{number:04d}"
        if not (folder / "round.json").is_file():
            raise ValueError("Round not found")
        return folder

    def videos(self):
        found = []
        for base, dirs, files in os.walk(self.root):
            dirs[:] = [d for d in dirs if d not in SKIP_DIRS and not d.startswith(".")]
            for name in files:
                path = Path(base) / name
                if path.suffix.lower() in VIDEO_EXTENSIONS and not name.startswith("."):
                    try:
                        stat = path.stat()
                        found.append({"path": self.rel(path), "bytes": stat.st_size, "modified": stat.st_mtime})
                    except OSError:
                        continue
        return sorted(found, key=lambda x: x["modified"], reverse=True)

    def metadata(self, path):
        """Prefer render receipts. Old exports can use a storyboard + measured plan."""
        result = {"chapters": [], "script": "", "lesson": "", "render_config": {}, "sources": [], "timings": []}
        receipt = path.with_name(path.stem + "-review.json")
        storyboard = path.parent / "storyboard.json"
        if receipt.is_file():
            data = read_json(receipt)
            result.update(chapters=normalized_chapters(data.get("chapters", [])),
                          lesson=str(data.get("lesson", "")), render_config=data.get("render_config", {}))
            result["sources"].append(self.rel(receipt))
        elif storyboard.is_file():
            result["chapters"] = normalized_chapters(read_json(storyboard))
            result["sources"].append(self.rel(storyboard))
        for script_path in (path.with_name(path.stem + "-narration.md"), path.parent / "narration.md"):
            if script_path.is_file():
                result["script"] = script_path.read_text(encoding="utf-8-sig")
                result["sources"].append(self.rel(script_path))
                break
        for plan_path in (path.with_name(path.stem + "-narration-plan.json"), path.parent / "plan.json"):
            if not plan_path.is_file():
                continue
            plan = read_json(plan_path)
            starts, durations = plan.get("chapter_starts", []), plan.get("chapter_durations", [])
            if starts and len(starts) == len(durations):
                result["timings"] = [(float(s), float(s) + float(d)) for s, d in zip(starts, durations)]
            if len(starts) == len(durations) == len(result["chapters"]):
                for c, start, duration in zip(result["chapters"], starts, durations):
                    c.update(start=float(start), end=float(start) + float(duration))
                result["chapters"] = normalized_chapters(result["chapters"])
                result["sources"].append(self.rel(plan_path))
                break
        if not result["timings"] and result["script"]:
            spans = re.findall(r"^Time: (\d+:\d+:\d+[.,]\d+) - (\d+:\d+:\d+[.,]\d+)", result["script"], re.MULTILINE)
            def seconds(value):
                h, m, s = value.replace(",", ".").split(":")
                return int(h) * 3600 + int(m) * 60 + float(s)
            result["timings"] = [(seconds(s), seconds(e)) for s, e in spans]
        if len(result["timings"]) == len(result["chapters"]):
            for chapter, (start, end) in zip(result["chapters"], result["timings"]):
                chapter.update(start=start, end=end)
            result["chapters"] = normalized_chapters(result["chapters"])
        return result

    def listing(self):
        result = []
        for file in self.library.glob("*/project.json"):
            data = read_json(file)
            rounds = sorted(file.parent.glob("round-*/round.json"))
            result.append({"id": data["id"], "title": data["title"], "created": data["created"], "rounds": len(rounds)})
        return sorted(result, key=lambda x: x["created"], reverse=True)

    def state(self, ident, number=None):
        directory = self.project_dir(ident)
        project = read_json(directory / "project.json")
        rounds = [read_json(p) for p in sorted(directory.glob("round-*/round.json"))]
        current = number or rounds[-1]["number"]
        folder = self.round_dir(ident, current)
        review = read_json(folder / "round.json")
        notes = {n["id"]: n for n in review.get("carried_notes", [])}
        events = sorted(folder.glob("event-*.json"))
        for event in events:
            note = read_json(event)["note"]
            notes[note["id"]] = note
        packets = [read_json(p / "revision.json") for p in sorted(folder.glob("packet-*")) if (p / "revision.json").is_file()]
        return {"project": project, "rounds": rounds, "round": review,
                "notes": list(notes.values()), "revision": len(events), "packets": packets,
                "read_only": current != rounds[-1]["number"]}

    def create(self, data):
        video = self.local_file(data.get("video", ""), VIDEO_EXTENSIONS)
        metadata = self.metadata(video)
        script = str(data.get("script") or metadata["script"])
        lesson = str(data.get("lesson") or metadata["lesson"]).strip()
        chapters = metadata["chapters"]
        if lesson and not chapters:
            try:
                from two_v_demo.lesson_registry import get_lesson
                source = get_lesson(lesson)
            except ImportError as exc:
                raise ValueError("Loading a lesson needs the renderer's Python environment. Start Video Review with py -3.12, or use a video with a -review.json receipt.") from exc
            chapters = [{"slug": c.slug, "title": c.title, "narration": list(c.narration)} for c in source.chapters]
            # Authored durations are not the measured duration of the old video.
            if len(metadata["timings"]) == len(chapters):
                for chapter, (start, end) in zip(chapters, metadata["timings"]):
                    chapter.update(start=start, end=end)
                chapters = normalized_chapters(chapters)
        if len(script) > 1000000:
            raise ValueError("Script is too large")
        ident = uuid.uuid4().hex
        project = {"schema": 1, "id": ident, "created": now(), "title": str(data.get("title") or video.stem)[:200],
                   "lesson": lesson, "original_script": script, "original_chapters": chapters,
                   "original_prompt": str(data.get("prompt", "")), "sources": metadata["sources"],
                   "render_config": metadata["render_config"]}
        with self.locked():
            directory = self.library / ident
            directory.mkdir()
            round_dir = directory / "round-0001"
            round_dir.mkdir()
            review = self._round(video, 1, chapters, script_for(chapters) if chapters else script,
                                 render_config=metadata["render_config"])
            write_new(round_dir / "round.json", review)
            write_new(directory / "project.json", project)
        return self.state(ident)

    def _round(self, video, number, chapters, script, **extra):
        stat = video.stat()
        return {"number": number, "created": now(), "video": self.rel(video),
                "video_bytes": stat.st_size, "video_mtime_ns": stat.st_mtime_ns,
                "chapters": chapters, "script": script, **extra}

    def _editable(self, ident, number, revision):
        state = self.state(ident, number)
        if state["read_only"]:
            raise ValueError("Earlier rounds are preserved. Continue in the latest round.")
        if revision != state["revision"]:
            raise ValueError("This review changed in another window. Reload before saving.")
        return state

    def save_note(self, ident, number, data):
        with self.locked():
            state = self._editable(ident, number, data.get("revision"))
            existing = next((n for n in state["notes"] if n["id"] == data.get("id")), None)
            if data.get("id") and existing is None:
                raise ValueError("Note not found")
            note = deepcopy(existing) if existing else {"id": uuid.uuid4().hex, "created": now(), "source_round": number}
            if existing and "text" not in data:
                # Status changes and edits both append events; never erase history.
                status = data.get("status")
                if status not in STATUSES:
                    raise ValueError("Unknown status")
                note["status"] = status
            else:
                start, end = float(data.get("start", 0)), data.get("end")
                end = None if end in (None, "") else float(end)
                if not math.isfinite(start) or start < 0 or (end is not None and (not math.isfinite(end) or end < start)):
                    raise ValueError("Use a valid time range in seconds")
                kind = data.get("kind", "visual")
                if kind not in KINDS:
                    raise ValueError("Unknown note type")
                text = str(data.get("text", "")).strip()
                if not text or len(text) > 20000:
                    raise ValueError("Enter a note (up to 20,000 characters)")
                chapter = str(data.get("chapter", ""))
                if chapter and chapter not in {c["slug"] for c in state["round"]["chapters"]}:
                    raise ValueError("Choose a chapter from this review")
                original, replacement = str(data.get("original", "")), str(data.get("replacement", ""))
                if replacement and (kind != "narration" or not original.strip()):
                    raise ValueError("Narration replacements need the exact original text")
                note.update(start=start, end=end, source_round=number, kind=kind, text=text, chapter=chapter,
                            priority=data.get("priority", "normal"), status="open", original=original, replacement=replacement)
                if note["priority"] not in {"high", "normal", "low"}:
                    raise ValueError("Unknown priority")
            note["updated"] = now()
            folder = self.round_dir(ident, number)
            write_new(folder / f"event-{state['revision'] + 1:06d}.json", {"created": now(), "note": note})
        return self.state(ident, number)

    def build_packet(self, ident, number, revision):
        with self.locked():
            state = self._editable(ident, number, revision)
            project, review = state["project"], state["round"]
            chapters, script = deepcopy(review["chapters"]), review["script"]
            pending = [deepcopy(n) for n in state["notes"] if n["status"] in ("open", "verify")]
            applied = []
            for note in pending:
                note["application"] = "preserve" if note["kind"] == "keep" else "task"
                if note["status"] == "verify":
                    note["application"] = "verify"
                    continue
                if note["kind"] != "narration" or not note["replacement"]:
                    continue
                if chapters:
                    if not note["chapter"]:
                        raise ValueError("Choose a chapter for each narration replacement; edit the note if needed")
                    chapter = next(c for c in chapters if c["slug"] == note["chapter"])
                    original = " ".join(chapter["narration"])
                    if original.count(note["original"]) != 1:
                        raise ValueError(f"Narration conflict at {stamp(note['start'])}: original text must match exactly once in {note['chapter']}")
                    chapter["narration"] = [original.replace(note["original"], note["replacement"], 1)]
                else:
                    if script.count(note["original"]) != 1:
                        raise ValueError("Narration conflict: original text must match exactly once in the script")
                    script = script.replace(note["original"], note["replacement"], 1)
                note["application"] = "script_updated"
                applied.append(note["id"])
            if chapters:
                script = script_for(chapters)
            original_by_slug = {c["slug"]: c for c in project["original_chapters"]}
            round_by_slug = {c["slug"]: c for c in review["chapters"]}
            previous_overrides = {}
            if review.get("parent_packet"):
                parent = read_json(self.local_file(review["parent_packet"], {".json"}))
                previous_overrides = {edit["slug"]: edit for edit in parent.get("narration_overrides", [])}
            overrides = []
            for c in chapters:
                previous = previous_overrides.get(c["slug"], {})
                old = (original_by_slug.get(c["slug"])
                       or ({"narration": previous["before"]} if previous.get("before") else round_by_slug[c["slug"]]))
                current = round_by_slug[c["slug"]]
                if old["narration"] != c["narration"] or current["narration"] != c["narration"]:
                    variants = [current["narration"], *previous.get("before_variants", [])]
                    if previous.get("before"):
                        variants.append(previous["before"])
                    variants = list({tuple(lines): lines for lines in variants}.values())
                    overrides.append({"slug": c["slug"], "before": old["narration"],
                                      "before_variants": variants, "after": c["narration"]})
            allocated = [int(p.name.split("-")[-1]) for p in self.round_dir(ident, number).glob("packet-*") if p.is_dir()]
            packet_number = max(allocated, default=0) + 1
            folder = self.round_dir(ident, number) / f"packet-{packet_number:04d}"
            folder.mkdir()
            packet = {"schema": "domesim.video-review.v1", "project_id": ident, "round": number,
                      "packet": packet_number, "created": now(), "review_revision": revision,
                      "parent_packet": review.get("parent_packet"), "lesson": project["lesson"],
                      "source_video": review["video"], "source_video_bytes": review["video_bytes"],
                      "source_video_mtime_ns": review["video_mtime_ns"], "notes": pending,
                      "applied_note_ids": applied, "narration_overrides": overrides,
                      "chapters": chapters, "render_config": review.get("render_config", project["render_config"]),
                      "script_sha256": text_hash(script), "path": self.rel(folder / "revision.json")}
            tasks = self._actions(packet)
            prompt = (project["original_prompt"] + "\n\n" if project["original_prompt"] else "")
            prompt += (f"# Next build: {project['title']} — after review round {number}\n\n"
                       f"Review packet: {packet['path']}\nSource video: {review['video']}\n\n"
                       "Treat this as the next iteration. Preserve original media, source snapshots, earlier scripts and prompts. "
                       "Implement the open production tasks below, retaining the requested keeps. Exact text replacements "
                       "are already present in script-updated.md and narration_overrides in revision.json. "
                       "Visual, audio, pacing and cut notes still require implementation; do not claim they are applied merely because a packet exists. "
                       "Render into a new output path, regenerate affected narration and timing, then attach the render as the next review round. "
                       "Verify carried notes against the new video before resolving them.\n\n" + tasks)
            prompt += "\n\n" + self._instructions(packet)
            for filename, content in (("script-before.md", review["script"]), ("script-updated.md", script),
                                      ("action-list.md", tasks), ("next-build-prompt.md", prompt)):
                (folder / filename).write_text(content, encoding="utf-8")
            write_new(folder / "revision.json", packet)
        return self.state(ident, number)

    def _actions(self, packet):
        lines = [f"# Review actions — round {packet['round']}", ""]
        if not packet["notes"]:
            lines.append("No open notes. Review the video before starting the next iteration.")
        for note in sorted(packet["notes"], key=lambda n: ({"high": 0, "normal": 1, "low": 2}[n["priority"]], n["source_round"], n.get("start") or 0)):
            when = stamp(note.get("start"))
            if note.get("end") is not None:
                when += "–" + stamp(note["end"])
            if note["source_round"] != packet["round"]:
                when = f"round {note['source_round']} at {stamp(note.get('source_start'))}; remap in current video"
            lines.append(f"- [ ] [{note['priority']} / {note['kind']} / {note['application']}] {when} "
                         f"{note.get('chapter', '')}: {note['text']}")
            if note["replacement"]:
                lines.extend([f"  Original: {note['original']}", f"  Replacement: {note['replacement']}"])
        return "\n".join(lines) + "\n"

    def _instructions(self, packet):
        if not packet["lesson"]:
            return ("No renderer lesson is linked. Use script-updated.md and this prompt with the video's original generator. "
                    "The review packet retains the full task list for that generator.")
        return ("## Render handoff\n\nAfter implementing production tasks, use the launcher's Masterclass tab: "
                f"Lesson = {packet['lesson']}, Review packet = {packet['path']}, and a fresh Export MP4 path.\n\n"
                "Or from the project root (uses the saved render settings when available):\n\n"
                f'```powershell\npy -3.12 video_review.py render --packet "{packet["path"]}"\n```\n\n'
                "This explicitly starts a render; the normal narrator may use the online speech service. "
                "Narration overrides are applied in memory and validated against their original text. "
                "Reused audio must be regenerated when its words change.\n")

    def packet_path(self, ident, number, packet_number):
        if not isinstance(packet_number, int) or packet_number < 1:
            raise ValueError("Invalid packet")
        path = self.round_dir(ident, number) / f"packet-{packet_number:04d}" / "revision.json"
        if not path.is_file():
            raise ValueError("Packet not found")
        return path

    def advance(self, ident, number, data):
        video = self.local_file(data.get("video", ""), VIDEO_EXTENSIONS)
        metadata = self.metadata(video)
        with self.locked():
            state = self._editable(ident, number, data.get("revision"))
            packet_path = self.packet_path(ident, number, data.get("packet"))
            packet = read_json(packet_path)
            if packet["review_revision"] != state["revision"]:
                raise ValueError("Generate a new handoff to include the latest notes before attaching the next render")
            if any(r["video"] == self.rel(video) for r in state["rounds"]):
                raise ValueError("Each round needs a new video file. Preserve the earlier render.")
            if metadata["lesson"] and state["project"]["lesson"] and metadata["lesson"] != state["project"]["lesson"]:
                raise ValueError("This render belongs to a different lesson. Start a separate review for it.")
            chapters = metadata["chapters"] or [{k: v for k, v in c.items() if k not in ("start", "end")} for c in packet["chapters"]]
            script = script_for(chapters) if chapters else (metadata["script"] or (packet_path.parent / "script-updated.md").read_text(encoding="utf-8"))
            carried = []
            for note in packet["notes"]:
                item = deepcopy(note)
                if item.get("start") is not None:
                    item.update(source_start=item["start"], source_end=item.get("end"))
                item.update(start=None, end=None)
                if item["id"] in packet["applied_note_ids"]:
                    item["status"] = "verify"
                carried.append(item)
            new_number = number + 1
            folder = self.project_dir(ident) / f"round-{new_number:04d}"
            folder.mkdir()
            write_new(folder / "round.json", self._round(video, new_number, chapters, script,
                      parent_packet=self.rel(packet_path), carried_notes=carried,
                      render_config=metadata["render_config"] or packet["render_config"]))
        return self.state(ident)

    def media(self, ident, number):
        review = read_json(self.round_dir(ident, number) / "round.json")
        path = self.local_file(review["video"], VIDEO_EXTENSIONS)
        stat = path.stat()
        if stat.st_size != review["video_bytes"] or stat.st_mtime_ns != review["video_mtime_ns"]:
            raise ValueError("This video changed on disk. Restore the original and attach the new render as a new round.")
        return path
