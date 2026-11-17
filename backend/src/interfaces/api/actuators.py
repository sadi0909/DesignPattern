from typing import Literal
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, status
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from application.actuators.dto import ActuatorExecutionDto
from application.actuators.execution_service import ActuatorExecutionService
from application.actuators.mappers import executions_to_dtos
from domain.actuators.errors import ActuatorPolicyBlockedError
from domain.devices.errors import DeviceNotFoundError
from infrastructure.adapters.actuators.composition import build_actuator_port
from infrastructure.persistence.actuator_state_repository import ActuatorStateRepository
from infrastructure.persistence.device_repository import DeviceRepository
from infrastructure.persistence.execution_log_repository import ExecutionLogRepository
from infrastructure.persistence.session import get_db
from infrastructure.settings import settings

router = APIRouter(prefix="/api/actuators", tags=["actuators"])


class ApplyActuatorRequest(BaseModel):
    command: str = Field(min_length=1, max_length=64, description="Command name to apply")
    payload: dict[str, object] = Field(
        default_factory=dict,
        description="Adapter-specific arguments; Phase 10 will replace this demo path.",
    )


class ApplyActuatorResponse(BaseModel):
    status: Literal["applied"]


def get_actuator_execution_service(
    db: Session = Depends(get_db),  # noqa: B008
) -> ActuatorExecutionService:
    """Composition root for this request: logging → max run time → adapter."""
    executions = ExecutionLogRepository(db)
    states = ActuatorStateRepository(db)
    port = build_actuator_port(
        states=states,
        executions=executions,
        max_runtime_seconds=settings.actuator_max_runtime_seconds,
    )
    return ActuatorExecutionService(DeviceRepository(db), port, executions)


@router.get(
    "/executions",
    response_model=list[ActuatorExecutionDto],
    summary="List recent actuator execution attempts",
)
def list_executions(
    limit: int = Query(20, ge=1, le=100, description="Newest executions to return"),
    service: ActuatorExecutionService = Depends(get_actuator_execution_service),  # noqa: B008
) -> list[ActuatorExecutionDto]:
    return executions_to_dtos(service.list_executions(limit))


@router.post(
    "/{device_id}/apply",
    response_model=ApplyActuatorResponse,
    responses={
        404: {"description": "Actuator not found"},
        409: {"description": "A policy decorator blocked the attempt"},
    },
    summary="Apply a command through the decorated actuator port (demo)",
)
def apply_actuator_command(
    device_id: UUID,
    payload: ApplyActuatorRequest,
    service: ActuatorExecutionService = Depends(get_actuator_execution_service),  # noqa: B008
) -> ApplyActuatorResponse:
    """Run one demo apply; logging records success and failure in both cases."""
    try:
        service.apply(device_id, payload.command, payload.payload)
    except DeviceNotFoundError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc
    except ActuatorPolicyBlockedError as exc:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(exc)) from exc
    return ApplyActuatorResponse(status="applied")
