"""Document model for a presentation: scenes, shots, overlays.

A Presentation is pure data. The engine evaluates it deterministically at
any absolute time t, so live preview and video export show identical
frames. Durations are *minimums*: when narration is enabled, each shot is
stretched to fit its measured speech.
"""

from __future__ import annotations

import json
from dataclasses import dataclass, field, asdict
from pathlib import Path

LENSES = {
    # name: (fov degrees, framing factor — multiplies the snap-to distance)
    "macro":     (21.0, 0.52),
    "portrait":  (34.0, 1.05),
    "wide":      (58.0, 1.45),
    "ultrawide": (92.0, 2.10),
}
PERSPECTIVES = (1, 2, 3, 4, 5, 6)   # 1-3 linear, 4 cylindrical,
                                    # 5 fisheye 180, 6 azimuthal 360


@dataclass
class OverlayPanel:
    """The floatable / hidable 2-D second screen."""
    title: str = ""
    bullets: tuple = ()
    equations: tuple = ()
    stats: tuple = ()            # (label, value) pairs
    position: str = "right"      # right | left | bottom | float
    anchor: tuple = (0.62, 0.10)  # when position == "float": fractional x, y
    visible: bool = True


@dataclass
class Shot:
    slug: str = "shot"
    duration: float = 6.0        # minimum seconds; narration may stretch it
    lens: str = "wide"
    perspective: int = 3
    focus: str = ""              # object name to snap to ("" = scene origin)
    orbit: float = 12.0          # slow orbit degrees across the shot
    dolly: float = 0.0           # fractional distance change across the shot
    yaw: float = -55.0           # start yaw (degrees)
    pitch: float = 18.0          # start pitch (degrees)
    height_bias: float = 0.0     # raises/lowers the look-at point
    narration: tuple = ()        # lines spoken over this shot
    caption: str = ""            # lower-third caption
    panel: OverlayPanel | None = None
    actions: tuple = ()          # (object, param, value_from, value_to)
    xray: bool = False           # render shell layers translucent

    def action_value(self, obj: str, param: str, progress: float,
                     default: float = 0.0) -> float:
        for a in self.actions:
            if a[0] == obj and a[1] == param:
                lo, hi = float(a[2]), float(a[3])
                return lo + (hi - lo) * max(0.0, min(1.0, progress))
        return default


@dataclass
class Scene:
    slug: str = "scene"
    title: str = ""
    environment: str = ""        # free-text prompt, parsed by prompt.py
    shots: tuple = ()
    world: tuple = ()            # extra (object, params) declarations

    @property
    def duration(self) -> float:
        return sum(s.duration for s in self.shots)


@dataclass
class Presentation:
    title: str = "Untitled"
    author: str = ""
    scenes: tuple = ()
    fps: int = 30
    size: tuple = (1920, 1080)
    voice: str = "en-US-AndrewMultilingualNeural"
    voice_rate: str = "-3%"

    # ---- timeline -----------------------------------------------------

    def all_shots(self) -> list[tuple[Scene, Shot]]:
        return [(scene, shot) for scene in self.scenes
                for shot in scene.shots]

    @property
    def duration(self) -> float:
        return sum(scene.duration for scene in self.scenes)

    def shot_at(self, t: float) -> tuple[int, float]:
        """(flat shot index, 0..1 progress) for looped timeline t."""
        pairs = self.all_shots()
        total = max(1e-6, self.duration)
        t %= total
        cursor = 0.0
        for i, (_scene, shot) in enumerate(pairs):
            if t < cursor + shot.duration:
                return i, (t - cursor) / max(1e-6, shot.duration)
            cursor += shot.duration
        return len(pairs) - 1, 1.0

    def shot_start(self, index: int) -> float:
        pairs = self.all_shots()
        return sum(s.duration for _sc, s in pairs[:index])

    def scene_of(self, flat_index: int) -> Scene:
        n = 0
        for scene in self.scenes:
            if flat_index < n + len(scene.shots):
                return scene
            n += len(scene.shots)
        return self.scenes[-1]

    # ---- (de)serialization -------------------------------------------

    def to_json(self, path: Path) -> None:
        payload = asdict(self)
        Path(path).write_text(json.dumps(payload, indent=2),
                              encoding="utf-8")

    @staticmethod
    def from_json(path: Path) -> "Presentation":
        raw = json.loads(Path(path).read_text(encoding="utf-8"))

        def panel(p):
            if not p:
                return None
            p = dict(p)
            for k in ("bullets", "equations"):
                p[k] = tuple(p.get(k) or ())
            p["stats"] = tuple(tuple(s) for s in p.get("stats") or ())
            p["anchor"] = tuple(p.get("anchor") or (0.62, 0.10))
            return OverlayPanel(**p)

        def shot(s):
            s = dict(s)
            s["narration"] = tuple(s.get("narration") or ())
            s["actions"] = tuple(tuple(a) for a in s.get("actions") or ())
            s["panel"] = panel(s.get("panel"))
            return Shot(**s)

        def scene(sc):
            sc = dict(sc)
            sc["shots"] = tuple(shot(s) for s in sc.get("shots") or ())
            sc["world"] = tuple(
                (w[0], dict(w[1])) for w in sc.get("world") or ())
            return Scene(**sc)

        raw["scenes"] = tuple(scene(sc) for sc in raw.get("scenes") or ())
        raw["size"] = tuple(raw.get("size") or (1920, 1080))
        return Presentation(**raw)

    def validate(self) -> None:
        assert self.scenes, "presentation has no scenes"
        for scene in self.scenes:
            assert scene.shots, f"scene {scene.slug} has no shots"
            for shot in scene.shots:
                assert shot.lens in LENSES, f"unknown lens {shot.lens}"
                assert shot.perspective in PERSPECTIVES, \
                    f"unknown perspective {shot.perspective}"
                assert shot.duration > 0.5, "shots must be > 0.5 s"
