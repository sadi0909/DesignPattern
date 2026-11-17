from dataclasses import dataclass
from datetime import UTC, datetime
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.orm import Session

from .models import ActuatorStateRow


@dataclass(frozen=True, slots=True)
class ActuatorStateSnapshot:
    """The persisted state plus when it was last written."""

    state: str
    updated_at: datetime


class ActuatorStateRepository:
    def __init__(self, session: Session) -> None:
        self._session = session

    def get_snapshot(self, device_id: UUID) -> ActuatorStateSnapshot | None:
        row = self._session.execute(
            select(ActuatorStateRow.state, ActuatorStateRow.updated_at).where(
                ActuatorStateRow.device_id == device_id
            )
        ).one_or_none()
        return None if row is None else ActuatorStateSnapshot(state=row.state, updated_at=row.updated_at)

    def get_state(self, device_id: UUID) -> str | None:
        snapshot = self.get_snapshot(device_id)
        return None if snapshot is None else snapshot.state

    def save_state(self, device_id: UUID, state: str) -> None:
        row = self._session.get(ActuatorStateRow, device_id)
        if row is None:
            self._session.add(ActuatorStateRow(device_id=device_id, state=state))
        else:
            row.state = state
            row.updated_at = datetime.now(UTC)
        self._session.commit()
