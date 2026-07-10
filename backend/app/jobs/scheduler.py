"""
Simple in-process task scheduler.
In production, replace with Celery Beat or APScheduler.
"""
from __future__ import annotations
import asyncio
from datetime import datetime, timezone
from app.jobs.tasks import get_task
from app.observability.logging import get_logger

logger = get_logger("opens2p.scheduler")

_scheduled_tasks: list[dict] = []


def schedule(task_name: str, interval_seconds: int, params: dict | None = None):
    """Schedule a task to run periodically."""
    _scheduled_tasks.append({
        "task_name": task_name,
        "interval": interval_seconds,
        "params": params or {},
        "last_run": None,
    })
    logger.info(f"Scheduled task '{task_name}' every {interval_seconds}s")


async def run_scheduler():
    """Main scheduler loop — runs registered tasks at their intervals."""
    logger.info("Scheduler started")
    while True:
        now = datetime.now(timezone.utc)
        for task_def in _scheduled_tasks:
            if task_def["last_run"] is None or \
               (now - task_def["last_run"]).total_seconds() >= task_def["interval"]:
                task_fn = get_task(task_def["task_name"])
                if task_fn:
                    try:
                        await task_fn(**task_def["params"])
                    except Exception as e:
                        logger.error(f"Task {task_def['task_name']} failed: {e}")
                task_def["last_run"] = now
        await asyncio.sleep(10)  # Check every 10 seconds
