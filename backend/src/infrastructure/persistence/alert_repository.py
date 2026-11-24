from datetime import datetime
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.orm import Session

from domain.alerts.entity import Alert

from .models import AlertRow


class AlertRepository:
    """Persists and lists alert rows produced by event subscribers."""

    def __init__(self, session: Session) -> None:
        self._session = session

    def record(
        self,
        *,
        location_id: UUID | None,
        device_id: UUID | None,
        severity: str,
        message: str,
        event_type: str,
        status: str = "active",
    ) -> Alert:
        row = AlertRow(
            location_id=location_id,
            device_id=device_id,
            severity=severity,
            message=message,
            event_type=event_type,
            status=status,
        )
        self._session.add(row)
        try:
            self._session.commit()
            self._session.refresh(row)
        except Exception:
            self._session.rollback()
            raise
        return self._to_domain(row)

    def has_active(self, device_id: UUID, event_type: str) -> bool:
        """True while an alert for this device/event is still active."""
        return (
            self._session.scalar(
                select(AlertRow.id)
                .where(
                    AlertRow.device_id == device_id,
                    AlertRow.event_type == event_type,
                    AlertRow.status == "active",
                )
                .limit(1)
            )
            is not None
        )

    def list_recent(
        self,
        limit: int = 50,
        *,
        status: str | None = None,
        location_id: UUID | None = None,
        since: datetime | None = None,
    ) -> list[Alert]:
        """Newest first, optionally filtered by status, location, or creation time."""
        query = select(AlertRow)
        if status is not None:
            query = query.where(AlertRow.status == status)
        if location_id is not None:
            query = query.where(AlertRow.location_id == location_id)
        if since is not None:
            query = query.where(AlertRow.created_at >= since)
        rows = self._session.scalars(
            query.order_by(AlertRow.created_at.desc(), AlertRow.id.desc()).limit(limit)
        ).all()
        return [self._to_domain(row) for row in rows]

    @staticmethod
    def _to_domain(row: AlertRow) -> Alert:
        return Alert(
            id=row.id,
            location_id=row.location_id,
            device_id=row.device_id,
            severity=row.severity,
            message=row.message,
            event_type=row.event_type,
            status=row.status,
            created_at=row.created_at,
            acknowledged_at=row.acknowledged_at,
        )
