"""
OpenS2P – Event Architecture
==============================
In-process event bus for domain events.
"""

from .event_bus import publish, subscribe, unsubscribe, clear_handlers
from . import schemas

__all__ = [
    "publish",
    "subscribe",
    "unsubscribe",
    "clear_handlers",
    "schemas",
]
