"""
OpenS2P Observability Package
==============================
Structured logging, metrics collection, health checks, and HTTP middleware.
"""

from app.observability.logging import get_logger, setup_logging
from app.observability.metrics import metrics, MetricsCollector
from app.observability.middleware import ObservabilityMiddleware
from app.observability.health import get_health_info, get_health_details

__all__ = [
    "get_logger",
    "setup_logging",
    "metrics",
    "MetricsCollector",
    "ObservabilityMiddleware",
    "get_health_info",
    "get_health_details",
]
