from uuid import UUID

from domain.devices.entity import Device
from domain.devices.errors import DeviceNotFoundError
from domain.devices.family_factory import get_family_factory
from infrastructure.persistence.device_repository import DeviceRepository


class DeviceFamilyService:
    def __init__(self, repository: DeviceRepository) -> None:
        self._repository = repository

    def provision_family(self, family: str) -> list[Device]:
        factory = get_family_factory(family)
        return self._repository.save_devices(factory.create_device_set())

    def list_devices(self, *, family: str | None = None, role: str | None = None) -> list[Device]:
        return self._repository.list_devices(device_family=family, role=role)

    def get_device(self, device_id: UUID) -> Device:
        device = self._repository.get_device(device_id)
        if device is None:
            raise DeviceNotFoundError(f"Device {device_id} does not exist")
        return device
