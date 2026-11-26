from datetime import datetime
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

    def list_for_device_between(
        self,
        device_id: UUID,
        *,
        start: datetime | None = None,
        end: datetime | None = None,
        limit: int = 500,
    ) -> list[Reading]:
        """Read one device's history inside an optional window, oldest first.

        Chart-friendly ordering: the Phase 13 trend chart plots left to right.
        The existing `(device_id, recorded_at DESC)` index still supports the
        filter because Postgres can scan an index backwards.
        """
        query = select(ReadingRow).where(ReadingRow.device_id == device_id)
        if start is not None:
            query = query.where(ReadingRow.recorded_at >= start)
        if end is not None:
            query = query.where(ReadingRow.recorded_at <= end)
        rows = self._session.scalars(
            query.order_by(ReadingRow.recorded_at.asc(), ReadingRow.id.asc()).limit(limit)
        ).all()
        return [self._to_domain(row) for row in rows]

    def latest_per_sensor(self, location_id: UUID) -> list[Reading]:
        """One latest reading per sensor assigned to the requested location."""
        ranked = (
            select(
                ReadingRow.id.label("reading_id"),
                func.row_number().over(
                    partition_by=ReadingRow.device_id,
                    order_by=(ReadingRow.recorded_at.desc(), ReadingRow.id.desc()),
                ).label("rank"),
            )
            .join(DeviceRow, DeviceRow.id == ReadingRow.device_id)
            .where(DeviceRow.role == "sensor", DeviceRow.location_id == location_id)
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
