from collections.abc import Callable
from uuid import UUID

from application.readings.dto import ReadingDto
from domain.devices.entity import Device
from domain.devices.errors import DeviceNotFoundError
from domain.events.bus import EventBus
from domain.events.events import ReadingTaken
from domain.sensors.ports import SensorPort
from domain.sensors.reading import Reading
from infrastructure.adapters.sensors.selector import select_sensor_adapter
from infrastructure.persistence.device_repository import DeviceRepository
from infrastructure.persistence.reading_repository import ReadingRepository

AdapterFactory = Callable[[Device], SensorPort]


class ReadingService:
    """Use case: resolve device -> pick adapter -> read -> persist -> DTO.

    Depends on the SensorPort abstraction; concrete adapters enter only
    through the selector (the one allowed seam to infrastructure adapters).
    """

    def __init__(
        self,
        devices: DeviceRepository,
        readings: ReadingRepository,
        adapter_selector: AdapterFactory = select_sensor_adapter,
        events: EventBus | None = None,
    ) -> None:
        self._devices = devices
        self._readings = readings
        self._adapter_selector = adapter_selector
        self._events = events

    def take_reading(self, device_id: UUID) -> ReadingDto:
        device = self._require_device(device_id)
        port = self._adapter_selector(device)
        reading = port.read(device)  # adapter errors surface as SensorReadError
        persisted = self._readings.insert(reading)
        if self._events is not None:
            # Publish only after the reading is durable; subscribers may react
            # to it (and open their own units of work) without changing the
            # reading pipeline.
            self._events.publish(
                ReadingTaken(
                    device_id=persisted.device_id,
                    location_id=device.location_id,
                    sensor_type=device.device_type,
                    value=persisted.value,
                    unit=persisted.unit,
                )
            )
        return self._to_dto(persisted)

    def list_readings(self, device_id: UUID, limit: int = 20) -> list[ReadingDto]:
        self._require_device(device_id)
        return [self._to_dto(reading) for reading in self._readings.list_for_device(device_id, limit=limit)]

    def _require_device(self, device_id: UUID) -> Device:
        device = self._devices.get_device(device_id)
        if device is None:
            raise DeviceNotFoundError(f"Device {device_id} does not exist")
        return device

    @staticmethod
    def _to_dto(reading: Reading) -> ReadingDto:
        return ReadingDto(
            device_id=reading.device_id,
            value=reading.value,
            unit=reading.unit,
            source=reading.source,
            recorded_at=reading.recorded_at,
        )
