"""Vendor-stub sensor driver adapter.

The mocked vendor SDK returns a raw payload that is deliberately shaped
differently from the domain: nested objects, odd field names, scaled integer
readings, vendor unit codes, and epoch milliseconds. ``translate`` converts
that raw shape into the normalized Reading. Translation only — irrigation
policy stays outside the adapter (Phase 6 Strategy).
"""

import random
import time
from datetime import UTC, datetime

from domain.devices.entity import Device
from domain.sensors.errors import SensorReadError
from domain.sensors.ports import SensorPort
from domain.sensors.reading import Reading

# Vendor raw readings are integers in tenths of the vendor unit code.
# Multipliers convert them to the normalized unit (percent / lux).
_UNIT_BY_VENDOR_CODE: dict[str, tuple[str, float]] = {
    "PCT": ("percent", 0.1),  # deci-percent -> percent
    "KLX": ("lux", 100.0),  # tenths of kilolux -> lux
}

_RAW_RANGES: dict[str, tuple[int, int]] = {
    "moisture_sensor": (200, 600),  # -> 20.0 .. 60.0 percent
    "light_sensor": (50, 500),  # -> 5000 .. 50000 lux
}


class VendorStubSensorAdapter(SensorPort):
    """Wraps the mocked vendor driver and speaks SensorPort to clients.

    ``source`` is always "vendor" so persisted history can tell which
    adapter produced a reading.
    """

    source = "vendor"

    def read(self, device: Device) -> Reading:
        if device.id is None:
            raise SensorReadError("Cannot read a device that has not been persisted")
        raw = self._fetch_raw(device)
        return self.translate(device, raw)

    @staticmethod
    def translate(device: Device, raw: dict) -> Reading:
        """Translate one raw vendor payload into a normalized Reading.

        Pure translation: field names, scaling, unit codes, timestamps.
        Kept side-effect free so unit tests can pass raw payloads directly.
        """
        if device.id is None:
            raise SensorReadError("Cannot read a device that has not been persisted")

        sample = raw.get("sample")
        if not isinstance(sample, dict):
            raise SensorReadError("Vendor payload is missing the 'sample' object")

        reading_tenths = sample.get("reading_tenths")
        if isinstance(reading_tenths, bool) or not isinstance(reading_tenths, (int, float)):
            raise SensorReadError("Vendor payload field 'sample.reading_tenths' is missing or not numeric")

        uom_code = sample.get("uom_code")
        if not isinstance(uom_code, str) or uom_code not in _UNIT_BY_VENDOR_CODE:
            raise SensorReadError(f"Unknown vendor unit code: {uom_code!r}")
        unit, multiplier = _UNIT_BY_VENDOR_CODE[uom_code]

        captured_epoch_ms = raw.get("captured_epoch_ms")
        if isinstance(captured_epoch_ms, bool) or not isinstance(captured_epoch_ms, (int, float)):
            raise SensorReadError("Vendor payload field 'captured_epoch_ms' is missing or not numeric")

        return Reading(
            device_id=device.id,
            value=float(reading_tenths) * multiplier,
            unit=unit,
            source="vendor",
            recorded_at=datetime.fromtimestamp(captured_epoch_ms / 1000, tz=UTC),
        )

    def _fetch_raw(self, device: Device) -> dict:
        """Stubbed vendor SDK call — returns the vendor's raw sample shape."""
        if device.device_type == "moisture_sensor":
            low, high = _RAW_RANGES["moisture_sensor"]
            uom_code = "PCT"
        elif device.device_type == "light_sensor":
            low, high = _RAW_RANGES["light_sensor"]
            uom_code = "KLX"
        else:
            raise SensorReadError(f"Vendor stub has no driver for device type {device.device_type!r}")
        return {
            "probe_sn": f"VND-{device.id!s}"[:16],
            "sample": {
                "reading_tenths": random.randint(low, high),
                "uom_code": uom_code,
            },
            "captured_epoch_ms": int(time.time() * 1000),
        }
