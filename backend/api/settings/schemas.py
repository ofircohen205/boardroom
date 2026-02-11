# backend/api/settings/schemas.py
"""Settings request/response schemas."""

from datetime import datetime
from typing import Optional

from pydantic import BaseModel, EmailStr, Field

from backend.core.enums import LLMProvider


class ProfileUpdate(BaseModel):
    """Partial profile update request."""

    first_name: Optional[str] = Field(None, min_length=1, max_length=100)
    last_name: Optional[str] = Field(None, min_length=1, max_length=100)
    email: Optional[EmailStr] = None


class ProfileResponse(BaseModel):
    """User profile response."""

    id: str
    email: str
    first_name: str
    last_name: str
    created_at: datetime


class PasswordChange(BaseModel):
    """Password change request."""

    current_password: str
    new_password: str = Field(..., min_length=8, max_length=128)


class APIKeyCreate(BaseModel):
    """API key creation/update request."""

    provider: LLMProvider
    api_key: str = Field(..., min_length=1)


class APIKeyResponse(BaseModel):
    """API key response with masked value."""

    provider: str
    masked_key: str
    created_at: datetime
