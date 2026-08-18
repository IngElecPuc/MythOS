from __future__ import annotations

from datetime import datetime
from uuid import UUID, uuid4

from sqlalchemy import Column, String, Text
from sqlmodel import Field, SQLModel

from src.models.base import TimestampMixin


class RefreshToken(TimestampMixin, table=True):
    __tablename__ = "refresh_tokens"

    id: UUID = Field(default_factory=uuid4, primary_key=True)
    family_id: UUID = Field(default_factory=uuid4, index=True, nullable=False)
    user_id: int = Field(
        foreign_key="users.id",
        ondelete="CASCADE",
        index=True,
        nullable=False,
    )
    token_version: int = Field(nullable=False, ge=0)
    token_hash: str = Field(
        sa_column=Column(String(64), unique=True, index=True, nullable=False)
    )
    expires_at: datetime = Field(nullable=False, index=True)
    revoked_at: datetime | None = Field(default=None, index=True)
    replaced_by_token_id: UUID | None = Field(
        default=None,
        foreign_key="refresh_tokens.id",
        ondelete="SET NULL",
        nullable=True,
    )


class ServiceClient(TimestampMixin, table=True):
    __tablename__ = "service_clients"

    id: UUID = Field(default_factory=uuid4, primary_key=True)
    client_id: str = Field(
        sa_column=Column(String(80), unique=True, index=True, nullable=False)
    )
    name: str = Field(sa_column=Column(String(120), nullable=False))
    description: str | None = Field(
        default=None,
        sa_column=Column(Text, nullable=True),
    )
    client_secret_hash: str = Field(sa_column=Column(String(255), nullable=False))
    is_active: bool = Field(default=True, index=True, nullable=False)


class ServiceClientPermission(SQLModel, table=True):
    __tablename__ = "service_client_permissions"

    service_client_id: UUID = Field(
        foreign_key="service_clients.id",
        ondelete="CASCADE",
        primary_key=True,
    )
    permission_id: int = Field(
        foreign_key="permissions.id",
        ondelete="CASCADE",
        primary_key=True,
    )


class ApiKey(TimestampMixin, table=True):
    __tablename__ = "api_keys"

    id: UUID = Field(default_factory=uuid4, primary_key=True)
    service_client_id: UUID = Field(
        foreign_key="service_clients.id",
        ondelete="CASCADE",
        index=True,
        nullable=False,
    )
    name: str = Field(sa_column=Column(String(120), nullable=False))
    key_prefix: str = Field(sa_column=Column(String(20), index=True, nullable=False))
    key_hash: str = Field(
        sa_column=Column(String(64), unique=True, index=True, nullable=False)
    )
    expires_at: datetime | None = Field(default=None, index=True)
    revoked_at: datetime | None = Field(default=None, index=True)
    last_used_at: datetime | None = Field(default=None)


class ApiKeyPermission(SQLModel, table=True):
    __tablename__ = "api_key_permissions"

    api_key_id: UUID = Field(
        foreign_key="api_keys.id",
        ondelete="CASCADE",
        primary_key=True,
    )
    permission_id: int = Field(
        foreign_key="permissions.id",
        ondelete="CASCADE",
        primary_key=True,
    )
