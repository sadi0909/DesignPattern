from dataclasses import dataclass
from datetime import datetime
from uuid import UUID


@dataclass(frozen=True, slots=True)
class AutomationRule:
    location_id: UUID
    strategy_key: str
    updated_at: datetime
