from abc import ABC, abstractmethod
from uuid import UUID


class ActuatorPort(ABC):
    """Application-facing actuator interface (the Adapter "target").

    Phase 5 ships only a simulation adapter (log/in-memory apply, no GPIO).
    Phase 9 wraps implementations of this port with decorators, and Phase 10
    sends encapsulated commands through it.
    """

    @abstractmethod
    def apply(self, device_id: UUID, command: str, payload: dict) -> None:
        """Apply one command to the device. Translation and apply only —
        irrigation policy stays outside the adapter."""
        raise NotImplementedError
