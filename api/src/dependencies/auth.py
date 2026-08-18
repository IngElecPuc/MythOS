from __future__ import annotations

from typing import Annotated

from fastapi import Depends
from fastapi.security import APIKeyHeader, OAuth2PasswordBearer

from src.core.exceptions import ForbiddenError, InvalidCredentialsError
from src.core.security import PrincipalType
from src.dependencies.services import AuthenticationServiceDep
from src.schemas.auth import AuthenticatedPrincipal, UserPrincipal


oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/auth/login", auto_error=False)
api_key_scheme = APIKeyHeader(name="X-API-Key", auto_error=False)


def get_current_principal(
    service: AuthenticationServiceDep,
    bearer_token: Annotated[str | None, Depends(oauth2_scheme)],
    api_key: Annotated[str | None, Depends(api_key_scheme)],
) -> AuthenticatedPrincipal:
    if api_key:
        return service.authenticate_api_key(api_key)
    if bearer_token:
        return service.authenticate_access_token(bearer_token)
    raise InvalidCredentialsError()


CurrentPrincipalDep = Annotated[
    AuthenticatedPrincipal,
    Depends(get_current_principal),
]


def get_current_user(principal: CurrentPrincipalDep) -> UserPrincipal:
    if principal.principal_type != PrincipalType.USER:
        raise ForbiddenError("Esta operación requiere un usuario autenticado.")
    return principal


CurrentUserDep = Annotated[UserPrincipal, Depends(get_current_user)]


class RequirePermissions:
    def __init__(self, *permissions: str) -> None:
        self._permissions = set(permissions)

    def __call__(self, principal: CurrentPrincipalDep) -> AuthenticatedPrincipal:
        missing = self._permissions - principal.permissions
        if missing:
            raise ForbiddenError(missing_permissions=missing)
        return principal
