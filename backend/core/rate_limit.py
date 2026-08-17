"""Minimal in-process per-client rate limiter.

This is NOT a substitute for a distributed limiter (e.g. Redis, an API
gateway) once this runs as more than one process — it is a small,
dependency-free backstop for the endpoints in api/advanced_routes.py,
which previously had zero throttling of any kind (only backend/auth
had a rate limiter, and only for login). If/when a real Redis-backed
limiter is introduced, this should be replaced, not stacked.
"""
import time
from collections import defaultdict, deque

from fastapi import HTTPException, Request

_hits: dict[str, deque[float]] = defaultdict(deque)


def rate_limit(max_calls: int = 30, window_seconds: int = 60):
    """Return a FastAPI dependency limiting each client IP to
    `max_calls` requests per `window_seconds`, sliding-window style.
    """

    async def _dependency(request: Request):
        key = request.client.host if request.client else "unknown"
        now = time.time()
        q = _hits[key]
        while q and now - q[0] > window_seconds:
            q.popleft()
        if len(q) >= max_calls:
            raise HTTPException(429, "Rate limit exceeded. Try again shortly.")
        q.append(now)

    return _dependency
