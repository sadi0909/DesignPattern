from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field


class ZoneConfigRequestDto(BaseModel):
    name: str = Field(min_length=1, max_length=128)
    moisture_threshold_low: float
    moisture_threshold_high: float
    schedule: dict[str, object] = Field(default_factory=dict)


class BuildLocationConfigRequestDto(BaseModel):
    location_name: str = Field(min_length=1, max_length=128)
    zones: list[ZoneConfigRequestDto]


class LocationResponseDto(BaseModel):
    id: UUID
    name: str


class ZoneResponseDto(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    location_id: UUID
    name: str
    moisture_threshold_low: float
    moisture_threshold_high: float
    schedule: dict[str, object]


class LocationConfigDto(BaseModel):
    location: LocationResponseDto
    zones: list[ZoneResponseDto]
