from datetime import datetime
from typing import Literal
from uuid import UUID

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from application.alerts.dto import AlertDto
from infrastructure.persistence.alert_repository import AlertRepository
from infrastructure.persistence.session import get_db

router = APIRouter(prefix="/api/alerts", tags=["alerts"])


def get_alert_repository(db: Session = Depends(get_db)) -> AlertRepository:  # noqa: B008
    return AlertRepository(db)


@router.get(
    "",
    response_model=list[AlertDto],
    summary="List persisted alerts, newest first",
)
def list_alerts(
    status: Literal["active", "resolved"] | None = Query(
        None, description="Filter by alert status; omit to return both"
    ),
    location_id: UUID | None = Query(None, description="Only alerts for one location"),  # noqa: B008
    since: datetime | None = Query(  # noqa: B008
        None, description="Only alerts created at or after this timestamp"
    ),
    limit: int = Query(50, ge=1, le=200, description="Newest alerts to return"),
    alerts: AlertRepository = Depends(get_alert_repository),  # noqa: B008
) -> list[AlertDto]:
    """Read the alert feed. Alerts survive refreshes because they live in PostgreSQL."""
    return [
        AlertDto.model_validate(alert, from_attributes=True)
        for alert in alerts.list_recent(
            limit,
            status=status,
            location_id=location_id,
            since=since,
        )
    ]
