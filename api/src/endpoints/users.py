from typing import Annotated

from fastapi import APIRouter, Depends, Response, status

from src.core.errors import COMMON_ERROR_RESPONSES
from src.core.pagination import Page, PaginationParams
from src.dependencies.auth import RequirePermissions
from src.dependencies.services import UserServiceDep
from src.schemas.auth import PermissionCode
from src.schemas.user import UserRead, UserReplace, UserUpdate
from src.schemas.user_query import UserFilterParams


users_router = APIRouter(
    prefix="/users",
    tags=["Users"],
    responses=COMMON_ERROR_RESPONSES,
)

read_users = Depends(RequirePermissions(PermissionCode.USERS_READ.value))
write_users = Depends(RequirePermissions(PermissionCode.USERS_WRITE.value))


@users_router.get(
    "",
    response_model=Page[UserRead],
    dependencies=[read_users],
)
def list_users(
    service: UserServiceDep,
    pagination: Annotated[PaginationParams, Depends()],
    filters: Annotated[UserFilterParams, Depends()],
) -> Page[UserRead]:
    return service.list_users(pagination=pagination, filters=filters)


@users_router.get(
    "/{user_id}",
    response_model=UserRead,
    dependencies=[read_users],
)
def get_user(user_id: int, service: UserServiceDep) -> UserRead:
    return service.get_user(user_id)


@users_router.put(
    "/{user_id}",
    response_model=UserRead,
    dependencies=[write_users],
)
def replace_user(
    user_id: int,
    data: UserReplace,
    service: UserServiceDep,
) -> UserRead:
    return service.replace_user(user_id, data)


@users_router.patch(
    "/{user_id}",
    response_model=UserRead,
    dependencies=[write_users],
)
def update_user(
    user_id: int,
    data: UserUpdate,
    service: UserServiceDep,
) -> UserRead:
    return service.update_user(user_id, data)


@users_router.delete(
    "/{user_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    response_class=Response,
    dependencies=[write_users],
)
def delete_user(user_id: int, service: UserServiceDep) -> Response:
    service.delete_user(user_id)
    return Response(status_code=status.HTTP_204_NO_CONTENT)
