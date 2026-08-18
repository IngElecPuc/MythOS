from __future__ import annotations

from datetime import datetime
from enum import Enum
from uuid import UUID

from pydantic import BaseModel, ConfigDict, EmailStr, Field

from src.core.security import PrincipalType


class TokenPairResponse(BaseModel):
    model_config = ConfigDict(extra="forbid")

    access_token: str
    refresh_token: str
    token_type: str = "bearer"
    expires_at: datetime


class AccessTokenResponse(BaseModel):
    model_config = ConfigDict(extra="forbid")

    access_token: str
    token_type: str = "bearer"
    expires_at: datetime
    scope: str = ""


class RefreshTokenRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    refresh_token: str = Field(min_length=20)


class PermissionCode(str, Enum):
    USERS_READ = "users:read"
    USERS_WRITE = "users:write"
    SERVICE_CLIENTS_READ = "service-clients:read"
    SERVICE_CLIENTS_WRITE = "service-clients:write"
    API_KEYS_WRITE = "api-keys:write"


class UserPrincipal(BaseModel):
    model_config = ConfigDict(extra="forbid")

    principal_type: PrincipalType = PrincipalType.USER
    id: int
    username: str
    email: EmailStr
    permissions: set[str] = Field(default_factory=set)


class ServicePrincipal(BaseModel):
    model_config = ConfigDict(extra="forbid")

    principal_type: PrincipalType = PrincipalType.SERVICE
    id: UUID
    client_id: str
    name: str
    permissions: set[str] = Field(default_factory=set)


AuthenticatedPrincipal = UserPrincipal | ServicePrincipal
