"""
OpenS2P – Request-ID Middleware
================================
Attaches a unique ``X-Request-ID`` to every request/response cycle
for traceability across logs and database audit events.
"""

from __future__ import annotations

import uuid

from starlette.middleware.base import BaseHTTPMiddleware, RequestResponseEndpoint
from starlette.requests import Request
from starlette.responses import Response


class RequestIDMiddleware(BaseHTTPMiddleware):
    """Middleware that ensures every request has an ``X-Request-ID`` header.

    If the client sends one it is reused; otherwise a new UUID is generated.
    """

    async def dispatch(
        self,
        request: Request,
        call_next: RequestResponseEndpoint,
    ) -> Response:
        req_id = request.headers.get("X-Request-ID", str(uuid.uuid4()))
        response = await call_next(request)
        response.headers["X-Request-ID"] = req_id
        return response
