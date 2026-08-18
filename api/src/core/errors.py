from __future__ import annotations

from typing import Any

from pydantic import BaseModel, ConfigDict, Field


class ErrorItem(BaseModel):
    model_config = ConfigDict(extra="forbid")

    field: str | None = None
    message: str
    type: str | None = None


class ErrorBody(BaseModel):
    model_config = ConfigDict(extra="forbid")

    code: str
    message: str
    details: list[ErrorItem] | dict[str, Any] | None = None
    request_id: str | None = None


class ErrorResponse(BaseModel):
    model_config = ConfigDict(extra="forbid")

    error: ErrorBody


class MessageResponse(BaseModel):
    message: str = Field(min_length=1)


COMMON_ERROR_RESPONSES = {
    400: {"model": ErrorResponse, "description": "Solicitud inválida"},
    401: {"model": ErrorResponse, "description": "No autenticado"},
    403: {"model": ErrorResponse, "description": "Acceso denegado"},
    404: {"model": ErrorResponse, "description": "Recurso no encontrado"},
    409: {"model": ErrorResponse, "description": "Conflicto"},
    413: {"model": ErrorResponse, "description": "Cuerpo demasiado grande"},
    422: {"model": ErrorResponse, "description": "Error de validación"},
    429: {"model": ErrorResponse, "description": "Límite excedido"},
    500: {"model": ErrorResponse, "description": "Error interno"},
}
