from abc import ABC, abstractmethod
from typing import ClassVar
from uuid import UUID

from domain.actuators.ports import ActuatorPort
from domain.devices.entity import Device


class Command(ABC):
    """An actuator request as an object that can be guarded and audited."""

    command_type: ClassVar[str]
    target_state: ClassVar[str | None] = None
    supported_device_types: ClassVar[tuple[str, ...]] = ()

    def __init__(self, payload: dict[str, object] | None = None) -> None:
        self.payload = dict(payload or {})

    def supports(self, device: Device) -> bool:
        return not self.supported_device_types or device.device_type in self.supported_device_types

    @abstractmethod
    def execute(self, port: ActuatorPort, device_id: UUID) -> None:
        """Send the command through the actuator port."""
        raise NotImplementedError
