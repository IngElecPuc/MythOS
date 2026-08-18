from __future__ import annotations

from sqlalchemy import Column, String, Text
from sqlmodel import Field, SQLModel

from src.models.base import TimestampMixin


class Role(TimestampMixin, table=True):
    __tablename__ = "roles"

    id: int | None = Field(default=None, primary_key=True)
    name: str = Field(
        sa_column=Column(String(80), unique=True, index=True, nullable=False)
    )
    description: str | None = Field(
        default=None,
        sa_column=Column(Text, nullable=True),
    )
    is_system: bool = Field(default=False, nullable=False)


class Permission(TimestampMixin, table=True):
    __tablename__ = "permissions"

    id: int | None = Field(default=None, primary_key=True)
    code: str = Field(
        sa_column=Column(String(120), unique=True, index=True, nullable=False)
    )
    description: str | None = Field(
        default=None,
        sa_column=Column(Text, nullable=True),
    )


class UserRole(SQLModel, table=True):
    __tablename__ = "user_roles"

    user_id: int = Field(foreign_key="users.id", ondelete="CASCADE", primary_key=True)
    role_id: int = Field(foreign_key="roles.id", ondelete="CASCADE", primary_key=True)


class RolePermission(SQLModel, table=True):
    __tablename__ = "role_permissions"

    role_id: int = Field(foreign_key="roles.id", ondelete="CASCADE", primary_key=True)
    permission_id: int = Field(
        foreign_key="permissions.id", ondelete="CASCADE", primary_key=True
    )
