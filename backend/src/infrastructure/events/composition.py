"""Composition root for the application-wide event bus.

A single bus lives for the process, which is what lets Phase 12 attach a
WebSocket subscriber once and have every future reading or command fan out to
it. Handlers therefore cannot hold a request-scoped SQLAlchemy session; each
handler opens a short session for the event it processes.
"""

from collections.abc import Callable
from typing import Any

from sqlalchemy.orm import Session

from application.alerts.subscribers import (
    AlertPersistenceSubscriber,
    MoistureThresholdSubscriber,
)
from domain.events.bus import EventBus
from domain.events.events import CommandExecuted, ReadingTaken, ThresholdCrossed
from infrastructure.db import SessionLocal
from infrastructure.persistence.alert_repository import AlertRepository
from infrastructure.persistence.location_repository import LocationRepository

HandlerBuilder = Callable[[Session], Callable[[Any], None]]


class _SessionHandler:
    """Runs a repository-backed subscriber in its own session per event."""

    def __init__(
        self,
        session_factory: Callable[[], Session],
        build_handler: HandlerBuilder,
    ) -> None:
        self._session_factory = session_factory
        self._build_handler = build_handler

    def __call__(self, event: object) -> None:
        with self._session_factory() as session:
            try:
                self._build_handler(session)(event)
                session.commit()
            except Exception:
                session.rollback()
                raise


def build_event_bus() -> EventBus:
    """Wire the bus and its Phase 11 subscribers."""
    bus = EventBus()
    bus.subscribe(
        ReadingTaken,
        _SessionHandler(
            SessionLocal,
            lambda session: MoistureThresholdSubscriber(
                LocationRepository(session), bus
            ).handle,
        ),
    )
    bus.subscribe(
        ThresholdCrossed,
        _SessionHandler(
            SessionLocal,
            lambda session: AlertPersistenceSubscriber(
                AlertRepository(session), events=bus
            ).handle,
        ),
    )
    bus.subscribe(
        CommandExecuted,
        _SessionHandler(
            SessionLocal,
            lambda session: AlertPersistenceSubscriber(
                AlertRepository(session), events=bus
            ).handle,
        ),
    )
    return bus


_event_bus: EventBus | None = None


def get_event_bus() -> EventBus:
    """Return the process-wide bus, creating and wiring it on first use."""
    global _event_bus
    if _event_bus is None:
        _event_bus = build_event_bus()
    return _event_bus
