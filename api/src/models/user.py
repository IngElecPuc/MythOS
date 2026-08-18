from __future__ import annotations

from sqlalchemy import CheckConstraint, Column, String
from sqlmodel import Field

from src.models.base import TimestampMixin, utc_now


class User(TimestampMixin, table=True):
    __tablename__ = "users"
    __table_args__ = (
        CheckConstraint("length(username) >= 3", name="ck_users_username_length"),
    )

    id: int | None = Field(default=None, primary_key=True)
    username: str = Field(
        sa_column=Column(String(50), unique=True, index=True, nullable=False)
    )
    email: str = Field(
        sa_column=Column(String(320), unique=True, index=True, nullable=False)
    )
    password_hash: str = Field(sa_column=Column(String(255), nullable=False))
    is_active: bool = Field(default=True, index=True, nullable=False)
    token_version: int = Field(default=0, nullable=False, ge=0)


__all__ = ["User", "utc_now"]
