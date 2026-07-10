"""
Simple application metrics collector.
In production, replace with Prometheus client.
"""
from __future__ import annotations
import time
from collections import defaultdict
from typing import Any


class MetricsCollector:
    """In-memory metrics collector for request counts, durations, etc."""

    def __init__(self):
        self._counts: dict[str, int] = defaultdict(int)
        self._durations: dict[str, list[float]] = defaultdict(list)
        self._errors: dict[str, int] = defaultdict(int)

    def increment(self, metric: str, tags: dict[str, str] | None = None) -> None:
        key = metric
        if tags:
            tag_str = ",".join(f"{k}={v}" for k, v in sorted(tags.items()))
            key = f"{metric}[{tag_str}]"
        self._counts[key] += 1

    def record_duration(self, metric: str, duration_ms: float) -> None:
        self._durations[metric].append(duration_ms)

    def record_error(self, metric: str) -> None:
        self._errors[metric] += 1

    def snapshot(self) -> dict[str, Any]:
        result: dict[str, Any] = {}
        for k, v in self._counts.items():
            result[f"count_{k}"] = v
        for k, v in self._durations.items():
            if v:
                result[f"avg_duration_ms_{k}"] = round(sum(v) / len(v), 2)
                result[f"max_duration_ms_{k}"] = round(max(v), 2)
                result[f"total_calls_{k}"] = len(v)
        for k, v in self._errors.items():
            result[f"errors_{k}"] = v
        return result

    def reset(self) -> None:
        self._counts.clear()
        self._durations.clear()
        self._errors.clear()


metrics = MetricsCollector()
