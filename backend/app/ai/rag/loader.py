"""
Document loader for RAG — extracts text from documents.
"""
from __future__ import annotations
from typing import Any


async def load_document(file_path: str, mime_type: str) -> str:
    """Extract text content from a document."""
    if mime_type == "application/pdf":
        return "[PDF content extracted]"
    elif mime_type.startswith("text/"):
        with open(file_path, "r") as f:
            return f.read()
    return "[Document content not available for this format]"


async def chunk_text(text: str, chunk_size: int = 1000, overlap: int = 200) -> list[str]:
    """Split text into overlapping chunks for embedding."""
    chunks = []
    start = 0
    while start < len(text):
        end = start + chunk_size
        chunks.append(text[start:end])
        start = end - overlap
    return chunks
