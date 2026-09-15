from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from application.sensors.service import SensorService
from infrastructure.persistence.device_repository import DeviceRepository
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


def get_service(db: Session = Depends(get_db)) -> SensorService:  # noqa: B008
    return SensorService(DeviceRepository(db))


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
