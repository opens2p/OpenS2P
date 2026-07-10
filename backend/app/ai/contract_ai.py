"""
OpenS2P – Contract AI
======================
AI-powered contract review — clause risk, anomaly detection, and
renewal intelligence.
"""

from __future__ import annotations

import uuid
from datetime import date
from typing import Any

from app.models import Contract
from app.services.uow import UnitOfWork


class ContractAIService:
    """AI analysis for procurement contracts."""

    def __init__(self, uow: UnitOfWork) -> None:
        self.uow = uow

    async def review(self, contract_id: uuid.UUID) -> dict[str, Any]:
        """Analyse a contract for risk findings.

        Returns a list of ``findings`` with severity, category, and description.
        """
        contract = await self.uow.contracts.get(contract_id)
        if contract is None:
            return {"error": "Contract not found"}

        return self._analyse(contract)

    def _analyse(self, contract: Contract) -> dict[str, Any]:
        findings: list[dict[str, str]] = []

        # Auto-renewal risk
        if contract.end_date:
            days_left = (contract.end_date - date.today()).days
            if days_left < 30:
                findings.append({
                    "severity": "HIGH",
                    "category": "AUTO_RENEWAL",
                    "description": f"Contract expires in {days_left} days — auto-renewal may apply",
                })
            elif days_left < 90:
                findings.append({
                    "severity": "MEDIUM",
                    "category": "EXPIRY_WARNING",
                    "description": f"Contract expiring in {days_left} days — plan renewal",
                })

        # Missing start / end dates
        if contract.start_date is None:
            findings.append({
                "severity": "MEDIUM",
                "category": "INCOMPLETE",
                "description": "Contract has no start date",
            })
        if contract.end_date is None:
            findings.append({
                "severity": "LOW",
                "category": "INCOMPLETE",
                "description": "Contract has no end date — open-ended term",
            })

        # Value-based risk
        if contract.contract_value and contract.contract_value > 100_000:
            findings.append({
                "severity": "LOW",
                "category": "HIGH_VALUE",
                "description": f"High-value contract (${contract.contract_value:,.2f}) — ensure appropriate approvals",
            })

        return {
            "findings": findings,
            "finding_count": len(findings),
            "high_risk_count": sum(1 for f in findings if f["severity"] == "HIGH"),
        }

    async def suggest_renewal_terms(self, contract_id: uuid.UUID) -> dict[str, Any]:
        """Suggest revised terms for contract renewal."""
        contract = await self.uow.contracts.get(contract_id)
        if contract is None:
            return {"error": "Contract not found"}

        # Placeholder — would use LLM in production
        return {
            "suggested_term_months": 12,
            "suggested_price_adjustment": 3.5,  # percent
            "reasoning": "Based on market rates and historical spend trends",
        }

    async def analyze_risk(self, contract_id: uuid.UUID) -> dict[str, Any]:
        from app.ai.core.provider import AIProvider
        from app.ai.core.prompts import PROMPTS
        contract = await self.uow.contracts.get(contract_id)
        if not contract:
            return {"error": "Contract not found"}
        context = {"contract_number": contract.contract_number, "value": float(contract.contract_value or 0), "start": str(contract.start_date or ""), "end": str(contract.end_date or "")}
        provider = AIProvider()
        result = await provider.generate(PROMPTS["contract_risk"], str(context))
        return {**context, "ai_analysis": result.get("content", "{}")}

    async def summarize(self, contract_id: uuid.UUID) -> dict[str, Any]:
        from app.ai.core.provider import AIProvider
        from app.ai.core.prompts import PROMPTS
        contract = await self.uow.contracts.get(contract_id)
        if not contract:
            return {"error": "Contract not found"}
        context = {"contract_number": contract.contract_number, "value": float(contract.contract_value or 0), "supplier_id": str(contract.supplier_id)}
        provider = AIProvider()
        result = await provider.generate(PROMPTS["contract_summary"], str(context))
        return {"summary": result.get("content", "{}")}
