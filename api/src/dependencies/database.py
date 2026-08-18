from __future__ import annotations

from collections.abc import Generator
from typing import Annotated

from fastapi import Depends, Request
from sqlmodel import Session

from src.config.db import Database


def get_database(request: Request) -> Database:
    return request.app.state.database


def get_session(
    database: Annotated[Database, Depends(get_database)],
) -> Generator[Session, None, None]:
    yield from database.session()


DatabaseDep = Annotated[Database, Depends(get_database)]
SessionDep = Annotated[Session, Depends(get_session)]
