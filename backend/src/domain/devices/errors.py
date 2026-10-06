class DeviceNotFoundError(LookupError):
    """Raised when a use case references a device that does not exist.

    Maps to HTTP 404 at the API boundary.
    """
