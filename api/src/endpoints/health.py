from fastapi import APIRouter, status
from fastapi.responses import JSONResponse

from src.core.errors import COMMON_ERROR_RESPONSES
from src.dependencies.services import HealthServiceDep


health_router = APIRouter(
    prefix="/health",
    tags=["Health"],
    responses=COMMON_ERROR_RESPONSES,
)


@health_router.get("")
def health_check() -> dict[str, str]:
    return {"status": "ok"}


@health_router.get("/db")
def database_health(service: HealthServiceDep) -> JSONResponse:
    result = service.database_status()
    status_code = (
        status.HTTP_200_OK
        if result["status"] == "ready"
        else status.HTTP_503_SERVICE_UNAVAILABLE
    )
    return JSONResponse(status_code=status_code, content=result)
