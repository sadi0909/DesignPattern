from uuid import UUID

from sqlalchemy import select
from sqlalchemy.orm import Session

from domain.actuators.execution import ActuatorExecution

from .models import ActuatorExecutionLogRow


class ExecutionLogRepository:
    """Persists every actuator apply attempt and reads the recent history."""

    def __init__(self, session: Session) -> None:
        self._session = session

    def record(
        self,
        device_id: UUID,
        *,
        success: bool,
        policy_applied: list[str],
        message: str | None = None,
    ) -> None:
        self._session.add(
            ActuatorExecutionLogRow(
                device_id=device_id,
                success=success,
                policy_applied=list(policy_applied),
                message=message,
            )
        )
        # Commit immediately: this row must survive the exception that the
        # logging decorator re-raises to the caller.
        self._session.commit()

    def list_recent(self, limit: int = 20) -> list[ActuatorExecution]:
        rows = self._session.scalars(
            select(ActuatorExecutionLogRow)
            .order_by(ActuatorExecutionLogRow.created_at.desc())
            .limit(limit)
        ).all()
        return [self._to_execution(row) for row in rows]

    @staticmethod
    def _to_execution(row: ActuatorExecutionLogRow) -> ActuatorExecution:
        return ActuatorExecution(
            id=row.id,
            device_id=row.device_id,
            success=row.success,
            policy_applied=list(row.policy_applied),
            message=row.message,
            created_at=row.created_at,
        )
