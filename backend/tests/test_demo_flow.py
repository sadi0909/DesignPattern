"""Phase 14 — the demo story as one integration test.

One test walks the narrative a reviewer follows by hand: configure a dry
location, provision a device family, read a sensor, watch the WebSocket feed,
start the pump, then confirm the same facts survive a fresh client and are
visible through the overview, alert, command, and history APIs.

Requires PostgreSQL: ``RUN_DB_INTEGRATION=1 pytest tests/test_demo_flow.py -q``.
"""

import os
from datetime import datetime, timedelta
from uuid import UUID

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import delete

from infrastructure.db import SessionLocal
from infrastructure.persistence.models import (
    ActuatorExecutionLogRow,
    ActuatorStateRow,
    AlertRow,
    CommandLogRow,
    DeviceRow,
    LocationRow,
    ReadingRow,
    ZoneRow,
)
from main import app

pytestmark = pytest.mark.skipif(
    os.getenv("RUN_DB_INTEGRATION") != "1",
    reason="set RUN_DB_INTEGRATION=1 to run against the configured PostgreSQL database",
)


def test_demo_story_covers_setup_read_alert_command_and_feed():
    location_id: UUID | None = None
    device_ids: list[UUID] = []
    try:
        with TestClient(app) as client:
            location = client.post(
                "/api/locations/config",
                json={
                    "location_name": "Phase 14 demo greenhouse",
                    "zones": [
                        {
                            "name": "Dry zone",
                            "moisture_threshold_low": 0.85,
                            "moisture_threshold_high": 0.95,
                            "schedule": {},
                        }
                    ],
                },
            )
            assert location.status_code == 201
            location_id = UUID(location.json()["location"]["id"])

            provisioned = client.post("/api/devices/provision?family=simulation")
            assert provisioned.status_code == 201
            devices = provisioned.json()
            assert len(devices) == 4
            device_ids = [UUID(device["id"]) for device in devices]

            sensor = next(
                device
                for device in devices
                if device["role"] == "sensor"
                and device["device_type"] == "moisture_sensor"
            )
            pump = next(
                device
                for device in devices
                if device["device_type"] == "water_pump"
            )

            for device in (sensor, pump):
                assigned = client.patch(
                    f"/api/devices/{device['id']}/location",
                    json={"location_id": str(location_id)},
                )
                assert assigned.status_code == 200
                assert assigned.json()["location_id"] == str(location_id)

            with client.websocket_connect("/api/ws") as websocket:
                read = client.post(f"/api/sensors/{sensor['id']}/read")
                assert read.status_code == 201
                reading = read.json()

                # The threshold subscriber publishes its alert inside the
                # reading publish, so the socket may see alert.created first.
                # Treat the pair as unordered and assert both arrived.
                events = {}
                for _ in range(2):
                    event = websocket.receive_json()
                    events[event["type"]] = event
                assert set(events) == {"reading.created", "alert.created"}
                reading_event = events["reading.created"]
                alert_event = events["alert.created"]

                started = client.post(
                    f"/api/devices/{pump['id']}/commands",
                    json={"command_type": "start_pump", "payload": {}},
                )
                assert started.status_code == 200
                assert started.json()["status"] == "success"

                state_event = websocket.receive_json()

            assert reading_event["type"] == "reading.created"
            assert reading_event["payload"]["device_id"] == sensor["id"]
            assert reading_event["payload"]["value"] == reading["value"]

            assert alert_event["type"] == "alert.created"
            assert alert_event["payload"]["location_id"] == str(location_id)
            assert alert_event["payload"]["device_id"] == sensor["id"]
            assert alert_event["payload"]["event_type"] == "threshold.crossed"

            assert state_event["type"] == "actuator.state_changed"
            assert state_event["payload"]["device_id"] == pump["id"]
            assert state_event["payload"]["from_state"] == "idle"
            assert state_event["payload"]["to_state"] == "running"

            # The chart window returns the persisted reading oldest-first.
            recorded_at = datetime.fromisoformat(reading["recorded_at"])
            window = client.get(
                f"/api/sensors/{sensor['id']}/readings",
                params={
                    "from": (recorded_at - timedelta(minutes=1)).isoformat(),
                    "to": (recorded_at + timedelta(minutes=1)).isoformat(),
                },
            )
            assert window.status_code == 200
            assert [row["device_id"] for row in window.json()] == [sensor["id"]]
            assert window.json()[0]["value"] == reading["value"]

            overview = client.get(f"/api/locations/{location_id}/overview")
            assert overview.status_code == 200
            summary = overview.json()
            assert summary["device_counts"] == {"sensor": 1, "actuator": 1}
            assert [row["device_id"] for row in summary["latest_readings"]] == [
                sensor["id"]
            ]
            assert summary["strategy_key"] == "conservative"

            alerts = client.get(f"/api/alerts?location_id={location_id}")
            assert alerts.status_code == 200
            assert len(alerts.json()) == 1
            assert alerts.json()[0]["device_id"] == sensor["id"]

            commands = client.get("/api/commands?limit=100")
            assert commands.status_code == 200
            attempts = [
                row for row in commands.json() if row["device_id"] == pump["id"]
            ]
            assert [row["status"] for row in attempts] == ["success"]

            pump_state = client.get(f"/api/devices/{pump['id']}")
            assert pump_state.status_code == 200
            assert pump_state.json()["state"] == "running"
            assert pump_state.json()["allowed_commands"] == ["stop_pump"]

        # A fresh client is a page refresh: the alert is database-backed.
        with TestClient(app) as client:
            refreshed = client.get(f"/api/alerts?location_id={location_id}")
            assert refreshed.status_code == 200
            assert len(refreshed.json()) == 1
    finally:
        if location_id is not None or device_ids:
            with SessionLocal() as session:
                if device_ids:
                    session.execute(
                        delete(AlertRow).where(AlertRow.device_id.in_(device_ids))
                    )
                    session.execute(
                        delete(ActuatorExecutionLogRow).where(
                            ActuatorExecutionLogRow.device_id.in_(device_ids)
                        )
                    )
                    session.execute(
                        delete(CommandLogRow).where(
                            CommandLogRow.device_id.in_(device_ids)
                        )
                    )
                    session.execute(
                        delete(ActuatorStateRow).where(
                            ActuatorStateRow.device_id.in_(device_ids)
                        )
                    )
                    session.execute(
                        delete(ReadingRow).where(ReadingRow.device_id.in_(device_ids))
                    )
                    session.execute(delete(DeviceRow).where(DeviceRow.id.in_(device_ids)))
                if location_id is not None:
                    session.execute(
                        delete(AlertRow).where(AlertRow.location_id == location_id)
                    )
                    session.execute(
                        delete(ZoneRow).where(ZoneRow.location_id == location_id)
                    )
                    session.execute(
                        delete(LocationRow).where(LocationRow.id == location_id)
                    )
                session.commit()
