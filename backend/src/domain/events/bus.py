"""In-process publish/subscribe bus (Observer subject).

The bus owns the subscriber list. Publishers call :meth:`EventBus.publish`
and never import concrete subscribers such as the alert repository or the
future WebSocket bridge.
"""

import logging
from collections.abc import Callable
from typing import Any

Handler = Callable[[Any], None]


class EventBus:
    """Synchronous Observer subject keyed by event class.

    Subscriptions are matched with ``isinstance`` semantics, so subscribing to
    :class:`~domain.events.events.DomainEvent` receives every event. Handlers
    run in registration order and a failing handler is logged and isolated so
    later subscribers (metrics, Phase 12 WebSocket) still receive the event.
    """

    def __init__(self) -> None:
        self._handlers: dict[type, list[Handler]] = {}
        self._logger = logging.getLogger(__name__)

    def subscribe(self, event_type: type, handler: Handler) -> Callable[[], None]:
        """Register ``handler`` for ``event_type`` and return an unsubscribe callable."""
        self._handlers.setdefault(event_type, []).append(handler)
        return lambda: self.unsubscribe(event_type, handler)

    def unsubscribe(self, event_type: type, handler: Handler) -> None:
        handlers = self._handlers.get(event_type)
        if handlers is None:
            return
        try:
            handlers.remove(handler)
        except ValueError:
            return
        if not handlers:
            self._handlers.pop(event_type, None)

    def publish(self, event: object) -> None:
        """Notify every subscriber of ``event``; one failure never aborts the fan-out."""
        delivered: set[int] = set()
        for event_type in type(event).__mro__:
            for handler in list(self._handlers.get(event_type, ())):
                if id(handler) in delivered:
                    continue
                delivered.add(id(handler))
                try:
                    handler(event)
                except Exception:
                    self._logger.exception(
                        "Event subscriber %r failed while handling %s",
                        handler,
                        type(event).__name__,
                    )
