from datetime import datetime
from uuid import UUID

from pydantic import BaseModel


class StrategyUpdateRequestDto(BaseModel):
    strategy_key: str


class AutomationRuleDto(BaseModel):
    """The strategy currently applied to a location.

    ``is_default`` is true when no rule has been saved yet, in which case
    ``strategy_key`` is the default and ``updated_at`` is null.
    """

    location_id: UUID
    strategy_key: str
    is_default: bool
    updated_at: datetime | None
    available_strategies: list[str]


class RecommendationDto(BaseModel):
    location_id: UUID
    strategy_key: str
    action: str
    reason: str
