# backend/api/auth/endpoints.py
"""Authentication endpoints."""

from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException
from fastapi.security import OAuth2PasswordRequestForm

from backend.dependencies import get_auth_service
from backend.domains.auth.services.exceptions import (
    InvalidCredentialsError,
    UserAlreadyExistsError,
)
from backend.domains.auth.services.service import AuthService
from backend.shared.auth.dependencies import get_current_user
from backend.shared.db.models import User

from .schemas import Token, UserCreate, UserResponse

router = APIRouter(prefix="/auth", tags=["auth"])


@router.post("/register", response_model=Token)
async def register(
    user_data: UserCreate,
    service: AuthService = Depends(get_auth_service),
) -> Token:
    """Register a new user account."""
    try:
        _user, access_token = await service.register_user(
            user_data.email,
            user_data.password,
            user_data.first_name,
            user_data.last_name,
            service.user_dao.session,
        )
        return Token(access_token=access_token, token_type="bearer")
    except UserAlreadyExistsError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/login", response_model=Token)
async def login(
    form_data: Annotated[OAuth2PasswordRequestForm, Depends()],
    service: AuthService = Depends(get_auth_service),
) -> Token:
    """Login and receive access token."""
    try:
        _user, access_token = await service.login_user(
            form_data.username, form_data.password, service.user_dao.session
        )
        return Token(access_token=access_token, token_type="bearer")
    except InvalidCredentialsError as e:
        raise HTTPException(
            status_code=401, detail=str(e), headers={"WWW-Authenticate": "Bearer"}
        )


@router.get("/me", response_model=UserResponse)
async def get_current_user_info(
    current_user: Annotated[User, Depends(get_current_user)],
) -> UserResponse:
    """Get current user information."""
    return UserResponse(
        id=str(current_user.id),
        email=current_user.email,
        first_name=current_user.first_name,
        last_name=current_user.last_name,
        created_at=current_user.created_at,
    )
