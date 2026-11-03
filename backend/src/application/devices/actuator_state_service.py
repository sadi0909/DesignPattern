from dataclasses import replace
from uuid import UUID

from domain.actuators.context import ActuatorContext
from domain.devices.entity import Device
from domain.devices.errors import DeviceNotFoundError
from infrastructure.persistence.actuator_state_repository import ActuatorStateRepository
from infrastructure.persistence.device_repository import DeviceRepository


class ActuatorStateService:
    """Load a persisted actuator state, guard the transition, then save it."""

    def __init__(
        self,
        devices: DeviceRepository,
        states: ActuatorStateRepository,
    ) -> None:
        self._devices = devices
        self._states = states

    def get_actuator(self, device_id: UUID) -> Device:
        device = self._devices.get_device(device_id)
        if device is None or device.role != "actuator":
            raise DeviceNotFoundError(f"Actuator {device_id} does not exist")
        return device

    def transition(self, device_id: UUID, target: str) -> Device:
        device = self.get_actuator(device_id)
        # Prefer the state table; the joined device value is the same in normal
        # operation. A missing row can only come from data created outside the
        # app, whose effective state before the first transition is idle.
        current_state = self._states.get_state(device_id) or device.state or "idle"
        context = ActuatorContext.from_name(device_id, current_state)
        context.transition(target)
        self._states.save_state(device_id, context.state_name)
        return replace(device, state=context.state_name)
