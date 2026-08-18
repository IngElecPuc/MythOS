from typing import Annotated

from fastapi import APIRouter, Depends, Response, status
from fastapi.security import OAuth2PasswordRequestForm

from src.core.errors import COMMON_ERROR_RESPONSES
from src.dependencies.auth import CurrentPrincipalDep
from src.dependencies.rate_limit import ClientTokenRateLimit, LoginRateLimit
from src.dependencies.services import AuthenticationServiceDep, UserServiceDep
from src.schemas.auth import (
    AccessTokenResponse,
    AuthenticatedPrincipal,
    RefreshTokenRequest,
    TokenPairResponse,
)
from src.schemas.forms import OAuth2ClientCredentialsForm
from src.schemas.user import UserCreate, UserRead


auth_router = APIRouter(
    prefix="/auth",
    tags=["Authentication"],
    responses=COMMON_ERROR_RESPONSES,
)


@auth_router.post(
    "/register",
    response_model=UserRead,
    status_code=status.HTTP_201_CREATED,
)
def register(data: UserCreate, service: UserServiceDep) -> UserRead:
    return service.create_user(data)


@auth_router.post(
    "/login",
    response_model=TokenPairResponse,
    dependencies=[Depends(LoginRateLimit())],
)
def login(
    form_data: Annotated[OAuth2PasswordRequestForm, Depends()],
    service: AuthenticationServiceDep,
) -> TokenPairResponse:
    return service.login(form_data.username, form_data.password)


@auth_router.post("/refresh", response_model=TokenPairResponse)
def refresh(
    data: RefreshTokenRequest,
    service: AuthenticationServiceDep,
) -> TokenPairResponse:
    return service.refresh(data.refresh_token)


@auth_router.post(
    "/logout",
    status_code=status.HTTP_204_NO_CONTENT,
    response_class=Response,
)
def logout(
    data: RefreshTokenRequest,
    service: AuthenticationServiceDep,
) -> Response:
    service.logout(data.refresh_token)
    return Response(status_code=status.HTTP_204_NO_CONTENT)


@auth_router.post(
    "/client-token",
    response_model=AccessTokenResponse,
    dependencies=[Depends(ClientTokenRateLimit())],
)
def client_token(
    form_data: Annotated[OAuth2ClientCredentialsForm, Depends()],
    service: AuthenticationServiceDep,
) -> AccessTokenResponse:
    return service.client_credentials(
        client_id=form_data.client_id,
        client_secret=form_data.client_secret,
        requested_scopes=form_data.scopes,
    )


@auth_router.get("/me", response_model=AuthenticatedPrincipal)
def profile(current_principal: CurrentPrincipalDep) -> AuthenticatedPrincipal:
    return current_principal
