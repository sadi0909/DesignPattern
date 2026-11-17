from application.commands.dto import CommandLogDto
from domain.commands.log import CommandLog


def command_log_to_dto(log: CommandLog) -> CommandLogDto:
    return CommandLogDto(
        id=log.id,
        command_type=log.command_type,
        device_id=log.device_id,
        payload=log.payload,
        status=log.status,
        error_message=log.error_message,
        created_at=log.created_at,
    )


def command_logs_to_dtos(logs: list[CommandLog]) -> list[CommandLogDto]:
    return [command_log_to_dto(log) for log in logs]
