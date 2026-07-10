"""
OpenS2P – RAG Pipeline
=======================
Document loading, chunking, retrieval, and chain for Retrieval-Augmented Generation.
"""

from .loader import load_document, chunk_text
from .retriever import retrieve, format_context
from .chain import rag_chain

__all__ = [
    "load_document",
    "chunk_text",
    "retrieve",
    "format_context",
    "rag_chain",
]
