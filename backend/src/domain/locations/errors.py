class ConfigurationError(ValueError):
    """Raised when a location configuration cannot form a valid aggregate."""


class LocationNotFoundError(LookupError):
    """Raised when a location id does not exist."""
