from abc import ABC, abstractmethod
from typing import ClassVar
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


class ActuatorDecorator(ActuatorPort):
    """Base wrapper that keeps the ``ActuatorPort`` interface and delegates inward.

    A decorator must not change ``apply``'s signature: callers should be able to
    stack any number of wrappers without knowing how many are present. Concrete
    wrappers advertise a stable policy name so the logging decorator can record
    every policy in the stack without hard-coding the composition.
    """

    policy_name: ClassVar[str] = "policy"

    def __init__(self, inner: ActuatorPort) -> None:
        self._inner = inner

    @property
    def inner(self) -> ActuatorPort:
        return self._inner

    def apply(self, device_id: UUID, command: str, payload: dict) -> None:
        self._inner.apply(device_id, command, payload)

    def policy_names(self) -> list[str]:
        """Return this wrapper and every nested wrapper, outermost first."""
        names = [self.policy_name]
        current: ActuatorPort = self._inner
        while isinstance(current, ActuatorDecorator):
            names.append(current.policy_name)
            current = current._inner
        return names
