"""
Authentication Schemas
"""

from pydantic import BaseModel, EmailStr
from typing import Optional
from datetime import datetime


class TokenResponse(BaseModel):
    """JWT token response"""
    access_token: str
    token_type: str = "bearer"
    expires_in: int


class GoogleAuthRequest(BaseModel):
    """Google OAuth code"""
    code: str


class UserProfile(BaseModel):
    """User profile information"""
    id: str
    email: EmailStr
    full_name: Optional[str] = None
    picture_url: Optional[str] = None
    is_active: bool = True
    is_superuser: bool = False
    preferences: dict = {}
    last_login: Optional[datetime] = None
    created_at: datetime
    updated_at: Optional[datetime] = None

    class Config:
        from_attributes = True


class UserWithOrganizations(UserProfile):
    """User profile with organization memberships"""
    organizations: list[dict] = []

    class Config:
        from_attributes = True
