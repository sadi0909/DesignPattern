"""Phase 8 actuator lifecycle tests: domain guards, persistence, and API."""

import os
from uuid import UUID, uuid4

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import delete, select

from application.devices.actuator_state_service import ActuatorStateService
from domain.actuators.context import ActuatorContext
from domain.actuators.errors import IllegalTransitionError, UnknownActuatorStateError
from domain.actuators.state import ACTUATOR_STATES, state_for
from domain.devices.entity import Device
from domain.devices.errors import DeviceNotFoundError
from infrastructure.db import SessionLocal
from infrastructure.persistence.device_repository import DeviceRepository
from infrastructure.persistence.models import ActuatorStateRow, DeviceRow
from interfaces.api.devices import get_actuator_state_service
from main import app


def test_every_state_is_registered_and_targets_exist():
    assert set(ACTUATOR_STATES) == {"off", "idle", "running", "error", "maintenance"}
    for name in ACTUATOR_STATES:
        state = state_for(name)
        assert name not in state.allowed_targets
        assert all(target in ACTUATOR_STATES for target in state.allowed_targets)
        assert state.allowed_commands()


def test_idle_to_running_is_allowed_and_commands_change():
    context = ActuatorContext(uuid4(), state_for("idle"))
    assert context.allowed_commands() == ["start_pump", "enter_maintenance", "shutdown"]

    assert context.transition("running") == "running"
    assert context.state_name == "running"
    assert context.allowed_commands() == ["stop_pump"]


def test_running_to_maintenance_is_rejected_and_state_is_unchanged():
    context = ActuatorContext(uuid4(), state_for("running"))
    with pytest.raises(IllegalTransitionError, match="running to maintenance"):
        context.transition("maintenance")
    assert context.state_name == "running"


def test_unknown_target_and_unknown_state_are_distinct_errors():
    with pytest.raises(UnknownActuatorStateError):
        ActuatorContext(uuid4(), state_for("idle")).transition("banana")

    with pytest.raises(UnknownActuatorStateError):
        state_for("depth_charge")


def test_error_reset_and_off_enable_paths():
    error_context = ActuatorContext(uuid4(), state_for("error"))
    assert error_context.transition("idle") == "idle"

    off_context = ActuatorContext(uuid4(), state_for("off"))
    assert off_context.transition("idle") == "idle"


class FakeDeviceRepository:
    def __init__(self, device: Device | None) -> None:
        self.device = device

    def get_device(self, device_id: UUID) -> Device | None:
        return self.device


class FakeActuatorStateRepository:
    def __init__(self, state: str | None = None) -> None:
        self.state = state
        self.saved: list[tuple[UUID, str]] = []

    def get_state(self, device_id: UUID) -> str | None:
        return self.state

    def save_state(self, device_id: UUID, state: str) -> None:
        self.saved.append((device_id, state))
        self.state = state


def test_service_saves_only_legal_transitions():
    device_id = uuid4()
    device = Device(
        id=device_id,
        device_type="water_pump",
        role="actuator",
        device_family="simulation",
        display_name="Pump",
    )
    states = FakeActuatorStateRepository("running")
    service = ActuatorStateService(FakeDeviceRepository(device), states)  # type: ignore[arg-type]

    with pytest.raises(IllegalTransitionError):
        service.transition(device_id, "maintenance")
    assert states.saved == []

    updated = service.transition(device_id, "idle")
    assert updated.state == "idle"
    assert states.saved == [(device_id, "idle")]


def test_service_rejects_missing_and_non_actuator_devices():
    sensor = Device(
        id=uuid4(),
        device_type="moisture_sensor",
        role="sensor",
        device_family="simulation",
        display_name="Sensor",
    )
    service = ActuatorStateService(
        FakeDeviceRepository(sensor),  # type: ignore[arg-type]
        FakeActuatorStateRepository("idle"),  # type: ignore[arg-type]
    )
    with pytest.raises(DeviceNotFoundError):
        service.transition(sensor.id, "running")

    missing_service = ActuatorStateService(
        FakeDeviceRepository(None),  # type: ignore[arg-type]
        FakeActuatorStateRepository(),  # type: ignore[arg-type]
    )
    with pytest.raises(DeviceNotFoundError):
        missing_service.transition(uuid4(), "idle")


class FakeActuatorService:
    def __init__(self, device: Device | None = None, error: Exception | None = None) -> None:
        self.device = device
        self.error = error

    def transition(self, device_id: UUID, target: str) -> Device:
        if self.error is not None:
            raise self.error
        if self.device is None:
            raise DeviceNotFoundError(f"Actuator {device_id} does not exist")
        from dataclasses import replace

        return replace(self.device, state=target)


def test_api_returns_state_and_allowed_commands():
    device = Device(
        id=uuid4(),
        device_type="water_pump",
        role="actuator",
        device_family="simulation",
        display_name="Pump",
        state="running",
    )
    app.dependency_overrides[get_actuator_state_service] = lambda: FakeActuatorService(device)
    try:
        with TestClient(app) as client:
            response = client.post(f"/api/devices/{device.id}/transition", json={"target": "running"})
            assert response.status_code == 200
            body = response.json()
            assert body["state"] == "running"
            assert body["allowed_commands"] == ["stop_pump"]

            schema = client.get("/openapi.json").json()
            operation = schema["paths"]["/api/devices/{device_id}/transition"]["post"]
            assert {"400", "404", "409"} <= set(operation["responses"])
            device_schema = schema["components"]["schemas"]["DeviceDto"]["properties"]
            assert {"state", "allowed_commands"} <= set(device_schema)
    finally:
        app.dependency_overrides.pop(get_actuator_state_service, None)


@pytest.mark.parametrize(
    ("error", "expected"),
    [
        (DeviceNotFoundError("Actuator missing"), 404),
        (UnknownActuatorStateError("Unknown actuator state: banana"), 400),
        (IllegalTransitionError("Cannot move an actuator from running to maintenance"), 409),
    ],
)
def test_api_maps_domain_errors_to_status_codes(error: Exception, expected: int):
    app.dependency_overrides[get_actuator_state_service] = lambda: FakeActuatorService(error=error)
    try:
        with TestClient(app) as client:
            response = client.post(f"/api/devices/{uuid4()}/transition", json={"target": "running"})
            assert response.status_code == expected
            assert response.json()["detail"] == str(error)
    finally:
        app.dependency_overrides.pop(get_actuator_state_service, None)


@pytest.mark.skipif(os.getenv("RUN_DB_INTEGRATION") != "1", reason="requires PostgreSQL")
def test_transition_persists_and_illegal_transition_does_not_update_row():
    device_id: UUID | None = None
    try:
        with SessionLocal() as session:
            saved = DeviceRepository(session).save_devices([
                Device(
                    id=None,
                    device_type="water_pump",
                    role="actuator",
                    device_family="simulation",
                    display_name="Phase 8 state test pump",
                )
            ])[0]
            device_id = saved.id
            assert saved.state == "idle"
            assert session.get(ActuatorStateRow, device_id).state == "idle"

        with TestClient(app) as client:
            detail = client.get(f"/api/devices/{device_id}")
            assert detail.status_code == 200
            assert detail.json()["state"] == "idle"
            assert detail.json()["allowed_commands"] == [
                "start_pump",
                "enter_maintenance",
                "shutdown",
            ]

            started = client.post(f"/api/devices/{device_id}/transition", json={"target": "running"})
            assert started.status_code == 200
            assert started.json()["state"] == "running"
            assert started.json()["allowed_commands"] == ["stop_pump"]

            rejected = client.post(
                f"/api/devices/{device_id}/transition", json={"target": "maintenance"}
            )
            assert rejected.status_code == 409

            unknown = client.post(
                f"/api/devices/{device_id}/transition", json={"target": "banana"}
            )
            assert unknown.status_code == 400

            missing = client.post(f"/api/devices/{uuid4()}/transition", json={"target": "idle"})
            assert missing.status_code == 404

        with SessionLocal() as session:
            row = session.get(ActuatorStateRow, device_id)
            assert row is not None
            assert row.state == "running"
            assert session.execute(
                select(ActuatorStateRow.device_id).where(ActuatorStateRow.device_id == device_id)
            ).one()
    finally:
        if device_id is not None:
            with SessionLocal() as session:
                session.execute(delete(DeviceRow).where(DeviceRow.id == device_id))
                session.commit()
