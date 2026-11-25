"""Phase 11 observer tests: bus fan-out, alerts, and the polling feed API."""

import os
from datetime import UTC, datetime
from pathlib import Path
from uuid import UUID, uuid4

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import delete, select

from application.alerts.subscribers import (
    AlertPersistenceSubscriber,
    MoistureThresholdSubscriber,
)
from application.commands.service import CommandService
from application.readings.service import ReadingService
from domain.actuators.ports import ActuatorPort
from domain.alerts.entity import Alert
from domain.commands.log import CommandLog
from domain.devices.entity import Device
from domain.events.bus import EventBus
from domain.events.events import (
    AlertCreated,
    CommandExecuted,
    ReadingTaken,
    ThresholdCrossed,
)
from domain.locations.entity import Location, LocationConfig, Zone
from domain.sensors.reading import Reading
from infrastructure.db import SessionLocal
from infrastructure.persistence.models import (
    AlertRow,
    DeviceRow,
    LocationRow,
    ReadingRow,
)
from main import app


class FakeAlertRepository:
    def __init__(self) -> None:
        self.alerts: list[Alert] = []

    def record(
        self,
        *,
        location_id: UUID | None,
        device_id: UUID | None,
        severity: str,
        message: str,
        event_type: str,
        status: str = "active",
    ) -> Alert:
        alert = Alert(
            id=uuid4(),
            location_id=location_id,
            device_id=device_id,
            severity=severity,
            message=message,
            event_type=event_type,
            status=status,
            created_at=datetime.now(UTC),
            acknowledged_at=None,
        )
        self.alerts.append(alert)
        return alert

    def has_active(self, device_id: UUID, event_type: str) -> bool:
        return any(
            alert.device_id == device_id
            and alert.event_type == event_type
            and alert.status == "active"
            for alert in self.alerts
        )


class FakeLocationRepository:
    def __init__(self, config: LocationConfig) -> None:
        self._config = config

    def get_config(self, location_id: UUID) -> LocationConfig | None:
        return self._config if self._config.location.id == location_id else None


class FakeDeviceRepository:
    def __init__(self, device: Device) -> None:
        self._device = device

    def get_device(self, device_id: UUID) -> Device | None:
        return self._device if self._device.id == device_id else None


class FakeReadingRepository:
    def __init__(self) -> None:
        self.rows: list[Reading] = []

    def insert(self, reading: Reading) -> Reading:
        self.rows.append(reading)
        return reading


class StubSensorPort:
    def __init__(self, value: float) -> None:
        self._value = value

    def read(self, device: Device) -> Reading:
        return Reading(
            device_id=device.id,  # type: ignore[arg-type]
            value=self._value,
            unit="percent",
            source="simulation",
            recorded_at=datetime.now(UTC),
        )


def _config(low: float = 0.4, high: float = 0.7, zone_name: str = "Zone A") -> LocationConfig:
    location_id = uuid4()
    return LocationConfig(
        location=Location(
            id=location_id,
            name="Greenhouse",
            zones=(
                Zone(
                    id=uuid4(),
                    location_id=location_id,
                    name=zone_name,
                    moisture_threshold_low=low,
                    moisture_threshold_high=high,
                ),
            ),
        )
    )


def _reading_event(
    location_id: UUID | None,
    *,
    device_id: UUID | None = None,
    value: float = 25.0,
    sensor_type: str = "moisture_sensor",
    unit: str = "percent",
) -> ReadingTaken:
    return ReadingTaken(
        device_id=device_id or uuid4(),
        location_id=location_id,
        sensor_type=sensor_type,
        value=value,
        unit=unit,
    )


def _wire_threshold_pipeline(
    config: LocationConfig,
) -> tuple[EventBus, FakeAlertRepository]:
    bus = EventBus()
    alerts = FakeAlertRepository()
    threshold = MoistureThresholdSubscriber(FakeLocationRepository(config), bus)
    persistence = AlertPersistenceSubscriber(alerts)  # type: ignore[arg-type]
    bus.subscribe(ReadingTaken, threshold.handle)
    bus.subscribe(ThresholdCrossed, persistence.handle)
    return bus, alerts


def test_bus_fans_out_to_every_subscriber_and_unsubscribe_stops_delivery():
    bus = EventBus()
    first: list[ReadingTaken] = []
    second: list[ReadingTaken] = []
    unsubscribe = bus.subscribe(ReadingTaken, first.append)
    bus.subscribe(ReadingTaken, second.append)

    event = _reading_event(None)
    bus.publish(event)

    assert len(first) == 1
    assert len(second) == 1

    unsubscribe()
    bus.publish(event)

    assert len(first) == 1
    assert len(second) == 2


def test_failing_subscriber_does_not_block_later_subscribers(caplog):
    bus = EventBus()
    delivered: list[ReadingTaken] = []

    def explode(event: ReadingTaken) -> None:
        raise RuntimeError("alert writer offline")

    bus.subscribe(ReadingTaken, explode)
    bus.subscribe(ReadingTaken, delivered.append)

    with caplog.at_level("ERROR"):
        bus.publish(_reading_event(None))

    assert len(delivered) == 1
    assert "alert writer offline" in caplog.text


def test_low_moisture_publishes_threshold_and_persists_warning_alert():
    config = _config(low=0.4, high=0.7)
    bus, alerts = _wire_threshold_pipeline(config)

    bus.publish(_reading_event(config.location.id, value=25.0))

    assert len(alerts.alerts) == 1
    alert = alerts.alerts[0]
    assert alert.event_type == "threshold.crossed"
    assert alert.severity == "warning"
    assert alert.status == "active"
    assert alert.location_id == config.location.id
    assert "below the low threshold" in alert.message


def test_moisture_above_the_high_threshold_is_also_an_alert():
    config = _config(low=0.4, high=0.7)
    bus, alerts = _wire_threshold_pipeline(config)

    bus.publish(_reading_event(config.location.id, value=85.0))

    assert len(alerts.alerts) == 1
    assert "above the high threshold" in alerts.alerts[0].message


def test_repeated_dry_readings_do_not_duplicate_an_active_threshold_alert():
    config = _config(low=0.4, high=0.7)
    bus, alerts = _wire_threshold_pipeline(config)
    device_id = uuid4()

    bus.publish(_reading_event(config.location.id, device_id=device_id, value=20.0))
    bus.publish(_reading_event(config.location.id, device_id=device_id, value=18.0))

    assert len(alerts.alerts) == 1


def test_unassigned_or_non_moisture_readings_do_not_alert():
    config = _config()
    bus, alerts = _wire_threshold_pipeline(config)

    bus.publish(_reading_event(None, value=5.0))
    bus.publish(
        _reading_event(
            config.location.id,
            value=5.0,
            sensor_type="light_sensor",
            unit="lux",
        )
    )

    assert alerts.alerts == []


def test_persisted_alert_is_announced_for_realtime_subscribers():
    config = _config(low=0.4, high=0.7)
    bus = EventBus()
    alerts = FakeAlertRepository()
    announced: list[AlertCreated] = []
    bus.subscribe(AlertCreated, announced.append)
    bus.subscribe(
        ReadingTaken,
        MoistureThresholdSubscriber(FakeLocationRepository(config), bus).handle,
    )
    bus.subscribe(
        ThresholdCrossed,
        AlertPersistenceSubscriber(alerts, events=bus).handle,  # type: ignore[arg-type]
    )

    bus.publish(_reading_event(config.location.id, value=20.0))

    assert len(alerts.alerts) == 1
    assert len(announced) == 1
    assert announced[0].alert_id == alerts.alerts[0].id
    assert announced[0].event_type == "threshold.crossed"
    assert announced[0].status == "active"


def test_failed_command_persists_a_critical_alert_but_success_does_not():
    bus = EventBus()
    alerts = FakeAlertRepository()
    persistence = AlertPersistenceSubscriber(alerts)  # type: ignore[arg-type]
    bus.subscribe(CommandExecuted, persistence.handle)
    device_id = uuid4()
    location_id = uuid4()

    bus.publish(
        CommandExecuted(
            device_id=device_id,
            location_id=location_id,
            command_type="stop_pump",
            status="failed",
            error_message="driver offline",
        )
    )
    bus.publish(
        CommandExecuted(
            device_id=device_id,
            location_id=location_id,
            command_type="start_pump",
            status="success",
        )
    )

    assert len(alerts.alerts) == 1
    alert = alerts.alerts[0]
    assert alert.event_type == "command.failed"
    assert alert.severity == "critical"
    assert "driver offline" in alert.message


def test_reading_service_publishes_only_after_the_reading_is_persisted():
    location_id = uuid4()
    device = Device(
        id=uuid4(),
        device_type="moisture_sensor",
        role="sensor",
        device_family="simulation",
        display_name="Test sensor",
        location_id=location_id,
    )
    readings = FakeReadingRepository()
    bus = EventBus()
    observed: list[tuple[ReadingTaken, int]] = []
    bus.subscribe(ReadingTaken, lambda event: observed.append((event, len(readings.rows))))

    service = ReadingService(
        FakeDeviceRepository(device),  # type: ignore[arg-type]
        readings,  # type: ignore[arg-type]
        adapter_selector=lambda _: StubSensorPort(22.0),
        events=bus,
    )
    service.take_reading(device.id)  # type: ignore[arg-type]

    assert len(observed) == 1
    event, persisted_count = observed[0]
    assert persisted_count == 1
    assert event.device_id == device.id
    assert event.location_id == location_id
    assert event.value == 22.0


class FakeStateRepository:
    def __init__(self, state: str = "idle") -> None:
        self.state = state

    def get_state(self, device_id: UUID) -> str | None:
        return self.state

    def save_state(self, device_id: UUID, state: str) -> None:
        self.state = state


class FailingPort(ActuatorPort):
    def apply(self, device_id: UUID, command: str, payload: dict) -> None:
        raise RuntimeError("driver offline")


class FakeCommandLogRepository:
    def record(
        self,
        *,
        command_type: str,
        device_id: UUID,
        payload: dict[str, object],
        status: str,
        error_message: str | None = None,
    ) -> CommandLog:
        return CommandLog(
            id=uuid4(),
            command_type=command_type,
            device_id=device_id,
            payload=dict(payload),
            status=status,  # type: ignore[arg-type]
            error_message=error_message,
            created_at=datetime.now(UTC),
        )


def test_command_service_publishes_failed_command_for_the_alert_subscriber():
    device = Device(
        id=uuid4(),
        device_type="water_pump",
        role="actuator",
        device_family="simulation",
        display_name="Test pump",
        state="idle",
        location_id=uuid4(),
    )
    bus = EventBus()
    published: list[CommandExecuted] = []
    bus.subscribe(CommandExecuted, published.append)
    service = CommandService(
        FakeDeviceRepository(device),  # type: ignore[arg-type]
        FakeStateRepository(),  # type: ignore[arg-type]
        FailingPort(),
        FakeCommandLogRepository(),  # type: ignore[arg-type]
        events=bus,
    )

    with pytest.raises(RuntimeError, match="driver offline"):
        service.submit(device.id, "start_pump")

    assert len(published) == 1
    assert published[0].status == "failed"
    assert published[0].command_type == "start_pump"


def test_publishers_do_not_import_alert_persistence_or_http():
    backend_dir = Path(__file__).resolve().parents[1]
    for relative_path in (
        "src/application/readings/service.py",
        "src/application/commands/service.py",
    ):
        source = (backend_dir / relative_path).read_text(encoding="utf-8")
        assert "AlertRepository" not in source
        assert "alert_repository" not in source
        assert "interfaces.api" not in source


def test_alerts_route_is_documented_in_openapi():
    with TestClient(app) as client:
        schema = client.get("/openapi.json").json()

    operation = schema["paths"]["/api/alerts"]["get"]
    assert operation["tags"] == ["alerts"]
    assert "status" in {parameter["name"] for parameter in operation["parameters"]}
    properties = schema["components"]["schemas"]["AlertDto"]["properties"]
    assert {
        "id",
        "location_id",
        "device_id",
        "severity",
        "message",
        "event_type",
        "status",
        "created_at",
    } <= set(properties)


@pytest.mark.skipif(os.getenv("RUN_DB_INTEGRATION") != "1", reason="requires PostgreSQL")
def test_low_moisture_read_persists_an_alert_visible_through_the_api():
    location_id: UUID | None = None
    device_id: UUID | None = None
    try:
        with TestClient(app) as client:
            location = client.post(
                "/api/locations/config",
                json={
                    "location_name": "Phase 11 alert greenhouse",
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

            sensor = client.post("/api/sensors", json={"type": "moisture"})
            assert sensor.status_code == 201
            device_id = UUID(sensor.json()["id"])

            assigned = client.patch(
                f"/api/devices/{device_id}/location",
                json={"location_id": str(location_id)},
            )
            assert assigned.status_code == 200

            read = client.post(f"/api/sensors/{device_id}/read")
            assert read.status_code == 201

            feed = client.get(
                f"/api/alerts?status=active&location_id={location_id}"
            )
            assert feed.status_code == 200
            rows = feed.json()
            assert len(rows) == 1
            assert rows[0]["event_type"] == "threshold.crossed"
            assert rows[0]["severity"] == "warning"
            assert rows[0]["device_id"] == str(device_id)
            assert "below the low threshold" in rows[0]["message"]

        # A fresh client simulates a page refresh: the alert is DB-backed.
        with TestClient(app) as client:
            refreshed = client.get(
                f"/api/alerts?status=active&location_id={location_id}"
            )
            assert refreshed.status_code == 200
            assert len(refreshed.json()) == 1

        with SessionLocal() as session:
            rows = session.scalars(
                select(AlertRow).where(AlertRow.device_id == device_id)
            ).all()
            assert len(rows) == 1
            assert rows[0].status == "active"
    finally:
        if device_id is not None or location_id is not None:
            with SessionLocal() as session:
                if device_id is not None:
                    session.execute(delete(AlertRow).where(AlertRow.device_id == device_id))
                    session.execute(delete(ReadingRow).where(ReadingRow.device_id == device_id))
                    session.execute(delete(DeviceRow).where(DeviceRow.id == device_id))
                if location_id is not None:
                    session.execute(delete(AlertRow).where(AlertRow.location_id == location_id))
                    session.execute(delete(LocationRow).where(LocationRow.id == location_id))
                session.commit()
