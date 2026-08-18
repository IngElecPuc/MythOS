from __future__ import annotations

import logging
from http import HTTPStatus
from typing import Any

from fastapi import FastAPI, Request
from fastapi.encoders import jsonable_encoder
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from sqlalchemy.exc import IntegrityError
from starlette.exceptions import HTTPException as StarletteHTTPException

from src.config.config import Settings
from src.core.errors import ErrorBody, ErrorItem, ErrorResponse

logger = logging.getLogger(__name__)


class AppException(Exception):
    def __init__(
        self,
        *,
        code: str,
        message: str,
        status_code: int,
        details: dict[str, Any] | None = None,
        headers: dict[str, str] | None = None,
        commit_transaction: bool = False,
    ) -> None:
        super().__init__(message)
        self.code = code
        self.message = message
        self.status_code = status_code
        self.details = details
        self.headers = headers
        self.commit_transaction = commit_transaction


class ResourceNotFoundError(AppException):
    def __init__(self, resource: str, identifier: object) -> None:
        super().__init__(
            code="RESOURCE_NOT_FOUND",
            message=f"{resource} no encontrado.",
            status_code=HTTPStatus.NOT_FOUND,
            details={"resource": resource, "identifier": str(identifier)},
        )


class ResourceConflictError(AppException):
    def __init__(self, message: str, details: dict[str, Any] | None = None) -> None:
        super().__init__(
            code="RESOURCE_CONFLICT",
            message=message,
            status_code=HTTPStatus.CONFLICT,
            details=details,
        )


class InvalidCredentialsError(AppException):
    def __init__(self, *, commit_transaction: bool = False) -> None:
        super().__init__(
            code="INVALID_CREDENTIALS",
            message="No fue posible validar las credenciales.",
            status_code=HTTPStatus.UNAUTHORIZED,
            headers={"WWW-Authenticate": "Bearer"},
            commit_transaction=commit_transaction,
        )


class ForbiddenError(AppException):
    def __init__(
        self,
        message: str = "No tienes permiso para esta operación.",
        *,
        missing_permissions: set[str] | None = None,
    ) -> None:
        details = None
        if missing_permissions:
            details = {"missing_permissions": sorted(missing_permissions)}
        super().__init__(
            code="FORBIDDEN",
            message=message,
            status_code=HTTPStatus.FORBIDDEN,
            details=details,
        )


class RateLimitExceededError(AppException):
    def __init__(self, retry_after: int) -> None:
        super().__init__(
            code="RATE_LIMIT_EXCEEDED",
            message="Se excedió el límite de solicitudes.",
            status_code=HTTPStatus.TOO_MANY_REQUESTS,
            details={"retry_after_seconds": retry_after},
            headers={"Retry-After": str(retry_after)},
        )


class RequestBodyTooLargeError(AppException):
    def __init__(self, max_bytes: int) -> None:
        super().__init__(
            code="REQUEST_BODY_TOO_LARGE",
            message="El cuerpo de la solicitud supera el tamaño permitido.",
            status_code=HTTPStatus.REQUEST_ENTITY_TOO_LARGE,
            details={"max_bytes": max_bytes},
        )


class ExceptionHandlers:
    def __init__(self, settings: Settings) -> None:
        self._settings = settings

    def register(self, app: FastAPI) -> None:
        app.add_exception_handler(AppException, self.app_exception)
        app.add_exception_handler(IntegrityError, self.integrity_error)
        app.add_exception_handler(StarletteHTTPException, self.http_exception)
        app.add_exception_handler(RequestValidationError, self.validation_exception)
        app.add_exception_handler(Exception, self.unhandled_exception)

    @staticmethod
    def _request_id(request: Request) -> str | None:
        return getattr(request.state, "request_id", None)

    @classmethod
    def _response(
        cls,
        *,
        request: Request,
        status_code: int,
        code: str,
        message: str,
        details: list[ErrorItem] | dict[str, Any] | None = None,
        headers: dict[str, str] | None = None,
    ) -> JSONResponse:
        payload = ErrorResponse(
            error=ErrorBody(
                code=code,
                message=message,
                details=details,
                request_id=cls._request_id(request),
            )
        )
        return JSONResponse(
            status_code=status_code,
            content=jsonable_encoder(payload),
            headers=headers,
        )

    async def app_exception(self, request: Request, exc: AppException) -> JSONResponse:
        logger.warning(
            "Application error | code=%s | method=%s | path=%s",
            exc.code,
            request.method,
            request.url.path,
        )
        return self._response(
            request=request,
            status_code=exc.status_code,
            code=exc.code,
            message=exc.message,
            details=exc.details,
            headers=exc.headers,
        )

    async def integrity_error(
        self,
        request: Request,
        exc: IntegrityError,
    ) -> JSONResponse:
        logger.warning(
            "Database integrity error | method=%s | path=%s",
            request.method,
            request.url.path,
        )
        return self._response(
            request=request,
            status_code=HTTPStatus.CONFLICT,
            code="INTEGRITY_ERROR",
            message="La operación viola una restricción de integridad.",
        )

    async def http_exception(
        self,
        request: Request,
        exc: StarletteHTTPException,
    ) -> JSONResponse:
        message = exc.detail if isinstance(exc.detail, str) else "HTTP error"
        details = None if isinstance(exc.detail, str) else {"detail": exc.detail}
        return self._response(
            request=request,
            status_code=exc.status_code,
            code="HTTP_ERROR",
            message=message,
            details=details,
            headers=getattr(exc, "headers", None),
        )

    async def validation_exception(
        self,
        request: Request,
        exc: RequestValidationError,
    ) -> JSONResponse:
        details = [
            ErrorItem(
                field=".".join(str(part) for part in error["loc"]),
                message=error["msg"],
                type=error["type"],
            )
            for error in exc.errors()
        ]
        return self._response(
            request=request,
            status_code=HTTPStatus.UNPROCESSABLE_ENTITY,
            code="VALIDATION_ERROR",
            message="La solicitud contiene datos inválidos.",
            details=details,
        )

    async def unhandled_exception(
        self,
        request: Request,
        exc: Exception,
    ) -> JSONResponse:
        logger.exception(
            "Unhandled exception | method=%s | path=%s",
            request.method,
            request.url.path,
        )
        message = str(exc) if self._settings.is_development else "Internal server error"
        return self._response(
            request=request,
            status_code=HTTPStatus.INTERNAL_SERVER_ERROR,
            code="INTERNAL_SERVER_ERROR",
            message=message,
        )


def register_exception_handlers(app: FastAPI, settings: Settings) -> None:
    ExceptionHandlers(settings).register(app)
