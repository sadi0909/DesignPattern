from datetime import UTC, datetime
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, status
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from application.readings.dto import ReadingDto
from application.readings.service import ReadingService
from application.sensors.service import SensorService
from domain.devices.errors import DeviceNotFoundError
from domain.sensors.errors import SensorReadError
from infrastructure.events.composition import get_event_bus
from infrastructure.persistence.device_repository import DeviceRepository
from infrastructure.persistence.reading_repository import ReadingRepository
from infrastructure.persistence.session import get_db

router = APIRouter(prefix="/api/sensors", tags=["sensors"])


class SensorCreateRequest(BaseModel):
    type: str = Field(min_length=1)
    display_name: str | None = None


class SensorResponse(BaseModel):
    id: UUID
    device_type: str
    display_name: str
    default_config: dict[str, object]
    location_id: UUID | None = None


def get_service(db: Session = Depends(get_db)) -> SensorService:  # noqa: B008
    return SensorService(DeviceRepository(db))


def get_reading_service(db: Session = Depends(get_db)) -> ReadingService:  # noqa: B008
    return ReadingService(
        DeviceRepository(db),
        ReadingRepository(db),
        events=get_event_bus(),
    )


@router.get("", response_model=list[SensorResponse])
def list_sensors(service: SensorService = Depends(get_service)) -> list[SensorResponse]:  # noqa: B008
    return [SensorResponse.model_validate(sensor, from_attributes=True) for sensor in service.list_sensors()]


@router.post("", response_model=SensorResponse, status_code=status.HTTP_201_CREATED)
def create_sensor(
    payload: SensorCreateRequest,
    service: SensorService = Depends(get_service),  # noqa: B008
) -> SensorResponse:
    try:
        sensor = service.create_sensor(payload.type, payload.display_name)
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc
    return SensorResponse.model_validate(sensor, from_attributes=True)


@router.post(
    "/{sensor_id}/read",
    response_model=ReadingDto,
    status_code=status.HTTP_201_CREATED,
    responses={
        400: {"description": "Adapter or validation failure"},
        404: {"description": "Sensor device not found"},
    },
)
def read_sensor(
    sensor_id: UUID,
    service: ReadingService = Depends(get_reading_service),  # noqa: B008
) -> ReadingDto:
    """Run the device's sensor adapter and persist the normalized reading."""
    try:
        return service.take_reading(sensor_id)
    except DeviceNotFoundError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc
    except SensorReadError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc


@router.get(
    "/{sensor_id}/readings",
    response_model=list[ReadingDto],
    responses={404: {"description": "Sensor device not found"}},
)
def list_sensor_readings(
    sensor_id: UUID,
    limit: int = Query(20, ge=1, le=500),
    from_: datetime | None = Query(  # noqa: B008
        None,
        alias="from",
        description="Only readings at or after this ISO-8601 timestamp",
    ),
    to: datetime | None = Query(  # noqa: B008
        None, description="Only readings at or before this ISO-8601 timestamp"
    ),
    service: ReadingService = Depends(get_reading_service),  # noqa: B008
) -> list[ReadingDto]:
    """Return persisted readings for one sensor device.

    Without `from`/`to` the newest rows come first (history panel). With a
    time window the rows are oldest first so charts plot left to right.
    """
    start = _ensure_utc(from_)
    end = _ensure_utc(to)
    if start is not None and end is not None and start > end:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="from must be earlier than to",
        )
    try:
        return service.list_readings(sensor_id, limit=limit, start=start, end=end)
    except DeviceNotFoundError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc


def _ensure_utc(value: datetime | None) -> datetime | None:
    if value is not None and value.tzinfo is None:
        return value.replace(tzinfo=UTC)
    return value
