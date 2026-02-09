# backend/api/auth/endpoints.py
"""Authentication endpoints."""
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.ext.asyncio import AsyncSession

from backend.db.database import get_db
from backend.db.models import User
from backend.auth.dependencies import get_current_user
from backend.services.auth import (
    register_user,
    login_user,
    UserAlreadyExistsError,
    InvalidCredentialsError,
)
from .schemas import UserCreate, Token, UserResponse

router = APIRouter()


@router.post("/register", response_model=Token)
async def register(user_data: UserCreate, db: AsyncSession = Depends(get_db)):
    """Register a new user account."""
    try:
        user, access_token = await register_user(user_data.email, user_data.password, db)
        return {"access_token": access_token, "token_type": "bearer"}
    except UserAlreadyExistsError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/login", response_model=Token)
async def login(
    form_data: Annotated[OAuth2PasswordRequestForm, Depends()],
    db: AsyncSession = Depends(get_db)
):
    """Login and receive access token."""
    try:
        user, access_token = await login_user(form_data.username, form_data.password, db)
        return {"access_token": access_token, "token_type": "bearer"}
    except InvalidCredentialsError as e:
        raise HTTPException(status_code=401, detail=str(e), headers={"WWW-Authenticate": "Bearer"})


@router.get("/me", response_model=UserResponse)
async def get_current_user_info(current_user: Annotated[User, Depends(get_current_user)]):
    """Get current user information."""
    return {
        "id": str(current_user.id),
        "email": current_user.email,
        "created_at": current_user.created_at
    }
