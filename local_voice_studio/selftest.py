"""Dependency-free vertical-slice checks for Local Voice Studio."""

from __future__ import annotations

import math
import tempfile
from pathlib import Path

from .audio_tools import (
    CANONICAL_RATE,
    build_voice_profile,
    create_clip_record,
    energy_segments,
    inspect_wav,
    write_pcm16_mono,
)
from .backends import (
    chatterbox_status,
    detect_hardware,
    export_f5_dataset,
    faster_whisper_status,
)
from .models import ConsentRecord, ProjectManifest
from .project import VoiceProject, sha256_file


def run_selftest() -> None:
    with tempfile.TemporaryDirectory(prefix="local-voice-studio-") as temporary:
        root = Path(temporary) / "project"
        project = VoiceProject.create(root, "Self Test", "Authorized Tester")
        unauthorized_source = Path(temporary) / "not-yet-authorized.wav"
        write_pcm16_mono(
            unauthorized_source,
            CANONICAL_RATE,
            [0] * CANONICAL_RATE,
        )
        try:
            project.import_raw(unauthorized_source)
        except PermissionError:
            pass
        else:
            raise AssertionError("audio import bypassed the consent gate")
        consent = ConsentRecord(
            speaker_name="Authorized Tester",
            voice_owner_confirmed=True,
            authorized_use_confirmed=True,
            anti_deception_confirmed=True,
        )
        project.save_consent(consent)
        assert project.consented
        try:
            project.save_consent(consent)
        except ValueError:
            pass
        else:
            raise AssertionError("immutable consent record was overwritten")

        round_trip = ProjectManifest.from_dict(project.manifest.to_dict())
        assert round_trip.name == "Self Test"
        try:
            project.resolve_relative("../escape.wav")
        except ValueError:
            pass
        else:
            raise AssertionError("path traversal was not rejected")

        seconds = 3.2
        samples = [
            int(7_000 * math.sin(2.0 * math.pi * 180.0 * index / CANONICAL_RATE))
            for index in range(int(CANONICAL_RATE * seconds))
        ]
        clip_path = root / "clips" / "fixture.wav"
        write_pcm16_mono(clip_path, CANONICAL_RATE, samples)
        metrics = inspect_wav(clip_path)
        assert abs(metrics.duration_s - seconds) < 0.01
        assert metrics.channels == 1 and metrics.sample_rate == CANONICAL_RATE
        assert metrics.clipped_pct == 0.0
        assert energy_segments(clip_path)

        clip = create_clip_record(
            project,
            clip_path,
            "fixture",
            "This is a clean authorized local voice fixture.",
            "fixture-source",
        )
        clip.status = "accepted"
        assert not clip.quality_issues, clip.quality_issues
        project.upsert_clip(clip)
        reloaded = project.load_clips()
        assert len(reloaded) == 1 and reloaded[0].text == clip.text

        profile = build_voice_profile(project, "teacher", reloaded, 2.0)
        reference = project.resolve_relative(profile.reference_wav)
        assert reference.is_file()
        assert profile.sha256 == sha256_file(reference)
        assert profile.locked

        metadata = export_f5_dataset(project, root / "runs" / "f5-export")
        first_line = metadata.read_text(encoding="utf-8").splitlines()[0]
        assert first_line == "audio_file|text"
        assert str(clip_path.resolve()) in metadata.read_text(encoding="utf-8")

        hardware = detect_hardware()
        assert hardware.grade
        assert chatterbox_status().backend_id == "chatterbox-turbo"
        assert faster_whisper_status().backend_id == "faster-whisper"
    print("Local Voice Studio selftest OK")
