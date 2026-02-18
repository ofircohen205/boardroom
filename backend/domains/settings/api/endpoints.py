# backend/api/settings/endpoints.py
"""User settings endpoints."""

from typing import Annotated

from backend.domains.settings.schemas import (
    PasswordChange,
    ProfileResponse,
    ProfileUpdate,
)
from fastapi import APIRouter, Depends, HTTPException

from backend.dependencies import get_settings_service
from backend.domains.settings.services.exceptions import (
    EmailAlreadyTakenError,
    InvalidPasswordError,
    SettingsError,
)
from backend.domains.settings.services.service import SettingsService
from backend.shared.auth.dependencies import get_current_user
from backend.shared.db.models import User

router = APIRouter(prefix="/settings", tags=["settings"])


# --- Profile ---


@router.get("/profile", response_model=ProfileResponse)
async def get_profile(
    current_user: Annotated[User, Depends(get_current_user)],
) -> ProfileResponse:
    """Get current user profile."""
    return ProfileResponse(
        id=str(current_user.id),
        email=current_user.email,
        first_name=current_user.first_name,
        last_name=current_user.last_name,
        created_at=current_user.created_at,
    )


@router.patch("/profile", response_model=ProfileResponse)
async def update_profile_endpoint(
    data: ProfileUpdate,
    current_user: Annotated[User, Depends(get_current_user)],
    service: SettingsService = Depends(get_settings_service),
) -> ProfileResponse:
    """Update current user profile."""
    try:
        result = await service.update_profile(
            user_id=current_user.id,
            db=service.user_dao.session,
            first_name=data.first_name,
            last_name=data.last_name,
            email=data.email,
        )
        return ProfileResponse(**result)
    except EmailAlreadyTakenError as e:
        raise HTTPException(status_code=409, detail=str(e))
    except SettingsError as e:
        raise HTTPException(status_code=400, detail=str(e))


# --- Password ---


@router.post("/password", status_code=200)
async def change_password_endpoint(
    data: PasswordChange,
    current_user: Annotated[User, Depends(get_current_user)],
    service: SettingsService = Depends(get_settings_service),
) -> dict:
    """Change current user's password."""
    try:
        await service.change_password(
            user_id=current_user.id,
            current_password=data.current_password,
            new_password=data.new_password,
            db=service.user_dao.session,
        )
        return {"message": "Password updated successfully"}
    except InvalidPasswordError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except SettingsError as e:
        raise HTTPException(status_code=400, detail=str(e))
