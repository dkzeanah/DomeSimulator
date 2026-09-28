"""My Voice: build a narration voice from your own videos, automatically.

Point it at videos (or audio, or folders of either) of yourself speaking.
It does the whole Local Voice Studio workflow without a single manual step:

1. **Pulls the audio** out of every file, cleaned up for speech (rumble cut,
   noise reduced, loudness levelled), and skips files it has already seen or
   whose audio duplicates one it has.
2. **Cuts it into sentences** and **transcribes** them locally
   (faster-whisper), dropping anything that is not speech.
3. **Finds your voice.** Every clip gets a speaker fingerprint; the clips
   that cluster together are you, and clips of somebody else, or of music,
   fall outside the cluster and are set aside.
4. **Measures your voice's characteristics** -- pitch, range, speaking rate,
   loudness, brightness -- into a voice card.
5. **Builds the voice.** The cleanest 10-15 seconds become the reference;
   the speaker fingerprints of *every* accepted clip are averaged into the
   voice's identity, which is what makes more recordings make it stronger
   rather than just longer. A calibration sentence is spoken both ways and
   the one that sounds more like you (measured, not guessed) is kept, and
   its speaking rate is matched to yours.
6. **Makes it the default.** From then on every film the exporter renders
   is narrated in your voice, locally, unless you switch back.

Run it again with more recordings any time: they are added to the pool and
the voice is rebuilt from everything so far.

    py -m local_voice_studio.my_voice build "H:/videos/a.mp4" "H:/videos/folder" --i-own-this-voice
    py -m local_voice_studio.my_voice status
    py -m local_voice_studio.my_voice say "Testing, one two three."
    py -m local_voice_studio.my_voice default mine|andrew

(Use the ``.venv-voice`` Python for everything except ``status`` and
``default``; the launcher's My Voice page does this for you.)

Everything stays on this computer, in ``my_voice/`` (not committed: it is
your voice). Every generated file is marked synthetic and carries the
model's watermark.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import math
import os
import re
import subprocess
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
HOME = ROOT / "my_voice"
PROJECT_DIR = HOME / "project"
SETTINGS = HOME / "default_voice.json"
LEDGER = HOME / "sources.json"
STATUS = HOME / "status.json"
EMBEDDINGS = HOME / "embeddings.npz"
SAMPLES = HOME / "samples"
VENV_PYTHON = ROOT / ".venv-voice" / "Scripts" / "python.exe"

MEDIA = {".mp4", ".mov", ".mkv", ".webm", ".m4v", ".avi", ".wav", ".mp3", ".m4a",
         ".aac", ".flac", ".ogg", ".opus"}
CLEAN_FILTER = "highpass=f=70,afftdn=nf=-25,loudnorm=I=-20:TP=-2:LRA=11"
CALIBRATION = ("Every member of this dome starts as a wedge, ripped from a log with a "
               "chainsaw. Three of them make a triangle, and forty triangles make the frame.")
REFERENCE_SECONDS = 14.0     # Turbo reads 15 s of prompt tokens and 10 s of voice features
TEMPO_LIMITS = (0.85, 1.15)  # beyond this, stretching sounds processed


def log(message: str) -> None:
    print(message, flush=True)


def _now() -> str:
    return time.strftime("%Y-%m-%d %H:%M:%S")


def _read(path: Path, default):
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return default


def _write(path: Path, payload) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    scratch = path.with_suffix(path.suffix + ".tmp")
    scratch.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")
    os.replace(scratch, path)


# ----------------------------------------------------------------------
# The default voice (read by the film exporter; no heavy imports)
# ----------------------------------------------------------------------

def default_voice() -> dict:
    """``{"engine": "mine", ...}`` when your voice is built and chosen, else Andrew."""
    settings = _read(SETTINGS, {})
    status = _read(STATUS, {})
    if settings.get("engine") == "mine" and status.get("profile_dir") and \
            (HOME / status["profile_dir"] / "profile.json").is_file():
        return {"engine": "mine", "profile": status.get("profile_id", ""),
                "label": f"My voice ({status.get('profile_id', '')})"}
    return {"engine": "andrew", "label": "Andrew (Microsoft online neural voice)"}


def set_default(engine: str) -> dict:
    if engine not in ("mine", "andrew"):
        raise ValueError("engine must be 'mine' or 'andrew'")
    if engine == "mine" and not _read(STATUS, {}).get("profile_dir"):
        raise RuntimeError("No voice built yet: run 'build' with your recordings first")
    _write(SETTINGS, {"engine": engine, "changed_at": _now()})
    return default_voice()


# ----------------------------------------------------------------------
# Step 1: sources -> cleaned audio, with duplicates caught
# ----------------------------------------------------------------------

def expand(paths) -> list[Path]:
    out: list[Path] = []
    for raw in paths:
        p = Path(str(raw).strip().strip('"'))
        if not str(p).strip():
            continue
        if p.is_dir():
            out.extend(sorted(q for q in p.iterdir() if q.suffix.lower() in MEDIA))
        elif p.is_file() and p.suffix.lower() in MEDIA:
            out.append(p)
        else:
            log(f"  skipped (not a media file or folder): {p}")
    seen, unique = set(), []
    for p in out:
        key = str(p.resolve()).lower()
        if key not in seen:
            seen.add(key)
            unique.append(p)
    return unique


def _file_id(path: Path) -> str:
    """Size, date and the first and last megabyte: fast on a slow drive, and
    different for any two different recordings."""
    st = path.stat()
    h = hashlib.sha256(f"{st.st_size}".encode())
    with path.open("rb") as handle:
        h.update(handle.read(1 << 20))
        if st.st_size > (2 << 20):
            handle.seek(-(1 << 20), os.SEEK_END)
            h.update(handle.read(1 << 20))
    return h.hexdigest()[:16]


def _envelope(wav_path: Path):
    import numpy as np
    import soundfile as sf

    audio, sr = sf.read(str(wav_path), dtype="float32")
    hop = sr // 10
    n = len(audio) // hop
    if n < 20:
        return None
    frames = audio[: n * hop].reshape(n, hop)
    env = np.sqrt((frames ** 2).mean(axis=1) + 1e-9)
    env = np.log(env)
    return (env - env.mean()) / (env.std() + 1e-9)


def _duplicate_of(env, known: dict) -> str:
    """The id of an already-imported recording with the same audio, if any."""
    import numpy as np

    if env is None:
        return ""
    for other_id, other in known.items():
        if other is None:
            continue
        n = min(len(env), len(other))
        if n < 50 or abs(len(env) - len(other)) > max(20, 0.02 * n):
            continue
        if float(np.corrcoef(env[:n], other[:n])[0, 1]) > 0.97:
            return other_id
    return ""


def ffmpeg() -> str:
    """A modern ffmpeg. The one on PATH here is deliberately ancient (old films
    re-render byte for byte through it) and lacks the denoise and loudness
    filters, so the voice environment's bundled 7.x build is preferred."""
    try:
        import imageio_ffmpeg
        return imageio_ffmpeg.get_ffmpeg_exe()
    except Exception:
        from .audio_tools import find_ffmpeg
        return find_ffmpeg()


def extract(source: Path, destination: Path) -> Path:
    destination.parent.mkdir(parents=True, exist_ok=True)
    subprocess.run([ffmpeg(), "-y", "-v", "error", "-i", str(source), "-vn",
                    "-af", CLEAN_FILTER, "-ac", "1", "-ar", "24000", "-c:a", "pcm_s16le",
                    str(destination)], check=True, capture_output=True)
    return destination


# ----------------------------------------------------------------------
# The whole build
# ----------------------------------------------------------------------

def _project(speaker: str, owner_confirmed: bool):
    from .models import ConsentRecord
    from .project import VoiceProject

    if (PROJECT_DIR / "project.json").is_file():
        project = VoiceProject.open(PROJECT_DIR)
    else:
        project = VoiceProject.create(PROJECT_DIR, "My voice", speaker)
    if not project.consented:
        if not owner_confirmed:
            raise PermissionError(
                "Confirm these are recordings of your own voice that you may use "
                "(the launcher checkbox, or --i-own-this-voice).")
        project.save_consent(ConsentRecord(speaker_name=speaker, voice_owner_confirmed=True,
                                           authorized_use_confirmed=True,
                                           anti_deception_confirmed=True))
    return project


def import_sources(project, sources: list[Path]) -> list[str]:
    """New recordings -> cleaned audio -> sentence clips. Returns the new clip ids."""
    from .audio_tools import create_clip_record, energy_segments, read_pcm16_mono, \
        write_pcm16_mono

    ledger = _read(LEDGER, {})
    envelopes = {}
    for sid, entry in ledger.items():
        wav = PROJECT_DIR / "normalized" / f"{sid}.wav"
        if entry.get("status") == "imported" and wav.is_file():
            envelopes[sid] = _envelope(wav)
    new_clips: list[str] = []
    clips = {c.clip_id: c for c in project.load_clips()}
    for index, source in enumerate(sources, start=1):
        sid = _file_id(source)
        tag = f"[{index}/{len(sources)}] {source.name}"
        known = ledger.get(sid, {})
        if known.get("status") in ("imported", "duplicate"):
            same = Path(known.get("path", "")).name
            log(f"{tag}: already used" + (f" (identical to {same})" if same != source.name else ""))
            continue
        wav = PROJECT_DIR / "normalized" / f"{sid}.wav"
        try:
            extract(source, wav)
        except subprocess.CalledProcessError as exc:
            detail = (exc.stderr or b"").decode("utf-8", "replace").strip().splitlines()
            log(f"{tag}: no usable audio ({detail[-1] if detail else 'ffmpeg failed'})")
            ledger[sid] = {"path": str(source), "status": "no audio", "at": _now()}
            continue
        env = _envelope(wav)
        dup = _duplicate_of(env, envelopes)
        if dup:
            log(f"{tag}: same audio as {Path(ledger[dup]['path']).name}; not counted twice")
            ledger[sid] = {"path": str(source), "status": "duplicate", "duplicate_of": dup,
                           "at": _now()}
            wav.unlink(missing_ok=True)
            continue
        envelopes[sid] = env
        rate, samples = read_pcm16_mono(wav)
        segments = energy_segments(wav, threshold_dbfs=-42.0, min_seconds=2.5,
                                   max_seconds=14.0)
        made = 0
        for n, (a, b) in enumerate(segments, start=1):
            clip_id = f"{sid[:8]}-{n:03d}"
            path = PROJECT_DIR / "clips" / f"{clip_id}.wav"
            write_pcm16_mono(path, rate, samples[a:b])
            clips[clip_id] = create_clip_record(project, path, clip_id, source_id=sid)
            new_clips.append(clip_id)
            made += 1
        seconds = len(samples) / rate
        ledger[sid] = {"path": str(source), "status": "imported", "seconds": seconds,
                       "clips": made, "at": _now()}
        log(f"{tag}: {seconds:.0f} s of audio -> {made} sentence clips")
        _write(LEDGER, ledger)
    project.save_clips(clips.values())
    _write(LEDGER, ledger)
    return new_clips


def transcribe(project, clip_ids: list[str]) -> dict:
    """Local Whisper on the new clips; marks non-speech. Returns {clip: speech?}."""
    if not clip_ids:
        return {}
    from faster_whisper import WhisperModel

    from .backends import detect_hardware

    device = "cuda" if detect_hardware().cuda_available else "cpu"
    log(f"Transcribing {len(clip_ids)} clips on {device} (local Whisper)...")
    model = WhisperModel("small.en", device=device,
                         compute_type="float16" if device == "cuda" else "int8")
    clips = {c.clip_id: c for c in project.load_clips()}
    speech = {}
    for n, cid in enumerate(clip_ids, start=1):
        clip = clips[cid]
        segments, _info = model.transcribe(str(project.resolve_relative(clip.audio_file)),
                                           beam_size=5, vad_filter=False,
                                           condition_on_previous_text=False)
        segments = list(segments)
        text = " ".join(s.text.strip() for s in segments).strip()
        no_speech = (sum(s.no_speech_prob for s in segments) / len(segments)) if segments else 1.0
        clip.text = text
        speech[cid] = bool(text) and no_speech < 0.6 and len(text.split()) >= 3
        if n % 25 == 0:
            log(f"  transcribed {n}/{len(clip_ids)}")
    project.save_clips(clips.values())
    del model
    _free_gpu()
    return speech


def _free_gpu() -> None:
    try:
        import gc

        import torch
        gc.collect()
        if torch.cuda.is_available():
            torch.cuda.empty_cache()
    except Exception:
        pass


_MODEL = None


def model():
    """Chatterbox Turbo, from the local cache only."""
    global _MODEL
    if _MODEL is None:
        os.environ.setdefault("HF_HUB_OFFLINE", "1")
        os.environ.setdefault("TRANSFORMERS_OFFLINE", "1")
        os.environ.setdefault("TQDM_DISABLE", "1")   # per-sentence progress bars flood the log
        import torch
        from chatterbox.tts_turbo import ChatterboxTurboTTS

        device = "cuda" if torch.cuda.is_available() else "cpu"
        log(f"Loading the voice model on {device}...")
        _MODEL = ChatterboxTurboTTS.from_pretrained(device=device)
    return _MODEL


def _load16k(path: Path):
    import librosa

    wav, _ = librosa.load(str(path), sr=16000)
    return wav


def fingerprints(project) -> dict:
    """Speaker embedding for every clip, cached across builds."""
    import numpy as np

    cached = {}
    if EMBEDDINGS.is_file():
        data = np.load(EMBEDDINGS)
        cached = {k: data[k] for k in data.files}
    clips = project.load_clips()
    todo = [c for c in clips if c.clip_id not in cached]
    if todo:
        log(f"Fingerprinting {len(todo)} clips...")
        ve = model().ve
        for c in todo:
            emb = ve.embeds_from_wavs([_load16k(project.resolve_relative(c.audio_file))],
                                      sample_rate=16000)
            v = np.asarray(emb, dtype="float32").reshape(-1)
            cached[c.clip_id] = v / (np.linalg.norm(v) + 1e-9)
        np.savez(EMBEDDINGS, **cached)
    return cached


def find_me(embeddings: dict, candidates: list[str]) -> tuple:
    """The dominant speaker's centre, and each clip's similarity to it."""
    import numpy as np

    ids = [c for c in candidates if c in embeddings]
    if not ids:
        return None, {}, 0.0
    matrix = np.stack([embeddings[c] for c in ids])
    centre = np.median(matrix, axis=0)
    for _ in range(3):
        centre /= np.linalg.norm(centre) + 1e-9
        sims = matrix @ centre
        keep = sims >= np.quantile(sims, 0.30)
        centre = matrix[keep].mean(axis=0)
    centre /= np.linalg.norm(centre) + 1e-9
    sims = matrix @ centre
    median = float(np.median(sims))
    mad = float(np.median(np.abs(sims - median)))
    threshold = max(0.70, median - 3.0 * 1.4826 * mad)
    return centre, dict(zip(ids, (float(s) for s in sims))), threshold


def characteristics(project, clip_ids: list[str]) -> dict:
    """Your voice, measured: pitch, range, rate, loudness, brightness."""
    import librosa
    import numpy as np

    clips = {c.clip_id: c for c in project.load_clips()}
    chosen = sorted(clip_ids)[:: max(1, len(clip_ids) // 40)][:40]
    f0s, cents, words, seconds, rms = [], [], 0, 0.0, []
    for cid in chosen:
        c = clips[cid]
        y, sr = librosa.load(str(project.resolve_relative(c.audio_file)), sr=16000)
        f0, voiced, _p = librosa.pyin(y, fmin=60, fmax=320, sr=sr, frame_length=1024)
        f0s.extend(f0[voiced & np.isfinite(f0)].tolist())
        cents.append(float(np.median(librosa.feature.spectral_centroid(y=y, sr=sr))))
        rms.append(c.rms_dbfs)
    for cid in clip_ids:
        c = clips[cid]
        words += len(c.text.split())
        seconds += c.duration_s
    f0s = np.asarray(f0s) if f0s else np.asarray([float("nan")])
    median = float(np.nanmedian(f0s))
    p10, p90 = (float(np.nanpercentile(f0s, q)) for q in (10, 90))
    return {
        "pitch_median_hz": median,
        "pitch_p10_hz": p10, "pitch_p90_hz": p90,
        "pitch_range_semitones": 12 * math.log2(p90 / p10) if p10 > 0 else float("nan"),
        "speaking_rate_wpm": 60.0 * words / seconds if seconds else float("nan"),
        "loudness_dbfs": float(np.median(rms)) if rms else float("nan"),
        "brightness_hz": float(np.median(cents)) if cents else float("nan"),
        "clips_measured_for_pitch": len(chosen),
    }


def _speech_rate(path: Path, text: str) -> float:
    """Words per minute of a generated file, leading and trailing silence trimmed."""
    import librosa

    y, sr = librosa.load(str(path), sr=16000)
    trimmed, _ = librosa.effects.trim(y, top_db=40)
    return 60.0 * len(text.split()) / max(0.5, len(trimmed) / sr)


def _similarity(path: Path, centre) -> float:
    import numpy as np

    emb = np.asarray(model().ve.embeds_from_wavs([_load16k(path)], sample_rate=16000)).reshape(-1)
    return float(emb @ centre / (np.linalg.norm(emb) + 1e-9))


def build_voice(project, accepted: list[str], sims: dict, centre, card: dict) -> dict:
    """Reference from the cleanest clips; identity averaged over all of them."""
    import librosa
    import numpy as np
    import torch
    from chatterbox.tts_turbo import Conditionals

    from .audio_tools import build_voice_profile

    clips = {c.clip_id: c for c in project.load_clips()}
    # The reference: short, clean, most like you.
    pool = [clips[c] for c in accepted if 4.0 <= clips[c].duration_s <= 12.0
            and clips[c].silence_pct < 25.0 and not clips[c].quality_issues]
    pool.sort(key=lambda c: -sims[c.clip_id])
    reference, total = [], 0.0
    for c in pool:
        if total >= REFERENCE_SECONDS:
            break
        reference.append(c)
        total += c.duration_s
    if total < 6.0:
        raise RuntimeError(f"Only {total:.1f} s of clean reference speech; add more recordings")
    for c in reference:
        c.status = "accepted"
    profile = build_voice_profile(project, "my-voice", reference, target_seconds=1e9)
    profile_dir = project.resolve_relative(f"profiles/{profile.profile_id}")
    reference_wav = profile_dir / "reference.wav"

    tts = model()
    log("Building the voice from the reference...")
    tts.prepare_conditionals(str(reference_wav))
    plain = tts.conds
    plain.save(profile_dir / "conds_reference.pt")

    # Strengthen: the identity vectors averaged over every accepted clip.
    log(f"Strengthening the identity from all {len(accepted)} accepted clips...")
    ve = np.stack([np.asarray(fingerprint, dtype="float32") for fingerprint in
                   (_fingerprint_cache()[c] for c in accepted)])
    ve_mean = ve.mean(axis=0)
    ve_mean /= np.linalg.norm(ve_mean) + 1e-9
    xvecs = []
    step = max(1, len(accepted) // 60)
    for cid in accepted[::step][:60]:
        y, _ = librosa.load(str(project.resolve_relative(clips[cid].audio_file)), sr=24000)
        ref = tts.s3gen.embed_ref(y, 24000, device=tts.device)
        xvecs.append(ref["embedding"].detach().float().cpu())
    strong = Conditionals.load(profile_dir / "conds_reference.pt", map_location="cpu")
    strong.t3.speaker_emb = torch.from_numpy(ve_mean).reshape(1, -1).to(strong.t3.speaker_emb.dtype)
    strong.gen["embedding"] = torch.stack(xvecs).mean(dim=0).to(strong.gen["embedding"].dtype)
    strong.save(profile_dir / "conds_strong.pt")

    # Calibrate: which sounds more like you, and how fast does it talk?
    SAMPLES.mkdir(parents=True, exist_ok=True)
    scores = {}
    for name in ("reference", "strong"):
        tts.conds = Conditionals.load(profile_dir / f"conds_{name}.pt").to(tts.device)
        out = SAMPLES / f"calibration-{profile.profile_id}-{name}.wav"
        _generate_to(tts, CALIBRATION, out, tempo=1.0)
        scores[name] = {"similarity": _similarity(out, centre),
                        "rate_wpm": _speech_rate(out, CALIBRATION), "sample": out.name}
        log(f"  {name}: sounds {scores[name]['similarity']:.3f} like you, "
            f"{scores[name]['rate_wpm']:.0f} words/min")
    active = max(scores, key=lambda k: scores[k]["similarity"])
    target = card["speaking_rate_wpm"]
    tempo = 1.0
    if math.isfinite(target) and scores[active]["rate_wpm"] > 0:
        tempo = min(TEMPO_LIMITS[1], max(TEMPO_LIMITS[0], target / scores[active]["rate_wpm"]))
    voice = {"profile_id": profile.profile_id,
             "profile_dir": str(profile_dir.relative_to(HOME)).replace("\\", "/"),
             "profile_sha256": profile.sha256, "active_conds": f"conds_{active}.pt",
             "tempo": tempo, "calibration": scores,
             "reference_clips": [c.clip_id for c in reference],
             "reference_seconds": total}
    tts.conds = Conditionals.load(profile_dir / voice["active_conds"]).to(tts.device)
    final = SAMPLES / f"sample-{profile.profile_id}.wav"
    # The sample wears your current tweaks; the raw take is kept so trying
    # other tweaks later needs no new speech.
    _generate_to(tts, CALIBRATION, final, tempo, tweaks(),
                 keep_raw=SAMPLES / f"raw-{profile.profile_id}.wav")
    voice["sample"] = final.name
    return voice


_FP = None


def _fingerprint_cache() -> dict:
    global _FP
    if _FP is None:
        import numpy as np
        data = np.load(EMBEDDINGS)
        _FP = {k: data[k] for k in data.files}
    return _FP


def build(sources, speaker: str = "Donovan Zeanah", owner_confirmed: bool = False,
          make_default: bool = True) -> dict:
    """Scan recordings, keep your voice, rebuild the profile from everything so far."""
    global _FP
    started = time.time()
    project = _project(speaker, owner_confirmed)
    files = expand(sources)
    log(f"{len(files)} recordings given; {len(_read(LEDGER, {}))} already known")
    new = import_sources(project, files)
    speech = transcribe(project, new)

    clips = {c.clip_id: c for c in project.load_clips()}
    embeddings = fingerprints(project)
    _FP = embeddings
    candidates = [cid for cid, c in clips.items()
                  if c.text.strip() and speech.get(cid, c.rejection_reason != "not speech")]
    centre, sims, threshold = find_me(embeddings, candidates)
    if centre is None:
        raise RuntimeError("No speech found in these recordings")
    accepted, other, quality = [], 0, 0
    for cid, c in clips.items():
        if cid in new and not speech.get(cid, False):
            c.status, c.rejection_reason = "rejected", "not speech"
            continue
        if cid not in sims:
            continue
        issues = [i for i in c.quality_issues if i not in ("too long",)]
        if sims[cid] < threshold:
            c.status, c.rejection_reason = "rejected", f"another voice ({sims[cid]:.2f})"
            other += 1
        elif issues:
            c.status, c.rejection_reason = "rejected", "; ".join(issues)
            quality += 1
        else:
            c.status, c.rejection_reason = "accepted", ""
            accepted.append(cid)
    project.save_clips(clips.values())
    minutes = sum(clips[c].duration_s for c in accepted) / 60.0
    log(f"Your voice: {len(accepted)} clips, {minutes:.1f} minutes "
        f"(set aside: {other} another voice or noise, {quality} quality)")
    if len(accepted) < 3:
        raise RuntimeError("Too little clean speech of one voice; add more recordings")
    np_centre = centre
    card = characteristics(project, accepted)
    log(f"Voice card: pitch {card['pitch_median_hz']:.0f} Hz "
        f"({card['pitch_p10_hz']:.0f}-{card['pitch_p90_hz']:.0f}), "
        f"{card['speaking_rate_wpm']:.0f} words/min, brightness {card['brightness_hz']:.0f} Hz")
    voice = build_voice(project, accepted, sims, np_centre, card)
    try:
        from .backends import export_f5_dataset
        export_f5_dataset(project, PROJECT_DIR / "runs" / "f5-dataset")
    except Exception as exc:  # the fine-tune export is a bonus, never a failure
        log(f"  (fine-tune dataset not exported: {exc})")
    ledger = _read(LEDGER, {})
    status = {
        **voice, "built_at": _now(), "speaker": speaker,
        "recordings": sum(1 for e in ledger.values() if e.get("status") == "imported"),
        "duplicates_skipped": sum(1 for e in ledger.values() if e.get("status") == "duplicate"),
        "clips_total": len(clips), "clips_accepted": len(accepted),
        "minutes_accepted": minutes, "similarity_threshold": threshold,
        "characteristics": card, "build_seconds": time.time() - started,
    }
    _write(STATUS, status)
    _write(HOME / "voice_card.json", card)
    if make_default:
        set_default("mine")
        log("Your voice is now the default narrator for every film.")
    log(f"Done in {status['build_seconds'] / 60:.1f} min. Listen: {SAMPLES / voice['sample']}")
    return status


# ----------------------------------------------------------------------
# Shaping the sound: pitch, body, pace, tone
# ----------------------------------------------------------------------

TWEAKS = HOME / "tweaks.json"
TWEAK_LIMITS = {
    # name: (lowest, highest, neutral, what it does)
    "pitch_semitones": (-7.0, 7.0, 0.0, "pitch up or down; the voice's size stays put"),
    "body_semitones": (-4.0, 4.0, 0.0, "negative = deeper, fuller chest; positive = "
                                       "lighter, smaller -- pitch stays put"),
    "speed": (0.75, 1.30, 1.0, "speaking rate, on top of the pace matched to yours"),
    "low_cut_hz": (0.0, 400.0, 0.0, "remove rumble and boom below this (0 = off)"),
    "high_cut_hz": (0.0, 16000.0, 0.0, "remove hiss and sparkle above this (0 = off)"),
    "bass_db": (-12.0, 12.0, 0.0, "low-end warmth, a shelf around 120 Hz"),
    "treble_db": (-12.0, 12.0, 0.0, "high-end clarity, a shelf around 5 kHz"),
}
TWEAK_PRESETS = {
    "natural": {},
    "deeper": {"pitch_semitones": -1.5, "body_semitones": -1.0, "bass_db": 3.0},
    "fuller": {"body_semitones": -1.5, "bass_db": 4.0, "treble_db": -1.0},
    "brighter": {"body_semitones": 0.5, "treble_db": 4.0, "low_cut_hz": 90.0},
    "higher": {"pitch_semitones": 2.0, "body_semitones": 0.5},
    "warm narrator": {"body_semitones": -0.7, "bass_db": 2.5, "treble_db": 1.5,
                      "low_cut_hz": 60.0, "speed": 0.96},
    "radio": {"low_cut_hz": 300.0, "high_cut_hz": 3400.0, "treble_db": 2.0},
}


def tweaks() -> dict:
    """The current shaping, every value clamped to its range."""
    stored = _read(TWEAKS, {})
    out = {}
    for name, (lo, hi, neutral, _what) in TWEAK_LIMITS.items():
        try:
            value = float(stored.get(name, neutral))
        except (TypeError, ValueError):
            value = neutral
        out[name] = min(hi, max(lo, value))
    return out


def set_tweaks(changes: dict | None = None, preset: str = "") -> dict:
    """Change some settings (or start from a preset) and save them."""
    base = {name: spec[2] for name, spec in TWEAK_LIMITS.items()}
    if preset:
        if preset not in TWEAK_PRESETS:
            raise ValueError(f"no preset {preset!r}; there are {', '.join(TWEAK_PRESETS)}")
        base.update(TWEAK_PRESETS[preset])
    else:
        base.update(tweaks())
    for name, value in (changes or {}).items():
        if name not in TWEAK_LIMITS:
            raise ValueError(f"no setting {name!r}; there are {', '.join(TWEAK_LIMITS)}")
        base[name] = float(value)
    _write(TWEAKS, base)
    return tweaks()


def _tweak_key(tw: dict) -> str:
    return ",".join(f"{k}={tw[k]:.3f}" for k in sorted(tw))


def _atempo(factor: float) -> list[str]:
    chain = []
    while factor > 2.0:
        chain.append("atempo=2.0")
        factor /= 2.0
    while factor < 0.5:
        chain.append("atempo=0.5")
        factor /= 0.5
    if abs(factor - 1.0) > 1e-3:
        chain.append(f"atempo={factor:.5f}")
    return chain


def shape(audio, sample_rate: int, out: Path, tempo: float = 1.0, tw: dict | None = None) -> Path:
    """Apply the pace match and every tweak, and write ``out``.

    Pitch uses the Rap Studio's TD-PSOLA (:func:`autotune.shift_semitones`),
    which moves pitch periods rather than resampling, so the voice does not
    turn into a chipmunk. *Body* is the reverse trick: resample (which moves
    the vocal-tract resonances with everything else), then put the pitch
    back with PSOLA and the length back with the tempo -- leaving only the
    resonances moved, which is what makes a voice sound bigger or smaller.
    """
    import numpy as np
    import soundfile as sf

    tw = tw or tweaks()
    y = np.asarray(audio, dtype=np.float32)
    ratio = 2.0 ** (tw["body_semitones"] / 12.0)
    pitch = tw["pitch_semitones"]
    if abs(tw["body_semitones"]) > 0.01:
        import librosa
        y = librosa.resample(y, orig_sr=sample_rate, target_sr=int(round(sample_rate / ratio)))
        pitch -= tw["body_semitones"]
    else:
        ratio = 1.0
    if abs(pitch) > 0.01:
        from .autotune import shift_semitones
        y = shift_semitones(y, sample_rate, pitch)
    filters = _atempo(tempo * tw["speed"] / ratio)
    if tw["low_cut_hz"] > 0:
        filters.append(f"highpass=f={tw['low_cut_hz']:.0f}:poles=2")
    if tw["high_cut_hz"] > 0:
        filters.append(f"lowpass=f={tw['high_cut_hz']:.0f}:poles=2")
    if abs(tw["bass_db"]) > 0.05:
        filters.append(f"bass=g={tw['bass_db']:.2f}:f=120:w=0.7")
    if abs(tw["treble_db"]) > 0.05:
        filters.append(f"treble=g={tw['treble_db']:.2f}:f=5000:w=0.7")
    if tw["bass_db"] > 0.05 or tw["treble_db"] > 0.05:
        filters.append("alimiter=limit=0.95:level=disabled")
    out.parent.mkdir(parents=True, exist_ok=True)
    if not filters:
        sf.write(str(out), y, sample_rate, subtype="PCM_16")
        return out
    raw = out.with_suffix(".unshaped.wav")
    sf.write(str(raw), y, sample_rate, subtype="PCM_16")
    subprocess.run([ffmpeg(), "-y", "-v", "error", "-i", str(raw), "-af", ",".join(filters),
                    "-ar", str(sample_rate), "-c:a", "pcm_s16le", str(out)],
                   check=True, capture_output=True)
    raw.unlink(missing_ok=True)
    return out


def preview(out: Path | None = None) -> Path:
    """The calibration sentence with the current tweaks -- no new speech needed
    once the raw sample exists, so trying settings takes a second."""
    import soundfile as sf

    status = _read(STATUS, {})
    if not status.get("profile_dir"):
        raise RuntimeError("No voice built yet: run 'build' first")
    raw = SAMPLES / f"raw-{status['profile_id']}.wav"
    if not raw.is_file():
        voice = Voice()
        voice.speak_raw(CALIBRATION, raw)
    audio, sr = sf.read(str(raw), dtype="float32")
    out = out or SAMPLES / f"preview-{time.strftime('%H%M%S')}.wav"
    shape(audio, sr, out, float(status.get("tempo", 1.0)))
    return out


# ----------------------------------------------------------------------
# Speaking
# ----------------------------------------------------------------------

def _chunks(text: str, limit: int = 240) -> list[str]:
    sentences = re.split(r"(?<=[.!?;:])\s+", " ".join(text.split()))
    out, current = [], ""
    for s in sentences:
        if current and len(current) + len(s) + 1 > limit:
            out.append(current)
            current = s
        else:
            current = f"{current} {s}".strip()
    if current:
        out.append(current)
    return out or [text]


def _speak_array(tts, text: str):
    """Speak ``text`` sentence group by group, joined and trimmed, unshaped."""
    import numpy as np

    pieces = []
    gap = np.zeros(int(tts.sr * 0.22), dtype="float32")
    for chunk in _chunks(text):
        wav = tts.generate(chunk).squeeze(0).numpy().astype("float32")
        # Trim the model's trailing breath/silence per chunk.
        loud = np.where(np.abs(wav) > 10 ** (-45 / 20))[0]
        if loud.size:
            wav = wav[max(0, loud[0] - 240): loud[-1] + 2400]
        pieces.extend([wav, gap])
    return np.concatenate(pieces[:-1]) if pieces else np.zeros(1, "float32")


NEUTRAL = {name: spec[2] for name, spec in TWEAK_LIMITS.items()}


def _generate_to(tts, text: str, out: Path, tempo: float, tw: dict | None = None,
                 keep_raw: Path | None = None) -> Path:
    """Speak ``text``, then match your pace and apply the tweaks (neutral if none)."""
    import soundfile as sf

    audio = _speak_array(tts, text)
    if keep_raw is not None:
        keep_raw.parent.mkdir(parents=True, exist_ok=True)
        sf.write(str(keep_raw), audio, tts.sr, subtype="PCM_16")
    return shape(audio, tts.sr, out, tempo, tw or NEUTRAL)


class Voice:
    """Your built voice, loaded once, ready to speak."""

    def __init__(self):
        status = _read(STATUS, {})
        if not status.get("profile_dir"):
            raise RuntimeError("No voice built yet: run 'build' first")
        from chatterbox.tts_turbo import Conditionals

        self.status = status
        self.tts = model()
        conds = HOME / status["profile_dir"] / status["active_conds"]
        self.tts.conds = Conditionals.load(conds).to(self.tts.device)
        self.tempo = float(status.get("tempo", 1.0))
        self.tweaks = tweaks()
        # Any change to the voice or its shaping invalidates cached narration.
        self.key = hashlib.sha256(
            f"{status['profile_sha256']}|{status['active_conds']}|{self.tempo:.4f}|"
            f"{_tweak_key(self.tweaks)}".encode()).hexdigest()[:16]

    def speak_raw(self, text: str, out: Path) -> Path:
        """Unshaped speech (no pace match, no tweaks): what previews start from."""
        return _generate_to(self.tts, text, out, 1.0, NEUTRAL)

    def say(self, text: str, out: Path) -> Path:
        _generate_to(self.tts, text, out, self.tempo, self.tweaks)
        _write(out.with_suffix(out.suffix + ".json"), {
            "schema": 1, "synthetic_voice": True, "generated_at": _now(),
            "backend": "chatterbox-turbo", "voice": self.status["profile_id"],
            "voice_key": self.key, "tempo": self.tempo, "tweaks": self.tweaks,
            "text": text, "watermark": "preserved model-provided watermark"})
        return out


def narrate(script_path: Path, out_dir: Path) -> Path:
    """A film's chapters in your voice, as a narration plan the exporter plays."""
    import soundfile as sf

    from two_v_demo.audio import SPEECH_DELAY, TAIL_PADDING, _build_mixed_track, \
        resolve_executable

    script = _read(script_path, None)
    if not script:
        raise ValueError(f"unreadable narration script: {script_path}")
    voice = Voice()
    out_dir.mkdir(parents=True, exist_ok=True)
    chapters = script["chapters"]
    clip_paths, speech = [], []
    for i, ch in enumerate(chapters):
        clip = out_dir / f"chapter_{i + 1:03d}.wav"
        side = _read(clip.with_suffix(".wav.json"), {})
        if clip.is_file() and side.get("text") == ch["text"] and side.get("voice_key") == voice.key:
            log(f"Chapter {i + 1}/{len(chapters)}: cached")
        else:
            log(f"Chapter {i + 1}/{len(chapters)}: {ch.get('title', '')}")
            voice.say(ch["text"], clip)
        info = sf.info(str(clip))
        clip_paths.append(clip)
        speech.append(info.frames / info.samplerate)
    durations = [max(float(ch["duration"]), SPEECH_DELAY + s + TAIL_PADDING)
                 for ch, s in zip(chapters, speech)]
    starts, cursor = [], 0.0
    for d in durations:
        starts.append(cursor)
        cursor += d
    track = out_dir / "narration.m4a"
    log("Assembling the narration track...")
    _build_mixed_track(clip_paths, starts, cursor, track, resolve_executable("ffmpeg"), log)
    plan = out_dir / "narration-plan.json"
    _write(plan, {
        "schema": 1, "synthetic_voice": True, "generated_at": _now(),
        "lesson": script.get("lesson", ""), "chapter_count": len(chapters),
        "voice_profile": voice.status["profile_id"], "profile_sha256": voice.status["profile_sha256"],
        "model": "chatterbox-turbo (my voice)", "chapter_starts": starts,
        "chapter_durations": durations, "speech_durations": speech,
        "speech_delay": SPEECH_DELAY, "track": track.name,
        "clips": [p.name for p in clip_paths], "watermark": "preserved model-provided watermark"})
    log(f"Narration plan: {plan}")
    return plan


# ----------------------------------------------------------------------
# The exporter's side (runs in the renderer's Python; light imports only)
# ----------------------------------------------------------------------

def narrate_for_export(chapters, speak_promise: bool, lesson_key: str, video_path: Path,
                       progress=print) -> Path:
    """Write the film's words out, have the voice environment speak them, return the plan."""
    from two_v_demo.audio import spoken_chapter_text

    out_dir = video_path.parent / f"{video_path.stem}-myvoice"
    out_dir.mkdir(parents=True, exist_ok=True)
    script = {"lesson": lesson_key, "chapters": [
        {"title": ch.title, "duration": float(ch.duration),
         "text": spoken_chapter_text(i, tuple(chapters), speak_promise)}
        for i, ch in enumerate(chapters)]}
    script_path = out_dir / "script.json"
    _write(script_path, script)
    python = str(VENV_PYTHON) if VENV_PYTHON.is_file() else sys.executable
    progress(f"Narrating {len(chapters)} chapters in your voice (local, {python})...")
    env = dict(os.environ, PYTHONUNBUFFERED="1")
    process = subprocess.Popen([python, "-m", "local_voice_studio.my_voice", "narrate",
                                "--script", str(script_path), "--out", str(out_dir)],
                               cwd=str(ROOT), env=env, stdout=subprocess.PIPE,
                               stderr=subprocess.STDOUT, text=True, bufsize=1)
    for line in process.stdout:
        progress("  " + line.rstrip())
    if process.wait() != 0:
        raise RuntimeError("Narrating in your voice failed; see the lines above. "
                           "Switch the default back to Andrew on the My Voice page to render now.")
    return out_dir / "narration-plan.json"


def summary() -> str:
    status = _read(STATUS, {})
    default = default_voice()
    if not status:
        return f"No voice built yet. Default narrator: {default['label']}."
    card = status.get("characteristics", {})
    cal = status.get("calibration", {})
    return "\n".join([
        f"Default narrator: {default['label']}",
        f"Voice {status['profile_id']}, built {status['built_at']}",
        f"From {status['recordings']} recordings ({status['duplicates_skipped']} duplicates skipped): "
        f"{status['clips_accepted']} of {status['clips_total']} clips kept, "
        f"{status['minutes_accepted']:.1f} minutes of you",
        f"Pitch {card.get('pitch_median_hz', 0):.0f} Hz (range {card.get('pitch_range_semitones', 0):.1f} "
        f"semitones), {card.get('speaking_rate_wpm', 0):.0f} words/min, "
        f"brightness {card.get('brightness_hz', 0):.0f} Hz",
        "Likeness (1.0 = you): " + ", ".join(f"{k} {v['similarity']:.3f}" for k, v in cal.items())
        + f"; using {status['active_conds'].removeprefix('conds_').removesuffix('.pt')}, "
          f"pace x{status['tempo']:.2f}",
        f"Listen: my_voice/samples/{status.get('sample', '')}",
    ])


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(prog="my_voice", description=__doc__.splitlines()[0])
    sub = parser.add_subparsers(dest="cmd", required=True)
    p = sub.add_parser("build")
    p.add_argument("paths", nargs="*")
    p.add_argument("--list", help="a text file with one path per line")
    p.add_argument("--speaker", default="Donovan Zeanah")
    p.add_argument("--i-own-this-voice", action="store_true")
    p.add_argument("--no-default", action="store_true")
    sub.add_parser("status")
    p = sub.add_parser("default"); p.add_argument("engine", choices=("mine", "andrew"))
    p = sub.add_parser("say"); p.add_argument("text"); p.add_argument("--out", default="")
    p = sub.add_parser("narrate"); p.add_argument("--script", required=True)
    p.add_argument("--out", required=True)
    p = sub.add_parser("tweak", help="show or change the sound: name=value ..., --preset, --reset")
    p.add_argument("settings", nargs="*")
    p.add_argument("--preset", choices=sorted(TWEAK_PRESETS))
    p.add_argument("--reset", action="store_true")
    p = sub.add_parser("preview", help="the sample sentence with the current tweaks")
    p.add_argument("--out", default="")
    args = parser.parse_args(argv)
    if sys.stdout.encoding and sys.stdout.encoding.lower() != "utf-8":
        sys.stdout.reconfigure(encoding="utf-8")
    if args.cmd == "status":
        print(summary())
        return 0
    if args.cmd == "default":
        print(set_default(args.engine)["label"])
        return 0
    if args.cmd == "build":
        paths = list(args.paths)
        if args.list:
            paths += Path(args.list).read_text(encoding="utf-8").splitlines()
        build(paths, args.speaker, args.i_own_this_voice, not args.no_default)
        print(summary())
        return 0
    if args.cmd == "say":
        out = Path(args.out) if args.out else SAMPLES / f"say-{time.strftime('%Y%m%d-%H%M%S')}.wav"
        Voice().say(args.text, out)
        print(out)
        return 0
    if args.cmd == "narrate":
        narrate(Path(args.script), Path(args.out))
        return 0
    if args.cmd == "tweak":
        changes = {}
        for item in args.settings:
            name, _, value = item.partition("=")
            changes[name.strip()] = float(value)
        if args.reset or args.preset or changes:
            set_tweaks(changes, preset="natural" if args.reset else (args.preset or ""))
        for name, value in tweaks().items():
            lo, hi, _n, what = TWEAK_LIMITS[name]
            print(f"{name:<16} {value:>8.2f}   ({lo:g} to {hi:g})  {what}")
        return 0
    if args.cmd == "preview":
        print(preview(Path(args.out) if args.out else None))
        return 0
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
