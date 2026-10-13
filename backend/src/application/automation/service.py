from uuid import UUID

from application.automation.dto import AutomationRuleDto, RecommendationDto
from domain.automation.context import LocationAutomationContext
from domain.automation.rule import AutomationRule
from domain.automation.strategy import (
    ACTION_IRRIGATE,
    ACTION_WAIT,
    DEFAULT_STRATEGY_KEY,
    STRATEGY_KEYS,
    AutomationStrategy,
    Recommendation,
    get_strategy,
)
from domain.locations.entity import LocationConfig
from domain.locations.errors import LocationNotFoundError
from domain.sensors.reading import Reading
from infrastructure.persistence.automation_repository import AutomationRepository
from infrastructure.persistence.location_repository import LocationRepository

MOISTURE_UNIT_PERCENT = "percent"


class AutomationService:
    """Use cases for per-location automation.

    Strategy choice is persisted per location. Evaluation loads the persisted
    key, builds plain contexts from the latest moisture reading and each zone's
    thresholds, and returns the strategy's recommendation.
    """

    def __init__(self, rules: AutomationRepository, locations: LocationRepository) -> None:
        self._rules = rules
        self._locations = locations

    def get_rule(self, location_id: UUID) -> AutomationRuleDto:
        self._require_location(location_id)
        return self._rule_dto(location_id, self._rules.get_rule(location_id))

    def set_strategy(self, location_id: UUID, strategy_key: str) -> AutomationRuleDto:
        get_strategy(strategy_key)  # unknown keys are rejected before any database access
        self._require_location(location_id)
        rule = self._rules.upsert_rule(location_id, strategy_key)
        return self._rule_dto(location_id, rule)

    def evaluate(self, location_id: UUID) -> RecommendationDto:
        config = self._require_location(location_id)
        rule = self._rules.get_rule(location_id)
        strategy_key = rule.strategy_key if rule is not None else DEFAULT_STRATEGY_KEY
        strategy = get_strategy(strategy_key)
        recommendation = self._recommend(location_id, config, strategy)
        return RecommendationDto(
            location_id=location_id,
            strategy_key=strategy_key,
            action=recommendation.action,
            reason=recommendation.reason,
        )

    def _recommend(
        self,
        location_id: UUID,
        config: LocationConfig,
        strategy: AutomationStrategy,
    ) -> Recommendation:
        zones = config.location.zones
        if not zones:
            return Recommendation(ACTION_WAIT, "No zones are configured for this location")

        reading = self._rules.latest_moisture_reading()
        if reading is None:
            return Recommendation(ACTION_WAIT, "No moisture reading has been recorded yet")
        if reading.unit != MOISTURE_UNIT_PERCENT:
            return Recommendation(ACTION_WAIT, f"Latest moisture reading has unsupported unit {reading.unit!r}")

        moisture = _to_fraction(reading)
        decisions = [
            strategy.decide(
                LocationAutomationContext(
                    location_id=location_id,
                    zone_name=zone.name,
                    moisture=moisture,
                    moisture_low=zone.moisture_threshold_low,
                    moisture_high=zone.moisture_threshold_high,
                )
            )
            for zone in zones
        ]
        # The location irrigates if any zone asks for water; otherwise it waits.
        for decision in decisions:
            if decision.action == ACTION_IRRIGATE:
                return decision
        return decisions[0]

    def _require_location(self, location_id: UUID) -> LocationConfig:
        config = self._locations.get_config(location_id)
        if config is None:
            raise LocationNotFoundError(f"Location {location_id} does not exist")
        return config

    @staticmethod
    def _rule_dto(location_id: UUID, rule: AutomationRule | None) -> AutomationRuleDto:
        return AutomationRuleDto(
            location_id=location_id,
            strategy_key=rule.strategy_key if rule is not None else DEFAULT_STRATEGY_KEY,
            is_default=rule is None,
            updated_at=rule.updated_at if rule is not None else None,
            available_strategies=list(STRATEGY_KEYS),
        )


def _to_fraction(reading: Reading) -> float:
    """Convert a percent reading (0-100) to the 0-1 scale used by zone thresholds."""
    return reading.value / 100.0
