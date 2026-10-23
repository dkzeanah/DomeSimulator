"""Canonical episode preset, without importing every unrelated film's geometry."""
from render_preset_model import _video

EPISODE_PRESET = _video(
    "sketch_gpt_pilot", "sketch_gpt_pilot", "sketch-gpt-nearly-level-s01e01.mp4",
    "Nearly Level / Shelf Esteem: captioned PG-13 family comedy animatic, "
    "cinematic cameras and five original characters. Includes its own closing series title.",
    size="960x540", fps="12", no_narration=True, compose_segments=False,
    orientation_sizes={"landscape":"960x540","portrait":"540x960"})
