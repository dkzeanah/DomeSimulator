"""Dome Forge -- a layered, single-dome builder.

Scoped deliberately to exactly one dome, the way a character creator is
scoped to one character: no site, no factory, no timeline. Everything is
a layer you can hide, fade, reorder, and tune.
"""

from .layers import Layer, LayerStack, DomeSettings, LAYER_KINDS, default_stack

__all__ = [
    "Layer", "LayerStack", "DomeSettings", "LAYER_KINDS", "default_stack",
]
