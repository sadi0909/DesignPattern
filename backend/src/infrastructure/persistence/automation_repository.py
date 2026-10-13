from datetime import UTC, datetime
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.orm import Session

from domain.automation.rule import AutomationRule
from domain.sensors.reading import Reading

from .models import AutomationRuleRow, DeviceRow, ReadingRow

# Matches MoistureSensorCreator.device_type. Devices are not yet bound to a
# location, so the latest moisture reading is taken across moisture sensors.
MOISTURE_DEVICE_TYPE = "moisture_sensor"


class AutomationRepository:
    def __init__(self, session: Session) -> None:
        self._session = session

    def get_rule(self, location_id: UUID) -> AutomationRule | None:
        row = self._session.scalars(
            select(AutomationRuleRow).where(AutomationRuleRow.location_id == location_id)
        ).first()
        return None if row is None else self._to_domain(row)

    def upsert_rule(self, location_id: UUID, strategy_key: str) -> AutomationRule:
        """Create or update the one rule for a location."""
        now = datetime.now(UTC)
        row = self._session.scalars(
            select(AutomationRuleRow).where(AutomationRuleRow.location_id == location_id)
        ).first()
        if row is None:
            row = AutomationRuleRow(
                location_id=location_id,
                strategy_key=strategy_key,
                parameters={},
                updated_at=now,
            )
            self._session.add(row)
        else:
            row.strategy_key = strategy_key
            row.updated_at = now
        try:
            self._session.commit()
            self._session.refresh(row)
        except Exception:
            self._session.rollback()
            raise
        return self._to_domain(row)

    def latest_moisture_reading(self) -> Reading | None:
        row = self._session.scalars(
            select(ReadingRow)
            .join(DeviceRow, DeviceRow.id == ReadingRow.device_id)
            .where(DeviceRow.device_type == MOISTURE_DEVICE_TYPE)
            .order_by(ReadingRow.recorded_at.desc(), ReadingRow.id.desc())
            .limit(1)
        ).first()
        if row is None:
            return None
        return Reading(
            device_id=row.device_id,
            value=float(row.value),
            unit=row.unit,
            source=row.source,
            recorded_at=row.recorded_at,
        )

    @staticmethod
    def _to_domain(row: AutomationRuleRow) -> AutomationRule:
        return AutomationRule(
            location_id=row.location_id,
            strategy_key=row.strategy_key,
            updated_at=row.updated_at,
        )
