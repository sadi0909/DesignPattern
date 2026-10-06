"""Phase 5 — Adapter tests.

Translation tests run without HTTP or a database. The insert test runs against
the real PostgreSQL database when RUN_DB_INTEGRATION=1.
"""

import os
from datetime import UTC, datetime
from uuid import UUID, uuid4

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import delete, select

from application.readings.service import ReadingService
from domain.actuators.ports import ActuatorPort
from domain.devices.entity import Device
from domain.devices.errors import DeviceNotFoundError
from domain.sensors.errors import SensorReadError
from domain.sensors.reading import Reading
from infrastructure.adapters.actuators.simulation import SimulationActuatorAdapter
from infrastructure.adapters.sensors.selector import select_sensor_adapter
from infrastructure.adapters.sensors.simulation import SimulationSensorAdapter
from infrastructure.adapters.sensors.vendor_stub import VendorStubSensorAdapter
from infrastructure.db import SessionLocal
from infrastructure.persistence.models import DeviceRow, ReadingRow
from interfaces.api.sensors import get_reading_service
from main import app


def _device(
    *,
    device_type: str = "moisture_sensor",
    device_family: str = "simulation",
    default_config: dict | None = None,
) -> Device:
    return Device(
        id=uuid4(),
        device_type=device_type,
        role="sensor",
        device_family=device_family,
        display_name="Test sensor",
        default_config=default_config or {},
    )


# ---------------------------------------------------------------------------
# Adapter translation (no HTTP, no database)
# ---------------------------------------------------------------------------


def test_vendor_adapter_normalizes_raw_payload():
    """The vendor raw shape (nested, odd names, scaled ints, epoch ms)
    translates into the normalized Reading fields."""
    device = _device(device_family="edge", default_config={"protocol": "gpio-stub"})
    raw = {
        "probe_sn": "VND-8842",
        "sample": {"reading_tenths": 245, "uom_code": "PCT"},
        "captured_epoch_ms": 1767225600000,
    }

    reading = VendorStubSensorAdapter.translate(device, raw)

    assert reading.device_id == device.id
    assert reading.value == pytest.approx(24.5)  # deci-percent -> percent
    assert reading.unit == "percent"
    assert reading.source == "vendor"
    assert reading.recorded_at == datetime(2026, 1, 1, tzinfo=UTC)


def test_vendor_adapter_converts_kilolux_to_lux():
    device = _device(device_type="light_sensor", device_family="edge")
    raw = {
        "probe_sn": "VND-8843",
        "sample": {"reading_tenths": 120, "uom_code": "KLX"},
        "captured_epoch_ms": 1767225600000,
    }

    reading = VendorStubSensorAdapter.translate(device, raw)

    assert reading.value == pytest.approx(12000.0)  # tenths of kilolux -> lux
    assert reading.unit == "lux"
    assert reading.source == "vendor"


def test_vendor_adapter_rejects_unknown_unit_code():
    device = _device()
    raw = {
        "probe_sn": "VND-8844",
        "sample": {"reading_tenths": 100, "uom_code": "FURLONGS"},
        "captured_epoch_ms": 1767225600000,
    }

    with pytest.raises(SensorReadError):
        VendorStubSensorAdapter.translate(device, raw)


def test_simulation_adapter_reads_plausible_value():
    reading = SimulationSensorAdapter().read(_device())

    assert reading.source == "simulation"
    assert reading.unit == "percent"
    assert 20.0 <= reading.value <= 80.0
    assert reading.recorded_at.tzinfo is not None


def test_selector_picks_adapter_by_protocol_and_family():
    assert isinstance(
        select_sensor_adapter(_device(default_config={"protocol": "sim"})),
        SimulationSensorAdapter,
    )
    assert isinstance(
        select_sensor_adapter(_device(default_config={"protocol": "gpio-stub"})),
        VendorStubSensorAdapter,
    )
    # Falls back to device_family when no explicit protocol is configured.
    assert isinstance(select_sensor_adapter(_device(device_family="simulation")), SimulationSensorAdapter)
    assert isinstance(select_sensor_adapter(_device(device_family="edge")), VendorStubSensorAdapter)

    with pytest.raises(SensorReadError):
        select_sensor_adapter(_device(default_config={"protocol": "carrier-pigeon"}))


def test_reading_requires_timezone_aware_timestamp():
    with pytest.raises(ValueError):
        Reading(
            device_id=uuid4(),
            value=1.0,
            unit="percent",
            source="simulation",
            recorded_at=datetime.fromisoformat("2026-01-01T00:00:00"),  # naive on purpose
        )


# ---------------------------------------------------------------------------
# Actuator port stub (Phase 9 wraps this adapter)
# ---------------------------------------------------------------------------


def test_simulation_actuator_apply_records_intent_in_memory():
    adapter = SimulationActuatorAdapter()
    assert isinstance(adapter, ActuatorPort)

    device_id = uuid4()
    adapter.apply(device_id, "open_valve", {"liters": 2})

    assert len(adapter.applied) == 1
    assert adapter.applied[0].device_id == device_id
    assert adapter.applied[0].command == "open_valve"
    assert adapter.applied[0].payload == {"liters": 2}


# ---------------------------------------------------------------------------
# Application service + API (in-memory fakes, no database)
# ---------------------------------------------------------------------------


class InMemoryDeviceRepository:
    def __init__(self, devices: list[Device]) -> None:
        self.devices: dict[UUID, Device] = {device.id: device for device in devices if device.id is not None}

    def get_device(self, device_id: UUID) -> Device | None:
        return self.devices.get(device_id)


class InMemoryReadingRepository:
    def __init__(self) -> None:
        self.rows: list[Reading] = []

    def insert(self, reading: Reading) -> Reading:
        self.rows.append(reading)
        return reading

    def list_for_device(self, device_id: UUID, limit: int = 20) -> list[Reading]:
        matching = [row for row in self.rows if row.device_id == device_id]
        matching.sort(key=lambda row: row.recorded_at, reverse=True)
        return matching[:limit]


def _override(devices: list[Device], selector=None) -> InMemoryReadingRepository:
    readings = InMemoryReadingRepository()
    service = ReadingService(
        InMemoryDeviceRepository(devices),
        readings,
        adapter_selector=selector or select_sensor_adapter,
    )
    app.dependency_overrides[get_reading_service] = lambda: service
    return readings


def test_take_reading_unknown_device_raises_not_found():
    service = ReadingService(InMemoryDeviceRepository([]), InMemoryReadingRepository())
    with pytest.raises(DeviceNotFoundError):
        service.take_reading(uuid4())


def test_read_api_returns_normalized_dto_and_history():
    device = _device()
    readings = _override([device])
    try:
        with TestClient(app) as client:
            read_response = client.post(f"/api/sensors/{device.id}/read")
            assert read_response.status_code == 201
            body = read_response.json()
            assert set(body) == {"device_id", "value", "unit", "source", "recorded_at"}
            assert body["device_id"] == str(device.id)
            assert body["source"] == "simulation"

            # A second read appends history instead of overwriting.
            second = client.post(f"/api/sensors/{device.id}/read")
            assert second.status_code == 201
            assert len(readings.rows) == 2

            history = client.get(f"/api/sensors/{device.id}/readings?limit=1")
            assert history.status_code == 200
            assert len(history.json()) == 1
    finally:
        app.dependency_overrides.pop(get_reading_service, None)


def test_read_api_maps_missing_device_to_404():
    _override([])
    try:
        with TestClient(app) as client:
            assert client.post(f"/api/sensors/{uuid4()}/read").status_code == 404
            assert client.get(f"/api/sensors/{uuid4()}/readings").status_code == 404
    finally:
        app.dependency_overrides.pop(get_reading_service, None)


def test_read_api_maps_adapter_failure_to_400():
    def failing_selector(device: Device):
        raise SensorReadError("vendor payload is malformed")

    device = _device()
    _override([device], selector=failing_selector)
    try:
        with TestClient(app) as client:
            response = client.post(f"/api/sensors/{device.id}/read")
            assert response.status_code == 400
            assert "malformed" in response.json()["detail"]
    finally:
        app.dependency_overrides.pop(get_reading_service, None)


def test_openapi_documents_reading_routes_and_schema():
    with TestClient(app) as client:
        schema = client.get("/openapi.json").json()

    read_path = schema["paths"]["/api/sensors/{sensor_id}/read"]["post"]
    history_path = schema["paths"]["/api/sensors/{sensor_id}/readings"]["get"]
    assert read_path["tags"] == ["sensors"]
    assert history_path["tags"] == ["sensors"]

    reading_properties = schema["components"]["schemas"]["ReadingDto"]["properties"]
    assert set(reading_properties) == {"device_id", "value", "unit", "source", "recorded_at"}


# ---------------------------------------------------------------------------
# Real database integration
# ---------------------------------------------------------------------------


@pytest.mark.skipif(
    os.getenv("RUN_DB_INTEGRATION") != "1",
    reason="set RUN_DB_INTEGRATION=1 to run against the configured PostgreSQL database",
)
def test_read_inserts_sensor_reading():
    created_device_id: UUID | None = None
    try:
        with TestClient(app) as client:
            create_response = client.post("/api/sensors", json={"type": "moisture"})
            assert create_response.status_code == 201
            created_device_id = UUID(create_response.json()["id"])

            first = client.post(f"/api/sensors/{created_device_id}/read")
            assert first.status_code == 201
            first_body = first.json()
            assert first_body["device_id"] == str(created_device_id)
            assert first_body["source"] == "simulation"

            second = client.post(f"/api/sensors/{created_device_id}/read")
            assert second.status_code == 201

            with SessionLocal() as session:
                rows = session.scalars(
                    select(ReadingRow).where(ReadingRow.device_id == created_device_id)
                ).all()
                # Two successful reads append two rows (history, not overwrite).
                assert len(rows) == 2
                assert all(row.source == "simulation" for row in rows)

            history = client.get(f"/api/sensors/{created_device_id}/readings?limit=1")
            assert history.status_code == 200
            latest = history.json()
            assert len(latest) == 1
            assert latest[0]["value"] == second.json()["value"]
    finally:
        if created_device_id is not None:
            with SessionLocal() as session:
                session.execute(delete(ReadingRow).where(ReadingRow.device_id == created_device_id))
                session.execute(delete(DeviceRow).where(DeviceRow.id == created_device_id))
                session.commit()
