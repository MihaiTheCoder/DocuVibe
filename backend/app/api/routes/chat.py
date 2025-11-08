"""
Chat Interface Routes

Handles conversational AI interactions for document search and workflow creation.
All endpoints require authentication and organization context.
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
from app.services.chat_service import ChatService

router = APIRouter(prefix="/chat", tags=["chat"])


@router.post("/message", response_model=ChatResponse)
async def send_chat_message(
    request: ChatMessageRequest,
    current_user: User = Depends(get_current_user),
    organization: Organization = Depends(get_current_organization),
    db: Session = Depends(get_db)
):
    """
    Send a chat message and get AI response

    Args:
        request: Chat message request
        current_user: Current authenticated user
        organization: Current organization context
        db: Database session

    Returns:
        Chat response with results and suggested actions
    """
    service = ChatService(db, str(organization.id))

    try:
        response = service.process_message(request)
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
    """
    Get conversation history

    Args:
        current_user: Current authenticated user
        organization: Current organization context
        db: Database session

    Returns:
        List of conversations
    """
    service = ChatService(db, str(organization.id))

    try:
        conversations = service.get_conversations()
        return conversations

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to retrieve conversations: {str(e)}"
        )
