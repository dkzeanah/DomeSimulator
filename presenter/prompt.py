"""ELIZA-style deduction of scene settings from free text.

Two parsers:

* :func:`parse_environment` — reads a prompt like "on a beach at a lake in
  the desert" or "tropical tsunami ridden environment" and fills an
  :class:`EnvironmentSpec` by ordered keyword rules. Rules compose: later
  keywords refine earlier ones instead of replacing the whole scene.

* :func:`parse_brief` — reads a production brief like "seven scenes each
  of three shots, a close up, macro, and ultra wide shot of elements 1, 2
  and 3" and emits a skeleton Presentation with lenses and focus targets
  distributed the way the sentence implies.
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field

from .script import LENSES, OverlayPanel, Presentation, Scene, Shot


@dataclass
class EnvironmentSpec:
    terrain: str = "grass"       # grass | sand | snow | rock
    water: str = "none"          # none | lake | ocean
    shoreline: bool = False      # a beach ring where terrain meets water
    weather: str = "clear"       # clear | snow | rain | storm
    tsunami: bool = False
    tornado: bool = False
    palms: int = 0
    cacti: int = 0
    pines: int = 0
    rocks: int = 0
    sky: str = "day"             # day | dusk | storm | night
    haze: float = 0.0

    def describe(self) -> str:
        bits = [self.terrain]
        if self.water != "none":
            bits.append(self.water + (" beach" if self.shoreline else ""))
        if self.weather != "clear":
            bits.append(self.weather)
        if self.tsunami:
            bits.append("tsunami")
        if self.tornado:
            bits.append("tornado")
        return ", ".join(bits)


# Ordered rules: (pattern, effects). Effects are attribute assignments;
# callables receive the spec for compound edits. Order matters — later
# rules may refine what earlier rules set (a lake in the desert keeps the
# desert terrain but adds water and a shoreline).
_RULES: tuple = (
    (r"desert|dune|arid", {"terrain": "sand", "cacti": 7, "haze": 0.15,
                           "sky": "day"}),
    (r"beach|shore|coast", {"shoreline": True, "terrain": "sand"}),
    (r"\blake\b|lagoon|pond", {"water": "lake"}),
    (r"ocean|sea\b|gulf", {"water": "ocean"}),
    (r"snow|arctic|winter|blizzard",
     {"terrain": "snow", "weather": "snow", "pines": 8, "cacti": 0,
      "sky": "dusk"}),
    (r"tropic|island|palm", {"palms": 9, "terrain": "sand",
                             "water": "ocean", "shoreline": True}),
    (r"tsunami|tidal wave", {"tsunami": True, "water": "ocean",
                             "sky": "storm", "weather": "storm"}),
    (r"tornado|twister|cyclone", {"tornado": True, "sky": "storm",
                                  "weather": "storm"}),
    (r"storm|thunder", {"sky": "storm", "weather": "rain"}),
    (r"rain", {"weather": "rain"}),
    (r"forest|wood|pine", {"pines": 12, "terrain": "grass"}),
    (r"mountain|rocky|boulder", {"rocks": 9}),
    (r"night", {"sky": "night"}),
    (r"dusk|sunset|evening", {"sky": "dusk"}),
    (r"fog|haze|mist", {"haze": 0.45}),
)


def parse_environment(text: str) -> EnvironmentSpec:
    spec = EnvironmentSpec()
    low = (text or "").lower()
    for pattern, effects in _RULES:
        if re.search(pattern, low):
            for key, value in effects.items():
                setattr(spec, key, value)
    # a lake or ocean next to sand implies a beach transition
    if spec.water != "none" and spec.terrain == "sand":
        spec.shoreline = True
    return spec


# ---------------------------------------------------------------------------
# Production-brief parsing
# ---------------------------------------------------------------------------

_NUMBER_WORDS = {
    "one": 1, "two": 2, "three": 3, "four": 4, "five": 5, "six": 6,
    "seven": 7, "eight": 8, "nine": 9, "ten": 10, "eleven": 11,
    "twelve": 12, "a": 1, "an": 1, "single": 1, "couple": 2, "few": 3,
}

_LENS_WORDS = (
    (r"close[- ]?up|closeup", "portrait"),
    (r"macro", "macro"),
    (r"ultra[- ]?wide|ultrawide", "ultrawide"),
    (r"wide", "wide"),
    (r"portrait", "portrait"),
    (r"establish", "ultrawide"),
)


def _number(token: str) -> int | None:
    token = token.strip().lower()
    if token.isdigit():
        return int(token)
    return _NUMBER_WORDS.get(token)


def _count(text: str, noun: str, default: int) -> int:
    match = re.search(rf"(\w+)\s+{noun}", text)
    if match:
        value = _number(match.group(1))
        if value:
            return value
    return default


def parse_brief(text: str, environment: str = "",
                focus_names: tuple = ()) -> Presentation:
    """Turn a brief into a skeleton Presentation.

    Understands scene/shot counts, lens keywords (in the order spoken),
    and "elements 1, 2 and 3" style focus lists (1-based indices into
    ``focus_names``, or literal object names)."""
    low = (text or "").lower()
    n_scenes = _count(low, r"scenes?", 3)
    n_shots = _count(low, r"shots?", 3)

    lenses: list[str] = []
    for pattern, lens in _LENS_WORDS:
        for match in re.finditer(pattern, low):
            lenses.append((match.start(), lens))
    lenses = [lens for _pos, lens in sorted(lenses)]
    # de-duplicate consecutive repeats while preserving spoken order
    ordered: list[str] = []
    for lens in lenses:
        if not ordered or ordered[-1] != lens:
            ordered.append(lens)
    if not ordered:
        ordered = ["wide", "portrait", "ultrawide"]

    # "elements 1, 2 and 3" or "element two"
    focuses: list[str] = []
    for match in re.finditer(r"elements?\s+([\w ,and]+)", low):
        for token in re.split(r"[ ,]|and", match.group(1)):
            value = _number(token)
            if value and focus_names and 1 <= value <= len(focus_names):
                focuses.append(focus_names[value - 1])
            elif token.strip() and not value and token.strip() in (
                    focus_names or ()):
                focuses.append(token.strip())
    if not focuses:
        focuses = list(focus_names[:3]) if focus_names else [""]

    per_shot = max(3.0, 22.0 / max(1, n_shots))
    scenes = []
    for s in range(n_scenes):
        shots = []
        for k in range(n_shots):
            lens = ordered[k % len(ordered)]
            focus = focuses[k % len(focuses)]
            shots.append(Shot(
                slug=f"s{s + 1}_shot{k + 1}", duration=per_shot,
                lens=lens, focus=focus,
                yaw=-60.0 + 30.0 * k + 8.0 * s,
                pitch=14.0 + 6.0 * (k % 3),
                orbit=10.0 if lens != "macro" else 5.0,
                caption=f"Scene {s + 1} · {lens} on "
                        f"{focus or 'the stage'}",
            ))
        scenes.append(Scene(
            slug=f"scene{s + 1}", title=f"Scene {s + 1}",
            environment=environment, shots=tuple(shots)))
    return Presentation(title=text.strip()[:60] or "Brief",
                        scenes=tuple(scenes))
