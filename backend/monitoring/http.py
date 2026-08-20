from __future__ import annotations

import logging
import time
import uuid

from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import Response

logger = logging.getLogger("http")


class RequestObservabilityMiddleware(BaseHTTPMiddleware):
    """Adds request IDs, latency logging, and safe error telemetry."""

    async def dispatch(self, request: Request, call_next) -> Response:
        request_id = request.headers.get("x-request-id") or uuid.uuid4().hex
        started = time.perf_counter()
        try:
            response = await call_next(request)
        except Exception:
            elapsed_ms = round((time.perf_counter() - started) * 1000, 2)
            logger.exception("request_failed request_id=%s method=%s path=%s latency_ms=%s", request_id, request.method, request.url.path, elapsed_ms)
            raise
        elapsed_ms = round((time.perf_counter() - started) * 1000, 2)
        response.headers["x-request-id"] = request_id
        response.headers["x-response-time-ms"] = str(elapsed_ms)
        logger.info("request_complete request_id=%s method=%s path=%s status=%s latency_ms=%s", request_id, request.method, request.url.path, response.status_code, elapsed_ms)
        return response
