"""
AquaGuard AI - Authentication Endpoints
Handles user login, logout, and profile retrieval.
"""
from datetime import datetime, timezone
from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession
from sqlmodel import select

from app.api.deps.auth import verify_password, create_access_token, get_current_user
from app.database.db import get_session
from app.models.models import User

router = APIRouter()


class LoginRequest(BaseModel):
    email: str
    password: str


class UserResponse(BaseModel):
    id: int
    email: str
    full_name: str
    role: str
    is_active: bool

    class Config:
        from_attributes = True


class LoginResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user: UserResponse


@router.post("/login", response_model=LoginResponse, summary="User Login")
async def login(credentials: LoginRequest, session: AsyncSession = Depends(get_session)):
    """
    Authenticate user via email and password, returning a signed JWT access token.
    Supports Admin, Operator, and Researcher roles.
    """
    statement = select(User).where(User.email == credentials.email.lower().strip())
    result = await session.execute(statement)
    user = result.scalars().first()

    if not user or not verify_password(credentials.password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password",
            headers={"WWW-Authenticate": "Bearer"},
        )

    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="User account is deactivated",
        )

    # Update last login timestamp
    user.last_login = datetime.now(timezone.utc)
    session.add(user)
    await session.commit()
    await session.refresh(user)

    # Generate JWT
    access_token = create_access_token(
        data={"sub": user.email, "role": user.role, "id": user.id}
    )

    return LoginResponse(
        access_token=access_token,
        token_type="bearer",
        user=UserResponse(
            id=user.id,
            email=user.email,
            full_name=user.full_name,
            role=user.role,
            is_active=user.is_active,
        ),
    )


@router.post("/logout", summary="User Logout")
async def logout(current_user: User = Depends(get_current_user)):
    """
    Client-side token invalidation endpoint.
    Stateless JWT logout acknowledges session termination.
    """
    return {"message": f"User {current_user.email} logged out successfully"}


@router.get("/me", response_model=UserResponse, summary="Get Current User Profile")
async def get_me(current_user: User = Depends(get_current_user)):
    """Retrieve the currently authenticated user's profile and permissions."""
    return UserResponse(
        id=current_user.id,
        email=current_user.email,
        full_name=current_user.full_name,
        role=current_user.role,
        is_active=current_user.is_active,
    )