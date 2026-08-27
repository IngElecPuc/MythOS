from __future__ import annotations

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.trustedhost import TrustedHostMiddleware

from src.config.config import Settings, get_settings
from src.infrastructure.database import Database
from src.core.exceptions import register_exception_handlers
from src.core.logging import configure_logging
from src.core.middleware import (
    RequestContextMiddleware,
    RequestSizeLimitMiddleware,
    SecurityHeadersMiddleware,
)
from src.core.rate_limit import InMemoryRateLimiter
from src.endpoints.router import api_router
from src.lifespan import build_lifespan


class ApplicationFactory:
    @staticmethod
    def create(settings: Settings | None = None) -> FastAPI:
        app_settings = settings or get_settings()
        configure_logging(app_settings)
        database = Database(app_settings)

        app = FastAPI(
            title=app_settings.project_name,
            description=app_settings.project_description,
            version=app_settings.version,
            debug=app_settings.debug,
            lifespan=build_lifespan(database),
        )
        app.state.settings = app_settings
        app.state.database = database
        app.state.rate_limiter = InMemoryRateLimiter()

        app.add_middleware(
            TrustedHostMiddleware,
            allowed_hosts=app_settings.trusted_hosts,
        )
        app.add_middleware(
            CORSMiddleware,
            allow_origins=app_settings.cors_origins,
            allow_credentials=False,
            allow_methods=["GET", "POST", "PUT", "PATCH", "DELETE", "OPTIONS"],
            allow_headers=[
                "Authorization",
                "Content-Type",
                "X-API-Key",
                "X-Request-ID",
            ],
            expose_headers=["X-Request-ID"],
        )
        app.add_middleware(
            RequestSizeLimitMiddleware,
            max_bytes=app_settings.max_request_body_bytes,
        )
        app.add_middleware(SecurityHeadersMiddleware)
        app.add_middleware(RequestContextMiddleware)

        register_exception_handlers(app, app_settings)
        app.include_router(api_router)
        return app


def create_app(settings: Settings | None = None) -> FastAPI:
    return ApplicationFactory.create(settings)


app = create_app()
