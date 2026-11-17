from datetime import datetime
from uuid import UUID

from pydantic import BaseModel


class ActuatorExecutionDto(BaseModel):
    """One row of the dashboard's actuator execution log."""

    id: UUID
    device_id: UUID
    success: bool
    policy_applied: list[str]
    message: str | None
    created_at: datetime
