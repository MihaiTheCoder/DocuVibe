"""
Enhanced Chat Interface Routes
"""

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List

from app.core.database import get_db
from app.models.user import User
from app.models.organization import Organization
from app.schemas.workflow import (
    ChatMessageRequest,
    ChatResponse,
    ConversationResponse
)
from app.utils.auth import get_current_user
from app.middleware.organization import get_current_organization
from app.services.chat_service import EnhancedChatService

router = APIRouter(prefix="/chat", tags=["chat"])


@router.post("/message", response_model=ChatResponse)
async def send_chat_message(
    request: ChatMessageRequest,
    current_user: User = Depends(get_current_user),
    organization: Organization = Depends(get_current_organization),
    db: Session = Depends(get_db)
):
    """Send a chat message and get AI response"""
    service = EnhancedChatService(
        db,
        str(organization.id),
        str(current_user.id)
    )

    try:
        response = await service.process_message(request)
        return response

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to process chat message: {str(e)}"
        )


@router.get("/conversations", response_model=List[ConversationResponse])
async def get_conversations(
    current_user: User = Depends(get_current_user),
    organization: Organization = Depends(get_current_organization),
    db: Session = Depends(get_db)
):
    """Get conversation history"""
    service = EnhancedChatService(
        db,
        str(organization.id),
        str(current_user.id)
    )

    try:
        conversations = service.get_conversations()
        return conversations

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to retrieve conversations: {str(e)}"
        )


@router.post("/mark-ready/{issue_id}")
async def mark_issue_ready(
    issue_id: str,
    current_user: User = Depends(get_current_user),
    organization: Organization = Depends(get_current_organization),
    db: Session = Depends(get_db)
):
    """Mark a GitHub issue as ready for implementation"""
    service = EnhancedChatService(
        db,
        str(organization.id),
        str(current_user.id)
    )

    try:
        success = await service.mark_issue_ready(issue_id)

        if not success:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Failed to mark issue as ready"
            )

        return {"success": True, "message": "Issue marked as ready"}

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to mark issue ready: {str(e)}"
        )
