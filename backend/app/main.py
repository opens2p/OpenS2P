"""
OpenS2P – FastAPI Application
==============================
Entry point for the OpenS2P Source-to-Pay platform.

Run with::

    uvicorn app.main:app --reload --port 8000

Or::

    python -m app.main
"""

from __future__ import annotations

from contextlib import asynccontextmanager
from typing import AsyncIterator

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.v1.router import router as v1_router
from app.db.session import get_engine
from app.middleware.request_id import RequestIDMiddleware


@asynccontextmanager
async def lifespan(_app: FastAPI) -> AsyncIterator[None]:
    """Application lifespan — startup / shutdown hooks."""
    # startup: verify DB connectivity
    engine = get_engine()
    try:
        async with engine.connect() as conn:
            await conn.execute(
                __import__("sqlalchemy").text("SELECT 1"),
            )
        print("✅ Database connection OK")
    except Exception as exc:
        print(f"⚠️  Database not reachable: {exc}")
    yield
    # shutdown: dispose engine
    await engine.dispose()


app = FastAPI(
    title="OpenS2P API",
    description="Enterprise Source-to-Contract & Source-to-Pay Platform",
    version="0.1.0",
    lifespan=lifespan,
    docs_url="/docs",
    redoc_url="/redoc",
    openapi_tags=[
        {"name": "Authentication", "description": "Login, register, token management"},
        {"name": "Supplier Management", "description": "Supplier lifecycle & onboarding"},
        {"name": "Contract Management", "description": "Contract lifecycle & renewals"},
        {"name": "Sourcing", "description": "RFQ/RFP events and bidding"},
        {"name": "Procurement", "description": "Purchase Requisitions & Orders"},
        {"name": "Invoice Management", "description": "Invoice matching & payment"},
        {"name": "Workflow", "description": "Approval workflows & task management"},
        {"name": "Audit", "description": "Immutable change history & timeline"},
        {"name": "AI Intelligence", "description": "AI-powered supplier, contract & invoice analysis"},
        {"name": "Administration", "description": "Health check, stats, admin ops"},
    ],
)

# ── middleware ─────────────────────────────────────────────────────────────

app.add_middleware(RequestIDMiddleware)

# ── middleware ─────────────────────────────────────────────────────────────

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ── routers ───────────────────────────────────────────────────────────────

app.include_router(v1_router)


@app.get("/")
async def root():
    return {
        "service": "OpenS2P API",
        "version": "0.1.0",
        "docs": "/docs",
        "redoc": "/redoc",
    }


# ── CLI entry point ───────────────────────────────────────────────────────

if __name__ == "__main__":
    import uvicorn

    uvicorn.run("app.main:app", host="0.0.0.0", port=8000, reload=True)
