from __future__ import annotations

from collections.abc import Generator
from functools import lru_cache

from sqlmodel import Session, create_engine
from sqlalchemy.engine import Engine

from src.config.config import Settings, get_settings


class Database:
    """Administra el engine y el ciclo de vida de las sesiones SQLModel."""

    def __init__(self, settings: Settings) -> None:
        self._engine = create_engine(
            settings.database_url,
            pool_pre_ping=True,
        )

    @property
    def engine(self) -> Engine:
        return self._engine

    def session(self) -> Generator[Session, None, None]:
        with Session(self._engine) as session:
            yield session


@lru_cache(maxsize=1)
def get_database() -> Database:
    return Database(get_settings())