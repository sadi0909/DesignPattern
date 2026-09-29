from typing import Literal

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from application.devices.dto import DeviceDto
from application.devices.family_service import DeviceFamilyService
from application.devices.mappers import devices_to_dtos
from domain.devices.family_factory import UnsupportedDeviceFamilyError
from infrastructure.persistence.device_repository import DeviceRepository
from infrastructure.persistence.session import get_db

router = APIRouter(prefix="/api/devices", tags=["devices"])


def get_device_family_service(db: Session = Depends(get_db)) -> DeviceFamilyService:  # noqa: B008
    return DeviceFamilyService(DeviceRepository(db))


@router.get("", response_model=list[DeviceDto])
def list_devices(
    family: str | None = None,
    role: Literal["sensor", "actuator"] | None = None,
    service: DeviceFamilyService = Depends(get_device_family_service),  # noqa: B008
) -> list[DeviceDto]:
    return devices_to_dtos(service.list_devices(family=family, role=role))


@router.post(
    "/provision",
    response_model=list[DeviceDto],
    status_code=status.HTTP_201_CREATED,
)
def provision_device_family(
    family: str = Query(min_length=1),
    service: DeviceFamilyService = Depends(get_device_family_service),  # noqa: B008
) -> list[DeviceDto]:
    try:
        devices = service.provision_family(family)
    except UnsupportedDeviceFamilyError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc
    return devices_to_dtos(devices)
