"""Idempotent demo data for local review (Phase 12).

Fixed UUIDs make the seed safe to run repeatedly: rows that already exist are
left untouched, so a reviewer can migrate an empty database and immediately
open the dashboard with a location, a sensor, a pump, and one reading.
"""

from datetime import UTC, datetime, timedelta
from uuid import NAMESPACE_URL, uuid5

from sqlalchemy.orm import Session

from infrastructure.db import SessionLocal
from infrastructure.persistence.models import (
    ActuatorStateRow,
    AutomationRuleRow,
    DeviceRow,
    LocationRow,
    ReadingRow,
    ZoneRow,
)

NAMESPACE = uuid5(NAMESPACE_URL, "smart-greenhouse/demo")
LOCATION_ID = uuid5(NAMESPACE, "location")
ZONE_ID = uuid5(NAMESPACE, "zone")
SENSOR_ID = uuid5(NAMESPACE, "sensor")
PUMP_ID = uuid5(NAMESPACE, "pump")
RULE_ID = uuid5(NAMESPACE, "automation-rule")
READING_ID = uuid5(NAMESPACE, "reading")


def seed_demo_data(session: Session) -> bool:
    """Insert any missing demo rows; returns True when something was added."""
    created = False

    if session.get(LocationRow, LOCATION_ID) is None:
        session.add(LocationRow(id=LOCATION_ID, name="Demo Greenhouse"))
        created = True
    session.flush()  # children reference the location; no ORM relationships exist

    if session.get(ZoneRow, ZONE_ID) is None:
        session.add(
            ZoneRow(
                id=ZONE_ID,
                location_id=LOCATION_ID,
                name="Demo Zone",
                moisture_threshold_low=0.35,
                moisture_threshold_high=0.65,
                schedule={},
            )
        )
        created = True

    if session.get(DeviceRow, SENSOR_ID) is None:
        session.add(
            DeviceRow(
                id=SENSOR_ID,
                device_type="moisture_sensor",
                role="sensor",
                device_family="simulation",
                location_id=LOCATION_ID,
                display_name="Demo moisture sensor",
                default_config={},
            )
        )
        created = True

    if session.get(DeviceRow, PUMP_ID) is None:
        session.add(
            DeviceRow(
                id=PUMP_ID,
                device_type="water_pump",
                role="actuator",
                device_family="simulation",
                location_id=LOCATION_ID,
                display_name="Demo water pump",
                default_config={},
            )
        )
        created = True

    session.flush()  # actuator state and readings reference the devices

    if session.get(ActuatorStateRow, PUMP_ID) is None:
        session.add(ActuatorStateRow(device_id=PUMP_ID, state="idle"))
        created = True

    if session.get(AutomationRuleRow, RULE_ID) is None:
        session.add(
            AutomationRuleRow(
                id=RULE_ID,
                location_id=LOCATION_ID,
                strategy_key="conservative",
                parameters={},
            )
        )
        created = True

    if session.get(ReadingRow, READING_ID) is None:
        session.add(
            ReadingRow(
                id=READING_ID,
                device_id=SENSOR_ID,
                value=48.0,
                unit="percent",
                source="simulation",
                recorded_at=datetime.now(UTC) - timedelta(minutes=5),
            )
        )
        created = True

    session.commit()
    return created


def main() -> None:
    with SessionLocal() as session:
        changed = seed_demo_data(session)
    print("Seed complete: demo rows inserted." if changed else "Seed complete: demo rows already present.")


if __name__ == "__main__":
    main()
