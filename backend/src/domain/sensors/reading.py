from dataclasses import dataclass
from datetime import datetime
from uuid import UUID


@dataclass(frozen=True, slots=True)
class Reading:
    """Normalized sensor reading produced by every SensorPort adapter.

    Adapters may see vendor payloads with odd field names, scaled integers,
    or epoch milliseconds. They all translate into this single shape so
    application code and persistence never handle vendor types.
    """

    device_id: UUID
    value: float
    unit: str
    source: str  # "simulation" | "vendor"
    recorded_at: datetime  # timezone-aware

    def __post_init__(self) -> None:
        if self.recorded_at.tzinfo is None:
            raise ValueError("Reading.recorded_at must be timezone-aware")
