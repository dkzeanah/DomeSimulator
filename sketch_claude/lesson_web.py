"""Lesson films on the web engine: any two_v_demo lesson, rendered in the browser.

    py -3.12 -m sketch_claude lesson 2v --stills      # one still per chapter, both orientations, to look at first
    py -3.12 -m sketch_claude lesson 2v               # the release: landscape, phone cut, captions, release folder
    py -3.12 -m sketch_claude lesson 2v --draft       # into tmp/, not the library

The moderngl engine (two_v_demo/app.py) stays as it is. This is its successor, and it keeps
what that engine learned, in one place:

* **The words are the lesson's own.** Each chapter's clip is ``audio.spoken_chapter_text``
  (promise, then narration) in the house voice (``audio.DEFAULT_VOICE``, rate and pitch), and
  a chapter lasts its authored length or its speech plus ``SPEECH_DELAY`` and
  ``TAIL_PADDING``, whichever is longer, exactly as the exporter times it. The narration plan
  records those stretched lengths, so the release's chapter timestamps are true.
* **Numbers on screen are computed.** A lesson with a web stage brings its equations from the
  code (for the 2V masterclass, ``two_v_demo.geometry``); the typed strings in the old chapter
  tuples are only the fallback for a lesson that has none yet.
* **Every render is a release.** Landscape and a phone cut framed for the phone (a second
  pass laid out for 9:16, not a crop that would cut off the sheet and the beat number),
  captions in the house format (``narration.write_companion_files``), the narration plan, the
  review JSON, and ``release.build_release``: a thumbnail per chapter, YouTube, Facebook and
  Instagram copy with hashtags.
* **The beat number is on every frame**, top left, so "beat 7 is wrong" points at one chapter.
* **Look before rendering.** ``--stills`` draws one frame from every chapter, both
  orientations, into tmp/lesson-stills/<lesson>/, in seconds instead of a render's minutes.
* **Music is made, not sampled**: ``two_v_demo.score.compose(bed=True)`` under the voice.

The browser draws a frame as a pure function of time (static/lesson.js, static/lessonstage.js),
so a render is the same frames however fast the machine. The frames go through the Director's
own render pipe (episode_server.render_start / render_frame); this module mixes the sound.
A lesson without its own web stage gets the generic one: the solver's wedge dome.
"""

from __future__ import annotations

import json
import math
import re
import subprocess
import time
from functools import lru_cache
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
STILLS = ROOT / "tmp" / "lesson-stills"
FPS = 30
TITLE_HOLD = 2.4          # seconds the chapter's title card stays up before it shrinks to the badge


def _lesson(key: str):
    from two_v_demo.lesson_registry import get_lesson
    return get_lesson(key)


def _duration(path: Path) -> float:
    from two_v_demo.audio import resolve_executable
    probe = resolve_executable("ffprobe")
    r = subprocess.run([probe, "-v", "error", "-show_entries", "format=duration", "-of", "csv=p=0", str(path)],
                       capture_output=True, text=True)
    return float(r.stdout.strip() or 0.0)


# ----------------------------------------------------------------------
# What the 2V masterclass shows, from the code that computes it
# ----------------------------------------------------------------------

MEASURED_LONG_IN = 72.0
MEASURED_SHORT_IN = 63.5
"""The owner's two measured members (the lesson's premise). Measured, not derived: on screen as such."""


def _v(a) -> list:
    return [[round(float(x), 6) for x in row] for row in a]


def stage_2v() -> dict:
    from two_v_demo import geometry as g
    G = g.build_demo_geometry()
    raw, _faces = g.raw_icosahedron()
    return {
        "phi": g.PHI,
        "raw": _v(raw), "ico": _v(G.ico_vertices), "icoEdges": [list(e) for e in G.ico_edges],
        "mid": _v(G.flat_midpoints), "verts": _v(G.vertices),
        "edges": [list(e) for e in G.edges], "edgeClass": list(G.edge_class_by_edge),
        "hemiFaces": [list(map(int, f)) for f in G.hemisphere_faces], "hemiEdges": [list(e) for e in G.hemisphere_edges],
        "baseRing": list(map(int, G.base_ring)),
        "platonic": [{"name": s.name, "verts": _v(s.vertices), "edges": [list(e) for e in s.edges], "faces": s.faces}
                     for s in g.platonic_solids()],
        "short": G.short_factor, "long": G.long_factor,
        "fit": _fit_dict(),
    }


def _fit_dict() -> dict:
    from two_v_demo import geometry as g
    f = g.fit_measurements(MEASURED_LONG_IN, MEASURED_SHORT_IN)
    return {"long": MEASURED_LONG_IN, "short": MEASURED_SHORT_IN, "R": f.best_fit_radius,
            "RL": f.radius_from_long, "RS": f.radius_from_short, "pL": f.predicted_long, "pS": f.predicted_short}


def equations_2v() -> dict[str, list[str]]:
    """Every equation the masterclass puts on screen, with its numbers computed here."""
    from two_v_demo import geometry as g
    G = g.build_demo_geometry()
    phi = g.PHI
    r_raw = math.sqrt(1 + phi * phi)
    parent = 2 / r_raw
    # flat_midpoints holds all 42 flat vertices: the 12 parent corners (radius 1) and the 30 midpoints
    mids = [r for r in (math.dist((0, 0, 0), m) for m in G.flat_midpoints) if r < 1 - 1e-9]
    assert len(mids) == 30 and max(mids) - min(mids) < 1e-9, mids
    mid = mids[0]
    f = g.fit_measurements(MEASURED_LONG_IN, MEASURED_SHORT_IN)
    counts = {c.name: c for c in G.edge_classes}
    tri = {t.name: t for t in G.triangle_classes}
    short, long = G.short_factor, G.long_factor
    sl = counts["SHORT"].hemisphere_count
    ll = counts["LONG"].hemisphere_count
    llll = next(t for t in G.triangle_classes if set(t.side_names) == {"LONG"})
    lss = next(t for t in G.triangle_classes if t is not llll)
    return {
        "welcome": [f"measured ratio = {MEASURED_LONG_IN:g} / {MEASURED_SHORT_IN:g} = {MEASURED_LONG_IN / MEASURED_SHORT_IN:.6f}",
                    f"phi = {phi:.6f}  (not the target)"],
        "triangles": ["F = F_compression + F_tension", "geometry explains form; engineering sizes members"],
        "platonic": ["faces: " + ", ".join(str(s.faces) for s in g.platonic_solids()),
                     "2V means: divide every parent edge into 2 segments"],
        "phi": ["phi = (1 + sqrt(5)) / 2", f"R_raw = sqrt(1 + phi^2) = {r_raw:.6f}", "edge_raw = 2"],
        "normalize": ["v_hat = v / ||v||", f"parent chord = 2 / sqrt(1 + phi^2) = {parent:.6f} R"],
        "subdivide": ["m = (a + b) / 2", f"||m|| = {mid:.6f} < 1"],
        "project": ["p = m / ||m||", f"projection distance = 1 - ||m|| = {1 - mid:.6f} R"],
        "classes": [f"SHORT = {short:.6f} R", f"LONG = {long:.6f} R", f"LONG / SHORT = {long / short:.6f}"],
        "derive": ["c = ||R u - R v||", "theta = acos(u . v)", "c = 2 R sin(theta / 2)"],
        "your_dome": [f"R_long = {MEASURED_LONG_IN:g} / {long:.6f} = {f.radius_from_long:.2f} in",
                      f"R_short = {MEASURED_SHORT_IN:g} / {short:.6f} = {f.radius_from_short:.2f} in",
                      f"best R = {f.best_fit_radius:.2f} in  (residuals {f.long_residual:+.3f} / {f.short_residual:+.3f} in)"],
        "cut_list": ["center length = chord factor x R",
                     f"at R = {f.best_fit_radius:.2f} in: LONG {long * f.best_fit_radius:.2f} in, SHORT {short * f.best_fit_radius:.2f} in",
                     "cut length = center length - connector deduction"],
        "triangles_build": [f"{lss.hemisphere_count} x SHORT-SHORT-LONG panels", f"{llll.hemisphere_count} x LONG-LONG-LONG panels",
                            f"base ring: {len(G.base_ring)} vertices;  {sl} SHORT + {ll} LONG struts"],
        "verify": ["check: length -> triangle -> ring -> radius -> height", f"expected dome height = R = {f.best_fit_radius:.2f} in"],
        "finale": ["phi -> icosahedron -> 2V subdivision -> projection -> SHORT + LONG -> scale"],
    }


#: Lessons with a web stage of their own: (stage data, equations). Add a lesson here to give it one.
WEB_STAGES = {"2v": (stage_2v, equations_2v)}


# ----------------------------------------------------------------------
# The timeline: the lesson's words, timed by their voice
# ----------------------------------------------------------------------

def _caption_cues(lesson, durations, speech) -> list[list]:
    """The burned-in captions: exactly the SRT the release ships, parsed back into cues."""
    from two_v_demo import audio as A
    from two_v_demo import narration as N
    speak_promise = getattr(lesson, "style", "teaching") != "hype"
    srt = N.subtitle_file(tuple(durations), tuple(speech), A.SPEECH_DELAY, lesson.chapters, speak_promise)
    cues = []
    for block in srt.strip().split("\n\n"):
        lines = block.strip().splitlines()
        if len(lines) < 3:
            continue
        a, b = lines[1].split(" --> ")
        sec = lambda s: int(s[0:2]) * 3600 + int(s[3:5]) * 60 + int(s[6:8]) + int(s[9:12]) / 1000
        cues.append([round(sec(a), 3), round(sec(b), 3), " ".join(lines[2:])])
    return cues


@lru_cache(maxsize=8)
def spec(key: str) -> dict:
    """Everything the browser needs to draw the film: chapters, timing, captions, the stage."""
    from two_v_demo import audio as A
    from . import episode_server as E
    lesson = _lesson(key)
    speak_promise = getattr(lesson, "style", "teaching") != "hype"
    rate = lesson.voice_rate or A.DEFAULT_RATE
    stage, eqs = WEB_STAGES.get(key, (None, None))
    computed = eqs() if eqs else {}
    chapters, durations, speech, clips = [], [], [], []
    t = 0.0
    for i, ch in enumerate(lesson.chapters):
        text = A.spoken_chapter_text(i, lesson.chapters, speak_promise)
        clip = E.voice(text, A.DEFAULT_VOICE, rate, A.DEFAULT_PITCH)
        spoken = _duration(clip)
        dur = max(float(ch.duration), A.SPEECH_DELAY + spoken + A.TAIL_PADDING)
        chapters.append({"slug": ch.slug, "number": ch.number, "title": ch.title, "promise": ch.promise,
                         "narration": list(ch.narration), "equations": computed.get(ch.slug, list(ch.equations)),
                         # the sheet says "computed" only where a computed number is on it
                         "computed": ch.slug in computed and any(re.search(r"\d\.\d", e) for e in computed[ch.slug]),
                         "stage": ch.stage if stage else "generic",
                         "camera": list(ch.camera), "start": round(t, 4), "duration": round(dur, 4),
                         "speechStart": round(t + A.SPEECH_DELAY, 4), "speech": round(spoken, 4)})
        durations.append(dur)
        speech.append(spoken)
        clips.append(str(clip))
        t += dur
    return {"key": key, "title": lesson.title, "brand": lesson.brand, "fps": FPS, "titleHold": TITLE_HOLD,
            "total": round(t, 4), "chapters": chapters, "captions": _caption_cues(lesson, durations, speech),
            "stage": stage() if stage else _generic_stage(),
            "voice": {"name": A.DEFAULT_VOICE, "rate": rate, "pitch": A.DEFAULT_PITCH}, "_clips": clips,
            "measured": {"long_in": MEASURED_LONG_IN, "short_in": MEASURED_SHORT_IN} if key == "2v" else None}


def _generic_stage() -> dict:
    """The solver's wedge dome, node and strut lines, for a lesson without a stage of its own."""
    from two_v_demo import raw_wedge_bridge as b
    topo = b.simulator().build_2v_hemisphere(72.0)
    s = float(topo.sphere_radius_in)
    return {"verts": _v(topo.vertices / s), "edges": [list(map(int, k)) for k in topo.edges],
            "edgeClass": ["LONG" if e.edge_type == "A" else "SHORT" for e in topo.edges.values()],
            "hemiFaces": [list(map(int, f.vertices)) for f in topo.faces]}


def public_spec(key: str) -> dict:
    return {k: v for k, v in spec(key).items() if not k.startswith("_")}


# ----------------------------------------------------------------------
# Sound, files and the release
# ----------------------------------------------------------------------

JOBS: dict[str, dict] = {}       # lesson -> the landscape result, waiting for its phone pass


def soundtrack(key: str, out: Path) -> Path:
    """Every chapter's clip at its own start, over the score's narration bed."""
    import numpy as np
    from two_v_demo import audio as A
    from two_v_demo import score
    s = spec(key)
    sr = score.SAMPLE_RATE
    total = s["total"] + 0.5
    bed = score.compose(total, bed=True)
    if bed.ndim == 1:
        bed = np.stack([bed, bed], axis=1)
    mix = bed[: int(total * sr)] * 0.16
    ff = A.resolve_executable("ffmpeg")
    for ch, clip in zip(s["chapters"], s["_clips"]):
        raw = subprocess.run([ff, "-v", "error", "-i", clip, "-f", "f32le", "-ac", "2", "-ar", str(sr), "-"],
                             capture_output=True).stdout
        voice = np.frombuffer(raw, dtype=np.float32).reshape(-1, 2).astype(np.float64)
        at = int(ch["speechStart"] * sr)
        end = min(len(mix), at + len(voice))
        # the bed dips under the voice and comes back after it
        duck = np.ones(len(mix))
        duck[max(0, at - sr // 4): end + sr // 2] = 0.55
        mix *= duck[:, None]
        mix[at:end] += voice[: end - at]
    peak = float(np.abs(mix).max()) or 1.0
    if peak > 0.98:
        mix *= 0.98 / peak
    score.write_wav(mix, out)
    return out


def finish(rid: str, meta: dict) -> dict:
    """Close a render: mux its frames with the sound; on the phone pass, file the whole release."""
    from two_v_demo import audio as A
    from two_v_demo import narration as N
    from . import episode_server as E
    key, orient = meta["lesson"], meta.get("orient", "landscape")
    r = E.RENDERS.pop(rid)
    r["proc"].stdin.close()
    err = r["proc"].stderr.read().decode("utf-8", "replace")
    if r["proc"].wait() != 0 or not r["video"].exists():
        return {"error": f"the frames did not encode: {err[-300:]}"}
    s = spec(key)
    wav = soundtrack(key, r["work"] / "soundtrack.wav")
    ff = A.resolve_executable("ffmpeg")
    if orient == "landscape":
        if r["draft"]:
            folder = ROOT / "tmp" / "sketch-claude-drafts" / f"lesson-{key}-{time.strftime('%Y%m%d-%H%M%S')}"
            folder.mkdir(parents=True)
            name = f"web-{key}"
        else:
            import medialib
            slug = "web-" + "".join(c if c.isalnum() else "-" for c in s["title"].lower()).strip("-")
            folder = medialib.new_folder(slug)
            name = folder.name.split("-", 1)[1]
        out = folder / f"{name}.mp4"
    else:
        job = JOBS[key]
        folder, name = Path(job["folder"]), job["name"]
        out = folder / f"{name}-vertical.mp4"
    run = subprocess.run([ff, "-y", "-v", "error", "-i", str(r["video"]), "-i", str(wav), "-c:v", "copy", "-c:a", "aac",
                          "-b:a", "192k", "-shortest", "-movflags", "+faststart", str(out)], capture_output=True, text=True)
    if run.returncode or not out.exists():
        return {"error": run.stderr[-400:], "kept": str(r["work"])}
    import shutil
    shutil.rmtree(r["work"], ignore_errors=True)
    lesson = _lesson(key)
    durations = tuple(c["duration"] for c in s["chapters"])
    speech = tuple(c["speech"] for c in s["chapters"])
    speak_promise = getattr(lesson, "style", "teaching") != "hype"
    N.write_companion_files(out, durations, speech, A.SPEECH_DELAY, lesson.chapters, s["title"], speak_promise)
    result = {"video": out.relative_to(ROOT).as_posix(), "folder": folder.relative_to(ROOT).as_posix()}
    if orient == "landscape":
        base = out.with_suffix("")
        Path(f"{base}-narration-plan.json").write_text(json.dumps({
            "engine": "web (sketch_claude/lesson_web.py)", "lesson": key, "voice": s["voice"],
            "speech_delay": A.SPEECH_DELAY, "tail_padding": A.TAIL_PADDING,
            "chapter_durations": list(durations), "chapter_starts": [c["start"] for c in s["chapters"]],
            "speech_durations": list(speech), "total_duration": s["total"]}, indent=2), encoding="utf-8")
        Path(f"{base}-review.json").write_text(json.dumps({
            "schema": "domesim.video-source.v1", "created": time.strftime("%Y-%m-%dT%H:%M:%S"), "lesson": key,
            "engine": "web", "title": s["title"],
            "chapters": [{"slug": c["slug"], "title": c["title"], "narration": c["narration"], "equations": c["equations"],
                          "start": c["start"], "end": c["start"] + c["duration"]} for c in s["chapters"]]},
            indent=2), encoding="utf-8")
        JOBS[key] = {"folder": str(folder), "name": name, "video": str(out), "draft": r["draft"]}
    else:
        job = JOBS.pop(key)
        if not job["draft"]:
            from two_v_demo.release import build_release
            rel = build_release(key, Path(job["video"]), portrait=out)
            result["release"] = str(getattr(rel, "folder", "")) if rel else ""
            try:
                import medialib
                medialib.write_index()
            except Exception:
                pass
    E.FINISHED.append(result)
    return result


def save_still(key: str, orient: str, n: int, png: bytes) -> dict:
    folder = STILLS / key / orient
    folder.mkdir(parents=True, exist_ok=True)
    f = folder / f"{n + 1:02d}.png"
    f.write_bytes(png)
    return {"still": f.relative_to(ROOT).as_posix()}


# ----------------------------------------------------------------------
# Headless: the same page, in a Chrome this process starts
# ----------------------------------------------------------------------

def headless(key: str, mode: str = "render", draft: bool = False, port: int | None = None, timeout_s: float = 3 * 3600) -> list[dict]:
    """``mode`` is "render" (landscape, then phone) or "stills". Returns what each pass produced."""
    import tempfile
    import threading
    from two_v_demo.book_export import _chrome_path
    from . import episode_server as E
    from . import server as SV
    chrome = _chrome_path()
    if not chrome:
        raise RuntimeError("no Chrome or Edge found for the headless render")
    public_spec(key)                       # voices synthesised before the browser asks
    httpd = SV.serve(port or 0)
    threading.Thread(target=httpd.serve_forever, daemon=True).start()
    results = []
    for orient in ("landscape", "phone"):
        size = "1920,1080" if orient == "landscape" else "1080,1920"
        url = (f"http://127.0.0.1:{httpd.server_address[1]}/lesson?lesson={key}&orient={orient}"
               f"&{'stills' if mode == 'stills' else 'autorender'}=1&draft={'1' if draft else '0'}")
        profile = tempfile.mkdtemp(prefix="lesson-chrome-")
        before = len(E.FINISHED)
        proc = subprocess.Popen([chrome, "--headless=new", f"--user-data-dir={profile}", f"--window-size={size}",
                                 "--mute-audio", "--enable-gpu", "--ignore-gpu-blocklist", "--use-angle=d3d11",
                                 "--enable-unsafe-swiftshader", "--disable-background-timer-throttling",
                                 "--disable-renderer-backgrounding", "--enable-logging=stderr", "--v=0", url],
                                stdout=subprocess.DEVNULL, stderr=subprocess.PIPE, text=True, encoding="utf-8", errors="replace")
        done: list[str] = []

        def relay(p=proc, d=done):
            for line in p.stderr:
                if "[lesson" in line:
                    msg = "[lesson" + line.split("[lesson", 1)[1].split('", source')[0].rstrip()
                    print(msg, flush=True)
                    if msg.startswith("[lesson-done]") or msg.startswith("[lesson-failed]"):
                        d.append(msg)
        threading.Thread(target=relay, daemon=True).start()
        t0 = time.time()
        try:
            while not done and (mode == "stills" or len(E.FINISHED) == before):
                if proc.poll() is not None:
                    raise RuntimeError("Chrome exited before the pass finished")
                if time.time() - t0 > timeout_s:
                    raise TimeoutError("the pass took too long")
                time.sleep(1.0)
            if done and done[0].startswith("[lesson-failed]"):
                raise RuntimeError(done[0])
            while mode != "stills" and len(E.FINISHED) == before:
                time.sleep(0.5)
            results.append(E.FINISHED[-1] if mode != "stills" else {"stills": str(STILLS / key / orient)})
        finally:
            proc.kill()
    httpd.shutdown()
    return results
