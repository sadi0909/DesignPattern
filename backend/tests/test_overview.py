"""Phase 7 overview tests, including the real PostgreSQL read path."""

import os
from datetime import UTC, datetime, timedelta
from uuid import UUID, uuid4

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import delete, event

from application.overview.dependencies import get_overview_facade
from application.overview.dto import (
    DeviceCountsDto,
    LocationOverviewDto,
    LocationSummaryDto,
    OverviewRecommendationDto,
)
from domain.locations.errors import LocationNotFoundError
from infrastructure.db import SessionLocal, engine
from infrastructure.persistence.models import DeviceRow, LocationRow, ReadingRow
from main import app


def test_handler_uses_facade_and_documents_schema():
    location_id = uuid4()

    class FakeFacade:
        def get_overview(self, requested_id: UUID) -> LocationOverviewDto:
            assert requested_id == location_id
            return LocationOverviewDto(
                location=LocationSummaryDto(id=location_id, name="Test location"),
                device_counts=DeviceCountsDto(sensor=0, actuator=0),
                latest_readings=[],
                strategy_key="conservative",
                last_recommendation=OverviewRecommendationDto(action="wait", reason="No reading"),
            )

    app.dependency_overrides[get_overview_facade] = lambda: FakeFacade()
    try:
        with TestClient(app) as client:
            response = client.get(f"/api/locations/{location_id}/overview")
            assert response.status_code == 200
            assert set(response.json()) == {
                "location", "device_counts", "latest_readings", "strategy_key", "last_recommendation"
            }
            schema = client.get("/openapi.json").json()
            operation = schema["paths"]["/api/locations/{location_id}/overview"]["get"]
            assert operation["responses"]["200"]["content"]["application/json"]["schema"]["$ref"].endswith(
                "/LocationOverviewDto"
            )
            assert "404" in operation["responses"]
            assert client.get("/scalar").status_code == 200
    finally:
        app.dependency_overrides.pop(get_overview_facade, None)


def test_missing_location_is_404_and_other_errors_are_not_hidden():
    class FakeFacade:
        def get_overview(self, location_id: UUID) -> LocationOverviewDto:
            raise LocationNotFoundError(f"Location {location_id} does not exist")

    app.dependency_overrides[get_overview_facade] = lambda: FakeFacade()
    try:
        with TestClient(app) as client:
            assert client.get(f"/api/locations/{uuid4()}/overview").status_code == 404
    finally:
        app.dependency_overrides.pop(get_overview_facade, None)

    class BrokenFacade:
        def get_overview(self, location_id: UUID) -> LocationOverviewDto:
            raise RuntimeError("database unavailable")

    app.dependency_overrides[get_overview_facade] = lambda: BrokenFacade()
    try:
        with TestClient(app, raise_server_exceptions=False) as client:
            assert client.get(f"/api/locations/{uuid4()}/overview").status_code == 500
    finally:
        app.dependency_overrides.pop(get_overview_facade, None)


@pytest.mark.skipif(os.getenv("RUN_DB_INTEGRATION") != "1", reason="requires PostgreSQL")
def test_overview_returns_strategy_and_readings():
    location_id: UUID | None = None
    device_ids: list[UUID] = []
    queries: list[str] = []

    def count_query(conn, cursor, statement, parameters, context, executemany):
        if statement.lstrip().upper().startswith("SELECT"):
            queries.append(statement)

    try:
        with TestClient(app) as client:
            created = client.post("/api/locations/config", json={
                "location_name": f"Overview test {uuid4()}",
                "zones": [{"name": "Bench", "moisture_threshold_low": 0.25,
                           "moisture_threshold_high": 0.45, "schedule": {}}],
            })
            assert created.status_code == 201
            location_id = UUID(created.json()["location"]["id"])
            assert client.get(f"/api/locations/{uuid4()}/overview").status_code == 404

            with SessionLocal() as session:
                for index in range(3):
                    device = DeviceRow(device_type="moisture_sensor", role="sensor", device_family="simulation")
                    session.add(device)
                    session.flush()
                    device_ids.append(device.id)
                    for value, minutes in [(10.0, 0), (40.0, 1)]:
                        session.add(ReadingRow(
                            device_id=device.id, value=value + index, unit="percent", source="simulation",
                            recorded_at=datetime(9990, 1, 1, tzinfo=UTC) + timedelta(minutes=minutes),
                        ))
                session.commit()

            assert client.put(f"/api/locations/{location_id}/automation", json={"strategy_key": "conservative"}).status_code == 200
            event.listen(engine, "before_cursor_execute", count_query)
            try:
                first = client.get(f"/api/locations/{location_id}/overview")
            finally:
                event.remove(engine, "before_cursor_execute", count_query)
            assert first.status_code == 200
            overview = first.json()
            assert overview["location"] == {"id": str(location_id), "name": created.json()["location"]["name"]}
            assert overview["device_counts"]["sensor"] >= 3
            readings = {r["device_id"]: r for r in overview["latest_readings"]}
            for index, device_id in enumerate(device_ids):
                assert readings[str(device_id)]["value"] == 40.0 + index
                assert readings[str(device_id)]["unit"] == "percent"
                assert "recorded_at" in readings[str(device_id)]
            assert overview["strategy_key"] == "conservative"
            assert overview["last_recommendation"]["action"] == "wait"
            assert len(queries) <= 8  # bounded independently of the number of sensors

            assert client.put(f"/api/locations/{location_id}/automation", json={"strategy_key": "aggressive"}).status_code == 200
            changed = client.get(f"/api/locations/{location_id}/overview").json()
            assert changed["strategy_key"] == "aggressive"
            assert changed["last_recommendation"]["action"] == "irrigate"

            with SessionLocal() as session:
                session.add(ReadingRow(device_id=device_ids[0], value=90.0, unit="percent", source="simulation",
                                       recorded_at=datetime(9990, 1, 2, tzinfo=UTC)))
                session.commit()
            refreshed = client.get(f"/api/locations/{location_id}/overview").json()
            assert next(r for r in refreshed["latest_readings"] if r["device_id"] == str(device_ids[0]))["value"] == 90.0
            assert refreshed["last_recommendation"]["action"] == "wait"
    finally:
        with SessionLocal() as session:
            if device_ids:
                session.execute(delete(ReadingRow).where(ReadingRow.device_id.in_(device_ids)))
                session.execute(delete(DeviceRow).where(DeviceRow.id.in_(device_ids)))
            if location_id is not None:
                session.execute(delete(LocationRow).where(LocationRow.id == location_id))
            session.commit()
