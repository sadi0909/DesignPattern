from uuid import UUID

from domain.actuators.context import ActuatorContext
from domain.actuators.ports import ActuatorPort
from domain.commands.errors import CommandRejectedError
from domain.commands.log import CommandLog
from domain.commands.registry import create_command
from domain.devices.errors import DeviceNotFoundError
from infrastructure.persistence.actuator_state_repository import ActuatorStateRepository
from infrastructure.persistence.command_log_repository import CommandLogRepository
from infrastructure.persistence.device_repository import DeviceRepository


class CommandService:
    """Invoker for actuator commands.

    It resolves a command object, checks State and device compatibility, runs the
    existing decorated port, advances the lifecycle only after apply succeeds,
    and records both successful and unsuccessful attempts in command_log.
    """

    def __init__(
        self,
        devices: DeviceRepository,
        states: ActuatorStateRepository,
        port: ActuatorPort,
        logs: CommandLogRepository,
    ) -> None:
        self._devices = devices
        self._states = states
        self._port = port
        self._logs = logs

    def submit(
        self,
        device_id: UUID,
        command_type: str,
        payload: dict[str, object] | None = None,
    ) -> CommandLog:
        command = create_command(command_type, payload)
        device = self._devices.get_device(device_id)
        if device is None or device.role != "actuator":
            raise DeviceNotFoundError(f"Actuator {device_id} does not exist")

        current_state = self._states.get_state(device_id) or device.state or "idle"
        context = ActuatorContext.from_name(device_id, current_state)

        if not command.supports(device):
            return self._reject(
                command.command_type,
                device_id,
                command.payload,
                f"{command.command_type} is not valid for {device.device_type}",
            )
        if command.command_type not in context.allowed_commands():
            return self._reject(
                command.command_type,
                device_id,
                command.payload,
                f"{command.command_type} is not allowed in state {context.state_name}",
            )
        if command.target_state is not None and not context.can_transition_to(command.target_state):
            return self._reject(
                command.command_type,
                device_id,
                command.payload,
                f"Cannot transition from {context.state_name} to {command.target_state}",
            )

        try:
            command.execute(self._port, device_id)
            if command.target_state is not None:
                context.transition(command.target_state)
                self._states.save_state(device_id, context.state_name)
        except Exception as exc:
            message = str(exc) or exc.__class__.__name__
            self._logs.record(
                command_type=command.command_type,
                device_id=device_id,
                payload=command.payload,
                status="failed",
                error_message=message,
            )
            raise

        return self._logs.record(
            command_type=command.command_type,
            device_id=device_id,
            payload=command.payload,
            status="success",
        )

    def list_commands(self, limit: int = 50) -> list[CommandLog]:
        return self._logs.list_recent(limit)

    def _reject(
        self,
        command_type: str,
        device_id: UUID,
        payload: dict[str, object],
        message: str,
    ) -> CommandLog:
        self._logs.record(
            command_type=command_type,
            device_id=device_id,
            payload=payload,
            status="rejected",
            error_message=message,
        )
        raise CommandRejectedError(message)
