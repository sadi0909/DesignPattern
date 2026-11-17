class UnknownCommandTypeError(ValueError):
    """Raised when a command type has no registered command object."""


class CommandRejectedError(RuntimeError):
    """Raised when State or device compatibility rejects a command before apply.

    The rejected attempt is persisted in command_log before this exception
    reaches the HTTP boundary.
    """


class CommandValidationError(ValueError):
    """Raised when a known command's payload is invalid."""
