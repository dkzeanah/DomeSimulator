"""The server side of the Director: the episode's workshop set, character voices, and recordings.

* :func:`set_pieces` -- the "Dome Time" studio bench beside the dome: the model's own jig,
  rails and a panel of real sticks, the table saw ripping on the dome's bevel, and a loose
  panel the cast can carry (its sticks centred on the origin, flat).
* :func:`voice` -- one line spoken in a character's voice (Edge TTS), cached by its text so a
  replay costs nothing.
* :func:`save_recording` -- a recorded take, turned into a release: a new numbered folder in
  ``deliverables/`` with the landscape cut (MP4), a phone cut, the captions, a thumbnail per
  scene and ``description.md``. Nothing is ever written over.
"""

from __future__ import annotations

import asyncio
import hashlib
import json
import math
import subprocess
from pathlib import Path

import numpy as np

from . import TAG
from . import model as M
from . import shop as SH
from .solids import Mesh

ROOT = Path(__file__).resolve().parents[1]
VOICE_CACHE = ROOT / "tmp" / "sketch-claude-voices"

#: Where the studio bench and the table saw stand, beside the dome (metres; the dome is at the origin).
BENCH_AT = (-6.2, -2.0)
SAW_AT = (-6.4, -4.6)


def _rot(deg: float) -> np.ndarray:
    a = math.radians(deg)
    return np.array([[math.cos(a), -math.sin(a), 0], [math.sin(a), math.cos(a), 0], [0, 0, 1.0]])


def _place(pieces, at, yaw=0.0, prefix="set"):
    """Stand shop pieces on the ground beside the dome (the ground is a deck's height below the floor)."""
    R = _rot(yaw)
    z = -M.D("deck_h_m")
    out = []
    for p in pieces:
        m = p.mesh
        p.mesh = Mesh(m.verts @ R.T + np.array([at[0], at[1], z]), m.tris, m.edges, m.polys)
        p.id = f"{prefix}-{p.id}"
        p.group = prefix
        out.append(p)
    return out


def set_pieces(spec: M.Spec) -> dict:
    m = M.build(spec)
    hexa = next(p for p in m.panels if p.cls == "B" and not p.partial and not p.window and not p.skylight)
    bench = SH.bench(size=(1.6, 1.3)) + SH.jig(m, hexa) + SH.panel_on_jig(m, hexa, "all")
    bench = [p for p in bench if p.tag != "site"]
    bevel = m.tables["classes"][1]["bevels"][1] if len(m.tables["classes"]) > 1 else m.tables["bevel_hi"]
    saw = SH.table_saw(bevel)
    pieces = _place(bench, BENCH_AT, 90, "bench") + _place(saw, SAW_AT, 90, "saw")
    # a loose panel to carry: the same sticks, centred on the origin, lying flat
    loose = SH.panel_on_jig(m, hexa, "all")
    c = np.vstack([p.mesh.verts for p in loose]).mean(axis=0)
    for p in loose:
        p.mesh = Mesh(p.mesh.verts - c, p.mesh.tris, p.mesh.edges, p.mesh.polys)
        p.id = "prop-" + p.id
        p.group = "prop-panel"
    from .server import _b64, _clean

    def enc(p):
        return {"id": p.id, "name": p.name, "tag": p.tag, "material": p.material, "group": p.group, "step": 0,
                "explode": [0, 0, 0], "info": {}, "v": _b64(p.mesh.verts, "<f4"), "t": _b64(p.mesh.tris, "<u4"),
                "e": _b64(p.mesh.edges, "<u4")}
    t = m.tables
    hexc = t["classes"][1] if len(t["classes"]) > 1 else t["classes"][0]
    figures = {
        "panels": t["panels"], "sticks": t["stick_count"], "cuts": len(t["sticks"]), "boards": t["boards"],
        "bevel": bevel, "fold": 2 * bevel, "bevel_lo": t["bevel_lo"], "bevel_hi": t["bevel_hi"],
        "diameter_m": t["diameter_m"], "height_m": t["height_m"], "floor_m2": t["floor_m2"],
        "hex_side_m": hexc["sides_m"][1], "hex_base_m": hexc["sides_m"][0], "hex_count": hexc["count"],
        "tail": 90 - min(hexc["angles"]), "sheets": t["sheets"], "rings": t["rings"],
        "frequency": spec.frequency, "kinds": len(t["classes"]),
    }
    return {"pieces": [enc(p) for p in pieces], "prop": [enc(p) for p in loose], "figures": _clean(figures),
            "bench_at": BENCH_AT, "saw_at": SAW_AT, "bench_top": SH.BENCH_Z - M.D("deck_h_m"), "ground": -M.D("deck_h_m")}


# ----------------------------------------------------------------------
# Voices
# ----------------------------------------------------------------------

def voice(text: str, voice_name: str, rate: str = "+0%", pitch: str = "+0Hz") -> Path:
    import edge_tts
    key = hashlib.sha1(json.dumps([text, voice_name, rate, pitch]).encode("utf-8")).hexdigest()[:20]
    VOICE_CACHE.mkdir(parents=True, exist_ok=True)
    out = VOICE_CACHE / f"{key}.mp3"
    if out.exists() and out.stat().st_size > 0:
        return out
    tmp = out.with_suffix(".part")

    async def go(p):
        await edge_tts.Communicate(text, voice_name, rate=rate, pitch=p).save(str(tmp))
    # the service now and then answers with no audio; it nearly always works on a second try. Some
    # voices (Emma) refuse small pitch shifts for long stretches: the last tries use the voice's own
    # pitch, which nobody can hear the difference of, rather than leave the line silent.
    import time
    for attempt in range(6):
        try:
            asyncio.run(go(pitch if attempt < 3 else "+0Hz"))
            if tmp.exists() and tmp.stat().st_size > 0:
                break
        except Exception:
            if attempt == 5:
                raise
        time.sleep(0.8 * (attempt + 1))
    tmp.replace(out)
    return out


# ----------------------------------------------------------------------
# Recordings -> a release
# ----------------------------------------------------------------------

def _ffmpeg() -> str:
    """The project's own ffmpeg (two_v_demo.audio finds a current build); an old one on PATH
    cannot encode AAC without -strict."""
    try:
        from two_v_demo.audio import resolve_executable
        return resolve_executable("ffmpeg")
    except Exception:
        return "ffmpeg"


def _folder(meta: dict) -> tuple[Path, str]:
    """Where a take goes: a new numbered folder in the library, or a rehearsal folder in tmp/."""
    import medialib
    slug = meta.get("slug") or "take"
    slug = "".join(ch if ch.isalnum() or ch == "-" else "-" for ch in slug.lower()).strip("-") or "take"
    if meta.get("draft"):
        import time
        folder = ROOT / "tmp" / "sketch-claude-drafts" / f"{slug}-{time.strftime('%Y%m%d-%H%M%S')}"
        folder.mkdir(parents=True)
        return folder, f"{TAG}-{slug}"
    folder = medialib.new_folder(f"{TAG}-{slug}")
    return folder, folder.name.split("-", 1)[1]


def save_recording(webm: bytes, meta: dict) -> dict:
    """File a live recording (the browser's WebM) as a release."""
    folder, name = _folder(meta)
    src = folder / f"{name}-source.webm"
    src.write_bytes(webm)
    return _release(folder, name, ["-i", str(src), "-c:v", "libx264", "-pix_fmt", "yuv420p", "-crf", "18", "-preset", "medium",
                                   "-r", "30", "-c:a", "aac", "-b:a", "160k"], meta)


def _release(folder: Path, name: str, encode: list[str], meta: dict) -> dict:
    ff = _ffmpeg()
    land = folder / f"{name}.mp4"
    log = []

    def run(args):
        r = subprocess.run([ff, "-y", "-v", "error", *args], capture_output=True, text=True)
        if r.returncode:
            log.append(r.stderr[-400:])
        return r.returncode == 0

    run([*encode, "-movflags", "+faststart", str(land)])
    phone = folder / f"{name}-vertical.mp4"
    if land.exists():
        # the phone cut: the middle of the scope frame, filling the screen
        run(["-i", str(land), "-vf", "crop=ih*0.74*9/16:ih*0.74,scale=1080:1920", "-c:v", "libx264", "-pix_fmt", "yuv420p",
             "-crf", "20", "-c:a", "copy", "-movflags", "+faststart", str(phone)])
    if meta.get("srt"):
        (folder / f"{name}.srt").write_text(meta["srt"], encoding="utf-8")
    thumbs = []
    if land.exists():
        for i, sc in enumerate(meta.get("scenes", [])):
            t = max(0.0, float(sc.get("t", 0)) + 1.5)
            f = folder / f"thumb-{i + 1:02d}-{''.join(c if c.isalnum() else '-' for c in sc.get('name', 'scene').lower())[:40]}.jpg"
            if run(["-ss", f"{t:.2f}", "-i", str(land), "-frames:v", "1", "-q:v", "3", str(f)]):
                thumbs.append(f.name)
    desc = [f"# {meta.get('title', 'Dome Sketch take')}", "", meta.get("logline", ""), "",
            "## Chapters", ""]
    for sc in meta.get("scenes", []):
        sec = int(float(sc.get("t", 0)))
        desc.append(f"{sec // 60}:{sec % 60:02d} {sc.get('name', '')}")
    desc += ["", "## Cast", ""] + [f"- {c}" for c in meta.get("cast", [])]
    desc += ["", "## Copy", "", meta.get("copy", ""), "", meta.get("tags", ""), "",
             f"Made in Dome Sketch ({TAG}): the dome, its sticks and every figure spoken are the model's own. "
             "Voices are synthesised (Microsoft Edge TTS); the music is synthesised in the browser; the characters are original."]
    (folder / "description.md").write_text("\n".join(desc) + "\n", encoding="utf-8")
    if not meta.get("draft"):
        try:
            import medialib
            medialib.write_index()
        except Exception:
            pass
    return {"folder": folder.relative_to(ROOT).as_posix(), "video": land.relative_to(ROOT).as_posix() if land.exists() else None,
            "phone": phone.relative_to(ROOT).as_posix() if phone.exists() else None, "thumbs": thumbs, "errors": log}


# ----------------------------------------------------------------------
# The frame-accurate render: frames streamed straight into ffmpeg, the soundtrack muxed at the end
# ----------------------------------------------------------------------

RENDERS: dict[str, dict] = {}
FINISHED: list[dict] = []          # results of finished renders, newest last (a headless job waits on this)


def render_start(slug: str, fps: int, draft: bool) -> dict:
    import time
    rid = f"r{int(time.time() * 1000)}"
    work = ROOT / "tmp" / "sketch-claude-drafts" / f"work-{rid}"
    work.mkdir(parents=True)
    video = work / "frames.mp4"
    proc = subprocess.Popen([_ffmpeg(), "-y", "-v", "error", "-f", "image2pipe", "-framerate", str(fps), "-c:v", "mjpeg", "-i", "-",
                             "-c:v", "libx264", "-pix_fmt", "yuv420p", "-crf", "17", "-preset", "medium", str(video)],
                            stdin=subprocess.PIPE, stderr=subprocess.PIPE)
    import threading
    RENDERS[rid] = {"proc": proc, "work": work, "video": video, "frames": 0, "slug": slug, "draft": draft, "fps": fps,
                    "pending": {}, "lock": threading.Lock()}
    return {"id": rid}


def render_frame(rid: str, jpeg: bytes, n: int) -> dict:
    """Frames can arrive out of order (several are in flight); they go to ffmpeg in order."""
    r = RENDERS[rid]
    if r["proc"].poll() is not None:
        raise RuntimeError(f"ffmpeg stopped: {r['proc'].stderr.read().decode('utf-8', 'replace')[-300:]}")
    with r["lock"]:
        if n < r["frames"]:          # a resend of a frame already written
            return {"frames": r["frames"]}
        r["pending"][n] = jpeg
        while r["frames"] in r["pending"]:
            r["proc"].stdin.write(r["pending"].pop(r["frames"]))
            r["frames"] += 1
    return {"frames": r["frames"]}


def render_finish(rid: str, wav: bytes, meta: dict) -> dict:
    r = RENDERS.pop(rid)
    r["proc"].stdin.close()
    err = r["proc"].stderr.read().decode("utf-8", "replace")
    if r["proc"].wait() != 0 or not r["video"].exists():
        return {"error": f"the frames did not encode: {err[-300:]}"}
    audio = r["work"] / "soundtrack.wav"
    audio.write_bytes(wav)
    folder, name = _folder({**meta, "draft": r["draft"] or meta.get("draft")})
    out = _release(folder, name, ["-i", str(r["video"]), "-i", str(audio), "-c:v", "copy", "-c:a", "aac", "-b:a", "192k", "-shortest"],
                   {**meta, "draft": r["draft"]})
    out["frames"] = r["frames"]
    FINISHED.append(out)
    video_ok = out.get("video") and (ROOT / out["video"]).stat().st_size > 1000
    if video_ok:
        import shutil
        shutil.rmtree(r["work"], ignore_errors=True)
    else:
        # the frames and the soundtrack stay, so a failed encode never costs the render
        out["kept"] = r["work"].relative_to(ROOT).as_posix()
    return out


def render_abort(rid: str) -> dict:
    r = RENDERS.pop(rid, None)
    if r:
        try:
            r["proc"].stdin.close()
            r["proc"].kill()
        except Exception:
            pass
        import shutil
        shutil.rmtree(r["work"], ignore_errors=True)
    return {"aborted": bool(r)}


def render_headless(spec: M.Spec, draft: bool = False, port: int | None = None, timeout_s: float = 3 * 3600, episode: str = "s01e01") -> dict:
    """Render the episode in a headless Chrome this process starts, against a server this process
    hosts, so the render never depends on a window being visible (browsers throttle hidden pages)."""
    import base64
    import tempfile
    import threading
    import time
    from urllib.parse import quote
    from two_v_demo.book_export import _chrome_path
    from . import server as SV
    chrome = _chrome_path()
    if not chrome:
        raise RuntimeError("no Chrome or Edge found for the headless render")
    httpd = SV.serve(port or 0)
    threading.Thread(target=httpd.serve_forever, daemon=True).start()
    url = (f"http://127.0.0.1:{httpd.server_address[1]}/director?autorender=1&episode={episode}&draft={'1' if draft else '0'}"
           f"&spec={quote(json.dumps(spec.to_dict()))}")
    profile = tempfile.mkdtemp(prefix="sketch-claude-chrome-")
    before = len(FINISHED)
    proc = subprocess.Popen([chrome, "--headless=new", f"--user-data-dir={profile}", "--window-size=1920,1080",
                             "--autoplay-policy=no-user-gesture-required", "--mute-audio",
                             "--enable-gpu", "--ignore-gpu-blocklist", "--use-angle=d3d11", "--enable-unsafe-swiftshader",
                             "--disable-background-timer-throttling", "--disable-renderer-backgrounding",
                             "--enable-logging=stderr", "--v=0", url],
                            stdout=subprocess.DEVNULL, stderr=subprocess.PIPE, text=True, encoding="utf-8", errors="replace")
    gave_up = []

    def relay():
        for line in proc.stderr:
            if "[render" in line:
                msg = "[render" + line.split("[render", 1)[1].split('", source')[0].rstrip()
                print(msg, flush=True)
                if msg.startswith("[render-done]") and len(FINISHED) == before:
                    gave_up.append(msg)
    threading.Thread(target=relay, daemon=True).start()
    t0 = time.time()
    try:
        while len(FINISHED) == before:
            if proc.poll() is not None:
                raise RuntimeError("Chrome exited before the render finished")
            if gave_up:
                time.sleep(3)
                if len(FINISHED) == before:
                    raise RuntimeError("the page stopped the render; see the [render] lines above")
            if time.time() - t0 > timeout_s:
                raise RuntimeError("the render timed out")
            time.sleep(2)
        return FINISHED[-1]
    finally:
        proc.kill()
        httpd.shutdown()
