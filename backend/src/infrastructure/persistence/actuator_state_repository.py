from datetime import UTC, datetime
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.orm import Session

from .models import ActuatorStateRow


class ActuatorStateRepository:
    def __init__(self, session: Session) -> None:
        self._session = session

    def get_state(self, device_id: UUID) -> str | None:
        return self._session.scalar(
            select(ActuatorStateRow.state).where(ActuatorStateRow.device_id == device_id)
        )

    def save_state(self, device_id: UUID, state: str) -> None:
        row = self._session.get(ActuatorStateRow, device_id)
        if row is None:
            self._session.add(ActuatorStateRow(device_id=device_id, state=state))
        else:
            row.state = state
            row.updated_at = datetime.now(UTC)
        self._session.commit()
