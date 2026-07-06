"""
OpenS2P – JWT token handling
==============================
Issues and validates RS256 / HS256 access tokens.
"""

from __future__ import annotations

import os
import uuid
from datetime import datetime, timedelta, timezone
from typing import Any

from jose import JWTError, jwt

# ── configuration (override via env) ───────────────────────────────────────

SECRET_KEY: str = os.getenv(
    "JWT_SECRET_KEY",
    "opens2p-dev-secret-key-do-not-use-in-production",
)
ALGORITHM: str = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES: int = int(os.getenv("JWT_EXPIRE_MINUTES", "60"))


def create_access_token(
    *,
    sub: str,
    tenant_id: str | None = None,
    roles: list[str] | None = None,
    extra_claims: dict[str, Any] | None = None,
) -> str:
    """Issue a signed JWT access token.

    Args:
        sub:       User UUID (the ``sub`` claim).
        tenant_id: Tenant UUID (included as ``tenant_id`` claim).
        roles:     List of role names (included as ``roles`` claim).
        extra_claims: Additional claims to merge into the payload.

    Returns:
        Encoded JWT string.
    """
    now = datetime.now(timezone.utc)
    payload: dict[str, Any] = {
        "sub": sub,
        "iat": now,
        "exp": now + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES),
        "type": "access",
    }
    if tenant_id is not None:
        payload["tenant_id"] = tenant_id
    if roles is not None:
        payload["roles"] = roles
    if extra_claims:
        payload.update(extra_claims)

    return jwt.encode(payload, SECRET_KEY, algorithm=ALGORITHM)


def decode_access_token(token: str) -> dict[str, Any]:
    """Validate and decode an access token.

    Returns:
        The decoded payload dict.

    Raises:
        JWTError: If the token is expired, malformed, or signature is invalid.
    """
    return jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
