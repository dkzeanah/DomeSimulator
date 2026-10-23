"""Lightweight render-preset model shared by the catalogue and selected-film entry points."""
from __future__ import annotations
from dataclasses import dataclass, field

# The narration voice every published video in this repository uses.
# Stated here rather than defaulted, because the timeline depends on it.
HOUSE_VOICE = "en-US-AndrewMultilingualNeural"


@dataclass(frozen=True)
class RenderPreset:
    """One reproducible video render, as launcher field values."""

    key: str
    label: str
    summary: str
    """One line the launcher shows when this preset is selected."""
    fields: dict = field(default_factory=dict)
    """Launcher field values. Keys match the Masterclass tab's widgets."""

    def applied(self) -> dict:
        """The full field set, house defaults filled in.

        A preset states what makes it itself; everything else comes from
        the house defaults so that adding a new shared default does not
        mean editing every preset.
        """
        merged = {
            "action": "export_video",
            "lesson": "2v",
            "size": "1920x1080",
            "fps": "30",
            "voice": HOUSE_VOICE,
            "voice_rate": "+0%",
            "voice_pitch": "+0Hz",
            "voice_volume": "+0%",
            "no_narration": False,
            "fullscreen": False,
            "compose_segments": False,
            "segments_include": "",
            "segments_exclude": "",
            "export_video": "",
            "shots": "",
            "voice_preview": "",
        }
        merged.update(self.fields)
        return merged


def _video(key: str, lesson: str, filename: str, summary: str,
           **extra) -> RenderPreset:
    """A full narrated export to the standard deliverables folder."""
    fields = {
        "lesson": lesson,
        "action": "export_video",
        "export_video": f"deliverables/masterclass/{filename}",
    }
    fields.update(extra)
    return RenderPreset(key=key, label=filename, summary=summary,
                        fields=fields)


