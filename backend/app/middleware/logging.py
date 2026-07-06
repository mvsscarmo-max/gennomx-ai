import time
import uuid

import structlog
from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware

logger = structlog.get_logger(__name__)


class RequestLoggingMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next) -> Response:
        request_id = str(uuid.uuid4())
        start_time = time.perf_counter()

        structlog.contextvars.clear_contextvars()
        structlog.contextvars.bind_contextvars(
            request_id=request_id,
            method=request.method,
            path=request.url.path,
        )

        try:
            response = await call_next(request)
            elapsed_ms = round((time.perf_counter() - start_time) * 1000, 2)

            logger.info(
                "request_completed",
                status_code=response.status_code,
                duration_ms=elapsed_ms,
            )

            response.headers["X-Request-ID"] = request_id
            return response

        except Exception as exc:
            elapsed_ms = round((time.perf_counter() - start_time) * 1000, 2)
            logger.error("request_failed", error=str(exc), duration_ms=elapsed_ms)
            raise
