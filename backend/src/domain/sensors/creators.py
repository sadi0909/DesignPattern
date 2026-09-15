from abc import ABC, abstractmethod

from .entity import Sensor


class SensorCreator(ABC):
    @abstractmethod
    def create_sensor(self, display_name: str | None = None) -> Sensor:
        """Create one configured sensor product."""
        raise NotImplementedError


class MoistureSensorCreator(SensorCreator):
    def create_sensor(self, display_name: str | None = None) -> Sensor:
        return Sensor(
            id=None,
            device_type="moisture_sensor",
            display_name=display_name or "Moisture Sensor",
            default_config={
                "unit": "percent",
                "sampling_interval_seconds": 300,
                "moisture_threshold_percent": 30,
            },
        )


class LightSensorCreator(SensorCreator):
    def create_sensor(self, display_name: str | None = None) -> Sensor:
        return Sensor(
            id=None,
            device_type="light_sensor",
            display_name=display_name or "Light Sensor",
            default_config={
                "unit": "lux",
                "sampling_interval_seconds": 60,
                "low_light_threshold_lux": 10000,
            },
        )


CREATORS: dict[str, SensorCreator] = {
    "moisture": MoistureSensorCreator(),
    "light": LightSensorCreator(),
}


def get_creator(sensor_type: str) -> SensorCreator:
    try:
        return CREATORS[sensor_type.strip().lower()]
    except KeyError as exc:
        raise ValueError(f"Unsupported sensor type: {sensor_type}") from exc
