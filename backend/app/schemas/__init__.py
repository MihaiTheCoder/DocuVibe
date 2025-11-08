"""
Schemas package
"""

from app.schemas.auth import (
    TokenResponse,
    GoogleAuthRequest,
    UserProfile,
    UserWithOrganizations,
)
from app.schemas.user import (
    UserBase,
    UserCreate,
    UserUpdate,
    UserResponse,
    UserDetailResponse,
    ProfileUpdateRequest,
)
from app.schemas.organization import (
    OrganizationBase,
    OrganizationCreate,
    OrganizationUpdate,
    OrganizationResponse,
    OrganizationDetailResponse,
    OrganizationMemberResponse,
    MemberInviteRequest,
    MemberRoleUpdateRequest,
    InvitationResponse,
)
from app.schemas.document import (
    DocumentBase,
    DocumentUploadResponse,
    DocumentResponse,
    DocumentDetailResponse,
    DocumentUpdateRequest,
    DocumentStageUpdateRequest,
    DocumentAssignRequest,
    DocumentApproveRequest,
    DocumentSignRequest,
    DocumentArchiveRequest,
    DocumentReprocessRequest,
    PaginatedDocumentsResponse,
)

__all__ = [
    # Auth
    "TokenResponse",
    "GoogleAuthRequest",
    "UserProfile",
    "UserWithOrganizations",
    # User
    "UserBase",
    "UserCreate",
    "UserUpdate",
    "UserResponse",
    "UserDetailResponse",
    "ProfileUpdateRequest",
    # Organization
    "OrganizationBase",
    "OrganizationCreate",
    "OrganizationUpdate",
    "OrganizationResponse",
    "OrganizationDetailResponse",
    "OrganizationMemberResponse",
    "MemberInviteRequest",
    "MemberRoleUpdateRequest",
    "InvitationResponse",
    # Document
    "DocumentBase",
    "DocumentUploadResponse",
    "DocumentResponse",
    "DocumentDetailResponse",
    "DocumentUpdateRequest",
    "DocumentStageUpdateRequest",
    "DocumentAssignRequest",
    "DocumentApproveRequest",
    "DocumentSignRequest",
    "DocumentArchiveRequest",
    "DocumentReprocessRequest",
    "PaginatedDocumentsResponse",
]
