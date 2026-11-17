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
def test_overview_is_scoped_to_one_of_two_locations():
    location_a_id: UUID | None = None
    location_b_id: UUID | None = None
    device_ids: list[UUID] = []
    queries: list[str] = []

    def count_query(conn, cursor, statement, parameters, context, executemany):
        if statement.lstrip().upper().startswith("SELECT"):
            queries.append(statement)

    try:
        with TestClient(app) as client:
            created_a = client.post(
                "/api/locations/config",
                json={
                    "location_name": f"Overview A {uuid4()}",
                    "zones": [
                        {
                            "name": "Bench",
                            "moisture_threshold_low": 0.25,
                            "moisture_threshold_high": 0.45,
                            "schedule": {},
                        }
                    ],
                },
            )
            assert created_a.status_code == 201
            location_a_id = UUID(created_a.json()["location"]["id"])
            location_a_name = created_a.json()["location"]["name"]

            created_b = client.post(
                "/api/locations/config",
                json={
                    "location_name": f"Overview B {uuid4()}",
                    "zones": [
                        {
                            "name": "Bench",
                            "moisture_threshold_low": 0.25,
                            "moisture_threshold_high": 0.45,
                            "schedule": {},
                        }
                    ],
                },
            )
            assert created_b.status_code == 201
            location_b_id = UUID(created_b.json()["location"]["id"])
            assert client.get(f"/api/locations/{uuid4()}/overview").status_code == 404

            sensor_a_ids: list[UUID] = []
            for index in range(3):
                sensor = client.post(
                    "/api/sensors",
                    json={"type": "moisture", "display_name": f"Overview A sensor {index}"},
                )
                assert sensor.status_code == 201
                sensor_id = UUID(sensor.json()["id"])
                sensor_a_ids.append(sensor_id)
                device_ids.append(sensor_id)

                assigned = client.patch(
                    f"/api/devices/{sensor_id}/location",
                    json={"location_id": str(location_a_id)},
                )
                assert assigned.status_code == 200
                assert assigned.json()["location_id"] == str(location_a_id)

            assert client.patch(
                f"/api/devices/{uuid4()}/location",
                json={"location_id": str(location_a_id)},
            ).status_code == 404
            assert client.patch(
                f"/api/devices/{sensor_a_ids[0]}/location",
                json={"location_id": str(uuid4())},
            ).status_code == 404

            with SessionLocal() as session:
                actuator_a = DeviceRow(
                    device_type="water_pump",
                    role="actuator",
                    device_family="simulation",
                    display_name="Overview A pump",
                    location_id=location_a_id,
                )
                sensor_b = DeviceRow(
                    device_type="moisture_sensor",
                    role="sensor",
                    device_family="simulation",
                    display_name="Overview B sensor",
                    location_id=location_b_id,
                )
                session.add_all([actuator_a, sensor_b])
                session.flush()
                device_ids.extend([actuator_a.id, sensor_b.id])

                for index, sensor_id in enumerate(sensor_a_ids):
                    session.add(
                        ReadingRow(
                            device_id=sensor_id,
                            value=40.0 + index,
                            unit="percent",
                            source="simulation",
                            recorded_at=datetime(9990, 1, 1, tzinfo=UTC),
                        )
                    )
                    session.add(
                        ReadingRow(
                            device_id=sensor_id,
                            value=41.0 + index,
                            unit="percent",
                            source="simulation",
                            recorded_at=datetime(9990, 1, 1, tzinfo=UTC) + timedelta(minutes=1),
                        )
                    )
                # This is newer and much drier than any location-A reading.
                # If location filtering leaks, conservative would irrigate A.
                session.add(
                    ReadingRow(
                        device_id=sensor_b.id,
                        value=5.0,
                        unit="percent",
                        source="simulation",
                        recorded_at=datetime(9990, 1, 1, 2, tzinfo=UTC),
                    )
                )
                session.commit()

            assert client.put(
                f"/api/locations/{location_a_id}/automation",
                json={"strategy_key": "conservative"},
            ).status_code == 200

            event.listen(engine, "before_cursor_execute", count_query)
            try:
                first = client.get(f"/api/locations/{location_a_id}/overview")
            finally:
                event.remove(engine, "before_cursor_execute", count_query)
            assert first.status_code == 200
            overview = first.json()
            assert overview["location"] == {"id": str(location_a_id), "name": location_a_name}
            assert overview["device_counts"] == {"sensor": 3, "actuator": 1}
            readings = {reading["device_id"]: reading for reading in overview["latest_readings"]}
            assert set(readings) == {str(sensor_id) for sensor_id in sensor_a_ids}
            for index, sensor_id in enumerate(sensor_a_ids):
                assert readings[str(sensor_id)]["value"] == 41.0 + index
                assert readings[str(sensor_id)]["unit"] == "percent"
                assert "recorded_at" in readings[str(sensor_id)]
            assert overview["strategy_key"] == "conservative"
            # Location B has a newer, drier reading. A must still use A's reading.
            assert overview["last_recommendation"]["action"] == "wait"
            assert len(queries) <= 8  # bounded independently of the number of sensors

            b_overview = client.get(f"/api/locations/{location_b_id}/overview").json()
            assert b_overview["device_counts"] == {"sensor": 1, "actuator": 0}
            assert {reading["device_id"] for reading in b_overview["latest_readings"]} == {
                str(sensor_b.id)
            }

            assert client.put(
                f"/api/locations/{location_a_id}/automation",
                json={"strategy_key": "aggressive"},
            ).status_code == 200
            changed = client.get(f"/api/locations/{location_a_id}/overview").json()
            assert changed["strategy_key"] == "aggressive"
            assert changed["last_recommendation"]["action"] == "irrigate"

            with SessionLocal() as session:
                session.add(
                    ReadingRow(
                        device_id=sensor_a_ids[0],
                        value=90.0,
                        unit="percent",
                        source="simulation",
                        recorded_at=datetime(9990, 1, 1, 3, tzinfo=UTC),
                    )
                )
                session.commit()
            refreshed = client.get(f"/api/locations/{location_a_id}/overview").json()
            assert next(
                reading for reading in refreshed["latest_readings"]
                if reading["device_id"] == str(sensor_a_ids[0])
            )["value"] == 90.0

            unassigned = client.patch(
                f"/api/devices/{sensor_a_ids[0]}/location",
                json={"location_id": None},
            )
            assert unassigned.status_code == 200
            assert unassigned.json()["location_id"] is None
    finally:
        with SessionLocal() as session:
            if device_ids:
                session.execute(delete(ReadingRow).where(ReadingRow.device_id.in_(device_ids)))
                session.execute(delete(DeviceRow).where(DeviceRow.id.in_(device_ids)))
            if location_a_id is not None:
                session.execute(delete(LocationRow).where(LocationRow.id == location_a_id))
            if location_b_id is not None:
                session.execute(delete(LocationRow).where(LocationRow.id == location_b_id))
            session.commit()
