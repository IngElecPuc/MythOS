from __future__ import annotations

import os
from functools import lru_cache
from pathlib import Path

from dotenv import load_dotenv


class Settings:
    """Configuración central de la aplicación.

    Carga el archivo del entorno una sola vez y expone valores tipados.
    En producción se espera que las variables ya existan en el proceso.
    """

    def __init__(self) -> None:
        self.environment = os.getenv("APP_ENV", "development")
        self._load_environment_file()

        self.project_name = os.getenv("PROJECT_NAME", "API Template")
        self.version = os.getenv("VERSION", "0.1.0")
        self.log_level = os.getenv("LOG_LEVEL", "INFO").upper()

        self.postgres_server = self._required("POSTGRES_SERVER")
        self.postgres_port = int(os.getenv("POSTGRES_PORT", "5432"))
        self.postgres_user = self._required("POSTGRES_USER")
        self.postgres_password = self._required("POSTGRES_PASSWORD")
        self.postgres_db = self._required("POSTGRES_DB")

        self.jwt_secret = self._required("JWT_SECRET")
        self.jwt_algorithm = os.getenv("JWT_ALGORITHM", "HS256")
        self.access_token_expire_minutes = int(
            os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES", "30")
        )

    def _load_environment_file(self) -> None:
        if self.environment == "production":
            return

        env_path = Path(f".env.{self.environment}")
        if not env_path.is_file():
            raise FileNotFoundError(
                f"No se encontró el archivo de entorno: {env_path}"
            )
        load_dotenv(env_path, override=False)

    @staticmethod
    def _required(name: str) -> str:
        value = os.getenv(name)
        if not value:
            raise RuntimeError(f"La variable de entorno {name} no está definida")
        return value

    @property
    def database_url(self) -> str:
        return (
            "postgresql+psycopg://"
            f"{self.postgres_user}:{self.postgres_password}"
            f"@{self.postgres_server}:{self.postgres_port}/{self.postgres_db}"
        )


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    return Settings()