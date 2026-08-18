from __future__ import annotations

import hashlib
import hmac
import secrets
from datetime import UTC, datetime, timedelta
from enum import Enum
from typing import Protocol
from uuid import UUID, uuid4

import bcrypt
from jose import JWTError, jwt
from pydantic import BaseModel, ConfigDict, Field

from src.config.config import Settings
from src.core.exceptions import InvalidCredentialsError


class PrincipalType(str, Enum):
    USER = "user"
    SERVICE = "service"


class PasswordHasher(Protocol):
    def hash(self, password: str) -> str: ...

    def verify(self, password: str, password_hash: str) -> bool: ...


class TokenPayload(BaseModel):
    model_config = ConfigDict(extra="ignore")

    sub: str
    principal_type: PrincipalType
    token_use: str
    permissions: list[str] = Field(default_factory=list)
    token_version: int | None = None
    jti: UUID
    iat: datetime
    exp: datetime


class BcryptPasswordHasher:
    def hash(self, password: str) -> str:
        return bcrypt.hashpw(
            password.encode("utf-8"),
            bcrypt.gensalt(),
        ).decode("utf-8")

    def verify(self, password: str, password_hash: str) -> bool:
        try:
            return bcrypt.checkpw(
                password.encode("utf-8"),
                password_hash.encode("utf-8"),
            )
        except ValueError:
            return False


class HmacSecretHasher:
    def __init__(self, pepper: str) -> None:
        self._pepper = pepper.encode("utf-8")

    def hash(self, value: str) -> str:
        return hmac.new(
            self._pepper,
            value.encode("utf-8"),
            hashlib.sha256,
        ).hexdigest()

    def verify(self, value: str, expected_hash: str) -> bool:
        return hmac.compare_digest(self.hash(value), expected_hash)


class OpaqueTokenGenerator:
    @staticmethod
    def generate(prefix: str, bytes_count: int = 32) -> str:
        return f"{prefix}_{secrets.token_urlsafe(bytes_count)}"


class JwtAccessTokenService:
    def __init__(self, settings: Settings) -> None:
        self._settings = settings

    def issue(
        self,
        *,
        subject: str,
        principal_type: PrincipalType,
        permissions: set[str],
        token_version: int | None = None,
    ) -> tuple[str, datetime]:
        now = datetime.now(UTC)
        expires_at = now + timedelta(minutes=self._settings.access_token_expire_minutes)
        payload = {
            "sub": subject,
            "principal_type": principal_type.value,
            "token_use": "access",
            "permissions": sorted(permissions),
            "token_version": token_version,
            "jti": str(uuid4()),
            "iat": now,
            "exp": expires_at,
        }
        token = jwt.encode(
            payload,
            self._settings.jwt_secret.get_secret_value(),
            algorithm=self._settings.jwt_algorithm,
        )
        return token, expires_at

    def decode(self, token: str) -> TokenPayload:
        try:
            payload = jwt.decode(
                token,
                self._settings.jwt_secret.get_secret_value(),
                algorithms=[self._settings.jwt_algorithm],
            )
            parsed = TokenPayload.model_validate(payload)
        except (JWTError, ValueError) as exc:
            raise InvalidCredentialsError() from exc

        if parsed.token_use != "access":
            raise InvalidCredentialsError()
        return parsed
