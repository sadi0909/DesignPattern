from uuid import UUID

from sqlalchemy import select
from sqlalchemy.orm import Session

from domain.locations.entity import Location, LocationConfig, Zone, schedule_to_dict

from .models import LocationRow, ZoneRow


class LocationRepository:
    def __init__(self, session: Session) -> None:
        self._session = session

    def save_config(self, config: LocationConfig) -> LocationConfig:
        location_row = LocationRow(name=config.location.name)
        try:
            self._session.add(location_row)
            self._session.flush()
            zone_rows = [
                ZoneRow(
                    location_id=location_row.id,
                    name=zone.name,
                    moisture_threshold_low=zone.moisture_threshold_low,
                    moisture_threshold_high=zone.moisture_threshold_high,
                    schedule=schedule_to_dict(zone.schedule),
                )
                for zone in config.location.zones
            ]
            self._session.add_all(zone_rows)
            self._session.flush()
            self._session.commit()
        except Exception:
            self._session.rollback()
            raise

        return self._to_domain(location_row, zone_rows)

    def get_config(self, location_id: UUID) -> LocationConfig | None:
        location_row = self._session.get(LocationRow, location_id)
        if location_row is None:
            return None
        zone_rows = self._session.scalars(
            select(ZoneRow)
            .where(ZoneRow.location_id == location_id)
            .order_by(ZoneRow.name, ZoneRow.id)
        ).all()
        return self._to_domain(location_row, zone_rows)

    @staticmethod
    def _to_domain(location_row: LocationRow, zone_rows: list[ZoneRow]) -> LocationConfig:
        return LocationConfig(
            location=Location(
                id=location_row.id,
                name=location_row.name,
                zones=tuple(
                    Zone(
                        id=zone_row.id,
                        location_id=zone_row.location_id,
                        name=zone_row.name,
                        moisture_threshold_low=float(zone_row.moisture_threshold_low),
                        moisture_threshold_high=float(zone_row.moisture_threshold_high),
                        schedule=dict(zone_row.schedule),
                    )
                    for zone_row in zone_rows
                ),
            )
        )
