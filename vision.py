"""
Per-dome vision system.

Every dome's apex PTZ camera runs simulated object detection: anything
inside the camera's current field of view (props, the player) counts as
a detection sample. Samples accumulate into a quantitative model over
time — exponential moving averages of objects in view, occupancy, and
per-type detection frequencies — the groundwork for likely-scenario
narrowing per room.
"""

from __future__ import annotations

import math

import numpy as np

import workshop

SAMPLE_PERIOD = 0.5      # seconds between detection samples
DETECT_RANGE = 40.0
EMA_ALPHA = 0.06


class VisionTracker:
    def __init__(self) -> None:
        self.timer = 0.0
        self.samples = 0
        self.ema_objects = 0.0
        self.ema_occupancy = 0.0
        self.type_counts: dict[str, int] = {}
        self.current: list[str] = []
        self.person_now = False

    def update(self, model, ptz, console, player_pos, dt: float) -> None:
        self.timer += dt
        if self.timer < SAMPLE_PERIOD or not console:
            return
        self.timer = 0.0
        self.samples += 1

        eye = np.asarray(console["ptz_eye"], dtype=np.float64)
        forward, _ = ptz.basis()
        forward = np.asarray(forward, dtype=np.float64)
        half_fov = math.radians(ptz.fov) * 0.55   # slight margin

        def in_view(point) -> bool:
            vec = np.asarray(point, dtype=np.float64) - eye
            dist = float(np.linalg.norm(vec))
            if dist < 0.3 or dist > DETECT_RANGE:
                return False
            cos_angle = float(np.dot(vec / dist, forward))
            return cos_angle > math.cos(half_fov)

        fh = model.foundation.height
        ox, oy = float(model.origin[0]), float(model.origin[1])
        seen: list[str] = []
        for entry in model.config.props:
            prop = workshop.PROP_TYPE_BY_NAME.get(entry.get("type"))
            if prop is None:
                continue
            center = (ox + float(entry["x"]), oy + float(entry["y"]),
                      fh + prop.pick_height * 0.5)
            if in_view(center):
                seen.append(entry["type"])
                self.type_counts[entry["type"]] = \
                    self.type_counts.get(entry["type"], 0) + 1

        # Player counts as a person detection when on this dome's floor.
        px, py = float(player_pos[0]) - ox, float(player_pos[1]) - oy
        person = 0.0
        self.person_now = False
        if math.hypot(px, py) <= model.floor_radius:
            if in_view((float(player_pos[0]), float(player_pos[1]),
                        fh + 0.9)):
                person = 1.0
                self.person_now = True
                seen.append("Person")
                self.type_counts["Person"] = \
                    self.type_counts.get("Person", 0) + 1

        self.current = seen
        self.ema_objects += EMA_ALPHA * (len(seen) - self.ema_objects)
        self.ema_occupancy += EMA_ALPHA * (person - self.ema_occupancy)

    def detect_text(self) -> str:
        if not self.current:
            return (f"DETECT 0 obj · avg {self.ema_objects:.1f} · "
                    f"occ {self.ema_occupancy * 100:.0f}%")
        shown = ", ".join(sorted(set(self.current))[:3])
        more = len(set(self.current)) - 3
        if more > 0:
            shown += f" +{more}"
        return (f"DETECT {len(self.current)}: {shown} · "
                f"avg {self.ema_objects:.1f} · "
                f"occ {self.ema_occupancy * 100:.0f}%")

    def summary(self) -> str:
        top = sorted(self.type_counts.items(), key=lambda kv: -kv[1])[:2]
        names = "/".join(name for name, _count in top) if top else "—"
        return (f"avg {self.ema_objects:.1f} obj · "
                f"occ {self.ema_occupancy * 100:.0f}% · top {names}")
