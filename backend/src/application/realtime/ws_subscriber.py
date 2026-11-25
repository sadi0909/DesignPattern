"""Bridge domain events to WebSocket JSON envelopes.

This is the Phase 12 Observer subscriber: it maps events already published by
the bus and hands them to the connection manager. It contains no alert rules,
command handling, or persistence, so the WebSocket transport cannot drift from
the domain behavior that produced the event.
"""

from collections.abc import Callable
from datetime import datetime
from typing import Any
from uuid import UUID

from application.realtime.connection_manager import ConnectionManager
from domain.events.bus import EventBus
from domain.events.events import ActuatorStateChanged, AlertCreated, ReadingTaken


def _uuid(value: UUID | None) -> str | None:
    return None if value is None else str(value)


def _time(value: datetime) -> str:
    return value.isoformat()


def event_to_message(event: object) -> dict[str, Any] | None:
    """Map one domain event to the public ``{type, payload}`` envelope."""
    if isinstance(event, ReadingTaken):
        return {
            "type": "reading.created",
            "payload": {
                "device_id": str(event.device_id),
                "location_id": _uuid(event.location_id),
                "sensor_type": event.sensor_type,
                "value": event.value,
                "unit": event.unit,
                "occurred_at": _time(event.occurred_at),
            },
        }
    if isinstance(event, ActuatorStateChanged):
        return {
            "type": "actuator.state_changed",
            "payload": {
                "device_id": str(event.device_id),
                "location_id": _uuid(event.location_id),
                "from_state": event.from_state,
                "to_state": event.to_state,
                "occurred_at": _time(event.occurred_at),
            },
        }
    if isinstance(event, AlertCreated):
        return {
            "type": "alert.created",
            "payload": {
                "id": str(event.alert_id),
                "location_id": _uuid(event.location_id),
                "device_id": _uuid(event.device_id),
                "severity": event.severity,
                "message": event.message,
                "event_type": event.event_type,
                "status": event.status,
                "created_at": _time(event.created_at),
                "acknowledged_at": None,
            },
        }
    return None


def subscribe_realtime(
    bus: EventBus,
    manager: ConnectionManager,
) -> Callable[[], None]:
    """Attach the manager as a bus subscriber and return the detach callable."""

    def forward(event: object) -> None:
        message = event_to_message(event)
        if message is not None:
            manager.broadcast(message)

    unsubscribers = [
        bus.subscribe(ReadingTaken, forward),
        bus.subscribe(ActuatorStateChanged, forward),
        bus.subscribe(AlertCreated, forward),
    ]

    def unsubscribe() -> None:
        for unsubscribe_one in unsubscribers:
            unsubscribe_one()

    return unsubscribe
