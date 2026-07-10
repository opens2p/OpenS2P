"""
Simple keyword-based retriever. In production, use vector embeddings (pgvector).
"""
from __future__ import annotations
from typing import Any


async def retrieve(query: str, documents: list[str], top_k: int = 3) -> list[dict[str, Any]]:
    """Retrieve most relevant documents for a query using keyword matching."""
    query_terms = query.lower().split()
    scored = []
    for i, doc in enumerate(documents):
        doc_lower = doc.lower()
        score = sum(1 for term in query_terms if term in doc_lower)
        if score > 0:
            scored.append({"index": i, "score": score, "content": doc[:500]})
    scored.sort(key=lambda x: -x["score"])
    return scored[:top_k]


async def format_context(results: list[dict[str, Any]]) -> str:
    """Format retrieved documents into a context string for the LLM."""
    parts = []
    for i, r in enumerate(results):
        parts.append(f"[Document {i+1}]\n{r['content']}\n")
    return "\n".join(parts)
