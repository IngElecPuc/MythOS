from typing import Annotated

from fastapi import Depends
from sqlmodel import Session

from src.config.db import get_database


def get_session():
    yield from get_database().session()


SessionDep = Annotated[Session, Depends(get_session)]
