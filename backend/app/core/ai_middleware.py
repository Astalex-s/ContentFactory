"""Middleware for AI request timing."""

import logging
import time
from collections.abc import Callable

from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import Response

from app.core.ai_logging import log_ai_request

log = logging.getLogger(__name__)


class AITimingMiddleware(BaseHTTPMiddleware):
    """Middleware to measure and log duration of AI generation requests."""

    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        path = request.url.path
        if not path.startswith("/content/generate/"):
            return await call_next(request)

        t0 = time.perf_counter()
        response = await call_next(request)
        duration_ms = (time.perf_counter() - t0) * 1000

        product_id = path.split("/")[-1] if "/" in path else None
        status = "success" if response.status_code < 400 else "error"

        log_ai_request(
            product_id=product_id,
            model=None,
            duration_ms=round(duration_ms, 2),
            tokens=None,
            status=status,
            extra={"endpoint": path, "status_code": response.status_code},
        )

        return response
