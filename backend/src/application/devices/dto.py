from typing import Literal
from uuid import UUID

from pydantic import BaseModel, Field


class DeviceDto(BaseModel):
    id: UUID
    device_type: str
    role: Literal["sensor", "actuator"]
    device_family: str
    display_name: str
    default_config: dict[str, object]
    state: str | None = Field(
        default=None,
        description="Persisted lifecycle state for actuators; null for sensors.",
    )
    allowed_commands: list[str] = Field(
        default_factory=list,
        description="Commands legal in the current state; empty for sensors.",
    )
