"""
OpenS2P – Contract API endpoints
==================================
"""

from __future__ import annotations

import uuid

from fastapi import APIRouter, Depends, HTTPException, Query

from app.schemas.common import ApiResponse
from app.schemas.contract import (
    ContractCreate,
    ContractRenew,
    ContractResponse,
    ContractUpdate,
)
from app.schemas.serialization import safe_validate
from app.services.contract_service import ContractService
from app.services.uow import UnitOfWork
from app.api.deps import get_unit_of_work
from app.security import AuthContext, require_auth, require_permission
from app.security import permissions as perm

router = APIRouter(prefix="/contracts", tags=["Contract Management"])


@router.get("", response_model=ApiResponse[list[ContractResponse]])
async def list_contracts(
    _: AuthContext = Depends(require_permission(perm.CONTRACT_VIEW)),
    skip: int = 0,
    limit: int = 50,
    expiring_within: int | None = Query(None, description="Filter contracts expiring within N days"),
    uow: UnitOfWork = Depends(get_unit_of_work),
):
    async with uow:
        svc = ContractService(uow)
        if expiring_within:
            contracts = await svc.list_expiring(within_days=expiring_within)
        else:
            contracts = await svc.uow.contracts.list(skip=skip, limit=limit)
        return ApiResponse(data=[await safe_validate(ContractResponse, c) for c in contracts])


@router.get("/{contract_id}", response_model=ApiResponse[ContractResponse])
async def get_contract(
    contract_id: uuid.UUID,
    _: AuthContext = Depends(require_permission(perm.CONTRACT_VIEW)),
    uow: UnitOfWork = Depends(get_unit_of_work),
):
    async with uow:
        contract = await uow.contracts.get(contract_id)
        if contract is None:
            raise HTTPException(status_code=404, detail="Contract not found")
        return ApiResponse(data=await safe_validate(ContractResponse, contract))


@router.post("", response_model=ApiResponse[ContractResponse], status_code=201)
async def create_contract(
    body: ContractCreate,
    _: None = Depends(require_permission(perm.CONTRACT_CREATE)),
    auth: AuthContext = Depends(require_auth),
    uow: UnitOfWork = Depends(get_unit_of_work),
):
    async with uow:
        svc = ContractService(uow, actor_id=auth.user_id)
        contract = await svc.create_contract(body.model_dump(exclude_none=True))
        data = await safe_validate(ContractResponse, contract)
        resp = ApiResponse(data=data, message="Contract created")
        await uow.commit()
        return resp


@router.patch("/{contract_id}", response_model=ApiResponse[ContractResponse])
async def update_contract(
    contract_id: uuid.UUID,
    body: ContractUpdate,
    _: None = Depends(require_permission(perm.CONTRACT_UPDATE)),
    auth: AuthContext = Depends(require_auth),
    uow: UnitOfWork = Depends(get_unit_of_work),
):
    async with uow:
        svc = ContractService(uow, actor_id=auth.user_id)
        contract = await svc.uow.contracts.update(
            contract_id, body.model_dump(exclude_none=True),
        )
        if contract is None:
            raise HTTPException(status_code=404, detail="Contract not found")
        data = await safe_validate(ContractResponse, contract)
        resp = ApiResponse(data=data)
        await uow.commit()
        return resp


@router.post("/{contract_id}/activate", response_model=ApiResponse[ContractResponse])
async def activate_contract(
    contract_id: uuid.UUID,
    _: None = Depends(require_permission(perm.CONTRACT_ACTIVATE)),
    auth: AuthContext = Depends(require_auth),
    uow: UnitOfWork = Depends(get_unit_of_work),
):
    async with uow:
        svc = ContractService(uow, actor_id=auth.user_id)
        result = await svc.activate_contract(contract_id)
        if result is None:
            raise HTTPException(status_code=404, detail="Contract not found")
        data = await safe_validate(ContractResponse, result)
        resp = ApiResponse(data=data, message="Contract activated")
        await uow.commit()
        return resp


@router.post("/{contract_id}/renew", response_model=ApiResponse[ContractResponse])
async def renew_contract(
    contract_id: uuid.UUID,
    body: ContractRenew,
    _: None = Depends(require_permission(perm.CONTRACT_RENEW)),
    auth: AuthContext = Depends(require_auth),
    uow: UnitOfWork = Depends(get_unit_of_work),
):
    async with uow:
        svc = ContractService(uow, actor_id=auth.user_id)
        result = await svc.renew_contract(
            contract_id,
            new_end_date=body.new_end_date,
            additional_value=body.additional_value,
        )
        if result is None:
            raise HTTPException(status_code=404, detail="Contract not found")
        data = await safe_validate(ContractResponse, result)
        resp = ApiResponse(data=data, message="Contract renewed")
        await uow.commit()
        return resp


@router.delete("/{contract_id}", status_code=204)
async def delete_contract(
    contract_id: uuid.UUID,
    _: None = Depends(require_permission(perm.CONTRACT_DELETE)),
    auth: AuthContext = Depends(require_auth),
    uow: UnitOfWork = Depends(get_unit_of_work),
):
    """Soft-delete a contract (sets is_active=False)."""
    async with uow:
        svc = ContractService(uow, actor_id=auth.user_id)
        deleted = await svc.delete_contract(contract_id)
        if not deleted:
            raise HTTPException(status_code=404, detail="Contract not found")
        await uow.commit()
