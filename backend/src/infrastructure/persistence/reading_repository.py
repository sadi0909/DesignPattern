from uuid import UUID

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from domain.sensors.reading import Reading

from .models import DeviceRow, ReadingRow


class ReadingRepository:
    """Appends and reads sensor_readings history rows."""

    def __init__(self, session: Session) -> None:
        self._session = session

    def insert(self, reading: Reading) -> Reading:
        """Append one history row. Every read adds a row; nothing is overwritten."""
        row = ReadingRow(
            device_id=reading.device_id,
            value=reading.value,
            unit=reading.unit,
            source=reading.source,
            recorded_at=reading.recorded_at,
        )
        self._session.add(row)
        try:
            self._session.commit()
            self._session.refresh(row)
        except Exception:
            self._session.rollback()
            raise
        return self._to_domain(row)

    def list_for_device(self, device_id: UUID, limit: int = 20) -> list[Reading]:
        rows = self._session.scalars(
            select(ReadingRow)
            .where(ReadingRow.device_id == device_id)
            .order_by(ReadingRow.recorded_at.desc(), ReadingRow.id.desc())
            .limit(limit)
        ).all()
        return [self._to_domain(row) for row in rows]

    def latest_per_sensor(self) -> list[Reading]:
        """One latest reading per sensor in one query; devices are not location-bound."""
        ranked = (
            select(
                ReadingRow.id.label("reading_id"),
                func.row_number().over(
                    partition_by=ReadingRow.device_id,
                    order_by=(ReadingRow.recorded_at.desc(), ReadingRow.id.desc()),
                ).label("rank"),
            )
            .join(DeviceRow, DeviceRow.id == ReadingRow.device_id)
            .where(DeviceRow.role == "sensor")
            .subquery()
        )
        rows = self._session.scalars(
            select(ReadingRow)
            .join(ranked, ranked.c.reading_id == ReadingRow.id)
            .where(ranked.c.rank == 1)
            .order_by(ReadingRow.recorded_at.desc(), ReadingRow.id.desc())
        ).all()
        return [self._to_domain(row) for row in rows]

    @staticmethod
    def _to_domain(row: ReadingRow) -> Reading:
        return Reading(
            device_id=row.device_id,
            value=float(row.value),
            unit=row.unit,
            source=row.source,
            recorded_at=row.recorded_at,
        )
