"""
Organization Schemas
"""

from pydantic import BaseModel, EmailStr
from typing import Optional
from datetime import datetime


class OrganizationBase(BaseModel):
    """Base organization schema"""
    name: str
    display_name: Optional[str] = None


class OrganizationCreate(OrganizationBase):
    """Schema for creating an organization"""
    settings: Optional[dict] = {}


class OrganizationUpdate(BaseModel):
    """Schema for updating an organization"""
    display_name: Optional[str] = None
    settings: Optional[dict] = None


class OrganizationResponse(OrganizationBase):
    """Schema for organization response"""
    id: str
    settings: dict
    subscription_tier: str
    storage_quota_gb: int
    storage_used_bytes: int
    created_at: datetime
    updated_at: Optional[datetime] = None

    class Config:
        from_attributes = True


class OrganizationDetailResponse(OrganizationResponse):
    """Schema for detailed organization response"""
    member_count: Optional[int] = None
    document_count: Optional[int] = None

    class Config:
        from_attributes = True


class OrganizationMemberResponse(BaseModel):
    """Schema for organization member"""
    user_id: str
    organization_id: str
    email: EmailStr
    full_name: Optional[str] = None
    role: str
    joined_at: datetime

    class Config:
        from_attributes = True


class MemberInviteRequest(BaseModel):
    """Schema for inviting a member"""
    email: EmailStr
    role: str = "member"


class MemberRoleUpdateRequest(BaseModel):
    """Schema for updating member role"""
    role: str


class InvitationResponse(BaseModel):
    """Schema for invitation response"""
    id: str
    email: EmailStr
    organization_id: str
    role: str
    invited_at: datetime
    status: str = "pending"

    class Config:
        from_attributes = True
