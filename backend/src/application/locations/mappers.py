from application.locations.dto import (
    LocationConfigDto,
    LocationResponseDto,
    ZoneResponseDto,
)
from domain.locations.entity import LocationConfig, schedule_to_dict


def location_config_to_dto(config: LocationConfig) -> LocationConfigDto:
    location = config.location
    if location.id is None:
        raise ValueError("Cannot map an unpersisted location configuration to a DTO")

    zones: list[ZoneResponseDto] = []
    for zone in location.zones:
        if zone.id is None or zone.location_id is None:
            raise ValueError("Cannot map an unpersisted zone to a DTO")
        zones.append(
            ZoneResponseDto(
                id=zone.id,
                location_id=zone.location_id,
                name=zone.name,
                moisture_threshold_low=zone.moisture_threshold_low,
                moisture_threshold_high=zone.moisture_threshold_high,
                schedule=schedule_to_dict(zone.schedule),
            )
        )

    return LocationConfigDto(
        location=LocationResponseDto(id=location.id, name=location.name),
        zones=zones,
    )
