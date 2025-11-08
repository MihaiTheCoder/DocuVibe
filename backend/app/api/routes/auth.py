"""
Authentication Routes
"""

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.responses import RedirectResponse
from sqlalchemy.orm import Session
from google.oauth2 import id_token
from google.auth.transport import requests as google_requests
from datetime import datetime, timedelta
import httpx

from app.core.config import settings
from app.core.database import get_db
from app.models.user import User
from app.models.organization import Organization, UserOrganization
from app.schemas.auth import TokenResponse, UserProfile, UserWithOrganizations
from app.utils.auth import create_access_token, get_current_user
import uuid

router = APIRouter(prefix="/auth", tags=["authentication"])


@router.get("/google/login")
async def google_login():
    """
    Redirect to Google OAuth login page

    Returns:
        Google OAuth URL for user authentication
    """
    if not settings.GOOGLE_CLIENT_ID:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Google OAuth not configured"
        )

    # Build Google OAuth URL
    google_auth_url = (
        "https://accounts.google.com/o/oauth2/v2/auth"
        f"?client_id={settings.GOOGLE_CLIENT_ID}"
        f"&redirect_uri={settings.GOOGLE_REDIRECT_URI}"
        "&response_type=code"
        "&scope=openid%20email%20profile"
        "&access_type=offline"
        "&prompt=consent"
    )

    return {"auth_url": google_auth_url}


@router.get("/google/callback")
async def google_callback(code: str, db: Session = Depends(get_db)):
    """
    Handle Google OAuth callback and create/update user

    Args:
        code: Authorization code from Google
        db: Database session

    Returns:
        JWT token response
    """
    if not settings.GOOGLE_CLIENT_ID or not settings.GOOGLE_CLIENT_SECRET:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Google OAuth not configured"
        )

    try:
        # Exchange code for token
        async with httpx.AsyncClient() as client:
            token_response = await client.post(
                "https://oauth2.googleapis.com/token",
                data={
                    "code": code,
                    "client_id": settings.GOOGLE_CLIENT_ID,
                    "client_secret": settings.GOOGLE_CLIENT_SECRET,
                    "redirect_uri": settings.GOOGLE_REDIRECT_URI,
                    "grant_type": "authorization_code",
                },
            )
            token_data = token_response.json()

            if "error" in token_data:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"OAuth error: {token_data['error']}"
                )

            # Verify ID token and get user info
            id_info = id_token.verify_oauth2_token(
                token_data["id_token"],
                google_requests.Request(),
                settings.GOOGLE_CLIENT_ID
            )

            email = id_info.get("email")
            google_id = id_info.get("sub")
            full_name = id_info.get("name")
            picture_url = id_info.get("picture")

            if not email or not google_id:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Invalid Google user info"
                )

            # Check if user exists
            user = db.query(User).filter(User.email == email).first()

            if user:
                # Update existing user
                user.google_id = google_id
                user.full_name = full_name or user.full_name
                user.picture_url = picture_url or user.picture_url
                user.last_login = datetime.utcnow()
            else:
                # Create new user
                user = User(
                    email=email,
                    google_id=google_id,
                    full_name=full_name,
                    picture_url=picture_url,
                    last_login=datetime.utcnow(),
                )
                db.add(user)
                db.flush()  # Get user ID

                # Create default organization for new user
                org_name = f"{email.split('@')[0]}-org"
                organization = Organization(
                    name=org_name,
                    display_name=f"{full_name}'s Organization" if full_name else f"{email}'s Organization",
                )
                db.add(organization)
                db.flush()

                # Add user to organization as admin
                user_org = UserOrganization(
                    user_id=user.id,
                    organization_id=organization.id,
                    role="admin",
                    invited_at=datetime.utcnow(),
                    joined_at=datetime.utcnow(),
                )
                db.add(user_org)

            db.commit()
            db.refresh(user)

            # Create JWT token
            access_token = create_access_token(
                data={"sub": str(user.id), "email": user.email}
            )

            return TokenResponse(
                access_token=access_token,
                token_type="bearer",
                expires_in=settings.JWT_EXPIRATION_HOURS * 3600
            )

    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Authentication failed: {str(e)}"
        )


@router.post("/logout")
async def logout(current_user: User = Depends(get_current_user)):
    """
    Logout user (client should discard token)

    Args:
        current_user: Current authenticated user

    Returns:
        Success message
    """
    # In a JWT-based system, logout is handled client-side by discarding the token
    # For additional security, you could implement token blacklisting here
    return {"message": "Successfully logged out"}


@router.get("/me", response_model=UserWithOrganizations)
async def get_current_user_info(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Get current user profile with organizations

    Args:
        current_user: Current authenticated user
        db: Database session

    Returns:
        User profile with organizations
    """
    # Get user's organizations
    user_orgs = db.query(UserOrganization).filter(
        UserOrganization.user_id == current_user.id
    ).all()

    organizations = []
    for user_org in user_orgs:
        org = db.query(Organization).filter(
            Organization.id == user_org.organization_id
        ).first()
        if org:
            organizations.append({
                "id": str(org.id),
                "name": org.name,
                "display_name": org.display_name,
                "role": user_org.role,
                "joined_at": user_org.joined_at
            })

    return UserWithOrganizations(
        id=str(current_user.id),
        email=current_user.email,
        full_name=current_user.full_name,
        picture_url=current_user.picture_url,
        is_active=current_user.is_active,
        is_superuser=current_user.is_superuser,
        preferences=current_user.preferences or {},
        last_login=current_user.last_login,
        created_at=current_user.created_at,
        updated_at=current_user.updated_at,
        organizations=organizations
    )
