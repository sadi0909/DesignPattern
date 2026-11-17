"""Policy decorator: refuse an apply while a run has exceeded its time limit."""

from collections.abc import Callable
from datetime import UTC, datetime
from uuid import UUID

from domain.actuators.errors import MaxRunTimeExceededError
from domain.actuators.ports import ActuatorDecorator, ActuatorPort
from infrastructure.persistence.actuator_state_repository import ActuatorStateRepository


class MaxRunTimeActuatorDecorator(ActuatorDecorator):
    """Short-circuit applies for an actuator that has been ``running`` too long.

    The policy reads Phase 8's persisted state and its ``updated_at``; it never
    invents a second lifecycle. When it blocks, the inner adapter is not called.
    """

    policy_name = "maxRunTime"

    def __init__(
        self,
        inner: ActuatorPort,
        states: ActuatorStateRepository,
        max_seconds: int = 30,
        clock: Callable[[], datetime] | None = None,
    ) -> None:
        super().__init__(inner)
        if max_seconds <= 0:
            raise ValueError("max_seconds must be positive")
        self._states = states
        self._max_seconds = max_seconds
        self._clock = clock or (lambda: datetime.now(UTC))

    def apply(self, device_id: UUID, command: str, payload: dict) -> None:
        snapshot = self._states.get_snapshot(device_id)
        if snapshot is not None and snapshot.state == "running":
            updated_at = snapshot.updated_at
            if updated_at.tzinfo is None:
                updated_at = updated_at.replace(tzinfo=UTC)
            elapsed = (self._clock() - updated_at).total_seconds()
            if elapsed > self._max_seconds:
                raise MaxRunTimeExceededError(
                    f"Max run time exceeded for actuator {device_id}: "
                    f"running for {elapsed:.0f}s (limit {self._max_seconds}s)"
                )
        super().apply(device_id, command, payload)
