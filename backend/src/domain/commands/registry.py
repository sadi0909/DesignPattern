from domain.commands.base import Command
from domain.commands.errors import UnknownCommandTypeError
from domain.commands.light import SetLightLevelCommand
from domain.commands.pump import StartPumpCommand, StopPumpCommand

_COMMAND_TYPES: dict[str, type[Command]] = {
    command.command_type: command
    for command in (StartPumpCommand, StopPumpCommand, SetLightLevelCommand)
}


def create_command(command_type: str, payload: dict[str, object] | None) -> Command:
    try:
        command_class = _COMMAND_TYPES[command_type.strip().lower()]
    except KeyError as exc:
        available = ", ".join(sorted(_COMMAND_TYPES))
        raise UnknownCommandTypeError(
            f"Unknown command type: {command_type}. Available: {available}"
        ) from exc
    return command_class(payload)
