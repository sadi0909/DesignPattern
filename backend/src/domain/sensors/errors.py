class SensorReadError(ValueError):
    """Raised when a sensor adapter cannot produce a normalized reading.

    Examples: a malformed vendor payload, an unknown vendor unit code, or a
    device type the simulation driver cannot simulate. Maps to HTTP 400.
    """
