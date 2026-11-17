from uuid import UUID

from domain.devices.entity import Device
from domain.devices.errors import DeviceNotFoundError
from domain.locations.errors import LocationNotFoundError
from infrastructure.persistence.device_repository import DeviceRepository
from infrastructure.persistence.location_repository import LocationRepository


class DeviceLocationService:
    """Assign or clear the optional location on an existing device."""

    def __init__(self, devices: DeviceRepository, locations: LocationRepository) -> None:
        self._devices = devices
        self._locations = locations

    def assign(self, device_id: UUID, location_id: UUID | None) -> Device:
        if self._devices.get_device(device_id) is None:
            raise DeviceNotFoundError(f"Device {device_id} does not exist")
        if location_id is not None and not self._locations.exists(location_id):
            raise LocationNotFoundError(f"Location {location_id} does not exist")
        return self._devices.assign_location(device_id, location_id)
