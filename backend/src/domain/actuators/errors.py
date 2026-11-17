class IllegalTransitionError(ValueError):
    """Raised when a command would move an actuator to a state its current state forbids.

    Maps to HTTP 409 at the API boundary; nothing is persisted.
    """


class UnknownActuatorStateError(ValueError):
    """Raised when a state name is not part of the actuator lifecycle.

    Maps to HTTP 400 at the API boundary.
    """


class ActuatorPolicyBlockedError(RuntimeError):
    """Raised when a policy decorator refuses a command before the adapter runs.

    Decorators short-circuit on purpose; the logging wrapper still records the
    attempt as unsuccessful with the policy names attached. Maps to HTTP 409.
    """


class MaxRunTimeExceededError(ActuatorPolicyBlockedError):
    """Raised when an actuator has been running longer than the configured limit."""
