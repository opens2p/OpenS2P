"""
OpenS2P – Auth tests
=====================
"""

from __future__ import annotations

import pytest
from httpx import AsyncClient, ASGITransport

from app.main import app

pytestmark = pytest.mark.asyncio


class TestAuth:
    """Authentication endpoint tests (no DB fixtures needed)."""

    async def test_health(self):
        """Admin health check with auth."""
        from app.security.jwt import create_access_token
        admin_token = create_access_token(
            sub="00000000-0000-0000-0000-000000000000",
            tenant_id="00000000-0000-0000-0000-000000000000",
            roles=["SYSTEM_ADMIN"],
        )
        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            resp = await client.get(
                "/api/v1/admin/health",
                headers={"Authorization": f"Bearer {admin_token}"},
            )
            assert resp.status_code == 200
            data = resp.json()
            assert data["status"] == "healthy"

    async def test_login_invalid(self):
        """Login with bad credentials should return 401."""
        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            resp = await client.post(
                "/api/v1/auth/login?username=nobody&password=doesntmatter",
            )
            assert resp.status_code == 401

    @pytest.mark.skip(reason="Needs isolated test DB session (asyncpg connection pooling quirk)")
    async def test_protected_no_token(self):
        """Protected routes should reject unauthenticated requests."""
        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            resp = await client.get("/api/v1/suppliers")
            assert resp.status_code == 401

    @pytest.mark.skip(reason="Needs isolated test DB session (asyncpg connection pooling quirk)")
    async def test_protected_admin_no_token(self):
        """Admin/stats should reject unauthenticated requests."""
        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            resp = await client.get("/api/v1/admin/stats")
            assert resp.status_code == 401
