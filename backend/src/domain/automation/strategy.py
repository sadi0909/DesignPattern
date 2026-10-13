"""Automation strategies: interchangeable moisture policies behind decide(context).

Strategies are pure. They take a LocationAutomationContext and return a
Recommendation. They never touch the database, actuators, or HTTP types.
Choosing a strategy (get_strategy) is kept separate from running it (decide).
"""

from abc import ABC, abstractmethod
from dataclasses import dataclass

from domain.automation.context import LocationAutomationContext
from domain.automation.errors import UnknownStrategyError

ACTION_IRRIGATE = "irrigate"
ACTION_WAIT = "wait"
DEFAULT_STRATEGY_KEY = "conservative"


@dataclass(frozen=True, slots=True)
class Recommendation:
    action: str
    reason: str


class AutomationStrategy(ABC):
    key: str

    @abstractmethod
    def decide(self, context: LocationAutomationContext) -> Recommendation:
        """Recommend irrigate or wait for one zone."""
        raise NotImplementedError


class ConservativeMoistureStrategy(AutomationStrategy):
    """Irrigates only when moisture falls below the zone's low threshold."""

    key = "conservative"

    def decide(self, context: LocationAutomationContext) -> Recommendation:
        if context.moisture < context.moisture_low:
            return Recommendation(
                ACTION_IRRIGATE,
                f"Zone {context.zone_name}: moisture {context.moisture:.2f} is below "
                f"the low threshold {context.moisture_low:.2f}",
            )
        return Recommendation(ACTION_WAIT, _wait_reason(context))


class AggressiveMoistureStrategy(AutomationStrategy):
    """Irrigates as soon as moisture falls below the zone's high threshold.

    Differs from the conservative policy inside the band between the low and
    high thresholds: there, conservative waits and aggressive irrigates.
    """

    key = "aggressive"

    def decide(self, context: LocationAutomationContext) -> Recommendation:
        if context.moisture < context.moisture_high:
            return Recommendation(
                ACTION_IRRIGATE,
                f"Zone {context.zone_name}: moisture {context.moisture:.2f} is below "
                f"the high threshold {context.moisture_high:.2f}",
            )
        return Recommendation(ACTION_WAIT, _wait_reason(context))


def _wait_reason(context: LocationAutomationContext) -> str:
    if context.moisture < context.moisture_high:
        return (
            f"Zone {context.zone_name}: moisture {context.moisture:.2f} is within "
            f"{context.moisture_low:.2f}–{context.moisture_high:.2f}"
        )
    return (
        f"Zone {context.zone_name}: moisture {context.moisture:.2f} is above "
        f"the high threshold {context.moisture_high:.2f}"
    )


_STRATEGIES: dict[str, AutomationStrategy] = {
    strategy.key: strategy
    for strategy in (ConservativeMoistureStrategy(), AggressiveMoistureStrategy())
}

STRATEGY_KEYS: tuple[str, ...] = tuple(_STRATEGIES)


def get_strategy(key: str) -> AutomationStrategy:
    """Look up a strategy by key. Unknown keys fail before any decide() call."""
    strategy = _STRATEGIES.get(key)
    if strategy is None:
        raise UnknownStrategyError(f"Unknown automation strategy: {key!r}")
    return strategy
