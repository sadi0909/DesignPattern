class IllegalTransitionError(ValueError):
    """Raised when a command would move an actuator to a state its current state forbids.

    Maps to HTTP 409 at the API boundary; nothing is persisted.
    """


class UnknownActuatorStateError(ValueError):
    """Raised when a state name is not part of the actuator lifecycle.

    Maps to HTTP 400 at the API boundary.
    """
