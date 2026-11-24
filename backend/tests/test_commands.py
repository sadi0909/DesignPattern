"""Phase 10 command object, invoker, and audit tests."""

import os
from datetime import UTC, datetime, timedelta
from uuid import UUID, uuid4

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import delete, select, update

from application.commands.service import CommandService
from domain.actuators.ports import ActuatorPort
from domain.commands.errors import (
    CommandRejectedError,
    CommandValidationError,
    UnknownCommandTypeError,
)
from domain.commands.light import SetLightLevelCommand
from domain.commands.log import CommandLog
from domain.commands.pump import StartPumpCommand, StopPumpCommand
from domain.commands.registry import create_command
from domain.devices.entity import Device
from domain.devices.errors import DeviceNotFoundError
from infrastructure.db import SessionLocal
from infrastructure.persistence.device_repository import DeviceRepository
from infrastructure.persistence.models import (
    ActuatorExecutionLogRow,
    ActuatorStateRow,
    AlertRow,
    CommandLogRow,
    DeviceRow,
)
from main import app


class FakeDeviceRepository:
    def __init__(self, device: Device | None) -> None:
        self.device = device

    def get_device(self, device_id: UUID) -> Device | None:
        if self.device is None or self.device.id != device_id:
            return None
        return self.device


class FakeStateRepository:
    def __init__(self, state: str = "idle") -> None:
        self.state = state
        self.saved: list[tuple[UUID, str]] = []

    def get_state(self, device_id: UUID) -> str | None:
        return self.state

    def save_state(self, device_id: UUID, state: str) -> None:
        self.saved.append((device_id, state))
        self.state = state


class RecordingPort(ActuatorPort):
    def __init__(self, error: Exception | None = None) -> None:
        self.calls: list[tuple[UUID, str, dict]] = []
        self._error = error

    def apply(self, device_id: UUID, command: str, payload: dict) -> None:
        self.calls.append((device_id, command, payload))
        if self._error is not None:
            raise self._error


class FakeCommandLogRepository:
    def __init__(self) -> None:
        self.logs: list[CommandLog] = []

    def record(
        self,
        *,
        command_type: str,
        device_id: UUID,
        payload: dict[str, object],
        status: str,
        error_message: str | None = None,
    ) -> CommandLog:
        log = CommandLog(
            id=uuid4(),
            command_type=command_type,
            device_id=device_id,
            payload=dict(payload),
            status=status,  # type: ignore[arg-type]
            error_message=error_message,
            created_at=datetime.now(UTC),
        )
        self.logs.append(log)
        return log

    def list_recent(self, limit: int = 50) -> list[CommandLog]:
        return self.logs[:limit]


def make_pump(state: str = "idle") -> Device:
    return Device(
        id=uuid4(),
        device_type="water_pump",
        role="actuator",
        device_family="simulation",
        display_name="Test pump",
        state=state,
    )


def make_service(
    device: Device,
    state: str = "idle",
    port: RecordingPort | None = None,
    logs: FakeCommandLogRepository | None = None,
) -> tuple[CommandService, FakeStateRepository, RecordingPort, FakeCommandLogRepository]:
    states = FakeStateRepository(state)
    port = port or RecordingPort()
    log_repository = logs or FakeCommandLogRepository()
    service = CommandService(
        FakeDeviceRepository(device),  # type: ignore[arg-type]
        states,  # type: ignore[arg-type]
        port,
        log_repository,  # type: ignore[arg-type]
    )
    return service, states, port, log_repository


def test_registry_builds_the_three_required_commands():
    assert isinstance(create_command("start_pump", {}), StartPumpCommand)
    assert isinstance(create_command("stop_pump", {}), StopPumpCommand)
    assert isinstance(create_command("set_light_level", {"level": 60}), SetLightLevelCommand)

    with pytest.raises(UnknownCommandTypeError, match="Unknown command type"):
        create_command("open_roof", {})


def test_set_light_level_requires_a_numeric_level():
    with pytest.raises(CommandValidationError, match="between 0 and 100"):
        create_command("set_light_level", {})
    with pytest.raises(CommandValidationError, match="between 0 and 100"):
        create_command("set_light_level", {"level": 101})


def test_start_pump_succeeds_through_port_and_advances_state():
    device = make_pump()
    service, states, port, logs = make_service(device)

    log = service.submit(device.id, "start_pump", {"liters": 2})

    assert log.status == "success"
    assert port.calls == [(device.id, "start_pump", {"liters": 2})]
    assert states.saved == [(device.id, "running")]
    assert logs.logs[0].status == "success"


def test_rejected_command_is_logged_but_never_reaches_the_port_or_state():
    device = make_pump(state="running")
    service, states, port, logs = make_service(device, state="running")

    with pytest.raises(CommandRejectedError, match="not allowed in state running"):
        service.submit(device.id, "start_pump", {})

    assert port.calls == []
    assert states.saved == []
    assert logs.logs[0].status == "rejected"
    assert "not allowed in state running" in (logs.logs[0].error_message or "")


def test_set_light_level_succeeds_for_a_grow_light_without_a_lifecycle_transition():
    device = Device(
        id=uuid4(),
        device_type="grow_light",
        role="actuator",
        device_family="simulation",
        display_name="Test light",
        state="idle",
    )
    service, states, port, logs = make_service(device)

    log = service.submit(device.id, "set_light_level", {"level": 65})

    assert log.status == "success"
    assert log.payload == {"level": 65}
    assert port.calls == [(device.id, "set_light_level", {"level": 65})]
    assert states.saved == []
    assert logs.logs[0].status == "success"


def test_set_light_level_is_rejected_for_a_pump_before_the_port():
    device = make_pump()
    service, _, port, logs = make_service(device)

    with pytest.raises(CommandRejectedError, match="not valid for water_pump"):
        service.submit(device.id, "set_light_level", {"level": 65})

    assert port.calls == []
    assert logs.logs[0].status == "rejected"


def test_port_failure_is_logged_as_failed_and_state_is_unchanged():
    device = make_pump()
    service, states, _, logs = make_service(device, port=RecordingPort(RuntimeError("driver offline")))

    with pytest.raises(RuntimeError, match="driver offline"):
        service.submit(device.id, "start_pump", {})

    assert states.saved == []
    assert logs.logs[0].status == "failed"
    assert logs.logs[0].error_message == "driver offline"


def test_missing_or_sensor_device_is_not_found():
    missing = uuid4()
    service, _, _, _ = make_service(make_pump())
    with pytest.raises(DeviceNotFoundError):
        service.submit(missing, "start_pump", {})

    sensor = Device(
        id=uuid4(),
        device_type="moisture_sensor",
        role="sensor",
        device_family="simulation",
        display_name="Sensor",
    )
    sensor_service, _, _, _ = make_service(sensor)
    with pytest.raises(DeviceNotFoundError):
        sensor_service.submit(sensor.id, "start_pump", {})


@pytest.mark.skipif(os.getenv("RUN_DB_INTEGRATION") != "1", reason="requires PostgreSQL")
def test_command_api_persists_success_rejection_and_execution_attempts():
    device_id: UUID | None = None
    try:
        with SessionLocal() as session:
            saved = DeviceRepository(session).save_devices(
                [
                    Device(
                        id=None,
                        device_type="water_pump",
                        role="actuator",
                        device_family="simulation",
                        display_name="Phase 10 command test pump",
                    )
                ]
            )[0]
            device_id = saved.id

        with TestClient(app) as client:
            started = client.post(
                "/api/commands",
                json={"command_type": "start_pump", "device_id": str(device_id)},
            )
            assert started.status_code == 200
            assert started.json()["status"] == "success"
            assert started.json()["command_type"] == "start_pump"

            state = client.get(f"/api/devices/{device_id}")
            assert state.status_code == 200
            assert state.json()["state"] == "running"
            assert state.json()["allowed_commands"] == ["stop_pump"]

            rejected = client.post(
                "/api/commands",
                json={"command_type": "start_pump", "device_id": str(device_id)},
            )
            assert rejected.status_code == 409
            assert "not allowed in state running" in rejected.json()["detail"]

            state = client.get(f"/api/devices/{device_id}")
            assert state.json()["state"] == "running"

            stopped = client.post(
                "/api/commands",
                json={"command_type": "stop_pump", "device_id": str(device_id)},
            )
            assert stopped.status_code == 200
            assert stopped.json()["status"] == "success"

            history = client.get("/api/commands?limit=10")
            assert history.status_code == 200
            attempts = [row for row in history.json() if row["device_id"] == str(device_id)]
            assert [row["status"] for row in attempts] == ["success", "rejected", "success"]
            assert attempts[1]["error_message"]
            assert attempts[1]["payload"] == {}

            unknown = client.post(
                "/api/commands",
                json={"command_type": "open_roof", "device_id": str(device_id)},
            )
            assert unknown.status_code == 400

            invalid = client.post(
                "/api/commands",
                json={
                    "command_type": "set_light_level",
                    "device_id": str(device_id),
                    "payload": {},
                },
            )
            assert invalid.status_code == 400

            missing = client.post(
                "/api/commands",
                json={"command_type": "start_pump", "device_id": str(uuid4())},
            )
            assert missing.status_code == 404

        with SessionLocal() as session:
            command_rows = session.scalars(
                select(CommandLogRow)
                .where(CommandLogRow.device_id == device_id)
                .order_by(CommandLogRow.created_at)
            ).all()
            assert [row.status for row in command_rows] == ["success", "rejected", "success"]
            assert command_rows[0].payload == {}
            assert command_rows[1].error_message
            assert session.get(ActuatorStateRow, device_id).state == "idle"

            execution_rows = session.scalars(
                select(ActuatorExecutionLogRow)
                .where(ActuatorExecutionLogRow.device_id == device_id)
                .order_by(ActuatorExecutionLogRow.created_at)
            ).all()
            # The rejected attempt did not reach the decorated actuator port.
            assert len(execution_rows) == 2
            assert all(row.success for row in execution_rows)
    finally:
        if device_id is not None:
            with SessionLocal() as session:
                # Phase 11 publishes command.failed alerts; remove them before
                # the device delete turns their foreign key into NULL.
                session.execute(delete(AlertRow).where(AlertRow.device_id == device_id))
                session.execute(delete(DeviceRow).where(DeviceRow.id == device_id))
                session.commit()


def test_command_routes_are_documented():
    with TestClient(app) as client:
        schema = client.get("/openapi.json").json()
    assert "/api/commands" in schema["paths"]
    assert "/api/devices/{device_id}/commands" in schema["paths"]
    assert {"400", "404", "409"} <= set(schema["paths"]["/api/commands"]["post"]["responses"])


@pytest.mark.skipif(os.getenv("RUN_DB_INTEGRATION") != "1", reason="requires PostgreSQL")
@pytest.mark.skipif(os.getenv("RUN_DB_INTEGRATION") != "1", reason="requires PostgreSQL")
def test_decorator_failure_is_failed_in_command_and_execution_logs():
    device_id: UUID | None = None
    try:
        with SessionLocal() as session:
            saved = DeviceRepository(session).save_devices(
                [
                    Device(
                        id=None,
                        device_type="water_pump",
                        role="actuator",
                        device_family="simulation",
                        display_name="Phase 10 policy failure pump",
                    )
                ]
            )[0]
            device_id = saved.id
            session.execute(
                update(ActuatorStateRow)
                .where(ActuatorStateRow.device_id == device_id)
                .values(
                    state="running",
                    updated_at=datetime.now(UTC) - timedelta(seconds=120),
                )
            )
            session.commit()

        with TestClient(app) as client:
            response = client.post(
                "/api/commands",
                json={"command_type": "stop_pump", "device_id": str(device_id)},
            )
            assert response.status_code == 409
            assert "Max run time exceeded" in response.json()["detail"]

        with SessionLocal() as session:
            command_row = session.scalars(
                select(CommandLogRow).where(CommandLogRow.device_id == device_id)
            ).one()
            assert command_row.status == "failed"
            assert "Max run time exceeded" in (command_row.error_message or "")

            execution_row = session.scalars(
                select(ActuatorExecutionLogRow).where(
                    ActuatorExecutionLogRow.device_id == device_id
                )
            ).one()
            assert execution_row.success is False
            assert execution_row.policy_applied == ["maxRunTime", "logging"]

            state = session.get(ActuatorStateRow, device_id)
            assert state is not None
            assert state.state == "running"
    finally:
        if device_id is not None:
            with SessionLocal() as session:
                # Phase 11 publishes command.failed alerts; remove them before
                # the device delete turns their foreign key into NULL.
                session.execute(delete(AlertRow).where(AlertRow.device_id == device_id))
                session.execute(delete(DeviceRow).where(DeviceRow.id == device_id))
                session.commit()


@pytest.mark.skipif(os.getenv("RUN_DB_INTEGRATION") != "1", reason="requires PostgreSQL")
def test_device_command_alias_uses_the_same_invoker():
    device_id: UUID | None = None
    try:
        with SessionLocal() as session:
            saved = DeviceRepository(session).save_devices(
                [
                    Device(
                        id=None,
                        device_type="water_pump",
                        role="actuator",
                        device_family="simulation",
                        display_name="Phase 10 command alias pump",
                    )
                ]
            )[0]
            device_id = saved.id

        with TestClient(app) as client:
            response = client.post(
                f"/api/devices/{device_id}/commands",
                json={"command_type": "start_pump"},
            )
            assert response.status_code == 200
            assert response.json()["status"] == "success"
            state = client.get(f"/api/devices/{device_id}").json()
            assert state["state"] == "running"
    finally:
        if device_id is not None:
            with SessionLocal() as session:
                # Phase 11 publishes command.failed alerts; remove them before
                # the device delete turns their foreign key into NULL.
                session.execute(delete(AlertRow).where(AlertRow.device_id == device_id))
                session.execute(delete(DeviceRow).where(DeviceRow.id == device_id))
                session.commit()


@pytest.mark.skipif(os.getenv("RUN_DB_INTEGRATION") != "1", reason="requires PostgreSQL")
def test_set_light_level_is_audited_for_a_grow_light():
    device_id: UUID | None = None
    try:
        with SessionLocal() as session:
            saved = DeviceRepository(session).save_devices(
                [
                    Device(
                        id=None,
                        device_type="grow_light",
                        role="actuator",
                        device_family="simulation",
                        display_name="Phase 10 command test light",
                    )
                ]
            )[0]
            device_id = saved.id

        with TestClient(app) as client:
            response = client.post(
                "/api/commands",
                json={
                    "command_type": "set_light_level",
                    "device_id": str(device_id),
                    "payload": {"level": 70},
                },
            )
            assert response.status_code == 200
            assert response.json()["status"] == "success"
            assert response.json()["payload"] == {"level": 70}

            state = client.get(f"/api/devices/{device_id}")
            assert state.json()["state"] == "idle"

        with SessionLocal() as session:
            row = session.scalars(
                select(CommandLogRow).where(CommandLogRow.device_id == device_id)
            ).one()
            assert row.command_type == "set_light_level"
            assert row.payload == {"level": 70}
            assert row.status == "success"
    finally:
        if device_id is not None:
            with SessionLocal() as session:
                # Phase 11 publishes command.failed alerts; remove them before
                # the device delete turns their foreign key into NULL.
                session.execute(delete(AlertRow).where(AlertRow.device_id == device_id))
                session.execute(delete(DeviceRow).where(DeviceRow.id == device_id))
                session.commit()
