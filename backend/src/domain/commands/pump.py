from uuid import UUID

from domain.actuators.ports import ActuatorPort
from domain.commands.base import Command


class StartPumpCommand(Command):
    command_type = "start_pump"
    target_state = "running"
    supported_device_types = ("water_pump",)

    def execute(self, port: ActuatorPort, device_id: UUID) -> None:
        port.apply(device_id, self.command_type, self.payload)


class StopPumpCommand(Command):
    command_type = "stop_pump"
    target_state = "idle"
    supported_device_types = ("water_pump",)

    def execute(self, port: ActuatorPort, device_id: UUID) -> None:
        port.apply(device_id, self.command_type, self.payload)
