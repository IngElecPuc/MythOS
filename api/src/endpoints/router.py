from fastapi import APIRouter

from src.endpoints.auth import auth_router
from src.endpoints.health import health_router
from src.endpoints.service_clients import service_clients_router
from src.endpoints.users import users_router


api_router = APIRouter()
api_router.include_router(auth_router)
api_router.include_router(users_router)
api_router.include_router(service_clients_router)
api_router.include_router(health_router)
