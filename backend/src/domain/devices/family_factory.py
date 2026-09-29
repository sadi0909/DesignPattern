from abc import ABC, abstractmethod

from domain.devices.entity import Device
from domain.sensors.creators import (
    LightSensorCreator,
    MoistureSensorCreator,
    SensorCreator,
)


class UnsupportedDeviceFamilyError(ValueError):
    """Raised when a requested device family has no registered factory."""


class DeviceFamilyFactory(ABC):
    @property
    @abstractmethod
    def family_key(self) -> str:
        """The family key assigned to every product in this kit."""
        raise NotImplementedError

    @property
    @abstractmethod
    def protocol(self) -> str:
        """The family-specific protocol hint used by its devices."""
        raise NotImplementedError

    @abstractmethod
    def create_device_set(self) -> list[Device]:
        """Create a coherent kit of sensors and actuators."""
        raise NotImplementedError

    def _create_sensor(self, creator: SensorCreator, display_name: str) -> Device:
        sensor = creator.create_sensor(display_name=display_name)
        return Device(
            id=None,
            device_type=sensor.device_type,
            role="sensor",
            device_family=self.family_key,
            display_name=sensor.display_name,
            default_config={**sensor.default_config, "protocol": self.protocol},
        )

    def _create_actuator(
        self,
        *,
        device_type: str,
        display_name: str,
        config: dict[str, object],
    ) -> Device:
        return Device(
            id=None,
            device_type=device_type,
            role="actuator",
            device_family=self.family_key,
            display_name=display_name,
            default_config={**config, "protocol": self.protocol},
        )


class SimulationDeviceFactory(DeviceFamilyFactory):
    @property
    def family_key(self) -> str:
        return "simulation"

    @property
    def protocol(self) -> str:
        return "sim"

    def create_device_set(self) -> list[Device]:
        return [
            self._create_sensor(MoistureSensorCreator(), "Simulation moisture sensor"),
            self._create_sensor(LightSensorCreator(), "Simulation light sensor"),
            self._create_actuator(
                device_type="water_pump",
                display_name="Sim irrigation pump",
                config={"default_state": "off", "max_runtime_seconds": 30},
            ),
            self._create_actuator(
                device_type="grow_light",
                display_name="Sim grow light",
                config={"default_state": "off", "dimming_supported": True},
            ),
        ]


class EdgeHardwareFactory(DeviceFamilyFactory):
    @property
    def family_key(self) -> str:
        return "edge"

    @property
    def protocol(self) -> str:
        return "gpio-stub"

    def create_device_set(self) -> list[Device]:
        return [
            self._create_sensor(MoistureSensorCreator(), "Edge moisture sensor"),
            self._create_sensor(LightSensorCreator(), "Edge light sensor"),
            self._create_actuator(
                device_type="water_pump",
                display_name="Edge irrigation pump",
                config={"default_state": "off", "max_runtime_seconds": 30, "gpio_pin": 17},
            ),
            self._create_actuator(
                device_type="grow_light",
                display_name="Edge grow light",
                config={"default_state": "off", "dimming_supported": True, "gpio_pin": 18},
            ),
        ]


_FAMILY_FACTORIES: dict[str, DeviceFamilyFactory] = {
    "simulation": SimulationDeviceFactory(),
    "edge": EdgeHardwareFactory(),
}


def get_family_factory(family: str) -> DeviceFamilyFactory:
    key = family.strip().lower()
    try:
        return _FAMILY_FACTORIES[key]
    except KeyError as exc:
        raise UnsupportedDeviceFamilyError(f"Unsupported device family: {family}") from exc
