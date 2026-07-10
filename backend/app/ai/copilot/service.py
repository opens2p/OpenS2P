"""
Procurement Copilot — natural language query interface.
"""
from __future__ import annotations
from app.ai.core.provider import AIProvider
from app.ai.core.prompts import PROMPTS
from app.ai.core.guardrails import validate_input, sanitize_output


class CopilotService:
    """AI assistant for procurement queries."""

    def __init__(self, uow=None):
        self.uow = uow

    async def chat(self, message: str, context: dict | None = None) -> dict:
        is_valid, error = validate_input(message)
        if not is_valid:
            return {"response": f"I cannot process that: {error}", "sources": []}

        # Gather platform context
        platform_context = ""
        if self.uow:
            try:
                supplier_count = len(await self.uow.suppliers.list())
                po_count = len(await self.uow.purchase_orders.list())
                invoice_count = len(await self.uow.invoices.list())
                platform_context = f"Platform has {supplier_count} suppliers, {po_count} purchase orders, {invoice_count} invoices."
            except Exception:
                platform_context = "Platform data available."

        full_prompt = f"{platform_context}\n\nUser question: {message}"
        provider = AIProvider()
        result = await provider.generate(PROMPTS["copilot"], full_prompt)
        response = sanitize_output(result.get("content", "I can help with procurement questions."))

        return {"response": response, "sources": ["OpenS2P platform data"]}
