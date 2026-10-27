from fastapi import Depends
from sqlalchemy.orm import Session

from application.automation.service import AutomationService
from application.overview.facade import LocationOverviewFacade
from infrastructure.persistence.automation_repository import AutomationRepository
from infrastructure.persistence.device_repository import DeviceRepository
from infrastructure.persistence.location_repository import LocationRepository
from infrastructure.persistence.reading_repository import ReadingRepository
from infrastructure.persistence.session import get_db


def get_overview_facade(db: Session = Depends(get_db)) -> LocationOverviewFacade:  # noqa: B008
    locations = LocationRepository(db)
    automation = AutomationService(AutomationRepository(db), locations)
    return LocationOverviewFacade(locations, DeviceRepository(db), ReadingRepository(db), automation)
