"""Immutable domain events published by application services.

Publishers describe what happened. They do not know who listens, so these
types import neither persistence nor HTTP/UI modules.
"""

from dataclasses import dataclass, field
from datetime import UTC, datetime
from typing import Literal
from uuid import UUID

Severity = Literal["info", "warning", "critical"]
CommandStatus = Literal["success", "failed", "rejected"]
ThresholdDirection = Literal["below", "above"]


def _now() -> datetime:
    return datetime.now(UTC)


@dataclass(frozen=True, slots=True, kw_only=True)
class DomainEvent:
    """Base event; ``occurred_at`` is filled when the publisher creates it."""

    occurred_at: datetime = field(default_factory=_now)


@dataclass(frozen=True, slots=True, kw_only=True)
class ReadingTaken(DomainEvent):
    """A sensor reading was normalized and persisted."""

    device_id: UUID
    location_id: UUID | None
    sensor_type: str
    value: float
    unit: str


@dataclass(frozen=True, slots=True, kw_only=True)
class ThresholdCrossed(DomainEvent):
    """A moisture reading fell outside one zone's configured thresholds.

    ``moisture`` and ``threshold`` are 0-1 fractions, matching the zone
    configuration. The alert message formats them as percentages.
    """

    device_id: UUID
    location_id: UUID | None
    zone_name: str
    moisture: float
    threshold: float
    direction: ThresholdDirection
    severity: Severity = "warning"


@dataclass(frozen=True, slots=True, kw_only=True)
class CommandExecuted(DomainEvent):
    """An operator command finished, failed, or was rejected before execution."""

    device_id: UUID
    location_id: UUID | None
    command_type: str
    status: CommandStatus
    error_message: str | None = None


@dataclass(frozen=True, slots=True, kw_only=True)
class ActuatorStateChanged(DomainEvent):
    """A guarded lifecycle transition was persisted."""

    device_id: UUID
    location_id: UUID | None
    from_state: str
    to_state: str
