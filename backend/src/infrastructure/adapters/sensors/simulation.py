"""Simulation sensor driver adapter.

Produces plausible synthetic values for the mocked device drivers — no lab
hardware required. This is one of the two Phase 5 adaptees behind SensorPort.
"""

import random
from datetime import UTC, datetime

from domain.devices.entity import Device
from domain.sensors.errors import SensorReadError
from domain.sensors.ports import SensorPort
from domain.sensors.reading import Reading

_UNIT_BY_DEVICE_TYPE: dict[str, str] = {
    "moisture_sensor": "percent",
    "light_sensor": "lux",
}

_VALUE_RANGES: dict[str, tuple[float, float]] = {
    "moisture_sensor": (20.0, 80.0),
    "light_sensor": (500.0, 50000.0),
}


class SimulationSensorAdapter(SensorPort):
    """Mocked device driver: plausible values, normalized to Reading.

    ``source`` is always "simulation" so persisted history can tell which
    adapter produced a reading.
    """

    source = "simulation"

    def read(self, device: Device) -> Reading:
        if device.id is None:
            raise SensorReadError("Cannot read a device that has not been persisted")
        unit = self._unit_for(device)
        low, high = self._range_for(device)
        return Reading(
            device_id=device.id,
            value=round(random.uniform(low, high), 2),
            unit=unit,
            source=self.source,
            recorded_at=datetime.now(UTC),
        )

    @staticmethod
    def _unit_for(device: Device) -> str:
        configured = device.default_config.get("unit")
        if isinstance(configured, str) and configured.strip():
            return configured.strip()
        unit = _UNIT_BY_DEVICE_TYPE.get(device.device_type)
        if unit is None:
            raise SensorReadError(f"Simulation driver has no unit for device type {device.device_type!r}")
        return unit

    @staticmethod
    def _range_for(device: Device) -> tuple[float, float]:
        value_range = _VALUE_RANGES.get(device.device_type)
        if value_range is None:
            raise SensorReadError(f"Simulation driver cannot simulate device type {device.device_type!r}")
        return value_range
