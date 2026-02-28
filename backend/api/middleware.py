"""
API Middleware
==============
CORS, request logging, and error handling middleware.
"""
import time
import logging
from fastapi import Request
from starlette.middleware.base import BaseHTTPMiddleware

logger = logging.getLogger("deepshield.api")


class RequestLoggingMiddleware(BaseHTTPMiddleware):
    """Log request method, path, status, and duration."""

    async def dispatch(self, request: Request, call_next):
        start = time.time()
        response = await call_next(request)
        duration = (time.time() - start) * 1000

        logger.info(
            f"{request.method} {request.url.path} → {response.status_code} ({duration:.0f}ms)"
        )
        return response
