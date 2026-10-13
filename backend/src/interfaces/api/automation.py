from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from application.automation.dto import (
    AutomationRuleDto,
    RecommendationDto,
    StrategyUpdateRequestDto,
)
from application.automation.service import AutomationService
from domain.automation.errors import UnknownStrategyError
from domain.locations.errors import LocationNotFoundError
from infrastructure.persistence.automation_repository import AutomationRepository
from infrastructure.persistence.location_repository import LocationRepository
from infrastructure.persistence.session import get_db

router = APIRouter(prefix="/api/locations", tags=["automation"])


def get_automation_service(db: Session = Depends(get_db)) -> AutomationService:  # noqa: B008
    return AutomationService(AutomationRepository(db), LocationRepository(db))


@router.get(
    "/{location_id}/automation",
    response_model=AutomationRuleDto,
    responses={404: {"description": "Location not found"}},
)
def get_automation_rule(
    location_id: UUID,
    service: AutomationService = Depends(get_automation_service),  # noqa: B008
) -> AutomationRuleDto:
    """Return the strategy applied to a location (the default if none is saved)."""
    try:
        return service.get_rule(location_id)
    except LocationNotFoundError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc


@router.put(
    "/{location_id}/automation",
    response_model=AutomationRuleDto,
    responses={
        400: {"description": "Unknown strategy key"},
        404: {"description": "Location not found"},
    },
)
def save_automation_strategy(
    location_id: UUID,
    request: StrategyUpdateRequestDto,
    service: AutomationService = Depends(get_automation_service),  # noqa: B008
) -> AutomationRuleDto:
    """Persist the strategy key that evaluation will use for this location."""
    try:
        return service.set_strategy(location_id, request.strategy_key)
    except UnknownStrategyError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc
    except LocationNotFoundError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc


@router.post(
    "/{location_id}/automation/evaluate",
    response_model=RecommendationDto,
    responses={404: {"description": "Location not found"}},
)
def evaluate_automation(
    location_id: UUID,
    service: AutomationService = Depends(get_automation_service),  # noqa: B008
) -> RecommendationDto:
    """Evaluate the persisted strategy against the latest moisture and zone thresholds."""
    try:
        return service.evaluate(location_id)
    except LocationNotFoundError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc
