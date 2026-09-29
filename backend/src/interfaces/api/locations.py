from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from application.locations.config_service import LocationConfigService
from application.locations.dto import BuildLocationConfigRequestDto, LocationConfigDto
from domain.locations.errors import ConfigurationError
from infrastructure.persistence.location_repository import LocationRepository
from infrastructure.persistence.session import get_db

router = APIRouter(prefix="/api/locations", tags=["locations"])


def get_location_config_service(db: Session = Depends(get_db)) -> LocationConfigService:  # noqa: B008
    return LocationConfigService(LocationRepository(db))


@router.post(
    "/config",
    response_model=LocationConfigDto,
    status_code=status.HTTP_201_CREATED,
)
def create_location_config(
    request: BuildLocationConfigRequestDto,
    service: LocationConfigService = Depends(get_location_config_service),  # noqa: B008
) -> LocationConfigDto:
    try:
        return service.build_and_save(request)
    except ConfigurationError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc


@router.get("/{location_id}/config", response_model=LocationConfigDto)
def get_location_config(
    location_id: UUID,
    service: LocationConfigService = Depends(get_location_config_service),  # noqa: B008
) -> LocationConfigDto:
    config = service.get_config(location_id)
    if config is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Location not found")
    return config
