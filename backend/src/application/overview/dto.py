from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, Field


class LocationSummaryDto(BaseModel):
    id: UUID
    name: str


class DeviceCountsDto(BaseModel):
    sensor: int
    actuator: int


class ReadingSummaryDto(BaseModel):
    device_id: UUID
    value: float
    unit: str
    recorded_at: datetime


class OverviewRecommendationDto(BaseModel):
    action: str
    reason: str


class LocationOverviewDto(BaseModel):
    location: LocationSummaryDto
    device_counts: DeviceCountsDto = Field(
        description="Global counts: devices are not yet associated with locations."
    )
    latest_readings: list[ReadingSummaryDto] = Field(
        description="Latest reading per sensor globally; sensors are not yet associated with locations."
    )
    strategy_key: str | None = Field(description="Active strategy, including the default when no rule is saved.")
    last_recommendation: OverviewRecommendationDto | None = Field(
        description="Computed on this request, not a persisted historical recommendation."
    )
