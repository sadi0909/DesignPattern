from uuid import UUID

from domain.actuators.ports import ActuatorPort
from domain.commands.base import Command
from domain.commands.errors import CommandValidationError


class SetLightLevelCommand(Command):
    command_type = "set_light_level"
    supported_device_types = ("grow_light",)

    def __init__(self, payload: dict[str, object] | None = None) -> None:
        super().__init__(payload)
        level = self.payload.get("level")
        if (
            isinstance(level, bool)
            or not isinstance(level, (int, float))
            or not 0 <= float(level) <= 100
        ):
            raise CommandValidationError(
                "set_light_level requires a numeric payload.level between 0 and 100"
            )

    def execute(self, port: ActuatorPort, device_id: UUID) -> None:
        port.apply(device_id, self.command_type, self.payload)
