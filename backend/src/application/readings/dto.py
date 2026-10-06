from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict


class ReadingDto(BaseModel):
    """Normalized reading returned by the read/history endpoints.

    JSON keys: ``device_id``, ``value``, ``unit``, ``source``,
    ``recorded_at`` (ISO-8601). Vendor-shaped fields never appear here.
    """

    model_config = ConfigDict(from_attributes=True)

    device_id: UUID
    value: float
    unit: str
    source: str
    recorded_at: datetime
