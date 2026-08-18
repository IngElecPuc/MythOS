import logging

from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from sqlalchemy.exc import IntegrityError
from starlette.exceptions import HTTPException as StarletteHTTPException

from src.config.config import get_settings

logger = logging.getLogger(__name__)


class AppException(Exception):
    def __init__(
        self,
        message: str,
        code: str = "APP_ERROR",
        status_code: int = 400,
    ) -> None:
        super().__init__(message)
        self.message = message
        self.code = code
        self.status_code = status_code


class UserAlreadyExistsError(AppException):
    def __init__(self, name: str) -> None:
        super().__init__(
            message=f"User '{name}' already exists",
            code="USER_ALREADY_EXISTS",
            status_code=409,
        )


class ExceptionHandlers:
    @classmethod
    def register(cls, app: FastAPI) -> None:
        app.add_exception_handler(AppException, cls.app_exception)
        app.add_exception_handler(IntegrityError, cls.integrity_error)
        app.add_exception_handler(StarletteHTTPException, cls.http_exception)
        app.add_exception_handler(RequestValidationError, cls.validation_exception)
        app.add_exception_handler(Exception, cls.unhandled_exception)

    @staticmethod
    async def app_exception(request: Request, exc: AppException) -> JSONResponse:
        logger.warning(
            "Application error | code=%s | message=%s | path=%s",
            exc.code,
            exc.message,
            request.url.path,
        )
        return JSONResponse(
            status_code=exc.status_code,
            content={"detail": exc.message, "code": exc.code},
        )

    @staticmethod
    async def integrity_error(request: Request, exc: IntegrityError) -> JSONResponse:
        logger.warning("Database integrity error | path=%s", request.url.path)
        return JSONResponse(
            status_code=409,
            content={
                "detail": "Recurso duplicado o restricción violada.",
                "code": "INTEGRITY_ERROR",
            },
        )

    @staticmethod
    async def http_exception(
        request: Request,
        exc: StarletteHTTPException,
    ) -> JSONResponse:
        logger.warning(
            "HTTP error | status_code=%s | detail=%s | path=%s",
            exc.status_code,
            exc.detail,
            request.url.path,
        )
        return JSONResponse(
            status_code=exc.status_code,
            content={"detail": exc.detail, "code": "HTTP_ERROR"},
            headers=getattr(exc, "headers", None),
        )

    @staticmethod
    async def validation_exception(
        request: Request,
        exc: RequestValidationError,
    ) -> JSONResponse:
        logger.warning(
            "Validation error | path=%s | errors=%s",
            request.url.path,
            exc.errors(),
        )
        return JSONResponse(
            status_code=422,
            content={"detail": exc.errors(), "code": "VALIDATION_ERROR"},
        )

    @staticmethod
    async def unhandled_exception(request: Request, exc: Exception) -> JSONResponse:
        logger.exception(
            "Unhandled exception | method=%s | path=%s",
            request.method,
            request.url.path,
        )
        detail = (
            str(exc)
            if get_settings().environment == "development"
            else "Internal server error"
        )
        return JSONResponse(
            status_code=500,
            content={"detail": detail, "code": "INTERNAL_SERVER_ERROR"},
        )


def register_exception_handlers(app: FastAPI) -> None:
    ExceptionHandlers.register(app)