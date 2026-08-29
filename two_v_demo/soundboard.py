"""A soundboard for themed repackaging: drops, stingers, one-shots, beds.

Sounds live in ``assets/audio/<category>/<name>.<ext>`` and are addressed
as ``category/name``.  Nothing here ships audio -- the repository
contains no sound files and this module will not download any, because
the licensing of a sound is the user's business and silently baking in
somebody else's clip is how a channel gets a strike.

Drop files into the folders and they appear.  A cue naming a sound that
is not present is **skipped with a warning**, never an error: a missing
airhorn must not take down a forty-minute render.

    assets/audio/
        drops/        quotes, memes, catchphrases, reactions
        stingers/     1-5 second intro / outro / transition sounds
        oneshots/     explosions, bells, laughs, impacts
        beds/         longer background music and ambience
        loops/        repeatable music, rhythm, ambience
        voice/        spoken snippets and sound bites

Supported formats are whatever the resolved ffmpeg can decode, which in
practice is all of wav, mp3, m4a, ogg and flac.
"""

from __future__ import annotations

import re
import subprocess
import wave
from dataclasses import dataclass
from pathlib import Path

import numpy as np


ROOT = Path("assets/audio")

CATEGORIES: tuple[tuple[str, str], ...] = (
    ("drops", "quotes, memes, catchphrases, reactions"),
    ("stingers", "1-5 second intro, outro and transition sounds"),
    ("oneshots", "explosions, bells, laughs, impacts"),
    ("beds", "longer background music and ambience"),
    ("loops", "repeatable music, rhythm and ambience"),
    ("voice", "spoken snippets and sound bites"),
)

CATEGORY_NAMES = tuple(name for name, _ in CATEGORIES)

AUDIO_SUFFIXES = (".wav", ".mp3", ".m4a", ".ogg", ".flac", ".aac")

SAMPLE_RATE = 44100
"""Matches the narration mixer, so cues need no resampling of their own."""


@dataclass(frozen=True)
class Sound:
    """One file on the board."""

    key: str
    category: str
    name: str
    path: Path

    @property
    def size_kb(self) -> float:
        return self.path.stat().st_size / 1024.0


def ensure_layout(root: Path = ROOT) -> tuple[Path, ...]:
    """Create the category folders, each with a note saying what goes in."""
    made: list[Path] = []
    for name, description in CATEGORIES:
        folder = root / name
        folder.mkdir(parents=True, exist_ok=True)
        readme = folder / "README.md"
        if not readme.exists():
            readme.write_text(
                f"# {name}\n\n{description}\n\n"
                f"Drop audio files here and they become available as "
                f"`{name}/<filename-without-extension>`.\n\n"
                f"Supported: {', '.join(AUDIO_SUFFIXES)}\n\n"
                "Nothing in this repository ships audio. Use sounds you have "
                "the right to use.\n",
                encoding="utf-8")
            made.append(readme)
    return tuple(made)


def discover(root: Path = ROOT) -> dict[str, Sound]:
    """Every sound currently on the board, keyed ``category/name``."""
    found: dict[str, Sound] = {}
    for category in CATEGORY_NAMES:
        folder = root / category
        if not folder.is_dir():
            continue
        for path in sorted(folder.iterdir()):
            if path.suffix.lower() not in AUDIO_SUFFIXES:
                continue
            key = f"{category}/{path.stem}"
            found[key] = Sound(key, category, path.stem, path)
    return found


def resolve(key: str, root: Path = ROOT) -> Sound | None:
    """Look one up, or return None so the caller can skip it politely."""
    return discover(root).get(key)


def decode(sound: Sound, ffmpeg: str) -> np.ndarray:
    """Decode to mono float32 at the mixer's sample rate."""
    command = [
        ffmpeg, "-v", "error", "-i", str(sound.path),
        "-f", "s16le", "-ac", "1", "-ar", str(SAMPLE_RATE), "-",
    ]
    result = subprocess.run(command, capture_output=True)
    if result.returncode != 0 or not result.stdout:
        return np.zeros(0, dtype=np.float32)
    raw = np.frombuffer(result.stdout, dtype="<i2").astype(np.float32)
    return raw / 32768.0


def mix_cues(
    track: np.ndarray,
    cues,
    starts,
    ffmpeg: str,
    root: Path = ROOT,
    progress=print,
) -> np.ndarray:
    """Lay soundboard cues onto an existing narration buffer.

    ``track`` is float32 mono at :data:`SAMPLE_RATE`. ``cues`` is an
    iterable of ``(key, at_seconds, gain, loop)``. A cue whose sound is
    missing is reported and skipped; a cue past the end of the track is
    trimmed rather than resizing the film.
    """
    board = discover(root)
    for key, at_seconds, gain, loop in cues:
        sound = board.get(key)
        if sound is None:
            progress(f"soundboard: {key} not found, skipping")
            continue
        samples = decode(sound, ffmpeg)
        if samples.size == 0:
            progress(f"soundboard: {key} decoded to nothing, skipping")
            continue
        start = max(0, int(at_seconds * SAMPLE_RATE))
        if start >= track.size:
            continue
        room = track.size - start
        if loop and samples.size < room:
            repeats = int(np.ceil(room / samples.size))
            samples = np.tile(samples, repeats)
        chunk = samples[:room] * gain
        track[start:start + chunk.size] += chunk
    return track


def write_wav(track: np.ndarray, path: Path) -> Path:
    """Write a float32 mono buffer as 16-bit PCM."""
    peak = float(np.max(np.abs(track))) if track.size else 0.0
    if peak > 1.0:
        track = track / peak
    data = np.clip(track * 32767.0, -32768, 32767).astype("<i2")
    path.parent.mkdir(parents=True, exist_ok=True)
    with wave.open(str(path), "wb") as handle:
        handle.setnchannels(1)
        handle.setsampwidth(2)
        handle.setframerate(SAMPLE_RATE)
        handle.writeframes(data.tobytes())
    return path


def bed_encoder(ffmpeg: str) -> tuple[str, ...]:
    """Pick an AAC encoder that will actually honour the bitrate asked for.

    ``audio.py._aac_encoder`` prefers ``libvo_aacenc`` over the native
    encoder, which was the right call when the native one was genuinely
    bad. On a build where the native encoder is merely gated behind
    ``-strict -2``, that preference silently costs you the track:
    libvo_aacenc ignores ``-b:a`` and lands around 64 kbps whatever you
    ask for, against roughly 160 for the native encoder on the same input.

    Re-encoding a whole narration to add a bed is not worth that, so this
    orders by quality instead. The shared helper is deliberately left
    alone -- every previously shipped video was encoded through it, and
    they have to keep reproducing byte for byte.
    """
    probe = subprocess.run([ffmpeg, "-encoders"], capture_output=True,
                           text=True, check=False)
    encoders = probe.stdout + probe.stderr
    if re.search(r"\blibfdk_aac\b", encoders):
        return ("-c:a", "libfdk_aac")
    if re.search(r"^\s*A\S*\s+aac\b", encoders, re.MULTILINE):
        return ("-c:a", "aac", "-strict", "-2")
    if re.search(r"\blibvo_aacenc\b", encoders):
        return ("-c:a", "libvo_aacenc")
    return ("-c:a", "aac", "-strict", "-2")


def mix_bed_into_track(
    track_path: Path,
    bed_key: str,
    ffmpeg: str,
    gain: float = 0.16,
    root: Path = ROOT,
    progress=print,
) -> bool:
    """Lay a looping bed under a finished narration track, in place.

    Done as a post-step on the encoded track rather than inside the
    narration mixer, because there are two mixer paths (a filter one and
    a PCM-compatibility one) and this has to work behind both. No ffmpeg
    filters are used, for the same reason the rest of this package avoids
    them: a 2013 build has to be able to run it.

    Returns False and leaves the track untouched if the bed is missing.
    """
    bed = discover(root).get(bed_key)
    if bed is None:
        progress(f"soundboard: bed {bed_key} not found; track left dry")
        return False

    def decode(path: Path) -> np.ndarray:
        result = subprocess.run(
            [ffmpeg, "-v", "error", "-i", str(path),
             "-f", "s16le", "-ac", "1", "-ar", str(SAMPLE_RATE), "-"],
            capture_output=True)
        if result.returncode != 0 or not result.stdout:
            return np.zeros(0, dtype=np.float32)
        return np.frombuffer(result.stdout, dtype="<i2").astype(np.float32) / 32768.0

    voice = decode(track_path)
    if voice.size == 0:
        progress("soundboard: could not decode the narration track")
        return False
    music = decode(bed.path)
    if music.size == 0:
        progress(f"soundboard: could not decode {bed_key}")
        return False

    if music.size < voice.size:
        music = np.tile(music, int(np.ceil(voice.size / music.size)))
    music = music[:voice.size] * gain

    # Duck the bed under speech so the voice always wins. A slow-moving
    # envelope of the narration drives it, which is cheap and enough.
    window = SAMPLE_RATE // 8
    envelope = np.convolve(np.abs(voice), np.ones(window) / window, mode="same")
    peak = float(np.max(envelope)) or 1.0
    duck = 1.0 - 0.65 * np.clip(envelope / peak, 0.0, 1.0)
    mixed = voice + music * duck

    limit = float(np.max(np.abs(mixed)))
    if limit > 1.0:
        mixed = mixed / limit

    # Encode beside the track and move it into place only once it is known
    # good. Encoding straight to track_path truncates the destination
    # before the encoder runs, so a codec this build happens to lack would
    # not merely fail -- it would destroy a narration that took an hour to
    # synthesise, and the render would carry on and mux the wreckage.
    scratch = track_path.with_suffix(".bedmix.wav")
    encoded = track_path.with_suffix(".bedmix.m4a")
    write_wav(mixed, scratch)

    result = subprocess.run(
        [ffmpeg, "-y", "-v", "error", "-i", str(scratch),
         *bed_encoder(ffmpeg), "-b:a", "192k", str(encoded)],
        capture_output=True)
    scratch.unlink(missing_ok=True)

    if (result.returncode != 0 or not encoded.exists()
            or encoded.stat().st_size == 0):
        encoded.unlink(missing_ok=True)
        detail = result.stderr.decode("utf-8", "replace").strip().splitlines()
        progress(f"soundboard: could not encode the bed mix, so the track is "
                 f"left dry and intact"
                 + (f" -- {detail[0]}" if detail else ""))
        return False

    encoded.replace(track_path)
    progress(f"soundboard: mixed {bed_key} under the narration at "
             f"gain {gain:.2f}, ducked under speech")
    return True


def board_menu(root: Path = ROOT) -> str:
    """What is on the board right now, by category."""
    board = discover(root)
    lines = [f"soundboard: {len(board)} sound(s) in {root}"]
    for category, description in CATEGORIES:
        members = [s for s in board.values() if s.category == category]
        lines.append(f"  {category:<10} {len(members):>3}   {description}")
        for sound in members[:8]:
            lines.append(f"      {sound.name}  ({sound.size_kb:.0f} kB)")
        if len(members) > 8:
            lines.append(f"      ... and {len(members) - 8} more")
    if not board:
        lines.append("")
        lines.append("  Nothing yet. Drop files into the folders above; this")
        lines.append("  repository deliberately ships no audio of its own.")
    return "\n".join(lines)


def validate_soundboard() -> None:
    """The board must work empty, which is how it will usually be."""
    board = discover()
    for key, sound in board.items():
        assert key == f"{sound.category}/{sound.name}", key
        assert sound.category in CATEGORY_NAMES, sound.category
        assert sound.path.is_file(), sound.path

    # A missing sound is skipped, not raised: a render must survive it.
    track = np.zeros(SAMPLE_RATE, dtype=np.float32)
    messages: list[str] = []
    result = mix_cues(track, [("oneshots/definitely-not-here", 0.1, 1.0, False)],
                      [], "ffmpeg", progress=messages.append)
    assert result is track
    assert any("not found" in message for message in messages), messages
    assert float(np.max(np.abs(result))) == 0.0

    # Mixing must never lengthen the film.
    before = track.size
    mix_cues(track, [], [], "ffmpeg", progress=lambda _: None)
    assert track.size == before

    # A missing bed must leave the track alone rather than raise.
    assert mix_bed_into_track(Path("nope.m4a"), "beds/not-here", "ffmpeg",
                              progress=lambda _: None) is False

    assert len(CATEGORIES) >= 6
    assert len(set(CATEGORY_NAMES)) == len(CATEGORY_NAMES)

    _check_bed_round_trip()


def _check_bed_round_trip() -> None:
    """Actually encode a bed onto a track, because a mocked test lied.

    The first version of this module hard-coded ``-c:a aac``, which the
    ffmpeg builds this package targets refuse unless experimental codecs
    are enabled. Nothing caught it: the unit tests only exercised the
    missing-sound path, which returns before reaching the encoder. So this
    runs the whole thing end to end against the real ffmpeg and checks the
    output is audibly different from the input.
    """
    import shutil
    import tempfile

    ffmpeg = shutil.which("ffmpeg")
    if ffmpeg is None:
        return  # nothing to prove without an encoder

    with tempfile.TemporaryDirectory() as folder:
        root = Path(folder) / "audio"
        (root / "beds").mkdir(parents=True)

        seconds, tone_hz = 3.0, 220.0
        time = np.arange(int(seconds * SAMPLE_RATE), dtype=np.float32)
        bed = np.sin(2.0 * np.pi * tone_hz * time / SAMPLE_RATE) * 0.6
        write_wav(bed.astype(np.float32), root / "beds" / "probe.wav")

        # A "narration" that is loud for a second and silent afterwards,
        # so the gap is where the bed has to show up.
        speech = np.zeros_like(time)
        speech[:SAMPLE_RATE] = np.sin(
            2.0 * np.pi * 700.0 * time[:SAMPLE_RATE] / SAMPLE_RATE) * 0.5
        source = Path(folder) / "track.wav"
        write_wav(speech, source)

        track = Path(folder) / "track.m4a"
        subprocess.run([ffmpeg, "-y", "-v", "error", "-i", str(source),
                        *bed_encoder(ffmpeg), str(track)], check=True)
        before = track.stat().st_size

        messages: list[str] = []
        ok = mix_bed_into_track(track, "beds/probe", ffmpeg, gain=0.5,
                                root=root, progress=messages.append)
        assert ok, messages
        assert track.exists() and track.stat().st_size > 0, \
            "the mix must never leave an empty track behind"
        assert before > 0

        # The silent half must now carry the bed.
        raw = subprocess.run(
            [ffmpeg, "-v", "error", "-i", str(track), "-f", "s16le",
             "-ac", "1", "-ar", str(SAMPLE_RATE), "-"],
            capture_output=True, check=True).stdout
        mixed = np.frombuffer(raw, dtype="<i2").astype(np.float32) / 32768.0
        tail = mixed[int(1.5 * SAMPLE_RATE):]
        assert tail.size, "decoded nothing back"
        level = float(np.sqrt((tail ** 2).mean()))
        assert level > 0.02, (
            f"the gap is still silent at {level:.5f} RMS -- the bed did not "
            f"reach the track")

        # No scratch files may survive a successful mix.
        leftovers = sorted(p.name for p in Path(folder).glob("*.bedmix.*"))
        assert not leftovers, leftovers

        # The bed must not cost the narration its bitrate. libvo_aacenc
        # ignores -b:a and lands near 64 kbps, which is how the first
        # mixed track lost two thirds of its data rate unnoticed.
        chosen = bed_encoder(ffmpeg)
        assert "libvo_aacenc" not in chosen or "libfdk_aac" in chosen, chosen
