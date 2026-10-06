"""Simulation actuator driver adapter.

Stub apply: records the command intent in memory and logs it — no GPIO and no
physical output. Phase 9 wraps this class (importable from
``infrastructure.adapters.actuators.simulation``) with decorators.
"""

import logging
from dataclasses import dataclass, field
from uuid import UUID

from domain.actuators.ports import ActuatorPort

logger = logging.getLogger(__name__)


@dataclass(frozen=True, slots=True)
class AppliedCommand:
    """One recorded command intent."""

    device_id: UUID
    command: str
    payload: dict = field(default_factory=dict)


class SimulationActuatorAdapter(ActuatorPort):
    """Mocked actuator driver: log-only apply, with an in-memory history."""

    def __init__(self) -> None:
        self.applied: list[AppliedCommand] = []

    def apply(self, device_id: UUID, command: str, payload: dict) -> None:
        intent = AppliedCommand(device_id=device_id, command=command, payload=dict(payload))
        self.applied.append(intent)
        logger.info(
            "Simulation actuator apply: device=%s command=%s payload=%s",
            device_id,
            command,
            payload,
        )
