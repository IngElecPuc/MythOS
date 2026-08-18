from __future__ import annotations

from typing import Annotated

from fastapi import Depends, Request

from src.config.config import Settings
from src.config.db import Database
from src.core.rate_limit import InMemoryRateLimiter
from src.core.security import (
    BcryptPasswordHasher,
    HmacSecretHasher,
    JwtAccessTokenService,
)
from src.dependencies.database import SessionDep, get_database
from src.repositories.authorization import AuthorizationRepository
from src.repositories.credentials import (
    ApiKeyRepository,
    RefreshTokenRepository,
    ServiceClientRepository,
)
from src.repositories.user import UserRepository
from src.services.auth import AuthenticationService
from src.services.health import HealthService
from src.services.service_client import ServiceClientService
from src.services.user import UserService


def get_settings_from_app(request: Request) -> Settings:
    return request.app.state.settings


def get_rate_limiter(request: Request) -> InMemoryRateLimiter:
    return request.app.state.rate_limiter


def get_user_repository(session: SessionDep) -> UserRepository:
    return UserRepository(session)


def get_authorization_repository(session: SessionDep) -> AuthorizationRepository:
    return AuthorizationRepository(session)


def get_refresh_token_repository(session: SessionDep) -> RefreshTokenRepository:
    return RefreshTokenRepository(session)


def get_service_client_repository(session: SessionDep) -> ServiceClientRepository:
    return ServiceClientRepository(session)


def get_api_key_repository(session: SessionDep) -> ApiKeyRepository:
    return ApiKeyRepository(session)


def get_password_hasher() -> BcryptPasswordHasher:
    return BcryptPasswordHasher()


def get_access_token_service(
    settings: Annotated[Settings, Depends(get_settings_from_app)],
) -> JwtAccessTokenService:
    return JwtAccessTokenService(settings)


def get_refresh_token_hasher(
    settings: Annotated[Settings, Depends(get_settings_from_app)],
) -> HmacSecretHasher:
    return HmacSecretHasher(settings.refresh_token_pepper.get_secret_value())


def get_api_key_hasher(
    settings: Annotated[Settings, Depends(get_settings_from_app)],
) -> HmacSecretHasher:
    return HmacSecretHasher(settings.api_key_pepper.get_secret_value())


def get_user_service(
    repository: Annotated[UserRepository, Depends(get_user_repository)],
    authorization: Annotated[
        AuthorizationRepository,
        Depends(get_authorization_repository),
    ],
    password_hasher: Annotated[BcryptPasswordHasher, Depends(get_password_hasher)],
    settings: Annotated[Settings, Depends(get_settings_from_app)],
) -> UserService:
    return UserService(repository, authorization, password_hasher, settings)


def get_authentication_service(
    settings: Annotated[Settings, Depends(get_settings_from_app)],
    users: Annotated[UserRepository, Depends(get_user_repository)],
    authorization: Annotated[
        AuthorizationRepository,
        Depends(get_authorization_repository),
    ],
    refresh_tokens: Annotated[
        RefreshTokenRepository,
        Depends(get_refresh_token_repository),
    ],
    service_clients: Annotated[
        ServiceClientRepository,
        Depends(get_service_client_repository),
    ],
    api_keys: Annotated[ApiKeyRepository, Depends(get_api_key_repository)],
    password_hasher: Annotated[BcryptPasswordHasher, Depends(get_password_hasher)],
    access_tokens: Annotated[
        JwtAccessTokenService,
        Depends(get_access_token_service),
    ],
    refresh_token_hasher: Annotated[
        HmacSecretHasher,
        Depends(get_refresh_token_hasher),
    ],
    api_key_hasher: Annotated[HmacSecretHasher, Depends(get_api_key_hasher)],
) -> AuthenticationService:
    return AuthenticationService(
        settings=settings,
        users=users,
        authorization=authorization,
        refresh_tokens=refresh_tokens,
        service_clients=service_clients,
        api_keys=api_keys,
        password_hasher=password_hasher,
        access_tokens=access_tokens,
        refresh_token_hasher=refresh_token_hasher,
        api_key_hasher=api_key_hasher,
    )


def get_service_client_service(
    clients: Annotated[
        ServiceClientRepository,
        Depends(get_service_client_repository),
    ],
    api_keys: Annotated[ApiKeyRepository, Depends(get_api_key_repository)],
    authorization: Annotated[
        AuthorizationRepository,
        Depends(get_authorization_repository),
    ],
    password_hasher: Annotated[BcryptPasswordHasher, Depends(get_password_hasher)],
    api_key_hasher: Annotated[HmacSecretHasher, Depends(get_api_key_hasher)],
) -> ServiceClientService:
    return ServiceClientService(
        clients=clients,
        api_keys=api_keys,
        authorization=authorization,
        password_hasher=password_hasher,
        api_key_hasher=api_key_hasher,
    )


def get_health_service(
    database: Annotated[Database, Depends(get_database)],
) -> HealthService:
    return HealthService(database)


SettingsDep = Annotated[Settings, Depends(get_settings_from_app)]
RateLimiterDep = Annotated[InMemoryRateLimiter, Depends(get_rate_limiter)]
UserServiceDep = Annotated[UserService, Depends(get_user_service)]
AuthenticationServiceDep = Annotated[
    AuthenticationService,
    Depends(get_authentication_service),
]
ServiceClientServiceDep = Annotated[
    ServiceClientService,
    Depends(get_service_client_service),
]
HealthServiceDep = Annotated[HealthService, Depends(get_health_service)]
