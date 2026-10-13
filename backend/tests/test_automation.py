"""Phase 6 — Strategy tests.

Strategy and service tests use in-memory fakes and no database. The
integration test runs against PostgreSQL when RUN_DB_INTEGRATION=1.
"""

import inspect
import os
from datetime import UTC, datetime, timedelta
from uuid import UUID, uuid4

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import delete

import domain.automation.strategy as strategy_module
from application.automation.service import AutomationService
from domain.automation.context import LocationAutomationContext
from domain.automation.errors import UnknownStrategyError
from domain.automation.rule import AutomationRule
from domain.automation.strategy import get_strategy
from domain.locations.entity import Location, LocationConfig, Zone
from domain.locations.errors import LocationNotFoundError
from domain.sensors.reading import Reading
from infrastructure.db import SessionLocal
from infrastructure.persistence.models import DeviceRow, LocationRow, ReadingRow
from interfaces.api.automation import get_automation_service
from main import app


def _context(moisture: float, low: float = 0.25, high: float = 0.45) -> LocationAutomationContext:
    return LocationAutomationContext(
        location_id=uuid4(),
        zone_name="Bench 1",
        moisture=moisture,
        moisture_low=low,
        moisture_high=high,
    )


# ---------------------------------------------------------------------------
# Strategy decisions (pure domain, no database)
# ---------------------------------------------------------------------------


def test_conservative_waits_when_within_band():
    recommendation = get_strategy("conservative").decide(_context(0.40))

    assert recommendation.action == "wait"
    assert "within 0.25–0.45" in recommendation.reason


def test_conservative_irrigates_below_low_threshold():
    recommendation = get_strategy("conservative").decide(_context(0.20))

    assert recommendation.action == "irrigate"
    assert "below the low threshold 0.25" in recommendation.reason


def test_aggressive_differs_on_same_context():
    context = _context(0.40)

    conservative = get_strategy("conservative").decide(context)
    aggressive = get_strategy("aggressive").decide(context)

    assert conservative.action == "wait"
    assert aggressive.action == "irrigate"
    assert "below the high threshold 0.45" in aggressive.reason


def test_both_strategies_wait_at_or_above_high_threshold():
    context = _context(0.50)

    assert get_strategy("conservative").decide(context).action == "wait"
    assert get_strategy("aggressive").decide(context).action == "wait"


def test_get_strategy_rejects_unknown_key():
    with pytest.raises(UnknownStrategyError):
        get_strategy("green")


def test_strategy_module_does_not_import_sqlalchemy():
    assert "sqlalchemy" not in inspect.getsource(strategy_module).lower()


# ---------------------------------------------------------------------------
# Application service with in-memory fakes
# ---------------------------------------------------------------------------


class FakeLocationRepository:
    def __init__(self, configs: list[LocationConfig]) -> None:
        self.configs = {config.location.id: config for config in configs}

    def get_config(self, location_id: UUID) -> LocationConfig | None:
        return self.configs.get(location_id)


class FakeAutomationRepository:
    def __init__(self, readings: list[Reading]) -> None:
        self.readings = readings
        self.rules: dict[UUID, AutomationRule] = {}
        self.upserts: list[str] = []

    def get_rule(self, location_id: UUID) -> AutomationRule | None:
        return self.rules.get(location_id)

    def upsert_rule(self, location_id: UUID, strategy_key: str) -> AutomationRule:
        self.upserts.append(strategy_key)
        rule = AutomationRule(location_id=location_id, strategy_key=strategy_key, updated_at=datetime.now(UTC))
        self.rules[location_id] = rule
        return rule

    def latest_moisture_reading(self) -> Reading | None:
        return max(self.readings, key=lambda reading: reading.recorded_at, default=None)


def _config(location_id: UUID, zones: tuple[tuple[str, float, float], ...] = (("Bench 1", 0.25, 0.45),)) -> LocationConfig:
    return LocationConfig(
        location=Location(
            id=location_id,
            name="Lab Site A",
            zones=tuple(
                Zone(
                    name=name,
                    moisture_threshold_low=low,
                    moisture_threshold_high=high,
                    id=uuid4(),
                    location_id=location_id,
                )
                for name, low, high in zones
            ),
        )
    )


def _reading(percent: float, minutes_ago: int = 0) -> Reading:
    return Reading(
        device_id=uuid4(),
        value=percent,
        unit="percent",
        source="simulation",
        recorded_at=datetime.now(UTC) - timedelta(minutes=minutes_ago),
    )


def _service(
    configs: list[LocationConfig],
    readings: list[Reading],
) -> tuple[AutomationService, FakeAutomationRepository]:
    rules = FakeAutomationRepository(readings)
    return AutomationService(rules, FakeLocationRepository(configs)), rules  # type: ignore[arg-type]


def test_evaluate_uses_persisted_strategy_for_same_moisture():
    location_id = uuid4()
    service, _ = _service([_config(location_id)], [_reading(40.0)])

    service.set_strategy(location_id, "aggressive")
    aggressive = service.evaluate(location_id)
    assert aggressive.strategy_key == "aggressive"
    assert aggressive.action == "irrigate"

    service.set_strategy(location_id, "conservative")
    conservative = service.evaluate(location_id)
    assert conservative.strategy_key == "conservative"
    assert conservative.action == "wait"


def test_evaluate_defaults_to_conservative_when_no_rule_is_saved():
    location_id = uuid4()
    service, _ = _service([_config(location_id)], [_reading(40.0)])

    recommendation = service.evaluate(location_id)

    assert recommendation.strategy_key == "conservative"
    assert recommendation.action == "wait"
    assert service.get_rule(location_id).is_default is True


def test_percent_reading_is_compared_on_the_fraction_scale():
    location_id = uuid4()
    service, _ = _service([_config(location_id)], [_reading(18.0)])

    recommendation = service.evaluate(location_id)

    assert recommendation.action == "irrigate"
    assert "0.18" in recommendation.reason


def test_zone_thresholds_drive_the_decision_and_any_zone_can_irrigate():
    location_id = uuid4()
    zones = (("Dry bench", 0.25, 0.45), ("Wet bench", 0.10, 0.30))
    service, _ = _service([_config(location_id, zones)], [_reading(18.0)])

    recommendation = service.evaluate(location_id)

    # 0.18 is below the Dry bench low threshold (0.25) but above the Wet bench's (0.10).
    assert recommendation.action == "irrigate"
    assert "Dry bench" in recommendation.reason


def test_evaluate_waits_when_no_moisture_reading_exists():
    location_id = uuid4()
    service, _ = _service([_config(location_id)], [])

    recommendation = service.evaluate(location_id)

    assert recommendation.action == "wait"
    assert "No moisture reading" in recommendation.reason


def test_unknown_strategy_is_rejected_before_persisting():
    location_id = uuid4()
    service, rules = _service([_config(location_id)], [])

    with pytest.raises(UnknownStrategyError):
        service.set_strategy(location_id, "green")

    assert rules.upserts == []


def test_missing_location_raises_not_found():
    service, _ = _service([], [_reading(40.0)])
    missing = uuid4()

    with pytest.raises(LocationNotFoundError):
        service.get_rule(missing)
    with pytest.raises(LocationNotFoundError):
        service.set_strategy(missing, "aggressive")
    with pytest.raises(LocationNotFoundError):
        service.evaluate(missing)


# ---------------------------------------------------------------------------
# HTTP API (service overridden with fakes, no database)
# ---------------------------------------------------------------------------


def _override_service(service: AutomationService) -> None:
    app.dependency_overrides[get_automation_service] = lambda: service


def test_put_then_evaluate_uses_saved_strategy_over_http():
    location_id = uuid4()
    service, _ = _service([_config(location_id)], [_reading(40.0)])
    _override_service(service)
    try:
        with TestClient(app) as client:
            saved = client.put(f"/api/locations/{location_id}/automation", json={"strategy_key": "aggressive"})
            assert saved.status_code == 200
            assert saved.json()["strategy_key"] == "aggressive"
            assert saved.json()["is_default"] is False

            fetched = client.get(f"/api/locations/{location_id}/automation")
            assert fetched.json()["strategy_key"] == "aggressive"
            assert fetched.json()["available_strategies"] == ["conservative", "aggressive"]

            evaluated = client.post(f"/api/locations/{location_id}/automation/evaluate")
            assert evaluated.status_code == 200
            assert set(evaluated.json()) == {"location_id", "strategy_key", "action", "reason"}
            assert evaluated.json()["strategy_key"] == "aggressive"
            assert evaluated.json()["action"] == "irrigate"
    finally:
        app.dependency_overrides.pop(get_automation_service, None)


def test_put_unknown_strategy_returns_400():
    location_id = uuid4()
    service, _ = _service([_config(location_id)], [])
    _override_service(service)
    try:
        with TestClient(app) as client:
            response = client.put(f"/api/locations/{location_id}/automation", json={"strategy_key": "green"})
        assert response.status_code == 400
        assert "green" in response.json()["detail"]
    finally:
        app.dependency_overrides.pop(get_automation_service, None)


def test_missing_location_returns_404_on_all_automation_routes():
    service, _ = _service([], [])
    _override_service(service)
    missing = uuid4()
    try:
        with TestClient(app) as client:
            assert client.get(f"/api/locations/{missing}/automation").status_code == 404
            assert client.put(f"/api/locations/{missing}/automation", json={"strategy_key": "aggressive"}).status_code == 404
            assert client.post(f"/api/locations/{missing}/automation/evaluate").status_code == 404
    finally:
        app.dependency_overrides.pop(get_automation_service, None)


def test_openapi_documents_automation_routes_and_schemas():
    with TestClient(app) as client:
        schema = client.get("/openapi.json").json()

    put_path = schema["paths"]["/api/locations/{location_id}/automation"]["put"]
    evaluate_path = schema["paths"]["/api/locations/{location_id}/automation/evaluate"]["post"]
    assert put_path["tags"] == ["automation"]
    assert evaluate_path["tags"] == ["automation"]

    recommendation_properties = schema["components"]["schemas"]["RecommendationDto"]["properties"]
    assert set(recommendation_properties) == {"location_id", "strategy_key", "action", "reason"}
    assert "greenhouse_id" not in str(schema)


# ---------------------------------------------------------------------------
# Real database integration
# ---------------------------------------------------------------------------


@pytest.mark.skipif(
    os.getenv("RUN_DB_INTEGRATION") != "1",
    reason="set RUN_DB_INTEGRATION=1 to run against the configured PostgreSQL database",
)
def test_strategy_persists_and_evaluates_against_stored_readings():
    from infrastructure.persistence.models import AutomationRuleRow

    location_id: UUID | None = None
    device_id: UUID | None = None
    try:
        with TestClient(app) as client:
            created = client.post(
                "/api/locations/config",
                json={
                    "location_name": f"Automation check {uuid4()}",
                    "zones": [
                        {
                            "name": "Bench 1",
                            "moisture_threshold_low": 0.2,
                            "moisture_threshold_high": 0.45,
                            "schedule": {},
                        }
                    ],
                },
            )
            assert created.status_code == 201
            location_id = UUID(created.json()["location"]["id"])

            sensor = client.post("/api/sensors", json={"type": "moisture"})
            assert sensor.status_code == 201
            device_id = UUID(sensor.json()["id"])

            # Future-dated so it is the latest moisture reading in the database.
            with SessionLocal() as session:
                session.add(
                    ReadingRow(
                        device_id=device_id,
                        value=40.0,
                        unit="percent",
                        source="simulation",
                        recorded_at=datetime.now(UTC) + timedelta(days=1),
                    )
                )
                session.commit()

            assert client.put(f"/api/locations/{location_id}/automation", json={"strategy_key": "aggressive"}).status_code == 200
            aggressive = client.post(f"/api/locations/{location_id}/automation/evaluate").json()
            assert aggressive["strategy_key"] == "aggressive"
            assert aggressive["action"] == "irrigate"

            assert client.put(f"/api/locations/{location_id}/automation", json={"strategy_key": "conservative"}).status_code == 200
            conservative = client.post(f"/api/locations/{location_id}/automation/evaluate").json()
            assert conservative["strategy_key"] == "conservative"
            assert conservative["action"] == "wait"

            with SessionLocal() as session:
                rule_count = len(
                    session.query(AutomationRuleRow).filter(AutomationRuleRow.location_id == location_id).all()
                )
                assert rule_count == 1  # one rule per location, updated in place
    finally:
        with SessionLocal() as session:
            if device_id is not None:
                session.execute(delete(ReadingRow).where(ReadingRow.device_id == device_id))
                session.execute(delete(DeviceRow).where(DeviceRow.id == device_id))
            if location_id is not None:
                session.execute(delete(LocationRow).where(LocationRow.id == location_id))
            session.commit()
