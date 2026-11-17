from uuid import UUID

from sqlalchemy import select
from sqlalchemy.orm import Session

from domain.commands.log import CommandLog

from .models import CommandLogRow


class CommandLogRepository:
    """Persists every command intent, including rejected and failed attempts."""

    def __init__(self, session: Session) -> None:
        self._session = session

    def record(
        self,
        *,
        command_type: str,
        device_id: UUID,
        payload: dict[str, object],
        status: str,
        error_message: str | None = None,
    ) -> CommandLog:
        row = CommandLogRow(
            command_type=command_type,
            device_id=device_id,
            payload=dict(payload),
            status=status,
            error_message=error_message,
        )
        self._session.add(row)
        # Commit immediately so rejected/failed attempts survive the exception
        # that is about to be raised to the API caller.
        self._session.commit()
        self._session.refresh(row)
        return self._to_domain(row)

    def list_recent(self, limit: int = 50) -> list[CommandLog]:
        rows = self._session.scalars(
            select(CommandLogRow)
            .order_by(CommandLogRow.created_at.desc(), CommandLogRow.id.desc())
            .limit(limit)
        ).all()
        return [self._to_domain(row) for row in rows]

    @staticmethod
    def _to_domain(row: CommandLogRow) -> CommandLog:
        return CommandLog(
            id=row.id,
            command_type=row.command_type,
            device_id=row.device_id,
            payload=dict(row.payload),
            status=row.status,  # type: ignore[arg-type]
            error_message=row.error_message,
            created_at=row.created_at,
        )
