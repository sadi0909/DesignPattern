"""Phase 9 decorator tests: policy order, short-circuiting, persistence, and API."""

import os
from datetime import UTC, datetime, timedelta
from uuid import UUID, uuid4

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import delete, select, update

from domain.actuators.errors import MaxRunTimeExceededError
from domain.actuators.execution import ActuatorExecution
from domain.actuators.ports import ActuatorPort
from domain.devices.entity import Device
from domain.devices.errors import DeviceNotFoundError
from infrastructure.adapters.actuators.composition import build_actuator_port
from infrastructure.db import SessionLocal
from infrastructure.persistence.actuator_state_repository import ActuatorStateSnapshot
from infrastructure.persistence.device_repository import DeviceRepository
from infrastructure.persistence.models import (
    ActuatorExecutionLogRow,
    ActuatorStateRow,
    DeviceRow,
)
from interfaces.api.actuators import get_actuator_execution_service
from main import app


class RecordingActuator(ActuatorPort):
    """Inner adapter double that records whether it was reached."""

    def __init__(self, error: Exception | None = None) -> None:
        self.calls: list[tuple[UUID, str, dict]] = []
        self._error = error

    def apply(self, device_id: UUID, command: str, payload: dict) -> None:
        self.calls.append((device_id, command, payload))
        if self._error is not None:
            raise self._error


class FakeStateRepository:
    def __init__(self, snapshot: ActuatorStateSnapshot | None = None) -> None:
        self.snapshot = snapshot

    def get_snapshot(self, device_id: UUID) -> ActuatorStateSnapshot | None:
        return self.snapshot


class FakeExecutionLogRepository:
    def __init__(self) -> None:
        self.records: list[dict] = []

    def record(
        self,
        device_id: UUID,
        *,
        success: bool,
        policy_applied: list[str],
        message: str | None = None,
    ) -> None:
        self.records.append(
            {
                "device_id": device_id,
                "success": success,
                "policy_applied": policy_applied,
                "message": message,
            }
        )

    def list_recent(self, limit: int = 20) -> list[ActuatorExecution]:
        return []


def build_stack(inner: ActuatorPort, states: FakeStateRepository, executions: FakeExecutionLogRepository):
    return build_actuator_port(
        adapter=inner,
        states=states,  # type: ignore[arg-type]
        executions=executions,  # type: ignore[arg-type]
        max_runtime_seconds=30,
    )


def test_successful_apply_reaches_adapter_and_records_every_policy():
    inner = RecordingActuator()
    executions = FakeExecutionLogRepository()
    port = build_stack(inner, FakeStateRepository(), executions)
    device_id = uuid4()

    port.apply(device_id, "start_pump", {"liters": 2})

    assert inner.calls == [(device_id, "start_pump", {"liters": 2})]
    assert executions.records == [
        {
            "device_id": device_id,
            "success": True,
            "policy_applied": ["maxRunTime", "logging"],
            "message": None,
        }
    ]


def test_max_runtime_blocks_without_calling_inner_and_records_failure():
    inner = RecordingActuator()
    executions = FakeExecutionLogRepository()
    states = FakeStateRepository(
        ActuatorStateSnapshot(
            state="running",
            updated_at=datetime.now(UTC) - timedelta(seconds=120),
        )
    )
    port = build_stack(inner, states, executions)

    with pytest.raises(MaxRunTimeExceededError, match="Max run time exceeded"):
        port.apply(uuid4(), "start_pump", {})

    assert inner.calls == []
    assert len(executions.records) == 1
    written = executions.records[0]
    assert written["success"] is False
    assert written["policy_applied"] == ["maxRunTime", "logging"]
    assert "limit 30s" in written["message"]


def test_running_within_limit_and_idle_states_are_not_blocked():
    now = datetime.now(UTC)
    for snapshot in (
        ActuatorStateSnapshot(state="running", updated_at=now),
        ActuatorStateSnapshot(state="idle", updated_at=now - timedelta(hours=2)),
        None,
    ):
        inner = RecordingActuator()
        executions = FakeExecutionLogRepository()
        port = build_stack(inner, FakeStateRepository(snapshot), executions)
        port.apply(uuid4(), "stop_pump", {})
        assert len(inner.calls) == 1
        assert executions.records[0]["success"] is True


def test_adapter_failure_is_logged_and_reraised():
    inner = RecordingActuator(error=RuntimeError("driver offline"))
    executions = FakeExecutionLogRepository()
    port = build_stack(inner, FakeStateRepository(), executions)

    with pytest.raises(RuntimeError, match="driver offline"):
        port.apply(uuid4(), "start_pump", {})

    assert executions.records[0]["success"] is False
    assert executions.records[0]["message"] == "driver offline"
    assert executions.records[0]["policy_applied"] == ["maxRunTime", "logging"]


class FakeExecutionService:
    def __init__(
        self,
        executions: list[ActuatorExecution] | None = None,
        error: Exception | None = None,
    ) -> None:
        self._executions = executions or []
        self._error = error

    def list_executions(self, limit: int = 20) -> list[ActuatorExecution]:
        return self._executions[:limit]

    def apply(self, device_id: UUID, command: str, payload: dict) -> None:
        if self._error is not None:
            raise self._error


def test_executions_endpoint_and_openapi_schema():
    device_id = uuid4()
    execution = ActuatorExecution(
        id=uuid4(),
        device_id=device_id,
        success=False,
        policy_applied=["maxRunTime", "logging"],
        message="Max run time exceeded",
        created_at=datetime.now(UTC),
    )
    app.dependency_overrides[get_actuator_execution_service] = lambda: FakeExecutionService([execution])
    try:
        with TestClient(app) as client:
            response = client.get("/api/actuators/executions?limit=5")
            assert response.status_code == 200
            body = response.json()
            assert body[0]["device_id"] == str(device_id)
            assert body[0]["success"] is False
            assert body[0]["policy_applied"] == ["maxRunTime", "logging"]

            applied = client.post(
                f"/api/actuators/{device_id}/apply",
                json={"command": "start_pump", "payload": {"liters": 1}},
            )
            assert applied.status_code == 200
            assert applied.json() == {"status": "applied"}

            schema = client.get("/openapi.json").json()
            assert "/api/actuators/executions" in schema["paths"]
            assert "/api/actuators/{device_id}/apply" in schema["paths"]
            properties = schema["components"]["schemas"]["ActuatorExecutionDto"]["properties"]
            assert {
                "id",
                "device_id",
                "success",
                "policy_applied",
                "message",
                "created_at",
            } <= set(properties)
    finally:
        app.dependency_overrides.pop(get_actuator_execution_service, None)


@pytest.mark.parametrize(
    ("error", "expected"),
    [
        (DeviceNotFoundError("Actuator missing"), 404),
        (MaxRunTimeExceededError("Max run time exceeded"), 409),
    ],
)
def test_apply_maps_policy_and_missing_actuator_errors(error: Exception, expected: int):
    app.dependency_overrides[get_actuator_execution_service] = lambda: FakeExecutionService(error=error)
    try:
        with TestClient(app) as client:
            response = client.post(
                f"/api/actuators/{uuid4()}/apply",
                json={"command": "start_pump"},
            )
            assert response.status_code == expected
            assert response.json()["detail"] == str(error)
    finally:
        app.dependency_overrides.pop(get_actuator_execution_service, None)


@pytest.mark.skipif(os.getenv("RUN_DB_INTEGRATION") != "1", reason="requires PostgreSQL")
def test_execution_log_persists_blocked_and_successful_attempts():
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
                        display_name="Phase 9 execution test pump",
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
            blocked = client.post(
                f"/api/actuators/{device_id}/apply",
                json={"command": "start_pump"},
            )
            assert blocked.status_code == 409
            assert "Max run time exceeded" in blocked.json()["detail"]

            rows = client.get("/api/actuators/executions?limit=100").json()
            attempts = [row for row in rows if row["device_id"] == str(device_id)]
            assert len(attempts) == 1
            assert attempts[0]["success"] is False
            assert attempts[0]["policy_applied"] == ["maxRunTime", "logging"]
            assert "Max run time exceeded" in attempts[0]["message"]

        with SessionLocal() as session:
            session.execute(
                update(ActuatorStateRow)
                .where(ActuatorStateRow.device_id == device_id)
                .values(state="idle", updated_at=datetime.now(UTC))
            )
            session.commit()

        with TestClient(app) as client:
            allowed = client.post(
                f"/api/actuators/{device_id}/apply",
                json={"command": "start_pump", "payload": {"liters": 2}},
            )
            assert allowed.status_code == 200
            assert allowed.json() == {"status": "applied"}

            missing = client.post(
                f"/api/actuators/{uuid4()}/apply",
                json={"command": "start_pump"},
            )
            assert missing.status_code == 404

        with SessionLocal() as session:
            rows = session.scalars(
                select(ActuatorExecutionLogRow)
                .where(ActuatorExecutionLogRow.device_id == device_id)
                .order_by(ActuatorExecutionLogRow.created_at)
            ).all()
            assert len(rows) == 2
            assert rows[0].success is False
            assert rows[1].success is True
            assert rows[1].policy_applied == ["maxRunTime", "logging"]
    finally:
        if device_id is not None:
            with SessionLocal() as session:
                session.execute(delete(DeviceRow).where(DeviceRow.id == device_id))
                session.commit()
