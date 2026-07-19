"""
OpenS2P – Invoice Service
===========================
"""

from __future__ import annotations

import uuid
from datetime import date, datetime
from decimal import Decimal
from typing import Any

from app.models import Invoice, MatchStatus
from app.services.uow import UnitOfWork

# Match: amount OK if variance ≤ max(2% of PO, $50)
# Auto-resolve: can clear PRICE_VARIANCE if variance ≤ max(5% of PO, $100)
MATCH_PCT = Decimal("0.02")
MATCH_ABS = Decimal("50")
AUTO_RESOLVE_PCT = Decimal("0.05")
AUTO_RESOLVE_ABS = Decimal("100")
QTY_TOLERANCE_PCT = Decimal("0.02")


class InvoiceMatchError(Exception):
    """Business-rule violation during invoice matching / resolve."""


def _serialize(value: Any) -> Any:
    """Convert a value to a JSON-safe representation."""
    if isinstance(value, (uuid.UUID, Decimal, date, datetime)):
        return str(value)
    if isinstance(value, dict):
        return {k: _serialize(v) for k, v in value.items()}
    if isinstance(value, list):
        return [_serialize(v) for v in value]
    return value


def _serialize_dict(d: dict[str, Any]) -> dict[str, Any]:
    """Deep-convert a dict's values to JSON-safe types."""
    return {k: _serialize(v) for k, v in d.items()}


def _money(value: Any) -> Decimal:
    if value is None:
        return Decimal("0")
    return Decimal(str(value))


def _amount_tolerance(po_total: Decimal, pct: Decimal, absolute: Decimal) -> Decimal:
    return max(po_total * pct, absolute)


class InvoiceService:
    """Invoice lifecycle and matching operations."""

    def __init__(self, uow: UnitOfWork, actor_id: uuid.UUID | None = None) -> None:
        self.uow = uow
        self.actor_id = actor_id

    async def submit_invoice(self, data: dict[str, Any]) -> Invoice:
        """Record a new invoice from a supplier."""
        if not data.get("invoice_number"):
            from app.services.numbering import next_document_number
            from app.models.invoice import Invoice as InvoiceModel
            data["invoice_number"] = await next_document_number(
                self.uow.session, InvoiceModel, "invoice_number", "INV",
            )
        invoice = await self.uow.invoices.create(data)
        await self.uow.audit.log(
            tenant_id=self.uow.tenant_id,
            entity_type="invoice",
            entity_id=invoice.id,
            event_type="INVOICE_SUBMITTED",
            new_values=_serialize_dict(data),
            created_by=self.actor_id,
        )
        return invoice

    async def _compute_match_context(
        self,
        invoice: Invoice,
    ) -> dict[str, Any]:
        """Build PO / invoice / GRN figures used by matching and the AI agent."""
        po = None
        if invoice.po_id:
            po = await self.uow.purchase_orders.get_with_items(invoice.po_id)

        receipts = []
        if invoice.po_id:
            receipts = await self.uow.receipts.list_by_po(invoice.po_id)

        po_total = Decimal("0")
        qty_ordered = Decimal("0")
        if po and po.items:
            for item in po.items:
                qty = _money(item.quantity)
                price = _money(item.price)
                po_total += qty * price
                qty_ordered += qty

        qty_received = Decimal("0")
        amount_received = Decimal("0")
        receipt_ids: list[str] = []
        for r in receipts:
            qty_received += _money(getattr(r, "quantity_received", None))
            amount_received += _money(getattr(r, "amount_received", None))
            receipt_ids.append(str(r.id))

        invoice_amount = _money(invoice.amount)
        amount_variance = invoice_amount - po_total
        amount_tolerance = _amount_tolerance(po_total, MATCH_PCT, MATCH_ABS)
        auto_tolerance = _amount_tolerance(po_total, AUTO_RESOLVE_PCT, AUTO_RESOLVE_ABS)

        return {
            "invoice_id": str(invoice.id),
            "invoice_number": invoice.invoice_number,
            "invoice_amount": float(invoice_amount),
            "po_id": str(invoice.po_id) if invoice.po_id else None,
            "po_number": getattr(po, "po_number", None) if po else None,
            "po_total": float(po_total),
            "qty_ordered": float(qty_ordered),
            "qty_received": float(qty_received),
            "amount_received": float(amount_received),
            "receipt_ids": receipt_ids,
            "receipt_count": len(receipts),
            "amount_variance": float(amount_variance),
            "amount_tolerance": float(amount_tolerance),
            "auto_resolve_tolerance": float(auto_tolerance),
            "has_po": po is not None,
            "has_receipt": len(receipts) > 0,
        }

    async def evaluate_match(
        self,
        invoice_id: uuid.UUID,
        *,
        amount_tolerance_override: Decimal | None = None,
    ) -> dict[str, Any]:
        """Evaluate 2/3-way match without mutating status. Returns match_result dict."""
        invoice = await self.uow.invoices.get(invoice_id)
        if invoice is None:
            raise InvoiceMatchError("Invoice not found")

        ctx = await self._compute_match_context(invoice)
        issues: list[dict[str, Any]] = []

        if not ctx["has_po"]:
            issues.append({
                "code": "MISSING_PO",
                "message": "Invoice is not linked to a purchase order",
            })
        elif not ctx["has_receipt"]:
            issues.append({
                "code": "MISSING_GRN",
                "message": "No goods receipt found for the purchase order",
            })
        else:
            po_total = _money(ctx["po_total"])
            invoice_amount = _money(ctx["invoice_amount"])
            variance = abs(invoice_amount - po_total)
            tolerance = amount_tolerance_override or _money(ctx["amount_tolerance"])
            if variance > tolerance:
                issues.append({
                    "code": "PRICE_VARIANCE",
                    "message": (
                        f"Invoice amount ${float(invoice_amount):.2f} differs from "
                        f"PO total ${float(po_total):.2f} by ${float(variance):.2f} "
                        f"(tolerance ${float(tolerance):.2f})"
                    ),
                    "variance": float(variance),
                    "tolerance": float(tolerance),
                })

            qty_ordered = _money(ctx["qty_ordered"])
            qty_received = _money(ctx["qty_received"])
            if qty_ordered > 0:
                # If receipts exist but quantity_received was never set, treat
                # completed receipts as full receipt of ordered qty for demo.
                if qty_received == 0 and ctx["receipt_count"] > 0:
                    qty_received = qty_ordered
                    ctx["qty_received"] = float(qty_received)
                min_required = qty_ordered * (Decimal("1") - QTY_TOLERANCE_PCT)
                if qty_received < min_required:
                    issues.append({
                        "code": "QTY_VARIANCE",
                        "message": (
                            f"Received qty {float(qty_received):.2f} is below "
                            f"ordered qty {float(qty_ordered):.2f}"
                        ),
                        "qty_ordered": float(qty_ordered),
                        "qty_received": float(qty_received),
                    })

        if issues:
            primary = issues[0]["code"]
            status = MatchStatus.EXCEPTION.value
            match_type = "EXCEPTION"
        else:
            primary = None
            status = MatchStatus.MATCHED.value
            match_type = "THREE_WAY" if ctx["has_receipt"] else "TWO_WAY"

        return {
            **ctx,
            "match_type": match_type,
            "status": status,
            "primary_issue": primary,
            "issues": issues,
            "passed": len(issues) == 0,
            "evaluated_at": datetime.utcnow().isoformat() + "Z",
        }

    async def _persist_match_result(
        self,
        invoice_id: uuid.UUID,
        match_result: dict[str, Any],
    ) -> Invoice | None:
        invoice = await self.uow.invoices.get(invoice_id)
        if invoice is None:
            return None
        extras = dict(invoice.extras or {})
        extras["match_result"] = _serialize_dict(match_result)
        return await self.uow.invoices.update(invoice_id, {"extras": extras})

    async def _mark_ready_for_payment(self, invoice_id: uuid.UUID) -> Invoice | None:
        """Mark a matched invoice as ready for the payment queue."""
        invoice = await self.uow.invoices.get(invoice_id)
        if invoice is None:
            return None
        extras = dict(invoice.extras or {})
        if extras.get("payment_status") == "SENT_TO_PAYMENT":
            return invoice
        extras["payment_status"] = "READY"
        extras["payment_ready"] = True
        return await self.uow.invoices.update(invoice_id, {"extras": extras})

    async def perform_matching(self, invoice_id: uuid.UUID) -> Invoice | None:
        """Execute 2-way and 3-way matching logic.

        2-way match:  invoice amount  vs  PO amount
        3-way match:  invoice amount  vs  PO amount AND receipt quantity
        """
        invoice = await self.uow.invoices.get(invoice_id)
        if invoice is None:
            return None

        old_status = invoice.match_status
        match_result = await self.evaluate_match(invoice_id)
        await self._persist_match_result(invoice_id, match_result)

        if match_result["passed"]:
            updated = await self.uow.invoices.update_match_status(
                invoice_id, MatchStatus.MATCHED,
            )
            updated = await self._mark_ready_for_payment(invoice_id) or updated
            await self.uow.audit.log(
                tenant_id=self.uow.tenant_id,
                entity_type="invoice",
                entity_id=invoice_id,
                event_type="INVOICE_MATCHED",
                old_values={"match_status": _status_value(old_status)},
                new_values={
                    "match_status": MatchStatus.MATCHED.value,
                    "match_type": match_result["match_type"],
                },
                created_by=self.actor_id,
            )
            return updated

        reason = match_result["issues"][0]["message"] if match_result["issues"] else "Match failed"
        return await self.flag_exception(invoice_id, reason)

    async def flag_exception(
        self,
        invoice_id: uuid.UUID,
        reason: str,
    ) -> Invoice | None:
        """Flag an invoice with a matching exception for review."""
        invoice = await self.uow.invoices.get(invoice_id)
        if invoice is None:
            return None
        old_status = invoice.match_status
        updated = await self.uow.invoices.update_match_status(
            invoice_id, MatchStatus.EXCEPTION,
        )
        await self.uow.audit.log(
            tenant_id=self.uow.tenant_id,
            entity_type="invoice",
            entity_id=invoice_id,
            event_type="INVOICE_EXCEPTION",
            old_values={"match_status": _status_value(old_status)},
            new_values={"match_status": MatchStatus.EXCEPTION.value, "reason": reason},
            created_by=self.actor_id,
        )
        return updated

    async def resolve_exception(
        self,
        invoice_id: uuid.UUID,
        *,
        mode: str = "auto",
        note: str | None = None,
    ) -> Invoice:
        """Clear an EXCEPTION when rules allow (auto) or force with manual note."""
        invoice = await self.uow.invoices.get(invoice_id)
        if invoice is None:
            raise InvoiceMatchError("Invoice not found")
        if invoice.match_status != MatchStatus.EXCEPTION:
            raise InvoiceMatchError("Invoice is not in EXCEPTION status")

        if mode == "manual":
            if not note:
                raise InvoiceMatchError("Manual resolve requires a note")
            match_result = await self.evaluate_match(invoice_id)
            match_result["status"] = MatchStatus.MATCHED.value
            match_result["passed"] = True
            match_result["match_type"] = "MANUAL_RESOLVE"
            match_result["resolution"] = {"mode": "manual", "note": note}
            await self._persist_match_result(invoice_id, match_result)
            updated = await self.uow.invoices.update_match_status(
                invoice_id, MatchStatus.MATCHED,
            )
            updated = await self._mark_ready_for_payment(invoice_id) or updated
            await self.uow.audit.log(
                tenant_id=self.uow.tenant_id,
                entity_type="invoice",
                entity_id=invoice_id,
                event_type="INVOICE_AUTO_RESOLVED",
                old_values={"match_status": MatchStatus.EXCEPTION.value},
                new_values={"match_status": MatchStatus.MATCHED.value, "mode": "manual", "note": note},
                created_by=self.actor_id,
            )
            return updated  # type: ignore[return-value]

        # Auto mode — re-evaluate with elevated amount tolerance for PRICE_VARIANCE
        extras = invoice.extras or {}
        prior = extras.get("match_result") or {}
        primary = prior.get("primary_issue")

        # Fresh evaluation first (may pass if GRN was added)
        fresh = await self.evaluate_match(invoice_id)
        if fresh["passed"]:
            await self._persist_match_result(invoice_id, {
                **fresh,
                "resolution": {"mode": "auto", "action": "re_match_after_fix"},
            })
            updated = await self.uow.invoices.update_match_status(
                invoice_id, MatchStatus.MATCHED,
            )
            updated = await self._mark_ready_for_payment(invoice_id) or updated
            await self.uow.audit.log(
                tenant_id=self.uow.tenant_id,
                entity_type="invoice",
                entity_id=invoice_id,
                event_type="INVOICE_AUTO_RESOLVED",
                old_values={"match_status": MatchStatus.EXCEPTION.value},
                new_values={"match_status": MatchStatus.MATCHED.value, "mode": "auto", "action": "re_match"},
                created_by=self.actor_id,
            )
            return updated  # type: ignore[return-value]

        # Try elevated tolerance for price variance
        if primary == "PRICE_VARIANCE" or any(
            i.get("code") == "PRICE_VARIANCE" for i in fresh.get("issues", [])
        ):
            auto_tol = _money(fresh["auto_resolve_tolerance"])
            elevated = await self.evaluate_match(
                invoice_id, amount_tolerance_override=auto_tol,
            )
            # Still require GRN / qty OK — only amount tolerance elevated
            blocking = [
                i for i in elevated.get("issues", [])
                if i.get("code") != "PRICE_VARIANCE"
            ]
            price_ok = not any(
                i.get("code") == "PRICE_VARIANCE" for i in elevated.get("issues", [])
            )
            if price_ok and not blocking:
                elevated["passed"] = True
                elevated["status"] = MatchStatus.MATCHED.value
                elevated["match_type"] = "AUTO_RESOLVE_TOLERANCE"
                elevated["resolution"] = {
                    "mode": "auto",
                    "action": "auto_match_tolerance",
                    "note": note,
                }
                await self._persist_match_result(invoice_id, elevated)
                updated = await self.uow.invoices.update_match_status(
                    invoice_id, MatchStatus.MATCHED,
                )
                updated = await self._mark_ready_for_payment(invoice_id) or updated
                await self.uow.audit.log(
                    tenant_id=self.uow.tenant_id,
                    entity_type="invoice",
                    entity_id=invoice_id,
                    event_type="INVOICE_AUTO_RESOLVED",
                    old_values={"match_status": MatchStatus.EXCEPTION.value},
                    new_values={
                        "match_status": MatchStatus.MATCHED.value,
                        "mode": "auto",
                        "action": "auto_match_tolerance",
                    },
                    created_by=self.actor_id,
                )
                return updated  # type: ignore[return-value]

        codes = [i.get("code") for i in fresh.get("issues", [])]
        if "MISSING_GRN" in codes:
            raise InvoiceMatchError(
                "Cannot auto-resolve: goods receipt is still missing. "
                "Record a GRN, then retry Auto-Resolve.",
            )
        if "PRICE_VARIANCE" in codes:
            raise InvoiceMatchError(
                "Cannot auto-resolve: price variance exceeds autonomous tolerance "
                f"(${fresh['auto_resolve_tolerance']:.2f}). Escalate for human review.",
            )
        raise InvoiceMatchError(
            f"Cannot auto-resolve: {fresh['issues'][0]['message'] if fresh.get('issues') else 'unknown issue'}",
        )

    async def approve_payment(self, invoice_id: uuid.UUID) -> Invoice | None:
        """Mark invoice as ready for payment (matched invoices only)."""
        return await self.send_to_payment(invoice_id)

    async def send_to_payment(self, invoice_id: uuid.UUID) -> Invoice | None:
        """Send a matched invoice to payment.

        Requires ``match_status=MATCHED``. Stores ``payment_status`` in extras
        so the UI can show Ready → Sent to Payment.
        """
        invoice = await self.uow.invoices.get(invoice_id)
        if invoice is None:
            return None
        if invoice.match_status != MatchStatus.MATCHED:
            raise InvoiceMatchError(
                "Invoice must be MATCHED (exceptions resolved) before sending to payment",
            )
        extras = dict(invoice.extras or {})
        current = extras.get("payment_status")
        if current == "SENT_TO_PAYMENT":
            return invoice

        extras["payment_status"] = "SENT_TO_PAYMENT"
        extras["payment_ready"] = True
        extras["sent_to_payment_at"] = datetime.utcnow().isoformat() + "Z"
        updated = await self.uow.invoices.update(invoice_id, {"extras": extras})
        await self.uow.audit.log(
            tenant_id=self.uow.tenant_id,
            entity_type="invoice",
            entity_id=invoice_id,
            event_type="INVOICE_SENT_TO_PAYMENT",
            old_values={"payment_status": current},
            new_values={"payment_status": "SENT_TO_PAYMENT"},
            created_by=self.actor_id,
        )
        return updated

    async def find_duplicates(self, invoice_id: uuid.UUID) -> list[Invoice]:
        """Detect potential duplicate invoices."""
        invoice = await self.uow.invoices.get(invoice_id)
        if invoice is None:
            return []
        return await self.uow.invoices.find_duplicates(invoice)

    async def get_exception_queue(self) -> list[Invoice]:
        """Return all invoices requiring human review."""
        return await self.uow.invoices.list_exception_queue()

    async def delete_invoice(
        self,
        invoice_id: uuid.UUID,
        *,
        soft: bool = True,
    ) -> bool:
        """Soft-delete (or hard-delete) an invoice."""
        invoice = await self.uow.invoices.get(invoice_id)
        if invoice is None:
            return False
        deleted = await self.uow.invoices.delete(invoice_id, soft=soft)
        if deleted:
            await self.uow.audit.log(
                tenant_id=self.uow.tenant_id,
                entity_type="invoice",
                entity_id=invoice_id,
                event_type="INVOICE_DELETED",
                old_values={
                    "invoice_number": str(getattr(invoice, "invoice_number", "")),
                    "amount": str(getattr(invoice, "amount", "")),
                },
                created_by=self.actor_id,
            )
        return deleted


def _status_value(status: MatchStatus | str | None) -> str | None:
    if status is None:
        return None
    if isinstance(status, MatchStatus):
        return status.value
    return str(status)
