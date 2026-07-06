"""
OpenS2P – Security Dependencies
=================================
FastAPI dependency-injection functions for authentication & authorisation.

Usage::

    @router.get("/suppliers")
    async def list_suppliers(
        current_user: AuthContext = Depends(require_auth),
        uow: UnitOfWork = Depends(get_unit_of_work),
    ):
        ...

    @router.post("/suppliers/{id}/approve")
    async def approve_supplier(
        current_user: AuthContext = Depends(require_permission(PERM.SUPPLIER_APPROVE)),
        ...
    ):
        ...
"""

from __future__ import annotations

import uuid
from dataclasses import dataclass
from typing import Any

from typing import Any

from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer

from app.security.jwt import decode_access_token
from app.security.permissions import has_permission

_bearer_scheme = HTTPBearer(auto_error=False)


@dataclass
class AuthContext:
    """Authenticated user context extracted from the JWT."""

    user_id: uuid.UUID
    tenant_id: uuid.UUID
    roles: list[str]
    token_payload: dict[str, Any]


async def require_auth(
    credentials: Any = Depends(_bearer_scheme),
) -> AuthContext:
    """Dependency: verify the Bearer token and return the authenticated context.

    Raises HTTP 401 if the token is missing, expired, or invalid.
    """
    if credentials is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authentication required",
            headers={"WWW-Authenticate": "Bearer"},
        )

    try:
        token_str = credentials.credentials if hasattr(credentials, "credentials") else credentials
        payload = decode_access_token(token_str)
    except Exception as exc:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired token",
        ) from exc

    user_id = uuid.UUID(payload["sub"])
    tenant_id = uuid.UUID(payload.get("tenant_id", ""))
    roles: list[str] = payload.get("roles", [])

    return AuthContext(
        user_id=user_id,
        tenant_id=tenant_id,
        roles=roles,
        token_payload=payload,
    )


def require_permission(permission: str):
    """Dependency factory: require a specific permission.

    Usage::

        @router.post("/suppliers/{id}/approve")
        async def approve_supplier(
            _: AuthContext = Depends(require_permission("supplier.approve")),
            ...
        ):
            ...
    """

    async def _check(auth: AuthContext = Depends(require_auth)) -> None:
        if not has_permission(permission, auth.roles):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Missing permission: {permission}",
            )

    return _check


async def optional_auth(
    credentials: Any = Depends(_bearer_scheme),
) -> AuthContext | None:
    """Like ``require_auth`` but returns ``None`` instead of raising 401.

    Use this in endpoints that work differently for authenticated vs
    anonymous users (e.g. login, public status pages).
    """
    if credentials is None:
        return None
    try:
        token_str = credentials.credentials if hasattr(credentials, "credentials") else credentials
        payload = decode_access_token(token_str)
        return AuthContext(
            user_id=uuid.UUID(payload["sub"]),
            tenant_id=uuid.UUID(payload.get("tenant_id", "")),
            roles=payload.get("roles", []),
            token_payload=payload,
        )
    except Exception:
        return None
