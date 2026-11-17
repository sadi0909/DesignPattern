from datetime import datetime
from typing import Literal
from uuid import UUID

from pydantic import BaseModel, Field


class CommandPayloadRequest(BaseModel):
    command_type: str = Field(min_length=1, description="start_pump, stop_pump, or set_light_level")
    payload: dict[str, object] = Field(default_factory=dict)


class CommandCreateRequest(CommandPayloadRequest):
    device_id: UUID


class CommandLogDto(BaseModel):
    id: UUID
    command_type: str
    device_id: UUID
    payload: dict[str, object]
    status: Literal["success", "failed", "rejected"]
    error_message: str | None
    created_at: datetime
