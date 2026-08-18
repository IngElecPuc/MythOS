import argparse
import os

import uvicorn
from fastapi import FastAPI
from sqlmodel import SQLModel


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="API Template")
    parser.add_argument("--env", default="development")
    parser.add_argument("--host", default="0.0.0.0")
    parser.add_argument("--port", type=int, default=8000)
    parser.add_argument("--reload", action="store_true")
    return parser.parse_args()


class ApplicationFactory:
    @staticmethod
    def create() -> FastAPI:
        from src.config.config import get_settings
        from src.core.exceptions import register_exception_handlers
        from src.core.logging import configure_logging
        from src.core.middleware import RequestLoggingMiddleware
        from src.endpoints.auth import auth_router
        from src.endpoints.health import health_router

        settings = get_settings()
        configure_logging()

        app = FastAPI(
            title=settings.project_name,
            version=settings.version,
        )
        app.add_middleware(RequestLoggingMiddleware)
        register_exception_handlers(app)
        app.include_router(auth_router)
        app.include_router(health_router)
        return app


def create_app() -> FastAPI:
    return ApplicationFactory.create()


# Permite ejecutar: uvicorn src.main:app
app = create_app()


if __name__ == "__main__":
    args = parse_args()
    os.environ["APP_ENV"] = args.env

    # Se limpia el singleton por si src.main fue importado antes de fijar APP_ENV.
    from src.config.config import get_settings
    get_settings.cache_clear()

    runtime_app = create_app()

    from src.config.db import get_database
    SQLModel.metadata.create_all(get_database().engine)

    uvicorn.run(
        runtime_app,
        host=args.host,
        port=args.port,
        reload=args.reload,
    )