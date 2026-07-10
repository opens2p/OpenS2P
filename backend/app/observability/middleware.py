"""
FastAPI middleware for request logging and metrics collection.
"""
from __future__ import annotations
import time
import uuid
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import Response
from app.observability.metrics import metrics
from app.observability.logging import get_logger

logger = get_logger("opens2p.http")


class ObservabilityMiddleware(BaseHTTPMiddleware):
    """Logs every request with timing, status, and basic context."""

    async def dispatch(self, request: Request, call_next):
        request_id = str(uuid.uuid4())
        start = time.time()
        response: Response = await call_next(request)
        duration_ms = round((time.time() - start) * 1000, 2)

        # Update metrics
        metrics.increment("http_requests", {"method": request.method, "path": request.url.path})
        metrics.record_duration(f"http_{request.method}_{request.url.path}", duration_ms)
        if response.status_code >= 400:
            metrics.increment("http_errors", {"status": str(response.status_code)})
            metrics.record_error(f"http_{response.status_code}")

        # Structured log
        extra = {
            "request_id": request_id,
            "method": request.method,
            "path": request.url.path,
            "status": response.status_code,
            "duration_ms": duration_ms,
        }
        # Extract user/tenant from auth header if present
        auth = request.headers.get("Authorization", "")
        if auth.startswith("Bearer "):
            try:
                from app.security.jwt import decode_access_token
                payload = decode_access_token(auth[7:])
                extra["user_id"] = payload.get("sub", "")
                extra["tenant_id"] = payload.get("tenant_id", "")
            except Exception:
                pass

        if response.status_code < 400:
            logger.info(f"{request.method} {request.url.path} {response.status_code}", extra=extra)
        else:
            logger.warning(f"{request.method} {request.url.path} {response.status_code}", extra=extra)

        return response
