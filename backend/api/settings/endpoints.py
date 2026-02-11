# backend/api/settings/endpoints.py
"""User settings endpoints."""
from typing import Annotated, List

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from backend.auth.dependencies import get_current_user
from backend.core.enums import LLMProvider
from backend.db.database import get_db
from backend.db.models import User
from backend.services.dependencies import get_settings_service
from backend.services.settings.exceptions import (
    EmailAlreadyTakenError,
    InvalidPasswordError,
    SettingsError,
)
from backend.services.settings.service import SettingsService

from .schemas import (
    APIKeyCreate,
    APIKeyResponse,
    PasswordChange,
    ProfileResponse,
    ProfileUpdate,
)

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
    db: AsyncSession = Depends(get_db),
) -> ProfileResponse:
    """Update current user profile."""
    try:
        result = await service.update_profile(
            user_id=current_user.id,
            db=db,
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
    db: AsyncSession = Depends(get_db),
) -> dict:
    """Change current user's password."""
    try:
        await service.change_password(
            user_id=current_user.id,
            current_password=data.current_password,
            new_password=data.new_password,
            db=db,
        )
        return {"message": "Password updated successfully"}
    except InvalidPasswordError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except SettingsError as e:
        raise HTTPException(status_code=400, detail=str(e))


# --- API Keys ---


@router.get("/api-keys", response_model=List[APIKeyResponse])
async def list_api_keys(
    current_user: Annotated[User, Depends(get_current_user)],
    service: SettingsService = Depends(get_settings_service),
    db: AsyncSession = Depends(get_db),
) -> List[APIKeyResponse]:
    """List all API keys for the current user (masked)."""
    keys = await service.get_api_keys_masked(user_id=current_user.id, db=db)
    return [APIKeyResponse(**k) for k in keys]


@router.post("/api-keys", response_model=APIKeyResponse)
async def create_or_update_api_key(
    data: APIKeyCreate,
    current_user: Annotated[User, Depends(get_current_user)],
    service: SettingsService = Depends(get_settings_service),
    db: AsyncSession = Depends(get_db),
) -> APIKeyResponse:
    """Create or update an API key for a provider."""
    result = await service.upsert_api_key(
        user_id=current_user.id,
        provider=data.provider,
        raw_key=data.api_key,
        db=db,
    )
    return APIKeyResponse(**result)


@router.delete("/api-keys/{provider}", status_code=200)
async def delete_api_key_endpoint(
    provider: LLMProvider,
    current_user: Annotated[User, Depends(get_current_user)],
    service: SettingsService = Depends(get_settings_service),
    db: AsyncSession = Depends(get_db),
) -> dict:
    """Delete an API key by provider."""
    deleted = await service.delete_api_key(
        user_id=current_user.id,
        provider=provider,
        db=db,
    )
    if not deleted:
        raise HTTPException(
            status_code=404, detail=f"No API key found for {provider.value}"
        )
    return {"message": f"API key for {provider.value} deleted"}
