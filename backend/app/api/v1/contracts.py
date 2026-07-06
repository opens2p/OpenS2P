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
from app.services.contract_service import ContractService
from app.services.uow import UnitOfWork
from app.api.deps import get_unit_of_work

router = APIRouter(prefix="/contracts", tags=["Contract Management"])


@router.get("", response_model=ApiResponse[list[ContractResponse]])
async def list_contracts(
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
        return ApiResponse(data=[ContractResponse.model_validate(c) for c in contracts])


@router.get("/{contract_id}", response_model=ApiResponse[ContractResponse])
async def get_contract(
    contract_id: uuid.UUID,
    uow: UnitOfWork = Depends(get_unit_of_work),
):
    async with uow:
        contract = await uow.contracts.get(contract_id)
        if contract is None:
            raise HTTPException(status_code=404, detail="Contract not found")
        return ApiResponse(data=ContractResponse.model_validate(contract))


@router.post("", response_model=ApiResponse[ContractResponse], status_code=201)
async def create_contract(
    body: ContractCreate,
    uow: UnitOfWork = Depends(get_unit_of_work),
):
    async with uow:
        svc = ContractService(uow)
        contract = await svc.create_contract(body.model_dump(exclude_none=True))
        await uow.commit()
        return ApiResponse(data=ContractResponse.model_validate(contract), message="Contract created")


@router.post("/{contract_id}/activate", response_model=ApiResponse[ContractResponse])
async def activate_contract(
    contract_id: uuid.UUID,
    uow: UnitOfWork = Depends(get_unit_of_work),
):
    async with uow:
        svc = ContractService(uow)
        result = await svc.activate_contract(contract_id)
        if result is None:
            raise HTTPException(status_code=404, detail="Contract not found")
        await uow.commit()
        return ApiResponse(data=ContractResponse.model_validate(result), message="Contract activated")


@router.post("/{contract_id}/renew", response_model=ApiResponse[ContractResponse])
async def renew_contract(
    contract_id: uuid.UUID,
    body: ContractRenew,
    uow: UnitOfWork = Depends(get_unit_of_work),
):
    async with uow:
        svc = ContractService(uow)
        result = await svc.renew_contract(
            contract_id,
            new_end_date=body.new_end_date,
            additional_value=body.additional_value,
        )
        if result is None:
            raise HTTPException(status_code=404, detail="Contract not found")
        await uow.commit()
        return ApiResponse(data=ContractResponse.model_validate(result), message="Contract renewed")
