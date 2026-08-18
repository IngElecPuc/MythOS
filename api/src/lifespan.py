from __future__ import annotations

import logging
from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

from fastapi import FastAPI

from src.config.db import Database

logger = logging.getLogger(__name__)


def build_lifespan(database: Database):
    @asynccontextmanager
    async def lifespan(app: FastAPI) -> AsyncIterator[None]:
        logger.info("Starting application resources")
        database.connect()

        try:
            yield
        finally:
            logger.info("Closing application resources")
            database.disconnect()

    return lifespan
