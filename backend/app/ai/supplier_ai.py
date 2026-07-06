"""
OpenS2P – Supplier AI
======================
AI-powered supplier intelligence — risk scoring, recommendations,
and anomaly detection.

Current implementation uses rule-based heuristics as placeholders.
In production these would call LLM or ML model endpoints.
"""

from __future__ import annotations

import uuid
from decimal import Decimal
from typing import Any

from app.models import Supplier
from app.services.uow import UnitOfWork


class SupplierAIService:
    """AI analysis for supplier profiles."""

    def __init__(self, uow: UnitOfWork) -> None:
        self.uow = uow

    async def analyze_risk(self, supplier_id: uuid.UUID) -> dict[str, Any]:
        """Analyse supplier risk and return a score with rationale.

        Returns:
            ``risk_score`` (0-100), ``risk_level``, ``factors``, ``recommendation``.
        """
        supplier = await self.uow.suppliers.get(supplier_id)
        if supplier is None:
            return {"error": "Supplier not found"}

        return self._assess(supplier)

    def _assess(self, supplier: Supplier) -> dict[str, Any]:
        """Heuristic risk assessment — swap with ML model later."""
        score = float(supplier.risk_score or 0)
        factors: list[str] = []

        if score == 0:
            score = 25.0
            factors.append("No historical risk data available")

        if supplier.status == "DRAFT":
            score = min(score + 15, 100)
            factors.append("Supplier not yet approved")

        if score < 30:
            level = "LOW"
            recommendation = "Low risk — standard onboarding"
        elif score < 60:
            level = "MEDIUM"
            recommendation = "Medium risk — additional due diligence recommended"
        else:
            level = "HIGH"
            recommendation = "High risk — require enhanced monitoring and frequent reviews"

        return {
            "risk_score": round(score, 1),
            "risk_level": level,
            "factors": factors,
            "recommendation": recommendation,
        }

    async def recommend_category(self, supplier_id: uuid.UUID) -> list[dict[str, Any]]:
        """Suggest procurement categories for a supplier based on profile."""
        supplier = await self.uow.suppliers.get(supplier_id)
        if supplier is None:
            return []
        # Placeholder — would use embedding similarity in production
        return [
            {"category": "Industrial Supplies", "confidence": 0.85},
            {"category": "MRO Parts", "confidence": 0.72},
            {"category": "Safety Equipment", "confidence": 0.68},
        ]
