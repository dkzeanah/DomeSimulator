"""Cabin World re-renders: a queue of every film, and a blueprint for each.

See rerender/README.md. Everything runs from ``py -3.12 -m rerender``.
"""

import os

# The lessons import pygame, whose greeting would land in a printed prompt.
os.environ.setdefault("PYGAME_HIDE_SUPPORT_PROMPT", "1")
