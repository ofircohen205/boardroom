# backend/api/auth/schemas.py
"""Auth request/response schemas."""
from datetime import datetime
from pydantic import BaseModel, EmailStr


class UserCreate(BaseModel):
    """User registration request."""
    email: EmailStr
    password: str


class Token(BaseModel):
    """JWT token response."""
    access_token: str
    token_type: str


class UserResponse(BaseModel):
    """User information response."""
    id: str
    email: str
    created_at: datetime
