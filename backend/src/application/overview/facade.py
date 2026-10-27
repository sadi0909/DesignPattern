from uuid import UUID

from application.automation.service import AutomationService
from application.overview.dto import (
    DeviceCountsDto,
    LocationOverviewDto,
    LocationSummaryDto,
    OverviewRecommendationDto,
    ReadingSummaryDto,
)
from domain.locations.errors import LocationNotFoundError
from infrastructure.persistence.device_repository import DeviceRepository
from infrastructure.persistence.location_repository import LocationRepository
from infrastructure.persistence.reading_repository import ReadingRepository


class LocationOverviewFacade:
    """A single read entry point; strategy policy remains in AutomationService."""

    def __init__(
        self,
        locations: LocationRepository,
        devices: DeviceRepository,
        readings: ReadingRepository,
        automation: AutomationService,
    ) -> None:
        self._locations = locations
        self._devices = devices
        self._readings = readings
        self._automation = automation

    def get_overview(self, location_id: UUID) -> LocationOverviewDto:
        config = self._locations.get_config(location_id)
        if config is None:
            raise LocationNotFoundError(f"Location {location_id} does not exist")

        counts = self._devices.count_by_role()
        readings = self._readings.latest_per_sensor()
        recommendation = self._automation.evaluate(location_id)
        return LocationOverviewDto(
            location=LocationSummaryDto(id=location_id, name=config.location.name),
            device_counts=DeviceCountsDto(sensor=counts.get("sensor", 0), actuator=counts.get("actuator", 0)),
            latest_readings=[
                ReadingSummaryDto(
                    device_id=reading.device_id,
                    value=reading.value,
                    unit=reading.unit,
                    recorded_at=reading.recorded_at,
                )
                for reading in readings
            ],
            strategy_key=recommendation.strategy_key,
            last_recommendation=OverviewRecommendationDto(
                action=recommendation.action, reason=recommendation.reason
            ),
        )
