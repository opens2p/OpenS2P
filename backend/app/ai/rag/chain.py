"""
RAG chain — retrieve context, generate answer.
"""
from __future__ import annotations
from typing import Any
from app.ai.core.provider import AIProvider
from app.ai.rag.retriever import retrieve, format_context


async def rag_chain(
    query: str,
    documents: list[str],
    system_prompt: str,
    provider: AIProvider | None = None,
) -> dict[str, Any]:
    """Complete RAG chain: retrieve context, generate answer."""
    provider = provider or AIProvider()
    results = await retrieve(query, documents)
    context = await format_context(results)
    user_prompt = f"Context:\n{context}\n\nQuestion: {query}\n\nAnswer based on the context above."
    return await provider.generate(system_prompt, user_prompt)
