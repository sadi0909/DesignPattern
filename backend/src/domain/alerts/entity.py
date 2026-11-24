from dataclasses import dataclass
from datetime import datetime
from uuid import UUID


@dataclass(frozen=True, slots=True)
class Alert:
    """One persisted notification produced by an event subscriber.

    ``location_id`` and ``device_id`` are nullable because readings and
    commands can reference an unassigned device, and alerts outlive devices
    (the foreign keys use ``ON DELETE SET NULL``).
    """

    id: UUID
    location_id: UUID | None
    device_id: UUID | None
    severity: str
    message: str
    event_type: str
    status: str
    created_at: datetime
    acknowledged_at: datetime | None = None
