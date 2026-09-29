import os
from dataclasses import replace
from uuid import uuid4

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import delete

from application.devices.family_service import DeviceFamilyService
from domain.devices.entity import Device
from infrastructure.db import SessionLocal
from infrastructure.persistence.models import DeviceRow
from interfaces.api.devices import get_device_family_service
from main import app


class InMemoryDeviceRepository:
    def __init__(self) -> None:
        self.devices: list[Device] = []

    def save_devices(self, devices: list[Device]) -> list[Device]:
        saved = [replace(device, id=uuid4()) for device in devices]
        self.devices.extend(saved)
        return saved

    def list_devices(
        self,
        *,
        device_family: str | None = None,
        role: str | None = None,
    ) -> list[Device]:
        return [
            device
            for device in self.devices
            if (device_family is None or device.device_family == device_family)
            and (role is None or device.role == role)
        ]


def test_provision_and_list_device_family():
    repository = InMemoryDeviceRepository()
    app.dependency_overrides[get_device_family_service] = lambda: DeviceFamilyService(repository)
    try:
        with TestClient(app) as client:
            provision_response = client.post("/api/devices/provision?family=simulation")
            assert provision_response.status_code == 201
            provisioned = provision_response.json()
            assert len(provisioned) == 4
            assert {device["device_family"] for device in provisioned} == {"simulation"}
            assert {device["role"] for device in provisioned} == {"sensor", "actuator"}

            list_response = client.get("/api/devices?family=simulation&role=actuator")
            assert list_response.status_code == 200
            actuators = list_response.json()
            assert len(actuators) == 2
            assert all(device["role"] == "actuator" for device in actuators)
    finally:
        app.dependency_overrides.pop(get_device_family_service, None)


def test_openapi_documents_device_dto_and_routes():
    with TestClient(app) as client:
        schema = client.get("/openapi.json").json()

    assert "devices" in schema["paths"]["/api/devices"]["get"]["tags"]
    assert "devices" in schema["paths"]["/api/devices/provision"]["post"]["tags"]
    assert set(schema["components"]["schemas"]["DeviceDto"]["properties"]) == {
        "id",
        "device_type",
        "role",
        "device_family",
        "display_name",
        "default_config",
    }


@pytest.mark.skipif(
    os.getenv("RUN_DB_INTEGRATION") != "1",
    reason="set RUN_DB_INTEGRATION=1 to run against the configured PostgreSQL database",
)
def test_real_database_provisions_both_families_and_preserves_sensors():
    created_device_ids: list[str] = []
    try:
        with TestClient(app) as client:
            baseline_response = client.get("/api/sensors")
            assert baseline_response.status_code == 200
            baseline_sensor_ids = {sensor["id"] for sensor in baseline_response.json()}

            sensor_create_response = client.post(
                "/api/sensors",
                json={"type": "moisture", "display_name": "Phase 3 compatibility smoke sensor"},
            )
            assert sensor_create_response.status_code == 201
            phase_two_sensor_id = sensor_create_response.json()["id"]
            created_device_ids.append(phase_two_sensor_id)

            baseline_actuator_counts: dict[str, int] = {}
            for family in ("simulation", "edge"):
                baseline_actuator_response = client.get(f"/api/devices?family={family}&role=actuator")
                assert baseline_actuator_response.status_code == 200
                baseline_actuator_counts[family] = len(baseline_actuator_response.json())

            for family, protocol in (("simulation", "sim"), ("edge", "gpio-stub")):
                provision_response = client.post(f"/api/devices/provision?family={family}")
                assert provision_response.status_code == 201
                provisioned = provision_response.json()
                created_device_ids.extend(device["id"] for device in provisioned)
                assert len(provisioned) == 4
                assert {device["device_family"] for device in provisioned} == {family}
                assert {device["role"] for device in provisioned} == {"sensor", "actuator"}
                assert {device["default_config"]["protocol"] for device in provisioned} == {protocol}

                family_response = client.get(f"/api/devices?family={family}")
                assert family_response.status_code == 200
                assert all(device["device_family"] == family for device in family_response.json())

                actuator_response = client.get(f"/api/devices?family={family}&role=actuator")
                assert actuator_response.status_code == 200
                assert len(actuator_response.json()) == baseline_actuator_counts[family] + 2

            sensors_response = client.get("/api/sensors")
            assert sensors_response.status_code == 200
            final_sensor_ids = {sensor["id"] for sensor in sensors_response.json()}
            assert baseline_sensor_ids <= final_sensor_ids
            assert phase_two_sensor_id in final_sensor_ids
            simulation_sensor_response = client.get("/api/devices?family=simulation&role=sensor")
            assert simulation_sensor_response.status_code == 200
            assert phase_two_sensor_id in {device["id"] for device in simulation_sensor_response.json()}
    finally:
        if created_device_ids:
            with SessionLocal() as session:
                session.execute(delete(DeviceRow).where(DeviceRow.id.in_(created_device_ids)))
                session.commit()


def test_unknown_family_returns_bad_request():
    app.dependency_overrides[get_device_family_service] = lambda: DeviceFamilyService(
        InMemoryDeviceRepository()  # type: ignore[arg-type]
    )
    try:
        with TestClient(app) as client:
            response = client.post("/api/devices/provision?family=cloud")
        assert response.status_code == 400
        assert "Unsupported device family" in response.json()["detail"]
    finally:
        app.dependency_overrides.pop(get_device_family_service, None)
