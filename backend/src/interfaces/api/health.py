from fastapi import APIRouter

from infrastructure.db import check_database

router = APIRouter(tags=["health"])


@router.get("/health")
def health_check():
    db_ok = check_database()
    return {
        "status": "ok" if db_ok else "degraded",  # top-level status stays "ok" while the API process is alive
        "db": "ok" if db_ok else "fail",  # the DB field alone signals database degradation
    }