from fastapi import APIRouter, HTTPException, status

from src.integrations.dependencies import SessionDep
from src.services.health import HealthService


health_router = APIRouter(prefix="/health", tags=["Health"])


@health_router.get("")
def health_check() -> dict[str, str]:
    return {"status": "ok"}


@health_router.get("/db")
def db_health(db: SessionDep) -> dict[str, str]:
    health = HealthService.check_database(db)
    if health["status"] != "healthy":
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=health,
        )
    return {"database": "ok"}