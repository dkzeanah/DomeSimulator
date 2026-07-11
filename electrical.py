"""
Live electrical system simulation across all domes on the site.

One shared battery bank + charge controller serves every dome (the tie
that links dome 1 and dome 2). Solar comes from Solar Panel shell
panels on any dome; loads come from powered-on devices plugged into
outlets. Battery dynamics run at an accelerated time factor so charge
and drain are visible while you play.
"""

from __future__ import annotations

import math

import workshop

BATTERY_KWH_EACH = 10.0
SUN_FACTOR = 0.75              # average irradiance vs nameplate
OUTLET_REACH = 3.0             # cord length from an outlet, meters
TIME_FACTOR = 600.0            # 1 real second = 10 simulated minutes


class ElectricalSystem:
    def __init__(self) -> None:
        self.charge_kwh = 6.0
        self.capacity_kwh = 0.0
        self.solar_watts = 0.0
        self.solar_by_dome: list[float] = []
        self.load_by_dome: list[float] = []
        self.lights_by_dome: list[int] = []
        self.has_system = False
        self.battery_empty = False

    @staticmethod
    def _outlet_positions(model) -> list[tuple[float, float]]:
        out = []
        for entry in model.config.props:
            prop = workshop.PROP_TYPE_BY_NAME.get(entry.get("type"))
            if prop is not None and prop.role in ("outlet", "battery",
                                                  "controller"):
                out.append((float(entry["x"]), float(entry["y"])))
        return out

    @classmethod
    def device_connected(cls, model, entry, has_system: bool) -> bool:
        """A device is powered if plugged into an outlet in reach —
        or freely, when no battery system exists anywhere (standalone
        generator / extension-cord mode)."""
        if not has_system:
            return True
        ex, ey = float(entry["x"]), float(entry["y"])
        for px, py in cls._outlet_positions(model):
            if math.hypot(ex - px, ey - py) <= OUTLET_REACH:
                return True
        return False

    def update(self, models: list, dt: float) -> None:
        banks = 0
        for model in models:
            for entry in model.config.props:
                prop = workshop.PROP_TYPE_BY_NAME.get(entry.get("type"))
                if prop is not None and prop.role == "battery":
                    banks += 1
        self.has_system = banks > 0
        self.capacity_kwh = banks * BATTERY_KWH_EACH

        self.solar_by_dome = []
        self.load_by_dome = []
        self.lights_by_dome = []
        for model in models:
            solar = sum(
                p.area * p.panel_type.watts_per_m2 for p in model.panels
            ) * SUN_FACTOR
            self.solar_by_dome.append(solar)

            load = 0.0
            lights = 0
            for entry in model.config.props:
                prop = workshop.PROP_TYPE_BY_NAME.get(entry.get("type"))
                if prop is None or prop.watts <= 0:
                    continue
                if not entry.get("on", True):
                    continue
                if not self.device_connected(model, entry,
                                             self.has_system):
                    continue
                load += prop.watts
                if prop.light_z is not None:
                    lights += 1
            self.load_by_dome.append(load)
            self.lights_by_dome.append(lights)

        self.solar_watts = sum(self.solar_by_dome)

        if self.has_system:
            usable_load = 0.0 if self.battery_empty else \
                sum(self.load_by_dome)
            net_watts = self.solar_watts - usable_load
            self.charge_kwh += net_watts / 1000.0 * \
                (dt * TIME_FACTOR / 3600.0)
            self.charge_kwh = min(max(self.charge_kwh, 0.0),
                                  self.capacity_kwh)
            self.battery_empty = self.charge_kwh <= 1e-6 and \
                self.solar_watts < sum(self.load_by_dome)
        else:
            self.battery_empty = False

    @property
    def net_watts(self) -> float:
        load = 0.0 if self.battery_empty else sum(self.load_by_dome)
        return self.solar_watts - load

    def charge_fraction(self) -> float:
        if self.capacity_kwh <= 0:
            return 0.0
        return self.charge_kwh / self.capacity_kwh

    def lamps_powered(self, model, entry) -> bool:
        """Should this lamp actually emit light right now?"""
        if not entry.get("on", True):
            return False
        if not self.has_system:
            return True
        if self.battery_empty:
            return False
        return self.device_connected(model, entry, True)
