from application.devices.dto import DeviceDto
from domain.devices.entity import Device


def device_to_dto(device: Device) -> DeviceDto:
    if device.id is None:
        raise ValueError("Cannot map an unpersisted device to a DTO")
    return DeviceDto(
        id=device.id,
        device_type=device.device_type,
        role=device.role,
        device_family=device.device_family,
        display_name=device.display_name,
        default_config=device.default_config,
    )


def devices_to_dtos(devices: list[Device]) -> list[DeviceDto]:
    return [device_to_dto(device) for device in devices]
