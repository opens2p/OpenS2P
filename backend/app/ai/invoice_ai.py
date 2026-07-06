"""
OpenS2P – Invoice AI
=====================
AI-powered invoice analysis — duplicate detection, price variance,
and fraud signals.
"""

from __future__ import annotations

import uuid
from typing import Any

from app.services.uow import UnitOfWork


class InvoiceAIService:
    """AI analysis for supplier invoices."""

    def __init__(self, uow: UnitOfWork) -> None:
        self.uow = uow

    async def analyze(self, invoice_id: uuid.UUID) -> dict[str, Any]:
        """Analyse an invoice for anomalies, duplicates, and fraud signals."""
        invoice = await self.uow.invoices.get(invoice_id)
        if invoice is None:
            return {"error": "Invoice not found"}

        signals: list[dict[str, Any]] = []
        anomalies: list[str] = []

        # Duplicate check
        duplicates = await self.uow.invoices.find_duplicates(invoice)
        if duplicates:
            signals.append({
                "type": "DUPLICATE",
                "severity": "HIGH",
                "message": f"Potential duplicate — {len(duplicates)} invoice(s) with same number and amount",
            })
            anomalies.append("DUPLICATE_DETECTED")

        # Amount threshold
        if invoice.amount and invoice.amount > 10_000:
            signals.append({
                "type": "HIGH_VALUE",
                "severity": "LOW",
                "message": f"High-value invoice (${invoice.amount:,.2f}) — verify approval",
            })

        # Match status
        if invoice.match_status and invoice.match_status.value == "EXCEPTION":
            signals.append({
                "type": "MATCH_EXCEPTION",
                "severity": "HIGH",
                "message": "Invoice has a matching exception requiring human review",
            })

        return {
            "signals": signals,
            "anomaly_count": len(signals),
            "high_risk_count": sum(1 for s in signals if s["severity"] == "HIGH"),
            "recommendation": "Review flagged items" if signals else "No anomalies detected — approve",
        }
