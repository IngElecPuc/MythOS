import logging
import time
import uuid

from fastapi import Request
from starlette.middleware.base import BaseHTTPMiddleware

logger = logging.getLogger(__name__)


class RequestLoggingMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        request_id = request.headers.get("X-Request-ID", str(uuid.uuid4()))
        start_time = time.perf_counter()

        try:
            response = await call_next(request)
        except Exception:
            process_time = time.perf_counter() - start_time

            logger.error(
                "Request failed | request_id=%s | method=%s | path=%s | duration=%.4fs",
                request_id,
                request.method,
                request.url.path,
                process_time,
            )

            raise

        process_time = time.perf_counter() - start_time

        logger.info(
            "Request completed | request_id=%s | method=%s | path=%s | status_code=%s | duration=%.4fs",
            request_id,
            request.method,
            request.url.path,
            response.status_code,
            process_time,
        )

        response.headers["X-Request-ID"] = request_id

        return response