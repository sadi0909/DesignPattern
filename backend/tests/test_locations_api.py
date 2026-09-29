import os
from dataclasses import replace
from uuid import UUID, uuid4

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import delete, select

from application.locations.config_service import LocationConfigService
from domain.locations.entity import Location, LocationConfig, Zone
from infrastructure.db import SessionLocal
from infrastructure.persistence.models import LocationRow
from interfaces.api.locations import get_location_config_service
from main import app


class InMemoryLocationRepository:
    def __init__(self) -> None:
        self.configs: dict[UUID, LocationConfig] = {}

    def save_config(self, config: LocationConfig) -> LocationConfig:
        location_id = uuid4()
        persisted = LocationConfig(
            location=replace(
                config.location,
                id=location_id,
                zones=tuple(
                    replace(zone, id=uuid4(), location_id=location_id)
                    for zone in config.location.zones
                ),
            )
        )
        self.configs[location_id] = persisted
        return persisted

    def get_config(self, location_id: UUID) -> LocationConfig | None:
        return self.configs.get(location_id)


def _request_body() -> dict[str, object]:
    return {
        "location_name": "Lab Site A",
        "zones": [
            {
                "name": "Bench 1",
                "moisture_threshold_low": 0.2,
                "moisture_threshold_high": 0.45,
                "schedule": {"watering": "08:00"},
            },
            {
                "name": "Bench 2",
                "moisture_threshold_low": 0.15,
                "moisture_threshold_high": 0.5,
                "schedule": {},
            },
        ],
    }


def test_create_and_get_location_config():
    repository = InMemoryLocationRepository()
    app.dependency_overrides[get_location_config_service] = lambda: LocationConfigService(repository)  # type: ignore[arg-type]
    try:
        with TestClient(app) as client:
            create_response = client.post("/api/locations/config", json=_request_body())
            assert create_response.status_code == 201
            created = create_response.json()
            assert created["location"]["name"] == "Lab Site A"
            assert len(created["zones"]) == 2
            location_id = created["location"]["id"]
            assert all(zone["location_id"] == location_id for zone in created["zones"])
            assert created["zones"][0]["schedule"] == {"watering": "08:00"}

            get_response = client.get(f"/api/locations/{location_id}/config")
            assert get_response.status_code == 200
            assert get_response.json() == created
    finally:
        app.dependency_overrides.pop(get_location_config_service, None)


def test_invalid_domain_config_returns_400_without_saving():
    repository = InMemoryLocationRepository()
    app.dependency_overrides[get_location_config_service] = lambda: LocationConfigService(repository)  # type: ignore[arg-type]
    body = _request_body()
    body["zones"] = [
        {
            "name": "Bench 1",
            "moisture_threshold_low": 0.7,
            "moisture_threshold_high": 0.2,
            "schedule": {},
        }
    ]
    try:
        with TestClient(app) as client:
            response = client.post("/api/locations/config", json=body)
        assert response.status_code == 400
        assert "Low moisture threshold" in response.json()["detail"]
        assert repository.configs == {}
    finally:
        app.dependency_overrides.pop(get_location_config_service, None)


def test_missing_location_returns_404():
    repository = InMemoryLocationRepository()
    app.dependency_overrides[get_location_config_service] = lambda: LocationConfigService(repository)  # type: ignore[arg-type]
    try:
        with TestClient(app) as client:
            response = client.get(f"/api/locations/{uuid4()}/config")
        assert response.status_code == 404
    finally:
        app.dependency_overrides.pop(get_location_config_service, None)


def test_openapi_documents_location_dto_and_routes():
    with TestClient(app) as client:
        schema = client.get("/openapi.json").json()

    assert "locations" in schema["paths"]["/api/locations/config"]["post"]["tags"]
    assert "locations" in schema["paths"]["/api/locations/{location_id}/config"]["get"]["tags"]
    assert "location_id" in schema["components"]["schemas"]["ZoneResponseDto"]["properties"]


def test_openapi_location_contract_uses_location_id_naming():
    with TestClient(app) as client:
        schema = client.get("/openapi.json").json()

    assert "greenhouse_id" not in str(schema)
    zone_properties = schema["components"]["schemas"]["ZoneResponseDto"]["properties"]
    assert "location_id" in zone_properties
    assert "greenhouse_id" not in zone_properties


@pytest.mark.skipif(
    os.getenv("RUN_DB_INTEGRATION") != "1",
    reason="set RUN_DB_INTEGRATION=1 to run against the configured PostgreSQL database",
)
def test_real_database_persists_and_reads_location_config():
    created_location_id: UUID | None = None
    try:
        with TestClient(app) as client:
            create_response = client.post("/api/locations/config", json=_request_body())
            assert create_response.status_code == 201
            created = create_response.json()
            created_location_id = UUID(created["location"]["id"])
            assert len(created["zones"]) == 2
            assert all(zone["location_id"] == str(created_location_id) for zone in created["zones"])

            get_response = client.get(f"/api/locations/{created_location_id}/config")
            assert get_response.status_code == 200
            assert get_response.json() == created
    finally:
        if created_location_id is not None:
            with SessionLocal() as session:
                session.execute(delete(LocationRow).where(LocationRow.id == created_location_id))
                session.commit()


@pytest.mark.skipif(
    os.getenv("RUN_DB_INTEGRATION") != "1",
    reason="set RUN_DB_INTEGRATION=1 to run against the configured PostgreSQL database",
)
def test_database_rolls_back_location_if_zone_insert_fails():
    from sqlalchemy.exc import IntegrityError

    from infrastructure.persistence.location_repository import LocationRepository

    location_name = f"Rollback check {uuid4()}"
    invalid_config = LocationConfig(
        location=Location(
            name=location_name,
            zones=(
                Zone(name="Duplicate", moisture_threshold_low=0.2, moisture_threshold_high=0.5),
                Zone(name="Duplicate", moisture_threshold_low=0.25, moisture_threshold_high=0.6),
            ),
        )
    )

    with SessionLocal() as session:
        with pytest.raises(IntegrityError):
            LocationRepository(session).save_config(invalid_config)
        assert session.scalar(select(LocationRow.id).where(LocationRow.name == location_name)) is None
