"""
OpenS2P – Invoice AI
=====================
AI-powered invoice analysis — duplicate detection, price variance,
3-way match context, and autonomous exception resolution.
"""

from __future__ import annotations

import uuid
from typing import Any

from app.ai.core.prompts import EXCEPTION_RESOLVE
from app.ai.core.provider import AIProvider
from app.models import MatchStatus
from app.services.invoice_service import InvoiceMatchError, InvoiceService
from app.services.uow import UnitOfWork


class InvoiceAIService:
    """AI analysis for supplier invoices."""

    def __init__(self, uow: UnitOfWork, actor_id: uuid.UUID | None = None) -> None:
        self.uow = uow
        self.actor_id = actor_id
        self.provider = AIProvider()

    async def detect_anomalies(self, invoice_id: uuid.UUID) -> dict[str, Any]:
        invoice = await self.uow.invoices.get(invoice_id)
        if not invoice:
            return {"error": "Invoice not found"}
        po = await self.uow.purchase_orders.get_with_items(invoice.po_id) if invoice.po_id else None
        anomalies = []
        if po and invoice.amount and po.items:
            po_total = sum((item.price or 0) * (item.quantity or 0) for item in po.items)
            if invoice.amount > po_total * Decimal_safe("1.1"):
                anomalies.append(
                    f"Invoice amount ${float(invoice.amount):.2f} exceeds "
                    f"PO total ${float(po_total):.2f} by >10%"
                )
        return {
            "invoice_id": str(invoice_id),
            "anomalies": anomalies,
            "risk": "HIGH" if anomalies else "LOW",
        }

    async def analyze(self, invoice_id: uuid.UUID) -> dict[str, Any]:
        """Analyse an invoice for anomalies, duplicates, and fraud signals."""
        invoice = await self.uow.invoices.get(invoice_id)
        if invoice is None:
            return {"error": "Invoice not found"}

        signals: list[dict[str, Any]] = []

        duplicates = await self.uow.invoices.find_duplicates(invoice)
        if duplicates:
            signals.append({
                "type": "DUPLICATE",
                "severity": "HIGH",
                "message": f"Potential duplicate — {len(duplicates)} invoice(s) with same number and amount",
            })

        if invoice.amount and invoice.amount > 10_000:
            signals.append({
                "type": "HIGH_VALUE",
                "severity": "LOW",
                "message": f"High-value invoice (${invoice.amount:,.2f}) — verify approval",
            })

        if invoice.match_status and invoice.match_status.value == "EXCEPTION":
            signals.append({
                "type": "MATCH_EXCEPTION",
                "severity": "HIGH",
                "message": "Invoice has a matching exception requiring review",
            })

        return {
            "signals": signals,
            "anomaly_count": len(signals),
            "high_risk_count": sum(1 for s in signals if s["severity"] == "HIGH"),
            "recommendation": "Review flagged items" if signals else "No anomalies detected — approve",
        }

    async def build_match_context(self, invoice_id: uuid.UUID) -> dict[str, Any]:
        """PO / Invoice / GRN figures for the Matching workspace and agent."""
        svc = InvoiceService(self.uow, actor_id=self.actor_id)
        invoice = await self.uow.invoices.get(invoice_id)
        if invoice is None:
            return {"error": "Invoice not found"}
        try:
            result = await svc.evaluate_match(invoice_id)
        except InvoiceMatchError as exc:
            return {"error": str(exc)}
        extras = invoice.extras or {}
        return {
            "invoice": {
                "id": str(invoice.id),
                "invoice_number": invoice.invoice_number,
                "amount": float(invoice.amount) if invoice.amount is not None else 0,
                "match_status": invoice.match_status.value if invoice.match_status else None,
                "extras": extras,
            },
            "match": result,
            "stored_match_result": extras.get("match_result"),
        }

    async def suggest_resolution(self, invoice_id: uuid.UUID) -> dict[str, Any]:
        """Rule decision + explanation for an EXCEPTION (or pending match)."""
        invoice = await self.uow.invoices.get(invoice_id)
        if invoice is None:
            return {"error": "Invoice not found"}

        svc = InvoiceService(self.uow, actor_id=self.actor_id)
        match = await svc.evaluate_match(invoice_id)
        extras = invoice.extras or {}
        prior = extras.get("match_result") or match
        primary = prior.get("primary_issue") or match.get("primary_issue")
        issues = match.get("issues") or prior.get("issues") or []

        if match.get("passed"):
            action = "re_match"
            explanation = (
                "Documents now reconcile. Re-run match or Auto-Resolve to clear the exception."
            )
        elif primary == "MISSING_GRN" or any(i.get("code") == "MISSING_GRN" for i in issues):
            action = "await_grn"
            explanation = (
                "No goods receipt is recorded for this PO. Receive goods first, "
                "then Auto-Resolve will clear the exception."
            )
        elif primary == "PRICE_VARIANCE" or any(i.get("code") == "PRICE_VARIANCE" for i in issues):
            variance = abs(float(match.get("amount_variance") or 0))
            auto_tol = float(match.get("auto_resolve_tolerance") or 0)
            if variance <= auto_tol:
                action = "auto_match_tolerance"
                explanation = (
                    f"Price variance ${variance:.2f} is within autonomous tolerance "
                    f"${auto_tol:.2f}. The agent can auto-approve this mismatch."
                )
            else:
                action = "escalate"
                explanation = (
                    f"Price variance ${variance:.2f} exceeds autonomous tolerance "
                    f"${auto_tol:.2f}. Escalate for human AP review."
                )
        elif any(i.get("code") == "QTY_VARIANCE" for i in issues):
            action = "escalate"
            explanation = "Received quantity is short of ordered quantity. Escalate for receiving review."
        else:
            action = "escalate"
            explanation = issues[0]["message"] if issues else "Unable to auto-resolve — escalate."

        # Optional LLM polish
        llm_note = None
        try:
            user_prompt = (
                f"Invoice {invoice.invoice_number}: status={invoice.match_status}, "
                f"issues={issues}, suggested_action={action}. "
                f"Write one short sentence explaining the resolution path."
            )
            ai = await self.provider.generate(EXCEPTION_RESOLVE, user_prompt)
            content = ai.get("content") or ""
            if ai.get("model") != "heuristic" and content and not content.startswith("AI error"):
                llm_note = content.strip()
            elif "exception" in user_prompt.lower() or action:
                llm_note = explanation
        except Exception:
            llm_note = explanation

        return {
            "invoice_id": str(invoice_id),
            "match_status": invoice.match_status.value if invoice.match_status else None,
            "action": action,
            "can_auto_resolve": action in {"auto_match_tolerance", "re_match"},
            "explanation": llm_note or explanation,
            "resolution_brief": self._build_resolution_brief(
                action=action,
                can_auto_resolve=action in {"auto_match_tolerance", "re_match"},
                match=match,
                issues=issues,
            ),
            "match": match,
        }

    def _build_resolution_brief(
        self,
        *,
        action: str,
        can_auto_resolve: bool,
        match: dict[str, Any],
        issues: list[dict[str, Any]],
    ) -> dict[str, str]:
        """Create a demo-friendly AP resolution brief from match evidence."""
        po_total = float(match.get("po_total") or 0)
        invoice_amount = float(match.get("invoice_amount") or 0)
        variance = invoice_amount - po_total
        abs_variance = abs(variance)
        auto_tolerance = float(match.get("auto_resolve_tolerance") or 0)
        primary_issue = match.get("primary_issue")

        if not match.get("has_po"):
            what_happened = "Invoice is not linked to a purchase order."
        elif primary_issue == "MISSING_GRN" or any(i.get("code") == "MISSING_GRN" for i in issues):
            what_happened = "Invoice has no matching goods receipt."
        elif abs_variance > 0:
            direction = "exceeds" if variance > 0 else "is below"
            what_happened = f"Invoice {direction} PO by ${abs_variance:,.2f}."
        else:
            what_happened = "PO, invoice, and goods receipt reconcile."

        if action == "auto_match_tolerance":
            why_it_matters = (
                f"Variance is within autonomous tolerance (${auto_tolerance:,.2f})."
            )
            recommended_action = "Auto-resolve and mark ready for payment."
        elif action == "re_match":
            why_it_matters = "Documents now reconcile after updated match evidence."
            recommended_action = "Re-run match and mark ready for payment."
        elif action == "await_grn":
            why_it_matters = "A 3-way match cannot complete until receipt evidence exists."
            recommended_action = "Record goods receipt, then retry auto-resolution."
        elif action == "escalate":
            why_it_matters = (
                f"Variance exceeds autonomous tolerance (${auto_tolerance:,.2f})."
                if primary_issue == "PRICE_VARIANCE"
                else "The exception falls outside autonomous resolution policy."
            )
            recommended_action = "Escalate to AP for human review."
        else:
            why_it_matters = "The agent needs policy evidence before taking action."
            recommended_action = "Review exception details."

        return {
            "what_happened": what_happened,
            "why_it_matters": why_it_matters,
            "recommended_action": recommended_action,
            "policy_boundary": (
                "Auto-resolve only within tolerance; escalate if variance exceeds "
                "tolerance or GRN is missing."
            ),
            "audit_note": (
                "AI action recorded with reason and match evidence."
                if can_auto_resolve
                else "AI recommendation recorded with reason and match evidence."
            ),
        }

    async def auto_resolve(self, invoice_id: uuid.UUID) -> dict[str, Any]:
        """Apply autonomous resolution when rules allow."""
        suggestion = await self.suggest_resolution(invoice_id)
        if suggestion.get("error"):
            return suggestion

        action = suggestion.get("action")
        if action not in {"auto_match_tolerance", "re_match"}:
            return {
                "success": False,
                "action": action,
                "explanation": suggestion.get("explanation"),
                "error": suggestion.get("explanation") or "Cannot auto-resolve this exception",
            }

        svc = InvoiceService(self.uow, actor_id=self.actor_id)
        try:
            invoice = await svc.resolve_exception(
                invoice_id,
                mode="auto",
                note=suggestion.get("explanation"),
            )
        except InvoiceMatchError as exc:
            return {
                "success": False,
                "action": action,
                "explanation": suggestion.get("explanation"),
                "error": str(exc),
            }

        return {
            "success": True,
            "action": action,
            "explanation": suggestion.get("explanation"),
            "invoice_id": str(invoice.id),
            "match_status": invoice.match_status.value if invoice.match_status else None,
            "extras": invoice.extras,
        }


def Decimal_safe(value: float):
    from decimal import Decimal
    return Decimal(str(value))
