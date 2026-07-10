"""
Document repository.
"""
from __future__ import annotations
import uuid
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from app.models.document import Document
from app.repositories.base import BaseRepository


class DocumentRepository(BaseRepository[Document]):
    def __init__(self, session: AsyncSession, tenant_id: uuid.UUID) -> None:
        super().__init__(session, Document, tenant_id=tenant_id)

    async def list_by_object(self, object_type: str, object_id: uuid.UUID) -> list[Document]:
        stmt = self._stmt().where(
            Document.object_type == object_type,
            Document.object_id == object_id,
        ).order_by(Document.created_at.desc())
        result = await self.session.execute(stmt)
        return list(result.unique().scalars().all())
