"""Explicit, validated narration overlays. Never edit a lesson's source file."""
from __future__ import annotations

from dataclasses import replace
import json
from pathlib import Path

from .model import read_json, text_hash, now


def load_packet(path):
    path = Path(path).resolve()
    data = read_json(path)
    if data.get("schema") != "domesim.video-review.v1":
        raise ValueError("Expected a Video Review revision.json packet")
    script = path.parent / "script-updated.md"
    if not script.is_file() or text_hash(script.read_text(encoding="utf-8")) != data.get("script_sha256"):
        raise ValueError("Review script changed after the handoff. Generate a new packet.")
    return data


def apply_packet(lesson, path):
    packet = load_packet(path)
    if not packet.get("lesson") or packet["lesson"] != lesson.key:
        raise ValueError("Review packet belongs to a different lesson")
    chapters = {c.slug: c for c in lesson.chapters}
    changed = {}
    for edit in packet.get("narration_overrides", []):
        slug, before, after = edit["slug"], edit["before"], edit["after"]
        if slug not in chapters or slug in changed:
            raise ValueError(f"Missing or duplicate review chapter: {slug}")
        if not isinstance(after, list) or not after or any(not isinstance(line, str) or not line.strip() for line in after):
            raise ValueError(f"Empty/invalid replacement narration: {slug}")
        chapter = chapters[slug]
        # The source may already contain the requested edit; otherwise require
        # an exact base match so later authored changes cannot disappear.
        current = " ".join(chapter.narration)
        accepted = [before, after, *edit.get("before_variants", [])]
        if any(not isinstance(lines, list) or any(not isinstance(line, str) for line in lines) for lines in accepted):
            raise ValueError(f"Invalid original narration: {slug}")
        if current not in {" ".join(lines) for lines in accepted}:
            raise ValueError(f"Narration in {slug} changed since review. Reconcile it and make a new review packet.")
        changed[slug] = replace(chapter, narration=tuple(after))
    updated = replace(lesson, chapters=tuple(changed.get(c.slug, c) for c in lesson.chapters))
    updated.validate()  # Includes word-cued callouts; never silently break them.
    return updated


def write_render_receipt(video, lesson, durations, render_config=None):
    cursor, chapters = 0.0, []
    for chapter, duration in zip(lesson.chapters, durations):
        chapters.append({"slug": chapter.slug, "title": chapter.title,
                         "narration": list(chapter.narration), "start": cursor, "end": cursor + duration})
        cursor += duration
    payload = {"schema": "domesim.video-source.v1", "created": now(), "lesson": lesson.key,
               "title": lesson.title, "chapters": chapters, "render_config": render_config or {}}
    path = Path(video).with_name(Path(video).stem + "-review.json")
    path.write_text(json.dumps(payload, indent=2, ensure_ascii=False), encoding="utf-8")
    return path


def render_packet(packet_path, root, output=None, size=None, fps=None):
    """Run only on an explicit CLI request. It uses a fresh output directory."""
    from .model import ReviewStore
    packet_path = Path(packet_path).resolve()
    packet = load_packet(packet_path)
    if not packet.get("lesson"):
        raise ValueError("This review has no renderer lesson; use its next-build-prompt.md with the original generator")
    if output:
        output = Path(output).resolve()
        if output.exists():
            raise ValueError("Choose a new output filename; existing renders are preserved")
    else:
        destination = packet_path.parent / "renders"
        destination.mkdir(exist_ok=True)
        for index in range(1, 100000):
            run = destination / f"render-{index:04d}"
            try:
                run.mkdir()
                output = run / "video.mp4"
                break
            except FileExistsError:
                continue
    # Explicit configuration replaces a launch ticket; no other launcher's
    # pending ticket is consumed or overwritten by this command.
    allowed = {"size", "fps", "voice", "voice_rate", "voice_pitch", "voice_volume",
               "video_encoder", "video_preset", "ffmpeg", "ffprobe", "no_narration",
               "local_narration_plan", "render_fps", "orientation", "compose_segments",
               "segments_include", "segments_exclude"}
    cfg = {k: v for k, v in packet.get("render_config", {}).items() if k in allowed}
    cfg.update(action="export_video", lesson=packet["lesson"], review_packet=str(packet_path),
               export_video=str(output), fullscreen=False)
    if size:
        cfg["size"] = size
    if fps:
        cfg["fps"] = fps
    from two_v_demo.app import main
    result = main(config=cfg)
    if result:
        return result
    store = ReviewStore(root)
    # New render is useful even if the review acquired newer notes meanwhile.
    try:
        state = store.state(packet["project_id"], packet["round"])
        if packet_path != store.packet_path(packet["project_id"], packet["round"], packet["packet"]):
            raise ValueError("Packet was imported; attach the render from the workbench")
        store.advance(packet["project_id"], packet["round"], {
            "video": str(output), "packet": packet["packet"], "revision": state["revision"]})
        print("Video Review: new render attached as the next round.")
    except ValueError as exc:
        print(f"Render saved. Attach it in Video Review when ready: {exc}")
    return 0
