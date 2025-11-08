"""
Organization Context Middleware
"""

from fastapi import Header, HTTPException, status, Depends
from sqlalchemy.orm import Session
from typing import Optional
import uuid

from app.core.database import get_db
from app.models.user import User
from app.models.organization import Organization, UserOrganization
from app.utils.auth import get_current_user


async def get_organization_id(
    x_organization_id: Optional[str] = Header(None, alias="X-Organization-ID")
) -> Optional[str]:
    """
    Extract organization ID from header

    Args:
        x_organization_id: Organization ID from X-Organization-ID header

    Returns:
        Organization ID string or None
    """
    return x_organization_id


async def get_current_organization(
    organization_id: Optional[str] = Depends(get_organization_id),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
) -> Organization:
    """
    Get the current organization from header and verify user has access

    Args:
        organization_id: Organization ID from header
        current_user: Current authenticated user
        db: Database session

    Returns:
        Organization object

    Raises:
        HTTPException: If organization ID is missing, invalid, or user doesn't have access
    """
    if not organization_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="X-Organization-ID header is required"
        )

    # Validate UUID format
    try:
        org_uuid = uuid.UUID(organization_id)
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid organization ID format"
        )

    # Check if organization exists
    organization = db.query(Organization).filter(Organization.id == org_uuid).first()
    if not organization:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Organization not found"
        )

    # Check if user has access to this organization
    user_org = db.query(UserOrganization).filter(
        UserOrganization.user_id == current_user.id,
        UserOrganization.organization_id == org_uuid
    ).first()

    if not user_org and not current_user.is_superuser:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You don't have access to this organization"
        )

    return organization


async def get_optional_organization(
    organization_id: Optional[str] = Depends(get_organization_id),
    db: Session = Depends(get_db)
) -> Optional[Organization]:
    """
    Get organization if header is provided (optional for some endpoints)

    Args:
        organization_id: Organization ID from header
        db: Database session

    Returns:
        Organization object or None
    """
    if not organization_id:
        return None

    try:
        org_uuid = uuid.UUID(organization_id)
    except ValueError:
        return None

    organization = db.query(Organization).filter(Organization.id == org_uuid).first()
    return organization


async def verify_organization_admin(
    current_user: User = Depends(get_current_user),
    organization: Organization = Depends(get_current_organization),
    db: Session = Depends(get_db)
) -> bool:
    """
    Verify that the current user is an admin of the organization

    Args:
        current_user: Current authenticated user
        organization: Current organization
        db: Database session

    Returns:
        True if user is admin

    Raises:
        HTTPException: If user is not an admin
    """
    if current_user.is_superuser:
        return True

    user_org = db.query(UserOrganization).filter(
        UserOrganization.user_id == current_user.id,
        UserOrganization.organization_id == organization.id
    ).first()

    if not user_org or user_org.role != "admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Admin permissions required"
        )

    return True
