from dataclasses import dataclass
from uuid import UUID


@dataclass(frozen=True, slots=True)
class LocationAutomationContext:
    """Plain inputs for one zone decision.

    ``moisture``, ``moisture_low`` and ``moisture_high`` are all 0-1 fractions,
    the same scale as the zone thresholds stored in Phase 4. Built by the
    application layer; strategies never see ORM rows.
    """

    location_id: UUID
    zone_name: str
    moisture: float
    moisture_low: float
    moisture_high: float
