"""
OpenS2P \u2013 Integration API endpoints
=====================================
"""
from __future__ import annotations
import uuid
from fastapi import APIRouter, Depends, HTTPException
from app.schemas.common import ApiResponse
from app.schemas.integration import (
    ConnectionCreate,
    ConnectionUpdate,
    ConnectionResponse,
    SyncRequest,
    SyncResponse,
    RunResponse,
    LogResponse,
)
from app.services.uow import UnitOfWork
from app.api.deps import get_unit_of_work
from app.security import AuthContext, require_auth, require_permission
from app.security import permissions as perm
from app.schemas.serialization import safe_validate
from app.integrations.base.connector import ConnectionConfig
from app.integrations.base.credentials import mask_credentials
from app.integrations.sap.client import create_sap_connector
from app.integrations.scheduler import run_sync

router = APIRouter(prefix="/integrations", tags=["Integrations"])

CONNECTOR_REGISTRY = {
    "sap": create_sap_connector,
}


def _get_connector(connector_type: str, config: ConnectionConfig):
    factory = CONNECTOR_REGISTRY.get(connector_type)
    if not factory:
        raise HTTPException(status_code=400, detail=f"Unsupported connector: {connector_type}")
    return factory(config)


@router.get("/connections", response_model=ApiResponse[list[ConnectionResponse]])
async def list_connections(
    _: None = Depends(require_permission(perm.ADMIN_STATS)),
    uow: UnitOfWork = Depends(get_unit_of_work),
):
    async with uow:
        connections = await uow.integration_connections.list()
        return ApiResponse(data=[await safe_validate(ConnectionResponse, c) for c in connections])


@router.post("/connections", response_model=ApiResponse[ConnectionResponse], status_code=201)
async def create_connection(
    body: ConnectionCreate,
    _: None = Depends(require_permission(perm.ADMIN_MANAGE_USERS)),
    auth: AuthContext = Depends(require_auth),
    uow: UnitOfWork = Depends(get_unit_of_work),
):
    async with uow:
        conn = await uow.integration_connections.create(body.model_dump(exclude_none=True))
        resp = await safe_validate(ConnectionResponse, conn)
        await uow.commit()
        return ApiResponse(data=resp, message="Connection created")


@router.get("/connections/{connection_id}", response_model=ApiResponse[ConnectionResponse])
async def get_connection(
    connection_id: uuid.UUID,
    _: None = Depends(require_permission(perm.ADMIN_STATS)),
    uow: UnitOfWork = Depends(get_unit_of_work),
):
    async with uow:
        conn = await uow.integration_connections.get(connection_id)
        if not conn:
            raise HTTPException(status_code=404, detail="Connection not found")
        return ApiResponse(data=await safe_validate(ConnectionResponse, conn))


@router.patch("/connections/{connection_id}", response_model=ApiResponse[ConnectionResponse])
async def update_connection(
    connection_id: uuid.UUID,
    body: ConnectionUpdate,
    _: None = Depends(require_permission(perm.ADMIN_MANAGE_USERS)),
    auth: AuthContext = Depends(require_auth),
    uow: UnitOfWork = Depends(get_unit_of_work),
):
    async with uow:
        conn = await uow.integration_connections.update(connection_id, body.model_dump(exclude_none=True))
        if not conn:
            raise HTTPException(status_code=404, detail="Connection not found")
        resp = await safe_validate(ConnectionResponse, conn)
        await uow.commit()
        return ApiResponse(data=resp)


@router.delete("/connections/{connection_id}", status_code=204)
async def delete_connection(
    connection_id: uuid.UUID,
    _: None = Depends(require_permission(perm.ADMIN_MANAGE_USERS)),
    auth: AuthContext = Depends(require_auth),
    uow: UnitOfWork = Depends(get_unit_of_work),
):
    async with uow:
        deleted = await uow.integration_connections.delete(connection_id)
        if not deleted:
            raise HTTPException(status_code=404, detail="Connection not found")
        await uow.commit()


@router.post("/connections/{connection_id}/test", response_model=ApiResponse[dict])
async def test_connection(
    connection_id: uuid.UUID,
    _: None = Depends(require_permission(perm.ADMIN_MANAGE_USERS)),
    auth: AuthContext = Depends(require_auth),
    uow: UnitOfWork = Depends(get_unit_of_work),
):
    async with uow:
        conn = await uow.integration_connections.get(connection_id)
        if not conn:
            raise HTTPException(status_code=404, detail="Connection not found")
        config = ConnectionConfig(
            id=conn.id, connector_type=conn.connector_type,
            endpoint_url=conn.endpoint_url, auth_type=conn.auth_type,
            credentials=conn.credentials, config=conn.config,
        )
        try:
            adapter = _get_connector(conn.connector_type, config)
            ok = await adapter.test_connection()
            if ok:
                await uow.integration_connections.mark_connected(connection_id)
                await uow.commit()
            return ApiResponse(data={"connected": ok, "connector_type": conn.connector_type})
        except Exception as e:
            return ApiResponse(data={"connected": False, "error": str(e)})


@router.post("/connections/{connection_id}/sync", response_model=ApiResponse[SyncResponse])
async def sync_connection(
    connection_id: uuid.UUID,
    body: SyncRequest,
    _: None = Depends(require_permission(perm.ADMIN_MANAGE_USERS)),
    auth: AuthContext = Depends(require_auth),
    uow: UnitOfWork = Depends(get_unit_of_work),
):
    async with uow:
        conn = await uow.integration_connections.get(connection_id)
        if not conn:
            raise HTTPException(status_code=404, detail="Connection not found")
        config = ConnectionConfig(
            id=conn.id, tenant_id=conn.tenant_id, connector_type=conn.connector_type,
            endpoint_url=conn.endpoint_url, auth_type=conn.auth_type,
            credentials=conn.credentials, config=conn.config,
        )
        run = await uow.integration_runs.create({
            "connection_id": connection_id, "direction": "extract",
            "status": "running", "started_at": None,
        })
        await uow.flush()
        try:
            result = await run_sync(connection_id, conn.connector_type, body.object_type, config)
            await uow.integration_runs.update(run.id, {
                "status": result["status"], "records_processed": result["records_processed"],
                "completed_at": None,
            })
            await uow.integration_connections.update_sync_time(connection_id)
            await uow.commit()
            return ApiResponse(data=SyncResponse(
                run_id=run.id, status=result["status"],
                records_processed=result["records_processed"],
            ))
        except Exception as e:
            await uow.integration_runs.update(run.id, {"status": "failed"})
            await uow.commit()
            return ApiResponse(data=SyncResponse(run_id=run.id, status="failed"))


@router.get("/runs", response_model=ApiResponse[list[RunResponse]])
async def list_runs(
    connection_id: uuid.UUID | None = None,
    _: None = Depends(require_permission(perm.ADMIN_STATS)),
    uow: UnitOfWork = Depends(get_unit_of_work),
):
    async with uow:
        if connection_id:
            runs = await uow.integration_runs.list_by_connection(connection_id)
        else:
            runs = await uow.integration_runs.list()
        return ApiResponse(data=[await safe_validate(RunResponse, r) for r in runs])


@router.get("/runs/{run_id}/logs", response_model=ApiResponse[list[LogResponse]])
async def get_run_logs(
    run_id: uuid.UUID,
    _: None = Depends(require_permission(perm.ADMIN_STATS)),
    uow: UnitOfWork = Depends(get_unit_of_work),
):
    async with uow:
        logs = await uow.integration_logs.list_by_run(run_id)
        return ApiResponse(data=[await safe_validate(LogResponse, log) for log in logs])
