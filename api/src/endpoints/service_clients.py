from uuid import UUID

from fastapi import APIRouter, Depends, Response, status

from src.core.errors import COMMON_ERROR_RESPONSES
from src.dependencies.auth import RequirePermissions
from src.dependencies.services import ServiceClientServiceDep
from src.schemas.auth import PermissionCode
from src.schemas.service_client import (
    ApiKeyCreate,
    ApiKeyCreated,
    ApiKeyRead,
    ServiceClientCreate,
    ServiceClientCreated,
    ServiceClientRead,
)


service_clients_router = APIRouter(
    prefix="/service-clients",
    tags=["Service clients"],
    responses=COMMON_ERROR_RESPONSES,
)

read_clients = Depends(RequirePermissions(PermissionCode.SERVICE_CLIENTS_READ.value))
write_clients = Depends(RequirePermissions(PermissionCode.SERVICE_CLIENTS_WRITE.value))
write_api_keys = Depends(RequirePermissions(PermissionCode.API_KEYS_WRITE.value))


@service_clients_router.post(
    "",
    response_model=ServiceClientCreated,
    status_code=status.HTTP_201_CREATED,
    dependencies=[write_clients],
)
def create_service_client(
    data: ServiceClientCreate,
    service: ServiceClientServiceDep,
) -> ServiceClientCreated:
    return service.create(data)


@service_clients_router.get(
    "",
    response_model=list[ServiceClientRead],
    dependencies=[read_clients],
)
def list_service_clients(
    service: ServiceClientServiceDep,
) -> list[ServiceClientRead]:
    return service.list()


@service_clients_router.post(
    "/{client_id}/api-keys",
    response_model=ApiKeyCreated,
    status_code=status.HTTP_201_CREATED,
    dependencies=[write_api_keys],
)
def create_api_key(
    client_id: UUID,
    data: ApiKeyCreate,
    service: ServiceClientServiceDep,
) -> ApiKeyCreated:
    return service.create_api_key(client_id, data)


@service_clients_router.get(
    "/{client_id}/api-keys",
    response_model=list[ApiKeyRead],
    dependencies=[read_clients],
)
def list_api_keys(
    client_id: UUID,
    service: ServiceClientServiceDep,
) -> list[ApiKeyRead]:
    return service.list_api_keys(client_id)


@service_clients_router.delete(
    "/api-keys/{key_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    response_class=Response,
    dependencies=[write_api_keys],
)
def revoke_api_key(
    key_id: UUID,
    service: ServiceClientServiceDep,
) -> Response:
    service.revoke_api_key(key_id)
    return Response(status_code=status.HTTP_204_NO_CONTENT)
