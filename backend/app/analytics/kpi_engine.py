"""
Reusable KPI calculation framework.
"""
from __future__ import annotations
from decimal import Decimal
from typing import Any, Callable, Awaitable

KPICalculator = Callable[..., Awaitable[Decimal]]

_kpi_registry: dict[str, KPICalculator] = {}


def register_kpi(name: str, calculator: KPICalculator) -> None:
    _kpi_registry[name] = calculator


def get_kpi_calculator(name: str) -> KPICalculator | None:
    return _kpi_registry.get(name)


def list_kpis() -> list[str]:
    return list(_kpi_registry.keys())


def calculate_trend(current: Decimal, previous: Decimal | None) -> dict[str, Any]:
    if previous is None or previous == 0:
        return {"direction": "flat", "change_percent": 0}
    change = current - previous
    change_pct = (change / previous) * 100
    direction = "up" if change > 0 else "down" if change < 0 else "flat"
    return {"direction": direction, "change": float(change), "change_percent": float(change_pct)}
