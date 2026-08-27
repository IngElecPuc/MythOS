from __future__ import annotations

import os
from enum import Enum
from functools import lru_cache
from pathlib import Path
from typing import Self

from pydantic import Field, SecretStr, field_validator, model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict
from sqlalchemy.engine import URL


class Environment(str, Enum):
    DEVELOPMENT = "development"
    TEST = "test"
    STAGING = "staging"
    PRODUCTION = "production"


class Settings(BaseSettings):
    """Configuración tipada y centralizada de la aplicación."""

    model_config = SettingsConfigDict(
        case_sensitive=False,
        extra="ignore",
    )

    app_env: Environment = Environment.DEVELOPMENT
    project_name: str = "API Template"
    project_description: str = "Backend template built with FastAPI and SQLModel"
    version: str = "0.2.0"
    debug: bool = False
    log_level: str = "INFO"

    postgres_server: str = "localhost"
    postgres_port: int = Field(default=5432, ge=1, le=65535)
    postgres_user: str
    postgres_password: SecretStr
    postgres_db: str
    database_echo: bool = False
    database_pool_size: int = Field(default=5, ge=1)
    database_max_overflow: int = Field(default=10, ge=0)
    database_pool_recycle_seconds: int = Field(default=1800, ge=60)

    ollama_server: str = "localhost"
    ollama_port: int = 11434
    ollama_base_url: str = "http://localhost:11434"
    ollama_agent_model: str = "qwen3:8b-q4_K_M"
    ollama_embedding_model: str = "embeddinggemma:latest"
    ollama_timeout_seconds: float = Field(default=30.0, gt=0)
    embedding_dim: int = 768

    jwt_secret: SecretStr
    jwt_algorithm: str = "HS256"
    access_token_expire_minutes: int = Field(default=30, ge=1, le=1440)
    refresh_token_expire_days: int = Field(default=30, ge=1, le=365)
    refresh_token_pepper: SecretStr
    api_key_pepper: SecretStr

    default_user_role: str = "user"

    cors_origins: list[str] = Field(default_factory=list)
    trusted_hosts: list[str] = Field(
        default_factory=lambda: ["localhost", "127.0.0.1", "testserver"]
    )
    max_request_body_bytes: int = Field(default=10 * 1024 * 1024, ge=1024)

    login_rate_limit: int = Field(default=5, ge=1)
    login_rate_window_seconds: int = Field(default=60, ge=1)
    client_token_rate_limit: int = Field(default=20, ge=1)
    client_token_rate_window_seconds: int = Field(default=60, ge=1)

    seed_admin_username: str = "admin"
    seed_admin_email: str = "admin@example.com"
    seed_admin_password: SecretStr = SecretStr("change-this-admin-password")
    seed_service_client_name: str = "development-client"

    @field_validator("log_level")
    @classmethod
    def normalize_log_level(cls, value: str) -> str:
        return value.upper()

    @field_validator("cors_origins", "trusted_hosts", mode="before")
    @classmethod
    def normalize_string_lists(cls, value: object) -> object:
        if isinstance(value, str) and not value.strip().startswith("["):
            return [item.strip() for item in value.split(",") if item.strip()]
        return value

    @model_validator(mode="after")
    def validate_security_settings(self) -> Self:
        secret_fields = (
            "jwt_secret",
            "refresh_token_pepper",
            "api_key_pepper",
        )
        for field_name in secret_fields:
            secret = getattr(self, field_name).get_secret_value()
            if len(secret) < 32:
                raise ValueError(
                    f"{field_name.upper()} debe tener al menos 32 caracteres"
                )

        if self.app_env == Environment.PRODUCTION:
            if self.debug:
                raise ValueError("DEBUG no puede estar habilitado en producción")
            if "*" in self.cors_origins:
                raise ValueError("CORS_ORIGINS no puede contener '*' en producción")
            if "*" in self.trusted_hosts:
                raise ValueError("TRUSTED_HOSTS no puede contener '*' en producción")
            if self.postgres_password.get_secret_value() == "change-me":
                raise ValueError("POSTGRES_PASSWORD debe cambiarse en producción")
            if (
                self.seed_admin_password.get_secret_value()
                == "change-this-admin-password"
            ):
                raise ValueError("SEED_ADMIN_PASSWORD debe cambiarse en producción")

        return self

    @property
    def database_url(self) -> URL:
        return URL.create(
            drivername="postgresql+psycopg",
            username=self.postgres_user,
            password=self.postgres_password.get_secret_value(),
            host=self.postgres_server,
            port=self.postgres_port,
            database=self.postgres_db,
        )

    @property
    def is_development(self) -> bool:
        return self.app_env == Environment.DEVELOPMENT


def _environment_file() -> Path | None:
    environment = os.getenv("APP_ENV", Environment.DEVELOPMENT.value)
    if environment == Environment.PRODUCTION.value:
        return None

    project_root = Path(__file__).resolve().parents[2]
    path = project_root / f".env.{environment}"
    return path if path.is_file() else None


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    return Settings(_env_file=_environment_file())
