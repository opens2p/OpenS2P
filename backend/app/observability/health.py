"""
Enhanced health check endpoints.
"""
from __future__ import annotations
from app.core.config import settings


def get_health_info() -> dict:
    return {
        "status": "healthy",
        "service": settings.APP_NAME,
        "version": settings.APP_VERSION,
        "timestamp": __import__("datetime").datetime.utcnow().isoformat(),
    }


def get_health_details(db_ok: bool = True) -> dict:
    return {
        **get_health_info(),
        "checks": {
            "database": "ok" if db_ok else "error",
            "cache": "not_configured",
        },
        "uptime": None,  # Would track process start time
    }
