"""
OpenS2P – AI Service
=====================
Placeholder for ML-powered intelligence features.

Future capabilities (post-MVP):
* Smart supplier recommendations based on category & past performance
* Anomaly detection in invoice amounts
* Risk prediction for new suppliers
* PO amount forecasting
* Contract clause similarity search
* Automated invoice matching using NLP
"""

from __future__ import annotations

import uuid
from decimal import Decimal
from typing import Any

from app.models import AIRecommendation
from app.services.uow import UnitOfWork


class AIService:
    """AI/ML recommendation service.

    Currently a placeholder — all methods return mock data until ML
    models are deployed.
    """

    def __init__(self, uow: UnitOfWork) -> None:
        self.uow = uow

    async def recommend_suppliers(
        self,
        category: str,
        *,
        max_results: int = 5,
    ) -> list[dict[str, Any]]:
        """Suggest suppliers for a given procurement category.

        TODO: replace with embedding-based similarity search.
        """
        _ = category  # placeholder
        return []

    async def detect_anomaly(
        self,
        entity_type: str,
        entity_id: uuid.UUID,
    ) -> dict[str, Any]:
        """Score a transaction for fraud / anomaly risk.

        Returns a dict with ``score`` and ``reason`` keys.
        """
        _ = entity_type, entity_id
        return {"score": 0.0, "reason": "No anomaly detected", "anomaly": False}

    async def save_recommendation(
        self,
        *,
        object_type: str,
        object_id: uuid.UUID,
        recommendation: dict[str, Any],
        confidence: Decimal | None = None,
    ) -> AIRecommendation:
        """Persist an AI recommendation for auditability."""
        return await self.uow.uow.ai.create({
            "object_type": object_type,
            "object_id": object_id,
            "recommendation": recommendation,
            "confidence": confidence,
        })
