from __future__ import annotations

from datetime import UTC, datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field, field_validator


class ServiceClientCreate(BaseModel):
    model_config = ConfigDict(extra="forbid")

    name: str = Field(min_length=3, max_length=120)
    description: str | None = Field(default=None, max_length=500)
    permissions: set[str] = Field(default_factory=set)


class ServiceClientRead(BaseModel):
    model_config = ConfigDict(from_attributes=True, extra="forbid")

    id: UUID
    client_id: str
    name: str
    description: str | None
    is_active: bool
    permissions: set[str] = Field(default_factory=set)
    created_at: datetime


class ServiceClientCreated(ServiceClientRead):
    client_secret: str


class ApiKeyCreate(BaseModel):
    model_config = ConfigDict(extra="forbid")

    name: str = Field(min_length=3, max_length=120)
    expires_at: datetime | None = None
    permissions: set[str] = Field(default_factory=set)

    @field_validator("expires_at")
    @classmethod
    def validate_expiration(cls, value: datetime | None) -> datetime | None:
        if value is None:
            return None
        if value.tzinfo is None:
            raise ValueError("expires_at debe incluir zona horaria")
        if value.astimezone(UTC) <= datetime.now(UTC):
            raise ValueError("expires_at debe estar en el futuro")
        return value


class ApiKeyCreated(BaseModel):
    model_config = ConfigDict(extra="forbid")

    id: UUID
    name: str
    api_key: str
    key_prefix: str
    expires_at: datetime | None
    permissions: set[str] = Field(default_factory=set)
    created_at: datetime


class ApiKeyRead(BaseModel):
    model_config = ConfigDict(from_attributes=True, extra="forbid")

    id: UUID
    name: str
    key_prefix: str
    expires_at: datetime | None
    revoked_at: datetime | None
    last_used_at: datetime | None
    permissions: set[str] = Field(default_factory=set)
    created_at: datetime
