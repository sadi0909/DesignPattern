from domain.locations.entity import Location, LocationConfig, Zone, schedule_to_dict
from domain.locations.errors import ConfigurationError


class LocationConfigBuilder:
    def __init__(self) -> None:
        self._location_name: str | None = None
        self._zones: list[Zone] = []

    def with_location_name(self, name: str) -> "LocationConfigBuilder":
        self._location_name = name
        return self

    def add_zone(
        self,
        name: str,
        moisture_threshold_low: float,
        moisture_threshold_high: float,
        schedule: dict[str, object] | None = None,
    ) -> "LocationConfigBuilder":
        self._zones.append(
            Zone(
                name=name,
                moisture_threshold_low=moisture_threshold_low,
                moisture_threshold_high=moisture_threshold_high,
                schedule=schedule_to_dict(schedule or {}),
            )
        )
        return self

    def build(self) -> LocationConfig:
        location_name = (self._location_name or "").strip()
        if not location_name:
            raise ConfigurationError("Location name is required")
        if len(location_name) > 128:
            raise ConfigurationError("Location name must be 128 characters or fewer")
        if not self._zones:
            raise ConfigurationError("At least one zone is required")

        validated_zones: list[Zone] = []
        zone_names: set[str] = set()
        for zone in self._zones:
            name = zone.name.strip()
            if not name:
                raise ConfigurationError("Zone name is required")
            if len(name) > 128:
                raise ConfigurationError("Zone names must be 128 characters or fewer")
            normalized_name = name.casefold()
            if normalized_name in zone_names:
                raise ConfigurationError(f"Zone names must be unique within a location: {name}")
            zone_names.add(normalized_name)

            low = zone.moisture_threshold_low
            high = zone.moisture_threshold_high
            if not 0.0 <= low <= 1.0 or not 0.0 <= high <= 1.0:
                raise ConfigurationError("Moisture thresholds must be between 0.0 and 1.0")
            if low >= high:
                raise ConfigurationError("Low moisture threshold must be less than high threshold")

            validated_zones.append(
                Zone(
                    name=name,
                    moisture_threshold_low=low,
                    moisture_threshold_high=high,
                    schedule=schedule_to_dict(zone.schedule),
                )
            )

        return LocationConfig(location=Location(name=location_name, zones=tuple(validated_zones)))
