"""Actuator lifecycle states and their guarded transitions.

Each state object owns the set of states reachable from it and the Phase 10
command names that make sense while it is active. The transition table is:

    off          -> idle, error
    idle         -> running, maintenance, off, error
    running      -> idle, error
    error        -> idle, off
    maintenance  -> idle, off, error

No state can transition to itself; repeating a command is rejected rather than
silently accepted.
"""

from abc import ABC
from typing import ClassVar

from domain.actuators.errors import IllegalTransitionError, UnknownActuatorStateError


class ActuatorState(ABC):
    """One mode of an actuator: its name, legal target states, and commands."""

    name: ClassVar[str]
    allowed_targets: ClassVar[frozenset[str]]
    commands: ClassVar[tuple[str, ...]]

    def allows(self, target: str) -> bool:
        return target in self.allowed_targets

    def allowed_commands(self) -> list[str]:
        return list(self.commands)

    def require_transition(self, target: str) -> None:
        if not self.allows(target):
            allowed = ", ".join(sorted(self.allowed_targets)) or "none"
            raise IllegalTransitionError(
                f"Cannot move an actuator from {self.name} to {target}; allowed: {allowed}"
            )


class OffState(ActuatorState):
    name = "off"
    allowed_targets = frozenset({"idle", "error"})
    commands = ("enable",)


class IdleState(ActuatorState):
    name = "idle"
    allowed_targets = frozenset({"running", "maintenance", "off", "error"})
    commands = ("start_pump", "enter_maintenance", "shutdown")


class RunningState(ActuatorState):
    name = "running"
    allowed_targets = frozenset({"idle", "error"})
    commands = ("stop_pump",)


class ErrorState(ActuatorState):
    name = "error"
    allowed_targets = frozenset({"idle", "off"})
    commands = ("reset",)


class MaintenanceState(ActuatorState):
    name = "maintenance"
    allowed_targets = frozenset({"idle", "off", "error"})
    commands = ("exit_maintenance", "shutdown")


_STATES: dict[str, ActuatorState] = {
    state.name: state
    for state in (OffState(), IdleState(), RunningState(), ErrorState(), MaintenanceState())
}

ACTUATOR_STATES: tuple[str, ...] = tuple(_STATES)


def state_for(name: str) -> ActuatorState:
    """Resolve a persisted state name to its state object."""
    try:
        return _STATES[name]
    except KeyError as exc:
        raise UnknownActuatorStateError(
            f"Unknown actuator state: {name}. Valid states: {', '.join(ACTUATOR_STATES)}"
        ) from exc
