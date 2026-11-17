from uuid import UUID

from domain.actuators.execution import ActuatorExecution
from domain.actuators.ports import ActuatorPort
from domain.devices.errors import DeviceNotFoundError
from infrastructure.persistence.device_repository import DeviceRepository
from infrastructure.persistence.execution_log_repository import ExecutionLogRepository


class ActuatorExecutionService:
    """Applies commands through the decorated port and reads the execution log.

    The service depends only on the ``ActuatorPort`` interface; it does not know
    how many decorators are stacked around the simulation adapter.
    """

    def __init__(
        self,
        devices: DeviceRepository,
        port: ActuatorPort,
        executions: ExecutionLogRepository,
    ) -> None:
        self._devices = devices
        self._port = port
        self._executions = executions

    def apply(self, device_id: UUID, command: str, payload: dict) -> None:
        device = self._devices.get_device(device_id)
        if device is None or device.role != "actuator":
            raise DeviceNotFoundError(f"Actuator {device_id} does not exist")
        self._port.apply(device_id, command, payload)

    def list_executions(self, limit: int = 20) -> list[ActuatorExecution]:
        return self._executions.list_recent(limit)
