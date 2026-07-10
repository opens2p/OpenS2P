"""
OpenS2P – AI Intelligence Layer
================================
Domain-specific AI analysis services for supplier, contract, and invoice domains.
"""

from .supplier_ai import SupplierAIService
from .contract_ai import ContractAIService
from .invoice_ai import InvoiceAIService
from .core import AIProvider, PROMPTS, validate_input, sanitize_output, mask_sensitive_context
from .rag import load_document, chunk_text, retrieve, format_context, rag_chain
from .copilot import CopilotService

__all__ = [
    "SupplierAIService",
    "ContractAIService",
    "InvoiceAIService",
    "AIProvider",
    "PROMPTS",
    "validate_input",
    "sanitize_output",
    "mask_sensitive_context",
    "load_document",
    "chunk_text",
    "retrieve",
    "format_context",
    "rag_chain",
    "CopilotService",
]
