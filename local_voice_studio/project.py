"""Portable, path-safe project storage."""

from __future__ import annotations

import csv
import hashlib
import json
import re
import shutil
from pathlib import Path
from typing import Iterable

from .models import (
    ClipRecord,
    ConsentRecord,
    ProjectManifest,
    VoiceProfile,
    utc_now,
)


METADATA_FIELDS = [
    "clip_id", "audio_file", "text", "status", "duration_s", "peak_dbfs",
    "rms_dbfs", "clipped_pct", "silence_pct", "sample_rate", "channels",
    "sha256", "source_id", "rejection_reason", "created_at",
]


def safe_slug(value: str, fallback: str = "voice") -> str:
    slug = re.sub(r"[^A-Za-z0-9_-]+", "-", value.strip()).strip("-_").lower()
    return slug or fallback


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


class VoiceProject:
    REQUIRED_DIRECTORIES = (
        "raw", "normalized", "clips", "profiles", "runs", "outputs/audio",
        "outputs/dome",
    )

    def __init__(self, root: Path, manifest: ProjectManifest):
        self.root = root.resolve()
        self.manifest = manifest

    @classmethod
    def create(
        cls,
        root: Path,
        name: str,
        speaker_label: str,
    ) -> "VoiceProject":
        root = root.resolve()
        if root.exists() and any(root.iterdir()):
            raise ValueError("New project directory must be empty")
        root.mkdir(parents=True, exist_ok=True)
        manifest = ProjectManifest(name=name.strip(), speaker_label=speaker_label.strip())
        project = cls(root, manifest)
        project.ensure_layout()
        project.save_manifest()
        project.save_clips([])
        project.audit("project_created", {"name": name, "speaker": speaker_label})
        return project

    @classmethod
    def open(cls, root: Path) -> "VoiceProject":
        root = root.resolve()
        path = root / "project.json"
        if not path.is_file():
            raise ValueError(f"Not a Local Voice Studio project: {root}")
        payload = json.loads(path.read_text(encoding="utf-8"))
        project = cls(root, ProjectManifest.from_dict(payload))
        project.ensure_layout()
        return project

    def ensure_layout(self) -> None:
        for relative in self.REQUIRED_DIRECTORIES:
            (self.root / relative).mkdir(parents=True, exist_ok=True)

    def resolve_relative(self, relative: str | Path) -> Path:
        candidate = (self.root / relative).resolve()
        try:
            candidate.relative_to(self.root)
        except ValueError as exc:
            raise ValueError("Project path escapes the project root") from exc
        return candidate

    def relative(self, path: Path) -> str:
        resolved = path.resolve()
        try:
            return resolved.relative_to(self.root).as_posix()
        except ValueError as exc:
            raise ValueError("File is outside the project") from exc

    def save_manifest(self) -> None:
        self.manifest.updated_at = utc_now()
        path = self.root / "project.json"
        path.write_text(
            json.dumps(self.manifest.to_dict(), indent=2) + "\n",
            encoding="utf-8",
        )

    def audit(self, event: str, details: dict) -> None:
        entry = {"at": utc_now(), "event": event, "details": details}
        with (self.root / "audit.jsonl").open("a", encoding="utf-8") as handle:
            handle.write(json.dumps(entry, sort_keys=True) + "\n")

    def save_consent(self, consent: ConsentRecord) -> None:
        if not consent.valid:
            raise ValueError("All ownership and authorization statements are required")
        path = self.root / "consent.json"
        if path.exists():
            raise ValueError("Consent record is immutable once accepted")
        path.write_text(
            json.dumps(consent.to_dict(), indent=2) + "\n",
            encoding="utf-8",
        )
        self.audit(
            "consent_asserted",
            {
                "speaker_name": consent.speaker_name,
                "statement_version": consent.statement_version,
            },
        )

    def load_consent(self) -> ConsentRecord | None:
        path = self.root / "consent.json"
        if not path.is_file():
            return None
        return ConsentRecord.from_dict(json.loads(path.read_text(encoding="utf-8")))

    @property
    def consented(self) -> bool:
        consent = self.load_consent()
        return bool(consent and consent.valid)

    def load_clips(self) -> list[ClipRecord]:
        path = self.root / "metadata.csv"
        if not path.exists():
            return []
        with path.open("r", newline="", encoding="utf-8") as handle:
            return [ClipRecord.from_row(row) for row in csv.DictReader(handle)]

    def save_clips(self, clips: Iterable[ClipRecord]) -> None:
        clip_list = list(clips)
        path = self.root / "metadata.csv"
        with path.open("w", newline="", encoding="utf-8") as handle:
            writer = csv.writer(handle, delimiter=",", quoting=csv.QUOTE_MINIMAL)
            writer.writerow(METADATA_FIELDS)
            for clip in clip_list:
                writer.writerow(clip.to_row())
        self.audit("metadata_saved", {"clip_count": len(clip_list)})

    def upsert_clip(self, clip: ClipRecord) -> None:
        clips = self.load_clips()
        for index, existing in enumerate(clips):
            if existing.clip_id == clip.clip_id:
                clips[index] = clip
                break
        else:
            clips.append(clip)
        self.save_clips(clips)

    def import_raw(self, source: Path) -> tuple[str, Path]:
        if not self.consented:
            raise PermissionError("Accept the ownership statement before importing audio")
        source = source.resolve()
        if not source.is_file():
            raise FileNotFoundError(source)
        digest = sha256_file(source)
        source_id = digest[:16]
        destination = self.root / "raw" / f"{source_id}{source.suffix.lower()}"
        if not destination.exists():
            shutil.copy2(source, destination)
        self.audit(
            "audio_imported",
            {"source_id": source_id, "name": source.name, "sha256": digest},
        )
        return source_id, destination

    def save_profile(self, profile: VoiceProfile) -> Path:
        directory = self.resolve_relative(f"profiles/{profile.profile_id}")
        directory.mkdir(parents=True, exist_ok=False)
        path = directory / "profile.json"
        path.write_text(
            json.dumps(profile.to_dict(), indent=2) + "\n",
            encoding="utf-8",
        )
        self.audit(
            "profile_locked",
            {"profile_id": profile.profile_id, "sha256": profile.sha256},
        )
        return path

    def profiles(self) -> list[VoiceProfile]:
        result: list[VoiceProfile] = []
        for path in sorted((self.root / "profiles").glob("*/profile.json")):
            result.append(
                VoiceProfile.from_dict(json.loads(path.read_text(encoding="utf-8")))
            )
        return result
