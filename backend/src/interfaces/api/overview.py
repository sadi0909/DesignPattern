from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status

from application.overview.dependencies import get_overview_facade
from application.overview.dto import LocationOverviewDto
from application.overview.facade import LocationOverviewFacade
from domain.locations.errors import LocationNotFoundError

router = APIRouter(prefix="/api/locations", tags=["overview"])


@router.get(
    "/{location_id}/overview",
    response_model=LocationOverviewDto,
    responses={404: {"description": "Location not found"}},
)
def get_overview(
    location_id: UUID,
    facade: LocationOverviewFacade = Depends(get_overview_facade),  # noqa: B008
) -> LocationOverviewDto:
    """Get a location and current recommendation with global device and sensor summaries."""
    try:
        return facade.get_overview(location_id)
    except LocationNotFoundError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc
