"""Serializable domain models for Local Voice Studio."""

from __future__ import annotations

from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
from typing import Any


SCHEMA_VERSION = 1


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


@dataclass
class ProjectManifest:
    schema: int = SCHEMA_VERSION
    name: str = ""
    speaker_label: str = ""
    created_at: str = field(default_factory=utc_now)
    updated_at: str = field(default_factory=utc_now)
    offline_only: bool = True
    canonical_sample_rate: int = 24_000
    canonical_channels: int = 1
    canonical_sample_width: int = 2

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)

    @classmethod
    def from_dict(cls, payload: dict[str, Any]) -> "ProjectManifest":
        known = {key: payload[key] for key in cls.__dataclass_fields__ if key in payload}
        manifest = cls(**known)
        if manifest.schema > SCHEMA_VERSION:
            raise ValueError(
                f"Project schema {manifest.schema} is newer than supported "
                f"schema {SCHEMA_VERSION}"
            )
        manifest.schema = SCHEMA_VERSION
        return manifest


@dataclass
class ConsentRecord:
    speaker_name: str
    voice_owner_confirmed: bool
    authorized_use_confirmed: bool
    anti_deception_confirmed: bool
    accepted_at: str = field(default_factory=utc_now)
    statement_version: int = 1

    @property
    def valid(self) -> bool:
        return (
            bool(self.speaker_name.strip())
            and self.voice_owner_confirmed
            and self.authorized_use_confirmed
            and self.anti_deception_confirmed
        )

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)

    @classmethod
    def from_dict(cls, payload: dict[str, Any]) -> "ConsentRecord":
        return cls(
            speaker_name=str(payload.get("speaker_name", "")),
            voice_owner_confirmed=bool(payload.get("voice_owner_confirmed")),
            authorized_use_confirmed=bool(payload.get("authorized_use_confirmed")),
            anti_deception_confirmed=bool(payload.get("anti_deception_confirmed")),
            accepted_at=str(payload.get("accepted_at", utc_now())),
            statement_version=int(payload.get("statement_version", 1)),
        )


@dataclass
class ClipRecord:
    clip_id: str
    audio_file: str
    text: str = ""
    status: str = "draft"
    duration_s: float = 0.0
    peak_dbfs: float = -120.0
    rms_dbfs: float = -120.0
    clipped_pct: float = 0.0
    silence_pct: float = 0.0
    sample_rate: int = 0
    channels: int = 0
    sha256: str = ""
    source_id: str = ""
    rejection_reason: str = ""
    created_at: str = field(default_factory=utc_now)

    @property
    def accepted(self) -> bool:
        return self.status == "accepted"

    @property
    def quality_issues(self) -> tuple[str, ...]:
        issues: list[str] = []
        if self.duration_s < 1.5:
            issues.append("too short")
        if self.duration_s > 20.0:
            issues.append("too long")
        if self.peak_dbfs > -0.3 or self.clipped_pct > 0.1:
            issues.append("clipping")
        if self.rms_dbfs < -38.0:
            issues.append("too quiet")
        if self.silence_pct > 35.0:
            issues.append("too much silence")
        if not self.text.strip():
            issues.append("missing transcript")
        if self.sample_rate != 24_000:
            issues.append("wrong sample rate")
        if self.channels != 1:
            issues.append("not mono")
        return tuple(issues)

    def to_row(self) -> list[str]:
        return [
            self.clip_id,
            self.audio_file,
            self.text,
            self.status,
            f"{self.duration_s:.6f}",
            f"{self.peak_dbfs:.6f}",
            f"{self.rms_dbfs:.6f}",
            f"{self.clipped_pct:.6f}",
            f"{self.silence_pct:.6f}",
            str(self.sample_rate),
            str(self.channels),
            self.sha256,
            self.source_id,
            self.rejection_reason,
            self.created_at,
        ]

    @classmethod
    def from_row(cls, row: dict[str, str]) -> "ClipRecord":
        return cls(
            clip_id=row.get("clip_id", ""),
            audio_file=row.get("audio_file", ""),
            text=row.get("text", ""),
            status=row.get("status", "draft"),
            duration_s=float(row.get("duration_s") or 0.0),
            peak_dbfs=float(row.get("peak_dbfs") or -120.0),
            rms_dbfs=float(row.get("rms_dbfs") or -120.0),
            clipped_pct=float(row.get("clipped_pct") or 0.0),
            silence_pct=float(row.get("silence_pct") or 0.0),
            sample_rate=int(row.get("sample_rate") or 0),
            channels=int(row.get("channels") or 0),
            sha256=row.get("sha256", ""),
            source_id=row.get("source_id", ""),
            rejection_reason=row.get("rejection_reason", ""),
            created_at=row.get("created_at", utc_now()),
        )


@dataclass
class VoiceProfile:
    schema: int
    profile_id: str
    name: str
    created_at: str
    reference_wav: str
    reference_text: str
    source_clip_ids: list[str]
    sha256: str
    duration_s: float
    locked: bool = True
    backend_hint: str = "chatterbox-turbo"

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)

    @classmethod
    def from_dict(cls, payload: dict[str, Any]) -> "VoiceProfile":
        return cls(**payload)
