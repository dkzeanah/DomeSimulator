"""Presenter — a scriptable 3-D explainer-video engine.

Generalizes the two_v_demo masterclass pipeline into a data-driven
presentation system: text prompts compose environments, scenes contain
shots, shots carry cameras / focus targets / narration / overlay panels,
objects are parametric and animatable, and the whole timeline renders
deterministically to an MP4 with a natural narration track.
"""

from .script import Presentation, Scene, Shot, OverlayPanel
from .prompt import parse_environment, parse_brief

__all__ = [
    "Presentation", "Scene", "Shot", "OverlayPanel",
    "parse_environment", "parse_brief",
]
