"""
User Schemas
"""

from pydantic import BaseModel, EmailStr
from typing import Optional
from datetime import datetime


class UserBase(BaseModel):
    """Base user schema"""
    email: EmailStr
    full_name: Optional[str] = None


class UserCreate(UserBase):
    """Schema for creating a user"""
    google_id: str
    picture_url: Optional[str] = None


class UserUpdate(BaseModel):
    """Schema for updating a user"""
    full_name: Optional[str] = None
    picture_url: Optional[str] = None
    preferences: Optional[dict] = None


class UserResponse(UserBase):
    """Schema for user response"""
    id: str
    picture_url: Optional[str] = None
    is_active: bool
    is_superuser: bool
    preferences: dict
    last_login: Optional[datetime] = None
    created_at: datetime
    updated_at: Optional[datetime] = None

    class Config:
        from_attributes = True


class UserDetailResponse(UserResponse):
    """Schema for detailed user response with relationships"""
    organizations: list[dict] = []

    class Config:
        from_attributes = True


class ProfileUpdateRequest(BaseModel):
    """Schema for updating user profile"""
    full_name: Optional[str] = None
    preferences: Optional[dict] = None
