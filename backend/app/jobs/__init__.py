"""
OpenS2P Background Jobs Package
=================================
Simple in-process task definitions and scheduler.
In production, replace with Celery/Arq + Redis.
"""

from app.jobs.tasks import register_task, get_task, sync_erp, refresh_analytics, check_expiring_contracts, update_supplier_risk
from app.jobs.scheduler import schedule, run_scheduler

__all__ = [
    "register_task",
    "get_task",
    "sync_erp",
    "refresh_analytics",
    "check_expiring_contracts",
    "update_supplier_risk",
    "schedule",
    "run_scheduler",
]
