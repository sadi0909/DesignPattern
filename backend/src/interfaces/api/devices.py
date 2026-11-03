from typing import Literal
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, status
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from application.devices.actuator_state_service import ActuatorStateService
from application.devices.dto import DeviceDto
from application.devices.family_service import DeviceFamilyService
from application.devices.mappers import device_to_dto, devices_to_dtos
from domain.actuators.errors import IllegalTransitionError, UnknownActuatorStateError
from domain.devices.errors import DeviceNotFoundError
from domain.devices.family_factory import UnsupportedDeviceFamilyError
from infrastructure.persistence.actuator_state_repository import ActuatorStateRepository
from infrastructure.persistence.device_repository import DeviceRepository
from infrastructure.persistence.session import get_db

router = APIRouter(prefix="/api/devices", tags=["devices"])


class TransitionRequest(BaseModel):
    target: str = Field(min_length=1, description="Target actuator state")


def get_device_family_service(db: Session = Depends(get_db)) -> DeviceFamilyService:  # noqa: B008
    return DeviceFamilyService(DeviceRepository(db))


def get_actuator_state_service(db: Session = Depends(get_db)) -> ActuatorStateService:  # noqa: B008
    return ActuatorStateService(DeviceRepository(db), ActuatorStateRepository(db))


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


@router.get(
    "/{device_id}",
    response_model=DeviceDto,
    responses={404: {"description": "Device not found"}},
)
def get_device(
    device_id: UUID,
    service: DeviceFamilyService = Depends(get_device_family_service),  # noqa: B008
) -> DeviceDto:
    """Return one device, including its persisted actuator state when applicable."""
    try:
        return device_to_dto(service.get_device(device_id))
    except DeviceNotFoundError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc


@router.post(
    "/{device_id}/transition",
    response_model=DeviceDto,
    responses={
        400: {"description": "Unknown target state"},
        404: {"description": "Actuator not found"},
        409: {"description": "Transition not allowed from the current state"},
    },
)
def transition_actuator(
    device_id: UUID,
    payload: TransitionRequest,
    service: ActuatorStateService = Depends(get_actuator_state_service),  # noqa: B008
) -> DeviceDto:
    """Guard and persist one actuator lifecycle transition, then return the new state."""
    try:
        device = service.transition(device_id, payload.target)
    except DeviceNotFoundError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc
    except UnknownActuatorStateError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc
    except IllegalTransitionError as exc:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(exc)) from exc
    return device_to_dto(device)
