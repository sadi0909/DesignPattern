"""Sensor adapter selection rule (documented in docs/patterns/adapter.md).

Rule: an explicit ``default_config["protocol"]`` wins
(``sim`` -> SimulationSensorAdapter, ``gpio-stub`` -> VendorStubSensorAdapter);
otherwise fall back to ``device_family`` (``simulation`` -> simulation adapter,
``edge`` -> vendor-stub adapter). This is the only place outside the adapters
themselves that knows concrete adapter classes.
"""

from domain.devices.entity import Device
from domain.sensors.errors import SensorReadError
from domain.sensors.ports import SensorPort

from .simulation import SimulationSensorAdapter
from .vendor_stub import VendorStubSensorAdapter

_BY_PROTOCOL: dict[str, type[SensorPort]] = {
    "sim": SimulationSensorAdapter,
    "simulation": SimulationSensorAdapter,
    "gpio-stub": VendorStubSensorAdapter,
    "vendor": VendorStubSensorAdapter,
    "vendor-stub": VendorStubSensorAdapter,
}

_BY_FAMILY: dict[str, type[SensorPort]] = {
    "simulation": SimulationSensorAdapter,
    "edge": VendorStubSensorAdapter,
}


def select_sensor_adapter(device: Device) -> SensorPort:
    """Return the adapter that speaks to this device's driver."""
    protocol = str(device.default_config.get("protocol", "")).strip().lower()
    if protocol:
        try:
            return _BY_PROTOCOL[protocol]()
        except KeyError as exc:
            raise SensorReadError(f"No sensor adapter registered for protocol {protocol!r}") from exc

    family = device.device_family.strip().lower()
    adapter_type = _BY_FAMILY.get(family)
    if adapter_type is None:
        raise SensorReadError(f"No sensor adapter registered for device family {family!r}")
    return adapter_type()
