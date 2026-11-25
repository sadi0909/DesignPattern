"""Phase 12 realtime tests: the bus fans out as WebSocket JSON envelopes."""

from datetime import UTC, datetime
from uuid import uuid4

from fastapi.testclient import TestClient

from application.realtime.ws_subscriber import event_to_message
from domain.events.events import (
    ActuatorStateChanged,
    AlertCreated,
    CommandExecuted,
    ReadingTaken,
)
from infrastructure.events.composition import get_event_bus
from main import app


def test_event_to_message_maps_reading_created():
    device_id = uuid4()

    message = event_to_message(
        ReadingTaken(
            device_id=device_id,
            location_id=None,
            sensor_type="moisture_sensor",
            value=42.5,
            unit="percent",
        )
    )

    assert message is not None
    assert message["type"] == "reading.created"
    assert message["payload"]["device_id"] == str(device_id)
    assert message["payload"]["location_id"] is None
    assert message["payload"]["value"] == 42.5
    assert message["payload"]["unit"] == "percent"


def test_event_to_message_maps_actuator_state_changed():
    device_id = uuid4()

    message = event_to_message(
        ActuatorStateChanged(
            device_id=device_id,
            location_id=None,
            from_state="idle",
            to_state="running",
        )
    )

    assert message is not None
    assert message["type"] == "actuator.state_changed"
    assert message["payload"]["device_id"] == str(device_id)
    assert message["payload"]["from_state"] == "idle"
    assert message["payload"]["to_state"] == "running"


def test_event_to_message_maps_alert_created():
    alert_id = uuid4()
    created_at = datetime.now(UTC)

    message = event_to_message(
        AlertCreated(
            alert_id=alert_id,
            location_id=None,
            device_id=None,
            severity="warning",
            message="Moisture 20.0% is below the low threshold",
            event_type="threshold.crossed",
            status="active",
            created_at=created_at,
        )
    )

    assert message is not None
    assert message["type"] == "alert.created"
    assert message["payload"]["id"] == str(alert_id)
    assert message["payload"]["severity"] == "warning"
    assert message["payload"]["status"] == "active"
    assert message["payload"]["created_at"].startswith(
        created_at.date().isoformat()
    )


def test_event_to_message_ignores_events_without_a_public_message():
    assert (
        event_to_message(
            CommandExecuted(
                device_id=uuid4(),
                location_id=None,
                command_type="start_pump",
                status="success",
            )
        )
        is None
    )


def test_websocket_receives_events_published_on_the_shared_bus():
    device_id = uuid4()
    alert_id = uuid4()

    with TestClient(app) as client, client.websocket_connect("/api/ws") as websocket:
        bus = get_event_bus()
        bus.publish(
            ReadingTaken(
                device_id=device_id,
                location_id=None,
                sensor_type="moisture_sensor",
                value=55.0,
                unit="percent",
            )
        )
        reading = websocket.receive_json()

        bus.publish(
            AlertCreated(
                alert_id=alert_id,
                location_id=None,
                device_id=device_id,
                severity="warning",
                message="Test alert",
                event_type="threshold.crossed",
                status="active",
                created_at=datetime.now(UTC),
            )
        )
        alert = websocket.receive_json()

    assert reading["type"] == "reading.created"
    assert reading["payload"]["device_id"] == str(device_id)
    assert alert["type"] == "alert.created"
    assert alert["payload"]["id"] == str(alert_id)
