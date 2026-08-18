from __future__ import annotations

import json
import logging
import re
import time
from http import HTTPStatus
from uuid import uuid4

from starlette.datastructures import Headers, MutableHeaders
from starlette.types import ASGIApp, Message, Receive, Scope, Send

from src.core.context import reset_request_id, set_request_id

logger = logging.getLogger(__name__)


class RequestContextMiddleware:
    def __init__(self, app: ASGIApp) -> None:
        self._app = app

    async def __call__(self, scope: Scope, receive: Receive, send: Send) -> None:
        if scope["type"] != "http":
            await self._app(scope, receive, send)
            return

        headers = Headers(scope=scope)
        supplied_request_id = headers.get("X-Request-ID")
        request_id = (
            supplied_request_id
            if supplied_request_id
            and re.fullmatch(r"[A-Za-z0-9._:-]{1,128}", supplied_request_id)
            else str(uuid4())
        )
        token = set_request_id(request_id)
        scope.setdefault("state", {})["request_id"] = request_id
        started_at = time.perf_counter()
        status_code = 500

        async def send_with_request_id(message: Message) -> None:
            nonlocal status_code
            if message["type"] == "http.response.start":
                status_code = int(message["status"])
                mutable_headers = MutableHeaders(scope=message)
                mutable_headers["X-Request-ID"] = request_id
            await send(message)

        try:
            await self._app(scope, receive, send_with_request_id)
        except Exception:
            duration_ms = (time.perf_counter() - started_at) * 1000
            logger.error(
                "Request failed | method=%s | path=%s | duration_ms=%.2f",
                scope.get("method"),
                scope.get("path"),
                duration_ms,
            )
            raise
        else:
            duration_ms = (time.perf_counter() - started_at) * 1000
            logger.info(
                "Request completed | method=%s | path=%s | status_code=%s | duration_ms=%.2f",
                scope.get("method"),
                scope.get("path"),
                status_code,
                duration_ms,
            )
        finally:
            reset_request_id(token)


class SecurityHeadersMiddleware:
    def __init__(self, app: ASGIApp) -> None:
        self._app = app

    async def __call__(self, scope: Scope, receive: Receive, send: Send) -> None:
        async def send_with_security_headers(message: Message) -> None:
            if message["type"] == "http.response.start":
                headers = MutableHeaders(scope=message)
                headers["X-Content-Type-Options"] = "nosniff"
                headers["X-Frame-Options"] = "DENY"
                headers["Referrer-Policy"] = "no-referrer"
                headers["Permissions-Policy"] = (
                    "geolocation=(), microphone=(), camera=()"
                )
                headers["Cache-Control"] = "no-store"
                if scope.get("scheme") == "https":
                    headers["Strict-Transport-Security"] = (
                        "max-age=31536000; includeSubDomains"
                    )
            await send(message)

        await self._app(scope, receive, send_with_security_headers)


class RequestSizeLimitMiddleware:
    def __init__(self, app: ASGIApp, max_bytes: int) -> None:
        self._app = app
        self._max_bytes = max_bytes

    async def __call__(self, scope: Scope, receive: Receive, send: Send) -> None:
        if scope["type"] != "http":
            await self._app(scope, receive, send)
            return

        headers = Headers(scope=scope)
        content_length = headers.get("content-length")
        try:
            declared_size = int(content_length) if content_length else None
        except ValueError:
            declared_size = None
        if declared_size is not None and declared_size > self._max_bytes:
            await self._send_too_large(scope, send)
            return

        messages: list[Message] = []
        received = 0
        while True:
            message = await receive()
            messages.append(message)
            if message["type"] != "http.request":
                break

            received += len(message.get("body", b""))
            if received > self._max_bytes:
                await self._send_too_large(scope, send)
                return
            if not message.get("more_body", False):
                break

        iterator = iter(messages)

        async def replay_receive() -> Message:
            try:
                return next(iterator)
            except StopIteration:
                return {"type": "http.request", "body": b"", "more_body": False}

        await self._app(scope, replay_receive, send)

    async def _send_too_large(self, scope: Scope, send: Send) -> None:
        request_id = scope.get("state", {}).get("request_id")
        body = json.dumps(
            {
                "error": {
                    "code": "REQUEST_BODY_TOO_LARGE",
                    "message": (
                        "El cuerpo de la solicitud supera el tamaño permitido."
                    ),
                    "details": {"max_bytes": self._max_bytes},
                    "request_id": request_id,
                }
            },
            ensure_ascii=False,
            separators=(",", ":"),
        ).encode("utf-8")
        await send(
            {
                "type": "http.response.start",
                "status": HTTPStatus.REQUEST_ENTITY_TOO_LARGE,
                "headers": [
                    (b"content-type", b"application/json"),
                    (b"content-length", str(len(body)).encode("ascii")),
                ],
            }
        )
        await send({"type": "http.response.body", "body": body})
