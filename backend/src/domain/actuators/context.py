from dataclasses import dataclass
from uuid import UUID

from domain.actuators.state import ActuatorState, state_for


@dataclass(slots=True)
class ActuatorContext:
    """Holds the current state and delegates commands to it.

    The context is pure: it never touches the database, HTTP, or vendor APIs.
    Loading and saving the state name are application/infrastructure concerns.
    """

    device_id: UUID
    state: ActuatorState

    @classmethod
    def from_name(cls, device_id: UUID, state_name: str) -> "ActuatorContext":
        return cls(device_id=device_id, state=state_for(state_name))

    @property
    def state_name(self) -> str:
        return self.state.name

    def allowed_commands(self) -> list[str]:
        return self.state.allowed_commands()

    def can_transition_to(self, target: str) -> bool:
        return self.state.allows(target)

    def transition(self, target: str) -> str:
        """Move to ``target`` when the current state allows it.

        An unknown target raises ``UnknownActuatorStateError``; a known but
        illegal edge raises ``IllegalTransitionError``. In both cases the
        context keeps its current state.
        """
        next_state = state_for(target)
        self.state.require_transition(next_state.name)
        self.state = next_state
        return next_state.name
