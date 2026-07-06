"""
OpenS2P – Authentication API endpoints
========================================
"""

from __future__ import annotations

import uuid

from fastapi import APIRouter, Depends, HTTPException, status

from app.models import User
from app.schemas.common import ApiResponse
from app.schemas.user import UserCreate, UserResponse
from app.security import (
    AuthContext,
    create_access_token,
    hash_password,
    require_auth,
    verify_password,
)
from app.services.uow import UnitOfWork
from app.api.deps import get_unit_of_work

router = APIRouter(prefix="/auth", tags=["Authentication"])


@router.post("/login")
async def login(
    username: str,
    password: str,
    uow: UnitOfWork = Depends(get_unit_of_work),
):
    """Authenticate with username/password and receive a JWT access token."""
    async with uow:
        user = await uow.users.get_by_username(username)
        if user is None or not verify_password(password, user.hashed_password or ""):
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid username or password",
            )

        # Fetch role names for the JWT
        user_with_roles = await uow.users.get_with_roles(user.id)
        role_names: list[str] = []
        if user_with_roles:
            role_names = [ur.role.role_name for ur in (user_with_roles.roles or [])]

        token = create_access_token(
            sub=str(user.id),
            tenant_id=str(user.tenant_id),
            roles=role_names,
        )

        return ApiResponse(data={
            "access_token": token,
            "token_type": "bearer",
            "expires_in": 3600,
            "user": UserResponse.model_validate(user),
        })


@router.post("/register", status_code=201)
async def register(
    body: UserCreate,
    uow: UnitOfWork = Depends(get_unit_of_work),
):
    """Register a new user (requires an existing tenant context)."""
    async with uow:
        # Check for duplicates
        existing = await uow.users.get_by_username(body.username)
        if existing:
            raise HTTPException(status_code=409, detail="Username already taken")
        existing_email = await uow.users.get_by_email(body.email)
        if existing_email:
            raise HTTPException(status_code=409, detail="Email already registered")

        user = await uow.users.create({
            "id": uuid.uuid4(),
            "username": body.username,
            "email": body.email,
            "first_name": body.first_name,
            "last_name": body.last_name,
            "hashed_password": hash_password(body.password),
        })
        await uow.commit()
        return ApiResponse(
            data=UserResponse.model_validate(user),
            message="User registered",
        )


@router.get("/me")
async def me(
    current_user: AuthContext = Depends(require_auth),
    uow: UnitOfWork = Depends(get_unit_of_work),
):
    """Return the currently authenticated user's profile."""
    async with uow:
        user = await uow.users.get(current_user.user_id)
        if user is None:
            raise HTTPException(status_code=404, detail="User not found")
        return ApiResponse(data={
            "user": UserResponse.model_validate(user),
            "roles": current_user.roles,
            "tenant_id": str(current_user.tenant_id),
        })
