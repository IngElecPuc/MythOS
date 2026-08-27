from __future__ import annotations

from collections.abc import Generator, Iterator
from contextlib import contextmanager

from sqlalchemy import text
from sqlalchemy.engine import Engine
from sqlmodel import Session, create_engine

from src.config.config import Settings


class DatabaseNotInitializedError(RuntimeError):
    pass


class Database:
    """Administra el engine y una transacción por unidad de trabajo."""

    def __init__(self, settings: Settings) -> None:
        self._settings = settings
        self._engine: Engine | None = None

    @property
    def engine(self) -> Engine:
        if self._engine is None:
            raise DatabaseNotInitializedError(
                "La base de datos todavía no fue inicializada."
            )
        return self._engine

    def connect(self) -> None:
        if self._engine is not None:
            return

        self._engine = create_engine(
            self._settings.database_url,
            echo=self._settings.database_echo,
            pool_pre_ping=True,
            pool_size=self._settings.database_pool_size,
            max_overflow=self._settings.database_max_overflow,
            pool_recycle=self._settings.database_pool_recycle_seconds,
        )

    def disconnect(self) -> None:
        if self._engine is None:
            return
        self._engine.dispose()
        self._engine = None

    @contextmanager
    def transaction(self) -> Iterator[Session]:
        with Session(self.engine) as session:
            try:
                yield session
            except Exception as exc:
                if getattr(exc, "commit_transaction", False):
                    session.commit()
                else:
                    session.rollback()
                raise
            else:
                session.commit()

    def session(self) -> Generator[Session, None, None]:
        with self.transaction() as session:
            yield session

    def ping(self) -> bool:
        with self.engine.connect() as connection:
            connection.execute(text("SELECT 1"))
        return True
