"""Composition root for the decorated actuator port.

Order matters: ``LoggingActuatorDecorator`` is outermost, so it records one row
per logical apply, including failures raised by ``MaxRunTimeActuatorDecorator``.
Max-run-time sits immediately inside it and wraps the real adapter, so a blocked
attempt never reaches the adapter.
"""

from domain.actuators.ports import ActuatorPort
from infrastructure.adapters.actuators.logging_decorator import LoggingActuatorDecorator
from infrastructure.adapters.actuators.max_runtime_decorator import (
    MaxRunTimeActuatorDecorator,
)
from infrastructure.adapters.actuators.simulation import SimulationActuatorAdapter
from infrastructure.persistence.actuator_state_repository import ActuatorStateRepository
from infrastructure.persistence.execution_log_repository import ExecutionLogRepository


def build_actuator_port(
    *,
    states: ActuatorStateRepository,
    executions: ExecutionLogRepository,
    max_runtime_seconds: int,
    adapter: ActuatorPort | None = None,
) -> ActuatorPort:
    inner: ActuatorPort = adapter or SimulationActuatorAdapter()
    limited: ActuatorPort = MaxRunTimeActuatorDecorator(
        inner,
        states,
        max_seconds=max_runtime_seconds,
    )
    return LoggingActuatorDecorator(limited, executions)
