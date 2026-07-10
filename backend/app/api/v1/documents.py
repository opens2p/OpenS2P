"""
OpenS2P – Document Management API
====================================
"""
from __future__ import annotations
import uuid
from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Form
from pydantic import BaseModel

from app.schemas.common import ApiResponse
from app.services.uow import UnitOfWork
from app.api.deps import get_unit_of_work
from app.security import AuthContext, require_auth, require_permission
from app.security import permissions as perm
from app.schemas.serialization import safe_validate

router = APIRouter(prefix="/documents", tags=["Documents"])


# Simplified document response
class DocumentResponse(BaseModel):
    model_config = {"from_attributes": True}
    id: uuid.UUID
    filename: str
    original_filename: str
    file_size: int
    mime_type: str
    object_type: str
    object_id: uuid.UUID
    category: str | None = None
    tenant_id: uuid.UUID
    created_at: datetime | None = None


@router.post("/upload", response_model=ApiResponse[DocumentResponse], status_code=201)
async def upload_document(
    file: UploadFile = File(...),
    object_type: str = Form(...),
    object_id: str = Form(...),
    category: str | None = Form(None),
    _: None = Depends(require_permission(perm.ADMIN_MANAGE_USERS)),
    auth: AuthContext = Depends(require_auth),
    uow: UnitOfWork = Depends(get_unit_of_work),
):
    content = await file.read()
    doc_data = {
        "filename": file.filename or "unknown",
        "original_filename": file.filename or "unknown",
        "file_size": len(content),
        "mime_type": file.content_type or "application/octet-stream",
        "file_path": f"uploads/{object_type}/{object_id}/{file.filename}",
        "object_type": object_type,
        "object_id": uuid.UUID(object_id),
        "category": category,
    }
    async with uow:
        doc = await uow.documents.create(doc_data)
        # In production, save file to S3/disk here
        resp = await safe_validate(DocumentResponse, doc)
        await uow.commit()
        return ApiResponse(data=resp, message="Document uploaded")


@router.get("/{document_id}", response_model=ApiResponse[DocumentResponse])
async def get_document(
    document_id: uuid.UUID,
    _: AuthContext = Depends(require_permission(perm.ADMIN_STATS)),
    uow: UnitOfWork = Depends(get_unit_of_work),
):
    async with uow:
        doc = await uow.documents.get(document_id)
        if not doc:
            raise HTTPException(status_code=404, detail="Document not found")
        return ApiResponse(data=await safe_validate(DocumentResponse, doc))


@router.get("/by-object/{object_type}/{object_id}", response_model=ApiResponse[list[DocumentResponse]])
async def list_documents(
    object_type: str,
    object_id: uuid.UUID,
    _: AuthContext = Depends(require_permission(perm.ADMIN_STATS)),
    uow: UnitOfWork = Depends(get_unit_of_work),
):
    async with uow:
        docs = await uow.documents.list_by_object(object_type, object_id)
        return ApiResponse(data=[await safe_validate(DocumentResponse, d) for d in docs])


@router.delete("/{document_id}", status_code=204)
async def delete_document(
    document_id: uuid.UUID,
    _: None = Depends(require_permission(perm.ADMIN_MANAGE_USERS)),
    auth: AuthContext = Depends(require_auth),
    uow: UnitOfWork = Depends(get_unit_of_work),
):
    async with uow:
        deleted = await uow.documents.delete(document_id)
        if not deleted:
            raise HTTPException(status_code=404, detail="Document not found")
        await uow.commit()
