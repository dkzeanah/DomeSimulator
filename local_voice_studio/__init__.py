"""Local-first voice dataset, profile, and model-adaptation studio."""

from .models import ClipRecord, ProjectManifest, VoiceProfile
from .project import VoiceProject

__all__ = ["ClipRecord", "ProjectManifest", "VoiceProfile", "VoiceProject"]

__version__ = "0.1.0"
