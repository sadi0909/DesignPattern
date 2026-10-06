from uuid import UUID

from sqlalchemy import select
from sqlalchemy.orm import Session

from domain.sensors.reading import Reading

from .models import ReadingRow


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

    @staticmethod
    def _to_domain(row: ReadingRow) -> Reading:
        return Reading(
            device_id=row.device_id,
            value=float(row.value),
            unit=row.unit,
            source=row.source,
            recorded_at=row.recorded_at,
        )
