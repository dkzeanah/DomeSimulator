#!/usr/bin/env python3
"""Generate a short trailer for the Dome Simulator launcher.

House-style, matching deliverables/dome_accessibility/.../assemble_slideshow_video:
  * 1920x1080, 30 fps, libx264 crf 18, +faststart
  * manifest-driven scenes, each with a duration and a narration line
  * a captions.srt sidecar written next to the video
  * a unique, non-overwriting versioned output directory + a render receipt

The trailer is a *silent* montage with burned-in titles, composited over the
project's own dome renders. The narration lines are written to the .srt so a
voiceover can be recorded and aligned afterwards. Nothing here overwrites.
"""
from __future__ import annotations

import json
import shutil
import subprocess
import sys
import uuid
from datetime import datetime
from pathlib import Path

import numpy as np
from PIL import Image, ImageDraw, ImageFont

ROOT = Path(__file__).resolve().parent
RENDERS = (ROOT.parent / "dome_accessibility_20260816_082305_167_1d3f14" / "assets")
FONTS = Path("C:/Windows/Fonts")

W, H = 1920, 1080
FPS = 30
MARGIN = 130

BG = (16, 18, 22)          # launcher theme background #12141a
INK = (232, 238, 245)      # near-white
SUBINK = (176, 189, 205)   # muted grey
ACCENT = (224, 164, 76)    # warm amber

FONT_KICKER = ImageFont.truetype(str(FONTS / "segoeuib.ttf"), 38)
FONT_HEAD = ImageFont.truetype(str(FONTS / "segoeuib.ttf"), 116)
FONT_HEAD_SM = ImageFont.truetype(str(FONTS / "segoeuib.ttf"), 92)
FONT_SUB = ImageFont.truetype(str(FONTS / "segoeui.ttf"), 42)

# scene: bg render filename or None (gradient card); kicker; headline (\n ok);
# sub; narration (spoken/SRT); seconds
SCENES = [
    dict(bg="01_hero_entry.png", kicker="", head="DOME\nSIMULATOR",
         sub="A geodesic dome design, manufacturing & presentation suite",
         vo="Dome Simulator — a complete toolkit for designing, pricing, "
            "manufacturing, and presenting geodesic dome buildings.", sec=11),
    dict(bg=None, kicker="ONE LAUNCHER", head="Eight tools,\none window",
         sub="No command line. Every option is a field.",
         vo="It all runs from one launcher. Eight tools, one window — no "
            "command line, every option right in front of you.", sec=10),
    dict(bg="02_open_circulation.png", kicker="DOME CREATOR",
         head="Walk it.\nBuild it.",
         sub="Mouse-first controls, everything in real-world scale",
         vo="The Dome Creator is a walkable, build-a-home customizer. "
            "Mouse-first controls, everything in real-world scale.", sec=11),
    dict(bg=None, kicker="LIVE BILL OF MATERIALS", head="Every number,\ncomputed",
         sub="Struts  ·  hubs  ·  weight  ·  cost  ·  solar kW  ·  trees to harvest",
         vo="Swap panels, layers, and frames, and a full bill of materials "
            "updates live — every figure computed from the geometry, never "
            "typed in.", sec=12),
    dict(bg="05_dome_cutaway.png", kicker="SIMULATE", head="Construction\n& power",
         sub="Real build order, labor hours, solar charge, battery draw",
         vo="Simulate the build element by element with real labor hours — "
            "then electrify it and watch solar charge the battery in real "
            "time.", sec=12),
    dict(bg=None, kicker="DOME FORGE", head="A dome made\nof layers",
         sub="Hide  ·  fade  ·  reorder  ·  tune every part",
         vo="Dome Forge builds one dome out of layers — the way an image is "
            "built of layers in a paint program.", sec=10),
    dict(bg=None, kicker="CUT PATTERNS", head="Curved shell,\nflat patterns",
         sub="To-scale, dimensioned, and nestable for cutting",
         vo="Because the shell is flat triangles, it flattens into real, "
            "to-scale cutting patterns — darts and all.", sec=10),
    dict(bg=None, kicker="ASSEMBLY LINE", head="The factory",
         sub="15 stations  →  a finished, watertight home",
         vo="The Assembly Line rolls a dome through fifteen stations until a "
            "complete, watertight home comes off the end.", sec=11),
    dict(bg=None, kicker="AN UNDERWRITING TOOL", head="Real P&L.\nReal break-even.",
         sub="Material + labor + overhead vs. sale price",
         vo="Every part carries a real cost and install time, feeding a live "
            "profit-and-loss model and break-even math for scaling up.", sec=12),
    dict(bg="03_accessible_kitchen.png", kicker="2V MASTERCLASS",
         head="Geometry from\nfirst principles",
         sub="14 chapters  ·  exportable to narrated video",
         vo="The 2V Masterclass rebuilds the geometry from first principles "
            "across fourteen chapters — and exports the whole lesson to "
            "video.", sec=12),
    dict(bg=None, kicker="PRESENTER STUDIO", head="Text to video",
         sub="A real editing timeline. The same engine renders the MP4.",
         vo="Presenter Studio is a text-to-video engine with a real editing "
            "timeline — and what you arrange is exactly what renders.", sec=11),
    dict(bg=None, kicker="LOCAL VOICE STUDIO", head="Narrate it —\nlocally",
         sub="Your own voice  ·  no hosted AI",
         vo="Local Voice Studio narrates it all in your own voice, entirely "
            "on your machine, with no hosted AI.", sec=10),
    dict(bg=None, kicker="ONE SOURCE OF TRUTH", head="Nothing\nhardcoded twice",
         sub="Shared geometry & materials across every tool",
         vo="Every number across every tool comes from the same shared "
            "geometry and materials code — so the figures can never drift out "
            "of sync.", sec=11),
    dict(bg="04_bed_bath_suite.png", kicker="", head="DOME\nSIMULATOR",
         sub="github.com/dkzeanah/DomeSimulator   ·   full demo playlist on YouTube",
         vo="It's all on GitHub, with a full demo playlist linked at the top "
            "of the repo. Dome Simulator.", sec=10),
]


def gradient_bg() -> Image.Image:
    top = np.array([22, 26, 34], dtype=float)
    bot = np.array([11, 12, 16], dtype=float)
    t = np.linspace(0, 1, H)[:, None]
    col = (top * (1 - t) + bot * t).astype(np.uint8)
    arr = np.repeat(col[:, None, :], W, axis=1)
    img = Image.fromarray(arr, "RGB")
    # subtle accent glow lower-left
    glow = Image.new("L", (W, H), 0)
    gd = ImageDraw.Draw(glow)
    gd.ellipse([-400, H - 300, 700, H + 500], fill=70)
    tint = Image.new("RGB", (W, H), ACCENT)
    img = Image.composite(Image.blend(img, tint, 0.10), img, glow)
    return img


def cover(img: Image.Image) -> Image.Image:
    scale = max(W / img.width, H / img.height)
    r = img.resize((round(img.width * scale), round(img.height * scale)),
                   Image.LANCZOS)
    left = (r.width - W) // 2
    top = (r.height - H) // 2
    return r.crop((left, top, left + W, top + H)).convert("RGB")


def scrim(img: Image.Image) -> Image.Image:
    """Darken the whole frame slightly, and hard on the lower-left text zone."""
    base = Image.new("L", (W, H), 90)          # overall darken ~35%
    grad = np.tile(np.linspace(235, 0, H)[:, None], (1, W)).astype(np.uint8)
    lower = Image.fromarray(grad, "L")          # stronger toward the bottom
    mask = Image.composite(Image.new("L", (W, H), 210), base, lower)
    black = Image.new("RGB", (W, H), (6, 7, 10))
    return Image.composite(black, img, mask)


def draw_tracked(d: ImageDraw.ImageDraw, xy, text, font, fill, track):
    x, y = xy
    for ch in text:
        d.text((x, y), ch, font=font, fill=fill)
        x += d.textlength(ch, font=font) + track


def wrap(d, text, font, max_w):
    words, lines, cur = text.split(), [], ""
    for w in words:
        trial = (cur + " " + w).strip()
        if d.textlength(trial, font=font) <= max_w:
            cur = trial
        else:
            lines.append(cur)
            cur = w
    if cur:
        lines.append(cur)
    return lines


def render_card(scene: dict, out: Path) -> None:
    if scene["bg"]:
        img = scrim(cover(Image.open(RENDERS / scene["bg"])))
    else:
        img = gradient_bg()
    d = ImageDraw.Draw(img)

    head_font = FONT_HEAD if len(scene["head"]) <= 26 else FONT_HEAD_SM
    head_lines = scene["head"].split("\n")
    line_h = head_font.size + 14
    block_h = line_h * len(head_lines)

    y = H - MARGIN - block_h - 78          # leave room for kicker above, sub below
    if scene["kicker"]:
        d.line([(MARGIN, y - 34), (MARGIN + 64, y - 34)], fill=ACCENT, width=5)
        draw_tracked(d, (MARGIN, y - 96), scene["kicker"], FONT_KICKER, ACCENT, 3)

    for i, line in enumerate(head_lines):
        d.text((MARGIN, y + i * line_h), line, font=head_font, fill=INK)

    sy = y + block_h + 26
    for line in wrap(d, scene["sub"], FONT_SUB, W - 2 * MARGIN):
        d.text((MARGIN, sy), line, font=FONT_SUB, fill=SUBINK)
        sy += FONT_SUB.size + 10

    img.save(out, "PNG")


def srt_time(s: float) -> str:
    ms = round(s * 1000)
    h, ms = divmod(ms, 3_600_000)
    m, ms = divmod(ms, 60_000)
    sec, ms = divmod(ms, 1000)
    return f"{h:02d}:{m:02d}:{sec:02d},{ms:03d}"


def main() -> int:
    ffmpeg = shutil.which("ffmpeg")
    if not ffmpeg:
        raise SystemExit("ffmpeg not found on PATH")

    stamp = datetime.now().strftime("%Y%m%d_%H%M%S_%f")[:-3]
    run = ROOT / f"render_{stamp}_{uuid.uuid4().hex[:6]}"
    slides = run / "slides"
    slides.mkdir(parents=True)

    concat = ["ffconcat version 1.0"]
    caps, manifest_scenes, t = [], [], 0.0
    for i, sc in enumerate(SCENES, 1):
        png = slides / f"slide-{i:02d}.png"
        render_card(sc, png)
        dur = float(sc["sec"])
        concat += [f"file '{png.as_posix()}'", f"duration {dur:.3f}"]
        caps.append(f"{i}\n{srt_time(t)} --> {srt_time(t + dur)}\n{sc['vo'].strip()}\n")
        manifest_scenes.append(dict(id=i, slide_number=i, duration_seconds=dur,
                                    kicker=sc["kicker"], headline=sc["head"],
                                    narration=sc["vo"].strip()))
        t += dur
    concat.append(f"file '{(slides / f'slide-{len(SCENES):02d}.png').as_posix()}'")

    concat_path = run / "slides.ffconcat"
    concat_path.write_text("\n".join(concat) + "\n", encoding="utf-8", newline="\n")
    srt_path = run / "captions.srt"
    srt_path.write_text("\n".join(caps), encoding="utf-8", newline="\n")

    manifest = dict(title="Dome Simulator — Launcher Trailer",
                    resolution=[W, H], frame_rate=FPS,
                    total_seconds=round(t, 3), scene_count=len(SCENES),
                    scenes=manifest_scenes)
    manifest_path = run / "video_manifest.json"
    manifest_path.write_text(json.dumps(manifest, indent=2) + "\n",
                             encoding="utf-8", newline="\n")

    video = run / "dome_simulator_trailer.mp4"
    vf = ("format=yuv420p")
    subprocess.run([ffmpeg, "-n", "-f", "concat", "-safe", "0", "-i",
                    str(concat_path), "-vf", vf, "-r", str(FPS), "-c:v",
                    "libx264", "-preset", "medium", "-crf", "18",
                    "-movflags", "+faststart", str(video)], check=True)

    receipt = dict(run_directory=str(run), video=str(video),
                   captions=str(srt_path), manifest=str(manifest_path),
                   scene_count=len(SCENES), timeline_seconds=round(t, 3),
                   note="silent trailer with burned-in titles; record VO over "
                        "the .srt lines", overwrite_policy="unique dir + ffmpeg -n")
    (run / "render_receipt.json").write_text(json.dumps(receipt, indent=2) + "\n",
                                             encoding="utf-8", newline="\n")
    print(json.dumps(receipt, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
