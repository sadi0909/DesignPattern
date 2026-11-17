"""Outermost actuator decorator: persist the outcome of every apply attempt."""

from uuid import UUID

from domain.actuators.ports import ActuatorDecorator, ActuatorPort
from infrastructure.persistence.execution_log_repository import ExecutionLogRepository


class LoggingActuatorDecorator(ActuatorDecorator):
    """Record every attempt, including short-circuited policy failures.

    Logging sits outermost so it sees both successful calls and exceptions raised
    by inner decorators. ``policy_names()`` walks the stack, so a newly added
    wrapper appears in ``policy_applied`` without editing this class.
    """

    policy_name = "logging"

    def __init__(self, inner: ActuatorPort, executions: ExecutionLogRepository) -> None:
        super().__init__(inner)
        self._executions = executions

    def apply(self, device_id: UUID, command: str, payload: dict) -> None:
        # Inner policies run first, so list them that way in the stored row.
        policy_applied = list(reversed(self.policy_names()))
        try:
            super().apply(device_id, command, payload)
        except Exception as exc:
            self._executions.record(
                device_id,
                success=False,
                policy_applied=policy_applied,
                message=str(exc) or exc.__class__.__name__,
            )
            raise
        self._executions.record(
            device_id,
            success=True,
            policy_applied=policy_applied,
            message=None,
        )
