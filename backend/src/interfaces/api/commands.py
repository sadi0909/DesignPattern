from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from application.commands.dto import (
    CommandCreateRequest,
    CommandLogDto,
    CommandPayloadRequest,
)
from application.commands.mappers import command_log_to_dto, command_logs_to_dtos
from application.commands.service import CommandService
from domain.actuators.errors import ActuatorPolicyBlockedError
from domain.commands.errors import (
    CommandRejectedError,
    CommandValidationError,
    UnknownCommandTypeError,
)
from domain.devices.errors import DeviceNotFoundError
from infrastructure.adapters.actuators.composition import build_actuator_port
from infrastructure.events.composition import get_event_bus
from infrastructure.persistence.actuator_state_repository import ActuatorStateRepository
from infrastructure.persistence.command_log_repository import CommandLogRepository
from infrastructure.persistence.device_repository import DeviceRepository
from infrastructure.persistence.execution_log_repository import ExecutionLogRepository
from infrastructure.persistence.session import get_db
from infrastructure.settings import settings

router = APIRouter(prefix="/api/commands", tags=["commands"])
device_commands_router = APIRouter(prefix="/api/devices", tags=["commands"])


def get_command_service(
    db: Session = Depends(get_db),  # noqa: B008
) -> CommandService:
    """Composition root: command invoker → logging → max runtime → adapter."""
    states = ActuatorStateRepository(db)
    executions = ExecutionLogRepository(db)
    port = build_actuator_port(
        states=states,
        executions=executions,
        max_runtime_seconds=settings.actuator_max_runtime_seconds,
    )
    return CommandService(
        DeviceRepository(db),
        states,
        port,
        CommandLogRepository(db),
        events=get_event_bus(),
    )


def _execute(
    device_id: UUID,
    request: CommandPayloadRequest,
    service: CommandService,
) -> CommandLogDto:
    try:
        log = service.submit(device_id, request.command_type, request.payload)
    except (UnknownCommandTypeError, CommandValidationError) as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc
    except DeviceNotFoundError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc
    except (CommandRejectedError, ActuatorPolicyBlockedError) as exc:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(exc)) from exc
    return command_log_to_dto(log)


@router.post(
    "",
    response_model=CommandLogDto,
    responses={
        400: {"description": "Unknown command type or invalid payload"},
        404: {"description": "Actuator not found"},
        409: {"description": "Command rejected by State or an actuator policy"},
    },
    summary="Execute an actuator command and record it",
)
def execute_command(
    request: CommandCreateRequest,
    service: CommandService = Depends(get_command_service),  # noqa: B008
) -> CommandLogDto:
    return _execute(request.device_id, request, service)


@device_commands_router.post(
    "/{device_id}/commands",
    response_model=CommandLogDto,
    responses={
        400: {"description": "Unknown command type or invalid payload"},
        404: {"description": "Actuator not found"},
        409: {"description": "Command rejected by State or an actuator policy"},
    },
    summary="Execute a command for one actuator (alias)",
)
def execute_device_command(
    device_id: UUID,
    request: CommandPayloadRequest,
    service: CommandService = Depends(get_command_service),  # noqa: B008
) -> CommandLogDto:
    return _execute(device_id, request, service)


@router.get(
    "",
    response_model=list[CommandLogDto],
    summary="List recent command attempts, newest first",
)
def list_commands(
    limit: int = Query(50, ge=1, le=100, description="Newest command attempts to return"),
    service: CommandService = Depends(get_command_service),  # noqa: B008
) -> list[CommandLogDto]:
    return command_logs_to_dtos(service.list_commands(limit))
